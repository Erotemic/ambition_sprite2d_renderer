"""Ferry landings at the two banks of the Viking North fjord."""

from ._district_props import Piece, targets
from .castle_godwin import lettering

OAK = (128, 84, 52)
END_GRAIN = (167, 119, 74)
DARK = (64, 47, 41)
ROPE = (190, 151, 102)
RED = (138, 62, 49)
CREAM = (237, 218, 182)
SLATE = (63, 79, 80)
SLATE_EDGE = (105, 124, 118)
FLOOR = 576


def landing(c, shore, land):
    """Draw a dock on the bank and stone steps below the water line."""
    def x(offset):
        return shore + land * offset

    def rect(p, left, top, right, bottom):
        p.rect(min(x(left), x(right)), top, max(x(left), x(right)), bottom)

    c.put(c.mask(lambda p: p.poly([
        (x(7), FLOOR), (x(0), FLOOR), (x(0), FLOOR + 16),
        (x(-16), FLOOR + 16), (x(-16), FLOOR + 32),
        (x(-48), FLOOR + 32), (x(-45), FLOOR + 47), (x(12), FLOOR + 49),
    ])), SLATE)
    c.put(c.mask(lambda p: [
        p.line([(x(0), FLOOR + 16), (x(-16), FLOOR + 16)], 2),
        p.line([(x(-16), FLOOR + 32), (x(-48), FLOOR + 32)], 2),
    ]), SLATE_EDGE)
    c.put(c.mask(lambda p: rect(p, 0, FLOOR, 92, FLOOR + 14)), DARK)
    c.put(c.mask(lambda p: rect(p, 0, FLOOR, 92, FLOOR + 7)), OAK)
    c.put(c.mask(lambda p: [
        p.line([(x(offset), FLOOR + 1), (x(offset - 2), FLOOR + 12)], 1.4)
        for offset in range(12, 92, 12)
    ]), DARK)
    for post, height in ((14, 34), (84, 27)):
        c.put(c.mask(lambda p: rect(p, post - 4, FLOOR - height, post + 5, FLOOR + 38)), OAK)
        c.put(c.mask(lambda p: rect(p, post - 5, FLOOR - height, post + 6, FLOOR - height + 4)), END_GRAIN)
    c.put(c.mask(lambda p: p.line([
        (x(14), FLOOR - 27), (x(33), FLOOR - 19), (x(52), FLOOR - 17),
        (x(70), FLOOR - 18), (x(84), FLOOR - 21),
    ], 2.4)), ROPE)
    c.put(c.mask(lambda p: [rect(p, 9, FLOOR - y, 20, FLOOR - y + 2) for y in (25, 22, 19)]), CREAM)

    sign = x(62)
    c.put(c.mask(lambda p: rect(p, 60, FLOOR - 83, 64, FLOOR)), DARK)
    c.put(c.mask(lambda p: p.rect(sign - 32, FLOOR - 86, sign + 32, FLOOR - 62)), END_GRAIN)
    c.put(c.mask(lambda p: p.rect(sign - 30, FLOOR - 84, sign + 30, FLOOR - 64)), RED)
    lettering(c, "FERRY", sign, FLOOR - 80, 10, CREAM)


def fjord(c, _kit):
    bed = FLOOR + 48
    c.put(c.mask(lambda p: p.rect(1104, bed, 1888, 640)), SLATE)
    c.put(c.mask(lambda p: p.line([(1104, bed + 1), (1888, bed + 1)], 2)), SLATE_EDGE)
    c.put(c.mask(lambda p: [
        p.poly([(x - 9, bed + 14), (x - 5, bed + 7), (x + 6, bed + 5), (x + 10, bed + 13)])
        for x in range(1162, 1872, 22)
    ]), (86, 102, 99))
    landing(c, 1104, -1)
    landing(c, 1888, 1)


TARGETS = targets({"history_fjord_landings": Piece((976, 482, 2020, 640), fjord)}, {})
