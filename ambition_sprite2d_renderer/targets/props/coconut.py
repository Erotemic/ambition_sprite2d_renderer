"""Coconut: a thing to pick up and throw.

A brown husked coconut with its three eyes at one end. It is a held item and
a thrown one: the game pins it at the ``grip`` (its middle) when a body
carries it and turns it as it flies. A bird can carry one too (the African
swallow grips it by the husk). See ``_held_prop_common`` for the shared
authoring contract; the nut is drawn with its eyes to the RIGHT (+X).

Animations:

- ``idle``: one frame. A coconut does not move by itself.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from PIL import Image

from ...authoring.sheet_build import build_sheet
from . import _held_prop_common as hp
from ambition_sprite2d_renderer.core.draw import blending_draw

TARGET_NAME = "coconut"
SHEET_FILES = (
    f"{TARGET_NAME}_spritesheet.png",
    f"{TARGET_NAME}_spritesheet.yaml",
    f"{TARGET_NAME}_spritesheet.ron",
    f"{TARGET_NAME}_actor.ron",
)

FRAME_SIZE = (56, 48)
ROWS: List[Tuple[str, int, int]] = [("idle", 1, 200)]

CX, CY = 28.0, 24.0
RX, RY = 21.0, 18.0

HUSK = (122, 78, 42, 255)
HUSK_HI = (160, 110, 62, 255)
HUSK_DARK = (78, 46, 20, 255)
EYE = (46, 26, 12, 255)


def _draw_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    del frame_idx, nframes
    if anim != "idle":
        raise ValueError(f"unknown animation: {anim}")
    canvas = hp.new_super(FRAME_SIZE)
    d = blending_draw(canvas)
    p = hp.px
    d.ellipse((p(CX - RX), p(CY - RY), p(CX + RX), p(CY + RY)), fill=HUSK, outline=hp.OUTLINE, width=int(p(1.4)))
    # Light on its upper side.
    d.ellipse((p(CX - RX * 0.72), p(CY - RY * 0.8), p(CX + RX * 0.42), p(CY - RY * 0.06)), fill=HUSK_HI)
    d.ellipse((p(CX - RX * 0.78), p(CY - RY * 0.62), p(CX + RX * 0.5), p(CY + RY * 0.22)), fill=HUSK)
    # The fibres of the husk run from one end to the other.
    for k in range(-3, 4):
        y = CY + k * 4.6
        bend = (1.0 - (k / 4.0) ** 2) * 2.0
        d.line([(p(CX - RX * 0.82), p(y)), (p(CX - 4), p(y - bend)), (p(CX + RX * 0.5), p(y))], fill=HUSK_DARK,
               width=max(1, int(p(0.7))), joint="curve")
    # The three eyes.
    for ex, ey in ((CX + RX * 0.68, CY - 5.0), (CX + RX * 0.78, CY + 3.0), (CX + RX * 0.5, CY + 6.5)):
        d.ellipse((p(ex - 2.2), p(ey - 2.6), p(ex + 2.2), p(ey + 2.6)), fill=EYE)
    return hp.finalize(canvas, FRAME_SIZE)


def _frame_meta(anim: str, frame_idx: int, nframes: int) -> dict:
    del anim, frame_idx, nframes
    return hp.anchor_meta({"grip": (CX, CY), "tip": (CX + RX, CY), "butt": (CX - RX, CY)})


ACTOR_METADATA = {
    "actor": {"character_id": "prop_coconut", "display_name": "Coconut"},
    "body": {
        "body_plan": "Prop",
        "body_kind": "Projectile",
        "mass_class": "Light",
        "locomotion_hint": "Thrown",
        "traits": ["prop", "coconut", "thrown", "projectile"],
    },
    "brain": {"default_preset": "stand_still"},
    "actions": {"default_preset": "peaceful"},
    "animation_bindings": {"default": {"animation": "idle", "events": []}},
    "sockets": {
        "grip": {"source": f"{TARGET_NAME}.geometry", "point": {"x": CX, "y": CY}},
        "tip": {"source": f"{TARGET_NAME}.geometry", "point": {"x": CX + RX, "y": CY}},
        "butt": {"source": f"{TARGET_NAME}.geometry", "point": {"x": CX - RX, "y": CY}},
    },
    "tags": ["prop", "coconut", "thrown"],
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
