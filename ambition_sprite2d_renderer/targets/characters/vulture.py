"""SVG-rigged vulture: a great dark bird that waits, then comes down to tear.

Dark plumage, a white ruff round the root of a bare red neck, a bald head
with a heavy brow, a pale hooked beak and broad wings with long fingered
flight feathers. It flies on slow beats, reaches down with its neck to tear,
and stands in the sun with its wings held wide.

The SVG ``data/characters/vulture/vulture.svg`` owns the art and marks every
joint (its hidden ``Rig Joints`` layer). The rig document under
``rigged/vulture/`` owns the skeleton and the clips;
``scripts/build_flyer_rigs.py`` derives it (through ``rigbuild.creature_rig``
with the ``bird`` anatomy) and authors the clips. This module owns only
publication; ``_flyer`` holds what these flyers share and ``_bird_fx`` draws
the effects.

    PYTHONPATH=tools/ambition_sprite2d_renderer python -m ambition_sprite2d_renderer publish vulture
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from PIL import Image

from . import _flyer

TARGET_NAME = "vulture"
USES_DROP_SHADOW = False
USES_PROPS = False
LINEAGE = _flyer.lineage(TARGET_NAME)
LOOPS = _flyer.LOOPS
RIG_PATH = _flyer.rig_path(TARGET_NAME)
FRAME_W, FRAME_H = 256, 256
#: Sprite pixels per SVG unit (the rig's ``svg_source.scale``): drawn 512
#: units square.
ART_SCALE = 0.5

BIRD = _flyer.flyer_fx(
    TARGET_NAME,
    art_scale=ART_SCALE,
    frame_size=(FRAME_W, FRAME_H),
    feathers=(((59, 48, 46, 255), (35, 27, 26, 255)), ((92, 75, 72, 255), (59, 48, 46, 255)), ((241, 236, 226, 255), (205, 197, 182, 255))),
    beak_tip=(80.6, 0.0),
    flight_pitch=46.0,
)

ACTOR_METADATA = _flyer.actor_metadata(
    TARGET_NAME,
    # Spelled out: the game's identity scan reads a literal, not a name.
    character_id="vulture",
    display_name="Vulture",
    art_scale=ART_SCALE,
    mass_class="Medium",
    traits=["large", "scavenger", "patient"],
    sockets={"beak": (352.0, 272.0), "head": (322.0, 238.0), "talons": (262.0, 410.0), "tail": (174.0, 408.0)},
    authoring=(
        "The vulture has dark plumage, a white ruff, a bare red neck and head with a heavy brow, a "
        "pale hooked beak and broad fingered wings, drawn as an SVG and posed by a rig. It flies on "
        "slow beats, reaches down with its neck to tear, and stands with its wings held wide."
    ),
    gameplay=(
        "Use as the big slow flyer: it takes a lot of blows and its beak hurts. "
        "Birds are dinosaurs, so the T-rex calls it with the rest of his kin."
    ),
    barks=["I do not hunt. I wait for the runway to end.", "You look tired. I like that.", "Hsssss."],
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
