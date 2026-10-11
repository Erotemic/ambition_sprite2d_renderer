"""SVG-rigged emu: a shaggy runner that dances and kicks.

Shaggy grey-brown plumage like hair, a blue-grey bare neck over a collar of
feathers, a dark tuft on its crown, a red eye and dark three-toed legs. It
runs, kicks forward with one leg and dances from foot to foot.

The SVG ``data/characters/emu/emu.svg`` owns the art and marks every
joint (its hidden ``Rig Joints`` layer). The rig document under
``rigged/emu/`` owns the skeleton and the clips;
``scripts/build_ratite_rigs.py`` derives it (through ``rigbuild.creature_rig``
with the ``ratite`` anatomy) and authors the clips. This module owns only
publication; ``_ratite`` holds what the ratites share and ``_bird_fx`` draws
the effects.

    PYTHONPATH=tools/ambition_sprite2d_renderer python -m ambition_sprite2d_renderer publish emu
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from PIL import Image

from . import _ratite

TARGET_NAME = "emu"
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
    feathers=(((125, 108, 88, 255), (92, 78, 64, 255)), ((160, 142, 118, 255), (125, 108, 88, 255))),
    beak_length=36.9,
)

ACTOR_METADATA = _ratite.actor_metadata(
    TARGET_NAME,
    display_name="Emu",
    art_scale=ART_SCALE,
    mass_class="Medium",
    traits=["tall", "fast", "shaggy"],
    sockets={"beak": (354.0, 142.0), "head": (324.0, 132.0), "feet": (256.0, 416.0), "tail": (164.0, 312.0)},
    authoring=(
        "The emu has shaggy grey-brown plumage like hair, a blue-grey bare neck over a collar of "
        "feathers, a dark tuft on its crown and a red eye, drawn as an SVG and posed by a rig. It "
        "strides, runs, kicks forward with one leg and dances from foot to foot."
    ),
    gameplay=(
        "Use as a fast ground bird that is hard to pin down: it runs at its target and kicks. "
        "Birds are dinosaurs, so the T-rex calls it with the rest of his kin."
    ),
    barks=["I can run anything. Slowly.", "We won that war, you know.", "Boom. Boom. Boom."],
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
