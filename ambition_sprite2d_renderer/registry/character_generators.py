"""Registry of the procedural character generators.

Each entry maps a target id to a :class:`CharacterGenerator` instance. There is
no adapter/wrapper layer: the generator listed here *is* what the sheet pipeline
renders. To add a target, implement a :class:`CharacterGenerator` in
``targets/characters/`` and register it below.
"""

from __future__ import annotations

from typing import Dict

from ..authoring.generator import CharacterGenerator
from ..targets.characters.alice_cryptographer import AliceCryptographerGenerator
from ..targets.characters.boss_side import AISlopZetaGenerator
from ..targets.characters.goblin_side import SideGoblinGenerator
from ..targets.characters.robot_side import SideRobotGenerator
from ..targets.characters.sandbag import SandbagGenerator
from ..targets.characters.toon_side import ToonSideGenerator

GENERATORS: Dict[str, CharacterGenerator] = {
    "alice_cryptographer": AliceCryptographerGenerator(),
    "boss": AISlopZetaGenerator(),
    "goblin": SideGoblinGenerator(),
    "robot": SideRobotGenerator(),
    "sandbag": SandbagGenerator(),
    "toon": ToonSideGenerator(),
}


def get_generator(target: str) -> CharacterGenerator:
    try:
        return GENERATORS[target]
    except KeyError as ex:
        raise KeyError(
            f"unknown target {target!r}; available={sorted(GENERATORS)}"
        ) from ex
