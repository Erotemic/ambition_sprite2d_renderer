"""Shared anatomy, pieces and effects of the four vikings.

Users: ``viking_warrior``, ``viking_shieldmaiden``, ``viking_heavy_warrior``
and ``viking_heavy_shieldmaiden``. Each target keeps its own pose curves,
skeleton (``_viking_*_rig``), palette, body and head art. This module holds
what they share: the drawing pen in design units, the piece and face helpers,
limbs as bones of a fixed length, boots, fists, the weapons and shields, and
the effects as pieces placed with an opacity.

Every rigid thing is a piece painted ONCE in its own frame and turned into
place (``shape_rig``). A face is a base piece and small expression overlays
(``_toon_rig.face``). A left and right copy of one shape (horns, braids) is
one raster placed mirrored (``_fx_piece.mirrored``): its canvas is cut on a
grid of 8 canvas pixels, so the mirror survives the reduction to the frame.

Units: design (work) units of a 640 x 640 frame. The canvas is ``SUPER``
canvas pixels a unit (2560 x 2560) and it reduces 8x to the 320 x 320 frame.
Angles are degrees, clockwise positive (+y is down). The vikings face +x.
"""

from __future__ import annotations

import math
from typing import Callable, Hashable, Optional, Sequence, Tuple

from PIL import Image

from ...authoring import rigdoc, shape_rig
from . import _fx_piece
from . import _solo_shape_rig as _rig
from . import _toon_rig

Point = Tuple[float, float]
RGBA = Tuple[int, int, int, int]

SUPER = 4
WORK_FRAME_SIZE = (640, 640)
FRAME_SIZE = (320, 320)
CANVAS = (WORK_FRAME_SIZE[0] * SUPER, WORK_FRAME_SIZE[1] * SUPER)
#: Canvas pixels a frame pixel: piece canvases are cut on this grid.
GRID = CANVAS[0] // FRAME_SIZE[0]


# --------------------------------------------------------------------------
# geometry


def rot(x: float, y: float, deg: float) -> Point:
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return (x * c - y * s, x * s + y * c)


def along(origin: Point, deg: float, dist: float) -> Point:
    r = math.radians(deg)
    return (origin[0] + dist * math.cos(r), origin[1] + dist * math.sin(r))


def angle(a: Point, b: Point) -> float:
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def frame_point(root: Point, deg: float) -> Callable[[float, float], Point]:
    """The map of a point of a frame (body or head) turned ``deg`` about
    ``root`` onto the canvas (design units)."""

    def P(x: float, y: float) -> Point:
        rx, ry = rot(x, y, deg)
        return (root[0] + rx, root[1] + ry)

    return P


def catmull(pts: Sequence[Point], closed: bool = True, steps: int = 6) -> list:
    """A smooth curve through ``pts`` (Catmull-Rom)."""
    n = len(pts)
    if n < 3:
        return list(pts)
    out = []
    count = n if closed else n - 1
    for i in range(count):
        p0 = pts[(i - 1) % n] if closed else pts[max(0, i - 1)]
        p1 = pts[i]
        p2 = pts[(i + 1) % n] if closed else pts[min(n - 1, i + 1)]
        p3 = pts[(i + 2) % n] if closed else pts[min(n - 1, i + 2)]
        for k in range(steps):
            t = k / steps
            t2, t3 = t * t, t * t * t
            out.append(
                tuple(
                    0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3)
                    for j in range(2)
                )
            )
    if not closed:
        out.append(tuple(pts[-1]))
    return out


def horn_frame(a: Point, c: Point, b: Point, t: float) -> Tuple[Point, Point]:
    """The point and unit normal at ``t`` of the quadratic curve from ``a``
    through the control ``c`` to ``b``."""
    u = 1.0 - t
    p = (u * u * a[0] + 2 * u * t * c[0] + t * t * b[0], u * u * a[1] + 2 * u * t * c[1] + t * t * b[1])
    d = (2 * u * (c[0] - a[0]) + 2 * t * (b[0] - c[0]), 2 * u * (c[1] - a[1]) + 2 * t * (b[1] - c[1]))
    n = math.hypot(*d) or 1.0
    return p, (-d[1] / n, d[0] / n)


def horn_outline(a: Point, c: Point, b: Point, half: float, steps: int = 16) -> list:
    """A horn: a tapering band along the curve ``a``-``c``-``b``, ``half``
    wide each side at its root and pointed at ``b``."""
    left, right = [], []
    for i in range(steps + 1):
        t = i / steps
        (x, y), (nx, ny) = horn_frame(a, c, b, t)
        w = half * (1.0 - t) ** 0.85 + 0.3
        left.append((x + nx * w, y + ny * w))
        right.append((x - nx * w, y - ny * w))
    return left + right[::-1]


# --------------------------------------------------------------------------
# the pen: design units on a piece canvas


class Pen:
    """Paints in design units about ``origin`` (canvas pixels) of a piece
    canvas, ``k`` design units a unit (a scaled head)."""

    def __init__(self, draw, origin: Point, k: float = 1.0) -> None:
        self.d = draw
        self.o = origin
        self.k = k * SUPER

    def p(self, x: float, y: float) -> Point:
        return (self.o[0] + x * self.k, self.o[1] + y * self.k)

    def w(self, width: float) -> int:
        return max(1, int(round(width * self.k)))

    def poly(self, pts, fill, line: Optional[RGBA] = None, width: float = 1.0, smooth: bool = False) -> None:
        if smooth:
            pts = catmull(pts)
        q = [self.p(*a) for a in pts]
        if fill is not None:
            self.d.polygon(q, fill=fill)
        if line is not None and width > 0:
            self.d.line(q + [q[0]], fill=line, width=self.w(width), joint="curve")

    def line(self, pts, fill, width: float = 1.0, smooth: bool = False) -> None:
        if smooth:
            pts = catmull(pts, closed=False)
        self.d.line([self.p(*a) for a in pts], fill=fill, width=self.w(width), joint="curve")

    def ellipse(self, cx, cy, rx, ry, fill, line: Optional[RGBA] = None, width: float = 1.0) -> None:
        a, b = self.p(cx - rx, cy - ry), self.p(cx + rx, cy + ry)
        self.d.ellipse((a[0], a[1], b[0], b[1]), fill=fill, outline=line, width=self.w(width) if line is not None else 0)

    def circle(self, c: Point, r: float, fill, line: Optional[RGBA] = None, width: float = 1.0) -> None:
        self.ellipse(c[0], c[1], r, r, fill, line, width)

    def arc(self, cx, cy, rx, ry, a0, a1, fill, width: float = 1.0) -> None:
        a, b = self.p(cx - rx, cy - ry), self.p(cx + rx, cy + ry)
        self.d.arc((a[0], a[1], b[0], b[1]), a0, a1, fill=fill, width=self.w(width))


def _snap_up(v: float) -> int:
    """``v`` canvas pixels up to the grid."""
    return int(math.ceil(v / GRID - 1e-9)) * GRID


def canvas_of(extent: Tuple[float, float, float, float], k: float = 1.0) -> Tuple[Tuple[int, int], Point]:
    """The canvas size and pivot (canvas pixels) of a piece reaching
    ``extent`` = (left, top, right, bottom) design units from its pivot, cut
    on the grid (so a mirrored copy reduces to the mirror)."""
    left, top, right, bottom = (e * k * SUPER for e in extent)
    ox, oy = _snap_up(left), _snap_up(top)
    return (ox + _snap_up(right), oy + _snap_up(bottom)), (float(ox), float(oy))


def piece(key: Hashable, extent, paint: Callable[[Pen], None], k: float = 1.0):
    """A piece ``paint(pen)`` paints about its pivot (design units), on a
    canvas reaching ``extent`` from it. ``key`` names everything ``paint``
    reads (the target's name first)."""
    size, origin = canvas_of(extent, k)
    return shape_rig.piece(("viking",) + tuple(key) + (k,), size, origin, lambda d: paint(Pen(d, origin, k)))


def put(img: Image.Image, part, at: Point, deg: float, name: str, opacity: float = 1.0) -> None:
    """``part`` with its pivot at ``at`` (design units), turned ``deg``."""
    if part is None:
        return
    _rig.place(img, part, (at[0] * SUPER, at[1] * SUPER), deg, name, opacity)


def put_mirrored(img: Image.Image, part, at: Point, deg: float, name: str) -> None:
    """``part`` mirrored left to right about its pivot (the same raster
    transposed: one part on the page), then placed as ``put``."""
    put(img, _fx_piece.mirrored(part), at, deg, name)


def face(img: Image.Image, at: Point, deg: float, name: str, extent, base, features, k: float = 1.0) -> None:
    """A head as a base piece and expression overlays riding it
    (``_toon_rig.face``). ``base`` = (key, paint(pen)); each feature =
    (suffix, key, paint(pen)), key ``None`` when it is not drawn."""
    size, origin = canvas_of(extent, k)

    def wrap(paint):
        return lambda d: paint(Pen(d, origin, k))

    def place(part, part_name: str) -> None:
        put(img, part, at, deg, part_name)

    _toon_rig.face(
        place,
        name,
        size,
        origin,
        (("viking",) + tuple(base[0]) + (k,), wrap(base[1])),
        [(suffix, None if key is None else ("viking_overlay",) + tuple(key) + (k,), wrap(paint)) for suffix, key, paint in features],
    )


def downsample(img: Image.Image) -> Image.Image:
    return rigdoc.downsampled_canvas(img, FRAME_SIZE)


def new_canvas() -> Image.Image:
    return Image.new("RGBA", CANVAS, (0, 0, 0, 0))


# --------------------------------------------------------------------------
# limbs


def paint_tube(pen: Pen, length: float, r0: float, r1: float, fill: RGBA, line: RGBA, width: float, start_cap: bool = True) -> None:
    """A tapered tube along +x from the pivot, outlined on its silhouette
    only. ``start_cap`` False: the start end is filled, not outlined (the
    tube continues a limb at a joint)."""
    if start_cap:
        pen.ellipse(0, 0, r0, r0, fill, line, width)
    else:
        pen.ellipse(0, 0, max(0.5, r0 - width), max(0.5, r0 - width), fill)
    pen.ellipse(length, 0, r1, r1, fill, line, width)
    pen.poly([(0, -r0), (length, -r1), (length, r1), (0, r0)], fill)
    h = width / 2.0
    pen.line([(0, -r0 + h), (length, -r1 + h)], line, width)
    pen.line([(0, r0 - h), (length, r1 - h)], line, width)


def tube_piece(key: Hashable, length: float, r0: float, r1: float, fill: RGBA, line: RGBA, width: float, start_cap: bool = True, detail: Optional[Callable[[Pen], None]] = None, k: float = 1.0):
    """A limb bone as a piece: ``paint_tube`` and an optional ``detail(pen)``
    painted on it in the bone's own frame (a cuff, a wrap, a band)."""
    r = max(r0, r1) + width + 1.0

    def paint(pen: Pen) -> None:
        paint_tube(pen, length, r0, r1, fill, line, width, start_cap)
        if detail is not None:
            detail(pen)

    return piece(("tube",) + tuple(key) + (length, r0, r1, fill, line, width, start_cap), (r, r, length + r, r), paint, k=k)


def two_bone(root: Point, target: Point, l1: float, l2: float, bend: Point) -> Tuple[Point, Point]:
    """``(joint, end)`` of a limb of bone lengths ``l1``, ``l2`` from
    ``root`` toward ``target``, the joint on the side of the point ``bend``.
    Out of reach the limb straightens toward the target (the end falls short)."""
    dx, dy = target[0] - root[0], target[1] - root[1]
    d = math.hypot(dx, dy)
    if d < 1e-6:
        return (root[0], root[1] + l1), (root[0], root[1] + l1 - l2)
    ux, uy = dx / d, dy / d
    d = max(abs(l1 - l2) + 0.5, min(d, l1 + l2 - 0.05))
    end = (root[0] + ux * d, root[1] + uy * d)
    a = (l1 * l1 - l2 * l2 + d * d) / (2 * d)
    h = math.sqrt(max(0.0, l1 * l1 - a * a))
    bx, by = root[0] + ux * a, root[1] + uy * a
    c1 = (bx - uy * h, by + ux * h)
    c2 = (bx + uy * h, by - ux * h)
    joint = c1 if math.dist(c1, bend) <= math.dist(c2, bend) else c2
    return joint, end


def leg(
    img: Image.Image,
    hip: Point,
    deg: float,
    lift: float,
    thigh: float,
    shin: float,
    thigh_part,
    shin_part,
    foot_part,
    side: str,
    foot_deg: float = 0.0,
) -> Point:
    """Thigh and shin of fixed lengths: the thigh at ``deg``, the shin aimed
    a little forward of it and raised by ``lift``; the foot rides the ankle
    flat (or turned ``foot_deg``: a body lying down). Returns the ankle."""
    knee = along(hip, deg, thigh)
    reach = along(knee, deg + 8, shin)
    reach = (reach[0], reach[1] - lift)
    shin_deg = angle(knee, reach)
    ankle = along(knee, shin_deg, shin)
    put(img, thigh_part, hip, deg, f"{side}_thigh")
    put(img, shin_part, knee, shin_deg, f"{side}_shin")
    put(img, foot_part, ankle, foot_deg, f"{side}_foot")
    return ankle


def arm(img: Image.Image, shoulder: Point, target: Point, l1: float, l2: float, bend: Point, upper_part, fore_part, side: str) -> Tuple[Point, Point]:
    """Upper arm and forearm of fixed lengths reaching for ``target``, the
    elbow toward ``bend``. Returns (elbow, hand)."""
    elbow, hand = two_bone(shoulder, target, l1, l2, bend)
    put(img, upper_part, shoulder, angle(shoulder, elbow), f"{side}_upper_arm")
    put(img, fore_part, elbow, angle(elbow, hand), f"{side}_forearm")
    return elbow, hand


def boot_piece(key: Hashable, pal: dict, *, toe: float = 15.0, height: float = 8.0, cuff: Optional[RGBA] = None, straps: Optional[RGBA] = None, k: float = 1.0):
    """A boot (or sandal, with ``straps``) at the ankle, toe toward +x."""
    O = pal["outline"]

    def paint(pen: Pen) -> None:
        sole = pal.get("sole", O)
        pen.poly([(-9, -height), (6, -height), (9, -2), (toe, 1), (toe + 2, 6), (toe - 1, 10), (-10, 10), (-11, 2)], pal["boot"], O, 1.6, smooth=False)
        pen.line([(-10, 9.6), (toe - 1, 9.6)], sole, 1.6)
        pen.line([(0, -height + 1), (2, 6)], pal.get("boot_shade", O), 0.9)
        if straps is not None:
            for x in (-6, -1, 4, 9):
                pen.line([(x, -height + 1), (x + 2, 8)], straps, 1.0)
        if cuff is not None:
            pen.poly([(-11, -height - 4), (9, -height - 4), (10, -height + 2), (4, -height + 4), (-2, -height + 1), (-8, -height + 4), (-12, -height + 1)], cuff, O, 1.2)

    return piece(("boot",) + tuple(key), (16, height + 8, toe + 6, 14), paint, k=k)


def fist_piece(key: Hashable, skin: RGBA, line: RGBA, r: float = 6.0, band: Optional[RGBA] = None, k: float = 1.0):
    """A fist at the end of a forearm, the forearm along +x: knuckles ahead,
    a thumb over the top."""

    def paint(pen: Pen) -> None:
        pen.ellipse(1.0, 0, r, r * 0.92, skin, line, 1.4)
        pen.line([(r * 0.55, -r * 0.55), (r * 0.6, r * 0.55)], line, 0.8)
        pen.line([(-r * 0.4, -r * 0.7), (r * 0.5, -r * 0.35)], line, 0.8)
        if band is not None:
            pen.line([(-r * 0.9, -r * 0.8), (-r * 0.9, r * 0.8)], band, 1.6)

    return piece(("fist",) + tuple(key) + (skin, line, r, band), (r + 3, r + 3, r + 4, r + 3), paint, k=k)


# --------------------------------------------------------------------------
# weapons (painted along +x from the grip; the cutting edge faces +y, the
# side a clockwise swing leads with)


def dane_axe_piece(key: Hashable, pal: dict, butt: float, tip: float, blade: float = 1.0, k: float = 1.0):
    """A long two-handed axe gripped at the pivot: the haft from ``-butt``
    to ``tip``, a bearded crescent head at the tip."""
    O = pal["outline"]
    s = blade

    def paint(pen: Pen) -> None:
        pen.line([(-butt, 0), (tip + 2, 0)], O, 5.4)
        pen.line([(-butt + 0.8, 0), (tip + 1.2, 0)], pal["wood"], 3.4)
        pen.line([(-butt + 2, -0.8), (tip - 6, -0.8)], pal["wood_light"], 0.9)
        for x in (-12, -6, 0, 6, 12):
            pen.line([(x - 2, -2), (x + 2, 2)], pal["leather_dark"], 1.1)
        pen.poly([(-butt - 3, -2.8), (-butt + 4, -2.8), (-butt + 4, 2.8), (-butt - 3, 2.8)], pal["steel_shade"], O, 1.0)
        h = tip - 8 * s
        head = [
            (h - 5 * s, -6 * s), (h + 7 * s, -6 * s), (h + 8 * s, 3 * s), (h + 13 * s, 14 * s),
            (h + 21 * s, 26 * s), (h + 9 * s, 33 * s), (h - 6 * s, 34 * s), (h - 16 * s, 30 * s),
            (h - 9 * s, 22 * s), (h - 5 * s, 10 * s), (h - 5 * s, 3 * s),
        ]
        pen.poly(head, pal["steel"], O, 1.6)
        edge = [(h + 21 * s, 26 * s), (h + 9 * s, 33 * s), (h - 6 * s, 34 * s), (h - 16 * s, 30 * s), (h - 12 * s, 27 * s), (h - 4 * s, 29 * s), (h + 8 * s, 28 * s), (h + 16 * s, 23 * s)]
        pen.poly(edge, pal["steel_light"])
        pen.poly([(h - 5 * s, -6 * s), (h - 1 * s, -6 * s), (h, 12 * s), (h - 7 * s, 24 * s), (h - 9 * s, 22 * s), (h - 5 * s, 10 * s)], pal["steel_shade"])
        pen.poly(head, None, O, 1.6)
        pen.circle((h + 1 * s, 0), 1.6 * s, pal["gold"], O, 0.6)

    return piece(("dane_axe",) + tuple(key) + (butt, tip, blade), (butt + 6, 12 * s, tip + 26 * s, 38 * s), paint, k=k)


def hand_axe_piece(key: Hashable, pal: dict, length: float, k: float = 1.0):
    """A one-handed bearded axe held at the pivot near the haft's end."""
    O = pal["outline"]

    def paint(pen: Pen) -> None:
        pen.line([(-6, 0), (length + 2, 0)], O, 5.0)
        pen.line([(-5.2, 0), (length + 1.2, 0)], pal["wood"], 3.0)
        pen.line([(-3, -0.8), (length - 6, -0.8)], pal["wood_light"], 0.8)
        pen.circle((-6, 0), 2.6, pal["steel_shade"], O, 0.9)
        h = length - 6
        head = [(h - 4, -5), (h + 6, -5), (h + 6, 2), (h + 10, 12), (h + 15, 21), (h + 4, 26), (h - 8, 25), (h - 4, 16), (h - 4, 3)]
        pen.poly(head, pal["steel"], O, 1.5)
        pen.poly([(h + 15, 21), (h + 4, 26), (h - 8, 25), (h - 5, 21), (h + 4, 22), (h + 11, 18)], pal["steel_light"])
        pen.poly([(h - 4, -5), (h - 1, -5), (h - 1, 14), (h - 6, 20), (h - 4, 16)], pal["steel_shade"])
        pen.poly(head, None, O, 1.5)
        pen.circle((h + 1, 0), 1.4, pal["gold"], O, 0.5)

    return piece(("hand_axe",) + tuple(key) + (length,), (10, 10, length + 20, 30), paint, k=k)


def double_axe_piece(key: Hashable, pal: dict, butt: float, tip: float, k: float = 1.0):
    """A long haft gripped at the pivot with a double-bladed head at the tip:
    two crescent blades, one each side of the haft."""
    O = pal["outline"]

    def paint(pen: Pen) -> None:
        pen.line([(-butt, 0), (tip + 4, 0)], O, 6.0)
        pen.line([(-butt + 0.8, 0), (tip + 3, 0)], pal["wood"], 4.0)
        pen.line([(-butt + 2, -1), (tip - 8, -1)], pal["wood_light"], 1.0)
        for x in (-14, -7, 0, 7, 14):
            pen.line([(x - 2, -2.4), (x + 2, 2.4)], pal["leather_dark"], 1.2)
        pen.poly([(-butt - 6, 0), (-butt + 2, -4), (-butt + 4, 0), (-butt + 2, 4)], pal["steel_shade"], O, 1.0)
        h = tip - 6
        for sign in (1, -1):
            blade = [(h - 5, 4 * sign), (h + 5, 4 * sign), (h + 10, 14 * sign), (h + 18, 30 * sign), (h + 2, 36 * sign), (h - 14, 30 * sign), (h - 10, 14 * sign)]
            pen.poly(blade, pal["steel"] if sign > 0 else pal["steel_shade"], O, 1.7)
            pen.poly([(h + 18, 30 * sign), (h + 2, 36 * sign), (h - 14, 30 * sign), (h - 10, 26 * sign), (h + 2, 30 * sign), (h + 13, 25 * sign)], pal["steel_light"])
            pen.poly(blade, None, O, 1.7)
        pen.poly([(h - 6, -6), (h + 6, -6), (h + 6, 6), (h - 6, 6)], pal["steel_shade"], O, 1.3)
        pen.circle((h, 0), 2.2, pal["gold"], O, 0.7)
        pen.poly([(tip + 2, -3), (tip + 10, 0), (tip + 2, 3)], pal["steel"], O, 1.0)

    return piece(("double_axe",) + tuple(key) + (butt, tip), (butt + 8, 40, tip + 24, 40), paint, k=k)


def spear_piece(key: Hashable, pal: dict, butt: float, tip: float, k: float = 1.0):
    """A spear held at the pivot: an ash shaft from ``-butt`` to ``tip``, a
    leaf blade beyond it, a bound socket and an iron butt spike."""
    O = pal["outline"]

    def paint(pen: Pen) -> None:
        pen.line([(-butt, 0), (tip, 0)], O, 6.4)
        pen.line([(-butt + 1, 0), (tip - 1, 0)], pal["wood"], 4.2)
        pen.line([(-butt + 2, -1.1), (tip - 4, -1.1)], pal["wood_light"], 1.0)
        pen.poly([(tip - 4, -4), (tip + 6, -4), (tip + 6, 4), (tip - 4, 4)], pal["gold_shade"], O, 1.1)
        pen.poly([(tip + 5, 0), (tip + 12, -9), (tip + 34, 0), (tip + 12, 9)], pal["steel"], O, 1.5)
        pen.poly([(tip + 7, 0), (tip + 13, -1.4), (tip + 31, 0), (tip + 13, 1.4)], pal["steel_light"])
        pen.line([(tip + 7, 0), (tip + 32, 0)], pal["steel_shade"], 0.8)
        pen.poly([(-butt - 12, 0), (-butt + 1, -4), (-butt + 1, 4)], pal["steel_shade"], O, 1.1)
        for x in (-6, 0, 6):
            pen.line([(x - 2, -3), (x + 2, 3)], pal["leather_dark"], 1.2)

    return piece(("spear",) + tuple(key) + (butt, tip), (butt + 16, 12, tip + 38, 12), paint, k=k)


# --------------------------------------------------------------------------
# shields


def round_shield_piece(key: Hashable, pal: dict, r: float, k: float = 1.0):
    """A round shield face on: wooden planks painted in two colours, an iron
    rim with rivets and a domed boss. ``pal`` names ``shield``,
    ``shield_dark``, ``shield_pattern``, ``steel``, ``steel_shade``."""
    O = pal["outline"]

    def paint(pen: Pen) -> None:
        pen.circle((0, 0), r + 2.6, pal["steel_shade"], O, 1.8)
        pen.circle((0, 0), r, pal["shield"], O, 1.0)
        # quarters in the pattern colour, a pinwheel as on the old sagas' shields
        for a0 in (0, 90, 180, 270):
            pts = [(0, 0)]
            for i in range(9):
                a = math.radians(a0 + i * 45 / 8.0)
                pts.append((r * 0.98 * math.cos(a), r * 0.98 * math.sin(a)))
            pen.poly(pts, pal["shield_pattern"])
        for a in range(0, 180, 30):
            c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
            pen.line([(-r * c * 0.98, -r * s * 0.98), (r * c * 0.98, r * s * 0.98)], pal["shield_dark"], 0.7)
        pen.circle((0, 0), r, None, O, 1.0)
        for i in range(12):
            a = math.radians(i * 30 + 15)
            pen.circle((math.cos(a) * (r + 1.2), math.sin(a) * (r + 1.2)), 1.0, pal["steel"])
        pen.circle((0, 0), r * 0.3, pal["steel"], O, 1.3)
        pen.ellipse(-r * 0.08, -r * 0.1, r * 0.13, r * 0.1, pal["steel_light"])

    return piece(("round_shield",) + tuple(key) + (r,), (r + 5, r + 5, r + 5, r + 5), paint, k=k)


def saw_shield_piece(key: Hashable, pal: dict, r: float, teeth: int = 18, k: float = 1.0):
    """A round shield with a toothed iron rim, a dark face and a star of
    straps around the boss (the heavy shieldmaiden's)."""
    O = pal["outline"]

    def paint(pen: Pen) -> None:
        pts = []
        for i in range(teeth * 2):
            a = math.tau * i / (teeth * 2)
            rr = r + (6 if i % 2 == 0 else 1.5)
            pts.append((rr * math.cos(a), rr * math.sin(a)))
        pen.poly(pts, pal["shield"], O, 1.6)
        pen.circle((0, 0), r * 0.82, pal["shield_shade"], O, 1.2)
        pen.circle((0, 0), r * 0.82 - 3, None, pal["shield"], 0.9)
        for i in range(8):
            a = math.tau * i / 8 + math.pi / 8
            c, s = math.cos(a), math.sin(a)
            pen.line([(c * r * 0.3, s * r * 0.3), (c * r * 0.78, s * r * 0.78)], pal["gold_shade"], 2.6)
            pen.circle((c * r * 0.7, s * r * 0.7), 1.4, pal["gold"])
        pen.circle((0, 0), r * 0.3, pal["steel"], O, 1.3)
        pen.circle((0, 0), r * 0.12, pal["gold"], O, 0.8)
        pen.ellipse(-r * 0.08, -r * 0.12, r * 0.1, r * 0.07, pal["steel_light"])

    return piece(("saw_shield",) + tuple(key) + (r, teeth), (r + 8, r + 8, r + 8, r + 8), paint, k=k)


# --------------------------------------------------------------------------
# effects: painted once at full strength, placed with an opacity


def swing_arc_piece(key: Hashable, color: RGBA, radius: float, span: float = 100.0, width: float = 6.0, lead: float = 20.0, k: float = 1.0):
    """A swing trail about the grip: an arc of ``radius`` from ``lead``
    degrees back ``span`` degrees (counter-clockwise: behind a clockwise
    swing), thick at its head and thinning to its tail."""

    def paint(pen: Pen) -> None:
        steps = 24
        outer, inner = [], []
        for i in range(steps + 1):
            t = i / steps
            a = math.radians(lead - span * t)
            w = width * (1.0 - t) ** 1.2 + 0.4
            outer.append(((radius + w / 2) * math.cos(a), (radius + w / 2) * math.sin(a)))
            inner.append(((radius - w / 2) * math.cos(a), (radius - w / 2) * math.sin(a)))
        pen.poly(outer + inner[::-1], color)
        hi = (255, 255, 250, min(255, color[3] + 60))
        core = []
        for i in range(steps // 2 + 1):
            a = math.radians(lead - span * 0.5 * i / (steps // 2))
            core.append((radius * math.cos(a), radius * math.sin(a)))
        pen.line(core, hi, width * 0.25)

    r = radius + width + 2
    return piece(("swing_arc",) + tuple(key) + (color, radius, span, width, lead), (r, r, r, r), paint, k=k)


def burst_piece(key: Hashable, color: RGBA, r: float, k: float = 1.0):
    """An impact burst: short strokes fanned toward +x."""

    def paint(pen: Pen) -> None:
        for a in (-50, -25, 0, 25, 50):
            c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
            pen.line([(c * r * 0.45, s * r * 0.45), (c * r, s * r)], color, 2.6)
        pen.arc(0, 0, r * 0.35, r * 0.35, -70, 70, color, 2.0)

    return piece(("burst",) + tuple(key) + (color, r), (r + 3, r + 3, r + 3, r + 3), paint, k=k)


def shout_piece(key: Hashable, color: RGBA, r: float, k: float = 1.0):
    """Two sound arcs opening toward +x (a shout)."""

    def paint(pen: Pen) -> None:
        for rr, w in ((r * 0.55, 2.4), (r, 2.0)):
            pen.arc(0, 0, rr, rr * 1.1, -38, 38, color, w)

    return piece(("shout",) + tuple(key) + (color, r), (2, r * 1.2 + 3, r + 3, r * 1.2 + 3), paint, k=k)


def dust_piece(key: Hashable, color: RGBA, k: float = 1.0):
    """A few dust puffs about the pivot (a foot on the ground)."""

    def paint(pen: Pen) -> None:
        for x, y, rx, ry in ((-18, 2, 5, 3.4), (-6, -2, 6.5, 4.4), (8, 1, 5, 3.4), (18, 4, 3.2, 2.4)):
            pen.ellipse(x, y, rx, ry, color)
        hi = (min(255, color[0] + 30), min(255, color[1] + 30), min(255, color[2] + 30), color[3])
        pen.ellipse(-7, -4, 3, 1.8, hi)

    return piece(("dust",) + tuple(key) + (color,), (26, 9, 26, 9), paint, k=k)


# --------------------------------------------------------------------------
# a two-handed grip


def two_hand_grip(chest: Point, weapon_deg: float, reach: float, spread: float) -> Tuple[Point, Point, Point]:
    """``(grip, upper_hand, lower_hand)`` of a two-handed weapon at
    ``weapon_deg``: the grip sits ``reach`` out from the ``chest`` along the
    weapon (an axe raised behind the head lifts the hands above it), the
    hands ``spread`` apart along the haft."""
    grip = along(chest, weapon_deg, reach)
    return grip, along(grip, weapon_deg, spread / 2.0), along(grip, weapon_deg, -spread / 2.0)


def hand_on_haft(shoulder: Point, grip: Point, weapon_deg: float, s: float, reach: float) -> Point:
    """The point of the haft through ``grip`` (along ``weapon_deg``) a hand
    takes: ``s`` along it from the grip, or, out of an arm's ``reach`` from
    ``shoulder``, the nearest point of the haft the arm reaches (the hand
    slides along the haft; it never lets go of it)."""
    ux, uy = math.cos(math.radians(weapon_deg)), math.sin(math.radians(weapon_deg))
    want = (grip[0] + ux * s, grip[1] + uy * s)
    if math.dist(shoulder, want) <= reach:
        return want
    vx, vy = shoulder[0] - grip[0], shoulder[1] - grip[1]
    t = vx * ux + vy * uy
    perp2 = vx * vx + vy * vy - t * t
    if perp2 >= reach * reach:
        return (grip[0] + ux * t, grip[1] + uy * t)
    h = math.sqrt(reach * reach - perp2)
    s2 = min((t - h, t + h), key=lambda v: abs(v - s))
    return (grip[0] + ux * s2, grip[1] + uy * s2)


def lying_lift(lean: float, lie: float) -> float:
    """How far a falling body's root rises so the body lies ON the ground:
    0 until the lean passes 15 degrees, then up to ``lie`` (the depth of the
    back below the root, lying flat, plus the root's depth below the soles)
    as it lies flat. The legs fall with the body, so nothing props it up."""
    s = math.sin(math.radians(abs(lean)))
    return lie * max(0.0, min(1.0, (s - 0.26) / 0.74))


def mouth_state(mouth: float) -> int:
    """An open mouth in four steps: 0 shut, 1 talking, 2 shouting, 3 roaring."""
    if mouth < 0.03:
        return 0
    if mouth < 0.15:
        return 1
    if mouth < 0.25:
        return 2
    return 3


__all__ = [
    "CANVAS",
    "FRAME_SIZE",
    "GRID",
    "Pen",
    "SUPER",
    "WORK_FRAME_SIZE",
    "along",
    "angle",
    "arm",
    "boot_piece",
    "canvas_of",
    "dane_axe_piece",
    "double_axe_piece",
    "downsample",
    "dust_piece",
    "face",
    "fist_piece",
    "frame_point",
    "hand_axe_piece",
    "horn_frame",
    "horn_outline",
    "hand_on_haft",
    "leg",
    "lerp",
    "lying_lift",
    "mouth_state",
    "new_canvas",
    "piece",
    "put",
    "put_mirrored",
    "rot",
    "round_shield_piece",
    "saw_shield_piece",
    "shout_piece",
    "spear_piece",
    "swing_arc_piece",
    "burst_piece",
    "tube_piece",
    "two_bone",
    "two_hand_grip",
]
