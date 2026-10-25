"""The gate's dialing glyphs: fifteen symbols, each its own shape."""

from __future__ import annotations

from ambition_sprite2d_renderer.glyphs.legally_distinct import CAP, GLYPHS, contours, render_glyph, spell


def test_every_chevron_is_its_own_symbol():
    assert "".join(g.letter for g in GLYPHS) == "ΛΕΓΑΛΛΥΔΙΣΤΙΝΧΤ"
    assert len({g.id for g in GLYPHS}) == 15
    pictures = {render_glyph(g, 48, "#ffffff").getchannel("A").tobytes() for g in GLYPHS}
    assert len(pictures) == 15, "two chevrons draw the same picture"


def test_the_ink_sits_between_the_baseline_and_the_cap_height():
    for glyph in GLYPHS:
        points = [p for contour in contours(glyph) for p in contour]
        ys = [y for _, y in points]
        xs = [x for x, _ in points]
        assert min(ys) >= -0.5 and max(ys) <= CAP + 0.5, glyph.id
        assert min(xs) >= -0.5 and max(xs) <= glyph.width + 0.5, glyph.id


def test_legally_distinct_spells_the_chevrons_in_order():
    assert spell("LEGALLY DISTINCT") == list(GLYPHS)
