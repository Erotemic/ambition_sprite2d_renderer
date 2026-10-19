#!/usr/bin/env python3
"""How the Ghoul Skulker's SVG was first drawn (reference, not authority).

    uv run python scripts/svg_art/ghoul_skulker_art.py            # its look (B)
    uv run python scripts/svg_art/ghoul_skulker_art.py --all DIR  # every look, to DIR

Writes ``data/characters/ghoul_skulker/ghoul_skulker.svg``; the SVG owns the
art after this has run once. ``JOINTS`` says where each part turns and
``LAYERS`` lists the parts; ``scripts/build_ghoul_skulker_rig.py`` reads both
and authors the rows.

Jon, 2026-10-18, of three redraws of the ghoul: "B for default skulker", and
"keep all 3 for basically everyone". B (``shroud``) is a stitched corpse in a
burial shroud: blue-grey skin, a stitched seam across the chest and round
the shoulder, the shroud as a hood and a wrap at the hips, long arms that
hang to the shins. A (``capped``, the old ghoul redrawn with its leather cap
and flap) and C (``bog``, a feral bog ghoul nearly on all fours) are KEPT,
NOT CAST: ``--all`` draws them whole, as their candidates were drawn, and
nothing rigs or registers them.

The read of the old ghoul is kept in every look: a crouched creeping wretch,
a hooked nose, moustache tendrils, a loincloth, bony limbs and clawed hands.

Drawing: cel-shaded with a thin ink. Within one part every shape's ink is
painted first and every fill over it; a part drawn later overlaps an earlier
one with its own ink edge (an elbow knob over the upper arm it turns on).
"""
from __future__ import annotations

import math
import re
import sys
from pathlib import Path
from typing import Dict, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import svgkit as svg  # noqa: E402
from svgkit import capsule, ellipse, line, path, smooth  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "ambition_sprite2d_renderer" / "data" / "characters" / "ghoul_skulker" / "ghoul_skulker.svg"
VIEW = "Ghoul Skulker - Side Right"
LOOK = "shroud"
W, H = 560, 560
#: The ground under its feet, in SVG units.
GROUND_Y = 470.0

# ---------------------------------------------------------------- cel kit

INK = "#171a20"
#: The outward growth of a silhouette's ink, design units.
INKW = 2.0
_CID = [0]


def set_ink(ink: str, w: float = 2.0) -> None:
    global INK, INKW
    INK, INKW = ink, w
    svg.configure(ink=ink, ow=1.0, colors={})


def shift_d(d: str, dx: float, dy: float) -> str:
    return re.sub(r"(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)",
                  lambda m: f"{float(m.group(1)) + dx:.2f},{float(m.group(2)) + dy:.2f}", d)


def cel(sil, base, light=None, shade=None, a=5.0, b=2.0, extra=()):
    """The cel-shaded fill of one shape: its LIGHT colour, the base shifted
    down-back, then a SHADE band on the down-back edge; ``extra`` clipped in."""
    _CID[0] += 1
    cid = f"g{_CID[0]}"
    items = []
    if light:
        items += [path(sil, light), path(shift_d(sil, -b, b), base)]
    else:
        items.append(path(sil, base))
    if shade:
        items.append(f'<path d="{sil} {shift_d(sil, a, -a)}" fill="{shade}" fill-rule="evenodd" />')
    items += list(extra)
    return [f'<clipPath id="{cid}"><path d="{sil}" /></clipPath>', f'<g clip-path="url(#{cid})">'] + items + ["</g>"]


class Group:
    """Shapes that read as one silhouette: every ink, then every fill."""

    def __init__(self):
        self.shapes = []
        self.post = []

    def add(self, sil, base, light=None, shade=None, a=5.0, b=2.0, extra=(), ink=True):
        self.shapes.append((sil, dict(base=base, light=light, shade=shade, a=a, b=b, extra=extra), ink))
        return self

    def items(self):
        out = [path(s, INK, INK, 2 * INKW) for s, _k, ink in self.shapes if ink]
        for s, k, _ink in self.shapes:
            out += cel(s, **k)
        return out + self.post


def skin(o, far=False):
    if far:
        return dict(base=o["far"], shade=o["far_sh"], a=2.6)
    return dict(base=o["skin"], light=o["skin_lt"], shade=o["skin_sh"], a=3.0, b=1.6)


def cloth(o, k="cloth"):
    return dict(base=o[k], light=o.get(k + "_lt"), shade=o[k + "_sh"], a=4, b=2)


def rot(v, deg):
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return (v[0] * c - v[1] * s, v[0] * s + v[1] * c)


def add(p, v, k=1.0):
    return (p[0] + v[0] * k, p[1] + v[1] * k)


# ------------------------------------------------------------------ limbs

def knob(g, p, r, pal):
    g.add(capsule(p, (p[0] + 0.1, p[1]), r, r), **pal)


def hand(g, o, wrist, deg, far=False, curl=28.0, spread=1.0, length=1.0):
    """A long-fingered claw: the palm along ``deg`` (0 = +x, y down), four
    fingers curling by ``curl`` per joint, dark hooked nails; thumb below."""
    pal = skin(o, far)
    u = rot((1, 0), deg)
    n = (-u[1], u[0])

    def Pt(t, s):
        return (wrist[0] + u[0] * t + n[0] * s, wrist[1] + u[1] * t + n[1] * s)

    g.add(smooth([Pt(-3, -6), Pt(10, -7.5), Pt(15, -2), Pt(14, 6), Pt(2, 7.5), Pt(-3, 4)]), **pal)
    nails = []
    for off, L in ((-5.5, 13), (-1.8, 15), (1.8, 14), (5.4, 11)):
        base = Pt(12, off * 0.9)
        d1 = rot(u, off * 3.0 * spread)
        m = add(base, d1, L * length * 0.55)
        d2 = rot(d1, curl)
        tip = add(m, d2, L * length * 0.5)
        g.add(capsule(base, m, 2.6, 2.3), **pal)
        g.add(capsule(m, tip, 2.3, 1.9), **pal)
        d3 = rot(d2, curl * 0.9)
        nb = (-d3[1], d3[0])
        nails.append(smooth([add(tip, nb, 2.0), add(add(tip, d3, 6.5), nb, 0.3) + (True,), add(tip, nb, -2.0), add(tip, d3, -1.5)]))
    th0 = Pt(4, 6)
    th1 = add(th0, rot(u, 40), 10)
    g.add(capsule(th0, th1, 2.8, 2.2), **pal)
    d = rot(u, 40 + curl)
    nb = (-d[1], d[0])
    nails.append(smooth([add(th1, nb, 1.8), add(add(th1, d, 5.5), nb, 0.2) + (True,), add(th1, nb, -1.8), add(th1, d, -1.2)]))
    for nl in nails:
        g.add(nl, base=o["nail"], light=o.get("nail_lt"), shade=None, b=0.8)


def foot(g, o, ankle, far=False, size=1.0):
    """A long bony bare foot, toes on the ground, small dark nails."""
    pal = skin(o, far)
    ax, ay = ankle
    s = size
    G = GROUND_Y
    f = smooth([(ax - 5 * s, ay - 4), (ax + 5 * s, ay - 2), (ax + 16 * s, G - 8), (ax + 27 * s, G - 6.5), (ax + 33 * s, G - 3),
                (ax + 31 * s, G, True), (ax - 6 * s, G, True), (ax - 9 * s, G - 4), (ax - 8 * s, ay + 4)])
    toes = [line([(ax + (22 + 4 * k) * s, G - 6 + k * 0.6), (ax + (23 + 4 * k) * s, G - 1)], o["skin_dk"], 1.0) for k in range(2)]
    g.add(f, **pal, extra=toes if not far else [])
    g.add(smooth([(ax + 29 * s, G - 4.5), (ax + 37 * s, G - 1.2, True), (ax + 30 * s, G - 0.4)]), base=o["nail"])


def leg(o, hip, knee, ankle, groups, far=False, r=(7.4, 5.8, 4.0)):
    """Thigh, shin (a knob at the knee) and foot, into ``groups``."""
    gu, gl, gf = groups
    pal = skin(o, far)
    gu.add(capsule(hip, knee, r[0], r[1]), **pal)
    gl.add(capsule(knee, ankle, r[1] * 0.92, r[2]), **pal)
    knob(gl, knee, r[1] * 1.05, pal)
    foot(gf, o, ankle, far)


def arm(o, sh, el, wr, deg, groups, far=False, curl=28.0, r=(6.4, 5.0, 4.0)):
    """Upper arm, forearm (a knob at the elbow) and claw, into ``groups``."""
    gu, gl, gh = groups
    pal = skin(o, far)
    gu.add(capsule(sh, el, r[0], r[1]), **pal)
    gl.add(capsule(el, wr, r[1], r[2]), **pal)
    knob(gl, el, r[1] * 1.08, pal)
    hand(gh, o, wr, deg, far, curl=curl)


# ------------------------------------------------------------------ head

def _tendril(pts, w, fill, lt):
    """A tapering drooping wisp through ``pts`` (inked)."""
    left, right = [], []
    n = len(pts)
    for i, p in enumerate(pts):
        a = pts[max(0, i - 1)]
        b = pts[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d
        ww = w * (1 - i / (n - 1)) * 0.9 + 0.35
        left.append((p[0] + nx * ww, p[1] + ny * ww))
        right.append((p[0] - nx * ww, p[1] - ny * ww))
    left[-1] = left[-1] + (True,)
    return "\n".join([path(smooth(left + right[::-1][1:]), fill, INK, 1.4), line([pts[0][:2], pts[1][:2]], lt, 0.8)])


def head(g, o, c, cap=None, ear="small", nose=1.0, tendrils="droop", face=True):
    """The gaunt head about cranium centre ``c``: a hooked nose, a sunken
    socket, moustache tendrils, an ear; ``cap`` is 'cap' (a leather cap with
    a flap), 'shroud' or None (bald). ``face`` adds the eye and the mouth
    (a rigged head has them as their own layers)."""
    hx, hy = c

    def Q(x, y, corner=False):
        return (hx + x, hy + y, True) if corner else (hx + x, hy + y)

    if cap == "shroud":
        # the shroud's back drape, behind the skull
        drape = smooth([Q(-6, -26), Q(-24, -18), Q(-32, 4), Q(-36, 30), Q(-30, 50, True), Q(-18, 40), Q(-8, 46, True), Q(-2, 26), Q(4, 10)])
        g.add(drape, **cloth(o, "shroud"), extra=[line([Q(-28, 8), Q(-26, 40)], o["shroud_sh"], 1.2)])
    skull = smooth([Q(-20, 10), Q(-22, -6), Q(-14, -20), Q(0, -26), Q(16, -24), Q(25, -13), Q(27, 0), Q(25, 10), Q(23, 22), Q(17, 30),
                    Q(6, 32), Q(-6, 27), Q(-14, 20)])
    sk = skin(o)
    g.add(skull, **sk, extra=[path(smooth([Q(6, 10), Q(16, 8), Q(18, 20), Q(10, 24), Q(4, 18)]), o["skin_sh"]),
                              ellipse(hx + 16, hy - 2, 7.5, 5.5, o["socket"]), line([Q(6, 26), Q(-6, 22)], o["skin_sh"], 1.2)])
    if ear == "big":
        e = smooth([Q(-2, -4), Q(-16, -16), Q(-30, -22, True), Q(-20, -6), Q(-12, 8), Q(-2, 8)])
    else:
        e = smooth([Q(-2, -4), Q(-12, -10), Q(-18, -12, True), Q(-14, 2), Q(-6, 8), Q(0, 6)])
    if cap != "shroud":
        g.add(e, **sk, extra=[line([Q(-6, -2), Q(-12, -6)], o["skin_dk"], 1.2)])
    if face:
        g.post += eye(o, c, "open") + mouth(o, c, "shut")
    k = nose
    nz = smooth([Q(22, -6), Q(30, -2), Q(38 * k, 6), Q(42 * k + 2, 16), Q(40 * k + 2, 25, True), Q(34 * k + 1, 20), Q(28, 16), Q(24, 12)])
    g.add(nz, **sk, extra=[ellipse(hx + 31 * k, hy + 15, 2.0, 1.2, o["skin_dk"])])
    if tendrils == "barbel":
        runs, wid = [((26, 17), (36, 24), (42, 36), (40, 48), (44, 58)), ((22, 18), (26, 30), (22, 42), (24, 54))], 2.2
    elif tendrils == "long":
        runs, wid = [((26, 17), (32, 28), (30, 40), (34, 52), (30, 62)), ((22, 18), (22, 30), (16, 40), (18, 50)),
                     ((24, 18), (28, 32), (24, 46), (26, 56))], 1.5
    else:
        runs, wid = [((26, 17), (34, 24), (32, 36), (36, 46), (32, 56)), ((22, 18), (22, 30), (16, 38), (18, 48))], 1.9
    for run in runs:
        g.post.append(_tendril([Q(*p) for p in run], wid, o["stache"], o["stache_lt"]))
    if cap == "cap":
        flap = smooth([Q(-10, -24), Q(-28, -26), Q(-44, -34), Q(-52, -30, True), Q(-40, -16), Q(-22, -6), Q(-10, -8)])
        g.add(flap, **cloth(o, "cap"), extra=[line([Q(-20, -14), Q(-44, -28)], o["cap_sh"], 1.2)])
        c2 = smooth([Q(-22, -2), Q(-22, -16), Q(-12, -28), Q(4, -33), Q(20, -29), Q(30, -18), Q(32, -12, True), Q(18, -12), Q(2, -14), Q(-14, -6)])
        g.add(c2, **cloth(o, "cap"), extra=[line([Q(-20, -8), Q(30, -14)], o["cap_sh"], 2.0), line([Q(2, -30), Q(4, -16)], o["cap_sh"], 1.1),
                                           ellipse(hx - 6, hy - 18, 1.6, 1.6, o["cap_sh"])])
    elif cap == "shroud":
        hood = smooth([Q(-24, 8), Q(-26, -10), Q(-16, -26), Q(2, -33), Q(20, -30), Q(30, -18), Q(30, -10, True), Q(18, -12), Q(4, -10),
                       Q(-6, -2), Q(-8, 14), Q(-4, 30), Q(-14, 30)])
        g.add(hood, **cloth(o, "shroud"), extra=[line([Q(-16, -18), Q(24, -16)], o["shroud_sh"], 1.2),
                                                line([Q(-20, -4), Q(10, -12)], o["shroud_sh"], 1.1), line([Q(-6, 2), Q(-6, 26)], o["shroud_sh"], 1.1)])
    else:
        g.post += [line([Q(-14, -14), Q(-6, -22)], o["skin_dk"], 1.0), ellipse(hx + 2, hy - 18, 3, 2, o["skin_lt"])]


def eye(o, c, kind):
    """One eye, deep in its socket, under a heavy brow (the rig shows one at a time)."""
    hx, hy = c
    brow = line([(hx + 6, hy - 8), (hx + 16, hy - 10), (hx + 26, hy - 6)], o["skin_dk"], 2.0)
    if kind == "open":
        return [ellipse(hx + 17, hy - 1.5, 3.2, 2.4, o["eye"]), ellipse(hx + 17.6, hy - 1.5, 1.2, 1.2, o["pupil"]), brow]
    if kind == "shut":
        return [line([(hx + 13, hy - 1), (hx + 17, hy + 0.8), (hx + 21, hy - 1)], INK, 1.6),
                line([(hx + 6, hy - 6), (hx + 16, hy - 8), (hx + 26, hy - 4)], o["skin_dk"], 2.0)]
    k = 2.6
    return [line([(hx + 17 - k, hy - 1.5 - k), (hx + 17 + k, hy - 1.5 + k)], INK, 1.5),
            line([(hx + 17 - k, hy - 1.5 + k), (hx + 17 + k, hy - 1.5 - k)], INK, 1.5), brow]


def mouth(o, c, kind):
    """A thin grim line and two snaggle teeth, or wide open in a cackle."""
    hx, hy = c

    def Q(x, y, corner=False):
        return (hx + x, hy + y, True) if corner else (hx + x, hy + y)

    if kind == "shut":
        return [line([Q(24, 22), Q(16, 23), Q(9, 21)], INK, 1.6),
                path(smooth([Q(14, 22.6), Q(15.6, 27, True), Q(17, 22.6)]), o["tooth"], INK, 0.8),
                path(smooth([Q(19, 22.4), Q(20.4, 26, True), Q(21.6, 22.2)]), o["tooth"], INK, 0.8)]
    gape = smooth([Q(25, 20), Q(16, 20.5), Q(8, 19, True), Q(10, 27), Q(16, 33), Q(23, 31), Q(26, 25)])
    return [path(gape, o["maw"], INK, 1.5),
            path(smooth([Q(13, 20.8), Q(14.6, 25, True), Q(16, 20.8)]), o["tooth"], INK, 0.8),
            path(smooth([Q(19, 20.6), Q(20.4, 24.5, True), Q(21.6, 20.6)]), o["tooth"], INK, 0.8),
            path(smooth([Q(15, 31.5), Q(16.6, 27.5, True), Q(18, 31.8)]), o["tooth"], INK, 0.8)]


# ----------------------------------------------------------------- torsos

def torso(g, o, pts, ribs, spine, extra=()):
    items = [line(r, o["skin_dk"], 1.2) for r in ribs] + [ellipse(x, y, 2.2, 1.7, o["skin_dk"]) for x, y in spine] + list(extra)
    g.add(smooth(pts), base=o["skin"], light=o["skin_lt"], shade=o["skin_sh"], a=6, b=2.4, extra=items)


def loincloth(g, o, belt, sil, k="cloth"):
    g.add(sil, **cloth(o, k), extra=[line([(belt[0][0] + 20, belt[0][1] + 6), (belt[0][0] + 22, belt[0][1] + 34)], o[k + "_sh"], 1.1)])
    g.post += [line(belt, INK, 4.6), line(belt, o["rope"], 2.6)]


# --------------------------------------------------------------- looks

BASE = dict(tooth="#e9e2c6", pupil="#1a1410", nail="#2a2420", nail_lt="#4a423a", rope="#8a7048", maw="#2a1418")

LOOKS = {
    "capped": dict(BASE, label="A: today's ghoul redrawn, cap + flap", ink="#1a1c18",
                   skin="#a9b496", skin_lt="#c9d3b6", skin_sh="#828d71", skin_dk="#5f6853", far="#8b9679", far_sh="#6c765d",
                   socket="#4f5845", eye="#e8d66a", stache="#3b3a33", stache_lt="#5d5b50",
                   cap="#6e4a32", cap_lt="#8f6545", cap_sh="#4d3322", cloth="#7b6a52", cloth_lt="#998668", cloth_sh="#5a4c39"),
    "shroud": dict(BASE, label="B: stitched corpse in a burial shroud", ink="#171a20",
                   skin="#93a1ac", skin_lt="#b6c3cc", skin_sh="#6f7d89", skin_dk="#4f5b66", far="#76838f", far_sh="#5c6874",
                   socket="#3e4852", eye="#c8f2ee", pupil="#5fc9c0", stache="#d8d6cc", stache_lt="#f4f2ea",
                   shroud="#d9d2bd", shroud_lt="#efe9d6", shroud_sh="#aea58e", cloth="#d9d2bd", cloth_lt="#efe9d6", cloth_sh="#aea58e",
                   stitch="#2a2026", rope="#6c5a44", fx="#c8f2ee", fx_core="#ffffff"),
    "bog": dict(BASE, label="C: feral bog ghoul, low, one claw reaching", ink="#1b1a10",
                skin="#8c8656", skin_lt="#ada66f", skin_sh="#6a643d", skin_dk="#4c4729", far="#706b43", far_sh="#575233",
                socket="#3e3a22", eye="#f0b443", stache="#2f3a24", stache_lt="#4c5a3a",
                cowl="#8e3a2a", cowl_lt="#b0533a", cowl_sh="#66281d", cloth="#4f4636", cloth_lt="#685d48", cloth_sh="#382f24"),
}

#: Where each bone of look B turns (SVG units): ``bone: (parent, x, y)``, parents first.
JOINTS: Dict[str, Tuple[str, float, float]] = {
    "body": ("", 270.0, 356.0),
    "torso": ("body", 270.0, 356.0),
    "head": ("torso", 330.0, 266.0),
    "far_arm_u": ("torso", 286.0, 276.0),
    "far_arm_l": ("far_arm_u", 282.0, 340.0),
    "far_hand": ("far_arm_l", 294.0, 400.0),
    "near_arm_u": ("torso", 302.0, 280.0),
    "near_arm_l": ("near_arm_u", 314.0, 342.0),
    "near_hand": ("near_arm_l", 324.0, 402.0),
    "far_leg_u": ("body", 258.0, 360.0),
    "far_leg_l": ("far_leg_u", 278.0, 408.0),
    "far_foot": ("far_leg_l", 254.0, 456.0),
    "near_leg_u": ("body", 274.0, 362.0),
    "near_leg_l": ("near_leg_u", 302.0, 404.0),
    "near_foot": ("near_leg_l", 288.0, 456.0),
}
#: B's cranium centre.
HEAD_C = (346.0, 246.0)

GAUNT = [(322, 266), (304, 256), (282, 256), (264, 266), (252, 290), (248, 318), (250, 346), (262, 366), (282, 366), (294, 352), (298, 330),
         (306, 308), (318, 290), (332, 276)]


def P(name):
    return JOINTS[name][1], JOINTS[name][2]


def drawn(o) -> Dict[str, list]:
    """Look B's parts, keyed by layer group id."""
    G: Dict[str, Group] = {}

    def g(key):
        return G.setdefault(key, Group())

    for side, far in (("far", True), ("near", False)):
        arm(o, P(f"{side}_arm_u"), P(f"{side}_arm_l"), P(f"{side}_hand"), 80 if far else 82,
            (g(f"{side}-arm-upper"), g(f"{side}-arm-lower"), g(f"{side}-hand")), far=far, curl=30)
        leg(o, P(f"{side}_leg_u"), P(f"{side}_leg_l"), P(f"{side}_foot"), (g(f"{side}-thigh"), g(f"{side}-shin"), g(f"{side}-foot")), far=far)
    st = o["stitch"]
    stitches = [line([(268, 278), (282, 298), (296, 316), (300, 336)], st, 1.3)]
    for t in range(5):
        x, y = 271 + t * 7.2, 283 + t * 11
        stitches.append(line([(x - 3, y + 3), (x + 3, y - 3)], st, 1.2))
    torso(g("torso"), o, GAUNT, ribs=[[(292, 298), (306, 304)], [(288, 310), (302, 317)]], spine=[(274, 264), (260, 280)], extra=stitches)
    g("torso").add(capsule((316, 276), (336, 260), 8.0, 7.0), **skin(o))  # the neck, thrust forward
    # the shroud's wrap at the hips, its end hanging behind, and the loincloth over it
    g("loincloth").add(smooth([(254, 352), (244, 380), (236, 414, True), (248, 406), (252, 420, True), (260, 386), (266, 356)]), **cloth(o))
    loincloth(g("loincloth"), o, [(248, 352), (276, 350), (300, 346)],
              smooth([(248, 348), (300, 342), (304, 368), (296, 384, True), (284, 378), (274, 392, True), (264, 380), (254, 392, True), (246, 376)]))
    head(g("head"), o, HEAD_C, cap="shroud", tendrils="long", face=False)
    # a stitched seam round the near shoulder
    g("near-arm-upper").post += [line([(296, 294), (302, 298), (312, 296)], st, 1.3)] + \
        [line([(296 + k * 5, 291 + k * 1.6), (298 + k * 5, 300 + k * 0.8)], st, 1.1) for k in range(3)]
    out = {k: v.items() for k, v in G.items()}
    for kind in ("open", "shut", "dead"):
        out[f"eye-{kind}"] = eye(o, HEAD_C, kind)
    for kind in ("shut", "open"):
        out[f"mouth-{kind}"] = mouth(o, HEAD_C, kind)
    out["fx-claw"] = claw_fx(o)
    return out


def claw_fx(o):
    """The rake of its claw (``fx_claw``): three gouges trailing the near
    hand's sweep, on the side it came from (behind the hand as it rakes
    forward and up), nothing ahead of the nails."""
    wx, wy = P("near_hand")
    out = []
    for k in range(3):
        off = (k - 1) * 7.0
        a = (wx - 34 + off * 0.4, wy + 8 + off)
        m = (wx - 14 + off * 0.2, wy + 22 + off)
        b = (wx + 6, wy + 26 + off * 0.8)
        out += [line([a, m, b], o["fx"], 3.4 - k * 0.6), line([a, m, b], o["fx_core"], 1.0)]
    return out


#: The parts, in the order they are drawn: (group id, label, part, bone, z, opacity channel).
LAYERS = [
    ("far-arm-upper", "Far Arm - Upper", "far_arm_u", "far_arm_u", 4, ""),
    ("far-arm-lower", "Far Arm - Lower", "far_arm_l", "far_arm_l", 5, ""),
    ("far-hand", "Far Hand", "far_hand", "far_hand", 6, ""),
    ("far-thigh", "Far Thigh", "far_leg_u", "far_leg_u", 8, ""),
    ("far-shin", "Far Shin", "far_leg_l", "far_leg_l", 9, ""),
    ("far-foot", "Far Foot", "far_foot", "far_foot", 10, ""),
    ("torso", "Torso", "torso", "torso", 14, ""),
    ("near-thigh", "Near Thigh", "near_leg_u", "near_leg_u", 16, ""),
    ("near-shin", "Near Shin", "near_leg_l", "near_leg_l", 17, ""),
    ("near-foot", "Near Foot", "near_foot", "near_foot", 18, ""),
    ("loincloth", "Shroud Wrap and Loincloth", "loincloth", "body", 20, ""),
    ("head", "Head", "head", "head", 26, ""),
    ("eye-open", "Eye - Open", "eye_open", "head", 27, "eye_open"),
    ("eye-shut", "Eye - Shut", "eye_shut", "head", 27, "eye_shut"),
    ("eye-dead", "Eye - Dead", "eye_dead", "head", 27, "eye_dead"),
    ("mouth-shut", "Mouth - Shut", "mouth_shut", "head", 27, "mouth_shut"),
    ("mouth-open", "Mouth - Open", "mouth_open", "head", 27, "mouth_open"),
    ("near-arm-upper", "Near Arm - Upper", "near_arm_u", "near_arm_u", 30, ""),
    ("near-arm-lower", "Near Arm - Lower", "near_arm_l", "near_arm_l", 31, ""),
    ("near-hand", "Near Hand", "near_hand", "near_hand", 32, ""),
    ("fx-claw", "FX - Claw", "fx_claw", "near_hand", 33, "fx_claw"),
]
#: Layers shown when no row says otherwise.
DEFAULT_ON = ("eye_open", "mouth_shut")


# ------------------------------------------------ the kept looks, whole

def draw_capped(o):
    """A, KEPT, NOT CAST: the old ghoul redrawn, its leather cap and flap."""
    back, body, front = Group(), Group(), Group()
    arm(o, (288, 278), (290, 334), (326, 366), 50, (back, back, back), far=True, curl=30)
    leg(o, (258, 360), (278, 408), (254, 456), (back, back, back), far=True)
    torso(body, o, GAUNT, ribs=[[(292, 292), (308, 298)], [(288, 304), (304, 311)], [(286, 316), (300, 322)]],
          spine=[(276, 264), (262, 278), (254, 298)], extra=[path(smooth([(292, 332), (298, 324), (294, 352), (286, 356)]), o["skin_sh"])])
    body.add(capsule((316, 276), (338, 260), 8.0, 7.0), **skin(o))
    leg(o, (274, 362), (304, 404), (288, 456), (body, body, body))
    loincloth(body, o, [(248, 352), (276, 350), (300, 346)],
              smooth([(248, 348), (300, 342), (304, 368), (300, 396, True), (292, 386), (284, 400, True), (274, 388), (262, 398, True),
                      (254, 386), (248, 394, True), (246, 368)]))
    head(body, o, (348, 246), cap="cap")
    arm(o, (302, 280), (318, 332), (346, 350), 30, (front, front, front), curl=34)
    return [back, body, front]


def draw_bog(o):
    """C, KEPT, NOT CAST: a feral bog ghoul nearly on all fours, one claw raised."""
    back, body, front = Group(), Group(), Group()
    arm(o, (294, 320), (304, 382), (316, 440), 74, (back, back, back), far=True, curl=40)
    leg(o, (246, 362), (276, 398), (246, 456), (back, back, back), far=True)
    torso(body, o, [(322, 302), (298, 292), (272, 290), (250, 298), (236, 318), (234, 344), (244, 364), (264, 368), (282, 358), (296, 344),
                    (312, 330), (326, 318), (336, 312)],
          ribs=[[(284, 326), (298, 334)], [(278, 338), (292, 346)], [(272, 350), (284, 356)]],
          spine=[(284, 292), (268, 292), (254, 298), (242, 312)])
    body.add(capsule((318, 314), (338, 300), 8.0, 7.0), **skin(o))
    leg(o, (260, 364), (296, 396), (270, 456), (body, body, body))
    loincloth(body, o, [(236, 350), (258, 358), (282, 356)],
              smooth([(234, 346), (282, 352), (286, 378), (278, 392, True), (268, 382), (256, 394, True), (246, 380), (236, 390, True), (232, 366)]))
    head(body, o, (352, 300), cap=None, ear="big", nose=1.05, tendrils="barbel")
    cowl = smooth([(334, 296), (318, 286), (296, 280), (276, 284), (262, 296), (258, 312, True), (270, 306), (276, 322, True), (288, 310),
                   (298, 326, True), (308, 312), (322, 320, True), (330, 310), (340, 312)])
    front.add(cowl, **cloth(o, "cowl"), extra=[line([(290, 286), (302, 312)], o["cowl_sh"], 1.2), line([(272, 292), (280, 316)], o["cowl_sh"], 1.1)])
    arm(o, (308, 320), (330, 372), (372, 384), 12, (front, front, front), curl=30)
    return [back, body, front]


KEPT = {"capped": draw_capped, "bog": draw_bog}


def svg_text(look: str = LOOK) -> str:
    o = LOOKS[look]
    set_ink(o["ink"])
    _CID[0] = 0
    if look in KEPT:
        groups = KEPT[look](o)
        svg.PARTS.clear()
        for i, g in enumerate(groups):
            svg.part(f"{look}-{i}", f"Whole drawing {i}", f"layer_{i}", "body", 10 * (i + 1), g.items())
        return svg.document(
            size=(W, H), design=f"ghoul-skulker-{look}", layer_id="ghoul-skulker", label=VIEW,
            comment=[f"  <!-- KEPT, NOT CAST: a ghoul look Jon kept (2026-10-18), {o['label']}; drawn whole, not rigged. -->"],
            joints=[])
    parts = drawn(o)
    svg.PARTS.clear()
    for group, label, name, bone, z, channel in LAYERS:
        extra = (f' data-rig-opacity="{channel}"' + (' data-rig-default="1"' if channel in DEFAULT_ON else "")) if channel else ""
        svg.part(group, label, name, bone, z, parts[group], extra)
    return svg.document(
        size=(W, H), design=f"ghoul-skulker-{look}", layer_id="ghoul-skulker", label=VIEW,
        comment=["  <!-- the Ghoul Skulker's look (Jon chose B, 2026-10-18): side view facing right, the ground at y=470.",
                 "       Drawn by scripts/svg_art/ghoul_skulker_art.py; each part turns about its JOINTS entry. -->"],
        joints=svg.joints_layer({k: (v[1], v[2]) for k, v in JOINTS.items()}),
    )


def main() -> None:
    if len(sys.argv) > 2 and sys.argv[1] == "--all":
        out = Path(sys.argv[2])
        out.mkdir(parents=True, exist_ok=True)
        for look in LOOKS:
            (out / f"ghoul_skulker_{look}.svg").write_text(svg_text(look), encoding="utf8")
            print(out / f"ghoul_skulker_{look}.svg")
        return
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".svg.tmp")
    tmp.write_text(svg_text(), encoding="utf8")
    tmp.replace(OUT)
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
