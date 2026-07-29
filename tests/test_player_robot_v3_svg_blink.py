from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
SVG_PATH = (
    ROOT
    / "ambition_sprite2d_renderer/data/characters/player_robot_v3_svg/player-robot-v3.svg"
)
RIG_PATH = (
    ROOT
    / "ambition_sprite2d_renderer/targets/characters/rigged/player_robot_v3/player_robot_v3.rig.json"
)
BUILD_SCRIPT = ROOT / "scripts/build_player_robot_v3_svg.py"


def _load_builder():
    spec = importlib.util.spec_from_file_location("build_player_robot_v3_svg", BUILD_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_player_robot_v3_svg_has_explicit_open_and_blink_faces():
    root = ET.parse(SVG_PATH).getroot()
    parts = {
        elem.attrib.get("data-rig-part"): elem
        for elem in root.iter()
        if elem.attrib.get("data-rig-part")
    }

    assert parts["face_open"].attrib["data-rig-bone"] == "head"
    assert parts["face_open"].attrib["data-rig-opacity"] == "face_open_vis"
    assert parts["face_blink"].attrib["data-rig-bone"] == "head"
    assert parts["face_blink"].attrib["data-rig-opacity"] == "blink_vis"

    labels = {
        elem.attrib.get("{http://www.inkscape.org/namespaces/inkscape}label")
        for elem in parts["face_blink"].iter()
    }
    assert "visor-blink" in labels
    assert "right-eye-blink" in labels
    assert "left-eye-blink" in labels


def test_idle_clip_swaps_open_and_blink_face_states():
    builder = _load_builder()
    doc = json.loads(RIG_PATH.read_text(encoding="utf8"))
    clips = builder.make_clips(doc)
    idle = clips["idle"]

    open_values = [key[1] for key in idle["channels"]["face_open_vis"]["keys"]]
    blink_values = [key[1] for key in idle["channels"]["blink_vis"]["keys"]]

    # Looping channels repeat their first value at t=1.0.
    assert len(open_values) == idle["frames"] + 1
    assert len(blink_values) == idle["frames"] + 1
    assert open_values[-1] == open_values[0]
    assert blink_values[-1] == blink_values[0]
    assert sum(blink_values[:-1]) == 1.0
    assert all(
        open_value + blink_value == 1.0
        for open_value, blink_value in zip(open_values, blink_values)
    )
