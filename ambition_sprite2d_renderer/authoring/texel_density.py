"""How many sheet pixels a character has per unit of the game's world.

A character's size in the game does not come from its frame's pixels: the
game reads its body box against the height it stands in the world (a catalog
``standing_height``, a boss's body box). So its resolution is free, and this
is the one number that sets it.

The default camera (``CameraZoomPreset::Duel``) shows 320 world units of
height; on a 1080-pixel window that is 3.375 screen pixels per unit. A sheet
at that density is drawn one sheet pixel to one screen pixel there; below it
the game magnifies the sheet and it is soft (the median character was 1.75,
measured 2026-10-17). A quality tier (``sprites_0_5x``) halves it again.
"""

from __future__ import annotations

import math
from typing import Tuple

#: Sheet pixels per world unit at the full tier.
TEXELS_PER_WORLD_UNIT = 3.4


def published_frame(frame: Tuple[int, int], body_px: float, world_height: float, density: float = TEXELS_PER_WORLD_UNIT) -> Tuple[int, int]:
    """The frame a character drawn on ``frame`` (its own pixels, the body
    ``body_px`` of them tall) is published at, so its body of ``world_height``
    units has ``density`` pixels per unit. Never smaller than ``frame``, and
    even, so a frame centre stays on a pixel edge."""
    f = max(1.0, density * world_height / body_px)
    return tuple(2 * int(math.ceil(v * f / 2.0)) for v in frame)  # type: ignore[return-value]
