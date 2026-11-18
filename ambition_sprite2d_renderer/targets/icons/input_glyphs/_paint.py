"""Shared primitives for the input-prompt art: palette, shapes, plates, text.

Every painter in this package draws into a BOX of a canvas, in canvas pixels.
A glyph file is one painter on a canvas of its own. A device illustration calls
the same painters with smaller boxes. Thus a button on a device is the same
drawing as its glyph, and the device layout is the list of those boxes.

The look follows ``hud_icons``: a light body with a dark rim. The rim keeps a
glyph visible on a white stage, and the light body keeps it visible on a dark
one. A plate has a darker lower lip, so a cap reads as a raised part.
"""

from __future__ import annotations

import math
from typing import Callable, List, Optional, Sequence, Tuple

from PIL import Image

from ambition_sprite2d_renderer.core.draw import blending_draw, font, resize_transparent_sprite

Color = Tuple[int, int, int, int]
Point = Tuple[float, float]
Box = Tuple[float, float, float, float]
#: A shape that can grow: ``shape(grow)`` gives its outline, with every edge
#: moved out by ``grow`` pixels (a negative value moves the edges in).
Shape = Callable[[float], List[Point]]

#: Supersample factor. Painters draw at this multiple and the file is reduced.
SUPERSAMPLE = 4

INK: Color = (18, 20, 28, 255)
BODY: Color = (244, 246, 251, 255)
LIP: Color = (190, 197, 211, 255)
PRESSED: Color = (205, 211, 223, 255)
LABEL: Color = (28, 32, 44, 255)
WELL: Color = (74, 81, 96, 255)
#: The colour of "this one": a highlighted direction, button or key part.
ACCENT: Color = (255, 182, 30, 255)
ACCENT_LIP: Color = (206, 128, 10, 255)
#: A light mark on a dark part (the arrows inside a stick well).
MARK: Color = (226, 231, 240, 255)


# ---- geometry -------------------------------------------------------------


def box_size(box: Box) -> Tuple[float, float]:
    return box[2] - box[0], box[3] - box[1]


def box_center(box: Box) -> Point:
    return (box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0


def sub_box(box: Box, fx0: float, fy0: float, fx1: float, fy1: float) -> Box:
    """The part of ``box`` between the given fractions of its width and height."""
    w, h = box_size(box)
    return (box[0] + fx0 * w, box[1] + fy0 * h, box[0] + fx1 * w, box[1] + fy1 * h)


def square_in(box: Box, frac: float = 1.0) -> Box:
    """The largest centred square in ``box``, scaled by ``frac``."""
    w, h = box_size(box)
    side = min(w, h) * frac
    cx, cy = box_center(box)
    return (cx - side / 2, cy - side / 2, cx + side / 2, cy + side / 2)


def shift(points: Sequence[Point], dx: float, dy: float) -> List[Point]:
    return [(x + dx, y + dy) for x, y in points]


def ellipse_shape(cx: float, cy: float, rx: float, ry: float, rot_deg: float = 0.0, n: int = 96) -> Shape:
    rot = math.radians(rot_deg)
    c, s = math.cos(rot), math.sin(rot)

    def shape(grow: float) -> List[Point]:
        ax, ay = max(0.5, rx + grow), max(0.5, ry + grow)
        pts = []
        for i in range(n):
            t = 2 * math.pi * i / n
            x, y = ax * math.cos(t), ay * math.sin(t)
            pts.append((cx + x * c - y * s, cy + x * s + y * c))
        return pts

    return shape


def circle_shape(cx: float, cy: float, r: float) -> Shape:
    return ellipse_shape(cx, cy, r, r)


def rrect_shape(
    box: Box,
    radii: float | Tuple[float, float, float, float],
    n: int = 12,
) -> Shape:
    """A rounded rectangle; ``radii`` are (top-left, top-right, bottom-right,
    bottom-left) in pixels, or one value for all four."""
    if not isinstance(radii, tuple):
        radii = (radii, radii, radii, radii)

    def shape(grow: float) -> List[Point]:
        x0, y0, x1, y1 = box[0] - grow, box[1] - grow, box[2] + grow, box[3] + grow
        half = min(x1 - x0, y1 - y0) / 2.0
        pts: List[Point] = []
        corners = (
            (x0, y0, math.pi, 1.5 * math.pi),  # top-left
            (x1, y0, 1.5 * math.pi, 2.0 * math.pi),  # top-right
            (x1, y1, 0.0, 0.5 * math.pi),  # bottom-right
            (x0, y1, 0.5 * math.pi, math.pi),  # bottom-left
        )
        signs = ((1, 1), (-1, 1), (-1, -1), (1, -1))
        for (cx, cy, a0, a1), (sx, sy), r in zip(corners, signs, radii):
            r = max(0.0, min(half, r + grow if r > 0 else 0.0))
            ox, oy = cx + sx * r, cy + sy * r
            if r <= 0.0:
                pts.append((cx, cy))
                continue
            for i in range(n + 1):
                t = a0 + (a1 - a0) * i / n
                pts.append((ox + r * math.cos(t), oy + r * math.sin(t)))
        return pts

    return shape


def polygon_shape(points: Sequence[Point]) -> Shape:
    """A convex polygon that grows by moving each vertex out from the centroid
    along its corner bisector. Good enough for the small arrow and arm shapes
    here, which are convex and roughly regular."""
    pts = list(points)
    n = len(pts)

    def shape(grow: float) -> List[Point]:
        if grow == 0:
            return list(pts)
        out = []
        for i in range(n):
            px, py = pts[i - 1]
            x, y = pts[i]
            nx, ny = pts[(i + 1) % n]
            # Outward normals of the two edges at this vertex.
            normals = []
            for (ax, ay), (bx, by) in (((px, py), (x, y)), ((x, y), (nx, ny))):
                ex, ey = bx - ax, by - ay
                length = math.hypot(ex, ey) or 1.0
                normals.append((ey / length, -ex / length))
            mx, my = normals[0][0] + normals[1][0], normals[0][1] + normals[1][1]
            length = math.hypot(mx, my) or 1.0
            mx, my = mx / length, my / length
            cos_half = max(0.25, normals[0][0] * mx + normals[0][1] * my)
            out.append((x + mx * grow / cos_half, y + my * grow / cos_half))
        return out

    # The outward normal above assumes clockwise winding in screen space (y
    # down). Reverse a counter-clockwise outline so `grow` always moves out.
    area = sum(pts[i - 1][0] * pts[i][1] - pts[i][0] * pts[i - 1][1] for i in range(n))
    if area < 0:
        pts.reverse()
    return shape


# ---- painting -------------------------------------------------------------


def rim_width(box: Box) -> float:
    """The dark rim width for a part in ``box``: thick enough to survive a
    reduction to 32 px, where it is about two pixels."""
    w, h = box_size(box)
    return max(1.5, 0.055 * min(w, h))


def plate(
    canvas: Image.Image,
    shape: Shape,
    rim: float,
    *,
    body: Color = BODY,
    lip: Color = LIP,
    bevel: float = 0.0,
) -> None:
    """A raised part: a dark rim, a darker lower lip, and a light top face."""
    d = blending_draw(canvas)
    d.polygon(shape(rim), fill=INK)
    if bevel > 0:
        d.polygon(shape(0), fill=lip)
        d.polygon(shift(shape(-bevel * 0.55), 0, -bevel * 0.55), fill=body)
    else:
        d.polygon(shape(0), fill=body)


def text_size(label: str, size_px: float, stroke: int = 0) -> Tuple[float, float]:
    f = font(int(round(size_px)))
    x0, y0, x1, y1 = f.getbbox(label, stroke_width=stroke)
    return x1 - x0, y1 - y0


def fit_font_px(label: str, max_w: float, max_h: float, start_px: float) -> float:
    """The largest font size not above ``start_px`` whose ink fits the area."""
    px = start_px
    while px > 6:
        w, h = text_size(label, px)
        if w <= max_w and h <= max_h:
            return px
        px *= 0.92
    return px


def label(
    canvas: Image.Image,
    text: str,
    center: Point,
    size_px: float,
    *,
    fill: Color = LABEL,
    stroke: float = 0.0,
    stroke_fill: Color = INK,
) -> None:
    """Draw ``text`` with its INK (not its em box) centred on ``center``."""
    d = blending_draw(canvas)
    f = font(int(round(size_px)))
    sw = int(round(stroke))
    x0, y0, x1, y1 = d.textbbox((0, 0), text, font=f, stroke_width=sw)
    x = center[0] - (x0 + x1) / 2.0
    y = center[1] - (y0 + y1) / 2.0
    d.text((x, y), text, font=f, fill=fill, stroke_width=sw, stroke_fill=stroke_fill)


def outlined_polygon(canvas: Image.Image, shape: Shape, rim: float, fill: Color) -> None:
    """A flat shape with a dark rim: an arrow, a symbol part."""
    d = blending_draw(canvas)
    d.polygon(shape(rim), fill=INK)
    d.polygon(shape(0), fill=fill)


def stroke_line(
    canvas: Image.Image,
    a: Point,
    b: Point,
    width: float,
    fill: Color,
    rim: float,
) -> None:
    """A thick line with a dark rim on every side, ends included."""
    d = blending_draw(canvas)
    ex, ey = b[0] - a[0], b[1] - a[1]
    length = math.hypot(ex, ey) or 1.0
    ux, uy = ex / length, ey / length
    a2 = (a[0] - ux * rim, a[1] - uy * rim)
    b2 = (b[0] + ux * rim, b[1] + uy * rim)
    d.line([a2, b2], fill=INK, width=int(round(width + 2 * rim)))
    d.line([a, b], fill=fill, width=int(round(width)))


def arrow_points(center: Point, size: float, direction: str) -> List[Point]:
    """A solid triangle pointing ``direction`` (up/down/left/right), fitting
    in a square of side ``size``."""
    cx, cy = center
    h = size / 2.0
    up = [(cx, cy - h), (cx + h, cy + h * 0.6), (cx - h, cy + h * 0.6)]
    angle = {"up": 0, "right": 90, "down": 180, "left": 270}[direction]
    return rotate(up, center, angle)


def rotate(points: Sequence[Point], center: Point, angle_deg: float) -> List[Point]:
    a = math.radians(angle_deg)
    c, s = math.cos(a), math.sin(a)
    cx, cy = center
    return [(cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c) for x, y in points]


DIRECTIONS = ("up", "down", "left", "right")
#: Unit offsets in screen space (y down).
DIRECTION_VECTORS = {"up": (0.0, -1.0), "down": (0.0, 1.0), "left": (-1.0, 0.0), "right": (1.0, 0.0)}


# ---- canvas ---------------------------------------------------------------


def new_canvas(size: Tuple[int, int], supersample: int = SUPERSAMPLE) -> Image.Image:
    return Image.new("RGBA", (size[0] * supersample, size[1] * supersample), (0, 0, 0, 0))


def finish(canvas: Image.Image, size: Tuple[int, int]) -> Image.Image:
    """Reduce a supersampled canvas to its file size without a pale halo."""
    return resize_transparent_sprite(canvas, size, reducing_gap=3.0)


def render_box(
    painter: Callable[[Image.Image, Box], None],
    size: Tuple[int, int],
    supersample: int = SUPERSAMPLE,
) -> Image.Image:
    """Run ``painter`` over a whole supersampled canvas and reduce it."""
    canvas = new_canvas(size, supersample)
    painter(canvas, (0.0, 0.0, float(canvas.width), float(canvas.height)))
    return finish(canvas, size)


def layer_masked(canvas: Image.Image, paint: Callable[[Image.Image], None], mask: Image.Image) -> None:
    """Paint on a scratch layer, keep only where ``mask`` is set, and composite.

    Used to colour one region of a part (one mouse button) without a second
    copy of the part's outline.
    """
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    paint(layer)
    alpha = layer.getchannel("A")
    from PIL import ImageChops

    layer.putalpha(ImageChops.multiply(alpha, mask))
    canvas.alpha_composite(layer)


def rect_mask(size: Tuple[int, int], box: Box) -> Image.Image:
    mask = Image.new("L", size, 0)
    blending_draw(mask).rectangle(box, fill=255)
    return mask


def optional_color(color: Optional[Color], default: Color) -> Color:
    return default if color is None else color
