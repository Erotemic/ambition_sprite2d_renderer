"""The circuit walk between the logic gates and the Echo Chamber deck."""

from __future__ import annotations

from ._district_props import Piece, targets
from ._town_kit import box
from .neural_props import NODE, PAL, PANEL, PANEL_LIGHT, TRACE


WALK = ((1424, 1552, 832), (1600, 1728, 768), (1808, 1936, 704))


def circuit_walk(canvas, _kit):
    """Draw the pads, braces, and signal lines below the walk."""
    for left, right, top in WALK:
        canvas.put(canvas.mask(lambda pen: pen.poly(
            [(left, top), (right, top), (right - 10, top + 17), (left + 8, top + 17)]
        )), PANEL)
        canvas.put(canvas.mask(box(left, top, right, top + 3)), TRACE)
        canvas.put(canvas.mask(box(left + 6, top + 4, right - 6, top + 10)), PANEL_LIGHT)
        for x in (left + 14, right - 14):
            canvas.put(canvas.mask(lambda pen: pen.line(
                [(x, top + 16), (x, top + 30), (x + 14, top + 42)], 4
            )), PANEL_LIGHT)
            canvas.put(canvas.mask(lambda pen: pen.ellipse(x, top + 11, 2.5)), NODE)
        mid = (left + right) / 2
        canvas.put(canvas.mask(lambda pen: pen.poly(
            [(mid + 9, top + 10), (mid, top + 5), (mid, top + 15)]
        )), NODE)
    for points in (
        [(1404, 882), (1486, 882), (1550, 817), (1592, 817)],
        [(1730, 796), (1762, 796), (1812, 748), (1870, 748)],
        [(1940, 730), (1952, 730), (1976, 706), (1988, 706)],
    ):
        canvas.put(canvas.mask(lambda pen: pen.line(points, 2)), TRACE, 0.65)


TARGETS = targets({
    "neural_weights_circuit_walk": Piece((1392, 675, 2000, 896), circuit_walk),
}, PAL)
