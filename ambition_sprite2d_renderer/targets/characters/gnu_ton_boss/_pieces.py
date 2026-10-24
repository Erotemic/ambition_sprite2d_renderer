"""Pieces of a drawing, each painted once and placed by a transform.

The giant is too large to bake a whole picture for each pose: its sheet held
every pose of every row, about 89 megapixels. It is drawn from PIECES instead.
A piece is SVG in its own coordinates (a bone drawn along +y from its root, a
face, the barrel of the beast). A frame is a list of PLACEMENTS: which piece,
and the rigid motion (and the stretch along one axis) that puts it in the
frame. `rasterize` paints a piece once (resvg) and caches it by its SVG text;
`compose` puts each placement on a canvas through `rigdoc.blit_rotated`, so
a part flipbook records each piece once and its place in each frame
(`authoring/part_flipbook.py`). `svg_of` writes the same placements as one SVG
document, to look at.

Angles are degrees, clockwise positive (+y is down), as SVG ``rotate`` and
``rigdoc.blit_rotated`` turn.
"""
from __future__ import annotations

import io
import math
from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Tuple

from PIL import Image

Point = Tuple[float, float]
#: An affine map as SVG writes one: ``x' = a x + c y + e``, ``y' = b x + d y + f``.
Affine = Tuple[float, float, float, float, float, float]

IDENT: Affine = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


def mul(m: Affine, n: Affine) -> Affine:
    """``m`` after ``n``."""
    a, b, c, d, e, f = m
    A, B, C, D, E, F = n
    return (a * A + c * B, b * A + d * B, a * C + c * D, b * C + d * D, a * E + c * F + e, b * E + d * F + f)


def chain(*maps: Affine) -> Affine:
    """The maps applied right to left, as SVG nests transforms."""
    out = IDENT
    for m in maps:
        out = mul(out, m)
    return out


def T(x: float, y: float) -> Affine:
    return (1.0, 0.0, 0.0, 1.0, float(x), float(y))


def R(degrees: float, cx: float = 0.0, cy: float = 0.0) -> Affine:
    """A turn of ``degrees`` about ``(cx, cy)``."""
    r = math.radians(degrees)
    c, s = math.cos(r), math.sin(r)
    return chain(T(cx, cy), (c, s, -s, c, 0.0, 0.0), T(-cx, -cy))


def apply(m: Affine, p: Point) -> Point:
    a, b, c, d, e, f = m
    return (a * p[0] + c * p[1] + e, b * p[0] + d * p[1] + f)


def angle_of(m: Affine) -> float:
    """The turn of a rigid map, in degrees."""
    return math.degrees(math.atan2(m[1], m[0]))


@dataclass(frozen=True)
class Piece:
    """SVG content in its own coordinates. ``origin`` is the point a placement
    puts somewhere; ``axis`` (degrees, in the content's coordinates) is the
    direction a placement's stretch scales along; ``reach`` is how far from
    ``origin`` the content can be (the box that is painted)."""

    body: Tuple[str, ...]
    origin: Point = (0.0, 0.0)
    axis: float = 90.0
    reach: float = 1200.0


@dataclass
class Placed:
    """One draw of a frame: ``piece`` stretched by ``stretch`` along its axis
    about its origin, then moved by the rigid map ``m``. ``name`` is the draw's
    track (once a frame); ``z`` its draw order (ties keep the order added)."""

    name: str
    z: float
    piece: Piece
    m: Affine = IDENT
    stretch: float = 1.0

    def full(self) -> Affine:
        """The whole map, the stretch in it (for the SVG of a frame)."""
        if self.stretch == 1.0:
            return self.m
        ox, oy = self.piece.origin
        turn = self.piece.axis - 90.0
        squash = (1.0, 0.0, 0.0, self.stretch, 0.0, 0.0)
        return chain(self.m, T(ox, oy), R(turn), squash, R(-turn), T(-ox, -oy))


@dataclass
class Scene:
    """The draws of one frame, in the order they were added."""

    items: List[Placed] = field(default_factory=list)

    def add(self, name: str, z: float, piece: Piece, m: Affine = IDENT, stretch: float = 1.0) -> None:
        self.items.append(Placed(name, z, piece, m, stretch))

    def ordered(self) -> List[Placed]:
        return [p for _k, p in sorted(enumerate(self.items), key=lambda kp: (kp[1].z, kp[0]))]


def svg_of(scene: Scene, view: Tuple[float, float, float, float]) -> str:
    """The frame as one SVG document over ``view`` (x, y, w, h)."""
    x, y, w, h = view
    out = ['<svg xmlns="http://www.w3.org/2000/svg" '
           f'width="{w:g}" height="{h:g}" viewBox="{x:g} {y:g} {w:g} {h:g}">']
    for k, placed in enumerate(scene.ordered()):
        a, b, c, d, e, f = placed.full()
        out.append(f'<g id="d{k}-{placed.name}" transform="matrix({a:.6f} {b:.6f} {c:.6f} {d:.6f} {e:.3f} {f:.3f})">')
        out.extend(placed.piece.body)
        out.append("</g>")
    out.append("</svg>")
    return "\n".join(out)


#: A transparent border kept round a painted piece: a resampled edge needs it.
BORDER = 2
_RASTERS: Dict[Tuple[Tuple[str, ...], Point, float, float], Tuple[Image.Image, Point]] = {}


def rasterize(piece: Piece) -> Tuple[Image.Image, Point]:
    """``piece`` painted at one pixel a unit, turned so its axis is +y, cut to
    what it covers: the raster and where its origin is in it. Cached."""
    key = (piece.body, piece.origin, piece.axis, piece.reach)
    cached = _RASTERS.get(key)
    if cached is not None:
        return cached
    import resvg_py

    ox, oy = piece.origin
    r = piece.reach
    turn = 90.0 - piece.axis
    head = ('<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{2 * r:g}" height="{2 * r:g}" viewBox="{ox - r:g} {oy - r:g} {2 * r:g} {2 * r:g}">')
    body = list(piece.body)
    if turn:
        body = [f'<g transform="rotate({turn:.6f} {ox:.4f} {oy:.4f})">'] + body + ["</g>"]
    text = "\n".join([head] + body + ["</svg>"])
    data = resvg_py.svg_to_bytes(svg_string=text, skip_system_fonts=True)
    image = Image.open(io.BytesIO(bytes(data))).convert("RGBA")
    box = image.getchannel("A").getbbox()
    if box is None:
        cached = (Image.new("RGBA", (1, 1), (0, 0, 0, 0)), (0.0, 0.0))
    else:
        x0, y0 = max(0, box[0] - BORDER), max(0, box[1] - BORDER)
        x1, y1 = min(image.width, box[2] + BORDER), min(image.height, box[3] + BORDER)
        assert box[0] > 0 and box[1] > 0 and box[2] < image.width and box[3] < image.height, (
            f"a piece reaches past its {r:g} reach: {box} of {image.size}")
        cached = (image.crop((x0, y0, x1, y1)), (r - x0, r - y0))
    _RASTERS[key] = cached
    return cached


def compose(scene: Scene, size: Tuple[int, int], offset: Point) -> Image.Image:
    """The frame on a canvas of ``size``: each draw blitted, in order, through
    ``rigdoc.blit_rotated`` (a part flipbook records it there). ``offset`` is
    the canvas pixel of the drawing's (0, 0)."""
    from ....authoring import rigdoc

    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    for placed in scene.ordered():
        raster, pivot = rasterize(placed.piece)
        at = apply(placed.m, placed.piece.origin)
        degrees = angle_of(placed.m) + placed.piece.axis - 90.0
        rigdoc.blit_rotated(canvas, raster, pivot, (at[0] + offset[0], at[1] + offset[1]), degrees,
                            part_name=placed.name, scale_y=placed.stretch)
    return canvas


def bone(a: Point, b: Point, length: float) -> Tuple[Affine, float]:
    """The rigid map and the stretch that put a bone drawn from (0, 0) along +y,
    ``length`` long, from ``a`` to ``b``."""
    d = math.hypot(b[0] - a[0], b[1] - a[1]) or 1e-6
    turn = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) - 90.0
    return chain(T(*a), R(turn)), d / length


def at_point(p: Point, degrees: float = 0.0) -> Affine:
    """The map that puts a piece's (0, 0) at ``p``, turned ``degrees``."""
    return chain(T(*p), R(degrees))


def joined(lines: Sequence[str]) -> Tuple[str, ...]:
    return tuple(lines)
