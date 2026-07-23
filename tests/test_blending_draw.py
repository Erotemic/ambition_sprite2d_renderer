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
