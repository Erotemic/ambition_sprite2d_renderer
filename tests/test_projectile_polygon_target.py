from ambition_sprite2d_renderer.authoring.motion_ir import CharacterMotionBinding
from ambition_sprite2d_renderer.targets.characters import projectile_polygon as target


REQUIRED_SAFE_POSES = {
    "idle", "walk", "run", "crouch", "jump", "fall", "roll", "air_dodge",
    "shield_raise", "jab", "attack_side", "attack_up", "attack_down",
    "smash_forward", "smash_up", "smash_down", "air_neutral", "air_forward",
    "air_back", "air_up", "air_down", "grab", "grab_hold", "pummel",
    "throw_forward", "throw_back", "throw_up", "throw_down", "grabbed",
    "launch", "knockdown", "getup", "tech", "ledge_grab", "ledge_getup",
    "ledge_attack", "ledge_roll", "ledge_jump", "item_hold", "item_throw",
    "shoot", "taunt", "victory_hold", "loss",
}


def _binding():
    return CharacterMotionBinding.load(target.MOTION_PATH)


def test_projectile_polygon_shares_the_full_polygon_reference_library():
    prepared = _binding().load_prepared()
    assert REQUIRED_SAFE_POSES <= set(prepared.library.clips)
    assert len(prepared.library.clips) >= 130
    assert prepared.binding.features["archetype"] == "projectile_beast_biped"
    assert prepared.binding.features["projectile_emitter"] == "head_cannon"


def test_projectile_polygon_reads_as_a_head_cannon_beast_biped():
    prepared = _binding().load_prepared()
    assert not [part for part in prepared.rig.parts if part.id == "sword"]
    text = _binding().rig_svg.read_text(encoding="utf8")
    assert "Projectile Polygon - Side" in text
    assert 'data-ambition-schema="ambition-svg-rig-v1"' in text
    assert 'id="polygon-head-cannon"' in text
    assert 'id="polygon-head-cannon-muzzle"' in text
    assert 'id="polygon-snout-upper"' in text
    assert 'id="polygon-snout-lower"' in text
    assert 'id="polygon-tail-blade"' in text
    assert 'data-rig-profile="humanoid-articulated-v1"' in text
    assert "ponytail" not in text.lower()
    assert "filter=" not in text


def test_projectile_polygon_renderer_projection_uses_direct_fk():
    doc = target._doc()
    assert doc.data["generated_projection"]["schema"] == "ambition-rigdoc-projection-v1"
    assert doc.ik_legs == []
    assert doc.ik_chains == []
    assert "shoot" in doc.clips


def test_projectile_polygon_publication_preserves_transformed_parts():
    from ambition_sprite2d_renderer.authoring.sheet_build import clipped_frame_edges

    clip = target._prepared().library.clips["shoot"]
    frame = target._render_frame("shoot", 0, clip.frame_count)
    assert frame.size == target._publication_frame_size()
    assert clipped_frame_edges(frame) == []
