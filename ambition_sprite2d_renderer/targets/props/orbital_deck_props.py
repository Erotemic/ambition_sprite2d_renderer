"""The orbital station's observation deck (`orbital_station_observation_deck`,
the Science dimension): the window the deck is for.

Drawn in room coordinates (`_district_props`) on the level's own numbers
(edited in place: `tools/ambition_ldtk_tools/specs/scenery_overlay.py`): the
floor (y 704), the ceiling (to y 48), the doors (x 48 and 1488), the benches
(x 360..520 and 960..1120), which this piece is drawn over and keeps clear of.

- `obs_deck_window`: a panoramic window on the planet: a hull frame round
  it, its mullions, the faintest glass with a reflection across it (the view
  behind is the room's), and two coin-op viewers on posts between the
  benches and the doors, which show the planet a little closer for a coin.

- `svc_clutter` (the service deck, its free wall x 1290..2100): lockers
  (one open on a spacesuit), a vending machine, the robots' charging dock,
  DAYS WITHOUT INCIDENT at zero, a mop and the wet floor's sign.

Animations: ``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .orbital_station import AMBER, HULL, HULL_DARK, HULL_LIGHT, PX, STEEL, STEEL_DARK, STEEL_LIGHT, plate

FLOOR, CEILING = 704, 48
WIN = (60, 96, 1540, 590)
PAL = {"stone": HULL, "stone_light": HULL_LIGHT, "dark": STEEL_DARK, "lamp": AMBER}
GLASS = (170, 210, 240)


def window(c, k):
    x0, y0, x1, y1 = WIN
    # The frame: hull plate round the window, the glass left clear.
    frame = c.mask(box(16, CEILING, 1584, y1 + 24)) * (1 - c.mask(lambda p: p.rect(x0, y0, x1, y1)))
    c.put(frame, HULL_DARK)
    c.put(frame * c.mask(lambda p: [p.rect(x, CEILING, x + 0.8, y1 + 24) for x in range(16, 1584, 40)]), scale(HULL_DARK, 0.8))
    c.put(c.mask(box(x0 - 6, y0 - 6, x1 + 6, y0)), STEEL_LIGHT)
    c.put(c.mask(box(x0 - 6, y1, x1 + 6, y1 + 8)), STEEL_LIGHT)
    # Mullions, and the faintest glass with a reflection across it.
    c.put(c.mask(lambda p: [p.rect(x - 4, y0, x + 4, y1) for x in range(x0 + 185, x1, 185)]), STEEL)
    glass = c.mask(box(x0, y0, x1, y1))
    c.put(glass, GLASS, 0.06)
    c.light(c.mask(lambda p: [p.poly([(x, y1), (x + 50, y1), (x + 260, y0), (x + 210, y0)]) for x in range(x0 - 200, x1, 560)], blur=6) * glass,
            (255, 255, 255), 0.08)
    # Lamps along the sill.
    c.put(c.mask(lambda p: [p.ellipse(x, y1 + 16, 3) for x in range(x0 + 40, x1, 120)]), AMBER)
    # Two coin-op viewers on posts.
    for vx in (240, 1320):
        c.put(c.mask(box(vx - 4, FLOOR - 70, vx + 4, FLOOR)), STEEL_DARK)
        c.put(c.mask(lambda p: (p.rect(vx - 16, FLOOR - 4, vx + 16, FLOOR), p.ellipse(vx, FLOOR - 82, 18, 14))), STEEL)
        c.put(c.mask(lambda p: [p.ellipse(vx + 14, FLOOR - 86 + d, 5, 4) for d in (-4, 6)]), STEEL_DARK)
        c.put(c.mask(lambda p: p.rect(vx - 6, FLOOR - 74, vx + 2, FLOOR - 70)), AMBER)


#: The service deck's floor; its free wall between the cargo lift's door
#: (to x 1248) and the habitation door (from x 2128).
SVC_FLOOR = 832


def service_clutter(c, k):
    g = SVC_FLOOR
    # Lockers, one ajar on a spacesuit.
    for i, x in enumerate(range(1300, 1460, 40)):
        plate(c, x, g - 150, x + 38, g, (90, 110, 130), ("locker", i), seams=0)
        c.put(c.mask(lambda p: [p.rect(x + 10, y, x + 28, y + 2) for y in (g - 140, g - 134, g - 128)]), STEEL_DARK)
        c.put(c.mask(lambda p: p.rect(x + 30, g - 80, x + 33, g - 66)), STEEL_LIGHT)
    sx = 1420
    c.put(c.mask(box(sx, g - 150, sx + 38, g)), (20, 24, 32))
    c.put(c.mask(lambda p: (p.ellipse(sx + 19, g - 126, 12, 13), p.rect(sx + 8, g - 112, sx + 30, g - 50), p.rect(sx + 10, g - 50, sx + 18, g - 8), p.rect(sx + 20, g - 50, sx + 28, g - 8))), (230, 230, 226))
    c.put(c.mask(lambda p: p.ellipse(sx + 19, g - 126, 8, 7)), (60, 120, 160))
    c.put(c.mask(lambda p: p.poly([(sx + 38, g - 150), (sx + 62, g - 160), (sx + 62, g + 4), (sx + 38, g)])), (100, 120, 140))
    # The vending machine, lit.
    vx = 1520
    plate(c, vx, g - 180, vx + 84, g, (170, 40, 50), "vending", seams=0)
    glass = c.mask(box(vx + 8, g - 170, vx + 58, g - 60))
    c.put(glass, (30, 40, 60))
    c.light(glass, (200, 230, 255), 0.25)
    cols = [(240, 200, 80), (120, 200, 120), (230, 120, 80), (200, 200, 220)]
    c.put(c.mask(lambda p: [p.rect(vx + 12 + j * 11, y, vx + 20 + j * 11, y + 12) for y in range(int(g - 164), int(g - 70), 22) for j in range(4)]), cols[0])
    c.put(c.mask(lambda p: [p.rect(vx + 12 + j * 22, y, vx + 20 + j * 22, y + 12) for y in range(int(g - 164), int(g - 70), 22) for j in range(2)]), cols[1])
    c.put(c.mask(lambda p: (p.rect(vx + 64, g - 150, vx + 76, g - 120), p.rect(vx + 14, g - 44, vx + 54, g - 30))), STEEL_DARK)
    # The robots' charging dock: a pad, a plug, a gauge.
    dx = 1660
    c.put(c.mask(lambda p: (p.rect(dx, g - 8, dx + 90, g), p.rect(dx + 80, g - 120, dx + 92, g - 8))), STEEL)
    c.put(c.mask(lambda p: p.rect(dx + 10, g - 4, dx + 70, g - 2)), (90, 220, 140))
    c.light(c.mask(lambda p: p.ellipse(dx + 40, g - 6, 50, 10), blur=6), (90, 220, 140), 0.4)
    c.put(c.mask(lambda p: p.line([(dx + 80, g - 100), (dx + 60, g - 90), (dx + 56, g - 60)], 3)), (40, 40, 44))
    c.put(c.mask(box(dx + 50, g - 64, dx + 62, g - 54)), (40, 40, 44))
    c.put(c.mask(box(dx + 84, g - 112, dx + 90, g - 80)), (20, 24, 30))
    c.put(c.mask(lambda p: [p.rect(dx + 85, y, dx + 89, y + 5) for y in (g - 110, g - 103, g - 96, g - 89)]), (90, 220, 140))
    # DAYS WITHOUT INCIDENT: a zero, in lights.
    bx0, by0 = 1810, g - 250
    c.put(c.mask(box(bx0, by0, bx0 + 150, by0 + 90)), (24, 28, 36))
    c.put(c.mask(box(bx0, by0, bx0 + 150, by0 + 14)), (230, 190, 60))
    c.put(c.mask(lambda p: p.ring(bx0 + 75, by0 + 52, 22, 5)), AMBER)
    c.light(c.mask(lambda p: p.ellipse(bx0 + 75, by0 + 52, 36), blur=8), AMBER, 0.3)
    # A mop in its bucket, the wet floor's sign.
    c.put(c.mask(lambda p: (p.poly([(1990, g), (2026, g), (2030, g - 30), (1986, g - 30)]), p.line([(2008, g - 30), (2020, g - 110)], 3))), (220, 190, 60))
    c.put(c.mask(lambda p: p.poly([(2050, g), (2062, g - 50), (2074, g)])), (240, 210, 60))
    c.put(c.mask(lambda p: p.poly([(2059, g - 26), (2065, g - 26), (2062, g - 36)])), (40, 40, 44))


PIECES: Dict[str, Piece] = {
    "svc_clutter": Piece((1290, 560, 2100, SVC_FLOOR), service_clutter),
    "obs_deck_window": Piece((16, CEILING, 1584, FLOOR), window),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
