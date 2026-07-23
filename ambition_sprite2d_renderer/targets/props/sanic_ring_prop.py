"""Animated ring prop sheet for the surface-locomotion sandbox.

This is an additive prop-sheet target, separate from the loose entity PNG target
``sanic_support_entities``.  It emits a normal runtime spritesheet with an idle
spin and a collect pop/sparkle row so gameplay can wire the ring as an animated
prop without changing the sprite-generator registry.
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
    ellipse_outline,
    glow_ellipse,
    line,
    new_frame,
    pulse,
    rgba,
    star,
)
from ambition_sprite2d_renderer.core.draw import blending_draw

TARGET_NAME = "sanic_ring_prop"
SHEET_FILES = tuple(f"{TARGET_NAME}{suffix}" for suffix in SHEET_FILES_SUFFIXES)
ROWS: List[Tuple[str, int, int]] = [
    # A calmer spin: 8 frames * 150ms ~= 1.2s per revolution (the 72ms original
    # read as a frantic blur once wired as a live pickup).
    ("idle", 8, 150),
    ("collect", 7, 54),
]

GOLD_DARK = rgba("#5A3307")
GOLD_RIM = rgba("#A65F08")
GOLD = rgba("#F5B11E")
GOLD_HI = rgba("#FFE88A")
GOLD_HOT = rgba("#FFF9C9")
SPARK = rgba("#FFF3B5")

ACTOR_METADATA = {
    "actor": {"character_id": TARGET_NAME, "display_name": "Animated Ring Prop"},
    "body": {
        "body_plan": "Prop",
        "body_kind": "Collectible",
        "locomotion_hint": "Stationary",
        "traits": ["prop", "pickup", "ring", "surface_locomotion_demo"],
    },
    "brain": {"default_preset": "stand_still"},
    "actions": {"default_preset": "peaceful"},
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "pickup.collect": {"animation": "collect", "events": []},
    },
    "sockets": {
        "center": {"source": f"{TARGET_NAME}.geometry", "point": {"x": 64.0, "y": 58.0}},
        "pickup": {"source": f"{TARGET_NAME}.geometry", "point": {"x": 64.0, "y": 58.0}},
    },
    "tags": ["prop", "pickup", "ring", "animated"],
}


def _ring_geometry(anim: str, frame_idx: int, nframes: int) -> dict[str, float]:
    t = frame_idx / max(1, nframes)
    if anim == "collect":
        p = clamp01(frame_idx / max(1, nframes - 1))
        return {
            "t": p,
            "cx": 64.0,
            "cy": 58.0 - 18.0 * p,
            "w": 58.0 + 44.0 * p,
            "h": 72.0 + 20.0 * p,
            "alpha": 1.0 - p * 0.82,
            "spark": p,
            "phase": p * math.tau,
        }
    spin = math.cos(t * math.tau)
    # Do not collapse fully edge-on; the art should read as a ring every frame.
    w = 14.0 + 54.0 * abs(spin)
    return {
        "t": t,
        "cx": 64.0,
        "cy": 58.0 + 2.0 * math.sin(t * math.tau),
        "w": w,
        "h": 74.0,
        "alpha": 1.0,
        "spark": 0.0,
        "phase": t * math.tau,
    }


def _draw_ring_core(img: Image.Image, spec: dict[str, float]) -> None:
    d = blending_draw(img)
    a = spec["alpha"]
    cx = spec["cx"]
    cy = spec["cy"]
    w = spec["w"]
    h = spec["h"]
    phase = spec["phase"]

    # No baked drop shadow (rule: shadows break crop/anchor alignment).
    glow_ellipse(img, cx, cy, w + 7, h + 7, color=alpha(GOLD_HI, 0.32 * a), width=5.2, blur=1.6)

    # Layered ellipse outlines give a thick torus while keeping the center truly transparent.
    ellipse_outline(d, cx, cy, w + 8, h + 8, color=alpha(GOLD_DARK, a), width=7.2)
    ellipse_outline(d, cx, cy, w + 2, h + 2, color=alpha(GOLD, a), width=8.8)
    ellipse_outline(d, cx - w * 0.035, cy - h * 0.035, w - 9, h - 11, color=alpha(GOLD_HI, 0.95 * a), width=3.2)
    ellipse_outline(d, cx + w * 0.035, cy + h * 0.05, max(5.0, w - 18), max(10.0, h - 22), color=alpha(GOLD_RIM, 0.78 * a), width=3.0)

    # Moving gleam locked to spin phase.
    gleam_x = cx + math.cos(phase - 0.72) * w * 0.42
    gleam_y = cy + math.sin(phase - 0.72) * h * 0.42
    star(d, gleam_x, gleam_y, 5.0 + 1.4 * abs(math.sin(phase)), color=alpha(GOLD_HOT, a), width=1.6)

    if spec["spark"] > 0.0:
        p = spec["spark"]
        for i in range(6):
            ang = phase + i * math.tau / 6.0
            r0 = 16.0 + 35.0 * p
            sx = cx + math.cos(ang) * r0
            sy = cy + math.sin(ang) * r0 * 0.78
            star(d, sx, sy, 3.0 + 4.5 * (1.0 - p), color=alpha(SPARK, (1.0 - p) * 0.95), width=1.3)


def _draw_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    img = new_frame()
    _draw_ring_core(img, _ring_geometry(anim, frame_idx, nframes))
    return downsample(img)


def _frame_meta(anim: str, frame_idx: int, nframes: int) -> dict:
    spec = _ring_geometry(anim, frame_idx, nframes)
    return {
        "anchors": {
            "center": {"x": round(spec["cx"], 2), "y": round(spec["cy"], 2)},
            "pickup": {"x": round(spec["cx"], 2), "y": round(spec["cy"], 2)},
        },
        "prop": {"kind": "ring", "state": anim, "progress": round(spec["t"], 4)},
    }


def _body_metrics(fw: int, fh: int) -> dict:
    # Pickup trigger art should not grow gameplay collision as the collect row expands.
    return {
        "body_pixel_bbox": {"x": int(fw * 0.25), "y": int(fh * 0.18), "w": int(fw * 0.50), "h": int(fh * 0.64)},
        "feet_pixel": {"x": fw / 2.0, "y": fh * 0.86},
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
