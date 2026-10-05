#!/usr/bin/env python3
"""Build the T-rex boss's rig document from its SVG.

The SVG ``data/characters/trex_enemy/trex_enemy.svg`` owns the art and says
where every joint is: each part layer names its ``data-rig-part``,
``data-rig-bone`` and ``data-rig-z`` (and, for the eye states,
``data-rig-opacity``), and the hidden ``Rig Joints`` layer holds one circle per
joint. This builder derives the skeleton from those joints, binds every part
to its bone at its rest pose, and authors the clips. It never draws.

    uv run python scripts/build_trex_enemy_rig.py

The clips keep the sheet contract the game already reads: the same nine rows,
frame counts and durations as before the SVG redesign.
"""

from __future__ import annotations

import json
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Callable, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "ambition_sprite2d_renderer"
SVG_PATH = PKG / "data" / "characters" / "trex_enemy" / "trex_enemy.svg"
RIG_PATH = PKG / "targets" / "characters" / "rigged" / "trex_enemy" / "trex_enemy_side.rig.json"
VIEW_LABEL = "T-Rex - Side Right"

SVG_NS = "http://www.w3.org/2000/svg"
INK_NS = "http://www.inkscape.org/namespaces/inkscape"

#: Sprite pixels per SVG unit. The art is drawn roomy (640x400 units); the
#: sprite keeps the on-screen size the T-rex had before the SVG redesign.
SCALE = 0.75
SVG_CENTER_X = 270.0
SVG_GROUND_Y = 372.0
FRAME_W, FRAME_H = 480, 300
CENTER_X = SVG_CENTER_X * SCALE
GROUND_Y = SVG_GROUND_Y * SCALE
SUPERSAMPLE = 4
#: Clip channels that are distances. The clips are authored in SVG units and
#: scaled with the art; angles and strengths are not.
DISTANCE_CHANNELS = {"root_x", "root_y", "near_foot_x", "near_foot_lift", "far_foot_x", "far_foot_lift"}

#: name, frames, ms, loop. The game binds these rows by name.
ROWS: List[Tuple[str, int, int, bool]] = [
    ("idle", 6, 120, True),
    ("walk", 8, 90, True),
    ("charge", 8, 76, True),
    ("bite", 7, 78, False),
    ("roar", 6, 104, False),
    ("tail_swipe", 7, 82, False),
    ("stomp", 6, 92, False),
    ("hurt", 4, 90, False),
    ("death", 8, 110, False),
]

Point = Tuple[float, float]


# --- the SVG ------------------------------------------------------------------


def read_svg() -> Tuple[Dict[str, Point], List[dict]]:
    """Joints (in SVG units) and the part layers."""
    root = ET.parse(SVG_PATH).getroot()
    joints: Dict[str, Point] = {}
    for circle in root.iter(f"{{{SVG_NS}}}circle"):
        name = circle.get("data-joint")
        if name:
            joints[name] = (float(circle.get("cx")), float(circle.get("cy")))
    parts = []
    for group in root.iter(f"{{{SVG_NS}}}g"):
        name = group.get("data-rig-part")
        if not name:
            continue
        parts.append(
            {
                "name": name,
                "id": group.get("id"),
                "bone": group.get("data-rig-bone"),
                "z": float(group.get("data-rig-z", "0")),
                "opacity": group.get("data-rig-opacity"),
                "default": group.get("data-rig-default"),
            }
        )
    return joints, parts


# --- the skeleton ---------------------------------------------------------------


def heading(a: Point, b: Point) -> float:
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


def rotate(p: Point, deg: float) -> Point:
    r = math.radians(deg)
    return (p[0] * math.cos(r) - p[1] * math.sin(r), p[0] * math.sin(r) + p[1] * math.cos(r))


def dist(a: Point, b: Point) -> float:
    return math.hypot(b[0] - a[0], b[1] - a[1])


def build_bones(J: Dict[str, Point]):
    """Bones as (name, parent, world origin, world angle, length) in sprite
    pixels (``J`` already scaled); the rest pose IS the drawing."""
    spec: List[Tuple[str, str | None, Point, float, float]] = []
    world: Dict[str, Tuple[Point, float]] = {}

    def add(name, parent, origin, angle, length):
        spec.append((name, parent, origin, angle, length))
        world[name] = (origin, angle)

    add("pelvis", None, J["pelvis"], 0.0, 0.0)
    add("torso", "pelvis", J["pelvis"], heading(J["pelvis"], J["neck_base"]), dist(J["pelvis"], J["neck_base"]))
    add("neck", "torso", J["neck_base"], heading(J["neck_base"], J["head"]), dist(J["neck_base"], J["head"]))
    add("head", "neck", J["head"], heading(J["head"], J["snout"]), dist(J["head"], J["snout"]))
    add("jaw", "head", J["jaw"], heading(J["head"], J["snout"]), 80.0)
    tail = ["tail0", "tail1", "tail2", "tail3", "tail_tip"]
    parent = "pelvis"
    for i in range(4):
        name = f"tail{i + 1}"
        add(name, parent, J[tail[i]], heading(J[tail[i]], J[tail[i + 1]]), dist(J[tail[i]], J[tail[i + 1]]))
        parent = name
    for side in ("far", "near"):
        hip, knee, ankle = J[f"{side}_hip"], J[f"{side}_knee"], J[f"{side}_ankle"]
        add(f"{side}_thigh", "pelvis", hip, heading(hip, knee), dist(hip, knee))
        add(f"{side}_shin", f"{side}_thigh", knee, heading(knee, ankle), dist(knee, ankle))
        add(f"{side}_foot", f"{side}_shin", ankle, 0.0, 0.0)
        sh, el, wr = J[f"{side}_shoulder"], J[f"{side}_elbow"], J[f"{side}_wrist"]
        add(f"{side}_arm_u", "torso", sh, heading(sh, el), dist(sh, el))
        add(f"{side}_arm_l", f"{side}_arm_u", el, heading(el, wr), dist(el, wr))

    bones = []
    for name, par, origin, angle, length in spec:
        if par is None:
            offset = (origin[0] - CENTER_X, origin[1] - GROUND_Y)
            rest = angle
        else:
            p_origin, p_angle = world[par]
            offset = rotate((origin[0] - p_origin[0], origin[1] - p_origin[1]), -p_angle)
            rest = (angle - p_angle + 180.0) % 360.0 - 180.0
        bones.append(
            {
                "name": name,
                "parent": par,
                "offset": [round(offset[0], 4), round(offset[1], 4)],
                "length": round(length, 4),
                "rest_angle": round(rest, 4),
            }
        )
    return bones, world


# --- clips ---------------------------------------------------------------------

Pose = Dict[str, float]


def smooth01(x: float) -> float:
    x = max(0.0, min(1.0, x))
    return x * x * (3.0 - 2.0 * x)


def pulse(x: float) -> float:
    return math.sin(math.pi * max(0.0, min(1.0, x)))


def track(keys: List[float], t: float) -> float:
    """``keys`` evenly spread over [0, 1], eased between."""
    n = len(keys) - 1
    x = max(0.0, min(1.0, t)) * n
    i = min(n - 1, int(x))
    return keys[i] + (keys[i + 1] - keys[i]) * smooth01(x - i)


def step(phase: float, centre: float, stride: float, lift: float) -> Tuple[float, float, float]:
    """A planted-then-swinging foot: ``(x, lift, pitch)`` at gait ``phase``.
    The first half is stance (the foot slides back under the walking body);
    the second half is the swing forward."""
    p = phase % 1.0
    if p < 0.5:
        return centre + stride * (1.0 - 4.0 * p), 0.0, 0.0
    s = (p - 0.5) / 0.5
    h = lift * pulse(s)
    return centre - stride + 2.0 * stride * smooth01(s), h, 0.45 * h


#: Where each foot plants, from the drawing's centre (SVG units).
NEAR_X = 2.0
FAR_X = -14.0


def gait(t: float, *, stride: float, lift: float, bob: float, sway: float, tail: float) -> Pose:
    p: Pose = {}
    nx, nl, npitch = step(t, NEAR_X, stride, lift)
    fx, fl, fpitch = step(t + 0.5, FAR_X, stride, lift)
    p.update(near_foot_x=nx, near_foot_lift=nl, near_foot_pitch=npitch,
             far_foot_x=fx, far_foot_lift=fl, far_foot_pitch=fpitch)
    w = math.tau * t
    # Highest at mid-stance, lowest as each foot lands.
    p["root_y"] = bob * (0.5 - abs(math.sin(w)))
    p["pelvis"] = sway * math.sin(w)
    p["torso"] = -0.4 * sway * math.sin(w)
    p["neck"] = -1.2 * sway * math.sin(w + 0.6)
    p["head"] = 0.8 * sway * math.sin(w + 1.2)
    for i in range(4):
        p[f"tail{i + 1}"] = tail * math.sin(w - 0.7 * (i + 1)) * (0.6 + 0.25 * i)
    p["near_arm_u"] = 6.0 * math.sin(w)
    p["near_arm_l"] = 6.0 * math.sin(w - 0.8)
    p["far_arm_u"] = -6.0 * math.sin(w)
    p["far_arm_l"] = -6.0 * math.sin(w - 0.8)
    return p


def eyes(state: str) -> Pose:
    return {"eye.open": 1.0 if state == "open" else 0.0, "eye.angry": 1.0 if state == "angry" else 0.0,
            "eye.shut": 1.0 if state == "shut" else 0.0, "eye.dead": 1.0 if state == "dead" else 0.0}


def idle(i: int, n: int, t: float) -> Pose:
    w = math.tau * t
    breath = math.sin(w)
    p: Pose = {
        "root_y": 1.6 * breath,
        "pelvis": -0.6 * breath,
        "torso": 0.8 * breath,
        "neck": -1.8 * math.sin(w - 0.5),
        "head": 1.4 * math.sin(w - 1.0),
        "jaw": 3.0 + 3.0 * max(0.0, math.sin(w - 0.4)),
        "near_arm_u": 4.0 * math.sin(w - 0.3),
        "near_arm_l": 5.0 * math.sin(w - 0.9),
        "far_arm_u": 3.0 * math.sin(w - 0.6),
        "far_arm_l": 4.0 * math.sin(w - 1.2),
    }
    for k in range(4):
        p[f"tail{k + 1}"] = (1.5 + 0.8 * k) * math.sin(w - 0.6 * (k + 1))
    p.update(eyes("shut" if i == n - 1 else "open"))
    return p


def walk(i: int, n: int, t: float) -> Pose:
    p = gait(t, stride=24.0, lift=18.0, bob=4.0, sway=1.6, tail=4.0)
    p["jaw"] = 3.0
    p.update(eyes("open"))
    return p


def charge(i: int, n: int, t: float) -> Pose:
    p = gait(t, stride=36.0, lift=26.0, bob=7.0, sway=2.4, tail=6.0)
    w = math.tau * t
    p["root_x"] = 10.0
    p["root_y"] += 4.0
    p["pelvis"] += 9.0
    p["torso"] += 2.0
    p["neck"] += 12.0
    p["head"] += -8.0 + 2.0 * math.sin(w)
    p["jaw"] = 10.0 + 6.0 * max(0.0, math.sin(w * 2.0))
    for k in range(4):
        p[f"tail{k + 1}"] -= 2.0 + k
    p["near_arm_u"] -= 18.0
    p["far_arm_u"] -= 18.0
    # Dust kicks up as each foot strikes (twice a cycle).
    p["fx.dust"] = 0.35 + 0.65 * abs(math.cos(w))
    p.update(eyes("angry"))
    return p


def bite(i: int, n: int, t: float) -> Pose:
    p: Pose = {
        "root_x": track([0, -12, 18, 28, 16, 6, 0], t),
        "root_y": track([0, -2, 4, 6, 3, 1, 0], t),
        "pelvis": track([0, -6, 8, 11, 6, 2, 0], t),
        "torso": track([0, -2, 3, 4, 2, 0, 0], t),
        "neck": track([0, -18, 10, 16, 8, 2, 0], t),
        "head": track([0, -10, 2, 2, 1, 0, 0], t),
        "jaw": track([3, 28, 40, 2, 8, 5, 3], t),
        "near_foot_x": track([NEAR_X, 10, 24, 24, 24, 12, NEAR_X], t),
        "near_foot_lift": track([0, 12, 0, 0, 0, 8, 0], t),
        "tail1": track([0, 6, -6, -4, -2, 0, 0], t),
        "tail2": track([0, 8, -8, -6, -2, 0, 0], t),
        "tail3": track([0, 10, -10, -8, -3, 0, 0], t),
        "tail4": track([0, 12, -14, -10, -4, 0, 0], t),
        "near_arm_u": track([0, -14, -26, -20, -10, -4, 0], t),
        "far_arm_u": track([0, -12, -24, -18, -8, -2, 0], t),
        "fx.bite": track([0, 0, 0.35, 1, 0.3, 0, 0], t),
    }
    p.update(eyes("angry" if 0.1 < t < 0.9 else "open"))
    return p


def roar(i: int, n: int, t: float) -> Pose:
    shake = (1.0 if i % 2 else -1.0) * (1.5 if i in (2, 3, 4) else 0.0)
    p: Pose = {
        "root_x": track([0, -8, 4, 6, 4, 0], t) + shake,
        "root_y": track([0, -3, 4, 5, 3, 0], t),
        "pelvis": track([0, -8, 5, 6, 4, 0], t),
        "torso": track([0, -3, 2, 3, 2, 0], t),
        "neck": track([0, -20, 4, 6, 2, 0], t),
        "head": track([0, -10, -10, -10, -6, 0], t),
        "jaw": track([3, 12, 40, 42, 34, 4], t),
        "tail1": track([0, -6, 6, 7, 4, 0], t),
        "tail2": track([0, -6, 8, 9, 5, 0], t),
        "tail3": track([0, -6, 10, 11, 6, 0], t),
        "tail4": track([0, -6, 12, 14, 8, 0], t),
        "near_arm_u": track([0, -20, -34, -36, -24, 0], t),
        "near_arm_l": track([0, -10, -20, -22, -12, 0], t),
        "far_arm_u": track([0, -18, -30, -32, -20, 0], t),
        "far_arm_l": track([0, -8, -18, -20, -10, 0], t),
        "near_foot_x": NEAR_X + 4.0,
        "fx.roar": track([0, 0, 0.75, 1, 0.8, 0], t),
    }
    p.update(eyes("angry" if 0.1 < t < 0.95 else "open"))
    return p


def tail_swipe(i: int, n: int, t: float) -> Pose:
    p: Pose = {
        "root_x": track([0, 8, 2, -12, -12, -5, 0], t),
        "root_y": track([0, 2, 4, 3, 2, 1, 0], t),
        "pelvis": track([0, 9, 4, -7, -6, -2, 0], t),
        "torso": track([0, 2, 1, -2, -2, 0, 0], t),
        "neck": track([0, 10, 6, -8, -8, -3, 0], t),
        "head": track([0, -4, -2, 4, 4, 1, 0], t),
        "jaw": track([3, 10, 16, 18, 10, 5, 3], t),
        "tail1": track([0, 14, 6, -8, -10, -4, 0], t),
        "tail2": track([0, 16, 2, -10, -12, -5, 0], t),
        "tail3": track([0, 16, -4, -12, -14, -6, 0], t),
        "tail4": track([0, 14, -10, -14, -16, -8, 0], t),
        "near_foot_x": track([NEAR_X, NEAR_X, 8, 8, 8, 4, NEAR_X], t),
        "far_foot_x": track([FAR_X, FAR_X - 10, FAR_X - 14, FAR_X - 14, FAR_X - 14, FAR_X - 6, FAR_X], t),
        "far_foot_lift": track([0, 10, 0, 0, 0, 0, 0], t),
        "near_arm_u": track([0, -10, -16, -12, -8, -2, 0], t),
        "fx.swipe": track([0, 0, 0.55, 1, 0.6, 0.1, 0], t),
    }
    p.update(eyes("angry" if 0.1 < t < 0.9 else "open"))
    return p


def stomp(i: int, n: int, t: float) -> Pose:
    p: Pose = {
        "root_x": track([0, 3, 10, 11, 6, 0], t),
        "root_y": track([0, -7, 8, 8, 3, 0], t),
        "pelvis": track([0, -8, 6, 5, 2, 0], t),
        "torso": track([0, -3, 3, 2, 1, 0], t),
        "neck": track([0, -12, 10, 8, 3, 0], t),
        "head": track([0, -4, 4, 2, 1, 0], t),
        "jaw": track([3, 14, 26, 18, 8, 3], t),
        "near_foot_x": track([NEAR_X, 16, 26, 26, 14, NEAR_X], t),
        "near_foot_lift": track([0, 44, 0, 0, 10, 0], t),
        "near_foot_pitch": track([0, 16, 0, 0, 4, 0], t),
        "near_arm_u": track([0, -24, 6, 4, 0, 0], t),
        "far_arm_u": track([0, -20, 8, 6, 0, 0], t),
        "tail1": track([0, -8, 6, 4, 1, 0], t),
        "tail2": track([0, -8, 8, 5, 1, 0], t),
        "tail3": track([0, -8, 10, 6, 2, 0], t),
        "tail4": track([0, -8, 12, 8, 2, 0], t),
        "fx.stomp": track([0, 0, 0.7, 1, 0.45, 0], t),
        "fx.dust": track([0, 0, 0.8, 1, 0.6, 0.15], t),
    }
    p.update(eyes("angry" if 0.1 < t < 0.9 else "open"))
    return p


def hurt(i: int, n: int, t: float) -> Pose:
    p: Pose = {
        "root_x": track([0, -14, -8, -2], t),
        "root_y": track([0, -2, 1, 0], t),
        "pelvis": track([0, -9, -4, -1], t),
        "torso": track([0, -3, -1, 0], t),
        "neck": track([0, -14, -6, -2], t),
        "head": track([0, -14, -5, 0], t),
        "jaw": track([3, 26, 14, 4], t),
        "tail1": track([0, 10, 4, 0], t),
        "tail2": track([0, 12, 5, 0], t),
        "tail3": track([0, 14, 6, 0], t),
        "tail4": track([0, 16, 8, 0], t),
        "near_arm_u": track([0, -30, -14, -2], t),
        "far_arm_u": track([0, -26, -12, -2], t),
        "fx.hit": track([0, 1, 0.35, 0], t),
    }
    p.update(eyes("shut" if 0.2 < t < 0.8 else "open"))
    return p


def death(i: int, n: int, t: float) -> Pose:
    p: Pose = {
        "root_x": track([0, -8, -12, -10, -6, -4, -4, -4], t),
        # 81, not 82: one unit lower, the fallen body's lower edge lands on a
        # half-covered pixel row the part flipbook's replay misses by a blob.
        "root_y": track([0, -3, 24, 56, 78, 81, 81, 81], t),
        "pelvis": track([0, -9, 2, 8, 6, 4, 4, 4], t),
        "torso": track([0, -3, 2, 4, 3, 2, 2, 2], t),
        "neck": track([0, -17, -8, 6, 12, 14, 15, 15], t),
        "head": track([0, -12, -4, 4, 6, 8, 8, 8], t),
        "jaw": track([3, 34, 24, 18, 14, 10, 9, 9], t),
        "near_foot_x": track([NEAR_X, NEAR_X, 6, 12, 16, 16, 16, 16], t),
        "far_foot_x": track([FAR_X, FAR_X, FAR_X + 2, FAR_X + 8, FAR_X + 12, FAR_X + 12, FAR_X + 12, FAR_X + 12], t),
        "tail1": track([0, -6, -8, -8, -6, -4, -4, -4], t),
        "tail2": track([0, -6, -8, -6, -2, 0, 0, 0], t),
        "tail3": track([0, -6, -6, -4, 2, 4, 4, 4], t),
        "tail4": track([0, -6, -4, -2, 4, 6, 6, 6], t),
        "near_arm_u": track([0, -30, -10, 10, 20, 24, 24, 24], t),
        "near_arm_l": track([0, -10, 0, 10, 16, 18, 18, 18], t),
        "far_arm_u": track([0, -26, -8, 10, 18, 22, 22, 22], t),
        "far_arm_l": track([0, -8, 2, 10, 14, 16, 16, 16], t),
        "fx.thud": track([0, 0, 0, 0, 1, 0.5, 0, 0], t),
    }
    p.update(eyes("dead" if t > 0.6 else "shut" if t > 0.1 else "open"))
    return p


CLIPS: Dict[str, Callable[[int, int, float], Pose]] = {
    "idle": idle,
    "walk": walk,
    "charge": charge,
    "bite": bite,
    "roar": roar,
    "tail_swipe": tail_swipe,
    "stomp": stomp,
    "hurt": hurt,
    "death": death,
}

DEFAULTS: Pose = {
    "near_foot_x": NEAR_X,
    "far_foot_x": FAR_X,
    "eye.open": 1.0,
    "jaw": 3.0,
}


def author_clip(name: str, frames: int, ms: int, loop: bool) -> dict:
    fn = CLIPS[name]
    times = [i / frames for i in range(frames)] if loop else [i / max(1, frames - 1) for i in range(frames)]
    poses = [fn(i, frames, t) for i, t in enumerate(times)]
    names = sorted({k for pose in poses for k in pose})
    channels = {}
    for key in names:
        k = SCALE if key in DISTANCE_CHANNELS else 1.0
        values = [round(float(pose.get(key, DEFAULTS.get(key, 0.0))) * k, 3) for pose in poses]
        if all(abs(v - values[0]) < 1e-9 for v in values):
            channels[key] = {"const": values[0]}
            continue
        pairs = [[round(t, 6), v] for t, v in zip(times, values)]
        if loop:
            pairs.append([1.0, values[0]])
        channels[key] = {"keys": pairs}
    return {"loop": loop, "frames": frames, "duration_ms": ms, "channels": channels}


# --- the document --------------------------------------------------------------------


def build() -> dict:
    J_svg, svg_parts = read_svg()
    J = {name: (x * SCALE, y * SCALE) for name, (x, y) in J_svg.items()}
    bones, world = build_bones(J)
    parts = []
    for sp in sorted(svg_parts, key=lambda p: p["z"]):
        origin, angle = world[sp["bone"]]
        # A sprite part's pivot is in SVG units (``svg_source.scale`` maps it).
        origin = (origin[0] / SCALE, origin[1] / SCALE)
        part = {
            "name": sp["name"],
            "bone": sp["bone"],
            "z": sp["z"],
            "kind": "sprite",
            "include": [sp["id"]],
            "pivot": [round(origin[0], 4), round(origin[1], 4)],
            "rest_angle": round(angle, 4),
        }
        if sp["opacity"]:
            part["opacity_channel"] = sp["opacity"]
            if sp["default"]:
                part["opacity_default"] = float(sp["default"])
        parts.append(part)
    ankle_h = GROUND_Y - J["near_ankle"][1]
    ik_legs = [
        {
            "upper": f"{side}_thigh",
            "lower": f"{side}_shin",
            "foot": f"{side}_foot",
            "channel_prefix": f"{side}_foot",
            "rest_x": round(J[f"{side}_ankle"][0] - CENTER_X, 4),
            "rest_lift": round(GROUND_Y - ankle_h - J[f"{side}_ankle"][1], 4),
            "rest_pitch": 0.0,
            "bend": -1.0,
        }
        for side in ("far", "near")
    ]
    clips = {name: author_clip(name, frames, ms, loop) for name, frames, ms, loop in ROWS}
    rel_svg = Path("../../../../data/characters/trex_enemy/trex_enemy.svg")
    return {
        "name": "trex_enemy",
        "frame": {
            "width": FRAME_W,
            "height": FRAME_H,
            "center_x": CENTER_X,
            "ground_y": GROUND_Y,
            "ankle_h": round(ankle_h, 4),
            "supersample": SUPERSAMPLE,
            "render_scale": 1,
        },
        "svg_source": {"path": str(rel_svg), "view": VIEW_LABEL, "ref_dpi": 25.4, "scale": SCALE},
        "palette": {},
        "bones": bones,
        "parts": parts,
        "ik_legs": ik_legs,
        "ik_chains": [],
        "clips": clips,
        "sprite_tuning": {"collision_scale": 1.0},
        "features": {"facing": "east"},
    }


def main(argv: List[str] | None = None) -> int:
    del argv
    doc = build()
    RIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    RIG_PATH.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf8")
    print(RIG_PATH.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
