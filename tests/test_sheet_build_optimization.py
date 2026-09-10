from __future__ import annotations

from PIL import Image

from ambition_sprite2d_renderer.authoring.sheet_build import build_sheet, font


def test_untrimmed_sheet_reuses_rendered_canonical_and_runtime_grid(tmp_path):
    calls: list[tuple[str, int, int]] = []

    def render(animation: str, index: int, count: int) -> Image.Image:
        calls.append((animation, index, count))
        image = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
        image.putpixel((index + 1, 1), (255, 255, 255, 255))
        return image

    outputs = build_sheet(
        target="tiny",
        rows=[("idle", 2, 100), ("wave", 1, 120)],
        render_fn=render,
        out_dir=tmp_path,
        frame_size=(8, 8),
        label_width=64,
        auto_crop=False,
        trim=False,
    )

    assert calls == [("idle", 0, 2), ("idle", 1, 2), ("wave", 0, 1)]

    sheet = Image.open(outputs["spritesheet"]).convert("RGBA")
    preview = Image.open(outputs["preview"]).convert("RGBA")
    assert preview.size == sheet.size

    frame_x = 64 + 7
    assert sheet.getpixel((frame_x, 7))[3] == 0
    assert preview.getpixel((frame_x, 7)) == (43, 33, 40, 255)


def test_sheet_label_fonts_are_cached_by_size():
    assert font(14) is font(14)
    assert font(11) is font(11)
    assert font(14) is not font(11)



def test_trimmed_preview_uses_local_opaque_label_drawing():
    from ambition_sprite2d_renderer.authoring.sheet_build import _trimmed_labeled_preview

    frame0 = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
    frame0.putpixel((1, 1), (255, 255, 255, 255))
    frame1 = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
    frame1.putpixel((2, 1), (255, 255, 255, 255))
    rendered_rows = [
        ("idle", 2, 100, [(frame0, {}), (frame1, {})]),
        ("wave", 1, 120, [(frame0, {})]),
    ]

    preview = _trimmed_labeled_preview(rendered_rows, 8, 8, 64)
    assert preview.size == (80, 16)
    assert preview.getpixel((1, 1)) == (20, 23, 31, 255)
    assert preview.getpixel((64 + 1, 1)) == (255, 255, 255, 255)


def test_sheet_publishes_sampled_hit_shapes_with_their_clock(tmp_path):
    import yaml

    triangle = [(1.0, 1.0), (5.0, 1.0), (3.0, 5.0)]
    outputs = build_sheet(
        target='sampled', rows=[('swing', 2, 40)],
        render_fn=lambda *_: Image.new('RGBA', (8, 8), 'white'),
        out_dir=tmp_path, frame_size=(8, 8), auto_crop=False, trim=False,
        animation_key_map={'swing': 'swing'},
        attack_hitboxes={'swing': {'poly': triangle,
                                  'frames': [{'poly': []}, {'poly': triangle}]}},
    )
    manifest = yaml.safe_load(outputs['yaml'].read_text())
    animation = manifest['body_metrics']['animations']['swing']
    assert animation['frame_duration_secs'] == 0.04
    assert not animation['hitbox']['frames'][0]['poly']
    assert len(animation['hitbox']['frames'][1]['poly']) == 3
    # RON is the runtime format; a YAML-only sample would never reach the engine.
    ron = outputs['ron'].read_text()
    assert 'frame_duration_secs: Some(0.04)' in ron
    assert 'frames: [(), (poly:' in ron
