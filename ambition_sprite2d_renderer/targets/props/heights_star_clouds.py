"""The clouds that lead to the star rack in Starlight Heights."""

import math

from ._district_props import Piece, targets

SHADE = (131, 105, 191)
LAVENDER = (186, 168, 229)
PINK = (242, 201, 238)
TOP = (255, 240, 250)
BRASS = (143, 100, 149)
GOLD = (255, 221, 134)

CLOUDS = (
    (1984, 576, 192), (2160, 512, 160), (2336, 448, 160), (2512, 384, 192),
    (2704, 336, 224),
    (2900, 384, 156), (2976, 448, 160), (3056, 512, 144), (3184, 576, 200),
)


def cloud(c, x, y, width, index):
    """Draw a flat landing face over a bank of cloud."""
    r = x + width
    rng = c.rand("star cloud", index)
    lobes = [(x + width * fraction, y + rng.uniform(13, 25), width * radius, rng.uniform(13, 25))
             for fraction, radius in ((0.19, 0.17), (0.4, 0.22), (0.66, 0.22), (0.83, 0.14))]
    silhouette = c.mask(lambda p: (
        p.rect(x + 2, y + 1, r - 2, y + 19),
        [p.ellipse(cx, cy + 3, rx, ry) for cx, cy, rx, ry in lobes],
    ))
    c.put(silhouette, SHADE)
    c.put(c.mask(lambda p: [p.ellipse(cx, cy, rx, ry - 4) for cx, cy, rx, ry in lobes]), LAVENDER)
    c.put(c.mask(lambda p: [p.ellipse(cx - 3, cy - 8, rx * 0.84, ry * 0.55) for cx, cy, rx, ry in lobes]), PINK)
    c.put(c.mask(lambda p: p.poly([
        (x, y + 4), (x + 9, y), (r - 10, y), (r, y + 4),
        (r - 10, y + 12), (x + width * 0.56, y + 10), (x + 12, y + 13),
    ])), TOP)
    c.put(c.mask(lambda p: p.line([(x + 10, y + 12), (x + width * 0.56, y + 10), (r - 10, y + 12)], 1.2)), PINK)


def star(c, x, y, radius):
    """Draw a small star with a shaded edge."""
    points = []
    for i in range(8):
        angle = i * math.tau / 8 - math.pi / 2
        span = radius if i % 2 == 0 else radius / 3
        points.append((x + span * math.cos(angle), y + span * math.sin(angle)))
    c.put(c.mask(lambda p: p.poly(points)), GOLD)
    c.put(c.mask(lambda p: p.ellipse(x - 1, y - 1, 2.4)), TOP)


def drying_rack(c):
    """Hang stars from a line above the chest."""
    for x, top in ((2732, 245), (2898, 240)):
        c.put(c.mask(lambda p: p.rect(x - 3, top, x + 3, 336)), BRASS)
        c.put(c.mask(lambda p: p.ellipse(x, top, 5.5)), GOLD)
        c.put(c.mask(lambda p: p.rect(x - 8, 331, x + 8, 336)), SHADE)
    c.put(c.mask(lambda p: p.line([(2732, 247), (2772, 256), (2815, 260), (2857, 253), (2898, 243)], 1.6)), BRASS)
    for x, top, y, radius in ((2757, 252, 275, 9), (2784, 257, 283, 12), (2840, 256, 280, 9), (2875, 249, 271, 12)):
        c.put(c.mask(lambda p: p.line([(x, top), (x, y - radius)], 1)), BRASS)
        star(c, x, y, radius)


def star_clouds(c, _kit):
    for index, (x, y, width) in enumerate(CLOUDS):
        cloud(c, x, y, width, index)
    drying_rack(c)


TARGETS = targets({"heights_star_clouds": Piece((1968, 232, 3400, 634), star_clouds)}, {})
