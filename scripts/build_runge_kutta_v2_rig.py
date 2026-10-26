#!/usr/bin/env python3
"""Build the rig documents of Carl Runga v2 and Martin Cutta v2.

    uv run python scripts/svg_art/runge_kutta_duo_art.py --rig   # the drawings, once
    uv run python scripts/build_runge_kutta_v2_rig.py

The drawings (``data/characters/<name>_v2/<name>_v2_<view>.svg``) say where
each part turns (their joints). This script makes each view's skeleton from
those joints, binds each part layer to its bone, and authors the clips. It
never draws. A channel is the turn of a bone from the drawing, in degrees
(positive is clockwise on the screen: in the side view a hanging limb swings
back and the torso leans forward; in the front view his right arm, on the
left of the screen, swings out).

It writes four documents, ``rigged/<name>_v2/<name>_v2_{side,front}.rig.json``.
The side view has the rows of the game (``idle``, ``walk``, ``interact``,
``attack_side``, ``hit``, ``death``); the front view has ``talk``, ``taunt``
and the stills of the portraits (``front_idle``, ``seize``).

Runga is heavy and slow: a short stride, a big shove of the near arm. Cutta
is upright and dry: a neat stride, the ledger held to him, and he swats with it.
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

_spec = importlib.util.spec_from_file_location("runge_kutta_duo_art", ROOT / "scripts" / "svg_art" / "runge_kutta_duo_art.py")
art = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(art)

PKG = ROOT / "ambition_sprite2d_renderer"
RIGGED = PKG / "targets" / "characters" / "rigged"

#: Frame pixels for each SVG unit.
SCALE = 0.5
#: The frame: the ground 8 px above its bottom, the pelvis on its centre line.
FRAME = {"width": 320, "height": 352, "center_x": 160, "ground_y": 344, "ankle_h": 0, "supersample": 3, "render_scale": 1, "trim": False}
#: The walk keeps a foot on the ground the body stands on in every frame, and
#: the run's lowest stride touches it (``RigDocument.plant_offsets``).
FRAME["plant"] = {"walk": "each", "run": "row"}

JOLT = "(1-t)*(1-t)"


def expr(text: str) -> dict:
    return {"expr": text}


def ramp(a: float, b: float) -> str:
    """0 to 1 between ``a`` and ``b`` of the clip, eased, held after."""
    return f"(lambda u: u*u*(3-2*u))(max(0.0, min(1.0, (t-{a})/{b - a})))"


def turn(a, b) -> float:
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


def legs(near_u: str, far_u: str, near_l: str, far_l: str) -> dict:
    """Thigh and shin turns; each shoe kept flat."""
    return {
        "near_leg_u": expr(near_u), "far_leg_u": expr(far_u),
        "near_leg_l": expr(near_l), "far_leg_l": expr(far_l),
        "near_foot": expr(f"-(({near_u}) + ({near_l}))"),
        "far_foot": expr(f"-(({far_u}) + ({far_l}))"),
    }


def face(shut: str = "False", talk: str = "False") -> dict:
    return {"eyes_shut": expr(f"1 if ({shut}) else 0"), "mouth_open": expr(f"1 if ({talk}) else 0")}


# ---- the side view -----------------------------------------------------------------------------

def side_clips(who: str, J: dict) -> dict:
    heavy = who == "runga"
    # The near arm's drawn directions; the turns that hold it straight out ahead.
    upper = turn(J["near_arm_u"][1:], J["near_arm_l"][1:])
    fore = turn(J["near_arm_l"][1:], J["near_hand"][1:])
    reach_u, reach_l = round(-upper, 2), round(upper - fore, 2)
    straight_l = round(upper - fore, 2)
    # His height over the soles, the pelvis's, in SVG units (for the fall).
    pelvis_h = art.GROUND_Y - J["body"][2]
    stride = 18 if heavy else 24
    clips = {
        # Runga breathes deep and slow, his weight on his heels; Cutta stands
        # straight, the ledger at his side, and looks about him.
        "idle": {
            "loop": True, "frames": 8, "duration_ms": 150 if heavy else 135,
            "channels": {
                "root_y": expr(("1.0" if heavy else "0.6") + "*sin(tau*t)"),
                "torso": expr(("-1.5 + 1.4" if heavy else "-0.5 + 0.8") + "*sin(tau*t)"),
                "head": expr(("-1.0*sin(tau*t+0.6)" if heavy else "-2.0*sin(tau*t+0.6)")),
                "near_arm_u": expr("2.0*sin(tau*t)"), "near_hand": expr("-3*sin(tau*t+0.4)"),
                "far_arm_u": expr("-2.0*sin(tau*t)"),
                **face(shut="0.74 < t < 0.88"),
            },
        },
        # A heavy tread (Runga) or a neat one (Cutta), the far arm swinging.
        "walk": {
            "loop": True, "frames": 8, "duration_ms": 110 if heavy else 96,
            "channels": {
                "root_y": expr(("-3.0" if heavy else "-2.2") + "*(1-abs(sin(tau*t)))"),
                "torso": expr(("2 + 1.6" if heavy else "-0.5 + 1.0") + "*sin(2*tau*t)"),
                "head": expr(("-1 - 1.4" if heavy else "-1 - 1.0") + "*sin(2*tau*t)"),
                **legs(f"-{stride}*sin(tau*t)", f"{stride}*sin(tau*t)", f"{stride + 6}*max(0.0, cos(tau*t))", f"{stride + 6}*max(0.0, -cos(tau*t))"),
                "far_arm_u": expr("-20*sin(tau*t)"), "far_arm_l": expr("-14"),
                "near_arm_u": expr(("18" if heavy else "6") + "*sin(tau*t)"),
                "near_arm_l": expr(("-10" if heavy else "-4") + " + 4*sin(tau*t)"),
            },
        },
        # Runga reaches out and works something before him; Cutta raises the
        # ledger and reads from it, head down.
        "interact": {
            "loop": False, "frames": 6, "duration_ms": 105,
            "channels": (
                {
                    "torso": expr(f"6*{ramp(0.0, 0.4)}"),
                    "head": expr(f"6*{ramp(0.0, 0.4)}"),
                    "near_arm_u": expr(f"({reach_u} + 30)*{ramp(0.0, 0.4)}"),
                    "near_arm_l": expr(f"({reach_l} - 10)*{ramp(0.0, 0.4)} + 8*sin(2*tau*t)*{ramp(0.4, 0.6)}"),
                    "near_hand": expr(f"-20*{ramp(0.0, 0.4)} + 14*sin(2*tau*t)*{ramp(0.4, 0.6)}"),
                    "far_arm_u": expr(f"-14*{ramp(0.0, 0.4)}"),
                }
                if heavy else
                {
                    "head": expr(f"14*{ramp(0.0, 0.4)}"),
                    "torso": expr(f"2*{ramp(0.0, 0.4)}"),
                    "near_arm_u": expr(f"-34*{ramp(0.0, 0.4)}"),
                    "near_arm_l": expr(f"-72*{ramp(0.0, 0.4)}"),
                    "near_hand": expr(f"-30*{ramp(0.0, 0.4)}"),
                    "far_arm_u": expr(f"-26*{ramp(0.1, 0.5)}"), "far_arm_l": expr(f"-80*{ramp(0.1, 0.5)}"),
                    "far_hand": expr(f"-20*{ramp(0.1, 0.5)} + 10*sin(2*tau*t)*{ramp(0.5, 0.7)}"),
                    **face(shut="0.6 < t < 0.8"),
                }
            ),
        },
        "hit": {
            "loop": False, "frames": 4, "duration_ms": 92,
            "channels": {
                "root_x": expr(f"-6*{JOLT}"),
                "torso": expr(f"-12*{JOLT}"),
                "head": expr(f"-14*{JOLT}"),
                "near_arm_u": expr(f"-26*{JOLT}"), "far_arm_u": expr(f"30*{JOLT}"),
                "near_arm_l": expr(f"-20*{JOLT}"),
                **legs(f"-10*{JOLT}", f"8*{JOLT}", "0", f"6*{JOLT}"),
                **face(shut="True", talk="True"),
            },
        },
    }
    # He goes over backwards and lies flat. His lowest point stays on the
    # ground as he tips back about the pelvis: the heel at first, then the
    # back of his coat (about 30 units behind the pelvis line).
    fall = "(1.5708*(lambda u: u*u*(3-2*u))(max(0.0, min(1.0, (t-0.1)/0.7))))"
    clips["death"] = {
        "loop": False, "frames": 8, "duration_ms": 112,
        "channels": {
            "body": expr(f"-90*{ramp(0.1, 0.8)}"),
            "root_x": expr(f"-16*{ramp(0.1, 0.8)}"),
            "root_y": expr(f"{SCALE}*({pelvis_h:g} - max({pelvis_h:g}*cos({fall}) + 8*sin({fall}), 70*cos({fall}) + 30*sin({fall})))"),
            "torso": expr(f"6*{ramp(0.0, 0.3)} - 6*{ramp(0.3, 0.8)}"),
            "head": expr(f"-10*{ramp(0.0, 0.4)} + 18*{ramp(0.5, 0.9)}"),
            "near_arm_u": expr(f"-50*{ramp(0.0, 0.4)} + 60*{ramp(0.5, 0.9)}"),
            "near_arm_l": expr(f"-20*{ramp(0.0, 0.4)} + 40*{ramp(0.5, 0.9)}"),
            "far_arm_u": expr(f"-40*{ramp(0.0, 0.4)} + 50*{ramp(0.5, 0.9)}"),
            **legs(f"-20*{ramp(0.0, 0.5)} + 14*{ramp(0.5, 0.9)}", f"-6*{ramp(0.0, 0.5)}", f"16*{ramp(0.0, 0.5)} - 8*{ramp(0.5, 0.9)}", "0"),
            **face(shut="t >= 0.15", talk="0.1 < t < 0.6"),
        },
    }
    # The swipe of the game (`striker_swipe`: wind-up 0.28 s, strike 0.08 s,
    # recovery 0.32 s): eight frames of 85 ms, the blow at the fourth and fifth.
    if heavy:
        # Runga winds his near arm back and shoves with the heel of his hand,
        # his whole weight behind it.
        channels = {
            "root_x": expr(f"-4*{ramp(0.0, 0.35)} + 22*{ramp(0.35, 0.5)} - 18*{ramp(0.7, 1.0)}"),
            "root_y": expr(f"4*{ramp(0.35, 0.5)} - 4*{ramp(0.7, 1.0)}"),
            "torso": expr(f"-8*{ramp(0.0, 0.35)} + 22*{ramp(0.35, 0.5)} - 14*{ramp(0.7, 1.0)}"),
            "head": expr(f"4*{ramp(0.0, 0.35)} - 14*{ramp(0.35, 0.5)} + 10*{ramp(0.7, 1.0)}"),
            "near_arm_u": expr(f"44*{ramp(0.0, 0.35)} + ({reach_u} - 44 + 8)*{ramp(0.35, 0.5)} - ({reach_u} + 8)*{ramp(0.7, 1.0)}"),
            "near_arm_l": expr(f"-70*{ramp(0.0, 0.35)} + ({reach_l} + 70)*{ramp(0.35, 0.5)} - {reach_l}*{ramp(0.7, 1.0)}"),
            "near_hand": expr(f"-30*{ramp(0.35, 0.5)} + 30*{ramp(0.7, 1.0)}"),
            "far_arm_u": expr(f"-30*{ramp(0.0, 0.35)} + 60*{ramp(0.35, 0.5)} - 30*{ramp(0.7, 1.0)}"),
            "far_arm_l": expr(f"-40*{ramp(0.0, 0.5)} + 40*{ramp(0.7, 1.0)}"),
            **legs(f"-34*{ramp(0.35, 0.5)} + 34*{ramp(0.7, 1.0)}", f"8*{ramp(0.0, 0.35)} + 16*{ramp(0.35, 0.5)} - 24*{ramp(0.7, 1.0)}",
                   f"30*{ramp(0.35, 0.5)} - 30*{ramp(0.7, 1.0)}", f"6*{ramp(0.0, 0.35)} - 6*{ramp(0.7, 1.0)}"),
            **face(shut="0.3 < t < 0.42", talk="0.35 < t < 0.75"),
        }
    else:
        # Cutta lifts the ledger behind his head and brings it down, flat, on
        # whatever is before him.
        channels = {
            "root_x": expr(f"-3*{ramp(0.0, 0.35)} + 14*{ramp(0.35, 0.5)} - 11*{ramp(0.7, 1.0)}"),
            "torso": expr(f"-6*{ramp(0.0, 0.35)} + 16*{ramp(0.35, 0.5)} - 10*{ramp(0.7, 1.0)}"),
            "head": expr(f"-6*{ramp(0.0, 0.35)} + 2*{ramp(0.35, 0.5)} + 4*{ramp(0.7, 1.0)}"),
            # back and up behind him, then over the top and down ahead
            # (the recovery goes on round to hang: 150 + 140 + 70 is a whole turn)
            "near_arm_u": expr(f"150*{ramp(0.0, 0.35)} + 140*{ramp(0.35, 0.5)} + 70*{ramp(0.7, 1.0)}"),
            "near_arm_l": expr(f"-50*{ramp(0.0, 0.35)} + (50 + {straight_l})*{ramp(0.35, 0.5)} - {straight_l}*{ramp(0.7, 1.0)}"),
            "near_hand": expr(f"-20*{ramp(0.0, 0.35)} + 20*{ramp(0.35, 0.5)}"),
            "far_arm_u": expr(f"-20*{ramp(0.0, 0.35)} + 40*{ramp(0.35, 0.5)} - 20*{ramp(0.7, 1.0)}"),
            "far_arm_l": expr(f"-30*{ramp(0.0, 0.5)} + 30*{ramp(0.7, 1.0)}"),
            **legs(f"-26*{ramp(0.35, 0.5)} + 26*{ramp(0.7, 1.0)}", f"14*{ramp(0.35, 0.5)} - 14*{ramp(0.7, 1.0)}",
                   f"22*{ramp(0.35, 0.5)} - 22*{ramp(0.7, 1.0)}", "0"),
            **face(talk="0.4 < t < 0.7"),
        }
    clips["attack_side"] = {"loop": False, "frames": 8, "duration_ms": 85, "channels": channels}
    return clips


# ---- the front view ----------------------------------------------------------------------------

def front_clips(who: str, J: dict) -> dict:
    heavy = who == "runga"
    talk = "sin(2*tau*t) > -0.3"
    clips = {
        # The portrait's still: he looks at you.
        "front_idle": {"loop": True, "frames": 1, "duration_ms": 150, "channels": {}},
    }
    if heavy:
        # Runga lectures you: his left hand up, one finger for each evaluation.
        clips["talk"] = {
            "loop": True, "frames": 6, "duration_ms": 110,
            "channels": {
                "root_y": expr("-0.6*abs(sin(tau*t))"),
                "head": expr("-2 + 3*sin(tau*t)"),
                "left_arm_u": expr("-34 + 4*sin(tau*t)"), "left_arm_l": expr("-96 + 10*sin(2*tau*t)"),
                "left_hand": expr("-20"),
                "right_arm_u": expr("4*sin(tau*t)"),
                **face(talk=talk),
            },
        }
        # Scheming: his fingertips together before his waistcoat, a slow
        # rock and a laugh.
        clips["taunt"] = {
            "loop": True, "frames": 8, "duration_ms": 110,
            "channels": {
                "root_y": expr("-1.0*abs(sin(2*tau*t))"),
                "torso": expr("2*sin(tau*t)"),
                "head": expr("4 - 3*sin(tau*t)"),
                "right_arm_u": expr("52 + 3*sin(2*tau*t)"), "right_arm_l": expr("-130 - 4*sin(2*tau*t)"), "right_hand": expr("-30"),
                "left_arm_u": expr("-52 - 3*sin(2*tau*t)"), "left_arm_l": expr("130 + 4*sin(2*tau*t)"), "left_hand": expr("30"),
                **face(shut="sin(2*tau*t) > 0.3", talk="sin(2*tau*t) > -0.4"),
            },
        }
    else:
        # Cutta lifts the ledger to his chest and makes his point with the
        # other hand.
        clips["talk"] = {
            "loop": True, "frames": 6, "duration_ms": 105,
            "channels": {
                "root_y": expr("-0.4*abs(sin(tau*t))"),
                "head": expr("2*sin(tau*t)"),
                "right_arm_u": expr("-12"), "right_arm_l": expr("-64"), "right_hand": expr("-10"),
                "left_arm_u": expr("-26 + 4*sin(tau*t)"), "left_arm_l": expr("-70 + 12*sin(2*tau*t)"),
                "left_hand": expr("-10 + 10*sin(2*tau*t)"),
                **face(talk=talk),
            },
        }
        # Scheming: he holds the ledger up for you to see the weights, and
        # taps it.
        clips["taunt"] = {
            "loop": True, "frames": 8, "duration_ms": 110,
            "channels": {
                "head": expr("-4 + 2*sin(tau*t)"),
                "right_arm_u": expr("-30"), "right_arm_l": expr("-110"), "right_hand": expr("-20"),
                "left_arm_u": expr("-20"), "left_arm_l": expr("-84 + 14*max(0.0, sin(2*tau*t))"),
                **face(shut="0.7 < t < 0.85", talk="sin(2*tau*t) > 0.4"),
            },
        }
    # Seizing the Kernel: both hands thrown up and out to grab it.
    clips["seize"] = {
        "loop": True, "frames": 4, "duration_ms": 94,
        "channels": {
            "root_y": expr("-1.5*abs(sin(tau*t))"),
            "head": expr("-4 + 2*sin(tau*t)"),
            "right_arm_u": expr("136 + 6*sin(tau*t)"), "right_arm_l": expr("28 + 8*sin(tau*t)"), "right_hand": expr("10"),
            "left_arm_u": expr("-136 - 6*sin(tau*t)"), "left_arm_l": expr("-28 - 8*sin(tau*t)"), "left_hand": expr("-10"),
            **face(talk="True"),
        },
    }
    return clips


VIEW_CLIPS = {"side": side_clips, "front": front_clips}


def build(who: str, view: str) -> dict:
    name = f"{art.FILES[who]}_v2"
    joints = art.joints_of(who, view)
    cx = joints["body"][1]
    bones = []
    for bone, (parent, x, y) in joints.items():
        if parent:
            _, px, py = joints[parent]
            offset = [round((x - px) * SCALE, 4), round((y - py) * SCALE, 4)]
        else:
            offset = [round((x - cx) * SCALE, 4), round((y - art.GROUND_Y) * SCALE, 4)]
        bones.append({"name": bone, "parent": parent or None, "offset": offset, "length": 0, "rest_angle": 0})
    parts = []
    for group, _label, part, bone, z, channel in art.layers_of(who, view):
        _, x, y = joints[bone]
        entry = {"name": part, "bone": bone, "z": z, "kind": "sprite", "include": [group], "pivot": [x, y], "rest_angle": 0}
        if channel:
            entry["opacity_channel"] = channel
            entry["opacity_default"] = 0
        parts.append(entry)
    return {
        "name": f"{name}_{view}",
        "frame": FRAME,
        "svg_source": {"path": f"../../../../data/characters/{name}/{name}_{view}.svg", "view": art.view_label(who, view), "ref_dpi": 25.4,
                       "scale": SCALE},
        "sprite_tuning": {"collision_scale": 1.2, "frame_sample_inset": 1},
        "palette": {},
        "bones": bones,
        "parts": parts,
        "ik_legs": [],
        "ik_chains": [],
        "clips": VIEW_CLIPS[view](who, joints),
    }


def main() -> None:
    for who in ("runga", "cutta"):
        name = f"{art.FILES[who]}_v2"
        for view in ("side", "front"):
            out = RIGGED / name / f"{name}_{view}.rig.json"
            out.parent.mkdir(parents=True, exist_ok=True)
            tmp = out.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(build(who, view), indent=2) + "\n", encoding="utf8")
            tmp.replace(out)
            print(f"wrote {out.relative_to(ROOT)}")
    for changed in install_repo_metadata(ROOT):
        print(f"catalog {Path(changed).relative_to(ROOT)}")


if __name__ == "__main__":
    main()
