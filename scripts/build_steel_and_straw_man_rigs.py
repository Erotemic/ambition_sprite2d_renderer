#!/usr/bin/env python3
"""Draw and rig the Steel Man and the Straw Man.

    uv run python scripts/build_steel_and_straw_man_rigs.py            # both
    uv run python scripts/build_steel_and_straw_man_rigs.py straw_man

Jon asked (2026-10-23) for two new characters, the Steel Man (the opposing
argument at its strongest) and the Straw Man (comic relief), NOT the Tin Man
and the Scarecrow. ``scripts/svg_art/steel_and_straw_man_art.py`` draws three
looks of each; the cast looks are steel A (the girder) and straw A (the
sheaf). This script writes each one's SVG (``data/characters/<id>/<id>.svg``:
the side view as part layers in the cell at the origin, the front view in the
next cell, a joints layer) and its rig (``rigged/<id>/<id>.rig.json``: the
bones from the joints, one part per layer, the rows), then installs the SVG's
rig catalog. The targets are ``targets/characters/steel_and_straw_man.py``.

A channel is the turn of a bone from the drawing, in degrees, positive
clockwise on the screen (a hanging limb swings back, the torso leans forward);
``bone.<name>.x`` / ``.y`` move a bone in frame pixels.

The rows: ``idle``, ``walk``, ``talk``, ``interact`` and ``hurt``. The Steel
Man is steady: his idle only breathes, he walks with a measured stride, he
talks like an orator with an open hand, and a blow hardly moves him. The Straw
Man wobbles: his idle sways and sheds a straw, his walk flops, he boasts with
his chest out, and a blow knocks straw out of him.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Dict

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ambition_sprite2d_renderer.devtools.svg_rig_tool import install_catalog  # noqa: E402

_spec = importlib.util.spec_from_file_location("steel_and_straw_man_art", ROOT / "scripts" / "svg_art" / "steel_and_straw_man_art.py")
art = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(art)

PKG = ROOT / "ambition_sprite2d_renderer"
#: Frame pixels for each SVG unit.
SCALE = 0.5
CENTER_X, GROUND_Y = art.CX, art.GROUND
FRAME = {"width": 400, "height": 480, "center_x": 200, "ground_y": 460, "ankle_h": 0, "supersample": 3, "render_scale": 1, "trim": False}
#: The walk keeps a foot on the ground the body stands on in every frame, and
#: the run's lowest stride touches it (``RigDocument.plant_offset``).
FRAME["plant"] = {"walk": "each", "run": "row"}

#: target id -> the art's character key
CAST = {"steel_man": "steel", "straw_man": "straw"}

JOLT = "(1-t)*(1-t)"


def expr(text: str) -> dict:
    return {"expr": text}


def ramp(a: float, b: float) -> str:
    """0 to 1 between ``a`` and ``b`` of the row, eased, held after."""
    return f"(lambda u: u*u*(3-2*u))(max(0.0, min(1.0, (t-{a})/{b - a})))"


def legs(near_u: str, far_u: str, near_l: str, far_l: str) -> dict:
    """Thigh and shin turns; each foot kept flat."""
    return {
        "near_leg_u": expr(near_u), "far_leg_u": expr(far_u),
        "near_leg_l": expr(near_l), "far_leg_l": expr(far_l),
        "near_foot": expr(f"-(({near_u}) + ({near_l}))"),
        "far_foot": expr(f"-(({far_u}) + ({far_l}))"),
    }


def arms(side: str, u: str, l: str = "0", h: str = "0") -> dict:
    return {f"{side}_arm_u": expr(u), f"{side}_arm_l": expr(l), f"{side}_hand": expr(h)}


def mouth(when: str) -> dict:
    return {"mouth_open": expr(f"1 if ({when}) else 0")}


def steel_clips() -> dict:
    lean = f"6*{ramp(0.0, 0.4)} - 6*{ramp(0.6, 1.0)}"
    return {
        # He stands his ground: a slow breath, nothing else moves.
        "idle": {
            "loop": True, "frames": 8, "duration_ms": 170,
            "channels": {
                "root_y": expr("0.35*sin(tau*t)"),
                "torso": expr("-0.5*sin(tau*t)"),
                "head": expr("0.4*sin(tau*t+0.8)"),
                **arms("near", "0.6*sin(tau*t)", "-0.4*sin(tau*t)"),
                **arms("far", "-0.6*sin(tau*t)", "0.4*sin(tau*t)"),
            },
        },
        # A measured stride, upright, the arms swinging a little.
        "walk": {
            "loop": True, "frames": 8, "duration_ms": 115,
            "channels": {
                "root_y": expr("-1.6*(1-abs(sin(tau*t)))"),
                "torso": expr("1.5 + 0.6*sin(2*tau*t)"),
                "head": expr("-1.5 - 0.6*sin(2*tau*t)"),
                **legs("-17*sin(tau*t)", "17*sin(tau*t)", "22*max(0.0, cos(tau*t))", "22*max(0.0, -cos(tau*t))"),
                **arms("near", "12*sin(tau*t)", "-8 + 4*sin(tau*t)"),
                **arms("far", "-12*sin(tau*t)", "-8 - 4*sin(tau*t)"),
            },
        },
        # The orator: the near hand open before him, a measured beat.
        "talk": {
            "loop": True, "frames": 8, "duration_ms": 130,
            "channels": {
                "torso": expr("-1 + 0.8*sin(tau*t)"),
                "head": expr("-2 + 2*sin(2*tau*t)"),
                **arms("near", "-22 + 5*sin(tau*t)", "-58 + 8*sin(tau*t+0.6)", "-10 + 6*sin(tau*t+1.0)"),
                **arms("far", "-4", "-6"),
                **mouth("sin(2*tau*t) > -0.3"),
            },
        },
        # A considered nod: a lean in, the head dips, the near hand comes up.
        "interact": {
            "loop": False, "frames": 6, "duration_ms": 120,
            "channels": {
                "torso": expr(lean),
                "head": expr(f"9*{ramp(0.1, 0.45)} - 9*{ramp(0.6, 1.0)}"),
                **arms("near", f"-24*{ramp(0.0, 0.4)} + 24*{ramp(0.6, 1.0)}", f"-30*{ramp(0.0, 0.4)} + 30*{ramp(0.6, 1.0)}"),
            },
        },
        # A blow: steel hardly gives; a short rock back.
        "hurt": {
            "loop": False, "frames": 4, "duration_ms": 92,
            "channels": {
                "root_x": expr(f"-2*{JOLT}"),
                "torso": expr(f"-4*{JOLT}"),
                "head": expr(f"-5*{JOLT}"),
                **arms("near", f"-6*{JOLT}"),
                **arms("far", f"8*{JOLT}"),
            },
        },
    }


def fall(name: str, start: float, length: float, drop: float, drift: float, spin: float) -> dict:
    """A loose straw lets go at ``start`` of the row, falls ``drop`` frame
    pixels (drifting ``drift``) and turns ``spin`` degrees in ``length`` of
    it, fading in its last fifth; before and after it is not drawn."""
    u = f"max(0.0, min(1.0, (t-{start})/{length}))"
    on = f"({start} <= t <= {start + length})"
    return {
        f"bone.{name}.y": expr(f"{drop}*({u})**1.6"),
        f"bone.{name}.x": expr(f"{drift}*sin(3.2*({u}))"),
        name: expr(f"{spin}*({u})"),
        name + "_vis": expr(f"(1.0 - max(0.0, ({u} - 0.8)/0.2)) if {on} else 0.0"),
    }


def straw_clips() -> dict:
    wob = "sin(tau*t)"
    lean = f"10*{ramp(0.0, 0.35)} - 10*{ramp(0.6, 1.0)}"
    return {
        # He cannot stand still: he sways on his bundles, his head lags, and
        # a straw works loose and falls.
        "idle": {
            "loop": True, "frames": 12, "duration_ms": 120,
            "channels": {
                "root_x": expr(f"1.2*{wob}"),
                "root_y": expr("0.6*sin(2*tau*t)"),
                "torso": expr(f"-3 + 3.5*{wob}"),
                "head": expr("-6 - 5*sin(tau*t-1.1)"),
                **legs(f"-2.5*{wob}", f"2*{wob}", f"3*max(0.0, {wob})", f"3*max(0.0, -{wob})"),
                **arms("near", "4 - 6*sin(tau*t-0.9)", "-6 - 8*sin(tau*t-1.6)", "10*sin(tau*t-2.0)"),
                **arms("far", "-3 + 6*sin(tau*t-0.6)", "-8 + 8*sin(tau*t-1.3)", "-8*sin(tau*t-1.8)"),
                **fall("chaff_1", 0.08, 0.6, 92, 7, 160),
                **fall("chaff_2", 0.5, 0.45, 70, -6, -120),
            },
        },
        # A floppy stride: the knees fold, the arms flail, the head bobs.
        "walk": {
            "loop": True, "frames": 8, "duration_ms": 100,
            "channels": {
                "root_y": expr("-3.0*(1-abs(sin(tau*t)))"),
                "torso": expr("-2 + 4*sin(2*tau*t)"),
                "head": expr("-6 - 7*sin(2*tau*t-1.0)"),
                **legs("-24*sin(tau*t)", "24*sin(tau*t)", "34*max(0.0, cos(tau*t))", "34*max(0.0, -cos(tau*t))"),
                **arms("near", "26*sin(tau*t)", "-18 - 16*sin(tau*t-0.9)", "18*sin(tau*t-1.4)"),
                **arms("far", "-26*sin(tau*t)", "-18 + 16*sin(tau*t-0.9)", "-18*sin(tau*t-1.4)"),
                **fall("chaff_3", 0.1, 0.7, 50, -16, 200),
            },
        },
        # The boast: chest out, chin up, a thumb jerked at himself, the
        # other hand on his hip.
        "talk": {
            "loop": True, "frames": 8, "duration_ms": 120,
            "channels": {
                "root_y": expr("-0.8*abs(sin(tau*t))"),
                "torso": expr("-7 + 2*sin(tau*t)"),
                "head": expr("-10 + 5*sin(2*tau*t)"),
                **arms("near", "-40 + 6*sin(tau*t)", "-138 + 10*sin(2*tau*t)", "-20 + 10*sin(2*tau*t)"),
                **arms("far", "28", "-78", "20"),
                **mouth("sin(2*tau*t) > -0.4"),
            },
        },
        # A nod he overdoes: he leans in, the head flops, he springs back.
        "interact": {
            "loop": False, "frames": 6, "duration_ms": 110,
            "channels": {
                "torso": expr(lean),
                "head": expr(f"18*{ramp(0.1, 0.4)} - 22*{ramp(0.55, 0.85)} + 4*{ramp(0.85, 1.0)}"),
                **arms("near", f"-34*{ramp(0.0, 0.4)} + 34*{ramp(0.6, 1.0)}", f"-30*{ramp(0.0, 0.4)} + 30*{ramp(0.6, 1.0)}"),
                **arms("far", f"10*{ramp(0.0, 0.4)} - 10*{ramp(0.6, 1.0)}"),
            },
        },
        # A blow knocks him loose: he folds back, the head pops up off its
        # neck, the arms fly, and straw bursts out of him.
        "hurt": {
            "loop": False, "frames": 5, "duration_ms": 92,
            "channels": {
                "root_x": expr(f"-8*{JOLT}"),
                "torso": expr(f"-16*{JOLT}"),
                "head": expr(f"-22*{JOLT}"),
                "bone.head.y": expr(f"-7*{JOLT}"),
                **arms("near", f"-40*{JOLT}", f"-30*{JOLT}"),
                **arms("far", f"50*{JOLT}", f"20*{JOLT}"),
                **legs(f"-10*{JOLT}", f"10*{JOLT}", f"8*{JOLT}", f"8*{JOLT}"),
                **fall("chaff_1", 0.0, 1.0, 34, 22, 260),
                **fall("chaff_2", 0.0, 1.0, 26, -26, -220),
                **fall("chaff_3", 0.0, 1.0, 20, 30, 180),
            },
        },
    }


def frame_point(x: float, y: float) -> dict:
    return {"x": round(FRAME["center_x"] + (x - CENTER_X) * SCALE, 1), "y": round(FRAME["ground_y"] + (y - GROUND_Y) * SCALE, 1)}


def build(target: str) -> Path:
    who = CAST[target]
    text = art.svg_text(who, comment="; rigged by scripts/build_steel_and_straw_man_rigs.py")
    d = art.rig_drawing(who)
    view = art.SIDE_LABEL.format(name=art.NAMES[who])
    svg_path = PKG / "data" / "characters" / target / f"{target}.svg"
    svg_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = svg_path.with_suffix(".svg.tmp")
    tmp.write_text(text, encoding="utf8")
    tmp.replace(svg_path)
    joints = d["joints"]
    bones = []
    for name, (parent, x, y) in joints.items():
        if parent:
            _, px, py = joints[parent]
            offset = [round((x - px) * SCALE, 4), round((y - py) * SCALE, 4)]
        else:
            offset = [round((x - CENTER_X) * SCALE, 4), round((y - GROUND_Y) * SCALE, 4)]
        bones.append({"name": name, "parent": parent or None, "offset": offset, "length": 0, "rest_angle": 0})
    parts = []
    for name, bone, z, _body in d["parts"]:
        _, x, y = joints[bone]
        part = {"name": name, "bone": bone, "z": z, "kind": "sprite", "include": [name.replace("_", "-")], "pivot": [round(x, 3), round(y, 3)],
                "rest_angle": 0}
        if name in art.SWITCHED:
            part["opacity_channel"] = name if name == "mouth_open" else name + "_vis"
            part["opacity_default"] = 0
        parts.append(part)
    doc = {
        "name": target,
        "frame": FRAME,
        "svg_source": {"path": f"../../../../data/characters/{target}/{target}.svg", "view": view, "ref_dpi": 25.4, "scale": SCALE},
        "sprite_tuning": {"collision_scale": 1.2, "frame_sample_inset": 1},
        "palette": {},
        "bones": bones,
        "parts": parts,
        "ik_legs": [],
        "ik_chains": [],
        "clips": steel_clips() if who == "steel" else straw_clips(),
    }
    out = PKG / "targets" / "characters" / "rigged" / target / f"{target}.rig.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf8")
    tmp.replace(out)
    print(f"wrote {svg_path.relative_to(ROOT)}")
    print(f"wrote {out.relative_to(ROOT)}")
    return out


def main() -> None:
    targets = sys.argv[1:] or list(CAST)
    for target in targets:
        if target not in CAST:
            raise SystemExit(f"unknown target {target!r}; one of {', '.join(CAST)}")
        rig = build(target)
        svg_path = PKG / "data" / "characters" / target / f"{target}.svg"
        if install_catalog(svg_path, [rig]):
            print(f"catalog {svg_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
