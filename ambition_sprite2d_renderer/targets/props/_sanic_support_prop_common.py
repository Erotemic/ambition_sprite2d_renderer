"""Shared drawing helpers for Sanic support prop sheets.

Private module: discovery ignores ``targets/props/_*.py``.  The public targets
(``sanic_ring_prop`` and ``sanic_spring_red_prop``) stay additive while sharing
small geometry/color helpers.
"""

from __future__ import annotations

import math
from typing import Iterable, Tuple

from PIL import Image, ImageColor, ImageDraw, ImageFilter
from ambition_sprite2d_renderer.core.draw import blending_draw

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

SUPER = 4
FRAME_SIZE = (128, 128)
SHEET_FILES_SUFFIXES = (
    "_spritesheet.png",
    "_spritesheet.yaml",
    "_spritesheet.ron",
    "_actor.ron",
)


def rgba(value: str, alpha: int | None = None) -> RGBA:
    r, g, b = ImageColor.getrgb(value)
    return (r, g, b, 255 if alpha is None else max(0, min(255, int(alpha))))


def clamp01(v: float) -> float:
    return max(0.0, min(1.0, v))


def ease(t: float) -> float:
    t = clamp01(t)
    return t * t * (3.0 - 2.0 * t)


def pulse(frame_idx: int, nframes: int, phase: float = 0.0) -> float:
    return math.sin((frame_idx / max(1, nframes)) * math.tau + phase)


def alpha(color: RGBA, factor: float) -> RGBA:
    return (color[0], color[1], color[2], max(0, min(255, int(round(color[3] * factor)))))


def scaled_points(points: Iterable[Point]) -> list[Point]:
    return [(x * SUPER, y * SUPER) for x, y in points]


def bbox(cx: float, cy: float, w: float, h: float) -> tuple[float, float, float, float]:
    hw = w * 0.5
    hh = h * 0.5
    return ((cx - hw) * SUPER, (cy - hh) * SUPER, (cx + hw) * SUPER, (cy + hh) * SUPER)


def new_frame() -> Image.Image:
    return Image.new("RGBA", (FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER), (0, 0, 0, 0))


def downsample(img: Image.Image) -> Image.Image:
    return img.resize(FRAME_SIZE, Image.Resampling.LANCZOS)


def ellipse_outline(
    draw: ImageDraw.ImageDraw,
    cx: float,
    cy: float,
    w: float,
    h: float,
    *,
    color: RGBA,
    width: float,
) -> None:
    draw.ellipse(
        bbox(cx, cy, w, h),
        outline=color,
        width=max(1, int(round(width * SUPER))),
    )


def rounded_rect(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float, float, float],
    *,
    radius: float,
    fill: RGBA,
    outline: RGBA | None = None,
    width: float = 1.0,
) -> None:
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle(
        (x0 * SUPER, y0 * SUPER, x1 * SUPER, y1 * SUPER),
        radius=radius * SUPER,
        fill=fill,
        outline=outline,
        width=max(1, int(round(width * SUPER))),
    )


def line(
    draw: ImageDraw.ImageDraw,
    points: Iterable[Point],
    *,
    fill: RGBA,
    width: float = 1.0,
    joint: str = "curve",
) -> None:
    draw.line(
        scaled_points(points),
        fill=fill,
        width=max(1, int(round(width * SUPER))),
        joint=joint,
    )


def poly(draw: ImageDraw.ImageDraw, points: Iterable[Point], *, fill: RGBA, outline: RGBA | None = None) -> None:
    pts = scaled_points(points)
    draw.polygon(pts, fill=fill, outline=outline)


def glow_ellipse(
    img: Image.Image,
    cx: float,
    cy: float,
    w: float,
    h: float,
    *,
    color: RGBA,
    width: float,
    blur: float,
) -> None:
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = blending_draw(layer)
    ellipse_outline(d, cx, cy, w, h, color=color, width=width)
    layer = layer.filter(ImageFilter.GaussianBlur(radius=max(0.0, blur * SUPER)))
    img.alpha_composite(layer)


def star(draw: ImageDraw.ImageDraw, cx: float, cy: float, r: float, *, color: RGBA, width: float = 1.4) -> None:
    line(draw, [(cx, cy - r), (cx, cy + r)], fill=color, width=width)
    line(draw, [(cx - r, cy), (cx + r, cy)], fill=color, width=width)
    line(draw, [(cx - r * 0.55, cy - r * 0.55), (cx + r * 0.55, cy + r * 0.55)], fill=alpha(color, 0.62), width=max(1.0, width * 0.72))
    line(draw, [(cx - r * 0.55, cy + r * 0.55), (cx + r * 0.55, cy - r * 0.55)], fill=alpha(color, 0.62), width=max(1.0, width * 0.72))
