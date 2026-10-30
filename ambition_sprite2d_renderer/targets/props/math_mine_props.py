"""The Möbius Mine (`math_mobius_mine`, the Math dimension): under the
Fractal Woods, down a hole in their floor. A mine with one side: at its far
end the half twist turns the world over, and the way back is the ceiling.

Drawn in room coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/math_town/make_specs.py` (`mobius_mine`):
the floor (y 576), the ceiling's underside (y 64), both walked on; the shaft
down from the woods (x 96..160) and its ladder (x 112..144); the half
twist's switch (x 1480).

- `mine_tunnel`: rock in strata, veins of ore, timber sets every 300 (two
  posts leaning in, a cap and a sill: the same seen either way up), lanterns hung from the caps and stood
  on the floor (one of each, for whichever way is up), the rails along the
  floor that, at the far end, twist up the back wall in a half turn and run
  back along the ceiling; a mine cart on the floor, another on the ceiling;
  the shaft's timbering.

Animations: ``idle``, 1 frame. No drop shadows.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .math_town_terraces import PAL

W, H = 1600, 640
FLOOR, CEIL = 576, 64
SHAFT = (96, 160)
TWIST = (1380, 1560)
ROCK = (86, 76, 70)
ROCK_DARK = (58, 50, 46)
ROCK_LIGHT = (120, 106, 94)
TIMBER = (120, 86, 52)
TIMBER_DARK = (84, 58, 36)
RAIL = (150, 150, 160)
LAMP = (255, 210, 130)


def cart(c, x, y, up):
    """A mine cart on the floor (`up`) or hung on the ceiling."""
    s = 1 if up else -1
    body = c.mask(lambda p: p.poly([(x - 28, y - s * 12), (x + 28, y - s * 12), (x + 34, y - s * 40), (x - 34, y - s * 40)]))
    c.put(body, (110, 96, 80))
    c.put(body * c.mask(lambda p: [p.rect(x - 34, yy, x + 34, yy + 2) for yy in (y - s * 22, y - s * 32)]), (80, 70, 60))
    c.put(c.mask(lambda p: [p.ellipse(x + dx, y - s * 7, 7) for dx in (-18, 18)]), (50, 48, 52))
    c.put(c.mask(lambda p: [p.ellipse(x + dx + rx, y - s * 46 + ry, 7, 5) for dx in (-16, 0, 16) for rx, ry in ((0, 0),)]), (190, 160, 90))


def tunnel(c, k):
    rng = c.rand("mine")
    # Rock in strata, darker at the ends of the face.
    rock = c.mask(box(16, 0, W - 16, H))
    c.put(rock, ROCK)
    c.put(rock * c.mask(lambda p: [p.poly([(16, y), (W - 16, y + rng.uniform(-30, 30)), (W - 16, y + 10), (16, y + 8)]) for y in range(80, FLOOR, 46)]), ROCK_DARK, 0.6)
    c.tone(rock * (c.noise("mine_rock", 14, 8, 3) - 0.5), 0.2)
    c.put(rock * c.mask(lambda p: [p.ellipse(rng.uniform(20, W - 20), rng.uniform(70, FLOOR - 10), rng.uniform(2, 6)) for _ in range(80)]), ROCK_LIGHT, 0.6)
    # The shaft up to the woods: its timbering, an opening of light.
    s0, s1 = SHAFT
    c.put(c.mask(box(s0, 0, s1, CEIL)), (190, 200, 150))
    c.light(c.mask(lambda p: p.poly([(s0, 0), (s1, 0), (s1 + 40, 260), (s0 - 40, 260)]), blur=12), (220, 230, 170), 0.3)
    c.put(c.mask(lambda p: [p.rect(x, 0, x + 6, CEIL + 12) for x in (s0 - 6, s1)]), TIMBER_DARK)
    # Timber sets every 300: two posts leaning in, a cap across their tops,
    # a sill under their feet, the same seen either way up.
    for x in range(330, TWIST[0] - 60, 300):
        c.put(c.mask(lambda p: (p.poly([(x - 70, FLOOR), (x - 54, FLOOR), (x - 44, CEIL), (x - 60, CEIL)]),
                                p.poly([(x + 54, FLOOR), (x + 70, FLOOR), (x + 60, CEIL), (x + 44, CEIL)]))), TIMBER)
        c.put(c.mask(lambda p: (p.line([(x - 70, FLOOR), (x - 60, CEIL)], 3), p.line([(x + 54, FLOOR), (x + 44, CEIL)], 3))), mix(TIMBER, (255, 230, 190), 0.25))
        c.put(c.mask(lambda p: [p.rect(x - 80, y, x + 80, y + 14) for y in (CEIL, FLOOR - 14)]), TIMBER_DARK)
        c.put(c.mask(lambda p: [p.poly([(x + s_ * 44, CEIL + 14), (x + s_ * 44, CEIL + 40), (x + s_ * 20, CEIL + 14)]) for s_ in (-1, 1)]), TIMBER_DARK)
    # Veins of ore in the strata, glinting.
    for _ in range(14):
        vx, vy = rng.uniform(200, TWIST[0] - 40), rng.uniform(CEIL + 60, FLOOR - 60)
        pts = [(vx + i * 14, vy + rng.uniform(-6, 6)) for i in range(6)]
        c.put(c.mask(lambda p: p.line(pts, 2.4)), (200, 170, 90))
        c.put(c.mask(lambda p: [p.ellipse(x_, y_, 1.4) for x_, y_ in pts[::2]]), (255, 240, 180))
    # Lanterns: one hung from a cap, one stood on the floor, by turns.
    for i, x in enumerate(range(480, TWIST[0], 300)):
        y = CEIL + 26 if i % 2 == 0 else FLOOR - 22
        c.put(c.mask(lambda p: p.rect(x - 1, CEIL + 10 if i % 2 == 0 else y, x + 1, y if i % 2 == 0 else FLOOR)), (60, 60, 64))
        c.put(c.mask(lambda p: p.rect(x - 6, y - 8, x + 6, y + 8)), LAMP)
        c.light(c.mask(lambda p: p.ellipse(x, y, 70, 50), blur=20), LAMP, 0.3)
    # The rails along the floor, up the back wall in a half twist, and back
    # along the ceiling.
    t0, t1 = TWIST
    for off in (-4, 4):
        c.put(c.mask(lambda p: p.rect(16, FLOOR - 4 + off * 0.5, t0, FLOOR - 2 + off * 0.5)), RAIL)
        c.put(c.mask(lambda p: p.rect(16, CEIL + 2 - off * 0.5, t0, CEIL + 4 - off * 0.5)), RAIL)
    pts_a, pts_b = [], []
    for t in np.linspace(0, 1, 40):
        x = t0 + (t1 - t0) * math.sin(t * math.pi)
        y = FLOOR - (FLOOR - CEIL) * t
        twist = math.cos(t * math.pi) * 8
        pts_a.append((x, y - twist))
        pts_b.append((x, y + twist))
    c.put(c.mask(lambda p: (p.line(pts_a, 3), p.line(pts_b, 3))), RAIL)
    c.put(c.mask(lambda p: [p.line([pts_a[i], pts_b[i]], 2.4) for i in range(0, 40, 3)]), TIMBER_DARK)
    c.light(c.mask(lambda p: p.line(pts_a, 8), blur=8), (180, 200, 255), 0.2)
    # Sleepers along both runs.
    c.put(c.mask(lambda p: ([p.rect(x, FLOOR - 3, x + 18, FLOOR) for x in range(30, t0, 34)], [p.rect(x, CEIL, x + 18, CEIL + 3) for x in range(30, t0, 34)])), TIMBER_DARK)
    # A cart on the floor; another, the same way up to whoever is on the
    # ceiling, hung there.
    cart(c, 760, FLOOR - 2, True)
    cart(c, 1080, CEIL + 2, False)


PIECES: Dict[str, Piece] = {
    "mine_tunnel": Piece((16, 0, W - 16, H), tunnel),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
