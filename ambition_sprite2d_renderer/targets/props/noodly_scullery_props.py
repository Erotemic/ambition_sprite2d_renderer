"""Draw the Scullery counters, serving shelves, and pantry."""

from ._district_props import Piece, targets
from ._town_kit import box

STONE = (106, 77, 76)
SHADOW = (58, 42, 51)
GROUT = (89, 65, 67)
IRON = (76, 68, 73)
WOOD = (111, 65, 55)
COPPER = (180, 110, 64)
GOLD = (222, 176, 111)
CREAM = (245, 216, 157)
FLOOR = 608


def wall(c):
    """Draw the wall behind the kitchen work surfaces."""
    c.put(c.mask(box(324, 176, 1100, FLOOR)), STONE)
    c.paint(c.mask(box(336, 188, 1088, FLOOR)),
            c.ramp([(188, (103, 72, 72)), (360, (88, 63, 67)), (FLOOR, SHADOW)]))
    for y in range(252, 584, 36):
        c.put(c.mask(box(336, y, 1088, y + 1)), GROUT, 0.65)
        c.put(c.mask(lambda p: [p.rect(x, y, x + 1, y + 36)
                                for x in range(352 + (y // 36 % 2) * 30, 1088, 60)]), GROUT, 0.55)
    c.put(c.mask(box(324, 176, 1100, 183)), COPPER)
    c.put(c.mask(box(324, 597, 1100, FLOOR)), GROUT)
    c.put(c.mask(box(618, 275, 818, 281)), IRON)
    for x in (650, 711, 774):
        c.put(c.mask(box(x - 2, 281, x + 2, 302)), COPPER)
    c.put(c.mask(lambda p: (p.ellipse(650, 310, 11, 14), p.ellipse(774, 309, 13, 10))), COPPER)
    c.put(c.mask(box(701, 302, 721, 320)), COPPER)
    c.put(c.mask(lambda p: [p.rect(x, 307, x + 2, 318) for x in (705, 710, 715)]), SHADOW)


def counter(c, left, right, top, *, legs=False):
    """Mark a one-way surface with a copper edge at its top."""
    for x in (left + 14, right - 14):
        if legs:
            c.put(c.mask(box(x - 4, top + 6, x + 4, FLOOR)), WOOD)
        else:
            c.put(c.mask(lambda p: p.line([(x - 10, top + 10), (x, top + 28),
                                          (x + 10, top + 10)], 4)), IRON)
    c.put(c.mask(box(left, top, right, top + 4)), GOLD)
    c.put(c.mask(box(left, top + 4, right, top + 11)), WOOD)
    c.put(c.mask(lambda p: [p.ellipse(x, top + 7, 1.5)
                            for x in range(left + 10, right - 6, 22)]), COPPER)


def stores(c):
    """Draw the larder and the lit recess of the Marinara Key."""
    for top, bottom in ((208, 352), (426, FLOOR)):
        c.put(c.mask(box(1152, top, 1392, bottom)), STONE)
        c.put(c.mask(box(1156, top + 8, 1388, bottom)), SHADOW)
    for x in (1191, 1299):
        c.put(c.mask(box(x, 237, x + 58, 241)), WOOD)
        c.put(c.mask(lambda p: (p.ellipse(x + 13, 226, 7, 11),
                                p.ellipse(x + 33, 228, 6, 9))), COPPER)
    c.put(c.mask(lambda p: p.arch(1204, 467, 1336, FLOOR)), WOOD)
    c.put(c.mask(lambda p: p.arch(1214, 477, 1326, FLOOR)), STONE)
    c.put(c.mask(box(1223, 476, 1317, 482)), COPPER)
    c.put(c.mask(box(1259, 483, 1281, 489)), CREAM)
    c.put(c.mask(box(1204, 597, 1336, FLOOR)), COPPER)


def scullery(c, kit):
    wall(c)
    counter(c, 400, 480, 544, legs=True)
    counter(c, 480, 640, 480)
    counter(c, 640, 800, 368)
    counter(c, 800, 960, 480)
    counter(c, 976, 1072, 416)
    stores(c)


PIECES = {"noodly_scullery_fixtures": Piece((320, 176, 1392, FLOOR), scullery, px=1.5)}
TARGETS = targets(PIECES, {"accent": GOLD})
