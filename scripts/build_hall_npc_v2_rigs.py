#!/usr/bin/env python3
"""Draw and rig the five redrawn hall NPCs: one skeleton, one set of rows.

    uv run python scripts/build_hall_npc_v2_rigs.py            # all five
    uv run python scripts/build_hall_npc_v2_rigs.py vault_keeper_v2

Jon asked (2026-10-22) for new art for the Architect, the Manifest Clerk, the
Vault Keeper, the Merchant Prototype and the General Hero; the looks were
decided 2026-10-23. Each is a side-view SVG rig of its own target
(``targets/characters/hall_npcs_v2.py``), drawn by the candidates' scripts:

* ``architect_v2``: ``architect_and_clerk_art.py`` look A, the modernist: a
  dark suit, round glasses, a violet bow tie, the roll of drawings under his arm;
* ``manifest_clerk``: the same script's look C, the old registrar: a long
  cardigan coat, half-moon glasses, the fanfold manifest from his fist to a heap
  on the floor (he had no art of his own; he wore the Architect's sheet);
* ``vault_keeper_v2``: ``vault_merchant_hero_art.py`` ``keeper_c``: a wine-red
  robe, bald, a black beard, a gold earring, the key-headed vault staff and the
  combination dial on his chest;
* ``merchant_prototype_v2``: ``merchant_b``, the travelling pedlar: the whole
  shop on her back (an axe, a bomb, a health cell), a polka-dot headscarf, an
  apron over a blue skirt;
* ``general_hero_v2``: ``hero_b``, the knight who came back: a breastplate, a
  blue cape, a blond beard, both hands on his planted sword.

This script writes ``data/characters/<id>/<id>.svg`` (the art: one part layer
per bone and a joints layer) and ``rigged/<id>/<id>.rig.json`` (the bones, the
parts and the rows), then installs each SVG's rig catalog. A channel is the
turn of a bone from the drawing, in degrees, positive clockwise on the screen
(a hanging limb swings back, the torso leans forward).

The rows are the four every hall guide had (``idle``, ``walk``, ``talk``,
``interact``) and ``hurt``; the General Hero also has ``slash`` and
``celebrate``. Every one of them holds something in the near hand, so the
near arm keeps still where the prop needs it.
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


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / "svg_art" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


PKG = ROOT / "ambition_sprite2d_renderer"
#: Frame pixels for each SVG unit.
SCALE = 0.5
#: The drawings' centre line and ground, in SVG units.
CENTER_X, GROUND_Y = 280.0, 502.0
FRAME = {"width": 400, "height": 480, "center_x": 200, "ground_y": 460, "ankle_h": 0, "supersample": 3, "render_scale": 1, "trim": False}
#: The walk keeps a foot on the ground the body stands on in every frame, and
#: the run's lowest stride touches it (``RigDocument.plant_offset``).
FRAME["plant"] = {"walk": "each", "run": "row"}

#: target id -> (art script, character key in it, display name, view label)
CAST = {
    "architect_v2": ("architect_and_clerk_art", "architect", "Architect"),
    "manifest_clerk": ("architect_and_clerk_art", "manifest_clerk", "Manifest Clerk"),
    "vault_keeper_v2": ("vault_merchant_hero_art", "vault_keeper", "Vault Keeper"),
    "merchant_prototype_v2": ("vault_merchant_hero_art", "merchant_prototype", "Merchant Prototype"),
    "general_hero_v2": ("vault_merchant_hero_art", "general_hero", "General Hero"),
}

JOLT = "(1-t)*(1-t)"


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


def arms(side: str, u: str, l: str = "0", h: str = "0") -> dict:
    return {f"{side}_arm_u": expr(u), f"{side}_arm_l": expr(l), f"{side}_hand": expr(h)}


#: How each one moves. ``stride``/``knee``: the walk's thigh and shin swing (a
#: robe or a skirt hides the legs, so there the feet only peek out under the
#: hem); ``near``: the near arm's sway in the idle (it holds the prop);
#: ``talk_near``: the near arm's turns while talking; ``far_free``: the far arm
#: swings in the walk; ``both_hands``: both hands are on one prop and turn
#: together; ``planted``: the prop stands on the floor, so the near hand turns
#: against the arm and the torso and the prop stays upright; ``lean`` and
#: ``flinch``: the torso's turn in the nod and the blow (a floor-length robe
#: tilts its hem with the torso, so it leans less).
STYLE: Dict[str, dict] = {
    "architect_v2": dict(stride=19, knee=24, near=1.0, talk_near=("-6 + 4*sin(tau*t)", "-14 + 6*sin(tau*t+0.5)", "8*sin(tau*t+0.5)"), far_free=True),
    "manifest_clerk": dict(stride=16, knee=20, near=0.4, talk_near=("-1.2*sin(tau*t)", "1.2*sin(tau*t)", "0"), far_free=True, stoop=True),
    "vault_keeper_v2": dict(stride=7, knee=6, lean=3, flinch=6, near=0.6, talk_near=("-1.5*sin(tau*t)", "1.0*sin(tau*t)", "0"), far_free=False, planted=True),
    "merchant_prototype_v2": dict(stride=7, knee=6, lean=3, flinch=6, near=1.0, talk_near=("-3*sin(tau*t)", "4*sin(tau*t+0.6)", "0"), far_free=True),
    "general_hero_v2": dict(stride=19, knee=24, near=0.6, talk_near=("-1.5*sin(tau*t)", "1.5*sin(tau*t)", "0"), far_free=False, both_hands=True,
                            planted=True),
}


def clips(target: str) -> dict:
    s = STYLE[target]
    both = s.get("both_hands")
    planted = s.get("planted")
    near_sway = s["near"]
    stoop = 3.0 if s.get("stoop") else 0.0

    def hold(u: str, l: str = "0", h: str = "0", torso: str = "0", upright: bool = True) -> dict:
        """The near arm's turns (with both hands on one prop, the far arm's
        too); a planted prop is kept upright against the arm and ``torso``."""
        if planted and upright:
            h = f"({h}) - (({u}) + ({l}) + ({torso}))"
        out = arms("near", u, l, h)
        if both:
            out.update(arms("far", u, l, h))
        return out

    stride, knee = s["stride"], s["knee"]
    walk_torso = f"{stoop} + 1 + 1.0*sin(2*tau*t)"
    if both:
        # He lifts the sword off the floor with his forearms and carries it, point down.
        walk_hold = hold("2*sin(2*tau*t)", "-32", torso=walk_torso)
    else:
        walk_hold = hold(f"{2.0 * near_sway}*sin(tau*t)", torso=walk_torso)
        walk_hold.update(arms("far", "-18*sin(tau*t)", "-10") if s["far_free"] else arms("far", "-4*sin(tau*t)"))
    tu, tl, th = s["talk_near"]
    talk_torso = "1.5 + 1.2*sin(tau*t)"
    talk = {
        "root_y": expr("-0.5*abs(sin(tau*t))"),
        "torso": expr(talk_torso),
        "head": expr("-3 + 4*sin(2*tau*t)"),
        **hold(tu, tl, th, torso=talk_torso),
    }
    if not both:
        talk.update(arms("far", "-3*sin(tau*t)", "-6"))
    idle_torso = f"{stoop} + 0.8*sin(tau*t)"
    k = s.get("lean", 7)
    lean = f"{stoop} + {k}*{ramp(0.0, 0.4)} - {k}*{ramp(0.6, 1.0)}"
    rows = {
        # He breathes; the near hand keeps its hold.
        "idle": {
            "loop": True, "frames": 6, "duration_ms": 140,
            "channels": {
                "root_y": expr("0.6*sin(tau*t)"),
                "torso": expr(idle_torso),
                "head": expr("-1.2*sin(tau*t+0.6)"),
                **hold(f"{near_sway}*sin(tau*t)", f"{-near_sway}*sin(tau*t)", torso=idle_torso),
                **({} if both else arms("far", "-1.5*sin(tau*t)")),
            },
        },
        "walk": {
            "loop": True, "frames": 8, "duration_ms": 100,
            "channels": {
                "root_y": expr("-2.0*(1-abs(sin(tau*t)))"),
                "torso": expr(walk_torso),
                "head": expr("-1 - 1.0*sin(2*tau*t)"),
                **legs(f"-{stride}*sin(tau*t)", f"{stride}*sin(tau*t)", f"{knee}*max(0.0, cos(tau*t))", f"{knee}*max(0.0, -cos(tau*t))"),
                **walk_hold,
            },
        },
        "talk": {"loop": True, "frames": 6, "duration_ms": 120, "channels": talk},
        # A nod over the counter: a lean in and a dip of the head.
        "interact": {
            "loop": False, "frames": 6, "duration_ms": 110,
            "channels": {
                "torso": expr(lean),
                "head": expr(f"10*{ramp(0.1, 0.45)} - 10*{ramp(0.6, 1.0)}"),
                **hold(f"-3*{ramp(0.0, 0.4)} + 3*{ramp(0.6, 1.0)}", torso=lean),
                **({} if both or not s["far_free"] else arms("far", f"-40*{ramp(0.0, 0.4)} + 40*{ramp(0.6, 1.0)}", f"-30*{ramp(0.0, 0.4)} + 30*{ramp(0.6, 1.0)}")),
            },
        },
        # A blow: a flinch back, the head thrown.
        "hurt": {
            "loop": False, "frames": 4, "duration_ms": 92,
            "channels": {
                "root_x": expr(f"-5*{JOLT}"),
                "torso": expr(f"{stoop} - {s.get('flinch', 10)}*{JOLT}"),
                "head": expr(f"-12*{JOLT}"),
                **hold(f"-6*{JOLT}", upright=False),
                **({} if both else arms("far", f"24*{JOLT}")),
                **legs(f"-6*{JOLT}", f"6*{JOLT}", "0", f"4*{JOLT}"),
            },
        },
    }
    if target == "general_hero_v2":
        rows.update(hero_rows(hold))
    return rows


def hero_rows(hold) -> dict:
    """The General Hero's own rows, both hands on the hilt: he lifts the sword
    over his shoulder and cuts down before him, and he raises it to the sky.

    The blade hangs point down from his hands as drawn; it points where the
    sum of the arm's and the hand's turns takes it. The wind-up's sum is -225
    (point up and back), the cut's -70 (point forward and a little down), the
    raise's -180 (point up): the forearm straightened (it is drawn bent
    forward), so the hands go up above his brow and clear of his face."""
    lift = ramp(0.0, 0.3)
    cut = ramp(0.35, 0.6)
    back = ramp(0.75, 1.0)
    up = ramp(0.0, 0.4)
    return {
        "slash": {
            "loop": False, "frames": 7, "duration_ms": 80,
            "channels": {
                "root_x": expr(f"-3*{lift} + 12*{cut} - 9*{back}"),
                "root_y": expr(f"4*{cut} - 4*{back}"),
                "torso": expr(f"-6*{lift} + 16*{cut} - 10*{back}"),
                "head": expr(f"4*{lift} - 8*{cut} + 4*{back}"),
                **hold(f"-160*{lift} + 80*{cut} + 80*{back}", f"50*{lift} + 20*{cut} - 70*{back}", f"-115*{lift} + 55*{cut} + 60*{back}", upright=False),
                **legs(f"-30*{cut} + 30*{back}", f"16*{cut} - 16*{back}", f"30*{cut} - 30*{back}", "0"),
            },
        },
        "celebrate": {
            "loop": False, "frames": 8, "duration_ms": 110,
            "channels": {
                "root_y": expr(f"-3*{ramp(0.3, 0.5)} + 3*{ramp(0.5, 0.7)}"),
                "torso": expr(f"-5*{up}"),
                "head": expr(f"-12*{ramp(0.1, 0.5)}"),
                **hold(f"-140*{up}", f"60*{up}", f"-100*{up}", upright=False),
            },
        },
    }


def frame_point(x: float, y: float) -> dict:
    return {"x": round(FRAME["center_x"] + (x - CENTER_X) * SCALE, 1), "y": round(FRAME["ground_y"] + (y - GROUND_Y) * SCALE, 1)}


def draw(target: str):
    """The cast look's SVG text and its drawing (parts and joints)."""
    script, char, title = CAST[target]
    art = _load(script)
    d = art.rig_drawing(char)
    svgkit = art.svg
    for name, bone, z, body in d["parts"]:
        svgkit.part(name.replace("_", "-"), name.replace("_", " ").title(), name, bone, z, body)
    view = f"{title} v2 - Side Right" if target.endswith("_v2") else f"{title} - Side Right"
    text = svgkit.document(
        size=(560, 560), design=target, layer_id=target.replace("_", "-"), label=view,
        comment=[f"  <!-- {title}: {d['label']}; side view facing right, the ground at y={GROUND_Y:g}.",
                 f"       Drawn by scripts/svg_art/{script}.py (look chosen 2026-10-23); rigged by scripts/build_hall_npc_v2_rigs.py. -->"],
        joints=svgkit.joints_layer({k: (v[1], v[2]) for k, v in d["joints"].items()}),
    )
    return text, d, view


def build(target: str) -> Path:
    text, d, view = draw(target)
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
        parts.append({"name": name, "bone": bone, "z": z, "kind": "sprite", "include": [name.replace("_", "-")], "pivot": [round(x, 3), round(y, 3)],
                      "rest_angle": 0})
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
        "clips": clips(target),
    }
    out = PKG / "targets" / "characters" / "rigged" / target / f"{target}.rig.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf8")
    tmp.replace(out)
    print(f"wrote {svg_path.relative_to(ROOT)}")
    print(f"wrote {out.relative_to(ROOT)}")
    return out


def sockets(target: str) -> dict:
    """The actor sockets, in frame pixels, from the drawing's joints."""
    _text, d, _view = draw(target)
    J = d["joints"]
    head = J["head"]
    crown_y = GROUND_Y - d["height"]
    return {
        "head": frame_point(head[1], (head[2] + crown_y) / 2),
        "chest": frame_point(J["torso"][1], (J["head"][2] + J["torso"][2]) / 2),
        "hand_l": frame_point(J["far_hand"][1], J["far_hand"][2]),
        "hand_r": frame_point(J["near_hand"][1], J["near_hand"][2]),
        "speech_bubble": frame_point(head[1], crown_y - 20),
    }


def main() -> None:
    targets = sys.argv[1:] or list(CAST)
    for target in targets:
        if target not in CAST:
            raise SystemExit(f"unknown target {target!r}; one of {', '.join(CAST)}")
        rig = build(target)
        # Only these SVGs: another drawing's catalog is not this script's to write.
        svg_path = PKG / "data" / "characters" / target / f"{target}.svg"
        if install_catalog(svg_path, [rig]):
            print(f"catalog {svg_path.relative_to(ROOT)}")
    print(json.dumps({t: sockets(t) for t in targets}, indent=1))


if __name__ == "__main__":
    main()
