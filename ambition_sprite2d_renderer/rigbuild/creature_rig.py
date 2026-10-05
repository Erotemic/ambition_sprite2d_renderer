"""Rig documents for creatures drawn as annotated SVGs.

A creature is drawn as an SVG whose part layers name their ``data-rig-part`` /
``data-rig-bone`` / ``data-rig-z`` (and ``data-rig-opacity`` for swap sets such
as eye states), and whose hidden ``Rig Joints`` layer holds one circle per
joint (``data-joint``). This module derives a skeleton from those joints,
binds every part to its bone at the drawn rest pose, puts the legs on IK,
samples a character's clip functions into keyed channels, and refreshes the
SVG's rig catalog.

A family module says what its anatomy is (``theropod``: the T-rex boss and the
raptor stalker; ``quadruped``: the bear mauler; ``fish``: the burning flying
shark; ``humanoid``: Bob, with a key-pose language for a fighter's moveset)
as a skeleton function and a list of legs; a character's builder script
(``scripts/build_<name>_rig.py``) supplies only its frame, its rows and its
clips.

⭐ THE SOURCE IS THE ART FILE. Nothing here draws.

Clips are authored in SVG units and scaled with the art: a clip function
returns, for one frame, channel values (bone angles in degrees, distances in
SVG units, strengths in [0, 1]); the distance channels (``root_x``,
``root_y`` and each leg's ``<prefix>_x`` / ``<prefix>_lift``) are scaled to
sprite pixels on the way into the document.
"""

from __future__ import annotations

import json
import math
import os
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, FrozenSet, List, Optional, Sequence, Tuple

SVG_NS = "http://www.w3.org/2000/svg"

Point = Tuple[float, float]
Pose = Dict[str, float]
ClipFn = Callable[[int, int, float], Pose]
#: (name, parent, rest world origin, rest world angle, length), sprite pixels.
BoneSpec = Tuple[str, Optional[str], Point, float, float]
Skeleton = Callable[[Dict[str, Point]], List[BoneSpec]]


@dataclass(frozen=True)
class Leg:
    """A two-bone leg on IK: ``upper`` and ``lower`` reach the ``foot`` bone's
    origin, which the drawing marks with the joint ``ankle``. ``bend`` picks
    the side the middle joint folds to; the one that reproduces the drawn
    joint at rest is the right one (a builder can check with
    ``RigDocument.solve``)."""

    upper: str
    lower: str
    foot: str
    prefix: str
    ankle: str
    bend: float = -1.0


@dataclass(frozen=True)
class CreatureSpec:
    """What a creature's drawing cannot state: its anatomy, where it
    publishes, at what size, and how it moves."""

    name: str
    svg_path: Path
    rig_path: Path
    view_label: str
    skeleton: Skeleton
    legs: Sequence[Leg]
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
    #: The joint whose height is the document's ``ankle_h`` (every leg's
    #: ankle is drawn at that height above the ground). A legless creature
    #: (a flyer, a swimmer) has none.
    ankle_joint: str = "near_ankle"
    #: Clips keyed between frames too: ``{clip: n}`` adds ``n`` evenly spaced
    #: keys inside each frame interval, so a reader sampling between frames
    #: (a swing's smear, its hit volume) follows the authored path instead of
    #: a straight line between two drawn frames. Frames render the same.
    substeps: Dict[str, int] = field(default_factory=dict)
    #: Angle channels kept continuous from key to key (no jump across
    #: +-180 degrees), so sampling between keys turns the short way round.
    angle_channels: FrozenSet[str] = frozenset()
    #: Write each channel's keys on one line (a fighter's hundred-odd clips
    #: are otherwise mostly whitespace).
    compact_keys: bool = False

    @property
    def center_x(self) -> float:
        return self.svg_center_x * self.scale

    @property
    def ground_y(self) -> float:
        return self.svg_ground_y * self.scale

    @property
    def distance_channels(self) -> FrozenSet[str]:
        names = {"root_x", "root_y"}
        for leg in self.legs:
            names |= {f"{leg.prefix}_x", f"{leg.prefix}_lift"}
        return frozenset(names)


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


def segment(name: str, parent: Optional[str], a: Point, b: Point) -> BoneSpec:
    """A bone from joint ``a`` toward joint ``b``."""
    return (name, parent, a, heading(a, b), dist(a, b))


def limb(upper: str, lower: str, foot: str, parent: str, hip: Point, knee: Point, ankle: Point) -> List[BoneSpec]:
    """A two-bone leg and the foot bone at its end (world angle 0 at rest, so
    a foot's pitch is its drawn angle)."""
    return [segment(upper, parent, hip, knee), segment(lower, upper, knee, ankle), (foot, lower, ankle, 0.0, 0.0)]


def build_bones(J: Dict[str, Point], spec: CreatureSpec):
    """Bones (the document's records) and each bone's rest ``(origin, world
    angle)``, in sprite pixels (``J`` already scaled); the rest pose IS the
    drawing."""
    order = spec.skeleton(J)
    world: Dict[str, Tuple[Point, float]] = {}
    bones = []
    for name, par, origin, angle, length in order:
        world[name] = (origin, angle)
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


EYE_STATES = ("open", "angry", "shut", "dead")


def eyes(state: str) -> Pose:
    """One eye state shown, the rest hidden (``eye.<state>`` swap set)."""
    return {f"eye.{name}": 1.0 if name == state else 0.0 for name in EYE_STATES}


def unwrap(values: List[float]) -> List[float]:
    """Angles (degrees) shifted by whole turns so no step exceeds half a turn."""
    out = values[:1]
    for v in values[1:]:
        prev = out[-1]
        out.append(round(v + 360.0 * round((prev - v) / 360.0), 3))
    return out


def author_clip(spec: CreatureSpec, name: str, frames: int, ms: int, loop: bool) -> dict:
    """Sample a clip function at the sheet's frame times into keyed channels."""
    fn = spec.clips[name]
    times = [i / frames for i in range(frames)] if loop else [i / max(1, frames - 1) for i in range(frames)]
    index = list(range(frames))
    sub = spec.substeps.get(name, 0)
    if sub:
        ends = times[1:] + ([1.0] if loop else [])
        fine, index = [], []
        for i, t0 in enumerate(times):
            fine.append(t0)
            index.append(i)
            if i < len(ends):
                for k in range(1, sub + 1):
                    fine.append(t0 + (ends[i] - t0) * k / (sub + 1))
                    index.append(i)
        times = fine
    poses = [fn(i, frames, t) for i, t in zip(index, times)]
    names = sorted({k for pose in poses for k in pose})
    distances = spec.distance_channels
    channels = {}
    for key in names:
        k = spec.scale if key in distances else 1.0
        values = [round(float(pose.get(key, spec.defaults.get(key, 0.0))) * k, 3) for pose in poses]
        if key in spec.angle_channels:
            values = unwrap(values)
        if all(abs(v - values[0]) < 1e-9 for v in values):
            channels[key] = {"const": values[0]}
            continue
        pairs = [[round(t, 6), v] for t, v in zip(times, values)]
        if loop:
            first = values[0]
            if key in spec.angle_channels:
                first = unwrap([values[-1], first])[1]
            pairs.append([1.0, first])
        channels[key] = {"keys": pairs}
    return {"loop": loop, "frames": frames, "duration_ms": ms, "channels": channels}


# --- the document --------------------------------------------------------------------


def build(spec: CreatureSpec) -> dict:
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
    ankle_h = spec.ground_y - J[spec.ankle_joint][1] if spec.legs else 0.0
    ik_legs = [
        {
            "upper": leg.upper,
            "lower": leg.lower,
            "foot": leg.foot,
            "channel_prefix": leg.prefix,
            "rest_x": round(J[leg.ankle][0] - spec.center_x, 4),
            "rest_lift": round(spec.ground_y - ankle_h - J[leg.ankle][1], 4),
            "rest_pitch": 0.0,
            "bend": leg.bend,
        }
        for leg in spec.legs
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


def install_svg_catalog(spec: CreatureSpec) -> None:
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


def compact_keys(text: str) -> str:
    """``json.dumps(indent=1)`` output with every ``[t, v]`` key pair, and
    every ``"keys"`` list of them, on one line. Still valid JSON, same data."""
    num = r"(-?[\d.e+-]+)"
    text = re.sub(r"\[\n\s*" + num + r",\n\s*" + num + r"\n\s*\]", r"[\1, \2]", text)
    return re.sub(
        r'("keys": )\[\n((?:\s*\[[^\[\]\n]*\],?\n)+)\s*\]',
        lambda m: m.group(1) + "[" + ", ".join(x.strip().rstrip(",") for x in m.group(2).strip().split("\n")) + "]",
        text,
    )


def write(spec: CreatureSpec) -> List[Path]:
    """Write the rig document, then the SVG's catalog from it."""
    doc = build(spec)
    spec.rig_path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(doc, indent=1)
    if spec.compact_keys:
        text = compact_keys(text)
    spec.rig_path.write_text(text + "\n", encoding="utf8")
    install_svg_catalog(spec)
    return [spec.rig_path, spec.svg_path]
