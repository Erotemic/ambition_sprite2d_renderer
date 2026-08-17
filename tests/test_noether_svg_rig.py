from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from ambition_sprite2d_renderer.authoring.fighter_motion_catalog import (
    applicable_categories,
    validate_motion_coverage,
)
from ambition_sprite2d_renderer.authoring.humanoid_svg_rig import (
    _collect_joint_ids,
    _collect_parts,
    _drawable_ids_in_view,
)
from ambition_sprite2d_renderer.targets.characters.noether_motion import (
    APPLICABLE_MOTION_SCOPES,
    FIGHTER_MOTION_COVERAGE,
    NOETHER_ROWS,
)
from scripts.build_scientist_fighter_rigs import SPECS, _noether_clips, _validate_view_facing

ROOT = Path(__file__).resolve().parent.parent
SVG = ROOT / "assets" / "noether.svg"
VIEW = "Noether - Side Left"


def _root() -> ET.Element:
    return ET.fromstring(SVG.read_bytes())


def test_noether_view_metadata_is_the_only_required_per_view_metadata():
    root = _root()
    ink = "{http://www.inkscape.org/namespaces/inkscape}label"
    view = next(elem for elem in root.iter() if elem.get(ink) == VIEW)
    assert view.get("data-rig-facing") == "east"
    assert view.get("data-rig-projection") == "three-quarter"
    assert view.get("data-rig-side-map") == "right=near,left=far"
    assert view.get("data-rig-pose-authority") == "geometry-only"
    assert view.get("data-rig-part-order") == "document"


def test_every_scientist_view_declares_the_facing_its_art_is_drawn_in():
    """Each character's SVG says which way the body in its view points.

    Every one of these views is named "… - Side Left", which names the VIEW and
    not the body: Noether's is drawn facing east while the Patent Clerk's and
    Carl Stargan's face west. The declaration is what the sheet manifest
    publishes and the renderer's sprite flip consults — the Patent Clerk faced
    backwards in game for exactly as long as nothing read it — so a regen that
    dropped the attribute has to fail here rather than in a screenshot.
    """
    facings = {name: spec.facing for name, spec in SPECS.items()}
    assert facings == {
        "patent_clerk": "west",
        "carl_stargan": "west",
        "noether": "east",
    }
    for spec in SPECS.values():
        # Raises when the SVG and the spec disagree, or the attribute is gone.
        _validate_view_facing(spec)


def test_noether_standard_labels_cover_every_drawable_without_generated_id_semantics():
    root = _root()
    parts = _collect_parts(root, VIEW, binding_mode="standard-humanoid")
    drawables = set(
        _drawable_ids_in_view(root, VIEW, binding_mode="standard-humanoid")
    )
    owners: dict[str, list[str]] = {}
    for part in parts:
        for drawable in part.include:
            owners.setdefault(drawable, []).append(part.name)

    assert drawables == set(owners)
    assert not {drawable: names for drawable, names in owners.items() if len(names) != 1}
    assert {part.name for part in parts} >= {
        "near_arm_u",
        "near_arm_l",
        "near_hand",
        "far_arm_u",
        "far_arm_l",
        "far_hand",
        "near_leg_u",
        "near_leg_l",
        "near_foot",
        "far_leg_u",
        "far_leg_l",
        "far_foot",
        "pelvis",
        "neck",
        "dress_back",
        "near_skirt",
        "center_skirt",
        "far_skirt",
    }


def test_noether_standard_joint_labels_include_tips_and_skirt_pivots():
    joints = _collect_joint_ids(_root(), VIEW, binding_mode="standard-humanoid")
    assert set(joints) >= {
        "neck",
        "waist",
        "near_shoulder",
        "near_elbow",
        "near_wrist",
        "near_handtip",
        "near_hip",
        "near_knee",
        "near_ankle",
        "near_toe",
        "far_shoulder",
        "far_elbow",
        "far_wrist",
        "far_handtip",
        "far_hip",
        "far_knee",
        "far_ankle",
        "far_toe",
        "near_skirt_pivot",
        "center_skirt_pivot",
        "far_skirt_pivot",
    }


def test_noether_full_fighter_coverage_is_complete():
    rows = {name for name, _frames, _duration in NOETHER_ROWS}
    validate_motion_coverage(
        row_names=rows,
        coverage=FIGHTER_MOTION_COVERAGE,
        scopes=APPLICABLE_MOTION_SCOPES,
        character="noether",
    )
    assert len(applicable_categories(APPLICABLE_MOTION_SCOPES)) == 124
    assert len(FIGHTER_MOTION_COVERAGE) == 124


def test_noether_spec_keeps_pose_authority_out_of_svg_and_has_skirt_bones():
    spec = SPECS["noether"]
    assert spec.label_binding_mode == "standard-humanoid"
    assert spec.facing == "east"
    assert spec.natural_arm_pose is not None
    assert all(
        hint.target[0] > hint.joint[0]
        for hint in spec.natural_arm_pose.values()
    )
    assert {bone.name for bone in spec.auxiliary_bones} == {
        "near_skirt",
        "center_skirt",
        "far_skirt",
    }


def test_noether_east_facing_generator_strike_reaches_forward_and_skirt_is_driven():
    spec = SPECS["noether"]
    # The clip authoring only needs IK rest metadata for this unit-level check;
    # geometry-dependent discontinuity repair is deliberately skipped when no
    # frame/bones are present.
    doc = {
        "ik_legs": [
            {
                "channel_prefix": "near_foot",
                "rest_x": 10.0,
                "rest_lift": 0.0,
                "rest_pitch": 0.0,
                "bend": 1.0,
            },
            {
                "channel_prefix": "far_foot",
                "rest_x": -10.0,
                "rest_lift": 0.0,
                "rest_pitch": 0.0,
                "bend": 1.0,
            },
        ],
        "ik_chains": [
            {
                "channel_prefix": "near_hand",
                "rest_x": 5.0,
                "rest_y": -98.0,
                "rest_pitch": 0.0,
                "bend": -1.0,
            },
            {
                "channel_prefix": "far_hand",
                "rest_x": 35.0,
                "rest_y": -104.0,
                "rest_pitch": 0.0,
                "bend": -1.0,
            },
        ],
    }
    clips = _noether_clips(spec, doc)
    strike = clips["generator_strike"]["channels"]["near_hand_x"]["keys"]
    values = [float(key[1]) for key in strike]
    assert max(values) > values[0] + 40.0
    assert "near_skirt" in clips["generator_strike"]["channels"]
    assert "center_skirt" in clips["generator_strike"]["channels"]
    assert "far_skirt" in clips["generator_strike"]["channels"]
