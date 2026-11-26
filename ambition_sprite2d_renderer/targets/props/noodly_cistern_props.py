"""Draw the pipes, valves, pool walls, and key recess in the Noodly Cistern."""

from __future__ import annotations

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale

COPPER = (175, 97, 64)
VERDIGRIS = (67, 124, 117)
IRON = (104, 112, 144)
JOINT = (59, 40, 46)
CREAM = (247, 222, 170)
OPEN = (63, 118, 148)
SHUT = (153, 87, 37)
POOL_TOP, POOL_BED = 784, 864
POOLS = ((336, 448), (560, 704), (832, 992), (1216, 1424))


def pipe(c, points, metal):
    """Draw a pipe with a metal rim at each end."""
    c.put(c.mask(lambda p: p.line(points, 15)), JOINT)
    c.put(c.mask(lambda p: p.line(points, 11)), metal)
    shine = [(x - 2, y - 2) for x, y in points]
    c.put(c.mask(lambda p: p.line(shine, 2)), mix(metal, CREAM, 0.52))
    for x, y in (points[0], points[-1]):
        c.put(c.mask(lambda p: p.ellipse(x, y, 9)), JOINT)
        c.put(c.mask(lambda p: p.ellipse(x, y, 6)), metal)


def plate(c, x, y, wheel, colour, shut=False):
    """Draw a plate with the Roman numeral of the wheel."""
    c.put(c.mask(box(x - 13, y - 10, x + 13, y + 10)), JOINT)
    c.put(c.mask(box(x - 11, y - 8, x + 11, y + 8)), colour)
    bars = [x + 5 * (i - (wheel - 1) / 2) for i in range(wheel)]
    c.put(c.mask(lambda p: [p.rect(b - 1, y - 5, b + 1, y + 5) for b in bars]), CREAM)
    if shut:
        c.put(c.mask(lambda p: p.line([(x - 9, y + 7), (x + 9, y - 7)], 2)), JOINT)


def valve(c, x, y, wheel, metal):
    """Draw the valve above the lever."""
    c.put(c.mask(box(x - 5, y + 15, x + 5, y + 46)), JOINT)
    c.put(c.mask(lambda p: p.ellipse(x, y, 21)), JOINT)
    c.put(c.mask(lambda p: p.ellipse(x, y, 17)), scale(metal, 0.5))
    c.put(c.mask(lambda p: p.ring(x, y, 16, 3)), mix(metal, CREAM, 0.45))
    c.put(c.mask(lambda p: (p.line([(x - 14, y), (x + 14, y)], 2),
                            p.line([(x, y - 14), (x, y + 14)], 2))), metal)
    plate(c, x, y, wheel, scale(metal, 0.67))


def pool_walls(c):
    """Draw the tile courses below the water surface."""
    enamel = c.ramp([(POOL_TOP, (92, 129, 113)), (POOL_BED, (42, 68, 70))])
    for x0, x1 in POOLS:
        water = c.mask(box(x0, POOL_TOP, x1, POOL_BED))
        c.paint(water, enamel)
        c.put(water * c.mask(lambda p: [p.rect(x0, y, x1, y + 2)
                                       for y in range(POOL_TOP + 16, POOL_BED, 16)]), (36, 67, 67))
        c.put(water * c.mask(lambda p: [p.rect(x, y, x + 2, y + 16)
                                       for y in range(POOL_TOP, POOL_BED, 16)
                                       for x in range(x0 + (y // 16 % 2) * 12, x1, 24)]), (36, 67, 67))


def cistern(c, k):
    pool_walls(c)
    pipe(c, [(768, 714), (768, 522), (584, 522), (584, 324), (514, 324)], VERDIGRIS)
    pipe(c, [(702, 314), (733, 314), (733, 232), (888, 232), (888, 478),
             (1014, 478), (1014, 734), (1173, 734)], IRON)
    pipe(c, [(282, 714), (300, 714), (300, 559), (386, 559), (386, 132),
             (836, 132), (836, 298), (910, 298)], COPPER)
    pipe(c, [(386, 559), (425, 559), (425, 704), (479, 704)], COPPER)
    pipe(c, [(836, 298), (836, 432), (958, 432), (958, 680), (1039, 680)], COPPER)
    for x, y, n, colour in ((282, 714, 1, COPPER), (768, 714, 2, VERDIGRIS), (702, 314, 3, IRON)):
        valve(c, x, y, n, colour)
    for x, y, n, shuts in ((520, 324, 2, False), (468, 704, 1, False), (898, 298, 1, True),
                            (1027, 680, 1, True), (1176, 734, 3, False)):
        plate(c, x, y, n, SHUT if shuts else OPEN, shut=shuts)

    above_shelf = c.mask(box(1295, 165, 1457, 304))
    c.put(above_shelf * c.mask(lambda p: p.arch(1295, 165, 1457, 304)), (79, 65, 65))
    c.put(above_shelf * c.mask(lambda p: p.arch(1306, 178, 1446, 304)), (54, 75, 59))
    c.put(c.mask(lambda p: (p.ellipse(1369, 210, 7, 4), p.ellipse(1383, 204, 7, 4),
                            p.line([(1374, 218), (1378, 199)], 2))), (140, 158, 98))
    c.put(c.mask(box(1296, 304, 1456, 311)), (109, 127, 96))
    c.put(c.mask(box(1296, 304, 1456, 307)), CREAM)
    c.put(c.mask(lambda p: p.ellipse(1376, 237, 29)), (62, 93, 61))


PIECES = {"noodly_cistern_plumbing": Piece((16, 96, 1584, 864), cistern, px=1.5)}
TARGETS = targets(PIECES, {"accent": CREAM})
