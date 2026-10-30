"""The Smoking Mountain (`primeval_smoking_mountain`, the jungle dimension):
past the tar pits, a mountain of basalt shelves up to a smoking crater.

Drawn in room coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/primeval/smoking_mountain.py`: the shelves
walked on (SHELVES: x0, x1, top), the lava pits between them (PITS: x0,
x1, the lava's top, the bed), the crater's lava (CRATER), the room's floor
(y 960).

- `volcano_west`, `volcano_east`: one drawing in two frames (a frame is at
  most a sheet's page wide). Basalt in layers, each shelf's top a lit edge,
  ferns clinging; lava glowing in the pits and in the crater, its plume of
  smoke; on the rim a deckchair and a telescope pointed at the sky, for the
  meteor watch.

Animations: ``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .eureka_props import edge_line
from .primeval_props import BONE, PAL, fern

H = 960
SHELVES = ((0, 520, 896), (660, 1000, 800), (1000, 1300, 704), (1440, 1760, 608), (1760, 2000, 512), (2000, 2200, 416))
PITS = ((520, 660, 912, 944), (1300, 1440, 752, 784))
CRATER = (2200, 2384, 448, 480)
BASALT = (58, 52, 54)
BASALT_LIGHT = (104, 94, 92)
LAVA = (255, 120, 40)
LAVA_HOT = (255, 220, 120)
CRUST = (90, 30, 20)


def volcano(c, k):
    rng = c.rand("volcano")
    # The cone behind, paler with distance, its crater at the east wall.
    cone = c.mask(lambda p: p.poly([(-300, H), (2140, 380), (2420, 380), (2700, H)]))
    c.put(cone, mix(BASALT, (200, 150, 120), 0.45))
    # (No noise on what crosses the frames' seam: a canvas's noise is
    # scaled to its frame, so the two frames' noise would not meet.)
    c.put(cone * c.mask(lambda p: [p.line([(x, H), (2280 + (x - 1000) * 0.05, 400)], 2) for x in range(-200, 2600, 160)]), mix(BASALT, (200, 150, 120), 0.3), 0.6)
    # The crater's lip over its lava, at the east wall.
    c.put(c.mask(lambda p: p.poly([(2200, 416), (2384, 400), (2400, 400), (2400, H), (2200, H)])) * (c.y > CRATER[3]), BASALT)
    # The mountain: each shelf a block of basalt from its top down, layered.
    for i, (x0, x1, top) in enumerate(SHELVES):
        m = c.mask(box(x0, top, x1, H))
        c.put(m, BASALT)
        c.put(m * c.mask(lambda p: [p.rect(x0, y, x1, y + 2) for y in range(top + 18, H, 26)]), scale(BASALT, 0.75))
        edge_line(c, x0, x1, top, BASALT_LIGHT, 5)
    # The pits: their walls, and the lava in them, crusted, glowing.
    for x0, x1, top, bed in PITS + (CRATER,):
        c.put(c.mask(box(x0, bed, x1, H)), BASALT)
        lava = c.mask(box(x0, top, x1, bed))
        c.put(lava, LAVA)
        c.put(lava * np.clip((c.noise(("crust", x0), 6, 2, 2) - 0.55) * 4, 0, 1), CRUST)
        c.put(lava * c.mask(box(x0, top, x1, top + 3)), LAVA_HOT)
        c.light(c.mask(lambda p: p.ellipse((x0 + x1) / 2, top, (x1 - x0) * 0.8, 70), blur=24), LAVA, 0.45)
    # The crater's plume, drifting.
    cx = (CRATER[0] + CRATER[1]) / 2
    for i in range(7):
        y = CRATER[2] - 40 - i * 60
        c.put(c.mask(lambda p: p.ellipse(cx - i * 26 + rng.uniform(-10, 10), y, 40 + i * 14, 26 + i * 6), blur=10), (110, 104, 108), 0.35)
    c.put(c.mask(lambda p: [p.ellipse(rng.uniform(1700, 2384), rng.uniform(40, 400), 1.6) for _ in range(40)]), (255, 150, 60), 0.8)
    # Ferns clinging to the shelves, a few bones.
    for x0, x1, top in SHELVES[:5]:
        # A third of the way along: clear of the frames' seam (x 1200).
        fern(c, x0 + (x1 - x0) * 0.3, top, 36, ("vfern", x0))
    c.put(c.mask(lambda p: [p.line([(x, 896 - 3), (x + 24, 896 - 6)], 4) for x in (180, 300)]), BONE)
    # On the rim: the meteor watch's deckchair and telescope.
    rx, ry = 2060, SHELVES[-1][2]
    c.put(c.mask(lambda p: (p.line([(rx, ry), (rx + 30, ry - 22)], 3), p.line([(rx + 30, ry), (rx + 6, ry - 30)], 3))), (150, 110, 70))
    c.put(c.mask(lambda p: p.poly([(rx + 4, ry - 22), (rx + 32, ry - 24), (rx + 14, ry - 50), (rx + 2, ry - 46)])), (60, 130, 150))
    c.put(c.mask(lambda p: [p.line([(rx + 70, ry - 40), (rx + 70 + dx, ry)], 2) for dx in (-14, 0, 14)]), (70, 60, 50))
    c.put(c.mask(lambda p: p.line([(rx + 56, ry - 34), (rx + 96, ry - 60)], 7)), (190, 160, 90))
    c.put(c.mask(lambda p: p.ellipse(rx + 97, ry - 61, 3, 5)), (180, 220, 240))


PIECES: Dict[str, Piece] = {
    # One drawing in two frames that overlap by 16: a frame's edge column is
    # filtered soft, so a seam where two frames only meet shows the sky
    # through it; overlapped, the later frame's soft edge lies on the
    # earlier frame's same pixels.
    "volcano_west": Piece((0, 300, 1208, H), volcano),
    "volcano_east": Piece((1192, 0, 2400, H), volcano),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
