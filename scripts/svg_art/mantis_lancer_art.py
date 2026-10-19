#!/usr/bin/env python3
"""How the Mantis Lancer's SVG was first drawn (reference, not authority).

    uv run python scripts/svg_art/mantis_lancer_art.py            # its look (A)
    uv run python scripts/svg_art/mantis_lancer_art.py --all DIR  # every look, to DIR

Writes ``data/characters/mantis_lancer/mantis_lancer.svg``; the SVG owns the
art after this has run once. ``JOINTS`` says where each part turns and
``LAYERS`` lists the parts; ``scripts/build_mantis_lancer_rig.py`` reads both
and authors the rows.

Jon, 2026-10-18, of three redraws of the mantis he had called old bad art:
"A is good for default mantis", and "keep all 3 for basically everyone". A
(``conehead``) is a slender green conehead mantis standing on four legs, its
red crest the cone of its head, the raptorial blades held in the praying
guard. B (``lacquered``, an armoured biped with a real lance) and C
(``deadleaf``, a low wide dead-leaf mantis) are KEPT, NOT CAST: their bodies
are not A's skeleton, so ``--all`` draws them whole, as their candidates were
drawn, and nothing rigs or registers them.

Drawing: cel-shaded with a thin ink. Within one part every shape's ink is
painted first and every fill over it, so a part reads as one silhouette with
no seams inside it; a part drawn later overlaps an earlier one with its own
ink edge (a knee knob over the thigh it turns on).
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
OUT = ROOT / "ambition_sprite2d_renderer" / "data" / "characters" / "mantis_lancer" / "mantis_lancer.svg"
VIEW = "Mantis Lancer - Side Right"
LOOK = "conehead"
W, H = 560, 560
#: The ground under its feet, in SVG units.
GROUND_Y = 470.0

# ---------------------------------------------------------------- cel kit

INK = "#141414"
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
    down-back (a light band stays on the up-front edge), then a SHADE band on
    the down-back edge; ``extra`` is drawn inside it, clipped."""
    _CID[0] += 1
    cid = f"m{_CID[0]}"
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


def frame(a, b):
    """The unit along a->b, its normal (+90 degrees, y down) and its length."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    d = math.hypot(dx, dy)
    ux, uy = dx / d, dy / d
    return (ux, uy), (-uy, ux), d


def at(a, b, t, s):
    (ux, uy), (nx, ny), d = frame(a, b)
    return (a[0] + ux * d * t + nx * s, a[1] + uy * d * t + ny * s)


# --------------------------------------------------------------- pieces

def blade(a, b, w, n_sp=0, side=1, sp_len=5.0, t0=0.18, t1=0.86, root_w=0.8, swell=0.45):
    """A tapered blade from a (root) to b (sharp tip); spines on ``side``."""
    def wt(t):
        return w * (root_w + swell * math.sin(math.pi * t * 0.9)) * (1 - t ** 2.2)
    N = 10
    out = [at(a, b, i / N, -side * wt(i / N)) for i in range(N)]
    out.append(tuple(b) + (True,))
    sp = sorted([t0 + (t1 - t0) / n_sp * (k + 0.5) for k in range(n_sp)], reverse=True) if n_sp else []
    j = 0
    for i in range(N - 1, -1, -1):
        t = i / N
        while j < len(sp) and sp[j] > t:
            tc, dd = sp[j], 0.022
            out.append(at(a, b, tc + dd, side * wt(tc + dd) * 0.95) + (True,))
            out.append(at(a, b, tc + dd * 2.2, side * (wt(tc) + sp_len)) + (True,))
            out.append(at(a, b, tc - dd, side * wt(tc - dd) * 0.95) + (True,))
            j += 1
        out.append(at(a, b, t, side * wt(t)))
    return smooth(out)


def pal_of(o, far=False):
    if far:
        return dict(base=o["far"], light=None, shade=o["far_sh"], a=2.5)
    return dict(base=o["base"], light=o["light"], shade=o["shade"], a=2.6, b=1.6)


def knob(g, p, r, pal):
    g.add(capsule(p, (p[0] + 0.1, p[1] + 0.1), r, r), **pal)


def tarsus(g, ankle, dirx, pal, r=3.0):
    """An insect foot: three beads and a hooked claw along the ground."""
    ax, ay = ankle
    p1 = (ax + dirx * 9, GROUND_Y - 4)
    p2 = (ax + dirx * 17, GROUND_Y - 2.5)
    p3 = (ax + dirx * 24, GROUND_Y - 2)
    g.add(capsule(ankle, p1, r, r * 0.85), **pal)
    g.add(capsule(p1, p2, r * 0.85, r * 0.75), **pal)
    g.add(capsule(p2, p3, r * 0.75, r * 0.6), **pal)
    claw = smooth([(p3[0] - dirx * 1, p3[1] - 2.2), (p3[0] + dirx * 6, p3[1] - 0.5), (p3[0] + dirx * 8, p3[1] + 2.2, True),
                   (p3[0] + dirx * 2, p3[1] + 1.8)])
    g.add(claw, base=pal["base"])


def leg(hip, knee, ankle, dirx, pal, groups, r=(5.0, 4.2, 3.4)):
    """Femur, tibia (a knob at the knee) and tarsus, into ``groups`` (one
    each, or the same group three times for a whole drawing)."""
    gu, gl, gf = groups
    gu.add(capsule(hip, knee, r[0], r[1]), **pal)
    gl.add(capsule(knee, ankle, r[1] * 0.9, r[2]), **pal)
    knob(gl, knee, r[1] * 1.15, pal)
    tarsus(gf, ankle, dirx, pal, r=r[2] * 0.9)


def _side(a, b, toward):
    """+1 if ``toward`` lies on the +normal side of a->b, else -1."""
    (_ux, _uy), (nx, ny), _d = frame(a, b)
    return 1 if (toward[0] - a[0]) * nx + (toward[1] - a[1]) * ny > 0 else -1


def raptorial(o, sh, knee, tip, hook, groups, far=False, steel=False, n_sp=5, fw=9.0):
    """Coxa sh->knee, the femur blade knee->tip (spines toward the tibia), the
    tibia folded back tip->hook with its own spines; into ``groups``."""
    gc, gb, gh = groups
    p = pal_of(o, far)
    gc.add(capsule(sh, knee, 7.5, 6.0), **p)
    side = _side(knee, tip, hook)
    fp = dict(p)
    if steel and not far:
        fp = dict(base=o["steel"], light=o["steel_lt"], shade=o["steel_sh"], a=2.4, b=1.6)
    gb.add(blade(knee, tip, fw, n_sp=n_sp, side=side, sp_len=6.0, root_w=0.9, swell=0.35), **fp)
    knob(gb, knee, 6.8, p)
    gh.add(blade(tip, hook, fw * 0.62, n_sp=3, side=_side(tip, hook, knee), sp_len=4.0, root_w=0.9, swell=0.2, t0=0.25, t1=0.8), **fp)
    knob(gh, tip, fw * 0.6, p)
    if not far:
        # a pale cutting edge along the blade's spined side, and its eye-spot
        gb.post.append(line([at(knee, tip, 0.2, side * 4.0), at(knee, tip, 0.85, side * 1.8)], o["edge"], 1.4))
        if o.get("spot"):
            c = at(knee, tip, 0.38, 0.0)
            gb.post.append(ellipse(c[0], c[1], 3.2, 2.4, o["spot"], INK, 1.0))


def compound_eye(o, c, rx, ry, rot=0.0, dead=False):
    x, y = c
    out = [ellipse(x, y, rx + INKW, ry + INKW, INK, rot=rot), ellipse(x, y, rx, ry, o["eye"], rot=rot),
           ellipse(x - rx * 0.25, y + ry * 0.28, rx * 0.72, ry * 0.6, o["eye_sh"], rot=rot)]
    if dead:
        k = rx * 0.45
        return out + [line([(x - k, y - k), (x + k, y + k)], INK, 1.6), line([(x - k, y + k), (x + k, y - k)], INK, 1.6)]
    # the pseudopupil, and a glint
    return out + [ellipse(x + rx * 0.22, y - ry * 0.05, rx * 0.26, ry * 0.26, INK),
                  ellipse(x + rx * 0.05, y - ry * 0.45, rx * 0.22, ry * 0.16, "#ffffff", rot=rot)]


def antenna(o, root, mid, tip):
    return [line([root, mid, tip], INK, 2.6), line([root, mid, tip], o["antenna"], 1.0)]


# ------------------------------------------------------------- the looks

LOOKS = {
    "conehead": dict(label="A: slender conehead, four legs, red cone", ink="#14200f",
                     base="#6fa24e", light="#a4cf72", shade="#4a7a36", far="#4f7c3a", far_sh="#3a5e2b",
                     wing="#86b45c", wing_lt="#b3d985", wing_sh="#5f8d42", vein="#4a7a36",
                     crest="#c9502c", crest_lt="#ec8a52", crest_sh="#93361d",
                     eye="#e3dc86", eye_sh="#b9b45e", antenna="#4a7a36", edge="#e9ecc8", spot="#e6e0a0",
                     belly="#93c062", fx="#f2f7d6", fx_core="#ffffff"),
    "lacquered": dict(label="B: armoured biped lancer, a real lance", ink="#17161a",
                      base="#3f7d63", light="#6aa785", shade="#2b5945", far="#2f5f4b", far_sh="#224536",
                      plate="#a3322a", plate_lt="#cf5a43", plate_sh="#71211c", trim="#d9a441",
                      crest="#d9a441", crest_lt="#f1cf78", crest_sh="#a77824",
                      eye="#f0c86a", eye_sh="#c49a3f", antenna="#2b5945", edge="#e7ead8",
                      wood="#6b4428", wood_lt="#8c5e3a", wood_sh="#4a2d1a", steel="#c3ccd2", steel_lt="#eef2f4", steel_sh="#8a959c",
                      tassel="#c23a2e"),
    "deadleaf": dict(label="C: low wide dead-leaf mantis, blades up", ink="#1f150c",
                     base="#a77b47", light="#d0a868", shade="#7a5430", far="#7d5a35", far_sh="#5e4126",
                     wing="#946a3c", wing_lt="#c39a5e", wing_sh="#6c4a28", vein="#5a3c20",
                     crest="#8a5a2e", crest_lt="#b98446", crest_sh="#5e3c1e",
                     eye="#c9d98a", eye_sh="#9fae5c", antenna="#6c4a28", edge="#efe2c4", band="#5a3c20", spot="#f1e6c6"),
}

#: Where each bone of look A turns (SVG units): ``bone: (parent, x, y)``, parents first.
JOINTS: Dict[str, Tuple[str, float, float]] = {
    "body": ("", 250.0, 348.0),
    "abdomen": ("body", 240.0, 346.0),
    "prothorax": ("body", 268.0, 338.0),
    "head": ("prothorax", 296.0, 226.0),
    "far_coxa": ("prothorax", 280.0, 288.0),
    "far_blade": ("far_coxa", 296.0, 322.0),
    "far_hook": ("far_blade", 338.0, 258.0),
    "near_coxa": ("prothorax", 288.0, 292.0),
    "near_blade": ("near_coxa", 308.0, 326.0),
    "near_hook": ("near_blade", 358.0, 254.0),
    "far_hind_u": ("body", 234.0, 352.0),
    "far_hind_l": ("far_hind_u", 214.0, 398.0),
    "far_hind_foot": ("far_hind_l", 204.0, 464.0),
    "far_fore_u": ("body", 254.0, 350.0),
    "far_fore_l": ("far_fore_u", 284.0, 394.0),
    "far_fore_foot": ("far_fore_l", 276.0, 462.0),
    "near_hind_u": ("body", 236.0, 354.0),
    "near_hind_l": ("near_hind_u", 200.0, 398.0),
    "near_hind_foot": ("near_hind_l", 184.0, 464.0),
    "near_fore_u": ("body", 256.0, 352.0),
    "near_fore_l": ("near_fore_u", 292.0, 392.0),
    "near_fore_foot": ("near_fore_l", 298.0, 462.0),
}


def P(name):
    return JOINTS[name][1], JOINTS[name][2]


#: The legs: (bone prefix, the way its foot points, far).
LEGS = (("far_hind", -1, True), ("far_fore", +1, True), ("near_hind", -1, False), ("near_fore", +1, False))


def drawn(o) -> Dict[str, list]:
    """Look A's parts, keyed by layer group id."""
    G: Dict[str, Group] = {}

    def g(key):
        return G.setdefault(key, Group())

    for prefix, dirx, far in LEGS:
        side = prefix.replace("_", "-")
        leg(P(f"{prefix}_u"), P(f"{prefix}_l"), P(f"{prefix}_foot"), dirx, pal_of(o, far),
            (g(f"{side}-femur"), g(f"{side}-tibia"), g(f"{side}-foot")))
    for side, far in (("far", True), ("near", False)):
        raptorial(o, P(f"{side}_coxa"), P(f"{side}_blade"), P(f"{side}_hook"),
                  (318.0, 296.0) if far else (334.0, 296.0), (g(f"{side}-coxa"), g(f"{side}-blade"), g(f"{side}-hook")), far=far)
    # the abdomen, and the folded wings over it
    abd = smooth([(240, 334), (204, 326), (166, 322), (134, 322), (112, 316, True), (116, 330), (128, 346), (160, 358), (200, 362),
                  (232, 360), (250, 352)])
    segs = [line([(x, 330 + (x - 110) * 0.02), (x - 4, 360)], o["shade"], 1.1) for x in (150, 172, 194, 216)]
    g("abdomen").add(abd, base=o["base"], light=o["belly"], shade=o["shade"], a=6, b=3, extra=segs)
    wing = smooth([(250, 330), (214, 316), (170, 310), (130, 314), (106, 318, True), (140, 326), (190, 332), (236, 340)])
    g("wing").add(wing, base=o["wing"], light=o["wing_lt"], shade=o["wing_sh"], a=3, b=2,
                  extra=[line([(240, 330), (190, 322), (130, 318)], o["vein"], 1.2), line([(200, 324), (176, 316)], o["vein"], 0.9),
                         ellipse(214, 323, 3.2, 1.8, o["wing_lt"])])
    g("thorax").add(capsule((228, 350), (272, 340), 14, 12), **pal_of(o))
    # the long prothorax, thickening where the arms hang
    g("prothorax").add(capsule((266, 342), (296, 232), 10, 7.5), base=o["base"], light=o["light"], shade=o["shade"], a=3.5, b=2)
    g("prothorax").add(capsule((268, 334), (281, 290), 11, 9.5), **pal_of(o))
    # the head: a broad triangle, a tall forked cone on top (the red crest)
    cone = smooth([(292, 210), (284, 188), (280, 166), (276, 150, True), (288, 160), (292, 156, True), (298, 176), (306, 196), (306, 210)])
    g("head").add(cone, base=o["crest"], light=o["crest_lt"], shade=o["crest_sh"], a=3, b=2)
    hd = smooth([(288, 222), (292, 206), (306, 200), (322, 204), (330, 214), (324, 226), (316, 240, True), (308, 246), (298, 238)])
    g("head").add(hd, base=o["base"], light=o["light"], shade=o["shade"], a=3, b=2,
                  extra=[line([(304, 234), (316, 240)], o["shade"], 1.0)])
    g("head").post += [line([(312, 244), (318, 250), (322, 248)], INK, 1.6)] + antenna(o, (322, 204), (340, 180), (362, 172))
    out = {k: v.items() for k, v in G.items()}
    out["eye-open"] = compound_eye(o, (318, 213), 8.0, 9.0, rot=-15)
    out["eye-dead"] = compound_eye(o, (318, 213), 8.0, 9.0, rot=-15, dead=True)
    out.update(fx_parts(o))
    return out


def fx_parts(o) -> Dict[str, list]:
    """The strikes, drawn about the near arm at rest: speed lines trailing
    the hook's point along its length (``fx_stab``, on the hook, nothing
    ahead of the point) and the crescent the blade leaves behind it as it
    sweeps down (``fx_slash``: on the blade's back, the side it came from)."""
    knee, tip = P("near_blade"), P("near_hook")
    point = (334.0, 296.0)
    (ux, uy), (nx, ny), d = frame(tip, point)
    stab = []
    for off, back, length, w in ((-11.0, 6.0, 64.0, 2.6), (11.0, 14.0, 50.0, 2.0), (-20.0, 22.0, 34.0, 1.6)):
        a = (point[0] - ux * back + nx * off, point[1] - uy * back + ny * off)
        b = (a[0] - ux * length, a[1] - uy * length)
        stab += [line([a, b], o["fx"], w + 1.6), line([a, b], o["fx_core"], w * 0.5)]
    # the crescent: from the blade's root round past its tip, on the side away from the spines (its back)
    side = -_side(knee, tip, (334.0, 296.0))
    pts = []
    for i in range(9):
        t = 0.25 + i * 0.12
        pts.append(at(knee, tip, t, side * (6 + 26 * math.sin(math.pi * min(1.0, (t - 0.25) / 1.0)))))
    for i in range(8, -1, -1):
        t = 0.25 + i * 0.12
        pts.append(at(knee, tip, t, side * 6))
    slash = [path(smooth(pts), o["fx"]), line([at(knee, tip, 0.4, side * 12), at(knee, tip, 1.0, side * 24)], o["fx_core"], 1.6)]
    return {"fx-stab": stab, "fx-slash": slash}


#: The parts, in the order they are drawn: (group id, label, part, bone, z, opacity channel).
LAYERS = [
    ("far-hind-femur", "Far Hind Leg - Femur", "far_hind_u", "far_hind_u", 2, ""),
    ("far-hind-tibia", "Far Hind Leg - Tibia", "far_hind_l", "far_hind_l", 3, ""),
    ("far-hind-foot", "Far Hind Leg - Tarsus", "far_hind_foot", "far_hind_foot", 4, ""),
    ("far-fore-femur", "Far Fore Leg - Femur", "far_fore_u", "far_fore_u", 5, ""),
    ("far-fore-tibia", "Far Fore Leg - Tibia", "far_fore_l", "far_fore_l", 6, ""),
    ("far-fore-foot", "Far Fore Leg - Tarsus", "far_fore_foot", "far_fore_foot", 7, ""),
    ("far-coxa", "Far Arm - Coxa", "far_coxa", "far_coxa", 8, ""),
    ("far-blade", "Far Arm - Blade", "far_blade", "far_blade", 9, ""),
    ("far-hook", "Far Arm - Hook", "far_hook", "far_hook", 10, ""),
    ("abdomen", "Abdomen", "abdomen", "abdomen", 12, ""),
    ("thorax", "Thorax", "thorax", "body", 13, ""),
    ("wing", "Wings", "wing", "abdomen", 14, ""),
    ("prothorax", "Prothorax", "prothorax", "prothorax", 15, ""),
    ("head", "Head", "head", "head", 18, ""),
    ("eye-open", "Eye - Open", "eye_open", "head", 19, "eye_open"),
    ("eye-dead", "Eye - Dead", "eye_dead", "head", 19, "eye_dead"),
    ("near-hind-femur", "Near Hind Leg - Femur", "near_hind_u", "near_hind_u", 20, ""),
    ("near-hind-tibia", "Near Hind Leg - Tibia", "near_hind_l", "near_hind_l", 21, ""),
    ("near-hind-foot", "Near Hind Leg - Tarsus", "near_hind_foot", "near_hind_foot", 22, ""),
    ("near-fore-femur", "Near Fore Leg - Femur", "near_fore_u", "near_fore_u", 23, ""),
    ("near-fore-tibia", "Near Fore Leg - Tibia", "near_fore_l", "near_fore_l", 24, ""),
    ("near-fore-foot", "Near Fore Leg - Tarsus", "near_fore_foot", "near_fore_foot", 25, ""),
    ("fx-slash", "FX - Slash", "fx_slash", "near_blade", 29, "fx_slash"),
    ("near-coxa", "Near Arm - Coxa", "near_coxa", "near_coxa", 30, ""),
    ("near-blade", "Near Arm - Blade", "near_blade", "near_blade", 31, ""),
    ("near-hook", "Near Arm - Hook", "near_hook", "near_hook", 32, ""),
    ("fx-stab", "FX - Stab", "fx_stab", "near_hook", 33, "fx_stab"),
]


# ------------------------------------------------ the kept looks, whole

def draw_lacquered(o):
    """B, KEPT, NOT CAST: an armoured biped lancer gripping a real lance."""
    far, body, near, lance, arm = Group(), Group(), Group(), Group(), Group()
    fp = pal_of(o, far=True)
    _biped_leg(o, (244, 372), (268, 410), (246, 448), far, fp)
    raptorial(o, (270, 288), (286, 318), (318, 300), (296, 328), (far, far, far), far=True, n_sp=3)
    abd = smooth([(252, 356), (226, 354), (200, 366), (184, 388), (182, 410), (194, 422), (214, 416), (236, 400), (254, 388)])
    body.add(abd, **pal_of(o), extra=[line([(x, 360 + (250 - x) * 0.3), (x + 14, 404 - (250 - x) * 0.1)], o["shade"], 1.1) for x in (196, 214, 232)])
    body.add(capsule((246, 372), (262, 334), 15, 13), **pal_of(o))
    cape = smooth([(262, 326), (244, 330), (220, 344), (198, 368), (184, 396), (186, 412, True), (204, 400), (226, 380), (248, 364), (262, 352)])
    body.add(cape, base=o["plate"], light=o["plate_lt"], shade=o["plate_sh"], a=4, b=2.2,
             extra=[line([(186, 410), (206, 398), (228, 378), (250, 362)], o["trim"], 2.4),
                    line([(250, 336), (222, 356), (202, 384)], o["plate_sh"], 1.2)])
    body.add(capsule((262, 340), (284, 246), 10, 8), **pal_of(o))
    bp = smooth([(258, 336), (256, 300), (266, 270), (286, 262, True), (292, 290), (286, 324), (272, 342)])
    body.add(bp, base=o["plate"], light=o["plate_lt"], shade=o["plate_sh"], a=4, b=2,
             extra=[line([(268, 272), (288, 266)], o["trim"], 2.2), line([(262, 300), (290, 296)], o["plate_sh"], 1.2)])
    body.add(smooth([(276, 226), (280, 210), (296, 204), (312, 208), (320, 218), (314, 230), (306, 244, True), (296, 250), (286, 242)]), **pal_of(o))
    helm = smooth([(274, 226), (276, 206), (290, 196), (306, 196), (316, 204), (312, 208), (296, 206), (284, 212), (282, 228)])
    body.add(helm, base=o["plate"], light=o["plate_lt"], shade=o["plate_sh"], a=3, b=2)
    cres = smooth([(296, 198), (288, 180), (278, 166, True), (294, 174), (304, 166, True), (318, 162, True), (308, 178), (302, 198)])
    body.add(cres, base=o["crest"], light=o["crest_lt"], shade=o["crest_sh"], a=2, b=1.5)
    body.post += compound_eye(o, (309, 217), 7.0, 8.0, rot=-15)
    body.post += [line([(302, 248), (308, 254), (312, 252)], INK, 1.6)] + antenna(o, (312, 206), (330, 188), (350, 186))
    _biped_leg(o, (252, 374), (282, 410), (264, 450), near, pal_of(o))
    a_, b_ = (186, 346), (432, 298)
    lance.add(capsule(a_, b_, 3.6, 3.2), base=o["wood"], light=o["wood_lt"], shade=o["wood_sh"], a=1.6, b=1.0)
    lance.add(blade((428, 299), (478, 289), 7.5, root_w=0.7, swell=0.5), base=o["steel"], light=o["steel_lt"], shade=o["steel_sh"], a=2.5, b=1.5)
    lance.add(capsule((424, 300), (432, 298), 5, 5), base=o["trim"], light=o["crest_lt"], shade=o["crest_sh"], a=2)
    tas = smooth([(424, 302), (418, 316), (410, 330, True), (420, 324), (426, 332, True), (428, 316), (430, 302)])
    lance.add(tas, base=o["tassel"], shade=o["plate_sh"], a=2)
    lance.add(capsule((180, 347), (190, 345), 4.6, 4.6), base=o["steel_sh"], light=o["steel"], a=1.5)
    raptorial(o, (280, 290), (296, 318), (334, 300), (326, 326), (arm, arm, arm), n_sp=3)
    sode = smooth([(268, 278), (290, 272), (300, 284, True), (296, 300, True), (272, 302, True)])
    arm.add(sode, base=o["plate"], light=o["plate_lt"], shade=o["plate_sh"], a=3, b=2, extra=[line([(272, 300), (296, 298)], o["trim"], 2.0)])
    return [far, body, near, lance, arm]


def _biped_leg(o, hip, knee, ankle, g, p):
    """B's strong insect leg standing alone: a thick femur, a slim tibia, a
    long three-bead tarsus forward with a claw and a spur back."""
    g.add(capsule(hip, knee, 9, 7), **p)
    g.add(capsule(knee, ankle, 6, 4.5), **p)
    knob(g, knee, 7.5, p)
    sp = smooth([(ankle[0] - 2, ankle[1] - 3), (ankle[0] - 12, ankle[1] + 6), (ankle[0] - 15, ankle[1] + 10, True), (ankle[0] - 4, ankle[1] + 6)])
    g.add(sp, base=p["base"], shade=p.get("shade"), a=1.5)
    tarsus(g, ankle, +1, p, r=4.2)


def draw_deadleaf(o):
    """C, KEPT, NOT CAST: a low, wide dead-leaf mantis, blades up in a guard."""
    far, body, near, arm = Group(), Group(), Group(), Group()
    fp = pal_of(o, far=True)
    R = (6.2, 5.0, 3.8)
    leg((258, 404), (292, 390), (314, 462), +1, fp, (far, far, far), r=R)
    leg((234, 406), (206, 392), (184, 462), -1, fp, (far, far, far), r=R)
    raptorial(o, (292, 356), (312, 384), (348, 316), (378, 338), (far, far, far), far=True, n_sp=5, fw=10.0)
    abd = smooth([(244, 394), (210, 380), (176, 368), (146, 354), (124, 336), (112, 318), (104, 314), (100, 326), (106, 344), (120, 360),
                  (132, 372, True), (138, 386), (160, 396, True), (168, 406), (198, 414), (228, 416), (250, 410)])
    body.add(abd, base=o["base"], light=o["light"], shade=o["shade"], a=7, b=3,
             extra=[line([(244, 402), (200, 396), (156, 384), (124, 362), (108, 330)], o["band"], 1.4),
                    line([(186, 396), (180, 410)], o["shade"], 1.0), line([(214, 400), (210, 414)], o["shade"], 1.0)])
    wing = smooth([(258, 386), (224, 372), (186, 362), (152, 352), (132, 346), (124, 354), (148, 370), (194, 384), (234, 394), (256, 398)])
    body.add(wing, base=o["wing"], light=o["wing_lt"], shade=o["wing_sh"], a=3, b=2,
             extra=[line([(254, 390), (204, 378), (160, 364), (132, 352)], o["vein"], 1.3),
                    line([(206, 378), (192, 366)], o["vein"], 1.0), line([(170, 368), (158, 358)], o["vein"], 1.0),
                    ellipse(196, 374, 5, 2.6, o["wing_lt"]), ellipse(154, 362, 3.5, 2.0, o["vein"])])
    body.add(capsule((226, 404), (268, 396), 16, 14), **pal_of(o))
    body.add(capsule((262, 398), (300, 342), 11, 9), **pal_of(o))
    lobe = smooth([(252, 408), (250, 380), (262, 360), (284, 340), (314, 326, True), (318, 352), (306, 378), (288, 400), (268, 414)])
    body.add(lobe, base=o["wing"], light=o["wing_lt"], shade=o["wing_sh"], a=5, b=2.4,
             extra=[line([(264, 398), (302, 344)], o["band"], 1.3), line([(280, 382), (296, 372)], o["shade"], 1.0),
                    line([(272, 370), (284, 362)], o["shade"], 1.0)])
    body.add(smooth([(300, 326), (302, 312), (314, 304), (330, 306), (340, 316), (334, 330), (324, 344, True), (314, 348), (304, 340)]), **pal_of(o))
    cr = smooth([(304, 316), (296, 300), (290, 282), (286, 270, True), (300, 280), (312, 296), (318, 308)])
    body.add(cr, base=o["crest"], light=o["crest_lt"], shade=o["crest_sh"], a=2, b=1.5)
    body.post += compound_eye(o, (327, 316), 7.5, 8.5, rot=-10)
    body.post += [line([(320, 346), (326, 352), (330, 350)], INK, 1.6)] + antenna(o, (332, 306), (354, 282), (382, 276))
    leg((264, 406), (306, 388), (334, 462), +1, pal_of(o), (near, near, near), r=R)
    leg((240, 408), (194, 390), (160, 462), -1, pal_of(o), (near, near, near), r=R)
    kn, tp = (324, 388), (366, 314)
    raptorial(o, (304, 360), kn, tp, (398, 336), (arm, arm, arm), n_sp=5, fw=10.0)
    for t in (0.34, 0.6):
        arm.post.append(line([at(kn, tp, t, -8), at(kn, tp, t + 0.04, 8)], o["band"], 2.4))
    return [far, body, near, arm]


KEPT = {"lacquered": draw_lacquered, "deadleaf": draw_deadleaf}


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
            size=(W, H), design=f"mantis-lancer-{look}", layer_id="mantis-lancer", label=VIEW,
            comment=[f"  <!-- KEPT, NOT CAST: a mantis look Jon kept (2026-10-18), {o['label']}; drawn whole, not rigged. -->"],
            joints=[])
    parts = drawn(o)
    svg.PARTS.clear()
    for group, label, name, bone, z, channel in LAYERS:
        extra = (f' data-rig-opacity="{channel}"' + (' data-rig-default="1"' if channel == "eye_open" else "")) if channel else ""
        svg.part(group, label, name, bone, z, parts[group], extra)
    return svg.document(
        size=(W, H), design=f"mantis-lancer-{look}", layer_id="mantis-lancer", label=VIEW,
        comment=["  <!-- the Mantis Lancer's look (Jon chose A, 2026-10-18): side view facing right, the ground at y=470.",
                 "       Drawn by scripts/svg_art/mantis_lancer_art.py; each part turns about its JOINTS entry. -->"],
        joints=svg.joints_layer({k: (v[1], v[2]) for k, v in JOINTS.items()}),
    )


def main() -> None:
    if len(sys.argv) > 2 and sys.argv[1] == "--all":
        out = Path(sys.argv[2])
        out.mkdir(parents=True, exist_ok=True)
        for look in LOOKS:
            (out / f"mantis_lancer_{look}.svg").write_text(svg_text(look), encoding="utf8")
            print(out / f"mantis_lancer_{look}.svg")
        return
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".svg.tmp")
    tmp.write_text(svg_text(), encoding="utf8")
    tmp.replace(OUT)
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
