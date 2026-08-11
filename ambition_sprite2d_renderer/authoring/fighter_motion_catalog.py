"""Canonical fighter-motion vocabulary and current-art coverage validation.

The vocabulary is data, not a renderer enum: it records the long-term motion
surface without forcing every character to draw every variation immediately.
Character profiles map the applicable current-art ``category`` values to rows.
"""

from __future__ import annotations

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
    "load_fighter_motion_catalog",
    "motion_entries",
    "validate_motion_coverage",
]
