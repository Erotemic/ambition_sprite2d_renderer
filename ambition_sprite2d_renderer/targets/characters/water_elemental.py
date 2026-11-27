"""Water Elemental: a cresting wave spirit."""
from __future__ import annotations
from pathlib import Path
from ._elemental_enemy_family import ElementSpec, publish_spec

TARGET_NAME = 'water_elemental'
SPEC = ElementSpec(
    target=TARGET_NAME,
    display_name='Water Elemental',
    element='water',
    traits=('elemental', 'water', 'wave'),
    description='A serpentine breaking wave with a curled foam crest, a dark current for a face, and a sweeping wave arm.',
    gameplay='A floating medium enemy that sloshes forward, bunches like a wave and surges with a watery slap.',
    run_speed=108.0,
    move_style='Float',
    body_kind='Floating',
    mass_class='Medium',
    floating=True,
    attack_preset='water_elemental_surge',
    standing_height=64.0,
    box=(91, 65, 218, 253),
    timing=(0.56, 0.18, 0.72),
)

def render(out_dir: str | Path, **opts):
    return publish_spec(SPEC, out_dir, **opts)
