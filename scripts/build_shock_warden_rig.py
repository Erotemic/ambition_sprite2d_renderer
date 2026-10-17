#!/usr/bin/env python3
"""Build the Shock Warden pose rig from the edited SVG.

    uv run python scripts/build_shock_warden_rig.py

The SVG owns the drawing and joint marker positions. This script owns the
rest hierarchy, sprite bindings, and authored clips. It does not draw art.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "scripts/svg_art/shock_warden_art.py"
SPEC = importlib.util.spec_from_file_location("shock_warden_art", ART)
art = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(art)
RIG = ROOT / "ambition_sprite2d_renderer/targets/characters/rigged/shock_warden/shock_warden.rig.json"
SCALE = 0.52
FRAME = {"width": 420, "height": 324, "center_x": 210, "ground_y": 225,
         "ankle_h": 0, "supersample": 3, "render_scale": 1, "trim": False}


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
    keys = set(REST)
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
    markers = {}
    for node in root.iter():
        name = node.get("data-rig-joint")
        if name:
            if name in markers:
                raise ValueError(f"duplicate joint marker: {name}")
            markers[name] = (float(node.attrib["cx"]), float(node.attrib["cy"]))
    wanted = set(art.JOINTS)
    if set(markers) != wanted:
        raise ValueError(f"joint markers mismatch: missing={wanted - set(markers)} extra={set(markers) - wanted}")
    return markers


CLIPS = {
    "idle": {"loop": True, "frames": 8, "duration_ms": 135,
             "channels": {**{key: {"const": value} for key, value in REST.items()},
                          "root_y": expr("0.7*sin(tau*t)"),
                          "torso": expr("0.7*sin(tau*t)"),
                          "head": expr("-1.2*sin(tau*t+0.25)"),
                          "shield": expr("0.8*sin(tau*t+0.6)"),
                          "shield_charge": expr("0.56+0.12*sin(tau*2*t)"),
                          "baton_charge": expr("0.45+0.12*sin(tau*2*t+0.7)")}},
    "walk": {"loop": True, "frames": 10, "duration_ms": 105,
             "channels": {**{key: {"const": value} for key, value in REST.items()},
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
                          "baton_upper": expr("-4*sin(tau*t)")}},
    "guard": pose_clip([(0.0, {}), (0.3, {"shield_upper": -6, "shield": -4,
                                          "shield_charge": 0.9}),
                        (0.8, {"shield_upper": -6, "shield": -4, "shield_charge": 0.9}),
                        (1.0, {})], frames=8, duration_ms=110),
    "brace": pose_clip([(0.0, {}),
                        (0.24, {"root_y": 8, "torso": 8, "head": -6,
                                "near_thigh": 14, "near_shin": -22, "far_thigh": -8,
                                "far_shin": 17, "shield_upper": 9,
                                "shield_forearm": -19, "shield": -8,
                                "shield_charge": 1}),
                        (0.76, {"root_y": 8, "torso": 8, "head": -6,
                                "near_thigh": 14, "near_shin": -22, "far_thigh": -8,
                                "far_shin": 17, "shield_upper": 9,
                                "shield_forearm": -19, "shield": -8,
                                "shield_charge": 1}),
                        (1.0, {})], frames=9, duration_ms=100),
    "shield_bash": pose_clip([(0.0, {}),
                        (0.23, {"root_x": -8, "root_y": 6, "torso": -8,
                                "shield_upper": 10, "shield_forearm": 10,
                                "shield": 8, "shield_charge": 0.9,
                                "near_thigh": -11, "far_thigh": 14}),
                        (0.47, {"root_x": 27, "root_y": -3, "torso": 13,
                                "shield_upper": -28, "shield_forearm": -17,
                                "shield": 32, "shield_charge": 1,
                                "shield_impact": 1, "near_thigh": -24,
                                "near_shin": 22, "far_thigh": 20,
                                "far_shin": -9}),
                        (0.65, {"root_x": 39, "root_y": -2, "torso": 14,
                                "shield_upper": -27, "shield_forearm": -18,
                                "shield": 31, "shield_charge": 0.95,
                                "shield_impact": 0.3,
                                "near_thigh": -19, "far_thigh": 24}),
                        (0.83, {"root_x": 28, "root_y": 12, "torso": 19,
                                "shield_upper": 15, "shield_forearm": 30,
                                "shield": 25, "shield_charge": 0.15,
                                "near_thigh": 8}),
                        (1.0, {"root_x": 0, "shield_charge": 0.4})],
                        frames=12, duration_ms=88),
    "baton_attack": pose_clip([(0.0, {}),
                        (0.2, {"baton_upper": 100, "baton_forearm": -18,
                                "baton": -12, "shield": -8,
                                "baton_charge": 0.8}),
                        (0.42, {"baton_upper": 126, "baton_forearm": -14,
                                 "baton": -18, "torso": -6,
                                 "baton_charge": 1}),
                        (0.54, {"baton_upper": 217, "baton_forearm": 27,
                                 "baton_hand": -5, "baton": -34,
                                 "torso": 8, "root_x": 8,
                                 "baton_charge": 1}),
                        (0.73, {"baton_upper": 243, "baton_forearm": 22,
                                 "baton": -45, "torso": 13,
                                 "root_x": 12, "baton_charge": 1}),
                        (1.0, {"baton_charge": 0.5})], frames=11, duration_ms=90),
    "recovery": pose_clip([(0.0, {"root_y": 9, "torso": 14,
                                   "head": 12, "shield_upper": 13,
                                   "shield_forearm": 24, "shield": 41,
                                   "shield_charge": 0.08, "baton_charge": 0.12,
                                   "near_thigh": 10, "far_thigh": -9}),
                           (0.7, {"root_y": 9, "torso": 14,
                                  "head": 12, "shield_upper": 13,
                                  "shield_forearm": 24, "shield": 41,
                                  "shield_charge": 0.08, "baton_charge": 0.12,
                                  "near_thigh": 10, "far_thigh": -9}),
                           (1.0, {})], frames=8, duration_ms=130),
    "hit": pose_clip([(0.0, {"root_x": -8, "torso": -18, "head": -19,
                               "shield": 18, "shield_charge": 0.15,
                               "baton_upper": 22}),
                      (0.4, {"root_x": -4, "torso": -11, "head": -12,
                               "shield": 12, "shield_charge": 0.15,
                               "baton_upper": 15}),
                      (1.0, {})], frames=5, duration_ms=92),
    "death": pose_clip([(0.0, {}),
                        (0.5, {"root_y": 20, "torso": 23,
                               "head": 25, "shield": 45,
                               "shield_upper": 17,
                               "baton_upper": 30, "baton_charge": 0,
                               "shield_charge": 0,
                               "near_thigh": 30, "near_shin": -32,
                               "far_thigh": -26, "far_shin": 38}),
                        (1.0, {"root_y": 37, "torso": 31,
                               "head": 32, "shield": 65,
                               "shield_upper": 35, "baton_upper": 68,
                               "near_thigh": 46, "near_shin": -52,
                               "far_thigh": -43, "far_shin": 58,
                               "baton_charge": 0, "shield_charge": 0})],
                       frames=9, duration_ms=115),
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
    print(f"wrote {RIG.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
