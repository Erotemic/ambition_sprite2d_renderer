"""Air Elemental: a cloud-whorl spirit with gusting limbs."""
from __future__ import annotations
from pathlib import Path
from ._elemental_enemy_family import ElementSpec, publish_spec

TARGET_NAME = 'air_elemental'
SPEC = ElementSpec(
    target=TARGET_NAME,
    display_name='Air Elemental',
    element='air',
    traits=('elemental', 'air', 'wind'),
    description='A storm djinn made of layered clouds and a coiling tornado, with narrow luminous eyes and unfurling gust ribbons.',
    gameplay='A light floating enemy that drifts into range, gathers itself and lashes forward with a cutting gust.',
    run_speed=110.0,
    move_style='Float',
    body_kind='Floating',
    mass_class='Light',
    floating=True,
    attack_preset='air_elemental_gust',
    standing_height=58.0,
    box=(94, 54, 211, 259),
    timing=(0.52, 0.18, 0.68),
)

def render(out_dir: str | Path, **opts):
    return publish_spec(SPEC, out_dir, **opts)
