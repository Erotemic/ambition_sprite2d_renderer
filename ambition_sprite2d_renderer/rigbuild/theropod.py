"""Rig documents for side-view theropods, derived from their annotated SVGs.

The T-rex boss and the raptor stalker share one anatomy: a pelvis carrying a
torso, an S-necked head with a hinged jaw, a four-bone tail, two-bone
digitigrade legs on IK with a foot below the ankle, and small two-bone arms.
Each is drawn as an SVG whose part layers name their ``data-rig-part`` /
``data-rig-bone`` / ``data-rig-z`` (and ``data-rig-opacity`` for swap sets such
as the eye states), and whose hidden ``Rig Joints`` layer holds one circle per
joint (``data-joint``). This module derives the skeleton from those joints,
binds every part to its bone at the drawn rest pose, samples a character's
clip functions into keyed channels, and refreshes the SVG's rig catalog.

⭐ THE SOURCE IS THE ART FILE. Nothing here draws; a character's builder
script (``scripts/build_<name>_rig.py``) supplies only its frame, its rows and
its clips.

Clips are authored in SVG units and scaled with the art: a clip function
returns, for one frame, channel values (bone angles in degrees, distances in
SVG units, strengths in [0, 1]); ``DISTANCE_CHANNELS`` are scaled to sprite
pixels on the way into the document.
"""

from __future__ import annotations

import json
import math
import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

SVG_NS = "http://www.w3.org/2000/svg"

Point = Tuple[float, float]
Pose = Dict[str, float]
ClipFn = Callable[[int, int, float], Pose]

#: Clip channels that are distances (scaled with the art); angles and
#: strengths are not.
DISTANCE_CHANNELS = frozenset(
    {"root_x", "root_y", "near_foot_x", "near_foot_lift", "far_foot_x", "far_foot_lift"}
)

TAIL_JOINTS = ("tail0", "tail1", "tail2", "tail3", "tail_tip")


@dataclass(frozen=True)
class TheropodSpec:
    """What a theropod's drawing cannot state: where it publishes, at what
    size, and how it moves."""

    name: str
    svg_path: Path
    rig_path: Path
    view_label: str
    #: Sprite pixels per SVG unit.
    scale: float
    #: The drawing's centre line and ground, in SVG units.
    svg_center_x: float
    svg_ground_y: float
    frame_size: Tuple[int, int]
    #: (row, frames, duration ms, loops). The game binds rows by name.
    rows: List[Tuple[str, int, int, bool]]
    clips: Dict[str, ClipFn]
    #: A channel's value in frames whose clip function leaves it out.
    defaults: Pose = field(default_factory=dict)
    supersample: int = 4
    #: The jaw bone's length, in sprite pixels (only the editor draws it).
    jaw_length: float = 80.0

    @property
    def center_x(self) -> float:
        return self.svg_center_x * self.scale

    @property
    def ground_y(self) -> float:
        return self.svg_ground_y * self.scale


# --- the SVG ------------------------------------------------------------------


def read_svg(svg_path: Path) -> Tuple[Dict[str, Point], List[dict]]:
    """Joints (in SVG units) and the part layers."""
    root = ET.parse(svg_path).getroot()
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


def build_bones(J: Dict[str, Point], spec: TheropodSpec):
    """Bones (the document's records) and each bone's rest ``(origin, world
    angle)``, in sprite pixels (``J`` already scaled); the rest pose IS the
    drawing."""
    order: List[Tuple[str, Optional[str], Point, float, float]] = []
    world: Dict[str, Tuple[Point, float]] = {}

    def add(name, parent, origin, angle, length):
        order.append((name, parent, origin, angle, length))
        world[name] = (origin, angle)

    add("pelvis", None, J["pelvis"], 0.0, 0.0)
    add("torso", "pelvis", J["pelvis"], heading(J["pelvis"], J["neck_base"]), dist(J["pelvis"], J["neck_base"]))
    add("neck", "torso", J["neck_base"], heading(J["neck_base"], J["head"]), dist(J["neck_base"], J["head"]))
    add("head", "neck", J["head"], heading(J["head"], J["snout"]), dist(J["head"], J["snout"]))
    add("jaw", "head", J["jaw"], heading(J["head"], J["snout"]), spec.jaw_length)
    parent = "pelvis"
    for i in range(4):
        name = f"tail{i + 1}"
        a, b = J[TAIL_JOINTS[i]], J[TAIL_JOINTS[i + 1]]
        add(name, parent, a, heading(a, b), dist(a, b))
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
    for name, par, origin, angle, length in order:
        if par is None:
            offset = (origin[0] - spec.center_x, origin[1] - spec.ground_y)
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


# --- clip authoring ----------------------------------------------------------------


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
    The first half is stance (the foot slides back under the moving body);
    the second half is the swing forward."""
    p = phase % 1.0
    if p < 0.5:
        return centre + stride * (1.0 - 4.0 * p), 0.0, 0.0
    s = (p - 0.5) / 0.5
    h = lift * pulse(s)
    return centre - stride + 2.0 * stride * smooth01(s), h, 0.45 * h


def gait(
    t: float,
    *,
    near_x: float,
    far_x: float,
    stride: float,
    lift: float,
    bob: float,
    sway: float,
    tail: float,
    arm: float = 6.0,
) -> Pose:
    """A two-legged loop: the feet half a cycle apart, the body highest at
    mid-stance, the neck and tail following the sway a little late."""
    p: Pose = {}
    nx, nl, npitch = step(t, near_x, stride, lift)
    fx, fl, fpitch = step(t + 0.5, far_x, stride, lift)
    p.update(near_foot_x=nx, near_foot_lift=nl, near_foot_pitch=npitch,
             far_foot_x=fx, far_foot_lift=fl, far_foot_pitch=fpitch)
    w = math.tau * t
    p["root_y"] = bob * (0.5 - abs(math.sin(w)))
    p["pelvis"] = sway * math.sin(w)
    p["torso"] = -0.4 * sway * math.sin(w)
    p["neck"] = -1.2 * sway * math.sin(w + 0.6)
    p["head"] = 0.8 * sway * math.sin(w + 1.2)
    for i in range(4):
        p[f"tail{i + 1}"] = tail * math.sin(w - 0.7 * (i + 1)) * (0.6 + 0.25 * i)
    p["near_arm_u"] = arm * math.sin(w)
    p["near_arm_l"] = arm * math.sin(w - 0.8)
    p["far_arm_u"] = -arm * math.sin(w)
    p["far_arm_l"] = -arm * math.sin(w - 0.8)
    return p


EYE_STATES = ("open", "angry", "shut", "dead")


def eyes(state: str) -> Pose:
    """One eye state shown, the rest hidden (``eye.<state>`` swap set)."""
    return {f"eye.{name}": 1.0 if name == state else 0.0 for name in EYE_STATES}


def author_clip(spec: TheropodSpec, name: str, frames: int, ms: int, loop: bool) -> dict:
    """Sample a clip function at the sheet's frame times into keyed channels."""
    fn = spec.clips[name]
    times = [i / frames for i in range(frames)] if loop else [i / max(1, frames - 1) for i in range(frames)]
    poses = [fn(i, frames, t) for i, t in enumerate(times)]
    names = sorted({k for pose in poses for k in pose})
    channels = {}
    for key in names:
        k = spec.scale if key in DISTANCE_CHANNELS else 1.0
        values = [round(float(pose.get(key, spec.defaults.get(key, 0.0))) * k, 3) for pose in poses]
        if all(abs(v - values[0]) < 1e-9 for v in values):
            channels[key] = {"const": values[0]}
            continue
        pairs = [[round(t, 6), v] for t, v in zip(times, values)]
        if loop:
            pairs.append([1.0, values[0]])
        channels[key] = {"keys": pairs}
    return {"loop": loop, "frames": frames, "duration_ms": ms, "channels": channels}


# --- the document --------------------------------------------------------------------


def build(spec: TheropodSpec) -> dict:
    J_svg, svg_parts = read_svg(spec.svg_path)
    J = {name: (x * spec.scale, y * spec.scale) for name, (x, y) in J_svg.items()}
    bones, world = build_bones(J, spec)
    parts = []
    for sp in sorted(svg_parts, key=lambda p: p["z"]):
        origin, angle = world[sp["bone"]]
        # A sprite part's pivot is in SVG units (``svg_source.scale`` maps it).
        origin = (origin[0] / spec.scale, origin[1] / spec.scale)
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
    ankle_h = spec.ground_y - J["near_ankle"][1]
    ik_legs = [
        {
            "upper": f"{side}_thigh",
            "lower": f"{side}_shin",
            "foot": f"{side}_foot",
            "channel_prefix": f"{side}_foot",
            "rest_x": round(J[f"{side}_ankle"][0] - spec.center_x, 4),
            "rest_lift": round(spec.ground_y - ankle_h - J[f"{side}_ankle"][1], 4),
            "rest_pitch": 0.0,
            "bend": -1.0,
        }
        for side in ("far", "near")
    ]
    clips = {name: author_clip(spec, name, frames, ms, loop) for name, frames, ms, loop in spec.rows}
    rel_svg = Path(os.path.relpath(spec.svg_path, spec.rig_path.parent))
    return {
        "name": spec.name,
        "frame": {
            "width": spec.frame_size[0],
            "height": spec.frame_size[1],
            "center_x": spec.center_x,
            "ground_y": spec.ground_y,
            "ankle_h": round(ankle_h, 4),
            "supersample": spec.supersample,
            "render_scale": 1,
        },
        "svg_source": {"path": rel_svg.as_posix(), "view": spec.view_label, "ref_dpi": 25.4, "scale": spec.scale},
        "palette": {},
        "bones": bones,
        "parts": parts,
        "ik_legs": ik_legs,
        "ik_chains": [],
        "clips": clips,
        "sprite_tuning": {"collision_scale": 1.0},
        "features": {"facing": "east"},
    }


def install_svg_catalog(spec: TheropodSpec) -> None:
    """Refresh the SVG's embedded rig catalog (``svg_rig_tool``) from the rig
    document, so the SVG states the same skeleton the rig turns."""
    from ..devtools import svg_rig_tool

    catalog, quality = svg_rig_tool.catalog_from_rigdoc(spec.rig_path, spec.svg_path, used_view_ids=set())
    svg_rig_tool.install_block(
        spec.svg_path, svg_rig_tool._serialize_character_block([catalog], {catalog.view_id: quality})
    )
    problems = svg_rig_tool.validate(spec.svg_path)
    if problems:
        raise SystemExit(f"{spec.svg_path.name}: rig catalog does not validate: {problems}")


def write(spec: TheropodSpec) -> List[Path]:
    """Write the rig document, then the SVG's catalog from it."""
    doc = build(spec)
    spec.rig_path.parent.mkdir(parents=True, exist_ok=True)
    spec.rig_path.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf8")
    install_svg_catalog(spec)
    return [spec.rig_path, spec.svg_path]
