"""Draw the west part of the raised walk in Eureka's Gate Court."""

from __future__ import annotations

from ._district_props import Piece, targets
from ._town_kit import box
from .eureka_props import IRON, OAK, PAL, SANDSTONE, SANDSTONE_DARK, edge_line
from .eureka_quad_props import TRIM, balustrade

FLOOR = 704
WALK = (848, 1232, 512)
STEPS = ((576, 656, 656), (752, 864, 576), (944, 1040, 608), (1056, 1168, 560))
COPPER = (150, 105, 62)
PANEL = (43, 67, 72)


def sign_board(c, left, right, top, bottom, base, posts):
    c.put(c.mask(lambda p: [p.rect(x, bottom - 5, x + 6, base) for x in posts]), IRON)
    c.put(c.mask(box(left, top, right, bottom)), TRIM)
    c.put(c.mask(box(left + 4, top + 4, right - 4, bottom - 4)), PANEL)
    c.put(c.mask(lambda p: [p.ellipse(x, top + 8, 1.6)
                            for x in (left + 9, right - 9)]), COPPER)


def step(c, left, right, top):
    c.put(c.mask(lambda p: [p.rect(x, top + 8, x + 5, FLOOR)
                            for x in (left + 10, right - 15)]), IRON)
    c.put(c.mask(lambda p: (
        p.line([(left + 12, top + 34), (left + 34, top + 10)], 3),
        p.line([(right - 13, top + 34), (right - 35, top + 10)], 3),
    )), IRON)
    c.put(c.mask(box(left, top, right, top + 13)), SANDSTONE_DARK)
    edge_line(c, left, right, top, TRIM, 5)
    c.put(c.mask(lambda p: [p.ellipse(x, top + 8, 1.3)
                            for x in range(left + 9, right - 4, 19)]), COPPER)


def court_walks(c, _):
    left, right, top = WALK
    piers = (848, 968, 1090, 1220)
    c.put(c.mask(lambda p: [p.rect(x, top + 12, x + 12, FLOOR - 7) for x in piers]), SANDSTONE)
    c.put(c.mask(lambda p: [p.rect(x + 9, top + 12, x + 12, FLOOR - 7) for x in piers]), SANDSTONE_DARK)
    c.put(c.mask(lambda p: [p.rect(x - 3, FLOOR - 7, x + 15, FLOOR) for x in piers]), SANDSTONE_DARK)
    for a, b in zip(piers, piers[1:]):
        c.put(c.mask(lambda p: p.line([
            (a + 10, top + 66), (a + 24, top + 43), (a + 42, top + 29),
            (b - 28, top + 29), (b - 12, top + 43), (b + 1, top + 66),
        ], 7)), SANDSTONE_DARK)
    c.put(c.mask(box(left, top, right, top + 19)), SANDSTONE)
    edge_line(c, left, right, top, TRIM, 8)
    edge_line(c, left, right, top + 18, SANDSTONE_DARK, 2)
    c.put(c.mask(lambda p: [p.rect(x, top + 9, x + 2, top + 17)
                            for x in range(left + 11, right, 24)]), OAK)
    balustrade(c, left, right, top)
    for span in STEPS:
        step(c, *span)
    sign_board(c, 108, 564, 379, 414, FLOOR, (104, 530))
    sign_board(c, 798, 1266, 374, 439, top - 25, (940, 1148))


TARGETS = targets({
    "eureka_court_walks": Piece((88, 365, 1272, FLOOR), court_walks),
}, PAL)
