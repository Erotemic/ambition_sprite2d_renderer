"""The drawing kit of the cast of the first two eras of the History dimension.

The History dimension is a timeline. Its first two eras are the Fertile
Crescent (biome `history_crescent`) and the Nile (biome `history_nile`).
Their cast is drawn on the kit of the Art dimension's cast
(`_art_cast_kit.py`): flat colour with one shade, and one bold dark outline
round the silhouette. This module adds four things:

- the colours of the two eras: the sepia of an old textbook, and the accent
  colours of each era;
- :func:`enemy_metadata`, the actor sidecar of an enemy of the dimension
  (the sidecar of the Art kit, with the tags of this dimension);
- :func:`alarm_mark`, the "!" over a creature that sees you;
- :func:`dust`, a puff of dust on the ground.

Each figure faces right and stands with its feet on its ground row.
"""

from __future__ import annotations

import math
import random
from typing import Sequence

from . import _art_cast_kit as K

#: The common palette: the warm sepia of an old textbook.
SEPIA = (196, 160, 112, 255)
SEPIA_LIGHT = (232, 210, 168, 255)
SEPIA_DARK = (128, 96, 60, 255)
#: The outline of the cast: a dark sepia ink.
OUTLINE = (44, 28, 22, 255)

#: The Fertile Crescent.
MUDBRICK = (198, 150, 98, 255)
MUDBRICK_SHADE = (150, 104, 64, 255)
WHEAT = (236, 196, 92, 255)
WHEAT_SHADE = (190, 146, 56, 255)
RIVER_TEAL = (58, 156, 150, 255)
LAPIS = (40, 72, 168, 255)
LAPIS_LIGHT = (96, 134, 220, 255)
BRONZE = (196, 132, 64, 255)
BRONZE_DARK = (128, 80, 36, 255)

#: The Nile.
SANDSTONE = (226, 192, 132, 255)
SANDSTONE_SHADE = (180, 140, 88, 255)
PAPYRUS = (104, 164, 74, 255)
NILE_BLUE = (52, 128, 196, 255)
GOLD = (240, 190, 60, 255)
GOLD_DARK = (172, 118, 28, 255)
LINEN = (232, 222, 196, 255)
LINEN_SHADE = (186, 170, 136, 255)

#: The "!" of a creature that sees you: red ochre.
ALARM = (214, 64, 40, 255)


def enemy_metadata(character_id: str, display_name: str, era: str, body_plan: str, body_kind: str, mass: str, locomotion: str,
                   traits: Sequence[str], description: str) -> dict:
    """The actor sidecar of an enemy of the History dimension. `era` is
    ``crescent`` or ``nile``."""
    meta = K.enemy_metadata(character_id, display_name, body_plan, body_kind, mass, locomotion, traits, description)
    meta["tags"] = ["enemy", "history", era]
    return meta


def alarm_mark(f: K.Frame, x: float, y: float) -> None:
    """The "!" over the head of a creature that sees you."""
    f.limb([(x, y - 10.0), (x, y)], 2.8, ALARM)
    f.ellipse(x, y + 5.5, 1.8, 1.8, ALARM)


def dust(f: K.Frame, x: float, y: float, amount: float, seed: str, colour=SEPIA_LIGHT, spread: float = 1.0) -> None:
    """A puff of dust on the ground at `(x, y)`: `amount` 0..1 sets its size."""
    if amount <= 0.02:
        return
    rng = random.Random(seed)
    for k in range(5):
        dx = rng.uniform(-10.0, 10.0) * spread
        r = (3.0 + rng.uniform(0.0, 3.0)) * amount
        f.ellipse(x + dx, y - r * 0.6 - rng.uniform(0.0, 3.0) * amount, r, r * 0.75, K.alpha(colour, 0.55 + 0.3 * amount), body=False)


def wave(t: float, k: float = 1.0, offset: float = 0.0) -> float:
    """A sine of a loop: `k` turns over the row."""
    return math.sin(math.tau * (t * k) + offset)
