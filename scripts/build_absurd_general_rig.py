#!/usr/bin/env python3
"""Build the General's rig document (``absurd_general``).

    uv run python scripts/svg_art/absurd_general_art.py   # the drawing, once
    uv run python scripts/build_absurd_general_rig.py

The drawing says where each part turns (``JOINTS`` in the art script). This
script makes the skeleton from those joints, binds each part layer to its
bone, and authors the rows. It never draws.

Each bone rests at no turn, so a channel of a clip is the turn of that bone
from the drawing, in degrees (positive turns clockwise on the screen). He
stands with his arms akimbo; a clip turns an arm a long way to raise it.

The rows are the six the General has always had: ``idle``, ``walk``,
``talk``, ``interact``, ``celebrate``, ``hit``. His cap is a bone of its own:
it lags his head a little, and a blow knocks it back.
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

_spec = importlib.util.spec_from_file_location("absurd_general_art", ROOT / "scripts" / "svg_art" / "absurd_general_art.py")
art = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(art)

PKG = ROOT / "ambition_sprite2d_renderer"
OUT = PKG / "targets" / "characters" / "rigged" / "absurd_general" / "absurd_general.rig.json"

#: Frame pixels for each SVG unit.
SCALE = 0.35
#: He stands at the middle of his frame, so a row can be mirrored about it.
FRAME = {"width": 232, "height": 224, "center_x": 116, "ground_y": 214, "ankle_h": 0, "supersample": 3, "render_scale": 1, "trim": False}

#: A beat that comes in, holds, and goes out: 0, then 1, then 0.
BEAT = "(lambda u: u*u*(3-2*u))(max(0.0, min(1.0, t/0.25, (1-t)/0.25)))"
#: A jolt: 1 at once, then it dies away.
JOLT = "(1-t)*(1-t)"


def expr(text: str) -> dict:
    return {"expr": text}


def mouth(open_when: str) -> dict:
    """The two mouths, one shown at a time."""
    return {"mouth_open": expr(f"1 if {open_when} else 0"), "mouth_grit": expr(f"0 if {open_when} else 1")}


def eyes(shut_when: str) -> dict:
    return {"eye_shut": expr(f"1 if {shut_when} else 0"), "eye_open": expr(f"0 if {shut_when} else 1")}


CLIPS = {
    # He stands and breathes hard through his teeth.
    "idle": {
        "loop": True, "frames": 8, "duration_ms": 140,
        "channels": {
            "root_y": expr("0.9*sin(tau*t)"),
            "torso": expr("1.0*sin(tau*t)"),
            "head": expr("-1.6*sin(tau*t+0.5)"),
            "hat": expr("2.2*sin(tau*t+1.2)"),
            "near_arm_upper": expr("1.5*sin(tau*t)"),
            "far_arm_upper": expr("-1.5*sin(tau*t)"),
            **eyes("0.86 < t < 0.97"),
        },
    },
    # Short fast steps under a coat that does not move much: he waddles.
    "walk": {
        "loop": True, "frames": 8, "duration_ms": 85,
        "channels": {
            "root_y": expr("-2.2*abs(sin(tau*t))"),
            "torso": expr("3.0*sin(tau*t)"),
            "head": expr("-2.4*sin(tau*t)"),
            "hat": expr("5.0*sin(tau*t+0.9)"),
            "near_leg": expr("30*sin(tau*t)"),
            "far_leg": expr("-30*sin(tau*t)"),
            "near_foot": expr("-30*sin(tau*t) - 14*max(0.0, cos(tau*t))"),
            "far_foot": expr("30*sin(tau*t) - 14*max(0.0, -cos(tau*t))"),
            "near_arm_upper": expr("4*sin(tau*t)"),
            "far_arm_upper": expr("4*sin(tau*t)"),
        },
    },
    # He shouts, and jabs his near hand at you on each word.
    "talk": {
        "loop": True, "frames": 8, "duration_ms": 110,
        "channels": {
            "root_y": expr("-1.2*abs(sin(tau*2*t))"),
            "torso": expr("4 + 2.0*sin(tau*2*t)"),
            "head": expr("3.0*sin(tau*2*t)"),
            "hat": expr("4.0*sin(tau*2*t+0.9)"),
            "near_arm_upper": expr("-84 + 9*sin(tau*2*t)"),
            "near_arm_lower": expr("16 + 12*sin(tau*2*t+0.6)"),
            "bone.near_arm_lower.z": {"const": 12},
            **mouth("(t*4) % 1.0 < 0.55"),
        },
    },
    # A salute: the near hand to the peak of the hat, the chest out.
    "interact": {
        "loop": False, "frames": 6, "duration_ms": 95,
        "channels": {
            "torso": expr(f"-4*{BEAT}"),
            "head": expr(f"-3*{BEAT}"),
            "hat": expr(f"3*sin(tau*t)*{BEAT}"),
            "near_arm_upper": expr(f"-166*{BEAT}"),
            "near_arm_lower": expr(f"64*{BEAT}"),
            "bone.near_arm_lower.z": {"const": 26},
        },
    },
    # Both fists up, and small hops.
    "celebrate": {
        "loop": True, "frames": 8, "duration_ms": 100,
        "channels": {
            "root_y": expr("-7*abs(sin(tau*t))"),
            "torso": expr("2.5*sin(tau*t)"),
            "head": expr("-4 + 2*sin(tau*t)"),
            "hat": expr("7*sin(tau*t+0.9)"),
            "near_arm_upper": expr("124 + 9*sin(tau*2*t)"),
            "near_arm_lower": expr("58 + 8*sin(tau*2*t+0.5)"),
            "far_arm_upper": expr("-124 - 9*sin(tau*2*t)"),
            "far_arm_lower": expr("-58 - 8*sin(tau*2*t+0.5)"),
            "near_leg": expr("10*sin(tau*t)"),
            "far_leg": expr("-10*sin(tau*t)"),
            **mouth("True"),
            **eyes("True"),
        },
    },
    # A blow: he goes back, and his cap goes back farther.
    "hit": {
        "loop": False, "frames": 5, "duration_ms": 90,
        "channels": {
            "root_x": expr(f"-5*{JOLT}"),
            "torso": expr(f"-12*{JOLT}"),
            "head": expr(f"-10*{JOLT}"),
            "hat": expr(f"-22*{JOLT}"),
            "near_arm_upper": expr(f"38*{JOLT}"),
            "far_arm_upper": expr(f"-38*{JOLT}"),
            "near_leg": expr(f"-14*{JOLT}"),
            "far_leg": expr(f"10*{JOLT}"),
            **mouth("True"),
            **eyes("True"),
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
            # The root: over the ground by the height of its joint.
            offset = [round((x - 320.0) * SCALE, 4), round((y - art.GROUND_Y) * SCALE, 4)]
        bones.append({"name": name, "parent": parent or None, "offset": offset, "length": 0, "rest_angle": 0})
    parts = []
    for group, _label, part, bone, z, channel in art.LAYERS:
        _, x, y = joints[bone]
        entry = {"name": part, "bone": bone, "z": z, "kind": "sprite", "include": [group], "pivot": [x, y], "rest_angle": 0}
        if channel:
            entry["opacity_channel"] = channel
            if channel in ("eye_open", "mouth_grit"):
                entry["opacity_default"] = 1
        parts.append(entry)
    return {
        "name": "absurd_general",
        "frame": FRAME,
        "svg_source": {"path": "../../../../data/characters/absurd_general/absurd_general.svg", "view": art.VIEW, "ref_dpi": 25.4, "scale": SCALE},
        "sprite_tuning": {"collision_scale": 1.15, "frame_sample_inset": 2},
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
