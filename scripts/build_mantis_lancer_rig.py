#!/usr/bin/env python3
"""Build the Mantis Lancer's rig document (``mantis_lancer``).

    uv run python scripts/svg_art/mantis_lancer_art.py   # the drawing, once
    uv run python scripts/build_mantis_lancer_rig.py

The drawing says where each part turns (``JOINTS`` in the art script). This
script makes the skeleton from those joints, binds each part layer to its
bone, and authors the rows. It never draws. A channel is the turn of a bone
from the drawing, in degrees (positive clockwise on the screen: a hanging
limb swings back, the prothorax leans forward).

The rows are the seven it has always had: ``idle``, ``walk``, ``stab``,
``slash``, ``pounce``, ``hurt``, ``death``.
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

_spec = importlib.util.spec_from_file_location("mantis_lancer_art", ROOT / "scripts" / "svg_art" / "mantis_lancer_art.py")
art = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(art)

PKG = ROOT / "ambition_sprite2d_renderer"
OUT = PKG / "targets" / "characters" / "rigged" / "mantis_lancer" / "mantis_lancer.rig.json"

#: Frame pixels for each SVG unit.
SCALE = 0.5
#: Its centre line (the thorax), in SVG units: the frame's centre.
CENTER_X = 250.0
FRAME = {"width": 304, "height": 240, "center_x": 128, "ground_y": 228, "ankle_h": 0, "supersample": 3, "render_scale": 1, "trim": False}
#: The walk keeps a foot on the ground the body stands on in every frame, and
#: the run's lowest stride touches it (``RigDocument.plant_offset``).
FRAME["plant"] = {"walk": "each", "run": "row"}

JOLT = "(1-t)*(1-t)"


def expr(text: str) -> dict:
    return {"expr": text}


#: A key: 0 to 1 between ``a`` and ``b`` of the row, eased, held after.
def ramp(a: float, b: float) -> str:
    return f"(lambda u: u*u*(3-2*u))(max(0.0, min(1.0, (t-{a})/{b - a})))"


def leg(prefix: str, u: str, l: str) -> dict:
    """A leg's femur and tibia turns; its tarsus kept flat on the ground."""
    return {f"{prefix}_u": expr(u), f"{prefix}_l": expr(l), f"{prefix}_foot": expr(f"-(({u}) + ({l}))")}


def legs(fore_u: str, fore_l: str, hind_u: str, hind_l: str, far_fore_u: str = None, far_fore_l: str = None,
         far_hind_u: str = None, far_hind_l: str = None) -> dict:
    """All four legs; the far pair copies the near pair unless given."""
    return {**leg("near_fore", fore_u, fore_l), **leg("near_hind", hind_u, hind_l),
            **leg("far_fore", far_fore_u or fore_u, far_fore_l or fore_l),
            **leg("far_hind", far_hind_u or hind_u, far_hind_l or hind_l)}


def gait(phase: str) -> tuple:
    """One leg's walk: the thigh swings forward with the knee lifted, then
    pushes back planted. ``phase`` offsets it in the cycle."""
    return (f"-16*sin(tau*t+{phase})", f"22*max(0.0, cos(tau*t+{phase}))")


def dead(dead: str = "False") -> dict:
    return {"eye_dead": expr(f"1 if ({dead}) else 0"), "eye_open": expr(f"0 if ({dead}) else 1")}


# The near arm's strike: the coxa swings forward, the blade and the hook
# unfold into one straight lance (the hook turns about 175 degrees).
STRIKE = {"near_coxa": -50.0, "near_blade": 80.0, "near_hook": -172.0}

CLIPS = {
    # The praying guard: a slow sway, the blades held up, the abdomen breathing.
    "idle": {
        "loop": True, "frames": 6, "duration_ms": 130,
        "channels": {
            "root_y": expr("0.6*sin(tau*t)"),
            "prothorax": expr("2*sin(tau*t)"),
            "head": expr("-4*sin(tau*t+0.5)"),
            "abdomen": expr("1.5*sin(tau*t+1.2)"),
            "near_coxa": expr("-2*sin(tau*t)"), "near_hook": expr("4*sin(tau*t+0.8)"),
            "far_coxa": expr("-2*sin(tau*t+0.4)"), "far_hook": expr("3*sin(tau*t+1.2)"),
            **dead(),
        },
    },
    # Four legs in a stalking alternation; the guard held, the head steady.
    "walk": {
        "loop": True, "frames": 8, "duration_ms": 95,
        "channels": {
            "root_y": expr("-1.5*abs(sin(tau*t))"),
            "prothorax": expr("1.5*sin(2*tau*t)"),
            "head": expr("-1.5*sin(2*tau*t)"),
            "abdomen": expr("2*sin(2*tau*t+1)"),
            **legs(*gait("0"), *gait("3.14159"), far_fore_u=gait("3.14159")[0], far_fore_l=gait("3.14159")[1],
                   far_hind_u=gait("0")[0], far_hind_l=gait("0")[1]),
            "near_coxa": expr("3*sin(tau*t)"), "far_coxa": expr("-3*sin(tau*t)"),
            **dead(),
        },
    },
    # Drawn back, then the near blade unfolds and lances straight forward.
    "stab": {
        "loop": False, "frames": 7, "duration_ms": 80,
        "channels": {
            "root_x": expr(f"-3*{ramp(0.0, 0.3)} + 12*{ramp(0.3, 0.5)} - 9*{ramp(0.7, 1.0)}"),
            "prothorax": expr(f"-10*{ramp(0.0, 0.3)} + 30*{ramp(0.3, 0.5)} - 20*{ramp(0.7, 1.0)}"),
            "head": expr(f"6*{ramp(0.0, 0.3)} - 20*{ramp(0.3, 0.5)} + 14*{ramp(0.7, 1.0)}"),
            "near_coxa": expr(f"16*{ramp(0.0, 0.3)} + ({STRIKE['near_coxa']} - 16)*{ramp(0.3, 0.5)} - ({STRIKE['near_coxa']})*{ramp(0.7, 1.0)}"),
            "near_blade": expr(f"-14*{ramp(0.0, 0.3)} + ({STRIKE['near_blade']} + 14)*{ramp(0.3, 0.5)} - {STRIKE['near_blade']}*{ramp(0.7, 1.0)}"),
            "near_hook": expr(f"{STRIKE['near_hook']}*{ramp(0.3, 0.5)} - ({STRIKE['near_hook']})*{ramp(0.7, 1.0)}"),
            "far_coxa": expr(f"-10*{ramp(0.3, 0.5)} + 10*{ramp(0.7, 1.0)}"),
            **legs(f"-14*{ramp(0.3, 0.5)} + 14*{ramp(0.7, 1.0)}", f"10*{ramp(0.3, 0.5)} - 10*{ramp(0.7, 1.0)}",
                   f"-10*{ramp(0.3, 0.5)} + 10*{ramp(0.7, 1.0)}", f"8*{ramp(0.3, 0.5)} - 8*{ramp(0.7, 1.0)}"),
            "fx_stab": expr("1 if 0.4 < t < 0.75 else 0"),
            **dead(),
        },
    },
    # The near blade raised forward and up, clear of the face, its hook
    # opened square to it like a scythe; then swept down through the ground
    # in front of it.
    "slash": {
        "loop": False, "frames": 7, "duration_ms": 80,
        "channels": {
            "root_x": expr(f"-2*{ramp(0.0, 0.3)} + 8*{ramp(0.3, 0.55)} - 6*{ramp(0.75, 1.0)}"),
            "prothorax": expr(f"-12*{ramp(0.0, 0.3)} + 34*{ramp(0.3, 0.55)} - 22*{ramp(0.75, 1.0)}"),
            "head": expr(f"8*{ramp(0.0, 0.3)} - 24*{ramp(0.3, 0.55)} + 16*{ramp(0.75, 1.0)}"),
            "near_coxa": expr(f"-92*{ramp(0.0, 0.3)} + 80*{ramp(0.3, 0.55)} + 12*{ramp(0.75, 1.0)}"),
            "near_blade": expr(f"120*{ramp(0.0, 0.3)} - 45*{ramp(0.3, 0.55)} - 75*{ramp(0.75, 1.0)}"),
            "near_hook": expr(f"-85*{ramp(0.0, 0.3)} + 85*{ramp(0.75, 1.0)}"),
            "far_coxa": expr(f"-14*{ramp(0.0, 0.3)} + 14*{ramp(0.75, 1.0)}"),
            **legs(f"-10*{ramp(0.3, 0.55)} + 10*{ramp(0.75, 1.0)}", f"8*{ramp(0.3, 0.55)} - 8*{ramp(0.75, 1.0)}",
                   f"-8*{ramp(0.3, 0.55)} + 8*{ramp(0.75, 1.0)}", "0"),
            "fx_slash": expr("1 if 0.4 < t < 0.7 else 0"),
            **dead(),
        },
    },
    # A crouch, a leap forward with both blades flung open, and a landing.
    "pounce": {
        "loop": False, "frames": 8, "duration_ms": 85,
        "channels": {
            "root_y": expr(f"10*{ramp(0.0, 0.25)} - 46*{ramp(0.25, 0.45)} + 36*{ramp(0.5, 0.75)} + 0*{ramp(0.75, 1.0)}"
                           f" - 10*{ramp(0.8, 1.0)}"),
            "root_x": expr(f"18*{ramp(0.25, 0.5)} - 18*{ramp(0.6, 1.0)}"),
            "prothorax": expr(f"-8*{ramp(0.0, 0.25)} + 30*{ramp(0.25, 0.45)} - 22*{ramp(0.6, 1.0)}"),
            "head": expr(f"-16*{ramp(0.25, 0.45)} + 16*{ramp(0.6, 1.0)}"),
            "abdomen": expr(f"6*{ramp(0.0, 0.25)} - 14*{ramp(0.25, 0.45)} + 8*{ramp(0.6, 1.0)}"),
            # crouched (fore knees forward, hind knees back), then stretched out behind, then crouched to land
            **legs(f"-22*{ramp(0.0, 0.25)} + 40*{ramp(0.25, 0.45)} - 40*{ramp(0.5, 0.75)} + 22*{ramp(0.8, 1.0)}",
                   f"30*{ramp(0.0, 0.25)} - 40*{ramp(0.25, 0.45)} + 40*{ramp(0.5, 0.75)} - 30*{ramp(0.8, 1.0)}",
                   f"20*{ramp(0.0, 0.25)} + 14*{ramp(0.25, 0.45)} - 14*{ramp(0.5, 0.75)} - 20*{ramp(0.8, 1.0)}",
                   f"-26*{ramp(0.0, 0.25)} + 40*{ramp(0.25, 0.45)} - 40*{ramp(0.5, 0.75)} + 26*{ramp(0.8, 1.0)}"),
            "near_coxa": expr(f"{STRIKE['near_coxa']}*{ramp(0.3, 0.5)} - ({STRIKE['near_coxa']})*{ramp(0.65, 0.95)}"),
            "near_blade": expr(f"{STRIKE['near_blade'] - 30}*{ramp(0.3, 0.5)} - {STRIKE['near_blade'] - 30}*{ramp(0.65, 0.95)}"),
            "near_hook": expr(f"-110*{ramp(0.3, 0.5)} + 110*{ramp(0.65, 0.95)}"),
            "far_coxa": expr(f"-40*{ramp(0.3, 0.5)} + 40*{ramp(0.65, 0.95)}"),
            "far_blade": expr(f"40*{ramp(0.3, 0.5)} - 40*{ramp(0.65, 0.95)}"),
            "far_hook": expr(f"-100*{ramp(0.3, 0.5)} + 100*{ramp(0.65, 0.95)}"),
            **dead(),
        },
    },
    # A blow: it rears back, the blades jolted open.
    "hurt": {
        "loop": False, "frames": 4, "duration_ms": 90,
        "channels": {
            "root_x": expr(f"-5*{JOLT}"),
            "prothorax": expr(f"-16*{JOLT}"),
            "head": expr(f"-12*{JOLT}"),
            "abdomen": expr(f"8*{JOLT}"),
            "near_coxa": expr(f"-24*{JOLT}"), "near_hook": expr(f"-40*{JOLT}"),
            "far_coxa": expr(f"-16*{JOLT}"), "far_hook": expr(f"-30*{JOLT}"),
            **legs(f"8*{JOLT}", f"-6*{JOLT}", f"-6*{JOLT}", f"6*{JOLT}"),
            **dead(),
        },
    },
    # The legs splay and give, the body sinks to the ground, and the
    # prothorax topples forward onto its blades.
    "death": {
        "loop": False, "frames": 8, "duration_ms": 110,
        "channels": {
            "root_y": expr(f"48*{ramp(0.0, 0.6)}"),
            "prothorax": expr(f"-8*{ramp(0.0, 0.25)} + 78*{ramp(0.25, 0.8)}"),
            "head": expr(f"6*{ramp(0.25, 0.8)} + 8*{ramp(0.7, 1.0)}"),
            "abdomen": expr(f"-6*{ramp(0.2, 0.7)}"),
            **legs(f"-54*{ramp(0.0, 0.6)}", f"-40*{ramp(0.0, 0.6)}", f"52*{ramp(0.0, 0.6)}", f"40*{ramp(0.0, 0.6)}"),
            # the arms swing forward and fold flat along the ground under it
            "near_coxa": expr(f"-118*{ramp(0.3, 0.8)}"), "near_blade": expr(f"-60*{ramp(0.3, 0.8)}"), "near_hook": expr(f"4*{ramp(0.3, 0.8)}"),
            "far_coxa": expr(f"-112*{ramp(0.3, 0.8)}"), "far_blade": expr(f"-60*{ramp(0.3, 0.8)}"),
            **dead("t >= 0.55"),
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
            entry["opacity_default"] = 1 if channel == "eye_open" else 0
        parts.append(entry)
    return {
        "name": "mantis_lancer",
        "frame": FRAME,
        "svg_source": {"path": "../../../../data/characters/mantis_lancer/mantis_lancer.svg", "view": art.VIEW, "ref_dpi": 25.4, "scale": SCALE},
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
