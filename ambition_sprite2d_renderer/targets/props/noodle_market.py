"""Drying racks and the curry house entrance in Brothlehem."""

from ._district_props import Piece, targets
from ._town_kit import box

FLOOR = 576
WALNUT = (82, 54, 43)
WOOD = (135, 82, 53)
GRAIN = (193, 127, 76)
NOODLES = ((251, 215, 134), (230, 168, 89), (255, 229, 165))
CLOTH = (41, 103, 96)
CLOTH_LIGHT = (91, 159, 134)
PLASTER = (176, 99, 71)
COPPER = (227, 163, 90)


def beam(c, left, right, y, base, posts):
    """Draw a rail at the height of the walking surface."""
    c.put(c.mask(lambda p: [p.rect(x - 5, y + 4, x + 5, base) for x in posts]), WALNUT)
    c.put(c.mask(lambda p: [p.rect(x - 3, y + 10, x - 1, base - 3) for x in posts]), GRAIN, 0.65)
    c.put(c.mask(box(left, y, right, y + 11)), WOOD)
    c.put(c.mask(box(left, y, right, y + 2)), GRAIN)
    c.put(c.mask(lambda p: [p.ellipse(x, y + 6, 1.7) for x in posts]), COPPER)


def hanging_pasta(c, left, right, y, width, length):
    """Draw groups with a clear gap between them."""
    for index, color in enumerate(NOODLES):
        strands = [
            (x + shift, length + (11 * bundle + 7 * shift) % 25)
            for bundle, x in enumerate(range(left, right - 28, 55))
            for shift in range(4 + index * 2, 28, 6)
        ]
        c.put(c.mask(lambda p: [
            p.line([(x, y), (x + 2, y + drop * 0.6), (x + 1, y + drop)], width)
            for x, drop in strands
        ]), color)


def crate(c, left, right, y):
    """Draw a crate with its lid at the height of the step."""
    c.put(c.mask(box(left, y, right, FLOOR)), WOOD)
    c.put(c.mask(lambda p: [p.rect(left + 4, seam, right - 4, seam + 2) for seam in range(y + 14, FLOOR, 13)]), WALNUT)
    c.put(c.mask(lambda p: [p.rect(x, y, x + 6, FLOOR) for x in (left + 4, right - 10)]), GRAIN)
    c.put(c.mask(box(left, y, right, y + 3)), GRAIN)
    c.put(c.mask(lambda p: p.line([(left + 10, FLOOR - 8), (right - 10, y + 9)], 4)), WALNUT)


def drying_racks(c, _kit):
    """Draw the five drying racks and both approaches from the street."""
    for left, right, y, width, length in (
        (16, 400, 320, 2, 76),
        (480, 800, 384, 1.5, 97),
        (880, 1200, 320, 3, 73),
        (1280, 1600, 256, 5, 55),
        (1680, 1904, 320, 2, 76),
    ):
        hanging_pasta(c, left + 25, right - 15, y + 8, width, length)
        beam(c, left, right, y, FLOOR, (left + 12, (left + right) // 2, right - 12))
    for left, right, y in ((380, 470, 512), (1760, 1856, 512)):
        crate(c, left, right, y)
    for left, right, y in ((300, 460, 448), (1664, 1776, 432)):
        beam(c, left, right, y, FLOOR, (left + 10, right - 10))
        c.put(c.mask(box(left + 20, y + 3, right - 20, y + 8)), CLOTH_LIGHT)


def curry_entrance(c, _kit):
    """Frame the working door under a cloth awning."""
    c.put(c.mask(box(1272, 382, 1544, FLOOR)), PLASTER)
    c.put(c.mask(lambda p: [
        p.rect(1274, y, 1542, y + 2) for y in range(398, FLOOR, 24)
    ]), WALNUT, 0.3)
    c.put(c.mask(box(1272, 382, 1544, 393)), WALNUT)
    c.put(c.mask(box(1351, 475, 1417, FLOOR)), WALNUT)
    c.put(c.mask(box(1356, 479, 1412, FLOOR)), COPPER)
    c.put(c.mask(box(1360, 480, 1408, FLOOR)), WALNUT)
    c.put(c.mask(lambda p: p.poly([(1283, 411), (1533, 411), (1552, 444), (1264, 444)])), CLOTH)
    c.put(c.mask(lambda p: [
        p.poly([(x, 412), (x + 13, 412), (x + 16, 444), (x, 444)])
        for x in range(1295, 1530, 32)
    ]), CLOTH_LIGHT)
    c.put(c.mask(box(1264, 443, 1552, 450)), CLOTH)
    c.put(c.mask(lambda p: p.poly([(1372, 430), (1400, 430), (1394, 439), (1378, 439)])), COPPER)
    c.put(c.mask(lambda p: [p.line([(x, 427), (x + 2, 423), (x, 420)], 1.5) for x in (1380, 1386, 1392)]), COPPER)


TARGETS = targets({
    "noodle_market_racks": Piece((16, 256, 1904, FLOOR), drying_racks),
    "noodle_market_curry_entrance": Piece((1264, 382, 1552, FLOOR), curry_entrance),
}, {})
