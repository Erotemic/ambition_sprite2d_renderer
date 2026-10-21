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
        svg_parts._render_kept = lambda root, keep, d: svg_parts._render_full(root, d)
        full = raw(*args)
    finally:
        svg_parts._render_kept = full_render
    assert windowed[1] == full[1]
    assert windowed[0].size == full[0].size
    diff = np.abs(np.asarray(windowed[0]).astype(int) - np.asarray(full[0]).astype(int))
    # Only the rounding of resvg's single-precision transform, at an edge.
    assert diff.max() <= 16
