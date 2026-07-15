import math

from ambition_sprite2d_renderer.registry.discovery import discover_module_targets
from ambition_sprite2d_renderer.targets.characters import willson as target


def _row_frames(animation: str) -> int:
    return next(nframes for name, nframes, _duration in target.ROWS if name == animation)


def test_willson_frames_render_without_clipping():
    for animation, nframes, _duration_ms in target.ROWS:
        for frame_idx in range(nframes):
            frame = target.render_frame(animation, frame_idx, nframes)
            assert frame.size == (target.FRAME_W, target.FRAME_H)
            bbox = frame.getchannel("A").getbbox()
            assert bbox is not None
            x0, y0, x1, y1 = bbox
            assert x0 > 0, (animation, frame_idx, bbox)
            assert y0 > 0, (animation, frame_idx, bbox)
            assert x1 < target.FRAME_W, (animation, frame_idx, bbox)
            assert y1 < target.FRAME_H, (animation, frame_idx, bbox)


def test_willson_lineage_records_composite_motion_polish():
    provenance = target.ACTOR_METADATA["provenance"]
    assert provenance["variant_family"] == target.TARGET_NAME
    assert provenance["variant_id"] == "gpt_5_6_composite_motion_polish_2026_07_15"
    concept, initial, polish = provenance["lineage"]
    assert concept["creator_kind"] == "human"
    assert concept["contribution"] == "character_name_and_pelican_riding_a_bicycle_concept"
    assert initial["creator"] == "gpt-5.6-thinking"
    assert initial["parent_revision_id"] == concept["revision_id"]
    assert polish["parent_revision_id"] == initial["revision_id"]
    assert "rider_bicycle_separation" in polish["contribution"]


def test_willson_layer_contract_keeps_foreground_wing_in_front():
    target._validate_layer_z(target.LAYER_Z)
    assert target.LAYER_Z["near_wing"] > target.LAYER_Z["body"]
    assert target.LAYER_Z["near_wing"] > target.LAYER_Z["bike_frame"]
    assert target.LAYER_Z["handle_details"] > target.LAYER_Z["near_wing"]
    assert set(target.PAINTERS) == set(target.LAYER_Z)


def test_idle_mount_cycle_reaches_a_grounded_dismount():
    nframes = _row_frames("idle")
    mounted = target._pose("idle", 0, nframes)
    dismounted = target._pose("idle", nframes // 2, nframes)

    assert mounted["dismount"] == 0.0
    assert mounted["rider_bike_inherit"] == 1.0
    assert dismounted["dismount"] == 1.0
    assert dismounted["rider_bike_inherit"] == 0.0
    assert dismounted["bike_angle"] < -5.0

    body = target._rider_xf(dismounted, target.BASE["body_center"])
    saddle = target._bike_xf(dismounted, target.BASE["seat_post"])
    assert body[0] < saddle[0] - 20.0
    assert body[1] < 145.0


def test_walk_wheel_rotation_cannot_alias_adjacent_frames():
    nframes = _row_frames("walk")
    poses = [target._pose("walk", idx, nframes) for idx in range(nframes)]
    deltas = [
        (poses[idx + 1]["wheel_angle"] - poses[idx]["wheel_angle"]) % 72.0
        for idx in range(nframes - 1)
    ]
    assert all(8.0 < delta < 68.0 for delta in deltas)
    assert all(pose["wheel_motion"] >= 0.95 for pose in poses)

    frames = [target.render_frame("walk", idx, nframes) for idx in range(nframes)]
    assert all(a.tobytes() != b.tobytes() for a, b in zip(frames, frames[1:]))


def test_pedals_remain_opposed_and_centered_on_crank():
    for animation, nframes, _duration_ms in target.ROWS:
        for frame_idx in range(nframes):
            pose = target._pose(animation, frame_idx, nframes)
            near, far = target._pedal_points(pose)
            crank = target._bike_xf(pose, target.BASE["crank"])
            midpoint = ((near[0] + far[0]) / 2.0, (near[1] + far[1]) / 2.0)
            assert math.dist(midpoint, crank) < 1e-6
            assert abs(math.dist(near, far) - 32.0) < 1e-6


def test_slash_is_a_committed_wheelie_beak_strike():
    nframes = _row_frames("slash")
    poses = [target._pose("slash", idx, nframes) for idx in range(nframes)]
    peak = max(poses, key=lambda pose: pose["attack_force"])

    assert peak["attack_force"] > 0.90
    assert peak["bike_angle"] < -8.0
    assert peak["body_lean"] < -8.0
    assert peak["beak_extend"] > 20.0
    assert peak["wheel_motion"] > 1.0

    idle = target.render_frame("slash", 0, nframes)
    strike = target.render_frame("slash", 4, nframes)
    assert idle.tobytes() != strike.tobytes()


def test_fly_keeps_bicycle_inside_the_single_character_silhouette():
    nframes = _row_frames("fly")
    wing_tips = []
    for idx in range(nframes):
        pose = target._pose("fly", idx, nframes)
        assert pose["flight"] == 1.0
        assert pose["rider_bike_inherit"] == 0.0
        body = target._rider_xf(pose, target.BASE["body_center"])
        crank = target._bike_xf(pose, target.BASE["crank"])
        assert crank[1] > body[1] + 85.0
        wing_tips.append(target._rider_xf(pose, target._flight_wing_local("near", pose["flight_flap"])[3]))

    vertical_span = max(point[1] for point in wing_tips) - min(point[1] for point in wing_tips)
    assert vertical_span > 55.0


def test_death_detaches_rider_from_bicycle_without_dropping_the_bike():
    nframes = _row_frames("death")
    first = target._pose("death", 0, nframes)
    last = target._pose("death", nframes - 1, nframes)

    assert first["rider_bike_inherit"] == 1.0
    assert last["rider_bike_inherit"] == 0.0
    assert last["rider_angle"] <= -69.0

    first_body = target._rider_xf(first, target.BASE["body_center"])
    first_crank = target._bike_xf(first, target.BASE["crank"])
    last_body = target._rider_xf(last, target.BASE["body_center"])
    last_crank = target._bike_xf(last, target.BASE["crank"])
    assert abs(last_body[0] - last_crank[0]) > abs(first_body[0] - first_crank[0]) + 65.0
    assert last["bike_dx"] > 20.0


def test_willson_avoids_blur_and_drop_shadow_raster_effects():
    assert not target._source_uses_forbidden_raster_effects()
    assert "shadow" not in target.PAL


def test_willson_is_auto_discovered_as_a_character_target():
    report = discover_module_targets()
    assert target.TARGET_NAME in report.targets
    assert report.targets[target.TARGET_NAME].category == "characters"
