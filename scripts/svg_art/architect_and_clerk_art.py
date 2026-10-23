#!/usr/bin/env python3
"""The Architect and the Manifest Clerk, redesign candidates (round 1).

    uv run python scripts/svg_art/architect_and_clerk_art.py --all DIR     # side + front SVG of every look, to DIR
    uv run python scripts/svg_art/architect_and_clerk_art.py --sheets DIR  # the SVGs, and the contact sheets Jon reviews

CANDIDATES, NOT CAST: nothing registers these drawings.  ``npc_architect`` still
draws from ``sprites/architect_spritesheet`` (the old purple toon), and
``npc_manifest_clerk`` borrows that same sheet (its catalog tag
``placeholder_sprite``).  Jon asked (2026-10-22) for redesigned art for both;
this round offers three looks of each.

WHO THEY ARE (the catalog rows and their dialogue):

* THE ARCHITECT (``npc_architect``, 173 cm, tags hub + guide) built the rooms:
  "Do not lean there. I spent three days getting that joint square."  Bridges,
  stairs, roofs; in the Kernel's basement they test movement and combat with the
  debug boxes on.  Barks: "Careful! I'm load-bearing.", "Measure twice. Resent
  the carpenter once."  A precise, fussy maker -- so every look carries a
  maker's instrument: the roll of drawings, the steel square, the dividers.
* THE MANIFEST CLERK (``npc_manifest_clerk``) keeps the list at the manifest
  kiosk of the intro, the night the lab was raided ("Your basement is marked
  small. Somebody attached the wrong sheet."), and in the Hall: "If you're not
  on the manifest, you're a discrepancy."  A functionary of the institution
  that sent the salvage crew, not a maker: paper, stamps, rules.  Each look is
  a different body and palette from every architect, so the two never read as
  one person in two coats.

HOUSE STYLE (the Oiler's, the Statesman's): a thick warm ink outline, flat
fills, one shade band down-left and one light band up-right, adult
proportions, small eyes.  No cast shadow under anybody.  Side view faces right
(the near side is the figure's right); the front view has the figure's right on
screen-left.  Each look draws on the same joints, scaled about the ground by
its ``k`` (its height against the Architect's 173 cm).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Callable, Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import svgkit as svg  # noqa: E402
from svgkit import capsule, ellipse, line, path, smooth  # noqa: E402

W = H = 560
INK = "#1d1714"
OW = 1.5
GROUND_Y = 502.0
#: Shade down-left, light up-right.
SD, LD = (-1.0, 0.6), (1.0, -0.8)
WHITE = "#f6f2ea"
PUPIL = "#16120f"

O: Dict = {}
_N = [0]


# ============================================================================================
# THE LOOKS
# ============================================================================================

SKIN = {
    "fair": dict(skin="#ecc6a6", skin_sh="#cc9f82", skin_lt="#f6dcc6", skin_dk="#a06f58", lip="#bf7e70"),
    "ruddy": dict(skin="#efc2a6", skin_sh="#d39a80", skin_lt="#f8d9c6", skin_dk="#a86a58", lip="#c27464", blush="#e9a48e"),
    "olive": dict(skin="#d2a47c", skin_sh="#b0805c", skin_lt="#e2bc9a", skin_dk="#835a3e", lip="#a86a58"),
    "brown": dict(skin="#9c6748", skin_sh="#7b4b32", skin_lt="#b4805e", skin_dk="#5a3422", lip="#7a4434"),
    "pale": dict(skin="#ead0bd", skin_sh="#c9ab98", skin_lt="#f6e4d8", skin_dk="#9e7d6c", lip="#b98a80"),
}

LOOKS: Dict[str, Dict[str, Dict]] = {
    "architect": {
        "A": dict(
            label="A: modernist - round glasses, violet bow tie, the roll of drawings",
            k=1.02, skin_tone="fair", iris="#4a3a2e",
            face=dict(nose=(12.5, 17.5), hump=1.2, chin=1.5, jaw=0.0, brow=0.0, lines=1),
            ffront=dict(fw=0.92, jaw=0.86),
            hair="slick", hair_c="#3a3634", hair_c_lt="#5a5552", temple="#8a8682",
            glasses="round", ear_pencil=True,
            jacket=dict(hem=384, color="#34363e", lapel=True, buttons=2), shirt="#ece8df",
            neck="bowtie", tie="#5b3f8c", tie_lt="#7d61b0",
            trouser="#2f3137", shoe="oxford", shoe_c="#1c1a1b",
            sleeve="jacket", build=dict(chest=0.0, belly=0.0, back=1.0),
            prop="roll", roll="#3e6dab", roll_lt="#6d98cf", roll_sh="#2a4c7c",
        ),
        "B": dict(
            label="B: master builder - steel square, tool belt, sleeves rolled",
            k=0.97, skin_tone="olive", iris="#3a2a20", female=True,
            face=dict(nose=(10.5, 16.5), hump=0.6, chin=0.5, jaw=-1.0, brow=-0.5, lines=1),
            ffront=dict(fw=0.92, jaw=0.84),
            hair="knot", hair_c="#3b302c", hair_c_lt="#5a4a44", streak="#a49a94", pencil_knot=True,
            vest=dict(color="#3d3a6b", hem=350), shirt="#ddd3be",
            neck="open",
            trouser="#a5895c", shoe="boot", shoe_c="#4a3224",
            sleeve="rolled", build=dict(chest=3.0, belly=0.0, back=0.0, shoulder=1.04),
            belt="tools", prop="square",
        ),
        "C": dict(
            label="C: site engineer - hard hat, hi-vis vest, brass dividers for a cane",
            k=1.0, skin_tone="ruddy", iris="#4f6a80",
            face=dict(nose=(10.5, 18.0), bulb=1.6, chin=0.0, jaw=1.5, brow=0.5, lines=2),
            ffront=dict(fw=1.0, jaw=1.0),
            hair="hat_white", hair_c="#d8d5ce", hair_c_lt="#f2f0eb", beard=True,
            hat="hardhat", hat_c="#f1ede4",
            vest=dict(color="#ec7a2c", hem=356, hivis=True), shirt="#a8c2dc",
            neck="tie", tie="#2b3a5a", tie_lt="#41557e",
            trouser="#9b8e6b", shoe="boot", shoe_c="#7a5634",
            sleeve="shirt", build=dict(chest=2.0, belly=7.0, back=0.0, shoulder=1.04),
            prop="dividers",
        ),
    },
    "manifest_clerk": {
        "A": dict(
            label="A: freight-office clerk - green eyeshade, sleeve garters, the clipboard",
            k=0.93, skin_tone="pale", iris="#5a4a3a",
            face=dict(nose=(9.5, 18.0), bulb=1.0, chin=-1.5, jaw=2.5, brow=0.0, lines=1, double_chin=True),
            ffront=dict(fw=1.06, jaw=1.06),
            hair="fringe", hair_c="#7b6a5a", hair_c_lt="#9a8a7a", moustache="#6a5848",
            hat="eyeshade", glasses="specs",
            vest=dict(color="#5b4433", hem=352, pointed=True, watch=True), shirt="#efeadf",
            neck="tie", tie="#7a2a2a", tie_lt="#9a4040",
            trouser="#55575e", shoe="oxford", shoe_c="#4a3226",
            sleeve="garter", build=dict(chest=1.0, belly=16.0, back=1.0, shoulder=0.98),
            prop="clipboard", ear_pencil=True,
        ),
        "B": dict(
            label="B: salvage quartermaster - field cap, armband, the rubber stamp",
            k=0.96, skin_tone="brown", iris="#2a1c14", female=True,
            face=dict(nose=(9.0, 16.5), hump=0.0, chin=1.0, jaw=-1.0, brow=-0.5, lines=0),
            ffront=dict(fw=0.92, jaw=0.88),
            hair="bun_cap", hair_c="#1e1918", hair_c_lt="#3a3230",
            hat="fieldcap", hat_c="#5a6658",
            jacket=dict(hem=372, color="#5a6658", lapel=False, buttons=0, uniform=True), shirt="#d8d4c4",
            neck="collar",
            trouser="#4c5649", shoe="boot", shoe_c="#1f1c1c",
            sleeve="jacket", armband="#d9822b", build=dict(chest=2.5, belly=0.0, back=0.0),
            belt="plain", prop="stamp", badge=True,
        ),
        "C": dict(
            label="C: registrar - half-moon glasses, oversleeves, the fanfold manifest",
            k=1.05, skin_tone="pale", iris="#6a7a86",
            face=dict(nose=(13.5, 20.0), hump=2.2, chin=2.0, jaw=-2.5, brow=0.5, lines=2, gaunt=True),
            ffront=dict(fw=0.84, jaw=0.78),
            hair="combed", hair_c="#a7a39c", hair_c_lt="#c6c2bb",
            glasses="halfmoon",
            cardigan=dict(color="#7a6f5c", hem=398), shirt="#e7e3d8",
            neck="tie", tie="#3b4a3e", tie_lt="#55695a",
            trouser="#3c3a40", shoe="oxford", shoe_c="#26201e",
            sleeve="oversleeve", stoop=True, build=dict(chest=-2.0, belly=0.0, back=4.0, shoulder=0.94),
            prop="fanfold",
        ),
    },
}

PROP_COLORS = dict(
    steel="#b4bac2", steel_sh="#7e868f", steel_lt="#dde1e6",
    brass="#c9a24a", brass_sh="#94722a", brass_lt="#e6c870",
    leather="#7a4f2e", leather_sh="#55341c", leather_lt="#9a6a44",
    rule="#e2c25a", rule_sh="#b0912e",
    paper="#f2efe6", paper_sh="#cfcabd", paper_lt="#fdfcf8",
    board="#b98b57", board_sh="#8e6538", board_lt="#d2a874",
    wood="#8a5a35", wood_sh="#62401f", wood_lt="#a8764c",
    rubber="#2a2424", ink_red="#b8322c",
    green_bar="#cfe3c6", pencil="#e6b83a", pencil_sh="#b88a1e",
    hivis_band="#d9dee3", lanyard="#b8322c",
)


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


def use(char: str, look: str) -> None:
    O.clear()
    O.update(PROP_COLORS)
    L = LOOKS[char][look]
    O.update(SKIN[L["skin_tone"]])
    O.update(L)
    O["char"], O["look"] = char, look
    O.setdefault("blush", None)
    O.setdefault("build", {})
    for k, v in dict(chest=0.0, belly=0.0, back=0.0, shoulder=1.0).items():
        O["build"].setdefault(k, v)
    # the garments' base colours, each with its shade and light
    for key, base in (("shirt", O.get("shirt")), ("trouser", O.get("trouser")), ("shoec", O.get("shoe_c")),
                      ("hr", O.get("hair_c")), ("tie", O.get("tie")), ("ht", O.get("hat_c")),
                      ("jk", (O.get("jacket") or {}).get("color")), ("roll", O.get("roll")),
                      ("armband", O.get("armband")), ("moustache", O.get("moustache"))):
        if base:
            O[key] = base
            O.setdefault(key + "_sh", tone(base, 0.74))
            O.setdefault(key + "_lt", tone(base, 1.2))
    if O.get("cardigan"):
        c = O["cardigan"]["color"]
        O["card"], O["card_sh"], O["card_lt"] = c, tone(c, 0.74), tone(c, 1.18)
    if O.get("vest"):
        c = O["vest"]["color"]
        O["vestc"], O["vestc_sh"], O["vestc_lt"] = c, tone(c, 0.72), tone(c, 1.2)
    if O.get("hair_c_lt"):
        O["hr_lt"] = O["hair_c_lt"]


# ============================================================================================
# THE HOUSE CEL SHADING (after oiler_art.py)
# ============================================================================================

def uid(tag="c"):
    _N[0] += 1
    return f"ac{tag}{_N[0]}"


def cel(d, base, shade, light=None, items=(), sdir=SD, ldir=LD, s=5.0, l=3.0, sw=None, ink=None, edges=None):
    """A shape: its fill, a ``shade`` band along the edges facing ``sdir`` and a
    ``light`` band along those facing ``ldir`` (clipped inside), the detail
    ``items``, then the ink outline -- or, given ``edges`` (open runs of
    points), ink on those runs only."""
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
    return cel(d, O[key + "_sh"], tone(O[key + "_sh"], 0.8), None, items, s=1.5, **kw)


def frame(origin, u_ang):
    ux, uy = math.cos(u_ang), math.sin(u_ang)
    nx, ny = -uy, ux
    return lambda t, s: (origin[0] + ux * t + nx * s, origin[1] + uy * t + ny * s)


def ang(a, b):
    return math.atan2(b[1] - a[1], b[0] - a[0])


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def mx(pts, cx=280.0):
    """Mirror points across ``x = cx`` (the front view's left half from its right)."""
    return [(2 * cx - p[0], p[1]) + tuple(p[2:]) for p in pts]


def rect(x0, y0, x1, y1):
    return smooth([(x0, y0, True), (x1, y0, True), (x1, y1, True), (x0, y1, True)])


def quad(pts):
    return smooth([tuple(p[:2]) + (True,) for p in pts])


# ============================================================================================
# HANDS (after oiler_art.py: tapered fingers, the back of the hand inked where it is free)
# ============================================================================================

HAND = 1.15


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


def skin_keys(near=True):
    if near:
        return O["skin"], O["skin_sh"], O["skin_lt"], O["skin_dk"]
    return O["skin_sh"], O["skin_dk"], None, O["skin_dk"]


def hand_side(wrist, a, near=True):
    """A relaxed hand hanging from ``wrist`` along ``a``, seen from its back,
    the fingers curling a little forward (toward +x)."""
    q = frame(wrist, a)
    p = lambda t, f: q(HAND * t, -HAND * f)
    sk, sh, lt, dk = skin_keys(near)
    fine = 1.3
    out = []
    thumb = finger(p(4, 5.0), p(11, 8.6), p(16.5, 9.6), 3.4 * HAND, 2.8 * HAND, 2.2 * HAND)
    out += cel(thumb, sk, sh, lt, [line([p(14.6, 8.0), p(15.4, 10.8)], dk, 0.7)], s=1.6, sw=fine)
    for f0, length, curl in ((-5.0, 12.5, 2.0), (-1.7, 15.0, 2.8), (1.6, 16.0, 3.4), (4.8, 14.5, 3.6)):
        fing = finger(p(10, f0), p(10 + length * 0.55, f0 + curl * 0.3), p(10 + length, f0 + curl), 2.1 * HAND, 1.95 * HAND, 1.7 * HAND)
        out += cel(fing, sk, sh, lt if f0 > 4 else None, [], s=1.0, sw=fine)
    run = [p(-1, -6.8), p(6, -7.4), p(11, -7.0), p(13.5, -3), p(14, 2), p(13, 6.6), p(7, 7.2), p(-1, 6.8)]
    palm = smooth([p(-3, -6.6)] + run + [p(-3, 6.6)])
    items = [line([p(4, -2.5), p(9.5, -3.2)], sh, 0.8), line([p(4, 1.5), p(9.5, 1.5)], sh, 0.8)]
    out += cel(palm, sk, sh, lt, items, s=2.5, edges=[run])
    return out


def hand_front(wrist, a, inward):
    """A relaxed hand hanging at the side, seen from the front: the palm to the
    thigh, the index curling in, the thumb down the front."""
    q = frame(wrist, a)
    p = lambda t, i: q(HAND * t, -HAND * i * inward)
    sk, sh, lt, dk = skin_keys()
    fine = 1.3
    out = []
    for i0, length, curl in ((3.2, 13.0, 3.0), (1.4, 14.5, 3.4)):
        out += cel(finger(p(9, i0), p(9 + length * 0.6, i0 + curl * 0.4), p(9 + length, i0 + curl), 2.1 * HAND, 2.0 * HAND, 1.7 * HAND),
                   sh, dk, None, [], s=1.0, sw=fine)
    run = [p(-1, -5.4), p(7, -6.0), p(12, -5.0), p(13.5, 0), p(12.5, 5.0), p(6, 5.6), p(-1, 5.4)]
    out += cel(smooth([p(-3, -5.2)] + run + [p(-3, 5.2)]), sk, sh, lt, [], s=2.0, edges=[run])
    idx = finger(p(10, -1.0), p(18.5, 0.6), p(24, 4.0), 2.4 * HAND, 2.2 * HAND, 1.9 * HAND)
    out += cel(idx, sk, sh, lt, [], s=1.2, sw=fine)
    thumb = finger(p(3, -4.4), p(11, -6.0), p(17.5, -4.2), 3.0 * HAND, 2.6 * HAND, 2.1 * HAND)
    out += cel(thumb, sk, sh, lt, [line([p(15.2, -6.2), p(15.8, -2.6)], dk, 0.7)], s=1.6, sw=fine)
    return out


def fist(c, a, thumb_side=1.0, near=True, k=1.0):
    """A hand closed round something at ``c``: ``a`` is the direction the
    knuckles run (along the held bar's grip), the back of the hand toward the
    camera; four knuckle bumps along the top, the thumb wrapped across."""
    q = frame(c, a)
    s = HAND * k
    p = lambda t, n: q(s * t, s * n)
    sk, sh, lt, dk = skin_keys(near)
    back = [p(-8, -6.5), p(-3, -8.2), p(3, -8.4), p(8, -7.2), p(9.5, -2), p(9.2, 4), p(6, 7.6), p(-2, 8.2), p(-7.6, 6.4), p(-9.4, 0)]
    items = [line([p(t, -7.6), p(t + 0.4, -3.4)], sh, 0.9) for t in (-3.6, 0.4, 4.4)]
    items.append(line([p(-6.5, 2.5), p(4, 3.0)], sh, 0.9))
    out = cel(smooth(back), sk, sh, lt, items, s=2.2, sw=1.6)
    thumb = finger(p(-6, 3.0 * thumb_side), p(-0.5, 5.2 * thumb_side), p(5.0, 4.6 * thumb_side), 3.0 * s, 2.6 * s, 2.1 * s)
    out += cel(thumb, sk, sh, lt, [line([p(3.6, 3.2 * thumb_side), p(4.0, 6.0 * thumb_side)], dk, 0.7)], s=1.4, sw=1.3)
    return out


# ============================================================================================
# SIDE VIEW (facing right; the figure's right side toward the camera)
# ============================================================================================

S_EYE = (296.0, 201.5)
S_LEGS = {"near": ((276, 352), (281, 418), (279, 484)), "far": ((262, 352), (262, 418), (255, 484))}
S_SHOULDER = {"near": (269.0, 268.0), "far": (259.0, 268.0)}

#: The near arm, by the prop it holds: (elbow, wrist, hand).
S_NEAR_ARM = {
    "roll": ((266, 316), (296, 318), "fist_roll"),
    "square": ((266, 316), (279, 358), "fist_down"),
    "dividers": ((268, 316), (304, 334), "fist_knob"),
    "clipboard": ((264, 316), (298, 300), "fist_board"),
    "stamp": ((266, 316), (294, 298), "fist_stamp"),
    "fanfold": ((266, 314), (304, 298), "fist_paper"),
}
S_FAR_ARM = ((256, 316), (264, 356))


def head_shift():
    """The stooped look carries the head and neck forward and down."""
    return (6.0, 5.0) if O.get("stoop") else (0.0, 0.0)


def s_torso_pts(grow=0.0, hem=352.0, flare=0.0, top_cut=0.0):
    """The trunk in profile from the neck to ``hem``: chest, belly and the
    curve of the back from the look's build; ``grow`` widens it all round
    (a garment over another), ``flare`` opens the skirt of a coat."""
    b = O["build"]
    ch, be, bk = b["chest"], b["belly"], b["back"]
    g = grow
    front = [(286 + g * 0.3, 244 - g + top_cut), (295 + ch * 0.3 + g, 258), (300 + ch + g, 279), (299 + ch * 0.5 + be * 0.35 + g, 298),
             (296 + be + g, 318), (295 + be * 0.8 + g, 336)]
    if hem > 356:
        front += [(294 + be * 0.35 + g + flare * 0.5, 352), (294 + g + flare, hem, True)]
        back = [(248 - g - flare, hem, True), (248 - g - flare * 0.4, 352)]
    else:
        front += [(294 + be * 0.3 + g, hem, True)]
        back = [(249 - g, hem, True)]
    back += [(247 - g, 330), (246 - g - bk * 0.4, 306), (247 - g - bk, 282), (251 - g - bk * 0.9, 262), (262 - g - bk * 0.4, 248 + top_cut)]
    return front + back


def s_shirt():
    """The shirt over the whole trunk: what shows of it is at the collar, the
    open front of a waistcoat, and under a vest."""
    out = C(smooth(s_torso_pts(0.0, 352)), "shirt", [line([(292, 270), (293, 340)], O["shirt_sh"], 1.0)], s=5)
    return out


def s_seat():
    """The seat of the trousers over the tops of the thighs: inked along the
    buttock behind and the front of the hip, open where the legs join it."""
    be = O["build"]["belly"]
    back = [(250, 334), (247, 352), (249, 368), (258, 376)]
    front = [(292 + be * 0.4, 334), (294 + be * 0.3, 352), (294, 366)]
    d = smooth(back[::-1] + [(268, 378), (286, 374)] + front[::-1][:0] + [front[2], front[1], front[0]])
    return C(d, "trouser", [], s=4, edges=[back, front])


def leg_shape(hip, knee, ankle, wh, wk, wa):
    def nrm(a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1.0
        return -dy / L, dx / L
    n1, n2 = nrm(hip, knee), nrm(knee, ankle)
    nk = ((n1[0] + n2[0]) / 2, (n1[1] + n2[1]) / 2)
    A = [(hip[0] + n1[0] * wh, hip[1] + n1[1] * wh), (knee[0] + nk[0] * wk, knee[1] + nk[1] * wk), (ankle[0] + n2[0] * wa, ankle[1] + n2[1] * wa, True)]
    B = [(ankle[0] - n2[0] * wa, ankle[1] - n2[1] * wa, True), (knee[0] - nk[0] * wk, knee[1] - nk[1] * wk), (hip[0] - n1[0] * wh, hip[1] - n1[1] * wh)]
    top = [(hip[0], hip[1] - wh * 0.9)]
    return smooth(A + B + top)


def trouser_widths():
    wide = O.get("shoe") == "boot" and O["char"] == "architect"
    return (14.5, 11.5, 10.5) if wide else (13.0, 10.2, 8.8)


def s_leg(side):
    hip, knee, ankle = S_LEGS[side]
    wh, wk, wa = trouser_widths()
    hem = (ankle[0], ankle[1] - 3)
    d = leg_shape(hip, knee, hem, wh, wk, wa)
    items = [line([(knee[0] - 6, knee[1] - 2), (knee[0] - 2, knee[1] + 6)], O["trouser_sh"], 1.1)]
    if O.get("shoe") == "boot" and O["char"] == "architect":  # the canvas work trousers: a knee patch seam
        items.append(line([(knee[0] - 9, knee[1] - 10), (knee[0] + 9, knee[1] - 12)], O["trouser_sh"], 1.0))
    if side == "near":
        out = C(d, "trouser", items, s=4.5)
    else:
        out = far(d, "trouser")
    return out + s_shoe(ankle, side == "near")


def s_shoe(ankle, near=True):
    ax, ay = ankle
    g = GROUND_Y
    if O.get("shoe") == "boot":
        d = smooth([(ax - 9.5, ay - 8), (ax + 5, ay - 8), (ax + 7, ay + 2), (ax + 17, ay + 7), (ax + 23, ay + 12), (ax + 23.5, g, True),
                    (ax - 11, g, True), (ax - 11.5, ay + 4)])
        items = [line([(ax - 11, g - 4), (ax + 23.5, g - 4)], O["shoec_sh"], 1.6), line([(ax + 2, ay - 2), (ax + 7, ay + 4)], O["shoec_lt"], 1.0)]
    else:
        d = smooth([(ax - 9, ay - 1), (ax + 3, ay - 1), (ax + 9, ay + 5), (ax + 19, ay + 9), (ax + 23, ay + 13), (ax + 23, g, True),
                    (ax - 10, g, True), (ax - 10.5, ay + 6)])
        items = [line([(ax - 10, g - 3), (ax + 23, g - 3)], O["shoec_sh"], 1.4), line([(ax + 4, ay + 3), (ax + 9, ay + 8)], O["shoec_sh"], 0.9),
                 line([(ax + 12, ay + 9), (ax + 19, ay + 11.5)], O["shoec_lt"], 1.2)]
    if near:
        return C(d, "shoec", items, s=3.5)
    return cel(d, O["shoec_sh"], tone(O["shoec_sh"], 0.7), None, [], s=1.5)


# ---- the trunk's garments -----------------------------------------------------------------

def s_vest():
    v = O["vest"]
    O["vestc"], O["vestc_sh"], O["vestc_lt"] = v["color"], tone(v["color"], 0.72), tone(v["color"], 1.2)
    b = O["build"]
    hem = v["hem"]
    pts = s_torso_pts(1.5, hem)
    # the vest opens at the throat: its front edge starts below the collar
    pts[0] = (290, 262)
    pts[1] = (297 + b["chest"] * 0.5, 268)
    if v.get("pointed"):
        i = [k for k, p in enumerate(pts) if len(p) > 2][0]
        pts[i] = (pts[i][0] + 1, hem + 6, True)
    pts[-1] = (266 - b["back"] * 0.4, 252)
    items = [line([(270, 262), (276, 300), (282, hem - 4)], O["vestc_sh"], 1.1)]
    if v.get("hivis"):
        for y in (300, 326):
            items.append(path(quad([(236, y), (320, y + 1), (320, y + 7), (236, y + 6)]), O["hivis_band"]))
            items.append(line([(236, y + 3.2), (320, y + 4.2)], "#aeb6be", 0.8))
        items.append(line([(286, 300), (298, 300)], tone(O["vestc"], 0.6), 1.2))
    else:
        fx = [p for p in pts[:6]]
        for y in (284, 298, 312, 326)[: (3 if hem < 340 else 4)]:
            x = max(p[0] for p in fx if abs(p[1] - y) < 26) - 3.5
            items.append(ellipse(x, y, 1.8, 1.8, O["brass"], INK, 0.6))
    if v.get("watch"):  # the watch chain from a button to the pocket
        items += [line([(300, 312), (292, 318), (284, 316)], O["brass"], 1.4), line([(300, 312), (292, 318), (284, 316)], INK, 0.4)]
        items.append(path(quad([(280, 320), (290, 320), (290, 323), (280, 323)]), tone(O["vestc"], 0.6)))
    return C(smooth(pts), "vestc", items, s=5)


def s_jacket():
    j = O["jacket"]
    hem = j["hem"]
    pts = s_torso_pts(2.5, hem, flare=3.0)
    items = [line([(258, 270), (256, 310), (256, hem - 6)], O["jk_sh"], 1.2)]
    be = O["build"]["belly"]
    if j.get("lapel"):
        # open at the front from the collar to the top button: the shirt and the
        # bow tie show in front of the lapel's edge
        pts[0] = (280, 249)
        pts[1] = (288.5, 268)
        pts[2] = (296, 290)
        lap = smooth([(280, 249), (288.5, 268), (296, 290), (300.5, 306), (295, 304), (285, 280), (276, 258)])
        items += [path(lap, O["jk_lt"]), line([(276, 258), (285, 280), (295, 304)], O["jk_sh"], 1.1)]
        items += [ellipse(301.5 + be * 0.5, y, 1.9, 1.9, tone(O["jk"], 0.6), INK, 0.6) for y in (310, 330)[: j.get("buttons", 2)]]
        items += [path(quad([(262, 352), (288, 352), (288, 356), (262, 356)]), O["jk_sh"]), line([(262, 352), (288, 352)], INK, 0.9)]
        items.append(path(quad([(272, 288), (285, 288), (285, 290.5), (272, 290.5)]), O["jk_sh"]))  # the breast pocket's welt
        items.append(path(smooth([(276, 287), (280, 282), (283, 287)]), O["shirt"], INK, 0.7))       # and its folded handkerchief
    if j.get("uniform"):
        # a standing collar, a breast pocket with its flap, the shoulder strap
        items += [path(quad([(276, 282), (296, 282), (296, 300), (276, 300)]), O["jk_sh"]),
                  path(quad([(275, 280), (297, 280), (296, 287), (286, 289), (276, 287)]), O["jk"], INK, 1.0),
                  ellipse(286, 285.5, 1.6, 1.6, "#2c2a24", INK, 0.5),
                  path(quad([(272, 360), (292, 360), (292, 368), (272, 368)]), O["jk_sh"]),
                  line([(298, 300), (298, 360)], O["jk_sh"], 1.0)]
    out = C(smooth(pts), "jk", items, s=6)
    if j.get("uniform"):
        out += cel(quad([(245, 340), (298 + O["build"]["belly"] * 0.8, 340), (298 + O["build"]["belly"] * 0.8, 347), (245, 347)]), "#2c2a24", "#1b1a16", None,
                   [path(rect(286, 339, 294, 348), "none", O["brass"], 1.6)], s=1)
    return out


def s_cardigan():
    c = O["cardigan"]
    O["card"], O["card_sh"], O["card_lt"] = c["color"], tone(c["color"], 0.74), tone(c["color"], 1.18)
    hem = c["hem"]
    pts = s_torso_pts(2.5, hem, flare=1.5)
    pts[0] = (288, 252)
    items = [line([(258, 270), (255, 330), (254, hem - 4)], O["card_sh"], 1.2),
             path(quad([(236, hem - 9), (320, hem - 9), (320, hem + 2), (236, hem + 2)]), O["card_sh"]),
             line([(236, hem - 9), (320, hem - 9)], INK, 0.8)]
    items += [line([(x, hem - 8), (x, hem)], tone(O["card"], 0.6), 0.7) for x in range(246, 306, 4)]
    # the open front edge with its band and buttons, a patch pocket
    items += [line([(290, 254), (300, 280), (299, 320), (298, hem - 9)], O["card_lt"], 2.2),
              line([(290, 252), (301, 279), (300, 320), (299, hem - 9)], INK, 0.8)]
    items += [ellipse(300.5, y, 1.6, 1.6, "#d8cfbd", INK, 0.5) for y in (300, 322, 344)]
    items += [path(quad([(270, 350), (292, 350), (292, 374), (270, 374)]), O["card_sh"]), line([(270, 350), (292, 350)], INK, 0.8)]
    return C(smooth(pts), "card", items, s=6)


def s_belt(y=340.0, h=7.0):
    be = O["build"]["belly"]
    d = quad([(246, y), (296 + be * 0.8, y), (296 + be * 0.8, y + h), (246, y + h)])
    return cel(d, O["leather"], O["leather_sh"], O["leather_lt"], [], s=1.5) if h > 3 else cel(d, "#2c2a24", "#1b1a16", None, [], s=1)


def s_tool_belt():
    """The builder's belt: leather, a pouch at the hip, the folding rule in it,
    a pencil and a hammer loop."""
    out = s_belt(344, 7)
    pouch = smooth([(254, 348), (284, 348), (286, 382), (280, 388, True), (256, 388, True), (252, 380)])
    out += cel(pouch, O["leather"], O["leather_sh"], O["leather_lt"],
               [path(quad([(252, 348), (286, 348), (285, 360), (253, 360)]), O["leather_sh"]), line([(253, 360), (285, 360)], INK, 0.9),
                line([(258, 370), (280, 370)], O["leather_sh"], 1.0)], s=3)
    rule = quad([(262, 330), (271, 329), (272, 350), (263, 351)])
    out = cel(rule, O["rule"], O["rule_sh"], None, [line([(264, 336), (270, 335.5)], INK, 0.6), line([(264, 342), (270, 341.5)], INK, 0.6)], s=1.5) + out
    pen = capsule((277, 336), (279, 350), 1.6, 1.6)
    out = cel(pen, O["pencil"], O["pencil_sh"], None, [], s=0.8, sw=1.2) + out
    return out


# ---- collar, tie, neck ---------------------------------------------------------------------

def s_neck():
    dx, dy = head_shift()
    svg.DX, svg.DY = dx * 0.6, dy * 0.6
    out = C(smooth([(263, 226), (286, 232), (290, 258), (264, 262)]), "skin", [line([(274, 240), (282, 244)], O["skin_sh"], 1.0)], s=4)
    if O.get("female"):
        out = C(smooth([(266, 226), (285, 232), (288, 258), (266, 262)]), "skin", [], s=4)
    svg.DX, svg.DY = 0.0, 0.0
    neck = O.get("neck")
    if neck in ("bowtie", "tie", "collar"):
        collar = smooth([(266, 244), (282, 244), (293, 247), (295, 256), (286, 258), (270, 254)])
        out += C(collar, "shirt", [line([(284, 247), (292, 255)], O["shirt_sh"], 0.9)], s=2.5)
    if neck == "bowtie":
        bow = smooth([(289, 252), (296, 248), (299, 254), (296, 260), (289, 257)])
        out += C(bow, "tie", [], s=1.6) + C(smooth([(292, 250), (296, 250), (297, 258), (292, 258)]), "tie", [], s=1)
    if neck == "tie":
        knot = smooth([(290, 251), (296, 251), (297, 257), (291, 258)])
        out += C(knot, "tie", [], s=1.5)
    if neck == "open":
        out += C(smooth([(266, 246), (282, 248), (292, 254), (296, 264), (288, 262), (278, 256), (268, 254)]), "shirt",
                 [line([(282, 252), (292, 260)], O["shirt_sh"], 0.9)], s=2)
    if neck == "collar" and O.get("jacket", {}).get("uniform"):
        out += C(smooth([(264, 244), (284, 244), (294, 248), (296, 258), (286, 260), (266, 256)]), "jk", [], s=2)
    if O.get("badge"):
        out += [line([(286, 258), (296, 270), (300, 290)], O["lanyard"], 1.6)]
        out += cel(quad([(295, 288), (305, 288), (305, 302), (295, 302)]), WHITE, "#c9c4b8", None,
                   [path(rect(297, 291, 303, 296), "#7a8aa0"), line([(297, 299), (303, 299)], "#666", 0.7)], s=1.2, sw=1.2)
    return out


def s_tie_front():
    """The long tie down the shirt front (under a vest, on the chest)."""
    if O.get("neck") != "tie":
        return []
    be = O["build"]["belly"]
    ch = O["build"]["chest"]
    d = smooth([(292, 257), (297, 257), (301 + ch * 0.6, 278), (300 + be * 0.2, 300), (297, 304, True), (295, 298), (294 + ch * 0.3, 276)])
    return C(d, "tie", [line([(295, 262), (298, 290)], O["tie_lt"], 1.0)], s=1.6)


# ---- heads ------------------------------------------------------------------------------

def profile_pts():
    """A face in profile, facing right, from the look's ``face`` numbers: the
    forehead, the nose (length, drop, hump, bulb), the lips, the chin, the jaw,
    the back of the skull."""
    f = O["face"]
    B = 299.0 + f.get("brow", 0.0)
    nl, nd = f.get("nose", (11.0, 17.0))
    tip = (B + nl, 199.0 + nd)
    root = (B + 1.0, 199.5)
    hump = f.get("hump", 0.0)
    bulb = f.get("bulb", 0.0)
    ml = 232.0 + f.get("mouth", 0.0)
    ch = f.get("chin", 0.0)
    cy = 249.0 + f.get("jaw", 0.0)
    mid = lerp(root, tip, 0.45)
    n = (tip[1] - root[1], -(tip[0] - root[0]))
    L = math.hypot(*n)
    mid = (mid[0] + n[0] / L * hump, mid[1] + n[1] / L * hump)
    gaunt = 1.5 if f.get("gaunt") else 0.0
    pts = [(260, 167), (280, 164.5), (B - 7, 169), (B - 2, 177), (B + 0.6, 188), (B + 0.2, 194.5), root, mid,
           (tip[0] - 1.6 + bulb * 0.2, tip[1] - 3.0 - bulb), (tip[0] + bulb * 0.5, tip[1] + 0.2), (tip[0] - 2.0, tip[1] + 3.2 + bulb * 0.5),
           (B + 3.5, tip[1] + 4.2, True), (B + 4.2 + gaunt * 0.3, ml - 4.5), (B + 4.0, ml - 1.6), (B + 2.2, ml, True), (B + 3.4, ml + 2.6),
           (B + 1.8, ml + 6.4), (B + 3.4 + ch, ml + 10.5), (B + 2.2 + ch, cy - 2.4), (B - 3.0 + ch * 0.5, cy + 0.4),
           (B - 15, cy + 0.6 - gaunt), (271, cy - 3.5), (261, cy - 11), (253, cy - 21), (247.2, 213), (247.0, 196), (250.5, 181)]
    return pts, B, tip, ml, cy


def s_head():
    dx, dy = head_shift()
    svg.DX, svg.DY = dx, dy
    out = s_head_inner()
    svg.DX, svg.DY = 0.0, 0.0
    return out


def s_head_inner():
    sk, dk = O["skin_sh"], O["skin_dk"]
    pts, B, tip, ml, cy = profile_pts()
    f = O["face"]
    ex, ey = B - 3.0, S_EYE[1]
    out = []
    if O.get("hair") == "knot":  # the knot of hair behind, under the skull's outline
        out += s_knot()
    if O.get("hair") == "bun_cap":
        out += C(smooth([(238, 204), (244, 196), (252, 198), (254, 212), (246, 218), (238, 214)]), "hr", [line([(242, 204), (250, 210)], O["hr_lt"], 1.0)], s=2.5)
    items = [
        line([(B + 0.5, cy - 1.5), (B - 12, cy - 0.5), (272, cy - 5), (266, cy - 14), (265, 222)], sk, 1.3),
        path(smooth([(255, 214), (262, 230), (273, cy - 6), (288, cy - 1.0), (B, cy - 1.0), (288, cy + 1.2), (272, cy - 2), (258, 234)]), sk),
        line([(B - 4, 207.5), (B + 1.5, 211)], sk, 1.0),
        # the nostril, the wing of the nose, the fold to the mouth
        line([(tip[0] - 7.5, tip[1] - 2.8), (tip[0] - 8.5, tip[1] + 0.6), (tip[0] - 6.4, tip[1] + 3.2)], dk, 1.0),
        line([(tip[0] - 5.4, tip[1] + 3.3), (tip[0] - 2.8, tip[1] + 3.6)], dk, 1.2),
        line([(tip[0] - 8.4, tip[1] + 1.2), (B - 3.4, ml - 4), (B - 2.0, ml + 1.5)], dk if f.get("lines", 1) >= 1 else sk, 0.95),
        line([(B + 1.0, 201), (tip[0] - 2.5, tip[1] - 4)], O["skin_lt"], 1.3),
        # the mouth's line and the lower lip's shade
        line([(B - 2.6, ml - 0.4), (B - 0.2, ml + 0.2), (B + 2.4, ml)], INK, 1.4),
        path(smooth([(B - 0.2, ml + 1.6), (B + 3.0, ml + 2.2), (B + 2.4, ml + 4.4), (B - 0.4, ml + 3.8)]), O["lip"]),
        line([(B + 0.4, ml + 7.0), (B + 2.2, ml + 7.0)], dk, 0.9),
    ]
    if f.get("lines", 1) >= 2:  # age: the crow's foot, the cheek's furrow, the forehead
        items += [line([(ex - 6.5, ey + 0.2), (ex - 9.5, ey - 1.4)], dk, 0.8), line([(ex - 6.3, ey + 2.4), (ex - 9.2, ey + 3.6)], dk, 0.8),
                  line([(B - 10, 214), (B - 13, 226)], sk, 1.1), line([(B - 9, 180), (B - 2, 179.5)], sk, 1.0), line([(B - 10, 185), (B - 3, 184.6)], sk, 0.9)]
    if f.get("gaunt"):
        items += [line([(B - 25, 218), (B - 20, 224), (B - 19, 233)], sk, 1.6)]
    if O.get("blush"):
        items.append(ellipse(B - 11, 220, 6.5, 4.0, O["blush"]))
    if f.get("double_chin"):
        items += [line([(B - 14, cy + 2.4), (B - 4, cy + 4.0), (B + 1, cy + 2.2)], sk, 1.1)]
    face = smooth(pts)
    out += C(face, "skin", items, s=6)
    if f.get("double_chin"):
        out = C(smooth([(B - 22, cy - 6), (B - 4, cy - 2), (B + 1.5, cy + 1.5), (B - 6, cy + 6), (B - 20, cy + 4)]), "skin", [], s=2) + out
    if O.get("ear_pencil"):  # tucked behind the ear, its point forward
        out += cel(capsule((250, 201), (276, 195), 1.8, 1.8), O["pencil"], O["pencil_sh"], None,
                   [path(smooth([(274, 193.2), (279.5, 194.6, True), (274.6, 197.2)]), "#e8cfa4")], s=0.8, sw=1.2)
    # the ear
    out += C(smooth([(258.6, 199), (265.6, 197.6), (268.2, 207), (266, 217.4), (259.6, 216.6)]), "skin",
             [line([(262.4, 202), (265.4, 207), (262.6, 212.4)], dk, 1.0)], s=3)
    if O.get("female"):
        out.append(ellipse(262.6, 219.0, 1.7, 1.7, O["brass_lt"], INK, 0.8))
        out.append(path(smooth([(B - 0.6, ml - 2.4), (B + 3.6, ml - 3.4), (B + 3.8, ml - 0.6), (B + 0.2, ml - 0.4)]), O["lip"]))
    out += s_eye(ex, ey)
    out += s_hair()
    if O.get("moustache"):
        out += C(smooth([(B - 2.0, tip[1] + 5.0), (tip[0] - 3.8, tip[1] + 4.6), (tip[0] - 3.2, tip[1] + 6.8), (B + 2.6, ml - 1.6), (B - 4.4, ml - 2.0)]), "moustache", [], s=1.0, sw=1.0)
    if O.get("beard"):
        out += s_beard(B, tip, ml, cy)
    if O.get("glasses"):
        out += s_glasses(ex, ey, B)
    if O.get("hat") == "hardhat":
        out += s_hardhat()
    if O.get("hat") == "eyeshade":
        out += s_eyeshade(B)
    if O.get("hat") == "fieldcap":
        out += s_fieldcap()
    return out


def s_eye(ex, ey):
    """One small eye, the lid heavy over it, the brow above."""
    out = [path(smooth([(ex - 3.8, ey + 0.6), (ex + 0.2, ey - 1.9), (ex + 3.8, ey - 0.8), (ex + 3.2, ey + 1.6), (ex - 0.6, ey + 2.1)]), WHITE),
           ellipse(ex + 2.0, ey - 0.1, 1.3, 1.9, O["iris"]), ellipse(ex + 2.3, ey - 0.1, 0.6, 0.9, PUPIL),
           line([(ex - 4.2, ey + 0.6), (ex + 0.2, ey - 2.2), (ex + 4.2, ey - 0.8)], INK, 1.6),
           line([(ex - 3.4, ey - 3.6), (ex + 0.4, ey - 4.6), (ex + 3.6, ey - 3.4)], O["skin_sh"], 0.9),
           line([(ex - 2.2, ey + 2.6), (ex + 2.8, ey + 2.2)], O["skin_sh"], 0.8)]
    brow_c = O.get("brow_c") or tone(O.get("hair_c", "#555555"), 0.75)
    if O.get("hair") in ("hat_white", "combed"):
        brow_c = tone(O["hair_c"], 0.7)
    if O.get("hair") == "fringe":
        brow_c = tone(O["hair_c"], 0.8)
    by = ey - 6.6
    arch = -1.0 if O.get("female") else 0.0
    out += [line([(ex - 6.0, by + 0.6), (ex - 0.5, by - 1.0 + arch), (ex + 5.2, by + 0.6)], brow_c, 2.6),
            line([(ex - 6.0, by + 0.6), (ex - 0.5, by - 1.0 + arch), (ex + 5.2, by + 0.6)], INK, 0.6)]
    return out


def s_hair():
    h = O.get("hair")
    if h == "slick":
        cap = [(292, 173), (290, 166), (280, 160.5), (264, 160), (252, 167), (246, 180), (246, 196), (249, 210), (253, 222)]
        inner = [(256, 214), (257, 200), (263, 192), (270, 182), (280, 175)]
        d = smooth(cap + inner)
        items = [line([(288, 166), (272, 164), (258, 172), (252, 186)], O["hr_lt"], 1.4), line([(282, 170), (266, 170), (256, 182)], O["hr_sh"], 1.1),
                 path(smooth([(256, 196), (262, 190), (264, 200), (258, 212)]), O["temple"])]
        return C(d, "hr", items, s=3.5, edges=[cap])
    if h == "knot":
        cap = [(293, 176), (291, 167), (281, 161), (265, 160), (252, 166), (245, 180), (245, 198), (249, 212), (254, 222)]
        inner = [(258, 214), (258, 198), (266, 186), (280, 178)]
        items = [line([(290, 168), (276, 164), (260, 168), (250, 182)], O["streak"], 2.2), line([(284, 174), (266, 174), (256, 188)], O["hr_sh"], 1.0),
                 line([(276, 170), (260, 176), (252, 194)], O["hr_lt"], 1.0)]
        return C(smooth(cap + inner), "hr", items, s=3.5, edges=[cap])
    if h == "hat_white":  # short white hair under the hat brim, over the ear and round the nape
        d = smooth([(249, 186), (264, 186), (266, 193), (259, 197), (253, 205), (248.6, 208), (246.8, 196)])
        return C(d, "hr", [], s=2, edges=[[(264, 186), (266, 193), (259, 197), (253, 205), (248.6, 208)]])
    if h == "fringe":  # bald on top; a fringe from temple to temple round the back
        d = smooth([(266, 186), (270, 194), (266, 200), (258, 214), (256, 226), (250, 224), (246.6, 212), (246.6, 196), (250, 186)])
        items = [line([(252, 194), (254, 214)], O["hr_sh"], 0.9), line([(262, 192), (258, 200)], O["hr_lt"], 0.9)]
        out = C(d, "hr", items, s=2, edges=[[(266, 186), (270, 194), (266, 200), (258, 214), (256, 226)]])
        # the scalp's shine
        return [line([(268, 168), (280, 166)], O["skin_lt"], 2.0)] + out
    if h == "bun_cap":
        d = smooth([(266, 190), (268, 198), (262, 200), (256, 214), (254, 224), (248, 216), (246.6, 200), (250, 188)])
        return C(d, "hr", [line([(252, 196), (253, 212)], O["hr_lt"], 0.9)], s=2, edges=[[(266, 190), (268, 198), (262, 200), (256, 214), (254, 224)]])
    if h == "combed":  # thin grey hair combed flat back from a receding line, the scalp showing through
        cap = [(286, 168), (280, 162.5), (266, 161), (254, 165.5), (247, 178), (246, 196), (249, 212), (254, 222)]
        inner = [(258, 214), (258, 199), (262, 190), (268, 180), (276, 172)]
        items = [line([(282, 166), (268, 165), (256, 172)], O["hr_lt"], 1.1), line([(280, 170), (264, 170), (254, 182)], O["hr_sh"], 0.9),
                 line([(272, 176), (260, 182), (254, 198)], O["hr_sh"], 0.9)]
        return C(smooth(cap + inner), "hr", items, s=3, edges=[cap])
    return []


def s_knot():
    out = C(smooth([(236, 196), (242, 186), (254, 186), (258, 200), (252, 212), (240, 212)]), "hr",
            [line([(240, 196), (250, 192), (254, 200)], O["hr_lt"], 1.1), line([(242, 204), (252, 206)], O["hr_sh"], 1.0),
             line([(240, 192), (246, 188)], O["streak"], 1.6)], s=3)
    if O.get("pencil_knot"):  # a pencil through the knot
        out = cel(capsule((232, 210), (258, 186), 1.8, 1.8), O["pencil"], O["pencil_sh"], None, [], s=0.8, sw=1.2) + out
        out += cel(capsule((234, 208), (238, 204), 1.8, 1.8), O["pencil"], O["pencil_sh"], None, [], s=0.8, sw=1.2)
    return out


def s_beard(B, tip, ml, cy):
    """A short white beard from below the ear round the jaw to the chin, and the
    moustache over the lip."""
    beard = smooth([(263, 214), (268, 222), (276, 232), (287, 238), (B - 3, ml + 2.4), (B + 2.6, ml + 4.4), (B + 4.4, ml + 10), (B + 2.6, cy + 2.6),
                    (B - 6, cy + 4.6), (B - 17, cy + 3.4), (272, cy - 2), (264, cy - 11), (261, 224)])
    items = [line([(272, 238), (282, 246)], O["hr_sh"], 1.0), line([(B - 9, cy - 1), (B - 3, cy + 2)], O["hr_sh"], 1.0),
             line([(278, 236), (288, 241)], O["hr_lt"], 1.2)]
    out = C(beard, "hr", items, s=3)
    out += C(smooth([(B - 3, tip[1] + 4.6), (tip[0] - 2.4, tip[1] + 4.0), (tip[0] - 0.4, tip[1] + 8.4), (B + 3, ml + 1.0), (B - 6, ml - 0.6)]), "hr", [], s=1.5, sw=1.4)
    # the mouth shows between moustache and beard
    out += [line([(B - 0.5, ml + 0.8), (B + 2.6, ml + 1.0)], INK, 1.2)]
    return out


def s_glasses(ex, ey, B):
    g = O["glasses"]
    if g == "round":  # heavy round black rims (the lens toward the camera, cheated a quarter turn)
        return [ellipse(ex + 1.5, ey + 0.2, 6.4, 6.2, "#e8eef2", INK, 2.6).replace('fill="#e8eef2"', 'fill="#e8eef2" fill-opacity="0.18"'),
                line([(ex - 4.8, ey - 1.4), (264, 202)], INK, 2.2)]
    if g == "specs":  # small oblong spectacles, wire
        return [path(smooth([(ex - 3.6, ey - 3.0), (ex + 5.8, ey - 3.0), (ex + 5.6, ey + 3.4), (ex - 3.4, ey + 3.4)]), "none", "#5a4a3a", 1.4),
                line([(ex - 3.6, ey - 1.6), (264, 201)], "#5a4a3a", 1.2)]
    if g == "halfmoon":  # half-moon reading glasses low on the nose, the chain looping to the collar
        return [path(smooth([(ex - 2.0, ey + 3.6, True), (ex + 7.4, ey + 3.4, True), (ex + 6.6, ey + 7.4), (ex + 2.4, ey + 8.6), (ex - 1.2, ey + 7.0)]),
                     "none", "#9a8a5a", 1.4),
                line([(ex - 2.0, ey + 4.0), (264, 203)], "#9a8a5a", 1.1),
                line([(263, 204), (258, 222), (262, 244), (272, 254)], "#b8a870", 0.9)]
    return []


def s_hardhat():
    dome = smooth([(246, 186), (246, 166), (256, 150), (274, 143), (292, 147), (302, 160), (305, 178), (276, 181)])
    items = [line([(270, 146), (268, 180)], O["ht_sh"], 2.4), line([(256, 154), (284, 146)], WHITE, 1.4), line([(272, 145), (272, 181)], INK, 0.8)]
    out = C(dome, "ht", items, s=4)
    brim = smooth([(242, 182), (276, 177), (304, 176), (318, 182, True), (304, 186), (276, 186), (244, 190)])
    out += C(brim, "ht", [], s=2)
    return out


def s_eyeshade(B):
    """The green celluloid eyeshade: a band round the head, the visor out over the eyes."""
    O["shade_g"], O["shade_g_sh"], O["shade_g_lt"] = "#3f8a5a", "#2c6a42", "#6fb586"
    band = smooth([(248, 182), (276, 176), (300, 178), (301, 186), (276, 184), (249, 191)])
    out = cel(band, "#2c3a30", "#1c241e", None, [], s=1, sw=1.6)
    visor = smooth([(284, 178), (304, 176), (322, 186, True), (318, 190), (300, 188), (286, 186)])
    out += cel(visor, O["shade_g"], O["shade_g_sh"], O["shade_g_lt"], [line([(296, 179), (316, 186)], "#a6dcb5", 1.2)], s=2)
    return out


def s_fieldcap():
    crown = smooth([(250, 182), (248, 166), (258, 154), (280, 150), (298, 156), (304, 170), (302, 180), (276, 182)])
    items = [line([(254, 172), (300, 168)], O["ht_sh"], 1.2), line([(258, 160), (282, 154)], O["ht_lt"], 1.4)]
    out = C(crown, "ht", items, s=4)
    out += C(quad([(250, 176), (302, 172), (303, 182), (250, 186)]), "ht", [], s=1.5)
    out += cel(smooth([(294, 178), (304, 176), (318, 183, True), (300, 185)]), "#222", "#111", "#444", [], s=1.2)
    out += cel(smooth([(292, 165), (297, 163), (299, 169), (294, 171)]), O["armband"], tone(O["armband"], 0.7), None, [], s=1, sw=1.2)
    return out


# ---- arms ---------------------------------------------------------------------------------

def sleeve_upper(s, e, near=True, band=True):
    kind = O["sleeve"]
    if kind == "jacket":
        key, r = "jk", (11.5, 10.0)
    elif kind == "oversleeve":
        key, r = "card", (11.5, 10.0)
    elif kind == "rolled":
        key, r = "shirt", (10.6, 9.4)
    else:
        key, r = "shirt", (11.5, 10.5)
    d = capsule(s, e, *r)
    a = ang(s, e)
    p = frame(s, a)
    items = [line([p(8, -r[0] * 0.4), p(36, -r[1] * 0.45)], O.get(key + "_lt", O[key]), 1.2)]
    if kind == "garter":  # the black sleeve garter above the elbow
        items.append(path(quad([p(26, -14), p(31, -14), p(31, 14), p(26, 14)]), "#1f1d1e"))
        items.append(line([p(28.5, -12), p(28.5, 12)], "#6a6a6a", 0.6))
    if O.get("armband") and near and band:
        items.append(path(quad([p(14, -14), p(22, -14), p(22, 14), p(14, 14)]), O["armband"]))
        items.append(ellipse(*p(18, -1), 2.4, 2.4, "#1f1d1e"))
        items.append(line([p(14, -13), p(14, 13)], INK, 0.8))
        items.append(line([p(22, -13), p(22, 13)], INK, 0.8))
    return C(d, key, items, s=4) if near else far(d, key)


def sleeve_lower(e, w, near=True):
    kind = O["sleeve"]
    a = ang(e, w)
    p = frame(e, a)
    L = math.hypot(w[0] - e[0], w[1] - e[1])
    if kind == "rolled":  # the bare forearm, the shirt rolled thick above the elbow
        out = cel(capsule(e, w, 8.4, 6.8), *skin_keys(near)[:3], [line([p(10, -3), p(L - 8, -3)], O["skin_sh"], 0.8)], s=3)
        roll = smooth([p(-3, -10.2), p(4, -10.6), p(4.6, 0), p(4, 10.6), p(-3, 10.2), p(-3.6, 0)])
        return out + (C(roll, "shirt", [line([p(1.5, -11), p(1.5, 11)], O["shirt_sh"], 1.0)], s=2.5) if near else far(roll, "shirt"))
    if kind == "oversleeve":  # black cotton oversleeves, gathered at the wrist
        d = capsule(e, w, 10.5, 9.0)
        O["over"], O["over_sh"], O["over_lt"] = "#2c2a2e", "#1a191c", "#45434a"
        items = [line([p(6, -6), p(L - 6, -5)], O["over_lt"], 1.0), line([p(L - 4, -8), p(L - 4, 8)], "#111", 1.0)]
        items += [line([p(t, -9), p(t + 2, -4)], "#111", 0.7) for t in (6, 14, 22)]
        return C(d, "over", items, s=3) if near else far(d, "over")
    key = "jk" if kind == "jacket" else "shirt"
    d = capsule(e, w, 10.0, 8.6)
    items = [line([p(6, -4), p(L - 6, -4)], O.get(key + "_lt", O[key]), 1.0)]
    out = C(d, key, items, s=3.5) if near else far(d, key)
    if kind == "jacket":  # the shirt cuff peeping out
        cuff = capsule(p(L - 4, 0), p(L + 1.5, 0), 8.2, 8.0)
        out += C(cuff, "shirt", [], s=1.5) if near else far(cuff, "shirt")
    else:
        cuff = capsule(p(L - 6, 0), p(L, 0), 8.8, 8.6)
        out += C(cuff, "shirt", [line([p(L - 3, -8), p(L - 3, 8)], O["shirt_sh"], 0.8)], s=1.5) if near else far(cuff, "shirt")
    return out


def s_far_arm():
    s = S_SHOULDER["far"]
    e, w = S_FAR_ARM
    return sleeve_upper(s, e, near=False) + sleeve_lower(e, w, near=False) + hand_side(w, ang(e, w), near=False)


def s_near_arm():
    s = S_SHOULDER["near"]
    e, w, hand = S_NEAR_ARM[O["prop"]]
    return sleeve_upper(s, e) + sleeve_lower(e, w) + near_fist()


def near_fist():
    """The near hand, closed on the prop it holds."""
    e, w, hand = S_NEAR_ARM[O["prop"]]
    a = ang(e, w)
    out = []
    if hand == "fist_down":
        out += fist(frame(w, a)(9, 0), a + math.pi / 2, -1)
    elif hand == "fist_roll":
        out += fist(frame(w, a)(8, 1), math.radians(18), 1)
    elif hand == "fist_knob":
        out += fist(frame(w, a)(8, -1), a + 0.2, 1)
    elif hand == "fist_board":
        out += fist(frame(w, a)(7, 0), a - 0.6, 1)
    elif hand == "fist_stamp":
        out += fist(frame(w, a)(8, 0), a, 1)
    elif hand == "fist_paper":
        out += fist(frame(w, a)(7, 0), a - 0.4, 1)
    return out


# ---- props (side) ---------------------------------------------------------------------

def s_prop_behind_arm():
    p = O["prop"]
    if p == "roll":
        a, b = (226, 288), (326, 322)
        d = capsule(a, b, 8.0, 8.0)
        u = frame(a, ang(a, b))
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        items = [line([u(10, -3.5), u(L - 12, -3.5)], O["roll_lt"], 1.6), line([u(L * 0.62, -8), u(L * 0.62, 8)], "#c9b07a", 2.4),
                 line([u(30, 4), u(L - 30, 4)], O["roll_sh"], 1.0)]
        out = C(d, "roll", items, s=3)
        # the open front end shows the paper's spiral
        e = u(L - 1, 0)
        out += [ellipse(e[0], e[1], 4.4, 7.6, "#e9eef4", INK, 1.4, rot=math.degrees(ang(a, b))),
                path(smooth([(e[0] - 1.6, e[1] - 4), (e[0] + 1.4, e[1] - 2.8), (e[0] + 1.6, e[1] + 2), (e[0] - 1, e[1] + 3.6), (e[0] - 0.8, e[1] - 0.6)],
                            closed=False), "none", O["roll_sh"], 0.8)]
        return out
    if p == "fanfold":
        return s_fanfold()
    return []


def s_prop_front():
    p = O["prop"]
    if p == "square":
        e, w, _ = S_NEAR_ARM["square"]
        top = (w[0] + 4, w[1] + 2)
        blade = quad([(top[0] - 3.5, top[1] - 6), (top[0] + 3.5, top[1] - 6), (top[0] + 3.5, 446), (top[0] - 3.5, 446)])
        tongue = quad([(top[0] - 3.5, 446), (top[0] + 46, 446), (top[0] + 46, 453), (top[0] - 3.5, 453)])
        ticks = [line([(top[0] - 3.5, y), (top[0] - 0.5 - (1.5 if (y // 6) % 2 else 0), y)], INK, 0.6) for y in range(370, 444, 6)]
        ticks += [line([(x, 453), (x, 450 - (1.5 if (x // 6) % 2 else 0))], INK, 0.6) for x in range(int(top[0] + 6), int(top[0] + 44), 6)]
        out = cel(tongue + " " + blade, O["steel"], O["steel_sh"], O["steel_lt"], [], s=2)
        out = cel(blade, O["steel"], O["steel_sh"], O["steel_lt"], ticks[:13], s=2) + cel(tongue, O["steel"], O["steel_sh"], O["steel_lt"], ticks[13:], s=2)
        return out
    if p == "dividers":
        return s_dividers()
    if p == "clipboard":
        return s_clipboard()
    if p == "stamp":
        return s_stamp()
    return []


def s_dividers():
    """Brass drafting dividers as tall as his hip, planted like a cane: the
    hinge under his palm, the two legs splayed to steel points on the ground."""
    hinge = (314, 346)
    legs = [((hinge[0] - 2, hinge[1] + 6), (300, GROUND_Y - 2)), ((hinge[0] + 2, hinge[1] + 6), (330, GROUND_Y - 2))]
    out = []
    for (a, b), near in zip(legs, (False, True)):
        d = capsule(a, b, 3.6, 1.6)
        out += cel(d, O["brass"] if near else O["brass_sh"], O["brass_sh"], O["brass_lt"] if near else None, [], s=1.5, sw=1.6)
        tipd = capsule(lerp(a, b, 0.9), b, 1.9, 0.6)
        out += cel(tipd, O["steel"], O["steel_sh"], None, [], s=0.6, sw=1.2)
    # the arc and its screw
    out += [line([lerp(*legs[0], 0.55), (316, lerp(*legs[0], 0.55)[1] + 2), lerp(*legs[1], 0.55)], INK, 3.0),
            line([lerp(*legs[0], 0.55), (316, lerp(*legs[0], 0.55)[1] + 2), lerp(*legs[1], 0.55)], O["brass_lt"], 1.4)]
    out += cel(smooth([(hinge[0] - 7, hinge[1] + 2), (hinge[0], hinge[1] - 8), (hinge[0] + 7, hinge[1] + 2), (hinge[0], hinge[1] + 8)]),
               O["brass"], O["brass_sh"], O["brass_lt"], [ellipse(hinge[0], hinge[1], 2.0, 2.0, O["brass_sh"], INK, 0.6)], s=1.5, sw=1.8)
    return out


def s_clipboard():
    """The clipboard held up to read: the board, the manifest on it, the clip."""
    c = (318, 286)
    deg = -14
    def R(x, y):
        a = math.radians(deg)
        return (c[0] + x * math.cos(a) - y * math.sin(a), c[1] + x * math.sin(a) + y * math.cos(a))
    board = quad([R(-17, -24), R(17, -24), R(17, 24), R(-17, 24)])
    out = cel(board, O["board"], O["board_sh"], O["board_lt"], [], s=2)
    paper = quad([R(-14, -18), R(14, -18), R(14, 22), R(-14, 22)])
    rows = [line([R(-11, y), R(11 if (y // 5) % 3 else 4, y)], "#8a8a92", 0.8) for y in range(-12, 20, 4)]
    out += cel(paper, O["paper"], O["paper_sh"], None, rows + [line([R(-11, -15), R(4, -15)], INK, 1.0)], s=1.2, sw=1.2)
    out += cel(quad([R(-7, -27), R(7, -27), R(8, -18), R(-8, -18)]), O["steel"], O["steel_sh"], O["steel_lt"], [], s=1, sw=1.4)
    return out


def stamp(c, k=1.35):
    """A big wooden-handled rubber stamp gripped at ``c`` by its stem: the knob
    above the fist, the block and its red-inked rubber below."""
    q = lambda x, y: (c[0] + x * k, c[1] + y * k)
    knob = smooth([q(-6, -11), q(0, -16), q(6, -11), q(3.4, -6), q(-3.4, -6)])
    stem = quad([q(-3, -8), q(3, -8), q(3, 10), q(-3, 10)])
    base = quad([q(-10, 9), q(10, 9), q(10, 16), q(-10, 16)])
    pad = quad([q(-9, 16), q(9, 16), q(9, 19), q(-9, 19)])
    out = cel(stem, O["wood"], O["wood_sh"], O["wood_lt"], [], s=1.5)
    out += cel(knob, O["wood"], O["wood_sh"], O["wood_lt"], [], s=2)
    out += cel(base, O["wood"], O["wood_sh"], O["wood_lt"], [line([q(-8, 12.5), q(8, 12.5)], O["wood_sh"], 1.0)], s=1.5)
    out += cel(pad, O["ink_red"], tone(O["ink_red"], 0.7), None, [], s=1, sw=1.4)
    return out


def stack_of_folds(cx, w, top, n=9):
    """The fanfold's heap on the floor: the folded sheets stacked, each fold a
    slab a little off the one below, the fold edges alternating sides."""
    out = []
    h = (GROUND_Y - top) / n
    for i in range(n):
        y1 = GROUND_Y - i * h
        y0 = y1 - h
        off = (2.5 if i % 2 else -2.5) + (i * 0.4)
        x0, x1 = cx - w / 2 + off, cx + w / 2 + off
        d = smooth([(x0, y0, True), (x1, y0, True), (x1 + (1.4 if i % 2 else 0), (y0 + y1) / 2), (x1, y1, True), (x0, y1, True),
                    (x0 - (0 if i % 2 else 1.4), (y0 + y1) / 2)])
        fill = O["paper"] if i % 2 else O["paper_lt"]
        out += cel(d, fill, O["paper_sh"], None, [line([(x0 + 5, (y0 + y1) / 2), (x1 - 5, (y0 + y1) / 2)], O["green_bar"], 1.4)], s=1.0, sw=1.1)
    return out


def s_stamp():
    """A big wooden-handled rubber stamp, raised and ready."""
    e, w, _ = S_NEAR_ARM["stamp"]
    return stamp(frame(w, ang(e, w))(8, 0))


def s_fanfold():
    """The manifest as a run of fanfold printout: the top sheet in his hand, the
    rest falling in zigzag folds and heaped on the floor, green-barred, the
    sprocket holes down both edges."""
    e, w, _ = S_NEAR_ARM["fanfold"]
    h = frame(w, ang(e, w))(7, 0)
    out = []
    x0, x1 = h[0] - 4, h[0] + 26
    y = h[1] - 6
    panels = []
    k = 0
    while y < 452:
        dy = 13.0
        lean = 6.0 if k % 2 else -6.0
        x0n, x1n = x0 + lean * 0.3 + 0.8, x1 + lean * 0.3 + 0.8
        panels.append(((x0, y), (x1, y), (x1n, y + dy), (x0n, y + dy), k))
        x0, x1 = x0n, x1n
        y += dy
        k += 1
    for (a, b, c2, d, k) in panels:
        fill = O["paper"] if k % 2 == 0 else O["paper_sh"]
        items = [path(quad([lerp(a, d, 0.2), lerp(b, c2, 0.2), lerp(b, c2, 0.55), lerp(a, d, 0.55)]), O["green_bar"])]
        items += [ellipse(*lerp(lerp(a, d, 0.5), lerp(b, c2, 0.5), t), 0.9, 0.9, "#9a988e") for t in (0.07, 0.93)]
        out += cel(quad([a, b, c2, d]), fill, O["paper_sh"], None, items, s=1, sw=1.3)
    return stack_of_folds((x0 + x1) / 2 + 2, 34, 458) + out


# ---- the cast look as rig parts: one part per bone -----------------------------------------
#
# The candidate painters draw a whole leg and a whole arm as one shape. The rig
# turns the thigh, the shin, the upper arm, the forearm and the hand on bones
# of their own, so the cast looks draw those pieces here, each about its joint
# (``rig_joints``). ``scripts/build_hall_npc_v2_rigs.py`` reads both.

#: The look Jon's cast wears, by character (2026-10-23).
CAST = {"architect": "A", "manifest_clerk": "C"}


def s_thigh(side):
    hip, knee, _ankle = S_LEGS[side]
    wh, wk, _wa = trouser_widths()
    d = capsule(hip, knee, wh, wk)
    items = [line([(knee[0] - 6, knee[1] - 12), (knee[0] - 3, knee[1] - 2)], O["trouser_sh"], 1.1)]
    return C(d, "trouser", items, s=4.5) if side == "near" else far(d, "trouser")


def s_shin(side):
    _hip, knee, ankle = S_LEGS[side]
    _wh, wk, wa = trouser_widths()
    d = capsule(knee, (ankle[0], ankle[1] - 3), wk, wa)
    return C(d, "trouser", [], s=4.5) if side == "near" else far(d, "trouser")


def s_foot(side):
    return s_shoe(S_LEGS[side][2], side == "near")


def near_arm_points():
    """Shoulder, elbow and wrist of the near arm, by the prop it holds."""
    e, w, _hand = S_NEAR_ARM[O["prop"]]
    return S_SHOULDER["near"], e, w


def s_arm_upper(side):
    if side == "near":
        s, e, _w = near_arm_points()
        return sleeve_upper(s, e)
    return sleeve_upper(S_SHOULDER["far"], S_FAR_ARM[0], near=False)


def s_arm_lower(side):
    if side == "near":
        _s, e, w = near_arm_points()
        return sleeve_lower(e, w)
    return sleeve_lower(*S_FAR_ARM, near=False)


def s_hand(side):
    if side == "far":
        e, w = S_FAR_ARM
        return hand_side(w, ang(e, w), near=False)
    return near_fist()


def s_fanfold_hanging():
    """The run of fanfold from his fist down to the heap, without the heap: it
    hangs from the hand and moves with it. It reaches a little into the heap,
    so a small lift of the hand opens no gap."""
    e, w, _ = S_NEAR_ARM["fanfold"]
    h = frame(w, ang(e, w))(7, 0)
    out = []
    x0, x1 = h[0] - 4, h[0] + 26
    y = h[1] - 6
    k = 0
    while y < 466:
        dy = 13.0
        lean = 6.0 if k % 2 else -6.0
        x0n, x1n = x0 + lean * 0.3 + 0.8, x1 + lean * 0.3 + 0.8
        a, b, c2, d = (x0, y), (x1, y), (x1n, y + dy), (x0n, y + dy)
        fill = O["paper"] if k % 2 == 0 else O["paper_sh"]
        items = [path(quad([lerp(a, d, 0.2), lerp(b, c2, 0.2), lerp(b, c2, 0.55), lerp(a, d, 0.55)]), O["green_bar"])]
        items += [ellipse(*lerp(lerp(a, d, 0.5), lerp(b, c2, 0.5), t), 0.9, 0.9, "#9a988e") for t in (0.07, 0.93)]
        out += cel(quad([a, b, c2, d]), fill, O["paper_sh"], None, items, s=1, sw=1.3)
        x0, x1 = x0n, x1n
        y += dy
        k += 1
    return out


def s_fanfold_heap():
    """The heap of fanfold on the floor: it stays on the floor."""
    e, w, _ = S_NEAR_ARM["fanfold"]
    h = frame(w, ang(e, w))(7, 0)
    x0 = h[0] - 4
    k = 0
    y = h[1] - 6
    while y < 452:
        x0 += (6.0 if k % 2 else -6.0) * 0.3 + 0.8
        y += 13.0
        k += 1
    return stack_of_folds(x0 + 15 + 2, 34, 458)


def rig_side_layers() -> List[Tuple[str, str, Callable[[], List[str]]]]:
    """The cast look's side view as ``(part, bone, painter)``, back to front."""
    L: List[Tuple[str, str, Callable[[], List[str]]]] = []
    if O.get("prop") == "fanfold":
        L += [("fanfold_heap", "body", s_fanfold_heap), ("fanfold", "near_hand", s_fanfold_hanging)]
    L += [("far_arm_u", "far_arm_u", lambda: s_arm_upper("far")), ("far_arm_l", "far_arm_l", lambda: s_arm_lower("far")),
          ("far_hand", "far_hand", lambda: s_hand("far"))]
    for side in ("far", "near"):
        L += [(f"{side}_shin", f"{side}_leg_l", lambda s=side: s_shin(s)), (f"{side}_thigh", f"{side}_leg_u", lambda s=side: s_thigh(s)),
              (f"{side}_shoe", f"{side}_foot", lambda s=side: s_foot(s))]
    L.append(("seat", "body", s_seat))
    L.append(("shirt", "torso", s_shirt))
    L.append(("tie", "torso", s_tie_front))
    for key, painter in (("vest", s_vest), ("cardigan", s_cardigan), ("jacket", s_jacket)):
        if O.get(key):
            L.append((key, "torso", painter))
    if O.get("belt") == "tools":
        L.append(("tool_belt", "torso", s_tool_belt))
    L.append(("neck", "torso", s_neck))
    L.append(("head", "head", s_head))
    if O.get("prop") == "roll":
        L.append(("roll", "near_hand", s_prop_behind_arm))
    if O.get("prop") == "dividers":
        L.append(("dividers", "near_hand", s_prop_front))
    if O.get("prop") in ("square", "clipboard", "stamp"):
        L.append((O["prop"], "near_hand", s_prop_front))
    L += [("near_arm_u", "near_arm_u", lambda: s_arm_upper("near")), ("near_arm_l", "near_arm_l", lambda: s_arm_lower("near")),
          ("near_hand", "near_hand", lambda: s_hand("near"))]
    return L


def rig_joints() -> Dict[str, Tuple[str, float, float]]:
    """Where each bone of the cast look turns, in DESIGN units (before the
    look's ``k``): ``bone: (parent, x, y)``, parents first."""
    dx, dy = head_shift()
    s, e, w = near_arm_points()
    fe, fw = S_FAR_ARM
    J = {
        "body": ("", 269.0, 352.0),
        "torso": ("body", 269.0, 352.0),
        "head": ("torso", 274.0 + dx * 0.6, 246.0 + dy * 0.6),
        "near_arm_u": ("torso", *s),
        "near_arm_l": ("near_arm_u", *e),
        "near_hand": ("near_arm_l", *w),
        "far_arm_u": ("torso", *S_SHOULDER["far"]),
        "far_arm_l": ("far_arm_u", *fe),
        "far_hand": ("far_arm_l", *fw),
    }
    for side in ("near", "far"):
        hip, knee, ankle = S_LEGS[side]
        J[f"{side}_leg_u"] = ("body", *hip)
        J[f"{side}_leg_l"] = (f"{side}_leg_u", *knee)
        J[f"{side}_foot"] = (f"{side}_leg_l", *ankle)
    return J


def rig_drawing(char: str) -> Dict:
    """The cast look's side view as rig parts: ``parts`` is ``(part, bone, z,
    body)`` back to front, ``joints`` the bones in SVG units (the look's ``k``
    applied); ``svgkit`` is configured for ``svgkit.document``."""
    use(char, CAST[char])
    _N[0] = 0
    svg.configure(dx=0, dy=0, ink=INK, ow=OW, colors={})
    k = O["k"]
    svg.transform((280.0, GROUND_Y, k))
    parts = [(name, bone, i, painter()) for i, (name, bone, painter) in enumerate(rig_side_layers())]
    svg.transform(None)
    J = {b: (p, 280.0 + (x - 280.0) * k, GROUND_Y + (y - GROUND_Y) * k) for b, (p, x, y) in rig_joints().items()}
    return {"parts": parts, "joints": J, "label": O["label"], "height": (GROUND_Y - 160.0) * k}


# ---- the side view in z order ----------------------------------------------------------

def side_layers() -> List[Tuple[str, Callable[[], List[str]]]]:
    L = [("far-arm", s_far_arm), ("far-leg", lambda: s_leg("far")), ("near-leg", lambda: s_leg("near"))]
    if O.get("prop") == "fanfold":
        L.insert(0, ("fanfold", s_prop_behind_arm))
    L.append(("seat", s_seat))
    L.append(("shirt", s_shirt))
    L.append(("tie", s_tie_front))
    if O.get("vest"):
        L.append(("vest", s_vest))
    if O.get("cardigan"):
        L.append(("cardigan", s_cardigan))
    if O.get("jacket"):
        L.append(("jacket", s_jacket))
    if O.get("belt") == "tools":
        L.append(("tool-belt", s_tool_belt))
    L.append(("neck", s_neck))
    L.append(("head", s_head))
    if O.get("prop") == "roll":
        L.append(("roll", s_prop_behind_arm))
    if O.get("prop") == "dividers":
        L.append(("dividers", s_prop_front))
    L.append(("near-arm", s_near_arm))
    if O.get("prop") in ("square", "clipboard", "stamp"):
        # the square hangs under the fist: drawn before the arm
        if O["prop"] == "square":
            L.insert(len(L) - 1, ("square", s_prop_front))
        else:
            L.insert(len(L) - 1, (O["prop"], s_prop_front))
    return L


# ============================================================================================
# FRONT VIEW (the figure's right on screen-left)
# ============================================================================================

F_CX = 280.0
F_EYES = ((268.0, 203.5), (292.0, 203.5))


def f_shoulder_w():
    return 34.0 * O["build"]["shoulder"]


def f_arm_pts(side):
    """Shoulder, elbow, wrist of each arm (``side`` -1 = his right, screen-left)."""
    sw = f_shoulder_w()
    s = (F_CX + side * (sw - 2), 268)
    prop = O["prop"]
    if prop == "fanfold":  # both hands up at the chest, holding the top sheet by its corners
        return s, (F_CX + side * (sw + 2), 318), (F_CX + side * 24, 300)
    if prop == "clipboard" and side == -1:
        return s, (F_CX + side * (sw + 2), 316), (F_CX + side * 28, 326)
    if prop == "stamp" and side == -1:
        return s, (F_CX + side * (sw + 3), 316), (F_CX + side * (sw - 8), 312)
    if prop == "dividers" and side == -1:
        return s, (F_CX + side * (sw + 6), 314), (F_CX + side * (sw + 12), 340)
    if prop == "roll" and side == -1:
        return s, (F_CX + side * (sw + 4), 314), (F_CX + side * (sw + 6), 352)
    return s, (F_CX + side * (sw + 3), 314), (F_CX + side * (sw + 4), 356)


def f_torso_pts(grow=0.0, hem=352.0, flare=0.0):
    b = O["build"]
    sw = f_shoulder_w()
    be = b["belly"]
    g = grow
    right = [(F_CX - 12, 246 - g), (F_CX - sw + 8, 254 - g), (F_CX - sw - 1 - g, 266), (F_CX - sw + 1 - g, 292), (F_CX - sw + 6 - be * 0.55 - g, 322)]
    if O.get("female"):
        right[4] = (F_CX - sw + 9 - g, 320)
    if hem > 356:
        right += [(F_CX - sw + 6 - be * 0.5 - g, 346), (F_CX - sw + 5 - g - flare, hem, True)]
    else:
        right += [(F_CX - sw + 7 - be * 0.6 - g, hem, True)]
    return right + mx(right[::-1])


def f_leg(side):
    hx = F_CX + side * 12
    hip, knee, ankle = (hx, 352), (hx - side * 0.5, 418), (hx - side * 1.5, 484)
    wh, wk, wa = trouser_widths()
    d = leg_shape(hip, knee, (ankle[0], ankle[1] - 3), wh, wk, wa)
    items = [line([(ankle[0] + side * 4, 380), (ankle[0] + side * 3, 470)], O["trouser_sh"], 1.0)]
    out = C(d, "trouser", items, s=4)
    return out + f_shoe(ankle)


def f_shoe(ankle):
    ax, ay = ankle
    g = GROUND_Y
    top = ay - 8 if O.get("shoe") == "boot" else ay - 1
    d = smooth([(ax - 9, top), (ax + 9, top), (ax + 10.5, ay + 8), (ax + 11.5, g - 3), (ax + 10, g, True), (ax - 10, g, True), (ax - 11.5, g - 3),
                (ax - 10.5, ay + 8)])
    items = [line([(ax - 11, g - 3.5), (ax + 11, g - 3.5)], O["shoec_sh"], 1.4), ellipse(ax + 3, ay + 9, 3.4, 2.0, O["shoec_lt"])]
    if O.get("shoe") == "oxford":
        items.append(line([(ax - 4, ay + 3), (ax + 4, ay + 3)], O["shoec_sh"], 1.0))
    return C(d, "shoec", items, s=3)


def f_seat():
    f_shoulder_w()
    be = O["build"]["belly"]
    d = smooth([(F_CX - 27 - be * 0.5, 330), (F_CX + 27 + be * 0.5, 330), (F_CX + 27, 364), (F_CX, 372), (F_CX - 27, 364)])
    return C(d, "trouser", [line([(F_CX, 352), (F_CX, 372)], O["trouser_sh"], 1.0)], s=4,
             edges=[[(F_CX - 27 - be * 0.5, 332), (F_CX - 27, 364)], [(F_CX + 27 + be * 0.5, 332), (F_CX + 27, 364)]])


def f_shirt():
    items = [line([(F_CX, 258), (F_CX, 350)], O["shirt_sh"], 1.0)]
    items += [ellipse(F_CX, y, 1.5, 1.5, "#dcd6ca", INK, 0.5) for y in (272, 290, 308, 326)]
    return C(smooth(f_torso_pts(0, 352)), "shirt", items, s=5)


def f_tie():
    n = O.get("neck")
    out = []
    if n in ("bowtie", "tie", "collar"):
        for sgn in (-1, 1):
            out += C(smooth([(F_CX, 258), (F_CX + sgn * 12, 248), (F_CX + sgn * 14, 256), (F_CX + sgn * 6, 264)]), "shirt", [], s=2)
    if n == "bowtie":
        for sgn in (-1, 1):
            out += C(smooth([(F_CX, 262), (F_CX + sgn * 11, 256), (F_CX + sgn * 12, 268), (F_CX, 264)]), "tie", [], s=1.5)
        out += C(rect(F_CX - 3, 258.5, F_CX + 3, 266), "tie", [], s=1)
    if n == "tie":
        be = O["build"]["belly"]
        out += C(smooth([(F_CX - 4, 258), (F_CX + 4, 258), (F_CX + 3, 266), (F_CX - 3, 266)]), "tie", [], s=1)
        out += C(smooth([(F_CX - 3, 266), (F_CX + 3, 266), (F_CX + 6.5, 300 + be), (F_CX, 308 + be, True), (F_CX - 6.5, 300 + be)]), "tie",
                 [line([(F_CX + 1, 270), (F_CX + 3, 298 + be)], O["tie_lt"], 1.0)], s=1.6)
    if n == "open":
        for sgn in (-1, 1):
            out += C(smooth([(F_CX + sgn * 2, 274), (F_CX + sgn * 13, 248), (F_CX + sgn * 17, 256), (F_CX + sgn * 8, 270)]), "shirt", [], s=2)
        out = C(smooth([(F_CX - 7, 254), (F_CX + 7, 254), (F_CX, 276)]), "skin", [], s=2) + out
    if O.get("badge"):
        out += [line([(F_CX - 8, 254), (F_CX - 2, 296)], O["lanyard"], 1.6), line([(F_CX + 8, 254), (F_CX + 2, 296)], O["lanyard"], 1.6)]
        out += cel(rect(F_CX - 6, 294, F_CX + 6, 310), WHITE, "#c9c4b8", None,
                   [path(rect(F_CX - 4, 297, F_CX + 1, 303), "#7a8aa0"), line([(F_CX - 4, 306), (F_CX + 4, 306)], "#666", 0.7)], s=1.2, sw=1.2)
    return out


def f_vest():
    v = O["vest"]
    O["vestc"], O["vestc_sh"], O["vestc_lt"] = v["color"], tone(v["color"], 0.72), tone(v["color"], 1.2)
    hem = v["hem"]
    pts = f_torso_pts(1.5, hem)
    # open in a V from the collar to the first button
    n = len(pts) // 2
    right, left = pts[:n], pts[n:]
    vdepth = 284 if not v.get("hivis") else 270
    right[0] = (F_CX - 12, 252)
    left[-1] = (F_CX + 12, 252)
    if v.get("pointed"):
        right[-1] = (right[-1][0], hem, True)
        left[0] = (left[0][0], hem, True)
        pts = right + [(F_CX - 4, hem + 8, True), (F_CX, hem + 2), (F_CX + 4, hem + 8, True)] + left + [(F_CX, vdepth, True)]
    else:
        pts = right + left + [(F_CX + 3, vdepth, True), (F_CX - 3, vdepth, True)]
    items = []
    if v.get("hivis"):
        sw = f_shoulder_w()
        for y in (300, 326):
            items.append(path(quad([(F_CX - sw - 10, y), (F_CX + sw + 10, y), (F_CX + sw + 10, y + 7), (F_CX - sw - 10, y + 7)]), O["hivis_band"]))
        items += [path(quad([(F_CX - 20, 252), (F_CX - 14, 252), (F_CX - 14, 300), (F_CX - 20, 300)]), O["hivis_band"]),
                  path(quad([(F_CX + 14, 252), (F_CX + 20, 252), (F_CX + 20, 300), (F_CX + 14, 300)]), O["hivis_band"])]
        items.append(line([(F_CX, 272), (F_CX, hem)], tone(O["vestc"], 0.6), 1.2))
    else:
        items += [ellipse(F_CX + 3.5, y, 1.8, 1.8, O["brass"], INK, 0.6) for y in range(int(vdepth) + 6, int(hem) - 4, 12)]
        items += [line([(F_CX - 22, 316), (F_CX - 10, 316)], O["vestc_sh"], 1.4), line([(F_CX + 10, 316), (F_CX + 22, 316)], O["vestc_sh"], 1.4)]
    if v.get("watch"):
        items += [line([(F_CX + 3, 318), (F_CX + 12, 324), (F_CX + 20, 318)], O["brass"], 1.4)]
    return C(smooth(pts), "vestc", items, s=5)


def f_jacket():
    j = O["jacket"]
    hem = j["hem"]
    pts = f_torso_pts(2.5, hem, flare=2)
    n = len(pts) // 2
    right, left = pts[:n], pts[n:]
    items = []
    if j.get("lapel"):
        # open from the collar to the button: two lapels and the shirt between
        right[0] = (F_CX - 13, 248)
        left[-1] = (F_CX + 13, 248)
        body = smooth(right + [(F_CX - 2, hem, True), (F_CX + 2, hem, True)] + left)
        items += [ellipse(F_CX + 3, y, 2.0, 2.0, tone(O["jk"], 0.6), INK, 0.6) for y in (322, 342)[: j.get("buttons", 2)]]
        items += [line([(F_CX, 316), (F_CX + 2, hem)], INK, 1.2), line([(F_CX - 26, 356), (F_CX - 10, 356)], INK, 1.0),
                  line([(F_CX + 10, 356), (F_CX + 26, 356)], INK, 1.0), line([(F_CX + 12, 284), (F_CX + 24, 284)], INK, 1.0)]
        items.append(path(smooth([(F_CX + 15, 284), (F_CX + 18, 279), (F_CX + 21, 284)]), O["shirt"], INK, 0.7))
        out = C(body, "jk", items, s=6)
        # the shirt and tie in the V, over the body; then the lapels over them
        vee = smooth([(F_CX - 13, 248, True), (F_CX + 13, 248, True), (F_CX, 316, True)])
        out += C(vee, "shirt", [], s=2)
        out += f_tie()
        for sgn in (-1, 1):
            lap = smooth([(F_CX + sgn * 13, 247, True), (F_CX + sgn * 20, 252), (F_CX + sgn * 21, 266, True), (F_CX + sgn * 14, 272, True),
                          (F_CX + sgn * 1.5, 316, True), (F_CX + sgn * 6, 286)])
            out += cel(lap, O["jk_lt"], O["jk"], None, [], s=1.5)
        return out
    if j.get("uniform"):
        items += [line([(F_CX, 258), (F_CX, hem)], INK, 1.1)]
        items += [ellipse(F_CX + 3, y, 1.8, 1.8, "#2c2a24", INK, 0.5) for y in (274, 294, 314, 360)]
        for sgn in (-1, 1):
            items += [path(quad([(F_CX + sgn * 8, 280), (F_CX + sgn * 24, 280), (F_CX + sgn * 24, 298), (F_CX + sgn * 8, 298)]), O["jk_sh"]),
                      path(quad([(F_CX + sgn * 7, 278), (F_CX + sgn * 25, 278), (F_CX + sgn * 24, 285), (F_CX + sgn * 16, 287), (F_CX + sgn * 8, 285)]),
                           O["jk"], INK, 1.0)]
        out = C(smooth(pts), "jk", items, s=6)
        # the standing collar
        out += C(smooth([(F_CX - 14, 244), (F_CX + 14, 244), (F_CX + 15, 256), (F_CX + 2, 260), (F_CX - 2, 260), (F_CX - 15, 256)]), "jk",
                 [line([(F_CX, 250), (F_CX, 260)], INK, 1.0)], s=2)
        O["build"]["belly"]
        sw = f_shoulder_w()
        out += cel(quad([(F_CX - sw + 5, 340), (F_CX + sw - 5, 340), (F_CX + sw - 5, 347), (F_CX - sw + 5, 347)]), "#2c2a24", "#1b1a16", None,
                   [path(rect(F_CX - 5, 339, F_CX + 5, 348), "none", O["brass"], 1.6)], s=1)
        return out
    return C(smooth(pts), "jk", items, s=6)


def f_cardigan():
    c = O["cardigan"]
    O["card"], O["card_sh"], O["card_lt"] = c["color"], tone(c["color"], 0.74), tone(c["color"], 1.18)
    hem = c["hem"]
    pts = f_torso_pts(2.5, hem, flare=1.5)
    n = len(pts) // 2
    right, left = pts[:n], pts[n:]
    out = []
    for half, sgn in ((right, -1), (left, 1)):
        inner = [(F_CX + sgn * 5, hem, True), (F_CX + sgn * 6, 330), (F_CX + sgn * 9, 286), (F_CX + sgn * 13, 250, True)]
        pts_h = half + inner if sgn == -1 else inner[::-1] + half
        items = [path(quad([(F_CX - 40, hem - 9), (F_CX + 40, hem - 9), (F_CX + 40, hem + 2), (F_CX - 40, hem + 2)]), O["card_sh"]),
                 line([(F_CX - 40, hem - 9), (F_CX + 40, hem - 9)], INK, 0.8),
                 line([(F_CX + sgn * 6.5, hem - 9), (F_CX + sgn * 7, 330), (F_CX + sgn * 10, 286), (F_CX + sgn * 14, 252)], O["card_lt"], 2.4),
                 path(quad([(F_CX + sgn * 12, 350), (F_CX + sgn * 28, 350), (F_CX + sgn * 28, 372), (F_CX + sgn * 12, 372)]), O["card_sh"]),
                 line([(F_CX + sgn * 12, 350), (F_CX + sgn * 28, 350)], INK, 0.8)]
        items += [line([(x, hem - 8), (x, hem)], tone(O["card"], 0.6), 0.7) for x in range(int(F_CX - 40), int(F_CX + 40), 4)]
        if sgn == -1:
            items += [ellipse(F_CX - 7.5, y, 1.6, 1.6, "#d8cfbd", INK, 0.5) for y in (300, 322, 344)]
        out += C(smooth(pts_h), "card", items, s=6)
    return out


def f_belt():
    sw = f_shoulder_w()
    O["build"]["belly"]
    y = 344
    d = quad([(F_CX - sw + 6, y), (F_CX + sw - 6, y), (F_CX + sw - 6, y + 7), (F_CX - sw + 6, y + 7)])
    out = cel(d, O["leather"], O["leather_sh"], O["leather_lt"], [path(rect(F_CX - 5, y - 1, F_CX + 5, y + 8), "none", O["steel"], 1.6)], s=1.5)
    if O.get("belt") == "tools":
        # the pouch on her right hip, the folding rule and pencil in it
        px = F_CX - sw + 6
        rule = quad([(px + 2, 330), (px + 10, 330), (px + 10, 352), (px + 2, 352)])
        out += cel(rule, O["rule"], O["rule_sh"], None, [line([(px + 3, 336), (px + 9, 336)], INK, 0.6), line([(px + 3, 342), (px + 9, 342)], INK, 0.6)], s=1.5)
        out += cel(capsule((px + 15, 334), (px + 15, 350), 1.6, 1.6), O["pencil"], O["pencil_sh"], None, [], s=0.8, sw=1.2)
        pouch = smooth([(px - 4, 350), (px + 22, 350), (px + 23, 382), (px + 18, 388, True), (px - 1, 388, True), (px - 5, 380)])
        out += cel(pouch, O["leather"], O["leather_sh"], O["leather_lt"],
                   [path(quad([(px - 5, 350), (px + 23, 350), (px + 22, 362), (px - 4, 362)]), O["leather_sh"]), line([(px - 4, 362), (px + 22, 362)], INK, 0.9)], s=3)
    return out


def f_neck():
    dx, dy = head_shift()
    svg.DY = dy * 0.6
    w = 11.0 if O.get("female") else 12.5
    out = C(capsule((F_CX, 230), (F_CX, 258), w, w), "skin", [line([(F_CX - 4, 246), (F_CX + 4, 246)], O["skin_sh"], 0.9)], s=4)
    svg.DY = 0.0
    return out


def f_face_pts():
    """The front face from the look's numbers: half-widths at the temples, the
    cheekbones, the jaw and the chin; ``fw`` narrows it all, ``jaw`` narrows the
    lower face."""
    f = O["ffront"]
    fw, jw = f.get("fw", 1.0), f.get("jaw", 1.0)
    cy = 248.5 + O["face"].get("jaw", 0.0)
    half = [(25, 178), (27, 192), (27.6, 206), (26.4, 220), (23 * jw, 232), (16 * jw, 241), (8 * jw, cy - 2)]
    right = [(F_CX - w * fw, y) for w, y in half]
    pts = right + [(F_CX, cy)] + mx(right[::-1]) + [(F_CX + 24 * fw, 171), (F_CX, 167.5), (F_CX - 24 * fw, 171)]
    return pts, fw, cy


def f_head():
    dx, dy = head_shift()
    svg.DY = dy
    out = f_head_inner()
    svg.DY = 0.0
    return out


def f_head_inner():
    sk, dk = O["skin_sh"], O["skin_dk"]
    pts, fw, cy = f_face_pts()
    f = O["face"]
    out = []
    if O.get("hair") == "knot":
        out += C(smooth([(F_CX - 30, 190), (F_CX - 26, 172), (F_CX, 162), (F_CX + 26, 172), (F_CX + 30, 190), (F_CX + 24, 214), (F_CX - 24, 214)]), "hr", [], s=3)
    if O.get("hair") == "bun_cap":
        out += C(smooth([(F_CX - 28, 192), (F_CX - 26, 176), (F_CX + 26, 176), (F_CX + 28, 192), (F_CX + 24, 214), (F_CX - 24, 214)]), "hr", [], s=3)
    # the ears
    for sgn in (-1, 1):
        ex = F_CX + sgn * 27.5 * fw
        ear = smooth([(ex - sgn * 1, 197), (ex + sgn * 4.5, 195), (ex + sgn * 6.5, 205), (ex + sgn * 4.5, 217), (ex - sgn * 0.5, 217)])
        out += C(ear, "skin", [line([(ex + sgn * 2, 200), (ex + sgn * 4.2, 206), (ex + sgn * 2.4, 212)], dk, 1.0)], s=2)
    if O.get("female"):  # small gold studs in the lobes
        for sgn in (-1, 1):
            out.append(ellipse(F_CX + sgn * 29.2 * fw, 216.5, 1.7, 1.7, O["brass_lt"], INK, 0.8))
    (rx, ry), (lx, ly) = F_EYES
    tip_y = 199 + f.get("nose", (11, 17))[1] + 1.0
    ml = 232.0 + f.get("mouth", 0.0)
    nw = 6.0 + f.get("bulb", 0.0) * 0.8
    items = [
        path(smooth([(F_CX - 27 * fw, 208), (F_CX - 24 * fw, 226), (F_CX - 14, 241), (F_CX - 2, cy - 1), (F_CX - 12, 236), (F_CX - 21 * fw, 222)]), sk),
        # the nose: the bridge's shade on his right, the light on his left, the wings and nostrils
        line([(F_CX - 3.4, 204), (F_CX - 4.6, tip_y - 4)], sk, 1.6), line([(F_CX + 3.0, 204), (F_CX + 3.8, tip_y - 5)], O["skin_lt"], 1.4),
        line([(F_CX - nw, tip_y - 2), (F_CX - nw + 0.6, tip_y + 2.6), (F_CX - 2.4, tip_y + 3.8), (F_CX, tip_y + 4.4), (F_CX + 2.4, tip_y + 3.8),
              (F_CX + nw - 0.6, tip_y + 2.6), (F_CX + nw, tip_y - 2)], INK, 1.1),
        ellipse(F_CX - 2.8, tip_y + 2.6, 1.3, 0.7, dk), ellipse(F_CX + 2.8, tip_y + 2.6, 1.3, 0.7, dk),
        ellipse(F_CX + 0.8, tip_y - 0.6, 2.0, 1.4, O["skin_lt"]),
        # the mouth: a firm line, the lower lip's shade, the groove under it
        line([(F_CX - 8.0, ml + 0.4), (F_CX - 3, ml - 0.4), (F_CX + 3, ml - 0.4), (F_CX + 8.0, ml + 0.4)], INK, 1.4),
        path(smooth([(F_CX - 5.5, ml + 1.6), (F_CX + 5.5, ml + 1.6), (F_CX + 3.5, ml + 4.4), (F_CX - 3.5, ml + 4.4)]), O["lip"]),
        line([(F_CX - 3, ml + 7.5), (F_CX + 3, ml + 7.5)], dk, 0.9),
        line([(F_CX - nw - 1, tip_y + 1), (F_CX - nw - 3.5, ml - 2), (F_CX - 8.6, ml + 2)], sk if f.get("lines", 1) < 2 else dk, 0.95),
        line([(F_CX + nw + 1, tip_y + 1), (F_CX + nw + 3.5, ml - 2), (F_CX + 8.6, ml + 2)], sk if f.get("lines", 1) < 2 else dk, 0.95),
    ]
    if O.get("blush"):
        items += [ellipse(F_CX - 15, 222, 5.5, 3.6, O["blush"]), ellipse(F_CX + 15, 222, 5.5, 3.6, O["blush"])]
    if O.get("female"):  # the upper lip's colour
        items.append(path(smooth([(F_CX - 7, ml), (F_CX - 2.4, ml - 2.6), (F_CX, ml - 1.8), (F_CX + 2.4, ml - 2.6), (F_CX + 7, ml), (F_CX, ml + 0.2)]), O["lip"]))
    if f.get("lines", 1) >= 2:
        items += [line([(F_CX - 9, 181), (F_CX + 9, 181)], sk, 1.0), line([(F_CX - 7, 186), (F_CX + 7, 186)], sk, 0.9)]
        for sgn in (-1, 1):
            items += [line([(F_CX + sgn * 19, 203), (F_CX + sgn * 22, 201)], dk, 0.8), line([(F_CX + sgn * 19, 206), (F_CX + sgn * 22, 207.5)], dk, 0.8)]
    if f.get("gaunt"):
        for sgn in (-1, 1):
            items.append(line([(F_CX + sgn * 21, 214), (F_CX + sgn * 17, 222), (F_CX + sgn * 17, 232)], sk, 1.6))
    if f.get("double_chin"):
        items.append(line([(F_CX - 10, cy - 2), (F_CX, cy + 0.6), (F_CX + 10, cy - 2)], sk, 1.1))
    out += C(smooth(pts), "skin", items, s=5)
    if f.get("double_chin"):
        out = C(smooth([(F_CX - 16, cy - 8), (F_CX + 16, cy - 8), (F_CX + 12, cy + 5), (F_CX, cy + 8), (F_CX - 12, cy + 5)]), "skin", [], s=2) + out
    for (x, y), sgn in ((F_EYES[0], -1), (F_EYES[1], 1)):
        out += f_eye(x, y, sgn)
    out += f_hair(fw)
    if O.get("moustache"):
        out += C(smooth([(F_CX - 9, tip_y + 6.6), (F_CX, tip_y + 4.2), (F_CX + 9, tip_y + 6.6), (F_CX + 7, tip_y + 9.4), (F_CX, tip_y + 8), (F_CX - 7, tip_y + 9.4)]),
                 "moustache", [], s=1.5, sw=1.4)
    if O.get("beard"):
        out += f_beard(fw, cy, tip_y, ml)
    if O.get("glasses"):
        out += f_glasses()
    if O.get("hat") == "hardhat":
        out += f_hardhat()
    if O.get("hat") == "eyeshade":
        out += f_eyeshade()
    if O.get("hat") == "fieldcap":
        out += f_fieldcap()
    if O.get("ear_pencil"):
        out += cel(capsule((F_CX + 26, 186), (F_CX + 34, 204), 1.8, 1.8), O["pencil"], O["pencil_sh"], None, [], s=0.8, sw=1.2)
    return out


def f_eye(x, y, sgn):
    out = [path(smooth([(x - 4.4, y + 0.4), (x, y - 2.0), (x + 4.4, y + 0.4), (x, y + 2.2)]), WHITE),
           ellipse(x - sgn * 0.3, y + 0.1, 1.7, 1.9, O["iris"]), ellipse(x - sgn * 0.3, y + 0.1, 0.8, 0.9, PUPIL),
           line([(x - 4.8, y + 0.6), (x - 1, y - 2.2), (x + 3, y - 1.8), (x + 4.8, y + 0.4)], INK, 1.5),
           line([(x - 3.2, y + 3.2), (x + 3.2, y + 3.2)], O["skin_sh"], 0.8),
           line([(x - 3.6, y - 4.0), (x + 3.6, y - 4.0)], O["skin_sh"], 0.8)]
    brow_c = tone(O.get("hair_c", "#555555"), 0.7 if O.get("hair") in ("hat_white", "combed", "fringe") else 0.75)
    by = y - 7.0
    arch = -1.2 if O.get("female") else 0.0
    pts = [(x - 5.4, by + (0.8 if sgn < 0 else 0.4)), (x, by - 0.8 + arch), (x + 5.4, by + (0.4 if sgn < 0 else 0.8))]
    out += [line(pts, brow_c, 2.6), line(pts, INK, 0.6)]
    return out


def f_hair(fw):
    h = O.get("hair")
    if h == "slick":
        d = smooth([(F_CX - 27 * fw, 200), (F_CX - 28 * fw, 180), (F_CX - 18, 164), (F_CX, 159.5), (F_CX + 18, 162), (F_CX + 28 * fw, 178), (F_CX + 27 * fw, 200),
                    (F_CX + 24 * fw, 196), (F_CX + 22, 182), (F_CX + 6, 175), (F_CX - 8, 173), (F_CX - 22, 180), (F_CX - 24 * fw, 196)])
        items = [line([(F_CX - 8, 173), (F_CX - 6, 162)], O["hr_sh"], 1.2), line([(F_CX + 4, 168), (F_CX + 18, 166)], O["hr_lt"], 1.4),
                 path(smooth([(F_CX - 27 * fw, 192), (F_CX - 24 * fw, 186), (F_CX - 24 * fw, 199)]), O["temple"]),
                 path(smooth([(F_CX + 27 * fw, 192), (F_CX + 24 * fw, 186), (F_CX + 24 * fw, 199)]), O["temple"])]
        return C(d, "hr", items, s=3)
    if h == "knot":
        d = smooth([(F_CX - 29.5 * fw, 211), (F_CX - 29 * fw, 182), (F_CX - 18, 165), (F_CX, 160), (F_CX + 18, 165), (F_CX + 29 * fw, 182), (F_CX + 29.5 * fw, 211),
                    (F_CX + 25.5 * fw, 206), (F_CX + 23, 186), (F_CX + 1, 173, True), (F_CX - 23, 186), (F_CX - 25.5 * fw, 206)])
        items = [line([(F_CX - 4, 166), (F_CX - 16, 176), (F_CX - 24, 190)], O["streak"], 2.2), line([(F_CX + 6, 168), (F_CX + 20, 180)], O["hr_lt"], 1.1),
                 line([(F_CX, 161), (F_CX + 1, 172)], O["hr_sh"], 1.0)]
        return C(d, "hr", items, s=3)
    if h == "hat_white":
        out = []
        for sgn in (-1, 1):
            out += C(smooth([(F_CX + sgn * 23 * fw, 186), (F_CX + sgn * 29 * fw, 188), (F_CX + sgn * 29 * fw, 204), (F_CX + sgn * 25 * fw, 202)]), "hr", [], s=2)
        return out
    if h == "fringe":
        out = [line([(F_CX - 8, 174), (F_CX + 6, 172)], O["skin_lt"], 2.2)]
        for sgn in (-1, 1):
            out += C(smooth([(F_CX + sgn * 22 * fw, 184), (F_CX + sgn * 29 * fw, 186), (F_CX + sgn * 30 * fw, 200), (F_CX + sgn * 27 * fw, 206),
                             (F_CX + sgn * 25 * fw, 196)]), "hr", [line([(F_CX + sgn * 27 * fw, 190), (F_CX + sgn * 28 * fw, 200)], O["hr_sh"], 0.9)], s=2)
        return out
    if h == "bun_cap":
        out = []
        for sgn in (-1, 1):
            out += C(smooth([(F_CX + sgn * 18, 184), (F_CX + sgn * 27 * fw, 186), (F_CX + sgn * 27 * fw, 200), (F_CX + sgn * 24 * fw, 196)]), "hr", [], s=2)
        return out
    if h == "combed":
        d = smooth([(F_CX - 27 * fw, 198), (F_CX - 28 * fw, 180), (F_CX - 18, 164), (F_CX, 161), (F_CX + 18, 164), (F_CX + 28 * fw, 180), (F_CX + 27 * fw, 198),
                    (F_CX + 25 * fw, 190), (F_CX + 20, 176), (F_CX + 8, 170), (F_CX - 8, 170), (F_CX - 20, 176), (F_CX - 25 * fw, 190)])
        items = [line([(F_CX - 14, 168), (F_CX + 10, 165)], O["hr_lt"], 1.0), line([(F_CX - 18, 172), (F_CX - 22, 186)], O["hr_sh"], 0.9)]
        return C(d, "hr", items, s=3)
    return []


def f_beard(fw, cy, tip_y, ml):
    d = smooth([(F_CX - 26 * fw, 214), (F_CX - 22, 226), (F_CX - 12, 230), (F_CX - 9, ml + 4), (F_CX, ml + 6), (F_CX + 9, ml + 4), (F_CX + 12, 230),
                (F_CX + 22, 226), (F_CX + 26 * fw, 214), (F_CX + 25, 232), (F_CX + 16, 246), (F_CX, cy + 6), (F_CX - 16, 246), (F_CX - 25, 232)])
    items = [line([(F_CX - 16, 236), (F_CX - 8, 248)], O["hr_sh"], 1.0), line([(F_CX + 8, 248), (F_CX + 16, 236)], O["hr_sh"], 1.0),
             line([(F_CX + 14, 230), (F_CX + 20, 238)], O["hr_lt"], 1.2)]
    out = C(d, "hr", items, s=3)
    out += C(smooth([(F_CX - 12, tip_y + 7), (F_CX, tip_y + 4.4), (F_CX + 12, tip_y + 7), (F_CX + 10, ml + 1), (F_CX, ml - 1), (F_CX - 10, ml + 1)]), "hr", [], s=1.5, sw=1.4)
    out += [line([(F_CX - 4, ml + 1.8), (F_CX + 4, ml + 1.8)], INK, 1.2)]
    return out


def f_glasses():
    g = O["glasses"]
    (rx, ry), (lx, ly) = F_EYES
    if g == "round":
        out = []
        for x in (rx, lx):
            out.append(ellipse(x, ry + 0.4, 7.4, 7.0, "#e8eef2", INK, 2.6).replace('fill="#e8eef2"', 'fill="#e8eef2" fill-opacity="0.18"'))
        out += [line([(rx + 7.4, ry - 1), (F_CX, ry - 2.6), (lx - 7.4, ly - 1)], INK, 2.0),
                line([(rx - 7.4, ry - 1), (F_CX - 27, 200)], INK, 2.0), line([(lx + 7.4, ly - 1), (F_CX + 27, 200)], INK, 2.0)]
        return out
    if g == "specs":
        out = []
        for x in (rx, lx):
            out.append(path(rect(x - 5.6, ry - 3.4, x + 5.6, ry + 3.6), "none", "#5a4a3a", 1.4))
        out += [line([(rx + 5.6, ry - 1), (F_CX, ry - 2), (lx - 5.6, ly - 1)], "#5a4a3a", 1.2)]
        return out
    if g == "halfmoon":
        out = []
        for x in (rx, lx):
            out.append(path(smooth([(x - 6.4, ry + 3.6, True), (x + 6.4, ry + 3.6, True), (x + 5.2, ry + 8.4), (x, ry + 9.6), (x - 5.2, ry + 8.4)]), "none", "#9a8a5a", 1.4))
        out += [line([(rx + 6.4, ry + 4.0), (F_CX, ry + 2.6), (lx - 6.4, ly + 4.0)], "#9a8a5a", 1.2),
                line([(rx - 6.4, ry + 4), (F_CX - 30, 222), (F_CX - 22, 252)], "#b8a870", 0.9),
                line([(lx + 6.4, ly + 4), (F_CX + 30, 222), (F_CX + 22, 252)], "#b8a870", 0.9)]
        return out
    return []


def f_hardhat():
    dome = smooth([(F_CX - 30, 184), (F_CX - 29, 164), (F_CX - 18, 148), (F_CX, 143), (F_CX + 18, 148), (F_CX + 29, 164), (F_CX + 30, 184)])
    items = [path(quad([(F_CX - 4, 143), (F_CX + 4, 143), (F_CX + 4, 184), (F_CX - 4, 184)]), O["ht_sh"]), line([(F_CX + 10, 150), (F_CX + 22, 160)], WHITE, 1.6)]
    out = C(dome, "ht", items, s=4)
    brim = smooth([(F_CX - 36, 186, True), (F_CX - 30, 180), (F_CX + 30, 180), (F_CX + 36, 186, True), (F_CX + 30, 191), (F_CX - 30, 191)])
    return out + C(brim, "ht", [], s=2)


def f_eyeshade():
    O["shade_g"], O["shade_g_sh"], O["shade_g_lt"] = "#3f8a5a", "#2c6a42", "#6fb586"
    out = cel(quad([(F_CX - 28, 180), (F_CX + 28, 180), (F_CX + 28, 186), (F_CX - 28, 186)]), "#2c3a30", "#1c241e", None, [], s=1, sw=1.6)
    visor = smooth([(F_CX - 28, 184, True), (F_CX + 28, 184, True), (F_CX + 34, 196, True), (F_CX - 34, 196, True)])
    out += cel(visor, O["shade_g"], O["shade_g_sh"], O["shade_g_lt"], [line([(F_CX - 24, 187), (F_CX + 24, 187)], "#a6dcb5", 1.2)], s=2)
    return out


def f_fieldcap():
    crown = smooth([(F_CX - 28, 184), (F_CX - 30, 166), (F_CX - 18, 152), (F_CX, 149), (F_CX + 18, 152), (F_CX + 30, 166), (F_CX + 28, 184)])
    items = [line([(F_CX - 26, 170), (F_CX + 26, 170)], O["ht_sh"], 1.2), line([(F_CX + 8, 154), (F_CX + 22, 160)], O["ht_lt"], 1.4)]
    out = C(crown, "ht", items, s=4)
    out += C(quad([(F_CX - 28, 176), (F_CX + 28, 176), (F_CX + 28, 185), (F_CX - 28, 185)]), "ht", [], s=1.5)
    out += cel(smooth([(F_CX - 24, 184, True), (F_CX + 24, 184, True), (F_CX + 20, 191), (F_CX - 20, 191)]), "#222", "#111", "#444", [], s=1.2)
    out += cel(smooth([(F_CX - 4, 162), (F_CX + 4, 162), (F_CX + 4, 172), (F_CX, 175), (F_CX - 4, 172)]), O["armband"], tone(O["armband"], 0.7), None, [], s=1, sw=1.2)
    return out


def f_arm(side):
    s, e, w = f_arm_pts(side)
    out = sleeve_upper(s, e, band=(side == -1)) + sleeve_lower(e, w)
    a = ang(e, w)
    prop = O["prop"]
    bent = (prop == "fanfold") or (side == -1 and prop in ("clipboard", "stamp", "dividers"))
    if bent:
        if prop == "dividers":
            out += fist(frame(w, a)(8, 0), a + 0.3, 1)
        elif prop == "stamp":
            out += fist(frame(w, a)(8, 0), -math.pi / 2, 1)
        else:
            out += fist(frame(w, a)(7, 0), a, 1)
    elif side == -1 and prop in ("square", "roll"):
        out += fist(frame(w, a)(9, 0), a + math.pi / 2, 1)
    else:
        out += hand_front(w, a, -side)
    return out


def f_prop_under():
    """Props drawn under the arms."""
    prop = O["prop"]
    s, e, w = f_arm_pts(-1)
    a = ang(e, w)
    g = frame(w, a)(9, 0)
    if prop == "square":
        top = (g[0], g[1] - 6)
        blade = quad([(top[0] - 3.5, top[1]), (top[0] + 3.5, top[1]), (top[0] + 3.5, 446), (top[0] - 3.5, 446)])
        tongue = quad([(top[0] - 3.5, 446), (top[0] - 3.5, 453), (top[0] - 30, 453), (top[0] - 30, 446)])
        ticks = [line([(top[0] + 3.5, y), (top[0] + 0.5, y)], INK, 0.6) for y in range(370, 444, 6)]
        return cel(blade, O["steel"], O["steel_sh"], O["steel_lt"], ticks, s=2) + cel(tongue, O["steel"], O["steel_sh"], O["steel_lt"], [], s=2)
    if prop == "roll":
        d = capsule((g[0], g[1] - 40), (g[0] + 4, g[1] + 46), 7.5, 7.5)
        items = [line([(g[0] - 3, g[1] - 36), (g[0], g[1] + 40)], O["roll_lt"], 1.6), line([(g[0] - 7, g[1] + 20), (g[0] + 9, g[1] + 20)], "#c9b07a", 2.4)]
        out = C(d, "roll", items, s=3)
        out += [ellipse(g[0], g[1] - 44, 7.0, 3.4, "#e9eef4", INK, 1.4), line([(g[0] - 3, g[1] - 44), (g[0] + 2, g[1] - 45)], O["roll_sh"], 0.8)]
        return out
    if prop == "dividers":
        hinge = frame(w, a)(10, 0)
        hinge = (hinge[0], hinge[1] + 2)
        legs = [((hinge[0] - 2, hinge[1] + 6), (hinge[0] - 16, GROUND_Y - 2)), ((hinge[0] + 2, hinge[1] + 6), (hinge[0] + 12, GROUND_Y - 2))]
        out = []
        for a2, b2 in legs:
            out += cel(capsule(a2, b2, 3.6, 1.6), O["brass"], O["brass_sh"], O["brass_lt"], [], s=1.5, sw=1.6)
            out += cel(capsule(lerp(a2, b2, 0.9), b2, 1.9, 0.6), O["steel"], O["steel_sh"], None, [], s=0.6, sw=1.2)
        m0, m1 = lerp(*legs[0], 0.55), lerp(*legs[1], 0.55)
        out += [line([m0, ((m0[0] + m1[0]) / 2, m0[1] + 3), m1], INK, 3.0), line([m0, ((m0[0] + m1[0]) / 2, m0[1] + 3), m1], O["brass_lt"], 1.4)]
        out += cel(smooth([(hinge[0] - 7, hinge[1] + 2), (hinge[0], hinge[1] - 8), (hinge[0] + 7, hinge[1] + 2), (hinge[0], hinge[1] + 8)]),
                   O["brass"], O["brass_sh"], O["brass_lt"], [], s=1.5, sw=1.8)
        return out
    return []


def f_prop_over():
    prop = O["prop"]
    if prop == "clipboard":
        s, e, w = f_arm_pts(-1)
        c = (F_CX - 4, 322)
        board = rect(c[0] - 18, c[1] - 26, c[0] + 18, c[1] + 26)
        out = cel(board, O["board"], O["board_sh"], O["board_lt"], [], s=2)
        rows = [line([(c[0] - 12, y), (c[0] + (12 if (y // 5) % 3 else 4), y)], "#8a8a92", 0.8) for y in range(int(c[1] - 12), int(c[1] + 20), 4)]
        out += cel(rect(c[0] - 15, c[1] - 20, c[0] + 15, c[1] + 22), O["paper"], O["paper_sh"], None, rows + [line([(c[0] - 12, c[1] - 16), (c[0] + 4, c[1] - 16)], INK, 1.0)],
                   s=1.2, sw=1.2)
        out += cel(rect(c[0] - 7, c[1] - 29, c[0] + 7, c[1] - 20), O["steel"], O["steel_sh"], O["steel_lt"], [], s=1, sw=1.4)
        return out
    if prop == "stamp":
        s, e, w = f_arm_pts(-1)
        return stamp(frame(w, ang(e, w))(8, 0))
    return []


def f_fanfold():
    out = []
    x0, x1 = F_CX - 16, F_CX + 16
    y = 296.0
    k = 0
    panels = []
    while y < 452:
        dy = 13.0
        sq = 1.5 if k % 2 else -1.5
        panels.append(((x0, y), (x1, y), (x1 + sq, y + dy), (x0 - sq, y + dy), k))
        x0, x1 = x0 - sq, x1 + sq
        y += dy
        k += 1
    for (a, b, c2, d, k) in panels:
        fill = O["paper"] if k % 2 == 0 else O["paper_sh"]
        items = [path(quad([lerp(a, d, 0.2), lerp(b, c2, 0.2), lerp(b, c2, 0.55), lerp(a, d, 0.55)]), O["green_bar"])]
        items += [ellipse(*lerp(lerp(a, d, 0.5), lerp(b, c2, 0.5), t), 0.9, 0.9, "#9a988e") for t in (0.06, 0.94)]
        out += cel(quad([a, b, c2, d]), fill, O["paper_sh"], None, items, s=1, sw=1.3)
    return stack_of_folds(F_CX, 38, 458) + out


def front_layers() -> List[Tuple[str, Callable[[], List[str]]]]:
    L = [("leg-right", lambda: f_leg(-1)), ("leg-left", lambda: f_leg(1)), ("seat", f_seat), ("neck", f_neck), ("shirt", f_shirt)]
    if not (O.get("jacket") or {}).get("lapel"):
        L.append(("tie", f_tie))
    if O.get("vest"):
        L.append(("vest", f_vest))
    if O.get("cardigan"):
        L.append(("cardigan", f_cardigan))
    if O.get("jacket"):
        L.append(("jacket", f_jacket))
    if O.get("belt") == "tools":
        L.append(("belt", f_belt))
    L.append(("head", f_head))
    if O.get("prop") in ("square", "roll", "dividers"):
        L.append(("prop", f_prop_under))
    if O.get("prop") == "fanfold":
        L.append(("fanfold", f_fanfold))
    L.append(("arm-right", lambda: f_arm(-1)))
    L.append(("arm-left", lambda: f_arm(1)))
    if O.get("prop") in ("clipboard", "stamp"):
        L.insert(len(L) - 2 if O["prop"] == "stamp" else len(L), ("prop", f_prop_over))
        if O["prop"] == "clipboard":  # the hand holds the board's edge: draw it over
            L.append(("hand-over", lambda: fist(frame(f_arm_pts(-1)[2], ang(*f_arm_pts(-1)[1:]))(7, 0), ang(*f_arm_pts(-1)[1:]), 1)))
    return L


# ============================================================================================
# OUTPUT
# ============================================================================================

VIEWS = {"side": side_layers, "front": front_layers}


def svg_text(char: str, look: str, view: str) -> str:
    use(char, look)
    _N[0] = 0
    svg.configure(dx=0, dy=0, ink=INK, ow=OW, colors={})
    svg.transform((280.0, GROUND_Y, O["k"]))
    for i, (name, painter) in enumerate(VIEWS[view]()):
        svg.part(f"{view}-{name}", name.replace("-", " ").title(), name.replace("-", "_"), "body", i, painter())
    svg.transform(None)
    title = {"architect": "Architect", "manifest_clerk": "Manifest Clerk"}[char]
    return svg.document(size=(W, H), design=f"{char}-r1-{look}", layer_id=f"{char}-{look}-{view}", label=f"{title} {look} - {view.title()}",
                        comment=[f"  <!-- CANDIDATE, NOT CAST: {title}, {O['label']} ({view}); the ground at y={GROUND_Y:g}.",
                                 "       Drawn by scripts/svg_art/architect_and_clerk_art.py. -->"],
                        joints=[])


def write_all(out: Path) -> List[Path]:
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    for char, looks in LOOKS.items():
        for look in looks:
            for view in VIEWS:
                p = out / f"{char}_{look}_{view}.svg"
                p.write_text(svg_text(char, look, view), encoding="utf8")
                paths.append(p)
    return paths


# ---- contact sheets (resvg_py + Pillow, the tool venv's) ---------------------------------

BG = (216, 221, 228)


def _render(text: str, zoom: float):
    import io
    import re
    import resvg_py
    from PIL import Image
    text = re.sub(r'width="(\d+)mm" height="(\d+)mm"', lambda m: f'width="{int(int(m.group(1)) * zoom)}" height="{int(int(m.group(2)) * zoom)}"', text, count=1)
    png = resvg_py.svg_to_bytes(svg_string=text)
    return Image.open(io.BytesIO(bytes(png))).convert("RGBA")


def _on_bg(im):
    from PIL import Image
    bg = Image.new("RGBA", im.size, BG + (255,))
    bg.alpha_composite(im)
    return bg.convert("RGB")


def _crop(im, pad=6):
    box = im.getchannel("A").getbbox()
    if not box:
        return im
    x0, y0, x1, y1 = box
    return im.crop((max(0, x0 - pad), max(0, y0 - pad), min(im.width, x1 + pad), min(im.height, y1 + pad)))


#: Game size: a 173 cm figure (k = 1) stands this many pixels tall.
GAME_PX = 96.0
#: The k = 1 figure's height in SVG units (crown 165 to the ground).
UNIT_H = GROUND_Y - 160.0


def _game(text: str, k: float):
    """The figure as the game draws it: supersampled, then downsampled to
    GAME_PX for 173 cm."""
    from PIL import Image
    z_final = GAME_PX / UNIT_H
    big = _render(text, z_final * 4)
    small = big.resize((max(1, big.width // 4), max(1, big.height // 4)), Image.LANCZOS)
    return _crop(small, 2)


def contact_sheet(char: str, out: Path) -> Path:
    from PIL import Image, ImageDraw, ImageFont
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
    rows = []
    for look in LOOKS[char]:
        side_t, front_t = svg_text(char, look, "side"), svg_text(char, look, "front")
        k = LOOKS[char][look]["k"]
        side = _crop(_render(side_t, 1.6))
        front = _crop(_render(front_t, 1.6))
        z = 4.0
        big = _render(side_t, z)
        # the head close-up: the box round the head (design units, scaled by k about the ground)
        def S(x, y):
            return ((280 + (x - 280) * k) * z, (GROUND_Y + (y - GROUND_Y) * k) * z)
        x0, y0 = S(232, 136)
        x1, y1 = S(330, 266)
        head = big.crop((int(x0), int(y0), int(x1), int(y1)))
        g_side, g_front = _game(side_t, k), _game(front_t, k)
        g2 = Image.new("RGBA", (g_side.width + g_front.width + 10, max(g_side.height, g_front.height)), (0, 0, 0, 0))
        g2.paste(g_side, (0, g2.height - g_side.height))
        g2.paste(g_front, (g_side.width + 10, g2.height - g_front.height))
        g2x = g2.resize((g2.width * 3, g2.height * 3), Image.NEAREST)
        rows.append((LOOKS[char][look]["label"], [side, front, head, g2, g2x]))
    gap = 30
    width = max(sum(im.width for im in ims) + gap * (len(ims) + 1) for _, ims in rows)
    heights = [max(im.height for im in ims) + 50 for _, ims in rows]
    sheet = Image.new("RGB", (width, sum(heights) + 20), BG)
    d = ImageDraw.Draw(sheet)
    y = 10
    for (label, ims), h in zip(rows, heights):
        d.text((gap, y), label, fill=(28, 24, 22), font=font)
        x = gap
        for im in ims:
            yy = y + 40 + (h - 50 - im.height) if im is not ims[2] else y + 40
            bg = _on_bg(im) if im.mode == "RGBA" else im
            sheet.paste(bg, (x, yy))
            x += im.width + gap
        y += h
    p = out / {"architect": "architect_r1.png", "manifest_clerk": "manifest_clerk_r1.png"}[char]
    sheet.save(p)
    return p


def pair_sheet(out: Path) -> Path:
    """Every architect beside every clerk at game size (and 3x), the heights true."""
    from PIL import Image, ImageDraw, ImageFont
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
    cells = []
    for la in LOOKS["architect"]:
        for lc in LOOKS["manifest_clerk"]:
            ims = [_game(svg_text("architect", la, "side"), 1), _game(svg_text("manifest_clerk", lc, "side"), 1)]
            cells.append((f"arch {la} + clerk {lc}", ims))
    # each pair standing on one ground line, the clerk facing the architect
    tiles = []
    for label, (a, c) in cells:
        c = c.transpose(Image.FLIP_LEFT_RIGHT)
        h = max(a.height, c.height)
        t = Image.new("RGBA", (a.width + c.width + 14, h), (0, 0, 0, 0))
        t.paste(a, (0, h - a.height))
        t.paste(c, (a.width + 14, h - c.height))
        tiles.append((label, t))
    scale = 2
    tw = max(t.width for _, t in tiles) * scale + 40
    th = max(t.height for _, t in tiles) * scale + 40
    sheet = Image.new("RGB", (tw * 3 + 20, th * 3 + 20), BG)
    d = ImageDraw.Draw(sheet)
    for i, (label, t) in enumerate(tiles):
        r, c = divmod(i, 3)
        x, y = 10 + c * tw, 10 + r * th
        d.text((x + 6, y + 2), label, fill=(28, 24, 22), font=font)
        big = t.resize((t.width * scale, t.height * scale), Image.NEAREST)
        sheet.paste(_on_bg(big), (x + 6, y + 22 + (th - 30 - big.height)))
    p = out / "pair_r1.png"
    sheet.save(p)
    return p


def main() -> None:
    if len(sys.argv) > 2 and sys.argv[1] in ("--all", "--sheets"):
        out = Path(sys.argv[2])
        for p in write_all(out / "svg" if sys.argv[1] == "--sheets" else out):
            print(p)
        if sys.argv[1] == "--sheets":
            for char in LOOKS:
                print(contact_sheet(char, out))
            print(pair_sheet(out))
        return
    raise SystemExit("usage: architect_and_clerk_art.py --all DIR | --sheets DIR   (candidates only; nothing is cast)")


if __name__ == "__main__":
    main()
