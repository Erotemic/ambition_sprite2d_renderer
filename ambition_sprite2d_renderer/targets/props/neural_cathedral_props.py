"""The moving deck and its supports at the west end of the memory gallery."""

from __future__ import annotations

from ._district_props import Piece, targets
from ._town_kit import box
from .neural_props import DENDRITE, FLESH, FLESH_DARK, FLESH_LIGHT, PAL, SPARK, branch, glow_bulb


def lift_fibres(canvas, _kit):
    """Draw the fibres between the gallery and the floor."""
    for x in (484, 588):
        branch(canvas, [(x, 522), (x + 3, 626), (x - 2, 778),
                        (x + 1, 924), (x, 1024)], 6)
        branch(canvas, [(x + 6, 530), (x + 5, 674), (x + 8, 842), (x + 5, 1024)], 2)
        glow_bulb(canvas, x, 538, 5, SPARK)
        glow_bulb(canvas, x, 992, 5, SPARK)
    for y in (644, 752, 864, 968):
        glow_bulb(canvas, 484, y, 2, SPARK, 0.45)
        glow_bulb(canvas, 588, y, 2, SPARK, 0.45)
    branch(canvas, [(484, 522), (541, 518), (588, 522), (615, 545)], 11, DENDRITE)


def memory_lift(canvas, _kit):
    """Draw the deck with its top at y 10 and a span from x 8 to x 120."""
    deck = canvas.mask(lambda pen: pen.poly([(8, 10), (120, 10), (113, 23),
                                            (64, 33), (15, 23)]))
    canvas.put(deck, FLESH_DARK)
    canvas.put(canvas.mask(box(8, 10, 120, 17)), FLESH)
    canvas.put(canvas.mask(box(8, 10, 120, 12)), FLESH_LIGHT)
    for x in (26, 45, 64, 83, 102):
        glow_bulb(canvas, x, 23, 2, SPARK, 0.6)


TARGETS = targets({
    "neural_cathedral_lift_fibres": Piece((460, 510, 624, 1026), lift_fibres),
    "neural_cathedral_memory_lift": Piece((0, 0, 128, 40), memory_lift),
}, PAL)
