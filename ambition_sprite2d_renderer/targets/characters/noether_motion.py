"""Noether full-fighter motion rows and current-art coverage.

The canonical long-term vocabulary lives in ``data/fighter_motion_vocabulary.yaml``.
This profile gives Noether one current-art row for every applicable fighter and
generic held-item category while keeping her character-specific specials named
for symmetry, invariants, conservation laws, and the ethereal traversal motif.
"""

from __future__ import annotations

from typing import Final

from .patent_clerk_motion import (
    FIGHTER_MOTION_COVERAGE as _BASE_COVERAGE,
    PATENT_ROWS as _BASE_ROWS,
)

# Reuse the established current-art fighter surface (frame counts and timings)
# without inheriting Patent Clerk's character-specific semantic names.
_SIGNATURE_RENAMES: Final[dict[str, str]] = {
    "known_result": "invariant_parry",
    "application_review": "symmetry_proof",
    "margin_correction": "generator_strike",
    "light_argument": "conservation_law",
    "reference_frame": "symmetry_shift",
    "elevator_thought": "ethereal_lift",
    "synchronize_clocks": "invariant_field",
    "mass_energy_conversion": "symmetry_break",
    "annus_mirabilis": "noether_theorem",
}

NOETHER_ROWS: Final[tuple[tuple[str, int, int], ...]] = tuple(
    (_SIGNATURE_RENAMES.get(name, name), frames, duration)
    for name, frames, duration in _BASE_ROWS
)

FIGHTER_MOTION_COVERAGE: Final[dict[str, str]] = {
    category: _SIGNATURE_RENAMES.get(row, row)
    for category, row in _BASE_COVERAGE.items()
}

APPLICABLE_MOTION_SCOPES: Final[tuple[str, ...]] = ("fighter_core", "generic_item")

EFFECT_ALIASES: Final[dict[str, str]] = {
    "attack_side": "generator_strike",
    "smash_forward": "symmetry_break",
    "special_neutral": "conservation_law",
    "special_side": "symmetry_shift",
    "special_up": "ethereal_lift",
    "special_down": "invariant_field",
    "final_smash": "noether_theorem",
    "parry": "invariant_parry",
}

__all__ = [
    "APPLICABLE_MOTION_SCOPES",
    "EFFECT_ALIASES",
    "FIGHTER_MOTION_COVERAGE",
    "NOETHER_ROWS",
]
