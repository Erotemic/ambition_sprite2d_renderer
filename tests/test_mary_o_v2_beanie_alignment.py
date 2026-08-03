from __future__ import annotations

import pytest
from PIL import Image

from ambition_sprite2d_renderer.targets.characters import mary_o_v2
from ambition_sprite2d_renderer.targets.characters._mary_o_v2_art import (
    _debug_part_image,
    _draw_head_foundation_side,
    _ellipse_dome_points,
)

_SCALE = 12
_HEAD_X = 4.0
_HEAD_Y = 2.0


def _matching_x_values(
    image: Image.Image,
    *,
    colors: set[tuple[int, int, int, int]],
    y1: int,
    y2: int,
) -> list[int]:
    pixels = image.load()
    return [
        x
        for y in range(y1, y2 + 1)
        for x in range(image.width)
        if pixels[x, y] in colors
    ]


@pytest.mark.parametrize("lookback", [False, True])
def test_side_forehead_edge_is_inline_with_beanie_edge(lookback: bool) -> None:
    """The visible beanie edge should continue directly into the forehead."""
    form = mary_o_v2.SHORT_FORM
    image = _debug_part_image(
        lambda px: _draw_head_foundation_side(
            px,
            form,
            _HEAD_X,
            _HEAD_Y,
            lookback=lookback,
        ),
        logical_size=(20, 18),
        scale=_SCALE,
    )

    # Measure the beanie's lower edge where it meets the face, then compare it
    # with the straight forehead segment immediately below. Using rendered fill
    # colors makes this a visual-output regression rather than a check of the
    # current implementation's coordinate constants.
    beanie_x_values = _matching_x_values(
        image,
        colors={form.palette.cap, form.palette.accent},
        y1=round((_HEAD_Y + 3.25) * _SCALE),
        y2=round((_HEAD_Y + 4.70) * _SCALE),
    )
    forehead_x_values = _matching_x_values(
        image,
        colors={form.palette.skin},
        y1=round((_HEAD_Y + 5.05) * _SCALE),
        y2=round((_HEAD_Y + 7.00) * _SCALE),
    )
    assert beanie_x_values
    assert forehead_x_values

    if lookback:
        beanie_edge_x = min(beanie_x_values)
        forehead_edge_x = min(forehead_x_values)
    else:
        beanie_edge_x = max(beanie_x_values)
        forehead_edge_x = max(forehead_x_values)

    delta_px = abs(beanie_edge_x - forehead_edge_x)
    assert delta_px <= 1, (
        "The side-view beanie and forehead edges are not inline: "
        f"beanie x={beanie_edge_x}, forehead x={forehead_edge_x}, "
        f"delta={delta_px}px ({delta_px / _SCALE:.2f} logical pixels), "
        f"lookback={lookback}."
    )


def test_side_beanie_top_reads_as_a_dome() -> None:
    """The cap crown should broaden rapidly from a narrow curved top."""
    form = mary_o_v2.SHORT_FORM
    image = _debug_part_image(
        lambda px: _draw_head_foundation_side(
            px,
            form,
            _HEAD_X,
            _HEAD_Y,
            lookback=False,
        ),
        logical_size=(20, 18),
        scale=_SCALE,
    )
    pixels = image.load()

    def cap_span(local_y: float) -> int:
        y = round((_HEAD_Y + local_y) * _SCALE)
        xs = [
            x
            for x in range(image.width)
            if pixels[x, y] == form.palette.cap
        ]
        assert xs
        return max(xs) - min(xs) + 1

    top_span = cap_span(0.30)
    middle_span = cap_span(1.80)
    lower_span = cap_span(2.30)
    assert top_span <= middle_span * 0.60
    assert middle_span >= top_span + 30
    assert lower_span >= middle_span


def test_beanie_crown_is_a_literal_half_ellipse() -> None:
    """Every curved crown point should lie on one upper ellipse."""
    x1, top_y, x2, base_y = (1.05, -0.55, 8.95, 3.65)
    steps = 20
    points = _ellipse_dome_points(x1, top_y, x2, base_y, steps=steps)
    arc = points[: steps + 1]
    cx = (x1 + x2) * 0.5
    rx = (x2 - x1) * 0.5
    ry = base_y - top_y

    assert arc[0] == pytest.approx((x1, base_y))
    assert arc[-1] == pytest.approx((x2, base_y))
    assert arc[steps // 2] == pytest.approx((cx, top_y))
    for px, py in arc:
        ellipse_value = ((px - cx) / rx) ** 2 + ((py - base_y) / ry) ** 2
        assert ellipse_value == pytest.approx(1.0, abs=1e-9)
        assert py <= base_y + 1e-9

    # The final two points close the fill along the flat diameter; no lower
    # half of an ellipse is authored or hidden beneath the band.
    assert points[-2:] == pytest.approx([(x2, base_y), (x1, base_y)])
