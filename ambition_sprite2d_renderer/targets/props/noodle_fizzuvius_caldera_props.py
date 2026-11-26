"""Draw the Caldera rock, corks, and bubble lift."""

from ._district_props import Piece, targets
from ._town_kit import box

SHADE = (62, 43, 55)
ROCK = (119, 70, 81)
FACET = (158, 87, 97)
CREST = (224, 159, 120)
BRASS = (239, 177, 107)
SODA = (109, 187, 177)
FOAM = (205, 234, 198)
CORK = (176, 105, 65)


def crust(c, left, right, top, depth):
    """Draw a rock face below a walk line."""
    width = right - left
    c.put(c.mask(lambda p: p.poly([
        (left, top), (right, top), (right - 8, top + 14), (left + width * 0.74, top + depth * 0.68),
        (left + width * 0.42, top + depth), (left + 13, top + 20),
    ])), SHADE)
    c.put(c.mask(lambda p: p.poly([
        (left, top), (right, top), (right - 10, top + 13), (left + width * 0.49, top + 23),
        (left + 12, top + 15),
    ])), ROCK)
    c.put(c.mask(lambda p: p.poly([
        (left + 18, top + 13), (left + width * 0.53, top + 10), (left + width * 0.42, top + depth - 5),
    ])), FACET)
    c.put(c.mask(box(left, top, right, top + 3)), CREST)


def mark_exit(c, floor, color):
    """Show the opening in the west wall."""
    c.put(c.mask(lambda p: p.poly([
        (16, floor - 96), (47, floor - 88), (79, floor - 50), (88, floor),
        (72, floor), (65, floor - 44), (37, floor - 76), (16, floor - 81),
    ])), SHADE)
    c.put(c.mask(lambda p: p.line([
        (18, floor - 83), (42, floor - 77), (67, floor - 46), (75, floor - 3),
    ], 3)), color)


def marker(c, left, right, top, bottom, post_floor, color):
    """Draw the sign and its posts."""
    for x in (right - 82, right - 20):
        c.put(c.mask(box(x, bottom, x + 4, post_floor)), SHADE)
    c.put(c.mask(box(left, top, right, bottom)), SHADE)
    c.put(c.mask(box(left + 4, top, right - 4, top + 3)), color)


def bubble_shaft(c):
    """Mark the lift path between the shore and the rim."""
    c.put(c.mask(box(1568, 480, 1664, 816)), SODA, 0.11)
    for x in (1573, 1659):
        c.put(c.mask(box(x - 2, 256, x + 2, 832)), SODA, 0.65)
        for y in (256, 333, 490, 650, 807):
            c.put(c.mask(box(x - 4, y, x + 4, y + 7)), BRASS)
    for n, y in enumerate(range(275, 815, 23)):
        x = 1588 + (n * 29) % 56
        c.put(c.mask(lambda p: p.ring(x, y, 2 + n % 4, 1.15)), FOAM, 0.68)
    c.put(c.mask(box(1554, 832, 1678, 840)), SHADE)
    c.put(c.mask(box(1568, 832, 1664, 835)), SODA)


def caldera(c, kit):
    for left, right, top, depth in (
        (408, 568, 320, 52), (656, 816, 352, 44), (904, 1064, 320, 60),
        (1152, 1312, 352, 47), (1400, 1560, 320, 59),
        (688, 752, 800, 66), (1040, 1104, 784, 81),
        (1680, 1904, 320, 75),
    ):
        crust(c, left, right, top, depth)
    for n, x in enumerate(range(414, 1520, 37)):
        y = 840 - (n * 7) % 26
        c.put(c.mask(lambda p: p.ring(x, y, 2 + n % 4, 1.2)), FOAM, 0.72)
    for x in (384, 1520):
        c.put(c.mask(box(x, 832, x + 16, 856)), ROCK)
        c.put(c.mask(box(x, 832, x + 16, 836)), CREST)
    bubble_shaft(c)
    marker(c, 104, 376, 726, 756, 832, BRASS)
    marker(c, 1514, 1886, 708, 738, 832, SODA)
    marker(c, 1628, 1892, 183, 235, 320, BRASS)
    c.put(c.mask(lambda p: p.poly([
        (1726, 320), (1736, 266), (1761, 244), (1808, 236),
        (1854, 244), (1880, 266), (1890, 320),
    ])), ROCK)
    c.put(c.mask(lambda p: p.poly([
        (1744, 320), (1751, 275), (1772, 256), (1808, 248),
        (1843, 256), (1865, 275), (1872, 320),
    ])), SHADE)
    c.put(c.mask(lambda p: p.ring(1808, 263, 10, 2)), SODA)
    mark_exit(c, 320, BRASS)
    mark_exit(c, 832, SODA)


def cork(c, kit):
    c.put(c.mask(lambda p: p.poly([
        (8, 12), (104, 12), (102, 25), (92, 34), (19, 34), (10, 25),
    ])), SHADE)
    c.put(c.mask(lambda p: p.poly([
        (8, 12), (104, 12), (100, 24), (92, 30), (19, 30), (12, 23),
    ])), CORK)
    c.put(c.mask(box(8, 12, 104, 15)), CREST)
    for n, x in enumerate(range(16, 98, 7)):
        c.put(c.mask(lambda p: p.ellipse(x, 19 + n % 8, 1 + n % 2 * 0.5)), SHADE, 0.7)
    for x in (22, 88):
        c.put(c.mask(box(x, 12, x + 3, 30)), BRASS)


def bubble_car(c, kit):
    c.put(c.mask(box(8, 12, 104, 22)), SHADE)
    c.put(c.mask(box(8, 12, 104, 15)), BRASS)
    c.put(c.mask(box(15, 15, 97, 18)), SODA)
    c.put(c.mask(lambda p: p.poly([
        (12, 21), (100, 21), (87, 31), (68, 38), (44, 38), (25, 31),
    ])), ROCK)
    for x in (28, 56, 84):
        c.put(c.mask(lambda p: p.ring(x, 25, 4, 1.6)), FOAM)


PIECES = {
    "noodle_fizzuvius_caldera_fixtures": Piece((16, 160, 1904, 896), caldera, px=1.25),
    "noodle_caldera_cork": Piece((0, 0, 112, 44), cork, px=2.0),
    "noodle_caldera_bubble_car": Piece((0, 0, 112, 44), bubble_car, px=2.0),
}
TARGETS = targets(PIECES, {"accent": BRASS})
