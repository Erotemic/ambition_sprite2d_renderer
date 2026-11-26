"""Scenery of the Business dimension (gate address DEALINGS): Capital, the
city where everyone is doing business
(`docs/planning/game/business-dimension.md`).

The rooms are written by
`game/ambition_map_assets/ambition_content/generators/business/make_specs.py`.
Each piece is drawn in its room's coordinates (`_district_props`): where the
room places a walk line (the café's awning, its balcony, the fountain's rim,
the Founder's pedestal, the College's tiers), the piece draws the light top
edge of the thing that is walked on at that y. The numbers here are the
generator's; change them together.

- Founders' Plaza (floor y 640): the café (awning y 520, balcony y 392),
  the Founder's fountain (rim y 592, pedestal y 528), the picket line, the
  portico of the Business College with its doorway (x 2276 to 2332).
- Records & Processing (floor y 960): the conveyor, the APPROVED press over
  it, the shredder in its pit (x 1280 to 1440), the clerk's desk on the
  high catwalk (y 448).
- The Business College's lecture hall (floor y 576): the board, the
  lectern's stage, the desks and the aisle under the tiers.

Also ``business_folder_carrier``, the look of the hanging carriage that
carries folders over the shredder: a platform look (`platform_looks.ron`),
its top bar the platform (`CARRIER_SPAN`, `CARRIER_TOP`).

Nothing here is writing: the words of the rooms are their signs.

Animations: ``idle``, 1 frame each.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

from ..characters import _art_cast_kit as K
from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .art_props import STILL, _publisher

PAL = {
    "stone": (204, 190, 182), "stone_light": (240, 230, 220), "trim": (226, 214, 200), "dark": (40, 32, 40),
    "glass_top": (176, 196, 226), "glass_low": (70, 72, 96), "lamp": (255, 214, 140), "wood": (110, 66, 44),
    "leaf": (70, 110, 84), "iron": (52, 48, 60), "brass": (214, 170, 90), "glaze": (226, 190, 110),
}

STONE = (204, 190, 182)
STONE_LIGHT = (240, 230, 220)
STONE_DARK = (132, 118, 124)
GOLD = (236, 190, 84)
GOLD_LIGHT = (255, 232, 156)
GOLD_DARK = (150, 106, 40)
WINE = (132, 36, 54)
WINE_DARK = (84, 22, 36)
CREAM = (246, 236, 220)
GLASS = (150, 176, 214)
GLASS_DARK = (60, 66, 92)
LAMP = (255, 214, 140)
LEAF = (70, 110, 84)
LEAF_DARK = (40, 70, 62)
WATER = (150, 200, 236)
STEEL = (110, 108, 124)
STEEL_DARK = (58, 56, 70)
STEEL_LIGHT = (176, 174, 190)
HAZARD = (232, 186, 52)
PAPER = (244, 240, 230)
PAPER_SHADE = (206, 200, 190)
RED = (178, 52, 62)
WOOD = (110, 66, 44)
WOOD_LIGHT = (160, 106, 70)
WOOD_DARK = (64, 38, 28)
BOARD = (232, 236, 236)

#: Founders' Plaza (`make_specs.py`).
PLAZA_FLOOR = 640
AWNING = 520
BALCONY = 392
RIM = 592
PEDESTAL = 528
DOORWAY = (2276, 2332)
#: Records & Processing.
RECORDS_FLOOR = 960
PIT = (1280, 1440)
DESK_WALK = 448
#: The lecture hall.
HALL_FLOOR = 576
STAGE = 544
TIERS = ((720, 880, 512), (880, 1040, 480), (1040, 1200, 432), (1200, 1584, 384))

CARRIER_FRAME = (320, 96)
CARRIER_SPAN = (16.0, 304.0)
CARRIER_TOP = 40.0


# ---------------------------------------------------------------------------
# Parts
# ---------------------------------------------------------------------------


def cornice(c, x0, x1, y, colour=STONE, depth=8):
    """A moulded cornice: a lit top edge, a shadowed underside, dentils."""
    c.put(c.mask(box(x0 - 6, y - depth, x1 + 6, y)), colour)
    c.put(c.mask(box(x0 - 6, y - depth, x1 + 6, y - depth + 1.5)), STONE_LIGHT)
    c.put(c.mask(box(x0 - 4, y, x1 + 4, y + 3)), scale(colour, 0.7))
    c.put(c.mask(lambda p: [p.rect(x, y + 3, x + 3, y + 7) for x in np.arange(x0, x1 - 2, 8)]), scale(colour, 0.78))


def column(c, x, top, bottom, w=14, colour=STONE):
    """A column: a shaft with flutes and its round shade, a capital, a base."""
    m = c.mask(box(x - w / 2, top + 8, x + w / 2, bottom - 6))
    c.put(m, colour)
    c.tone(m * np.clip((c.x - x) / (w / 2), -1, 1), -0.28)
    c.put(c.mask(lambda p: [p.rect(xx, top + 10, xx + 0.8, bottom - 8) for xx in np.arange(x - w / 2 + 3, x + w / 2 - 2, 3)]), scale(colour, 0.82), 0.6)
    c.put(c.mask(box(x - w / 2 - 4, top, x + w / 2 + 4, top + 8)), STONE_LIGHT)
    c.put(c.mask(box(x - w / 2 - 3, bottom - 6, x + w / 2 + 3, bottom)), scale(colour, 0.85))


def banner(c, x, top, bottom, w=22):
    """A long wine banner, swallowtailed, with a gold tie on it."""
    c.put(c.mask(box(x - w * 0.7, top - 3, x + w * 0.7, top)), GOLD_DARK)
    m = c.mask(lambda p: p.poly([(x - w / 2, top), (x + w / 2, top), (x + w / 2, bottom), (x, bottom - w * 0.6), (x - w / 2, bottom)]))
    c.put(m, WINE)
    c.tone(m * np.clip((c.x - x) / (w / 2), -1, 1), -0.18)
    mid = top + (bottom - top) * 0.42
    s = w * 0.5
    c.put(c.mask(lambda p: p.poly([(x - s * 0.28, mid - s * 1.6), (x + s * 0.28, mid - s * 1.6), (x + s * 0.18, mid - s * 1.1), (x + s * 0.4, mid + s * 1.8),
                                   (x, mid + s * 2.5), (x - s * 0.4, mid + s * 1.8), (x - s * 0.18, mid - s * 1.1)])), GOLD)


def window(c, x0, y0, x1, y1, lit=True, arch=False):
    """A tall window: its glass (lit warm or holding the sky), its bars."""
    if arch:
        glass = c.mask(lambda p: (p.rect(x0, y0 + (x1 - x0) / 2, x1, y1), p.ellipse((x0 + x1) / 2, y0 + (x1 - x0) / 2, (x1 - x0) / 2)))
    else:
        glass = c.mask(box(x0, y0, x1, y1))
    c.put(glass, mix(LAMP, (255, 236, 200), 0.3) if lit else GLASS)
    c.paint(glass, c.ramp([(y0, (255, 230, 180) if lit else (200, 214, 236)), (y1, LAMP if lit else GLASS_DARK)]), 0.6)
    c.put(c.mask(lambda p: (p.rect((x0 + x1) / 2 - 0.8, y0, (x0 + x1) / 2 + 0.8, y1), p.rect(x0, (y0 + y1) / 2, x1, (y0 + y1) / 2 + 1.4))), STEEL_DARK)
    c.put(c.mask(box(x0 - 2, y1, x1 + 2, y1 + 3)), STONE_LIGHT)


def awning(c, x0, x1, top, depth=26, stripes=(WINE, CREAM)):
    """A striped awning whose top edge is at `top` (the walk line), its
    scalloped valance under it."""
    m = c.mask(lambda p: p.poly([(x0, top), (x1, top), (x1 + 8, top + depth), (x0 - 8, top + depth)]))
    n = max(4, int((x1 - x0) / 22))
    for k in range(n):
        sx0 = x0 - 8 + (x1 - x0 + 16) * k / n
        sx1 = x0 - 8 + (x1 - x0 + 16) * (k + 1) / n
        c.put(m * c.mask(box(sx0, top, sx1, top + depth + 12)), stripes[k % 2])
    c.tone(m * np.clip((c.y - top) / depth, 0, 1), -0.18)
    c.put(c.mask(lambda p: [p.ellipse(x0 - 8 + (x1 - x0 + 16) * (k + 0.5) / n, top + depth, (x1 - x0 + 16) / n / 2, 5) for k in range(n)]),
          WINE_DARK)
    c.put(c.mask(box(x0, top, x1, top + 1.6)), mix(CREAM, (255, 255, 255), 0.4))


def railing(c, x0, x1, walk, h=22, colour=GOLD_DARK):
    """A railing on a walk: a top rail and balusters."""
    c.put(c.mask(box(x0, walk - h, x1, walk - h + 3)), colour)
    c.put(c.mask(lambda p: [p.rect(x, walk - h + 3, x + 2, walk) for x in np.arange(x0 + 2, x1, 9)]), scale(colour, 0.8))


def hazard_stripe(c, x0, x1, y0, y1):
    m = c.mask(box(x0, y0, x1, y1))
    c.put(m, (40, 36, 40))
    c.put(m * c.mask(lambda p: [p.poly([(x, y1), (x + 8, y1), (x + 8 + (y1 - y0), y0), (x + (y1 - y0), y0)]) for x in np.arange(x0 - 20, x1, 16)]), HAZARD)


def stack_of_paper(c, x, foot, n, w=26, tag="stack"):
    rng = c.rand(tag)
    for k in range(n):
        off = rng.uniform(-2, 2)
        y = foot - (k + 1) * 3.2
        c.put(c.mask(box(x - w / 2 + off, y, x + w / 2 + off, y + 3.0)), PAPER if k % 2 else PAPER_SHADE)
    c.put(c.mask(box(x - 1, foot - n * 3.2, x + 1, foot)), RED, 0.8)


# ---------------------------------------------------------------------------
# Founders' Plaza
# ---------------------------------------------------------------------------


def cafe_front(c, k):
    """The Bottom Line, the café of the plaza: a shop front of glass under a
    striped awning (its top the walk at y 520), the floor over it with a
    balcony (y 392) at its east end, tables out front."""
    g = PLAZA_FLOOR
    x0, x1 = 620, 1180
    k.wall(x0, 300, x1, g, STONE, "limestone", "cafe")
    cornice(c, x0, x1, 300)
    # The upper floor's windows, and its balcony with a door onto it.
    for x in (650, 740, 830):
        window(c, x, 330, x + 46, 420, lit=True, arch=True)
    c.put(c.mask(box(1010, 300 + 26, 1062, BALCONY)), mix(LAMP, WOOD, 0.4))
    c.put(c.mask(box(1014, 330, 1058, BALCONY)), WOOD)
    c.put(c.mask(box(960, BALCONY, 1180, BALCONY + 10)), STONE_LIGHT)
    c.put(c.mask(box(960, BALCONY + 10, 1180, BALCONY + 14)), STONE_DARK)
    railing(c, 962, 1178, BALCONY)
    # A string course over the shop.
    c.put(c.mask(box(x0, AWNING - 30, x1, AWNING - 24)), STONE_LIGHT)
    # The shop front: glass, the door, lamps.
    glass = c.mask(box(650, AWNING + 26, 990, g - 18))
    c.put(glass, mix(LAMP, (255, 236, 200), 0.2))
    c.paint(glass, c.ramp([(AWNING, (255, 232, 190)), (g, LAMP)]), 0.5)
    for x in (735, 820, 905):
        c.put(c.mask(box(x, AWNING + 26, x + 3, g - 18)), WOOD_DARK)
    c.put(c.mask(box(650, g - 18, 990, g)), WOOD)
    # Shelves of cups and a counter seen through the glass.
    c.put(c.mask(lambda p: [p.rect(670, y, 970, y + 2) for y in (AWNING + 54, AWNING + 76)]), WOOD_DARK, 0.6)
    c.put(c.mask(lambda p: [p.ellipse(x, AWNING + 50, 3, 3.5) for x in np.arange(680, 960, 14)]), CREAM, 0.7)
    awning(c, 640, 1000, AWNING)
    # The east bay: a pier of stone with a lamp.
    c.put(c.mask(box(1010, AWNING - 20, 1170, g)), scale(STONE, 0.92))
    window(c, 1040, AWNING + 10, 1140, g - 30, lit=False)
    c.light(c.mask(lambda p: p.ellipse(1000, AWNING + 50, 30, 30), blur=8), LAMP, 0.4)
    # Tables and chairs out front, a coffee on one.
    for tx in (700, 860):
        c.put(c.mask(lambda p: (p.ellipse(tx, g - 26, 18, 3), p.rect(tx - 1.5, g - 26, tx + 1.5, g - 2), p.rect(tx - 9, g - 3, tx + 9, g))), STEEL_DARK)
        for side in (-1, 1):
            cx = tx + side * 28
            c.put(c.mask(lambda p: (p.rect(cx - 8, g - 18, cx + 8, g - 15), p.rect(cx + side * 6, g - 34, cx + side * 8, g - 15),
                                    p.rect(cx - 7, g - 15, cx - 5, g), p.rect(cx + 5, g - 15, cx + 7, g))), STEEL_DARK)
        c.put(c.mask(lambda p: p.rect(tx - 4, g - 34, tx + 3, g - 27)), CREAM)
    c.put(c.mask(box(x0, g - 4, x1, g)), STONE_DARK, 0.5)


def founder_statue(c, k):
    """The Founder: a gilt statue of a man in a suit with a briefcase,
    looking up at the Tower, on a pedestal (y 528) in a round fountain (its
    rim y 592), water from four spouts."""
    g = PLAZA_FLOOR
    cx = 1440
    # The basin: its rim (the walk) and the water in it.
    basin = c.mask(box(1280, RIM, 1600, g))
    c.put(basin, STONE)
    c.tone(basin * np.clip((c.y - RIM) / 48, 0, 1), -0.15)
    c.put(c.mask(box(1280, RIM, 1600, RIM + 4)), STONE_LIGHT)
    c.put(c.mask(lambda p: [p.rect(x, RIM + 10, x + 2, g - 6) for x in np.arange(1290, 1600, 40)]), STONE_DARK, 0.5)
    c.put(c.mask(box(1288, RIM - 6, 1592, RIM)), WATER, 0.65)
    # The pedestal, in two steps, a plaque on its face.
    ped = c.mask(box(1384, PEDESTAL, 1496, RIM))
    c.put(ped, STONE)
    c.tone(ped * np.clip((c.x - cx) / 56, -1, 1), -0.22)
    c.put(c.mask(box(1378, PEDESTAL, 1502, PEDESTAL + 5)), STONE_LIGHT)
    c.put(c.mask(box(1412, PEDESTAL + 20, 1468, PEDESTAL + 46)), GOLD_DARK)
    c.put(c.mask(box(1415, PEDESTAL + 23, 1465, PEDESTAL + 43)), GOLD)
    # The jets of the spouts, arcing into the basin.
    for sx, d in ((1392, -1), (1488, 1)):
        jet = c.mask(lambda p: p.line([(sx, PEDESTAL + 18), (sx + d * 30, PEDESTAL + 6), (sx + d * 60, PEDESTAL + 20), (sx + d * 80, RIM - 4)], 3), blur=0.8)
        c.put(jet, WATER, 0.8)
        c.light(jet, (255, 255, 255), 0.3)
    # The figure: legs, coat, arm up holding his lapel, briefcase in the other.
    top = PEDESTAL
    fig = []
    fig.append(lambda p: p.poly([(cx - 16, top), (cx - 6, top), (cx - 3, top - 70), (cx - 15, top - 70)]))
    fig.append(lambda p: p.poly([(cx + 4, top), (cx + 14, top), (cx + 16, top - 70), (cx + 4, top - 70)]))
    fig.append(lambda p: p.poly([(cx - 22, top - 66), (cx + 22, top - 66), (cx + 20, top - 150), (cx + 8, top - 160), (cx - 8, top - 160), (cx - 20, top - 150)]))
    fig.append(lambda p: p.poly([(cx + 18, top - 150), (cx + 28, top - 140), (cx + 32, top - 100), (cx + 24, top - 98), (cx + 18, top - 130)]))
    fig.append(lambda p: p.poly([(cx - 18, top - 150), (cx - 30, top - 120), (cx - 18, top - 112), (cx - 6, top - 138)]))
    fig.append(lambda p: p.ellipse(cx + 2, top - 176, 13, 15))
    fig.append(lambda p: p.rect(cx - 3, top - 162, cx + 7, top - 156))
    figure = c.mask(lambda p: [f(p) for f in fig])
    c.put(figure, GOLD)
    c.tone(figure * np.clip((c.x - cx + 6) / 26, -1, 1), -0.35)
    c.light(figure * c.mask(lambda p: p.rect(cx - 30, top - 200, cx - 4, top), blur=6), GOLD_LIGHT, 0.5)
    # His briefcase, his tie, his hair; he looks up and to the east.
    case = c.mask(lambda p: (p.rect(cx + 18, top - 98, cx + 48, top - 76), p.rect(cx + 28, top - 104, cx + 38, top - 98)))
    c.put(case, GOLD_DARK)
    c.put(c.mask(lambda p: p.rect(cx + 18, top - 98, cx + 48, top - 95)), GOLD_LIGHT, 0.6)
    c.put(c.mask(lambda p: p.poly([(cx - 1, top - 156), (cx + 5, top - 156), (cx + 6, top - 118), (cx + 2, top - 112), (cx - 2, top - 118)])), GOLD_DARK)
    c.put(c.mask(lambda p: p.ellipse(cx - 1, top - 186, 13, 7)), GOLD_DARK)
    c.put(c.mask(lambda p: p.ellipse(cx + 10, top - 178, 2, 2)), GOLD_DARK)
    c.light(c.mask(lambda p: p.ellipse(cx, top - 120, 70, 110), blur=20), GOLD_LIGHT, 0.12)


def picket_line(c, k):
    """The picket line of the clerks' union: a sawhorse barricade, placards
    on sticks (blank faces: the words are the room's signs), a thermos and a
    stack of leaflets on a crate, a brazier for the cold mornings."""
    g = PLAZA_FLOOR
    # The sawhorse.
    for x in (1730, 1990):
        c.put(c.mask(lambda p: (p.line([(x - 14, g), (x, g - 40)], 4), p.line([(x + 14, g), (x, g - 40)], 4))), WOOD_DARK)
    bar = c.mask(box(1716, g - 46, 2004, g - 34))
    c.put(bar, CREAM)
    c.put(bar * c.mask(lambda p: [p.poly([(x, g - 34), (x + 14, g - 34), (x + 26, g - 46), (x + 12, g - 46)]) for x in np.arange(1700, 2010, 28)]), RED)
    # The placards on their sticks, leaned and planted.
    rng = c.rand("placards")
    for x, lean, colour in ((1760, -4, CREAM), (1830, 3, (240, 214, 120)), (1900, -2, CREAM), (1960, 5, (214, 226, 236))):
        c.put(c.mask(lambda p: p.line([(x, g), (x + lean, g - 96)], 3)), WOOD)
        face = c.mask(lambda p: p.poly([(x + lean - 26, g - 140), (x + lean + 26, g - 138), (x + lean + 24, g - 92), (x + lean - 28, g - 94)]))
        c.put(face, colour)
        c.tone(face * (c.noise(("placard", x), 3, 3, 2) - 0.5), 0.12)
        c.put(face * c.mask(lambda p: [p.rect(x + lean - 18, y, x + lean + rng.uniform(4, 18), y + 3) for y in (g - 128, g - 118, g - 108)]), RED, 0.85)
    # The crate with the leaflets and the thermos.
    c.put(c.mask(box(2010, g - 30, 2050, g)), WOOD)
    c.put(c.mask(lambda p: [p.rect(2010, y, 2050, y + 1.5) for y in (g - 20, g - 10)]), WOOD_DARK)
    stack_of_paper(c, 2024, g - 30, 4, w=16, tag="leaflets")
    c.put(c.mask(box(2040, g - 48, 2047, g - 30)), RED)


def college_front(c, k):
    """The portico of Capital Business College: a pediment with a tie in it
    over six columns, banners, tall lit windows, and the doorway of bronze
    doors (x 2276 to 2332) at the top of no steps: the plaza is level."""
    g = PLAZA_FLOOR
    x0, x1 = 2080, 2528
    k.wall(x0, 240, x1, g, STONE, "limestone", "college")
    for x in (2100, 2440):
        window(c, x, 300, x + 60, 470, lit=True, arch=True)
        window(c, x, 500, x + 60, 600, lit=True)
    # The pediment.
    ped = c.mask(lambda p: p.poly([(2150, 230), (2458, 230), (2304, 150)]))
    c.put(ped, STONE)
    c.put(c.mask(lambda p: p.poly([(2168, 224), (2440, 224), (2304, 160)])), scale(STONE, 0.86))
    c.put(c.mask(lambda p: p.poly([(2297, 178), (2311, 178), (2309, 186), (2316, 214), (2304, 222), (2292, 214), (2299, 186)])), GOLD)
    cornice(c, 2150, 2458, 240)
    # The porch: its ceiling in shade, the columns, the doorway.
    c.put(c.mask(box(2160, 250, 2448, g)), scale(STONE, 0.66))
    for x in (2172, 2228, 2380, 2436):
        column(c, x, 250, g)
    # The doorway: a frame of stone round the bronze doors that the game
    # draws in it, and a fanlight over it.
    c.put(c.mask(box(DOORWAY[0] - 12, g - 128, DOORWAY[1] + 12, g)), STONE_LIGHT)
    c.put(c.mask(box(DOORWAY[0] - 4, g - 112, DOORWAY[1] + 4, g)), (30, 24, 30))
    fan = c.mask(lambda p: p.ellipse((DOORWAY[0] + DOORWAY[1]) / 2, g - 112, 30, 14))
    c.put(fan * c.mask(box(DOORWAY[0] - 6, g - 130, DOORWAY[1] + 6, g - 112)), LAMP)
    banner(c, 2200, 270, 420)
    banner(c, 2408, 270, 420)
    c.light(c.mask(lambda p: p.ellipse(2304, g - 60, 70, 60), blur=14), LAMP, 0.2)


# ---------------------------------------------------------------------------
# Records & Processing
# ---------------------------------------------------------------------------


def records_conveyor(c, k):
    """A conveyor along the floor that carries forms east to the press:
    rollers under a dark belt, forms on it, legs and a hazard edge."""
    g = RECORDS_FLOOR
    x0, x1 = 170, 1170
    c.put(c.mask(box(x0, g - 34, x1, g - 22)), (40, 36, 46))
    c.put(c.mask(box(x0, g - 34, x1, g - 32)), STEEL_LIGHT, 0.6)
    c.put(c.mask(lambda p: [p.ellipse(x, g - 28, 6, 6) for x in np.arange(x0 + 10, x1, 30)]), STEEL)
    c.put(c.mask(lambda p: [p.ellipse(x, g - 28, 2, 2) for x in np.arange(x0 + 10, x1, 30)]), STEEL_DARK)
    for x in np.arange(x0 + 20, x1, 120):
        c.put(c.mask(box(x, g - 22, x + 5, g)), STEEL_DARK)
    hazard_stripe(c, x0, x1, g - 22, g - 18)
    rng = c.rand("forms")
    for x in np.arange(x0 + 30, x1 - 30, 70):
        stack_of_paper(c, x + rng.uniform(-10, 10), g - 34, rng.randint(2, 5), w=24, tag=("form", int(x)))


def stamp_press(c, k):
    """The APPROVED press: a cast frame over the conveyor, a red stamp head
    on its ram with the stamp's mark under it, a green lamp of ready."""
    g = RECORDS_FLOOR
    cx = 710
    # The two uprights and the crown.
    for x in (600, 800):
        m = c.mask(box(x, 660, x + 24, g - 22))
        c.put(m, (92, 84, 100))
        c.tone(m * np.clip((c.x - x - 12) / 12, -1, 1), -0.25)
    crown = c.mask(lambda p: (p.rect(590, 640, 834, 700), p.ellipse(712, 640, 122, 30)))
    c.put(crown, (102, 92, 112))
    c.put(c.mask(box(590, 696, 834, 702)), (60, 54, 70))
    c.put(c.mask(lambda p: [p.ellipse(x, 670, 4, 4) for x in (610, 650, 774, 814)]), STEEL_LIGHT)
    c.put(c.mask(lambda p: p.ellipse(cx, 652, 8, 8)), (90, 240, 140))
    c.light(c.mask(lambda p: p.ellipse(cx, 652, 20, 20), blur=6), (90, 240, 140), 0.5)
    # The ram and the stamp head, up.
    c.put(c.mask(box(cx - 10, 702, cx + 10, 800)), STEEL_LIGHT)
    head = c.mask(lambda p: (p.ellipse(cx, 812, 46, 22), p.rect(cx - 46, 812, cx + 46, 850)))
    c.put(head, RED)
    c.tone(head * np.clip((c.x - cx) / 46, -1, 1), -0.25)
    c.put(c.mask(box(cx - 50, 850, cx + 50, 866)), (60, 40, 40))
    # The mark it leaves, on the form under it: a tick in a box.
    stack_of_paper(c, cx, g - 34, 2, w=40, tag="under press")
    c.put(c.mask(lambda p: p.line([(cx - 10, g - 41), (cx - 3, g - 38), (cx + 10, g - 44)], 2)), RED)


def shredder(c, k):
    """The shredder over its pit (x 1280 to 1440): a hopper with a red lamp,
    the teeth of its cutters at the bottom of the pit, shreds everywhere,
    hazard paint on the pit's edges."""
    g = RECORDS_FLOOR
    x0, x1 = PIT
    bottom = 1072
    # The pit's walls, dark.
    c.put(c.mask(box(x0, g, x1, bottom + 16)), (24, 20, 28))
    # The cutters: rows of teeth.
    for row, y in enumerate((bottom - 26, bottom - 10)):
        c.put(c.mask(box(x0, y, x1, y + 12)), STEEL_DARK)
        c.put(c.mask(lambda p: [p.poly([(x, y), (x + 8, y), (x + 4, y - 10)]) for x in np.arange(x0 + (row * 4), x1, 8)]), STEEL_LIGHT)
    rng = c.rand("shreds")
    c.put(c.mask(lambda p: [p.rect(x, y, x + 1.6, y + rng.uniform(4, 9)) for x, y in ((rng.uniform(x0, x1), rng.uniform(g + 20, bottom - 30)) for _ in range(90))]), PAPER, 0.8)
    hazard_stripe(c, x0 - 16, x0, g - 6, g + 60)
    hazard_stripe(c, x1, x1 + 16, g - 6, g + 60)
    # The hopper over the pit, hung from the ceiling on a pipe.
    c.put(c.mask(box(1356, 820, 1364, 880)), STEEL_DARK)
    hop = c.mask(lambda p: p.poly([(1300, 880), (1420, 880), (1400, 930), (1320, 930)]))
    c.put(hop, (150, 146, 160))
    c.tone(hop * np.clip((c.x - 1360) / 60, -1, 1), -0.3)
    c.put(c.mask(box(1300, 880, 1420, 886)), STEEL_LIGHT)
    c.put(c.mask(lambda p: [p.rect(x, 930, x + 2, 944) for x in np.arange(1324, 1398, 6)]), PAPER, 0.85)
    c.put(c.mask(lambda p: p.ellipse(1410, 896, 5, 5)), (255, 60, 60))
    c.light(c.mask(lambda p: p.ellipse(1410, 896, 16, 16), blur=6), (255, 60, 60), 0.5)


def records_desk(c, k):
    """The senior clerk's desk on the high catwalk (y 448): a desk with its
    in-tray and out-tray (the in-tray taller), a green banker's lamp, a
    terminal of the pneumatic tube with a capsule in it."""
    g = DESK_WALK
    c.put(c.mask(box(560, g - 38, 760, g - 32)), WOOD_LIGHT)
    c.put(c.mask(box(566, g - 32, 754, g)), WOOD)
    c.put(c.mask(lambda p: [p.rect(x, g - 26, x + 50, g - 24) for x in (580, 690)]), WOOD_DARK)
    stack_of_paper(c, 590, g - 38, 9, w=30, tag="in tray")
    stack_of_paper(c, 734, g - 38, 2, w=30, tag="out tray")
    c.put(c.mask(lambda p: (p.rect(660, g - 54, 664, g - 38), p.ellipse(662, g - 58, 16, 7))), (40, 120, 80))
    c.light(c.mask(lambda p: p.ellipse(662, g - 44, 30, 14), blur=6), LAMP, 0.4)
    # The tube comes down from the ceiling into its terminal.
    c.put(c.mask(box(820, 330, 836, g - 60)), (214, 170, 90))
    c.put(c.mask(box(824, 330, 832, g - 60)), mix(GLASS, (255, 255, 255), 0.3), 0.6)
    term = c.mask(box(806, g - 66, 850, g - 20))
    c.put(term, (180, 140, 76))
    c.put(c.mask(box(814, g - 58, 842, g - 30)), GLASS_DARK)
    c.put(c.mask(lambda p: p.ellipse(828, g - 44, 7, 11)), (214, 170, 90))
    c.put(c.mask(box(812, g - 20, 844, g)), STEEL_DARK)


# ---------------------------------------------------------------------------
def records_catwalk(c, left, right, y):
    """Draw a steel shelf with wall brackets."""
    c.put(c.mask(lambda p: [
        p.poly([(x, y + 10), (x + 27, y + 10), (x, y + 33)])
        for x in range(left + 12, right - 32, 64)
    ]), STEEL_DARK)
    railing(c, left + 4, right - 4, y, h=19, colour=GOLD)
    c.put(c.mask(box(left, y, right, y + 12)), STEEL_DARK)
    c.put(c.mask(box(left, y, right, y + 2)), STEEL_LIGHT)
    c.put(c.mask(lambda p: [
        p.ellipse(x, y + 7, 1.5) for x in range(left + 10, right - 5, 25)
    ]), STEEL_LIGHT, 0.8)


def records_service_stairs(c, _kit):
    """Draw the east service steps and the carrier track."""
    for left, right, y in (
        (1488, 1616, 896), (1600, 1968, 832), (1936, 2160, 768),
        (2128, 2544, 704), (2112, 2256, 640),
    ):
        records_catwalk(c, left, right, y)
    c.put(c.mask(box(1520, 548, 2128, 555)), STEEL_DARK)
    c.put(c.mask(box(1520, 548, 2128, 550)), STEEL_LIGHT)
    c.put(c.mask(lambda p: [
        p.rect(x - 3, 530, x + 3, 548) for x in (1530, 1680, 1830, 1980, 2118)
    ]), STEEL)


def records_archive_stairs(c, _kit):
    """Draw the west shelves from the carrier to the archive."""
    for left, right, y in (
        (1040, 1504, 576), (880, 1056, 512), (400, 912, 448),
        (336, 464, 384), (16, 368, 320),
    ):
        records_catwalk(c, left, right, y)


# ---------------------------------------------------------------------------
# The Business College's lecture hall
# ---------------------------------------------------------------------------


def lecture_room(c, k):
    """The lecture hall: panelled walls, tall windows, a whiteboard with a
    chart that only goes up, a lectern on its stage (y 544), the front of a
    row of desks on each tier, a clock and an aisle under the seats."""
    g = HALL_FLOOR
    k.wall(16, 32, 1584, g, (186, 160, 136), "plaster", "lecture wall")
    # Panelling to the dado, in the warm wood of an old college.
    pan = c.mask(box(16, 360, 1584, g))
    c.put(pan, WOOD)
    c.put(c.mask(lambda p: [p.rect(x, 380, x + 70, g - 20) for x in np.arange(30, 1580, 90)]), WOOD_LIGHT, 0.25)
    c.put(c.mask(box(16, 356, 1584, 362)), WOOD_DARK)
    for x in (840, 1040, 1240, 1440):
        window(c, x, 90, x + 70, 300, lit=False, arch=True)
    # The whiteboard and its chart: an arrow that only goes up.
    c.put(c.mask(box(196, 110, 724, 330)), STEEL)
    c.put(c.mask(box(204, 118, 716, 322)), BOARD)
    c.put(c.mask(lambda p: [p.rect(240 + i * 60, 300 - h, 280 + i * 60, 300) for i, h in enumerate((30, 50, 74, 100, 130, 168))]), (90, 130, 200), 0.85)
    c.put(c.mask(lambda p: p.line([(240, 280), (330, 250), (420, 220), (510, 170), (600, 140), (660, 128)], 3)), RED)
    c.put(c.mask(lambda p: p.poly([(660, 120), (676, 128), (660, 138)])), RED)
    c.put(c.mask(box(196, 330, 724, 336)), STEEL_DARK)
    # The clock.
    c.put(c.mask(lambda p: p.ellipse(780, 120, 22, 22)), CREAM)
    c.put(c.mask(lambda p: p.ring(780, 120, 22, 3)), WOOD_DARK)
    c.put(c.mask(lambda p: (p.line([(780, 120), (780, 104)], 2), p.line([(780, 120), (792, 124)], 2))), (30, 30, 30))
    # The stage and the lectern.
    c.put(c.mask(box(176, STAGE, 576, STAGE + 4)), WOOD_LIGHT)
    lect = c.mask(lambda p: p.poly([(420, STAGE), (470, STAGE), (476, STAGE - 60), (414, STAGE - 60)]))
    c.put(lect, WOOD_DARK)
    c.put(c.mask(box(408, STAGE - 66, 482, STAGE - 58)), WOOD_LIGHT)
    c.put(c.mask(lambda p: p.poly([(438, STAGE - 44), (452, STAGE - 44), (450, STAGE - 30), (445, STAGE - 26), (440, STAGE - 30)])), GOLD)
    # The aisle runs between the supports. The lamps mark its floor.
    for left, right, top in TIERS:
        c.put(c.mask(box(left, top + 12, right, g)), scale(WOOD_DARK, 0.84))
        c.put(c.mask(box(left, g - 5, right, g)), WOOD_LIGHT)
        c.put(c.mask(lambda p: [p.rect(x, top + 10, x + 7, g) for x in (left + 12, right - 18)]), WOOD)
        centre = (left + right) // 2
        c.put(c.mask(box(centre - 12, g - 39, centre + 12, g - 33)), LAMP)
        c.light(c.mask(lambda p: p.ellipse(centre, g - 29, 31, 18), blur=9), LAMP, 0.27)
        c.put(c.mask(box(left, top, right, top + 12)), WOOD)
        c.put(c.mask(box(left, top, right, top + 3)), WOOD_LIGHT)
        # The back row leaves space for the ladder.
        desk_end = min(right - 12, 1500)
        c.put(c.mask(box(left + 36, top - 26, desk_end, top - 22)), WOOD_LIGHT)
        c.put(c.mask(box(left + 42, top - 22, desk_end, top - 8)), scale(WOOD, 0.9))
        c.put(c.mask(lambda p: [p.rect(x, top - 8, x + 3, top) for x in range(left + 46, desk_end, 72)]), WOOD_DARK)
    banner(c, 120, 60, 260, w=30)
    banner(c, 1540, 60, 260, w=30)


# ---------------------------------------------------------------------------
# The folder carrier (a platform look)
# ---------------------------------------------------------------------------


def _draw_carrier():
    f = K.Frame(CARRIER_FRAME)
    x0, x1 = CARRIER_SPAN
    top = CARRIER_TOP
    steel = (110, 108, 124, 255)
    # The two cables up to the track out of sight.
    for x in (x0 + 40.0, x1 - 40.0):
        f.ink([(x, 0.0), (x, top)], 2.0, (40, 38, 48, 255))
    # The bar: hazard paint on its face, arrows of the way it runs.
    f.poly([(x0, top), (x1, top), (x1, top + 14.0), (x0, top + 14.0)], (40, 36, 40, 255))
    for x in range(int(x0) - 12, int(x1), 18):
        a, b = max(x0, x), min(x1, x + 9.0)
        if b > a:
            f.poly([(a, top + 14.0), (b, top + 14.0), (min(x1, b + 6.0), top + 3.0), (min(x1, a + 6.0), top + 3.0)], (232, 186, 52, 255), body=False)
    f.ink([(x0, top + 1.0), (x1, top + 1.0)], 1.6, (200, 198, 210, 255))
    for x in ((x0 + x1) / 2.0 - 30.0, (x0 + x1) / 2.0 + 10.0):
        f.poly([(x, top + 4.0), (x + 12.0, top + 7.5), (x, top + 11.0)], (90, 230, 240, 255), body=False)
    # The hanging folders under it, their tabs up.
    colours = ((236, 196, 92, 255), (214, 176, 80, 255), (236, 196, 92, 255), (200, 160, 70, 255))
    for k, x in enumerate(range(int(x0) + 24, int(x1) - 30, 54)):
        f.poly([(x, top + 14.0), (x + 46.0, top + 14.0), (x + 44.0, top + 50.0), (x + 2.0, top + 50.0)], colours[k % 4])
        f.poly([(x + 6.0, top + 10.0), (x + 18.0, top + 10.0), (x + 18.0, top + 14.0), (x + 6.0, top + 14.0)], colours[(k + 1) % 4], body=False)
        f.ink([(x + 4.0, top + 22.0), (x + 42.0, top + 22.0)], 1.0, (246, 240, 230, 255))
    return f.finish(width=1.4)


#: Every piece: its frame in its room, and how it is drawn.
PIECES: Dict[str, Piece] = {
    # business_founders_plaza
    "business_cafe_front": Piece((600, 290, 1200, 640), cafe_front),
    "business_founder_statue": Piece((1260, 300, 1620, 640), founder_statue),
    "business_picket_line": Piece((1690, 480, 2060, 640), picket_line),
    "business_college_front": Piece((2060, 140, 2544, 640), college_front),
    # business_records_processing
    "business_records_service_stairs": Piece((1488, 530, 2544, 932), records_service_stairs),
    "business_records_archive_stairs": Piece((16, 300, 1504, 612), records_archive_stairs),
    "business_records_conveyor": Piece((160, 900, 1180, 960), records_conveyor),
    "business_stamp_press": Piece((580, 600, 850, 960), stamp_press),
    "business_shredder": Piece((1250, 800, 1470, 1088), shredder),
    "business_records_desk": Piece((540, 320, 860, 448), records_desk),
    # business_college_lecture_hall
    "business_lecture_room": Piece((16, 32, 1584, 576), lecture_room),
}

TARGETS = targets(PIECES, PAL)
TARGETS["business_folder_carrier"] = _publisher(
    "business_folder_carrier", "Folder Carrier", STILL, CARRIER_FRAME, lambda anim, i, n: _draw_carrier(),
    {"top": ((CARRIER_SPAN[0] + CARRIER_SPAN[1]) / 2.0, CARRIER_TOP)}, "Scenery", ["prop", "platform", "business"])

__all__ = ["PAL", "PIECES", "TARGETS"]
