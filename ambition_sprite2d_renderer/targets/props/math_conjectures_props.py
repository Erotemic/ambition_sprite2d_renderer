"""The conjectures (`math_conjectures`, the math dimension): behind a cracked
wall at the west end of the Fractal Woods' roots, a cellar whose walls are
chalked over with the problems nobody has solved. PROOF LEFT AS AN EXERCISE.

Drawn in room coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/math_town/make_specs.py` (`fractal_roots`,
`conjectures`): the roots' floor (y 576) and the cracked wall over their way
west (x 16..48, 112 high); the cellar's floor (y 576), its roof (to y 64).

- `roots_cracked_wall`: earth and roots over the way west, cracked, chalk
  dust in the crack (the look of a breakable wall: hit it).
- `conjectures_room`: blackboard walls: the zeta function's zeros all on
  one line (and a question mark); the Collatz arrows, 27 going up and up
  and coming down; twin primes paired off to the edge of the board; an even
  number written as two primes, again and again; a desk, a stool, a candle
  burned to nothing, a waste basket full.

Animations: ``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .math_roots_props import EARTH, EARTH_DARK, ROOT, ROOT_DARK
from .math_town_terraces import PAL

FLOOR, ROOF = 576, 64
CRACK = (16, 48, FLOOR - 112)
W = 592
BOARD = (40, 56, 50)
BOARD_EDGE = (110, 80, 50)
CHALK = (232, 236, 228)
CHALK_RED = (236, 140, 130)
WOOD = (130, 92, 58)
PAPER = (236, 228, 204)


def cracked_wall(c, k):
    x0, x1, y0 = CRACK
    m = c.mask(box(x0, y0, x1, FLOOR))
    c.put(m, EARTH)
    c.put(m * (c.noise("roots_crack", 3, 8, 2) > 0.55), EARTH_DARK)
    c.put(c.mask(lambda p: p.line([(x0 + 4, y0 + 10), (x1 - 4, y0 + 40), (x0 + 8, y0 + 80)], 4)), ROOT_DARK)
    c.put(c.mask(lambda p: p.line([(x0 + 4, y0 + 10), (x1 - 4, y0 + 40), (x0 + 8, y0 + 80)], 2.4)), ROOT)
    c.put(c.mask(lambda p: p.line([(x0 + 18, y0), (x0 + 10, y0 + 36), (x0 + 22, y0 + 64), (x0 + 12, y0 + 92), (x0 + 18, FLOOR)], 2)), (24, 18, 14))
    c.put(c.mask(lambda p: [p.ellipse(x0 + 16 + (i % 3) * 3, FLOOR - 4 - i * 2, 2, 1) for i in range(6)]), CHALK, 0.7)


def scrawl(c, x, y, n, w=8, h=10, gap=4, colour=CHALK):
    """`n` chalk marks in a row: a line of working."""
    c.put(c.mask(lambda p: [p.rect(x + i * (w + gap), y, x + i * (w + gap) + w * (0.5 + 0.5 * ((i * 7) % 3) / 2), y + h) for i in range(n)]), colour)


def room(c, k):
    wall = c.mask(box(16, ROOF, W - 16, FLOOR))
    c.put(wall, BOARD)
    c.tone(wall * (c.noise("conj_board", 8, 5, 3) - 0.5), 0.15)
    c.put(wall * (c.noise("conj_dust", 30, 14, 2) > 0.66), CHALK, 0.08)
    c.put(c.mask(box(16, 16, W - 16, ROOF)), EARTH_DARK)
    c.put(c.mask(lambda p: [p.rect(x, ROOF, x + 6, FLOOR) for x in (180, 400)]), BOARD_EDGE)
    # The zeros on one line, and a question mark.
    c.put(c.mask(lambda p: p.line([(100, 90), (100, 300)], 1.4)), CHALK)
    c.put(c.mask(lambda p: [p.ellipse(100, y, 4, 4) for y in (120, 150, 172, 200, 214, 236, 252, 270, 284)]), CHALK)
    c.put(c.mask(lambda p: [p.ellipse(x, y, 3) for x, y in ((60, 180), (140, 230))]), CHALK_RED)
    c.put(c.mask(lambda p: [p.line([(x - 5, y - 5), (x + 5, y + 5)], 1.4) for x, y in ((60, 180), (140, 230))]), CHALK_RED)
    c.put(c.mask(lambda p: (p.ring(150, 110, 10, 2), p.rect(150, 118, 152, 128), p.ellipse(151, 134, 1.6))), CHALK)
    # Collatz: 27, up and up, and down at last.
    pts, n, x = [], 27, 200
    while n != 1 and len(pts) < 112:
        pts.append((x, 300 - min(n, 9232) ** 0.5 * 2.2))
        n = n // 2 if n % 2 == 0 else 3 * n + 1
        x += 1.6
    c.put(c.mask(lambda p: p.line(pts, 1.2)), CHALK)
    scrawl(c, 204, 314, 6, 6, 8, 3)
    # Twin primes, paired off to the edge of the board.
    for i, (a, b) in enumerate(((3, 5), (5, 7), (11, 13), (17, 19), (29, 31), (41, 43), (59, 61), (71, 73))):
        y = 350 + i * 22
        scrawl(c, 200 + (i % 2) * 6, y, 2, 7, 10, 3)
        c.put(c.mask(lambda p: p.ring(214 + (i % 2) * 6, y + 5, 14, 1.2)), CHALK)
        scrawl(c, 240, y, 2, 7, 10, 3)
    c.put(c.mask(lambda p: [p.ellipse(330 + i * 12, 532, 1.6) for i in range(3)]), CHALK)
    # Goldbach: an even number as two primes, again and again.
    for i in range(9):
        y = 100 + i * 26
        scrawl(c, 424, y, 2, 7, 10, 3)
        c.put(c.mask(lambda p: (p.rect(450, y + 4, 460, y + 6), p.rect(450, y + 8, 460, y + 10))), CHALK)
        scrawl(c, 466, y, 1, 7, 10, 3)
        c.put(c.mask(lambda p: (p.rect(484, y + 4, 494, y + 6), p.rect(488, y, 490, y + 10))), CHALK)
        scrawl(c, 500, y, 2 if i % 2 else 1, 7, 10, 3)
    # PROOF LEFT AS AN EXERCISE, underlined.
    scrawl(c, 424, 360, 9, 9, 12, 4, CHALK_RED)
    c.put(c.mask(lambda p: p.line([(424, 378), (536, 378)], 1.4)), CHALK_RED)
    # The desk, the stool, a candle burned to nothing, the waste basket.
    g = FLOOR
    c.put(c.mask(lambda p: (p.rect(420, g - 70, 560, g - 62), p.rect(428, g - 62, 436, g), p.rect(544, g - 62, 552, g))), WOOD)
    c.put(c.mask(lambda p: (p.rect(470, g - 76, 484, g - 70), p.line([(477, g - 76), (479, g - 82)], 1))), (230, 220, 200))
    c.put(c.mask(lambda p: p.poly([(500, g - 70), (540, g - 70), (538, g - 74), (502, g - 74)])), PAPER)
    c.put(c.mask(lambda p: (p.rect(370, g - 36, 400, g - 30), p.rect(374, g - 30, 378, g), p.rect(392, g - 30, 396, g))), WOOD)
    c.put(c.mask(lambda p: p.poly([(60, g), (110, g), (116, g - 50), (54, g - 50)])), (90, 90, 96))
    c.put(c.mask(lambda p: [p.ellipse(64 + i * 10, g - 52 - (i % 3) * 5, 9, 7) for i in range(6)]), PAPER)


PIECES: Dict[str, Piece] = {
    "roots_cracked_wall": Piece((CRACK[0], CRACK[2], CRACK[1], FLOOR), cracked_wall),
    "conjectures_room": Piece((16, 16, W - 16, FLOOR), room),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
