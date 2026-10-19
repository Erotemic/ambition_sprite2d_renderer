#!/usr/bin/env python3
"""How the President Portrait's SVG was first drawn (reference, not authority).

    uv run python scripts/svg_art/president_portrait_art.py            # his look (B)
    uv run python scripts/svg_art/president_portrait_art.py --all DIR  # every look, to DIR

Writes ``data/characters/president_portrait/president_portrait.svg``; the SVG
owns the art after this has run once. ``JOINTS`` says where each part turns
and ``LAYERS`` lists the parts; ``scripts/build_president_portrait_rig.py``
reads both and authors the rows.

Who: the hall's living presidential portrait ("Ninety-eight percent approval
in this frame"), read as George Washington. He faces us, as a portrait does.

Jon, 2026-10-18, of three redraws: "B for colonial general" — B is
``continental``, the Continental Army general in blue and buff, gold
epaulettes, the pale-blue riband, riding boots, his hand on his sword. A
(``lansdowne``, black velvet and a dress sword) and C (``engraving``, the
dollar-bill duotone, older and stouter, a rolled decree) are KEPT, NOT CAST:
this script draws them (``--all``) and nothing registers them.

Left and right here are the VIEWER's: ``left_*`` is his right arm and leg.
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
OUT = ROOT / "ambition_sprite2d_renderer" / "data" / "characters" / "president_portrait" / "president_portrait.svg"
VIEW = "President Portrait - Front"
LOOK = "continental"
W = H = 560
CX = 280.0
INK = "#1d1714"
OW = 1.5
#: The ground under his soles, in SVG units.
GROUND_Y = 502.0

LOOKS = {
    "lansdowne": dict(
        label="A: Lansdowne - black velvet, dress sword", ink=INK,
        coat="#2b2733", coat_sh="#1b1820", coat_lt="#4a4456", lining="#1b1820",
        vest="#2b2733", vest_sh="#1b1820", vest_lt="#4a4456",
        breech="#2b2733", breech_sh="#1b1820", breech_lt="#4a4456",
        stock="#e9e6dd", stock_sh="#c3beb2", stock_lt="#fbfaf6",
        cuff="coat", button="#5a5462",
        skin="#e7c4a6", skin_sh="#c79a7e", skin_lt="#f3d9c2", skin_dk="#9c6a55", lip="#b97a6c",
        hair="#e6e3dc", hair_sh="#bdb9b0", hair_lt="#faf9f5",
        iris="#4f6170", shoe="#1e1b1f", shoe_lt="#3d3940", buckle="#d7dde3",
        sash=("#3d5aa8", "#f2f0ea", "#b23a3c"), medal="#e0b84e", medal_sh="#a7822e",
        hold="sword", hilt="#d7dde3", hilt_sh="#9aa3ad", scabbard="#26222a",
        sh_k=1.0, hip_k=1.0, legs="stockings", stocking="#d9d6cf", stocking_sh="#aaa59b",
    ),
    "continental": dict(
        label="B: Continental general - blue and buff", ink=INK,
        coat="#283a6a", coat_sh="#1a2648", coat_lt="#40589a", lining="#c7a56c",
        vest="#d8b77f", vest_sh="#b3925d", vest_lt="#ecd4a4",
        breech="#d8b77f", breech_sh="#b3925d", breech_lt="#ecd4a4",
        stock="#f0ede4", stock_sh="#c9c3b5", stock_lt="#ffffff",
        cuff="buff", facing="#d8b77f", facing_sh="#b3925d", facing_lt="#ecd4a4", button="#e3b84c",
        skin="#e6c1a1", skin_sh="#c4977a", skin_lt="#f2d6bd", skin_dk="#99674f", lip="#b57565",
        hair="#e2ded6", hair_sh="#b9b4aa", hair_lt="#f8f7f3",
        iris="#4f6170", shoe="#1e1a1a", shoe_lt="#45393a", buckle="#e3b84c",
        sash=("#86b9df", "#86b9df", "#5f97c2"), medal="#e0b84e", medal_sh="#a7822e",
        epaulette="#e3b84c", epaulette_sh="#a9822c",
        hold="sword", hilt="#e3b84c", hilt_sh="#a9822c", scabbard="#3a2a22",
        sh_k=1.08, hip_k=1.04, legs="boots",
    ),
    "engraving": dict(
        label="C: dollar-bill engraving - older, stouter, decree", ink="#13261b", hatch=True,
        coat="#3f5e49", coat_sh="#2b4434", coat_lt="#5f8169", lining="#2b4434",
        vest="#9db39d", vest_sh="#7a947c", vest_lt="#bccdb9",
        breech="#3f5e49", breech_sh="#2b4434", breech_lt="#5f8169",
        stock="#e7ecdc", stock_sh="#bcc8b3", stock_lt="#f7f9f1",
        cuff="coat", button="#c9d6c0",
        skin="#d9dfc8", skin_sh="#aebaa0", skin_lt="#eef1e2", skin_dk="#6f8669", lip="#8ea38a",
        hair="#eef1e4", hair_sh="#bfcab5", hair_lt="#fbfcf7",
        iris="#2f4a39", shoe="#1c3024", shoe_lt="#3a5444", buckle="#c9d6c0",
        sash=("#2f5a46", "#e7ecdc", "#2f5a46"), medal="#c7b25a", medal_sh="#8e7b34",
        hold="scroll", hilt="#c9d6c0", hilt_sh="#8ea38a", scabbard="#1c3024",
        sh_k=1.04, hip_k=1.16, legs="stockings", stocking="#d6dccb", stocking_sh="#aab6a0", older=True,
    ),
}
for _look in LOOKS.values():
    _look.setdefault("parchment", "#ece2c4")
    _look.setdefault("parchment_sh", "#c4b48a")
    _look.setdefault("seal", "#8c2f2c")
    _look.setdefault("book", "#5e2e26")
    _look.setdefault("book_sh", "#3e1d18")
    _look.setdefault("book_lt", "#7c4136")
    _look.setdefault("glow", "#f3dc8a")

O: dict = {}
#: The head is drawn 12% smaller than its sketch, about the chin: five heads tall.
HEAD_XF = (280.0, 238.0, 0.88)
_N = [0]


# ---- the house cel shading ---------------------------------------------------------

def uid(tag="c"):
    _N[0] += 1
    return f"{tag}{_N[0]}"


def cel(d, base, shade, light=None, items=(), sdir=(1.0, 0.6), ldir=(-1.0, -0.8), s=5.0, l=3.0, sw=None, ink=None):
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
    out.append(path(d, "none", ink or O.get("ink", INK), sw or 2 * OW))
    return out


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


def B(x, y):
    """Body point: widened about the centre line, shoulders by ``sh_k``, hips by ``hip_k``."""
    t = max(0.0, min(1.0, (y - 250.0) / 120.0))
    k = O["sh_k"] + (O["hip_k"] - O["sh_k"]) * t
    return (CX + (x - CX) * k, y)


def Bs(pts):
    return [B(p[0], p[1]) + tuple(p[2:]) for p in pts]


def mir(pts):
    return [(2 * CX - p[0], p[1]) + tuple(p[2:]) for p in reversed(pts)]


def C(d, key, items=(), **kw):
    """Cel-shade ``d`` in the palette family ``key`` (key, key_sh, key_lt)."""
    sh = O[key + "_sh"]
    if O.get("hatch") and key in ("coat", "breech", "vest"):
        sh = "url(#hatch-%s)" % key
    return cel(d, O[key], sh, O.get(key + "_lt"), items, ink=O["ink"], **kw)


def hatch_defs():
    if not O.get("hatch"):
        return []
    out = ["<defs>"]
    for key in ("coat", "breech", "vest"):
        out.append(f'<pattern id="hatch-{key}" patternUnits="userSpaceOnUse" width="3.2" height="3.2" patternTransform="rotate(35)">'
                   f'<rect width="3.2" height="3.2" fill="{O[key]}"/><rect width="1.3" height="3.2" fill="{O[key + "_sh"]}"/></pattern>')
    out.append("</defs>")
    return out


# ---- the skeleton -----------------------------------------------------------------

def arm_points(side):
    """Shoulder, elbow, wrist of the ``left`` (viewer's) or ``right`` arm."""
    if side == "left":
        return B(240, 266), B(228, 318), B(230, 362)
    return B(320, 266), B(346, 312), B(338, 344)


def fist_point():
    """The right (viewer's) fist, closed on the hilt."""
    _s2, e2, w2 = arm_points("right")
    return frame(w2, math.atan2(w2[1] - e2[1], w2[0] - e2[0]))(9, 0)


def knee_x(side):
    return B(263, 420)[0] if side == "left" else B(297, 420)[0]


def joints() -> Dict[str, Tuple[str, float, float]]:
    """Where each bone turns (SVG units): ``bone: (parent, x, y)``, parents first."""
    ls, le, lw = arm_points("left")
    rs, re_, rw = arm_points("right")
    return {
        "body": ("", CX, 338.0),
        "torso": ("body", CX, 338.0),
        "head": ("torso", CX, 240.0),
        "left_arm_u": ("torso", *ls),
        "left_arm_l": ("left_arm_u", *le),
        "left_hand": ("left_arm_l", *lw),
        "right_arm_u": ("torso", *rs),
        "right_arm_l": ("right_arm_u", *re_),
        "right_hand": ("right_arm_l", *rw),
        "left_leg": ("body", knee_x("left"), 404.0),
        "right_leg": ("body", knee_x("right"), 404.0),
    }


# ---- the parts ---------------------------------------------------------------------

def hair_back():
    d = smooth([(252, 200), (249, 178), (258, 162), (280, 156), (302, 162), (311, 178), (308, 200), (300, 210), (260, 210)])
    out = C(d, "hair")
    # one side roll each side at the temple, tucked behind the face over the ear
    for side in (-1, 1):
        x0, x1 = (246, 266) if side < 0 else (314, 294)
        roll = capsule((x0, 206), (x1, 205), 6.4, 6.0)
        out += C(roll, "hair", [line([(x0 - side * 1.5, 203), (x0 - side * 4, 206), (x0 - side * 1.5, 209)], O["hair_sh"], 1.1),
                                line([(x0 - side * 6, 201.5), (x1, 201)], O["hair_lt"], 1.2)], s=3, sdir=(0.2, 1.0))
    return out


def scabbard():
    """The scabbard hanging behind the coat skirt on his left hip."""
    if O["hold"] != "sword":
        return []
    a = B(334, 362)
    out = cel(smooth(band(a, (a[0] + 16, 448), 7.0)), O["scabbard"], O["coat_sh"], None, ink=O["ink"])
    out += cel(smooth(band((a[0] + 15, 438), (a[0] + 17, 452), 8.5)), O["hilt"], O["hilt_sh"], None, ink=O["ink"], s=2)
    return out


def sword_hilt():
    """The hilt, out of the coat at his hip: it stays when his hand leaves it."""
    if O["hold"] != "sword":
        return []
    hilt = B(342, 356)
    f = fist_point()
    out = cel(capsule((hilt[0] - 4, hilt[1] + 10), (hilt[0] + 4, hilt[1] - 8), 2.6, 2.2), O["hilt_sh"], "#5b6168", None, [], s=1, ink=O["ink"])
    out += cel(smooth([(hilt[0] - 10, hilt[1] + 10), (hilt[0] + 6, hilt[1] + 6), (hilt[0] + 9, hilt[1] + 11), (hilt[0] - 8, hilt[1] + 15)]),
               O["hilt"], O["hilt_sh"], None, [], s=2, ink=O["ink"])
    out += cel(smooth([(f[0] - 2.5, f[1] - 14), (f[0] + 3.5, f[1] - 14), (f[0] + 4.5, f[1] - 9), (f[0] - 3.5, f[1] - 9)]),
               O["hilt"], O["hilt_sh"], None, [], s=1.5, ink=O["ink"])
    return out


def coat_back():
    d = smooth(Bs([(234, 338), (326, 338), (334, 404, True), (226, 404, True)]))
    return cel(d, O["lining"], O["coat_sh"], None, ink=O["ink"])


def leg(side):
    """A boot (or stocking) and the shoe, from the knee down."""
    m = (lambda pts: pts) if side == "left" else mir
    dx = knee_x(side) - (263 if side == "left" else 297)
    sh = lambda pts: [(p[0] + dx, p[1]) + tuple(p[2:]) for p in pts]
    out = []
    if O["legs"] == "boots":
        boot = sh(m([(250, 398), (276, 398), (277, 440), (274, 484), (272, 494), (256, 494), (253, 470), (249, 432)]))
        out += cel(smooth(boot), O["shoe"], "#120f10", O["shoe_lt"], [], s=4, ink=O["ink"])
        top = sh(m([(247, 396, True), (279, 396, True), (279, 410, True), (248, 412, True)]))
        out += cel(smooth(top), O["shoe"], "#120f10", O["shoe_lt"], [line(sh(m([(250, 403), (277, 403)])), "#120f10", 1.2)], s=3, ink=O["ink"])
    else:
        st, stsh = O.get("stocking", "#ece9e1"), O.get("stocking_sh", "#c7c2b6")
        sock = sh(m([(252, 396), (275, 396), (277, 440), (273, 468), (272, 488), (259, 488), (256, 468), (250, 440)]))
        out += cel(smooth(sock), st, stsh, "#f7f5f0", [line(sh(m([(266, 446), (265, 478)])), stsh, 1.0)], s=4, ink=O["ink"])
    shoe = sh(m([(255, 482), (272, 481), (277, 490), (275, 500), (258, 502, True), (244, 500), (245, 491)]))
    items = [path(smooth(sh(m([(256, 480, True), (271, 480, True), (271, 489), (257, 489)]))), O["shoe_lt"]),
             path(smooth(sh(m([(258, 486, True), (269, 486, True), (269, 491, True), (258, 491, True)]))), O["buckle"], O["ink"], 0.9)]
    out += cel(smooth(shoe), O["shoe"], "#100d0e", O["shoe_lt"], items, s=3, ink=O["ink"])
    return out


def breeches():
    d = smooth(Bs([(248, 338), (312, 338), (315, 372), (310, 418, True), (285, 419, True), (282, 384), (278, 384), (275, 419, True),
                   (250, 418, True), (245, 372)]))
    items = [line(Bs([(262, 352), (264, 410)]), O["breech_sh"], 1.1), line(Bs([(298, 352), (296, 410)]), O["breech_sh"], 1.1),
             line(Bs([(250, 410), (275, 411)]), O["ink"], 1.0), line(Bs([(285, 411), (310, 410)]), O["ink"], 1.0)]
    for x in (256, 304):
        items.append(ellipse(*B(x, 414), 1.6, 1.6, O["button"], O["ink"], 0.7))
    return C(d, "breech", items)


def waistcoat():
    pts = [(270, 242), (290, 242), (294, 300), (297, 340), (301, 368), (287, 377, True), (280, 372), (273, 377, True), (259, 368),
           (263, 340), (266, 300)]
    items = [ellipse(*B(281, y), 1.7, 1.7, O["button"], O["ink"], 0.7) for y in range(286, 368, 11)]
    items.append(line(Bs([(270, 342), (279, 344)]), O["ink"], 1.0))
    items.append(line(Bs([(283, 344), (292, 342)]), O["ink"], 1.0))
    return C(smooth(Bs(pts)), "vest", items)


COAT_L = [(272, 240), (254, 244), (236, 251), (224, 262), (220, 282), (224, 306), (231, 332), (229, 352), (222, 380),
          (215, 407, True), (238, 413), (256, 410, True), (258, 386), (263, 360), (267, 330), (268, 300), (270, 268)]


def coat():
    # the stand collar behind the neck
    out = C(smooth(Bs([(256, 236), (268, 230), (292, 230), (304, 236), (300, 246), (260, 246)])), "coat", [], s=3)
    for side in (-1, 1):
        pts = Bs(COAT_L if side < 0 else mir(COAT_L))
        px = 236 if side < 0 else 324
        flap = Bs([(px - 12, 356, True), (px + 12, 356, True), (px + 10, 364), (px + 4, 361), (px, 366), (px - 4, 361), (px - 10, 364)])
        items = [path(smooth(flap), O["coat_sh"], O["ink"], 1.0), line(Bs([(px + side * -2, 372), (px + side * 4, 404)]), O["coat_sh"], 1.4)]
        out += C(smooth(pts), "coat", items, sdir=(1.0, 0.5) if side > 0 else (0.6, 0.8))
        if O.get("facing"):
            fl = [(272, 242), (262, 246), (256, 262), (256, 296), (258, 330), (264, 334, True), (268, 300), (270, 266)]
            fl = Bs(fl if side < 0 else mir(fl))
            out += cel(smooth(fl), O["facing"], O["facing_sh"], O["facing_lt"],
                       [ellipse(*B(260 if side < 0 else 300, y), 1.9, 1.9, O["button"], O["ink"], 0.7) for y in (262, 280, 298, 316)],
                       s=3, ink=O["ink"])
        else:
            for (x, y) in [(270, 266), (268, 290), (268, 314), (266, 336)]:
                xx = x - 5 if side < 0 else 2 * CX - x + 5
                out.append(ellipse(*B(xx, y), 1.9, 1.9, O["button"], O["ink"], 0.7))
    return out


def epaulettes():
    if not O.get("epaulette"):
        return []
    out = []
    for side in (-1, 1):
        cx = B(234 if side < 0 else 326, 256)[0]
        for k in range(7):
            x = cx - 12 + k * 4
            out.append(line([(x, 260), (x + side * 0.6, 274)], O["epaulette"], 2.4))
            out.append(line([(x, 268), (x + side * 0.6, 274)], O["epaulette_sh"], 1.2))
        pad = smooth([(cx - 15, 262), (cx - 6, 250), (cx + 8, 249), (cx + 15, 258), (cx + 12, 264), (cx - 12, 266)])
        out += cel(pad, O["epaulette"], O["epaulette_sh"], "#f6db8c", [], s=3, ink=O["ink"])
    return out


def sash():
    a, b = B(238, 255), B(322, 344)
    c1, c2, c3 = O["sash"]
    p = frame(a, math.atan2(b[1] - a[1], b[0] - a[0]))
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    if c2 != c1:
        items = [path(smooth(band(p(-4, 0), p(L + 4, 0), 5.0)), c2), path(smooth(band(p(-4, 0), p(L + 4, 0), 1.6)), c3)]
    else:
        items = [path(smooth(band(p(-4, 4.5), p(L + 4, 4.5), 4.0)), c3)]
    out = cel(smooth(band(a, b, 15.0)), c1, c3, None, items, s=2.5, ink=O["ink"])
    # rosette and medallion at the hip
    m = B(310, 334)
    out += cel(smooth([(m[0] - 7, m[1] - 2), (m[0] - 3, m[1] - 7), (m[0] + 4, m[1] - 7), (m[0] + 7, m[1] - 1), (m[0] + 4, m[1] + 5),
                       (m[0] - 4, m[1] + 5)]), c1, c3, None, [], s=2, ink=O["ink"])
    out += cel(smooth([(m[0] - 5, m[1] + 6), (m[0], m[1] + 3), (m[0] + 5, m[1] + 6), (m[0] + 5, m[1] + 13), (m[0], m[1] + 16), (m[0] - 5, m[1] + 13)]),
               O["medal"], O["medal_sh"], "#f7df95", [ellipse(m[0], m[1] + 9.5, 2.0, 2.0, O["medal_sh"])], s=2.5, l=1.5, ink=O["ink"])
    return out


def neck_and_stock():
    out = C(smooth([(268, 222), (292, 222), (293, 244), (267, 244)]), "skin", [], s=4)
    stock = smooth([(266, 234), (280, 238), (294, 234), (296, 244), (280, 248), (264, 244)])
    out += cel(stock, O["stock"], O["stock_sh"], O["stock_lt"], [], s=3, ink=O["ink"])
    jabot = smooth([(272, 244), (288, 244), (292, 254), (289, 262), (293, 270), (286, 280), (280, 286), (274, 280), (267, 270),
                    (271, 262), (268, 254)])
    items = [line([(276, 250), (274, 262), (277, 276)], O["stock_sh"], 1.1), line([(284, 250), (286, 262), (283, 276)], O["stock_sh"], 1.1),
             line([(270, 262), (290, 262)], O["stock_sh"], 0.9)]
    out += cel(jabot, O["stock"], O["stock_sh"], O["stock_lt"], items, s=3, ink=O["ink"])
    return out


EYES = ((269.5, 204.0), (290.5, 204.0))


def head():
    """The face (without its eyes), the ears and the hair over the crown."""
    older = O.get("older")
    face = [(258, 194), (259, 180), (267, 171), (280, 168), (293, 171), (301, 180), (302, 194), (301, 210), (296, 224), (288, 233),
            (280, 236), (272, 233), (264, 224), (259, 210)]
    if older:  # heavier jaw (the dentures), fuller cheeks
        face = [(258, 194), (259, 180), (267, 171), (280, 168), (293, 171), (301, 180), (302, 194), (303, 212), (298, 226), (289, 235),
                (280, 237), (271, 235), (262, 226), (257, 212)]
    out = []
    for side in (-1, 1):
        ex = 258 if side < 0 else 302
        out += C(smooth([(ex, 204), (ex + side * 5, 203), (ex + side * 7, 210), (ex + side * 5, 220), (ex, 221)]), "skin",
                 [line([(ex + side * 1.5, 207), (ex + side * 4, 212), (ex + side * 2, 217)], O["skin_dk"], 1.0)], s=3)
    sk, dk = O["skin_sh"], O["skin_dk"]
    items = [
        # nose: bridge shade on the far side, the tip, the nostrils
        path(smooth([(282, 198), (285, 212), (287, 220), (283, 222), (281, 212)]), sk),
        ellipse(279.5, 219.5, 2.6, 1.8, O["skin_lt"]),
        line([(275, 222), (277, 224.5)], dk, 1.3), line([(285, 224.5), (287, 222)], dk, 1.3),
        line([(274, 223), (280, 226), (286, 223)], sk, 1.0),
        # the long upper lip and a firm, pressed mouth
        path(smooth([(272, 230), (280, 231.5), (288, 230), (285, 233), (275, 233)]), O["lip"]),
        line([(271, 229.6), (276, 230.4), (280, 231), (284, 230.4), (289, 229.6)], O["ink"], 1.2),
        # cheek bones and the chin
        line([(266, 214), (270, 222)], sk, 1.0), line([(294, 214), (290, 222)], sk, 1.1),
        path(smooth([(274, 235), (280, 233), (286, 235), (280, 237)]), sk),
    ]
    if older:
        items += [line([(268, 222), (271, 231)], sk, 1.2), line([(292, 222), (289, 231)], sk, 1.2),
                  line([(262, 228), (266, 234)], sk, 1.0), line([(298, 228), (294, 234)], sk, 1.0)]
    for (ex, ey), s in zip(EYES, (-1, 1)):
        # brows: low and level, the inner end lower (stern)
        inner, outer = (ex + 5.5 * s * -1, ey - 6.0), (ex - 6.5 * s * -1, ey - 7.8)
        items.append(line([inner, (ex, ey - 8.2), outer], O["hair_sh"], 2.4))
        items.append(line([inner, (ex, ey - 8.2), outer], O["ink"], 0.7))
        items.append(line([(ex - 3.5, ey + 3.6), (ex + 3.5, ey + 3.6)], sk, 0.9))
    items.append(line([(280, 196), (280, 200)], sk, 1.0))  # the furrow between the brows
    out += C(smooth(face), "skin", items, sdir=(1.0, 0.4), s=5)
    # the hair over the crown, swept back off a high forehead
    front = smooth([(256, 196), (256, 180), (264, 166), (280, 160), (296, 166), (304, 180), (304, 196), (300, 186), (293, 178), (284, 182),
                    (276, 178), (266, 181), (261, 188)])
    strands = [line([(266, 170), (276, 176)], O["hair_sh"], 1.1), line([(282, 165), (288, 176)], O["hair_sh"], 1.1),
               line([(294, 170), (299, 180)], O["hair_sh"], 1.1)]
    out += C(front, "hair", strands, s=4)
    return out


def eyes(kind):
    """One set of eyes, small under heavy lids (the rig shows one at a time)."""
    out = []
    for ex, ey in EYES:
        if kind == "open":
            white = smooth([(ex - 5, ey), (ex - 1.5, ey - 2.6), (ex + 3.5, ey - 1.6), (ex + 5, ey + 0.4), (ex + 1, ey + 2.0), (ex - 3, ey + 1.6)])
            out += [path(white, "#f4f1ea"), ellipse(ex + 0.3, ey - 0.1, 1.9, 2.1, O["iris"]), ellipse(ex + 0.3, ey - 0.1, 0.9, 0.9, "#141414"),
                    ellipse(ex - 0.4, ey - 0.8, 0.5, 0.5, "#ffffff"),
                    line([(ex - 5.4, ey + 0.2), (ex - 1.5, ey - 2.9), (ex + 3.5, ey - 2.0), (ex + 5.6, ey + 0.3)], O["ink"], 1.5)]
        elif kind == "shut":
            out.append(line([(ex - 5.2, ey - 0.4), (ex, ey + 1.6), (ex + 5.2, ey - 0.4)], O["ink"], 1.5))
        else:
            out += [line([(ex - 3.4, ey - 2.6), (ex + 3.4, ey + 2.6)], O["ink"], 1.4), line([(ex - 3.4, ey + 2.6), (ex + 3.4, ey - 2.6)], O["ink"], 1.4)]
    return out


def mouth_open():
    """His mouth open to speak, over the pressed one."""
    return [ellipse(280, 231, 9.5, 3.6, O["skin"]),
            path(smooth([(273, 229), (280, 228), (287, 229), (285, 234), (280, 236), (275, 234)]), "#5a2a2a", O["ink"], 1.2),
            path(smooth([(276, 233), (280, 232), (284, 233), (280, 235.5)]), O["lip"])]


def hand(wrist, ang, thumb):
    """A relaxed open hand, back toward us, fingers together, thumb toward ``thumb`` (+1/-1 across)."""
    fill, sh = O["skin"], O["skin_sh"]
    p = frame(wrist, ang)
    sil = smooth([p(-1, -6.5), p(8, -7.6), p(17, -7.2), p(25, -5.8), p(29, -2), p(28.5, 2.5), p(24, 6), p(15, 7.4), p(7, 7.2), p(-1, 6.5)])
    items = [line([p(17, -3.4), p(26, -3.0)], sh, 1.0), line([p(17, 0.2), p(27.5, 0.2)], sh, 1.0), line([p(16, 3.6), p(25, 3.6)], sh, 1.0),
             line([p(12, -6), p(14, 0), p(12, 6)], sh, 0.8)]
    out = cel(sil, fill, sh, O["skin_lt"], items, sdir=(0.8, 0.8), s=3.5, ink=O["ink"])
    out += cel(capsule(p(5, thumb * 6.0), p(16, thumb * 9.4), 3.4, 2.6), fill, sh, None, [], s=2, ink=O["ink"])
    return out


def fist(at):
    x, y = at
    fill, sh = O["skin"], O["skin_sh"]
    sil = smooth([(x - 9, y - 7), (x + 1, y - 9), (x + 9, y - 6), (x + 10, y + 2), (x + 6, y + 8), (x - 4, y + 8), (x - 10, y + 2)])
    items = [line([(x - 6, y - 1), (x + 8, y - 1)], sh, 1.0), line([(x - 5, y + 3.5), (x + 7, y + 3.5)], sh, 1.0),
             line([(x - 1, y - 8), (x - 1, y - 2)], sh, 0.8)]
    out = cel(sil, fill, sh, O["skin_lt"], items, s=3, ink=O["ink"])
    out += cel(capsule((x - 7, y - 6), (x + 3, y - 3), 3.0, 2.6), fill, sh, None, [], s=1.6, ink=O["ink"])
    return out


def cuff(wr, ang):
    p = frame(wr, ang)
    lace = smooth([p(2, -10), p(10, -9), p(12, -5), p(10, 0), p(12, 5), p(10, 9), p(2, 10), p(4, 0)])
    out = cel(lace, O["stock"], O["stock_sh"], O["stock_lt"], [line([p(5, -5), p(10, 0), p(5, 5)], O["stock_sh"], 0.9)], s=2.5, ink=O["ink"])
    key = "facing" if O["cuff"] == "buff" else "coat"
    c = smooth([p(-14, -13) + (True,), p(2, -12.5) + (True,), p(4, 12) + (True,), p(-13, 13) + (True,)])
    detail = [ellipse(*p(-5, -6), 1.6, 1.6, O["button"], O["ink"], 0.6), ellipse(*p(-5, 0), 1.6, 1.6, O["button"], O["ink"], 0.6),
              line([p(-13, -12), p(-12, 12)], O[key + "_sh"], 1.4)]
    out += cel(c, O[key], O[key + "_sh"], O.get(key + "_lt"), detail, s=3, ink=O["ink"])
    return out


def upper_arm(side):
    s, e, _w = arm_points(side)
    return C(capsule(s, e, 13.5, 11.5), "coat", [], s=4)


def forearm(side):
    _s, e, w = arm_points(side)
    out = C(capsule(e, w, 11.5, 10.0), "coat", [], s=4)
    out.append(ellipse(e[0], e[1], 10.1, 10.1, O["coat"]))
    out += cuff(w, math.atan2(w[1] - e[1], w[0] - e[0]))
    return out


def left_hand():
    _s, e, w = arm_points("left")
    ang = math.atan2(w[1] - e[1], w[0] - e[0])
    return hand(frame(w, ang)(8, 0), ang + 0.05, 1)


def right_hand():
    f = fist_point()
    out = []
    if O["hold"] == "scroll":
        # look C: the rolled decree held upright against the hip
        roll = smooth(band((f[0] - 12, f[1] + 24), (f[0] + 20, f[1] - 18), 12.0))
        out += cel(roll, O["parchment"], O["parchment_sh"], "#fbf8ea",
                   [line([(f[0] + 12, f[1] - 18), (f[0] + 22, f[1] - 10)], O["parchment_sh"], 1.0),
                    ellipse(f[0] + 19, f[1] - 15, 3.2, 3.2, O["parchment_sh"]), ellipse(f[0] + 19, f[1] - 15, 1.2, 1.2, O["ink"])], s=3, ink=O["ink"])
        out += cel(smooth([(f[0] - 8, f[1] + 12), (f[0] - 1, f[1] + 14), (f[0] - 4, f[1] + 26, True), (f[0] - 7, f[1] + 19), (f[0] - 11, f[1] + 24, True)]),
                   O["seal"], "#5e1d1b", None, [], s=1.5, ink=O["ink"])
    return out + fist(f)


# ---- the props and effects (each shown by its own channel) -------------------------------

def proclamation():
    """The decree, unrolled and held up by its top roll in the right fist (``prop_decree``)."""
    x, y = fist_point()
    top, bot = y - 4, y + 66
    sheet_d = smooth([(x - 4, top) + (True,), (x + 46, top) + (True,), (x + 47, bot - 4), (x + 42, bot) + (True,), (x - 3, bot) + (True,)])
    items = [line([(x + 6, top + 14 + 7 * i), (x + 38 - (i % 3) * 6, top + 14 + 7 * i)], O["parchment_sh"], 1.1) for i in range(6)]
    items.append(line([(x + 8, top + 8), (x + 34, top + 8)], "#3a2a22", 1.6))
    out = cel(sheet_d, O["parchment"], O["parchment_sh"], "#fbf6e6", items, s=3, ink=O["ink"])
    out += cel(capsule((x - 7, top), (x + 50, top), 4.5, 4.5), O["parchment"], O["parchment_sh"], "#fbf6e6", [], s=2, ink=O["ink"])
    out += cel(capsule((x - 5, bot), (x + 48, bot), 3.6, 3.6), O["parchment"], O["parchment_sh"], None, [], s=2, ink=O["ink"])
    sx, sy = x + 34, bot - 12
    out += cel(smooth([(sx - 6, sy - 5), (sx, sy - 7), (sx + 6, sy - 5), (sx + 7, sy + 1), (sx + 3, sy + 6), (sx - 4, sy + 6), (sx - 7, sy + 1)]),
               O["seal"], "#5e1d1b", None, [ellipse(sx, sy, 2.2, 2.2, "#5e1d1b")], s=1.5, ink=O["ink"])
    return out


def oath_book():
    """The book he swears on, held against his chest in the right fist (``prop_book``)."""
    x, y = fist_point()
    cover = smooth([(x - 26, y - 22) + (True,), (x + 4, y - 24) + (True,), (x + 6, y + 14) + (True,), (x - 24, y + 16) + (True,)])
    items = [line([(x - 21, y - 21), (x - 20, y + 14)], O["book_sh"], 2.2),
             path(smooth([(x - 14, y - 12) + (True,), (x - 3, y - 13) + (True,), (x - 2, y - 4) + (True,), (x - 13, y - 3) + (True,)]), O["medal"])]
    out = cel(smooth([(x - 23, y + 14) + (True,), (x + 6, y + 12) + (True,), (x + 6, y + 17) + (True,), (x - 23, y + 19) + (True,)]),
              O["parchment"], O["parchment_sh"], None, [], s=1.5, ink=O["ink"])
    out += cel(cover, O["book"], O["book_sh"], O["book_lt"], items, s=3, ink=O["ink"])
    return out


def flourish_fx():
    """A gleam off the decree as he presents it (``fx_decree``)."""
    x, y = fist_point()
    cx, cy = x + 22, y + 30
    out = []
    for k, (r, a0, a1) in enumerate(((44, 200, 340), (54, 215, 325))):
        pts = [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in range(a0, a1 + 1, 10)]
        out.append(line(pts, O["glow"], 3.0 - k))
    for (dx, dy) in ((-30, -40), (52, -36), (60, 8)):
        out.append(path(smooth([(cx + dx, cy + dy - 6), (cx + dx + 2, cy + dy - 2), (cx + dx + 6, cy + dy), (cx + dx + 2, cy + dy + 2),
                                (cx + dx, cy + dy + 6), (cx + dx - 2, cy + dy + 2), (cx + dx - 6, cy + dy), (cx + dx - 2, cy + dy - 2)]), O["glow"]))
    return out


def oath_fx():
    """Rays about the raised right hand (``fx_oath``)."""
    _s, e, w = arm_points("left")
    ang = math.atan2(w[1] - e[1], w[0] - e[0])
    c = frame(w, ang)(22, 0)
    out = []
    for k in range(7):
        a = ang + math.radians(-60 + k * 20)
        out.append(line([(c[0] + 22 * math.cos(a), c[1] + 22 * math.sin(a)), (c[0] + 34 * math.cos(a), c[1] + 34 * math.sin(a))], O["glow"], 2.4))
    return out


#: The parts, in the order they are drawn: (group id, label, part, bone, z, opacity channel).
LAYERS = [
    ("hair-back", "Hair - Back", "hair_back", "head", 5, ""),
    ("scabbard", "Scabbard", "scabbard", "body", 8, ""),
    ("coat-back", "Coat Lining", "coat_back", "body", 10, ""),
    ("right-leg", "Right Leg", "right_leg", "right_leg", 20, ""),
    ("left-leg", "Left Leg", "left_leg", "left_leg", 21, ""),
    ("breeches", "Breeches", "breeches", "body", 30, ""),
    ("waistcoat", "Waistcoat", "waistcoat", "torso", 40, ""),
    ("coat", "Coat", "coat", "torso", 45, ""),
    ("epaulettes", "Epaulettes", "epaulettes", "torso", 46, ""),
    ("sash", "Sash", "sash", "torso", 48, ""),
    ("neck", "Neck and Stock", "neck", "torso", 50, ""),
    ("head", "Head", "head", "head", 60, ""),
    ("eye-open", "Eyes - Open", "eye_open", "head", 61, "eye_open"),
    ("eye-shut", "Eyes - Shut", "eye_shut", "head", 61, "eye_shut"),
    ("eye-dead", "Eyes - Dead", "eye_dead", "head", 61, "eye_dead"),
    ("mouth-open", "Mouth - Open", "mouth_open", "head", 62, "mouth_open"),
    ("sword-hilt", "Sword Hilt", "sword_hilt", "body", 70, ""),
    ("left-hand", "Left Hand", "left_hand", "left_hand", 74, ""),
    ("left-arm-upper", "Left Arm - Upper", "left_arm_u", "left_arm_u", 75, ""),
    ("left-arm-lower", "Left Arm - Lower", "left_arm_l", "left_arm_l", 76, ""),
    ("fx-oath", "FX - Oath", "fx_oath", "left_hand", 77, "fx_oath"),
    ("right-arm-upper", "Right Arm - Upper", "right_arm_u", "right_arm_u", 80, ""),
    ("right-arm-lower", "Right Arm - Lower", "right_arm_l", "right_arm_l", 81, ""),
    ("prop-decree", "Prop - Decree", "prop_decree", "right_hand", 82, "prop_decree"),
    ("prop-book", "Prop - Book", "prop_book", "right_hand", 82, "prop_book"),
    ("right-hand", "Right Hand", "right_hand", "right_hand", 83, ""),
    ("fx-decree", "FX - Decree", "fx_decree", "right_hand", 84, "fx_decree"),
]
#: Parts drawn about the head's own scale (``HEAD_XF``).
HEAD_PARTS = {"hair-back", "head", "eye-open", "eye-shut", "eye-dead", "mouth-open"}
#: A channel shown unless a row hides it.
SHOWN = {"eye_open"}


def drawn() -> Dict[str, list]:
    return {
        "hair-back": hair_back, "scabbard": scabbard, "coat-back": coat_back,
        "right-leg": lambda: leg("right"), "left-leg": lambda: leg("left"), "breeches": breeches,
        "waistcoat": waistcoat, "coat": coat, "epaulettes": epaulettes, "sash": sash, "neck": neck_and_stock,
        "head": head, "eye-open": lambda: eyes("open"), "eye-shut": lambda: eyes("shut"), "eye-dead": lambda: eyes("dead"),
        "mouth-open": mouth_open, "sword-hilt": sword_hilt,
        "left-hand": left_hand, "left-arm-upper": lambda: upper_arm("left"), "left-arm-lower": lambda: forearm("left"),
        "fx-oath": oath_fx,
        "right-arm-upper": lambda: upper_arm("right"), "right-arm-lower": lambda: forearm("right"),
        "prop-decree": proclamation, "prop-book": oath_book, "right-hand": right_hand, "fx-decree": flourish_fx,
    }


def use(look: str) -> None:
    O.clear()
    O.update(LOOKS[look])


use(LOOK)
JOINTS = joints()


def svg_text(look: str = LOOK) -> str:
    use(look)
    _N[0] = 0
    svg.configure(dx=0, dy=0, ink=O["ink"], ow=OW, colors={})
    svg.PARTS.clear()
    painters = drawn()
    if O.get("hatch"):
        svg.part("defs", "Defs", "defs", "body", 0, hatch_defs())
    for group, label, name, bone, z, channel in LAYERS:
        svg.transform(HEAD_XF if group in HEAD_PARTS else None)
        body = painters[group]()
        svg.transform(None)
        extra = (f' data-rig-opacity="{channel}"' + (' data-rig-default="1"' if channel in SHOWN else "")) if channel else ""
        part(group, label, name, bone, z, body, extra)
    note = ("the President Portrait's look (Jon chose B, 2026-10-18)" if look == LOOK
            else "KEPT, NOT CAST: a President Portrait look Jon kept (2026-10-18), not registered in the cast")
    out = svg.document(
        size=(W, H), design=f"president-portrait-{look}", layer_id="president-portrait", label=VIEW,
        comment=[f"  <!-- {note}: front view, the ground at y={GROUND_Y:g}.",
                 "       Drawn by scripts/svg_art/president_portrait_art.py; each part turns about its JOINTS entry. -->"],
        joints=svg.joints_layer({k: (v[1], v[2]) for k, v in joints().items()}),
    )
    use(LOOK)
    return out


def main() -> None:
    if len(sys.argv) > 2 and sys.argv[1] == "--all":
        out = Path(sys.argv[2])
        out.mkdir(parents=True, exist_ok=True)
        for look in LOOKS:
            (out / f"president_portrait_{look}.svg").write_text(svg_text(look), encoding="utf8")
            print(out / f"president_portrait_{look}.svg")
        return
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".svg.tmp")
    tmp.write_text(svg_text(), encoding="utf8")
    tmp.replace(OUT)
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
