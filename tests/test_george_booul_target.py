from ambition_sprite2d_renderer.registry import discover_module_targets
from ambition_sprite2d_renderer.targets.characters import george_booul


def test_george_booul_target_contract():
    assert george_booul.TARGET_NAME == "george_booul"
    assert george_booul.ROWS[0][0] == "idle"
    assert "George Boole" in george_booul.AUTHORING_DESCRIPTION
    assert george_booul.GAMEPLAY_DESCRIPTION
    assert george_booul.SUGGESTED_BARKS["idle"]
    assert george_booul.FALLBACK_DIALOGUE


def test_george_booul_renders_classic_sheet_ghost_frame():
    frame = george_booul.render_frame("idle", 0, 8)
    assert frame.mode == "RGBA"
    assert frame.size == george_booul.FRAME_SIZE
    assert frame.getbbox() is not None


def test_george_booul_is_discovered_as_additive_target():
    report = discover_module_targets()
    assert "george_booul" in report.targets
