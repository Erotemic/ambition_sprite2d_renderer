"""Draw the stone alcoves and signs of the Noodly Nave."""

from ._district_props import Piece, targets
from ._town_kit import box

STONE = (95, 67, 72)
SHADOW = (57, 41, 53)
MORTAR = (79, 56, 64)
BRONZE = (160, 108, 72)
GOLD = (221, 168, 92)
WATER = (152, 208, 220)
OFFERING = (169, 199, 126)
SILVER = (218, 214, 221)


def alcove(c, door, floor):
    """Draw stone behind a door and keep its sill at the floor."""
    c.put(c.mask(lambda p: p.arch(door - 56, floor - 158, door + 56, floor)), STONE)
    c.put(c.mask(lambda p: p.arch(door - 43, floor - 144, door + 43, floor)), SHADOW)
    c.put(c.mask(box(door - 57, floor - 5, door + 57, floor)), BRONZE)
    for x in (door - 54, door + 46):
        c.put(c.mask(box(x, floor - 82, x + 8, floor - 78)), MORTAR)
        c.put(c.mask(box(x, floor - 46, x + 8, floor - 42)), MORTAR)


def sign(c, x, y, post, floor, color, emblem):
    """Draw a sign where the route enters the main hall."""
    c.put(c.mask(lambda p: p.line([(post, floor), (post, y - 19), (x, y - 19)], 4)), STONE)
    c.put(c.mask(box(post - 8, floor - 6, post + 8, floor)), BRONZE)
    c.put(c.mask(lambda p: p.poly([(x - 35, y - 17), (x + 35, y - 17),
                                    (x + 35, y + 17), (x, y + 28), (x - 35, y + 17)])), SHADOW)
    c.put(c.mask(box(x - 35, y - 19, x + 35, y - 16)), BRONZE)
    c.put(c.mask(lambda p: [p.ellipse(px, y + 11, 2) for px in (x - 28, x + 28)]), BRONZE)
    emblem(c, x, y + 1, color)


def wheel(c, x, y, color):
    c.put(c.mask(lambda p: p.ring(x, y, 13, 3)), color)
    c.put(c.mask(lambda p: (p.line([(x - 12, y), (x + 12, y)], 2),
                            p.line([(x, y - 12), (x, y + 12)], 2), p.ellipse(x, y, 4))), color)


def bell(c, x, y, color):
    c.put(c.mask(lambda p: p.poly([(x - 6, y - 11), (x + 6, y - 11), (x + 9, y + 6),
                                    (x + 14, y + 10), (x - 14, y + 10), (x - 9, y + 6)])), color)
    c.put(c.mask(lambda p: p.ellipse(x, y + 13, 3)), color)


def vessel(c, x, y, color):
    c.put(c.mask(box(x - 14, y - 11, x + 14, y - 8)), color)
    c.put(c.mask(lambda p: p.poly([(x - 11, y - 6), (x + 11, y - 6), (x + 7, y + 4),
                                    (x + 2, y + 7), (x + 2, y + 11), (x + 7, y + 13),
                                    (x - 7, y + 13), (x - 2, y + 11), (x - 2, y + 7), (x - 7, y + 4)])), color)


def colander(c, x, y, color):
    c.put(c.mask(box(x - 22, y - 7, x + 22, y - 4)), color)
    c.put(c.mask(lambda p: p.poly([(x - 15, y - 3), (x + 15, y - 3), (x + 10, y + 9),
                                    (x + 6, y + 12), (x - 6, y + 12), (x - 10, y + 9)])), color)
    c.put(c.mask(lambda p: [p.ellipse(x + dx, y + 2, 1.4) for dx in (-7, 0, 7)]), SHADOW)
    c.put(c.mask(lambda p: [p.ellipse(x + dx, y + 7, 1.4) for dx in (-4, 4)]), SHADOW)


def nave(c, kit):
    for x, floor in ((88, 416), (88, 736), (1512, 416), (1512, 736)):
        alcove(c, x, floor)
    sign(c, 406, 154, 275, 224, GOLD, bell)
    sign(c, 406, 474, 275, 544, WATER, wheel)
    sign(c, 1192, 154, 1325, 224, SILVER, colander)
    sign(c, 1096, 474, 1229, 544, OFFERING, vessel)


PIECES = {"noodly_nave_fixtures": Piece((16, 128, 1584, 992), nave, px=1.25)}
TARGETS = targets(PIECES, {"accent": GOLD})
