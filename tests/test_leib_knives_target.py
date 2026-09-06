from pathlib import Path

from PIL import Image

from ambition_sprite2d_renderer.registry import discover_all_targets
from ambition_sprite2d_renderer.targets.characters import leib_knives


def test_leib_knives_is_registered_with_authoring_guidance():
    target = discover_all_targets().targets["leib_knives"]
    assert target.category == "characters"
    assert target._actor_metadata["actor"]["character_id"] == "npc_leib_knives"

    guidance = target._actor_metadata["authoring"]
    assert "Gottfried Wilhelm Leibniz" in guidance["authoring_description"]
    assert "mixed society" in guidance["authoring_description"]
    assert "precision duelist" in guidance["gameplay_description"]
    assert guidance["suggested_barks"]["provoked"]
    assert len(guidance["fallback_dialogue"]) >= 3


def test_leib_knives_canonical_renders_without_sheet_packer(tmp_path: Path):
    path = leib_knives.render_canonical(tmp_path)
    assert path.exists()
    image = Image.open(path).convert("RGBA")
    assert 0 < image.width <= leib_knives.FRAME_SIZE[0]
    assert 0 < image.height <= leib_knives.FRAME_SIZE[1]
    assert image.getchannel("A").getbbox() is not None


def test_leib_knives_has_voice_and_combat_rows():
    row_names = {name for name, _frames, _duration in leib_knives.ROWS}
    assert {"idle", "walk", "talk", "slash", "hit", "death"} <= row_names
    assert {"crosscut", "integral_sweep", "notation", "block"} <= row_names
    assert all(leib_knives.SUGGESTED_BARKS.values())
    assert leib_knives.FALLBACK_DIALOGUE
