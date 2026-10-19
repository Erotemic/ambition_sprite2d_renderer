"""The Hooded Sentinel: one of the three sentinel bosses, the look ``hooded_sentinel``.

Worn by Mode Collapse. Jon, 2026-10-18, of three redraws of the generic v1 boss:
"for the boss all 3 are good and each can be used to make some of the non
unique bosses unique-ish". The skeleton, rows and hitboxes are shared
(``_sentinel_boss``).
"""

from __future__ import annotations

from pathlib import Path

from . import _sentinel_boss

TARGET_NAME = "hooded_sentinel_boss"

ACTOR_METADATA = _sentinel_boss.actor_metadata(TARGET_NAME, "Hooded Sentinel", [
    "The old generic boss's wraith, redrawn: a deep cowl, a bone mask, three glowing magenta eyes, a toothed grin.",
    'A ragged cloak trailing to a tail, a magenta core gem at the collar.',
    'Jointed arms studded with glowing joints, three white claws.',
])


def render(out_dir: str | Path, **opts):
    del opts
    return _sentinel_boss.render(TARGET_NAME, ACTOR_METADATA, out_dir)


__all__ = ["ACTOR_METADATA", "TARGET_NAME", "render"]
