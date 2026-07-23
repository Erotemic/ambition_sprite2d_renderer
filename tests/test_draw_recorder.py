"""Tests for the PIL->SVG draw recorder and the pirate SVG-authority render.

The unit tests need only stdlib (they inspect the emitted SVG string). The
fidelity/port tests rasterize through resvg and render a real target, so they
skip cleanly where those heavier deps are unavailable.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from ambition_sprite2d_renderer.authoring.draw_recorder import DrawRecorder


def _svg_root(rec: DrawRecorder) -> ET.Element:
    return ET.fromstring(rec.to_svg())


def test_primitives_map_to_svg_elements() -> None:
    rec = DrawRecorder((64, 48))
    rec.polygon([(1, 2), (3, 4), (5, 6)], fill=(200, 10, 20, 255))
    rec.line([(0, 0), (10, 10)], fill=(0, 0, 0, 255), width=3)
    rec.ellipse((2, 2, 12, 22), fill=(1, 2, 3, 128), outline=(0, 0, 0, 255), width=2)
    root = _svg_root(rec)
    tags = [el.tag.rsplit("}", 1)[-1] for el in root.iter()]
    assert tags.count("polygon") == 1
    assert tags.count("polyline") == 1
    assert tags.count("ellipse") == 1
    assert root.get("viewBox") == "0 0 64 48"


def test_ellipse_center_and_radii() -> None:
    rec = DrawRecorder((32, 32))
    rec.ellipse((2, 4, 12, 24), fill=(0, 0, 0, 255))
    el = next(e for e in _svg_root(rec).iter() if e.tag.endswith("ellipse"))
    assert el.get("cx") == "7" and el.get("cy") == "14"
    assert el.get("rx") == "5" and el.get("ry") == "10"


def test_translucent_fill_emits_opacity() -> None:
    rec = DrawRecorder((8, 8))
    rec.polygon([(0, 0), (8, 0), (8, 8)], fill=(255, 255, 255, 90))
    poly = next(e for e in _svg_root(rec).iter() if e.tag.endswith("polygon"))
    assert poly.get("fill") == "rgb(255,255,255)"
    assert abs(float(poly.get("fill-opacity")) - 90 / 255) < 1e-3


def test_component_scope_wraps_in_group() -> None:
    rec = DrawRecorder((16, 16))
    with rec.component("hat"):
        rec.polygon([(0, 0), (4, 0), (4, 4)], fill=(1, 1, 1, 255))
    groups = [e for e in _svg_root(rec).iter() if e.tag.endswith("}g")]
    assert len(groups) == 1
    assert groups[0].get("{http://www.inkscape.org/namespaces/inkscape}label") == "hat"


def test_arc_is_sampled_as_polyline() -> None:
    rec = DrawRecorder((100, 100))
    rec.arc((0, 0, 100, 100), start=0, end=90, fill=(255, 255, 255, 255), width=4)
    lines = [e for e in _svg_root(rec).iter() if e.tag.endswith("polyline")]
    assert len(lines) == 1
    assert len(lines[0].get("points").split()) >= 3  # sampled into segments


# -- resvg / target-render gated --------------------------------------------


def test_pirate_capture_is_faithful_at_supersample() -> None:
    """A captured pirate frame rasterizes back within edge tolerance at 512."""
    pytest.importorskip("resvg_py")
    from unittest import mock

    from PIL import ImageChops

    import ambition_sprite2d_renderer.targets.characters._pirate_common as pc
    from ambition_sprite2d_renderer.authoring.draw_recorder import rasterize_svg

    with mock.patch.object(pc, "downsample", lambda img, final_size=None: img):
        pil = pc.draw_character("pirate_raider", "idle", 0, 6)  # 512, no downsample
    svg = pc.capture_character_svg("pirate_raider", "idle", 0, 6)
    ras = rasterize_svg(svg, pil.size)

    diff = ImageChops.difference(pil, ras)
    merged = diff.split()[0]
    for band in diff.split()[1:]:
        merged = ImageChops.lighter(merged, band)
    total = pil.size[0] * pil.size[1]
    over = sum(merged.histogram()[9:]) / total  # pixels differing by > 8
    assert over < 0.03, f"capture drifted {over:.2%} of pixels beyond edge tol"


@pytest.mark.parametrize("target", ["pirate_raider", "pirate_admiral", "pirate_lookout"])
def test_pirate_svg_authority_matches_contract(tmp_path: Path, target: str) -> None:
    """Every pirate publishes the same contract from its SVG authority."""
    pytest.importorskip("resvg_py")

    import ambition_sprite2d_renderer.targets.characters._pirate_common as pc
    from ambition_sprite2d_renderer.core.equivalence import (
        CONTRACT, EXACT, RASTER, compare_renders, load_render,
    )

    pil_dir, svg_dir = tmp_path / "pil", tmp_path / "svg"
    pc.render_target(target, pil_dir)
    pc.render_target_svg(target, svg_dir)
    rep = compare_renders(load_render(pil_dir), load_render(svg_dir))
    assert rep.structural_ok, [d.diffs for d in rep.dimensions if not d.ok]
    assert rep.verdict in (EXACT, RASTER, CONTRACT)


def test_captured_svg_has_named_component_layers() -> None:
    import xml.etree.ElementTree as ET

    import ambition_sprite2d_renderer.targets.characters._pirate_common as pc

    svg = pc.capture_character_svg("pirate_raider", "idle", 0, 6)
    ink = "{http://www.inkscape.org/namespaces/inkscape}label"
    labels = {g.get(ink) for g in ET.fromstring(svg).iter() if g.tag.endswith("}g")}
    assert {"legs", "body", "arms", "head"} <= labels


def test_part_scope_registers_and_places() -> None:
    rec = DrawRecorder((64, 64))
    for _frame in range(3):
        with rec.part("hat", (10, 20), 15.0):
            rec.polygon([(0, 0), (4, 0), (2, 4)], fill=(1, 2, 3, 255))
    assert len(rec.part_defs) == 1          # identical geometry -> ONE def
    svg = rec.to_svg()
    assert svg.count("<use ") == 3          # ...placed three times
    assert "<defs>" in svg and "rotate(15)" in svg


def test_pillow_part_draw_matches_world_math() -> None:
    from ambition_sprite2d_renderer.authoring.draw_recorder import PillowPartDraw
    from ambition_sprite2d_renderer.authoring.sheet_build import transform

    captured = {}

    class Spy:
        def polygon(self, pts, fill=None):
            captured["pts"] = pts

    d = PillowPartDraw(Spy())
    origin, deg = (37.5, 91.25), 23.0
    local = [(-4.0, 2.5), (6.0, -3.25)]
    with d.part("x", origin, deg):
        d.polygon(local, fill=None)
    want = [transform(p, origin, deg=deg) for p in local]
    assert captured["pts"] == want          # byte-faithful to the old math


def test_component_scene_round_trips(tmp_path: Path) -> None:
    import ambition_sprite2d_renderer.targets.characters._pirate_common as pc
    from ambition_sprite2d_renderer.authoring.svg_scene import ComponentScene

    scene = pc.build_scene("pirate_raider")
    stats = scene.stats()
    assert stats["parts"] >= 8 and stats["frames"] == 38
    assert stats["part_uses"] > stats["parts"]   # real reuse across frames
    path = scene.save(tmp_path / "pirate_raider.svg")
    loaded = ComponentScene.load(path)
    assert loaded.stats() == stats
    assert loaded.missing_part_refs() == []
    # every frame doc is standalone-renderable XML with defs + uses
    doc = loaded.frame_doc("idle", 0)
    import xml.etree.ElementTree as ET
    root = ET.fromstring(doc)
    assert any(el.tag.endswith("defs") for el in root)


def test_part_edit_propagates_to_frames(tmp_path: Path) -> None:
    """The human-loop property: edit ONE part in the scene file, every frame
    that uses it changes."""
    import re

    import ambition_sprite2d_renderer.targets.characters._pirate_common as pc
    from ambition_sprite2d_renderer.authoring.svg_scene import ComponentScene

    path = pc.export_scene("pirate_raider", tmp_path / "s.svg")
    text = path.read_text()
    m = re.search(r'<g id="(part_hat_[a-f0-9]+)"', text)
    assert m
    edited = tmp_path / "edited.svg"
    edited.write_text(text.replace("rgb(31,23,32)", "rgb(96,40,160)"))
    a, b = ComponentScene.load(path), ComponentScene.load(edited)
    changed = sum(
        1 for key in a.frames
        if a.frame_doc(*key) != b.frame_doc(*key)
    )
    assert changed == len(a.frames)         # hat used in every frame
