"""The drawing kit of the cast of the Amphitheatre (the Art dimension).

The Amphitheatre is the performance quarter of the Art dimension. Its cast
(the stagehand, the critic, the mime) is drawn on the kit of the dimension
(`_art_cast_kit.py`). This module adds three things that the three of them
use:

- the colours of the stage: red velvet, gold, black and spotlight white;
- :class:`Pen`, which draws on a :class:`~._art_cast_kit.Frame` through a
  turn about a point, so that a figure can fall over as one piece;
- :func:`joint`, which finds the elbow or the knee between two ends of a
  limb (two-bone inverse kinematics).

Each figure faces right and stands with its feet on its ground row.
"""

from __future__ import annotations

import math
from typing import List, Sequence, Tuple

from . import _art_cast_kit as K

Point = Tuple[float, float]

#: The colours of the stage.
VELVET = (184, 26, 52, 255)
VELVET_DARK = (112, 14, 34, 255)
BLACK_CLOTH = (52, 50, 68, 255)
BLACK_SHADE = (34, 32, 46, 255)
BLACK_LIGHT = (96, 94, 120, 255)
#: The outline of a figure dressed in black (the stagehand).
CREW_OUTLINE = (128, 112, 176, 255)
SPOT = (255, 248, 220, 255)
SKIN = (238, 192, 156, 255)
SKIN_SHADE = (204, 150, 116, 255)
FACE_WHITE = (250, 250, 252, 255)
TOMATO = (226, 46, 34, 255)
TOMATO_DARK = (150, 22, 18, 255)
LEAF = (70, 150, 60, 255)


def joint(root: Point, end: Point, l1: float, l2: float, bend: float) -> Tuple[Point, Point]:
    """The middle joint of a limb from `root` to `end`, with bones `l1` and
    `l2`. `bend` is +1 or -1: the side the joint goes to. For a limb that
    hangs down, -1 puts the joint in front (a knee) and +1 behind (an
    elbow). If the end is too far, the limb is straight and the end moves
    in. Returns the joint and the end."""
    dx, dy = end[0] - root[0], end[1] - root[1]
    d = math.hypot(dx, dy) or 0.01
    reach = l1 + l2 - 0.05
    if d > reach:
        end = (root[0] + dx / d * reach, root[1] + dy / d * reach)
        dx, dy, d = end[0] - root[0], end[1] - root[1], reach
    d = max(d, abs(l1 - l2) + 0.05)
    ux, uy = dx / d, dy / d
    a = (l1 * l1 - l2 * l2 + d * d) / (2.0 * d)
    h = math.sqrt(max(0.0, l1 * l1 - a * a))
    return (root[0] + ux * a - uy * h * bend, root[1] + uy * a + ux * h * bend), end


class Pen:
    """Draws on a frame through a turn of `rot` degrees about `pivot`, then
    a move of `shift`. With no turn and no move it draws as the frame."""

    def __init__(self, f: K.Frame, pivot: Point = (0.0, 0.0), rot: float = 0.0, shift: Point = (0.0, 0.0)) -> None:
        self.f, self.pivot, self.rot, self.shift = f, pivot, rot, shift

    def p(self, points: Sequence[Point]) -> List[Point]:
        pts = list(points)
        if self.rot:
            pts = K.turn(pts, self.pivot[0], self.pivot[1], self.rot)
        sx, sy = self.shift
        return [(x + sx, y + sy) for x, y in pts]

    def at(self, x: float, y: float) -> Point:
        return self.p([(x, y)])[0]

    def poly(self, points: Sequence[Point], fill, body: bool = True) -> None:
        self.f.poly(self.p(points), fill, body)

    def ellipse(self, cx: float, cy: float, rx: float, ry: float, fill, body: bool = True, count: int = 24) -> None:
        self.f.poly(self.p(K.ellipse_points(cx, cy, rx, ry, count)), fill, body)

    def limb(self, points: Sequence[Point], width: float, fill, body: bool = True) -> None:
        self.f.limb(self.p(points), width, fill, body)

    def ink(self, points: Sequence[Point], width: float = 1.2, fill=K.INK) -> None:
        self.f.ink(self.p(points), width, fill)

    def dot(self, cx: float, cy: float, r: float, fill=K.INK) -> None:
        x, y = self.at(cx, cy)
        self.f.dot(x, y, r, fill)

    def glow(self, cx: float, cy: float, r: float, fill) -> None:
        x, y = self.at(cx, cy)
        self.f.glow(x, y, r, fill)

    def glow_line(self, points: Sequence[Point], width: float, fill) -> None:
        self.f.glow_line(self.p(points), width, fill)


def alarm_mark(f: K.Frame, x: float, y: float) -> None:
    """The "!" over the head of a figure that sees you (as the rest of the
    cast of the dimension draws it)."""
    f.limb([(x, y - 10.0), (x, y)], 2.6, K.MAGENTA)
    f.ellipse(x, y + 5.0, 1.7, 1.7, K.MAGENTA)
