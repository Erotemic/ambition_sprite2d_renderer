#!/usr/bin/env python3
"""How the Colonial Statesman's SVG was first drawn (reference, not authority).

    uv run python scripts/svg_art/colonial_statesman_art.py            # his look (A)
    uv run python scripts/svg_art/colonial_statesman_art.py --all DIR  # every look, to DIR

Writes ``data/characters/colonial_statesman/colonial_statesman.svg``; the SVG
owns the art after this has run once. ``JOINTS`` says where each part turns
and ``LAYERS`` lists the parts; ``scripts/build_colonial_statesman_rig.py``
reads both and authors the rows.

Who: the hall's 18th-century statesman, a pompous orator and aristocratic
duelist ("Order, continuity, and a modest tax. I submitted twelve pages";
"I hereby declare war on your impudence!"). His kit: a rapier (the thrust
row) and a flintlock pistol (the pistol row). He used to be a recolour of the
President's body, facing us; he now stands in the cast's side view, facing
right, so the rapier and the pistol read.

Jon, 2026-10-18, of three redraws: "A for statesmen" — A is ``federalist``,
the Federalist orator: slim, a bottle-green coat, a buff waistcoat and
breeches, his powdered hair in a queue with a black bow, a rapier at his hip
and his twelve-page speech in hand. B (``governor``, a stout royal governor
in claret velvet and a full wig) and C (``tricorn``, a lean duelist in
charcoal with a pistol in his sash) are KEPT, NOT CAST: this script draws
them (``--all``) and nothing registers them.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Dict, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import svgkit as svg  # noqa: E402
from svgkit import capsule, ellipse, line, part, path, smooth  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "ambition_sprite2d_renderer" / "data" / "characters" / "colonial_statesman" / "colonial_statesman.svg"
VIEW = "Colonial Statesman - Side Right"
LOOK = "federalist"
W = H = 560
CX = 272.0
INK = "#1d1714"
OW = 1.5
#: The ground under his soles, in SVG units.
GROUND_Y = 502.0
#: Shade down-back (left, below), light up-front (right, above): he faces right.
SD, LD = (-1.0, 0.6), (1.0, -0.8)

LOOKS = {
    "federalist": dict(
        label="A: Federalist orator - green coat, the speech",
        coat="#2f5a45", coat_sh="#1f3e2f", coat_lt="#467a60",
        vest="#d6b98a", vest_sh="#b29466", vest_lt="#ead3aa",
        breech="#d6b98a", breech_sh="#b29466", breech_lt="#ead3aa",
        trim=None, button="#d9b456",
        skin="#ecc6a6", skin_sh="#cc9f82", skin_lt="#f6dcc6", skin_dk="#a06f58", lip="#bf7e70", cheek=None,
        hair="#e7e3da", hair_sh="#bdb8ae", hair_lt="#faf8f4", wig="queue",
        iris="#4f5f6e", stocking="#ece9e1", stocking_sh="#c4bfb3",
        shoe="#1e1b1d", shoe_lt="#3e383c", buckle="#d7dde3",
        hilt="#d7dde3", hilt_sh="#8f98a2", scabbard="#2a2220",
        k_w=0.96, belly=0.0, hold="pages", face="lean",
    ),
    "governor": dict(
        label="B: Royal governor - claret, full wig, stout",
        coat="#6e2232", coat_sh="#4b1622", coat_lt="#933648",
        vest="#e9d9a8", vest_sh="#c6b07a", vest_lt="#f7ecc8",
        breech="#6e2232", breech_sh="#4b1622", breech_lt="#933648",
        trim="#e0b54a", button="#e0b54a",
        skin="#eec3a3", skin_sh="#cf9a7e", skin_lt="#f8dbc5", skin_dk="#a46a56", lip="#c07468", cheek="#e3a08a",
        hair="#ece9e2", hair_sh="#c3beb4", hair_lt="#fbfaf6", wig="full",
        iris="#5a4a3e", stocking="#ece9e1", stocking_sh="#c4bfb3",
        shoe="#1e1b1d", shoe_lt="#3e383c", buckle="#e0b54a", heel="#a8323a",
        hilt="#e0b54a", hilt_sh="#a17c2a", scabbard="#2a2220",
        k_w=1.12, belly=14.0, hold="hilt", face="jowl",
    ),
    "tricorn": dict(
        label="C: Tricorn duelist - charcoal, pistol in sash",
        coat="#2e2d33", coat_sh="#1d1c21", coat_lt="#4a4952",
        vest="#9a2a2e", vest_sh="#701c20", vest_lt="#bb4044",
        breech="#2e2d33", breech_sh="#1d1c21", breech_lt="#4a4952",
        trim=None, button="#c9ccd2",
        skin="#e9c4a5", skin_sh="#c79c80", skin_lt="#f5dac4", skin_dk="#9d6c56", lip="#b5786a", cheek=None,
        hair="#dcd9d2", hair_sh="#b2aea5", hair_lt="#f3f1ec", wig="queue",
        iris="#3c4a58", stocking="#d9d6cf", stocking_sh="#aaa59b",
        shoe="#1e1b1d", shoe_lt="#3e383c", buckle="#c9ccd2",
        hilt="#c9ccd2", hilt_sh="#8a8f98", scabbard="#1f1a19",
        hat="#1d1b20", hat_sh="#111013", hat_lt="#3a3740", lace="#d9b456",
        k_w=0.92, belly=0.0, hold="pistol", face="sharp", pistol=True,
    ),
}
for _look in LOOKS.values():
    _look.setdefault("blade", "#d9dfe5")
    _look.setdefault("blade_sh", "#9aa4ae")
    _look.setdefault("wood", "#6e4529")
    _look.setdefault("wood_sh", "#4a2d19")
    _look.setdefault("wood_lt", "#8e6040")
    _look.setdefault("steel", "#5f636b")
    _look.setdefault("steel_sh", "#3e4148")
    _look.setdefault("flash", "#ffe08a")
    _look.setdefault("flash_core", "#fff8de")
    _look.setdefault("smoke", "#d8d4cc")

O: dict = {}
_N = [0]


# ---- the house cel shading ---------------------------------------------------------

def uid(tag="c"):
    _N[0] += 1
    return f"{tag}{_N[0]}"


def cel(d, base, shade, light=None, items=(), sdir=SD, ldir=LD, s=5.0, l=3.0, sw=None, ink=None):
    """A shape: its fill, a ``shade`` band along the edges facing ``sdir`` and a
    ``light`` band along those facing ``ldir`` (clipped inside), the detail
    ``items``, then the thin ink outline."""
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
    out.append(path(d, "none", ink or INK, sw or 2 * OW))
    return out


def C(d, key, items=(), **kw):
    return cel(d, O[key], O[key + "_sh"], O.get(key + "_lt"), items, **kw)


def frame(origin, u_ang):
    """``p(t, s)``: ``t`` along the angle ``u_ang`` (radians) from ``origin``, ``s`` across it."""
    ux, uy = math.cos(u_ang), math.sin(u_ang)
    nx, ny = -uy, ux
    return lambda t, s: (origin[0] + ux * t + nx * s, origin[1] + uy * t + ny * s)


def band(a, b, w):
    """A straight strap of width ``w`` from ``a`` to ``b`` (square ends)."""
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    p, q = frame(a, ang), frame(b, ang)
    return [p(0, -w / 2) + (True,), q(0, -w / 2) + (True,), q(0, w / 2) + (True,), p(0, w / 2) + (True,)]


def Wd(pts, belly=False):
    """Torso points narrowed/widened about the body line by ``k_w``; ``belly`` pushes the front out at the waist."""
    out = []
    for p in pts:
        x, y = p[0], p[1]
        x = CX + (x - CX) * O["k_w"]
        if belly and x > CX:
            x += O["belly"] * math.exp(-((y - 322.0) / 30.0) ** 2)
        out.append((x, y) + tuple(p[2:]))
    return out


# ---- the skeleton -----------------------------------------------------------------

LEGS = {"near": ((276, 348), (284, 416), (279, 484)), "far": ((262, 348), (262, 416), (252, 484))}
FAR_ARM = ((264, 262), (258, 316), (268, 360))


def hold_point():
    """Where his near fist closes: on the speech, round the pistol butt, or on the hilt."""
    if O["hold"] == "pages":
        return (300.0, 318.0)
    if O["hold"] == "pistol":
        b = Wd([(300, 336)], belly=True)[0]
        return (b[0] + 11, b[1] - 6)
    g = Wd([(292, 362)])[0]
    return (g[0] + 8, g[1] - 14)


def near_arm_points():
    """Shoulder, elbow, wrist and fist of the near arm."""
    sh, el = Wd([(270, 262)])[0], Wd([(262, 314)])[0]
    F = hold_point()
    d = math.hypot(F[0] - el[0], F[1] - el[1])
    wr = (F[0] - (F[0] - el[0]) / d * 10, F[1] - (F[1] - el[1]) / d * 10)
    return sh, el, wr, F


def joints() -> Dict[str, Tuple[str, float, float]]:
    """Where each bone turns (SVG units): ``bone: (parent, x, y)``, parents first."""
    sh, el, wr, _F = near_arm_points()
    fs, fe, fw = FAR_ARM
    J = {
        "body": ("", 270.0, 348.0),
        "torso": ("body", 270.0, 348.0),
        "head": ("torso", 282.0, 236.0),
        "near_arm_u": ("torso", *sh),
        "near_arm_l": ("near_arm_u", *el),
        "near_hand": ("near_arm_l", *wr),
        "far_arm_u": ("torso", *fs),
        "far_arm_l": ("far_arm_u", *fe),
        "far_hand": ("far_arm_l", *fw),
    }
    for side in ("near", "far"):
        hip, knee, ankle = LEGS[side]
        J[f"{side}_leg_u"] = ("body", *hip)
        J[f"{side}_leg_l"] = (f"{side}_leg_u", *knee)
        J[f"{side}_foot"] = (f"{side}_leg_l", *ankle)
    return J


# ---- legs --------------------------------------------------------------------

def thigh(side):
    """The breeches thigh, buckled under the knee."""
    near = side == "near"
    hip, (kx, ky), _a = LEGS[side]
    th = smooth([(hip[0] - 14, hip[1] - 6), (hip[0] + 14, hip[1] - 8), (kx + 10, ky - 2), (kx + 9, ky + 6, True), (kx - 10, ky + 6, True),
                 (kx - 13, ky - 6)])
    if near:
        return C(th, "breech", [line([(kx - 10, ky + 1), (kx + 9, ky + 1)], O["breech_sh"], 1.2),
                                ellipse(kx + 7, ky + 2, 1.5, 1.5, O["button"], INK, 0.6)])
    return cel(th, O["breech_sh"], O["breech_sh"], None, [], s=1)


def shin(side):
    """The stocking, a calf at the back."""
    near = side == "near"
    _h, (kx, ky), (ax, ay) = LEGS[side]
    sock = smooth([(kx - 9, ky - 4), (kx + 8, ky - 4), (kx + 7, ky + 26), (ax + 5, ay - 12), (ax + 5, ay + 2), (ax - 6, ay + 2),
                   (ax - 8, ay - 20), (kx - 13, ky + 26)])
    st, stsh = (O["stocking"], O["stocking_sh"]) if near else (O["stocking_sh"], "#9c978c")
    return cel(sock, st, stsh, "#f8f6f1" if near else None, [], s=4)


def shoe(side):
    """The shoe, toe to the right, a buckle on the instep."""
    near = side == "near"
    _h, _k, (ax, ay) = LEGS[side]
    d = smooth([(ax - 9, ay - 2), (ax + 6, ay - 4), (ax + 14, ay + 4), (ax + 26, ay + 10), (ax + 29, ay + 16, True), (ax - 4, ay + 18, True),
                (ax - 11, ay + 12)])
    items = [path(smooth([(ax + 2, ay - 4, True), (ax + 10, ay - 4, True), (ax + 12, ay + 4), (ax + 3, ay + 5)]), O["buckle"], INK, 0.9)]
    if O.get("heel"):
        items.append(path(smooth([(ax - 11, ay + 12, True), (ax - 3, ay + 12, True), (ax - 3, ay + 18, True), (ax - 11, ay + 18, True)]), O["heel"]))
    return cel(d, O["shoe"] if near else "#141214", "#0f0d0e", O["shoe_lt"] if near else None, items, s=3)


# ---- the far arm ---------------------------------------------------------------------

def far_upper():
    s, e, _w = FAR_ARM
    return cel(capsule(s, e, 11, 9.5), O["coat_sh"], O["coat_sh"], None, [], s=1)


def far_lower():
    _s, e, w = FAR_ARM
    return cel(capsule(e, w, 9.5, 8.5), O["coat_sh"], O["coat_sh"], None, [], s=1)


def far_hand():
    _s, _e, w = FAR_ARM
    return cel(smooth([(w[0] - 7, w[1] + 2), (w[0] + 6, w[1] + 2), (w[0] + 6, w[1] + 22), (w[0] - 4, w[1] + 24)]), O["skin_sh"], O["skin_dk"], None, [], s=2)


# ---- coat, waistcoat, stock -----------------------------------------------------------

def waistcoat():
    pts = Wd([(282, 242), (298, 246), (306, 262), (309, 290), (308, 320), (306, 348), (299, 362, True), (288, 352), (284, 300)], belly=True)
    items = [ellipse(*Wd([(p[0], p[1])], belly=True)[0], 1.7, 1.7, O["button"], INK, 0.6)
             for p in [(303, 270), (305, 284), (305, 298), (305, 312), (304, 326), (303, 340)]]
    items.append(line(Wd([(288, 336), (300, 334)], belly=True), INK, 1.0))
    if O.get("trim"):  # brocade sprigs
        for (x, y) in [(294, 276), (296, 300), (296, 324)]:
            q = Wd([(x, y)], belly=True)[0]
            items.append(ellipse(q[0], q[1], 2.2, 1.4, O["vest_sh"]))
    return C(smooth(pts), "vest", items)


COAT = [(290, 240), (272, 238), (258, 246), (248, 258), (242, 282), (242, 310), (246, 334), (242, 360), (234, 390), (229, 413, True),
        (250, 418), (264, 414, True), (269, 388), (277, 364), (287, 346), (292, 320), (294, 290), (294, 262)]


def coat():
    items = [
        # the back seam and the pleats of the tail
        line(Wd([(250, 340), (244, 386), (240, 412)]), O["coat_sh"], 1.4),
        line(Wd([(258, 344), (256, 412)]), O["coat_sh"], 1.2),
        # the pocket flap, scalloped
        path(smooth(Wd([(256, 352, True), (282, 350, True), (280, 359), (274, 356), (269, 362), (263, 357), (257, 360)])), O["coat_sh"], INK, 1.0),
        # the waist seam
        line(Wd([(246, 336), (270, 340), (288, 344)]), O["coat_sh"], 1.1),
    ]
    if O.get("trim"):  # gold lace down the front edge and round the pocket
        items.append(line(Wd([(290, 244), (292, 262), (292, 292), (290, 320), (285, 345), (276, 365), (268, 390), (263, 414)]), O["trim"], 3.0))
        items.append(line(Wd([(256, 352), (282, 350)]), O["trim"], 2.0))
    for y, x in [(262, 290), (284, 291), (306, 290), (328, 288)]:
        q = Wd([(x - 3, y)])[0]
        items.append(ellipse(q[0], q[1], 2.0, 2.0, O["button"], INK, 0.6))
    out = C(smooth(Wd(COAT)), "coat", items, s=6)
    out += C(smooth(Wd([(268, 232), (288, 234), (292, 246), (270, 248), (262, 244)])), "coat", [], s=3)  # stand collar
    return out


def sash_pistol():
    """Look C: a flintlock tucked through a crimson sash at the waist, the butt forward."""
    if not O.get("pistol"):
        return []
    b = Wd([(300, 336)], belly=True)[0]
    out = cel(smooth(band((b[0] - 2, b[1] + 6), (b[0] - 34, b[1] + 9), 4.0)), O["steel"], O["steel_sh"], None, [], s=1)
    sash = smooth(Wd([(246, 330), (300, 338), (312, 340), (310, 352), (292, 352), (246, 344)], belly=True))
    out += cel(sash, "#7a1c22", "#521216", "#9c2c30", [line(Wd([(250, 337), (306, 345)], belly=True), "#521216", 1.0)], s=3)
    butt = smooth([(b[0] - 2, b[1] + 6), (b[0] + 8, b[1] - 2), (b[0] + 18, b[1] - 10), (b[0] + 25, b[1] - 18), (b[0] + 32, b[1] - 13, True),
                   (b[0] + 26, b[1] - 5), (b[0] + 14, b[1] + 5), (b[0] + 2, b[1] + 11)])
    out += cel(butt, O["wood"], O["wood_sh"], O["wood_lt"], [ellipse(b[0] + 28, b[1] - 14, 4.0, 3.0, O["hilt"], INK, 0.8, rot=-40),
                                                             line([(b[0] + 4, b[1] + 5), (b[0] + 16, b[1] - 3)], O["wood_sh"], 1.0)], s=2)
    return out


def neck_and_stock():
    out = cel(capsule((280, 222), (283, 246), 10.5, 10.5), O["skin"], O["skin_sh"], O["skin_lt"], [], s=4)
    out += cel(smooth([(271, 234), (291, 236), (295, 246), (273, 248)]), "#f1eee6", "#c9c3b6", "#ffffff", [], s=3)
    jabot = smooth([(290, 240), (300, 242), (306, 252), (303, 258), (308, 266), (302, 276), (295, 280), (296, 266), (291, 254)])
    out += cel(jabot, "#f1eee6", "#c9c3b6", "#ffffff",
               [line([(296, 246), (300, 256), (298, 268), (300, 276)], "#c9c3b6", 1.0), line([(302, 256), (306, 262)], "#c9c3b6", 0.9)], s=3)
    return out


# ---- head ----------------------------------------------------------------------

def face_points():
    f = O["face"]
    nose_tip = (314, 208) if f != "sharp" else (316, 209)
    pts = [(254, 192), (255, 174), (265, 163), (281, 158), (295, 162), (302, 172), (304, 183), (303, 190), (307, 197), (311, 204),
           nose_tip + (True,), (309, 211), (304, 212, True), (305, 217), (303, 220, True), (305, 223), (303, 227), (300, 229),
           (303, 234), (300, 239), (292, 241), (284, 238), (276, 231), (270, 224), (262, 216), (256, 206)]
    if f == "jowl":
        pts = pts[:18] + [(302, 233), (300, 240), (293, 245), (284, 245), (276, 238), (270, 228), (262, 216), (256, 206)]
    return pts


def head_back():
    """The hair behind the head: the queue and its bow, or the full wig's fall of curls."""
    if O["wig"] == "full":
        fall = smooth([(262, 160), (246, 168), (238, 190), (236, 220), (232, 250), (240, 272), (256, 276), (266, 262), (272, 236), (276, 210),
                       (284, 186)])
        curls = [path(smooth([(x - 6, y), (x, y - 6), (x + 6, y), (x, y + 6)]), "none", O["hair_sh"], 1.3)
                 for (x, y) in [(244, 196), (240, 222), (238, 248), (252, 262), (256, 236), (262, 212)]]
        return C(fall, "hair", curls, s=5)
    out = C(smooth([(258, 210), (252, 236), (248, 262), (252, 266), (258, 240), (264, 214)]), "hair", [], s=2)
    out += cel(smooth([(256, 216), (244, 210), (242, 224), (254, 222), (248, 236), (260, 234), (262, 222)]), "#1d1a1d", "#0f0d0f", "#3a3439", [], s=2)
    return out


EYE = (296.0, 196.0)


def head():
    """The face (without its eye), the ear, the hair over the crown (and look C's hat)."""
    out = []
    sk, dk = O["skin_sh"], O["skin_dk"]
    ex, ey = EYE
    items = [
        # cheek and jaw shade, the nostril, the mouth
        path(smooth([(262, 214), (284, 224), (296, 236), (284, 244), (266, 232)]), sk),
        line([(306, 209), (309, 211)], dk, 1.3),
        line([(303, 220.2), (297, 221.4)], INK, 1.3),
        path(smooth([(299, 222), (304, 222.5), (303, 226), (299, 225)]), O["lip"]),
        line([(300, 205), (304, 214)], sk, 1.1),
        line([(ex - 3, ey + 3.4), (ex + 2, ey + 3.2)], sk, 0.9),
        # the brow
        line([(ex - 6, ey - 6.5), (ex, ey - 7.8), (ex + 6, ey - 6.0)], O["hair_sh"], 2.4),
        line([(ex - 6, ey - 6.5), (ex, ey - 7.8), (ex + 6, ey - 6.0)], INK, 0.7),
    ]
    if O.get("cheek"):
        items.append(ellipse(292, 214, 6.0, 4.0, O["cheek"]))
    if O["face"] == "jowl":
        items += [line([(284, 236), (296, 242)], sk, 1.2), line([(298, 214), (302, 226)], sk, 1.0)]
    if O["face"] == "sharp":
        items += [line([(282, 210), (290, 226)], sk, 1.3)]
    out += C(smooth(face_points()), "skin", items, s=6)
    out += C(smooth([(268, 200), (276, 199), (278, 210), (274, 219), (267, 216)]), "skin", [line([(271, 203), (275, 209), (271, 214)], dk, 1.1)], s=3)
    if O["wig"] == "full":
        crown = smooth([(298, 168), (290, 156), (274, 150), (256, 154), (244, 166), (240, 184), (246, 200), (256, 214), (264, 212), (266, 196),
                        (274, 182), (288, 172)])
        strands = [line([(286, 160), (270, 166), (258, 182)], O["hair_sh"], 1.2), line([(280, 155), (262, 160), (250, 176)], O["hair_lt"], 1.2)]
        out += C(crown, "hair", strands, s=4)
        for (x, y) in [(270, 196), (268, 212), (266, 228)]:
            c = smooth([(x - 7, y), (x - 1, y - 7), (x + 6, y - 1), (x + 1, y + 7)])
            out += C(c, "hair", [path(smooth([(x - 3, y), (x, y - 3), (x + 3, y), (x, y + 2)]), "none", O["hair_sh"], 1.1)], s=2)
    else:
        crown = smooth([(299, 170), (292, 159), (278, 154), (262, 157), (250, 168), (246, 184), (248, 202), (256, 214), (262, 214), (264, 200),
                        (272, 186), (286, 176)])
        strands = [line([(290, 164), (274, 164), (260, 176)], O["hair_sh"], 1.2), line([(286, 170), (272, 172), (262, 186)], O["hair_sh"], 1.0)]
        out += C(crown, "hair", strands, s=4)
        out += C(capsule((258, 193), (282, 192), 5.6, 5.4), "hair", [line([(281, 189), (284, 192), (281, 195)], O["hair_sh"], 1.1)], s=3, sdir=(0.0, 1.0))
    if O.get("hat"):
        svg.DY = 7.0  # the hat sits down on the wig
        out += tricorn()
        svg.DY = 0.0
    return out


def tricorn():
    """A black tricorn, a corner to the front, gold lace on the brim and a cockade."""
    brim = smooth([(232, 172, True), (250, 154), (276, 148), (300, 154), (318, 166, True), (300, 168), (276, 166), (250, 170)])
    crown = smooth([(250, 160), (254, 140), (270, 132), (288, 134), (300, 146), (300, 160)])
    out = cel(crown, O["hat"], O["hat_sh"], O["hat_lt"], [], s=4)
    out += cel(brim, O["hat"], O["hat_sh"], O["hat_lt"], [line([(234, 171), (250, 158), (276, 152), (300, 157), (316, 166)], O["lace"], 2.0)], s=3)
    corner = smooth([(276, 150), (300, 140), (320, 166, True), (304, 166), (288, 160)])
    out += cel(corner, O["hat"], O["hat_sh"], O["hat_lt"], [line([(282, 152), (300, 144), (316, 164)], O["lace"], 2.0)], s=3)
    out += cel(smooth([(292, 146), (298, 142), (302, 148), (296, 152)]), "#1d1a1d", "#0f0d0f", "#4a434a", [ellipse(297, 147, 1.4, 1.4, O["lace"])], s=1)
    return out


def eyes(kind):
    """His eye, small, set under the brow, the iris to the front (the rig shows one at a time)."""
    ex, ey = EYE
    if kind == "open":
        return [path(smooth([(ex - 4, ey), (ex - 0.5, ey - 2.4), (ex + 3.5, ey - 1.2), (ex + 1.5, ey + 1.6), (ex - 2.5, ey + 1.4)]), "#f4f1ea"),
                ellipse(ex + 1.6, ey - 0.4, 1.5, 1.9, O["iris"]), ellipse(ex + 1.8, ey - 0.4, 0.7, 0.8, "#141414"),
                line([(ex - 4.4, ey + 0.1), (ex - 0.5, ey - 2.8), (ex + 4.0, ey - 1.0)], INK, 1.5)]
    if kind == "shut":
        return [line([(ex - 4.4, ey - 0.4), (ex, ey + 1.4), (ex + 4.0, ey - 0.6)], INK, 1.5)]
    return [line([(ex - 3, ey - 2.6), (ex + 3, ey + 2.6)], INK, 1.4), line([(ex - 3, ey + 2.6), (ex + 3, ey - 2.6)], INK, 1.4)]


def mouth_open():
    """His mouth open to speak, over the pressed one."""
    return [path(smooth([(296, 218), (304, 218.5), (305, 226), (298, 227)]), O["skin"]),
            path(smooth([(297, 219.6), (303.5, 219.4), (304, 225.5), (299, 226.5)]), "#5a2a2a", INK, 1.1),
            path(smooth([(299, 224.6), (303.5, 224.4), (303.6, 226), (299.5, 226.4)]), O["lip"])]


# ---- the near arm, the sword at his hip, and the things he holds -------------------------

def cuff(wr, ang):
    p = frame(wr, ang)
    lace = smooth([p(2, -10), p(10, -9), p(12, -5), p(10, 0), p(12, 5), p(10, 9), p(2, 10), p(4, 0)])
    out = cel(lace, "#f1eee6", "#c9c3b6", "#ffffff", [line([p(5, -5), p(10, 0), p(5, 5)], "#c9c3b6", 0.9)], s=2.5)
    c = smooth([p(-14, -12) + (True,), p(2, -11.5) + (True,), p(3, 11) + (True,), p(-13, 12) + (True,)])
    det = [ellipse(*p(-5, -5), 1.6, 1.6, O["button"], INK, 0.6), ellipse(*p(-5, 1), 1.6, 1.6, O["button"], INK, 0.6)]
    if O.get("trim"):
        det.append(line([p(-12, -11), p(-11, 11)], O["trim"], 2.0))
    return out + C(c, "coat", det, s=3)


def near_upper():
    sh, el, _wr, _F = near_arm_points()
    return C(capsule(sh, el, 13, 11.5), "coat", [], s=5)


def near_lower():
    _sh, el, wr, _F = near_arm_points()
    out = C(capsule(el, wr, 11.5, 10), "coat", [], s=5)
    out.append(ellipse(el[0], el[1], 9.8, 9.8, O["coat"]))
    return out + cuff(wr, math.atan2(wr[1] - el[1], wr[0] - el[0]))


def near_fist():
    """The fist: pinching the speech, round the pistol butt, or on the pommel."""
    x, y = hold_point()
    d = smooth([(x - 10, y - 6), (x, y - 9), (x + 9, y - 5), (x + 11, y + 2), (x + 6, y + 8), (x - 5, y + 7), (x - 11, y + 1)])
    it = [line([(x - 3, y - 2), (x + 9, y - 1)], O["skin_sh"], 1.0), line([(x - 3, y + 3), (x + 8, y + 3.5)], O["skin_sh"], 1.0)]
    out = cel(d, O["skin"], O["skin_sh"], O["skin_lt"], it, s=3)
    return out + cel(capsule((x - 2, y - 6), (x + 8, y - 7), 3.0, 2.4), O["skin"], O["skin_sh"], None, [], s=1.5)


def scabbard():
    """The scabbard on his near hip, back and down behind him."""
    g = Wd([(292, 362)])[0]
    out = cel(smooth(band((g[0] - 3, g[1] + 3), (g[0] - 66, g[1] + 98), 6.0)), O["scabbard"], "#120e0d", "#4a3a34", [], s=1.5)
    return out + cel(smooth(band((g[0] - 60, g[1] + 89), (g[0] - 67, g[1] + 100), 7.5)), O["hilt"], O["hilt_sh"], None, [], s=1.5)


def hilt_at(g, ang=0.0):
    """A swept rapier hilt, its grip running forward-up from ``g`` (turned by ``ang`` radians)."""
    c, s_ = math.cos(ang), math.sin(ang)
    R = lambda dx, dy: (g[0] + dx * c - dy * s_, g[1] + dx * s_ + dy * c)
    out = cel(capsule(R(2, -1), R(12, -13), 2.4, 2.2), "#3b2a24", "#24180f", None,
              [line([R(4, -4), R(7, -4)], O["hilt_sh"], 0.8), line([R(7, -8), R(10, -8)], O["hilt_sh"], 0.8)], s=1)
    out += cel(smooth([R(10, -17), R(15, -17), R(16, -12), R(11, -11)]), O["hilt"], O["hilt_sh"], None, [], s=1.5)
    bow = [R(-2, 2), R(12, 2), R(18, -6), R(15, -14)]
    quillon = [R(2, 0), R(-10, 4)]
    out += [line(bow, INK, 3.6), line(bow, O["hilt"], 1.8), line(quillon, INK, 3.6), line(quillon, O["hilt"], 1.8)]
    out += cel(smooth([R(-5, -3), R(2, -6), R(6, 1), R(1, 6), R(-5, 4)]), O["hilt"], O["hilt_sh"], "#ffffff", [], s=2)
    return out


def rapier_sheathed():
    """The hilt at his hip (``hilt_sheathed``): gone while the rapier is drawn."""
    return hilt_at(Wd([(292, 362)])[0])


def pages():
    """His twelve-page speech, folded once, held by its top edge (``prop_pages``)."""
    if O["hold"] != "pages":
        return []
    x, y = hold_point()
    x, y = x + 2, y - 4
    out = []
    for k, (dx, rot) in enumerate([(4, -18), (2, -24), (0, -30)]):
        p = frame((x + dx, y), math.radians(90 + rot))
        sheet_d = smooth([p(-2, -14) + (True,), p(-2, 14) + (True,), p(44, 15) + (True,), p(46, -13) + (True,)])
        items = [line([p(8 + 6 * i, -9), p(8 + 6 * i, 9 - (i % 2) * 5)], "#9b8c6c", 0.9) for i in range(6)] if k == 2 else []
        out += cel(sheet_d, "#efe7cf", "#cbbd98", "#fbf7ea", items, s=2.5)
    return out


def forearm_angle():
    _sh, el, wr, _F = near_arm_points()
    return math.atan2(wr[1] - el[1], wr[0] - el[0])


def rapier_drawn():
    """The rapier drawn, its blade out along his forearm (``prop_rapier``)."""
    F = hold_point()
    a = forearm_angle()
    p = frame(F, a)
    blade = smooth([p(6, -2.2) + (True,), p(130, -0.8), p(142, 0) + (True,), p(130, 0.9), p(6, 2.2) + (True,)])
    out = cel(blade, O["blade"], O["blade_sh"], "#ffffff", [line([p(12, 0), p(124, 0)], O["blade_sh"], 0.7)], s=1.2, l=0.8)
    # the hilt, turned so its grip lies in the fist and its cup guards the front of the hand
    out += hilt_at(p(-8, 4), a - math.radians(-50))
    return out


def pistol_drawn():
    """His flintlock in hand, the barrel out along his forearm (``prop_pistol``)."""
    F = hold_point()
    a = forearm_angle()
    p = frame(F, a)
    out = cel(smooth(band(p(2, -6), p(52, -5), 5.0)), O["steel"], O["steel_sh"], "#8a8f98", [line([p(4, -7.4), p(50, -6.6)], "#8a8f98", 0.8)], s=1.2)
    stock = smooth([p(-4, -9), p(26, -9), p(28, -3), p(8, -2), p(2, 6), p(-6, 14), p(-12, 16) + (True,), p(-12, 8), p(-8, 0)])
    out += cel(stock, O["wood"], O["wood_sh"], O["wood_lt"], [ellipse(*p(-10, 13), 3.4, 2.6, O["hilt"], INK, 0.7, rot=math.degrees(a) + 50)], s=2)
    # the lock and the cock
    out += cel(smooth([p(0, -12) + (True,), p(8, -12) + (True,), p(8, -6) + (True,), p(0, -6) + (True,)]), O["steel"], O["steel_sh"], None, [], s=1)
    out += [line([p(-1, -11), p(-4, -16), p(1, -17)], INK, 2.6), line([p(-1, -11), p(-4, -16), p(1, -17)], O["steel"], 1.2)]
    return out


def shot_fx():
    """The flash and the smoke off the muzzle (``fx_shot``)."""
    F = hold_point()
    a = forearm_angle()
    p = frame(F, a)
    m = p(56, -5.5)
    out = []
    for k in range(5):
        r, ang = (5, 9, 6, 8, 4)[k] * 1.0, a + math.radians(-60 + k * 30)
        out.append(path(smooth([(m[0], m[1] - 3), (m[0] + (14 + r) * math.cos(ang), m[1] + (14 + r) * math.sin(ang)) + (True,), (m[0], m[1] + 3)]),
                        O["flash"]))
    out.append(ellipse(*p(64, -5.5), 9, 7, O["flash"]))
    out.append(ellipse(*p(62, -5.5), 4.5, 3.5, O["flash_core"]))
    for (t, s_, r) in ((78, -10, 7), (90, -16, 9), (100, -8, 6)):
        out.append(ellipse(*p(t, s_), r, r * 0.8, O["smoke"]))
    return out


def thrust_fx():
    """A gleam streaking off the point of the lunge (``fx_thrust``)."""
    F = hold_point()
    a = forearm_angle()
    p = frame(F, a)
    out = [path(smooth([p(60, -6), p(150, -1), p(166, 0) + (True,), p(150, 1), p(60, 6)]), "#fff6cf"),
           line([p(40, -12), p(110, -9)], "#fff6cf", 1.2), line([p(48, 12), p(116, 9)], "#fff6cf", 1.2)]
    tip = p(150, 0)
    for k in range(4):
        ang = a + math.radians(k * 90 + 45)
        out.append(line([tip, (tip[0] + 12 * math.cos(ang), tip[1] + 12 * math.sin(ang))], "#fff6cf", 1.8))
    return out


#: The parts, in the order they are drawn: (group id, label, part, bone, z, opacity channel).
LAYERS = [
    ("head-back", "Hair - Back", "head_back", "head", 4, ""),
    ("far-arm-upper", "Far Arm - Upper", "far_arm_u", "far_arm_u", 6, ""),
    ("far-arm-lower", "Far Arm - Lower", "far_arm_l", "far_arm_l", 7, ""),
    ("far-hand", "Far Hand", "far_hand", "far_hand", 8, ""),
    ("far-shin", "Far Stocking", "far_leg_l", "far_leg_l", 10, ""),
    ("far-thigh", "Far Thigh", "far_leg_u", "far_leg_u", 11, ""),
    ("far-shoe", "Far Shoe", "far_foot", "far_foot", 12, ""),
    ("near-shin", "Near Stocking", "near_leg_l", "near_leg_l", 20, ""),
    ("near-thigh", "Near Thigh", "near_leg_u", "near_leg_u", 21, ""),
    ("near-shoe", "Near Shoe", "near_foot", "near_foot", 22, ""),
    ("waistcoat", "Waistcoat", "waistcoat", "torso", 30, ""),
    ("coat", "Coat", "coat", "torso", 40, ""),
    ("sash-pistol", "Sash Pistol", "sash_pistol", "torso", 42, ""),
    ("neck", "Neck and Stock", "neck", "torso", 50, ""),
    ("head", "Head", "head", "head", 60, ""),
    ("eye-open", "Eye - Open", "eye_open", "head", 61, "eye_open"),
    ("eye-shut", "Eye - Shut", "eye_shut", "head", 61, "eye_shut"),
    ("eye-dead", "Eye - Dead", "eye_dead", "head", 61, "eye_dead"),
    ("mouth-open", "Mouth - Open", "mouth_open", "head", 62, "mouth_open"),
    ("scabbard", "Scabbard", "scabbard", "body", 68, ""),
    ("rapier-sheathed", "Rapier - Sheathed", "rapier_sheathed", "body", 70, "hilt_sheathed"),
    ("near-arm-upper", "Near Arm - Upper", "near_arm_u", "near_arm_u", 78, ""),
    ("near-arm-lower", "Near Arm - Lower", "near_arm_l", "near_arm_l", 79, ""),
    ("prop-pages", "Prop - Speech", "prop_pages", "near_hand", 80, "prop_pages"),
    ("prop-rapier", "Prop - Rapier", "prop_rapier", "near_hand", 80, "prop_rapier"),
    ("prop-pistol", "Prop - Pistol", "prop_pistol", "near_hand", 80, "prop_pistol"),
    ("near-hand", "Near Hand", "near_hand", "near_hand", 82, ""),
    ("fx-thrust", "FX - Thrust", "fx_thrust", "near_hand", 84, "fx_thrust"),
    ("fx-shot", "FX - Shot", "fx_shot", "near_hand", 84, "fx_shot"),
]
#: Channels shown unless a row hides them.
SHOWN = {"eye_open", "hilt_sheathed", "prop_pages"}


def drawn() -> Dict[str, list]:
    return {
        "head-back": head_back, "far-arm-upper": far_upper, "far-arm-lower": far_lower, "far-hand": far_hand,
        "far-shin": lambda: shin("far"), "far-thigh": lambda: thigh("far"), "far-shoe": lambda: shoe("far"),
        "near-shin": lambda: shin("near"), "near-thigh": lambda: thigh("near"), "near-shoe": lambda: shoe("near"),
        "waistcoat": waistcoat, "coat": coat, "sash-pistol": sash_pistol, "neck": neck_and_stock, "head": head,
        "eye-open": lambda: eyes("open"), "eye-shut": lambda: eyes("shut"), "eye-dead": lambda: eyes("dead"), "mouth-open": mouth_open,
        "scabbard": scabbard, "rapier-sheathed": rapier_sheathed,
        "near-arm-upper": near_upper, "near-arm-lower": near_lower,
        "prop-pages": pages, "prop-rapier": rapier_drawn, "prop-pistol": pistol_drawn, "near-hand": near_fist,
        "fx-thrust": thrust_fx, "fx-shot": shot_fx,
    }


def use(look: str) -> None:
    O.clear()
    O.update(LOOKS[look])


use(LOOK)
JOINTS = joints()


def svg_text(look: str = LOOK) -> str:
    use(look)
    _N[0] = 0
    svg.configure(dx=0, dy=0, ink=INK, ow=OW, colors={})
    svg.PARTS.clear()
    painters = drawn()
    for group, label, name, bone, z, channel in LAYERS:
        extra = (f' data-rig-opacity="{channel}"' + (' data-rig-default="1"' if channel in SHOWN else "")) if channel else ""
        part(group, label, name, bone, z, painters[group](), extra)
    note = ("the Colonial Statesman's look (Jon chose A, 2026-10-18)" if look == LOOK
            else "KEPT, NOT CAST: a Colonial Statesman look Jon kept (2026-10-18), not registered in the cast")
    out = svg.document(
        size=(W, H), design=f"colonial-statesman-{look}", layer_id="colonial-statesman", label=VIEW,
        comment=[f"  <!-- {note}: side view facing right, the ground at y={GROUND_Y:g}.",
                 "       Drawn by scripts/svg_art/colonial_statesman_art.py; each part turns about its JOINTS entry. -->"],
        joints=svg.joints_layer({k: (v[1], v[2]) for k, v in joints().items()}),
    )
    use(LOOK)
    return out


def main() -> None:
    if len(sys.argv) > 2 and sys.argv[1] == "--all":
        out = Path(sys.argv[2])
        out.mkdir(parents=True, exist_ok=True)
        for look in LOOKS:
            (out / f"colonial_statesman_{look}.svg").write_text(svg_text(look), encoding="utf8")
            print(out / f"colonial_statesman_{look}.svg")
        return
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".svg.tmp")
    tmp.write_text(svg_text(), encoding="utf8")
    tmp.replace(OUT)
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
