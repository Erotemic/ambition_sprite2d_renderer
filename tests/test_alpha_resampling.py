"""Regression tests for transparent SVG-rig resampling.

The player robot's white shell exposed Lanczos negative-lobe ringing as
isolated pale pixels outside the real silhouette.  These tests pin the shared
RGBA transform seam instead of special-casing that asset.
"""
from __future__ import annotations

from PIL import Image, ImageDraw

from ambition_sprite2d_renderer.core.draw import (
    resize_transparent_sprite,
    rotate_transparent_sprite,
)


def test_bicubic_sprite_reduction_does_not_grow_a_lanczos_halo() -> None:
    source = Image.new("RGBA", (40, 40), (0, 0, 0, 0))
    ImageDraw.Draw(source).rectangle((10, 10, 29, 29), fill=(255, 255, 255, 255))

    reduced = resize_transparent_sprite(source, (10, 10), reducing_gap=3.0)

    # The source occupies exactly output pixels 2..7.  Lanczos produces faint
    # alpha at the outer image boundary for this fixture; bicubic does not.
    assert reduced.getchannel("A").getbbox() == (2, 2, 8, 8)
    assert all(
        reduced.getpixel((x, y))[3] == 0
        for y in range(10)
        for x in range(10)
        if not (2 <= x < 8 and 2 <= y < 8)
    )


def test_rotation_ignores_rgb_hidden_beneath_transparency() -> None:
    clean = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
    dirty = Image.new("RGBA", (24, 24), (255, 255, 255, 0))
    for image in (clean, dirty):
        ImageDraw.Draw(image).rectangle((7, 4, 16, 19), fill=(18, 120, 220, 255))

    clean_rotated = rotate_transparent_sprite(clean, 23.5, center=(12, 12))
    dirty_rotated = rotate_transparent_sprite(dirty, 23.5, center=(12, 12))

    assert dirty_rotated.tobytes() == clean_rotated.tobytes()


def test_unrotated_parts_reduce_on_the_frame_grid() -> None:
    """An unrotated part must keep the sampling phase of the whole frame."""
    from ambition_sprite2d_renderer.authoring import rigdoc
    from ambition_sprite2d_renderer.authoring.part_flipbook import build_rig_flipbook

    back = Image.new("RGBA", (73, 100), (40, 100, 210, 255))

    def render(_row, _index, _count):
        frame = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
        rigdoc.blit_rotated(frame, back, (0, 0), (13, 9), 0, part_name="back")
        return rigdoc.downsampled_canvas(frame, (32, 32))

    flipbook = build_rig_flipbook(
        "rest_parts", [("idle", 1, 100)], render, None, (0, 0), (32, 32)
    )
    assert flipbook.recompose("idle", 0).tobytes() == render("idle", 0, 1).tobytes()
