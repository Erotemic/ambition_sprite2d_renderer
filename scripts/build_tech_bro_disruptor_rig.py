#!/usr/bin/env python3
"""Draw Chadwick Disruptor III's SVG once and build his rig (``tech_bro_disruptor``).

    uv run python scripts/build_tech_bro_disruptor_rig.py           # the rig (and the SVG if absent)
    uv run python scripts/build_tech_bro_disruptor_rig.py --redraw  # redraw the SVG first

The drawing is look A (``founder``) of ``scripts/svg_art/chadwick/chadwick_robot_drafts.py``,
which Jon chose on 2026-10-18; once written, the SVG owns the art. This
script makes the skeleton from the drawing's joints, binds each part layer to
its bone, and authors the rows. A channel is the turn of a bone from the
drawing, in degrees (positive clockwise on the screen).

The rows are the eight Chadwick has always had: ``idle``, ``walk``, ``talk``,
``charge``, ``cast``, ``celebrate``, ``hit``, ``death``.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "svg_art"))

from ambition_sprite2d_renderer.devtools.svg_rig_tool import install_repo_metadata  # noqa: E402

_spec = importlib.util.spec_from_file_location("chadwick_robot_drafts", ROOT / "scripts" / "svg_art" / "chadwick" / "chadwick_robot_drafts.py")
art = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(art)
import svgkit  # noqa: E402

PKG = ROOT / "ambition_sprite2d_renderer"
SVG = PKG / "data" / "characters" / "tech_bro_disruptor" / "tech_bro_disruptor.svg"
OUT = PKG / "targets" / "characters" / "rigged" / "tech_bro_disruptor" / "tech_bro_disruptor.rig.json"
LOOK = "founder"
VIEW = "Chadwick"

#: Frame pixels for each SVG unit.
SCALE = 0.4
#: The drawing is offset by the art script's ``DX``/``DY``.
DX, DY = art.DX, art.DY
#: The ground under his soles, and his centre line (the pelvis), in SVG units.
GROUND_Y = 456.0 + 18.0 + DY
CENTER_X = 250.0 + DX
FRAME = {"width": 224, "height": 224, "center_x": 112, "ground_y": 214, "ankle_h": 0, "supersample": 3, "render_scale": 1, "trim": False}

#: Each bone: (parent, the joint of the drawing it turns about).
BONES = {
    "body": ("", "pelvis"),
    "pelvis": ("body", "pelvis"),
    "torso": ("body", "pelvis"),
    "head": ("torso", "neck"),
    "near_arm_u": ("torso", "near_shoulder"),
    "near_arm_l": ("near_arm_u", "near_elbow"),
    "near_hand": ("near_arm_l", "near_wrist"),
    "far_arm_u": ("torso", "far_shoulder"),
    "far_arm_l": ("far_arm_u", "far_elbow"),
    "far_hand": ("far_arm_l", "far_wrist"),
    "near_leg_u": ("body", "near_hip"),
    "near_leg_l": ("near_leg_u", "near_knee"),
    "near_foot": ("near_leg_l", "near_ankle"),
    "far_leg_u": ("body", "far_hip"),
    "far_leg_l": ("far_leg_u", "far_knee"),
    "far_foot": ("far_leg_l", "far_ankle"),
}

JOLT = "(1-t)*(1-t)"
EASE = "(t*t*(3-2*t))"
BEAT = "(lambda u: u*u*(3-2*u))(max(0.0, min(1.0, t/0.25, (1-t)/0.25)))"


def expr(text: str) -> dict:
    return {"expr": text}


def legs(near_u: str, far_u: str, near_l: str, far_l: str) -> dict:
    """Thigh and shin turns; each boot kept level."""
    return {
        "near_leg_u": expr(near_u), "far_leg_u": expr(far_u),
        "near_leg_l": expr(near_l), "far_leg_l": expr(far_l),
        "near_foot": expr(f"-(({near_u}) + ({near_l}))"),
        "far_foot": expr(f"-(({far_u}) + ({far_l}))"),
    }


CLIPS = {
    # Eyes on his phone, weight on one hip.
    "idle": {
        "loop": True, "frames": 8, "duration_ms": 140,
        "channels": {
            "root_y": expr("0.6*sin(tau*t)"),
            "torso": expr("1.0*sin(tau*t)"),
            "head": expr("6 + 1.5*sin(tau*t+0.5)"),
            "near_arm_u": expr("1.5*sin(tau*t)"),
            "far_arm_u": expr("-1.5*sin(tau*t)"),
        },
    },
    # A relaxed stroll, still reading.
    "walk": {
        "loop": True, "frames": 8, "duration_ms": 95,
        "channels": {
            "root_y": expr("-2.2*(1-abs(sin(tau*t)))"),
            "torso": expr("1.5*sin(2*tau*t)"),
            "head": expr("6 - 1.0*sin(2*tau*t)"),
            **legs("-26*sin(tau*t)", "26*sin(tau*t)", "36*max(0.0, cos(tau*t))", "36*max(0.0, -cos(tau*t))"),
            "far_arm_u": expr("-18*sin(tau*t)"), "far_arm_l": expr("-10"),
            "near_arm_u": expr("4*sin(tau*t)"),
        },
    },
    # The pitch: the phone held out to you, jabbed on each point.
    "talk": {
        "loop": True, "frames": 8, "duration_ms": 110,
        "channels": {
            "root_y": expr("-1.0*abs(sin(tau*2*t))"),
            "torso": expr("-2 + 1.5*sin(tau*2*t)"),
            "head": expr("-4 + 3*sin(tau*2*t)"),
            "near_arm_u": expr("-24 + 8*sin(tau*2*t)"),
            "near_arm_l": expr("-6 + 10*sin(tau*2*t+0.6)"),
            "far_arm_u": expr("-30 + 6*sin(tau*2*t+1.2)"), "far_arm_l": expr("-50"),
        },
    },
    # Winding up a disruption: crouched, the phone pulled back, humming.
    "charge": {
        "loop": True, "frames": 6, "duration_ms": 90,
        "channels": {
            "root_y": expr("6 + 1.0*sin(2*tau*t)"),
            "torso": expr("10 + 1.5*sin(2*tau*t)"),
            "head": expr("-6"),
            **legs("-28", "22", "44", "30"),
            "near_arm_u": expr("40 + 3*sin(2*tau*t)"), "near_arm_l": expr("-70"),
            "far_arm_u": expr("-40"), "far_arm_l": expr("-30"),
        },
    },
    # He pushes the update at you: phone thrust out, the other hand flung back.
    "cast": {
        "loop": False, "frames": 7, "duration_ms": 80,
        "channels": {
            "root_x": expr(f"4*{EASE}"),
            "torso": expr(f"8 - 14*{EASE}"),
            "head": expr(f"-8*{EASE}"),
            **legs(f"-20*{EASE}", f"18*{EASE}", f"14*{EASE}", f"10*{EASE}"),
            "near_arm_u": expr(f"40 - 104*{EASE}"), "near_arm_l": expr(f"-70 + 74*{EASE}"),
            "far_arm_u": expr(f"30*{EASE}"), "far_arm_l": expr("-10"),
        },
    },
    # He posts the win: phone up, a fist pump.
    "celebrate": {
        "loop": True, "frames": 8, "duration_ms": 100,
        "channels": {
            "root_y": expr("-6*abs(sin(tau*t))"),
            "torso": expr("-3 + 2*sin(tau*t)"),
            "head": expr("-10 + 2*sin(tau*t)"),
            # A fist pump out in front of him, clear of his face; the phone
            # held high behind his head.
            "near_arm_u": expr("-70 + 6*sin(tau*2*t)"), "near_arm_l": expr("-80 - 10*abs(sin(tau*2*t))"),
            "far_arm_u": expr("-165 - 8*abs(sin(tau*2*t))"), "far_arm_l": expr("-10"),
            **legs("-6*abs(sin(tau*t))", "6*abs(sin(tau*t))", "12*abs(sin(tau*t))", "12*abs(sin(tau*t))"),
        },
    },
    # A blow: he rocks back, phone flung up.
    "hit": {
        "loop": False, "frames": 5, "duration_ms": 90,
        "channels": {
            "root_x": expr(f"-5*{JOLT}"),
            "torso": expr(f"-14*{JOLT}"),
            "head": expr(f"-16*{JOLT}"),
            "near_arm_u": expr(f"-40*{JOLT}"), "near_arm_l": expr(f"-20*{JOLT}"),
            "far_arm_u": expr(f"36*{JOLT}"),
            **legs(f"-10*{JOLT}", f"8*{JOLT}", "0", f"6*{JOLT}"),
        },
    },
    # He goes down flat on his back, the phone still in his hand.
    "death": {
        "loop": False, "frames": 8, "duration_ms": 110,
        "channels": {
            # The whole of him tips back about the pelvis and lies along the deck.
            "body": expr(f"-88*{EASE}"),
            "root_x": expr(f"4*{EASE}"),
            # less the lift that keeps his back on the ground line as he tips
            "root_y": expr(f"58*{EASE} - 8*sin(3.14159*t) - 15*(lambda u: u*u*(3-2*u))(max(0.0, min(1.0, (t-0.15)/0.3)))"),
            "head": expr(f"10*{EASE}"),
            "near_arm_u": expr(f"-30*{EASE}"), "near_arm_l": expr(f"-30*{EASE}"),
            "far_arm_u": expr(f"20*{EASE}"),
            **legs(f"-6*{EASE}", f"4*{EASE}", f"10*{EASE}", f"6*{EASE}"),
        },
    },
}


def redraw() -> None:
    SVG.parent.mkdir(parents=True, exist_ok=True)
    text = art.draw(LOOK).replace(
        "<!-- CHADWICK's design (Jon chose look A, 2026-10-18); his rig is not built yet.",
        "<!-- CHADWICK's design (Jon chose look A, 2026-10-18); the rig is scripts/build_tech_bro_disruptor_rig.py.")
    tmp = SVG.with_suffix(".svg.tmp")
    tmp.write_text(text, encoding="utf8")
    tmp.replace(SVG)
    print(f"wrote {SVG.relative_to(ROOT)}")


def build() -> dict:
    art.draw(LOOK)  # to read the parts it declares
    joints = {name: (x + DX, y + DY) for name, (x, y) in art.J.items()}
    bones = []
    for name, (parent, at) in BONES.items():
        x, y = joints[at]
        if parent:
            px, py = joints[BONES[parent][1]]
            offset = [round((x - px) * SCALE, 4), round((y - py) * SCALE, 4)]
        else:
            offset = [round((x - CENTER_X) * SCALE, 4), round((y - GROUND_Y) * SCALE, 4)]
        bones.append({"name": name, "parent": parent or None, "offset": offset, "length": 0, "rest_angle": 0})
    parts = []
    for pid, _label, part, bone, z, _extra, _body in sorted(svgkit.PARTS, key=lambda p: p[4]):
        x, y = joints[BONES[bone][1]]
        parts.append({"name": part, "bone": bone, "z": z, "kind": "sprite", "include": [pid], "pivot": [x, y], "rest_angle": 0})
    return {
        "name": "tech_bro_disruptor",
        "frame": FRAME,
        "svg_source": {"path": "../../../../data/characters/tech_bro_disruptor/tech_bro_disruptor.svg", "view": VIEW,
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
    if "--redraw" in sys.argv or not SVG.exists():
        redraw()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf8")
    tmp.replace(OUT)
    print(f"wrote {OUT.relative_to(ROOT)}")
    for changed in install_repo_metadata(ROOT):
        print(f"catalog {Path(changed).relative_to(ROOT)}")


if __name__ == "__main__":
    main()
