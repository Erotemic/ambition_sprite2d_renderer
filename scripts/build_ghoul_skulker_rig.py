#!/usr/bin/env python3
"""Build the Ghoul Skulker's rig document (``ghoul_skulker``).

    uv run python scripts/svg_art/ghoul_skulker_art.py   # the drawing, once
    uv run python scripts/build_ghoul_skulker_rig.py

The drawing says where each part turns (``JOINTS`` in the art script). This
script makes the skeleton from those joints, binds each part layer to its
bone, and authors the rows. It never draws. A channel is the turn of a bone
from the drawing, in degrees (positive clockwise on the screen: a hanging
limb swings back, the torso leans forward).

The rows are the seven it has always had: ``idle``, ``skulk``, ``claw``,
``pounce``, ``cackle``, ``hurt``, ``death``.
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

_spec = importlib.util.spec_from_file_location("ghoul_skulker_art", ROOT / "scripts" / "svg_art" / "ghoul_skulker_art.py")
art = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(art)

PKG = ROOT / "ambition_sprite2d_renderer"
OUT = PKG / "targets" / "characters" / "rigged" / "ghoul_skulker" / "ghoul_skulker.rig.json"

#: Frame pixels for each SVG unit.
SCALE = 0.5
#: Its centre line (the pelvis), in SVG units: the frame's centre.
CENTER_X = 270.0
FRAME = {"width": 256, "height": 224, "center_x": 112, "ground_y": 214, "ankle_h": 0, "supersample": 3, "render_scale": 1, "trim": False}

JOLT = "(1-t)*(1-t)"


def expr(text: str) -> dict:
    return {"expr": text}


#: A key: 0 to 1 between ``a`` and ``b`` of the row, eased, held after.
def ramp(a: float, b: float) -> str:
    return f"(lambda u: u*u*(3-2*u))(max(0.0, min(1.0, (t-{a})/{b - a})))"


def legs(near_u: str, far_u: str, near_l: str, far_l: str) -> dict:
    """Thigh and shin turns; each foot kept flat."""
    return {
        "near_leg_u": expr(near_u), "far_leg_u": expr(far_u),
        "near_leg_l": expr(near_l), "far_leg_l": expr(far_l),
        "near_foot": expr(f"-(({near_u}) + ({near_l}))"),
        "far_foot": expr(f"-(({far_u}) + ({far_l}))"),
    }


def face(shut: str = "False", dead: str = "False", gape: str = "False") -> dict:
    return {"eye_shut": expr(f"1 if ({shut}) and not ({dead}) else 0"), "eye_dead": expr(f"1 if ({dead}) else 0"),
            "eye_open": expr(f"0 if ({shut}) or ({dead}) else 1"),
            "mouth_open": expr(f"1 if ({gape}) else 0"), "mouth_shut": expr(f"0 if ({gape}) else 1")}


CLIPS = {
    # It sways where it stands, the long arms dangling, the claws twitching.
    "idle": {
        "loop": True, "frames": 6, "duration_ms": 130,
        "channels": {
            "root_y": expr("0.8*sin(tau*t)"),
            "torso": expr("1.5*sin(tau*t)"),
            "head": expr("-3*sin(tau*t+0.6)"),
            "near_arm_u": expr("3*sin(tau*t+0.5)"), "far_arm_u": expr("3*sin(tau*t+1.5)"),
            "near_hand": expr("8*sin(2*tau*t)"), "far_hand": expr("-6*sin(2*tau*t+1)"),
            **face(shut="0.8 < t < 0.95"),
        },
    },
    # A creeping skulk: hunched lower, knees high, the arms swinging loose.
    "skulk": {
        "loop": True, "frames": 8, "duration_ms": 95,
        "channels": {
            "root_y": expr("4 - 3*abs(sin(tau*t))"),
            "torso": expr("8 + 2*sin(2*tau*t)"),
            "head": expr("-8 - 2*sin(2*tau*t)"),
            **legs("-28*sin(tau*t) - 8", "28*sin(tau*t) - 8", "34*max(0.0, cos(tau*t)) + 12", "34*max(0.0, -cos(tau*t)) + 12"),
            "near_arm_u": expr("-6 + 14*sin(tau*t)"), "near_arm_l": expr("-6"), "near_hand": expr("6*sin(tau*t)"),
            "far_arm_u": expr("-6 - 14*sin(tau*t)"), "far_arm_l": expr("-6"),
            **face(),
        },
    },
    # The near arm drawn back low, then raked forward and up through its prey.
    "claw": {
        "loop": False, "frames": 7, "duration_ms": 82,
        "channels": {
            "root_x": expr(f"-3*{ramp(0.0, 0.3)} + 11*{ramp(0.3, 0.55)} - 8*{ramp(0.75, 1.0)}"),
            "torso": expr(f"-6*{ramp(0.0, 0.3)} + 22*{ramp(0.3, 0.55)} - 16*{ramp(0.75, 1.0)}"),
            "head": expr(f"4*{ramp(0.0, 0.3)} - 16*{ramp(0.3, 0.55)} + 12*{ramp(0.75, 1.0)}"),
            # the rake ends forward and low, clear of the face
            "near_arm_u": expr(f"36*{ramp(0.0, 0.3)} - 100*{ramp(0.3, 0.55)} + 64*{ramp(0.75, 1.0)}"),
            "near_arm_l": expr(f"-20*{ramp(0.0, 0.3)} + 6*{ramp(0.3, 0.55)} + 14*{ramp(0.75, 1.0)}"),
            "near_hand": expr(f"20*{ramp(0.0, 0.3)} - 56*{ramp(0.3, 0.55)} + 36*{ramp(0.75, 1.0)}"),
            "far_arm_u": expr(f"-20*{ramp(0.3, 0.55)} + 20*{ramp(0.75, 1.0)}"),
            **legs(f"-18*{ramp(0.3, 0.55)} + 18*{ramp(0.75, 1.0)}", f"14*{ramp(0.3, 0.55)} - 14*{ramp(0.75, 1.0)}",
                   f"12*{ramp(0.3, 0.55)} - 12*{ramp(0.75, 1.0)}", "0"),
            "fx_claw": expr("1 if 0.4 < t < 0.75 else 0"),
            **face(gape="0.35 < t < 0.7"),
        },
    },
    # Down into a crouch, then a leap with both claws out in front, and a landing.
    "pounce": {
        "loop": False, "frames": 6, "duration_ms": 78,
        "channels": {
            "root_y": expr(f"14*{ramp(0.0, 0.25)} - 50*{ramp(0.25, 0.5)} + 36*{ramp(0.55, 0.8)}"),
            "root_x": expr(f"16*{ramp(0.25, 0.55)} - 16*{ramp(0.6, 1.0)}"),
            "torso": expr(f"16*{ramp(0.0, 0.25)} + 20*{ramp(0.25, 0.5)} - 36*{ramp(0.6, 1.0)}"),
            "head": expr(f"-10*{ramp(0.0, 0.25)} - 18*{ramp(0.25, 0.5)} + 28*{ramp(0.6, 1.0)}"),
            **legs(f"-40*{ramp(0.0, 0.25)} + 70*{ramp(0.25, 0.5)} - 30*{ramp(0.6, 1.0)}",
                   f"-30*{ramp(0.0, 0.25)} + 60*{ramp(0.25, 0.5)} - 30*{ramp(0.6, 1.0)}",
                   f"60*{ramp(0.0, 0.25)} - 30*{ramp(0.25, 0.5)} - 30*{ramp(0.6, 1.0)}",
                   f"50*{ramp(0.0, 0.25)} - 10*{ramp(0.25, 0.5)} - 40*{ramp(0.6, 1.0)}"),
            "near_arm_u": expr(f"20*{ramp(0.0, 0.25)} - 104*{ramp(0.25, 0.5)} + 84*{ramp(0.6, 1.0)}"),
            "near_hand": expr(f"-40*{ramp(0.25, 0.5)} + 40*{ramp(0.6, 1.0)}"),
            "far_arm_u": expr(f"20*{ramp(0.0, 0.25)} - 96*{ramp(0.25, 0.5)} + 76*{ramp(0.6, 1.0)}"),
            "far_hand": expr(f"-36*{ramp(0.25, 0.5)} + 36*{ramp(0.6, 1.0)}"),
            "fx_claw": expr("1 if 0.45 < t < 0.75 else 0"),
            **face(gape="0.3 < t < 0.75"),
        },
    },
    # Head thrown back, mouth open, shoulders shaking, the claws wrung together.
    "cackle": {
        "loop": True, "frames": 6, "duration_ms": 108,
        "channels": {
            "root_y": expr("-1.5*abs(sin(2*tau*t))"),
            "torso": expr("-8 + 3*sin(2*tau*t)"),
            "head": expr("-16 + 5*sin(2*tau*t)"),
            "near_arm_u": expr("-34 + 4*sin(2*tau*t)"), "near_arm_l": expr("-56"), "near_hand": expr("-20 + 10*sin(4*tau*t)"),
            "far_arm_u": expr("-30 - 4*sin(2*tau*t)"), "far_arm_l": expr("-60"), "far_hand": expr("-20 - 10*sin(4*tau*t)"),
            **face(shut="True", gape="True"),
        },
    },
    # A blow: it flinches back, eyes screwed shut.
    "hurt": {
        "loop": False, "frames": 4, "duration_ms": 90,
        "channels": {
            "root_x": expr(f"-5*{JOLT}"),
            "torso": expr(f"-16*{JOLT}"),
            "head": expr(f"-14*{JOLT}"),
            "near_arm_u": expr(f"-30*{JOLT}"), "far_arm_u": expr(f"24*{JOLT}"),
            **legs(f"-10*{JOLT}", f"8*{JOLT}", "0", f"6*{JOLT}"),
            **face(shut="True", gape="True"),
        },
    },
    # Its knees buckle, then it topples forward flat on its face, the long
    # arms flung out in front along the ground.
    "death": {
        "loop": False, "frames": 8, "duration_ms": 112,
        "channels": {
            "root_y": expr(f"6*{ramp(0.0, 0.25)} + 29*{ramp(0.25, 0.75)} - 3*{ramp(0.75, 0.85)} + 3*{ramp(0.85, 1.0)}"),
            "root_x": expr(f"6*{ramp(0.25, 0.75)}"),
            "body": expr(f"55*{ramp(0.2, 0.75)}"),
            "torso": expr(f"6*{ramp(0.0, 0.25)} - 6*{ramp(0.25, 0.75)}"),
            "head": expr(f"-52*{ramp(0.4, 0.8)}"),
            # the thighs lie along the ground behind it, the knees bend and the
            # shins lift, the toes point down
            **legs(f"45*{ramp(0.2, 0.75)}", f"42*{ramp(0.2, 0.75)}", f"30*{ramp(0.0, 0.25)} + 10*{ramp(0.25, 0.75)}",
                   f"26*{ramp(0.0, 0.25)} + 10*{ramp(0.25, 0.75)}"),
            "near_foot": expr(f"-(45*{ramp(0.2, 0.75)} + 30*{ramp(0.0, 0.25)} + 10*{ramp(0.25, 0.75)}) + 35*{ramp(0.25, 0.75)}"),
            "far_foot": expr(f"-(42*{ramp(0.2, 0.75)} + 26*{ramp(0.0, 0.25)} + 10*{ramp(0.25, 0.75)}) + 35*{ramp(0.25, 0.75)}"),
            "near_arm_u": expr(f"-125*{ramp(0.15, 0.55)}"), "far_arm_u": expr(f"-118*{ramp(0.15, 0.55)}"),
            "near_arm_l": expr(f"-8*{ramp(0.25, 0.8)}"), "far_arm_l": expr(f"-10*{ramp(0.25, 0.8)}"),
            "near_hand": expr(f"-20*{ramp(0.5, 0.9)}"), "far_hand": expr(f"-20*{ramp(0.5, 0.9)}"),
            **face(shut="t < 0.6", dead="t >= 0.6"),
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
            entry["opacity_default"] = 1 if channel in art.DEFAULT_ON else 0
        parts.append(entry)
    return {
        "name": "ghoul_skulker",
        "frame": FRAME,
        "svg_source": {"path": "../../../../data/characters/ghoul_skulker/ghoul_skulker.svg", "view": art.VIEW, "ref_dpi": 25.4, "scale": SCALE},
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
