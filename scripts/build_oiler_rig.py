#!/usr/bin/env python3
"""Rebind Oiler's directly authored Euler-mechanic SVG to three view rigs.

The SVG is the editable source of truth.  This command validates the flat,
propless Euler-inspired character-art contract, then refreshes only geometry
and sprite bindings. Hand-tuned clips in the generated ``.rig.json`` files are
preserved unless ``--fresh`` is requested.

Usage::

    uv run python scripts/build_oiler_rig.py build
    uv run python scripts/build_oiler_rig.py build --fresh
    uv run python scripts/build_oiler_rig.py validate
"""

from __future__ import annotations

import argparse
import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

from ambition_sprite2d_renderer.authoring.humanoid_svg_rig import (
    HumanoidViewSpec,
    build_humanoid_view_document,
    merge_generated_geometry,
)
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument

ROOT = Path(__file__).resolve().parents[1]
SVG = ROOT / "ambition_sprite2d_renderer/data/characters/oiler/oiler-multiview.svg"
RIG_DIR = ROOT / "ambition_sprite2d_renderer/targets/characters/rigged/oiler"
SCRATCH = ROOT / "agent-scratch/oiler_rig"
DESIGN_ID = "euler-mechanic-v1"
RIG_HIERARCHY_ID = "pca-style-v1"
NOSE_DESIGN_ID = "euler-straight-bridge-projections-v2"
INKSCAPE_LABEL = "{http://www.inkscape.org/namespaces/inkscape}label"
INKSCAPE_GROUPMODE = "{http://www.inkscape.org/namespaces/inkscape}groupmode"
RIG_PART = "data-rig-part"
RIG_BONE = "data-rig-bone"
RIG_Z = "data-rig-z"
RIG_JOINT = "data-rig-joint"
RIG_SIDE_MAP = "data-rig-side-map"
NOSE_PROJECTIONS = {
    "Oiler - Three Quarter": "three-quarter-left",
    "Oiler - Front": "front",
    "Oiler - Side Right": "profile-right",
}

ANATOMICAL_TOP_LAYER_ORDER = (
    "Arm - Left",
    "Leg - Left",
    "Leg - Right",
    "Torso",
    "Head",
    "Arm - Right",
    "Joints",
)
PERSPECTIVE_PART_PARENT = {
    "far_arm_u": "Arm - Left",
    "far_arm_l": "Arm - Left",
    "far_hand": "Arm - Left",
    "far_leg_u": "Leg - Left",
    "far_leg_l": "Leg - Left",
    "far_leg_foot": "Leg - Left",
    "near_leg_u": "Leg - Right",
    "near_leg_l": "Leg - Right",
    "near_leg_foot": "Leg - Right",
    "pelvis_yoke": "Torso",
    "torso": "Torso",
    "apron": "Torso",
    "head": "Head",
    "blink": "Head",
    "talk_mouth": "Head",
    "near_arm_u": "Arm - Right",
    "near_arm_l": "Arm - Right",
    "near_hand": "Arm - Right",
}
FRONT_PART_PARENT = {
    **{
        name.replace("far_", "left_", 1): parent.replace("Far", "Left")
        for name, parent in PERSPECTIVE_PART_PARENT.items()
        if name.startswith("far_")
    },
    **{
        name.replace("near_", "right_", 1): parent.replace("Near", "Right")
        for name, parent in PERSPECTIVE_PART_PARENT.items()
        if name.startswith("near_")
    },
    **{
        name: parent
        for name, parent in PERSPECTIVE_PART_PARENT.items()
        if not name.startswith(("near_", "far_"))
    },
}
ANATOMICAL_JOINT_LAYER_ORDER = (
    "Core Joints",
    "Arm Joints - Left",
    "Arm Joints - Right",
    "Leg Joints - Left",
    "Leg Joints - Right",
)

VIEWS = {
    "three_quarter": HumanoidViewSpec(
        view="Oiler - Three Quarter",
        name="oiler_three_quarter",
        target_height=105.0,
        collision_scale=1.72,
    ),
    "front": HumanoidViewSpec(
        view="Oiler - Front",
        name="oiler_front",
        target_height=105.0,
        collision_scale=1.72,
    ),
    "side": HumanoidViewSpec(
        view="Oiler - Side Right",
        name="oiler_side",
        target_height=105.0,
        collision_scale=1.72,
    ),
}


def _rig_joint_name(elem: ET.Element) -> str | None:
    explicit = elem.get(RIG_JOINT)
    if explicit:
        return explicit
    label = elem.get(INKSCAPE_LABEL) or ""
    if label.startswith("joint:"):
        return label.split(":", 1)[1]
    return None


def _validate_artist_hierarchy(
    root: ET.Element, view_nodes: dict[str, ET.Element]
) -> None:
    """Keep Oiler's layer panel as editable as the manually authored PCA SVG."""

    if root.get("data-rig-hierarchy") != RIG_HIERARCHY_ID:
        raise ValueError(
            f"Oiler SVG must declare data-rig-hierarchy={RIG_HIERARCHY_ID!r}"
        )

    machine_labels = [
        elem.get(INKSCAPE_LABEL)
        for elem in root.iter()
        if (elem.get(INKSCAPE_LABEL) or "").startswith(("part:", "joint:"))
    ]
    if machine_labels:
        raise ValueError(
            "Oiler's Inkscape labels must stay human-readable; rig metadata "
            f"belongs in data-rig-* attributes: {machine_labels[:5]}"
        )

    for view_name, view in view_nodes.items():
        is_front = view_name == "Oiler - Front"
        top_layer_order = ANATOMICAL_TOP_LAYER_ORDER
        part_parent = FRONT_PART_PARENT if is_front else PERSPECTIVE_PART_PARENT
        joint_layer_order = ANATOMICAL_JOINT_LAYER_ORDER
        if is_front:
            if view.get(RIG_SIDE_MAP) != "left=far,right=near":
                raise ValueError(
                    "Oiler front must map character-relative left/right anatomy "
                    "onto the runtime's far/near channels"
                )
        elif view.get(RIG_SIDE_MAP):
            raise ValueError(
                f"{view_name} uses depth-oriented near/far labels and must not "
                f"declare {RIG_SIDE_MAP}"
            )

        direct_layers = [
            child
            for child in list(view)
            if isinstance(child.tag, str)
            and child.tag.endswith("}g")
            and child.get(INKSCAPE_LABEL)
        ]
        direct_labels = tuple(child.get(INKSCAPE_LABEL) for child in direct_layers)
        if set(direct_labels) != set(top_layer_order) or len(direct_labels) != len(
            top_layer_order
        ):
            raise ValueError(
                f"{view_name} top-level layers must be {top_layer_order}, "
                f"got {direct_labels}"
            )
        if any(child.get(INKSCAPE_GROUPMODE) != "layer" for child in direct_layers):
            raise ValueError(f"{view_name} anatomical groups must be Inkscape layers")

        parents = {child: parent for parent in view.iter() for child in list(parent)}
        parts = [elem for elem in view.iter() if elem.get(RIG_PART)]
        names = [elem.get(RIG_PART) for elem in parts]
        if len(names) != len(set(names)):
            raise ValueError(f"{view_name} contains duplicate data-rig-part names")
        expected_parts = set(part_parent)
        if view_name == "Oiler - Side Right":
            expected_parts.remove("talk_mouth")
        if set(names) != expected_parts:
            raise ValueError(
                f"{view_name} rig parts differ: expected {sorted(expected_parts)}, "
                f"got {sorted(names)}"
            )
        for part in parts:
            name = part.get(RIG_PART)
            parent = parents.get(part)
            parent_label = parent.get(INKSCAPE_LABEL) if parent is not None else None
            if parent_label != part_parent[name]:
                raise ValueError(
                    f"{view_name} part {name!r} belongs under {part_parent[name]!r}, "
                    f"not {parent_label!r}"
                )
            if not part.get(RIG_BONE) or part.get(RIG_Z) is None:
                raise ValueError(
                    f"{view_name} part {name!r} lacks explicit rig metadata"
                )
            if part.get(INKSCAPE_GROUPMODE) != "layer":
                raise ValueError(f"{view_name} part {name!r} must be an Inkscape layer")

        joints_layer = next(
            child
            for child in direct_layers
            if child.get(INKSCAPE_LABEL) == "Joints"
        )
        joint_group_labels = tuple(
            child.get(INKSCAPE_LABEL)
            for child in list(joints_layer)
            if isinstance(child.tag, str) and child.tag.endswith("}g")
        )
        if set(joint_group_labels) != set(joint_layer_order) or len(
            joint_group_labels
        ) != len(joint_layer_order):
            raise ValueError(
                f"{view_name} joint groups must be {joint_layer_order}, "
                f"got {joint_group_labels}"
            )
        joint_names = [
            elem.get(RIG_JOINT) for elem in joints_layer.iter() if elem.get(RIG_JOINT)
        ]
        if len(joint_names) != 18 or len(joint_names) != len(set(joint_names)):
            raise ValueError(
                f"{view_name} must expose 18 uniquely named data-rig-joint markers"
            )
        if is_front:
            source_terms = [
                *(elem.get(INKSCAPE_LABEL) or "" for elem in view.iter()),
                *(elem.get(RIG_PART) or "" for elem in view.iter()),
                *(elem.get(RIG_BONE) or "" for elem in view.iter()),
                *(elem.get(RIG_JOINT) or "" for elem in view.iter()),
            ]
            leaked = [
                term
                for term in source_terms
                if "near" in term.lower() or "far" in term.lower()
            ]
            if leaked:
                raise ValueError(
                    "Oiler front SVG must name anatomy from Oiler's own left/right "
                    f"frame, not camera depth: {leaked[:5]}"
                )


def _validate_svg_source() -> None:
    """Reject source edits that erase Oiler's distinctive art contract."""

    text = SVG.read_text(encoding="utf8").lower()
    forbidden = (
        "<filter",
        "<lineargradient",
        "<radialgradient",
        "url(#",
        "drop-shadow",
        "dropshadow",
        "part:machine",
        "part:wrench",
        'data-rig-part="machine"',
        'data-rig-part="wrench"',
        "oil-flask",
        "satchel",
    )
    present = [token for token in forbidden if token in text]
    if present:
        raise ValueError(f"Oiler SVG contains forbidden art features: {present}")

    root = ET.parse(SVG).getroot()
    if root.get("data-character-design") != DESIGN_ID:
        raise ValueError(f"Oiler SVG must declare data-character-design={DESIGN_ID!r}")

    ids = {elem.get("id") for elem in root.iter() if elem.get("id")}

    retired = sorted(
        elem_id
        for elem_id in ids
        if "beard" in elem_id.lower() or "moustache" in elem_id.lower()
    )
    if retired:
        raise ValueError(f"Oiler's clean-shaven Euler face regressed: {retired}")

    view_nodes = {
        elem.get(INKSCAPE_LABEL): elem
        for elem in root.iter()
        if (elem.get(INKSCAPE_LABEL) or "").startswith("Oiler - ")
    }
    expected = {spec.view for spec in VIEWS.values()}
    if set(view_nodes) != expected:
        raise ValueError(
            f"Oiler SVG views differ: expected {expected}, got {set(view_nodes)}"
        )

    required_design_roles = {
        "cap-back-and-tail",
        "cap-crown-and-folds",
        "neckcloth-and-cravat",
        "face-shape-and-ears",
        "lapels-and-upper-coat-trim",
        "apron-details",
        "nose-construction",
    }
    for view_name, view in view_nodes.items():
        design_roles = {
            elem.get("data-oiler-role")
            for elem in view.iter()
            if elem.get("data-oiler-role")
        }
        missing_roles = sorted(required_design_roles - design_roles)
        if missing_roles:
            raise ValueError(
                f"{view_name} is missing Euler design roles: {missing_roles}"
            )

    _validate_artist_hierarchy(root, view_nodes)

    if root.get("data-nose-design") != NOSE_DESIGN_ID:
        raise ValueError(
            f"Oiler SVG must declare data-nose-design={NOSE_DESIGN_ID!r}"
        )
    for view_name, view in view_nodes.items():
        nose_layers = [
            elem
            for elem in view.iter()
            if elem.get(INKSCAPE_LABEL) == "Nose"
        ]
        if len(nose_layers) != 1:
            raise ValueError(
                f"{view_name} must expose exactly one artist-facing Nose layer"
            )
        nose = nose_layers[0]
        if nose.get("data-oiler-role") != "nose-construction":
            raise ValueError(f"{view_name} Nose layer lacks its design role")
        if nose.get("data-nose-form") != "straight-bridge-soft-tip":
            raise ValueError(
                f"{view_name} nose must use Oiler's shared straight-bridge form"
            )
        expected_projection = NOSE_PROJECTIONS[view_name]
        if nose.get("data-nose-projection") != expected_projection:
            raise ValueError(
                f"{view_name} nose must declare the {expected_projection!r} projection"
            )

    nose_ids = {
        elem.get("id")
        for view in view_nodes.values()
        for elem in view.iter()
        if elem.get("id")
    }
    required_nose_ids = {
        "tq-nose-bridge",
        "tq-nostril",
        "front-nose-bridge",
        "front-nostril-left",
        "front-nostril-right",
        "side-nostril",
    }
    missing_nose_ids = sorted(required_nose_ids - nose_ids)
    if missing_nose_ids:
        raise ValueError(
            f"Oiler's shared nose construction is incomplete: {missing_nose_ids}"
        )
    forbidden_nose_ids = {
        "side-nose",
        "side-nose-crease",
        "front-face-centerline",
        "front-nose-base",
        "tq-nose-base",
    }
    stale_nose_ids = sorted(forbidden_nose_ids & nose_ids)
    if stale_nose_ids:
        raise ValueError(
            "Oiler's retired nose constructions remain in the SVG: "
            f"{stale_nose_ids}"
        )

    # The front view is deliberately authored around a frontal body axis.  It
    # must not regress to a translated/sheared copy of the three-quarter art.
    front = view_nodes["Oiler - Front"]
    if front.get("data-view-construction") != "authored-front-v3":
        raise ValueError("Oiler front view must declare authored-front-v3")
    axis_x = float(front.get("data-front-axis-x", "nan"))
    if front.get("data-front-hip-layout") != "pelvis-sockets-v3":
        raise ValueError("Oiler front view must declare pelvis-sockets-v3")
    if front.get("data-front-face-volume") != "full-volume-v3":
        raise ValueError("Oiler front view must declare full-volume-v3")

    front_required = {
        "front-nose-bridge",
        "front-cheek-left",
        "front-cheek-right",
        "front-cap-center-pleat",
        "front-coat-center-seam",
        "front-coat-button-upper",
        "front-coat-button-lower",
    }
    missing = sorted(front_required - ids)
    if missing:
        raise ValueError(f"Oiler front view lacks frontal construction: {missing}")

    joints = {
        name: (float(elem.get("cx")), float(elem.get("cy")))
        for elem in front.iter()
        if (name := _rig_joint_name(elem)) is not None
    }
    for name in ("waist", "neck"):
        if abs(joints[name][0] - axis_x) > 0.01:
            raise ValueError(f"Oiler front {name} is off the frontal axis")
    for right_name, left_name in (
        ("right_shoulder", "left_shoulder"),
        ("right_hip", "left_hip"),
        ("right_knee", "left_knee"),
        ("right_ankle", "left_ankle"),
    ):
        right_x = joints[right_name][0]
        left_x = joints[left_name][0]
        if not right_x < axis_x < left_x:
            raise ValueError(
                f"Oiler front {right_name}/{left_name} must straddle the body axis"
            )
        if left_x - right_x < 18.0:
            raise ValueError(
                f"Oiler front {right_name}/{left_name} are implausibly compressed"
            )

    hip_depth = (joints["right_hip"][1] + joints["left_hip"][1]) / 2.0 - joints[
        "waist"
    ][1]
    hip_span = joints["left_hip"][0] - joints["right_hip"][0]
    if not 21.0 <= hip_depth <= 27.0:
        raise ValueError(
            f"Oiler front hip sockets must sit low in the pelvis, got depth {hip_depth}"
        )
    if not 32.0 <= hip_span <= 40.0:
        raise ValueError(
            f"Oiler front hip sockets must form a stable pelvis span, got {hip_span}"
        )

    # The side view must remain a genuinely authored profile.  These metadata
    # flags are intentionally explicit because the most common regression is a
    # flattened frontal pouch, a two-lapel V, or an arm whose elbow bends the
    # wrong way after manual SVG edits.
    side = view_nodes["Oiler - Side Right"]
    expected_side_contract = {
        "data-side-profile-construction": "authored-profile-v3",
        "data-side-arm-hinge": "shoulder-back-elbow-back-wrist-forward-v3",
        "data-side-pouch-construction": "narrow-profile-gusset-v2",
        "data-side-lapel-construction": "single-profile-lapel-v2",
        "data-side-face-construction": "integrated-profile-features-v3",
    }
    for attr, expected_value in expected_side_contract.items():
        if side.get(attr) != expected_value:
            raise ValueError(
                f"Oiler side view must declare {attr}={expected_value!r}"
            )

    side_ids = {elem.get("id"): elem for elem in side.iter() if elem.get("id")}
    side_required = {
        "side-ear",
        "side-ear-inner",
        "side-philtrum",
        "side-mouth-closed",
        "side-lower-lip",
        "side-lapel-edge",
        "side-apron-pocket-flap",
        "side-apron-pocket-gusset",
        "side-apron-belt-loop",
    }
    missing_side = sorted(side_required - side_ids.keys())
    if missing_side:
        raise ValueError(
            f"Oiler side view lacks authored profile details: {missing_side}"
        )

    side_joints = {
        name: (float(elem.get("cx")), float(elem.get("cy")))
        for elem in side.iter()
        if (name := _rig_joint_name(elem)) is not None
    }
    for side_name in ("far", "near"):
        shoulder = side_joints[f"{side_name}_shoulder"]
        elbow = side_joints[f"{side_name}_elbow"]
        wrist = side_joints[f"{side_name}_wrist"]
        shoulder_to_elbow = shoulder[0] - elbow[0]
        elbow_to_wrist = wrist[0] - elbow[0]
        if not 6.0 <= shoulder_to_elbow <= 12.0:
            raise ValueError(
                f"Oiler side {side_name} elbow must sit modestly behind the "
                f"shoulder, got {shoulder_to_elbow}"
            )
        if not 9.0 <= elbow_to_wrist <= 14.0:
            raise ValueError(
                f"Oiler side {side_name} wrist must return forward from the "
                f"elbow, got {elbow_to_wrist}"
            )
        if not shoulder[1] < elbow[1] < wrist[1]:
            raise ValueError(
                f"Oiler side {side_name} arm joints are vertically inverted"
            )


def _const(value: float) -> dict:
    return {"const": round(float(value), 4)}


def _expr(expr: str) -> dict:
    return {"expr": expr}


def _keys(values, *, ease: str = "smooth") -> dict:
    n = len(values)
    return {
        "keys": [
            [round(i / n, 6), round(float(value), 4), ease]
            for i, value in enumerate(values)
        ]
    }


def _shot(values, *, ease: str = "smooth") -> dict:
    """Keys for a ONE-SHOT clip, spaced the way one-shots are sampled.

    ``RigDocument.frame_time`` samples a loop at ``i/n`` and a one-shot at
    ``i/(n-1)`` -- so a one-shot authored with :func:`_keys` puts its last key at
    ``(n-1)/n`` and its last FRAME at ``1.0``, which clamps and spends the final
    frame repeating the one before it.  For a walk cycle that is invisible; for
    an attack it eats the recovery frame, which is the one the eye reads as "the
    swing is over".  These land on the frames.
    """

    n = len(values)
    return {
        "keys": [
            [round(i / max(1, n - 1), 6), round(float(value), 4), ease]
            for i, value in enumerate(values)
        ]
    }


def _rest(doc: dict, prefix: str, axis: str) -> float:
    for chain in doc.get("ik_chains", []):
        if chain.get("channel_prefix") == prefix:
            return float(chain[f"rest_{axis}"])
    for leg in doc.get("ik_legs", []):
        if leg.get("channel_prefix") == prefix:
            return float(leg[f"rest_{axis}"])
    raise KeyError((prefix, axis))


def _rest_pitch(doc: dict, prefix: str) -> float:
    for collection in (doc.get("ik_chains", []), doc.get("ik_legs", [])):
        for chain in collection:
            if chain.get("channel_prefix") == prefix:
                return float(chain["rest_pitch"])
    raise KeyError(prefix)


def _with_visibility(channels: dict, *, blink=0.0, talk=0.0):
    """Set expression channels only.

    Character art deliberately contains no tools, machines, bags, or other
    detachable props. Runtime props should bind to the exported hand sockets.
    """

    channels.update(
        {
            "blink_vis": _const(blink),
            "talk_vis": _const(talk),
        }
    )
    return channels


def _three_quarter_clips(doc: dict) -> dict:
    nx = _rest(doc, "near_hand", "x")
    ny = _rest(doc, "near_hand", "y")
    fx = _rest(doc, "far_hand", "x")
    fy = _rest(doc, "far_hand", "y")
    np = _rest_pitch(doc, "near_hand")
    fp = _rest_pitch(doc, "far_hand")
    scale = float(doc["svg_source"]["scale"])

    idle = _with_visibility(
        {
            "root_y": _expr("-0.55*sin(tau*t)"),
            "torso": _expr("0.7*sin(tau*t)"),
            "head": _expr("-0.5*sin(tau*t)"),
            "near_hand_x": _expr(f"{nx:.4f} - 0.7*sin(tau*t)"),
            "near_hand_y": _expr(f"{ny:.4f} + 0.5*sin(tau*t)"),
            "near_hand_pitch": _const(np),
            "far_hand_x": _expr(f"{fx:.4f} + 0.5*sin(tau*t)"),
            "far_hand_y": _expr(f"{fy:.4f} - 0.35*sin(tau*t)"),
            "far_hand_pitch": _const(fp),
            # Narrow pulse near the end of the 8-frame loop.
            "blink_vis": {
                "keys": [
                    [0.0, 0.0, "linear"],
                    [0.72, 0.0, "linear"],
                    [0.78, 1.0, "linear"],
                    [0.88, 0.0, "linear"],
                ]
            },
        }
    )

    near_dx = 15.0 * scale
    near_dy = 15.0 * scale
    far_dx = 7.0 * scale
    far_dy = 1.0 * scale
    interact = _with_visibility(
        {
            "root_y": _keys([0.0, 0.5, 0.9, 0.7, 0.3, 0.0]),
            "torso": _keys([0.0, 1.0, 2.2, 1.3, 2.0, 0.0]),
            "head": _keys([0.0, -1.0, -2.1, -1.5, -2.0, 0.0]),
            "near_hand_x": _keys(
                [
                    nx,
                    nx + near_dx * 0.45,
                    nx + near_dx,
                    nx + near_dx * 0.8,
                    nx + near_dx,
                    nx,
                ]
            ),
            "near_hand_y": _keys(
                [
                    ny,
                    ny + near_dy * 0.4,
                    ny + near_dy,
                    ny + near_dy * 0.8,
                    ny + near_dy,
                    ny,
                ]
            ),
            "near_hand_pitch": _keys([np, np + 4, np + 13, np - 7, np + 12, np]),
            "far_hand_x": _keys([fx, fx + far_dx, fx + far_dx, fx + far_dx, fx, fx]),
            "far_hand_y": _keys([fy, fy + far_dy, fy + far_dy, fy, fy, fy]),
            "far_hand_pitch": _const(fp),
        }
    )
    return {
        "idle": {"loop": True, "frames": 8, "duration_ms": 120, "channels": idle},
        "interact": {
            "loop": False,
            "frames": 6,
            "duration_ms": 105,
            "channels": interact,
        },
    }


def _front_clips(doc: dict) -> dict:
    nx = _rest(doc, "near_hand", "x")
    ny = _rest(doc, "near_hand", "y")
    fx = _rest(doc, "far_hand", "x")
    fy = _rest(doc, "far_hand", "y")
    np = _rest_pitch(doc, "near_hand")
    fp = _rest_pitch(doc, "far_hand")
    scale = float(doc["svg_source"]["scale"])

    gesture_x = -18.0 * scale
    gesture_y = -24.0 * scale
    talk = _with_visibility(
        {
            "root_y": _keys([0.0, -0.4, 0.0, -0.5, 0.0, -0.2]),
            "torso": _keys([0.0, -0.5, 0.3, -0.4, 0.2, 0.0]),
            "head": _keys([0.0, 0.8, -0.5, 0.6, -0.4, 0.0]),
            "near_hand_x": _keys(
                [
                    nx,
                    nx + gesture_x * 0.45,
                    nx + gesture_x,
                    nx + gesture_x * 0.75,
                    nx + gesture_x * 0.2,
                    nx,
                ]
            ),
            "near_hand_y": _keys(
                [
                    ny,
                    ny + gesture_y * 0.35,
                    ny + gesture_y,
                    ny + gesture_y * 0.7,
                    ny + gesture_y * 0.15,
                    ny,
                ]
            ),
            "near_hand_pitch": _keys([np, np - 8, np - 16, np - 7, np, np]),
            "far_hand_x": _keys([fx, fx + 1.2, fx + 2.0, fx + 1.0, fx, fx]),
            "far_hand_y": _keys([fy, fy - 0.5, fy - 1.0, fy - 0.5, fy, fy]),
            "far_hand_pitch": _const(fp),
            "talk_vis": _keys([0.0, 1.0, 0.0, 1.0, 0.0, 1.0], ease="linear"),
            "blink_vis": _keys([0.0, 0.0, 0.0, 0.0, 1.0, 0.0], ease="linear"),
        }
    )
    return {"talk": {"loop": True, "frames": 6, "duration_ms": 100, "channels": talk}}


def _side_clips(doc: dict) -> dict:
    nfx = _rest(doc, "near_foot", "x")
    nfp = _rest_pitch(doc, "near_foot")
    ffx = _rest(doc, "far_foot", "x")
    ffp = _rest_pitch(doc, "far_foot")
    nhx = _rest(doc, "near_hand", "x")
    nhy = _rest(doc, "near_hand", "y")
    nhp = _rest_pitch(doc, "near_hand")
    fhx = _rest(doc, "far_hand", "x")
    fhy = _rest(doc, "far_hand", "y")
    fhp = _rest_pitch(doc, "far_hand")

    stride = [10, 7, 3, -2, -10, -8, -3, 4]
    lift = [0, 0, 0, 0, 0, 3, 6, 3]
    far_stride = stride[4:] + stride[:4]
    far_lift = lift[4:] + lift[:4]
    arm = [-5.5, -4.0, -1.5, 2.5, 5.5, 4.0, 1.5, -2.5]
    far_arm = arm[4:] + arm[:4]

    walk = _with_visibility(
        {
            "root_y": _keys([0.0, 1.15, 0.35, -0.55, 0.0, 1.15, 0.35, -0.55]),
            "torso": _keys([0.5, 1.2, 0.4, -0.2, -0.5, -1.2, -0.4, 0.2]),
            "head": _keys([-0.3, -0.7, -0.2, 0.2, 0.3, 0.7, 0.2, -0.2]),
            "near_foot_x": _keys([nfx + v for v in stride], ease="linear"),
            "near_foot_lift": _keys(lift),
            "near_foot_pitch": _keys([nfp + v for v in (6, 2, -2, -5, 0, 3, 9, 11)]),
            "far_foot_x": _keys([ffx + v for v in far_stride], ease="linear"),
            "far_foot_lift": _keys(far_lift),
            "far_foot_pitch": _keys([ffp + v for v in (0, 3, 9, 11, 6, 2, -2, -5)]),
            "near_hand_x": _keys([nhx + v for v in arm]),
            "near_hand_y": _keys(
                [nhy + v for v in (0, 0.5, 1, 0.5, 0, -0.5, -1, -0.5)]
            ),
            "near_hand_pitch": _keys([nhp + v for v in (0, 1, 2, 1, 0, -1, -2, -1)]),
            "far_hand_x": _keys([fhx + v for v in far_arm]),
            "far_hand_y": _keys([fhy + v for v in (0, -0.5, -1, -0.5, 0, 0.5, 1, 0.5)]),
            "far_hand_pitch": _keys([fhp + v for v in (0, -1, -2, -1, 0, 1, 2, 1)]),
            "blink_vis": _keys([0, 0, 0, 0, 0, 0, 1, 0], ease="linear"),
        }
    )
    clips = {"walk": {"loop": True, "frames": 8, "duration_ms": 100, "channels": walk}}
    clips.update(_side_fight_clips(doc))
    return clips


def _arm_envelope(doc: dict, prefix: str) -> tuple:
    """Where this arm hangs from, and how far it can get -- in CHANNEL units.

    IK hand channels are frame offsets from ``(center_x, ground_y)``, and the
    shoulder is a fact of the SVG, so hardcoding either would silently rot the
    moment the drawing moves.  Returns ``(shoulder_x, shoulder_y, reach)``.
    """

    document = RigDocument(doc)
    skeleton = document.build_skeleton()
    frame = doc["frame"]
    cx = float(frame["center_x"])
    gy = float(frame["ground_y"])
    chain = next(
        c for c in doc["ik_chains"] if c.get("channel_prefix") == prefix
    )
    world = skeleton.world({}, root=(cx, gy))
    shoulder = world[chain["upper"]].origin
    reach = skeleton.bones[chain["upper"]].length + skeleton.bones[chain["lower"]].length
    return (shoulder[0] - cx, shoulder[1] - gy, reach)


def _side_fight_clips(doc: dict) -> dict:
    """**The rows Oiler needed before he could fight.**

    His sheet published four: idle, walk, talk, interact.  A platform-fighter
    move names the row it wants and settles for ``attack_side`` -> ``attack`` ->
    ``slash`` -> ``idle``, so every swing in a sixteen-move repertoire drew the
    STANDING POSE -- and cost the gameplay nothing to do it, which is why it
    stayed broken.  These are the rows that table names
    (``game/ambition_content/src/oiler_moveset.rs``).

    Side view, because a platform fighter is a side-on game and it is the
    silhouette his walk already reads in.

    NB the art is contractually propless -- no wrench, no oil can, no satchel --
    so every pose here is MIMED at the hand sockets.  A tool belongs on
    ``sockets.tool_grip`` at runtime, never in the SVG.

    !! **poses are authored as ANGLES on the arm's reachable circle, not as
    (x, y) guesses.**  Oiler's arms are short and already near full extension
    at rest -- a 26.5px reach from a shoulder 25.6px above the hanging wrist --
    so a target picked by eye lands outside the circle, gets clamped by the IK,
    and every "big" swing collapses onto the same 45-degree pose.  The first
    draft of these clips did exactly that and read as a man shrugging.
    """

    sx, sy, reach = _arm_envelope(doc, "near_hand")
    fsx, fsy, freach = _arm_envelope(doc, "far_hand")
    nhp = _rest_pitch(doc, "near_hand")
    fhp = _rest_pitch(doc, "far_hand")
    nfx = _rest(doc, "near_foot", "x")
    ffx = _rest(doc, "far_foot", "x")

    # Forward is +x: the side rig's own geometry check requires the wrist to
    # return forward of the elbow and the elbow to sit behind the shoulder.
    # Angles are measured from straight-forward, positive downward, so the
    # hanging rest pose is +90 and straight overhead is -90.
    REST_DEG = 90.0

    def near(deg: float, frac: float = 0.94) -> tuple:
        rad = math.radians(deg)
        return (sx + reach * frac * math.cos(rad), sy + reach * frac * math.sin(rad))

    def far(deg: float, frac: float = 0.94) -> tuple:
        rad = math.radians(deg)
        return (
            fsx + freach * frac * math.cos(rad),
            fsy + freach * frac * math.sin(rad),
        )

    def pitch(rest: float, deg: float) -> float:
        """Hand pitch that follows the arm, calibrated off its own rest pose."""
        return rest + (deg - REST_DEG)

    def arm(poses, *, side="near"):
        """Expand ``[(deg, frac), ...]`` into the three channels one arm needs."""
        place = near if side == "near" else far
        rest = nhp if side == "near" else fhp
        targets = [place(deg, frac) for deg, frac in poses]
        prefix = "near_hand" if side == "near" else "far_hand"
        return {
            f"{prefix}_x": _shot([t[0] for t in targets]),
            f"{prefix}_y": _shot([t[1] for t in targets]),
            f"{prefix}_pitch": _shot([pitch(rest, deg) for deg, _ in poses]),
        }

    # ---- the swings ------------------------------------------------------
    # A flat wrench swing at chest height: wind back over the shoulder, come
    # through level, follow through low.
    attack_side = _with_visibility(
        {
            "root_x": _shot([0.0, -2.0, 0.0, 2.5, 3.0, 0.5]),
            "torso": _shot([0.0, -7.0, 0.0, 9.0, 8.0, 2.0]),
            "head": _shot([0.0, 4.0, 0.0, -5.0, -4.0, -1.0]),
            **arm(
                [
                    (REST_DEG, 0.90),
                    (152.0, 0.72),
                    (118.0, 0.80),
                    (18.0, 0.98),
                    (2.0, 0.99),
                    (52.0, 0.92),
                ]
            ),
            **arm(
                [
                    (REST_DEG, 0.92),
                    (128.0, 0.78),
                    (110.0, 0.82),
                    (56.0, 0.92),
                    (44.0, 0.94),
                    (78.0, 0.92),
                ],
                side="far",
            ),
            "near_foot_x": _shot([nfx + 2, nfx, nfx + 3, nfx + 8, nfx + 9, nfx + 3]),
            "far_foot_x": _shot([ffx - 1, ffx - 3, ffx - 4, ffx - 6, ffx - 6, ffx - 2]),
        }
    )

    # The gauge needle sweeping: an overhead arc that beats a shorthop.
    attack_up = _with_visibility(
        {
            "root_y": _shot([0.0, 1.5, 0.0, -1.5, -2.0, -0.5]),
            "torso": _shot([0.0, 6.0, -2.0, -10.0, -11.0, -3.0]),
            "head": _shot([0.0, -4.0, 2.0, 8.0, 9.0, 3.0]),
            **arm(
                [
                    (REST_DEG, 0.90),
                    (128.0, 0.70),
                    (28.0, 0.78),
                    (-52.0, 0.96),
                    (-76.0, 0.99),
                    (-24.0, 0.90),
                ]
            ),
            **arm(
                [
                    (REST_DEG, 0.92),
                    (104.0, 0.80),
                    (78.0, 0.84),
                    (36.0, 0.88),
                    (24.0, 0.90),
                    (64.0, 0.90),
                ],
                side="far",
            ),
            "near_foot_x": _shot([nfx, nfx - 1, nfx + 1, nfx + 3, nfx + 3, nfx]),
        }
    )

    # Oil dragged forward at shin height.  He drops onto the trailing leg for
    # it, because the arm alone cannot get anywhere near the floor.
    attack_down = _with_visibility(
        {
            "root_y": _shot([0.0, 1.0, 5.0, 8.5, 9.0, 2.5]),
            "torso": _shot([0.0, -4.0, 5.0, 13.0, 14.0, 4.0]),
            "head": _shot([0.0, 3.0, -4.0, -9.0, -10.0, -3.0]),
            **arm(
                [
                    (REST_DEG, 0.90),
                    (146.0, 0.72),
                    (110.0, 0.84),
                    (46.0, 0.98),
                    (34.0, 0.99),
                    (74.0, 0.92),
                ]
            ),
            **arm(
                [
                    (REST_DEG, 0.92),
                    (124.0, 0.78),
                    (112.0, 0.84),
                    (86.0, 0.90),
                    (80.0, 0.92),
                    (86.0, 0.92),
                ],
                side="far",
            ),
            "near_foot_x": _shot([nfx + 1, nfx, nfx + 5, nfx + 10, nfx + 11, nfx + 3]),
            "far_foot_x": _shot([ffx - 1, ffx - 3, ffx - 6, ffx - 9, ffx - 9, ffx - 3]),
        }
    )

    # THE TORQUE SPEC -- Oiler's one kill move.  Four frames of visible windup,
    # because a heavyweight swing nobody can see coming is not a smash.
    smash_forward = _with_visibility(
        {
            "root_x": _shot([0.0, -2.5, -4.5, -4.5, 0.0, 4.0, 5.0, 1.5]),
            "root_y": _shot([0.0, 1.0, 2.5, 3.0, 1.0, -1.0, -1.5, 0.0]),
            "torso": _shot([0.0, -8.0, -13.0, -14.0, 0.0, 12.0, 15.0, 4.0]),
            "head": _shot([0.0, 5.0, 8.0, 9.0, 0.0, -8.0, -10.0, -3.0]),
            **arm(
                [
                    (REST_DEG, 0.90),
                    (150.0, 0.74),
                    (176.0, 0.86),
                    (182.0, 0.90),
                    (108.0, 0.80),
                    (16.0, 0.99),
                    (4.0, 1.00),
                    (56.0, 0.92),
                ]
            ),
            **arm(
                [
                    (REST_DEG, 0.92),
                    (136.0, 0.80),
                    (158.0, 0.86),
                    (162.0, 0.88),
                    (114.0, 0.82),
                    (52.0, 0.94),
                    (42.0, 0.96),
                    (80.0, 0.92),
                ],
                side="far",
            ),
            "near_foot_x": _shot(
                [nfx, nfx - 3, nfx - 4, nfx - 4, nfx + 2, nfx + 9, nfx + 10, nfx + 3]
            ),
            "far_foot_x": _shot(
                [ffx, ffx - 1, ffx - 2, ffx - 2, ffx - 4, ffx - 7, ffx - 7, ffx - 2]
            ),
        }
    )

    # THE GEYSER, and the pose every special borrows: both hands down to a valve
    # at his feet, brace, and then flung up as the line lets go.
    special = _with_visibility(
        {
            "root_y": _shot([0.0, 2.5, 6.0, 7.0, 3.0, -2.0, -4.0, -2.5]),
            "root_x": _shot([0.0, 0.5, 1.5, 1.5, 0.5, -1.0, -1.5, -1.0]),
            "torso": _shot([0.0, 6.0, 13.0, 15.0, 5.0, -9.0, -16.0, -11.0]),
            "head": _shot([0.0, -4.0, -9.0, -11.0, -3.0, 7.0, 13.0, 9.0]),
            **arm(
                [
                    (REST_DEG, 0.90),
                    (76.0, 0.94),
                    (58.0, 0.99),
                    (52.0, 1.00),
                    (74.0, 0.92),
                    (-16.0, 0.90),
                    (-64.0, 0.99),
                    (-48.0, 0.94),
                ]
            ),
            **arm(
                [
                    (REST_DEG, 0.92),
                    (80.0, 0.94),
                    (64.0, 0.98),
                    (58.0, 0.99),
                    (78.0, 0.92),
                    (-8.0, 0.90),
                    (-56.0, 0.98),
                    (-40.0, 0.94),
                ],
                side="far",
            ),
            "near_foot_x": _shot(
                [nfx, nfx + 2, nfx + 4, nfx + 4, nfx + 2, nfx, nfx - 1, nfx]
            ),
            "far_foot_x": _shot(
                [ffx, ffx - 2, ffx - 4, ffx - 4, ffx - 2, ffx, ffx + 1, ffx]
            ),
        }
    )

    # Struck: snapped back off his heels, and back to stance.
    hit = _with_visibility(
        {
            "root_x": _shot([0.0, -4.5, -3.0, -1.0, 0.0]),
            "root_y": _shot([0.0, -1.5, -0.5, 0.0, 0.0]),
            "torso": _shot([0.0, 13.0, 8.0, 3.0, 0.0]),
            "head": _shot([0.0, -15.0, -10.0, -4.0, 0.0]),
            **arm(
                [
                    (REST_DEG, 0.90),
                    (126.0, 0.72),
                    (112.0, 0.78),
                    (98.0, 0.86),
                    (REST_DEG, 0.90),
                ]
            ),
            **arm(
                [
                    (REST_DEG, 0.92),
                    (134.0, 0.74),
                    (118.0, 0.80),
                    (100.0, 0.88),
                    (REST_DEG, 0.92),
                ],
                side="far",
            ),
            "near_foot_x": _shot([nfx, nfx - 5, nfx - 3, nfx - 1, nfx]),
            "far_foot_x": _shot([ffx, ffx - 3, ffx - 2, ffx - 1, ffx]),
        }
    )
    # !! after `_with_visibility`, which writes both gates as consts.
    hit["blink_vis"] = _shot([0.0, 1.0, 1.0, 0.0, 0.0], ease="linear")

    # Down: he folds backwards over the hip and stays there.  The lean stops at
    # 30 degrees so his head never leaves the logical frame.
    death = _with_visibility(
        {
            "root_x": _shot([0.0, -1.5, -4.0, -6.0, -7.5, -8.0]),
            "root_y": _shot([0.0, -1.0, 3.0, 8.0, 12.0, 14.0]),
            "torso": _shot([0.0, 7.0, 15.0, 23.0, 28.0, 30.0]),
            "head": _shot([0.0, -7.0, -12.0, -16.0, -18.0, -19.0]),
            **arm(
                [
                    (REST_DEG, 0.90),
                    (108.0, 0.84),
                    (126.0, 0.76),
                    (142.0, 0.70),
                    (152.0, 0.66),
                    (156.0, 0.64),
                ]
            ),
            **arm(
                [
                    (REST_DEG, 0.92),
                    (104.0, 0.86),
                    (120.0, 0.78),
                    (136.0, 0.72),
                    (146.0, 0.68),
                    (150.0, 0.66),
                ],
                side="far",
            ),
            "near_foot_x": _shot([nfx, nfx + 2, nfx + 5, nfx + 8, nfx + 10, nfx + 11]),
            "near_foot_lift": _shot([0.0, 0.0, 0.5, 1.5, 2.0, 2.0]),
            "far_foot_x": _shot([ffx, ffx + 1, ffx + 3, ffx + 5, ffx + 6, ffx + 6]),
        },
        blink=1.0,
    )

    # Wipes his hands on the apron, then points at the mess you are about to be.
    taunt = _with_visibility(
        {
            "root_y": _shot([0.0, 0.5, 1.0, 0.5, 0.0, -0.5, -1.0, -0.5]),
            "torso": _shot([0.0, 3.0, 6.0, 3.0, 0.0, -3.0, -6.0, -3.0]),
            "head": _shot([0.0, -2.0, -3.0, -2.0, 0.0, 3.0, 6.0, 3.0]),
            **arm(
                [
                    (REST_DEG, 0.90),
                    (98.0, 0.66),
                    (104.0, 0.58),
                    (98.0, 0.66),
                    (REST_DEG, 0.90),
                    (46.0, 0.86),
                    (6.0, 0.99),
                    (48.0, 0.92),
                ]
            ),
            **arm(
                [
                    (REST_DEG, 0.92),
                    (94.0, 0.68),
                    (100.0, 0.60),
                    (94.0, 0.68),
                    (REST_DEG, 0.92),
                    (96.0, 0.90),
                    (98.0, 0.92),
                    (94.0, 0.92),
                ],
                side="far",
            ),
        }
    )
    taunt["blink_vis"] = _shot(
        [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0], ease="linear"
    )

    def one_shot(frames: int, duration_ms: int, channels: dict) -> dict:
        return {
            "loop": False,
            "frames": frames,
            "duration_ms": duration_ms,
            "channels": channels,
        }

    return {
        "attack_side": one_shot(6, 70, attack_side),
        "attack_up": one_shot(6, 66, attack_up),
        "attack_down": one_shot(6, 70, attack_down),
        "smash_forward": one_shot(8, 64, smash_forward),
        "special": one_shot(8, 72, special),
        "hit": one_shot(5, 80, hit),
        "death": one_shot(6, 90, death),
        "taunt": one_shot(8, 100, taunt),
    }


def seed_clips(view_name: str, doc: dict) -> dict:
    if view_name == "three_quarter":
        return _three_quarter_clips(doc)
    if view_name == "front":
        return _front_clips(doc)
    if view_name == "side":
        return _side_clips(doc)
    raise KeyError(view_name)


def _drop_retired_prop_channels(clips: dict) -> None:
    """Remove visibility channels from the earlier embedded-prop prototype."""

    for clip in clips.values():
        channels = clip.get("channels", {})
        channels.pop("tool_vis", None)
        channels.pop("machine_vis", None)


def build_one(view_name: str, *, fresh: bool) -> Path:
    spec = VIEWS[view_name]
    path = RIG_DIR / f"{spec.name}.rig.json"
    generated = build_humanoid_view_document(SVG, RIG_DIR, spec)
    generated["clips"] = seed_clips(view_name, generated)
    existing = {}
    if path.exists() and not fresh:
        existing = json.loads(path.read_text(encoding="utf8"))
    doc = generated if fresh else merge_generated_geometry(existing, generated)
    _drop_retired_prop_channels(doc.get("clips", {}))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf8")
    print(
        f"wrote {path.relative_to(ROOT)}: {len(doc['bones'])} bones, "
        f"{len(doc['parts'])} SVG parts, clips={list(doc['clips'])}"
    )
    return path


def cmd_build(args) -> None:
    _validate_svg_source()
    for name in VIEWS:
        build_one(name, fresh=args.fresh)


def cmd_validate(args) -> None:
    _validate_svg_source()
    paths = [build_one(name, fresh=args.fresh) for name in VIEWS]
    SCRATCH.mkdir(parents=True, exist_ok=True)
    for path in paths:
        doc = RigDocument.load(path)
        for clip, frames, _duration in doc.rows():
            images = [doc.render_frame(clip, i, frames) for i in range(frames)]
            if any(im.getchannel("A").getbbox() is None for im in images):
                raise RuntimeError(f"{path.name}:{clip} produced an empty frame")
            w = sum(im.width for im in images)
            strip = Image.new("RGBA", (w, images[0].height), (0, 0, 0, 0))
            x = 0
            for image in images:
                strip.alpha_composite(image, (x, 0))
                x += image.width
            out = SCRATCH / f"{path.stem}_{clip}.png"
            strip.save(out)
            print(f"validated {clip}: {out.relative_to(ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    build.add_argument("--fresh", action="store_true")
    build.set_defaults(func=cmd_build)
    validate = sub.add_parser("validate")
    validate.add_argument("--fresh", action="store_true")
    validate.set_defaults(func=cmd_validate)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
