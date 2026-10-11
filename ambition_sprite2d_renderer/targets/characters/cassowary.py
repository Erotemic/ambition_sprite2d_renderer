"""SVG-rigged cassowary: the most dangerous of the birds, with a casque and a dagger claw.

Black shaggy plumage, a bright blue neck with red down its nape and two
red wattles, a tall casque of horn on its crown and thick legs whose inner
toe carries a long claw. It kicks with that claw, and it stamps a warning.

The SVG ``data/characters/cassowary/cassowary.svg`` owns the art and marks every
joint (its hidden ``Rig Joints`` layer). The rig document under
``rigged/cassowary/`` owns the skeleton and the clips;
``scripts/build_ratite_rigs.py`` derives it (through ``rigbuild.creature_rig``
with the ``ratite`` anatomy) and authors the clips. This module owns only
publication; ``_ratite`` holds what the ratites share and ``_bird_fx`` draws
the effects.

    PYTHONPATH=tools/ambition_sprite2d_renderer python -m ambition_sprite2d_renderer publish cassowary
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from PIL import Image

from . import _ratite

TARGET_NAME = "cassowary"
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
    feathers=(((36, 33, 43, 255), (69, 65, 79, 255)), ((24, 22, 29, 255), (47, 116, 214, 255))),
    beak_length=39.3,
)

ACTOR_METADATA = _ratite.actor_metadata(
    TARGET_NAME,
    # Spelled out: the game's identity scan reads a literal, not a name.
    character_id="cassowary",
    display_name="Cassowary",
    art_scale=ART_SCALE,
    mass_class="Heavy",
    traits=["tall", "dangerous", "shaggy"],
    sockets={"beak": (350.0, 164.0), "head": (318.0, 152.0), "feet": (256.0, 416.0), "tail": (170.0, 318.0)},
    authoring=(
        "The cassowary has black shaggy plumage, a bright blue neck with red wattles, a tall "
        "casque of horn on its crown and thick legs with a dagger claw, drawn as an SVG and posed "
        "by a rig. It strides, runs, kicks forward claw first and stamps a warning."
    ),
    gameplay=(
        "Use as the heavy ground bird: slower than the ostrich and the emu, and its kick hurts "
        "the most. Birds are dinosaurs, so the T-rex calls it with the rest of his kin."
    ),
    barks=["Every one of your constraints is required. Mine are strong.", "Stay. There.", "BOOM."],
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
