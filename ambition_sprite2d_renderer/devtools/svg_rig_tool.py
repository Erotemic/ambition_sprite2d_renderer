"""Inspect and make small, source-preserving edits to Ambition rig SVGs.

The v1 SVG-rig catalog deliberately lives *inside* the SVG but outside artwork
views.  Existing renderers therefore keep seeing the same source layers while a
future renderer, Godot bridge, or PySide editor can read one backend-neutral
static-rig description:

* ``<metadata id="ambition-rig-metadata">`` describes views, bones, parts, and
  the exact SVG element ids that make up each rigid visual part.
* ``<g id="ambition-rig-markers">`` contains editor-visible joint and per-part
  bind-pivot markers in root SVG coordinates.  It is not nested under an art
  view, so legacy view extraction never publishes it.

This module is intentionally useful to coding agents.  ``summary`` emits a
compact text representation, ``move-marker`` changes one pivot without
reserializing the SVG, and ``nudge-part`` moves rigid artwork relative to its
fixed bind/joint geometry. ``translate-part-source`` moves artwork and its bind
pivot together when an author only wants to reorganize source layout.
``validate`` catches dangling ids, malformed topology, and marker coordinate
space mistakes before a renderer has to interpret the file.

The catalog is character-authored data.  It does not define gameplay semantics,
animation clips, or Godot resources.
"""

from __future__ import annotations

import argparse
import io
import math
import re
import statistics
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

INK_NS = "http://www.inkscape.org/namespaces/inkscape"
INK_LABEL = f"{{{INK_NS}}}label"
SVG_NS = "http://www.w3.org/2000/svg"

BEGIN = "<!-- BEGIN AMBITION SVG RIG v1 -->"
END = "<!-- END AMBITION SVG RIG v1 -->"

SCHEMA = "ambition-svg-rig-v1"
RIG_METADATA_ID = "ambition-rig-metadata"
MARKER_LAYER_ID = "ambition-rig-markers"

# Hand-drawn art under `assets/` that a rig in `data/characters/` was derived
# from. It is a source, not a renderable rig and not an inert reference: an
# author edits the drawing here and the rig carries the rig vocabulary.
RIG_TEMPLATE_NAMES = frozenset(
    {
        "author-rig-labels-joints.svg",
        "officer.svg",
        # Annotated source art: these two already carry the rig VOCABULARY (part
        # groups and a `rig-joints` layer) but not the managed catalog block,
        # which `rigbuild.annotated_side_rig` derives into `data/characters/`.
        "medic.svg",
        "performer.svg",
    }
)

_NUMBER = re.compile(r"^-?(?:\d+(?:\.\d*)?|\.\d+)$")
_ID_ATTR = re.compile(r"\bid\s*=\s*(['\"])(?P<value>.*?)\1", re.DOTALL)


@dataclass(frozen=True)
class BoneGeometry:
    name: str
    parent: str | None
    rest_offset: tuple[float, float]
    rest_angle: float
    length: float
    origin: tuple[float, float]
    tip: tuple[float, float] | None
    origin_marker_id: str | None = None
    tip_marker_id: str | None = None


@dataclass(frozen=True)
class ViewCatalog:
    view_id: str
    source_label: str
    source_layer_id: str
    root_anchor: tuple[float, float]
    projection: str
    profile: str
    facing: str | None
    pose_authority: str
    part_order: str
    side_map: str | None
    bones: tuple[BoneGeometry, ...]
    parts: tuple[dict, ...]


def _local(tag: object) -> str:
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def _fmt(value: float) -> str:
    text = f"{float(value):.6f}".rstrip("0").rstrip(".")
    return "0" if text in {"", "-0"} else text


def _slug(text: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return value or "view"


def _projection_from_label(label: str) -> str:
    low = label.lower()
    if "three quarter" in low or "three-quarter" in low:
        return "three-quarter"
    if "front right" in low or "front left" in low:
        return "three-quarter"
    if "front" in low:
        return "front"
    if "side" in low:
        return "side"
    return "unspecified"


def _view_id_from_label(label: str, *, existing: set[str]) -> str:
    projection = _projection_from_label(label)
    if projection == "three-quarter":
        candidate = "three_quarter"
    elif projection in {"front", "side"}:
        candidate = projection
    else:
        candidate = _slug(label)
    if candidate not in existing:
        return candidate
    full = _slug(label)
    if full not in existing:
        return full
    i = 2
    while f"{full}_{i}" in existing:
        i += 1
    return f"{full}_{i}"


def _profile_for_bones(names: set[str]) -> str:
    standard = {
        "pelvis", "torso", "head",
        "near_arm_u", "near_arm_l", "near_arm_hand",
        "far_arm_u", "far_arm_l", "far_arm_hand",
        "near_leg_u", "near_leg_l", "near_leg_foot",
        "far_leg_u", "far_leg_l", "far_leg_foot",
    }
    legacy = {
        "pelvis", "torso", "head",
        "l_arm_u", "l_arm_l", "r_arm_u", "r_arm_l",
        "l_leg_u", "l_leg_l", "r_leg_u", "r_leg_l",
    }
    if standard <= names:
        return "humanoid-articulated-v1"
    if legacy <= names:
        return "articulated-biped-v1"
    return "custom-articulated-v1"


def _world_bones(doc: Mapping[str, object]) -> dict[str, tuple[tuple[float, float], float, float]]:
    bones = {str(b["name"]): b for b in doc.get("bones", [])}  # type: ignore[index]
    frame = doc["frame"]  # type: ignore[index]
    root = (
        float(frame.get("center_x", float(frame["width"]) / 2.0)),  # type: ignore[union-attr,index]
        float(frame["ground_y"]),  # type: ignore[index]
    )
    out: dict[str, tuple[tuple[float, float], float, float]] = {}

    def solve(name: str) -> tuple[tuple[float, float], float, float]:
        if name in out:
            return out[name]
        bone = bones[name]
        parent = bone.get("parent")
        if parent:
            parent_origin, parent_angle, _ = solve(str(parent))
        else:
            parent_origin, parent_angle = root, 0.0
        ox, oy = (float(v) for v in bone.get("offset", (0.0, 0.0)))
        angle = math.radians(parent_angle)
        origin = (
            parent_origin[0] + ox * math.cos(angle) - oy * math.sin(angle),
            parent_origin[1] + ox * math.sin(angle) + oy * math.cos(angle),
        )
        world_angle = parent_angle + float(bone.get("rest_angle", 0.0))
        length = float(bone.get("length", 0.0))
        out[name] = (origin, world_angle, length)
        return out[name]

    for name in bones:
        solve(name)
    return out


@dataclass(frozen=True)
class SvgReferenceSpace:
    """Mapping between RigDocument reference pixels and root SVG user units.

    ``RigDocument`` pivots are measured in pixels after rasterizing the complete
    SVG at ``ref_dpi``.  That is *not* necessarily the root ``viewBox`` space:
    a 210 mm document at 96 dpi has about 3.78 reference pixels per SVG user
    unit, while the Fighting Polygon documents deliberately map 900 user units
    to 900 reference pixels.  Editor markers live in root SVG user space, so the
    conversion must be explicit.
    """

    viewbox: tuple[float, float, float, float]
    px_per_user_x: float
    px_per_user_y: float

    @property
    def width_px(self) -> float:
        return self.viewbox[2] * self.px_per_user_x

    @property
    def height_px(self) -> float:
        return self.viewbox[3] * self.px_per_user_y

    def reference_to_user(self, point: tuple[float, float]) -> tuple[float, float]:
        vx, vy, _vw, _vh = self.viewbox
        return (
            vx + point[0] / self.px_per_user_x,
            vy + point[1] / self.px_per_user_y,
        )


def _root_viewbox(svg_path: Path) -> tuple[float, float, float, float] | None:
    root = ET.parse(svg_path).getroot()
    raw = root.get("viewBox")
    if not raw:
        return None
    vals = [float(v) for v in raw.replace(",", " ").split()]
    return tuple(vals) if len(vals) == 4 else None  # type: ignore[return-value]


def _length_to_reference_px(raw: str | None, *, dpi: float) -> float | None:
    if not raw:
        return None
    match = re.fullmatch(r"\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))(?:[eE]([+-]?\d+))?\s*([A-Za-z%]*)\s*", raw)
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


def _svg_reference_space(svg_path: Path, ref_dpi: float) -> SvgReferenceSpace:
    root = ET.parse(svg_path).getroot()
    viewbox = _root_viewbox(svg_path)
    if viewbox is None:
        raise ValueError(f"{svg_path}: rig SVG needs a root viewBox")
    _vx, _vy, vw, vh = viewbox
    width_px = _length_to_reference_px(root.get("width"), dpi=ref_dpi)
    height_px = _length_to_reference_px(root.get("height"), dpi=ref_dpi)
    if width_px is None or height_px is None or vw == 0.0 or vh == 0.0:
        raise ValueError(f"{svg_path}: cannot map root SVG units to reference pixels")
    sx = width_px / vw
    sy = height_px / vh
    # All managed character sources currently have viewport and viewBox aspect
    # ratios that agree.  Reject a future preserveAspectRatio/letterbox case
    # rather than silently placing authoring markers in the wrong space.
    if not math.isclose(sx, sy, rel_tol=1e-6, abs_tol=1e-9):
        raise ValueError(
            f"{svg_path}: non-uniform viewport/viewBox mapping is not supported "
            f"for rig bootstrap (sx={sx}, sy={sy})"
        )
    return SvgReferenceSpace(viewbox=viewbox, px_per_user_x=sx, px_per_user_y=sy)


def _estimate_frame_to_reference(doc: Mapping[str, object], reference: SvgReferenceSpace) -> tuple[float, float, float, str]:
    """Return ``scale, tx, ty, quality`` for frame = reference_px*scale + translation."""

    source = doc.get("svg_source", {})
    scale = float(source.get("scale", 1.0))  # type: ignore[union-attr]
    frame = doc["frame"]  # type: ignore[index]
    if (
        abs(reference.width_px * scale - float(frame["width"])) < 1e-6  # type: ignore[index]
        and abs(reference.height_px * scale - float(frame["height"])) < 1e-6  # type: ignore[index]
    ):
        return scale, 0.0, 0.0, "exact-frame-space"

    world = _world_bones(doc)
    candidates: list[tuple[float, float]] = []
    by_bone: dict[str, list[tuple[float, float]]] = {}
    for part in doc.get("parts", []):  # type: ignore[union-attr]
        bone = str(part.get("bone", ""))
        if bone not in world or "pivot" not in part:
            continue
        pivot = tuple(float(v) for v in part["pivot"])
        by_bone.setdefault(bone, []).append(pivot)  # type: ignore[arg-type]

    for bone, pivots in by_bone.items():
        unique: list[tuple[float, float]] = []
        for pivot in pivots:
            if not any(math.dist(pivot, seen) < 1e-6 for seen in unique):
                unique.append(pivot)
        if len(unique) != 1:
            continue
        (fx, fy), _, _ = world[bone]
        px, py = unique[0]
        candidates.append((fx - px * scale, fy - py * scale))

    if not candidates:
        return scale, 0.0, 0.0, "unanchored-estimate"
    tx = statistics.median(v[0] for v in candidates)
    ty = statistics.median(v[1] for v in candidates)
    residuals = [math.hypot(x - tx, y - ty) for x, y in candidates]
    max_residual = max(residuals, default=0.0)
    quality = "exact-pivot-fit" if max_residual <= 0.05 else "estimated-pivot-fit"
    return scale, tx, ty, quality


def _frame_point_to_reference(point: tuple[float, float], mapping: tuple[float, float, float, str]) -> tuple[float, float]:
    scale, tx, ty, _ = mapping
    if abs(scale) < 1e-12:
        raise ValueError("SVG source scale may not be zero")
    return ((point[0] - tx) / scale, (point[1] - ty) / scale)


def _joint_names_for_bone(name: str, *, has_standard_hands: bool) -> tuple[str, str | None]:
    if name == "pelvis":
        return "hip_center", None
    if name == "torso":
        return "waist", None
    if name == "head":
        return "neck", None
    standard: dict[str, tuple[str, str]] = {}
    for side in ("near", "far"):
        standard.update({
            f"{side}_arm_u": (f"{side}_shoulder", f"{side}_elbow"),
            f"{side}_arm_l": (f"{side}_elbow", f"{side}_wrist"),
            f"{side}_arm_hand": (f"{side}_wrist", f"{side}_handtip"),
            f"{side}_leg_u": (f"{side}_hip", f"{side}_knee"),
            f"{side}_leg_l": (f"{side}_knee", f"{side}_ankle"),
            f"{side}_leg_foot": (f"{side}_ankle", f"{side}_toe"),
        })
    if name in standard:
        return standard[name]
    for side, stem in (("l", "left"), ("r", "right")):
        legacy = {
            f"{side}_arm_u": (f"{stem}_shoulder", f"{stem}_elbow"),
            f"{side}_arm_l": (f"{stem}_elbow", f"{stem}_handtip" if not has_standard_hands else f"{stem}_wrist"),
            f"{side}_leg_u": (f"{stem}_hip", f"{stem}_knee"),
            f"{side}_leg_l": (f"{stem}_knee", f"{stem}_toe"),
        }
        if name in legacy:
            return legacy[name]
    if name == "jaw":
        return "jaw_hinge", None
    return f"{name}_pivot", f"{name}_tip"


def _view_element(
    root: ET.Element, label: str, *, required_element_ids: set[str] | None = None
) -> ET.Element:
    matches = [elem for elem in root.iter() if elem.get(INK_LABEL) == label]
    if len(matches) == 1:
        return matches[0]
    if not matches and required_element_ids:
        layer_mode = f"{{{INK_NS}}}groupmode"
        candidates: list[ET.Element] = []
        for elem in root.iter():
            if elem.get(layer_mode) != "layer":
                continue
            descendant_ids = {child.get("id") for child in elem.iter() if child.get("id")}
            if required_element_ids <= descendant_ids:
                candidates.append(elem)
        if len(candidates) == 1:
            return candidates[0]
    raise ValueError(f"expected exactly one SVG view labelled {label!r}, found {len(matches)}")


def _parse_side_map(raw: str | None) -> dict[str, str]:
    """Parse compact SVG side aliases such as ``left=far,right=near``."""

    out: dict[str, str] = {}
    if not raw:
        return out
    for item in raw.split(","):
        if "=" not in item:
            continue
        left, right = (part.strip() for part in item.split("=", 1))
        if left and right:
            out[left] = right
    return out


def _canonical_joint_name(name: str, side_map: Mapping[str, str]) -> str:
    """Map source-view anatomy aliases onto the rig document's semantics."""

    for authored_side, rig_side in side_map.items():
        prefix = f"{authored_side}_"
        if name.startswith(prefix):
            return f"{rig_side}_{name[len(prefix):]}"
    return name


def _source_joint_markers(
    root: ET.Element, view: ET.Element
) -> dict[str, tuple[str, tuple[float, float]]]:
    """Return authored joint markers under ``view`` in root SVG coordinates.

    Several mature SVG rigs already carry the correct anatomy directly in the
    artwork source.  Those markers are better static-rig authority than a
    coordinate reconstruction from a generated ``RigDocument``.  Their XML
    ids are preserved so the catalog can reference them directly instead of
    creating a second editable copy.
    """

    side_map = _parse_side_map(view.get("data-rig-side-map"))
    out: dict[str, tuple[str, tuple[float, float]]] = {}
    for elem in view.iter():
        raw_name = elem.get("data-rig-joint")
        element_id = elem.get("id")
        if not raw_name or not element_id or element_id.startswith("ambition-rig-"):
            continue
        name = _canonical_joint_name(raw_name, side_map)
        if name in out:
            raise ValueError(
                f"SVG view {view.get(INK_LABEL) or view.get('id')!r} has duplicate "
                f"authored joint {name!r}"
            )
        out[name] = (element_id, _element_point_in_root(root, elem))
    return out


def catalog_from_rigdoc(rig_path: Path, svg_path: Path, *, used_view_ids: set[str]) -> tuple[ViewCatalog, str]:
    import json

    doc = json.loads(Path(rig_path).read_text())
    source = doc["svg_source"]
    label = str(source["view"])
    root = ET.parse(svg_path).getroot()
    required_ids = {str(eid) for part in doc.get("parts", []) for eid in part.get("include", [])}
    view = _view_element(root, label, required_element_ids=required_ids)
    view_id = _view_id_from_label(label, existing=used_view_ids)
    used_view_ids.add(view_id)
    names = {str(b["name"]) for b in doc.get("bones", [])}
    profile = _profile_for_bones(names)
    authored_joints = _source_joint_markers(root, view)
    ref_dpi = float(source.get("ref_dpi", 96.0))
    reference = _svg_reference_space(svg_path, ref_dpi)
    mapping = _estimate_frame_to_reference(doc, reference)
    world = _world_bones(doc)
    has_standard_hands = any(name.endswith("_arm_hand") for name in names)

    scale = mapping[0]
    frame = doc["frame"]
    root_frame = (
        float(frame.get("center_x", float(frame["width"]) / 2.0)),
        float(frame["ground_y"]),
    )
    root_anchor = reference.reference_to_user(_frame_point_to_reference(root_frame, mapping))

    bones: list[BoneGeometry] = []
    for bone in doc.get("bones", []):
        name = str(bone["name"])
        origin_frame, world_angle, length_frame = world[name]
        origin = reference.reference_to_user(_frame_point_to_reference(origin_frame, mapping))
        length = length_frame / scale / reference.px_per_user_x
        tip = None
        if length_frame > 0.0:
            rad = math.radians(world_angle)
            tip_frame = (
                origin_frame[0] + math.cos(rad) * length_frame,
                origin_frame[1] + math.sin(rad) * length_frame,
            )
            tip = reference.reference_to_user(_frame_point_to_reference(tip_frame, mapping))
        ox, oy = (float(v) / scale / reference.px_per_user_x for v in bone.get("offset", (0.0, 0.0)))
        origin_name, tip_name = _joint_names_for_bone(
            name, has_standard_hands=has_standard_hands
        )
        origin_marker_id = None
        tip_marker_id = None
        if origin_name in authored_joints:
            origin_marker_id, origin = authored_joints[origin_name]
        if tip is not None and tip_name and tip_name in authored_joints:
            tip_marker_id, tip = authored_joints[tip_name]
        bones.append(
            BoneGeometry(
                name=name,
                parent=bone.get("parent"),
                rest_offset=(ox, oy),
                rest_angle=float(bone.get("rest_angle", 0.0)),
                length=length,
                origin=origin,
                tip=tip,
                origin_marker_id=origin_marker_id,
                tip_marker_id=tip_marker_id,
            )
        )

    # The pelvis root is usually represented by two hip landmarks rather than
    # an explicit hip-center marker.  When the SVG already owns those joints,
    # derive the generated pelvis point from them so the entire hierarchy stays
    # in the artwork's coordinate frame.
    if "near_hip" in authored_joints and "far_hip" in authored_joints:
        near = authored_joints["near_hip"][1]
        far = authored_joints["far_hip"][1]
        hip_center = ((near[0] + far[0]) / 2.0, (near[1] + far[1]) / 2.0)
        bones = [
            BoneGeometry(
                name=bone.name,
                parent=bone.parent,
                rest_offset=bone.rest_offset,
                rest_angle=bone.rest_angle,
                length=bone.length,
                origin=hip_center if bone.name == "pelvis" else bone.origin,
                tip=bone.tip,
                origin_marker_id=bone.origin_marker_id,
                tip_marker_id=bone.tip_marker_id,
            )
            for bone in bones
        ]

    # For old direct-rig SVGs that do not yet contain authored joint markers,
    # a unique rigid-part pivot is a stronger statement about an origin than a
    # reconstructed frame-space bone.  This primarily improves older custom
    # articulated characters such as Hunny Horror while leaving the polygon
    # rigs on their already-validated pivot-fit path.
    if not authored_joints and mapping[3] == "exact-frame-space":
        pivots_by_bone: dict[str, list[tuple[float, float]]] = {}
        for raw_part in doc.get("parts", []):
            if "pivot" not in raw_part or not raw_part.get("bone"):
                continue
            pivot = reference.reference_to_user(
                tuple(float(v) for v in raw_part["pivot"])
            )
            bucket = pivots_by_bone.setdefault(str(raw_part["bone"]), [])
            if not any(math.dist(pivot, seen) <= 1e-6 for seen in bucket):
                bucket.append(pivot)
        anchored: list[BoneGeometry] = []
        for bone in bones:
            candidates = pivots_by_bone.get(bone.name, [])
            anchored.append(
                BoneGeometry(
                    name=bone.name,
                    parent=bone.parent,
                    rest_offset=bone.rest_offset,
                    rest_angle=bone.rest_angle,
                    length=bone.length,
                    origin=candidates[0] if len(candidates) == 1 else bone.origin,
                    tip=bone.tip,
                    origin_marker_id=bone.origin_marker_id,
                    tip_marker_id=bone.tip_marker_id,
                )
            )
        bones = anchored

        # Reuse each child's anchored origin for the matching parent tip.  This
        # keeps upper-arm/upper-leg guides connected even when the legacy frame
        # bone and the art bind pivot differed by a few pixels.
        children: dict[str, list[BoneGeometry]] = {}
        for bone in bones:
            if bone.parent:
                children.setdefault(bone.parent, []).append(bone)
        connected: list[BoneGeometry] = []
        for bone in bones:
            child_list = children.get(bone.name, [])
            tip = child_list[0].origin if bone.tip is not None and len(child_list) == 1 else bone.tip
            connected.append(
                BoneGeometry(
                    name=bone.name,
                    parent=bone.parent,
                    rest_offset=bone.rest_offset,
                    rest_angle=bone.rest_angle,
                    length=bone.length,
                    origin=bone.origin,
                    tip=tip,
                    origin_marker_id=bone.origin_marker_id,
                    tip_marker_id=bone.tip_marker_id,
                )
            )
        bones = connected

    converted_parts: list[dict] = []
    for raw_part in doc.get("parts", []):
        part = dict(raw_part)
        if "pivot" in part:
            pivot_ref = tuple(float(v) for v in part["pivot"])
            part["_rig_user_pivot"] = reference.reference_to_user(pivot_ref)
        converted_parts.append(part)
    parts = tuple(converted_parts)
    facing = view.get("data-rig-facing")
    projection = view.get("data-rig-projection") or _projection_from_label(label)
    pose_authority = view.get("data-rig-pose-authority") or "geometry-only"
    part_order = view.get("data-rig-part-order") or "attribute"
    side_map = view.get("data-rig-side-map")
    catalog = ViewCatalog(
        view_id=view_id,
        source_label=label,
        source_layer_id=view.get("id") or "",
        root_anchor=root_anchor,
        projection=projection,
        profile=profile,
        facing=facing,
        pose_authority=pose_authority,
        part_order=part_order,
        side_map=side_map,
        bones=tuple(bones),
        parts=parts,
    )
    quality = "authored-svg-joints" if authored_joints else mapping[3]
    return catalog, quality


def _xml_escape(value: object) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _attrs(items: Iterable[tuple[str, object | None]]) -> str:
    return " ".join(f'{name}="{_xml_escape(value)}"' for name, value in items if value not in (None, ""))


def _marker_id(view_id: str, kind: str, name: str) -> str:
    return f"ambition-rig-{_slug(view_id)}-{kind}-{_slug(name)}"


def _serialize_character_block(views: Sequence[ViewCatalog], qualities: Mapping[str, str]) -> str:
    lines = [BEGIN]
    lines.append(
        f'<metadata id="{RIG_METADATA_ID}" data-ambition-schema="{SCHEMA}" '
        'data-ambition-role="character-rig" data-rig-coordinate-space="root-svg-user-space" data-rig-rest-authority="markers">'
    )
    for view in views:
        lines.append(
            "  <g "
            + _attrs(
                [
                    ("id", f"ambition-rig-view-{_slug(view.view_id)}"),
                    ("data-rig-view-def", view.view_id),
                    ("data-rig-source-layer", view.source_layer_id),
                    ("data-rig-source-label", view.source_label),
                    ("data-rig-root", _marker_id(view.view_id, "joint", "rig_root")),
                    ("data-rig-projection", view.projection),
                    ("data-rig-facing", view.facing),
                    ("data-rig-profile", view.profile),
                    ("data-rig-pose-authority", view.pose_authority),
                    ("data-rig-part-order", view.part_order),
                    ("data-rig-side-map", view.side_map),
                    ("data-rig-source-map-quality", qualities.get(view.view_id)),
                ]
            )
            + ">"
        )
        bone_names = {b.name for b in view.bones}
        has_standard_hands = any(name.endswith("_arm_hand") for name in bone_names)
        for bone in view.bones:
            origin_name, tip_name = _joint_names_for_bone(bone.name, has_standard_hands=has_standard_hands)
            origin_marker = bone.origin_marker_id or _marker_id(view.view_id, "joint", origin_name)
            tip_marker = (
                bone.tip_marker_id or _marker_id(view.view_id, "joint", tip_name)
                if bone.tip is not None and tip_name
                else None
            )
            lines.append(
                "    <g "
                + _attrs(
                    [
                        ("id", f"ambition-rig-{_slug(view.view_id)}-bone-{_slug(bone.name)}"),
                        ("data-rig-bone-def", bone.name),
                        ("data-rig-parent", bone.parent),
                        ("data-rig-origin", origin_marker),
                        ("data-rig-tip", tip_marker),
                    ]
                )
                + " />"
            )
        for part in view.parts:
            part_name = str(part["name"])
            pivot_marker = _marker_id(view.view_id, "bind", part_name)
            lines.append(
                "    <g "
                + _attrs(
                    [
                        ("id", f"ambition-rig-{_slug(view.view_id)}-part-{_slug(part_name)}"),
                        ("data-rig-part-def", part_name),
                        ("data-rig-bone", part.get("bone")),
                        ("data-rig-z", _fmt(float(part.get("z", 0.0)))),
                        ("data-rig-pivot", pivot_marker),
                        ("data-rig-bind-angle", _fmt(float(part.get("rest_angle", 0.0)))),
                        ("data-rig-opacity", part.get("opacity_channel")),
                        ("data-rig-elements", " ".join(str(v) for v in part.get("include", []))),
                    ]
                )
                + " />"
            )
        lines.append("  </g>")
    lines.append("</metadata>")

    lines.append(
        f'<g id="{MARKER_LAYER_ID}" data-rig-editor-layer="true" '
        'inkscape:groupmode="layer" inkscape:label="Ambition Rig Markers">'
    )
    for view in views:
        lines.append(
            f'  <g id="ambition-rig-markers-{_slug(view.view_id)}" data-rig-view="{_xml_escape(view.view_id)}" '
            f'inkscape:label="Rig Markers - {_xml_escape(view.source_label)}">'
        )
        bone_names = {b.name for b in view.bones}
        has_standard_hands = any(name.endswith("_arm_hand") for name in bone_names)
        joints: dict[str, tuple[float, float]] = {"rig_root": view.root_anchor}
        for bone in view.bones:
            origin_name, tip_name = _joint_names_for_bone(bone.name, has_standard_hands=has_standard_hands)
            if bone.origin_marker_id is None:
                joints.setdefault(origin_name, bone.origin)
            if bone.tip is not None and tip_name and bone.tip_marker_id is None:
                joints.setdefault(tip_name, bone.tip)
            if bone.tip is not None and tip_name:
                lines.append(
                    "    <line "
                    + _attrs(
                        [
                            ("id", _marker_id(view.view_id, "guide", bone.name)),
                            ("data-rig-bone-guide", bone.name),
                            ("x1", _fmt(bone.origin[0])),
                            ("y1", _fmt(bone.origin[1])),
                            ("x2", _fmt(bone.tip[0])),
                            ("y2", _fmt(bone.tip[1])),
                            ("stroke", "#d226c6"),
                            ("stroke-width", "1.25"),
                            ("stroke-opacity", "0.32"),
                        ]
                    )
                    + " />"
                )
        for name, (x, y) in sorted(joints.items()):
            lines.append(
                "    <circle "
                + _attrs(
                    [
                        ("id", _marker_id(view.view_id, "joint", name)),
                        ("data-rig-joint", name),
                        ("cx", _fmt(x)),
                        ("cy", _fmt(y)),
                        ("r", "3"),
                        ("fill", "#ff3bd4"),
                        ("fill-opacity", "0.58"),
                        ("stroke", "#43133d"),
                        ("stroke-width", "1"),
                    ]
                )
                + " />"
            )
        for part in view.parts:
            if "pivot" not in part:
                continue
            px, py = (float(v) for v in part.get("_rig_user_pivot", part["pivot"]))
            name = str(part["name"])
            lines.append(
                "    <circle "
                + _attrs(
                    [
                        ("id", _marker_id(view.view_id, "bind", name)),
                        ("data-rig-bind-pivot", name),
                        ("cx", _fmt(px)),
                        ("cy", _fmt(py)),
                        ("r", "2.2"),
                        ("fill", "#28c8ff"),
                        ("fill-opacity", "0.42"),
                        ("stroke", "#093b52"),
                        ("stroke-width", "0.8"),
                    ]
                )
                + " />"
            )
        lines.append("  </g>")
    lines.append("</g>")
    lines.append(END)
    return "\n".join(lines)


def _serialize_reference_block(role: str) -> str:
    return "\n".join(
        [
            BEGIN,
            f'<metadata id="{RIG_METADATA_ID}" data-ambition-schema="{SCHEMA}" '
            f'data-ambition-role="{_xml_escape(role)}" />',
            END,
        ]
    )


def install_block(path: Path, block: str) -> None:
    path = Path(path)
    text = path.read_text(encoding="utf8")
    if BEGIN in text or END in text:
        if text.count(BEGIN) != 1 or text.count(END) != 1:
            raise ValueError(f"{path}: malformed managed rig block")
        start = text.index(BEGIN)
        stop = text.index(END, start) + len(END)
        line_start = text.rfind("\n", 0, start) + 1
        indent = text[line_start:start]
        if indent.strip():
            # BEGIN should be the first non-whitespace token on its line.  Fall
            # back to a direct replacement rather than guessing around unusual
            # hand-edited XML.
            line_start = start
            indent = ""
        managed = "\n".join(
            f"{indent}{line}" if line else line for line in block.splitlines()
        )
        new = text[:line_start] + managed + text[stop:]
    else:
        match = re.search(r"\s*</svg>\s*$", text)
        if not match:
            raise ValueError(f"{path}: missing closing </svg>")
        closing = text[match.start():]
        prefix = text[:match.start()].rstrip()
        new = prefix + "\n  " + block.replace("\n", "\n  ") + "\n" + closing.lstrip()
    if not new.endswith("\n"):
        new += "\n"
    path.write_text(new, encoding="utf8")


def _managed_root(path: Path) -> ET.Element:
    root = ET.parse(path).getroot()
    metadata = next((e for e in root.iter() if e.get("id") == RIG_METADATA_ID), None)
    if metadata is None:
        raise ValueError(f"{path}: no {RIG_METADATA_ID!r} block")
    return root


def _find_by_id(root: ET.Element, element_id: str) -> ET.Element:
    matches = [e for e in root.iter() if e.get("id") == element_id]
    if len(matches) != 1:
        raise ValueError(f"expected one SVG element id={element_id!r}, found {len(matches)}")
    return matches[0]


def _view_defs(root: ET.Element) -> list[ET.Element]:
    return [e for e in root.iter() if e.get("data-rig-view-def")]


def validate(path: Path) -> list[str]:
    root = _managed_root(path)
    ids: dict[str, int] = {}
    for elem in root.iter():
        if eid := elem.get("id"):
            ids[eid] = ids.get(eid, 0) + 1
    errors = [f"duplicate SVG id {eid!r}" for eid, count in ids.items() if count > 1]
    viewbox = _root_viewbox(Path(path))
    marker_layer = next((e for e in root.iter() if e.get("id") == MARKER_LAYER_ID), None)
    if viewbox is not None and marker_layer is not None:
        vx, vy, vw, vh = viewbox
        margin_x = max(1.0, abs(vw) * 0.05)
        margin_y = max(1.0, abs(vh) * 0.05)
        for marker in marker_layer.iter():
            if _local(marker.tag) != "circle":
                continue
            try:
                x = float(marker.get("cx", "nan"))
                y = float(marker.get("cy", "nan"))
            except ValueError:
                errors.append(f"marker {marker.get('id')!r} has non-numeric coordinates")
                continue
            if not (vx - margin_x <= x <= vx + vw + margin_x and vy - margin_y <= y <= vy + vh + margin_y):
                errors.append(
                    f"marker {marker.get('id')!r} at ({_fmt(x)}, {_fmt(y)}) is outside root viewBox "
                    f"{viewbox}; likely coordinate-space mismatch"
                )
    views = _view_defs(root)
    seen_views: set[str] = set()
    for view in views:
        view_id = view.get("data-rig-view-def") or ""
        if view_id in seen_views:
            errors.append(f"duplicate rig view {view_id!r}")
        seen_views.add(view_id)
        source_layer = view.get("data-rig-source-layer")
        if source_layer and source_layer not in ids:
            errors.append(f"view {view_id}: missing source layer {source_layer!r}")
        root_marker = view.get("data-rig-root")
        if not root_marker:
            errors.append(f"view {view_id}: missing rig root marker")
        elif root_marker not in ids:
            errors.append(f"view {view_id}: missing rig root {root_marker!r}")
        bones = [e for e in view if e.get("data-rig-bone-def")]
        parts = [e for e in view if e.get("data-rig-part-def")]
        bone_names = {e.get("data-rig-bone-def") or "" for e in bones}
        for bone in bones:
            name = bone.get("data-rig-bone-def") or ""
            parent = bone.get("data-rig-parent")
            if parent and parent not in bone_names:
                errors.append(f"view {view_id}: bone {name!r} has missing parent {parent!r}")
            for attr in ("data-rig-origin", "data-rig-tip"):
                marker = bone.get(attr)
                if marker and marker not in ids:
                    errors.append(f"view {view_id}: bone {name!r} references missing {attr} {marker!r}")
        part_names: set[str] = set()
        owned: dict[str, str] = {}
        for part in parts:
            name = part.get("data-rig-part-def") or ""
            if name in part_names:
                errors.append(f"view {view_id}: duplicate part {name!r}")
            part_names.add(name)
            bone = part.get("data-rig-bone") or ""
            if bone and bone not in bone_names:
                errors.append(f"view {view_id}: part {name!r} references missing bone {bone!r}")
            pivot = part.get("data-rig-pivot")
            if pivot and pivot not in ids:
                errors.append(f"view {view_id}: part {name!r} references missing pivot {pivot!r}")
            for eid in (part.get("data-rig-elements") or "").split():
                if eid not in ids:
                    errors.append(f"view {view_id}: part {name!r} references missing element {eid!r}")
                previous = owned.get(eid)
                if previous and previous != name:
                    errors.append(f"view {view_id}: SVG element {eid!r} owned by both {previous!r} and {name!r}")
                owned[eid] = name
    return errors


def summary(path: Path) -> str:
    root = _managed_root(path)
    metadata = _find_by_id(root, RIG_METADATA_ID)
    role = metadata.get("data-ambition-role", "unknown")
    lines = [f"{Path(path)}", f"schema={metadata.get('data-ambition-schema')} role={role}"]
    for view in _view_defs(root):
        view_id = view.get("data-rig-view-def") or "?"
        lines.append(
            f"view {view_id}: layer={view.get('data-rig-source-layer') or '?'} "
            f"projection={view.get('data-rig-projection') or '?'} "
            f"profile={view.get('data-rig-profile') or '?'} "
            f"facing={view.get('data-rig-facing') or '-'}"
        )
        bones = [e for e in view if e.get("data-rig-bone-def")]
        parts = [e for e in view if e.get("data-rig-part-def")]
        lines.append(f"  bones={len(bones)} parts={len(parts)}")
        for bone in bones:
            lines.append(
                f"  B {bone.get('data-rig-bone-def')} parent={bone.get('data-rig-parent') or '-'} "
                f"origin={bone.get('data-rig-origin') or '-'} tip={bone.get('data-rig-tip') or '-'}"
            )
        for part in parts:
            elements = (part.get("data-rig-elements") or "").split()
            elem_text = elements[0] if len(elements) == 1 else f"[{len(elements)} ids]"
            lines.append(
                f"  P {part.get('data-rig-part-def')} bone={part.get('data-rig-bone')} "
                f"z={part.get('data-rig-z')} pivot={part.get('data-rig-pivot')} art={elem_text}"
            )
    return "\n".join(lines)


def _find_start_tag(text: str, element_id: str) -> tuple[int, int, str]:
    # XML ids in this repository are unique. Search a bounded start tag around
    # the literal id rather than reserializing the document with an XML writer.
    pattern = re.compile(r"<(?P<tag>[A-Za-z_][\w:.-]*)(?P<body>[^<>]*?\bid\s*=\s*(['\"])" + re.escape(element_id) + r"\3[^<>]*?)(?P<close>/?>)", re.DOTALL)
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise ValueError(f"expected one source start tag id={element_id!r}, found {len(matches)}")
    m = matches[0]
    return m.start(), m.end(), m.group(0)


def _remove_element_source_preserving(path: Path, element_id: str) -> None:
    """Delete one self-closing element by id, leaving the rest of the file byte-identical.

    Source-preserving for the reason every edit in this module is: these files
    are HAND-EDITED in Inkscape, and a full parse-and-serialize round trip
    rewrites attribute order and whitespace across the whole document, which
    turns a one-marker change into an unreviewable diff.
    """
    text = Path(path).read_text(encoding="utf8")
    start, stop, tag = _find_start_tag(text, element_id)
    if not tag.rstrip().endswith("/>"):
        raise ValueError(
            f"{path}: element {element_id!r} is not self-closing; refusing to guess where it ends"
        )
    # Take the whitespace in front of it too, so removing a marker does not
    # leave a blank line where it stood.
    lead = start
    while lead > 0 and text[lead - 1] in " \t":
        lead -= 1
    if lead > 0 and text[lead - 1] == "\n":
        lead -= 1
    Path(path).write_text(text[:lead] + text[stop:], encoding="utf8")


def _set_attrs_source_preserving(path: Path, element_id: str, attrs: Mapping[str, str]) -> None:
    text = Path(path).read_text(encoding="utf8")
    start, stop, tag = _find_start_tag(text, element_id)
    updated = tag
    for name, value in attrs.items():
        if value is None:
            # ⭐ `None` DELETES. An attribute whose right answer is "say nothing"
            # cannot be expressed by writing a value — a part that names an empty
            # bind pivot is a part naming a marker that does not exist.
            updated = re.sub(
                r"\s" + re.escape(name) + r"\s*=\s*(['\"]).*?\1",
                "",
                updated,
                count=1,
                flags=re.DOTALL,
            )
            continue
        escaped = _xml_escape(value)
        pat = re.compile(r"(\s" + re.escape(name) + r"\s*=\s*)(['\"])(.*?)\2", re.DOTALL)
        if pat.search(updated):
            updated = pat.sub(lambda m: m.group(1) + m.group(2) + escaped + m.group(2), updated, count=1)
        else:
            pos = updated.rfind("/>")
            if pos < 0:
                pos = updated.rfind(">")
            updated = updated[:pos].rstrip() + f' {name}="{escaped}"' + updated[pos:]
    Path(path).write_text(text[:start] + updated + text[stop:], encoding="utf8")


def _marker_for(root: ET.Element, *, view_id: str, kind: str, name: str) -> ET.Element:
    if kind == "joint":
        view = next(
            (v for v in _view_defs(root) if v.get("data-rig-view-def") == view_id),
            None,
        )
        if view is None:
            raise ValueError(f"unknown rig view {view_id!r}")
        bones = [e for e in view if e.get("data-rig-bone-def")]
        bone_names = {e.get("data-rig-bone-def") or "" for e in bones}
        has_standard_hands = any(value.endswith("_arm_hand") for value in bone_names)
        candidate_ids: list[str] = []
        if name == "rig_root" and view.get("data-rig-root"):
            candidate_ids.append(view.get("data-rig-root") or "")
        for bone in bones:
            bone_name = bone.get("data-rig-bone-def") or ""
            origin_name, tip_name = _joint_names_for_bone(
                bone_name, has_standard_hands=has_standard_hands
            )
            if name == origin_name and bone.get("data-rig-origin"):
                candidate_ids.append(bone.get("data-rig-origin") or "")
            if name == tip_name and bone.get("data-rig-tip"):
                candidate_ids.append(bone.get("data-rig-tip") or "")
        candidate_ids = list(dict.fromkeys(value for value in candidate_ids if value))
        if len(candidate_ids) == 1:
            return _find_by_id(root, candidate_ids[0])
        if len(candidate_ids) > 1:
            raise ValueError(
                f"joint {name!r} in view {view_id!r} resolves to multiple marker ids: "
                f"{candidate_ids}"
            )

    attr = "data-rig-joint" if kind == "joint" else "data-rig-bind-pivot"
    matches = [
        e for e in root.iter()
        if e.get(attr) == name
        and any(a.get("data-rig-view") == view_id for a in _ancestors(root, e))
    ]
    if len(matches) != 1:
        raise ValueError(f"expected one {kind} marker {name!r} in view {view_id!r}, found {len(matches)}")
    return matches[0]


def _ancestors(root: ET.Element, target: ET.Element) -> list[ET.Element]:
    parent = {child: node for node in root.iter() for child in node}
    out: list[ET.Element] = []
    cur = target
    while cur in parent:
        cur = parent[cur]
        out.append(cur)
    return out


def refresh_guides(path: Path, *, view_id: str | None = None) -> int:
    """Re-anchor editor-only bone guide lines to their authoritative markers."""

    root = _managed_root(path)
    updates: list[tuple[str, dict[str, str]]] = []
    for view in _view_defs(root):
        current_view = view.get("data-rig-view-def") or ""
        if view_id is not None and current_view != view_id:
            continue
        for bone in (e for e in view if e.get("data-rig-bone-def")):
            origin_id = bone.get("data-rig-origin")
            tip_id = bone.get("data-rig-tip")
            if not origin_id or not tip_id:
                continue
            origin = _find_by_id(root, origin_id)
            tip = _find_by_id(root, tip_id)
            guide_id = _marker_id(current_view, "guide", bone.get("data-rig-bone-def") or "")
            try:
                _find_by_id(root, guide_id)
            except ValueError:
                # Direct-SVG rigs such as Mary-O can use the catalog without
                # carrying generated guide lines.
                continue
            updates.append(
                (
                    guide_id,
                    {
                        "x1": _fmt(_element_point_in_root(root, origin)[0]),
                        "y1": _fmt(_element_point_in_root(root, origin)[1]),
                        "x2": _fmt(_element_point_in_root(root, tip)[0]),
                        "y2": _fmt(_element_point_in_root(root, tip)[1]),
                    },
                )
            )
    for element_id, attrs in updates:
        _set_attrs_source_preserving(path, element_id, attrs)
    return len(updates)


def retire_redundant_bind_pivots(
    path: Path, *, view_id: str | None = None, tolerance: float = 2.0
) -> list[str]:
    """Delete every bind pivot that has nothing to say, and unwire its part.

    ⭐ A BIND PIVOT IS AN OFFSET, AND MOST PARTS DO NOT WANT ONE. The rig reader
    falls back to the bone's own origin for a part that names no pivot, so a
    marker sitting on that origin is a second copy of a coordinate the skeleton
    already carries — and a second copy is a thing that has to be dragged in
    step by hand forever. Jon, on authoring this rig: *"I have to move 2 markers
    for every position. I don't want authoring to be that hard."*

    ⛔ AND IT IS NOT COSMETIC. The two drift apart the moment somebody moves one
    and not the other, and the art then hinges about a point it is no longer
    attached to. That is how this rig ended up with a head swinging 163 units
    wide of its own skull.

    A pivot further than `tolerance` from its bone origin is KEPT: somebody
    meant that one (a sleeve hinging outboard of the shoulder without dragging
    the arm chain). Returns the part names that were unwired.
    """

    root = _managed_root(path)
    retired: list[str] = []
    drop_ids: list[str] = []
    for view in _view_defs(root):
        current_view = view.get("data-rig-view-def") or ""
        if view_id is not None and current_view != view_id:
            continue
        origins: dict[str, tuple[float, float]] = {}
        for bone in (e for e in view if e.get("data-rig-bone-def")):
            origin_id = bone.get("data-rig-origin")
            if not origin_id:
                continue
            origins[bone.get("data-rig-bone-def") or ""] = _element_point_in_root(
                root, _find_by_id(root, origin_id)
            )
        for part in (e for e in view if e.get("data-rig-part-def")):
            pivot_id = part.get("data-rig-pivot")
            origin = origins.get(part.get("data-rig-bone") or "")
            if not pivot_id or origin is None:
                continue
            try:
                marker = _find_by_id(root, pivot_id)
            except ValueError:
                continue
            if math.dist(_element_point_in_root(root, marker), origin) > tolerance:
                continue
            retired.append(part.get("data-rig-part-def") or "")
            drop_ids.append(pivot_id)
            element_id = part.get("id")
            if element_id:
                _set_attrs_source_preserving(path, element_id, {"data-rig-pivot": None})
    for marker_id in drop_ids:
        _remove_element_source_preserving(path, marker_id)
    return retired


def sync_bind_angles(path: Path, *, view_id: str | None = None) -> list[str]:
    """Re-derive each part's bind angle from the joints its bone now sits on.

    ⛔ **moving a joint silently tilts the art that rides it.** A part renders at
    ``bone_world_angle - data-rig-bind-angle``, so the two agree only while the
    bind angle is the angle the art was drawn at. Drag an elbow to where it
    belongs and the forearm's bone turns while its bind angle does not — the
    limb comes out of rest already rotated by the correction, in every frame.

    This restates the assumption these humanoid rigs are authored under: the art
    IS drawn in its rest pose. Bones with no tip have no direction of their own,
    so their parts are left exactly as authored.

    Returns the part names whose angle changed.
    """

    root = _managed_root(path)
    changed: list[str] = []
    updates: list[tuple[str, dict[str, str]]] = []
    for view in _view_defs(root):
        current_view = view.get("data-rig-view-def") or ""
        if view_id is not None and current_view != view_id:
            continue
        angles: dict[str, float] = {}
        for bone in (e for e in view if e.get("data-rig-bone-def")):
            origin_id, tip_id = bone.get("data-rig-origin"), bone.get("data-rig-tip")
            if not origin_id or not tip_id:
                continue
            origin = _element_point_in_root(root, _find_by_id(root, origin_id))
            tip = _element_point_in_root(root, _find_by_id(root, tip_id))
            if math.dist(origin, tip) <= 1e-9:
                continue
            angles[bone.get("data-rig-bone-def") or ""] = math.degrees(
                math.atan2(tip[1] - origin[1], tip[0] - origin[0])
            )
        for part in (e for e in view if e.get("data-rig-part-def")):
            angle = angles.get(part.get("data-rig-bone") or "")
            if angle is None:
                continue
            current = part.get("data-rig-bind-angle")
            wanted = _fmt(angle)
            if current == wanted:
                continue
            element_id = part.get("id")
            if not element_id:
                continue
            updates.append((element_id, {"data-rig-bind-angle": wanted}))
            changed.append(part.get("data-rig-part-def") or element_id)
    for element_id, attrs in updates:
        _set_attrs_source_preserving(path, element_id, attrs)
    return changed


def move_marker(path: Path, *, view_id: str, kind: str, name: str, x: float, y: float) -> None:
    root = _managed_root(path)
    marker = _marker_for(root, view_id=view_id, kind=kind, name=name)
    marker_id = marker.get("id")
    if not marker_id:
        raise ValueError("rig marker has no id")
    local_x, local_y = _root_point_to_element_local(root, marker, (x, y))
    attrs = (
        {"cx": _fmt(local_x), "cy": _fmt(local_y)}
        if marker.get("cx") is not None and marker.get("cy") is not None
        else {"x": _fmt(local_x), "y": _fmt(local_y)}
    )
    _set_attrs_source_preserving(path, marker_id, attrs)
    if kind == "joint":
        refresh_guides(path, view_id=view_id)


Matrix = tuple[float, float, float, float, float, float]


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


def _parent_matrix(root: ET.Element, elem: ET.Element) -> Matrix:
    ancestors = list(reversed(_ancestors(root, elem)))
    current: Matrix = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    # The root SVG's own transform is not part of ordinary child user space.
    for ancestor in ancestors:
        if ancestor is root:
            continue
        current = _matrix_mul(current, _transform_matrix(ancestor.get("transform")))
    return current


def _apply_matrix(matrix: Matrix, point: tuple[float, float]) -> tuple[float, float]:
    a, b, c, d, e, f = matrix
    x, y = point
    return (a * x + c * y + e, b * x + d * y + f)


def _element_point_in_root(root: ET.Element, elem: ET.Element) -> tuple[float, float]:
    """Resolve an SVG point marker through its complete transform chain."""

    if elem.get("cx") is not None and elem.get("cy") is not None:
        point = (float(elem.get("cx", "0")), float(elem.get("cy", "0")))
    elif elem.get("x") is not None and elem.get("y") is not None:
        point = (float(elem.get("x", "0")), float(elem.get("y", "0")))
    else:
        raise ValueError(f"SVG marker {elem.get('id')!r} has no point coordinates")
    matrix = _matrix_mul(_parent_matrix(root, elem), _transform_matrix(elem.get("transform")))
    return _apply_matrix(matrix, point)


def _root_point_to_element_local(
    root: ET.Element, elem: ET.Element, point: tuple[float, float]
) -> tuple[float, float]:
    """Invert a point marker's complete transform chain."""

    matrix = _matrix_mul(_parent_matrix(root, elem), _transform_matrix(elem.get("transform")))
    a, b, c, d, e, f = matrix
    det = a * d - b * c
    if abs(det) < 1e-12:
        raise ValueError(f"cannot edit marker {elem.get('id')!r} through a singular SVG transform")
    x = point[0] - e
    y = point[1] - f
    return ((d * x - c * y) / det, (-b * x + a * y) / det)


def _root_delta_to_parent(matrix: Matrix, dx: float, dy: float) -> tuple[float, float]:
    a, b, c, d, _e, _f = matrix
    det = a * d - b * c
    if abs(det) < 1e-12:
        raise ValueError("cannot nudge art through a singular SVG transform")
    return ((d * dx - c * dy) / det, (-b * dx + a * dy) / det)


def _translate_value(existing: str | None, dx: float, dy: float) -> str:
    prefix = f"translate({_fmt(dx)},{_fmt(dy)})"
    return prefix if not existing else f"{prefix} {existing}"


def _part_context(path: Path, *, view_id: str, part_name: str) -> tuple[ET.Element, ET.Element, list[ET.Element]]:
    root = _managed_root(path)
    view = next((v for v in _view_defs(root) if v.get("data-rig-view-def") == view_id), None)
    if view is None:
        raise ValueError(f"unknown rig view {view_id!r}")
    part = next((p for p in view if p.get("data-rig-part-def") == part_name), None)
    if part is None:
        raise ValueError(f"unknown part {part_name!r} in view {view_id!r}")
    element_ids = (part.get("data-rig-elements") or "").split()
    elems = [_find_by_id(root, eid) for eid in element_ids]
    selected = set(elems)
    topmost = [
        elem for elem in elems
        if not any(ancestor in selected for ancestor in _ancestors(root, elem))
    ]
    return root, part, topmost


def _nudge_part_art(path: Path, *, view_id: str, part_name: str, dx: float, dy: float) -> ET.Element:
    root, part, topmost = _part_context(path, view_id=view_id, part_name=part_name)
    for elem in topmost:
        eid = elem.get("id")
        assert eid
        local_dx, local_dy = _root_delta_to_parent(_parent_matrix(root, elem), dx, dy)
        _set_attrs_source_preserving(
            path,
            eid,
            {"transform": _translate_value(elem.get("transform"), local_dx, local_dy)},
        )
    return part


def nudge_part(path: Path, *, view_id: str, part_name: str, dx: float, dy: float) -> None:
    """Move artwork by a root-SVG delta while keeping its bind/skeleton fixed."""

    _nudge_part_art(path, view_id=view_id, part_name=part_name, dx=dx, dy=dy)


def translate_part_source(path: Path, *, view_id: str, part_name: str, dx: float, dy: float) -> None:
    """Move artwork and its dedicated bind pivot without changing assembled pose."""

    part = _nudge_part_art(path, view_id=view_id, part_name=part_name, dx=dx, dy=dy)
    root = _managed_root(path)
    marker_id = part.get("data-rig-pivot")
    if not marker_id:
        return
    marker = _find_by_id(root, marker_id)
    if marker.get("data-rig-bind-pivot") != part_name:
        # Some direct-SVG rigs intentionally share a skeletal joint as their
        # part pivot. Moving that marker would mutate the skeleton, so source
        # translation leaves it fixed.
        return
    move_marker(
        path,
        view_id=view_id,
        kind="bind",
        name=part_name,
        x=float(marker.get("cx", "0")) + dx,
        y=float(marker.get("cy", "0")) + dy,
    )


def install_repo_metadata(repo_root: Path, *, force: bool = False) -> list[Path]:
    """Bootstrap v1 catalogs from every committed rig document plus Mary-O.

    This is a migration helper, not the future source of truth.  It copies the
    *current* static rig facts into the SVG so the next renderer can switch
    authority without reconstructing them from legacy ``.rig.json`` files.
    """

    import json

    repo_root = Path(repo_root).resolve()
    rigdocs = sorted((repo_root / "ambition_sprite2d_renderer/targets/characters").rglob("*.rig.json"))
    by_svg: dict[Path, list[Path]] = {}
    for rig_path in rigdocs:
        try:
            doc = json.loads(rig_path.read_text())
        except Exception:
            continue
        source = doc.get("svg_source")
        if not isinstance(source, dict) or not source.get("path") or not source.get("view"):
            continue
        svg_path = (rig_path.parent / str(source["path"])).resolve()
        if svg_path.exists():
            by_svg.setdefault(svg_path, []).append(rig_path)

    changed: list[Path] = []
    for svg_path, paths in sorted(by_svg.items(), key=lambda item: str(item[0])):
        if not force and BEGIN in svg_path.read_text(encoding="utf8"):
            continue
        used: set[str] = set()
        views: list[ViewCatalog] = []
        qualities: dict[str, str] = {}
        for rig_path in sorted(paths):
            try:
                catalog, quality = catalog_from_rigdoc(rig_path, svg_path, used_view_ids=used)
            except ValueError as ex:
                # Some retired rig documents intentionally remain beside their
                # replacement view. They are not source authority when their
                # named/source elements no longer exist in the current SVG.
                if "expected exactly one SVG view labelled" in str(ex):
                    continue
                raise
            views.append(catalog)
            qualities[catalog.view_id] = quality
        if views:
            install_block(svg_path, _serialize_character_block(views, qualities))
            changed.append(svg_path)

    # Mary-O is already a direct-SVG rigid-part authoring source rather than a
    # RigDocument.  Its embedded attributes are copied into the same catalog so
    # it proves that the format is not secretly a fixed humanoid template.
    mary = repo_root / "assets/mary_o_v2.svg"
    if mary.exists() and (force or BEGIN not in mary.read_text(encoding="utf8")):
        install_block(mary, _mary_o_block(mary))
        changed.append(mary)

    # Every SVG gets an explicit role, even when it is not a character rig. That
    # prevents future tooling from treating reference/draft files as latent rigs.
    all_svgs = sorted(
        set((repo_root / "assets").rglob("*.svg"))
        | set((repo_root / "ambition_sprite2d_renderer/data/characters").rglob("*.svg"))
    )
    rig_set = {p.resolve() for p in changed}
    for svg_path in all_svgs:
        if svg_path.resolve() in rig_set:
            continue
        if not force and BEGIN in svg_path.read_text(encoding="utf8"):
            continue
        role = "rig-template" if svg_path.name in RIG_TEMPLATE_NAMES else "reference"
        install_block(svg_path, _serialize_reference_block(role))
        changed.append(svg_path)
    return sorted(set(changed))


def _mary_o_block(path: Path) -> str:
    root = ET.parse(path).getroot()
    # Top-level authored game views; head authoring and size guides are helpers,
    # not renderable rig views.
    views = [
        e for e in root
        if _local(e.tag) == "g" and e.get("data-rig-projection") in {"side", "front"}
    ]
    lines = [BEGIN]
    lines.append(
        f'<metadata id="{RIG_METADATA_ID}" data-ambition-schema="{SCHEMA}" '
        'data-ambition-role="character-rig" data-rig-coordinate-space="root-svg-user-space" data-rig-rest-authority="markers">'
    )
    for view in views:
        label = view.get(INK_LABEL) or view.get("id") or "Mary-O"
        view_id = _slug(label.removeprefix("Mary-O - "))
        projection = view.get("data-rig-projection") or "unspecified"
        markers = {e.get("data-rig-joint"): e for e in view.iter() if e.get("data-rig-joint")}
        torso_marker = markers.get("torso")
        lines.append(
            "  <g "
            + _attrs(
                [
                    ("id", f"ambition-rig-view-{view_id}"),
                    ("data-rig-view-def", view_id),
                    ("data-rig-source-layer", view.get("id")),
                    ("data-rig-source-label", label),
                    ("data-rig-root", torso_marker.get("id") if torso_marker is not None else None),
                    ("data-rig-projection", projection),
                    ("data-rig-profile", "rigid-biped-v1"),
                    ("data-rig-pose-authority", "geometry-only"),
                    ("data-rig-part-order", "attribute"),
                    ("data-rig-source-map-quality", "authored-markers"),
                ]
            )
            + ">"
        )
        parts = [e for e in view.iter() if e.get("data-rig-part") and e.get("data-rig-bone")]
        bone_names = sorted({e.get("data-rig-bone") for e in parts if e.get("data-rig-bone")})
        for bone in bone_names:
            if bone == "torso":
                parent = None
            elif bone == "torso_back":
                parent = "torso"
            else:
                parent = "torso"
            origin_marker = markers.get(bone)
            tip_marker = markers.get({
                "near_arm": "near_handtip", "far_arm": "far_handtip",
                "near_leg": "near_toe", "far_leg": "far_toe",
                "character_left_arm": "character_left_handtip",
                "character_right_arm": "character_right_handtip",
                "character_left_leg": "character_left_toe",
                "character_right_leg": "character_right_toe",
            }.get(bone, ""))

            lines.append(
                "    <g "
                + _attrs(
                    [
                        ("id", f"ambition-rig-{view_id}-bone-{_slug(bone)}"),
                        ("data-rig-bone-def", bone),
                        ("data-rig-parent", parent),
                        ("data-rig-origin", origin_marker.get("id") if origin_marker is not None else None),
                        ("data-rig-tip", tip_marker.get("id") if tip_marker is not None else None),
                    ]
                )
                + " />"
            )
        for part in parts:
            name = part.get("data-rig-part") or ""
            bone = part.get("data-rig-bone") or ""
            marker = markers.get(bone)
            # The current Mary-O SVG wrappers are already exact ownership units;
            # reference the wrapper itself instead of duplicating its child ids.
            lines.append(
                "    <g "
                + _attrs(
                    [
                        ("id", f"ambition-rig-{view_id}-part-{_slug(name)}"),
                        ("data-rig-part-def", name),
                        ("data-rig-bone", bone),
                        ("data-rig-z", part.get("data-rig-z") or "0"),
                        ("data-rig-pivot", marker.get("id") if marker is not None else None),
                        ("data-rig-bind-angle", "0"),
                        ("data-rig-elements", part.get("id")),
                    ]
                )
                + " />"
            )
        lines.append("  </g>")
    lines.append("</metadata>")
    lines.append(END)
    return "\n".join(lines)


def _set_display_inline(elem: ET.Element) -> None:
    style_items: list[str] = []
    for item in (elem.get("style") or "").split(";"):
        item = item.strip()
        if not item or item.startswith("display:"):
            continue
        style_items.append(item)
    style_items.append("display:inline")
    elem.set("style", ";".join(style_items))


def _preview_svg_bytes(path: Path, *, width: int, view_id: str | None = None) -> bytes:
    """Rasterize an SVG for visual rig review without modifying the source.

    All catalogued source views and the editor marker layer are made visible in
    the in-memory copy.  This is intentionally a review renderer, not a sprite
    publishing path.
    """

    try:
        import cairosvg
    except ImportError as ex:  # pragma: no cover - depends on author env
        raise RuntimeError(
            "SVG layout preview requires CairoSVG; install the repository's "
            "normal SVG authoring dependencies first"
        ) from ex

    root = ET.parse(path).getroot()
    metadata = next((e for e in root.iter() if e.get("id") == RIG_METADATA_ID), None)
    if metadata is not None:
        views = [e for e in metadata if e.get("data-rig-view-def")]
        selected_source: ET.Element | None = None
        for view in views:
            source_id = view.get("data-rig-source-layer")
            if not source_id:
                continue
            try:
                source_elem = _find_by_id(root, source_id)
            except ValueError:
                continue
            if view_id is None or view.get("data-rig-view-def") == view_id:
                _set_display_inline(source_elem)
                if view_id is not None:
                    selected_source = source_elem
            else:
                source_elem.set("style", "display:none")

        if selected_source is not None:
            parents = {child: node for node in root.iter() for child in node}
            top = selected_source
            while top in parents and parents[top] is not root:
                top = parents[top]
            # A view preview is most useful when unrelated authoring/helper
            # layouts do not determine the crop or thumbnail scale.
            for child in root:
                if _local(child.tag) == "g" and child is not top and child.get("id") != MARKER_LAYER_ID:
                    child.set("style", "display:none")
        marker_layer = next((e for e in root.iter() if e.get("id") == MARKER_LAYER_ID), None)
        if marker_layer is not None:
            _set_display_inline(marker_layer)
            if view_id is not None:
                for marker_view in marker_layer:
                    if marker_view.get("data-rig-view") == view_id:
                        _set_display_inline(marker_view)
                    elif marker_view.get("data-rig-view"):
                        marker_view.set("style", "display:none")
            for elem in marker_layer.iter():
                if elem.get("data-rig-joint") == "rig_root":
                    elem.set("style", "display:none")

    payload = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    return cairosvg.svg2png(bytestring=payload, output_width=max(32, int(width)))


def write_repo_preview(
    repo_root: Path,
    output: Path,
    *,
    columns: int = 3,
    tile_width: int = 440,
    rigs_only: bool = False,
) -> Path:
    """Write one labelled contact sheet containing every SVG authoring layout."""

    from PIL import Image, ImageDraw, ImageFont

    repo_root = Path(repo_root).resolve()
    output = Path(output).resolve()
    paths = sorted(
        set((repo_root / "assets").rglob("*.svg"))
        | set((repo_root / "ambition_sprite2d_renderer/data/characters").rglob("*.svg")),
        key=lambda value: str(value.relative_to(repo_root)),
    )
    entries: list[tuple[Path, str | None, str]] = []
    for path in paths:
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError:
            continue
        metadata = next((e for e in root.iter() if e.get("id") == RIG_METADATA_ID), None)
        role = metadata.get("data-ambition-role", "unmanaged") if metadata is not None else "unmanaged"
        if rigs_only and role != "character-rig":
            continue
        views = [
            e.get("data-rig-view-def")
            for e in metadata
            if e.get("data-rig-view-def")
        ] if metadata is not None else []
        if role == "character-rig" and views:
            entries.extend((path, value, role) for value in views if value)
        else:
            entries.append((path, None, role))
    if not entries:
        raise ValueError(f"{repo_root}: no SVG authoring layouts found")

    columns = max(1, int(columns))
    tile_width = max(160, int(tile_width))
    image_height = int(tile_width * 0.72)
    label_height = 54
    tile_height = image_height + label_height
    rows = math.ceil(len(entries) / columns)
    sheet = Image.new("RGB", (columns * tile_width, rows * tile_height), (238, 238, 238))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()

    for index, (path, view_id, role) in enumerate(entries):
        raw = _preview_svg_bytes(
            path,
            width=max(600, tile_width * 2),
            view_id=view_id,
        )
        image = Image.open(io.BytesIO(raw)).convert("RGBA")
        alpha_bbox = image.getchannel("A").getbbox()
        if alpha_bbox:
            image = image.crop(alpha_bbox)
        max_w = tile_width - 20
        max_h = image_height - 20
        scale = min(max_w / max(1, image.width), max_h / max(1, image.height), 1.0)
        size = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
        if size != image.size:
            image = image.resize(size, Image.Resampling.LANCZOS)

        col = index % columns
        row = index // columns
        x0 = col * tile_width
        y0 = row * tile_height
        # White tile makes transparency obvious without competing with rig hues.
        draw.rectangle((x0 + 4, y0 + 4, x0 + tile_width - 5, y0 + image_height - 5), fill=(255, 255, 255))
        px = x0 + (tile_width - image.width) // 2
        py = y0 + (image_height - image.height) // 2
        sheet.paste(image, (px, py), image)
        label = str(path.relative_to(repo_root))
        if view_id is not None:
            label = f"{label} :: {view_id}"
        if len(label) > 62:
            label = "..." + label[-59:]
        draw.text((x0 + 10, y0 + image_height + 8), label, fill=(20, 20, 20), font=font)

        detail = f"{role}; view={view_id or '-'}"
        draw.text((x0 + 10, y0 + image_height + 26), detail, fill=(70, 70, 70), font=font)

    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)
    return output


def _cmd_sync_bind_angles(args: argparse.Namespace) -> int:
    changed = sync_bind_angles(Path(args.svg), view_id=args.view)
    if not changed:
        print(f"{args.svg}: bind angles already match the joints")
    else:
        print(f"{args.svg}: re-derived {len(changed)} bind angles: {', '.join(changed)}")
    return 0


def _cmd_retire_bind_pivots(args: argparse.Namespace) -> int:
    retired = retire_redundant_bind_pivots(
        Path(args.svg), view_id=args.view, tolerance=args.tolerance
    )
    if not retired:
        print(f"{args.svg}: every bind pivot is a deliberate offset; nothing retired")
    else:
        print(
            f"{args.svg}: retired {len(retired)} redundant bind pivot(s) "
            f"(they now follow their bone origin): {', '.join(retired)}"
        )
    return 0


def _cmd_refresh_guides(args: argparse.Namespace) -> int:
    count = refresh_guides(Path(args.svg), view_id=args.view)
    print(f"{args.svg}: re-anchored {count} bone guide(s)")
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    errors = validate(Path(args.svg))
    if errors:
        for error in errors:
            print(error)
        return 1
    print(f"{args.svg}: rig metadata valid")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("summary", help="print a concise rig catalog")
    p.add_argument("svg")

    p = sub.add_parser("validate", help="validate rig metadata references/topology")
    p.add_argument("svg")

    p = sub.add_parser("move-marker", help="move one joint or bind-pivot marker")
    p.add_argument("svg")
    p.add_argument("view")
    p.add_argument("kind", choices=("joint", "bind"))
    p.add_argument("name")
    p.add_argument("x", type=float)
    p.add_argument("y", type=float)

    p = sub.add_parser(
        "sync-bind-angles",
        help="re-derive part bind angles after moving joint markers",
    )
    p.add_argument("svg")
    p.add_argument("--view", default=None)

    p = sub.add_parser(
        "retire-bind-pivots",
        help="delete bind pivots that sit on their bone origin, so a joint is ONE marker",
    )
    p.add_argument("svg")
    p.add_argument("--view", default=None)
    p.add_argument(
        "--tolerance",
        type=float,
        default=2.0,
        help="a pivot further than this from its bone origin was MEANT; keep it",
    )

    p = sub.add_parser("refresh-guides", help="refresh editor bone guides after direct marker edits")
    p.add_argument("svg")
    p.add_argument("--view", default=None)

    p = sub.add_parser("nudge-part", help="move one rigid art part relative to its fixed bind/skeleton")
    p.add_argument("svg")
    p.add_argument("view")
    p.add_argument("part")
    p.add_argument("dx", type=float)
    p.add_argument("dy", type=float)

    p = sub.add_parser("translate-part-source", help="move rigid art and its dedicated bind pivot together")
    p.add_argument("svg")
    p.add_argument("view")
    p.add_argument("part")
    p.add_argument("dx", type=float)
    p.add_argument("dy", type=float)

    p = sub.add_parser("bootstrap-repo", help="one-time migration: embed catalogs from current rig docs")
    p.add_argument("repo", nargs="?", default=".")
    p.add_argument(
        "--force",
        action="store_true",
        help="replace existing managed catalogs (normally preserve manual SVG rig edits)",
    )

    p = sub.add_parser("preview-repo", help="render a labelled contact sheet of SVG authoring layouts")
    p.add_argument("repo", nargs="?", default=".")
    p.add_argument("--output", "-o", default="svg_rig_layout_preview.png")
    p.add_argument("--columns", type=int, default=3)
    p.add_argument("--tile-width", type=int, default=440)
    p.add_argument("--rigs-only", action="store_true")

    args = parser.parse_args(argv)
    if args.command == "summary":
        print(summary(Path(args.svg)))
        return 0
    if args.command == "validate":
        return _cmd_validate(args)
    if args.command == "move-marker":
        move_marker(Path(args.svg), view_id=args.view, kind=args.kind, name=args.name, x=args.x, y=args.y)
        return 0
    if args.command == "retire-bind-pivots":
        return _cmd_retire_bind_pivots(args)
    if args.command == "sync-bind-angles":
        return _cmd_sync_bind_angles(args)
    if args.command == "refresh-guides":
        print(f"updated {refresh_guides(Path(args.svg), view_id=args.view)} guide(s)")
        return 0
    if args.command == "nudge-part":
        nudge_part(Path(args.svg), view_id=args.view, part_name=args.part, dx=args.dx, dy=args.dy)
        return 0
    if args.command == "translate-part-source":
        translate_part_source(Path(args.svg), view_id=args.view, part_name=args.part, dx=args.dx, dy=args.dy)
        return 0
    if args.command == "bootstrap-repo":
        changed = install_repo_metadata(Path(args.repo), force=args.force)
        for path in changed:
            print(path)
        return 0
    if args.command == "preview-repo":
        path = write_repo_preview(
            Path(args.repo),
            Path(args.output),
            columns=args.columns,
            tile_width=args.tile_width,
            rigs_only=args.rigs_only,
        )
        print(path)
        return 0
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
