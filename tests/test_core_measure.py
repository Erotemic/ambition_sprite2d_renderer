"""Tests for the canonical body/feet measurement."""
from __future__ import annotations

from PIL import Image

from ambition_sprite2d_renderer.core.measure import measure_body_metrics


def test_transparent_frame_returns_none():
    assert measure_body_metrics(Image.new("RGBA", (64, 64), (0, 0, 0, 0))) is None


def test_feet_is_inclusive_last_opaque_row():
    # Opaque block rows [10, 40) → last opaque row is 39 (inclusive), not 40.
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    for y in range(10, 40):
        for x in range(20, 44):
            img.putpixel((x, y), (255, 0, 0, 255))
    m = measure_body_metrics(img)
    assert m["body_pixel_bbox"] == {"x": 20, "y": 10, "w": 24, "h": 30}
    assert m["feet_pixel"]["y"] == 39  # inclusive, matches the door "lowest pixel"
    # centre x of [20,44): (20 + 44 - 1) / 2 = 31.5
    assert m["feet_pixel"]["x"] == 31.5
    # anchor: 0.5 - 39/64
    assert abs(m["feet_anchor_norm"]["y"] - (0.5 - 39 / 64)) < 1e-9


def test_the_resampling_fringe_under_the_feet_is_not_body():
    # A frame downsampled with LANCZOS leaves near-transparent rows under an
    # opaque edge (Sanic's soles: alpha 15, 4, 1). A body that counted them
    # stood its drawn feet 3 px above the floor.
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    for y in range(10, 40):
        for x in range(20, 44):
            img.putpixel((x, y), (255, 0, 0, 255))
    for y, alpha in ((40, 15), (41, 4), (42, 1)):
        for x in range(24, 40):
            img.putpixel((x, y), (255, 0, 0, alpha))
    m = measure_body_metrics(img)
    assert m["body_pixel_bbox"] == {"x": 20, "y": 10, "w": 24, "h": 30}
    assert m["feet_pixel"]["y"] == 39
