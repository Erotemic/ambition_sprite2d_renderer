"""Check that the Shock Warden legs have clear depth against the coat."""
from __future__ import annotations

import json
from pathlib import Path

from ambition_sprite2d_renderer.authoring.rigdoc import visible_parts

ROOT = Path(__file__).resolve().parents[1]
RIG = (
    ROOT
    / "ambition_sprite2d_renderer/targets/characters/rigged"
    / "shock_warden/shock_warden.rig.json"
)


def test_canvas_right_leg_is_in_front_of_coat_and_behind_belt():
    rig = json.loads(RIG.read_text(encoding="utf8"))
    parts = {part["name"]: part for part in visible_parts(rig["parts"], {})}
    bones = {bone["name"]: bone for bone in rig["bones"]}

    # The rest-pose leg on the right side of the canvas is called "far".
    assert bones["far_thigh"]["offset"][0] > 0
    assert bones["near_thigh"]["offset"][0] < 0

    coat = parts["coat_tails"]
    belt = parts["hip_belt"]
    torso = parts["torso"]
    assert coat["include"] == ["coat-tails"]
    assert belt["include"] == ["hip-belt"]
    assert coat["bone"] == belt["bone"] == "hips"

    for segment in ("far_thigh", "far_shin", "far_boot"):
        assert coat["z"] < parts[segment]["z"] < belt["z"] < torso["z"]

    # The canvas-left leg stays forward of the coat.
    for segment in ("near_thigh", "near_shin", "near_boot"):
        assert parts[segment]["z"] > coat["z"]


def test_shock_warden_leg_depth_remains_stable_across_clips():
    rig = json.loads(RIG.read_text(encoding="utf8"))
    for clip in rig["clips"].values():
        channels = clip["channels"]
        for leg in ("far_thigh", "far_shin", "far_boot", "near_thigh", "near_shin", "near_boot"):
            # No clip may hide a leg by overriding its paint depth.
            assert f"bone.{leg}.z" not in channels
