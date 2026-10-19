#!/usr/bin/env python3
"""Build Captain Pulse's rig document (``pulse_voyager_captain``).

    uv run python scripts/svg_art/pulse_voyager_captain_art.py   # the drawing, once
    uv run python scripts/build_pulse_voyager_captain_rig.py

The drawing says where each part turns (``JOINTS`` in the art script). This
script makes the skeleton from those joints, binds each part layer to its
bone, and authors the rows. It never draws.

Each bone rests at no turn, so a channel of a clip is the turn of that bone
from the drawing, in degrees (positive turns clockwise on the screen: a
torso leans forward, a hanging limb swings back). A boot is kept level by
turning it back by its leg's two turns.

The rows are the eight the Captain has always had: ``idle``, ``walk``,
``run``, ``talk``, ``dash``, ``celebrate``, ``hit``, ``death``.
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

_spec = importlib.util.spec_from_file_location("pulse_voyager_captain_art", ROOT / "scripts" / "svg_art" / "pulse_voyager_captain_art.py")
art = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(art)

PKG = ROOT / "ambition_sprite2d_renderer"
OUT = PKG / "targets" / "characters" / "rigged" / "pulse_voyager_captain" / "pulse_voyager_captain.rig.json"

#: Frame pixels for each SVG unit.
SCALE = 0.4
#: The drawing's centre line: the frame's centre, so a row mirrors about it.
CENTER_X = 262.0
FRAME = {"width": 224, "height": 224, "center_x": 112, "ground_y": 214, "ankle_h": 0, "supersample": 3, "render_scale": 1, "trim": False}

#: A beat that comes in, holds, and goes out: 0, then 1, then 0.
BEAT = "(lambda u: u*u*(3-2*u))(max(0.0, min(1.0, t/0.25, (1-t)/0.25)))"
#: A jolt: 1 at once, then it dies away.
JOLT = "(1-t)*(1-t)"
#: Eased 0 to 1 over the row.
EASE = "(t*t*(3-2*t))"


def expr(text: str) -> dict:
    return {"expr": text}


def eyes(**when: str) -> dict:
    """The eye sets, one shown at a time: each named set where its condition
    holds, the open eyes otherwise."""
    out = {f"eye_{k}": expr(f"1 if ({v}) else 0") for k, v in when.items()}
    shown = " or ".join(f"({v})" for v in when.values()) or "False"
    out["eye_open"] = expr(f"0 if ({shown}) else 1")
    return out


def legs(near_leg: str, far_leg: str, near_shin: str, far_shin: str) -> dict:
    return {
        "near_leg": expr(near_leg), "far_leg": expr(far_leg),
        "near_shin": expr(near_shin), "far_shin": expr(far_shin),
        "near_foot": expr(f"-(({near_leg}) + ({near_shin}))"),
        "far_foot": expr(f"-(({far_leg}) + ({far_shin}))"),
    }


CLIPS = {
    # He stands easy and hums: a breath, a glance, a blink.
    "idle": {
        "loop": True, "frames": 8, "duration_ms": 140,
        "channels": {
            "root_y": expr("0.8*sin(tau*t)"),
            "torso": expr("1.2*sin(tau*t)"),
            "head": expr("-1.6*sin(tau*t+0.5)"),
            "near_arm_upper": expr("2.0*sin(tau*t)"), "far_arm_upper": expr("-2.0*sin(tau*t)"),
            "near_arm_lower": expr("-4"), "far_arm_lower": expr("-4"),
            **eyes(shut="0.86 < t < 0.97"),
        },
    },
    # A brisk deck walk, arms swinging against the legs.
    "walk": {
        "loop": True, "frames": 8, "duration_ms": 90,
        "channels": {
            "root_y": expr("-2.4*(1-abs(sin(tau*t)))"),
            "torso": expr("2 + 1.5*sin(2*tau*t)"),
            "head": expr("-2 - 1.2*sin(2*tau*t)"),
            **legs("-32*sin(tau*t)", "32*sin(tau*t)", "40*max(0.0, cos(tau*t))", "40*max(0.0, -cos(tau*t))"),
            "near_arm_upper": expr("20*sin(tau*t)"), "far_arm_upper": expr("-20*sin(tau*t)"),
            "near_arm_lower": expr("-12 - 8*max(0.0, -sin(tau*t))"), "far_arm_lower": expr("-12 - 8*max(0.0, sin(tau*t))"),
        },
    },
    # A run: leaning in, arms pumping, the comet trail lit.
    "run": {
        "loop": True, "frames": 8, "duration_ms": 70,
        "channels": {
            "root_y": expr("-5*(1-abs(sin(tau*t)))"),
            "torso": expr("10 + 2*sin(2*tau*t)"),
            "head": expr("-8 - 2*sin(2*tau*t)"),
            **legs("-40*sin(tau*t)", "40*sin(tau*t)", "70*max(0.0, cos(tau*t))", "70*max(0.0, -cos(tau*t))"),
            "near_arm_upper": expr("40*sin(tau*t)"), "far_arm_upper": expr("-40*sin(tau*t)"),
            "near_arm_lower": expr("-80"), "far_arm_lower": expr("-80"),
            "fx_trail": expr("0.55 + 0.15*sin(2*tau*t)"),
        },
    },
    # He briefs the crew: a hand out on each point, the visor's meter talking.
    "talk": {
        "loop": True, "frames": 8, "duration_ms": 110,
        "channels": {
            "root_y": expr("-1.0*abs(sin(tau*2*t))"),
            "torso": expr("-2 + 1.5*sin(tau*2*t)"),
            "head": expr("-3 + 3.0*sin(tau*2*t)"),
            "near_arm_upper": expr("-48 + 10*sin(tau*2*t)"),
            "near_arm_lower": expr("-46 + 12*sin(tau*2*t+0.6)"),
            "far_arm_lower": expr("-6"),
            "mouth_talk": expr("1 if (t*4) % 1.0 < 0.6 else 0"),
        },
    },
    # Full burn: bent low, arms back, the comet trail streaming.
    "dash": {
        "loop": True, "frames": 6, "duration_ms": 70,
        "channels": {
            "root_y": expr("-2 + 1.0*sin(tau*t)"),
            "torso": expr("24"),
            "head": expr("-18"),
            **legs("-46", "38", "64", "34"),
            "near_arm_upper": expr("58 + 4*sin(tau*t)"), "far_arm_upper": expr("50 - 4*sin(tau*t)"),
            "near_arm_lower": expr("-18"), "far_arm_lower": expr("-18"),
            "fx_trail": expr("0.9 + 0.1*sin(2*tau*t)"),
            **eyes(happy="True"),
        },
    },
    # Both fists up, and small hops.
    "celebrate": {
        "loop": True, "frames": 8, "duration_ms": 100,
        "channels": {
            "root_y": expr("-8*abs(sin(tau*t))"),
            "torso": expr("-3 + 2*sin(tau*t)"),
            "head": expr("-6 + 2*sin(tau*t)"),
            # The near arm goes up behind the head, so the visor stays in view.
            "near_arm_upper": expr("-142 + 8*sin(tau*2*t)"), "near_arm_lower": expr("-30 + 8*sin(tau*2*t+0.5)"),
            "far_arm_upper": expr("-150 - 8*sin(tau*2*t)"), "far_arm_lower": expr("-20 - 8*sin(tau*2*t+0.5)"),
            "bone.near_arm_upper.z": {"const": -10}, "bone.near_arm_lower.z": {"const": -10}, "bone.near_hand.z": {"const": -10},
            **legs("-8*abs(sin(tau*t))", "8*abs(sin(tau*t))", "16*abs(sin(tau*t))", "16*abs(sin(tau*t))"),
            **eyes(happy="True"),
        },
    },
    # A blow: he rocks back, arms flung out.
    "hit": {
        "loop": False, "frames": 5, "duration_ms": 90,
        "channels": {
            "root_x": expr(f"-6*{JOLT}"),
            "torso": expr(f"-16*{JOLT}"),
            "head": expr(f"-14*{JOLT}"),
            "near_arm_upper": expr(f"-40*{JOLT}"), "far_arm_upper": expr(f"40*{JOLT}"),
            "near_arm_lower": expr(f"-30*{JOLT}"), "far_arm_lower": expr(f"-20*{JOLT}"),
            **legs(f"-12*{JOLT}", f"10*{JOLT}", "0", f"8*{JOLT}"),
            **eyes(hurt="True"),
        },
    },
    # He topples back onto the deck and his lights go out.
    "death": {
        "loop": False, "frames": 8, "duration_ms": 110,
        "channels": {
            # The body tips back about the hips; the legs fold down to the deck.
            "body": expr(f"-84*{EASE}"),
            "root_x": expr(f"-10*{EASE}"),
            "root_y": expr(f"6*{EASE} - 6*sin(3.14159*t)"),
            "head": expr(f"6*{EASE}"),
            "near_arm_upper": expr(f"-30*{EASE}"), "far_arm_upper": expr(f"-20*{EASE}"),
            "near_arm_lower": expr(f"-10*{EASE}"),
            # The legs hang from the body, so they first undo its tip, then fold.
            **legs(f"(84 - 18)*{EASE}", f"(84 - 6)*{EASE}", f"-24*{EASE}", f"-10*{EASE}"),
            **eyes(hurt="t < 0.5", dead="t >= 0.5"),
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
        "name": "pulse_voyager_captain",
        "frame": FRAME,
        "svg_source": {"path": "../../../../data/characters/pulse_voyager_captain/pulse_voyager_captain.svg", "view": art.VIEW,
                       "ref_dpi": 25.4, "scale": SCALE},
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
