"""Check crawler foot contacts and the shared surface gait solver."""
from __future__ import annotations

import math
from pathlib import Path

import pytest

from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
from ambition_sprite2d_renderer.authoring.surface_gait import (
    ContactCache, Gait, Leg, SurfaceContact, SurfacePose,
)

RIG_PATH = (
    Path(__file__).resolve().parents[1]
    / "ambition_sprite2d_renderer/targets/characters/rigged/searchlight_crawler/"
    "searchlight_crawler.rig.json"
)


def setup():
    doc = RigDocument.load(RIG_PATH)
    spec = doc.data["footfall"]
    gait = Gait(**{key: spec[key] for key in ("stride", "stance", "lift")})
    legs = {
        name: Leg(name=name, rest_tip=tuple(values["rest_tip"]),
                  tarsus_length=values["tarsus_length"],
                  tarsus_pitch=values["tarsus_pitch"], phase=values["phase"])
        for name, values in spec["legs"].items()
    }
    return doc, gait, legs


def footprint(doc, world, name, surface_pose):
    tip = world[f"{name}_tarsus"].tip
    return surface_pose.world((tip[0] - doc.frame["center_x"],
                               tip[1] - doc.frame["ground_y"]))


def surfaces(speed):
    angle = 0.18
    length = math.hypot(1.0, angle)
    return {
        "floor": (
            lambda t: SurfacePose((speed*t, 0.0), (1.0, 0.0)),
            lambda guess, down: SurfaceContact((guess[0], 0.0), (0.0, -1.0)),
        ),
        "ramp": (
            lambda t: SurfacePose(
                (speed*t/length, angle*speed*t/length),
                (1.0/length, angle/length)),
            lambda guess, down: SurfaceContact(
                (guess[0], angle*guess[0]), (angle/length, -1.0/length)),
        ),
        "wall": (
            lambda t: SurfacePose((0.0, -speed*t), (0.0, -1.0)),
            lambda guess, down: SurfaceContact((0.0, guess[1]), (-1.0, 0.0)),
        ),
        "ceiling": (
            lambda t: SurfacePose((-speed*t, 0.0), (-1.0, 0.0)),
            lambda guess, down: SurfaceContact((guess[0], 0.0), (0.0, 1.0)),
        ),
        "rough": (
            lambda t: SurfacePose((speed*t, 3.0*math.sin(speed*t/65.0)),
                                  (1.0, 0.0)),
            lambda guess, down: SurfaceContact(
                (guess[0], 3.0*math.sin(guess[0]/65.0)), (0.0, -1.0)),
        ),
    }


def test_anatomy_has_ik_links_and_fixed_body():
    doc, gait, legs = setup()
    assert len(legs) == len(doc.ik_chains)
    sk = doc.build_skeleton()
    for chain in doc.ik_chains:
        upper = sk.bones[chain["upper"]]
        lower = sk.bones[chain["lower"]]
        assert upper.length > 0 and lower.length > 0
        assert upper.parent.endswith("_coxa")
        assert lower.parent == upper.name
        assert sk.bones[chain["end"]].parent == lower.name
    positions = [doc.solve("walk", t / 32)[0]["body"].origin for t in range(32)]
    assert max(math.dist(positions[0], p) for p in positions) == 0


def test_baked_clip_matches_footfall_trajectories():
    doc, gait, legs = setup()
    for step in range(81):
        t = step / 80
        world, params = doc.solve("walk", t)
        for leg in legs.values():
            displacement, lift = gait.foot_offset(t, leg.phase)
            tip = world[f"{leg.name}_tarsus"].tip
            expected_x = doc.frame["center_x"] + leg.rest_tip[0] + displacement
            expected_y = doc.frame["ground_y"] + leg.rest_tip[1] - lift
            assert tip == pytest.approx((expected_x, expected_y), abs=2e-4)


def test_staggered_footfalls_keep_support():
    _, gait, legs = setup()
    assert len({leg.phase for leg in legs.values()}) >= 4
    for i in range(120):
        t = i / 120
        support = [leg for leg in legs.values()
                   if gait.phase_at(t, leg.phase) < gait.stance]
        swing = [leg for leg in legs.values()
                 if gait.phase_at(t, leg.phase) >= gait.stance]
        assert len(support) >= 4
        assert len(swing) >= 1


@pytest.mark.parametrize("surface", ["floor", "ramp", "wall", "ceiling", "rough"])
def test_contact_goals_hold_world_foot_on_surface(surface):
    doc, gait, legs = setup()
    frame_at, probe = surfaces(gait.stride / gait.stance)[surface]
    for i in range(80):
        t = i / 40
        overrides = gait.contact_channels(t, legs, frame_at, probe)
        world, _ = doc.solve("walk", t % 1.0, channel_overrides=overrides)
        for leg in legs.values():
            if gait.phase_at(t, leg.phase) >= gait.stance:
                continue
            landing_at = math.floor(t + leg.phase) - leg.phase
            f = frame_at(landing_at)
            guess = f.world((leg.rest_tip[0] + gait.stride / 2, leg.rest_tip[1]))
            target = probe(guess, f.down).point
            assert footprint(doc, world, leg.name, frame_at(t)) == pytest.approx(target, abs=1e-4)


def test_external_foot_goals_do_not_change_other_pose_channels():
    doc, gait, legs = setup()
    frame_at, probe = surfaces(gait.stride / gait.stance)["ramp"]
    t = 0.2
    channels = gait.contact_channels(t, legs, frame_at, probe)
    before, p_before = doc.solve("scan", t)
    after, p_after = doc.solve("scan", t, channel_overrides=channels)
    assert after["light"].angle == pytest.approx(before["light"].angle)
    assert p_after["beam_visible"] == p_before["beam_visible"]
    assert doc.sample("scan", t) == p_before
    assert p_after != p_before


def test_baked_expression_matches_python_sampler():
    doc, gait, legs = setup()
    for i in range(124):
        t = i / 124
        values = doc.sample("walk", t)
        for leg in legs.values():
            prefix = f"{leg.name}_contact"
            ox, lift = gait.foot_offset(t, leg.phase)
            a = math.radians(leg.tarsus_pitch)
            expected_x = leg.rest_tip[0] - leg.tarsus_length*math.cos(a) + ox
            expected_y = leg.rest_tip[1] - leg.tarsus_length*math.sin(a) - lift
            assert values[f"{prefix}_x"] == pytest.approx(expected_x, abs=2e-6)
            assert values[f"{prefix}_y"] == pytest.approx(expected_y, abs=2e-6)


def test_cached_landings_need_probes_only_when_legs_step():
    _, gait, legs = setup()
    frame_at, ground_probe = surfaces(gait.stride / gait.stance)["floor"]
    count = 0

    def probe(point, direction):
        nonlocal count
        count += 1
        return ground_probe(point, direction)

    cache = ContactCache()
    for i in range(180):
        t = i / 60.0
        cached = gait.contact_channels(t, legs, frame_at, probe, cache=cache)
        if i % 29 == 0:
            uncached = gait.contact_channels(t, legs, frame_at, ground_probe)
            assert cached == uncached
    assert count < len(legs) * 8
    assert len(cache.landings) < 64
    cache.clear()
    assert not cache.landings
