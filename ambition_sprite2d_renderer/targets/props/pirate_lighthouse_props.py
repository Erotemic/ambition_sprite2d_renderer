"""The Lighthouse Point (`pirate_lighthouse_point`, PvN dimension): out of
the Pirate Port, east of the Wreckers' Reef: the honest light, which the
wreckers would like out.

Drawn in room coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/pirate_port/make_specs.py` (`point`): the
rock (y 960), the tower (x 900..1100 at its foot, 940..1060 under the
gallery), its stair landings inside (LANDINGS: x0, x1, y), the gallery (x
860..1140, y 400), all walked on.

- `point_lighthouse`: the tower in red and white bands, cut away to show
  its stair inside (each landing a plank on brackets), the gallery and its
  rail, the lamp room's glass and the great lens, its two beams.
- `point_cottage`: the keeper's cottage, whitewashed, slate and a smoking
  chimney, a lit window, a garden of cabbages behind a wall, a rowing boat
  upturned on trestles, a bench facing the sea.

Animations: ``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .eureka_props import edge_line
from .pirate_port_props import PAL, PLANK, PLANK_DARK, TIMBER

G = 960
TOWER = (900, 1100, 940, 1060)
GALLERY = (860, 1140, 400)
#: The stair inside the tower: landings zigzagging up (x0, x1, y).
LANDINGS = ((930, 1000, 880), (1000, 1070, 800), (935, 1005, 720), (995, 1065, 640), (940, 1010, 560), (990, 1060, 480))
RED = (190, 50, 44)
WHITE = (236, 232, 222)
INSIDE = (60, 52, 50)
GLASS = (200, 230, 240)
LAMP = (255, 236, 160)
SLATE = (70, 76, 86)


def tower_x(y):
    """The tower's two sides at height y (from its foot to the gallery)."""
    b0, b1, t0, t1 = TOWER
    f = (G - y) / (G - GALLERY[2])
    return b0 + (t0 - b0) * f, b1 + (t1 - b1) * f


def lighthouse(c, k):
    b0, b1, t0, t1 = TOWER
    gy = GALLERY[2]
    shell = c.mask(lambda p: p.poly([(b0, G), (b1, G), (t1, gy), (t0, gy)]))
    # Bands of red and white, the cut-away inside dark between its walls.
    c.put(shell, WHITE)
    c.put(shell * c.mask(lambda p: [p.rect(b0 - 20, y, b1 + 20, y + 70) for y in range(gy + 70, G, 140)]), RED)
    c.tone(shell * np.clip((c.x - (b0 + b1) / 2) / 100, -1, 1), -0.2)
    inner = c.mask(lambda p: p.poly([(b0 + 18, G), (b1 - 18, G), (t1 - 14, gy + 20), (t0 + 14, gy + 20)]))
    c.put(inner, INSIDE)
    c.put(inner * c.mask(lambda p: [p.rect(b0, y, b1, y + 1.2) for y in range(gy + 30, G, 22)]), scale(INSIDE, 0.8))
    # The landings: planks on brackets, a rail on the open side.
    for x0, x1, y in LANDINGS:
        c.put(c.mask(box(x0, y, x1, y + 8)), PLANK)
        edge_line(c, x0, x1, y, mix(PLANK, (255, 240, 210), 0.3), 2)
        c.put(c.mask(lambda p: p.poly([(x0 + 6, y + 8), (x0 + 16, y + 8), (x0 + 6, y + 22)]) if x0 < (b0 + b1) / 2 - 10 else p.poly([(x1 - 6, y + 8), (x1 - 16, y + 8), (x1 - 6, y + 22)])), PLANK_DARK)
    # A window or two, lit, and the door at the foot.
    for y in (820, 640):
        c.put(c.mask(box(990, y, 1010, y + 26)), LAMP)
    c.put(c.mask(lambda p: (p.rect(980, G - 60, 1020, G), p.ellipse(1000, G - 60, 20, 10))), (60, 40, 30))
    # The gallery and its rail, the lamp room's glass, the lens, the beams.
    gx0, gx1, _ = GALLERY
    c.put(c.mask(box(gx0, gy, gx1, gy + 12)), (50, 50, 56))
    edge_line(c, gx0, gx1, gy, (120, 120, 130), 3)
    c.put(c.mask(lambda p: (p.rect(gx0, gy - 30, gx1, gy - 27), [p.rect(x, gy - 30, x + 2, gy) for x in range(gx0, gx1 + 1, 20)])), (50, 50, 56))
    lr0, lr1, lt = 950, 1050, gy - 110
    c.put(c.mask(box(lr0, lt, lr1, gy)), GLASS, 0.5)
    c.put(c.mask(lambda p: [p.rect(x, lt, x + 3, gy) for x in range(lr0, lr1 + 1, 25)]), (50, 50, 56))
    c.put(c.mask(lambda p: p.poly([(lr0 - 10, lt), (lr1 + 10, lt), (1000, lt - 40)])), RED)
    c.put(c.mask(lambda p: p.ellipse(1000, lt - 44, 6)), (50, 50, 56))
    c.put(c.mask(lambda p: p.ellipse(1000, gy - 55, 26, 34)), LAMP)
    c.put(c.mask(lambda p: [p.rect(974, y, 1026, y + 2) for y in range(gy - 86, gy - 22, 8)]), mix(LAMP, (255, 255, 255), 0.5))
    # The beams: soft light laid over the sky (a light over nothing shows
    # nothing, so they are painted, faint).
    beams = c.mask(lambda p: (p.poly([(1026, gy - 70), (1026, gy - 40), (1560, gy - 10), (1560, gy - 140)]), p.poly([(974, gy - 70), (974, gy - 40), (440, gy - 10), (440, gy - 140)])), blur=14)
    c.put(beams * np.clip(1 - np.abs(c.x - 1000) / 560, 0, 1), LAMP, 0.3)
    c.light(c.mask(lambda p: p.ellipse(1000, gy - 55, 80), blur=24), LAMP, 0.5)


def cottage(c, k):
    x0, x1, ridge = 480, 760, G - 160
    walls = c.mask(box(x0, G - 110, x1, G))
    c.put(walls, WHITE)
    c.tone(walls * (c.noise("cottage", 8, 4, 2) - 0.5), 0.08)
    c.put(c.mask(lambda p: p.poly([(x0 - 16, G - 110), (x1 + 16, G - 110), ((x0 + x1) / 2, ridge)])), SLATE)
    c.put(c.mask(lambda p: [p.line([(x0 - 8 + i * 12, G - 112), ((x0 + x1) / 2 - 2 + i * 0.4, ridge + 4)], 0.6) for i in range(26)]), scale(SLATE, 0.8))
    c.put(c.mask(box(x1 - 70, ridge - 10, x1 - 46, G - 120)), WHITE)
    for i in range(4):
        c.put(c.mask(lambda p: p.ellipse(x1 - 58 + i * 7, ridge - 24 - i * 18, 7 + i * 3, 5 + i * 2), blur=4), (210, 210, 214), 0.35)
    c.put(c.mask(box(x0 + 40, G - 80, x0 + 80, G - 46)), LAMP)
    c.put(c.mask(lambda p: (p.rect(x0 + 59, G - 80, x0 + 61, G - 46), p.rect(x0 + 40, G - 64, x0 + 80, G - 62))), TIMBER)
    c.put(c.mask(box(x0 + 140, G - 70, x0 + 176, G)), (40, 70, 90))
    # The garden wall and its cabbages; the boat on trestles; the bench.
    c.put(c.mask(box(300, G - 30, 470, G)), (130, 126, 116))
    c.put(c.mask(lambda p: [p.ellipse(x, G - 34, 9, 6) for x in range(320, 460, 24)]), (90, 140, 80))
    c.put(c.mask(lambda p: (p.line([(780, G), (790, G - 30)], 3), p.line([(860, G), (850, G - 30)], 3))), TIMBER)
    c.put(c.mask(lambda p: p.poly([(760, G - 30), (880, G - 30), (870, G - 46), (770, G - 46)])), (40, 90, 110))
    c.put(c.mask(lambda p: (p.rect(1200, G - 24, 1290, G - 20), p.rect(1206, G - 20, 1210, G), p.rect(1280, G - 20, 1284, G), p.rect(1200, G - 44, 1204, G - 24))), TIMBER)


PIECES: Dict[str, Piece] = {
    "point_lighthouse": Piece((420, 200, 1580, G), lighthouse),
    "point_cottage": Piece((290, 760, 1300, G), cottage),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
