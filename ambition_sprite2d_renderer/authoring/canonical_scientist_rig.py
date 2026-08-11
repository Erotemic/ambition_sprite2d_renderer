"""Canonical rig lifecycle for manually traced scientist paperdolls.

The checked-in SVG is the source of truth. Generated rig JSON is accepted only
when it records native ``resvg_py`` provenance and the hash of the current SVG.
Older CairoSVG-derived rigs are therefore rebuilt automatically rather than
silently reused.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping

from .rigdoc import RigDocument

ROOT = Path(__file__).resolve().parents[2]
BUILDER_PATH = ROOT / "scripts" / "build_scientist_fighter_rigs.py"
EXPECTED_SCHEMA = "canonical-svg-rig-v3"
EXPECTED_BUILDER_VERSION = 17

_SVG_NAMES = {
    "patent_clerk": "patent-clerk.svg",
    "carl_stargan": "carl-stargan.svg",
}
_RIG_NAMES = {
    "patent_clerk": "patent_clerk_side.rig.json",
    "carl_stargan": "carl_stargan_side.rig.json",
}


def svg_path(character: str) -> Path:
    try:
        filename = _SVG_NAMES[character]
    except KeyError as ex:
        raise KeyError(f"unknown canonical scientist fighter {character!r}") from ex
    return ROOT / "assets" / filename


def rig_path(character: str) -> Path:
    try:
        filename = _RIG_NAMES[character]
    except KeyError as ex:
        raise KeyError(f"unknown canonical scientist fighter {character!r}") from ex
    return (
        ROOT
        / "ambition_sprite2d_renderer"
        / "targets"
        / "characters"
        / "rigged"
        / character
        / filename
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json(path: Path) -> Mapping[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None
    return value if isinstance(value, dict) else None


def rig_status(character: str) -> tuple[bool, str]:
    """Return whether the generated rig is current and why."""

    source = svg_path(character)
    generated = rig_path(character)
    if not source.exists():
        return False, f"missing canonical SVG: {source}"
    document = _read_json(generated)
    if document is None:
        return False, f"missing or invalid generated rig: {generated}"
    provenance = document.get("build_provenance")
    if not isinstance(provenance, dict):
        return False, "generated rig has no native-renderer provenance"
    if provenance.get("schema") != EXPECTED_SCHEMA:
        return False, f"unexpected rig provenance schema: {provenance.get('schema')!r}"
    if provenance.get("builder_version") != EXPECTED_BUILDER_VERSION:
        return False, f"stale rig builder version: {provenance.get('builder_version')!r}"
    if provenance.get("renderer") != "resvg_py":
        return False, f"rig was built by unsupported renderer: {provenance.get('renderer')!r}"
    if not provenance.get("renderer_version"):
        return False, "rig does not record the native renderer version"
    if provenance.get("svg_sha256") != _sha256(source):
        return False, "canonical SVG changed after the rig was generated"
    if provenance.get("part_order") != "svg-document":
        return False, "generated rig does not preserve canonical SVG document order"
    return True, "current"


def _load_builder() -> ModuleType:
    if not BUILDER_PATH.exists():
        raise FileNotFoundError(BUILDER_PATH)
    spec = importlib.util.spec_from_file_location(
        "_ambition_scientist_fighter_rig_builder",
        BUILDER_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import rig builder from {BUILDER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def ensure_scientist_rig(character: str) -> Path:
    """Return a current rig, rebuilding stale output with native resvg."""

    current, _reason = rig_status(character)
    if current:
        return rig_path(character)

    builder = _load_builder()
    try:
        character_spec = builder.SPECS[character]
    except (AttributeError, KeyError) as ex:
        raise RuntimeError(f"builder has no specification for {character!r}") from ex
    built = Path(builder.build_one(character_spec))
    current, reason = rig_status(character)
    if not current:
        raise RuntimeError(
            f"native rig build for {character} did not produce current output: {reason}"
        )
    return built


def load_scientist_rig(character: str) -> RigDocument:
    return RigDocument.load(ensure_scientist_rig(character))
