"""The authored files one target's render reads, for the publish's cache key.

`scripts/regen/sprites.sh` keys each sheet on the files it is made of. It
guessed the data half by name (a rig at `rigged/<name>.rig.json`, the
directory `data/characters/<name>/`), and a target that reads another
target's art (`gnu_ton_scholar_fighter` draws `gnu_ton_scholar_villain.svg`)
or a nested rig document kept its key when that file changed: a stale sheet
(review of 2026-10-14). The files a render opens are the answer, so the render
records them.

The record is exact only when the process has read nothing before the
target's own module: a second target that reads a shared SVG from an
in-process cache opens nothing, and a module that parses its rig when it is
imported opens it once, in whatever process imported it first. Discovery
imports every target module. So a recorded target is published by
[`publish_in_subprocess`]: a new interpreter that starts recording, imports
only that target's module (or reads its config) and publishes it.

What is recorded: each file under the repository that the render opens to
read, each directory it lists (a glob that finds a new file is a new input),
and each renderer module the process imported. Not recorded: other Python
source, the directories the import system lists, the tool's own environment
(`.venv`, which the toolchain fingerprint keys), the render's own outputs
(`generated/`, the destination root) and `.cache/`.

The modules are the render's code. The publish keyed every sheet on the
whole renderer core (68 files), so an edit to one of them made every sheet
stale: 56 min of renders (measured 2026-10-15). Ten sampled renders each
imported 15 to 69 of the core's files, and 35 of the files were imported by
none of them. The process imports only its target's module, so the modules
it has at the end are the code that ran.
A loose rig document is registered by `targets/characters/rigged.py`, which
reads every loose document when it is imported, so the record of each loose
rig target has all of them: more than it needs, never less.
"""

from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Iterable

#: Set by the publish: the directory that gets `<target>.reads`.
READS_ENV = "AMBITION_SPRITE_READS_DIR"

_WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC

_files: set[str] | None = None
_dirs: set[str] | None = None
_root = ""
_excluded: tuple[str, ...] = ()
_hooked = False


def _relative(path: object) -> str | None:
    if path is None or isinstance(path, int):
        return None
    try:
        real = os.path.realpath(os.fsdecode(path))
    except (TypeError, ValueError):
        return None
    if not real.startswith(_root + os.sep):
        return None
    if any(real == prefix or real.startswith(prefix + os.sep) for prefix in _excluded):
        return None
    parts = real.split(os.sep)
    if "__pycache__" in parts or ".venv" in parts or real.endswith((".py", ".pyc")):
        return None
    return os.path.relpath(real, _root)


def _from_the_import_system() -> bool:
    frame = sys._getframe(2)
    while frame is not None:
        if frame.f_code.co_filename.startswith("<frozen importlib"):
            return True
        frame = frame.f_back
    return False


def _hook(event: str, args: tuple) -> None:
    if _files is None or _dirs is None:
        return
    if event == "open":
        path, mode, flags = args
        if mode is not None:
            if any(char in mode for char in "wax+"):
                return
        elif flags & _WRITE_FLAGS:
            return
        if (rel := _relative(path)) is not None and os.path.isfile(os.path.join(_root, rel)):
            _files.add(rel)
    elif event in ("os.listdir", "os.scandir"):
        # The import system lists each package directory it searches. That
        # is the code, which the static import closure keys.
        if _from_the_import_system():
            return
        if (rel := _relative(args[0])) is not None:
            _dirs.add(rel)


def start(root: Path, excluded: Iterable[Path]) -> None:
    """Record from now on, in this process. An audit hook cannot be removed,
    so a process records at most one target's render."""
    global _files, _dirs, _root, _excluded, _hooked
    _root = os.path.realpath(root)
    _excluded = tuple(os.path.realpath(path) for path in excluded)
    _files, _dirs = set(), set()
    if not _hooked:
        sys.addaudithook(_hook)
        _hooked = True


def _modules() -> set[str]:
    """The renderer's Python files that this process imported, relative to
    the repository."""
    if not _root:
        return set()
    renderer = os.path.realpath(Path(__file__).resolve().parents[1])
    out = set()
    for module in list(sys.modules.values()):
        file = getattr(module, "__file__", None)
        if not file:
            continue
        real = os.path.realpath(file)
        parts = real.split(os.sep)
        if (
            real.endswith(".py")
            and real.startswith(renderer + os.sep)
            and real.startswith(_root + os.sep)
            and ".venv" not in parts
        ):
            out.add(os.path.relpath(real, _root))
    return out


def recorded() -> list[str] | None:
    """The files this process has recorded so far, as absolute paths, or
    None when it does not record (`provenance` keeps them as the render's inputs)."""
    if _files is None:
        return None
    return sorted(os.path.join(_root, rel) for rel in _files | _modules())


def directories() -> list[dict]:
    """The directory membership that a recorded publication used."""
    return [{"path": rel, "members": sorted(os.listdir(os.path.join(_root, rel)))}
            for rel in sorted(_dirs or ()) if os.path.isdir(os.path.join(_root, rel))]


def merge(files: list[str], directories: list[dict]) -> None:
    """Add the input observations of a rendering worker."""
    if _files is None or _dirs is None:
        return
    for path in files:
        rel = _relative(path)
        if rel:
            _files.add(rel)
        elif path.endswith(".py") and os.path.realpath(path).startswith(_root + os.sep):
            _files.add(os.path.relpath(os.path.realpath(path), _root))
    for item in directories:
        _dirs.add(item["path"])


def exclude(path: Path) -> None:
    global _excluded
    _excluded = (*_excluded, os.path.realpath(path))


def write(path: Path) -> None:
    """Write the record: `f <file>` and `d <directory>` lines, relative to the
    repository, sorted. Written whole, then moved into place."""
    files, dirs = sorted((_files or set()) | _modules()), sorted(_dirs or ())
    text = "".join(f"f {rel}\n" for rel in files) + "".join(f"d {rel}\n" for rel in dirs)
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(path.suffix + ".partial")
    partial.write_text(text)
    partial.replace(path)


def publish_in_subprocess(
    target: Any,
    out_dir: Path,
    dest_root: Path,
    opts: dict,
    reads_path: Path,
    root: Path,
    excluded: Iterable[Path],
) -> tuple[str | None, float]:
    """Publish `target` in a new interpreter that records its reads into
    `reads_path`: the failure text or None, and the seconds."""
    spec = {
        "name": target.name,
        "kind": target.kind,
        "category": target.category,
        "module_path": target.module_path,
        "config_path": str(target._config_path) if target._config_path else None,
        "lineup_row": getattr(target, "_lineup_row", False),
        "out_dir": str(out_dir),
        "dest_root": str(dest_root),
        "opts": opts,
        "reads": str(reads_path),
        "root": str(root),
        "excluded": [str(path) for path in excluded],
    }
    started = time.perf_counter()
    done = subprocess.run(
        [sys.executable, "-m", "ambition_sprite2d_renderer.read_record", json.dumps(spec)],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parents[1],
    )
    took = time.perf_counter() - started
    if done.returncode != 0:
        tail = (done.stderr or done.stdout).strip().splitlines()[-3:]
        return f"exit {done.returncode}: {' | '.join(tail)}", took
    return None, took


def _one_target(spec: dict) -> Any:
    """The one target `spec` names, built as discovery builds it, from its own
    module or config only."""
    from .registry import discovery

    if spec["kind"] == "config" and spec.get("lineup_row"):
        lineup = discovery._discover_faction_lineup(Path(spec["config_path"]))
        if spec["name"] not in lineup:
            raise SystemExit(f"{spec['config_path']} has no lineup row {spec['name']!r}")
        return lineup[spec["name"]]
    if spec["kind"] == "config":
        return discovery.Target.from_config(
            config_path=Path(spec["config_path"]), category=spec["category"]
        )
    dotted = spec["module_path"]
    stem = dotted.rsplit(".", 1)[-1]
    module = importlib.import_module(dotted)
    if isinstance(getattr(module, "TARGETS", None), dict):
        built = discovery._build_module_targets(module, stem, spec["category"], dotted, [])
        for target in built:
            if target.name == spec["name"]:
                return target
        raise SystemExit(f"{dotted} defines no target {spec['name']!r}")
    return discovery._build_module_target(module, stem, spec["category"], dotted, module.render)


def main(argv: list[str]) -> int:
    spec = json.loads(argv[0])
    start(Path(spec["root"]), [Path(path) for path in spec["excluded"]])
    target = _one_target(spec)
    out_dir, opts = Path(spec["out_dir"]), spec["opts"]
    target._publish_parameters = opts
    target.render_sheet(out_dir, **opts)
    if target.supports_portraits:
        target.render_portraits(out_dir, **opts)
    target.install(out_dir, Path(spec["dest_root"]))
    write(Path(spec["reads"]))
    return 0


if __name__ == "__main__":
    from ambition_sprite2d_renderer import read_record as recorder
    sys.exit(recorder.main(sys.argv[1:]))
