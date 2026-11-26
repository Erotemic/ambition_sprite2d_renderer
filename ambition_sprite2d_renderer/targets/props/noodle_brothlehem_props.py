"""Draw the gate court and houses of Brothlehem."""

from ._district_props import Piece, targets
from ._town_kit import box

FLOOR = 576
WALNUT = (81, 52, 51)
WOOD = (139, 83, 54)
COPPER = (199, 132, 75)
GOLD = (234, 184, 108)
PLASTER = (179, 119, 89)
BRICK = (157, 83, 65)
CLOTH = (49, 105, 96)
TEAL = (96, 157, 133)


def gate_court(c):
    """Frame the ring and mark the street from the terminal."""
    for x in (109, 418):
        c.put(c.mask(box(x, 282, x + 13, FLOOR)), PLASTER)
        c.put(c.mask(box(x + 3, 289, x + 6, 566)), COPPER)
        c.put(c.mask(box(x - 5, 566, x + 18, FLOOR)), WALNUT)
    c.put(c.mask(box(100, 269, 440, 285)), WALNUT)
    c.put(c.mask(box(106, 269, 434, 273)), GOLD)
    for x in (116, 425):
        c.put(c.mask(box(x - 7, 341, x + 7, 354)), WOOD)
        c.put(c.mask(box(x - 4, 343, x + 4, 351)), GOLD)
    for x in (583, 659):
        c.put(c.mask(box(x - 5, 552, x + 5, FLOOR)), WALNUT)
        c.put(c.mask(box(x - 3, 554, x + 3, 560)), GOLD)
    for x in (507, 845):
        c.put(c.mask(box(x - 4, 447, x + 4, FLOOR)), WALNUT)
    c.put(c.mask(box(486, 428, 866, 477)), WALNUT)
    c.put(c.mask(box(489, 428, 863, 432)), COPPER)


def cap(c, left, right, top, color):
    """Draw a roof edge on its walking surface."""
    c.put(c.mask(box(left, top, right, top + 12)), color)
    c.put(c.mask(box(left, top, right, top + 3)), GOLD)
    c.put(c.mask(lambda p: [p.ellipse(x, top + 8, 1.5)
                            for x in range(left + 12, right - 8, 24)]), COPPER)


def bakery(c):
    """Draw the bakery and the cart below its roof."""
    c.put(c.mask(box(1004, 456, 1276, FLOOR)), PLASTER)
    c.put(c.mask(box(1040, 492, 1240, 508)), BRICK)
    for x in (1060, 1170):
        c.put(c.mask(lambda p: p.arch(x, 477, x + 56, 535)), WALNUT)
        c.put(c.mask(lambda p: p.arch(x + 6, 484, x + 50, 529)), WOOD)
        c.put(c.mask(box(x + 13, 499, x + 43, 519)), COPPER)
    c.put(c.mask(box(1004, 565, 1276, FLOOR)), WALNUT)
    cap(c, 1000, 1280, 448, BRICK)
    c.put(c.mask(box(886, 520, 994, 558)), WOOD)
    c.put(c.mask(box(890, 541, 990, 545)), WALNUT)
    c.put(c.mask(lambda p: [p.ellipse(x, 562, 13) for x in (907, 976)]), WALNUT)
    c.put(c.mask(lambda p: [p.ellipse(x, 562, 3) for x in (907, 976)]), COPPER)
    cap(c, 880, 1000, 512, WOOD)


def pilgrim_inn(c):
    """Draw the Pilgrims' Rest below its flat roof."""
    c.put(c.mask(box(1364, 391, 1636, FLOOR)), BRICK)
    c.put(c.mask(box(1372, 398, 1628, FLOOR)), PLASTER)
    for x in (1394, 1546):
        c.put(c.mask(lambda p: p.arch(x, 414, x + 56, 460)), WALNUT)
        c.put(c.mask(lambda p: p.arch(x + 6, 420, x + 50, 454)), WOOD)
        c.put(c.mask(box(x + 25, 425, x + 29, 454)), COPPER)
    c.put(c.mask(box(1370, 473, 1630, 494)), CLOTH)
    c.put(c.mask(lambda p: p.arch(1468, 499, 1532, FLOOR)), WALNUT)
    c.put(c.mask(box(1368, 566, 1633, FLOOR)), WALNUT)
    cap(c, 1360, 1640, 384, CLOTH)


def bell_house(c):
    """Draw the bell house and the three steps from the street."""
    c.put(c.mask(box(1724, 325, 1904, FLOOR)), PLASTER)
    c.put(c.mask(box(1740, 333, 1904, FLOOR)), WALNUT)
    c.put(c.mask(box(1750, 338, 1904, FLOOR)), WOOD)
    c.put(c.mask(lambda p: p.arch(1810, 329, 1862, 377)), WALNUT)
    c.put(c.mask(lambda p: p.poly([(1827, 340), (1845, 340), (1852, 361),
                                  (1820, 361)])), GOLD)
    c.put(c.mask(lambda p: p.ellipse(1836, 365, 3)), COPPER)
    cap(c, 1720, 1904, 320, BRICK)
    cap(c, 1744, 1888, 384, WOOD)
    for x in (1757, 1876):
        c.put(c.mask(lambda p: p.line([(x, 392), (x + 9, 414), (x + 18, 392)], 4)), WALNUT)
    c.put(c.mask(box(1664, 448, 1744, 458)), TEAL)
    c.put(c.mask(lambda p: p.poly([(1664, 455), (1744, 455), (1744, 475),
                                  (1673, 469)])), CLOTH)
    c.put(c.mask(box(1676, 475, 1682, FLOOR)), WALNUT)
    c.put(c.mask(box(1776, 512, 1872, FLOOR)), WOOD)
    c.put(c.mask(box(1783, 521, 1865, 524)), COPPER)
    c.put(c.mask(box(1783, 550, 1865, 553)), WALNUT)
    c.put(c.mask(lambda p: p.line([(1786, 568), (1861, 522)], 4)), COPPER)
    cap(c, 1776, 1872, 512, WOOD)


def square(c, kit):
    gate_court(c)
    bakery(c)
    pilgrim_inn(c)
    bell_house(c)


PIECES = {"noodle_brothlehem_fixtures": Piece((16, 228, 1904, FLOOR), square, px=1.25)}
TARGETS = targets(PIECES, {"accent": GOLD})
