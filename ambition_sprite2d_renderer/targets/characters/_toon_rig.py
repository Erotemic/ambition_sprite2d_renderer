"""Helpers to draw the toon family of procedural characters as rigs
(``authoring.shape_rig``).

These painters drew each shape straight into the frame (a limb polygon
between two joints, a head with each point turned) and turned the whole
body layer as a picture (``Image.rotate``). A part flipbook stores each such
frame as new rasters. Drawn through this module, a rigid group (a head, a
torso, a hand) is a piece painted once in its own frame, and ``Frame`` turns
each place as the old layer turn did.

Angles are degrees, clockwise positive (+y is down), as ``shape_rig`` turns.
"""

from __future__ import annotations

import math
from typing import Callable, Hashable, Optional, Sequence, Tuple

from PIL import Image

from ...authoring import shape_rig
from ...core.draw import blending_draw

Point = Tuple[float, float]
Color = Tuple[int, int, int, int]


class Frame:
    """The canvas pieces are placed on, turned as one body ``degrees``
    about ``pivot`` (canvas pixels). This replaces an ``Image.rotate`` of
    the whole body layer: each place turns, not the picture."""

    def __init__(
        self,
        canvas: Image.Image,
        degrees: float = 0.0,
        pivot: Point = (0.0, 0.0),
        flash: Tuple[Tuple[int, int, int], float] = None,
    ) -> None:
        self.canvas = canvas
        self.degrees = float(degrees)
        self.pivot = pivot
        #: ``(color, strength)``: every piece placed is tinted (``tinted``).
        self.flash = flash if flash is not None and flash[1] > 0.0 else None
        radians = math.radians(self.degrees)
        self._cos = math.cos(radians)
        self._sin = math.sin(radians)

    def point(self, p: Point) -> Point:
        """``p`` (canvas pixels) moved by the body turn."""
        if self.degrees == 0.0:
            return p
        x = p[0] - self.pivot[0]
        y = p[1] - self.pivot[1]
        return (self.pivot[0] + x * self._cos - y * self._sin, self.pivot[1] + x * self._sin + y * self._cos)

    def place(self, part: Tuple[Image.Image, Point], at: Point, degrees: float, name: str) -> None:
        """``shape_rig.place`` of ``part`` with its pivot at ``at`` (canvas
        pixels, before the body turn), turned ``degrees`` plus the body turn."""
        if self.flash is not None:
            part = tinted(part, *self.flash)
        shape_rig.place(self.canvas, part, self.point(at), degrees + self.degrees, name)


def piece(key: Hashable, size: Tuple[float, float], pivot: Point, paint: Callable) -> Tuple[Image.Image, Point]:
    """``shape_rig.piece``."""
    return shape_rig.piece(key, size, pivot, paint)


_OVERLAYS: dict = {}


def overlay_piece(
    key: Hashable,
    size: Tuple[float, float],
    pivot: Point,
    paint: Callable,
    align: int = 8,
) -> Optional[Tuple[Image.Image, Point]]:
    """A piece painted in the frame of another piece (the same ``size`` and
    ``pivot``) and cut to the pixels it paints. Placed at the same point and
    turn as that piece, it lands on it; stored, it is only its own pixels.
    ``None`` when ``paint`` paints nothing.

    The cut starts on a multiple of ``align`` pixels, so a supersampled
    overlay reduces on the same pixel grid as the piece it lands on.
    ``key`` must name everything ``paint`` reads."""
    if key in _OVERLAYS:
        return _OVERLAYS[key]
    full = Image.new("RGBA", (max(1, int(math.ceil(size[0]))), max(1, int(math.ceil(size[1])))), (0, 0, 0, 0))
    paint(blending_draw(full))
    box = full.getchannel("A").getbbox()
    part = None
    if box is not None:
        x0 = box[0] - box[0] % align
        y0 = box[1] - box[1] % align
        part = (full.crop((x0, y0, box[2], box[3])), (pivot[0] - x0, pivot[1] - y0))
    _OVERLAYS[key] = part
    return part


def face(
    place: Callable[[Tuple[Image.Image, Point], str], None],
    name: str,
    size: Tuple[float, float],
    pivot: Point,
    base: Tuple[Hashable, Callable],
    features: Sequence[Tuple[str, Hashable, Callable]] = (),
) -> None:
    """A head as a BASE piece and EXPRESSION overlays that ride it.

    ``base`` is ``(key, paint)``: the head shape, skin and hair, which no
    expression changes. Each feature is ``(suffix, key, paint)``: the eyes,
    the brows, the mouth, painted in the base's frame (``overlay_piece``)
    and keyed by the expression state it reads. A character then stores one
    head and a few small features, not one head per expression, and the
    features recombine (open eyes with each mouth). ``place(part, name)``
    puts each piece at the head's point and turn, so the features turn with
    the head. A feature with key ``None`` is not drawn."""
    place(piece(base[0], size, pivot, base[1]), name)
    for suffix, key, paint in features:
        if key is None:
            continue
        part = overlay_piece(key, size, pivot, paint)
        if part is not None:
            place(part, f"{name}_{suffix}")


def angle(a: Point, b: Point) -> float:
    """The direction from ``a`` to ``b`` in degrees, clockwise positive."""
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


def quantize(value: float, step: float) -> float:
    """``value`` rounded to a multiple of ``step``: a pose value that keys a
    piece is rounded, so near poses share one piece."""
    return round(value / step) * step


def bbox(center: Point, rx: float, ry: float) -> Tuple[float, float, float, float]:
    return (center[0] - rx, center[1] - ry, center[0] + rx, center[1] + ry)


def paint_tube(
    draw,
    start: Point,
    length: float,
    r0: float,
    r1: float,
    fill: Color,
    outline: Color,
    width: float,
    *,
    start_cap: bool = True,
) -> None:
    """A tapered tube along +x from ``start`` (local pixels): rounded ends of
    radius ``r0`` and ``r1``, outlined on its silhouette only, so no ring
    shows inside it.

    ``start_cap`` False paints the start end filled but not outlined and a
    little smaller: the tube continues a limb at a joint, and the bone
    before it shows its own rounded end on the outside of the bend."""
    x0, y0 = start
    x1 = x0 + length
    w = max(1, round(width))
    if start_cap:
        draw.ellipse(bbox((x0, y0), r0, r0), fill=fill, outline=outline, width=w)
    else:
        inner = max(0.5, r0 - w)
        draw.ellipse(bbox((x0, y0), inner, inner), fill=fill)
    draw.ellipse(bbox((x1, y0), r1, r1), fill=fill, outline=outline, width=w)
    draw.polygon([(x0, y0 - r0), (x1, y0 - r1), (x1, y0 + r1), (x0, y0 + r0)], fill=fill)
    half = w / 2.0
    draw.line([(x0, y0 - r0 + half), (x1, y0 - r1 + half)], fill=outline, width=w)
    draw.line([(x0, y0 + r0 - half), (x1, y0 + r1 - half)], fill=outline, width=w)


def tube(
    frame: Frame,
    a: Point,
    b: Point,
    r0: float,
    r1: float,
    fill: Color,
    outline: Color,
    width: float,
    name: str,
    *,
    quantum: float,
    start_cap: bool = True,
    detail: Callable = None,
    detail_key: Hashable = None,
) -> None:
    """A tapered tube (``paint_tube``) from ``a`` toward ``b`` (canvas
    pixels) as one turned piece. Its length is ``|b - a|`` rounded to
    ``quantum`` pixels: a limb whose authored length changes per pose is a
    few pieces, and the joint's rounded end hides the rest.

    ``detail(draw, start, length)`` paints more on the tube in its own frame
    (a seam, a crease); ``detail_key`` names what it reads."""
    length = max(quantum, quantize(math.hypot(b[0] - a[0], b[1] - a[1]), quantum))
    pad = max(r0, r1) + width + 2
    start = (pad, pad)

    def paint(draw) -> None:
        paint_tube(draw, start, length, r0, r1, fill, outline, width, start_cap=start_cap)
        if detail is not None:
            detail(draw, start, length)

    key = ("toon_tube", length, round(r0, 3), round(r1, 3), fill, outline, round(width, 3), start_cap, detail_key)
    part = piece(key, (length + 2 * pad, 2 * pad), start, paint)
    frame.place(part, a, angle(a, b), name)


def anchored(
    frame: Frame,
    key: Hashable,
    half: Tuple[float, float],
    at: Point,
    paint: Callable,
    name: str,
    degrees: float = 0.0,
) -> None:
    """A piece painted by ``paint(draw, origin)`` with its anchor at
    ``origin`` on a ``2 * half`` canvas, placed with the anchor at ``at``
    (canvas pixels), turned ``degrees``. The old painters take the point
    they draw around; given the piece's own origin they paint it once.
    ``key`` must name everything ``paint`` reads."""
    hx, hy = float(math.ceil(half[0])), float(math.ceil(half[1]))
    origin = (hx, hy)
    part = piece(key, (2 * hx, 2 * hy), origin, lambda draw: paint(draw, origin))
    frame.place(part, at, degrees, name)


_TINTED: dict = {}


def tinted(part: Tuple[Image.Image, Point], color: Tuple[int, int, int], strength: float) -> Tuple[Image.Image, Point]:
    """``part`` with ``color`` composited over its own pixels at ``strength``
    of their alpha (a hit flash), cached per part and strength."""
    image, pivot = part
    strength = round(strength, 2)
    key = (id(image), color, strength)
    cached = _TINTED.get(key)
    if cached is None or cached[0] is not image:
        tint = Image.new("RGBA", image.size, (*color, 255))
        tint.putalpha(image.getchannel("A").point(lambda value: round(value * strength)))
        out = image.copy()
        out.alpha_composite(tint)
        cached = (image, (out, pivot))
        _TINTED[key] = cached
    return cached[1]


def _vdraw_length(v, value: float) -> float:
    """A design length in canvas pixels through ``v`` (``VDraw.d`` when the
    facade scales its design, else ``v.scale``)."""
    length = getattr(v, "d", None)
    return length(value) if length is not None else value * v.scale


def vpiece(v, key: Hashable, half: float, at: Point, paint: Callable, name: str, degrees: float = 0.0, origin: Point = None) -> None:
    """A piece for a painter that draws through a ``VDraw`` (``v.p`` maps a
    design point to canvas pixels): ``paint(local, origin)`` draws through a
    ``VDraw`` of the same kind on the piece's own canvas, around the design
    point ``origin``. Placed with ``origin`` at the design point ``at``,
    turned ``degrees``. ``key`` must name everything ``paint`` reads; the
    canvas reaches ``half`` design units around ``origin`` (by default
    ``(half, half)``)."""
    scale = v.scale
    origin = (float(half), float(half)) if origin is None else origin
    pivot = v.p(origin)
    reach = half * scale
    size = (pivot[0] + reach, pivot[1] + reach)
    part = piece((key, scale), size, pivot, lambda draw: paint(type(v)(draw._img, scale), origin))
    shape_rig.place(v.image, part, v.p(at), degrees, name)


def vtube(v, a: Point, b: Point, radius: float, stroke: float, fill: Color, outline: Color, name: str, *, quantum: float = 0.5, detail: Callable = None, detail_key: Hashable = None) -> None:
    """``VDraw.capsule`` (design coordinates) as a turned tube piece: the
    capsule of ``radius`` with an outline ``stroke`` wide around it.
    ``detail`` paints in canvas pixels (see ``tube``)."""
    r = _vdraw_length(v, radius + stroke)
    tube(
        Frame(v.image),
        v.p(a),
        v.p(b),
        r,
        r,
        fill,
        outline,
        _vdraw_length(v, stroke),
        name,
        quantum=_vdraw_length(v, quantum),
        detail=detail,
        detail_key=detail_key,
    )
