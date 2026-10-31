"""The Pirate Admiral's fighter body language (``_pirate_admiral_fighter``):
every fighter category resolves to a row of his, each row is its own pose,
bodies lie on the floor, and nothing leaves the sheet frame."""

from __future__ import annotations

import numpy as np
import pytest

from ambition_sprite2d_renderer.authoring.fighter_motion_catalog import validate_motion_coverage
from ambition_sprite2d_renderer.targets.characters import _pirate_admiral_fighter as fighter
from ambition_sprite2d_renderer.targets.characters import _pirate_common as crew

KIND = "pirate_admiral"


def _rows():
    return {name: count for name, count, _ms in crew.rows_of(KIND)}


def _bottom(img) -> int:
    alpha = np.array(img.getchannel("A")) > 24
    return int(alpha.nonzero()[0].max())


def test_every_fighter_category_has_a_row():
    validate_motion_coverage(
        row_names=set(_rows()),
        coverage=fighter.FIGHTER_MOTION_COVERAGE,
        scopes=fighter.APPLICABLE_MOTION_SCOPES,
        character=KIND,
    )


def test_the_fighter_rows_follow_his_moves_and_rows_the_game_asks_for_exist():
    names = [name for name, _n, _ms in crew.rows_of(KIND)]
    assert names[-len(fighter.ROWS):] == [name for name, _n, _ms in fighter.ROWS]
    assert len(names) == len(set(names))
    assert {
        "hit", "hit_high", "hit_mid", "hit_low", "hit_air", "launch", "launch_up", "launch_horizontal",
        "launch_down", "meteor", "tumble", "knockdown", "prone", "prone_face_up", "prone_face_down",
        "getup", "getup_roll", "getup_attack", "tech", "tech_roll", "turnaround", "run_stop", "teeter",
        "run", "dash_startup", "dash", "skid", "walk_stop", "jump_squat", "jump", "double_jump", "fall",
        "land_recovery", "land_hard", "crouch", "crouch_start", "crouch_end", "block", "shield_hit",
        "roll", "roll_back", "spot_dodge", "air_dodge", "ledge_grab", "grab_hold", "grabbed",
    } <= set(names)


def test_each_frame_of_a_fighter_row_is_its_own_pose():
    for name, count, _ms in fighter.ROWS:
        poses = {
            tuple(round(v, 3) if isinstance(v, float) else v for v in crew.pose_of(KIND, name, i, count).values())
            for i in range(count)
        }
        assert len(poses) == count, name


def test_the_head_stays_near_the_line_of_the_body():
    for name, count, _ms in fighter.ROWS:
        for i in range(count):
            assert abs(crew.pose_of(KIND, name, i, count)["head_tilt"]) <= 16.0, (name, i)


def test_the_turn_ends_in_the_guard():
    """The game draws ``turnaround`` in the new facing: it ends square to it."""
    count = _rows()["turnaround"]
    end = crew.pose_of(KIND, "turnaround", count - 1, count)
    guard = crew.pose_of(KIND, "idle", 0, 6)
    for channel in ("body_tilt", "sword_upper", "sword_fore", "weapon", "off_upper", "left_thigh", "right_thigh"):
        assert abs(end[channel] - crew.home_pose()[channel]) < 1e-6, channel
    assert guard  # the idle row is the family's


@pytest.mark.parametrize("row", ["prone_face_up", "prone_face_down", "prone", "knockdown", "getup", "tech",
                                 "crouch", "land_hard", "roll"])
def test_a_body_on_the_floor_is_on_the_floor_line(row):
    """Its lowest paint is on the line the soles of the guard stand on, within
    a pixel, in every frame."""
    floor = _bottom(crew.draw_rig_frame(KIND, "idle", 0, 6))
    count = _rows()[row]
    frames = range(count) if row.startswith("prone") or row in ("crouch", "roll") else [count - 1]
    for i in frames:
        bottom = _bottom(crew.draw_rig_frame(KIND, row, i, count))
        assert abs(bottom - floor) <= 1, (row, i, bottom, floor)


def test_no_fighter_frame_leaves_the_sheet_frame():
    for name, count, _ms in fighter.ROWS:
        for i in range(count):
            alpha = np.array(crew.draw_rig_frame(KIND, name, i, count).getchannel("A")) > 24
            edge = alpha[0].any() or alpha[-1].any() or alpha[:, 0].any() or alpha[:, -1].any()
            assert not edge, (name, i)
