"""Derive an `ambition-svg-rig-v1` catalog from art annotated in place.

The art already carries `data-rig-bone` / `data-rig-part` / `data-rig-z`, and a
joints layer already carries `data-rig-joint` circles in root user space. That
is the whole static rig; this turns it into the catalog + marker layer the
renderer reads, so the annotated artwork stays the single authored source.
"""
from __future__ import annotations

import math
from typing import Iterable

from lxml import etree

SVG = "http://www.w3.org/2000/svg"
INK = "http://www.inkscape.org/namespaces/inkscape"

# `humanoid-articulated-v1`: bone -> (parent, origin joint, tip joint).
# Parents are listed before children so the catalog order is already valid.
HUMANOID_V1: tuple[tuple[str, str | None, str, str | None], ...] = (
    ("pelvis", None, "hip_center", None),
    ("torso", "pelvis", "waist", None),
    ("head", "torso", "neck", None),
    ("far_arm_u", "torso", "far_shoulder", "far_elbow"),
    ("far_arm_l", "far_arm_u", "far_elbow", "far_wrist"),
    ("far_arm_hand", "far_arm_l", "far_wrist", "far_handtip"),
    ("far_leg_u", "pelvis", "far_hip", "far_knee"),
    ("far_leg_l", "far_leg_u", "far_knee", "far_ankle"),
    ("far_leg_foot", "far_leg_l", "far_ankle", "far_toe"),
    ("near_arm_u", "torso", "near_shoulder", "near_elbow"),
    ("near_arm_l", "near_arm_u", "near_elbow", "near_wrist"),
    ("near_arm_hand", "near_arm_l", "near_wrist", "near_handtip"),
    ("near_leg_u", "pelvis", "near_hip", "near_knee"),
    ("near_leg_l", "near_leg_u", "near_knee", "near_ankle"),
    ("near_leg_foot", "near_leg_l", "near_ankle", "near_toe"),
)


def _fmt(value: float) -> str:
    text = f"{float(value):.6f}".rstrip("0").rstrip(".")
    return "0" if text in {"", "-0"} else text


def collect_joints(root, layer_id: str) -> dict[str, tuple[float, float]]:
    layer = root.xpath(f"//*[@id='{layer_id}']")[0]
    out = {}
    for elem in layer.iter():
        name = elem.get("data-rig-joint")
        if name:
            out[name] = (float(elem.get("cx")), float(elem.get("cy")))
    return out


def collect_parts(root, view_id: str) -> list[dict]:
    view = root.xpath(f"//*[@id='{view_id}']")[0]
    out = []
    for elem in view.iter():
        name = elem.get("data-rig-part")
        if not name:
            continue
        out.append(
            {
                "name": name,
                "bone": elem.get("data-rig-bone"),
                "z": elem.get("data-rig-z") or "0",
                "element": elem.get("id"),
                # ⛔⛔ AN ALTERNATE'S CHANNEL IS PART OF THE PART. Dropped here,
                # it never reached the catalog, `motion_ir` read no channel, and
                # a part meant to be INVISIBLE until a clip asks for it drew in
                # every frame -- which is why the Officer published with a spare
                # fist beside his hip and a second torso beside his head.
                "opacity": elem.get("data-rig-opacity"),
                "opacity_default": elem.get("data-rig-opacity-default"),
            }
        )
    out.sort(key=lambda part: float(part["z"]))
    return out


def bone_world_angles(joints, parts) -> dict[str, float]:
    """World rest angle per bone: origin->tip where it exists, else the parent's.

    A zero-length organizational bone (pelvis, torso, head) has no direction of
    its own; its art is drawn upright, so 0 is the honest bind angle and the
    renderer's fallback agrees with it.
    """
    angles: dict[str, float] = {}
    for name, parent, origin, tip in HUMANOID_V1:
        if tip is not None and origin in joints and tip in joints:
            ox, oy = joints[origin]
            tx, ty = joints[tip]
            if math.dist((ox, oy), (tx, ty)) > 1e-9:
                angles[name] = math.degrees(math.atan2(ty - oy, tx - ox))
                continue
        angles[name] = 0.0
    return angles


def build(
    *,
    view_id: str,
    source_layer: str,
    source_label: str,
    facing: str,
    catalog_view: str,
    joints,
    parts,
    profile: str = "humanoid-articulated-v1",
) -> tuple[str, str]:
    """Return ``(metadata_block, marker_layer)`` as serialized SVG fragments."""

    # Angles are derived from the coordinates the markers will actually CARRY,
    # not from full-precision intermediates: the markers are the rest authority,
    # so anything derived off unrounded values disagrees with `sync-bind-angles`
    # in the last digit the moment anyone re-runs it.
    joints = {name: (round(x, 6), round(y, 6)) for name, (x, y) in joints.items()}
    angles = bone_world_angles(joints, parts)
    jid = lambda name: f"ambition-rig-{catalog_view}-joint-{name}"
    bid = lambda name: f"ambition-rig-{catalog_view}-bind-{name}"
    origin_of = {bone: origin for bone, _parent, origin, _tip in HUMANOID_V1}

    meta = [
        '<metadata id="ambition-rig-metadata"',
        '   data-ambition-schema="ambition-svg-rig-v1"',
        '   data-ambition-role="character-rig"',
        '   data-rig-coordinate-space="root-svg-user-space"',
        '   data-rig-rest-authority="markers">',
        f'  <g id="ambition-rig-view-{catalog_view}"',
        f'     data-rig-view-def="{catalog_view}"',
        f'     data-rig-facing="{facing}"',
        f'     data-rig-source-layer="{source_layer}"',
        f'     data-rig-source-label="{source_label}"',
        f'     data-rig-root="{jid("rig_root")}"',
        '     data-rig-projection="side"',
        f'     data-rig-profile="{profile}"',
        '     data-rig-pose-authority="geometry-only"',
        '     data-rig-part-order="attribute"',
        '     data-rig-source-map-quality="authored-markers">',
    ]
    for name, parent, origin, tip in HUMANOID_V1:
        attrs = [
            f'id="ambition-rig-{catalog_view}-bone-{name}"',
            f'data-rig-bone-def="{name}"',
        ]
        if parent:
            attrs.append(f'data-rig-parent="{parent}"')
        attrs.append(f'data-rig-origin="{jid(origin)}"')
        if tip is not None and tip in joints:
            attrs.append(f'data-rig-tip="{jid(tip)}"')
        meta.append("    <g " + "\n       ".join(attrs) + " />")
    for part in parts:
        bone = part["bone"]
        attrs = [
            f'id="ambition-rig-{catalog_view}-part-{part["name"]}"',
            f'data-rig-part-def="{part["name"]}"',
            f'data-rig-bone="{bone}"',
            f'data-rig-z="{part["z"]}"',
            f'data-rig-pivot="{bid(part["name"])}"',
            f'data-rig-bind-angle="{_fmt(angles[bone])}"',
            f'data-rig-elements="{part["element"]}"',
        ]
        if part.get("opacity"):
            attrs.append(f'data-rig-opacity="{part["opacity"]}"')
            if part.get("opacity_default") is not None:
                attrs.append(
                    f'data-rig-opacity-default="{part["opacity_default"]}"')
        meta.append("    <g " + "\n       ".join(attrs) + " />")
    meta += ["  </g>", "</metadata>"]

    markers = [
        '<g id="ambition-rig-markers"',
        '   data-rig-editor-layer="true"',
        '   inkscape:groupmode="layer"',
        f'   inkscape:label="Ambition Rig Markers"',
        '   style="display:inline">',
        f'  <g id="ambition-rig-markers-{catalog_view}"',
        f'     data-rig-view="{catalog_view}"',
        f'     inkscape:label="Rig Markers - {source_label}">',
    ]
    radius = _marker_radius(joints)
    for name, _parent, origin, tip in HUMANOID_V1:
        if tip is None or tip not in joints:
            continue
        ox, oy = joints[origin]
        tx, ty = joints[tip]
        markers.append(
            f'    <line id="ambition-rig-{catalog_view}-guide-{name}"\n'
            f'       data-rig-bone-guide="{name}"\n'
            f'       x1="{_fmt(ox)}" y1="{_fmt(oy)}" x2="{_fmt(tx)}" y2="{_fmt(ty)}"\n'
            f'       stroke="#d226c6" stroke-width="{_fmt(radius * 0.4)}" stroke-opacity="0.32" />'
        )
    for name in sorted(joints):
        cx, cy = joints[name]
        markers.append(
            f'    <circle id="{jid(name)}"\n'
            f'       data-rig-joint="{name}"\n'
            f'       inkscape:label="Joint - {name}"\n'
            f'       cx="{_fmt(cx)}" cy="{_fmt(cy)}" r="{_fmt(radius)}"\n'
            f'       fill="#ff3bd4" fill-opacity="0.58" stroke="#43133d" stroke-width="{_fmt(radius / 3)}" />'
        )
    # One bind pivot per PART, separate from the skeleton it starts on. Sharing
    # the joint marker makes the art un-tunable: nudging a sleeve that hinges a
    # little outboard of the shoulder would drag the shoulder, and with it the
    # whole arm chain. Seeded at the bone origin, so an untouched rig renders
    # exactly as it does now.
    for part in parts:
        cx, cy = joints[origin_of[part["bone"]]]
        markers.append(
            f'    <circle id="{bid(part["name"])}"\n'
            f'       data-rig-bind-pivot="{part["name"]}"\n'
            f'       inkscape:label="Bind - {part["name"]}"\n'
            f'       cx="{_fmt(cx)}" cy="{_fmt(cy)}" r="{_fmt(radius * 0.733)}"\n'
            f'       fill="#28c8ff" fill-opacity="0.42" stroke="#093b52" stroke-width="{_fmt(radius * 0.267)}" />'
        )
    markers += ["  </g>", "</g>"]
    return "\n".join(meta), "\n".join(markers)


def _marker_radius(joints) -> float:
    """Markers are editor furniture; size them to the rig, not to a constant."""
    ys = [y for _x, y in joints.values()]
    return round(max(1e-6, (max(ys) - min(ys)) / 200.0), 4)
