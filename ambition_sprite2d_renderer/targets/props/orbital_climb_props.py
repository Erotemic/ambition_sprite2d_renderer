"""Things passed on the tether's climb (`eureka_elevator_climb`, the Science
dimension), each at its altitude.

Drawn in room coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/eureka/make_specs.py` (`elevator_climb`):
the room is 1280 by 3200, the ribbon up its middle (x 640, the car's
middle; the camera shows about x 320..960 of it), the signs at 12 km (y 2944), 100 km (y 2240), 2,000 km (y 1440)
and 20,000 km (y 640).

- `climb_balloon`: a weather balloon, its instrument box and radar
  reflector on a line, beside the 12 km sign: the weather is below now.
- `climb_karman`: the Karman line: a hoop round the ribbon with its plaque,
  and a dotted line across the room. Space, technically.
- `climb_satellite`: a satellite of low orbit, panels out, and its
  traffic: a lost glove and a spanner turning slowly.
- `climb_navsat`: a navigation satellite, high and alone, its dish to the
  planet.

Animations: ``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .orbital_station import AMBER, CYAN, HULL, HULL_LIGHT, INK, NAVY, RED, STEEL, STEEL_DARK, STEEL_LIGHT, lamp

MID = 640
PAL = {"stone": HULL, "stone_light": HULL_LIGHT, "dark": STEEL_DARK, "lamp": AMBER}
GOLD = (210, 170, 70)
PANEL = (40, 60, 120)


def balloon(c, k):
    bx, by = 450, 2700
    body = c.mask(lambda p: p.ellipse(bx, by, 46, 52))
    c.put(body, (236, 236, 240))
    c.tone(body * np.clip((c.x - bx) / 46, -1, 1), -0.2)
    c.light(c.mask(lambda p: p.ellipse(bx - 16, by - 20, 12, 16), blur=6), (255, 255, 255), 0.5)
    c.put(c.mask(lambda p: p.poly([(bx - 6, by + 50), (bx + 6, by + 50), (bx + 3, by + 58), (bx - 3, by + 58)])), (210, 210, 214))
    c.put(c.mask(lambda p: p.line([(bx, by + 58), (bx + 4, by + 150)], 1)), (180, 180, 186))
    c.put(c.mask(lambda p: p.poly([(bx - 10, by + 100), (bx + 10, by + 90), (bx + 18, by + 104), (bx - 2, by + 114)])), STEEL_LIGHT)
    c.put(c.mask(box(bx - 8, by + 150, bx + 16, by + 168)), (236, 140, 60))
    c.put(c.mask(lambda p: p.rect(bx - 4, by + 155, bx + 12, by + 158)), INK)


def karman(c, k):
    y = 2240
    # The dotted line across the room.
    c.put(c.mask(lambda p: [p.rect(x, y - 1, x + 14, y + 1) for x in range(40, 1240, 28)]), (240, 240, 250), 0.7)
    # The hoop round the ribbon, and its plaque on a stalk.
    c.put(c.mask(lambda p: p.ring(MID, y, 22, 4)), STEEL_LIGHT)
    c.put(c.mask(lambda p: p.ring(MID, y, 22, 1.4)), AMBER)
    lamp(c, MID - 22, y, RED, r=2, glow=8)
    lamp(c, MID + 22, y, RED, r=2, glow=8)
    c.put(c.mask(lambda p: p.rect(MID + 22, y - 1, MID + 70, y + 1)), STEEL)
    c.put(c.mask(box(MID + 70, y - 14, MID + 120, y + 14)), STEEL_DARK)
    c.put(c.mask(lambda p: (p.rect(MID + 76, y - 8, MID + 100, y - 5), p.rect(MID + 76, y + 1, MID + 112, y + 4))), AMBER)


def satellite(c, k):
    sx, sy = 450, 1400
    rng = c.rand("sat")
    # The body in gold foil, the panels out either side.
    c.put(c.mask(box(sx - 18, sy - 22, sx + 18, sy + 22)), GOLD)
    c.put(c.mask(lambda p: [p.line([(sx - 18 + rng.uniform(0, 36), sy - 22), (sx - 18 + rng.uniform(0, 36), sy + 22)], 0.6) for _ in range(8)]), scale(GOLD, 0.75))
    for side in (-1, 1):
        x0 = sx + side * 24
        x1 = sx + side * 104
        c.put(c.mask(lambda p: p.rect(min(sx, x0) if side > 0 else x0, sy - 1.5, max(sx, x0) if side < 0 else x0, sy + 1.5)), STEEL)
        panel = c.mask(box(min(x0, x1), sy - 16, max(x0, x1), sy + 16))
        c.put(panel, PANEL)
        c.put(panel * c.mask(lambda p: ([p.rect(x, sy - 16, x + 0.8, sy + 16) for x in np.arange(min(x0, x1), max(x0, x1), 10)], p.rect(min(x0, x1), sy - 0.4, max(x0, x1), sy + 0.4))), scale(PANEL, 0.6))
        c.light(panel * c.mask(lambda p: p.poly([(min(x0, x1), sy + 16), (min(x0, x1) + 14, sy + 16), (min(x0, x1) + 34, sy - 16), (min(x0, x1) + 20, sy - 16)])), (255, 255, 255), 0.2)
    c.put(c.mask(lambda p: (p.line([(sx, sy - 22), (sx, sy - 44)], 1.2), p.ellipse(sx, sy - 46, 3))), STEEL_LIGHT)
    lamp(c, sx, sy - 46, RED, r=1.6, glow=6)
    # Its traffic: a lost glove, a spanner turning.
    gx, gy = 800, 1520
    glove = c.mask(lambda p: (p.ellipse(gx, gy, 14, 10), [p.ellipse(gx - 12 + i * 6, gy - 12 + abs(i - 1.5) * 2, 3, 7) for i in range(4)], p.ellipse(gx + 14, gy - 4, 6, 4), p.rect(gx - 12, gy + 6, gx + 12, gy + 16)))
    c.put(glove, (236, 236, 236))
    c.put(c.mask(box(gx - 12, gy + 12, gx + 12, gy + 16)), (200, 90, 50))
    c.tone(glove * np.clip((c.x - gx) / 16, -1, 1), -0.15)
    wx, wy, a = 870, 1380, math.radians(30)
    dx, dy = 34 * math.cos(a), 34 * math.sin(a)
    c.put(c.mask(lambda p: (p.line([(wx - dx, wy - dy), (wx + dx, wy + dy)], 5), p.ring(wx + dx, wy + dy, 7, 4), p.ring(wx - dx, wy - dy, 6, 3))), STEEL_LIGHT)
    c.put(c.mask(lambda p: [p.line([(wx + dx * f + 10, wy + dy * f - 14), (wx + dx * f + 18, wy + dy * f - 20)], 0.8) for f in (-0.6, 0.0, 0.6)]), (220, 230, 250), 0.6)


def navsat(c, k):
    sx, sy = 830, 600
    c.put(c.mask(box(sx - 14, sy - 14, sx + 14, sy + 14)), STEEL_LIGHT)
    c.put(c.mask(lambda p: p.rect(sx - 14, sy - 4, sx + 14, sy + 4)), NAVY)
    for side in (-1, 1):
        x0, x1 = sx + side * 18, sx + side * 60
        c.put(c.mask(lambda p: p.rect(min(sx, x0), sy - 1, max(sx, x0), sy + 1)), STEEL)
        panel = c.mask(box(min(x0, x1), sy - 10, max(x0, x1), sy + 10))
        c.put(panel, PANEL)
        c.put(panel * c.mask(lambda p: [p.rect(x, sy - 10, x + 0.8, sy + 10) for x in np.arange(min(x0, x1), max(x0, x1), 8)]), scale(PANEL, 0.6))
    # Its dish, to the planet below.
    c.put(c.mask(lambda p: (p.rect(sx - 1, sy + 14, sx + 1, sy + 24), p.poly([(sx - 14, sy + 24), (sx + 14, sy + 24), (sx + 8, sy + 32), (sx - 8, sy + 32)]))), HULL_LIGHT)
    lamp(c, sx, sy - 14, CYAN, r=1.6, glow=6)


PIECES: Dict[str, Piece] = {
    "climb_balloon": Piece((390, 2630, 510, 2880), balloon),
    "climb_karman": Piece((36, 2220, 1244, 2260), karman),
    "climb_satellite": Piece((320, 1320, 920, 1550), satellite),
    "climb_navsat": Piece((760, 576, 900, 640), navsat),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
