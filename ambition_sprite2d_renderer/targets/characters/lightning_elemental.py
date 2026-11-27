
"""Lightning Elemental: a storm-wraith of living arcs."""
from __future__ import annotations
from pathlib import Path
from ._elemental_enemy_family import ElementSpec, publish_spec

TARGET_NAME = 'lightning_elemental'
SPEC = ElementSpec(
    target=TARGET_NAME,
    display_name='Lightning Elemental',
    element='lightning',
    traits=('elemental', 'lightning', 'storm'),
    description='A storm-wraith with a recessed face suspended in white-hot electrical channels, recursively branching corona, and forked discharge limbs.',
    gameplay='A floating skirmisher. It charges a forked claw and fires an existing lightning projectile.',
    run_speed=120.0,
    move_style='Float',
    body_kind='Floating',
    mass_class='Medium',
    floating=True,
    attack_preset='lightning_elemental_arc',
    standing_height=64.0,
    box=(92, 61, 220, 250),
    timing=(0.50, 0.18, 0.64),
)

def render(out_dir: str | Path, **opts):
    return publish_spec(SPEC, out_dir, **opts)
