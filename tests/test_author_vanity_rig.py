from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
from ambition_sprite2d_renderer.targets.characters import rigged as rigged_targets

ROOT = Path(__file__).resolve().parents[1]
SVG = ROOT / "assets/author-rig-labels-joints.svg"
RIG = ROOT / "assets/rigs/author_vanity/author_vanity.rig.json"
INK_LABEL = "{http://www.inkscape.org/namespaces/inkscape}label"


def test_author_vanity_asset_stays_outside_game_registry():
    assert RIG.exists()
    assert "targets/characters/rigged" not in RIG.as_posix()
    data = json.loads(RIG.read_text(encoding="utf8"))
    assert data["name"] == "author_vanity"
    assert data["features"]["registered_game_target"] is False
    assert "author_vanity" not in rigged_targets.TARGETS
    assert set(data["clips"]) == {
        "vanity_idle",
        "vanity_wave",
        "vanity_receive",
    }


def test_author_vanity_svg_contract():
    root = ET.fromstring(SVG.read_bytes())
    view = next(elem for elem in root.iter() if elem.get(INK_LABEL) == "Author - Side West")
    parts = [elem for elem in view.iter() if elem.get("data-rig-part")]
    joints = [elem for elem in view.iter() if elem.get("data-rig-joint")]
    assert len(parts) == 20
    assert len({elem.get("data-rig-part") for elem in parts}) == 20
    assert len(joints) == 18
    assert len({elem.get("data-rig-joint") for elem in joints}) == 18
    assert all(elem.get("id") for elem in view.iter() if elem.tag.rsplit("}", 1)[-1] in {"path", "polygon", "rect", "ellipse", "circle", "line", "image"})


def test_author_vanity_rig_loads_and_solves():
    doc = RigDocument.load(RIG)
    assert len(doc.bones) == 15
    assert len(doc.parts) == 20
    for clip in doc.clips:
        world, params = doc.solve(clip, 0.5)
        assert "pelvis" in world
        assert params
