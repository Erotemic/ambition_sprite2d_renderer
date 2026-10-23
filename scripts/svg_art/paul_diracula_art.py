#!/usr/bin/env python3
"""Paul Diracula, redesigned: Paul Dirac as Count Dracula.

    uv run python scripts/svg_art/paul_diracula_art.py                # the cast drawing (look A, side view)
    uv run python scripts/build_paul_diracula_v2_rig.py               # then its rig
    uv run python scripts/svg_art/paul_diracula_art.py --all DIR      # every view of every look, to DIR
    uv run python scripts/svg_art/paul_diracula_art.py --sheet PNG    # the contact sheet of the looks

Jon, 2026-10-22: "a new Paul Diracula". Three looks were drawn (round 1).
Jon did not pick one; on 2026-10-23 he asked to see the new art in the game,
so look A (``count``) is CAST: it is the target ``paul_diracula_v2``
(``targets/characters/paul_diracula_v2.py``), drawn from
``data/characters/paul_diracula_v2/paul_diracula_v2_side.svg``, which this
script writes. The old procedural target ``paul_diracula`` stays renderable.
Looks B and C are kept here, not cast. Look A has Dirac's side parting under
the Count's widow's peak, so the parody reads as Dirac.

WHO.  ``npc_paul_diracula`` (183 cm, a MainHall scientist, a ``precision_duelist``
and ``playable_candidate``): "I vant to annihilate your positron", "Symmetry.
Always symmetry", "I speak rarely". In the Hall he answers "Hello?" with
"Hello." His moves (the old target's rows) are ``delta_spike``, ``dirac_sea``,
``pair_creation``, ``spinor_turn`` and ``vacuum_step``: so the design carries
the Dirac sea, a particle and its mirror, and stays clean enough for sparse
geometric effects to read over him.

THE PARODY READS AS ITS PERSON.  Dirac first: a tall, very thin man, a long
narrow face with a high forehead, dark hair combed straight back, a long
straight nose, a small closed mouth that says nothing, deep-set small eyes, a
1930s suit worn stiffly. Dracula on top, never instead: the pallor, a widow's
peak, shadowed sockets, two small fangs over the lower lip, and a cape with a
tall standing collar lined in a second colour.

THE LOOKS.
* ``count`` (A): Lugosi's evening dress on Dirac's frame -- a black tailcoat,
  white tie, and the medallion on its ribbon, here a ``psi``; the opera cape
  lined in crimson.
* ``sea`` (B): the Dirac sea -- a midnight suit, and the cape's lining is the
  sea: a dark field of filled states with one bright HOLE in it, the positron.
  The clasp is a pair, a filled disc chained to an empty ring. Gloves are a
  pair too: one white, one black.
* ``inverness`` (C): the most Dirac -- a grey 1930s three-piece suit, a plain
  dark tie, and over it a 1930s Inverness cape-coat, its capelet lined in
  oxblood, its collar turned up like a vampire's. A stub of chalk in his hand;
  his collar pins are a bra and a ket.

House style: Oiler's (``oiler_art.py``): thin warm ink, flat cel fills with
one shade band (below-left) and one light band (above-right), adult
proportions, small eyes. No drop shadow. No lettering: the glyphs (psi, the
bra-ket) are drawn as paths.
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
from svgkit import capsule, ellipse, line, part, path, smooth  # noqa: E402

W = H = 560
INK = "#1b1519"
OW = 1.5
GROUND_Y = 502.0
#: Shade down-left, light up-right.
SD, LD = (-1.0, 0.6), (1.0, -0.8)

BASE = dict(
    # the pallor: a cool grey-violet shade, never green
    skin="#e3d9d3", skin_sh="#b8a8ad", skin_lt="#f1ebe6", skin_dk="#86737c", socket="#b29ea8", lip="#9c6f74", lip_dk="#6e4049",
    fang="#fbfaf6",
    hair="#25222b", hair_sh="#151318", hair_lt="#46424f",
    shirt="#f8f6f1", shirt_sh="#cfc9bf", shirt_lt="#ffffff",
    shoe="#1c1a1f", shoe_sh="#0e0d10", shoe_lt="#3c3942",
    iris="#3a3036",
    glove_near="skin", glove_far="skin",
)
LOOKS: Dict[str, Dict] = {
    "count": dict(
        label="A: the Count (evening dress, opera cape, psi medallion)",
        coat="#26232c", coat_sh="#16141a", coat_lt="#3d3946",
        vest="#f8f6f1", vest_sh="#cfc9bf", vest_lt="#ffffff",
        trouser="#26232c", trouser_sh="#16141a", trouser_lt="#3d3946",
        cape="#1d1a21", cape_sh="#0f0d12", cape_lt="#34303b",
        lining="#9a2232", lining_sh="#6a1522", lining_lt="#bd3a4a",
        tie="white_bow", coat_kind="tails", cape_kind="opera", jewel="psi_medallion", hair_kind="peak_part",
    ),
    "sea": dict(
        label="B: the Dirac Sea (lining full of states, one hole; a pair of gloves)",
        coat="#232a40", coat_sh="#151a2a", coat_lt="#36405e",
        vest="#232a40", vest_sh="#151a2a", vest_lt="#36405e",
        trouser="#232a40", trouser_sh="#151a2a", trouser_lt="#36405e",
        cape="#181b26", cape_sh="#0c0e15", cape_lt="#2a2f40",
        lining="#1d3e6a", lining_sh="#122a4c", lining_lt="#2b5488", state="#7fb8e6", hole="#f2e7a0",
        tie="red_tie", tie_c="#a3263a", tie_sh="#701828",
        coat_kind="suit", cape_kind="sea", jewel="pair_clasp", hair_kind="peak",
        glove_near="#f1efe9", glove_far="#1e1c22",
    ),
    "inverness": dict(
        label="C: the Lecturer (Dirac's grey suit and parting, Inverness cape-coat, bra-ket collar pins)",
        coat="#5d5c63", coat_sh="#43424a", coat_lt="#77767e",
        vest="#5d5c63", vest_sh="#43424a", vest_lt="#77767e",
        trouser="#5d5c63", trouser_sh="#43424a", trouser_lt="#77767e",
        cape="#2b2a31", cape_sh="#1b1a20", cape_lt="#403f48",
        lining="#7a2430", lining_sh="#541621", lining_lt="#953543",
        tie="dark_tie", tie_c="#4a3a46", tie_sh="#33272f",
        coat_kind="suit", cape_kind="inverness", jewel="braket", hair_kind="part",
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
    return f"dra{tag}{_N[0]}"


# ---- the cel shader of oiler_art.py (copied) ----------------------------------------------

def cel(d, base, shade, light=None, items=(), sdir=SD, ldir=LD, s=5.0, l=3.0, sw=None, ink=None, edges=None):
    """A shape: its fill, a ``shade`` band along the edges facing ``sdir`` and a
    ``light`` band along those facing ``ldir`` (clipped inside), the detail
    ``items``, then the ink outline (or ink on the open runs ``edges`` only)."""
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


def mx(pts, cx=280.0):
    """Mirror points across ``x = cx``."""
    return [(2 * cx - p[0], p[1]) + tuple(p[2:]) for p in pts]


def tube(a, b, r0, r1, key, near=True, s=4, items=(), open_end=True):
    """A limb piece from ``a`` to ``b``: a capsule inked along its two sides and
    round its top cap only, so where it overlaps the next piece (drawn under
    it) the joint shows no seam."""
    q = frame(a, ang(a, b))
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    top = [q(-r0 * math.sin(th), r0 * math.cos(th)) for th in [math.pi * i / 10 for i in range(11)]]
    if open_end:  # a flat, uninked end buried in the next piece: no cap to catch a shade band
        d = svg.poly(top[::-1] + [q(L + r1 * 0.6, r1), q(L + r1 * 0.6, -r1)])
        edges = [[q(0, -r0), q(L + r1 * 0.6, -r1)], [q(0, r0), q(L + r1 * 0.6, r1)], top]
    else:
        d, edges = capsule(a, b, r0, r1), None
    if near:  # shade and light across the limb only, so no band curls round the open end
        return cel(d, O[key], O[key + "_sh"], O.get(key + "_lt"), items, s=s, edges=edges, sdir=(-1.0, 0.0), ldir=(1.0, 0.0))
    return cel(d, O[key + "_sh"], O[key + "_sh"], None, items, s=1, edges=edges)


def rect(x0, y0, x1, y1):
    return smooth([(x0, y0, True), (x1, y0, True), (x1, y1, True), (x0, y1, True)])


# ---- hands (oiler_art.py's, longer and thinner: a precise man's fingers) --------------------

HAND = 1.12


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


def hand_colors(which):
    key = O["glove_" + which]
    if key == "skin":
        return O["skin"], O["skin_sh"], O["skin_lt"], O["skin_dk"]
    if key == "#1e1c22":
        return key, "#0f0e12", "#3a3742", "#0a090c"
    return key, "#c9c4bb", "#ffffff", "#9d978c"


def hand_side(wrist, a, near=True, which="near", chalk=False):
    """A hand hanging from ``wrist`` along ``a``: the thumb, four long fingers
    curling a little forward, the back of the hand inked where it is not joined
    to the cuff.  With ``chalk``, a stub of chalk held between thumb and index."""
    q = frame(wrist, a)
    p = lambda t, f: q(HAND * t, -HAND * f)
    sk, sh, lt, dk = hand_colors(which)
    if not near:
        lt = None
    fine = 1.3
    out = []
    thumb = finger(p(4, 5.0), p(11, 8.4), p(16.5, 8.8), 3.0 * HAND, 2.5 * HAND, 1.9 * HAND)
    out += cel(thumb, sk, sh, lt, [], s=1.6, sw=fine)
    for f0, length, curl in ((-4.6, 14.5, 2.4), (-1.5, 17.5, 3.4), (1.6, 18.5, 4.2), (4.6, 16.0, 4.6)):
        fing = finger(p(10, f0), p(10 + length * 0.55, f0 + curl * 0.3), p(10 + length, f0 + curl), 1.9 * HAND, 1.7 * HAND, 1.45 * HAND)
        out += cel(fing, sk, sh, lt if f0 > 4 else None, [], s=1.0, sw=fine)
    run = [p(-1, -6.0), p(6, -6.6), p(11, -6.2), p(13.5, -2.6), p(14, 2), p(13, 6.0), p(7, 6.6), p(-1, 6.2)]
    palm = smooth([p(-3, -6.0)] + run + [p(-3, 6.0)])
    items = [line([p(4, -2.2), p(9.5, -2.8)], sh, 0.8), line([p(4, 1.5), p(9.5, 1.5)], sh, 0.8)]
    out += cel(palm, sk, sh, lt, items, s=2.5, edges=[run])
    if chalk:  # pinched between the thumb and the index, poking forward
        out += cel(capsule(p(13, 7), p(16, 17), 2.4, 2.4), "#f6f3ea", "#cfcabd", None, [], s=1, sw=1.3)
    return out


def hand_front(wrist, a, inward, which="near"):
    """A relaxed hand at his side seen from the front, the back of it edge-on."""
    q = frame(wrist, a)
    p = lambda t, i: q(HAND * t, -HAND * i * inward)
    sk, sh, lt, dk = hand_colors(which)
    fine = 1.3
    out = []
    for i0, length, curl in ((3.0, 15.0, 3.0), (1.3, 16.5, 3.4)):
        out += cel(finger(p(9, i0), p(9 + length * 0.6, i0 + curl * 0.4), p(9 + length, i0 + curl), 1.9 * HAND, 1.8 * HAND, 1.5 * HAND),
                   sh, dk, None, [], s=1.0, sw=fine)
    run = [p(-1, -5.0), p(7, -5.6), p(12, -4.6), p(13.5, 0), p(12.5, 4.6), p(6, 5.2), p(-1, 5.0)]
    out += cel(smooth([p(-3, -4.8)] + run + [p(-3, 4.8)]), sk, sh, lt, [], s=2.0, edges=[run])
    idx = finger(p(10, -1.0), p(19.5, 0.4), p(26, 3.8), 2.1 * HAND, 1.9 * HAND, 1.6 * HAND)
    out += cel(idx, sk, sh, lt, [], s=1.2, sw=fine)
    thumb = finger(p(3, -4.0), p(11, -5.6), p(17.5, -3.8), 2.7 * HAND, 2.3 * HAND, 1.8 * HAND)
    out += cel(thumb, sk, sh, lt, [], s=1.6, sw=fine)
    return out


# ---- glyphs, drawn as strokes (no lettering) ----------------------------------------------

def psi(cx, cy, k, color, sw):
    """A psi: the cup and the stem."""
    return [line([(cx - 4.5 * k, cy - 5 * k), (cx - 4.2 * k, cy - 0.5 * k), (cx, cy + 2.2 * k), (cx + 4.2 * k, cy - 0.5 * k), (cx + 4.5 * k, cy - 5 * k)],
                 color, sw),
            line([(cx, cy - 6.5 * k), (cx, cy + 6 * k)], color, sw)]


def bra_ket(cx, cy, k, color, sw, kind):
    """``bra`` is the angle and the bar; ``ket`` the bar and the angle."""
    sgn = -1 if kind == "bra" else 1
    return [line([(cx - sgn * 2.2 * k, cy - 4.5 * k, True), (cx + sgn * 2.2 * k, cy, True), (cx - sgn * 2.2 * k, cy + 4.5 * k, True)], color, sw),
            line([(cx - sgn * 4.4 * k, cy - 4.8 * k), (cx - sgn * 4.4 * k, cy + 4.8 * k)], color, sw)]


def jewel_front(cx, cy, k=1.0):
    """The look's piece at the throat (front view) or on the chest."""
    j = O["jewel"]
    out = []
    if j == "psi_medallion":
        out += [line([(cx - 13, cy - 26), (cx - 6, cy - 6), (cx, cy - 2)], "#9a2232", 3.2), line([(cx + 13, cy - 26), (cx + 6, cy - 6), (cx, cy - 2)], "#9a2232", 3.2)]
        out += cel(smooth([(cx + 9 * math.cos(t * math.pi / 4) * k, cy + 6 + 9 * math.sin(t * math.pi / 4) * k) for t in range(8)]),
                   "#d9b54a", "#a17f27", "#f2d777", [], s=2, sw=1.4)
        out += psi(cx, cy + 6, 0.95 * k, "#5c4313", 1.5)
    elif j == "pair_clasp":
        out.append(line([(cx - 9, cy), (cx + 9, cy)], "#c9ccd6", 1.6))
        out += cel(smooth([(cx - 9 + 4.2 * math.cos(t * math.pi / 4), cy + 4.2 * math.sin(t * math.pi / 4)) for t in range(8)]),
                   "#c9ccd6", "#8d92a3", "#eef0f5", [], s=1.5, sw=1.3)
        out.append(ellipse(cx + 9, cy, 4.2, 4.2, "none", INK, 3.6))
        out.append(ellipse(cx + 9, cy, 4.2, 4.2, "none", "#c9ccd6", 1.6))
    elif j == "braket":
        pass
    return out


# ============================================================================================
# SIDE VIEW (facing right; his right side toward the camera)
# ============================================================================================

S_LEGS = {"near": ((280, 350), (284, 424), (279, 488)), "far": ((266, 350), (264, 424), (256, 488))}
S_NEAR_ARM = ((272, 254), (266, 304), (280, 350))
S_FAR_ARM = ((262, 254), (254, 304), (262, 348))
#: The head is drawn in first-sketch units and scaled about the throat.
S_HEAD_XF = (284.0, 226.0, 0.86)
S_EYE = (294.0, 172.0)


def s_face_points():
    """Dirac in profile: a high upright forehead, a strong brow, a long straight
    nose, a small mouth set back, a firm chin, and a long jaw up to the ear;
    the back of the skull round under the combed-back hair."""
    return [(262, 135), (282, 132), (296, 138), (303, 149), (305.4, 160), (305.6, 166), (303.8, 171), (306.0, 177), (310.2, 186), (314.6, 194.4),
            (314.2, 197.2, True), (309.6, 198.0), (305.8, 198.6), (305.4, 201.6), (306.0, 204.6), (303.6, 206.2, True), (305.2, 208.0), (304.0, 211.2, True),
            (305.0, 214.6), (305.6, 219.0), (302.4, 224.0), (294, 226.0), (282, 222.0), (271, 214.0), (263.4, 204), (254, 194), (247.6, 178), (247.0, 160),
            (252, 144)]


def s_head():
    sk, dk = O["skin_sh"], O["skin_dk"]
    ex, ey = S_EYE
    items = [
        # the gaunt hollow under the cheekbone, the line of the long jaw
        path(smooth([(280, 192), (290, 191), (297, 196), (291, 199), (284, 204), (279, 208)]), sk),
        line([(302, 223.4), (290, 223.6), (278, 218), (268, 208)], sk, 1.3),
        line([(282, 188), (292, 186.4), (299, 188)], sk, 1.2),
        # the sunken socket round the small eye, and the strong brow above it
        path(smooth([(286, 170), (293, 165.4), (302, 167.4), (304, 173), (300, 178.6), (291, 178.6)]), O["socket"]),
        # the long nose's light, its wing and nostril
        line([(305, 175), (311.4, 190)], O["skin_lt"], 1.6),
        path(smooth([(303.6, 191.6), (309, 190.4), (311.4, 195.2), (306.6, 197.0), (303.6, 195.6)]), sk),
        line([(303.8, 191.2), (303.0, 194.8), (305.0, 197.2)], dk, 1.0),
        # the furrow from the nose's wing toward the mouth's corner
        line([(302.6, 197.4), (300.2, 204.4)], dk, 0.9),
        # the crease at the root of the nose, between the brows
        line([(303.4, 166.4), (304.4, 170.4)], dk, 0.8),
    ]
    out = C(smooth(s_face_points()), "skin", items, s=6)
    # the ear: long and close to the head
    out += C(smooth([(262.6, 176), (270.6, 175.4), (273.0, 186), (270.4, 197.4), (264, 197.0), (261.4, 186)]), "skin",
             [line([(265.6, 180), (269.4, 186), (266.4, 193)], dk, 1.0)], s=3)
    out += s_hair()
    return out


def s_hair():
    """Combed straight back: from a widow's peak (``peak``) smooth over the
    crown; or Dirac's own side parting (``part``), a wave lifting off the
    forehead.  Tucked close at the nape; the temple bare above the ear."""
    if O["hair_kind"] == "peak_part":
        # Dirac's own side parting, with the Count's widow's peak: the hairline
        # dips to a point over the brow, the hair lies flat and close, parted
        # high on the crown and combed over from the parting toward the ear.
        edge = [(303.4, 152.0), (300.0, 148.6), (296.6, 153.4, True), (290.6, 150.0), (283, 151.6), (278.4, 158), (276.0, 168), (274.4, 176),
                (268.4, 172), (262.8, 175.4), (259.6, 186), (257, 196.4), (251.6, 197)]
        top = [(250, 190), (245.4, 172), (245.6, 156), (250.0, 143), (258.4, 134.2), (271, 129.0), (287, 127.6), (299.4, 129.4), (305.4, 135.4),
               (306.0, 143), (304.8, 148.6)]
        part_line = [(301.6, 134.6), (288, 133.0), (274, 134.6), (262, 140.4)]
        items = [
            # the parting: a line of scalp along the crown
            line(part_line, O["skin_sh"], 2.0),
            line([(301.0, 133.4), (288, 131.8), (274, 133.4)], O["skin_lt"], 0.8),
            # the hair combed over from the parting, down and back toward the ear
            line([(302.0, 136.4), (298, 141.6), (291.6, 146.8)], O["hair_lt"], 1.5),
            line([(290, 134.6), (284, 142), (276, 149), (271, 158)], O["hair_lt"], 1.4),
            line([(278, 135.6), (271, 143), (265, 152), (262, 166)], O["hair_sh"], 1.1),
            line([(266, 140), (258.6, 150), (255, 166)], O["hair_sh"], 1.0),
        ]
        return cel(smooth(edge + top), O["hair"], O["hair_sh"], O["hair_lt"], items, s=3, l=2)
    if O["hair_kind"] == "part":
        edge = [(305.0, 150), (299.0, 147.6), (291, 150.4), (283, 152), (278.4, 158), (276.0, 168), (274.4, 176), (268.4, 172), (262.8, 175.4),
                (259.6, 186), (257, 196.4), (251.6, 197)]
        top = [(250, 190), (245.4, 172), (245.6, 156), (250.6, 141.6), (260, 131.4), (274, 125.4), (290, 123.0), (302.4, 124.6), (309.6, 131.4),
               (309.4, 141), (306.6, 146)]
        items = [line([(304, 128), (290, 126), (272, 130), (256, 142)], O["hair_lt"], 1.7),
                 line([(306, 138), (292, 134), (276, 138), (262, 150), (256, 168)], O["hair_sh"], 1.1),
                 line([(298, 145), (284, 144), (270, 152), (262, 170)], O["hair_sh"], 1.0)]
        return cel(smooth(edge + top), O["hair"], O["hair_sh"], O["hair_lt"], items, s=3, l=2)
    edge = [(304.6, 154), (300.0, 150.6), (293.4, 153.0), (287, 151.4), (280.4, 156), (276.6, 166), (274.4, 176), (268.4, 172), (262.8, 175.4),
            (259.6, 186), (257, 196.4), (251.6, 197)]
    top = [(250, 190), (245.4, 172), (245.6, 156), (250.6, 141.6), (260, 131.4), (274, 126.4), (289, 127.0), (300.4, 132.6), (306.6, 141.4),
           (307.4, 149)]
    d = smooth(edge + top)
    items = [line([(296, 134), (280, 131), (262, 137), (252, 152)], O["hair_lt"], 1.6),
             line([(298, 142), (284, 139), (268, 143), (258, 156), (254, 172)], O["hair_sh"], 1.1),
             line([(290, 148), (274, 148), (264, 158), (260, 172)], O["hair_sh"], 1.0)]
    return cel(d, O["hair"], O["hair_sh"], O["hair_lt"], items, s=3, l=2)


def s_face(eye="open", mouth="shut"):
    """The face's features: the small deep-set eye, the straight brow, the
    small closed mouth and the fang that shows over the lower lip.  The rig
    swaps the eye (``open`` / ``shut``) and the mouth (``shut`` / ``open``) by
    opacity: ``s_brow``, ``s_eye`` and ``s_mouth`` are the parts."""
    return s_brow() + s_eye(eye) + s_mouth(mouth)


def s_brow():
    """The brow: straight, heavy, low."""
    ex, ey = S_EYE
    return [line([(ex - 6.4, ey - 7.4), (ex + 1, ey - 8.4), (ex + 8.4, ey - 7.6)], O["hair"], 2.4)]


def s_eye(kind="open"):
    """The eye: a narrow almond, mostly lid, the iris dark (``open``); or the
    lid down, one line (``shut``)."""
    ex, ey = S_EYE
    if kind == "shut":
        return [line([(ex - 4.6, ey + 0.4), (ex - 0.6, ey + 1.6), (ex + 4.4, ey + 0.6)], INK, 1.7),
                line([(ex - 2.6, ey + 2.8), (ex + 1.4, ey + 3.0)], O["skin_dk"], 0.9)]
    out = []
    eye = smooth([(ex - 4.2, ey + 0.4, True), (ex, ey - 2.6), (ex + 4.0, ey - 0.2, True), (ex + 0.6, ey + 2.0)])
    out.append(path(eye, "#f1ece6"))
    out.append(ellipse(ex + 1.6, ey + 0.1, 1.8, 2.0, O["iris"]))
    out.append(line([(ex - 4.6, ey + 0.2), (ex - 1.0, ey - 2.8), (ex + 2.4, ey - 2.4), (ex + 4.4, ey - 0.4)], INK, 1.7))
    out.append(line([(ex - 2.6, ey + 2.4), (ex + 1.4, ey + 2.6)], O["skin_dk"], 0.9))
    return out


def s_mouth(kind="shut"):
    """The mouth: a short closed line set back, thin lips, and the fang over
    the lower lip (``shut``); or a small dark opening with the fang at its top
    (``open``, for talk)."""
    if kind == "open":
        return [path(smooth([(306.2, 205.6, True), (301.0, 206.2), (297.2, 205.4, True), (299.4, 209.6), (303.8, 210.6)]), "#3a1820", INK, 1.2),
                path(smooth([(302.0, 206.0, True), (304.4, 205.9, True), (303.4, 209.0, True)]), O["fang"], INK, 0.8),
                line([(304.2, 211.6), (300.6, 212.0)], O["lip"], 1.3)]
    return [line([(306.0, 206.0), (301.2, 206.6), (297.4, 205.6)], O["lip_dk"], 1.5),
            line([(303.6, 208.6), (300.6, 209.4)], O["lip"], 1.3),
            # the fang: a small white point over the lower lip
            path(smooth([(302.0, 206.3, True), (304.6, 206.2, True), (303.5, 210.2, True)]), O["fang"], INK, 0.9)]


def s_neck():
    """The long thin neck, the collar of the shirt and the knot at the throat."""
    out = C(smooth([(270, 214), (292, 214), (296, 244), (268, 246)]), "skin", [line([(286, 222), (290, 236)], O["skin_sh"], 1.0)], s=4)
    # the stiff collar
    collar = smooth([(268, 230), (294, 228), (299, 238, True), (296, 246), (270, 248), (266, 240)])
    out += C(collar, "shirt", [line([(276, 238), (296, 236)], O["shirt_sh"], 0.9)], s=2.5)
    tie = O["tie"]
    if tie == "white_bow":
        out += C(smooth([(294, 236), (302, 232, True), (304, 238), (302, 244, True), (294, 241)]), "shirt", [], s=1.5, sw=1.6)
    else:
        out += cel(smooth([(293, 236), (300, 236), (301, 244), (294, 245)]), O["tie_c"], O["tie_sh"], None, [], s=1.5, sw=1.6)
    return out


def s_torso():
    """The narrow chest and the back: a waistcoat or shirt front under the
    coat, the coat's front edge and lapel."""
    ck = O["coat_kind"]
    out = []
    # the shirt front / waistcoat at the chest
    vest = smooth([(296, 244), (302, 262), (304, 290), (302, 322), (296, 334, True), (276, 332, True), (278, 280), (284, 250)])
    out += C(vest, "vest" if ck == "tails" else "shirt", [], s=3)
    if O["tie"] != "white_bow":
        if ck == "suit":  # the waistcoat over the shirt
            wv = smooth([(300, 268), (305, 290), (304, 322), (298, 336, True), (276, 334, True), (280, 300), (292, 270)])
            out += C(wv, "vest", [ellipse(302, 296, 1.5, 1.5, O["coat_sh"], INK, 0.5), ellipse(302.4, 312, 1.5, 1.5, O["coat_sh"], INK, 0.5)], s=3)
    # the coat: back, shoulder, the front edge rolling back to the lapel
    back = [(262, 244), (252, 252), (249, 276), (251, 304), (254, 330), (256, 352)]
    if ck == "tails":  # cut away at the waist, tails behind to the back of the knee
        coat = smooth([(286, 242), (296, 256, True), (286, 290), (284, 322, True), (270, 334), (266, 360), (264, 420, True), (248, 420, True),
                       (248, 380), (250, 330), (249, 290), (250, 262), (262, 244)])
        items = [line([(262, 340), (258, 414)], O["coat_sh"], 1.2), line([(266, 270), (276, 300)], O["coat_lt"], 1.2)]
        out += C(coat, "coat", items, s=5)
        # the satin lapel
        out += cel(smooth([(286, 244), (296, 256, True), (288, 282, True), (282, 270)]), O["coat_lt"], O["coat"], None, [], s=1, sw=1.6)
    else:
        coat = smooth([(286, 242), (298, 256, True), (300, 290), (300, 330), (298, 356, True), (256, 358, True), (254, 330), (250, 300), (249, 274),
                       (252, 252), (264, 243)])
        items = [line([(286, 258), (292, 300), (294, 352)], O["coat_sh"], 1.3), line([(258, 336), (296, 340)], O["coat_sh"], 1.1),
                 line([(266, 262), (270, 300)], O["coat_lt"], 1.2)]
        out += C(coat, "coat", items, s=5)
        out += cel(smooth([(286, 244), (298, 256, True), (292, 286, True), (284, 268)]), O["coat_lt"], O["coat"], None, [], s=1, sw=1.6)
        # the waistcoat shows at the coat's open front, the tie down it
        out += C(smooth([(298, 262), (303, 290), (303, 328), (298, 340, True), (294, 300), (293, 268)]), "vest", [], s=2)
        out += cel(smooth([(297, 246), (301, 248), (302.6, 272), (301, 292, True), (297.6, 288), (297, 262)]), O["tie_c"], O["tie_sh"], None, [], s=1.2, sw=1.3)
    if O["jewel"] == "psi_medallion":
        out += [line([(286, 246), (298, 268)], "#9a2232", 2.4)]
        out += cel(smooth([(301 + 7 * math.cos(t * math.pi / 4) * 0.55, 276 + 7 * math.sin(t * math.pi / 4)) for t in range(8)]),
                   "#d9b54a", "#a17f27", "#f2d777", [], s=1.5, sw=1.3)
    return out


def leg_piece(hip, knee, ankle, toe_dx, piece, near=True, front=False):
    """One rigid piece of a long thin trousered leg: ``thigh``, ``shin`` or the
    pointed black ``foot`` (``toe_dx`` ahead of the ankle; 0 from the front)."""
    (kx, ky), (ax, ay) = knee, ankle
    if piece == "thigh":  # drawn OVER the shin, open at the knee
        return tube(hip, (kx, ky + 4), 11.5, 9.8, "trouser", near)
    if piece == "shin":
        crease = [line([(kx + (2 if not front else 0), ky + 6), (ax + (2 if not front else 0), ay - 6)], O["trouser_sh"], 1.0)]
        return tube(knee, (ax, ay - 2), 9.8, 8.4, "trouser", near, items=crease if near else (), open_end=False)
    sg = 1 if toe_dx >= 0 else -1
    if front:
        d = smooth([(ax - 8.4, ay - 4), (ax + 8.4, ay - 4), (ax + 9.6, ay + 6), (ax + 6, ay + 14, True), (ax - 6, ay + 14, True), (ax - 9.6, ay + 6)])
        items = [line([(ax - 6, ay + 2), (ax + 6, ay + 2)], O["shoe_lt"], 1.0)]
    else:
        d = smooth([(ax - 9 * sg, ay - 5), (ax + 6 * sg, ay - 4), (ax + toe_dx * 0.7, ay + 5), (ax + toe_dx + 4 * sg, ay + 11, True),
                    (ax + toe_dx, ay + 14, True), (ax - 10 * sg, ay + 14, True)])
        items = [line([(ax + 2 * sg, ay + 3), (ax + toe_dx * 0.9, ay + 9)], O["shoe_lt"], 1.0)]
    return C(d, "shoe", items, s=3) if near else cel(d, O["shoe_sh"], "#08070a", None, [], s=1)


def s_leg(side, piece):
    hip, knee, ankle = S_LEGS[side]
    return leg_piece(hip, knee, ankle, 28, piece, side == "near")


def sleeve(s, e, w, near=True, piece="both"):
    """The coat sleeve, shoulder to wrist in two capsules, and the shirt cuff.
    ``piece`` is ``upper`` (shoulder to elbow), ``lower`` (elbow to wrist and
    the cuff) or ``both``; the rig turns the two about the elbow."""
    out = []
    q = frame(w, ang(e, w))
    past_elbow = (e[0] + (e[0] - s[0]) * 0.08, e[1] + (e[1] - s[1]) * 0.08)
    if piece in ("lower", "both"):
        out += tube(e, w, 9.0 if near else 8.8, 8.0 if near else 7.8, "coat", near, open_end=False)
        if near:
            out += C(smooth([q(-2.6, -7.6), q(1.8, -7.4), q(1.8, 7.4), q(-2.6, 7.6)]), "shirt", [], s=1.2, sw=1.5)
    if piece in ("upper", "both"):
        if near:
            out += tube(s, past_elbow, 10.5, 9.0, "coat", True,
                        items=[line([frame(s, ang(s, e))(4, -4), frame(s, ang(s, e))(30, -4)], O["coat_lt"], 1.1)])
        else:
            out += tube(s, past_elbow, 10, 8.8, "coat", False)
    return out


def s_cape_back():
    """Behind everything: the cape's far half, its inside to us between the legs
    and below the tails; and the standing collar behind the head."""
    k = O["cape_kind"]
    out = []
    lining_items = sea_states(200, 250, 300, 500) if k == "sea" else []
    if k == "inverness":
        # the coat's long skirt: grey-black outside, lined; ends at mid-calf
        d = smooth([(262, 248), (284, 250), (296, 330), (302, 452, True), (240, 456, True), (236, 380), (246, 300)])
        out += C(d, "lining", [], s=3)
        return out
    d = smooth([(258, 246), (290, 250), (298, 330), (304, 492, True), (214, 494, True), (226, 400), (240, 300)])
    out += C(d, "lining", lining_items, s=3)
    return out


def sea_states(x0, y0, x1, y1, step=16.0, hole=None):
    """The Dirac sea on the lining: a field of filled states (small pale dots
    on a diamond grid) and, at ``hole``, the one empty state: a bright ring."""
    out = []
    for j, y in enumerate(range(int(y0), int(y1), int(step))):
        out.append(line([(x0 - 10, y + step * 0.5), (x1 + 10, y + step * 0.5)], O["lining_lt"], 0.9))
        for x in range(int(x0), int(x1), int(step * 0.8)):
            if hole and abs(x - hole[0]) < step * 0.45 and abs(y - hole[1]) < step / 2:
                continue
            out.append(ellipse(x, y, 1.8, 1.8, O["state"]))
    if hole:
        out.append(ellipse(hole[0], hole[1], 4.2, 4.2, "none", O["hole"], 2.0))
    return out


def s_cape_near():
    """The cape's near half, hanging from the shoulder behind the arm: black
    outside, the lining turned out along its front edge and the flared hem;
    and its standing collar rising behind the head."""
    k = O["cape_kind"]
    out = []
    if k == "inverness":
        # the long coat's near side, behind the arm
        d = smooth([(258, 246), (276, 250), (262, 330), (250, 452, True), (234, 452, True), (236, 380), (240, 300), (246, 262)])
        out += C(d, "cape", [line([(250, 300), (244, 440)], O["cape_sh"], 1.3)], s=5)
        return out
    outer = [(286, 244), (276, 270), (266, 330), (258, 400), (254, 470), (252, 494, True), (214, 496, True), (204, 472), (208, 400), (218, 330),
             (232, 270), (246, 248)]
    folds = [line([(240, 290), (228, 380), (220, 486)], O["cape_sh"], 1.5), line([(254, 300), (246, 390), (240, 488)], O["cape_sh"], 1.3),
             line([(262, 280), (254, 330)], O["cape_lt"], 1.3)]
    out += C(smooth(outer), "cape", folds, s=6)
    # the lining turned out at the front edge, widening to the hem
    turn = smooth([(284, 252), (277, 272), (268, 330), (261, 400), (258, 470), (258, 494, True), (250, 494, True), (252, 440), (256, 380), (262, 320),
                   (272, 268)])
    items = sea_states(240, 250, 290, 500, step=12) if k == "sea" else []
    out += C(turn, "lining", items, s=2)
    return out


def s_collar():
    """The cape's standing collar behind the head: its inside (the lining) faces
    us, its outer rim black."""
    k = O["cape_kind"]
    if k == "inverness":
        # the coat collar turned up: a high, square-ish wall behind the jaw
        d = smooth([(272, 250), (260, 248), (250, 238), (247, 212), (250, 196, True), (262, 200), (270, 220), (278, 240)])
        return C(d, "cape", [line([(254, 206), (258, 236)], O["cape_lt"], 1.1)], s=3) + \
            C(smooth([(262, 202), (270, 220), (278, 240), (272, 246), (264, 230), (258, 210)]), "lining", [], s=1.5)
    d = smooth([(276, 250), (256, 252), (240, 236), (232, 206), (234, 168, True), (246, 182), (256, 206), (268, 230), (282, 244)])
    out = C(d, "cape", [], s=3)
    face = smooth([(238, 178), (248, 190), (258, 210), (270, 232), (280, 244), (262, 246), (248, 232), (240, 210)])
    items = sea_states(230, 170, 280, 250, step=10, hole=(250, 214)) if k == "sea" else []
    out += C(face, "lining", items, s=2)
    return out


def s_capelet():
    """The Inverness coat's capelet over the shoulders, to the elbow."""
    if O["cape_kind"] != "inverness":
        return []
    front = [(284, 242), (296, 252), (304, 276), (309, 310), (312, 338, True)]
    d = smooth(front + [(290, 344), (266, 346), (240, 342, True), (234, 318), (236, 286), (244, 260), (262, 246)])
    items = [line([(254, 266), (246, 336)], O["cape_sh"], 1.3), line([(272, 262), (270, 340)], O["cape_sh"], 1.2),
             line([(290, 266), (296, 336)], O["cape_lt"], 1.2)]
    out = C(d, "cape", items, s=5)
    # the lining shows at the capelet's open front edge
    out += C(smooth([(294, 254), (302, 276), (307, 310), (310, 338, True), (304, 340, True), (301, 310), (297, 280), (290, 258)]), "lining", [], s=1)
    return out


def s_braket_pins():
    if O["jewel"] != "braket":
        return []
    return bra_ket(256, 222, 0.9, "#d9b54a", 1.6, "ket")


def s_far_arm(piece="both"):
    s, e, w = S_FAR_ARM
    return sleeve(s, e, w, near=False, piece=piece)


def s_far_hand():
    _s, e, w = S_FAR_ARM
    return hand_side(w, ang(e, w), near=False, which="far")


def s_near_arm(piece="both"):
    s, e, w = S_NEAR_ARM
    return sleeve(s, e, w, piece=piece)


def s_near_hand():
    _s, e, w = S_NEAR_ARM
    return hand_side(w, ang(e, w), which="near", chalk=O.get("chalk", False))


def s_joints():
    ns, ne, nw = S_NEAR_ARM
    fs, fe, fw = S_FAR_ARM
    J = {"body": ("", 272.0, 350.0), "torso": ("body", 272.0, 350.0), "head": ("torso", 284.0, 226.0), "cape": ("torso", 270.0, 250.0),
         "near_arm_u": ("torso", *ns), "near_arm_l": ("near_arm_u", *ne), "near_hand": ("near_arm_l", *nw),
         "far_arm_u": ("torso", *fs), "far_arm_l": ("far_arm_u", *fe), "far_hand": ("far_arm_l", *fw)}
    for side in ("near", "far"):
        hip, knee, ankle = S_LEGS[side]
        J[f"{side}_leg_u"] = ("body", *hip)
        J[f"{side}_leg_l"] = (f"{side}_leg_u", *knee)
        J[f"{side}_foot"] = (f"{side}_leg_l", *ankle)
    return J


def side_layers():
    """The side view's parts: (group id, label, part, bone, z, painter[, opacity channel]).
    A part with a channel is drawn only while its channel is on: the eye and
    the mouth have two parts each, of which one is on."""
    head = lambda f: (lambda: _with_head_xf(f, S_HEAD_XF))
    return [
        ("cape-back", "Cape - Far Half", "cape_back", "cape", 2, s_cape_back),
        ("collar", "Cape - Standing Collar", "cape_collar", "torso", 3, s_collar),
        ("far-arm-lower", "Far Arm - Lower", "far_arm_l", "far_arm_l", 6, lambda: s_far_arm("lower")),
        ("far-arm-upper", "Far Arm - Upper", "far_arm_u", "far_arm_u", 6.5, lambda: s_far_arm("upper")),
        ("far-hand", "Far Hand", "far_hand", "far_hand", 7, s_far_hand),
        ("far-thigh", "Far Thigh", "far_leg_u", "far_leg_u", 11.5, lambda: s_leg("far", "thigh")),
        ("far-shin", "Far Shin", "far_leg_l", "far_leg_l", 11, lambda: s_leg("far", "shin")),
        ("far-foot", "Far Foot", "far_foot", "far_foot", 12, lambda: s_leg("far", "foot")),
        ("near-thigh", "Near Thigh", "near_leg_u", "near_leg_u", 21.5, lambda: s_leg("near", "thigh")),
        ("near-shin", "Near Shin", "near_leg_l", "near_leg_l", 21, lambda: s_leg("near", "shin")),
        ("near-foot", "Near Foot", "near_foot", "near_foot", 22, lambda: s_leg("near", "foot")),
        ("neck", "Neck, Collar and Tie", "neck", "torso", 28, s_neck),
        ("torso", "Coat", "torso", "torso", 30, s_torso),
        ("cape-near", "Cape - Near Half", "cape_near", "cape", 34, s_cape_near),
        ("head", "Head", "head", "head", 60, head(s_head)),
        ("brow", "Brow", "brow", "head", 61, head(s_brow)),
        ("eye-open", "Eye - Open", "eye_open", "head", 61.2, head(lambda: s_eye("open")), "eye_open"),
        ("eye-shut", "Eye - Shut", "eye_shut", "head", 61.2, head(lambda: s_eye("shut")), "eye_shut"),
        ("mouth-shut", "Mouth - Shut", "mouth_shut", "head", 61.4, head(lambda: s_mouth("shut")), "mouth_shut"),
        ("mouth-open", "Mouth - Open", "mouth_open", "head", 61.4, head(lambda: s_mouth("open")), "mouth_open"),
        ("near-arm-lower", "Near Arm - Lower", "near_arm_l", "near_arm_l", 70, lambda: s_near_arm("lower")),
        ("near-arm-upper", "Near Arm - Upper", "near_arm_u", "near_arm_u", 70.5, lambda: s_near_arm("upper")),
        ("near-hand", "Near Hand", "near_hand", "near_hand", 72, s_near_hand),
        ("capelet", "Inverness Capelet", "capelet", "torso", 76, s_capelet),
        ("pins", "Collar Pins", "pins", "torso", 77, s_braket_pins),
    ]


#: The opacity channels that are on when nothing sets them.
DEFAULT_ON = {"eye_open", "mouth_shut"}


def _with_head_xf(f, xf):
    svg.transform(xf)
    try:
        return f()
    finally:
        svg.transform(None)


# ============================================================================================
# FRONT VIEW (his right on screen-left)
# ============================================================================================

F_CX = 280.0
F_ARM_R = ((243, 256), (236, 304), (238, 348))
F_ARM_L = tuple((2 * F_CX - x, y) for x, y in F_ARM_R)
F_LEG_R = ((268, 352), (268, 424), (267, 488))
F_LEG_L = tuple((2 * F_CX - x, y) for x, y in F_LEG_R)
F_HEAD_XF = (280.0, 228.0, 0.86)
F_EYES = ((268.0, 174.0), (292.0, 174.0))


def f_face_points():
    """A long narrow face: the high forehead under the hair, the cheekbones,
    the hollow below them, a long jaw to a firm square-ish chin."""
    right = [(280, 130), (295, 132), (304.4, 142), (307.4, 158), (307.6, 174), (306.6, 186), (304.0, 198), (300.4, 210), (294.6, 220), (287, 226.4),
             (280, 228)]
    return right + mx(right[1:-1])[::-1]


def f_head():
    sk, dk = O["skin_sh"], O["skin_dk"]
    items = [
        # the hollows under the cheekbones
        path(smooth([(255, 192), (260, 195), (262, 201), (259, 207)]), sk),
        path(smooth([(305, 192), (300, 195), (298, 201), (301, 207)]), sk),
        # the jaw's shade, the chin's light
        path(smooth([(256, 200), (262, 214), (272, 224), (280, 226), (288, 224), (298, 214), (304, 200), (300, 214), (288, 228), (272, 228),
                     (260, 214)]), sk),
        # the sockets
        path(smooth([(259, 172), (266, 167), (276, 170), (275, 179), (266, 181), (259, 178)]), O["socket"]),
        path(smooth([(301, 172), (294, 167), (284, 170), (285, 179), (294, 181), (301, 178)]), O["socket"]),
        # the long nose: its shaded side, its tip and nostrils
        path(smooth([(277.6, 176), (279, 176), (277.8, 192), (275.6, 197), (274, 194)]), sk),
        line([(281.6, 178), (283.2, 192)], O["skin_lt"], 1.4),
        line([(273.6, 195.6), (276.4, 198.6), (280, 199.4), (283.6, 198.6), (286.4, 195.6)], dk, 1.1),
    ]
    out = C(smooth(f_face_points()), "skin", items, s=5)
    for sgn in (-1, 1):
        ear = [(280 + sgn * 25.6, 166), (280 + sgn * 32.6, 164.0), (280 + sgn * 34.4, 177), (280 + sgn * 31.0, 193), (280 + sgn * 25.6, 193)]
        out = C(smooth(ear), "skin", [line([(280 + sgn * 28.0, 171), (280 + sgn * 29.6, 180), (280 + sgn * 27.8, 188)], dk, 1.0)], s=2.5) + out
    out += f_hair()
    return out


def f_hair():
    """Combed straight back from a sharp widow's peak; tight at the temples.
    Or (``part``) Dirac's own: parted on his left, swept across and back in
    one wave over his right brow."""
    if O["hair_kind"] == "part":
        pts = [(255.0, 168, True), (251.6, 152), (254.6, 136), (264, 125.0), (280, 120.4), (296, 122.4), (306, 131), (309.2, 148), (308.4, 168, True),
               (305.6, 169), (304.6, 156), (301.6, 148.6), (296.4, 146.0, True), (288, 147.0), (278, 145.0), (268, 143.6), (260, 146.6), (256.6, 154),
               (255.8, 166)]
        items = [line([(296.4, 146), (295.4, 136), (293, 126)], O["hair_sh"], 1.2),
                 line([(292, 140), (282, 132), (268, 132), (258, 142)], O["hair_lt"], 1.6),
                 line([(290, 146), (278, 140), (266, 140), (259, 148)], O["hair_sh"], 1.0),
                 line([(300, 140), (304, 150)], O["hair_sh"], 1.0)]
        return cel(smooth(pts), O["hair"], O["hair_sh"], O["hair_lt"], items, s=3, l=2)
    pts = [(280, 151.0, True), (272, 147.4), (264, 145.4), (258.6, 148), (255.6, 156), (254.4, 170, True), (251.6, 168), (251.0, 150), (255.0, 135),
           (265, 125.6), (280, 122.6), (295, 125.6), (305, 135), (309.0, 150), (308.4, 168), (305.6, 170, True), (304.4, 156), (301.4, 148), (296, 145.4),
           (288, 147.4)]
    items = [line([(280, 146), (276, 134), (270, 127)], O["hair_lt"], 1.5), line([(272, 145), (266, 136), (259, 132)], O["hair_sh"], 1.0),
             line([(288, 145), (294, 136), (301, 132)], O["hair_sh"], 1.0), line([(260, 147), (257, 158)], O["hair_sh"], 1.0),
             line([(300, 147), (303, 158)], O["hair_sh"], 1.0)]
    return cel(smooth(pts), O["hair"], O["hair_sh"], O["hair_lt"], items, s=3, l=2)


def f_face():
    out = []
    for i, (ex, ey) in enumerate(F_EYES):
        sg = -1 if i == 0 else 1
        eye = smooth([(ex - 4.6, ey + 0.4, True), (ex, ey - 2.4), (ex + 4.6, ey + 0.4, True), (ex, ey + 2.2)])
        out.append(path(eye, "#f1ece6"))
        out.append(ellipse(ex, ey + 0.2, 1.9, 2.1, O["iris"]))
        out.append(line([(ex - 5, ey + 0.4), (ex - 1.6, ey - 2.6), (ex + 1.6, ey - 2.6), (ex + 5, ey + 0.4)], INK, 1.7))
        out.append(line([(ex - 3, ey + 2.6), (ex + 3, ey + 2.6)], O["skin_dk"], 0.8))
        # the brows: straight and level, the inner ends a touch lower
        out.append(line([(ex - sg * 7, ey - 7.6), (ex, ey - 8.6), (ex + sg * 7.6, ey - 8.2)], O["hair"], 2.4))
    # the mouth: short, straight, closed
    out.append(line([(272.4, 206.4), (276, 207.2), (284, 207.2), (287.6, 206.4)], O["lip_dk"], 1.5))
    out.append(line([(276.4, 210.4), (283.6, 210.4)], O["lip"], 1.3))
    # two small fangs over the lower lip
    for fx in (276.0, 284.0):
        out.append(path(smooth([(fx - 1.6, 207.3, True), (fx + 1.6, 207.3, True), (fx, 211.4, True)]), O["fang"], INK, 0.9))
    return out


def f_neck():
    out = C(smooth([(270, 214), (290, 214), (292, 246), (268, 246)]), "skin", [path(smooth([(270, 222), (290, 222), (290, 228), (270, 230)]), O["skin_sh"])],
            s=3)
    collar = smooth([(266, 236), (280, 244), (294, 236), (297, 246), (282, 256, True), (278, 256, True), (263, 246)])
    out += C(collar, "shirt", [], s=2)
    if O["tie"] == "white_bow":
        out += C(smooth([(280, 248), (268, 242, True), (266, 254, True)]), "shirt", [], s=1.5, sw=1.6)
        out += C(smooth([(280, 248), (292, 242, True), (294, 254, True)]), "shirt", [], s=1.5, sw=1.6)
        out += C(smooth([(277, 244.6, True), (283, 244.6, True), (283, 251, True), (277, 251, True)]), "shirt", [], s=1, sw=1.6)
    return out


def f_torso():
    ck = O["coat_kind"]
    out = []
    shirt = smooth([(262, 248), (298, 248), (300, 300), (296, 340), (264, 340), (260, 300)])
    out += C(shirt, "shirt", [], s=3)
    if ck == "tails":
        # the white waistcoat, low cut, a point at the waist
        wv = smooth([(264, 282), (280, 314), (296, 282), (298, 330), (292, 344, True), (280, 338), (268, 344, True), (262, 330)])
        out += C(wv, "vest", [ellipse(280, 322, 1.4, 1.4, "#c7c1b8", INK, 0.5)], s=2.5)
        # studs on the shirt front
        out += [ellipse(280, 266, 1.4, 1.4, "#26232c"), ellipse(280, 280, 1.4, 1.4, "#26232c"), ellipse(280, 294, 1.3, 1.3, "#26232c")]
    else:
        out += cel(smooth([(277, 250), (283, 250), (284.5, 262), (282.5, 310), (280, 315, True), (277.5, 310), (275.5, 262)]), O["tie_c"], O["tie_sh"], None,
                   [], s=1.5, sw=1.1)
        wv = smooth([(262, 266), (276, 296), (280, 300), (284, 296), (298, 266), (300, 330), (296, 346, True), (280, 340), (264, 346, True), (260, 330)])
        out += C(wv, "vest", [ellipse(280, 310, 1.5, 1.5, O["coat_sh"], INK, 0.5), ellipse(280, 322, 1.5, 1.5, O["coat_sh"], INK, 0.5),
                              ellipse(280, 334, 1.5, 1.5, O["coat_sh"], INK, 0.5)], s=2.5)
    # the coat: two fronts open over the chest, the lapels rolling to the waist
    for sgn in (-1, 1):
        if ck == "tails":
            front = [(280 + sgn * 18, 246), (280 + sgn * 40, 252), (280 + sgn * 41, 290), (280 + sgn * 37, 330), (280 + sgn * 34, 348, True),
                     (280 + sgn * 22, 336, True), (280 + sgn * 19, 300), (280 + sgn * 13, 262)]
        else:
            front = [(280 + sgn * 18, 246), (280 + sgn * 40, 252), (280 + sgn * 41, 290), (280 + sgn * 39, 330), (280 + sgn * 38, 362, True),
                     (280 + sgn * 3, 362, True), (280 + sgn * 4, 340), (280 + sgn * 9, 304), (280 + sgn * 13, 262)]
        items = [line([(280 + sgn * 33, 260), (280 + sgn * 34, 330)], O["coat_sh"] if sgn < 0 else O["coat_lt"], 1.2)]
        out += C(smooth(front), "coat", items, s=4)
        lapel = smooth([(280 + sgn * 14, 248), (280 + sgn * 24, 252), (280 + sgn * 22, 268, True), (280 + sgn * 26, 272, True), (280 + sgn * 14, 300),
                        (280 + sgn * 11, 270)])
        out += cel(lapel, O["coat_lt"], O["coat"], None, [], s=1, sw=1.5)
    if O["jewel"] == "psi_medallion":
        out += jewel_front(280, 262)
    if O["jewel"] == "pair_clasp":
        pass
    return out


def f_leg(side, piece):
    hip, knee, ankle = F_LEG_R if side == "right" else F_LEG_L
    return leg_piece(hip, knee, ankle, 0, piece, True, front=True)


def f_arm(side):
    s, e, w = F_ARM_R if side == "right" else F_ARM_L
    return sleeve(s, e, w)


def f_hand(side):
    _s, e, w = F_ARM_R if side == "right" else F_ARM_L
    which = "near" if side == "right" else "far"
    return hand_front(w, ang(e, w), 1 if side == "right" else -1, which=which)


def f_cape():
    """Behind him: the cape falling from the shoulders, open, flaring to the
    hem; its inside shows where it flares out past his legs."""
    k = O["cape_kind"]
    out = []
    if k == "inverness":
        d = smooth([(244, 250), (316, 250), (330, 330), (336, 452, True), (224, 452, True), (230, 330)])
        out += C(d, "cape", [line([(244, 340), (240, 448)], O["cape_sh"], 1.3), line([(316, 340), (320, 448)], O["cape_sh"], 1.3)], s=5)
        # its lining seen inside between the legs
        out += C(smooth([(262, 360), (298, 360), (304, 452, True), (256, 452, True)]), "lining", [], s=1, edges=[])
        return out
    d = smooth([(246, 246), (314, 246), (334, 300), (356, 400), (370, 494, True), (190, 494, True), (204, 400), (226, 300)])
    out += C(d, "cape", [line([(220, 340), (204, 488)], O["cape_sh"], 1.4), line([(340, 340), (356, 488)], O["cape_lt"], 1.3)], s=6)
    # the lining: the inside of the cape, behind the legs
    inner = smooth([(252, 250), (308, 250), (326, 330), (342, 420), (352, 494, True), (208, 494, True), (218, 420), (234, 330)])
    items = sea_states(200, 240, 360, 500, step=14, hole=(318, 432)) if k == "sea" else \
        [line([(240, 360), (230, 490)], O["lining_sh"], 1.3), line([(320, 360), (330, 490)], O["lining_sh"], 1.3)]
    out += C(inner, "lining", items, s=4)
    return out


def f_collar():
    """The standing collar: two tall wings behind the head, their inside to us."""
    k = O["cape_kind"]
    out = []
    if k == "inverness":
        for sgn in (-1, 1):
            d = smooth([(280 + sgn * 12, 246), (280 + sgn * 34, 250), (280 + sgn * 40, 232), (280 + sgn * 34, 198, True), (280 + sgn * 22, 214),
                        (280 + sgn * 16, 232)])
            out += C(d, "cape", [], s=3)
            out += C(smooth([(280 + sgn * 33, 202), (280 + sgn * 23, 216), (280 + sgn * 17, 236), (280 + sgn * 26, 244), (280 + sgn * 34, 230)]),
                     "lining", [], s=1)
        return out
    for sgn in (-1, 1):
        d = smooth([(280 + sgn * 10, 248), (280 + sgn * 40, 254), (280 + sgn * 56, 222), (280 + sgn * 60, 164, True), (280 + sgn * 40, 184),
                    (280 + sgn * 26, 214)])
        out += C(d, "cape", [], s=3)
        face = smooth([(280 + sgn * 55, 172), (280 + sgn * 41, 188), (280 + sgn * 28, 216), (280 + sgn * 18, 244), (280 + sgn * 38, 248),
                       (280 + sgn * 51, 222)])
        items = sea_states(220, 160, 340, 250, step=10, hole=(326, 214)) if k == "sea" else []
        out += C(face, "lining", items, s=2)
    return out


def f_capelet():
    if O["cape_kind"] != "inverness":
        return []
    out = []
    for sgn in (-1, 1):
        half = [(280 + sgn * 12, 244), (280 + sgn * 26, 242), (280 + sgn * 44, 252), (280 + sgn * 56, 276), (280 + sgn * 63, 312),
                (280 + sgn * 66, 344, True), (280 + sgn * 44, 350), (280 + sgn * 24, 348, True), (280 + sgn * 19, 300), (280 + sgn * 14, 262)]
        items = [line([(280 + sgn * 40, 268), (280 + sgn * 46, 344)], O["cape_sh"] if sgn < 0 else O["cape_lt"], 1.3),
                 line([(280 + sgn * 24, 262), (280 + sgn * 26, 346)], O["cape_sh"], 1.2)]
        out += C(smooth(half), "cape", items, s=5)
        out += C(smooth([(280 + sgn * 12, 246), (280 + sgn * 17, 246), (280 + sgn * 23, 300), (280 + sgn * 29, 347, True), (280 + sgn * 24, 348, True),
                         (280 + sgn * 19, 300)]), "lining", [], s=1)
    return out


def f_pins():
    j = O["jewel"]
    if j == "braket":
        return bra_ket(253, 240, 0.9, "#d9b54a", 1.6, "bra") + bra_ket(307, 240, 0.9, "#d9b54a", 1.6, "ket")
    if j == "pair_clasp":
        return jewel_front(280, 252)
    return []


def f_joints():
    J = {"body": ("", 280.0, 352.0), "torso": ("body", 280.0, 352.0), "head": ("torso", 280.0, 228.0)}
    for side, (s, e, w) in (("right", F_ARM_R), ("left", F_ARM_L)):
        J[f"{side}_arm_u"] = ("torso", *s)
        J[f"{side}_arm_l"] = (f"{side}_arm_u", *e)
        J[f"{side}_hand"] = (f"{side}_arm_l", *w)
    for side, (h, k, a) in (("right", F_LEG_R), ("left", F_LEG_L)):
        J[f"{side}_leg_u"] = ("body", *h)
        J[f"{side}_leg_l"] = (f"{side}_leg_u", *k)
        J[f"{side}_foot"] = (f"{side}_leg_l", *a)
    return J


def front_layers():
    head = lambda f: (lambda: _with_head_xf(f, F_HEAD_XF))
    L = [
        ("cape", "Cape", "cape", "torso", 2, f_cape),
        ("collar", "Cape - Standing Collar", "cape_collar", "torso", 3, f_collar),
    ]
    for side, z in (("right", 10), ("left", 10)):
        L += [(f"{side}-thigh", f"{side.title()} Thigh", f"{side}_leg_u", f"{side}_leg_u", z + 1.5, lambda s=side: f_leg(s, "thigh")),
              (f"{side}-shin", f"{side.title()} Shin", f"{side}_leg_l", f"{side}_leg_l", z + 1, lambda s=side: f_leg(s, "shin")),
              (f"{side}-foot", f"{side.title()} Foot", f"{side}_foot", f"{side}_foot", z + 2, lambda s=side: f_leg(s, "foot"))]
    L += [
        ("neck", "Neck, Collar and Tie", "neck", "torso", 28, f_neck),
        ("torso", "Coat", "torso", "torso", 30, f_torso),
        ("head", "Head", "head", "head", 60, head(f_head)),
        ("face", "Face", "face_still", "head", 61, head(f_face)),
    ]
    for side in ("right", "left"):
        L += [(f"{side}-arm", f"{side.title()} Arm", f"{side}_arm", f"{side}_arm_u", 70, lambda s=side: f_arm(s)),
              (f"{side}-hand", f"{side.title()} Hand", f"{side}_hand", f"{side}_hand", 72, lambda s=side: f_hand(s))]
    L += [("capelet", "Inverness Capelet", "capelet", "torso", 76, f_capelet), ("pins", "Collar Pins", "pins", "torso", 77, f_pins)]
    return L


# ============================================================================================
# DOCUMENTS
# ============================================================================================

VIEWS: Dict[str, Tuple[str, Callable[[], List], Callable[[], Dict]]] = {
    "side": ("Paul Diracula - Side Right", side_layers, s_joints),
    "front": ("Paul Diracula - Front", front_layers, f_joints),
}


def svg_text(look: str, view: str) -> str:
    use(look)
    _N[0] = 0
    svg.configure(dx=0, dy=0, ink=INK, ow=OW, colors={})
    label, layers, joints = VIEWS[view]
    for group, plabel, name, bone, z, painter, *channel in layers():
        body = painter()
        svg.transform(None)
        if body:
            extra = ""
            if channel:
                extra = f' data-rig-opacity="{channel[0]}"' + (' data-rig-default="1"' if channel[0] in DEFAULT_ON else "")
            part(group, plabel, name, bone, z, body, extra)
    return svg.document(
        size=(W, H), design=f"paul-diracula-{look}", layer_id="paul-diracula", label=label,
        comment=[f"  <!-- CANDIDATE, NOT CAST: Paul Diracula, {O['label']}, {label} (2026-10-22); the ground at y={GROUND_Y:g}.",
                 "       Drawn by scripts/svg_art/paul_diracula_art.py. -->"],
        joints=svg.joints_layer({k: (v[1], v[2]) for k, v in joints().items()}),
    )


# ============================================================================================
# THE CONTACT SHEET (tool venv: resvg_py + PIL)
# ============================================================================================

def raster(text: str, scale: float):
    import resvg_py
    from PIL import Image
    text = re.sub(r'width="[\d.]+mm" height="[\d.]+mm"', f'width="{W * scale:g}" height="{H * scale:g}"', text, count=1)
    text = text.replace('<g id="rig-joints"', '<g id="rig-joints" visibility="hidden"')
    # a part whose opacity channel is off at rest (the shut eye, the open mouth) is not drawn
    text = re.sub(r'(data-rig-opacity="[a-z_]+")>', r'\1 visibility="hidden">', text)
    data = resvg_py.svg_to_bytes(svg_string=text, skip_system_fonts=True)
    return Image.open(io.BytesIO(bytes(data))).convert("RGBA")


def contact_sheet(out_png: Path, looks=None) -> None:
    from PIL import Image, ImageDraw, ImageFont
    looks = looks or list(LOOKS)
    BG = (216, 221, 229, 255)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 22)
    except OSError:
        font = ImageFont.load_default()
    S = 2.0  # figure scale
    fig_box = (150, 110, 410, 510)  # design-space crop holding the whole figure
    head_box = (226, 112, 334, 262)  # design-space crop for the head
    rows = []
    for look in looks:
        use(look)
        side = raster(svg_text(look, "side"), S)
        front = raster(svg_text(look, "front"), S)
        side_c = side.crop(tuple(int(v * S) for v in fig_box))
        front_c = front.crop(tuple(int(v * S) for v in fig_box))
        HS = 4.0
        head_s = raster(svg_text(look, "side"), HS).crop(tuple(int(v * HS) for v in head_box))
        head_f = raster(svg_text(look, "front"), HS).crop(tuple(int(v * HS) for v in (226, 112, 334, 262)))
        # game size: the 128 px frame of the old target holds ~96 px of him
        game = []
        for im in (side, front):
            fig = im.crop(tuple(int(v * S) for v in (150, 120, 410, 506)))
            gh = 96
            gw = round(fig.width * gh / fig.height)
            small = fig.resize((gw, gh), Image.LANCZOS)
            game.append(small)
        cols = [side_c, front_c, head_s, head_f]
        row_h = max(c.height for c in cols) + 50
        gx = sum(c.width for c in cols) + 40 * len(cols) + 40
        row_w = gx + sum(g.width for g in game) * 4 + 120
        row = Image.new("RGBA", (row_w, row_h), BG)
        d = ImageDraw.Draw(row)
        d.text((16, 10), O["label"], fill=(30, 26, 30, 255), font=font)
        x = 20
        for c in cols:
            row.alpha_composite(c, (x, 46 + (row_h - 46 - c.height) // 2))
            x += c.width + 40
        # game size at 1x, then the same pixels shown 3x (nearest) to judge them
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
    sheet = Image.new("RGBA", (W_, sum(r.height for r in rows)), BG)
    y = 0
    for r in rows:
        sheet.alpha_composite(r, (0, y))
        y += r.height
    out_png.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(out_png)
    print(out_png)


#: The cast look and where its drawing goes (the rig reads it there).
CAST_LOOK = "count"
CAST_NAME = "paul_diracula_v2"
CAST_OUT = Path(__file__).resolve().parents[2] / "ambition_sprite2d_renderer" / "data" / "characters" / CAST_NAME / f"{CAST_NAME}_side.svg"
CAST_VIEW = VIEWS["side"][0]


def cast_svg_text() -> str:
    """The cast drawing: look A, the side view, marked as cast."""
    text = svg_text(CAST_LOOK, "side")
    return text.replace("CANDIDATE, NOT CAST: Paul Diracula", "CAST 2026-10-23 as paul_diracula_v2: Paul Diracula", 1)


def main() -> None:
    if len(sys.argv) == 1 or sys.argv[1] == "--cast":
        CAST_OUT.parent.mkdir(parents=True, exist_ok=True)
        tmp = CAST_OUT.with_suffix(".svg.tmp")
        tmp.write_text(cast_svg_text(), encoding="utf8")
        tmp.replace(CAST_OUT)
        print(CAST_OUT)
        return
    if len(sys.argv) > 2 and sys.argv[1] == "--all":
        out = Path(sys.argv[2])
        out.mkdir(parents=True, exist_ok=True)
        for look in LOOKS:
            for view in VIEWS:
                p = out / f"paul_diracula_{look}_{view}.svg"
                p.write_text(svg_text(look, view), encoding="utf8")
                print(p)
        return
    if len(sys.argv) > 2 and sys.argv[1] == "--sheet":
        contact_sheet(Path(sys.argv[2]), sys.argv[3:] or None)
        return
    raise SystemExit("usage: paul_diracula_art.py [--cast] | --all DIR | --sheet PNG [look ...]")


if __name__ == "__main__":
    main()
