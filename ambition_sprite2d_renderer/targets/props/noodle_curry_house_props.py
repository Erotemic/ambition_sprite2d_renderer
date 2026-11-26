"""Draw Marie Curry's kitchen, service steps, and bowl of udon."""

from ._district_props import Piece, targets
from ._town_kit import box

FLOOR = 448
WOOD = (145, 91, 59)
WALNUT = (75, 50, 49)
BRICK = (152, 84, 65)
GROUT = (121, 77, 63)
COPPER = (192, 120, 69)
GOLD = (233, 181, 104)
CREAM = (248, 217, 153)
TEAL = (65, 121, 102)
GLOW = (179, 217, 124)


def room(c):
    """Draw the walls and leave daylight in the front window."""
    opening = c.mask(lambda p: p.arch(145, 116, 352, 297)) * c.mask(box(145, 116, 352, 294))
    plaster = c.mask(box(16, 32, 1008, FLOOR))
    faces = plaster * (1 - opening)
    c.paint(faces, c.ramp([(32, (180, 118, 91)), (285, (160, 96, 78)), (FLOOR, (123, 75, 66))]))
    for y in (324, 348, 372, 396, 420):
        c.put(c.mask(box(16, y, 1008, y + 1)), GROUT, 0.75)
    c.put(c.mask(box(16, 34, 1008, 43)), WALNUT)
    c.put(c.mask(box(16, 436, 1008, FLOOR)), WALNUT)
    frame = c.mask(lambda p: p.arch(133, 104, 364, 301)) * c.mask(box(133, 104, 364, 299))
    c.put(frame * (1 - opening), WALNUT)
    c.put(opening * c.mask(box(245, 110, 252, 299)), WALNUT)
    c.put(opening * c.mask(box(143, 208, 354, 216)), WALNUT)
    c.put(c.mask(box(132, 292, 365, 302)), COPPER)
    c.put(c.mask(lambda p: p.arch(23, 308, 104, FLOOR)), WALNUT)
    c.put(c.mask(box(24, 438, 103, FLOOR)), WOOD)
    c.put(c.mask(box(438, 87, 842, 126)), WALNUT)
    c.put(c.mask(box(441, 87, 839, 91)), GOLD)


def stove(c):
    """Draw the hearth and the pot behind the serving counter."""
    c.put(c.mask(lambda p: p.arch(536, 149, 748, FLOOR)), WALNUT)
    c.put(c.mask(lambda p: p.arch(548, 162, 736, FLOOR)), BRICK)
    c.put(c.mask(box(558, 270, 726, 349)), WALNUT)
    c.put(c.mask(box(564, 276, 720, 342)), GROUT)
    c.put(c.mask(box(558, 248, 726, 257)), TEAL)
    c.put(c.mask(box(558, 247, 726, 251)), COPPER)
    for x in (586, 627):
        c.put(c.mask(lambda p: p.line([(x, 179), (x, 200)], 2)), COPPER)
        c.put(c.mask(lambda p: p.ellipse(x, 209, 7, 11)), COPPER)
    c.put(c.mask(lambda p: p.ellipse(689, 231, 26, 16)), GLOW, 0.25)
    c.put(c.mask(box(676, 224, 704, 246)), TEAL)
    c.put(c.mask(lambda p: p.ellipse(690, 223, 17, 5)), GLOW)
    c.put(c.mask(box(668, 229, 676, 232)), COPPER)
    c.put(c.mask(box(704, 229, 712, 232)), COPPER)
    c.put(c.mask(box(525, 393, 755, FLOOR)), WOOD)
    for x in (539, 723):
        c.put(c.mask(box(x, 397, x + 16, FLOOR)), WALNUT)
    cap(c, 520, 760, 384)


def cap(c, left, right, top):
    """Mark the top of a platform with a gold edge."""
    c.put(c.mask(box(left, top, right, top + 10)), WALNUT)
    c.put(c.mask(box(left, top, right, top + 3)), GOLD)


def shelves(c):
    """Draw the spice shelf and the steps at the east wall."""
    c.put(c.mask(box(797, 136, 998, FLOOR)), WALNUT)
    c.put(c.mask(box(805, 145, 990, FLOOR)), GROUT)
    c.put(c.mask(box(805, 182, 990, 188)), WOOD)
    for x, color in ((816, COPPER), (847, TEAL), (898, GOLD), (946, BRICK)):
        c.put(c.mask(lambda p: p.ellipse(x + 9, 168, 9, 14)), color)
        c.put(c.mask(box(x + 4, 154, x + 14, 158)), WALNUT)
    for left, right, top in ((800, 992, 288), (800, 912, 352), (912, 992, 400)):
        c.put(c.mask(box(left + 4, top + 9, right - 4, min(top + 42, FLOOR))), WOOD)
        c.put(c.mask(box(left + 9, top + 19, right - 9, top + 21)), COPPER)
        cap(c, left, right, top)


def kitchen(c, kit):
    room(c)
    stove(c)
    shelves(c)


def udon(c, kit):
    c.put(c.mask(lambda p: p.poly([(6, 21), (42, 21), (37, 34), (31, 39),
                                  (17, 39), (11, 34)])), WALNUT)
    c.put(c.mask(lambda p: p.poly([(8, 23), (40, 23), (35, 33), (30, 37),
                                  (18, 37), (13, 33)])), TEAL)
    c.put(c.mask(lambda p: p.ellipse(24, 21, 18, 7)), COPPER)
    c.put(c.mask(lambda p: p.ellipse(24, 20, 15, 4)), WOOD)
    c.put(c.mask(lambda p: (p.line([(14, 21), (19, 18), (23, 21), (28, 17), (33, 20)], 2.2),
                            p.line([(22, 13), (26, 10), (22, 6)], 1.4))), CREAM)


PIECES = {
    "noodle_curry_house_fixtures": Piece((16, 32, 1008, FLOOR), kitchen, px=1.5),
    "noodle_curry_udon_pickup": Piece((0, 0, 48, 48), udon, px=2.0),
}
TARGETS = targets(PIECES, {"accent": GOLD})
