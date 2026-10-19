#!/usr/bin/env python3
"""Build the Creator's rig document (``creator``).

    uv run python scripts/svg_art/creator_art.py   # the drawing, once
    uv run python scripts/build_creator_rig.py

The drawing says where each part turns (``joints`` and ``BONES`` in the art
script). This script makes the skeleton from those joints, binds each part
layer to its bone, and authors the rows. It never draws. A channel is the turn
of a bone from the drawing, in degrees (positive clockwise on the screen: a
hanging limb swings back, the torso leans forward).

The rows are the four he has always had: ``idle``, ``speak``, ``gesture``,
``walk``. His far hand stays in his coat pocket; the near hand holds the
tablet, kept upright when the arm lifts it.
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

_spec = importlib.util.spec_from_file_location("creator_art", ROOT / "scripts" / "svg_art" / "creator_art.py")
art = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(art)

PKG = ROOT / "ambition_sprite2d_renderer"
OUT = PKG / "targets" / "characters" / "rigged" / "creator" / "creator.rig.json"

#: Frame pixels for each SVG unit.
SCALE = 0.4
FRAME = {"width": 160, "height": 192, "center_x": 70, "ground_y": 184, "ankle_h": 0, "supersample": 3, "render_scale": 1, "trim": False}


def expr(text: str) -> dict:
    return {"expr": text}


def ramp(a: float, b: float) -> str:
    """0 to 1 between ``a`` and ``b`` of the row, eased, held after."""
    return f"(lambda u: u*u*(3-2*u))(max(0.0, min(1.0, (t-{a})/{b - a})))"


def legs(near_u: str, far_u: str, near_l: str, far_l: str) -> dict:
    """Thigh and shin turns; each shoe kept flat."""
    return {
        "near_leg_u": expr(near_u), "far_leg_u": expr(far_u),
        "near_leg_l": expr(near_l), "far_leg_l": expr(far_l),
        "near_foot": expr(f"-(({near_u}) + ({near_l}))"),
        "far_foot": expr(f"-(({far_u}) + ({far_l}))"),
    }


def tablet_arm(upper: str, lower: str) -> dict:
    """The near arm, the tablet kept upright in its hand."""
    return {"near_arm_u": expr(upper), "near_arm_l": expr(lower), "near_hand": expr(f"-(({upper}) + ({lower}))")}


def face(shut: str = "False", talk: str = "False") -> dict:
    return {"eye_open": expr(f"0 if ({shut}) else 1"), "eye_shut": expr(f"1 if ({shut}) else 0"),
            "mouth_open": expr(f"1 if ({talk}) else 0")}


CLIPS = {
    # Reading his tablet, weight on his heels; a blink.
    "idle": {
        "loop": True, "frames": 6, "duration_ms": 145,
        "channels": {
            "root_y": expr("0.6*sin(tau*t)"),
            "torso": expr("-0.8*sin(tau*t)"),
            "head": expr("4 + 1.2*sin(tau*t+0.5)"),
            **tablet_arm("1.0*sin(tau*t)", "-1.5*sin(tau*t)"),
            "far_arm_u": expr("0.8*sin(tau*t)"),
            **face(shut="0.75 < t < 0.95"),
        },
    },
    # Explaining: the head nods on the words, the tablet hand marks them.
    "speak": {
        "loop": True, "frames": 6, "duration_ms": 110,
        "channels": {
            "root_y": expr("-0.6*abs(sin(tau*t))"),
            "torso": expr("-1 + 1.0*sin(tau*t)"),
            "head": expr("-2 + 3*sin(tau*t)"),
            **tablet_arm("-6 + 4*sin(tau*t)", "-8 + 8*sin(tau*t+0.8)"),
            **face(talk="floor(t*6 + 0.01) % 2 == 0"),
        },
    },
    # He holds the tablet up to show you, talks you through it, lowers it.
    "gesture": {
        "loop": False, "frames": 6, "duration_ms": 100,
        "channels": {
            "root_x": expr(f"2*{ramp(0.0, 0.35)} - 2*{ramp(0.75, 1.0)}"),
            "torso": expr(f"4*{ramp(0.0, 0.35)} - 4*{ramp(0.75, 1.0)}"),
            "head": expr(f"-6*{ramp(0.0, 0.35)} + 6*{ramp(0.75, 1.0)}"),
            **tablet_arm(f"-40*{ramp(0.0, 0.35)} + 40*{ramp(0.75, 1.0)}", f"-14*{ramp(0.0, 0.35)} + 14*{ramp(0.75, 1.0)}"),
            **face(talk="0.3 < t < 0.75 and floor(t*6 + 0.01) % 2 == 0"),
        },
    },
    # An unhurried walk, still half reading.
    "walk": {
        "loop": True, "frames": 8, "duration_ms": 95,
        "channels": {
            # lowest at full stride, where both legs are straight and slanted
            "root_y": expr("5.0*abs(sin(tau*t))"),
            "torso": expr("1.5 + 1.0*sin(2*tau*t)"),
            "head": expr("2 - 1.0*sin(2*tau*t)"),
            **legs("-24*sin(tau*t)", "24*sin(tau*t)", "32*max(0.0, cos(tau*t))", "32*max(0.0, -cos(tau*t))"),
            "far_arm_u": expr("-6*sin(tau*t)"),
            **tablet_arm("4*sin(tau*t)", "-2*sin(tau*t)"),
            **face(),
        },
    },
}


def build() -> dict:
    joints = art.joints()
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
            entry["opacity_default"] = 1 if channel == "eye_open" else 0
        parts.append(entry)
    return {
        "name": "creator",
        "frame": FRAME,
        "svg_source": {"path": "../../../../data/characters/creator/creator.svg", "view": art.VIEW, "ref_dpi": 25.4, "scale": SCALE},
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
