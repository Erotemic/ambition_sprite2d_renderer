"""Draw a procedural character as a rig: each piece once, in its own frame,
turned into place.

A procedural painter that draws its limbs straight into the frame (a capsule
between two joints, a polygon already turned) makes every pose a new picture,
so a part flipbook recorded from it stores a limb at every angle: the
goblins took 130-140 draws a frame and more texels than their own sheet
(`docs/planning/engine/mary-o-part-realization.md`, 2026-10-03). Drawn
through this module instead, a piece is painted ONCE in a local raster (cached
by what it looks like) and placed with ``rigdoc.blit_rotated``: the sheet is
composed from those pieces, and the recorder sees one part turned per frame —
what a rig document is.

Angles are degrees, clockwise positive (+y is down), as ``blit_rotated`` turns.
"""

from __future__ import annotations

import math
from typing import Callable, Dict, Hashable, Optional, Tuple

from PIL import Image

from ..core.draw import blending_draw

Point = Tuple[float, float]
Color = Tuple[int, int, int, int]

#: key -> (raster, pivot). A piece that looks the same is painted once a
#: process; the recorder dedupes it by its pixels anyway, this saves the paint.
_PIECES: Dict[Hashable, Tuple[Image.Image, Point]] = {}


def piece(key: Hashable, size: Tuple[float, float], pivot: Point, paint: Callable) -> Tuple[Image.Image, Point]:
    """The local raster ``paint(draw)`` paints on a transparent ``size`` canvas,
    with its ``pivot`` (local pixels), cached under ``key``. ``key`` must name
    everything ``paint`` reads."""
    cached = _PIECES.get(key)
    if cached is None:
        image = Image.new("RGBA", (max(1, int(math.ceil(size[0]))), max(1, int(math.ceil(size[1])))), (0, 0, 0, 0))
        paint(blending_draw(image))
        cached = (image, pivot)
        _PIECES[key] = cached
    return cached


def place(canvas: Image.Image, part: Tuple[Image.Image, Point], at: Point, degrees: float, name: str) -> None:
    """Composite ``part`` with its pivot at ``at``, turned ``degrees``, as the
    draw ``name`` (one name once a frame)."""
    from . import rigdoc  # rigdoc imports modules that import this one

    image, pivot = part
    rigdoc.blit_rotated(canvas, image, pivot, at, degrees, part_name=name)


def capsule(
    canvas: Image.Image,
    a: Point,
    b: Point,
    radius: float,
    fill: Color,
    outline: Color,
    outline_w: float,
    name: str,
    *,
    length: Optional[float] = None,
) -> None:
    """``common_draw.draw_capsule`` from ``a`` to ``b`` as a turned piece: the
    capsule is painted once along +x and placed by its first end. ``length``
    names the bone's length when it is fixed (a rig bone); otherwise the
    distance, rounded to a quarter pixel, keys the piece."""
    from .common_draw import draw_capsule

    span = math.hypot(b[0] - a[0], b[1] - a[1]) if length is None else length
    span = round(span * 4) / 4
    pad = radius + outline_w + 2
    key = ("capsule", span, round(radius, 3), fill, outline, round(outline_w, 3))
    part = piece(
        key,
        (span + 2 * pad, 2 * pad),
        (pad, pad),
        lambda draw: draw_capsule(draw, (pad, pad), (pad + span, pad), radius, fill, outline, outline_w),
    )
    place(canvas, part, a, math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])), name)
