"""Eternal Cosmic Mary-O: her sheet says what the game reads from it."""

from __future__ import annotations

from ambition_sprite2d_renderer.registry import discover_all_targets
from ambition_sprite2d_renderer.targets.characters import _mary_o_v2_model as model
from ambition_sprite2d_renderer.targets.characters import mary_o_v2_cosmic as cosmic
from ambition_sprite2d_renderer.targets.characters._mary_o_v2_cosmic_art import S, frame


def test_the_target_is_discoverable() -> None:
    assert cosmic.TARGET in discover_all_targets().targets


def test_her_body_is_the_body_of_her_grown_forms_at_half_the_pixels() -> None:
    """Her sheet is published as drawn, and her other sheets at two times
    that. The game gives her the height of her grown forms, so her body box
    must be theirs, at half the pixels."""
    fire = model.form_collision_box(model.FIRE_FORM)
    box = cosmic.STAGE.body_box_px()
    scale = model.OUTPUT_RESOLUTION_SCALE
    assert (box["w"], box["h"]) == (fire["w"] / scale, fire["h"] / scale)
    feet_x, feet_y = cosmic.STAGE.feet_px
    assert box["y"] + box["h"] == feet_y
    assert abs(box["x"] + box["w"] / 2.0 - feet_x) <= 0.5


def test_the_transformation_is_one_row_as_long_as_the_game_holds_her() -> None:
    rows = {name: (frames, ms) for name, frames, ms in cosmic.ROWS}
    assert rows["transform"] == (cosmic.TRANSFORM_FRAMES, cosmic.TRANSFORM_FRAME_MS)
    assert len(cosmic.transformation()) == cosmic.TRANSFORM_FRAMES


def test_each_frame_is_in_its_stage() -> None:
    """A wing or a star that goes out of the stage is cut at its edge. The
    transformation is the exception: its column of light is the height of the
    frame, and the star comes down from over it. Her way out of the form is
    the same, the other way."""
    stage = cosmic.STAGE
    for name, frames, _ms in cosmic.ROWS:
        if name in ("transform", cosmic.LEAVE_ROW):
            continue
        for index in range(frames):
            box = frame(stage, cosmic.look_for(name, index)).getbbox()
            assert box is not None, (name, index)
            assert box[0] > 0 and box[1] > 0 and box[2] < stage.w * S and box[3] < stage.h * S, (name, index, box)


def test_the_last_frame_of_the_transformation_is_her_idle() -> None:
    """The transformation ends on the frame her idle starts on, so the game
    goes from one to the other with no jump."""
    stage = cosmic.STAGE
    last = frame(stage, cosmic.transformation()[-1])
    idle = frame(stage, cosmic.look_for("idle", 0))
    assert last.tobytes() == idle.tobytes()


def test_a_frame_of_parts_is_its_layers_and_her_body_is_one_of_them() -> None:
    """The game draws a barrier about her body and not about her wings. It
    reads her body by the names of its layers, so they are there, each frame
    that is of parts, and her wings are layers of their own."""
    from ambition_sprite2d_renderer.targets.characters._mary_o_v2_cosmic_art import (
        BODY_TRACKS,
        figure_layers,
        is_of_parts,
    )

    look = cosmic.look_for("idle", 0)
    assert is_of_parts(look)
    names = [name for name, image in figure_layers(cosmic.STAGE, look)[0] if image.getbbox()]
    assert set(BODY_TRACKS) <= set(names)
    assert {"far_wing", "near_wing", "hair"} <= set(names) - set(BODY_TRACKS)
    # Her wings are behind her figure.
    assert names.index("near_wing") < names.index("body")


def test_the_transformation_is_not_of_parts_where_light_is_on_the_whole_figure() -> None:
    """Light on the whole figure and a turn of it are in no part, so those
    frames stay the sheet's (`_publish_parts` leaves the row out)."""
    from ambition_sprite2d_renderer.targets.characters._mary_o_v2_cosmic_art import is_of_parts

    assert any(not is_of_parts(look) for look in cosmic.transformation())


def test_her_way_out_starts_as_the_form_and_ends_as_light_and_no_more() -> None:
    """The game plays the row and then changes her character to the form of
    her ladder, which can be each of three. So the last frame has no thing of
    the cosmic form in it but light, and the first has her wings."""
    rows = {name: (frames, ms) for name, frames, ms in cosmic.ROWS}
    looks = cosmic.detransformation()
    assert rows[cosmic.LEAVE_ROW] == (len(looks), cosmic.LEAVE_FRAME_MS)
    first, last = looks[0], looks[-1]
    assert first.wing == 1.0 and first.light == 0.0
    assert last.light == 1.0 and (last.wing, last.hair, last.ring, last.crown) == (0, 0, 0, None)
    assert last.lift == 0.0
