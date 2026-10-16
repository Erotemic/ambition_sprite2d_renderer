"""The chain gun of the Iron Trooper (``evil_heavy``): a held prop.

A heavy rotary gun of the Evil dimension's regime: a cluster of barrels in
two clamps, an iron body with a carry handle, a pistol grip at the rear, a
second grip under the barrels, a box of ammunition under the body with a
belt going in, and a red plate with the faction's invented cog
(``_evil_faction``; not a real symbol).

It is drawn as the held props are (``_held_prop_common``): flat, the muzzle
pointing RIGHT (+x). The game pins it at ``grip`` (the pistol grip, the
trigger hand) and turns it to aim. ``fore_grip`` is where the other hand
holds it, ``muzzle`` where a shot leaves it, ``butt`` its rear end.

Rows: ``idle`` (one frame; the canonical picture) and ``spin`` (the barrels
turn, for while it fires).
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Tuple

from PIL import Image

from ...authoring.sheet_build import build_sheet
from ambition_sprite2d_renderer.core.draw import blending_draw
from ..characters import _evil_faction as F
from ..characters._ai_era_kit import OUTLINE, WHITE, Kit, RGBA, mix
from . import _held_prop_common as hp

TARGET_NAME = "evil_chain_gun"
SHEET_FILES = (
    f"{TARGET_NAME}_spritesheet.png",
    f"{TARGET_NAME}_spritesheet.yaml",
    f"{TARGET_NAME}_spritesheet.ron",
    f"{TARGET_NAME}_actor.ron",
)

FRAME_SIZE = (184, 72)
ROWS: List[Tuple[str, int, int]] = [("idle", 1, 200), ("spin", 4, 40)]

K = Kit(FRAME_SIZE)

IRON: RGBA = (100, 106, 118, 255)
IRON_DARK: RGBA = (62, 66, 78, 255)
IRON_DEEP: RGBA = (40, 42, 52, 255)
IRON_LIGHT: RGBA = (170, 176, 188, 255)
BARREL: RGBA = (74, 78, 90, 255)
BARREL_LIGHT: RGBA = (150, 156, 170, 255)
GRIP: RGBA = (60, 44, 36, 255)
GRIP_LIGHT: RGBA = (104, 78, 60, 255)
BRASS: RGBA = (204, 160, 76, 255)
BRASS_DARK: RGBA = (130, 96, 40, 255)

#: Anchors, in frame pixels.
GRIP_AT = (56.0, 55.0)
FORE_GRIP_AT = (114.0, 52.0)
MUZZLE_AT = (176.0, 30.0)
BUTT_AT = (24.0, 32.0)
#: The middle line of the barrels.
AXIS = 30.0


def _body():
    """The body: the back plate, the receiver, the carry handle, the two
    grips and the ammunition box. Painted about ``home`` = the frame's
    (0, 0)."""

    def at(x: float, y: float):
        return K.at(x, y)

    def shape(d) -> None:
        K.poly(d, [at(22.0, 22.0), at(34.0, 20.0), at(34.0, 44.0), at(24.0, 42.0)], WHITE)
        K.rrect(d, K.home[0] + 32.0, K.home[1] + 20.0, K.home[0] + 100.0, K.home[1] + 42.0, 3.0, WHITE)
        K.stroke(d, [at(50.0, 20.0), at(54.0, 11.0), at(84.0, 11.0), at(88.0, 20.0)], WHITE, 4.0)
        K.poly(d, [at(50.0, 40.0), at(62.0, 40.0), at(60.0, 62.0), at(50.0, 62.0)], WHITE)
        K.poly(d, [at(108.0, 38.0), at(118.0, 38.0), at(118.0, 60.0), at(110.0, 60.0)], WHITE)
        K.rrect(d, K.home[0] + 66.0, K.home[1] + 40.0, K.home[0] + 96.0, K.home[1] + 60.0, 2.0, WHITE)

    def detail(d) -> None:
        # The grips are wood.
        K.poly(d, [at(50.0, 41.0), at(62.0, 41.0), at(60.0, 70.0), at(40.0, 70.0)], GRIP)
        K.poly(d, [at(108.0, 39.0), at(118.0, 39.0), at(130.0, 70.0), at(100.0, 70.0)], GRIP)
        for y in (46.0, 50.0, 54.0, 58.0):
            K.line(d, [at(51.0, y), at(60.0, y - 1.0)], GRIP_LIGHT, 0.5)
            K.line(d, [at(109.4, y), at(117.4, y)], GRIP_LIGHT, 0.5)
        # The ammunition box, darker, with its lid.
        K.rrect(d, K.home[0] + 66.0, K.home[1] + 40.0, K.home[0] + 96.0, K.home[1] + 70.0, 0.0, IRON_DARK)
        K.line(d, [at(66.0, 44.0), at(96.0, 44.0)], IRON_DEEP, 0.7)
        K.line(d, [at(68.0, 41.4), at(94.0, 41.4)], IRON, 0.6)
        # Seams and rivets of the receiver; the trigger guard.
        K.line(d, [at(34.0, 21.0), at(34.0, 41.0)], IRON_DEEP, 0.7)
        K.line(d, [at(36.0, 23.0), at(98.0, 23.0)], IRON_LIGHT, 0.7)
        for x in (38.0, 46.0, 92.0, 98.0):
            for y in (26.0, 38.0):
                K.oval(d, at(x, y), 0.8, 0.8, IRON_LIGHT, OUTLINE, 0.3)
        # The plate with the mark of the regime.
        K.rrect(d, K.home[0] + 58.0, K.home[1] + 25.0, K.home[0] + 76.0, K.home[1] + 37.0, 1.0, F.RED, OUTLINE, 0.5)
        K.oval(d, at(67.0, 31.0), 4.6, 4.6, OUTLINE)
        K.oval(d, at(67.0, 31.0), 4.1, 4.1, F.DISC)
        F.cog(K, d, at(67.0, 31.0), 3.3)

    return K.solid(("gun_body",), shape, IRON, detail, outline=1.3, rim=0.35, shade=0.35, shade_colour=IRON_DEEP)


def _barrels(phase: int):
    """The barrel cluster from the receiver to the muzzle; ``phase`` (0-3) is
    how far it has turned, so the light is on another barrel."""

    def shape(d) -> None:
        K.rrect(d, K.home[0] + 98.0, K.home[1] + AXIS - 7.0, K.home[0] + 176.0, K.home[1] + AXIS + 7.0, 2.0, WHITE)
        for x in (104.0, 136.0, 168.0):
            K.rrect(d, K.home[0] + x, K.home[1] + AXIS - 9.0, K.home[0] + x + 7.0, K.home[1] + AXIS + 9.0, 1.4, WHITE)

    def detail(d) -> None:
        for k, dy in enumerate((-4.6, 0.0, 4.6)):
            lit = (k + phase) % 4 == 0
            K.rrect(d, K.home[0] + 98.0, K.home[1] + AXIS + dy - 2.0, K.home[0] + 176.0, K.home[1] + AXIS + dy + 2.0, 1.0,
                    BARREL_LIGHT if lit else BARREL)
            K.line(d, [K.at(98.0, AXIS + dy + 2.3), K.at(176.0, AXIS + dy + 2.3)], IRON_DEEP, 0.7)
        for x in (104.0, 136.0, 168.0):
            K.rrect(d, K.home[0] + x, K.home[1] + AXIS - 9.0, K.home[0] + x + 7.0, K.home[1] + AXIS + 9.0, 1.4, IRON, OUTLINE, 0.5)
            K.line(d, [K.at(x + 1.4, AXIS - 7.6), K.at(x + 1.4, AXIS + 7.6)], IRON_LIGHT, 0.6)
        # The dark mouths of the barrels at the muzzle.
        for dy in (-4.6, 0.0, 4.6):
            K.oval(d, K.at(175.4, AXIS + dy), 0.8, 1.2, IRON_DEEP)

    return K.solid(("gun_barrels", phase), shape, BARREL, detail, outline=1.3, rim=0.3, shade=0.3, shade_colour=IRON_DEEP)


def _belt():
    """The belt of cartridges from the box, hanging in a loop."""

    def paint(d) -> None:
        pts = [(70.0 + 6.0 * k, 61.0 + 4.0 * math.sin(math.pi * k / 4.0)) for k in range(5)]
        for x, y in pts:
            K.rrect(d, K.home[0] + x - 1.8, K.home[1] + y - 3.2, K.home[0] + x + 1.8, K.home[1] + y + 3.2, 0.8, BRASS, OUTLINE, 0.5)
            K.line(d, [K.at(x - 1.4, y - 1.6), K.at(x + 1.4, y - 1.6)], BRASS_DARK, 0.5)

    return K.piece(("gun_belt",), paint)


def _draw_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    del nframes
    if anim not in ("idle", "spin"):
        raise ValueError(f"unknown animation: {anim}")
    phase = frame_idx % 4 if anim == "spin" else 0
    img = K.new_frame()
    origin = (0.0, 0.0)
    K.place(img, _barrels(phase), origin, "barrels")
    K.place(img, _body(), origin, "body")
    K.place(img, _belt(), origin, "belt")
    return K.downsample(img)


def _frame_meta(anim: str, frame_idx: int, nframes: int) -> dict:
    del anim, frame_idx, nframes
    return hp.anchor_meta({"grip": GRIP_AT, "fore_grip": FORE_GRIP_AT, "muzzle": MUZZLE_AT, "butt": BUTT_AT})


ACTOR_METADATA = {
    "actor": {"character_id": "prop_evil_chain_gun", "display_name": "Chain Gun"},
    "body": {"body_plan": "Prop", "body_kind": "Standard", "mass_class": "Heavy", "locomotion_hint": "Held",
             "traits": ["prop", "weapon", "gun", "chain_gun", "evil_faction"]},
    "brain": {"default_preset": "stand_still"},
    "actions": {"default_preset": "peaceful"},
    "animation_bindings": {"default": {"animation": "idle", "events": []}, "action.ranged.primary": {"animation": "spin", "events": []}},
    "sockets": {
        name: {"source": f"{TARGET_NAME}.geometry", "point": {"x": p[0], "y": p[1]}}
        for name, p in (("grip", GRIP_AT), ("fore_grip", FORE_GRIP_AT), ("muzzle", MUZZLE_AT), ("butt", BUTT_AT))
    },
    "tags": ["prop", "weapon", "gun", "evil_faction"],
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
