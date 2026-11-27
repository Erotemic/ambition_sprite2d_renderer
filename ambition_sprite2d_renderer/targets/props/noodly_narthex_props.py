"""Draw the doors, welcome alcove, and upper landing of the Narthex."""

from ._district_props import Piece, targets
from ._town_kit import box

STONE = (109, 80, 81)
SHADOW = (60, 43, 54)
GROUT = (86, 64, 73)
BRONZE = (167, 112, 73)
GOLD = (219, 170, 101)
CREAM = (248, 220, 165)
VIOLET = (187, 163, 218)
PESTO = (157, 192, 117)
FLOOR = 480


def door_frame(c, x, color):
    """Draw a door frame with a plate above its label."""
    c.put(c.mask(lambda p: p.arch(x - 39, 347, x + 39, FLOOR)), STONE)
    c.put(c.mask(lambda p: p.arch(x - 32, 357, x + 32, FLOOR)), SHADOW)
    c.put(c.mask(box(x - 39, 476, x + 39, FLOOR)), BRONZE)
    c.put(c.mask(box(x - 20, 326, x + 20, 353)), SHADOW)
    c.put(c.mask(box(x - 21, 326, x + 21, 329)), color)


def doors(c):
    door_frame(c, 56, VIOLET)
    c.put(c.mask(lambda p: p.ring(56, 340, 7, 2)), VIOLET)
    c.put(c.mask(lambda p: (p.ellipse(46, 340, 1.4), p.ellipse(66, 340, 1.4))), VIOLET)
    door_frame(c, 224, GOLD)
    c.put(c.mask(lambda p: p.line([(213, 346), (219, 346), (219, 342), (225, 342),
                                  (225, 337), (231, 337), (231, 333), (235, 333)], 2)), GOLD)


def welcome(c):
    """Draw the welcome alcove and its lamp."""
    c.put(c.mask(lambda p: p.arch(414, 312, 592, FLOOR)), STONE)
    inside = c.mask(lambda p: p.arch(426, 325, 580, FLOOR))
    c.paint(inside, c.ramp([(325, (124, 85, 75)), (392, (91, 66, 71)), (FLOOR, SHADOW)]))
    c.put(c.mask(box(414, 473, 592, FLOOR)), GROUT)
    c.put(c.mask(box(501, 318, 505, 340)), BRONZE)
    c.put(c.mask(box(493, 338, 513, 352)), BRONZE)
    c.put(c.mask(box(497, 340, 509, 349)), CREAM)


def ledge(c, left, right, top):
    """Draw the lip at the top of a one-way ledge."""
    for x in (left + 14, right - 14):
        c.put(c.mask(lambda p: p.line([(x - 8, top + 9), (x, top + 23),
                                      (x + 8, top + 9)], 3)), GROUT)
    c.put(c.mask(box(left, top, right, top + 4)), GOLD)
    c.put(c.mask(box(left, top + 4, right, top + 12)), STONE)
    c.put(c.mask(lambda p: [p.ellipse(x, top + 8, 1.4)
                            for x in range(left + 9, right - 7, 19)]), GOLD)


def alms(c):
    """Draw a room behind the Pesto seal."""
    c.put(c.mask(box(592, 44, 944, 240)), STONE)
    c.put(c.mask(box(603, 55, 944, 240)), SHADOW)
    c.put(c.mask(box(602, 225, 944, 240)), GROUT)
    for x in (626, 914):
        c.put(c.mask(box(x - 3, 55, x + 3, 169)), GROUT)
        c.put(c.mask(box(x - 11, 151, x + 11, 173)), BRONZE)
        c.put(c.mask(box(x - 7, 154, x + 7, 169)), PESTO)
    c.put(c.mask(box(708, 104, 768, 107)), BRONZE)
    c.put(c.mask(lambda p: p.ring(738, 126, 12, 3)), PESTO)


def narthex(c, kit):
    doors(c)
    welcome(c)
    alms(c)
    ledge(c, 272, 368, 416)
    ledge(c, 320, 400, 352)
    ledge(c, 368, 528, 304)


PIECES = {"noodly_narthex_fixtures": Piece((16, 44, 944, FLOOR), narthex, px=1.5)}
TARGETS = targets(PIECES, {"accent": GOLD})
