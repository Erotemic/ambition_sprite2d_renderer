"""Draw the tram tube between the observation deck and the orchard."""

from __future__ import annotations

from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .orbital_station import AMBER, CYAN, GREEN, HULL, HULL_DARK, HULL_LIGHT, INK, LEAF, LEAF_DARK, RED, STEEL, STEEL_DARK, STEEL_LIGHT

W, DECK, TOP = 3200, 576, 120
TRENCH = (1200, 1840, 624)
LIFT_ROOF = (2768, 3200, 416)
LIFT_DOOR = 3040
PAL = {"stone": HULL, "stone_light": HULL_LIGHT, "dark": STEEL_DARK, "lamp": AMBER}
SPACE = (8, 10, 22)


def hazard_band(c, x0, x1, y0, y1):
    m = c.mask(box(x0, y0, x1, y1))
    c.put(m, AMBER)
    c.put(m * c.mask(lambda p: [p.poly([(x, y1), (x + 8, y1), (x + 8 + (y1 - y0), y0), (x + (y1 - y0), y0)]) for x in np.arange(x0 - 20, x1, 16)]), INK)


def spoke(c, k):
    rng = c.rand("spoke")
    wall = c.mask(box(16, TOP, W - 16, DECK))
    c.put(wall, scale(HULL_DARK, 0.9))
    c.put(wall * c.mask(lambda p: [p.rect(16, y, W - 16, y + 1) for y in range(TOP + 40, DECK, 48)]), scale(HULL_DARK, 0.75))
    # The ribs, and a porthole on the stars between each two.
    for x in range(100, W - 16, 200):
        c.put(c.mask(box(x - 10, TOP, x + 10, DECK)), STEEL)
        c.put(c.mask(box(x - 10, TOP, x - 7, DECK)), STEEL_LIGHT)
        px, py = x + 100, 300
        if px < LIFT_ROOF[0] - 40:
            c.put(c.mask(lambda p: p.ellipse(px, py, 30)), STEEL_DARK)
            glass = c.mask(lambda p: p.ellipse(px, py, 24))
            c.put(glass, SPACE)
            c.put(glass * c.mask(lambda p: [p.ellipse(px + rng.uniform(-22, 22), py + rng.uniform(-22, 22), rng.uniform(0.6, 1.3)) for _ in range(6)]), (230, 236, 255))
            c.put(glass * c.mask(lambda p: p.poly([(px - 14, py + 20), (px - 6, py + 22), (px + 12, py - 20), (px + 4, py - 22)])), (255, 255, 255), 0.1)
    # Overhead: conduits, a cable tray, lamps.
    for y, col in ((TOP + 6, STEEL_LIGHT), (TOP + 18, (150, 90, 60)), (TOP + 30, (70, 120, 150))):
        c.put(c.mask(box(16, y, W - 16, y + 8)), col)
    c.put(c.mask(lambda p: [p.rect(x, TOP + 4, x + 6, TOP + 42) for x in range(60, W, 120)]), STEEL_DARK)
    for x in range(200, W - 16, 200):
        c.put(c.mask(box(x - 20, TOP + 42, x + 20, TOP + 48)), mix(AMBER, (255, 255, 255), 0.4))
        c.light(c.mask(lambda p: p.ellipse(x, TOP + 60, 50, 30), blur=12), AMBER, 0.25)
    for a, b in ((16, 1180), (1860, 2768)):
        c.put(c.mask(lambda p: (p.rect(a, DECK - 40, b, DECK - 37), [p.rect(x, DECK - 37, x + 3, DECK) for x in np.arange(a + 10, b - 4, 80)])), STEEL_LIGHT)
    # The tram's trench: its walls, rails, hazard edges, the painted TRAM.
    t0, t1, tf = TRENCH
    c.put(c.mask(box(t0, DECK, t1, tf)), STEEL_DARK)
    c.put(c.mask(lambda p: [p.rect(t0, y, t1, y + 3) for y in (tf - 10, tf - 4)]), STEEL_LIGHT)
    hazard_band(c, t0 - 30, t0, DECK - 6, DECK)
    hazard_band(c, t1, t1 + 30, DECK - 6, DECK)
    c.put(c.mask(lambda p: [p.poly([(x, 470), (x + 30, 480), (x, 490)]) for x in range(t0 + 100, t1 - 100, 120)]), CYAN, 0.6)
    # The orchard walk crosses above the gated lift landing.
    l0, l1, lf = LIFT_ROOF
    c.put(c.mask(box(l0, lf, l1, lf + 16)), STEEL_DARK)
    c.put(c.mask(box(l0, lf, l1, lf + 3)), STEEL_LIGHT)
    c.put(c.mask(lambda p: (
        p.rect(l0 + 60, lf - 26, l1, lf - 23),
        [p.rect(x, lf - 26, x + 3, lf) for x in range(l0 + 60, l1, 44)],
    )), STEEL_LIGHT)
    hazard_band(c, l0, l0 + 60, lf + 4, lf + 10)
    c.put(c.mask(lambda p: [p.ellipse(3120, y, 5) for y in (DECK - 94, DECK - 74)]), GREEN)
    dx = LIFT_DOOR
    c.put(c.mask(box(dx - 8, DECK - 106, dx + 56, DECK)), STEEL_DARK)
    c.put(c.mask(lambda p: (p.rect(dx, DECK - 90, dx + 48, DECK), p.ellipse(dx + 24, DECK - 90, 24, 8))), STEEL)
    c.put(c.mask(lambda p: p.ellipse(dx + 24, DECK - 66, 8)), SPACE)
    c.put(c.mask(lambda p: p.rect(dx + 38, DECK - 50, dx + 42, DECK - 36)), AMBER)
    # A bench, a plant, and a mural of the planet between the ribs.
    bx = 640
    c.put(c.mask(lambda p: (p.rect(bx - 40, DECK - 24, bx + 40, DECK - 20), p.rect(bx - 36, DECK - 20, bx - 32, DECK), p.rect(bx + 32, DECK - 20, bx + 36, DECK))), STEEL_LIGHT)
    c.put(c.mask(lambda p: p.poly([(744, DECK), (776, DECK), (780, DECK - 30), (740, DECK - 30)])), STEEL)
    c.put(c.mask(lambda p: [p.line([(760, DECK - 30), (760 + dx, DECK - 30 - dy)], 3) for dx, dy in ((-24, 28), (-10, 42), (4, 48), (18, 40), (28, 24))]), LEAF)
    c.put(c.mask(lambda p: [p.line([(760, DECK - 30), (760 + dx, DECK - 30 - dy)], 1.2) for dx, dy in ((-16, 34), (10, 44))]), LEAF_DARK)
    mx, my = 2210, 330
    c.put(c.mask(box(mx - 90, my - 70, mx + 90, my + 70)), SPACE)
    c.put(c.mask(lambda p: p.ellipse(mx, my + 40, 70, 50)) * c.mask(box(mx - 90, my - 70, mx + 90, my + 70)), (40, 96, 176))
    c.put(c.mask(lambda p: [p.ellipse(mx + dx, my + 20 + dy, 14, 6) for dx, dy in ((-30, 0), (20, 10), (0, 30))]) * c.mask(lambda p: p.ellipse(mx, my + 40, 70, 50)), (96, 140, 84))
    c.put(c.mask(lambda p: (p.line([(mx - 90, my - 70), (mx + 90, my - 70), (mx + 90, my + 70), (mx - 90, my + 70), (mx - 90, my - 70)], 4))), STEEL)


PIECES: Dict[str, Piece] = {
    # One drawing in two frames that overlap by 16 (see `orbital_spur_props`).
    "spoke_west": Piece((16, TOP, 1608, TRENCH[2] + 4), spoke),
    "spoke_east": Piece((1592, TOP, W - 16, TRENCH[2] + 4), spoke),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
