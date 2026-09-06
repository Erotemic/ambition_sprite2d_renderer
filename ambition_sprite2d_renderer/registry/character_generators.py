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
from ..targets.characters.bob_engineer import BobEngineerGenerator
from ..targets.characters.eve_eavesdropper import EveEavesdropperGenerator
from ..targets.characters.erdish_scholar import ErdishScholarGenerator
from ..targets.characters.boss_side import AISlopZetaGenerator
from ..targets.characters.mallory_interceptor import MalloryInterceptorGenerator
from ..targets.characters.goblin_side import SideGoblinGenerator
from ..targets.characters.ninja_side import NinjaSideGenerator
from ..targets.characters.robot_side import SideRobotGenerator
from ..targets.characters.sandbag import SandbagGenerator
from ..targets.characters.toon_side import ToonSideGenerator
from ..targets.characters.trent_elder import TrentElderGenerator

GENERATORS: Dict[str, CharacterGenerator] = {
    "alice_cryptographer": AliceCryptographerGenerator(),
    "bob_engineer": BobEngineerGenerator(),
    "eve_eavesdropper": EveEavesdropperGenerator(),
    "erdish_scholar": ErdishScholarGenerator(),
    "boss": AISlopZetaGenerator(),
    "mallory_interceptor": MalloryInterceptorGenerator(),
    "goblin": SideGoblinGenerator(),
    "ninja": NinjaSideGenerator(),
    "robot": SideRobotGenerator(),
    "sandbag": SandbagGenerator(),
    "toon": ToonSideGenerator(),
    "trent_elder": TrentElderGenerator(),
}


def get_generator(target: str) -> CharacterGenerator:
    try:
        return GENERATORS[target]
    except KeyError as ex:
        raise KeyError(
            f"unknown target {target!r}; available={sorted(GENERATORS)}"
        ) from ex
