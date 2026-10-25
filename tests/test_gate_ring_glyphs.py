"""The gate ring's glyphs: feet toward the centre, none in the base's slice."""

from __future__ import annotations

import math

from ambition_sprite2d_renderer.glyphs.legally_distinct import GLYPHS
from ambition_sprite2d_renderer.targets.props import interdimensional_gate as gate


def test_each_glyph_stands_on_the_ray_from_the_centre():
    for glyph in GLYPHS:
        placement = gate._placement(glyph.index)
        ray = math.radians(gate._plaque_angle(glyph.index))
        turn = math.radians(placement.angle_deg)
        # A glyph's up is (0, -1) before it turns (y down); turned clockwise,
        # it must point out along the ray, so its baseline is square to it
        # and its foot faces the centre.
        up = (math.sin(turn), -math.cos(turn))
        assert math.isclose(up[0], math.cos(ray), abs_tol=1e-9), glyph.id
        assert math.isclose(up[1], math.sin(ray), abs_tol=1e-9), glyph.id


def test_no_plaque_in_the_bottom_slice_and_the_inscription_reads_over_the_top():
    for glyph in GLYPHS:
        from_bottom = abs((gate._plaque_angle(glyph.index) - 90.0 + 180.0) % 360.0 - 180.0)
        assert from_bottom >= gate.BASE_GAP_DEG / 2.0 - 1e-9, glyph.id
    # Clockwise from the lower left: the first plaque is left of centre, the
    # middle one at 12 o'clock, the last right of centre.
    assert math.cos(math.radians(gate._plaque_angle(0))) < 0
    assert math.isclose(gate._plaque_angle(7) % 360.0, 270.0)
    assert math.cos(math.radians(gate._plaque_angle(14))) > 0
