"""Ume's tea house inside (`ninja_village_tea_room`, PvN dimension): the tea
room on the ground, the guest rooms up the step chest.

Drawn in room coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/ninja_village/make_specs.py`
(`tea_room`): the floor (y 448), the ceiling (to y 32), the door (x 40),
the step chest's treads (STEPS: x0, x1, top) and the loft's floor (x 560..
1008, y 256), all walked on.

- `tea_room`: plaster and dark timber; a raised floor of tatami; low
  tables and cushions; the sunken hearth with its kettle on the pot hook;
  the menu of wooden plaques; the alcove with a scroll and one flower; the
  sliding door out; the step chest (a stair of drawers) up to the loft; up
  there, two guest rooms behind sliding panels, one with its futon laid
  out and, under it, a child's pair of straw sandals.

Everyday village things, drawn with care: no costume and no joke at the
culture's cost. Animations: ``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .ninja_village_props import CEDAR, CEDAR_LIGHT, INDIGO, PAL, PAPER, PLASTER, SHOJI, TIMBER, VERMILION, paper_lantern, post, walk_edge

W, FLOOR, CEILING = 1024, 448, 32
LOFT = (560, 1008, 256)
#: The step chest's treads (x0, x1, top), up from the floor to the loft.
STEPS = ((432, 464, 416), (464, 496, 384), (496, 528, 352), (528, 560, 320), (560, 592, 288))
TATAMI = (196, 186, 124)
TATAMI_EDGE = (40, 50, 40)


def tatami(c, x0, x1, y):
    """Mats seen at their edge: a band, its cloth border, the weave."""
    c.put(c.mask(box(x0, y, x1, y + 8)), TATAMI)
    c.put(c.mask(lambda p: [p.rect(x, y, x + 3, y + 8) for x in np.arange(x0, x1, 90)]), TATAMI_EDGE)
    c.put(c.mask(box(x0, y, x1, y + 1.2)), mix(TATAMI, (255, 250, 220), 0.4))


def room(c, k):
    g = FLOOR
    rng = c.rand("tea_room")
    wall = c.mask(box(16, CEILING, W - 16, g))
    c.put(wall, PLASTER)
    c.tone(wall * (c.noise("tea_plaster", 20, 10, 2) - 0.5), 0.08)
    c.put(c.mask(box(16, CEILING, W - 16, CEILING + 14)), TIMBER)
    for x in (24, 300, 560, 780, 1000):
        post(c, x, CEILING, g, 10, TIMBER)
    # The loft's beam and floor (walked on), and its two guest rooms.
    lx0, lx1, loft = LOFT
    c.put(c.mask(box(lx0, loft, lx1, loft + 18)), TIMBER)
    walk_edge(c, lx0, lx1, loft, CEDAR_LIGHT)
    for rx0, rx1 in ((600, 780), (800, 990)):
        c.put(c.mask(box(rx0, CEILING + 40, rx1, loft)), (226, 214, 184))
    # Room one: its panels slid open on the futon; under it, the sandals.
    c.put(c.mask(box(600, CEILING + 40, 690, loft)), SHOJI)
    c.put(c.mask(lambda p: ([p.rect(x, CEILING + 40, x + 1.4, loft) for x in np.arange(600, 690, 15)], [p.rect(600, y, 690, y + 1.4) for y in np.arange(CEILING + 52, loft, 22)])), CEDAR)
    c.put(c.mask(lambda p: p.rect(700, loft - 14, 776, loft)), (236, 232, 222))
    c.put(c.mask(lambda p: p.rect(700, loft - 22, 776, loft - 14)), (120, 60, 70))
    c.put(c.mask(lambda p: p.ellipse(712, loft - 18, 10, 5)), (236, 232, 222))
    for sx in (746, 756):
        c.put(c.mask(lambda p: p.ellipse(sx, loft - 2, 4, 2)), (200, 176, 110))
        c.put(c.mask(lambda p: p.line([(sx - 2, loft - 3), (sx, loft - 1), (sx + 2, loft - 3)], 0.8)), VERMILION)
    # Room two: its panels shut, a lantern by them.
    c.put(c.mask(box(800, CEILING + 40, 990, loft)), SHOJI)
    c.put(c.mask(lambda p: ([p.rect(x, CEILING + 40, x + 1.4, loft) for x in np.arange(800, 990, 15)], [p.rect(800, y, 990, y + 1.4) for y in np.arange(CEILING + 52, loft, 22)])), CEDAR)
    c.light(c.mask(box(800, CEILING + 40, 990, loft), blur=8), (255, 230, 180), 0.2)
    # The step chest: a stair of drawers, each tread walked on.
    for x0, x1, top in STEPS:
        c.put(c.mask(box(x0, top, x1, g)), CEDAR)
        c.put(c.mask(lambda p: [p.rect(x0 + 3, y, x1 - 3, y + 1.2) for y in np.arange(top + 16, g, 28)]), TIMBER)
        c.put(c.mask(lambda p: [p.ellipse((x0 + x1) / 2, y + 8, 1.6) for y in np.arange(top + 16, g - 10, 28)]), (190, 160, 90))
        walk_edge(c, x0, x1, top, CEDAR_LIGHT)
    # The tea room: tatami, the sunken hearth and its kettle, low tables.
    tatami(c, 16, W - 16, g - 8)
    hx = 330
    c.put(c.mask(box(hx - 40, g - 8, hx + 40, g)), (60, 50, 44))
    c.put(c.mask(lambda p: p.ellipse(hx, g - 8, 30, 3)), (90, 60, 50))
    c.light(c.mask(lambda p: p.ellipse(hx, g - 8, 30, 10), blur=6), (255, 140, 60), 0.5)
    c.put(c.mask(lambda p: (p.rect(hx - 1, CEILING + 14, hx + 1, g - 60), p.rect(hx - 12, g - 66, hx + 12, g - 62))), TIMBER)
    c.put(c.mask(lambda p: p.poly([(hx - 6, g - 62), (hx + 6, g - 62), (hx + 4, g - 54), (hx - 4, g - 54)])), CEDAR_LIGHT)
    c.put(c.mask(lambda p: (p.ellipse(hx, g - 40, 13, 11), p.rect(hx - 6, g - 56, hx + 6, g - 50))), (40, 40, 44))
    c.put(c.mask(lambda p: p.line([(hx - 10, g - 54), (hx, g - 58), (hx + 10, g - 54)], 1.2)), (40, 40, 44))
    for i in range(3):
        c.put(c.mask(lambda p: p.ellipse(hx + 14 + i * 4, g - 50 - i * 12, 4 + i * 2, 3 + i), blur=3), (250, 250, 250), 0.25)
    for tx in (700, 900):
        c.put(c.mask(lambda p: (p.rect(tx - 34, g - 30, tx + 34, g - 24), p.rect(tx - 28, g - 24, tx - 24, g - 8), p.rect(tx + 24, g - 24, tx + 28, g - 8))), CEDAR)
        c.put(c.mask(lambda p: (p.ellipse(tx - 8, g - 34, 5, 4), p.ellipse(tx + 10, g - 34, 5, 4))), (220, 214, 196))
        for cx in (tx - 48, tx + 48):
            c.put(c.mask(lambda p: p.rect(cx - 14, g - 13, cx + 14, g - 8)), INDIGO)
    # The menu of wooden plaques, and the alcove with its scroll and flower.
    for i in range(6):
        x = 630 + i * 30
        c.put(c.mask(box(x, 296, x + 22, 350)), CEDAR_LIGHT)
        c.put(c.mask(lambda p: [p.line([(x + 11, 302 + j * 12), (x + 11 + rng.uniform(-3, 3), 309 + j * 12)], 1.6) for j in range(4)]), (40, 30, 26))
    c.put(c.mask(box(120, 90, 240, g - 70)), (214, 196, 156))
    c.put(c.mask(box(120, g - 74, 240, g - 66)), TIMBER)
    c.put(c.mask(box(160, 110, 200, 280)), (240, 234, 216))
    c.put(c.mask(lambda p: p.line([(180, 130), (176, 190), (184, 250)], 4)), (30, 28, 30))
    c.put(c.mask(lambda p: (p.ellipse(220, g - 86, 5, 9), p.line([(220, g - 94), (216, g - 120)], 1))), (90, 110, 120))
    c.put(c.mask(lambda p: p.ellipse(215, g - 122, 4)), VERMILION)
    # The sliding door out (the room's door zone, x 40..88).
    c.put(c.mask(box(34, g - 104, 94, g)), TIMBER)
    c.put(c.mask(box(40, g - 96, 88, g)), CEDAR)
    panes = c.mask(box(46, g - 90, 82, g - 30))
    c.put(panes, SHOJI)
    c.put(c.mask(lambda p: ([p.rect(x, g - 90, x + 1.4, g - 30) for x in np.arange(55, 82, 9)], [p.rect(46, y, 82, y + 1.4) for y in np.arange(g - 78, g - 30, 12)])) * panes, scale(CEDAR, 0.7))
    # Lanterns.
    for x in (420, 860):
        paper_lantern(c, x, CEILING + 20 if x < 500 else loft + 22, PAPER, 0.8)


PIECES: Dict[str, Piece] = {
    "tea_room": Piece((16, CEILING, W - 16, FLOOR), room),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
