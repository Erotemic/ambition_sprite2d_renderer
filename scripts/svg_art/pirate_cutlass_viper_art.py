#!/usr/bin/env python3
"""How the Pirate Cutlass Viper's SVG was first drawn (reference, not authority).

    uv run python scripts/svg_art/pirate_cutlass_viper_art.py            # her look (A)
    uv run python scripts/svg_art/pirate_cutlass_viper_art.py --all DIR  # every look, to DIR

Writes ``data/characters/pirate_cutlass_viper/pirate_cutlass_viper.svg``; the
SVG owns the art after this has run once. ``JOINTS`` says where each part
turns and ``LAYERS`` lists the parts; ``scripts/build_pirate_cutlass_viper_rig.py``
reads both and authors the rows.

The Viper is the crew's lean STRIKER: a woman duelist ("One clean cut. A
second cut means the first one missed."). Jon, 2026-10-18, of three redraws:
"A for viper, keep the rest". A (``faithful``) is today's Viper redrawn: a
tricorn over a red bandana, a long dark ponytail, a blouse under a laced plum
bodice, a gold sash, plum coat tails, blue breeches, tall boots and a curved
cutlass with a brass D-guard. B (``viper``: a jade coat with scale trim, a
plumed tricorn, a braid and a snake-hilted cutlass) and C (``striped``:
hatless, long bandana tails, a red bolero and striped breeches) are KEPT, NOT
CAST. All three share her skeleton and parts, so ``--all`` draws each one
rig-ready (B and C a touch narrower or broader, as their candidates were).

Drawing: cel-shaded with a thin ink; each shape is filled, shaded inside its
own outline, and inked on top.
"""
from __future__ import annotations

import math
import re
import sys
from pathlib import Path
from typing import Dict, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import svgkit as svg  # noqa: E402
from svgkit import capsule, ellipse, line, path, poly, smooth  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "ambition_sprite2d_renderer" / "data" / "characters" / "pirate_cutlass_viper" / "pirate_cutlass_viper.svg"
VIEW = "Pirate Cutlass Viper - Side Right"
LOOK = "faithful"
W, H = 560, 560
#: The ground under her boots, in SVG units.
GROUND_Y = 500.0

# ---------------------------------------------------------------- cel kit

INK = "#1a1517"
OW = 1.5
_N = [0]
_NUM = re.compile(r"(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)")


def begin(ink: str, ow: float = 1.5) -> None:
    global INK, OW
    INK, OW = ink, ow
    svg.configure(dx=0, dy=0, ink=ink, ow=ow, colors={})


def shifted(d, dx, dy):
    return _NUM.sub(lambda m: f"{float(m.group(1)) + dx:.2f},{float(m.group(2)) + dy:.2f}", d)


def cel(sil, base, shade=None, light=None, items=(), s=(5.0, -4.0), l=(2.6, -2.2), width=None, outline=True):
    """A cel-shaded shape: the base fill, a shade band down-back and a light
    band up-front (both clipped inside), ``items`` clipped too, then the ink."""
    _N[0] += 1
    cid = f"v{_N[0]}"
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


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def rot(p, deg):
    a = math.radians(deg)
    return (p[0] * math.cos(a) - p[1] * math.sin(a), p[0] * math.sin(a) + p[1] * math.cos(a))


def xf(origin, deg, pts):
    """Local points (x along the bone, y to its right) turned by deg and put at origin."""
    out = []
    for q in pts:
        r = rot((q[0], q[1]), deg)
        out.append((origin[0] + r[0], origin[1] + r[1]) + tuple(q[2:]))
    return out


def limb(a, b, r0, r1, base, shade, light=None, items=()):
    k = min(r0, r1)
    return cel(capsule(a, b, r0, r1), base, shade, light, items, s=(k * 0.55, -k * 0.45), l=(k * 0.28, -k * 0.24))


def hand_open(wr, deg, base, shade, light=None, k=1.0):
    """A relaxed hand from the wrist along ``deg``: fingers together, slightly
    curled, the thumb on the forward side."""
    pts = [(x * k, y * k) for x, y in [(0, -6.5), (10, -7.5), (19, -7), (27, -5.5), (31, -2), (31, 2.5), (27, 5.5), (18, 7), (8, 7), (0, 6)]]
    items = [line(xf(wr, deg, [(16 * k, -2.2 * k), (29 * k, -1.6 * k)]), shade, 1.1),
             line(xf(wr, deg, [(15 * k, 2.0 * k), (27 * k, 2.4 * k)]), shade, 1.1)]
    out = cel(smooth(xf(wr, deg, pts)), base, shade, light, items, s=(2.2, -1.8), l=(1.2, -1.0))
    th = [(4 * k, -5 * k), (10 * k, -9 * k), (17 * k, -10.5 * k), (21 * k, -9 * k), (17 * k, -6.5 * k), (9 * k, -3 * k)]
    return out + cel(smooth(xf(wr, deg, th)), base, shade, None, s=(1.4, -1.2), width=1.6 * OW)


def hand_grip(c, pole_deg, base, shade, light=None, k=1.0):
    """A fist closed round a grip through ``c`` along ``pole_deg``, the
    knuckles forward, the thumb wrapped over."""
    a = pole_deg
    pts = [(x * k, y * k) for x, y in [(-9, -8), (-10, 2), (-8, 9), (0, 11), (9, 9), (10, 0), (8, -8), (0, -9)]]
    items = [line(xf(c, a, [(-5 * k, 6 * k), (-5 * k, 10 * k)]), shade, 1.0), line(xf(c, a, [(0, 6.5 * k), (0, 11 * k)]), shade, 1.0),
             line(xf(c, a, [(5 * k, 6 * k), (5 * k, 10 * k)]), shade, 1.0)]
    out = cel(smooth(xf(c, a, pts)), base, shade, light, items, s=(2.0, -1.6), l=(1.1, -0.9))
    th = [(x * k, y * k) for x, y in [(-9, -3), (-4, 4), (2, 6), (4, 3), (-2, -2), (-8, -7)]]
    return out + cel(smooth(xf(c, a, th)), base, shade, None, s=(1.0, -0.8), width=1.6 * OW)


def boot(ankle, base, shade, light, sole, top=26, toe=36, k=1.0):
    ax, ay = ankle
    g = GROUND_Y
    pts = [(ax - 12 * k, ay - top * k), (ax + 9 * k, ay - top * k - 1), (ax + 11 * k, ay - 6 * k), (ax + (toe - 12) * k, g - 13 * k),
           (ax + toe * k, g - 6 * k), (ax + (toe - 2) * k, g, True), (ax - 14 * k, g, True), (ax - 15 * k, g - 10 * k)]
    items = [path(poly([(ax - 30, g - 4 * k), (ax + toe * k + 10, g - 4 * k), (ax + toe * k + 10, g + 4), (ax - 30, g + 4)]), sole),
             path(poly([(ax - 16 * k, g - 7 * k), (ax - 2 * k, g - 7 * k), (ax - 2 * k, g + 2), (ax - 16 * k, g + 2)]), sole)]
    return cel(smooth(pts), base, shade, light, items, s=(4.0, -3.0), l=(2.0, -1.6))


# ---- the profile head (local units: origin at the ear, facing +x) ----------------
SKULL_F = [(-18, 20), (-29, 5), (-31, -13), (-24, -30), (-7, -39), (10, -38), (21, -30), (25.5, -18), (26.4, -10, True),
           (25.2, -5.5), (27.5, 0), (32, 8, True), (28.2, 10.6), (28.6, 14), (30.2, 17), (28, 19.6, True), (30, 22.4),
           (27.5, 26), (28.4, 30), (24, 34.5), (13, 35), (2, 29), (-7, 21)]


def hd(c, k, pts):
    return [(c[0] + q[0] * k, c[1] + q[1] * k) + tuple(q[2:]) for q in pts]


#: Where her eye sits on the head, in local head units.
EX, EY = 17.5, -6.0


def features(c, k, skin, shade, brow, lips):
    """The brow, the nostril, the mouth and the ear, drawn over the skull
    (the eye is its own layer)."""
    out = []
    by = EY - 6.5 - 0.6
    bpts = [(EX - 6, by + 2.2), (EX - 1, by - 1.0), (EX + 4.5, by - 0.6), (EX + 6.5, by + 1.4, True), (EX + 2, by + 0.8), (EX - 3, by + 2.2)]
    out.append(path(smooth(hd(c, k, bpts)), brow, INK, 0.7))
    nx, ny = 28.5, 8.5
    out.append(path(smooth(hd(c, k, [(nx - 4, ny - 1), (nx - 1, ny - 1.6), (nx + 0.5, ny + 1), (nx - 3, ny + 1.4)])), shade))
    out.append(line(hd(c, k, [(nx - 6, ny - 3), (nx - 5, ny + 1), (nx - 2.5, ny + 2.2)]), shade, 1.1))
    my, mx = 19.6, 27.8
    out.append(path(smooth(hd(c, k, [(mx - 4.5, my), (mx - 0.5, my - 2.6), (mx + 1.8, my - 2.4), (mx + 1.2, my, True),
                                    (mx + 2.2, my + 2.6), (mx - 1, my + 3.4), (mx - 4.5, my + 0.6)])), lips))
    out.append(line(hd(c, k, [(mx - 6.5, my + 0.6), (mx - 3, my + 0.1), (mx + 1.2, my)]), INK, 1.3))
    es = smooth(hd(c, k, [(-3, -9), (3, -9.5), (5.5, -3), (4.5, 5), (0, 10), (-4, 7), (-5.5, -1)]))
    out += cel(es, skin, shade, None, [line(hd(c, k, [(0, -5), (2.5, -1), (0.5, 5)]), shade, 1.4)], s=(2, -1.5), width=1.4 * OW)
    return out


def eye(c, k, shade, kind):
    """Her eye: open (white, iris, a heavy upper lid, lashes) or shut (the lid
    closed, the lashes down). The rig shows one at a time."""
    if kind == "open":
        white = smooth(hd(c, k, [(EX - 4.5, EY + 0.5), (EX - 1, EY - 2.6), (EX + 3.5, EY - 2.4), (EX + 5.6, EY + 0.2, True),
                                (EX + 2, EY + 2.2), (EX - 2.5, EY + 1.8)]))
        out = [path(white, "#f4ece2"), ellipse(c[0] + (EX + 2.4) * k, c[1] + (EY - 0.1) * k, 1.9 * k, 2.2 * k, "#2e2219"),
               ellipse(c[0] + (EX + 2.9) * k, c[1] + (EY - 0.9) * k, 0.55 * k, 0.55 * k, "#ffffff"),
               path(smooth(hd(c, k, [(EX - 5.5, EY + 0.4), (EX - 1, EY - 3.2), (EX + 4, EY - 3.0), (EX + 6.4, EY + 0.4, True),
                                    (EX + 3.5, EY - 1.6), (EX - 1, EY - 1.9)])), INK),
               line(hd(c, k, [(EX - 2.5, EY + 2.1), (EX + 3, EY + 2.3)]), shade, 0.9)]
        for dx, dy in ((4.4, -2.0), (5.6, -1.0)):
            out.append(line(hd(c, k, [(EX + dx, EY + dy), (EX + dx + 2.6, EY + dy - 1.8)]), INK, 1.2))
        return out
    out = [line(hd(c, k, [(EX - 5, EY - 0.4), (EX - 0.5, EY + 1.8), (EX + 4, EY + 1.6), (EX + 6.2, EY + 0.2)]), INK, 1.6)]
    for dx, dy in ((3.6, 1.6), (5.4, 0.8)):
        out.append(line(hd(c, k, [(EX + dx, EY + dy), (EX + dx + 2.2, EY + dy + 1.8)]), INK, 1.1))
    return out


# ------------------------------------------------------------- the looks

LOOKS = {
    "faithful": dict(
        label="A: today's Viper, redrawn (tricorn, plum, blue)",
        ink="#1c1416", skin="#c0845c", skin_sh="#94603f", skin_lt="#dba27a", lips="#9c4b45",
        hair="#3a1f17", hair_lt="#5e3a2a", hat="#3b2620", hat_sh="#24160f", hat_lt="#5a3b30",
        band="#b0243e", band_sh="#7c1629", band_lt="#d8506a",
        blouse="#efe3cb", blouse_sh="#c9b796", bodice="#6e2c3e", bodice_sh="#4a1b28", bodice_lt="#8f4458",
        sash="#e0b445", sash_sh="#a98226", coat="#6e2c3e", coat_sh="#4a1b28", coat_lt="#8f4458",
        legs="#2e5378", legs_sh="#1f3a56", legs_lt="#4a75a0", boot="#4a3024", boot_sh="#2f1d15", boot_lt="#6e4a37",
        sole="#1a1210", steel="#d4dae0", steel_sh="#8c96a0", steel_lt="#f4f7fa", brass="#d9a441", brass_sh="#9c7020",
        hat_kind="tricorn", hair_kind="ponytail", tails=True, w=1.0, earring="hoop", hilt="d_guard"),
    "viper": dict(
        label="B: the viper - jade coat, scale trim, snake hilt",
        ink="#14171a", skin="#8d5a3b", skin_sh="#663e27", skin_lt="#a87252", lips="#6a3330",
        hair="#17110f", hair_lt="#3a2c26", hat="#1d1c1f", hat_sh="#0e0d10", hat_lt="#3a383e",
        band="#2f7a5a", band_sh="#1d5540", band_lt="#4fa07c",
        blouse="#e8e2cf", blouse_sh="#bdb59c", bodice="#2a2328", bodice_sh="#18141a", bodice_lt="#463c44",
        sash="#c9a23e", sash_sh="#8e6f22", coat="#2c6b52", coat_sh="#1b4a38", coat_lt="#458a6d",
        legs="#3a3036", legs_sh="#251e23", legs_lt="#574a52", boot="#221c1e", boot_sh="#121011", boot_lt="#3e3438",
        sole="#0e0b0c", steel="#d8dde2", steel_sh="#8a949e", steel_lt="#f6f8fa", brass="#c9a23e", brass_sh="#8e6f22",
        hat_kind="tricorn_feather", hair_kind="braid", tails=True, w=0.94, build=(0.95, 1.04), longcoat=True, earring="fang",
        hilt="snake", scales=True),
    "striped": dict(
        label="C: hatless - long bandana tails, red bolero, striped breeches",
        ink="#1d1513", skin="#d6a07a", skin_sh="#a8704f", skin_lt="#ecbf9a", lips="#a8524c",
        hair="#7a3a1e", hair_lt="#a65a32", hat=None, hat_sh=None, hat_lt=None,
        band="#c23b2e", band_sh="#8a2419", band_lt="#e06a58",
        blouse="#f1e7d2", blouse_sh="#c8b99a", bodice="#5a3a26", bodice_sh="#3c2618", bodice_lt="#7a5236",
        sash="#2b3d5c", sash_sh="#1a2740", coat="#7c2a2e", coat_sh="#561a1e", coat_lt="#9e4246",
        legs="#ece0c6", legs_sh="#c2b393", legs_lt="#fff7e6", stripe="#2b3d5c",
        boot="#8a5a34", boot_sh="#5e3b20", boot_lt="#b07a4a",
        sole="#24170f", steel="#d4dae0", steel_sh="#8c96a0", steel_lt="#f4f7fa", brass="#d9a441", brass_sh="#9c7020",
        hat_kind=None, hair_kind="braid_long", tails=False, w=1.08, build=(1.05, 0.98), earring="hoop", hilt="basket", jacket=True),
}

#: Where each bone turns (SVG units): ``bone: (parent, x, y)``, parents first.
#: The drawn pose is her ready stance: the sword hand forward, the other on her hip.
JOINTS: Dict[str, Tuple[str, float, float]] = {
    "body": ("", 268.0, 318.0),
    "torso": ("body", 268.0, 318.0),
    "head": ("torso", 280.0, 194.0),
    "coat": ("body", 252.0, 290.0),
    "far_arm_u": ("torso", 262.0, 210.0),
    "far_arm_l": ("far_arm_u", 228.0, 258.0),
    "far_hand": ("far_arm_l", 250.0, 290.0),
    "near_arm_u": ("torso", 284.0, 214.0),
    "near_arm_l": ("near_arm_u", 304.0, 264.0),
    "near_hand": ("near_arm_l", 336.0, 286.0),
    "far_leg_u": ("body", 258.0, 316.0),
    "far_leg_l": ("far_leg_u", 248.0, 404.0),
    "far_foot": ("far_leg_l", 226.0, 474.0),
    "near_leg_u": ("body", 278.0, 318.0),
    "near_leg_l": ("near_leg_u", 302.0, 402.0),
    "near_foot": ("near_leg_l", 318.0, 474.0),
}
#: Her cranium (the ear) and the head's drawing scale.
HEAD_C, HEAD_K = (287.0, 158.0), 1.06
#: The cutlass, from the grip: its turn from +x, and the grip in the hand.
BLADE_DEG = -38.0


def P(name):
    return JOINTS[name][1], JOINTS[name][2]


def widen(pts, w, cx=270.0):
    return [(cx + (q[0] - cx) * w,) + tuple(q[1:]) for q in pts]


def far_arm(o):
    sh, el, wr = P("far_arm_u"), P("far_arm_l"), P("far_hand")
    upper = cel(smooth([(sh[0] - 14, sh[1] - 4), (sh[0] + 8, sh[1] - 8), (sh[0] + 10, sh[1] + 16), (el[0] + 10, el[1] - 8),
                        (el[0] + 2, el[1] + 4), (el[0] - 9, el[1] - 2), (sh[0] - 16, sh[1] + 14)]), o["blouse_sh"], o["blouse_sh"])
    lower = limb(el, wr, 6.8, 5.4, o["skin_sh"], o["skin_sh"])
    # the hand set on the hip, fingers forward
    hand = hand_open(wr, 8.0, o["skin_sh"], o["skin_sh"], k=0.9)
    return upper, lower, hand


def leg(o, side):
    near = side == "near"
    hip, kn, an = P(f"{side}_leg_u"), P(f"{side}_leg_l"), P(f"{side}_foot")
    base, sh, lt = (o["legs"], o["legs_sh"], o["legs_lt"]) if near else (o["legs_sh"], o["legs_sh"], None)
    items = []
    if o.get("stripe"):
        for off in (-8, 0, 8):
            items.append(line([(hip[0] + off, hip[1] - 10), (kn[0] + off * 0.8, kn[1] + 4)], o["stripe"] if near else o["sash_sh"], 3.0))
    thigh = cel(capsule(hip, kn, 14.0, 11.0), base, sh, lt, items, s=(6, -4))
    bb = (o["boot"], o["boot_sh"], o["boot_lt"]) if near else (o["boot_sh"], o["boot_sh"], None)
    # the shin inside a tall boot shaft to above the knee, a turned-down cuff
    shin = limb(kn, an, 11.0, 8.0, base, sh, lt)
    shaft = smooth([(kn[0] - 12, kn[1] - 8), (kn[0] + 12, kn[1] - 11), (kn[0] + 10, kn[1] + 12), (an[0] + 10, an[1] - 4),
                    (an[0] - 10, an[1] - 2), (kn[0] - 10, kn[1] + 12)])
    shin += cel(shaft, bb[0], bb[1], bb[2], s=(5, -3))
    cuff = smooth([(kn[0] - 15, kn[1] - 14, True), (kn[0] + 15, kn[1] - 18, True), (kn[0] + 14, kn[1] - 4, True), (kn[0] - 14, kn[1] + 1, True)])
    shin += cel(cuff, bb[2] or bb[0], bb[1], None, s=(4, -3))
    foot = boot(an, bb[0], bb[1], bb[2], o["sole"], top=10, toe=30)
    return thigh, shin, foot


def coat_tails(o):
    w = o["w"]
    sil = smooth(widen([(250, 284), (290, 286), (296, 302), (290, 340), (282, 392), (262, 420, True), (252, 394), (240, 410),
                        (222, 424, True), (222, 380), (232, 322)], w))
    items = [line(widen([(258, 296), (250, 396)], w), o["coat_sh"], 2.0)]
    if o.get("scales"):
        for i in range(7):
            x = 232 + i * 6
            items.append(path(smooth(widen([(x - 3, 396 + i * 0.6), (x, 401 + i * 0.6, True), (x + 3, 396 + i * 0.6)], w)), o["sash"]))
    return cel(sil, o["coat"], o["coat_sh"], o["coat_lt"], items, s=(10, -4))


def torso(o):
    w = o["w"]
    out = cel(capsule((279, 186), (279, 212), 8.0, 9.5), o["skin"], o["skin_sh"], None, s=(5, -2))  # the neck
    # the blouse: back and chest, the waist drawn in
    sil = smooth(widen([(262, 202), (284, 200), (296, 212), (302, 230), (301, 246), (294, 258), (290, 278), (294, 306),
                        (286, 324), (254, 324), (250, 300), (252, 276), (249, 246), (252, 218)], w))
    out += cel(sil, o["blouse"], o["blouse_sh"], None, [line(widen([(282, 204), (292, 222)], w), o["blouse_sh"], 1.6)], s=(8, -4))
    # the bodice: laced, from under the bust to the hip
    bod = smooth(widen([(250, 240, True), (276, 238), (300, 244, True), (295, 258), (290, 278), (295, 306), (288, 326),
                        (254, 326), (250, 300), (252, 272)], w))
    items = []
    for i in range(5):
        y = 248 + i * 15
        dx = 2 if i in (1, 2) else 0
        items.append(line(widen([(292 - dx, y), (299 - dx, y + 7)], w), o["sash"], 1.4))
        items.append(line(widen([(299 - dx, y), (292 - dx, y + 7)], w), o["sash"], 1.4))
    items.append(line(widen([(262, 240), (258, 320)], w), o["bodice_sh"], 1.6))
    out += cel(bod, o["bodice"], o["bodice_sh"], o["bodice_lt"], items, s=(9, -3))
    if o.get("longcoat"):
        lc = smooth(widen([(250, 206), (270, 198), (288, 204), (290, 220), (280, 250), (274, 290), (276, 330), (268, 336),
                           (250, 330), (244, 290), (246, 244), (246, 220)], w))
        litems = [line(widen([(284, 208), (274, 250), (270, 330)], w), o["coat_lt"], 2.4)]
        if o.get("scales"):
            for i in range(14):
                y = 212 + i * 8.5
                x = 283 - (y - 208) * 0.25 + max(0, y - 250) * 0.17
                litems.append(path(smooth(widen([(x - 7, y - 2), (x - 3.5, y + 3.5), (x, y - 2), (x - 3.5, y + 0.5)], w)), o["sash"]))
        out += cel(lc, o["coat"], o["coat_sh"], o["coat_lt"], litems, s=(8, -3))
    if o.get("jacket"):
        jk = smooth(widen([(250, 206), (270, 198), (290, 204), (292, 220), (284, 248), (276, 262, True), (254, 266, True),
                           (246, 244), (246, 222)], w))
        jitems = [line(widen([(256, 262), (276, 260)], w), o["sash"], 2.4), line(widen([(286, 210), (278, 254)], w), o["bodice_lt"], 2.0)]
        out += cel(jk, o["coat"], o["coat_sh"], o["coat_lt"], jitems, s=(8, -3))
    # the sash: wound round the waist, a knot and two ends at the back hip
    sash = smooth(widen([(248, 290, True), (296, 284, True), (298, 300, True), (248, 306, True)], w))
    out += cel(sash, o["sash"], o["sash_sh"], None, [line(widen([(252, 297), (296, 292)], w), o["sash_sh"], 1.2)], s=(3, -3))
    ends = smooth(widen([(252, 296), (238, 306), (232, 336, True), (242, 330), (246, 342, True), (252, 318), (258, 304)], w))
    out += cel(ends, o["sash"], o["sash_sh"], None, s=(4, -2))
    # a baldric strap
    out.append(line(widen([(298, 226), (278, 262), (256, 296)], w), INK, 5.0))
    out.append(line(widen([(298, 226), (278, 262), (256, 296)], w), o["boot"], 3.0))
    return out


def head(o):
    c, k = HEAD_C, HEAD_K
    out = []
    hair, hl = o["hair"], o["hair_lt"]
    # the hair behind the head: a ponytail or a braid
    if o["hair_kind"] == "ponytail":
        tail = smooth([(c[0] - 26, c[1] - 14), (c[0] - 38, c[1] + 4), (c[0] - 44, c[1] + 40), (c[0] - 40, c[1] + 82),
                       (c[0] - 30, c[1] + 104, True), (c[0] - 30, c[1] + 70), (c[0] - 22, c[1] + 34), (c[0] - 14, c[1] + 10)])
        out += cel(tail, hair, None, hl, [line([(c[0] - 34, c[1] + 10), (c[0] - 36, c[1] + 70)], hl, 1.6)], s=(4, -2), l=(3, 0))
    else:
        n = 7 if o["hair_kind"] == "braid" else 9
        for i in range(n):
            y = c[1] + 2 + i * 12
            x = c[0] - 30 - math.sin(i * 0.5) * 4
            seg = smooth([(x - 7, y), (x + 1, y - 7), (x + 8, y + 2), (x + 2, y + 11), (x - 6, y + 9)])
            out += cel(seg, hair, None, hl, s=(0, 0), l=(1.5, 1.5), width=2.2)
        y = c[1] + 2 + n * 12
        x = c[0] - 30 - math.sin(n * 0.5) * 4
        out += cel(smooth([(x - 4, y - 4, True), (x + 4, y - 4, True), (x + 3, y + 1, True), (x - 3, y + 1, True)]), o["band"], o["band_sh"], None, s=(2, -1))
        out += cel(smooth([(x - 4, y), (x + 4, y), (x + 6, y + 14, True), (x + 1, y + 8), (x - 5, y + 16, True)]), hair, None, hl, s=(0, 0), l=(1, 1))
    face_items = [path(smooth(hd(c, k, [(-34, 4), (-10, 14), (6, 26), (20, 34), (26, 44), (-30, 44)])), o["skin_sh"]),
                  path(smooth(hd(c, k, [(4, -30), (20, -28), (25, -14), (14, -20)])), o["skin_lt"])]
    out += cel(smooth(hd(c, k, SKULL_F)), o["skin"], o["skin_sh"], o["skin_lt"], face_items, s=(6, -4), l=(2.6, -2))
    out += features(c, k, o["skin"], o["skin_sh"], hair, o["lips"])
    # hair over the crown and a lock before the ear
    cap = smooth([(c[0] - 33, c[1] + 8), (c[0] - 34, c[1] - 16), (c[0] - 22, c[1] - 34), (c[0] - 2, c[1] - 40), (c[0] + 16, c[1] - 36),
                  (c[0] + 26, c[1] - 22), (c[0] + 22, c[1] - 18), (c[0] + 8, c[1] - 22), (c[0] - 6, c[1] - 16), (c[0] - 12, c[1] - 6),
                  (c[0] - 16, c[1] + 6), (c[0] - 22, c[1] + 18)])
    out += cel(cap, hair, None, hl, [line([(c[0] - 26, c[1] - 22), (c[0] - 8, c[1] - 34)], hl, 1.6)], s=(0, 0), l=(2, 2))
    # the bandana: a band round the brow, knotted at the back
    band = smooth([(c[0] - 34, c[1] - 20), (c[0] - 14, c[1] - 34), (c[0] + 10, c[1] - 38), (c[0] + 26, c[1] - 28),
                   (c[0] + 27, c[1] - 19, True), (c[0] + 8, c[1] - 24), (c[0] - 14, c[1] - 20), (c[0] - 30, c[1] - 8)])
    out += cel(band, o["band"], o["band_sh"], o["band_lt"], [line([(c[0] - 18, c[1] - 26), (c[0] + 16, c[1] - 30)], o["band_sh"], 1.2)],
               s=(3, 3), l=(1.5, -2))
    knot = (c[0] - 34, c[1] - 14)
    tail_len = 24 if o.get("hat_kind") else 54
    t1 = smooth([knot, (knot[0] - 10, knot[1] + 4), (knot[0] - 18, knot[1] + tail_len * 0.6), (knot[0] - 14, knot[1] + tail_len, True),
                 (knot[0] - 6, knot[1] + tail_len * 0.5), (knot[0] + 2, knot[1] + 6)])
    t2 = smooth([knot, (knot[0] - 14, knot[1] - 4), (knot[0] - 30, knot[1] + tail_len * 0.35), (knot[0] - 30, knot[1] + tail_len * 0.8, True),
                 (knot[0] - 20, knot[1] + tail_len * 0.3), (knot[0] - 2, knot[1] + 4)])
    out = cel(t2, o["band_sh"], None, None) + out  # behind everything of the head
    out += cel(t1, o["band"], o["band_sh"], None, s=(3, -1))
    out += cel(smooth([(knot[0] - 6, knot[1] - 6), (knot[0] + 5, knot[1] - 6), (knot[0] + 6, knot[1] + 5), (knot[0] - 5, knot[1] + 5)]),
               o["band"], o["band_sh"], o["band_lt"], s=(2, -2))
    ex, ey = c[0] + 1, c[1] + 10
    if o["earring"] == "hoop":
        out += [ellipse(ex, ey + 4, 3.6, 4.4, "none", INK, 2.8), ellipse(ex, ey + 4, 3.6, 4.4, "none", o["brass"], 1.4)]
    else:
        out += cel(smooth([(ex - 2, ey), (ex + 2, ey), (ex + 1, ey + 9, True)]), "#eee6d6", "#b8ad98", None, s=(1, -1), width=1.4)
    hat = o.get("hat_kind")
    if hat:
        hx, hy = c[0] + 2, c[1] - 42
        crown = smooth([(hx - 26, hy + 8), (hx - 22, hy - 12), (hx - 6, hy - 22), (hx + 12, hy - 21), (hx + 23, hy - 10), (hx + 25, hy + 8)])
        # the tricorn in profile: the back flap cocked up high, the front corner forward
        brim = smooth([(hx - 40, hy - 26, True), (hx - 30, hy - 2), (hx - 8, hy + 6), (hx + 18, hy + 4), (hx + 44, hy - 10, True),
                       (hx + 36, hy + 6), (hx + 20, hy + 14), (hx - 8, hy + 16), (hx - 34, hy + 10), (hx - 46, hy - 8)])
        if hat == "tricorn_feather":
            fe = smooth([(hx - 14, hy - 18), (hx - 36, hy - 40), (hx - 66, hy - 46), (hx - 82, hy - 36, True), (hx - 60, hy - 34),
                         (hx - 34, hy - 24), (hx - 16, hy - 12)])
            out += cel(fe, o["band"], o["band_sh"], o["band_lt"], [line([(hx - 16, hy - 15), (hx - 80, hy - 37)], o["band_sh"], 1.0)], s=(2, 3))
        out += cel(crown, o["hat"], o["hat_sh"], o["hat_lt"], s=(7, -2), l=(2.5, -2))
        if hat == "tricorn_feather":
            out += cel(smooth([(hx - 27, hy - 2, True), (hx + 25, hy - 2, True), (hx + 26, hy + 5, True), (hx - 28, hy + 5, True)]),
                       o["band"], o["band_sh"], None)
            out += cel(smooth([(hx - 4, hy - 4), (hx + 8, hy - 5), (hx + 12, hy + 1, True), (hx + 6, hy + 6), (hx - 4, hy + 6)]),
                       o["brass"], o["brass_sh"], None, [ellipse(hx + 6, hy - 1, 1.1, 1.1, INK)], s=(2, -1))
        else:
            out.append(line([(hx - 27, hy), (hx + 25, hy)], o["band"], 3.0))
        out += cel(brim, o["hat"], o["hat_sh"], o["hat_lt"], [line([(hx - 30, hy + 9), (hx + 24, hy + 9)], o["hat_sh"], 1.4)],
                   s=(3, -3), l=(1.5, -1.5))
    return out


def _bend(pts):
    """The cutlass's curve: the blade sweeps back toward its point."""
    return [(x, y - 16.0 * (max(x - 16, 0) / 120.0) ** 2) + tuple(r) for x, y, *r in pts]


def cutlass(o, grip):
    """The cutlass from the grip along ``BLADE_DEG``: the blade widens toward
    a clipped point, the guard curls round the knuckles."""
    a = BLADE_DEG
    blade = smooth(xf(grip, a, _bend([(18, -2.5), (60, -5.0), (100, -7.0), (126, -8, True), (136, -1, True), (122, 7), (80, 7.5),
                                      (40, 5.5), (18, 4)])))
    items = [path(smooth(xf(grip, a, _bend([(18, 1.0), (80, 1.0), (124, -1), (134, -2), (122, 7), (80, 7.5), (40, 5.5), (18, 4)]))),
                  o["steel_sh"]),
             line(xf(grip, a, _bend([(22, -1), (90, -3.5), (122, -5)])), o["steel_lt"], 1.6)]
    out = cel(smooth(xf(grip, a, [(-14, -3.4, True), (14, -3.4, True), (14, 3.4, True), (-14, 3.4, True)])), "#3a2418", "#24160f", None)
    out += cel(blade, o["steel"], None, None, items)
    hilt = o["hilt"]
    if hilt == "basket":
        g = smooth(xf(grip, a, [(14, -9), (18, -10, True), (18, 16, True), (0, 22), (-14, 18), (-16, 10), (-6, 14), (8, 14)]))
        out += cel(g, o["brass"], o["brass_sh"], None, [ellipse(*xf(grip, a, [(4, 16)])[0], 1.6, 1.6, o["brass_sh"]),
                                                       ellipse(*xf(grip, a, [(-6, 16)])[0], 1.6, 1.6, o["brass_sh"])], s=(2, -2))
    elif hilt == "snake":
        # the guard is a snake: its body the knuckle-bow, its head the pommel
        bow = [(14, -6), (16, 12), (4, 16), (-12, 12), (-17, 2)]
        out += [line(xf(grip, a, bow), INK, 6.4), line(xf(grip, a, bow), o["coat_lt"], 3.6)]
        out += cel(smooth(xf(grip, a, [(-14, -3), (-22, -6), (-28, -2, True), (-22, 4), (-14, 4)])), o["coat_lt"], o["coat"], None,
                   [ellipse(*xf(grip, a, [(-22, -1.8)])[0], 1.2, 1.2, "#e8c040")], s=(2, -1))
        out += cel(smooth(xf(grip, a, [(12, -9, True), (18, -9, True), (18, 9, True), (12, 9, True)])), o["brass"], o["brass_sh"], None)
    else:
        bow = [(16, -6), (18, 12), (4, 17), (-12, 13), (-16, 4)]
        out += [line(xf(grip, a, bow), INK, 5.6), line(xf(grip, a, bow), o["brass"], 3.0)]
        out += cel(smooth(xf(grip, a, [(12, -9, True), (18, -9, True), (18, 9, True), (12, 9, True)])), o["brass"], o["brass_sh"], None)
        out += cel(smooth(xf(grip, a, [(-14, -5), (-21, -4), (-21, 4), (-14, 5)])), o["brass"], o["brass_sh"], None)
    return out


def grip_point():
    wr = P("near_hand")
    return (wr[0] + 8, wr[1] + 1)


def near_arm(o):
    sh, el, wr = P("near_arm_u"), P("near_arm_l"), P("near_hand")
    # a full blouse sleeve gathered at the elbow
    sleeve = smooth([(sh[0] - 13, sh[1] - 6), (sh[0] + 6, sh[1] - 10), (sh[0] + 16, sh[1] + 8), (el[0] + 12, el[1] - 12),
                     (el[0] + 8, el[1] + 2), (el[0] - 6, el[1] + 4), (el[0] - 12, el[1] - 8), (sh[0] - 14, sh[1] + 14)])
    if o.get("jacket") or o.get("longcoat"):
        upper = cel(sleeve, o["coat"], o["coat_sh"], o["coat_lt"], [line([(el[0] - 12, el[1] - 4), (el[0] + 10, el[1] - 8)], o["sash"], 3)], s=(7, -4))
    else:
        upper = cel(sleeve, o["blouse"], o["blouse_sh"], None, [line([(sh[0] + 2, sh[1] + 4), (el[0] - 2, el[1] - 6)], o["blouse_sh"], 1.4)], s=(7, -4))
    lower = limb(el, wr, 7.0, 5.6, o["skin"], o["skin_sh"], o["skin_lt"])
    # a leather bracer
    lower += cel(capsule(lerp(el, wr, 0.45), lerp(el, wr, 0.92), 7.6, 6.6), o["boot"], o["boot_sh"], o["boot_lt"], s=(3, -2))
    hand = cutlass(o, grip_point()) + hand_grip(grip_point(), BLADE_DEG, o["skin"], o["skin_sh"], o["skin_lt"], k=0.95)
    return upper, lower, hand


def slash_fx(o):
    """The crescent the cutlass leaves as it cuts up from behind her hip
    (``fx_slash``): on the side of the blade it came from (below it, as it
    rises), widening toward the point; nothing ahead of the edge."""
    g, a = grip_point(), BLADE_DEG
    outer = _bend([(30 + i * 13, 8 + 30 * math.sin(math.pi * min(1.0, i / 8.0) * 0.5)) for i in range(9)])
    inner = _bend([(30 + i * 13, 8) for i in range(8, -1, -1)])
    return [path(smooth(xf(g, a, outer + inner)), o["steel_lt"], extra=' fill-opacity="0.85"'),
            line(xf(g, a, _bend([(46, 14), (90, 24), (128, 34)])), "#ffffff", 1.6)]


def drawn(o) -> Dict[str, list]:
    out = {"coat": coat_tails(o) if o["tails"] else [], "torso": torso(o), "head": head(o), "fx-slash": slash_fx(o)}
    c, k = HEAD_C, HEAD_K
    out["eye-open"] = eye(c, k, o["skin_sh"], "open")
    out["eye-shut"] = eye(c, k, o["skin_sh"], "shut")
    out["far-arm-upper"], out["far-arm-lower"], out["far-hand"] = far_arm(o)
    out["near-arm-upper"], out["near-arm-lower"], out["near-hand"] = near_arm(o)
    for side in ("far", "near"):
        out[f"{side}-thigh"], out[f"{side}-shin"], out[f"{side}-foot"] = leg(o, side)
    return out


#: The parts, in the order they are drawn: (group id, label, part, bone, z, opacity channel).
LAYERS = [
    ("far-arm-upper", "Far Arm - Sleeve", "far_arm_u", "far_arm_u", 4, ""),
    ("far-arm-lower", "Far Arm - Forearm", "far_arm_l", "far_arm_l", 5, ""),
    ("far-hand", "Far Hand", "far_hand", "far_hand", 6, ""),
    ("far-thigh", "Far Thigh", "far_leg_u", "far_leg_u", 8, ""),
    ("far-foot", "Far Boot", "far_foot", "far_foot", 9, ""),
    ("far-shin", "Far Shin and Boot Shaft", "far_leg_l", "far_leg_l", 10, ""),
    ("coat", "Coat Tails", "coat", "coat", 14, ""),
    ("near-thigh", "Near Thigh", "near_leg_u", "near_leg_u", 16, ""),
    ("near-foot", "Near Boot", "near_foot", "near_foot", 17, ""),
    ("near-shin", "Near Shin and Boot Shaft", "near_leg_l", "near_leg_l", 18, ""),
    ("torso", "Torso", "torso", "torso", 22, ""),
    ("head", "Head", "head", "head", 26, ""),
    ("eye-open", "Eye - Open", "eye_open", "head", 27, "eye_open"),
    ("eye-shut", "Eye - Shut", "eye_shut", "head", 27, "eye_shut"),
    ("fx-slash", "FX - Slash", "fx_slash", "near_hand", 29, "fx_slash"),
    ("near-arm-upper", "Near Arm - Sleeve", "near_arm_u", "near_arm_u", 30, ""),
    ("near-arm-lower", "Near Arm - Forearm", "near_arm_l", "near_arm_l", 31, ""),
    ("near-hand", "Near Hand and Cutlass", "near_hand", "near_hand", 32, ""),
]


def svg_text(look: str = LOOK) -> str:
    o = LOOKS[look]
    begin(o["ink"], 1.5)
    _N[0] = 0
    parts = drawn(o)
    svg.PARTS.clear()
    for group, label, name, bone, z, channel in LAYERS:
        extra = (f' data-rig-opacity="{channel}"' + (' data-rig-default="1"' if channel == "eye_open" else "")) if channel else ""
        svg.part(group, label, name, bone, z, parts[group], extra)
    note = ("the Pirate Cutlass Viper's look (Jon chose A, 2026-10-18)" if look == LOOK
            else "KEPT, NOT CAST: a Viper look Jon kept (2026-10-18), not registered in the cast")
    text = svg.document(
        size=(W, H), design=f"pirate-cutlass-viper-{look}", layer_id="pirate-cutlass-viper", label=VIEW,
        comment=[f"  <!-- {note}: side view facing right, the ground at y=500.",
                 "       Drawn by scripts/svg_art/pirate_cutlass_viper_art.py; each part turns about its JOINTS entry. -->"],
        joints=svg.joints_layer({k: (v[1], v[2]) for k, v in JOINTS.items()}),
    )
    sx, sy = o.get("build", (1.0, 1.0))
    if (sx, sy) != (1.0, 1.0):
        # a kept look's build: the whole figure a touch narrower/taller or broader, about her feet
        t = f"translate({270.0 * (1 - sx):.2f},{GROUND_Y * (1 - sy):.2f}) scale({sx},{sy})"
        text = text.replace('<g id="pirate-cutlass-viper" ', f'<g id="pirate-cutlass-viper" transform="{t}" ', 1)
    return text


def main() -> None:
    if len(sys.argv) > 2 and sys.argv[1] == "--all":
        out = Path(sys.argv[2])
        out.mkdir(parents=True, exist_ok=True)
        for look in LOOKS:
            (out / f"pirate_cutlass_viper_{look}.svg").write_text(svg_text(look), encoding="utf8")
            print(out / f"pirate_cutlass_viper_{look}.svg")
        return
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".svg.tmp")
    tmp.write_text(svg_text(), encoding="utf8")
    tmp.replace(OUT)
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
