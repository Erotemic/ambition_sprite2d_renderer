"""Backend-neutral authored rig/motion representation for editor frontends.

This module is the schema seam between character-authored sources and interactive
editors.  The source SVG owns static artwork + rig geometry.  Motion JSON owns
named rest-relative poses and clips.  Godot, PySide, procedural generators, and
agent-facing tools are all frontends over these semantics rather than sources of
runtime meaning.

The first pilot deliberately targets rigid cutout 2D rigs:

* SVG rig metadata provides a :class:`RigDefinition` in root-SVG user units.
* :class:`PoseState` stores parent-local deltas from that rest rig.
* :class:`ClipDefinition` is pose-centric: a timeline is a sequence of complete
  pose keys, optionally referring to reusable named poses.  Explicit scalar
  property tracks are supported for motion that genuinely needs independent
  continuous curves.
* :class:`CharacterMotionBinding` supplies only presentation-frame mapping and
  selects a motion library for one character.

``RigDocument`` remains a renderer compatibility projection for now.  The
adapter here intentionally bakes IK/procedural legacy channels into direct FK
transforms; Godot-specific scene/resource structure is never part of this model.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import math
from pathlib import Path
import re
from typing import Any, Iterable, Mapping, Sequence
import xml.etree.ElementTree as ET

Point = tuple[float, float]
Matrix = tuple[float, float, float, float, float, float]

SVG_RIG_SCHEMA = "ambition-svg-rig-v1"
MOTION_BINDING_SCHEMA = "ambition-character-motion-v1"
MOTION_LIBRARY_SCHEMA = "ambition-motion-library-v1"
POSE_SCHEMA = "ambition-pose-v1"
CLIP_SCHEMA = "ambition-clip-v1"
LEGACY_PROJECTION_SCHEMA = "ambition-rigdoc-projection-v1"

# Explicitly serialized with each motion library so other frontends do not have
# to infer our coordinate conventions from Python or from Godot.
MOTION_SPACE_V1 = {
    "linear_unit": "rig_user_unit",
    "x_axis": "right",
    "y_axis": "down",
    "rotation_unit": "degrees",
    "positive_rotation": "clockwise",
    "bone_transform": "parent_local_delta_from_svg_rest",
}

_EPS = 1e-7


def _round(value: float, digits: int = 6) -> float:
    value = round(float(value), digits)
    return 0.0 if abs(value) < 0.5 * 10 ** (-digits) else value


def _vec_round(value: Sequence[float], digits: int = 6) -> Point:
    return (_round(value[0], digits), _round(value[1], digits))


def _rotate(point: Point, degrees: float) -> Point:
    angle = math.radians(degrees)
    c, s = math.cos(angle), math.sin(angle)
    return (point[0] * c - point[1] * s, point[0] * s + point[1] * c)


def _sub(a: Point, b: Point) -> Point:
    return (a[0] - b[0], a[1] - b[1])


def _add(a: Point, b: Point) -> Point:
    return (a[0] + b[0], a[1] + b[1])


def _mul(point: Point, scale: float) -> Point:
    return (point[0] * scale, point[1] * scale)


def _matrix_mul(left: Matrix, right: Matrix) -> Matrix:
    a1, b1, c1, d1, e1, f1 = left
    a2, b2, c2, d2, e2, f2 = right
    return (
        a1 * a2 + c1 * b2,
        b1 * a2 + d1 * b2,
        a1 * c2 + c1 * d2,
        b1 * c2 + d1 * d2,
        a1 * e2 + c1 * f2 + e1,
        b1 * e2 + d1 * f2 + f1,
    )


def _transform_matrix(raw: str | None) -> Matrix:
    current: Matrix = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    if not raw:
        return current
    for match in re.finditer(r"([A-Za-z]+)\s*\(([^)]*)\)", raw):
        name = match.group(1).lower()
        values = [float(v) for v in re.split(r"[\s,]+", match.group(2).strip()) if v]
        if name == "matrix" and len(values) == 6:
            op: Matrix = tuple(values)  # type: ignore[assignment]
        elif name == "translate" and len(values) in {1, 2}:
            op = (1.0, 0.0, 0.0, 1.0, values[0], values[1] if len(values) == 2 else 0.0)
        elif name == "scale" and len(values) in {1, 2}:
            sy = values[1] if len(values) == 2 else values[0]
            op = (values[0], 0.0, 0.0, sy, 0.0, 0.0)
        elif name == "rotate" and len(values) in {1, 3}:
            angle = math.radians(values[0])
            ca, sa = math.cos(angle), math.sin(angle)
            rot: Matrix = (ca, sa, -sa, ca, 0.0, 0.0)
            if len(values) == 3:
                cx, cy = values[1], values[2]
                op = _matrix_mul(
                    _matrix_mul((1.0, 0.0, 0.0, 1.0, cx, cy), rot),
                    (1.0, 0.0, 0.0, 1.0, -cx, -cy),
                )
            else:
                op = rot
        elif name == "skewx" and len(values) == 1:
            op = (1.0, 0.0, math.tan(math.radians(values[0])), 1.0, 0.0, 0.0)
        elif name == "skewy" and len(values) == 1:
            op = (1.0, math.tan(math.radians(values[0])), 0.0, 1.0, 0.0, 0.0)
        else:
            raise ValueError(f"unsupported SVG transform component {match.group(0)!r}")
        current = _matrix_mul(current, op)
    return current


def _ancestors(root: ET.Element, target: ET.Element) -> list[ET.Element]:
    parent_by_child = {child: parent for parent in root.iter() for child in parent}
    out: list[ET.Element] = []
    current = target
    while current in parent_by_child:
        current = parent_by_child[current]
        out.append(current)
    return out


def _element_matrix(root: ET.Element, elem: ET.Element) -> Matrix:
    current: Matrix = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    for ancestor in reversed(_ancestors(root, elem)):
        if ancestor is root:
            continue
        current = _matrix_mul(current, _transform_matrix(ancestor.get("transform")))
    return _matrix_mul(current, _transform_matrix(elem.get("transform")))


def _apply_matrix(matrix: Matrix, point: Point) -> Point:
    a, b, c, d, e, f = matrix
    return (a * point[0] + c * point[1] + e, b * point[0] + d * point[1] + f)


def _element_point_in_root(root: ET.Element, elem: ET.Element) -> Point:
    if elem.get("cx") is not None and elem.get("cy") is not None:
        point = (float(elem.get("cx", "0")), float(elem.get("cy", "0")))
    elif elem.get("x") is not None and elem.get("y") is not None:
        point = (float(elem.get("x", "0")), float(elem.get("y", "0")))
    else:
        raise ValueError(f"SVG marker {elem.get('id')!r} has no point coordinates")
    return _apply_matrix(_element_matrix(root, elem), point)


def _length_to_reference_px(raw: str | None, *, dpi: float) -> float | None:
    if not raw:
        return None
    match = re.fullmatch(
        r"\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))(?:[eE]([+-]?\d+))?\s*([A-Za-z%]*)\s*",
        raw,
    )
    if not match:
        return None
    value = float(match.group(1))
    if match.group(2):
        value *= 10.0 ** int(match.group(2))
    unit = match.group(3).lower()
    if unit in {"", "px"}:
        return value
    if unit == "mm":
        return value * dpi / 25.4
    if unit == "cm":
        return value * dpi / 2.54
    if unit == "in":
        return value * dpi
    if unit == "pt":
        return value * dpi / 72.0
    if unit == "pc":
        return value * dpi / 6.0
    return None


@dataclass(frozen=True)
class SvgReferenceSpace:
    viewbox: tuple[float, float, float, float]
    reference_px_per_user_x: float
    reference_px_per_user_y: float

    def user_to_reference(self, point: Point) -> Point:
        vx, vy, _vw, _vh = self.viewbox
        return (
            (point[0] - vx) * self.reference_px_per_user_x,
            (point[1] - vy) * self.reference_px_per_user_y,
        )


def svg_reference_space(svg_path: str | Path, *, dpi: float = 96.0) -> SvgReferenceSpace:
    root = ET.parse(svg_path).getroot()
    raw = root.get("viewBox")
    if not raw:
        raise ValueError(f"{svg_path}: SVG rig needs a root viewBox")
    values = [float(v) for v in raw.replace(",", " ").split()]
    if len(values) != 4:
        raise ValueError(f"{svg_path}: malformed root viewBox {raw!r}")
    vx, vy, vw, vh = values
    width_px = _length_to_reference_px(root.get("width"), dpi=dpi)
    height_px = _length_to_reference_px(root.get("height"), dpi=dpi)
    if width_px is None or height_px is None or vw == 0.0 or vh == 0.0:
        raise ValueError(f"{svg_path}: cannot map root SVG units to reference pixels")
    sx, sy = width_px / vw, height_px / vh
    if not math.isclose(sx, sy, rel_tol=1e-6, abs_tol=1e-9):
        raise ValueError(
            f"{svg_path}: non-uniform root SVG viewport mapping is unsupported "
            f"for rigid cutout rigs (sx={sx}, sy={sy})"
        )
    return SvgReferenceSpace((vx, vy, vw, vh), sx, sy)


@dataclass(frozen=True)
class Transform2D:
    position: Point = (0.0, 0.0)
    rotation_deg: float = 0.0
    scale: Point = (1.0, 1.0)

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any] | None) -> "Transform2D":
        raw = raw or {}
        return cls(
            position=tuple(float(v) for v in raw.get("position", (0.0, 0.0))),  # type: ignore[arg-type]
            rotation_deg=float(raw.get("rotation_deg", 0.0)),
            scale=tuple(float(v) for v in raw.get("scale", (1.0, 1.0))),  # type: ignore[arg-type]
        )

    def to_dict(self, *, sparse: bool = False) -> dict[str, Any]:
        # Sparse source should reflect serialized precision, not floating-point
        # residue from matrix/IK conversion.  In particular, a 1e-7-ish legacy
        # solver residual must not become a visible authored translation that an
        # editor then treats as intentional.
        out: dict[str, Any] = {}
        position = _vec_round(self.position)
        rotation = _round(self.rotation_deg)
        scale = _vec_round(self.scale)
        if not sparse or any(v != 0.0 for v in position):
            out["position"] = list(position)
        if not sparse or rotation != 0.0:
            out["rotation_deg"] = rotation
        if not sparse or any(v != 1.0 for v in scale):
            out["scale"] = list(scale)
        return out

    def merged(self, patch: "Transform2D", raw_patch: Mapping[str, Any]) -> "Transform2D":
        return Transform2D(
            position=patch.position if "position" in raw_patch else self.position,
            rotation_deg=patch.rotation_deg if "rotation_deg" in raw_patch else self.rotation_deg,
            scale=patch.scale if "scale" in raw_patch else self.scale,
        )


@dataclass(frozen=True)
class BoneDefinition:
    id: str
    parent: str | None
    rest: Transform2D
    length: float
    origin: Point
    tip: Point | None
    origin_marker: str
    tip_marker: str | None


@dataclass(frozen=True)
class PartDefinition:
    id: str
    bone: str
    z: float
    elements: tuple[str, ...]
    pivot: Point
    pivot_marker: str
    bind_world_rotation_deg: float
    opacity_parameter: str | None = None


@dataclass(frozen=True)
class RigDefinition:
    source_svg: Path
    view_id: str
    source_layer: str
    source_label: str
    profile: str
    projection: str
    facing: str | None
    root_anchor: Point
    bones: tuple[BoneDefinition, ...]
    parts: tuple[PartDefinition, ...]

    @property
    def bone_by_id(self) -> dict[str, BoneDefinition]:
        return {bone.id: bone for bone in self.bones}

    @property
    def part_by_id(self) -> dict[str, PartDefinition]:
        return {part.id: part for part in self.parts}

    def validate(self) -> list[str]:
        errors: list[str] = []
        bone_ids = [bone.id for bone in self.bones]
        if len(set(bone_ids)) != len(bone_ids):
            errors.append("duplicate bone ids")
        seen: set[str] = set()
        for bone in self.bones:
            if bone.parent and bone.parent not in seen:
                errors.append(f"bone {bone.id!r} appears before or lacks parent {bone.parent!r}")
            seen.add(bone.id)
        part_ids = [part.id for part in self.parts]
        if len(set(part_ids)) != len(part_ids):
            errors.append("duplicate part ids")
        bones = set(bone_ids)
        for part in self.parts:
            if part.bone not in bones:
                errors.append(f"part {part.id!r} references missing bone {part.bone!r}")
            if not part.elements:
                errors.append(f"part {part.id!r} has no SVG elements")
        return errors


def load_svg_rig_definition(svg_path: str | Path, *, view_id: str | None = None) -> RigDefinition:
    """Resolve the embedded SVG catalog into explicit parent-local rest transforms.

    Marker positions are authoritative.  Bone angles are derived from origin→tip
    geometry when available; zero-length organizational bones fall back to the
    bound art's authored bind angle.  No legacy ``.rig.json`` is consulted.
    """

    svg_path = Path(svg_path).resolve()
    root = ET.parse(svg_path).getroot()
    ids = {elem.get("id"): elem for elem in root.iter() if elem.get("id")}
    metadata = ids.get("ambition-rig-metadata")
    if metadata is None:
        raise ValueError(f"{svg_path}: missing ambition-rig-metadata")
    if metadata.get("data-ambition-schema") != SVG_RIG_SCHEMA:
        raise ValueError(
            f"{svg_path}: expected {SVG_RIG_SCHEMA!r}, got {metadata.get('data-ambition-schema')!r}"
        )
    if metadata.get("data-ambition-role") != "character-rig":
        raise ValueError(f"{svg_path}: SVG is not a character rig")

    views = [elem for elem in metadata if elem.get("data-rig-view-def")]
    if view_id is None:
        if len(views) != 1:
            raise ValueError(
                f"{svg_path}: {len(views)} rig views available; choose one explicitly"
            )
        view = views[0]
    else:
        matches = [elem for elem in views if elem.get("data-rig-view-def") == view_id]
        if len(matches) != 1:
            available = [elem.get("data-rig-view-def") for elem in views]
            raise ValueError(f"{svg_path}: unknown rig view {view_id!r}; available={available}")
        view = matches[0]

    root_marker_id = view.get("data-rig-root")
    if not root_marker_id or root_marker_id not in ids:
        raise ValueError(f"{svg_path}: rig view lacks a valid root marker")
    root_anchor = _element_point_in_root(root, ids[root_marker_id])

    raw_bones = [elem for elem in view if elem.get("data-rig-bone-def")]
    raw_parts = [elem for elem in view if elem.get("data-rig-part-def")]
    part_angles_by_bone: dict[str, list[float]] = {}
    for part in raw_parts:
        bone = part.get("data-rig-bone")
        if bone and part.get("data-rig-bind-angle") is not None:
            part_angles_by_bone.setdefault(bone, []).append(float(part.get("data-rig-bind-angle", "0")))

    origins: dict[str, Point] = {}
    tips: dict[str, Point | None] = {}
    world_angles: dict[str, float] = {}
    bone_elements: dict[str, ET.Element] = {}
    for elem in raw_bones:
        name = str(elem.get("data-rig-bone-def"))
        origin_id = elem.get("data-rig-origin")
        if not origin_id or origin_id not in ids:
            raise ValueError(f"{svg_path}: bone {name!r} lacks origin marker")
        origin = _element_point_in_root(root, ids[origin_id])
        tip_id = elem.get("data-rig-tip")
        tip = _element_point_in_root(root, ids[tip_id]) if tip_id and tip_id in ids else None
        origins[name], tips[name], bone_elements[name] = origin, tip, elem
        if tip is not None and math.dist(origin, tip) > _EPS:
            world_angles[name] = math.degrees(math.atan2(tip[1] - origin[1], tip[0] - origin[0]))
        else:
            candidates = part_angles_by_bone.get(name, [])
            if candidates:
                first = candidates[0]
                if any(abs(value - first) > 1e-4 for value in candidates[1:]):
                    raise ValueError(
                        f"{svg_path}: zero-length bone {name!r} has inconsistent bound-art angles {candidates}"
                    )
                world_angles[name] = first
            else:
                parent = elem.get("data-rig-parent")
                world_angles[name] = world_angles.get(str(parent), 0.0) if parent else 0.0

    bones: list[BoneDefinition] = []
    for elem in raw_bones:
        name = str(elem.get("data-rig-bone-def"))
        parent = elem.get("data-rig-parent") or None
        if parent:
            if parent not in origins or parent not in world_angles:
                raise ValueError(f"{svg_path}: bone {name!r} parent {parent!r} is not defined first")
            parent_origin = origins[parent]
            parent_angle = world_angles[parent]
        else:
            parent_origin = root_anchor
            parent_angle = 0.0
        local_position = _rotate(_sub(origins[name], parent_origin), -parent_angle)
        local_rotation = world_angles[name] - parent_angle
        tip = tips[name]
        length = math.dist(origins[name], tip) if tip is not None else 0.0
        bones.append(
            BoneDefinition(
                id=name,
                parent=parent,
                rest=Transform2D(
                    position=_vec_round(local_position),
                    rotation_deg=_round(local_rotation),
                ),
                length=_round(length),
                origin=_vec_round(origins[name]),
                tip=_vec_round(tip) if tip is not None else None,
                origin_marker=str(elem.get("data-rig-origin")),
                tip_marker=str(elem.get("data-rig-tip")) if elem.get("data-rig-tip") else None,
            )
        )

    parts: list[PartDefinition] = []
    for elem in raw_parts:
        name = str(elem.get("data-rig-part-def"))
        bone = str(elem.get("data-rig-bone"))
        pivot_id = elem.get("data-rig-pivot")
        if not pivot_id or pivot_id not in ids:
            raise ValueError(f"{svg_path}: part {name!r} lacks valid bind pivot")
        parts.append(
            PartDefinition(
                id=name,
                bone=bone,
                z=float(elem.get("data-rig-z", "0")),
                elements=tuple((elem.get("data-rig-elements") or "").split()),
                pivot=_vec_round(_element_point_in_root(root, ids[pivot_id])),
                pivot_marker=pivot_id,
                bind_world_rotation_deg=float(elem.get("data-rig-bind-angle", "0")),
                opacity_parameter=elem.get("data-rig-opacity") or None,
            )
        )

    rig = RigDefinition(
        source_svg=svg_path,
        view_id=str(view.get("data-rig-view-def")),
        source_layer=str(view.get("data-rig-source-layer") or ""),
        source_label=str(view.get("data-rig-source-label") or ""),
        profile=str(view.get("data-rig-profile") or "custom-articulated-v1"),
        projection=str(view.get("data-rig-projection") or "unspecified"),
        facing=view.get("data-rig-facing") or None,
        root_anchor=_vec_round(root_anchor),
        bones=tuple(bones),
        parts=tuple(parts),
    )
    errors = rig.validate()
    if errors:
        raise ValueError(f"{svg_path}: invalid rig definition: {'; '.join(errors)}")
    return rig


@dataclass(frozen=True)
class PoseState:
    root: Transform2D = Transform2D()
    bones: Mapping[str, Transform2D] = field(default_factory=dict)
    parameters: Mapping[str, float] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any] | None) -> "PoseState":
        raw = raw or {}
        return cls(
            root=Transform2D.from_dict(raw.get("root")),
            bones={
                str(name): Transform2D.from_dict(value)
                for name, value in (raw.get("bones") or {}).items()
            },
            parameters={str(name): float(value) for name, value in (raw.get("parameters") or {}).items()},
        )

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        root = self.root.to_dict(sparse=True)
        if root:
            out["root"] = root
        bones = {
            name: transform.to_dict(sparse=True)
            for name, transform in sorted(self.bones.items())
            if transform.to_dict(sparse=True)
        }
        if bones:
            out["bones"] = bones
        if self.parameters:
            out["parameters"] = {
                name: _round(value) for name, value in sorted(self.parameters.items())
            }
        return out

    def patched(self, raw_patch: Mapping[str, Any] | None) -> "PoseState":
        if not raw_patch:
            return self
        root_raw = raw_patch.get("root")
        root = self.root
        if root_raw is not None:
            patch = Transform2D.from_dict(root_raw)
            root = self.root.merged(patch, root_raw)
        bones = dict(self.bones)
        for name, transform_raw in (raw_patch.get("bones") or {}).items():
            base = bones.get(str(name), Transform2D())
            patch = Transform2D.from_dict(transform_raw)
            bones[str(name)] = base.merged(patch, transform_raw)
        params = dict(self.parameters)
        params.update({str(name): float(value) for name, value in (raw_patch.get("parameters") or {}).items()})
        return PoseState(root=root, bones=bones, parameters=params)


@dataclass(frozen=True)
class PoseDefinition:
    id: str
    state: PoseState
    rig_profile: str | None = None
    source: Mapping[str, Any] = field(default_factory=dict)
    path: Path | None = None

    @classmethod
    def load(cls, path: str | Path) -> "PoseDefinition":
        path = Path(path)
        raw = json.loads(path.read_text(encoding="utf8"))
        if raw.get("schema") != POSE_SCHEMA:
            raise ValueError(f"{path}: expected schema {POSE_SCHEMA!r}")
        return cls(
            id=str(raw["id"]),
            state=PoseState.from_dict(raw.get("state")),
            rig_profile=raw.get("rig_profile"),
            source=dict(raw.get("source") or {}),
            path=path.resolve(),
        )

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"schema": POSE_SCHEMA, "id": self.id}
        if self.rig_profile:
            out["rig_profile"] = self.rig_profile
        if self.source:
            out["source"] = dict(self.source)
        out["state"] = self.state.to_dict()
        return out


@dataclass(frozen=True)
class ClipPoseKey:
    at_s: float
    pose: str | None = None
    state: PoseState | None = None
    overrides: Mapping[str, Any] = field(default_factory=dict)
    interpolation: str = "linear"
    frame: int | None = None

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "ClipPoseKey":
        pose = raw.get("pose")
        state_raw = raw.get("state")
        if (pose is None) == (state_raw is None):
            raise ValueError("clip pose key must contain exactly one of 'pose' or 'state'")
        return cls(
            at_s=float(raw["at_s"]),
            pose=str(pose) if pose is not None else None,
            state=PoseState.from_dict(state_raw) if state_raw is not None else None,
            overrides=dict(raw.get("overrides") or {}),
            interpolation=str(raw.get("interpolation", "linear")),
            frame=int(raw["frame"]) if raw.get("frame") is not None else None,
        )

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"at_s": _round(self.at_s)}
        if self.frame is not None:
            out["frame"] = self.frame
        if self.pose is not None:
            out["pose"] = self.pose
        elif self.state is not None:
            out["state"] = self.state.to_dict()
        if self.overrides:
            out["overrides"] = dict(self.overrides)
        if self.interpolation != "linear":
            out["interpolation"] = self.interpolation
        return out


@dataclass(frozen=True)
class ScalarKey:
    at_s: float
    value: float
    interpolation: str = "linear"

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "ScalarKey":
        return cls(
            at_s=float(raw["at_s"]),
            value=float(raw["value"]),
            interpolation=str(raw.get("interpolation", "linear")),
        )

    def to_dict(self) -> dict[str, Any]:
        out = {"at_s": _round(self.at_s), "value": _round(self.value)}
        if self.interpolation != "linear":
            out["interpolation"] = self.interpolation
        return out


@dataclass(frozen=True)
class ScalarTrack:
    target: str
    keys: tuple[ScalarKey, ...]

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "ScalarTrack":
        return cls(
            target=str(raw["target"]),
            keys=tuple(ScalarKey.from_dict(key) for key in raw.get("keys", [])),
        )

    def to_dict(self) -> dict[str, Any]:
        return {"target": self.target, "keys": [key.to_dict() for key in self.keys]}


@dataclass(frozen=True)
class ClipMarker:
    at_s: float
    name: str

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "ClipMarker":
        return cls(at_s=float(raw["at_s"]), name=str(raw["name"]))

    def to_dict(self) -> dict[str, Any]:
        return {"at_s": _round(self.at_s), "name": self.name}


@dataclass(frozen=True)
class ClipDefinition:
    id: str
    loop: bool
    duration_s: float
    frame_count: int
    frame_duration_ms: int
    pose_keys: tuple[ClipPoseKey, ...]
    tracks: tuple[ScalarTrack, ...] = ()
    markers: tuple[ClipMarker, ...] = ()
    source: Mapping[str, Any] = field(default_factory=dict)
    path: Path | None = None

    @classmethod
    def load(cls, path: str | Path) -> "ClipDefinition":
        path = Path(path)
        raw = json.loads(path.read_text(encoding="utf8"))
        if raw.get("schema") != CLIP_SCHEMA:
            raise ValueError(f"{path}: expected schema {CLIP_SCHEMA!r}")
        sampling = raw.get("sampling") or {}
        return cls(
            id=str(raw["id"]),
            loop=bool(raw.get("loop", False)),
            duration_s=float(raw["duration_s"]),
            frame_count=int(sampling["frame_count"]),
            frame_duration_ms=int(sampling["frame_duration_ms"]),
            pose_keys=tuple(ClipPoseKey.from_dict(key) for key in raw.get("pose_keys", [])),
            tracks=tuple(ScalarTrack.from_dict(track) for track in raw.get("tracks", [])),
            markers=tuple(ClipMarker.from_dict(marker) for marker in raw.get("markers", [])),
            source=dict(raw.get("source") or {}),
            path=path.resolve(),
        )

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "schema": CLIP_SCHEMA,
            "id": self.id,
            "loop": self.loop,
            "duration_s": _round(self.duration_s),
            "sampling": {
                "frame_count": self.frame_count,
                "frame_duration_ms": self.frame_duration_ms,
            },
        }
        if self.source:
            out["source"] = dict(self.source)
        out["pose_keys"] = [key.to_dict() for key in self.pose_keys]
        if self.tracks:
            out["tracks"] = [track.to_dict() for track in self.tracks]
        if self.markers:
            out["markers"] = [marker.to_dict() for marker in self.markers]
        return out

    @property
    def animation_span_s(self) -> float:
        if self.loop:
            return self.duration_s
        if self.frame_count <= 1:
            return max(self.duration_s, 1e-9)
        return max((self.frame_count - 1) * self.frame_duration_ms / 1000.0, 1e-9)


@dataclass(frozen=True)
class MotionLibrary:
    id: str
    rig_profile: str
    space: Mapping[str, str]
    poses: Mapping[str, PoseDefinition]
    clips: Mapping[str, ClipDefinition]
    path: Path

    @classmethod
    def load(cls, path: str | Path) -> "MotionLibrary":
        path = Path(path).resolve()
        raw = json.loads(path.read_text(encoding="utf8"))
        if raw.get("schema") != MOTION_LIBRARY_SCHEMA:
            raise ValueError(f"{path}: expected schema {MOTION_LIBRARY_SCHEMA!r}")
        poses: dict[str, PoseDefinition] = {}
        clips: dict[str, ClipDefinition] = {}
        for rel_root in raw.get("pose_roots", ["poses"]):
            root = (path.parent / rel_root).resolve()
            if root.is_dir():
                for pose_path in sorted(root.rglob("*.pose.json")):
                    pose = PoseDefinition.load(pose_path)
                    if pose.id in poses:
                        raise ValueError(f"{path}: duplicate pose id {pose.id!r}")
                    poses[pose.id] = pose
        for rel_root in raw.get("clip_roots", ["clips"]):
            root = (path.parent / rel_root).resolve()
            if root.is_dir():
                for clip_path in sorted(root.rglob("*.clip.json")):
                    clip = ClipDefinition.load(clip_path)
                    if clip.id in clips:
                        raise ValueError(f"{path}: duplicate clip id {clip.id!r}")
                    clips[clip.id] = clip
        space = dict(raw.get("space") or {})
        if space != MOTION_SPACE_V1:
            raise ValueError(
                f"{path}: unsupported or missing motion space contract {space!r}; "
                f"expected {MOTION_SPACE_V1!r}"
            )
        library = cls(
            id=str(raw["id"]),
            rig_profile=str(raw["rig_profile"]),
            space=space,
            poses=poses,
            clips=clips,
            path=path,
        )
        errors = library.validate()
        if errors:
            raise ValueError(f"{path}: invalid motion library: {'; '.join(errors)}")
        return library

    def validate(self, rig: RigDefinition | None = None) -> list[str]:
        errors: list[str] = []
        allowed_interpolation = {"linear", "smooth", "in", "out", "sine", "hold"}
        rig_bones = set(rig.bone_by_id) if rig is not None else None

        def validate_state(label: str, state: PoseState) -> None:
            if rig_bones is not None:
                unknown = sorted(set(state.bones) - rig_bones)
                if unknown:
                    errors.append(f"{label} references unknown bones {unknown}")
            values = [
                *state.root.position,
                state.root.rotation_deg,
                *state.root.scale,
                *state.parameters.values(),
            ]
            for transform in state.bones.values():
                values.extend([*transform.position, transform.rotation_deg, *transform.scale])
            if any(not math.isfinite(float(value)) for value in values):
                errors.append(f"{label} contains non-finite transform/parameter values")

        for pose in self.poses.values():
            if pose.rig_profile and pose.rig_profile != self.rig_profile:
                errors.append(
                    f"pose {pose.id!r} profile {pose.rig_profile!r} != library profile {self.rig_profile!r}"
                )
            validate_state(f"pose {pose.id!r}", pose.state)

        for clip in self.clips.values():
            if clip.frame_count < 1 or clip.frame_duration_ms <= 0 or clip.duration_s <= 0:
                errors.append(f"clip {clip.id!r} has invalid sampling/duration")
            last = -math.inf
            for index, key in enumerate(clip.pose_keys):
                if key.at_s < last - _EPS:
                    errors.append(f"clip {clip.id!r} pose keys are not time-sorted")
                    break
                last = key.at_s
                if key.at_s < -_EPS or key.at_s > clip.duration_s + _EPS:
                    errors.append(f"clip {clip.id!r} key at {key.at_s} lies outside duration")
                if key.interpolation not in allowed_interpolation:
                    errors.append(
                        f"clip {clip.id!r} uses unsupported interpolation {key.interpolation!r}"
                    )
                if key.pose and key.pose not in self.poses:
                    errors.append(f"clip {clip.id!r} references missing pose {key.pose!r}")
                if key.state is not None:
                    validate_state(f"clip {clip.id!r} key {index}", key.state)
                if key.overrides:
                    validate_state(
                        f"clip {clip.id!r} key {index} overrides",
                        PoseState.from_dict(key.overrides),
                    )

            seen_targets: set[str] = set()
            for track in clip.tracks:
                if track.target in seen_targets:
                    errors.append(f"clip {clip.id!r} repeats track target {track.target!r}")
                seen_targets.add(track.target)
                if not track.keys:
                    errors.append(f"clip {clip.id!r} track {track.target!r} has no keys")
                    continue
                track_last = -math.inf
                for key in track.keys:
                    if key.at_s < track_last - _EPS:
                        errors.append(
                            f"clip {clip.id!r} track {track.target!r} keys are not time-sorted"
                        )
                        break
                    track_last = key.at_s
                    if key.at_s < -_EPS or key.at_s > clip.duration_s + _EPS:
                        errors.append(
                            f"clip {clip.id!r} track {track.target!r} key at {key.at_s} lies outside duration"
                        )
                    if key.interpolation not in allowed_interpolation:
                        errors.append(
                            f"clip {clip.id!r} track {track.target!r} uses unsupported interpolation {key.interpolation!r}"
                        )
                    if not math.isfinite(key.value):
                        errors.append(
                            f"clip {clip.id!r} track {track.target!r} contains a non-finite value"
                        )
                if rig_bones is not None:
                    match = re.fullmatch(
                        r"bone\.([^.]+)\.(?:position\.[xy]|rotation_deg|scale\.[xy])",
                        track.target,
                    )
                    if match and match.group(1) not in rig_bones:
                        errors.append(
                            f"clip {clip.id!r} track {track.target!r} references unknown bone"
                        )
        return errors

    def resolve_pose_key(self, key: ClipPoseKey) -> PoseState:
        if key.pose is not None:
            state = self.poses[key.pose].state
        elif key.state is not None:
            state = key.state
        else:  # pragma: no cover - constructor validation
            raise ValueError("pose key has no source")
        return state.patched(key.overrides)


@dataclass(frozen=True)
class RenderBinding:
    frame_width_px: int
    frame_height_px: int
    root_anchor_px: Point
    frame_px_per_rig_unit: float
    supersample: int = 4
    render_scale: int = 1
    ankle_h_px: float = 0.0
    svg_ref_dpi: float = 96.0

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "RenderBinding":
        return cls(
            frame_width_px=int(raw["frame_px"][0]),
            frame_height_px=int(raw["frame_px"][1]),
            root_anchor_px=tuple(float(v) for v in raw["root_anchor_px"]),  # type: ignore[arg-type]
            frame_px_per_rig_unit=float(raw["frame_px_per_rig_unit"]),
            supersample=int(raw.get("supersample", 4)),
            render_scale=int(raw.get("render_scale", 1)),
            ankle_h_px=float(raw.get("ankle_h_px", 0.0)),
            svg_ref_dpi=float(raw.get("svg_ref_dpi", 96.0)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "frame_px": [self.frame_width_px, self.frame_height_px],
            "root_anchor_px": list(_vec_round(self.root_anchor_px)),
            "frame_px_per_rig_unit": _round(self.frame_px_per_rig_unit, 9),
            "supersample": self.supersample,
            "render_scale": self.render_scale,
            "ankle_h_px": _round(self.ankle_h_px),
            "svg_ref_dpi": _round(self.svg_ref_dpi),
        }


@dataclass(frozen=True)
class CharacterMotionBinding:
    character: str
    rig_svg: Path
    rig_view: str
    library_path: Path
    render: RenderBinding
    sprite_tuning: Mapping[str, Any]
    features: Mapping[str, Any]
    natural_pose: str
    path: Path

    @classmethod
    def load(cls, path: str | Path) -> "CharacterMotionBinding":
        path = Path(path).resolve()
        raw = json.loads(path.read_text(encoding="utf8"))
        if raw.get("schema") != MOTION_BINDING_SCHEMA:
            raise ValueError(f"{path}: expected schema {MOTION_BINDING_SCHEMA!r}")
        rig = raw["rig"]
        return cls(
            character=str(raw["character"]),
            rig_svg=(path.parent / rig["svg"]).resolve(),
            rig_view=str(rig["view"]),
            library_path=(path.parent / raw["motion_library"]).resolve(),
            render=RenderBinding.from_dict(raw["render"]),
            sprite_tuning=dict(raw.get("sprite_tuning") or {}),
            features=dict(raw.get("features") or {}),
            natural_pose=str(raw.get("natural_pose", "idle")),
            path=path,
        )

    def load_prepared(self) -> "PreparedCharacterMotion":
        rig = load_svg_rig_definition(self.rig_svg, view_id=self.rig_view)
        library = MotionLibrary.load(self.library_path)
        errors = library.validate(rig)
        if rig.profile != library.rig_profile:
            errors.append(
                f"rig profile {rig.profile!r} does not match motion library {library.rig_profile!r}"
            )
        if errors:
            raise ValueError(f"{self.path}: {'; '.join(errors)}")
        return PreparedCharacterMotion(binding=self, rig=rig, library=library)


def _target_to_legacy_channel(target: str) -> str:
    if target == "root.position.x":
        return "root_x"
    if target == "root.position.y":
        return "root_y"
    match = re.fullmatch(r"bone\.([^.]+)\.rotation_deg", target)
    if match:
        return match.group(1)
    match = re.fullmatch(r"bone\.([^.]+)\.position\.([xy])", target)
    if match:
        return f"bone.{match.group(1)}.{match.group(2)}"
    match = re.fullmatch(r"parameter\.(.+)", target)
    if match:
        return match.group(1)
    raise ValueError(f"legacy renderer projection cannot represent track target {target!r}")


def _legacy_ease(name: str) -> str:
    if name not in {"linear", "smooth", "in", "out", "sine", "hold"}:
        raise ValueError(f"legacy RigDocument projection cannot represent interpolation {name!r}")
    return name


@dataclass(frozen=True)
class PreparedCharacterMotion:
    binding: CharacterMotionBinding
    rig: RigDefinition
    library: MotionLibrary

    def _rig_to_frame_delta(self, point: Point) -> Point:
        return _mul(point, self.binding.render.frame_px_per_rig_unit)

    def _rig_to_frame_point(self, point: Point) -> Point:
        return _add(
            self.binding.render.root_anchor_px,
            self._rig_to_frame_delta(_sub(point, self.rig.root_anchor)),
        )

    def _part_reference_pivot(self, part: PartDefinition) -> Point:
        reference = svg_reference_space(self.rig.source_svg, dpi=self.binding.render.svg_ref_dpi)
        return reference.user_to_reference(part.pivot)

    def to_rig_document(self):
        """Build the current renderer's ``RigDocument`` as a disposable projection.

        The neutral IR can grow beyond what RigDocument can express.  Reject
        unsupported transforms here instead of silently dropping semantics.
        """

        from .rigdoc import RigDocument

        for clip in self.library.clips.values():
            for key in clip.pose_keys:
                state = self.library.resolve_pose_key(key)
                transforms = [("root", state.root), *state.bones.items()]
                for label, transform in transforms:
                    if label == "root" and abs(transform.rotation_deg) > _EPS:
                        raise ValueError(
                            f"clip {clip.id!r}: legacy renderer projection cannot represent root rotation"
                        )
                    if any(abs(v - 1.0) > _EPS for v in transform.scale):
                        raise ValueError(
                            f"clip {clip.id!r}: legacy renderer projection cannot represent scale on {label!r}"
                        )

        render = self.binding.render
        scale = render.frame_px_per_rig_unit
        reference = svg_reference_space(self.rig.source_svg, dpi=render.svg_ref_dpi)
        frame_per_reference_px = scale / reference.reference_px_per_user_x
        data: dict[str, Any] = {
            "name": self.binding.character,
            "frame": {
                "width": render.frame_width_px,
                "height": render.frame_height_px,
                "ground_y": render.root_anchor_px[1],
                "center_x": render.root_anchor_px[0],
                "ankle_h": render.ankle_h_px,
                "supersample": render.supersample,
                "render_scale": render.render_scale,
            },
            "svg_source": {
                "path": str(self.rig.source_svg),
                "view": self.rig.source_label,
                "ref_dpi": render.svg_ref_dpi,
                "scale": frame_per_reference_px,
            },
            "palette": {},
            "bones": [],
            "parts": [],
            "ik_legs": [],
            "ik_chains": [],
            "clips": {},
            "sprite_tuning": dict(self.binding.sprite_tuning),
            "features": dict(self.binding.features),
            "natural_pose": {"clip": self.binding.natural_pose},
            "generated_projection": {
                "schema": LEGACY_PROJECTION_SCHEMA,
                "source": str(self.binding.path),
                "note": "Disposable compatibility projection; edit SVG rig metadata and motion JSON instead.",
            },
        }
        for bone in self.rig.bones:
            data["bones"].append(
                {
                    "name": bone.id,
                    "parent": bone.parent,
                    "offset": list(_vec_round(self._rig_to_frame_delta(bone.rest.position))),
                    "length": _round(bone.length * scale),
                    "rest_angle": _round(bone.rest.rotation_deg),
                }
            )
        for part in self.rig.parts:
            pivot = self._part_reference_pivot(part)
            item: dict[str, Any] = {
                "name": part.id,
                "bone": part.bone,
                "z": part.z,
                "kind": "sprite",
                "include": list(part.elements),
                "pivot": list(_vec_round(pivot)),
                "rest_angle": _round(part.bind_world_rotation_deg),
            }
            if part.opacity_parameter:
                item["opacity_channel"] = part.opacity_parameter
            data["parts"].append(item)

        for clip_name, clip in self.library.clips.items():
            # Resolve the complete pose state first.  Sparse authored poses are
            # excellent source data, but the compatibility projection needs a
            # value at every key for every channel that appears anywhere in the
            # clip.  Otherwise a translation that returns to rest can vanish
            # from the sparse key and RigDocument will keep interpolating the
            # preceding nonzero value.
            resolved_keys: list[tuple[float, str, PoseState]] = []
            translated_channels: set[str] = set()
            parameter_channels: set[str] = set()
            for pose_key in clip.pose_keys:
                state = self.library.resolve_pose_key(pose_key)
                # Motion keys live in authored clip time.  Sprite sampling is a
                # separate publication concern, so the compatibility projection
                # normalizes every key against duration_s rather than against the
                # old frame-count/frame-duration sampling table.
                t = pose_key.at_s / max(clip.duration_s, 1e-9)
                t = max(0.0, min(1.0, t))
                ease = _legacy_ease(pose_key.interpolation)
                resolved_keys.append((t, ease, state))
                parameter_channels.update(state.parameters)
                for bone in self.rig.bones:
                    delta = state.bones.get(bone.id, Transform2D())
                    if abs(delta.position[0]) > _EPS:
                        translated_channels.add(f"bone.{bone.id}.x")
                    if abs(delta.position[1]) > _EPS:
                        translated_channels.add(f"bone.{bone.id}.y")

            pose_channels = {
                "root_x",
                "root_y",
                *(bone.id for bone in self.rig.bones),
                *translated_channels,
                *parameter_channels,
            }
            channel_keys: dict[str, list[list[Any]]] = {
                name: [] for name in sorted(pose_channels)
            }
            for t, ease, state in resolved_keys:
                values: dict[str, float] = {
                    "root_x": state.root.position[0] * scale,
                    "root_y": state.root.position[1] * scale,
                }
                for bone in self.rig.bones:
                    delta = state.bones.get(bone.id, Transform2D())
                    values[bone.id] = delta.rotation_deg
                    values[f"bone.{bone.id}.x"] = delta.position[0] * scale
                    values[f"bone.{bone.id}.y"] = delta.position[1] * scale
                values.update(state.parameters)
                for channel in channel_keys:
                    channel_keys[channel].append(
                        [_round(t, 9), _round(values.get(channel, 0.0)), ease]
                    )

            for track in clip.tracks:
                channel = _target_to_legacy_channel(track.target)
                keys: list[list[Any]] = []
                for key in track.keys:
                    t = key.at_s / max(clip.duration_s, 1e-9)
                    value = key.value
                    if track.target.endswith("position.x") or track.target.endswith("position.y"):
                        value *= scale
                    keys.append([_round(t, 9), _round(value), _legacy_ease(key.interpolation)])
                channel_keys[channel] = keys

            data["clips"][clip_name] = {
                "loop": clip.loop,
                "frames": clip.frame_count,
                "duration_ms": clip.frame_duration_ms,
                "channels": {
                    name: {"keys": keys} for name, keys in sorted(channel_keys.items())
                },
            }

        return RigDocument(data, source_path=self.binding.path)

    def write_legacy_projection(self, path: str | Path) -> Path:
        doc = self.to_rig_document()
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        doc.save(path)
        return path


def _legacy_rest_world(doc) -> Mapping[str, Any]:
    frame = doc.frame
    root = (
        float(frame.get("center_x", frame["width"] / 2)),
        float(frame.get("ground_y", frame["height"] - 2)),
    )
    return doc.build_skeleton().world(root=root)


def fit_legacy_render_binding(doc, rig: RigDefinition) -> RenderBinding:
    """Fit the old frame-pixel projection onto the marker-authoritative SVG rig.

    Prefer the legacy SVG raster scale when it is compatible with the marker
    geometry.  That value is part of the existing publication contract and
    retaining it avoids tiny raster resampling differences during migration.
    Least-squares fitting is only a fallback for legacy documents whose raster
    declaration cannot explain their authored skeleton.
    """

    legacy_world = _legacy_rest_world(doc)
    frame = doc.frame
    frame_root = (
        float(frame.get("center_x", frame["width"] / 2)),
        float(frame.get("ground_y", frame["height"] - 2)),
    )

    def max_residual(scale: float) -> float:
        residual = 0.0
        for bone in rig.bones:
            if bone.id not in legacy_world:
                continue
            predicted = _add(frame_root, _mul(_sub(bone.origin, rig.root_anchor), scale))
            residual = max(residual, math.dist(predicted, legacy_world[bone.id].origin))
        return residual

    scale: float | None = None
    try:
        reference = svg_reference_space(
            rig.source_svg, dpi=float(doc.svg_source.get("ref_dpi", 96.0))
        )
        declared = float(doc.svg_source["scale"]) * reference.reference_px_per_user_x
    except (KeyError, TypeError, ValueError):
        declared = 0.0
    if declared > 0.0 and max_residual(declared) <= 0.05:
        scale = declared

    if scale is None:
        numerator = 0.0
        denominator = 0.0
        for bone in rig.bones:
            if bone.id not in legacy_world:
                continue
            rig_vec = _sub(bone.origin, rig.root_anchor)
            frame_vec = _sub(legacy_world[bone.id].origin, frame_root)
            numerator += rig_vec[0] * frame_vec[0] + rig_vec[1] * frame_vec[1]
            denominator += rig_vec[0] ** 2 + rig_vec[1] ** 2
            if bone.tip is not None:
                rig_tip_vec = _sub(bone.tip, rig.root_anchor)
                frame_tip = legacy_world[bone.id].tip
                frame_tip_vec = _sub(frame_tip, frame_root)
                numerator += rig_tip_vec[0] * frame_tip_vec[0] + rig_tip_vec[1] * frame_tip_vec[1]
                denominator += rig_tip_vec[0] ** 2 + rig_tip_vec[1] ** 2
        if denominator <= _EPS:
            raise ValueError("cannot fit render scale from a degenerate rig")
        scale = numerator / denominator

    if scale <= 0:
        raise ValueError(f"legacy rig maps to non-positive frame scale {scale}")
    residual = max_residual(scale)
    if residual > 0.05:
        raise ValueError(
            f"legacy rig and SVG markers do not share one frame projection; max rest residual={residual:.4f}px"
        )

    return RenderBinding(
        frame_width_px=int(frame["width"]),
        frame_height_px=int(frame["height"]),
        root_anchor_px=frame_root,
        frame_px_per_rig_unit=scale,
        supersample=int(frame.get("supersample", 4)),
        render_scale=int(frame.get("render_scale", 1)),
        ankle_h_px=float(frame.get("ankle_h", 0.0)),
        svg_ref_dpi=float(doc.svg_source.get("ref_dpi", 96.0)),
    )


def _frame_point_to_rig(point: Point, *, rig: RigDefinition, render: RenderBinding) -> Point:
    return _add(
        rig.root_anchor,
        _mul(_sub(point, render.root_anchor_px), 1.0 / render.frame_px_per_rig_unit),
    )


def _free_legacy_parameters(doc, sampled: Mapping[str, float]) -> dict[str, float]:
    bones = set(doc.build_skeleton().bones)
    prefixes = {
        str(item.get("channel_prefix"))
        for item in [*doc.ik_legs, *doc.ik_chains]
        if item.get("channel_prefix")
    }
    out: dict[str, float] = {}
    for name, value in sampled.items():
        if name in bones or name in {"root_x", "root_y"}:
            continue
        if re.fullmatch(r"bone\.[^.]+\.[xy]", name):
            continue
        if any(name.startswith(f"{prefix}_") for prefix in prefixes):
            continue
        out[name] = float(value)
    return out


def bake_legacy_pose_state(doc, rig: RigDefinition, render: RenderBinding, clip_name: str, t: float) -> PoseState:
    """Bake one legacy solver result into direct rest-relative FK transforms."""

    world, sampled = doc.solve(clip_name, t)
    bones_by_id = rig.bone_by_id
    root_position = (
        float(sampled.get("root_x", 0.0)) / render.frame_px_per_rig_unit,
        float(sampled.get("root_y", 0.0)) / render.frame_px_per_rig_unit,
    )
    deltas: dict[str, Transform2D] = {}
    for bone in rig.bones:
        actual = world[bone.id]
        actual_origin = _frame_point_to_rig(actual.origin, rig=rig, render=render)
        if bone.parent:
            parent_world = world[bone.parent]
            parent_origin = _frame_point_to_rig(parent_world.origin, rig=rig, render=render)
            parent_angle = parent_world.angle
        else:
            parent_origin = _add(rig.root_anchor, root_position)
            parent_angle = 0.0
        local_position = _rotate(_sub(actual_origin, parent_origin), -parent_angle)
        local_angle = actual.angle - parent_angle
        position_delta = _sub(local_position, bone.rest.position)
        # Solving an IK chain and decomposing it back into FK creates tiny
        # floating-point attachment residuals.  They are many orders below a
        # source pixel and should not become authored pose translations.
        position_delta = tuple(0.0 if abs(v) < 1e-4 else v for v in position_delta)
        rotation_delta = local_angle - bone.rest.rotation_deg
        if abs(rotation_delta) < 1e-5:
            rotation_delta = 0.0
        transform = Transform2D(
            position=_vec_round(position_delta),
            rotation_deg=_round(rotation_delta),
        )
        if transform.to_dict(sparse=True):
            deltas[bone.id] = transform
    return PoseState(
        root=Transform2D(position=_vec_round(root_position)),
        bones=deltas,
        parameters=_free_legacy_parameters(doc, sampled),
    )


def bake_legacy_clip(doc, rig: RigDefinition, render: RenderBinding, clip_name: str) -> ClipDefinition:
    source = doc.clips[clip_name]
    frames = max(1, int(source.get("frames", 1)))
    frame_duration_ms = int(source.get("duration_ms", 100))
    loop = bool(source.get("loop", True))
    keys: list[ClipPoseKey] = []
    for frame in range(frames):
        t = doc.frame_time(clip_name, frame, frames)
        state = bake_legacy_pose_state(doc, rig, render, clip_name, t)
        keys.append(
            ClipPoseKey(
                at_s=frame * frame_duration_ms / 1000.0,
                frame=frame,
                state=state,
                interpolation="linear",
            )
        )
    return ClipDefinition(
        id=clip_name,
        loop=loop,
        duration_s=frames * frame_duration_ms / 1000.0,
        frame_count=frames,
        frame_duration_ms=frame_duration_ms,
        pose_keys=tuple(keys),
        source={
            "kind": "legacy-rigdoc-bake",
            "clip": clip_name,
            "baked_at": "published-frame-samples",
            "note": "IK, expressions, and solver controls were baked to direct FK pose transforms.",
        },
    )


def write_json(path: str | Path, data: Mapping[str, Any]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n", encoding="utf8")
    return path


def _pose_filename(pose_id: str) -> str:
    return pose_id.replace("/", "__") + ".pose.json"


def bake_legacy_motion_library(
    doc,
    rig: RigDefinition,
    *,
    library_id: str,
    out_dir: str | Path,
    canonical_poses: Mapping[str, tuple[str, int]] | None = None,
) -> tuple[RenderBinding, Path]:
    """Bake a legacy rig's complete published clip vocabulary into motion JSON.

    ``canonical_poses`` maps reusable pose ids to ``(clip, frame)``.  The exact
    key that supplied a canonical pose is rewritten as a pose reference so the
    pilot exercises real pose reuse rather than merely defining unused files.
    """

    out_dir = Path(out_dir)
    poses_dir = out_dir / "poses"
    clips_dir = out_dir / "clips"
    render = fit_legacy_render_binding(doc, rig)
    baked = {
        name: bake_legacy_clip(doc, rig, render, name) for name in doc.clips
    }

    canonical_poses = dict(canonical_poses or {})
    by_source: dict[tuple[str, int], str] = {}
    for pose_id, (clip_name, frame) in canonical_poses.items():
        if clip_name not in baked:
            raise ValueError(f"canonical pose {pose_id!r} references unknown clip {clip_name!r}")
        clip = baked[clip_name]
        if frame < 0 or frame >= len(clip.pose_keys):
            raise ValueError(f"canonical pose {pose_id!r} frame {frame} outside clip {clip_name!r}")
        state = clip.pose_keys[frame].state
        if state is None:
            raise ValueError("legacy bake unexpectedly produced a pose reference")
        pose = PoseDefinition(
            id=pose_id,
            state=PoseState(root=state.root, bones=state.bones),
            rig_profile=rig.profile,
            source={"clip": clip_name, "frame": frame, "kind": "promoted-legacy-pose"},
        )
        write_json(poses_dir / _pose_filename(pose_id), pose.to_dict())
        by_source[(clip_name, frame)] = pose_id

    for clip_name, clip in baked.items():
        rewritten: list[ClipPoseKey] = []
        for index, key in enumerate(clip.pose_keys):
            pose_id = by_source.get((clip_name, index))
            if pose_id is None:
                rewritten.append(key)
                continue
            # Preserve clip-only scalar parameters as an override; canonical
            # reusable poses contain body transforms only.
            state = key.state or PoseState()
            overrides: dict[str, Any] = {}
            if state.parameters:
                overrides["parameters"] = dict(state.parameters)
            rewritten.append(
                ClipPoseKey(
                    at_s=key.at_s,
                    frame=key.frame,
                    pose=pose_id,
                    overrides=overrides,
                    interpolation=key.interpolation,
                )
            )
        rewritten_clip = ClipDefinition(
            id=clip.id,
            loop=clip.loop,
            duration_s=clip.duration_s,
            frame_count=clip.frame_count,
            frame_duration_ms=clip.frame_duration_ms,
            pose_keys=tuple(rewritten),
            tracks=clip.tracks,
            markers=clip.markers,
            source=clip.source,
        )
        write_json(clips_dir / f"{clip_name}.clip.json", rewritten_clip.to_dict())

    manifest = {
        "schema": MOTION_LIBRARY_SCHEMA,
        "id": library_id,
        "rig_profile": rig.profile,
        "space": dict(MOTION_SPACE_V1),
        "pose_roots": ["poses"],
        "clip_roots": ["clips"],
    }
    manifest_path = write_json(out_dir / "library.json", manifest)
    return render, manifest_path


def binding_dict(
    *,
    character: str,
    svg_relpath: str,
    view: str,
    library_relpath: str,
    render: RenderBinding,
    sprite_tuning: Mapping[str, Any] | None = None,
    features: Mapping[str, Any] | None = None,
    natural_pose: str = "idle",
) -> dict[str, Any]:
    return {
        "schema": MOTION_BINDING_SCHEMA,
        "character": character,
        "rig": {"svg": svg_relpath, "view": view},
        "motion_library": library_relpath,
        "render": render.to_dict(),
        "sprite_tuning": dict(sprite_tuning or {}),
        "features": dict(features or {}),
        "natural_pose": natural_pose,
    }


__all__ = [
    "CLIP_SCHEMA",
    "LEGACY_PROJECTION_SCHEMA",
    "MOTION_BINDING_SCHEMA",
    "MOTION_LIBRARY_SCHEMA",
    "MOTION_SPACE_V1",
    "POSE_SCHEMA",
    "BoneDefinition",
    "CharacterMotionBinding",
    "ClipDefinition",
    "ClipMarker",
    "ClipPoseKey",
    "MotionLibrary",
    "PartDefinition",
    "PoseDefinition",
    "PoseState",
    "PreparedCharacterMotion",
    "RenderBinding",
    "RigDefinition",
    "ScalarKey",
    "ScalarTrack",
    "Transform2D",
    "bake_legacy_clip",
    "bake_legacy_motion_library",
    "bake_legacy_pose_state",
    "binding_dict",
    "fit_legacy_render_binding",
    "load_svg_rig_definition",
    "svg_reference_space",
    "write_json",
]
