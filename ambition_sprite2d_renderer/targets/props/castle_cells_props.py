"""The cells under Castle Godwin (`castle_godwin_cells`, the Evil dimension):
the dungeon between the Complaints Department and the lab tower, where the
complaints end up, and the people who made them.

Drawn in room coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/castle_kitchens/make_specs.py` (`cells`):
the floor (y 512), the ceiling (to y 48), the ways west to the Complaints
Department and east into the tower, both at the floor.

- `castle_cells_room`: a low stone vault; three cells behind iron bars
  along the back wall (a cot, a bucket, a tally of days scratched on the
  stone; the middle cell's door open, its trusty out); the chute from the
  Complaints Department's suggestions box, and under it the heap of every
  suggestion ever made; the jailer's desk, its ring of keys, its stamp.

Animations: ``idle``, 1 frame. No drop shadows.
"""

from __future__ import annotations

from typing import Dict

import numpy as np

from . import castle_godwin as CG
from ._district_props import Piece, targets
from ._town_kit import box, mix, scale

W, FLOOR, CEILING = 720, 512, 48
PAL = {"stone": CG.STONE, "stone_light": CG.STONE_LIGHT, "dark": (22, 18, 26), "lamp": (255, 200, 120)}
STONE, STONE_DARK, STONE_LIGHT = CG.STONE, CG.STONE_DARK, CG.STONE_LIGHT
IRON = (46, 46, 52)
IRON_LIGHT = (96, 96, 104)
WOOD = (96, 64, 44)
WOOD_DARK = (60, 40, 30)
STRAW = (170, 140, 80)
PAPER = (220, 210, 186)
RED = CG.RED
LAMP = (255, 200, 120)
CELLS = ((60, 240), (260, 440), (460, 640))


def room(c, k):
    g = FLOOR
    wall = c.mask(box(16, CEILING, W - 16, g))
    c.put(wall, STONE)
    c.put(wall * c.mask(lambda p: [p.rect(16, y, W - 16, y + 1.4) for y in range(CEILING, g, 22)]), STONE_DARK, 0.8)
    c.put(wall * c.mask(lambda p: [p.rect(x + (22 if (y // 22) % 2 else 0), y, x + 1.4 + (22 if (y // 22) % 2 else 0), y + 22)
                                   for y in range(CEILING, g, 22) for x in range(16, W, 44)]), STONE_DARK, 0.7)
    c.tone(wall * (c.noise("cells_damp", 14, 8, 3) - 0.5), 0.18)
    c.tone(wall * np.clip((200 - c.y) / 150, 0, 1), -0.4)
    # The cells: dark inside, a cot, a bucket, a tally on the wall; bars.
    for i, (x0, x1) in enumerate(CELLS):
        inside = c.mask(box(x0, 150, x1, g))
        c.put(inside, STONE_DARK)
        c.tone(inside, -0.35)
        c.put(c.mask(box(x0 + 14, g - 34, x0 + 90, g - 26)), WOOD)
        c.put(c.mask(box(x0 + 14, g - 40, x0 + 90, g - 34)), STRAW)
        c.put(c.mask(lambda p: p.poly([(x1 - 50, g), (x1 - 46, g - 26), (x1 - 22, g - 26), (x1 - 18, g)])), WOOD_DARK)
        c.put(c.mask(lambda p: [p.rect(x0 + 30 + j * 6 + (j // 5) * 6, 220, x0 + 32 + j * 6 + (j // 5) * 6, 250) for j in range(5 + i * 7)]), STONE_LIGHT, 0.8)
        c.put(c.mask(lambda p: [p.line([(x0 + 28 + q * 36, 248), (x0 + 58 + q * 36, 222)], 1.4) for q in range((5 + i * 7) // 5)]), STONE_LIGHT, 0.8)
        c.put(c.mask(lambda p: (p.rect(x0 - 6, 140, x1 + 6, 150), p.rect(x0 - 6, g - 6, x1 + 6, g))), IRON)
        bars = [x for x in range(x0 + 8, x1, 18)]
        if i == 1:
            # The middle cell's door open: its bars swung out flat.
            bars = [x for x in bars if x < x0 + 60 or x > x1 - 60]
            c.put(c.mask(lambda p: [p.rect(x1 + 10, 150 + j * 4, x1 + 70, 152 + j * 4) for j in range(0, 90, 18)]), IRON)
        c.put(c.mask(lambda p: [p.rect(x, 150, x + 4, g - 6) for x in bars]), IRON)
        c.put(c.mask(lambda p: [p.rect(x, 150, x + 1.4, g - 6) for x in bars]), IRON_LIGHT)
    # The chute from the suggestions box, and the heap under it.
    c.put(c.mask(lambda p: p.poly([(16, 80), (60, 80), (110, 120), (80, 132)])), IRON)
    c.put(c.mask(lambda p: p.poly([(70, 120), (120, 120), (130, 140), (64, 140)])), IRON_LIGHT)
    rng = c.rand("suggestions")
    heap = c.mask(lambda p: p.poly([(40, g), (80, g - 60), (130, g - 72), (180, g - 50), (210, g)]))
    c.put(heap * c.mask(box(16, 140, 230, g)), PAPER)
    c.put(c.mask(lambda p: [p.rect(x, y, x + 18, y + 12) for x, y in ((rng.uniform(50, 190), rng.uniform(g - 64, g - 14)) for _ in range(22))]),
          mix(PAPER, (120, 110, 90), 0.3))
    c.put(c.mask(lambda p: [p.rect(x + 3, y + 3, x + 15, y + 4) for x, y in ((rng.uniform(50, 190), rng.uniform(g - 60, g - 12)) for _ in range(14))]), (90, 80, 70))
    # The jailer's desk: its ring of keys, its stamp, a lamp.
    d0, d1 = 540, 690
    c.put(c.mask(lambda p: (p.rect(d0, g - 48, d1, g - 40), p.rect(d0 + 8, g - 40, d0 + 14, g), p.rect(d1 - 14, g - 40, d1 - 8, g))), WOOD)
    c.put(c.mask(lambda p: p.ring(d0 + 40, g - 56, 9, 2)), IRON_LIGHT)
    c.put(c.mask(lambda p: [p.line([(d0 + 40 + dx, g - 50), (d0 + 42 + dx, g - 38)], 1.6) for dx in (-6, -2, 3, 7)]), IRON_LIGHT)
    c.put(c.mask(lambda p: (p.rect(d0 + 80, g - 58, d0 + 90, g - 48), p.ellipse(d0 + 85, g - 60, 6, 3))), RED)
    c.put(c.mask(lambda p: (p.rect(d1 - 40, g - 70, d1 - 26, g - 48), p.poly([(d1 - 46, g - 70), (d1 - 20, g - 70), (d1 - 33, g - 82)]))), IRON)
    c.light(c.mask(lambda p: p.ellipse(d1 - 33, g - 60, 60, 40), blur=12), LAMP, 0.3)


PIECES: Dict[str, Piece] = {
    "castle_cells_room": Piece((16, CEILING, W - 16, FLOOR), room),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
