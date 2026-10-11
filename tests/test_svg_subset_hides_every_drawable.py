"""A part renders WHAT IT CLAIMS, and nothing else.

⛔⛔ THE BUG THIS EXISTS FOR. `rasterize_subset` keeps the elements a part
includes and HIDES every other drawable — by tag, against `_DRAWABLE`. A tag
missing from that set is never hidden, so it survived into EVERY part and was
composited once per bone, each at that bone's transform.

`polyline` was missing. The Projectile Polygon's mouth line is the only polyline
in the shipped art, and he grew a fan of dark strokes across his face that got
worse the more his bones rotated — fifteen copies of one line, each following a
different limb. It read as an animation artifact, which is why it went unfound.

⭐ THE TEST IS PER-TAG AND EXHAUSTIVE ON PURPOSE. A test that only checked
`polyline` would pass forever while the next tag somebody draws with leaks the
same way.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ambition_sprite2d_renderer.authoring import svg_parts

#: Every tag that puts ink on the canvas, with a minimal instance of it.
INK = {
    "path": '<path id="{id}" d="M 10,10 L 40,10 L 40,40 Z" fill="#ff0000"/>',
    "polygon": '<polygon id="{id}" points="10,10 40,10 40,40" fill="#ff0000"/>',
    "polyline": '<polyline id="{id}" points="10,10 40,10 40,40" fill="none" '
    'stroke="#ff0000" stroke-width="4"/>',
    "rect": '<rect id="{id}" x="10" y="10" width="30" height="30" fill="#ff0000"/>',
    "ellipse": '<ellipse id="{id}" cx="25" cy="25" rx="15" ry="12" fill="#ff0000"/>',
    "circle": '<circle id="{id}" cx="25" cy="25" r="15" fill="#ff0000"/>',
    "line": '<line id="{id}" x1="10" y1="10" x2="40" y2="40" stroke="#ff0000" '
    'stroke-width="4"/>',
}


def _doc(tmp_path: Path, other: str) -> Path:
    svg = tmp_path / "subset.svg"
    svg.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" '
        'width="100mm" height="100mm" viewBox="0 0 100 100">'
        '<g inkscape:groupmode="layer" inkscape:label="side" id="side">'
        '<rect id="mine" x="60" y="60" width="20" height="20" fill="#00ff00"/>'
        f"{other}"
        "</g></svg>",
        encoding="utf8",
    )
    return svg


@pytest.mark.parametrize("tag", sorted(INK))
def test_a_tag_the_subset_does_not_claim_is_not_drawn(tmp_path: Path, tag: str) -> None:
    svg = _doc(tmp_path, INK[tag].format(id="theirs"))
    svg_parts._rasterize_subset_cached.cache_clear()
    image, _offset, _ppu = svg_parts.rasterize_subset(svg, "side", ["mine"], 96.0)
    assert image is not None, f"the claimed element vanished alongside the {tag}"
    colours = {px[:3] for px in image.convert("RGBA").get_flattened_data() if px[3] > 8}
    assert (255, 0, 0) not in colours, (
        f"a <{tag}> the part does not include was drawn into it; every part in the "
        f"document would carry a copy, each at its own bone's transform"
    )
    assert (0, 255, 0) in colours, "the part's own art did not render"


def test_every_ink_tag_this_test_knows_is_declared_drawable() -> None:
    """⛔ THE POISON. Drop a tag from `_DRAWABLE` and the parametrised test above
    still passes for the others — this is what says the SET is complete for
    everything the fixture can draw."""
    missing = sorted(set(INK) - set(svg_parts._DRAWABLE))
    assert not missing, f"tags that put ink on the canvas but are never hidden: {missing}"


def test_editor_expression_layer_visibility_does_not_remove_a_rig_part(tmp_path: Path) -> None:
    """Inkscape's alternative-layer toggles must not change rig sprite pixels."""
    source = (
        '<g id="facial-options" data-rig-editor-visibility="editor-only" style="display:none">'
        '<g id="face-a" data-rig-editor-visibility="editor-only" style="display:none">'
        '<ellipse id="my-eye" cx="24" cy="24" rx="8" ry="6" fill="#ff0000" />'
        '</g>'
        '<g id="face-b" data-rig-editor-visibility="editor-only">'
        '<rect id="other-eye" x="60" y="60" width="15" height="15" fill="#00ff00" />'
        '</g>'
        '</g>'
        '<g id="suppressed" style="display:none">'
        '<rect id="manually-hidden" x="50" y="20" width="10" height="10" fill="#0000ff" />'
        '</g>'
    )
    svg = _doc(tmp_path, source)
    hidden_variant, _, _ = svg_parts.rasterize_subset(svg, 'side', ['face-a'], 96.0)
    normal_variant, _, _ = svg_parts.rasterize_subset(svg, 'side', ['face-b'], 96.0)
    manual_hidden, _, _ = svg_parts.rasterize_subset(svg, 'side', ['suppressed'], 96.0)
    assert hidden_variant is not None and normal_variant is not None
    assert hidden_variant.getbbox() and normal_variant.getbbox()
    assert manual_hidden is None, 'non-editor hidden shapes must stay hidden'
    colors_a = {rgb[:3] for rgb in hidden_variant.get_flattened_data() if rgb[3] > 8}
    colors_b = {rgb[:3] for rgb in normal_variant.get_flattened_data() if rgb[3] > 8}
    assert (255, 0, 0) in colors_a and (0, 255, 0) not in colors_a
    assert (0, 255, 0) in colors_b and (255, 0, 0) not in colors_b
