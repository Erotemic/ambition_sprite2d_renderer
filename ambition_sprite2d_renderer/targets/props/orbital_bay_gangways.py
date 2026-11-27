"""Draw the gantry, hauler walk, and shuttle service deck."""

from __future__ import annotations

from ._district_props import Piece, targets
from ._town_kit import box
from .orbital_station import AMBER, CYAN, HULL, HULL_LIGHT, INK, STEEL, STEEL_DARK, STEEL_LIGHT, lamp

FLOOR = 960
SPINE = 576
WEST_STEPS = ((560, 688, 896), (640, 768, 832), (560, 688, 768),
              (640, 768, 704), (560, 688, 640))
EAST_STEPS = ((2352, 2464, 896), (2288, 2400, 832), (2112, 2368, 768))
PAL = {"stone": HULL, "stone_light": HULL_LIGHT, "dark": STEEL_DARK, "lamp": AMBER}


def deck(c, left, right, top, depth):
    c.put(c.mask(box(left, top, right, top + depth)), STEEL_DARK)
    c.put(c.mask(box(left, top, right, top + 3)), STEEL_LIGHT)
    c.put(c.mask(lambda p: [p.line([(x, top + 4), (x + 12, top + depth - 3)], 1.8)
                            for x in range(left + 5, right - 13, 19)]), STEEL)
    c.put(c.mask(lambda p: [p.ellipse(x, top + depth - 4, 1.3)
                            for x in range(left + 10, right - 5, 28)]), INK)


def post(c, x, top, width=8):
    c.put(c.mask(box(x, top, x + width, FLOOR)), STEEL_DARK)
    c.put(c.mask(box(x, top, x + 2, FLOOR)), STEEL)
    c.put(c.mask(box(x - 4, FLOOR - 7, x + width + 4, FLOOR)), STEEL)


def rail(c, left, right, top):
    c.put(c.mask(lambda p: (
        p.rect(left, top - 31, right, top - 27),
        [p.rect(x, top - 27, x + 2, top) for x in range(left + 3, right - 3, 36)],
    )), STEEL_LIGHT)


def notice(c, left, right, top, bottom, deck_top):
    c.put(c.mask(lambda p: [p.rect(x, bottom - 5, x + 5, deck_top)
                            for x in (left + 12, right - 17)]), STEEL)
    c.put(c.mask(box(left, top, right, bottom)), STEEL)
    c.put(c.mask(box(left + 4, top + 4, right - 4, bottom - 4)), (26, 44, 55))
    c.put(c.mask(lambda p: [p.ellipse(x, top + 8, 1.5)
                            for x in (left + 8, right - 8)]), AMBER)


def gangways(c, _):
    for x in (574, 747, 1152, 1680, 2166, 2210, 2354):
        post(c, x, SPINE + 14)
    for top in (654, 782, 910):
        c.put(c.mask(lambda p: p.line([(584, top + 40), (749, top)], 4)), STEEL_DARK)
    for x, y in ((2372, 902), (2304, 838), (2128, 780)):
        post(c, x, y)
    for left, right, top in (*WEST_STEPS, *EAST_STEPS):
        deck(c, left, right, top, 16)
    deck(c, 640, 2400, SPINE, 22)
    for left, right in ((650, 1488), (1600, 2168), (2216, 2400)):
        rail(c, left, right, SPINE)
    rail(c, 2120, 2168, 768)
    rail(c, 2216, 2360, 768)
    notice(c, 2182, 2400, 475, 518, 548)
    notice(c, 2332, 2552, 777, 819, 832)
    for x, y in ((2170, 564), (2214, 756), (2400, 570)):
        lamp(c, x, y, CYAN, r=3, glow=10)


TARGETS = targets({
    "orbital_bay_gangways": Piece((536, 462, 2560, FLOOR), gangways),
}, PAL)
