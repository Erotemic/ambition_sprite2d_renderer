"""Art provenance: which generator made which published file, from which inputs.

Jon, 2026-10-24: "This UI needs to connect any real piece of art to its
generator", and a portable provenance file next to the outputs. The renderer's
`.cache/` digests say the same thing, but only in the checkout that rendered:
a fresh worktree has none.

A publish writes one record for each published unit (a sprite target, a
parallax theme, a terrain skin) as JSON:

    {"schema": "ambition.art_provenance.v1", "unit": "goblin",
     "basis": "rendered",
     "generator": {"family": "sprite_target", "id": "goblin", "source": ..., "command": ...},
     "root": "sprites",
     "outputs": [{"path": "goblin_spritesheet.png", "sha256": ..., "bytes": ...,
                  "made_by": {"callable": ..., "source": ..., "line": ...}}],
     "inputs": [{"path": "tools/.../configs/goblin.yaml", "sha256": ...}],
     "renderer": {"commit": ..., "dirty": false}, "written_at": ...}

`basis` says how the record was made: `rendered` (written by the render that
made the outputs, so its input digests are what the render read), `cache`
(backfilled from `.cache/sheets`, whose digests the outputs matched; input
digests unknown) or `plan` (backfilled from the generator's own table of
outputs; the bytes were not rendered here). A reader checks each output's
digest against the file on disk: a record never vouches for a file that has
since changed.

The records go in a provenance root beside the runtime asset root, never in
it: the asset roots are packaged whole (`scripts/package_asset_guard.py`), and
the layout says what an asset is (Q82). `AMBITION_ART_PROVENANCE_DIR` names
the record directory of one publish (the publish scripts set it, because a
full sprite publish installs into a staging root). Without it, a destination
under the runtime asset root records into the same relative path under the
provenance root, and any other destination (a test, a scratch install)
records nothing.

    python -m ambition_sprite2d_renderer.provenance backfill
"""

from __future__ import annotations

import argparse
import datetime as _dt
import functools
import hashlib
import importlib.util
import inspect
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Iterable

SCHEMA = "ambition.art_provenance.v1"
#: The record directory of one publish.
ENV = "AMBITION_ART_PROVENANCE_DIR"

_RENDERER = Path(__file__).resolve().parents[1]


def repo_root() -> Path:
    override = os.environ.get("AMBITION_REPO_ROOT")
    if override:
        return Path(override).resolve()
    return Path(__file__).resolve().parents[3]


def asset_root() -> Path:
    """The runtime asset root the sprite, background and terrain publishes write into."""
    return repo_root() / "crates" / "ambition_platformer2d_actor_monolith" / "assets"


def provenance_root() -> Path:
    """The root of the records: a sibling of the asset root, not inside it."""
    return asset_root().parent / "asset_provenance"


def record_dir(dest: Path) -> Path | None:
    """Where the records of files published into `dest` go, or None when
    `dest` is not a game asset root."""
    env = os.environ.get(ENV)
    if env:
        return Path(env)
    try:
        rel = Path(dest).resolve().relative_to(asset_root().resolve())
    except ValueError:
        return None
    return provenance_root() / rel


def _repo_relative(path: Path | str) -> str:
    real = Path(os.path.realpath(path))
    try:
        return real.relative_to(Path(os.path.realpath(repo_root()))).as_posix()
    except ValueError:
        return real.as_posix()


@functools.lru_cache(maxsize=4096)
def _digest(path: str, mtime_ns: int, size: int) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def digest(path: Path | str) -> str:
    st = os.stat(path)
    return _digest(os.path.realpath(path), st.st_mtime_ns, st.st_size)


@functools.lru_cache(maxsize=1)
def renderer_state() -> dict[str, Any]:
    """The renderer's commit, and whether its source differs from that commit."""
    def git(*args: str) -> str:
        done = subprocess.run(["git", "-C", str(_RENDERER), *args], capture_output=True, text=True, timeout=30)
        return done.stdout.strip() if done.returncode == 0 else ""

    commit = git("rev-parse", "HEAD") or None
    dirty = bool(git("status", "--porcelain", "--untracked-files=no", "--", "ambition_sprite2d_renderer"))
    return {"commit": commit, "dirty": dirty}


def made_by(fn: Callable | None) -> dict[str, Any] | None:
    """The callable that drew an output: its dotted name, file and line."""
    if fn is None:
        return None
    fn = inspect.unwrap(fn)
    out: dict[str, Any] = {"callable": f"{getattr(fn, '__module__', '?')}:{getattr(fn, '__qualname__', repr(fn))}"}
    try:
        out["source"] = _repo_relative(inspect.getsourcefile(fn) or "")
        out["line"] = inspect.getsourcelines(fn)[1]
    except (OSError, TypeError):
        pass
    return out


def renderer_modules() -> list[str]:
    """The renderer's Python files this process imported: the code a
    background or terrain draw ran (more than one unit needs, never less)."""
    package = _RENDERER / "ambition_sprite2d_renderer"
    out = set()
    for module in list(sys.modules.values()):
        file = getattr(module, "__file__", None)
        if file and file.endswith(".py"):
            real = Path(os.path.realpath(file))
            if real.is_relative_to(package) and ".venv" not in real.parts:
                out.add(str(real))
    return sorted(out)


def _inputs(paths: Iterable[str | Path] | None, *, hashed: bool = True) -> list[dict[str, Any]]:
    out = []
    for path in sorted({os.path.realpath(p) for p in paths or ()}):
        if not os.path.isfile(path):
            continue
        out.append({"path": _repo_relative(path), "sha256": digest(path) if hashed else None})
    return out


def write_record(
    directory: Path,
    unit: str,
    *,
    generator: dict[str, Any],
    dest: Path,
    outputs: Iterable[tuple[Path, dict[str, Any] | None]],
    inputs: list[dict[str, Any]],
    basis: str = "rendered",
    extra: dict[str, Any] | None = None,
) -> Path:
    """Write the record of `unit`: each output (with the callable that made
    it, when known) relative to `dest`. Written whole, then moved into place."""
    dest = Path(dest)
    rows = []
    for path, by in outputs:
        path = Path(path)
        if not path.is_file():
            continue
        row: dict[str, Any] = {"path": path.relative_to(dest).as_posix(), "sha256": digest(path), "bytes": path.stat().st_size}
        if by:
            row["made_by"] = by
        rows.append(row)
    rows.sort(key=lambda row: row["path"])
    try:
        root = directory.resolve().relative_to(provenance_root().resolve()).as_posix()
    except ValueError:
        root = dest.name
    record = {
        "schema": SCHEMA,
        "unit": unit,
        "basis": basis,
        "generator": generator,
        "root": root,
        "outputs": rows,
        "inputs": inputs,
        "renderer": renderer_state(),
        "written_at": _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat(),
    }
    if extra:
        record.update(extra)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{unit}.json"
    partial = path.with_suffix(".json.partial")
    partial.write_text(json.dumps(record, indent=1, sort_keys=True) + "\n")
    partial.replace(path)
    return path


def read_record(path: Path) -> dict[str, Any] | None:
    try:
        record = json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return None
    return record if record.get("schema") == SCHEMA else None


# ---- sprite targets ------------------------------------------------------------------------


def target_generator(target: Any) -> dict[str, Any]:
    """The generator of a registered sprite target: its authoring source and
    the command that publishes it again."""
    config = getattr(target, "_config_path", None)
    module = getattr(target, "module_path", None)
    source = None
    if config:
        source = _repo_relative(config)
    elif module:
        spec = importlib.util.find_spec(module)
        if spec is not None and spec.origin:
            source = _repo_relative(spec.origin)
    data = [_repo_relative(path) for path in getattr(target, "data_sources", ())]
    return {
        "family": "sprite_target",
        "id": target.name,
        "kind": target.kind,
        "category": target.category,
        "module": module,
        # A target made from a data file (a chargen spec) has that file as its
        # source; the module that reads it is still `module`.
        "source": data[0] if data else source,
        "module_source": source,
        "data": data,
        "command": f"./scripts/regen/sprites.sh --target {target.name}",
    }


def record_target_install(target: Any, dest_root: Path, copied: Iterable[Path]) -> Path | None:
    """Record a target's install. Never fails the publish: a record that
    cannot be written is a warning."""
    try:
        directory = record_dir(dest_root)
        if directory is None:
            return None
        from . import read_record as reads

        recorded = reads.recorded()
        generator = target_generator(target)
        if recorded is None:
            # Not a recording publish: the authoring sources are the inputs known.
            recorded = [repo_root() / rel for rel in {generator["source"], generator["module_source"], *generator["data"]} if rel]
        return write_record(
            directory,
            target.name,
            generator=generator,
            dest=Path(dest_root),
            outputs=[(Path(path), None) for path in copied],
            inputs=_inputs(recorded),
        )
    except Exception as ex:  # noqa: BLE001 - a record never fails a publish
        print(f"[provenance] warning: no record for {getattr(target, 'name', target)}: {ex}", file=sys.stderr)
        return None


# ---- backgrounds and terrain -----------------------------------------------------------------


class Book:
    """The outputs of one background or terrain draw, by unit, with the
    callable that drew each. `write` records each unit."""

    def __init__(self, family: str, dest: Path, command: str) -> None:
        self.family = family
        self.dest = Path(dest)
        self.command = command
        self.units: dict[str, list[tuple[Path, dict[str, Any] | None]]] = {}

    def add(self, unit: str, path: Path, fn: Callable | None) -> None:
        self.units.setdefault(unit, []).append((Path(path), made_by(fn)))

    def write(self, *, basis: str = "rendered") -> list[Path]:
        try:
            directory = record_dir(self.dest)
            if directory is None:
                return []
            inputs = _inputs(renderer_modules(), hashed=basis == "rendered")
            return [
                write_record(
                    directory,
                    unit,
                    generator={"family": self.family, "id": unit, "command": self.command.format(unit=unit)},
                    dest=self.dest,
                    outputs=outputs,
                    inputs=inputs,
                    basis=basis,
                )
                for unit, outputs in self.units.items()
            ]
        except Exception as ex:  # noqa: BLE001 - a record never fails a publish
            print(f"[provenance] warning: no {self.family} records: {ex}", file=sys.stderr)
            return []

    def _write_plan(self, directory: Path) -> list[Path]:
        inputs = _inputs(renderer_modules(), hashed=False)
        return [
            write_record(
                directory,
                unit,
                generator={"family": self.family, "id": unit, "command": self.command.format(unit=unit)},
                dest=self.dest,
                outputs=outputs,
                inputs=inputs,
                basis="plan",
                # Nothing was rendered: the commit that drew these bytes is not known.
                extra={"renderer": None},
            )
            for unit, outputs in self.units.items()
        ]


# ---- backfill -------------------------------------------------------------------------------


def _sheet_cache(cache_dir: Path) -> dict[str, tuple[str, dict[str, str]]]:
    """`.cache/sheets/<target>`: the cache key, and the digest of each output."""
    out = {}
    sheets = cache_dir / "sheets"
    if not sheets.is_dir():
        return out
    for path in sheets.iterdir():
        lines = path.read_text().splitlines()
        if not lines:
            continue
        digests = {}
        for line in lines[1:]:
            if " " in line:
                sha, rel = line.split(" ", 1)
                digests[rel] = sha
        out[path.name] = (lines[0], digests)
    return out


def backfill_sprites(sprites_dir: Path, cache_dir: Path, directory: Path) -> tuple[int, int]:
    """Write a `cache` record for each target whose outputs on disk match the
    digests in `.cache/sheets` and that has no record vouching for them yet.
    The written and the skipped counts."""
    from .registry.discovery import discover_all_targets

    targets = discover_all_targets().targets
    written = skipped = 0
    for name, (key, digests) in sorted(_sheet_cache(cache_dir).items()):
        target = targets.get(name)
        if target is None or not digests:
            skipped += 1
            continue
        paths = [sprites_dir / rel for rel in digests]
        if not all(p.is_file() and digest(p) == digests[rel] for p, rel in zip(paths, digests)):
            skipped += 1
            continue
        existing = read_record(directory / f"{name}.json")
        if existing and {o["path"]: o["sha256"] for o in existing.get("outputs", [])} == digests:
            skipped += 1
            continue
        reads = cache_dir / "reads" / f"{name}.reads"
        recorded = [repo_root() / line[2:] for line in reads.read_text().splitlines() if line.startswith("f ")] if reads.is_file() else []
        write_record(
            directory,
            name,
            generator=target_generator(target),
            dest=sprites_dir,
            outputs=[(p, None) for p in paths],
            inputs=_inputs(recorded, hashed=False),
            basis="cache",
            # The commit of the render that made these bytes is not known here.
            extra={"cache_key": key, "renderer": None},
        )
        written += 1
    return written, skipped


def backfill_plan(book: Book, directory: Path) -> tuple[int, int]:
    """Write a `plan` record for each unit of `book` that has no record."""
    skipped = 0
    for unit in list(book.units):
        if read_record(directory / f"{unit}.json"):
            skipped += 1
            del book.units[unit]
    return len(book._write_plan(directory)), skipped


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ambition_sprite2d_renderer.provenance", description=__doc__.split("\n", 1)[0])
    sub = parser.add_subparsers(dest="command", required=True)
    fill = sub.add_parser("backfill", help="record already-published art that has no record yet")
    fill.add_argument("--families", default="sprites,backgrounds,sky_parts,terrain")
    args = parser.parse_args(argv)
    families = set(args.families.split(","))
    root = asset_root()
    if "sprites" in families:
        n, s = backfill_sprites(root / "sprites", _RENDERER / ".cache", provenance_root() / "sprites")
        print(f"sprites: {n} records written, {s} skipped (record current, no cache digest, or outputs changed)")
    if "backgrounds" in families:
        from .backgrounds.__main__ import plan as background_plan

        dest = root / "backgrounds" / "parallax_layers"
        n, s = backfill_plan(background_plan(dest, []), provenance_root() / "backgrounds" / "parallax_layers")
        print(f"backgrounds: {n} records written, {s} skipped")
    if "sky_parts" in families:
        from .backgrounds.__main__ import parts_plan

        dest = root / "backgrounds" / "sky_parts"
        n, s = backfill_plan(parts_plan(dest), provenance_root() / "backgrounds" / "sky_parts")
        print(f"sky parts: {n} records written, {s} skipped")
    if "terrain" in families:
        from .terrain.__main__ import plan as terrain_plan

        dest = root / "room_dressing"
        n, s = backfill_plan(terrain_plan(dest, []), provenance_root() / "room_dressing")
        print(f"terrain: {n} records written, {s} skipped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
