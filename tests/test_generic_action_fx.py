from pathlib import Path

from ambition_sprite2d_renderer.registry import discover_all_targets
from ambition_sprite2d_renderer.targets.props import generic_action_fx as fx
from ambition_sprite2d_renderer.yaml_io import safe_load


def _alpha_area(img) -> int:
    histogram = img.getchannel("A").histogram()
    return sum(histogram[1:])


def test_generic_action_fx_is_discovered_as_a_sprite_target():
    report = discover_all_targets()
    target = report.targets[fx.TARGET_NAME]
    assert target.category == "props"
    assert target.kind == "module"


def test_generic_action_fx_catalog_has_authored_semantics_for_every_row():
    row_names = {name for name, _frames, _duration in fx.ROWS}
    assert row_names == set(fx.EFFECT_SPECS)
    assert fx.EFFECT_SPECS["charge_pulse"]["loop"] is True
    assert fx.EFFECT_SPECS["muzzle_flash"]["orientation"] == "positive_x_is_forward"
    assert fx.EFFECT_SPECS["landing_puff"]["placement"] == "surface_contact"


def test_one_shots_end_clear_but_charge_pulse_remains_visible():
    for name, frames, _duration in fx.ROWS:
        last = fx._draw_frame(name, frames - 1, frames)
        if name == "charge_pulse":
            assert _alpha_area(last) > 100
        else:
            assert _alpha_area(last) == 0, name


def test_signature_frames_are_visually_substantial_and_distinct():
    samples = {
        "hit_hard": fx._draw_frame("hit_hard", 0, 6),
        "landing_puff": fx._draw_frame("landing_puff", 2, 7),
        "poof_magic": fx._draw_frame("poof_magic", 3, 8),
        "muzzle_flash": fx._draw_frame("muzzle_flash", 0, 5),
        "charge_pulse": fx._draw_frame("charge_pulse", 2, 8),
    }
    for name, image in samples.items():
        assert _alpha_area(image) > 300, name
    assert len({image.tobytes() for image in samples.values()}) == len(samples)


def test_render_publishes_runtime_anchors_and_author_owned_sidecar(tmp_path: Path):
    fx.render(tmp_path)
    manifest = safe_load((tmp_path / "generic_action_fx_spritesheet.yaml").read_text())
    authoring = safe_load((tmp_path / fx.AUTHORING_FILE).read_text())

    assert authoring["status"] == "authoring_hints_not_yet_runtime_contract"
    assert set(authoring["animations"]) == {name for name, _, _ in fx.ROWS}
    assert authoring["animations"]["charge_pulse"]["loop"] is True
    assert authoring["animations"]["muzzle_flash"]["origin_anchor"] == "origin"

    rows = {row["animation"]: row for row in manifest["rows"]}
    muzzle_origin = rows["muzzle_flash"]["rects"][0]["anchors"]["origin"]
    landing_contact = rows["landing_puff"]["rects"][0]["anchors"]["contact"]
    assert 0 <= muzzle_origin["x"] <= manifest["frame_width"]
    assert 0 <= muzzle_origin["y"] <= manifest["frame_height"]
    assert 0 <= landing_contact["x"] <= manifest["frame_width"]
    assert 0 <= landing_contact["y"] <= manifest["frame_height"]

    # The arbitrary effect payload is deliberately present in human-readable
    # frame metadata for the integration pass to evaluate/promote.
    hard_frame = rows["hit_hard"]["rects"][0]
    assert hard_frame["effect"]["family"] == "impact"
    assert hard_frame["effect"]["phase"] == "impact"


def test_authoring_sidecar_is_part_of_the_declared_install_surface(tmp_path: Path):
    report = discover_all_targets()
    target = report.targets[fx.TARGET_NAME]
    render_dir = tmp_path / "rendered"
    install_dir = tmp_path / "installed"
    target.render_sheet(render_dir)
    copied = target.install(render_dir, install_dir)

    assert (install_dir / fx.AUTHORING_FILE).exists()
    assert install_dir / fx.AUTHORING_FILE in copied
    assert fx.AUTHORING_FILE in target.claimed_install_names()


def test_full_sprite_regen_roster_publishes_generic_action_fx():
    repo_root = Path(__file__).resolve().parents[3]
    regen = (repo_root / "regen_sprites.sh").read_text(encoding="utf8")
    assert "\n    generic_action_fx\n" in regen
