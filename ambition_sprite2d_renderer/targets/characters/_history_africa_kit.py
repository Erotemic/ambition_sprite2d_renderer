"""The drawing kit of the cast of Africa, the Levant and Sumer (the History dimension).

The second pass of the History dimension is a grid: each floor is a region
of the world, and each column is a time. This kit serves the creatures of
the African floor (the Cradle, the southern coast, the Green Sahara, Aksum
and Kush) and of the Levant and the Bronze Age of Uruk.

The cast is drawn on the kit of the Art dimension's cast
(`_art_cast_kit.py`): flat colour with one shade, and one bold dark outline
round the silhouette. This module adds:

- the palette of these rooms: the sepia ink of an old textbook, the ochre
  earth and gold grass of the savanna, and the colours of the Bronze Age sea;
- :func:`enemy_metadata`, the actor sidecar of an enemy of the dimension;
- :func:`alarm_mark` and :func:`dust`;
- :class:`ScaledPen`, the pen of the Steppe kit (it turns, moves and scales).

It draws nothing by itself. Each figure faces right and stands with its
feet on its ground row.
"""

from __future__ import annotations

import math
import random
from typing import Sequence

from . import _art_cast_kit as K
from ._history_steppe_kit import ScaledPen

__all__ = ["ScaledPen", "enemy_metadata", "alarm_mark", "dust"]

#: The ink of the dimension: the dark brown of a printed textbook.
SEPIA_INK = (48, 30, 22, 255)
#: The "!" of a creature that sees you: red ochre, as on a painted rock.
RED_OCHRE = (196, 64, 38, 255)
RED_OCHRE_DARK = (132, 40, 26, 255)

#: The savanna: ochre earth and gold grass.
OCHRE = (214, 158, 82, 255)
OCHRE_DARK = (160, 104, 50, 255)
GRASS_GOLD = (228, 196, 110, 255)
DUST = (222, 196, 150, 255)

#: Skin of the people of these rooms.
SKIN = (176, 116, 78, 255)
SKIN_SHADE = (132, 82, 54, 255)
SKIN_LIGHT = (204, 150, 108, 255)

#: The Bronze Age: bronze, linen, a sea blue.
BRONZE = (204, 142, 62, 255)
BRONZE_DARK = (136, 88, 36, 255)
BRONZE_LIGHT = (246, 204, 128, 255)
LINEN = (236, 226, 200, 255)
LINEN_SHADE = (190, 174, 140, 255)
SEA = (44, 112, 156, 255)
SEA_DARK = (26, 70, 104, 255)
FEATHER = (240, 232, 214, 255)
FEATHER_SHADE = (196, 180, 150, 255)


def enemy_metadata(character_id: str, display_name: str, era: str, body_plan: str, body_kind: str, mass: str, locomotion: str,
                   traits: Sequence[str], description: str) -> dict:
    """The actor sidecar of an enemy of the History dimension: the Art kit's
    sidecar with the tags of this dimension and of its room (`era`)."""
    meta = K.enemy_metadata(character_id, display_name, body_plan, body_kind, mass, locomotion, traits, description)
    meta["tags"] = ["enemy", "history", era]
    return meta


def alarm_mark(f: K.Frame, x: float, y: float) -> None:
    """The "!" over the head of a creature that sees you, in red ochre."""
    f.limb([(x, y - 10.0), (x, y)], 2.6, RED_OCHRE)
    f.ellipse(x, y + 5.0, 1.7, 1.7, RED_OCHRE)


def dust(f: K.Frame, x: float, y: float, amount: float, seed: str, spread: float = 1.0, colour=DUST) -> None:
    """A puff of dust on the ground at `(x, y)`: `amount` 0..1 sets its size."""
    if amount <= 0.02:
        return
    rng = random.Random(seed)
    for _ in range(5):
        dx = rng.uniform(-10.0, 10.0) * spread
        r = (3.0 + rng.uniform(0.0, 3.0)) * amount
        f.ellipse(x + dx, y - r * 0.6 - rng.uniform(0.0, 3.0) * amount, r, r * 0.75, K.alpha(colour, 0.55 + 0.3 * amount), body=False)


def gait(ph: float, stride: float, lift: float):
    """The place of a paw at phase `ph` of a stride: on the ground it moves
    back under the body; in the air it comes forward and up."""
    ph %= 1.0
    if ph < 0.5:
        u = ph / 0.5
        return (stride * (0.5 - u), 0.0)
    u = (ph - 0.5) / 0.5
    return (stride * (-0.5 + (1.0 - math.cos(math.pi * u)) / 2.0), -lift * math.sin(math.pi * u))


class ScaledFrame(K.Frame):
    """A frame that draws every shape `scale` times its size about `pivot`.

    Use it to fit a big creature and its whole strike in its frame. Put the
    pivot on the ground row, so that the feet stay on the ground."""

    def __init__(self, size, scale: float, pivot) -> None:
        super().__init__(size)
        self.scale, self.pivot = scale, pivot

    def _q(self, x: float, y: float):
        px, py = self.pivot
        return px + (x - px) * self.scale, py + (y - py) * self.scale

    def _w(self, points):
        return [(qx * K.SUPER, qy * K.SUPER) for qx, qy in (self._q(x, y) for x, y in points)]

    def ellipse(self, cx, cy, rx, ry, fill, body=True):
        x, y = self._q(cx, cy)
        super().ellipse(x, y, rx * self.scale, ry * self.scale, fill, body)

    def dot(self, cx, cy, r, fill=K.INK):
        x, y = self._q(cx, cy)
        super().dot(x, y, r * self.scale, fill)

    def glow(self, cx, cy, r, fill):
        x, y = self._q(cx, cy)
        super().glow(x, y, r * self.scale, fill)

    def limb(self, points, width, fill, body=True):
        super().limb(points, width * self.scale, fill, body)

    def ink(self, points, width=1.2, fill=K.INK):
        super().ink(points, width * self.scale, fill)

    def glow_line(self, points, width, fill):
        super().glow_line(points, width * self.scale, fill)
