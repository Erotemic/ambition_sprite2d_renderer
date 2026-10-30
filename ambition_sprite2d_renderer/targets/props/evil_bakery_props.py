"""Crumb's bakery inside (`evil_crumbs_bakery`, the Evil dimension), in
Lower Godwin: two ovens for two breads, and behind the flour, the press.

Drawn in room coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/evil_moor/make_specs.py` (`bakery`): the
floor (y 384), the ceiling (to y 32), the door out (x 40).

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


def room(c, k):
    rng = c.rand("bakery")
    wall = c.mask(box(16, CEIL, W - 16, FLOOR))
    c.put(wall, WHITEWASH)
    c.tone(wall * (c.noise("bakery_wash", 20, 8, 2) - 0.5), 0.1)
    c.put(c.mask(box(16, CEIL, W - 16, CEIL + 14)), TIMBER)
    c.put(c.mask(lambda p: [p.rect(x, CEIL, x + 10, FLOOR) for x in (16, 400, 700, W - 26)]), TIMBER)
    c.put(c.mask(box(16, FLOOR - 20, W - 16, FLOOR)), mix(WHITEWASH, TIMBER, 0.4))
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
    # The hamlet's oven: brick, its mouth glowing.
    h0, h1 = 260, 390
    oven = c.mask(lambda p: (p.rect(h0, FLOOR - 100, h1, FLOOR), p.ellipse((h0 + h1) / 2, FLOOR - 100, (h1 - h0) / 2, 30)))
    c.put(oven, BRICK)
    c.put(oven * c.mask(lambda p: [p.rect(h0, y, h1, y + 1.4) for y in range(FLOOR - 120, FLOOR, 10)]), scale(BRICK, 0.7))
    mouth = c.mask(lambda p: (p.rect(h0 + 34, FLOOR - 56, h1 - 34, FLOOR - 20), p.ellipse((h0 + h1) / 2, FLOOR - 56, (h1 - h0) / 2 - 34, 12)))
    c.put(mouth, (60, 20, 10))
    c.put(c.mask(lambda p: [p.poly([(x - 6, FLOOR - 22), (x, FLOOR - 40 - rng.uniform(0, 8)), (x + 6, FLOOR - 22)]) for x in range(h0 + 44, h1 - 40, 10)]), FIRE)
    c.light(c.mask(lambda p: p.ellipse((h0 + h1) / 2, FLOOR - 40, 70, 40), blur=14), FIRE, 0.4)
    # Shelves of both breads, the counter.
    for y in (120, 170):
        c.put(c.mask(lambda p: p.rect(430, y, 680, y + 6)), TIMBER)
    c.put(c.mask(lambda p: [p.rect(x, 104, x + 22, 120) for x in range(440, 540, 26)]), BLACK_LOAF)
    c.put(c.mask(lambda p: [p.rect(x + 4, 110, x + 18, 113) for x in range(440, 540, 26)]), CREST)
    c.put(c.mask(lambda p: [p.ellipse(x, 160, 14, 10) for x in range(570, 680, 28)]), LOAF)
    c.put(c.mask(lambda p: [p.ellipse(x, 160, 14, 10) for x in range(450, 560, 28)]), LOAF)
    c.put(c.mask(lambda p: [p.line([(x - 6, 156), (x + 6, 154)], 1) for x in range(450, 680, 28)]), scale(LOAF, 0.7))
    c.put(c.mask(box(430, FLOOR - 50, 680, FLOOR)), TIMBER)
    c.put(c.mask(box(426, FLOOR - 54, 684, FLOOR - 48)), mix(TIMBER, (200, 160, 110), 0.4))
    c.put(c.mask(lambda p: [p.ellipse(x, FLOOR - 62, 14, 9) for x in (470, 520)]), LOAF)
    # The flour sacks stacked high, and behind them, the press.
    for i, (x, y) in enumerate(((730, FLOOR), (770, FLOOR), (810, FLOOR), (750, FLOOR - 34), (790, FLOOR - 34), (770, FLOOR - 68))):
        c.put(c.mask(lambda p: (p.ellipse(x, y - 17, 22, 17), p.rect(x - 22, y - 17, x + 22, y))), SACK)
        c.put(c.mask(lambda p: p.rect(x - 8, y - 22, x + 8, y - 14)), (120, 100, 80))
    px0, px1 = 860, 980
    c.put(c.mask(lambda p: (p.rect(px0, FLOOR - 70, px1, FLOOR - 60), [p.rect(x, FLOOR - 60, x + 8, FLOOR) for x in (px0 + 4, px1 - 12)],
                            p.rect(px0 + 50, FLOOR - 150, px0 + 62, FLOOR - 70), p.rect(px0 + 20, FLOOR - 154, px1 - 20, FLOOR - 144),
                            p.line([(px0 + 56, FLOOR - 120), (px1 + 6, FLOOR - 128)], 3))), IRON)
    c.put(c.mask(box(px0 + 10, FLOOR - 78, px1 - 10, FLOOR - 70)), PAPER)
    # The Gazette drying on a line, and stacked.
    c.put(c.mask(lambda p: p.line([(720, 70), (1000, 76)], 1)), TIMBER)
    for x in range(730, 1000, 44):
        c.put(c.mask(box(x, 72, x + 34, 112)), PAPER)
        c.put(c.mask(lambda p: (p.rect(x + 3, 76, x + 31, 82), [p.rect(x + 3, y, x + 31, y + 1) for y in range(86, 110, 4)])), INK, 0.7)
        c.put(c.mask(lambda p: p.rect(x + 15, 68, x + 19, 76)), TIMBER)
    c.put(c.mask(lambda p: [p.rect(870, y, 920, y + 3) for y in range(FLOOR - 96, FLOOR - 72, 4)]), PAPER)


PIECES: Dict[str, Piece] = {
    "bakery_room": Piece((16, CEIL, W - 16, FLOOR), room),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
