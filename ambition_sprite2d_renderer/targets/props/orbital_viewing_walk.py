"""Draw the viewing walk along the observation deck window."""

from __future__ import annotations

from ._district_props import Piece, targets
from ._town_kit import box
from .orbital_station import AMBER, CYAN, HULL, HULL_LIGHT, INK, STEEL, STEEL_DARK, STEEL_LIGHT

FLOOR = 704
WALK = ((288, 704), (480, 624), (600, 624), (720, 584),
        (928, 584), (1056, 624), (1168, 624), (1312, 704))
PAL = {"stone": HULL, "stone_light": HULL_LIGHT, "dark": STEEL_DARK, "lamp": AMBER}


def deck(c, left, right):
    x0, y0 = left
    x1, y1 = right
    c.put(c.mask(lambda p: p.poly([(x0, y0), (x1, y1), (x1, y1 + 15), (x0, y0 + 15)])), STEEL_DARK)
    c.put(c.mask(lambda p: p.line([(x0, y0 + 2), (x1, y1 + 2)], 3)), STEEL_LIGHT)
    if y0 == y1:
        c.put(c.mask(lambda p: (
            p.line([(x0, y0 - 24), (x1, y1 - 24)], 3),
            [p.line([(x, y0 - 24), (x, y0)], 2) for x in range(x0 + 8, x1, 39)],
            [p.ellipse(x, y0 + 9, 1.4) for x in range(x0 + 10, x1, 22)],
        )), STEEL)


def scope(c):
    c.put(c.mask(box(814, 549, 826, 584)), STEEL_DARK)
    c.put(c.mask(box(803, 579, 837, 584)), STEEL_LIGHT)
    c.put(c.mask(lambda p: p.line([(802, 560), (840, 531)], 14)), STEEL)
    c.put(c.mask(lambda p: p.line([(805, 556), (839, 530)], 3)), STEEL_LIGHT)
    c.put(c.mask(lambda p: p.ellipse(802, 560, 6, 8)), INK)
    c.put(c.mask(lambda p: p.ellipse(841, 530, 7, 8)), STEEL_DARK)
    c.put(c.mask(lambda p: p.ellipse(843, 529, 4.2, 5.5)), CYAN)


def viewing_walk(c, _):
    for x, top in ((454, 638), (603, 636), (728, 598), (913, 598), (1132, 638)):
        c.put(c.mask(box(x, top, x + 7, FLOOR)), STEEL_DARK)
        c.put(c.mask(box(x, top, x + 2, FLOOR)), STEEL)
    for left, right in zip(WALK, WALK[1:]):
        deck(c, left, right)
    for x in (778, 849):
        c.put(c.mask(box(x, 665, x + 5, FLOOR)), STEEL_DARK)
    c.put(c.mask(box(768, 656, 864, 668)), STEEL_DARK)
    c.put(c.mask(box(768, 656, 864, 659)), STEEL_LIGHT)
    c.put(c.mask(lambda p: [p.ellipse(x, 664, 1.4) for x in (781, 816, 851)]), AMBER)
    c.put(c.mask(box(727, 597, 920, 637)), STEEL)
    c.put(c.mask(box(731, 601, 916, 633)), (27, 44, 54))
    c.put(c.mask(lambda p: [p.ellipse(x, 605, 1.8) for x in (736, 911)]), AMBER)
    for x, y in ((302, 692), (1298, 690)):
        c.put(c.mask(lambda p: p.poly([(x - 7, y + 3), (x, y - 5), (x + 7, y + 3)])), CYAN)
    scope(c)


TARGETS = targets({
    "orbital_viewing_walk": Piece((272, 512, 1328, FLOOR), viewing_walk),
}, PAL)
