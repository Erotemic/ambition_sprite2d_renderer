"""Regression contracts for sprite-regeneration performance changes."""
from __future__ import annotations

from PIL import Image

from ambition_sprite2d_renderer.authoring.sheet_build import build_sheet


def test_build_sheet_reuses_rendered_frame_for_canonical(tmp_path, monkeypatch):
    monkeypatch.setenv("AMBITION_SPRITE_PROGRESS", "0")
    calls = []

    def render(anim, frame_idx, nframes):
        calls.append((anim, frame_idx, nframes))
        image = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
        image.putpixel((frame_idx + 2, 5), (255, 255, 255, 255))
        return image

    rows = [("idle", 3, 100), ("walk", 4, 80)]
    outputs = build_sheet(
        target="canonical_reuse_probe",
        rows=rows,
        render_fn=render,
        out_dir=tmp_path,
        frame_size=(24, 24),
        auto_crop=False,
        trim=False,
    )
    assert len(calls) == sum(row[1] for row in rows)
    assert outputs["canonical_transparent"].exists()


def test_lanczos_reducing_gap_keeps_dimensions_and_flat_pixels():
    image = Image.new("RGBA", (256, 192), (10, 20, 30, 255))
    regular = image.resize((64, 48), Image.Resampling.LANCZOS)
    reduced = image.resize((64, 48), Image.Resampling.LANCZOS, reducing_gap=3.0)
    assert reduced.size == (64, 48)
    assert reduced.tobytes() == regular.tobytes()
