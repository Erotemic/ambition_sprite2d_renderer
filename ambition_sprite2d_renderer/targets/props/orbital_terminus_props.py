"""The tether terminus (`orbital_station_tether_terminus`, the Science
dimension): the station end of Eureka's space elevator, where the car comes
up through the floor.

Drawn in room coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/eureka/make_specs.py` (`terminus`): the
floor (y 956), the vault (to y 48), the shaft (x 576..704), the down car's
door (x 200) and the docking bay's door (x 1160).

- `terminus_hall`: hull plate; the ribbon of the tether up the room's middle
  through collars in the floor and the vault; a window on the planet's limb;
  the down car's lift doors and the bay's bulkhead (scenery draws over a
  door, so the hall draws its own); the arrivals board; a handrail; the
  souvenir kiosk: shirts on a line, snow globes with the planet in them,
  bottles of genuine orbit air.

Animations: ``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .orbital_station import AMBER, CYAN, GREEN, HULL, HULL_DARK, HULL_LIGHT, INK, LEAF, LEAF_DARK, RED, STEEL, STEEL_DARK, STEEL_LIGHT, hazard, lamp, plate, screen

W, FLOOR, VAULT = 1280, 956, 48
SHAFT = (576, 704)
DOWN_DOOR, BAY_DOOR = 200, 1160
WIN = (800, 250, 1120, 700)
PAL = {"stone": HULL, "stone_light": HULL_LIGHT, "dark": STEEL_DARK, "lamp": AMBER}
SPACE = (8, 10, 22)
OCEAN = (40, 96, 176)
LAND = (96, 140, 84)
CLOUD = (236, 242, 248)


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
    cx, cy, r = (x0 + x1) / 2 - 60, 1900, 1290
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
    # The down car's lift doors, its arrow lamp; the bay's bulkhead.
    lx = DOWN_DOOR
    plate(c, lx - 14, FLOOR - 110, lx + 62, FLOOR, STEEL, "lift_frame", seams=0)
    c.put(c.mask(lambda p: (p.rect(lx, FLOOR - 96, lx + 23, FLOOR), p.rect(lx + 25, FLOOR - 96, lx + 48, FLOOR))), STEEL_LIGHT)
    c.put(c.mask(lambda p: p.poly([(lx + 16, FLOOR - 126), (lx + 32, FLOOR - 126), (lx + 24, FLOOR - 116)])), AMBER)
    bx = BAY_DOOR
    plate(c, bx - 16, FLOOR - 116, bx + 64, FLOOR, STEEL_DARK, "bulkhead", seams=0)
    c.put(c.mask(lambda p: (p.rect(bx, FLOOR - 92, bx + 48, FLOOR), p.ellipse(bx + 24, FLOOR - 92, 24, 10))), STEEL)
    c.put(c.mask(lambda p: p.ring(bx + 24, FLOOR - 56, 8, 3)), STEEL_LIGHT)
    hazard(c, bx - 16, FLOOR - 116, bx + 64, FLOOR - 108, tag="bulkhead_h")
    # The arrivals board.
    plate(c, 330, 150, 750, 290, STEEL_DARK, "board", seams=0)
    screen(c, 340, 160, 740, 280, tint=AMBER, rows=5, tag="arrivals")
    # A handrail along the wall at waist height, clear of the doors, the
    # window's plant and the kiosk.
    for a, b in ((60, lx - 30), (480, SHAFT[0] - 30), (SHAFT[1] + 30, 720), (800, bx - 30)):
        c.put(c.mask(lambda p: (p.rect(a, FLOOR - 40, b, FLOOR - 37), [p.rect(x, FLOOR - 37, x + 3, FLOOR) for x in np.arange(a + 6, b - 4, 60)])), STEEL_LIGHT)
    # The souvenir kiosk, at a person's scale (a body is 64 tall): awning,
    # counter, shirts on a line, globes, bottles.
    k0, k1 = 300, 450
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
