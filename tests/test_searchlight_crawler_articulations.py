"""Check independent part actions while the crawler walks on surfaces."""
from __future__ import annotations

import math
from pathlib import Path
from xml.etree import ElementTree

import pytest

from ambition_sprite2d_renderer.authoring.articulation_layers import (
    Articulation, PoseComposer,
)
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
from ambition_sprite2d_renderer.authoring.surface_gait import (
    Gait, Leg, SurfaceContact, SurfacePose,
)

RIG_PATH = (
    Path(__file__).resolve().parents[1]
    / "ambition_sprite2d_renderer/targets/characters/rigged/searchlight_crawler/"
    "searchlight_crawler.rig.json"
)


def rig():
    doc = RigDocument.load(RIG_PATH)
    return doc, PoseComposer(doc)


def actions(t):
    return (
        Articulation("aim", "aim_scan", t),
        Articulation("beam", "beam_focus", t),
        Articulation("iris", "iris_blink", t),
        Articulation("alarm", "alarm_flash", t),
        Articulation("vent", "vent_cycle", t),
        Articulation("chassis", "chassis_brace", t),
    )


def gait_data(doc):
    spec = doc.data["footfall"]
    gait = Gait(**{k: spec[k] for k in ("stride", "stance", "lift")})
    legs = {
        name: Leg(name, tuple(values["rest_tip"]), values["tarsus_length"],
                  values["tarsus_pitch"], values["phase"])
        for name, values in spec["legs"].items()
    }
    return gait, legs


def test_every_action_clip_owns_only_its_slot():
    doc, composer = rig()
    for t in (0.0, 0.17, 0.46, 0.75):
        result = composer.sample("walk", t, actions(t))
        assert all(key in result for key in doc.sample("walk", t))
        assert result["focus_visible"] >= 0
        assert result["beam_visible"] == 0
    for slot, clip in (("aim", "aim_scan"), ("beam", "beam_focus"),
                       ("iris", "iris_close"), ("alarm", "alarm_flash"),
                       ("vent", "vent_cycle"), ("chassis", "chassis_brace")):
        assert set(doc.clips[clip]["channels"]) <= composer.slots[slot]


def test_actions_are_order_independent_and_do_not_change_gait_channels():
    doc, composer = rig()
    t = 0.23
    base = doc.sample("walk", t)
    forward = composer.sample("walk", t, actions(t))
    reverse = composer.sample("walk", t, tuple(reversed(actions(t))))
    assert forward == reverse
    assert all(forward[key] == value for key, value in base.items()
               if key in composer.contact_channels)
    assert doc.sample("walk", t) == base


def test_blend_and_direct_aim_do_not_overwrite_other_part_channels():
    doc, composer = rig()
    phase = 0.41
    scan = doc.sample("aim_scan", phase)["light"]
    half = composer.sample("walk", phase, (
        Articulation("aim", "aim_scan", phase, weight=0.5),
        Articulation("beam", "beam_search"),
        Articulation("iris", values={"bone.shutter_upper.y": 3.0}),
    ))
    assert half["light"] == pytest.approx(scan/2.0)
    assert half["beam_visible"] > 0
    assert half["bone.shutter_upper.y"] == 3.0
    direct = composer.sample("walk", phase, (
        Articulation("aim", values={"light": -32.0, "bone.light.x": 4.0}),
    ))
    assert direct["light"] == -32.0
    assert direct["bone.light.x"] == 4.0
    assert "beam_visible" in direct
    assert doc.sample("walk", phase)["beam_visible"] == direct["beam_visible"]


@pytest.mark.parametrize("wrong", [
    (Articulation("aim", values={"near_front_outer_contact_x": 3.0}),),
    (Articulation("aim", "alarm_flash"),),
    (Articulation("nobody", values={"light": 5.0}),),
    (Articulation("beam", "missing_clip"),),
    (Articulation("aim", weight=1.1),),
    (Articulation("aim"), Articulation("aim")),
])
def test_invalid_action_ownership_is_rejected(wrong):
    _, composer = rig()
    with pytest.raises(ValueError):
        composer.sample("walk", 0.25, wrong)


def test_contacts_reject_non_foot_channels():
    _, composer = rig()
    with pytest.raises(ValueError):
        composer.sample("walk", 0.22, contacts={"light": 6.0})


def test_sampled_channel_solve_matches_standard_solve():
    doc, _ = rig()
    for clip in ("walk", "scan", "hit"):
        sample = doc.sample(clip, 0.31)
        old, params = doc.solve(clip, 0.31)
        new, merged = doc.solve(clip, 0.31, sampled_channels=sample)
        assert params == merged
        for bone in old:
            assert new[bone].origin == pytest.approx(old[bone].origin)
            assert new[bone].angle == pytest.approx(old[bone].angle)


def test_independent_parts_actually_move_on_separate_bones():
    doc, composer = rig()
    before, _ = composer.solve("walk", 0.0)
    active, params = composer.solve("walk", 0.25, actions(0.25))
    assert active["light"].angle != pytest.approx(before["light"].angle)
    assert active["antenna"].angle != pytest.approx(before["antenna"].angle)
    assert active["exhaust_hatch"].angle != pytest.approx(before["exhaust_hatch"].angle)
    assert active["shutter_upper"].origin != pytest.approx(before["shutter_upper"].origin)
    assert active["shutter_lower"].origin != pytest.approx(before["shutter_lower"].origin)
    assert params["beacon_visible"] > 0
    assert params["focus_visible"] > 0
    assert params["exhaust_visible"] > 0


@pytest.mark.parametrize("angle", [0.0, 0.19, -0.23, -math.pi/2, math.pi])
def test_support_feet_stay_planted_with_all_actions(angle):
    doc, composer = rig()
    gait, legs = gait_data(doc)
    c, s = math.cos(angle), math.sin(angle)
    travel = (c, s)
    down = (-s, c)
    speed = gait.stride / gait.stance

    def frame_at(t):
        return SurfacePose((speed*t*c, speed*t*s), travel)

    def probe(guess, _direction):
        # Project each query onto one contact plane through the origin.
        forward = guess[0]*c + guess[1]*s
        return SurfaceContact((forward*c, forward*s), (-down[0], -down[1]))

    for i in range(26):
        t = i / 26
        contact_channels = gait.contact_channels(t, legs, frame_at, probe)
        world, values = composer.solve("walk", t, actions(t), contacts=contact_channels)
        assert values["focus_visible"] > 0
        for leg in legs.values():
            if gait.phase_at(t, leg.phase) >= gait.stance:
                continue
            started = math.floor(t+leg.phase)-leg.phase
            pose = frame_at(started)
            guess = pose.world((leg.rest_tip[0]+gait.stride/2, leg.rest_tip[1]))
            target = probe(guess, pose.down).point
            toe = world[f"{leg.name}_tarsus"].tip
            current = frame_at(t).world((toe[0]-doc.frame["center_x"],
                                         toe[1]-doc.frame["ground_y"]))
            assert current == pytest.approx(target, abs=2e-4)


def test_svg_owns_every_articulation_part_and_bone():
    doc, _ = rig()
    svg = doc.source_path.parent / doc.svg_source["path"]
    root = ElementTree.parse(svg).getroot()
    source_ids = {node.get("id") for node in root.iter() if node.get("id")}
    bones = {item["name"] for item in doc.bones}
    for part in doc.parts:
        assert part["bone"] in bones
        assert set(part.get("include", ())) <= source_ids
    for name in ("shutter_upper", "shutter_lower", "antenna", "light", "exhaust_hatch"):
        assert name in bones
    for group in ("part-shutter-upper", "part-shutter-lower", "part-beacon-halo",
                  "part-exhaust-hatch", "part-search-cone-narrow"):
        assert group in source_ids


def test_composed_articulations_render_real_svg():
    doc, composer = rig()
    composed = composer.solve("walk", 0.23, actions(0.23))
    image = doc.render_at("walk", 0.23, solved=composed, supersample=2)
    assert image.getbbox() is not None
    assert image.getbbox()[0] > 0
    assert image.getbbox()[2] < image.width
