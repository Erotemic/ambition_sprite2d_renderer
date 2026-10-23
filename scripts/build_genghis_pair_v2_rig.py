#!/usr/bin/env python3
"""Build the rig documents of Genghis Can and Genghis Can't, look C (``genghis_can_v2``, ``genghis_cant_v2``).

    uv run python scripts/svg_art/genghis_pair_art.py --rig   # the two drawings, once
    uv run python scripts/build_genghis_pair_v2_rig.py

The drawing says where each part turns (``joints`` and ``BONES`` in the art
script). This script makes the skeleton from those joints, binds each part
layer to its bone, and authors the rows. It never draws. A channel is the turn
of a bone from the drawing, in degrees (positive clockwise on the screen: a
hanging limb swings back, the torso leans forward).

The rows are the five the pair has always had: ``idle``, ``walk``, ``talk``,
``interact``, ``taunt``. The pun is in the body, so it is in the rows too:
Can keeps pointing the way (he walks pointing), and his taunt thrusts the
point at the sky; Can't keeps his fist under his chin (he walks thinking), and
his taunt is a shrug with the hand fallen open.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ambition_sprite2d_renderer.devtools.svg_rig_tool import install_catalog  # noqa: E402

_spec = importlib.util.spec_from_file_location("genghis_pair_art", ROOT / "scripts" / "svg_art" / "genghis_pair_art.py")
art = importlib.util.module_from_spec(_spec)
sys.path.insert(0, str(ROOT / "scripts" / "svg_art"))
_spec.loader.exec_module(art)

PKG = ROOT / "ambition_sprite2d_renderer"

#: Frame pixels for each SVG unit.
SCALE = 0.4
FRAME = {"width": 150, "height": 176, "center_x": 64, "ground_y": 168, "ankle_h": 0, "supersample": 3, "render_scale": 1, "trim": False}


def out_path(who: str) -> Path:
    name = f"genghis_{who}_v2"
    return PKG / "targets" / "characters" / "rigged" / name / f"{name}.rig.json"


def expr(text: str) -> dict:
    return {"expr": text}


def ramp(a: float, b: float) -> str:
    """0 to 1 between ``a`` and ``b`` of the row, eased, held after."""
    return f"(lambda u: u*u*(3-2*u))(max(0.0, min(1.0, (t-{a})/{b - a})))"


def legs(near_u: str, far_u: str, near_l: str, far_l: str) -> dict:
    """Thigh and shin turns; each boot kept flat."""
    return {
        "near_leg_u": expr(near_u), "far_leg_u": expr(far_u),
        "near_leg_l": expr(near_l), "far_leg_l": expr(far_l),
        "near_foot": expr(f"-(({near_u}) + ({near_l}))"),
        "far_foot": expr(f"-(({far_u}) + ({far_l}))"),
    }


def face(shut: str = "False", talk: str = "False") -> dict:
    return {"eye_open": expr(f"0 if ({shut}) else 1"), "eye_shut": expr(f"1 if ({shut}) else 0"),
            "mouth_open": expr(f"1 if ({talk}) else 0")}


TALK = "floor(t*6 + 0.01) % 2 == 0"

CLIPS = {
    "can": {
        # Chest out, still pointing the way; the point steady, a blink.
        "idle": {
            "loop": True, "frames": 8, "duration_ms": 140,
            "channels": {
                "root_y": expr("0.6*sin(tau*t)"),
                "torso": expr("-0.6*sin(tau*t)"),
                "head": expr("0.8*sin(tau*t+0.6)"),
                "near_arm_u": expr("1.2*sin(tau*t)"),
                "near_arm_l": expr("-1.0*sin(tau*t+0.4)"),
                "far_arm_u": expr("0.6*sin(tau*t)"),
                "skirt": expr("0.4*sin(tau*t)"),
                **face(shut="0.8 < t < 0.95"),
            },
        },
        # He walks where he points: a long stride, chest first, the arm out.
        "walk": {
            "loop": True, "frames": 8, "duration_ms": 96,
            "channels": {
                "root_y": expr("4.0*abs(sin(tau*t))"),
                "torso": expr("-1 + 0.8*sin(2*tau*t)"),
                "head": expr("1 - 0.8*sin(2*tau*t)"),
                **legs("-18*sin(tau*t)", "18*sin(tau*t)", "26*max(0.0, cos(tau*t))", "26*max(0.0, -cos(tau*t))"),
                "near_arm_u": expr("1.5*sin(2*tau*t)"),
                "far_arm_u": expr("-8*sin(tau*t)"),
                "skirt": expr("-1.5*sin(2*tau*t)"),
                **face(),
            },
        },
        # Telling you: chin up, the head nods on the words, the finger jabs them.
        "talk": {
            "loop": True, "frames": 6, "duration_ms": 108,
            "channels": {
                "root_y": expr("-0.5*abs(sin(tau*t))"),
                "torso": expr("-1.5 + 0.8*sin(tau*t)"),
                "head": expr("-3 + 3*sin(tau*t)"),
                "near_arm_u": expr("-4 + 5*sin(tau*t)"),
                "near_arm_l": expr("-4*sin(tau*t+0.8)"),
                **face(talk=TALK),
            },
        },
        # He lifts the point to the far horizon, holds it, says so, lowers it.
        "interact": {
            "loop": False, "frames": 6, "duration_ms": 92,
            "channels": {
                "torso": expr(f"-2*{ramp(0.0, 0.4)} + 2*{ramp(0.7, 1.0)}"),
                "head": expr(f"-5*{ramp(0.0, 0.4)} + 5*{ramp(0.7, 1.0)}"),
                "near_arm_u": expr(f"-22*{ramp(0.0, 0.4)} + 22*{ramp(0.7, 1.0)}"),
                "near_arm_l": expr(f"6*{ramp(0.0, 0.4)} - 6*{ramp(0.7, 1.0)}"),
                **face(talk="0.4 < t < 0.7"),
            },
        },
        # "Yes. Next question.": the point thrust at the sky, chin up, a shout.
        "taunt": {
            "loop": False, "frames": 8, "duration_ms": 94,
            "channels": {
                "root_y": expr(f"-2*{ramp(0.0, 0.35)} + 2*{ramp(0.75, 1.0)}"),
                "torso": expr(f"-4*{ramp(0.0, 0.35)} + 4*{ramp(0.75, 1.0)}"),
                "head": expr(f"-10*{ramp(0.0, 0.35)} + 10*{ramp(0.75, 1.0)}"),
                "near_arm_u": expr(f"-48*{ramp(0.0, 0.35)} + 48*{ramp(0.75, 1.0)}"),
                "near_arm_l": expr(f"-6*{ramp(0.0, 0.35)} + 6*{ramp(0.75, 1.0)}"),
                "far_arm_u": expr(f"-6*{ramp(0.0, 0.35)} + 6*{ramp(0.75, 1.0)}"),
                **face(talk="0.3 < t < 0.8"),
            },
        },
    },
    "cant": {
        # Thinking: the fist rubs under his chin, the head goes "hm"; a blink.
        "idle": {
            "loop": True, "frames": 8, "duration_ms": 150,
            "channels": {
                "root_y": expr("0.5*sin(tau*t)"),
                "torso": expr("0.6*sin(tau*t)"),
                "head": expr("1.5*sin(tau*t)"),
                "near_arm_u": expr("-0.8*sin(2*tau*t)"),
                "near_arm_l": expr("2.5*sin(2*tau*t)"),
                "near_hand": expr("-2*sin(2*tau*t)"),
                "far_arm_u": expr("0.5*sin(tau*t)"),
                "skirt": expr("0.3*sin(tau*t)"),
                **face(shut="0.45 < t < 0.6"),
            },
        },
        # He walks still thinking: short steps, stooped, the fist at his chin.
        "walk": {
            "loop": True, "frames": 8, "duration_ms": 104,
            "channels": {
                "root_y": expr("2.5*abs(sin(tau*t))"),
                "torso": expr("2 + 0.5*sin(2*tau*t)"),
                "head": expr("2 - 0.6*sin(2*tau*t)"),
                **legs("-13*sin(tau*t)", "13*sin(tau*t)", "18*max(0.0, cos(tau*t))", "18*max(0.0, -cos(tau*t))"),
                "far_arm_u": expr("1.0*sin(tau*t)"),
                "skirt": expr("-1*sin(2*tau*t)"),
                **face(),
            },
        },
        # On the one hand, on the other: the fist leaves his chin and comes back.
        "talk": {
            "loop": True, "frames": 6, "duration_ms": 116,
            "channels": {
                "root_y": expr("-0.4*abs(sin(tau*t))"),
                "torso": expr("1 + 0.6*sin(tau*t)"),
                "head": expr("1 + 2*sin(tau*t+1.0)"),
                "near_arm_u": expr("-3*sin(tau*t)"),
                "near_arm_l": expr("9 + 9*sin(tau*t)"),
                "near_hand": expr("-6 - 6*sin(tau*t)"),
                **face(talk=TALK),
            },
        },
        # He leans in to look at the thing, thinks better of it, leans back.
        "interact": {
            "loop": False, "frames": 6, "duration_ms": 100,
            "channels": {
                "root_x": expr(f"2*{ramp(0.0, 0.4)} - 2*{ramp(0.7, 1.0)}"),
                "torso": expr(f"6*{ramp(0.0, 0.4)} - 6*{ramp(0.7, 1.0)}"),
                "head": expr(f"6*{ramp(0.0, 0.4)} - 6*{ramp(0.7, 1.0)}"),
                "near_arm_l": expr(f"-3*{ramp(0.0, 0.4)} + 3*{ramp(0.7, 1.0)}"),
                **face(shut="0.55 < t < 0.7"),
            },
        },
        # "Could I? Probably. Should I?": a shrug, the hand fallen open from his chin.
        "taunt": {
            "loop": False, "frames": 8, "duration_ms": 100,
            "channels": {
                "root_y": expr(f"-2*{ramp(0.0, 0.35)} + 2*{ramp(0.75, 1.0)}"),
                "torso": expr(f"-2*{ramp(0.0, 0.35)} + 2*{ramp(0.75, 1.0)}"),
                "head": expr(f"-6*{ramp(0.0, 0.35)} + 6*{ramp(0.75, 1.0)}"),
                "near_arm_u": expr(f"-8*{ramp(0.0, 0.35)} + 8*{ramp(0.75, 1.0)}"),
                "near_arm_l": expr(f"52*{ramp(0.0, 0.35)} - 52*{ramp(0.75, 1.0)}"),
                "near_hand": expr(f"-20*{ramp(0.0, 0.35)} + 20*{ramp(0.75, 1.0)}"),
                "far_arm_u": expr(f"-14*{ramp(0.0, 0.35)} + 14*{ramp(0.75, 1.0)}"),
                **face(talk="0.35 < t < 0.7"),
            },
        },
    },
}


def build(who: str) -> dict:
    joints = art.joints(who)
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
    for group, part, bone, z, channel in art.rig_parts(who):
        x, y = joints[art.BONES[bone][1]]
        entry = {"name": part, "bone": bone, "z": z, "kind": "sprite", "include": [group], "pivot": [round(x, 4), round(y, 4)], "rest_angle": 0}
        if channel:
            entry["opacity_channel"] = channel
            entry["opacity_default"] = 1 if channel == "eye_open" else 0
        parts.append(entry)
    name = f"genghis_{who}_v2"
    return {
        "name": name,
        "frame": FRAME,
        "svg_source": {"path": f"../../../../data/characters/{name}/{name}.svg", "view": art.rig_view(who), "ref_dpi": 25.4, "scale": SCALE},
        "sprite_tuning": {"collision_scale": 1.68, "frame_sample_inset": 1},
        "palette": {},
        "bones": bones,
        "parts": parts,
        "ik_legs": [],
        "ik_chains": [],
        "clips": CLIPS[who],
    }


def main() -> None:
    for who in ("can", "cant"):
        out = out_path(who)
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = out.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(build(who), indent=2) + "\n", encoding="utf8")
        tmp.replace(out)
        print(f"wrote {out.relative_to(ROOT)}")
        # The rig catalog block of this SVG only (``install_repo_metadata``
        # stamps every SVG of the repository that lacks one).
        if install_catalog(art.rig_out(who), [out]):
            print(f"catalog {art.rig_out(who).relative_to(ROOT)}")


if __name__ == "__main__":
    main()
