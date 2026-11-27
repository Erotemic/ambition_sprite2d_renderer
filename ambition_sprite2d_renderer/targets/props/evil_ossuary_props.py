"""The ossuary of the other founders (`evil_other_founders`, the Evil
dimension): behind a cracked wall at the catacombs' west end, where the
castle put the founders before the founder: six of them, struck from the
record and from their busts.

Use the room dimensions in `evil_moor/make_specs.py`.

- `catacombs_cracked_wall`: the wall the castle bricked over the way west:
  skulls set in mortar, cracked through (the look of a breakable wall:
  hit it).
- `ossuary_room`: six busts on plinths, their faces chiselled off, each in
  his own hat (a tricorn, a crown, a mitre, a top hat, a bowler, a fez); a
  sunburst of thigh bones on the wall; candles; a brass plaque, scratched
  out.

Animations: ``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .evil_catacombs_props import BONE, BONE_DARK, CANDLE, STONE_DARK, vault
from .evil_inn_props import PAL

W, FLOOR, CEILING = 640, 512, 32
CRACK = (16, 48, FLOOR - 112)
BRASS = (190, 150, 70)
MARBLE = (196, 190, 182)
MARBLE_DARK = (140, 134, 128)
HATS = ((40, 36, 40), (220, 180, 80), (230, 226, 216), (30, 28, 32), (50, 44, 40), (150, 40, 40))


def cracked_wall(c, k):
    x0, x1, y0 = CRACK
    m = c.mask(box(x0, y0, x1, FLOOR))
    c.put(m, STONE_DARK)
    c.put(m * c.mask(lambda p: [p.ellipse(x0 + 9 + (j % 2) * 14, y, 7, 7) for j, y in enumerate(range(int(y0) + 10, FLOOR, 16))]), BONE_DARK)
    c.put(c.mask(lambda p: [p.ellipse(x0 + 9 + (j % 2) * 14 + dx, y - 1, 1.6, 2) for j, y in enumerate(range(int(y0) + 10, FLOOR, 16)) for dx in (-2.5, 2.5)]), (30, 24, 26))
    # The crack through it.
    c.put(c.mask(lambda p: p.line([(x0 + 18, y0), (x0 + 10, y0 + 30), (x0 + 22, y0 + 56), (x0 + 8, y0 + 84), (x0 + 16, FLOOR)], 2)), (14, 10, 12))
    c.put(c.mask(lambda p: p.line([(x0 + 22, y0 + 56), (x1, y0 + 64)], 1.4)), (14, 10, 12))
    c.light(c.mask(lambda p: p.line([(x0 + 10, y0 + 30), (x0 + 22, y0 + 56)], 3), blur=3), (255, 220, 160), 0.2)


def stone_shelf(c, x0, x1, y):
    for x in (x0 + 15, x1 - 15):
        c.put(c.mask(lambda p: p.poly([(x - 5, y + 14), (x + 12, y + 14), (x + 5, y + 38), (x - 5, y + 38)])), (68, 58, 57))
    c.put(c.mask(box(x0, y, x1, y + 16)), (102, 86, 79))
    c.put(c.mask(box(x0, y, x1, y + 4)), (172, 150, 132))


def room(c, k):
    vault(c, 16, W - 16)
    # The sunburst of thigh bones on the back wall.
    cx, cy = W / 2, 128
    c.put(c.mask(lambda p: [p.line([(cx + 30 * np.cos(a), cy + 30 * np.sin(a)), (cx + 65 * np.cos(a), cy + 65 * np.sin(a))], 5)
                            for a in np.linspace(0, 2 * np.pi, 16, endpoint=False)]), BONE)
    c.put(c.mask(lambda p: p.ellipse(cx, cy, 20, 20)), BONE)
    c.put(c.mask(lambda p: (*[p.ellipse(cx + dx, cy - 5, 5, 6) for dx in (-8, 8)], p.poly([(cx - 2, cy + 6), (cx + 2, cy + 6), (cx, cy + 2)]))), (30, 24, 26))
    c.put(c.mask(lambda p: (p.rect(cx - 9, cy + 12, cx + 9, cy + 13), *[p.rect(cx - 9 + j * 4.5, cy + 10, cx - 8.4 + j * 4.5, cy + 16) for j in range(5)])), (30, 24, 26))
    c.put(c.mask(box(211, 204, 429, 263)), MARBLE_DARK)
    c.put(c.mask(box(216, 209, 424, 258)), (50, 40, 44))
    stone_shelf(c, 144, 224, 448)
    stone_shelf(c, 256, 384, 384)
    stone_shelf(c, 416, 496, 448)
    c.put(c.mask(box(281, 379, 359, 384)), (87, 69, 59))
    # Six busts on plinths, their faces chiselled off, each in his hat.
    positions = ((70, 512), (173, 448), (225, 410), (415, 410), (467, 448), (570, 512))
    for i, (x, base) in enumerate(positions):
        top = base - 48
        c.put(c.mask(lambda p: (p.rect(x - 22, top, x + 22, base), p.rect(x - 28, top - 6, x + 28, top))), MARBLE_DARK)
        c.put(c.mask(box(x - 14, top + 13, x + 14, top + 26)), mix(BRASS, (0, 0, 0), 0.25))
        c.put(c.mask(lambda p: [p.line([(x + dx, top + 14), (x + dx + 5, top + 24)], 1) for dx in (-11, -4, 3)]), (75, 54, 46))
        c.put(c.mask(lambda p: (p.ellipse(x, top - 40, 18, 22), p.poly([(x - 26, top - 6), (x + 26, top - 6), (x + 16, top - 24), (x - 16, top - 24)]))), MARBLE)
        c.put(c.mask(lambda p: p.poly([(x - 10, top - 50), (x + 12, top - 52), (x + 10, top - 28), (x - 8, top - 26)])), MARBLE_DARK)
        c.put(c.mask(lambda p: [p.line([(x - 8 + j * 5, top - 48), (x - 6 + j * 5, top - 30)], 0.8) for j in range(4)]), scale(MARBLE_DARK, 0.7))
        hat = HATS[i]
        y = top - 60
        if i == 0:  # a tricorn
            c.put(c.mask(lambda p: p.poly([(x - 26, y + 4), (x, y - 14), (x + 26, y + 4), (x, y - 2)])), hat)
        elif i == 1:  # a crown
            c.put(c.mask(lambda p: p.poly([(x - 16, y + 4), (x - 16, y - 12), (x - 8, y - 4), (x, y - 16), (x + 8, y - 4), (x + 16, y - 12), (x + 16, y + 4)])), hat)
        elif i == 2:  # a mitre
            c.put(c.mask(lambda p: p.poly([(x - 14, y + 4), (x - 10, y - 20), (x, y - 28), (x + 10, y - 20), (x + 14, y + 4)])), hat)
            c.put(c.mask(lambda p: p.rect(x - 2, y - 24, x + 2, y + 4)), (200, 160, 70))
        elif i == 3:  # a top hat
            c.put(c.mask(lambda p: (p.rect(x - 24, y, x + 24, y + 4), p.rect(x - 14, y - 34, x + 14, y))), hat)
        elif i == 4:  # a bowler
            c.put(c.mask(lambda p: (p.rect(x - 24, y, x + 24, y + 4), p.ellipse(x, y, 16, 14))), hat)
        else:  # a fez
            c.put(c.mask(lambda p: p.poly([(x - 14, y + 4), (x - 11, y - 18), (x + 11, y - 18), (x + 14, y + 4)])), hat)
            c.put(c.mask(lambda p: p.line([(x, y - 18), (x + 12, y - 6)], 1.4)), (30, 30, 30))
    for x, y in ((131, 416), (249, 351), (391, 351), (509, 416)):
        c.put(c.mask(lambda p: (p.rect(x - 7, y + 18, x + 7, y + 23),
                                 p.poly([(x - 6, y + 22), (x + 7, y + 22), (x - 4, y + 30)]))), (88, 63, 48))
        c.put(c.mask(lambda p: (p.rect(x - 3, y + 4, x + 3, y + 18), p.ellipse(x, y, 2.4, 4))), (230, 220, 200))
        c.light(c.mask(lambda p: p.ellipse(x, y + 6, 70, 62), blur=12), CANDLE, 0.25)


PIECES: Dict[str, Piece] = {
    "catacombs_cracked_wall": Piece((CRACK[0], CRACK[2], CRACK[1], FLOOR), cracked_wall),
    "ossuary_room": Piece((16, 0, W - 16, FLOOR), room),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
