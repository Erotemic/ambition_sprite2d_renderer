"""The colours of South Asia and East Asia in the History dimension's grid.

The second pass of the History dimension is a grid: each floor is a region
of the world, and the rooms of one column are of one time. This module is
for the creatures of two floors:

- South Asia: the southern route, Mehrgarh, and the cities of the Indus
  (biome `history_indus`): warm red brick, river silt, the pale steatite of
  the seals, monsoon grey;
- East Asia: the Yellow River and the Shang court (biome
  `history_yellow_river`): loess yellow, the green of old bronze, jade,
  cinnabar red, the cream of oracle bone.

The cast is drawn on the kit of the Art dimension (`_art_cast_kit.py`):
cel shapes, flat colour with one shade, and one thick dark outline round
each silhouette. This module also gives :func:`enemy_metadata` (the sidecar
with the tags of this dimension and of a floor) and :func:`alarm_mark`. It
draws nothing by itself.
"""

from __future__ import annotations

import math
from typing import Sequence

from . import _art_cast_kit as K

#: The ink of the dimension: the dark brown of a printed textbook.
SEPIA_INK = (48, 30, 22, 255)
PAPER = (244, 232, 204, 255)
MAP_RED = (206, 58, 40, 255)

# -- South Asia ---------------------------------------------------------------
BRICK = (196, 104, 70, 255)
BRICK_LIGHT = (226, 146, 104, 255)
BRICK_DARK = (138, 66, 44, 255)
SILT = (208, 178, 132, 255)
SILT_DARK = (156, 126, 86, 255)
#: Steatite: the soft stone of the seals, fired white.
STEATITE = (238, 228, 204, 255)
STEATITE_SHADE = (196, 180, 150, 255)
STEATITE_DARK = (132, 116, 92, 255)
#: The faience and the carnelian of Indus beads.
FAIENCE = (64, 168, 170, 255)
CARNELIAN = (204, 82, 52, 255)

# -- East Asia ----------------------------------------------------------------
LOESS = (222, 186, 112, 255)
LOESS_DARK = (170, 132, 70, 255)
#: Old bronze: green with verdigris, and the bright metal where it is worn.
BRONZE_GREEN = (82, 150, 120, 255)
BRONZE_GREEN_LIGHT = (150, 206, 170, 255)
BRONZE_GREEN_DARK = (40, 94, 78, 255)
BRONZE_GREEN_DEEP = (24, 60, 52, 255)
BRONZE_BRIGHT = (214, 160, 76, 255)
JADE = (110, 186, 140, 255)
CINNABAR = (204, 48, 40, 255)
CINNABAR_DARK = (140, 28, 26, 255)
BONE = (240, 226, 196, 255)
BONE_SHADE = (198, 178, 140, 255)


def enemy_metadata(character_id: str, display_name: str, body_plan: str, body_kind: str, mass: str, locomotion: str,
                   traits: Sequence[str], description: str, region: str) -> dict:
    """The actor sidecar of an enemy of the History dimension: the Art kit's
    sidecar, with the tags of this dimension and of its floor (`region` is
    ``south_asia`` or ``east_asia``)."""
    meta = K.enemy_metadata(character_id, display_name, body_plan, body_kind, mass, locomotion, traits, description)
    meta["tags"] = ["enemy", "history", region]
    return meta


def alarm_mark(f: K.Frame, x: float, y: float) -> None:
    """The "!" over a creature that sees you: map red, as a mark on a map."""
    f.limb([(x, y - 10.0), (x, y)], 2.6, MAP_RED)
    f.ellipse(x, y + 5.0, 1.7, 1.7, MAP_RED)


def mix(a, b, u: float):
    """The colour `u` of the way from `a` to `b`."""
    u = max(0.0, min(1.0, u))
    return tuple(int(a[j] + (b[j] - a[j]) * u) for j in range(3)) + (int(a[3] + (b[3] - a[3]) * u),)


def wave(t: float, k: float = 1.0, offset: float = 0.0) -> float:
    """A sine of a loop: `k` turns over the row."""
    return math.sin(math.tau * (t * k) + offset)
