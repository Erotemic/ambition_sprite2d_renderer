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


def _install_fake_resvg(monkeypatch, svg_parts, fake) -> None:
    """Make the rasterizer call `fake` instead of the real compiled resvg.

    ⛔⛔ **patching `sys.modules["resvg_py"]` alone stopped working and is why
    these two tests were red.** `_native_resvg_callable` deliberately requires
    `inspect.isbuiltin` — *"never a Python compatibility shim"* — so a fake
    written in Python is REFUSED by design, the rasterizer falls through to
    CairoSVG, and in an environment without it the test dies with *"SVG sprite
    rendering requires native resvg-py"*. That message named the wrong cause:
    `resvg_py` was installed the whole time.

    ⭐ so the seam to patch is the DETECTOR, not the module table. These tests
    are about the raster CACHE; which callable counts as native is a different
    rule with its own test below, and weakening it to let a fake through would
    have deleted a real guarantee to make a green light.
    """
    monkeypatch.setitem(sys.modules, "resvg_py", SimpleNamespace(svg_to_bytes=fake))
    monkeypatch.setattr(
        svg_parts, "_native_resvg_callable", lambda module: getattr(module, "svg_to_bytes", None)
    )


def test_only_the_compiled_resvg_counts_as_native() -> None:
    """**The rule the two cache tests were accidentally leaning on.**

    A Python callable named `svg_to_bytes` must NOT be mistaken for the native
    rasterizer: the fallback's own doc says its antialiasing differs and that
    *"callers must not mistake fallback pixels for canonical publication
    output"*. Nothing asserted that until now, which is how the cache tests
    could depend on it, break when it tightened, and read as an environment
    problem.
    """
    from ambition_sprite2d_renderer.authoring import svg_parts

    def python_shim(*, svg_string, dpi):  # pragma: no cover - never called
        return b""

    assert svg_parts._native_resvg_callable(SimpleNamespace(svg_to_bytes=python_shim)) is None
    assert svg_parts._native_resvg_callable(SimpleNamespace()) is None
    # `len` stands in for any compiled builtin; the check is on HOW it is
    # implemented, not on what it does.
    assert svg_parts._native_resvg_callable(SimpleNamespace(svg_to_bytes=len)) is len


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

    _install_fake_resvg(monkeypatch, svg_parts, fake_svg_to_bytes)
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

    _install_fake_resvg(monkeypatch, svg_parts, fake_svg_to_bytes)
    svg_parts._rasterize_subset_cached.cache_clear()
    svg_parts._parse.cache_clear()

    svg_parts.rasterize_subset(svg, "", ["arm"], 96.0)
    svg.write_text('<svg xmlns="http://www.w3.org/2000/svg"><rect id="arm"/><circle id="new"/></svg>', encoding="utf8")
    svg_parts.rasterize_subset(svg, "", ["arm"], 96.0)

    assert len(calls) == 2
