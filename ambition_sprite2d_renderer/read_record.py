"""Record source files read by one isolated render worker.

The worker starts recording before it loads its target. This includes shared
art and modules loaded at import time. Source membership records absent inputs.
The publication owner copies these sources before it starts the worker.
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




