"""Orchard apple: an apple off one of the gravity works' trees.

A red apple with a short stem and one leaf, lit from the upper left. It is a
held item and a thrown one (the ``apple`` held item): the trees of the works'
orchard grow them in their crowns, and an apple that drops falls the way its
room pulls (in the orchard's up fields, up to the ceiling). See
``_held_prop_common`` for the shared authoring contract; the apple is drawn
stem UP, and its grip is its middle.

Animations:

- ``idle``: one frame. An apple does not move by itself.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from PIL import Image

from ...authoring.sheet_build import build_sheet
from . import _held_prop_common as hp
from ambition_sprite2d_renderer.core.draw import blending_draw

TARGET_NAME = "orchard_apple"
SHEET_FILES = (
    f"{TARGET_NAME}_spritesheet.png",
    f"{TARGET_NAME}_spritesheet.yaml",
    f"{TARGET_NAME}_spritesheet.ron",
    f"{TARGET_NAME}_actor.ron",
)

FRAME_SIZE = (40, 40)
ROWS: List[Tuple[str, int, int]] = [("idle", 1, 200)]

CX, CY = 20.0, 22.0
R = 13.0

RED = (196, 36, 40, 255)
RED_DARK = (130, 18, 28, 255)
RED_HI = (236, 96, 82, 255)
BLUSH = (226, 150, 60, 255)
STEM = (92, 60, 32, 255)
LEAF = (86, 156, 60, 255)
LEAF_DARK = (52, 108, 40, 255)


def _draw_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    del frame_idx, nframes
    if anim != "idle":
        raise ValueError(f"unknown animation: {anim}")
    canvas = hp.new_super(FRAME_SIZE)
    d = blending_draw(canvas)
    p = hp.px
    # The body: two shoulders and a rounder bottom, a dimple at the top.
    for (x0, y0, x1, y1) in ((CX - R, CY - R * 0.86, CX + R * 0.18, CY + R * 0.9),
                             (CX - R * 0.18, CY - R * 0.86, CX + R, CY + R * 0.9),
                             (CX - R * 0.8, CY - R * 0.4, CX + R * 0.8, CY + R)):
        d.ellipse((p(x0), p(y0), p(x1), p(y1)), fill=RED_DARK, outline=hp.OUTLINE, width=int(p(1.4)))
    for (x0, y0, x1, y1) in ((CX - R + 1.4, CY - R * 0.86 + 1.4, CX + R * 0.18 - 1.0, CY + R * 0.9 - 1.6),
                             (CX - R * 0.18 + 1.0, CY - R * 0.86 + 1.4, CX + R - 1.4, CY + R * 0.9 - 1.6),
                             (CX - R * 0.8 + 1.4, CY - R * 0.4 + 1.0, CX + R * 0.8 - 1.4, CY + R - 1.4)):
        d.ellipse((p(x0), p(y0), p(x1), p(y1)), fill=RED)
    # A warm blush on the sunny side, and the light on the upper left.
    d.ellipse((p(CX - R * 0.7), p(CY - R * 0.5), p(CX + R * 0.1), p(CY + R * 0.4)), fill=BLUSH)
    d.ellipse((p(CX - R * 0.62), p(CY - R * 0.44), p(CX + R * 0.18), p(CY + R * 0.52)), fill=RED)
    d.ellipse((p(CX - R * 0.62), p(CY - R * 0.6), p(CX - R * 0.22), p(CY - R * 0.12)), fill=RED_HI)
    # The dimple the stem rises from.
    d.ellipse((p(CX - 3.0), p(CY - R * 0.86 - 0.6), p(CX + 3.0), p(CY - R * 0.86 + 3.4)), fill=RED_DARK)
    # The stem, and a leaf off it.
    d.line([(p(CX), p(CY - R * 0.7)), (p(CX + 1.2), p(CY - R - 4.0)), (p(CX + 2.6), p(CY - R - 6.5))],
           fill=STEM, width=int(p(2.0)), joint="curve")
    leaf = [(p(CX + 1.6), p(CY - R - 3.6)), (p(CX + 6.0), p(CY - R - 8.4)), (p(CX + 12.0), p(CY - R - 7.0)),
            (p(CX + 8.0), p(CY - R - 2.4))]
    d.polygon(leaf, fill=LEAF, outline=hp.OUTLINE)
    d.line([(p(CX + 2.2), p(CY - R - 3.8)), (p(CX + 10.0), p(CY - R - 6.6))], fill=LEAF_DARK, width=max(1, int(p(0.7))))
    return hp.finalize(canvas, FRAME_SIZE)


def _frame_meta(anim: str, frame_idx: int, nframes: int) -> dict:
    del anim, frame_idx, nframes
    return hp.anchor_meta({"grip": (CX, CY), "tip": (CX + R, CY), "butt": (CX - R, CY)})


ACTOR_METADATA = {
    "actor": {"character_id": "prop_orchard_apple", "display_name": "Apple"},
    "body": {
        "body_plan": "Prop",
        "body_kind": "Projectile",
        "mass_class": "Light",
        "locomotion_hint": "Thrown",
        "traits": ["prop", "apple", "thrown", "projectile"],
    },
    "brain": {"default_preset": "stand_still"},
    "actions": {"default_preset": "peaceful"},
    "animation_bindings": {"default": {"animation": "idle", "events": []}},
    "sockets": {
        "grip": {"source": f"{TARGET_NAME}.geometry", "point": {"x": CX, "y": CY}},
        "tip": {"source": f"{TARGET_NAME}.geometry", "point": {"x": CX + R, "y": CY}},
        "butt": {"source": f"{TARGET_NAME}.geometry", "point": {"x": CX - R, "y": CY}},
    },
    "tags": ["prop", "apple", "thrown"],
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
