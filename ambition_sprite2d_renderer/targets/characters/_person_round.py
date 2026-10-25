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

from ._ai_era_kit import Kit, RGBA

Vec = Tuple[float, float, float]
#: ``paint(u, v, lit, far)``: the colours (an ``(n, 4)`` array) of ``n``
#: points of a surface. ``u`` and ``v`` are where the points are on it (see
#: ``Surface``); ``lit`` is how much each faces the key light (-1 to 1);
#: ``far`` is true when the part is a far limb in this view.
Paint = Callable[[np.ndarray, np.ndarray, np.ndarray, bool], np.ndarray]

#: How far the camera looks down, in degrees. The cast's views are level; a
#: part that the cast draws as if seen from a little above (a brim) says so
#: with a cheat (``from_above``).
PITCH = 0.0


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


# ---- Cheats ------------------------------------------------------------------
#
# The cast's views are drawn, not projected, and that is their character: in
# the three-quarter view the face is turned further than the skull (the nose,
# the beard and the far eye go out toward the profile), and a brim is an oval
# from the front. A cheat gives a surface its own view, and the surface is
# placed so that its ``pivot`` is where the true view puts it.

Cheat = Callable[[View], View]


def profile_push(degrees: float) -> Cheat:
    """Turn a surface ``degrees`` further toward the profile than the view
    is: the most at three quarters, none at the front, the side or the back."""

    def cheat(view: View) -> View:
        return replace(view, yaw=view.yaw + degrees * math.sin(math.radians(2.0 * view.yaw)))

    return cheat


def from_above(pitch: float) -> Cheat:
    """See a surface from ``pitch`` degrees above, whatever the view's tilt."""

    def cheat(view: View) -> View:
        return replace(view, pitch=pitch)

    return cheat


def both(*cheats: Cheat) -> Cheat:
    def cheat(view: View) -> View:
        for c in cheats:
            view = c(view)
        return view

    return cheat


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
    #: How this surface is cheated (``Cheat``), about ``pivot``.
    cheat: Optional[Callable[[View], View]] = None
    pivot: Vec = (0.0, 0.0, 0.0)

    def moved(self, by: Vec) -> "Surface":
        return replace(self, verts=self.verts + np.asarray(by, float), pivot=tuple(np.asarray(self.pivot, float) + np.asarray(by, float)))

    def scaled(self, k: float) -> "Surface":
        """``k`` times as large, about body-space zero."""
        return replace(self, verts=self.verts * k, pivot=tuple(np.asarray(self.pivot, float) * k))

    def cheated(self, cheat: Callable[[View], View], pivot: Vec) -> "Surface":
        return replace(self, cheat=cheat, pivot=pivot)


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


def lift(x: float, l: float, yaw: float = 45.0) -> float:
    """How far forward (``z``) a point is that a level view at ``yaw`` draws
    ``x`` across from the middle, when it is ``l`` to the side (from a front
    view). Two views of a cast member give a point in 3D this way."""
    t = math.radians(yaw)
    return (x - l * math.cos(t)) / math.sin(t)


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
    cheat: Optional[Callable[[View], View]] = None
    pivot: Vec = (0.0, 0.0, 0.0)

    def moved(self, by: Vec) -> "Line":
        return replace(self, points=self.points + np.asarray(by, float), pivot=tuple(np.asarray(self.pivot, float) + np.asarray(by, float)))

    def scaled(self, k: float) -> "Line":
        return replace(self, points=self.points * k, pivot=tuple(np.asarray(self.pivot, float) * k))

    def cheated(self, cheat: Callable[[View], View], pivot: Vec) -> "Line":
        return replace(self, cheat=cheat, pivot=pivot)


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
    #: The views it is drawn in (default: all); another piece draws the rest.
    when: Optional[Callable[[View], bool]] = None


@dataclass
class Sprite:
    """A piece drawn in 2D, as the cast draws it, at a place 3D gives it:
    ``draw(view, far)`` returns the piece (a ``Kit`` part, outline and all),
    its turn in degrees, and whether it is mirrored; it is placed at
    ``anchor`` and is as near as ``anchor`` is. The 3D says where a thing is
    and how it is turned; the drawing is the cast's."""

    name: str
    anchor: Vec
    draw: Callable[[View, bool], Optional[Tuple[object, float, bool]]]
    dims: bool = False
    when: Optional[Callable[[View], bool]] = None
    #: How far in front of its anchor the piece counts as being (a head is
    #: drawn over the collar under it, as the cast paints it).
    lead: float = 0.0


def near_turn(*turns: float, within: float = 10.0) -> Callable[[View], bool]:
    """``when``: the views that face the person within ``within`` degrees of
    one of ``turns`` (``facing``)."""

    def when(view: View) -> bool:
        return any(abs((facing(view) - t + 180.0) % 360.0 - 180.0) <= within for t in turns)

    return when


def composed(K: Kit, layers: Sequence[Tuple[object, str]], degrees: float = 0.0) -> Optional[object]:
    """Pieces of the cast placed one over another at ``home``, as one piece:
    a head and what is on it (``Person.head_layers``)."""
    canvas = K.scratch()
    for piece, name in layers:
        K.place(canvas, piece, K.home, name, degrees)  # type: ignore[arg-type]
    return K._cut(canvas)


@dataclass
class Drawn:
    """A piece the cast's own code draws on a frame at points that 3D gives
    it: ``draw(view, far, at)`` paints a frame (``Kit.new_frame``) and returns
    it; ``at(p)`` is where a body-space point is in the frame. A limb is drawn
    so: its bones from joint to joint, its hand at its wrist, as the cast
    draws them."""

    name: str
    anchor: Vec
    draw: Callable[[View, bool, Callable[[Sequence[float]], Tuple[float, float]]], Optional[Image.Image]]
    dims: bool = False
    when: Optional[Callable[[View], bool]] = None
    lead: float = 0.0


def place_bones(K: Kit, img: Image.Image, name: str, bones: Sequence[Tuple[Tuple[float, float], Tuple[float, float], Callable[[bool, float], object]]]) -> None:
    """A limb as the cast paints it: every bone's outline, and then every
    bone, so a joint has no line through it. A bone is ``(a, b, make)``, frame
    points and ``make(edge, length)``, the piece along +x from ``a``."""
    for edge in (True, False):
        for k, (a, b, make) in enumerate(bones):
            K.place(img, make(edge, math.dist(a, b)), a, f"{name}_{k}{'_edge' if edge else ''}", _angle(a, b))  # type: ignore[arg-type]


def _angle(a: Sequence[float], b: Sequence[float]) -> float:
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


def facing(view: View, heading: float = 0.0) -> float:
    """The turn of a thing that points ``heading`` (degrees, 0 forward, 90 to
    the person's left), as this view sees it: 0 toward the viewer, 90 to the
    right of the picture, 180 away, -90 to the left."""
    return (view.yaw - heading + 180.0) % 360.0 - 180.0


@dataclass
class Figure:
    """A person in the round: its parts (a ``Part`` of 3D surfaces, or a
    ``Sprite``) in body space, and the frame of the character's sheet
    (``Person``) they are drawn in."""

    parts: List[object]
    frame: Tuple[int, int]
    cx: float
    ground: float
    hip_up: float
    #: The trunk's middle: a ``dims`` part behind it is a far limb.
    trunk: Vec = (0.0, -20.0, 0.0)


# ---- A head in 3D ------------------------------------------------------------


@dataclass
class Glasses:
    """``round`` or ``square`` lenses ``size`` (half the width, half the
    height) in front of the eyes, their rims ``weight`` thick, the top of a
    rim ``top`` heavier (a heavy frame), and their arms back to the ears."""

    shape: str
    size: Tuple[float, float]
    frame: RGBA
    lens: Optional[RGBA] = None
    weight: float = 0.8
    top: float = 0.0


@dataclass
class Head3D:
    """A head from its middle, for the views a character has no head drawn
    for. Each part is an ellipsoid ``(middle, radii)``; ``ear`` is the right
    one (the left is its mirror); ``eye`` is the turn and the height of the
    right eye on the skull. ``hair(u, v)`` says where the skull is hair;
    ``volumes`` stand off it in the hair's colour. A ``beard`` is a loft of
    rings; ``moustache`` an ellipsoid; ``mouth`` ``(y, z, half width,
    colour)``. ``lines`` are the character's own (in head space)."""

    skin: RGBA
    shade: RGBA
    deep: RGBA
    skull: Tuple[Vec, Vec]
    jaw: Tuple[Vec, Vec]
    nose: Tuple[Vec, Vec]
    ear: Tuple[Vec, Vec]
    eye: Tuple[float, float]
    eye_size: float = 1.0
    ink: RGBA = (28, 24, 32, 255)
    lid: Optional[RGBA] = None
    #: ``(colour, under, height, weight)``: the brows over the eyes.
    brow: Optional[Tuple[RGBA, Optional[RGBA], float, float]] = None
    hair: Optional[Callable[[np.ndarray, np.ndarray], np.ndarray]] = None
    hair_colour: RGBA = (240, 240, 236, 255)
    hair_shade: Optional[RGBA] = None
    volumes: Sequence[Tuple[Vec, Vec]] = ()
    beard: Optional[Sequence[Ring]] = None
    moustache: Optional[Tuple[Vec, Vec]] = None
    mouth: Optional[Tuple[float, float, float, RGBA]] = None
    glasses: Optional[Glasses] = None
    lines: Sequence[Line] = ()
    #: Where the far side of the face is in shade (``lit`` under it).
    shade_at: float = -0.45


def head_part(h: Head3D, at: Vec, name: str = "head") -> Part:
    """``h`` as a part, its middle at ``at``."""
    skin_shade = _mix(h.skin, h.shade, 0.7)
    flat_skin = flat(h.skin, shade=skin_shade, at=h.shade_at)
    hair_shade = h.hair_shade or h.hair_colour

    def scalp(u, v, lit, far):
        out = fill(h.skin, len(u))
        put(out, lit < h.shade_at, skin_shade)
        if h.hair is not None:
            put(out, h.hair(u, v), h.hair_colour)
        return out

    def beard(u, v, lit, far):
        out = fill(h.hair_colour, len(u))
        put(out, lit < -0.6, hair_shade)
        if h.mouth is not None:
            y, _z, half, colour = h.mouth
            put(out, (np.abs(v - y) < 0.35) & (np.abs(arc(u, 5.6)) < half), colour)
        return out

    skull_c, skull_r = h.skull
    surfaces = [ellipsoid(skull_c, skull_r, scalp), ellipsoid(h.jaw[0], h.jaw[1], flat_skin), ellipsoid(h.nose[0], h.nose[1], flat_skin)]
    surfaces += [ellipsoid(c, r, flat(h.hair_colour, shade=hair_shade, at=-0.6)) for c, r in h.volumes]
    (el, ey_, ez), er = h.ear
    for side in (-1.0, 1.0):
        surfaces.append(ellipsoid((side * abs(el), ey_, ez), er, flat(h.skin, shade=h.shade)))
    if h.beard is not None:
        surfaces.append(loft(h.beard, beard))
    if h.moustache is not None:
        surfaces.append(ellipsoid(h.moustache[0], h.moustache[1], flat(h.hair_colour, shade=hair_shade, at=-0.4)))
    lines: List[Line] = []
    eu, ev = h.eye
    for side in (-1.0, 1.0):
        eye, n = on_ellipsoid(skull_c, skull_r, side * eu, ev, 0.1)
        g = h.glasses
        lens = eye + np.array([0.0, 0.0, 1.0])
        face = np.array([0.25 * side, 0.0, 1.0])
        if g is not None and g.lens is not None:
            lines.append(_lens(lens, face, g, None, fill_colour=g.lens))
        lines.append(circle(eye + n * 0.4, n, h.eye_size, None, fill=h.ink, slack=1.6))
        if h.lid is not None:
            lid = [on_ellipsoid(skull_c, skull_r, side * eu + du, ev - 1.6 + 0.02 * du * du, 0.1)[0] for du in (-14.0, -6.0, 0.0, 6.0, 14.0)]
            lines.append(curve(lid, h.lid, 0.5))
        if h.brow is not None:
            colour, under, by, weight = h.brow
            brow = [on_ellipsoid(skull_c, skull_r, side * u, by - 0.4 * math.sin(math.radians((u - 10.0) * 6.0)), 0.3)[0] for u in (10.0, 20.0, 30.0, 40.0)]
            if under is not None:
                lines.append(curve(brow, under, weight + 0.6))
            lines.append(curve(brow, colour, weight))
        if g is not None:
            lines.append(_lens(lens, face, g, g.frame))
            ear_top = (side * (abs(el) - 0.3), ey_ - 1.6, ez)
            lines.append(curve([lens + [side * g.size[0], -0.2, -0.4], (side * (skull_r[0] - 0.4), ev - 0.3, lens[2] - 4.0), ear_top], g.frame, 0.6))
        ear = np.array([side * (abs(el) + er[0]), ey_, ez])
        lines.append(circle(ear, (side, 0.0, 0.0), min(er[1], er[2]) * 0.85, (34, 22, 48, 255), 0.6, slack=0.6))
        lines.append(curve([ear + [0.0, -1.4, 0.6], ear + [0.0, 0.0, -0.2], ear + [0.0, 1.4, 0.4]], h.deep, 0.45, slack=0.6))
    if h.glasses is not None:
        left = on_ellipsoid(skull_c, skull_r, -eu, ev)[0] + [0.0, 0.0, 1.0]
        right = on_ellipsoid(skull_c, skull_r, eu, ev)[0] + [0.0, 0.0, 1.0]
        bridge_z = h.nose[0][2] - h.nose[1][2] * 0.2
        lines.append(curve([left + [h.glasses.size[0], -0.2, 0.2], (0.0, ev - 0.4, bridge_z), right + [-h.glasses.size[0], -0.2, 0.2]], h.glasses.frame, 0.6))
    tip = np.asarray(h.nose[0]) + [0.0, h.nose[1][1] * 0.8, h.nose[1][2] * 0.5]
    lines.append(curve([tip + [-1.2, -0.5, -0.6], tip + [0.0, 0.0, 0.2], tip + [1.2, -0.5, -0.6]], h.deep, 0.6))
    lines += list(h.lines)
    return Part(name, [s.moved(at) for s in surfaces], [ln.moved(at) for ln in lines], base=h.skin, shade_colour=h.deep, anchor=at)


def _lens(centre: np.ndarray, face: np.ndarray, g: Glasses, colour: Optional[RGBA], fill_colour: Optional[RGBA] = None) -> Line:
    if g.shape == "round":
        return circle(centre, face, g.size[0], colour, g.weight, fill=fill_colour)
    w = face / np.linalg.norm(face)
    a = np.cross([0.0, 1.0, 0.0], w)
    a /= np.linalg.norm(a)
    b = np.array([0.0, 1.0, 0.0])
    rx, ry = g.size
    corners = [centre + a * x + b * y for x, y in ((-rx, -ry), (rx, -ry), (rx, ry), (-rx, ry), (-rx, -ry))]
    return Line(np.array(corners), colour, g.weight + g.top, fill_colour)


def _mix(a: RGBA, b: RGBA, t: float) -> RGBA:
    return tuple(int(round(a[i] * (1.0 - t) + b[i] * t)) for i in range(4))  # type: ignore[return-value]


# ---- A person of _person_rig in the round ------------------------------------
#
# A ``Person`` has its pieces drawn by its own makers: the dress of each bone
# (``upper_arm``, ``forearm``, ``thigh``, ``shin``), its hands, its neck and
# shoes, its head and trunk in the views it has them. These place them at
# joints in 3D.


def _between(a: Tuple[float, float], b: Tuple[float, float], t: float) -> Tuple[float, float]:
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def _seg_bones(K: Kit, tag: str, a: Tuple[float, float], b: Tuple[float, float], segs) -> list:
    """The bones of a limb dressed in ``segs`` (``_person_rig.Seg``) from
    frame point ``a`` to ``b``, as ``Person.limb`` places them."""
    from ._person_rig import bone

    out = []
    for t0, t1, w0, w1, colour in segs:
        out.append((_between(a, b, t0), _between(a, b, t1),
                    lambda edge, length, w0=w0, w1=w1, colour=colour: bone(K, tag, length, w0, w1, colour, edge)))
    return out


def person_arm(person, name: str, shoulder: Sequence[float], elbow: Sequence[float], wrist: Sequence[float], hand: str, *,
               lead: float = 3.0) -> Drawn:
    """An arm of ``person`` from 3D joints: its sleeve on its two bones and
    its hand (``hand``: soft, flat, fist, point, open) at its wrist, as near
    as the wrist."""
    K = person.K

    def draw(view: View, far: bool, at) -> Image.Image:
        s, e, w = at(shoulder), at(elbow), at(wrist)
        img = K.new_frame()
        near = not far
        place_bones(K, img, name, _seg_bones(K, name, s, e, person.upper_arm(near)) + _seg_bones(K, name, e, w, person.forearm(near)))
        K.place(img, person.hand(hand, near), w, f"{name}_hand", _angle(e, w))
        return img

    return Drawn(name, tuple(wrist), draw, dims=True, lead=lead)


def person_leg(person, name: str, hip: Sequence[float], knee: Sequence[float], ankle: Sequence[float], *, lead: float = -12.0) -> Drawn:
    """A leg of ``person`` from 3D joints, in what its bones are dressed in.
    It goes under the trunk (``lead``), as the cast paints a leg that does not
    kick."""
    K = person.K

    def draw(view: View, far: bool, at) -> Image.Image:
        h, k, a = at(hip), at(knee), at(ankle)
        img = K.new_frame()
        near = not far
        place_bones(K, img, name, _seg_bones(K, name, h, k, person.thigh(near)) + _seg_bones(K, name, k, a, person.shin(near)))
        return img

    return Drawn(name, tuple(knee), draw, dims=True, lead=lead)


def person_neck(person, base: Sequence[float], top: Sequence[float]) -> Drawn:
    """``person``'s neck from its base to where it goes into the head."""
    K = person.K

    def draw(view: View, far: bool, at) -> Optional[Image.Image]:
        if person.neck is None:
            return None
        a, b = at(base), at(top)
        img = K.new_frame()
        K.place(img, person.neck(float(round(math.dist(a, b)))), a, "neck", _angle(a, b))
        return img

    return Drawn("neck", tuple(base), draw)


def shoes(name: str, ankle: Sequence[float], side: Callable[[bool], object], front: Callable[[], object], back: Callable[[], object]) -> Sprite:
    """A shoe in every view: ``front()`` seen from the toe, ``back()`` from
    the heel, ``side(near)`` from the side, its toe to the side the foot
    points (mirrored for the left)."""

    def draw(view: View, far: bool):
        turn = facing(view)
        toward = math.cos(math.radians(turn))
        if toward > 0.85:
            return front(), 0.0, False
        if toward < -0.85:
            return back(), 0.0, False
        return side(not far), 0.0, turn < 0.0

    return Sprite(name, tuple(ankle), draw, dims=True, lead=3.0)


def own_art(name: str, anchor: Sequence[float], three_quarter: Optional[Callable[[], object]], front: Optional[Callable[[], object]] = None, *,
            degrees: float = 0.0, lead: float = 0.0, mirror: bool = True) -> Sprite:
    """A piece of a character's own art in the views it is drawn for: its
    three-quarter view, its mirror for the left (``mirror``: only a piece that
    is the same on both sides; a pocket on one side is not), and its front
    view if it has one. Another piece draws the other views
    (``not_in(sprite.when)``)."""

    def draw(view: View, far: bool):
        turn = facing(view)
        if abs(turn) <= 10.0:
            return (front() if front is not None else None), 0.0, False
        return three_quarter(), degrees, turn < 0.0  # type: ignore[misc]

    return Sprite(name, tuple(anchor), draw, when=own_turns(front is not None, mirror), lead=lead)


def own_turns(front: bool, mirror: bool = True) -> Callable[[View], bool]:
    """The views a character's own art is drawn for (``own_art``)."""
    return near_turn(*((45.0,) + ((-45.0,) if mirror else ()) + ((0.0,) if front else ())))


def not_in(when: Callable[[View], bool]) -> Callable[[View], bool]:
    return lambda view: not when(view)


# ---- Drawing -----------------------------------------------------------------


def _project(points: np.ndarray, view: View, cheat: Optional[Callable[[View], View]], pivot: Vec) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Screen x, screen y and depth of ``points`` in ``view``; a cheated
    thing is seen in its own view, with its pivot where ``view`` puts it."""
    ex, ey, ed = view.basis()
    if cheat is None:
        return points @ ex, points @ ey, points @ ed
    cx, cy, cd = cheat(view).basis()
    q = np.asarray(pivot, float)
    p = points - q
    return p @ cx + q @ ex, p @ cy + q @ ey, p @ cd + q @ ed


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
    for k, s in enumerate(surfaces):
        x, y, dz = _project(s.verts, view, s.cheat, s.pivot)
        sx, sy = to_canvas(x, y)
        lit = s.normals @ (view if s.cheat is None else s.cheat(view)).key_light()
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
    grown_depth = np.asarray(Image.fromarray(near, "F").filter(ImageFilter.MaxFilter(reach)))
    depth = np.where(mask, near, grown_depth)
    return np.asarray(out), depth


def _draw_sprite(K: Kit, sprite: Sprite, view: View, to_canvas: Callable, far: bool) -> Optional[Tuple[np.ndarray, np.ndarray]]:
    made = sprite.draw(view, far)
    if made is None or made[0] is None:
        return None
    piece, degrees, mirrored = made
    if mirrored:
        img, (ax, ay) = piece  # type: ignore[misc]
        piece = (img.transpose(Image.Transpose.FLIP_LEFT_RIGHT), (img.width - ax, ay))
        degrees = -degrees
    a = np.asarray(sprite.anchor, float)[None, :]
    x, y, dz = _project(a, view, None, (0.0, 0.0, 0.0))
    sx, sy = to_canvas(x, y)
    img = K.new_frame()
    K.place(img, piece, (float(sx[0]) / K.scale, float(sy[0]) / K.scale), sprite.name, degrees)
    rgba = np.asarray(img)
    return rgba, np.where(rgba[..., 3] > 0, float(dz[0]) + sprite.lead, -np.inf).astype(np.float32)


def _draw_lines(K: Kit, d: ImageDraw.ImageDraw, lines: Sequence[Line], view: View, to_canvas: Callable, depth: np.ndarray) -> None:
    h, w = depth.shape
    for line in lines:
        pts = line.points
        # Fine steps, so a line is hidden where it goes behind the surface.
        steps = [pts[0]]
        for a, b in zip(pts[:-1], pts[1:]):
            n = max(1, int(math.ceil(np.linalg.norm(b - a) / 0.4)))
            steps.extend(a + (b - a) * (k / n) for k in range(1, n + 1))
        x, y, dz = _project(np.array(steps), view, line.cheat, line.pivot)
        sx, sy = to_canvas(x, y)
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
    def at(p: Sequence[float]) -> Tuple[float, float]:
        q = np.asarray(p, float)
        return (figure.cx + float(q @ ex), figure.ground - lift + float(q @ ey))

    for part in figure.parts:
        if part.when is not None and not part.when(view):
            continue
        far = part.dims and float(np.asarray(part.anchor) @ ed) < trunk - 1.5
        if isinstance(part, Drawn):
            img = part.draw(view, far, at)
            if img is None:
                continue
            rgba = np.asarray(img)
            layer = rgba, np.where(rgba[..., 3] > 0, float(np.asarray(part.anchor) @ ed) + part.lead, -np.inf).astype(np.float32)
        elif isinstance(part, Sprite):
            layer = _draw_sprite(K, part, view, to_canvas, far)
        else:
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


__all__ = ["not_in", "own_art", "own_turns", "person_arm", "person_leg", "person_neck", "shoes", "Drawn", "Glasses", "Head3D", "head_part", "place_bones", "composed", "near_turn", "lift", "Sprite", "facing", "Cheat", "both", "from_above", "profile_push", "Figure", "Line", "Paint", "Part", "Ring", "Surface", "VIEWS", "VIEW_BY_KEY", "View", "arc", "circle", "curve", "draw", "ellipsoid", "fill",
           "flat", "limb", "loft", "on_ellipsoid", "put", "turnaround", "two_bone"]
