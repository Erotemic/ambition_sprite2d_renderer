from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
SVG_PATH = (
    ROOT
    / "ambition_sprite2d_renderer/data/characters/player_robot_v3_svg/player-robot-v3.svg"
)


def _parts():
    root = ET.parse(SVG_PATH).getroot()
    return {
        elem.attrib["data-rig-part"]: elem
        for elem in root.iter()
        if "data-rig-part" in elem.attrib
    }


def _descendant_ids(elem):
    return {child.attrib.get("id") for child in elem.iter() if child.attrib.get("id")}


def test_complete_boot_and_toe_artwork_share_the_foot_bone():
    parts = _parts()

    far_foot_ids = _descendant_ids(parts["far_foot"])
    near_foot_ids = _descendant_ids(parts["near_foot"])
    far_lower_ids = _descendant_ids(parts["far_leg_l"])
    near_lower_ids = _descendant_ids(parts["near_leg_l"])

    assert parts["far_foot"].attrib["data-rig-bone"] == "far_leg_foot"
    assert {"path4617", "path4629"} <= far_foot_ids
    assert "path-far-shin-link" in far_lower_ids
    assert "path4617" not in far_lower_ids

    assert parts["near_foot"].attrib["data-rig-bone"] == "near_leg_foot"
    assert {"path4615", "path4627"} <= near_foot_ids
    assert "path-near-shin-link" in near_lower_ids
    assert "path4615" not in near_lower_ids


def test_lower_leg_parts_only_own_the_articulating_shin_links():
    parts = _parts()
    assert parts["far_leg_l"].attrib["data-rig-bone"] == "far_leg_l"
    assert parts["near_leg_l"].attrib["data-rig-bone"] == "near_leg_l"
    assert "Lower Leg Link" in parts["far_leg_l"].attrib[
        "{http://www.inkscape.org/namespaces/inkscape}label"
    ]
    assert "Lower Leg Link" in parts["near_leg_l"].attrib[
        "{http://www.inkscape.org/namespaces/inkscape}label"
    ]
