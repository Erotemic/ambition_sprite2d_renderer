"""The draw-time guard for art that runs off the logical frame.

Jon, 2026-08-16: *"Super sanics spikes are clipped by the sprite renderer. This
might need a structural fix. We should not be able to clip sprite artwork so
easily."* He was right on both counts — a roster scan found the same signature on
23 of 133 shipped sheets.

⭐ **why the naive test is wrong, and why this file exists.** "The art touches the
frame edge" flags **74** of those 133, because `render_sheet`'s auto-crop fits the
sheet's frame to the union alpha bbox — so touching the boundary often means the
frame was fitted to the art, not that the art was cut. The discriminator is the
shape of the edge: a real tip tapers up from nothing, a truncated one starts wide.
Measured on the shipped sheets, topmost-row opaque counts:

    super_sanic idle   12 14 17 18 20 22 24 25   <- no tip: CUT
    sanic       idle    0  0  0  0  3  6  8 11   <- a taper
    sanic       jump    0  0  0  0  0  0  0  0   <- touches, NOT cut

So the guard looks for a flat RUN along the boundary, and the cases below pin
both sides of that distinction rather than only the positive one.
"""

from PIL import Image, ImageDraw

from ambition_sprite2d_renderer.authoring.sheet_build import clipped_frame_edges


def blank(size: int = 64) -> Image.Image:
    return Image.new("RGBA", (size, size), (0, 0, 0, 0))


def test_a_clean_frame_reports_nothing():
    frame = blank()
    ImageDraw.Draw(frame).ellipse((20, 20, 44, 44), fill=(255, 0, 0, 255))
    assert clipped_frame_edges(frame) == []


def test_a_shape_cut_off_at_the_top_is_reported():
    """A wide band flush against the top edge — the super-Sanic signature."""
    frame = blank()
    ImageDraw.Draw(frame).rectangle((16, 0, 48, 40), fill=(255, 0, 0, 255))
    assert clipped_frame_edges(frame) == ["top"]


def test_a_tapering_tip_that_merely_touches_the_edge_is_not_a_cut():
    """⛔ THE POISON, and the one that decides whether this guard is usable.

    `sanic/jump` touches the boundary and is fine; a guard that cannot tell the
    difference reddens on 74 sheets, gets ignored, and is worse than nothing.
    """
    frame = blank()
    # A spike whose apex is a single pixel ON the top edge.
    ImageDraw.Draw(frame).polygon([(32, 0), (24, 40), (40, 40)], fill=(255, 0, 0, 255))
    assert clipped_frame_edges(frame) == []


def test_every_edge_is_checked_not_just_the_top():
    """`puppy_slug` is cut on three edges at once; a top-only check misses it."""
    frame = blank()
    draw = ImageDraw.Draw(frame)
    draw.rectangle((0, 20, 30, 44), fill=(255, 0, 0, 255))  # left
    draw.rectangle((20, 33, 63, 50), fill=(255, 0, 0, 255))  # right
    draw.rectangle((16, 40, 48, 63), fill=(255, 0, 0, 255))  # bottom
    assert clipped_frame_edges(frame) == ["bottom", "left", "right"]


def test_a_nearly_transparent_edge_is_not_a_cut():
    """Anti-aliased or ghosted art brushing the edge is not lost art.

    The alpha threshold is what keeps a soft glow from reading as a truncation,
    and several sheets carry exactly that kind of aura.
    """
    frame = blank()
    ImageDraw.Draw(frame).rectangle((16, 0, 48, 40), fill=(255, 0, 0, 60))
    assert clipped_frame_edges(frame) == []


def test_a_short_run_is_not_a_cut():
    """Below the run threshold: a few pixels is a detail, not a severed shape."""
    frame = blank()
    ImageDraw.Draw(frame).rectangle((30, 0, 33, 20), fill=(255, 0, 0, 255))
    assert clipped_frame_edges(frame) == []


def test_a_degenerate_frame_answers_rather_than_raising():
    """A 1px frame has no interior; the guard must not be the thing that fails."""
    assert clipped_frame_edges(Image.new("RGBA", (1, 1), (255, 0, 0, 255))) == []
