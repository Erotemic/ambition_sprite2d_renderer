"""The Prototype Workshop under Castle Godwin's barracks
(`castle_godwin_workshop`, the Evil dimension): where the castle's failed
prototypes come from.

Drawn in room coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/castle_kitchens/make_specs.py`
(`workshop`): the floor (y 512), the ceiling (to y 48), the door back up to
the barracks (x 40).

- `workshop_room`: a stone vault; its iron door (scenery draws over a door,
  so the room draws its own); the tool wall, one outline empty (the big
  spanner); the workbench and a walking toaster half built on it; the
  boiler, copper, its gauge in the red and its pipes up into the vault;
  the blueprints pinned up (a kettle with legs, a searchlight with legs, a
  hound of springs), one stamped REJECTED; the battle kettle on the
  assembly bench, its spout a cannon; the red button on its pedestal.

Animations: ``idle``, 1 frame. No drop shadows.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from . import castle_godwin as CG
from .eureka_props import ashlar

W, FLOOR, CEILING = 1280, 512, 48
PAL = {"stone": CG.STONE, "stone_light": CG.STONE_LIGHT, "dark": (22, 18, 26), "lamp": (255, 200, 120)}
STONE, STONE_DARK = CG.STONE, CG.STONE_DARK
RED = CG.RED
WOOD = (96, 64, 44)
WOOD_DARK = (60, 40, 30)
IRON = (52, 52, 60)
STEEL = (130, 136, 146)
COPPER = (190, 104, 60)
COPPER_LIGHT = (232, 150, 96)
BLUEPRINT = (40, 70, 130)
CHALK = (220, 230, 245)


def bench(c, x0, x1, g):
    c.put(c.mask(box(x0, g - 38, x1, g - 32)), WOOD)
    c.put(c.mask(lambda p: [p.rect(x, g - 32, x + 5, g) for x in (x0 + 6, x1 - 11)]), WOOD_DARK)
    c.put(c.mask(box(x0 + 6, g - 12, x1 - 6, g - 9)), WOOD_DARK)


def room(c, k):
    g = FLOOR
    rng = c.rand("workshop")
    ashlar(c, 16, CEILING, W - 16, g, STONE, course=20, block=40, tag="workshop", vary=0.06)
    c.tone(c.mask(box(16, CEILING, W - 16, g)) * np.clip((200 - c.y) / 150, 0, 1), -0.35)
    for x in range(16, W, 400):
        c.put(c.mask(lambda p: p.poly([(x - 14, g), (x - 14, 140), (x, CEILING), (x + 14, 140), (x + 14, g)])), STONE_DARK)
    c.put(c.mask(box(16, g - 22, W - 16, g)), STONE_DARK)
    # The iron door back up to the barracks (the room's door zone, x 40..88).
    c.put(c.mask(box(34, g - 104, 94, g)), STONE_DARK)
    door = c.mask(box(40, g - 96, 88, g))
    c.put(door, IRON)
    c.put(door * c.mask(lambda p: ([p.rect(40, y, 88, y + 2) for y in (g - 80, g - 48, g - 16)], [p.ellipse(x, y, 1.6) for x in (46, 82) for y in range(g - 90, g, 12)])), scale(IRON, 0.6))
    c.put(c.mask(lambda p: p.ring(80, g - 50, 4, 1.6)), STEEL)
    # The tool wall: a board of hooks and outlines, one outline empty.
    c.put(c.mask(box(130, 250, 380, 400)), WOOD_DARK)
    c.put(c.mask(lambda p: [p.ellipse(x, y, 0.9) for x in range(138, 376, 12) for y in range(258, 396, 12)]), (40, 28, 22))
    tools = [((160, 270), (160, 340), 4), ((200, 270), (200, 330), 3), ((240, 266), (252, 340), 5), ((290, 270), (290, 320), 6)]
    for a, b, w in tools:
        c.put(c.mask(lambda p: p.line([a, b], w)), STEEL)
    c.put(c.mask(lambda p: (p.ellipse(160, 272, 7), p.rect(196, 268, 206, 276), p.poly([(284, 268), (296, 268), (300, 282), (280, 282)]))), STEEL)
    c.put(c.mask(lambda p: (p.ring(340, 280, 9, 1.4), p.ring(340, 376, 11, 1.4), p.line([(340, 289), (340, 365)], 1.4))), (220, 220, 230), 0.8)
    # The workbench, a vice, a walking toaster half built.
    bench(c, 130, 380, g)
    c.put(c.mask(lambda p: (p.rect(140, g - 52, 170, g - 38), p.rect(150, g - 58, 160, g - 52))), IRON)
    tx = 290
    c.put(c.mask(lambda p: (p.rect(tx - 20, g - 70, tx + 20, g - 44), p.ellipse(tx, g - 70, 20, 5))), STEEL)
    c.put(c.mask(lambda p: [p.rect(tx - 12 + i * 14, g - 74, tx - 4 + i * 14, g - 70) for i in range(2)]), (30, 28, 30))
    c.put(c.mask(lambda p: [p.line([(tx + dx, g - 44), (tx + dx * 1.6, g - 38)], 1.6) for dx in (-12, 12)]), STEEL)
    c.put(c.mask(lambda p: p.line([(tx + 20, g - 58), (tx + 30, g - 58)], 2)), IRON)
    c.put(c.mask(lambda p: [p.ellipse(tx + dx, g - 62, 2.4) for dx in (-6, 6)]), (255, 200, 80))
    # The boiler: copper, the gauge in the red, pipes up into the vault.
    b0, b1 = 430, 620
    boiler = c.mask(lambda p: (p.rect(b0, g - 150, b1, g - 20), p.ellipse((b0 + b1) / 2, g - 150, (b1 - b0) / 2, 18)))
    c.put(boiler, COPPER)
    c.tone(boiler * np.clip((c.x - (b0 + b1) / 2) / ((b1 - b0) / 2), -1, 1), -0.25)
    c.put(boiler * c.mask(lambda p: [p.rect(b0, y, b1, y + 3) for y in (g - 120, g - 70)]), scale(COPPER, 0.7))
    c.put(boiler * c.mask(lambda p: [p.ellipse(x, y, 1.6) for x in range(b0 + 8, b1, 14) for y in (g - 118, g - 68)]), COPPER_LIGHT)
    c.put(c.mask(lambda p: [p.rect(x - 6, g - 20, x + 6, g) for x in (b0 + 20, b1 - 20)]), IRON)
    c.put(c.mask(lambda p: (p.rect(b0 + 40, CEILING, b0 + 54, g - 160), p.rect(b1 - 60, CEILING, b1 - 46, g - 160))), COPPER)
    gx, gy = (b0 + b1) / 2, g - 96
    c.put(c.mask(lambda p: p.ellipse(gx, gy, 18)), (236, 230, 210))
    c.put(c.mask(lambda p: p.ring(gx, gy, 18, 3)), IRON)
    c.put(c.mask(lambda p: p.poly([(gx, gy), (gx + 16 * math.cos(-0.5), gy + 16 * math.sin(-0.5)), (gx + 16 * math.cos(0.3), gy + 16 * math.sin(0.3))])), RED, 0.7)
    c.put(c.mask(lambda p: p.line([(gx, gy), (gx + 14 * math.cos(0.15), gy + 14 * math.sin(0.15))], 1.6)), (30, 28, 30))
    c.put(c.mask(lambda p: (p.rect(b0 + 30, g - 46, b0 + 70, g - 26), p.ellipse(b0 + 50, g - 36, 10))), (40, 20, 14))
    c.light(c.mask(lambda p: p.ellipse(b0 + 50, g - 36, 16), blur=6), (255, 140, 60), 0.6)
    for i in range(4):
        c.put(c.mask(lambda p: p.ellipse(b1 - 20 + i * 8, g - 170 - i * 18, 8 + i * 4, 5 + i * 2), blur=4), (230, 230, 236), 0.3)
    # The blueprints, one stamped REJECTED.
    for i, x in enumerate((680, 760, 840)):
        c.put(c.mask(box(x, 170, x + 70, 260)), BLUEPRINT)
        c.put(c.mask(lambda p: p.ellipse(x + 35, 172, 2.4)), RED)
        if i == 0:   # a kettle with legs
            pts = lambda p: (p.ring(x + 35, 210, 16, 1), p.line([(x + 51, 206), (x + 62, 198)], 1), p.line([(x + 26, 225), (x + 20, 248)], 1), p.line([(x + 44, 225), (x + 50, 248)], 1))
        elif i == 1:  # a searchlight with legs
            pts = lambda p: (p.ring(x + 35, 205, 12, 1), p.line([(x + 23, 205), (x + 8, 190)], 1), p.line([(x + 30, 217), (x + 22, 248)], 1), p.line([(x + 40, 217), (x + 48, 248)], 1), p.line([(x + 35, 217), (x + 35, 248)], 1))
        else:        # a hound of springs
            pts = lambda p: (p.line([(x + 14, 220), (x + 54, 220)], 1), p.ring(x + 58, 212, 6, 1), [p.line([(x + xx, 220), (x + xx + 3 * ((j % 2) * 2 - 1), 228 + j % 3), (x + xx, 248)], 1) for j, xx in enumerate((18, 26, 44, 52))])
        c.put(c.mask(pts), CHALK)
    c.put(c.mask(lambda p: p.poly([(752, 230), (836, 210), (840, 226), (756, 246)])), RED, 0.85)
    # The assembly bench: the battle kettle, its spout a cannon.
    bench(c, 940, 1180, g)
    kx = 1040
    kettle = c.mask(lambda p: (p.ellipse(kx, g - 70, 30, 24), p.rect(kx - 30, g - 70, kx + 30, g - 52)))
    c.put(kettle, STEEL)
    c.tone(kettle * np.clip((c.x - kx) / 30, -1, 1), -0.25)
    c.put(c.mask(lambda p: (p.line([(kx + 26, g - 66), (kx + 52, g - 84)], 7), p.ring(kx, g - 98, 10, 3))), IRON)
    c.put(c.mask(lambda p: [p.line([(kx + dx, g - 52), (kx + dx * 1.3, g - 38)], 3) for dx in (-20, -7, 7, 20)]), IRON)
    c.put(c.mask(lambda p: [p.ellipse(kx + dx, g - 76, 3) for dx in (-9, 9)]), (255, 90, 60))
    c.put(c.mask(lambda p: [p.rect(1110 + i * 12, g - 46, 1118 + i * 12, g - 38) for i in range(4)]), (150, 130, 90))
    # The red button on its pedestal. Do not.
    px = 1220
    c.put(c.mask(lambda p: (p.rect(px - 8, g - 40, px + 8, g), p.rect(px - 12, g - 44, px + 12, g - 40))), IRON)
    c.put(c.mask(lambda p: p.ellipse(px, g - 46, 7, 4)), RED)
    c.put(c.mask(lambda p: p.poly([(px - 14, g - 44), (px + 14, g - 44), (px + 10, g - 62), (px - 10, g - 62)])), (200, 220, 240), 0.3)


PIECES: Dict[str, Piece] = {
    "workshop_room": Piece((16, CEILING, W - 16, FLOOR), room),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
