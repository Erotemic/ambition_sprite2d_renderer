from pathlib import Path

from ambition_sprite2d_renderer.registry import discover_all_targets
from ambition_sprite2d_renderer.targets.props import george_booul_vfx as fx
from ambition_sprite2d_renderer.yaml_io import safe_load


def _alpha_area(image) -> int:
    return sum(image.getchannel("A").histogram()[1:])


def test_george_booul_vfx_is_discoverable_and_complete():
    report = discover_all_targets()
    assert fx.TARGET_NAME in report.targets
    assert {name for name, _, _ in fx.ROWS} == set(fx.EFFECT_SPECS) == set(fx.DRAWERS)
    assert len(fx.ROWS) == 21


def test_up_b_authoring_tracks_the_real_move_timing():
    rows = {name: (frames, duration) for name, frames, duration in fx.ROWS}
    assert rows["excluded_middle_windup"] == (4, 45)
    assert rows["excluded_middle_ascent"] == (7, 64)
    assert rows["excluded_middle_tail"] == (10, 67)
    doc = fx._authoring_document()
    timing = doc["move_timing_notes"]["excluded_middle"]
    assert timing["windup_ms"] == 180
    assert timing["set_impulse_at_ms"] == 180
    assert timing["nominal_time_to_apex_ms"] == 450
    assert timing["committed_until_ms"] == 1150
    for name in (
        "excluded_middle_windup",
        "excluded_middle_launch",
        "excluded_middle_ascent",
        "excluded_middle_gate",
        "excluded_middle_tail",
    ):
        assert fx.EFFECT_SPECS[name]["move_id_hint"] == "excluded_middle"
        assert fx.EFFECT_SPECS[name]["sfx_cue_hint"].startswith("vfx.george_booul.up_b.")


def test_one_shots_clear_and_afterimage_loop_stays_visible():
    for name, frames, _ in fx.ROWS:
        last = fx._draw_frame(name, frames - 1, frames)
        if name in fx.LOOPS:
            assert _alpha_area(last) > 100, name
        else:
            assert _alpha_area(last) == 0, name


def test_boolean_and_special_signature_frames_are_visually_distinct():
    samples = {
        "boo": fx._draw_frame("boo_pop", 2, 7),
        "toggle": fx._draw_frame("binary_toggle", 3, 8),
        "and": fx._draw_frame("and_converge", 3, 8),
        "bivalence": fx._draw_frame("bivalence_strong", 3, 7),
        "up_b": fx._draw_frame("excluded_middle_launch", 2, 6),
        "reductio": fx._draw_frame("reductio_impact", 2, 6),
    }
    for name, image in samples.items():
        assert _alpha_area(image) > 180, name
    assert len({image.tobytes() for image in samples.values()}) == len(samples)


def test_render_publishes_anchors_and_authoring_sidecar(tmp_path: Path):
    fx.render(tmp_path)
    manifest = safe_load((tmp_path / "george_booul_vfx_spritesheet.yaml").read_text())
    authoring = safe_load((tmp_path / fx.AUTHORING_FILE).read_text())
    rows = {row["animation"]: row for row in manifest["rows"]}

    assert authoring["character_context"]["character_id"] == "smash_george_booul"
    assert authoring["animations"]["excluded_middle_launch"]["sfx_cue_hint"] == "vfx.george_booul.up_b.launch"
    assert "contact" in rows["reductio_impact"]["rects"][0]["anchors"]
    assert "origin" in rows["excluded_middle_launch"]["rects"][0]["anchors"]
    assert (tmp_path / fx.AUTHORING_FILE).is_file()


def test_authoring_sidecar_is_declared_and_installable(tmp_path: Path):
    target = discover_all_targets().targets[fx.TARGET_NAME]
    render_dir = tmp_path / "rendered"
    install_dir = tmp_path / "installed"
    target.render_sheet(render_dir)
    copied = target.install(render_dir, install_dir)
    sidecar = install_dir / fx.AUTHORING_FILE
    assert sidecar.is_file()
    assert sidecar in copied
    assert fx.AUTHORING_FILE in target.claimed_install_names()
