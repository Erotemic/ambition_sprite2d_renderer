#!/usr/bin/env python3
"""Build Hypatia Prime's rig document (``hypatia_prime``).

    uv run python scripts/svg_art/hypatia_prime_art.py   # the drawing, once
    uv run python scripts/build_hypatia_prime_rig.py

The drawing says where each part turns (``joints`` and ``BONES`` in the art
script). This script makes the skeleton from those joints, binds each part
layer to its bone, and authors the rows. It never draws. A channel is the turn
of a bone from the drawing, in degrees (positive clockwise on the screen: a
hanging limb swings back, the torso leans forward, the staff's top comes
forward).

The rows are the twenty-two she has always had. Her skirt's two panels follow
her legs at half their swing - the front one the forward leg, the back one
the rear - so a knee pushes the cloth rather than the cloth swinging like a
board. Her staff stays upright unless a row turns it (``upright``).
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

_spec = importlib.util.spec_from_file_location("hypatia_prime_art", ROOT / "scripts" / "svg_art" / "hypatia_prime_art.py")
art = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(art)

PKG = ROOT / "ambition_sprite2d_renderer"
OUT = PKG / "targets" / "characters" / "rigged" / "hypatia_prime" / "hypatia_prime.rig.json"

#: Frame pixels for each SVG unit.
SCALE = 0.36
FRAME = {"width": 288, "height": 256, "center_x": 110, "ground_y": 240, "ankle_h": 0, "supersample": 3, "render_scale": 1, "trim": False}

JOLT = "(1-t)*(1-t)"


def expr(text: str) -> dict:
    return {"expr": text}


def ramp(a: float, b: float) -> str:
    """0 to 1 between ``a`` and ``b`` of the row, eased, held after."""
    return f"(lambda u: u*u*(3-2*u))(max(0.0, min(1.0, (t-{a})/{b - a})))"


def legs(near_u: str, far_u: str, near_l: str, far_l: str, skirt: float = 0.5) -> dict:
    """Thigh and shin turns, each foot kept flat, the skirt's panels after
    the forward and the rear leg."""
    return {
        "near_leg_u": expr(near_u), "far_leg_u": expr(far_u),
        "near_leg_l": expr(near_l), "far_leg_l": expr(far_l),
        "near_foot": expr(f"-(({near_u}) + ({near_l}))"),
        "far_foot": expr(f"-(({far_u}) + ({far_l}))"),
        "skirt_f": expr(f"{skirt}*min(({near_u}), ({far_u}))"),
        "skirt_b": expr(f"{skirt}*max(({near_u}), ({far_u}))"),
    }


def lowered(root_y: str, gather: float = 1.3) -> dict:
    """While she is lower than she stands (``root_y`` > 0), her skirt's panels
    gather short instead of sinking into the ground (each is 57 px from hip
    to hem; a turned panel reaches lower, hence ``gather``)."""
    down = f"max(0.0, {root_y})"
    k = f"max(0.35, 1 - {gather}*{down}/57)"
    return {"root_y": expr(root_y), "bone.skirt_f.scale_y": expr(k), "bone.skirt_b.scale_y": expr(k)}


def upright(upper: str, lower: str, lean: str = "0", tilt: str = "0") -> dict:
    """The near arm, the staff kept upright in the world (``lean`` is what
    turns the arm's parents: torso and body), then tilted ``tilt`` (its top
    forward)."""
    return {"near_arm_u": expr(upper), "near_arm_l": expr(lower),
            "near_hand": expr(f"({tilt}) - (({upper}) + ({lower}) + ({lean}))")}


def face(shut: str = "False", dead: str = "False", talk: str = "False") -> dict:
    return {"eye_open": expr(f"0 if ({shut}) or ({dead}) else 1"), "eye_shut": expr(f"1 if ({shut}) and not ({dead}) else 0"),
            "eye_dead": expr(f"1 if ({dead}) else 0"), "mouth_open": expr(f"1 if ({talk}) else 0")}


def far_arm_front(on: str) -> dict:
    """The far arm brought round in front of her (to show the scroll)."""
    z = f"(62 if ({on}) else 0)"
    return {"bone.far_arm_u.z": expr(z), "bone.far_arm_l.z": expr(z), "bone.far_hand.z": expr(z)}


def alternate(a: str, b: str, n: int, on: str) -> dict:
    """Two effect parts shown on alternate frames while ``on`` (a turning)."""
    return {a: expr(f"({on}) * (1 if floor(t*{n} + 0.01) % 2 == 0 else 0)"),
            b: expr(f"({on}) * (0 if floor(t*{n} + 0.01) % 2 == 0 else 1)")}


TALK8 = "floor(t*8 + 0.01) % 2 == 0"
#: Death, frame by frame: how far each pose reached below her soles' line
#: before this lift (measured off the rendered frames; up is negative).
DEATH_LIFT = [0, -5, -8, -7, -16, -17, -3, -3]
# The lance: traced (the conics), then the staff levelled and driven forward.
TRACE = ramp(0.0, 0.3)
THRUST = ramp(0.42, 0.58)
BACK = ramp(0.8, 1.0)

CLIPS = {
    # She stands with the staff, considering; a blink.
    "idle": {
        "loop": True, "frames": 8, "duration_ms": 150,
        "channels": {
            "root_y": expr("0.5*sin(tau*t)"),
            "torso": expr("-0.8*sin(tau*t)"),
            "head": expr("1.2*sin(tau*t+0.5)"),
            "far_arm_u": expr("1.0*sin(tau*t)"),
            **upright("0", "0", "-0.8*sin(tau*t)"),
            **face(shut="0.78 < t < 0.92"),
        },
    },
    "walk": {
        "loop": True, "frames": 8, "duration_ms": 106,
        "channels": {
            # lowest at full stride, where both legs are straight and slanted
            "root_y": expr("4.4*abs(sin(tau*t))"),
            "torso": expr("2 + 1.0*sin(2*tau*t)"),
            "head": expr("-1 - 1.0*sin(2*tau*t)"),
            **legs("-22*sin(tau*t)", "22*sin(tau*t)", "30*max(0.0, cos(tau*t))", "30*max(0.0, -cos(tau*t))"),
            "far_arm_u": expr("-10*sin(tau*t)"),
            **upright("4*sin(tau*t)", "0", "2 + 1.0*sin(2*tau*t)"),
            **face(),
        },
    },
    "run": {
        "loop": True, "frames": 8, "duration_ms": 82,
        "channels": {
            "root_y": expr("7*abs(sin(tau*t)) - 3"),
            "torso": expr("10 + 2*sin(2*tau*t)"),
            "head": expr("-8 - 2*sin(2*tau*t)"),
            **legs("-38*sin(tau*t)", "38*sin(tau*t)", "70*max(0.0, cos(tau*t))", "70*max(0.0, -cos(tau*t))"),
            "far_arm_u": expr("-30*sin(tau*t)"), "far_arm_l": expr("-40"),
            **upright("-14 + 8*sin(tau*t)", "-10", "10 + 2*sin(2*tau*t)", "18"),
            **face(),
        },
    },
    "crouch": {
        "loop": False, "frames": 6, "duration_ms": 96,
        "channels": {
            **lowered(f"30*{ramp(0.0, 0.5)}"),
            "torso": expr(f"14*{ramp(0.0, 0.5)}"),
            "head": expr(f"-12*{ramp(0.0, 0.5)}"),
            **legs(f"-62*{ramp(0.0, 0.5)}", f"-30*{ramp(0.0, 0.5)}", f"112*{ramp(0.0, 0.5)}", f"100*{ramp(0.0, 0.5)}"),
            "far_arm_u": expr(f"-20*{ramp(0.0, 0.5)}"),
            **upright(f"-10*{ramp(0.0, 0.5)}", "0", f"14*{ramp(0.0, 0.5)}", f"8*{ramp(0.0, 0.5)}"),
            "bone.staff.y": expr(f"-30*{ramp(0.0, 0.5)}"),
            **face(),
        },
    },
    # A spring off the ground: knees tucked, the staff lifted.
    "jump": {
        "loop": False, "frames": 6, "duration_ms": 90,
        "channels": {
            **lowered(f"8*(1 - {ramp(0.0, 0.3)}) - 8*{ramp(0.3, 0.6)}"),
            "bone.staff.y": expr(f"-10*(1 - {ramp(0.0, 0.3)})"),
            "torso": expr(f"6*(1 - {ramp(0.0, 0.3)}) - 4*{ramp(0.3, 0.6)}"),
            "head": expr(f"-6*{ramp(0.3, 0.6)}"),
            **legs(f"-20 - 30*{ramp(0.3, 0.7)}", f"-6 - 20*{ramp(0.3, 0.7)}", f"30 + 50*{ramp(0.3, 0.7)}", f"30 + 40*{ramp(0.3, 0.7)}"),
            "far_arm_u": expr(f"-70*{ramp(0.2, 0.6)}"), "far_arm_l": expr(f"-20*{ramp(0.2, 0.6)}"),
            **upright(f"-30*{ramp(0.2, 0.6)}", "0", f"6*(1 - {ramp(0.0, 0.3)}) - 4*{ramp(0.3, 0.6)}"),
            **face(),
        },
    },
    # Falling: legs hang, the skirt and the free arm flutter up.
    "fall": {
        "loop": True, "frames": 6, "duration_ms": 94,
        "channels": {
            "torso": expr("-3"),
            "head": expr("-4 + 2*sin(tau*t)"),
            **legs("-12 + 3*sin(tau*t)", "8 - 3*sin(tau*t)", "24", "34"),
            "skirt_f": expr("-14 + 5*sin(2*tau*t)"), "skirt_b": expr("16 + 5*sin(2*tau*t+1)"),
            "far_arm_u": expr("-110 + 8*sin(tau*t)"), "far_arm_l": expr("-20"),
            **upright("-24", "0", "-3"),
            **face(),
        },
    },
    # A hard landing: she drops into it and rises.
    "land_hard": {
        "loop": False, "frames": 6, "duration_ms": 88,
        "channels": {
            **lowered(f"22*{JOLT}"),
            "torso": expr(f"18*{JOLT}"),
            "head": expr(f"-12*{JOLT}"),
            **legs(f"-46*{JOLT}", f"-24*{JOLT}", f"84*{JOLT}", f"76*{JOLT}"),
            "far_arm_u": expr(f"-40*{JOLT}"),
            **upright(f"-12*{JOLT}", "0", f"18*{JOLT}"),
            "bone.staff.y": expr(f"-22*{JOLT}"),
            **face(shut="t < 0.3"),
        },
    },
    # A burst forward, low, the staff trailing.
    "dash": {
        "loop": False, "frames": 7, "duration_ms": 66,
        "channels": {
            "root_x": expr(f"10*{ramp(0.0, 0.4)} - 10*{ramp(0.75, 1.0)}"),
            "root_y": expr(f"8*{ramp(0.0, 0.3)} - 8*{ramp(0.75, 1.0)}"),
            "torso": expr(f"22*{ramp(0.0, 0.3)} - 22*{ramp(0.75, 1.0)}"),
            "head": expr(f"-16*{ramp(0.0, 0.3)} + 16*{ramp(0.75, 1.0)}"),
            **legs(f"-42*{ramp(0.0, 0.3)} + 42*{ramp(0.75, 1.0)}", f"40*{ramp(0.0, 0.3)} - 40*{ramp(0.75, 1.0)}",
                   f"24*{ramp(0.0, 0.3)} - 24*{ramp(0.75, 1.0)}", f"40*{ramp(0.0, 0.3)} - 40*{ramp(0.75, 1.0)}"),
            "far_arm_u": expr(f"50*{ramp(0.0, 0.3)} - 50*{ramp(0.75, 1.0)}"),
            **upright(f"30*{ramp(0.0, 0.3)} - 30*{ramp(0.75, 1.0)}", "0", f"22*{ramp(0.0, 0.3)} - 22*{ramp(0.75, 1.0)}",
                      f"-40*{ramp(0.0, 0.3)} + 40*{ramp(0.75, 1.0)}"),
            **face(),
        },
    },
    # A forward roll, tucked, the staff held upright through it.
    "roll": {
        "loop": False, "frames": 8, "duration_ms": 66,
        "channels": {
            "root_x": expr(f"18*{ramp(0.0, 1.0)}"),
            # each frame set on the ground: how far the turning, tucked body
            # reaches below (or stops short of) her soles' line, measured
            **lowered(f"18*{ramp(0.0, 0.2)} - 18*{ramp(0.8, 1.0)} + [0, 4, 0, -28, -3, 9, 5, 0][floor(t*7 + 0.5)]"),
            "body": expr(f"360*{ramp(0.1, 0.9)}"),
            "torso": expr(f"20*{ramp(0.0, 0.2)} - 20*{ramp(0.8, 1.0)}"),
            "head": expr(f"20*{ramp(0.0, 0.2)} - 20*{ramp(0.8, 1.0)}"),
            **legs(f"-80*{ramp(0.0, 0.2)} + 80*{ramp(0.8, 1.0)}", f"-70*{ramp(0.0, 0.2)} + 70*{ramp(0.8, 1.0)}",
                   f"120*{ramp(0.0, 0.2)} - 120*{ramp(0.8, 1.0)}", f"120*{ramp(0.0, 0.2)} - 120*{ramp(0.8, 1.0)}", skirt=0.7),
            "far_arm_u": expr(f"-40*{ramp(0.0, 0.2)} + 40*{ramp(0.8, 1.0)}"), "far_arm_l": expr(f"-60*{ramp(0.0, 0.2)} + 60*{ramp(0.8, 1.0)}"),
            **upright(f"-30*{ramp(0.0, 0.2)} + 30*{ramp(0.8, 1.0)}", f"-40*{ramp(0.0, 0.2)} + 40*{ramp(0.8, 1.0)}",
                      f"360*{ramp(0.1, 0.9)} + 20*{ramp(0.0, 0.2)} - 20*{ramp(0.8, 1.0)}"),
            "bone.staff.y": expr("-55*sin(3.14159*t)"),
            **face(shut="0.2 < t < 0.8"),
        },
    },
    # A quick guard: the staff tipped across in front of her.
    "block": {
        "loop": False, "frames": 6, "duration_ms": 82,
        "channels": {
            "root_y": expr(f"6*{ramp(0.0, 0.3)}"),
            "torso": expr(f"-6*{ramp(0.0, 0.3)}"),
            "head": expr(f"4*{ramp(0.0, 0.3)}"),
            **legs(f"-14*{ramp(0.0, 0.3)}", f"14*{ramp(0.0, 0.3)}", f"16*{ramp(0.0, 0.3)}", f"10*{ramp(0.0, 0.3)}"),
            "far_arm_u": expr(f"-40*{ramp(0.0, 0.3)}"), "far_arm_l": expr(f"-50*{ramp(0.0, 0.3)}"),
            **upright(f"-34*{ramp(0.0, 0.3)}", f"-20*{ramp(0.0, 0.3)}", f"-6*{ramp(0.0, 0.3)}", f"34*{ramp(0.0, 0.3)}"),
            "bone.staff.y": expr(f"-14*{ramp(0.0, 0.3)}"),
            **face(),
        },
    },
    "hit": {
        "loop": False, "frames": 5, "duration_ms": 86,
        "channels": {
            "root_x": expr(f"-5*{JOLT}"),
            "torso": expr(f"-14*{JOLT}"),
            "head": expr(f"-12*{JOLT}"),
            "far_arm_u": expr(f"24*{JOLT}"),
            **legs(f"-10*{JOLT}", f"8*{JOLT}", "0", f"6*{JOLT}"),
            **upright(f"-10*{JOLT}", "0", f"-14*{JOLT}"),
            **face(shut="True"),
        },
    },
    # She sinks to her knees and falls forward on her face (the ring on her
    # back stays above her); the lance falls flat on the ground beside her.
    "death": {
        "loop": False, "frames": 8, "duration_ms": 112,
        "channels": {
            **lowered(f"26*{ramp(0.0, 0.4)}*(1 - {ramp(0.45, 0.85)})"),
            # each frame set on the ground: how far that pose reaches below her
            # soles' line, measured (``DEATH_LIFT``)
            "root_y": expr(f"26*{ramp(0.0, 0.4)} + 13*{ramp(0.45, 0.85)} + {DEATH_LIFT}[floor(t*7 + 0.5)]"),
            "root_x": expr(f"6*{ramp(0.45, 0.85)}"),
            "body": expr(f"84*{ramp(0.45, 0.85)}"),
            "torso": expr(f"10*{ramp(0.0, 0.4)} - 4*{ramp(0.45, 0.85)}"),
            "head": expr(f"10*{ramp(0.0, 0.4)} - 4*{ramp(0.45, 0.85)}"),
            **legs(f"-64*{ramp(0.0, 0.4)} + 64*{ramp(0.45, 0.85)}", f"-54*{ramp(0.0, 0.4)} + 54*{ramp(0.45, 0.85)}",
                   f"116*{ramp(0.0, 0.4)} - 116*{ramp(0.45, 0.85)}", f"106*{ramp(0.0, 0.4)} - 106*{ramp(0.45, 0.85)}"),
            # face down, the feet's toes turn back along the ground
            "near_foot": expr(f"-(-64*{ramp(0.0, 0.4)} + 116*{ramp(0.0, 0.4)}) - 70*{ramp(0.45, 0.85)}"),
            "far_foot": expr(f"-(-54*{ramp(0.0, 0.4)} + 106*{ramp(0.0, 0.4)}) - 70*{ramp(0.45, 0.85)}"),
            **upright("0", "0", f"10*{ramp(0.0, 0.4)} - 4*{ramp(0.45, 0.85)} + 84*{ramp(0.45, 0.85)}",
                      f"90*{ramp(0.45, 0.85)}"),
            # kneeling, the lance slides down through her hand to the ground;
            # fallen, it lies flat on the ground beside her (behind her body)
            "bone.staff.y": expr(f"-26*{ramp(0.0, 0.4)}*(1 - {ramp(0.45, 0.85)}) + [0, 4, 4, 3, 0, 0, 0, 0][floor(t*7 + 0.5)]"),
            "bone.staff.x": expr(f"-7*{ramp(0.6, 0.9)}"),
            "bone.staff.z": expr("-60 if t > 0.5 else 0"),
            **face(shut="0.3 < t < 0.7", dead="t >= 0.7"),
        },
    },
    # She explains: a hand marks the points, her head with them.
    "talk": {
        "loop": True, "frames": 8, "duration_ms": 106,
        "channels": {
            "torso": expr("-1 + 1.0*sin(tau*t)"),
            "head": expr("-2 + 3*sin(tau*t)"),
            "far_arm_u": expr("-34 + 10*sin(tau*t)"), "far_arm_l": expr("-50 + 14*sin(tau*t+0.8)"),
            **far_arm_front("True"),
            **upright("0", "0", "-1 + 1.0*sin(tau*t)"),
            **face(talk=TALK8),
        },
    },
    # She holds the scroll out to you.
    "interact": {
        "loop": False, "frames": 8, "duration_ms": 96,
        "channels": {
            "root_x": expr(f"3*{ramp(0.0, 0.4)} - 3*{ramp(0.7, 1.0)}"),
            "torso": expr(f"6*{ramp(0.0, 0.4)} - 6*{ramp(0.7, 1.0)}"),
            "head": expr(f"-4*{ramp(0.0, 0.4)} + 4*{ramp(0.7, 1.0)}"),
            "far_arm_u": expr(f"-74*{ramp(0.0, 0.4)} + 74*{ramp(0.7, 1.0)}"), "far_arm_l": expr(f"-26*{ramp(0.0, 0.4)} + 26*{ramp(0.7, 1.0)}"),
            **far_arm_front("0.1 < t < 0.95"),
            **upright("0", "0", f"6*{ramp(0.0, 0.4)} - 6*{ramp(0.7, 1.0)}"),
            **face(),
        },
    },
    # The astrolabe turned before her, the staff braced.
    "astrolabe_guard": {
        "loop": False, "frames": 8, "duration_ms": 72,
        "channels": {
            "root_y": expr(f"8*{ramp(0.0, 0.25)}"),
            "torso": expr(f"-4*{ramp(0.0, 0.25)}"),
            **legs(f"-18*{ramp(0.0, 0.25)}", f"16*{ramp(0.0, 0.25)}", f"20*{ramp(0.0, 0.25)}", f"14*{ramp(0.0, 0.25)}"),
            "far_arm_u": expr(f"-80*{ramp(0.0, 0.25)}"), "far_arm_l": expr(f"-10*{ramp(0.0, 0.25)}"),
            **far_arm_front("t > 0.05"),
            **upright(f"-30*{ramp(0.0, 0.25)}", f"-24*{ramp(0.0, 0.25)}", f"-4*{ramp(0.0, 0.25)}", f"20*{ramp(0.0, 0.25)}"),
            "bone.staff.y": expr(f"-12*{ramp(0.0, 0.25)}"),
            **alternate("fx_astro_a", "fx_astro_b", 8, f"{ramp(0.0, 0.25)}"),
            **face(),
        },
    },
    # The conics traced with the staff's tip, then the staff levelled and
    # driven forward along the one line they agree on.
    "conic_lance": {
        "loop": False, "frames": 10, "duration_ms": 68,
        "channels": {
            "root_x": expr(f"-3*{TRACE} + 14*{THRUST} - 11*{BACK}"),
            "root_y": expr(f"4*{THRUST} - 4*{BACK}"),
            "torso": expr(f"-6*{TRACE} + 16*{THRUST} - 10*{BACK}"),
            "head": expr(f"4*{TRACE} - 10*{THRUST} + 6*{BACK}"),
            **legs(f"-30*{THRUST} + 30*{BACK}", f"26*{THRUST} - 26*{BACK}", f"20*{THRUST} - 20*{BACK}", f"10*{THRUST} - 10*{BACK}"),
            "far_arm_u": expr(f"30*{THRUST} - 30*{BACK}"),
            **upright(f"-40*{TRACE} - 40*{THRUST} + 80*{BACK}", f"95*{THRUST} - 95*{BACK}",
                      f"-6*{TRACE} + 16*{THRUST} - 10*{BACK}", f"20*{TRACE} + 70*{THRUST} - 90*{BACK}"),
            "fx_conic": expr(f"{ramp(0.05, 0.25)} * (1 - {ramp(0.45, 0.6)})"),
            "fx_lance": expr("1 if 0.5 < t < 0.82 else 0"),
            **face(),
        },
    },
    # Epicycles set turning round her, the staff held high.
    "epicycle_orbit": {
        "loop": False, "frames": 10, "duration_ms": 76,
        "channels": {
            "root_y": expr(f"-2*{ramp(0.0, 0.3)} + 2*{ramp(0.8, 1.0)}"),
            "torso": expr(f"-4*{ramp(0.0, 0.3)} + 4*{ramp(0.8, 1.0)}"),
            "head": expr(f"-8*{ramp(0.0, 0.3)} + 8*{ramp(0.8, 1.0)}"),
            "far_arm_u": expr(f"-60*{ramp(0.0, 0.3)} + 60*{ramp(0.8, 1.0)}"),
            **upright(f"-56*{ramp(0.0, 0.3)} + 56*{ramp(0.8, 1.0)}", f"30*{ramp(0.0, 0.3)} - 30*{ramp(0.8, 1.0)}",
                      f"-4*{ramp(0.0, 0.3)} + 4*{ramp(0.8, 1.0)}"),
            "bone.staff.y": expr(f"20*{ramp(0.0, 0.3)} - 20*{ramp(0.8, 1.0)}"),
            **alternate("fx_orbit_a", "fx_orbit_b", 10, f"{ramp(0.1, 0.3)} * (1 - {ramp(0.85, 1.0)})"),
            **face(),
        },
    },
    # The other reconstructions of her rise behind her and do not settle.
    "library_of_shadows": {
        "loop": False, "frames": 12, "duration_ms": 78,
        "channels": {
            "root_y": expr(f"4*{ramp(0.0, 0.3)} - 4*{ramp(0.8, 1.0)}"),
            "torso": expr(f"-6*{ramp(0.0, 0.3)} + 6*{ramp(0.8, 1.0)}"),
            "head": expr(f"-10*{ramp(0.0, 0.3)} + 10*{ramp(0.8, 1.0)}"),
            "far_arm_u": expr(f"-110*{ramp(0.0, 0.3)} + 110*{ramp(0.8, 1.0)}"), "far_arm_l": expr(f"-10*{ramp(0.0, 0.3)} + 10*{ramp(0.8, 1.0)}"),
            **far_arm_front("0.1 < t < 0.9"),
            **upright(f"-20*{ramp(0.0, 0.3)} + 20*{ramp(0.8, 1.0)}", "0", f"-6*{ramp(0.0, 0.3)} + 6*{ramp(0.8, 1.0)}"),
            "fx_shadows": expr(f"{ramp(0.1, 0.4)} * (1 - {ramp(0.8, 1.0)}) * (0.75 + 0.25*sin(3*tau*t))"),
            **face(shut="0.3 < t < 0.45"),
        },
    },
    # Folios flung from her hand, each with a piece missing.
    "missing_folio": {
        "loop": False, "frames": 10, "duration_ms": 80,
        "channels": {
            "root_x": expr(f"-2*{ramp(0.0, 0.3)} + 6*{ramp(0.3, 0.45)} - 4*{ramp(0.8, 1.0)}"),
            "torso": expr(f"-6*{ramp(0.0, 0.3)} + 14*{ramp(0.3, 0.45)} - 8*{ramp(0.8, 1.0)}"),
            "head": expr(f"4*{ramp(0.0, 0.3)} - 8*{ramp(0.3, 0.45)} + 4*{ramp(0.8, 1.0)}"),
            "far_arm_u": expr(f"30*{ramp(0.0, 0.3)} - 120*{ramp(0.3, 0.45)} + 90*{ramp(0.8, 1.0)}"),
            "far_arm_l": expr(f"-30*{ramp(0.0, 0.3)} + 20*{ramp(0.3, 0.45)} + 10*{ramp(0.8, 1.0)}"),
            **far_arm_front("0.32 < t < 0.9"),
            **legs(f"-16*{ramp(0.3, 0.45)} + 16*{ramp(0.8, 1.0)}", f"14*{ramp(0.3, 0.45)} - 14*{ramp(0.8, 1.0)}", "0", "0"),
            **upright("0", "0", f"-6*{ramp(0.0, 0.3)} + 14*{ramp(0.3, 0.45)} - 8*{ramp(0.8, 1.0)}"),
            "fx_folio_a": expr("1 if 0.35 < t < 0.55 else 0"),
            "fx_folio_b": expr(f"(1 if 0.55 <= t else 0) * (1 - {ramp(0.85, 1.0)})"),
            **face(),
        },
    },
    # The fragments align into one radiant model behind her; the staff raised.
    "prime_revelation": {
        "loop": False, "frames": 12, "duration_ms": 74,
        "channels": {
            "root_y": expr(f"-3*{ramp(0.0, 0.3)} + 3*{ramp(0.85, 1.0)}"),
            "torso": expr(f"-6*{ramp(0.0, 0.3)} + 6*{ramp(0.85, 1.0)}"),
            "head": expr(f"-12*{ramp(0.0, 0.3)} + 12*{ramp(0.85, 1.0)}"),
            "far_arm_u": expr(f"-40*{ramp(0.0, 0.3)} + 40*{ramp(0.85, 1.0)}"), "far_arm_l": expr(f"-30*{ramp(0.0, 0.3)} + 30*{ramp(0.85, 1.0)}"),
            **upright(f"-110*{ramp(0.0, 0.3)} + 110*{ramp(0.85, 1.0)}", f"80*{ramp(0.0, 0.3)} - 80*{ramp(0.85, 1.0)}",
                      f"-6*{ramp(0.0, 0.3)} + 6*{ramp(0.85, 1.0)}"),
            "fx_reveal": expr(f"{ramp(0.15, 0.45)} * (1 - {ramp(0.85, 1.0)})"),
            **face(shut="0.45 < t < 0.6"),
        },
    },
    "celebrate": {
        "loop": True, "frames": 8, "duration_ms": 92,
        "channels": {
            "root_y": expr("-4*abs(sin(tau*t))"),
            "torso": expr("-4 + 2*sin(tau*t)"),
            "head": expr("-10 + 2*sin(tau*t)"),
            "far_arm_u": expr("-120 + 10*abs(sin(tau*t))"), "far_arm_l": expr("-20"),
            **upright("-110 + 10*abs(sin(tau*t))", "80", "-4 + 2*sin(tau*t)"),
            "bone.staff.y": expr("-6*abs(sin(tau*t))"),
            **face(talk="True"),
        },
    },
    # She reads you a correction off her scroll.
    "taunt": {
        "loop": True, "frames": 8, "duration_ms": 98,
        "channels": {
            "torso": expr("-3 + 1.0*sin(tau*t)"),
            "head": expr("6 + 2*sin(tau*t)"),
            "far_arm_u": expr("-60"), "far_arm_l": expr("-56 + 6*sin(2*tau*t)"),
            **far_arm_front("True"),
            **upright("0", "0", "-3 + 1.0*sin(tau*t)"),
            **face(talk=TALK8),
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
    for group, _label, part, bone, z, channel in art.layers():
        x, y = joints[art.BONES[bone][1]]
        entry = {"name": part, "bone": bone, "z": z, "kind": "sprite", "include": [group], "pivot": [x, y], "rest_angle": 0}
        if channel:
            entry["opacity_channel"] = channel
            entry["opacity_default"] = 1 if channel == "eye_open" else 0
        parts.append(entry)
    return {
        "name": "hypatia_prime",
        "frame": FRAME,
        "svg_source": {"path": "../../../../data/characters/hypatia_prime/hypatia_prime.svg", "view": art.VIEW, "ref_dpi": 25.4,
                       "scale": SCALE},
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
