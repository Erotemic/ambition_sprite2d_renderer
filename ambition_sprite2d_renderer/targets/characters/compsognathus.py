"""SVG-rigged compsognathus: a tiny quick dinosaur that bites.

Green with dark stripes and a pale belly: the build of the dilophosaurus
made small, with a plain skull. It runs low and fast and bites.

The SVG ``data/characters/compsognathus/compsognathus.svg`` owns the art and marks every
joint (its hidden ``Rig Joints`` layer). The rig document under
``rigged/compsognathus/`` owns the skeleton and the clips;
``scripts/build_ratite_rigs.py`` derives it (through ``rigbuild.creature_rig``
with the ``ratite`` anatomy, which is the build of a small two-legged
dinosaur too) and authors the clips. This module owns only publication;
``_ratite`` holds what the targets of that build share and ``_bird_fx`` draws
the effects.

    PYTHONPATH=tools/ambition_sprite2d_renderer python -m ambition_sprite2d_renderer publish compsognathus
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from PIL import Image

from . import _ratite

TARGET_NAME = "compsognathus"
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
    # What it sheds when it is hit: scales, in its own colours.
    feathers=(((111, 160, 106, 255), (70, 122, 76, 255)), ((226, 223, 166, 255), (111, 160, 106, 255))),
    # The head bone runs from the back of the skull to the end of the snout.
    beak_length=41.6,
)

ACTOR_METADATA = _ratite.actor_metadata(
    TARGET_NAME,
    # Spelled out: the game's identity scan reads a literal, not a name.
    character_id="compsognathus",
    display_name="Compsognathus",
    art_scale=ART_SCALE,
    mass_class="Light",
    traits=["small", "fast", "swarm"],
    sockets={"mouth": (347.6, 275.9), "head": (320.3, 264.7), "feet": (236.0, 416.0), "tail": (117.0, 334.2)},
    authoring=(
        "The compsognathus is tiny and green with dark stripes, drawn as an SVG and posed by a rig. "
        "It runs low and fast on two legs and bites."
    ),
    gameplay=(
        "Use in numbers: one is a nuisance and three are a problem. An enemy of the primeval trail."
    ),
    barks=["Chrrp!", "It compiles.", "Chrrp chrrp chrrp."],
    body_plan="BeastBiped",
    kind=("dinosaur",),
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
