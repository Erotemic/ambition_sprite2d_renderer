"""Draw the side balconies and stone backdrop of the Noodly Sanctum."""

from __future__ import annotations

from ._district_props import Piece, targets
from ._town_kit import box, mix

STONE = (103, 75, 76)
SHADOW = (51, 37, 48)
MORTAR = (82, 59, 63)
ENAMEL = (105, 54, 63)
BRONZE = (168, 112, 68)
GOLD = (228, 178, 107)
CREAM = (249, 215, 157)
FLOOR = 736


def apse(c):
    """Draw the stone at the back of the arena."""
    wall = c.mask(box(202, 78, 758, FLOOR))
    border = wall * c.mask(lambda p: p.arch(202, 78, 758, FLOOR))
    inside = wall * c.mask(lambda p: p.arch(234, 114, 726, FLOOR))
    c.put(border, STONE)
    c.paint(inside, c.ramp([(110, (78, 53, 66)), (468, (74, 53, 60)), (FLOOR, SHADOW)]))
    c.put(inside * c.mask(lambda p: [p.rect(234, y, 726, y + 1)
                                    for y in range(330, FLOOR, 34)]), MORTAR, 0.46)
    c.put(inside * c.mask(lambda p: [p.rect(x, y, x + 1, y + 34)
                                    for y in range(330, FLOOR, 34)
                                    for x in range(240 + (y // 34 % 2) * 28, 726, 56)]), MORTAR, 0.46)
    c.put(border * c.mask(lambda p: p.ring(480, 356, 264, 5)) * c.mask(box(202, 78, 758, 357)), BRONZE)
    c.put(c.mask(box(198, 700, 762, 736)), SHADOW)
    c.put(c.mask(box(198, 700, 762, 705)), MORTAR)
    c.put(c.mask(box(418, 722, 542, 726)), BRONZE, 0.78)
    c.put(c.mask(box(451, 716, 509, 720)), GOLD, 0.72)


def balcony(c, left, right):
    """Draw a balcony and its supports."""
    for x in (left + 12, right - 25):
        c.put(c.mask(box(x, 599, x + 13, FLOOR)), STONE)
        c.put(c.mask(box(x + 2, 602, x + 5, FLOOR)), MORTAR)
    for x in (left + 16, right - 17):
        c.put(c.mask(lambda p: p.line([(x - 11, 600), (x, 620), (x + 11, 600)], 4)), BRONZE)
    c.put(c.mask(box(left, 592, right, 596)), GOLD)
    c.put(c.mask(box(left, 596, right, 604)), ENAMEL)
    c.put(c.mask(box(left, 604, right, 610)), MORTAR)
    c.put(c.mask(lambda p: [p.ellipse(x, 600, 2) for x in range(left + 14, right - 8, 24)]), GOLD)


def window(c, x):
    """Draw the light behind a side balcony."""
    c.put(c.mask(box(x - 61, 307, x + 61, 592)), STONE)
    c.put(c.mask(box(x - 68, 299, x + 68, 311)), MORTAR)
    c.put(c.mask(box(x - 64, 301, x + 64, 304)), BRONZE)
    c.put(c.mask(lambda p: [p.rect(x - 60, y, x + 60, y + 1)
                            for y in range(322, 592, 24)]), MORTAR, 0.64)
    surround = c.mask(box(x - 51, 322, x + 51, 533))
    c.put(surround * c.mask(lambda p: p.arch(x - 51, 322, x + 51, 533)), MORTAR)
    glass = c.mask(box(x - 40, 337, x + 40, 522)) * c.mask(lambda p: p.arch(x - 40, 337, x + 40, 522))
    c.paint(glass, c.ramp([(337, (196, 126, 82)), (522, (112, 69, 75))]))
    c.put(glass * c.mask(lambda p: (p.rect(x - 3, 337, x + 3, 522),
                                    p.rect(x - 40, 422, x + 40, 428))), STONE)
    c.put(c.mask(box(x - 49, 524, x + 49, 530)), mix(STONE, GOLD, 0.30))


def sanctum(c, k):
    apse(c)
    window(c, 116)
    window(c, 844)
    balcony(c, 96, 288)
    balcony(c, 672, 864)
    for x in (277, 683):
        c.put(c.mask(box(x - 4, 533, x + 4, 560)), MORTAR)
        c.put(c.mask(box(x - 8, 548, x + 8, 561)), BRONZE)
        c.put(c.mask(box(x - 5, 550, x + 5, 559)), CREAM)


PIECES = {"noodly_sanctum_fixtures": Piece((16, 64, 944, FLOOR), sanctum, px=1.5)}
TARGETS = targets(PIECES, {"accent": GOLD})
