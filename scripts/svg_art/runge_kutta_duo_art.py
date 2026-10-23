#!/usr/bin/env python3
"""Carl Runga and Martin Cutta, redesigned: the drawings of ``carl_runga_v2`` and ``martin_cutta_v2``.

    uv run python scripts/svg_art/runge_kutta_duo_art.py --rig          # the cast look's SVGs (then build_runge_kutta_v2_rig.py)
    uv run python scripts/svg_art/runge_kutta_duo_art.py --all DIR      # side + front SVG of every look
    uv run python scripts/svg_art/runge_kutta_duo_art.py --sheets DIR   # the contact sheets (resvg_py + PIL)

Jon, 2026-10-22: "need a new Carl Runga and Martin Cutta."  The pun duo on the
Runge-Kutta method: Carl Runge (1856-1927) and Martin Kutta (1867-1944).

CAST: look A (2026-10-23; Jon saw the three looks and did not pick, then asked
for the new art in the game).  ``--rig`` writes
``data/characters/<name>_v2/<name>_v2_{side,front}.svg``, the parts in the
README's layer contract, each on its bone, with the face's channels
(``eyes_shut``, ``mouth_open``); ``scripts/build_runge_kutta_v2_rig.py`` reads
the joints and the layers from here and authors the clips.  Looks B and C are
KEPT, NOT CAST.  The first designs (``_runge_kutta_duo.py``) still render.

WHO THEY ARE.  Runga is the name on the method and does the shouting: 183 cm,
broad and heavy (``slow_heavy``), the vigorous outdoorsman Runge was, with
Runge's full beard and bald dome.  Cutta is "the thin one": 173 cm, upright,
dry, the keeper of the coefficients, with Kutta's moustache.  Both dress c.
1900.  Each has three looks; the looks pair up as a duo (A with A ...):

* A, the Goettingen pair: Runga in a black frock coat over a wine waistcoat
  (grizzled brown beard, no hat); Cutta in a dove-grey lounge suit, high collar,
  pince-nez on a cord and the ledger of coefficients.
* B, the field pair: Runga the alpinist (loden Norfolk jacket, knickerbockers,
  Tyrolean hat, an alpenstock, a red-brown beard); Cutta the aerodynamicist of
  the Kutta-Joukowski lift (a linen duster, a motoring cap with goggles, a
  scarf, gauntlets and riding boots, an upturned moustache).
* C, the raiders: an older Runga with the white beard of his best-known
  photograph, in an Inverness cape and a homburg; Cutta in a black frock coat
  and a bowler with a furled umbrella.

House style: Oiler's (``oiler_art.py``): flat cel fills with one shade below-
left and a light band above-right, a thin warm ink line, adult proportions, no
drop shadow.  The side view faces right (his right side to the camera).
Hands, ``cel`` and the finger outline are copied from ``oiler_art.py``.

HOW IT IS BUILT.  The torso garments are written in body coordinates: in the
side view ``(u, y)`` with ``u`` 0 at the back and 1 at the front of the body
at height ``y``; in the front view ``(v, y)`` with ``v`` -1..1 across the body's
half width.  So one coat drawing fits both builds.  Heads are drawn in a
local frame about the eye (side) or between the eyes (front), scaled by the
character's head size.
"""
from __future__ import annotations

import io
import math
import sys
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent))
import svgkit as svg  # noqa: E402
from svgkit import capsule, line, part, path, smooth  # noqa: E402

W = H = 560
INK = "#1d1714"
OW = 1.5
GROUND_Y = 502.0
SD, LD = (-1.0, 0.6), (1.0, -0.8)

# ============================================================================================
# palette helpers
# ============================================================================================


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _hex(c):
    return "#" + "".join(f"{max(0, min(255, int(round(v)))):02x}" for v in c)


def dark(h, k=0.74):
    """The shade tone: darker and a touch cooler."""
    r, g, b = _rgb(h)
    return _hex((r * k * 0.97, g * k, b * k * 1.06 + 4))


def lite(h, k=0.2):
    r, g, b = _rgb(h)
    return _hex((r + (255 - r) * k, g + (255 - g) * k, b + (255 - b) * k * 0.85))


# ============================================================================================
# the two builds
# ============================================================================================

#: Side view: ``eye`` the eye, ``hk`` the head's scale; ``back``/``front`` the
#: body's outline (y, x) from the neck down; the joints.  Front view: ``hw``
#: the half width (y, w) from the neck down; the joints.
BUILDS = {
    "runga": dict(
        hk=1.0, eye=(299.0, 182.0), feye=(280.0, 182.0), hand=1.12, nb=226.0, sy=244.0, wy=322.0, hy=346.0, knee=420.0,
        back=[(222, 270), (236, 256), (256, 248), (290, 249), (322, 252), (346, 249), (420, 247)],
        front=[(222, 290), (236, 297), (256, 304), (290, 307), (322, 310), (346, 303), (420, 301)],
        n_arm=((272, 252), (268, 310), (281, 362)), f_arm=((268, 250), (263, 308), (272, 358)),
        n_leg=((283, 346), (287, 420), (283, 486)), f_leg=((266, 346), (264, 420), (256, 486)),
        r_up=(13.5, 11.8), r_fore=(11.2, 9.4), r_thigh=(15.5, 12.5), r_shin=(11.8, 9.8), toe=28,
        hw=[(222, 13), (236, 30), (250, 46), (280, 45), (322, 41), (346, 39), (420, 40)],
        fr_arm=((241, 254), (234, 310), (234, 362)), fr_leg=((265, 346), (264, 420), (264, 486)),
    ),
    "cutta": dict(
        hk=0.93, eye=(292.0, 202.0), feye=(280.0, 202.0), hand=1.0, nb=246.0, sy=262.0, wy=334.0, hy=356.0, knee=424.0,
        back=[(242, 268), (254, 259), (272, 254), (300, 255), (334, 257), (356, 254), (424, 253)],
        front=[(242, 286), (254, 291), (272, 296), (300, 297), (334, 296), (356, 294), (424, 293)],
        n_arm=((274, 268), (271, 322), (280, 370)), f_arm=((270, 266), (265, 320), (273, 366)),
        n_leg=((280, 356), (283, 424), (279, 486)), f_leg=((266, 356), (264, 424), (256, 486)),
        r_up=(11.0, 9.6), r_fore=(9.2, 7.8), r_thigh=(12.8, 10.6), r_shin=(9.8, 8.2), toe=25,
        hw=[(242, 11), (254, 25), (266, 40), (296, 37), (334, 31), (356, 31), (424, 32)],
        fr_arm=((246, 270), (241, 322), (241, 370)), fr_leg=((268, 356), (268, 424), (268, 486)),
    ),
}

SKIN = dict(skin="#e3b896", skin_sh="#c08f6e", skin_lt="#f2d3b8", skin_dk="#94634c", lip="#b97a6a", blush="#e5ab92")
SHIRT = dict(shirt="#efe9de", shirt_sh="#c8bfae", shirt_lt="#fbf8f2")

LOOKS: Dict[str, Dict[str, dict]] = {
    "runga": {
        "A": dict(label="A: Goettingen professor - frock coat, wine waistcoat, grizzled beard",
                  coat="#2c2b34", coat_lt="#45434f", facing="#1c1b21", vest="#7a2a34", trousers="#6c6a70", stripe="#55535a",
                  shoe="#201b18", beard="#6b5444", beard_lt="#8f7966", beard_sh="#4a3a30", grey="#a59a90",
                  coat_kind="frock", collar="wing", tie="#1e1d26", chain=True, legs="trousers", hat=None),
        "B": dict(label="B: alpinist - loden Norfolk jacket, knickerbockers, alpenstock",
                  coat="#5c6b3e", vest="#5c6b3e", knick="#8b7656", sock="#cfc3a2", sock_band="#5c6b3e", shoe="#5a3a24",
                  beard="#8a4f2c", beard_lt="#ad6c45", beard_sh="#5f3420", hat="tyrolean", hat_c="#4a5532", hat_band="#2e2a22",
                  feather="#c7b98f", coat_kind="norfolk", collar="soft", tie="#8f2f2b", legs="knickers", staff=True,
                  button="#3b2b1d"),
        "C": dict(label="C: the white-bearded elder - Inverness cape, homburg",
                  coat="#62564c", coat_lt="#7c6f63", vest="#3c3a40", trousers="#3b3a40", shoe="#1e1a18",
                  beard="#e6e1d8", beard_lt="#fbf8f2", beard_sh="#b3ab9f", hat="homburg", hat_c="#2f2e2c", hat_band="#1a1918",
                  coat_kind="inverness", collar="wing", tie="#4a2230", legs="trousers", check="#544a41", button="#2a2420"),
    },
    "cutta": {
        "A": dict(label="A: coefficient clerk - grey lounge suit, pince-nez, the ledger",
                  coat="#8a919b", vest="#8a919b", trousers="#8a919b", shoe="#1e1a18", hair="#3a2c24",
                  coat_kind="lounge", collar="high", tie="#1d1f2a", legs="trousers", pince=True, ledger=True,
                  stache="walrus", hat=None, button="#3a3d44"),
        "B": dict(label="B: aerodynamicist - linen duster, motoring cap and goggles, riding boots",
                  coat="#c2ae84", vest="#6e5a46", trousers="#7c6d55", shoe="#3a2a1e", hair="#3a2c24",
                  coat_kind="duster", collar="scarf", scarf="#9c3029", legs="breeches", glove="#6e4a30",
                  stache="kaiser", hat="cap", hat_c="#6b5f52", goggles=True, button="#5a4630"),
        "C": dict(label="C: the accomplice - black frock coat, bowler, furled umbrella",
                  coat="#23242b", coat_lt="#3a3b45", facing="#16161b", vest="#4a5168", trousers="#6a6c74", stripe="#53555c",
                  shoe="#1a1716", hair="#3a2c24", coat_kind="frock", collar="wing", tie="#6d1f28", legs="trousers",
                  stache="walrus", hat="bowler", hat_c="#1d1d21", hat_band="#111114", umbrella=True, chain=True),
    },
}

O: Dict = {}
G: Dict = {}


def use(who: str, look: str) -> None:
    O.clear()
    O.update(SKIN)
    O.update(SHIRT)
    O.update(dict(button="#b89a52", gold="#c9a24a", glass="#cfe0e6"))
    O.update(LOOKS[who][look])
    O["who"], O["look"] = who, look
    for key in ("coat", "vest", "trousers", "knick", "sock", "shoe", "hat_c", "scarf", "glove", "hair", "facing"):
        if key in O:
            O.setdefault(key + "_sh", dark(O[key]))
            O.setdefault(key + "_lt", lite(O[key]))
    if "beard" in O:
        O.setdefault("hair", O["beard"])
        O.setdefault("hair_sh", O["beard_sh"])
        O.setdefault("hair_lt", O["beard_lt"])
    O.setdefault("brow", O["hair_sh"] if who == "cutta" else O["beard_sh"])
    G.clear()
    G.update(BUILDS[who])
    global HAND
    HAND = G["hand"]


# ============================================================================================
# the point map: a head is drawn in its own frame
# ============================================================================================

_XF = [None]


def _P(x, y):
    if _XF[0] is not None:
        ox, oy, k = _XF[0]
        x, y = ox + x * k, oy + y * k
    return x + svg.DX, y + svg.DY


svg.P = _P


def K():
    return _XF[0][2] if _XF[0] is not None else 1.0


def E(cx, cy, rx, ry, fill, stroke=None, sw=None, rot=0.0):
    """An ellipse whose radii follow the head frame's scale."""
    x, y = _P(cx, cy)
    k = K()
    s = f'<ellipse cx="{svg.f(x)}" cy="{svg.f(y)}" rx="{svg.f(rx * k)}" ry="{svg.f(ry * k)}" fill="{fill}"'
    if rot:
        s += f' transform="rotate({svg.f(rot)} {svg.f(x)} {svg.f(y)})"'
    if stroke:
        s += f' stroke="{stroke}" stroke-width="{svg.f(sw)}"'
    return s + " />"


_N = [0]


def uid():
    _N[0] += 1
    return f"rk{_N[0]}"


def cel(d, base, shade, light=None, items=(), sdir=SD, ldir=LD, s=5.0, l=3.0, sw=None, ink=None, edges=None):
    """oiler_art.cel: fill, a shade band on the edges facing ``sdir``, a light
    band on those facing ``ldir``, the ``items`` clipped inside, the ink."""
    cid = uid()
    k = K()
    sx, sy = -sdir[0] * s * k, -sdir[1] * s * k
    out = [f'<clipPath id="{cid}"><path d="{d}" /></clipPath>',
           f'<clipPath id="{cid}s"><path d="{d}" transform="translate({sx:.2f} {sy:.2f})" /></clipPath>',
           f'<g clip-path="url(#{cid})">', path(d, shade), f'<g clip-path="url(#{cid}s)">']
    if light:
        lx, ly = -ldir[0] * l * k, -ldir[1] * l * k
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


def far(d, key, items=(), **kw):
    return cel(d, O[key + "_sh"], O[key + "_sh"], None, items, s=1, **kw)


def frame(origin, u_ang):
    ux, uy = math.cos(u_ang), math.sin(u_ang)
    nx, ny = -uy, ux
    return lambda t, s: (origin[0] + ux * t + nx * s, origin[1] + uy * t + ny * s)


def ang(a, b):
    return math.atan2(b[1] - a[1], b[0] - a[0])


def mx(pts, cx=280.0):
    return [(2 * cx - p[0], p[1]) + tuple(p[2:]) for p in pts]


def interp(table, y):
    if y <= table[0][0]:
        return table[0][1]
    for (y0, a), (y1, b) in zip(table, table[1:]):
        if y <= y1:
            return a + (b - a) * (y - y0) / (y1 - y0)
    return table[-1][1]


def S(pts):
    """Side-view body points ``(u, y)`` to drawing points."""
    out = []
    for p in pts:
        b, f = interp(G["back"], p[1]), interp(G["front"], p[1])
        out.append((b + p[0] * (f - b), p[1]) + tuple(p[2:]))
    return out


def F(pts, cx=280.0):
    """Front-view body points ``(v, y)`` to drawing points."""
    return [(cx + p[0] * interp(G["hw"], p[1]), p[1]) + tuple(p[2:]) for p in pts]


def FM(pts):
    """A front-view piece and its mirror (the other side of the body)."""
    return [F(pts), F([(-p[0],) + tuple(p[1:]) for p in pts])]


# ============================================================================================
# hands (oiler_art), with a glove option
# ============================================================================================

HAND = 1.1


def finger(b, m, e, w0, w1, w2):
    def nrm(p0, p1):
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        L = math.hypot(dx, dy) or 1.0
        return -dy / L, dx / L, dx / L, dy / L
    n0x, n0y, _, _ = nrm(b, m)
    n1x, n1y, ux, uy = nrm(m, e)
    side_a = [(b[0] + n0x * w0, b[1] + n0y * w0), (m[0] + (n0x + n1x) / 2 * w1, m[1] + (n0y + n1y) / 2 * w1), (e[0] + n1x * w2, e[1] + n1y * w2)]
    side_b = [(e[0] - n1x * w2, e[1] - n1y * w2), (m[0] - (n0x + n1x) / 2 * w1, m[1] - (n0y + n1y) / 2 * w1), (b[0] - n0x * w0, b[1] - n0y * w0)]
    tip = (e[0] + ux * w2 * 1.1, e[1] + uy * w2 * 1.1)
    return smooth(side_a + [tip] + side_b)


def hand_tones(near=True):
    key = "glove" if O.get("glove") else "skin"
    sk, sh, lt = O[key], O[key + "_sh"], O.get(key + "_lt")
    dk = O["skin_dk"] if key == "skin" else dark(O["glove"], 0.6)
    return (sk, sh, lt, dk) if near else (sh, dk, None, dk)


def hand_side(wrist, a, near=True, grip=False):
    """oiler_art.hand_side: a relaxed hand hanging from ``wrist`` seen from its
    back; ``grip`` curls the fingers round a staff."""
    q = frame(wrist, a)
    p = lambda t, f: q(HAND * t, -HAND * f)
    sk, sh, lt, dk = hand_tones(near)
    fine = 1.3
    out = []
    thumb = finger(p(4, 5.0), p(11, 8.6), p(16.5, 9.6), 3.4 * HAND, 2.8 * HAND, 2.2 * HAND)
    out += cel(thumb, sk, sh, lt, [line([p(14.6, 8.0), p(15.4, 10.8)], dk, 0.7)], s=1.6, sw=fine)
    curls = ((-5.0, 12.5, 2.0), (-1.7, 15.0, 2.8), (1.6, 16.0, 3.4), (4.8, 14.5, 3.6))
    if grip:
        curls = ((-5.0, 9.0, 7.0), (-1.7, 10.0, 8.0), (1.6, 10.5, 8.6), (4.8, 10.0, 8.6))
    for f0, length, curl in curls:
        fing = finger(p(10, f0), p(10 + length * 0.55, f0 + curl * 0.3), p(10 + length, f0 + curl), 2.1 * HAND, 1.95 * HAND, 1.7 * HAND)
        out += cel(fing, sk, sh, lt if f0 > 4 else None, [line([p(10 + length * 0.55, f0 + curl * 0.3 - 1.2), p(10 + length * 0.55, f0 + curl * 0.3 + 1.2)],
                                                              sh, 0.7)], s=1.0, sw=fine)
    run = [p(-1, -6.8), p(6, -7.4), p(11, -7.0), p(13.5, -3), p(14, 2), p(13, 6.6), p(7, 7.2), p(-1, 6.8)]
    palm = smooth([p(-3, -6.6)] + run + [p(-3, 6.6)])
    items = [line([p(4, -2.5), p(9.5, -3.2)], sh, 0.8), line([p(4, 1.5), p(9.5, 1.5)], sh, 0.8)]
    out += cel(palm, sk, sh, lt, items, s=2.5, edges=[run])
    return out


def hand_front(wrist, a, inward):
    """oiler_art.hand_front: a relaxed hand at his side seen from the front."""
    q = frame(wrist, a)
    p = lambda t, i: q(HAND * t, -HAND * i * inward)
    sk, sh, lt, dk = hand_tones()
    fine = 1.3
    out = []
    for i0, length, curl in ((3.2, 13.0, 3.0), (1.4, 14.5, 3.4)):
        out += cel(finger(p(9, i0), p(9 + length * 0.6, i0 + curl * 0.4), p(9 + length, i0 + curl), 2.1 * HAND, 2.0 * HAND, 1.7 * HAND),
                   sh, dk, None, [], s=1.0, sw=fine)
    run = [p(-1, -5.4), p(7, -6.0), p(12, -5.0), p(13.5, 0), p(12.5, 5.0), p(6, 5.6), p(-1, 5.4)]
    out += cel(smooth([p(-3, -5.2)] + run + [p(-3, 5.2)]), sk, sh, lt, [], s=2.0, edges=[run])
    idx = finger(p(10, -1.0), p(18.5, 0.6), p(24, 4.0), 2.4 * HAND, 2.2 * HAND, 1.9 * HAND)
    out += cel(idx, sk, sh, lt, [line([p(18.4, -1.4), p(18.8, 2.4)], sh, 0.7)], s=1.2, sw=fine)
    thumb = finger(p(3, -4.4), p(11, -6.0), p(17.5, -4.2), 3.0 * HAND, 2.6 * HAND, 2.1 * HAND)
    out += cel(thumb, sk, sh, lt, [line([p(15.2, -6.2), p(15.8, -2.6)], dk, 0.7)], s=1.6, sw=fine)
    return out


# ============================================================================================
# arms
# ============================================================================================

def sleeve_key():
    return "coat"


def limb(a, b, r0, r1, ink_a=True, ink_b=True):
    """A tapered capsule from ``a`` to ``b`` and its ink runs: both sides, and
    each round end only when asked (a joint's end hidden by the next piece
    is left uninked, so an elbow or a knee reads as one limb)."""
    ux, uy = (b[0] - a[0]), (b[1] - a[1])
    L = math.hypot(ux, uy) or 1.0
    ux, uy = ux / L, uy / L
    nx, ny = -uy, ux
    arc = lambda c, r, t0: [(c[0] + (math.cos(t) * ux + math.sin(t) * nx) * r, c[1] + (math.cos(t) * uy + math.sin(t) * ny) * r)
                            for t in (t0 + math.pi * i / 10 for i in range(11))]
    A, B = arc(a, r0, math.pi / 2), arc(b, r1, -math.pi / 2)
    d = svg.poly(A + B)
    if ink_a and ink_b:
        return d, None
    runs = []
    if ink_b:
        runs.append([A[-1]] + B + [A[0]])
    else:
        runs += [[A[-1], B[0]], [B[-1], A[0]]]
    if ink_a:
        runs.append(A)
    return d, runs


def straight(run):
    return path("M" + " L".join(svg.pt(_P(*p[:2])) for p in run), "none", INK, 2 * OW)


def limb_cel(d_runs, key, items=(), near=True, s=5):
    d, runs = d_runs
    if near:
        out = C(d, key, items, s=s, edges=[] if runs else None)
    else:
        out = far(d, key, edges=[] if runs else None)
    return out + ([straight(r) for r in runs] if runs else [])


def upper_arm(s, e, near=True):
    r0, r1 = G["r_up"]
    dr = limb(s, e, r0, r1, ink_b=False)
    if not near:
        return limb_cel(dr, sleeve_key(), near=False)
    p = frame(s, ang(s, e))
    items = [line([p(6, -r0 * 0.5), p(30, -r1 * 0.55)], O["coat_lt"], 1.2), line([p(10, r0 * 0.4), p(36, r1 * 0.5)], O["coat_sh"], 1.1)]
    return limb_cel(dr, sleeve_key(), items, s=5)


def fore_arm(e, w, near=True):
    """The coat's forearm, its cuff (a gauntlet's in look B of Cutta), and the
    shirt cuff showing below it."""
    r0, r1 = G["r_fore"]
    a = ang(e, w)
    p = frame(w, a)
    out = []
    if O.get("glove"):  # the gauntlet's flared cuff over the sleeve end
        sleeve = capsule(e, p(-6, 0), r0, r1)
        out += C(sleeve, "coat", [], s=3) if near else far(sleeve, "coat")
        cuff = smooth([p(-14, -r1 - 3.5), p(-14, r1 + 3.5), p(2, r1 - 0.5), p(2, -r1 + 0.5)])
        out += C(cuff, "glove", [line([p(-10, -r1 - 1), p(-10, r1 + 1)], O["glove_sh"], 1.0)], s=2) if near else far(cuff, "glove")
        return out
    sc = capsule(p(-8, 0), p(1.5, 0), r1 - 1.0, r1 - 1.6)
    out += C(sc, "shirt", [], s=2) if near else far(sc, "shirt")
    sleeve = limb(e, p(-4, 0), r0, r1 + 0.6, ink_a=False)
    items = [line([p(-12, -r1 + 2), p(-12, r1 - 2)], O["coat_sh"], 1.0)] if near else []
    out += limb_cel(sleeve, "coat", items, near=near, s=4)
    return out


def hand_at(e, w, near=True, grip=False):
    return hand_side(w, ang(e, w), near=near, grip=grip)


# ============================================================================================
# legs
# ============================================================================================

def trouser_thigh(hip, knee, near, key="trousers"):
    r0, r1 = G["r_thigh"]
    dr = limb(hip, knee, r0, r1, ink_a=False, ink_b=False)
    items = []
    if near and O.get("stripe"):
        p = frame(hip, ang(hip, knee))
        items = [line([p(-10, s), p(80, s)], O["stripe"], 1.4) for s in (-9, -3, 3, 9)]
    return limb_cel(dr, key, items, near=near, s=4)


def trouser_shin(knee, ankle, near, front=False):
    r0, r1 = G["r_shin"]
    (kx, ky), (ax, ay) = knee, ankle
    if front:
        d = smooth([(kx - r0, ky - 4), (kx + r0, ky - 4), (ax + r1 + 1.5, ay - 4), (ax + r1 + 2.5, ay + 7, True), (ax - r1 - 2.5, ay + 7, True), (ax - r1 - 1.5, ay - 4)])
    else:
        d = smooth([(kx - r0, ky - 4), (kx + r0, ky - 2), (ax + r1 + 2.5, ay - 4), (ax + r1 + 4, ay + 5, True), (ax - r1 - 3, ay + 8, True), (ax - r1 - 1, ay - 4)])
    if front:
        runs = [[(kx + r0, ky - 4), (ax + r1 + 1.5, ay - 4), (ax + r1 + 2.5, ay + 7)], [(ax + r1 + 2.5, ay + 7), (ax - r1 - 2.5, ay + 7)],
                [(ax - r1 - 2.5, ay + 7), (ax - r1 - 1.5, ay - 4), (kx - r0, ky - 4)]]
    else:
        runs = [[(kx + r0, ky - 2), (ax + r1 + 2.5, ay - 4), (ax + r1 + 4, ay + 5)], [(ax + r1 + 4, ay + 5), (ax - r1 - 3, ay + 8)],
                [(ax - r1 - 3, ay + 8), (ax - r1 - 1, ay - 4), (kx - r0, ky - 4)]]
    if not near:
        return far(d, "trousers", edges=[]) + [straight(r) for r in runs]
    items = []
    if O.get("stripe"):
        items = [line([(kx + s, ky - 6), (ax + s * 1.1, ay + 10)], O["stripe"], 1.4) for s in (-7, -2.5, 2, 6.5)]
    items.append(line([(ax - r1, ay - 2), (ax + 2, ay + 1), (ax + r1 + 2, ay - 3)], O["trousers_sh"], 1.0))
    return C(d, "trousers", items, s=4, edges=[]) + [straight(r) for r in runs]


def shoe(ankle, near, front=False, boot=0.0, key="shoe"):
    """A leather shoe (``boot`` raises an ankle-boot's shaft), its sole at the ground."""
    ax, ay = ankle
    toe = G["toe"]
    if front:
        d = smooth([(ax - 9.5, ay - 3 - boot), (ax + 9.5, ay - 3 - boot), (ax + 10.5, ay + 6), (ax + 9, ay + 15, True), (ax - 9, ay + 15, True), (ax - 10.5, ay + 6)])
        items = [line([(ax - 9, ay + 13), (ax + 9, ay + 13)], O[key + "_sh"], 1.4), E(ax + 3, ay + 8, 2.6, 1.6, O[key + "_lt"])]
    else:
        d = smooth([(ax - 10, ay - 6 - boot), (ax + 6, ay - 6 - boot), (ax + 9, ay + 2), (ax + toe - 4, ay + 7), (ax + toe, ay + 11), (ax + toe, ay + 15, True),
                    (ax - 11, ay + 16, True), (ax - 11.5, ay + 6)])
        items = [line([(ax - 10, ay + 13.4), (ax + toe - 1, ay + 12.6)], O[key + "_sh"], 1.4), E(ax + toe - 9, ay + 6.5, 3.4, 1.4, O[key + "_lt"], rot=12)]
        if boot:
            items.append(line([(ax + 3, ay - 4 - boot), (ax + 7, ay + 2)], O[key + "_sh"], 1.0))
    return C(d, key, items, s=3) if near else cel(d, O[key + "_sh"], dark(O[key + "_sh"], 0.7), None, [], s=1)


def leg_pieces(hip, knee, ankle, near, front=False):
    """The leg in z order, per legwear."""
    style = O["legs"]
    if style == "trousers":
        return shoe(ankle, near, front) + trouser_shin(knee, ankle, near, front) + trouser_thigh(hip, knee, near)
    if style == "knickers":  # wool stockings, ankle boots, knickerbockers bloused over the knee
        (kx, ky), (ax, ay) = knee, ankle
        r0, r1 = G["r_shin"]
        st = capsule((kx, ky + 8), (ax, ay - 4), r0 - 0.5, r1 - 1.0)
        out = C(st, "sock", [line([(kx - 6 + i * 3.4, ky + 22), (ax - 6 + i * 3.0, ay - 10)], O["sock_sh"], 0.8) for i in range(5)], s=3) if near else far(st, "sock")
        out += shoe(ankle, near, front, boot=8.0)
        band = capsule((kx, ky + 16), (kx + (ax - kx) * 0.12, ky + 24), r0 + 1.2, r0 + 0.6)
        out += C(band, "sock", [line([(kx - r0, ky + 20), (kx + r0, ky + 21)], O["sock_sh"], 1.0)], s=2) if near else far(band, "sock")
        r0t, r1t = G["r_thigh"]
        if front:
            kn = smooth([(hip[0] - r0t, hip[1] - 4), (hip[0] + r0t, hip[1] - 4), (kx + r1t + 3, ky - 6), (kx + r1t + 4, ky + 8), (kx + r1t, ky + 16, True), (kx - r1t, ky + 16, True),
                         (kx - r1t - 4, ky + 8), (kx - r1t - 3, ky - 6)])
        else:
            kn = smooth([(hip[0] - r0t, hip[1] - 6), (hip[0] + r0t, hip[1] - 2), (kx + r1t + 2, ky - 8), (kx + r1t + 5, ky + 6), (kx + r1t - 1, ky + 16, True), (kx - r1t, ky + 17, True),
                         (kx - r1t - 4, ky + 4), (kx - r1t - 2, ky - 12)])
        items = [line([(kx - 6, ky + 2), (kx + 2, ky + 14)], O["knick_sh"], 1.1), line([(kx + 4, ky - 4), (kx + 9, ky + 10)], O["knick_sh"], 1.0)]
        return out + (C(kn, "knick", items, s=4) if near else far(kn, "knick"))
    if style == "breeches":  # riding breeches flared at the thigh, tall boots
        (kx, ky), (ax, ay) = knee, ankle
        r0t, r1t = G["r_thigh"]
        if front:
            br = smooth([(hip[0] - r0t, hip[1] - 4), (hip[0] + r0t, hip[1] - 4), (kx + r1t + 6, ky - 40), (kx + r1t, ky + 4), (kx - r1t, ky + 4), (kx - r1t - 6, ky - 40)])
        else:
            br = smooth([(hip[0] - r0t, hip[1] - 6), (hip[0] + r0t, hip[1] - 2), (kx + r1t + 2, ky - 30), (kx + r1t, ky + 6), (kx - r1t, ky + 8), (kx - r1t - 7, ky - 30)])
        out = C(br, "trousers", [], s=4) if near else far(br, "trousers")
        r0, r1 = G["r_shin"]
        if front:
            bt = smooth([(kx - r0 - 1.5, ky - 2), (kx + r0 + 1.5, ky - 2), (ax + r1 + 1, ay - 4), (ax + r1 + 1, ay + 4), (ax - r1 - 1, ay + 4), (ax - r1 - 1, ay - 4)])
        else:
            bt = smooth([(kx - r0 - 1.5, ky - 4), (kx + r0 + 2.5, ky - 8, True), (ax + r1 + 1, ay - 6), (ax + r1 + 1, ay + 4), (ax - r1 - 1, ay + 4), (ax - r1 - 1, ay - 6)])
        items = [line([(kx - r0, ky + 4), (kx + r0 + 1, ky + 1)], O["shoe_sh"], 1.2), line([(kx + 3, ky + 10), (ax + 4, ay - 8)], O["shoe_lt"], 1.3)]
        out += shoe(ankle, near, front)
        out += C(bt, "shoe", items, s=3) if near else cel(bt, O["shoe_sh"], dark(O["shoe_sh"], 0.7), None, [], s=1)
        return out
    raise KeyError(style)


# ============================================================================================
# SIDE VIEW
# ============================================================================================

def coat_len():
    """The coat's hem: frock coats to above the knee, long coats to mid-calf."""
    kind = O["coat_kind"]
    return {"frock": G["knee"] - 8, "lounge": G["hy"] + 22, "norfolk": G["hy"] + 18,
            "duster": G["knee"] + 34, "inverness": G["knee"] + 30}[kind]


def s_shirtfront():
    """What shows at the front of the chest between the coat's open edges: the
    waistcoat, its buttons and (look A, C) the watch chain."""
    nb, sy, wy, hy = G["nb"], G["sy"], G["wy"], G["hy"]
    kind = O["coat_kind"]
    if kind in ("norfolk", "duster", "inverness"):
        return []
    bottom = wy + 14
    d = smooth(S([(0.30, nb + 2), (0.80, nb + 4), (0.98, sy + 10), (1.03, sy + 44), (1.04, wy), (1.0, bottom, True), (0.5, bottom + 4, True), (0.3, wy)]))
    items = [E(*S([(0.985, y)])[0], 1.7, 1.7, O["button"], INK, 0.6) for y in range(int(sy + 26), int(bottom - 4), 13)]
    if O.get("chain"):
        items.append(line(S([(1.0, wy - 14), (0.86, wy - 4), (0.74, wy - 10)]), O["gold"], 1.6))
    return C(d, "vest", items, s=4)


def s_coat_body():
    nb, sy, wy, hy = G["nb"], G["sy"], G["wy"], G["hy"]
    kind = O["coat_kind"]
    hem = coat_len()
    if kind in ("frock",):  # open over the waistcoat, its silk lapel rolled to the waist
        back = [(0.42, nb - 2), (0.12, nb + 8), (0.0, sy + 16), (0.02, wy - 6), (0.05, wy + 4)]
        d = smooth(S(back + [(0.5, wy + 8), (0.86, wy + 4), (0.86, sy + 30), (0.84, sy + 6), (0.72, nb + 4)]))
        items = [line(S([(0.16, sy + 4), (0.06, sy + 36), (0.08, wy)]), O["coat_sh"], 1.2),
                 line(S([(0.03, wy + 2), (0.5, wy + 6), (0.86, wy + 3)]), O["coat_sh"], 1.1)]
        out = C(d, "coat", items, s=6)
        lapel = smooth(S([(0.66, nb + 2), (0.86, nb + 8), (0.93, sy + 10), (0.88, sy + 46), (0.86, wy + 2), (0.79, wy - 6), (0.80, sy + 24), (0.75, sy + 2)]))
        out += C(lapel, "facing", [], s=2)
        return out
    if kind == "lounge":  # the sack coat buttoned high, short lapels, rounded fronts
        d = smooth(S([(0.42, nb - 2), (0.12, nb + 8), (0.0, sy + 16), (0.02, wy), (-0.02, hy), (-0.03, hem, True), (0.6, hem + 2), (0.96, hem - 4),
                      (1.05, hy - 4), (1.07, wy), (1.06, sy + 34), (1.0, sy + 20), (0.86, nb + 6), (0.72, nb + 4)]))
        items = [line(S([(0.14, sy + 4), (0.04, sy + 36), (0.04, hy)]), O["coat_sh"], 1.2),
                 path(smooth(S([(0.5, hy - 4, True), (0.84, hy - 4, True), (0.84, hy + 4), (0.5, hy + 4)])), O["coat_sh"], INK, 1.0)]
        items += [E(*S([(1.035, y)])[0], 1.9, 1.9, O["button"], INK, 0.6) for y in (sy + 40, sy + 56, wy + 2)]
        out = C(d, "coat", items, s=6)
        lapel = smooth(S([(0.7, nb + 2), (0.9, nb + 8), (1.04, sy + 12), (1.03, sy + 28), (0.93, sy + 22), (0.80, sy + 4)]))
        out += C(lapel, "coat", [], s=2)
        return out
    if kind == "norfolk":  # belted, a box pleat down the front and the back, patch pocket
        d = smooth(S([(0.42, nb - 2), (0.12, nb + 8), (-0.01, sy + 16), (0.0, wy), (-0.04, hy), (-0.05, hem, True), (0.6, hem + 3), (1.06, hem, True),
                      (1.06, hy - 2), (1.07, wy), (1.06, sy + 34), (1.0, sy + 18), (0.86, nb + 6), (0.72, nb + 4)]))
        items = [line(S([(0.14, sy + 6), (0.14, hem)]), O["coat_sh"], 1.3), line(S([(0.24, sy + 6), (0.24, hem)]), O["coat_sh"], 1.3),
                 line(S([(0.84, sy + 10), (0.84, hem)]), O["coat_sh"], 1.3), line(S([(0.94, sy + 6), (0.94, hem)]), O["coat_sh"], 1.1),
                 path(smooth(S([(0.42, wy + 12, True), (0.78, wy + 12, True), (0.80, hem - 6, True), (0.42, hem - 6, True)])), O["coat_sh"], INK, 1.0),
                 path(smooth(S([(0.40, wy + 10, True), (0.80, wy + 10, True), (0.80, wy + 19, True), (0.40, wy + 19, True)])), O["coat"], INK, 1.0)]
        items += [E(*S([(1.04, y)])[0], 2.0, 2.0, O["button"], INK, 0.6) for y in (sy + 30, sy + 48, hy - 2)]
        out = C(d, "coat", items, s=6)
        lapel = smooth(S([(0.7, nb + 2), (0.9, nb + 8), (1.05, sy + 10), (1.04, sy + 22), (0.94, sy + 18), (0.80, sy + 4)]))
        out += C(lapel, "coat", [], s=2)
        belt = smooth(S([(-0.02, wy - 6, True), (1.08, wy - 6, True), (1.08, wy + 4, True), (-0.02, wy + 4, True)]))
        out += C(belt, "coat", [line(S([(0, wy - 1), (1.06, wy - 1)]), O["coat_sh"], 1.0), E(*S([(1.0, wy - 1)])[0], 2.2, 2.2, O["button"], INK, 0.6)], s=2)
        return out
    if kind == "duster":  # long, loose, buttoned to the chest, a back vent, deep pockets
        d = smooth(S([(0.42, nb - 4), (0.10, nb + 8), (-0.04, sy + 16), (-0.06, wy), (-0.16, hy + 10), (-0.30, hem, True), (0.5, hem + 4), (1.22, hem, True),
                      (1.12, hy), (1.08, wy), (1.08, sy + 32), (1.02, sy + 16), (0.86, nb + 4), (0.72, nb + 2)]))
        items = [line(S([(0.0, hy), (-0.08, hem - 2)]), O["coat_sh"], 1.4), line(S([(0.42, hy + 20), (0.36, hem - 4)]), O["coat_sh"], 1.2),
                 line(S([(0.92, hy + 10), (1.0, hem - 4)]), O["coat_sh"], 1.1),
                 path(smooth(S([(0.48, wy + 22, True), (0.86, wy + 22, True), (0.86, wy + 30, True), (0.48, wy + 30, True)])), O["coat_sh"], INK, 1.0),
                 line(S([(1.06, sy + 20), (1.08, wy + 4), (1.12, hy + 14), (1.2, hem - 2)]), O["coat_sh"], 1.2)]
        items += [E(*S([(1.04, y)])[0], 2.0, 2.0, O["button"], INK, 0.6) for y in (sy + 28, sy + 50, wy + 4)]
        out = C(d, "coat", items, s=7)
        return out
    if kind == "inverness":  # the long coat under the cape: its skirt is what shows
        d = smooth(S([(0.42, nb - 2), (0.10, nb + 8), (-0.02, sy + 16), (-0.04, wy), (-0.12, hy + 10), (-0.22, hem, True), (0.5, hem + 4), (1.14, hem, True),
                      (1.08, hy), (1.08, wy), (1.08, sy + 32), (1.02, sy + 16), (0.86, nb + 4), (0.72, nb + 2)]))
        items = check_items(S([(-0.3, nb)])[0][0], nb, S([(1.2, nb)])[0][0], hem + 4)
        items += [line(S([(0.0, hy), (-0.06, hem - 2)]), O["coat_sh"], 1.4), line(S([(1.06, wy), (1.12, hem - 2)]), O["coat_sh"], 1.2)]
        items += [E(*S([(1.05, y)])[0], 2.0, 2.0, O["button"], INK, 0.6) for y in (hy - 4, hy + 18, hy + 40)]
        return C(d, "coat", items, s=7)
    raise KeyError(kind)


def check_items(x0, y0, x1, y1, step=11.0):
    """A quiet tweed check: thin lines both ways in the coat's own darker tone."""
    out = []
    y = y0
    while y < y1:
        out.append(line([(x0, y), (x1, y)], O["check"], 0.8))
        y += step
    x = x0
    while x < x1:
        out.append(line([(x, y0), (x, y1)], O["check"], 0.8))
        x += step
    return out


def s_skirt(side):
    """The frock coat's skirt below the waist seam, near and far panels."""
    if O["coat_kind"] != "frock":
        return []
    wy, hy = G["wy"], G["hy"]
    hem = coat_len()
    if side == "far":
        d = smooth(S([(0.05, wy), (0.6, wy + 2), (0.62, hy + 20), (0.6, hem - 2, True), (-0.10, hem, True), (-0.06, hy + 20)]))
        return far(d, "coat")
    d = smooth(S([(0.04, wy + 2), (0.86, wy + 4), (1.03, hy + 6), (1.06, hem - 4, True), (-0.10, hem, True), (-0.06, hy + 20), (0.0, hy)]))
    items = [line(S([(0.08, wy + 10), (0.0, hem - 2)]), O["coat_sh"], 1.3), line(S([(0.5, wy + 14), (0.48, hem - 2)]), O["coat_sh"], 1.1),
             line(S([(0.18, wy + 6), (0.12, wy + 30)]), O["coat_lt"], 1.2)]
    out = C(d, "coat", items, s=6)
    edge = smooth(S([(0.83, wy + 2), (0.88, wy + 2), (1.03, hy + 6), (1.07, hem - 4, True), (1.0, hem - 4, True), (0.96, hy + 6)]))
    return out + C(edge, "facing", [], s=1)


def s_cape():
    """The Inverness cape: from the collar over the shoulders to the hip, its
    front edge open over the chest."""
    if O["coat_kind"] != "inverness":
        return []
    nb, sy, wy, hy = G["nb"], G["sy"], G["wy"], G["hy"]
    d = smooth(S([(0.40, nb - 4), (0.06, nb + 6), (-0.16, sy + 20), (-0.32, wy - 6), (-0.38, hy - 4, True), (0.40, hy + 6), (1.00, hy + 2), (1.30, hy - 6, True),
                  (1.26, wy - 16), (1.14, sy + 16), (0.98, nb + 6), (0.72, nb)]))
    x0, x1 = S([(-0.5, nb)])[0][0], S([(1.4, nb)])[0][0]
    items = check_items(x0, nb - 6, x1, hy + 12)
    items += [line(S([(0.5, sy + 10), (0.42, hy)]), O["coat_sh"], 1.3), line(S([(0.92, sy + 20), (1.04, hy)]), O["coat_sh"], 1.2),
              line(S([(0.2, sy + 6), (-0.04, wy)]), O["coat_lt"], 1.3)]
    out = C(d, "coat", items, s=7)
    collar = smooth(S([(0.30, nb - 12), (0.66, nb - 10), (0.96, nb - 2), (1.02, nb + 10), (0.80, nb + 14), (0.46, nb + 10), (0.18, nb + 6)]))
    return out + C(collar, "coat", [line(S([(0.4, nb + 2), (0.9, nb + 6)]), O["coat_sh"], 1.0)], s=3)


def s_pelvis():
    hy = G["hy"]
    return C(smooth(S([(0.05, hy - 16, True), (0.95, hy - 16, True), (0.98, hy + 14, True), (0.05, hy + 14, True)])), "trousers" if O["legs"] != "knickers" else "knick", [], s=3)


def neck_line():
    """The neck runs from under the skull forward-down to the middle of the
    torso's top: the neck leans, the head sits ahead of the shoulders."""
    hk = G["hk"]
    ex, ey = G["eye"]
    top = (ex - 15 * hk, ey + 20 * hk)
    base = S([(0.5, G["nb"] + 4)])[0][:2]
    return top, base, 11.8 * hk


def neck_x(y):
    (tx, ty), (bx, by), _r = neck_line()
    return tx + (bx - tx) * (y - ty) / (by - ty)


def s_neck():
    """The neck, the shirt collar round it (wing, high, soft), the coat's collar
    behind it, and the tie at the throat (or the scarf)."""
    nb = G["nb"]
    top, base, r = neck_line()
    out = C(capsule(top, base, r, r), "skin", [line([(top[0] + r * 0.6, top[1] + 4), (base[0] + r * 0.7, base[1] - 10)], O["skin_sh"], 1.0)], s=4)
    kind = O["collar"]
    if kind == "scarf":
        ct, cb = nb - 16, nb + 4
        xt, xb = neck_x(ct), neck_x(cb)
        sc = smooth([(xt - r - 4, ct), (xt + r + 3, ct + 2), (xb + r + 5, cb), (xb - r - 3, cb + 2)])
        out += C(sc, "scarf", [line([(xt - r, ct + 6), (xt + r + 2, ct + 8)], O["scarf_sh"], 1.1), line([(xt - r, ct + 12), (xb + r + 2, ct + 14)], O["scarf_sh"], 1.0)], s=3)
        tail = smooth([(xb + r - 2, cb - 6), (xb + r + 6, cb - 4), (xb + r + 9, cb + 26), (xb + r + 4, cb + 38, True), (xb + r - 3, cb + 30, True), (xb + r - 4, cb + 6)])
        out += C(tail, "scarf", [line([(xb + r + 2, cb), (xb + r + 4, cb + 30)], O["scarf_sh"], 1.0)], s=2)
        return out
    ct = nb - (17 if kind == "high" else 12)
    cb = nb + 2
    xt, xb = neck_x(ct), neck_x(cb)
    col = smooth([(xt - r - 1.5, ct, True), (xt + r + 1.8, ct + 3, True), (xb + r + 2.2, cb, True), (xb - r - 1.5, cb - 1, True)])
    out += C(col, "shirt", [line([(xt - r, (ct + cb) / 2), (xt + r + 1, (ct + cb) / 2 + 1.5)], O["shirt_sh"], 0.8)], s=2)
    if kind == "wing":  # the wing tip folded down at the throat
        out += C(smooth([(xt + r + 1.8, ct + 3), (xt + r + 6, ct + 7), (xt + r + 2, ct + 10, True)]), "shirt", [], s=1)
    # the coat's collar, rolled round the back of the neck
    if O["coat_kind"] != "inverness":
        out += C(smooth([(xb - r - 3, cb - 6), (xb - r + 3, cb - 7), (xb + 2, cb - 1), (xb + r + 2, cb + 6), (xb - r - 3, cb + 6)]), "coat", [], s=2)
    tie = O["tie"]
    tx, ty = xb + r - 0.6, cb - 3
    if kind == "wing":  # a bow
        out += cel(smooth([(tx - 2, ty - 4), (tx + 5, ty - 6, True), (tx + 6, ty + 2, True), (tx - 2, ty + 3)]), tie, dark(tie), lite(tie), [], s=1)
    else:  # the knot, the blade falling under the coat
        out += cel(smooth([(tx - 1, ty - 3), (tx + 3, ty - 2), (tx + 3.4, ty + 4), (tx, ty + 4)]), tie, dark(tie), lite(tie), [], s=1, sw=1.4)
    return out


# ---- heads ------------------------------------------------------------------------------------

def head_frame(view):
    ex, ey = G["eye"] if view == "side" else G["feye"]
    _XF[0] = (ex, ey, G["hk"])


def runga_side_head():
    """Runge in profile: a high bald dome, a strong nose, a small deep-set eye
    under a heavy brow, short hair round the back and over the ear joining the
    full beard, which hides the jaw and juts forward below the moustache."""
    sk, dk = O["skin_sh"], O["skin_dk"]
    out = []
    skull = [(-14, -39), (0, -40.5), (11, -35), (16.5, -25), (18, -14), (17.6, -7), (15, -2.5), (17, 2.5), (21.4, 8.6), (25.6, 13.6), (26.2, 16.4), (24, 18.2),
             (18, 18.6, True), (19, 24), (18, 30), (13, 34), (2, 34), (-8, 30), (-16, 24), (-24, 25), (-31, 17), (-35.5, 4), (-35.5, -10), (-30, -27)]
    items = [E(3, -31, 7, 3.2, O["skin_lt"], rot=-12),
             line([(4, -22), (13, -20.5)], sk, 1.0), line([(2, -17), (13.5, -15.4)], sk, 0.9),
             line([(17.4, 11), (14.6, 13.6), (15.4, 17.0), (18.4, 18.2)], dk, 1.1),
             line([(18.6, 0), (23.4, 10.8)], O["skin_lt"], 1.6),
             line([(9, 3), (12, 6), (15, 6)], sk, 1.0)]
    out += C(smooth(skull), "skin", items, s=6)
    # the short hair round the back of the dome, over the ear
    hair = [(-4, -12), (-10, -19), (-24, -23), (-33, -17.5), (-37.5, -4), (-36.4, 8), (-31, 19), (-25, 24), (-19, 18), (-11, 9), (-7.6, 1), (-6.4, -6)]
    out += C(smooth(hair), "beard", [line([(-14, -16), (-28, -15), (-33, -2)], O["beard_sh"], 1.0), line([(-20, -9), (-29, 4)], O["beard_sh"], 0.9)], s=2.5)
    ear = [(-24, -4), (-16, -4.6), (-13.4, 3.6), (-15.4, 12.6), (-21.4, 13.4), (-24.8, 5)]
    out += C(smooth(ear), "skin", [line([(-17.4, -1), (-15.8, 4), (-18, 9.6)], dk, 1.0)], s=2.5)
    # the beard: from the sideburn in front of the ear, along the cheek to the
    # moustache, down over the chin and jutting forward onto the chest
    beard = [(-8.4, -5), (-5, 3), (1, 9), (9, 14.6), (15, 20), (20, 23.4), (24.4, 29), (27, 38), (26, 49), (21.4, 59), (13, 67), (3, 70, True), (-3, 63),
             (-9, 52), (-13, 40), (-15, 28), (-12.6, 17), (-10.6, 6)]
    strands = [line([(2, 16), (8, 32), (8, 50)], O["beard_sh"], 1.1), line([(14, 26), (19, 42), (15, 58)], O["beard_sh"], 1.1),
               line([(-8, 14), (-6, 34), (-2, 54)], O["beard_sh"], 1.0), line([(9, 22), (14, 36)], O["beard_lt"], 1.2),
               line([(20, 32), (22, 44)], O["beard_lt"], 1.2)]
    if O.get("grey"):
        strands += [line([(4, 30), (6, 44)], O["grey"], 1.1), line([(17, 46), (14, 58)], O["grey"], 1.1), line([(-4, 24), (-3, 38)], O["grey"], 1.0)]
    out += C(smooth(beard), "beard", strands, s=5)
    out += runga_side_stache()
    out += eye_side(0, 0, heavy=True)
    out.append(line([(-6.4, -6.2), (1, -8.4), (9.6, -6.8)], O["beard_sh"], 3.6))
    out.append(line([(-5.6, -6.6), (1, -8.6), (9, -7.2)], O["beard"], 1.6))
    return out


def runga_side_stache():
    stache = [(14, 16.8), (19, 17.4), (23.4, 19.6), (25.6, 23.6), (24.6, 27.0, True), (20.6, 25.2), (16, 24.4), (12.6, 21.8)]
    return cel(smooth(stache), O["beard_lt"], O["beard"], None, [line([(16.6, 19.6), (23, 22.4)], O["beard"], 0.9)], s=2, sw=1.3)


def eye_side(ex, ey, heavy=False):
    """A small eye in profile, the iris to the front, the upper lid heavy."""
    sk = O["skin_sh"]
    out = [path(smooth([(ex - 3.4, ey + 0.6), (ex + 0.6, ey - 1.7), (ex + 3.8, ey - 0.6), (ex + 3.2, ey + 1.4), (ex - 0.6, ey + 1.8)]), "#f2ece2"),
           E(ex + 2.2, ey - 0.1, 1.15, 1.7, "#4a3a30"), E(ex + 2.5, ey - 0.1, 0.6, 0.9, "#141414"),
           line([(ex - 3.8, ey + 0.4), (ex + 0.6, ey - 2.0), (ex + 4.2, ey - 0.8)], INK, 1.7),
           line([(ex - 2.4, ey + 2.2), (ex + 2.8, ey + 1.6)], INK, 0.7)]
    if heavy:
        out.append(line([(ex - 3.2, ey - 3.6), (ex + 1, ey - 4.6), (ex + 4.2, ey - 3.0)], sk, 1.0))
    out.append(line([(ex - 4.6, ey + 0.8), (ex - 7, ey - 0.4)], O["skin_dk"], 0.7))
    return out


def cutta_side_head():
    """Kutta in profile: neat dark hair combed back from a parting, a straight
    nose, a long upper lip under a full moustache, a firm clean-shaven chin and
    a lean cheek."""
    sk, dk = O["skin_sh"], O["skin_dk"]
    out = []
    face = [(-14, -37), (0, -38), (10, -33), (15, -23), (16.4, -13), (16.8, -6.6), (14.2, -2), (16.6, 4), (20, 9.6), (23.2, 13.6), (22.6, 16.4), (16.8, 17.4, True),
            (17.6, 22.6), (17.2, 25.2), (18.0, 27.4), (16.2, 30), (17.0, 33.4), (14, 37.4), (5, 38.2), (-5, 34), (-13, 26), (-19, 23), (-26, 22), (-32, 12),
            (-34.4, -2), (-33, -18), (-26, -30)]
    items = [line([(14.2, 10.4), (12.0, 13.2), (13.0, 16.4), (16.4, 17.2)], dk, 1.1), line([(17.6, 0), (21.6, 10)], O["skin_lt"], 1.5),
             line([(3, 12), (6, 22), (8, 28)], sk, 1.2), line([(-12, 25), (-2, 33), (10, 37)], sk, 1.2),
             line([(10, 4), (13, 7)], sk, 0.9)]
    out += C(smooth(face), "skin", items, s=6)
    ear = [(-19, -4), (-11.5, -4.6), (-9.4, 3.6), (-11.4, 12.4), (-17, 13), (-20, 5)]
    hair = [(14.4, -22), (11, -33), (0, -41.5), (-16, -42), (-29, -35), (-36.6, -20), (-36.4, -4), (-32.4, 10), (-26, 18), (-21.6, 8), (-19.6, -2), (-12, -6),
            (-9.6, 4, True), (-7, 4, True), (-6.8, -10), (-1, -17), (8, -21)]
    strands = [line([(10, -30), (-6, -37), (-24, -33)], O["hair_lt"], 1.2), line([(4, -24), (-12, -30), (-28, -24)], O["hair_sh"], 1.1),
               line([(-14, -20), (-28, -12), (-31, 2)], O["hair_sh"], 1.0)]
    out += C(smooth(hair), "hair", strands, s=3)
    out += C(smooth(ear), "skin", [line([(-13.4, -1), (-11.8, 4), (-14, 9.4)], dk, 1.0)], s=2.5)
    if O["stache"] == "kaiser":
        out += [line([(18.4, 26.2), (16.4, 26.4)], INK, 1.2)]
    out += cutta_side_stache()
    out += eye_side(0, 0)
    out.append(line([(-5.6, -5.8), (1, -8.4), (8.8, -7.6)], O["hair"], 2.4))  # one brow up: the dry look
    if O.get("pince"):
        out += [E(6.2, 0.4, 1.3, 4.4, O["glass"], INK, 1.0), line([(7.4, -2.4), (13.6, -3.6)], INK, 0.9),
                line([(5.6, 4.6), (2, 18), (-2, 34), (-1, 48)], "#20202a", 0.8)]
    return out


def cutta_side_stache():
    if O["stache"] == "kaiser":  # the ends waxed and turned up
        st = [(13, 17.6), (18, 17.8), (21.6, 19.4), (24.4, 18.0), (26.4, 14.0, True), (26.2, 18.6), (23.4, 22.2), (18, 22.8), (12.4, 21.4)]
    else:  # a full moustache, drooping over the lip
        st = [(13, 17.4), (17.6, 17.6), (21, 19.4), (22.6, 22.8), (21.8, 26.6, True), (18.6, 24.8), (14.6, 24.2), (11.8, 21.8)]
    return C(smooth(st), "hair", [line([(15.6, 19.6), (20.6, 21.4)], O["hair_lt"], 0.9)], s=2, sw=1.3)


def runga_front_head():
    sk, dk = O["skin_sh"], O["skin_dk"]
    out = []
    fringe = [(17, -24), (26, -25), (31.6, -14), (32.2, 0), (30, 12), (24, 14), (20, 0)]
    for pts in (fringe, mx(fringe, 0)):  # the short hair round the dome, seen past its sides
        out += C(smooth(pts), "beard", [], s=2)
    for sg in (-1, 1):  # the ears
        ex = sg * 26.5
        ear = smooth([(ex - sg * 1, -4), (ex + sg * 5, -6), (ex + sg * 7, 3), (ex + sg * 5, 13), (ex - sg * 0.5, 13)])
        out += C(ear, "skin", [line([(ex + sg * 2.4, -1), (ex + sg * 4.4, 4), (ex + sg * 2.6, 9)], dk, 1.0)], s=2)
    face = [(0, -41), (14, -38.5), (23, -29), (26.4, -15), (26.4, 0), (25, 14), (21, 25), (13, 32), (0, 35), (-13, 32), (-21, 25), (-25, 14), (-26.4, 0),
            (-26.4, -15), (-23, -29), (-14, -38.5)]
    items = [E(6, -31, 8, 3.6, O["skin_lt"], rot=-8), line([(-10, -22), (10, -22.6)], sk, 1.0), line([(-8, -17), (9, -17.4)], sk, 0.9),
             path(smooth([(-26, -6), (-24, 10), (-20, 20), (-23, 6)]), sk),
             # the nose: the bridge's shade, a broad round tip, the nostrils
             line([(-2.6, 2), (-3.4, 11)], sk, 1.6), line([(2.8, 2), (3.4, 10.4)], O["skin_lt"], 1.4),
             path(smooth([(-6.2, 13.2), (-3, 10.6), (0, 11.6), (3, 10.6), (6.2, 13.2), (5, 17.2), (0, 18.6), (-5, 17.2)]), sk),
             E(0.4, 13.4, 3.2, 2.8, O["skin"]), E(1.2, 12.6, 1.5, 1.2, O["skin_lt"]),
             line([(-6.4, 13.4), (-5.4, 17), (-2, 18.4), (2, 18.4), (5.4, 17), (6.4, 13.4)], INK, 1.1)]
    out += C(smooth(face), "skin", items, s=5)
    beard = [(25.6, -4), (27.6, 10), (29.6, 24), (28.6, 38), (23, 53), (13, 64), (0, 69, True), (-13, 64), (-23, 53), (-28.6, 38), (-29.6, 24), (-27.6, 10),
             (-25.6, -4), (-21, 6), (-15.6, 13.6), (-9, 19), (-3, 21), (0, 21.4), (3, 21), (9, 19), (15.6, 13.6), (21, 6)]
    strands = [line([(-14, 26), (-14, 44), (-8, 58)], O["beard_sh"], 1.1), line([(14, 26), (14, 44), (8, 58)], O["beard_sh"], 1.1),
               line([(0, 30), (0, 60)], O["beard_sh"], 1.0), line([(-22, 16), (-22, 40)], O["beard_sh"], 1.0), line([(22, 16), (22, 40)], O["beard_sh"], 1.0),
               line([(6, 34), (6, 50)], O["beard_lt"], 1.2), line([(-7, 36), (-6, 48)], O["beard_lt"], 1.1)]
    if O.get("grey"):
        strands += [line([(-10, 30), (-10, 46)], O["grey"], 1.1), line([(10, 44), (12, 56)], O["grey"], 1.1), line([(19, 26), (18, 36)], O["grey"], 1.0)]
    out += C(smooth(beard), "beard", strands, s=5)
    out += [E(0, 25, 4.6, 2.0, O["lip"], INK, 0.9)]
    out += runga_front_stache()
    for sg in (-1, 1):
        out += eye_front(sg * 11, 0, heavy=True)
        out.append(line([(sg * 4.8, -6.4), (sg * 11, -8.6), (sg * 17.6, -6.8)], O["beard_sh"], 3.6))
        out.append(line([(sg * 5.2, -6.8), (sg * 11, -8.8), (sg * 17, -7.2)], O["beard"], 1.6))
    out.append(line([(0, -9), (0, -4)], dk, 0.9))
    return out


def runga_front_stache():
    st = [(0, 18.6), (6, 18.2), (12, 20), (16.4, 25), (15.4, 28, True), (10, 25.6), (4, 24.4), (0, 24.6), (-4, 24.4), (-10, 25.6), (-15.4, 28, True), (-16.4, 25),
          (-12, 20), (-6, 18.2)]
    return cel(smooth(st), O["beard_lt"], O["beard"], None, [line([(0, 19.6), (0, 23.6)], O["beard"], 0.9)], s=2, sw=1.3)


def eye_front(cx, cy, heavy=False):
    sk = O["skin_sh"]
    out = [path(smooth([(cx - 4.4, cy + 0.6), (cx - 1.4, cy - 1.8), (cx + 1.6, cy - 2.0), (cx + 4.4, cy + 0.0), (cx + 2.0, cy + 1.8), (cx - 1.8, cy + 1.9)]), "#f2ece2"),
           E(cx, cy - 0.1, 1.7, 1.8, "#4a3a30"), E(cx, cy - 0.1, 0.8, 0.9, "#141414"),
           line([(cx - 4.8, cy + 0.6), (cx - 1.4, cy - 2.1), (cx + 1.6, cy - 2.3), (cx + 4.8, cy - 0.1)], INK, 1.6),
           line([(cx - 3.0, cy + 2.2), (cx + 2.8, cy + 2.0)], INK, 0.6)]
    if heavy:
        out.append(line([(cx - 4, cy - 3.8), (cx, cy - 4.8), (cx + 4, cy - 3.8)], sk, 1.0))
    return out


def cutta_front_head():
    sk, dk = O["skin_sh"], O["skin_dk"]
    out = []
    for sg in (-1, 1):
        ex = sg * 21
        ear = smooth([(ex - sg * 1, -4), (ex + sg * 4.6, -6), (ex + sg * 6.4, 3), (ex + sg * 4.4, 12), (ex - sg * 0.5, 12)])
        out += C(ear, "skin", [line([(ex + sg * 2.2, -1), (ex + sg * 4.0, 4), (ex + sg * 2.4, 9)], dk, 1.0)], s=2)
    face = [(0, -38), (13, -36), (20, -27), (21.4, -14), (21.4, 0), (20.4, 12), (17.4, 22), (12.4, 30), (6, 35.6), (0, 37), (-6, 35.6), (-12.4, 30), (-17.4, 22),
            (-20.4, 12), (-21.4, 0), (-21.4, -14), (-20, -27), (-13, -36)]
    items = [path(smooth([(-21, -4), (-19, 12), (-14, 24), (-17, 8)]), sk), line([(-13, 12), (-11, 22)], sk, 1.1), line([(13, 12), (11, 22)], sk, 1.1),
             line([(-2.2, 2), (-2.8, 10)], sk, 1.5), line([(2.4, 2), (2.8, 9.6)], O["skin_lt"], 1.3),
             path(smooth([(-5.0, 12.4), (-2.4, 10.4), (0, 11.2), (2.4, 10.4), (5.0, 12.4), (4.0, 15.6), (0, 16.6), (-4.0, 15.6)]), sk),
             E(0.3, 12.8, 2.5, 2.2, O["skin"]), E(0.9, 12.2, 1.2, 1.0, O["skin_lt"]),
             line([(-5.0, 12.6), (-4.4, 15.4), (-1.6, 16.6), (1.6, 16.6), (4.4, 15.4), (5.0, 12.6)], INK, 1.0),
             line([(-3, 33), (3, 33)], sk, 1.0)]
    out += C(smooth(face), "skin", items, s=5)
    hair = [(-21.6, -2), (-23, -20), (-18, -34), (-6, -42.5), (8, -42), (19, -35), (23, -21), (22, -2), (19.6, -10), (18, -21), (8, -25.6), (-6.4, -27.4, True),
            (-15, -22), (-19.4, -12)]
    out += C(smooth(hair), "hair", [line([(-6.4, -27), (-7.4, -40)], O["hair_lt"], 1.2), line([(0, -27), (12, -36), (18, -24)], O["hair_sh"], 1.0),
                                      line([(-10, -28), (-17, -26)], O["hair_sh"], 1.0)], s=3)
    if O["stache"] == "kaiser":
        out += [E(0, 24.6, 4.0, 1.6, O["lip"]), line([(-4.4, 23.6), (4.4, 23.6)], INK, 1.1)]
    else:
        out += [E(0, 27.0, 3.6, 1.4, O["lip"])]
    out += cutta_front_stache()
    for sg in (-1, 1):
        out += eye_front(sg * 10, 0)
    out.append(line([(-15.6, -6.4), (-10, -7.8), (-4.4, -6.6)], O["hair"], 2.3))
    out.append(line([(4.4, -7.6), (10, -10.2), (15.6, -8.6)], O["hair"], 2.3))  # his left brow up
    if O.get("pince"):
        for sg in (-1, 1):
            out.append(E(sg * 10, 0.4, 4.6, 4.2, O["glass"], INK, 1.0))
            out += eye_front(sg * 10, 0)
        out.append(line([(-5.4, -0.6), (0, -2.4), (5.4, -0.6)], INK, 1.0))
        out.append(line([(-14.4, 2), (-18, 14), (-20, 30), (-17, 46)], "#20202a", 0.8))
    return out


def cutta_front_stache():
    if O["stache"] == "kaiser":
        st = [(0, 18.0), (6, 17.8), (12, 18.6), (17, 15.4), (20.4, 10.4, True), (20.4, 15.4), (15, 20.6), (7, 21.6), (0, 21.0)]
    else:
        st = [(0, 17.4), (6, 17.2), (12, 19.4), (15.4, 24.4), (14.6, 28.4, True), (10, 25.4), (4, 24.0), (0, 24.4)]
    st = st + [(-p[0], p[1]) + tuple(p[2:]) for p in reversed(st[1:-1])]
    return C(smooth(st), "hair", [line([(-8, 19.4), (-3, 19)], O["hair_lt"], 0.9), line([(3, 19), (8, 19.4)], O["hair_lt"], 0.9)], s=2, sw=1.3)


# ---- hats --------------------------------------------------------------------------------------

def hat_side():
    kind = O.get("hat")
    if not kind:
        return []
    hc = "hat_c"
    out = []
    if kind == "tyrolean":
        crown = [(-31, -26), (-29, -42), (-19, -54), (-6, -51, True), (6, -55), (15, -47), (18, -30)]
        out += C(smooth(crown), hc, [line([(-4, -50), (-4, -38)], O[hc + "_sh"], 1.1)], s=3)
        band = smooth([(-31.4, -32, True), (18.4, -36, True), (18.6, -29, True), (-31, -25, True)])
        out += cel(band, O["hat_band"], dark(O["hat_band"]), None, [], s=1)
        brush = smooth([(-30, -32), (-36, -42), (-42, -50), (-38, -54), (-32, -48), (-26, -42), (-24, -34)])
        out += cel(brush, O["feather"], dark(O["feather"]), lite(O["feather"]), [line([(-24, -38), (-32, -52)], dark(O["feather"]), 0.9)], s=2)
        brim = smooth([(-44, -33, True), (-36, -28), (-16, -27.6), (4, -28.4), (20, -30), (30, -26.4), (28, -22.6, True), (8, -24), (-16, -22.6), (-38, -23)])
        out += C(brim, hc, [], s=2)
        return out
    if kind == "homburg":
        crown = [(-31, -25), (-30, -45), (-21, -55), (-6, -51, True), (6, -55.6), (16, -49), (19, -28)]
        out += C(smooth(crown), hc, [line([(-6, -51), (-7, -42)], O[hc + "_sh"], 1.2)], s=3)
        band = smooth([(-31.4, -33, True), (19.4, -35, True), (19.6, -27, True), (-31.2, -25, True)])
        out += cel(band, O["hat_band"], dark(O["hat_band"]), None, [], s=1)
        brim = smooth([(-44, -31, True), (-38, -25), (-16, -23.6), (6, -25.4), (24, -29), (33, -33, True), (30, -24), (8, -20.6), (-16, -19.4), (-40, -21)])
        out += C(brim, hc, [line([(-38, -24), (-14, -21.8), (8, -23.4), (26, -27)], O[hc + "_lt"], 1.0)], s=2)
        return out
    if kind == "bowler":
        crown = [(-31, -24), (-32, -38), (-23, -51), (-6, -56), (10, -52), (18, -41), (19, -27)]
        out += C(smooth(crown), hc, [line([(2, -52), (12, -45)], O[hc + "_lt"], 1.6)], s=3)
        band = smooth([(-31.6, -30, True), (19.4, -32, True), (19.6, -26, True), (-31.4, -24, True)])
        out += cel(band, O["hat_band"], dark(O["hat_band"]), None, [], s=1)
        brim = smooth([(-41, -25, True), (-36, -22), (-14, -22.4), (8, -24), (24, -26.6), (29, -28, True), (26, -21.4), (8, -20.4), (-16, -18.6), (-37, -18.6)])
        out += C(brim, hc, [], s=2)
        return out
    if kind == "cap":  # a soft motoring cap, the goggles strapped on above the peak
        cap = [(-35, -18), (-36, -30), (-28, -40), (-12, -45), (6, -43), (18, -34), (21, -27), (-6, -22), (-26, -16)]
        out += C(smooth(cap), hc, [line([(-30, -30), (-6, -38), (14, -32)], O[hc + "_sh"], 1.0), line([(-20, -40), (2, -42)], O[hc + "_lt"], 1.2)], s=4)
        peak = smooth([(10, -30, True), (22, -29), (33, -24.4), (32, -21.6, True), (18, -22.6), (8, -24)])
        out += C(peak, hc, [], s=1.5)
        if O.get("goggles"):
            out.append(line([(-34, -26), (-12, -34), (4, -36)], "#3a2c22", 3.2))
            out += cel(smooth([(2, -40.4), (12, -41), (15, -33.6), (8, -30.4), (1, -33)]), "#6f5a44", "#4a3a2c", "#8f785e", [], s=1.5)
            out.append(E(10.6, -36.0, 3.4, 4.2, "#9cc4cc", INK, 1.2))
            out.append(E(11.6, -37.4, 1.0, 1.4, "#e8f6f8"))
        return out
    raise KeyError(kind)


def hat_front():
    kind = O.get("hat")
    if not kind:
        return []
    hc = "hat_c"
    out = []
    if kind == "tyrolean":
        brush = smooth([(-20, -34), (-28, -46), (-32, -56), (-26, -58), (-21, -48), (-15, -38)])
        out += cel(brush, O["feather"], dark(O["feather"]), lite(O["feather"]), [line([(-21, -40), (-28, -54)], dark(O["feather"]), 0.9)], s=2)
        crown = [(-21, -27), (-20, -45), (-12, -55), (0, -50, True), (12, -55), (20, -45), (21, -27)]
        out += C(smooth(crown), hc, [line([(0, -50), (0, -38)], O[hc + "_sh"], 1.1)], s=3)
        out += cel(smooth([(-21.4, -34), (21.4, -34), (21.4, -27), (-21.4, -27)]), O["hat_band"], dark(O["hat_band"]), None, [], s=1)
        out += C(smooth([(-35, -31, True), (-22, -29), (0, -28.4), (22, -29), (35, -31, True), (30, -24), (0, -23.4), (-30, -24)]), hc, [], s=2)
        return out
    if kind == "homburg":
        crown = [(-20, -26), (-20, -47), (-12, -56), (0, -51, True), (12, -56), (20, -47), (20, -26)]
        out += C(smooth(crown), hc, [line([(0, -51), (0, -41)], O[hc + "_sh"], 1.2)], s=3)
        out += cel(smooth([(-20.4, -34), (20.4, -34), (20.4, -26), (-20.4, -26)]), O["hat_band"], dark(O["hat_band"]), None, [], s=1)
        out += C(smooth([(-34, -33, True), (-24, -27.4), (0, -26), (24, -27.4), (34, -33, True), (30, -22.4), (0, -20.8), (-30, -22.4)]), hc, [], s=2)
        return out
    if kind == "bowler":
        crown = [(-20, -25), (-21, -42), (-13, -53), (0, -56), (13, -53), (21, -42), (20, -25)]
        out += C(smooth(crown), hc, [line([(6, -51), (14, -44)], O[hc + "_lt"], 1.6)], s=3)
        out += cel(smooth([(-20.4, -31), (20.4, -31), (20.4, -25), (-20.4, -25)]), O["hat_band"], dark(O["hat_band"]), None, [], s=1)
        out += C(smooth([(-29, -27, True), (-22, -24.4), (0, -23.4), (22, -24.4), (29, -27, True), (26, -20.4), (0, -19.6), (-26, -20.4)]), hc, [], s=2)
        return out
    if kind == "cap":
        cap = [(-24, -20), (-25, -32), (-18, -42), (0, -46), (18, -42), (25, -32), (24, -20), (0, -22)]
        out += C(smooth(cap), hc, [line([(-16, -38), (0, -42), (16, -38)], O[hc + "_lt"], 1.2)], s=4)
        out += C(smooth([(-18, -24, True), (18, -24, True), (20, -19), (0, -17), (-20, -19)]), hc, [], s=1.5)
        if O.get("goggles"):
            out.append(line([(-24, -30), (0, -33), (24, -30)], "#3a2c22", 3.2))
            for sg in (-1, 1):
                out += cel(smooth([(sg * 3, -37), (sg * 14, -37.6), (sg * 15.4, -29.6), (sg * 3, -29)]), "#6f5a44", "#4a3a2c", "#8f785e", [], s=1.5)
                out.append(E(sg * 8.8, -33.4, 4.4, 3.4, "#9cc4cc", INK, 1.2))
                out.append(E(sg * 8.8 + 1.4, -34.6, 1.2, 0.9, "#e8f6f8"))
        return out
    raise KeyError(kind)


def s_head():
    head_frame("side")
    body = runga_side_head() if O["who"] == "runga" else cutta_side_head()
    body += hat_side()
    _XF[0] = None
    return body


def f_head():
    head_frame("front")
    body = runga_front_head() if O["who"] == "runga" else cutta_front_head()
    body += hat_front()
    _XF[0] = None
    return body


# ---- props -------------------------------------------------------------------------------------

def staff(top, bottom, w=3.0, key="wood"):
    """A staff from ``top`` to the ground: the alpenstock (ash, an iron spike)
    or the furled umbrella (black silk, a crook)."""
    out = []
    if O.get("staff"):
        wood, wsh, wlt = "#9a7a52", "#6e5436", "#b8986c"
        out += cel(capsule(top, (bottom[0], bottom[1] - 10), w, w * 0.9), wood, wsh, wlt, [], s=1.2)
        out += cel(smooth([(bottom[0] - w, bottom[1] - 12), (bottom[0] + w, bottom[1] - 12), (bottom[0] + 0.6, bottom[1], True), (bottom[0] - 0.6, bottom[1], True)]),
                   "#8a8e94", "#5d6168", "#b4b8be", [], s=1)
        out += cel(capsule((top[0], top[1] + 4), (top[0], top[1] + 14), w + 1.2, w + 1.2), "#6b4a2a", "#4a321c", None, [], s=1)
        return out
    # the umbrella: ferrule, the furled silk swelling below the handle, a crook
    a = ang(top, bottom)
    p = frame(top, a)
    L = math.hypot(bottom[0] - top[0], bottom[1] - top[1])
    silk = smooth([p(10, -2.2), p(L * 0.45, -6.6), p(L * 0.62, -5.6), p(L - 14, -1.8), p(L - 14, 1.8), p(L * 0.62, 5.0), p(L * 0.45, 6.2), p(10, 2.2)])
    out += cel(capsule(p(0, 0), p(L - 4, 0), 1.5, 1.3), "#2a2a2e", "#18181b", None, [], s=1)
    out += cel(silk, "#2a2a30", "#17171b", "#43434c", [line([p(L * 0.3, -3), p(L * 0.72, 2.4)], "#17171b", 1.0), line([p(L * 0.4, 4), p(L * 0.6, -4)], "#17171b", 0.9)], s=2)
    out += cel(capsule(p(L - 6, 0), p(L, 0), 1.3, 0.8), "#b8a072", "#8a7650", None, [], s=1)
    crook = smooth([p(-4, -2), p(-10, -2.5), p(-17, 2), p(-17, 10), p(-12, 13), p(-9, 10), p(-12, 8), p(-12, 4), p(-8, 2.4), p(-2, 2.4)])
    out += cel(crook, "#6a3c22", "#47271a", "#8c5434", [], s=1.2)
    return out


def ledger(hand_pt, front=False):
    """The ledger of coefficients, its spine held at his side: dark green
    cloth, a red label with the four weights."""
    x, y = hand_pt
    if front:
        d = smooth([(x - 5, y - 16, True), (x + 5, y - 18, True), (x + 6, y + 32, True), (x - 4, y + 34, True)])
        return cel(d, "#2f4a3c", "#1f3329", "#456a56", [line([(x, y - 16), (x, y + 28)], "#e8dfc8", 1.2)], s=1)
    d = smooth([(x - 26, y - 12, True), (x + 14, y - 22, True), (x + 24, y + 28, True), (x - 14, y + 38, True)])
    items = [path(smooth([(x - 13, y + 2, True), (x + 8, y - 3, True), (x + 11, y + 9, True), (x - 10, y + 14, True)]), "#a43a2e", INK, 0.8),
             line([(x - 9, y + 6), (x + 7, y + 2)], "#f0e2c0", 0.9), line([(x - 8, y + 10), (x + 8, y + 6)], "#f0e2c0", 0.9)]
    out = cel(d, "#2f4a3c", "#1f3329", "#456a56", items, s=3)
    out += cel(smooth([(x - 14, y + 38, True), (x + 24, y + 28, True), (x + 25, y + 31, True), (x - 13, y + 41, True)]), "#efe6d2", "#c9bea6", None, [], s=1)
    return out


# ---- the side view in layers -----------------------------------------------------------------

def cape_z(z):
    """Under an Inverness cape the arms (and what they hold) are drawn below the
    cape, and the cape below the head, so the beard falls over it."""
    return 51 + (z - 69) * 0.2 if O["coat_kind"] == "inverness" else z


def leg_split(hip, knee, ankle, near, front=False):
    """The leg as three parts, each on its own bone: ``(thigh, shin, shoe)``.
    Only trousers split; other legwear is one piece on the thigh."""
    if O["legs"] != "trousers":
        return leg_pieces(hip, knee, ankle, near, front), [], []
    return trouser_thigh(hip, knee, near), trouser_shin(knee, ankle, near, front), shoe(ankle, near, front)


def leg_layers(prefix, label, hip, knee, ankle, near, z, front=False):
    """The three leg parts in z order (shoe, shin, thigh: the thigh on top),
    their bones ``<prefix>_foot``, ``<prefix>_leg_l`` and ``<prefix>_leg_u``."""
    pieces = {}

    def piece(i):
        if not pieces:
            pieces.update(enumerate(leg_split(hip, knee, ankle, near, front)))
        return pieces[i]

    gid = prefix.replace("_", "-")
    return [(f"{gid}-shoe", f"{label} - Shoe", f"{prefix}_shoe", f"{prefix}_foot", z, lambda: piece(2)),
            (f"{gid}-shin", f"{label} - Shin", f"{prefix}_shin", f"{prefix}_leg_l", z + 1, lambda: piece(1)),
            (f"{gid}-thigh", f"{label} - Thigh", f"{prefix}_thigh", f"{prefix}_leg_u", z + 2, lambda: piece(0))]


# ---- the face's states: the shut eyes and the open mouth, drawn over the head -----------------

LID = [(-3.9, 0.6), (-1.0, -2.6), (2.0, -2.8), (4.4, -0.9), (3.6, 1.9), (-0.6, 2.4)]
FLID = [(-4.9, 0.7), (-1.6, -2.6), (1.6, -2.8), (4.9, 0.0), (2.2, 2.4), (-2.0, 2.5)]


def eyes_shut(view):
    """Both lids down: skin over each eye and the lash line, low and curved."""
    head_frame(view)
    out = []
    if view == "side":
        out += [path(smooth(LID), O["skin"]), line([(-3.8, 0.6), (0.4, 1.4), (4.2, 0.2)], INK, 1.6)]
        if O.get("pince"):
            out += [E(6.2, 0.4, 1.3, 4.4, O["glass"], INK, 1.0)]
    else:
        for cx in ((-11, 11) if O["who"] == "runga" else (-10, 10)):
            if O.get("pince"):
                out.append(E(cx, 0.4, 4.6, 4.2, O["glass"], INK, 1.0))
            out += [path(smooth([(cx + x, y) for x, y in FLID]), O["skin"] if not O.get("pince") else O["glass"]),
                     line([(cx - 4.6, 0.6), (cx, 1.6), (cx + 4.6, 0.6)], INK, 1.5)]
    _XF[0] = None
    return out


def mouth_open(view):
    """The mouth open to speak, under the moustache (drawn again over it)."""
    head_frame(view)
    dark_m, tongue = "#4a2220", "#a5524c"
    if view == "side":
        if O["who"] == "runga":
            out = [path(smooth([(15.6, 23.4), (22.6, 25.4), (21.0, 30.4, True), (16.4, 29.4)]), dark_m, INK, 1.1),
                   E(19.0, 28.6, 2.2, 1.1, tongue)]
            out += runga_side_stache()
        else:
            out = [path(smooth([(12.6, 24.0), (18.4, 24.4), (18.0, 29.6, True), (13.4, 28.0)]), dark_m, INK, 1.1),
                   E(16.0, 28.0, 1.8, 0.9, tongue)]
            out += cutta_side_stache()
    else:
        if O["who"] == "runga":
            out = [E(0, 27.4, 4.4, 3.6, dark_m, INK, 1.0), E(0, 29.4, 2.6, 1.3, tongue)]
            out += runga_front_stache()
        else:
            out = [E(0, 27.8, 3.6, 3.0, dark_m, INK, 1.0), E(0, 29.6, 2.2, 1.1, tongue)]
            out += cutta_front_stache()
    _XF[0] = None
    return out


#: The face's channels: (group id, label, part, z, channel), drawn on the head.
FACE_LAYERS = [("eyes-shut", "Eyes - Shut", "eyes_shut", 61, "eyes_shut"),
               ("mouth-open", "Mouth - Open", "mouth_open", 62, "mouth_open")]


def face_layers(view):
    return [(gid, lab, name, "head", z, (lambda fn=fn: fn(view)), channel)
            for (gid, lab, name, z, channel), fn in zip(FACE_LAYERS, (eyes_shut, mouth_open))]


def side_layers():
    ns, ne, nw = G["n_arm"]
    fs, fe, fw = G["f_arm"]
    nh, nk, na = G["n_leg"]
    fh, fk, fa = G["f_leg"]
    L = [
        ("far-arm-lower", "Far Arm - Lower", "far_arm_l", "far_arm_l", 6, lambda: fore_arm(fe, fw, near=False)),
        ("far-arm-upper", "Far Arm - Upper", "far_arm_u", "far_arm_u", 7, lambda: upper_arm(fs, fe, near=False)),
        ("far-hand", "Far Hand", "far_hand", "far_hand", 8, lambda: hand_at(fe, fw, near=False)),
        ("far-skirt", "Far Skirt", "far_skirt", "body", 9, lambda: s_skirt("far")),
    ]
    L += leg_layers("far", "Far Leg", fh, fk, fa, False, 10)
    L += [("pelvis", "Pelvis", "pelvis_yoke", "body", 19, s_pelvis)]
    L += leg_layers("near", "Near Leg", nh, nk, na, True, 20)
    L += [
        ("vest", "Waistcoat", "vest", "torso", 30, s_shirtfront),
        ("coat", "Coat", "coat", "torso", 36, s_coat_body),
        ("near-skirt", "Near Skirt", "near_skirt", "body", 40, lambda: s_skirt("near")),
        ("neck", "Neck, Collar and Tie", "neck", "torso", 50, s_neck),
        ("head", "Head", "head", "head", 60, s_head),
    ]
    L += face_layers("side")
    prop = []
    if O.get("staff"):
        prop = [("prop", "Alpenstock", "prop", "near_hand", 76, lambda: staff((nw[0] + 26 * HAND, nw[1] - 40), (nw[0] + 30 * HAND, GROUND_Y)))]
    if O.get("umbrella"):
        prop = [("prop", "Umbrella", "prop", "near_hand", 76, lambda: staff((nw[0] + 20 * HAND, nw[1] + 14), (nw[0] + 50, GROUND_Y - 1)))]
    if O.get("ledger"):
        prop = [("prop", "Ledger", "prop", "near_hand", 76, lambda: ledger((nw[0] + 8, nw[1] + 14)))]
    L += prop
    grip = bool(O.get("staff") or O.get("umbrella"))
    L += [
        ("near-arm-lower", "Near Arm - Lower", "near_arm_l", "near_arm_l", cape_z(77), lambda: fore_arm(ne, nw)),
        ("near-arm-upper", "Near Arm - Upper", "near_arm_u", "near_arm_u", cape_z(78), lambda: upper_arm(ns, ne)),
        ("near-hand", "Near Hand", "near_hand", "near_hand", cape_z(82), lambda: hand_at(ne, nw, grip=grip)),
        ("cape", "Cape", "cape", "torso", 56 if O["coat_kind"] == "inverness" else 90, s_cape),
    ]
    return L


def side_joints():
    """Where each bone turns: ``bone: (parent, x, y)``, parents first.  The
    pelvis is ``body`` (the root) and ``torso`` turns at the waist above it;
    the head turns at the top of the neck."""
    ns, ne, nw = G["n_arm"]
    fs, fe, fw = G["f_arm"]
    px, py = S([(0.5, G["hy"])])[0][:2]
    top, _base, _r = neck_line()
    J = {"body": ("", px, py), "torso": ("body", px, G["wy"]), "head": ("torso", *top)}
    J.update({"near_arm_u": ("torso", *ns), "near_arm_l": ("near_arm_u", *ne), "near_hand": ("near_arm_l", *nw),
              "far_arm_u": ("torso", *fs), "far_arm_l": ("far_arm_u", *fe), "far_hand": ("far_arm_l", *fw)})
    for side in ("n", "f"):
        h, k, a = G[f"{side}_leg"]
        nm = "near" if side == "n" else "far"
        J.update({f"{nm}_leg_u": ("body", *h), f"{nm}_leg_l": (f"{nm}_leg_u", *k), f"{nm}_foot": (f"{nm}_leg_l", *a)})
    return J


# ============================================================================================
# FRONT VIEW (his right on screen-left)
# ============================================================================================

def fr_arms():
    s, e, w = G["fr_arm"]
    return {"right": (s, e, w), "left": tuple((560 - p[0], p[1]) for p in (s, e, w))}


def fr_legs():
    h, k, a = G["fr_leg"]
    return {"right": (h, k, a), "left": tuple((560 - p[0], p[1]) for p in (h, k, a))}


def f_torso_under():
    """The shirt front and the waistcoat between the open coat's lapels."""
    nb, sy, wy, hy = G["nb"], G["sy"], G["wy"], G["hy"]
    kind = O["coat_kind"]
    out = C(smooth(F([(-0.5, nb), (0.5, nb), (0.6, sy + 30), (0, sy + 40), (-0.6, sy + 30)])), "shirt", [], s=2)
    if kind in ("frock", "lounge"):
        bottom = wy + 16 if kind == "frock" else wy + 10
        v = smooth(F([(-0.28, nb + 6), (0, nb + 26), (0.28, nb + 6), (0.62, sy + 10), (0.64, wy), (0.5, bottom, True), (0.02, bottom + 6), (-0.5, bottom, True),
                      (-0.64, wy), (-0.62, sy + 10)]))
        items = [E(280.6, y, 1.8, 1.8, O["button"], INK, 0.6) for y in range(int(nb + 34), int(bottom), 12)]
        if O.get("chain"):
            items.append(line(F([(-0.5, wy - 6), (-0.2, wy + 2), (0, wy - 4)]), O["gold"], 1.6))
        out += C(v, "vest", items + [line([(280, nb + 26), (280, bottom + 4)], O["vest_sh"], 1.0)], s=4)
    return out


def f_coat():
    nb, sy, wy, hy = G["nb"], G["sy"], G["wy"], G["hy"]
    kind = O["coat_kind"]
    hem = coat_len()
    out = []
    if kind == "frock":
        for side, pts in zip((-1, 1), FM([(0.3, nb + 2), (0.62, sy - 8), (1.0, sy + 6), (1.02, wy - 10), (1.0, wy), (1.04, hy), (1.1, hem, True), (0.5, hem + 2, True),
                                          (0.32, hy + 10), (0.30, wy + 8), (0.42, wy - 6), (0.56, sy + 16), (0.30, nb + 16)])):
            out += C(smooth(pts), "coat", [line(F([(side * 0.78, wy + 4), (side * 0.8, hem - 4)]), O["coat_sh"], 1.2),
                                           line(F([(side * 1.0, wy + 2), (side * 0.44, wy + 4)]), O["coat_sh"], 1.1)], s=6)
        for pts in FM([(0.28, nb + 2), (0.42, nb + 4), (0.66, sy + 18), (0.46, wy - 4), (0.34, wy + 4), (0.42, sy + 22), (0.30, nb + 18)]):
            out += C(smooth(pts), "facing", [], s=2)
        return out
    if kind == "lounge":
        body = F([(0.3, nb + 2), (0.62, sy - 8), (1.0, sy + 6), (1.02, wy - 10), (1.04, hy), (1.0, hem, True), (0.3, hem + 2), (0.06, hem - 8), (0.0, wy + 4),
                  (-0.0, sy + 24)])
        body = body + [(560 - p[0], p[1]) + tuple(p[2:]) for p in reversed(body)]
        items = [line([(280, sy + 22), (280, wy + 6), (284, hem - 8)], O["coat_sh"], 1.3)]
        items += [E(282, y, 1.9, 1.9, O["button"], INK, 0.6) for y in (sy + 30, sy + 46, wy + 0)]
        for sg in (-1, 1):
            items.append(path(smooth(F([(sg * 0.5, hy - 2, True), (sg * 0.9, hy - 2, True), (sg * 0.9, hy + 5), (sg * 0.5, hy + 5)])), O["coat_sh"], INK, 1.0))
        out += C(smooth(body), "coat", items, s=6)
        for pts in FM([(0.26, nb + 2), (0.40, nb + 4), (0.72, sy + 6), (0.52, sy + 10), (0.06, sy + 26), (0.28, nb + 18)]):
            out += C(smooth(pts), "coat", [], s=2)
        return out
    if kind == "norfolk":
        body = F([(0.3, nb + 2), (0.62, sy - 8), (1.0, sy + 6), (1.04, wy - 10), (1.06, hy), (1.06, hem, True), (0.0, hem + 2)])
        body = body + [(560 - p[0], p[1]) + tuple(p[2:]) for p in reversed(body[1:-1])] + [F([(-0.3, nb + 2)])[0]]
        items = [line([(280, sy + 18), (280, hem)], O["coat_sh"], 1.3)]
        for sg in (-1, 1):
            items += [line(F([(sg * 0.42, sy + 12), (sg * 0.42, hem)]), O["coat_sh"], 1.3), line(F([(sg * 0.62, sy + 12), (sg * 0.62, hem)]), O["coat_sh"], 1.3),
                      path(smooth(F([(sg * 0.2, wy + 12, True), (sg * 0.86, wy + 12, True), (sg * 0.86, hem - 6, True), (sg * 0.2, hem - 6, True)])), O["coat_sh"], INK, 1.0),
                      path(smooth(F([(sg * 0.18, wy + 10, True), (sg * 0.88, wy + 10, True), (sg * 0.88, wy + 19, True), (sg * 0.18, wy + 19, True)])), O["coat"], INK, 1.0)]
        items += [E(280, y, 2.0, 2.0, O["button"], INK, 0.6) for y in (sy + 26, sy + 46, hy - 2)]
        out += C(smooth(body), "coat", items, s=6)
        for pts in FM([(0.22, nb + 2), (0.40, nb + 4), (0.66, sy + 6), (0.42, sy + 8), (0.02, sy + 20), (0.20, nb + 14)]):
            out += C(smooth(pts), "coat", [], s=2)
        belt = smooth(F([(-1.07, wy - 6, True), (1.07, wy - 6, True), (1.07, wy + 4, True), (-1.07, wy + 4, True)]))
        out += C(belt, "coat", [line(F([(-1.06, wy - 1), (1.06, wy - 1)]), O["coat_sh"], 1.0)], s=2)
        out += cel(smooth([(273, wy - 8, True), (287, wy - 8, True), (287, wy + 6, True), (273, wy + 6, True)]), "#b4975a", "#8a7040", None,
                   [path(smooth([(276, wy - 5, True), (284, wy - 5, True), (284, wy + 3, True), (276, wy + 3, True)]), O["coat"])], s=1)
        return out
    if kind in ("duster", "inverness"):
        flare = 1.34 if kind == "duster" else 1.26
        body = F([(0.3, nb + 2), (0.62, sy - 8), (1.02, sy + 6), (1.06, wy - 10), (1.12, hy), (flare, hem, True), (0.0, hem + 3)])
        body = body + [(560 - p[0], p[1]) + tuple(p[2:]) for p in reversed(body[1:-1])] + [F([(-0.3, nb + 2)])[0]]
        items = [line([(282, sy + 18), (282, hy), (284, hem)], O["coat_sh"], 1.3)]
        if kind == "inverness":
            x0, x1 = F([(-1.6, nb)])[0][0], F([(1.6, nb)])[0][0]
            items = check_items(x0, nb, x1, hem + 4) + items
        for sg in (-1, 1):
            items.append(line(F([(sg * 0.7, hy), (sg * 0.9, hem - 4)]), O["coat_sh"], 1.2))
            if kind == "duster":
                items.append(line(F([(sg * 0.42, wy + 16), (sg * 0.62, wy + 34)]), INK, 1.4))
        items += [E(284, y, 2.0, 2.0, O["button"], INK, 0.6) for y in ((sy + 26, sy + 46, wy + 4) if kind == "duster" else (hy - 4, hy + 18, hy + 40))]
        out += C(smooth(body), "coat", items, s=7)
        if kind == "duster":
            for pts in FM([(0.22, nb), (0.44, nb + 2), (0.80, sy + 10), (0.52, sy + 14), (0.04, sy + 22), (0.20, nb + 14)]):
                out += C(smooth(pts), "coat", [], s=2)
        return out
    raise KeyError(kind)


def f_neck():
    nb, sy = G["nb"], G["sy"]
    hk = G["hk"]
    fy = G["feye"][1]
    r = 11.8 * hk
    out = C(capsule((280, fy + 26 * hk), (280, nb + 6), r, r), "skin", [line([(280 - r + 3, fy + 34 * hk), (280 - r + 4, nb)], O["skin_sh"], 1.0)], s=4)
    kind = O["collar"]
    if kind == "scarf":
        out += C(smooth([(280 - r - 6, nb - 14), (280 + r + 6, nb - 14), (280 + r + 9, nb + 2), (280, nb + 6), (280 - r - 9, nb + 2)]), "scarf",
                 [line([(280 - r - 4, nb - 6), (280 + r + 4, nb - 6)], O["scarf_sh"], 1.0)], s=3)
        out += C(smooth([(284, nb - 2), (294, nb), (296, nb + 36), (289, nb + 44, True), (283, nb + 28)]), "scarf",
                 [line([(289, nb + 4), (290, nb + 36)], O["scarf_sh"], 1.0)], s=2)
        return out
    ct = nb - (16 if kind == "high" else 11)
    col = smooth([(280 - r - 2, ct, True), (280 + r + 2, ct, True), (280 + r + 3, nb + 3, True), (280, nb + 6), (280 - r - 3, nb + 3, True)])
    out += C(col, "shirt", [line([(280, ct + 1), (280, nb + 4)], O["shirt_sh"], 1.0)], s=2.5)
    if kind == "wing":
        for sg in (-1, 1):
            out += C(smooth([(280 + sg * 1.5, ct + 3), (280 + sg * 9, ct + 6), (280 + sg * 4, ct + 10, True)]), "shirt", [], s=1)
    tie = O["tie"]
    if kind in ("soft", "high"):  # a four-in-hand: the knot and a narrow blade into the waistcoat
        out += cel(smooth([(276.6, nb - 2, True), (283.4, nb - 2, True), (282, nb + 5, True), (278, nb + 5, True)]), tie, dark(tie), lite(tie), [], s=1)
        out += cel(smooth([(278, nb + 5), (282, nb + 5), (283.6, sy + 18), (280, sy + 23, True), (276.4, sy + 18)]), tie, dark(tie), lite(tie),
                   [line([(281, nb + 8), (282, sy + 16)], dark(tie), 0.9)], s=1.5)
    else:  # a bow tie
        out += cel(smooth([(269, nb - 5), (280, nb - 1, True), (291, nb - 5), (291, nb + 4), (280, nb + 1, True), (269, nb + 4)]), tie, dark(tie), lite(tie), [], s=1.5)
        out += cel(smooth([(277.4, nb - 3.6, True), (282.6, nb - 3.6, True), (282.6, nb + 2.6, True), (277.4, nb + 2.6, True)]), dark(tie), dark(tie, 0.6), None, [], s=1)
    return out


def f_arm(side, piece):
    s, e, w = fr_arms()[side]
    if piece == "upper":
        return upper_arm(s, e)
    if piece == "lower":
        return fore_arm(e, w)
    return hand_front(w, ang(e, w), 1 if side == "right" else -1)


def f_cape():
    if O["coat_kind"] != "inverness":
        return []
    nb, sy, wy, hy = G["nb"], G["sy"], G["wy"], G["hy"]
    body = F([(0.30, nb - 6), (0.66, sy - 10), (1.14, sy + 8), (1.36, wy - 8), (1.50, hy - 4, True), (0.6, hy + 6), (0.10, hy + 4, True), (0.08, sy + 20)])
    out = []
    for sg in (-1, 1):
        pts = body if sg > 0 else [(560 - p[0], p[1]) + tuple(p[2:]) for p in body]
        x0, x1 = (280, 380) if sg > 0 else (180, 281)
        items = check_items(x0, nb - 10, x1, hy + 12) + [line(F([(sg * 0.7, sy + 10), (sg * 0.86, hy)]), O["coat_sh"], 1.2)]
        out += C(smooth(pts), "coat", items, s=7)
    collar = smooth(F([(-0.86, nb - 14), (-0.3, nb - 18), (0.3, nb - 18), (0.86, nb - 14), (0.9, nb + 2), (0.4, nb + 8), (0, nb + 14), (-0.4, nb + 8), (-0.9, nb + 2)]))
    return out + C(collar, "coat", [], s=3)


def front_layers():
    L = [("pelvis", "Pelvis", "pelvis_yoke", "body", 9, lambda: C(smooth(F([(-0.8, G["hy"] - 16, True), (0.8, G["hy"] - 16, True), (0.7, G["hy"] + 12, True),
                                                                       (-0.7, G["hy"] + 12, True)])), "trousers" if O["legs"] != "knickers" else "knick", [], s=3))]
    for side, lab, z in (("left", "Left Leg", 10), ("right", "Right Leg", 14)):
        h, k, a = fr_legs()[side]
        L += leg_layers(side, lab, h, k, a, True, z, front=True)
    L += [("vest", "Shirt and Waistcoat", "vest", "torso", 30, f_torso_under),
          ("coat", "Coat", "coat", "torso", 36, f_coat),
          ("neck", "Neck, Collar and Tie", "neck", "torso", 50, f_neck),
          ("head", "Head", "head", "head", 60, f_head)]
    L += face_layers("front")
    z = 70
    s_r, e_r, w_r = fr_arms()["right"]
    if O.get("staff"):
        L.append(("prop", "Alpenstock", "prop", "right_hand", 69, lambda: staff((w_r[0] + 4, w_r[1] - 36), (w_r[0] + 4, GROUND_Y))))
    if O.get("umbrella"):
        L.append(("prop", "Umbrella", "prop", "right_hand", 69, lambda: staff((w_r[0] + 2, w_r[1] + 16), (w_r[0] - 10, GROUND_Y - 1))))
    if O.get("ledger"):
        L.append(("prop", "Ledger", "prop", "right_hand", 69, lambda: ledger((w_r[0] - 2, w_r[1] + 14), front=True)))
    for side, lab in (("left", "Left"), ("right", "Right")):
        L += [(f"{side}-arm-lower", f"Arm - {lab} - Lower", f"{side}_arm_l", f"{side}_arm_l", cape_z(z), lambda s=side: f_arm(s, "lower")),
              (f"{side}-arm-upper", f"Arm - {lab} - Upper", f"{side}_arm_u", f"{side}_arm_u", cape_z(z + 1), lambda s=side: f_arm(s, "upper")),
              (f"{side}-hand", f"Arm - {lab} - Hand", f"{side}_hand", f"{side}_hand", cape_z(z + 2), lambda s=side: f_arm(s, "hand"))]
        z += 5
    L.append(("cape", "Cape", "cape", "torso", 56 if O["coat_kind"] == "inverness" else 90, f_cape))
    return L


def front_joints():
    J = {"body": ("", 280.0, G["hy"]), "torso": ("body", 280.0, G["wy"]), "head": ("torso", 280.0, G["nb"] - 4)}
    for side, (s, e, w) in fr_arms().items():
        J.update({f"{side}_arm_u": ("torso", *s), f"{side}_arm_l": (f"{side}_arm_u", *e), f"{side}_hand": (f"{side}_arm_l", *w)})
    for side, (h, k, a) in fr_legs().items():
        J.update({f"{side}_leg_u": ("body", *h), f"{side}_leg_l": (f"{side}_leg_u", *k), f"{side}_foot": (f"{side}_leg_l", *a)})
    return J


# ============================================================================================
# documents
# ============================================================================================

VIEWS = {"side": ("Side Right", side_layers, side_joints), "front": ("Front", front_layers, front_joints)}
NAMES = {"runga": "Carl Runga", "cutta": "Martin Cutta"}
FILES = {"runga": "carl_runga", "cutta": "martin_cutta"}


def svg_text(who: str, look: str, view: str, rig: bool = False) -> str:
    """One view of one look.  ``rig`` writes the cast drawing (the face's
    channel layers hidden by default); without it, a candidate (every layer
    shown but the face's channels, which a candidate leaves out)."""
    use(who, look)
    _N[0] = 0
    svg.configure(dx=0, dy=0, ink=INK, ow=OW, colors={})
    label, layers, joints = VIEWS[view]
    for layer in layers():
        group, plabel, name, bone, z, painter = layer[:6]
        channel = layer[6] if len(layer) > 6 else ""
        if channel and not rig:
            continue
        _XF[0] = None
        part(group, plabel, name, bone, z, painter(), f' data-rig-opacity="{channel}"' if channel else "")
    _XF[0] = None
    J = joints()
    if rig:
        design = f"{FILES[who]}-v2"
        comment = [f"  <!-- {NAMES[who]} v2: look {look}, {O['label']}, {label} (cast 2026-10-23); the ground at y={GROUND_Y:g}.",
                   "       Drawn by scripts/svg_art/runge_kutta_duo_art.py (its rig mode); each part turns about its joint below. -->"]
    else:
        design = f"{FILES[who]}-r1-{look.lower()}"
        comment = [f"  <!-- CANDIDATE, NOT CAST: {NAMES[who]}, {O['label']}, {label} (2026-10-22); the ground at y={GROUND_Y:g}.",
                   "       Drawn by scripts/svg_art/runge_kutta_duo_art.py. -->"]
    return svg.document(
        size=(W, H), design=design, layer_id=FILES[who].replace("_", "-"), label=view_label(who, view),
        comment=comment, joints=svg.joints_layer({k: (v[1], v[2]) for k, v in J.items()}),
    )


def view_label(who: str, view: str) -> str:
    """The SVG view layer's label, which a rig document names as its view."""
    return f"{NAMES[who]} - {VIEWS[view][0]}"


#: The cast look (Jon did not pick from round 1; chosen 2026-10-23: A).
CAST_LOOK = "A"
#: The drawing a rig reads: ``data/characters/<file>_v2/<file>_v2_<view>.svg``.
DATA = Path(__file__).resolve().parents[2] / "ambition_sprite2d_renderer" / "data" / "characters"


def rig_svg_path(who: str, view: str) -> Path:
    return DATA / f"{FILES[who]}_v2" / f"{FILES[who]}_v2_{view}.svg"


def joints_of(who: str, view: str) -> Dict[str, tuple]:
    """``bone: (parent, x, y)`` of the cast look in one view (SVG units)."""
    use(who, CAST_LOOK)
    return VIEWS[view][2]()


def layers_of(who: str, view: str) -> List[tuple]:
    """``(group, label, part, bone, z, channel)`` of the cast look in one view."""
    use(who, CAST_LOOK)
    return [tuple(layer[:5]) + ((layer[6] if len(layer) > 6 else ""),) for layer in VIEWS[view][1]()]


# ============================================================================================
# contact sheets
# ============================================================================================

def _render(text, zoom):
    import resvg_py
    from PIL import Image
    text = text.replace(f'width="{W}mm" height="{H}mm"', f'width="{W}" height="{H}"')
    png = bytes(resvg_py.svg_to_bytes(svg_string=text, zoom=zoom))
    return Image.open(io.BytesIO(png)).convert("RGBA")


#: The game draws Runga about 96 px tall; Cutta at his own height on the same scale.
GAME_ZOOM = 96.0 / (GROUND_Y - 146.0)
BG = (214, 219, 226, 255)


def _crop_body(im, pad=6):
    """The figure's bounding box, padded; its bottom is the soles (the ground)."""
    box = im.getbbox()
    return im.crop((box[0] - pad, box[1] - pad, box[2] + pad, box[3]))


def _font(size, bold=True):
    from PIL import ImageFont
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    try:
        return ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{name}", size)
    except OSError:
        return ImageFont.load_default()


def _game(text, scale=3):
    from PIL import Image
    im = _render(text, GAME_ZOOM)
    return im.resize((im.size[0] * scale, im.size[1] * scale), Image.NEAREST)


def character_sheet(who: str, out: Path) -> Path:
    from PIL import Image, ImageDraw
    rows = []
    z = 1.5
    for look in "ABC":
        side, front = svg_text(who, look, "side"), svg_text(who, look, "front")
        s_im, f_im = _render(side, z), _render(front, z)
        s_im, f_im = _crop_body(s_im, 16), _crop_body(f_im, 16)
        use(who, look)
        ex, ey = G["eye"]
        hz = 4.0
        head = _render(side, hz).crop((int((ex - 62) * hz), int((ey - 62) * hz), int((ex + 44) * hz), int((ey + 80) * hz)))
        head = head.resize((int(head.size[0] * 0.8), int(head.size[1] * 0.8)), Image.LANCZOS)
        fx, fy = G["feye"]
        fhead = _render(front, hz).crop((int((fx - 48) * hz), int((fy - 62) * hz), int((fx + 48) * hz), int((fy + 80) * hz)))
        fhead = fhead.resize((int(fhead.size[0] * 0.8), int(fhead.size[1] * 0.8)), Image.LANCZOS)
        g_side, g_front = _crop_body(_game(side), 12), _crop_body(_game(front), 12)
        rows.append((O["label"], [s_im, f_im, head, fhead, g_side, g_front]))
    gap, lab = 24, 34
    width = max(sum(i.size[0] for i in ims) + gap * (len(ims) + 1) for _, ims in rows)
    height = sum(max(i.size[1] for i in ims) + lab + gap for _, ims in rows)
    sheet = Image.new("RGBA", (width, height), BG)
    d = ImageDraw.Draw(sheet)
    y = 0
    for label, ims in rows:
        d.text((gap, y + 10), label, fill=(24, 24, 28, 255), font=_font(20))
        x = gap
        hrow = max(i.size[1] for i in ims)
        for i, im in enumerate(ims):
            yy = y + lab + (hrow - im.size[1] if i in (0, 1, 4, 5) else 0)  # the figures stand on the row's floor
            sheet.alpha_composite(im, (x, yy))
            x += im.size[0] + gap
        y += hrow + lab + gap
    d.text((width - 520, height - 22), "side | front | head side | head front | game size x3 (side, front)", fill=(80, 84, 92, 255), font=_font(13, False))
    out.mkdir(parents=True, exist_ok=True)
    p = out / f"{FILES[who]}_r1.png"
    sheet.convert("RGB").save(p)
    return p


def duo_sheet(out: Path) -> Path:
    from PIL import Image, ImageDraw
    rows = []
    for look in "ABC":
        ims = []
        for view in ("side", "front"):
            pair = [_crop_body(_game(svg_text(who, look, view)), 6) for who in ("runga", "cutta")]
            ims.append(pair)
        big = [_crop_body(_render(svg_text(who, look, "side"), 1.3), 4) for who in ("runga", "cutta")]
        rows.append((look, ims, big))
    gap, lab = 28, 34
    sheet_w = 40 + max(sum(i.size[0] + 4 for pair in [big] + ims for i in pair) + 2 * gap * 3 for _, ims, big in rows)
    hrow = 0
    for _, ims, big in rows:
        hrow = max(hrow, max(i.size[1] for pair in ims for i in pair), max(i.size[1] for i in big))
    sheet = Image.new("RGBA", (sheet_w, (hrow + lab + gap) * len(rows)), BG)
    d = ImageDraw.Draw(sheet)
    y = 0
    for look, ims, big in rows:
        use("runga", look)
        a = O["label"].split(" - ")[0]
        use("cutta", look)
        b = O["label"].split(" - ")[0].split(": ")[1]
        d.text((gap, y + 8), f"{a} + {b}", fill=(24, 24, 28, 255), font=_font(20))
        x = gap
        for pair in [big] + ims:
            for im in pair:
                sheet.alpha_composite(im, (x, y + lab + hrow - im.size[1]))
                x += im.size[0] + 4
            x += gap * 2
        y += hrow + lab + gap
    d.text((gap, sheet.size[1] - 22), "side (1.3x) | game size x3: side, front - Runga left, Cutta right", fill=(80, 84, 92, 255), font=_font(13, False))
    p = out / "duo_r1.png"
    sheet.convert("RGB").save(p)
    return p


def main() -> None:
    if len(sys.argv) > 2 and sys.argv[1] == "--all":
        out = Path(sys.argv[2])
        out.mkdir(parents=True, exist_ok=True)
        for who in LOOKS:
            for look in LOOKS[who]:
                for view in VIEWS:
                    p = out / f"{FILES[who]}_{look}_{view}.svg"
                    p.write_text(svg_text(who, look, view), encoding="utf8")
                    print(p)
        return
    if len(sys.argv) > 2 and sys.argv[1] == "--sheets":
        out = Path(sys.argv[2])
        for who in LOOKS:
            print(character_sheet(who, out))
        print(duo_sheet(out))
        return
    if len(sys.argv) > 1 and sys.argv[1] == "--rig":
        for who in LOOKS:
            for view in VIEWS:
                out = rig_svg_path(who, view)
                out.parent.mkdir(parents=True, exist_ok=True)
                tmp = out.with_suffix(".svg.tmp")
                tmp.write_text(svg_text(who, CAST_LOOK, view, rig=True), encoding="utf8")
                tmp.replace(out)
                print(out)
        return
    raise SystemExit("usage: runge_kutta_duo_art.py --rig | --all DIR | --sheets DIR")


if __name__ == "__main__":
    main()
