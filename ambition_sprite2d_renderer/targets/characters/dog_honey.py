"""Honey: a short orange dog like a fox, with two very large ears and a brush of a tail.

Drawn from a photograph of a dog of Jon's (2026-10-13). The drawing is
``data/characters/dog_honey/dog_honey_side.svg``. The joints and the motion are the
companion dog's (``_house_dog``).
"""

from __future__ import annotations

from pathlib import Path

from ambition_sprite2d_renderer.targets.characters import _house_dog

TARGET_NAME = "dog_honey"
RIG_PATH = _house_dog.rig_path(TARGET_NAME)

ACTOR_METADATA = _house_dog.actor_metadata(
    {"character_id": "npc_dog_honey", "display_name": "Honey"},
    [
        "Honey, the smallest of the three (35 lb): a short orange dog like a fox, with two very large ears.",
        "Grey about the nose and the brow, a small white patch on the chest, a thick brush of a tail. No collar.",
    ],
)


def render(out_dir: str | Path, **opts):
    del opts
    return _house_dog.render(TARGET_NAME, ACTOR_METADATA, out_dir)


__all__ = ["ACTOR_METADATA", "render"]
