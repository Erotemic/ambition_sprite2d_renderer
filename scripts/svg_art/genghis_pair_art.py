#!/usr/bin/env python3
"""Genghis Can and Genghis Can't, redesigned: three looks, and the cast one as rig-ready SVGs.

    uv run python scripts/svg_art/genghis_pair_art.py --rig         # look C of both, one part per bone (the cast drawings)
    uv run python scripts/svg_art/genghis_pair_art.py --all DIR     # side + front SVG of every look of both, to DIR
    uv run python scripts/svg_art/genghis_pair_art.py --sheets DIR  # the round-1 contact sheets (needs resvg_py)

THE CAST LOOK is C, ``steppe`` (2026-10-23). ``--rig`` writes
``data/characters/genghis_<who>_v2/genghis_<who>_v2.svg``; the SVG owns the
art after this has run. ``joints(who)`` says where each part turns and
``rig_parts(who)`` lists the parts; ``scripts/build_genghis_pair_v2_rig.py``
reads both and authors the rows. The targets are ``genghis_can_v2`` and
``genghis_cant_v2``. Looks A (``portrait``) and B (``warlord``) are KEPT, NOT
CAST: ``--all`` draws them and nothing registers them. The first design (the
procedural ``genghis_can`` / ``genghis_cant``) stays renderable as the lineage.

WHO THEY ARE (``character_catalog.ron``, ``dialogue/sandbox/hall.yarn``): two
brothers, both Genghis Khan.  The joke is the pun on Khan: Genghis CAN says
yes before he checks ("Can I take this hall? Yes. Next question."); Genghis
CAN'T has a horde and also reservations ("I have reconsidered leaving this
stand six times since you walked up").  "They named him for what he does.
They named me for what I consider."  Can is 173 cm, Can't 170 cm.

HOW THE DESIGN CARRIES THE JOKE.  Both read as Genghis Khan first (Jon: a
parody reads as its person): the deel crossed to the right with its trimmed
closure and knot buttons, a broad sash, horse-hoof cuffs, booted feet with
turned-up toes, the long thin moustache and chin tuft of the Yuan court
portrait, and the hair looped behind the ears.  The pun is carried by the
body, so it reads at game size:

* CAN stands tall, chest out, chin up; his moustache sweeps and his chin
  tuft points forward; brows level and low.  Everything on him that can
  stand up, stands up (the cap ribbons fly, the plume rises, the fur flaps
  are tied up).
* CAN'T stoops, chin down, shoulders up; brows lifted in the middle; his
  moustache and tuft droop, and he has gone greyer (he worries).  Everything
  on him that can droop, droops.

THE THREE LOOKS (each drawn for both brothers):

* ``portrait``: the Yuan court portrait -- a white felt cap with a fur brim
  and ribbons, a pale deel.  Can stands akimbo; Can't reads a map.
* ``warlord``: lamellar armour over the deel and a spiked helmet with a
  horsehair plume.  Can raises his sabre, plume UP; Can't wrings his hands,
  sabre still sheathed, plume DOWN.
* ``steppe``: a winter deel and a fox-fur hat.  Can points the way, flaps
  tied up; Can't cups his chin, flaps down and tied under it.

House style: Oiler's (``oiler_art.py``): flat cel fills with one shade band
down-left and a light band up-right, thick warm ink, adult proportions, small
eyes.  No drop shadows.  Side view faces right; the front view has his right
on screen-left.
"""
from __future__ import annotations

import io
import math
import sys
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).resolve().parent))
import svgkit as svg  # noqa: E402
from svgkit import capsule, ellipse, line, path, smooth  # noqa: E402

W = H = 560
INK = "#1d1714"
OW = 1.5
GROUND_Y = 502.0
CX = 280.0
#: Shade down-left, light up-right.
SD, LD = (-1.0, 0.6), (1.0, -0.8)
WHITE = "#f7f3ea"

BASE = dict(
    skin="#d9a67e", skin_sh="#b47e5a", skin_lt="#ebc39f", skin_dk="#87563b", lip="#a9665a", blush="#d99579",
    eye="#231915",
    boot="#3b2b22", boot_sh="#22180f", boot_lt="#5a4436",
    sole="#1b130e", sole_sh="#0f0a07",
    metal="#aab2bb", metal_sh="#78818c", metal_lt="#dde2e8",
    parch="#e9d6a8", parch_sh="#c7ad76", parch_lt="#f6ead0", route="#8a3b2a", river="#5a86a8",
    gold="#d8a53a", gold_sh="#a2721c", gold_lt="#f1cd6a",
    wood="#6b4428", wood_sh="#45291a", wood_lt="#8c5d3a",
)

#: The brothers: posture, face and hair.  Can't is greyer.
WHO = {
    "can": dict(name="Genghis Can", lean=-4.0, scale=1.0, broad=1.05, brow="stern", mouth="firm", stache="sweep", beard="spear",
                hair="#2a211d", hair_sh="#15100d", hair_lt="#54463c", f_head_dy=0.0, f_tilt=0.0, f_shrug=0.0),
    "cant": dict(name="Genghis Can't", lean=8.0, scale=0.975, broad=0.97, brow="worried", mouth="unsure", stache="droop", beard="wisp",
                 hair="#77706b", hair_sh="#4f4946", hair_lt="#a59e98", f_head_dy=7.0, f_tilt=-6.0, f_shrug=-5.0),
}

LOOKS = {
    "portrait": dict(
        label="portrait", blurb="the Yuan court portrait: white felt cap, fur brim, pale deel",
        can=dict(hat="cap", pose="akimbo", pitch=-6.0,
                 deel="#ece5d5", deel_sh="#c4baa4", deel_lt="#faf6ec", trim="#5e3a28", trim_sh="#3e2418", trim_lt="#7e5440",
                 sash="#b3302a", sash_sh="#80201c", sash_lt="#d0544a",
                 hatc="#f1ece0", hatc_sh="#c9c1af", hatc_lt="#fdfbf5", fur="#d8cdb8", fur_sh="#a99c84", fur_lt="#efe7d8",
                 ribbon="#b3302a", ribbon_sh="#80201c", ribbon_lt="#d0544a"),
        cant=dict(hat="cap", pose="map", pitch=16.0,
                  deel="#9fb2c2", deel_sh="#76899b", deel_lt="#bccbd6", trim="#3e4a5a", trim_sh="#28313d", trim_lt="#5a6878",
                  sash="#b98f3c", sash_sh="#8a6826", sash_lt="#d4ae60",
                  hatc="#e6e2d8", hatc_sh="#bdb7a8", hatc_lt="#f6f3ec", fur="#b9b1a4", fur_sh="#8d857a", fur_lt="#d4cec4",
                  ribbon="#5a6c86", ribbon_sh="#3e4c62", ribbon_lt="#7a8ca6"),
    ),
    "warlord": dict(
        label="warlord", blurb="lamellar over the deel, spiked helmet, horsehair plume",
        can=dict(hat="helmet", plume="up", armor=True, pose="sabre", pitch=-5.0,
                 deel="#a3272a", deel_sh="#741a1e", deel_lt="#c2443e", trim="#d8a53a", trim_sh="#a2721c", trim_lt="#f1cd6a",
                 sash="#2f3a52", sash_sh="#1e2638", sash_lt="#46557a",
                 lam="#c9953c", lam_sh="#94681f", lam_lt="#e9c06a", lace="#7a1e1c",
                 helm="#c9953c", helm_sh="#94681f", helm_lt="#ecc672", band="#7a1e1c", band_sh="#55130f", band_lt="#a03430",
                 plumec="#c22a26", plumec_sh="#861a18", plumec_lt="#e45a48",
                 avent="#a3272a", avent_sh="#741a1e", avent_lt="#c2443e"),
        cant=dict(hat="helmet", plume="down", armor=True, pose="clasp", pitch=8.0, sheathed=True,
                  deel="#3c5878", deel_sh="#283d56", deel_lt="#57789a", trim="#a8a28c", trim_sh="#7d7866", trim_lt="#c9c3ac",
                  sash="#6a5a3c", sash_sh="#4a3e28", sash_lt="#8a7854",
                  lam="#8a929b", lam_sh="#5f6770", lam_lt="#b4bcc4", lace="#2c3e58",
                  helm="#8a929b", helm_sh="#5f6770", helm_lt="#bcc3ca", band="#2c3e58", band_sh="#1c2a3e", band_lt="#46607e",
                  plumec="#d8d2c4", plumec_sh="#a49c8c", plumec_lt="#f2eee4",
                  avent="#3c5878", avent_sh="#283d56", avent_lt="#57789a"),
    ),
    "steppe": dict(
        label="steppe", blurb="winter deel, fox-fur hat with ear flaps, quiver",
        can=dict(hat="fur", flaps="up", pose="point", pitch=-4.0,
                 deel="#2f6d8a", deel_sh="#1f4c62", deel_lt="#4a90ac", trim="#e0a43a", trim_sh="#a8781e", trim_lt="#f6c86a",
                 sash="#d0662a", sash_sh="#9a4618", sash_lt="#ec8a4c",
                 hatc="#2f6d8a", hatc_sh="#1f4c62", hatc_lt="#4a90ac", fur="#b7652e", fur_sh="#82421a", fur_lt="#d98c50",
                 knot="#c42a26", case="#7a4a26", case_sh="#54301a", case_lt="#9c6838"),
        cant=dict(hat="fur", flaps="down", pose="chin", pitch=4.0,
                  deel="#7e4f55", deel_sh="#5a363c", deel_lt="#9c6a70", trim="#4f6476", trim_sh="#36475a", trim_lt="#6c8296",
                  sash="#5a6e80", sash_sh="#3e4e5e", sash_lt="#7a8ea0",
                  hatc="#5a3a40", hatc_sh="#3e262b", hatc_lt="#7a5258", fur="#9a948c", fur_sh="#6e6862", fur_lt="#bcb6ae",
                  knot="#5a6e80", case="#5c4a36", case_sh="#3e3224", case_lt="#7a654c"),
    ),
}
LOOK_ORDER = ("portrait", "warlord", "steppe")
LETTER = dict(portrait="A", warlord="B", steppe="C")
O: Dict = {}


def use(look: str, who: str) -> None:
    O.clear()
    O.update(BASE)
    O.update(WHO[who])
    O.update(LOOKS[look][who])
    O["who"], O["look"] = who, look


# ---- the point map: posture rotations, then the figure's scale about the ground ------------------

_P0 = svg.P
_MAP: Dict = {"rots": [], "scale": 1.0}


def _rot(x, y, cx, cy, deg):
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c


def _P(x, y):
    for cx, cy, deg in _MAP["rots"]:
        x, y = _rot(x, y, cx, cy, deg)
    k = _MAP["scale"]
    x, y = CX + (x - CX) * k, GROUND_Y + (y - GROUND_Y) * k
    return _P0(x, y)


svg.P = _P

_N = [0]


def uid(tag="c"):
    _N[0] += 1
    return f"gk{tag}{_N[0]}"


def cel(d, base, shade, light=None, items=(), sdir=SD, ldir=LD, s=5.0, l=3.0, sw=None, ink=None, edges=None):
    """A shape: its fill, a ``shade`` band along the edges facing ``sdir`` and a
    ``light`` band along those facing ``ldir`` (clipped inside), the detail
    ``items``, then the ink outline -- or ink on the open runs ``edges`` only.
    (Oiler's helper, unchanged.)"""
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


def far(d, key, items=(), **kw):
    """A shape on the far side of the body: its colour in shade, no light band."""
    return cel(d, O[key + "_sh"], O[key + "_sh"], None, items, s=1, **kw)


def frame(origin, u_ang):
    ux, uy = math.cos(u_ang), math.sin(u_ang)
    nx, ny = -uy, ux
    return lambda t, s: (origin[0] + ux * t + nx * s, origin[1] + uy * t + ny * s)


def ang(a, b):
    return math.atan2(b[1] - a[1], b[0] - a[0])


def mx(pts, cx=CX):
    """Mirror points across ``x = cx``."""
    return [(2 * cx - p[0], p[1]) + tuple(p[2:]) for p in pts]


def sym(half):
    """A closed outline symmetric about ``x = CX`` from its right half, which
    runs from the top centre point to the bottom centre point."""
    return half + mx(list(reversed(half[1:-1])))


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


# ============================================================================================
# SHARED PIECES: hands, sleeves, cuffs, props
# ============================================================================================

def skin_keys(near):
    return (O["skin"], O["skin_sh"], O["skin_lt"]) if near else (O["skin_sh"], O["skin_dk"], None)


def fist(w, a, near=True, thumb=1, knuckles=True):
    """A closed fist at the wrist ``w``, the knuckles along ``a`` (radians);
    ``thumb`` (+1 / -1) is the side its thumb wraps on, 0 hides it."""
    q = frame(w, a)
    sk, sh, lt = skin_keys(near)
    d = smooth([q(-2, -7.6), q(6, -9.2), q(13, -9), q(17.6, -5.6), q(18.6, 0), q(17.6, 5.6), q(13, 9), q(6, 9.2), q(-2, 7.6)])
    items = [line([q(13.4, s0), q(18.2, s0 * 0.9)], O["skin_dk"] if not near else sh, 1.0) for s0 in (-3.4, 0.4, 4.0)] if knuckles else []
    out = cel(d, sk, sh, lt, items, s=2.5)
    if thumb:
        t = thumb
        out += cel(smooth([q(3, -6 * t), q(9, -9.6 * t), q(14.6, -7.4 * t), q(14.2, -3.6 * t), q(8, -3.4 * t)]), sk, sh, lt, [], s=1.5, sw=2.2)
    return out


def point_hand(w, a, near=True, thumb=-1):
    """A fist with the index finger out along ``a``: the way, pointed."""
    q = frame(w, a)
    sk, sh, lt = skin_keys(near)
    out = cel(smooth([q(-2, -7.4), q(6, -8.6), q(13, -7.6), q(16.4, -3), q(16.2, 4), q(13, 8.6), q(6, 9), q(-2, 7.4)]), sk, sh, lt,
              [line([q(12.6, 1.4), q(16.0, 1.6)], sh, 1.0), line([q(12, 4.8), q(15, 5.4)], sh, 1.0)], s=2.5)
    out += cel(capsule(q(11, -5.0 * thumb), q(29, -6.2 * thumb), 3.4, 2.8), sk, sh, lt, [line([q(21, -8.4 * thumb), q(21, -3.8 * thumb)], sh, 0.8)],
               s=1.4, sw=2.2)
    out += cel(smooth([q(3, -6 * thumb), q(9, -9.8 * thumb), q(13.6, -9.6 * thumb), q(13, -6 * thumb), q(7, -4 * thumb)]), sk, sh, lt, [], s=1.4, sw=2.2)
    return out


def sleeve(s, e, w, near=True, key="deel", ru=12.5, rf=11.0, upper=True, lower=True):
    """The deel's loose sleeve: the upper arm, then the forearm over it."""
    out = []
    fn = (lambda d, items, sh: C(d, key, items, s=sh)) if near else (lambda d, items, sh: far(d, key, items))
    if upper:
        q = frame(s, ang(s, e))
        out += fn(capsule(s, e, ru, ru - 0.6), [line([q(10, ru * 0.35), q(30, ru * 0.25)], O[key + "_sh"], 1.1)], 4)
    if lower:
        q = frame(e, ang(e, w))
        out += fn(capsule(e, w, rf + 0.6, rf), [line([q(6, -rf * 0.2), q(22, -rf * 0.35)], O[key + "_sh"], 1.1)], 4)
    return out


def cuff(e, w, near=True, r=11.0):
    """The horse-hoof cuff: the sleeve's end flared over the back of the hand,
    faced with the trim."""
    q = frame(w, ang(e, w))
    d = smooth([q(-7, -r - 0.6), q(0, -r - 2.6), q(3.6, -r - 1.2) + (True,), q(5.2, -2), q(3.6, r + 1.2) + (True,), q(0, r + 2.6), q(-7, r + 0.6)])
    return C(d, "trim", [line([q(-3.4, -r), q(-3.4, r)], O["trim_sh"], 1.0)], s=2.5) if near else far(d, "trim")


def sabre(c, a, length=92.0, sheathed=False):
    """A curved steppe sabre whose grip is centred at ``c``, the blade along
    ``a`` and curving back; ``sheathed`` draws it in its scabbard."""
    q = frame(c, a)
    out = []
    if sheathed:
        d = smooth([q(9, -4.6), q(40, -5.8), q(length * 0.75, -3.6), q(length, 2.6), q(length + 2, 6.2) + (True,), q(length * 0.75, 3.8), q(40, 4.0),
                    q(9, 4.6)])
        out += cel(d, O["wood"], O["wood_sh"], O["wood_lt"], [line([q(30, -5.2), q(30, 4.4)], O["gold"], 2.6),
                                                              line([q(length * 0.7, -3.4), q(length * 0.7, 3.4)], O["gold"], 2.6)], s=2.5)
    else:
        blade = smooth([q(8, -3.2), q(length * 0.5, -4.4), q(length * 0.85, -1.6), q(length + 2, 4.4) + (True,), q(length * 0.82, 4.4), q(length * 0.5, 2.4),
                        q(8, 2.8)])
        out += cel(blade, O["metal"], O["metal_sh"], O["metal_lt"], [line([q(14, -0.6), q(length * 0.6, -1.2), q(length * 0.84, 1.2)], O["metal_lt"], 1.3)],
                   s=2.0)
    out += cel(smooth([q(5.6, -9), q(8.6, -9.4), q(9.6, 0), q(8.6, 9.4), q(5.6, 9), q(6.6, 0)]), O["gold"], O["gold_sh"], O["gold_lt"], [], s=1.5)
    out += cel(capsule(q(-14, 0), q(5, 0), 3.6, 3.4), O["wood"], O["wood_sh"], O["wood_lt"], [], s=1.2)
    out += cel(smooth([q(-19.5, 0), q(-16, -4.4), q(-12.6, 0), q(-16, 4.4)]), O["gold"], O["gold_sh"], O["gold_lt"], [], s=1.2)
    return out


def map_sheet(quad, roll_r=4.6):
    """An unrolled campaign map between two rolls: ``quad`` is its corners
    (left-top, right-top, right-bottom, left-bottom).  On it a route that
    doubles back on itself, a river, three mountains and a ring of
    question."""
    lt, rt, rb, lb = quad

    def at(u, v):
        return lerp(lerp(lt, rt, u), lerp(lb, rb, u), v)

    items = [line([at(0.12, 0.78), at(0.3, 0.55), at(0.5, 0.7), at(0.42, 0.36), at(0.7, 0.3), at(0.62, 0.62), at(0.84, 0.5)], O["route"], 1.3),
             line([at(0.18, 0.12), at(0.3, 0.3), at(0.24, 0.5), at(0.34, 0.92)], O["river"], 1.4)]
    for u, v in ((0.62, 0.16), (0.74, 0.2), (0.86, 0.78)):
        items.append(path(smooth([at(u - 0.06, v + 0.08, ) + (True,), at(u, v - 0.06) + (True,), at(u + 0.06, v + 0.08) + (True,)], closed=False),
                          "none", O["parch_sh"], 1.3))
    cx, cy = at(0.84, 0.5)
    items.append(line([(cx - 2.6, cy - 2.6), (cx + 2.6, cy + 2.6)], O["route"], 1.4))
    items.append(line([(cx - 2.6, cy + 2.6), (cx + 2.6, cy - 2.6)], O["route"], 1.4))
    out = cel(smooth([lt + (True,), rt + (True,), rb + (True,), lb + (True,)]), O["parch"], O["parch_sh"], O["parch_lt"], items, s=3)
    for a, b in ((lt, lb), (rt, rb)):
        out += cel(capsule((a[0], a[1] - 3), (b[0], b[1] + 3), roll_r, roll_r), O["parch"], O["parch_sh"], O["parch_lt"],
                   [line([(a[0] - 1, a[1] + 2), (b[0] - 1, b[1] - 2)], O["parch_sh"], 1.0)], s=2)
        for p in (a, b):
            out.append(ellipse(p[0], p[1] + (-4 if p in (lt, rt) else 4), 2.0, 1.6, O["wood"], INK, 1.0))
    return out


def scallop(run, n, amp, out_sign=1.0):
    """Points along the open polyline ``run`` with ``n`` soft bumps standing off
    it by ``amp`` (fur): every bump's crest and the dips between them."""
    segs = list(zip(run[:-1], run[1:]))
    lens = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in segs]
    total = sum(lens)

    def at(u):
        d = u * total
        for (a, b), L in zip(segs, lens):
            if d <= L:
                t = d / L if L else 0.0
                return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t), ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
            d -= L
        a, b = segs[-1]
        return b, ((b[0] - a[0]) / lens[-1], (b[1] - a[1]) / lens[-1])

    pts = []
    for k in range(n):
        for u, h in ((k / n, 0.0), ((k + 0.5) / n, amp)):
            (px, py), (tx, ty) = at(u)
            nx, ny = ty * out_sign, -tx * out_sign
            pts.append((px + nx * h, py + ny * h) + ((True,) if h == 0.0 else ()))
    (px, py), _ = at(1.0)
    pts.append((px, py, True))
    return pts


def fur_ticks(x0, y0, x1, y1, step=9.0):
    """Short curved strands of fur, shade and light, staggered over a box."""
    out = []
    j = 0
    y = y0
    while y < y1:
        x = x0 + (step / 2 if j % 2 else 0)
        while x < x1:
            k = int(x * 7 + y * 3) % 3
            col = O["fur_lt"] if k == 0 else O["fur_sh"]
            out.append(line([(x - 1.6, y + 3), (x, y), (x + 1.2, y - 3)], col, 1.1))
            x += step
        y += step * 0.8
        j += 1
    return out


def quiver(top, a, length=78.0):
    """An open quiver hung at the hip, the arrows' fletchings standing out of
    its mouth."""
    q = frame(top, a)
    out = []
    for s0, h, tilt in ((-4.6, 16, -2.0), (-1.0, 19, 0.0), (2.8, 17, 2.4), (5.6, 14, 4.0)):
        b = q(2, s0)
        tip = q(-h, s0 + tilt)
        out += [line([b, tip], O["wood_sh"], 1.6)]
        f = smooth([q(-h * 0.45, s0 + tilt * 0.45 - 2.2), q(-h - 1.5, s0 + tilt - 1.6) + (True,), q(-h - 1.5, s0 + tilt + 1.6) + (True,),
                    q(-h * 0.45, s0 + tilt * 0.45 + 2.2)])
        out += cel(f, WHITE, "#c9c2b4", None, [], s=1, sw=1.6)
    d = smooth([q(-2, -9) + (True,), q(-2, 9) + (True,), q(length * 0.7, 7.4), q(length, 5) + (True,), q(length, -5) + (True,), q(length * 0.7, -7.4)])
    items = [line([q(6, -9), q(6, 9)], O["trim"], 2.4), line([q(length * 0.62, -8), q(length * 0.62, 8)], O["trim"], 2.0),
             line([q(14, 2), q(length - 6, 1)], O["case_sh"], 1.1)]
    out += C(d, "case", items, s=3)
    return out


def lamellae(x0, y0, x1, y1, row=12.0, col=7.5, key="lam"):
    """Rows of laced lamellar plates filling a box (clipped by the caller's shape)."""
    out = []
    j = 0
    y = y0
    while y < y1:
        out.append(path(smooth([(x0, y, True), (x1, y, True), (x1, y + row - 1.2, True), (x0, y + row - 1.2, True)]), O[key + "_lt"] if j % 2 else O[key]))
        off = 0 if j % 2 else col / 2
        x = x0 + off
        while x < x1:
            out.append(line([(x, y + 0.8), (x, y + row - 1.6)], O[key + "_sh"], 0.9))
            x += col
        out.append(line([(x0, y + row - 0.6), (x1, y + row - 0.6)], O["lace"], 1.6))
        y += row
        j += 1
    return out


# ============================================================================================
# SIDE VIEW (facing right; his right side toward the camera)
# ============================================================================================

S_WAIST = (272.0, 352.0)
S_NECK = (276.0, 252.0)
S_SH_NEAR = (272.0, 274.0)
S_SH_FAR = (262.0, 272.0)

#: (near elbow, near wrist, far elbow, far wrist) per pose, in the torso's frame.
S_POSES = {
    "akimbo": ((246, 314), (270, 346), (240, 312), (262, 344)),
    "map": ((282, 322), (300, 318), (270, 318), (332, 316)),
    "sabre": ((300, 252), (318, 224), (258, 318), (266, 354)),
    "clasp": ((272, 322), (296, 334), (264, 320), (300, 330)),
    "point": ((304, 270), (336, 264), (244, 314), (266, 342)),
    "chin": ((286, 324), None, (266, 320), (288, 330)),
}


def s_chin():
    """Where his chin is, in the torso's frame (the head's pitch applied)."""
    return _rot(299.0, 251.0, S_NECK[0], S_NECK[1], O["pitch"])


def s_arm_points(side):
    ne, nw, fe, fw = S_POSES[O["pose"]]
    if side == "near":
        if nw is None:  # the chin: the fist's knuckles just under it
            cx, cy = s_chin()
            nw = (cx - 4.0, cy + 17.0)
        return S_SH_NEAR, ne, nw
    return S_SH_FAR, fe, fw


def s_hand(side, w, a, near):
    pose = O["pose"]
    if pose == "point" and near:
        return point_hand(w, a, near)
    if pose == "chin" and near:
        return fist(w, a, near, thumb=1)
    if pose == "map":
        return fist(w, a, near, thumb=0)
    return fist(w, a, near, thumb=1 if near else 0)


def s_far_arm():
    s, e, w = s_arm_points("far")
    out = sleeve(s, e, w, near=False)
    a = ang(e, w)
    out += s_hand("far", w, a, False)
    out += cuff(e, w, near=False)
    return out


def s_near_arm():
    s, e, w = s_arm_points("near")
    a = ang(e, w)
    pose = O["pose"]
    out = []
    if pose == "sabre":
        out += sabre(frame(w, a)(9, 0), math.radians(-62), length=96)
    out += sleeve(s, e, w, near=True)
    if O.get("armor"):
        out += pauldron(s, e)
    out += s_hand("near", w, a, True)
    out += cuff(e, w)
    if pose == "map":
        out += map_sheet([(304, 292), (338, 300), (336, 338), (302, 334)])
        q = frame(w, a)
        out += cel(capsule(q(8, -7), (305, 314), 3.2, 2.8), O["skin"], O["skin_sh"], O["skin_lt"], [], s=1.4, sw=2.2)
    if pose == "clasp":
        # his far hand's fingers laced over the near fist
        q = frame(w, a)
        for k, s0 in enumerate((-4.0, 0.0, 4.0)):
            out += cel(capsule(q(4 + k, s0 - 1), q(13 + k, s0 + 1.6), 2.6, 2.4), O["skin_sh"], O["skin_dk"], None, [], s=1, sw=1.8)
    return out


def pauldron(s, e):
    """A lamellar shoulder guard riding the upper arm."""
    q = frame(s, ang(s, e))
    d = smooth([q(-8, -12), q(-6, 0), q(-8, 12), q(10, 16), q(26, 15) + (True,), q(26, -15) + (True,), q(10, -16)])
    rows = []
    for t in range(-4, 26, 8):
        rows.append(line([q(t, -17), q(t, 17)], O["lace"], 1.6))
        for sv in range(-15, 16, 5):
            rows.append(line([q(t + 1, sv), q(t + 6.5, sv)], O["lam_sh"], 0.9))
    return C(d, "lam", rows, s=3)


def s_boot(near):
    """A gutal: a tall felt-lined boot, its toe turned up, a thick sole."""
    ax = 284.0 if near else 262.0
    shaft = smooth([(ax - 12, 424), (ax + 10, 424), (ax + 11, 470), (ax + 14, 482), (ax - 13, 486, True), (ax - 13, 456)])
    foot = smooth([(ax - 14, 478), (ax + 8, 476), (ax + 22, 484), (ax + 30, 478), (ax + 33, 471, True), (ax + 31, 484), (ax + 26, 494), (ax + 18, 496),
                   (ax - 14, 496, True)])
    sole = smooth([(ax - 15, 494, True), (ax + 20, 494), (ax + 28, 492), (ax + 26, 502, True), (ax - 15, 502, True)])
    if near:
        out = C(shaft, "boot", [line([(ax - 11, 432), (ax + 10, 432)], O["trim"], 2.4), line([(ax - 4, 444), (ax + 2, 462), (ax - 2, 474)], O["boot_lt"], 1.1)],
                s=4)
        out += C(foot, "boot", [line([(ax - 6, 486), (ax + 8, 482), (ax + 20, 487), (ax + 28, 480)], O["trim"], 1.6)], s=3)
        return out + C(sole, "sole", [], s=1.5)
    out = far(shaft, "boot") + far(foot, "boot")
    return out + far(sole, "sole")


def s_skirt():
    """The deel below the sash: a full wrap to mid-calf, the front panel's edge
    running down his right side with its trim, a slit at the hem."""
    if O.get("armor"):
        back, front = (232, 352), (312, 352)
    else:
        back, front = (234, 352), (310, 352)
    d = smooth([back, front, (315, 400), (321, 440, True), (225, 442, True), (227, 400)])
    items = [line([(256, 372), (250, 438)], O["deel_sh"], 1.3), line([(296, 372), (302, 436)], O["deel_sh"], 1.1)]
    out = C(d, "deel", items, s=6)
    edge = smooth([(268, 356), (275, 356), (277, 424), (280, 441, True), (271, 441, True), (270, 424)])
    out += C(edge, "trim", [], s=1.5)
    out += [path(smooth([(272, 424), (277, 424), (279, 440, True), (270, 440, True)]), O["deel_sh"], INK, 1.2)]
    hem = smooth([(225, 434, True), (321, 432, True), (322, 442, True), (225, 444, True)])
    return out + C(hem, "trim", [], s=1.5)


def s_tassets():
    d = smooth([(230, 350), (314, 350), (319, 384), (323, 414, True), (225, 416, True), (227, 384)])
    return C(d, "lam", lamellae(214, 352, 334, 418), s=4)


def s_torso():
    """The deel from the collar to the sash, crossed over to his right: the
    trimmed closure runs from the throat back to the armpit, then straight
    down his side; three knot buttons ride it."""
    d = smooth([(260, 256), (284, 254), (298, 262), (307, 282), (311, 312), (311, 352, True), (234, 354, True), (233, 316), (237, 286), (247, 266)])
    items = [line([(248, 300), (244, 340)], O["deel_sh"], 1.2)]
    out = C(d, "deel", items, s=6)
    band = smooth([(297, 260), (292, 274), (283, 286), (276, 292), (275, 340, True), (268, 340, True), (267, 318), (270, 284), (280, 278), (287, 270),
                   (291, 260)])
    out += C(band, "trim", [], s=1.5)
    for p in ((293, 268), (284, 280), (272, 304), (272, 326)):
        out += [ellipse(p[0], p[1], 2.2, 2.2, O["gold"], INK, 1.0)]
    return out


def s_cuirass():
    d = smooth([(264, 262), (292, 262), (306, 280), (313, 310), (313, 354, True), (232, 356, True), (231, 316), (236, 288), (248, 270)])
    items = lamellae(226, 262, 320, 360)
    return C(d, "lam", items, s=5)


def s_sash():
    d = smooth([(232, 336, True), (313, 334, True), (315, 358, True), (232, 360, True)])
    items = [line([(234, 344), (313, 342)], O["sash_sh"], 1.2), line([(234, 351), (314, 350)], O["sash_lt"], 1.1)]
    out = C(d, "sash", items, s=3)
    tail = smooth([(238, 352), (248, 354), (250, 388), (246, 394, True), (238, 390, True), (236, 370)])
    out += C(tail, "sash", [line([(243, 360), (243, 388)], O["sash_sh"], 1.0)], s=2.5)
    if O["look"] == "steppe":
        out += quiver((262, 338), math.radians(96))
    if O.get("sheathed"):
        out += sabre((300, 352), math.radians(132), length=96, sheathed=True)
    return out


def s_neck():
    out = C(smooth([(262, 236), (290, 238), (294, 258), (262, 260)]), "skin", [], s=4)
    collar = smooth([(258, 254), (282, 252), (296, 256), (298, 264, True), (284, 262), (260, 266, True)])
    return out + C(collar, "trim", [], s=2)


def s_face_points():
    """A Genghis profile, facing right: a sloping brow, a straight nose with a
    rounded tip, the long upper lip under the moustache, a modest chin under
    the tuft, a broad jaw to the ear."""
    return [(258, 172), (278, 168), (291, 174), (297, 186), (299, 196), (297.4, 202), (300.6, 208), (305.4, 215.6), (309.2, 221.4), (308.6, 224.4),
            (304.6, 226.2), (302.2, 227.2), (302.8, 231.2), (301.6, 234.6, True), (302.2, 237.4), (300.6, 241.4), (301.4, 245.4), (298.6, 250.4),
            (289, 252.6), (277, 249.6), (266, 242), (258, 231), (251.6, 217), (249.6, 201), (251.4, 185)]


def s_ear_and_loop(show_ear=True, show_loop=True):
    out = []
    dk = O["skin_dk"]
    if show_loop:  # the hair braided and looped behind the ear
        loop = smooth([(252, 214), (260, 216), (262, 232), (259, 246), (253, 248), (249, 240), (250, 226)])
        hole = smooth([(254.6, 230), (257.6, 230), (258, 240), (254.6, 241)])
        out += cel(loop, O["hair"], O["hair_sh"], O["hair_lt"], [line([(252, 222), (259, 224)], O["hair_sh"], 1.0), line([(251, 236), (258, 238)],
                                                                                                                 O["hair_sh"], 1.0)], s=2)
        out += [path(hole, O["hair_sh"], INK, 1.2)]
    if show_ear:
        out += C(smooth([(259.4, 204), (266.4, 202.6), (269, 212), (266.6, 222.4), (260.4, 221.6)]), "skin",
                 [line([(263.2, 207), (266.2, 212), (263.4, 217.4)], dk, 1.0)], s=3)
    return out


def eye_profile(ex, ey):
    """A small eye under a heavy lid, facing right."""
    out = [path(smooth([(ex - 3.6, ey + 0.6), (ex + 0.4, ey - 1.6), (ex + 4.0, ey - 0.6), (ex + 3.4, ey + 1.8), (ex - 0.6, ey + 2.2)]), WHITE),
           ellipse(ex + 2.2, ey + 0.2, 1.5, 1.9, O["eye"])]
    worried = O["brow"] == "worried"
    lid_top = -1.8 if worried else -0.8
    out += [path(smooth([(ex - 4.6, ey + 0.2), (ex + 0.4, ey + lid_top - 2.4), (ex + 5.0, ey - 1.8), (ex + 4.4, ey - 0.2), (ex + 0.4, ey + lid_top)]),
                 O["skin"]),
            line([(ex - 4.6, ey + 0.6), (ex + 0.4, ey + lid_top), (ex + 4.8, ey - 0.4)], INK, 1.8),
            line([(ex - 2.4, ey + 2.6), (ex + 3.0, ey + 2.2)], O["skin_dk"], 0.8)]
    return out


#: Where the side view's eye is, in the head's frame.
S_EYE = (290.0, 207.0)


def s_face():
    """The features: eye, brow, cheekbone, nose wing, mouth."""
    return s_face_lines() + eye_profile(*S_EYE) + s_brow() + s_mouth()


def s_face_lines():
    """The cheekbone and the nose wing."""
    sk, dk = O["skin_sh"], O["skin_dk"]
    return [line([(276, 214), (279, 221), (284, 225)], sk, 1.3),
            line([(300.4, 216.4), (299.0, 219.6), (301.0, 222.6), (304.4, 222.8)], dk, 1.1)]


def s_brow():
    """Can's brow level and low; Can't's lifted in the middle, with the
    creases of a worried forehead."""
    sk, dk = O["skin_sh"], O["skin_dk"]
    out = []
    hair = O["hair"]
    if O["brow"] == "stern":
        brow = smooth([(280.4, 198.2), (289, 197.4), (297.4, 199.6, True), (296.6, 202.2), (289, 200.6), (280.6, 201.2)])
        out += [path(brow, hair, INK, 1.0), line([(296.6, 203.6), (295.4, 199.4)], dk, 0.9)]
    else:
        brow = smooth([(281, 199.2), (289, 196.2), (295.6, 193.0, True), (296.2, 195.8), (289.4, 198.8), (281.4, 201.6)])
        out += [path(brow, hair, INK, 1.0), line([(284, 189.4), (292, 187.6)], sk, 1.0), line([(286, 185.4), (293, 184.4)], sk, 0.9)]
    return out


def s_mouth():
    """The mouth, closed, set back under the moustache."""
    dk = O["skin_dk"]
    out = []
    if O["mouth"] == "firm":
        out += [line([(294.8, 234.6), (298.2, 234.4), (301.4, 234.6)], INK, 1.6), line([(294.6, 233.0), (295.4, 236.2)], dk, 0.9)]
    else:
        out += [line([(295.0, 236.4), (298.2, 234.8), (301.4, 234.8)], INK, 1.5), line([(295.6, 237.0), (294.6, 240.4)], dk, 0.9)]
    return out


def s_beard():
    """The moustache from under the nose and the chin tuft: Can's swept and
    pointed, Can't's limp and long."""
    out = []
    hk = ("hair", "hair_sh", "hair_lt")
    if O["beard"] == "spear":
        tuft = smooth([(294, 244), (301.6, 243.4), (306, 252), (309.6, 264, True), (300, 258), (293, 250)])
    else:
        tuft = smooth([(294, 245), (301, 244.6), (302.4, 256), (300.6, 272, True), (296.6, 262), (293.4, 252)])
    out += cel(tuft, O[hk[0]], O[hk[1]], O[hk[2]], [line([(298, 248), (302, 258)], O["hair_lt"], 0.9)], s=2)
    if O["stache"] == "sweep":
        st = smooth([(296, 228.6), (303.4, 227.4), (307.2, 229.6), (304.6, 232.0), (299.6, 233.0), (295.4, 238.6), (293.0, 246.6), (289.6, 251.0, True),
                     (290.8, 243.0), (293.2, 234.4)])
    else:
        st = smooth([(296, 228.6), (303.2, 227.6), (305.4, 230.0), (302.2, 232.4), (299.2, 236.8), (298.6, 248.0), (299.0, 262.0, True), (294.8, 254.0),
                     (294.2, 240.0), (294.0, 232.4)])
    out += cel(st, O[hk[0]], O[hk[1]], O[hk[2]], [], s=1.6, sw=2.2)
    return out


def s_head():
    hat = O["hat"]
    out = []
    show_ear = hat == "cap" or (hat == "fur" and O["flaps"] == "up")
    show_loop = hat != "helmet"
    out += C(smooth(s_face_points()), "skin", [path(smooth([(252, 214), (262, 232), (276, 244), (290, 250), (300, 249), (290, 253), (272, 249), (258, 236)]),
                                                     O["skin_sh"])], s=6)
    # the hair at the nape below the hat
    nape = [(250.6, 194), (258, 194), (259.6, 206), (256.6, 220), (252, 226)]
    out += cel(smooth(nape + [(249.6, 216), (249.4, 202)]), O["hair"], O["hair_sh"], O["hair_lt"], [], s=2, edges=[nape])
    out += s_ear_and_loop(show_ear, show_loop)
    out += s_face()
    out += s_beard()
    return out


def s_hat_back():
    """What hangs behind the head: the cap's ribbons, the drooping plume."""
    hat = O["hat"]
    out = []
    if hat == "cap":
        if O["who"] == "can":  # flying back, stiff as banners
            for k, (dy, tip) in enumerate(((0, (206, 214)), (6, (212, 238)))):
                d = smooth([(250, 196 + dy), (232, 198 + dy + k * 6), tip + (True,), (226, 206 + dy + k * 8), (248, 204 + dy)])
                out += C(d, "ribbon", [], s=2)
        else:  # hanging limp down his back
            for k, x0 in enumerate((246, 252)):
                d = smooth([(x0 - 4, 198), (x0 + 3, 198), (x0 + 2 - k * 3, 262), (x0 - 1 - k * 3, 270, True), (x0 - 5 - k * 3, 262)])
                out += C(d, "ribbon", [], s=2)
    if hat == "helmet":
        # the aventail: a quilted curtain from the brim round the back and sides
        d = smooth([(286, 198), (284, 222), (281, 244, True), (262, 248), (240, 256, True), (236, 228), (238, 198)])
        items = [line([(283, 220), (240, 226)], O["avent_sh"], 1.2), line([(281, 236), (238, 244)], O["avent_sh"], 1.2)]
        items += [line([(x, 200), (x - 2, 250)], O["avent_sh"], 1.0) for x in (250, 262, 274)]
        out += C(d, "avent", items, s=4)
        if O["plume"] == "down":
            d = smooth([(270, 126), (276, 116), (266, 112), (248, 118), (234, 134), (226, 158), (224, 186), (220, 204, True), (230, 196), (234, 204, True),
                        (238, 180), (242, 156), (252, 136)])
            items = [line([(266, 116), (246, 124), (234, 144), (228, 176)], O["plumec_sh"], 1.1), line([(262, 124), (246, 136), (238, 160), (234, 190)],
                                                                                                      O["plumec_sh"], 1.0)]
            out += C(d, "plumec", items, s=3)
    if hat == "fur" and O["flaps"] == "down":
        d = smooth([(258, 194), (262, 210), (258, 238), (250, 250, True), (240, 244), (238, 214), (242, 194)])
        out += C(d, "fur", [line([(246, 210), (244, 236)], O["fur_sh"], 1.1), line([(252, 214), (250, 240)], O["fur_sh"], 1.1)], s=3)
    return out


def s_hat():
    hat = O["hat"]
    out = []
    if hat == "cap":
        dome = smooth([(299, 190), (297, 175), (288, 163), (272, 157), (256, 159), (245, 169), (241, 184), (243, 196)])
        out += C(dome, "hatc", [line([(272, 159), (276, 186)], O["hatc_sh"], 1.1), line([(286, 166), (292, 186)], O["hatc_lt"], 1.6)], s=5)
        out += [ellipse(272, 155, 4.4, 3.6, O["ribbon"], INK, 1.2)]
        top = scallop([(240, 186), (262, 184), (284, 182), (304, 186)], 7, 2.4)
        bot = [(306, 196, True), (286, 198), (262, 202), (240, 206, True)]
        brim = smooth(top + bot)
        out += C(brim, "fur", [line([(250, 196), (262, 194)], O["fur_sh"], 1.0), line([(276, 192), (290, 190)], O["fur_sh"], 1.0)], s=3)
    elif hat == "helmet":
        bowl = smooth([(300, 194), (298, 172), (288, 152), (274, 136, True), (260, 150), (248, 168), (242, 194)])
        items = [line([(274, 138), (282, 192)], O["helm_sh"], 1.3), line([(274, 138), (262, 192)], O["helm_sh"], 1.3),
                 line([(276, 146), (290, 186)], O["helm_lt"], 1.8)]
        out += C(bowl, "helm", items, s=5)
        out += C(smooth([(240, 188), (302, 188), (304, 198, True), (240, 200, True)]), "band", [], s=1.5)
        out += [ellipse(x, 194, 1.8, 1.8, O["gold"], INK, 0.9) for x in (252, 266, 280, 294)]
        out += C(smooth([(296, 196), (314, 197), (316, 201, True), (298, 204, True)]), "helm", [], s=1.5)  # the brow peak
        out += C(capsule((274, 136), (274, 118), 2.6, 2.2), "helm", [], s=1)
        out += C(smooth([(268, 120), (280, 120), (277, 113, True), (271, 113, True)]), "helm", [], s=1)
        if O["plume"] == "up":
            d = smooth([(270, 114), (262, 98), (258, 78), (264, 84), (268, 66), (274, 80), (282, 64), (283, 84), (290, 78), (287, 98), (279, 114)])
            items = [line([(274, 110), (274, 80)], O["plumec_sh"], 1.1), line([(270, 108), (264, 88)], O["plumec_sh"], 1.0),
                     line([(278, 108), (284, 88)], O["plumec_lt"], 1.0)]
            out += C(d, "plumec", items, s=3)
    elif hat == "fur":
        crown = smooth([(292, 188), (290, 166), (282, 146), (272, 134, True), (262, 148), (252, 168), (248, 188)])
        out += C(crown, "hatc", [line([(272, 136), (276, 184)], O["hatc_sh"], 1.2), line([(278, 142), (288, 180)], O["hatc_lt"], 1.6)], s=4)
        out += [ellipse(272, 132, 4.6, 4.0, O["knot"], INK, 1.2)]
        if O["flaps"] == "up":
            # the flaps tied up: a deep roll of fox fur flaring up round the crown
            top = scallop([(230, 170), (254, 163), (284, 161), (318, 166)], 6, 4.2)
            band = smooth(top + [(318, 176), (310, 192), (300, 200, True), (272, 202), (246, 202, True), (234, 192), (230, 180)])
            out += C(band, "fur", fur_ticks(236, 172, 314, 198), s=4)
        else:
            band = smooth(scallop([(240, 182), (266, 178), (296, 180), (302, 184)], 6, 2.2) + [(304, 194, True), (282, 198), (256, 200), (240, 200, True)])
            out += C(band, "fur", [line([(250, 192), (264, 190)], O["fur_sh"], 1.0), line([(276, 190), (292, 190)], O["fur_sh"], 1.0)], s=3)
            flap = smooth([(256, 196), (280, 196), (281, 222), (277, 244, True), (264, 246), (256, 232), (254, 212)])
            out += C(flap, "fur", [line([(262, 204), (264, 236)], O["fur_sh"], 1.1), line([(272, 204), (273, 236)], O["fur_sh"], 1.1)], s=3)
    return out


def side_layers():
    """The side view's layers, back to front: (name, painter, rotations)."""
    lean = O["lean"]
    torso = [(S_WAIST[0], S_WAIST[1], lean)]
    head = [(S_NECK[0], S_NECK[1], O["pitch"]), (S_WAIST[0], S_WAIST[1], lean)]
    L = [
        ("hat-back", s_hat_back, head),
        ("far-arm", s_far_arm, torso),
        ("far-boot", lambda: s_boot(False), []),
        ("near-boot", lambda: s_boot(True), []),
        ("skirt", s_skirt, []),
    ]
    if O.get("armor"):
        L.append(("tassets", s_tassets, []))
    L += [("torso", s_torso, torso)]
    if O.get("armor"):
        L.append(("cuirass", s_cuirass, torso))
    L += [
        ("sash", s_sash, torso),
        ("neck", s_neck, torso),
        ("head", s_head, head),
        ("hat", s_hat, head),
        ("near-arm", s_near_arm, torso),
    ]
    return L


# ============================================================================================
# FRONT VIEW (his right on screen-left)
# ============================================================================================

F_NECK = (280.0, 254.0)
F_SH_R, F_SH_L = (230.0, 278.0), (330.0, 278.0)

#: (right elbow, right wrist, left elbow, left wrist) per pose.
F_POSES = {
    "akimbo": ((202, 318), (234, 344), (358, 318), (326, 344)),
    "map": ((222, 326), (240, 320), (338, 326), (320, 320)),
    "sabre": ((210, 236), (206, 198), (358, 318), (326, 344)),
    "clasp": ((228, 326), (266, 336), (332, 326), (296, 336)),
    "point": ((202, 318), (234, 344), (370, 284), (402, 278)),
    "chin": ((244, 330), (268, 274), (330, 330), (250, 336)),
}


def fx(p):
    """A torso point, widened by the brother's breadth."""
    return (CX + (p[0] - CX) * O["broad"], p[1]) + tuple(p[2:])


def f_shoulders():
    dy = O["f_shrug"]
    return (fx(F_SH_R)[0], F_SH_R[1] + dy), (fx(F_SH_L)[0], F_SH_L[1] + dy)


def f_boots():
    out = []
    for sg in (-1, 1):
        x = CX + sg * 16
        shaft = smooth([(x - 12, 430), (x + 12, 430), (x + 12, 484), (x - 12, 484)])
        out += C(shaft, "boot", [line([(x - 11, 438), (x + 11, 438)], O["trim"], 2.4)], s=4)
        foot = smooth([(x - 14, 480), (x - 4, 476), (x, 466, True), (x + 4, 476), (x + 14, 480), (x + 15, 494), (x - 15, 494)])
        out += C(foot, "boot", [line([(x - 8, 486), (x, 480), (x + 8, 486)], O["trim"], 1.4)], s=3)
        out += C(smooth([(x - 16, 492, True), (x + 16, 492, True), (x + 15, 502, True), (x - 15, 502, True)]), "sole", [], s=1.5)
    return out


def f_skirt():
    half = [(CX, 352), fx((322, 352)), fx((330, 400)), fx((338, 442, True)), (CX, 444)]
    d = smooth(sym(half))
    items = [line([fx((300, 372)), fx((306, 438))], O["deel_sh"], 1.2), line([fx((262, 372)), fx((256, 438))], O["deel_sh"], 1.2)]
    out = C(d, "deel", items, s=6)
    # the front panel's edge, down his right side
    e0, e1 = fx((246, 356)), fx((240, 440))
    out += C(smooth([e0, (e0[0] + 7, e0[1]), (e1[0] + 7, e1[1], True), (e1[0], e1[1], True)]), "trim", [], s=1.5)
    hem = smooth([fx((221, 434, True)), fx((339, 434, True)), fx((340, 443, True)), fx((220, 445, True))])
    return out + C(hem, "trim", [], s=1.5)


def f_tassets():
    out = []
    for sg in (-1, 1):
        x0, x1 = (CX + sg * 2, CX + sg * 50) if sg > 0 else (CX + sg * 50, CX + sg * 2)
        d = smooth([fx((x0, 350, True)), fx((x1, 350, True)), fx((x1 + sg * 4 if sg > 0 else x1 - 4, 414, True)), fx((x0, 416, True))])
        out += C(d, "lam", lamellae(fx((x0 - 10, 0))[0], 352, fx((x1 + 10, 0))[0], 420), s=4)
    return out


def f_torso_shape():
    _r, (lx, ly) = f_shoulders()
    half = [(CX, 254), (296, 256), (lx - 6, ly - 8), (lx + 4, ly + 6), fx((326, 318)), fx((322, 354, True)), (CX, 356)]
    return smooth(sym(half))


def f_torso():
    d = f_torso_shape()
    out = C(d, "deel", [line([fx((304, 300)), fx((308, 344))], O["deel_sh"], 1.2)], s=6)
    # the closure: from the throat across to his right armpit, then down his right side
    a0, a1, a2 = (282, 262), fx((252, 286)), fx((244, 300))
    band = smooth([(286, 260), fx((262, 280)), fx((250, 296)), fx((248, 340, True)), fx((240, 340, True)), fx((241, 292)), fx((256, 276)), (276, 262)])
    out += C(band, "trim", [], s=1.5)
    for p in (lerp(a0, a1, 0.35), lerp(a0, a1, 0.8), (a2[0] + 0.5, 312), (a2[0] + 0.5, 330)):
        out += [ellipse(p[0], p[1], 2.2, 2.2, O["gold"], INK, 1.0)]
    return out


def f_cuirass():
    _r, (lx, ly) = f_shoulders()
    half = [(CX, 262), (300, 262), (lx - 12, ly - 2), (lx - 4, ly + 14), fx((326, 320)), fx((322, 354, True)), (CX, 356)]
    d = smooth(sym(half))
    return C(d, "lam", lamellae(fx((214, 0))[0], 262, fx((346, 0))[0], 360), s=5)


def f_sash():
    d = smooth([fx((236, 334, True)), fx((324, 334, True)), fx((325, 358, True)), fx((235, 360, True))])
    items = [line([fx((238, 342)), fx((322, 342))], O["sash_sh"], 1.2), line([fx((238, 350)), fx((322, 350))], O["sash_lt"], 1.1)]
    out = C(d, "sash", items, s=3)
    # the knot and its tails at his left hip
    kx = fx((306, 0))[0]
    out += C(smooth([(kx - 7, 338), (kx + 7, 338), (kx + 8, 356), (kx - 8, 356)]), "sash", [], s=2)
    for dx, tip in ((-4, 388), (5, 380)):
        out += C(smooth([(kx + dx - 4, 354), (kx + dx + 4, 354), (kx + dx + 5, tip, True), (kx + dx - 3, tip + 4, True)]), "sash", [], s=2)
    if O["look"] == "steppe":
        out += quiver((fx((330, 0))[0] + 6, 336), math.radians(84))
    if O.get("sheathed"):
        x = fx((244, 0))[0]
        out += sabre((x, 344), math.radians(100), length=92, sheathed=True)
    return out


def f_neck():
    out = C(smooth([(266, 236), (294, 236), (296, 262), (264, 262)]), "skin", [], s=4)
    collar = smooth([(262, 252), (280, 256), (298, 252), (302, 262, True), (280, 266), (258, 262, True)])
    return out + C(collar, "trim", [], s=2)


def f_face_shape():
    half = [(CX, 168), (296, 170), (306, 180), (309, 196), (310, 212), (307, 228), (300, 240), (290, 249), (CX, 252)]
    return smooth(sym(half))


def eye_front(cx, cy, sg):
    """A small frontal eye; ``sg`` +1 for the screen-right eye."""
    worried = O["brow"] == "worried"
    out = [path(smooth([(cx - 4.6, cy + 0.6), (cx, cy - 1.8), (cx + 4.6, cy + 0.4), (cx, cy + 2.4)]), WHITE),
           ellipse(cx + sg * 0.4, cy + 0.3, 1.8, 1.9, O["eye"])]
    top = -2.6 if worried else -1.2
    out += [path(smooth([(cx - 5.6, cy + 0.2), (cx, cy + top - 3.0), (cx + 5.6, cy + 0.2), (cx, cy + top)]), O["skin"]),
            line([(cx - 5.4, cy + 0.6), (cx - 1.2 * sg, cy + top), (cx + 5.4, cy + 0.6)], INK, 1.8),
            line([(cx - 3.4, cy + 3.2), (cx + 3.4, cy + 3.2)], O["skin_dk"], 0.8)]
    return out


def f_head():
    sk, dk = O["skin_sh"], O["skin_dk"]
    hat = O["hat"]
    out = []
    show_ear = hat == "cap" or (hat == "fur" and O["flaps"] == "up")
    if show_ear:
        for sg in (-1, 1):
            ex = CX + sg * 29.5
            ear = smooth([(ex - sg * 1, 204), (ex + sg * 4.5, 202), (ex + sg * 6.5, 212), (ex + sg * 4.5, 224), (ex - sg * 0.5, 224)])
            out += C(ear, "skin", [line([(ex + sg * 2, 207), (ex + sg * 4.2, 213), (ex + sg * 2.4, 219)], dk, 1.0)], s=2)
    if hat != "helmet":  # the hair loops below the ears
        for sg in (-1, 1):
            x = CX + sg * 30
            x = CX + sg * 29
            loop = smooth([(x - sg * 2, 196), (x + sg * 4, 196), (x + sg * 6, 222), (x + sg * 5, 244), (x + sg * 1, 252, True), (x - sg * 4, 244),
                           (x - sg * 4, 222)])
            items = [line([(x - 3, y), (x + 1 * sg, y + 2.4), (x + 4, y)], O["hair_lt"], 1.0) for y in (226, 232, 238, 244)]
            out += cel(loop, O["hair"], O["hair_sh"], O["hair_lt"], items, s=2)
            out += [path(smooth([(x - 0.6 * sg, 228), (x + 1.8 * sg, 230), (x + 1.6 * sg, 242), (x - 0.4 * sg, 240)]), O["hair_sh"], INK, 1.0)]
    items = [path(smooth([(252, 210), (256, 228), (266, 242), (278, 250), (266, 238), (259, 224)]), sk),
             line([(258, 216), (264, 226)], sk, 1.2), line([(302, 216), (296, 226)], sk, 1.2),
             # the nose: a straight bridge shaded on his right, a rounded tip, the wings
             path(smooth([(277, 206), (279.4, 205), (279.6, 220), (276.4, 224), (274, 222)]), sk),
             ellipse(281.4, 219.6, 2.6, 1.8, O["skin_lt"]),
             line([(275.4, 219.0), (273.8, 222.4), (276.6, 225.0), (279.0, 224.6)], dk, 1.2),
             line([(284.6, 219.0), (286.2, 222.4), (283.4, 225.0), (281.0, 224.6)], dk, 1.2)]
    out += C(f_face_shape(), "skin", items, s=6)
    out += eye_front(267.5, 209.0, -1) + eye_front(292.5, 209.0, 1)
    hair = O["hair"]
    if O["brow"] == "stern":
        for sg in (-1, 1):
            pts = [(CX + sg * 4, 203.4), (CX + sg * 13, 200.6), (CX + sg * 20, 201.2), (CX + sg * 20, 203.6), (CX + sg * 12, 203.4), (CX + sg * 4.6, 206.0)]
            out += [path(smooth(pts), hair, INK, 1.0)]
        out += [line([(276.6, 203.4), (277.4, 207.4)], dk, 0.9), line([(283.4, 203.4), (282.6, 207.4)], dk, 0.9)]
    else:
        for sg in (-1, 1):
            pts = [(CX + sg * 4.4, 199.0), (CX + sg * 12, 200.0), (CX + sg * 20, 203.4), (CX + sg * 19.4, 205.6), (CX + sg * 12, 202.6), (CX + sg * 4.4, 201.8)]
            out += [path(smooth(pts), hair, INK, 1.0)]
        out += [line([(272, 191), (288, 191)], sk, 1.0), line([(274, 187.4), (286, 187.4)], sk, 0.9)]
    # the mouth, under the moustache
    if O["mouth"] == "firm":
        out += [line([(273.6, 235.4), (280, 236.0), (286.4, 235.4)], INK, 1.6)]
    else:
        out += [line([(273.4, 237.6), (280, 235.8), (286.6, 237.6)], INK, 1.5)]
    out += [line([(276.6, 240.6), (283.4, 240.6)], dk, 0.9)]
    # the tuft, then the moustache
    if O["beard"] == "spear":
        tuft = smooth([(274.6, 244), (285.4, 244), (283, 258), (280, 266, True), (277, 258)])
    else:
        tuft = smooth([(275.4, 245), (284.6, 245), (283.4, 262), (280, 276, True), (276.6, 262)])
    out += cel(tuft, hair, O["hair_sh"], O["hair_lt"], [line([(280, 248), (280, 262)], O["hair_sh"], 0.9)], s=2)
    for sg in (-1, 1):
        if O["stache"] == "sweep":
            pts = [(CX, 228.6), (CX + sg * 7, 228.4), (CX + sg * 12.4, 232.4), (CX + sg * 15.6, 242), (CX + sg * 17.4, 252, True), (CX + sg * 12.6, 244),
                   (CX + sg * 9.6, 235.4), (CX + sg * 4, 232.6), (CX, 232.6)]
        else:
            pts = [(CX, 228.6), (CX + sg * 7, 228.6), (CX + sg * 10.6, 232.6), (CX + sg * 11.6, 246), (CX + sg * 11.2, 262, True), (CX + sg * 8.2, 250),
                   (CX + sg * 7.6, 236.4), (CX + sg * 3.6, 232.8), (CX, 232.8)]
        out += cel(smooth(pts), hair, O["hair_sh"], O["hair_lt"], [], s=1.6, sw=2.2)
    return out


def f_hat_back():
    out = []
    hat = O["hat"]
    if hat == "cap":
        if O["who"] == "can":
            for k, (dy, tip) in enumerate(((0, (CX - 62, 190)), (8, (CX - 58, 214)))):
                d = smooth([(CX - 24, 194 + dy), (CX - 44, 192 + dy + k * 4), tip + (True,), (CX - 44, 202 + dy + k * 6), (CX - 24, 204 + dy)])
                out += C(d, "ribbon", [], s=2)
        else:
            for sg in (-1, 1):
                d = smooth([(CX + sg * 24, 198), (CX + sg * 31, 200), (CX + sg * 33, 262), (CX + sg * 30, 270, True), (CX + sg * 27, 262)])
                out += C(d, "ribbon", [], s=2)
    if hat == "helmet":
        half = [(CX, 196), (308, 196), (318, 214), (320, 244, True), (300, 252), (296, 230), (296, 210), (CX, 206)]
        d = smooth(sym(half))
        items = [line([(318, 226), (300, 228)], O["avent_sh"], 1.2), line([(242, 226), (260, 228)], O["avent_sh"], 1.2),
                 line([(310, 200), (310, 248)], O["avent_sh"], 1.0), line([(250, 200), (250, 248)], O["avent_sh"], 1.0)]
        out += C(d, "avent", items, s=4)
        if O["plume"] == "down":
            d = smooth([(CX - 6, 122), (CX + 4, 112), (CX + 22, 116), (CX + 38, 132), (CX + 46, 156), (CX + 48, 184), (CX + 52, 204, True), (CX + 42, 196),
                        (CX + 38, 206, True), (CX + 36, 180), (CX + 30, 152), (CX + 16, 130)])
            out += C(d, "plumec", [line([(CX + 8, 118), (CX + 28, 128), (CX + 40, 154), (CX + 44, 184)], O["plumec_sh"], 1.1),
                                   line([(CX + 4, 124), (CX + 22, 136), (CX + 34, 160), (CX + 40, 190)], O["plumec_sh"], 1.0)], s=3)
    if hat == "fur" and O["flaps"] == "down":
        for sg in (-1, 1):
            d = smooth([(CX + sg * 22, 196), (CX + sg * 36, 196), (CX + sg * 38, 226), (CX + sg * 33, 250, True), (CX + sg * 24, 246), (CX + sg * 24, 216)])
            out += C(d, "fur", [line([(CX + sg * 30, 204), (CX + sg * 30, 240)], O["fur_sh"], 1.1)], s=3)
    return out


def f_hat():
    hat = O["hat"]
    out = []
    if hat == "cap":
        half = [(CX, 155), (296, 157), (308, 166), (313, 181), (312, 194, True), (CX, 194)]
        out += C(smooth(sym(half)), "hatc", [line([(CX, 157), (CX, 190)], O["hatc_sh"], 1.0), line([(298, 163), (306, 186)], O["hatc_lt"], 1.6)], s=5)
        out += [ellipse(CX, 153, 4.6, 3.6, O["ribbon"], INK, 1.2)]
        top = scallop([(246, 186), (CX, 182), (314, 186)], 9, 2.4)
        brim = smooth(top + [(316, 198, True), (CX, 200), (244, 198, True)])
        out += C(brim, "fur", [line([(256, 194), (270, 194)], O["fur_sh"], 1.0), line([(290, 194), (304, 194)], O["fur_sh"], 1.0)], s=3)
    elif hat == "helmet":
        half = [(CX, 134, True), (292, 146), (304, 166), (310, 194, True), (CX, 194)]
        items = [line([(CX, 138), (CX, 192)], O["helm_sh"], 1.3), line([(CX, 138), (264, 192)], O["helm_sh"], 1.2), line([(CX, 138), (296, 192)], O["helm_sh"], 1.2),
                 line([(288, 146), (302, 184)], O["helm_lt"], 1.8)]
        out += C(smooth(sym(half)), "helm", items, s=5)
        out += C(smooth([(246, 188, True), (314, 188, True), (316, 199, True), (244, 199, True)]), "band", [], s=1.5)
        out += [ellipse(x, 193.6, 1.8, 1.8, O["gold"], INK, 0.9) for x in (254, 267, 293, 306)]
        out += C(smooth([(270, 196), (CX, 192), (290, 196), (288, 203, True), (272, 203, True)]), "helm", [], s=1.5)
        out += C(capsule((CX, 134), (CX, 116), 2.6, 2.2), "helm", [], s=1)
        out += C(smooth([(CX - 6, 118), (CX + 6, 118), (CX + 3, 111, True), (CX - 3, 111, True)]), "helm", [], s=1)
        if O["plume"] == "up":
            d = smooth([(CX - 5, 112), (CX - 14, 96), (CX - 18, 74), (CX - 10, 82), (CX - 6, 62), (CX, 78), (CX + 6, 62), (CX + 10, 82), (CX + 18, 74),
                        (CX + 14, 96), (CX + 5, 112)])
            items = [line([(CX, 108), (CX, 80)], O["plumec_sh"], 1.1), line([(CX - 4, 106), (CX - 10, 86)], O["plumec_sh"], 1.0),
                     line([(CX + 4, 106), (CX + 10, 86)], O["plumec_lt"], 1.0)]
            out += C(d, "plumec", items, s=3)
    elif hat == "fur":
        half = [(CX, 132, True), (290, 146), (300, 168), (304, 188, True), (CX, 188)]
        out += C(smooth(sym(half)), "hatc", [line([(CX, 134), (CX, 186)], O["hatc_sh"], 1.1), line([(290, 150), (298, 182)], O["hatc_lt"], 1.6)], s=4)
        out += [ellipse(CX, 131, 4.6, 4.0, O["knot"], INK, 1.2)]
        if O["flaps"] == "up":
            # the flaps tied up: a deep roll of fox fur flaring up round the crown
            top = scallop([(232, 168), (CX, 161), (328, 168)], 8, 4.2)
            band = smooth(top + [(330, 178), (322, 194), (310, 202, True), (CX, 204), (250, 202, True), (238, 194), (230, 178)])
            out += C(band, "fur", fur_ticks(238, 172, 322, 200), s=4)
        else:
            band = smooth(scallop([(244, 184), (CX, 180), (316, 184)], 9, 2.2) + [(318, 198, True), (CX, 202), (242, 198, True)])
            out += C(band, "fur", [line([(256, 194), (270, 194)], O["fur_sh"], 1.0), line([(290, 194), (304, 194)], O["fur_sh"], 1.0)], s=3)
    return out


def f_arm(side):
    """One arm of the front view: ``R`` (his right, screen-left) or ``L``."""
    re_, rw, le, lw = F_POSES[O["pose"]]
    (rs, ls) = f_shoulders()
    s, e, w = (rs, re_, rw) if side == "R" else (ls, le, lw)
    pose = O["pose"]
    a = ang(e, w)
    out = []
    if pose == "sabre" and side == "R":
        out += sabre(frame(w, a)(9, 0), math.radians(-96), length=96)
    out += sleeve(s, e, w, near=True)
    if O.get("armor"):
        out += pauldron(s, e)
    thumb = 1 if side == "R" else -1
    if pose == "point" and side == "L":
        out += point_hand(w, a, True, thumb=1)
    elif pose == "map":
        out += fist(w, a, True, thumb=0)
    else:
        out += fist(w, a, True, thumb=thumb)
    out += cuff(e, w)
    return out


def f_props():
    out = []
    if O["pose"] == "map":
        out += map_sheet([(242, 296), (318, 296), (318, 338), (242, 338)])
        for sg in (-1, 1):  # the thumbs over the rolls
            x = CX + sg * 38
            out += cel(capsule((x + sg * 6, 318), (x - sg * 3, 312), 3.2, 2.8), O["skin"], O["skin_sh"], O["skin_lt"], [], s=1.4, sw=2.2)
    if O["pose"] == "clasp":
        for k, y in enumerate((330, 335, 340)):
            out += cel(capsule((268, y), (290, y + 1), 2.6, 2.4), O["skin"], O["skin_sh"], O["skin_lt"], [], s=1.2, sw=1.8)
    return out


def front_layers():
    head = [(F_NECK[0], F_NECK[1], O["f_tilt"])]
    dy = O["f_head_dy"]
    pose = O["pose"]
    L = [
        ("hat-back", f_hat_back, head),
        ("boots", f_boots, []),
        ("skirt", f_skirt, []),
    ]
    if O.get("armor"):
        L.append(("tassets", f_tassets, []))
    L.append(("torso", f_torso, []))
    if O.get("armor"):
        L.append(("cuirass", f_cuirass, []))
    L += [("sash", f_sash, [])]
    behind = pose in ("akimbo", "sabre", "point")
    if behind:
        L += [("arm-R", lambda: f_arm("R"), []), ("arm-L", lambda: f_arm("L"), [])]
    L += [("neck", f_neck, []), ("head", f_head, head), ("hat", f_hat, head)]
    if pose == "chin":
        L += [("arm-L", lambda: f_arm("L"), []), ("arm-R", lambda: f_arm("R"), [])]
    elif not behind:
        L += [("arm-R", lambda: f_arm("R"), []), ("arm-L", lambda: f_arm("L"), [])]
    L.append(("props", f_props, []))
    return [(n, p, r, dy if n in ("hat-back", "head", "hat") else 0.0) for n, p, r in L]


# ============================================================================================
# THE DOCUMENT
# ============================================================================================

def svg_text(look: str, who: str, view: str) -> str:
    use(look, who)
    _N[0] = 0
    svg.configure(dx=0, dy=0, ink=INK, ow=OW, colors={})
    _MAP["scale"] = O["scale"]
    if view == "side":
        layers = [(n, p, r, 0.0) for n, p, r in side_layers()]
    else:
        layers = front_layers()
    for name, painter, rots, dy in layers:
        _MAP["rots"] = list(rots)
        body = _with_dy(painter, dy)
        _MAP["rots"] = []
        svg.part(name, name.replace("-", " ").title(), name.replace("-", "_"), name.replace("-", "_"), len(svg.PARTS), body)
    _MAP["scale"] = 1.0
    label = f"{O['name']} - {'Side Right' if view == 'side' else 'Front'}"
    return svg.document(
        size=(W, H), design=f"genghis-{who}-{look}", layer_id=f"genghis-{who}", label=label,
        comment=[f"  <!-- CANDIDATE, NOT CAST: {O['name']}, look {LETTER[look]} ({LOOKS[look]['blurb']}), {label} (2026-10-23);",
                 f"       the ground at y={GROUND_Y:g}. Drawn by scripts/svg_art/genghis_pair_art.py. -->"],
        joints=[],
    )


def _with_dy(painter, dy):
    """Run ``painter`` with its points shifted down by ``dy`` first (the front
    view's lowered head)."""
    if not dy:
        return painter()
    rots = _MAP["rots"]

    def P2(x, y):
        y = y + dy
        for cx, cy, deg in rots:
            x, y = _rot(x, y, cx, cy + dy, deg)
        k = _MAP["scale"]
        x, y = CX + (x - CX) * k, GROUND_Y + (y - GROUND_Y) * k
        return _P0(x, y)

    svg.P = P2
    try:
        return painter()
    finally:
        svg.P = _P


# ============================================================================================
# THE RIG: look C (steppe), the cast look, as one part per bone
# ============================================================================================

#: The look the game shows (decided 2026-10-23 after round 1: C, steppe).
CAST_LOOK = "steppe"
ROOT = Path(__file__).resolve().parents[2]


def rig_out(who: str) -> Path:
    name = f"genghis_{who}_v2"
    return ROOT / "ambition_sprite2d_renderer" / "data" / "characters" / name / f"{name}.svg"


def rig_view(who: str) -> str:
    return f"{WHO[who]['name']} - Side Right"


#: The legs under the deel, in the body's frame (no lean): hips, knees, ankles.
#: The ankle is where the boot's shaft meets its foot.
S_LEGS = dict(near_hip=(280.0, 362.0), far_hip=(262.0, 360.0), near_knee=(283.0, 420.0), far_knee=(262.0, 420.0),
              near_ankle=(284.0, 480.0), far_ankle=(262.0, 480.0))

#: Each bone: (parent, the joint of the drawing it turns about). Parents first.
BONES = {
    "body": ("", "pelvis"),
    "skirt": ("body", "pelvis"),
    "torso": ("body", "pelvis"),
    "head": ("torso", "neck"),
    "far_arm_u": ("torso", "far_shoulder"),
    "far_arm_l": ("far_arm_u", "far_elbow"),
    "near_arm_u": ("torso", "near_shoulder"),
    "near_arm_l": ("near_arm_u", "near_elbow"),
    "near_hand": ("near_arm_l", "near_wrist"),
    "far_leg_u": ("body", "far_hip"),
    "far_leg_l": ("far_leg_u", "far_knee"),
    "far_foot": ("far_leg_l", "far_ankle"),
    "near_leg_u": ("body", "near_hip"),
    "near_leg_l": ("near_leg_u", "near_knee"),
    "near_foot": ("near_leg_l", "near_ankle"),
}

TROUSER = dict(trou="#3a302b", trou_sh="#241d19", trou_lt="#54463e")


def _torso_rots():
    return [(S_WAIST[0], S_WAIST[1], O["lean"])]


def _head_rots():
    return [(S_NECK[0], S_NECK[1], O["pitch"]), (S_WAIST[0], S_WAIST[1], O["lean"])]


def _mapped(p, rots):
    x, y = p
    for cx, cy, deg in rots:
        x, y = _rot(x, y, cx, cy, deg)
    k = O["scale"]
    return (CX + (x - CX) * k, GROUND_Y + (y - GROUND_Y) * k)


def joints(who: str) -> Dict[str, tuple]:
    """Where each joint of ``who``'s cast drawing is DRAWN, in SVG units (the
    posture's lean and pitch and his scale applied)."""
    use(CAST_LOOK, who)
    tr = _torso_rots()
    ns, ne, nw = s_arm_points("near")
    fs, fe, fw = s_arm_points("far")
    J = {"pelvis": _mapped(S_WAIST, []), "neck": _mapped(S_NECK, tr),
         "near_shoulder": _mapped(ns, tr), "near_elbow": _mapped(ne, tr), "near_wrist": _mapped(nw, tr),
         "far_shoulder": _mapped(fs, tr), "far_elbow": _mapped(fe, tr), "far_wrist": _mapped(fw, tr)}
    for k, p in S_LEGS.items():
        J[k] = _mapped(p, [])
    return J


def r_thigh(near):
    hip, knee = (S_LEGS["near_hip"], S_LEGS["near_knee"]) if near else (S_LEGS["far_hip"], S_LEGS["far_knee"])
    d = capsule(hip, knee, 12.0, 10.5)
    return C(d, "trou", [], s=4) if near else far(d, "trou")


def r_shin(near):
    """The trouser from the knee into the boot, then the boot's shaft."""
    knee = S_LEGS["near_knee"] if near else S_LEGS["far_knee"]
    ax = 284.0 if near else 262.0
    out = C(capsule(knee, (ax, 436), 10.5, 9.5), "trou", [], s=3) if near else far(capsule(knee, (ax, 436), 10.5, 9.5), "trou")
    shaft = smooth([(ax - 12, 424), (ax + 10, 424), (ax + 11, 470), (ax + 13, 484), (ax - 13, 488, True), (ax - 13, 456)])
    if near:
        out += C(shaft, "boot", [line([(ax - 11, 432), (ax + 10, 432)], O["trim"], 2.4), line([(ax - 4, 444), (ax + 2, 462), (ax - 2, 474)], O["boot_lt"], 1.1)],
                 s=4)
    else:
        out += far(shaft, "boot")
    return out


def r_foot(near):
    """The boot's foot, its toe turned up, and its thick sole."""
    ax = 284.0 if near else 262.0
    foot = smooth([(ax - 14, 474), (ax + 8, 474), (ax + 22, 484), (ax + 30, 478), (ax + 33, 471, True), (ax + 31, 484), (ax + 26, 494), (ax + 18, 496),
                   (ax - 14, 496, True)])
    sole = smooth([(ax - 15, 494, True), (ax + 20, 494), (ax + 28, 492), (ax + 26, 502, True), (ax - 15, 502, True)])
    if near:
        return C(foot, "boot", [line([(ax - 6, 486), (ax + 8, 482), (ax + 20, 487), (ax + 28, 480)], O["trim"], 1.6)], s=3) + C(sole, "sole", [], s=1.5)
    return far(foot, "boot") + far(sole, "sole")


def r_arm(side, piece):
    """One piece of an arm: ``upper`` (the sleeve to the elbow), ``lower`` (the
    sleeve to the wrist; on the far arm also the hand and the cuff), ``hand``,
    ``cuff``."""
    s, e, w = s_arm_points(side)
    near = side == "near"
    a = ang(e, w)
    if piece == "upper":
        return sleeve(s, e, w, near=near, lower=False)
    if piece == "lower":
        out = sleeve(s, e, w, near=near, upper=False)
        if not near:
            out += s_hand("far", w, a, False) + cuff(e, w, near=False)
        return out
    if piece == "hand":
        return s_hand(side, w, a, near)
    return cuff(e, w, near=near)


def eye_shut_profile(ex, ey):
    """The eye closed: the lid down to a soft line, the lashes' crease under it."""
    return [path(smooth([(ex - 4.8, ey - 0.2), (ex + 0.4, ey - 3.6), (ex + 5.2, ey - 2.0), (ex + 4.6, ey + 2.6), (ex - 0.6, ey + 3.0)]), O["skin"]),
            line([(ex - 4.6, ey + 0.8), (ex + 0.4, ey + 2.0), (ex + 4.8, ey + 0.6)], INK, 1.8),
            line([(ex - 3.0, ey - 1.6), (ex + 2.6, ey - 2.4)], O["skin_sh"], 0.9)]


def mouth_open_profile():
    """The mouth open under the moustache: a dark wedge back from the lips,
    the tongue low in it."""
    d = smooth([(294.4, 233.6, True), (302.2, 233.8), (302.6, 238.6, True), (298.4, 241.4), (294.6, 238.6)])
    tongue = smooth([(296.0, 239.0), (300.8, 238.6), (299.6, 240.8), (296.8, 240.6)])
    return [path(d, "#4e2420", INK, 1.2), path(tongue, "#b0645a")]


def r_head():
    """The head without its eye, brow, beard and hat (those are their own parts)."""
    hat = O["hat"]
    show_ear = hat == "cap" or (hat == "fur" and O["flaps"] == "up")
    out = C(smooth(s_face_points()), "skin", [path(smooth([(252, 214), (262, 232), (276, 244), (290, 250), (300, 249), (290, 253), (272, 249), (258, 236)]),
                                                   O["skin_sh"])], s=6)
    nape = [(250.6, 194), (258, 194), (259.6, 206), (256.6, 220), (252, 226)]
    out += cel(smooth(nape + [(249.6, 216), (249.4, 202)]), O["hair"], O["hair_sh"], O["hair_lt"], [], s=2, edges=[nape])
    out += s_ear_and_loop(show_ear, hat != "helmet")
    return out + s_face_lines() + s_mouth()


#: The parts, back to front: (group id, label, part, bone, z, painter, rotations, opacity channel).
def rig_layers():
    tr, hr = _torso_rots(), _head_rots()
    return [
        ("hat-back", "Hat - Back (Flaps)", "hat_back", "head", 5, s_hat_back, hr, ""),
        ("far-arm-upper", "Far Arm - Upper", "far_arm_u", "far_arm_u", 10, lambda: r_arm("far", "upper"), tr, ""),
        ("far-arm-lower", "Far Arm - Lower and Hand", "far_arm_l", "far_arm_l", 11, lambda: r_arm("far", "lower"), tr, ""),
        ("far-thigh", "Far Thigh", "far_leg_u", "far_leg_u", 20, lambda: r_thigh(False), [], ""),
        ("far-shin", "Far Shin and Boot", "far_leg_l", "far_leg_l", 21, lambda: r_shin(False), [], ""),
        ("far-foot", "Far Foot", "far_foot", "far_foot", 22, lambda: r_foot(False), [], ""),
        ("near-thigh", "Near Thigh", "near_leg_u", "near_leg_u", 30, lambda: r_thigh(True), [], ""),
        ("near-shin", "Near Shin and Boot", "near_leg_l", "near_leg_l", 31, lambda: r_shin(True), [], ""),
        ("near-foot", "Near Foot", "near_foot", "near_foot", 32, lambda: r_foot(True), [], ""),
        ("skirt", "Deel - Skirt", "skirt", "skirt", 40, s_skirt, [], ""),
        ("torso", "Deel - Body", "torso", "torso", 50, s_torso, tr, ""),
        ("sash", "Sash and Quiver", "sash", "torso", 52, s_sash, tr, ""),
        ("neck", "Neck and Collar", "neck", "torso", 54, s_neck, tr, ""),
        ("head", "Head", "head", "head", 60, r_head, hr, ""),
        ("eye-open", "Eye - Open", "eye_open", "head", 61, lambda: eye_profile(*S_EYE), hr, "eye_open"),
        ("eye-shut", "Eye - Shut", "eye_shut", "head", 61, lambda: eye_shut_profile(*S_EYE), hr, "eye_shut"),
        ("mouth-open", "Mouth - Open", "mouth_open", "head", 61.5, mouth_open_profile, hr, "mouth_open"),
        ("beard", "Moustache and Tuft", "beard", "head", 62, s_beard, hr, ""),
        ("brow", "Brow", "brow", "head", 63, s_brow, hr, ""),
        ("hat", "Fox-Fur Hat", "hat", "head", 64, s_hat, hr, ""),
        ("near-arm-upper", "Near Arm - Upper", "near_arm_u", "near_arm_u", 80, lambda: r_arm("near", "upper"), tr, ""),
        ("near-arm-lower", "Near Arm - Lower", "near_arm_l", "near_arm_l", 81, lambda: r_arm("near", "lower"), tr, ""),
        ("near-hand", "Near Hand", "near_hand", "near_hand", 82, lambda: r_arm("near", "hand"), tr, ""),
        ("near-cuff", "Near Cuff", "near_cuff", "near_arm_l", 83, lambda: r_arm("near", "cuff"), tr, ""),
    ]


def rig_parts(who: str):
    """``who``'s parts as the SVG holds them: (group id, part, bone, z, opacity
    channel), the empty ones left out."""
    use(CAST_LOOK, who)
    O.update(TROUSER)
    out = []
    for group, _label, name, bone, z, painter, _rots, channel in rig_layers():
        if painter():
            out.append((group, name, bone, z, channel))
    return out


def rig_svg_text(who: str) -> str:
    """``who``'s cast drawing: the side view facing right, one part per bone."""
    use(CAST_LOOK, who)
    O.update(TROUSER)
    _N[0] = 0
    svg.configure(dx=0, dy=0, ink=INK, ow=OW, colors={})
    svg.PARTS.clear()
    _MAP["scale"] = O["scale"]
    for group, label, name, bone, z, painter, rots, channel in rig_layers():
        _MAP["rots"] = list(rots)
        body = painter()
        _MAP["rots"] = []
        if not body:  # Can's flaps are tied up: nothing hangs behind his head
            continue
        extra = f' data-rig-opacity="{channel}"' + (' data-rig-default="1"' if channel == "eye_open" else "") if channel else ""
        svg.part(group, label, name, bone, z, body, extra)
    _MAP["scale"] = 1.0
    J = joints(who)
    O.update(TROUSER)
    text = svg.document(
        size=(W, H), design=f"genghis-{who}-v2-{CAST_LOOK}", layer_id=f"genghis-{who}-v2", label=rig_view(who),
        comment=[f"  <!-- {O['name']}, look C (steppe: a winter deel and a fox-fur hat), cast 2026-10-23: side view facing right,",
                 f"       the ground at y={GROUND_Y:g}. Drawn by the rig mode of scripts/svg_art/genghis_pair_art.py; each part turns about its bone's joint. -->"],
        joints=svg.joints_layer(J),
    )
    return text


# ============================================================================================
# CONTACT SHEETS (review only; need resvg_py, the renderer's tool venv has it)
# ============================================================================================

def rasterize(svg_string: str, px_per_unit: float):
    import resvg_py
    from PIL import Image
    png = resvg_py.svg_to_bytes(svg_string=svg_string, dpi=float(px_per_unit * 25.4))
    return Image.open(io.BytesIO(bytes(png))).convert("RGBA")


def _crop(img, box_units, k):
    x0, y0, x1, y1 = box_units
    return img.crop((int(x0 * k), int(y0 * k), int(x1 * k), int(y1 * k)))


BG = (215, 220, 228, 255)
#: The figure's crop (design units): wide enough for the plume, the sabre and the pointing arm.
FIG_BOX = (140, 52, 444, 506)
#: Game size: Can is 173 cm and stands ~96 px tall in game.
GAME_K = 96.0 / (GROUND_Y - 150.0)


def head_boxes(look, who):
    """The head close-ups' crops, following the head through the posture."""
    use(look, who)
    k = O["scale"]

    def box(x, y):
        x, y = CX + (x - CX) * k, GROUND_Y + (y - GROUND_Y) * k
        return (x - 72, y - 112, x + 72, y + 66)
    x, y = _rot(282.0, 212.0, S_NECK[0], S_NECK[1], O["pitch"])
    x, y = _rot(x, y, S_WAIST[0], S_WAIST[1], O["lean"])
    fx_, fy_ = _rot(CX, 212.0 + O["f_head_dy"], F_NECK[0], F_NECK[1] + O["f_head_dy"], O["f_tilt"])
    return box(x, y), box(fx_, fy_)


def _font(size):
    from PIL import ImageFont
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"):
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def _on_bg(img):
    from PIL import Image
    bg = Image.new("RGBA", img.size, BG)
    bg.alpha_composite(img)
    return bg


def contact_sheet(who: str, out: Path) -> None:
    """Per look: a label, the side figure, the front figure, a head close-up,
    and both views at game size."""
    from PIL import Image, ImageDraw
    k = 1.5
    rows = []
    for look in LOOK_ORDER:
        side = rasterize(svg_text(look, who, "side"), k)
        front = rasterize(svg_text(look, who, "front"), k)
        head = rasterize(svg_text(look, who, "side"), 4.0)
        fhead = rasterize(svg_text(look, who, "front"), 4.0)
        sbox, fbox = head_boxes(look, who)
        gs = rasterize(svg_text(look, who, "side"), GAME_K)
        gf = rasterize(svg_text(look, who, "front"), GAME_K)
        rows.append((look, _crop(side, FIG_BOX, k), _crop(front, FIG_BOX, k), _crop(head, sbox, 4.0), _crop(fhead, fbox, 4.0),
                     _crop(gs, FIG_BOX, GAME_K), _crop(gf, FIG_BOX, GAME_K)))
    pad, lab = 16, 30
    widths = [r[1].width + r[2].width + r[3].width // 2 + (r[5].width + r[6].width) * 3 + pad * 8 for r in rows]
    Wd = max(widths)
    Hd = sum(lab + max(r[1].height, r[3].height // 2 + r[4].height // 2 + pad) + pad for r in rows) + pad
    sheet = Image.new("RGBA", (Wd, Hd), BG)
    dr = ImageDraw.Draw(sheet)
    font = _font(18)
    y = pad
    for look, s, f, h, fh, gs, gf in rows:
        lk = LOOKS[look]
        dr.text((pad, y), f"{LETTER[look]}: {lk['label']} -- {lk['blurb']}; {WHO[who]['name']} {_pose_blurb(look, who)}", fill=(30, 26, 24, 255), font=font)
        y += lab
        x = pad
        for im in (s, f):
            sheet.alpha_composite(im, (x, y))
            x += im.width + pad
        h2 = h.resize((h.width // 2, h.height // 2))
        fh2 = fh.resize((fh.width // 2, fh.height // 2))
        sheet.alpha_composite(h2, (x, y))
        sheet.alpha_composite(fh2, (x, y + h2.height + pad))
        x += max(h2.width, fh2.width) + pad
        for im in (gs, gf):
            sheet.alpha_composite(im, (x, y + s.height - im.height))
            x += im.width + 4
        x += pad
        dr.text((x, y + s.height - gs.height * 2 - 24), "game size | 2x nearest", fill=(70, 66, 64, 255), font=_font(13))
        for im in (gs, gf):
            b = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
            sheet.alpha_composite(b, (x, y + s.height - b.height))
            x += b.width + 4
        y += max(s.height, h2.height + fh2.height + pad) + pad
    sheet.save(out)
    print(out)


def _pose_blurb(look, who):
    return {"akimbo": "stands akimbo", "map": "reads the map", "sabre": "raises his sabre, plume up",
            "clasp": "wrings his hands, plume down", "point": "points the way, flaps up", "chin": "cups his chin, flaps down"}[LOOKS[look][who]["pose"]]


def pair_sheet(out: Path) -> None:
    """Per look, both brothers side by side at game size (side then front), and
    once more at 3x so the read can be judged without squinting."""
    from PIL import Image, ImageDraw
    font = _font(16)
    cells = []
    for look in LOOK_ORDER:
        ims = []
        for who in ("can", "cant"):
            for view in ("side", "front"):
                ims.append(_crop(rasterize(svg_text(look, who, view), GAME_K), FIG_BOX, GAME_K))
        cells.append((look, ims))
    pad = 12
    cw = sum(im.width for im in cells[0][1]) + pad * 3
    big = 3
    Wd = pad + (cw + pad) + cw * big + pad * 2
    ch = cells[0][1][0].height
    Hd = pad + len(cells) * (ch * big + 28 + pad)
    sheet = Image.new("RGBA", (Wd, Hd), BG)
    dr = ImageDraw.Draw(sheet)
    y = pad
    for look, ims in cells:
        dr.text((pad, y), f"{LETTER[look]}: {LOOKS[look]['label']} -- Genghis Can (left pair) and Genghis Can't (right pair), game size and 3x nearest",
                fill=(30, 26, 24, 255), font=font)
        y += 28
        x = pad
        for i, im in enumerate(ims):
            sheet.alpha_composite(im, (x, y + ch * big - im.height))
            x += im.width + (pad * 2 if i == 1 else 2)
        x += pad * 2
        for i, im in enumerate(ims):
            b = im.resize((im.width * big, im.height * big), Image.NEAREST)
            sheet.alpha_composite(b, (x, y))
            x += b.width + (pad * 2 if i == 1 else 2)
        y += ch * big + pad
    sheet.save(out)
    print(out)


def main() -> None:
    if len(sys.argv) > 2 and sys.argv[1] == "--all":
        out = Path(sys.argv[2])
        out.mkdir(parents=True, exist_ok=True)
        for look in LOOK_ORDER:
            for who in ("can", "cant"):
                for view in ("side", "front"):
                    p = out / f"genghis_{who}_{LETTER[look]}_{look}_{view}.svg"
                    p.write_text(svg_text(look, who, view), encoding="utf8")
                    print(p)
        return
    if len(sys.argv) > 1 and sys.argv[1] == "--rig":
        for who in ("can", "cant"):
            out = rig_out(who)
            out.parent.mkdir(parents=True, exist_ok=True)
            tmp = out.with_suffix(".svg.tmp")
            tmp.write_text(rig_svg_text(who), encoding="utf8")
            tmp.replace(out)
            print(f"wrote {out.relative_to(ROOT)}")
        return
    if len(sys.argv) > 2 and sys.argv[1] == "--sheets":
        out = Path(sys.argv[2])
        out.mkdir(parents=True, exist_ok=True)
        contact_sheet("can", out / "genghis_can_r1.png")
        contact_sheet("cant", out / "genghis_cant_r1.png")
        pair_sheet(out / "pair_r1.png")
        return
    raise SystemExit("usage: genghis_pair_art.py --rig | --all DIR | --sheets DIR")


if __name__ == "__main__":
    main()
