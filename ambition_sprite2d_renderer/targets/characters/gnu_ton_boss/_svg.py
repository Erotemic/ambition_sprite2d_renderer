"""The small SVG drawing kit the giant gnu is drawn with.

A copy of the helpers of ``scripts/svg_art/svgkit.py`` and ``birdkit.py`` that
the giant uses: those two are reference scripts outside this package, and a
published target can not import them. ``smooth`` is a closed Catmull-Rom
spline through points (a point with a third element ``True`` is a corner);
``part`` declares a layer with a draw order; ``outlined`` is a filled
silhouette with its shading clipped inside it and an ink edge.
"""

from __future__ import annotations

import math
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

DX, DY = 0.0, 0.0
INK = "#000000"
#: Half the silhouette ink width (an ink layer's stroke is ``4 * OW``).
OW = 1.0
C: Dict[str, str] = {}
_XF: Optional[Tuple[float, float, float]] = None

#: (id, label, part, bone, z, extra attributes, body lines)
PARTS: List[tuple] = []


def configure(*, dx: float = 0.0, dy: float = 0.0, ink: str, ow: float, colors: Dict[str, str]) -> None:
    """Start a drawing: its offset, outline ink and width, and palette."""
    global DX, DY, INK, OW, C, _XF
    DX, DY, INK, OW, C, _XF = dx, dy, ink, ow, colors, None
    PARTS.clear()


def transform(xf: Optional[Tuple[float, float, float]]) -> None:
    """Scale design points by ``k`` about ``(cx, cy)`` from now on (``None``
    resets)."""
    global _XF
    _XF = xf


def P(x, y):
    if _XF is not None:
        cx, cy, k = _XF
        x, y = cx + (x - cx) * k, cy + (y - cy) * k
    return (x + DX, y + DY)


def f(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return s if s != "-0" else "0"


def pt(p):
    return f"{f(p[0])},{f(p[1])}"


def smooth(points, closed=True, tension=1.0):
    """Catmull-Rom through design points; a 3rd element True marks a corner."""
    pts = [(P(p[0], p[1]), len(p) > 2 and p[2]) for p in points]
    n = len(pts)
    out = [f"M{pt(pts[0][0])}"]
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0 = pts[(i - 1) % n][0] if (closed or i > 0) else pts[i][0]
        p1, c1 = pts[i]
        p2, c2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n][0] if (closed or i + 2 < n) else p2
        k = tension / 6.0
        a = p1 if c1 else (p1[0] + (p2[0] - p0[0]) * k, p1[1] + (p2[1] - p0[1]) * k)
        b = p2 if c2 else (p2[0] - (p3[0] - p1[0]) * k, p2[1] - (p3[1] - p1[1]) * k)
        out.append(f"C{pt(a)} {pt(b)} {pt(p2)}")
    if closed:
        out.append("Z")
    return " ".join(out)


def smooth_run(points, i0, count):
    """The closed spline through ``points`` from vertex i0 along ``count`` segments."""
    segs = smooth(points).split(" C")[1:]
    segs[-1] = segs[-1].replace(" Z", "")
    n = len(points)
    out = [f"M{pt(P(*points[i0][:2]))}"]
    for k in range(count):
        out.append("C" + segs[(i0 + k) % n])
    return " ".join(out)


def poly(points):
    pts = [P(*p[:2]) for p in points]
    return "M" + " L".join(pt(p) for p in pts) + " Z"


def capsule(a, b, r0, r1):
    """A tapered capsule from design point a to b, round at both ends."""
    ax, ay = a
    bx, by = b
    d = math.hypot(bx - ax, by - ay)
    ux, uy = (bx - ax) / d, (by - ay) / d
    nx, ny = -uy, ux
    pts = []
    steps = 10
    for i in range(steps + 1):
        th = math.pi / 2 + math.pi * i / steps
        lx, ly = math.cos(th) * r0, math.sin(th) * r0
        pts.append((ax + lx * ux + ly * nx, ay + lx * uy + ly * ny))
    for i in range(steps + 1):
        th = -math.pi / 2 + math.pi * i / steps
        lx, ly = math.cos(th) * r1, math.sin(th) * r1
        pts.append((bx + lx * ux + ly * nx, by + lx * uy + ly * ny))
    return poly(pts)


def path(d, fill="none", stroke=None, sw=None, extra=""):
    s = f'<path d="{d}" fill="{fill}"'
    if stroke:
        s += f' stroke="{stroke}" stroke-width="{f(sw)}" stroke-linejoin="round" stroke-linecap="round"'
    return s + extra + " />"


def line(points, stroke, sw, closed=False, tension=1.0):
    return path(smooth(points, closed=closed, tension=tension), "none", stroke, sw)


def ellipse(cx, cy, rx, ry, fill, stroke=None, sw=None, rot=0.0):
    x, y = P(cx, cy)
    s = f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="{f(rx)}" ry="{f(ry)}" fill="{fill}"'
    if rot:
        s += f' transform="rotate({f(rot)} {f(x)} {f(y)})"'
    if stroke:
        s += f' stroke="{stroke}" stroke-width="{f(sw)}"'
    return s + " />"


def part(pid, label, name, bone, z, body, extra=""):
    PARTS.append((pid, label, name, bone, z, extra, body))


def clipped(cid, sil_d, items):
    return [f'<clipPath id="{cid}"><path d="{sil_d}" /></clipPath>',
            f'<g clip-path="url(#{cid})">'] + items + ["</g>"]


def ink(name, bone, z, sil_d):
    """A part's silhouette grown by the outline width, as its own layer."""
    part(f"{name.replace('_', '-')}-ink", f"Ink - {name}", f"{name}_ink", bone, z,
         [path(sil_d, INK, INK, 2 * OW * 2)])


def fringe(edge, n, length, lean, fill, tip=None, ow=1.1, inset=8.0, flip=False, jitter=0.0):
    """A row of ``n`` spikes standing off the polyline ``edge``: each spike's
    tip sits ``length`` out along the edge's normal (the side away from the
    body; ``flip`` for the other side), leaning ``lean`` (fraction of a
    spacing) along the edge. Closed back through the body ``inset`` deep, so
    the body fill drawn over it leaves only the spikes."""
    segs = list(zip(edge[:-1], edge[1:]))
    lens = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in segs]
    total = sum(lens)

    def at(u):
        d = u * total
        for (a, b), L in zip(segs, lens):
            if d <= L or (a, b) == segs[-1]:
                t = d / L if L else 0.0
                tx, ty = (b[0] - a[0]) / L, (b[1] - a[1]) / L
                return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t), (tx, ty)
            d -= L
        return edge[-1], (1.0, 0.0)

    def spike(k):
        (pm, tm) = at((k + 0.5) / n)
        nx, ny = tm[1] * sign, -tm[0] * sign
        L = length * (1.0 + jitter * math.sin(k * 2.3))
        slide = lean * total / n
        return pm, tm, nx, ny, L, slide

    sign = -1.0 if flip else 1.0
    outer = []
    for k in range(n):
        p0, _t0 = at(k / n)
        pm, tm, nx, ny, L, slide = spike(k)
        tipp = (pm[0] + nx * L + tm[0] * slide, pm[1] + ny * L + tm[1] * slide)
        outer += [p0 + (True,), tipp + (True,)]
    pe, _te = at(1.0)
    outer.append(pe + (True,))
    inner = []
    for k in range(n, -1, -1):
        p, t = at(k / n)
        nx, ny = t[1] * sign, -t[0] * sign
        inner.append((p[0] - nx * inset, p[1] - ny * inset, True))
    out = [path(smooth(outer + inner), fill, INK, ow)]
    if tip:
        for k in range(n):
            pm, tm, nx, ny, L, slide = spike(k)
            tipp = (pm[0] + nx * L + tm[0] * slide, pm[1] + ny * L + tm[1] * slide)
            mid = (pm[0] + nx * L * 0.55 + tm[0] * slide * 0.55, pm[1] + ny * L * 0.55 + tm[1] * slide * 0.55)
            out.append(line([mid, tipp], tip, 2.2))
    return out


def outlined(sil, fill, items=(), cid=None, width=None):
    """A filled silhouette with shading clipped inside it and an ink edge."""
    body = [path(sil, fill)]
    if items:
        body = clipped(cid, sil, [path(sil, fill)] + list(items))
    return body + [path(sil, "none", INK, width or 2 * OW)]


def tube(centre: Sequence[Tuple[float, float]], r0: float, r1: float) -> List[tuple]:
    """The outline of a tapered tube along ``centre`` (a neck), as points for
    ``smooth``: down one side and back up the other."""
    left, right = [], []
    n = len(centre) - 1
    for i, (x, y) in enumerate(centre):
        ax, ay = centre[max(0, i - 1)]
        bx, by = centre[min(n, i + 1)]
        d = math.hypot(bx - ax, by - ay)
        nx, ny = -(by - ay) / d, (bx - ax) / d
        r = r0 + (r1 - r0) * i / n
        left.append((x + nx * r, y + ny * r))
        right.append((x - nx * r, y - ny * r))
    return left + right[::-1]
