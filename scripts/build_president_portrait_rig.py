#!/usr/bin/env python3
"""Build the President Portrait's rig document (``president_portrait``).

    uv run python scripts/svg_art/president_portrait_art.py   # the drawing, once
    uv run python scripts/build_president_portrait_rig.py

The drawing says where each part turns (``JOINTS`` in the art script). This
script makes the skeleton from those joints, binds each part layer to its
bone, and authors the rows. It never draws. A channel is the turn of a bone
from the drawing, in degrees (positive clockwise on the screen: his right
arm, on the viewer's left, swings out and up; his left arm swings in).

He faces us, as a portrait does. The rows are the seven he has always had:
``idle``, ``walk``, ``address``, ``decree``, ``oath``, ``hurt``, ``death``.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ambition_sprite2d_renderer.devtools.svg_rig_tool import install_repo_metadata  # noqa: E402

_spec = importlib.util.spec_from_file_location("president_portrait_art", ROOT / "scripts" / "svg_art" / "president_portrait_art.py")
art = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(art)

PKG = ROOT / "ambition_sprite2d_renderer"
OUT = PKG / "targets" / "characters" / "rigged" / "president_portrait" / "president_portrait.rig.json"

#: Frame pixels for each SVG unit.
SCALE = 0.5
#: His centre line, in SVG units: the frame's centre.
CENTER_X = art.CX
FRAME = {"width": 320, "height": 352, "center_x": 160, "ground_y": 344, "ankle_h": 0, "supersample": 3, "render_scale": 1, "trim": False}

JOLT = "(1-t)*(1-t)"
#: The death topple, in radians.
TOPPLE = "(1.5708*(lambda u: u*u*(3-2*u))(max(0.0, min(1.0, (t-0.1)/0.7))))"
EASE = "(t*t*(3-2*t))"


def expr(text: str) -> dict:
    return {"expr": text}


def ramp(a: float, b: float) -> str:
    """0 to 1 between ``a`` and ``b`` of the row, eased, held after."""
    return f"(lambda u: u*u*(3-2*u))(max(0.0, min(1.0, (t-{a})/{b - a})))"


def eyes(shut: str = "False", dead: str = "False") -> dict:
    return {"eye_shut": expr(f"1 if ({shut}) and not ({dead}) else 0"), "eye_dead": expr(f"1 if ({dead}) else 0"),
            "eye_open": expr(f"0 if ({shut}) or ({dead}) else 1")}


def level(hand: str, upper: str, lower: str, torso: str = "0") -> dict:
    """The hand held level, whatever its arm does (so what it holds stays upright)."""
    return {hand: expr(f"-(({upper}) + ({lower}) + ({torso}))")}


CLIPS = {
    # He stands for his portrait: a slow breath, his hand on his sword, a blink.
    "idle": {
        "loop": True, "frames": 6, "duration_ms": 130,
        "channels": {
            "root_y": expr("0.6*sin(tau*t)"),
            "torso": expr("0.8*sin(tau*t)"),
            "head": expr("-1.2*sin(tau*t+0.6)"),
            "left_arm_u": expr("1.5*sin(tau*t)"), "left_hand": expr("-2*sin(tau*t+0.5)"),
            "right_arm_u": expr("-0.8*sin(tau*t)"),
            **eyes(shut="0.7 < t < 0.9"),
        },
    },
    # A measured march toward us: a boot lifts, the other, his right arm swings.
    "walk": {
        "loop": True, "frames": 8, "duration_ms": 96,
        "channels": {
            "root_y": expr("-2.4*abs(sin(tau*t))"),
            "root_x": expr("1.5*sin(tau*t)"),
            "body": expr("1.5*sin(tau*t)"),
            "torso": expr("-1.0*sin(tau*t)"),
            "head": expr("-0.8*sin(tau*t)"),
            "bone.left_leg.y": expr("-9*max(0.0, sin(tau*t))"),
            "bone.left_leg.scale_y": expr("1 - 0.06*max(0.0, sin(tau*t))"),
            "bone.right_leg.y": expr("-9*max(0.0, -sin(tau*t))"),
            "bone.right_leg.scale_y": expr("1 - 0.06*max(0.0, -sin(tau*t))"),
            "left_arm_u": expr("6*sin(tau*t)"), "left_arm_l": expr("4*sin(tau*t)"),
            "right_arm_u": expr("-1.5*sin(tau*t)"),
        },
    },
    # He addresses the hall: his right arm out, the open hand, the mouth working.
    "address": {
        "loop": True, "frames": 6, "duration_ms": 112,
        "channels": {
            "root_y": expr("-0.6*abs(sin(tau*t))"),
            "torso": expr("-1.5 + 1.0*sin(tau*t)"),
            "head": expr("2 + 2*sin(tau*t)"),
            "left_arm_u": expr("48 + 8*sin(tau*t)"),
            "left_arm_l": expr("38 + 10*sin(tau*t+0.6)"),
            "left_hand": expr("-12 + 8*sin(tau*t+1.0)"),
            "mouth_open": expr("1 if sin(2*tau*t) > -0.2 else 0"),
        },
    },
    # He draws out the proclamation and holds it up to be read.
    "decree": {
        "loop": False, "frames": 7, "duration_ms": 82,
        "channels": {
            "root_y": expr(f"-2*{ramp(0.3, 0.55)} + 2*{ramp(0.8, 1.0)}"),
            "torso": expr(f"-3*{ramp(0.0, 0.3)} + 6*{ramp(0.3, 0.55)}"),
            "head": expr(f"-6*{ramp(0.3, 0.55)}"),
            "right_arm_u": expr(f"-30*{ramp(0.0, 0.3)} - 62*{ramp(0.3, 0.55)}"),
            "right_arm_l": expr(f"-40*{ramp(0.0, 0.3)} + 22*{ramp(0.3, 0.55)}"),
            **level("right_hand", f"-30*{ramp(0.0, 0.3)} - 62*{ramp(0.3, 0.55)}", f"-40*{ramp(0.0, 0.3)} + 22*{ramp(0.3, 0.55)}",
                    f"-3*{ramp(0.0, 0.3)} + 6*{ramp(0.3, 0.55)}"),
            "left_arm_u": expr(f"10*{ramp(0.3, 0.55)}"),
            "prop_decree": expr("1 if t > 0.15 else 0"),
            "fx_decree": expr("1 if 0.45 < t < 0.85 else 0"),
            "mouth_open": expr("1 if 0.55 < t < 0.95 else 0"),
        },
    },
    # The oath: his right hand raised, the book held to his heart.
    "oath": {
        "loop": False, "frames": 6, "duration_ms": 96,
        "channels": {
            "root_y": expr(f"-1.5*{ramp(0.2, 0.6)}"),
            "torso": expr(f"-2*{ramp(0.0, 0.6)}"),
            "head": expr(f"-4*{ramp(0.2, 0.6)}"),
            "left_arm_u": expr(f"92*{ramp(0.0, 0.6)}"),
            "left_arm_l": expr(f"88*{ramp(0.0, 0.6)}"),
            "left_hand": expr(f"-6*{ramp(0.0, 0.6)}"),
            "right_arm_u": expr(f"16*{ramp(0.0, 0.5)}"),
            "right_arm_l": expr(f"88*{ramp(0.0, 0.5)}"),
            **level("right_hand", f"16*{ramp(0.0, 0.5)}", f"88*{ramp(0.0, 0.5)}", f"-2*{ramp(0.0, 0.6)}"),
            "prop_book": expr("1"),
            "fx_oath": expr("1 if t > 0.55 else 0"),
            "mouth_open": expr("1 if 0.5 < t < 0.9 else 0"),
        },
    },
    # A blow: he rocks back on his heels, eyes screwed shut.
    "hurt": {
        "loop": False, "frames": 4, "duration_ms": 92,
        "channels": {
            "root_x": expr(f"-5*{JOLT}"),
            "root_y": expr(f"-2*{JOLT}"),
            "body": expr(f"-4*{JOLT}"),
            "torso": expr(f"-6*{JOLT}"),
            "head": expr(f"-10*{JOLT}"),
            "left_arm_u": expr(f"24*{JOLT}"), "left_arm_l": expr(f"20*{JOLT}"),
            "right_arm_u": expr(f"-20*{JOLT}"), "right_arm_l": expr(f"-20*{JOLT}"),
            "mouth_open": expr("1"),
            **eyes(shut="True"),
        },
    },
    # He topples sideways and lies at length, his hand still at his sword.
    "death": {
        "loop": False, "frames": 8, "duration_ms": 112,
        "channels": {
            "body": expr(f"-90*{ramp(0.1, 0.8)}"),
            "root_x": expr(f"-8*{ramp(0.1, 0.8)}"),
            # His lowest point stays on the ground as he tips about the pelvis
            # (164 units above his soles; his coat is 66 units to his side).
            # less a lift mid-topple, where the measured lowest point ran below the ground
            "root_y": expr(f"0.5*(164 - max(164*cos({TOPPLE}) + 22*sin({TOPPLE}), 66*sin({TOPPLE}))) - 28*sin(3.14159*max(0.0, min(1.0, (t-0.3)/0.55)))"),
            "torso": expr(f"-4*{ramp(0.0, 0.3)} + 4*{ramp(0.3, 0.8)}"),
            "head": expr(f"-8*{ramp(0.0, 0.4)} + 14*{ramp(0.5, 0.9)}"),
            "left_arm_u": expr(f"30*{ramp(0.0, 0.4)} - 46*{ramp(0.5, 0.9)}"),
            "left_arm_l": expr(f"20*{ramp(0.0, 0.4)} - 10*{ramp(0.5, 0.9)}"),
            "right_arm_u": expr(f"-24*{ramp(0.0, 0.4)} + 10*{ramp(0.5, 0.9)}"),
            "bone.left_leg.y": expr(f"-4*{ramp(0.1, 0.5)}"),
            "mouth_open": expr("1 if 0.1 < t < 0.6 else 0"),
            **eyes(shut="t < 0.6", dead="t >= 0.6"),
        },
    },
}


def build() -> dict:
    joints = art.JOINTS
    bones = []
    for name, (parent, x, y) in joints.items():
        if parent:
            _, px, py = joints[parent]
            offset = [round((x - px) * SCALE, 4), round((y - py) * SCALE, 4)]
        else:
            offset = [round((x - CENTER_X) * SCALE, 4), round((y - art.GROUND_Y) * SCALE, 4)]
        bones.append({"name": name, "parent": parent or None, "offset": offset, "length": 0, "rest_angle": 0})
    parts = []
    for group, _label, part, bone, z, channel in art.LAYERS:
        _, x, y = joints[bone]
        entry = {"name": part, "bone": bone, "z": z, "kind": "sprite", "include": [group], "pivot": [x, y], "rest_angle": 0}
        if channel:
            entry["opacity_channel"] = channel
            entry["opacity_default"] = 1 if channel in art.SHOWN else 0
        parts.append(entry)
    return {
        "name": "president_portrait",
        "frame": FRAME,
        "svg_source": {"path": "../../../../data/characters/president_portrait/president_portrait.svg", "view": art.VIEW, "ref_dpi": 25.4,
                       "scale": SCALE},
        "sprite_tuning": {"collision_scale": 1.2, "frame_sample_inset": 1},
        "palette": {},
        "bones": bones,
        "parts": parts,
        "ik_legs": [],
        "ik_chains": [],
        "clips": CLIPS,
    }


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf8")
    tmp.replace(OUT)
    print(f"wrote {OUT.relative_to(ROOT)}")
    for changed in install_repo_metadata(ROOT):
        print(f"catalog {Path(changed).relative_to(ROOT)}")


if __name__ == "__main__":
    main()
