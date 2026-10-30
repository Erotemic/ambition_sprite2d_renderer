"""The rest of GNU-ton's gravity works (the Science dimension): a thing in
each hall that says what the hall is about.

Drawn in room coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/gnu_ton_gravity/make_specs.py`:

- `hall_cradle` (`gnu_ton_conservation_hall`: vault y 48, floor y 896, the
  west bay x 96..352): a Newton's cradle the height of the hall, hung from
  the vault, its first ball drawn back. What goes in comes out.
- `hall_lectern` (the hall's east floor, x 1568 on, y 896): a lectern with
  the PRINCIPIA open on it, and a quill.
- `gallery_chandelier_hung`, `gallery_chandelier_stood`
  (`gnu_ton_inversion_gallery`: its thick vault's underside y 160, floor y
  896, x 400..560 between its lever and its chasm): one chandelier hung from
  the ceiling and its twin standing on the floor, so whichever way the
  gallery is turned, it is right.

Animations: ``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

import math
from typing import Dict

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .orbital_station import AMBER, HULL, HULL_LIGHT, INK, STEEL, STEEL_DARK, STEEL_LIGHT

HALL_VAULT, HALL_FLOOR = 48, 896
CRADLE = (180, 340)
LECTERN_X = 1720
GALLERY_CEILING, GALLERY_FLOOR = 160, 896
CHANDELIER_X = 480
PAL = {"stone": HULL, "stone_light": HULL_LIGHT, "dark": STEEL_DARK, "lamp": AMBER}

BRASS = (204, 164, 82)
BRASS_DARK = (150, 112, 50)
BRASS_LIGHT = (250, 220, 150)
WOOD = (122, 80, 50)
WOOD_DARK = (84, 54, 34)
PAPER = (240, 230, 204)
CANDLE = (246, 238, 214)
FLAME = (255, 196, 90)


def ball(c, x, y, r):
    c.put(c.mask(lambda p: p.ellipse(x, y, r)), STEEL_LIGHT)
    c.put(c.mask(lambda p: p.ellipse(x + r * 0.3, y + r * 0.3, r * 0.8)), STEEL, 0.55)
    c.put(c.mask(lambda p: p.ellipse(x - r * 0.4, y - r * 0.4, r * 0.28)), (255, 255, 255), 0.85)


def cradle(c, k):
    x0, x1 = CRADLE
    bar_y = HALL_VAULT + 120
    # The frame: two hangers from the vault, a top bar.
    for x in (x0 + 6, x1 - 6):
        c.put(c.mask(box(x - 3, HALL_VAULT, x + 3, bar_y)), STEEL_DARK)
    c.put(c.mask(box(x0, bar_y - 6, x1, bar_y + 6)), BRASS)
    c.put(c.mask(box(x0, bar_y - 6, x1, bar_y - 3)), BRASS_LIGHT)
    r = 20.0
    pitch = 2 * r + 1
    cx = (x0 + x1) / 2
    xs = [cx + (i - 2) * pitch for i in range(5)]
    hang = 420
    for i, x in enumerate(xs):
        if i == 0:
            # Drawn back, ready to let go.
            a = math.radians(-16)
            bx, by = x + math.sin(a) * hang, bar_y + math.cos(a) * hang
        else:
            bx, by = x, bar_y + hang
        c.put(c.mask(lambda p: p.line([(x - 8, bar_y + 6), (bx, by - r)], 1.4)), STEEL_LIGHT, 0.75)
        c.put(c.mask(lambda p: p.line([(x + 8, bar_y + 6), (bx, by - r)], 1.4)), STEEL_LIGHT, 0.75)
        ball(c, bx, by, r)


def lectern(c, k):
    x, f = LECTERN_X, HALL_FLOOR
    c.put(c.mask(lambda p: p.poly([(x - 30, f), (x + 30, f), (x + 18, f - 8), (x - 18, f - 8)])), WOOD_DARK)
    c.put(c.mask(box(x - 7, f - 96, x + 7, f - 8)), WOOD)
    c.put(c.mask(box(x + 3, f - 96, x + 7, f - 8)), WOOD_DARK)
    top = [(x - 44, f - 112), (x + 44, f - 126), (x + 44, f - 114), (x - 44, f - 100)]
    c.put(c.mask(lambda p: p.poly(top)), WOOD)
    # The book, open: two pages, lines of writing, a diagram of an orbit.
    left = [(x - 40, f - 114), (x - 2, f - 122), (x - 2, f - 140), (x - 40, f - 130)]
    right = [(x + 2, f - 122), (x + 40, f - 130), (x + 40, f - 146), (x + 2, f - 140)]
    c.put(c.mask(lambda p: (p.poly(left), p.poly(right))), PAPER)
    c.put(c.mask(lambda p: [p.line([(x - 36, f - 128 + d * 0.2 - d), (x - 6, f - 135 + d * 0.2 - d)], 0.8) for d in (0, -4, -8)]), INK, 0.6)
    c.put(c.mask(lambda p: p.ring(x + 21, f - 134, 6, 0.9)), INK, 0.7)
    c.put(c.mask(lambda p: p.ellipse(x + 21, f - 134, 1.6)), AMBER)
    # The quill, in its pot.
    c.put(c.mask(box(x + 26, f - 126, x + 34, f - 118)), INK)
    c.put(c.mask(lambda p: p.poly([(x + 30, f - 124), (x + 46, f - 168), (x + 40, f - 166), (x + 29, f - 126)])), PAPER)


def chandelier(c, x, anchor, hanging):
    """A brass chandelier of five candles; `anchor` is the ceiling (hanging)
    or the floor (standing), and its candles burn away from it."""
    s = 1 if hanging else -1
    stem_end = anchor + s * 46
    c.put(c.mask(box(x - 2, min(anchor, stem_end), x + 2, max(anchor, stem_end))), BRASS_DARK)
    ring_y = stem_end + s * 10
    c.put(c.mask(lambda p: p.ellipse(x, ring_y, 46, 7)), BRASS)
    c.put(c.mask(lambda p: p.ellipse(x, ring_y - 2, 46, 4)), BRASS_LIGHT, 0.6)
    c.put(c.mask(lambda p: p.ellipse(x, stem_end, 7, 5)), BRASS)
    for dx in (-40, -20, 0, 20, 40):
        # The stood one is the hung one turned over: its candles point down.
        tip = ring_y - 26 if hanging else ring_y + 26
        c.put(c.mask(box(x + dx - 3, min(ring_y, tip), x + dx + 3, max(ring_y, tip))), CANDLE)
        fy = tip - 6 if hanging else tip + 6
        c.put(c.mask(lambda p: p.ellipse(x + dx, fy, 3, 5)), FLAME)
        c.light(c.mask(lambda p: p.ellipse(x + dx, fy, 10, 10), blur=4), FLAME, 0.3)


def hung(c, k):
    chandelier(c, CHANDELIER_X, GALLERY_CEILING, True)


def stood(c, k):
    chandelier(c, CHANDELIER_X, GALLERY_FLOOR, False)


PIECES: Dict[str, Piece] = {
    "hall_cradle": Piece((CRADLE[0] - 140, HALL_VAULT, CRADLE[1] + 40, HALL_VAULT + 620), cradle),
    "hall_lectern": Piece((LECTERN_X - 56, HALL_FLOOR - 180, LECTERN_X + 56, HALL_FLOOR), lectern),
    "gallery_chandelier_hung": Piece((CHANDELIER_X - 56, GALLERY_CEILING, CHANDELIER_X + 56, GALLERY_CEILING + 100), hung),
    "gallery_chandelier_stood": Piece((CHANDELIER_X - 56, GALLERY_FLOOR - 100, CHANDELIER_X + 56, GALLERY_FLOOR), stood),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
