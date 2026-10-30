"""Lower Godwin (`evil_lower_godwin`, the Evil dimension): the hamlet under
the castle, west of the Castle Allotments: the people the castle rules,
getting on with it.

Drawn in room coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/evil_moor/make_specs.py` (`hamlet`): the
ground (y 656); the crier's platform (x 1270..1410, y 592), walked on.

- `hamlet_west`: two cottages, crooked, thatched, their windows lit; the
  bakery with its sign (a loaf) and its window of loaves; a washing line.
- `hamlet_east`: the well and its bucket; the stocks (FOR COMPLAINING); the
  crier's platform and its bell; the decree board, pasted over and over;
  a third cottage with its shutters closed and its door barred, and a
  little cart of turnips.

Silhouettes against the moor's red sky, lit on their left by it, as the
moor. Animations: ``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .eureka_props import edge_line
from .evil_forest_props import NEAR_BLACK, PAL, rim

G = 656
PLATFORM = (1270, 1410, 592)
WALL = (70, 60, 58)
WALL_DARK = (48, 40, 40)
THATCH = (90, 70, 46)
TIMBER = (34, 26, 24)
WINDOW = (255, 170, 80)
PAPER = (200, 186, 150)
LOAF = (196, 140, 80)


def cottage(c, x0, x1, eave, ridge, tag, lit=True, crooked=0.0):
    walls = c.mask(lambda p: p.poly([(x0, G), (x0 + crooked, eave), (x1 + crooked, eave), (x1, G)]))
    c.put(walls, WALL)
    c.put(walls * c.mask(lambda p: [p.rect(x0, y, x1 + crooked, y + 1.2) for y in np.arange(eave + 12, G, 14)]), WALL_DARK, 0.6)
    rim(c, walls)
    roof = c.mask(lambda p: p.poly([(x0 - 18 + crooked, eave + 4), (x1 + 18 + crooked, eave + 4), ((x0 + x1) / 2 + crooked * 1.4, ridge)]))
    c.put(roof, THATCH)
    c.put(roof * c.mask(lambda p: [p.line([(x, eave + 4), ((x0 + x1) / 2 + crooked * 1.4 + (x - (x0 + x1) / 2) * 0.2, ridge + 6)], 0.8) for x in np.arange(x0 - 14, x1 + 18, 9)]), scale(THATCH, 0.7))
    rim(c, roof, 0.4)
    # The door and a window.
    dx = x0 + (x1 - x0) * 0.62
    c.put(c.mask(box(dx, G - 54, dx + 26, G)), TIMBER)
    wx = x0 + (x1 - x0) * 0.2
    c.put(c.mask(box(wx, eave + 20, wx + 28, eave + 44)), WINDOW if lit else TIMBER)
    c.put(c.mask(lambda p: (p.rect(wx + 13, eave + 20, wx + 15, eave + 44), p.rect(wx, eave + 31, wx + 28, eave + 33))), TIMBER)
    if lit:
        c.light(c.mask(lambda p: p.ellipse(wx + 14, eave + 32, 30, 22), blur=10), WINDOW, 0.3)


def west(c, k):
    cottage(c, 120, 300, G - 96, G - 170, "c1", crooked=6)
    cottage(c, 380, 540, G - 90, G - 156, "c2", crooked=-4)
    # The bakery: taller, its sign a loaf, its window of loaves.
    b0, b1 = 700, 920
    cottage(c, b0, b1, G - 120, G - 200, "bakery")
    c.put(c.mask(lambda p: (p.rect(b1 - 30, G - 140, b1 + 30, G - 136), p.line([(b1 + 20, G - 136), (b1 + 20, G - 126)], 1))), TIMBER)
    c.put(c.mask(lambda p: p.ellipse(b1 + 20, G - 116, 18, 10)), LOAF)
    c.put(c.mask(lambda p: [p.line([(b1 + 10 + i * 8, G - 122), (b1 + 14 + i * 8, G - 110)], 1.2) for i in range(3)]), scale(LOAF, 0.7))
    c.put(c.mask(box(b0 + 30, G - 70, b0 + 110, G - 30)), WINDOW)
    c.put(c.mask(lambda p: [p.ellipse(b0 + 44 + i * 18, G - 38, 8, 5) for i in range(4)]), LOAF)
    # A washing line between the cottages: shirts, a castle uniform.
    c.put(c.mask(lambda p: p.line([(300, G - 110), (340, G - 104), (380, G - 112)], 1)), TIMBER)
    for x, col in ((316, (180, 170, 150)), (350, (90, 40, 40)), (366, (160, 150, 130))):
        c.put(c.mask(lambda p: p.poly([(x - 7, G - 106), (x + 7, G - 106), (x + 6, G - 88), (x - 6, G - 88)])), col)


def east(c, k):
    # The well, its roof and bucket.
    wx = 1500
    c.put(c.mask(lambda p: p.rect(wx - 30, G - 34, wx + 30, G)), (90, 84, 80))
    c.put(c.mask(lambda p: [p.rect(wx - 30, y, wx + 30, y + 1.2) for y in (G - 24, G - 12)]), WALL_DARK)
    c.put(c.mask(lambda p: [p.rect(x, G - 90, x + 4, G - 34) for x in (wx - 26, wx + 22)]), TIMBER)
    c.put(c.mask(lambda p: p.poly([(wx - 40, G - 88), (wx + 40, G - 88), (wx, G - 112)])), THATCH)
    c.put(c.mask(lambda p: (p.line([(wx, G - 88), (wx, G - 60)], 1), p.poly([(wx - 7, G - 60), (wx + 7, G - 60), (wx + 5, G - 48), (wx - 5, G - 48)]))), TIMBER)
    # The stocks: a beam with three holes, on two posts.
    sx = 1640
    c.put(c.mask(lambda p: [p.rect(x, G - 50, x + 6, G) for x in (sx - 40, sx + 34)]), TIMBER)
    c.put(c.mask(box(sx - 46, G - 50, sx + 46, G - 34)), mix(TIMBER, (120, 90, 60), 0.5))
    c.put(c.mask(lambda p: [p.ellipse(sx + dx, G - 42, 5, 4) for dx in (-24, 0, 24)]), NEAR_BLACK)
    # The crier's platform (walked on), its post and bell.
    p0, p1, py = PLATFORM
    c.put(c.mask(box(p0, py, p1, py + 10)), TIMBER)
    edge_line(c, p0, p1, py, (110, 80, 60), 3)
    c.put(c.mask(lambda p: [p.rect(x, py + 10, x + 6, G) for x in (p0 + 6, p1 - 12)]), TIMBER)
    c.put(c.mask(lambda p: (p.rect(p1 - 14, py - 70, p1 - 10, py), p.rect(p1 - 30, py - 70, p1 - 10, py - 66))), TIMBER)
    c.put(c.mask(lambda p: (p.poly([(p1 - 30, py - 64), (p1 - 18, py - 64), (p1 - 16, py - 48), (p1 - 32, py - 48)]), p.ellipse(p1 - 24, py - 46, 3))), (170, 130, 60))
    # The decree board, pasted over and over.
    rng = c.rand("decrees")
    dx0, dx1 = 1740, 1860
    c.put(c.mask(lambda p: [p.rect(x, G - 120, x + 6, G) for x in (dx0, dx1 - 6)]), TIMBER)
    c.put(c.mask(box(dx0 - 6, G - 140, dx1 + 6, G - 60)), TIMBER)
    for i in range(9):
        x, y = rng.uniform(dx0, dx1 - 34), rng.uniform(G - 136, G - 96)
        c.put(c.mask(box(x, y, x + 34, y + 40)), mix(PAPER, (90, 80, 70), rng.uniform(0, 0.4)))
        c.put(c.mask(lambda p: [p.rect(x + 4, y + 6 + j * 6, x + 30, y + 7 + j * 6) for j in range(5)]), (60, 50, 50), 0.6)
    c.put(c.mask(box(dx0 + 30, G - 134, dx1 - 30, G - 96)), (230, 220, 190))
    c.put(c.mask(lambda p: p.rect(dx0 + 36, G - 128, dx1 - 36, G - 120)), (160, 30, 30))
    # A third cottage, its shutters shut and its door barred; a turnip cart.
    cottage(c, 1960, 2140, G - 96, G - 168, "c3", lit=False)
    c.put(c.mask(lambda p: p.line([(2060, G - 50), (2094, G - 10)], 4)), (110, 80, 60))
    cx = 2270
    c.put(c.mask(lambda p: (p.poly([(cx - 40, G - 40), (cx + 40, G - 40), (cx + 34, G - 16), (cx - 34, G - 16)]), p.line([(cx + 40, G - 30), (cx + 80, G - 10)], 3))), (100, 74, 50))
    c.put(c.mask(lambda p: p.ring(cx - 10, G - 10, 10, 3)), TIMBER)
    c.put(c.mask(lambda p: [p.ellipse(cx + dx, G - 44 - abs(dx) * 0.1, 8, 7) for dx in (-26, -12, 2, 16, 28, -18, 8)]), (190, 170, 200))
    c.put(c.mask(lambda p: [p.line([(cx + dx, G - 50), (cx + dx + 2, G - 60)], 2) for dx in (-26, 2, 28)]), (70, 110, 60))


PIECES: Dict[str, Piece] = {
    "hamlet_west": Piece((90, G - 210, 1000, G), west),
    "hamlet_east": Piece((1250, G - 180, 2360, G), east),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
