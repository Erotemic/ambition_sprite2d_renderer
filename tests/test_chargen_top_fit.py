from __future__ import annotations

from ambition_sprite2d_renderer.chargen.body import build
from ambition_sprite2d_renderer.chargen.drawkit import make_ctx
from ambition_sprite2d_renderer.chargen.geometry import VIEW_BY_KEY
from ambition_sprite2d_renderer.chargen.spec import CharacterSpec, TOP_FITS, generate
from ambition_sprite2d_renderer.chargen.svgout import Canvas
from ambition_sprite2d_renderer.chargen.wear import top_profile, top_shell


def _shell(spec: CharacterSpec):
    fig = build(spec)
    ctx = make_ctx(fig, VIEW_BY_KEY['front'], Canvas(1, (0, 0)))
    profile = top_profile(fig, ctx)
    return fig, ctx, profile, top_shell(fig, ctx.plan, profile)


def test_top_fit_schema_roundtrip():
    spec = generate('average_male', 3, {'outfit': {'top_fit': 'baggy', 'top_bagginess': 0.6}})
    data = spec.to_dict()
    assert data['outfit']['top_fit'] == 'baggy'
    assert data['outfit']['top_bagginess'] == 0.6
    restored = CharacterSpec.from_dict(data)
    assert restored.outfit.top_fit == 'baggy'
    assert restored.outfit.top_bagginess == 0.6
    assert 'auto' in TOP_FITS


def test_bagginess_widens_top_shell_and_relaxes_bumps():
    base = generate('average_female', 5, {'outfit': {'top': 'shirt', 'tucked': False, 'top_fit': 'fitted'}})
    loose = generate('average_female', 5, {'outfit': {'top': 'shirt', 'tucked': False, 'top_fit': 'baggy', 'top_bagginess': 1.0}})
    fig0, ctx0, p0, sh0 = _shell(base)
    fig1, ctx1, p1, sh1 = _shell(loose)
    y = fig0.y_waist
    sec0, sec1 = sh0.section(y), sh1.section(y)
    assert sec1.rx > sec0.rx + 0.5 * fig0.k
    assert sec1.rzf > sec0.rzf + 0.5 * fig0.k
    assert p1.cling < p0.cling
    assert ctx1.plan['top_hem'] == ctx0.plan['top_hem']


def test_auto_profile_makes_sweater_looser_than_tshirt():
    tshirt = generate('average_male', 9, {'outfit': {'top': 'tshirt', 'sleeves': 'short'}})
    sweater = generate('average_male', 9, {'outfit': {'top': 'sweater', 'sleeves': 'long'}})
    fig_t, ctx_t, profile_t, _ = _shell(tshirt)
    fig_s, ctx_s, profile_s, _ = _shell(sweater)
    assert profile_s.sleeve_add > profile_t.sleeve_add
    assert profile_s.chest > profile_t.chest
    assert fig_s.y_chest == fig_t.y_chest


def test_garment_profiles_cover_the_body_and_each_other():
    import math
    from ambition_sprite2d_renderer.chargen.garment import fitted_top, outer_shell
    from ambition_sprite2d_renderer.chargen.spec import BASES

    for base in BASES:
        for fit in ('fitted', 'regular', 'relaxed', 'baggy'):
            for tucked in (False, True):
                spec = generate(base, 13, {'outfit': {'top': 'shirt', 'top_fit': fit,
                    'top_bagginess': 0.8, 'outer': 'jacket', 'tucked': tucked}})
                fig = build(spec)
                ctx = make_ctx(fig, VIEW_BY_KEY['front'], Canvas(1, (0, 0)))
                _, shirt = fitted_top(ctx)
                coat = outer_shell(ctx)
                for j in range(17):
                    y = fig.torso.top + (fig.torso.bottom - fig.torso.top) * j / 16
                    for alpha in range(0, 360, 15):
                        a = math.radians(alpha)
                        for inside, outside in ((fig.torso, shirt), (shirt, coat)):
                            x, _, z = inside.point(alpha, y)
                            X, _, Z = outside.point(alpha, y)
                            assert (X-x)*math.sin(a) >= -1e-8, (base, fit, tucked, y, alpha)
                            assert (Z-z)*math.cos(a) >= -1e-8, (base, fit, tucked, y, alpha)


def test_shoulder_backings_share_the_sleeve_bone_and_feature():
    from ambition_sprite2d_renderer.chargen.rig import draw_views
    spec = generate('average_female', 4, {'outfit': {'top': 'shirt', 'top_fit': 'baggy',
                    'sleeves': 'long', 'outer': 'none', 'wardrobe': ['top:sweater']}})
    _, views = draw_views(spec, [VIEW_BY_KEY['front'], VIEW_BY_KEY['side']])
    for view in views:
        parts = {p.name: p for p in view.parts}
        for suffix in ('', '@sweater'):
            sleeve = parts['near_arm_u__top'+suffix]
            backing = parts['near_arm_u__top_backing'+suffix]
            assert sleeve.bone == backing.bone
            assert sleeve.feature == backing.feature
            assert backing.z < parts['torso__top'].z < sleeve.z
        if view.view.key == 'side':
            assert 'far_arm_u__top_backing' not in parts


def test_fit_controls_are_available_for_default_valued_specs():
    from ambition_sprite2d_renderer.chargen.studio import schema
    spec = generate('average_male', 4).to_dict()
    assert 'top_fit' not in spec['outfit'] and 'top_bagginess' not in spec['outfit']
    sc = schema()
    assert sc['optional_defaults']['outfit.top_fit'] == 'auto'
    assert sc['optional_defaults']['outfit.top_bagginess'] == 0.0
    assert sc['choices']['outfit.top_fit'] == list(TOP_FITS)
    assert sc['bounds']['outfit.top_bagginess'] == [0.0, 1.0]
