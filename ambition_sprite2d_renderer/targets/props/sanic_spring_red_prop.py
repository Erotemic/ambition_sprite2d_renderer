"""Animated red spring prop sheet for the surface-locomotion sandbox.

Rows:
- ``idle``: readable armed spring with a tiny mechanical bounce.
- ``compress``: cap presses down and coils flatten.
- ``release``: cap snaps upward with motion streaks, then settles.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Tuple

from PIL import Image, ImageDraw

from ...authoring.sheet_build import build_sheet, write_canonical
from ._sanic_support_prop_common import (
    FRAME_SIZE,
    SHEET_FILES_SUFFIXES,
    alpha,
    clamp01,
    downsample,
    ease,
    line,
    new_frame,
    poly,
    pulse,
    rgba,
    rounded_rect,
    scaled_points,
    soft_shadow,
    star,
)
from ambition_sprite2d_renderer.core.draw import blending_draw

TARGET_NAME = "sanic_spring_red_prop"
SHEET_FILES = tuple(f"{TARGET_NAME}{suffix}" for suffix in SHEET_FILES_SUFFIXES)
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 4, 120),
    ("compress", 4, 52),
    ("release", 6, 48),
]

OUTLINE = rgba("#2A1712")
RED_DARK = rgba("#861A15")
RED = rgba("#D9362F")
RED_HOT = rgba("#FF766C")
METAL_DARK = rgba("#4B5663")
METAL = rgba("#AEB9C4")
METAL_HI = rgba("#EEF5FF")
SPARK = rgba("#FFF5B8")

ACTOR_METADATA = {
    "actor": {"character_id": TARGET_NAME, "display_name": "Animated Red Spring Prop"},
    "body": {
        "body_plan": "Prop",
        "body_kind": "ReboundSurface",
        "locomotion_hint": "Stationary",
        "traits": ["prop", "spring", "rebound", "surface_locomotion_demo"],
    },
    "brain": {"default_preset": "stand_still"},
    "actions": {"default_preset": "peaceful"},
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "spring.compress": {"animation": "compress", "events": []},
        "spring.release": {"animation": "release", "events": []},
    },
    "sockets": {
        "base": {"source": f"{TARGET_NAME}.geometry", "point": {"x": 64.0, "y": 104.0}},
        "launch_surface": {"source": f"{TARGET_NAME}.geometry", "point": {"x": 64.0, "y": 42.0}},
    },
    "tags": ["prop", "spring", "rebound", "animated"],
}


def _spring_state(anim: str, frame_idx: int, nframes: int) -> dict[str, float]:
    p = frame_idx / max(1, nframes - 1)
    if anim == "compress":
        c = ease(p)
        return {"t": p, "compression": c, "overshoot": 0.0, "spark": 0.0}
    if anim == "release":
        # Fast release overshoots upward then settles back near idle.
        c = max(0.0, 1.0 - p * 1.65)
        overshoot = max(0.0, math.sin(clamp01(p) * math.pi) * (1.0 - p) * 0.86)
        return {"t": p, "compression": c, "overshoot": overshoot, "spark": 1.0 - p}
    return {"t": p, "compression": 0.06 + 0.035 * pulse(frame_idx, nframes), "overshoot": 0.0, "spark": 0.0}


def _draw_bolt(d: ImageDraw.ImageDraw, cx: float, cy: float) -> None:
    d.ellipse((
        (cx - 3.5) * 4,
        (cy - 3.5) * 4,
        (cx + 3.5) * 4,
        (cy + 3.5) * 4,
    ), fill=METAL, outline=OUTLINE, width=4)
    d.ellipse(((cx - 2.0) * 4, (cy - 2.0) * 4, cx * 4, cy * 4), fill=METAL_HI)


def _draw_motion_lines(d: ImageDraw.ImageDraw, amount: float) -> None:
    if amount <= 0.05:
        return
    for x, h, phase in ((37, 18, 0.0), (91, 20, 0.6), (50, 12, 1.3), (78, 14, 2.0)):
        a = max(0.0, min(1.0, amount * (0.7 + 0.3 * math.sin(phase))))
        line(d, [(x, 53), (x, 53 + h)], fill=alpha(METAL_HI, 0.58 * a), width=1.8)


def _draw_spring(img: Image.Image, spec: dict[str, float]) -> None:
    d = blending_draw(img)
    c = clamp01(spec["compression"])
    overshoot = spec["overshoot"]
    spark = spec["spark"]

    # Geometry: base stays planted; the launch cap travels along the vertical axis.
    base_y = 99.0
    top_y = 38.0 + 31.0 * c - 16.0 * overshoot
    coil_top = top_y + 18.0
    coil_bottom = 87.0
    amp = 20.0 - 9.0 * c

    soft_shadow(d, 64, 111, 78, 12, strength=48)
    _draw_motion_lines(d, overshoot + spark * 0.45)

    # Base and lower cap.
    rounded_rect(d, (27, 91, 101, 108), radius=5, fill=RED_DARK, outline=OUTLINE, width=2)
    rounded_rect(d, (34, 84, 94, 99), radius=4, fill=RED, outline=OUTLINE, width=2)
    line(d, [(38, 88), (89, 88)], fill=RED_HOT, width=2.2)

    # Coil zig-zag adapts to compressed height.
    steps = 5
    pts: list[tuple[float, float]] = []
    for i in range(steps):
        y = coil_top + (coil_bottom - coil_top) * (i / max(1, steps - 1))
        x = 64.0 + ((-amp) if i % 2 == 0 else amp)
        pts.append((x, y))
    line(d, pts, fill=OUTLINE, width=8.2)
    line(d, pts, fill=METAL_DARK, width=5.6)
    hi_pts = [(x + (2.0 if i % 2 == 0 else -2.0), y - 1.0) for i, (x, y) in enumerate(pts)]
    line(d, hi_pts, fill=METAL_HI, width=2.0)

    # Top cap. A polygon lip makes it read as a launch pad rather than a box.
    poly(
        d,
        [(32, top_y + 11), (96, top_y + 11), (106, top_y + 22), (96, top_y + 33), (32, top_y + 33), (22, top_y + 22)],
        fill=RED,
        outline=OUTLINE,
    )
    rounded_rect(d, (34, top_y + 2, 94, top_y + 18), radius=6, fill=RED, outline=OUTLINE, width=2)
    line(d, [(42, top_y + 6), (86, top_y + 6)], fill=RED_HOT, width=3.0)
    line(d, [(31, top_y + 28), (97, top_y + 28)], fill=rgba("#70110F"), width=2.0)

    for bx, by in ((39, 94), (89, 94), (40, top_y + 15), (88, top_y + 15)):
        _draw_bolt(d, bx, by)

    if spark > 0.05:
        for i, (sx, sy) in enumerate(((30, 35), (98, 34), (24, 61), (104, 62))):
            star(d, sx, sy - 7.0 * overshoot, 3.0 + 4.0 * spark, color=alpha(SPARK, 0.75 * spark), width=1.25)


def _draw_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    img = new_frame()
    _draw_spring(img, _spring_state(anim, frame_idx, nframes))
    return downsample(img)


def _frame_meta(anim: str, frame_idx: int, nframes: int) -> dict:
    spec = _spring_state(anim, frame_idx, nframes)
    top_y = 38.0 + 31.0 * clamp01(spec["compression"]) - 16.0 * spec["overshoot"]
    return {
        "anchors": {
            "base": {"x": 64.0, "y": 104.0},
            "launch_surface": {"x": 64.0, "y": round(top_y + 7.0, 2)},
        },
        "prop": {"kind": "spring_red", "state": anim, "progress": round(spec["t"], 4)},
    }


def _body_metrics(fw: int, fh: int) -> dict:
    return {
        "body_pixel_bbox": {"x": int(fw * 0.17), "y": int(fh * 0.12), "w": int(fw * 0.66), "h": int(fh * 0.82)},
        "feet_pixel": {"x": fw / 2.0, "y": float(fh)},
        "feet_anchor_norm": {"x": 0.0, "y": -0.5},
    }


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=_draw_frame,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
        frame_meta_fn=_frame_meta,
        auto_crop=True,
        crop_margin=6,
        body_metrics_fn=_body_metrics,
        actor_metadata=ACTOR_METADATA,
        trim=False,
    )
    return [
        outputs["spritesheet"],
        outputs["yaml"],
        outputs["ron"],
        outputs["actor"],
        outputs["preview"],
        outputs["canonical"],
        outputs["canonical_transparent"],
    ]


def render_canonical(out_dir: str | Path, **opts) -> Path:
    del opts
    return write_canonical(
        TARGET_NAME,
        ROWS,
        _draw_frame,
        Path(out_dir),
        frame_size=FRAME_SIZE,
        crop_margin=6,
    )
