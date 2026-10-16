"""Seam gauge: a square plate of a measured grid, to measure how seamless a
portal is.

A plate of 8 x 8 cells in two colours the rest of the game does not use
(pure magenta and pure blue), ruled by dark lines, with a white corner mark
at its top left so a turn or a mirror through a portal shows. The seam lab
(``scripts/portal_seam_lab.py`` in the game repo) films it crossing portals
and counts its pixels in each frame: a gauge that is drawn whole has all its
cells, wherever the portal cuts it. It is a held item that throws on use, so
a body can carry it, drop it or throw it at a portal.

Animations:

- ``idle``: one frame. A gauge does not move by itself.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from PIL import Image

from ...authoring.sheet_build import build_sheet
from . import _held_prop_common as hp
from ambition_sprite2d_renderer.core.draw import blending_draw

TARGET_NAME = "seam_gauge"
SHEET_FILES = (
    f"{TARGET_NAME}_spritesheet.png",
    f"{TARGET_NAME}_spritesheet.yaml",
    f"{TARGET_NAME}_spritesheet.ron",
    f"{TARGET_NAME}_actor.ron",
)

FRAME_SIZE = (64, 64)
ROWS: List[Tuple[str, int, int]] = [("idle", 1, 200)]

CELLS = 8
MARGIN = 2.0
CELL = (FRAME_SIZE[0] - 2 * MARGIN) / CELLS
CX, CY = FRAME_SIZE[0] * 0.5, FRAME_SIZE[1] * 0.5

# Pure colours, so a pixel of the gauge is told from the rest of the frame.
MAGENTA = (255, 0, 255, 255)
BLUE = (0, 0, 255, 255)
RULE = (20, 20, 24, 255)
MARK = (255, 255, 255, 255)


def _draw_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    del frame_idx, nframes
    if anim != "idle":
        raise ValueError(f"unknown animation: {anim}")
    canvas = hp.new_super(FRAME_SIZE)
    d = blending_draw(canvas)
    p = hp.px
    for row in range(CELLS):
        for col in range(CELLS):
            x0 = MARGIN + col * CELL
            y0 = MARGIN + row * CELL
            fill = MAGENTA if (row + col) % 2 == 0 else BLUE
            d.rectangle((p(x0), p(y0), p(x0 + CELL), p(y0 + CELL)), fill=fill)
    # The rules between the cells and round the plate.
    for k in range(CELLS + 1):
        at = MARGIN + k * CELL
        width = max(1, int(p(0.8)))
        d.line([(p(at), p(MARGIN)), (p(at), p(FRAME_SIZE[1] - MARGIN))], fill=RULE, width=width)
        d.line([(p(MARGIN), p(at)), (p(FRAME_SIZE[0] - MARGIN), p(at))], fill=RULE, width=width)
    # The corner mark: top left, so a turn or a mirror shows.
    d.rectangle((p(MARGIN + 1.0), p(MARGIN + 1.0), p(MARGIN + CELL - 1.0), p(MARGIN + CELL - 1.0)), fill=MARK)
    return hp.finalize(canvas, FRAME_SIZE)


def _frame_meta(anim: str, frame_idx: int, nframes: int) -> dict:
    del anim, frame_idx, nframes
    return hp.anchor_meta({"grip": (CX, CY), "tip": (FRAME_SIZE[0] - MARGIN, CY), "butt": (MARGIN, CY)})


ACTOR_METADATA = {
    "actor": {"character_id": "prop_seam_gauge", "display_name": "Seam Gauge"},
    "body": {
        "body_plan": "Prop",
        "body_kind": "Projectile",
        "mass_class": "Light",
        "locomotion_hint": "Thrown",
        "traits": ["prop", "gauge", "thrown", "diagnostic"],
    },
    "brain": {"default_preset": "stand_still"},
    "actions": {"default_preset": "peaceful"},
    "animation_bindings": {"default": {"animation": "idle", "events": []}},
    "sockets": {
        "grip": {"source": f"{TARGET_NAME}.geometry", "point": {"x": CX, "y": CY}},
        "tip": {"source": f"{TARGET_NAME}.geometry", "point": {"x": FRAME_SIZE[0] - MARGIN, "y": CY}},
        "butt": {"source": f"{TARGET_NAME}.geometry", "point": {"x": MARGIN, "y": CY}},
    },
    "tags": ["prop", "gauge", "thrown"],
}


def render(out_dir: str | Path, **opts) -> List[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=_draw_frame,
        out_dir=out_dir,
        frame_size=opts.get("frame_size") or FRAME_SIZE,
        frame_meta_fn=_frame_meta,
        auto_crop=True,
        crop_margin=3,
        actor_metadata=ACTOR_METADATA,
    )
    return [
        outputs["canonical"],
        outputs["canonical_transparent"],
        outputs["spritesheet"],
        outputs["yaml"],
        outputs["ron"],
        outputs["actor"],
        outputs["preview"],
    ]


__all__ = ["ACTOR_METADATA", "FRAME_SIZE", "ROWS", "TARGET_NAME", "render"]
