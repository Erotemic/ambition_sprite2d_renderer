"""Robot melee slash effect — a broad, readable Hollow-Knight-style sweep.

The game sizes this effect to the resolved melee hitbox and selects a row for
the attack pose. The runtime rotates rows only with the gravity frame and uses
a local horizontal mirror for left-facing side attacks, so facing never turns
the asymmetric accent layers upside down.

The five-frame, 120 ms rows preserve the existing lifetime, but now begin in
the fully active state for Hollow-Knight-like responsiveness:

- impact: a broad white cut is already out on frame 0,
- follow-through: the same readable footprint starts to contract,
- dissipate: the sweep shrinks and feathers,
- release: the remaining energy thins quickly,
- clear: transparent.

``side`` is the broad forward/back swoop, ``up`` and ``down`` are the same
attack language above or below the body, and ``poke`` is the intentionally odd
grounded down-tilt thrust.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFilter

from ...authoring.sheet_build import build_sheet
from ambition_sprite2d_renderer.core.draw import blending_draw

TARGET_NAME = "robot_slash"
SHEET_FILES = (
    f"{TARGET_NAME}_spritesheet.png",
    f"{TARGET_NAME}_spritesheet.yaml",
    f"{TARGET_NAME}_spritesheet.ron",
    f"{TARGET_NAME}_actor.ron",
)

FRAME_SIZE = (160, 160)
SUPER = 4
ROWS: List[Tuple[str, int, int]] = [
    ("side", 5, 24),
    ("up", 5, 24),
    ("down", 5, 24),
    ("poke", 5, 24),
]

CORE = (255, 255, 255, 255)
HOT = (226, 247, 255, 255)
BODY = (174, 226, 255, 255)
EDGE = (76, 163, 239, 255)
DEEP = (29, 83, 177, 255)


def _px(value: float) -> float:
    return value * SUPER


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _smoothstep(edge0: float, edge1: float, value: float) -> float:
    if edge0 == edge1:
        return 1.0 if value >= edge1 else 0.0
    t = _clamp((value - edge0) / (edge1 - edge0))
    return t * t * (3.0 - 2.0 * t)


def _phase(t: float) -> str:
    if t < 0.18:
        return "impact"
    if t < 0.44:
        return "follow_through"
    if t < 0.72:
        return "dissipate"
    if t < 0.95:
        return "release"
    return "clear"


def _amplitude(t: float) -> float:
    if t <= 0.56:
        return _lerp(1.0, 0.82, _smoothstep(0.0, 0.56, t))
    return 0.82 * (1.0 - _smoothstep(0.62, 1.0, t))


def _cubic_point(
    p0: Tuple[float, float],
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    p3: Tuple[float, float],
    t: float,
) -> Tuple[float, float]:
    omt = 1.0 - t
    return (
        omt ** 3 * p0[0]
        + 3.0 * omt * omt * t * p1[0]
        + 3.0 * omt * t * t * p2[0]
        + t ** 3 * p3[0],
        omt ** 3 * p0[1]
        + 3.0 * omt * omt * t * p1[1]
        + 3.0 * omt * t * t * p2[1]
        + t ** 3 * p3[1],
    )


def _cubic_tangent(
    p0: Tuple[float, float],
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    p3: Tuple[float, float],
    t: float,
) -> Tuple[float, float]:
    omt = 1.0 - t
    dx = (
        3.0 * omt * omt * (p1[0] - p0[0])
        + 6.0 * omt * t * (p2[0] - p1[0])
        + 3.0 * t * t * (p3[0] - p2[0])
    )
    dy = (
        3.0 * omt * omt * (p1[1] - p0[1])
        + 6.0 * omt * t * (p2[1] - p1[1])
        + 3.0 * t * t * (p3[1] - p2[1])
    )
    length = math.hypot(dx, dy) or 1.0
    return dx / length, dy / length


def _width_profile(u: float, max_width: float) -> float:
    """Thin at the ends, broad and bowl-shaped through the center volume."""
    bowl = math.sin(math.pi * _clamp(u)) ** 0.34
    center_bias = 0.88 + 0.46 * math.sin(math.pi * _clamp(u)) ** 2
    return max_width * bowl * center_bias


def _sweep_polygon(
    progress: float,
    max_width: float,
    *,
    y_shift: float = 0.0,
    width_scale: float = 1.0,
    samples: int = 56,
) -> List[Tuple[float, float]]:
    """A body-to-tip swoop with an exaggerated U-shaped belly.

    The attack should feel like a forward swhoop in front of the robot rather
    than a diagonal crescent pasted above it. The centerline therefore dips
    much deeper through the lower middle of the frame before curling back up
    toward the leading tip.
    """
    p0 = (12.0, 82.0 + y_shift)
    p1 = (26.0, 148.0 + y_shift)
    p2 = (112.0, 152.0 + y_shift)
    p3 = (154.0, 58.0 + y_shift)
    end = _clamp(progress, 0.06, 1.0)
    outer: List[Tuple[float, float]] = []
    inner: List[Tuple[float, float]] = []
    for index in range(samples + 1):
        u = end * index / samples
        x, y = _cubic_point(p0, p1, p2, p3, u)
        tx, ty = _cubic_tangent(p0, p1, p2, p3, u)
        nx, ny = -ty, tx
        local_u = index / samples
        width = _width_profile(local_u, max_width * width_scale)
        outer.append((x + nx * width * 0.52, y + ny * width * 0.52))
        inner.append((x - nx * width * 0.48, y - ny * width * 0.48))
    return outer + list(reversed(inner))


def _scaled(points: Sequence[Tuple[float, float]]) -> List[Tuple[float, float]]:
    return [(_px(x), _px(y)) for x, y in points]


def _rotate_point_ccw(point: Tuple[float, float], center: Tuple[float, float] = (80.0, 80.0)) -> Tuple[float, float]:
    x, y = point
    cx, cy = center
    dx = x - cx
    dy = y - cy
    return (cx - dy, cy + dx)


def _rotate_frame_ccw(image: Image.Image) -> Image.Image:
    return image.rotate(90, resample=Image.Resampling.BICUBIC, center=(80, 80))


def _arc_state(t: float) -> dict:
    shrink = _smoothstep(0.0, 0.82, t)
    release = _smoothstep(0.62, 1.0, t)
    return {
        "progress": _lerp(1.0, 0.58, shrink),
        "width": _lerp(60.0, 16.0, shrink) * _lerp(1.0, 0.74, release),
        "amp": _amplitude(t),
        "release": release,
    }


def _draw_sweep_frame(t: float) -> Image.Image:
    state = _arc_state(t)
    amp = state["amp"]
    canvas = Image.new(
        "RGBA",
        (FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER),
        (0, 0, 0, 0),
    )
    if amp <= 0.01:
        return canvas.resize(FRAME_SIZE, Image.Resampling.LANCZOS)

    progress = state["progress"]
    width = state["width"]
    release = state["release"]

    # Broad blurred envelope first. It is intentionally substantial, but the
    # opaque white body still defines the player-readable damage region.
    halo = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    halo_draw = blending_draw(halo)
    halo_draw.polygon(
        _scaled(_sweep_polygon(progress, width, width_scale=1.34)),
        fill=(EDGE[0], EDGE[1], EDGE[2], int(128 * amp)),
    )
    halo_draw.polygon(
        _scaled(_sweep_polygon(progress * 0.93, width, y_shift=5.0, width_scale=0.96)),
        fill=(BODY[0], BODY[1], BODY[2], int(92 * amp * (1.0 - 0.35 * release))),
    )
    halo = halo.filter(ImageFilter.GaussianBlur(radius=int(3.4 * SUPER)))
    canvas.alpha_composite(halo)

    draw = blending_draw(canvas)
    draw.polygon(
        _scaled(_sweep_polygon(progress, width, width_scale=1.08)),
        fill=(DEEP[0], DEEP[1], DEEP[2], int(220 * amp)),
    )
    draw.polygon(
        _scaled(_sweep_polygon(progress, width, y_shift=-1.0, width_scale=0.84)),
        fill=(BODY[0], BODY[1], BODY[2], int(238 * amp)),
    )
    draw.polygon(
        _scaled(_sweep_polygon(progress, width, y_shift=-3.0, width_scale=0.58)),
        fill=(HOT[0], HOT[1], HOT[2], int(250 * amp)),
    )
    draw.polygon(
        _scaled(_sweep_polygon(progress, width, y_shift=-5.0, width_scale=0.31)),
        fill=(CORE[0], CORE[1], CORE[2], int(255 * amp)),
    )

    # Feathered trailing streaks remain inside the same broad sweep footprint.
    if progress > 0.55:
        for y_shift, width_scale, alpha in ((8.0, 0.22, 122), (13.0, 0.12, 78)):
            draw.polygon(
                _scaled(
                    _sweep_polygon(
                        progress * _lerp(0.78, 0.94, release),
                        width,
                        y_shift=y_shift,
                        width_scale=width_scale,
                    )
                ),
                fill=(HOT[0], HOT[1], HOT[2], int(alpha * amp)),
            )

    if release > 0.05:
        for x, y, radius, alpha in (
            (42.0, 122.0, 1.7, 124),
            (74.0, 130.0, 1.25, 102),
            (116.0, 114.0, 1.0, 82),
        ):
            drift = release * 8.0
            draw.ellipse(
                (
                    _px(x - radius),
                    _px(y + drift - radius),
                    _px(x + radius),
                    _px(y + drift + radius),
                ),
                fill=(HOT[0], HOT[1], HOT[2], int(alpha * amp)),
            )

    return canvas.resize(FRAME_SIZE, Image.Resampling.LANCZOS)


def _draw_up_frame_raw(t: float) -> Image.Image:
    side = _draw_sweep_frame(t)
    return side.rotate(90, resample=Image.Resampling.BICUBIC, center=(80, 80))


def _draw_down_frame_raw(t: float) -> Image.Image:
    side = _draw_sweep_frame(t)
    return side.rotate(-90, resample=Image.Resampling.BICUBIC, center=(80, 80))


def _poke_polygon(progress: float, max_width: float, width_scale: float = 1.0):
    x0 = 5.0
    x1 = _lerp(70.0, 155.0, _clamp(progress))
    cy = 82.0
    width = max_width * width_scale
    return [
        (x0, cy - width * 0.22),
        (x0 + (x1 - x0) * 0.32, cy - width * 0.50),
        (x1 - width * 0.34, cy - width * 0.22),
        (x1, cy),
        (x1 - width * 0.34, cy + width * 0.22),
        (x0 + (x1 - x0) * 0.32, cy + width * 0.50),
        (x0, cy + width * 0.22),
    ]


def _draw_poke_frame_raw(t: float) -> Image.Image:
    shrink = _smoothstep(0.0, 0.82, t)
    release = _smoothstep(0.62, 1.0, t)
    progress = _lerp(1.0, 0.44, shrink)
    width = _lerp(50.0, 13.0, shrink) * _lerp(1.0, 0.76, release)
    amp = _amplitude(t)

    canvas = Image.new(
        "RGBA",
        (FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER),
        (0, 0, 0, 0),
    )
    if amp <= 0.01:
        return canvas.resize(FRAME_SIZE, Image.Resampling.LANCZOS)

    halo = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    halo_draw = blending_draw(halo)
    halo_draw.polygon(
        _scaled(_poke_polygon(progress, width, 1.28)),
        fill=(EDGE[0], EDGE[1], EDGE[2], int(128 * amp)),
    )
    halo = halo.filter(ImageFilter.GaussianBlur(radius=int(3.0 * SUPER)))
    canvas.alpha_composite(halo)

    draw = blending_draw(canvas)
    for width_scale, color, alpha in (
        (1.00, DEEP, 220),
        (0.78, BODY, 238),
        (0.50, HOT, 250),
        (0.20, CORE, 255),
    ):
        draw.polygon(
            _scaled(_poke_polygon(progress, width, width_scale)),
            fill=(color[0], color[1], color[2], int(alpha * amp)),
        )

    return canvas.resize(FRAME_SIZE, Image.Resampling.LANCZOS)


def _draw_frame(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
    t = frame_idx / max(1, frame_count - 1)
    if animation == "up":
        image = _draw_up_frame_raw(t)
    elif animation == "down":
        image = _draw_down_frame_raw(t)
    elif animation == "poke":
        image = _draw_poke_frame_raw(t)
    else:
        image = _draw_sweep_frame(t)
    return _rotate_frame_ccw(image)


def _frame_meta(animation: str, frame_idx: int, frame_count: int) -> dict:
    t = frame_idx / max(1, frame_count - 1)
    anchors = {
        "side": ((12.0, 82.0), (154.0, 58.0)),
        "up": ((64.0, 152.0), (97.0, 7.0)),
        "down": ((96.0, 8.0), (63.0, 153.0)),
        "poke": ((5.0, 82.0), (155.0, 82.0)),
    }
    origin, tip = anchors[animation]
    origin = _rotate_point_ccw(origin)
    tip = _rotate_point_ccw(tip)
    return {
        "anchors": {
            "origin": {"x": origin[0], "y": origin[1]},
            "tip": {"x": tip[0], "y": tip[1]},
        },
        "effect": {
            "kind": animation,
            "progress": round(t, 4),
            "phase": _phase(t),
            "intensity": round(_amplitude(t), 4),
        },
    }


ACTOR_METADATA = {
    "actor": {"character_id": "fx_robot_slash", "display_name": "Robot Slash"},
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
        "action.melee.down_tilt": {"animation": "poke", "events": []},
    },
    "sockets": {
        "origin": {
            "source": f"{TARGET_NAME}.geometry",
            "point": {"x": 78.0, "y": 12.0},
        },
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
