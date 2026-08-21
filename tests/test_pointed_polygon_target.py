from ambition_sprite2d_renderer.authoring.motion_ir import CharacterMotionBinding
from ambition_sprite2d_renderer.targets.characters import pointed_polygon as target


REQUIRED_SAFE_POSES = {
    "idle",
    "walk",
    "run",
    "crouch",
    "jump",
    "fall",
    "roll",
    "air_dodge",
    "shield_raise",
    "jab",
    "attack_side",
    "attack_up",
    "attack_down",
    "smash_forward",
    "smash_up",
    "smash_down",
    "air_neutral",
    "air_forward",
    "air_back",
    "air_up",
    "air_down",
    "grab",
    "grab_hold",
    "pummel",
    "throw_forward",
    "throw_back",
    "throw_up",
    "throw_down",
    "grabbed",
    "launch",
    "knockdown",
    "getup",
    "tech",
    "ledge_grab",
    "ledge_getup",
    "ledge_attack",
    "ledge_roll",
    "ledge_jump",
    "item_hold",
    "item_throw",
    "taunt",
    "victory_hold",
    "loss",
}


def _binding():
    return CharacterMotionBinding.load(target.MOTION_PATH)


def test_polygon_sword_motion_library_publishes_the_safe_humanoid_pose_vocabulary():
    prepared = _binding().load_prepared()
    assert REQUIRED_SAFE_POSES <= set(prepared.library.clips)
    assert len(prepared.library.clips) >= 130


def test_polygon_sword_has_one_integral_sword_part_on_the_near_hand():
    prepared = _binding().load_prepared()
    sword = [part for part in prepared.rig.parts if part.id == "sword"]
    assert len(sword) == 1
    assert sword[0].bone == "near_arm_hand"
    assert sword[0].elements == ("polygon-sword",)


def test_polygon_sword_svg_is_the_editable_static_rig_authority():
    binding = _binding()
    prepared = binding.load_prepared()
    svg = binding.rig_svg
    assert svg.exists()
    assert prepared.rig.source_svg == svg
    text = svg.read_text(encoding="utf8")
    assert "Pointed Polygon - Side" in text
    assert 'data-ambition-schema="ambition-svg-rig-v1"' in text
    assert 'data-rig-facing="west"' in text
    assert prepared.rig.facing == "west"
    for part_id in (
        "polygon-head",
        "polygon-torso",
        "polygon-pelvis",
        "polygon-near-arm-u",
        "polygon-near-hand",
        "polygon-sword",
    ):
        assert f'id="{part_id}"' in text
    assert "filter=" not in text


def test_polygon_sword_publishes_its_svg_declared_west_facing(monkeypatch, tmp_path):
    doc = target._doc()
    assert doc.authored_faces_left is True

    captured = {}

    def fake_build_sheet(**kwargs):
        captured.update(kwargs)
        return {}

    monkeypatch.setattr(target, "build_sheet", fake_build_sheet)
    monkeypatch.setattr(target, "_publication_frame_size", lambda: (128, 192))
    assert target.render(tmp_path) == []
    assert captured["authored_faces_left"] is True


def test_polygon_sword_renderer_projection_contains_direct_fk_not_ik_authority():
    doc = target._doc()
    assert doc.data["generated_projection"]["schema"] == "ambition-rigdoc-projection-v1"
    assert doc.ik_legs == []
    assert doc.ik_chains == []

    clip = doc.clips["walk"]
    assert "near_foot_x" not in clip["channels"]
    assert "near_foot_lift" not in clip["channels"]
    assert "near_leg_foot" in clip["channels"]

    pitches = []
    origins = []
    for frame in range(int(clip["frames"])):
        world, _ = doc.solve("walk", doc.frame_time("walk", frame))
        foot = world["near_leg_foot"]
        pitches.append(round(foot.angle, 3))
        origins.append((round(foot.origin[0], 3), round(foot.origin[1], 3)))
    assert len(set(pitches)) > 1
    assert len(set(origins)) > 1


def test_polygon_sword_publication_uses_actual_scaled_raster_size_and_overscan():
    from ambition_sprite2d_renderer.authoring.sheet_build import clipped_frame_edges

    clip = target._prepared().library.clips["grab"]
    frame = target._render_frame("grab", 3, clip.frame_count)

    assert frame.size == target._publication_frame_size()
    assert clipped_frame_edges(frame) == []
