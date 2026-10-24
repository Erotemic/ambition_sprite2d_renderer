"""Paint for the generated drawing: colours, and SVG elements in screen cm.

The house style (the cast drawn since 2026-10): flat colour, a thick dark
outline round every silhouette, thin inner lines, and simple cel shading with
the shade on the left and the light on the right. NO drop shadow, ever.

An outlined shape is drawn as INK then FILL: the ink is the shape stroked
``2 * OUTLINE`` wide in the ink colour, the fill is the shape in its colour on
top. Several pieces of one region paint all their inks before any fill, so
they read as one outlined silhouette with no seams inside it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

from .geometry import Point

INK = "#1d1714"
#: The outline width outside a silhouette, in cm (about 1/290 of a person).
OUTLINE = 0.6
#: The width of an inner line, in cm.
FINE = 0.28


def _rgb(h: str) -> Tuple[int, int, int]:
    return int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)


def _hex(c: Sequence[float]) -> str:
    return "#" + "".join(f"{max(0, min(255, int(round(v)))):02x}" for v in c)


def mix(a: str, b: str, t: float) -> str:
    ra, rb = _rgb(a), _rgb(b)
    return _hex([x + (y - x) * t for x, y in zip(ra, rb)])


def shade(c: str, k: float = 0.22) -> str:
    """The cel shade of ``c``: darker, a little toward warm violet."""
    r, g, b = _rgb(c)
    return _hex([r * (1 - k) - 4 * k, g * (1 - k * 1.12), b * (1 - k * 0.9)])


def light(c: str, k: float = 0.2) -> str:
    return mix(c, "#fffaf0", k)


def luminance(c: str) -> float:
    r, g, b = _rgb(c)
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255.0


@dataclass(frozen=True)
class El:
    """One SVG drawable (a ``path``), its geometry in screen cm."""

    d: str
    fill: str = "none"
    stroke: str = "none"
    width: float = 0.0
    cap: str = "round"
    opacity: float = 1.0


def simplify(pts: Sequence[Point], tol: float = 0.035, closed: bool = True) -> List[Point]:
    """Ramer-Douglas-Peucker: drop points within ``tol`` cm of the line."""
    pts = list(pts)
    if len(pts) <= 6:
        return pts
    if closed:
        # Split a closed ring at its two farthest-apart points.
        i0 = 0
        i1 = max(range(len(pts)), key=lambda i: (pts[i][0] - pts[0][0]) ** 2 + (pts[i][1] - pts[0][1]) ** 2)
        a = _rdp(pts[i0:i1 + 1], tol)
        b = _rdp(pts[i1:] + [pts[0]], tol)
        return a[:-1] + b[:-1]
    return _rdp(pts, tol)


def _rdp(pts: List[Point], tol: float) -> List[Point]:
    if len(pts) < 3:
        return list(pts)
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        i, j = stack.pop()
        ax, ay = pts[i]
        bx, by = pts[j]
        dx, dy = bx - ax, by - ay
        n = (dx * dx + dy * dy) ** 0.5
        best, at = -1.0, -1
        for k in range(i + 1, j):
            px, py = pts[k]
            d = abs(dy * (px - ax) - dx * (py - ay)) / n if n > 1e-12 else ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
            if d > best:
                best, at = d, k
        if at >= 0 and best > tol:
            keep[at] = True
            stack.append((i, at))
            stack.append((at, j))
    return [p for p, k in zip(pts, keep) if k]


def _f(v: float) -> str:
    s = f"{v:.2f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


class Canvas:
    """Screen cm -> SVG user units for one view cell."""

    def __init__(self, unit: float, origin: Point) -> None:
        self.unit = unit
        self.ox, self.oy = origin

    def xy(self, p: Point) -> Tuple[float, float]:
        return (self.ox + p[0] * self.unit, self.oy + p[1] * self.unit)

    def poly_d(self, pts: Sequence[Point], closed: bool = True) -> str:
        q = [self.xy(p) for p in simplify(pts, closed=closed)]
        if not q:
            return ""
        out = "M" + " ".join(f"{_f(x)},{_f(y)}" for x, y in q)
        return out + ("Z" if closed else "")

    def smooth_d(self, pts: Sequence[Point], closed: bool = True) -> str:
        """A Catmull-Rom curve through the points, as cubic Beziers."""
        q = [self.xy(p) for p in pts]
        n = len(q)
        if n < 3:
            return self.poly_d(pts, closed)
        out = [f"M{_f(q[0][0])},{_f(q[0][1])}"]
        segs = n if closed else n - 1
        for i in range(segs):
            p0 = q[(i - 1) % n] if (closed or i > 0) else q[i]
            p1, p2 = q[i], q[(i + 1) % n]
            p3 = q[(i + 2) % n] if (closed or i + 2 < n) else p2
            c1 = (p1[0] + (p2[0] - p0[0]) / 6.0, p1[1] + (p2[1] - p0[1]) / 6.0)
            c2 = (p2[0] - (p3[0] - p1[0]) / 6.0, p2[1] - (p3[1] - p1[1]) / 6.0)
            out.append(f"C{_f(c1[0])},{_f(c1[1])} {_f(c2[0])},{_f(c2[1])} {_f(p2[0])},{_f(p2[1])}")
        return " ".join(out) + ("Z" if closed else "")

    def w(self, cm: float) -> float:
        return cm * self.unit


class Paint:
    """Collects the elements of one part, in paint order."""

    def __init__(self, canvas: Canvas) -> None:
        self.cv = canvas
        self.els: List[El] = []

    def region(self, polys: Iterable[Sequence[Point]], color: str, *, ink: bool = True, smooth: bool = False,
               outline: float = OUTLINE) -> None:
        polys = [p for p in polys if len(p) >= 3]
        if not polys:
            return
        mk = self.cv.smooth_d if smooth else self.cv.poly_d
        ds = [mk(p) for p in polys]
        if ink:
            for d in ds:
                self.els.append(El(d, fill=INK, stroke=INK, width=self.cv.w(2 * outline)))
        for d in ds:
            # A hairline of the fill's own colour closes the seams between
            # the pieces of one region.
            self.els.append(El(d, fill=color, stroke=color, width=self.cv.w(0.12) if len(ds) > 1 else 0.0))

    def flat(self, polys: Iterable[Sequence[Point]], color: str, *, smooth: bool = False, opacity: float = 1.0) -> None:
        """Fill only: shading, a band of colour inside an outlined region."""
        mk = self.cv.smooth_d if smooth else self.cv.poly_d
        for p in polys:
            if len(p) >= 3:
                self.els.append(El(mk(p), fill=color, opacity=opacity))

    def line(self, pts: Sequence[Point], color: str = INK, width: float = FINE, *, smooth: bool = True, cap: str = "round") -> None:
        if len(pts) < 2:
            return
        d = self.cv.smooth_d(pts, closed=False) if smooth and len(pts) >= 3 else self.cv.poly_d(pts, closed=False)
        self.els.append(El(d, stroke=color, width=self.cv.w(width), cap=cap))

    def dot(self, p: Point, r: float, color: str) -> None:
        import math

        pts = [(p[0] + r * math.cos(2 * math.pi * i / 10), p[1] + r * math.sin(2 * math.pi * i / 10)) for i in range(10)]
        self.els.append(El(self.cv.smooth_d(pts), fill=color))


def element_xml(el: El, eid: str) -> str:
    attrs = [f'id="{eid}"', f'd="{el.d}"']
    attrs.append(f'fill="{el.fill}"')
    if el.stroke != "none" and el.width > 0.0:
        attrs.append(f'stroke="{el.stroke}" stroke-width="{_f(el.width)}" stroke-linejoin="round" stroke-linecap="{el.cap}"')
    if el.opacity < 1.0:
        attrs.append(f'opacity="{_f(el.opacity)}"')
    return "<path " + " ".join(attrs) + "/>"


__all__ = ["Canvas", "El", "FINE", "INK", "OUTLINE", "Paint", "element_xml", "light", "luminance", "mix", "shade"]
