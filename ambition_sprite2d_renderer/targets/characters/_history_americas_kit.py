"""The drawing kit of the cast of the Americas and Oceania (the History dimension).

The second pass of the History dimension is a grid: each floor is a region
of the world, and each column is a time. This kit serves the creatures of
two floors: the Americas (Beringia, the first maize) and Oceania (Sahul,
the New Guinea highlands). Their cast is drawn on the kit of the Art
dimension's cast (`_art_cast_kit.py`): flat colour with one shade, and one
bold dark outline round the silhouette. This module adds:

- the colours of the two floors;
- :func:`enemy_metadata`, the actor sidecar of an enemy of the dimension,
  with the tag of its room;
- :class:`ScaledFrame`, a frame that draws every shape larger or smaller
  about a pivot, so that one drawing can serve a large and a small beast;
- :func:`gait`, the place of a foot in a walk cycle;
- :func:`along`, a point in the frame of a body that turns;
- :func:`finish`, the frame in the sepia outline of the dimension.

The "!" mark and the puff of dust are those of `_history_cast_kit.py`.
Each figure faces right and stands with its feet on its ground row.
"""

from __future__ import annotations

import math
from typing import List, Sequence, Tuple

from . import _art_cast_kit as K
from . import _history_cast_kit as HC

Point = Tuple[float, float]

#: The outline of the cast: the dark sepia ink of the first pass.
OUTLINE = (44, 28, 22, 255)
SEPIA_INK = HC.SEPIA_INK

#: The Americas: the gold of maize, the red of a volcano, the green of agave.
MAIZE = (238, 196, 72, 255)
MAIZE_SHADE = (186, 140, 40, 255)
VOLCANO = (170, 70, 46, 255)
AGAVE = (104, 150, 128, 255)
AGAVE_DARK = (62, 104, 90, 255)
JUNGLE = (64, 120, 62, 255)
#: Oceania: red earth, eucalyptus grey-green, and the blue of the sea.
RED_EARTH = (184, 92, 52, 255)
RED_EARTH_SHADE = (132, 60, 34, 255)
EUCALYPT = (150, 170, 140, 255)
SEA = (52, 132, 176, 255)

#: The "!" of a creature that sees you: red ochre.
ALARM = (214, 64, 40, 255)

alarm_mark = HC.alarm_mark
dust = HC.dust
lerp = HC.lerp


def enemy_metadata(character_id: str, display_name: str, room: str, body_plan: str, body_kind: str, mass: str, locomotion: str,
                   traits: Sequence[str], description: str) -> dict:
    """The actor sidecar of an enemy of the History dimension. `room` is the
    tag of its room: ``beringia``, ``first_maize``, ``sahul`` or
    ``highlands``."""
    meta = K.enemy_metadata(character_id, display_name, body_plan, body_kind, mass, locomotion, traits, description)
    meta["tags"] = ["enemy", "history", room]
    return meta


class ScaledFrame(K.Frame):
    """A frame that draws every shape `scale` times larger about `pivot`.
    Line widths and radii grow by the same amount."""

    def __init__(self, size: Tuple[int, int], scale: float, pivot: Point) -> None:
        super().__init__(size)
        self.scale = scale
        self.pivot = pivot

    def _p(self, x: float, y: float) -> Point:
        px, py = self.pivot
        return px + (x - px) * self.scale, py + (y - py) * self.scale

    def _w(self, points):
        return [(self._p(x, y)[0] * K.SUPER, self._p(x, y)[1] * K.SUPER) for x, y in points]

    def ellipse(self, cx, cy, rx, ry, fill, body=True):
        x, y = self._p(cx, cy)
        K.Frame.ellipse(self, x, y, rx * self.scale, ry * self.scale, fill, body)

    def dot(self, cx, cy, r, fill=K.INK):
        x, y = self._p(cx, cy)
        K.Frame.dot(self, x, y, r * self.scale, fill)

    def glow(self, cx, cy, r, fill):
        x, y = self._p(cx, cy)
        K.Frame.glow(self, x, y, r * self.scale, fill)

    def limb(self, points, width, fill, body=True):
        K.Frame.limb(self, points, width * self.scale, fill, body)

    def ink(self, points, width=1.2, fill=K.INK):
        K.Frame.ink(self, points, width * self.scale, fill)

    def glow_line(self, points, width, fill):
        K.Frame.glow_line(self, points, width * self.scale, fill)


def gait(ph: float, stride: float, lift: float) -> Point:
    """The place of a foot at phase `ph` of a walk: on the ground it moves
    back under the body; in the air it comes forward and up."""
    ph %= 1.0
    if ph < 0.55:
        u = ph / 0.55
        return (stride * (0.5 - u), 0.0)
    u = (ph - 0.55) / 0.45
    return (stride * (-0.5 + (1.0 - math.cos(math.pi * u)) / 2.0), -lift * math.sin(math.pi * u))


def along(origin: Point, axis: Point, u: float, v: float) -> Point:
    """The point `u` along the unit `axis` from `origin` and `v` across it
    (`v` positive is below the axis when the axis points right)."""
    ax, ay = axis
    return (origin[0] + ax * u - ay * v, origin[1] + ay * u + ax * v)


def frame_of(a: Point, b: Point) -> Tuple[Point, float]:
    """The unit axis from `a` to `b`, and the distance."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    d = math.hypot(dx, dy) or 1.0
    return (dx / d, dy / d), d


def turned(points: Sequence[Point], centre: Point, degrees: float, shift: Point = (0.0, 0.0)) -> List[Point]:
    """`points` given about `centre`, turned by `degrees` and moved by `shift`."""
    pts = [(centre[0] + x, centre[1] + y) for x, y in points]
    pts = K.turn(pts, centre[0], centre[1], degrees)
    return [(x + shift[0], y + shift[1]) for x, y in pts]


def keyed(table: Sequence[Sequence[float]], t: float) -> List[float]:
    """The row of `table` at `t` (0..1), mixed between its two nearest rows:
    a pose given as key frames."""
    x = max(0.0, min(1.0, t)) * (len(table) - 1)
    k = min(len(table) - 2, int(x))
    u = x - k
    return [a + (b - a) * u for a, b in zip(table[k], table[k + 1])]


def finish(f: K.Frame, fade: float = 1.0, width: float = 1.6) -> object:
    """The frame at its published size, in the sepia outline of the dimension."""
    return f.finish(outline=OUTLINE, width=width, fade=fade)
