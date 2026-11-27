"""The viewing balcony and its steps in the Echo Chamber."""

from __future__ import annotations

from ._district_props import Piece, targets
from ._town_kit import box
from .neural_props import NODE, PAL, PANEL, PANEL_LIGHT, TRACE, VIOLET


SEATS = ((256, 384, 448), (400, 512, 384), (864, 976, 384), (992, 1120, 448))
BALCONY = (528, 848, 320)
FLOOR = 512


def viewing_balcony(canvas, _kit):
    """Draw the two approaches and mark where Echo speaks."""
    left, right, top = BALCONY
    for x in (left + 16, right - 16):
        canvas.put(canvas.mask(box(x - 4, top, x + 4, FLOOR)), PANEL)
        canvas.put(canvas.mask(box(x - 3, top, x - 1, FLOOR)), PANEL_LIGHT)
    speaking_area = canvas.mask(lambda pen: pen.ellipse(640, 503, 73, 7))
    speaking_ring = speaking_area - canvas.mask(lambda pen: pen.ellipse(640, 503, 69, 5))
    canvas.put(speaking_area, PANEL)
    canvas.put(speaking_ring, VIOLET, 0.8)
    for x0, x1, y in (*SEATS, BALCONY):
        bevel = min(22, (x1 - x0) // 5)
        canvas.put(canvas.mask(lambda pen: pen.poly(
            [(x0, y), (x1, y), (x1 - bevel, y + 21), (x0 + bevel, y + 21)]
        )), PANEL)
        canvas.put(canvas.mask(box(x0, y + 3, x1, y + 8)), PANEL_LIGHT)
        canvas.put(canvas.mask(box(x0, y, x1, y + 2)), TRACE)
        for x in range(x0 + 22, x1 - 14, 28):
            canvas.put(canvas.mask(lambda pen: pen.ellipse(x, y + 13, 2)), NODE)
    canvas.put(canvas.mask(box(left + 12, top - 21, right - 12, top - 18)), PANEL_LIGHT)
    canvas.put(canvas.mask(lambda pen: [pen.rect(x, top - 19, x + 3, top)
                                      for x in range(left + 14, right - 10, 25)]), TRACE, 0.6)


TARGETS = targets({
    "neural_echo_viewing_balcony": Piece((240, 268, 1136, 514), viewing_balcony),
}, PAL)
