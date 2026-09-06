from __future__ import annotations

from ambition_sprite2d_renderer.authoring.motion_authoring import (
    apply_phase_template,
    apply_pose_goals,
    phase_keys_for_frames,
    solve_pose_goals,
)
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument


def _doc() -> RigDocument:
    return RigDocument(
        {
            "name": "motion_probe",
            "frame": {"width": 128, "height": 128, "center_x": 64.0, "ground_y": 104.0, "ankle_h": 2.0},
            "bones": [
                {"name": "pelvis", "parent": None, "offset": [0, -22], "length": 0, "rest_angle": 0},
                {"name": "torso", "parent": "pelvis", "offset": [0, -20], "length": 0, "rest_angle": 0},
                {"name": "head", "parent": "torso", "offset": [0, -18], "length": 8, "rest_angle": -90},
                {"name": "near_arm_u", "parent": "torso", "offset": [7, -13], "length": 18, "rest_angle": 10},
                {"name": "near_arm_l", "parent": "near_arm_u", "offset": [18, 0], "length": 16, "rest_angle": 0},
                {"name": "near_arm_hand", "parent": "near_arm_l", "offset": [16, 0], "length": 4, "rest_angle": 0},
                {"name": "far_arm_u", "parent": "torso", "offset": [-7, -13], "length": 18, "rest_angle": 170},
                {"name": "far_arm_l", "parent": "far_arm_u", "offset": [18, 0], "length": 16, "rest_angle": 0},
                {"name": "far_arm_hand", "parent": "far_arm_l", "offset": [16, 0], "length": 4, "rest_angle": 0},
                {"name": "near_leg_u", "parent": "pelvis", "offset": [5, 0], "length": 22, "rest_angle": 80},
                {"name": "near_leg_l", "parent": "near_leg_u", "offset": [22, 0], "length": 21, "rest_angle": 0},
                {"name": "near_leg_foot", "parent": "near_leg_l", "offset": [21, 0], "length": 7, "rest_angle": 0},
                {"name": "far_leg_u", "parent": "pelvis", "offset": [-5, 0], "length": 22, "rest_angle": 100},
                {"name": "far_leg_l", "parent": "far_leg_u", "offset": [22, 0], "length": 21, "rest_angle": 0},
                {"name": "far_leg_foot", "parent": "far_leg_l", "offset": [21, 0], "length": 7, "rest_angle": 0},
            ],
            "parts": [],
            "ik_legs": [
                {"upper": "near_leg_u", "lower": "near_leg_l", "foot": "near_leg_foot", "channel_prefix": "near_foot", "rest_x": 9, "rest_lift": 0, "bend": 1},
                {"upper": "far_leg_u", "lower": "far_leg_l", "foot": "far_leg_foot", "channel_prefix": "far_foot", "rest_x": -9, "rest_lift": 0, "bend": -1},
            ],
            "ik_chains": [
                {"upper": "near_arm_u", "lower": "near_arm_l", "end": "near_arm_hand", "channel_prefix": "near_hand", "rest_x": 22, "rest_y": -42, "bend": -1, "pitch_mode": "follow_lower"},
                {"upper": "far_arm_u", "lower": "far_arm_l", "end": "far_arm_hand", "channel_prefix": "far_hand", "rest_x": -20, "rest_y": -40, "bend": 1, "pitch_mode": "follow_lower"},
            ],
            "clips": {
                "jab": {"loop": False, "frames": 6, "duration_ms": 70, "channels": {"torso": {"expr": "2*sin(pi*t)"}}},
                "walk": {"loop": True, "frames": 8, "duration_ms": 100, "channels": {}},
            },
        }
    )


def test_phase_template_materializes_semantic_pose_keys():
    doc = _doc()
    keys = apply_phase_template(doc, "walk", "walk")
    assert [item["frame"] for item in keys] == list(range(8))
    assert keys[0]["role"] == "contact_near"
    assert keys[4]["role"] == "contact_far"
    assert doc.clips["walk"]["pose_keys"] == list(range(8))
    assert doc.clips["walk"]["authoring_phase_keys"]["template"] == "walk"


def test_semantic_endpoint_goal_writes_ik_channels_and_preserves_existing_motion():
    doc = _doc()
    values = apply_pose_goals(
        doc,
        "jab",
        2,
        {
            "root": {"shift": [3, 1]},
            "bones": {"torso": {"angle_deg": -9}},
            "near_hand": {"target": {"space": "frame", "value": [104, 61]}, "bend": "down"},
            "near_foot": {"target": {"space": "frame", "value": [76, 102]}, "bend": "forward"},
            "head": {"look_at": {"space": "frame", "value": [112, 58]}},
        },
    )
    assert {"root_x", "root_y", "torso", "near_hand_x", "near_hand_y", "near_hand_bend", "near_foot_x", "near_foot_lift", "near_foot_bend", "head"}.issubset(values)
    assert 2 in doc.clips["jab"]["pose_keys"]
    # Expression channel was materialized rather than discarded.
    assert len(doc.clips["jab"]["channels"]["torso"]["keys"]) >= 6

    world, _params = doc.solve("jab", doc.frame_time("jab", 2))
    hand = world["near_arm_hand"].origin
    assert abs(hand[0] - 104) < 2.0
    assert abs(hand[1] - 61) < 2.0


def test_solve_pose_goals_is_non_mutating():
    doc = _doc()
    before = doc.data.copy()
    values = solve_pose_goals(doc, "jab", 1, {"near_hand": {"target": [98, 60], "bend": "up"}})
    assert "near_hand_x" in values
    assert "near_hand_x" not in doc.clips["jab"]["channels"]
    assert doc.data == before


def test_phase_template_downsamples_cleanly_on_short_clips():
    keys = phase_keys_for_frames("smash_attack", 4, loop=False)
    frames = [item["frame"] for item in keys]
    assert frames == sorted(set(frames))
    assert frames[0] == 0
    assert frames[-1] == 3


def test_retarget_clip_transfers_endpoints_by_body_scale():
    from ambition_sprite2d_renderer.authoring.motion_retarget import retarget_clip

    source = _doc()
    # Give the source walk actual endpoint motion.
    source.clips["walk"]["channels"] = {
        "near_hand_x": {"keys": [[0.0, 20], [0.5, 30]]},
        "near_hand_y": {"const": -43},
        "far_hand_x": {"keys": [[0.0, -24], [0.5, -14]]},
        "far_hand_y": {"const": -39},
        "near_foot_x": {"keys": [[0.0, 12], [0.5, -7]]},
        "near_foot_lift": {"keys": [[0.0, 0], [0.5, 8]]},
        "far_foot_x": {"keys": [[0.0, -8], [0.5, 11]]},
        "far_foot_lift": {"keys": [[0.0, 8], [0.5, 0]]},
    }
    target = _doc()
    target.data["name"] = "target_probe"
    # Make target anatomy larger so automatic retarget scale is not 1.
    for bone in target.bones:
        if "leg_" in bone["name"] or "arm_" in bone["name"]:
            bone["length"] = float(bone.get("length", 0.0)) * 1.18
    report = retarget_clip(source, "walk", target, target_clip="walk_from_source")
    assert report["target_clip"] == "walk_from_source"
    assert set(report["transferred_endpoints"]) == {"far_foot", "far_hand", "near_foot", "near_hand"}
    assert report["endpoint_scale"] > 1.0
    clip = target.clips["walk_from_source"]
    assert clip["authoring_retarget"]["source_rig"] == "motion_probe"
    assert clip["authoring_phase_keys"]["template"] == "walk"
    assert "near_hand_x" in clip["channels"]


def test_motion_rig_resolver_is_read_only_for_missing_targets():
    from ambition_sprite2d_renderer.authoring.motion_rig_resolver import find_existing_rig_document

    try:
        find_existing_rig_document("definitely_missing_motion_rig")
    except FileNotFoundError as exc:
        message = str(exc)
    else:
        raise AssertionError("missing target unexpectedly resolved")
    assert "do not regenerate rigs implicitly" in message
    assert "--rig" in message
