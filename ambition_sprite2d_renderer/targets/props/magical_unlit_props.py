"""The Unlit (the Magical dimension, Mary-O's): where the void is hostile.
Black and white, as the void's own things are.

Drawn in room coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/magical/make_specs.py`:

- `magical_void_coliseum` (1920 by 1280, floor y 1216): `coliseum_stand_west`,
  `coliseum_stand_east`, the stands either side of the ring, tier on tier,
  and on them the crowd: void stars, come to watch the void learn to fight. Grey
  edges, not white: they are not the ground and they do not fight.
- `magical_void_ledges` (floor y 576, roof y 64; a gap 160 wide between each
  piece of floor, a one-way ledge over it at y 466, 40 past each side):
  `ledges_gap`, drawn at the first gap (x 520..680) and placed at each:
  the chains that hang the ledge from the roof, and under the floor's line,
  pieces of the castle falling away into the void.
- `magical_void_wastes` (2560 wide, floor y 576): `wastes_dead_things`, what
  the void left out here, in grey line: the star trees with nothing on them,
  a lamp on its side, a wheel.

Animations: ``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

import math
from typing import Dict

from ._district_props import Piece, targets
from .magical_void_depths_props import EDGE, GREY, PAL, VOID, circle, dashed, shrink, star_pts

#: The stands' edges are grey: in the void a white edge is a thing you can
#: stand on or be hit by (the terrain, the void's creatures); the crowd is
#: neither.
DIM = (84, 82, 92)


def dim_poly(c, pts, edge=1.4):
    c.put(c.mask(lambda p: p.poly(pts)), DIM)
    c.put(c.mask(lambda p: p.poly(shrink(pts, edge))), VOID)

RING_FLOOR = 1216
STAND_W = 440
STAND_TOP = 760
WASTES_FLOOR = 576


def stand(c, x0, x1, toward):
    """Tiers stepping down toward the ring (`toward` +1 east, -1 west); a
    void star on each seat, its eyes on the ring."""
    tiers = 5
    step_h = (RING_FLOOR - STAND_TOP) / tiers
    step_w = (x1 - x0) / tiers
    for t in range(tiers):
        # The tier nearest the ring is the lowest.
        k = t if toward > 0 else tiers - 1 - t
        tx0 = x0 + t * step_w
        ty = RING_FLOOR - (tiers - k) * step_h
        dim_poly(c, [(tx0, RING_FLOOR), (tx0 + step_w, RING_FLOOR), (tx0 + step_w, ty), (tx0, ty)], 1.4)
        for j in range(2):
            sx = tx0 + step_w * (0.3 + 0.4 * j)
            r = 13 + (t * 7 + j * 3) % 4
            sy = ty - r * 0.85
            dim_poly(c, star_pts(sx, sy, r, 0.48, 0.15 * ((t + j) % 3 - 1)), 1.4)
            # Its eyes, on the ring.
            ex = sx + toward * r * 0.22
            c.put(c.mask(lambda p: [p.ellipse(ex - r * 0.2, sy - r * 0.05, 1.6), p.ellipse(ex + r * 0.2, sy - r * 0.05, 1.6)]), EDGE)


def stand_west(c, k):
    stand(c, 40, 40 + STAND_W, 1)


def stand_east(c, k):
    stand(c, 1880 - STAND_W, 1880, -1)


def dead_things(c, k):
    f = WASTES_FLOOR
    # The star trees, bare: a trunk, round crowns gone to dashed line.
    for x, s in ((420, 1.0), (1180, 0.8), (2100, 1.1)):
        dashed(c, [(x, f), (x + 6 * s, f - 140 * s), (x - 4 * s, f - 190 * s)], 2.2, 16, 10, GREY)
        dashed(c, [(x + 14 * s, f), (x + 12 * s, f - 130 * s)], 2.2, 16, 10, GREY)
        for dx, dy, r in ((-60, -230, 46), (10, -270, 58), (70, -225, 44)):
            dashed(c, circle(x + dx * s, f + dy * s, r * s), 1.6, 10, 16, GREY, 0.8)
    # A star lamp, on its side, its star rolled off.
    x = 760
    c.put(c.mask(lambda p: p.line([(x, f - 3), (x + 130, f - 8)], 2.2)), GREY)
    pts = star_pts(x + 160, f - 14, 14, 0.5, 0.6)
    c.put(c.mask(lambda p: p.line(pts + [pts[0]], 1.6)), GREY)
    # A cart's wheel, half sunk in the dark.
    x = 1640
    c.put(c.mask(lambda p: p.line([(x + 38 * math.cos(a), f - 10 + 38 * math.sin(a)) for a in [math.pi + i * math.pi / 16 for i in range(17)]], 2.2)), GREY)
    c.put(c.mask(lambda p: [p.line([(x, f - 10), (x + 36 * math.cos(a), f - 10 + 36 * math.sin(a))], 1.4) for a in (3.6, 4.4, 5.2, 6.0)]), GREY)
    # Something watching from the far side: two eyes, low, white.
    c.put(c.mask(lambda p: [p.ellipse(2380, f - 60, 2.4), p.ellipse(2396, f - 60, 2.4)]), EDGE)


GAP = (520, 680)
LEDGE_Y, ROOF_Y = WASTES_FLOOR - 110, 64


def chain(c, x, y0, y1):
    for y in range(int(y0), int(y1) - 10, 14):
        c.put(c.mask(lambda p: p.ellipse(x, y + 7, 3.2, 6.5)), GREY)
        c.put(c.mask(lambda p: p.ellipse(x, y + 7, 1.6, 4.5)), VOID)


def gap(c, k):
    x0, x1 = GAP
    chain(c, x0 - 30, ROOF_Y, LEDGE_Y)
    chain(c, x1 + 30, ROOF_Y, LEDGE_Y)
    # Below the floor's line: castle stone falling, smaller as it goes.
    f = WASTES_FLOOR
    for i, (dx, dy, s) in enumerate(((30, 18, 18), (96, 30, 14), (60, 46, 10), (120, 54, 7), (20, 58, 5))):
        pts = [(x0 + dx, f + dy), (x0 + dx + s, f + dy + s * 0.2), (x0 + dx + s * 0.8, f + dy + s * 0.9), (x0 + dx - s * 0.2, f + dy + s * 0.7)]
        c.put(c.mask(lambda p: p.poly(pts)), GREY)
        c.put(c.mask(lambda p: p.poly(shrink(pts, 1.2))), VOID)
        c.put(c.mask(lambda p: p.line([(x0 + dx + s * 0.3, f + dy - 4), (x0 + dx + s * 0.3, f + dy - 4 - s * 0.8)], 1.0)), GREY, 0.6)


PIECES: Dict[str, Piece] = {
    "coliseum_stand_west": Piece((30, STAND_TOP - 40, 40 + STAND_W + 10, RING_FLOOR), stand_west),
    "coliseum_stand_east": Piece((1880 - STAND_W - 10, STAND_TOP - 40, 1890, RING_FLOOR), stand_east),
    "ledges_gap": Piece((GAP[0] - 44, ROOF_Y, GAP[1] + 44, WASTES_FLOOR + 64), gap),
    "wastes_dead_things": Piece((300, WASTES_FLOOR - 340, 2420, WASTES_FLOOR), dead_things, px=1.5),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
