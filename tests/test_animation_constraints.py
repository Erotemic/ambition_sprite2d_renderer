"""Continuous rig constraints: planted feet stay fixed between pose keys."""

from __future__ import annotations

from pathlib import Path

import pytest

from ambition_sprite2d_renderer.authoring.animation_constraints import (
    active_plant_for_foot,
    pin_active,
    pin_for_bone,
    plant_active,
    plant_for_foot,
    remove_foot_plant,
    transform_pins,
    update_plant_target,
    upsert_full_clip_pin,
    upsert_full_clip_plant,
)
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument


TEMPLATE = (
    Path(__file__).resolve().parent.parent
    / "ambition_sprite2d_renderer"
    / "data"
    / "rig_templates"
    / "player_robot_fable.rig.json"
)


def moving_idle_doc() -> RigDocument:
    doc = RigDocument.load(TEMPLATE)
    channels = doc.data["clips"]["idle"]["channels"]
    # Deliberately make the ankle march while the root bobs. A persistent plant
    # must override these sampled targets continuously, not only at frame keys.
    channels["near_foot_x"] = {"expr": "5+3*sin(tau*t)"}
    channels["near_foot_lift"] = {"expr": "1.5+1.5*sin(tau*t)"}
    return doc


def test_continuous_plant_keeps_ankle_fixed_while_knee_bends():
    doc = moving_idle_doc()
    before = [doc.solve("idle", t)[0]["near_foot"].origin for t in (0.0, 0.125, 0.25)]
    assert before[0] != pytest.approx(before[1])

    initial, _ = doc.solve("idle", 0.0)
    foot = initial["near_foot"]
    upsert_full_clip_plant(
        doc,
        "idle",
        foot_name="near_foot",
        channel_prefix="near_foot",
        target=foot.origin,
        pitch=foot.angle,
    )

    samples = [doc.solve("idle", t)[0] for t in (0.0, 0.0625, 0.125, 0.25, 0.375, 0.5)]
    for world in samples:
        assert world["near_foot"].origin == pytest.approx(foot.origin, abs=1e-6)
        assert world["near_foot"].angle == pytest.approx(foot.angle, abs=1e-6)

    # The ankle is fixed, but the knee is not frozen: root/pelvis bob changes
    # the chain geometry and the solver bends the knee on every sample.
    knee_positions = {tuple(round(v, 4) for v in world["near_leg_l"].origin) for world in samples}
    assert len(knee_positions) > 2


def test_plant_target_can_be_dragged_and_removed():
    doc = moving_idle_doc()
    world, _ = doc.solve("idle", 0.0)
    foot = world["near_foot"]
    upsert_full_clip_plant(
        doc,
        "idle",
        foot_name="near_foot",
        channel_prefix="near_foot",
        target=foot.origin,
        pitch=foot.angle,
    )
    assert update_plant_target(doc, "idle", "near_foot", (70.5, 95.25))
    moved, _ = doc.solve("idle", 0.37)
    assert moved["near_foot"].origin == pytest.approx((70.5, 95.25))
    assert plant_for_foot(doc, "idle", "near_foot") is not None
    assert remove_foot_plant(doc, "idle", "near_foot")
    assert plant_for_foot(doc, "idle", "near_foot") is None


def test_constraint_window_supports_future_walk_contacts():
    clip = {"frames": 8, "loop": True}
    plant = {"start_frame": 2, "end_frame": 4, "enabled": True}
    assert not plant_active(clip, plant, 0.0)
    assert plant_active(clip, plant, 2 / 8)
    assert plant_active(clip, plant, 4 / 8)
    assert not plant_active(clip, plant, 6 / 8)

    wrapped = {"start_frame": 6, "end_frame": 1, "enabled": True}
    assert plant_active(clip, wrapped, 7 / 8)
    assert plant_active(clip, wrapped, 0 / 8)
    assert not plant_active(clip, wrapped, 3 / 8)


def test_active_lookup_is_non_mutating_when_constraints_are_absent():
    doc = RigDocument.load(TEMPLATE)
    assert "animation_constraints" not in doc.data
    assert active_plant_for_foot(doc, "idle", "near_foot", 0.0) is None
    assert "animation_constraints" not in doc.data


def test_fk_player_robot_feet_can_be_continuously_planted():
    rig = (
        Path(__file__).resolve().parent.parent
        / "ambition_sprite2d_renderer"
        / "targets"
        / "characters"
        / "rigged"
        / "player_robot"
        / "player_robot.rig.json"
    )
    doc = RigDocument.load(rig)
    initial, _ = doc.solve("idle", 0.0)
    for foot, upper, lower in (
        ("near_leg_foot", "near_leg_u", "near_leg_l"),
        ("far_leg_foot", "far_leg_u", "far_leg_l"),
    ):
        endpoint = initial[foot]
        upsert_full_clip_plant(
            doc,
            "idle",
            foot_name=foot,
            channel_prefix="",
            target=endpoint.origin,
            pitch=endpoint.angle,
            upper=upper,
            lower=lower,
            bend=1.0,
        )

    samples = [doc.solve("idle", t)[0] for t in (0.0, 0.11, 0.23, 0.37, 0.61, 0.89)]
    for world in samples:
        assert world["near_leg_foot"].origin == pytest.approx(
            initial["near_leg_foot"].origin, abs=1e-3
        )
        assert world["far_leg_foot"].origin == pytest.approx(
            initial["far_leg_foot"].origin, abs=1e-3
        )
    knees = {
        tuple(round(value, 4) for value in world["near_leg_l"].origin)
        for world in samples
    }
    assert len(knees) > 2


def test_rigid_foot_pin_holds_boot_origin_and_toe_together():
    rig = (
        Path(__file__).resolve().parent.parent
        / "ambition_sprite2d_renderer"
        / "targets"
        / "characters"
        / "rigged"
        / "player_robot"
        / "player_robot.rig.json"
    )
    doc = RigDocument.load(rig)
    initial, _ = doc.solve("idle", 0.0)
    foot = initial["near_leg_foot"]
    upsert_full_clip_pin(
        doc,
        "idle",
        bone_name="near_leg_foot",
        anchor_local=(foot.length, 0.0),
        target=foot.tip,
        rotation=foot.angle,
        upper="near_leg_u",
        lower="near_leg_l",
        bend=1.0,
        role="foot",
    )

    for t in (0.0, 0.11, 0.27, 0.49, 0.73, 0.91):
        world, _ = doc.solve("idle", t)
        solved = world["near_leg_foot"]
        assert solved.origin == pytest.approx(foot.origin, abs=1e-3)
        assert solved.tip == pytest.approx(foot.tip, abs=1e-3)
        assert solved.angle == pytest.approx(foot.angle, abs=1e-3)


def test_any_two_segment_endpoint_part_can_be_pinned_rigidly():
    rig = (
        Path(__file__).resolve().parent.parent
        / "ambition_sprite2d_renderer"
        / "targets"
        / "characters"
        / "rigged"
        / "player_robot"
        / "player_robot.rig.json"
    )
    doc = RigDocument.load(rig)
    initial, _ = doc.solve("idle", 0.0)
    hand = initial["near_arm_hand"]
    upsert_full_clip_pin(
        doc,
        "idle",
        bone_name="near_arm_hand",
        anchor_local=(hand.length, 0.0),
        target=hand.tip,
        rotation=hand.angle,
        upper="near_arm_u",
        lower="near_arm_l",
        bend=-1.0,
        role="part",
    )

    for t in (0.0, 0.13, 0.31, 0.58, 0.87):
        world, _ = doc.solve("idle", t)
        solved = world["near_arm_hand"]
        assert solved.origin == pytest.approx(hand.origin, abs=1e-3)
        assert solved.tip == pytest.approx(hand.tip, abs=1e-3)
        assert solved.angle == pytest.approx(hand.angle, abs=1e-3)


def test_legacy_foot_plants_migrate_to_one_generic_pin_authority():
    doc = RigDocument.load(TEMPLATE)
    doc.data["animation_constraints"] = {
        "version": 1,
        "clips": {
            "idle": {
                "foot_plants": [
                    {
                        "foot": "near_foot",
                        "upper": "near_leg_u",
                        "lower": "near_leg_l",
                        "target": [69.0, 96.9],
                        "pitch": 0.0,
                        "scope": "clip",
                    }
                ]
            }
        },
    }
    pins = transform_pins(doc, "idle", create=False)
    assert len(pins) == 1
    assert pins[0]["bone"] == "near_foot"
    assert pins[0]["role"] == "foot"
    assert pin_for_bone(doc, "idle", "near_foot") is pins[0]
    assert "foot_plants" not in doc.data["animation_constraints"]["clips"]["idle"]
    assert doc.data["animation_constraints"]["version"] == 2
    assert pin_active(doc.clips["idle"], pins[0], 0.4)


def test_visual_part_on_terminal_lower_bone_can_pin_its_authored_point():
    """A hand part need not have a redundant hand bone to be pinnable."""
    doc = RigDocument.load(TEMPLATE)
    target = (78.0, 66.0)
    upsert_full_clip_pin(
        doc,
        "idle",
        bone_name="near_arm_l",
        anchor_local=(8.0, 0.0),
        target=target,
        rotation=0.0,
        upper="near_arm_u",
        lower="near_arm_l",
        bend=1.0,
        lock_rotation=False,
        role="part",
        solver_mode="point_on_lower",
    )

    for t in (0.0, 0.13, 0.37, 0.61, 0.91):
        world, _ = doc.solve("idle", t)
        hand_center = world["near_arm_l"].to_world((8.0, 0.0))
        assert hand_center == pytest.approx(target, abs=1e-6)
