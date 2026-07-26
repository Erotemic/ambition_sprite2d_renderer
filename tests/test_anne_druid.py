from __future__ import annotations

from PIL import Image

from ambition_sprite2d_renderer.registry.discovery import discover_module_targets
from ambition_sprite2d_renderer.targets.characters import anne_druid as target


def test_anne_druid_frames_remain_inside_authored_canvas():
    for animation, nframes, _duration_ms in target.ROWS:
        for frame_idx in range(nframes):
            frame = target.render_frame(animation, frame_idx, nframes)
            assert frame.size == (target.FRAME_W, target.FRAME_H)
            bbox = frame.getchannel("A").getbbox()
            assert bbox is not None, (animation, frame_idx)
            left, top, right, bottom = bbox
            assert left > 0, (animation, frame_idx, bbox)
            assert top > 0, (animation, frame_idx, bbox)
            assert right < target.FRAME_W, (animation, frame_idx, bbox)
            assert bottom < target.FRAME_H, (animation, frame_idx, bbox)


def test_anne_druid_carries_behind_the_scenes_authoring_description(tmp_path):
    description = target.AUTHORING_DESCRIPTION
    assert description["parody_of"] == "Ann Druyan"
    assert "Voyager Golden Record" in description["concept"]
    assert description["visual_inspiration"]
    assert description["gameplay_inspiration"]
    assert description["boundaries"]
    assert target.ACTOR_METADATA["authoring_description"] is description

    outputs = target.render(tmp_path)
    actor = next(path for path in outputs if path.name == "anne_druid_actor.ron")
    text = actor.read_text(encoding="utf8")
    assert "authoring_description: Some" in text
    assert 'parody_of: "Ann Druyan"' in text
    assert "Preserve agency and scientific curiosity" in text


def test_anne_druid_specials_have_visible_motion_and_distinct_science_identity():
    for animation in (
        "golden_record_guard",
        "whale_song",
        "pulsar_beacon",
        "cosmic_garden",
        "voyager_cast",
    ):
        nframes = next(n for name, n, _duration in target.ROWS if name == animation)
        first = target.render_frame(animation, 0, nframes)
        peak = target.render_frame(animation, max(1, nframes // 2), nframes)
        assert first.tobytes() != peak.tobytes(), animation

    assert target._pose("golden_record_guard", 4, 8).record_front is True
    assert target._pose("whale_song", 5, 10).effect == "whale_song"
    assert target._pose("pulsar_beacon", 5, 10).effect == "pulsar"
    assert target._pose("cosmic_garden", 5, 10).effect == "cosmic_garden"
    assert target._pose("voyager_cast", 5, 10).record_x > 95.0


def test_anne_druid_publishes_native_named_portraits(tmp_path):
    outputs = target.render_portraits(tmp_path)
    assert [path.name for path in outputs] == [
        "anne_druid_portraits.png",
        "anne_druid_portraits.ron",
    ]
    sheet = Image.open(outputs[0])
    assert sheet.width % target.PORTRAIT_SIZE[0] == 0
    assert sheet.height % target.PORTRAIT_SIZE[1] == 0
    assert sheet.getchannel("A").getbbox() is not None

    manifest = outputs[1].read_text(encoding="utf8")
    assert 'default_clip: "default"' in manifest
    assert '"speaking": (' in manifest
    assert '"wonder": (' in manifest
    assert '"listening": (' in manifest
    assert '"whale_song": (' in manifest
    assert '"pale_blue_dot": (' in manifest


def test_anne_druid_is_auto_discovered_as_character_target():
    report = discover_module_targets()
    assert target.TARGET_NAME in report.targets
    discovered = report.targets[target.TARGET_NAME]
    assert discovered.category == "characters"
    assert discovered.supports_portraits
