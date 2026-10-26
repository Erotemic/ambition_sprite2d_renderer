"""A toon character's walking and running feet are on the ground it stands on.

The game draws every row of a sheet on the standing body, so a planted foot of
the walk must reach the standing ground line. Regression: the walk planted its
feet a fixed share of the leg below a hip that bobbed UP, 4-7 px above the
idle's soles at 128 px (10 px on the published General Hero, Architect, Raid
Enforcer, Vault Keeper and Merchant).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from ambition_sprite2d_renderer.registry import CharacterJob
from ambition_sprite2d_renderer.registry.character_generators import get_generator

CONFIGS = Path(__file__).resolve().parent.parent / "ambition_sprite2d_renderer" / "configs" / "review"
SOLID = 192


def _lowest_sole(gen, spec, job, anim):
    frames = gen.animations()[anim]["frames"]
    bottoms = []
    for i in range(frames):
        alpha = np.asarray(gen.render_frame(spec, anim, i, (128, 128), job).convert("RGBA"))[..., 3]
        bottoms.append(int(np.flatnonzero((alpha >= SOLID).any(axis=1))[-1]) + 1)
    return max(bottoms)


@pytest.mark.parametrize("config", ["general_hero.yaml", "architect.yaml", "vault_keeper.yaml"])
def test_the_walk_and_run_plant_on_the_standing_ground(config):
    job = CharacterJob.load(CONFIGS / config)
    gen = get_generator(job.target)
    spec = gen.sample_spec(job)
    ground = _lowest_sole(gen, spec, job, "idle")
    for anim in ("walk", "run"):
        assert abs(_lowest_sole(gen, spec, job, anim) - ground) <= 1, (config, anim)
