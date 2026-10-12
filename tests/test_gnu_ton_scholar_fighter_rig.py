"""Renderer-facing invariants for the D2 scholar's second, fighter rig.

Art choices (specific colors, silhouette, row inventory) remain visual review
work.  These tests check that the two rigs share one art authority, publication
and IK work, and authored movement actually changes the resulting skeleton.
"""
from __future__ import annotations

import math
from pathlib import Path

from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
from ambition_sprite2d_renderer.registry.discovery import discover_module_targets

PACKAGE = Path(__file__).resolve().parents[1] / "ambition_sprite2d_renderer"
ROOT = PACKAGE.parent
FIGHTER = PACKAGE / "targets/characters/rigged/gnu_ton_scholar_fighter.rig.json"
BOSS = PACKAGE / "targets/characters/rigged/gnu_ton_scholar_villain.rig.json"


def rigs():
    return RigDocument.load(BOSS), RigDocument.load(FIGHTER)


def test_fighter_is_registered_and_binds_exactly_the_boss_art_and_skeleton():
    boss, fighter = rigs()
    assert "gnu_ton_scholar_fighter" in discover_module_targets().targets
    assert boss.svg_source == fighter.svg_source
    assert boss.parts == fighter.parts
    assert boss.bones == fighter.bones
    assert boss.ik_legs == fighter.ik_legs
    assert fighter.frame["width"] >= boss.frame["width"]
    assert fighter.frame["height"] >= boss.frame["height"]
    assert {"near_hand", "far_hand", "head", "tail_near", "tail_far"} <= {
        bone["name"] for bone in fighter.bones
    }


def test_fighter_has_runtime_family_coverage_without_rewriting_boss_clips():
    boss, fighter = rigs()
    # Families the engine / Smash-style fighter presentation needs to select.
    # No exact counts: authored poses and timing may continue to be iterated.
    families = (
        {"idle", "walk", "run", "crouch", "jump", "fall", "land"},
        {"shield_raise", "shield_hold", "shield_release", "parry", "air_dodge"},
        {"jab", "dash_attack", "smash_forward", "smash_up", "smash_down"},
        {"air_neutral", "air_forward", "air_back", "air_up", "air_down"},
        {"special_neutral", "special_side", "special_up", "special_down"},
        {"grab", "grab_hold", "throw_forward", "throw_back", "throw_up", "throw_down"},
        {"hit", "launch", "tumble", "prone", "getup", "death"},
        {"ledge_grab", "ledge_getup", "ledge_roll", "ledge_getup_attack"},
    )
    assert all(family <= set(fighter.clips) for family in families)
    assert {"rest", "point", "conduct", "invoke", "hit", "death",
            "brace", "tumble", "dazed", "climb"} <= set(boss.clips)


def test_foot_ik_and_airborne_modes_produce_distinct_world_positions():
    _boss, fighter = rigs()
    idle, _ = fighter.solve("idle", 0.0)
    run, _ = fighter.solve("run", 0.25)
    jump, _ = fighter.solve("jump", 0.5)
    for side in ("near", "far"):
        ankle = f"{side}_foot"
        assert ankle in idle and ankle in run and ankle in jump
        assert math.dist(idle[ankle].origin, run[ankle].origin) > 2
        assert jump[ankle].origin[1] < idle[ankle].origin[1] - 2


def test_attacks_have_real_windup_and_active_limb_displacement():
    _boss, fighter = rigs()
    for attack, bone in (
        ("smash_forward", "near_hand"),
        ("smash_up", "near_hand"),
        ("smash_down", "near_hand"),
        ("air_forward", "near_hand"),
        ("throw_back", "far_hand"),
    ):
        start, _ = fighter.solve(attack, 0.0)
        active, _ = fighter.solve(attack, 0.5)
        distance = math.dist(start[bone].origin, active[bone].origin)
        assert distance > 5, (attack, bone, distance)


def test_props_and_expressions_switch_without_creating_new_arm_bones():
    _boss, fighter = rigs()
    neutral = fighter.solve("idle", 0.5)[1]
    casting = fighter.solve("special_neutral", 0.5)[1]
    grabbing = fighter.solve("grab_hold", 0.5)[1]
    shielding = fighter.solve("shield_hold", 0.5)[1]
    assert neutral["prop.quill"] == neutral["prop.book"] == 1.0
    assert casting["prop.book"] == 0.0
    assert casting["prop.book_open"] == 1.0
    assert grabbing["prop.quill"] == grabbing["prop.book"] == 0.0
    assert shielding["prop.book"] == 1.0
    assert all(part["bone"] in {b["name"] for b in fighter.bones}
               for part in fighter.parts)


def test_looping_fighter_pose_transitions_have_seam_safe_root_motion():
    _boss, fighter = rigs()
    for row in ("idle", "walk", "run", "crouch", "fall", "shield_hold"):
        clip = fighter.clips[row]
        assert clip["loop"]
        start_params = fighter.solve(row, 0.0)[1]
        end_params = fighter.solve(row, 1.0)[1]
        for channel in ("root_x", "root_y", "pelvis", "torso"):
            assert abs(start_params[channel] - end_params[channel]) < 0.01, (row, channel)


def test_representative_fighter_frames_render_inside_frame():
    _boss, fighter = rigs()
    w, h = int(fighter.frame["width"]), int(fighter.frame["height"])
    pad = 30
    for name in ("idle", "run", "jump", "ledge_getup_attack", "smash_forward",
                 "smash_up", "smash_down", "air_down", "special_up",
                 "roll", "grab", "prone", "getup", "victory_hold"):
        n = fighter.clips[name]["frames"]
        for i in (0, n // 2, n - 1):
            frame = fighter.render_frame(name, i, n, padding=pad)
            bbox = frame.getbbox()
            assert bbox is not None, (name, i)
            left, top, right, bottom = [value - pad for value in bbox]
            assert 2 <= left < right <= w - 2, (name, i, bbox)
            assert 2 <= top < bottom <= h - 2, (name, i, bbox)
