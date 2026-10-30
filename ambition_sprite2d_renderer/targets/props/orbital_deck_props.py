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

Animations: ``idle``, 1 frame. No drop shadows.
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


PIECES: Dict[str, Piece] = {
    "obs_deck_window": Piece((16, CEILING, 1584, FLOOR), window),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
