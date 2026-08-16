from pathlib import Path

from ambition_sprite2d_renderer.registry import discover_all_targets
from ambition_sprite2d_renderer.targets.props import oiler_vfx as fx
from ambition_sprite2d_renderer.yaml_io import safe_load


def _alpha_area(img) -> int:
    return sum(img.getchannel("A").histogram()[1:])


def test_oiler_vfx_auto_registers_by_existing_in_props_directory():
    report = discover_all_targets()
    assert fx.TARGET_NAME in report.targets
    target = report.targets[fx.TARGET_NAME]
    assert target.category == "props"
    assert target.kind == "module"


def test_catalog_is_complete_and_has_mechanic_visual_variety():
    names = {name for name, _frames, _duration in fx.ROWS}
    assert names == set(fx.EFFECT_SPECS) == set(fx.DRAWERS)
    assert len(names) == 20
    assert fx.LOOPS == {"invariant_loop", "gate_calibration", "portal_leak"}
    families = {spec["family"] for spec in fx.EFFECT_SPECS.values()}
    assert len(families) >= 8


def test_one_shots_end_clear_and_loops_remain_visible():
    for name, frames, _duration in fx.ROWS:
        image = fx._draw_frame(name, frames - 1, frames)
        if name in fx.LOOPS:
            assert _alpha_area(image) > 100, name
        else:
            assert _alpha_area(image) == 0, name


def test_signature_frames_are_substantial_and_distinct():
    samples = {
        name: fx._draw_frame(name, max(0, frames // 2), frames)
        for name, frames, _duration in fx.ROWS
    }
    assert all(_alpha_area(image) > 90 for image in samples.values())
    assert len({image.tobytes() for image in samples.values()}) == len(samples)


def test_render_publishes_anchors_and_auto_registration_note(tmp_path: Path):
    fx.render(tmp_path)
    manifest = safe_load((tmp_path / "oiler_vfx_spritesheet.yaml").read_text())
    authoring = safe_load((tmp_path / fx.AUTHORING_FILE).read_text())
    assert authoring["auto_registration"]["central_registry_edit_required"] is False
    assert set(authoring["animations"]) == {name for name, _, _ in fx.ROWS}
    rows = {row["animation"]: row for row in manifest["rows"]}
    assert "emitter" in rows["oil_drip"]["rects"][0]["anchors"]
    assert "contact" in rows["oil_splash"]["rects"][0]["anchors"]
