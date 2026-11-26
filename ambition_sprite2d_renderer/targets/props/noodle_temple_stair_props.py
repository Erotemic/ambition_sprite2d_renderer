"""Draw the overlook, stair faces, and door of the Temple Stair."""

from ._district_props import Piece, targets
from ._town_kit import box

STONE = (112, 78, 76)
SHADE = (78, 54, 62)
RECESS = (56, 40, 52)
MORTAR = (97, 68, 69)
COPPER = (166, 107, 66)
GOLD = (227, 179, 107)
CREAM = (246, 220, 167)


def stair_faces(c):
    """Draw the faces below the step edges."""
    for n in range(6):
        left = 480 + 128 * n
        top = 576 - 64 * n
        right = left + (128 if n < 5 else 784)
        c.put(c.mask(box(left + 3, top + 9, right, top + 59)), STONE)
        c.put(c.mask(box(left + 4, top + 11, right, top + 15)), COPPER)
        c.put(c.mask(box(left + 4, top + 32, right, top + 34)), MORTAR)
        c.put(c.mask(lambda p: [p.rect(x, top + 34, x + 2, top + 57)
                                for x in range(left + 43, right, 48)]), MORTAR)


def deck(c, left, right, top, supports):
    """Draw a deck over the stone that carries it."""
    for x, base in supports:
        c.put(c.mask(box(x - 5, top + 9, x + 5, base)), SHADE)
        c.put(c.mask(box(x - 9, base - 6, x + 9, base)), STONE)
        c.put(c.mask(lambda p: p.line([(x - 12, top + 12), (x, top + 30),
                                      (x + 12, top + 12)], 3)), COPPER)
    c.put(c.mask(box(left, top, right, top + 4)), GOLD)
    c.put(c.mask(box(left, top + 4, right, top + 13)), SHADE)
    c.put(c.mask(lambda p: [p.ellipse(x, top + 8, 1.6)
                            for x in range(left + 11, right - 8, 24)]), GOLD)


def overlook(c):
    """Draw the five decks and the shelter above the rest deck."""
    c.put(c.mask(box(568, 266, 775, 274)), SHADE)
    c.put(c.mask(box(568, 266, 775, 269)), COPPER)
    for x in (588, 752):
        c.put(c.mask(box(x - 4, 274, x + 4, 384)), SHADE)
    c.put(c.mask(box(665, 273, 669, 282)), COPPER)
    c.put(c.mask(box(658, 279, 676, 291)), SHADE)
    c.put(c.mask(box(661, 281, 673, 288)), CREAM)
    deck(c, 208, 352, 576, ((230, 640), (330, 640)))
    deck(c, 320, 464, 512, ((340, 576), (443, 640)))
    deck(c, 432, 576, 448, ((448, 512), (558, 576)))
    deck(c, 544, 784, 384, ((566, 576), (764, 448)))
    deck(c, 752, 960, 320, ((772, 384), (938, 384)))


def portal(c):
    """Draw the temple front around the door."""
    c.put(c.mask(box(1590, 121, 1888, 256)), STONE)
    c.put(c.mask(box(1604, 130, 1874, 256)), SHADE)
    c.put(c.mask(lambda p: p.arch(1690, 119, 1798, 256)), STONE)
    c.put(c.mask(lambda p: p.arch(1704, 134, 1784, 256)), RECESS)
    for x in (1610, 1850):
        c.put(c.mask(box(x - 9, 128, x + 9, 256)), STONE)
        c.put(c.mask(box(x - 13, 245, x + 13, 256)), COPPER)
    c.put(c.mask(lambda p: p.poly([(1578, 125), (1726, 90), (1762, 90),
                                    (1900, 125)])), SHADE)
    c.put(c.mask(box(1586, 123, 1894, 130)), GOLD)
    c.put(c.mask(lambda p: p.ring(1744, 111, 9, 2)), GOLD)
    for x in (1670, 1818):
        c.put(c.mask(box(x - 7, 167, x + 7, 185)), COPPER)
        c.put(c.mask(box(x - 4, 169, x + 4, 182)), CREAM)


def trail_marker(c):
    """Draw the marker for the way down to the terraces."""
    c.put(c.mask(box(112, 563, 119, 640)), SHADE)
    c.put(c.mask(lambda p: p.poly([(74, 577), (88, 565), (159, 565),
                                    (159, 589), (88, 589)])), STONE)
    c.put(c.mask(lambda p: p.line([(115, 577), (88, 577),
                                  (96, 571)], 2)), GOLD)
    c.put(c.mask(lambda p: p.line([(88, 577), (96, 583)], 2)), GOLD)


def stair(c, kit):
    stair_faces(c)
    overlook(c)
    portal(c)
    trail_marker(c)


PIECES = {"noodle_temple_stair_fixtures": Piece((16, 88, 1904, 640), stair, px=1.25)}
TARGETS = targets(PIECES, {"accent": GOLD})
