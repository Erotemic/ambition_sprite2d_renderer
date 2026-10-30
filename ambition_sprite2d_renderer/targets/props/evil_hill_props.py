"""Gallows Hill and Lower Godwin's bell tower (the Evil dimension): the hill
over the hamlet, climbed to up the bell tower, east along it to the
Searchlight Ridge.

Drawn in room coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/evil_moor/make_specs.py` (`hamlet`, `hill`):
the hamlet's ground (y 656) and the bell tower (x 1040..1160; its ladder the
engine's, x 1084..1116); the hill's ground (y 480 to its foot, 544), the
hatch over the tower's top (x 1040..1160), the way east to the ridge.

- `hamlet_belltower`: a tall timber tower from the hamlet's ground to the
  top of the room: four posts braced, a roofed belfry at the top, the bell.
- `hill_west`: the hill's turf over rock; wind-bent trees; the paupers'
  graves, crooked boards in a row; the top of the bell tower coming up
  through the hill, its hatch.
- `hill_east`: the gibbet (empty; a notice on it, a crow on its arm); the
  founder's billboard, his face pasted over twice; a dry-stone wall; the
  path on east to the ridge.

Silhouettes against the red sky, lit on their left by it, as the moor.
Animations: ``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .evil_forest_props import NEAR_BLACK, PAL, rim

HAMLET_G = 656
TOWER = (1040, 1160)
HILL_W, HILL_G, HILL_FOOT = 2800, 480, 544
TIMBER = (34, 26, 24)
TIMBER_LIGHT = (70, 52, 44)
BRONZE = (150, 110, 60)
TURF = (40, 30, 32)
ROCK = (46, 34, 38)
ROCK_LIGHT = (90, 60, 62)
PAPER = (200, 186, 150)
RED = (150, 30, 30)


def belltower(c, k):
    t0, t1 = TOWER
    g = HAMLET_G
    posts = c.mask(lambda p: [p.rect(x, 60, x + 10, g) for x in (t0 + 4, t1 - 14)])
    c.put(posts, TIMBER)
    c.put(c.mask(lambda p: [p.line([(t0 + 9, y), (t1 - 9, y + 80)], 4) for y in range(140, g - 60, 160)]
                 + [p.line([(t1 - 9, y), (t0 + 9, y + 80)], 4) for y in range(140, g - 60, 160)]), TIMBER)
    c.put(c.mask(lambda p: [p.rect(t0, y, t1, y + 6) for y in range(140, g, 160)]), TIMBER)
    rim(c, posts, 0.4)
    # The belfry: its roof, the bell.
    c.put(c.mask(lambda p: p.poly([(t0 - 16, 64), ((t0 + t1) / 2, 4), (t1 + 16, 64)])), TIMBER_LIGHT)
    c.put(c.mask(lambda p: (p.poly([((t0 + t1) / 2 - 20, 104), ((t0 + t1) / 2 + 20, 104), ((t0 + t1) / 2 + 14, 74), ((t0 + t1) / 2 - 14, 74)]),
                            p.ellipse((t0 + t1) / 2, 74, 14, 8))), BRONZE)
    c.put(c.mask(lambda p: p.line([((t0 + t1) / 2 + 12, 100), (t1 - 6, 140), (t1 - 6, g - 40)], 1.4)), (120, 100, 70))


def turf(c, x0, x1):
    m = c.mask(lambda p: p.poly([(x0, HILL_FOOT), (x0, HILL_G + 4), *[(x, HILL_G + 2 * math.sin(x / 41.0)) for x in np.linspace(x0, x1, 40)], (x1, HILL_G + 4), (x1, HILL_FOOT)]))
    c.put(m, ROCK)
    c.put(m * (c.y < HILL_G + 14), TURF)
    c.tone(m * (c.noise(("hill", x0), (x1 - x0) / 60, 3, 2) - 0.5), 0.25)
    rim(c, m, 0.35)


def bent_tree(c, x, h, lean):
    c.put(c.mask(lambda p: p.line([(x, HILL_G), (x + lean * 0.3, HILL_G - h * 0.5), (x + lean, HILL_G - h)], 7)), NEAR_BLACK)
    for i, (dx, dy) in enumerate(((0.6, 0.7), (1.0, 0.9), (0.4, 0.55))):
        c.put(c.mask(lambda p: p.line([(x + lean * dx, HILL_G - h * dy), (x + lean * dx + lean * 0.6, HILL_G - h * dy - 30 + i * 12)], 3)), NEAR_BLACK)


def hill_west(c, k):
    t0, t1 = TOWER
    turf(c, 16, t0)
    turf(c, t1, 1600)
    bent_tree(c, 300, 180, 90)
    bent_tree(c, 760, 140, 70)
    # The paupers' graves: crooked boards in a row, one with a wreath.
    rng = c.rand("hill_graves")
    for i, x in enumerate(range(420, 700, 46)):
        lean = rng.uniform(-0.15, 0.15)
        c.put(c.mask(lambda p: (p.line([(x, HILL_G), (x + 40 * lean, HILL_G - 44)], 4),
                                p.line([(x - 12 + 30 * lean, HILL_G - 30), (x + 12 + 30 * lean, HILL_G - 32)], 3))), TIMBER_LIGHT)
    c.put(c.mask(lambda p: p.ring(512, HILL_G - 20, 8, 2.4)), (60, 70, 40))
    c.put(c.mask(lambda p: [p.ellipse(x, HILL_G + 1, 22, 5) for x in range(420, 700, 46)]), mix(TURF, (0, 0, 0), 0.3))
    # The top of the bell tower through the hill, its hatch.
    c.put(c.mask(lambda p: [p.rect(x, HILL_G - 40, x + 10, HILL_FOOT) for x in (t0 + 4, t1 - 14)]), TIMBER)
    c.put(c.mask(box(t0, HILL_G, t1, HILL_G + 8)), TIMBER_LIGHT)
    c.put(c.mask(lambda p: [p.rect(x, HILL_G, x + 2, HILL_G + 8) for x in range(t0 + 10, t1, 18)]), TIMBER)


def hill_east(c, k):
    turf(c, 1600, HILL_W)
    # The gibbet, empty; a sign on it.
    gx = 1800
    c.put(c.mask(lambda p: (p.rect(gx, HILL_G - 200, gx + 10, HILL_G), p.rect(gx, HILL_G - 200, gx + 90, HILL_G - 190),
                            p.line([(gx + 10, HILL_G - 150), (gx + 50, HILL_G - 190)], 5))), TIMBER)
    c.put(c.mask(lambda p: p.line([(gx + 80, HILL_G - 190), (gx + 80, HILL_G - 120)], 1.4)), (120, 100, 70))
    c.put(c.mask(lambda p: p.ring(gx + 80, HILL_G - 112, 8, 1.6)), (120, 100, 70))
    # A crow on its arm.
    c.put(c.mask(lambda p: (p.ellipse(gx + 40, HILL_G - 210, 10, 7), p.ellipse(gx + 50, HILL_G - 216, 5, 5),
                            p.poly([(gx + 54, HILL_G - 217), (gx + 62, HILL_G - 215), (gx + 54, HILL_G - 213)]),
                            p.poly([(gx + 32, HILL_G - 210), (gx + 20, HILL_G - 204), (gx + 30, HILL_G - 206)]))), NEAR_BLACK)
    # A dry-stone wall, tumbled at one end.
    rng = c.rand("hill_wall")
    c.put(c.mask(lambda p: [p.ellipse(x + rng.uniform(-3, 3), HILL_G - 8 - 13 * row + rng.uniform(-2, 2), 11, 7)
                            for row in range(3) for x in range(1960 + row * 9, 2160 - row * 40, 20)]), ROCK_LIGHT)
    c.put(c.mask(box(gx - 30, HILL_G - 100, gx + 40, HILL_G - 70)), PAPER)
    c.put(c.mask(lambda p: [p.rect(gx - 24, y, gx + 34, y + 1.2) for y in (HILL_G - 92, HILL_G - 84, HILL_G - 76)]), (60, 50, 50))
    # The founder's billboard, his face pasted over twice.
    bx0, bx1 = 2200, 2460
    c.put(c.mask(lambda p: [p.rect(x, HILL_G - 260, x + 10, HILL_G) for x in (bx0 + 20, bx1 - 30)]), TIMBER)
    board = c.mask(box(bx0, HILL_G - 300, bx1, HILL_G - 150))
    c.put(board, RED)
    c.put(c.mask(lambda p: p.ellipse((bx0 + bx1) / 2, HILL_G - 225, 44, 52)), PAPER)
    c.put(c.mask(lambda p: p.poly([((bx0 + bx1) / 2 - 30, HILL_G - 250), ((bx0 + bx1) / 2 + 50, HILL_G - 260), ((bx0 + bx1) / 2 + 40, HILL_G - 190), ((bx0 + bx1) / 2 - 36, HILL_G - 196)])), mix(PAPER, (0, 0, 0), 0.15))
    c.put(c.mask(lambda p: p.rect((bx0 + bx1) / 2 - 20, HILL_G - 226, (bx0 + bx1) / 2 + 24, HILL_G - 220)), NEAR_BLACK)
    rim(c, board, 0.4)
    bent_tree(c, 2600, 160, -80)


PIECES: Dict[str, Piece] = {
    "hamlet_belltower": Piece((TOWER[0] - 20, 0, TOWER[1] + 20, HAMLET_G), belltower),
    "hill_west": Piece((16, 200, 1600, HILL_FOOT), hill_west),
    "hill_east": Piece((1600, 140, HILL_W, HILL_FOOT), hill_east),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
