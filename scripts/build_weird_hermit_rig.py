#!/usr/bin/env python3
"""Build the Weird Hermit's rig document (``weird_hermit``).

    uv run python scripts/svg_art/weird_hermit_art.py   # the drawing, once
    uv run python scripts/build_weird_hermit_rig.py

The drawing says where each part turns (``JOINTS`` in the art script). This
script makes the skeleton from those joints, binds each part layer to its
bone, and authors the rows. It never draws. A channel is the turn of a bone
from the drawing, in degrees (positive clockwise on the screen: a hanging
limb swings back, the torso leans forward).

The rows are the seven he has always had: ``idle``, ``creep``,
``finger_jab``, ``grab``, ``curse_sneeze``, ``hurt``, ``death``.
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

_spec = importlib.util.spec_from_file_location("weird_hermit_art", ROOT / "scripts" / "svg_art" / "weird_hermit_art.py")
art = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(art)

PKG = ROOT / "ambition_sprite2d_renderer"
OUT = PKG / "targets" / "characters" / "rigged" / "weird_hermit" / "weird_hermit.rig.json"

#: Frame pixels for each SVG unit.
SCALE = 0.5
#: His centre line (the pelvis), in SVG units: the frame's centre.
CENTER_X = 252.0
FRAME = {"width": 240, "height": 224, "center_x": 112, "ground_y": 214, "ankle_h": 0, "supersample": 3, "render_scale": 1, "trim": False}

JOLT = "(1-t)*(1-t)"
EASE = "(t*t*(3-2*t))"


def expr(text: str) -> dict:
    return {"expr": text}


def legs(near_u: str, far_u: str, near_l: str, far_l: str) -> dict:
    """Thigh and shin turns; each foot kept flat."""
    return {
        "near_leg_u": expr(near_u), "far_leg_u": expr(far_u),
        "near_leg_l": expr(near_l), "far_leg_l": expr(far_l),
        "near_foot": expr(f"-(({near_u}) + ({near_l}))"),
        "far_foot": expr(f"-(({far_u}) + ({far_l}))"),
    }


def eyes(shut: str = "False", dead: str = "False") -> dict:
    return {"eye_shut": expr(f"1 if ({shut}) and not ({dead}) else 0"), "eye_dead": expr(f"1 if ({dead}) else 0"),
            "eye_open": expr(f"0 if ({shut}) or ({dead}) else 1")}


#: A key: 0 to 1 between ``a`` and ``b`` of the row, eased, held after.
def ramp(a: float, b: float) -> str:
    return f"(lambda u: u*u*(3-2*u))(max(0.0, min(1.0, (t-{a})/{b - a})))"


CLIPS = {
    # He mutters to himself: a slow sway, the fingers working, a blink.
    "idle": {
        "loop": True, "frames": 6, "duration_ms": 130,
        "channels": {
            "root_y": expr("0.8*sin(tau*t)"),
            "torso": expr("1.5*sin(tau*t)"),
            "head": expr("-2.5*sin(tau*t+0.6)"),
            "near_hand": expr("8*sin(2*tau*t)"), "far_hand": expr("-6*sin(2*tau*t+1)"),
            "near_arm_u": expr("2*sin(tau*t)"), "far_arm_u": expr("-2*sin(tau*t)"),
            **eyes(shut="0.8 < t < 0.95"),
        },
    },
    # A sneaking tiptoe: knees high, hunched lower, fingers out in front.
    "creep": {
        "loop": True, "frames": 8, "duration_ms": 95,
        "channels": {
            "root_y": expr("3 - 2.5*abs(sin(tau*t))"),
            "torso": expr("6 + 2*sin(2*tau*t)"),
            "head": expr("-6 - 2*sin(2*tau*t)"),
            **legs("-30*sin(tau*t) - 6", "30*sin(tau*t) - 6", "34*max(0.0, cos(tau*t)) + 8", "34*max(0.0, -cos(tau*t)) + 8"),
            "near_arm_u": expr("-24 + 6*sin(tau*t)"), "near_arm_l": expr("-10"), "near_hand": expr("10*sin(2*tau*t)"),
            "far_arm_u": expr("-18 - 6*sin(tau*t)"), "far_arm_l": expr("-10"),
        },
    },
    # He draws back and jabs one long finger: a crackle off the tip.
    "finger_jab": {
        "loop": False, "frames": 7, "duration_ms": 75,
        "channels": {
            "root_x": expr(f"-3*{ramp(0.0, 0.3)} + 9*{ramp(0.3, 0.5)}"),
            "torso": expr(f"-6*{ramp(0.0, 0.3)} + 14*{ramp(0.3, 0.5)}"),
            "head": expr(f"4*{ramp(0.0, 0.3)} - 10*{ramp(0.3, 0.5)}"),
            # Drawn back, then out straight at shoulder height.
            "near_arm_u": expr(f"30*{ramp(0.0, 0.3)} - 112*{ramp(0.3, 0.5)} + 82*{ramp(0.7, 1.0)}"),
            "near_arm_l": expr(f"-40*{ramp(0.0, 0.3)} + 76*{ramp(0.3, 0.5)} - 36*{ramp(0.7, 1.0)}"),
            "near_hand": expr(f"-12*{ramp(0.3, 0.5)} + 12*{ramp(0.7, 1.0)}"),
            **legs(f"-16*{ramp(0.3, 0.5)}", f"14*{ramp(0.3, 0.5)}", f"10*{ramp(0.3, 0.5)}", "0"),
            "fx_jab": expr("1 if 0.4 < t < 0.75 else 0"),
        },
    },
    # Both hands lunge out and clutch.
    "grab": {
        "loop": False, "frames": 7, "duration_ms": 85,
        "channels": {
            "root_x": expr(f"8*{ramp(0.2, 0.5)} - 6*{ramp(0.7, 1.0)}"),
            "torso": expr(f"16*{ramp(0.2, 0.5)} - 12*{ramp(0.7, 1.0)}"),
            "head": expr(f"-14*{ramp(0.2, 0.5)} + 10*{ramp(0.7, 1.0)}"),
            "near_arm_u": expr(f"-80*{ramp(0.2, 0.5)} + 60*{ramp(0.7, 1.0)}"),
            "near_arm_l": expr(f"30*{ramp(0.2, 0.5)} - 20*{ramp(0.7, 1.0)}"),
            "near_hand": expr(f"40*{ramp(0.5, 0.65)} - 40*{ramp(0.8, 1.0)}"),
            "far_arm_u": expr(f"-70*{ramp(0.2, 0.5)} + 52*{ramp(0.7, 1.0)}"),
            "far_hand": expr(f"36*{ramp(0.5, 0.65)} - 36*{ramp(0.8, 1.0)}"),
            **legs(f"-20*{ramp(0.2, 0.5)}", f"16*{ramp(0.2, 0.5)}", f"16*{ramp(0.2, 0.5)}", "0"),
            "fx_grab": expr("1 if 0.45 < t < 0.7 else 0"),
        },
    },
    # A wind-up of a sniff, head back, then the curse sneezed out of his nose.
    "curse_sneeze": {
        "loop": False, "frames": 7, "duration_ms": 90,
        "channels": {
            "torso": expr(f"-10*{ramp(0.0, 0.4)} + 22*{ramp(0.4, 0.55)} - 12*{ramp(0.75, 1.0)}"),
            "head": expr(f"-24*{ramp(0.0, 0.4)} + 40*{ramp(0.4, 0.55)} - 16*{ramp(0.75, 1.0)}"),
            "near_arm_u": expr(f"-20*{ramp(0.0, 0.4)} + 30*{ramp(0.4, 0.55)} - 10*{ramp(0.75, 1.0)}"),
            "far_arm_u": expr(f"-14*{ramp(0.0, 0.4)} + 20*{ramp(0.4, 0.55)} - 6*{ramp(0.75, 1.0)}"),
            "fx_sneeze": expr("1 if 0.5 < t < 0.9 else 0"),
            **eyes(shut="0.35 < t < 0.65"),
        },
    },
    # A blow: he flinches back, eyes screwed shut.
    "hurt": {
        "loop": False, "frames": 4, "duration_ms": 90,
        "channels": {
            "root_x": expr(f"-5*{JOLT}"),
            "torso": expr(f"-16*{JOLT}"),
            "head": expr(f"-14*{JOLT}"),
            "near_arm_u": expr(f"-30*{JOLT}"), "far_arm_u": expr(f"30*{JOLT}"),
            **legs(f"-10*{JOLT}", f"8*{JOLT}", "0", f"6*{JOLT}"),
            **eyes(shut="True"),
        },
    },
    # His knees go and he folds forward onto the ground.
    "death": {
        "loop": False, "frames": 8, "duration_ms": 110,
        "channels": {
            # He sinks onto his knees, then pitches forward on his face; as he
            # lies down he rises back to the ground line he knelt below.
            "root_y": expr(f"22*{ramp(0.0, 0.45)} - 22*{ramp(0.45, 0.85)}"),
            "root_x": expr(f"10*{ramp(0.45, 0.85)}"),
            "torso": expr(f"20*{ramp(0.0, 0.45)} + 44*{ramp(0.45, 0.85)}"),
            "head": expr(f"10*{ramp(0.45, 0.85)}"),
            **legs(f"-70*{ramp(0.0, 0.45)} + 10*{ramp(0.45, 0.85)}", f"-60*{ramp(0.0, 0.45)} + 10*{ramp(0.45, 0.85)}",
                   f"120*{ramp(0.0, 0.45)}", f"110*{ramp(0.0, 0.45)}"),
            "near_arm_u": expr(f"-40*{ramp(0.45, 0.85)}"), "far_arm_u": expr(f"-30*{ramp(0.45, 0.85)}"),
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
            entry["opacity_default"] = 1 if channel == "eye_open" else 0
        parts.append(entry)
    return {
        "name": "weird_hermit",
        "frame": FRAME,
        "svg_source": {"path": "../../../../data/characters/weird_hermit/weird_hermit.svg", "view": art.VIEW, "ref_dpi": 25.4, "scale": SCALE},
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
