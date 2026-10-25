"""Gate cradle: the stand a dimension gate ring sits in.

Scenery (an LDtk `Prop`): a limestone plinth with a frieze of hexagonal tiles
and the lemniscate on its face, stairs up to it at each end, and two pylons
whose brass arms hold the ring at three and nine o'clock. The ring and its
portal are their own props (`gate_ring`, `gate_portal`) and stand on the
plinth; nothing of the ring or of a portal is painted here (portals are drawn
by the portal presentation, never in art).

A body walks it on one line the room places along the noses of the treads
and over the plinth (a hidden `SurfaceChain`, `walkable_lines`): up one stair
(`STEPS` treads of `STEP_RUN` by `STEP_RISE` units), across, down the other.
Each tread's top is the one light line of its step.

Units: one design unit is one world unit; the frame has `PX` pixels to the
unit. The bottom of the frame is the floor.

Animations:

- ``idle``: 1 frame.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Tuple

from PIL import Image

from ...authoring.sheet_build import build_sheet
from . import _held_prop_common as hp
from ambition_sprite2d_renderer.core.draw import blending_draw

TARGET_NAME = "gate_cradle"

#: Pixels of the frame to one world unit.
PX = 2
#: The cradle in world units: the plinth, the stairs at each end, the ring it holds.
PLINTH_W, PLINTH_H = 288, 48
STEP_RUN, STEP_RISE = 8, 4
STEPS = PLINTH_H // STEP_RISE
STAIR_W = STEPS * STEP_RUN
WIDTH = PLINTH_W + 2 * STAIR_W
#: The ring is 288 units (1.5 of its 192 design units: `interdimensional_gate`).
RING_R = 69.0 * 1.5
#: The ring's centre over the plinth top (the ring sheet's body bottom is 71
#: design units under its centre: the outer band and its two low clamps).
RING_LIFT = 71.0 * 1.5
PYLON_TOP = PLINTH_H + RING_LIFT + 40.0
HEIGHT = int(PYLON_TOP + 18)

FRAME_SIZE = (WIDTH * PX, HEIGHT * PX)
ROWS: List[Tuple[str, int, int]] = [("idle", 1, 400)]

STONE = (214, 202, 178, 255)
STONE_HI = (240, 232, 214, 255)
STONE_DARK = (150, 138, 118, 255)
JOINT = (122, 110, 94, 255)
TILE = (70, 108, 160, 255)
TILE_DARK = (44, 70, 110, 255)
GOLD = (214, 170, 84, 255)
WALK = (255, 252, 240, 255)


def _u(v: float) -> float:
    """World units -> supersample pixels."""
    return hp.px(v * PX)


def _y(units_up: float) -> float:
    """A height over the floor -> a supersample y."""
    return _u(HEIGHT - units_up)


def _box(d, x0, up0, x1, up1, fill, outline=None, width=1.0) -> None:
    d.rectangle((_u(x0), _y(up1), _u(x1), _y(up0)), fill=fill, outline=outline, width=max(1, int(_u(width))))


def _stairs(d, plinth_edge: float, outward: int) -> None:
    """The stairs from the floor up to the plinth on the side `outward`
    points to (-1 left, +1 right) of the plinth edge at `plinth_edge`. Tread
    `j` (1 to `STEPS`) is `j * STEP_RISE` high; the highest is beside the
    plinth and as high as it."""
    for j in range(1, STEPS + 1):
        top = j * STEP_RISE
        near = plinth_edge + outward * (STEPS - j) * STEP_RUN
        far = near + outward * STEP_RUN
        x0, x1 = min(near, far), max(near, far)
        _box(d, x0, 0, x1, top, STONE)
        _box(d, x0, top - 0.8, x1, top, WALK)
        _box(d, x0, top - 0.6 - STEP_RISE, x1, top - STEP_RISE, JOINT)
    outer = plinth_edge + outward * STAIR_W
    _box(d, min(outer, outer - outward * 1.2), 0, max(outer, outer - outward * 1.2), STEP_RISE, JOINT)


def _hex_band(d, x0: float, x1: float, up0: float, up1: float) -> None:
    r = 4.0
    dx, dy = r * math.sqrt(3), r * 1.5
    _box(d, x0, up0, x1, up1, TILE_DARK)
    j = 0
    row = 0
    v = up1 - r
    while v > up0 + r * 0.5:
        u = x0 + r + (row % 2) * dx / 2
        while u < x1 - r * 0.5:
            j += 1
            pts = [(_u(u + r * 0.88 * math.cos(math.radians(30 + 60 * k))), _y(v + r * 0.88 * math.sin(math.radians(30 + 60 * k)))) for k in range(6)]
            d.polygon(pts, fill=GOLD if j % 7 == 0 else TILE)
            u += dx
        v -= dy
        row += 1


def _pylon(d, cx: float, ring_side: int) -> None:
    """A pylon of cut stone on the plinth at `cx`, its brass arm reaching
    toward the ring on `ring_side` (+1 right, -1 left), and a tetrahedron
    on its head."""
    w = 26.0
    base = PLINTH_H
    _box(d, cx - w / 2, base, cx + w / 2, PYLON_TOP, STONE, hp.OUTLINE, 1.2)
    # The courses of the pylon, and its lit and its shaded side.
    for up in range(int(base) + 14, int(PYLON_TOP), 14):
        _box(d, cx - w / 2 + 1, up, cx + w / 2 - 1, up + 0.6, JOINT)
    _box(d, cx - w / 2 + 1.2, base + 1, cx - w / 2 + 4, PYLON_TOP - 1, STONE_HI)
    _box(d, cx + w / 2 - 5, base + 1, cx + w / 2 - 1.2, PYLON_TOP - 1, STONE_DARK)
    # The head: a tetrahedron seen from the front, its two faces lit and shaded.
    top = PYLON_TOP
    apex = (_u(cx), _y(top + 16))
    d.polygon([(_u(cx - w / 2 - 2), _y(top)), (_u(cx), _y(top)), apex], fill=STONE_HI, outline=hp.OUTLINE)
    d.polygon([(_u(cx), _y(top)), (_u(cx + w / 2 + 2), _y(top)), apex], fill=STONE_DARK, outline=hp.OUTLINE)
    # The brass arm, level with the ring's centre, ending just short of its rim.
    centre_up = PLINTH_H + RING_LIFT
    ring_x = WIDTH / 2 - ring_side * RING_R
    near = cx + ring_side * w / 2
    end = ring_x - ring_side * 1.0
    x0, x1 = min(near, end), max(near, end)
    _box(d, x0, centre_up - 5, x1, centre_up + 5, hp.BRASS, hp.OUTLINE, 1.0)
    _box(d, x0, centre_up + 3, x1, centre_up + 5, hp.BRASS_HI)
    for bolt in (x0 + 4, x1 - 4):
        d.ellipse((_u(bolt - 1.6), _y(centre_up + 1.6), _u(bolt + 1.6), _y(centre_up - 1.6)), fill=hp.BRASS_DARK)


def _lemniscate(d, cx: float, cy_up: float, a: float) -> None:
    pts = []
    for i in range(121):
        t = i / 120 * math.tau
        den = 1 + math.sin(t) ** 2
        pts.append((_u(cx + a * math.cos(t) / den), _y(cy_up + a * math.sin(t) * math.cos(t) / den)))
    d.line(pts, fill=GOLD, width=max(1, int(_u(1.6))), joint="curve")


def _draw_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    del frame_idx, nframes
    if anim != "idle":
        raise ValueError(f"unknown animation: {anim}")
    canvas = hp.new_super(FRAME_SIZE)
    d = blending_draw(canvas)
    px0, px1 = STAIR_W, STAIR_W + PLINTH_W
    # The plinth: courses of limestone, a frieze of tiles, a cornice whose top
    # is the walk line, and the lemniscate on a plaque in the middle.
    _box(d, px0, 0, px1, PLINTH_H, STONE, hp.OUTLINE, 1.2)
    for up in (12, 24):
        _box(d, px0 + 1, up, px1 - 1, up + 0.6, JOINT)
    for k, x in enumerate(range(int(px0) + 24, int(px1), 36)):
        lo, hi = (0, 12) if k % 2 else (12, 24)
        _box(d, x, lo, x + 0.6, hi, JOINT)
    _hex_band(d, px0 + 2, px1 - 2, 27, 39)
    _box(d, px0 - 4, PLINTH_H - 6, px1 + 4, PLINTH_H, STONE_HI, hp.OUTLINE, 1.0)
    _box(d, px0 - 4, PLINTH_H - 1.2, px1 + 4, PLINTH_H, WALK)
    plaque_w = 44
    cx = WIDTH / 2
    _box(d, cx - plaque_w / 2, 4, cx + plaque_w / 2, 22, STONE_HI, hp.OUTLINE, 1.0)
    _lemniscate(d, cx, 13, 14)
    # The stairs at each end.
    _stairs(d, px0, -1)
    _stairs(d, px1, +1)
    # The pylons, outside the ring, each with its arm.
    _pylon(d, cx - RING_R - 26, +1)
    _pylon(d, cx + RING_R + 26, -1)
    return hp.finalize(canvas, FRAME_SIZE)


def _frame_meta(anim: str, frame_idx: int, nframes: int) -> dict:
    del anim, frame_idx, nframes
    return hp.anchor_meta({"foot": (FRAME_SIZE[0] / 2, FRAME_SIZE[1]), "ring_centre": (FRAME_SIZE[0] / 2, (HEIGHT - PLINTH_H - RING_LIFT) * PX)}, forward=(0.0, -1.0))


ACTOR_METADATA = {
    "actor": {"character_id": "prop_gate_cradle", "display_name": "Gate Cradle"},
    "body": {
        "body_plan": "Prop",
        "body_kind": "Scenery",
        "mass_class": "Heavy",
        "locomotion_hint": "Static",
        "traits": ["prop", "gate", "scenery"],
    },
    "brain": {"default_preset": "stand_still"},
    "actions": {"default_preset": "peaceful"},
    "animation_bindings": {"default": {"animation": "idle", "events": []}},
    "tags": ["prop", "gate", "scenery"],
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
        auto_crop=False,
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


__all__ = ["ACTOR_METADATA", "FRAME_SIZE", "ROWS", "TARGET_NAME", "WIDTH", "HEIGHT", "PLINTH_H", "STEP_RUN", "STEP_RISE", "STEPS", "RING_LIFT", "render"]
