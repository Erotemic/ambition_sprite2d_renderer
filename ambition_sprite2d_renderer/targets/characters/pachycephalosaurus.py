"""SVG-rigged pachycephalosaurus: a dinosaur with a dome of bone on its skull, which rams.

Sand and rust, a pale belly, a thick dome of bone on its skull with knobs
behind it. It walks on two legs with its head carried low and forward. It
draws back and drives its skull into what is in front of it.

The SVG ``data/characters/pachycephalosaurus/pachycephalosaurus.svg`` owns the art and marks every
joint (its hidden ``Rig Joints`` layer). The rig document under
``rigged/pachycephalosaurus/`` owns the skeleton and the clips;
``scripts/build_ratite_rigs.py`` derives it (through ``rigbuild.creature_rig``
with the ``ratite`` anatomy, which is the build of a small two-legged
dinosaur too) and authors the clips. This module owns only publication;
``_ratite`` holds what the targets of that build share and ``_bird_fx`` draws
the effects.

    PYTHONPATH=tools/ambition_sprite2d_renderer python -m ambition_sprite2d_renderer publish pachycephalosaurus
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from PIL import Image

from . import _ratite

TARGET_NAME = "pachycephalosaurus"
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
    # What it sheds when it is hit: scales, in its own colours.
    feathers=(((184, 141, 88, 255), (138, 94, 52, 255)), ((230, 214, 168, 255), (184, 141, 88, 255))),
    # The head bone runs from the back of the skull to the end of the snout.
    beak_length=65.1,
)

ACTOR_METADATA = _ratite.actor_metadata(
    TARGET_NAME,
    # Spelled out: the game's identity scan reads a literal, not a name.
    character_id="pachycephalosaurus",
    display_name="Pachycephalosaurus",
    art_scale=ART_SCALE,
    mass_class="Heavy",
    traits=["charger", "domed"],
    sockets={"mouth": (408.0, 226.0), "head": (366.0, 190.0), "feet": (236.0, 416.0), "tail": (44.0, 284.0)},
    authoring=(
        "The pachycephalosaurus is sand and rust with a thick dome of bone on its skull, drawn as "
        "an SVG and posed by a rig. It walks on two legs with its head low, and it rams."
    ),
    gameplay=(
        "Use as the charger: it runs at its target and hits hard with its skull, and running into "
        "it hurts. An enemy of the primeval trail."
    ),
    barks=["Applying patch.", "Head first. Always head first.", "THUD."],
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
