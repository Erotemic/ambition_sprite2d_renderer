#!/usr/bin/env python3
"""Build the bossofthegame's rig document (``bossofthegame_boss``).

    uv run python scripts/svg_art/bossofthegame_art.py   # the drawing, once
    uv run python scripts/build_bossofthegame_rig.py
    ./scripts/regen/sprites.sh --target bossofthegame_boss

The drawing says where each part turns (``joints`` and ``BONES`` of the art
script, the Creator's skeleton). This script makes the skeleton from those
joints, binds each part layer to its bone, and authors the rows. A channel is
the turn of a bone from the drawing, in degrees (positive clockwise on the
screen: a hanging limb swings back, the torso leans forward).

A boss sheet's first six rows are fixed slots (the game's
``boss_sheets.ron``): ``rest`` (he types), ``floor_slam`` (both hands down on
the keys), ``side_sweep`` (a swing of the keyboard), ``spike_halo`` (arms up:
he conducts his agent), ``hit`` and ``death``. He does not die: ``death`` is
him sitting down on the stage, the crown in his hand. ``talk`` follows them.
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

_spec = importlib.util.spec_from_file_location("bossofthegame_art", ROOT / "scripts" / "svg_art" / "bossofthegame_art.py")
art = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(art)

PKG = ROOT / "ambition_sprite2d_renderer"
OUT = PKG / "targets" / "characters" / "rigged" / "bossofthegame" / "bossofthegame.rig.json"

#: Frame pixels for each SVG unit.
SCALE = 0.4
FRAME = {"width": 200, "height": 224, "center_x": 90, "ground_y": 214, "ankle_h": 0, "supersample": 3, "render_scale": 1, "trim": False}


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


def board_arm(upper: str, lower: str) -> dict:
    """The near arm, the keyboard kept level in its hand."""
    return {"near_arm_u": expr(upper), "near_arm_l": expr(lower), "near_hand": expr(f"-(({upper}) + ({lower}))")}


def face(shut: str = "False", talk: str = "False") -> dict:
    return {"eye_open": expr(f"0 if ({shut}) else 1"), "eye_shut": expr(f"1 if ({shut}) else 0"),
            "mouth_open": expr(f"1 if ({talk}) else 0")}


#: The far hand typing: a quick tap on the keys.
TYPE = "3*sin(4*tau*t)"

CLIPS = {
    # He types, head down over the keys; the far hand taps fast, the near
    # hand slower; a blink.
    "rest": {
        "loop": True, "frames": 8, "duration_ms": 110,
        "channels": {
            "root_y": expr("0.5*sin(tau*t)"),
            "torso": expr("3"),
            "head": expr("10 + 1.5*sin(2*tau*t)"),
            **board_arm("2*sin(2*tau*t+1)", "-2*sin(2*tau*t+1)"),
            "far_arm_u": expr(f"{TYPE}"),
            "far_arm_l": expr(f"-{TYPE}"),
            **face(shut="0.8 < t < 0.95"),
        },
    },
    # Both hands up, then down hard on the keys.
    "floor_slam": {
        "loop": False, "frames": 8, "duration_ms": 70,
        "channels": {
            "root_y": expr(f"-3*{ramp(0.0, 0.4)} + 7*{ramp(0.4, 0.55)} - 4*{ramp(0.7, 1.0)}"),
            "torso": expr(f"-6*{ramp(0.0, 0.4)} + 16*{ramp(0.4, 0.55)} - 10*{ramp(0.7, 1.0)}"),
            "head": expr(f"-10*{ramp(0.0, 0.4)} + 22*{ramp(0.4, 0.55)} - 12*{ramp(0.7, 1.0)}"),
            **board_arm(f"-30*{ramp(0.0, 0.4)} + 30*{ramp(0.4, 0.55)}", "0"),
            "far_arm_u": expr(f"-80*{ramp(0.0, 0.4)} + 80*{ramp(0.4, 0.55)}"),
            "far_arm_l": expr(f"-30*{ramp(0.0, 0.4)} + 30*{ramp(0.4, 0.55)}"),
            **face(talk=f"0.4 < t < 0.8"),
        },
    },
    # He swings the keyboard by its strap: back, then round in front of him.
    "side_sweep": {
        "loop": False, "frames": 8, "duration_ms": 80,
        "channels": {
            "root_x": expr(f"-3*{ramp(0.0, 0.35)} + 6*{ramp(0.35, 0.6)} - 3*{ramp(0.7, 1.0)}"),
            "torso": expr(f"-10*{ramp(0.0, 0.35)} + 22*{ramp(0.35, 0.6)} - 12*{ramp(0.7, 1.0)}"),
            "head": expr(f"-4*{ramp(0.0, 0.35)} + 6*{ramp(0.35, 0.6)} - 2*{ramp(0.7, 1.0)}"),
            "near_arm_u": expr(f"60*{ramp(0.0, 0.35)} - 150*{ramp(0.35, 0.6)} + 90*{ramp(0.7, 1.0)}"),
            "near_arm_l": expr(f"-20*{ramp(0.0, 0.35)} + 20*{ramp(0.7, 1.0)}"),
            "near_hand": expr(f"-40*{ramp(0.0, 0.35)} + 100*{ramp(0.35, 0.6)} - 60*{ramp(0.7, 1.0)}"),
            "far_arm_u": expr(f"20*{ramp(0.0, 0.35)} - 50*{ramp(0.35, 0.6)} + 30*{ramp(0.7, 1.0)}"),
            **face(talk="0.35 < t < 0.7"),
        },
    },
    # Arms up: he conducts his agent, the keyboard held high in one hand.
    "spike_halo": {
        "loop": True, "frames": 8, "duration_ms": 80,
        "channels": {
            "root_y": expr("-1.5*abs(sin(tau*t))"),
            "torso": expr("-6"),
            "head": expr("-14 + 3*sin(tau*t)"),
            **board_arm("-130 + 12*sin(tau*t)", "-20 + 10*sin(tau*t+0.6)"),
            "far_arm_u": expr("-150 - 14*sin(tau*t)"),
            "far_arm_l": expr("-20 - 12*sin(tau*t+0.6)"),
            **face(talk="floor(t*8 + 0.01) % 2 == 0"),
        },
    },
    # Struck: he rocks back, eyes shut.
    "hit": {
        "loop": False, "frames": 5, "duration_ms": 80,
        "channels": {
            "root_x": expr(f"-5*{ramp(0.0, 0.3)} + 5*{ramp(0.5, 1.0)}"),
            "torso": expr(f"-14*{ramp(0.0, 0.3)} + 14*{ramp(0.5, 1.0)}"),
            "head": expr(f"-16*{ramp(0.0, 0.3)} + 16*{ramp(0.5, 1.0)}"),
            **board_arm(f"20*{ramp(0.0, 0.3)} - 20*{ramp(0.5, 1.0)}", "0"),
            "far_arm_u": expr(f"-30*{ramp(0.0, 0.3)} + 30*{ramp(0.5, 1.0)}"),
            **face(shut="t < 0.7", talk="t < 0.5"),
        },
    },
    # He does not die. He sits down on the stage, legs out in front, the
    # keyboard down beside him, and holds his crown in his lap.
    "death": {
        "loop": False, "frames": 10, "duration_ms": 105,
        "channels": {
            "root_y": expr(f"58*{ramp(0.1, 0.6)}"),
            "root_x": expr(f"-14*{ramp(0.1, 0.6)}"),
            "torso": expr(f"-8*{ramp(0.1, 0.6)} + 14*{ramp(0.6, 0.9)}"),
            "head": expr(f"6*{ramp(0.1, 0.6)} + 14*{ramp(0.6, 0.9)}"),
            **legs(f"-88*{ramp(0.1, 0.6)}", f"-84*{ramp(0.1, 0.6)}", "0", f"6*{ramp(0.1, 0.6)}"),
            **board_arm(f"-30*{ramp(0.1, 0.6)}", f"-20*{ramp(0.1, 0.6)}"),
            "far_arm_u": expr(f"-40*{ramp(0.1, 0.6)}"),
            "far_arm_l": expr(f"-30*{ramp(0.1, 0.6)}"),
            **face(shut="0.6 < t < 0.8"),
        },
    },
    # He speaks: a nod on the words, the near hand marks them.
    "talk": {
        "loop": True, "frames": 6, "duration_ms": 110,
        "channels": {
            "root_y": expr("-0.6*abs(sin(tau*t))"),
            "torso": expr("-1 + 1.0*sin(tau*t)"),
            "head": expr("-2 + 3*sin(tau*t)"),
            **board_arm("-6 + 4*sin(tau*t)", "-8 + 8*sin(tau*t+0.8)"),
            **face(talk="floor(t*6 + 0.01) % 2 == 0"),
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
        "name": "bossofthegame",
        "frame": FRAME,
        "svg_source": {"path": "../../../../data/characters/bossofthegame/bossofthegame.svg", "view": art.VIEW, "ref_dpi": 25.4,
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
