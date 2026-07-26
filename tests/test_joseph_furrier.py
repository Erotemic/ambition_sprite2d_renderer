from __future__ import annotations

from ambition_sprite2d_renderer.registry.discovery import discover_module_targets
from ambition_sprite2d_renderer.targets.characters import joseph_furrier as target


def test_joseph_furrier_authoring_description_records_parody_and_inspiration():
    description = target.authoring_description
    assert target.ACTOR_METADATA["authoring_description"] == description
    assert "Joseph Fourier" in description
    assert "blanket" in description.lower()
    assert "step_function" in description
    assert "not another claim about Fourier's life" in description


def test_joseph_furrier_frames_remain_inside_authored_canvas():
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


def test_joseph_furrier_specials_keep_stairs_secondary_to_blanket_identity():
    idle = target._pose("idle", 1, 8)
    step = target._pose("step_function", 3, 8)
    descent = target._pose("spectral_descent", 3, 8)
    harmonic = target._pose("harmonic_split", 3, 8)

    assert idle.step == 0.0
    assert idle.descent == 0.0
    assert step.step > 0.8
    assert descent.step > 0.8
    assert descent.descent > 0.8
    assert harmonic.harmonic > 0.8
    assert harmonic.blanket_open > 0.6


def test_joseph_furrier_is_auto_discovered_with_local_metadata():
    report = discover_module_targets()
    discovered = report.targets[target.TARGET_NAME]
    assert discovered.category == "characters"
    assert discovered.supports_portraits
    assert discovered._actor_metadata["authoring_description"] == target.authoring_description
