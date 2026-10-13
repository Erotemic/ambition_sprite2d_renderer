"""Pool noodle: a tube of foam for a pool, and a thing to hit with.

It lies by the pools of the Noodly Temple (the joke is that it is a noodle).
A body picks it up and swings it: it is long, it is light, and it does not
hurt much. It is a held item: the game pins it at the ``grip`` and turns it
with the swing. See ``_held_prop_common`` for the shared authoring contract;
the noodle is drawn with its far end to the RIGHT (+X).

A pool noodle is a tube with a hole through it, in one bright colour. It is
not stiff: it droops a little from the hand to its far end.

Animations:

- ``idle``: one frame.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from PIL import Image

from ...authoring.sheet_build import build_sheet
from . import _held_prop_common as hp
from ambition_sprite2d_renderer.core.draw import blending_draw

TARGET_NAME = "pool_noodle"
SHEET_FILES = (
    f"{TARGET_NAME}_spritesheet.png",
    f"{TARGET_NAME}_spritesheet.yaml",
    f"{TARGET_NAME}_spritesheet.ron",
    f"{TARGET_NAME}_actor.ron",
)

FRAME_SIZE = (208, 56)
ROWS: List[Tuple[str, int, int]] = [("idle", 1, 200)]

#: The ends of the tube, its half thickness, and how far its far end droops.
BUTT_X, TIP_X, CY = 12.0, 196.0, 24.0
HALF = 9.0
DROOP = 9.0
GRIP_X = 34.0

FOAM = (66, 200, 220, 255)
FOAM_HI = (164, 240, 248, 255)
FOAM_DARK = (26, 126, 158, 255)
HOLE = (14, 62, 84, 255)


def _mid(x: float) -> float:
    """The middle of the tube at `x`: level at the hand, lower at the far end."""
    t = max(0.0, (x - GRIP_X) / (TIP_X - GRIP_X))
    return CY + DROOP * t * t


def _draw_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    del frame_idx, nframes
    if anim != "idle":
        raise ValueError(f"unknown animation: {anim}")
    canvas = hp.new_super(FRAME_SIZE)
    d = blending_draw(canvas)
    p = hp.px
    xs = [BUTT_X + (TIP_X - BUTT_X) * i / 48.0 for i in range(49)]
    upper = [(p(x), p(_mid(x) - HALF)) for x in xs]
    lower = [(p(x), p(_mid(x) + HALF)) for x in reversed(xs)]
    d.polygon(upper + lower, fill=FOAM)
    # The round of the tube: light along its upper side, shade along its lower.
    d.polygon([(p(x), p(_mid(x) - HALF * 0.72)) for x in xs] + [(p(x), p(_mid(x) - HALF * 0.24)) for x in reversed(xs)], fill=FOAM_HI)
    d.polygon([(p(x), p(_mid(x) + HALF * 0.42)) for x in xs] + [(p(x), p(_mid(x) + HALF)) for x in reversed(xs)], fill=FOAM_DARK)
    d.line(upper + lower + [upper[0]], fill=hp.OUTLINE, width=max(1, int(p(1.4))), joint="curve")
    # The near end is cut square. The far end shows the hole through the tube.
    d.ellipse((p(BUTT_X - 3.2), p(_mid(BUTT_X) - HALF), p(BUTT_X + 3.2), p(_mid(BUTT_X) + HALF)), fill=FOAM_DARK, outline=hp.OUTLINE, width=max(1, int(p(1.4))))
    ty = _mid(TIP_X)
    d.ellipse((p(TIP_X - 4.6), p(ty - HALF), p(TIP_X + 4.6), p(ty + HALF)), fill=FOAM_HI, outline=hp.OUTLINE, width=max(1, int(p(1.4))))
    d.ellipse((p(TIP_X - 2.0), p(ty - HALF * 0.44), p(TIP_X + 2.0), p(ty + HALF * 0.44)), fill=HOLE)
    # The marks the mould leaves in the foam: a few short lines along it.
    for x in (58.0, 96.0, 134.0, 168.0):
        d.line([(p(x), p(_mid(x) + HALF * 0.06)), (p(x + 14.0), p(_mid(x + 14.0) + HALF * 0.06))], fill=FOAM_DARK, width=max(1, int(p(0.8))))
    return hp.finalize(canvas, FRAME_SIZE)


def _frame_meta(anim: str, frame_idx: int, nframes: int) -> dict:
    del anim, frame_idx, nframes
    return hp.anchor_meta({"grip": (GRIP_X, CY), "tip": (TIP_X, _mid(TIP_X)), "butt": (BUTT_X, CY)})


ACTOR_METADATA = {
    "actor": {"character_id": "prop_pool_noodle", "display_name": "Pool Noodle"},
    "body": {
        "body_plan": "Prop",
        "body_kind": "Weapon",
        "mass_class": "Light",
        "locomotion_hint": "Held",
        "traits": ["prop", "pool_noodle", "weapon", "foam"],
    },
    "brain": {"default_preset": "stand_still"},
    "actions": {"default_preset": "peaceful"},
    "animation_bindings": {"default": {"animation": "idle", "events": []}},
    "sockets": {
        "grip": {"source": f"{TARGET_NAME}.geometry", "point": {"x": GRIP_X, "y": CY}},
        "tip": {"source": f"{TARGET_NAME}.geometry", "point": {"x": TIP_X, "y": _mid(TIP_X)}},
        "butt": {"source": f"{TARGET_NAME}.geometry", "point": {"x": BUTT_X, "y": CY}},
    },
    "tags": ["prop", "pool_noodle", "weapon"],
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
