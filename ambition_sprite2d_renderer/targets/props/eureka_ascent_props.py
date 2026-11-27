"""Draw the roof landings and altitude signs on the tether ascent."""

from __future__ import annotations

from ._district_props import Piece, targets
from ._town_kit import box
from .orbital_climb_props import PAL
from .orbital_station import AMBER, INK, STEEL, STEEL_DARK, STEEL_LIGHT, lamp

ROOF = 3184
FLOOR = 3200
SHAFT = (576, 704)
SCREEN = (29, 46, 57)


def notice(c, left, right, top, bottom):
    c.put(c.mask(box(left, top, right, bottom)), STEEL)
    c.put(c.mask(box(left + 4, top + 4, right - 4, bottom - 4)), SCREEN)
    c.put(c.mask(lambda p: [p.ellipse(x, top + 8, 1.7)
                            for x in (left + 8, right - 8)]), AMBER)


def shelf(c, left, right, lip):
    c.put(c.mask(box(left, ROOF, right, FLOOR)), STEEL_DARK)
    c.put(c.mask(box(left, ROOF, right, ROOF + 4)), STEEL_LIGHT)
    c.put(c.mask(lambda p: [p.rect(x, ROOF + 9, x + 3, FLOOR - 2)
                            for x in range(left + 36, right - 10, 40)]), STEEL)
    c.put(c.mask(box(lip - 24, ROOF, lip, ROOF + 7)), AMBER)
    c.put(c.mask(lambda p: [p.line([(x, ROOF + 7), (x + 5, ROOF)], 2)
                            for x in range(lip - 22, lip - 3, 7)]), INK)


def low_route(c, _):
    left_edge, right_edge = SHAFT
    shelf(c, 16, left_edge, left_edge)
    shelf(c, right_edge, 1264, right_edge + 24)
    for x in (348, 499, 775, 925):
        c.put(c.mask(box(x, 3128, x + 7, ROOF)), STEEL)
    notice(c, 300, 546, 3092, 3133)
    notice(c, 734, 980, 3092, 3133)
    for x in (left_edge - 13, right_edge + 13):
        c.put(c.mask(box(x - 3, ROOF - 17, x + 4, ROOF)), STEEL)
        lamp(c, x, ROOF - 17, AMBER, r=3, glow=10)
    notice(c, 711, 981, 2926, 2967)
    notice(c, 711, 981, 2219, 2262)


def high_route(c, _):
    notice(c, 711, 981, 1419, 1461)
    notice(c, 299, 573, 612, 655)


TARGETS = targets({
    "climb_route_lower": Piece((16, 2200, 1264, FLOOR), low_route),
    "climb_route_upper": Piece((288, 600, 992, 1476), high_route),
}, PAL)
