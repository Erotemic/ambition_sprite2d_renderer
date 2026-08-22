"""Additive SVG + rigid-bone proof of concept for Mary-O v2.

The shipped Mary-O targets remain procedural and pixel-locked. This module
captures their accepted anatomy into one editable SVG and builds tiny rigid
paper-doll rigs from it:

* side-view arms and legs are one rigid vector group per visible limb;
* front/death-view arms and legs are one rigid vector group per character side;
* no elbow or knee articulation and no separate rotated-limb artwork;
* transient transformation visuals remain Python postprocess effects.

The SVG is deliberately an authoring document, not flattened interchange. Each
form has a side view and a front/death view. Parts and their leaf geometry have
semantic ids/labels, while pivot helpers live in hidden guide groups. Moving a
part wrapper in Inkscape moves its art and pivot together; the loader evaluates
SVG transforms directly when rebuilding the rig.
"""

from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass, replace
import math
from pathlib import Path
import re
import warnings
import xml.etree.ElementTree as ET
from typing import Dict, Iterable, Iterator, List, Mapping, Sequence, Tuple

from PIL import Image

from ...authoring.rigdoc import RigDocument
from ._mary_o_v2_art import (
    _ARM_REFERENCE_WIDTH,
    _HEAD_BOTTOM_LOCAL,
    _ScaledAbout,
    _arm_k,
    _draw_arm,
    _draw_body_front,
    _draw_body_side,
    _draw_dead_eyes_front,
    _draw_dead_mouth_front,
    _draw_fire_orb,
    _draw_head_foundation_side,
    _draw_head_front,
    _draw_leg,
    _draw_power_loss_sparkles,
    _draw_powered_front_garment,
    _draw_short_pinafore_front,
    _draw_side_face_features,
    _draw_side_pose,
    _draw_sleeve_wing_side,
    _draw_transform_aura,
    _draw_transform_outfit_stars,
    _draw_v2_ear_star,
    _draw_v2_hat_wing,
    _draw_wing_side,
    _draw_wings_front,
    _side_pose_head_origin,
    _snap_side_head_origin,
)
from ._mary_o_v2_model import (
    AUTHORING_FRAME_SIZE,
    DEAD_ARM_X,
    DEAD_HIP_X,
    DEAD_HIP_Y,
    DEAD_SHOULDER_Y,
    DEAD_WING_X,
    DEAD_WING_Y,
    FIRE_FORM,
    LOGICAL_SIZE,
    SCALE,
    SHORT_FORM,
    SHORT_POSES,
    TALL_FORM,
    TALL_LIKE_POSES,
    FormSpec,
    Pose,
    _fire_accessory_t,
    _magic_stage_value,
    rig_for,
)

SVG_NS = "http://www.w3.org/2000/svg"
INK_NS = "http://www.inkscape.org/namespaces/inkscape"
SODIPODI_NS = "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
XLINK_NS = "http://www.w3.org/1999/xlink"
ET.register_namespace("", SVG_NS)
ET.register_namespace("inkscape", INK_NS)
ET.register_namespace("sodipodi", SODIPODI_NS)
ET.register_namespace("xlink", XLINK_NS)
INK_LABEL = f"{{{INK_NS}}}label"
INK_GROUPMODE = f"{{{INK_NS}}}groupmode"
SODIPODI_INSENSITIVE = f"{{{SODIPODI_NS}}}insensitive"
XLINK_HREF = f"{{{XLINK_NS}}}href"

# The logical 24x32 sprite is rasterized at 3x into 72x96 and then centred in
# the 80x96 authored frame. Capturing in authored pixels preserves the accepted
# placement while giving Inkscape a straightforward one-unit-per-reference-px
# coordinate system.
_NATIVE_W = LOGICAL_SIZE[0] * SCALE
_NATIVE_H = LOGICAL_SIZE[1] * SCALE
_FRAME_W, _FRAME_H = AUTHORING_FRAME_SIZE
_CANVAS_X = (_FRAME_W - _NATIVE_W) // 2
_CANVAS_Y = _FRAME_H - _NATIVE_H
_VIEW_GAP = 12
_AUTHORING_LIBRARY_HEIGHT = 760
_VIEW_PITCH_X = _FRAME_W + _VIEW_GAP
_VIEW_PITCH_Y = _FRAME_H + _VIEW_GAP
_SOURCE_WIDTH = 600
_SOURCE_HEIGHT = _AUTHORING_LIBRARY_HEIGHT + _FRAME_H * 2 + _VIEW_GAP
_REF_DPI = 25.4  # one SVG user unit -> one reference pixel

_FORM_KEYS = {
    SHORT_FORM.target_name: "short",
    TALL_FORM.target_name: "tall",
    FIRE_FORM.target_name: "fire",
}
_FORM_TITLES = {"short": "Short", "tall": "Tall", "fire": "Fire"}
_VIEW_LABELS = {
    (key, projection): f"Mary-O - {_FORM_TITLES[key]} {projection.title()}"
    for key in ("short", "tall", "fire")
    for projection in ("side", "front")
}
_VIEW_ORIGINS = {
    (key, projection): (
        index * _VIEW_PITCH_X,
        _AUTHORING_LIBRARY_HEIGHT if projection == "side" else _AUTHORING_LIBRARY_HEIGHT + _VIEW_PITCH_Y,
    )
    for index, key in enumerate(("short", "tall", "fire"))
    for projection in ("side", "front")
}


def _svg(tag: str) -> str:
    return f"{{{SVG_NS}}}{tag}"


def _find_element(root: ET.Element, element_id: str) -> ET.Element:
    node = next((node for node in root.iter() if node.get("id") == element_id), None)
    if node is None:
        raise ValueError(f"Mary-O SVG POC element not found: {element_id}")
    return node


def _rename(node: ET.Element, *, element_id: str, label: str) -> None:
    node.set("id", element_id)
    node.set(INK_LABEL, label)


def _vertical_segment(node: ET.Element, x: float, y1: float, y2: float) -> None:
    node.set("d", f"M {_fmt(x)} {_fmt(y1)} L {_fmt(x)} {_fmt(y2)}")


def _hat_fill_curve(node: ET.Element, *, points: Sequence[tuple[float, float]]) -> None:
    node.tag = _svg("polygon")
    node.attrib.pop("d", None)
    node.set("points", " ".join(f"{_fmt(x)},{_fmt(y)}" for x, y in [*points, points[0]]))


def _hat_outline_curve(node: ET.Element, *, points: Sequence[tuple[float, float]]) -> None:
    node.set("d", "M " + " L ".join(f"{_fmt(x)} {_fmt(y)}" for x, y in points))


def _dedupe_pupil_rects(group: ET.Element, *, prefix: str, labels: Sequence[str]) -> None:
    pupils = [
        child
        for child in list(group)
        if child.tag == _svg("rect")
        and child.get("fill") == "#1c1613"
        and float(child.get("width", "99")) <= 1.0
        and float(child.get("height", "99")) <= 2.0
    ]
    unique: list[ET.Element] = []
    seen: set[tuple[str | None, str | None, str | None, str | None]] = set()
    for node in pupils:
        key = (
            node.get("x"),
            node.get("y"),
            node.get("width"),
            node.get("height"),
        )
        if key in seen:
            group.remove(node)
            continue
        seen.add(key)
        unique.append(node)
    unique.sort(key=lambda node: (float(node.get("x", "0")), float(node.get("y", "0"))))
    for node in unique:
        group.remove(node)
    for idx, node in enumerate(unique):
        label = labels[min(idx, len(labels) - 1)]
        slug = _slug(label)
        _rename(node, element_id=f"{prefix}_{slug}", label=label)
        group.append(node)


def _polish_generated_svg(root: ET.Element) -> ET.Element:
    """Apply authoring-oriented cleanup on top of the procedural capture.

    The authoring SVG benefits from a few semantic cleanups beyond the raw
    procedural capture, especially clearer suspender naming and vertical strap
    cleanup. Further simplification of hats, eyes, and arm rectangles happens in
    `_postprocess_svg_source` before this helper runs.
    """

    strap_specs = (
        ("maryo_short_side_torso_torso_outfit_line_01", "maryo_short_side_torso_torso_outfit_character_right_suspender_strap", "Character Right Suspender Strap", 38, 79, 84),
        ("maryo_short_side_torso_torso_outfit_line_02", "maryo_short_side_torso_torso_outfit_character_left_suspender_strap", "Character Left Suspender Strap", 45, 79, 84),
        ("maryo_tall_side_torso_torso_outfit_line_01", "maryo_tall_side_torso_torso_outfit_character_right_suspender_strap", "Character Right Suspender Strap", 36, 44, 52),
        ("maryo_tall_side_torso_torso_outfit_line_02", "maryo_tall_side_torso_torso_outfit_character_left_suspender_strap", "Character Left Suspender Strap", 47, 44, 52),
        ("maryo_short_front_torso_front_torso_outfit_line_01", "maryo_short_front_torso_front_torso_outfit_character_right_suspender_strap", "Character Right Suspender Strap", 36, 77, 82),
        ("maryo_short_front_torso_front_torso_outfit_line_02", "maryo_short_front_torso_front_torso_outfit_character_left_suspender_strap", "Character Left Suspender Strap", 42, 77, 82),
        ("maryo_tall_front_torso_front_torso_outfit_line_01", "maryo_tall_front_torso_front_torso_outfit_character_right_suspender_strap", "Character Right Suspender Strap", 33, 41, 50),
        ("maryo_tall_front_torso_front_torso_outfit_line_02", "maryo_tall_front_torso_front_torso_outfit_character_left_suspender_strap", "Character Left Suspender Strap", 47, 41, 50),
    )
    for old_id, new_id, label, x, y1, y2 in strap_specs:
        node = _find_element(root, old_id)
        _rename(node, element_id=new_id, label=label)
        _vertical_segment(node, x, y1, y2)

    pupil_groups = (
        ("maryo_short_side_head_head_foundation", "maryo_short_side_head_head_foundation", ("Visible Pupil",)),
        ("maryo_tall_side_head_head_foundation", "maryo_tall_side_head_head_foundation", ("Visible Pupil",)),
        ("maryo_fire_side_head_head_foundation", "maryo_fire_side_head_head_foundation", ("Visible Pupil",)),
        ("maryo_short_front_head_front_head_anatomy", "maryo_short_front_head_front_head_anatomy", ("Character Right Pupil", "Character Left Pupil")),
        ("maryo_tall_front_head_front_head_anatomy", "maryo_tall_front_head_front_head_anatomy", ("Character Right Pupil", "Character Left Pupil")),
        ("maryo_fire_front_head_front_head_anatomy", "maryo_fire_front_head_front_head_anatomy", ("Character Right Pupil", "Character Left Pupil")),
    )
    for group_id, prefix, labels in pupil_groups:
        _dedupe_pupil_rects(_find_element(root, group_id), prefix=prefix, labels=labels)

    return root


def _translate_expr(dx: float, dy: float) -> str:
    return f"translate({_fmt(dx)} {_fmt(dy)})"


def _set_use_ref(node: ET.Element, ref_id: str) -> None:
    node.set("href", f"#{ref_id}")
    node.set(XLINK_HREF, f"#{ref_id}")


def _form_for_key(key: str) -> FormSpec:
    return {"short": SHORT_FORM, "tall": TALL_FORM, "fire": FIRE_FORM}[key]


def _side_layout_for_key(key: str) -> _Layout:
    return _layout(_form_for_key(key), Pose())


def _front_layout_for_key(key: str) -> _FrontLayout:
    return _front_layout(_form_for_key(key), Pose(mode="dead"))


def _part_anchor(key: str, projection: str, part_name: str) -> tuple[float, float]:
    if projection == "side":
        g = _side_layout_for_key(key)
        return {
            "far_arm": g.back_arm_origin,
            "far_leg": g.back_leg_origin,
            "back_wings": (g.body_x, g.body_top),
            "near_leg": g.near_leg_origin,
            "torso": (g.body_x, g.body_top),
            "head": (g.head_x + 5.05, g.head_top + 7.5),
            "near_arm": g.near_arm_origin,
        }[part_name]
    g = _front_layout_for_key(key)
    leg_x_offset = 1.1
    arm_x_offset = 0.8 * _arm_k(_form_for_key(key))
    return {
        "character_right_leg": (g.character_right_hip[0] - leg_x_offset, g.character_right_hip[1]),
        "character_left_leg": (g.character_left_hip[0] - leg_x_offset, g.character_left_hip[1]),
        "back_wings": g.wing_anchor,
        "torso": (g.body_x, g.body_top),
        "head": (g.head_x + 5.5, g.head_top + 7.5),
        "foreground_garment": (g.body_x, g.body_top),
        "death_expression": (g.head_x + 5.5, g.head_top + 7.5),
        "character_right_arm": (g.character_right_shoulder[0] - arm_x_offset, g.character_right_shoulder[1]),
        "character_left_arm": (g.character_left_shoulder[0] - arm_x_offset, g.character_left_shoulder[1]),
    }[part_name]




def _authored_point(point: tuple[float, float]) -> tuple[float, float]:
    return (
        float(int(round(point[0] * SCALE)) + _CANVAS_X),
        float(int(round(point[1] * SCALE)) + _CANVAS_Y),
    )


def _head_scale_anchor(key: str, projection: str) -> tuple[float, float]:
    if projection == "side":
        g = _side_layout_for_key(key)
        return _authored_point((g.head_x + 5.05, g.head_top + _HEAD_BOTTOM_LOCAL))
    g = _front_layout_for_key(key)
    return _authored_point((g.head_x + 5.5, g.head_top + _HEAD_BOTTOM_LOCAL))

def _slot_anchor(key: str, projection: str, part_name: str) -> tuple[float, float]:
    column_x = {"short": 0.0, "tall": _VIEW_PITCH_X, "fire": _VIEW_PITCH_X * 2}[key]
    if projection == "side":
        tray_y = 76.0
        rel = {
            "head": (18.0, 18.0),
            "torso": (8.0, 86.0),
            "near_arm": (58.0, 18.0),
            "far_arm": (58.0, 54.0),
            "near_leg": (58.0, 94.0),
            "far_leg": (58.0, 142.0),
            "back_wings": (10.0, 150.0),
        }[part_name]
    else:
        tray_y = 244.0
        rel = {
            "head": (18.0, 18.0),
            "death_expression": (18.0, 52.0),
            "torso": (8.0, 92.0),
            "foreground_garment": (8.0, 128.0),
            "character_right_arm": (58.0, 92.0),
            "character_left_arm": (58.0, 128.0),
            "character_right_leg": (58.0, 162.0),
            "character_left_leg": (58.0, 194.0),
            "back_wings": (8.0, 164.0),
        }[part_name]
    return (column_x + rel[0], tray_y + rel[1])


def _create_master_group(
    master_layer: ET.Element,
    source_group: ET.Element,
    *,
    master_id: str,
    label: str,
    source_anchor: tuple[float, float],
    slot_anchor: tuple[float, float],
) -> ET.Element:
    master = ET.Element(_svg("g"))
    master.set("id", master_id)
    master.set(INK_LABEL, label)
    master.set("data-authoring-master", "true")
    master.set("transform", _translate_expr(slot_anchor[0] - source_anchor[0], slot_anchor[1] - source_anchor[1]))
    for child in list(source_group):
        source_group.remove(child)
        master.append(child)
    master_layer.append(master)
    return master


def _clear_children(node: ET.Element) -> None:
    for child in list(node):
        node.remove(child)


def _install_clone_art(
    art_group: ET.Element,
    *,
    master_id: str,
    source_slot_anchor: tuple[float, float],
    target_anchor: tuple[float, float],
) -> None:
    _clear_children(art_group)
    _append_clone_instance(
        art_group,
        master_id=master_id,
        source_slot_anchor=source_slot_anchor,
        target_anchor=target_anchor,
        label="Clone Assembly",
    )


def _append_clone_instance(
    container: ET.Element,
    *,
    master_id: str,
    source_slot_anchor: tuple[float, float],
    target_anchor: tuple[float, float],
    scale: float = 1.0,
    label: str | None = None,
    instance_id: str | None = None,
) -> ET.Element:
    outer = ET.SubElement(container, _svg("g"))
    if instance_id is not None:
        outer.set("id", instance_id)
    if label is not None:
        outer.set(INK_LABEL, label)
    outer.set("transform", _translate_expr(target_anchor[0], target_anchor[1]))
    parent = outer
    if abs(scale - 1.0) > 1e-6:
        parent = ET.SubElement(outer, _svg("g"))
        parent.set("transform", f"scale({_fmt(scale)})")
    clone = ET.SubElement(parent, _svg("use"))
    _set_use_ref(clone, master_id)
    clone.set("transform", _translate_expr(-source_slot_anchor[0], -source_slot_anchor[1]))
    return outer


def _append_anchor_clone(
    container: ET.Element,
    *,
    master_id: str,
    source_slot_anchor: tuple[float, float],
    target_anchor: tuple[float, float],
    scale: float = 1.0,
) -> None:
    _append_clone_instance(
        container,
        master_id=master_id,
        source_slot_anchor=source_slot_anchor,
        target_anchor=target_anchor,
        scale=scale,
    )


def _find_semantic_child(group: ET.Element, suffix: str) -> ET.Element | None:
    return next((child for child in list(group) if (child.get("id") or "").endswith(suffix)), None)


def _head_scale_ratio(key: str) -> float:
    return float(getattr(_form_for_key(key), "head_scale", 1.0) or 1.0)


def _hex_color(color) -> str:
    return f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"


def _neutral_head_form() -> FormSpec:
    return replace(TALL_FORM, magic_stage=0, power="tall", head_scale=1.0)


def _capture_neutral_head_art(projection: str) -> ET.Element:
    form = _neutral_head_form()
    painter = _paint_side_view if projection == "side" else _paint_front_view
    fragment = painter(form)
    temp = ET.fromstring(
        f'<svg xmlns="{SVG_NS}" xmlns:inkscape="{INK_NS}">{fragment}</svg>'
    )
    wrapper = next(child for child in temp if child.get("data-rig-part") == "head")
    art = next(child for child in wrapper if child.get("data-rig-art") == "true")
    for group in list(art):
        gid = group.get("id") or ""
        if gid.endswith("_head_foundation") or gid.endswith("_front_head_anatomy"):
            _replace_hat_dome_with_angular_polygon(group)
            _simplify_eye_geometry(group)
            _lift_pupils_to_front(group)
            if projection == "side":
                _dedupe_pupil_rects(group, prefix="neutral_side", labels=("Visible Pupil",))
            else:
                _dedupe_pupil_rects(
                    group,
                    prefix="neutral_front",
                    labels=("Character Right Pupil", "Character Left Pupil"),
                )
    return art


def _primitive_group(
    primitive_layer: ET.Element,
    *,
    elements: Sequence[ET.Element],
    master_id: str,
    label: str,
    source_anchor: tuple[float, float],
    slot_anchor: tuple[float, float],
    recolor_hexes: Sequence[str] = (),
) -> tuple[str, tuple[float, float]]:
    holder = ET.Element(_svg("g"))
    recolor = {value.lower() for value in recolor_hexes}
    for index, element in enumerate(elements, start=1):
        fill = (element.get("fill") or "").lower()
        stroke = (element.get("stroke") or "").lower()
        if fill in recolor:
            element.set("fill", "currentColor")
        if stroke in recolor:
            element.set("stroke", "currentColor")
        element.set("id", f"{master_id}_shape_{index:02d}")
        element.set(INK_LABEL, f"{label} Shape {index}")
        holder.append(element)
    _create_master_group(
        primitive_layer,
        holder,
        master_id=master_id,
        label=label,
        source_anchor=source_anchor,
        slot_anchor=slot_anchor,
    )
    return master_id, slot_anchor


def _recolor_subtree_currentcolor(group: ET.Element, recolor_hexes: Sequence[str]) -> None:
    recolor = {value.lower() for value in recolor_hexes}
    for element in group.iter():
        fill = (element.get("fill") or "").lower()
        stroke = (element.get("stroke") or "").lower()
        if fill in recolor:
            element.set("fill", "currentColor")
        if stroke in recolor:
            element.set("stroke", "currentColor")


def _append_component_shapes(container: ET.Element, *, child_id: str, label: str, elements: Sequence[ET.Element]) -> None:
    for index, element in enumerate(elements, start=1):
        element.set("id", f"{child_id}_shape_{index:02d}")
        element.set(INK_LABEL, f"{label} Shape {index}")
        container.append(element)


def _editable_head_component_group(
    primitive_layer: ET.Element,
    *,
    master_id: str,
    label: str,
    source_anchor: tuple[float, float],
    slot_anchor: tuple[float, float],
    segments: Sequence[tuple[str, Sequence[ET.Element], str, Sequence[str], str | None, str | None]],
) -> tuple[tuple[str, tuple[float, float]], dict[str, tuple[str, tuple[float, float], str | None]]]:
    master = ET.Element(_svg("g"))
    master.set("id", master_id)
    master.set(INK_LABEL, label)
    master.set("data-authoring-master", "true")
    components: dict[str, tuple[str, tuple[float, float], str | None]] = {}
    translate = _translate_expr(slot_anchor[0] - source_anchor[0], slot_anchor[1] - source_anchor[1])
    for name, elements, child_label, recolors, role, display_color in segments:
        child_id = f"{master_id}_{name}"
        child = ET.Element(_svg("g"))
        child.set("id", child_id)
        child.set(INK_LABEL, child_label)
        child.set("transform", translate)
        if display_color is not None:
            child.set("color", display_color)
        _recolor_subtree_currentcolor(child, ())
        for element in elements:
            child.append(element)
        _recolor_subtree_currentcolor(child, recolors)
        _append_component_shapes(child, child_id=child_id, label=child_label, elements=list(child))
        master.append(child)
        components[name] = (child_id, slot_anchor, role)
    primitive_layer.append(master)
    return (master_id, slot_anchor), components


def _head_authoring_components(primitive_layer: ET.Element) -> tuple[dict[str, tuple[str, tuple[float, float], str | None]], dict[str, tuple[str, tuple[float, float]]]]:
    normal = TALL_FORM.palette
    side_anchor = _head_scale_anchor("tall", "side")
    front_anchor = _head_scale_anchor("tall", "front")
    side_art = _capture_neutral_head_art("side")
    front_art = _capture_neutral_head_art("front")
    side_foundation = _find_semantic_child(side_art, "_head_foundation")
    side_face = _find_semantic_child(side_art, "_face_details")
    front_foundation = _find_semantic_child(front_art, "_front_head_anatomy")
    if side_foundation is None or side_face is None or front_foundation is None:
        raise ValueError("neutral Mary-O head capture is incomplete")

    side = list(side_foundation)
    front = list(front_foundation)
    if len(side) != 17 or len(front) != 18:
        raise ValueError(
            f"unexpected neutral Mary-O head topology: side={len(side)} front={len(front)}"
        )

    side_master, side_components = _editable_head_component_group(
        primitive_layer,
        master_id="maryo_component_normal_side_head",
        label="Editable Normal Side Head",
        source_anchor=side_anchor,
        slot_anchor=(108.0, 64.0),
        segments=(
            ("rear_hair", side[0:2], "Rear Hair", (_hex_color(normal.hair),), "hair", _hex_color(normal.hair)),
            ("skin", [side[2]], "Face", (_hex_color(normal.skin),), "skin", _hex_color(normal.skin)),
            ("nose_shadow", [side[3]], "Nose Shadow", ("#dfa47c",), "nose", "#dfa47c"),
            ("foreground_hair", side[4:8], "Foreground Hair", (_hex_color(normal.hair),), "hair", _hex_color(normal.hair)),
            ("ponytail_tie", side[8:10], "Ponytail Tie", (), None, None),
            ("hat_dome", [side[10]], "Hat Dome", (_hex_color(normal.cap),), "cap", _hex_color(normal.cap)),
            ("hat_trim", side[11:14], "Hat Trim", (_hex_color(normal.accent),), "accent", _hex_color(normal.accent)),
            ("eye", side[14:17], "Eye", (), None, None),
            ("face_details", list(side_face), "Face Details", (), None, None),
        ),
    )

    front_master, front_components = _editable_head_component_group(
        primitive_layer,
        master_id="maryo_component_normal_front_head",
        label="Editable Normal Front Head",
        source_anchor=front_anchor,
        slot_anchor=(352.0, 64.0),
        segments=(
            ("rear_hair", front[0:2], "Rear Hair", (_hex_color(normal.hair),), "hair", _hex_color(normal.hair)),
            ("hat_dome", [front[2]], "Hat Dome", (_hex_color(normal.cap),), "cap", _hex_color(normal.cap)),
            ("under_hat_hair", [front[3]], "Under-Hat Hair", (_hex_color(normal.hair),), "hair", _hex_color(normal.hair)),
            ("hat_trim", front[4:7], "Hat Trim", (_hex_color(normal.accent),), "accent", _hex_color(normal.accent)),
            ("skin", [front[7]], "Face", (_hex_color(normal.skin),), "skin", _hex_color(normal.skin)),
            ("forehead_hair", [front[8]], "Forehead Hair", (_hex_color(normal.hair),), "hair", _hex_color(normal.hair)),
            ("eyes", front[9:11], "Eyes", (), None, None),
            ("blush", front[11:13], "Blush", (), None, None),
            ("nose_shadow", [front[13]], "Nose Shadow", ("#dfa47c",), "nose", "#dfa47c"),
            ("face_linework", front[14:16], "Face Linework", (), None, None),
            ("pupils", front[16:18], "Pupils", (), None, None),
        ),
    )

    components = {**{f"side_{k}": v for k, v in side_components.items()}, **{f"front_{k}": v for k, v in front_components.items()}}
    masters = {"side": side_master, "front": front_master}
    return components, masters


def _take_children(group: ET.Element, predicate) -> list[ET.Element]:
    out: list[ET.Element] = []
    for child in list(group):
        if predicate(child):
            group.remove(child)
            out.append(child)
    return out


def _head_accessory_components(
    primitive_layer: ET.Element,
    arts: dict[tuple[str, str, str], ET.Element],
) -> dict[str, tuple[str, tuple[float, float]]]:
    slots = {
        "big_side_ribbon": (30.0, 280.0),
        "big_side_hat_star": (92.0, 280.0),
        "side_ear_star": (148.0, 280.0),
        "fire_side_ribbon": (204.0, 280.0),
        "fire_side_extras": (270.0, 280.0),
        "fire_side_hat_wing": (340.0, 280.0),
        "big_front_ribbons": (420.0, 280.0),
        "big_front_hat_star": (488.0, 280.0),
        "fire_front_ribbons": (30.0, 350.0),
        "fire_front_extras": (110.0, 350.0),
    }
    out: dict[str, tuple[str, tuple[float, float]]] = {}

    def add(name: str, elements: Sequence[ET.Element], label: str, anchor: tuple[float, float], recolor=()):
        mid, slot = _primitive_group(
            primitive_layer,
            elements=elements,
            master_id=f"maryo_primitive_{name}",
            label=label,
            source_anchor=anchor,
            slot_anchor=slots[name],
            recolor_hexes=recolor,
        )
        out[name] = (mid, slot)

    tall_side_art = arts[("tall", "side", "head")]
    tall_side_found = _find_semantic_child(tall_side_art, "_head_foundation")
    tall_ear = _find_semantic_child(tall_side_art, "_ear_star_accessory")
    fire_side_art = arts[("fire", "side", "head")]
    fire_side_found = _find_semantic_child(fire_side_art, "_head_foundation")
    fire_hat_wing = _find_semantic_child(fire_side_art, "_hat_wing_accessory")
    tall_front_art = arts[("tall", "front", "head")]
    tall_front_found = _find_semantic_child(tall_front_art, "_front_head_anatomy")
    fire_front_art = arts[("fire", "front", "head")]
    fire_front_found = _find_semantic_child(fire_front_art, "_front_head_anatomy")
    if None in (tall_side_found, tall_ear, fire_side_found, fire_hat_wing, tall_front_found, fire_front_found):
        raise ValueError("powered Mary-O head source is incomplete")

    pink = "#e778aa"
    gold = "#ffd054"
    fire_buttons = _hex_color(FIRE_FORM.palette.buttons)
    brooch_light = "#fff4cd"

    big_side_ribbon = _take_children(tall_side_found, lambda n: n.tag == _svg("polygon") and (n.get("fill") or "").lower() == pink)
    big_side_star = _take_children(tall_side_found, lambda n: n.tag == _svg("polygon") and (n.get("fill") or "").lower() == gold)
    add("big_side_ribbon", big_side_ribbon, "Primitive Big Side Ribbon", _head_scale_anchor("tall", "side"))
    add("big_side_hat_star", big_side_star, "Primitive Powered Side Hat Star", _head_scale_anchor("tall", "side"))
    add("side_ear_star", list(tall_ear), "Primitive Side Ear Star", _head_scale_anchor("tall", "side"), (_hex_color(TALL_FORM.palette.buttons),))

    fire_side_ribbon = _take_children(fire_side_found, lambda n: n.tag == _svg("polygon") and (n.get("fill") or "").lower() == pink)
    fire_side_extras = _take_children(
        fire_side_found,
        lambda n: n.tag == _svg("polygon") and (n.get("fill") or "").lower() in {fire_buttons.lower(), brooch_light},
    )
    # The fire hat badge intentionally reuses the powered star master; only
    # the fire-only temple/star embellishments live in this primitive.
    add("fire_side_ribbon", fire_side_ribbon, "Primitive Fire Side Ribbon", _head_scale_anchor("fire", "side"))
    add("fire_side_extras", fire_side_extras, "Primitive Fire Side Head Extras", _head_scale_anchor("fire", "side"), (fire_buttons,))
    add("fire_side_hat_wing", list(fire_hat_wing), "Primitive Fire Side Hat Wing", _head_scale_anchor("fire", "side"))

    big_front_ribbons = _take_children(tall_front_found, lambda n: n.tag == _svg("polygon") and (n.get("fill") or "").lower() == pink)
    big_front_star = _take_children(tall_front_found, lambda n: n.tag == _svg("polygon") and (n.get("fill") or "").lower() == gold)
    add("big_front_ribbons", big_front_ribbons, "Primitive Big Front Ribbons", _head_scale_anchor("tall", "front"))
    add("big_front_hat_star", big_front_star, "Primitive Powered Front Hat Star", _head_scale_anchor("tall", "front"))

    fire_front_ribbons = _take_children(fire_front_found, lambda n: n.tag == _svg("polygon") and (n.get("fill") or "").lower() == pink)
    fire_front_extras = _take_children(
        fire_front_found,
        lambda n: n.tag == _svg("polygon") and (n.get("fill") or "").lower() in {fire_buttons.lower(), "#ffc940"},
    )
    add("fire_front_ribbons", fire_front_ribbons, "Primitive Fire Front Ribbons", _head_scale_anchor("fire", "front"))
    add("fire_front_extras", fire_front_extras, "Primitive Fire Front Head Extras", _head_scale_anchor("fire", "front"), (fire_buttons,))
    return out


def _append_palette_primitive(
    assembly: ET.Element,
    component: tuple[str, tuple[float, float], str | None],
    *,
    target_anchor: tuple[float, float],
    palette,
    label: str,
) -> None:
    master_id, slot, role = component
    color = None
    if role == "hair":
        color = _hex_color(palette.hair)
    elif role == "skin":
        color = _hex_color(palette.skin)
    elif role == "cap":
        color = _hex_color(palette.cap)
    elif role == "accent":
        color = _hex_color(palette.accent)
    elif role == "nose":
        color = "#dfa47c" if palette is TALL_FORM.palette else "#e0a880"
    instance = _append_clone_instance(
        assembly,
        master_id=master_id,
        source_slot_anchor=slot,
        target_anchor=target_anchor,
        label=label,
    )
    if color is not None:
        instance.set("color", color)
        clone = next((node for node in instance.iter() if node.tag == _svg("use")), None)
        if clone is not None:
            clone.set("color", color)


def _build_base_head_assembly(
    assembly_layer: ET.Element,
    *,
    master_id: str,
    label: str,
    slot_anchor: tuple[float, float],
    projection: str,
    palette,
    components: dict[str, tuple[str, tuple[float, float], str | None]],
) -> tuple[str, tuple[float, float]]:
    group = ET.Element(_svg("g"))
    group.set("id", master_id)
    group.set(INK_LABEL, label)
    group.set("data-authoring-assembly", "true")
    order = (
        (
            "side_rear_hair", "side_skin", "side_nose_shadow", "side_foreground_hair",
            "side_ponytail_tie", "side_hat_dome", "side_hat_trim", "side_eye", "side_face_details",
        )
        if projection == "side"
        else (
            "front_rear_hair", "front_hat_dome", "front_under_hat_hair", "front_hat_trim",
            "front_skin", "front_forehead_hair", "front_eyes", "front_blush",
            "front_nose_shadow", "front_face_linework", "front_pupils",
        )
    )
    for name in order:
        _append_palette_primitive(
            group,
            components[name],
            target_anchor=slot_anchor,
            palette=palette,
            label=components[name][0].replace("maryo_primitive_", "").replace("_", " ").title(),
        )
    assembly_layer.append(group)
    return master_id, slot_anchor


def _build_form_head_assembly(
    assembly_layer: ET.Element,
    *,
    key: str,
    projection: str,
    slot_anchor: tuple[float, float],
    base: tuple[str, tuple[float, float]],
    accessories: dict[str, tuple[str, tuple[float, float]]],
) -> tuple[str, tuple[float, float]]:
    group = ET.Element(_svg("g"))
    master_id = f"maryo_assembly_{key}_{projection}_head"
    group.set("id", master_id)
    group.set(INK_LABEL, f"Assembly {_FORM_TITLES[key]} {projection.title()} Head")
    group.set("data-authoring-assembly", "true")
    _append_clone_instance(
        group,
        master_id=base[0],
        source_slot_anchor=base[1],
        target_anchor=slot_anchor,
        scale=_head_scale_ratio(key),
        label="Base Head",
    )
    if projection == "side":
        if key == "tall":
            for name, label in (
                ("big_side_ribbon", "Big Ribbon"),
                ("big_side_hat_star", "Hat Star"),
                ("side_ear_star", "Ear Star"),
            ):
                _append_clone_instance(
                    group,
                    master_id=accessories[name][0],
                    source_slot_anchor=accessories[name][1],
                    target_anchor=slot_anchor,
                    label=label,
                )
        elif key == "fire":
            for name, label in (
                ("fire_side_ribbon", "Fire Ribbon"),
                ("big_side_hat_star", "Hat Star"),
                ("side_ear_star", "Ear Star"),
                ("fire_side_extras", "Fire Head Extras"),
                ("fire_side_hat_wing", "Hat Wing"),
            ):
                inst = _append_clone_instance(
                    group,
                    master_id=accessories[name][0],
                    source_slot_anchor=accessories[name][1],
                    target_anchor=slot_anchor,
                    label=label,
                )
                if name == "side_ear_star":
                    inst.set("color", _hex_color(FIRE_FORM.palette.buttons))
    else:
        if key == "tall":
            for name, label in (
                ("big_front_ribbons", "Big Ribbons"),
                ("big_front_hat_star", "Hat Star"),
            ):
                _append_clone_instance(
                    group,
                    master_id=accessories[name][0],
                    source_slot_anchor=accessories[name][1],
                    target_anchor=slot_anchor,
                    label=label,
                )
        elif key == "fire":
            for name, label in (
                ("fire_front_ribbons", "Fire Ribbons"),
                ("big_front_hat_star", "Hat Star"),
                ("fire_front_extras", "Fire Head Extras"),
            ):
                _append_clone_instance(
                    group,
                    master_id=accessories[name][0],
                    source_slot_anchor=accessories[name][1],
                    target_anchor=slot_anchor,
                    label=label,
                )
    assembly_layer.append(group)
    return master_id, slot_anchor


def _component_slot(key: str, projection: str, component: str) -> tuple[float, float]:
    row_y = {"short": 255.0, "tall": 350.0, "fire": 455.0}[key]
    xmap = {
        ("side", "torso"): 58.0,
        ("side", "arm"): 145.0,
        ("side", "leg"): 205.0,
        ("side", "wings"): 270.0,
        ("front", "torso"): 350.0,
        ("front", "arm"): 445.0,
        ("front", "leg"): 505.0,
        ("front", "wings"): 565.0,
    }
    return (xmap[(projection, component)], row_y)


def _promote_reused_art_component(
    primitive_layer: ET.Element,
    arts: dict[tuple[str, str, str], ET.Element],
    *,
    key: str,
    projection: str,
    canonical_part: str,
    target_parts: Sequence[str],
    component_name: str,
    label: str,
    slot_anchor: tuple[float, float],
) -> None:
    source_art = arts[(key, projection, canonical_part)]
    source_anchor = _part_anchor(key, projection, canonical_part)
    master_id = f"maryo_component_{key}_{projection}_{component_name}"
    _create_master_group(
        primitive_layer,
        source_art,
        master_id=master_id,
        label=label,
        source_anchor=source_anchor,
        slot_anchor=slot_anchor,
    )
    for part_name in target_parts:
        target_art = arts[(key, projection, part_name)]
        _install_clone_art(
            target_art,
            master_id=master_id,
            source_slot_anchor=slot_anchor,
            target_anchor=_part_anchor(key, projection, part_name),
        )


def _promote_single_art_component(
    primitive_layer: ET.Element,
    arts: dict[tuple[str, str, str], ET.Element],
    *,
    key: str,
    projection: str,
    part_name: str,
    component_name: str,
    label: str,
    slot_anchor: tuple[float, float],
) -> ET.Element:
    art = arts[(key, projection, part_name)]
    master_id = f"maryo_component_{key}_{projection}_{component_name}"
    master = _create_master_group(
        primitive_layer,
        art,
        master_id=master_id,
        label=label,
        source_anchor=_part_anchor(key, projection, part_name),
        slot_anchor=slot_anchor,
    )
    _install_clone_art(
        art,
        master_id=master_id,
        source_slot_anchor=slot_anchor,
        target_anchor=_part_anchor(key, projection, part_name),
    )
    return master


def _promote_front_torso_component(
    primitive_layer: ET.Element,
    arts: dict[tuple[str, str, str], ET.Element],
    *,
    key: str,
    slot_anchor: tuple[float, float],
) -> None:
    torso_art = arts[(key, "front", "torso")]
    fg_art = arts[(key, "front", "foreground_garment")]
    source_anchor = _part_anchor(key, "front", "torso")
    outfit = next((child for child in torso_art if (child.get("id") or "").endswith("_front_torso_outfit")), None)
    if outfit is None:
        raise ValueError(f"Mary-O {key} front torso has no garment geometry group")

    # Keep the torso coherent for authoring, but make the death foreground
    # repaint reference the exact same garment paths rather than storing a
    # second editable copy. The procedural body draws its shirt/base first and
    # the repaintable garment after it.
    base_count = 1 if key == "short" else 2
    children = list(outfit)
    if len(children) <= base_count:
        raise ValueError(f"Mary-O {key} front torso is too small to split")
    for child in children:
        outfit.remove(child)

    master_id = f"maryo_component_{key}_front_torso"
    master = ET.Element(_svg("g"))
    master.set("id", master_id)
    master.set(INK_LABEL, f"Editable {_FORM_TITLES[key]} Front Torso")
    master.set("data-authoring-master", "true")

    translate = _translate_expr(slot_anchor[0] - source_anchor[0], slot_anchor[1] - source_anchor[1])
    base_group = ET.SubElement(master, _svg("g"))
    base_group.set("id", f"{master_id}_body_base")
    base_group.set(INK_LABEL, "Body Base")
    base_group.set("transform", translate)
    garment_group = ET.SubElement(master, _svg("g"))
    garment_group.set("id", f"{master_id}_foreground_garment")
    garment_group.set(INK_LABEL, "Foreground Garment")
    garment_group.set("transform", translate)
    for child in children[:base_count]:
        base_group.append(child)
    for child in children[base_count:]:
        garment_group.append(child)
    primitive_layer.append(master)

    _install_clone_art(
        torso_art,
        master_id=master_id,
        source_slot_anchor=slot_anchor,
        target_anchor=source_anchor,
    )
    # The nested garment group carries its own display translation because it is
    # directly referenced outside the parent authoring component. Its geometry
    # therefore has the same slot anchor as the complete torso.
    _install_clone_art(
        fg_art,
        master_id=f"{master_id}_foreground_garment",
        source_slot_anchor=slot_anchor,
        target_anchor=_part_anchor(key, "front", "foreground_garment"),
    )


def _dedupe_side_fire_wings(master: ET.Element) -> None:
    primary = next((node for node in master.iter() if (node.get("id") or "").endswith("_primary_back_wing")), None)
    secondary = next((node for node in master.iter() if (node.get("id") or "").endswith("_secondary_back_wing")), None)
    if primary is None or secondary is None:
        return
    parent = next((node for node in master.iter() if secondary in list(node)), None)
    if parent is None:
        return
    index = list(parent).index(secondary)
    parent.remove(secondary)
    use = ET.Element(_svg("use"))
    use.set("id", f"{master.get('id')}_secondary_wing_clone")
    use.set(INK_LABEL, "Secondary Wing Clone")
    _set_use_ref(use, primary.get("id") or "")
    # The procedural secondary differs from the primary by less than a pixel
    # after this transform; using a clone removes the duplicate source geometry.
    use.set("transform", "matrix(0.98915 -0.01526 -0.00318 0.99629 3.5078 5.7783)")
    parent.insert(index, use)


def _dedupe_front_wings(master: ET.Element, *, fire: bool) -> None:
    group = next((node for node in master.iter() if (node.get("id") or "").endswith("_front_back_wings")), None)
    if group is None:
        return
    children = list(group)
    split = 6 if fire else 3
    if len(children) != split * 2:
        return
    left = ET.Element(_svg("g"))
    left.set("id", f"{master.get('id')}_character_right_wing")
    left.set(INK_LABEL, "Character Right Wing")
    for child in children[:split]:
        group.remove(child)
        left.append(child)
    for child in children[split:]:
        group.remove(child)
    group.append(left)
    use = ET.SubElement(group, _svg("use"))
    use.set("id", f"{master.get('id')}_character_left_wing_clone")
    use.set(INK_LABEL, "Character Left Wing Clone")
    _set_use_ref(use, left.get("id") or "")
    if fire:
        use.set("transform", "matrix(-0.96527 0 -0.01154 1 79.8142 0)")
    else:
        use.set("transform", "matrix(-1 0 0 1 80 0)")


def _promote_shared_death_expression(
    primitive_layer: ET.Element,
    arts: dict[tuple[str, str, str], ET.Element],
) -> None:
    key = "short"
    source_art = arts[(key, "front", "death_expression")]
    slot = (555.0, 245.0)
    master_id = "maryo_component_shared_front_death_expression"
    _create_master_group(
        primitive_layer,
        source_art,
        master_id=master_id,
        label="Editable Shared Front Death Expression",
        source_anchor=_part_anchor(key, "front", "death_expression"),
        slot_anchor=slot,
    )
    for target_key in ("short", "tall", "fire"):
        target_art = arts[(target_key, "front", "death_expression")]
        _install_clone_art(
            target_art,
            master_id=master_id,
            source_slot_anchor=slot,
            target_anchor=_part_anchor(target_key, "front", "death_expression"),
        )


def _promote_authoring_masters(root: ET.Element) -> ET.Element:
    view_layers = {
        (layer.get("data-rig-form"), layer.get("data-rig-projection")): layer
        for layer in root
        if layer.get("data-rig-form") and layer.get("data-rig-projection")
    }
    primitive_layer = ET.Element(_svg("g"))
    primitive_layer.set("id", "maryo_primitive_components")
    primitive_layer.set(INK_GROUPMODE, "layer")
    primitive_layer.set(INK_LABEL, "Mary-O - Authoring Components")
    primitive_layer.set("data-rig-library", "true")
    assembly_layer = ET.Element(_svg("g"))
    assembly_layer.set("id", "maryo_component_assemblies")
    assembly_layer.set(INK_GROUPMODE, "layer")
    assembly_layer.set(INK_LABEL, "Mary-O - Component Assemblies")
    assembly_layer.set("data-rig-library", "true")
    root.insert(0, assembly_layer)
    root.insert(0, primitive_layer)

    arts: dict[tuple[str, str, str], ET.Element] = {}
    for (key, projection), view in view_layers.items():
        for wrapper in list(view):
            part_name = wrapper.get("data-rig-part") or ""
            art = next((child for child in list(wrapper) if child.get("data-rig-art") == "true"), None)
            if part_name and art is not None:
                arts[(key, projection, part_name)] = art

    head_components, head_masters = _head_authoring_components(primitive_layer)
    head_accessories = _head_accessory_components(primitive_layer, arts)
    fire_side_base = _build_base_head_assembly(
        assembly_layer,
        master_id="maryo_assembly_fire_side_head_base",
        label="Assembly Fire Side Head Base",
        slot_anchor=(260.0, 455.0),
        projection="side",
        palette=FIRE_FORM.palette,
        components=head_components,
    )
    fire_front_base = _build_base_head_assembly(
        assembly_layer,
        master_id="maryo_assembly_fire_front_head_base",
        label="Assembly Fire Front Head Base",
        slot_anchor=(540.0, 455.0),
        projection="front",
        palette=FIRE_FORM.palette,
        components=head_components,
    )

    head_assemblies: dict[tuple[str, str], tuple[str, tuple[float, float]]] = {}
    for key, slot in (("short", (70.0, 585.0)), ("tall", (190.0, 585.0)), ("fire", (310.0, 585.0))):
        head_assemblies[(key, "side")] = _build_form_head_assembly(
            assembly_layer,
            key=key,
            projection="side",
            slot_anchor=slot,
            base=fire_side_base if key == "fire" else head_masters["side"],
            accessories=head_accessories,
        )
    for key, slot in (("short", (370.0, 665.0)), ("tall", (465.0, 665.0)), ("fire", (555.0, 665.0))):
        head_assemblies[(key, "front")] = _build_form_head_assembly(
            assembly_layer,
            key=key,
            projection="front",
            slot_anchor=slot,
            base=fire_front_base if key == "fire" else head_masters["front"],
            accessories=head_accessories,
        )

    # Final six views depend only on the head assemblies, never on duplicated
    # form-specific head geometry.
    for key in ("short", "tall", "fire"):
        for projection in ("side", "front"):
            art = arts[(key, projection, "head")]
            master_id, slot = head_assemblies[(key, projection)]
            _install_clone_art(
                art,
                master_id=master_id,
                source_slot_anchor=slot,
                target_anchor=_head_scale_anchor(key, projection),
            )

    # Keep the clone/source-authority system scoped to the head. Body parts stay
    # local to the final six views instead of appearing as extra authoring
    # masters in the sheet.
    _promote_shared_death_expression(primitive_layer, arts)

    return root


def _rgba(color: Tuple[int, int, int, int] | None) -> tuple[str, float]:
    if color is None:
        return "none", 1.0
    r, g, b, a = color
    return f"#{r:02x}{g:02x}{b:02x}", a / 255.0


def _fmt(value: float) -> str:
    rounded = round(float(value), 4)
    if rounded == int(rounded):
        return str(int(rounded))
    return f"{rounded:.4f}".rstrip("0").rstrip(".")


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _title(value: str) -> str:
    return value.replace("_", " ").title()


def _points_attr(value: str) -> list[tuple[float, float]]:
    numbers = [float(token) for token in re.findall(r"-?\d+(?:\.\d+)?", value or "")]
    if len(numbers) % 2:
        raise ValueError(f"malformed SVG point list: {value!r}")
    return list(zip(numbers[0::2], numbers[1::2]))


def _closed_poly_path(points: Sequence[tuple[float, float]]) -> str:
    if not points:
        return ""
    head, *tail = points
    commands = [f"M {_fmt(head[0])} {_fmt(head[1])}"]
    commands.extend(f"L {_fmt(x)} {_fmt(y)}" for x, y in tail)
    commands.append("Z")
    return " ".join(commands)


def _rect_path(node: ET.Element) -> str:
    x = float(node.get("x", "0"))
    y = float(node.get("y", "0"))
    w = float(node.get("width", "0"))
    h = float(node.get("height", "0"))
    rx = float(node.get("rx", node.get("ry", "0") or "0"))
    ry = float(node.get("ry", node.get("rx", "0") or "0"))
    rx = max(0.0, min(abs(rx), abs(w) / 2.0))
    ry = max(0.0, min(abs(ry), abs(h) / 2.0))
    if rx <= 1e-9 or ry <= 1e-9:
        return _closed_poly_path(((x, y), (x + w, y), (x + w, y + h), (x, y + h)))
    return " ".join((
        f"M {_fmt(x + rx)} {_fmt(y)}",
        f"L {_fmt(x + w - rx)} {_fmt(y)}",
        f"A {_fmt(rx)} {_fmt(ry)} 0 0 1 {_fmt(x + w)} {_fmt(y + ry)}",
        f"L {_fmt(x + w)} {_fmt(y + h - ry)}",
        f"A {_fmt(rx)} {_fmt(ry)} 0 0 1 {_fmt(x + w - rx)} {_fmt(y + h)}",
        f"L {_fmt(x + rx)} {_fmt(y + h)}",
        f"A {_fmt(rx)} {_fmt(ry)} 0 0 1 {_fmt(x)} {_fmt(y + h - ry)}",
        f"L {_fmt(x)} {_fmt(y + ry)}",
        f"A {_fmt(rx)} {_fmt(ry)} 0 0 1 {_fmt(x + rx)} {_fmt(y)} Z",
    ))


def _ellipse_path(cx: float, cy: float, rx: float, ry: float) -> str:
    return " ".join((
        f"M {_fmt(cx - rx)} {_fmt(cy)}",
        f"A {_fmt(rx)} {_fmt(ry)} 0 1 0 {_fmt(cx + rx)} {_fmt(cy)}",
        f"A {_fmt(rx)} {_fmt(ry)} 0 1 0 {_fmt(cx - rx)} {_fmt(cy)} Z",
    ))


def _convert_visible_leaf_to_path(node: ET.Element) -> None:
    local = _local_name(node.tag)
    d: str | None = None
    geometry_attrs: tuple[str, ...] = ()
    if local == "rect":
        d = _rect_path(node)
        geometry_attrs = ("x", "y", "width", "height", "rx", "ry")
    elif local == "polygon":
        d = _closed_poly_path(_points_attr(node.get("points", "")))
        geometry_attrs = ("points",)
    elif local == "polyline":
        points = _points_attr(node.get("points", ""))
        if points:
            head, *tail = points
            d = " ".join(
                [f"M {_fmt(head[0])} {_fmt(head[1])}"]
                + [f"L {_fmt(x)} {_fmt(y)}" for x, y in tail]
            )
        geometry_attrs = ("points",)
    elif local == "line":
        d = (
            f"M {_fmt(float(node.get('x1', '0')))} {_fmt(float(node.get('y1', '0')))} "
            f"L {_fmt(float(node.get('x2', '0')))} {_fmt(float(node.get('y2', '0')))}"
        )
        geometry_attrs = ("x1", "y1", "x2", "y2")
    elif local == "ellipse":
        d = _ellipse_path(
            float(node.get("cx", "0")),
            float(node.get("cy", "0")),
            float(node.get("rx", "0")),
            float(node.get("ry", "0")),
        )
        geometry_attrs = ("cx", "cy", "rx", "ry")
    elif local == "circle":
        radius = float(node.get("r", "0"))
        d = _ellipse_path(
            float(node.get("cx", "0")),
            float(node.get("cy", "0")),
            radius,
            radius,
        )
        geometry_attrs = ("cx", "cy", "r")
    if d is None:
        return
    node.tag = _svg("path")
    for attr in geometry_attrs:
        node.attrib.pop(attr, None)
    node.set("d", d)
    if node.get("stroke") not in (None, "none"):
        if node.get("stroke-linecap") is None:
            node.set("stroke-linecap", "square")
        if node.get("stroke-linejoin") is None:
            node.set("stroke-linejoin", "miter")
        if node.get("stroke-miterlimit") is None:
            node.set("stroke-miterlimit", "4")


def _normalize_primitive_geometry_to_paths(root: ET.Element) -> None:
    """Use paths as the hand-authoring vocabulary for visible source geometry.

    Procedural capture is free to use rectangles, polygons, ellipses, and lines,
    but the checked-in SVG is an Inkscape authoring artifact. Converting only the
    editable primitive layer at the export boundary gives artists one predictable
    node-editing representation while leaving hidden rig-guide circles untouched.
    """
    primitive_layer = next(
        (node for node in root if node.get("id") == "maryo_primitive_components"),
        None,
    )
    if primitive_layer is None:
        raise ValueError("Mary-O SVG is missing the primitive authoring layer")
    for node in list(primitive_layer.iter()):
        if _local_name(node.tag) in {"rect", "polygon", "polyline", "line", "ellipse", "circle"}:
            _convert_visible_leaf_to_path(node)


def _mark_authoring_tiers(root: ET.Element) -> None:
    """Make the one-way authoring dependency graph explicit in Inkscape.

    Primitive components are the only geometry authority. Derived assemblies and
    final six model views are locked by default so node edits cannot accidentally
    happen on a downstream representation that cannot propagate back upstream.
    They can still be unlocked intentionally when an author needs to inspect or
    tune an assembly transform.
    """
    primitive_layer = next(
        (node for node in root if node.get("id") == "maryo_primitive_components"),
        None,
    )
    assembly_layer = next(
        (node for node in root if node.get("id") == "maryo_component_assemblies"),
        None,
    )
    if primitive_layer is None or assembly_layer is None:
        raise ValueError("Mary-O SVG authoring tiers are incomplete")

    primitive_layer.set("data-authoring-role", "editable-source")
    primitive_layer.attrib.pop(SODIPODI_INSENSITIVE, None)
    for node in primitive_layer.iter():
        if node.get("data-authoring-master") == "true":
            node.set("data-authoring-editable", "true")

    assembly_layer.set("data-authoring-role", "derived")
    assembly_layer.set("data-authoring-editable", "false")
    assembly_layer.set(SODIPODI_INSENSITIVE, "true")
    for node in assembly_layer.iter():
        if node.get("data-authoring-assembly") == "true":
            node.set("data-authoring-editable", "false")

    for layer in root:
        if not (layer.get("data-rig-form") and layer.get("data-rig-projection")):
            continue
        layer.set("data-authoring-role", "final-view")
        layer.set("data-authoring-editable", "false")
        layer.set(SODIPODI_INSENSITIVE, "true")


class _SvgPixelCanvas:
    """PixelCanvas-compatible vector recorder with authoring-quality labels."""

    def __init__(self, form_key: str, projection: str) -> None:
        self.form_key = form_key
        self.projection = projection
        self._root_elements: List[str] = []
        self._active: List[List[str]] = [self._root_elements]
        self._part_prefix: str | None = None
        self._semantic_stack: List[str] = []
        self._leaf_counts: Dict[tuple[str, str, str], int] = {}
        # Pivots are collected here and emitted as ONE flat 'Rig Joints' layer by
        # `body()`, never inside the part they belong to -- see that method.
        self._pivots: List[str] = []

    def _p(self, x: float, y: float) -> tuple[int, int]:
        return (
            int(round(x * SCALE)) + _CANVAS_X,
            int(round(y * SCALE)) + _CANVAS_Y,
        )

    def _box(self, x1: float, y1: float, x2: float, y2: float) -> tuple[int, int, int, int]:
        a = self._p(x1, y1)
        b = self._p(x2, y2)
        return a[0], a[1], b[0], b[1]

    def _emit(self, text: str) -> None:
        self._active[-1].append(text)

    @contextmanager
    def semantic_group(self, name: str, *, label: str | None = None) -> Iterator[None]:
        """Give a logical subassembly its own Inkscape group and naming scope."""
        if self._part_prefix is None:
            yield
            return
        slug = _slug(name)
        body: List[str] = []
        self._active.append(body)
        self._semantic_stack.append(slug)
        try:
            yield
        finally:
            self._semantic_stack.pop()
            self._active.pop()
        if body:
            group_id = f'{self._part_prefix}_{slug}'
            self._emit(
                f'<g id="{group_id}" inkscape:label="{label or _title(name)}">'
                f'{"".join(body)}</g>'
            )

    def _leaf_attrs(self, kind: str) -> str:
        if self._part_prefix is None:
            return ""
        scope = "_".join(self._semantic_stack) or "art"
        key = (self._part_prefix, scope, kind)
        count = self._leaf_counts.get(key, 0) + 1
        self._leaf_counts[key] = count
        element_id = f"{self._part_prefix}_{scope}_{kind}_{count:02d}"
        label = f"{_title(scope)} {_title(kind)} {count}"
        return f'id="{element_id}" inkscape:label="{label}" '

    @contextmanager
    def rig_part(
        self,
        name: str,
        bone: str,
        pivot: tuple[float, float],
        z: float,
        *,
        label: str | None = None,
    ) -> Iterator[None]:
        body: List[str] = []
        previous_prefix = self._part_prefix
        previous_stack = self._semantic_stack
        prefix = f"maryo_{self.form_key}_{self.projection}_{name}"
        self._part_prefix = prefix
        self._semantic_stack = []
        self._active.append(body)
        try:
            yield
        finally:
            self._active.pop()
            self._part_prefix = previous_prefix
            self._semantic_stack = previous_stack
        if not body:
            return
        px, py = self._p(*pivot)
        #  THE PIVOT DOES NOT GO INSIDE THE PART. It is stashed for the flat
        # 'Rig Joints' layer `body()` writes, which is how every other rig SVG in
        # this package authors pivots. Nesting one inside its part made it a
        # drawable WITHIN that part (so it leaked into the part's raster, which is
        # why the cross had to be a separate hidden thing at all) and put its
        # cx/cy in the part's local space -- displaced up to 880 units from what
        # Inkscape shows, so nobody could place one by eye. The pivot-cross path
        # is gone with it: the dot is the pivot.
        self._pivots.append(
            f'<circle id="{prefix}_pivot" inkscape:label="{label or _title(name)} Pivot" '
            f'data-rig-joint="{bone}" cx="{px}" cy="{py}" r="1.35" '
            f'fill="#ff3bd4" fill-opacity="0.30" stroke="#43133d" stroke-width="0.7"/>'
        )
        wrapper = (
            f'<g id="{prefix}" inkscape:label="{label or _title(name)}" '
            f'data-rig-part="{name}" data-rig-bone="{bone}" data-rig-z="{_fmt(z)}">'
            f'<g id="{prefix}_art" inkscape:label="Artwork" '
            f'data-rig-art="true">{"".join(body)}</g>'
            f'</g>'
        )
        self._emit(wrapper)

    def rect(self, x1, y1, x2, y2, *, fill, outline=None, width=1.0) -> None:
        ax, ay, bx, by = self._box(x1, y1, x2, y2)
        fc, fo = _rgba(fill)
        # Pillow's rectangle accepts a zero-width pixel interval and paints one
        # pixel. SVG width=0 paints nothing. Preserve the procedural semantics
        # without expanding ordinary non-degenerate rectangles.
        w = max(1, abs(bx - ax))
        h = max(1, abs(by - ay))
        attrs = [
            self._leaf_attrs("rect").strip(),
            f'x="{min(ax,bx)}"', f'y="{min(ay,by)}"',
            f'width="{w}"', f'height="{h}"', f'fill="{fc}"',
        ]
        if fo != 1.0:
            attrs.append(f'fill-opacity="{_fmt(fo)}"')
        if outline is not None:
            sc, so = _rgba(outline)
            attrs.extend((
                f'stroke="{sc}"',
                f'stroke-width="{max(1, int(round(width*SCALE)))}"',
                'stroke-linejoin="miter"',
                'stroke-miterlimit="4"',
            ))
            if so != 1.0:
                attrs.append(f'stroke-opacity="{_fmt(so)}"')
        self._emit(f'<rect {" ".join(a for a in attrs if a)}/>')

    def ellipse(self, x1, y1, x2, y2, *, fill, outline=None, width=1.0) -> None:
        ax, ay, bx, by = self._box(x1, y1, x2, y2)
        cx, cy = (ax + bx) / 2.0, (ay + by) / 2.0
        rx, ry = max(0.5, abs(bx - ax) / 2.0), max(0.5, abs(by - ay) / 2.0)
        fc, fo = _rgba(fill)
        attrs = [
            self._leaf_attrs("ellipse").strip(),
            f'cx="{_fmt(cx)}"', f'cy="{_fmt(cy)}"',
            f'rx="{_fmt(rx)}"', f'ry="{_fmt(ry)}"', f'fill="{fc}"',
        ]
        if fo != 1.0:
            attrs.append(f'fill-opacity="{_fmt(fo)}"')
        if outline is not None:
            sc, so = _rgba(outline)
            attrs.extend((f'stroke="{sc}"', f'stroke-width="{max(1, int(round(width*SCALE)))}"'))
            if so != 1.0:
                attrs.append(f'stroke-opacity="{_fmt(so)}"')
        self._emit(f'<ellipse {" ".join(a for a in attrs if a)}/>')

    def polygon(self, pts: Iterable[tuple[float, float]], *, fill, outline=None, width=1.0) -> None:
        points = [self._p(x, y) for x, y in pts]
        fc, fo = _rgba(fill)
        attrs = [
            self._leaf_attrs("polygon").strip(),
            f'points="{" ".join(f"{x},{y}" for x,y in points)}"',
            f'fill="{fc}"',
        ]
        if fo != 1.0:
            attrs.append(f'fill-opacity="{_fmt(fo)}"')
        if outline is not None:
            sc, so = _rgba(outline)
            attrs.extend((
                f'stroke="{sc}"',
                f'stroke-width="{max(1, int(round(width*SCALE)))}"',
                'stroke-linejoin="miter"',
                'stroke-miterlimit="4"',
            ))
            if so != 1.0:
                attrs.append(f'stroke-opacity="{_fmt(so)}"')
        self._emit(f'<polygon {" ".join(a for a in attrs if a)}/>')

    def line(self, pts: Iterable[tuple[float, float]], *, fill, width=1.0) -> None:
        points = [self._p(x, y) for x, y in pts]
        sc, so = _rgba(fill)
        if not points:
            return
        d = "M " + " L ".join(f"{x} {y}" for x, y in points)
        attrs = [
            self._leaf_attrs("line").strip(),
            f'd="{d}"', 'fill="none"', f'stroke="{sc}"',
            f'stroke-width="{max(1, int(round(width*SCALE)))}"',
            'stroke-linecap="square"', 'stroke-linejoin="miter"',
            'stroke-miterlimit="4"',
        ]
        if so != 1.0:
            attrs.append(f'stroke-opacity="{_fmt(so)}"')
        # Use <path>, not <polyline>: svg_parts deliberately knows how to hide
        # path drawables when isolating one rig subset.
        self._emit(f'<path {" ".join(a for a in attrs if a)}/>')

    def body(self) -> str:
        """The view's markup, with its pivots as one flat trailing layer.

        Hidden, as the per-part guides were, so a pivot never renders; a LAYER so
        Inkscape can toggle it while an author places the dots.
        """
        out = "".join(self._root_elements)
        if self._pivots:
            out += (
                f'<g id="maryo_{self.form_key}_{self.projection}_rig_joints" '
                f'inkscape:label="Rig Joints" inkscape:groupmode="layer" '
                f'style="display:none">{"".join(self._pivots)}</g>'
            )
        return out


@dataclass(frozen=True)
class _Layout:
    body_x: float
    body_top: float
    torso_bottom: float
    body_w: float
    head_x: float
    head_top: float
    lookback: bool
    back_shoulder: tuple[float, float]
    near_shoulder: tuple[float, float]
    back_hip: tuple[float, float]
    near_hip: tuple[float, float]
    back_arm_origin: tuple[float, float]
    near_arm_origin: tuple[float, float]
    back_leg_origin: tuple[float, float]
    near_leg_origin: tuple[float, float]


def _layout(form: FormSpec, pose: Pose) -> _Layout:
    """Resolve the same attachment coordinates used by `_draw_side_pose`."""
    foot_y = 30.2 + pose.bob + form.foot_dy
    torso_bottom = foot_y - form.leg_height + form.body_dy + 0.4 * pose.crouch
    body_top = torso_bottom - form.body_height + 0.6 * pose.crouch
    body_x = 7.0 + pose.body_lean + form.body_dx
    if pose.mode == "swim":
        body_x = 6.3 + pose.body_lean + form.body_dx
    elif pose.mode == "crouch":
        body_x = 6.8 + pose.body_lean + form.body_dx
    elif pose.mode == "climb":
        body_x = 6.4 + pose.body_lean + form.body_dx
    compact = pose.mode == "crouch"
    body_w = (
        form.body_width - 0.10 * min(pose.crouch, 1.6)
        if compact
        else form.body_width + 0.4 * min(pose.crouch, 1.4)
    )
    solved = rig_for(
        form,
        foot_y=foot_y,
        hip_y=torso_bottom,
        body_top=body_top,
        body_left=body_x,
        body_right=body_x + body_w,
    )
    back_shoulder = (
        solved.shoulder(-1)[0] + pose.arm_back_dx,
        solved.shoulder(-1)[1] + pose.arm_back_dy,
    )
    near_shoulder = (
        solved.shoulder(1)[0] + pose.arm_front_dx,
        solved.shoulder(1)[1] + pose.arm_front_dy,
    )
    back_hip = (
        solved.hip(-1)[0] + form.leg_dx + pose.leg_back_dx,
        solved.hip(-1)[1] + form.leg_dy + pose.leg_back_dy,
    )
    near_hip = (
        solved.hip(1)[0] + form.leg_dx + pose.leg_front_dx,
        solved.hip(1)[1] + form.leg_dy + pose.leg_front_dy,
    )
    head_x, resolved_head_top, lookback = _side_pose_head_origin(form, pose)
    return _Layout(
        body_x=body_x,
        body_top=body_top,
        torso_bottom=torso_bottom,
        body_w=body_w,
        head_x=head_x,
        head_top=resolved_head_top,
        lookback=lookback,
        back_shoulder=back_shoulder,
        near_shoulder=near_shoulder,
        back_hip=back_hip,
        near_hip=near_hip,
        back_arm_origin=(
            solved.arm_hang()[0] + form.back_arm_dx + pose.arm_back_dx,
            solved.arm_hang()[1] + form.back_arm_dy + pose.arm_back_dy,
        ),
        near_arm_origin=(
            body_x
            + (8.3 - _ARM_REFERENCE_WIDTH + form.body_width)
            + form.front_arm_dx
            + pose.arm_front_dx,
            body_top + 0.8 + form.front_arm_dy + pose.arm_front_dy,
        ),
        back_leg_origin=(
            solved.leg_x(-1) + form.leg_dx + pose.leg_back_dx,
            solved.hip_y + form.leg_dy + pose.leg_back_dy,
        ),
        near_leg_origin=(
            solved.leg_x(1) + form.leg_dx + pose.leg_front_dx,
            torso_bottom + form.leg_dy + pose.leg_front_dy,
        ),
    )


@dataclass(frozen=True)
class _FrontLayout:
    body_x: float
    body_top: float
    torso_bottom: float
    head_x: float
    head_top: float
    character_right_shoulder: tuple[float, float]
    character_left_shoulder: tuple[float, float]
    character_right_hip: tuple[float, float]
    character_left_hip: tuple[float, float]
    wing_anchor: tuple[float, float]


def _front_layout(form: FormSpec, pose: Pose) -> _FrontLayout:
    """Resolve Mary-O's front/death attachment coordinates in character terms."""
    body_x = 6.0 + form.body_dx
    foot_y = 29.2 + pose.bob + form.foot_dy
    torso_bottom = foot_y - form.leg_height + form.body_dy
    body_top = torso_bottom - form.body_height
    head_top = body_top - (form.head_offset - 0.2)
    solved = rig_for(
        form,
        foot_y=foot_y,
        hip_y=torso_bottom,
        body_top=body_top,
        body_left=body_x + 1.2,
        body_right=body_x + 1.2 + form.body_width,
    )
    shoulder_y = body_top + form.body_height * DEAD_SHOULDER_Y
    hip_y = solved.hip_y + form.body_height * DEAD_HIP_Y
    # Facing the viewer, character-right is screen-left.
    character_right_shoulder = (solved.mid(DEAD_ARM_X[0]), shoulder_y)
    character_left_shoulder = (solved.mid(DEAD_ARM_X[1]), shoulder_y)
    character_right_hip = (solved.mid(DEAD_HIP_X[0]), hip_y)
    character_left_hip = (solved.mid(DEAD_HIP_X[1]), hip_y)
    return _FrontLayout(
        body_x=body_x,
        body_top=body_top,
        torso_bottom=torso_bottom,
        head_x=body_x + 0.58 - form.body_dx,
        head_top=head_top,
        character_right_shoulder=character_right_shoulder,
        character_left_shoulder=character_left_shoulder,
        character_right_hip=character_right_hip,
        character_left_hip=character_left_hip,
        wing_anchor=(solved.mid(DEAD_WING_X), body_top + form.body_height * DEAD_WING_Y),
    )


def _draw_grouped_side_head(px: _SvgPixelCanvas, form: FormSpec, x: float, y: float) -> None:
    """Draw the accepted side head while exposing its authored subassemblies."""
    x, y = _snap_side_head_origin(x, y)
    head_px = px
    if getattr(form, "head_scale", 1.0) != 1.0:
        head_px = _ScaledAbout(px, x + 5.05, y + _HEAD_BOTTOM_LOCAL, form.head_scale)
    with head_px.semantic_group("head_foundation", label="Hair, Hat, Skin and Eye"):
        _draw_head_foundation_side(head_px, form, x, y, lookback=False)
    with head_px.semantic_group("face_details", label="Face Details"):
        _draw_side_face_features(head_px, form, x, y, lookback=False)
    if _magic_stage_value(form) <= 0:
        return
    with head_px.semantic_group("ear_star_accessory", label="Ear Star Accessory"):
        _draw_v2_ear_star(head_px, form, x, y, lookback=False)
    with head_px.semantic_group("hat_wing_accessory", label="Hat Wing Accessory"):
        _draw_v2_hat_wing(head_px, form, x, y, lookback=False)


def _paint_side_view(form: FormSpec) -> str:
    key = _FORM_KEYS[form.target_name]
    px = _SvgPixelCanvas(key, "side")
    pose = Pose()
    g = _layout(form, pose)

    with px.rig_part("far_arm", "far_arm", g.back_arm_origin, 10, label="Far Arm"):
        with px.semantic_group("sleeve_glove", label="Sleeve and Glove"):
            _draw_arm(px, g.back_arm_origin[0], g.back_arm_origin[1], front=False, form=form, length=4.0 * _arm_k(form))
    with px.rig_part("far_leg", "far_leg", g.back_leg_origin, 20, label="Far Leg"):
        with px.semantic_group("leg_shoe", label="Leg and Shoe"):
            _draw_leg(px, g.back_leg_origin[0], g.back_leg_origin[1], form=form, length=form.leg_height - form.body_dy)
    with px.rig_part("back_wings", "torso_back", (g.body_x, g.body_top), 30, label="Back Wings"):
        fire_accessory_t = _fire_accessory_t(form)
        side_wing_boost = 0.45 * fire_accessory_t
        with px.semantic_group("primary_back_wing", label="Primary Back Wing"):
            _draw_wing_side(px, g.body_x + 1.6, g.body_top + 3.4, form=form, spread=side_wing_boost)
        if _magic_stage_value(form) >= 1.7:
            with px.semantic_group("secondary_back_wing", label="Secondary Back Wing"):
                _draw_wing_side(px, g.body_x + 2.6, g.body_top + 5.1, form=form, spread=max(0.0, side_wing_boost - 0.15))
    with px.rig_part("near_leg", "near_leg", g.near_leg_origin, 40, label="Near Leg"):
        with px.semantic_group("leg_shoe", label="Leg and Shoe"):
            _draw_leg(px, g.near_leg_origin[0], g.near_leg_origin[1], form=form, length=form.leg_height - form.body_dy, front=True)
    with px.rig_part("torso", "torso", (g.body_x, g.body_top), 50, label="Torso and Outfit"):
        with px.semantic_group("torso_outfit", label="Garment Geometry"):
            _draw_body_side(px, form, g.body_x, g.body_top, 0.0, compact=False)
    with px.rig_part("head", "head", (g.head_x + 5.05, g.head_top + 7.5), 60, label="Head"):
        _draw_grouped_side_head(px, form, g.head_x, g.head_top)
    with px.rig_part("near_arm", "near_arm", g.near_arm_origin, 70, label="Near Arm"):
        with px.semantic_group("sleeve_glove", label="Sleeve and Glove"):
            _draw_arm(px, g.near_arm_origin[0], g.near_arm_origin[1], front=True, form=form, length=4.0 * _arm_k(form))
    return px.body()


def _paint_front_view(form: FormSpec) -> str:
    """Capture a complete front/death component library without rotated limbs."""
    key = _FORM_KEYS[form.target_name]
    px = _SvgPixelCanvas(key, "front")
    g = _front_layout(form, Pose(mode="dead"))
    leg_length = form.leg_height - form.body_dy - 0.35
    arm_length = 4.9
    # _draw_leg's authored centreline is x+1.1; _draw_arm's is approximately
    # x+0.8*k. Centre those one-piece bind limbs on the actual joint markers so
    # death rotation is a genuine bone transform rather than alternate artwork.
    leg_x_offset = 1.1
    arm_x_offset = 0.8 * _arm_k(form)

    with px.rig_part("character_right_leg", "character_right_leg", g.character_right_hip, 10, label="Character Right Leg"):
        with px.semantic_group("leg_shoe", label="Leg and Shoe"):
            _draw_leg(px, g.character_right_hip[0] - leg_x_offset, g.character_right_hip[1], form=form, length=leg_length, front=True)
    with px.rig_part("character_left_leg", "character_left_leg", g.character_left_hip, 20, label="Character Left Leg"):
        with px.semantic_group("leg_shoe", label="Leg and Shoe"):
            _draw_leg(px, g.character_left_hip[0] - leg_x_offset, g.character_left_hip[1], form=form, length=leg_length, front=True)
    with px.rig_part("back_wings", "torso_back", (g.body_x, g.body_top), 30, label="Back Wings"):
        with px.semantic_group("front_back_wings", label="Front-View Back Wings"):
            _draw_wings_front(px, g.wing_anchor[0], g.wing_anchor[1], form=form, spread=0.0)
    with px.rig_part("torso", "torso", (g.body_x, g.body_top), 40, label="Front Torso and Outfit"):
        with px.semantic_group("front_torso_outfit", label="Garment Geometry"):
            _draw_body_front(px, form, g.body_x, g.body_top)
    with px.rig_part("head", "head", (g.head_x + 5.5, g.head_top + 7.5), 50, label="Front Head"):
        with px.semantic_group("front_head_anatomy", label="Front Head, Face, Hat and Hair"):
            _draw_head_front(px, form, g.head_x, g.head_top)
    # The procedural death composer intentionally repaints the garment over the
    # front hair. Keep that as a named SVG component instead of silently baking
    # the ordering into the head or torso raster.
    with px.rig_part("foreground_garment", "torso", (g.body_x, g.body_top), 60, label="Foreground Garment"):
        with px.semantic_group("garment_repaint", label="Death Foreground Garment Repaint"):
            if form.magic_stage >= 1:
                _draw_powered_front_garment(px, form, g.body_x, g.body_top)
            else:
                _draw_short_pinafore_front(
                    px,
                    form,
                    g.body_x,
                    g.body_top,
                    form.body_width,
                    form.body_height,
                    g.body_top + form.body_height * 0.63,
                )
    with px.rig_part("death_expression", "head", (g.head_x + 5.5, g.head_top + 7.5), 65, label="Death Expression"):
        with px.semantic_group("x_eyes", label="Death X Eyes"):
            _draw_dead_eyes_front(px, g.head_x, g.head_top)
        with px.semantic_group("open_mouth", label="Death Open Mouth"):
            _draw_dead_mouth_front(px, g.head_x, g.head_top)
    with px.rig_part("character_right_arm", "character_right_arm", g.character_right_shoulder, 70, label="Character Right Arm"):
        with px.semantic_group("sleeve_glove", label="Sleeve and Glove"):
            _draw_arm(px, g.character_right_shoulder[0] - arm_x_offset, g.character_right_shoulder[1], front=True, form=form, length=arm_length)
    with px.rig_part("character_left_arm", "character_left_arm", g.character_left_shoulder, 80, label="Character Left Arm"):
        with px.semantic_group("sleeve_glove", label="Sleeve and Glove"):
            _draw_arm(px, g.character_left_shoulder[0] - arm_x_offset, g.character_left_shoulder[1], front=True, form=form, length=arm_length)
    return px.body()


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _hat_dome_points_from_bbox(x1: float, y_top: float, x2: float, y_base: float) -> list[tuple[float, float]]:
    w = x2 - x1
    h = y_base - y_top
    return [
        (x1, y_base),
        (x1 + 0.14 * w, y_top + 0.56 * h),
        (x1 + 0.30 * w, y_top + 0.22 * h),
        (x1 + 0.50 * w, y_top),
        (x1 + 0.70 * w, y_top + 0.22 * h),
        (x1 + 0.86 * w, y_top + 0.56 * h),
        (x2, y_base),
    ]


def _replace_hat_dome_with_angular_polygon(group: ET.Element) -> None:
    children = list(group)
    dome_fill = None
    dome_outline = None
    for idx, child in enumerate(children):
        if _local_name(child.tag) not in {"polygon", "path"}:
            continue
        if child.get("stroke") not in (None, "none"):
            continue
        points_attr = child.get("points")
        d_attr = child.get("d")
        if points_attr:
            pts = points_attr.split()
            if len(pts) < 6:
                continue
        elif d_attr:
            if "A" not in d_attr:
                continue
        else:
            continue
        dome_fill = (idx, child)
        break
    if dome_fill is None:
        return
    for idx in range(dome_fill[0] + 1, len(children)):
        child = children[idx]
        if _local_name(child.tag) == "path" and child.get("fill") == "none" and child.get("stroke"):
            dome_outline = (idx, child)
            break
    xs: list[float] = []
    ys: list[float] = []
    if dome_fill[1].get("points"):
        for token in (dome_fill[1].get("points") or "").split():
            pxs, pys = token.split(",")
            xs.append(float(pxs))
            ys.append(float(pys))
    else:
        nums = [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?", dome_fill[1].get("d") or "")]
        xs.extend(nums[0::2])
        ys.extend(nums[1::2])
    x1, x2 = min(xs), max(xs)
    y_top, y_base = min(ys), max(ys)
    pts = _hat_dome_points_from_bbox(x1, y_top, x2, y_base)
    attrs = {k: v for k, v in dome_fill[1].attrib.items() if k not in {"points", "d", "stroke", "stroke-width", "stroke-linejoin", "stroke-miterlimit", "stroke-linecap"}}
    attrs["points"] = " ".join(f"{_fmt(x)},{_fmt(y)}" for x, y in pts)
    attrs["fill"] = dome_fill[1].get("fill") or "#000000"
    attrs["stroke"] = dome_outline[1].get("stroke") if dome_outline is not None else "#1c1613"
    attrs["stroke-width"] = dome_outline[1].get("stroke-width") if dome_outline is not None and dome_outline[1].get("stroke-width") else "1"
    attrs["stroke-linejoin"] = "miter"
    attrs["stroke-miterlimit"] = "4"
    dome_poly = ET.Element(f"{{{SVG_NS}}}polygon", attrs)
    group.remove(dome_fill[1])
    group.insert(dome_fill[0], dome_poly)
    if dome_outline is not None:
        group.remove(dome_outline[1])


def _rect_metrics(node: ET.Element) -> tuple[float, float, float, float] | None:
    try:
        x = float(node.get("x", "0"))
        y = float(node.get("y", "0"))
        w = float(node.get("width", "0"))
        h = float(node.get("height", "0"))
    except ValueError:
        return None
    return x, y, w, h


def _merge_outer_inner_rect(outer: ET.Element, inner: ET.Element, *, stroke_width: float | None = None) -> None:
    dark = outer.get("fill") or "#1c1613"
    mo = _rect_metrics(outer)
    if mo is None:
        return
    ox, oy, ow, oh = mo
    sw = 1.0 if stroke_width is None else stroke_width
    # Preserve the original outer silhouette as closely as possible by using
    # the outer box as the source of truth and centering a one-pixel outline on
    # its edges. This reads much closer to the original stacked pixel rects than
    # simply stroking the inner fill rect.
    inner.set("x", _fmt(ox + sw / 2.0))
    inner.set("y", _fmt(oy + sw / 2.0))
    inner.set("width", _fmt(max(0.5, ow - sw)))
    inner.set("height", _fmt(max(0.5, oh - sw)))
    inner.set("stroke", dark)
    inner.set("stroke-width", _fmt(sw))
    inner.set("stroke-linejoin", "miter")
    inner.set("stroke-miterlimit", "4")


def _remove_matching_box_outline_paths(group: ET.Element, box: tuple[float, float, float, float]) -> None:
    x, y, w, h = box
    def near(a: float, b: float) -> bool:
        return abs(a - b) < 0.01
    for child in list(group):
        if _local_name(child.tag) != "path" or child.get("stroke") != "#1c1613":
            continue
        nums = [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?", child.get("d") or "")]
        if len(nums) != 4:
            continue
        x1, y1, x2, y2 = nums
        horizontal = near(y1, y2) and near(min(x1, x2), x) and near(max(x1, x2), x + w) and (near(y1, y) or near(y1, y + h))
        vertical = near(x1, x2) and near(min(y1, y2), y) and near(max(y1, y2), y + h) and (near(x1, x) or near(x1, x + w))
        if horizontal or vertical:
            group.remove(child)


def _simplify_arm_geometry(group: ET.Element) -> None:
    dark = "#1c1613"
    children = list(group)
    i = 0
    while i < len(children) - 1:
        a, b = children[i], children[i + 1]
        if _local_name(a.tag) == _local_name(b.tag) == "rect" and a.get("fill") == dark and b.get("fill") not in (None, dark):
            ma = _rect_metrics(a)
            mb = _rect_metrics(b)
            if ma and mb:
                ax, ay, aw, ah = ma
                bx, by, bw, bh = mb
                if bx >= ax and by >= ay and (bx + bw) <= (ax + aw) and (by + bh) <= (ay + ah):
                    _merge_outer_inner_rect(a, b)
                    group.remove(a)
                    _remove_matching_box_outline_paths(group, ma)
                    children = list(group)
                    continue
        i += 1


def _simplify_eye_geometry(group: ET.Element) -> None:
    dark = "#1c1613"
    children = list(group)
    i = 0
    while i < len(children) - 1:
        a, b = children[i], children[i + 1]
        if _local_name(a.tag) == _local_name(b.tag) == "rect" and a.get("fill") == dark and b.get("fill") == "#ffffff":
            ma = _rect_metrics(a)
            mb = _rect_metrics(b)
            if ma and mb:
                ax, ay, aw, ah = ma
                bx, by, bw, bh = mb
                if bx >= ax and by >= ay and (bx + bw) <= (ax + aw) and (by + bh) <= (ay + ah):
                    _merge_outer_inner_rect(a, b, stroke_width=1.0)
                    group.remove(a)
                    children = list(group)
                    continue
        i += 1


def _lift_pupils_to_front(group: ET.Element) -> None:
    dark = "#1c1613"
    pupils = []
    for child in list(group):
        if _local_name(child.tag) != "rect":
            continue
        if child.get("fill") != dark:
            continue
        try:
            width = float(child.get("width", "0"))
            height = float(child.get("height", "0"))
        except ValueError:
            continue
        if width <= 1.5 and height <= 2.5:
            pupils.append(child)
    for child in pupils:
        group.remove(child)
        group.append(child)




def _materialize_recolored_uses(root: ET.Element) -> None:
    """Inline recolored clone instances so local source colors do not override them.

    The head authoring masters keep normal-form colors on their semantic source
    groups for easy editing. When a derived assembly wants a different palette
    (notably the fire hat cap/trim), inherited color on a <use> is blocked by
    the source group's own color attribute. Materialize only those recolored
    instances into local copied geometry so the authoring sheet stays simple and
    the fire heads render with the intended palette.
    """
    id_map = {node.get("id"): node for node in root.iter() if node.get("id")}
    href_attr = f"{{{XLINK_NS}}}href"
    for node in list(root.iter()):
        desired = node.get("color")
        if not desired:
            continue
        use = next((child for child in node.iter(_svg("use"))), None)
        if use is None:
            continue
        href = use.get("href") or use.get(href_attr) or ""
        if not href.startswith("#"):
            continue
        source = id_map.get(href[1:])
        if source is None:
            continue
        source_color = source.get("color")
        if source_color is None or source_color.lower() == desired.lower():
            continue
        use_transform = use.get("transform")
        _clear_children(node)
        wrapper = ET.SubElement(node, _svg("g"))
        if use_transform:
            wrapper.set("transform", use_transform)
        clone_group = deepcopy(source)
        for sub in clone_group.iter():
            sub.attrib.pop("id", None)
        clone_group.set("color", desired)
        wrapper.append(clone_group)



def _dedupe_authoring_component_paths(root: ET.Element) -> None:
    components = next((node for node in root if node.get("id") == "maryo_primitive_components"), None)
    if components is None:
        return
    ignored = {"id", INK_LABEL}
    for component in components:
        parent_map = {child: node for node in component.iter() for child in node}
        signatures: set[tuple] = set()
        for node in list(component.iter()):
            if _local_name(node.tag) != "path":
                continue
            signature = tuple(sorted((key, value) for key, value in node.attrib.items() if key not in ignored))
            if signature in signatures:
                parent = parent_map.get(node)
                if parent is not None:
                    parent.remove(node)
                continue
            signatures.add(signature)


def _ensure_semantic_ids(root: ET.Element) -> None:
    counters: dict[str, int] = {}
    drawable = {"path", "polygon", "rect", "ellipse", "circle", "line", "polyline"}
    for node in root.iter():
        if _local_name(node.tag) not in drawable:
            continue
        if node.get("id"):
            continue
        label = (node.get(INK_LABEL) or _local_name(node.tag)).lower().replace(" ", "_")
        label = re.sub(r"[^a-z0-9_]+", "", label).strip("_") or "shape"
        counters[label] = counters.get(label, 0) + 1
        node.set("id", f"maryo_{label}_{counters[label]:02d}")

def _postprocess_svg_source(svg_text: str) -> str:
    root = ET.fromstring(svg_text)
    for node in root.iter():
        if _local_name(node.tag) == "g" and node.get("data-rig-art") == "true":
            node.set(INK_LABEL, "Artwork")
        gid = node.get("id") or ""
        if gid.endswith("_torso_outfit") or gid.endswith("_front_torso_outfit"):
            node.set(INK_LABEL, "Garment Geometry")
        if gid.endswith("_sleeve_glove"):
            _simplify_arm_geometry(node)
        if gid.endswith("_head_foundation") or gid.endswith("_front_head_anatomy"):
            _replace_hat_dome_with_angular_polygon(node)
            _simplify_eye_geometry(node)
            _lift_pupils_to_front(node)
    _polish_generated_svg(root)
    _promote_authoring_masters(root)
    _materialize_recolored_uses(root)
    _normalize_primitive_geometry_to_paths(root)
    _dedupe_authoring_component_paths(root)
    _ensure_semantic_ids(root)
    _mark_authoring_tiers(root)
    return ET.tostring(root, encoding="unicode") + "\n"


def svg_source_text() -> str:
    """Return editable side + front component libraries for all three forms."""
    forms = (SHORT_FORM, TALL_FORM, FIRE_FORM)
    layers: List[str] = []
    for form in forms:
        key = _FORM_KEYS[form.target_name]
        for projection, painter in (("side", _paint_side_view), ("front", _paint_front_view)):
            view_x, view_y = _VIEW_ORIGINS[(key, projection)]
            layers.append(
                f'<g id="maryo_view_{key}_{projection}" inkscape:groupmode="layer" '
                f'inkscape:label="{_VIEW_LABELS[(key, projection)]}" '
                f'data-rig-form="{key}" data-rig-projection="{projection}" '
                f'data-view-origin-x="{view_x}" data-view-origin-y="{view_y}" '
                f'transform="translate({view_x} {view_y})">'
                f'{painter(form)}</g>'
            )
    raw = (
        f'<svg xmlns="{SVG_NS}" xmlns:inkscape="{INK_NS}" '
        f'width="{_SOURCE_WIDTH}mm" height="{_SOURCE_HEIGHT}mm" '
        f'viewBox="0 0 {_SOURCE_WIDTH} {_SOURCE_HEIGHT}">'
        '<metadata>Generated from the accepted Mary-O v2 anatomy. Primitive Components are '
        'the single editable geometry authority and are normalized to SVG paths. Component '
        'Assemblies and final rig views are clone-derived and locked by default in Inkscape. '
        'Pivot helpers remain hidden inside Rig Guides groups. Python owns transient effects.</metadata>'
        f'{"".join(layers)}</svg>'
    )
    return _postprocess_svg_source(raw)


def export_svg_source(path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg_source_text(), encoding="utf8")
    return path


# --- SVG transform evaluation for hidden joint markers ---------------------
_IDENTITY = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
_XFORM_RE = re.compile(r"(\w+)\s*\(([^)]*)\)")


def _mat_mul(m, n):
    a1, b1, c1, d1, e1, f1 = m
    a2, b2, c2, d2, e2, f2 = n
    return (
        a1 * a2 + c1 * b2,
        b1 * a2 + d1 * b2,
        a1 * c2 + c1 * d2,
        b1 * c2 + d1 * d2,
        a1 * e2 + c1 * f2 + e1,
        b1 * e2 + d1 * f2 + f1,
    )


def _parse_transform(value: str | None):
    matrix = _IDENTITY
    for name, args in _XFORM_RE.findall(value or ""):
        values = [float(v) for v in re.split(r"[\s,]+", args.strip()) if v]
        if not values:
            continue
        if name == "translate":
            local = (1.0, 0.0, 0.0, 1.0, values[0], values[1] if len(values) > 1 else 0.0)
        elif name == "scale":
            sx = values[0]
            sy = values[1] if len(values) > 1 else sx
            local = (sx, 0.0, 0.0, sy, 0.0, 0.0)
        elif name == "rotate":
            radians = math.radians(values[0])
            c, s = math.cos(radians), math.sin(radians)
            rot = (c, s, -s, c, 0.0, 0.0)
            if len(values) >= 3:
                cx, cy = values[1], values[2]
                local = _mat_mul(
                    _mat_mul((1.0, 0.0, 0.0, 1.0, cx, cy), rot),
                    (1.0, 0.0, 0.0, 1.0, -cx, -cy),
                )
            else:
                local = rot
        elif name == "matrix" and len(values) >= 6:
            local = tuple(values[:6])
        else:
            continue
        matrix = _mat_mul(matrix, local)
    return matrix


def _apply_transform(matrix, x: float, y: float) -> tuple[float, float]:
    a, b, c, d, e, f = matrix
    return (a * x + c * y + e, b * x + d * y + f)


def _absolute_point(elem: ET.Element, parent: Dict[ET.Element, ET.Element], x: float, y: float) -> tuple[float, float]:
    chain: List[ET.Element] = []
    node: ET.Element | None = elem
    while node is not None:
        chain.append(node)
        node = parent.get(node)
    matrix = _IDENTITY
    for node in reversed(chain):
        matrix = _mat_mul(matrix, _parse_transform(node.get("transform")))
    return _apply_transform(matrix, x, y)


def _view_for_form(form: FormSpec, projection: str = "side") -> str:
    return _VIEW_LABELS[(_FORM_KEYS[form.target_name], projection)]


def _source_view_origin(form: FormSpec, projection: str = "side") -> tuple[float, float]:
    return tuple(float(v) for v in _VIEW_ORIGINS[(_FORM_KEYS[form.target_name], projection)])


_XLINK_HREF = "{http://www.w3.org/1999/xlink}href"
_DANGLING_USE_WARNED: set[str] = set()


def _warn_about_dangling_uses(root: ET.Element, svg_path: Path) -> None:
    """Warn when an SVG `<use>` references a missing id.

    A dangling reference renders nothing and is a real defect, but it should not
    block loading an in-progress asset. Warn once per file per process because a
    rig may be built repeatedly across forms and projections.
    """
    ids = {node.get("id") for node in root.iter() if node.get("id")}
    dangling = []
    for node in root.iter():
        if node.tag.rsplit("}", 1)[-1] != "use":
            continue
        href = node.get("href") or node.get(_XLINK_HREF) or ""
        if href.startswith("#") and href[1:] not in ids:
            dangling.append((node.get("id") or "<unnamed use>", href))
    if not dangling:
        return
    key = str(svg_path)
    if key in _DANGLING_USE_WARNED:
        return
    _DANGLING_USE_WARNED.add(key)
    listed = ", ".join(f"{who} -> {href}" for who, href in sorted(dangling))
    warnings.warn(
        f"{svg_path.name}: {len(dangling)} <use> element(s) reference an id this "
        f"document does not contain, so they draw NOTHING: {listed}",
        RuntimeWarning,
        stacklevel=3,
    )


#: Which tip pivot measures a limb's authored direction. A bone absent here has
#: no orientation to measure (torso, head) and is never rotated.
_TIP_OF_BONE = {
    "far_arm": "far_handtip",
    "near_arm": "near_handtip",
    "far_leg": "far_toe",
    "near_leg": "near_toe",
    "character_left_arm": "character_left_handtip",
    "character_right_arm": "character_right_handtip",
    "character_left_leg": "character_left_toe",
    "character_right_leg": "character_right_toe",
}


def _form_is_fire(form: FormSpec) -> bool:
    return "fire" in form.target_name


def _find_part_records(svg_path: Path, form: FormSpec, projection: str = "side") -> List[dict]:
    root = ET.fromstring(svg_path.read_bytes())
    _warn_about_dangling_uses(root, svg_path)
    parent = {child: node for node in root.iter() for child in node}
    view_label = _view_for_form(form, projection)
    view = next((g for g in root if g.get(INK_LABEL) == view_label), None)
    if view is None:
        raise ValueError(f"Mary-O SVG is missing view {view_label!r}")
    view_x, view_y = _source_view_origin(form, projection)
    #  PIVOTS LIVE IN THE MODEL'S FLAT `Rig Joints` LAYER, not inside the part
    # wrappers, which is how every other rig SVG in this package keys them
    # (`player-robot-v3.svg`, `oiler`, ...). Two things were wrong with a pivot
    # nested inside its part: it is a drawable *within* that part, so it leaks
    # into the part's raster, and its authored `cx`/`cy` is in the part's local
    # space -- Mary-O's were displaced 750-880 units from what Inkscape shows,
    # which makes them impossible to place by eye. Lookup is by `data-rig-joint`
    # == the part's `data-rig-bone`, so the pairing is still by NAME.
    joints_layer = next((g for g in view if g.get(INK_LABEL) == "Rig Joints"), None)
    if joints_layer is None:
        raise ValueError(
            f"Mary-O SVG view {view_label!r} has no 'Rig Joints' layer; pivots are "
            f"authored one flat layer per model, keyed by data-rig-joint"
        )
    markers = {
        m.get("data-rig-joint"): m
        for m in joints_layer.iter()
        if m.get("data-rig-joint")
    }
    #  A PART IS A PART WHEREVER IT SITS. This used to scan only the
    # view's DIRECT children, which quietly lost any part an author nested --
    # Tall and Short Front keep their `Death Expression` inside `Front Head`
    # (bone `head`), which is a perfectly reasonable place for a face to live,
    # and the result was no death face on those forms at all. Walking the whole
    # view in document order finds them, and keeps that order as the z-order.
    #
    #  a nested part must also be SUBTRACTED from its parent's art, or the face
    # would draw twice: once as the head's artwork and again as its own part,
    # with only one of them following the death channel.
    nested_part_ids = {
        e.get("id")
        for e in view.iter()
        if e is not view and e.get("data-rig-bone") and e.get("id")
    }
    records: List[dict] = []
    for source_order, wrapper in enumerate(e for e in view.iter() if e is not view):
        bone = wrapper.get("data-rig-bone")
        if not bone:
            continue
        #  ONLY FIRE HAS WINGS. The art exists in the tall views as well,
        # but tall Mary-O is not winged; drawing them there is wrong. Skipped at
        # read time rather than deleted, so the tall art stays intact for
        # whatever it is doing in the authoring file.
        if wrapper.get("data-rig-part") == "back_wings" and not _form_is_fire(form):
            continue
        name = wrapper.get("data-rig-part") or (wrapper.get("id") or "")
        #  A PART'S ART IS SIMPLY WHAT IS INSIDE IT. Once the pivots moved
        # out to the flat `Rig Joints` layer, a part wrapper holds nothing BUT
        # art, so demanding a `data-rig-art="true"` group is a rule with nothing
        # left to exclude -- and it rejected perfectly good authoring: Short
        # Front draws its arms as `<use>` clones of the side arms, directly
        # inside the wrapper, which is reuse worth encouraging. The tagged group
        # is still honoured when present (that is what the exporter emits).
        tagged = next((c for c in wrapper if c.get("data-rig-art") == "true"), None)
        art = tagged if tagged is not None else (wrapper if len(wrapper) else None)
        if art is None:
            #  AN EMPTY PART IS AUTHORING, NOT AN ERROR. `foreground_garment`
            # is genuinely empty in some forms; it used to satisfy the old check
            # because an empty `Artwork` group still counted as one, and became
            # fatal the moment that group was dissolved. A part with nothing in it
            # simply draws nothing. (A part with content but no ids IS still an
            # error -- see below.)
            continue
        #  A PART NEED NOT OWN A PIVOT. `back_wings` never had one and is not
        # supposed to: it is driven by `bone.torso_back`, which `_pose_values`
        # feeds from the SAME translation deltas as `bone.torso`, so the wings
        # hang off the body rather than articulating. A bone's pivot is only its
        # REST ANCHOR (every `rest_angle` here is 0 — Mary-O translates, she does
        # not rotate), so resting such a part at the torso's pivot moves it
        # exactly with the torso and displaces nothing.
        #  `markers.get(bone) or markers.get("torso")` IS A BUG, and it is
        # silent. An `ElementTree.Element` with no children is FALSY, and every
        # pivot is a childless `<circle>` -- so `or` discarded the correct marker
        # and handed every part the torso's pivot. It renders: each part simply
        # anchors at the body. Test for `None`, never for truth, on an Element.
        marker = markers.get(bone)
        if marker is None:
            marker = markers.get("torso")
        if marker is None:
            raise ValueError(
                f"Mary-O SVG part {name!r} has no pivot and neither does its view's "
                f"torso, so there is nothing to rest it against; the view's "
                f"'Rig Joints' layer holds {sorted(markers)}"
            )
        if tagged is not None:
            art_ids = [art.get("id")] if art.get("id") else []
        else:
            art_ids = [
                c.get("id")
                for c in wrapper
                if c.get("id") and c.get("id") not in nested_part_ids
            ]
        if not art_ids:
            raise ValueError(
                f"Mary-O SVG art for {name!r} has no id to render; every drawable "
                f"a part owns needs one so the rasterizer can isolate it"
            )
        try:
            cx = float(marker.get("cx", "nan"))
            cy = float(marker.get("cy", "nan"))
        except ValueError as ex:
            raise ValueError(f"Mary-O SVG pivot for {name!r} has invalid coordinates") from ex
        pivot_abs = _absolute_point(marker, parent, cx, cy)
        #  THE ART'S OWN ORIENTATION, so a pose is a DELTA and not an
        # absolute. A limb rotated to `angle` used to be rotated BY `angle`,
        # which is only right if the art is drawn pointing straight down. Mary-O's
        # front arms are authored at ~140 degrees (out to the sides), so death
        # added its 118 on top and crossed them over her chest. Measuring
        # pivot -> tip makes the renderer independent of how the limb happens to
        # be drawn, which is what the tip pivots are FOR.
        authored_angle = None
        authored_length = None
        tip_name = _TIP_OF_BONE.get(bone)
        if tip_name is not None:
            tip = markers.get(tip_name)
            if tip is not None:
                tx, ty = _absolute_point(
                    tip, parent, float(tip.get("cx", "nan")), float(tip.get("cy", "nan"))
                )
                # 0 = down, +90 = screen east, matching Mary-O's authored angles.
                authored_angle = math.degrees(
                    math.atan2(tx - pivot_abs[0], ty - pivot_abs[1])
                )
                #  the limb's real length, pivot to tip. Guessing it from
                # `form.leg_height` is what let a crouch drive the feet 14 units
                # through the floor: that number is layout intent, not geometry.
                authored_length = math.hypot(tx - pivot_abs[0], ty - pivot_abs[1])
        records.append(
            {
                "name": name,
                "bone": bone,
                #  THE SVG'S OWN STACKING IS THE Z-ORDER, and nothing may
                # reorder it. `rigdoc` sorts parts by this key, so handing it
                # the wrapper's DOCUMENT POSITION makes "raise/lower in Inkscape"
                # the one control over what draws in front -- the same answer
                # `humanoid_svg_rig` reached (it passes `source_order` as `z`).
                #
                #  it used to read `data-rig-z`, a second opinion that DISAGREED
                # with the art in four of six views: Short Side authors
                # far_arm after near_arm while its `data-rig-z` (10 vs 70) puts it
                # behind, so the sheet did not match the SVG an author was looking
                # at. The attribute is left on the elements -- it is still the
                # exporter's way of seeding a sensible initial stacking -- but it
                # is no longer consulted when reading.
                "z": float(source_order),
                "art_ids": art_ids,
                "pivot_abs": pivot_abs,
                "authored_angle": authored_angle,
                "authored_length": authored_length,
                "pivot_local": (pivot_abs[0] - view_x, pivot_abs[1] - view_y),
            }
        )
    if not records:
        raise ValueError(f"Mary-O SVG view {view_label!r} contains no rig parts")
    return records


def _delta(a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
    """Return a-b in authored-frame pixels."""
    return ((a[0] - b[0]) * SCALE, (a[1] - b[1]) * SCALE)


#: How far the torso squashes in a crouch. Tall and Fire are meant to end up at
#: half their idle height, which the torso alone has to supply; Short is already
#: one brick tall, so her crouch is a token dip rather than a fold.
#: How far the torso folds in a crouch.  half height is NOT reachable by
#: changing this: with legs and torso both collapsed to nothing the silhouette
#: still measures 0.79 of idle, because the head is a fixed, unscaled block. See
#: the note in `_pose_values`.


#: The per-pose nudge each limb reads. These are AUTHORED offsets -- a shoulder
#: or hip placed on purpose for a frame -- not the layout-differencing that used
#: to slide limbs off the body.
_POSE_NUDGE = {
    "near_arm": ("arm_front_dx", "arm_front_dy"),
    "far_arm": ("arm_back_dx", "arm_back_dy"),
    "near_leg": ("leg_front_dx", "leg_front_dy"),
    "far_leg": ("leg_back_dx", "leg_back_dy"),
}


#: Skid turns her head back over her shoulder. A FRACTION of her width, not a
#: pixel count, so it holds for every form; measured off the hand-placed pose
#: sheet at -0.0996 (tall) and -0.1130 (short).
_SKID_HEAD_X_FRACTION = -0.10


def _pose_values(form: FormSpec, pose: Pose, authored: Mapping[str, float] | None = None,
                 lengths: Mapping[str, float] | None = None) -> Dict[str, float]:
    base = _layout(form, Pose())
    cur = _layout(form, pose)
    authored = authored or {}
    lengths = lengths or {}
    out: Dict[str, float] = {}

    torso_dx, torso_dy = _delta((cur.body_x, cur.body_top), (base.body_x, base.body_top))
    for bone in ("torso_back", "torso"):
        out[f"bone.{bone}.x"] = torso_dx
        out[f"bone.{bone}.y"] = torso_dy

    #  THE HEAD RIDES THE TORSO TOO, and this was the last limb that did
    # not. Its own layout delta drifts away from the body pose by pose -- in
    # TALL swim far enough to open a visible gap at the neck (the hair still
    # touches, which is why a connected-components check would not catch it).
    # Same rule as the arms and legs: travel with the torso, then apply whatever
    # nudge the pose deliberately authored on top.
    head_dx = torso_dx + pose.head_dx * SCALE
    head_dy = torso_dy + pose.head_dy * SCALE
    out["bone.head.x"] = head_dx
    out["bone.head.y"] = head_dy
    #  SKID LOOKS BACK, so the head is mirrored rather than re-drawn. The
    # pose already carries the intent as `mode="lookback"`; it just had no way to
    # say it to the rig until `bone.<n>.flip_x` existed. One authored head serves
    # both directions.
    out["bone.head.flip_x"] = 1.0 if pose.mode == "lookback" else 0.0
    if pose.mode == "lookback":
        #  SKID LOOKS BACK OVER HER SHOULDER, so the head sits EAST of the
        # body -- 10% of her width. The layout's own `head_dx` was -1.1, i.e.
        # west, which put the mirrored face on the wrong side of her neck.
        #  MEASURED off the edited pose sheet, not guessed. Placed by hand
        # the head lands 10% of her width WEST -- tall at -2.81 and short at
        # -1.83, which are -0.0996 and -0.1130 of `body_width * SCALE`. I had it
        # EAST, which is the "translation is in the wrong direction" report.
        out["bone.head.x"] = _SKID_HEAD_X_FRACTION * form.body_width * SCALE

    if pose.mode == "crouch":
        #  THE CROUCH IS AUTHORED, NOT HARD-CODED. `body_dy` and
        # `torso_scale` sit in the pose table beside `crouch`, in the same units
        # as every other pose value, so the shape of a crouch is visible and
        # editable where the rest of the poses are. They were measured off the
        # hand-placed pose sheet -- but they live as DATA, not as a magic number
        # in the renderer that nobody can see or check.
        #
        #  the extra drop is the TORSO's alone. Head, shoulders and legs keep
        # the pose's own delta; pushing it through to them puts the feet through
        # the floor, and a 15.12-unit leg cannot shorten enough to compensate.
        lost = (1.0 - pose.torso_scale) * form.body_height * SCALE
        for bone in ("torso", "torso_back"):
            out[f"bone.{bone}.scale_y"] = pose.torso_scale
            out[f"bone.{bone}.y"] = out[f"bone.{bone}.y"] + pose.body_dy * SCALE
        out["bone.head.y"] = out["bone.head.y"] + lost
        crouch_drop = lost
        for bone in ("far_leg", "near_leg"):
            leg_px = max(1e-6, lengths.get(bone) or form.leg_height * SCALE)
            out[f"bone.{bone}.scale_y"] = max(0.05, 1.0 - torso_dy / leg_px)
    else:
        crouch_drop = 0.0

    def limb(
        bone: str,
        angle: float | None,
        base_pivot: tuple[float, float],
        cur_pivot: tuple[float, float],
        base_origin: tuple[float, float],
        cur_origin: tuple[float, float],
    ) -> None:
        if angle is None:
            dx, dy = _delta(cur_origin, base_origin)
            out[bone] = 0.0
        else:
            dx, dy = _delta(cur_pivot, base_pivot)
            # Mary-O historical limb angles use 0=down and +90=right.
            # RigDocument rotates screen-clockwise from the authored bind art,
            # so a down-authored rigid limb consumes the opposite signed delta.
            out[bone] = authored.get(bone, 0.0) - float(angle)
        #  AN ARM PIVOTS; IT DOES NOT SLIDE SIDEWAYS. The layout's per-pose
        # shoulder positions carry a horizontal component that came from the
        # procedural draw, where an arm was a shape positioned each frame rather
        # than a sprite hanging off a shoulder. Through the rig that reads as the
        # whole arm skating east/west across the body. Vertical shift is kept --
        # shoulders genuinely rise and fall with the torso -- and so is the pivot.
        #  AN ARM ROTATES ON ITS OWN AND TRANSLATES WITH THE TORSO. Its
        # own shoulder delta comes from the procedural layout, where an arm was a
        # shape placed per frame rather than a sprite hanging off a joint; fed to
        # the rig it slides the arm across the body and tears it off in skid.
        #  but zeroing it outright is the OTHER error, and it is the one that
        # broke death: every arm bone is root-parented, so an arm with no
        # translation simply stays behind while the torso, head and legs move.
        # Carrying the TORSO's delta is what "rigidly attached at the shoulder"
        # actually means.
        #  EVERY LIMB TRAVELS WITH THE TORSO AND POSES BY ROTATION. A leg
        # is hinged at the hip exactly as an arm is hinged at the shoulder, so
        # its own per-frame origin from the procedural layout detaches it the
        # same way -- which is the "legs disjoint from her body" in skid.
        #
        #  plus whatever nudge the pose deliberately AUTHORED, exactly as the
        # head takes `head_dx`/`head_dy`.  zeroing these was wrong: the
        # procedural SLIDING that had to go came from differencing two layouts,
        # not from `arm_front_dx`, which is somebody placing a shoulder on
        # purpose. Without it walk's east arm pivots 4.2 units west and 3.3 low.
        nudge = _POSE_NUDGE.get(bone)
        nx, ny = (0.0, 0.0) if nudge is None else (
            getattr(pose, nudge[0]) * SCALE,
            getattr(pose, nudge[1]) * SCALE,
        )
        out[f"bone.{bone}.x"] = torso_dx + nx
        out[f"bone.{bone}.y"] = torso_dy + ny

    limb("far_arm", pose.arm_back_angle, base.back_arm_origin, cur.back_shoulder, base.back_arm_origin, cur.back_arm_origin)
    limb("near_arm", pose.arm_front_angle, base.near_arm_origin, cur.near_shoulder, base.near_arm_origin, cur.near_arm_origin)
    limb("far_leg", pose.leg_back_angle, base.back_leg_origin, cur.back_hip, base.back_leg_origin, cur.back_leg_origin)
    limb("near_leg", pose.leg_front_angle, base.near_leg_origin, cur.near_hip, base.near_leg_origin, cur.near_leg_origin)
    if crouch_drop:
        # The shoulders sit on the torso, so they fall with its top. Legs do not:
        # the hips are the anchor the squash is measured from.
        for bone in ("far_arm", "near_arm"):
            out[f"bone.{bone}.y"] = out[f"bone.{bone}.y"] + crouch_drop
    return out


def _front_pose_values(form: FormSpec, pose: Pose, authored: Mapping[str, float] | None = None) -> Dict[str, float]:
    base = _front_layout(form, Pose(mode="dead"))
    cur = _front_layout(form, pose)
    authored = authored or {}
    out: Dict[str, float] = {}

    torso_dx, torso_dy = _delta((cur.body_x, cur.body_top), (base.body_x, base.body_top))
    for bone in ("torso_back", "torso"):
        out[f"bone.{bone}.x"] = torso_dx
        out[f"bone.{bone}.y"] = torso_dy

    head_dx, head_dy = _delta((cur.head_x, cur.head_top), (base.head_x, base.head_top))
    out["bone.head.x"] = head_dx
    out["bone.head.y"] = head_dy

    #  THE FRONT VIEW IS THE DEATH POSE, so death rotates NOTHING. This
    # used to drive each limb to a hard-coded angle (arms -/+118, legs -12/+16)
    # inherited from the procedural draw, where limbs were drawn straight down
    # and swung into place. Measured against the authored art those targets were
    # simply wrong: the arms sit at ~132 degrees and were being pulled 14 degrees
    # in, and the legs sit at ~55 and were being pulled ~43 degrees INWARD --
    # which is the "legs bend the wrong way" report. The art already says what
    # the pose is; the rig's job is to translate the body, not to re-pose limbs
    # somebody drew.
    limbs = (
        ("character_right_arm", base.character_right_shoulder, cur.character_right_shoulder),
        ("character_left_arm", base.character_left_shoulder, cur.character_left_shoulder),
        ("character_right_leg", base.character_right_hip, cur.character_right_hip),
        ("character_left_leg", base.character_left_hip, cur.character_left_hip),
    )
    for bone, base_pivot, cur_pivot in limbs:
        dx, dy = _delta(cur_pivot, base_pivot)
        out[bone] = 0.0
        # Every limb goes where the torso goes; see the side note.
        out[f"bone.{bone}.x"] = torso_dx
        out[f"bone.{bone}.y"] = torso_dy
    return out


def _keys(values: Sequence[float], *, loop: bool) -> dict:
    n = len(values)
    if n == 1:
        return {"const": float(values[0])}
    denom = n if loop else max(1, n - 1)
    return {"keys": [[i / denom, float(value), "linear"] for i, value in enumerate(values)]}


def _clips_for_form(form: FormSpec, projection: str = "side",
                    authored: Mapping[str, float] | None = None,
                    lengths: Mapping[str, float] | None = None) -> Dict[str, dict]:
    poses = TALL_LIKE_POSES if form.tall else SHORT_POSES
    row_durations = {row: duration for row, _frames, duration in form.rows}
    if projection == "front":
        pose_list = poses["death"]
        sampled = [_front_pose_values(form, pose, authored) for pose in pose_list]
        channel_names = sorted({name for frame in sampled for name in frame})
        return {
            "death": {
                "loop": False,
                "frames": len(pose_list),
                "duration_ms": row_durations["death"],
                "channels": {
                    name: _keys([frame.get(name, 0.0) for frame in sampled], loop=False)
                    for name in channel_names
                },
            }
        }

    looping = {"idle", "walk", "climb", "swim"}
    clips: Dict[str, dict] = {}
    for animation, pose_list in poses.items():
        #  only DEATH is excluded, and for a reason that is not about the rig:
        # it is authored as a FRONT projection, so its channels come from
        # `_front_pose_values` against the front document. `skid` and `crouch`
        # used to be excluded too, because the sheet drew them from the old
        # procedural code -- so the SVG art was silently unused for two of the
        # animations an author was looking at.
        if animation not in row_durations or animation == "death":
            continue
        loop = animation in looping
        sampled = [_pose_values(form, pose, authored, lengths) for pose in pose_list]
        channel_names = sorted({name for frame in sampled for name in frame})
        channels = {
            name: _keys([frame.get(name, 0.0) for frame in sampled], loop=loop)
            for name in channel_names
        }
        clips[animation] = {
            "loop": loop,
            "frames": len(pose_list),
            "duration_ms": row_durations[animation],
            "channels": channels,
        }
    return clips


def build_rig_document(svg_path: str | Path, form: FormSpec, projection: str = "side") -> RigDocument:
    """Build one rigid paper-doll document from an editable SVG projection."""
    if projection not in {"side", "front"}:
        raise ValueError(f"unknown Mary-O projection: {projection!r}")
    svg_path = Path(svg_path).resolve()
    records = _find_part_records(svg_path, form, projection)
    #  THE CLIPPED FEET ARE NOT FIXED BY MOVING THIS. Raising the ground
    # line to `_FRAME_H - 4` was measured and did NOT clear them: FIRE still ran
    # to the frame's bottom edge in idle, walk, skid, climb and fireball. Her
    # silhouette is 84 units in a 96-unit frame, so it FITS -- the art is simply
    # composited hard against the bottom, which means the cause is where the
    # sheet places the frame, not where this rig puts her feet.
    root = (_FRAME_W / 2.0, _FRAME_H - 1.0)
    bones = []
    seen: set[str] = set()
    for record in records:
        bone = str(record["bone"])
        if bone in seen:
            continue
        seen.add(bone)
        px, py = record["pivot_local"]
        bones.append(
            {
                "name": bone,
                "parent": None,
                "offset": [round(px - root[0], 4), round(py - root[1], 4)],
                "length": 0.0,
                "rest_angle": 0.0,
            }
        )
    parts = [
        {
            "name": record["name"],
            "bone": record["bone"],
            "z": record["z"],
            "kind": "sprite",
            "include": list(record["art_ids"]),
            "pivot": [round(record["pivot_abs"][0], 3), round(record["pivot_abs"][1], 3)],
            "rest_angle": 0.0,
        }
        for record in records
    ]
    data = {
        "name": f"{form.target_name}_svg_poc_{projection}",
        "maryo_projection": projection,
        "frame": {
            "width": _FRAME_W,
            "height": _FRAME_H,
            "center_x": root[0],
            "ground_y": root[1],
            "ankle_h": 0.0,
            "supersample": 1,
            "render_scale": 2,
        },
        "svg_source": {
            "path": str(svg_path),
            "view": _view_for_form(form, projection),
            "ref_dpi": _REF_DPI,
            "scale": 1.0,
        },
        "palette": {},
        "bones": bones,
        "parts": parts,
        "ik_legs": [],
        "ik_chains": [],
        "maryo_authored_lengths": {
            r["bone"]: r["authored_length"]
            for r in records
            if r.get("authored_length") is not None
        },
        "maryo_authored_angles": {
            r["bone"]: r["authored_angle"]
            for r in records
            if r.get("authored_angle") is not None
        },
        "clips": _clips_for_form(
            form,
            projection,
            {r["bone"]: r["authored_angle"] for r in records if r.get("authored_angle") is not None},
            {r["bone"]: r["authored_length"] for r in records if r.get("authored_length") is not None},
        ),
        "features": {},
        "sprite_tuning": {"part_order": "document"},
    }
    return RigDocument(data, source_path=svg_path)


def render_pose_with_doc(doc: RigDocument, form: FormSpec, pose: Pose) -> Image.Image:
    """Render an arbitrary pose through an already-loaded side or front doc."""
    projection = str(doc.data.get("maryo_projection", "side"))
    authored = doc.data.get("maryo_authored_angles") or {}
    values = (
        _front_pose_values(form, pose, authored)
        if projection == "front"
        else _pose_values(form, pose, authored, doc.data.get("maryo_authored_lengths") or {})
    )
    clip_name = "__maryo_poc_pose__"
    doc.data["clips"][clip_name] = {
        "loop": False,
        "frames": 1,
        "duration_ms": 1,
        "channels": {name: {"const": value} for name, value in values.items()},
    }
    doc.clips[clip_name] = doc.data["clips"][clip_name]
    return doc.render_frame(clip_name, 0, 1)


def render_rig_pose(svg_path: str | Path, form: FormSpec, pose: Pose, *, projection: str = "side") -> Image.Image:
    doc = build_rig_document(svg_path, form, projection)
    return render_pose_with_doc(doc, form, pose)


def render_rig_animation(
    svg_path: str | Path,
    form: FormSpec,
    animation: str,
    frame_idx: int,
    frame_count: int,
    *,
    projection: str = "side",
) -> Image.Image:
    doc = build_rig_document(svg_path, form, projection)
    return doc.render_frame(animation, frame_idx, frame_count)

def _logical_effect(painter) -> Image.Image:
    from ..super_mary_o_common import rasterize_logical

    native = rasterize_logical(LOGICAL_SIZE, SCALE, painter)
    authored = Image.new("RGBA", AUTHORING_FRAME_SIZE, (0, 0, 0, 0))
    authored.alpha_composite(native, (_CANVAS_X, _CANVAS_Y))
    return authored.resize((_FRAME_W * 2, _FRAME_H * 2), Image.Resampling.NEAREST)


def composite_effects(
    rig_frame: Image.Image,
    *,
    form: FormSpec,
    pose: Pose,
    animation: str,
    frame_idx: int,
    transform_aura: bool = False,
    power_loss: bool = False,
    fire_loss: bool = False,
    extra_star_phase: int = 0,
    sleeve_wing_boost: float = 0.0,
    show_orb: bool = False,
    fixed_transform_orb: bool = False,
) -> Image.Image:
    """Apply Mary-O's bespoke Python effects around the assembled SVG rig.

    This mirrors Noether's rig/effect split: anatomy remains SVG + bones while
    power flashes, sparkles, temporary sleeve wings, outfit stars, and fireball
    orbs stay procedural presentation effects.
    """
    behind = Image.new("RGBA", rig_frame.size, (0, 0, 0, 0))
    if transform_aura:
        behind.alpha_composite(_logical_effect(lambda px: _draw_transform_aura(px, frame_idx)))
    if power_loss:
        behind.alpha_composite(
            _logical_effect(lambda px: _draw_power_loss_sparkles(px, frame_idx, fire=fire_loss))
        )
    behind.alpha_composite(rig_frame)

    g = _layout(form, pose)
    if sleeve_wing_boost > 0.0:
        # Back sleeve wing is behind the body in the old composer. In the POC it
        # is intentionally emitted after the rigid body as an effect overlay;
        # the important contract being tested is that it no longer forces a
        # second arm sprite. If accepted, this can gain the same behind/front
        # split Noether uses without changing the rig topology.
        behind.alpha_composite(
            _logical_effect(
                lambda px: (
                    _draw_sleeve_wing_side(
                        px,
                        g.back_shoulder[0] - 0.3,
                        g.back_shoulder[1] + 1.1,
                        form=form,
                        strength=max(0.45, sleeve_wing_boost * 0.8),
                        facing=-1.0,
                    ),
                    _draw_sleeve_wing_side(
                        px,
                        g.near_shoulder[0] + 0.2,
                        g.near_shoulder[1] + 1.0,
                        form=form,
                        strength=sleeve_wing_boost,
                        facing=1.0,
                    ),
                )
            )
        )
    if extra_star_phase > 0:
        behind.alpha_composite(
            _logical_effect(
                lambda px: _draw_transform_outfit_stars(
                    px,
                    g.body_x,
                    g.body_top,
                    phase=extra_star_phase,
                    form=form,
                )
            )
        )
    if show_orb:
        if fixed_transform_orb:
            ox, oy = 19.4, 13.2 + 0.3 * math.sin(frame_idx)
        else:
            ox, oy = g.near_shoulder[0] + 5.0, g.near_shoulder[1] + 0.8
        behind.alpha_composite(_logical_effect(lambda px: _draw_fire_orb(px, ox, oy)))
    return behind


def procedural_fallback(form: FormSpec, pose: Pose, *, animation: str) -> Image.Image:
    """Render a side fallback frame with the accepted procedural compositor."""
    from ..super_mary_o_common import rasterize_logical

    native = rasterize_logical(
        LOGICAL_SIZE,
        SCALE,
        lambda px: _draw_side_pose(px, form, pose, animation=animation),
    )
    authored = Image.new("RGBA", AUTHORING_FRAME_SIZE, (0, 0, 0, 0))
    authored.alpha_composite(native, (_CANVAS_X, _CANVAS_Y))
    return authored.resize((_FRAME_W * 2, _FRAME_H * 2), Image.Resampling.NEAREST)


__all__ = [
    "build_rig_document",
    "composite_effects",
    "export_svg_source",
    "procedural_fallback",
    "render_pose_with_doc",
    "render_rig_animation",
    "render_rig_pose",
    "svg_source_text",
]
