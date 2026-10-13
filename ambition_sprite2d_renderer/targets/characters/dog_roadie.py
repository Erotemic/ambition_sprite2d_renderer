"""Roadie: a cattle dog, with a tan head and legs, a blue-grey saddle, a white end to its tail.

Drawn from a photograph of a dog of Jon's (2026-10-13). The drawing is
``data/characters/dog_roadie/dog_roadie_side.svg``. The joints and the motion are the
companion dog's (``_house_dog``).
"""

from __future__ import annotations

from pathlib import Path

from ambition_sprite2d_renderer.targets.characters import _house_dog

TARGET_NAME = "dog_roadie"
RIG_PATH = _house_dog.rig_path(TARGET_NAME)

ACTOR_METADATA = _house_dog.actor_metadata(
    "npc_dog_roadie",
    "Roadie",
    [
        "Roadie, the biggest of the three (50 lb): a cattle dog with a tan head and legs, and a blue-grey saddle with pale flecks.",
        "A ruff at the neck, a brush of a tail with a white end, an orange collar.",
    ],
)


def render(out_dir: str | Path, **opts):
    del opts
    return _house_dog.render(TARGET_NAME, ACTOR_METADATA, out_dir)


__all__ = ["ACTOR_METADATA", "render"]
