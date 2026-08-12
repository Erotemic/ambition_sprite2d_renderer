from __future__ import annotations

import io
import sys
from types import SimpleNamespace

from PIL import Image


def _png_bytes(color=(20, 40, 80, 255)) -> bytes:
    image = Image.new("RGBA", (12, 10), color)
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def test_rasterize_subset_cache_reuses_resvg_across_calls(tmp_path, monkeypatch):
    from ambition_sprite2d_renderer.authoring import svg_parts

    svg = tmp_path / "parts.svg"
    svg.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape">'
        '<g inkscape:label="side"><rect id="arm" x="0" y="0" width="4" height="4"/></g>'
        '</svg>',
        encoding="utf8",
    )
    calls = []

    def fake_svg_to_bytes(*, svg_string, dpi):
        calls.append((svg_string, dpi))
        return _png_bytes()

    monkeypatch.setitem(sys.modules, "resvg_py", SimpleNamespace(svg_to_bytes=fake_svg_to_bytes))
    svg_parts._rasterize_subset_cached.cache_clear()
    svg_parts._parse.cache_clear()

    first, first_off, first_ppu = svg_parts.rasterize_subset(svg, "side", ["arm"], 96.0)
    second, second_off, second_ppu = svg_parts.rasterize_subset(svg, "side", ["arm"], 96.0)

    assert len(calls) == 1
    assert first is not second
    assert first is not None and second is not None
    assert first.tobytes() == second.tobytes()
    assert first_off == second_off
    assert first_ppu == second_ppu

    # Returned images are independent copies: mutating one must not poison the
    # process-wide cached raster used by later RigDocuments.
    first.putpixel((0, 0), (255, 0, 0, 0))
    third, _off, _ppu = svg_parts.rasterize_subset(svg, "side", ["arm"], 96.0)
    assert third is not None
    assert third.getpixel((0, 0)) == second.getpixel((0, 0))


def test_rasterize_subset_cache_invalidates_when_svg_changes(tmp_path, monkeypatch):
    from ambition_sprite2d_renderer.authoring import svg_parts

    svg = tmp_path / "parts.svg"
    svg.write_text('<svg xmlns="http://www.w3.org/2000/svg"><rect id="arm"/></svg>', encoding="utf8")
    calls = []

    def fake_svg_to_bytes(*, svg_string, dpi):
        calls.append((svg_string, dpi))
        return _png_bytes()

    monkeypatch.setitem(sys.modules, "resvg_py", SimpleNamespace(svg_to_bytes=fake_svg_to_bytes))
    svg_parts._rasterize_subset_cached.cache_clear()
    svg_parts._parse.cache_clear()

    svg_parts.rasterize_subset(svg, "", ["arm"], 96.0)
    svg.write_text('<svg xmlns="http://www.w3.org/2000/svg"><rect id="arm"/><circle id="new"/></svg>', encoding="utf8")
    svg_parts.rasterize_subset(svg, "", ["arm"], 96.0)

    assert len(calls) == 2
