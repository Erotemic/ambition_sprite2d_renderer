"""Contract checks for the bespoke Paul Diracula sprite target."""

from __future__ import annotations

from ambition_sprite2d_renderer.targets.characters import paul_diracula


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
