"""The mark of the fascist faction of the Evil dimension, as its people wear
it: a black cog of eight teeth with a hole in its middle, on a white disc,
on red. The castle's banners carry the same mark.

The mark is invented. It is not a real symbol, and no real symbol of a real
regime may be drawn in its place.
"""

from __future__ import annotations

import math
from typing import List

from ._ai_era_kit import OUTLINE, WHITE, Kit, Point, RGBA, mix

RED: RGBA = (184, 36, 40, 255)
RED_DARK: RGBA = (124, 22, 30, 255)
DISC: RGBA = (246, 244, 238, 255)
COG: RGBA = (22, 20, 24, 255)


#: The cog as parts of its radius: the round of its body, and its hole.
COG_BODY = 0.7
COG_HOLE = 0.28


def cog_points(c: Point, r: float) -> List[Point]:
    """The outline of the cog's eight square teeth about ``c``, ``r`` to
    their tips. The body (``COG_BODY``) and the hole (``COG_HOLE``) are
    circles: any drawing surface can draw the mark from these."""
    pts = []
    for k in range(8):
        a = math.tau * k / 8.0
        for da, rr in ((-0.24, COG_BODY), (-0.17, 1.0), (0.17, 1.0), (0.24, COG_BODY)):
            pts.append((c[0] + math.cos(a + da) * r * rr, c[1] + math.sin(a + da) * r * rr))
    return pts


def cog(K: Kit, d, c: Point, r: float, colour: RGBA = COG, hole: RGBA = DISC) -> None:
    """The cog about ``c``: eight square teeth, ``r`` to their tips, and a
    hole in its middle."""
    K.poly(d, cog_points(c, r), colour)
    K.oval(d, c, r * COG_BODY, r * COG_BODY, colour)
    K.oval(d, c, r * COG_HOLE, r * COG_HOLE, hole)


def emblem(K: Kit, radius: float):
    """The white disc with the black cog, from its middle."""

    def paint(d) -> None:
        K.oval(d, K.home, radius + 0.45, radius + 0.45, OUTLINE)
        K.oval(d, K.home, radius, radius, DISC)
        cog(K, d, K.home, radius * 0.8)

    return K.piece(("emblem", radius), paint)


def band(K: Kit, width: float, length: float = 5.6):
    """The red armband, along +x from its middle: it goes round the arm, so
    it is ``width`` across (the arm and a little more) and ``length`` along
    the arm."""
    half = length / 2.0

    def shape(d) -> None:
        K.rrect(d, K.home[0] - half, K.home[1] - width / 2.0, K.home[0] + half, K.home[1] + width / 2.0, 0.5, WHITE)

    def detail(d) -> None:
        K.line(d, [K.at(-half + 0.4, -width / 2.0 + 0.6), K.at(half - 0.4, -width / 2.0 + 0.6)], mix(RED, WHITE, 0.3), 0.5)

    return K.solid(("band", width, length), shape, RED, detail, outline=1.0, rim=0.25, shade=0.35, shade_colour=RED_DARK)
