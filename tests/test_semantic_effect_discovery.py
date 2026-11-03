"""Only declared effect sheets contribute to the semantic effect vocabulary."""
from types import ModuleType, SimpleNamespace
from ambition_sprite2d_renderer.registry.discovery import _build_module_target


def test_a_drawing_helper_named_fx_does_not_declare_an_effect_sheet():
    module = SimpleNamespace(render=lambda out_dir: [], ROWS=[('a_pose', 1, 100)], FX=ModuleType('glyphs'))
    actor = _build_module_target(module, 'actor', 'props', 'fixture.actor', module.render)
    assert actor.semantic_effects == []
    module.FX = {'cue_family': 'sounds', 'residency': 'Core', 'fade': 'OverItsLife'}
    effect = _build_module_target(module, 'effect', 'props', 'fixture.effect', module.render)
    assert effect.semantic_effects == ['a_pose']
