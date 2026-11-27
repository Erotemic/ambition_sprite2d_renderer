"""The Searchlight Ridge (`evil_searchlight_ridge`, the Evil dimension): high
over the moor and the allotments, the line of searchlights the moor is named
for, reached up the moor's watchtower; at its west end a gap in the ridge
drops onto the allotments' greenhouse roof, and a plank bridge over it
goes on west to Gallows Hill.

Use the room dimensions in `evil_moor/make_specs.py`.

- `ridge_west`: the broken end of the ridge over the gap, its edge fallen
  away; the plank bridge over it, planks missing, on ropes to posts; the
  stub of rock beyond, the way on west; barbed wire; a searchlight
  emplacement, its beam sweeping the sky.
- `ridge_east`: the sentry hut; two more searchlights, their beams; a line
  of cable on poles between them; the top of the watchtower coming up
  through the ridge.

Silhouettes against the red sky, lit on their left by it, as the moor.
Animations: ``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box
from .evil_forest_props import NEAR_BLACK, PAL, rim

W, G, FOOT = 3600, 480, 544
GAP = (70, 450)
TOWER = (3100, 3220)
ROCK = (46, 34, 38)
ROCK_LIGHT = (90, 60, 62)
IRON = (40, 36, 40)
LAMP = (255, 236, 190)
BEAM = (255, 240, 200)
WIRE = (110, 100, 104)
TIMBER = (34, 26, 24)
WINDOW = (255, 170, 80)
WALK_EDGE = (170, 110, 77)
WALK_BEAM = (73, 47, 44)


def ground(c, x0, x1):
    """The ridge's rock from `x0` to `x1`, its crest at G."""
    crest = [(x, G + 3 * math.sin(x / 37.0)) for x in np.linspace(x0, x1, 100)]
    m = c.mask(lambda p: p.poly([(x0, FOOT), *crest, (x1, FOOT)]))
    c.put(m, ROCK)
    c.tone(m * np.sin(c.x / 83 + c.y / 9) * np.sin(c.x / 119 - c.y / 13), 0.12)
    c.put(c.mask(lambda p: p.line(crest, 3)), ROCK_LIGHT)
    rim(c, m, 0.35)


def searchlight(c, x, sweep, floor=G):
    c.put(c.mask(lambda p: (p.rect(x - 4, floor - 70, x + 4, floor),
                             p.poly([(x - 18, floor), (x + 18, floor), (x + 8, floor - 12), (x - 8, floor - 12)]))), IRON)
    c.put(c.mask(lambda p: p.ellipse(x, floor - 82, 16, 14)), IRON)
    c.put(c.mask(lambda p: p.ellipse(x + 8 * math.sin(sweep), floor - 84 - 8 * math.cos(sweep), 8, 7)), LAMP)
    tip = (x + 700 * math.sin(sweep), floor - 84 - 700 * math.cos(sweep))
    side = (math.cos(sweep) * 60, math.sin(sweep) * 60)
    beam = c.mask(lambda p: p.poly([(x - 6, floor - 84), (x + 6, floor - 84),
                                    (tip[0] + side[0], tip[1] + side[1]), (tip[0] - side[0], tip[1] - side[1])]), blur=8)
    c.put(beam * np.clip((c.y - 4) / 164, 0, 1), BEAM, 0.16)


def wire(c, x0, x1, y):
    c.put(c.mask(lambda p: [p.ring(x, y - 12, 12, 1.2) for x in np.arange(x0, x1, 14)]), WIRE)
    c.put(c.mask(lambda p: [p.rect(x, y - 30, x + 3, y) for x in np.arange(x0, x1, 120)]), TIMBER)


def west(c, k):
    g0, g1 = GAP
    # The stub of rock west of the gap (the way on to the hill), and the
    # broken end of the ridge falling away into the gap.
    stub = c.mask(lambda p: p.poly([(16, FOOT), (16, G), (g0, G), (g0 + 10, G + 40), (g0 - 10, FOOT)]))
    c.put(stub, ROCK)
    rim(c, stub, 0.35)
    # The plank bridge over the gap: planks on two ropes, some missing (it is
    # dropped through), a post at each end.
    c.put(c.mask(lambda p: [p.rect(x, G - 50, x + 8, G + 6) for x in (g0 - 14, g1 + 6)]), TIMBER)
    c.put(c.mask(lambda p: [p.line([(g0 - 10, G - 46), ((g0 + g1) / 2, G - 20), (g1 + 10, G - 46)], 1.4),
                            p.line([(g0, G + 2), (g1, G + 2)], 1.4)]), WIRE)
    missing = {3, 4, 9, 13, 14, 15}
    c.put(c.mask(lambda p: [p.rect(x, G, x + 16, G + 6) for i, x in enumerate(range(g0, g1 - 8, 20)) if i not in missing]), (120, 92, 70))
    ground(c, g1, TOWER[0])
    c.put(c.mask(lambda p: p.poly([(g1, G), (g1 - 30, G + 30), (g1 - 10, FOOT), (g1 + 10, FOOT)])), ROCK)
    wire(c, g1 + 40, g1 + 400, G)
    c.put(c.mask(lambda p: [p.rect(x, 374, x + 4, G) for x in (471, 590)]), TIMBER)
    c.put(c.mask(box(420, 342, 644, 379)), WALK_BEAM)
    c.put(c.mask(box(425, 347, 639, 374)), TIMBER)
    searchlight(c, 900, -0.5)
    wire(c, 1200, 1700, G)


def gantry(c, x0, x1, y, posts):
    for x in posts:
        c.put(c.mask(box(x - 4, y + 12, x + 4, G)), IRON)
        c.put(c.mask(lambda p: p.line([(x, y + 42), (x + 23, y + 12)], 5)), IRON)
        c.put(c.mask(box(x - 3, y + 17, x - 1, G - 4)), WALK_BEAM)
    c.put(c.mask(box(x0, y, x1, y + 16)), WALK_BEAM)
    c.put(c.mask(box(x0, y, x1, y + 4)), WALK_EDGE)
    c.put(c.mask(lambda p: [p.ellipse(x, y + 10, 1.6) for x in range(x0 + 11, x1 - 5, 27)]), WIRE)


def east(c, k):
    t0, t1 = TOWER
    ground(c, GAP[1], t0)
    ground(c, t1, W - 16)
    # The top of the watchtower, coming up through the ridge: its posts and
    # its ladder (the engine draws the ladder; the posts are here).
    c.put(c.mask(lambda p: [p.rect(x, G - 40, x + 8, FOOT) for x in (t0, t1 - 8)]), TIMBER)
    c.put(c.mask(lambda p: p.rect(t0 - 6, G - 44, t1 + 6, G - 38)), TIMBER)
    # The sentry hut: planks, a lit window, a tin roof.
    h0, h1 = 2300, 2460
    hut = c.mask(box(h0, 342, h1, G))
    c.put(hut, TIMBER)
    c.put(hut * c.mask(lambda p: [p.rect(x, 342, x + 1.4, G) for x in range(h0, h1, 12)]), NEAR_BLACK, 0.6)
    c.put(c.mask(box(h0 + 30, G - 80, h0 + 70, G - 50)), WINDOW)
    c.light(c.mask(lambda p: p.ellipse(h0 + 50, G - 65, 50, 30), blur=10), WINDOW, 0.25)
    rim(c, hut, 0.4)
    c.put(c.mask(lambda p: p.line([(2000, 347), (2130, 384), (2310, 379), (2602, 408), (2800, 394)], 2)), NEAR_BLACK)
    gantry(c, 1824, 1920, 416, (1848, 1882))
    gantry(c, 1920, 2240, 352, (1944, 2020, 2112, 2200))
    gantry(c, 2288, 2480, 336, ())
    gantry(c, 2512, 2656, 368, (2540, 2614))
    gantry(c, 2688, 2832, 400, (2712, 2800))
    gantry(c, 2880, 2960, 432, (2910, 2932))
    searchlight(c, 2000, 0.35, floor=352)
    searchlight(c, 2800, -0.25, floor=400)
    c.put(c.mask(lambda p: [p.rect(x, 277, x + 5, 336) for x in (2304, 2456)]), IRON)
    c.put(c.mask(box(2264, 223, 2504, 287)), WALK_BEAM)
    c.put(c.mask(box(2270, 229, 2498, 281)), (45, 34, 35))
    wire(c, 3260, 3560, G)


PIECES: Dict[str, Piece] = {
    "ridge_west": Piece((16, 0, 1816, FOOT), west),
    "ridge_east": Piece((1784, 0, W - 16, FOOT), east),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
