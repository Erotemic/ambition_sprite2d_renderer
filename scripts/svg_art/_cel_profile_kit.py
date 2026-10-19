"""Cel-shaded side-view figure helpers over ``svgkit`` (reference, not authority).

Used by the drawing scripts of the Dark Lord, the Creator and Hypatia Prime
(2026-10-18 redraws). ``cel(sil, base, shade, light)`` clips to the silhouette,
paints a shade band (the shape minus itself shifted up-front, so it hugs the
down-back edge) and a light band (the shape minus itself shifted down-back, so
it hugs the up-front edge), then inks the outline. The bands follow any
outline, so every shape is shaded alike without hand-placed band polygons.

Faces are drawn in profile, facing +x: ``skull``, ``face`` (shading clipped to
the skull) and ``features`` (eye, brow, nose, mouth, ear) in local units about
the ear, scaled by ``k``.
"""
from __future__ import annotations

import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import svgkit as svg  # noqa: E402
from svgkit import capsule, ellipse, line, path, poly, smooth  # noqa: E402,F401

INK = "#1a1517"
OW = 1.5
_N = [0]


def begin(ink: str, ow: float = 1.5) -> None:
    """Start a drawing: its ink and outline half-width; no parts yet."""
    global INK, OW
    INK, OW = ink, ow
    svg.configure(dx=0, dy=0, ink=ink, ow=ow, colors={})
    _N[0] = 0


def _cid() -> str:
    _N[0] += 1
    return f"c{_N[0]}"


_NUM = re.compile(r"(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)")


def shifted(d: str, dx: float, dy: float) -> str:
    return _NUM.sub(lambda m: f"{float(m.group(1)) + dx:.2f},{float(m.group(2)) + dy:.2f}", d)


def cel(sil, base, shade=None, light=None, items=(), s=(5.0, -4.0), l=(2.6, -2.2), width=None, outline=True):
    """A shape: base fill, a shade band down-back and a light band up-front
    (both clipped inside), ``items`` clipped too, then its ink outline."""
    cid = _cid()
    inner = [path(sil, base)]
    if shade:
        inner.append(path(sil + " " + shifted(sil, s[0], s[1]), shade, extra=' fill-rule="evenodd"'))
    if light:
        inner.append(path(sil + " " + shifted(sil, -l[0], -l[1]), light, extra=' fill-rule="evenodd"'))
    inner += list(items)
    out = [f'<clipPath id="{cid}"><path d="{sil}" /></clipPath>', f'<g clip-path="url(#{cid})">'] + inner + ["</g>"]
    if outline:
        out.append(path(sil, "none", INK, width or 2 * OW))
    return out


def group(shapes, width=None):
    """Several shapes inked as ONE silhouette (every ink under every fill):
    ``shapes`` = [(sil, base, shade, light, items, s, l)]."""
    w = width or 2 * OW
    out = [path(sh[0], INK, INK, w * 2) for sh in shapes]
    for sh in shapes:
        sil, base, shade, light = sh[:4]
        items = sh[4] if len(sh) > 4 else ()
        s = sh[5] if len(sh) > 5 else (5.0, -4.0)
        l = sh[6] if len(sh) > 6 else (2.6, -2.2)
        out += cel(sil, base, shade, light, items, s, l, outline=False)
    return out


def tone(hex_color: str, f: float) -> str:
    """``#rrggbb`` darkened (``f`` < 1) or lightened toward white (``f`` > 1)."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    if f <= 1:
        r, g, b = (int(v * f) for v in (r, g, b))
    else:
        t = f - 1
        r, g, b = (int(v + (255 - v) * t) for v in (r, g, b))
    return f"#{r:02x}{g:02x}{b:02x}"


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def norm(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    d = math.hypot(dx, dy) or 1.0
    return dx / d, dy / d


def along(a, b):
    """Point maker along a->b: ``p(t, s)`` is t units along, s to the left normal."""
    ux, uy = norm(a, b)
    nx, ny = -uy, ux
    return lambda t, s: (a[0] + ux * t + nx * s, a[1] + uy * t + ny * s)


def rot(p, deg):
    a = math.radians(deg)
    return (p[0] * math.cos(a) - p[1] * math.sin(a), p[0] * math.sin(a) + p[1] * math.cos(a))


def xf(origin, deg, pts):
    """Local points (x along a bone, y to its right) turned by ``deg`` and put at ``origin``."""
    out = []
    for q in pts:
        r = rot((q[0], q[1]), deg)
        out.append((origin[0] + r[0], origin[1] + r[1]) + tuple(q[2:]))
    return out


def deg_of(a, b) -> float:
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


def glow(cx, cy, rx, ry, color, alpha=0.28, rot_deg=0.0):
    """An authored soft halo: one flat translucent ellipse (never a blur)."""
    x, y = svg.P(cx, cy)
    tr = f' transform="rotate({rot_deg:.1f} {x:.1f} {y:.1f})"' if rot_deg else ""
    return f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="{color}" fill-opacity="{alpha}"{tr} />'


def limb(a, b, r0, r1, base, shade, light=None, items=(), s=None):
    """A tapered limb segment, shaded."""
    k = min(r0, r1)
    return cel(capsule(a, b, r0, r1), base, shade, light, items, s=s or (k * 0.55, -k * 0.45), l=(k * 0.28, -k * 0.24))


def hand_open(wr, deg, base, shade, light=None, k=1.0, thumb_fwd=True):
    """A relaxed hand from the wrist along ``deg``: fingers together, slightly
    curled, the thumb on the forward side."""
    tsg = -1 if thumb_fwd else 1
    pts = [(0, -6.5), (10, -7.5), (19, -7), (27, -5.5), (31, -2), (31, 2.5), (27, 5.5), (18, 7), (8, 7), (0, 6)]
    pts = [(x * k, y * k) for x, y in pts]
    items = [line(xf(wr, deg, [(16 * k, -2.2 * k), (29 * k, -1.6 * k)]), shade, 1.1),
             line(xf(wr, deg, [(15 * k, 2.0 * k), (27 * k, 2.4 * k)]), shade, 1.1)]
    out = cel(smooth(xf(wr, deg, pts)), base, shade, light, items, s=(2.2, -1.8), l=(1.2, -1.0))
    th = [(4 * k, tsg * 5 * k), (10 * k, tsg * 9 * k), (17 * k, tsg * 10.5 * k), (21 * k, tsg * 9 * k),
          (17 * k, tsg * 6.5 * k), (9 * k, tsg * 3 * k)]
    out += cel(smooth(xf(wr, deg, th)), base, shade, None, s=(1.4, -1.2), width=1.6 * OW)
    return out


def hand_fist(wr, deg, base, shade, light=None, k=1.0):
    pts = [(-1, -7), (9, -9), (17, -8), (21, -3), (21, 4), (16, 8), (4, 8.5), (-1, 6)]
    pts = [(x * k, y * k) for x, y in pts]
    items = [line(xf(wr, deg, [(13 * k, -7 * k), (14 * k, 7 * k)]), shade, 1.1),
             line(xf(wr, deg, [(17.5 * k, -6 * k), (18 * k, 6 * k)]), shade, 1.0)]
    out = cel(smooth(xf(wr, deg, pts)), base, shade, light, items, s=(2.2, -1.8), l=(1.2, -1.0))
    th = [(3 * k, -7 * k), (10 * k, -10 * k), (15 * k, -8 * k), (12 * k, -4 * k), (4 * k, -3 * k)]
    out += cel(smooth(xf(wr, deg, th)), base, shade, None, s=(1.2, -1.0), width=1.6 * OW)
    return out


def hand_grip(c, pole_deg, base, shade, light=None, k=1.0, side=1):
    """A fist closed round a pole through ``c`` along ``pole_deg``: the
    knuckles on the ``side`` of the pole, the thumb wrapped over."""
    a = pole_deg
    pts = [(-9, -8 * side), (-10, 2 * side), (-8, 9 * side), (0, 11 * side), (9, 9 * side), (10, 0), (8, -8 * side),
           (0, -9 * side)]
    pts = [(x * k, y * k) for x, y in pts]
    items = [line(xf(c, a, [(-5 * k, 6 * side * k), (-5 * k, 10 * side * k)]), shade, 1.0),
             line(xf(c, a, [(0, 6.5 * side * k), (0, 11 * side * k)]), shade, 1.0),
             line(xf(c, a, [(5 * k, 6 * side * k), (5 * k, 10 * side * k)]), shade, 1.0)]
    out = cel(smooth(xf(c, a, pts)), base, shade, light, items, s=(2.0, -1.6), l=(1.1, -0.9))
    th = [(-9 * k, -3 * side * k), (-4 * k, 4 * side * k), (2 * k, 6 * side * k), (4 * k, 3 * side * k), (-2 * k, -2 * side * k),
          (-8 * k, -7 * side * k)]
    out += cel(smooth(xf(c, a, th)), base, shade, None, s=(1.0, -0.8), width=1.6 * OW)
    return out


# ---- profile heads (local units: origin at the ear, facing +x) ----------------------------
SKULL_M = [(-19, 22), (-30, 6), (-33, -13), (-25, -31), (-7, -41), (11, -40), (23, -31), (27.5, -18), (28.5, -10, True),
           (27, -5), (29.5, 1), (35.5, 10.5, True), (30, 13.5), (30.5, 17), (31, 19.5), (29.3, 22, True), (30.3, 25),
           (28.4, 28), (30, 33), (25.5, 37.5), (13, 38), (2, 31), (-7, 23)]
SKULL_F = [(-18, 20), (-29, 5), (-31, -13), (-24, -30), (-7, -39), (10, -38), (21, -30), (25.5, -18), (26.4, -10, True),
           (25.2, -5.5), (27.5, 0), (32, 8, True), (28.2, 10.6), (28.6, 14), (30.2, 17), (28, 19.6, True), (30, 22.4),
           (27.5, 26), (28.4, 30), (24, 34.5), (13, 35), (2, 29), (-7, 21)]


def hd(c, k, pts):
    return [(c[0] + q[0] * k, c[1] + q[1] * k) + tuple(q[2:]) for q in pts]


def skull(c, k, female=False):
    return smooth(hd(c, k, SKULL_F if female else SKULL_M))


def face(c, k, shade, light, cheek=None):
    """Shading of the face, to be clipped to the skull."""
    items = [path(smooth(hd(c, k, [(-34, 4), (-10, 14), (6, 26), (20, 34), (26, 44), (-30, 44)])), shade),
             path(smooth(hd(c, k, [(4, -30), (20, -28), (25, -14), (14, -20)])), light)]
    if cheek:
        items.append(ellipse(c[0] + 16 * k, c[1] + 10 * k, 6 * k, 3.5 * k, cheek))
    return items


def eye(c, k, kind, shade, female=False, iris="#2e2219", eye_white="#f4ece2", lashes=False, eye_dy=0.0):
    """The near eye: ``open``, ``shut`` (a lid line) or ``dead`` (an X)."""
    ey = -6 + eye_dy
    ex = 18.5 if not female else 17.5
    if kind == "shut":
        out = [line(hd(c, k, [(ex - 5, ey + 0.2), (ex + 0.5, ey + 1.6), (ex + 6, ey + 0.2)]), INK, 1.5)]
        if lashes:
            out.append(line(hd(c, k, [(ex + 5.2, ey + 0.4), (ex + 7.4, ey + 1.6)]), INK, 1.1))
        return out
    if kind == "dead":
        return [line(hd(c, k, [(ex - 3.5, ey - 3), (ex + 4.5, ey + 3)]), INK, 1.5),
                line(hd(c, k, [(ex - 3.5, ey + 3), (ex + 4.5, ey - 3)]), INK, 1.5)]
    white = smooth(hd(c, k, [(ex - 4.5, ey + 0.5), (ex - 1, ey - 2.6), (ex + 3.5, ey - 2.4), (ex + 5.6, ey + 0.2, True),
                            (ex + 2, ey + 2.2), (ex - 2.5, ey + 1.8)]))
    out = [path(white, eye_white),
           ellipse(c[0] + (ex + 2.4) * k, c[1] + (ey - 0.1) * k, 1.9 * k, 2.2 * k, iris),
           ellipse(c[0] + (ex + 2.9) * k, c[1] + (ey - 0.9) * k, 0.55 * k, 0.55 * k, "#ffffff"),
           # the upper lid, heavier at the front
           path(smooth(hd(c, k, [(ex - 5.5, ey + 0.4), (ex - 1, ey - 3.2), (ex + 4, ey - 3.0), (ex + 6.4, ey + 0.4, True),
                                 (ex + 3.5, ey - 1.6), (ex - 1, ey - 1.9)])), INK),
           line(hd(c, k, [(ex - 2.5, ey + 2.1), (ex + 3, ey + 2.3)]), shade, 0.9)]
    if lashes:
        for dx, dy in ((4.4, -2.0), (5.6, -1.0)):
            out.append(line(hd(c, k, [(ex + dx, ey + dy), (ex + dx + 2.6, ey + dy - 1.8)]), INK, 1.2))
    return out


def features(c, k, skin, shade, female=False, brow="#2a1d18", lips=None, stern=0.0, ear=True, mouth=True):
    """Brow, nostril, cheek line, mouth and ear, over the skull (the eye is
    ``eye``: a rig swaps it)."""
    out = []
    ey = -6
    ex = 18.5 if not female else 17.5
    by = ey - 6.5 - stern * 1.0
    if female:
        bpts = [(ex - 6, by + 2.2), (ex - 1, by - 1.0), (ex + 4.5, by - 0.6), (ex + 6.5, by + 1.4, True), (ex + 2, by + 0.8),
                (ex - 3, by + 2.2)]
    else:
        bpts = [(ex - 6, by + 1.2 - stern), (ex - 1, by - 1.4), (ex + 5, by - 0.2 + stern * 1.5), (ex + 7.5, by + 2.2 + stern * 2, True),
                (ex + 2, by + 1.8 + stern), (ex - 4, by + 2.6)]
    out.append(path(smooth(hd(c, k, bpts)), brow, INK, 0.7))
    nx, ny = (31, 10.5) if not female else (28.5, 8.5)
    out.append(path(smooth(hd(c, k, [(nx - 4, ny - 1), (nx - 1, ny - 1.6), (nx + 0.5, ny + 1), (nx - 3, ny + 1.4)])), shade))
    out.append(line(hd(c, k, [(nx - 6, ny - 3), (nx - 5, ny + 1), (nx - 2.5, ny + 2.2)]), shade, 1.1))
    my = 22 if not female else 19.6
    mx = 29 if not female else 27.8
    if lips:
        out.append(path(smooth(hd(c, k, [(mx - 4.5, my), (mx - 0.5, my - 2.6), (mx + 1.8, my - 2.4), (mx + 1.2, my, True),
                                        (mx + 2.2, my + 2.6), (mx - 1, my + 3.4), (mx - 4.5, my + 0.6)])), lips))
    if mouth:
        out.append(line(hd(c, k, [(mx - 6.5, my + 0.6), (mx - 3, my + 0.1), (mx + 1.2, my)]), INK, 1.3))
    if ear:
        es = smooth(hd(c, k, [(-3, -9), (3, -9.5), (5.5, -3), (4.5, 5), (0, 10), (-4, 7), (-5.5, -1)]))
        out += cel(es, skin, shade, None, [line(hd(c, k, [(0, -5), (2.5, -1), (0.5, 5)]), shade, 1.4)], s=(2, -1.5),
                   width=1.4 * OW)
    return out


def talk_mouth(c, k, female=False):
    """An open mouth, for a talking frame (a dark wedge at the lips)."""
    my = 22 if not female else 19.6
    mx = 29 if not female else 27.8
    return [path(smooth(hd(c, k, [(mx - 6, my + 0.2), (mx + 1.6, my - 0.8, True), (mx + 1.2, my + 3.2), (mx - 3, my + 4.2)])), "#3a1a1a",
                 INK, 1.0)]


def part(group_id, label, name, bone, z, body, channel="", default_on=False):
    """A rig part layer; ``channel`` names its opacity channel."""
    extra = ""
    if channel:
        extra = f' data-rig-opacity="{channel}"' + (' data-rig-default="1"' if default_on else "")
    svg.part(group_id, label, name, bone, z, body, extra)


def document(*, design, layer_id, label, comment, joints, size=(560, 560)):
    return svg.document(size=size, design=design, layer_id=layer_id, label=label, comment=comment,
                        joints=svg.joints_layer(joints))
