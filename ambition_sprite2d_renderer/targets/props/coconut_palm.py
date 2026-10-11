"""Coconut palm: a tree for a room, with coconuts under its crown.

Scenery (an LDtk `Prop`): a bent ringed trunk and a crown of fronds that
hang, with a cluster of green coconuts under it. It has no collision. A
coconut that can be picked up is a thing of the world (the `coconut` held
prop), not a part of this picture: a room puts those on the ground by the
tree.

Animations:

- ``idle``: 6 frames. The fronds sway in a slow wind; the trunk holds still.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Tuple

from PIL import Image

from ...authoring.sheet_build import build_sheet
from . import _held_prop_common as hp
from ambition_sprite2d_renderer.core.draw import blending_draw

TARGET_NAME = "coconut_palm"
SHEET_FILES = (
    f"{TARGET_NAME}_spritesheet.png",
    f"{TARGET_NAME}_spritesheet.yaml",
    f"{TARGET_NAME}_spritesheet.ron",
    f"{TARGET_NAME}_actor.ron",
)

FRAME_SIZE = (220, 250)
ROWS: List[Tuple[str, int, int]] = [("idle", 6, 220)]

#: Where the trunk stands and where its crown is, in frame pixels.
FOOT = (104.0, 246.0)
CROWN = (120.0, 82.0)

TRUNK = (132, 96, 58, 255)
TRUNK_HI = (170, 132, 84, 255)
TRUNK_DARK = (84, 56, 30, 255)
LEAF = (58, 146, 62, 255)
LEAF_HI = (112, 190, 84, 255)
LEAF_DARK = (30, 92, 44, 255)
NUT = (92, 132, 52, 255)
NUT_HI = (140, 176, 78, 255)
NUT_RIPE = (122, 78, 42, 255)


def _trunk_at(t: float) -> Tuple[float, float]:
    """The middle of the trunk `t` (0 foot .. 1 crown) of the way up: a lean
    that is all in its lower half."""
    x = FOOT[0] + (CROWN[0] - FOOT[0]) * (1.0 - (1.0 - t) ** 2.2)
    y = FOOT[1] + (CROWN[1] - FOOT[1]) * t
    return x, y


def _frond(d, angle: float, length: float, sway: float, colour, rib) -> None:
    """One frond from the crown: a rib that arches out and hangs, with
    leaflets to each side of it."""
    p = hp.px
    a = math.radians(angle + sway)
    tip = (CROWN[0] + math.cos(a) * length, CROWN[1] + math.sin(a) * length * 0.62 + length * 0.42)
    ctrl = (CROWN[0] + math.cos(a) * length * 0.62, CROWN[1] + math.sin(a) * length * 0.6 - length * 0.26)
    pts = []
    for i in range(15):
        t = i / 14.0
        pts.append(((1 - t) ** 2 * CROWN[0] + 2 * (1 - t) * t * ctrl[0] + t * t * tip[0],
                    (1 - t) ** 2 * CROWN[1] + 2 * (1 - t) * t * ctrl[1] + t * t * tip[1]))
    for i in range(1, 15):
        t = i / 14.0
        (x0, y0), (x1, y1) = pts[i - 1], pts[i]
        dx, dy = x1 - x0, y1 - y0
        n = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / n, dx / n
        leaf = 15.0 * math.sin(math.pi * min(1.0, t * 1.15)) + 3.0
        # a leaflet hangs: each side goes out from the rib and down
        for side in (-1.0, 1.0):
            end = (x1 + nx * side * leaf * 0.7 - dx / n * 2.0, y1 + ny * side * leaf * 0.7 + leaf * 0.55)
            d.polygon([(p(x0), p(y0)), (p(x1), p(y1)), (p(end[0]), p(end[1]))], fill=colour)
    d.line([(p(x), p(y)) for x, y in pts], fill=rib, width=max(1, int(p(1.6))), joint="curve")


def _draw_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    if anim != "idle":
        raise ValueError(f"unknown animation: {anim}")
    sway = 4.0 * math.sin(math.tau * frame_idx / max(1, nframes))
    canvas = hp.new_super(FRAME_SIZE)
    d = blending_draw(canvas)
    p = hp.px
    # The fronds behind the trunk's head.
    for angle, length in ((-160.0, 78.0), (-20.0, 82.0), (-125.0, 70.0), (-55.0, 72.0)):
        _frond(d, angle, length, sway * 0.6, LEAF_DARK, LEAF_DARK)
    # The trunk: rings, wider at the foot.
    steps = 22
    for i in range(steps):
        t0, t1 = i / steps, (i + 1) / steps
        (x0, y0), (x1, y1) = _trunk_at(t0), _trunk_at(t1)
        w0, w1 = 11.0 - 5.0 * t0, 11.0 - 5.0 * t1
        d.polygon([(p(x0 - w0), p(y0)), (p(x0 + w0), p(y0)), (p(x1 + w1), p(y1)), (p(x1 - w1), p(y1))],
                  fill=TRUNK if i % 2 else TRUNK_HI, outline=hp.OUTLINE)
        d.line([(p(x0 - w0 + 1), p(y0 - 1)), (p(x0 + w0 - 1), p(y0 - 1))], fill=TRUNK_DARK, width=max(1, int(p(0.8))))
    # The coconuts, in a cluster under the crown.
    for (dx, dy, r, ripe) in ((-9.0, 10.0, 7.5, False), (6.0, 12.0, 8.0, True), (-1.0, 18.0, 7.0, False), (13.0, 5.0, 6.5, False)):
        cx, cy = CROWN[0] + dx, CROWN[1] + dy
        d.ellipse((p(cx - r), p(cy - r), p(cx + r), p(cy + r)), fill=NUT_RIPE if ripe else NUT, outline=hp.OUTLINE,
                  width=max(1, int(p(1.0))))
        if not ripe:
            d.ellipse((p(cx - r * 0.55), p(cy - r * 0.6), p(cx + r * 0.1), p(cy - r * 0.05)), fill=NUT_HI)
    # The fronds in front, and the bud at the top.
    for angle, length in ((-178.0, 92.0), (-142.0, 96.0), (-100.0, 84.0), (-72.0, 88.0), (-38.0, 96.0), (-4.0, 92.0)):
        _frond(d, angle, length, sway, LEAF, LEAF_HI)
    d.ellipse((p(CROWN[0] - 8), p(CROWN[1] - 9), p(CROWN[0] + 8), p(CROWN[1] + 6)), fill=LEAF_DARK, outline=hp.OUTLINE,
              width=max(1, int(p(1.0))))
    return hp.finalize(canvas, FRAME_SIZE)


def _frame_meta(anim: str, frame_idx: int, nframes: int) -> dict:
    del anim, frame_idx, nframes
    return hp.anchor_meta({"foot": FOOT, "crown": CROWN}, forward=(0.0, -1.0))


ACTOR_METADATA = {
    "actor": {"character_id": "prop_coconut_palm", "display_name": "Coconut Palm"},
    "body": {
        "body_plan": "Prop",
        "body_kind": "Scenery",
        "mass_class": "Heavy",
        "locomotion_hint": "Static",
        "traits": ["prop", "tree", "palm", "scenery"],
    },
    "brain": {"default_preset": "stand_still"},
    "actions": {"default_preset": "peaceful"},
    "animation_bindings": {"default": {"animation": "idle", "events": []}},
    "sockets": {
        "foot": {"source": f"{TARGET_NAME}.geometry", "point": {"x": FOOT[0], "y": FOOT[1]}},
        "crown": {"source": f"{TARGET_NAME}.geometry", "point": {"x": CROWN[0], "y": CROWN[1]}},
    },
    "tags": ["prop", "tree", "palm", "scenery"],
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


__all__ = ["ACTOR_METADATA", "FRAME_SIZE", "ROWS", "TARGET_NAME", "render"]
