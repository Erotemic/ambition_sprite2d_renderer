"""Draw the bells, seal plates, and hazard rails of the Noodly Belfry."""

from __future__ import annotations

from ._district_props import Piece, targets
from ._town_kit import box, mix

TIMBER = (68, 46, 47)
BRONZE = (171, 108, 57)
GOLD = (235, 179, 96)
IRON = (68, 64, 77)
STEEL = (148, 135, 124)
CREAM = (248, 221, 177)


def plaque(c, x, y, number):
    """Draw the mark that identifies a bell and its seal."""
    c.put(c.mask(box(x - 15, y - 11, x + 15, y + 11)), TIMBER)
    c.put(c.mask(box(x - 12, y - 8, x + 12, y + 8)), BRONZE)
    marks = [x + 6 * (i - (number - 1) / 2) for i in range(number)]
    c.put(c.mask(lambda p: [p.rect(mark - 1, y - 5, mark + 1, y + 5) for mark in marks]), CREAM)


def bell(c, x, y, lever_x, floor, number):
    """Draw the bell and the rope to its lever."""
    c.put(c.mask(lambda p: p.line([(x + 21, y - 12), (lever_x, y - 12), (lever_x, floor - 24)], 3)),
          TIMBER)
    c.put(c.mask(box(x - 37, y - 22, x + 37, y - 12)), TIMBER)
    c.put(c.mask(lambda p: [p.ellipse(px, y - 17, 2) for px in (x - 31, x + 31)]), STEEL)
    c.put(c.mask(box(x - 9, y - 12, x + 9, y + 3)), IRON)
    shell = c.mask(lambda p: p.poly([(x - 11, y), (x + 11, y), (x + 17, y + 9),
                                     (x + 20, y + 28), (x + 31, y + 44),
                                     (x - 31, y + 44), (x - 20, y + 28), (x - 17, y + 9)]))
    c.put(shell, BRONZE)
    c.put(shell * c.mask(lambda p: p.ellipse(x - 12, y + 19, 14, 26)), GOLD, 0.59)
    c.put(c.mask(lambda p: p.ellipse(x, y + 45, 31, 6)), TIMBER)
    c.put(c.mask(lambda p: p.ellipse(x, y + 48, 6)), GOLD)
    c.put(c.mask(box(x - 31, y + 41, x + 31, y + 44)), GOLD)
    plaque(c, x, y + 21, number)


def hazard_rails(c):
    """Mark the full travel of each moving hazard."""
    for x in (840, 930, 1010):
        c.put(c.mask(box(x - 7, 660, x + 7, 790)), TIMBER, 0.85)
        c.put(c.mask(box(x - 3, 665, x + 3, 788)), IRON)
        for y in (660, 790):
            c.put(c.mask(box(x - 15, y - 3, x + 15, y + 3)), IRON)
            c.put(c.mask(lambda p: [p.ellipse(px, y, 2) for px in (x - 11, x + 11)]), STEEL)


def belfry(c, k):
    bell(c, 168, 1137, 102, 1216, 1)
    bell(c, 1080, 706, 1092, 800, 2)
    bell(c, 168, 401, 102, 480, 3)
    hazard_rails(c)
    for number, x in enumerate((736, 832, 928), start=1):
        plaque(c, x, 247, number)

    for x, low, high in ((640, 1376, 688), (528, 816, 224)):
        c.put(c.mask(box(x - 22, high - 8, x + 22, high + 5)), TIMBER)
        c.put(c.mask(box(x - 22, low - 7, x + 22, low)), TIMBER)
        c.put(c.mask(lambda p: [p.ellipse(px, high - 3, 2) for px in (x - 18, x + 18)]), STEEL)
    c.put(c.mask(box(432, 816, 656, 821)), mix(GOLD, TIMBER, 0.26))
    c.put(c.mask(box(432, 821, 656, 831)), TIMBER)


PIECES = {"noodly_belfry_fixtures": Piece((64, 208, 1120, 1376), belfry, px=1.5)}
TARGETS = targets(PIECES, {"accent": CREAM})
