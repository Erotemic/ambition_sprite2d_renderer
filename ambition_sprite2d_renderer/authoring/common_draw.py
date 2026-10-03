from __future__ import annotations

import math
from typing import Iterable, Tuple

from PIL import Image, ImageDraw
from ambition_sprite2d_renderer.core.draw import blending_draw

Point = Tuple[float, float]
Color = Tuple[int, int, int, int]

try:
    RESAMPLING = Image.Resampling
except AttributeError:  # pragma: no cover
    RESAMPLING = Image


def _composite_turned(base: Image.Image, layer: Image.Image, center: Point, name: str) -> None:
    """Composite a turned layer onto ``base`` with its centre at ``center``.

    It goes through rigdoc's seam, so a part flipbook records the layer as one
    part, on the track ``name``. One frame must not use one name two times.
    The pixels are the same as ``base.alpha_composite``."""
    from . import rigdoc  # rigdoc imports this module

    rigdoc.composite_layer(
        base, layer, (int(center[0] - layer.size[0] / 2), int(center[1] - layer.size[1] / 2)), name=name
    )


def draw_capsule(
    draw: ImageDraw.ImageDraw,
    a: Point,
    b: Point,
    radius: float,
    fill: Color,
    outline: Color,
    outline_w: float = 1.0,
) -> None:
    width_o = max(1, int(round(radius * 2.0 + outline_w * 2.0)))
    width_i = max(1, int(round(radius * 2.0)))
    draw.line([a, b], fill=outline, width=width_o)
    draw.line([a, b], fill=fill, width=width_i)
    for c in (a, b):
        x, y = c
        draw.ellipse(
            (
                x - radius - outline_w,
                y - radius - outline_w,
                x + radius + outline_w,
                y + radius + outline_w,
            ),
            fill=outline,
        )
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=fill)


def draw_rotated_rounded_rect(
    base: Image.Image,
    center: Point,
    size: Point,
    angle: float,
    radius: float,
    fill: Color,
    outline: Color | None = None,
    outline_w: float = 0.0,
    *,
    name: str = "rotated_rect",
) -> None:
    w, h = (
        max(2, int(math.ceil(size[0] + outline_w * 4))),
        max(2, int(math.ceil(size[1] + outline_w * 4))),
    )
    pad = int(max(w, h) * 0.35 + abs(outline_w) + 4)
    layer = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    d = blending_draw(layer)
    box = (
        pad + outline_w,
        pad + outline_w,
        pad + outline_w + size[0],
        pad + outline_w + size[1],
    )
    if outline is not None and outline_w > 0:
        obox = (
            box[0] - outline_w,
            box[1] - outline_w,
            box[2] + outline_w,
            box[3] + outline_w,
        )
        d.rounded_rectangle(obox, radius=radius + outline_w, fill=outline)
    d.rounded_rectangle(box, radius=radius, fill=fill)
    layer = layer.rotate(angle, resample=RESAMPLING.BICUBIC, expand=True)
    _composite_turned(base, layer, center, name)


def draw_rotated_ellipse(
    base: Image.Image,
    center: Point,
    size: Point,
    angle: float,
    fill: Color,
    outline: Color | None = None,
    outline_w: float = 0.0,
    *,
    name: str = "rotated_ellipse",
) -> None:
    w, h = (
        max(2, int(math.ceil(size[0] + outline_w * 4))),
        max(2, int(math.ceil(size[1] + outline_w * 4))),
    )
    pad = int(max(w, h) * 0.35 + abs(outline_w) + 4)
    layer = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    d = blending_draw(layer)
    box = (
        pad + outline_w,
        pad + outline_w,
        pad + outline_w + size[0],
        pad + outline_w + size[1],
    )
    if outline is not None and outline_w > 0:
        obox = (
            box[0] - outline_w,
            box[1] - outline_w,
            box[2] + outline_w,
            box[3] + outline_w,
        )
        d.ellipse(obox, fill=outline)
    d.ellipse(box, fill=fill)
    layer = layer.rotate(angle, resample=RESAMPLING.BICUBIC, expand=True)
    _composite_turned(base, layer, center, name)

