"""The projected hip geometry and the layered legwear authoring contract."""
from __future__ import annotations

import math

import pytest

from ambition_sprite2d_renderer.chargen import overlay
from ambition_sprite2d_renderer.chargen.body import build
from ambition_sprite2d_renderer.chargen.drawkit import hip_opening, make_ctx, thigh_radius
from ambition_sprite2d_renderer.chargen.geometry import VIEWS, VIEW_BY_KEY
from ambition_sprite2d_renderer.chargen.rig import draw_views
from ambition_sprite2d_renderer.chargen.spec import BASES, generate
from ambition_sprite2d_renderer.chargen.svgout import Canvas


def test_hip_profile_is_smooth_and_view_consistent():
    for base in BASES:
        for family in ('standard', 'crew'):
            fig = build(generate(base, 11, {'family': family}))
            for view in VIEWS:
                radius = thigh_radius(make_ctx(fig, view, Canvas(1, (0, 0))))
                assert radius == pytest.approx(math.hypot(view.c * fig.leg_r[0], view.s * fig.thigh_depth))
                assert min(fig.leg_r[0], fig.thigh_depth) - 1e-9 <= radius <= max(fig.leg_r[0], fig.thigh_depth) + 1e-9
            edge = hip_opening(fig)
            under = hip_opening(fig, overlap=-0.9 * fig.k)
            for a in range(-180, 181, 15):
                assert edge(a, fig.y_hip) == pytest.approx(edge(-a, fig.y_hip))
                assert edge(a, fig.y_hip) - under(a, fig.y_hip) == pytest.approx(0.9 * fig.k)
            upper, lower = fig.torso.section(fig.y_hipw), fig.torso.section(fig.y_crotch)
            for key in ('rx', 'rzf', 'rzb'):
                assert 0 < getattr(lower, key) <= getattr(upper, key)


@pytest.mark.parametrize('bottom', ['trousers', 'shorts'])
@pytest.mark.parametrize('tucked', [True, False])
def test_hip_outline_and_fill_share_a_bone_and_feature(bottom, tucked):
    spec = generate('average_male', 4, {'outfit': {'bottom': bottom, 'tucked': tucked, 'top': 'shirt'}})
    _, views = draw_views(spec, [VIEW_BY_KEY['front'], VIEW_BY_KEY['side']])
    for view in views:
        parts = {p.name: p for p in view.parts}
        front, back = parts['pelvis__legwear'], parts['pelvis__legwear_backing']
        assert front.feature == back.feature == 'legwear:' + bottom
        assert front.bone == back.bone == 'pelvis'
        assert back.backing_for == front.name
        for depth in ('near', 'far'):
            assert back.z < parts[f'{depth}_leg_u__legwear'].z < front.z


def test_wardrobe_alternate_has_its_own_backing():
    spec = generate('average_female', 11, {'outfit': {'bottom': 'skirt', 'wardrobe': ['legwear:trousers']}})
    _, views = draw_views(spec, [VIEW_BY_KEY['front']])
    parts = {p.name: p for p in views[0].parts}
    assert 'pelvis__legwear_backing' not in parts
    backing = parts['pelvis__legwear_backing@trousers']
    assert backing.feature == parts['pelvis__legwear@trousers'].feature == 'legwear:trousers'


@pytest.mark.parametrize('mode', ['replace', 'over'])
def test_overlay_owns_replaced_silhouette_only(tmp_path, monkeypatch, mode):
    monkeypatch.setattr(overlay, 'OVERLAYS', tmp_path)
    (tmp_path / 'probe.overlay.svg').write_text(f'''<svg xmlns="http://www.w3.org/2000/svg" data-overlay-ref="height:172">
      <g data-view="front"><g data-overlay-part="pelvis__legwear" data-overlay-mode="{mode}"
      data-overlay-anchor="waist" data-overlay-scale="height height"><path d="M0,0 L10,0 L10,10 Z" fill="#004466"/></g></g>
      </svg>''')
    spec = generate('average_male', 4, {'outfit': {'bottom': 'trousers'}})
    spec.overlay = 'probe'
    _, views = draw_views(spec, [VIEW_BY_KEY['front'], VIEW_BY_KEY['side']])
    for view in views:
        names = {p.name for p in view.parts}
        assert ('pelvis__legwear_backing' in names) == (mode == 'over' or view.view.key == 'side')
