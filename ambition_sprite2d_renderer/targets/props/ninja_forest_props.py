"""The charcoal burner's camp in the cedar forest (`ninja_village_forest`,
PvN dimension): between the first two cedars, on the forest floor.

Drawn in room coordinates (`_district_props`) on the numbers of
`ninja_village_props` (the forest's floor, y 832; cedar 0's trunk at x 312,
cedar 1's at x 680).

- `forest_kiln_camp`: an earth kiln smoking at its vents, its stoking mouth
  glowing; cedar billets stacked to season; a lean-to of bark and poles
  against cedar 1, a straw mat and a kettle on a little fire in it; bales of
  charcoal in straw (tawara) by the door; an axe in a stump.

Everyday mountain things, drawn with care: no costume and no joke at the
culture's cost. Animations: ``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .eureka_props import Batch
from .ninja_village_props import BARK, CEDAR, CEDAR_LIGHT, FOREST_FLOOR, PAL, TIMBER

G = FOREST_FLOOR
EARTH = (118, 92, 70)
EARTH_DARK = (84, 64, 50)
STRAW = (196, 170, 108)
STRAW_DARK = (150, 124, 74)
EMBER = (255, 140, 60)
SMOKE = (150, 146, 140)


def camp(c, k):
    rng = c.rand("kiln_camp")
    # The kiln: an earth dome, its vents smoking, its mouth glowing.
    kx = 424
    dome = c.mask(lambda p: (p.ellipse(kx, G, 74, 78), p.rect(kx - 74, G - 10, kx + 74, G)))
    c.put(dome * (c.y <= G), EARTH)
    c.tone(dome * (c.y <= G) * np.clip((c.x - kx) / 74, -1, 1), -0.25)
    c.put(dome * (c.y <= G) * c.mask(lambda p: [p.line([(kx - 70 + i * 3, G - 6 - i * 13), (kx + 70 - i * 3, G - 6 - i * 13)], 1.2) for i in range(5)]), EARTH_DARK, 0.7)
    mouth = c.mask(lambda p: (p.ellipse(kx - 20, G - 16, 16, 16), p.rect(kx - 36, G - 16, kx - 4, G)))
    c.put(mouth, (40, 20, 14))
    c.put(c.mask(lambda p: p.ellipse(kx - 20, G - 8, 11, 7)), EMBER)
    c.light(c.mask(lambda p: p.ellipse(kx - 20, G - 10, 40, 24), blur=10), EMBER, 0.35)
    vents = [(kx - 40, G - 52), (kx + 6, G - 74), (kx + 44, G - 50)]
    c.put(c.mask(lambda p: [p.ellipse(x, y, 5, 3) for x, y in vents]), (36, 26, 20))
    for vx, vy in vents:
        for i in range(5):
            c.put(c.mask(lambda p: p.ellipse(vx + i * 5 + rng.uniform(-3, 3), vy - 14 - i * 18, 6 + i * 3, 5 + i * 2), blur=4), SMOKE, 0.4 - i * 0.06)
    # Cedar billets stacked to season, ends out.
    b = Batch(c)
    for row in range(4):
        for col in range(4 - row % 2):
            x, y = 516 + col * 15 + (row % 2) * 7, G - 7 - row * 13
            b.add(CEDAR, 1.0, lambda p, x=x, y=y: p.ellipse(x, y, 7))
            b.add(CEDAR_LIGHT, 1.0, lambda p, x=x, y=y: p.ellipse(x, y, 4.4))
            b.add(scale(CEDAR, 0.7), 1.0, lambda p, x=x, y=y: p.ellipse(x, y, 1.2))
    b.draw()
    # The lean-to against cedar 1: bark slabs on a pole frame, open west.
    lx0, lx1, ridge = 586, 672, G - 104
    c.put(c.mask(lambda p: (p.line([(lx0 + 4, G), (lx0 + 4, G - 58)], 4), p.line([(lx0 - 6, G - 56), (lx1, ridge)], 4))), TIMBER)
    roof = c.mask(lambda p: p.poly([(lx0 - 14, G - 52), (lx1 + 2, ridge - 8), (lx1 + 2, ridge + 4), (lx0 - 12, G - 44)]))
    # Under the roof, the shade inside; then the roof over it.
    c.put(c.mask(lambda p: p.poly([(lx0 + 8, G), (lx0 + 8, G - 44), (lx1, ridge + 6), (lx1, G)])), (40, 30, 24))
    c.put(roof, BARK)
    c.put(roof * c.mask(lambda p: [p.line([(lx0 - 12 + i * 12, G - 50 - i * 6.3), (lx0 - 4 + i * 12, G - 42 - i * 6.3)], 1) for i in range(7)]), scale(BARK, 0.7))
    c.put(c.mask(lambda p: p.poly([(lx0 + 10, G), (lx1 - 4, G), (lx1 - 8, G - 5), (lx0 + 14, G - 5)])), STRAW)
    # The kettle on a little fire, in the lean-to's mouth.
    fx = lx0 + 30
    c.put(c.mask(lambda p: (p.line([(fx - 12, G), (fx, G - 30)], 2), p.line([(fx + 12, G), (fx, G - 30)], 2), p.line([(fx, G - 30), (fx, G - 22)], 1))), TIMBER)
    c.put(c.mask(lambda p: (p.ellipse(fx, G - 14, 8, 7), p.rect(fx - 3, G - 23, fx + 3, G - 20))), (50, 48, 52))
    c.put(c.mask(lambda p: [p.poly([(fx + dx - 3, G), (fx + dx, G - 7 - abs(dx)), (fx + dx + 3, G)]) for dx in (-4, 0, 4)]), EMBER)
    # Bales of charcoal in straw by the lean-to, tied twice.
    for x, y in ((694, G), (722, G), (708, G - 22)):
        bale = c.mask(lambda p: (p.ellipse(x, y - 11, 13, 11), p.rect(x - 13, y - 11, x + 13, y)))
        c.put(bale * (c.y <= y), STRAW)
        c.put(bale * (c.y <= y) * c.mask(lambda p: [p.rect(xx, y - 22, xx + 2, y) for xx in (x - 6, x + 5)]), STRAW_DARK)
        c.put(c.mask(lambda p: [p.ellipse(x + dx, y - 11 + dy, 1.8) for dx, dy in ((-3, -1), (2, -2), (0, 2), (4, 2))]), (40, 38, 38))
    # An axe in a stump.
    sx = 560
    c.put(c.mask(box(sx - 12, G - 18, sx + 12, G)), CEDAR)
    c.put(c.mask(lambda p: p.ellipse(sx, G - 18, 12, 3)), CEDAR_LIGHT)
    c.put(c.mask(lambda p: p.line([(sx - 2, G - 20), (sx + 14, G - 44)], 2.4)), (150, 112, 74))
    c.put(c.mask(lambda p: p.poly([(sx - 6, G - 24), (sx + 2, G - 16), (sx + 6, G - 22), (sx, G - 28)])), (120, 124, 130))


PIECES: Dict[str, Piece] = {
    "forest_kiln_camp": Piece((330, G - 200, 740, G), camp),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
