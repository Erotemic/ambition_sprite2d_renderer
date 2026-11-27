"""The tether terminus (`orbital_station_tether_terminus`, the Science
dimension): the station end of Eureka's space elevator, where the car comes
up through the floor.

Use the room dimensions in `eureka/make_specs.py`. Use the collision
height of 944 units for the floor.

- `terminus_hall`: hull plate, the tether collars, the viewing gallery,
  the window, the west exit to the docking bay, the arrivals board, and
  the souvenir kiosk.

Animations: ``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box
from .orbital_station import AMBER, CYAN, GREEN, HULL, HULL_DARK, HULL_LIGHT, INK, LEAF, LEAF_DARK, RED, STEEL, STEEL_DARK, STEEL_LIGHT, hazard, lamp, plate, screen

W, FLOOR, VAULT = 1280, 944, 48
SHAFT = (576, 704)
GALLERIES = ((192, 576, 720), (704, 1136, 720))
STEPS = ((128, 240, 880), (192, 304, 816), (256, 368, 752),
         (1104, 1216, 880), (1040, 1152, 816), (976, 1088, 752))
WIN = (800, 250, 1120, 700)
PAL = {"stone": HULL, "stone_light": HULL_LIGHT, "dark": STEEL_DARK, "lamp": AMBER}
SPACE = (8, 10, 22)
OCEAN = (40, 96, 176)
LAND = (96, 140, 84)
CLOUD = (236, 242, 248)
PANEL = (29, 45, 57)


def notice(c, x0, y0, x1, y1):
    c.put(c.mask(box(x0, y0, x1, y1)), STEEL)
    c.put(c.mask(box(x0 + 4, y0 + 4, x1 - 4, y1 - 4)), PANEL)
    c.put(c.mask(lambda p: [p.ellipse(x, y0 + 8, 1.8)
                            for x in (x0 + 8, x1 - 8)]), AMBER)


def deck(c, left, right, top):
    c.put(c.mask(lambda p: [
        p.line([(x, top + 16), (x + 17, top + 38)], 5)
        for x in (left + 13, right - 38)
    ]), STEEL_DARK)
    c.put(c.mask(box(left, top, right, top + 16)), STEEL)
    c.put(c.mask(box(left, top, right, top + 3)), STEEL_LIGHT)
    c.put(c.mask(lambda p: [p.ellipse(x, top + 10, 1.5)
                            for x in range(left + 9, right - 7, 20)]), INK)


def hall(c, k):
    rng = c.rand("terminus")
    plate(c, 16, VAULT, W - 16, FLOOR, HULL, "terminus_wall", seams=64.0)
    # A band of darker plate along the foot of the wall.
    plate(c, 16, FLOOR - 120, W - 16, FLOOR, HULL_DARK, "terminus_dado", seams=64.0, rivets=False)
    # The window on the planet's limb: space, stars, the curve of the world.
    x0, y0, x1, y1 = WIN
    glass = c.mask(lambda p: (p.rect(x0 + 30, y0, x1 - 30, y1), p.rect(x0, y0 + 30, x1, y1 - 30),
                              [p.ellipse(x, y, 30) for x in (x0 + 30, x1 - 30) for y in (y0 + 30, y1 - 30)]))
    c.put(glass, SPACE)
    c.put(glass * c.mask(lambda p: [p.ellipse(rng.uniform(x0, x1), rng.uniform(y0, y1 - 160), rng.uniform(0.6, 1.4)) for _ in range(60)]), (230, 236, 255))
    cx, cy, r = (x0 + x1) / 2 - 60, 1850, 1290
    world = glass * c.mask(lambda p: p.ellipse(cx, cy, r))
    c.put(world, OCEAN)
    c.put(world * np.clip((c.noise("land", 5, 3, 3) - 0.56) * 6, 0, 1), LAND)
    c.put(world * np.clip((c.noise("cloud", 9, 4, 3) - 0.5) * 4, 0, 1), CLOUD, 0.85)
    c.put(world * np.clip((c.y - (cy - r)) / 140, 0, 1), (6, 14, 40), 0.55)
    c.put(glass * c.mask(lambda p: p.ring(cx, cy, r + 3, 5), blur=3), CYAN, 0.7)
    rim = c.mask(lambda p: (p.rect(x0 + 30, y0 - 12, x1 - 30, y0), p.rect(x0 + 30, y1, x1 - 30, y1 + 12),
                            p.rect(x0 - 12, y0 + 30, x0, y1 - 30), p.rect(x1, y0 + 30, x1 + 12, y1 - 30),
                            [p.ring(x, y, 36, 12) for x in (x0 + 30, x1 - 30) for y in (y0 + 30, y1 - 30)]))
    c.put(rim * (1 - glass), STEEL)
    c.light(glass * c.mask(lambda p: p.poly([(x0 + 40, y1), (x0 + 90, y1), (x0 + 220, y0), (x0 + 170, y0)]), blur=6), (255, 255, 255), 0.08)
    # The tether: a ribbon up the middle, through a collar in floor and vault.
    mx = (SHAFT[0] + SHAFT[1]) / 2
    c.put(c.mask(box(mx - 6, VAULT, mx + 6, FLOOR)), (40, 40, 46))
    c.put(c.mask(box(mx - 6, VAULT, mx - 3, FLOOR)), (90, 92, 100))
    for y, h in ((VAULT, 26), (FLOOR - 30, 30)):
        plate(c, SHAFT[0] - 12, y, SHAFT[1] + 12, y + h, STEEL, ("collar", y), seams=0)
        hazard(c, SHAFT[0] - 12, y + h - 8 if y == VAULT else y, SHAFT[1] + 12, y + h if y == VAULT else y + 8, tag=("collar_h", y))
    for x in (SHAFT[0] - 4, SHAFT[1] + 4):
        lamp(c, x, FLOOR - 40, GREEN, r=3, glow=10)
    plate(c, 16, 816, 96, 832, STEEL_DARK, "bay_frame", seams=0)
    c.put(c.mask(box(86, 828, 96, FLOOR)), STEEL)
    lamp(c, 43, 827, GREEN, r=3, glow=10)
    notice(c, 21, 780, 233, 823)
    notice(c, 231, 473, 569, 520)
    notice(c, 252, 539, 548, 672)
    screen(c, 269, 605, 532, 658, tint=AMBER, rows=3, tag="arrivals")
    for x in (212, 493, 738, 1115):
        c.put(c.mask(box(x, 731, x + 10, FLOOR)), STEEL_DARK)
    for left, right, top in GALLERIES:
        deck(c, left, right, top)
        c.put(c.mask(lambda p: (
            p.rect(left + 6, top - 33, right - 6, top - 29),
            [p.rect(x, top - 32, x + 3, top) for x in range(left + 8, right - 4, 41)],
        )), STEEL_LIGHT)
    for span in STEPS:
        deck(c, *span)
    hazard(c, 552, 720, 576, 726, tag="gallery_lip_w")
    hazard(c, 704, 720, 728, 726, tag="gallery_lip_e")
    # A handrail along the wall at waist height, clear of the doors, the
    # window's plant and the kiosk.
    for a, b in ((103, 275), (480, SHAFT[0] - 30), (800, 1240)):
        c.put(c.mask(lambda p: (p.rect(a, FLOOR - 40, b, FLOOR - 37), [p.rect(x, FLOOR - 37, x + 3, FLOOR) for x in np.arange(a + 6, b - 4, 60)])), STEEL_LIGHT)
    # The souvenir kiosk, at a person's scale (a body is 64 tall): awning,
    # counter, shirts on a line, globes, bottles.
    k0, k1 = 300, 450
    notice(c, 284, 766, 466, 820)
    c.put(c.mask(lambda p: [p.rect(x, FLOOR - 112, x + 3, FLOOR - 36) for x in (k0 + 4, k1 - 7)]), STEEL)
    awning = c.mask(lambda p: p.poly([(k0 - 6, FLOOR - 118), (k1 + 6, FLOOR - 118), (k1 + 12, FLOOR - 104), (k0 - 12, FLOOR - 104)]))
    c.put(awning, HULL_LIGHT)
    c.put(awning * c.mask(lambda p: [p.rect(x, FLOOR - 118, x + 12, FLOOR - 104) for x in range(k0 - 12, k1 + 12, 24)]), RED)
    c.put(c.mask(lambda p: p.line([(k0 + 10, FLOOR - 96), (k1 - 10, FLOOR - 96)], 0.8)), INK)
    for i, colour in enumerate((AMBER, CYAN, GREEN, RED)):
        sx = k0 + 30 + i * 30
        shirt = c.mask(lambda p: p.poly([(sx - 8, FLOOR - 95), (sx + 8, FLOOR - 95), (sx + 13, FLOOR - 89), (sx + 8, FLOOR - 87), (sx + 7, FLOOR - 72), (sx - 7, FLOOR - 72), (sx - 8, FLOOR - 87), (sx - 13, FLOOR - 89)]))
        c.put(shirt, colour)
        c.put(c.mask(lambda p: p.ellipse(sx, FLOOR - 82, 3)), OCEAN)
    plate(c, k0, FLOOR - 36, k1, FLOOR, STEEL_DARK, "counter", seams=30.0, rivets=False)
    c.put(c.mask(box(k0 - 3, FLOOR - 39, k1 + 3, FLOOR - 35)), STEEL_LIGHT)
    for gx in (k0 + 16, k0 + 32, k0 + 48):
        c.put(c.mask(lambda p: p.rect(gx - 5, FLOOR - 42, gx + 5, FLOOR - 39)), STEEL)
        c.put(c.mask(lambda p: p.ellipse(gx, FLOOR - 47, 5.5)), (210, 230, 245), 0.55)
        c.put(c.mask(lambda p: p.ellipse(gx, FLOOR - 47, 2.4)), OCEAN)
    for bx_ in range(k1 - 50, k1 - 6, 9):
        c.put(c.mask(lambda p: (p.rect(bx_ - 2.5, FLOOR - 52, bx_ + 2.5, FLOOR - 39), p.rect(bx_ - 1.2, FLOOR - 56, bx_ + 1.2, FLOOR - 52))), (200, 230, 240), 0.6)
        c.put(c.mask(lambda p: p.rect(bx_ - 2.5, FLOOR - 48, bx_ + 2.5, FLOOR - 44)), AMBER)
    # A potted fern by the window, the station's one plant.
    c.put(c.mask(lambda p: p.poly([(744, FLOOR), (776, FLOOR), (780, FLOOR - 30), (740, FLOOR - 30)])), STEEL)
    c.put(c.mask(lambda p: [p.line([(760, FLOOR - 30), (760 + dx, FLOOR - 30 - dy)], 3) for dx, dy in ((-26, 30), (-12, 44), (2, 50), (16, 42), (28, 26))]), LEAF)
    c.put(c.mask(lambda p: [p.line([(760, FLOOR - 30), (760 + dx, FLOOR - 30 - dy)], 1.2) for dx, dy in ((-18, 36), (10, 46))]), LEAF_DARK)


PIECES: Dict[str, Piece] = {
    "terminus_hall": Piece((16, VAULT, W - 16, FLOOR), hall),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
