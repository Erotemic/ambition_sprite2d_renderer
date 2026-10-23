#!/usr/bin/env python3
"""The News Board v2: the talking notice board, and its three candidate looks.

    uv run python scripts/svg_art/news_board_art.py                # the cast SVG (look A, front)
    uv run python scripts/build_news_board_v2_rig.py               # then its rig
    uv run python scripts/svg_art/news_board_art.py --all DIR      # every view of every look, to DIR
    uv run python scripts/svg_art/news_board_art.py --sheet PNG    # the contact sheet of the looks

Jon, 2026-10-22: redesigned art for "the news board". He saw the three looks
and did not pick; on 2026-10-23 he asked to see the new art in the game. Look A
(``market``) is cast: the board stands on the street of the Drain Market
(``drain_alley``), where a board of planks on old drain pipes belongs. The cast
SVG is ``data/characters/news_board_v2/news_board_v2.svg`` (the front view);
the target is ``targets/props/news_board_v2.py``. The old procedural board
(``targets/props/news_board.py``, a purple "Disruptor Industries" cork board)
stays renderable. B and C are KEPT, NOT CAST.

The cast parts: the horn turns on its bracket (bone ``horn``) and its two rings
of sound show in turn when it talks (``voice_near``, ``voice_far``); the loose
pink slip is taped at its top only and lifts in a draught (bone ``slip``).

WHAT IT IS.  ``npc_news_board`` (``prop_like``, ``stand_still``): a board that
TALKS, in the Drain Market (``drain_alley``: "Read the news board" ->
``news_board_lab_incident``, signed "Drain Market Bulletin") and in the Hall.
Its voice is cheerful official spin: "BREAKING: LAB WALL COLLAPSES. OTHER WALLS
REMAIN EMPLOYED.", "Smoke cleared of all wrongdoing.", "Eyewitness disagreement
received. Filing under OPINION.", "the researcher was posthumously added to a
valid target list". So every look carries:

* a VOICE: a public-address horn -- the thing that talks, and the part a talk
  row can shake; and
* its news as PICTURES, never words (nothing to translate): the lab wall with
  a hole in it, a smoke cloud wearing a halo ("cleared"), a researcher in a
  target's crosshair, a red rubber stamp. Headlines are bars of ink.

THE LOOKS.
* ``market`` (A): the Drain Market's own board -- planks on two old drain
  pipes, a pitched corrugated-tin roof, a cork field of pinned notices, a horn wired
  to the roof.
* ``kiosk`` (B): the official version, after the old art's purple corporate
  kiosk -- a steel slab with a lit header, a broadcast screen (the BREAKING
  bar, the wall picture), a ticker, a speaker grille, a slot that prints
  bulletins, and a camera watching the reader.
* ``column`` (C): an advertising column (a Litfass pillar) pasted over with
  bulletins, its iron cap crowned by a yoke of two PA horns.

Views: ``front`` and ``tq`` (three-quarter, turned toward screen-right). Both
are the SAME geometry seen through a small perspective camera (``Cam``), so
the turnaround agrees with itself. House style: Oiler's (``oiler_art.py``):
thin warm ink, flat cel fills, one shade band below-left, one light band
above-right. No drop shadow.
"""
from __future__ import annotations

import io
import math
import re
import sys
from pathlib import Path
from typing import Callable, Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import svgkit as svg  # noqa: E402
from svgkit import ellipse, line, part, path, smooth  # noqa: E402

W = H = 560
INK = "#1d1714"
OW = 1.5
GROUND_Y = 502.0
SD, LD = (-1.0, 0.6), (1.0, -0.8)

BASE = dict(
    paper="#ece6d6", paper_sh="#cfc6b0", paper_lt="#f8f4ea",
    yellow="#efd27a", yellow_sh="#d0b05a", yellow_lt="#f8e5a6",
    pink="#e7b9b2", pink_sh="#c99a93", pink_lt="#f3d3cd",
    blue="#c9d6e6", blue_sh="#a5b4c8", blue_lt="#e2eaf3",
    text="#4a4650", red="#c0392b", red_sh="#8e2a20", brick="#b05a3c", brick_sh="#86412b",
    smoke="#9a9aa2", smoke_sh="#76767e", halo="#f2cf4a", coat="#f4f2ec", target="#c62f2f",
    horn="#8d969c", horn_sh="#646c73", horn_lt="#b2bac0", horn_mouth="#2a2a30",
    brass="#c9a24a", brass_sh="#97762e", brass_lt="#e6c672",
)
LOOKS: Dict[str, Dict] = {
    "market": dict(
        label="A: Drain Market board (planks on drain pipes, pitched tin roof, pinned notices, PA horn)",
        wood="#7d5b3c", wood_sh="#573e28", wood_lt="#9c7853",
        cork="#b98a5a", cork_sh="#966b42", cork_lt="#cda177",
        pipe="#5f7a78", pipe_sh="#41585a", pipe_lt="#80a09b", rust="#a0522d",
        tin="#8d969c", tin_sh="#646c73", tin_lt="#b2bac0",
    ),
    "kiosk": dict(
        label="B: Official kiosk (steel slab, broadcast screen, ticker, speaker, printed slips, camera)",
        steel="#4b4f5e", steel_sh="#33363f", steel_lt="#666b7c",
        head="#4a2a6e", head_sh="#331c4e", head_lt="#6a44a0", logo="#e8d7ff",
        screen="#14222f", screen_sh="#0c151d", screen_lt="#24405a", glow="#3c6d93",
        ticker="#f2b33d", led="#5bffa8",
    ),
    "column": dict(
        label="C: Advertising column (pasted bulletins, iron cap, a yoke of PA horns)",
        iron="#2f5a45", iron_sh="#1f3f30", iron_lt="#477a60",
        drum="#d8ccb0", drum_sh="#b7aa8c", drum_lt="#e8dfca",
    ),
}
O: Dict = {}
_N = [0]


def use(look: str) -> None:
    O.clear()
    O.update(BASE)
    O.update(LOOKS[look])
    O["look"] = look


def uid(tag="c"):
    _N[0] += 1
    return f"nb{tag}{_N[0]}"


def cel(d, base, shade, light=None, items=(), sdir=SD, ldir=LD, s=5.0, l=3.0, sw=None, ink=None, edges=None):
    """oiler_art.py's cel shape (copied): fill, a shade band toward ``sdir``, a
    light band toward ``ldir``, the ``items`` clipped inside, the ink."""
    cid = uid()
    sx, sy = -sdir[0] * s, -sdir[1] * s
    out = [f'<clipPath id="{cid}"><path d="{d}" /></clipPath>',
           f'<clipPath id="{cid}s"><path d="{d}" transform="translate({sx:.2f} {sy:.2f})" /></clipPath>',
           f'<g clip-path="url(#{cid})">', path(d, shade), f'<g clip-path="url(#{cid}s)">']
    if light:
        lx, ly = -ldir[0] * l, -ldir[1] * l
        out += [path(d, light), path(d, base, extra=f' transform="translate({lx:.2f} {ly:.2f})"')]
    else:
        out.append(path(d, base))
    out.append("</g>")
    out += list(items)
    out.append("</g>")
    if edges is None:
        out.append(path(d, "none", ink or INK, sw or 2 * OW))
    else:
        out += [line(run, ink or INK, sw or 2 * OW) for run in edges]
    return out


def C(d, key, items=(), **kw):
    return cel(d, O[key], O[key + "_sh"], O.get(key + "_lt"), items, **kw)


def poly(pts):
    return smooth([tuple(p[:2]) + (True,) for p in pts])


# ============================================================================================
# THE CAMERA: one geometry, two views
# ============================================================================================

class Cam:
    """World: X across (0 at the board's middle), Y down (the ground at 502),
    Z away from the viewer.  The prop turns by ``turn`` degrees about the
    vertical axis, then a camera at eye height ``eye`` and distance ``dist``
    projects it (a mild perspective)."""

    def __init__(self, turn=0.0, eye=300.0, dist=1500.0, cx=280.0):
        self.t = math.radians(turn)
        self.eye, self.dist, self.cx = eye, dist, cx

    def rot(self, X, Z):
        c, s = math.cos(self.t), math.sin(self.t)
        return X * c + Z * s, -X * s + Z * c

    def __call__(self, X, Y, Z=0.0):
        Xr, Zr = self.rot(X, Z)
        k = self.dist / (self.dist + Zr)
        return (self.cx + Xr * k, self.eye + (Y - self.eye) * k)

    def facing(self, nx, nz, X=0.0, Y=0.0, Z=0.0):
        """True when a face with outward normal (nx, 0, nz) at (X, Y, Z) is seen."""
        Xr, Zr = self.rot(X, Z)
        nxr, nzr = self.rot(nx, nz)
        return nxr * (Xr - 0.0) + nzr * (Zr + self.dist) < 0


CAM = [Cam()]


def P3(X, Y, Z=0.0):
    return CAM[0](X, Y, Z)


def P3c(Xr, Y, Zr=0.0):
    """A point given in the CAMERA's frame (for what turns with the eye, not the
    prop: a round thing's outline)."""
    c, s = math.cos(CAM[0].t), math.sin(CAM[0].t)
    return P3(Xr * c - Zr * s, Y, Xr * s + Zr * c)


def plane(X0, Y0, Z0, ax=(1.0, 0.0)):
    """A flat surface's mapper: local (u, v) -> screen, u along ``ax`` (in the
    X-Z plane) from (X0, Y0, Z0), v down."""
    return lambda u, v: P3(X0 + u * ax[0], Y0 + v, Z0 + u * ax[1])


def cyl(cxw, czw, r, phi0_deg):
    """A cylinder's surface mapper: local (u, v) -> screen, u running round
    the drum (arc length) from the angle ``phi0`` (0 faces the viewer when the
    prop is not turned), v down from 0 = world Y."""
    def M(u, v):
        phi = math.radians(phi0_deg) + u / r
        t = CAM[0].t  # a point round the back is pressed onto the visible rim
        phi = t + max(-math.radians(89), min(math.radians(89), phi - t))
        return P3(cxw + r * math.sin(phi), v, czw - r * math.cos(phi))
    return M


def box(x0, x1, y0, y1, z0, z1, key, front_items=(), s=4, faces=("front", "left", "right", "top", "bottom")):
    """A box: its visible faces, each a cel shape in the key's tones (the
    front in the base, the sides in shade, the top in light)."""
    F = {
        "front": ([(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)], (0, -1), (O[key], O[key + "_sh"], O.get(key + "_lt"))),
        "left": ([(x0, y0, z1), (x0, y0, z0), (x0, y1, z0), (x0, y1, z1)], (-1, 0), (O[key + "_sh"], O[key + "_sh"], None)),
        "right": ([(x1, y0, z0), (x1, y0, z1), (x1, y1, z1), (x1, y1, z0)], (1, 0), (O[key + "_sh"], O[key + "_sh"], None)),
    }
    out = []
    for name in faces:
        if name not in F:
            continue
        pts, (nx, nz), (b, sh, lt) = F[name]
        cxm = sum(p[0] for p in pts) / 4
        czm = sum(p[2] for p in pts) / 4
        if not CAM[0].facing(nx, nz, cxm, 0, czm):
            continue
        d = poly([P3(*p) for p in pts])
        out += cel(d, b, sh, lt, front_items if name == "front" else (), s=s if name == "front" else 1.5, sw=2 * OW)
    # the top or the underside, whichever the eye sees
    if "top" in faces and y0 > CAM[0].eye:
        d = poly([P3(x0, y0, z1), P3(x1, y0, z1), P3(x1, y0, z0), P3(x0, y0, z0)])
        out += cel(d, O.get(key + "_lt") or O[key], O[key], None, [], s=1, sw=2 * OW)
    if "bottom" in faces and y1 < CAM[0].eye:
        d = poly([P3(x0, y1, z0), P3(x1, y1, z0), P3(x1, y1, z1), P3(x0, y1, z1)])
        out += cel(d, O[key + "_sh"], O[key + "_sh"], None, [], s=1, sw=2 * OW)
    return out


def vcyl(xw, zw, r, y0, y1, key, items=(), n=24, s=None):
    """An upright cylinder from y0 (top) to y1 (bottom), its silhouette with the
    front halves of its end ellipses."""
    eye = CAM[0].eye
    # each end shows the half of its rim that lies farther from the eye line:
    # below the eye the bottom's NEAR half and the top's FAR half, above it the reverse
    zb = -1.0 if y1 > eye else 1.0
    zt = 1.0 if y0 > eye else -1.0
    c, s_ = math.cos(CAM[0].t), math.sin(CAM[0].t)

    def rim(y, xr, zr):  # a rim point given in the CAMERA's frame, back to the world's
        return P3(xw + xr * c - zr * s_, y, zw + xr * s_ + zr * c)
    bot = [rim(y1, -r * math.cos(math.pi * i / n), zb * r * math.sin(math.pi * i / n)) for i in range(n + 1)]
    top = [rim(y0, r * math.cos(math.pi * i / n), zt * r * math.sin(math.pi * i / n)) for i in range(n + 1)]
    d = poly(bot + top)
    out = cel(d, O[key], O[key + "_sh"], O.get(key + "_lt"), items, sdir=(-1, 0), ldir=(1, 0), s=s or r * 0.35, l=r * 0.25)
    if y0 > eye:  # the top face, seen from above
        rim = [P3(xw + r * math.cos(2 * math.pi * i / (2 * n)), y0, zw + r * math.sin(2 * math.pi * i / (2 * n))) for i in range(2 * n)]
        out += cel(poly(rim), O.get(key + "_lt") or O[key], O[key], None, [], s=1, sw=1.4)
    return out


def ring_pts(M, cu, cv, r, n=18, ry=None):
    ry = ry if ry is not None else r
    return [M(cu + r * math.cos(2 * math.pi * i / n), cv + ry * math.sin(2 * math.pi * i / n)) for i in range(n)]


def quad(M, u0, v0, u1, v1, n=1):
    """A rectangle in a surface's local units, subdivided along u (so a drum
    bends it)."""
    top = [M(u0 + (u1 - u0) * i / n, v0) for i in range(n + 1)]
    bot = [M(u1 - (u1 - u0) * i / n, v1) for i in range(n + 1)]
    return top + bot


# ============================================================================================
# THE NEWS, AS PICTURES (local poster units; M maps them onto the surface)
# ============================================================================================

def text_lines(M, u0, v0, u1, n, gap=6.0, w=2.2, color=None, seed=0):
    """Lines of copy: grey bars of uneven length, the last one short."""
    out = []
    for i in range(n):
        frac = 1.0 if i < n - 1 else 0.55
        jag = 0.08 * math.sin((i + seed) * 2.7)
        out.append(line([M(u0, v0 + i * gap), M(u0 + (u1 - u0) * (frac - abs(jag)), v0 + i * gap)], color or O["text"], w))
    return out


def headline(M, u0, v0, u1, h=6.0):
    """A headline: two fat ink bars, the second shorter (a word broken off)."""
    return [path(poly([M(u0, v0), M(u0 + (u1 - u0) * 0.62, v0), M(u0 + (u1 - u0) * 0.62, v0 + h), M(u0, v0 + h)]), INK),
            path(poly([M(u0 + (u1 - u0) * 0.68, v0), M(u1, v0), M(u1, v0 + h), M(u0 + (u1 - u0) * 0.68, v0 + h)]), INK)]


def picto_wall(M, u0, v0, w, h):
    """The lab wall with a hole torn in it: courses of brick, a ragged gap."""
    out = [path(poly([M(u0, v0), M(u0 + w, v0), M(u0 + w, v0 + h), M(u0, v0 + h)]), "#2c2a33")]
    rows = 5
    bh = h / rows
    gap = [(0.38, 0.0), (0.62, 0.0), (0.70, 0.2), (0.62, 0.42), (0.74, 0.62), (0.64, 1.0), (0.30, 1.0), (0.40, 0.7), (0.26, 0.46), (0.36, 0.22)]
    for r in range(rows):
        off = 0.5 if r % 2 else 0.0
        bw = w / 3.5
        k = -1
        while True:
            k += 1
            a = (k - off) * bw
            b = a + bw
            if a >= w:
                break
            a, b = max(a, 0), min(b, w)
            mid = (a + b) / 2 / w
            vmid = (r + 0.5) / rows
            if 0.30 < mid < 0.70 and 0.0 < vmid < 1.0 and not (mid < 0.36 and vmid > 0.7):
                continue
            out.append(path(poly([M(u0 + a + 0.6, v0 + r * bh + 0.6), M(u0 + b - 0.6, v0 + r * bh + 0.6), M(u0 + b - 0.6, v0 + (r + 1) * bh - 0.6),
                                  M(u0 + a + 0.6, v0 + (r + 1) * bh - 0.6)]), O["brick"]))
    out.append(line([M(u0 + w * p[0], v0 + h * p[1]) for p in gap] + [M(u0 + w * gap[0][0], v0 + h * gap[0][1])], O["paper"], 1.4))
    # the falling bricks
    for du, dv, rot in ((0.52, 0.48, 0.3), (0.46, 0.78, -0.4)):
        cu, cv = u0 + w * du, v0 + h * dv
        q = [(-3.2, -1.6), (3.2, -1.6), (3.2, 1.6), (-3.2, 1.6)]
        out.append(path(poly([M(cu + x * math.cos(rot) - y * math.sin(rot), cv + x * math.sin(rot) + y * math.cos(rot)) for x, y in q]), O["brick"],
                        INK, 0.8))
    return out


def picto_smoke_halo(M, cu, cv, k=1.0):
    """Smoke, cleared of all wrongdoing: a grey cloud wearing a halo."""
    out = [path(smooth(ring_pts(M, cu, cv - 21 * k, 11 * k, ry=3.4 * k)), "none", INK, 3.8),
           path(smooth(ring_pts(M, cu, cv - 21 * k, 11 * k, ry=3.4 * k)), "none", O["halo"], 2.2)]
    puffs = [(-9, 2, 7), (0, -4, 9), (9, 1, 7.5), (3, 6, 6), (-4, 7, 5.5)]
    blob = []
    for i in range(36):
        a = 2 * math.pi * i / 36
        best = max(((px + pr * math.cos(a), py + pr * math.sin(a)) for px, py, pr in puffs), key=lambda q: q[0] * math.cos(a) + q[1] * math.sin(a))
        blob.append(M(cu + best[0] * k, cv + best[1] * k))
    out += cel(smooth(blob), O["smoke"], O["smoke_sh"], "#b9b9c0", [line([M(cu - 6 * k, cv - 1 * k), M(cu + 2 * k, cv - 5 * k)], "#c4c4ca", 1.2)], s=2.5,
               sw=1.4)
    # the face of an innocent cloud: two closed, content eyes
    out += [line([M(cu - 5 * k, cv + 1 * k), M(cu - 3 * k, cv - 0.6 * k), M(cu - 1 * k, cv + 1 * k)], INK, 1.1),
            line([M(cu + 2 * k, cv + 1 * k), M(cu + 4 * k, cv - 0.6 * k), M(cu + 6 * k, cv + 1 * k)], INK, 1.1)]
    return out


def picto_target(M, cu, cv, k=1.0):
    """The researcher, posthumously added to the list: a head and shoulders in a
    lab coat with goggles pushed up, under a red crosshair."""
    out = []
    shoulders = [M(cu - 14 * k, cv + 18 * k), M(cu - 12 * k, cv + 8 * k), M(cu - 5 * k, cv + 4 * k), M(cu + 5 * k, cv + 4 * k), M(cu + 12 * k, cv + 8 * k),
                 M(cu + 14 * k, cv + 18 * k)]
    out += cel(smooth(shoulders, closed=True), O["coat"], "#c9c6be", None, [line([M(cu, cv + 4 * k), M(cu, cv + 18 * k)], "#a9a59c", 1.0)], s=1.5, sw=1.4)
    out += cel(smooth(ring_pts(M, cu, cv - 3 * k, 6.4 * k)), "#5a5560", "#46424c", None, [], s=1, sw=1.4)
    out += [path(smooth(ring_pts(M, cu, cv - 8 * k, 5 * k, ry=1.6 * k)), "#9fc3d6", INK, 0.9)]
    ring = ring_pts(M, cu, cv + 1 * k, 15 * k)
    out += [path(smooth(ring), "none", O["target"], 2.0),
            line([M(cu - 19 * k, cv + 1 * k), M(cu - 9 * k, cv + 1 * k)], O["target"], 1.8), line([M(cu + 9 * k, cv + 1 * k), M(cu + 19 * k, cv + 1 * k)], O["target"], 1.8),
            line([M(cu, cv - 18 * k), M(cu, cv - 12 * k)], O["target"], 1.8)]
    return out


def picto_stamp(M, cu, cv, k=1.0, rot=-0.22):
    """A red rubber stamp, slapped on crooked: a double border and a scrawl --
    FILED UNDER OPINION, without the words."""
    def R(x, y):
        return M(cu + (x * math.cos(rot) - y * math.sin(rot)) * k, cv + (x * math.sin(rot) + y * math.cos(rot)) * k)
    out = [path(poly([R(-17, -8), R(17, -8), R(17, 8), R(-17, 8)]), "none", O["red"], 1.8),
           path(poly([R(-14.5, -5.5), R(14.5, -5.5), R(14.5, 5.5), R(-14.5, 5.5)]), "none", O["red"], 0.9),
           line([R(-11, 1), R(-7, -3), R(-3, 2), R(1, -3), R(5, 2), R(9, -2), R(11, 0)], O["red"], 1.6)]
    return out


def picto_official(M, cu, cv, k=1.0):
    """An official, beaming: a round face with a wide smile, a tie, a lapel pin."""
    out = []
    body = [M(cu - 15 * k, cv + 20 * k), M(cu - 13 * k, cv + 9 * k), M(cu, cv + 5 * k), M(cu + 13 * k, cv + 9 * k), M(cu + 15 * k, cv + 20 * k)]
    out += cel(smooth(body), "#3d4660", "#2b3247", None, [path(poly([M(cu - 2 * k, cv + 7 * k), M(cu + 2 * k, cv + 7 * k), M(cu + 1.4 * k, cv + 19 * k),
                                                                       M(cu - 1.4 * k, cv + 19 * k)]), O["red"])], s=1.5, sw=1.4)
    out += cel(smooth(ring_pts(M, cu, cv - 3 * k, 9 * k, ry=9.6 * k)), "#e7bf9c", "#c99a78", None, [
        line([M(cu - 5 * k, cv - 1 * k), M(cu, cv + 3 * k), M(cu + 5 * k, cv - 1 * k)], INK, 1.3),
        ellipse(*M(cu - 3.4 * k, cv - 5 * k), 1.1, 1.1, INK), ellipse(*M(cu + 3.4 * k, cv - 5 * k), 1.1, 1.1, INK)], s=2, sw=1.4)
    out += [path(smooth(ring_pts(M, cu, cv - 9.5 * k, 9 * k, ry=3 * k)), "#6b6158", INK, 1.0)]
    return out


def pin(M, u, v, color=None):
    x, y = M(u, v)
    return [ellipse(x, y, 2.2, 2.2, color or O["red"], INK, 0.9), ellipse(x - 0.6, y - 0.7, 0.7, 0.7, "#f6d0c8")]


def tape(M, u, v, rot=0.5, L=12.0):
    c, s = math.cos(rot), math.sin(rot)
    pts = [(-L / 2, -2.4), (L / 2, -2.4), (L / 2, 2.4), (-L / 2, 2.4)]
    return [path(poly([M(u + x * c - y * s, v + x * s + y * c) for x, y in pts]), "#e9ddb0", "#b9ab7a", 0.6, extra=' fill-opacity="0.85"')]


def sheet(M, u0, v0, u1, v1, key, items=(), n=1, curl=0.0):
    """A pinned sheet of paper in the tones of ``key``, its contents clipped to it."""
    pts = quad(M, u0, v0, u1, v1, n)
    if curl:  # a lifted bottom-right corner
        pts[n + 1] = M(u1 - curl, v1 - curl * 0.4)
    return cel(poly(pts), O[key], O[key + "_sh"], O.get(key + "_lt"), items, s=2, l=1.5, sw=1.6)


def tabs(M, u0, u1, v, n, h=11.0, key="paper"):
    """Tear-off tabs along a notice's foot (one already torn away)."""
    out = []
    w = (u1 - u0) / n
    for i in range(n):
        if i == n - 2:
            continue
        a = u0 + i * w + 0.6
        out += cel(poly([M(a, v), M(a + w - 1.2, v), M(a + w - 1.2, v + h), M(a, v + h)]), O[key], O[key + "_sh"], None,
                   [line([M(a + w / 2 - 0.6, v + 2), M(a + w / 2 - 0.6, v + h - 2)], O["text"], 1.0)], s=1, sw=1.0)
    return out


def front_page(M, u0, v0, w, h):
    """The front page: the masthead bar, the headline, the wall picture, copy."""
    items = [path(poly([M(u0 + 4, v0 + 4), M(u0 + w - 4, v0 + 4), M(u0 + w - 4, v0 + 11), M(u0 + 4, v0 + 11)]), INK),
             line([M(u0 + 6, v0 + 7.5), M(u0 + w * 0.3, v0 + 7.5)], O["paper"], 1.2), line([M(u0 + w * 0.6, v0 + 7.5), M(u0 + w - 6, v0 + 7.5)], O["paper"], 1.2)]
    items += headline(M, u0 + 5, v0 + 15, u0 + w - 5, 5.5)
    pw, ph = w - 10, h * 0.42
    items += picto_wall(M, u0 + 5, v0 + 25, pw, ph)
    items += text_lines(M, u0 + 5, v0 + 29 + ph, u0 + w * 0.48, 4, gap=5.4, w=1.8)
    items += text_lines(M, u0 + w * 0.54, v0 + 29 + ph, u0 + w - 5, 4, gap=5.4, w=1.8, seed=2)
    return items


# ============================================================================================
# THE HORN: the board's voice (a public-address horn on a bracket)
# ============================================================================================

def horn(base, aim_deg, L=34.0, mouth=13.0, open_k=0.55):
    """A PA horn from its driver at ``base`` (screen units) toward ``aim``
    (degrees, screen; 0 = right): a can-shaped driver, a flaring cone, and its
    bell's rim seen at ``open_k`` (0 edge-on, 1 straight into it)."""
    a = math.radians(aim_deg)
    q = lambda t, s: (base[0] + math.cos(a) * t - math.sin(a) * s, base[1] + math.sin(a) * t + math.cos(a) * s)
    out = []
    driver = [q(-9, -6.4), q(2, -6.4), q(2, 6.4), q(-9, 6.4)]
    out += cel(smooth([p + (True,) for p in driver]), O["horn_sh"], "#4a5157", None, [], s=1.5)
    cone = [q(0, -3.6), q(L * 0.55, -mouth * 0.42), q(L, -mouth), q(L, mouth), q(L * 0.55, mouth * 0.42), q(0, 3.6)]
    out += cel(smooth([cone[0] + (True,), cone[1], cone[2] + (True,), cone[3] + (True,), cone[4], cone[5] + (True,)]), O["horn"], O["horn_sh"], O["horn_lt"],
               [line([q(4, -2.6), q(L - 3, -mouth + 3)], O["horn_lt"], 1.3)], s=3)
    rim = [q(L + mouth * open_k * math.cos(t), mouth * math.sin(t)) for t in [2 * math.pi * i / 20 for i in range(20)]]
    out += [path(smooth(rim), O["horn_lt"], INK, 2 * OW)]
    inner = [q(L + mouth * open_k * 0.72 * math.cos(t), mouth * 0.72 * math.sin(t)) for t in [2 * math.pi * i / 20 for i in range(20)]]
    out += [path(smooth(inner), O["horn_mouth"], INK, 1.0)]
    return out


# ============================================================================================
# A: THE DRAIN MARKET BOARD
# ============================================================================================

def market_parts():
    out: Dict[str, List[str]] = {}
    # the posts: two old drain pipes, flanged, rust weeping from the joints
    posts = []
    for xw in (-74.0, 74.0):
        items = [line([P3(xw - 3, 330), P3(xw - 3, 360)], O["rust"], 2.0), line([P3(xw + 2, 430), P3(xw + 2, 452)], O["rust"], 1.6)]
        posts += vcyl(xw, 14, 7.5, 188, 498, "pipe", items)
        for yy in (340.0, 482.0):  # the flanges
            posts += vcyl(xw, 14, 10.5, yy, yy + 9, "pipe")
    out["posts"] = posts
    # the board: a plank frame round a cork field
    bx0, bx1, by0, by1 = -92.0, 92.0, 214.0, 418.0
    out["board"] = box(bx0, bx1, by0, by1, 0, 12, "wood", [
        line([P3(bx0 + 2, by0 + 10), P3(bx1 - 2, by0 + 10)], O["wood_sh"], 1.2),
        line([P3(bx0 + 2, by1 - 10), P3(bx1 - 2, by1 - 10)], O["wood_sh"], 1.2),
        line([P3(bx0 + 30, by0 + 3), P3(bx0 + 52, by0 + 4)], O["wood_lt"], 1.2),
        line([P3(bx1 - 40, by1 - 5), P3(bx1 - 12, by1 - 6)], O["wood_lt"], 1.2),
    ] + [ellipse(*P3(x, y), 1.6, 1.6, "#3a3a3a") for x in (bx0 + 6, bx1 - 6) for y in (by0 + 6, by1 - 6)])
    M = plane(0, 0, -0.5)
    cork = quad(M, bx0 + 10, by0 + 12, bx1 - 10, by1 - 12)
    flecks = [ellipse(*M(bx0 + 14 + (i * 37) % 160, by0 + 18 + (i * 53) % 170), 1.0, 0.8, O["cork_sh"]) for i in range(40)]
    out["cork"] = cel(poly(cork), O["cork"], O["cork_sh"], O["cork_lt"], flecks, s=4, sw=1.6)
    # the notices
    n = []
    n += sheet(M, -78, 228, 8, 334, "paper", front_page(M, -78, 228, 86, 106), curl=5)
    n += pin(M, -72, 233) + pin(M, 3, 233, "#3f6fb5")
    n += sheet(M, 16, 226, 80, 288, "yellow", [*picto_smoke_halo(M, 48, 266, 1.05)] + headline(M, 22, 232, 74, 4.5))
    n += tape(M, 48, 227, 0.08, 16)
    n += sheet(M, 20, 296, 80, 404, "paper", [path(poly([M(20, 296), M(80, 296), M(80, 306), M(20, 306)]), O["red"]),
                                                *picto_target(M, 50, 340, 1.12)] + text_lines(M, 26, 368, 74, 3, gap=5.4, w=1.8) +
                [line([M(25, 390), M(56, 390)], INK, 2.4)])
    n += pin(M, 24, 300, "#e0b84e") + pin(M, 76, 300, "#e0b84e")
    n += sheet(M, -80, 342, -24, 382, "blue", text_lines(M, -74, 352, -30, 4, gap=6, w=1.8) + headline(M, -74, 345, -32, 3.6))
    n += tabs(M, -80, -24, 382, 6, key="blue")
    n += pin(M, -52, 346)
    n += picto_stamp(M, -26, 316, 1.0)
    out["notices"] = n
    # the loose slip: taped at its top only, so it lifts in a draught (its own bone)
    out["slip"] = sheet(M, -16, 344, 12, 396, "pink", text_lines(M, -12, 352, 8, 6, gap=6.2, w=1.6, seed=4)) + tape(M, -2, 344, -0.4, 11)
    # the roof: a gable of planks under a pitched sheet of corrugated tin
    ex0, ex1, ey, apex, z0, z1 = -112.0, 112.0, 208.0, 166.0, -22.0, 26.0
    gable = poly([P3(-88, ey + 2, 0), P3(0, apex + 12, 0), P3(88, ey + 2, 0)])
    out["awning"] = cel(gable, O["wood"], O["wood_sh"], O["wood_lt"], [line([P3(-60, 204, 0), P3(60, 204, 0)], O["wood_sh"], 1.1),
                                                                       line([P3(-30, 192, 0), P3(30, 192, 0)], O["wood_sh"], 1.1)], s=3)
    for sgn in (-1, 1):  # each slope: its underside (seen from below), then its corrugated edge
        e0, e1 = (sgn * 112.0, ey), (0.0, apex)
        under = poly([P3(e0[0], e0[1], z0), P3(e1[0], e1[1], z0), P3(e1[0], e1[1], z1), P3(e0[0], e0[1], z1)])
        ribs = [line([P3(e0[0] + (e1[0] - e0[0]) * f, e0[1] + (e1[1] - e0[1]) * f, z0), P3(e0[0] + (e1[0] - e0[0]) * f, e0[1] + (e1[1] - e0[1]) * f, z1)],
                     "#4c535a", 1.0) for f in [i / 12 for i in range(1, 12)]]
        out["awning"] += cel(under, O["tin_sh"], "#4c535a", None, ribs, s=1)
    for sgn in (-1, 1):
        e0, e1 = (sgn * 112.0, ey), (0.0, apex)
        n = 12
        scal = []
        for i in range(n + 1):  # the scalloped front edge of the tin, wave by wave
            f = i / n
            x, y = e0[0] + (e1[0] - e0[0]) * f, e0[1] + (e1[1] - e0[1]) * f
            scal.append(P3(x, y + (3.0 if i % 2 else 0.0), z0))
        edge = [P3(e1[0], e1[1] - 9, z0), P3(e0[0], e0[1] - 9, z0)] + scal
        out["awning"] += cel(poly(edge), O["tin"], O["tin_sh"], O["tin_lt"],
                             [line([P3(e0[0] + (e1[0] - e0[0]) * f, e0[1] + (e1[1] - e0[1]) * f - 7, z0),
                                    P3(e0[0] + (e1[0] - e0[0]) * f, e0[1] + (e1[1] - e0[1]) * f + 1, z0)], O["tin_sh"], 1.0)
                              for f in [i / 12 for i in range(1, 12, 2)]] +
                             [line([P3(sgn * 70, ey - 13, z0), P3(sgn * 70 + sgn * 6, ey - 9, z0)], "#a0522d", 1.4)], s=2, sdir=(0, 1))
    out["awning"] += [line([P3(-52, 197, z0), P3(-50, 204, z0 + 2)], "#7fa0b0", 1.6), ellipse(*P3(-49.5, 208, z0 + 2), 1.5, 2.2, "#9cc0d0", INK, 0.7)]
    # the horn, bolted to the awning's left end, its cable looped down to the board
    hb = P3(-58, 170, -10)
    aim = -150 - math.degrees(CAM[0].t) * 0.6
    out["horn"] = [line([P3(-58, 186, -10), P3(-58, 172, -10)], "#3c3c42", 3.4)] + horn(hb, aim, L=32, mouth=12.5,
                                                                                         open_k=0.45 + 0.4 * abs(math.sin(CAM[0].t)))
    cable = [P3(-62, 176, -10), P3(-76, 186, -14), P3(-100, 214, -10), P3(-97, 232, -2), P3(-92, 240, -1)]
    out["cable"] = [line(cable, INK, 2.6), line(cable, "#3c3c42", 1.2)]
    # the voice: two rings of sound out of the bell, shown in turn while it talks
    out["voice-near"] = voice_arc(hb, aim, 32 + 9, 15.0)
    out["voice-far"] = voice_arc(hb, aim, 32 + 20, 21.0)
    return out


#: Where the horn turns (its bracket on the roof) and where the loose slip is taped.
MARKET_JOINTS = {"horn": (-58.0, 186.0, -10.0), "slip": (-2.0, 344.0, -0.5)}


def voice_arc(base, aim_deg, dist, half):
    """A ring of sound ``dist`` from the horn's driver along ``aim``: an inked
    arc ``half`` units each side, bowed away from the bell (authored, never a glow)."""
    a = math.radians(aim_deg)
    q = lambda t, s: (base[0] + math.cos(a) * t - math.sin(a) * s, base[1] + math.sin(a) * t + math.cos(a) * s)
    pts = [q(dist + 5.0 * (1 - (k / 6) ** 2), half * k / 6) for k in range(-6, 7)]
    return [line(pts, INK, 5.6), line(pts, O["paper_lt"], 2.8)]


MARKET_LAYERS = [("posts", "Posts", 2), ("board", "Board Frame", 10), ("cork", "Cork", 11), ("notices", "Notices", 20), ("slip", "Loose Slip", 21),
                 ("awning", "Awning", 30), ("cable", "Horn Cable", 39), ("horn", "Horn (the voice)", 40), ("voice-near", "Voice - Near Ring", 41),
                 ("voice-far", "Voice - Far Ring", 42)]


# ============================================================================================
# B: THE OFFICIAL KIOSK
# ============================================================================================

def kiosk_parts():
    out: Dict[str, List[str]] = {}
    x0, x1, y0, y1, z0, z1 = -66.0, 66.0, 170.0, 474.0, 0.0, 34.0
    out["plinth"] = box(-76, 76, 474, 501, -6, 40, "steel", [line([P3(-70, 480), P3(70, 480)], O["steel_lt"], 1.2)])
    seams = [line([P3(x0 + 4, 352), P3(x1 - 4, 352)], O["steel_sh"], 1.2), line([P3(x0 + 4, 430), P3(x1 - 4, 430)], O["steel_sh"], 1.2),
             line([P3(x1 - 8, 214), P3(x1 - 8, 466)], O["steel_lt"], 1.2)]
    seams += [ellipse(*P3(x, y), 1.4, 1.4, "#2a2c33") for x in (x0 + 6, x1 - 6) for y in (218, 346, 358, 424, 436, 466)]
    out["body"] = box(x0, x1, y0 + 40, y1, z0, z1, "steel", seams)
    # the lit header: a purple box with the corporate mark (an eye in a speech bubble)
    M = plane(0, 0, -2)
    hd = box(x0 - 4, x1 + 4, y0, y0 + 40, -2, z1 + 2, "head", [])
    logo = []
    bub = [M(-15, 177), M(15, 177), M(17, 180), M(17, 197), M(15, 200), M(-4, 200), M(-11, 206), M(-9, 200), M(-15, 200), M(-17, 197), M(-17, 180)]
    logo += [path(smooth(bub), O["logo"], INK, 1.2)]
    logo += [path(smooth([M(-10, 188.5, ), M(0, 182.5), M(10, 188.5), M(0, 194.5)]), O["head"]), ellipse(*M(0, 188.5), 3.2, 3.2, O["logo"]),
             ellipse(*M(0, 188.5), 1.5, 1.5, O["head"])]
    logo += [line([M(-56, 186), M(-28, 186)], O["head_lt"], 3.0), line([M(28, 192), M(56, 192)], O["head_lt"], 3.0)]
    out["header"] = hd + logo
    # the screen: the broadcast
    sx0, sx1, sy0, sy1 = -54.0, 54.0, 222.0, 326.0
    scr = [path(poly([M(sx0, sy0), M(sx1, sy0), M(sx1, sy1), M(sx0, sy1)]), O["screen"])]
    scr += [line([M(sx0 + 2, y), M(sx1 - 2, y)], O["screen_lt"], 0.7) for y in range(int(sy0) + 4, int(sy1), 5)]
    scr += picto_wall(M, -46, 232, 52, 50)
    scr += [path(poly([M(-46, 232), M(6, 232), M(6, 282), M(-46, 282)]), "none", O["glow"], 1.4)]
    scr += picto_smoke_halo(M, 30, 258, 0.82)
    # the BREAKING bar: red, with a white lightning flash and a headline in bars
    scr += [path(poly([M(sx0, 292), M(sx1, 292), M(sx1, 308), M(sx0, 308)]), O["red"]),
            path(poly([M(-49, 294), M(-43, 294), M(-46, 299.5), M(-42, 299.5), M(-50, 307), M(-47, 301), M(-51, 301)]), "#ffffff"),
            line([M(-36, 297.5), M(10, 297.5)], "#ffffff", 3.2), line([M(-36, 303.5), M(-6, 303.5)], "#f3c2c2", 2.4)]
    scr += [path(poly([M(sx0, 308), M(sx1, 308), M(sx1, sy1), M(sx0, sy1)]), "#1d3448")]
    scr += [line([M(sx0 + 6 + i * 14, 317), M(sx0 + 14 + i * 14, 317)], O["ticker"], 2.4) for i in range(7)]
    bezel = box(sx0 - 6, sx1 + 6, sy0 - 6, sy1 + 6, -4, 0, "steel", [])
    out["screen"] = bezel + cel(poly([M(sx0, sy0), M(sx1, sy0), M(sx1, sy1), M(sx0, sy1)]), O["screen"], O["screen_sh"], None, scr, s=2, sw=1.6)
    # the speaker grille (the voice) and the green LED
    g = []
    for r in range(4):
        for c in range(7):
            g.append(ellipse(*M(-27 + c * 9 + (4.5 if r % 2 else 0), 368 + r * 8), 2.2, 2.2, "#1b1d23"))
    grille = cel(poly([M(-36, 360), M(36, 360), M(36, 400), M(-36, 400)]), O["steel_sh"], "#262830", None, g, s=1.5, sw=1.6)
    grille += [ellipse(*M(48, 366), 2.6, 2.6, O["led"], INK, 1.0)]
    out["speaker"] = grille
    # the print slot, and today's slip curling out of it
    slot = [path(poly([M(-30, 440), M(30, 440), M(30, 446), M(-30, 446)]), "#15161b", INK, 1.4)]
    slip = [M(-22, 443), M(22, 443), M(23, 458), M(20, 468), M(14, 473), M(-16, 472), M(-21, 462)]
    slot += cel(smooth([slip[0] + (True,), slip[1] + (True,)] + slip[2:]), O["paper"], O["paper_sh"], O["paper_lt"],
                headline(M, -16, 449, 16, 3.2) + text_lines(M, -16, 457, 14, 2, gap=5, w=1.5), s=2, sw=1.5)
    slot += picto_stamp(M, 10, 466, 0.42, rot=-0.3)
    out["slot"] = slot
    # the camera on its arm, watching the reader
    cam_base = P3(x1 - 4, 172, 8)
    out["camera"] = [line([cam_base, (cam_base[0] + 12, cam_base[1] - 14)], "#3a3d48", 4.0)]
    cb = (cam_base[0] + 12, cam_base[1] - 14)
    a = math.radians(160)
    q = lambda t, s: (cb[0] + math.cos(a) * t - math.sin(a) * s, cb[1] + math.sin(a) * t + math.cos(a) * s)
    out["camera"] += cel(smooth([q(-6, -6) + (True,), q(18, -7) + (True,), q(18, 7) + (True,), q(-6, 6) + (True,)]), O["steel"], O["steel_sh"], O["steel_lt"],
                         [], s=2)
    out["camera"] += [ellipse(*q(19, 0), 3.4, 5.4, "#101218", INK, 1.2), ellipse(*q(19.6, -1.2), 1.0, 1.4, "#8fd0ff"),
                      ellipse(*q(2, -3.6), 1.4, 1.4, "#ff5050")]
    return out


KIOSK_LAYERS = [("plinth", "Plinth", 1), ("body", "Body", 10), ("header", "Lit Header", 12), ("screen", "Screen", 20), ("speaker", "Speaker (the voice)", 22),
                ("slot", "Print Slot", 24), ("camera", "Camera", 30)]


# ============================================================================================
# C: THE ADVERTISING COLUMN
# ============================================================================================

def column_parts():
    out: Dict[str, List[str]] = {}
    R = 54.0
    turn_deg = math.degrees(CAM[0].t)
    out["base"] = vcyl(0, 0, R + 8, 468, 501, "iron", [line([P3c(-R - 4, 476), P3c(R + 4, 476)], O["iron_lt"], 1.3)])
    out["base"] += vcyl(0, 0, R + 3, 460, 470, "iron")
    # the drum, pasted over: each bulletin is laid on the drum's own curve
    posters = []

    def poster(phi_deg, v0, w, h, key, content):
        if math.cos(math.radians(phi_deg) - CAM[0].t) < 0.2:
            return []  # round the back: not seen
        M = cyl(0, 0, R + 0.4, phi_deg)
        n = 6
        pts = quad(M, -w / 2, v0, w / 2, v0 + h, n)
        return cel(poly(pts), O[key], O[key + "_sh"], O.get(key + "_lt"), content(M), s=2, l=1.5, sw=1.6)
    posters += poster(-58, 206, 60, 120, "pink", lambda M: headline(M, -24, 214, 24, 5) + [*picto_official(M, 0, 252, 1.2)] +
                      text_lines(M, -22, 286, 22, 5, gap=6, w=1.8))
    posters += poster(2, 196, 74, 112, "paper", lambda M: front_page(M, -37, 196, 74, 112))
    posters += poster(58, 212, 58, 84, "yellow", lambda M: headline(M, -22, 220, 22, 4.5) + picto_smoke_halo(M, 0, 266, 1.15))
    posters += poster(-30, 334, 64, 110, "paper", lambda M: [path(poly(quad(M, -32, 334, 32, 346, 4)), O["red"])] + picto_target(M, 0, 380, 1.2) +
                      text_lines(M, -24, 410, 24, 4, gap=6, w=1.8))
    posters += poster(38, 316, 58, 130, "blue", lambda M: headline(M, -22, 326, 22, 4.5) + text_lines(M, -22, 340, 22, 12, gap=7, w=1.7, seed=3))
    posters += poster(-96, 300, 50, 120, "yellow", lambda M: text_lines(M, -18, 312, 18, 12, gap=8, w=1.8))
    posters += poster(96, 214, 50, 90, "pink", lambda M: text_lines(M, -18, 224, 18, 9, gap=8, w=1.8))
    stamp = picto_stamp(cyl(0, 0, R + 0.6, 14), 0, 304, 1.15, rot=-0.18)
    tape_l = tape(cyl(0, 0, R + 0.8, -14), 0, 336, 0.6, 14)
    paste = [line([cyl(0, 0, R, -80)(0, 452), cyl(0, 0, R, 80)(0, 452)], O["drum_sh"], 1.2)]
    out["drum"] = vcyl(0, 0, R, 180, 462, "drum", posters + stamp + tape_l + paste, s=10)
    # the iron cap: a ring moulding, a dome, a finial
    out["cap"] = vcyl(0, 0, R + 7, 168, 182, "iron", [line([P3c(-R - 4, 173), P3c(R + 4, 173)], O["iron_lt"], 1.2)])
    dome = [P3c(-R - 4, 170), P3c(-R + 6, 152), P3c(-30, 140), P3c(0, 135), P3c(30, 140), P3c(R - 6, 152), P3c(R + 4, 170)]
    out["cap"] += cel(smooth([dome[0] + (True,)] + dome[1:-1] + [dome[-1] + (True,)]), O["iron"], O["iron_sh"], O["iron_lt"],
                      [line([P3c(-20, 141), P3c(10, 138)], O["iron_lt"], 1.6)], s=5, sdir=(-1, 0))
    out["cap"] += vcyl(0, 0, 4.5, 96, 138, "iron")
    out["cap"] += cel(smooth(ring_pts(lambda u, v: P3c(u, v), 0, 92, 6, ry=6)), O["brass"], O["brass_sh"], O["brass_lt"], [], s=2)
    # the crown of horns: a pair on a yoke round the mast, aimed out and down
    # at the street either way (a round prop: they keep to the eye's frame)
    hs = [line([P3c(-12, 116), P3c(12, 116)], INK, 6.0), line([P3c(-12, 116), P3c(12, 116)], O["iron"], 3.0)]
    for sgn in (-1, 1):
        hs += horn(P3c(sgn * 10, 116), 90 - sgn * 72, L=30, mouth=12.0, open_k=0.42)
    out["horns"] = hs
    return out


COLUMN_LAYERS = [("horns_back", "Horns - Far", 1), ("base", "Plinth", 4), ("drum", "Drum and Bulletins", 10), ("cap", "Iron Cap", 20),
                 ("horns", "Horns (the voice)", 30)]


# ============================================================================================
# DOCUMENTS
# ============================================================================================

KINDS = {"market": (market_parts, MARKET_LAYERS), "kiosk": (kiosk_parts, KIOSK_LAYERS), "column": (column_parts, COLUMN_LAYERS)}
VIEWS = {"front": ("News Board - Front", 0.0), "tq": ("News Board - Three Quarter", -34.0)}


def svg_text(look: str, view: str) -> str:
    use(look)
    _N[0] = 0
    svg.configure(dx=0, dy=0, ink=INK, ow=OW, colors={})
    label, turn = VIEWS[view]
    CAM[0] = Cam(turn=turn)
    painter, layers = KINDS[look]
    drawn = painter()
    for group, plabel, z in layers:
        if drawn.get(group):
            part(group, plabel, group, "body", z, drawn[group])
    CAM[0] = Cam()
    base = P3(0, GROUND_Y)
    return svg.document(
        size=(W, H), design=f"news-board-{look}", layer_id="news-board", label=label,
        comment=[f"  <!-- CANDIDATE, NOT CAST: News Board, {O['label']}, {label} (2026-10-22); the ground at y={GROUND_Y:g}.",
                 "       Drawn by scripts/svg_art/news_board_art.py. -->"],
        joints=svg.joints_layer({"body": base}),
    )


# ============================================================================================
# THE CAST: look A, front view, as the rig's SVG
# ============================================================================================

ROOT = Path(__file__).resolve().parents[2]
CAST_LOOK = "market"
CAST_NAME = "news_board_v2"
CAST_VIEW = "News Board v2 - Front"
OUT = ROOT / "ambition_sprite2d_renderer" / "data" / "characters" / CAST_NAME / f"{CAST_NAME}.svg"
#: Each cast part: its bone, and its opacity channel ("" when always shown).
CAST_BONES = {"horn": ("horn", ""), "voice-near": ("horn", "voice_near"), "voice-far": ("horn", "voice_far"), "slip": ("slip", "")}


def cast_joints() -> Dict[str, Tuple[float, float]]:
    """Where the cast board's bones turn, in SVG units (front view)."""
    CAM[0] = Cam()
    J = {"body": P3(0, GROUND_Y)}
    J.update({name: P3(*xyz) for name, xyz in MARKET_JOINTS.items()})
    return J


def cast_svg_text() -> str:
    """The News Board's SVG: look A (the Drain Market board), seen from the front."""
    use(CAST_LOOK)
    _N[0] = 0
    svg.configure(dx=0, dy=0, ink=INK, ow=OW, colors={})
    CAM[0] = Cam()
    drawn = market_parts()
    for group, plabel, z in MARKET_LAYERS:
        bone, channel = CAST_BONES.get(group, ("body", ""))
        extra = f' data-rig-opacity="{channel}"' if channel else ""
        part(group, plabel, group.replace("-", "_"), bone, z, drawn[group], extra)
    return svg.document(
        size=(W, H), design="news-board-v2-market", layer_id="news-board-v2", label=CAST_VIEW,
        comment=[f"  <!-- The News Board v2: {O['label']}, seen from the front; the ground at y={GROUND_Y:g}.",
                 "       Look A, chosen 2026-10-23: the board stands in the Drain Market street (drain_alley).",
                 "       Drawn by scripts/svg_art/news_board_art.py; scripts/build_news_board_v2_rig.py rigs it. -->"],
        joints=svg.joints_layer(cast_joints()),
    )


# ============================================================================================
# THE CONTACT SHEET (tool venv: resvg_py + PIL)
# ============================================================================================

def raster(text: str, scale: float):
    import resvg_py
    from PIL import Image
    text = re.sub(r'width="[\d.]+mm" height="[\d.]+mm"', f'width="{W * scale:g}" height="{H * scale:g}"', text, count=1)
    text = text.replace('<g id="rig-joints"', '<g id="rig-joints" visibility="hidden"')
    data = resvg_py.svg_to_bytes(svg_string=text, skip_system_fonts=True)
    return Image.open(io.BytesIO(bytes(data))).convert("RGBA")


#: The game's scale: the cast is drawn ~360 units tall for ~96 px (Paul Diracula's frame).
GAME_PX_PER_UNIT = 96.0 / 368.0
#: The close-up of each look (design units): where its news is.
DETAIL = {"market": (180, 210, 300, 340), "kiosk": (214, 214, 346, 330), "column": (226, 186, 334, 330)}


def contact_sheet(out_png: Path, looks=None) -> None:
    from PIL import Image, ImageDraw, ImageFont
    looks = looks or list(LOOKS)
    BG = (216, 221, 229, 255)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 22)
    except OSError:
        font = ImageFont.load_default()
    S = 2.0
    fig_box = (140, 90, 420, 506)
    rows = []
    for look in looks:
        use(look)
        label = O["label"]
        front = raster(svg_text(look, "front"), S)
        tq = raster(svg_text(look, "tq"), S)
        crop = lambda im, b, k: im.crop(tuple(int(v * k) for v in b))
        DS = 4.0
        detail = crop(raster(svg_text(look, "front"), DS), DETAIL[look], DS)
        cols = [crop(front, fig_box, S), crop(tq, fig_box, S), detail]
        game = []
        for im in (front, tq):
            g = im.resize((round(W * S * GAME_PX_PER_UNIT / S), round(H * S * GAME_PX_PER_UNIT / S)), Image.LANCZOS)
            bb = g.getbbox()
            game.append(g.crop(bb))
        row_h = max(c.height for c in cols) + 56
        row_w = sum(c.width for c in cols) + 40 * len(cols) + 40 + sum(g.width for g in game) * 4 + 120
        row = Image.new("RGBA", (row_w, row_h), BG)
        ImageDraw.Draw(row).text((16, 10), label, fill=(30, 26, 30, 255), font=font)
        x = 20
        for c in cols:
            row.alpha_composite(c, (x, 50 + (row_h - 50 - c.height) // 2))
            x += c.width + 40
        for g in game:
            row.alpha_composite(g, (x, row_h - g.height - 20))
            x += g.width + 14
        x += 20
        for g in game:
            big = g.resize((g.width * 3, g.height * 3), Image.NEAREST)
            row.alpha_composite(big, (x, row_h - big.height - 20))
            x += big.width + 14
        rows.append(row)
    W_ = max(r.width for r in rows)
    out = Image.new("RGBA", (W_, sum(r.height for r in rows)), BG)
    y = 0
    for r in rows:
        out.alpha_composite(r, (0, y))
        y += r.height
    out_png.parent.mkdir(parents=True, exist_ok=True)
    out.convert("RGB").save(out_png)
    print(out_png)


def main() -> None:
    if len(sys.argv) > 2 and sys.argv[1] == "--all":
        out = Path(sys.argv[2])
        out.mkdir(parents=True, exist_ok=True)
        for look in LOOKS:
            for view in VIEWS:
                p = out / f"news_board_{look}_{view}.svg"
                p.write_text(svg_text(look, view), encoding="utf8")
                print(p)
        return
    if len(sys.argv) > 2 and sys.argv[1] == "--sheet":
        contact_sheet(Path(sys.argv[2]), sys.argv[3:] or None)
        return
    if len(sys.argv) == 1:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        tmp = OUT.with_suffix(".svg.tmp")
        tmp.write_text(cast_svg_text(), encoding="utf8")
        tmp.replace(OUT)
        print(f"wrote {OUT.relative_to(ROOT)}")
        return
    raise SystemExit("usage: news_board_art.py [--all DIR | --sheet PNG [look ...]]")


if __name__ == "__main__":
    main()
