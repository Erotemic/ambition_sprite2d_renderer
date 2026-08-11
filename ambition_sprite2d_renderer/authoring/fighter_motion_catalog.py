"""Canonical fighter-motion vocabulary and current-art coverage validation.

The vocabulary is data, not a renderer enum: it records the long-term motion
surface without forcing every character to draw every variation immediately.
Character profiles map the applicable current-art ``category`` values to rows.
"""

from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import yaml


CATALOG_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "fighter_motion_vocabulary.yaml"
)


@lru_cache(maxsize=1)
def load_fighter_motion_catalog() -> dict:
    value = yaml.safe_load(CATALOG_PATH.read_text(encoding="utf8"))
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise ValueError(f"invalid fighter motion catalog: {CATALOG_PATH}")
    return value


def motion_entries() -> tuple[dict, ...]:
    data = load_fighter_motion_catalog()
    entries = [*data.get("motions", []), *data.get("ambition_extensions", [])]
    if not all(isinstance(entry, dict) for entry in entries):
        raise ValueError("fighter motion catalog entries must be mappings")
    return tuple(entries)


def applicable_categories(scopes: Iterable[str]) -> frozenset[str]:
    scope_set = frozenset(str(scope) for scope in scopes)
    return frozenset(
        str(entry["category"])
        for entry in motion_entries()
        if str(entry.get("scope")) in scope_set
    )



def materialize_motion_rows(
    *,
    rows: Sequence[tuple[str, int, int]],
    clips: Mapping[str, dict],
    aliases: Mapping[str, str],
    looping_rows: Iterable[str] = (),
    character: str,
    keep_extra: bool = False,
) -> dict[str, dict]:
    """Return one clip per declared row, cloning aliases only when needed.

    Existing authored clips always win. Missing rows may borrow an established
    source clip through ``aliases``; because rig channels are normalized over
    ``t`` the clone can safely publish with a different frame count or duration.
    This is the current-art seam used when a fighter needs complete semantic
    coverage before every variation deserves bespoke choreography.
    """

    declared = {str(name): (int(frames), int(duration)) for name, frames, duration in rows}
    out = {str(name): deepcopy(clip) for name, clip in clips.items() if str(name) in declared}
    looping = frozenset(str(name) for name in looping_rows)

    unresolved = [name for name in declared if name not in out]
    while unresolved:
        progressed = False
        for name in list(unresolved):
            source = aliases.get(name)
            if source is None or source not in out:
                continue
            frames, duration = declared[name]
            clip = deepcopy(out[source])
            clip["frames"] = frames
            clip["duration_ms"] = duration
            clip["loop"] = name in looping
            out[name] = clip
            unresolved.remove(name)
            progressed = True
        if not progressed:
            break

    if unresolved:
        missing_aliases = {name: aliases.get(name) for name in unresolved}
        raise ValueError(
            f"{character} cannot materialize fighter rows: {missing_aliases}"
        )

    ordered = {name: out[name] for name, _frames, _duration in rows}
    if keep_extra:
        for name, clip in clips.items():
            if str(name) not in ordered:
                ordered[str(name)] = deepcopy(clip)
    return ordered


def invert_rotation_channel(clip: Mapping[str, object], channel: str) -> dict:
    """Clone ``clip`` and reverse the sign of one angular channel.

    This is useful for the minimum genuinely directional distinction we retain
    even at the current-art level: a backward roll should rotate backward, not
    merely be a forward-roll clip published under another name.
    """

    out = deepcopy(dict(clip))
    channels = out.get("channels")
    if not isinstance(channels, dict):
        return out
    spec = channels.get(channel)
    if not isinstance(spec, dict):
        return out
    if "const" in spec:
        spec["const"] = -float(spec["const"])
    if "keys" in spec and isinstance(spec["keys"], list):
        for key in spec["keys"]:
            if isinstance(key, list) and len(key) >= 2 and isinstance(key[1], (int, float)):
                key[1] = -float(key[1])
    if "expr" in spec:
        spec["expr"] = f"-({spec['expr']})"
    return out

def validate_motion_coverage(
    *,
    row_names: Sequence[str] | set[str],
    coverage: Mapping[str, str],
    scopes: Iterable[str],
    character: str,
) -> None:
    """Require exactly one current-art decision for every applicable category.

    Several categories may deliberately resolve to the same row. That is how a
    current fighter stays compact while the catalog retains eventual variants.
    """

    rows = frozenset(str(name) for name in row_names)
    required = applicable_categories(scopes)
    actual = frozenset(str(category) for category in coverage)
    missing = required - actual
    extra = actual - required
    missing_rows = {
        str(category): str(row)
        for category, row in coverage.items()
        if str(row) not in rows
    }
    if missing or extra or missing_rows:
        raise ValueError(
            f"{character} fighter motion coverage mismatch: "
            f"missing_categories={sorted(missing)}, "
            f"extra_categories={sorted(extra)}, "
            f"missing_rows={missing_rows}"
        )


__all__ = [
    "CATALOG_PATH",
    "applicable_categories",
    "invert_rotation_channel",
    "load_fighter_motion_catalog",
    "materialize_motion_rows",
    "motion_entries",
    "validate_motion_coverage",
]
