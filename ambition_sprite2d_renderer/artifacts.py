"""Resolve a producer's declared products and their file references."""
from __future__ import annotations

import json
from pathlib import Path
import re
import shutil

from .publication_store import relative


def references(path: Path) -> list[str]:
    """Read page references from the published metadata formats."""
    if path.suffix == ".ron":
        text = path.read_text()
        fields = re.findall(r'\b(?:pages|images)\s*:\s*\[([^\]]*)\]|\bimage\s*:\s*("(?:[^"\\]|\\.)*")', text)
        return list(dict.fromkeys(json.loads(word) for group in fields for part in group
                                  for word in re.findall(r'"(?:[^"\\]|\\.)*"', part)))
    if path.suffix in (".yaml", ".yml", ".json"):
        if path.suffix == ".json":
            value = json.loads(path.read_text())
        else:
            from .yaml_io import safe_load
            value = safe_load(path.read_text())
        found = []
        def visit(value):
            if isinstance(value, dict):
                for key, item in value.items():
                    if key in ("image", "images", "pages"):
                        found.extend([item] if isinstance(item, str) else [v for v in item if isinstance(v, str)] if isinstance(item, list) else [])
                    else:
                        visit(item)
            elif isinstance(value, list):
                for item in value:
                    visit(item)
        visit(value)
        return list(dict.fromkeys(found))
    return []


#: What a sheet file brings beside it when it is installed, if it was rendered.
COMPANION_SUFFIXES = ("_actor.ron", "_body_rig.ron", "_parts.ron")


def companion_names(name: str) -> list[str]:
    """The optional files installed beside sheet file ``name``: the install's
    rule, and so the rule for what an installed file belongs to."""
    if not name.endswith(("_spritesheet.ron", "_spritesheet.yaml", "_spritesheet.png")):
        return []
    stem = name.split("_spritesheet")[0]
    return [stem + suffix for suffix in COMPANION_SUFFIXES]


def required_names(target, *, portraits: bool = True) -> list[str]:
    names = list(target.sheet_files) + (list(target.portrait_files) if portraits else [])
    names += [name.removesuffix(".yaml") + ".ron" for name in names if name.endswith("_spritesheet.yaml")]
    # Discovery can infer an actor descriptor for a target with no sheet.
    return list(dict.fromkeys(name for name in names if not name.endswith("_actor.ron")
            and not name.endswith(("_canonical.png", "_canonical_transparent.png", "_preview_labeled.png", "_debug.png"))))


def collect(target, directory: Path, *, portraits: bool = True) -> dict[str, Path]:
    """Find declared files in a clean render directory. References are required."""
    by_name = {}
    for path in directory.rglob("*"):
        if path.is_file():
            by_name.setdefault(path.name, []).append(path)
    result = {}
    def add(name: str, prefix: str = "", *, optional: bool = False):
        relative(name)
        paths = by_name.get(Path(name).name, [])
        exact = directory / name
        source = exact if exact.is_file() else paths[0] if len(paths) == 1 else None
        if source is None:
            if optional and not paths:
                return
            raise ValueError(f"{target.name}: missing or ambiguous product {name}")
        logical = (Path(prefix) / name).as_posix()
        if logical in result:
            return
        result[logical] = source
        for page in references(source):
            page_source = source.parent / relative(page)
            if not page_source.is_file():
                raise ValueError(f"{target.name}: {source.name} names missing page {page}")
            result[(Path(logical).parent / page).as_posix()] = page_source
    for name in required_names(target, portraits=portraits):
        prefix = target.portrait_install_subdir if name in target.portrait_files else target.install_subdir
        add(name, prefix or "")
        for companion in companion_names(name):
            add(companion, prefix or "", optional=True)
    return result


def install(target, directory: Path, destination: Path, *, portraits: bool = True) -> list[Path]:
    """Install the same resolved membership used by bundle acceptance."""
    products = collect(target, directory, portraits=portraits)
    copied = []
    for logical, source in products.items():
        path = destination / logical
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.is_symlink():
            path.unlink()
        shutil.copyfile(source, path)
        copied.append(path)
    return copied
