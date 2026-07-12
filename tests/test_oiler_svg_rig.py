"""Contract tests for Oiler's direct-SVG multiview humanoid rig."""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from pathlib import Path

from ambition_sprite2d_renderer.authoring.humanoid_svg_rig import (
    HumanoidViewSpec,
    build_humanoid_view_document,
)
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
from ambition_sprite2d_renderer.registry import discover_all_targets
from ambition_sprite2d_renderer.targets.characters import oiler

ROOT = Path(__file__).resolve().parent.parent
SVG = ROOT / "ambition_sprite2d_renderer/data/characters/oiler/oiler-multiview.svg"
RIG_DIR = ROOT / "ambition_sprite2d_renderer/targets/characters/rigged/oiler"
LABEL = "{http://www.inkscape.org/namespaces/inkscape}label"
GROUPMODE = "{http://www.inkscape.org/namespaces/inkscape}groupmode"
ANATOMICAL_TOP_LAYER_NAMES = {
    "Arm - Left",
    "Arm - Right",
    "Leg - Left",
    "Leg - Right",
    "Torso",
    "Head",
    "Joints",
}


def _artist_layer_paths(view: ET.Element) -> set[tuple[str, ...]]:
    """Return human-facing Inkscape layer paths, independent of z-order."""

    paths: set[tuple[str, ...]] = set()

    def walk(parent: ET.Element, prefix: tuple[str, ...]) -> None:
        for child in list(parent):
            if child.get(GROUPMODE) != "layer":
                continue
            label = child.get(LABEL)
            assert label
            path = (*prefix, label)
            paths.add(path)
            walk(child, path)

    walk(view, ())
    return paths


def test_oiler_svg_extracts_to_a_complete_humanoid_rig(tmp_path):
    # One representative view exercises the full label/joint extraction path;
    # the committed front/side documents are validated separately below.
    data = build_humanoid_view_document(
        SVG,
        tmp_path,
        HumanoidViewSpec(view="Oiler - Side Right", name="test_side"),
    )
    assert len(data["bones"]) == 15
    assert len(data["ik_legs"]) == 2
    assert len(data["ik_chains"]) == 2
    assert {p["bone"] for p in data["parts"]} >= {
        "torso",
        "head",
        "near_arm_u",
        "near_leg_u",
    }


def test_generic_arm_ik_places_the_wrist_on_its_world_target():
    doc = RigDocument.load(RIG_DIR / "oiler_front.rig.json")
    chain = next(c for c in doc.ik_chains if c["channel_prefix"] == "near_hand")
    tx = float(chain["rest_x"]) - 4.0
    ty = float(chain["rest_y"]) - 6.0
    doc.clips["ik_probe"] = {
        "loop": False,
        "frames": 1,
        "channels": {
            "near_hand_x": {"const": tx},
            "near_hand_y": {"const": ty},
            "near_hand_pitch": {"const": float(chain["rest_pitch"])},
        },
    }
    world, _ = doc.solve("ik_probe", 0.0)
    wrist = world["near_arm_hand"].origin
    expected = (doc.frame["center_x"] + tx, doc.frame["ground_y"] + ty)
    assert math.dist(wrist, expected) < 0.05


def test_oiler_target_overrides_the_legacy_yaml_generator():
    target = discover_all_targets().targets["oiler"]
    assert target.kind == "module"
    assert target.module_path == "ambition_sprite2d_renderer.targets.characters.oiler"


def test_runtime_animation_samples_render_nonempty_without_edge_clipping():
    for animation, frames, _duration in oiler.ROWS:
        for frame_idx in sorted({0, frames // 2, frames - 1}):
            image = oiler._render_frame(animation, frame_idx, frames)
            bbox = image.getchannel("A").getbbox()
            assert bbox is not None, (animation, frame_idx)
            x1, y1, x2, y2 = bbox
            assert x1 > 0 and y1 > 0
            assert x2 < image.width and y2 < image.height


def test_oiler_svg_is_flat_and_contains_no_embedded_props():
    text = SVG.read_text(encoding="utf8").lower()
    for forbidden in (
        "drop-shadow",
        "dropshadow",
        "<filter",
        "<lineargradient",
        "<radialgradient",
        "url(#",
        "part:machine",
        "part:wrench",
        'data-rig-part="machine"',
        'data-rig-part="wrench"',
        "oil-flask",
        "satchel",
    ):
        assert forbidden not in text


def test_oiler_svg_preserves_the_euler_mechanic_design_contract():
    root = ET.parse(SVG).getroot()
    assert root.get("data-character-design") == "euler-mechanic-v1"

    ids = {elem.get("id") for elem in root.iter() if elem.get("id")}
    required_design_roles = {
        "cap-back-and-tail",
        "cap-crown-and-folds",
        "neckcloth-and-cravat",
        "face-shape-and-ears",
        "lapels-and-upper-coat-trim",
        "apron-details",
        "nose-construction",
    }
    views = [
        elem for elem in root.iter() if (elem.get(LABEL) or "").startswith("Oiler - ")
    ]
    assert len(views) == 3
    for view in views:
        roles = {
            elem.get("data-oiler-role")
            for elem in view.iter()
            if elem.get("data-oiler-role")
        }
        assert required_design_roles <= roles

    assert not any("beard" in elem_id or "moustache" in elem_id for elem_id in ids)

    # The historical coat reference is carried by flat Euler-blue panels and
    # charcoal trim, while the waist apron keeps him legible as a mechanic.
    text = SVG.read_text(encoding="utf8").lower()
    assert text.count('fill="#2f7187"') >= 3
    assert text.count('fill="#28323a"') >= 6
    assert text.count('fill="#e8dfcf"') >= 3


def test_oiler_svg_uses_pca_style_artist_layers_with_separate_rig_metadata():
    root = ET.parse(SVG).getroot()
    assert root.get("data-rig-hierarchy") == "pca-style-v1"

    machine_labels = [
        elem.get(LABEL, "")
        for elem in root.iter()
        if elem.get(LABEL, "").startswith(("part:", "joint:"))
    ]
    assert machine_labels == []

    views = [
        elem for elem in root.iter() if (elem.get(LABEL) or "").startswith("Oiler - ")
    ]
    assert len(views) == 3
    for view in views:
        layers = [
            child
            for child in list(view)
            if isinstance(child.tag, str) and child.tag.endswith("}g")
        ]
        assert {layer.get(LABEL) for layer in layers} == ANATOMICAL_TOP_LAYER_NAMES
        assert all(layer.get(GROUPMODE) == "layer" for layer in layers)

        parts = [elem for elem in view.iter() if elem.get("data-rig-part")]
        assert len(parts) in {17, 18}
        assert len({elem.get("data-rig-part") for elem in parts}) == len(parts)
        assert all(elem.get("data-rig-bone") for elem in parts)
        assert all(elem.get("data-rig-z") is not None for elem in parts)
        assert all(elem.get(GROUPMODE) == "layer" for elem in parts)

        joints = [elem for elem in view.iter() if elem.get("data-rig-joint")]
        assert len(joints) == 18
        assert len({elem.get("data-rig-joint") for elem in joints}) == 18

        head = next(layer for layer in layers if layer.get(LABEL) == "Head")
        head_labels = {elem.get(LABEL) for elem in head.iter()}
        assert {
            "Head Base",
            "Cloth Cap - Back and Tail",
            "Face Shape and Ears",
            "Cloth Cap - Crown and Folds",
            "Hair",
            "Facial Features and Age Lines",
        } <= head_labels


def test_oiler_views_share_one_anatomical_artist_layer_vocabulary():
    root = ET.parse(SVG).getroot()
    assert root.get("data-authoring-layer-vocabulary") == (
        "anatomical-left-right-v1"
    )

    views = [
        elem for elem in root.iter() if (elem.get(LABEL) or "").startswith("Oiler - ")
    ]
    assert len(views) == 3

    reference_paths = _artist_layer_paths(views[0])
    for view in views:
        labels = {path[-1] for path in _artist_layer_paths(view)}
        assert not any("Near" in label or "Far" in label for label in labels)
        assert _artist_layer_paths(view) == reference_paths

    assert {
        ("Arm - Left", "Upper Arm - Left"),
        ("Arm - Right", "Upper Arm - Right"),
        ("Leg - Left", "Upper Leg - Left"),
        ("Leg - Right", "Upper Leg - Right"),
        ("Torso", "Coat and Torso", "Coat Buttons"),
        ("Head", "Head Base", "Hair"),
        ("Head", "Talk Mouth"),
        ("Joints", "Arm Joints - Left"),
        ("Joints", "Arm Joints - Right"),
    } <= reference_paths


def test_human_readable_labels_do_not_change_extracted_part_names(tmp_path):
    data = build_humanoid_view_document(
        SVG,
        tmp_path,
        HumanoidViewSpec(view="Oiler - Front", name="metadata_probe"),
    )
    names = {part["name"] for part in data["parts"]}
    assert {"pelvis_yoke", "torso", "head", "near_hand", "far_leg_foot"} <= names


def test_oiler_front_source_uses_character_relative_left_and_right():
    root = ET.parse(SVG).getroot()
    front = next(elem for elem in root.iter() if elem.get(LABEL) == "Oiler - Front")
    assert front.get("data-rig-side-map") == "left=far,right=near"

    labels = [elem.get(LABEL, "") for elem in front.iter()]
    assert "Arm - Left" in labels
    assert "Arm - Right" in labels
    assert "Leg - Left" in labels
    assert "Leg - Right" in labels

    source_names = [
        *(elem.get("data-rig-part", "") for elem in front.iter()),
        *(elem.get("data-rig-bone", "") for elem in front.iter()),
        *(elem.get("data-rig-joint", "") for elem in front.iter()),
    ]
    assert not any("near" in name or "far" in name for name in source_names)
    assert {"left_arm_u", "right_arm_u", "left_hip", "right_hip"} <= set(source_names)


def test_oiler_front_is_independently_authored_around_a_frontal_axis():
    root = ET.parse(SVG).getroot()
    front = next(elem for elem in root.iter() if elem.get(LABEL) == "Oiler - Front")
    assert front.get("data-view-construction") == "authored-front-v3"
    assert front.get("data-front-hip-layout") == "pelvis-sockets-v3"
    assert front.get("data-front-face-volume") == "full-volume-v3"
    axis_x = float(front.get("data-front-axis-x"))

    ids = {elem.get("id") for elem in front.iter() if elem.get("id")}
    assert {
        "front-nose-bridge",
        "front-cheek-left",
        "front-cheek-right",
        "front-cap-center-pleat",
        "front-coat-center-seam",
        "front-coat-button-upper",
        "front-coat-button-lower",
    } <= ids

    joints = {
        elem.get("data-rig-joint"): (float(elem.get("cx")), float(elem.get("cy")))
        for elem in front.iter()
        if elem.get("data-rig-joint")
    }
    assert joints["waist"][0] == axis_x
    assert joints["neck"][0] == axis_x
    for right_name, left_name in (
        ("right_shoulder", "left_shoulder"),
        ("right_hip", "left_hip"),
        ("right_knee", "left_knee"),
        ("right_ankle", "left_ankle"),
    ):
        right_x = joints[right_name][0]
        left_x = joints[left_name][0]
        assert right_x < axis_x < left_x, (left_name, right_name)
        assert left_x - right_x >= 18.0, (left_name, right_name)

    hip_depth = (joints["right_hip"][1] + joints["left_hip"][1]) / 2.0 - joints[
        "waist"
    ][1]
    hip_span = joints["left_hip"][0] - joints["right_hip"][0]
    assert 21.0 <= hip_depth <= 27.0
    assert 32.0 <= hip_span <= 40.0


def test_oiler_hips_are_inside_an_explicit_pelvis_yoke():
    root = ET.parse(SVG).getroot()
    views = {
        elem.get(LABEL): elem
        for elem in root.iter()
        if (elem.get(LABEL) or "").startswith("Oiler - ")
    }
    assert set(views) == {
        "Oiler - Front",
        "Oiler - Side Right",
        "Oiler - Three Quarter",
    }

    for view_name, view in views.items():
        parts = {
            elem.get("data-rig-part"): elem
            for elem in view.iter()
            if elem.get("data-rig-part")
        }
        assert parts["pelvis_yoke"].get("data-rig-bone") == "pelvis"

        joints = {
            elem.get("data-rig-joint"): (float(elem.get("cx")), float(elem.get("cy")))
            for elem in view.iter()
            if elem.get("data-rig-joint")
        }
        waist = joints["waist"]
        if view_name == "Oiler - Front":
            assert parts["right_leg_u"].get("data-rig-bone") == "right_leg_u"
            first_hip = joints["right_hip"]
            second_hip = joints["left_hip"]
        else:
            assert parts["near_leg_u"].get("data-rig-bone") == "near_leg_u"
            first_hip = joints["near_hip"]
            second_hip = joints["far_hip"]
        hip_mid = (
            (first_hip[0] + second_hip[0]) / 2.0,
            (first_hip[1] + second_hip[1]) / 2.0,
        )

        # The frontal pelvis deliberately uses lower, wider sockets than the
        # perspective views. This is the anatomical correction that motivated
        # the polish pass; it must not be normalized back into the torso.
        if view_name == "Oiler - Front":
            assert 21.0 <= hip_mid[1] - waist[1] <= 27.0
            assert 32.0 <= math.dist(first_hip, second_hip) <= 40.0
        else:
            # Perspective views deliberately vary apparent depth and socket
            # spacing to communicate foreshortening. Preserve only the useful
            # anatomical invariant: the two sockets remain below the waist and
            # distinct instead of collapsing into one center point.
            assert 12.0 <= hip_mid[1] - waist[1] <= 32.0, view_name
            assert math.dist(first_hip, second_hip) >= 6.0, view_name
        assert abs(hip_mid[0] - waist[0]) <= 4.0, view_name


def test_oiler_side_profile_is_authored_as_a_profile_not_a_flattened_front():
    """The facing-right source keeps profile anatomy and clothing readable."""

    root = ET.parse(SVG).getroot()
    side = next(elem for elem in root.iter() if elem.get(LABEL) == "Oiler - Side Right")
    assert side.get("data-side-profile-construction") == "authored-profile-v3"
    assert side.get("data-side-arm-hinge") == (
        "shoulder-back-elbow-back-wrist-forward-v3"
    )
    assert side.get("data-side-pouch-construction") == (
        "narrow-profile-gusset-v2"
    )
    assert side.get("data-side-lapel-construction") == "single-profile-lapel-v2"
    assert side.get("data-side-face-construction") == (
        "integrated-profile-features-v3"
    )

    ids = {elem.get("id"): elem for elem in side.iter() if elem.get("id")}
    assert {
        "side-ear",
        "side-ear-inner",
        "side-philtrum",
        "side-mouth-closed",
        "side-lower-lip",
        "side-lapel-edge",
        "side-apron-pocket-flap",
        "side-apron-pocket-gusset",
        "side-apron-belt-loop",
    } <= ids.keys()
    assert ids["side-ear"].get("stroke") == "#17120e"
    assert ids["side-mouth-closed"].get("fill") == "#7a4039"
    assert 1.4 <= float(ids["side-mouth-closed"].get("stroke-width")) <= 2.0
    assert ids["side-apron-pocket-flap"].get("fill") != "none"

    joints = {
        elem.get("data-rig-joint"): (float(elem.get("cx")), float(elem.get("cy")))
        for elem in side.iter()
        if elem.get("data-rig-joint")
    }
    # Oiler faces screen-right. Relaxed elbows sit behind their shoulders, while
    # each wrist returns forward from the elbow rather than reverse-hinging.
    for side_name in ("far", "near"):
        shoulder = joints[f"{side_name}_shoulder"]
        elbow = joints[f"{side_name}_elbow"]
        wrist = joints[f"{side_name}_wrist"]
        # Facing screen-right: the shoulder sits back on the ribcage, the elbow
        # falls behind it, and the wrist returns forward.  Keep the bend modest
        # rather than letting the arm become a reverse-hinged zig-zag.
        assert 6.0 <= shoulder[0] - elbow[0] <= 12.0
        assert 9.0 <= wrist[0] - elbow[0] <= 14.0
        assert shoulder[1] < elbow[1] < wrist[1]


def test_oiler_uses_one_nose_design_across_all_views():
    """Front, three-quarter, and profile are projections of one nose."""

    root = ET.parse(SVG).getroot()
    assert root.get("data-nose-design") == "euler-straight-bridge-projections-v2"

    views = [
        elem for elem in root.iter() if (elem.get(LABEL) or "").startswith("Oiler - ")
    ]
    assert len(views) == 3
    expected_projections = {
        "Oiler - Three Quarter": "three-quarter-left",
        "Oiler - Front": "front",
        "Oiler - Side Right": "profile-right",
    }
    for view in views:
        nose_layers = [
            elem for elem in view.iter() if elem.get(LABEL) == "Nose"
        ]
        assert len(nose_layers) == 1
        nose = nose_layers[0]
        assert nose.get("data-oiler-role") == "nose-construction"
        assert nose.get("data-nose-form") == "straight-bridge-soft-tip"
        assert nose.get("data-nose-projection") == expected_projections[view.get(LABEL)]

    ids = {elem.get("id") for elem in root.iter() if elem.get("id")}
    assert {
        "tq-nose-bridge",
        "tq-nostril",
        "front-nose-bridge",
        "front-nostril-left",
        "front-nostril-right",
        "side-nostril",
    } <= ids
    assert {
        "side-nose",
        "side-nose-crease",
        "front-face-centerline",
        "front-nose-base",
        "tq-nose-base",
    }.isdisjoint(ids)
