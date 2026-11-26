"""Draw the broth paddies, upper fields, and grain lift of the Durum Terraces."""

from ._district_props import Piece, targets
from ._town_kit import box

STONE = (111, 77, 70)
SHADE = (70, 49, 56)
WOOD = (131, 81, 49)
COPPER = (174, 111, 58)
GOLD = (227, 175, 88)
CREAM = (246, 213, 135)
STEM = (128, 108, 56)


def wheat(c, left, right, floor):
    """Draw a row of durum wheat above a field."""
    for x in range(left, right, 12):
        tip = floor - 27 - (x // 12 % 3) * 5
        c.put(c.mask(lambda p: p.line([(x, floor), (x + 2, tip)], 1.6)), STEM)
        c.put(c.mask(lambda p: (p.ellipse(x, tip + 8, 2.3, 5),
                                p.ellipse(x + 4, tip + 6, 2.3, 5),
                                p.ellipse(x + 2, tip + 1, 2.3, 4))), GOLD)


def paddy_banks(c):
    """Mark the stone banks and leave the broth visible."""
    for left, right, top in ((480, 672, 1024), (1248, 1440, 1152)):
        for x in (left - 17, right):
            c.put(c.mask(box(x, top + 6, x + 17, top + 63)), STONE)
            c.put(c.mask(box(x, top + 30, x + 17, top + 33)), SHADE)
            c.put(c.mask(box(x, top + 6, x + 17, top + 10)), GOLD)
        wheat(c, left - 76, left - 26, top)
        wheat(c, right + 26, right + 76, top)
    wheat(c, 176, 318, 960)
    wheat(c, 1596, 1695, 1216)


def field_ledge(c, left, top):
    """Mark the edge of a high field."""
    right = left + 192
    c.put(c.mask(box(left, top, right, top + 4)), GOLD)
    c.put(c.mask(box(left, top + 4, right, top + 12)), STONE)
    for x in (left + 29, right - 29):
        c.put(c.mask(lambda p: p.line([(x - 12, top + 9), (x, top + 27),
                                      (x + 12, top + 9)], 3)), SHADE)


def gantry(c):
    """Draw the lift rails between the dry field and the upper landing."""
    for x in (855, 969):
        c.put(c.mask(box(x - 5, 557, x + 5, 1088)), SHADE)
        c.put(c.mask(box(x - 2, 567, x + 2, 1080)), WOOD)
        c.put(c.mask(box(x - 9, 1078, x + 9, 1088)), STONE)
        c.put(c.mask(box(x - 8, 648, x + 8, 654)), COPPER)
    c.put(c.mask(box(847, 551, 977, 564)), SHADE)
    c.put(c.mask(box(851, 551, 973, 555)), GOLD)
    c.put(c.mask(lambda p: p.ring(912, 564, 10, 3)), COPPER)
    c.put(c.mask(box(909, 576, 915, 1068)), WOOD, 0.52)
    c.put(c.mask(box(835, 1006, 874, 1042)), SHADE)
    c.put(c.mask(lambda p: p.line([(854, 1031), (854, 1015), (848, 1021)], 2.5)), CREAM)
    c.put(c.mask(lambda p: p.line([(854, 1015), (860, 1021)], 2.5)), CREAM)


def threshing_floor(c):
    """Draw the shelter at the top of the fields."""
    c.put(c.mask(box(1737, 180, 1904, 256)), SHADE)
    c.put(c.mask(lambda p: p.poly([(1718, 181), (1762, 136), (1890, 136),
                                    (1904, 166), (1904, 181)])), WOOD)
    c.put(c.mask(box(1720, 179, 1904, 182)), GOLD)
    c.put(c.mask(box(1743, 182, 1749, 256)), STONE)
    for x in (1765, 1784):
        c.put(c.mask(lambda p: p.ellipse(x, 242, 10, 14)), COPPER)
        c.put(c.mask(box(x - 5, 229, x + 5, 232)), GOLD)


def terraces(c, kit):
    paddy_banks(c)
    gantry(c)
    for n in range(11):
        field_ledge(c, 32 + 160 * n, 896 - 64 * n)
    threshing_floor(c)


def grain_car(c, kit):
    c.put(c.mask(box(8, 12, 104, 16)), GOLD)
    c.put(c.mask(box(8, 16, 104, 26)), WOOD)
    c.put(c.mask(box(14, 26, 98, 34)), SHADE)
    for x in (17, 95):
        c.put(c.mask(box(x - 3, 10, x + 3, 31)), COPPER)
        c.put(c.mask(lambda p: p.ellipse(x, 20, 1.4)), CREAM)


PIECES = {
    "noodle_terraces_fixtures": Piece((16, 132, 1904, 1220), terraces, px=1.0),
    "noodle_terraces_grain_car": Piece((0, 0, 112, 44), grain_car, px=2.0),
}
TARGETS = targets(PIECES, {"accent": GOLD})
