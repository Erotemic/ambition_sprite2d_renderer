"""Draw the walks between the Gate Court and the lecture hall terrace."""

from __future__ import annotations

from ._district_props import Piece, targets
from ._town_kit import box
from .eureka_props import IRON, OAK, PAL, SANDSTONE, SANDSTONE_DARK, edge_line
from .eureka_quad_props import TRIM, balustrade

FLOOR = 768
PATENT = (576, 960, 576)
CAFE = (1008, 1200, 576)
FOUNTAIN = (1232, 1408, 592)
LECTURE_HALL = (1456, 1600, 576)
PANEL = (43, 67, 72)
BRASS = (155, 115, 67)


def notice(c, left, right, top, bottom):
    c.put(c.mask(box(left, top, right, bottom)), TRIM)
    c.put(c.mask(box(left + 4, top + 4, right - 4, bottom - 4)), PANEL)
    c.put(c.mask(lambda p: [p.ellipse(x, top + 8, 1.5)
                            for x in (left + 8, right - 8)]), BRASS)


def pier(c, x, top):
    c.put(c.mask(box(x, top + 12, x + 12, FLOOR)), SANDSTONE_DARK)
    c.put(c.mask(box(x, top + 12, x + 8, FLOOR - 5)), SANDSTONE)
    c.put(c.mask(box(x - 4, FLOOR - 7, x + 16, FLOOR)), SANDSTONE_DARK)


def deck(c, left, right, top, brackets):
    c.put(c.mask(lambda p: [p.line([(x, top + 43), (x + 17, top + 15)], 5)
                            for x in brackets]), SANDSTONE_DARK)
    c.put(c.mask(box(left, top, right, top + 18)), SANDSTONE)
    edge_line(c, left, right, top, TRIM, 7)
    edge_line(c, left, right, top + 17, SANDSTONE_DARK, 2)
    balustrade(c, left, right, top)


def walks(c, _):
    for x in (592, 652):
        pier(c, x, PATENT[2])
    for x in (1234, 1395):
        pier(c, x, FOUNTAIN[2])
    for x in (1464, 1584):
        pier(c, x, LECTURE_HALL[2])
    c.put(c.mask(lambda p: p.line([
        (1240, 680), (1267, 633), (1293, 613), (1351, 613),
        (1377, 634), (1401, 676),
    ], 7)), SANDSTONE_DARK)
    deck(c, *PATENT, (590, 652, 685, 810, 942))
    deck(c, *CAFE, (1014, 1178))
    deck(c, *FOUNTAIN, (1236, 1388))
    deck(c, *LECTURE_HALL, (1464, 1568))
    c.put(c.mask(lambda p: [p.rect(x, 730, x + 6, FLOOR) for x in (970, 1026)]), IRON)
    c.put(c.mask(box(960, 720, 1040, 733)), OAK)
    edge_line(c, 960, 1040, 720, TRIM, 4)
    notice(c, 674, 840, 594, 650)
    notice(c, 844, 996, 606, 669)
    notice(c, 1000, 1208, 593, 649)


TARGETS = targets({
    "quad_campus_walks": Piece((560, 528, 1610, FLOOR), walks),
}, PAL)
