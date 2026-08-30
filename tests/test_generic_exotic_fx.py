from pathlib import Path

from ambition_sprite2d_renderer.registry import discover_all_targets
from ambition_sprite2d_renderer.targets.props import generic_exotic_fx as fx
from ambition_sprite2d_renderer.yaml_io import safe_load


def _alpha_area(img) -> int:
    histogram = img.getchannel("A").histogram()
    return sum(histogram[1:])


def test_generic_exotic_fx_is_discovered_as_a_sprite_target():
    report = discover_all_targets()
    target = report.targets[fx.TARGET_NAME]
    assert target.category == "props"
    assert target.kind == "module"


def test_generic_exotic_fx_catalog_is_complete_and_varied():
    row_names = {name for name, _frames, _duration in fx.ROWS}
    assert row_names == set(fx.EFFECT_SPECS)
    assert row_names == set(fx.DRAWERS)
    assert len(row_names) == 24
    assert len({spec["family"] for spec in fx.EFFECT_SPECS.values()}) >= 12
    assert fx.EFFECT_SPECS["sonic_boom"]["orientation"] == "positive_x_is_forward"
    assert fx.EFFECT_SPECS["slime_splat"]["placement"] == "surface_contact"
    assert fx.EFFECT_SPECS["smoke_column"]["loop"] is True
    assert fx.EFFECT_SPECS["rune_circle"]["loop"] is True
    assert fx.EFFECT_SPECS["shadow_wisp"]["blend_mode_hint"] == "alpha_or_multiply"


def test_one_shots_end_clear_and_loops_remain_visible():
    for name, frames, _duration in fx.ROWS:
        last = fx._draw_frame(name, frames - 1, frames)
        if name in fx.LOOPS:
            assert _alpha_area(last) > 100, name
        else:
            assert _alpha_area(last) == 0, name


def test_signature_frames_are_substantial_and_visually_distinct():
    samples = {
        "smoke_puff": fx._draw_frame("smoke_puff", 3, 9),
        "poison_cloud": fx._draw_frame("poison_cloud", 3, 12),
        "slime_splat": fx._draw_frame("slime_splat", 3, 8),
        "sonic_boom": fx._draw_frame("sonic_boom", 3, 8),
        "psychic_pulse": fx._draw_frame("psychic_pulse", 3, 9),
        "time_shatter": fx._draw_frame("time_shatter", 3, 9),
        "rune_circle": fx._draw_frame("rune_circle", 3, 12),
        "gear_scatter": fx._draw_frame("gear_scatter", 3, 9),
        "vine_sprout": fx._draw_frame("vine_sprout", 5, 11),
        "petal_burst": fx._draw_frame("petal_burst", 4, 10),
        "sand_whorl": fx._draw_frame("sand_whorl", 3, 12),
        "shadow_wisp": fx._draw_frame("shadow_wisp", 3, 12),
    }
    for name, image in samples.items():
        assert _alpha_area(image) > 180, name
    assert len({image.tobytes() for image in samples.values()}) == len(samples)


def test_render_publishes_runtime_anchors_and_richer_authoring_hints(tmp_path: Path):
    fx.render(tmp_path)
    manifest = safe_load((tmp_path / "generic_exotic_fx_spritesheet.yaml").read_text())
    authoring = safe_load((tmp_path / fx.AUTHORING_FILE).read_text())

    assert authoring["status"] == "authoring_hints_not_yet_runtime_contract"
    assert set(authoring["animations"]) == {name for name, _, _ in fx.ROWS}
    assert authoring["animations"]["smoke_column"]["completion_hint"] == "loop_until_cancelled"
    assert authoring["animations"]["sonic_boom"]["origin_anchor"] == "origin"
    assert authoring["animations"]["gear_scatter"]["tint_policy_hint"] == "preserve_palette_preferred"

    rows = {row["animation"]: row for row in manifest["rows"]}
    splat_contact = rows["slime_splat"]["rects"][0]["anchors"]["contact"]
    smoke_emitter = rows["smoke_column"]["rects"][0]["anchors"]["emitter"]
    assert 0 <= splat_contact["x"] <= manifest["frame_width"]
    assert 0 <= splat_contact["y"] <= manifest["frame_height"]
    assert 0 <= smoke_emitter["x"] <= manifest["frame_width"]
    assert 0 <= smoke_emitter["y"] <= manifest["frame_height"]

    frame = rows["time_shatter"]["rects"][0]
    assert frame["effect"]["family"] == "time"
    assert frame["effect"]["phase"] == "fracture"


def test_authoring_sidecar_is_part_of_declared_install_surface(tmp_path: Path):
    report = discover_all_targets()
    target = report.targets[fx.TARGET_NAME]
    render_dir = tmp_path / "rendered"
    install_dir = tmp_path / "installed"
    target.render_sheet(render_dir)
    copied = target.install(render_dir, install_dir)

    assert (install_dir / fx.AUTHORING_FILE).exists()
    assert install_dir / fx.AUTHORING_FILE in copied
    assert fx.AUTHORING_FILE in target.claimed_install_names()


def test_full_sprite_regen_roster_publishes_generic_exotic_fx(regen_roster: str):
    assert "\n    generic_exotic_fx\n" in regen_roster
