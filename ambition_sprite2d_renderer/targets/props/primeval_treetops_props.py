"""The treetops over the primeval run (`primeval_treetops`, the jungle
dimension): up the great tree's rope ladder out of the run, east along the
canopy, and down through a gap in the leaves into the rookery.

Drawn in room coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/primeval/treetops.py`: in the run, its
floor (y 480) and the hole in its ceiling over the great tree (x 896..960);
in the treetops, the canopy's floor (y 512 to the room's foot, 576), the
hole the tree comes up through (x 96..160, its hatch), the platforms
(`PLATFORMS`, walked on), the gap down to the rookery (x 2720..2800). The
rope ladders are the engine's.

- `run_great_tree`: the great tree in the run: a buttressed trunk from the
  floor up through the room's top, lianas hanging, a ranger's sign nailed on.
- `treetops_west`: the canopy's leaves, the great tree's crown round its
  hatch; the canopy research station on its deck (a hut of planks and
  thatch, its door hanging, a weather vane, a notebook left open); rope
  bridges between the crowns.
- `treetops_east`: a pterosaur's nest on the highest crown (sticks, three
  eggs, one hatched: the shell, footprints); more bridges; the gap in the
  leaves at the east end, lianas hanging down it.

Animations: ``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .primeval_props import LEAF, LEAF_LIGHT, MOSS, PAL

RUN_FLOOR = 480
TREE = (896, 960)
W, G, H = 2880, 512, 576
HATCH = (96, 160)
GAP = (2720, 2800)
#: The platforms (x0, x1, y), walked on: the station's deck, the bridges, the
#: nest's crown.
PLATFORMS = ((280, 560, 400), (640, 960, 336), (1040, 1360, 400), (1440, 1760, 288), (1840, 2160, 384), (2240, 2560, 320))
STATION, NEST = PLATFORMS[0], PLATFORMS[3]
BARK = (92, 64, 44)
BARK_DARK = (60, 42, 30)
BARK_LIGHT = (140, 104, 70)
LIANA = (70, 96, 44)
PLANK = (150, 112, 70)
PLANK_DARK = (100, 74, 48)
ROPE = (196, 170, 120)
THATCH = (170, 140, 80)
PAPER = (236, 228, 200)
EGG = (226, 214, 180)
LEAF_DARK = (34, 70, 32)


def bark(c, m, seed):
    c.put(m, BARK)
    c.put(m * (c.noise(seed, 6, 30, 3) > 0.62), BARK_DARK, 0.8)
    c.put(m * (c.noise(seed + "_hi", 8, 40, 2) > 0.7), BARK_LIGHT, 0.5)


def lianas(c, xs, y0, rng):
    for x in xs:
        ln = rng.uniform(80, 200)
        c.put(c.mask(lambda p: p.line([(x, y0), (x + rng.uniform(-10, 10), y0 + ln * 0.5), (x + rng.uniform(-6, 6), y0 + ln)], 2.4)), LIANA)
        c.put(c.mask(lambda p: [p.ellipse(x + rng.uniform(-6, 6), y0 + rng.uniform(10, ln), 5, 3) for _ in range(5)]), LEAF_LIGHT)


def great_tree(c, k):
    t0, t1 = TREE
    m = c.mask(lambda p: (p.rect(t0 - 40, 0, t1 + 40, RUN_FLOOR),
                          p.poly([(t0 - 40, RUN_FLOOR - 160), (t0 - 110, RUN_FLOOR), (t0 - 40, RUN_FLOOR)]),
                          p.poly([(t1 + 40, RUN_FLOOR - 140), (t1 + 120, RUN_FLOOR), (t1 + 40, RUN_FLOOR)]),
                          p.poly([(t0 - 20, RUN_FLOOR - 100), (t0 - 60, RUN_FLOOR), (t0, RUN_FLOOR)])))
    bark(c, m, "great_tree")
    c.tone(m * np.clip((c.x - (t0 - 40)) / 200, 0, 1), -0.25)
    rng = c.rand("great_tree_lianas")
    lianas(c, (t0 - 30, t0 - 6, t1 + 20, t1 + 34), 0, rng)
    # Moss on its buttresses; the ranger's sign nailed on.
    mr = c.rand("tree_moss")
    c.put(m * c.mask(lambda p: [p.ellipse(mr.uniform(t0 - 90, t1 + 100), mr.uniform(RUN_FLOOR - 70, RUN_FLOOR - 6), mr.uniform(10, 26), mr.uniform(5, 10)) for _ in range(14)]), MOSS, 0.85)
    c.put(c.mask(box(t1 + 4, 300, t1 + 34, 340)), PLANK)
    c.put(c.mask(lambda p: [p.rect(t1 + 8, y, t1 + 30, y + 2) for y in (310, 318, 326)]), PLANK_DARK)


def leaves(c, x0, x1, seed):
    """The canopy's floor of leaves, G to the foot, crowns bulging up."""
    m = c.mask(lambda p: (p.rect(x0, G + 6, x1, H), *[p.ellipse(x, G + 14, 70, 26) for x in range(int(x0), int(x1) + 60, 90)]))
    c.put(m, LEAF_DARK)
    c.put(m * (c.noise(seed, (x1 - x0) / 40, 3, 3) > 0.5), LEAF)
    c.put(m * (c.noise(seed + "_hi", (x1 - x0) / 25, 4, 2) > 0.72) * (c.y < G + 30), LEAF_LIGHT)
    return m


def platform(c, x0, x1, y, rope=True):
    c.put(c.mask(box(x0, y, x1, y + 8)), PLANK)
    c.put(c.mask(lambda p: [p.rect(x, y, x + 1.4, y + 8) for x in range(int(x0) + 14, int(x1), 16)]), PLANK_DARK)
    if rope:
        c.put(c.mask(lambda p: [p.line([(x0, y - 30), ((x0 + x1) / 2, y - 18), (x1, y - 30)], 1.4), p.rect(x0, y - 32, x0 + 3, y), p.rect(x1 - 3, y - 32, x1, y)]), ROPE)


def crown(c, x, top, rng):
    """A tree's trunk up from the leaves to `top`, its crown round it."""
    m = c.mask(box(x - 16, top, x + 16, G + 20))
    bark(c, m, f"crown_{x}")
    c.put(c.mask(lambda p: [p.ellipse(x + rng.uniform(-90, 90), top - rng.uniform(0, 40), rng.uniform(40, 70), rng.uniform(22, 34)) for _ in range(6)]), LEAF)
    c.put(c.mask(lambda p: [p.ellipse(x + rng.uniform(-80, 80), top - rng.uniform(10, 50), rng.uniform(20, 40), rng.uniform(10, 18)) for _ in range(5)]), LEAF_LIGHT, 0.8)


def west(c, k):
    rng = c.rand("treetops_w")
    for x, top in ((420, 330), (800, 270), (1200, 330)):
        crown(c, x, top, rng)
    m = leaves(c, 16, HATCH[0], "tt_w0")
    leaves(c, HATCH[1], 1440, "tt_w1")
    # The great tree's top through the leaves, round its hatch.
    h0, h1 = HATCH
    t = c.mask(lambda p: (p.rect(h0 - 30, G - 60, h0, H), p.rect(h1, G - 60, h1 + 30, H)))
    bark(c, t, "great_top")
    c.put(c.mask(box(h0, G, h1, G + 8)), PLANK)
    c.put(c.mask(lambda p: [p.rect(x, G, x + 1.4, G + 8) for x in range(h0 + 14, h1, 16)]), PLANK_DARK)
    c.put(c.mask(lambda p: [p.ellipse(x, G - 70, 60, 30) for x in (h0 - 20, h1 + 30)]), LEAF)
    # The research station on its deck: planks, thatch, its door hanging.
    x0, x1, y = STATION
    platform(c, x0, x1, y, rope=False)
    hx0, hx1 = x0 + 40, x0 + 200
    hut = c.mask(box(hx0, y - 110, hx1, y))
    c.put(hut, PLANK)
    c.put(hut * c.mask(lambda p: [p.rect(x, y - 110, x + 1.4, y) for x in range(hx0, hx1, 14)]), PLANK_DARK)
    c.put(c.mask(lambda p: p.poly([(hx0 - 20, y - 106), ((hx0 + hx1) / 2, y - 160), (hx1 + 20, y - 106)])), THATCH)
    c.put(c.mask(lambda p: [p.line([(x, y - 150 + (x - hx0) * 0.0), (x - 10, y - 104)], 1.2) for x in range(hx0 - 10, hx1 + 20, 8)]), scale(THATCH, 0.75))
    c.put(c.mask(box(hx0 + 20, y - 80, hx0 + 56, y)), (30, 24, 20))
    c.put(c.mask(lambda p: p.poly([(hx0 + 56, y - 80), (hx0 + 80, y - 74), (hx0 + 80, y - 4), (hx0 + 56, y)])), PLANK_DARK)
    c.put(c.mask(box(hx0 + 100, y - 80, hx0 + 140, y - 54)), (180, 200, 190))
    c.put(c.mask(lambda p: (p.line([((hx0 + hx1) / 2, y - 160), ((hx0 + hx1) / 2, y - 190)], 1.6),
                            p.poly([((hx0 + hx1) / 2, y - 190), ((hx0 + hx1) / 2 + 22, y - 184), ((hx0 + hx1) / 2, y - 180)]))), (60, 60, 60))
    # The notebook left open on a crate on the deck.
    c.put(c.mask(box(x1 - 90, y - 30, x1 - 50, y)), PLANK_DARK)
    c.put(c.mask(lambda p: p.poly([(x1 - 96, y - 30), (x1 - 70, y - 34), (x1 - 44, y - 30), (x1 - 70, y - 28)])), PAPER)
    for x0, x1, y in PLATFORMS[1:3]:
        platform(c, x0, x1, y)
    lianas(c, (600, 990, 1010, 1380), 120, rng)


def east(c, k):
    rng = c.rand("treetops_e")
    for x, top in ((1600, 230), (2000, 320), (2400, 260)):
        crown(c, x, top, rng)
    leaves(c, 1440, GAP[0], "tt_e0")
    leaves(c, GAP[1], W - 16, "tt_e1")
    for x0, x1, y in PLATFORMS[3:]:
        platform(c, x0, x1, y)
    # The nest on the highest crown: sticks, three eggs, one hatched.
    x0, x1, y = NEST
    nx = x0 + 90
    c.put(c.mask(lambda p: [p.line([(nx - 70 + i * 9, y - 4 - (i % 3) * 4), (nx - 40 + i * 7, y - 30 + (i % 4) * 5)], 2.4) for i in range(16)]), BARK_LIGHT)
    c.put(c.mask(lambda p: p.ellipse(nx, y - 10, 70, 14)), BARK)
    for j, ex in enumerate((nx - 30, nx, nx + 28)):
        if j == 2:
            c.put(c.mask(lambda p: (p.poly([(ex - 14, y - 20), (ex - 10, y - 36), (ex - 4, y - 28), (ex + 2, y - 38), (ex + 8, y - 28), (ex + 14, y - 34), (ex + 14, y - 20)]))), EGG)
        else:
            c.put(c.mask(lambda p: p.ellipse(ex, y - 32, 14, 18)), EGG)
            c.put(c.mask(lambda p: [p.ellipse(ex + dx, y - 34 + dy, 2, 1.6) for dx, dy in ((-5, -4), (4, 2), (-2, 8))]), (170, 150, 110))
    # Footprints going off the crown: three toes, a long stride.
    c.put(c.mask(lambda p: [p.line([(x, y + 3), (x + dx, y + 6)], 1) for x in range(int(nx) + 80, int(x1) - 10, 40) for dx in (-4, 0, 4)]), PLANK_DARK)
    # The gap at the east end, lianas hanging down it.
    lianas(c, (GAP[0] + 10, GAP[0] + 40, GAP[1] - 16), G - 40, rng)
    lianas(c, (1700, 2250, 2620), 140, rng)


PIECES: Dict[str, Piece] = {
    "run_great_tree": Piece((TREE[0] - 120, 0, TREE[1] + 130, RUN_FLOOR), great_tree),
    "treetops_west": Piece((16, 60, 1440, H), west),
    "treetops_east": Piece((1440, 60, W - 16, H), east),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
