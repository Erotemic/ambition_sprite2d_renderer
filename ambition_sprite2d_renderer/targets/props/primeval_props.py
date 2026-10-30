"""Scenery of the primeval trail (the jungle dimension, `dinosaur.ldtk`).

Drawn in each room's coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/primeval/make_specs.py`.

- `primeval_tyrant_hall_room`: the T-rex's hall (`primeval_tyrant_hall`,
  1792 x 704, floor y 672): a sunken temple the jungle took back. Mossy
  cracked walls, light through holes in the roof, two great carved tyrant
  heads in the walls, his throne with a crown on a cushion (much too small
  for him), braziers, bones, vines; the ledges (y 464) and steps (y 560) by
  each wall as fallen blocks.

Animations: ``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale

PAL = {
    "stone": (120, 128, 104), "stone_light": (190, 196, 160), "trim": (200, 196, 160), "dark": (30, 36, 30),
    "glass_top": (150, 200, 180), "glass_low": (60, 90, 80), "lamp": (255, 190, 110), "wood": (100, 70, 44),
    "leaf": (64, 120, 56), "iron": (40, 40, 40), "brass": (210, 160, 70), "glaze": (210, 170, 80),
}
TEMPLE = (112, 118, 96)
TEMPLE_DARK = (64, 70, 56)
TEMPLE_LIGHT = (176, 180, 144)
MOSS = (88, 130, 60)
LEAF = (60, 112, 50)
LEAF_LIGHT = (120, 170, 80)
BONE = (230, 222, 196)
GOLD = (236, 196, 84)
VELVET = (150, 40, 50)
FIRE = (255, 160, 60)
SUN = (255, 236, 170)

HALL_W, HALL_H, HALL_FLOOR = 1792, 704, 672
LEDGES = ((16, 208, 464), (1584, 1776, 464))
STEPS = ((240, 368, 560), (1424, 1552, 560))


def blocks(c, m, colour, course=26.0, length=44.0, tag="blocks"):
    """Big temple blocks where `m` is: each its own tone, cracked, mossy."""
    row = np.floor(c.y / course)
    u = c.x / length + (row % 2) * 0.5
    col = np.floor(u)
    h = (np.sin(row * 12.9898 + col * 78.233) * 43758.5453) % 1.0
    c.put(m, colour)
    c.tone(m * (h - 0.5), 0.22)
    fy, fx = c.y / course - row, u - col
    joint = ((fy < 0.06) | (fx < 0.03)).astype(np.float32)
    c.put(m * joint, scale(colour, 0.6), 0.8)
    # A few cracks: where the noise crosses its middle, and only in some blocks.
    cracks = np.clip(1 - np.abs(c.noise((tag, "cracks"), 10, 6, 2) - 0.5) * 90, 0, 1) * (h > 0.6)
    c.put(m * cracks, scale(colour, 0.55), 0.5)
    moss = np.clip((c.noise((tag, "moss"), 10, 6, 3) - 0.55) * 4, 0, 1)
    c.put(m * moss, MOSS, 0.75)


def vine(c, x, top, length, tag, sway=6.0):
    rng = c.rand("vine", tag)
    pts = [(x + sway * math.sin(t / 30.0 + rng.random()), top + t) for t in np.arange(0, length, 4)]
    c.put(c.mask(lambda p: p.line(pts, 1.6)), (70, 90, 50))
    leaves = c.mask(lambda p: [p.ellipse(px + rng.uniform(-5, 5), py, rng.uniform(2.5, 5), rng.uniform(1.6, 3)) for px, py in pts[::2]])
    c.put(leaves, LEAF)
    c.tone(leaves * (c.noise(("vl", tag), 20, 60, 1) - 0.5), 0.4)
    c.put(c.mask(lambda p: [p.ellipse(px + 3, py, 1.6) for px, py in pts[5::9]]), (230, 90, 120))


def fern(c, x, ground, size, tag):
    rng = c.rand("fern", tag)
    for i in range(7):
        a = math.radians(-160 + i * 23 + rng.uniform(-6, 6))
        L = size * rng.uniform(0.7, 1.0)
        tip = (x + L * math.cos(a), ground + L * math.sin(a) * 0.8)
        stem = [(x + (tip[0] - x) * t, ground + (tip[1] - ground) * t - 18 * math.sin(math.pi * t) * (size / 80)) for t in np.linspace(0, 1, 16)]
        c.put(c.mask(lambda p: p.line(stem, 1.4)), LEAF)
        c.put(c.mask(lambda p: [p.ellipse(px, py, 4 * (1 - j / 16) + 1, 2) for j, (px, py) in enumerate(stem[2:], start=2)]), LEAF_LIGHT if i % 2 else LEAF)


def tyrant_head(c, cx, cy, s, facing, tag):
    """A great tyrant's head carved in the wall: jaw, teeth, a deep eye."""
    f = facing
    pts = [(cx - 70 * s * f, cy - 40 * s), (cx + 50 * s * f, cy - 46 * s), (cx + 110 * s * f, cy - 20 * s), (cx + 118 * s * f, cy + 8 * s),
           (cx + 40 * s * f, cy + 14 * s), (cx - 60 * s * f, cy + 30 * s), (cx - 86 * s * f, cy)]
    head = c.mask(lambda p: p.poly(pts))
    blocks(c, head, TEMPLE_LIGHT, 14, 22, tag)
    jaw = c.mask(lambda p: p.poly([(cx - 50 * s * f, cy + 34 * s), (cx + 40 * s * f, cy + 22 * s), (cx + 100 * s * f, cy + 30 * s), (cx + 96 * s * f, cy + 48 * s), (cx - 40 * s * f, cy + 60 * s)]))
    blocks(c, jaw, TEMPLE_LIGHT, 14, 22, (tag, "jaw"))
    mouth = c.mask(lambda p: p.poly([(cx - 40 * s * f, cy + 22 * s), (cx + 118 * s * f, cy + 10 * s), (cx + 100 * s * f, cy + 30 * s), (cx - 50 * s * f, cy + 34 * s)]))
    c.put(mouth, (24, 20, 18))
    teeth = c.mask(lambda p: [p.poly([(cx + (x0) * s * f, cy + (y0) * s), (cx + (x0 + 9) * s * f, cy + (y0) * s), (cx + (x0 + 4) * s * f, cy + (y0 + d) * s)])
                              for x0, y0, d in [(t, 14 - t * 0.04, 13) for t in range(-30, 110, 14)] + [(t, 32, -12) for t in range(-36, 96, 14)]])
    c.put(teeth, BONE)
    eye = c.mask(lambda p: p.ellipse(cx + 40 * s * f, cy - 22 * s, 11 * s, 7 * s))
    c.put(eye, (20, 16, 14))
    c.light(c.mask(lambda p: p.ellipse(cx + 40 * s * f, cy - 22 * s, 4 * s), blur=3), FIRE, 0.8)
    c.put(c.mask(lambda p: p.line([(cx + 20 * s * f, cy - 34 * s), (cx + 62 * s * f, cy - 30 * s)], 4 * s)), TEMPLE_DARK)
    c.put(c.mask(lambda p: p.ellipse(cx + 104 * s * f, cy - 8 * s, 3 * s)), TEMPLE_DARK)


def brazier(c, x, ground, tag):
    c.put(c.mask(lambda p: (p.rect(x - 6, ground - 60, x + 6, ground), p.rect(x - 16, ground - 6, x + 16, ground))), TEMPLE_DARK)
    bowl = c.mask(lambda p: p.ellipse(x, ground - 64, 22, 10)) * (c.y > ground - 66)
    c.put(bowl, (90, 70, 50))
    rng = c.rand("flame", tag)
    for i in range(5):
        fx = x + rng.uniform(-12, 12)
        h = rng.uniform(18, 34)
        c.put(c.mask(lambda p: p.poly([(fx - 7, ground - 66), (fx + 7, ground - 66), (fx + rng.uniform(-3, 3), ground - 66 - h)])), mix(FIRE, (255, 240, 160), i / 5), 0.9)
    c.light(c.mask(lambda p: p.ellipse(x, ground - 80, 70, 60), blur=30), FIRE, 0.4)


def bones(c, x, ground, n, tag):
    rng = c.rand("bones", tag)
    b = []
    for _ in range(n):
        bx, a, L = x + rng.uniform(-50, 50), rng.uniform(-0.6, 0.6), rng.uniform(16, 34)
        p0 = (bx - L / 2 * math.cos(a), ground - 3 - L / 2 * math.sin(a))
        p1 = (bx + L / 2 * math.cos(a), ground - 3 + L / 2 * math.sin(a))
        b.append((p0, p1))
    c.put(c.mask(lambda p: [p.line([p0, p1], 3) for p0, p1 in b] + [p.ellipse(q[0], q[1], 3.2) for pair in b for q in pair]), BONE)
    sx = x + rng.uniform(-20, 20)
    c.put(c.mask(lambda p: (p.ellipse(sx, ground - 9, 11, 8), p.rect(sx - 2, ground - 4, sx + 14, ground))), BONE)
    c.put(c.mask(lambda p: p.ellipse(sx - 3, ground - 11, 2.4)), (40, 34, 30))


def tyrant_hall_room(c, k):
    """The T-rex's hall."""
    w, g = HALL_W, HALL_FLOOR
    k.ground = g
    wall = c.mask(box(0, 0, w, g))
    blocks(c, wall, TEMPLE, tag="hall_wall")
    c.tone(wall, -0.2)
    # Light through holes in the roof: shafts down onto the floor.
    for hx, width in ((520, 70), (900, 110), (1290, 70)):
        c.put(c.mask(lambda p: p.ellipse(hx, 14, width * 0.6, 12)), SUN, 0.9)
        shaft = c.mask(lambda p: p.poly([(hx - width * 0.5, 14), (hx + width * 0.5, 14), (hx + width * 1.1 + 60, g), (hx - width * 0.4 + 60, g)]), blur=10)
        c.light(shaft, SUN, 0.22)
    rng = c.rand("dust")
    c.put(c.mask(lambda p: [p.ellipse(rng.uniform(450, 1400), rng.uniform(40, g - 40), 1.0) for _ in range(90)]), SUN, 0.5)
    # Two great heads carved in the walls, facing into the arena.
    tyrant_head(c, 250, 250, 1.3, 1, "head_w")
    tyrant_head(c, w - 250, 250, 1.3, -1, "head_e")
    # The throne at the back of the arena: a stone seat far too big for a
    # man, and on a cushion a crown far too small for a tyrant.
    tx = 900
    throne = c.mask(lambda p: (p.rect(tx - 120, g - 150, tx + 120, g), p.rect(tx - 140, g - 330, tx - 90, g - 150), p.rect(tx + 90, g - 330, tx + 140, g - 150), p.poly([(tx - 120, g - 330), (tx + 120, g - 330), (tx + 90, g - 420), (tx - 90, g - 420)])))
    blocks(c, throne, TEMPLE_LIGHT, 20, 34, "throne")
    c.put(c.mask(box(tx - 90, g - 330, tx + 90, g - 150)), TEMPLE_DARK)
    c.put(c.mask(lambda p: p.ellipse(tx, g - 160, 40, 12)), VELVET)
    c.put(c.mask(lambda p: p.ellipse(tx, g - 164, 36, 8)), mix(VELVET, (255, 255, 255), 0.15))
    crown = c.mask(lambda p: p.poly([(tx - 12, g - 168), (tx + 12, g - 168), (tx + 14, g - 182), (tx + 7, g - 176), (tx, g - 186), (tx - 7, g - 176), (tx - 14, g - 182)]))
    c.put(crown, GOLD)
    c.light(c.mask(lambda p: p.ellipse(tx, g - 176, 14), blur=4), GOLD, 0.5)
    c.put(c.mask(lambda p: [p.ellipse(x, g - 172, 1.6) for x in (tx - 6, tx, tx + 6)]), (200, 40, 60))
    # The tyrant's tooth sign over the throne.
    c.put(c.mask(lambda p: p.poly([(tx - 18, g - 420), (tx + 18, g - 420), (tx, g - 470)])), BONE)
    # The ledges and steps by each wall: fallen blocks whose tops are the walk
    # lines.
    for x0, x1, y in LEDGES + STEPS:
        m = c.mask(box(x0, y, x1, g))
        blocks(c, m, TEMPLE_LIGHT, 24, 40, ("ledge", x0))
        c.put(c.mask(box(x0, y, x1, y + 3)), mix(TEMPLE_LIGHT, (255, 250, 220), 0.5))
        c.tone(m * np.clip((c.y - y) / (g - y), 0, 1), -0.2)
    # Braziers, bones, ferns and vines.
    for bx in (640, 1160):
        brazier(c, bx, g, ("br", bx))
    bones(c, 520, g, 7, "b1")
    bones(c, 1290, g, 6, "b2")
    for fx, s in ((420, 70), (1380, 80), (760, 50), (1040, 56)):
        fern(c, fx, g, s, ("f", fx))
    for vx, L in ((120, 180), (380, 120), (700, 90), (1100, 140), (1420, 110), (1680, 190)):
        vine(c, vx, 0, L, ("v", vx))


PIECES: Dict[str, Piece] = {
    "primeval_tyrant_hall_room": Piece((0, 0, HALL_W, HALL_FLOOR), tyrant_hall_room),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
