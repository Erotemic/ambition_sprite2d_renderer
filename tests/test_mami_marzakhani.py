from __future__ import annotations

from PIL import Image

from ambition_sprite2d_renderer.registry.discovery import discover_module_targets
from ambition_sprite2d_renderer.targets.characters import mami_marzakhani as target


def test_mami_marzakhani_publishes_native_named_portraits(tmp_path):
    outputs = target.render_portraits(tmp_path)
    assert [path.name for path in outputs] == [
        "mami_marzakhani_portraits.png",
        "mami_marzakhani_portraits.ron",
    ]
    sheet = Image.open(outputs[0])
    assert sheet.width % target.PORTRAIT_W == 0
    assert sheet.height % target.PORTRAIT_H == 0
    assert sheet.width * sheet.height == target.PORTRAIT_W * target.PORTRAIT_H * 16
    default = sheet.crop((0, 0, target.PORTRAIT_W, target.PORTRAIT_H))
    bbox = default.getchannel("A").getbbox()
    assert bbox is not None
    assert bbox[2] - bbox[0] > 200
    assert bbox[3] - bbox[1] > 290
    assert len(default.getcolors(maxcolors=1_000_000) or []) > 500

    manifest = outputs[1].read_text(encoding="utf8")
    assert 'default_clip: "default"' in manifest
    assert '"explaining": (' in manifest
    assert '"thinking": (' in manifest
    assert '"delighted": (' in manifest
    assert "duration_ms: 104" in manifest
    assert "duration_ms: 128" in manifest


def test_mami_marzakhani_actions_have_visible_motion_and_math_identity():
    for animation in ("walk", "geodesic_sweep", "boundary_fold", "moduli_bloom"):
        nframes = next(n for name, n, _duration in target.ROWS if name == animation)
        first = target.render_frame(animation, 0, nframes)
        peak = target.render_frame(animation, max(1, nframes // 3), nframes)
        assert first.tobytes() != peak.tobytes(), animation


def test_mami_marzakhani_is_auto_discovered_as_character_target():
    report = discover_module_targets()
    assert target.TARGET_NAME in report.targets
    assert report.targets[target.TARGET_NAME].category == "characters"
    assert report.targets[target.TARGET_NAME].supports_portraits
