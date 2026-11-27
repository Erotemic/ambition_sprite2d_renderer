"""Scenery of the Unfinished dimension, the one the Boss's agents are still
building (gate address INSTALLING, `docs/planning/game/unfinished-dimension.md`).

The rooms are written by
`game/ambition_map_assets/ambition_content/generators/unfinished/make_specs.py`.
Each piece is drawn in its room's coordinates (`_district_props`): where the
room places a walk line (a deck of the scaffold), the piece draws the light
top edge of it at that y. The numbers here are the generator's; change them
together.

Held down in colour (Jon found the concept sheets too colourful): unpainted
greys and browns, blueprint ink for what is only drawn, one accent, the
yellow of a hard hat.

- The Staging Area (floor y 640): the site cabin; the survey post (the
  easel and the theodolite); three trees, painted on one side and still a
  drawing on the other; the scaffold, its decks at y 512 and 384.
- The Draft (the built ground's floor y 640, the void under it): the
  ground's torn edge and the water that runs off it; the cranes' cables
  down to the slabs and the painter's platform, and the outlines of the
  platforms not built yet.
- The Site Office (floor y 512): the three gauges, GRAVITY, WEATHER and
  LAYERS; the backlog board and the desk with the spec on it.

Nothing here is writing: the words of the rooms are their signs.

Animations: ``idle``, 1 frame each.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale

PAL = {
    "stone": (170, 164, 158), "stone_light": (210, 206, 200), "trim": (232, 190, 70), "dark": (30, 28, 30),
    "glass_top": (180, 200, 220), "glass_low": (70, 80, 100), "lamp": (255, 224, 160), "wood": (120, 90, 60),
    "leaf": (110, 132, 96), "iron": (60, 62, 70), "brass": (200, 170, 90), "glaze": (210, 200, 180),
}

INK = (120, 140, 176)
INK_LIGHT = (170, 190, 220)
PAPER = (226, 228, 232)
BLUEPRINT = (70, 96, 140)
STEEL = (74, 78, 90)
STEEL_LIGHT = (120, 124, 138)
STEEL_DARK = (44, 46, 54)
HAT = (232, 190, 70)
WOOD = (120, 90, 60)
WOOD_DARK = (76, 56, 40)
CABIN = (150, 96, 84)
CABIN_DARK = (100, 64, 58)
LEAF = (110, 132, 96)
LEAF_DARK = (80, 98, 72)
BARK = (100, 78, 60)
WATER = (170, 196, 220)
WATER_LIGHT = (230, 238, 246)
GLASS = (180, 200, 220)
LAMP = (255, 224, 160)
NOTE = (236, 226, 170)
DIAL = (40, 42, 50)
LIQUIDS = ((120, 160, 190), (200, 170, 90), (150, 120, 170))

#: The Staging Area.
FLOOR = 640
DECKS = (512, 384)
SCAFFOLD = (1800, 2040)
SCAFFOLD_STEPS = ((1648, 1760, 576), (2032, 2144, 448), (2128, 2240, 512), (2208, 2320, 576))
#: The Draft.
SLABS = ((700, 860, 640), (960, 1120, 576), (1220, 1380, 640), (1740, 1900, 640), (2000, 2160, 576))
PAINTER = (1460, 1640, 560)
UNBUILT = ((870, 950, 720), (1500, 1580, 738), (1910, 1990, 700))
INSPECTION_DECKS = ((608, 640, 640), (640, 1008, 800), (1056, 1456, 768))
INSPECTION_LADDERS = ((656, 592, 800), (1408, 496, 768))
VOID_TOP = 1120
#: The Site Office.
OFFICE_FLOOR = 512
OFFICE_WORKTOP = 432


def walk_top(c, x0, x1, y, colour):
    c.put(c.mask(box(x0, y, x1, y + 3)), mix(colour, (255, 255, 240), 0.5))


def wire_box(c, x0, y0, x1, y1, w=1.5, colour=INK):
    """The outline of a thing that is only drawn so far, its grid in it."""
    c.put(c.mask(lambda p: p.line([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], w)), colour, 0.9)
    c.put(c.mask(lambda p: ([p.line([(x, y0), (x, y1)], w * 0.5) for x in np.arange(x0 + 16, x1, 16)],
                            [p.line([(x0, y), (x1, y)], w * 0.5) for y in np.arange(y0 + 16, y1, 16)])), colour, 0.45)
    c.light(c.mask(box(x0, y0, x1, y1), blur=6), INK_LIGHT, 0.12)


def crate(c, x0, y1, w, h):
    c.put(c.mask(box(x0, y1 - h, x0 + w, y1)), (150, 116, 76))
    c.tone(c.mask(box(x0 + w * 0.6, y1 - h, x0 + w, y1)), -0.15)
    c.put(c.mask(lambda p: (p.rect(x0, y1 - h, x0 + w, y1 - h + 3), p.rect(x0, y1 - 3, x0 + w, y1), p.line([(x0 + 3, y1 - 3), (x0 + w - 3, y1 - h + 3)], 2.5))), (100, 76, 50))


def stripes(c, x0, y0, x1, y1):
    """Hazard stripes, yellow and dark, on a band."""
    band = c.mask(box(x0, y0, x1, y1))
    c.put(band, STEEL_DARK)
    c.put(band * ((((c.x - c.y) // 10) % 2) == 0), HAT)


# ---------------------------------------------------------------------------
# The Staging Area
# ---------------------------------------------------------------------------


def site_cabin(c, k):
    """The site cabin: a plank hut with a pitched roof, a lit window, a lamp
    over the door (the door is the room's), crates by its wall."""
    x0, x1, g = 600, 880, FLOOR
    wall = c.mask(box(x0, 500, x1, g))
    c.put(wall, CABIN)
    c.put(c.mask(lambda p: [p.rect(x0, y, x1, y + 2) for y in np.arange(506, g, 14)]), CABIN_DARK, 0.6)
    c.tone(c.mask(box(x1 - 30, 500, x1, g)), -0.15)
    roof = c.mask(lambda p: p.poly([(x0 - 16, 504), (x1 + 16, 504), ((x0 + x1) / 2, 450)]))
    c.put(roof, (70, 74, 84))
    c.tone(roof * (c.x > (x0 + x1) / 2), -0.15)
    c.put(c.mask(box(x0 - 16, 500, x1 + 16, 508)), (90, 94, 104))
    # The window, lit; gears on its sill.
    c.put(c.mask(box(790, 540, 850, 590)), WOOD_DARK)
    glass = c.mask(box(795, 545, 845, 585))
    c.paint(glass, c.ramp([(545, LAMP), (585, mix(LAMP, CABIN, 0.4))]))
    c.put(c.mask(lambda p: (p.rect(818, 545, 822, 585), p.rect(795, 563, 845, 567))), WOOD_DARK)
    c.light(c.mask(lambda p: p.ellipse(820, 565, 60, 40), blur=16), LAMP, 0.25)
    # The lamp over the door.
    c.put(c.mask(lambda p: (p.rect(736, 518, 744, 524), p.poly([(728, 524), (752, 524), (746, 532), (734, 532)]))), STEEL_DARK)
    c.light(c.mask(lambda p: p.ellipse(740, 534, 30, 18), blur=10), LAMP, 0.5)
    crate(c, 620, g, 44, 36)
    crate(c, 630, g - 36, 30, 24)


def survey_post(c, k):
    """The survey post: an easel with a blueprint of a tree on it, rolls of
    plans in a crate, and a theodolite on its tripod looking east."""
    g = FLOOR
    # The easel.
    c.put(c.mask(lambda p: (p.line([(950, g), (972, 540)], 4), p.line([(1010, g), (988, 540)], 4), p.line([(980, 540), (996, g)], 3))), WOOD)
    board = c.mask(box(940, 540, 1020, 600))
    c.put(board, BLUEPRINT)
    c.put(c.mask(lambda p: ([p.rect(940, y, 1020, y + 0.8) for y in np.arange(546, 600, 8)], [p.rect(x, 540, x + 0.8, 600) for x in np.arange(946, 1020, 8)])) * board, INK_LIGHT, 0.4)
    c.put(c.mask(lambda p: (p.line([(980, 592), (980, 572)], 2), p.ring(980, 564, 12, 1.6), p.ring(970, 572, 7, 1.4), p.ring(990, 572, 7, 1.4))), PAPER, 0.9)
    c.put(c.mask(box(936, 600, 1024, 606)), WOOD_DARK)
    # Rolls of plans in a crate.
    crate(c, 1028, g, 32, 26)
    for dx in (0, 8, 16):
        c.put(c.mask(lambda p: p.line([(1034 + dx, g - 26), (1030 + dx, g - 48)], 5)), PAPER)
    # The theodolite on its tripod.
    tx = 1110
    c.put(c.mask(lambda p: (p.line([(tx, 586), (tx - 18, g)], 2.5), p.line([(tx, 586), (tx + 18, g)], 2.5), p.line([(tx, 586), (tx + 2, g)], 2.5))), WOOD)
    c.put(c.mask(lambda p: (p.rect(tx - 10, 572, tx + 10, 588), p.rect(tx - 4, 566, tx + 16, 576))), HAT)
    c.put(c.mask(lambda p: p.ellipse(tx + 16, 571, 3, 4)), STEEL_DARK)
    c.light(c.mask(lambda p: p.poly([(tx + 18, 570), (tx + 26, 556), (tx + 26, 586)]), blur=4), INK_LIGHT, 0.4)


def half_trees(c, k):
    """Three trees, each painted on its west side and still a drawing on its
    east: the bark and leaves stop at a line, and the outline goes on."""
    g = FLOOR
    for tx, h, r in ((1260, 250, 70), (1440, 300, 86), (1620, 230, 64)):
        cy = g - h + r
        trunk = c.mask(lambda p: p.poly([(tx - 10, g), (tx + 10, g), (tx + 6, cy + r * 0.5), (tx - 6, cy + r * 0.5)]))
        crown = c.mask(lambda p: (p.ellipse(tx, cy, r, r * 0.9), p.ellipse(tx - r * 0.55, cy + r * 0.35, r * 0.6, r * 0.5), p.ellipse(tx + r * 0.55, cy + r * 0.3, r * 0.6, r * 0.5)))
        west = (c.x < tx + 2).astype(np.float32)
        c.put(trunk * west, BARK)
        c.paint(crown * west, c.ramp([(cy - r, mix(LEAF, PAPER, 0.15)), (cy + r, LEAF_DARK)]))
        c.tone(crown * west * (c.noise(("leaves", tx), 20, 18, 2) - 0.5), 0.2)
        east = 1.0 - west
        edge = np.clip(crown - c.soften(crown, 2.0), 0, 1) * 3.0
        tedge = np.clip(trunk - c.soften(trunk, 2.0), 0, 1) * 3.0
        c.put(np.clip(edge + tedge, 0, 1) * east, INK)
        grid = ((np.abs(((c.x - tx) % 14) - 7) < 0.6) | (np.abs(((c.y - cy) % 14) - 7) < 0.6)).astype(np.float32)
        c.put(crown * east * grid, INK, 0.35)
        # The line where the painting stops.
        c.put(c.mask(box(tx, cy - r - 4, tx + 2, g)) * np.clip(crown + trunk, 0, 1), HAT, 0.8)


def scaffold(c, k):
    """The scaffold: two posts, decks at y 512 and 384, crossed braces, a
    lamp, and a hard hat left on the top deck."""
    x0, x1 = SCAFFOLD
    for x in (x0, x1 - 8):
        c.put(c.mask(box(x, 340, x + 8, FLOOR)), STEEL)
        c.tone(c.mask(box(x + 5, 340, x + 8, FLOOR)), -0.2)
    for ya, yb in ((FLOOR, DECKS[0]), (DECKS[0], DECKS[1])):
        c.put(c.mask(lambda p: (p.line([(x0 + 4, ya), (x1 - 4, yb + 12)], 3), p.line([(x1 - 4, ya), (x0 + 4, yb + 12)], 3))), STEEL_LIGHT, 0.8)
    for y in DECKS:
        c.put(c.mask(box(x0 - 6, y, x1 + 6, y + 12)), WOOD)
        c.put(c.mask(lambda p: [p.rect(x, y, x + 1.5, y + 12) for x in np.arange(x0, x1, 30)]), WOOD_DARK)
        walk_top(c, x0 - 6, x1 + 6, y, WOOD)
    c.put(c.mask(lambda p: ([p.rect(x, 340, x + 3, DECKS[1]) for x in (x0 + 4, x1 - 7)], p.rect(x0, 350, x1, 354))), STEEL_LIGHT)
    # The board for its sign, hazard-striped, hung under the top deck.
    stripes(c, x0 + 20, DECKS[1] + 30, x1 - 20, DECKS[1] + 38)
    c.put(c.mask(lambda p: p.poly([(x1 - 50, DECKS[1]), (x1 - 20, DECKS[1]), (x1 - 24, DECKS[1] - 10), (x1 - 35, DECKS[1] - 16), (x1 - 46, DECKS[1] - 10)])), HAT)
    c.put(c.mask(lambda p: p.ellipse(x1 - 2, DECKS[0] + 24, 5)), STEEL_DARK)
    c.light(c.mask(lambda p: p.ellipse(x1 - 2, DECKS[0] + 34, 40, 30), blur=12), LAMP, 0.4)

    for left, right, top in SCAFFOLD_STEPS:
        post_a, post_b = left + 14, right - 14
        c.put(c.mask(lambda p: (
            p.line([(post_a, top + 12), (post_b, FLOOR - 5)], 3),
            p.line([(post_b, top + 12), (post_a, FLOOR - 5)], 3),
        )), STEEL_LIGHT)
        c.put(c.mask(lambda p: [
            (p.rect(x - 3, top + 10, x + 3, FLOOR - 4), p.rect(x - 8, FLOOR - 4, x + 8, FLOOR))
            for x in (post_a, post_b)
        ]), STEEL)
        c.put(c.mask(box(left, top, right, top + 12)), WOOD)
        stripes(c, left, top + 7, left + 16, top + 12)
        stripes(c, right - 16, top + 7, right, top + 12)
        walk_top(c, left, right, top, WOOD)


# ---------------------------------------------------------------------------
# The Draft
# ---------------------------------------------------------------------------


def spill(c, k):
    """Where the built ground ends: its edge breaks into loose cubes, and the
    stream on it runs off and falls into the void."""
    g = FLOOR
    rng = c.rand("edge cubes")
    for _ in range(18):
        x = rng.uniform(560, 660)
        y = rng.uniform(g + 20, g + 260)
        s = rng.uniform(8, 20)
        if x > 600 or rng.random() < 0.5:
            wire_box(c, x, y, x + s, y + s, 1.2)
        else:
            c.put(c.mask(box(x, y, x + s, y + s)), (92, 80, 72))
    fall = c.mask(box(604, g - 6, 636, VOID_TOP))
    c.paint(fall, c.ramp([(g, WATER_LIGHT), (VOID_TOP, mix(WATER, (40, 42, 64), 0.6))]))
    c.put(fall * (np.sin(c.y * 0.3 + c.x * 0.5) > 0.6), WATER_LIGHT, 0.5)
    c.put(c.mask(box(570, g - 6, 640, g)), WATER, 0.9)
    rng = c.rand("spray")
    c.put(c.mask(lambda p: [p.ellipse(620 + rng.uniform(-30, 30), VOID_TOP - rng.uniform(0, 40), 2) for _ in range(20)]), WATER_LIGHT, 0.7)


def cranes(c, k):
    """The cranes' cables, down from out of sight to each slab; the painter's
    platform on its four cables with its hazard rail; and, in the gaps, the
    outlines of the platforms that are not built yet."""
    for x0, x1, top in SLABS:
        for x in (x0 + 16, x1 - 16):
            c.put(c.mask(lambda p: p.line([(x, 32), (x, top)], 1.6)), STEEL_LIGHT)
        c.put(c.mask(lambda p: p.line([(x0 + 16, top - 40), ((x0 + x1) / 2, top - 70), (x1 - 16, top - 40)], 1.6)), STEEL_LIGHT)
        c.put(c.mask(box((x0 + x1) / 2 - 6, top - 80, (x0 + x1) / 2 + 6, top - 64)), HAT)
    p0, p1, ptop = PAINTER
    for x in (p0 + 10, p1 - 10):
        c.put(c.mask(lambda p: p.line([(x, 32), (x, ptop - 34)], 1.6)), STEEL_LIGHT)
    c.put(c.mask(lambda p: ([p.rect(x, ptop - 34, x + 3, ptop) for x in (p0 + 8, (p0 + p1) / 2, p1 - 11)], p.rect(p0 + 8, ptop - 36, p1 - 8, ptop - 32))), STEEL_LIGHT)
    stripes(c, p0, ptop + 18, p1, ptop + 26)
    # Paint cans on the platform, one tipped.
    for x, colour in ((p0 + 30, (150, 176, 210)), (p0 + 52, (230, 232, 236))):
        c.put(c.mask(box(x, ptop - 18, x + 16, ptop)), colour)
        c.put(c.mask(box(x, ptop - 18, x + 16, ptop - 15)), STEEL_LIGHT)
    for x0, x1, y in UNBUILT:
        wire_box(c, x0, y, x1, y + 24)


def inspection_scaffold(c, k):
    """Draw the inspection decks and the ladders beside the suspended slabs."""
    for x, slab_bottom, deck_top in ((728, 672, 800), (820, 672, 800),
                                     (1080, 608, 768), (1256, 672, 768), (1344, 672, 768)):
        c.put(c.mask(box(x - 2, slab_bottom, x + 2, deck_top)), STEEL_LIGHT)
        c.put(c.mask(box(x - 5, slab_bottom, x + 5, slab_bottom + 7)), STEEL)
    for x0, x1, top in INSPECTION_DECKS:
        c.put(c.mask(box(x0, top, x1, top + 16)), STEEL)
        c.put(c.mask(box(x0 + 2, top + 3, x1 - 2, top + 9)), WOOD)
        c.put(c.mask(lambda p: [p.rect(x, top + 3, x + 2, top + 9)
                                for x in range(x0 + 16, x1, 16)]), WOOD_DARK)
        walk_top(c, x0, x1, top, HAT)
        stripes(c, x0, top + 9, x0 + 16, top + 16)
        stripes(c, x1 - 16, top + 9, x1, top + 16)
        bevel = min(32, (x1 - x0) // 3)
        c.put(c.mask(lambda p: p.line(
            [(x0 + 8, top + 16), (x0 + bevel, top + 32),
             (x1 - bevel, top + 32), (x1 - 8, top + 16)], 4
        )), STEEL)
    for x, top, bottom in INSPECTION_LADDERS:
        c.put(c.mask(lambda p: [p.rect(rail, top, rail + 4, bottom)
                                for rail in (x + 2, x + 26)]), WOOD_DARK)
        c.put(c.mask(lambda p: [p.rect(x + 6, y, x + 26, y + 4)
                                for y in range(top + 8, bottom, 16)]), HAT)


# ---------------------------------------------------------------------------
# The Site Office
# ---------------------------------------------------------------------------


def office_wall(c, k):
    """Timber panels and two windows. The windows show the site."""
    windows = ((46, 152, 164, 304), (984, 52, 1190, 142))
    wall = 1 - c.mask(lambda p: [p.rect(*rect) for rect in windows])
    c.put(wall, (103, 91, 83))
    for y in range(36, OFFICE_FLOOR, 34):
        c.put(c.mask(box(0, y, 1280, y + 2)) * wall, (78, 67, 63))
        c.put(c.mask(box(0, y + 2, 1280, y + 3)) * wall, (125, 109, 96))
    c.put(c.mask(lambda p: [p.rect(x, 32, x + 14, OFFICE_FLOOR) for x in (28, 174, 900, 1228)]) * wall, WOOD_DARK)
    c.put(c.mask(box(0, 32, 1280, 44)), WOOD_DARK)
    c.put(c.mask(box(0, OFFICE_FLOOR - 10, 1280, OFFICE_FLOOR)), WOOD_DARK)
    for left, top, right, bottom in windows:
        centre = (left + right) // 2
        c.put(c.mask(lambda p: (
            p.rect(left - 6, top - 6, right + 6, top + 5),
            p.rect(left - 6, top, left + 5, bottom),
            p.rect(right - 5, top, right + 6, bottom),
            p.rect(centre - 2, top, centre + 2, bottom),
            p.rect(left - 10, bottom - 3, right + 10, bottom + 8),
        )), WOOD_DARK)
        walk_top(c, left - 10, right + 10, bottom - 3, WOOD)


def gauges(c, k):
    """The three gauges of the dimension, on a console: GRAVITY (arrows down
    and up), WEATHER (a cloud and its rain) and LAYERS (a stack of sheets).
    Pipes run up out of them; a tube of liquid beside each."""
    g = OFFICE_FLOOR
    c.put(c.mask(box(200, OFFICE_WORKTOP, 888, g)), STEEL)
    c.put(c.mask(box(192, OFFICE_WORKTOP, 896, OFFICE_WORKTOP + 12)), STEEL_DARK)
    walk_top(c, 192, 896, OFFICE_WORKTOP, STEEL_LIGHT)
    for n, (x, colour) in enumerate(zip((300, 540, 780), LIQUIDS)):
        c.put(c.mask(box(x - 96, 450, x + 96, 503)), STEEL_LIGHT)
        c.put(c.mask(box(x - 92, 454, x + 92, 499)), STEEL)
        c.put(c.mask(box(x - 24, 461, x + 24, 466)), STEEL_DARK)
        c.put(c.mask(lambda p: (p.rect(x - 8, 32, x + 8, 177), p.rect(x - 12, 124, x + 12, 136))), STEEL_DARK)
        c.put(c.mask(lambda p: p.ellipse(x, 270, 96, 96)), STEEL_LIGHT)
        c.put(c.mask(lambda p: p.ellipse(x, 270, 84, 84)), DIAL)
        c.put(c.mask(lambda p: p.ring(x, 270, 74, 2)), mix(colour, PAPER, 0.4))
        c.put(c.mask(lambda p: [p.line([(x + 66 * math.cos(a), 270 + 66 * math.sin(a)), (x + 74 * math.cos(a), 270 + 74 * math.sin(a))], 2) for a in np.linspace(math.pi * 0.8, math.pi * 2.2, 9)]), PAPER, 0.8)
        if n == 0:
            c.put(c.mask(lambda p: (p.poly([(x - 8, 230), (x + 8, 230), (x, 246)]), p.rect(x - 2, 210, x + 2, 232), p.poly([(x - 8, 310), (x + 8, 310), (x, 294)]), p.rect(x - 2, 308, x + 2, 330))), mix(colour, PAPER, 0.5))
        elif n == 1:
            c.put(c.mask(lambda p: (p.ellipse(x - 10, 240, 16, 10), p.ellipse(x + 8, 236, 18, 12), p.rect(x - 24, 238, x + 24, 250))), PAPER, 0.9)
            c.put(c.mask(lambda p: [p.line([(x + d, 258), (x + d - 4, 272)], 2) for d in (-14, -2, 10)]), mix(colour, PAPER, 0.5))
        else:
            for j in range(3):
                y = 236 + j * 14
                c.put(c.mask(lambda p: p.poly([(x - 24, y), (x, y - 8), (x + 24, y), (x, y + 8)])), mix(colour, PAPER, 0.2 + 0.25 * j))
        a = math.radians(-60 + 50 * n)
        c.put(c.mask(lambda p: p.line([(x, 270), (x + 56 * math.cos(a), 270 + 56 * math.sin(a))], 4)), HAT)
        c.put(c.mask(lambda p: p.ellipse(x, 270, 7)), STEEL_LIGHT)
        # The tube beside it.
        tx = x + 104
        c.put(c.mask(box(tx - 9, 200, tx + 9, 380)), STEEL_DARK)
        c.put(c.mask(box(tx - 6, 260 - 20 * n, tx + 6, 376)), colour, 0.85)
        c.put(c.mask(box(tx - 6, 204, tx + 6, 376)), GLASS, 0.2)


def backlog(c, k):
    """The backlog: a board of notes (the room's signs are its words), and a
    desk under it with the spec on it in a stack, a hard hat beside it."""
    g = OFFICE_FLOOR
    c.put(c.mask(box(940, 170, 1220, 340)), WOOD_DARK)
    c.put(c.mask(box(946, 176, 1214, 334)), (119, 94, 73))
    rng = c.rand("notes")
    for col in range(6):
        x, y = 958 + col * 42 + rng.uniform(-3, 3), 292 + rng.uniform(-4, 4)
        tilt = rng.uniform(-2, 2)
        c.put(c.mask(lambda p: p.poly([(x, y), (x + 30, y + tilt), (x + 30, y + 28), (x, y + 28)])), NOTE, 0.95)
        c.put(c.mask(lambda p: p.ellipse(x + 15, y + 4, 3)), WOOD_DARK)
    c.put(c.mask(lambda p: [p.rect(x, OFFICE_WORKTOP, x + 10, g) for x in (954, 1212)]), WOOD_DARK)
    c.put(c.mask(box(944, OFFICE_WORKTOP, 1232, OFFICE_WORKTOP + 12)), WOOD)
    walk_top(c, 944, 1232, OFFICE_WORKTOP, WOOD)
    for j in range(9):
        band = OFFICE_WORKTOP - 4 * j
        offset = (j % 2) * 3
        c.put(c.mask(box(1100 + offset, band - 4, 1170 + offset, band - 1)), PAPER)
    c.put(c.mask(box(1100, OFFICE_WORKTOP - 38, 1170, OFFICE_WORKTOP - 34)), (200, 60, 60))
    c.put(c.mask(lambda p: (
        p.poly([(1186, OFFICE_WORKTOP), (1222, OFFICE_WORKTOP), (1218, OFFICE_WORKTOP - 12),
                (1206, OFFICE_WORKTOP - 18), (1192, OFFICE_WORKTOP - 12)]),
        p.rect(1182, OFFICE_WORKTOP - 2, 1226, OFFICE_WORKTOP),
    )), HAT)


#: Every piece: its frame in its room, and how it is drawn.
PIECES: Dict[str, Piece] = {
    # The Staging Area.
    "unfinished_site_cabin": Piece((580, 440, 900, 640), site_cabin),
    "unfinished_survey_post": Piece((920, 520, 1140, 640), survey_post),
    "unfinished_half_trees": Piece((1170, 330, 1700, 640), half_trees),
    "unfinished_scaffold": Piece((1632, 330, 2336, 640), scaffold),
    # The Draft.
    "unfinished_spill": Piece((540, 590, 700, 1136), spill),
    "unfinished_cranes": Piece((680, 24, 2180, 800), cranes),
    "unfinished_inspection_scaffold": Piece((588, 488, 1472, 840), inspection_scaffold),
    # The Site Office.
    "unfinished_office_wall": Piece((0, 0, 1280, 512), office_wall),
    "unfinished_gauges": Piece((180, 32, 900, 512), gauges),
    "unfinished_backlog": Piece((920, 160, 1240, 512), backlog),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PAL", "PIECES", "TARGETS"]
