"""Hand-drawn overlay art on generated characters (``chargen/overlay.py``)."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from ambition_sprite2d_renderer.chargen import overlay
from ambition_sprite2d_renderer.chargen.rig import draw_views
from ambition_sprite2d_renderer.chargen.spec import generate, validate
from ambition_sprite2d_renderer.targets.characters.townsfolk import SPECS, load


ART = """<svg xmlns="http://www.w3.org/2000/svg" data-overlay-ref="height:172 head:26.66">
  <g data-view="front">
    <g data-overlay-part="hair" data-overlay-mode="replace" data-overlay-anchor="neck" data-overlay-scale="height head"
       transform="translate(160,180)">
      <path d="m-10,-60 h20 v10 l-20,0 z" fill="#ff0000"/>
    </g>
    <g data-overlay-part="head" data-overlay-mode="over" data-overlay-anchor="neck" data-overlay-scale="height height">
      <path style="fill:#00ff00;stroke:#000000;stroke-width:2" d="M0,0 C1,1 2,2 3,3 S5,5 6,6 Z" transform="translate(1,2)"/>
    </g>
  </g>
</svg>
"""


@pytest.fixture
def art(tmp_path, monkeypatch):
    monkeypatch.setattr(overlay, "OVERLAYS", tmp_path)
    (tmp_path / "probe.overlay.svg").write_text(ART, encoding="utf8")
    return "probe"


def _human():
    spec = generate("average_male", 3, {"hair": {"style": "short"}, "body": {"height_cm": 172.0, "head": 0.155}})
    return spec


def test_relative_and_short_commands_become_absolute():
    segs = overlay.parse_d("m10,10 l5,0 h5 v5 c1,1 2,2 3,3 s1,1 2,2 q1,0 2,0 t2,0 z")
    assert segs[0] == ("M", [(10.0, 10.0)])
    assert segs[1] == ("L", [(15.0, 10.0)])
    assert segs[2] == ("L", [(20.0, 10.0)])
    assert segs[3] == ("L", [(20.0, 15.0)])
    assert segs[4] == ("C", [(21.0, 16.0), (22.0, 17.0), (23.0, 18.0)])
    # S reflects the last control point about the current point.
    assert segs[5] == ("C", [(24.0, 19.0), (24.0, 19.0), (25.0, 20.0)])
    assert segs[6][0] == "Q" and segs[7] == ("Q", [(28.0, 20.0), (29.0, 20.0)])
    assert segs[-1] == ("Z", [])


def test_arcs_are_refused():
    with pytest.raises(ValueError, match="arcs"):
        overlay.parse_d("M0,0 A5,5 0 0 1 10,0")


def test_replace_swaps_the_drawing_and_over_adds_a_part_on_the_bone(art):
    spec = _human()
    plain = {p.name: p for p in draw_views(spec)[1][0].parts}
    spec.overlay = art
    drawn = {p.name: p for p in draw_views(spec)[1][0].parts}
    assert [e.fill for e in drawn["hair"].els] == ["#ff0000"]
    assert (drawn["hair"].bone, drawn["hair"].z) == (plain["hair"].bone, plain["hair"].z)
    over = drawn["head__overlay"]
    assert over.bone == plain["head"].bone and over.z > plain["head"].z
    assert drawn["head"].els == plain["head"].els
    assert over.els[0].fill == "#00ff00" and over.els[0].width == pytest.approx(2.0)
    # Another view has no cell, so it draws as the generator does.
    side = {p.name: p for p in draw_views(spec)[1][2].parts}
    assert "head__overlay" not in side


def test_the_art_follows_the_measures_of_the_figure(art):
    spec = _human()
    spec.overlay = art
    tall = copy.deepcopy(spec)
    tall.body.height_cm = 172.0 * 1.1

    def width(s):
        hair = {p.name: p for p in draw_views(s)[1][0].parts}["hair"]
        xs = [float(t.split(",")[0].lstrip("MLZ")) for t in hair.els[0].d.split() if "," in t]
        return max(xs) - min(xs)

    assert width(tall) == pytest.approx(width(spec) * 1.1, rel=0.02)


def test_a_part_the_view_does_not_draw_is_an_error(art, tmp_path):
    (tmp_path / "probe.overlay.svg").write_text(ART.replace('data-overlay-part="hair"', 'data-overlay-part="no_such_part"'))
    spec = _human()
    spec.overlay = art
    with pytest.raises(ValueError, match="no_such_part"):
        draw_views(spec)


def test_an_unknown_overlay_does_not_validate():
    spec = _human()
    spec.overlay = "no_such_overlay"
    assert any("overlay" in e for e in validate(spec))


def test_a_spec_without_an_overlay_does_not_write_the_field():
    assert "overlay" not in _human().to_dict()


OVERLAID = sorted(p for p in SPECS.glob("*.chargen.yaml") if "overlay:" in p.read_text())


def test_nikobolt_and_coulomba_have_overlays():
    assert {p.name for p in OVERLAID} >= {"science_nikobolt.chargen.yaml", "science_coulomba.chargen.yaml"}


@pytest.mark.parametrize("path", OVERLAID, ids=lambda p: p.name.split(".")[0])
def test_a_resident_draws_its_overlay_in_every_view(path: Path):
    spec, _game = load(path)
    ov = overlay.load(spec.overlay)
    _fig, views = draw_views(spec)
    for dv in views:
        groups = {g.part: g for g in ov.cells[dv.view.key]}
        parts = {p.name: p for p in dv.parts}
        assert groups, dv.view.key
        for name, g in groups.items():
            if g.mode == "over":
                assert len(parts[name + "__overlay"].els) == len(g.els), (dv.view.key, name)
            elif g.els:
                assert len(parts[name].els) == len(g.els), (dv.view.key, name)
            else:
                assert name not in parts, (dv.view.key, name)
