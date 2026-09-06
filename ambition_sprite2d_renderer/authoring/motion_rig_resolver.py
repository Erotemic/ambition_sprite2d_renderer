"""Read-only rig resolution for agent-facing motion authoring tools.

Motion inspection and local pose editing should not regenerate source assets as
an incidental side effect.  In particular, canonical scientist targets have a
builder lifecycle used by publication/audit tooling, but a motion review should
prefer an already-authored rig document when one exists.

This resolver therefore searches published rig JSON only.  If no existing rig
can be resolved unambiguously it raises with guidance to pass ``--rig`` rather
than invoking a generator behind the caller's back.
"""

from __future__ import annotations

import json
from pathlib import Path


def _rig_root() -> Path:
    package_root = Path(__file__).resolve().parents[1]
    return package_root / "targets" / "characters" / "rigged"


def _existing_explicit(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise FileNotFoundError(resolved)
    return resolved


def _document_name(path: Path) -> str | None:
    try:
        data = json.loads(path.read_text(encoding="utf8"))
    except (OSError, json.JSONDecodeError):
        return None
    name = data.get("name")
    return str(name) if name is not None else None


def find_existing_rig_document(target: str, *, explicit: Path | None = None) -> Path:
    """Resolve an existing rig without running any rig/source generator.

    Resolution order intentionally mirrors authored ownership:

    1. caller-provided ``--rig``;
    2. target-specific published rig directory;
    3. legacy loose exact-name rig;
    4. a single existing rig whose document ``name`` equals ``target``.

    Unlike :func:`pose_audit.find_rig_document`, this function never freshness-
    checks or rebuilds canonical SVG fighters.  Read-only diagnostics and local
    edits should be stable even while source SVG ownership is temporarily being
    edited by another agent.
    """

    if explicit is not None:
        return _existing_explicit(Path(explicit))

    rig_root = _rig_root()
    preferred = [
        rig_root / target / f"{target}.rig.json",
        rig_root / target / f"{target}_side.rig.json",
        rig_root / target / f"{target}_three_quarter.rig.json",
        rig_root / target / f"{target}_front.rig.json",
        rig_root / f"{target}.rig.json",
    ]
    for path in preferred:
        if path.is_file():
            return path.resolve()

    matches: list[Path] = []
    if rig_root.is_dir():
        for path in rig_root.rglob("*.rig.json"):
            if _document_name(path) == target:
                matches.append(path.resolve())

    unique = sorted(set(matches))
    if len(unique) == 1:
        return unique[0]
    if len(unique) > 1:
        raise ValueError(
            f"multiple existing rig documents match {target!r}: "
            + ", ".join(str(path) for path in unique)
            + "; pass --rig to choose one explicitly"
        )
    raise FileNotFoundError(
        f"no existing rig document found for target {target!r} under {rig_root}; "
        "motion tools do not regenerate rigs implicitly, so pass --rig or build/publish the rig first"
    )


__all__ = ["find_existing_rig_document"]
