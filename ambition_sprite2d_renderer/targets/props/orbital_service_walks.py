"""Draw the maintenance walks above the orbital service deck."""

from __future__ import annotations

from ._district_props import Piece, targets
from ._town_kit import box
from .orbital_station import (
    AMBER, CYAN, HULL, HULL_LIGHT, STEEL, STEEL_DARK, STEEL_LIGHT, lamp, plate, screen,
)

FLOOR = 832
WEST_WALK = (544, 1120, 592)
EAST_WALK = (1216, 2128, 528)
PAL = {"stone": HULL, "stone_light": HULL_LIGHT, "dark": STEEL_DARK, "lamp": AMBER}


def column(c, x, top, arm):
    c.put(c.mask(box(x, top, x + 10, FLOOR)), STEEL_DARK)
    c.put(c.mask(box(x, top, x + 3, FLOOR)), STEEL)
    c.put(c.mask(box(x - 5, FLOOR - 7, x + 15, FLOOR)), STEEL)
    c.put(c.mask(lambda p: p.line([(x + 5, top + 51), (x + arm, top)], 6)), STEEL)


def walk(c, left, right, top, rail_left, rail_right):
    c.put(c.mask(box(left, top, right, top + 17)), STEEL_DARK)
    c.put(c.mask(box(left, top, right, top + 3)), STEEL_LIGHT)
    c.put(c.mask(lambda p: [p.line([(x, top + 4), (x + 9, top + 13)], 2)
                            for x in range(left + 7, right - 12, 19)]), STEEL)
    c.put(c.mask(lambda p: (
        p.line([(rail_left, top - 27), (rail_right, top - 27)], 3),
        [p.line([(x, top - 27), (x, top)], 2) for x in range(rail_left, rail_right, 34)],
    )), STEEL_LIGHT)
    for x in (left + 8, right - 8):
        lamp(c, x, top + 8, AMBER, r=2, glow=7)


def service_walks(c, _):
    for x, arm in ((591, 42), (925, -44), (1075, 37)):
        column(c, x, WEST_WALK[2] + 16, arm)
    for x, arm in ((1240, 52), (1630, 57), (1976, 70)):
        column(c, x, EAST_WALK[2] + 16, arm)

    c.put(c.mask(lambda p: p.line([(1148, 496), (1250, 496), (1250, 478), (1564, 478)], 9)), STEEL_DARK)
    c.put(c.mask(lambda p: p.line([(1148, 493), (1247, 493), (1247, 475), (1564, 475)], 2)), STEEL)
    for x in (1344, 1402, 1460):
        plate(c, x, 458, x + 51, 527, HULL, ("filter", x), seams=0)
        c.put(c.mask(lambda p: [p.line([(x + 9, y), (x + 42, y)], 2)
                                for y in range(469, 513, 7)]), STEEL_DARK)
        lamp(c, x + 40, 518, CYAN, r=2, glow=6)
    plate(c, 1518, 476, 1568, 527, STEEL, "filter-panel", seams=0)
    screen(c, 1525, 483, 1561, 506, rows=3, tag="filter-panel")

    walk(c, *WEST_WALK, 587, 1070)
    walk(c, *EAST_WALK, 1264, 2084)
    c.put(c.mask(box(652, 610, 825, 640)), STEEL)
    c.put(c.mask(box(656, 613, 821, 637)), (24, 38, 48))
    for x, top in ((584, WEST_WALK[2]), (2088, EAST_WALK[2])):
        lamp(c, x, top - 6, CYAN, r=3, glow=10)


TARGETS = targets({
    "orbital_service_walks": Piece((528, 440, 2144, FLOOR), service_walks),
}, PAL)
