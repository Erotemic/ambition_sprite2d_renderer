import json
from pathlib import Path

from ambition_sprite2d_renderer.authoring.motion_ir import (
    CharacterMotionBinding,
    MOTION_SPACE_V1,
    MotionLibrary,
)
from ambition_sprite2d_renderer.targets.characters import (
    pugnacious_polygon,
    pointed_polygon,
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
        CharacterMotionBinding.load(pointed_polygon.MOTION_PATH),
        CharacterMotionBinding.load(pugnacious_polygon.MOTION_PATH),
    )


def test_sword_and_brawler_own_separate_libraries_on_one_rig_profile():
    """They are different humanoids, so their BASE motion differs, not just their attacks.

    A swordsman and a brawler do not stand, walk or guard alike, so the two
    libraries are forked outright rather than sharing clips with attack
    overrides. What still has to match is the rig profile: the same skeleton
    reads both, which is what lets a pose be carried from one to the other.

    The fork is only safe while it stays COMPLETE. A brawler library missing
    clips the sword has is a fighter with holes in its vocabulary that nothing
    else would report, so the row sets are compared rather than counted.
    """
    sword, brawler = _bindings()
    assert sword.library_path != brawler.library_path
    assert sword.rig_svg != brawler.rig_svg

    sword_prepared = sword.load_prepared()
    brawler_prepared = brawler.load_prepared()
    assert sword_prepared.library.id == "humanoid/fighting_polygon_v1"
    assert brawler_prepared.library.id == "humanoid/fighting_brawler_v1"
    assert sword_prepared.rig.profile == brawler_prepared.rig.profile == "humanoid-articulated-v1"
    assert len(sword_prepared.library.clips) == 136
    assert set(brawler_prepared.library.clips) == set(sword_prepared.library.clips)
    assert set(sword_prepared.library.poses) == CANONICAL_POSES
    # Pose ids name the library they belong to; a fork that kept the sword's ids
    # would read as the same poses in a diff and in every debugger.
    assert all(
        pose.startswith("humanoid/fighting_brawler/")
        for pose in brawler_prepared.library.poses
    )


def test_sword_prepares_shared_east_motion_in_its_west_facing_art_frame():
    sword, brawler = _bindings()
    source = MotionLibrary.load(sword.library_path)
    prepared = sword.load_prepared()
    brawler_prepared = brawler.load_prepared()

    assert sword.motion_source_facing == "east"
    assert prepared.rig.facing == "west"
    assert prepared.reflects_motion_x is True
    assert brawler_prepared.reflects_motion_x is False

    source_contact = source.poses["humanoid/fighting_polygon/jab/contact"]
    prepared_contact = prepared.library.poses[source_contact.id]
    assert prepared_contact.state.root.position[0] == -source_contact.state.root.position[0]
    assert (
        prepared_contact.state.bones["near_arm_u"].rotation_deg
        == -source_contact.state.bones["near_arm_u"].rotation_deg
    )

    # Reflection is a prepared character-local view, not a forked source
    # library.  Every pose and clip must convert losslessly back to the one
    # shared source representation so Godot edits can be written safely.
    for pose_id, source_pose in source.poses.items():
        assert prepared.to_source_pose(prepared.library.poses[pose_id]).to_dict() == source_pose.to_dict()
    for clip_id, source_clip in source.clips.items():
        assert prepared.to_source_clip(prepared.library.clips[clip_id]).to_dict() == source_clip.to_dict()


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
    for target in (pointed_polygon, pugnacious_polygon):
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


def test_every_binding_on_one_library_shares_that_library_unit_scale():
    """A shared library's translations are absolute, so its readers share a scale.

    `space.linear_unit` is `rig_user_unit`: a dash authored as "276 units
    forward" means units of whichever rig reads it. Bind art drawn at another
    scale and only the translations are wrong — the character walks correctly
    and then throws itself a frame-and-a-half sideways on its first dash, which
    is exactly how the Author arrived. Grouping by library instead of naming the
    fighters keeps this true for the next character to bind one.
    """
    root = Path(__file__).resolve().parents[1] / "ambition_sprite2d_renderer/data/characters"
    by_library: dict[Path, dict[str, float]] = {}
    for path in sorted(root.glob("*/*.motion.json")):
        binding = CharacterMotionBinding.load(path)
        by_library.setdefault(binding.library_path, {})[binding.character] = (
            binding.render.frame_px_per_rig_unit
        )

    assert by_library, "no character motion bindings discovered"
    disagreements = {
        library.name: scales
        for library, scales in by_library.items()
        if len(set(scales.values())) > 1
    }
    assert disagreements == {}


def test_a_clip_that_swaps_torsos_shows_exactly_one_on_every_frame():
    """A swap set is all-or-nothing per key, and silence reads as hidden.

    ⛔ The renderer falls back to a part's `opacity_default` only when the
    channel is ABSENT. The projection makes a channel present on EVERY key of a
    clip the moment one key mentions it, so a clip that turned the trunk for
    three frames left the other three with all torsos at zero — a fighter with
    a hole where his chest goes, in the published sheet, on frames nobody was
    looking at because they were the calm ones.

    Checked as a SUM rather than a presence: two torsos at once is the same
    authoring mistake wearing the opposite sign.
    """
    from ambition_sprite2d_renderer.targets.characters import (
        author,
        officer,
        pointed_polygon,
        pugnacious_polygon,
    )

    swap = ("torso_front_vis", "torso_side_vis", "torso_back_vis")
    for target in (author, officer, pointed_polygon, pugnacious_polygon):
        doc = target._doc()
        for name, clip in doc.clips.items():
            channels = {key: clip["channels"][key] for key in swap if key in clip["channels"]}
            if not channels:
                continue  # never turns the trunk; the default keeps it visible
            totals = [
                round(sum(track["keys"][index][1] for track in channels.values()), 4)
                for index in range(len(next(iter(channels.values()))["keys"]))
            ]
            assert totals == [1.0] * len(totals), (
                f"{doc.data['name']} {name}: torso visibility per frame {totals}"
            )
