"""A person of the cast in the round: its pieces as shapes in 3D, drawn in
any view in the cast's own paint.

The cast (``_person_rig``) is drawn three quarters from the front, facing
right, and some of it also from the front. Each of those pieces is a flat
shape for its one view. Here a piece is a shape in 3D (an ellipsoid, a loft
of level rings, a limb between two joints) with its colours on its surface,
so one description draws every view: the side, the back, the back three
quarters, and the true left views of a person who is not symmetric.

The paint is the cast's (``Kit``): a flat fill, a light rim and a shaded edge
on each part, a dark outline round it, and fine lines on it. Inside a part
the nearest surface is drawn (a beard over a chin, hair round a skull), with
no line between them. Between parts the nearest part is drawn, and its
outline goes with it.

The rows that a character has stay as they are. This draws only the views
that it does not have, and ``turnaround`` puts the character's own art beside
the same views drawn from 3D, so the fit can be judged.

Body space is in frame pixels, from the middle of the hips: ``l`` to the
person's left, ``y`` down, ``z`` forward. A ``View`` turns the camera round
the person (``yaw`` 0 is the front, 90 sees the person face right, 180 is the
back, -90 sees the person face left) and tilts it down (``pitch``). The near
side of a view that faces right is the person's RIGHT, as in the cast.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage

from ._ai_era_kit import Kit, RGBA

Vec = Tuple[float, float, float]
#: ``paint(u, v, lit, far)``: the colours (an ``(n, 4)`` array) of ``n``
#: points of a surface. ``u`` and ``v`` are where the points are on it (see
#: ``Surface``); ``lit`` is how much each faces the key light (-1 to 1);
#: ``far`` is true when the part is a far limb in this view.
Paint = Callable[[np.ndarray, np.ndarray, np.ndarray, bool], np.ndarray]

#: How far the camera looks down, in degrees. The cast's front view draws a
#: brim 12.6 px wide as an ellipse 2.6 px high (Davy Hylbert's hat): about 12.
PITCH = 10.0


@dataclass(frozen=True)
class View:
    key: str
    yaw: float
    label: str
    pitch: float = PITCH

    def basis(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Screen right, screen down, and toward the camera, in body space."""
        t, p = math.radians(self.yaw), math.radians(self.pitch)
        ex = np.array([math.cos(t), 0.0, math.sin(t)])
        level = np.array([-math.sin(t), 0.0, math.cos(t)])
        ed = level * math.cos(p) + np.array([0.0, -math.sin(p), 0.0])
        ey = np.array([0.0, math.cos(p), 0.0]) + level * math.sin(p)
        return ex, ey, ed

    def key_light(self) -> np.ndarray:
        """The key light: from in front of the viewer, high and to the left."""
        ex, ey, ed = self.basis()
        v = 0.8 * ed - 0.5 * ex - 0.35 * ey
        return v / np.linalg.norm(v)


#: The eight views, in turnaround order.
VIEWS: Tuple[View, ...] = (
    View("front", 0.0, "front"),
    View("front_3q", 45.0, "front 3/4"),
    View("side", 90.0, "side"),
    View("back_3q", 135.0, "back 3/4"),
    View("back", 180.0, "back"),
    View("back_3q_left", -135.0, "back 3/4 (left)"),
    View("side_left", -90.0, "side (left)"),
    View("front_3q_left", -45.0, "front 3/4 (left)"),
)
VIEW_BY_KEY = {v.key: v for v in VIEWS}


# ---- Paint -------------------------------------------------------------------


def fill(colour: RGBA, n: int) -> np.ndarray:
    return np.tile(np.asarray(colour, np.uint8), (n, 1))


def put(out: np.ndarray, where: np.ndarray, colour: RGBA) -> np.ndarray:
    out[where] = np.asarray(colour, np.uint8)
    return out


def flat(colour: RGBA, far: Optional[RGBA] = None, shade: Optional[RGBA] = None, at: float = -0.3) -> Paint:
    """One colour. ``far``: its colour on a far limb. ``shade``: its colour
    where the key light does not reach (``lit`` under ``at``)."""

    def paint(u, v, lit, is_far):
        out = fill(far if (is_far and far is not None) else colour, len(u))
        if shade is not None:
            put(out, lit < at, shade)
        return out

    return paint


def arc(u: np.ndarray, radius: float) -> np.ndarray:
    """How far round a surface of ``radius`` the turn ``u`` (degrees) is."""
    return radius * np.radians(u)


# ---- Surfaces ----------------------------------------------------------------


@dataclass
class Surface:
    """Triangles and what is painted on them. ``uv`` is where on its shape
    each vertex is: a loft or an ellipsoid has ``u``, the turn round it in
    degrees (0 in front, 90 to the person's left), and ``v``, its height (or
    the ``v`` its ring gives); a limb has ``u`` round it and ``v`` from 0 at
    its root to 1 at its end."""

    verts: np.ndarray
    normals: np.ndarray
    uv: np.ndarray
    tris: np.ndarray
    paint: Paint

    def moved(self, by: Vec) -> "Surface":
        return replace(self, verts=self.verts + np.asarray(by, float))


def _grid(points: np.ndarray, uv: np.ndarray, paint: Paint, middle: Optional[np.ndarray] = None) -> Surface:
    """A surface from a grid of points (rows, columns + 1, 3); the last column
    is the first again, so ``u`` does not wrap inside a triangle. The normals
    point away from ``middle`` (default: the middle of the points)."""
    rows, cols = points.shape[0], points.shape[1]
    du = np.gradient(points, axis=1)
    dv = np.gradient(points, axis=0) if rows > 1 else np.zeros_like(points)
    n = np.cross(du, dv)
    length = np.linalg.norm(n, axis=-1, keepdims=True)
    centre = points.reshape(-1, 3).mean(axis=0) if middle is None else middle
    out = points - centre
    out_len = np.linalg.norm(out, axis=-1, keepdims=True)
    n = np.where(length > 1e-9, n / np.maximum(length, 1e-9), out / np.maximum(out_len, 1e-9))
    flip = (n * out).sum(axis=-1, keepdims=True) < 0.0
    n = np.where(flip, -n, n)
    idx = np.arange(rows * cols).reshape(rows, cols)
    a, b, c, d = idx[:-1, :-1], idx[:-1, 1:], idx[1:, :-1], idx[1:, 1:]
    tris = np.concatenate([np.stack([a, b, d], -1).reshape(-1, 3), np.stack([a, d, c], -1).reshape(-1, 3)])
    return Surface(points.reshape(-1, 3), n.reshape(-1, 3), uv.reshape(-1, 2), tris, paint)


@dataclass(frozen=True)
class Ring:
    """A level ring of a loft: its height ``y``; its middle ``(l, z)``; its
    half-widths across (``rl``) and from front to back (``rz``). ``droop``:
    how much lower its front is (a brim that comes down in front); ``lift``:
    how much higher its sides are (a crown pinched from front to back).
    ``v``: the ``v`` its points paint with (default: their height)."""

    y: float
    l: float = 0.0
    z: float = 0.0
    rl: float = 1.0
    rz: float = 1.0
    droop: float = 0.0
    lift: float = 0.0
    v: Optional[float] = None


def loft(rings: Sequence[Ring], paint: Paint, cols: int = 48) -> Surface:
    """The surface through ``rings``, in order. A ring of no size closes it
    (a cap, or the point of a beard)."""
    u = np.linspace(-180.0, 180.0, cols + 1)
    ur = np.radians(u)
    pts, uv = [], []
    for r in rings:
        y = r.y + r.droop * np.maximum(0.0, np.cos(ur)) - r.lift * np.sin(ur) ** 2
        pts.append(np.stack([r.l + r.rl * np.sin(ur), y, r.z + r.rz * np.cos(ur)], -1))
        uv.append(np.stack([u, y if r.v is None else np.full_like(u, r.v)], -1))
    points = np.array(pts)
    middle = np.array([np.mean([r.l for r in rings]), np.mean([r.y for r in rings]), np.mean([r.z for r in rings])])
    return _grid(points, np.array(uv), paint, middle)


def ellipsoid(centre: Vec, radii: Vec, paint: Paint, rows: int = 18, cols: int = 40) -> Surface:
    cl, cy, cz = centre
    rl, ry, rz = radii
    rings = []
    for k in range(rows + 1):
        a = math.radians(-90.0 + 180.0 * k / rows)
        rings.append(Ring(cy + ry * math.sin(a), cl, cz, rl * math.cos(a), rz * math.cos(a)))
    s = loft(rings, paint, cols)
    s.normals = (s.verts - np.asarray(centre)) / np.asarray(radii) ** 2
    s.normals /= np.maximum(np.linalg.norm(s.normals, axis=-1, keepdims=True), 1e-9)
    return s


def on_ellipsoid(centre: Vec, radii: Vec, u: float, v: float, out: float = 0.0) -> Tuple[np.ndarray, np.ndarray]:
    """The point of an ellipsoid at the turn ``u`` and the height ``v``, moved
    ``out`` along its normal, and that normal."""
    c, r = np.asarray(centre, float), np.asarray(radii, float)
    k = math.sqrt(max(0.0, 1.0 - ((v - c[1]) / r[1]) ** 2))
    a = math.radians(u)
    p = np.array([c[0] + r[0] * k * math.sin(a), v, c[2] + r[2] * k * math.cos(a)])
    n = (p - c) / r ** 2
    n /= np.linalg.norm(n)
    return p + n * out, n


def limb(a: Vec, b: Vec, r0: float, r1: float, paint: Paint, rows: int = 10, cols: int = 24) -> Surface:
    """A limb from ``a`` to ``b``, ``r0`` thick at its root and ``r1`` at its
    end, with round ends."""
    a_, b_ = np.asarray(a, float), np.asarray(b, float)
    axis = b_ - a_
    length = float(np.linalg.norm(axis))
    w = axis / max(length, 1e-9)
    side = np.cross(w, [0.0, 1.0, 0.0])
    if np.linalg.norm(side) < 1e-6:
        side = np.cross(w, [0.0, 0.0, 1.0])
    side /= np.linalg.norm(side)
    up = np.cross(side, w)
    u = np.linspace(-180.0, 180.0, cols + 1)
    ur = np.radians(u)[None, :, None]
    # The ends are half spheres: a ring's place along the axis, its radius,
    # and its ``v``.
    cap = 5
    stations = [(-r0 * math.cos(math.radians(90.0 * k / cap)), r0 * math.sin(math.radians(90.0 * k / cap)), 0.0) for k in range(cap)]
    stations += [(length * t, r0 + (r1 - r0) * t, t) for t in np.linspace(0.0, 1.0, rows + 1)]
    stations += [(length + r1 * math.sin(math.radians(90.0 * k / cap)), r1 * math.cos(math.radians(90.0 * k / cap)), 1.0) for k in range(1, cap + 1)]
    along = np.array([s[0] for s in stations])[:, None, None]
    radius = np.array([s[1] for s in stations])[:, None, None]
    pts = a_ + w * along + radius * (np.cos(ur) * side + np.sin(ur) * up)
    uv = np.stack(np.broadcast_arrays(np.degrees(ur[..., 0]), np.array([s[2] for s in stations])[:, None]), -1)
    s = _grid(pts, uv, paint, (a_ + b_) / 2.0)
    # Normals of a capsule: from the nearest point of its axis.
    t = np.clip(((s.verts - a_) @ w) / max(length, 1e-9), 0.0, 1.0)
    n = s.verts - (a_ + np.outer(t, axis))
    s.normals = n / np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-9)
    return s


def two_bone(root: Vec, target: Vec, first: float, second: float, pole: Vec) -> Tuple[np.ndarray, np.ndarray]:
    """The middle joint and the end of a limb of two bones from ``root``
    toward ``target``, bent toward ``pole``."""
    r, t = np.asarray(root, float), np.asarray(target, float)
    d = t - r
    dist = float(np.linalg.norm(d))
    w = d / max(dist, 1e-9)
    span = max(abs(first - second) + 0.05, min(first + second - 0.05, dist))
    along = (first * first - second * second + span * span) / (2.0 * span)
    off = math.sqrt(max(0.0, first * first - along * along))
    p = np.asarray(pole, float)
    p = p - (p @ w) * w
    p /= max(float(np.linalg.norm(p)), 1e-9)
    return r + w * along + p * off, r + w * span


# ---- Parts -------------------------------------------------------------------


@dataclass
class Line:
    """A fine line on a part, through 3D points. ``fill``: it is a closed
    shape with this colour inside (a lens, a pupil)."""

    points: np.ndarray
    colour: Optional[RGBA]
    width: float = 0.6
    fill: Optional[RGBA] = None
    #: A point this far behind the surface in front of it still shows.
    slack: float = 0.8


def curve(points: Sequence[Vec], colour: Optional[RGBA], width: float = 0.6, *, fill: Optional[RGBA] = None, slack: float = 0.8) -> Line:
    return Line(np.asarray(points, float), colour, width, fill, slack)


def circle(centre: Sequence[float], normal: Sequence[float], radius: float, colour: Optional[RGBA], width: float = 0.6, *, fill: Optional[RGBA] = None,
           slack: float = 0.8, n: int = 20) -> Line:
    """A circle in 3D: its middle, the way it faces, its radius."""
    c, w = np.asarray(centre, float), np.asarray(normal, float)
    w = w / np.linalg.norm(w)
    a = np.cross(w, [0.0, 1.0, 0.0])
    if np.linalg.norm(a) < 1e-6:
        a = np.cross(w, [1.0, 0.0, 0.0])
    a /= np.linalg.norm(a)
    b = np.cross(w, a)
    t = np.linspace(0.0, math.tau, n + 1)[:, None]
    return Line(c + radius * (np.cos(t) * a + np.sin(t) * b), colour, width, fill, slack)


@dataclass
class Part:
    """What is drawn as one piece, with one outline: its surfaces, the fine
    lines on it, and how it is lit (as ``Kit.solid``). Only the pixels
    painted in ``base`` are lit; any other colour is detail on it."""

    name: str
    surfaces: List[Surface]
    lines: List[Line] = field(default_factory=list)
    base: RGBA = (128, 128, 128, 255)
    outline: float = 1.3
    rim: float = 0.3
    shade: float = 0.35
    shade_colour: Optional[RGBA] = None
    #: The point that says how near the part is. A part with ``dims`` is
    #: painted as a far limb when it is behind the trunk.
    anchor: Vec = (0.0, 0.0, 0.0)
    dims: bool = False


@dataclass
class Figure:
    """A person in the round: its parts in body space, and the frame of the
    character's sheet (``Person``) they are drawn in."""

    parts: List[Part]
    frame: Tuple[int, int]
    cx: float
    ground: float
    hip_up: float
    #: The trunk's middle: a ``dims`` part behind it is a far limb.
    trunk: Vec = (0.0, -20.0, 0.0)


# ---- Drawing -----------------------------------------------------------------


@dataclass
class _Buffers:
    depth: np.ndarray
    sid: np.ndarray
    u: np.ndarray
    v: np.ndarray
    lit: np.ndarray


def _rasterize(surfaces: Sequence[Surface], view: View, size: Tuple[int, int], to_canvas: Callable) -> _Buffers:
    """The nearest surface at each pixel: its depth, which surface, and its
    ``u``, ``v`` and ``lit`` there."""
    w, h = size
    depth = np.full((h, w), -np.inf, np.float32)
    sid = np.full((h, w), -1, np.int32)
    uu, vv, ll = (np.zeros((h, w), np.float32) for _ in range(3))
    ex, ey, ed = view.basis()
    light = view.key_light()
    for k, s in enumerate(surfaces):
        sx, sy = to_canvas(s.verts @ ex, s.verts @ ey)
        dz = s.verts @ ed
        lit = s.normals @ light
        for i0, i1, i2 in s.tris:
            x0, y0, x1, y1, x2, y2 = sx[i0], sy[i0], sx[i1], sy[i1], sx[i2], sy[i2]
            area = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
            if abs(area) < 1e-6:
                continue
            xa, xb = max(0, int(math.floor(min(x0, x1, x2)))), min(w - 1, int(math.ceil(max(x0, x1, x2))))
            ya, yb = max(0, int(math.floor(min(y0, y1, y2)))), min(h - 1, int(math.ceil(max(y0, y1, y2))))
            if xa > xb or ya > yb:
                continue
            X, Y = np.meshgrid(np.arange(xa, xb + 1) + 0.5, np.arange(ya, yb + 1) + 0.5)
            b0 = ((x1 - X) * (y2 - Y) - (x2 - X) * (y1 - Y)) / area
            b1 = ((x2 - X) * (y0 - Y) - (x0 - X) * (y2 - Y)) / area
            b2 = 1.0 - b0 - b1
            inside = (b0 >= -1e-4) & (b1 >= -1e-4) & (b2 >= -1e-4)
            if not inside.any():
                continue
            z = b0 * dz[i0] + b1 * dz[i1] + b2 * dz[i2]
            cur = depth[ya:yb + 1, xa:xb + 1]
            win = inside & (z > cur)
            if not win.any():
                continue
            cur[win] = z[win]
            sid[ya:yb + 1, xa:xb + 1][win] = k
            for buf, vals in ((uu, s.uv[:, 0]), (vv, s.uv[:, 1]), (ll, lit)):
                buf[ya:yb + 1, xa:xb + 1][win] = (b0 * vals[i0] + b1 * vals[i1] + b2 * vals[i2])[win]
    return _Buffers(depth, sid, uu, vv, ll)


def _draw_part(K: Kit, part: Part, view: View, to_canvas: Callable, far: bool) -> Optional[Tuple[np.ndarray, np.ndarray]]:
    """One part as a layer of the canvas: its colours (with its outline) and
    the depth of each of its pixels."""
    size = K.canvas
    buf = _rasterize(part.surfaces, view, size, to_canvas)
    mask = np.isfinite(buf.depth)
    if not mask.any():
        return None
    body = np.zeros((size[1], size[0], 4), np.uint8)
    for k, s in enumerate(part.surfaces):
        sel = buf.sid == k
        if sel.any():
            body[sel] = s.paint(buf.u[sel], buf.v[sel], buf.lit[sel], far)
    mask_img = Image.fromarray(np.where(mask, 255, 0).astype(np.uint8), "L")
    # As ``Kit.solid``: the part's fill (its ``base`` colour) is lit, and
    # what is painted on it (a beard, a waistcoat, a band) is not.
    lit_img = Image.fromarray(body, "RGBA")
    K.light(mask_img, lit_img, part.base, rim=part.rim, shade=part.shade, shade_colour=part.shade_colour)
    is_fill = (body == np.asarray(part.base, np.uint8)).all(axis=-1)
    body_img = Image.fromarray(np.where(is_fill[..., None], np.asarray(lit_img), body), "RGBA")
    if part.lines:
        layer = Image.new("RGBA", size, (0, 0, 0, 0))
        _draw_lines(K, ImageDraw.Draw(layer), part.lines, view, to_canvas, buf.depth)
        body_img.alpha_composite(layer)
    body_img.putalpha(mask_img)
    reach = 2 * K.s(part.outline) + 1 if part.outline > 0.0 else 1
    grown = mask_img.filter(ImageFilter.MaxFilter(reach)) if part.outline > 0.0 else mask_img
    out = Image.new("RGBA", size, K.ink)
    out.putalpha(grown)
    out.alpha_composite(body_img)
    near = np.where(mask, buf.depth, -1e9).astype(np.float32)
    depth = np.where(mask, near, ndimage.grey_dilation(near, size=(reach, reach)))
    return np.asarray(out), depth


def _draw_lines(K: Kit, d: ImageDraw.ImageDraw, lines: Sequence[Line], view: View, to_canvas: Callable, depth: np.ndarray) -> None:
    ex, ey, ed = view.basis()
    h, w = depth.shape
    for line in lines:
        pts = line.points
        # Fine steps, so a line is hidden where it goes behind the surface.
        steps = [pts[0]]
        for a, b in zip(pts[:-1], pts[1:]):
            n = max(1, int(math.ceil(np.linalg.norm(b - a) / 0.4)))
            steps.extend(a + (b - a) * (k / n) for k in range(1, n + 1))
        p = np.array(steps)
        sx, sy = to_canvas(p @ ex, p @ ey)
        dz = p @ ed
        xi, yi = np.clip(sx.astype(int), 0, w - 1), np.clip(sy.astype(int), 0, h - 1)
        seen = (dz + line.slack >= depth[yi, xi]) & np.isfinite(depth[yi, xi])
        if line.fill is not None and seen.mean() > 0.5:
            d.polygon([(float(x), float(y)) for x, y in zip(sx, sy)], fill=tuple(line.fill))
        if line.colour is None:
            continue
        width = max(1, K.s(line.width))
        run: List[Tuple[float, float]] = []
        for x, y, ok in zip(sx, sy, seen):
            if ok:
                run.append((float(x), float(y)))
                continue
            if len(run) > 1:
                d.line(run, fill=tuple(line.colour), width=width, joint="curve")
            run = []
        if len(run) > 1:
            d.line(run, fill=tuple(line.colour), width=width, joint="curve")


def draw(K: Kit, figure: Figure, view: View) -> Image.Image:
    """``figure`` in ``view``, as a frame of its sheet: standing on its
    ground line, its hips over ``cx``."""
    ex, ey, ed = view.basis()
    lift = figure.hip_up * math.cos(math.radians(view.pitch))
    scale = K.scale

    def to_canvas(x: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        return (figure.cx + x) * scale, (figure.ground - lift + y) * scale

    trunk = float(np.asarray(figure.trunk) @ ed)
    w, h = K.canvas
    best = np.full((h, w), -np.inf, np.float32)
    out = np.zeros((h, w, 4), np.uint8)
    for part in figure.parts:
        far = part.dims and float(np.asarray(part.anchor) @ ed) < trunk - 1.5
        layer = _draw_part(K, part, view, to_canvas, far)
        if layer is None:
            continue
        rgba, depth = layer
        win = (rgba[..., 3] > 0) & (depth > best)
        out[win] = rgba[win]
        best[win] = depth[win]
    return K.downsample(Image.fromarray(out, "RGBA"))


# ---- A turnaround ------------------------------------------------------------


def turnaround(K: Kit, figure: Figure, path: Path, *, title: str = "", own: Optional[Dict[str, Image.Image]] = None, zoom: int = 3,
               views: Sequence[View] = VIEWS) -> Path:
    """Every view of ``figure`` side by side. ``own``: the character's own
    art for some views (``view key -> frame``), drawn in a row under the
    views from 3D, so the two can be compared."""
    frames = [draw(K, figure, v) for v in views]
    rows = [frames]
    if own:
        blank = Image.new("RGBA", frames[0].size, (0, 0, 0, 0))
        rows.append([own.get(v.key, blank) for v in views])
    box = None
    for row in rows:
        for f in row:
            b = f.getchannel("A").getbbox()
            if b is not None:
                box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
    assert box is not None
    pad = 4
    box = (max(0, box[0] - pad), max(0, box[1] - pad), box[2] + pad, box[3] + pad)
    cw, ch = (box[2] - box[0]) * zoom, (box[3] - box[1]) * zoom
    label_h, title_h = 18, 26 if title else 0
    sheet = Image.new("RGBA", (cw * len(views), title_h + (ch + label_h) * len(rows)), (214, 218, 226, 255))
    d = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 13)
        bold = ImageFont.truetype("DejaVuSans-Bold.ttf", 15)
    except OSError:
        font = bold = ImageFont.load_default()
    if title:
        d.text((8, 5), title, fill=(30, 30, 40), font=bold)
    names = ["from 3D", "own art"]
    for r, row in enumerate(rows):
        y = title_h + r * (ch + label_h)
        for i, (v, f) in enumerate(zip(views, row)):
            if f.getchannel("A").getbbox() is None:
                continue
            cell = f.crop(box).resize((cw, ch), Image.Resampling.NEAREST)
            sheet.alpha_composite(cell, (i * cw, y))
            d.text((i * cw + 6, y + ch + 1), f"{v.label} - {names[r]}", fill=(30, 30, 40), font=font)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(path)
    return path


__all__ = ["Figure", "Line", "Paint", "Part", "Ring", "Surface", "VIEWS", "VIEW_BY_KEY", "View", "arc", "circle", "curve", "draw", "ellipsoid", "fill",
           "flat", "limb", "loft", "on_ellipsoid", "put", "turnaround", "two_bone"]
