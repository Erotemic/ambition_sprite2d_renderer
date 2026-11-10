"""Immutable art bundles and one atomic publication selection."""
from __future__ import annotations

import fcntl
import sys
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


def copy_digest(source: Path, target: Path) -> tuple[str, int]:
    """Copy `source` to `target` and return the digest and size of the bytes
    copied: one read of the source, and the digest is of exactly what was
    written."""
    value, size = hashlib.sha256(), 0
    with source.open("rb") as reader, target.open("wb") as writer:
        for block in iter(lambda: reader.read(1024 * 1024), b""):
            value.update(block)
            writer.write(block)
            size += len(block)
    return value.hexdigest(), size


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
        #: Verified manifests by key. A bundle is immutable: its key is its manifest's digest.
        self._bundles: dict[str, str] = {}

    def selected(self, *, verify_identity: bool = True) -> dict:
        """The selection. A reader that only resolves files passes
        `verify_identity=False`: a stale recorded identity is a freshness
        question, while unsafe member paths refuse either way."""
        path = self.root / "published.json"
        if not path.exists():
            return {"schema": SCHEMA, "generation": None, "bundles": {}, "files": {}}
        value = json.loads(path.read_text())
        if value.get("schema") != SCHEMA:
            raise ValueError(f"Unsupported publication: {path}")
        if verify_identity and value.get("generation") != identity({name: item for name, item in value.items() if name != "generation"}):
            raise ValueError(f"Invalid publication identity: {path}")
        for logical, item in value["files"].items():
            relative(logical)
            relative(item["path"])
        return value

    def bundle(self, key: str) -> dict:
        if key in self._bundles:
            return json.loads(self._bundles[key])
        if len(key) != 64 or any(c not in "0123456789abcdef" for c in key):
            raise ValueError("Invalid bundle identity")
        text = (self.root / "bundles" / key / "manifest.json").read_text()
        value = json.loads(text)
        if value.get("schema") != BUNDLE_SCHEMA or identity(value) != key:
            raise ValueError(f"Invalid bundle manifest: {key}")
        self._bundles[key] = text
        return value

    def accept(self, unit: str, files: dict[str, tuple[Path, str, str]], recipe: dict | None,
               *, parents: dict[str, str] | None = None, roots: list[str] | None = None) -> str:
        """Accept only the exact members supplied by a completed producer."""
        if not files:
            raise ValueError(f"Empty bundle: {unit}")
        destinations = {}
        for logical, (source, role, tier) in sorted(files.items()):
            relative(logical)
            if not source.is_file():
                raise ValueError(f"Missing bundle member: {unit}: {source}")
            destinations[logical] = relative(f"{role}/{tier}/{logical.removeprefix('review/') if role == 'review' else logical}")
        bundles = self.root / "bundles"
        bundles.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=bundles, prefix=".bundle-") as temporary:
            staging = Path(temporary)
            # One pass: each member is read once, and its recorded digest is of
            # the bytes this bundle holds.
            rows = {}
            for logical, (source, role, tier) in sorted(files.items()):
                target = staging / destinations[logical]
                target.parent.mkdir(parents=True, exist_ok=True)
                sha256, size = copy_digest(source, target)
                rows[logical] = {"path": destinations[logical], "sha256": sha256, "bytes": size, "role": role, "tier": tier}
            manifest = {"schema": BUNDLE_SCHEMA, "unit": unit, "recipe": recipe, "parents": parents or {}, "files": rows}
            if roots is not None:
                manifest["roots"] = sorted({relative(root) for root in roots})
            key = identity(manifest)
            destination = bundles / key
            # The key names the members' digests, so an accepted bundle with
            # this key holds these bytes; its members only have to be there.
            # Reading them again is `audit`'s work.
            if destination.exists():
                if self.integrity(key, deep=False):
                    raise ValueError(f"Incomplete immutable bundle: {key}")
                return key
            write_json(staging / "manifest.json", manifest)
            try:
                staging.rename(destination)
            except OSError as error:
                if error.errno not in (errno.EEXIST, errno.ENOTEMPTY):
                    raise
                if self.integrity(key, deep=False):
                    raise ValueError(f"Incomplete immutable bundle: {key}")
        return key

    def integrity(self, key: str, *, deep: bool = True, hashes=None) -> list[dict]:
        manifest = self.bundle(key)
        defects = []
        for logical, item in manifest["files"].items():
            path = self.root / "bundles" / key / relative(item["path"])
            if deep and hashes is not None:
                # The digest cache stats the file once; None means it is not a readable file.
                found = hashes.file(path)
                if found is None:
                    defects.append({"code": "missing", "path": logical})
                elif found != item["sha256"]:
                    defects.append({"code": "changed-output", "path": logical})
            elif not path.is_file():
                defects.append({"code": "missing", "path": logical})
            elif deep and digest(path) != item["sha256"]:
                defects.append({"code": "changed-output", "path": logical})
        return defects

    def audit(self, *, hashes=None) -> dict[str, list[dict]]:
        """Read every member of every selected bundle against its recorded
        digest: the deep check that selection does not make. For a release or
        a doubt, not for each publication."""
        return {unit: defects for unit, key in sorted(self.selected()["bundles"].items())
                if (defects := self.integrity(key, hashes=hashes))}

    def publish(self, replacements: dict[str, str], base, *, replace: bool = False, only_missing=False, refresh_units=()) -> dict:
        """Select ``replacements`` and return the new selection.

        ``base`` is the selection the caller planned against: the selection
        itself, or only its generation. Builds and publications do not wait on
        each other. When another publication moved the selection after the
        caller planned, the caller's CHANGES are merged onto the newer
        selection: each unit the caller added, replaced or removed relative to
        its base. A unit that both changed is the caller's (the last writer
        wins per unit). With only a generation, the changes are
        ``replacements``.

        ``only_missing`` keeps accepted units and paths under the publication
        lock. A concurrent publisher's products are kept too.
        ``refresh_units`` can replace derived indexes when new units are added.

        Selection reads accepted manifests: a bundle that this publication
        newly selects must have its members present, and one already selected
        is not looked at again. Payload digests are `audit`'s.

        A bundle whose recorded parent is not the selected one is still
        selected. It is listed in ``stale`` with its reason, so a status query
        reports it and the next build of that unit replaces it.
        """
        self.root.mkdir(parents=True, exist_ok=True)
        with (self.root / ".publish.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            previous = self.selected()
            if only_missing:
                replacements = {unit: key for unit, key in replacements.items()
                                if unit in refresh_units or (unit not in previous['bundles'] and not any(
                                    item['role'] == 'runtime' and logical in previous['files']
                                    for logical, item in self.bundle(key)['files'].items()))}
                replace = False
            planned = base.get("generation") if isinstance(base, dict) else base
            if previous["generation"] != planned:
                before = base.get("bundles", {}) if isinstance(base, dict) else {}
                changed = {unit: key for unit, key in replacements.items() if before.get(unit) != key}
                removed = set(before) - set(replacements) if replace and isinstance(base, dict) else set()
                bundles = {unit: key for unit, key in previous["bundles"].items() if unit not in removed} | changed
                print(f"publication: another publication moved the selection; merged {len(changed)} changed and "
                      f"{len(removed)} removed unit(s) onto it", file=sys.stderr)
            else:
                bundles = dict(replacements) if replace else previous["bundles"] | replacements
            files = {}
            stale: dict[str, list[str]] = {}
            managed_roots = set(MANAGED_ROOTS)
            for unit, key in sorted(bundles.items()):
                manifest = self.bundle(key)
                if manifest["unit"] != unit:
                    raise ValueError(f"Bundle owner mismatch: {unit}")
                if previous["bundles"].get(unit) != key and self.integrity(key, deep=False):
                    raise ValueError(f"Incomplete bundle: {unit}")
                for parent, expected in manifest["parents"].items():
                    if bundles.get(parent) != expected:
                        stale.setdefault(unit, []).append(f"parent {parent} is not the one it was built from")
                managed_roots.update(manifest.get("roots", [logical.split("/", 1)[0] for logical, item in manifest["files"].items() if item["role"] == "runtime"]))
                for logical, item in manifest["files"].items():
                    if item["role"] != "runtime":
                        continue
                    if logical in files:
                        raise ValueError(f"Two producers own {logical}")
                    files[logical] = dict(item, unit=unit, bundle=key, path=f"bundles/{key}/{item['path']}")
            roots = sorted(managed_roots)
            selection = {"schema": SCHEMA, "bundles": bundles, "files": files, "roots": roots}
            if stale:
                selection["stale"] = stale
                for unit, reasons in sorted(stale.items()):
                    print(f"publication: {unit} is stale: {'; '.join(reasons)}", file=sys.stderr)
            selection["generation"] = identity(selection)
            write_json(self.root / "published.json", selection)
            return selection

    def paths(self) -> dict[str, Path]:
        return {name: self.root / item["path"] for name, item in self.selected()["files"].items()}
