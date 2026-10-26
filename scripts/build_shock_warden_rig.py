#!/usr/bin/env python3
"""Build the Shock Warden pose rig from the edited SVG.

    uv run python scripts/build_shock_warden_rig.py

The SVG owns the drawing and joint marker positions. This script owns the
rest hierarchy, sprite bindings, and authored clips. It does not draw art.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ambition_sprite2d_renderer.devtools import svg_rig_tool  # noqa: E402
ART = ROOT / "scripts/svg_art/shock_warden_art.py"
SPEC = importlib.util.spec_from_file_location("shock_warden_art", ART)
art = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(art)
RIG = ROOT / "ambition_sprite2d_renderer/targets/characters/rigged/shock_warden/shock_warden.rig.json"
SCALE = 0.52
FRAME = {"width": 420, "height": 324, "center_x": 210, "ground_y": 225,
         "ankle_h": 0, "supersample": 3, "render_scale": 1, "trim": False}
#: The walk keeps a foot on the ground the body stands on in every frame, and
#: the run's lowest stride touches it (``RigDocument.plant_offset``).
FRAME["plant"] = {"walk": "each", "run": "row"}


def expr(code: str) -> dict:
    return {"expr": code}


REST = {
    "hips": 0.0, "torso": 0.0, "head": 0.0,
    "near_thigh": 0.0, "near_shin": 0.0, "near_boot": 0.0,
    "far_thigh": 0.0, "far_shin": 0.0, "far_boot": 0.0,
    "shield_upper": 0.0, "shield_forearm": 0.0, "shield": 0.0,
    "baton_upper": 0.0, "baton_forearm": 0.0, "baton_hand": 0.0, "baton": 0.0,
    "shield_charge": 0.7, "baton_charge": 0.6, "shield_impact": 0.0,
    "root_x": 0.0, "root_y": 0.0,
}


def pose_clip(stops: list[tuple[float, dict]], frames: int, duration_ms: int, loop: bool = False) -> dict:
    """Build channels from shared rest values and timed pose deltas."""
    if not stops or stops[0][0] != 0.0 or stops[-1][0] != 1.0:
        raise ValueError("pose clips must cover 0 to 1")
    keys = {name for name, value in REST.items() if value != 0.0}
    for _t, pose in stops:
        keys.update(pose)
    channels = {
        key: {"keys": [[float(t), float(pose.get(key, REST.get(key, 0.0))), "linear"]
                         for t, pose in stops]}
        for key in sorted(keys)
    }
    return {"loop": loop, "frames": frames, "duration_ms": duration_ms, "channels": channels}


def joint_positions(svg_path: Path) -> dict[str, tuple[float, float]]:
    """Read Inkscape joint markers, including markers in hidden groups."""
    root = ET.parse(svg_path).getroot()
    # The source layer owns joint markers. The embedded catalog also contains
    # derived markers and must not become a second skeleton input.
    layer = next(node for node in root.iter() if node.get("id") == "joint-markers")
    markers = {}
    for node in layer.iter():
        name = node.get("data-rig-joint")
        if name:
            if name in markers:
                raise ValueError(f"duplicate joint marker: {name}")
            markers[name] = (float(node.attrib["cx"]), float(node.attrib["cy"]))
    wanted = set(art.JOINTS)
    if set(markers) != wanted:
        raise ValueError(f"joint markers mismatch: missing={wanted - set(markers)} extra={set(markers) - wanted}")
    return markers


def held_shield(pose: dict, pitch: float = 0.0) -> dict:
    """Keep the shield angle independent of torso and arm turns."""
    support_angle = sum(pose.get(name, REST[name]) for name in (
        "torso", "shield_upper", "shield_forearm"
    ))
    return {**pose, "shield": pitch - support_angle}


CLIPS = {
    "idle": {"loop": True, "frames": 8, "duration_ms": 135,
             "channels": {**{key: {"const": value} for key, value in REST.items() if value},
                          "root_y": expr("0.7*sin(tau*t)"),
                          "torso": expr("0.7*sin(tau*t)"),
                          "head": expr("-1.2*sin(tau*t+0.25)"),
                          "shield": expr("-0.7*sin(tau*t)"),
                          "shield_charge": expr("0.56+0.12*sin(tau*2*t)"),
                          "baton_charge": expr("0.45+0.12*sin(tau*2*t+0.7)")}},
    "walk": {"loop": True, "frames": 10, "duration_ms": 105,
             "channels": {**{key: {"const": value} for key, value in REST.items() if value},
                          "root_y": expr("-1.2*abs(sin(tau*t))"),
                          "torso": expr("1.8*sin(tau*t)"),
                          "head": expr("-1.4*sin(tau*t)"),
                          "near_thigh": expr("21*sin(tau*t)"),
                          "near_shin": expr("-9*sin(tau*t)-6*max(0,sin(tau*t))"),
                          "near_boot": expr("-8*sin(tau*t)"),
                          "far_thigh": expr("-21*sin(tau*t)"),
                          "far_shin": expr("9*sin(tau*t)-6*max(0,-sin(tau*t))"),
                          "far_boot": expr("8*sin(tau*t)"),
                          "shield_upper": expr("-3*sin(tau*t)"),
                          "shield_forearm": expr("2*sin(tau*t)"),
                          "shield": expr("-0.8*sin(tau*t)"),
                          "baton_upper": expr("-4*sin(tau*t)")}},
    "guard": pose_clip([
        (0.0, held_shield({})),
        (0.25, held_shield({"root_y": 2, "torso": 4, "head": -3,
                            "shield_upper": 18, "shield_forearm": -29,
                            "near_thigh": 4, "shield_charge": 0.9,
                            "baton_charge": 0.4}, pitch=-2)),
        (0.85, held_shield({"root_y": 2, "torso": 4, "head": -3,
                            "shield_upper": 18, "shield_forearm": -29,
                            "near_thigh": 4, "shield_charge": 0.9,
                            "baton_charge": 0.4}, pitch=-2)),
        (1.0, held_shield({})),
    ], frames=8, duration_ms=110),
    "brace": pose_clip([
        (0.0, held_shield({})),
        (0.25, held_shield({"root_y": 7, "torso": 16, "head": -13,
                            "near_thigh": 23, "near_shin": -32,
                            "far_thigh": -14, "far_shin": 21,
                            "shield_upper": 22, "shield_forearm": -38,
                            "shield_charge": 1, "baton_upper": -11}, pitch=-2)),
        (0.78, held_shield({"root_y": 7, "torso": 16, "head": -13,
                            "near_thigh": 23, "near_shin": -32,
                            "far_thigh": -14, "far_shin": 21,
                            "shield_upper": 22, "shield_forearm": -38,
                            "shield_charge": 1, "baton_upper": -11}, pitch=-2)),
        (1.0, held_shield({})),
    ], frames=9, duration_ms=100),
    "shield_bash": pose_clip([
        (0.0, held_shield({})),
        (0.21, held_shield({"root_x": -16, "root_y": 4, "torso": -12,
                            "head": 7, "shield_upper": 24,
                            "shield_forearm": -32, "shield_charge": 0.95,
                            "near_thigh": 9, "far_thigh": -13}, pitch=-2)),
        (0.46, held_shield({"root_x": 55, "root_y": -7, "torso": 36,
                            "head": -23, "shield_upper": -29,
                            "shield_forearm": -7, "shield_charge": 1,
                            "shield_impact": 1, "near_thigh": -29,
                            "near_shin": 23, "far_thigh": 27,
                            "far_shin": -16, "baton_upper": -7}, pitch=0)),
        (0.61, held_shield({"root_x": 69, "root_y": -5, "torso": 38,
                            "head": -25, "shield_upper": -30,
                            "shield_forearm": -8, "shield_charge": 1,
                            "shield_impact": 0.45, "near_thigh": -27,
                            "near_shin": 20, "far_thigh": 25,
                            "far_shin": -12, "baton_upper": -8}, pitch=0)),
        (0.82, {"root_x": 42, "root_y": 7, "torso": 21,
                 "head": -13, "shield_upper": 5,
                 "shield_forearm": 12, "shield": 26,
                 "shield_charge": 0.15, "near_thigh": 8,
                 "far_thigh": -8}),
        (1.0, {"root_x": 12, "root_y": 5, "torso": 12,
               "head": -8, "shield_upper": 10,
               "shield_forearm": 15, "shield": 24,
               "shield_charge": 0.2}),
    ], frames=14, duration_ms=85),
    "baton_attack": pose_clip([
        (0.0, held_shield({})),
        (0.22, held_shield({"root_x": -5, "torso": -8,
                            "head": 6, "baton_upper": 100,
                            "baton_forearm": -20, "baton": -5,
                            "baton_charge": 0.8, "shield_upper": 8,
                            "shield_forearm": -13}, pitch=-2)),
        (0.42, held_shield({"root_x": -8, "torso": -9,
                            "head": 5, "baton_upper": 135,
                            "baton_forearm": -22, "baton": -12,
                            "baton_charge": 1, "shield_upper": 8,
                            "shield_forearm": -13}, pitch=-2)),
        (0.60, held_shield({"root_x": 12, "root_y": -2, "torso": 6,
                            "head": -6, "baton_upper": 184,
                            "baton_forearm": -10, "baton": -12,
                            "baton_charge": 1, "shield_upper": 10,
                            "bone.baton_forearm.z": 22,
                            "bone.baton_hand.z": 22,
                            "bone.baton.z": 22,
                            "shield_forearm": 15}, pitch=72)),
        (0.75, held_shield({"root_x": 17, "root_y": -4, "torso": 15,
                            "head": -12, "baton_upper": 198,
                            "baton_forearm": -14, "baton": -16,
                            "baton_charge": 1, "shield_upper": 18,
                            "bone.baton_forearm.z": 22,
                            "bone.baton_hand.z": 22,
                            "bone.baton.z": 22,
                            "shield_forearm": 19, "near_thigh": -10,
                            "far_thigh": 8}, pitch=83)),
        (0.91, held_shield({"root_x": 12, "root_y": -2, "torso": 10,
                            "head": -7, "baton_upper": 175,
                            "baton_forearm": -22, "baton": -12,
                            "baton_charge": 0.65, "shield_upper": 12,
                            "bone.baton_forearm.z": 14,
                            "bone.baton_hand.z": 14,
                            "bone.baton.z": 14,
                            "shield_forearm": 8}, pitch=45)),
        (1.0, held_shield({"baton_charge": 0.4})),
    ], frames=13, duration_ms=90),
    "recovery": pose_clip([
        (0.0, {"root_y": 3, "torso": 14, "head": -4,
               "shield_upper": 12, "shield_forearm": 22,
               "shield": 43, "shield_charge": 0.08,
               "baton_charge": 0.12, "near_thigh": 11,
               "far_thigh": -8}),
        (0.7, {"root_y": 3, "torso": 14, "head": -4,
               "shield_upper": 12, "shield_forearm": 22,
               "shield": 43, "shield_charge": 0.08,
               "baton_charge": 0.12, "near_thigh": 11,
               "far_thigh": -8}),
        (1.0, {}),
    ], frames=8, duration_ms=130),
    "hit": pose_clip([
        (0.0, {"root_x": -8, "torso": -18, "head": -7,
               "shield": 16, "shield_charge": 0.15,
               "baton_upper": 25}),
        (0.4, {"root_x": -4, "torso": -11, "head": -5,
               "shield": 12, "shield_charge": 0.15,
               "baton_upper": 14}),
        (1.0, {}),
    ], frames=5, duration_ms=92),
    "death": pose_clip([
        (0.0, {}),
        (0.5, {"root_y": 20, "torso": 23, "head": -11,
               "shield": 45, "shield_upper": 17,
               "baton_upper": 30, "baton_charge": 0,
               "shield_charge": 0, "near_thigh": 30,
               "near_shin": -32, "far_thigh": -26,
               "far_shin": 38}),
        (1.0, {"root_y": 37, "torso": 31, "head": -15,
               "shield": 65, "shield_upper": 35,
               "baton_upper": 68, "near_thigh": 46,
               "near_shin": -52, "far_thigh": -43,
               "far_shin": 58, "baton_charge": 0,
               "shield_charge": 0}),
    ], frames=9, duration_ms=115),
}

ACTOR_METADATA = {
    "actor": {"character_id": "npc_shock_warden", "display_name": "Shock Warden"},
    "authoring_description": {
        "visual_inspirations": [
            "Short, wide armored soldier with an oversized electrified riot shield.",
            "A black coat, steel mask, heavy boots, and a steel electric baton.",
            "Fictional gear emblems mark the authoritarian unit.",
        ],
        "rigging_notes": [
            "The SVG owns every part shape and joint marker.",
            "The shield, its electrical rim, and the baton have separate controls.",
            "The shield-bash and baton-swing rows include warning and recovery poses.",
        ],
    },
    "body": {"body_plan": "HumanoidBiped", "body_kind": "Standard",
             "mass_class": "Heavy", "traits": ["human", "soldier", "enemy", "evil", "armored"],
             "locomotion_hint": "Walk"},
    "visual": {"default_pose": "idle"},
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "combat.guard": {"animation": "guard", "events": []},
        "combat.block": {"animation": "brace", "events": []},
        "attack.shield_bash": {"animation": "shield_bash", "events": []},
        "attack.baton": {"animation": "baton_attack", "events": []},
        "reaction.exposed": {"animation": "recovery", "events": []},
        "reaction.hit": {"animation": "hit", "events": []},
        "life.death": {"animation": "death", "events": []},
    },
    "tags": ["human", "soldier", "enemy", "evil", "armored", "svg_rigged", "concept"],
}


def build() -> dict:
    joints = joint_positions(art.SVG)
    bones = []
    for name, (parent, _orig_x, _orig_y) in art.JOINTS.items():
        x, y = joints[name]
        if parent:
            px, py = joints[parent]
            offset = [(x - px) * SCALE, (y - py) * SCALE]
        else:
            offset = [(x - art.CENTER_X) * SCALE, (y - art.GROUND_Y) * SCALE]
        bones.append({"name": name, "parent": parent,
                      "offset": [round(v, 4) for v in offset],
                      "length": 0, "rest_angle": 0})
    parts = []
    for groups, name, bone, z, channel in art.PARTS:
        x, y = joints[bone]
        part = {"name": name, "bone": bone, "z": z,
                "kind": "sprite", "include": list(groups),
                "pivot": [x, y], "rest_angle": 0}
        if channel:
            part["opacity_channel"] = channel
            part["opacity_default"] = 0
        parts.append(part)
    return {
        "name": art.NAME,
        "frame": FRAME,
        "svg_source": {"path": "../../../../data/characters/shock_warden/shock_warden.svg",
                       "view": art.VIEW, "ref_dpi": 25.4, "scale": SCALE},
        "sprite_tuning": {"collision_scale": 1.1, "frame_sample_inset": 2},
        "palette": {}, "bones": bones, "parts": parts,
        "ik_legs": [], "ik_chains": [], "clips": CLIPS,
        "actor_metadata": ACTOR_METADATA,
    }


def main() -> None:
    RIG.parent.mkdir(parents=True, exist_ok=True)
    temp = RIG.with_suffix(".tmp")
    temp.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf8")
    temp.replace(RIG)
    # Keep the SVG catalog in sync with the rig. Update this file only.
    catalog, quality = svg_rig_tool.catalog_from_rigdoc(
        RIG, art.SVG, used_view_ids=set()
    )
    block = svg_rig_tool._serialize_character_block(
        [catalog], {catalog.view_id: quality}
    )
    svg_rig_tool.install_block(art.SVG, block)
    errors = svg_rig_tool.validate(art.SVG)
    if errors:
        raise ValueError(f"invalid Shock Warden SVG catalog: {errors}")
    print(f"wrote {RIG.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
