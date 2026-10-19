#!/usr/bin/env python3
"""Build the Dark Lord's rig document (``dark_lord``).

    uv run python scripts/svg_art/dark_lord_art.py   # the drawing, once
    uv run python scripts/build_dark_lord_rig.py

The drawing says where each part turns (``joints`` and ``BONES`` in the art
script). This script makes the skeleton from those joints, binds each part
layer to its bone, and authors the rows. It never draws. A channel is the turn
of a bone from the drawing, in degrees (positive clockwise on the screen: a
hanging limb swings back, the torso leans forward, a held weapon's head comes
over the front and down).

The rows are the eight he has always had: ``idle``, ``walk``, ``slash``,
``cast``, ``summon``, ``guard``, ``hurt``, ``death``. He holds the halberd in
both fists; a row that keeps both on the shaft turns only what carries both
arms (the torso, the body), and a row that swings it lets the far hand go and
drops that arm behind his chest (``bone.<far arm>.z``).
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

_spec = importlib.util.spec_from_file_location("dark_lord_art", ROOT / "scripts" / "svg_art" / "dark_lord_art.py")
art = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(art)

PKG = ROOT / "ambition_sprite2d_renderer"
OUT = PKG / "targets" / "characters" / "rigged" / "dark_lord" / "dark_lord.rig.json"

#: Frame pixels for each SVG unit.
SCALE = 0.4
#: His centre line (the pelvis), in SVG units: the frame's ``center_x``.
CENTER_X = 276.0
FRAME = {"width": 360, "height": 320, "center_x": 150, "ground_y": 300, "ankle_h": 0, "supersample": 3, "render_scale": 1, "trim": False}

JOLT = "(1-t)*(1-t)"
EASE = "(t*t*(3-2*t))"


def expr(text: str) -> dict:
    return {"expr": text}


def ramp(a: float, b: float) -> str:
    """0 to 1 between ``a`` and ``b`` of the row, eased, held after."""
    return f"(lambda u: u*u*(3-2*u))(max(0.0, min(1.0, (t-{a})/{b - a})))"


def legs(near_u: str, far_u: str, near_l: str, far_l: str) -> dict:
    """Thigh and shin turns; each sabaton kept flat."""
    return {
        "near_leg_u": expr(near_u), "far_leg_u": expr(far_u),
        "near_leg_l": expr(near_l), "far_leg_l": expr(far_l),
        "near_foot": expr(f"-(({near_u}) + ({near_l}))"),
        "far_foot": expr(f"-(({far_u}) + ({far_l}))"),
    }


def far_arm_behind(on: str) -> dict:
    """The far arm let go of the shaft: drawn behind his chest while ``on``."""
    z = f"(-50 if ({on}) else 0)"
    return {"bone.far_arm_u.z": expr(z), "bone.far_arm_l.z": expr(z), "bone.far_hand.z": expr(z)}


def lowered(root_y: str) -> dict:
    """While he is lower than he stands (``root_y`` > 0), the haft slides up
    through his fists so its butt stays on the ground, and the cape gathers
    on the ground instead of sinking into it (its hem is 126 px below its
    pivot)."""
    down = f"max(0.0, {root_y})"
    return {"root_y": expr(root_y), "bone.weapon.y": expr(f"-{down}"), "bone.cape.scale_y": expr(f"1 - {down}/126")}


def visor(dark: str = "False") -> dict:
    return {"eye_open": expr(f"0 if ({dark}) else 1"), "eye_dead": expr(f"1 if ({dark}) else 0")}


# The slash: wound up overhead (the blade hanging down his back), then over
# the front and down, the far hand let go and flung back.
UP = ramp(0.0, 0.32)
DOWN = ramp(0.32, 0.5)
BACK = ramp(0.72, 1.0)

CLIPS = {
    # Looming: a slow breath, the cape stirring.
    "idle": {
        "loop": True, "frames": 6, "duration_ms": 130,
        "channels": {
            "root_y": expr("0.8*sin(tau*t)"),
            "torso": expr("-1.0*sin(tau*t)"),
            "head": expr("1.5*sin(tau*t+0.6)"),
            "cape": expr("2.0*sin(tau*t+0.8)"),
            "near_pauldron": expr("0.8*sin(tau*t)"), "far_pauldron": expr("0.8*sin(tau*t)"),
            **visor(),
        },
    },
    # A heavy armoured advance, the halberd carried upright in both fists.
    "walk": {
        "loop": True, "frames": 8, "duration_ms": 100,
        "channels": {
            "root_y": expr("-3.0*(1-abs(sin(tau*t)))"),
            "torso": expr("3 + 1.5*sin(2*tau*t)"),
            "head": expr("-3 - 1.0*sin(2*tau*t)"),
            "cape": expr("6 + 4*sin(2*tau*t+0.7)"),
            **legs("-24*sin(tau*t)", "24*sin(tau*t)", "30*max(0.0, cos(tau*t))", "30*max(0.0, -cos(tau*t))"),
            **visor(),
        },
    },
    # The halberd over his head and down in front.
    "slash": {
        "loop": False, "frames": 8, "duration_ms": 78,
        "channels": {
            "root_x": expr(f"-4*{UP} + 14*{DOWN} - 10*{BACK}"),
            "root_y": expr(f"-2*{UP} + 8*{DOWN} - 6*{BACK}"),
            "torso": expr(f"-8*{UP} + 22*{DOWN} - 14*{BACK}"),
            "head": expr(f"4*{UP} - 12*{DOWN} + 8*{BACK}"),
            "cape": expr(f"-4*{UP} + 18*{DOWN} - 14*{BACK}"),
            "near_arm_u": expr(f"-160*{UP} + 100*{DOWN} + 60*{BACK}"),
            "near_arm_l": expr(f"40*{UP} + 50*{DOWN} - 90*{BACK}"),
            "near_hand": expr(f"-7*{UP} + 97*{DOWN} - 90*{BACK}"),
            "near_pauldron": expr(f"-24*{UP} + 18*{DOWN} + 6*{BACK}"),
            "far_arm_u": expr(f"30*{UP} + 20*{DOWN} - 50*{BACK}"),
            "far_arm_l": expr(f"-30*{UP} + 10*{DOWN} + 20*{BACK}"),
            **far_arm_behind("0.04 < t < 0.9"),
            **legs(f"-26*{DOWN} + 26*{BACK}", f"22*{DOWN} - 22*{BACK}", f"24*{DOWN} - 24*{BACK}", f"8*{DOWN} - 8*{BACK}"),
            "fx_slash": expr("1 if 0.36 < t < 0.62 else 0"),
            **visor(),
        },
    },
    # The free hand thrust out, a rune bolt kindled in it.
    "cast": {
        "loop": False, "frames": 7, "duration_ms": 90,
        "channels": {
            "root_x": expr(f"-3*{ramp(0.0, 0.35)} + 7*{ramp(0.35, 0.55)} - 4*{ramp(0.8, 1.0)}"),
            "torso": expr(f"-6*{ramp(0.0, 0.35)} + 12*{ramp(0.35, 0.55)} - 6*{ramp(0.8, 1.0)}"),
            "head": expr(f"4*{ramp(0.0, 0.35)} - 8*{ramp(0.35, 0.55)} + 4*{ramp(0.8, 1.0)}"),
            "cape": expr(f"-3*{ramp(0.0, 0.35)} + 10*{ramp(0.35, 0.55)} - 7*{ramp(0.8, 1.0)}"),
            "far_arm_u": expr(f"20*{ramp(0.0, 0.3)} - 86*{ramp(0.3, 0.55)} + 66*{ramp(0.8, 1.0)}"),
            "far_arm_l": expr(f"-40*{ramp(0.0, 0.3)} + 50*{ramp(0.3, 0.55)} - 10*{ramp(0.8, 1.0)}"),
            "far_hand": expr(f"-20*{ramp(0.3, 0.55)} + 20*{ramp(0.8, 1.0)}"),
            **legs(f"-14*{ramp(0.35, 0.55)} + 14*{ramp(0.8, 1.0)}", f"12*{ramp(0.35, 0.55)} - 12*{ramp(0.8, 1.0)}",
                   f"10*{ramp(0.35, 0.55)} - 10*{ramp(0.8, 1.0)}", "0"),
            "fx_cast": expr(f"{ramp(0.25, 0.5)} * (1 - {ramp(0.85, 1.0)})"),
            **visor(),
        },
    },
    # The halberd lifted and its butt slammed down; the free hand bids the
    # iron rise out of the ground ahead.
    "summon": {
        "loop": False, "frames": 7, "duration_ms": 95,
        "channels": {
            **lowered(f"-4*{ramp(0.0, 0.35)} + 14*{ramp(0.35, 0.5)} - 10*{ramp(0.75, 1.0)}"),
            "torso": expr(f"-6*{ramp(0.0, 0.35)} + 16*{ramp(0.35, 0.5)} - 10*{ramp(0.75, 1.0)}"),
            "head": expr(f"-4*{ramp(0.0, 0.35)} + 2*{ramp(0.35, 0.5)} + 2*{ramp(0.75, 1.0)}"),
            "cape": expr(f"-6*{ramp(0.0, 0.35)} + 14*{ramp(0.35, 0.5)} - 8*{ramp(0.75, 1.0)}"),
            "near_arm_u": expr(f"-34*{ramp(0.0, 0.35)} + 34*{ramp(0.35, 0.5)}"),
            "near_hand": expr(f"34*{ramp(0.0, 0.35)} - 34*{ramp(0.35, 0.5)}"),
            "near_pauldron": expr(f"-8*{ramp(0.0, 0.35)} + 8*{ramp(0.35, 0.5)}"),
            "far_arm_u": expr(f"-70*{ramp(0.1, 0.4)} + 20*{ramp(0.4, 0.55)} + 50*{ramp(0.8, 1.0)}"),
            "far_arm_l": expr(f"-30*{ramp(0.1, 0.4)} + 50*{ramp(0.4, 0.55)} - 20*{ramp(0.8, 1.0)}"),
            "far_hand": expr(f"30*{ramp(0.4, 0.55)} - 30*{ramp(0.8, 1.0)}"),
            **legs(f"-18*{ramp(0.35, 0.5)} + 18*{ramp(0.75, 1.0)}", f"14*{ramp(0.35, 0.5)} - 14*{ramp(0.75, 1.0)}",
                   f"30*{ramp(0.35, 0.5)} - 30*{ramp(0.75, 1.0)}", f"20*{ramp(0.35, 0.5)} - 20*{ramp(0.75, 1.0)}"),
            "fx_summon": expr(f"{ramp(0.45, 0.6)} * (1 - {ramp(0.9, 1.0)})"),
            **visor(),
        },
    },
    # Braced behind the upright halberd: crouched, leaning into it.
    "guard": {
        "loop": False, "frames": 5, "duration_ms": 105,
        "channels": {
            **lowered(f"10*{ramp(0.0, 0.5)}"),
            "root_x": expr(f"-3*{ramp(0.0, 0.5)}"),
            "torso": expr(f"12*{ramp(0.0, 0.5)}"),
            "head": expr(f"-10*{ramp(0.0, 0.5)}"),
            "cape": expr(f"-6*{ramp(0.0, 0.5)}"),
            **legs(f"-28*{ramp(0.0, 0.5)}", f"22*{ramp(0.0, 0.5)}", f"40*{ramp(0.0, 0.5)}", f"30*{ramp(0.0, 0.5)}"),
            **visor(),
        },
    },
    # A blow rocks him back.
    "hurt": {
        "loop": False, "frames": 4, "duration_ms": 90,
        "channels": {
            "root_x": expr(f"-6*{JOLT}"),
            "torso": expr(f"-14*{JOLT}"),
            "head": expr(f"-12*{JOLT}"),
            "cape": expr(f"16*{JOLT}"),
            **legs(f"-10*{JOLT}", f"8*{JOLT}", "0", f"6*{JOLT}"),
            **visor("t > 0.2 and t < 0.45"),
        },
    },
    # He sinks to his knees, then pitches forward on his face; the visor goes out.
    "death": {
        "loop": False, "frames": 8, "duration_ms": 115,
        "channels": {
            "root_y": expr(f"24*{ramp(0.0, 0.4)} + 10*{ramp(0.45, 0.85)}"),
            "root_x": expr(f"6*{ramp(0.45, 0.85)}"),
            "body": expr(f"84*{ramp(0.45, 0.85)}"),
            "torso": expr(f"10*{ramp(0.0, 0.4)} + 6*{ramp(0.45, 0.85)}"),
            "head": expr(f"10*{ramp(0.0, 0.4)} - 10*{ramp(0.45, 0.85)}"),
            "cape": expr(f"-10*{ramp(0.45, 0.85)}"),
            **legs(f"-70*{ramp(0.0, 0.4)} + 70*{ramp(0.45, 0.85)}", f"-62*{ramp(0.0, 0.4)} + 62*{ramp(0.45, 0.85)}",
                   f"124*{ramp(0.0, 0.4)} - 124*{ramp(0.45, 0.85)}", f"114*{ramp(0.0, 0.4)} - 114*{ramp(0.45, 0.85)}"),
            # face down, the sabatons' toes turn back along the ground
            "near_foot": expr(f"-(-70*{ramp(0.0, 0.4)} + 124*{ramp(0.0, 0.4)}) - 70*{ramp(0.45, 0.85)}"),
            "far_foot": expr(f"-(-62*{ramp(0.0, 0.4)} + 114*{ramp(0.0, 0.4)}) - 70*{ramp(0.45, 0.85)}"),
            # the cape gathers on the ground as he kneels, and lies along his back
            "bone.cape.scale_y": expr(f"1 - (24/126)*{ramp(0.0, 0.4)}*(1 - {ramp(0.45, 0.85)})"),
            # the near arm reaches out ahead of him as he goes down, still
            # gripping the halberd, which stays upright, its butt on the ground
            "near_arm_u": expr(f"-184*{ramp(0.45, 0.85)}"),
            "near_arm_l": expr(f"78*{ramp(0.45, 0.85)}"),
            "near_hand": expr(f"-(10*{ramp(0.0, 0.4)} + (84 + 6 - 184 + 78)*{ramp(0.45, 0.85)})"),
            "bone.weapon.y": expr(f"-32*{ramp(0.0, 0.4)} - 42*{ramp(0.45, 0.85)}"),
            # the far arm along his side
            "far_arm_u": expr(f"16*{ramp(0.45, 0.85)}"),
            **visor("t >= 0.7"),
        },
    },
}


def build() -> dict:
    joints = art.joints()
    bones = []
    for name, (parent, at) in art.BONES.items():
        x, y = joints[at]
        if parent:
            px, py = joints[art.BONES[parent][1]]
            offset = [round((x - px) * SCALE, 4), round((y - py) * SCALE, 4)]
        else:
            offset = [round((x - CENTER_X) * SCALE, 4), round((y - art.GROUND_Y) * SCALE, 4)]
        bones.append({"name": name, "parent": parent or None, "offset": offset, "length": 0, "rest_angle": 0})
    parts = []
    for group, _label, part, bone, z, channel in art.layers():
        x, y = joints[art.BONES[bone][1]]
        entry = {"name": part, "bone": bone, "z": z, "kind": "sprite", "include": [group], "pivot": [x, y], "rest_angle": 0}
        if channel:
            entry["opacity_channel"] = channel
            entry["opacity_default"] = 1 if channel == "eye_open" else 0
        parts.append(entry)
    return {
        "name": "dark_lord",
        "frame": FRAME,
        "svg_source": {"path": "../../../../data/characters/dark_lord/dark_lord.svg", "view": art.VIEW, "ref_dpi": 25.4, "scale": SCALE},
        "sprite_tuning": {"collision_scale": 1.0, "frame_sample_inset": 1},
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
