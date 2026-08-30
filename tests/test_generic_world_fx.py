from pathlib import Path

from ambition_sprite2d_renderer.registry import discover_all_targets
from ambition_sprite2d_renderer.targets.props import generic_world_fx as fx
from ambition_sprite2d_renderer.yaml_io import safe_load


def _alpha_area(img) -> int:
    histogram = img.getchannel("A").histogram()
    return sum(histogram[1:])


def test_generic_world_fx_is_discovered_as_a_sprite_target():
    report = discover_all_targets()
    target = report.targets[fx.TARGET_NAME]
    assert target.category == "props"
    assert target.kind == "module"


def test_generic_world_fx_catalog_is_complete_and_varied():
    row_names = {name for name, _frames, _duration in fx.ROWS}
    assert row_names == set(fx.EFFECT_SPECS)
    # ⛔ A FLOOR, NOT A COUNT. `== 18` broke the moment a nineteenth effect was
    # authored, which is content growing rather than anything going wrong — and
    # it guarded nothing the set-equality above does not already guard. What is
    # worth pinning is that the catalog cannot SHRINK back to a token few.
    assert len(row_names) >= 18
    assert len({spec["family"] for spec in fx.EFFECT_SPECS.values()}) >= 9
    assert fx.EFFECT_SPECS["dash_streak"]["orientation"] == "positive_x_is_forward"
    assert fx.EFFECT_SPECS["water_splash"]["placement"] == "surface_contact"
    assert fx.EFFECT_SPECS["ember_wisp"]["loop"] is True
    assert fx.EFFECT_SPECS["shield_break"]["layer_hint"] == "over_source"


def test_one_shots_end_clear_and_loops_remain_visible():
    for name, frames, _duration in fx.ROWS:
        last = fx._draw_frame(name, frames - 1, frames)
        if name in fx.LOOPS:
            assert _alpha_area(last) > 100, name
        else:
            assert _alpha_area(last) == 0, name


def test_signature_frames_are_substantial_and_visually_distinct():
    samples = {
        "dash_streak": fx._draw_frame("dash_streak", 2, 7),
        "shield_break": fx._draw_frame("shield_break", 3, 8),
        "heal_bloom": fx._draw_frame("heal_bloom", 3, 8),
        "teleport_arrive": fx._draw_frame("teleport_arrive", 3, 8),
        "water_splash": fx._draw_frame("water_splash", 3, 8),
        "ember_wisp": fx._draw_frame("ember_wisp", 2, 10),
        "electric_arc": fx._draw_frame("electric_arc", 2, 7),
        "ice_shatter": fx._draw_frame("ice_shatter", 3, 8),
    }
    for name, image in samples.items():
        assert _alpha_area(image) > 250, name
    assert len({image.tobytes() for image in samples.values()}) == len(samples)


def test_render_publishes_runtime_anchors_and_richer_authoring_hints(tmp_path: Path):
    fx.render(tmp_path)
    manifest = safe_load((tmp_path / "generic_world_fx_spritesheet.yaml").read_text())
    authoring = safe_load((tmp_path / fx.AUTHORING_FILE).read_text())

    assert authoring["status"] == "authoring_hints_not_yet_runtime_contract"
    assert set(authoring["animations"]) == {name for name, _, _ in fx.ROWS}
    assert authoring["animations"]["dizzy_stars"]["completion_hint"] == "loop_until_cancelled"
    assert authoring["animations"]["electric_arc"]["origin_anchor"] == "origin"
    assert authoring["animations"]["heal_bloom"]["tint_policy_hint"] == "preserve_palette_preferred"

    rows = {row["animation"]: row for row in manifest["rows"]}
    water_contact = rows["water_splash"]["rects"][0]["anchors"]["contact"]
    ember_emitter = rows["ember_wisp"]["rects"][0]["anchors"]["emitter"]
    assert 0 <= water_contact["x"] <= manifest["frame_width"]
    assert 0 <= water_contact["y"] <= manifest["frame_height"]
    assert 0 <= ember_emitter["x"] <= manifest["frame_width"]
    assert 0 <= ember_emitter["y"] <= manifest["frame_height"]

    frame = rows["shield_break"]["rects"][0]
    assert frame["effect"]["family"] == "defense"
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


def test_full_sprite_regen_roster_publishes_generic_world_fx(regen_roster: str):
    assert "\n    generic_world_fx\n" in regen_roster
