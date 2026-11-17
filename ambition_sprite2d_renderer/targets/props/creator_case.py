"""The Creator's case: a worn leather case of logs and notes, carried by its
handle.

The case the goblins came for (level 1, the workshop raid): a squat oxblood
leather case with a darker lid band, brass corner caps and clasps, a stitched
seam, and a leather handle on top. A paper tag on a string hangs from the
handle, so it reads as somebody's case of papers rather than a weapon or a
tool box. It is a held item that throws on use, like any carried object; the
raid's last raider runs off with it in his hand.

Animations:

- ``idle``: one frame. A case does not move by itself.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from PIL import Image

from ...authoring.sheet_build import build_sheet
from . import _held_prop_common as hp
from ambition_sprite2d_renderer.core.draw import blending_draw

TARGET_NAME = "creator_case"
SHEET_FILES = (
    f"{TARGET_NAME}_spritesheet.png",
    f"{TARGET_NAME}_spritesheet.yaml",
    f"{TARGET_NAME}_spritesheet.ron",
    f"{TARGET_NAME}_actor.ron",
)

FRAME_SIZE = (64, 52)
ROWS: List[Tuple[str, int, int]] = [("idle", 1, 200)]

#: The body of the case, and its handle above it.
BODY = (8.0, 20.0, 56.0, 48.0)
LID_BOTTOM = 29.0
HANDLE = (24.0, 8.0, 40.0, 21.0)
GRIP = (32.0, 10.0)

LEATHER = (112, 46, 38, 255)
LEATHER_LIGHT = (146, 68, 52, 255)
LEATHER_DARK = (72, 28, 24, 255)
OUTLINE = (40, 18, 16, 255)
BRASS = (204, 162, 78, 255)
BRASS_DARK = (138, 102, 40, 255)
STITCH = (214, 186, 150, 255)
TAG = (232, 220, 188, 255)
STRING = (90, 80, 64, 255)


def _draw_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    del frame_idx, nframes
    if anim != "idle":
        raise ValueError(f"unknown animation: {anim}")
    canvas = hp.new_super(FRAME_SIZE)
    d = blending_draw(canvas)
    p = hp.px
    x0, y0, x1, y1 = BODY

    # The handle: a leather loop on two brass lugs.
    hx0, hy0, hx1, hy1 = HANDLE
    d.rounded_rectangle((p(hx0), p(hy0), p(hx1), p(hy1)), radius=p(5.0), outline=OUTLINE, width=int(p(4.2)))
    d.rounded_rectangle((p(hx0), p(hy0), p(hx1), p(hy1)), radius=p(5.0), outline=LEATHER_DARK, width=int(p(2.6)))
    for lx in (hx0 - 1.0, hx1 - 3.0):
        d.rectangle((p(lx), p(hy1 - 2.0), p(lx + 4.0), p(y0 + 1.0)), fill=BRASS, outline=BRASS_DARK, width=int(p(0.6)))

    # The body: oxblood leather, lit from the top left.
    d.rounded_rectangle((p(x0), p(y0), p(x1), p(y1)), radius=p(3.5), fill=LEATHER, outline=OUTLINE, width=int(p(1.4)))
    d.rectangle((p(x0 + 2.0), p(LID_BOTTOM + 2.0), p(x0 + 5.0), p(y1 - 3.0)), fill=LEATHER_LIGHT)
    d.rectangle((p(x0 + 2.0), p(y1 - 5.0), p(x1 - 2.0), p(y1 - 2.0)), fill=LEATHER_DARK)
    # The lid band, darker, with its seam stitched.
    d.rectangle((p(x0 + 1.0), p(y0 + 1.0), p(x1 - 1.0), p(LID_BOTTOM)), fill=LEATHER_DARK)
    d.rectangle((p(x0 + 2.0), p(y0 + 2.0), p(x1 - 2.0), p(y0 + 4.0)), fill=LEATHER)
    d.line([(p(x0 + 1.0), p(LID_BOTTOM)), (p(x1 - 1.0), p(LID_BOTTOM))], fill=OUTLINE, width=int(p(1.0)))
    x = x0 + 3.0
    while x < x1 - 4.0:
        d.line([(p(x), p(LID_BOTTOM + 2.0)), (p(x + 1.6), p(LID_BOTTOM + 2.0))], fill=STITCH, width=int(p(0.6)))
        x += 3.2

    # Brass corner caps.
    for cx, cy in ((x0, y0), (x1 - 5.0, y0), (x0, y1 - 5.0), (x1 - 5.0, y1 - 5.0)):
        d.rectangle((p(cx), p(cy), p(cx + 5.0), p(cy + 5.0)), fill=BRASS, outline=BRASS_DARK, width=int(p(0.6)))
    # Two clasps across the lid's edge.
    for cx in (18.0, 42.0):
        d.rectangle((p(cx), p(LID_BOTTOM - 4.0), p(cx + 5.0), p(LID_BOTTOM + 3.0)), fill=BRASS, outline=BRASS_DARK, width=int(p(0.6)))
        d.rectangle((p(cx + 1.6), p(LID_BOTTOM - 1.0), p(cx + 3.4), p(LID_BOTTOM + 1.0)), fill=BRASS_DARK)

    # A paper tag on a string from the handle's lug.
    d.line([(p(hx1 - 1.0), p(hy1 - 1.0)), (p(hx1 + 6.0), p(y0 + 5.0))], fill=STRING, width=int(p(0.6)))
    tag = [(p(hx1 + 4.0), p(y0 + 4.0)), (p(hx1 + 11.0), p(y0 + 6.0)), (p(hx1 + 9.5), p(y0 + 13.0)), (p(hx1 + 2.5), p(y0 + 11.0))]
    d.polygon(tag, fill=TAG, outline=STRING)
    d.line([(p(hx1 + 4.5), p(y0 + 8.0)), (p(hx1 + 9.0), p(y0 + 9.2))], fill=STRING, width=int(p(0.5)))
    return hp.finalize(canvas, FRAME_SIZE)


def _frame_meta(anim: str, frame_idx: int, nframes: int) -> dict:
    del anim, frame_idx, nframes
    return hp.anchor_meta({"grip": GRIP, "tip": (BODY[2], (BODY[1] + BODY[3]) * 0.5), "butt": (BODY[0], (BODY[1] + BODY[3]) * 0.5)})


ACTOR_METADATA = {
    "actor": {"character_id": "prop_creator_case", "display_name": "The Creator's Case"},
    "body": {
        "body_plan": "Prop",
        "body_kind": "Projectile",
        "mass_class": "Light",
        "locomotion_hint": "Thrown",
        "traits": ["prop", "case", "carried", "story"],
    },
    "brain": {"default_preset": "stand_still"},
    "actions": {"default_preset": "peaceful"},
    "animation_bindings": {"default": {"animation": "idle", "events": []}},
    "sockets": {
        "grip": {"source": f"{TARGET_NAME}.geometry", "point": {"x": GRIP[0], "y": GRIP[1]}},
    },
    "tags": ["prop", "case", "story"],
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
