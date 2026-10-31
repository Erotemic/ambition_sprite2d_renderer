"""The Void Castle (the Magical dimension, Mary-O's): the keep the void took,
and the Void Lizard's bridge under it.

Drawn in room coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/magical/make_specs.py`:

- `magical_void_keep` (ground y 640; its stairs down, holes x 480..544 and
  2000..2064): `keep_gate`, the arch the dune road comes in by, its
  portcullis up; `keep_banner`, a banner of void with the lizard on it (the
  room hangs it three times); `keep_star_statue`, the town's star on its
  plinth, the void's ink poured over its face; `keep_stair`, a kerb and a
  rail round a stair's hole (once at each).
- `magical_void_bridge` (floor y 576 at each end, the bridge x 760..1800 at y
  576 over the pit, its bottom y 632): `bridge_span`, the bridge's chains and
  posts and the lava in the pit under it; `bridge_switch`, the switch at its
  east end that drops it (the Void Lizard would rather you did not);
  `bridge_tea_table`, the lizard's table on its bridge: a cup, a pot, a book.

The void is a body with no light in it and a white edge, as the lizard is.
Animations: ``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

import math
from typing import Dict

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .magical_square_props import CREAM, GOLD, GOLD_DARK, PINK, PINK_DARK, PINK_LIGHT, star

KEEP_FLOOR = 640
STAIR_W = (480, 544)
BANNER_X = 760
BANNER_TOP = 96
STATUE_X = 1310
BRIDGE_FLOOR = 576
SPAN = (760, 1800)
PIT_FLOOR = 632
SWITCH_X = 1900
TABLE_X = 1060

STONE = (78, 62, 104)
STONE_DARK = (54, 42, 76)
STONE_LIGHT = (120, 100, 150)
VOID = (16, 8, 26)
EDGE = (240, 236, 255)
IRON = (64, 58, 78)
IRON_LIGHT = (130, 122, 150)
LAVA = (255, 112, 70)
LAVA_HOT = (255, 206, 110)
LAVA_DEEP = (190, 50, 70)
WOOD = (150, 100, 80)
WOOD_DARK = scale(WOOD, 0.72)
PAL = {"stone": STONE, "stone_light": STONE_LIGHT, "dark": VOID, "lamp": LAVA_HOT}


def void(c, shape, edge=1.6):
    """A shape of void: no light in it, a white edge round it."""
    c.put(c.mask(shape), EDGE)
    c.put(c.mask(lambda p: shape(p, inset=edge)), VOID)


LIZARD = [(-0.52, 0.40), (-0.28, 0.18), (-0.30, 0.02), (-0.20, 0.04), (-0.24, -0.12), (-0.12, -0.06), (-0.14, -0.24),
          (-0.03, -0.16), (-0.04, -0.34), (0.04, -0.26), (0.0, -0.48), (0.12, -0.31), (0.13, -0.46), (0.20, -0.30),
          (0.44, -0.26), (0.44, -0.17), (0.24, -0.12), (0.20, -0.04), (0.14, 0.02), (0.22, 0.10), (0.13, 0.11),
          (0.12, 0.30), (0.18, 0.42), (0.02, 0.42), (0.0, 0.30), (-0.10, 0.42), (-0.24, 0.42), (-0.22, 0.30)]


def lizard_shape(cx, cy, s):
    """The Void Lizard standing, facing east, as its own sheet draws it: a
    spined back, two horns, a long jaw, its tail on the ground behind."""
    def shape(p, inset=0.0):
        k = 1 - inset / (s * 0.4)
        p.poly([(cx + x * s * k, cy + y * s * k) for x, y in LIZARD])
    return shape


def lizard(c, cx, cy, s):
    """The lizard in void, its white edge, its eye and teeth white."""
    void(c, lizard_shape(cx, cy, s), max(1.2, s * 0.02))
    c.put(c.mask(lambda p: p.poly([(cx + 0.20 * s, cy - 0.25 * s), (cx + 0.30 * s, cy - 0.23 * s), (cx + 0.22 * s, cy - 0.21 * s)])), EDGE)
    c.put(c.mask(lambda p: [p.poly([(cx + x * s, cy - 0.17 * s), (cx + (x + 0.03) * s, cy - 0.17 * s), (cx + (x + 0.015) * s, cy - 0.12 * s)]) for x in (0.26, 0.32, 0.38)]), EDGE)


def gate(c, k):
    x0, x1, f = 0, 200, KEEP_FLOOR
    # The arch the road comes in by: two piers, a round head, its stones.
    c.put(c.mask(lambda p: (p.rect(x0, 280, x1, f), p.ellipse((x0 + x1) / 2, 280, (x1 - x0) / 2, 70))), STONE)
    c.put(c.mask(lambda p: (p.rect(x0 + 40, 340, x1 - 40, f), p.ellipse((x0 + x1) / 2, 340, (x1 - x0) / 2 - 40, 50))), STONE_DARK)
    c.put(c.mask(lambda p: [p.rect(x0, y, x0 + 40, y + 2) for y in range(310, f, 40)] + [p.rect(x1 - 40, y + 20, x1, y + 22) for y in range(300, f - 20, 40)]), STONE_LIGHT, 0.5)
    # The portcullis, up in the arch: its teeth.
    c.put(c.mask(lambda p: [p.rect(x, 300, x + 5, 360) for x in range(x0 + 50, x1 - 44, 18)]), IRON)
    c.put(c.mask(lambda p: [p.poly([(x, 360), (x + 5, 360), (x + 2.5, 372)]) for x in range(x0 + 50, x1 - 44, 18)]), IRON_LIGHT)
    c.put(c.mask(box(x0 + 44, 318, x1 - 44, 324)), IRON)
    # Over the arch, the void has put its own sign: the lizard.
    lizard(c, (x0 + x1) / 2, 228, 90)


def banner(c, k):
    x, top = BANNER_X, BANNER_TOP
    c.put(c.mask(box(x - 54, top - 6, x + 54, top + 2)), IRON)
    c.put(c.mask(lambda p: [p.ellipse(xx, top - 2, 6) for xx in (x - 54, x + 54)]), IRON_LIGHT)
    shape = lambda p, inset=0.0: p.poly([(x - 44 + inset, top + inset), (x + 44 - inset, top + inset), (x + 44 - inset, top + 230 - inset), (x, top + 196 - inset), (x - 44 + inset, top + 230 - inset)])
    void(c, shape, 2.2)
    # On it the lizard, drawn in its edge, and a star under its foot.
    c.put(c.mask(lizard_shape(x, top + 92, 84)), EDGE, 0.9)
    c.put(c.mask(lambda p: p.poly([(x + 0.20 * 84, top + 92 - 0.25 * 84), (x + 0.30 * 84, top + 92 - 0.23 * 84), (x + 0.22 * 84, top + 92 - 0.21 * 84)])), VOID)
    star(c, x + 4, top + 162, 9, mix(GOLD, VOID, 0.55))


def star_statue(c, k):
    x, f = STATUE_X, KEEP_FLOOR
    # The plinth.
    c.put(c.mask(box(x - 50, f - 70, x + 50, f)), STONE_LIGHT)
    c.put(c.mask(box(x + 34, f - 70, x + 50, f)), STONE)
    c.put(c.mask(box(x - 58, f - 80, x + 58, f - 68)), mix(STONE_LIGHT, CREAM, 0.3))
    c.put(c.mask(box(x - 36, f - 46, x + 36, f - 30)), STONE, 0.6)
    # The town's star, in pale stone, a face that smiled.
    star(c, x, f - 140, 72, mix(CREAM, STONE_LIGHT, 0.35), 0.48)
    star(c, x + 6, f - 134, 58, mix(CREAM, STONE_LIGHT, 0.55), 0.48)
    c.put(c.mask(lambda p: p.line([(x - 18, f - 116), (x, f - 108), (x + 18, f - 116)], 2.4)), STONE)
    # The void's ink, poured from its top point over its eyes, and pooled.
    ink = lambda p, inset=0.0: (p.poly([(x - 10 + inset, f - 216), (x + 12 - inset, f - 216), (x + 30 - inset, f - 158), (x + 36 - inset, f - 140), (x + 22 - inset, f - 130), (x + 14 - inset, f - 146), (x + 4, f - 136), (x - 12 + inset, f - 148), (x - 26 + inset, f - 130), (x - 34 + inset, f - 146), (x - 28 + inset, f - 160)]),
                                p.ellipse(x - 26, f - 120, 4 - inset * 0.5, 7 - inset * 0.5), p.ellipse(x + 26, f - 108, 3.5 - inset * 0.5, 6 - inset * 0.5))
    void(c, ink, 1.4)
    void(c, lambda p, inset=0.0: p.ellipse(x + 30, f - 79, 22 - inset, 4 - inset * 0.4), 1.2)


def stair(c, k):
    x0, x1 = STAIR_W
    f = KEEP_FLOOR
    for a, b in ((x0 - 26, x0), (x1, x1 + 26)):
        c.put(c.mask(box(a, f - 12, b, f)), STONE_LIGHT)
        c.put(c.mask(box(a, f - 4, b, f)), STONE)
    # A rail either side, so nobody walks in by mistake.
    for x in (x0 - 18, x1 + 14):
        c.put(c.mask(box(x, f - 64, x + 4, f - 12)), IRON)
        c.put(c.mask(lambda p: p.ellipse(x + 2, f - 66, 4)), IRON_LIGHT)


def span(c, k):
    x0, x1 = SPAN
    f = BRIDGE_FLOOR
    # The lava in the pit, its crust, its glow up the pit's walls.
    c.put(c.mask(box(x0, f + 26, x1, PIT_FLOOR + 8)), LAVA_DEEP)
    c.put(c.mask(lambda p: [p.ellipse(x, f + 30, 22, 7) for x in range(x0 + 10, x1, 36)]), LAVA)
    c.put(c.mask(lambda p: [p.ellipse(x + 8, f + 28, 8, 3) for x in range(x0 + 10, x1, 36)]), LAVA_HOT)
    c.put(c.mask(lambda p: [p.ellipse(x, f + 44, 3) for x in range(x0 + 30, x1, 97)]), LAVA_HOT, 0.8)
    c.put(c.mask(box(x0, f - 40, x1, f + 30), blur=14), LAVA, 0.22)
    # The deck: planks, end on, under the walk.
    c.put(c.mask(box(x0, f, x1, f + 14)), WOOD)
    c.put(c.mask(lambda p: [p.rect(x, f, x + 1.5, f + 14) for x in range(x0 + 20, x1, 24)]), WOOD_DARK)
    c.put(c.mask(box(x0, f, x1, f + 2)), mix(WOOD, (255, 255, 255), 0.25))
    # Its posts and the chains between them.
    posts = list(range(x0, x1 + 1, 208))
    for x in posts:
        c.put(c.mask(box(x - 4, f - 54, x + 4, f)), IRON)
        c.put(c.mask(lambda p: p.ellipse(x, f - 56, 6)), IRON_LIGHT)
    for a, b in zip(posts, posts[1:]):
        pts = [(a + (b - a) * t / 16, f - 52 + 18 * math.sin(math.pi * t / 16)) for t in range(17)]
        c.put(c.mask(lambda p: p.line(pts, 2.4)), IRON)
        c.put(c.mask(lambda p: [p.ring(x, y, 2.4, 1) for x, y in pts[1:-1:2]]), IRON_LIGHT, 0.7)


def switch(c, k):
    x, f = SWITCH_X, BRIDGE_FLOOR
    # A stone block with a big round button on it, pink: the switch.
    c.put(c.mask(box(x - 28, f - 40, x + 28, f)), STONE_LIGHT)
    c.put(c.mask(box(x + 18, f - 40, x + 28, f)), STONE)
    c.put(c.mask(lambda p: p.ellipse(x, f - 44, 24, 12)), PINK_DARK)
    c.put(c.mask(lambda p: p.ellipse(x, f - 48, 22, 10)), PINK)
    c.put(c.mask(lambda p: p.ellipse(x - 7, f - 51, 7, 3)), PINK_LIGHT)
    star(c, x, f - 22, 8, GOLD)
    # The wire from it to the bridge, along the ground.
    c.put(c.mask(lambda p: p.line([(x - 28, f - 6), (x - 70, f - 4), (x - 100, f - 2)], 1.6)), LAVA_DEEP)


def tea_table(c, k):
    x, f = TABLE_X, BRIDGE_FLOOR
    c.put(c.mask(box(x - 40, f - 44, x + 40, f - 38)), WOOD)
    for lx in (x - 32, x + 28):
        c.put(c.mask(box(lx, f - 38, lx + 4, f)), WOOD_DARK)
    # A cloth, a pot, a cup on its saucer, a book face down.
    c.put(c.mask(lambda p: p.poly([(x - 42, f - 44), (x + 42, f - 44), (x + 38, f - 30), (x - 38, f - 30)])), CREAM)
    c.put(c.mask(lambda p: [p.ellipse(x, f - 37, 3) for x in range(int(x - 34), int(x + 36), 10)]), PINK_LIGHT)
    void(c, lambda p, inset=0.0: (p.ellipse(x - 18, f - 56, 12 - inset, 11 - inset), p.rect(x - 34 + inset, f - 60 + inset, x - 28, f - 56 - inset)), 1.2)
    c.put(c.mask(lambda p: p.ellipse(x + 10, f - 45, 9, 2.5)), CREAM)
    c.put(c.mask(lambda p: p.poly([(x + 4, f - 54), (x + 16, f - 54), (x + 14, f - 46), (x + 6, f - 46)])), CREAM)
    c.put(c.mask(lambda p: p.ring(x + 18, f - 50, 3, 1.2)), CREAM)
    c.put(c.mask(lambda p: p.poly([(x + 22, f - 46), (x + 38, f - 48), (x + 38, f - 44), (x + 22, f - 44)])), GOLD_DARK)


PIECES: Dict[str, Piece] = {
    "keep_gate": Piece((0, 150, 200, KEEP_FLOOR), gate),
    "keep_banner": Piece((BANNER_X - 64, BANNER_TOP - 14, BANNER_X + 64, BANNER_TOP + 236), banner),
    "keep_star_statue": Piece((STATUE_X - 90, KEEP_FLOOR - 240, STATUE_X + 90, KEEP_FLOOR), star_statue),
    "keep_stair": Piece((STAIR_W[0] - 32, KEEP_FLOOR - 76, STAIR_W[1] + 32, KEEP_FLOOR), stair),
    "bridge_span": Piece((SPAN[0] - 10, BRIDGE_FLOOR - 70, SPAN[1] + 10, PIT_FLOOR + 8), span),
    "bridge_switch": Piece((SWITCH_X - 110, BRIDGE_FLOOR - 64, SWITCH_X + 36, BRIDGE_FLOOR), switch),
    "bridge_tea_table": Piece((TABLE_X - 48, BRIDGE_FLOOR - 70, TABLE_X + 48, BRIDGE_FLOOR), tea_table),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
