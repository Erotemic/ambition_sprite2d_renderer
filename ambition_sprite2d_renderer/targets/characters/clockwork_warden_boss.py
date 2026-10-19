"""The Clockwork Warden: one of the three sentinel bosses, the look ``clockwork_warden``.

Worn by the Clockwork Warden. Jon, 2026-10-18, of three redraws of the generic v1 boss:
"for the boss all 3 are good and each can be used to make some of the non
unique bosses unique-ish". The skeleton, rows and hitboxes are shared
(``_sentinel_boss``).
"""

from __future__ import annotations

from pathlib import Path

from . import _sentinel_boss

TARGET_NAME = "clockwork_warden_boss"

ACTOR_METADATA = _sentinel_boss.actor_metadata(TARGET_NAME, "Clockwork Warden", [
    'A brass and verdigris automaton: a riveted cowl, a brass face with a grille mouth, three lens eyes.',
    'A gear halo that turns, a bell of lamellar plates with a clock for a heart, a pendulum swinging under it.',
    'Jointed brass arms with piston rods, steel pincers for hands.',
])


def render(out_dir: str | Path, **opts):
    del opts
    return _sentinel_boss.render(TARGET_NAME, ACTOR_METADATA, out_dir)


__all__ = ["ACTOR_METADATA", "TARGET_NAME", "render"]
