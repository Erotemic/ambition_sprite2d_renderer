from pathlib import Path

from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
from ambition_sprite2d_renderer.targets.characters import fighting_polygon_sword as target


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


def test_polygon_sword_rig_publishes_the_safe_humanoid_pose_vocabulary():
    doc = RigDocument.load(target.RIG_PATH)
    assert REQUIRED_SAFE_POSES <= set(doc.clips)
    assert len(doc.clips) >= 130


def test_polygon_sword_has_one_integral_sword_part_on_the_near_hand():
    doc = RigDocument.load(target.RIG_PATH)
    sword = [part for part in doc.parts if part.get("name") == "sword"]
    assert len(sword) == 1
    assert sword[0]["bone"] == "near_arm_hand"
    assert sword[0]["include"] == ["polygon-sword"]


def test_polygon_sword_svg_is_the_editable_art_authority():
    doc = RigDocument.load(target.RIG_PATH)
    svg = (target.RIG_PATH.parent / doc.svg_source["path"]).resolve()
    assert svg.exists()
    text = svg.read_text(encoding="utf8")
    assert "Fighting Polygon Sword - Side" in text
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


def test_polygon_sword_foot_channels_are_bound_to_real_ik_legs():
    doc = RigDocument.load(target.RIG_PATH)
    bindings = {leg["channel_prefix"]: leg for leg in doc.ik_legs}
    assert set(bindings) == {"near_foot", "far_foot"}
    assert bindings["near_foot"]["foot"] == "near_leg_foot"
    assert bindings["far_foot"]["foot"] == "far_leg_foot"

    clip = doc.clips["walk"]
    pitches = []
    origins = []
    for frame in range(int(clip["frames"])):
        world, _ = doc.solve("walk", doc.frame_time("walk", frame))
        foot = world["near_leg_foot"]
        pitches.append(round(foot.angle, 3))
        origins.append((round(foot.origin[0], 3), round(foot.origin[1], 3)))
    assert len(set(pitches)) > 1
    assert len(set(origins)) > 1
