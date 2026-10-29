"""An effect sheet says so in its record (`SheetRecord::fx`): the game finds
its effect sheets there, so a new one is a publish and no Rust edit."""

from __future__ import annotations

import importlib

import pytest

from ambition_sprite2d_renderer.authoring.sheet_build import _checked_fx
from ambition_sprite2d_renderer.core.manifest_ron import record_to_ron

FX_TARGETS = [
    "generic_action_fx", "generic_world_fx", "generic_exotic_fx", "generic_explosions",
    "george_booul_vfx", "oiler_vfx", "pirate_admiral_vfx", "ninja_shadow_oni_leader_vfx",
    "pca_vfx", "patent_clerk_vfx", "carl_stargan_vfx", "noether_vfx", "gnu_ton_vfx",
    "projectile_polygon_vfx", "ninja_kagero_vfx",
]


def _record(**extra):
    return {"target": "t", "frame_width": 8, "frame_height": 8, "rows": [], **extra}


def test_an_effect_sheet_record_states_its_facts_and_another_does_not():
    fx = {"cue_family": "explosion", "residency": "Core", "fade": "OverItsLife"}
    ron = record_to_ron(_record(fx=fx))
    assert 'fx: Some((cue_family: "explosion", residency: Core, fade: OverItsLife)),' in ron
    # The control: a sheet that declares nothing emits nothing.
    assert "fx:" not in record_to_ron(_record())


@pytest.mark.parametrize("field, value", [("residency", "Resident"), ("fade", "Slowly"), ("cue_family", " ")])
def test_a_bad_fact_is_refused_with_its_field(field, value):
    fx = {"cue_family": "explosion", "residency": "Core", "fade": "OverItsLife", field: value}
    with pytest.raises(ValueError, match=f"fx.{field}"):
        _checked_fx(fx, "t")


@pytest.mark.parametrize("target", FX_TARGETS)
def test_each_effect_target_declares_its_facts(target):
    module = importlib.import_module(f"ambition_sprite2d_renderer.targets.props.{target}")
    assert _checked_fx(module.FX, target) == module.FX
