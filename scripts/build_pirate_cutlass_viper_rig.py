#!/usr/bin/env python3
"""Build the Pirate Cutlass Viper's rig document (``pirate_cutlass_viper``).

    uv run python scripts/svg_art/pirate_cutlass_viper_art.py   # the drawing, once
    uv run python scripts/build_pirate_cutlass_viper_rig.py

The drawing says where each part turns (``JOINTS`` in the art script). This
script makes the skeleton from those joints, binds each part layer to its
bone, and authors the rows. It never draws. A channel is the turn of a bone
from the drawing, in degrees (positive clockwise on the screen: a hanging
limb swings back, the torso leans forward).

The rows are the ten she has always had: ``idle``, ``walk``, ``turn_right``,
``profile_right``, ``turn_left``, ``profile_left``, ``slash``, ``taunt``,
``hurt``, ``death``; and the two the game pins before a fight, ``notice``
and ``windup`` (both loop on its clock, so every frame is the whole pose with
a shiver). She is drawn from the side only: ``turn_right`` lowers
her guard into ``profile_right``, her stance at ease, and the target draws
``turn_left`` and ``profile_left`` as their mirror images (the rows here are
the same motion, facing right). The frame's centre is her pelvis, so a
mirrored frame keeps her in place.
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

_spec = importlib.util.spec_from_file_location("pirate_cutlass_viper_art", ROOT / "scripts" / "svg_art" / "pirate_cutlass_viper_art.py")
art = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(art)

PKG = ROOT / "ambition_sprite2d_renderer"
OUT = PKG / "targets" / "characters" / "rigged" / "pirate_cutlass_viper" / "pirate_cutlass_viper.rig.json"

#: Frame pixels for each SVG unit.
SCALE = 0.4
#: Her centre line (the pelvis), in SVG units: the frame's centre.
CENTER_X = 268.0
FRAME = {"width": 256, "height": 240, "center_x": 128, "ground_y": 230, "ankle_h": 0, "supersample": 3, "render_scale": 1, "trim": False}

JOLT = "(1-t)*(1-t)"
EASE = "(t*t*(3-2*t))"


def expr(text: str) -> dict:
    return {"expr": text}


#: A key: 0 to 1 between ``a`` and ``b`` of the row, eased, held after.
def ramp(a: float, b: float) -> str:
    return f"(lambda u: u*u*(3-2*u))(max(0.0, min(1.0, (t-{a})/{b - a})))"


def legs(near_u: str, far_u: str, near_l: str, far_l: str) -> dict:
    """Thigh and shin turns; each boot kept flat."""
    return {
        "near_leg_u": expr(near_u), "far_leg_u": expr(far_u),
        "near_leg_l": expr(near_l), "far_leg_l": expr(far_l),
        "near_foot": expr(f"-(({near_u}) + ({near_l}))"),
        "far_foot": expr(f"-(({far_u}) + ({far_l}))"),
    }


def eyes(shut: str = "False") -> dict:
    return {"eye_shut": expr(f"1 if ({shut}) else 0"), "eye_open": expr(f"0 if ({shut}) else 1")}


#: Her stance at ease: the cutlass lowered, its point down and forward.
EASE_POSE = {"near_arm_u": 14.0, "near_arm_l": 36.0, "near_hand": 70.0, "torso": -2.0, "head": -2.0}


def at_ease(weight: str, breathe: str = "0") -> dict:
    """The stance at ease, ``weight`` of the way there (an expression)."""
    out = {}
    for bone, deg in EASE_POSE.items():
        extra = f" + {breathe}" if bone in ("torso",) else ""
        out[bone] = expr(f"{deg}*({weight}){extra}")
    return out


CLIPS = {
    # Her ready stance: the cutlass forward, the other hand on her hip, breathing.
    "idle": {
        "loop": True, "frames": 6, "duration_ms": 130,
        "channels": {
            "root_y": expr("0.6*sin(tau*t)"),
            "torso": expr("1.0*sin(tau*t)"),
            "head": expr("-1.5*sin(tau*t+0.5)"),
            "near_arm_u": expr("2*sin(tau*t)"), "near_hand": expr("4*sin(tau*t+0.8)"),
            "coat": expr("2*sin(tau*t+1)"),
            **eyes("0.8 < t < 0.95"),
        },
    },
    # A duelist's stride, the guard kept up.
    "walk": {
        "loop": True, "frames": 8, "duration_ms": 95,
        "channels": {
            "root_y": expr("-2.4*(1-abs(sin(tau*t)))"),
            "torso": expr("1.5*sin(2*tau*t)"),
            "head": expr("-1.0*sin(2*tau*t)"),
            **legs("-24*sin(tau*t)", "24*sin(tau*t)", "32*max(0.0, cos(tau*t))", "32*max(0.0, -cos(tau*t))"),
            "near_arm_u": expr("4*sin(tau*t)"), "near_hand": expr("-4*sin(tau*t)"),
            "far_arm_u": expr("-4*sin(tau*t)"),
            "coat": expr("-6*sin(2*tau*t)"),
            **eyes(),
        },
    },
    # From her guard to her stance at ease.
    "turn_right": {
        "loop": False, "frames": 5, "duration_ms": 90,
        "channels": {**at_ease(EASE), "coat": expr(f"-6*sin(3.14159*t)"), **eyes()},
    },
    # At ease, facing right: the cutlass lowered, a slow breath.
    "profile_right": {
        "loop": True, "frames": 4, "duration_ms": 120,
        "channels": {**at_ease("1", "1.0*sin(tau*t)"), "root_y": expr("0.5*sin(tau*t)"), "coat": expr("2*sin(tau*t+1)"), **eyes()},
    },
    # The mirrors of the two rows above (the target flips them).
    "turn_left": {
        "loop": False, "frames": 5, "duration_ms": 90,
        "channels": {**at_ease(EASE), "coat": expr(f"-6*sin(3.14159*t)"), **eyes()},
    },
    "profile_left": {
        "loop": True, "frames": 4, "duration_ms": 120,
        "channels": {**at_ease("1", "1.0*sin(tau*t)"), "root_y": expr("0.5*sin(tau*t)"), "coat": expr("2*sin(tau*t+1)"), **eyes()},
    },
    # A rising cut: the cutlass drawn back low behind her hip, then swept
    # forward and up through the target on a lunge, the point finishing high.
    "slash": {
        "loop": False, "frames": 7, "duration_ms": 78,
        "channels": {
            "root_x": expr(f"-3*{ramp(0.0, 0.3)} + 13*{ramp(0.3, 0.55)} - 10*{ramp(0.75, 1.0)}"),
            "root_y": expr(f"3*{ramp(0.0, 0.3)} + 2*{ramp(0.3, 0.55)} - 5*{ramp(0.75, 1.0)}"),
            "torso": expr(f"-4*{ramp(0.0, 0.3)} + 14*{ramp(0.3, 0.55)} - 10*{ramp(0.75, 1.0)}"),
            "head": expr(f"4*{ramp(0.0, 0.3)} - 10*{ramp(0.3, 0.55)} + 6*{ramp(0.75, 1.0)}"),
            "near_arm_u": expr(f"50*{ramp(0.0, 0.3)} - 110*{ramp(0.3, 0.55)} + 60*{ramp(0.75, 1.0)}"),
            "near_arm_l": expr(f"10*{ramp(0.0, 0.3)} - 20*{ramp(0.3, 0.55)} + 10*{ramp(0.75, 1.0)}"),
            "near_hand": expr(f"100*{ramp(0.0, 0.3)} - 67*{ramp(0.3, 0.55)} - 33*{ramp(0.75, 1.0)}"),
            "far_arm_u": expr(f"10*{ramp(0.3, 0.55)} - 10*{ramp(0.75, 1.0)}"),
            "coat": expr(f"6*{ramp(0.0, 0.3)} - 18*{ramp(0.3, 0.55)} + 12*{ramp(0.75, 1.0)}"),
            **legs(f"-6*{ramp(0.0, 0.3)} - 18*{ramp(0.3, 0.55)} + 24*{ramp(0.75, 1.0)}", f"18*{ramp(0.3, 0.55)} - 18*{ramp(0.75, 1.0)}",
                   f"14*{ramp(0.3, 0.55)} - 14*{ramp(0.75, 1.0)}", f"6*{ramp(0.3, 0.55)} - 6*{ramp(0.75, 1.0)}"),
            "fx_slash": expr("1 if 0.4 < t < 0.7 else 0"),
            **eyes(),
        },
    },
    # The cutlass lowered, the other hand held out in front and beckoning:
    # "come on, then."
    "taunt": {
        "loop": True, "frames": 6, "duration_ms": 110,
        "channels": {
            **at_ease("1"),
            "head": expr("-6 + 2*sin(tau*t)"),
            "far_arm_u": expr("-90"), "far_arm_l": expr("34 + 6*sin(tau*t)"), "far_hand": expr("-25 + 35*sin(tau*t)"),
            "coat": expr("2*sin(tau*t)"),
            **eyes(),
        },
    },
    # A blow: she rocks back, eyes screwed shut.
    "hurt": {
        "loop": False, "frames": 4, "duration_ms": 90,
        "channels": {
            "root_x": expr(f"-5*{JOLT}"),
            "torso": expr(f"-14*{JOLT}"),
            "head": expr(f"-14*{JOLT}"),
            "near_arm_u": expr(f"-24*{JOLT}"), "near_hand": expr(f"20*{JOLT}"),
            "far_arm_u": expr(f"30*{JOLT}"),
            "coat": expr(f"10*{JOLT}"),
            **legs(f"-10*{JOLT}", f"8*{JOLT}", "0", f"6*{JOLT}"),
            **eyes("True"),
        },
    },
    # Her knees give and she falls back flat, one knee up, the cutlass
    # dropped along her side.
    "death": {
        "loop": False, "frames": 8, "duration_ms": 110,
        "channels": {
            "body": expr(f"-86*{ramp(0.15, 0.85)}"),
            "root_x": expr(f"-6*{ramp(0.15, 0.85)}"),
            # less a lift while she tips, so her swinging boots stay on the ground line
            "root_y": expr(f"3*{ramp(0.0, 0.2)} + 53*{ramp(0.2, 0.85)} - 20*sin(3.14159*max(0.0, min(1.0, (t-0.15)/0.75)))"),
            "torso": expr(f"4*{ramp(0.0, 0.2)} - 4*{ramp(0.2, 0.85)}"),
            "head": expr(f"10*{ramp(0.4, 0.9)}"),
            # the near knee up, its boot flat; the far leg along the ground
            **legs(f"-10*{ramp(0.0, 0.2)} - 13*{ramp(0.2, 0.85)}", f"-8*{ramp(0.0, 0.2)} + 8*{ramp(0.2, 0.85)}",
                   f"16*{ramp(0.0, 0.2)} + 48*{ramp(0.2, 0.85)}", f"14*{ramp(0.0, 0.2)} - 34*{ramp(0.2, 0.85)}"),
            "near_foot": expr(f"86*{ramp(0.15, 0.85)} - (-10*{ramp(0.0, 0.2)} - 13*{ramp(0.2, 0.85)} + 16*{ramp(0.0, 0.2)} + 48*{ramp(0.2, 0.85)})"),
            # the sword arm along her side, the blade on the ground toward her feet
            "near_arm_u": expr(f"18*{ramp(0.3, 0.9)}"), "near_arm_l": expr(f"34*{ramp(0.3, 0.9)}"),
            "near_hand": expr(f"72*{ramp(0.3, 0.9)}"),
            "far_arm_u": expr(f"-40*{ramp(0.3, 0.9)}"), "far_arm_l": expr(f"40*{ramp(0.3, 0.9)}"),
            "coat": expr(f"-12*{ramp(0.3, 0.9)}"),
            **eyes("t > 0.3"),
        },
    },
}


def held(*values: float) -> dict:
    """One value per frame of a held three-frame row (the game loops it)."""
    return {"keys": [[i / (len(values) - 1), v, "linear"] for i, v in enumerate(values)]}


def held_legs(near_u: float, far_u: float, near_l: float, far_l: float) -> dict:
    """``legs`` for a held pose: constant turns, each boot kept flat."""
    return legs(str(near_u), str(far_u), str(near_l), str(far_l))


# She has seen you: drawn up tall, her head snapped up and round to you, the
# cutlass brought up into a high guard, the free arm flung out at you.
CLIPS["notice"] = {
    "loop": False, "frames": 3, "duration_ms": 110,
    "channels": {
        "root_y": expr("3"),
        "torso": expr("-6"),
        "head": held(-12.0, -13.5, -11.0),
        "near_arm_u": held(-34.0, -35.0, -33.0), "near_arm_l": expr("-20"), "near_hand": held(-6.0, -9.0, -4.0),
        "far_arm_u": held(-78.0, -80.0, -77.0), "far_arm_l": expr("-14"), "far_hand": expr("-10"),
        "coat": expr("4"),
        **held_legs(-8.0, 6.0, 4.0, 2.0),
        **eyes(),
    },
}

# The rising cut held back: down in a deep lunge, her weight on the back foot,
# the cutlass drawn far back low behind her hip, the free arm out in front of
# her at you, her head up and on you.
CLIPS["windup"] = {
    "loop": False, "frames": 3, "duration_ms": 90,
    "channels": {
        "root_x": held(-5.0, -4.6, -5.4),
        "root_y": expr("8"),
        "torso": held(8.0, 8.6, 7.6),
        "head": held(-14.0, -13.0, -14.6),
        "near_arm_u": held(64.0, 66.0, 63.0), "near_arm_l": expr("14"), "near_hand": held(112.0, 114.0, 110.0),
        "far_arm_u": held(-62.0, -60.0, -63.0), "far_arm_l": expr("-18"), "far_hand": expr("-16"),
        "coat": expr("10"),
        **held_legs(-26.0, 22.0, 30.0, 12.0),
        **eyes(),
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
        "name": "pirate_cutlass_viper",
        "frame": FRAME,
        "svg_source": {"path": "../../../../data/characters/pirate_cutlass_viper/pirate_cutlass_viper.svg", "view": art.VIEW,
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
