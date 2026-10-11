"""SVG-rigged shoebill: a great grey wading bird that stands, stares and strikes.

Slate grey, a great clog of a bill with a hooked nail at its tip, a pale eye
under a brow that never lifts, a small crest and long dark legs. Not a ratite,
but it has their build and hunts on foot, so it is posed on their anatomy. It
stands still for a long time, then falls on its prey bill first; it greets
with a clatter of its bill and a bow.

The SVG ``data/characters/shoebill/shoebill.svg`` owns the art and marks every
joint (its hidden ``Rig Joints`` layer). The rig document under
``rigged/shoebill/`` owns the skeleton and the clips;
``scripts/build_ratite_rigs.py`` derives it (through ``rigbuild.creature_rig``
with the ``ratite`` anatomy) and authors the clips. This module owns only
publication; ``_ratite`` holds what these birds share and ``_bird_fx`` draws
the effects.

    PYTHONPATH=tools/ambition_sprite2d_renderer python -m ambition_sprite2d_renderer publish shoebill
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from PIL import Image

from . import _ratite

TARGET_NAME = "shoebill"
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
    feathers=(((111, 129, 146, 255), (79, 95, 110, 255)), ((152, 169, 183, 255), (111, 129, 146, 255))),
    beak_length=88.2,
)

ACTOR_METADATA = _ratite.actor_metadata(
    TARGET_NAME,
    display_name="Shoebill",
    art_scale=ART_SCALE,
    mass_class="Medium",
    traits=["tall", "ambusher", "wader"],
    sockets={"beak": (374.0, 198.0), "head": (306.0, 142.0), "feet": (256.0, 416.0), "tail": (158.0, 284.0)},
    authoring=(
        "The shoebill is slate grey with a great clog of a bill, a pale eye under a brow that never "
        "lifts, a small crest and long dark legs, drawn as an SVG and posed by a rig. It stands and "
        "stares, falls on its prey bill first, and greets with a clatter of its bill and a bow."
    ),
    gameplay=(
        "Use as the slow, patient ground bird: it walks, it waits, and its one strike has a long tell "
        "and hurts a lot. Birds are dinosaurs, so the T-rex calls it with the rest of his kin."
    ),
    barks=["...", "I do nothing until the value is needed.", "CLACK-CLACK-CLACK-CLACK."],
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
