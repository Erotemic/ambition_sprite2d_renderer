from pathlib import Path

from ambition_sprite2d_renderer.registry.discovery import discover_module_targets
from ambition_sprite2d_renderer.targets.characters import vera_ruin as target


def _frames(animation: str) -> int:
    return next(nframes for name, nframes, _duration in target.ROWS if name == animation)


def test_vera_ruin_every_frame_is_nonempty_and_inside_canvas():
    for animation, nframes, _duration_ms in target.ROWS:
        for frame_idx in range(nframes):
            frame = target.render_frame(animation, frame_idx, nframes)
            assert frame.size == (target.FRAME_W, target.FRAME_H)
            bbox = frame.getchannel("A").getbbox()
            assert bbox is not None, (animation, frame_idx)
            x0, y0, x1, y1 = bbox
            assert x0 > 0, (animation, frame_idx, bbox)
            assert y0 > 0, (animation, frame_idx, bbox)
            assert x1 < target.FRAME_W, (animation, frame_idx, bbox)
            assert y1 < target.FRAME_H, (animation, frame_idx, bbox)


def test_vera_ruin_is_not_a_recolored_existing_character():
    source = Path(target.__file__).read_text(encoding="utf8").lower()
    assert "mami" not in source
    assert "marzakhani" not in source
    assert "toon_side" not in source
    assert "from .mami" not in source
    assert "from .davy" not in source
    assert "from .girdle" not in source
    assert "spectrograph halo" in source
    assert "segmented spectrograph halo" in source


def test_vera_ruin_authoring_contract_is_complete():
    meta = target.ACTOR_METADATA
    assert meta["actor"]["display_name"] == "Vera Ruin"
    assert "Vera Rubin" in meta["authoring_description"]
    assert "rotation" in meta["gameplay_description"].lower()
    assert len(meta["suggested_barks"]) >= 6
    assert len(meta["fallback_dialogue"]) >= 5
    assert "spectrograph_duelist" in meta["tags"]


def test_vera_ruin_signature_animations_are_distinct():
    names = {name for name, _nframes, _duration in target.ROWS}
    expected = {"curve_cut", "spectral_lens", "halo_reveal", "counter_rotation"}
    assert expected.issubset(names)
    samples = []
    for name in sorted(expected):
        nframes = _frames(name)
        samples.append(target.render_frame(name, nframes // 2, nframes).tobytes())
    assert len(set(samples)) == len(samples)


def test_vera_ruin_constant_silhouette_contains_wide_halo():
    frame = target.render_frame("idle", 0, _frames("idle"))
    bbox = frame.getchannel("A").getbbox()
    assert bbox is not None
    x0, _y0, x1, _y1 = bbox
    assert x1 - x0 > 100


def test_vera_ruin_portrait_expressions_render():
    default = target._portrait("default")
    skeptical = target._portrait("skeptical")
    delighted = target._portrait("delighted")
    assert default.size == (256, 256)
    assert default.getchannel("A").getbbox() is not None
    assert default.tobytes() != skeptical.tobytes()
    assert skeptical.tobytes() != delighted.tobytes()


def test_vera_ruin_is_auto_discovered():
    report = discover_module_targets()
    assert target.TARGET_NAME in report.targets
    assert report.targets[target.TARGET_NAME].category == "characters"
