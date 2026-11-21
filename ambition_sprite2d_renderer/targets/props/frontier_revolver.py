"""A frontier revolver: a held prop.

A long-barrelled single-action revolver of the Frontier dimension: a
gunmetal frame, a six-chamber cylinder, a barrel with a front sight, a
hammer, a brass trigger guard and a curved wooden grip. Peyote Lean carries
one (``data/townsfolk/peyote_lean.chargen.yaml``); any character can hold it
as the held item ``frontier_revolver``.

It is drawn as the held props are (``_held_prop_common``): flat, the muzzle
pointing RIGHT (+x). The game pins it at ``grip`` (the middle of the wooden
grip, the shooting hand) and turns it to aim. ``muzzle`` is where a shot
leaves it, ``butt`` the end of the grip.

Rows: ``idle`` (one frame; the canonical picture).
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from ...authoring.sheet_build import build_sheet
from ambition_sprite2d_renderer.core.draw import blending_draw
from . import _held_prop_common as hp

TARGET_NAME = "frontier_revolver"
SHEET_FILES = (
    f"{TARGET_NAME}_spritesheet.png",
    f"{TARGET_NAME}_spritesheet.yaml",
    f"{TARGET_NAME}_spritesheet.ron",
    f"{TARGET_NAME}_actor.ron",
)

FRAME_SIZE = (132, 64)
ROWS: List[Tuple[str, int, int]] = [("idle", 1, 200)]

GUNMETAL = (70, 74, 84, 255)
GUNMETAL_DARK = (44, 46, 54, 255)
GUNMETAL_HI = (150, 156, 168, 255)

#: Anchors, in frame pixels.
GRIP_AT = (24.0, 42.0)
MUZZLE_AT = (126.0, 22.0)
BUTT_AT = (12.0, 56.0)


def _poly(d, pts, fill, outline=hp.OUTLINE) -> None:
    d.polygon([(hp.px(x), hp.px(y)) for x, y in pts], fill=fill, outline=outline, width=max(1, int(hp.px(1.0))))


def _line(d, pts, fill, width: float) -> None:
    d.line([(hp.px(x), hp.px(y)) for x, y in pts], fill=fill, width=max(1, int(hp.px(width))))


def _draw_frame(anim: str, frame_idx: int, nframes: int):
    del anim, frame_idx, nframes
    img = hp.new_super(FRAME_SIZE)
    d = blending_draw(img)
    # The barrel, with its rib and the front sight.
    _poly(d, [(58, 17), (126, 17), (126, 26), (58, 27)], GUNMETAL)
    _line(d, [(60, 19), (124, 19)], GUNMETAL_HI, 1.1)
    _poly(d, [(119, 13), (123, 13), (124, 17), (118, 17)], GUNMETAL_DARK)
    # The ejector rod housing under the barrel.
    _poly(d, [(58, 27), (98, 27), (98, 31), (58, 31)], GUNMETAL_DARK)
    # The frame, from the hammer to the barrel.
    _poly(d, [(30, 16), (60, 14), (62, 32), (50, 38), (34, 38), (28, 28)], GUNMETAL)
    # The cylinder, with its flutes.
    _poly(d, [(38, 13), (58, 13), (60, 33), (38, 34)], GUNMETAL_DARK)
    for y in (18.0, 23.5, 29.0):
        _line(d, [(41, y), (57, y)], GUNMETAL_HI, 0.9)
    # The hammer.
    _poly(d, [(28, 16), (34, 15), (30, 8), (24, 9), (26, 13)], GUNMETAL_DARK)
    # The brass trigger guard and the trigger.
    _line(d, [(34, 38), (36, 46), (44, 47), (50, 38)], hp.BRASS, 1.8)
    _line(d, [(41, 37), (40, 43)], GUNMETAL_DARK, 1.4)
    # The wooden grip, curving down and back.
    grip = [(27, 26), (36, 37), (33, 47), (24, 58), (12, 58), (14, 50), (20, 40), (22, 30)]
    _poly(d, grip, hp.WOOD)
    _line(d, [(24, 33), (19, 45), (15, 55)], hp.WOOD_HI, 1.2)
    _poly(d, [(12, 56), (24, 56), (24, 60), (12, 60)], hp.BRASS)
    # A pin through the grip.
    d.ellipse([hp.px(23), hp.px(40), hp.px(26), hp.px(43)], fill=hp.BRASS_HI, outline=hp.OUTLINE)
    return hp.finalize(img, FRAME_SIZE)


def _frame_meta(anim: str, frame_idx: int, nframes: int) -> dict:
    del anim, frame_idx, nframes
    return hp.anchor_meta({"grip": GRIP_AT, "muzzle": MUZZLE_AT, "butt": BUTT_AT})


ACTOR_METADATA = {
    "actor": {"character_id": "prop_frontier_revolver", "display_name": "Frontier Revolver"},
    "body": {"body_plan": "Prop", "body_kind": "Standard", "mass_class": "Light", "locomotion_hint": "Held",
             "traits": ["prop", "weapon", "gun", "revolver", "frontier"]},
    "brain": {"default_preset": "stand_still"},
    "actions": {"default_preset": "peaceful"},
    "animation_bindings": {"default": {"animation": "idle", "events": []}},
    "sockets": {
        name: {"source": f"{TARGET_NAME}.geometry", "point": {"x": p[0], "y": p[1]}}
        for name, p in (("grip", GRIP_AT), ("muzzle", MUZZLE_AT), ("butt", BUTT_AT))
    },
    "tags": ["prop", "weapon", "gun", "frontier"],
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
    return [outputs[k] for k in ("canonical", "canonical_transparent", "spritesheet", "yaml", "ron", "actor", "preview")]


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
