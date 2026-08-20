import json
from pathlib import Path

from ambition_sprite2d_renderer.authoring.motion_ir import (
    CharacterMotionBinding,
    MOTION_SPACE_V1,
)
from ambition_sprite2d_renderer.targets.characters import (
    fighting_polygon_brawler,
    fighting_polygon_sword,
)


CANONICAL_POSES = {
    "humanoid/fighting_polygon/idle",
    "humanoid/fighting_polygon/crouch",
    "humanoid/fighting_polygon/jab/anticipation",
    "humanoid/fighting_polygon/jab/contact",
    "humanoid/fighting_polygon/jab/recovery",
    "humanoid/fighting_polygon/ftilt/anticipation",
    "humanoid/fighting_polygon/ftilt/contact",
    "humanoid/fighting_polygon/ftilt/recovery",
    "humanoid/fighting_polygon/grab/anticipation",
    "humanoid/fighting_polygon/grab/extension",
    "humanoid/fighting_polygon/grab/hold",
    "humanoid/fighting_polygon/grab/recovery",
    "humanoid/fighting_polygon/pummel/contact",
    "humanoid/fighting_polygon/throw_forward/anticipation",
    "humanoid/fighting_polygon/throw_forward/release",
    "humanoid/fighting_polygon/throw_forward/recovery",
}


def _bindings():
    return (
        CharacterMotionBinding.load(fighting_polygon_sword.MOTION_PATH),
        CharacterMotionBinding.load(fighting_polygon_brawler.MOTION_PATH),
    )


def test_fighting_polygons_share_one_motion_library_but_own_distinct_static_rigs():
    sword, brawler = _bindings()
    assert sword.library_path == brawler.library_path
    assert sword.rig_svg != brawler.rig_svg

    sword_prepared = sword.load_prepared()
    brawler_prepared = brawler.load_prepared()
    assert sword_prepared.library.id == "humanoid/fighting_polygon_v1"
    assert brawler_prepared.library.id == sword_prepared.library.id
    assert sword_prepared.rig.profile == brawler_prepared.rig.profile == "humanoid-articulated-v1"
    assert len(sword_prepared.library.clips) == 136
    assert set(sword_prepared.library.poses) == CANONICAL_POSES


def test_motion_library_serializes_the_coordinate_contract_instead_of_implying_godot_semantics():
    sword, _ = _bindings()
    raw = json.loads(sword.library_path.read_text(encoding="utf8"))
    assert raw["space"] == MOTION_SPACE_V1
    assert raw["space"]["bone_transform"] == "parent_local_delta_from_svg_rest"
    assert raw["space"]["y_axis"] == "down"
    assert raw["space"]["positive_rotation"] == "clockwise"


def test_motion_library_discovers_independent_pose_and_clip_files_without_a_global_file_census():
    sword, _ = _bindings()
    raw = json.loads(sword.library_path.read_text(encoding="utf8"))
    assert raw["pose_roots"] == ["poses"]
    assert raw["clip_roots"] == ["clips"]
    assert "poses" not in raw or isinstance(raw["poses"], str)
    assert "clips" not in raw or isinstance(raw["clips"], str)

    base = sword.library_path.parent
    assert len(list((base / "poses").glob("*.pose.json"))) == len(CANONICAL_POSES)
    assert len(list((base / "clips").glob("*.clip.json"))) == 136


def test_pose_centric_clips_reference_reusable_named_whole_body_poses():
    sword, _ = _bindings()
    library = sword.load_prepared().library

    jab = library.clips["jab"]
    refs = {key.pose for key in jab.pose_keys if key.pose is not None}
    assert refs == {
        "humanoid/fighting_polygon/jab/anticipation",
        "humanoid/fighting_polygon/jab/contact",
        "humanoid/fighting_polygon/jab/recovery",
    }
    contact = library.poses["humanoid/fighting_polygon/jab/contact"]
    assert contact.state.bones
    assert "near_arm_u" in contact.state.bones
    assert contact.state.bones["near_arm_u"].rotation_deg != 0.0


def test_clip_sampling_is_separate_from_animation_time():
    sword, _ = _bindings()
    jab = sword.load_prepared().library.clips["jab"]
    assert jab.frame_count == 5
    assert jab.frame_duration_ms == 45
    assert jab.duration_s == 0.225
    assert [key.at_s for key in jab.pose_keys] == [0.0, 0.045, 0.09, 0.135, 0.18]


def test_renderer_projection_is_generated_from_motion_ir_and_contains_no_legacy_solver_language():
    for target in (fighting_polygon_sword, fighting_polygon_brawler):
        doc = target._doc()
        assert doc.data["generated_projection"]["schema"] == "ambition-rigdoc-projection-v1"
        assert doc.ik_legs == []
        assert doc.ik_chains == []
        assert len(doc.clips) == 136
        for clip in doc.clips.values():
            for spec in clip["channels"].values():
                assert "expr" not in spec
            assert not any(
                channel.startswith(("near_foot_", "far_foot_", "near_hand_", "far_hand_"))
                for channel in clip["channels"]
            )
