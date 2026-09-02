"""The clipping guard's blind spot: flat art seated flush does not taper either.

D129. `clipped_frame_edges` infers truncation from the silhouette — "a truncated
shape does not TAPER" — which is the best a guard can do for art DRAWN INTO the
canvas, where overflow is genuinely lost at that moment.

⛔ It cannot see one case, and that case is the playable protagonist.
`bottom_center_canvas` seats a finished 24x32 logical sprite on the frame's last
row, so a flat pixel-art foot is a full-width run at the boundary — to a taper
test, indistinguishable from a cut. The 2026-08-31 sweep counted 41 such frames
across six Mary-O forms, and the row's own conclusion was that inflating those
canvases would move every Mary-O sprite's ground contact to silence a false
positive.

⇒ A composited frame does not need to be guessed at. The sprite existed WHOLE
before the frame did, so whether anything was lost is known exactly, and the
compositor is the one place that knows. It marks the frames it did not cut.
"""

from PIL import Image, ImageDraw

from ambition_sprite2d_renderer.authoring.sheet_build import clipped_frame_edges
from ambition_sprite2d_renderer.targets.super_mary_o_common import (
    COMPOSITED_WHOLE,
    bottom_center_canvas,
)


def _flat_footed_sprite() -> Image.Image:
    """A 24x32 logical sprite with a flat bottom — the shape that cries wolf."""
    sprite = Image.new("RGBA", (24, 32), (0, 0, 0, 0))
    ImageDraw.Draw(sprite).rectangle([4, 0, 19, 31], fill=(255, 0, 0, 255))
    return sprite


def test_flush_seated_pixel_art_is_not_reported_as_clipped():
    frame = bottom_center_canvas(_flat_footed_sprite(), (48, 48))
    assert frame.info.get(COMPOSITED_WHOLE) is True, "premise: the sprite fitted"
    assert clipped_frame_edges(frame) == []


def test_the_same_pixels_unmarked_still_read_as_a_cut():
    """⭐ THE POINT, and why the marker is a FACT rather than a suppression.

    Identical pixels. The taper rule cannot separate these two; only knowing how
    the frame was built can. If this ever goes green the marker has stopped
    carrying information and the exemption above is hiding real cuts.
    """
    frame = bottom_center_canvas(_flat_footed_sprite(), (48, 48))
    unmarked = frame.copy()
    unmarked.info.clear()
    assert clipped_frame_edges(unmarked) == ["bottom"]


def test_a_composite_that_did_not_fit_is_still_reported():
    """⛔ `alpha_composite` CLIPS. The helper can truncate like any other road,
    so it marks only what it did not cut — otherwise this would be a blanket
    exemption for every target that happens to use it."""
    too_tall = Image.new("RGBA", (64, 64), (255, 0, 0, 255))
    frame = bottom_center_canvas(too_tall, (48, 48))
    assert frame.info.get(COMPOSITED_WHOLE) is None, "a cut composite must not be marked"
    assert clipped_frame_edges(frame), "and the guard must still report it"


def test_an_offset_that_pushes_the_sprite_out_is_still_reported():
    sprite = _flat_footed_sprite()
    frame = bottom_center_canvas(sprite, (48, 48), offset_y=10)
    assert frame.info.get(COMPOSITED_WHOLE) is None
    assert clipped_frame_edges(frame)


def test_art_drawn_into_the_canvas_is_unaffected():
    """The guard's real job is untouched: a shape that arrives at the boundary
    already near full width is still a cut."""
    frame = Image.new("RGBA", (48, 48), (0, 0, 0, 0))
    ImageDraw.Draw(frame).rectangle([0, 30, 47, 47], fill=(255, 0, 0, 255))
    assert "bottom" in clipped_frame_edges(frame)
