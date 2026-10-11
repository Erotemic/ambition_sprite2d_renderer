"""SVG-rigged ostrich: the tallest of the birds, a runner that kicks.

A black body with white plumes on its wings and its tail, a long bare neck
and bare legs with two toes. It runs with its wings out, kicks forward with
one leg and, to a problem, puts its head in the sand.

The SVG ``data/characters/ostrich/ostrich.svg`` owns the art and marks every
joint (its hidden ``Rig Joints`` layer). The rig document under
``rigged/ostrich/`` owns the skeleton and the clips;
``scripts/build_ratite_rigs.py`` derives it (through ``rigbuild.creature_rig``
with the ``ratite`` anatomy) and authors the clips. This module owns only
publication; ``_ratite`` holds what the ratites share and ``_bird_fx`` draws
the effects.

    PYTHONPATH=tools/ambition_sprite2d_renderer python -m ambition_sprite2d_renderer publish ostrich
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from PIL import Image

from . import _ratite

TARGET_NAME = "ostrich"
USES_DROP_SHADOW = False
USES_PROPS = False
LINEAGE = _ratite.lineage(TARGET_NAME)
LOOPS = _ratite.LOOPS
RIG_PATH = _ratite.rig_path(TARGET_NAME)
FRAME_W, FRAME_H = 256, 256
#: Sprite pixels per SVG unit (the rig's ``svg_source.scale``): drawn 512
#: units square.
ART_SCALE = 0.5

BIRD = _ratite.ratite_fx(
    TARGET_NAME,
    art_scale=ART_SCALE,
    frame_size=(FRAME_W, FRAME_H),
    feathers=(((38, 34, 42, 255), (64, 59, 72, 255)), ((244, 239, 230, 255), (207, 199, 186, 255))),
    beak_length=38.5,
)

ACTOR_METADATA = _ratite.actor_metadata(
    TARGET_NAME,
    # Spelled out: the game's identity scan reads a literal, not a name.
    character_id="ostrich",
    display_name="Ostrich",
    art_scale=ART_SCALE,
    mass_class="Medium",
    traits=["tall", "fast"],
    sockets={"beak": (360.0, 98.0), "head": (328.0, 88.0), "feet": (256.0, 416.0), "tail": (146.0, 250.0)},
    authoring=(
        "The ostrich is black with white plumes on its wings and its tail, a long bare neck and "
        "bare two-toed legs, drawn as an SVG and posed by a rig. It strides, runs with its wings out "
        "for balance, kicks forward with one leg and puts its head in the sand."
    ),
    gameplay=(
        "Use as the fastest and tallest ground bird: it runs its target down and kicks with a "
        "long reach. Birds are dinosaurs, so the T-rex calls it with the rest of his kin."
    ),
    barks=["If I do not see the problem, there is no problem.", "Ignore it. It is cheaper.", "HONK."],
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
