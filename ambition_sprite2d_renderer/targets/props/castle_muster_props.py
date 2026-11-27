"""Draw the galleries of Castle Godwin's great hall."""

from ._district_props import Piece, targets


def galleries(c, _kit):
    """Match the steps and balcony to the hall's walking surfaces."""
    left = ((400, 512, 768), (448, 560, 704), (448, 768, 640), (720, 832, 576), (800, 896, 528))
    walks = (*left, *((1920 - x1, 1920 - x0, y) for x0, x1, y in left), (768, 1152, 480))
    posts = ((420, 774, 832), (470, 645, 832), (740, 650, 832),
             (796, 488, 784), (880, 538, 784))
    posts = (*posts, *((1920 - x, top, bottom) for x, top, bottom in posts))
    c.put(c.mask(lambda p: [p.rect(x - 5, top, x + 5, bottom) for x, top, bottom in posts]), (55, 47, 57))
    c.put(c.mask(lambda p: [p.rect(x - 5, top, x - 3, bottom) for x, top, bottom in posts]), (92, 84, 93))
    c.put(c.mask(lambda p: [
        p.line([(x - 17, top + 8), (x, top + 36), (x + 17, top + 8)], 3.5)
        for x, top, bottom in posts if bottom - top > 52
    ]), (61, 54, 63))
    c.put(c.mask(lambda p: [p.rect(x0, y, x1, y + 15) for x0, x1, y in walks]), (72, 64, 74))
    c.put(c.mask(lambda p: [p.rect(x0, y, x1, y + 2) for x0, x1, y in walks]), (145, 128, 125))
    c.put(c.mask(lambda p: [
        p.rect(x, y + 4, x + 2, y + 12)
        for x0, x1, y in walks for x in range(x0 + 8, x1 - 4, 15)
    ]), (111, 92, 92))
    c.put(c.mask(lambda p: (
        p.rect(788, 447, 1132, 451),
        [p.rect(x, 449, x + 3, 480) for x in range(790, 1135, 42)],
    )), (78, 64, 73))
    c.put(c.mask(lambda p: p.poly([
        (866, 481), (1054, 481), (1054, 507), (1017, 511),
        (960, 505), (904, 511), (866, 507),
    ])), (101, 29, 38))
    c.put(c.mask(lambda p: p.line([
        (868, 505), (904, 509), (960, 503), (1017, 509), (1052, 505),
    ], 1.5)), (165, 96, 78))


TARGETS = targets({
    "castle_muster_galleries": Piece((368, 432, 1552, 832), galleries, px=1.0),
}, {})
