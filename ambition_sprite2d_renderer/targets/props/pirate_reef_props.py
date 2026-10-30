"""The Wreckers' Reef (`pirate_wreckers_reef`, PvN dimension): out of the
Pirate Port, east of the docks: a galleon broken on the reef, and the
wreckers who lured her there with a false light.

Drawn in room coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/pirate_port/make_specs.py` (`reef`): the
shore (y 768, x ..420), the reef's rocks (x 500..580 top 740, 700..780 top
720), the boarding net (x 800..880, y 680), the stern section (x 880..1480,
deck y 616, its aft castle y 520 from x 1320), the bow section (x 1760..2300,
deck y 672), the mast stump's top (x 1960..2060, y 440), the east rocks
(x 2380.., top 640); the sea from y 784 to the bed at 928.

- `reef_shore`: sand and rocks, the wreckers' false lighthouse (a lantern
  and a mirror on a pole, lit to look like a harbour), salvage crates and
  barrels, a net.
- `reef_wreck`: the galleon in two: the stern with its windows and aft
  castle, the main mast fallen across the gap, a torn sail; the bow with its
  figurehead (a lion) and bowsprit, the foremast's stump and its broken
  top; the rocks at the east end.

Animations: ``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .eureka_props import Batch, edge_line
from .pirate_port_props import HULL, HULL_BAND, HULL_DARK, PAL, PLANK, PLANK_DARK, PLANK_LIGHT, ROPE, SAIL, TIMBER, planks

DECK, SEA, BED = 768, 784, 928
ROCKS = ((500, 580, 740), (700, 780, 720))
NET = (800, 880, 680)
STERN = (880, 1480, 616)
AFT = (1320, 1480, 520)
BOW = (1760, 2300, 672)
STUMP = (1960, 2060, 440)
EAST_ROCKS = (2380, 2544, 640)
SAND = (206, 186, 140)
ROCK = (92, 96, 96)
LAMP = (255, 214, 140)


def rock(c, x0, x1, top, bottom=BED, tag="rock"):
    m = c.mask(lambda p: p.poly([(x0, bottom), (x0 + 6, top + 10), (x0 + (x1 - x0) * 0.4, top), (x1 - 8, top + 4), (x1, bottom)]))
    c.put(m, ROCK)
    c.tone(m * (c.noise(("reef", tag, x0), 4, 6, 3) - 0.5), 0.35)
    c.put(m * c.mask(box(x0, top, x1, top + 4)), mix(ROCK, (255, 255, 255), 0.3))
    c.put(m * np.clip((c.noise(("weed", x0), 8, 4, 2) - 0.55) * 4, 0, 1) * (c.y > SEA - 10), (60, 96, 60))


def shore(c, k):
    # The sand bank, its edge running into the sea.
    sand = c.mask(lambda p: p.poly([(0, DECK), (420, DECK), (470, BED), (0, BED)]))
    c.put(sand, SAND)
    c.tone(sand * (c.noise("sand", 12, 4, 2) - 0.5), 0.15)
    for i, (x0, x1, top) in enumerate(ROCKS):
        rock(c, x0, x1, top, tag=i)
    # The false lighthouse: a pole, a lantern and a mirror, lit like a harbour.
    px = 300
    c.put(c.mask(box(px - 4, DECK - 200, px + 4, DECK)), TIMBER)
    c.put(c.mask(lambda p: (p.line([(px - 30, DECK), (px, DECK - 120)], 3), p.line([(px + 30, DECK), (px, DECK - 120)], 3))), TIMBER)
    lan = c.mask(lambda p: p.rect(px - 12, DECK - 228, px + 12, DECK - 200))
    c.put(lan, LAMP)
    c.put(c.mask(lambda p: (p.rect(px - 14, DECK - 232, px + 14, DECK - 228), p.rect(px - 14, DECK - 200, px + 14, DECK - 196))), (40, 40, 44))
    c.put(c.mask(lambda p: p.poly([(px + 14, DECK - 236), (px + 34, DECK - 244), (px + 34, DECK - 186), (px + 14, DECK - 194)])), (200, 210, 220))
    c.light(c.mask(lambda p: p.poly([(px + 20, DECK - 226), (px + 20, DECK - 204), (860, DECK - 160), (860, DECK - 300)]), blur=12), LAMP, 0.25)
    c.light(c.mask(lambda p: p.ellipse(px, DECK - 214, 60), blur=18), LAMP, 0.4)
    # Salvage on the sand: crates, barrels, a net.
    for x, h in ((80, 40), (124, 30), (100, 70)):
        y1 = DECK if h != 70 else DECK - 40
        c.put(c.mask(box(x, y1 - min(h, 40), x + 40, y1)), PLANK)
        c.put(c.mask(lambda p: (p.rect(x, y1 - min(h, 40), x + 40, y1 - min(h, 40) + 3), p.line([(x + 2, y1 - 2), (x + 38, y1 - min(h, 40) + 2)], 2.5))), PLANK_DARK)
    for x in (180, 210):
        m = np.maximum(c.mask(lambda p: p.ellipse(x, DECK - 18, 13, 18)), c.mask(box(x - 12, DECK - 34, x + 12, DECK - 2)))
        c.put(m, PLANK)
        c.put(m * c.mask(lambda p: [p.rect(x - 14, y, x + 14, y + 2.4) for y in (DECK - 28, DECK - 8)]), (60, 60, 64))
    c.put(c.mask(lambda p: [p.line([(360 + i * 8, DECK), (380 + i * 6, DECK - 30)], 1) for i in range(6)] + [p.line([(356, DECK - 8 - j * 7), (420, DECK - 6 - j * 7)], 1) for j in range(4)]), ROPE)


def wreck(c, k):
    rng = c.rand("wreck")
    # The stern section: hull planks, gunports, stern windows, aft castle.
    s0, s1, sd = STERN
    hull = c.mask(lambda p: p.poly([(s0, sd), (s1, sd - 10), (s1 + 20, AFT[2]), (s1, BED), (s0 + 40, BED), (s0 - 10, sd + 60)]))
    c.put(hull, HULL)
    c.put(hull * c.mask(lambda p: [p.rect(s0 - 10, y, s1 + 20, y + 1.2) for y in range(sd + 12, BED, 14)]), HULL_DARK)
    c.put(hull * c.mask(box(s0 - 10, sd + 30, s1 + 20, sd + 38)), HULL_BAND)
    c.put(c.mask(lambda p: [p.rect(x, sd + 50, x + 22, sd + 66) for x in range(s0 + 40, s1 - 60, 90)]), (30, 22, 18))
    planks(c, k, AFT[0], AFT[2], s1 + 20, sd, HULL, step=12, tag="aft")
    c.put(c.mask(lambda p: [p.rect(x, AFT[2] + 30, x + 18, AFT[2] + 56) for x in range(AFT[0] + 20, s1, 40)]), (220, 200, 120), 0.7)
    edge_line(c, AFT[0], AFT[1], AFT[2], PLANK, 5)
    c.put(c.mask(lambda p: (p.rect(AFT[0], AFT[2] - 26, AFT[1], AFT[2] - 23), [p.rect(x, AFT[2] - 26, x + 3, AFT[2]) for x in range(AFT[0] + 2, AFT[1], 20)])), TIMBER)
    edge_line(c, s0, AFT[0], sd, PLANK, 5)
    # The broken end of the stern, splintered, toward the gap.
    c.put(c.mask(lambda p: p.poly([(s1, sd - 10), (s1 + 8, sd + 20), (s1 - 6, sd + 50), (s1 + 10, sd + 90), (s1, BED)])), HULL_DARK)
    # The main mast fallen across the gap, its torn sail.
    c.put(c.mask(lambda p: p.line([(s1 - 60, sd - 6), (BOW[0] + 120, BOW[2] + 40)], 12)), (112, 80, 52))
    sail = c.mask(lambda p: p.poly([(s1 - 20, sd - 4), (s1 + 140, sd + 30), (s1 + 120, SEA + 10), (s1 + 40, SEA - 10), (s1, sd + 60)]))
    c.put(sail, SAIL, 0.9)
    c.put(sail * c.mask(lambda p: [p.line([(s1 + 10 + i * 20, sd + 10 + i * 4), (s1 + 20 + i * 18, SEA)], 0.8) for i in range(6)]), (180, 170, 150))
    # The bow section: hull, figurehead, bowsprit, the foremast's stump.
    b0, b1, bd = BOW
    bow = c.mask(lambda p: p.poly([(b0, bd + 10), (b1 - 40, bd), (b1 + 30, bd - 40), (b1 + 10, BED), (b0 + 20, BED), (b0 - 10, bd + 80)]))
    c.put(bow, HULL)
    c.put(bow * c.mask(lambda p: [p.rect(b0 - 10, y, b1 + 30, y + 1.2) for y in range(bd + 12, BED, 14)]), HULL_DARK)
    c.put(bow * c.mask(box(b0 - 10, bd + 30, b1 + 30, bd + 38)), HULL_BAND)
    edge_line(c, b0, b1, bd, PLANK, 5)
    c.put(c.mask(lambda p: p.line([(b1 + 10, bd - 30), (b1 + 120, bd - 130)], 8)), (112, 80, 52))
    lx, ly = b1 + 28, bd - 30
    lion = c.mask(lambda p: (p.ellipse(lx, ly, 16, 18), p.ellipse(lx + 10, ly + 2, 10, 8)))
    c.put(lion, (210, 170, 70))
    c.put(c.mask(lambda p: [p.line([(lx, ly), (lx + 22 * math.cos(a), ly + 22 * math.sin(a))], 3) for a in np.linspace(math.pi * 0.6, math.pi * 1.6, 9)]), (170, 120, 40))
    c.put(c.mask(lambda p: p.ellipse(lx + 8, ly - 3, 2)), (40, 30, 20))
    x0, x1, top = STUMP
    mx = (x0 + x1) / 2
    c.put(c.mask(box(mx - 9, top, mx + 9, bd)), (112, 80, 52))
    c.put(c.mask(lambda p: p.poly([(mx - 9, top), (mx - 2, top - 26), (mx + 4, top - 8), (mx + 9, top - 20), (mx + 9, top)])), (112, 80, 52))
    planks(c, k, x0, top, x1, top + 10, PLANK, step=5, vertical=True, tag="stump_top")
    edge_line(c, x0, x1, top, PLANK, 4)
    c.put(c.mask(lambda p: (p.line([(mx, top + 20), (b0 + 20, bd)], 1.2), p.line([(mx, top + 20), (b1 - 30, bd)], 1.2))), ROPE)
    # The rocks at the east end.
    rock(c, EAST_ROCKS[0], EAST_ROCKS[1], EAST_ROCKS[2], tag="east")


PIECES: Dict[str, Piece] = {
    "reef_shore": Piece((0, 520, 860, BED + 32), shore),
    "reef_wreck": Piece((860, 280, 2560, BED + 32), wreck),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
