"""The Fractal Woods (`math_fractal_woods`, the Math dimension): out of town,
east of the summit: every tree a forest, every branch a tree.

Drawn in room coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/math_town/make_specs.py` (`fractal_woods`):
the ground (y 704); the great tree's limbs, walked on (LIMBS); the Koch
hedge (x 1100..1320), the Sierpinski rock (x 1440..1700), the Mandelbrot
bush (x 1820..2240).

- `woods_great_tree`: a binary fractal tree, its trunk at x 700; the limbs
  the room walks on drawn flat and broad where they are.
- `woods_far_west`, `woods_far_east`: smaller fractal trees behind, paler
  with distance (one drawing in two frames).
- `woods_curiosities`: a hedge clipped to a Koch curve, a rock that is a
  Sierpinski triangle, a topiary in the shape of the Mandelbrot set (and,
  on its edge, a smaller one).

Animations: ``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .eureka_props import Batch, edge_line
from .math_town_terraces import PAL

W, FLOOR = 2400, 704
TRUNK_X = 700
#: The great tree's limbs walked on: (x0, x1, y).
LIMBS = ((540, 700, 592), (720, 880, 480), (560, 720, 368), (660, 800, 256))
KOCH = (1100, 1320)
SIERPINSKI = (1440, 1700)
MANDELBROT = (1820, 2240)
BARK = (92, 74, 60)
BARK_LIGHT = (140, 112, 88)
LEAF = (86, 132, 92)
LEAF_LIGHT = (130, 176, 120)
STONE = (150, 146, 136)


def branches(b, x, y, angle, length, width, depth, colour, rng, leaves=None):
    if depth == 0 or length < 4:
        if leaves is not None:
            leaves.append((x, y))
        return
    x1, y1 = x + length * math.cos(angle), y - length * math.sin(angle)
    b.add(colour, 1.0, lambda p, a=(x, y), c_=(x1, y1), w=width: p.line([a, c_], w))
    spread = 0.42 + rng.uniform(-0.06, 0.06)
    for sign in (-1, 1):
        branches(b, x1, y1, angle + sign * spread, length * 0.72, width * 0.68, depth - 1, colour, rng, leaves)


def great_tree(c, k):
    rng = c.rand("great_tree")
    b = Batch(c)
    leaves = []
    b.add(BARK, 1.0, lambda p: p.poly([(TRUNK_X - 26, FLOOR), (TRUNK_X + 26, FLOOR), (TRUNK_X + 14, FLOOR - 220), (TRUNK_X - 14, FLOOR - 220)]))
    branches(b, TRUNK_X, FLOOR - 220, math.pi / 2, 150, 22, 9, BARK, rng, leaves)
    b.draw()
    c.put(c.mask(lambda p: [p.ellipse(x, y, 7 + rng.uniform(-2, 3)) for x, y in leaves]), LEAF)
    c.put(c.mask(lambda p: [p.ellipse(x - 2, y - 2, 3) for x, y in leaves[::2]]), LEAF_LIGHT)
    c.tone(c.mask(lambda p: p.poly([(TRUNK_X - 26, FLOOR), (TRUNK_X - 6, FLOOR), (TRUNK_X - 4, FLOOR - 220), (TRUNK_X - 14, FLOOR - 220)])), 0.15)
    # The limbs walked on: broad and flat, each grown from the trunk.
    for x0, x1, y in LIMBS:
        near = x1 if x1 <= TRUNK_X else x0
        c.put(c.mask(lambda p: p.poly([(TRUNK_X, y + 30), (near, y + 6), (near, y + 14), (TRUNK_X, y + 40)])), BARK)
        c.put(c.mask(lambda p: p.poly([(x0, y), (x1, y), (x1 - 6, y + 14), (x0 + 6, y + 14)])), BARK)
        edge_line(c, x0, x1, y, BARK_LIGHT, 4)
        c.put(c.mask(lambda p: [p.ellipse(x, y - 2, 5) for x in (x0 + 4, x1 - 4)]), LEAF)


def far_trees(c, k):
    rng = c.rand("far_trees")
    for x, s, fade in ((140, 90, 0.55), (1050, 110, 0.5), (1380, 80, 0.6), (1760, 120, 0.5), (2300, 90, 0.55)):
        b = Batch(c)
        leaves = []
        colour = mix(BARK, (200, 210, 220), fade)
        b.add(colour, 1.0, lambda p, x=x, s=s: p.poly([(x - 8, FLOOR), (x + 8, FLOOR), (x + 5, FLOOR - s), (x - 5, FLOOR - s)]))
        branches(b, x, FLOOR - s, math.pi / 2, s * 0.6, 7, 7, colour, rng, leaves)
        b.draw()
        c.put(c.mask(lambda p: [p.ellipse(lx, ly, 4) for lx, ly in leaves]), mix(LEAF, (200, 210, 220), fade))


def koch(p0, p1, depth):
    if depth == 0:
        return [p0]
    (x0, y0), (x1, y1) = p0, p1
    dx, dy = (x1 - x0) / 3, (y1 - y0) / 3
    a = (x0 + dx, y0 + dy)
    b_ = (x0 + 2 * dx, y0 + 2 * dy)
    peak = (a[0] + dx * 0.5 + dy * math.sqrt(3) / 2, a[1] + dy * 0.5 - dx * math.sqrt(3) / 2)
    out = []
    for q0, q1 in ((p0, a), (a, peak), (peak, b_), (b_, p1)):
        out += koch(q0, q1, depth - 1)
    return out


def curiosities(c, k):
    g = FLOOR
    # The Koch hedge: its top a Koch curve.
    k0, k1 = KOCH
    top = koch((k0, g - 50), (k1, g - 50), 4) + [(k1, g - 50)]
    hedge = c.mask(lambda p: p.poly(top + [(k1, g), (k0, g)]))
    c.put(hedge, LEAF)
    c.tone(hedge * (c.noise("koch", 20, 6, 2) - 0.5), 0.25)
    c.put(c.mask(lambda p: p.line(top, 1.4)), LEAF_LIGHT)
    # The Sierpinski rock.
    s0, s1 = SIERPINSKI
    tris = [((s0, g), (s1, g), ((s0 + s1) / 2, g - (s1 - s0) * 0.8))]
    for _ in range(4):
        nxt = []
        for (a, b_, t) in tris:
            ab = ((a[0] + b_[0]) / 2, (a[1] + b_[1]) / 2)
            at = ((a[0] + t[0]) / 2, (a[1] + t[1]) / 2)
            bt = ((b_[0] + t[0]) / 2, (b_[1] + t[1]) / 2)
            nxt += [(a, ab, at), (ab, b_, bt), (at, bt, t)]
        tris = nxt
    rock = c.mask(lambda p: [p.poly(list(t)) for t in tris])
    c.put(rock, STONE)
    c.tone(rock * np.clip((c.x - (s0 + s1) / 2) / ((s1 - s0) / 2), -1, 1), -0.2)
    c.put(rock * np.clip((c.noise("sier_moss", 10, 6, 2) - 0.6) * 4, 0, 1), (100, 130, 80))
    # The Mandelbrot topiary: the set itself, clipped in box.
    m0, m1 = MANDELBROT
    cx, cy, sc = (m0 + m1) / 2, g - 170, 100.0
    re = (c.x - cx) / sc - 0.6
    im = (c.y - cy) / sc
    z = np.zeros_like(re, dtype=np.complex128)
    cpx = re + 1j * im
    inside = np.ones(re.shape, dtype=bool)
    near = (np.abs(re + 0.6) < 2.2) & (np.abs(im) < 1.4)
    for _ in range(40):
        z = np.where(inside & near, z * z + cpx, z)
        inside &= np.abs(z) <= 2.0
    bush = (inside & near).astype(np.float32)
    c.put(bush, (60, 104, 70))
    c.tone(bush * (c.noise("mandel", 30, 20, 2) - 0.5), 0.3)
    # Its stem and pot under the main cardioid (re -0.25).
    sx = cx + 0.35 * sc
    c.put(c.mask(lambda p: p.rect(sx - 5, cy + 0.6 * sc, sx + 5, g - 20)), BARK)
    c.put(c.mask(lambda p: (p.poly([(sx - 34, g - 26), (sx + 34, g - 26), (sx + 26, g), (sx - 26, g)]), p.ellipse(sx, g - 26, 34, 5))), (170, 90, 60))


PIECES: Dict[str, Piece] = {
    # One drawing in two frames (a frame is at most a sheet's page wide).
    "woods_far_west": Piece((40, 300, 1200, FLOOR), far_trees),
    "woods_far_east": Piece((1200, 300, W - 40, FLOOR), far_trees),
    "woods_great_tree": Piece((420, 20, 1000, FLOOR), great_tree),
    "woods_curiosities": Piece((1080, 400, 2300, FLOOR), curiosities),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
