"""Bind explicitly labelled multiview SVG art to the reusable 2D bone rig.

This is the deliberately small, artist-facing contract used by Oiler.  The SVG
is the source of truth: an artist edits ordinary vector groups and joint marker
circles in Inkscape; this module extracts bone geometry and sprite bindings
without recreating or interpreting the artwork.

Top-level view layers are normal Inkscape layers.  Inside a view, artist-facing
labels are free to stay human-readable.  Rig metadata lives on explicit SVG
data attributes:

* ``data-rig-part``, ``data-rig-bone``, ``data-rig-z`` and optional
  ``data-rig-opacity`` bind a drawable group as one rigid sprite part.
* ``data-rig-joint`` names a circle at an articulation.
* ``data-rig-side-map`` optionally maps artist-facing anatomical side names
  onto the renderer's depth-oriented ``near``/``far`` channels.  A frontal
  view can therefore use ``left_arm_u`` and ``right_hip`` throughout the SVG
  while still emitting a rig compatible with the shared animation runtime.

The original compact label forms
``part:<part_name>:<bone_name>:<z>[:<opacity_channel>]`` and
``joint:<joint_name>`` remain supported for older character SVGs.  Markers may
be hidden in the authored SVG; extraction isolates them by id and reads their
rendered centre, so arbitrary ancestor grouping and transforms are respected.

After applying an optional side map, the required joint names are ``waist``,
``neck`` and, for each of ``near`` and ``far``: ``shoulder``, ``elbow``,
``wrist``, ``handtip``, ``hip``, ``knee``, ``ankle`` and ``toe``.  The
resulting document uses the standard pelvis/torso/head + two-arm + two-leg
skeleton and emits generic two-bone IK chains for both arms as well as the
existing planted-foot IK bindings.

The art hierarchy is explicit on purpose.  Unlike PCA's compatibility
extractor, there are no heuristics based on English group names, bounding-box
joint guesses, or character-specific element ids.  A reshaped path keeps its
binding; a renamed generated id is irrelevant; manual SVG editing remains the
primary authoring workflow.
"""

from __future__ import annotations

import math
import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Tuple

from .skeleton import two_bone_ik
from .svg_parts import _label, _local, rasterize_subset

Point = Tuple[float, float]
_DRAWABLE = {"path", "polygon", "rect", "ellipse", "circle", "line"}
_PART_NAME_ATTR = "data-rig-part"
_PART_BONE_ATTR = "data-rig-bone"
_PART_Z_ATTR = "data-rig-z"
_PART_OPACITY_ATTR = "data-rig-opacity"
_JOINT_ATTR = "data-rig-joint"
_SIDE_MAP_ATTR = "data-rig-side-map"


@dataclass(frozen=True)
class HumanoidViewSpec:
    """Geometry/output policy for one SVG view layer."""

    view: str
    name: str
    frame_width: int = 128
    frame_height: int = 128
    center_x: float = 64.0
    ground_y: float = 118.0
    target_height: float = 104.0
    ref_dpi: float = 25.4
    supersample: int = 4
    render_scale: int = 2
    collision_scale: float = 1.65


@dataclass(frozen=True)
class _PartBinding:
    name: str
    bone: str
    z: float
    include: Tuple[str, ...]
    opacity_channel: Optional[str] = None


def _parse_side_map(layer: ET.Element) -> Dict[str, str]:
    """Parse ``left=far,right=near``-style aliases from a view layer.

    The map is deliberately source-to-runtime.  SVG authors name anatomy from
    the character's frame of reference; the extracted rig keeps the existing
    depth-oriented channel vocabulary used by clips and runtime code.
    """

    text = (layer.get(_SIDE_MAP_ATTR) or "").strip()
    if not text:
        return {}
    aliases: Dict[str, str] = {}
    for item in text.split(","):
        if "=" not in item:
            raise ValueError(
                f"invalid {_SIDE_MAP_ATTR} item {item!r}; expected source=target"
            )
        source, target = (part.strip() for part in item.split("=", 1))
        if not source or not target:
            raise ValueError(
                f"invalid {_SIDE_MAP_ATTR} item {item!r}; sides may not be empty"
            )
        if source in aliases:
            raise ValueError(f"duplicate {_SIDE_MAP_ATTR} source side {source!r}")
        aliases[source] = target
    if len(set(aliases.values())) != len(aliases):
        raise ValueError(f"{_SIDE_MAP_ATTR} targets must be unique: {aliases}")
    return aliases


def _map_side_prefix(name: str, aliases: Mapping[str, str]) -> str:
    """Map a leading anatomical side token without touching unrelated words."""

    for source, target in aliases.items():
        if name == source:
            return target
        prefix = f"{source}_"
        if name.startswith(prefix):
            return f"{target}_{name[len(prefix) :]}"
    return name


def _parse_part_label(label: str) -> Optional[Tuple[str, str, float, Optional[str]]]:
    """Parse the legacy machine-readable Inkscape label form."""

    fields = label.split(":")
    if len(fields) not in {4, 5} or fields[0] != "part":
        return None
    _, name, bone, z_text, *tail = fields
    try:
        z = float(z_text)
    except ValueError as ex:
        raise ValueError(f"invalid z in SVG part label {label!r}") from ex
    opacity = tail[0] if tail and tail[0] else None
    return name, bone, z, opacity


def _parse_part_element(
    elem: ET.Element,
) -> Optional[Tuple[str, str, float, Optional[str]]]:
    """Read explicit rig attributes, falling back to the legacy label syntax."""

    name = elem.get(_PART_NAME_ATTR)
    if name is None:
        return _parse_part_label(_label(elem) or "")

    bone = elem.get(_PART_BONE_ATTR)
    z_text = elem.get(_PART_Z_ATTR)
    missing = [
        attr
        for attr, value in ((_PART_BONE_ATTR, bone), (_PART_Z_ATTR, z_text))
        if not value
    ]
    if missing:
        raise ValueError(
            f"SVG rig part {name!r} is missing required attributes: {missing}"
        )
    try:
        z = float(z_text)
    except ValueError as ex:
        raise ValueError(
            f"invalid {_PART_Z_ATTR}={z_text!r} on SVG rig part {name!r}"
        ) from ex
    return name, bone, z, elem.get(_PART_OPACITY_ATTR) or None


def _joint_name(elem: ET.Element) -> Optional[str]:
    """Return a joint name from explicit metadata or the legacy label form."""

    explicit = elem.get(_JOINT_ATTR)
    if explicit:
        return explicit
    label = _label(elem) or ""
    if label.startswith("joint:"):
        return label.split(":", 1)[1]
    return None


def _descendant_ids(group: ET.Element) -> Tuple[str, ...]:
    ids: List[str] = []
    for elem in group.iter():
        if _local(elem.tag) not in _DRAWABLE:
            continue
        eid = elem.get("id")
        if not eid:
            raise ValueError(
                f"drawable under {_label(group)!r} has no id; save from Inkscape "
                "or add stable ids before extracting"
            )
        # Joint markers can sit near/inside a part group while authoring; never
        # let a marker become visible art.
        if _joint_name(elem) is not None:
            continue
        ids.append(eid)
    return tuple(ids)


def _view_root(root: ET.Element, view: str) -> ET.Element:
    for elem in root.iter():
        if _label(elem) == view:
            return elem
    available = sorted({lbl for e in root.iter() if (lbl := _label(e))})
    raise KeyError(f"SVG view {view!r} not found; labelled groups include {available}")


def _collect_parts(root: ET.Element, view: str) -> List[_PartBinding]:
    layer = _view_root(root, view)
    side_map = _parse_side_map(layer)
    parts: List[_PartBinding] = []
    for elem in layer.iter():
        parsed = _parse_part_element(elem)
        if parsed is None:
            continue
        name, bone, z, opacity = parsed
        name = _map_side_prefix(name, side_map)
        bone = _map_side_prefix(bone, side_map)
        include = _descendant_ids(elem)
        if not include:
            raise ValueError(
                f"SVG part group {_label(elem)!r} contains no drawable ids"
            )
        parts.append(_PartBinding(name, bone, z, include, opacity))
    if not parts:
        raise ValueError(f"SVG view {view!r} contains no rig-part groups")
    names = [p.name for p in parts]
    if len(names) != len(set(names)):
        dupes = sorted({n for n in names if names.count(n) > 1})
        raise ValueError(f"duplicate part names in {view!r}: {dupes}")
    return parts


def _collect_joint_ids(root: ET.Element, view: str) -> Dict[str, str]:
    layer = _view_root(root, view)
    side_map = _parse_side_map(layer)
    out: Dict[str, str] = {}
    for elem in layer.iter():
        name = _joint_name(elem)
        if name is None:
            continue
        name = _map_side_prefix(name, side_map)
        eid = elem.get("id")
        if not eid:
            raise ValueError(f"joint marker {name!r} has no SVG id")
        if name in out:
            raise ValueError(f"duplicate joint marker {name!r} in {view!r}")
        out[name] = eid
    return out


def _joint_positions(
    svg_path: Path,
    view: str,
    joint_ids: Mapping[str, str],
    ref_dpi: float,
) -> Dict[str, Point]:
    out: Dict[str, Point] = {}
    for name, eid in joint_ids.items():
        img, (ox, oy), _ = rasterize_subset(svg_path, view, [eid], ref_dpi)
        if img is None:
            raise ValueError(f"joint marker {name!r} rendered empty in {view!r}")
        out[name] = (ox + img.width / 2.0, oy + img.height / 2.0)
    return out


def _required_joints() -> Tuple[str, ...]:
    names = ["waist", "neck"]
    for side in ("far", "near"):
        names.extend(
            f"{side}_{joint}"
            for joint in (
                "shoulder",
                "elbow",
                "wrist",
                "handtip",
                "hip",
                "knee",
                "ankle",
                "toe",
            )
        )
    return tuple(names)


def _choose_bend(
    root: Point, joint: Point, target: Point, l1: float, l2: float
) -> float:
    """Choose the IK branch whose middle joint best matches the authored elbow/knee."""

    best = 1.0
    best_err = float("inf")
    for bend in (1.0, -1.0):
        a1, _ = two_bone_ik(root, target, l1, l2, bend=bend)
        rad = math.radians(a1)
        candidate = (root[0] + math.cos(rad) * l1, root[1] + math.sin(rad) * l1)
        err = math.dist(candidate, joint)
        if err < best_err:
            best, best_err = bend, err
    return best


def _world_to_parent_offset(
    origin: Point, parent_origin: Point, parent_angle: float
) -> Point:
    dx, dy = origin[0] - parent_origin[0], origin[1] - parent_origin[1]
    a = math.radians(-parent_angle)
    c, s = math.cos(a), math.sin(a)
    return (dx * c - dy * s, dx * s + dy * c)


def _all_part_ids(parts: Iterable[_PartBinding]) -> List[str]:
    out: List[str] = []
    for part in parts:
        out.extend(part.include)
    return out


def build_humanoid_view_document(
    svg_path: Path,
    rig_dir: Path,
    spec: HumanoidViewSpec,
    *,
    clips: Optional[Mapping[str, dict]] = None,
) -> dict:
    """Extract one labelled SVG view into a complete ``RigDocument`` mapping."""

    svg_path = Path(svg_path).resolve()
    rig_dir = Path(rig_dir).resolve()
    root = ET.fromstring(svg_path.read_bytes())
    parts = _collect_parts(root, spec.view)
    joint_ids = _collect_joint_ids(root, spec.view)
    joints = _joint_positions(svg_path, spec.view, joint_ids, spec.ref_dpi)

    missing = sorted(set(_required_joints()) - set(joints))
    if missing:
        raise ValueError(f"SVG view {spec.view!r} is missing joints: {missing}")

    art, (art_x, art_y), _ = rasterize_subset(
        svg_path, spec.view, _all_part_ids(parts), spec.ref_dpi
    )
    if art is None:
        raise ValueError(f"SVG view {spec.view!r} rendered no art")
    art_bottom = art_y + art.height
    art_height = float(art.height)
    scale = spec.target_height / art_height
    hip_center_src = (
        (joints["near_hip"][0] + joints["far_hip"][0]) / 2.0,
        (joints["near_hip"][1] + joints["far_hip"][1]) / 2.0,
    )

    def m(point: Point) -> Point:
        return (
            (point[0] - hip_center_src[0]) * scale + spec.center_x,
            (point[1] - art_bottom) * scale + spec.ground_y,
        )

    mapped = {name: m(point) for name, point in joints.items()}
    hip_center = m(hip_center_src)
    root_frame = (spec.center_x, spec.ground_y)

    bone_specs: List[Tuple[str, Optional[str], Point, Optional[Point]]] = [
        ("pelvis", None, hip_center, None),
        ("torso", "pelvis", mapped["waist"], None),
        ("head", "torso", mapped["neck"], None),
    ]
    for side in ("far", "near"):
        bone_specs.extend(
            [
                (
                    f"{side}_arm_u",
                    "torso",
                    mapped[f"{side}_shoulder"],
                    mapped[f"{side}_elbow"],
                ),
                (
                    f"{side}_arm_l",
                    f"{side}_arm_u",
                    mapped[f"{side}_elbow"],
                    mapped[f"{side}_wrist"],
                ),
                (
                    f"{side}_arm_hand",
                    f"{side}_arm_l",
                    mapped[f"{side}_wrist"],
                    mapped[f"{side}_handtip"],
                ),
                (
                    f"{side}_leg_u",
                    "pelvis",
                    mapped[f"{side}_hip"],
                    mapped[f"{side}_knee"],
                ),
                (
                    f"{side}_leg_l",
                    f"{side}_leg_u",
                    mapped[f"{side}_knee"],
                    mapped[f"{side}_ankle"],
                ),
                (
                    f"{side}_leg_foot",
                    f"{side}_leg_l",
                    mapped[f"{side}_ankle"],
                    mapped[f"{side}_toe"],
                ),
            ]
        )

    world: Dict[str, Tuple[Point, float]] = {}
    bones: List[dict] = []
    source_pivot: Dict[str, Point] = {
        "pelvis": hip_center_src,
        "torso": joints["waist"],
        "head": joints["neck"],
    }
    for side in ("far", "near"):
        source_pivot.update(
            {
                f"{side}_arm_u": joints[f"{side}_shoulder"],
                f"{side}_arm_l": joints[f"{side}_elbow"],
                f"{side}_arm_hand": joints[f"{side}_wrist"],
                f"{side}_leg_u": joints[f"{side}_hip"],
                f"{side}_leg_l": joints[f"{side}_knee"],
                f"{side}_leg_foot": joints[f"{side}_ankle"],
            }
        )

    for name, parent, origin, distal in bone_specs:
        if distal is None:
            angle, length = 0.0, 0.0
        else:
            angle = math.degrees(
                math.atan2(distal[1] - origin[1], distal[0] - origin[0])
            )
            length = math.dist(origin, distal)
        if parent is None:
            parent_origin, parent_angle = root_frame, 0.0
        else:
            parent_origin, parent_angle = world[parent]
        offset = _world_to_parent_offset(origin, parent_origin, parent_angle)
        bones.append(
            {
                "name": name,
                "parent": parent,
                "offset": [round(offset[0], 4), round(offset[1], 4)],
                "length": round(length, 4),
                "rest_angle": round(angle - parent_angle, 4),
            }
        )
        world[name] = (origin, angle)

    bone_names = {b["name"] for b in bones}
    rig_parts: List[dict] = []
    for binding in parts:
        if binding.bone not in bone_names:
            raise ValueError(
                f"part {binding.name!r} in {spec.view!r} binds unknown bone "
                f"{binding.bone!r}"
            )
        pivot = source_pivot[binding.bone]
        part = {
            "name": binding.name,
            "bone": binding.bone,
            "z": binding.z,
            "kind": "sprite",
            "include": list(binding.include),
            "pivot": [round(pivot[0], 3), round(pivot[1], 3)],
            "rest_angle": round(world[binding.bone][1], 4),
        }
        if binding.opacity_channel:
            part["opacity_channel"] = binding.opacity_channel
        rig_parts.append(part)
    rig_parts.sort(key=lambda p: float(p["z"]))

    ankle_y = (mapped["near_ankle"][1] + mapped["far_ankle"][1]) / 2.0
    ankle_h = spec.ground_y - ankle_y
    ik_legs: List[dict] = []
    ik_chains: List[dict] = []
    for side in ("near", "far"):
        hip = mapped[f"{side}_hip"]
        knee = mapped[f"{side}_knee"]
        ankle = mapped[f"{side}_ankle"]
        wrist = mapped[f"{side}_wrist"]
        elbow = mapped[f"{side}_elbow"]
        shoulder = mapped[f"{side}_shoulder"]
        arm_u = math.dist(shoulder, elbow)
        arm_l = math.dist(elbow, wrist)
        leg_u = math.dist(hip, knee)
        leg_l = math.dist(knee, ankle)
        ik_legs.append(
            {
                "upper": f"{side}_leg_u",
                "lower": f"{side}_leg_l",
                "foot": f"{side}_leg_foot",
                "channel_prefix": f"{side}_foot",
                "rest_x": round(ankle[0] - spec.center_x, 4),
                "rest_lift": round(ankle_y - ankle[1], 4),
                "rest_pitch": round(world[f"{side}_leg_foot"][1], 4),
                "bend": _choose_bend(hip, knee, ankle, leg_u, leg_l),
            }
        )
        ik_chains.append(
            {
                "upper": f"{side}_arm_u",
                "lower": f"{side}_arm_l",
                "end": f"{side}_arm_hand",
                "channel_prefix": f"{side}_hand",
                "rest_x": round(wrist[0] - spec.center_x, 4),
                "rest_y": round(wrist[1] - spec.ground_y, 4),
                "rest_pitch": round(world[f"{side}_arm_hand"][1], 4),
                "bend": _choose_bend(shoulder, elbow, wrist, arm_u, arm_l),
            }
        )

    return {
        "name": spec.name,
        "frame": {
            "width": spec.frame_width,
            "height": spec.frame_height,
            "center_x": spec.center_x,
            "ground_y": spec.ground_y,
            "ankle_h": round(ankle_h, 4),
            "supersample": spec.supersample,
            "render_scale": spec.render_scale,
        },
        "svg_source": {
            "path": os.path.relpath(svg_path, rig_dir),
            "view": spec.view,
            "ref_dpi": spec.ref_dpi,
            "scale": round(scale, 8),
        },
        "palette": {},
        "bones": bones,
        "parts": rig_parts,
        "ik_legs": ik_legs,
        "ik_chains": ik_chains,
        "clips": dict(clips or {}),
        "sprite_tuning": {"collision_scale": spec.collision_scale},
    }


def merge_generated_geometry(existing: Mapping[str, object], generated: dict) -> dict:
    """Refresh SVG-derived geometry while preserving authored animation data."""

    generated_keys = {
        "name",
        "frame",
        "svg_source",
        "bones",
        "parts",
        "ik_legs",
        "ik_chains",
    }
    out = dict(existing)
    for key in generated_keys:
        out[key] = generated[key]
    if not out.get("clips"):
        out["clips"] = generated.get("clips", {})
    for soft in ("palette", "sprite_tuning", "features"):
        merged = dict(generated.get(soft, {}))
        merged.update(
            existing.get(soft, {}) if isinstance(existing.get(soft), dict) else {}
        )
        if merged:
            out[soft] = merged
    return out


__all__ = [
    "HumanoidViewSpec",
    "build_humanoid_view_document",
    "merge_generated_geometry",
]
