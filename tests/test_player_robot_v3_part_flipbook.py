"""Player robot v3 is drawn from parts (the plan is
`docs/planning/engine/mary-o-part-realization.md` in the game repository; the
robot is its second character).

The robot exercises what Mary-O does not:

* his rig is SUPERSAMPLED (4x, reduced once per frame), so no part lands on a
  whole frame pixel. Each part is reduced on its own and placed exactly,
  between pixels: a CONTINUOUS flipbook (``PartFlipbook.placement``);
* his other side is a MIRRORED row, drawn as mirrored draws of the same parts;
* his smash blade FADES on its own (a draw's opacity), and his death fades the
  whole body AS ONE PICTURE (a frame's opacity);
* his blink is a sliced body, carried as one overlay per frame.

A continuous replay is not the same picture as the render to the bit: the
render composites at 4x and reduces once, the replay reduces each part and
composites. So the comparison forgives 64 levels but NO place
(``part_flipbook.CONTINUOUS_REPLAY_TOLERANCE``): the usual pixel of slack
forgave the robot's head drawn a pixel off. Bounded as the in-engine gate is
(A <= 1%, B <= 6 px). The publish runs the same check on every frame
(``build_rig_flipbook``), so this test holds a sample of rows that covers each
mechanism, and the poisons that prove the measure sees each one go wrong.
"""

from __future__ import annotations

import dataclasses

import pytest
from PIL import Image

from ambition_sprite2d_renderer.authoring import part_flipbook, rigdoc
from ambition_sprite2d_renderer.authoring.part_flipbook import (
    CONTINUOUS_REPLAY_TOLERANCE as TOLERANCE,
    PLACEMENT_CONTINUOUS,
    PartFlipbook,
    build_rig_flipbook,
    largest_wrong_blob,
    parity,
)
from ambition_sprite2d_renderer.targets.characters import player_robot_v3 as robot

PARITY_BOUND = 0.01
BLOB_BOUND = 6

#: One row per mechanism: rigid parts (idle), a tweened loop and its mirror
#: (walk), a frame fade (death), a sliced body (blink_out), a blurred effect
#: layer (hover), a faded part and its mirror (smash_forward), a translucent
#: shield over the body (block).
SAMPLE = (
    "idle",
    "walk",
    "walk~mirrored",
    "death",
    "blink_out",
    "hover",
    "smash_forward",
    "smash_forward~mirrored",
    "block",
)


@pytest.fixture(scope="module")
def sample():
    rows = [row for row in robot.ROWS if row[0] in SAMPLE]
    assert sorted(name for name, _n, _ms in rows) == sorted(SAMPLE)
    size = (robot.FRAME_SIZE[0] + 32, robot.FRAME_SIZE[1] + 32)
    feet = robot.body_metrics(*size)["feet_pixel"]
    tweened = [name for name in robot.TWEENED_ROWS if name in SAMPLE]
    flipbook = build_rig_flipbook(robot.TARGET_NAME, rows, robot.published_frame, None, (feet["x"], feet["y"]), size, tweened)
    references = {
        (name, index): robot.published_frame(name, index, count) for name, count, _ms in rows for index in range(count)
    }
    return flipbook, references


def test_the_sample_is_drawn_from_parts_and_is_the_published_frame(sample):
    flipbook, references = sample
    assert flipbook.placement == PLACEMENT_CONTINUOUS
    assert flipbook.tweens.keys() == {"walk", "walk~mirrored"}
    failures = []
    for (name, index), reference in references.items():
        candidate = flipbook.recompose(name, index)
        wrong, blob = parity(reference, candidate, **TOLERANCE), largest_wrong_blob(reference, candidate, **TOLERANCE)
        if wrong > PARITY_BOUND or blob > BLOB_BOUND:
            failures.append(f"{name}[{index}]: {wrong:.4f} of pixels, blob {blob}")
    assert len(references) == sum(n for name, n, _ms in robot.ROWS if name in SAMPLE) > 0
    assert not failures, "frames the flipbook does not reproduce:\n" + "\n".join(failures)


def test_each_mechanism_is_in_the_flipbook(sample):
    """⛔ The premise of every poison below: the sample HAS the thing."""
    flipbook, _references = sample
    death = flipbook.frame_opacity["death"]
    assert death[0] == 1.0 and death[-1] < 0.6, death
    assert set(flipbook.frame_opacity) == {"death"}
    # The blade fades out after the strike (the swap sets' cross-fades fade
    # single parts too).
    faded = {d.track for frame in flipbook.clips["smash_forward"][1] for d in frame if d.opacity < 1.0}
    assert "blade" in faded, faded
    mirrored = [d for frame in flipbook.clips["walk~mirrored"][1] for d in frame if d.track and not d.track.startswith("overlay:")]
    assert mirrored and all(d.scale == (-1.0, 1.0) for d in mirrored)
    tracks = {d.track for frame in flipbook.clips["blink_out"][1] for d in frame}
    assert "overlay:teleport_body" in tracks and "overlay:fx_back" in tracks, tracks
    assert any(d.track == "overlay:fx_front" for d in flipbook.clips["hover"][1][0])


def test_the_published_table_reads_back_as_the_flipbook(sample, tmp_path):
    flipbook, _references = sample
    flipbook.write(tmp_path)
    back = PartFlipbook.from_published(tmp_path / f"{robot.TARGET_NAME}_parts.ron")
    assert back.placement == PLACEMENT_CONTINUOUS
    assert back.frame_opacity == {"death": pytest.approx(flipbook.frame_opacity["death"], abs=1e-4)}
    assert back.tweens == flipbook.tweens
    for row, (_duration, frames) in flipbook.clips.items():
        for frame, read in zip(frames, back.clips[row][1]):
            assert [(d.part, d.track, d.scale) for d in frame] == [(d.part, d.track, d.scale) for d in read]
            assert [d.opacity for d in read] == pytest.approx([d.opacity for d in frame], abs=1e-4)


# -- the measures can fail --------------------------------------------------------


def _poisoned(flipbook, row, index, change):
    """``flipbook``'s frame ``index`` of ``row`` recomposed with its draws (and
    frame opacity) changed by ``change(draws, opacity) -> (draws, opacity)``."""
    draws, opacity = change(list(flipbook.clips[row][1][index]), flipbook.opacity_of(row, index))
    poisoned = dataclasses.replace(
        flipbook,
        clips={**flipbook.clips, row: (flipbook.clips[row][0], [draws])},
        frame_opacity={**flipbook.frame_opacity, row: [opacity]},
    )
    return poisoned.recompose(row, 0)


def _outside(reference, candidate):
    return (
        parity(reference, candidate, **TOLERANCE) > PARITY_BOUND
        or largest_wrong_blob(reference, candidate, **TOLERANCE) > BLOB_BOUND
    )


def _fails(sample, row, index, change):
    flipbook, references = sample
    reference = references[(row, index)]
    assert not _outside(reference, flipbook.recompose(row, index)), "the honest frame is already outside"
    return _outside(reference, _poisoned(flipbook, row, index, change))


def _without(track):
    return lambda draws, opacity: ([d for d in draws if d.track != track], opacity)


def test_a_dropped_part_fails(sample):
    assert _fails(sample, "idle", 0, _without("near_hand"))


@pytest.mark.parametrize("track", ["head", "near_hand", "near_foot"])
def test_a_visible_part_a_pixel_off_fails(sample, track):
    def nudge(draws, opacity):
        assert any(d.track == track for d in draws), track
        return [dataclasses.replace(d, at=(d.at[0] + 1.0, d.at[1])) if d.track == track else d for d in draws], opacity

    assert _fails(sample, "idle", 0, nudge)


def test_a_dropped_effect_layer_fails(sample):
    assert _fails(sample, "hover", 0, _without("overlay:fx_front"))


def test_a_death_frame_drawn_opaque_fails(sample):
    flipbook, _references = sample
    last = len(flipbook.clips["death"][1]) - 1
    assert _fails(sample, "death", last, lambda draws, opacity: (draws, 1.0))


def test_a_death_faded_part_by_part_fails(sample):
    """The frame fades as ONE picture: the same opacity on each draw lets the
    parts show through each other."""
    flipbook, _references = sample
    last = len(flipbook.clips["death"][1]) - 1

    def per_part(draws, opacity):
        return [dataclasses.replace(d, opacity=d.opacity * opacity) for d in draws], 1.0

    assert _fails(sample, "death", last, per_part)


def test_a_blade_drawn_opaque_fails(sample):
    flipbook, _references = sample
    index = min(
        range(len(flipbook.clips["smash_forward"][1])),
        key=lambda i: min([d.opacity for d in flipbook.clips["smash_forward"][1][i]]),
    )

    def opaque(draws, opacity):
        return [dataclasses.replace(d, opacity=1.0) for d in draws], opacity

    assert _fails(sample, "smash_forward", index, opaque)


def test_a_mirrored_row_drawn_unmirrored_fails(sample):
    def unmirrored(draws, opacity):
        return [dataclasses.replace(d, scale=(1.0, 1.0), rotation=-d.rotation) if d.scale[0] < 0 else d for d in draws], opacity

    assert _fails(sample, "walk~mirrored", 0, unmirrored)


def test_a_frame_painted_outside_the_seams_is_refused():
    """A post-process the seams do not carry (here a stroke drawn straight onto
    the published frame) is refused at publish, not shipped without it."""

    def stroked(row, index, count):
        frame = robot.published_frame(row, index, count)
        for x in range(100, 140):
            frame.putpixel((x, 60), (255, 0, 0, 255))
        return frame

    size = (robot.FRAME_SIZE[0] + 32, robot.FRAME_SIZE[1] + 32)
    with pytest.raises(AssertionError, match="outside rigdoc's seams"):
        build_rig_flipbook(robot.TARGET_NAME, [("idle", 8, 120)], stroked, None, (130.0, 173.0), size)


def test_a_mirror_seam_mirrors_each_draw_about_the_frame():
    """``rigdoc.mirrored_canvas`` recorded: a part's pivot lands at
    ``width - x``, it turns the other way and is mirrored about its pivot."""
    sprite = Image.new("RGBA", (8, 4), (0, 0, 0, 0))
    sprite.paste((255, 255, 255, 255), (0, 0, 3, 4))
    with part_flipbook.recorded_paint() as record:
        canvas = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
        rigdoc.blit_rotated(canvas, sprite, (1.0, 1.0), (40.0, 50.0), 0.0, part_name="toy")
        big = rigdoc.downsampled_canvas(canvas, (32, 32))
        out = rigdoc.mirrored_canvas(big)
    (op,) = record.ops_for(out)
    assert (op.world, op.degrees, op.scale_x, op.exact) == ((32 - 10.0, 12.5), 0.0, -1.0, False)
