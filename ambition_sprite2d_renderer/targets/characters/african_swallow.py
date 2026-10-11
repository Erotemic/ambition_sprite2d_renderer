"""SVG-rigged African swallow: a small fast bird with a rufous cap.

A rufous cap and rump, white below with dark streaks, long pointed wings
and a forked tail. The coconut it is known for is not in this drawing: a
coconut is a thing of the world that it picks up and drops.

The SVG ``data/characters/african_swallow/african_swallow.svg`` owns the art and marks every
joint (its hidden ``Rig Joints`` layer). The rig document under
``rigged/african_swallow/`` owns the skeleton and the clips;
``scripts/build_flyer_rigs.py`` derives it (through ``rigbuild.creature_rig``
with the ``bird`` anatomy) and authors the clips. This module owns only
publication; ``_flyer`` holds what these flyers share and ``_bird_fx`` draws
the effects.

    PYTHONPATH=tools/ambition_sprite2d_renderer python -m ambition_sprite2d_renderer publish african_swallow
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from PIL import Image

from . import _flyer

TARGET_NAME = "african_swallow"
USES_DROP_SHADOW = False
USES_PROPS = False
LINEAGE = _flyer.lineage(TARGET_NAME)
LOOPS = _flyer.LOOPS
RIG_PATH = _flyer.rig_path(TARGET_NAME)
FRAME_W, FRAME_H = 128, 128
#: Sprite pixels per SVG unit (the rig's ``svg_source.scale``): drawn 512
#: units square.
ART_SCALE = 0.25

BIRD = _flyer.flyer_fx(
    TARGET_NAME,
    art_scale=ART_SCALE,
    frame_size=(FRAME_W, FRAME_H),
    feathers=(((36, 52, 94, 255), (20, 28, 56, 255)), ((251, 246, 238, 255), (217, 208, 194, 255)), ((210, 105, 30, 255), (154, 68, 16, 255))),
    beak_tip=(57.0, 0.0),
    flight_pitch=40.0,
)

ACTOR_METADATA = _flyer.actor_metadata(
    TARGET_NAME,
    # Spelled out: the game's identity scan reads a literal, not a name.
    character_id="african_swallow",
    display_name="African Swallow",
    art_scale=ART_SCALE,
    mass_class="Light",
    traits=["small", "fast", "swallow"],
    sockets={"beak": (338.0, 298.0), "head": (298.0, 290.0), "talons": (262.0, 410.0), "tail": (112.0, 408.0)},
    authoring=(
        "The African swallow has a rufous cap and rump and is white below with dark streaks, with "
        "long pointed wings and a forked tail, drawn as an SVG and posed by a rig. It flies on quick "
        "shallow beats, darts in beak first and sings from a perch."
    ),
    gameplay=(
        "Use as the swallow that carries: it picks up a coconut where a room has one and drops it on "
        "its target. Birds are dinosaurs, so the T-rex calls it with the rest of his kin."
    ),
    barks=["It is a question of weight ratios.", "I do not migrate. I commute.", "Tswit. Oof."],
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
