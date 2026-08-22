"""Tests for detecting artwork clipped by the logical frame boundary.

Touching a frame edge is not itself clipping because auto-crop may fit a frame
tightly around valid art. The detector instead looks for a flat opaque run at the
boundary, distinguishing truncated geometry from a naturally tapering tip."""

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


def test_super_sanics_raised_spikes_fit_inside_their_frame():
    """Super Sanic's raised spikes must fit without changing base Sanic.

    Check representative idle/walk/run frames rather than the full sheet. Base
    Sanic is the control so shrinking all spikes or globally growing the frame
    cannot satisfy the regression test.
    checked.
    """
    from ambition_sprite2d_renderer.targets.characters import sanic

    rows = {name: count for name, count, *_ in sanic.ROWS}
    for skin_name, skin in (("sanic", sanic.NORMAL), ("super_sanic", sanic.SUPER_SKIN)):
        for anim in ("idle", "walk", "run"):
            frame = sanic._draw_sanic(skin, anim, 0, rows[anim])
            assert clipped_frame_edges(frame) == [], (
                f"{skin_name} {anim}#0 is CUT at {clipped_frame_edges(frame)}. "
                "Art drawn past the logical frame is lost at draw time, not "
                "shrunk — see `SUPER_SPIKE_FIT` for the measured reach that fits."
            )
