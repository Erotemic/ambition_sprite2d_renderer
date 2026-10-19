"""The Gradient Sentinel: one of the three sentinel bosses, the look ``gradient_sentinel``.

Worn by the boss every boss without art of its own wears (the ``gradient_sentinel`` sheet
key), and the hall's "Boss". Jon, 2026-10-18, of three redraws of the generic v1 boss:
"for the boss all 3 are good and each can be used to make some of the non
unique bosses unique-ish". The skeleton, rows and hitboxes are shared
(``_sentinel_boss``).
"""

from __future__ import annotations

from pathlib import Path

from . import _sentinel_boss

TARGET_NAME = "gradient_sentinel_boss"

ACTOR_METADATA = _sentinel_boss.actor_metadata(TARGET_NAME, "Gradient Sentinel", [
    'An eldritch shroud: a tall hood whose peak droops back, a white mask with two cyan eyes and a third on the brow.',
    'A crown of spikes behind the head; the hem in stepped bands, the contour lines of a loss surface.',
    'Boneless tendril arms with long white fingers.',
])


def render(out_dir: str | Path, **opts):
    del opts
    return _sentinel_boss.render(TARGET_NAME, ACTOR_METADATA, out_dir)


__all__ = ["ACTOR_METADATA", "TARGET_NAME", "render"]
