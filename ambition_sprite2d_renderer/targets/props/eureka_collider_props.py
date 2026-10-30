"""The Eureka Collider (`eureka_collider`, the Science dimension): under the
lecture hall, down its stair: a stretch of the ring's tunnel and the
detector's cavern at its end.

Drawn in room coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/eureka/make_specs.py` (`collider`): the
floor (y 576), the vault (to y 48), the door up (x 40), the detector's
gallery (x 1500..1760, y 384), walked on.

- `collider_tunnel`: the tunnel's concrete, curving away; the beam pipe
  along it on its stands, a blue magnet every 160, cable trays, warning
  lamps; the staff's bicycles in their rack (the ring is 27 km round); the
  detector at the east end, end on: rings in rings, an octagon of them, the
  beam pipe through its heart; its gallery and the control desk.

Animations: ``idle``, 1 frame. No drop shadows.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .eureka_props import PAL

W, FLOOR, VAULT = 2000, 576, 48
GALLERY = (1500, 1760, 384)
CONCRETE = (150, 150, 146)
CONCRETE_DARK = (110, 110, 108)
PIPE = (190, 196, 204)
MAGNET = (40, 90, 170)
MAGNET_LIGHT = (90, 140, 210)
CABLE = (60, 60, 64)
AMBER = (246, 176, 76)
RED = (214, 72, 60)
YELLOW = (230, 200, 60)
DETECTOR = ((230, 120, 60), (200, 200, 60), (80, 160, 200), (150, 90, 170), (90, 170, 110), (210, 210, 220))


def octagon(cx, cy, r):
    return [(cx + r * math.cos(math.pi / 8 + i * math.pi / 4), cy + r * math.sin(math.pi / 8 + i * math.pi / 4)) for i in range(8)]


def tunnel(c, k):
    rng = c.rand("collider")
    wall = c.mask(box(16, VAULT, W - 16, FLOOR))
    c.put(wall, CONCRETE)
    c.tone(wall * (c.noise("collider_concrete", 20, 8, 2) - 0.5), 0.1)
    c.put(wall * c.mask(lambda p: [p.rect(x, VAULT, x + 1.4, FLOOR) for x in range(16, W, 120)]), CONCRETE_DARK)
    c.tone(wall * np.clip((180 - c.y) / 130, 0, 1), -0.3)
    # Cable trays along the wall, and the lamps.
    for y, col in ((110, CABLE), (126, (150, 60, 50)), (142, (60, 110, 60))):
        c.put(c.mask(box(16, y, 1400, y + 8)), col)
    for x in range(120, 1400, 240):
        c.put(c.mask(box(x - 16, 80, x + 16, 88)), mix(AMBER, (255, 255, 255), 0.5))
        c.light(c.mask(lambda p: p.ellipse(x, 100, 60, 30), blur=12), AMBER, 0.2)
    # The beam pipe on its stands, a magnet every 160.
    py = 400
    c.put(c.mask(box(16, py - 6, 1520, py + 6)), PIPE)
    c.put(c.mask(box(16, py - 6, 1520, py - 3)), (230, 236, 240))
    for x in range(120, 1440, 160):
        c.put(c.mask(lambda p: (p.rect(x - 4, py + 6, x + 4, FLOOR), p.rect(x - 16, FLOOR - 6, x + 16, FLOOR))), CONCRETE_DARK)
        m = c.mask(lambda p: p.rect(x + 30, py - 26, x + 110, py + 26))
        c.put(m, MAGNET)
        c.put(m * c.mask(box(x + 30, py - 26, x + 110, py - 20)), MAGNET_LIGHT)
        c.put(c.mask(lambda p: [p.rect(x + 40 + i * 20, py - 18, x + 46 + i * 20, py + 18) for i in range(4)]), scale(MAGNET, 0.7))
        c.put(c.mask(lambda p: p.ellipse(x + 104, py - 30, 3)), RED if (x // 160) % 3 == 0 else (80, 200, 100))
    # The staff's bicycles, in their rack.
    for i, bx in enumerate((260, 320, 380)):
        c.put(c.mask(lambda p: (p.ring(bx - 14, FLOOR - 14, 13, 2), p.ring(bx + 18, FLOOR - 14, 13, 2))), (40, 40, 44))
        c.put(c.mask(lambda p: p.line([(bx - 14, FLOOR - 14), (bx, FLOOR - 34), (bx + 18, FLOOR - 14), (bx + 2, FLOOR - 14), (bx - 14, FLOOR - 14)], 2)),
              ((200, 60, 50), (60, 120, 200), (220, 200, 60))[i])
        c.put(c.mask(lambda p: (p.line([(bx, FLOOR - 34), (bx - 4, FLOOR - 40)], 2), p.line([(bx + 14, FLOOR - 30), (bx + 18, FLOOR - 40)], 2))), (40, 40, 44))
    c.put(c.mask(lambda p: p.rect(240, FLOOR - 8, 410, FLOOR - 4)), CABLE)
    # The detector at the east end, end on: rings in rings.
    cx, cy = 1630, 330
    for i, (r, col) in enumerate(zip((230, 200, 165, 130, 95, 60), DETECTOR)):
        c.put(c.mask(lambda p: p.poly(octagon(cx, cy, r))), col)
        c.put(c.mask(lambda p: p.line(octagon(cx, cy, r) + [octagon(cx, cy, r)[0]], 2)), scale(col, 0.6))
        c.put(c.mask(lambda p: [p.line([(cx + (r - 12) * math.cos(a), cy + (r - 12) * math.sin(a)), (cx + (r - 30) * math.cos(a), cy + (r - 30) * math.sin(a))], 2) for a in np.linspace(0, 2 * math.pi, 16, endpoint=False)]), scale(col, 0.75))
    c.put(c.mask(lambda p: p.ellipse(cx, cy, 24)), PIPE)
    c.put(c.mask(lambda p: p.ellipse(cx, cy, 10)), (30, 30, 40))
    c.light(c.mask(lambda p: p.ellipse(cx, cy, 40), blur=10), (200, 220, 255), 0.5)
    # Its stands and the gallery before it (walked on), the control desk.
    c.put(c.mask(lambda p: [p.rect(x, cy + 200, x + 30, FLOOR) for x in (cx - 160, cx + 130)]), CONCRETE_DARK)
    g0, g1, gy = GALLERY
    c.put(c.mask(box(g0, gy, g1, gy + 10)), (70, 70, 76))
    c.put(c.mask(lambda p: (p.rect(g0, gy - 30, g1, gy - 27), [p.rect(x, gy - 30, x + 2, gy) for x in range(g0, g1 + 1, 20)])), YELLOW)
    c.put(c.mask(lambda p: [p.rect(x, gy + 10, x + 6, FLOOR) for x in (g0 + 10, g1 - 16)]), (70, 70, 76))
    c.put(c.mask(lambda p: (p.rect(1800, FLOOR - 50, 1960, FLOOR - 44), p.rect(1806, FLOOR - 44, 1812, FLOOR), p.rect(1948, FLOOR - 44, 1954, FLOOR))), (70, 70, 76))
    c.put(c.mask(lambda p: [p.rect(x, FLOOR - 90, x + 40, FLOOR - 52) for x in (1810, 1858, 1906)]), (20, 30, 40))
    c.put(c.mask(lambda p: [p.line([(x + 4, FLOOR - 70 + rng.uniform(-8, 8)), (x + 36, FLOOR - 70 + rng.uniform(-8, 8))], 1) for x in (1810, 1858, 1906)]), (120, 220, 140))


PIECES: Dict[str, Piece] = {
    "collider_tunnel": Piece((16, VAULT, W - 16, FLOOR), tunnel),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
