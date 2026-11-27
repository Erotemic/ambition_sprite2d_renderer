"""Draw the Fizzy Flats sampling walk and spring markers."""

from ._district_props import Piece, targets
from ._town_kit import box

FLOOR = 512
WOOD = (129, 81, 65)
SHADE = (72, 50, 58)
STONE = (152, 97, 101)
CRYSTAL = (209, 132, 123)
COPPER = (185, 124, 73)
GOLD = (235, 180, 107)
FOAM = (201, 233, 185)
SODA = (133, 196, 164)


def hermitage(c):
    """Frame the hermit's place at the first spring."""
    for x in (208, 444):
        c.put(c.mask(box(x, 332, x + 12, FLOOR)), SHADE)
        c.put(c.mask(box(x, 332, x + 4, FLOOR)), WOOD)
        c.put(c.mask(box(x - 3, FLOOR - 12, x + 15, FLOOR)), STONE)
    c.put(c.mask(lambda p: p.poly([(184, 336), (240, 299), (428, 299), (478, 336)])), SHADE)
    c.put(c.mask(box(184, 332, 478, 338)), COPPER)
    c.put(c.mask(box(181, 356, 479, 385)), SHADE)
    c.put(c.mask(box(185, 356, 475, 359)), GOLD)


def spring(c, left, right):
    """Mark the upper edge of the soda and show bubbles above it."""
    for x0, x1 in ((left - 15, left), (right, right + 15)):
        c.put(c.mask(box(x0, 512, x1, 550)), STONE)
        c.put(c.mask(box(x0, 512, x1, 517)), GOLD)
    c.put(c.mask(box(left, 526, right, 530)), SODA, 0.8)
    for x, y, radius in ((left + 22, 518, 3), (left + 43, 506, 4), (right - 31, 511, 5), (right - 15, 521, 2)):
        c.put(c.mask(lambda p: p.ring(x, y, radius, 1.3)), FOAM, 0.88)


def crystals(c, x):
    """Draw a small group of sugar crystals behind the trail."""
    c.put(c.mask(lambda p: p.poly([(x - 17, FLOOR), (x - 11, 483), (x, 472),
                                  (x + 11, 489), (x + 14, FLOOR)])), STONE)
    c.put(c.mask(lambda p: p.poly([(x, 472), (x + 9, 486), (x + 7, 505), (x - 3, 493)])), CRYSTAL)
    c.put(c.mask(lambda p: p.poly([(x + 14, FLOOR), (x + 18, 496), (x + 29, 490),
                                  (x + 38, 501), (x + 40, FLOOR)])), STONE)


def deck(c, left, right, top, posts):
    """Draw a deck at its walking height."""
    for x in posts:
        c.put(c.mask(box(x - 5, top + 8, x + 5, FLOOR)), SHADE)
        c.put(c.mask(box(x - 9, FLOOR - 6, x + 9, FLOOR)), STONE)
        c.put(c.mask(lambda p: p.line([(x - 12, top + 10), (x, top + 24),
                                      (x + 12, top + 10)], 3)), COPPER)
    c.put(c.mask(box(left, top, right, top + 11)), WOOD)
    c.put(c.mask(box(left, top, right, top + 3)), GOLD)
    c.put(c.mask(lambda p: [p.ellipse(x, top + 7, 1.5)
                            for x in range(left + 11, right - 6, 24)]), COPPER)


def flats(c, kit):
    hermitage(c)
    for left, right in ((560, 720), (1008, 1200), (1408, 1520)):
        spring(c, left, right)
    for x in (142, 506, 761, 1348, 1780):
        crystals(c, x)
    for x in (547, 736):
        c.put(c.mask(box(x - 3, 417, x + 3, FLOOR)), SHADE)
    c.put(c.mask(box(410, 399, 870, 428)), SHADE)
    c.put(c.mask(box(414, 399, 866, 402)), GOLD)
    c.put(c.mask(box(1072, 512, 1120, 534)), STONE)
    c.put(c.mask(box(1072, 512, 1120, 516)), GOLD)
    deck(c, 800, 928, 448, (815, 905))
    deck(c, 912, 1056, 384, (936, 997))
    deck(c, 1104, 1264, 384, (1110, 1233))
    deck(c, 1280, 1424, 416, (1297, 1390))
    deck(c, 1472, 1616, 416, (1535, 1600))


PIECES = {"noodle_fizzy_flats_fixtures": Piece((16, 288, 1904, 560), flats, px=1.25)}
TARGETS = targets(PIECES, {"accent": GOLD})
