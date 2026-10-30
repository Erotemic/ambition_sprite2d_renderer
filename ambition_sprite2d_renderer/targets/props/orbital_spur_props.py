"""The damaged spur of the orbital station (`orbital_station_damaged_spur`,
the Science dimension): "live cables, no air, no crew".

Drawn in room coordinates (`_district_props`) on the level's own numbers
(edited in place: `tools/ambition_ldtk_tools/specs/scenery_overlay.py`): the
deck (y 832) and its three holes (x 560..688, 1200..1360, 1760..1888, their
pits live), the buckled bulkhead (x 896..1072, y 64..592; the way under it
y 592..832), the crew's cache (x 2280), the breaker (x 2400).

- `spur_west`, `spur_east`: one drawing in two frames (a frame is at most a
  sheet's page wide). A hull breach on the stars, its plates peeled back and
  frosted; the deck torn up at each hole, the cables severed over it and
  arcing; the bulkhead buckled, its blast door jammed up (the way under it is clear); red emergency lamps
  under the ceiling; the crew's mess left as it was (a table tipped, trays,
  a mug, a wall calendar stopped on a day); a hand-painted sign of the
  crew's that the room's label reads.

Animations: ``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .eureka_props import Batch, stars
from .orbital_station import AMBER, CYAN, HULL, HULL_DARK, RED, STEEL, STEEL_DARK, STEEL_LIGHT, plate

FLOOR, CEILING = 832, 64
HOLES = ((560, 688), (1200, 1360), (1760, 1888))
BULKHEAD = (896, 1072, 592)
BREACH = (300, 160, 520, 440)
PAL = {"stone": HULL, "stone_light": STEEL_LIGHT, "dark": STEEL_DARK, "lamp": AMBER}
ARC = (190, 220, 255)
FROST = (220, 236, 246)
CABLE = (40, 40, 46)


def bolt(rng, a, b, n=10, jag=10.0):
    (x0, y0), (x1, y1) = a, b
    pts = [a]
    for i in range(1, n):
        t = i / n
        pts.append((x0 + (x1 - x0) * t + rng.uniform(-jag, jag), y0 + (y1 - y0) * t + rng.uniform(-jag / 2, jag / 2)))
    return pts + [b]


def spur(c, k):
    rng = c.rand("spur")
    # The breach: a hole on the stars, its plates peeled outward, frost round it.
    bx0, by0, bx1, by1 = BREACH
    cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2
    hole = [(cx + (bx1 - bx0) / 2 * math.cos(t) * rng.uniform(0.7, 1.0), cy + (by1 - by0) / 2 * math.sin(t) * rng.uniform(0.7, 1.0))
            for t in np.linspace(0, 2 * math.pi, 18, endpoint=False)]
    m = c.mask(lambda p: p.poly(hole))
    c.put(m, (6, 8, 16))
    stars(c, bx0, by0, bx1, by1, 40, "breach_stars", clip=m)
    c.light(c.mask(lambda p: p.poly(hole), blur=18) * (1 - m), FROST, 0.35)
    for i, (x, y) in enumerate(hole[::2]):
        dx, dy = x - cx, y - cy
        L = math.hypot(dx, dy)
        ux, uy = dx / L, dy / L
        petal = [(x - uy * 16, y + ux * 16), (x + uy * 16, y - ux * 16), (x + ux * 34 + uy * 4, y + uy * 34 - ux * 4)]
        c.put(c.mask(lambda p: p.poly(petal)), HULL_DARK)
        c.put(c.mask(lambda p: p.line(petal[1:], 1.2)), STEEL_LIGHT)
    # Red emergency lamps under the ceiling, their light down the wall.
    for x in range(120, 2560, 320):
        c.put(c.mask(lambda p: p.rect(x - 10, CEILING, x + 10, CEILING + 10)), STEEL_DARK)
        c.put(c.mask(lambda p: p.ellipse(x, CEILING + 12, 8, 5)), RED)
        c.light(c.mask(lambda p: p.poly([(x - 10, CEILING + 14), (x + 10, CEILING + 14), (x + 70, CEILING + 260), (x - 70, CEILING + 260)]), blur=18), RED, 0.2)
    # The deck torn up at each hole, the cables severed over it and arcing.
    for h0, h1 in HOLES:
        for x, d in ((h0, 1), (h1, -1)):
            c.put(c.mask(lambda p: p.poly([(x - d * 30, FLOOR), (x, FLOOR), (x + d * 10, FLOOR - 26), (x - d * 6, FLOOR - 30)])), HULL_DARK)
            c.put(c.mask(lambda p: p.line([(x - d * 30, FLOOR), (x + d * 10, FLOOR - 26)], 1.2)), STEEL_LIGHT)
        mid = (h0 + h1) / 2
        ends = [(mid - 30, FLOOR - 120), (mid + 6, FLOOR - 80), (mid + 34, FLOOR - 150)]
        c.put(c.mask(lambda p: [p.line([(x + rng.uniform(-30, 30), CEILING), (x, y)], 4) for x, y in ends]), CABLE)
        c.put(c.mask(lambda p: [p.ellipse(x, y, 4) for x, y in ends]), (180, 120, 60))
        for x, y in ends[:2]:
            arc = bolt(rng, (x, y + 2), (x + rng.uniform(-30, 30), FLOOR + 20))
            c.light(c.mask(lambda p: p.line(arc, 6), blur=5), ARC, 0.6)
            c.put(c.mask(lambda p: p.line(arc, 1.4)), (250, 252, 255))
    # The bulkhead: buckled plate, its blast door jammed half shut.
    k0, k1, kb = BULKHEAD
    plate(c, k0, CEILING, k1, kb, STEEL, "bulkhead", seams=22)
    c.put(c.mask(lambda p: p.poly([(k0, kb - 120), (k1, kb - 150), (k1, kb - 110), (k0, kb - 90)])), STEEL_DARK)
    c.put(c.mask(lambda p: [p.rect(x, kb - 14, x + 16, kb) for x in range(k0, k1, 32)]), AMBER)
    c.put(c.mask(lambda p: p.line([(k0, kb), (k1, kb)], 2)), STEEL_LIGHT)
    # The crew's mess by their cache: a table tipped, trays, a mug, a calendar.
    tx = 2120
    c.put(c.mask(lambda p: (p.poly([(tx, FLOOR), (tx + 10, FLOOR), (tx + 70, FLOOR - 60), (tx + 60, FLOOR - 66)]), p.rect(tx + 40, FLOOR - 10, tx + 110, FLOOR - 4))), STEEL_LIGHT)
    c.put(c.mask(lambda p: [p.poly([(x, FLOOR), (x + 22, FLOOR), (x + 20, FLOOR - 3), (x + 2, FLOOR - 3)]) for x in (2190, 2216)]), (196, 120, 60))
    c.put(c.mask(lambda p: (p.rect(2244, FLOOR - 10, 2254, FLOOR), p.ring(2257, FLOOR - 5, 3, 1.2))), (230, 230, 236))
    c.put(c.mask(box(2160, 560, 2210, 620)), (236, 232, 220))
    c.put(c.mask(box(2160, 560, 2210, 572)), RED)
    c.put(c.mask(lambda p: [p.rect(2164 + (i % 7) * 6.5, 576 + (i // 7) * 8, 2168 + (i % 7) * 6.5, 580 + (i // 7) * 8) for i in range(28)]), (120, 120, 130))
    c.put(c.mask(lambda p: p.ring(2164 + 3 * 6.5 + 2, 576 + 2 * 8 + 2, 4, 1.2)), RED)
    c.light(c.mask(lambda p: p.ellipse(2400, 790, 40), blur=10), CYAN, 0.25)


PIECES: Dict[str, Piece] = {
    "spur_west": Piece((16, CEILING, 1280, FLOOR + 32), spur),
    "spur_east": Piece((1280, CEILING, 2544, FLOOR + 32), spur),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
