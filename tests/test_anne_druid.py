from __future__ import annotations

from PIL import Image

from ambition_sprite2d_renderer.registry.discovery import discover_module_targets
from ambition_sprite2d_renderer.targets.characters import anne_druid as target


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
