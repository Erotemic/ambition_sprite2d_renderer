"""Contract tests for Oiler's multiview humanoid rig.

The art is drawn by ``scripts/svg_art/oiler_art.py`` (the 2026-10-20 redesign).
These pin what the runtime relies on -- the views, the rig they extract to, the
expression channels and the mirrored rows of an asymmetric character -- not how
the drawing is authored."""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

#  the same guard its sibling SVG suites carry: rendering an SVG rig needs
# native resvg-py; without it these would RAISE rather than skip.
pytest.importorskip("resvg_py")

from ambition_sprite2d_renderer.authoring.humanoid_svg_rig import (
    HumanoidViewSpec,
    build_humanoid_view_document,
)
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
from ambition_sprite2d_renderer.registry import discover_all_targets

ROOT = Path(__file__).resolve().parent.parent
SVG = ROOT / "ambition_sprite2d_renderer/data/characters/oiler/oiler-multiview.svg"
RIG_DIR = ROOT / "ambition_sprite2d_renderer/targets/characters/rigged/oiler"
LABEL = "{http://www.inkscape.org/namespaces/inkscape}label"
VIEWS = ("Oiler - Three Quarter", "Oiler - Front", "Oiler - Side Right", "Oiler - Three Quarter Left", "Oiler - Side Left")
FACES = ("knowing", "pleased", "delighted", "surprised", "thinking", "stern", "worried", "hurt")


def _views():
    root = ET.parse(SVG).getroot()
    return {elem.get(LABEL): elem for elem in root if elem.get(LABEL)}


def test_oiler_svg_extracts_to_a_complete_humanoid_rig(tmp_path):
    data = build_humanoid_view_document(SVG, tmp_path, HumanoidViewSpec(view="Oiler - Side Right", name="test_side"))
    assert len(data["bones"]) == 15
    assert len(data["ik_legs"]) == 2
    assert len(data["ik_chains"]) == 2
    assert {p["bone"] for p in data["parts"]} >= {"torso", "head", "near_arm_u", "near_leg_u", "pelvis"}


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


def test_oiler_has_five_views_and_only_his_left_side_is_stored_to_be_mirrored():
    views = _views()
    assert set(views) == set(VIEWS)
    mirrored = {name for name, layer in views.items() if layer.get("data-view-mirror") == "x"}
    assert mirrored == {"Oiler - Three Quarter Left", "Oiler - Side Left"}
    assert views["Oiler - Front"].get("data-rig-side-map") == "left=far,right=near"


def test_every_view_draws_every_expression_and_shows_knowing_by_default():
    for name, layer in _views().items():
        channels = {e.get("data-rig-opacity"): e.get("data-rig-opacity-default") for e in layer.iter() if e.get("data-rig-opacity")}
        assert set(channels) == {f"face_{face}_vis" for face in FACES} | {"blink_vis", "talk_vis"}, name
        assert [ch for ch, default in channels.items() if default == "1"] == ["face_knowing_vis"], name


def test_a_left_view_takes_its_right_twins_clips():
    for right, left in (("oiler_three_quarter", "oiler_three_quarter_left"), ("oiler_side", "oiler_side_left")):
        r = RigDocument.load(RIG_DIR / f"{right}.rig.json")
        l_doc = RigDocument.load(RIG_DIR / f"{left}.rig.json")
        assert set(l_doc.clips) == set(r.clips)
        assert {b["name"] for b in l_doc.data["bones"]} == {b["name"] for b in r.data["bones"]}


def test_every_row_has_a_mirrored_twin_of_the_same_length():
    from ambition_sprite2d_renderer.targets.characters import oiler

    rows = {name: frames for name, frames, _ms in oiler.ROWS}
    for name, source in oiler.MIRROR_OF.items():
        assert rows[name] == rows[source]
    assert set(oiler.MIRROR_OF.values()) == {name for name, _f, _ms in oiler.BASE_ROWS}


def test_hit_and_death_wear_the_hurt_face():
    doc = RigDocument.load(RIG_DIR / "oiler_side.rig.json")
    for clip in ("hit", "death"):
        assert doc.clips[clip]["channels"]["face_hurt_vis"] == {"const": 1.0}
        assert doc.clips[clip]["channels"]["face_knowing_vis"] == {"const": 0.0}
