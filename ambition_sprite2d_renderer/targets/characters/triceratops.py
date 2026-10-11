"""SVG-rigged triceratops: a heavy horned dinosaur on four legs, which gores.

Slate blue with a pale belly: a barrel of a body on four thick legs, a heavy
tail, a frill of bone with ochre blotches, two long brow horns, a nose horn
and a hooked beak. It walks slowly, gallops with its head down, and throws
its horns up into what is in front of it.

The SVG ``data/characters/triceratops/triceratops.svg`` owns the art and marks
every joint (its hidden ``Rig Joints`` layer). The rig document under
``rigged/triceratops/`` owns the skeleton and the clips;
``scripts/build_triceratops_rig.py`` derives it (through
``rigbuild.creature_rig`` with the ``quadruped`` anatomy and a tail bone) and
authors the clips. This module owns only publication; ``_ratite`` holds the
actor contract of a ground enemy that runs at its target and ``_bird_fx``
draws the effects.

    PYTHONPATH=tools/ambition_sprite2d_renderer python -m ambition_sprite2d_renderer publish triceratops
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from PIL import Image

from . import _ratite
from ._bird_fx import BirdFx

TARGET_NAME = "triceratops"
USES_DROP_SHADOW = False
USES_PROPS = False
LINEAGE = _ratite.lineage(TARGET_NAME)
LOOPS = _ratite.LOOPS
RIG_PATH = _ratite.rig_path(TARGET_NAME)
FRAME_W, FRAME_H = 256, 256
#: Sprite pixels per SVG unit (the rig's ``svg_source.scale``): drawn 512
#: units square.
ART_SCALE = 0.5

BIRD = BirdFx(
    target=TARGET_NAME,
    rig_path=RIG_PATH,
    art_scale=ART_SCALE,
    frame_size=(FRAME_W, FRAME_H),
    # What it sheds when it is hit: scales, in its own colours.
    feathers=(((111, 135, 150, 255), (79, 100, 116, 255)), ((201, 195, 164, 255), (111, 135, 150, 255))),
    # The tip of the near brow horn, in the head bone's frame (the bone runs
    # from the back of the skull to the beak).
    beak_tip=(63.5, -126.9),
    body_bone="torso",
    foot_bone="near_fore_paw",
)

ACTOR_METADATA = _ratite.actor_metadata(
    TARGET_NAME,
    # Spelled out: the game's identity scan reads a literal, not a name.
    character_id="triceratops",
    display_name="Triceratops",
    art_scale=ART_SCALE,
    mass_class="Heavy",
    traits=["heavy", "horned", "charger"],
    sockets={"mouth": (446.0, 342.0), "head": (384.0, 292.0), "feet": (236.0, 416.0), "tail": (40.0, 356.0)},
    authoring=(
        "The triceratops is slate blue with a frill of bone, two long brow horns and a nose horn, drawn as "
        "an SVG and posed by a rig. It walks on four thick legs, gallops head down, and gores."
    ),
    gameplay=(
        "Use as the heavy of the primeval trail: slow to turn, a lot of health, and its horns hit hard. "
        "Running into it hurts."
    ),
    barks=["Hrrrmph.", "Try. Catch. Finally.", "*it paws the ground*"],
    body_plan="Quadruped",
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
