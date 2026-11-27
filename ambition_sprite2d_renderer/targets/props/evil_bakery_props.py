"""Crumb's bakery inside (`evil_crumbs_bakery`, the Evil dimension), in
Lower Godwin: two ovens for two breads, and behind the flour, the press.

Use the room dimensions in `evil_moor/make_specs.py`.

- `bakery_room`: whitewash and timber; the door out; the castle's oven
  (black iron, the crest on its door, its loaves black and stamped) and the
  hamlet's (brick, glowing, its loaves round and soft); shelves of both;
  the counter; flour sacks stacked high, and behind them a printing press,
  a line of wet sheets pegged up to dry, a stack of the Lower Godwin
  Gazette.

Animations: ``idle``, 1 frame. No drop shadows.
"""

from __future__ import annotations

from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .evil_forest_props import PAL

W, FLOOR, CEIL = 1024, 384, 32
WHITEWASH = (214, 204, 186)
TIMBER = (60, 44, 34)
BRICK = (150, 76, 56)
IRON = (40, 38, 42)
CREST = (150, 30, 30)
FIRE = (255, 150, 60)
LOAF = (196, 140, 80)
BLACK_LOAF = (52, 44, 40)
SACK = (200, 186, 150)
PAPER = (230, 222, 200)
INK = (30, 28, 30)
BEAM = (91, 58, 41)
EDGE = (185, 122, 74)


def board(c, x0, x1, y0, y1):
    c.put(c.mask(box(x0, y0, x1, y1)), BEAM)
    c.put(c.mask(box(x0 + 3, y0 + 3, x1 - 3, y1 - 3)), TIMBER)


def shelf(c, x0, x1, y, legs):
    for x in legs:
        c.put(c.mask(lambda p: p.poly([(x - 4, y + 14), (x + 14, y + 14), (x + 3, y + 35), (x - 4, y + 35)])), TIMBER)
    c.put(c.mask(box(x0, y, x1, y + 16)), BEAM)
    c.put(c.mask(box(x0, y, x1, y + 4)), EDGE)
    c.put(c.mask(lambda p: [p.ellipse(x, y + 9, 1.3) for x in range(x0 + 9, x1, 26)]), TIMBER)


def room(c, k):
    rng = c.rand("bakery")
    wall = c.mask(box(16, CEIL, W - 16, FLOOR))
    c.put(wall, WHITEWASH)
    c.tone(wall * (c.noise("bakery_wash", 20, 8, 2) - 0.5), 0.1)
    c.put(c.mask(box(16, CEIL, W - 16, CEIL + 14)), TIMBER)
    c.put(c.mask(lambda p: [p.rect(x, CEIL, x + 10, FLOOR) for x in (16, 400, 700, W - 26)]), TIMBER)
    c.put(c.mask(box(16, FLOOR - 20, W - 16, FLOOR)), mix(WHITEWASH, TIMBER, 0.4))
    c.put(c.mask(box(704, 46, 998, FLOOR)), (163, 139, 120))
    c.put(c.mask(lambda p: (p.rect(720, 178, 991, FLOOR), p.ellipse(855.5, 178, 135.5, 64))), (96, 71, 58))
    c.put(c.mask(box(720, 178, 728, FLOOR)), BEAM)
    c.put(c.mask(box(983, 178, 991, FLOOR)), BEAM)
    # The door out (the room's door zone, x 40..88).
    c.put(c.mask(box(34, FLOOR - 104, 94, FLOOR)), TIMBER)
    c.put(c.mask(box(40, FLOOR - 96, 88, FLOOR)), (90, 64, 44))
    c.put(c.mask(lambda p: p.ellipse(80, FLOOR - 50, 2.4)), (190, 160, 90))
    # The castle's oven: black iron, the crest, its loaves black and stamped.
    o0, o1 = 130, 250
    c.put(c.mask(box(o0, FLOOR - 120, o1, FLOOR)), IRON)
    c.put(c.mask(lambda p: p.rect(o0 + 20, FLOOR - 90, o1 - 20, FLOOR - 40)), scale(IRON, 0.6))
    c.put(c.mask(lambda p: p.poly([(190, FLOOR - 84), (204, FLOOR - 78), (200, FLOOR - 56), (190, FLOOR - 48), (180, FLOOR - 56), (176, FLOOR - 78)])), CREST)
    c.put(c.mask(lambda p: p.rect(o0 + 40, FLOOR - 150, o0 + 60, FLOOR - 120)), IRON)
    c.put(c.mask(box(173, 46, 187, 234)), scale(IRON, 1.18))
    # The hamlet's oven: brick, its mouth glowing.
    h0, h1 = 260, 390
    oven = c.mask(lambda p: (p.rect(h0, FLOOR - 100, h1, FLOOR), p.ellipse((h0 + h1) / 2, FLOOR - 100, (h1 - h0) / 2, 30)))
    c.put(oven, BRICK)
    c.put(oven * c.mask(lambda p: [p.rect(h0, y, h1, y + 1.4) for y in range(FLOOR - 120, FLOOR, 10)]), scale(BRICK, 0.7))
    mouth = c.mask(lambda p: (p.rect(h0 + 34, FLOOR - 56, h1 - 34, FLOOR - 20), p.ellipse((h0 + h1) / 2, FLOOR - 56, (h1 - h0) / 2 - 34, 12)))
    c.put(mouth, (60, 20, 10))
    c.put(c.mask(lambda p: [p.poly([(x - 6, FLOOR - 22), (x, FLOOR - 40 - rng.uniform(0, 8)), (x + 6, FLOOR - 22)]) for x in range(h0 + 44, h1 - 40, 10)]), FIRE)
    c.light(c.mask(lambda p: p.ellipse((h0 + h1) / 2, FLOOR - 40, 70, 40), blur=14), FIRE, 0.4)
    c.put(c.mask(box(310, 46, 336, 253)), scale(BRICK, 0.65))
    c.put(c.mask(lambda p: [p.rect(310, y, 336, y + 1.5) for y in range(61, 253, 14)]), scale(BRICK, 0.48))
    # Shelves of both breads, the counter.
    for y in (120, 170):
        c.put(c.mask(lambda p: p.rect(430, y, 680, y + 6)), TIMBER)
    c.put(c.mask(lambda p: [p.rect(x, 104, x + 22, 120) for x in range(440, 540, 26)]), BLACK_LOAF)
    c.put(c.mask(lambda p: [p.rect(x + 4, 110, x + 18, 113) for x in range(440, 540, 26)]), CREST)
    c.put(c.mask(lambda p: [p.ellipse(x, 160, 14, 10) for x in range(570, 680, 28)]), LOAF)
    c.put(c.mask(lambda p: [p.ellipse(x, 160, 14, 10) for x in range(450, 560, 28)]), LOAF)
    c.put(c.mask(lambda p: [p.line([(x - 6, 156), (x + 6, 154)], 1) for x in range(450, 680, 28)]), scale(LOAF, 0.7))
    c.put(c.mask(box(436, 344, 668, FLOOR)), TIMBER)
    c.put(c.mask(lambda p: [p.ellipse(x, 330, 14, 8) for x in (470, 520)]), LOAF)
    board(c, 448, 648, 73, 102)
    board(c, 448, 648, 121, 150)
    c.put(c.mask(lambda p: [p.rect(x, 333, x + 6, FLOOR) for x in (103, 165)]), TIMBER)
    shelf(c, 96, 176, 320, ())
    shelf(c, 192, 400, 256, (217, 378))
    shelf(c, 416, 688, 240, (436, 530, 667))
    shelf(c, 432, 672, 336, ())
    px0, px1 = 860, 980
    c.put(c.mask(lambda p: (p.rect(px0, FLOOR - 70, px1, FLOOR - 60), [p.rect(x, FLOOR - 60, x + 8, FLOOR) for x in (px0 + 4, px1 - 12)],
                            p.rect(px0 + 50, FLOOR - 150, px0 + 62, FLOOR - 70), p.rect(px0 + 20, FLOOR - 154, px1 - 20, FLOOR - 144),
                            p.line([(px0 + 56, FLOOR - 120), (px1 + 6, FLOOR - 128)], 3))), IRON)
    c.put(c.mask(box(px0 + 10, FLOOR - 78, px1 - 10, FLOOR - 70)), PAPER)
    # The Gazette drying on a line, and stacked.
    c.put(c.mask(lambda p: p.line([(752, 94), (988, 101)], 1)), TIMBER)
    for x in range(771, 984, 46):
        c.put(c.mask(box(x, 100, x + 30, 137)), PAPER)
        c.put(c.mask(lambda p: (p.rect(x + 3, 104, x + 27, 109), [p.rect(x + 3, y, x + 27, y + 1) for y in range(112, 134, 4)])), INK, 0.7)
        c.put(c.mask(lambda p: p.rect(x + 13, 95, x + 17, 103)), TIMBER)
    board(c, 746, 982, 141, 176)
    c.put(c.mask(lambda p: (p.rect(966, 185, 978, 204), p.ellipse(972, 183, 4, 6))), (255, 194, 100))
    c.light(c.mask(lambda p: p.ellipse(969, 211, 55, 73), blur=16), (255, 190, 110), 0.25)
    c.put(c.mask(lambda p: [p.rect(870, y, 920, y + 3) for y in range(FLOOR - 96, FLOOR - 72, 4)]), PAPER)
    for x, y in ((731, FLOOR), (770, FLOOR), (810, FLOOR), (849, FLOOR),
                 (751, 352), (790, 352), (838, 352), (765, 320)):
        c.put(c.mask(lambda p: (p.ellipse(x, y - 17, 22, 17), p.rect(x - 22, y - 17, x + 22, y))), SACK)
        c.put(c.mask(box(x - 8, y - 22, x + 8, y - 14)), (120, 100, 80))
    shelf(c, 704, 800, 304, (718, 777))
    shelf(c, 832, 912, 352, (845, 887))


PIECES: Dict[str, Piece] = {
    "bakery_room": Piece((16, CEIL, W - 16, FLOOR), room),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
