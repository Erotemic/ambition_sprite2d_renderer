"""George Boo'l's fighter body language (`_george_booul_fighter`): every
`fighter_core` category resolves to a row he draws, no row repeats another,
a body on the floor lies on his hem line, and only a keyed row sinks."""

from __future__ import annotations

import dataclasses

import pytest

from ambition_sprite2d_renderer.authoring.fighter_motion_catalog import validate_motion_coverage
from ambition_sprite2d_renderer.targets.characters import george_booul as g
from ambition_sprite2d_renderer.targets.characters._george_booul_fighter import (
    APPLICABLE_MOTION_SCOPES,
    FIGHTER_MOTION_COVERAGE,
    REST,
    ROWS_SPEC,
    fighter_rows,
)


def test_covers_every_fighter_core_category():
    validate_motion_coverage(
        row_names={name for name, _frames, _ms in g.ROWS},
        coverage=FIGHTER_MOTION_COVERAGE,
        scopes=APPLICABLE_MOTION_SCOPES,
        character=g.TARGET_NAME,
    )


def test_rows_are_declared_once_and_every_binding_has_its_row():
    names = [name for name, _frames, _ms in g.ROWS]
    assert len(names) == len(set(names))
    assert {name for name, _f, _ms in fighter_rows()} <= set(names)
    for binding in g.ACTOR_METADATA["animation_bindings"].values():
        assert binding["animation"] in names, binding


def test_rest_mirrors_the_pose_defaults():
    rest = g.Pose()
    for name, value in REST.items():
        assert getattr(rest, name) == value, name
    for f in dataclasses.fields(g.Pose):
        if f.name not in REST and f.name != "blink" and f.name != "fx":
            assert getattr(rest, f.name) == 0.0, f.name


def test_no_row_repeats_another_rows_poses():
    seen: dict = {}
    for name, frames, _ms in g.ROWS:
        key = tuple(tuple(sorted(vars(g._pose(name, i, frames)).items())) for i in range(frames))
        assert key not in seen, f"{name} draws exactly what {seen[key]} draws"
        seen[key] = name


@pytest.mark.parametrize("row", ["prone_face_up", "prone_face_down", "prone", "trip_idle", "knockdown"])
def test_a_body_on_the_floor_lies_on_his_hem_line(row):
    frames = {name: count for name, count, _ms in g.ROWS}
    floor = g.render_frame("idle", 0, 8).getbbox()[3]
    box = g.render_frame(row, frames[row] - 1, frames[row]).getbbox()
    assert abs(box[3] - floor) <= 1, f"{row}: lowest paint at {box[3]}, hem line {floor}"
    assert box[0] > 0 and box[2] < g.FRAME_SIZE[0], f"{row}: art runs off the frame side {box}"


def test_only_a_keyed_row_reaches_below_the_floor():
    rest = g._REST_LOW
    sinking = {name for name, (_ms, keys) in ROWS_SPEC.items() if any(k.get("sink") for k in keys)}
    assert sinking == {"platform_drop", "bury_start", "buried", "bury_escape"}
    for name, frames, _ms in g.ROWS:
        if name in sinking or name not in ROWS_SPEC:
            continue
        for i in range(frames):
            assert g._lowest_paint(g._pose(name, i, frames)) <= rest + 1e-6, f"{name}:{i}"


def test_a_recoil_ends_on_its_settled_pose_and_the_turn_ends_facing_front():
    for row in ("hit_high", "hit_mid", "hit_low", "hit_air"):
        keys = ROWS_SPEC[row][1]
        assert keys[-1].get("fx", "") == "", row
        assert abs(keys[-1].get("lean", 0.0)) + abs(keys[-1].get("tilt", 0.0)) > 8.0, row
    assert ROWS_SPEC["turnaround"][1][-1]["yaw"] == g.GAME_YAW
