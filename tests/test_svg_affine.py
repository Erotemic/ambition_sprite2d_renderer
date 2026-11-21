"""SVG point placement and reference units share one mathematical contract."""

import xml.etree.ElementTree as ET

import pytest

from ambition_sprite2d_renderer.svg_affine import length_to_reference_px, transform_matrix
from ambition_sprite2d_renderer.authoring import motion_ir
from ambition_sprite2d_renderer.devtools import svg_rig_tool


@pytest.mark.parametrize("transform, point, expected", [
    (None, (2, 3), (2, 3)),
    ("matrix(1 2 3 4 5 6)", (2, 3), (16, 22)),
    ("translate(5)", (2, 3), (7, 3)),
    ("translate(5 -2) scale(2 3)", (2, 3), (9, 7)),
    ("scale(2)", (2, 3), (4, 6)),
    ("rotate(90)", (2, 3), (-3, 2)),
    ("rotate(90 2 3)", (3, 3), (2, 4)),
    ("skewX(45)", (2, 3), (5, 3)),
    ("skewY(45)", (2, 3), (2, 5)),
])
def test_transform_point(transform, point, expected):
    a, b, c, d, e, f = transform_matrix(transform)
    x, y = point
    assert (a*x + c*y + e, b*x + d*y + f) == pytest.approx(expected)


@pytest.mark.parametrize("raw, expected", [
    ("2", 2), ("2px", 2), ("25.4mm", 96), ("2.54cm", 96),
    ("1in", 96), ("72pt", 96), ("6pc", 96), ("1e2px", 100),
    (None, None), ("20%", None), ("invalid", None),
])
def test_reference_units(raw, expected):
    result = length_to_reference_px(raw, dpi=96)
    assert result == (pytest.approx(expected) if expected is not None else None)


@pytest.mark.parametrize("consumer", [motion_ir, svg_rig_tool])
def test_nested_marker_placement(consumer):
    root = ET.fromstring('<svg><g transform="translate(10 20)"><g transform="scale(2 3)">'
                         '<circle id="joint" cx="2" cy="3" transform="rotate(90)"/>'
                         '</g></g></svg>')
    marker = root.find('.//circle')
    assert consumer._element_point_in_root(root, marker) == pytest.approx((4, 26))


def test_unsupported_transform_is_rejected():
    with pytest.raises(ValueError):
        transform_matrix("translate(1 2 3)")
