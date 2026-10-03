from __future__ import annotations

import math
from typing import Iterable, Tuple

from PIL import Image, ImageDraw

Point = Tuple[float, float]
Color = Tuple[int, int, int, int]

try:
    RESAMPLING = Image.Resampling
except AttributeError:  # pragma: no cover
    RESAMPLING = Image


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
    """A rounded rectangle turned ``angle`` degrees (counter-clockwise, as
    ``Image.rotate``) about ``center``: painted once unturned (cached by what it
    looks like) and placed by ``rigdoc.blit_rotated``, so a part flipbook stores
    it once and turns it (``shape_rig``)."""
    from . import shape_rig

    w, h = (
        max(2, int(math.ceil(size[0] + outline_w * 4))),
        max(2, int(math.ceil(size[1] + outline_w * 4))),
    )
    pad = int(max(w, h) * 0.35 + abs(outline_w) + 4)
    box = (
        pad + outline_w,
        pad + outline_w,
        pad + outline_w + size[0],
        pad + outline_w + size[1],
    )

    def paint(d) -> None:
        if outline is not None and outline_w > 0:
            obox = (box[0] - outline_w, box[1] - outline_w, box[2] + outline_w, box[3] + outline_w)
            d.rounded_rectangle(obox, radius=radius + outline_w, fill=outline)
        d.rounded_rectangle(box, radius=radius, fill=fill)

    key = ("rounded_rect", round(size[0], 3), round(size[1], 3), round(radius, 3), fill, outline, round(outline_w, 3))
    size_px = (w + pad * 2, h + pad * 2)
    part = shape_rig.piece(key, size_px, (size_px[0] / 2, size_px[1] / 2), paint)
    shape_rig.place(base, part, center, -angle, name)


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
    """A ellipse turned ``angle`` degrees (counter-clockwise, as
    ``Image.rotate``) about ``center``: painted once unturned (cached by what it
    looks like) and placed by ``rigdoc.blit_rotated``, so a part flipbook stores
    it once and turns it (``shape_rig``)."""
    from . import shape_rig

    w, h = (
        max(2, int(math.ceil(size[0] + outline_w * 4))),
        max(2, int(math.ceil(size[1] + outline_w * 4))),
    )
    pad = int(max(w, h) * 0.35 + abs(outline_w) + 4)
    box = (
        pad + outline_w,
        pad + outline_w,
        pad + outline_w + size[0],
        pad + outline_w + size[1],
    )

    def paint(d) -> None:
        if outline is not None and outline_w > 0:
            obox = (box[0] - outline_w, box[1] - outline_w, box[2] + outline_w, box[3] + outline_w)
            d.ellipse(obox, fill=outline)
        d.ellipse(box, fill=fill)

    key = ("ellipse", round(size[0], 3), round(size[1], 3), fill, outline, round(outline_w, 3))
    size_px = (w + pad * 2, h + pad * 2)
    part = shape_rig.piece(key, size_px, (size_px[0] / 2, size_px[1] / 2), paint)
    shape_rig.place(base, part, center, -angle, name)

