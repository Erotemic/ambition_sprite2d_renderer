#!/usr/bin/env python3
"""Build the Colonial Statesman's rig document (``colonial_statesman``).

    uv run python scripts/svg_art/colonial_statesman_art.py   # the drawing, once
    uv run python scripts/build_colonial_statesman_rig.py

The drawing says where each part turns (``JOINTS`` in the art script). This
script makes the skeleton from those joints, binds each part layer to its
bone, and authors the rows. It never draws. A channel is the turn of a bone
from the drawing, in degrees (positive clockwise on the screen: a hanging
limb swings back, the torso leans forward).

The rows are the seven he has always had: ``idle``, ``walk``, ``address``,
``thrust`` (he draws his rapier and lunges), ``pistol`` (he draws his
flintlock and fires), ``hurt``, ``death``.
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

from ambition_sprite2d_renderer.devtools.svg_rig_tool import install_repo_metadata  # noqa: E402

_spec = importlib.util.spec_from_file_location("colonial_statesman_art", ROOT / "scripts" / "svg_art" / "colonial_statesman_art.py")
art = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(art)

PKG = ROOT / "ambition_sprite2d_renderer"
OUT = PKG / "targets" / "characters" / "rigged" / "colonial_statesman" / "colonial_statesman.rig.json"

#: Frame pixels for each SVG unit.
SCALE = 0.5
#: His centre line (the pelvis), in SVG units: the frame's centre.
CENTER_X = 270.0
FRAME = {"width": 320, "height": 352, "center_x": 160, "ground_y": 344, "ankle_h": 0, "supersample": 3, "render_scale": 1, "trim": False}
#: The walk keeps a foot on the ground the body stands on in every frame, and
#: the run's lowest stride touches it (``RigDocument.plant_offset``).
FRAME["plant"] = {"walk": "each", "run": "row"}

JOLT = "(1-t)*(1-t)"


def _turn(a, b):
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


_J = art.JOINTS
#: The near arm's drawn directions: the upper arm hangs down-back, the forearm points forward.
UPPER = _turn(_J["near_arm_u"][1:], _J["near_arm_l"][1:])
FORE = _turn(_J["near_arm_l"][1:], _J["near_hand"][1:])
#: The turns that hold the near arm straight out ahead at shoulder height.
REACH_U = round(-UPPER, 2)
REACH_L = round(UPPER - FORE, 2)


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


def eyes(shut: str = "False", dead: str = "False") -> dict:
    return {"eye_shut": expr(f"1 if ({shut}) and not ({dead}) else 0"), "eye_dead": expr(f"1 if ({dead}) else 0"),
            "eye_open": expr(f"0 if ({shut}) or ({dead}) else 1")}


#: The death fall, in radians: back about the pelvis.
FALL = "(1.5708*(lambda u: u*u*(3-2*u))(max(0.0, min(1.0, (t-0.1)/0.7))))"

CLIPS = {
    # He stands on his dignity: a slow breath, the speech in hand, a blink.
    "idle": {
        "loop": True, "frames": 6, "duration_ms": 130,
        "channels": {
            "root_y": expr("0.6*sin(tau*t)"),
            "torso": expr("-1 + 1.0*sin(tau*t)"),
            "head": expr("-1.5*sin(tau*t+0.6)"),
            "near_arm_u": expr("1.5*sin(tau*t)"), "near_hand": expr("-3*sin(tau*t+0.4)"),
            "far_arm_u": expr("-1.5*sin(tau*t)"),
            **eyes(shut="0.7 < t < 0.9"),
        },
    },
    # A stately walk, chin up, the speech held to him.
    "walk": {
        "loop": True, "frames": 8, "duration_ms": 96,
        "channels": {
            "root_y": expr("-2.2*(1-abs(sin(tau*t)))"),
            "torso": expr("-1 + 1.2*sin(2*tau*t)"),
            "head": expr("-2 - 1.0*sin(2*tau*t)"),
            **legs("-26*sin(tau*t)", "26*sin(tau*t)", "30*max(0.0, cos(tau*t))", "30*max(0.0, -cos(tau*t))"),
            "far_arm_u": expr("-18*sin(tau*t)"), "far_arm_l": expr("-12"),
            "near_arm_u": expr("5*sin(tau*t)"),
        },
    },
    # He declaims from his twelve pages, the far hand raised to the gallery.
    "address": {
        "loop": True, "frames": 6, "duration_ms": 112,
        "channels": {
            "root_y": expr("-0.6*abs(sin(tau*t))"),
            "torso": expr("-3 + 1.0*sin(tau*t)"),
            "head": expr("-8 + 2*sin(tau*t)"),
            "near_arm_u": expr("-30 + 3*sin(tau*t)"), "near_arm_l": expr("-24"),
            "near_hand": expr("40 + 4*sin(tau*t)"),
            "far_arm_u": expr("-92 + 10*sin(tau*t)"), "far_arm_l": expr("-28 + 8*sin(tau*t+0.8)"),
            "far_hand": expr("-30"),
            "mouth_open": expr("1 if sin(2*tau*t) > -0.2 else 0"),
        },
    },
    # He drops the speech, draws the rapier and lunges, the far hand up behind him.
    "thrust": {
        "loop": False, "frames": 7, "duration_ms": 82,
        "channels": {
            "root_x": expr(f"-3*{ramp(0.0, 0.2)} + 17*{ramp(0.2, 0.45)} - 8*{ramp(0.75, 1.0)}"),
            "root_y": expr(f"9*{ramp(0.2, 0.45)} - 5*{ramp(0.75, 1.0)}"),
            "torso": expr(f"-4*{ramp(0.0, 0.2)} + 14*{ramp(0.2, 0.45)} - 6*{ramp(0.75, 1.0)}"),
            "head": expr(f"2*{ramp(0.0, 0.2)} - 10*{ramp(0.2, 0.45)} + 4*{ramp(0.75, 1.0)}"),
            # en garde (the point up before him), then straight out at the lunge
            "near_arm_u": expr(f"-62*{ramp(0.0, 0.2)} + ({REACH_U} + 62)*{ramp(0.2, 0.45)} + 22*{ramp(0.75, 1.0)}"),
            "near_arm_l": expr(f"26*{ramp(0.0, 0.2)} + ({REACH_L} - 26)*{ramp(0.2, 0.45)} - 20*{ramp(0.75, 1.0)}"),
            "near_hand": expr(f"-40*{ramp(0.0, 0.2)} + 40*{ramp(0.2, 0.45)}"),
            "far_arm_u": expr(f"60*{ramp(0.0, 0.2)} + 60*{ramp(0.2, 0.45)} - 40*{ramp(0.75, 1.0)}"),
            "far_arm_l": expr(f"-70*{ramp(0.0, 0.45)} + 30*{ramp(0.75, 1.0)}"),
            "far_hand": expr(f"-30*{ramp(0.0, 0.45)}"),
            **legs(f"-46*{ramp(0.2, 0.45)} + 20*{ramp(0.75, 1.0)}", f"10*{ramp(0.0, 0.2)} + 26*{ramp(0.2, 0.45)} - 16*{ramp(0.75, 1.0)}",
                   f"40*{ramp(0.2, 0.45)} - 20*{ramp(0.75, 1.0)}", f"8*{ramp(0.0, 0.2)} - 8*{ramp(0.2, 0.45)}"),
            "prop_pages": expr("1 if t < 0.1 else 0"),
            "prop_rapier": expr("0 if t < 0.1 else 1"),
            "hilt_sheathed": expr("1 if t < 0.1 else 0"),
            "fx_thrust": expr("1 if 0.4 < t < 0.75 else 0"),
            "mouth_open": expr("1 if 0.3 < t < 0.8 else 0"),
        },
    },
    # He draws the flintlock, levels it at you, fires; the kick throws his hand up.
    "pistol": {
        "loop": False, "frames": 6, "duration_ms": 88,
        "channels": {
            "root_x": expr(f"-4*{ramp(0.55, 0.75)}"),
            "torso": expr(f"-2*{ramp(0.0, 0.4)} - 4*{ramp(0.55, 0.75)} + 4*{ramp(0.8, 1.0)}"),
            "head": expr(f"-2*{ramp(0.0, 0.4)} - 6*{ramp(0.55, 0.75)} + 6*{ramp(0.8, 1.0)}"),
            "near_arm_u": expr(f"({REACH_U} + 6)*{ramp(0.0, 0.4)} - 10*{ramp(0.55, 0.7)} + 10*{ramp(0.8, 1.0)}"),
            "near_arm_l": expr(f"({REACH_L} - 6)*{ramp(0.0, 0.4)} - 16*{ramp(0.55, 0.7)} + 16*{ramp(0.8, 1.0)}"),
            "far_arm_u": expr(f"20*{ramp(0.0, 0.4)}"), "far_arm_l": expr(f"-80*{ramp(0.0, 0.4)}"),
            "far_hand": expr(f"-20*{ramp(0.0, 0.4)}"),
            **legs("-8", f"10*{ramp(0.0, 0.4)}", "4", "0"),
            "prop_pages": expr("1 if t < 0.1 else 0"),
            "prop_pistol": expr("0 if t < 0.1 else 1"),
            "fx_shot": expr("1 if 0.5 < t < 0.75 else 0"),
            **eyes(shut="0.5 < t < 0.75"),
        },
    },
    # A blow: he flinches back, eyes screwed shut.
    "hurt": {
        "loop": False, "frames": 4, "duration_ms": 92,
        "channels": {
            "root_x": expr(f"-5*{JOLT}"),
            "torso": expr(f"-12*{JOLT}"),
            "head": expr(f"-14*{JOLT}"),
            "near_arm_u": expr(f"-24*{JOLT}"), "far_arm_u": expr(f"30*{JOLT}"),
            **legs(f"-10*{JOLT}", f"8*{JOLT}", "0", f"6*{JOLT}"),
            "mouth_open": expr("1"),
            **eyes(shut="True"),
        },
    },
    # He goes over backwards and lies flat, the speech still in his hand.
    "death": {
        "loop": False, "frames": 8, "duration_ms": 112,
        "channels": {
            "body": expr(f"-90*{ramp(0.1, 0.8)}"),
            "root_x": expr(f"-14*{ramp(0.1, 0.8)}"),
            # His lowest point stays on the ground as he tips back about the
            # pelvis (154 units above his soles; his coat tail hangs 65 below
            # it, 41 behind; his heel 10 behind).
            "root_y": expr(f"0.5*(154 - max(154*cos({FALL}) + 10*sin({FALL}), 65*cos({FALL}) + 41*sin({FALL})))"),
            "torso": expr(f"6*{ramp(0.0, 0.3)} - 6*{ramp(0.3, 0.8)}"),
            "head": expr(f"-10*{ramp(0.0, 0.4)} + 22*{ramp(0.5, 0.9)}"),
            # The arms fly up as he goes, then fall to lie along his sides.
            "near_arm_u": expr(f"-50*{ramp(0.0, 0.4)} + 60*{ramp(0.5, 0.9)}"),
            "near_arm_l": expr(f"-20*{ramp(0.0, 0.4)} + 50*{ramp(0.5, 0.9)}"),
            "near_hand": expr(f"30*{ramp(0.5, 0.9)}"),
            "far_arm_u": expr(f"-40*{ramp(0.0, 0.4)} + 50*{ramp(0.5, 0.9)}"),
            "far_arm_l": expr(f"-10*{ramp(0.5, 0.9)}"),
            **legs(f"-20*{ramp(0.0, 0.5)} + 14*{ramp(0.5, 0.9)}", f"-6*{ramp(0.0, 0.5)}", f"16*{ramp(0.0, 0.5)} - 8*{ramp(0.5, 0.9)}", "0"),
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
        "name": "colonial_statesman",
        "frame": FRAME,
        "svg_source": {"path": "../../../../data/characters/colonial_statesman/colonial_statesman.svg", "view": art.VIEW, "ref_dpi": 25.4,
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
