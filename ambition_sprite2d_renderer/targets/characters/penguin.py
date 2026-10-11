"""SVG-rigged penguin: an upright bird that waddles, and slides when it wants to go fast.

A black back and head, a white front with a gold wash at the throat, a pale
cheek, an orange beak and orange feet, and a flipper at each side. It waddles
with its flippers out, goes down on its belly to slide, slaps with a flipper
and trumpets with its head thrown back.

The SVG ``data/characters/penguin/penguin.svg`` owns the art and marks every
joint (its hidden ``Rig Joints`` layer). The rig document under
``rigged/penguin/`` owns the skeleton and the clips;
``scripts/build_penguin_rig.py`` derives it (through ``rigbuild.creature_rig``
with the ``bird`` anatomy) and authors the clips. This module owns only
publication; ``_ratite`` holds the contract of a ground bird that runs at its
target and ``_bird_fx`` draws the effects.

    PYTHONPATH=tools/ambition_sprite2d_renderer python -m ambition_sprite2d_renderer publish penguin
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from PIL import Image

from . import _ratite

TARGET_NAME = "penguin"
USES_DROP_SHADOW = False
USES_PROPS = False
LINEAGE = _ratite.lineage(TARGET_NAME)
LOOPS = _ratite.LOOPS
RIG_PATH = _ratite.rig_path(TARGET_NAME)
FRAME_W, FRAME_H = 128, 128
#: Sprite pixels per SVG unit (the rig's ``svg_source.scale``): drawn 512
#: units square.
ART_SCALE = 0.25

BIRD = _ratite.ratite_fx(
    TARGET_NAME,
    art_scale=ART_SCALE,
    frame_size=(FRAME_W, FRAME_H),
    feathers=(((34, 40, 58, 255), (61, 72, 102, 255)), ((246, 243, 234, 255), (213, 208, 196, 255))),
    # The head bone runs from the neck to the beak tip.
    beak_length=72.8,
)

ACTOR_METADATA = _ratite.actor_metadata(
    TARGET_NAME,
    # Spelled out: the game's identity scan reads a literal, not a name.
    character_id="penguin",
    display_name="Penguin",
    art_scale=ART_SCALE,
    mass_class="Light",
    traits=["upright", "slider"],
    sockets={"beak": (332.0, 244.0), "head": (266.0, 236.0), "feet": (256.0, 416.0), "tail": (190.0, 410.0)},
    authoring=(
        "The penguin has a black back and head, a white front with a gold wash at the throat, an "
        "orange beak and orange feet, drawn as an SVG and posed by a rig. It waddles, goes down on "
        "its belly to slide, slaps with a flipper and trumpets with its head thrown back."
    ),
    gameplay=(
        "Use as a small ground bird that is slow on its feet and fast on its belly: it slides at "
        "its target and slaps. Birds are dinosaurs, so the T-rex calls it with the rest of his kin."
    ),
    barks=["I am free. As in fish.", "Read my source. All of it.", "NOOT."],
)

#: The sheet's rows are the rig's clips, in its order (the game reads them by name).
ROWS: List[Tuple[str, int, int]] = BIRD.rows()


def render_frame(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
    return BIRD.render_frame(animation, frame_idx, frame_count)


# ---- Target registration hooks ------------------------------------------------


def render(out_dir: Path, **opts) -> List[Path]:
    del opts
    return BIRD.render(Path(out_dir), ACTOR_METADATA)


def render_canonical(out_dir: Path, **opts) -> Path:
    del opts
    return BIRD.render_canonical(Path(out_dir))


__all__ = ["ACTOR_METADATA", "LINEAGE", "LOOPS", "ROWS", "TARGET_NAME", "render", "render_canonical", "render_frame"]
