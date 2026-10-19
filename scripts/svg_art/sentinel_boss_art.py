#!/usr/bin/env python3
"""How the three sentinel bosses' SVGs were first drawn (reference, not authority).

    uv run python scripts/svg_art/sentinel_boss_art.py            # all three, into data/characters/
    uv run python scripts/svg_art/sentinel_boss_art.py --all DIR  # all three, to DIR

The generic v1 boss (the renderer's ``boss`` target) was one floating wraith
worn by every boss without art of its own. Jon, 2026-10-18, of three redraws:
"for the boss all 3 are good and each can be used to make some of the non
unique bosses unique-ish". Each look is its own sheet:

* ``gradient_sentinel``: an eldritch shroud, a spike halo, a hem in stepped
  bands, tendril arms. The ``gradient_sentinel`` sheet key, the fallback every
  boss without art wears, and the hall's "Boss".
* ``clockwork_warden``: a brass and verdigris automaton, a gear halo, lens
  eyes, a clock heart, pincers and a pendulum. The Clockwork Warden.
* ``hooded_sentinel``: the old wraith redrawn, a cowl, a bone mask, three
  eyes, jointed arms. Mode Collapse.

One skeleton for all three, side view facing right. ``JOINTS`` says where
each part turns and ``LAYERS`` lists the parts; a look that has no such part
(only the Warden has a pendulum) draws it empty.
``scripts/build_sentinel_boss_rigs.py`` reads both and authors the rows.
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
DATA = ROOT / "ambition_sprite2d_renderer" / "data" / "characters"
W, H = 560, 560
OW = 1.6

#: Each look's target (its sheet is ``<target>_spritesheet.png``).
TARGETS = {
    "gradient_sentinel": "gradient_sentinel_boss",
    "clockwork_warden": "clockwork_warden_boss",
    "hooded_sentinel": "hooded_sentinel_boss",
}

#: Where each bone turns (SVG units): ``bone: (parent, x, y)``, parents first.
#: ``body`` is the cloak's middle, the point the whole of him floats about;
#: ``floor`` is the floor under him, which the slam's shock stays on.
JOINTS: Dict[str, Tuple[str, float, float]] = {
    "body": ("", 300.0, 300.0),
    "floor": ("", 300.0, 470.0),
    "head": ("body", 306.0, 232.0),
    "halo": ("head", 294.0, 162.0),
    "pendulum": ("body", 268.0, 380.0),
    "far_arm_u": ("body", 256.0, 242.0),
    "far_arm_l": ("far_arm_u", 204.0, 264.0),
    "far_hand": ("far_arm_l", 150.0, 238.0),
    "near_arm_u": ("body", 338.0, 252.0),
    "near_arm_l": ("near_arm_u", 392.0, 284.0),
    "near_hand": ("near_arm_l", 446.0, 262.0),
}

LOOKS = {
    "hooded_sentinel": dict(
        name="Hooded Sentinel",
        ink="#120a18", cloak="#2b1f3a", cloak_sh="#1a1224", cloak_lt="#443259", hood_in="#0c0710",
        mask="#d9d0e2", mask_sh="#a79bb8", mask_lt="#f4effa", mask_dk="#6d6080",
        limb="#3a2a4e", limb_sh="#241830", limb_lt="#5a4574", joint="#2a1d38",
        claw="#e8e0ee", claw_sh="#b0a3bf",
        eye="#ff4bdd", eye_hi="#ffd6f6", halo="#ff4bdd", core="#ff4bdd", core_hi="#ffd6f6",
        trim="#5a4574", trim_sh="#3a2a4e", trim_lt="#7d64a0",
        kind="hood"),
    "clockwork_warden": dict(
        name="Clockwork Warden",
        ink="#14100a", cloak="#2f5552", cloak_sh="#1f3b39", cloak_lt="#4a7a74", hood_in="#11100c",
        mask="#d8c79a", mask_sh="#a8955f", mask_lt="#f2e6c2", mask_dk="#6f5d33",
        limb="#b08a3e", limb_sh="#7c5f26", limb_lt="#dcb868", joint="#4d3c1c",
        claw="#c9cdd2", claw_sh="#8d9299",
        eye="#ffb02e", eye_hi="#fff0c4", halo="#ffb02e", core="#f4ead0", core_hi="#fffaf0",
        trim="#b08a3e", trim_sh="#7c5f26", trim_lt="#e6c473",
        kind="clock"),
    "gradient_sentinel": dict(
        name="Gradient Sentinel",
        ink="#0a0b18", cloak="#1d2348", cloak_sh="#121632", cloak_lt="#2d3768", hood_in="#05060e",
        mask="#ece6dc", mask_sh="#b9b0a2", mask_lt="#ffffff", mask_dk="#77705f",
        limb="#232a56", limb_sh="#151a3a", limb_lt="#36417a", joint="#1a1f40",
        claw="#ece6dc", claw_sh="#b9b0a2",
        eye="#4fe3ff", eye_hi="#e6fbff", halo="#4fe3ff", core="#ff4fc8", core_hi="#ffe0f4",
        trim="#3a2f7a", trim_sh="#261f55", trim_lt="#5a4bb0",
        bands=["#3a2f7a", "#6a2f8c", "#a8329a", "#e0409a"],
        kind="eldritch"),
}


def J(name):
    _, x, y = JOINTS[name]
    return (x, y)


# ------------------------------------------------------------------ kit ---

BIG = "M-4000,-4000 H6000 V6000 H-4000 Z "
_N = [0]


def cid(prefix="sb"):
    _N[0] += 1
    return f"{prefix}{_N[0]}"


def bands(sil, sh, lt, k=6.0, m=3.0):
    """The shade band (down-back) and light band (up-front) items of ``sil``,
    to clip inside it."""
    out = []
    if sh:
        out.append(f'<g transform="translate({k:.2f},{-k * 0.75:.2f})"><path d="{BIG}{sil}" fill="{sh}" fill-rule="evenodd" /></g>')
    if lt:
        out.append(f'<g transform="translate({-m:.2f},{m * 0.9:.2f})"><path d="{BIG}{sil}" fill="{lt}" fill-rule="evenodd" /></g>')
    return out


def cel(sil, base, sh=None, lt=None, extras=(), k=6.0, m=3.0, outline=None, ow=None):
    """A shape: its fill, cel bands and ``extras`` clipped inside, then its
    outline (``outline=False``: a group's ink draws it)."""
    c = cid()
    items = [path(sil, base)] + bands(sil, sh, lt, k, m) + list(extras)
    out = [f'<clipPath id="{c}"><path d="{sil}" /></clipPath>', f'<g clip-path="url(#{c})">'] + items + ["</g>"]
    if outline is not False:
        out.append(path(sil, "none", outline or svg.INK, ow or 2 * svg.OW))
    return out


def group(shapes, ow=None):
    """``shapes`` = (sil, base, sh, lt, extras, k, m): one ink silhouette
    under all of them, then their fills with no outline."""
    w = ow or 2 * svg.OW
    out = [path(s[0], svg.INK, svg.INK, w * 2) for s in shapes]
    for s in shapes:
        out += cel(s[0], s[1], s[2], s[3], s[4] if len(s) > 4 else (), s[5] if len(s) > 5 else 6.0,
                   s[6] if len(s) > 6 else 3.0, outline=False)
    return out


def shade(hex_color, f):
    """``hex_color`` with its channels scaled by ``f`` (<1 darker, >1 toward white)."""
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


def glow_ring(cx, cy, rx, ry, color, alpha=0.28):
    """An authored soft glow: a flat translucent ellipse, no blur."""
    x, y = svg.P(cx, cy)
    return f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="{color}" fill-opacity="{alpha}" />'


def disc(c, r, n=24):
    return svg.poly([(c[0] + math.cos(a) * r, c[1] + math.sin(a) * r) for a in [i * math.tau / n for i in range(n)]])


def catmull(points, samples=8):
    """Sample an open Catmull-Rom curve through ``points``."""
    out = []
    n = len(points)
    for i in range(n - 1):
        p0, p1, p2, p3 = points[max(i - 1, 0)], points[i], points[i + 1], points[min(i + 2, n - 1)]
        for s in range(samples):
            t = s / samples
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    out.append(points[-1])
    return out


def tube(points, w0, w1):
    """A tapered tube along a smooth curve (a tendril), as a closed path."""
    cl = catmull(points, 6)
    n = len(cl)
    L, R = [], []
    for i, p in enumerate(cl):
        ux, uy = norm(cl[max(i - 1, 0)], cl[min(i + 1, n - 1)])
        w = w0 + (w1 - w0) * (i / (n - 1))
        L.append((p[0] - uy * w, p[1] + ux * w))
        R.append((p[0] + uy * w, p[1] - ux * w))
    return svg.poly(L + R[::-1])


# ----------------------------------------------------------------- halo ---

def halo(o):
    """The gear ring (the Warden) or the spike crown (the Gradient Sentinel),
    behind the head; it turns about ``halo``."""
    cx, cy = J("halo")
    out = []
    if o["kind"] == "clock":
        r, n = 82, 18
        teeth = []
        for i in range(n * 2):
            a = math.tau * i / (n * 2)
            rr = r + (9 if i % 2 == 0 else 0)
            a0, a1 = a - math.pi / (n * 2) * 0.6, a + math.pi / (n * 2) * 0.6
            teeth += [(cx + math.cos(a0) * rr, cy + math.sin(a0) * rr, True), (cx + math.cos(a1) * rr, cy + math.sin(a1) * rr, True)]
        ring = svg.poly(teeth)
        d = ring + " " + disc((cx, cy), r - 14, 48)
        c = cid()
        out += [f'<clipPath id="{c}"><path d="{d}" fill-rule="evenodd" clip-rule="evenodd" /></clipPath>', f'<g clip-path="url(#{c})">',
                path(ring, o["trim"]),
                f'<g transform="translate(5,4)"><path d="{BIG}{ring}" fill="{o["trim_sh"]}" fill-rule="evenodd" /></g>',
                ellipse(cx, cy, r - 6, r - 6, "none", o["trim_lt"], 1.4), "</g>",
                f'<path d="{d}" fill="none" stroke="{o["ink"]}" stroke-width="2.2" fill-rule="evenodd" />']
        for k in range(6):
            a = math.tau * k / 6 + 0.3
            out += cel(capsule((cx + math.cos(a) * 22, cy + math.sin(a) * 22), (cx + math.cos(a) * (r - 12), cy + math.sin(a) * (r - 12)), 4, 3),
                       o["trim"], o["trim_sh"], o["trim_lt"], k=2, m=1, outline=o["ink"], ow=1.4)
    elif o["kind"] == "eldritch":
        for k in range(11):
            a = math.radians(-205 + k * 23)
            L = 132 if k % 2 == 0 else 108
            b0 = (cx + math.cos(a - 0.07) * 62, cy + math.sin(a - 0.07) * 62)
            b1 = (cx + math.cos(a + 0.07) * 62, cy + math.sin(a + 0.07) * 62)
            tip = (cx + math.cos(a) * L, cy + math.sin(a) * L)
            mid = (cx + math.cos(a) * (L - 24), cy + math.sin(a) * (L - 24))
            s = smooth([b0 + (True,), tip + (True,), b1 + (True,)])
            out += cel(s, o["trim"], o["trim_sh"], o["trim_lt"], [line([mid, tip], o["eye"] if k % 2 == 0 else o["core"], 3.2)],
                       k=2, m=1, outline=o["ink"], ow=1.5)
    return out


# ----------------------------------------------------------------- head ---

def head(o):
    """The hood (or cowl), the void it opens on, the mask and the mouth; the
    eyes are their own layers."""
    ink, kind = o["ink"], o["kind"]
    out = []
    if kind == "hood":
        hood = smooth([(254, 200), (244, 152), (258, 114), (294, 92), (336, 98), (364, 124), (374, 160), (370, 198), (352, 228), (318, 240),
                       (278, 238)])
    elif kind == "clock":
        hood = smooth([(254, 204), (246, 156), (262, 116), (296, 98), (338, 104), (362, 128), (370, 160), (366, 200), (350, 228), (318, 240),
                       (278, 238)])
    else:
        # a tall hood whose peak droops back
        hood = smooth([(254, 204), (240, 150), (232, 98), (214, 58, True), (254, 80), (292, 90), (334, 98), (362, 124), (374, 160),
                       (370, 198), (352, 228), (318, 240), (278, 238)])
    det = []
    if kind == "clock":
        for k in range(7):
            a = math.radians(200 + k * 22)
            det.append(ellipse(300 + math.cos(a) * 60, 168 + math.sin(a) * 62, 2.2, 2.2, o["trim_lt"], ink, 0.8))
        det.append(line([(262, 132), (300, 112), (344, 118)], o["cloak_sh"], 1.6))
    else:
        det.append(line([(262, 140), (272, 190), (290, 228)], o["cloak_sh"], 1.8))
    out += cel(hood, o["cloak"], o["cloak_sh"], o["cloak_lt"], det, k=12, m=4, outline=ink, ow=2 * OW)
    void = smooth([(290, 132), (322, 116), (356, 124), (370, 154), (370, 192), (356, 220), (326, 232), (300, 226), (284, 196), (282, 160)])
    out.append(path(void, o["hood_in"], ink, 1.4))
    if kind == "clock":
        rim = smooth([(286, 130), (322, 112), (360, 122), (376, 154), (376, 194), (360, 224), (326, 238), (296, 230), (278, 198), (276, 158)])
        ring_d = rim + " " + void
        c = cid()
        out += [f'<clipPath id="{c}"><path d="{ring_d}" clip-rule="evenodd" /></clipPath>', f'<g clip-path="url(#{c})">',
                path(rim, o["trim"]), f'<g transform="translate(4,3)"><path d="{BIG}{rim}" fill="{o["trim_sh"]}" fill-rule="evenodd" /></g>', "</g>",
                f'<path d="{ring_d}" fill="none" stroke="{ink}" stroke-width="1.6" fill-rule="evenodd" />']
    if kind == "eldritch":
        mask = smooth([(300, 138), (322, 126), (346, 132), (360, 152), (362, 182), (356, 214), (344, 240, True), (330, 222), (312, 220),
                       (298, 206), (292, 176)])
    else:
        mask = smooth([(298, 142), (320, 130), (346, 136), (362, 158), (364, 186), (354, 210), (336, 224), (314, 226), (298, 212),
                       (292, 178)])
    mdet = []
    if kind == "eldritch":
        mdet.append(line([(316, 134), (312, 146), (318, 152)], o["mask_dk"], 1.3))  # a crack in the brow
    if kind == "clock":
        mdet += [line([(300, 192), (362, 186)], o["mask_dk"], 1.2), ellipse(304, 150, 2, 2, o["mask_dk"]), ellipse(300, 204, 2, 2, o["mask_dk"])]
    out += cel(mask, o["mask"], o["mask_sh"], o["mask_lt"], mdet, k=9, m=3, outline=ink, ow=2 * OW)
    # the eye sockets, dark under whichever eyes are showing
    if kind == "hood":
        for x, y, r in HOOD_EYES:
            out.append(path(smooth([(x - r, y + 1), (x - 1, y - r), (x + r - 1, y - 2), (x + r - 2, y + r * 0.6), (x - 2, y + r * 0.82)]),
                            o["hood_in"], ink, 1.2))
    elif kind == "clock":
        for x, y, r in CLOCK_EYES:
            out += cel(smooth([(x - r - 3, y), (x, y - r - 3), (x + r + 3, y), (x, y + r + 3)]), o["trim"], o["trim_sh"], o["trim_lt"], k=2, m=1,
                       outline=ink, ow=1.4)
            out.append(ellipse(x, y, r, r, o["hood_in"], ink, 1.0))
    else:
        out.append(path(smooth([(337, 128, True), (343, 140), (337, 152, True), (331, 140)]), o["hood_in"], ink, 1.2))
        for x, y, r in ELDRITCH_EYES:
            out.append(path(smooth([(x - r - 3, y + 2), (x - 1, y - r + 1), (x + r + 1, y - 1), (x + 1, y + r * 0.6)]), o["hood_in"], ink, 1.2))
    # the mouth
    if kind == "clock":
        grille = smooth([(306, 200, True), (356, 194, True), (354, 214, True), (312, 218, True)])
        bars = [line([(312 + i * 8, 199 - i * 0.6), (314 + i * 7.6, 216 - i * 0.4)], o["mask_lt"], 2.0) for i in range(6)]
        out += cel(grille, o["hood_in"], None, None, bars, outline=ink, ow=1.4)
    else:
        my = 204 if kind == "hood" else 206
        mouth = smooth([(306, my - 2, True), (330, my - 6), (358, my - 10, True), (352, my + 6), (330, my + 12), (310, my + 8)])
        teeth = []
        for i in range(6):
            x = 312 + i * 7.6
            yt = my - 3 - i * 1.2
            teeth.append(path(smooth([(x - 3.2, yt - 3, True), (x + 3.2, yt - 3, True), (x + 0.4, yt + 5, True)]), o["claw"], ink, 0.8))
            yb = my + 9 - i * 0.7
            teeth.append(path(smooth([(x - 2.8 + 3, yb + 3, True), (x + 3.2 + 3, yb + 3, True), (x + 3.4, yb - 4.5, True)]), o["claw"], ink, 0.8))
        out += cel(mouth, o["hood_in"], None, None, teeth, outline=ink, ow=1.4)
    return out


HOOD_EYES = [(318, 168, 13.0), (339, 161, 13.6), (356, 168, 9.6)]
CLOCK_EYES = [(320, 166, 10.0), (340, 158, 9.0), (356, 168, 6.6)]
ELDRITCH_EYES = [(322, 166, 10.0), (348, 164, 9.0)]


def eyes(o, lit: bool):
    """The eyes: glowing (``eye_lit``), or gone out (``eye_dark``, death)."""
    kind = o["kind"]
    out = []
    if kind == "hood":
        for x, y, r in HOOD_EYES:
            if lit:
                out += [glow_ring(x, y, r + 5, r + 3, o["halo"], 0.22), ellipse(x, y, r * 0.8, r * 0.76, o["eye"]),
                        ellipse(x + 1, y - 1.5, r * 0.25, r * 0.25, o["eye_hi"])]
            else:
                out.append(ellipse(x, y + 1, r * 0.5, r * 0.18, shade(o["eye"], 0.35)))
    elif kind == "clock":
        for x, y, r in CLOCK_EYES:
            if lit:
                out += [glow_ring(x, y, r + 4, r + 4, o["halo"], 0.22), ellipse(x, y, r * 0.66, r * 0.66, o["eye"]),
                        ellipse(x, y, r * 0.3, r * 0.3, "#5a3a08"), ellipse(x + r * 0.28, y - r * 0.3, r * 0.18, r * 0.18, o["eye_hi"])]
            else:
                # the lens cracked and dark
                out += [ellipse(x, y, r * 0.66, r * 0.66, "#2a2418"),
                        line([(x - r * 0.5, y - r * 0.4), (x + r * 0.1, y + r * 0.1), (x + r * 0.5, y - r * 0.2)], o["claw_sh"], 0.9)]
    else:
        if lit:
            out += [glow_ring(337, 140, 8, 13, o["core"], 0.24), path(smooth([(337, 132, True), (340, 140), (337, 148, True), (334, 140)]), o["core"]),
                    ellipse(337.6, 137, 1.0, 2.0, o["core_hi"])]
        for x, y, r in ELDRITCH_EYES:
            if lit:
                out += [glow_ring(x, y, r + 5, r + 3, o["eye"], 0.24), ellipse(x, y, r * 0.55, r * 0.55, o["eye"]),
                        ellipse(x + 1, y - 1.2, r * 0.22, r * 0.22, o["eye_hi"])]
            else:
                out.append(ellipse(x, y + 1, r * 0.45, r * 0.16, shade(o["eye"], 0.3)))
    return out


# ---------------------------------------------------------------- cloak ---

def cloak(o):
    """The cloak (or the Warden's bell of plates), its collar and its core."""
    ink, kind = o["ink"], o["kind"]
    out = []
    if kind == "clock":
        sil = smooth([(262, 214), (238, 250), (220, 320), (208, 392, True), (240, 404), (276, 410), (312, 404), (344, 396, True), (352, 330),
                      (354, 262), (346, 232)])
        det = []
        for row in range(5):
            y = 258 + row * 26
            det.append(line([(196, y + 2), (280, y + 6), (364, y)], o["cloak_sh"], 2.0))
            det.append(line([(196, y + 5), (280, y + 9), (364, y + 3)], o["cloak_lt"], 1.0))
            for i in range(7):
                x = 214 + i * 22 + (row % 2) * 11
                det.append(line([(x, y + 7), (x - 1, y + 28)], o["cloak_sh"], 1.4))
                det.append(ellipse(x + 6, y + 12, 1.6, 1.6, o["trim"], o["ink"], 0.5))
        det.append(path(smooth([(200, 384), (360, 376), (360, 420), (200, 420)]), o["trim"]))
        det.append(line([(200, 386), (360, 378)], o["trim_lt"], 1.4))
        out += cel(sil, o["cloak"], o["cloak_sh"], o["cloak_lt"], det, k=16, m=5, outline=ink, ow=2 * OW)
        col = smooth([(266, 222), (300, 232), (344, 232), (360, 242), (346, 256), (300, 256), (264, 246)])
        out += cel(col, o["trim"], o["trim_sh"], o["trim_lt"], [ellipse(280 + i * 16, 244, 1.8, 1.8, o["trim_lt"], ink, 0.6) for i in range(5)],
                   k=3, m=1.5, outline=ink, ow=1.8)
        cx, cy = 306.0, 302.0
        out += cel(disc((cx, cy), 23, 36), o["trim"], o["trim_sh"], o["trim_lt"], k=3, m=1.5, outline=ink, ow=2.0)
        out.append(glow_ring(cx, cy, 22, 22, o["halo"], 0.25))
        out.append(ellipse(cx, cy, 16, 16, o["core"], ink, 1.2))
        for k in range(12):
            a = math.tau * k / 12
            out.append(line([(cx + math.cos(a) * 12, cy + math.sin(a) * 12), (cx + math.cos(a) * 15, cy + math.sin(a) * 15)], o["mask_dk"], 1.4))
        out.append(line([(cx, cy), (cx + 1, cy - 11)], ink, 2.0))
        out.append(line([(cx, cy), (cx + 8, cy + 4)], ink, 2.0))
        out.append(ellipse(cx, cy, 2.2, 2.2, o["eye"], ink, 0.8))
        return out
    if kind == "hood":
        sil = smooth([(262, 214), (236, 252), (214, 322), (196, 392), (174, 440), (150, 488, True), (198, 452), (222, 424), (244, 438, True),
                      (258, 404), (276, 440, True), (292, 404), (312, 434, True), (324, 398), (346, 420, True), (350, 380), (358, 320),
                      (356, 262), (346, 232)])
    else:
        sil = smooth([(262, 214), (234, 254), (210, 326), (186, 396), (156, 446), (118, 498, True), (180, 466), (210, 440), (226, 470, True),
                      (246, 420), (262, 478, True), (282, 424), (300, 470, True), (316, 416), (338, 452, True), (348, 400), (358, 330),
                      (356, 262), (346, 232)])
    det = [line([(256, 250), (238, 330), (214, 420)], o["cloak_sh"], 2.0), line([(300, 262), (296, 340), (292, 400)], o["cloak_sh"], 1.8),
           line([(330, 270), (336, 340), (340, 396)], o["cloak_lt"], 1.4)]
    if kind == "eldritch":
        # stepped "gradient" bands across the hem: contour lines of a loss surface
        for i, col in enumerate(o["bands"]):
            y0 = 352 + i * 30
            det.append(path(smooth([(100, y0 + 30), (200, y0 - 6), (300, y0 + 8), (380, y0 - 10), (380, 560), (100, 560)]), col))
        for x, y in ((246, 300), (226, 352), (288, 330)):
            det += [path(smooth([(x - 8, y), (x, y - 4), (x + 8, y), (x, y + 4)]), o["hood_in"], ink, 0.9), ellipse(x, y, 2.4, 2.4, o["eye"])]
    out += cel(sil, o["cloak"], o["cloak_sh"], o["cloak_lt"], det, k=16, m=5, outline=ink, ow=2 * OW)
    col = smooth([(266, 222), (300, 234), (344, 232), (360, 242), (348, 258), (300, 258), (264, 246)])
    out += cel(col, o["trim"], o["trim_sh"], o["trim_lt"], k=3, m=1.5, outline=ink, ow=1.8)
    cx, cy = 306.0, 292.0
    out.append(glow_ring(cx, cy, 20, 18, o["core"], 0.25))
    out += cel(smooth([(cx - 12, cy), (cx, cy - 14), (cx + 12, cy), (cx, cy + 16)]), o["core"], shade(o["core"], 0.6), o["core_hi"],
               [ellipse(cx + 2, cy - 4, 3, 4, o["core_hi"])], k=4, m=2, outline=ink, ow=1.6)
    out.append(path(smooth([(cx - 17, cy - 2), (cx - 4, cy - 18), (cx + 4, cy - 18), (cx + 17, cy - 2), (cx + 4, cy - 12), (cx - 4, cy - 12)]),
                    o["trim"], ink, 1.2))
    return out


def pendulum(o):
    """The Warden's pendulum, hung from under his bell; it swings."""
    if o["kind"] != "clock":
        return []
    ink = o["ink"]
    bob = (262.0, 470.0)
    out = [path(capsule(J("pendulum"), bob, 3.4, 3.4), o["trim_sh"], ink, 1.6)]
    out += cel(disc(bob, 22, 32), o["trim"], o["trim_sh"], o["trim_lt"], [ellipse(bob[0], bob[1], 10, 10, "none", o["trim_sh"], 1.6)],
               k=5, m=2, outline=ink, ow=2.2)
    return out


# ----------------------------------------------------------------- arms ---

def _limb_colours(o, far):
    if far:
        return shade(o["limb"], 0.72), shade(o["limb_sh"], 0.72), None
    return o["limb"], o["limb_sh"], o["limb_lt"]


def _joint_disc(o, q, r, far):
    jcol = o["joint"] if o["kind"] == "hood" else (o["trim_sh"] if not far else shade(o["trim_sh"], 0.7))
    dot = o["eye"] if o["kind"] == "hood" else o["trim_lt"]
    return cel(disc(q, r), jcol, shade(jcol, 0.7), shade(jcol, 1.25) if not far else None, [ellipse(q[0], q[1], r * 0.35, r * 0.35, dot)],
               k=3, m=1.5, outline=o["ink"], ow=1.8)


def _tendril_mids(side):
    s, e, w = J(f"{side}_arm_u"), J(f"{side}_arm_l"), J(f"{side}_hand")
    m1, m2 = lerp(s, e, 0.5), lerp(e, w, 0.5)
    return (m1[0], m1[1] + 14), (m2[0], m2[1] - 12)


def upper_arm(o, side):
    far = side == "far"
    s, e = J(f"{side}_arm_u"), J(f"{side}_arm_l")
    base, sh, lt = _limb_colours(o, far)
    if o["kind"] == "eldritch":
        m1, _ = _tendril_mids(side)
        rings = [line([lerp(s, e, u), (lerp(s, e, u)[0] + 3, lerp(s, e, u)[1] + 6)], sh, 1.2) for u in (0.3, 0.6)]
        return cel(tube([s, m1, e], 16, 12), base, sh, lt, rings, k=4, m=2, outline=o["ink"], ow=2 * OW)
    r0, r1 = (13, 11) if o["kind"] == "hood" else (12, 11)
    out = group([(capsule(s, e, r0, r1), base, sh, lt, [], 4, 2)], 2 * OW)
    if o["kind"] == "clock":
        out.append(line([lerp(s, e, 0.2), lerp(s, e, 0.8)], o["claw"] if not far else o["claw_sh"], 2.2))
    return out + _joint_disc(o, s, 16, far)


def forearm(o, side):
    far = side == "far"
    e, w = J(f"{side}_arm_l"), J(f"{side}_hand")
    base, sh, lt = _limb_colours(o, far)
    if o["kind"] == "eldritch":
        # the tendril goes on from the elbow; a round end covers the join
        _, m2 = _tendril_mids(side)
        return group([(tube([e, m2, w], 12, 8), base, sh, lt, [], 4, 2), (disc(e, 12.0), base, sh, lt, [], 4, 2)], 2 * OW)
    r1 = 11
    out = group([(capsule(e, w, r1, r1 - 1), base, sh, lt, [], 4, 2)], 2 * OW)
    if o["kind"] == "clock":
        out.append(line([lerp(e, w, 0.2), lerp(e, w, 0.8)], o["claw"] if not far else o["claw_sh"], 2.2))
    return out + _joint_disc(o, e, 14, far)


def hand(o, side):
    far = side == "far"
    ink, kind = o["ink"], o["kind"]
    wr = J(f"{side}_hand")
    el = _tendril_mids(side)[1] if kind == "eldritch" else J(f"{side}_arm_l")
    ux, uy = norm(el, wr)
    p = lambda t, s: (wr[0] + ux * t - uy * s, wr[1] + uy * t + ux * s)  # noqa: E731
    cl = o["claw"] if not far else shade(o["claw"], 0.75)
    clsh = o["claw_sh"] if not far else shade(o["claw_sh"], 0.75)
    out = []
    if kind == "clock":
        # a pincer: two hooked steel jaws on a brass knuckle
        for s in (-1, 1):
            jaw = smooth([p(4, s * 5) + (True,), p(22, s * 17), p(42, s * 15), p(52, s * 2) + (True,), p(38, s * 6), p(20, s * 8)])
            out += cel(jaw, cl, clsh, o["mask_lt"] if not far else None, k=3, m=1.2, outline=ink, ow=1.6)
        out += cel(svg.poly([p(math.cos(a) * 13, math.sin(a) * 13) for a in [i * math.pi / 10 for i in range(20)]]),
                   o["limb"] if not far else shade(o["limb"], 0.75), o["limb_sh"], o["limb_lt"] if not far else None,
                   [ellipse(*p(0, 0), 3, 3, o["eye"])], k=3, m=1.2, outline=ink, ow=1.6)
        return out + _joint_disc(o, wr, 11, far)
    fingers = ((-15, 46, 34), (-1, 54, 8), (13, 44, -20)) if kind == "hood" else ((-11, 46, 24), (-4, 54, 10), (4, 52, -2), (11, 40, -16))
    for s0, ln, bend in fingers:
        a = p(6, s0)
        b = p(6 + ln * 0.55, s0 * 1.6)
        c = p(6 + ln, s0 * 1.2 + bend * 0.6)
        if kind == "hood":
            claw = smooth([(a[0] - uy * 4.6, a[1] + ux * 4.6), (b[0] - uy * 4.8, b[1] + ux * 4.8), c + (True,), (b[0] + uy * 3.6, b[1] - ux * 3.6),
                           (a[0] + uy * 4.6, a[1] - ux * 4.6)])
            out += cel(claw, cl, clsh, o["mask_lt"] if not far else None, k=2, m=1, outline=ink, ow=1.3)
        else:
            out += group([(capsule(a, b, 4.0, 3.2), cl, clsh, None, [], 1.5, 0.8), (capsule(b, c, 3.2, 1.8), cl, clsh, None, [], 1.5, 0.8)], 1.3)
    knuckle = svg.poly([p(math.cos(a) * 13 + 2, math.sin(a) * 12) for a in [i * math.pi / 10 for i in range(20)]])
    out += cel(knuckle, o["limb"] if not far else shade(o["limb"], 0.75), o["limb_sh"], o["limb_lt"] if not far else None,
               [ellipse(*p(3, 0), 3.4, 3.4, o["eye"] if kind == "hood" else o["core"])], k=3, m=1.2, outline=ink, ow=1.6)
    if kind == "hood":
        out += _joint_disc(o, wr, 11, far)
    return out


# ------------------------------------------------------------------- fx ---

def ring_fx(o):
    """``spike_halo``: the volley he throws out, a ring of bolts round him."""
    cx, cy = 300.0, 290.0
    out = [ellipse(cx, cy, 190, 190, "none", o["halo"], 3.0), glow_ring(cx, cy, 196, 196, o["halo"], 0.06)]
    for k in range(12):
        a = math.tau * k / 12 + 0.13
        b = (cx + math.cos(a) * 176, cy + math.sin(a) * 176)
        t = (cx + math.cos(a) * 212, cy + math.sin(a) * 212)
        n = (-math.sin(a) * 6, math.cos(a) * 6)
        bolt = smooth([(b[0] + n[0], b[1] + n[1], True), t + (True,), (b[0] - n[0], b[1] - n[1], True)])
        out.append(path(bolt, o["eye"], o["ink"], 1.4))
        out.append(line([lerp(b, t, 0.2), lerp(b, t, 0.75)], o["eye_hi"], 1.6))
    return out


def slam_fx(o):
    """``floor_slam``: the shock where his claws strike the floor."""
    gy = 470.0
    out = [ellipse(300, gy, 180, 18, "none", o["halo"], 3.0), glow_ring(300, gy, 196, 24, o["halo"], 0.14)]
    for x0, dx in ((140, -1), (460, 1)):
        for k in range(3):
            x = x0 + dx * k * 22
            spike = smooth([(x - 8, gy, True), (x + dx * 6, gy - 34 + k * 8, True), (x + 8, gy, True)])
            out.append(path(spike, o["eye"], o["ink"], 1.4))
    return out


def dash_fx(o):
    """``dash_echo``: the echo he leaves behind as he dashes, streaks trailing back."""
    out = []
    for k, (y, ln) in enumerate(((160, 150), (220, 190), (280, 210), (340, 180), (400, 140))):
        x1 = 236 - k % 2 * 10
        out.append(path(smooth([(x1, y - 7, True), (x1 - ln, y, True), (x1, y + 7, True)]), o["halo"]))
        out.append(line([(x1 - 10, y), (x1 - ln * 0.7, y)], o["eye_hi"], 1.4))
    return out


#: The parts, in the order they are drawn: (group id, label, part, bone, z, opacity channel).
LAYERS = [
    ("fx-dash", "FX - Dash Echo", "fx_dash", "body", 1, "fx_dash"),
    ("halo", "Halo", "halo", "halo", 2, ""),
    ("far-arm-upper", "Far Arm - Upper", "far_arm_u", "far_arm_u", 10, ""),
    ("far-arm-lower", "Far Arm - Lower", "far_arm_l", "far_arm_l", 11, ""),
    ("far-hand", "Far Hand", "far_hand", "far_hand", 12, ""),
    ("pendulum", "Pendulum", "pendulum", "pendulum", 15, ""),
    ("cloak", "Cloak", "cloak", "body", 20, ""),
    ("head", "Head", "head", "head", 40, ""),
    ("eye-lit", "Eyes - Lit", "eye_lit", "head", 41, "eye_lit"),
    ("eye-dark", "Eyes - Dark", "eye_dark", "head", 41, "eye_dark"),
    ("near-arm-upper", "Near Arm - Upper", "near_arm_u", "near_arm_u", 60, ""),
    ("near-arm-lower", "Near Arm - Lower", "near_arm_l", "near_arm_l", 61, ""),
    ("near-hand", "Near Hand", "near_hand", "near_hand", 62, ""),
    ("fx-ring", "FX - Ring Volley", "fx_ring", "body", 70, "fx_ring"),
    ("fx-slam", "FX - Floor Slam", "fx_slam", "floor", 70, "fx_slam"),
]


def drawn(o) -> Dict[str, list]:
    out = {"fx-dash": dash_fx(o), "halo": halo(o), "pendulum": pendulum(o), "cloak": cloak(o), "head": head(o),
           "eye-lit": eyes(o, True), "eye-dark": eyes(o, False), "fx-ring": ring_fx(o), "fx-slam": slam_fx(o)}
    for side in ("far", "near"):
        out[f"{side}-arm-upper"] = upper_arm(o, side)
        out[f"{side}-arm-lower"] = forearm(o, side)
        out[f"{side}-hand"] = hand(o, side)
    return out


def svg_text(look: str) -> str:
    o = LOOKS[look]
    svg.configure(dx=0, dy=0, ink=o["ink"], ow=OW, colors={})
    parts = drawn(o)
    svg.PARTS.clear()
    for group_id, label, name, bone, z, channel in LAYERS:
        extra = (f' data-rig-opacity="{channel}"' + (' data-rig-default="1"' if channel == "eye_lit" else "")) if channel else ""
        part(group_id, label, name, bone, z, parts[group_id], extra)
    return svg.document(
        size=(W, H), design=TARGETS[look].replace("_", "-"), layer_id=TARGETS[look].replace("_", "-"), label=view(look),
        comment=[f"  <!-- The {o['name']} (Jon kept all three sentinel redraws, 2026-10-18): side view facing right, floating.",
                 "       Drawn by scripts/svg_art/sentinel_boss_art.py; each part turns about its JOINTS entry. -->"],
        joints=svg.joints_layer({k: (v[1], v[2]) for k, v in JOINTS.items()}),
    )


def view(look: str) -> str:
    return f"{LOOKS[look]['name']} - Side Right"


def svg_path(look: str) -> Path:
    target = TARGETS[look]
    return DATA / target / f"{target}.svg"


def main() -> None:
    if len(sys.argv) > 2 and sys.argv[1] == "--all":
        out = Path(sys.argv[2])
        out.mkdir(parents=True, exist_ok=True)
        for look in LOOKS:
            (out / f"{TARGETS[look]}.svg").write_text(svg_text(look), encoding="utf8")
            print(out / f"{TARGETS[look]}.svg")
        return
    for look in LOOKS:
        dest = svg_path(look)
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(".svg.tmp")
        tmp.write_text(svg_text(look), encoding="utf8")
        tmp.replace(dest)
        print(f"wrote {dest.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
