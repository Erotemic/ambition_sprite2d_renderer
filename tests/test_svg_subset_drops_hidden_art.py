"""A part is drawn from the document with the rest of the art removed, not
only hidden, and its pixels are the same.

`_drop_hidden` removes each `display:none` subtree before the document is
written for resvg: writing the hidden art (every other view and part) was
most of the cost of a part. These tests hold it to its rule: the pixels do
not change, a hidden subtree that something refers to stays, and the
hidden art that nothing refers to goes.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from ambition_sprite2d_renderer.authoring import svg_parts

#: Two views. The part is a rect in "side" painted with a gradient that is
#: defined in the "front" layer (hidden for this part); "front" also holds
#: art that nothing refers to.
DOC = (
    '<svg xmlns="http://www.w3.org/2000/svg" '
    'xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" '
    'width="100mm" height="100mm" viewBox="0 0 100 100">'
    '<g inkscape:groupmode="layer" inkscape:label="side" id="side">'
    '<rect id="mine" x="10" y="10" width="60" height="60" fill="url(#shade)"/>'
    '<rect id="sibling" x="70" y="70" width="20" height="20" fill="#ff0000"/>'
    "</g>"
    '<g inkscape:groupmode="layer" inkscape:label="front" id="front">'
    '<linearGradient id="shade" x1="0" x2="1"><stop offset="0" stop-color="#00ff00"/>'
    '<stop offset="1" stop-color="#0000ff"/></linearGradient>'
    '<g id="front_art"><path id="front_body" d="M 0,0 L 90,0 L 90,90 Z" fill="#ff0000"/></g>'
    "</g></svg>"
)


def _part(tmp_path: Path, drop: bool, monkeypatch) -> np.ndarray:
    svg = tmp_path / "doc.svg"
    svg.write_text(DOC, encoding="utf8")
    if not drop:
        monkeypatch.setattr(svg_parts, "_drop_hidden", lambda root, keep: None)
    svg_parts._rasterize_subset_cached.cache_clear()
    try:
        image, offset, _ = svg_parts.rasterize_subset(svg, "side", ["mine"], 96.0)
    finally:
        svg_parts._rasterize_subset_cached.cache_clear()
        monkeypatch.undo()
    assert image is not None, "the part's own art did not render"
    return np.asarray(image.convert("RGBA")), offset


def test_dropping_the_hidden_art_changes_no_pixel(tmp_path: Path, monkeypatch) -> None:
    kept, kept_at = _part(tmp_path, False, monkeypatch)
    dropped, dropped_at = _part(tmp_path, True, monkeypatch)
    assert dropped_at == kept_at
    assert dropped.shape == kept.shape
    assert np.array_equal(dropped, kept), "removing the hidden art changed the part's pixels"
    # The part is painted by the gradient (green to blue), not left unpainted.
    assert (dropped[..., 3] > 8).sum() > 0
    assert dropped[..., 1].max() > 100 and dropped[..., 2].max() > 100


def test_a_referenced_definition_stays_and_unreferenced_hidden_art_goes() -> None:
    import xml.etree.ElementTree as ET

    root = ET.fromstring(DOC)
    ids = {node.get("id"): node for node in root.iter() if node.get("id")}
    keep = {id(node) for node in ids["mine"].iter()} | {id(ids["side"]), id(root)}
    for name in ("front",):
        svg_parts._hide(ids[name])
    svg_parts._hide(ids["sibling"])
    svg_parts._drop_hidden(root, keep)
    left = {node.get("id") for node in root.iter() if node.get("id")}
    assert {"mine", "side", "shade"} <= left, f"a kept or referenced element was removed: {left}"
    stops = [node for node in ids["shade"] if svg_parts._local(node.tag) == "stop"]
    assert len(stops) == 2, "a referenced gradient lost its stops (they have no id of their own)"
    assert not {"sibling", "front_art", "front_body"} & left, f"hidden art that nothing refers to stayed: {left}"
