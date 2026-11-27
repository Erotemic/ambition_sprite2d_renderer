"""Fire Elemental: a living flame with ember fists."""
from __future__ import annotations
from pathlib import Path
from ._elemental_enemy_family import ElementSpec, publish_spec

TARGET_NAME = 'fire_elemental'
SPEC = ElementSpec(
    target=TARGET_NAME,
    display_name='Fire Elemental',
    element='fire',
    traits=('elemental', 'fire', 'flame'),
    description='A horned living flame with a cinder mask, molten core, and tongues of fire that lash forward.',
    gameplay='A floating aggressive enemy that bunches up, surges forward and scorches with a fast fiery lash.',
    run_speed=120.0,
    move_style='Float',
    body_kind='Floating',
    mass_class='Light',
    floating=True,
    attack_preset='fire_elemental_scorch',
    standing_height=70.0,
    box=(102, 26, 216, 242),
    timing=(0.48, 0.16, 0.62),
)

def render(out_dir: str | Path, **opts):
    return publish_spec(SPEC, out_dir, **opts)
