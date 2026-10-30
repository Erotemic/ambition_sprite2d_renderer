"""The Fibonacci Meadow (`math_fibonacci_meadow`, the Math dimension): out of
town, east of the Fractal Woods: a farm where everything grows by the sum of
the last two.

Drawn in room coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/math_town/make_specs.py` (`fibonacci_meadow`):
the ground (y 704); the squares (SQUARES, their tops walked on) and the
ledge up to the last (y 496).

- `meadow_farm`: Farmer Fibbs's cottage and its fence, his counting board of
  rabbits (1, 1, 2, 3, 5, 8, and a 13 chalked over the edge).
- `meadow_squares`: garden plots in squares of 1, 1, 2, 3, 5 and 8, each
  framed in boards, a quarter of the golden spiral drawn across each: the
  spiral, unrolled.
- `meadow_field`: sunflowers, their seeds set at the golden angle; the
  hutch of compartments with 1, 1, 2, 3 and 5 rabbits in them and the sixth
  with its door burst open.

Animations: ``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .math_town_terraces import PAL

W, FLOOR = 2400, 704
#: The squares: (x0, side). Their tops are walked on.
SQUARES = ((900, 32), (932, 32), (964, 64), (1028, 96), (1124, 160), (1284, 256))
GOLDEN = math.pi * (3 - math.sqrt(5))
BOARD = (150, 112, 70)
BOARD_DARK = (104, 76, 46)
SOIL = (110, 82, 58)
GREEN = (96, 150, 80)
GREEN_DARK = (66, 112, 60)
GOLD = (236, 190, 60)
SPIRAL = (200, 80, 60)
PLASTER = (236, 226, 200)
ROOF = (168, 84, 58)
SEED = (90, 60, 34)
PETAL = (246, 196, 40)
FUR = (244, 240, 232)
EAR = (236, 180, 180)
SLATE = (46, 52, 50)
CHALK = (236, 236, 228)


def rabbit(c, x, y, s=1.0):
    """A rabbit sitting, facing right."""
    c.put(c.mask(lambda p: (p.ellipse(x, y, 9 * s, 7 * s), p.ellipse(x + 8 * s, y - 6 * s, 5 * s))), FUR)
    c.put(c.mask(lambda p: [p.ellipse(x + 6 * s + dx, y - 15 * s, 1.8 * s, 6 * s) for dx in (0, 4 * s)]), FUR)
    c.put(c.mask(lambda p: [p.ellipse(x + 6 * s + dx, y - 15 * s, 0.8 * s, 4 * s) for dx in (0, 4 * s)]), EAR)
    c.put(c.mask(lambda p: p.ellipse(x + 10 * s, y - 7 * s, 1.1 * s)), (30, 30, 30))
    c.put(c.mask(lambda p: p.ellipse(x - 9 * s, y - 2 * s, 3 * s)), FUR)


def farm(c, k):
    # The cottage: plaster, a red roof, a green door, a window.
    x0, x1, top = 120, 420, 520
    c.put(c.mask(box(x0, top, x1, FLOOR)), PLASTER)
    c.put(c.mask(lambda p: p.poly([(x0 - 20, top + 4), ((x0 + x1) / 2, top - 90), (x1 + 20, top + 4)])), ROOF)
    c.put(c.mask(lambda p: [p.line([(x, top + 4), ((x0 + x1) / 2, top - 90)], 1) for x in range(x0 - 10, x1 + 20, 22)]), scale(ROOF, 0.75))
    c.put(c.mask(box(300, FLOOR - 96, 352, FLOOR)), GREEN_DARK)
    c.put(c.mask(lambda p: p.ellipse(342, FLOOR - 48, 2.4)), GOLD)
    c.put(c.mask(box(160, 570, 240, 630)), (130, 170, 200))
    c.put(c.mask(lambda p: (p.rect(198, 570, 202, 630), p.rect(160, 598, 240, 602))), PLASTER)
    # The fence along the farm.
    c.put(c.mask(lambda p: [p.rect(x, FLOOR - 44, x + 6, FLOOR) for x in range(440, 860, 40)]), BOARD)
    c.put(c.mask(lambda p: [p.rect(440, y, 860, y + 5) for y in (FLOOR - 36, FLOOR - 18)]), BOARD)
    # The counting board: rows of rabbits by the month.
    bx0, by0, bx1, by1 = 470, 470, 720, 620
    c.put(c.mask(box(bx0 - 6, by0 - 6, bx1 + 6, by1 + 6)), BOARD_DARK)
    c.put(c.mask(box(bx0, by0, bx1, by1)), SLATE)
    c.put(c.mask(lambda p: [p.rect(x, by1, x + 6, FLOOR) for x in (bx0 + 20, bx1 - 26)]), BOARD_DARK)
    for row, n in enumerate((1, 1, 2, 3, 5, 8)):
        y = by0 + 14 + row * 22
        c.put(c.mask(lambda p: [p.ellipse(bx0 + 14 + i * 22, y, 6, 5) for i in range(n)]), CHALK)
        c.put(c.mask(lambda p: [p.line([(bx0 + 16 + i * 22, y - 4), (bx0 + 18 + i * 22, y - 12)], 1.2) for i in range(n)]), CHALK)
    # A thirteenth, chalked over the edge onto the post.
    c.put(c.mask(lambda p: p.ellipse(bx1 + 4, by1 + 8, 6, 5)), CHALK)


def squares(c, k):
    for i, (x0, s) in enumerate(SQUARES):
        top = FLOOR - s
        plot = c.mask(box(x0, top, x0 + s, FLOOR))
        c.put(plot, SOIL)
        c.tone(plot * (c.noise(("plot", i), max(2, s / 12), max(2, s / 12), 2) - 0.5), 0.15)
        # Rows of greens, as many as the square is wide in eights.
        step = max(8.0, s / 8)
        c.put(plot * c.mask(lambda p: [p.ellipse(x, y, step * 0.32, step * 0.26) for y in np.arange(top + step, FLOOR - 2, step)
                                       for x in np.arange(x0 + step * 0.6, x0 + s - 2, step * 0.8)]), GREEN)
        c.put(plot * c.mask(lambda p: [p.ellipse(x, y - step * 0.08, step * 0.14) for y in np.arange(top + step, FLOOR - 2, step)
                                       for x in np.arange(x0 + step * 0.6, x0 + s - 2, step * 0.8)]), GREEN_DARK)
        # The frame of boards, its top walked on.
        c.put(plot * (1 - c.mask(box(x0 + 4, top + 6, x0 + s - 4, FLOOR))), BOARD)
        c.put(c.mask(box(x0, top, x0 + s, top + 3)), mix(BOARD, (255, 255, 255), 0.25))
        # A quarter of the golden spiral across it.
        cx, cy = x0 + s, FLOOR
        arc = [(cx - s * math.cos(t), cy - s * math.sin(t)) for t in np.linspace(0, math.pi / 2, 24)]
        c.put(plot * c.mask(lambda p: p.line(arc, max(1.6, s * 0.03))), SPIRAL)
    # The ledge up to the last square (the art of a ladder of crates).
    c.put(c.mask(box(1222, 496, 1282, 504)), BOARD)
    c.put(c.mask(lambda p: (p.rect(1226, 504, 1232, 544), p.rect(1272, 504, 1278, 544))), BOARD_DARK)


def sunflower(c, x, height, r, tag):
    head_y = FLOOR - height
    c.put(c.mask(lambda p: p.line([(x, FLOOR), (x - 4, FLOOR - height * 0.5), (x, head_y)], max(2, r * 0.12))), GREEN_DARK)
    for side in (-1, 1):
        ly = FLOOR - height * (0.35 if side < 0 else 0.55)
        c.put(c.mask(lambda p: p.poly([(x, ly), (x + side * r * 0.9, ly - r * 0.3), (x + side * r * 1.2, ly - r * 0.05), (x + side * r * 0.4, ly + r * 0.2)])), GREEN)
    c.put(c.mask(lambda p: [p.ellipse(x + r * 1.15 * math.cos(a), head_y + r * 1.15 * math.sin(a), r * 0.36, r * 0.36) for a in np.linspace(0, 2 * math.pi, 16, endpoint=False)]), PETAL)
    c.put(c.mask(lambda p: p.ellipse(x, head_y, r)), SEED)
    # The seeds at the golden angle.
    n = int(r * r * 0.9)
    c.put(c.mask(lambda p: [p.ellipse(x + r * 0.95 * math.sqrt(j / n) * math.cos(j * GOLDEN), head_y + r * 0.95 * math.sqrt(j / n) * math.sin(j * GOLDEN), max(0.7, r * 0.05))
                            for j in range(1, n)]), (200, 150, 60))


def field(c, k):
    rng = c.rand("meadow_field")
    for i, (x, h, r) in enumerate(((1620, 200, 16), (1700, 260, 20), (1780, 170, 14), (2180, 230, 18), (2260, 290, 22), (2330, 190, 15))):
        sunflower(c, x, h, r, i)
    # The hutch: six compartments; 1, 1, 2, 3, 5 rabbits, and the sixth
    # burst open, rabbits leaving it.
    hx0, hy0, cw, ch = 1860, 560, 48, 48
    c.put(c.mask(box(hx0 - 6, hy0 - 20, hx0 + 3 * cw + 6, hy0 + 2 * ch + 4)), BOARD_DARK)
    c.put(c.mask(lambda p: p.poly([(hx0 - 14, hy0 - 18), (hx0 + 1.5 * cw, hy0 - 44), (hx0 + 3 * cw + 14, hy0 - 18)])), ROOF)
    c.put(c.mask(lambda p: [p.rect(x, hy0 + 2 * ch + 4, x + 6, FLOOR) for x in (hx0, hx0 + 3 * cw - 6)]), BOARD_DARK)
    for j, n in enumerate((1, 1, 2, 3, 5, None)):
        col, row = j % 3, j // 3
        x0, y0 = hx0 + col * cw + 3, hy0 + row * ch + 3
        c.put(c.mask(box(x0, y0, x0 + cw - 6, y0 + ch - 6)), (60, 46, 34))
        c.put(c.mask(lambda p: p.rect(x0 + 2, y0 + ch - 14, x0 + cw - 8, y0 + ch - 6)), (206, 178, 100))
        if n is None:
            c.put(c.mask(lambda p: p.poly([(x0 + cw - 6, y0), (x0 + cw + 10, y0 + 6), (x0 + cw + 10, y0 + ch - 2), (x0 + cw - 6, y0 + ch - 6)])), BOARD)
            continue
        for i in range(n):
            s = 0.7 if n > 2 else 0.85
            rabbit(c, x0 + 10 + (i % 3) * 12, y0 + ch - 14 - (i // 3) * 12, s)
        c.put(c.mask(lambda p: [p.rect(x, y0, x + 1.4, y0 + ch - 6) for x in np.arange(x0 + 6, x0 + cw - 6, 7)]), (150, 150, 156), 0.8)
    # The eight from the burst compartment, off across the field.
    for i in range(8):
        rabbit(c, 2010 + i * 24 + rng.uniform(-4, 4), FLOOR - 6 - (i % 2) * 3, 0.8)


PIECES: Dict[str, Piece] = {
    "meadow_farm": Piece((90, 420, 880, FLOOR), farm),
    "meadow_squares": Piece((890, 440, 1550, FLOOR), squares),
    "meadow_field": Piece((1590, 380, W - 40, FLOOR), field),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
