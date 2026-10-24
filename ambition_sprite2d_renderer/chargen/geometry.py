"""The 3D primitives of the character generator and how a view sees them.

A character is built in centimetres in its own body frame:

* ``l``: the character's LEFT (positive), so its right side is ``l < 0``;
* ``y``: DOWN, with the ground at ``y = 0`` (the top of the head is negative);
* ``z``: FORWARD, out of the chest.

A :class:`View` is an orthographic camera turned about the vertical axis by a
yaw and tilted down a little (``pitch``). Yaw 0 is the front, 90 is the side
(the character faces screen-right and shows its RIGHT side), 180 is the back.
Every view of a character projects the same 3D primitives, so the views agree.

The primitives:

* :class:`Loft`: a body of horizontal rings (torso, head, neck, skirt, hair).
  Its silhouette in a view is the run of each ring's visible arc; a
  *coverage margin* ``m(alpha, y)`` (positive where covered) cuts a region out
  of the surface (hair, a V-neck, an open coat), and the cut is interpolated
  between samples, so an edge is smooth.
* capsules (limbs) and convex hulls of 3D points (hands, feet, ears, a brim).

Regions are returned as polygons in screen centimetres (``x`` right, ``y``
down). Several polygons of one region are drawn as one outlined shape: every
polygon's ink first, then every fill (see ``svgout``).
"""

from __future__ import annotations

import bisect
import math
from dataclasses import dataclass, field
from typing import Callable, Iterable, List, Optional, Sequence, Tuple

Vec3 = Tuple[float, float, float]
Point = Tuple[float, float]
#: alpha (degrees, 0 = forward, 90 = the character's left), y -> centimetres.
Bump = Callable[[float, float], float]
#: alpha, y -> positive where the surface is covered.
Margin = Callable[[float, float], float]

#: Samples round a ring. 5 degrees: a nose of 12 degrees still has 3 samples.
N_ALPHA = 72


@dataclass(frozen=True)
class View:
    """An orthographic camera: ``yaw`` about the vertical axis, ``pitch`` down."""

    key: str
    yaw: float
    label: str
    pitch: float = 6.0
    s: float = field(init=False, repr=False, compare=False)
    c: float = field(init=False, repr=False, compare=False)
    sp: float = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "s", math.sin(math.radians(self.yaw)))
        object.__setattr__(self, "c", math.cos(math.radians(self.yaw)))
        object.__setattr__(self, "sp", math.sin(math.radians(self.pitch)))

    def depth(self, p: Vec3) -> float:
        """How far ``p`` is toward the camera."""
        return p[2] * self.c - p[0] * self.s

    def project(self, p: Vec3) -> Point:
        l, y, z = p
        return (l * self.c + z * self.s, y + (z * self.c - l * self.s) * self.sp)

    def facing(self, alpha: float) -> float:
        """The cosine between a surface direction ``alpha`` and the camera."""
        return math.cos(math.radians(alpha + self.yaw))


#: The five views every character is drawn in, in turnaround order. A left
#: view is the mirror of its right twin.
VIEWS: Tuple[View, ...] = (
    View("front", 0.0, "Front"),
    View("front_3q", 45.0, "Front Three Quarter"),
    View("side", 90.0, "Side"),
    View("back_3q", 135.0, "Back Three Quarter"),
    View("back", 180.0, "Back"),
)
VIEW_BY_KEY = {v.key: v for v in VIEWS}


# ---- small vector helpers -----------------------------------------------------


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def lerp2(a: Point, b: Point, t: float) -> Point:
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def add3(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def sub3(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def scale3(a: Vec3, k: float) -> Vec3:
    return (a[0] * k, a[1] * k, a[2] * k)


def norm3(a: Vec3) -> Vec3:
    n = math.sqrt(a[0] ** 2 + a[1] ** 2 + a[2] ** 2) or 1.0
    return (a[0] / n, a[1] / n, a[2] / n)


def cross3(a: Vec3, b: Vec3) -> Vec3:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def gauss(x: float, mu: float, sigma: float) -> float:
    return math.exp(-(((x - mu) / sigma) ** 2))


def smoothstep(e0: float, e1: float, x: float) -> float:
    if e0 == e1:
        return 0.0 if x < e0 else 1.0
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3.0 - 2.0 * t)


def wrap180(a: float) -> float:
    """``a`` in degrees, folded to (-180, 180]."""
    a = math.fmod(a + 180.0, 360.0)
    if a <= 0.0:
        a += 360.0
    return a - 180.0


def interp_knots(x: float, knots: Sequence[Tuple[float, float]]) -> float:
    """Piecewise-smooth interpolation through ``(x, value)`` knots (sorted by x)."""
    if x <= knots[0][0]:
        return knots[0][1]
    for (x0, v0), (x1, v1) in zip(knots, knots[1:]):
        if x <= x1:
            t = smoothstep(x0, x1, x)
            return v0 + (v1 - v0) * t
    return knots[-1][1]


def catmull(p0: float, p1: float, p2: float, p3: float, t: float) -> float:
    t2, t3 = t * t, t * t * t
    return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)


# ---- lofts --------------------------------------------------------------------


@dataclass(frozen=True)
class RingKey:
    """One authored cross-section of a loft: height, centre, half-width,
    half-depths in front of and behind the centre, and squareness (2 is an
    ellipse; more is boxier)."""

    y: float
    rx: float
    rzf: float
    rzb: float
    cl: float = 0.0
    cz: float = 0.0
    sq: float = 2.0


_CHANNELS = ("rx", "rzf", "rzb", "cl", "cz", "sq")


@dataclass
class Loft:
    """A body of rings between key cross-sections, top (small ``y``) first."""

    keys: List[RingKey]
    bumps: List[Bump] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.keys = sorted(self.keys, key=lambda k: k.y)

    @property
    def top(self) -> float:
        return self.keys[0].y

    @property
    def bottom(self) -> float:
        return self.keys[-1].y

    def shell(self, t: float, *, bumps: bool = True, cap_top: bool = True) -> "Loft":
        """A loft ``t`` centimetres outside this one (cloth, hair). A closed
        top (a ring of no width, the crown) is raised by ``t`` too."""
        keys = [RingKey(k.y, k.rx + t, k.rzf + t, k.rzb + t, k.cl, k.cz, k.sq) for k in self.keys]
        if cap_top and self.keys[0].rx < 1e-6:
            k0 = self.keys[0]
            keys[0] = RingKey(k0.y - t, 0.0, 0.0, 0.0, k0.cl, k0.cz, k0.sq)
        return Loft(keys, list(self.bumps) if bumps else [])

    def section(self, y: float) -> RingKey:
        """The cross-section at ``y`` (Catmull-Rom between keys)."""
        ks = self.keys
        if y <= ks[0].y:
            return ks[0]
        if y >= ks[-1].y:
            return ks[-1]
        i = bisect.bisect_right([k.y for k in ks], y) - 1
        i = max(0, min(i, len(ks) - 2))
        k1, k2 = ks[i], ks[i + 1]
        k0 = ks[i - 1] if i > 0 else k1
        k3 = ks[i + 2] if i + 2 < len(ks) else k2
        t = (y - k1.y) / max(1e-9, k2.y - k1.y)
        if i == 0 and k1.rx < 1e-6 and k1.rzf < 1e-6:
            # A closed top is a dome (an ellipse's cap), not a cone.
            u = math.sqrt(max(0.0, t * (2.0 - t)))
            return RingKey(y, k2.rx * u, k2.rzf * u, k2.rzb * u, lerp(k1.cl, k2.cl, t), lerp(k1.cz, k2.cz, t), k2.sq)

        def ch(a: float, b: float, c: float, d: float) -> float:
            # No overshoot past the two keys it lies between: a ring never
            # bulges past the sections an author gave.
            v = catmull(a, b, c, d, t)
            return min(max(b, c), max(min(b, c), v))

        return RingKey(
            y,
            ch(k0.rx, k1.rx, k2.rx, k3.rx),
            ch(k0.rzf, k1.rzf, k2.rzf, k3.rzf),
            ch(k0.rzb, k1.rzb, k2.rzb, k3.rzb),
            ch(k0.cl, k1.cl, k2.cl, k3.cl),
            ch(k0.cz, k1.cz, k2.cz, k3.cz),
            ch(k0.sq, k1.sq, k2.sq, k3.sq),
        )

    def _at(self, k: RingKey, alpha: float, sa: float, ca: float, out: float) -> Vec3:
        e = 2.0 / max(1.0, k.sq)
        fs = math.copysign(abs(sa) ** e, sa)
        fc = math.copysign(abs(ca) ** e, ca)
        rz = k.rzf if ca >= 0.0 else k.rzb
        bump = out
        for b in self.bumps:
            bump += b(alpha, k.y)
        return (k.cl + k.rx * fs + bump * sa, k.y, k.cz + rz * fc + bump * ca)

    def point(self, alpha: float, y: float, out: float = 0.0) -> Vec3:
        """The surface point at ``alpha`` degrees round the ring at ``y``,
        pushed ``out`` centimetres along the radius."""
        a = math.radians(alpha)
        return self._at(self.section(y), alpha, math.sin(a), math.cos(a), out)

    def ring(self, y: float, n: int = N_ALPHA) -> List[Tuple[float, Vec3]]:
        k = self.section(y)
        return [(a, self._at(k, a, sa, ca, 0.0)) for a, sa, ca in _trig(n)]


_TRIG: dict = {}


def _trig(n: int) -> List[Tuple[float, float, float]]:
    if n not in _TRIG:
        _TRIG[n] = [(360.0 * i / n, math.sin(2 * math.pi * i / n), math.cos(2 * math.pi * i / n)) for i in range(n)]
    return _TRIG[n]


@dataclass
class Run:
    """A visible covered stretch of one ring, in screen order (left to right)."""

    pts: List[Point]

    @property
    def x0(self) -> float:
        return min(p[0] for p in self.pts)

    @property
    def x1(self) -> float:
        return max(p[0] for p in self.pts)

    @property
    def left(self) -> Point:
        return self.pts[0]

    @property
    def right(self) -> Point:
        return self.pts[-1]


def _front_arc(view: View, samples: List[Tuple[float, Vec3]]) -> List[Tuple[float, Point]]:
    """The arc of a ring that faces the camera, left to right on screen."""
    proj = [(a, view.project(p), p[2] * view.c - p[0] * view.s) for a, p in samples]
    n = len(proj)
    xs = [q[1][0] for q in proj]
    if max(xs) - min(xs) < 1e-6:
        return [(proj[0][0], proj[0][1])]
    i0 = min(range(n), key=lambda i: (xs[i], i))
    i1 = max(range(n), key=lambda i: (xs[i], -i))
    fwd = [i0]
    i = i0
    while i != i1:
        i = (i + 1) % n
        fwd.append(i)
    back = [i0]
    i = i0
    while i != i1:
        i = (i - 1) % n
        back.append(i)

    def mean_depth(idx: List[int]) -> float:
        inner = idx[1:-1] or idx
        return sum(proj[j][2] for j in inner) / len(inner)

    arc = fwd if mean_depth(fwd) >= mean_depth(back) else back
    return [(proj[j][0], proj[j][1]) for j in arc]


def ring_runs(view: View, loft: Loft, y: float, margin: Optional[Margin] = None, n: int = N_ALPHA) -> List[Run]:
    """The covered runs of the visible arc of the ring at ``y``."""
    arc = _front_arc(view, loft.ring(y, n))
    if margin is None:
        return [Run([p for _a, p in arc])]
    ms = [margin(a, y) for a, _p in arc]
    runs: List[Run] = []
    cur: List[Point] = []
    for k, (_a, p) in enumerate(arc):
        m = ms[k]
        if k > 0:
            pm = ms[k - 1]
            pp = arc[k - 1][1]
            if (pm >= 0.0) != (m >= 0.0):
                t = pm / (pm - m) if pm != m else 0.5
                cut = lerp2(pp, p, t)
                if pm >= 0.0:
                    cur.append(cut)
                    runs.append(Run(cur))
                    cur = []
                else:
                    cur = [cut]
        if m >= 0.0:
            cur.append(p)
    if cur:
        runs.append(Run(cur))
    return [r for r in runs if len(r.pts) >= 1]


def loft_region(
    view: View,
    loft: Loft,
    y0: float,
    y1: float,
    margin: Optional[Margin] = None,
    *,
    step: float = 0.5,
) -> List[List[Point]]:
    """The polygons of a loft's surface between heights ``y0`` and ``y1``
    (covered where ``margin`` is positive) as seen from ``view``."""
    y0, y1 = max(y0, loft.top), min(y1, loft.bottom)
    if y1 <= y0:
        return []
    count = max(2, int(math.ceil((y1 - y0) / step)) + 1)
    levels = [lerp(y0, y1, i / (count - 1)) for i in range(count)]
    rings = [ring_runs(view, loft, y, margin) for y in levels]
    return runs_to_polygons(rings)


def _overlaps(a: Run, b: Run, tol: float = 1e-4) -> bool:
    return a.x0 <= b.x1 + tol and b.x0 <= a.x1 + tol


def runs_to_polygons(rings: List[List[Run]]) -> List[List[Point]]:
    """Polygons covering the runs of successive rings.

    Runs that continue one-to-one from ring to ring form one column polygon;
    where a region splits or merges, a small connector joins the rings. The
    pieces overlap, and the drawing paints all inks before all fills, so they
    read as one outlined shape."""
    polys: List[List[Point]] = []
    columns: List[List[Run]] = []
    prev: List[Run] = []
    prev_col: List[Optional[int]] = []
    for runs in rings:
        cur_col: List[Optional[int]] = []
        children = {i: [j for j, r in enumerate(runs) if _overlaps(p, r)] for i, p in enumerate(prev)}
        for j, r in enumerate(runs):
            parents = [i for i, p in enumerate(prev) if _overlaps(p, r)]
            if len(parents) == 1 and len(children[parents[0]]) == 1 and prev_col[parents[0]] is not None:
                col = prev_col[parents[0]]
                columns[col].append(r)
                cur_col.append(col)
                continue
            columns.append([r])
            cur_col.append(len(columns) - 1)
            for i in parents:
                polys.append(list(prev[i].pts) + list(reversed(r.pts)))
        prev, prev_col = runs, cur_col
    for col in columns:
        if len(col) < 2:
            continue
        poly = list(col[0].pts)
        poly += [r.right for r in col[1:-1]]
        poly += list(reversed(col[-1].pts))
        poly += [r.left for r in reversed(col[1:-1])]
        polys.append(poly)
    return [_dedupe(p) for p in polys if len(_dedupe(p)) >= 3]


def column_bands(view: View, loft: Loft, y0: float, y1: float, margin: Optional[Margin], *, side: str, frac: float, cap: float,
                 step: float = 0.5, y_from: float = 0.0, y_to: float = 1.0) -> List[List[Point]]:
    """A shading band inside a region: the ``side`` edge (``"left"`` or
    ``"right"``) of each run, ``frac`` of its width but at most ``cap``. Only
    the stretch from ``y_from`` to ``y_to`` (fractions of the height) is kept."""
    y0, y1 = max(y0, loft.top), min(y1, loft.bottom)
    if y1 <= y0:
        return []
    count = max(2, int(math.ceil((y1 - y0) / step)) + 1)
    levels = [lerp(y0, y1, i / (count - 1)) for i in range(count)]
    levels = [y for y in levels if lerp(y0, y1, y_from) - 1e-9 <= y <= lerp(y0, y1, y_to) + 1e-9]
    banded: List[List[Run]] = []
    for y in levels:
        out = []
        for r in ring_runs(view, loft, y, margin):
            w = min(frac * (r.x1 - r.x0), cap)
            if w <= 1e-3:
                continue
            if side == "left":
                edge = r.left
                inner = _point_at_x(r.pts, r.left[0] + w)
                out.append(Run(_dedupe([edge] + [p for p in r.pts if p[0] < inner[0]][1:] + [inner])))
            else:
                edge = r.right
                inner = _point_at_x(r.pts, r.right[0] - w)
                out.append(Run(_dedupe([inner] + [p for p in r.pts if p[0] > inner[0]][:-1] + [edge])))
        banded.append(out)
    return runs_to_polygons(banded)


def _point_at_x(pts: List[Point], x: float) -> Point:
    for a, b in zip(pts, pts[1:]):
        if (a[0] - x) * (b[0] - x) <= 0.0 and a[0] != b[0]:
            return lerp2(a, b, (x - a[0]) / (b[0] - a[0]))
    return min(pts, key=lambda p: abs(p[0] - x))


def _dedupe(pts: List[Point], eps: float = 1e-4) -> List[Point]:
    out: List[Point] = []
    for p in pts:
        if not out or abs(p[0] - out[-1][0]) > eps or abs(p[1] - out[-1][1]) > eps:
            out.append(p)
    if len(out) > 1 and abs(out[0][0] - out[-1][0]) <= eps and abs(out[0][1] - out[-1][1]) <= eps:
        out.pop()
    return out


# ---- capsules and hulls ---------------------------------------------------------


def capsule(a: Point, b: Point, r0: float, r1: float, n: int = 10) -> List[Point]:
    """A tapered capsule from ``a`` (radius ``r0``) to ``b`` (radius ``r1``)."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    d = math.hypot(dx, dy)
    if d < 1e-6:
        r = max(r0, r1)
        return [(a[0] + r * math.cos(t), a[1] + r * math.sin(t)) for t in (2 * math.pi * i / (2 * n) for i in range(2 * n))]
    phi = math.atan2(dy, dx)
    beta = math.asin(max(-0.95, min(0.95, (r0 - r1) / d)))
    out: List[Point] = []
    # Round the far end from one tangent to the other, then the near end.
    for i in range(n + 1):
        t = phi - math.pi / 2 - beta + (math.pi + 2 * beta) * i / n
        out.append((b[0] + r1 * math.cos(t), b[1] + r1 * math.sin(t)))
    for i in range(n + 1):
        t = phi + math.pi / 2 + beta + (math.pi - 2 * beta) * i / n
        out.append((a[0] + r0 * math.cos(t), a[1] + r0 * math.sin(t)))
    return out


def tube(a: Point, b: Point, r0: float, r1: float, *, round_a: bool = True, round_b: bool = True, n: int = 10) -> List[Point]:
    """A tapered tube: rounded at an end that is a joint, cut square at an end
    that is a hem or a cuff (a round cap there reads as a ball)."""
    if round_a and round_b:
        return capsule(a, b, r0, r1, n)
    dx, dy = b[0] - a[0], b[1] - a[1]
    d = math.hypot(dx, dy)
    if d < 1e-6:
        return capsule(a, b, r0, r1, n)
    ux, uy = dx / d, dy / d
    nx, ny = -uy, ux
    out: List[Point] = []
    phi = math.atan2(dy, dx)
    if round_b:
        out += [(b[0] + r1 * math.cos(t), b[1] + r1 * math.sin(t)) for t in (phi - math.pi / 2 + math.pi * i / n for i in range(n + 1))]
    else:
        out += [(b[0] - nx * r1, b[1] - ny * r1), (b[0] + nx * r1, b[1] + ny * r1)]
    if round_a:
        out += [(a[0] + r0 * math.cos(t), a[1] + r0 * math.sin(t)) for t in (phi + math.pi / 2 + math.pi * i / n for i in range(n + 1))]
    else:
        out += [(a[0] + nx * r0, a[1] + ny * r0), (a[0] - nx * r0, a[1] - ny * r0)]
    return out


def capsule_band(a: Point, b: Point, r0: float, r1: float, w: float, *, side: str = "left") -> List[Point]:
    """A strip along one long edge of a capsule (``side`` on screen)."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    d = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / d, dx / d
    if (nx < 0.0) != (side == "left"):
        nx, ny = -nx, -ny
    return [
        (a[0] + nx * r0, a[1] + ny * r0),
        (b[0] + nx * r1, b[1] + ny * r1),
        (b[0] + nx * max(0.0, r1 - w), b[1] + ny * max(0.0, r1 - w)),
        (a[0] + nx * max(0.0, r0 - w), a[1] + ny * max(0.0, r0 - w)),
    ]


def hull(points: Iterable[Point]) -> List[Point]:
    """The convex hull (counter-clockwise on screen), by the monotone chain."""
    pts = sorted(set((round(p[0], 6), round(p[1], 6)) for p in points))
    if len(pts) <= 2:
        return pts

    def cross(o: Point, a: Point, b: Point) -> float:
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower: List[Point] = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper: List[Point] = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def ellipse3(center: Vec3, u: Vec3, v: Vec3, ru: float, rv: float, n: int = 16) -> List[Vec3]:
    """``n`` points round an ellipse in 3D (axes ``u`` and ``v``)."""
    out = []
    for i in range(n):
        t = 2 * math.pi * i / n
        out.append(add3(center, add3(scale3(u, ru * math.cos(t)), scale3(v, rv * math.sin(t)))))
    return out


def clip_convex(subject: List[Point], clipper: List[Point]) -> List[Point]:
    """Sutherland-Hodgman: ``subject`` cut to the convex polygon ``clipper``."""
    if len(clipper) < 3 or len(subject) < 3:
        return []
    area = sum(clipper[i][0] * clipper[(i + 1) % len(clipper)][1] - clipper[(i + 1) % len(clipper)][0] * clipper[i][1] for i in range(len(clipper)))
    sign = 1.0 if area > 0 else -1.0

    def inside(p: Point, a: Point, b: Point) -> bool:
        return sign * ((b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])) >= 0.0

    def meet(p: Point, q: Point, a: Point, b: Point) -> Point:
        x1, y1, x2, y2 = p[0], p[1], q[0], q[1]
        x3, y3, x4, y4 = a[0], a[1], b[0], b[1]
        den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(den) < 1e-12:
            return q
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
        return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))

    out = list(subject)
    for i in range(len(clipper)):
        a, b = clipper[i], clipper[(i + 1) % len(clipper)]
        inp, out = out, []
        if not inp:
            break
        s = inp[-1]
        for e in inp:
            if inside(e, a, b):
                if not inside(s, a, b):
                    out.append(meet(s, e, a, b))
                out.append(e)
            elif inside(s, a, b):
                out.append(meet(s, e, a, b))
            s = e
    return out


def polygon_area(pts: Sequence[Point]) -> float:
    return 0.5 * abs(sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts))))


def bounds(polys: Iterable[Sequence[Point]]) -> Tuple[float, float, float, float]:
    xs: List[float] = []
    ys: List[float] = []
    for poly in polys:
        for x, y in poly:
            xs.append(x)
            ys.append(y)
    return (min(xs), min(ys), max(xs), max(ys))
