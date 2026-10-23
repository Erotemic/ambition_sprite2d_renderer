#!/usr/bin/env python3
"""Build Paul Diracula's rig document (``paul_diracula_v2``).

    uv run python scripts/svg_art/paul_diracula_art.py      # the drawing (look A, side view)
    uv run python scripts/build_paul_diracula_v2_rig.py

The drawing says where each part turns (``s_joints`` and ``side_layers`` in
the art script). This script makes the skeleton from those joints, binds each
part layer to its bone, and authors the rows. It never draws. It writes the rig catalog into the SVG. A channel is the
turn of a bone from the drawing, in degrees (positive clockwise on the screen:
a hanging limb swings back, the torso leans forward). The cape hangs from its
own bone at the shoulders, so it can flare behind him and close in front of
him.

He is "unnervingly still": the idle hardly moves, and the moves are short and
exact. The rows:

- ``idle``, ``walk``, ``run``, ``jump``, ``fall``: his body and the cape.
- ``talk`` (his mouth, one hand marks the words), ``interact`` (he reaches).
- ``slash``: the gloved hand comes from high behind him and rakes down and
  forward, the cape flaring behind.
- ``attack_side``: the delta spike, one straight thrust of the arm.
- ``special``: pair creation, the two hands thrown apart, one each way.
- ``block``: he closes the cape across his body, the arm raised in it.
- ``hit``, ``death`` (to his knees, then he bows into the cape).

Each grounded frame is moved up or down so that the lowest sole or knee is on
the ground line (``_ground``).
"""

from __future__ import annotations

import copy
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Callable, Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument  # noqa: E402
from ambition_sprite2d_renderer.devtools.svg_rig_tool import install_catalog  # noqa: E402

_spec = importlib.util.spec_from_file_location("paul_diracula_art", ROOT / "scripts" / "svg_art" / "paul_diracula_art.py")
art = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(art)

NAME = art.CAST_NAME
PKG = ROOT / "ambition_sprite2d_renderer"
OUT = PKG / "targets" / "characters" / "rigged" / NAME / f"{NAME}_side.rig.json"

#: Frame pixels for each SVG unit: he stands about 144 px in the frame.
SCALE = 0.4
FRAME = {"width": 224, "height": 200, "center_x": 100, "ground_y": 192, "ankle_h": 0, "supersample": 3, "render_scale": 1, "trim": False}
#: The sole is this far under the ankle, the heel behind it and the toe ahead (SVG units).
SOLE_DY, HEEL_DX, TOE_DX = 14.0, -10.0, 32.0
#: A knee on the ground: the trouser round the knee (SVG units).
KNEE_R = 10.0

TAU = math.tau
Pose = Dict[str, float]


def ease(u: float) -> float:
    u = max(0.0, min(1.0, u))
    return u * u * (3.0 - 2.0 * u)


def ramp(t: float, a: float, b: float) -> float:
    """0 before ``a``, 1 after ``b``, eased between."""
    return ease((t - a) / (b - a))


def legs(nu: float, nl: float, fu: float, fl: float, body: float = 0.0) -> Pose:
    """Thigh and shin turns; each shoe kept flat on the ground."""
    return {"near_leg_u": nu, "near_leg_l": nl, "far_leg_u": fu, "far_leg_l": fl,
            "near_foot": -(nu + nl + body), "far_foot": -(fu + fl + body)}


def face(shut: bool = False, talk: bool = False) -> Pose:
    return {"eye_open": 0.0 if shut else 1.0, "eye_shut": 1.0 if shut else 0.0,
            "mouth_open": 1.0 if talk else 0.0, "mouth_shut": 0.0 if talk else 1.0}


# ---- the rows ----------------------------------------------------------------------------

def idle(i: int, n: int) -> Pose:
    """Still, upright, the hands at his sides; he breathes, the cape stirs, he blinks once."""
    ph = TAU * i / n
    return {"torso": 0.5 * math.sin(ph), "head": -0.6 * math.sin(ph + 0.6), "cape": 1.2 * math.sin(ph + 1.2),
            "near_arm_u": 0.8 * math.sin(ph), "far_arm_u": -0.6 * math.sin(ph), **legs(0, 0, 0, 0), **face(shut=i == 5)}


def walk(i: int, n: int) -> Pose:
    """A measured walk, upright; the arms swing a little; the cape trails."""
    ph = TAU * i / n
    s, c = math.sin(ph), math.cos(ph)
    return {"torso": 2.0 + 0.8 * math.sin(2 * ph), "head": -1.5 - 0.8 * math.sin(2 * ph), "cape": 5.0 + 2.5 * math.sin(2 * ph + 0.7),
            "near_arm_u": 12 * s, "near_arm_l": -6 - 4 * max(0.0, -s), "far_arm_u": -12 * s, "far_arm_l": -6 - 4 * max(0.0, s),
            **legs(-24 * s, 30 * max(0.0, c), 24 * s, 30 * max(0.0, -c)), **face()}


def run(i: int, n: int) -> Pose:
    """A long low run, leaning in, the elbows bent and the cape streaming behind."""
    ph = TAU * i / n
    s, c = math.sin(ph), math.cos(ph)
    return {"body": 0.0, "torso": 11.0 + 1.5 * math.sin(2 * ph), "head": -9.0, "cape": 22.0 + 6.0 * math.sin(2 * ph + 0.9),
            "near_arm_u": 32 * s, "near_arm_l": -55 - 10 * s, "far_arm_u": -32 * s, "far_arm_l": -55 + 10 * s,
            **legs(-40 * s, 15 + 60 * max(0.0, c), 40 * s, 15 + 60 * max(0.0, -c)), **face()}


def jump(i: int, n: int) -> Pose:
    """He gathers and leaves the ground: the knees come up, the cape lifts."""
    u = ease(i / (n - 1))
    return {"torso": 4 * u, "head": -4 * u, "cape": 10 + 22 * u,
            "near_arm_u": -24 * u, "near_arm_l": -30 * u, "far_arm_u": 18 * u, "far_arm_l": -20 * u,
            **legs(-46 * u, 70 * u, -18 * u, 50 * u), **face(), "root_y": -6 * u}


def fall(i: int, n: int) -> Pose:
    """Coming down, the arms a little out, the cape billowing up behind him."""
    ph = TAU * i / n
    return {"torso": -2.0, "head": 3.0, "cape": 38 + 4 * math.sin(ph),
            "near_arm_u": -32 + 3 * math.sin(ph), "near_arm_l": -14, "far_arm_u": 30 - 3 * math.sin(ph), "far_arm_l": -12,
            **legs(-16, 26, 10, 18), **face(), "root_y": -6.0}


def talk(i: int, n: int) -> Pose:
    """He speaks rarely and exactly: the near hand lifts to mark the word, the head nods once."""
    ph = TAU * i / n
    return {"torso": 1.0, "head": 2.0 * math.sin(ph), "cape": 0.8 * math.sin(ph),
            "near_arm_u": -22 + 3 * math.sin(ph), "near_arm_l": -62 + 8 * math.sin(ph + 0.8), "near_hand": -10.0,
            **legs(0, 0, 0, 0), **face(talk=i % 2 == 0)}


def interact(i: int, n: int) -> Pose:
    """He reaches out with one long hand, and draws it back."""
    t = i / (n - 1)
    u = ramp(t, 0.0, 0.4) - ramp(t, 0.7, 1.0)
    return {"torso": 8 * u, "head": 4 * u, "cape": 3 * u,
            "near_arm_u": -72 * u, "near_arm_l": -8 * u, "near_hand": -8 * u, **legs(-10 * u, 8 * u, 6 * u, 0), **face()}


def slash(i: int, n: int) -> Pose:
    """The gloved hand comes up behind him, then rakes down and forward past
    his body (the swing is live at about a third of the row); the cape flares
    behind him; he steps into it."""
    t = i / (n - 1)
    wind = ramp(t, 0.0, 0.3)
    strike = ramp(t, 0.3, 0.55)
    back = ramp(t, 0.75, 1.0)
    # up behind (+150), on round to forward and down (+310 = -50), and on
    # down to his side (+360 = 0): the arm never turns back through the swing
    arm = 150 * wind + 160 * strike + 50 * back
    k = 1 - back
    return {"torso": (-6 * wind + 20 * strike) * k, "head": (4 * wind - 10 * strike) * k,
            "cape": (12 * wind + 34 * strike) * k,
            "near_arm_u": arm, "near_arm_l": (-30 * wind + 26 * strike) * k, "near_hand": (-20 * wind + 30 * strike) * k,
            "far_arm_u": (-10 * wind + 30 * strike) * k, "far_arm_l": -20 * strike * k,
            **legs((-4 * wind - 26 * strike) * k, (8 * wind + 20 * strike) * k, (6 * wind + 16 * strike) * k, 6 * strike * k),
            "root_x": 7 * strike * k, **face()}


def attack_side(i: int, n: int) -> Pose:
    """The delta spike: nothing, then all of it at one point -- one straight
    thrust of the arm, held a moment, withdrawn."""
    t = i / (n - 1)
    u = ramp(t, 0.15, 0.35) - ramp(t, 0.7, 1.0)
    return {"torso": 12 * u, "head": -6 * u, "cape": 16 * u,
            "near_arm_u": -86 * u, "near_arm_l": 4 * u, "near_hand": -6 * u, "far_arm_u": 18 * u, "far_arm_l": -18 * u,
            **legs(-24 * u, 14 * u, 14 * u, 4 * u), "root_x": 8 * u, **face()}


def special(i: int, n: int) -> Pose:
    """Pair creation: the hands come together before him, then are thrown
    apart, one forward and one back; the cape opens."""
    t = i / (n - 1)
    gather = ramp(t, 0.0, 0.35)
    throw = ramp(t, 0.35, 0.55)
    back = ramp(t, 0.8, 1.0)
    k = 1 - back
    return {"torso": (6 * gather - 6 * throw) * k, "head": (6 * gather - 8 * throw) * k, "cape": (-8 * gather + 30 * throw) * k,
            "near_arm_u": (-50 * gather - 36 * throw) * k, "near_arm_l": (-50 * gather + 50 * throw) * k, "near_hand": (-10 * gather) * k,
            "far_arm_u": (-50 * gather + 150 * throw) * k, "far_arm_l": (-50 * gather + 46 * throw) * k,
            **legs(-12 * throw * k, 8 * throw * k, 10 * throw * k, 0), **face()}


def block(i: int, n: int) -> Pose:
    """He closes the cape across himself, the near arm raised inside it."""
    t = i / (n - 1)
    u = ramp(t, 0.0, 0.5)
    return {"torso": -4 * u, "head": 6 * u, "cape": -38 * u,
            "near_arm_u": -100 * u, "near_arm_l": -34 * u, "near_hand": -10 * u, "far_arm_u": -20 * u, "far_arm_l": -40 * u,
            **legs(-8 * u, 10 * u, 8 * u, 4 * u), **face()}


def hit(i: int, n: int) -> Pose:
    """Struck: he rocks back stiffly, the eye shut, and recovers."""
    t = i / (n - 1)
    u = ramp(t, 0.0, 0.25) * (1 - ramp(t, 0.5, 1.0))
    # the cape hangs from the torso: it turns back with it, so that it still hangs
    return {"torso": -14 * u, "head": -12 * u, "cape": 12 * u,
            "near_arm_u": -26 * u, "near_arm_l": -20 * u, "far_arm_u": -16 * u, "far_arm_l": -20 * u,
            **legs(10 * u, 6 * u, -6 * u, 4 * u), "root_x": -6 * u, **face(shut=u > 0.4)}


def death(i: int, n: int) -> Pose:
    """The knees give; he goes down on them, and bows forward into his cape."""
    t = i / (n - 1)
    knees = ramp(t, 0.0, 0.45)
    bow = ramp(t, 0.35, 0.9)
    # the cape is rigid: it is turned back as he sinks, so that its hem stays
    # on the ground behind him and does not go into it
    return {"torso": 8 * knees + 62 * bow, "head": 6 * knees + 16 * bow, "cape": 40 * knees - 42 * bow,
            "near_arm_u": -10 * knees + 20 * bow, "near_arm_l": -14 * knees - 30 * bow, "far_arm_u": -6 * knees + 24 * bow, "far_arm_l": -20 * bow,
            "near_leg_u": -70 * knees, "near_leg_l": 120 * knees, "near_foot": -50 * knees,
            "far_leg_u": -62 * knees, "far_leg_l": 118 * knees, "far_foot": -56 * knees,
            "root_x": -12 * knees, **face(shut=t > 0.5)}


#: Each row: (pose of frame i of n, frames, ms per frame, loops, grounded).
ROWS: Dict[str, tuple] = {
    "idle": (idle, 8, 160, True, True),
    "walk": (walk, 8, 105, True, True),
    "run": (run, 8, 76, True, True),
    "jump": (jump, 4, 90, False, False),
    "fall": (fall, 4, 110, True, False),
    "talk": (talk, 6, 115, True, True),
    "interact": (interact, 6, 95, False, True),
    "slash": (slash, 8, 55, False, True),
    "attack_side": (attack_side, 6, 55, False, True),
    "special": (special, 8, 70, False, True),
    "block": (block, 6, 70, False, True),
    "hit": (hit, 5, 80, False, True),
    "death": (death, 8, 110, False, True),
}

#: The channels every frame states (a frame that leaves one out is at 0).
CHANNELS = ("root_x", "root_y", "body", "torso", "head", "cape", "near_arm_u", "near_arm_l", "near_hand", "far_arm_u", "far_arm_l", "far_hand",
            "near_leg_u", "near_leg_l", "near_foot", "far_leg_u", "far_leg_l", "far_foot",
            "eye_open", "eye_shut", "mouth_open", "mouth_shut")


def clip(make: Callable[[int, int], Pose], n: int, ms: int, loop: bool) -> dict:
    """A clip with one key for each frame, at the time of that frame."""
    frames = [make(i, n) for i in range(n)]
    channels = {}
    for name in CHANNELS:
        keys = []
        for i, pose in enumerate(frames):
            t = i / n if loop else i / max(1, n - 1)
            keys.append([round(t, 6), round(float(pose.get(name, 0.0)), 3), "linear"])
        channels[name] = {"keys": keys}
    return {"loop": loop, "frames": n, "duration_ms": ms, "channels": channels}


# ---- the document ------------------------------------------------------------------------

def skeleton() -> List[dict]:
    joints = art.s_joints()
    _root, cx, cy = joints["body"]
    bones = []
    for name, (parent, x, y) in joints.items():
        if parent:
            _pp, px, py = joints[parent]
            offset = [round((x - px) * SCALE, 4), round((y - py) * SCALE, 4)]
        else:
            offset = [round((x - cx) * SCALE, 4), round((y - art.GROUND_Y) * SCALE, 4)]
        bones.append({"name": name, "parent": parent or None, "offset": offset, "length": 0, "rest_angle": 0})
    return bones


def parts() -> List[dict]:
    art.use(art.CAST_LOOK)
    joints = art.s_joints()
    out = []
    for group, _label, name, bone, z, painter, *channel in art.side_layers():
        if not painter():  # a part the look does not wear (the Inverness capelet, the pins)
            continue
        _parent, x, y = joints[bone]
        entry = {"name": name, "bone": bone, "z": z, "kind": "sprite", "include": [group], "pivot": [x, y], "rest_angle": 0}
        if channel:
            entry["opacity_channel"] = channel[0]
            entry["opacity_default"] = 1 if channel[0] in art.DEFAULT_ON else 0
        out.append(entry)
    return out


def _ground(doc: dict) -> None:
    """Move each grounded frame so its lowest sole or knee is on the ground line."""
    rig = RigDocument(copy.deepcopy(doc), source_path=OUT)
    gy = float(doc["frame"]["ground_y"])
    for row, (_make, n, _ms, _loop, grounded) in ROWS.items():
        if not grounded:
            continue
        keys = doc["clips"][row]["channels"]["root_y"]["keys"]
        for i in range(n):
            world, _s = rig.solve(row, rig.frame_time(row, i, n))
            low = -1e9
            for side in ("near", "far"):
                foot = world[f"{side}_foot"]
                for dx in (HEEL_DX, TOE_DX):
                    low = max(low, foot.to_world((dx * SCALE, SOLE_DY * SCALE))[1])
                low = max(low, world[f"{side}_leg_l"].origin[1] + KNEE_R * SCALE)
            keys[i][1] = round(keys[i][1] + gy - low, 3)
        rig = RigDocument(copy.deepcopy(doc), source_path=OUT)


def build() -> dict:
    doc = {
        "name": NAME,
        "frame": FRAME,
        "svg_source": {"path": f"../../../../data/characters/{NAME}/{NAME}_side.svg", "view": art.CAST_VIEW, "ref_dpi": 25.4, "scale": SCALE},
        "sprite_tuning": {"collision_scale": 1.0, "frame_sample_inset": 1},
        "palette": {},
        "bones": skeleton(),
        "parts": parts(),
        "ik_legs": [],
        "ik_chains": [],
        "clips": {row: clip(make, n, ms, loop) for row, (make, n, ms, loop, _g) in ROWS.items()},
    }
    _ground(doc)
    return doc


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = build()
    tmp = OUT.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf8")
    tmp.replace(OUT)
    print(f"wrote {OUT.relative_to(ROOT)}")
    # The rig catalog in the SVG, from this rig document only: a repo-wide
    # install would also write the SVGs of other characters.
    svg_path = OUT.parent / doc["svg_source"]["path"]
    if install_catalog(svg_path, [OUT]):
        print(f"catalog {svg_path.resolve().relative_to(ROOT)}")


if __name__ == "__main__":
    main()
