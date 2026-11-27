"""Draw the metal galleries in Wolfenstein's throne arena."""

from ._district_props import Piece, targets


def galleries(c, _kit):
    """Mark the deck edges and connect the galleries to their stands."""
    walks = (
        (6848, 6960, 768), (6912, 7040, 720), (6960, 7216, 672),
        (7056, 7184, 608), (7136, 7264, 560), (7232, 7568, 512),
        (7312, 7440, 560), (7360, 7504, 608), (7440, 7696, 672),
        (7616, 7744, 720), (7728, 7840, 768),
    )
    stands = ((6870, 768), (6930, 720), (6990, 672), (7170, 560),
              (7252, 512), (7546, 512), (7460, 608), (7664, 672),
              (7718, 720), (7818, 768))
    c.put(c.mask(lambda p: [p.rect(x - 5, y + 10, x + 5, 832) for x, y in stands]), (48, 38, 44))
    c.put(c.mask(lambda p: [p.rect(x - 5, y + 10, x - 3, 832) for x, y in stands]), (92, 67, 63))
    c.put(c.mask(lambda p: [
        p.line([(x - 18, y + 13), (x, y + 41), (x + 18, y + 13)], 4)
        for x, y in stands
    ]), (65, 48, 48))
    c.put(c.mask(lambda p: [p.rect(x0, y, x1, y + 14) for x0, x1, y in walks]), (74, 53, 49))
    c.put(c.mask(lambda p: [p.rect(x0, y, x1, y + 2.5) for x0, x1, y in walks]), (210, 165, 116))
    c.put(c.mask(lambda p: [
        p.rect(x, y + 5, x + 3, y + 10)
        for x0, x1, y in walks for x in range(x0 + 12, x1 - 4, 24)
    ]), (149, 106, 79))
    c.put(c.mask(lambda p: (
        p.rect(7244, 482, 7556, 486),
        [p.rect(x, 484, x + 3, 512) for x in range(7246, 7555, 44)],
    )), (97, 67, 63))


TARGETS = targets({
    "castle_wolfenstein_galleries": Piece((6820, 472, 7860, 832), galleries, px=1.0),
}, {})
