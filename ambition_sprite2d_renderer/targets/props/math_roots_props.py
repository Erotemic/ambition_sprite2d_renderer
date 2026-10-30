"""The roots of the Fractal Woods (`math_fractal_roots`, the math dimension):
under the woods, west of the Mobius Mine on its floor, the great fractal
tree's roots, branching all the way down; up through a knot of them into
the woods again (the knot is opened from below).

Drawn in room coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/math_town/make_specs.py` (`fractal_woods`,
`fractal_roots`): the woods' floor (y 704, its foot 768) and the knot's hole
(x 800..864); the roots' floor (y 576), roof (to y 64), the shaft up to the
knot (x 208..272; its ladder the engine's), the way east into the mine at
the floor.

- `woods_root_knot`: a knot of roots plugging the hole under the great tree
  (the look of the lock wall the lever below opens).
- `woods_root_hole`: the hole, dark, roots round its rim (seen once the knot
  is open).
- `roots_west`: earth, the shaft up under the knot; the great tree's root,
  branching in halves and halves of halves to hair roots; a lantern; a
  surveyor's lost protractor.
- `roots_east`: more roots, each branch a smaller root; glowing toadstools
  in a sunflower's spiral (the golden angle); a vein of crystal in a
  Sierpinski triangle; the timbers where the mine begins.

Animations: ``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .math_town_terraces import PAL

WOODS_FLOOR, WOODS_H = 704, 768
KNOT = (800, 864)
W, FLOOR, ROOF = 1600, 576, 64
SHAFT = (208, 272)
EARTH = (96, 74, 58)
EARTH_DARK = (64, 48, 38)
ROOT = (150, 112, 74)
ROOT_DARK = (104, 76, 50)
TIMBER = (120, 86, 52)
GLOW = (170, 240, 200)
CRYSTAL = (180, 200, 240)
LAMP = (255, 210, 130)
BRASS = (200, 170, 90)


def branch(c, x, y, ang, ln, width, depth, rng, out):
    """A root from (x, y) heading `ang` (radians, 0 = down), splitting in two
    `depth` more times: each child shorter and thinner. Segments go to `out`."""
    x2, y2 = x + ln * math.sin(ang), y + ln * math.cos(ang)
    out.append(((x, y), (x2, y2), width))
    if depth == 0:
        return
    for turn in (-1, 1):
        branch(c, x2, y2, ang + turn * rng.uniform(0.35, 0.6), ln * 0.68, max(1.2, width * 0.62), depth - 1, rng, out)


def roots(c, x, y, ln, width, depth, seed, ang=0.0):
    rng = c.rand(seed)
    segs = []
    branch(c, x, y, ang, ln, width, depth, rng, segs)
    c.put(c.mask(lambda p: [p.line([a, b], w + 2) for a, b, w in segs]), ROOT_DARK)
    c.put(c.mask(lambda p: [p.line([a, b], w) for a, b, w in segs]), ROOT)


def earth(c, x0, x1, seed):
    m = c.mask(box(x0, ROOF, x1, FLOOR))
    c.put(m, EARTH)
    c.tone(m * (c.noise(seed, 24, 8, 3) - 0.5), 0.3)
    c.put(m * (c.noise(seed + "_strata", 4, 14, 2) > 0.62), EARTH_DARK, 0.5)
    c.tone(m * np.clip((ROOF + 120 - c.y) / 100, 0, 1), -0.35)
    c.put(c.mask(box(x0, 16, x1, ROOF)), EARTH_DARK)


def knot(c, k):
    x0, x1 = KNOT
    c.put(c.mask(box(x0, WOODS_FLOOR, x1, WOODS_H)), EARTH_DARK)
    rng = c.rand("knot")
    segs = [((rng.uniform(x0, x1), WOODS_FLOOR + rng.uniform(0, 64)), (rng.uniform(x0, x1), WOODS_FLOOR + rng.uniform(0, 64)), rng.uniform(4, 9)) for _ in range(16)]
    c.put(c.mask(lambda p: [p.line([a, b], w + 2) for a, b, w in segs]), ROOT_DARK)
    c.put(c.mask(lambda p: [p.line([a, b], w) for a, b, w in segs]), ROOT)
    c.put(c.mask(box(x0, WOODS_FLOOR, x1, WOODS_FLOOR + 3)), mix(ROOT, (255, 255, 255), 0.2))


def hole(c, k):
    x0, x1 = KNOT
    m = c.mask(box(x0, WOODS_FLOOR, x1, WOODS_H))
    c.put(m, (30, 24, 20))
    c.tone(m * np.clip((c.y - WOODS_FLOOR) / 60, 0, 1), -0.5)
    c.put(c.mask(lambda p: [p.line([(x, WOODS_FLOOR), (x + 6, WOODS_FLOOR + 30)], 3) for x in (x0 + 2, x1 - 8)]), ROOT_DARK)


def west(c, k):
    earth(c, 16, 800, "roots_w")
    s0, s1 = SHAFT
    c.put(c.mask(box(s0, 16, s1, ROOF)), (30, 24, 20))
    # The great tree's taproot, coming down beside the shaft, and its kin.
    roots(c, 330, ROOF, 140, 22, 6, "taproot")
    roots(c, 620, ROOF, 110, 14, 5, "root_b", ang=0.25)
    roots(c, 60, ROOF, 90, 10, 4, "root_c", ang=-0.2)
    # A lantern hung on a root; the lost protractor.
    c.put(c.mask(lambda p: (p.line([(470, ROOF), (470, 200)], 1.2), p.rect(462, 200, 478, 222))), (40, 40, 44))
    c.put(c.mask(box(465, 203, 475, 219)), LAMP)
    c.light(c.mask(lambda p: p.ellipse(470, 220, 110, 90), blur=18), LAMP, 0.25)
    c.put(c.mask(lambda p: (p.ring(700, FLOOR, 26, 3), p.rect(672, FLOOR - 3, 728, FLOOR))), BRASS)
    c.put(c.mask(box(670, FLOOR - 26, 730, FLOOR - 25)) * c.mask(lambda p: p.ellipse(700, FLOOR, 26)), BRASS)


def east(c, k):
    earth(c, 800, W - 16, "roots_e")
    roots(c, 1000, ROOF, 120, 16, 5, "root_d", ang=-0.15)
    roots(c, 1380, ROOF, 100, 12, 5, "root_e", ang=0.2)
    # Toadstools in a sunflower's spiral: seed n at radius ~ sqrt(n), turned
    # by the golden angle.
    cx, cy = 1180, FLOOR - 90
    golden = math.pi * (3 - math.sqrt(5))
    pts = [(cx + 7 * math.sqrt(n) * math.cos(n * golden), cy + 4.2 * math.sqrt(n) * math.sin(n * golden)) for n in range(1, 90)]
    c.put(c.mask(lambda p: [p.ellipse(x, y, 3.4, 2.4) for x, y in pts]), GLOW)
    c.light(c.mask(lambda p: p.ellipse(cx, cy, 90, 50), blur=14), GLOW, 0.35)
    # A vein of crystal in the wall: a Sierpinski triangle, three levels.
    def tri(x, y, s, d, out):
        if d == 0:
            out.append([(x, y), (x + s, y), (x + s / 2, y - s * 0.87)])
            return
        tri(x, y, s / 2, d - 1, out)
        tri(x + s / 2, y, s / 2, d - 1, out)
        tri(x + s / 4, y - s * 0.435, s / 2, d - 1, out)
    tris = []
    tri(860, 330, 140, 3, tris)
    c.put(c.mask(lambda p: [p.poly(t) for t in tris]), CRYSTAL)
    c.light(c.mask(lambda p: p.poly([(860, 330), (1000, 330), (930, 208)]), blur=10), CRYSTAL, 0.2)
    # Where the mine begins: its timbers.
    c.put(c.mask(lambda p: (p.rect(W - 120, ROOF, W - 104, FLOOR), p.rect(W - 130, ROOF, W - 16, ROOF + 16))), TIMBER)


PIECES: Dict[str, Piece] = {
    "woods_root_knot": Piece((KNOT[0], WOODS_FLOOR, KNOT[1], WOODS_H), knot),
    "woods_root_hole": Piece((KNOT[0], WOODS_FLOOR, KNOT[1], WOODS_H), hole),
    "roots_west": Piece((16, 16, 800, FLOOR), west),
    "roots_east": Piece((800, 16, W - 16, FLOOR), east),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
