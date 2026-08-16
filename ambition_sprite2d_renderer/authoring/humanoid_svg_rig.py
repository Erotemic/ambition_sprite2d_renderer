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

The source drawing is allowed to be an exploded or splayed authoring layout.
Joint markers still define attachment geometry and segment lengths, but callers
that care about anatomical IK direction should supply ``LimbPoseHint`` values.
Those pose-space hints choose elbow/knee branches without treating the SVG's
convenient source arrangement as an idle/rest-pose authority.

The default art hierarchy remains explicit on purpose. Unlike PCA's
compatibility extractor, explicit mode has no heuristics based on English group
names, bounding-box joint guesses, or character-specific generated element ids.
For manually traced paper dolls that follow Ambition's standard labels, callers
may opt into ``standard-humanoid`` label binding: labels such as ``Upper Arm -
Near Right`` and ``Hand Tip - Far`` are interpreted together with the view's
``data-rig-side-map``. That mode still never depends on generated XML ids and
validates contradictory anatomy/depth labels as errors. Manual SVG editing
remains the primary authoring workflow.
"""

from __future__ import annotations

import math
import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass, replace
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
_LABEL_BINDING_MODES = {"explicit", "standard-humanoid"}


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
    part_order: str = "attribute"
    arm_pose_hints: Optional[Mapping[str, "LimbPoseHint"]] = None
    leg_pose_hints: Optional[Mapping[str, "LimbPoseHint"]] = None
    arm_bend_overrides: Optional[Mapping[str, float]] = None
    leg_bend_overrides: Optional[Mapping[str, float]] = None
    arm_max_reach_ratio: Optional[float] = None
    label_binding_mode: str = "explicit"
    auxiliary_bones: Tuple["AuxiliaryBoneSpec", ...] = ()


@dataclass(frozen=True)
class AuxiliaryBoneSpec:
    """One non-humanoid rigid bone anchored by a labelled SVG joint marker.

    Auxiliary bones are for paper-doll appendages such as coat tails, skirt
    panels, antennae, or other rigid secondary-motion pieces. The SVG remains
    art/pivot authority; animation clips own the bone rotation channel named by
    ``name``.
    """

    name: str
    parent: str
    joint: str
    rest_angle: float = 0.0


@dataclass(frozen=True)
class LimbPoseHint:
    """Pose-space target used to choose an IK branch independently of SVG layout.

    ``target`` and ``joint`` are offsets from the rig frame's
    ``(center_x, ground_y)``.  They describe an intended posed limb, not the
    exploded/source arrangement used to expose artwork in the SVG.

    The generated rig still measures segment lengths and part pivots from the
    SVG.  This hint controls only which analytic two-bone solution is considered
    anatomically correct.
    """

    target: Point
    joint: Point


@dataclass(frozen=True)
class _PartBinding:
    name: str
    bone: str
    z: float
    include: Tuple[str, ...]
    opacity_channel: Optional[str] = None
    source_order: int = 0


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


def _normal_label(label: str) -> str:
    """Normalize an artist-facing Inkscape label for convention matching."""

    return " ".join(
        label.lower()
        .replace("_", " ")
        .replace("-", " ")
        .replace("/", " ")
        .split()
    )


def _side_from_standard_label(label: str, aliases: Mapping[str, str]) -> Optional[str]:
    """Resolve anatomical/depth words in a standardized artist label.

    Labels may say either ``near``/``far``, anatomical ``left``/``right``, or
    both (for example ``Upper Leg - Near Right``). When both are present they
    must agree with ``data-rig-side-map`` on the view layer. This keeps labels
    human-readable while making accidental anatomy/depth contradictions a hard
    authoring error instead of a silent rig flip.
    """

    words = set(_normal_label(label).split())
    depth = [side for side in ("near", "far") if side in words]
    anatomical = [side for side in aliases if side in words]
    if len(depth) > 1:
        raise ValueError(f"ambiguous near/far side in SVG label {label!r}")
    if len(anatomical) > 1:
        raise ValueError(f"ambiguous anatomical side in SVG label {label!r}")
    mapped = aliases[anatomical[0]] if anatomical else None
    explicit = depth[0] if depth else None
    if mapped and explicit and mapped != explicit:
        raise ValueError(
            f"SVG label {label!r} contradicts data-rig-side-map: "
            f"anatomical {anatomical[0]!r} maps to {mapped!r}, not {explicit!r}"
        )
    return explicit or mapped


def _standard_part_from_label(
    elem: ET.Element,
    aliases: Mapping[str, str],
    source_order: int,
) -> Optional[_PartBinding]:
    """Interpret Ambition's standardized-ish artist labels as rigid parts.

    This mode is deliberately opt-in per character/view. It never inspects
    generated XML ids and therefore survives ordinary Inkscape regrouping and
    id churn. Container labels such as ``Torso`` and ``Arm - Near`` remain
    non-parts; their leaf semantic groups (``Shirt``, ``Upper Arm - Near``,
    ``Hair - Back``...) own the artwork. Dress panel leaf paths are supported
    because a paper-doll skirt needs independent pivots even when the artist
    keeps all panels inside one convenient ``Dress`` group.
    """

    raw = _label(elem) or ""
    label = _normal_label(raw)
    if not label:
        return None
    side = _side_from_standard_label(raw, aliases)
    is_group = _local(elem.tag) == "g"

    limb_kind = None
    if is_group and "upper arm" in label:
        limb_kind = ("arm_u", "arm_u")
    elif is_group and "lower arm" in label:
        limb_kind = ("arm_l", "arm_l")
    elif is_group and (label.startswith("hand ") or label == "hand"):
        limb_kind = ("hand", "arm_hand")
    elif is_group and "upper leg" in label:
        limb_kind = ("leg_u", "leg_u")
    elif is_group and "lower leg" in label:
        limb_kind = ("leg_l", "leg_l")
    elif is_group and (label.startswith("foot ") or label == "foot"):
        limb_kind = ("foot", "leg_foot")
    if limb_kind is not None:
        if side is None:
            raise ValueError(f"standard humanoid part label needs a side: {raw!r}")
        name_suffix, bone_suffix = limb_kind
        include = _direct_drawable_ids(elem, absorb_nested_groups=True, aliases=aliases)
        if not include:
            return None
        return _PartBinding(
            f"{side}_{name_suffix}",
            f"{side}_{bone_suffix}",
            float(source_order),
            include,
            None,
            source_order,
        )

    fixed = {
        "pelvis": ("pelvis", "pelvis"),
        "neck": ("neck", "torso"),
        "shirt": ("torso_shirt", "torso"),
        "shirt details": ("torso_details", "torso"),
        "buttons": ("torso_buttons", "torso"),
        "bodice near": ("torso_bodice_near", "torso"),
        "bodice far": ("torso_bodice_far", "torso"),
        "collar bow": ("torso_collar", "torso"),
        "head base": ("head_base", "head"),
        "facial features": ("head_features", "head"),
        "hair back": ("hair_back", "head"),
        "hair mid": ("hair_mid", "head"),
        "hair front": ("hair_front", "head"),
    }
    if is_group and label in fixed:
        include = _direct_drawable_ids(elem, absorb_nested_groups=True, aliases=aliases)
        if not include:
            return None
        name, bone = fixed[label]
        return _PartBinding(name, bone, float(source_order), include, None, source_order)

    if is_group and label == "head":
        include = _direct_drawable_ids(elem, absorb_nested_groups=True, aliases=aliases)
        if include:
            return _PartBinding(
                "head_misc", "head", float(source_order), include, None, source_order
            )

    # Noether-style panelled dress. Anatomical labels are resolved through the
    # view-level side map so the same convention remains valid in another view.
    if label == "dress base":
        eid = elem.get("id")
        if not eid:
            raise ValueError("dress-base drawable has no SVG id")
        return _PartBinding(
            "dress_back", "center_skirt", float(source_order), (eid,), None, source_order
        )
    if label == "dress fabric center":
        eid = elem.get("id")
        if not eid:
            raise ValueError("center dress panel has no SVG id")
        return _PartBinding(
            "center_skirt", "center_skirt", float(source_order), (eid,), None, source_order
        )
    if label.startswith("dress fabric "):
        panel_side = _side_from_standard_label(raw, aliases)
        if panel_side is None:
            raise ValueError(f"dress panel label needs left/right or near/far: {raw!r}")
        eid = elem.get("id")
        if not eid:
            raise ValueError(f"dress panel {raw!r} has no SVG id")
        return _PartBinding(
            f"{panel_side}_skirt",
            f"{panel_side}_skirt",
            float(source_order),
            (eid,),
            None,
            source_order,
        )
    return None


def _standard_joint_from_label(
    elem: ET.Element, aliases: Mapping[str, str]
) -> Optional[str]:
    raw = _label(elem) or ""
    label = _normal_label(raw)
    if not label:
        return None
    if label in {"waist", "neck"}:
        return label
    if label == "skirt pivot center":
        return "center_skirt_pivot"
    if label.startswith("skirt pivot "):
        side = _side_from_standard_label(raw, aliases)
        if side is None:
            return None
        return f"{side}_skirt_pivot"

    side = _side_from_standard_label(raw, aliases)
    if side is None:
        return None
    for phrase, suffix in (
        ("hand tip", "handtip"),
        ("shoulder", "shoulder"),
        ("elbow", "elbow"),
        ("wrist", "wrist"),
        ("hip", "hip"),
        ("knee", "knee"),
        ("ankle", "ankle"),
        ("toe", "toe"),
    ):
        if phrase in label:
            return f"{side}_{suffix}"
    return None


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


def _is_standard_part_container(
    elem: ET.Element, aliases: Mapping[str, str]
) -> bool:
    """Return whether ``elem`` is a standardized rigid-part boundary.

    Standard-humanoid authoring primarily uses flat semantic groups, but it is
    still useful to allow purely organizational nested groups (for example a
    scalable eye assembly or a hair-detail bundle). Those container groups
    should be absorbed into the surrounding rigid part, while true standardized
    part groups remain ownership boundaries.
    """

    if _local(elem.tag) != "g":
        return False
    raw = _label(elem) or ""
    label = _normal_label(raw)
    if not label:
        return False
    if (
        "upper arm" in label
        or "lower arm" in label
        or label.startswith("hand ")
        or label == "hand"
        or "upper leg" in label
        or "lower leg" in label
        or label.startswith("foot ")
        or label == "foot"
    ):
        return True
    if label in {
        "pelvis",
        "neck",
        "shirt",
        "shirt details",
        "buttons",
        "bodice near",
        "bodice far",
        "collar bow",
        "head base",
        "facial features",
        "hair back",
        "hair mid",
        "hair front",
        "head",
    }:
        return True
    if label == "dress base" or label == "dress fabric center":
        return True
    if label.startswith("dress fabric "):
        return True
    # Side-bearing labels that would normally resolve into a standard part must
    # still count as boundaries even if the current view's side-map would later
    # reject them for ambiguity.
    if _side_from_standard_label(raw, aliases) is not None and label.startswith(
        ("dress fabric ",)
    ):
        return True
    return False



def _direct_drawable_ids(
    group: ET.Element,
    *,
    absorb_nested_groups: bool = False,
    aliases: Optional[Mapping[str, str]] = None,
) -> Tuple[str, ...]:
    """Drawable ids owned by one standardized label group.

    By default this returns only direct child drawables. In standard-humanoid
    mode we also allow purely organizational nested groups and absorb their
    descendants, as long as those nested groups are not themselves standardized
    rigid-part boundaries.
    """

    ids: List[str] = []
    child_aliases: Mapping[str, str] = aliases or {}
    for elem in list(group):
        local = _local(elem.tag)
        if local in _DRAWABLE:
            eid = elem.get("id")
            if not eid:
                raise ValueError(
                    f"drawable under {_label(group)!r} has no id; save from Inkscape "
                    "or add stable ids before extracting"
                )
            ids.append(eid)
            continue
        if not absorb_nested_groups or local != "g":
            continue
        if _parse_part_element(elem) is not None:
            continue
        if _is_standard_part_container(elem, child_aliases):
            continue
        ids.extend(
            _direct_drawable_ids(
                elem,
                absorb_nested_groups=True,
                aliases=child_aliases,
            )
        )
    return tuple(ids)


def _view_root(root: ET.Element, view: str) -> ET.Element:
    for elem in root.iter():
        if _label(elem) == view:
            return elem
    available = sorted({lbl for e in root.iter() if (lbl := _label(e))})
    raise KeyError(f"SVG view {view!r} not found; labelled groups include {available}")

def _resolve_nested_ownership(
    entries: List[Tuple[int, "_PartBinding"]],
) -> List["_PartBinding"]:
    """**The most specific layer owns the art.**

    ⛔ **an artist nesting one recognised part inside another used to break the
    build.** Jon reorganised Carl Stargan's SVG so his hair sublayers sit inside
    `Head`, and the Patent Clerk's hands inside the forearms — both perfectly
    ordinary Inkscape structure — and the rig refused to build at all:
    *"does not have one-to-one drawable ownership: multiply_assigned={'path1933':
    ['head', 'hair_front'], ...}"*. The container absorbs nested groups so its
    leftovers (`head_misc`) can be drawn, which means it also absorbed the
    sublayers that are parts in their own right.

    So a drawable claimed by several bindings goes to the DEEPEST one, and a
    container keeps only what no child part claimed. That is what "leftovers"
    meant all along; it was just never subtracted. A container left with nothing
    is dropped rather than published empty.

    ⚠ the one-to-one check downstream is NOT relaxed — it still fails on art a
    binding genuinely cannot place, which is the error worth keeping.
    """

    owner: Dict[str, Tuple[int, int]] = {}
    for index, (depth, binding) in enumerate(entries):
        for drawable_id in binding.include:
            best = owner.get(drawable_id)
            if best is None or depth > best[0]:
                owner[drawable_id] = (depth, index)
    resolved: List[_PartBinding] = []
    for index, (_depth, binding) in enumerate(entries):
        keep = tuple(
            drawable_id
            for drawable_id in binding.include
            if owner[drawable_id][1] == index
        )
        if keep:
            resolved.append(replace(binding, include=keep))
    return resolved


def _collect_parts(
    root: ET.Element, view: str, *, binding_mode: str = "explicit"
) -> List[_PartBinding]:
    layer = _view_root(root, view)
    side_map = _parse_side_map(layer)
    if binding_mode not in _LABEL_BINDING_MODES:
        raise ValueError(
            f"unsupported SVG label binding mode {binding_mode!r}; "
            f"expected one of {sorted(_LABEL_BINDING_MODES)}"
        )
    parts: List[_PartBinding] = []
    source_order = 0
    drawable_order = {
        elem.get("id"): index
        for index, elem in enumerate(layer.iter())
        if _local(elem.tag) in _DRAWABLE and elem.get("id")
    }
    # How deep each element sits under the view layer, so nested parts can be
    # resolved most-specific-first (see `_resolve_nested_ownership`).
    depths: Dict[int, int] = {id(layer): 0}
    for parent in layer.iter():
        for child in parent:
            depths[id(child)] = depths.get(id(parent), 0) + 1
    nested: List[Tuple[int, _PartBinding]] = []
    for elem in layer.iter():
        if binding_mode == "standard-humanoid":
            binding = _standard_part_from_label(elem, side_map, source_order)
            if binding is None:
                continue
            actual_order = min(drawable_order[eid] for eid in binding.include)
            nested.append(
                (
                    depths.get(id(elem), 0),
                    _PartBinding(
                        binding.name,
                        binding.bone,
                        float(actual_order),
                        binding.include,
                        binding.opacity_channel,
                        actual_order,
                    ),
                )
            )
            source_order += 1
            continue
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
        nested.append(
            (
                depths.get(id(elem), 0),
                _PartBinding(name, bone, z, include, opacity, source_order),
            )
        )
        source_order += 1
    # Both binding modes take descendants, so both can nest — Carl Stargan's
    # hair inside his head is `explicit`, the Patent Clerk's hands inside his
    # forearms are too.
    parts = _resolve_nested_ownership(nested)
    if not parts:
        raise ValueError(f"SVG view {view!r} contains no rig-part groups")
    if binding_mode == "standard-humanoid":
        parts.sort(key=lambda part: part.source_order)
    names = [p.name for p in parts]
    if len(names) != len(set(names)):
        dupes = sorted({n for n in names if names.count(n) > 1})
        raise ValueError(f"duplicate part names in {view!r}: {dupes}")
    return parts


def _collect_joint_ids(
    root: ET.Element, view: str, *, binding_mode: str = "explicit"
) -> Dict[str, str]:
    layer = _view_root(root, view)
    side_map = _parse_side_map(layer)
    if binding_mode not in _LABEL_BINDING_MODES:
        raise ValueError(
            f"unsupported SVG label binding mode {binding_mode!r}; "
            f"expected one of {sorted(_LABEL_BINDING_MODES)}"
        )
    out: Dict[str, str] = {}
    for elem in layer.iter():
        name = _joint_name(elem)
        if (
            name is None
            and binding_mode == "standard-humanoid"
            and _local(elem.tag) in {"circle", "ellipse"}
        ):
            name = _standard_joint_from_label(elem, side_map)
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


def _drawable_ids_in_view(
    root: ET.Element, view: str, *, binding_mode: str = "explicit"
) -> List[str]:
    """Return drawable ids in the view that are not joint markers."""

    layer = _view_root(root, view)
    side_map = _parse_side_map(layer)
    ids: List[str] = []
    for elem in layer.iter():
        if _local(elem.tag) not in _DRAWABLE:
            continue
        if _joint_name(elem) is not None:
            continue
        if (
            binding_mode == "standard-humanoid"
            and _local(elem.tag) in {"circle", "ellipse"}
            and _standard_joint_from_label(elem, side_map) is not None
        ):
            continue
        eid = elem.get("id")
        if not eid:
            raise ValueError(
                f"drawable in SVG view {view!r} has no id; save from Inkscape "
                "or assign stable ids before extracting"
            )
        ids.append(eid)
    return ids


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


def _bend_for_side(
    pose_hints: Optional[Mapping[str, LimbPoseHint]],
    overrides: Optional[Mapping[str, float]],
    side: str,
    *,
    center_x: float,
    ground_y: float,
    root: Point,
    joint: Point,
    target: Point,
    l1: float,
    l2: float,
) -> float:
    """Choose the IK branch from pose authority before consulting SVG layout."""
    if pose_hints is not None and side in pose_hints:
        hint = pose_hints[side]
        hinted_joint = (center_x + hint.joint[0], ground_y + hint.joint[1])
        hinted_target = (center_x + hint.target[0], ground_y + hint.target[1])
        return _choose_bend(root, hinted_joint, hinted_target, l1, l2)
    if overrides is not None and side in overrides:
        value = float(overrides[side])
        return 1.0 if value >= 0.0 else -1.0
    return _choose_bend(root, joint, target, l1, l2)


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
    preserve_svg_draw_order: bool = False,
) -> dict:
    """Extract one labelled SVG view into a complete ``RigDocument`` mapping."""

    svg_path = Path(svg_path).resolve()
    rig_dir = Path(rig_dir).resolve()
    root = ET.fromstring(svg_path.read_bytes())
    parts = _collect_parts(
        root, spec.view, binding_mode=spec.label_binding_mode
    )
    joint_ids = _collect_joint_ids(
        root, spec.view, binding_mode=spec.label_binding_mode
    )
    drawable_ids = set(
        _drawable_ids_in_view(
            root, spec.view, binding_mode=spec.label_binding_mode
        )
    )
    ownership: Dict[str, List[str]] = {}
    for binding in parts:
        for drawable_id in binding.include:
            ownership.setdefault(drawable_id, []).append(binding.name)
    unassigned = sorted(drawable_ids - set(ownership))
    multiply_assigned = {
        drawable_id: owners
        for drawable_id, owners in sorted(ownership.items())
        if len(owners) > 1
    }
    if unassigned or multiply_assigned:
        details: List[str] = []
        if unassigned:
            details.append(f"unassigned={unassigned}")
        if multiply_assigned:
            details.append(f"multiply_assigned={multiply_assigned}")
        raise ValueError(
            f"SVG view {spec.view!r} does not have one-to-one drawable ownership: "
            + "; ".join(details)
        )
    joints = _joint_positions(svg_path, spec.view, joint_ids, spec.ref_dpi)

    required_joints = set(_required_joints())
    required_joints.update(aux.joint for aux in spec.auxiliary_bones)
    missing = sorted(required_joints - set(joints))
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
    for aux in spec.auxiliary_bones:
        bone_specs.append((aux.name, aux.parent, mapped[aux.joint], None))
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
    for aux in spec.auxiliary_bones:
        source_pivot[aux.name] = joints[aux.joint]
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

    auxiliary_rest_angles = {aux.name: float(aux.rest_angle) for aux in spec.auxiliary_bones}
    for name, parent, origin, distal in bone_specs:
        if distal is None:
            angle, length = auxiliary_rest_angles.get(name, 0.0), 0.0
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
    if spec.part_order not in {"attribute", "document"}:
        raise ValueError(
            f"unsupported SVG part order policy {spec.part_order!r}; "
            "expected 'attribute' or 'document'"
        )

    rig_parts: List[dict] = []
    for document_index, binding in enumerate(parts):
        if binding.bone not in bone_names:
            raise ValueError(
                f"part {binding.name!r} in {spec.view!r} binds unknown bone "
                f"{binding.bone!r}"
            )
        pivot = source_pivot[binding.bone]
        part = {
            "name": binding.name,
            "bone": binding.bone,
            "z": (
                float(document_index)
                if spec.part_order == "document"
                else binding.z
            ),
            "kind": "sprite",
            "include": list(binding.include),
            "pivot": [round(pivot[0], 3), round(pivot[1], 3)],
            "rest_angle": round(world[binding.bone][1], 4),
            "svg_source_order": int(binding.source_order),
        }
        if binding.opacity_channel:
            part["opacity_channel"] = binding.opacity_channel
        rig_parts.append(part)
    rig_parts.sort(
        key=lambda p: (
            float(p["z"]),
            int(p.get("svg_source_order", 0)),
        )
    )

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
                "bend": _bend_for_side(
                    spec.leg_pose_hints,
                    spec.leg_bend_overrides,
                    side,
                    center_x=spec.center_x,
                    ground_y=spec.ground_y,
                    root=hip,
                    joint=knee,
                    target=ankle,
                    l1=leg_u,
                    l2=leg_l,
                ),
            }
        )
        arm_pose_hint = (
            spec.arm_pose_hints.get(side)
            if spec.arm_pose_hints is not None
            else None
        )
        arm_rest_x = (
            float(arm_pose_hint.target[0])
            if arm_pose_hint is not None
            else wrist[0] - spec.center_x
        )
        arm_rest_y = (
            float(arm_pose_hint.target[1])
            if arm_pose_hint is not None
            else wrist[1] - spec.ground_y
        )
        arm_chain = {
            "upper": f"{side}_arm_u",
            "lower": f"{side}_arm_l",
            "end": f"{side}_arm_hand",
            "channel_prefix": f"{side}_hand",
            "rest_x": round(arm_rest_x, 4),
            "rest_y": round(arm_rest_y, 4),
            "rest_pitch": round(world[f"{side}_arm_hand"][1], 4),
            # Explicit natural-pose rigs want the hand artwork to inherit the
            # lower forearm unless a clip deliberately authors a world pitch.
            # Legacy SVG-layout rigs retain the historic world-pitch fallback.
            "pitch_mode": "follow_lower" if arm_pose_hint is not None else "world",
            "bend": _bend_for_side(
                spec.arm_pose_hints,
                spec.arm_bend_overrides,
                side,
                center_x=spec.center_x,
                ground_y=spec.ground_y,
                root=shoulder,
                joint=elbow,
                target=wrist,
                l1=arm_u,
                l2=arm_l,
            ),
            "pose_authority": "explicit-hint" if arm_pose_hint is not None else "svg-layout",
        }
        if spec.arm_max_reach_ratio is not None:
            arm_chain["max_reach_ratio"] = float(spec.arm_max_reach_ratio)
        ik_chains.append(arm_chain)

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
        "sprite_tuning": {
            "collision_scale": spec.collision_scale,
            "part_order": spec.part_order,
        },
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
    "AuxiliaryBoneSpec",
    "HumanoidViewSpec",
    "build_humanoid_view_document",
    "merge_generated_geometry",
]
