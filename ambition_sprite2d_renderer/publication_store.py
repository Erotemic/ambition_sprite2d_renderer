"""Immutable art bundles and one atomic publication selection."""
from __future__ import annotations

import fcntl
import errno
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import tempfile

SCHEMA = "ambition.art_publication.v1"
BUNDLE_SCHEMA = "ambition.art_bundle.v1"
TIERS = {"full": "sprites", "half": "sprites_0_5x", "quarter": "sprites_0_25x", "potato": "sprites_potato"}
MANAGED_ROOTS = (*TIERS.values(), "sprite_packs")


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        value = hashlib.sha256()
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
        return value.hexdigest()


def identity(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def relative(value: str) -> str:
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts or path.as_posix() != value or "\\" in value:
        raise ValueError(f"Invalid artifact path: {value!r}")
    return value


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".write-")
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(value, stream, sort_keys=True, indent=1)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


class Store:
    def __init__(self, root: Path):
        self.root = Path(root)

    def selected(self) -> dict:
        path = self.root / "published.json"
        if not path.exists():
            return {"schema": SCHEMA, "generation": None, "bundles": {}, "files": {}}
        value = json.loads(path.read_text())
        if value.get("schema") != SCHEMA:
            raise ValueError(f"Unsupported publication: {path}")
        if value.get("generation") != identity({name: item for name, item in value.items() if name != "generation"}):
            raise ValueError(f"Invalid publication identity: {path}")
        for logical, item in value["files"].items():
            relative(logical)
            relative(item["path"])
        return value

    def bundle(self, key: str) -> dict:
        if len(key) != 64 or any(c not in "0123456789abcdef" for c in key):
            raise ValueError("Invalid bundle identity")
        value = json.loads((self.root / "bundles" / key / "manifest.json").read_text())
        if value.get("schema") != BUNDLE_SCHEMA or identity(value) != key:
            raise ValueError(f"Invalid bundle manifest: {key}")
        return value

    def accept(self, unit: str, files: dict[str, tuple[Path, str, str]], recipe: dict | None,
               *, parents: dict[str, str] | None = None) -> str:
        """Accept only the exact members supplied by a completed producer."""
        if not files:
            raise ValueError(f"Empty bundle: {unit}")
        rows = {}
        for logical, (source, role, tier) in sorted(files.items()):
            relative(logical)
            if not source.is_file():
                raise ValueError(f"Missing bundle member: {unit}: {source}")
            physical = f"{role}/{tier}/{logical.removeprefix('review/') if role == 'review' else logical}"
            rows[logical] = {"path": relative(physical), "sha256": digest(source), "bytes": source.stat().st_size,
                             "role": role, "tier": tier}
        manifest = {"schema": BUNDLE_SCHEMA, "unit": unit, "recipe": recipe, "parents": parents or {}, "files": rows}
        key = identity(manifest)
        destination = self.root / "bundles" / key
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            if self.integrity(key):
                raise ValueError(f"Corrupt immutable bundle: {key}")
            return key
        with tempfile.TemporaryDirectory(dir=destination.parent, prefix=".bundle-") as temporary:
            staging = Path(temporary)
            for logical, (source, _role, _tier) in files.items():
                target = staging / rows[logical]["path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
                if digest(target) != rows[logical]["sha256"]:
                    raise ValueError(f"Artifact changed during acceptance: {logical}")
            write_json(staging / "manifest.json", manifest)
            try:
                staging.rename(destination)
            except OSError as error:
                if error.errno not in (errno.EEXIST, errno.ENOTEMPTY):
                    raise
                if self.integrity(key):
                    raise ValueError(f"Corrupt immutable bundle: {key}")
        return key

    def integrity(self, key: str, *, deep: bool = True, hashes=None) -> list[dict]:
        manifest = self.bundle(key)
        defects = []
        for logical, item in manifest["files"].items():
            path = self.root / "bundles" / key / relative(item["path"])
            if not path.is_file():
                defects.append({"code": "missing", "path": logical})
            elif deep and (hashes.file(path) if hashes is not None else digest(path)) != item["sha256"]:
                defects.append({"code": "changed-output", "path": logical})
        return defects

    def publish(self, replacements: dict[str, str], base: str | None, *, replace: bool = False) -> dict:
        """A changed base refuses publication. Builds can run without this lock."""
        self.root.mkdir(parents=True, exist_ok=True)
        with (self.root / ".publish.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            previous = self.selected()
            if previous["generation"] != base:
                raise ValueError("The published selection changed. Plan the request again.")
            bundles = dict(replacements) if replace else previous["bundles"] | replacements
            files = {}
            for unit, key in sorted(bundles.items()):
                manifest = self.bundle(key)
                if manifest["unit"] != unit:
                    raise ValueError(f"Bundle owner mismatch: {unit}")
                if self.integrity(key):
                    raise ValueError(f"Incomplete bundle: {unit}")
                for parent, expected in manifest["parents"].items():
                    if bundles.get(parent) != expected:
                        raise ValueError(f"Changed bundle dependency: {unit}: {parent}")
                for logical, item in manifest["files"].items():
                    if item["role"] != "runtime":
                        continue
                    if logical in files:
                        raise ValueError(f"Two producers own {logical}")
                    files[logical] = dict(item, unit=unit, bundle=key, path=f"bundles/{key}/{item['path']}")
            roots = sorted(set(MANAGED_ROOTS) | {name.split("/", 1)[0] for name in files})
            selection = {"schema": SCHEMA, "bundles": bundles, "files": files, "roots": roots}
            selection["generation"] = identity(selection)
            write_json(self.root / "published.json", selection)
            return selection

    def paths(self) -> dict[str, Path]:
        return {name: self.root / item["path"] for name, item in self.selected()["files"].items()}
