"""A part is drawn from a document without the art of the other parts, and
its pixels are the same.

A part used to be drawn from the whole document with every other shape
hidden, written out for resvg twice. Two things now make it cheaper:
`_drop_hidden` removes each hidden subtree that nothing refers to, and
`_selective_subset` builds the part's document from one shared parse,
copying only the kept elements, their ancestors and what they refer to.
These tests hold both to the rule that the pixels do not change, and
`_drop_hidden` to its own rule about what it keeps.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from ambition_sprite2d_renderer.authoring import svg_parts

#: Two views. The part is a rect in "side" painted with a gradient that is
#: defined in the "front" layer (hidden for this part), and a `use` of a
#: shape that is also in "front"; "front" also holds art that nothing refers
#: to, and "side" a sibling that the part does not keep.
DOC = (
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
    'xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" '
    'width="100mm" height="100mm" viewBox="0 0 100 100">'
    '<g inkscape:groupmode="layer" inkscape:label="side" id="side">'
    '<g id="mine"><rect id="mine_body" x="10" y="10" width="60" height="60" fill="url(#shade)"/>'
    '<use id="mine_badge" xlink:href="#badge" x="20" y="20"/></g>'
    '<rect id="sibling" x="70" y="70" width="20" height="20" fill="#ff0000"/>'
    "</g>"
    '<g inkscape:groupmode="layer" inkscape:label="front" id="front">'
    '<linearGradient id="shade" x1="0" x2="1"><stop offset="0" stop-color="#00ff00"/>'
    '<stop offset="1" stop-color="#0000ff"/></linearGradient>'
    '<circle id="badge" cx="20" cy="20" r="6" fill="#ffff00"/>'
    '<g id="front_art"><path id="front_body" d="M 0,0 L 90,0 L 90,90 Z" fill="#ff0000"/></g>'
    "</g></svg>"
)


def _part(tmp_path: Path, monkeypatch, *, selective: bool, drop: bool) -> tuple:
    svg = tmp_path / "doc.svg"
    svg.write_text(DOC, encoding="utf8")
    with monkeypatch.context() as patch:
        if not selective:
            patch.setattr(svg_parts, "_INERT", set())
        if not drop:
            patch.setattr(svg_parts, "_drop_hidden", lambda root, keep: None)
        svg_parts._document.cache_clear()
        svg_parts._rasterize_subset_cached.cache_clear()
        try:
            image, offset, _ = svg_parts.rasterize_subset(svg, "side", ["mine"], 96.0)
        finally:
            svg_parts._document.cache_clear()
            svg_parts._rasterize_subset_cached.cache_clear()
    assert image is not None, "the part's own art did not render"
    return np.asarray(image.convert("RGBA")), offset


def test_each_way_of_drawing_a_part_gives_the_same_pixels(tmp_path: Path, monkeypatch) -> None:
    whole, whole_at = _part(tmp_path, monkeypatch, selective=False, drop=False)
    for name, kwargs in (("pruned", dict(selective=False, drop=True)), ("selective", dict(selective=True, drop=True))):
        pixels, at = _part(tmp_path, monkeypatch, **kwargs)
        assert at == whole_at, f"the {name} part is placed elsewhere"
        assert pixels.shape == whole.shape and np.array_equal(pixels, whole), f"the {name} part's pixels changed"
    # The part is painted by the gradient (green to blue) and has its badge
    # (yellow); the sibling and the other view's art (red) are not drawn.
    opaque = whole[whole[..., 3] > 200][:, :3]
    assert (opaque[:, 1] > 150).any() and (opaque[:, 2] > 150).any(), "the gradient did not paint the part"
    assert ((opaque[:, 0] > 200) & (opaque[:, 1] > 200) & (opaque[:, 2] < 80)).any(), "the used badge is missing"
    assert not ((opaque[:, 0] > 200) & (opaque[:, 1] < 60) & (opaque[:, 2] < 60)).any(), "art the part does not keep was drawn"


def test_the_selective_document_is_only_what_the_part_needs() -> None:
    doc = svg_parts._Document(DOC.encode("utf8"))
    assert doc.selective
    root, _keep = svg_parts._selective_subset(doc, "side", ("mine",))
    left = {node.get("id") for node in root.iter() if node.get("id")}
    assert {"mine", "mine_body", "side", "shade"} <= left, f"a kept or referenced element is missing: {left}"
    assert not {"front_art", "front_body"} & left, f"art that nothing refers to was copied: {left}"
    assert any(i.startswith("subset_ref_") for i in left), "the badge's `use` has no copy of its target"
    stops = [node for node in root.iter() if svg_parts._local(node.tag) == "stop"]
    assert len(stops) == 2, "the gradient lost its stops (they have no id of their own)"
    # The shared parse is not changed by drawing a part from it.
    assert not any("display:none" in (node.get("style") or "") for node in doc.root.iter())


def test_a_referenced_definition_stays_and_unreferenced_hidden_art_goes() -> None:
    import xml.etree.ElementTree as ET

    root = ET.fromstring(DOC)
    ids = {node.get("id"): node for node in root.iter() if node.get("id")}
    keep = {id(node) for node in ids["mine"].iter()} | {id(ids["side"]), id(root)}
    svg_parts._hide(ids["front"])
    svg_parts._hide(ids["sibling"])
    svg_parts._drop_hidden(root, keep)
    left = {node.get("id") for node in root.iter() if node.get("id")}
    assert {"mine", "side", "shade", "badge"} <= left, f"a kept or referenced element was removed: {left}"
    stops = [node for node in ids["shade"] if svg_parts._local(node.tag) == "stop"]
    assert len(stops) == 2, "a referenced gradient lost its stops (they have no id of their own)"
    assert not {"sibling", "front_art", "front_body"} & left, f"hidden art that nothing refers to stayed: {left}"
