"""SVG-rigged kiwi: a small round bird with a long beak that it uses like a needle.

A brown pear of shaggy plumage with no wing or tail to see, a long thin
ivory beak, whiskers and big feet. It trots, stabs with its beak and probes
the ground for its food.

The SVG ``data/characters/kiwi/kiwi.svg`` owns the art and marks every
joint (its hidden ``Rig Joints`` layer). The rig document under
``rigged/kiwi/`` owns the skeleton and the clips;
``scripts/build_ratite_rigs.py`` derives it (through ``rigbuild.creature_rig``
with the ``ratite`` anatomy) and authors the clips. This module owns only
publication; ``_ratite`` holds what the ratites share and ``_bird_fx`` draws
the effects.

    PYTHONPATH=tools/ambition_sprite2d_renderer python -m ambition_sprite2d_renderer publish kiwi
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from PIL import Image

from . import _ratite

TARGET_NAME = "kiwi"
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
    feathers=(((140, 106, 72, 255), (104, 76, 50, 255)), ((176, 140, 98, 255), (140, 106, 72, 255))),
    beak_length=118.8,
)

ACTOR_METADATA = _ratite.actor_metadata(
    TARGET_NAME,
    display_name="Kiwi",
    art_scale=ART_SCALE,
    mass_class="Light",
    traits=["small", "nocturnal", "shaggy"],
    sockets={"beak": (398.0, 362.0), "head": (302.0, 292.0), "feet": (244.0, 416.0), "tail": (160.0, 358.0)},
    authoring=(
        "The kiwi is a small brown pear of shaggy plumage with no wing or tail to see, a long "
        "thin beak, whiskers and big feet, drawn as an SVG and posed by a rig. It trots, stabs with "
        "its beak and probes the ground."
    ),
    gameplay=(
        "Use as the smallest ground bird: quick, low, hard to hit, and it stabs with its beak. "
        "Birds are dinosaurs, so the T-rex calls it with the rest of his kin."
    ),
    barks=["Same answer as the big one. Faster.", "Sniff. Sniff sniff.", "Kee-wee!"],
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
