from __future__ import annotations

from PIL import Image

from ambition_sprite2d_renderer.registry.discovery import discover_module_targets
from ambition_sprite2d_renderer.targets.characters import mami_marzakhani as target


def test_mami_marzakhani_frames_remain_inside_authored_canvas():
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


def test_mami_marzakhani_has_prop_free_shadow_free_authoring_contract():
    assert target.USES_PROPS is False
    assert target.USES_DROP_SHADOW is False
    assert target.source_uses_forbidden_raster_effects() is False
    assert not any(name == "SHADOW" or name.endswith("_SHADOW") for name in vars(target) if name != "USES_DROP_SHADOW")


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

    geodesic = target._pose("geodesic_sweep", 6, 8)
    boundary = target._pose("boundary_fold", 4, 8)
    moduli = target._pose("moduli_bloom", 6, 10)
    assert geodesic.geodesic > 0.75
    assert boundary.boundary > 0.75
    assert moduli.moduli > 0.75


def test_mami_marzakhani_is_auto_discovered_as_character_target():
    report = discover_module_targets()
    assert target.TARGET_NAME in report.targets
    assert report.targets[target.TARGET_NAME].category == "characters"
    assert report.targets[target.TARGET_NAME].supports_portraits
