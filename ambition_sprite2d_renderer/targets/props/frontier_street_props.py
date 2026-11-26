"""The service walks from Bell's Livery to the water tower."""

from __future__ import annotations

from ._district_props import Piece, targets
from ._town_kit import box
from .frontier_props import HULL_ORANGE, PAL, PLANK, PLANK_LIGHT, STEEL_DARK, TIMBER, crate, deck_edge


def tower_service_walk(canvas, _kit):
    """Draw the pump pipe, the walks, and the crate on the boardwalk."""
    pipe = [(1440, 419), (1484, 423), (1560, 423), (1578, 442),
            (1578, 518), (1606, 542), (1606, 608)]
    canvas.put(canvas.mask(lambda pen: pen.line(pipe, 9)), STEEL_DARK)
    canvas.put(canvas.mask(lambda pen: pen.line(pipe, 4)), HULL_ORANGE)
    for left, right, top in ((1456, 1568, 416), (1584, 1680, 464)):
        canvas.put(canvas.mask(lambda pen: pen.line(
            [(left + 8, top + 5), (left + 26, top + 14), (right - 24, top + 14),
             (right - 6, top + 5)], 4
        )), STEEL_DARK)
        canvas.put(canvas.mask(box(left, top, right, top + 8)), PLANK)
        deck_edge(canvas, left, right, top, PLANK_LIGHT)
        canvas.put(canvas.mask(lambda pen: pen.line(
            [(left + 23, top), (left + 23, top - 18),
             (right - 20, top - 18), (right - 20, top)], 2
        )), TIMBER)
    crate(canvas, 1620, 544, 1708, 608, PLANK)
    deck_edge(canvas, 1616, 1712, 544, PLANK_LIGHT)


TARGETS = targets({
    "frontier_water_tower_service_walk": Piece((1436, 386, 1722, 616), tower_service_walk),
}, PAL)
