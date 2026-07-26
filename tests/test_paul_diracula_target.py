"""Contract checks for the bespoke Paul Diracula sprite target."""

from __future__ import annotations

from ambition_sprite2d_renderer.targets.characters import paul_diracula


def test_paul_diracula_authoring_contract():
    assert paul_diracula.TARGET_NAME == "paul_diracula"
    assert "Paul Dirac" in paul_diracula.AUTHORING_DESCRIPTION
    assert "Dirac Sea" in paul_diracula.GAMEPLAY_DESCRIPTION
    assert len(paul_diracula.SUGGESTED_BARKS) >= 5
    assert len(paul_diracula.FALLBACK_DIALOGUE) >= 4

    lineage = paul_diracula.ACTOR_METADATA["lineage"]
    assert lineage["authoring_description"] == paul_diracula.AUTHORING_DESCRIPTION
    assert lineage["gameplay_description"] == paul_diracula.GAMEPLAY_DESCRIPTION
    assert lineage["suggested_barks"] == paul_diracula.SUGGESTED_BARKS
    assert lineage["fallback_dialogue"] == paul_diracula.FALLBACK_DIALOGUE


def test_paul_diracula_signature_frames_render():
    counts = {name: frames for name, frames, _duration in paul_diracula.ROWS}
    for animation in (
        "idle",
        "talk",
        "delta_spike",
        "dirac_sea",
        "pair_creation",
        "spinor_turn",
    ):
        frame_count = counts[animation]
        image = paul_diracula.render_frame(animation, frame_count // 2, frame_count)
        assert image.size == (paul_diracula.FRAME_W, paul_diracula.FRAME_H)
        assert image.convert("RGBA").getchannel("A").getbbox() is not None
