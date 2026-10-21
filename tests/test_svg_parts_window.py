"""A part is drawn in a window about its paint, not over the whole canvas
(`svg_parts._render_kept`). The window must hold all of the paint: a part drawn
in it has the size and the offset of the same part drawn over the canvas."""

from __future__ import annotations

import numpy as np
import pytest

resvg_py = pytest.importorskip("resvg_py")

from ambition_sprite2d_renderer.authoring import svg_parts  # noqa: E402

# A large canvas (a sheet of many views) with one small part far from its
# origin. The part is a path drawn only as a wide stroke: the coarse pass once
# set each stroke to a fixed narrow width, and cut such a leg off.
SVG = """<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
  width="2400mm" height="1200mm" viewBox="0 0 2400 1200">
  <g inkscape:label="View" inkscape:groupmode="layer" transform="translate(1700,800)">
    <path id="leg" d="M 0 0 Q 5 18 7 37" fill="none" stroke="#17120e" stroke-width="18" stroke-linecap="round"/>
    <circle id="dot" cx="40" cy="10" r="0.6" fill="#f00" fill-opacity="0.2"/>
    <rect id="other" x="-1600" y="-700" width="30" height="30" fill="#00f"/>
  </g>
</svg>"""


@pytest.mark.parametrize("ids", [("leg",), ("leg", "dot")])
def test_a_windowed_part_matches_the_full_canvas(tmp_path, ids):
    path = tmp_path / "sheet.svg"
    path.write_text(SVG)
    dpi = 25.4 * 4.0
    raw = svg_parts._rasterize_subset_cached.__wrapped__
    st = path.stat()
    args = (str(path), st.st_mtime_ns, st.st_size, "View", ids, dpi)
    windowed = raw(*args)
    full_render = svg_parts._render_kept
    try:
        svg_parts._render_kept = lambda root, keep, d, origin=None: svg_parts._render_full(root, d)
        full = raw(*args)
    finally:
        svg_parts._render_kept = full_render
    assert windowed[1] == full[1]
    assert windowed[0].size == full[0].size
    diff = np.abs(np.asarray(windowed[0]).astype(int) - np.asarray(full[0]).astype(int))
    # Only the rounding of resvg's single-precision transform, at an edge.
    assert diff.max() <= 16


def test_a_view_with_a_pixel_origin_keeps_its_pixels_when_its_cell_moves(tmp_path):
    """A view layer's `data-rig-pixel-origin` is in the layer's own
    coordinates: a layer moved on the canvas by a distance that is not a whole
    number of output pixels draws its part on the same pixels, at the same
    offset from its origin."""
    layer = """<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
      width="400mm" height="200mm" viewBox="0 0 400 200">
      <g inkscape:label="View" inkscape:groupmode="layer" transform="translate(%s,0)" data-rig-pixel-origin="0 0">
        <path id="leg" d="M 30 40 Q 35 58 37 77" fill="none" stroke="#17120e" stroke-width="18" stroke-linecap="round"/>
      </g>
    </svg>"""
    dpi = 25.4 * 4.64  # not a whole number of pixels to the unit
    drawn = []
    for dx in ("0", "101.3"):
        path = tmp_path / f"sheet_{dx}.svg"
        path.write_text(layer % dx)
        origin = svg_parts.view_pixel_origin(path, "View")
        assert origin == (float(dx), 0.0)
        drawn.append(svg_parts.rasterize_subset(path, "View", ["leg"], dpi, origin))
    (a, off_a, _), (b, off_b, _) = drawn
    assert off_a == off_b
    assert a.size == b.size
    assert np.abs(np.asarray(a).astype(int) - np.asarray(b).astype(int)).max() <= 16
