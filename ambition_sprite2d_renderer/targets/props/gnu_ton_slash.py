"""The strike of GNU-ton's quill: a stroke of ink, as a pen makes it.

The game sizes this effect to the hit volume of the move and turns it along
the strike (`rendering/slash_visuals.rs`), as it does the robot's
(`robot_slash.py`). So each row is in SWING SPACE: `x = 0` is his hand,
`x = REACH` is the tip of the strike, and `y` is across it.

A row is one stroke of a pen: the full stroke is there on the first frame
(the blow lands with its picture), then the pen lifts: the stroke goes thin
from the hand's end, breaks, and drops of ink fly off the tip. The last frame
is clear.

- ``side``: a swash, a little bowed. The jab, the thrust, the book.
- ``up``: a flourish, with a curl at its end. The strikes over his head.
- ``down``: a flat stroke that spatters. The low sweep, the strikes under him.

The colours are his: the cream of his paper in the middle, the blue ink of his
coat at the edge. A stroke of dark ink alone does not show on a dark room.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Tuple

from PIL import Image

from ...authoring.sheet_build import build_sheet
from ...core.draw import blending_draw

TARGET_NAME = "gnu_ton_slash"
SHEET_FILES = (
    f"{TARGET_NAME}_spritesheet.png",
    f"{TARGET_NAME}_spritesheet.yaml",
    f"{TARGET_NAME}_spritesheet.ron",
    f"{TARGET_NAME}_actor.ron",
)

FRAME_SIZE = (192, 96)
SUPER = 4
# Six frames of 24 ms: the stroke is there for the live part of a quick move
# (his jab is live for 0.1 s) and its ink is gone a little after.
ROWS: List[Tuple[str, int, int]] = [
    ("side", 6, 24),
    ("up", 6, 24),
    ("down", 6, 24),
]

PAPER = (255, 250, 232)
CREAM = (244, 226, 178)
INK = (38, 48, 112)
INK_DEEP = (22, 26, 66)

REACH = float(FRAME_SIZE[0])
AXIS_Y = FRAME_SIZE[1] / 2.0
#: The stroke starts and stops a little inside the frame: the game stretches
#: the frame onto the hit volume, and the art is all inside it.
T_NEAR, T_FAR = 0.05, 0.95

#: For each row: how far the stroke bows (in half heights of the frame; over
#: the axis is negative), its thickest width (the same unit), where along it
#: that is, and how far its end hooks back.
SHAPES = {
    "side": {"bow": -0.5, "belly": 0.82, "peak": 0.55, "hook": 0.0},
    "up": {"bow": -0.62, "belly": 0.72, "peak": 0.45, "hook": 1.0},
    "down": {"bow": 0.42, "belly": 0.7, "peak": 0.62, "hook": 0.0},
}

#: Drops of ink off the stroke: where each starts along it, its way (x along
#: the strike, y across), and its size (in half heights of the frame).
DROPS = {
    "side": [(0.92, (0.07, -0.34), 0.13), (0.8, (0.04, 0.5), 0.1), (0.98, (0.1, 0.16), 0.08), (0.62, (-0.02, -0.5), 0.07)],
    "up": [(0.9, (0.05, -0.4), 0.12), (0.74, (0.0, -0.6), 0.09), (0.55, (-0.04, 0.4), 0.07)],
    "down": [(0.9, (0.07, 0.5), 0.13), (0.72, (0.03, 0.62), 0.1), (0.5, (0.0, 0.6), 0.08), (0.97, (0.1, -0.2), 0.07)],
}


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _smooth(edge0: float, edge1: float, value: float) -> float:
    t = _clamp((value - edge0) / (edge1 - edge0))
    return t * t * (3.0 - 2.0 * t)


def _outer(shape: dict, t: float) -> Tuple[float, float]:
    """The outer edge of the stroke at `t` (0 at the hand, 1 at the tip): the
    way the nib went."""
    half = FRAME_SIZE[1] / 2.0
    x = REACH * (T_NEAR + (T_FAR - T_NEAR) * t)
    # The far side of the axis from the bow, so the stroke is in the frame.
    y = AXIS_Y - shape["bow"] * half * 0.42 + shape["bow"] * half * 1.3 * math.sin(math.pi * t) ** 0.85
    if shape["hook"] > 0.0 and t > 0.6:
        # The flourish: the end of the stroke comes round, toward the hand.
        k = _smooth(0.6, 1.0, t)
        x -= REACH * 0.16 * shape["hook"] * k * k
        y += half * 0.5 * shape["hook"] * k * k * (-1.0 if shape["bow"] < 0.0 else 1.0) * -1.0
    return x, y


def _width(shape: dict, t: float) -> float:
    """The width of the full stroke at `t`: a nib that is pressed, then lifted
    to a hair."""
    # One smooth curve with its top at `peak`: two curves that meet there
    # make a notch in the edge.
    k = _clamp(t) ** (math.log(0.5) / math.log(shape["peak"]))
    return shape["belly"] * (FRAME_SIZE[1] / 2.0) * math.sin(math.pi * k) ** 1.15


def _stroke(shape: dict, t0: float, t1: float, width: float, inset: float) -> list:
    """The outline of the stroke from `t0` to `t1`: its outer edge, and an
    inner edge `width` of the full width in from it. `inset` moves the outer
    edge in (the paper in the middle of the ink)."""
    steps = 48
    outer, inner = [], []
    inward = 1.0 if shape["bow"] < 0.0 else -1.0
    for i in range(steps + 1):
        t = t0 + (t1 - t0) * i / steps
        x, y = _outer(shape, t)
        # A part of the stroke has a point at each of its ends.
        ends = math.sin(math.pi * i / steps) ** 0.4 if (t0, t1) != (0.0, 1.0) else 1.0
        full = _width(shape, t) * ends
        outer.append((x, y + inward * full * inset))
        inner.append((x, y + inward * full * max(inset, width)))
    return outer + inner[::-1]


def _scaled(points) -> list:
    return [(x * SUPER, y * SUPER) for x, y in points]


def _drop(draw, at: Tuple[float, float], way: Tuple[float, float], radius: float) -> None:
    """A drop of ink that flies: round at its head, a point behind it."""
    if radius <= 0.4:
        return
    norm = math.hypot(*way) or 1.0
    ux, uy = way[0] / norm, way[1] / norm
    for grow, fill in ((1.5, CREAM), (0.0, INK)):
        r = radius + grow
        tail = (at[0] - ux * r * 2.6, at[1] - uy * r * 2.6)
        side = (-uy * r, ux * r)
        draw.polygon(
            _scaled([(at[0] + side[0], at[1] + side[1]), tail, (at[0] - side[0], at[1] - side[1])]),
            fill=fill + (255,),
        )
        x, y = at[0] * SUPER, at[1] * SUPER
        draw.ellipse((x - r * SUPER, y - r * SUPER, x + r * SUPER, y + r * SUPER), fill=fill + (255,))


def _draw_frame(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
    p = frame_idx / max(1, frame_count - 1)
    shape = SHAPES[animation]
    canvas = Image.new("RGBA", (FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER), (0, 0, 0, 0))
    if p >= 1.0:
        return canvas.resize(FRAME_SIZE, Image.Resampling.LANCZOS)
    draw = blending_draw(canvas)
    half = FRAME_SIZE[1] / 2.0

    # The pen lifts: the stroke goes from the hand's end, and goes thin. The
    # paper in it goes first, and a line of ink is left.
    start = 0.8 * _smooth(0.0, 0.9, p)
    thin = 1.0 - 0.8 * _smooth(0.1, 1.0, p)
    paper = 1.0 - _smooth(0.2, 0.7, p)
    span = (start, 1.0) if start > 0.0 else (0.0, 1.0)
    draw.polygon(_scaled(_stroke(shape, *span, thin, 0.0)), fill=INK_DEEP + (255,))
    draw.polygon(_scaled(_stroke(shape, *span, thin * 0.94, 0.05)), fill=INK + (255,))
    if paper > 0.05:
        draw.polygon(_scaled(_stroke(shape, *span, thin * (0.34 + 0.52 * paper), 0.34)), fill=CREAM + (255,))
        draw.polygon(_scaled(_stroke(shape, *span, thin * (0.34 + 0.3 * paper), 0.46)), fill=PAPER + (255,))

    # Drops of ink off the stroke: out, and smaller.
    fly = _smooth(0.0, 1.0, p)
    for t, (vx, vy), size in DROPS[animation]:
        if p <= 0.0:
            continue
        x, y = _outer(shape, t)
        at = (x + vx * REACH * fly * 1.5, y + vy * half * fly * 1.3 + 0.2 * half * fly * fly)
        _drop(draw, at, (vx * REACH, vy * half + 0.4 * half * fly), size * half * (1.0 - 0.7 * p))
    return canvas.resize(FRAME_SIZE, Image.Resampling.LANCZOS)


def _frame_meta(animation: str, frame_idx: int, frame_count: int) -> dict:
    return {
        "anchors": {
            "origin": {"x": 0.0, "y": AXIS_Y},
            "tip": {"x": REACH, "y": AXIS_Y},
        },
        "effect": {"kind": animation, "progress": round(frame_idx / max(1, frame_count - 1), 4)},
    }


ACTOR_METADATA = {
    "actor": {"character_id": "fx_gnu_ton_slash", "display_name": "GNU-ton Quill Stroke"},
    "body": {
        "body_plan": "Effect",
        "body_kind": "Slash",
        "locomotion_hint": "Stationary",
        "traits": ["fx", "slash", "melee", "overlay"],
    },
    "brain": {"default_preset": "stand_still"},
    "actions": {"default_preset": "peaceful"},
    "animation_bindings": {
        "default": {"animation": "side", "events": []},
        "action.melee.side": {"animation": "side", "events": []},
        "action.melee.up": {"animation": "up", "events": []},
        "action.melee.down_air": {"animation": "down", "events": []},
    },
    "sockets": {
        "origin": {"source": f"{TARGET_NAME}.geometry", "point": {"x": 0.0, "y": AXIS_Y}},
    },
    "tags": ["fx", "slash", "melee", "overlay"],
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
        # The game samples this sheet as a grid of whole frames.
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
