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


def test_carl_stargans_ground_roll_stays_inside_his_frame():
    """The shared scientist roll dips BELOW the ground line, and one of the three
    sheets had no room for it.

    ⭐ MEASURED, not reasoned. `_common_clips` authors ONE `roll` for all three
    canonical scientist rigs, and every one of them puts the body 38-42px below
    its own `ground_y` at the tuck (frame 3). Emmy and the Patent Clerk both draw
    into their rig canvas PLUS `RIG_RENDER_PADDING`; Carl drew into the bare
    160x160 rig frame, so on his sheet alone the tuck was cut off — 8 frames
    across `roll`, `roll_back`, `tumble`, `spot_dodge`, `getup_roll`,
    `tech_roll`, `trip_roll` and `grab_escape`, which are the seven clips that
    CLONE that roll plus the tumble that shares its pose.

    ⛔ THE CONTROL IS `idle`, and it is not decoration: padding a canvas makes
    every clipping test easier to pass, so the fixture has to show the frame is
    still fitted to the character rather than merely enormous.
    """
    from ambition_sprite2d_renderer.targets.characters import carl_stargan

    rows = {name: count for name, count, *_ in carl_stargan.ROWS}
    # The tuck frame of every clip that clones the shared roll, plus the tumble
    # that shares its pose. Representative frames rather than the whole 953-frame
    # sheet: this is the pose that was lost, and the sweep is what finds a new one.
    for animation, frame_idx in (
        ("roll", 3),
        ("roll_back", 5),
        ("tumble", 3),
        ("spot_dodge", 3),
        ("getup_roll", 3),
        ("tech_roll", 3),
        ("trip_roll", 3),
        ("grab_escape", 3),
    ):
        frame = carl_stargan.render_frame(animation, frame_idx, rows[animation])
        assert clipped_frame_edges(frame) == [], (
            f"carl_stargan {animation}#{frame_idx} is CUT at "
            f"{clipped_frame_edges(frame)}. The roll tucks below his ground line "
            "and the drawing canvas has to hold it — see `RIG_RENDER_PADDING`, "
            "which is how `patent_clerk` and `noether` hold the same pose."
        )

    # ⛔ AND THE FRAME MUST STILL BE FITTED TO HIM. Padding a canvas makes every
    # clipping assertion above easier to pass, and a canvas grown until nothing
    # can reach its edge is not a fix — it is the guard being disabled with extra
    # steps. So the deepest pose has to arrive NEAR the bottom edge: the room was
    # sized to the pose, not the pose given a room.
    deepest = carl_stargan.render_frame("roll", 3, rows["roll"])
    bbox = deepest.getchannel("A").getbbox()
    assert bbox is not None, "the roll tuck frame is empty"
    slack = deepest.size[1] - bbox[3]
    assert slack <= 32, (
        f"carl_stargan's deepest pose stops {slack}px above the bottom of a "
        f"{deepest.size[0]}x{deepest.size[1]} frame. The padding is no longer a "
        "margin around the pose that needed it; every sheet frame carries that "
        "emptiness and the height contract scales it."
    )
