"""Earth Elemental: a slow rocky bruiser."""
from __future__ import annotations
from pathlib import Path
from ._elemental_enemy_family import ElementSpec, publish_spec

TARGET_NAME = 'earth_elemental'
SPEC = ElementSpec(
    target=TARGET_NAME,
    display_name='Earth Elemental',
    element='earth',
    traits=('elemental', 'earth', 'rock'),
    description='A massive interlocking granite-and-moss monster with low shoulders, angular stone fists, and a recessed glowing gaze.',
    gameplay='A slow heavy enemy that stomps into range, braces, and crashes forward with a stone-handed slam.',
    run_speed=88.0,
    move_style='WalkHeavy',
    body_kind='Standard',
    mass_class='Heavy',
    floating=False,
    attack_preset='earth_elemental_slam',
    standing_height=84.0,
    box=(87, 73, 214, 267),
    timing=(0.62, 0.2, 0.84),
)

def render(out_dir: str | Path, **opts):
    return publish_spec(SPEC, out_dir, **opts)
