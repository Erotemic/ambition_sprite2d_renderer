"""The drawing kit of the cast of the History dimension.

The cast of the History dimension is drawn in the house style of the Art
dimension's cast (`_art_cast_kit.py`): flat colour with one shade and one
bold dark outline round the silhouette. This module adds what the History
cast uses and the Art kit does not have:

- the palette of the dimension: the warm sepia of an old textbook, and the
  accent colours of each era;
- :func:`enemy_metadata`, the actor sidecar of an enemy of the dimension
  (the Art kit's sidecar, with the tags of this dimension);
- :func:`leg` and :func:`arm`, which draw a limb of a figure through a
  :class:`~._stage_kit.Pen` with two-bone inverse kinematics;
- :func:`alarm_mark` and :func:`dust`, the "!" of a figure that sees you
  and a puff of dust or of clay.

Each figure faces right and stands with its feet on its ground row.
"""

from __future__ import annotations

import math
import random
from typing import Sequence, Tuple

from . import _art_cast_kit as K
from . import _stage_kit as S

Point = Tuple[float, float]

#: The ink of the dimension: a warm dark brown, as the ink of an old book.
SEPIA_INK = (46, 30, 22, 255)
SEPIA = (214, 186, 140, 255)
SEPIA_SHADE = (168, 136, 96, 255)
SKIN = (226, 176, 132, 255)
SKIN_SHADE = (184, 132, 94, 255)
SKIN_DARK = (176, 120, 84, 255)
SKIN_DARK_SHADE = (132, 84, 56, 255)

#: The Classical Shore: white marble, terracotta red, olive green, Aegean blue.
MARBLE = (240, 236, 226, 255)
MARBLE_SHADE = (190, 184, 172, 255)
TERRACOTTA = (196, 92, 56, 255)
TERRACOTTA_DARK = (138, 56, 32, 255)
OLIVE = (112, 128, 58, 255)
OLIVE_DARK = (74, 86, 36, 255)
AEGEAN = (40, 110, 170, 255)
AEGEAN_DARK = (22, 66, 112, 255)
BRONZE = (204, 144, 62, 255)
BRONZE_DARK = (134, 88, 34, 255)
BRONZE_LIGHT = (246, 206, 128, 255)
CRIMSON = (178, 36, 40, 255)
CRIMSON_DARK = (112, 20, 26, 255)

#: The Silk Road: dune ochre, crimson, saffron, jade, indigo night.
OCHRE = (214, 160, 84, 255)
OCHRE_DARK = (160, 108, 48, 255)
SAFFRON = (240, 168, 40, 255)
JADE = (60, 150, 112, 255)
JADE_DARK = (32, 98, 72, 255)
INDIGO = (52, 52, 112, 255)
INDIGO_DARK = (30, 28, 70, 255)
STEEL = (206, 210, 220, 255)
STEEL_SHADE = (130, 136, 156, 255)
CLAY = (164, 124, 98, 255)
CLAY_SHADE = (118, 86, 66, 255)
CLAY_LIGHT = (196, 160, 132, 255)


def enemy_metadata(character_id: str, display_name: str, body_plan: str, body_kind: str, mass: str, locomotion: str,
                   traits: Sequence[str], description: str, era: str) -> dict:
    """The actor sidecar of an enemy of the History dimension: the Art kit's
    sidecar, with the tags of this dimension and of its era."""
    meta = K.enemy_metadata(character_id, display_name, body_plan, body_kind, mass, locomotion, traits, description)
    meta["tags"] = ["enemy", "history", era]
    return meta


def leg(pen: S.Pen, hip: Point, foot: Point, thigh: float, shin: float, width: float, colour, knee_out: float = -1.0):
    """A leg from `hip` to `foot` (the ankle). Returns the knee and the ankle."""
    knee, ankle = S.joint(hip, foot, thigh, shin, knee_out)
    pen.limb([hip, knee, ankle], width, colour)
    return knee, ankle


def arm(pen: S.Pen, shoulder: Point, hand: Point, upper: float, fore: float, width: float, colour, elbow_out: float = 1.0):
    """An arm from `shoulder` to `hand`. Returns the elbow and the hand."""
    elbow, hand = S.joint(shoulder, hand, upper, fore, elbow_out)
    pen.limb([shoulder, elbow, hand], width, colour)
    return elbow, hand


def alarm_mark(f: K.Frame, x: float, y: float, colour=CRIMSON) -> None:
    """The "!" over the head of a figure that sees you."""
    f.limb([(x, y - 10.0), (x, y)], 2.6, colour)
    f.ellipse(x, y + 5.0, 1.7, 1.7, colour)


def dust(f: K.Frame, x: float, y: float, spread: float, amount: float, seed: str, colour=SEPIA, count: int = 7) -> None:
    """A puff of dust at (`x`, `y`): `amount` 0..1 grows it and fades it."""
    if amount <= 0.0:
        return
    rng = random.Random(seed)
    for _ in range(count):
        a = rng.uniform(math.pi, math.tau)
        r = spread * (0.4 + 0.6 * amount) * rng.uniform(0.5, 1.0)
        f.ellipse(x + math.cos(a) * r, y + math.sin(a) * r * 0.5, rng.uniform(1.6, 3.2) * (0.6 + amount), rng.uniform(1.4, 2.6) * (0.6 + amount),
                  K.alpha(colour, 0.75 * (1.0 - 0.6 * amount)), body=False)


def lerp(a: Point, b: Point, u: float) -> Point:
    return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)
