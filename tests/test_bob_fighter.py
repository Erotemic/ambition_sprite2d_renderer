"""Bob's fighter contract and the humanoid rig math under it.

Bob is a roster fighter, so the runtime-facing contract is that every
applicable fighter-motion category resolves to a row his sheet publishes,
and that the rig the sheet is drawn from authors exactly those rows. The rig
math tests pin ``rigbuild.humanoid``'s pose language against the drawing:
the rest pose IS the drawing, and the hip pivot of a spin is honoured.
"""

from __future__ import annotations

import pytest

from ambition_sprite2d_renderer.authoring.fighter_motion_catalog import (
    applicable_categories,
    validate_motion_coverage,
)
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
from ambition_sprite2d_renderer.rigbuild import humanoid as H
from ambition_sprite2d_renderer.rigbuild.creature_rig import read_svg, unwrap
from ambition_sprite2d_renderer.targets.characters._bob_motion import (
    APPLICABLE_MOTION_SCOPES,
    BOB_FRONT_ROWS,
    BOB_LOOPS,
    BOB_ROWS,
    FIGHTER_MOTION_COVERAGE,
)
from ambition_sprite2d_renderer.targets.characters import bob as bob_target

SVG = bob_target.RIG_PATH.parents[4] / "data" / "characters" / "bob" / "bob.svg"
ROW_NAMES = {name for name, _frames, _ms in BOB_ROWS}


def test_bob_covers_every_current_applicable_motion_category():
    assert set(FIGHTER_MOTION_COVERAGE) == applicable_categories(APPLICABLE_MOTION_SCOPES)
    validate_motion_coverage(
        row_names=ROW_NAMES,
        coverage=FIGHTER_MOTION_COVERAGE,
        scopes=APPLICABLE_MOTION_SCOPES,
        character="bob",
    )


def test_bob_rigs_author_every_declared_row_in_order():
    # The side rig draws every row but the front-view ones, which the front
    # rig draws; together they are the sheet, in its order.
    side = RigDocument.load(bob_target.RIG_PATH)
    front = RigDocument.load(bob_target.FRONT_RIG_PATH)
    assert side.rows() == [row for row in BOB_ROWS if row[0] not in BOB_FRONT_ROWS]
    assert front.rows() == [row for row in BOB_ROWS if row[0] in BOB_FRONT_ROWS]
    assert bob_target.ROWS == list(BOB_ROWS)
    for name, _frames, _ms in BOB_ROWS:
        doc = front if name in BOB_FRONT_ROWS else side
        assert bool(doc.clips[name]["loop"]) == (name in BOB_LOOPS), name


def test_bob_has_a_front_facing_idle():
    assert "idle_front" in BOB_FRONT_ROWS
    joints, _parts = read_svg(SVG.with_name("bob_front.svg"))
    # Facing the viewer: the shoulders and hips straddle the centre line.
    assert joints["far_shoulder"][0] < 340.0 < joints["near_shoulder"][0]
    assert joints["far_hip"][0] < 340.0 < joints["near_hip"][0]


def test_bob_keeps_every_row_name_the_procedural_sheet_published():
    # The pre-SVG Bob published these rows; something may still bind them by
    # name, so the redesign keeps every one.
    old = (
        "idle walk run jump fall slash hit death blink_out blink_in dash crouch wall_slide wall_jump "
        "ledge_grab climb swim interact talk block land roll slide crouch_walk pickup throw aim shoot "
        "charge cast celebrate sit sleep hover stomp dash_startup land_hard land_recovery wall_grab "
        "ledge_climb ledge_getup ledge_roll ledge_getup_attack float_glide attack_side attack_up "
        "attack_down air_neutral air_forward air_back air_down air_up idle_front idle_side"
    ).split()
    assert not set(old) - ROW_NAMES


def test_unwrap_turns_the_short_way_round():
    assert unwrap([170.0, -170.0, -150.0]) == [170.0, 190.0, 210.0]
    assert unwrap([-10.0, 350.0]) == [-10.0, -10.0]


@pytest.fixture(scope="module")
def body() -> H.Body:
    return H.Body.from_svg(SVG, 340.0, 569.0)


def test_humanoid_rest_pose_is_the_drawing(body):
    rest = {
        "nf": ("g", body.rest_x("near"), 0.0, 0.0),
        "ff": ("g", body.rest_x("far"), 0.0, 0.0),
    }
    ch = body.channels(rest)
    for bone in ("pelvis", "torso", "head", "near_arm_u", "near_arm_l", "near_hand", "far_arm_u", "far_arm_l",
                 "far_hand"):
        assert ch[bone] == pytest.approx(0.0, abs=1e-6), bone


def test_humanoid_body_mode_foot_at_rest_offset_is_the_drawn_ankle(body):
    # A foot carried with the hips at zero offset sits where it was drawn.
    x, lift, pitch = body.foot_world({"nf": ("b", 0.0, 0.0, 0.0)}, "near")
    assert x == pytest.approx(body.rest_x("near"))
    assert lift == pytest.approx(0.0, abs=1e-6)
    assert pitch == 0.0


def test_humanoid_spin_about_keeps_the_pivot_still(body):
    # Spinning half a turn about a point 70 units up the torso leaves that
    # point where it was: the hips swing round it.
    pose = H.Body.pivoted({"x": 0.0, "y": 0.0, "spin": 180.0, "spin_about": 70.0})
    assert pose["x"] == pytest.approx(0.0, abs=1e-9)
    assert pose["y"] == pytest.approx(-140.0)
    assert "spin_about" not in pose


def test_bob_svg_marks_every_humanoid_joint():
    joints, parts = read_svg(SVG)
    needed = {"pelvis", "neck", "head_top"} | {
        f"{side}_{j}" for side in H.SIDES for j in ("shoulder", "elbow", "wrist", "hip", "knee", "ankle")
    }
    assert needed <= set(joints)
    bones = {p["bone"] for p in parts}
    assert {"near_hand", "far_hand", "torso", "head", "pelvis"} <= bones
