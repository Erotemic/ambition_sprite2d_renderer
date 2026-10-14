"""Bezoar: a tall, lanky fawn dog, with a dark mask, ears that fold at the end, and its tongue out.

Drawn from a photograph of a dog of Jon's (2026-10-13). The drawing is
``data/characters/dog_bezoar/dog_bezoar_side.svg``. The joints and the motion are the
companion dog's (``_house_dog``).
"""

from __future__ import annotations

from pathlib import Path

from ambition_sprite2d_renderer.targets.characters import _house_dog

TARGET_NAME = "dog_bezoar"
RIG_PATH = _house_dog.rig_path(TARGET_NAME)

ACTOR_METADATA = _house_dog.actor_metadata(
    {"character_id": "npc_dog_bezoar", "display_name": "Bezoar"},
    [
        "Bezoar, tall and lanky (40 lb): a fawn dog on long legs, with a dark mask on its muzzle.",
        "Ears that stand up and fold at the end, a tongue that hangs out.",
        "A brown collar with a pattern, a brass tag and a blue tag in the shape of a bone.",
    ],
)


def render(out_dir: str | Path, **opts):
    del opts
    return _house_dog.render(TARGET_NAME, ACTOR_METADATA, out_dir)


__all__ = ["ACTOR_METADATA", "render"]
