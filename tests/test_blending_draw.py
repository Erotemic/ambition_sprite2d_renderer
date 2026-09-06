"""Behavioral matrix for core.draw.blending_draw across image modes.

The helper is used at every content-draw site (358 call sites), so its mode
contract is pinned per-mode rather than inferred from "targets stop crashing":

  RGBA — translucent inks composite (scratch layer); opaque byte-identical to
         raw drawing; alpha==0 keeps deliberate eraser (clobber) semantics.
  RGB  — translucent RGBA inks blend via Pillow's native Draw(img, "RGBA").
  L/P  — scalar/index inks draw normally (their native contract).
"""
from __future__ import annotations

from PIL import Image, ImageDraw

from ambition_sprite2d_renderer.core.draw import blending_draw


def _red_base() -> Image.Image:
    img = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
    ImageDraw.Draw(img).rectangle((0, 0, 7, 7), fill=(200, 0, 0, 255))
    return img


def test_rgba_translucent_composites() -> None:
    got = _red_base()
    blending_draw(got).rectangle((2, 2, 5, 5), fill=(255, 255, 255, 100))
    want = _red_base()
    layer = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
    ImageDraw.Draw(layer).rectangle((2, 2, 5, 5), fill=(255, 255, 255, 100))
    want.alpha_composite(layer)
    assert got.tobytes() == want.tobytes()


def test_rgba_opaque_is_byte_identical_to_raw() -> None:
    a, b = _red_base(), _red_base()
    blending_draw(a).polygon([(1, 1), (6, 1), (3, 6)], fill=(0, 255, 0, 255))
    ImageDraw.Draw(b, "RGBA").polygon([(1, 1), (6, 1), (3, 6)], fill=(0, 255, 0, 255))
    assert a.tobytes() == b.tobytes()


def test_rgba_alpha_zero_keeps_eraser_semantics() -> None:
    a, b = _red_base(), _red_base()
    blending_draw(a).line((0, 0, 7, 7), fill=(0, 0, 0, 0), width=1)
    ImageDraw.Draw(b, "RGBA").line((0, 0, 7, 7), fill=(0, 0, 0, 0), width=1)
    assert a.tobytes() == b.tobytes()
    assert a.getpixel((3, 3))[3] == 0  # actually erased


def test_rgb_translucent_blends_not_clobbers() -> None:
    img = Image.new("RGB", (4, 4), (0, 0, 0))
    blending_draw(img).rectangle((0, 0, 3, 3), fill=(255, 0, 0, 128))
    r, g, b = img.getpixel((1, 1))
    assert 120 <= r <= 136 and g == 0 and b == 0  # ~50% red over black


def test_l_and_p_scalar_inks_draw() -> None:
    l = Image.new("L", (4, 4), 0)
    blending_draw(l).rectangle((0, 0, 3, 3), fill=128)
    assert l.getpixel((1, 1)) == 128
    p = Image.new("P", (4, 4), 0)
    blending_draw(p).rectangle((0, 0, 3, 3), fill=3)
    assert p.getpixel((1, 1)) == 3


def _full_overlay_reference(name: str, *args, **kwargs) -> Image.Image:
    base = _red_base()
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    getattr(ImageDraw.Draw(layer, "RGBA"), name)(*args, **kwargs)
    base.alpha_composite(layer)
    return base


def test_rgba_local_overlay_matches_full_frame_reference_for_primitives() -> None:
    cases = [
        ("rectangle", ((-2, 1, 5, 6),), {"fill": (255, 255, 255, 100)}),
        ("ellipse", ((1, 0, 7, 6),), {"fill": (20, 240, 120, 90), "outline": (255, 255, 255, 120), "width": 2}),
        ("rounded_rectangle", ((0, 1, 7, 7),), {"radius": 2, "fill": (20, 80, 240, 100)}),
        ("polygon", ([(0, 0), (7, 1), (4, 7)],), {"fill": (240, 180, 20, 110)}),
        ("line", ((-2, 7, 4, 1, 9, 6),), {"fill": (255, 255, 255, 100), "width": 3, "joint": "curve"}),
        ("arc", ((-1, -1, 7, 7),), {"start": 10, "end": 250, "fill": (255, 255, 255, 100), "width": 2}),
        ("pieslice", ((0, 0, 8, 8),), {"start": 35, "end": 190, "fill": (255, 255, 255, 100)}),
        ("point", ([(1, 1), (6, 6)],), {"fill": (255, 255, 255, 100)}),
    ]
    for name, args, kwargs in cases:
        got = _red_base()
        getattr(blending_draw(got), name)(*args, **kwargs)
        want = _full_overlay_reference(name, *args, **kwargs)
        assert got.tobytes() == want.tobytes(), name


def test_rgba_local_overlay_accounts_for_positional_width_and_nested_bbox() -> None:
    cases = [
        ("line", ([(0, 7), (7, 0)], (255, 255, 255, 100), 5), {}),
        ("ellipse", ([(0, 0), (7, 7)], (20, 240, 120, 90), (255, 255, 255, 120), 4), {}),
        (
            "rounded_rectangle",
            ([(0, 0), (7, 7)], 2),
            {"fill": (20, 80, 240, 100), "outline": (255, 255, 255, 120), "width": 3},
        ),
    ]
    for name, args, kwargs in cases:
        got = _red_base()
        getattr(blending_draw(got), name)(*args, **kwargs)
        want = _full_overlay_reference(name, *args, **kwargs)
        assert got.tobytes() == want.tobytes(), name


def test_rgba_translucent_polygon_never_punches_alpha_hole_in_opaque_shape() -> None:
    """Regression for the classic translucent polygon alpha-clobber failure."""
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    base = ImageDraw.Draw(img, "RGBA")
    base.polygon([(3, 3), (28, 5), (25, 28), (5, 25)], fill=(80, 100, 140, 255))
    alpha_before = img.getchannel("A").copy()

    blending_draw(img).polygon(
        [(8, 7), (26, 11), (19, 25), (7, 21)],
        fill=(245, 180, 60, 96),
    )

    alpha_after = img.getchannel("A")
    for y in range(img.height):
        for x in range(img.width):
            if alpha_before.getpixel((x, y)) == 255:
                assert alpha_after.getpixel((x, y)) == 255


def test_rgba_translucent_polygon_matches_full_canvas_reference_on_concave_overlap() -> None:
    """Pin correctness on a concave polygon with overlapping translucent geometry."""
    base = Image.new("RGBA", (40, 40), (0, 0, 0, 0))
    ImageDraw.Draw(base, "RGBA").polygon(
        [(2, 2), (37, 4), (31, 36), (8, 32)],
        fill=(110, 70, 160, 220),
    )

    points = [(5, 6), (34, 7), (18, 18), (34, 31), (6, 29), (15, 18)]

    got = base.copy()
    blending_draw(got).polygon(points, fill=(40, 220, 230, 112), outline=(255, 255, 255, 144))

    want = base.copy()
    layer = Image.new("RGBA", want.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer, "RGBA").polygon(
        points,
        fill=(40, 220, 230, 112),
        outline=(255, 255, 255, 144),
    )
    want.alpha_composite(layer)

    assert got.tobytes() == want.tobytes()
