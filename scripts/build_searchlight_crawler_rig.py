#!/usr/bin/env python3
"""Build the Searchlight Crawler pose rig from the SVG draft's joint plan.

    cd tools/ambition_sprite2d_renderer
    uv run python scripts/build_searchlight_crawler_rig.py

The SVG owns the part art. The rig owns motion. This builder reads the part
list and joints from the same draft plan as the SVG generator. It does not
replace or modify the SVG.
"""

from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ambition_sprite2d_renderer.authoring.surface_gait import Gait, Leg

spec = importlib.util.spec_from_file_location(
    "searchlight_crawler_art",
    ROOT / "scripts" / "svg_art" / "searchlight_crawler_art.py",
)
assert spec is not None and spec.loader is not None
art = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = art
spec.loader.exec_module(art)

OUT = (
    ROOT
    / "ambition_sprite2d_renderer/targets/characters/rigged/searchlight_crawler/"
    "searchlight_crawler.rig.json"
)
SCALE = 0.36
FRAME = {
    "width": 288,
    "height": 224,
    "center_x": 144,
    "ground_y": 185,
    "ankle_h": 0,
    "supersample": 3,
    "render_scale": 1,
    "trim": False,
}


def expr(text: str) -> dict:
    return {"expr": text}


# The shape function starts and ends at zero. A hit uses the first frame.
BEAT = "(lambda u: u*u*(3-2*u))(max(0.0, min(1.0, t/0.26, (1-t)/0.26)))"
JOLT = "(1-t)*(1-t)"


# Use a four-beat wave. A small pair swings while most legs keep contact.
# The groups move around the body instead of pulling both sides in and out.
PHASE_GROUPS = {
    "near_rear_outer": 0.0, "far_front_inner": 0.0,
    "near_front_outer": 0.25, "far_rear_inner": 0.25,
    "far_rear_outer": 0.5, "near_front_inner": 0.5,
    "far_front_outer": 0.75, "near_rear_inner": 0.75,
}
GAIT = Gait(stride=26.0, stance=0.68, lift=18.0)


def leg_spec(name: str) -> Leg:
    pts = art.LEG_POINTS[name]
    ax, ay = pts[3]
    tx, ty = pts[4]
    pitch = math.degrees(math.atan2(ty-ay, tx-ax))
    return Leg(
        name=name,
        rest_tip=((tx-322.0)*SCALE, (ty-art.GROUND_Y)*SCALE),
        tarsus_length=math.dist(pts[3], pts[4])*SCALE,
        tarsus_pitch=pitch,
        phase=PHASE_GROUPS[name],
    )


def foot_channels() -> dict:
    channels = {}
    for name in art.LEG_POINTS:
        channels.update(GAIT.planar_channels(leg_spec(name)))
    return channels


NAME_TO_REST = {
    name: ((chain[3][0]-322.0)*SCALE, (chain[3][1]-art.GROUND_Y)*SCALE)
    for name, chain in art.LEG_POINTS.items()
}


# Each slot owns disjoint channels. Locomotion owns the foot IK goals.
# Game actions can select one clip per slot and combine the results.
ARTICULATION_SLOTS = {
    "aim": ["light", "bone.light.x", "bone.light.y"],
    "beam": ["beam_visible", "focus_visible", "alert_visible"],
    "iris": ["bone.shutter_upper.y", "bone.shutter_lower.y"],
    "alarm": ["antenna", "beacon_visible"],
    "vent": ["exhaust_hatch", "exhaust_visible"],
    "chassis": ["body"],
}


def articulation_clips() -> dict:
    return {
        "aim_scan": {"loop": True, "frames": 16, "duration_ms": 85,
                     "channels": {"light": expr("35*sin(tau*t)"),
                                  "bone.light.x": expr("2.0*sin(tau*t+0.4)"),
                                  "bone.light.y": expr("1.5*sin(tau*t+0.8)")}},
        "aim_track": {"loop": True, "frames": 8, "duration_ms": 110,
                      "channels": {"light": expr("12+4*sin(tau*t)")}},
        "beam_search": {"loop": True, "frames": 8, "duration_ms": 110,
                        "channels": {"beam_visible": expr("0.8"),
                                     "focus_visible": expr("0"),
                                     "alert_visible": expr("0")}},
        "beam_focus": {"loop": True, "frames": 8, "duration_ms": 110,
                       "channels": {"beam_visible": expr("0"),
                                    "focus_visible": expr("0.95"),
                                    "alert_visible": expr("0.75")}},
        "beam_off": {"loop": True, "frames": 4, "duration_ms": 120,
                     "channels": {"beam_visible": expr("0"),
                                  "focus_visible": expr("0"),
                                  "alert_visible": expr("0")}},
        "iris_close": {"loop": False, "frames": 12, "duration_ms": 60,
                       "channels": {"bone.shutter_upper.y": expr("7.4*t*t*(3-2*t)"),
                                    "bone.shutter_lower.y": expr("-7.4*t*t*(3-2*t)")}},
        "iris_open": {"loop": False, "frames": 12, "duration_ms": 60,
                      "channels": {"bone.shutter_upper.y": expr("7.4*(1-t*t*(3-2*t))"),
                                   "bone.shutter_lower.y": expr("-7.4*(1-t*t*(3-2*t))")}},
        "iris_blink": {"loop": True, "frames": 12, "duration_ms": 90,
                       "channels": {"bone.shutter_upper.y": expr("7.4*max(0,sin(tau*t))**2"),
                                    "bone.shutter_lower.y": expr("-7.4*max(0,sin(tau*t))**2")}},
        "alarm_flash": {"loop": True, "frames": 8, "duration_ms": 105,
                        "channels": {"antenna": expr("-11+3*sin(tau*t)"),
                                     "beacon_visible": expr("0.3+0.7*max(0,sin(tau*2*t))")}},
        "vent_cycle": {"loop": True, "frames": 10, "duration_ms": 120,
                       "channels": {"exhaust_hatch": expr("-28*max(0,sin(tau*t))"),
                                    "exhaust_visible": expr("0.4+0.5*max(0,sin(tau*t))")}},
        "chassis_brace": {"loop": True, "frames": 10, "duration_ms": 110,
                          "channels": {"body": expr("3.0*sin(tau*t)")}},
        "chassis_recoil": {"loop": False, "frames": 8, "duration_ms": 80,
                           "channels": {"body": expr(f"-5*{BEAT}")}},
    }


def clips() -> dict:
    return {
        "idle": {
            "loop": True, "frames": 8, "duration_ms": 130,
            "channels": {
                "root_y": expr("0"),
                "body": expr("0"),
                "light": expr("2*sin(tau*t+0.2)"),
                "antenna": expr("3.2*sin(tau*t+0.7)"),
                "beam_visible": expr("0"),
                "alert_visible": expr("0"),
            },
        },
        "walk": {
            "loop": True, "frames": 24, "duration_ms": 46,
            "channels": {
                "beam_visible": expr("0"),
                "alert_visible": expr("0"),
                **foot_channels(),
            },
        },
        "scan": {
            "loop": True, "frames": 16, "duration_ms": 125,
            "channels": {
                "body": expr("1.3*sin(tau*t)"),
                "light": expr("30*sin(tau*t)"),
                "antenna": expr("4.5*sin(tau*t+0.35)"),
                "beam_visible": expr("0.88"),
                "alert_visible": expr("0"),
            },
        },
        "alert": {
            "loop": False, "frames": 8, "duration_ms": 80,
            "channels": {
                "root_y": expr(f"4*{BEAT}"),
                "body": expr(f"-4*{BEAT}"),
                "light": expr(f"-20*{BEAT}"),
                "antenna": expr(f"10*{BEAT}"),
                "beam_visible": expr(f"0.12+0.48*{BEAT}"),
                "alert_visible": expr(f"0.15+0.85*{BEAT}"),
            },
        },
        "climb": {
            "loop": True, "frames": 12, "duration_ms": 100,
            "channels": {
                "body": expr("-30+3*sin(tau*t)"),
                "root_y": expr("-37-6*abs(sin(tau*t))"),
                "light": expr("16+8*sin(tau*t)"),
                "antenna": expr("7*sin(tau*t+0.5)"),
                "beam_visible": expr("0.6"),
                "alert_visible": expr("0"),
            },
        },
        "strike": {
            "loop": False, "frames": 8, "duration_ms": 95,
            "channels": {
                "root_y": expr(f"-6*{BEAT}"),
                "body": expr(f"6*{BEAT}"),
                "light": expr(f"-30*{BEAT}"),
                "antenna": expr(f"14*{BEAT}"),
                "beam_visible": expr("0.95"),
                "alert_visible": expr(f"0.5+0.5*{BEAT}"),
            },
        },
        "stun": {
            "loop": True, "frames": 8, "duration_ms": 125,
            "channels": {
                "root_y": expr("3+1.4*sin(tau*t)"),
                "body": expr("9+2*sin(tau*t)"),
                "light": expr("22+4*sin(tau*t+0.4)"),
                "antenna": expr("-23+4*sin(tau*t+0.2)"),
                "beam_visible": expr("0"),
                "alert_visible": expr("0.14+0.13*sin(tau*3*t)"),
            },
        },
        "hit": {
            "loop": False, "frames": 6, "duration_ms": 85,
            "channels": {
                "root_x": expr(f"-6*{JOLT}"),
                "body": expr(f"-8*{JOLT}"),
                "light": expr(f"13*{JOLT}"),
                "antenna": expr(f"-23*{JOLT}"),
                "beam_visible": expr("0"),
                "alert_visible": expr(f"0.35*{JOLT}"),
            },
        },
        **articulation_clips(),
    }


ACTOR_METADATA = {
    "actor": {"character_id": "npc_searchlight_crawler", "display_name": "Searchlight Crawler"},
    "authoring_description": {
        "visual_inspirations": [
            "A small armored searchlight on eight long mechanical spider legs.",
            "Thin hinged limbs, a faceted hull, and a strong lamp silhouette.",
            "A pale search cone and red warning marks show what the unit sees.",
        ],
        "rigging_notes": [
            "The SVG owns the part shapes. The rig owns the joints and motion.",
            "Each leg uses an articulated coxa, femur, tibia, and tarsus.",
            "The walk clip specifies foot targets for the shared IK solver.",
            "The beam and warning iris use separate opacity channels.",
            "The aim, beam, iris, beacon, vent, and chassis have independent controls.",
        ],
    },
    "body": {
        "body_plan": "Crawler",
        "body_kind": "Mechanical",
        "mass_class": "Medium",
        "traits": ["machine", "crawler", "surveillance", "enemy", "evil"],
        "locomotion_hint": "Walk",
    },
    "brain": {"default_preset": "searchlight_crawler_preview"},
    "actions": {"default_preset": "searchlight_crawler_preview"},
    "visual": {"default_pose": "idle"},
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "state.alert": {"animation": "alert", "events": []},
        "state.scan": {"animation": "scan", "events": []},
        "locomotion.climb": {"animation": "climb", "events": []},
        "attack.beam": {"animation": "strike", "events": []},
        "reaction.hit": {"animation": "hit", "events": []},
        "reaction.stun": {"animation": "stun", "events": []},
    },
    "tags": ["machine", "crawler", "enemy", "evil", "svg_rigged", "concept"],
}


def build() -> dict:
    # Convert the four-link SVG joints into an articulated bone chain. The
    # child starts at the end of its parent's measured segment, so the solver
    # and the vector art use the same lengths. Rest rotations are stored on
    # both the bones and the parts to keep the SVG unchanged at zero pose.
    chains = {}
    for name, coords in art.LEG_POINTS.items():
        directions = [math.degrees(math.atan2(b[1]-a[1], b[0]-a[0]))
                      for a, b in zip(coords, coords[1:])]
        lengths = [math.dist(a, b)*SCALE for a, b in zip(coords, coords[1:])]
        chains[name] = (directions, lengths)
    bones = []
    parts = []
    for name, (parent, x, y) in art.JOINTS.items():
        parts_of_leg = [(leg, i) for leg in art.LEG_POINTS
                        for i, segment in enumerate(art.SEGMENTS)
                        if name == f"{leg}_{segment}"]
        if parts_of_leg:
            leg, index = parts_of_leg[0]
            dirs, lengths = chains[leg]
            if index == 0:
                bx, by = art.JOINTS[parent][1:]
                offset = [(x-bx)*SCALE, (y-by)*SCALE]
                rest_angle = dirs[0]
            else:
                offset = [lengths[index-1], 0.0]
                rest_angle = dirs[index]-dirs[index-1]
            length = lengths[index]
        else:
            if parent:
                _, px, py = art.JOINTS[parent]
                offset = [(x-px)*SCALE, (y-py)*SCALE]
            else:
                offset = [(x-322.0)*SCALE, (y-art.GROUND_Y)*SCALE]
            rest_angle = 0.0
            length = 0.0
        bones.append({
            "name": name, "parent": parent,
            "offset": [round(v, 6) for v in offset],
            "length": round(length, 6), "rest_angle": round(rest_angle, 6),
        })
    rest_angles = {b["name"]: b["rest_angle"] for b in bones}
    for group, _label, part, bone, z, channel in art.LAYERS:
        _, x, y = art.JOINTS[bone]
        rest_world_angle = 0.0
        if bone in rest_angles and "_" in bone:
            for leg, (dirs, _lengths) in chains.items():
                for i, segment in enumerate(art.SEGMENTS):
                    if bone == f"{leg}_{segment}":
                        rest_world_angle = dirs[i]
        entry = {
            "name": part, "bone": bone, "z": z, "kind": "sprite",
            "include": [group], "pivot": [x, y],
            "rest_angle": round(rest_world_angle, 6),
        }
        if channel:
            entry["opacity_channel"] = channel
            entry["opacity_default"] = 0
        parts.append(entry)
    ik_chains = []
    for name, pts in art.LEG_POINTS.items():
        # Preserve the original raised-knee side of the target line.
        sx, sy = pts[1]
        kx, ky = pts[2]
        ax, ay = pts[3]
        side_of_line = (ax-sx)*(ky-sy) - (ay-sy)*(kx-sx)
        dirs, lens = chains[name]
        ik_chains.append({
            "upper": f"{name}_femur",
            "lower": f"{name}_tibia",
            "end": f"{name}_tarsus",
            "channel_prefix": f"{name}_contact",
            "rest_x": NAME_TO_REST[name][0],
            "rest_y": NAME_TO_REST[name][1],
            "rest_pitch": dirs[3],
            "bend": 1 if side_of_line < 0 else -1,
        })
    return {
        "name": "searchlight_crawler",
        "frame": FRAME,
        "svg_source": {
            "path": "../../../../data/characters/searchlight_crawler/searchlight_crawler.svg",
            "view": art.VIEW,
            "ref_dpi": 25.4,
            "scale": SCALE,
        },
        "sprite_tuning": {"collision_scale": 1.12, "frame_sample_inset": 2},
        "palette": {},
        "bones": bones,
        "parts": parts,
        "ik_legs": [],
        "ik_chains": ik_chains,
        "articulation_slots": ARTICULATION_SLOTS,
        "footfall": {
            "stride": GAIT.stride,
            "stance": GAIT.stance,
            "lift": GAIT.lift,
            "legs": {
                name: {
                    "rest_tip": list(leg_spec(name).rest_tip),
                    "tarsus_length": leg_spec(name).tarsus_length,
                    "tarsus_pitch": leg_spec(name).tarsus_pitch,
                    "phase": leg_spec(name).phase,
                }
                for name in art.LEG_POINTS
            },
        },
        "clips": clips(),
        "actor_metadata": ACTOR_METADATA,
    }


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf8")
    tmp.replace(OUT)
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
