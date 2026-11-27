"""The entrance steps and the balcony above the Wet Whistle bar."""

from __future__ import annotations

from ._district_props import Piece, targets
from ._town_kit import box
from .frontier_props import GLOW, PAL, PLANK, PLANK_DARK, PLANK_LIGHT, TIMBER, deck_edge, planks, post


def balcony_walk(canvas, kit):
    """Draw the steps, the balcony extension, and the bar top."""
    kit.ground = 512
    for left, right, top in ((144, 224, 448), (176, 240, 400)):
        for x in (left + 9, right - 9):
            post(canvas, x, top, 512, 4)
        canvas.put(canvas.mask(box(left, top, right, top + 12)), TIMBER)
        deck_edge(canvas, left, right, top, PLANK_LIGHT)
    for x in (702, 974):
        post(canvas, x, 352, 432, 6)
    kit.balcony(688, 992, 352, PLANK, rail=TIMBER)
    deck_edge(canvas, 784, 992, 432, PLANK_LIGHT)
    for x in (744, 915):
        canvas.put(canvas.mask(box(x - 3, 365, x + 3, 370)), TIMBER)
        canvas.light(canvas.mask(lambda pen: pen.ellipse(x, 375, 25, 13), blur=9), GLOW, 0.3)
        canvas.put(canvas.mask(lambda pen: pen.ellipse(x, 371, 4, 3)), GLOW)
    planks(canvas, None, 1008, 464, 1264, 512, PLANK, step=7.0, vertical=True, tag="stage")
    canvas.put(canvas.mask(box(1008, 506, 1264, 512)), PLANK_DARK)
    deck_edge(canvas, 1008, 1264, 464, PLANK_LIGHT)


TARGETS = targets({
    "frontier_saloon_balcony_walk": Piece((128, 318, 1266, 514), balcony_walk),
}, PAL)
