"""Helpers for drawing the solo procedural characters as rigs (``shape_rig``).

These painters were written to draw every shape straight into the frame and
then turn, squash or fade WHOLE LAYERS (``Image.rotate`` of a body layer, a
resize of a crop). A part flipbook can follow a layer composited at an offset,
but not one turned or scaled as a picture: each such frame is a new raster.

Drawn through this module instead, a rigid group (a torso, a head, a hat) is
painted ONCE at its rest place on a full-frame canvas (``rest_piece``: the old
paint code runs unchanged, then the raster is cut to what it covers), and the
layer transform is applied to where the piece lands and how far it turns
(``Xform``). Limbs are two bones of a fixed length (``two_bone``) drawn as
turned capsules.

Angles: ``Xform`` takes the painters' own ``Image.rotate`` angles
(counter-clockwise positive) and reports ``deg`` in ``shape_rig``'s
convention (clockwise positive, +y down).
"""

from __future__ import annotations

import math
from typing import Callable, Dict, Hashable, Optional, Tuple

from PIL import Image

from ...authoring import rigdoc, shape_rig
from ...core.draw import blending_draw

Point = Tuple[float, float]
Color = Tuple[int, int, int, int]

_REST: Dict[Hashable, Tuple[Image.Image, Point]] = {}


def rest_piece(key: Hashable, size: Tuple[int, int], pivot: Point, paint: Callable) -> Tuple[Image.Image, Point]:
    """``paint(draw)`` on a transparent ``size`` canvas (the painter's own frame,
    the group at its rest place), cut to what it covers; the pivot moves with
    the cut. Cached under ``key``, which must name everything ``paint`` reads."""
    cached = _REST.get(key)
    if cached is None:
        image = Image.new("RGBA", (int(size[0]), int(size[1])), (0, 0, 0, 0))
        paint(blending_draw(image))
        box = image.getchannel("A").getbbox() or (0, 0, 1, 1)
        cached = (image.crop(box), (float(pivot[0]) - box[0], float(pivot[1]) - box[1]))
        _REST[key] = cached
    return cached


def place(canvas: Image.Image, part: Tuple[Image.Image, Point], at: Point, degrees: float, name: str, opacity: float = 1.0) -> None:
    """``shape_rig.place`` with an opacity (the part's alpha scaled)."""
    image, pivot = part
    if opacity >= 0.999:
        shape_rig.place(canvas, part, at, degrees, name)
    elif opacity > 0.004:
        rigdoc.blit_rotated(canvas, image, pivot, at, degrees, float(opacity), part_name=name)


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
    opacity: float = 1.0,
) -> None:
    """``shape_rig.capsule`` with an opacity."""
    if opacity >= 0.999:
        shape_rig.capsule(canvas, a, b, radius, fill, outline, outline_w, name, length=length)
        return
    from ...authoring.common_draw import draw_capsule

    span = math.hypot(b[0] - a[0], b[1] - a[1]) if length is None else length
    span = round(span * 4) / 4
    pad = radius + outline_w + 2
    key = ("capsule", span, round(radius, 3), fill, outline, round(outline_w, 3))
    part = shape_rig.piece(
        key,
        (span + 2 * pad, 2 * pad),
        (pad, pad),
        lambda draw: draw_capsule(draw, (pad, pad), (pad + span, pad), radius, fill, outline, outline_w),
    )
    place(canvas, part, a, math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])), name, opacity)


class Xform:
    """An affine map of canvas points (a layer's turn, squash and shift) and
    the degrees (clockwise) a piece riding it turns."""

    __slots__ = ("m", "deg")

    def __init__(self, m=(1.0, 0.0, 0.0, 0.0, 1.0, 0.0), deg: float = 0.0) -> None:
        self.m = m
        self.deg = deg

    def pt(self, p: Point) -> Point:
        a, b, c, d, e, f = self.m
        return (a * p[0] + b * p[1] + c, d * p[0] + e * p[1] + f)

    def vec(self, v: Point) -> Point:
        a, b, _c, d, e, _f = self.m
        return (a * v[0] + b * v[1], d * v[0] + e * v[1])

    def _then(self, n, deg: float = 0.0) -> "Xform":
        a, b, c, d, e, f = self.m
        A, B, C, D, E, F = n
        return Xform((A * a + B * d, A * b + B * e, A * c + B * f + C, D * a + E * d, D * b + E * e, D * c + E * f + F), self.deg + deg)

    def translate(self, dx: float, dy: float) -> "Xform":
        return self._then((1.0, 0.0, dx, 0.0, 1.0, dy))

    def rotate_ccw(self, center: Point, degrees: float) -> "Xform":
        """Then turned as ``Image.rotate(degrees, center=center)`` turns a layer."""
        if abs(degrees) < 1e-9:
            return self
        r = math.radians(degrees)
        c, s = math.cos(r), math.sin(r)
        cx, cy = center
        # Counter-clockwise on screen (+y down): x' = c*x + s*y, y' = -s*x + c*y.
        return self._then((c, s, cx - c * cx - s * cy, -s, c, cy + s * cx - c * cy), -degrees)

    def rotate_cw(self, center: Point, degrees: float) -> "Xform":
        return self.rotate_ccw(center, -degrees)

    def affine(self, kx: float, ox: float, x0: float, ky: float, oy: float, y0: float) -> "Xform":
        """Then ``x' = ox + (x - x0) * kx``, ``y' = oy + (y - y0) * ky`` (a
        layer's crop resized and pasted: the pieces move, they do not stretch)."""
        return self._then((kx, 0.0, ox - x0 * kx, 0.0, ky, oy - y0 * ky))


IDENTITY = Xform()


def two_bone(root: Point, target: Point, length: float, bend: Point, stretch_q: float = 3.0) -> Tuple[Point, float]:
    """The joint of a two-bone limb from ``root`` reaching ``target`` with both
    bones ``length`` long, bent toward ``bend``. Out of reach, both bones
    lengthen to the next ``stretch_q`` step (a stretched limb: a few lengths).
    Returns ``(joint, bone_length)``."""
    dx, dy = target[0] - root[0], target[1] - root[1]
    d = math.hypot(dx, dy)
    seg = length
    if d >= 2.0 * length:
        seg = math.ceil((d / 2.0 + 0.01) / stretch_q) * stretch_q
    if d < 1e-6:
        return (root[0] + bend[0] * seg, root[1] + bend[1] * seg), seg
    ux, uy = dx / d, dy / d
    h = math.sqrt(max(0.0, seg * seg - (d / 2.0) ** 2))
    px, py = -uy, ux
    if px * bend[0] + py * bend[1] < 0:
        px, py = -px, -py
    return (root[0] + ux * d / 2.0 + px * h, root[1] + uy * d / 2.0 + py * h), seg


def limb(
    canvas: Image.Image,
    root: Point,
    target: Point,
    length: float,
    bend: Point,
    radius: float,
    fill: Color,
    outline: Color,
    outline_w: float,
    name: str,
    *,
    seamless: bool = True,
    stretch_q: float = 3.0,
    opacity: float = 1.0,
) -> Point:
    """A two-bone limb of fixed bone ``length`` from ``root`` to ``target``,
    drawn as turned capsules. ``seamless`` draws both outlines, then both
    fills (no outline ring at the joint: the polyline look, four draws);
    otherwise each bone is one outlined capsule (two draws). Returns the joint."""
    joint, seg = two_bone(root, target, length, bend, stretch_q)
    if seamless:
        R = radius + outline_w
        capsule(canvas, root, joint, R, outline, outline, 0.0, f"{name}_upper_line", length=seg, opacity=opacity)
        capsule(canvas, joint, target, R, outline, outline, 0.0, f"{name}_lower_line", length=seg, opacity=opacity)
        capsule(canvas, root, joint, radius, fill, fill, 0.0, f"{name}_upper", length=seg, opacity=opacity)
        capsule(canvas, joint, target, radius, fill, fill, 0.0, f"{name}_lower", length=seg, opacity=opacity)
    else:
        capsule(canvas, root, joint, radius, fill, outline, outline_w, f"{name}_upper", length=seg, opacity=opacity)
        capsule(canvas, joint, target, radius, fill, outline, outline_w, f"{name}_lower", length=seg, opacity=opacity)
    return joint


def bone(canvas: Image.Image, a: Point, b: Point, radius: float, fill: Color, outline: Color, outline_w: float, name: str, q: float = 3.0, opacity: float = 1.0) -> None:
    """One capsule from ``a`` to ``b`` whose length is rounded to ``q`` pixels
    (a bone that stretches, in a few lengths)."""
    span = math.hypot(b[0] - a[0], b[1] - a[1])
    capsule(canvas, a, b, radius, fill, outline, outline_w, name, length=max(q, round(span / q) * q), opacity=opacity)


def q(value: float, step: float) -> float:
    """``value`` to the nearest ``step`` (a piece's look keyed by a pose value)."""
    return round(round(value / step) * step, 6)


def clean_capsule(
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
    opacity: float = 1.0,
) -> None:
    """A capsule whose outline (line and end discs) is painted before its fill
    (line and end discs), so no outline arc crosses the bone at its ends — the
    order most of these painters' own ``_capsule`` helpers use (unlike
    ``common_draw.draw_capsule``). Painted once along +x, placed turned."""
    span = math.hypot(b[0] - a[0], b[1] - a[1]) if length is None else length
    span = round(span * 4) / 4
    pad = radius + outline_w + 2
    R = radius + outline_w

    def paint(draw) -> None:
        y = pad
        draw.line([(pad, y), (pad + span, y)], fill=outline, width=max(1, int(round(2 * R))))
        for x in (pad, pad + span):
            draw.ellipse((x - R, y - R, x + R, y + R), fill=outline)
        draw.line([(pad, y), (pad + span, y)], fill=fill, width=max(1, int(round(2 * radius))))
        for x in (pad, pad + span):
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=fill)

    key = ("clean_capsule", span, round(radius, 3), fill, outline, round(outline_w, 3))
    part = shape_rig.piece(key, (span + 2 * pad, 2 * pad), (pad, pad), paint)
    place(canvas, part, a, math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])), name, opacity)


def clean_bone(canvas: Image.Image, a: Point, b: Point, radius: float, fill: Color, outline: Color, outline_w: float, name: str, q: float = 3.0, opacity: float = 1.0) -> None:
    """``bone`` drawn as a ``clean_capsule``: the length rounded to ``q`` pixels."""
    span = math.hypot(b[0] - a[0], b[1] - a[1])
    clean_capsule(canvas, a, b, radius, fill, outline, outline_w, name, length=max(q, round(span / q) * q), opacity=opacity)


def tapered_segment(
    canvas: Image.Image,
    a: Point,
    b: Point,
    ra: float,
    rb: float,
    fill: Color,
    name: str,
    *,
    q: float = 4.0,
    opacity: float = 1.0,
    seam: Optional[Tuple[Color, float, float, float]] = None,
) -> None:
    """A filled tapered tube from ``a`` (radius ``ra``) to ``b`` (radius
    ``rb``) with round ends and no outline, its length rounded to ``q``
    pixels; painted once along +x, placed turned. ``seam`` = (colour, width,
    side offset at ``a``, side offset at ``b``) adds a line along the tube's
    -normal side (a sleeve seam). Two of these per limb outline-colour first,
    then two fill-colour, draw one continuous bent tube (``tube2``)."""
    span = math.hypot(b[0] - a[0], b[1] - a[1])
    span = max(q, round(span / q) * q)
    r = max(ra, rb)
    pad = r + 3.0
    key = ("tapered_segment", span, round(ra, 2), round(rb, 2), fill, seam)

    def paint(draw) -> None:
        y = pad
        x0, x1 = pad, pad + span
        draw.polygon([(x0, y - ra), (x1, y - rb), (x1, y + rb), (x0, y + ra)], fill=fill)
        draw.ellipse((x0 - ra, y - ra, x0 + ra, y + ra), fill=fill)
        draw.ellipse((x1 - rb, y - rb, x1 + rb, y + rb), fill=fill)
        if seam is not None:
            colour, width, off_a, off_b = seam
            # -normal of +x (normal is (-dy, dx) = (0, 1)) is up.
            draw.line([(x0, y - off_a), (x1, y - off_b)], fill=colour, width=max(1, int(round(width))))

    part = shape_rig.piece(key, (span + 2 * pad, 2 * pad), (pad, pad), paint)
    place(canvas, part, a, math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])), name, opacity)


def tube2(
    canvas: Image.Image,
    a: Point,
    b: Point,
    c: Point,
    radii: Tuple[float, float, float],
    fill: Color,
    outline: Color,
    outline_w: float,
    name: str,
    *,
    q: float = 4.0,
    opacity: float = 1.0,
    seams: Optional[Tuple[Tuple[Color, float, float, float], Tuple[Color, float, float, float]]] = None,
) -> None:
    """A bent two-segment tube through the joints ``a``, ``b``, ``c`` (radii at
    each) with an outline ``outline_w`` wide centred on its edge, as four
    turned pieces: both segments outline-coloured, then both filled (a round
    joint, no outline across it). Lengths are rounded to ``q`` pixels."""
    r0, r1, r2 = radii
    h = outline_w / 2.0
    tapered_segment(canvas, a, b, r0 + h, r1 + h, outline, f"{name}_upper_line", q=q, opacity=opacity)
    tapered_segment(canvas, b, c, r1 + h, r2 + h, outline, f"{name}_lower_line", q=q, opacity=opacity)
    s0, s1 = seams if seams is not None else (None, None)
    tapered_segment(canvas, a, b, r0 - h, r1 - h, fill, f"{name}_upper", q=q, opacity=opacity, seam=s0)
    tapered_segment(canvas, b, c, r1 - h, r2 - h, fill, f"{name}_lower", q=q, opacity=opacity, seam=s1)


def local_piece(key: Hashable, extent: Tuple[float, float, float, float], paint: Callable, scale: float) -> Tuple[Image.Image, Point]:
    """A piece painted in its own frame in a painter's design units:
    ``paint(draw, origin)`` draws with the pivot at ``origin`` (design units)
    on a canvas covering ``extent`` = (left, top, right, bottom) around the
    pivot; ``scale`` design units to canvas pixels (the supersample). Cached
    under ``key`` (which must name everything ``paint`` reads)."""
    left, top, right, bottom = extent
    origin = (left + 2.0, top + 2.0)
    size = (int(math.ceil((left + right + 4.0) * scale)), int(math.ceil((top + bottom + 4.0) * scale)))
    return rest_piece(key, size, (origin[0] * scale, origin[1] * scale), lambda d: paint(d, origin))


def quad_segment(
    canvas: Image.Image,
    a: Point,
    b: Point,
    ra: float,
    rb: float,
    fill: Color,
    outline: Optional[Color],
    outline_w: float,
    name: str,
    *,
    q: float = 4.0,
    opacity: float = 1.0,
) -> None:
    """An outlined trapezoid from ``a`` (half-width ``ra``) to ``b`` (``rb``)
    with square ends — a painter's ``_segment_quad`` polygon with its closed
    outline (``joint="curve"``) — its length rounded to ``q`` pixels; painted
    once along +x, placed turned."""
    span = math.hypot(b[0] - a[0], b[1] - a[1])
    span = max(q, round(span / q) * q)
    pad = max(ra, rb) + outline_w + 2.0
    key = ("quad_segment", span, round(ra, 2), round(rb, 2), fill, outline, round(outline_w, 2))

    def paint(draw) -> None:
        y = pad
        pts = [(int(round(pad)), int(round(y + ra))), (int(round(pad + span)), int(round(y + rb))), (int(round(pad + span)), int(round(y - rb))), (int(round(pad)), int(round(y - ra)))]
        draw.polygon(pts, fill=fill)
        if outline is not None and outline_w > 0:
            draw.line(pts + [pts[0]], fill=outline, width=max(1, int(round(outline_w))), joint="curve")

    part = shape_rig.piece(key, (span + 2 * pad, 2 * pad), (pad, pad), paint)
    place(canvas, part, a, math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])), name, opacity)
