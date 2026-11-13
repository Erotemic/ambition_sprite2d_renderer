#!/usr/bin/env python3
"""Build Full Stack's rig document (``full_stack_giant``).

    uv run python scripts/svg_art/full_stack_art.py   # the drawing, once
    uv run python scripts/build_full_stack_rig.py
    ./scripts/regen/sprites.sh --target full_stack_giant

The drawing says where each part turns (``JOINTS`` and ``BONES`` of the art
script). This script makes the skeleton, binds each part to its bone, and
authors the rows. A channel is the turn of a bone in degrees (positive
clockwise on the screen), or a move of the root in frame pixels.

The guitar's edge and the top of the amp head are ground in the game (the
catalog row ``npc_full_stack`` states them as still lines), so no row moves
the cabinet or the guitar more than a pixel or two: the arms and the amp
head play, the body keeps the beat.

- ``idle``: it plays: a steady strum, the head nods on the beat (the robot's
  head more than the amp under it). A mount with
  no conductor draws this row the whole fight.
- ``strum``: the power chord: the arm high, then down across the strings.
- ``riff``: the fretting hand runs up and down the neck.
- ``feedback``: the meters pin in the red and the cones glow.
- ``solo``: between the Boss's phases, while he holds his beat: the arm
  windmills over the strings, both heads bang, the cones flash.
- ``outro``: he has gone down; it plays him off: a slow strum, the robot's
  head bowed (the amp head, where he stands, barely moves).
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

_spec = importlib.util.spec_from_file_location("full_stack_art", ROOT / "scripts" / "svg_art" / "full_stack_art.py")
art = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(art)

PKG = ROOT / "ambition_sprite2d_renderer"
OUT = PKG / "targets" / "characters" / "rigged" / "full_stack" / "full_stack.rig.json"

#: Frame pixels for each SVG unit: the drawing is in frame pixels.
SCALE = 1.0
FRAME = {"width": art.SIZE[0], "height": art.SIZE[1], "center_x": art.CENTER_X, "ground_y": art.GROUND_Y, "ankle_h": 0,
         "supersample": 2, "render_scale": 1, "trim": False}


def expr(text: str) -> dict:
    return {"expr": text}


def ramp(a: float, b: float) -> str:
    """0 to 1 between ``a`` and ``b`` of the row, eased, held after."""
    return f"(lambda u: u*u*(3-2*u))(max(0.0, min(1.0, (t-{a})/{b - a})))"


#: Two beats a loop.
BEAT = "abs(sin(2*pi*t))"

CLIPS = {
    "idle": {
        "loop": True, "frames": 8, "duration_ms": 110,
        "channels": {
            "root_y": expr(f"1.5*{BEAT}"),
            "head": expr(f"3*{BEAT} - 1.5"),
            "robot_head": expr(f"5*{BEAT} - 2.5"),
            "near_arm_u": expr("-4*sin(2*tau*t)"),
            "near_arm_l": expr("14*sin(2*tau*t)"),
            "far_arm_u": expr("2*sin(tau*t)"),
            "far_arm_l": expr("-3*sin(tau*t)"),
            "glow": expr("0"),
        },
    },
    "strum": {
        "loop": False, "frames": 8, "duration_ms": 80,
        "channels": {
            "root_y": expr(f"-2*{ramp(0.0, 0.4)} + 4*{ramp(0.4, 0.55)} - 2*{ramp(0.7, 1.0)}"),
            "head": expr(f"-8*{ramp(0.0, 0.4)} + 14*{ramp(0.4, 0.55)} - 6*{ramp(0.7, 1.0)}"),
            "robot_head": expr(f"-14*{ramp(0.0, 0.4)} + 26*{ramp(0.4, 0.55)} - 12*{ramp(0.7, 1.0)}"),
            "near_arm_u": expr(f"-40*{ramp(0.0, 0.4)} + 40*{ramp(0.4, 0.55)}"),
            "near_arm_l": expr(f"-40*{ramp(0.0, 0.4)} + 60*{ramp(0.4, 0.55)} - 20*{ramp(0.7, 1.0)}"),
            "far_arm_l": expr(f"-6*{ramp(0.0, 0.4)} + 6*{ramp(0.7, 1.0)}"),
            "glow": expr(f"1 if 0.45 < t < 0.8 else 0"),
        },
    },
    "riff": {
        "loop": True, "frames": 8, "duration_ms": 70,
        "channels": {
            "root_y": expr(f"1*{BEAT}"),
            "head": expr("4*sin(2*tau*t)"),
            "robot_head": expr("8*sin(2*tau*t)"),
            "near_arm_l": expr("10*sin(4*tau*t)"),
            "far_arm_u": expr("-10*sin(tau*t)"),
            "far_arm_l": expr("12*sin(tau*t)"),
            "glow": expr("0"),
        },
    },
    "solo": {
        "loop": True, "frames": 8, "duration_ms": 70,
        "channels": {
            "root_y": expr(f"2*{BEAT}"),
            "head": expr("3*sin(2*tau*t)"),
            "robot_head": expr("16*sin(2*tau*t)"),
            "near_arm_u": expr("-34 + 30*sin(tau*t)"),
            "near_arm_l": expr("-20 + 40*sin(tau*t)"),
            "far_arm_u": expr("-6*sin(2*tau*t)"),
            "far_arm_l": expr("10*sin(2*tau*t)"),
            "glow": expr("1 if sin(2*tau*t) > 0 else 0"),
        },
    },
    "outro": {
        "loop": True, "frames": 8, "duration_ms": 160,
        "channels": {
            "root_y": expr("0.6*sin(tau*t)"),
            "head": expr("1.5 + 0.8*sin(tau*t)"),
            "robot_head": expr("9 + 2*sin(tau*t)"),
            "near_arm_u": expr("-3*sin(tau*t)"),
            "near_arm_l": expr("9*sin(tau*t)"),
            "far_arm_l": expr("-2*sin(tau*t)"),
            "glow": expr("0"),
        },
    },
    "feedback": {
        "loop": True, "frames": 6, "duration_ms": 90,
        "channels": {
            "root_y": expr("0.8*sin(3*tau*t)"),
            "head": expr("-6 + 1.5*sin(3*tau*t)"),
            "robot_head": expr("-10 + 3*sin(6*tau*t)"),
            "near_arm_u": expr("-20"),
            "near_arm_l": expr("-30 + 4*sin(3*tau*t)"),
            "glow": expr("1"),
        },
    },
}


def build() -> dict:
    joints = art.JOINTS
    cx = joints["pelvis"][0]
    bones = []
    for name, (parent, at) in art.BONES.items():
        x, y = joints[at]
        if parent:
            px, py = joints[art.BONES[parent][1]]
            offset = [round((x - px) * SCALE, 4), round((y - py) * SCALE, 4)]
        else:
            offset = [round((x - cx) * SCALE, 4), round((y - art.GROUND_Y) * SCALE, 4)]
        bones.append({"name": name, "parent": parent or None, "offset": offset, "length": 0, "rest_angle": 0})
    parts = []
    for group, _label, part, bone, z, channel in art.LAYERS:
        x, y = joints[art.BONES[bone][1]]
        entry = {"name": part, "bone": bone, "z": z, "kind": "sprite", "include": [group], "pivot": [x, y], "rest_angle": 0}
        if channel:
            entry["opacity_channel"] = channel
            entry["opacity_default"] = 0
        parts.append(entry)
    return {
        "name": "full_stack",
        "frame": FRAME,
        "svg_source": {"path": "../../../../data/characters/full_stack/full_stack.svg", "view": art.VIEW, "ref_dpi": 25.4,
                       "scale": SCALE},
        "sprite_tuning": {"collision_scale": 1.0, "frame_sample_inset": 1},
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
