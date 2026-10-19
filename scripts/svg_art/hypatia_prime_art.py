#!/usr/bin/env python3
"""How Hypatia Prime's SVG was first drawn (reference, not authority).

    uv run python scripts/svg_art/hypatia_prime_art.py            # her look (A)
    uv run python scripts/svg_art/hypatia_prime_art.py --all DIR  # every look, to DIR

Writes ``data/characters/hypatia_prime/hypatia_prime.svg``; the SVG owns the
art after this has run once. ``joints(look)`` says where each part turns and
``layers(look)`` lists the parts; ``scripts/build_hypatia_prime_rig.py`` reads
both and authors the rows.

Who she is (``targets/characters/hypatia_prime.py`` AUTHORING_DESCRIPTION): a
reconstruction of Hypatia of Alexandria - mathematician, astronomer,
philosopher, teacher - "assembled from incomplete sources"; 168 cm. Jon,
2026-10-18, first chose the literal reconstruction (``alexandria``: a cream
chiton, a blue himation, hair in a knot, a scroll), then corrected it: "this is
hypatia prime, not literal hypatia, so maybe give her some future techno space
armor, with the alexandria vibe. Also I think she was supposed to be an old
woman." Her look is ``prime``: an old woman (silver hair under a crown braid,
a lined face, a slight stoop, bony hands, commanding still) in sleek plate over
the ivory chiton and the blue himation - the cloth reads as cloth, the armour
as armour - with Greek-key meanders as lit circuitry along their borders, an
armillary ring at her breast and another on her back, and her staff an
armillary tech-lance. ``alexandria``, ``guardian`` (today's midnight mantle,
bronze lamellar, an astrolabe halo) and ``library`` (a white robe, a saffron
cloak, a codex) are KEPT, NOT CAST: this script draws them (``--all``) on the
same parts and bones, and nothing registers them. Her own line: "Every age redraws me in its own
clothing. I have learned to keep several wardrobes."

The chiton's skirt is two panels on their own bones (``skirt_f`` and
``skirt_b``, from the hips), so it opens when she strides; her shins and
sandalled feet are drawn under it and show below the hem.

Her effects (each an opacity channel): the astrolabe she turns in guard,
the conic sections and the lance of light, the epicycle orbits, the shadows
of her other reconstructions, the missing folios, and the revelation.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _cel_profile_kit as K  # noqa: E402
from _cel_profile_kit import capsule, cel, ellipse, hd, lerp, line, path, smooth, xf  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "ambition_sprite2d_renderer" / "data" / "characters" / "hypatia_prime" / "hypatia_prime.svg"
VIEW = "Hypatia Prime - Side Right"
LOOK = "prime"
OW = 1.45
#: The ground under her soles, in SVG units.
GROUND_Y = 500.0

BRONZE = dict(br="#c8923e", br_sh="#8e5f22", br_lt="#ecc06a")
#: Her effects' colours: a cyan of starlight on bronze, and the three hues of
#: the reconstructions that are not her.
FX = dict(glyph_fx="#6fe0f0", glyph_hi="#d8fbff", ghost_a="#509ebf", ghost_b="#ad5eaf", ghost_c="#cd9746")

LOOKS = {
    "prime": dict(
        label="Prime: an old scholar in future plate over the Alexandrian drape, an armillary lance",
        ink="#16171f", skin="#c39276", skin_sh="#936650", skin_lt="#dbb196", lips="#94605a",
        hair="#e4e1dc", hair_lt="#ffffff", hair_sh="#aaa59e", dress="#ece4d2", dress_sh="#c4b896", dress_lt="#fbf6ea",
        wrap="#2c4a80", wrap_sh="#1d3358", wrap_lt="#46699f", trim="#5fe6ff",
        sandal="#4c5568", sandal_sh="#323848", hair_kind="crown", halo=False, armor=False, hood=False, tech=True, aged=True,
        plate="#dde2ea", plate_sh="#98a3b4", plate_lt="#ffffff", plate_dk="#3a4560", glow="#5fe6ff", glow_hi="#d8fbff",
        far_prop="scroll", build=(1.0, 1.0), glyph="#5fe6ff", **BRONZE, **FX),
    "alexandria": dict(
        label="A: Alexandria - chiton, blue himation, hair knot, scroll",
        ink="#1b1618", skin="#c99a76", skin_sh="#9c6e52", skin_lt="#e0b692", lips="#a35a52",
        hair="#2a1c16", hair_lt="#4e3a2e", dress="#efe6d2", dress_sh="#c8b998", dress_lt="#fffaf0",
        wrap="#2f4f86", wrap_sh="#1f355e", wrap_lt="#4a6ea8", trim="#c8923e",
        sandal="#7a4e2c", sandal_sh="#53341c", hair_kind="knot", halo=False, armor=False, hood=False,
        far_prop="scroll", build=(1.0, 1.0), **BRONZE, **FX),
    "guardian": dict(
        label="B: today's scholar-guardian - midnight mantle, bronze, astrolabe halo",
        ink="#14131c", skin="#b98a68", skin_sh="#8c5f46", skin_lt="#d2a482", lips="#8e4c48",
        hair="#1c1514", hair_lt="#3c2e2a", dress="#4a3a78", dress_sh="#33285a", dress_lt="#6452a0",
        wrap="#232a4e", wrap_sh="#151a34", wrap_lt="#363f6e", trim="#c8923e",
        sandal="#5a3a22", sandal_sh="#3a2414", hair_kind="veiled", halo=True, armor=True, hood=True,
        far_prop="folio", build=(1.04, 1.0), glyph="#6fe0f0", **BRONZE, **FX),
    "library": dict(
        label="C: the library keeper - white robe, saffron cloak, codex",
        ink="#1c1612", skin="#d8aa86", skin_sh="#ac7a5c", skin_lt="#eec4a2", lips="#a8584e",
        hair="#5a2e1c", hair_lt="#84482c", dress="#f4f0e6", dress_sh="#cfc6b2", dress_lt="#ffffff",
        wrap="#d0902c", wrap_sh="#9a641a", wrap_lt="#eab258", trim="#2c7a78",
        sandal="#8a5a30", sandal_sh="#5e3c1e", hair_kind="loose", halo=False, armor=False, hood=False,
        far_prop="codex", build=(0.96, 1.03), **BRONZE, **FX),
}

STAFF_X = 334.0
STAFF_TOP = 104.0
CX = 270.0  # a look's build stretch is about (CX, GROUND_Y)

BASE_J = dict(head=(284.0, 163.0), neck=(278.0, 202.0), pelvis=(272.0, 330.0),
              near_shoulder=(280.0, 224.0), far_shoulder=(262.0, 220.0),
              near_elbow=(290.0, 284.0), near_wrist=(320.0, 276.0), grip=(STAFF_X, 277.0),
              far_elbow=(250.0, 284.0), far_wrist=(256.0, 334.0),
              near_hip=(282.0, 330.0), far_hip=(262.0, 330.0), near_knee=(290.0, 410.0), far_knee=(264.0, 410.0),
              near_ankle=(298.0, 484.0), far_ankle=(260.0, 484.0))

#: Each bone: (parent, the joint of the drawing it turns about). Parents first.
BONES = {
    "body": ("", "pelvis"),
    "torso": ("body", "pelvis"),
    "head": ("torso", "neck"),
    "far_arm_u": ("torso", "far_shoulder"),
    "far_arm_l": ("far_arm_u", "far_elbow"),
    "far_hand": ("far_arm_l", "far_wrist"),
    "near_arm_u": ("torso", "near_shoulder"),
    "near_arm_l": ("near_arm_u", "near_elbow"),
    "near_hand": ("near_arm_l", "near_wrist"),
    "staff": ("near_hand", "grip"),
    "skirt_b": ("body", "far_hip"),
    "skirt_f": ("body", "near_hip"),
    "far_leg_u": ("body", "far_hip"),
    "far_leg_l": ("far_leg_u", "far_knee"),
    "far_foot": ("far_leg_l", "far_ankle"),
    "near_leg_u": ("body", "near_hip"),
    "near_leg_l": ("near_leg_u", "near_knee"),
    "near_foot": ("near_leg_l", "near_ankle"),
}


def _J(o) -> Dict[str, Tuple[float, float]]:
    J = dict(BASE_J)
    if o["far_prop"] == "codex":  # the codex held against the hip
        J.update(far_elbow=(248.0, 282.0), far_wrist=(240.0, 330.0))
    if o["far_prop"] == "scroll":  # the arm hangs a little back, the scroll behind her
        J.update(far_elbow=(248.0, 286.0), far_wrist=(238.0, 330.0))
    if o.get("aged"):  # a slight stoop: the head carried forward and a little down
        J.update(head=(289.0, 168.0), neck=(281.0, 205.0))
    return J


def stretch(o, p):
    sx, sy = o["build"]
    return (CX + (p[0] - CX) * sx, GROUND_Y + (p[1] - GROUND_Y) * sy)


def joints(look: str = LOOK) -> Dict[str, Tuple[float, float]]:
    """Where each joint is DRAWN (after the look's build stretch)."""
    o = LOOKS[look]
    return {k: stretch(o, v) for k, v in _J(o).items()}


# ------------------------------------------------------------------- pieces ---

def meander(a, b, h, o, width=1.1):
    """A Greek key (meander) band from ``a`` to ``b``, ``h`` tall, as glowing
    circuitry: a rail along its foot and a square spiral rising off it each
    unit; a soft wider glow under the lines."""
    u = h / 4.0
    (ux, uy), d = K.norm(a, b), math.hypot(b[0] - a[0], b[1] - a[1])
    deg = math.degrees(math.atan2(uy, ux))
    runs = [[(0, 4 * u), (d, 4 * u)]]
    for i in range(int(d // (5 * u))):
        x0 = i * 5 * u + u * 0.5
        runs.append([(x0, 4 * u), (x0, 0), (x0 + 4 * u, 0), (x0 + 4 * u, 3 * u), (x0 + u, 3 * u), (x0 + u, u), (x0 + 3 * u, u),
                     (x0 + 3 * u, 2 * u), (x0 + 2 * u, 2 * u)])
    out = []
    for run in runs:
        pts = xf(a, deg, [(q[0], q[1] - 4 * u) for q in run])
        out.append(path("M" + " L".join(f"{K.svg.f(p[0])},{K.svg.f(p[1])}" for p in pts), "none", o["glow"], width * 2.6,
                        extra=' stroke-opacity="0.35"'))
        out.append(path("M" + " L".join(f"{K.svg.f(p[0])},{K.svg.f(p[1])}" for p in pts), "none", o["glow_hi"], width,
                        ))
    return out


def tech_lance(o):
    """Prime's staff: an armillary tech-lance - a dark alloy shaft with a lit
    seam, plate collars, the armillary of lit rings, a blade above it."""
    x = STAFF_X
    top = STAFF_TOP
    out = cel(smooth([(x - 3.8, top + 16, True), (x + 3.8, top + 16, True), (x + 3.8, 492, True), (x - 3.8, 492, True)]),
              "#3a4256", "#262c3a", "#5a6478", s=(2, 0), l=(1, 0))
    out.append(line([(x + 1.2, top + 24), (x + 1.2, 486)], o["glow"], 0.9))
    out += cel(smooth([(x - 4, 490, True), (x + 4, 490, True), (x, 500, True)]), o["plate_sh"], o["plate_dk"], None, width=1.2)
    for y in (top + 22, 214, 446):
        out += cel(smooth([(x - 6, y, True), (x + 6, y, True), (x + 6, y + 9, True), (x - 6, y + 9, True)]), o["plate"], o["plate_sh"],
                   o["plate_lt"], [line([(x - 6, y + 4.5), (x + 6, y + 4.5)], o["glow"], 1.0)], s=(2, -1))
    # the blade above the armillary
    blade = smooth([(x - 6.5, top - 20, True), (x - 3, top - 44), (x, top - 70, True), (x + 3, top - 44), (x + 6.5, top - 20, True), (x, top - 14)])
    out += cel(blade, o["plate"], o["plate_sh"], o["plate_lt"], [line([(x, top - 22), (x, top - 62)], o["glow"], 1.2)], s=(3, -1))
    cx, cy, r = x, top, 20.0

    def ring(rx, ry, rot, col, w):
        return [ellipse(cx, cy, rx, ry, "none", K.INK, w + 2.4, rot), ellipse(cx, cy, rx, ry, "none", col, w, rot)]

    out.append(K.glow(cx, cy, r + 6, r + 6, o["glow"], 0.2))
    out += ring(r * 0.36, r, 0, o["plate_sh"], 2.2)
    out += ring(r, r * 0.4, -24, o["glow"], 1.8)
    out.append(ellipse(cx, cy, 5.2, 5.2, o["glow_hi"], K.INK, 1.6))
    out += ring(r, r, 0, o["plate"], 3.0)
    out += ring(r, r * 0.34, 30, o["glow"], 1.6)
    out += ring(r * 0.3, r, 18, o["plate"], 2.0)
    return out


def backpack_ring(o):
    """Prime: an armillary ring mounted on her back plate, tilted, its nodes lit."""
    if not o.get("tech"):
        return []
    cx, cy = 236.0, 214.0
    out = cel(smooth([(240, 214), (256, 210), (262, 232), (258, 262), (244, 264), (238, 240)]), o["plate_sh"], o["plate_dk"], o["plate"], s=(3, -2))
    for rx, ry, rot, col, w in ((24, 62, -16, o["plate"], 3.4), (60, 18, -16, o["glow"], 1.6)):
        out += [ellipse(cx, cy, rx, ry, "none", K.INK, w + 2.6, rot), ellipse(cx, cy, rx, ry, "none", col, w, rot)]
    for a in (-100, -20, 70, 160):
        t = math.radians(a - 16)
        out.append(ellipse(cx + math.cos(t) * 22, cy + math.sin(t) * 58, 2.6, 2.6, o["glow_hi"], K.INK, 1.0))
    return out


def staff(o):
    """The armillary staff: a bronze-shod pole with a celestial model on top."""
    if o.get("tech"):
        return tech_lance(o)
    x = STAFF_X
    out = cel(smooth([(x - 3.6, STAFF_TOP + 16, True), (x + 3.6, STAFF_TOP + 16, True), (x + 3.6, 498, True), (x - 3.6, 498, True)]),
              "#6a4628", "#452c18", "#8c6440", s=(2, 0), l=(1, 0))
    for y in (STAFF_TOP + 22, 214, 446):
        out += cel(smooth([(x - 5.5, y, True), (x + 5.5, y, True), (x + 5.5, y + 8, True), (x - 5.5, y + 8, True)]), o["br"], o["br_sh"],
                   o["br_lt"], s=(2, -1))
    cx, cy, r = x, STAFF_TOP, 20.0

    def ring(rx, ry, rot, col, w):
        return [ellipse(cx, cy, rx, ry, "none", K.INK, w + 2.4, rot), ellipse(cx, cy, rx, ry, "none", col, w, rot)]

    out += ring(r * 0.36, r, 0, o["br_sh"], 2.2)
    out += ring(r, r * 0.4, -24, o["br_sh"], 2.2)
    out.append(ellipse(cx, cy, 5.2, 5.2, o.get("glyph", "#f2d48a"), K.INK, 1.6))
    out += ring(r, r, 0, o["br"], 3.0)
    out += ring(r, r * 0.34, 30, o["br_lt"], 2.2)
    out += ring(r * 0.3, r, 18, o["br"], 2.0)
    out.append(ellipse(cx, cy - r - 4, 3.4, 3.4, o["br_lt"], K.INK, 1.4))
    return out


def halo(o):
    if not o["halo"]:
        return []
    c = BASE_J["head"]
    cx, cy, r = c[0] - 8, c[1] - 6, 52.0
    out = [ellipse(cx, cy, r, r, "none", K.INK, 7.4), ellipse(cx, cy, r, r, "none", o["br"], 4.4),
           ellipse(cx, cy, r - 9, r - 9, "none", K.INK, 3.6), ellipse(cx, cy, r - 9, r - 9, "none", o["br_sh"], 1.6)]
    for i in range(24):
        a = math.radians(i * 15)
        L = 6 if i % 3 == 0 else 3
        out.append(line([(cx + math.cos(a) * (r - 2), cy + math.sin(a) * (r - 2)), (cx + math.cos(a) * (r - 2 - L), cy + math.sin(a) * (r - 2 - L))],
                        o["br_sh"], 1.2))
    for a, L in ((-60, 30), (200, 34), (120, 26)):  # the rete's star pointers
        t = math.radians(a)
        p = (cx + math.cos(t) * (r - 10), cy + math.sin(t) * (r - 10))
        q = (cx + math.cos(t) * (r - 10 - L), cy + math.sin(t) * (r - 10 - L))
        out.append(line([p, q], K.INK, 3.6))
        out.append(line([p, q], o["br"], 1.6))
        out.append(ellipse(p[0], p[1], 2.4, 2.4, o["glyph"], K.INK, 1.0))
    return out


def foot(o, J, side):
    """A bare foot in a sandal, flat on the ground (Prime: a plated sabaton)."""
    near = side == "near"
    if o.get("tech"):
        x, _ = J[f"{side}_ankle"]
        g = GROUND_Y
        pc = (o["plate"], o["plate_sh"], o["plate_lt"]) if near else (o["plate_sh"], o["plate_dk"], None)
        sh = smooth([(x - 11, g - 18), (x + 6, g - 17), (x + 18, g - 9), (x + 30, g - 5), (x + 32, g, True), (x - 13, g, True), (x - 14, g - 9)])
        out = cel(sh, *pc, [line([(x + 4, g - 15), (x + 14, g - 8)], o["plate_dk"], 0.9)], s=(3, -2), l=(1.5, -1))
        out += cel(smooth([(x - 14, g - 3, True), (x + 33, g - 3, True), (x + 33, g + 1, True), (x - 14, g + 1, True)]), o["sandal"],
                   o["sandal_sh"], None, width=1.4)
        out.append(line([(x - 12, g - 4.5), (x + 30, g - 4.5)], o["glow"], 1.0))
        return out
    x, _ = J[f"{side}_ankle"]
    g = GROUND_Y
    sk = (o["skin"], o["skin_sh"], o["skin_lt"]) if near else (o["skin_sh"], o["skin_sh"], None)
    sh = smooth([(x - 10, g - 14), (x + 6, g - 14), (x + 18, g - 8), (x + 28, g - 5), (x + 30, g, True), (x - 12, g, True), (x - 13, g - 8)])
    out = cel(sh, *sk, [line([(x + 18, g - 2), (x + 20, g - 6)], o["skin_sh"], 0.9)], s=(3, -2), l=(1.5, -1))
    sole = smooth([(x - 13, g - 3, True), (x + 31, g - 3, True), (x + 31, g + 1, True), (x - 13, g + 1, True)])
    out += cel(sole, o["sandal"], o["sandal_sh"], None, width=1.4)
    for a, b in (((x - 2, g - 13), (x + 14, g - 4)), ((x + 6, g - 13), (x - 6, g - 4)), ((x - 9, g - 16), (x + 4, g - 12))):
        out.append(line([a, b], K.INK, 3.6))
        out.append(line([a, b], o["sandal"], 2.0))
    return out


def shin(o, J, side):
    """The shin under the chiton (it shows below the hem when the knee lifts)."""
    near = side == "near"
    kn, an = J[f"{side}_knee"], J[f"{side}_ankle"]
    base, sh = (o["skin"], o["skin_sh"]) if near else (o["skin_sh"], o["skin_sh"])
    out = K.limb(kn, (an[0], an[1] - 4), 8.6, 6.4, base, sh, o["skin_lt"] if near else None)
    if o.get("tech"):  # a greave over the shin
        pc = (o["plate"], o["plate_sh"], o["plate_lt"]) if near else (o["plate_sh"], o["plate_dk"], None)
        out += cel(capsule(lerp(kn, an, 0.2), (an[0], an[1] - 6), 9.4, 7.4), *pc, [line([lerp(kn, an, 0.3), lerp(kn, an, 0.85)], o["glow"], 1.0)],
                   s=(3, -2))
    return out


def thigh(o, J, side):
    """The thigh, in the chiton's cloth (it shows only when a panel swings off it)."""
    near = side == "near"
    base = o["dress"] if near else o["dress_sh"]
    return cel(capsule(J[f"{side}_hip"], J[f"{side}_knee"], 13.0, 10.0), base, o["dress_sh"], None, s=(5, -3))


def far_upper(o, J):
    return cel(capsule(J["far_shoulder"], J["far_elbow"], 9.5, 7.5), o["dress_sh"], o["dress_sh"])


def far_lower(o, J):
    return cel(capsule(J["far_elbow"], J["far_wrist"], 7.0, 5.6), o["skin_sh"], o["skin_sh"])


def far_hand(o, J):
    el, wr = J["far_elbow"], J["far_wrist"]
    deg = K.deg_of(el, wr)
    p = o["far_prop"]
    out = []
    if p == "scroll":
        sx, sy = wr[0] - 4, wr[1] + 8
        out += cel(smooth([(sx - 30, sy - 7, True), (sx + 22, sy - 11, True), (sx + 23, sy + 1, True), (sx - 29, sy + 5, True)]), "#e6d6aa",
                   "#b8a478", None, [line([(sx - 14, sy - 6), (sx + 10, sy - 8)], "#8a7650", 0.9)], s=(2, -2))
        for e in ((sx - 30, sy - 1), (sx + 23, sy - 5)):
            out.append(ellipse(e[0], e[1], 3.4, 6.8, o["br"], K.INK, 1.2, rot=-5))
        out += K.hand_fist(wr, deg, o["skin_sh"], o["skin_sh"], k=0.92)
    elif p == "codex":
        out += K.hand_open(wr, deg - 40, o["skin_sh"], o["skin_sh"], k=0.92)
    else:
        out += K.hand_open(wr, deg - 10, o["skin_sh"], o["skin_sh"], k=0.92)
    return out


#: The chiton, cut in three: the bodice to the hips, and the skirt's back and
#: front panels, which overlap down the middle where a fold falls anyway.
BODICE = [(256, 210), (276, 204), (292, 212), (300, 228), (302, 244), (296, 256), (294, 270), (300, 300), (304, 334, True), (246, 338, True),
          (248, 290), (246, 248), (248, 224)]
SKIRT_B = [(250, 312), (282, 312), (288, 400), (290, 488, True), (240, 488, True), (238, 420), (244, 340)]
SKIRT_F = [(266, 312), (298, 308), (310, 360), (318, 420), (322, 486, True), (268, 488, True), (266, 420), (264, 360)]


def bodice(o):
    neck = (282, 200) if o.get("aged") else (277, 196)
    out = cel(capsule(neck, (277, 216), 8.6, 10.0), o["skin"], o["skin_sh"], None,
              [line([(neck[0] + 5, neck[1] + 6), (neck[0] + 2, neck[1] + 14)], o["skin_sh"], 0.9)] if o.get("aged") else [], s=(5, -2))
    items = [line([(300, 228), (296, 248)], o["dress_sh"], 1.2), line([(262, 300), (258, 334)], o["dress_sh"], 1.4),
             line([(286, 300), (290, 334)], o["dress_sh"], 1.4)]
    out += cel(smooth(BODICE), o["dress"], o["dress_sh"], o["dress_lt"], items, s=(12, -3), l=(3, -1))
    # the girdle under the bust
    out += cel(smooth([(247, 254, True), (296, 252, True), (295, 262, True), (247, 264, True)]), o["trim"], o["br_sh"], None, s=(2, -2))
    if o.get("tech"):
        out += tech_plate(o)
    if o["armor"]:
        for i in range(4):  # bronze lamellar panels over the chest and down the hips
            y = 266 + i * 15
            sil_p = smooth([(250 - i * 0.6, y, True), (298 + i * 1.5, y - 1, True), (300 + i * 1.8, y + 15, True), (250 - i * 0.8, y + 16, True)])
            out += cel(sil_p, o["br"], o["br_sh"], o["br_lt"], [line([(262, y + 2), (262, y + 14)], o["br_sh"], 1.0),
                                                                line([(276, y + 1), (276, y + 14)], o["br_sh"], 1.0),
                                                                line([(290, y + 1), (290, y + 14)], o["br_sh"], 1.0)], s=(3, -2))
        chest = smooth([(254, 214), (276, 208), (292, 214), (300, 230), (300, 246), (296, 254), (250, 256), (248, 232)])
        out += cel(chest, o["br"], o["br_sh"], o["br_lt"], [line([(256, 240), (296, 236)], o["br_sh"], 1.0)], s=(6, -3))
        out.append(ellipse(286, 230, 4.0, 4.0, o["glyph"], K.INK, 1.2))
    return out


def tech_plate(o):
    """Prime's breastplate over the chiton: a sleek plate from the collar to
    the girdle, a meander of light along its foot, the armillary ring at its
    heart, a gorget at the throat. A plain plate: no breasts moulded in it."""
    out = []
    plate = smooth([(254, 214), (272, 206), (290, 210), (300, 226), (302, 242), (298, 252, True), (250, 254, True), (246, 236), (248, 222)])
    out += cel(plate, o["plate"], o["plate_sh"], o["plate_lt"], [line([(268, 210), (264, 252)], o["plate_sh"], 1.0),
                                                              line([(296, 220), (300, 240)], o["plate_lt"], 1.6)], s=(8, -3), l=(2, -1))
    out += meander((251, 252), (297, 250), 6.0, o)
    gorget = smooth([(262, 206), (276, 199), (290, 203), (294, 211), (278, 210), (262, 214)])
    out += cel(gorget, o["plate_sh"], o["plate_dk"], o["plate"], s=(2, -1), width=1.6)
    cx, cy = 286.0, 232.0  # the chest ring: an armillary, lit
    out += [K.glow(cx, cy, 13, 13, o["glow"], 0.25), ellipse(cx, cy, 9, 9, o["plate_dk"], K.INK, 1.4),
            ellipse(cx, cy, 7, 7, "none", o["glow"], 1.4), ellipse(cx, cy, 7, 2.6, "none", o["glow_hi"], 1.0, rot=-24),
            ellipse(cx, cy, 2.6, 7, "none", o["glow"], 1.0, rot=14), ellipse(cx, cy, 1.8, 1.8, o["glow_hi"])]
    return out


def skirt_back(o):
    items = [line([(262, 330), (258, 400), (252, 486)], o["dress_sh"], 1.6), line([(276, 330), (274, 420), (276, 486)], o["dress_sh"], 1.4)]
    out = cel(smooth(SKIRT_B), o["dress_sh"], K.tone(o["dress_sh"], 0.88), None, items, s=(8, -3))
    if o.get("tech"):
        out += meander((242, 474), (290, 476), 7.0, o)
    return out


def skirt_front(o):
    items = [line([(286, 330), (290, 400), (292, 486)], o["dress_sh"], 1.6), line([(298, 320), (306, 400), (314, 486)], o["dress_sh"], 1.6),
             # the near knee pushing the cloth forward
             line([(300, 404), (312, 416), (316, 484)], o["dress_sh"], 1.6)]
    out = cel(smooth(SKIRT_F), o["dress"], o["dress_sh"], o["dress_lt"], items, s=(10, -3), l=(3, -1))
    if o.get("tech"):
        out += meander((268, 474), (321, 472), 7.0, o)
    return out


def wrap(o):
    """The outer garment: a himation (A, C) across the hips to the knee, or
    the midnight mantle (B) down the back."""
    if o["hood"]:
        sil = smooth([(254, 206), (274, 206), (282, 220), (270, 246), (264, 300), (266, 360), (262, 446, True), (226, 452, True),
                      (226, 390), (232, 300), (238, 240)])
        items = [line([(282, 222), (268, 250), (262, 300), (264, 360), (260, 446)], o["trim"], 3.0),
                 line([(244, 250), (236, 440)], o["wrap_sh"], 1.6),
                 # faint copied diagrams on the cloth: the palimpsest
                 path(smooth([(238, 330), (252, 318), (258, 336), (246, 350)], closed=True), "none", o["wrap_lt"], 1.0),
                 line([(234, 380), (258, 372), (256, 404)], o["wrap_lt"], 1.0)]
        return cel(sil, o["wrap"], o["wrap_sh"], o["wrap_lt"], items, s=(10, -3))
    sil = smooth([(244, 262), (262, 270), (286, 282), (302, 300), (312, 332), (318, 372), (316, 404, True), (290, 396), (262, 410),
                  (240, 418, True), (238, 360), (240, 300)])
    items = [line([(250, 290), (290, 312), (310, 350)], o["wrap_sh"], 2.0), line([(246, 330), (284, 344), (312, 380)], o["wrap_sh"], 2.0),
             line([(244, 372), (276, 380), (304, 396)], o["wrap_sh"], 1.6),
             line([(244, 264), (286, 284), (302, 300)], o["wrap_lt"], 2.0)]
    if o.get("tech"):  # the himation's border: a meander of light
        edge = [(242, 412), (262, 404), (290, 390), (316, 398)]
        for a, b in zip(edge, edge[1:]):
            items += meander(a, b, 7.0, o, width=1.0)
    elif o["trim"]:
        items.append(line([(240, 416), (262, 408), (290, 394), (316, 402)], o["trim"], 3.2))
    return cel(sil, o["wrap"], o["wrap_sh"], o["wrap_lt"], items, s=(10, -3))


def far_drape(o):
    """The himation's end over the far shoulder, hanging down the back."""
    if o["hood"]:
        return []
    sil = smooth([(252, 210), (270, 206), (274, 220), (258, 236), (248, 290), (244, 350, True), (232, 340), (234, 280), (242, 230)])
    return cel(sil, o["wrap_sh"], o["wrap_sh"], None, [line([(256, 230), (242, 330)], K.tone(o["wrap_sh"], 0.8), 1.4)], s=(4, -2))


#: An older woman's profile: SKULL_F with a fuller, longer nose and the
#: mouth a little sunken under it.
SKULL_AGED = [(-18, 20), (-29, 5), (-31, -13), (-24, -30), (-7, -39), (10, -38), (21, -30), (25.5, -18), (26.4, -10, True),
              (25.4, -5.5), (28.5, 0), (34.2, 9.6, True), (29.2, 12.2), (28.4, 15), (29.6, 17.4), (27.6, 19.8, True), (29.4, 22.6),
              (27.2, 26), (28.2, 30), (24, 34.5), (13, 35), (2, 29), (-7, 21)]


def head_at(o):
    return _J(o)["head"]


def aged_lines(o, c, k):
    """Lines of age over the face: the brow, the crow's feet, the fold from
    nose to mouth, under the eye, the jowl."""
    sh = K.tone(o["skin_sh"], 0.82)
    return [line(hd(c, k, [(4, -24), (16, -25)]), sh, 1.1), line(hd(c, k, [(6, -20), (15, -21)]), sh, 1.0),
            line(hd(c, k, [(10.5, -8), (12.5, -5.5)]), sh, 1.1), line(hd(c, k, [(11, -4), (13.5, -3)]), sh, 1.0),
            line(hd(c, k, [(13.5, -1.6), (20, -0.8)]), sh, 1.2),
            line(hd(c, k, [(26, 12), (23.2, 17), (23.6, 22)]), sh, 1.4),
            line(hd(c, k, [(24.5, 23.5), (22.8, 27)]), sh, 1.1),
            line(hd(c, k, [(6, 24), (13, 30), (20, 33)]), sh, 1.3),
            line(hd(c, k, [(2, 8), (6, 16)]), sh, 1.0)]


def head(o):
    c, k = head_at(o), 1.0
    out = []
    kind = o["hair_kind"]
    hair, hl = o["hair"], o["hair_lt"]
    if kind == "loose":  # long loose waves down the back
        back = smooth([(c[0] - 22, c[1] - 30), (c[0] - 38, c[1] - 10), (c[0] - 42, c[1] + 30), (c[0] - 46, c[1] + 80), (c[0] - 40, c[1] + 120, True),
                       (c[0] - 32, c[1] + 104), (c[0] - 26, c[1] + 116, True), (c[0] - 22, c[1] + 70), (c[0] - 18, c[1] + 30), (c[0] - 10, c[1] + 6)])
        out += cel(back, hair, None, hl, [line([(c[0] - 34, c[1] + 10), (c[0] - 38, c[1] + 70), (c[0] - 34, c[1] + 104)], hl, 1.4),
                                          line([(c[0] - 26, c[1] + 20), (c[0] - 28, c[1] + 80)], "#3e1e12", 1.4)], s=(0, 0), l=(3, 0))
    if o["hood"]:  # the hood behind the head
        hood_back = smooth([(c[0] + 6, c[1] - 44), (c[0] - 22, c[1] - 44), (c[0] - 42, c[1] - 22), (c[0] - 46, c[1] + 16), (c[0] - 40, c[1] + 48),
                            (c[0] - 22, c[1] + 54), (c[0] - 10, c[1] + 40)])
        out += cel(hood_back, o["wrap_sh"], o["wrap_sh"], None)
    if kind == "crown":  # a low silver knot at the back
        knot = smooth([(c[0] - 30, c[1] - 2), (c[0] - 44, c[1] + 2), (c[0] - 46, c[1] + 16), (c[0] - 36, c[1] + 24), (c[0] - 26, c[1] + 18)])
        out += cel(knot, hair, o["hair_sh"], hl, [line([(c[0] - 42, c[1] + 6), (c[0] - 32, c[1] + 18)], o["hair_sh"], 1.2)], s=(2, -1), l=(1, 1))
    if o.get("aged"):
        skull = smooth(hd(c, k, SKULL_AGED))
        out += cel(skull, o["skin"], o["skin_sh"], o["skin_lt"], K.face(c, k, o["skin_sh"], o["skin_lt"]) + aged_lines(o, c, k),
                   s=(6, -4), l=(2.6, -2))
        out += K.features(c, k, o["skin"], o["skin_sh"], female=True, brow=o["hair_sh"], lips=o["lips"], stern=0.5)
    else:
        out += cel(K.skull(c, k, True), o["skin"], o["skin_sh"], o["skin_lt"], K.face(c, k, o["skin_sh"], o["skin_lt"]), s=(6, -4), l=(2.6, -2))
        out += K.features(c, k, o["skin"], o["skin_sh"], female=True, brow=hair, lips=o["lips"], stern=0.2)
    # hair over the crown: parted, drawn back
    cap = smooth([(c[0] - 33, c[1] + 8), (c[0] - 34, c[1] - 16), (c[0] - 22, c[1] - 35), (c[0] - 2, c[1] - 42), (c[0] + 16, c[1] - 37),
                  (c[0] + 25, c[1] - 24), (c[0] + 24, c[1] - 17, True), (c[0] + 14, c[1] - 24), (c[0] + 2, c[1] - 22), (c[0] - 6, c[1] - 14),
                  (c[0] - 9, c[1] - 2), (c[0] - 14, c[1] + 8), (c[0] - 22, c[1] + 18)])
    waves = [line([(c[0] + 20, c[1] - 30), (c[0] + 2, c[1] - 34), (c[0] - 18, c[1] - 26), (c[0] - 30, c[1] - 8)], hl, 1.4),
             line([(c[0] + 14, c[1] - 24), (c[0] - 4, c[1] - 26), (c[0] - 20, c[1] - 14)], K.tone(hair, 0.6), 1.2)]
    if kind == "crown":
        waves = [line([(c[0] + 18, c[1] - 30), (c[0] + 2, c[1] - 35), (c[0] - 18, c[1] - 27), (c[0] - 30, c[1] - 10)], o["hair_sh"], 1.0),
                 line([(c[0] + 12, c[1] - 24), (c[0] - 4, c[1] - 27), (c[0] - 22, c[1] - 16), (c[0] - 28, c[1])], o["hair_sh"], 1.0),
                 line([(c[0] + 6, c[1] - 18), (c[0] - 8, c[1] - 19), (c[0] - 20, c[1] - 6)], o["hair_sh"], 0.9)]
        out += cel(cap, hair, o["hair_sh"], hl, waves, s=(2, -1), l=(1.5, 1.5))
    elif kind != "veiled":
        out += cel(cap, hair, None, hl, waves, s=(0, 0), l=(2, 2))
    if kind == "knot":  # a knot of hair low at the back, bound by a fillet
        knot = smooth([(c[0] - 30, c[1] - 6), (c[0] - 46, c[1] - 4), (c[0] - 50, c[1] + 12), (c[0] - 40, c[1] + 22), (c[0] - 28, c[1] + 16)])
        out += cel(knot, hair, None, hl, [line([(c[0] - 46, c[1] + 2), (c[0] - 34, c[1] + 16)], hl, 1.4),
                                          line([(c[0] - 44, c[1] + 12), (c[0] - 32, c[1] + 4)], K.tone(hair, 0.6), 1.2)], s=(0, 0), l=(2, 2))
        fillet = [(c[0] + 20, c[1] - 30), (c[0] - 6, c[1] - 30), (c[0] - 28, c[1] - 12), (c[0] - 34, c[1] + 2)]
        out.append(line(fillet, K.INK, 4.4))
        out.append(line(fillet, o["br"], 2.4))
    if kind == "crown":  # a braid laid over the crown like a diadem, a lit circlet in front of it
        braid = [(c[0] + 14, c[1] - 34), (c[0] + 2, c[1] - 40), (c[0] - 12, c[1] - 39), (c[0] - 24, c[1] - 31), (c[0] - 31, c[1] - 18)]
        for a, b in zip(braid, braid[1:]):
            m = lerp(a, b, 0.5)
            out += cel(K.capsule(lerp(a, m, -0.25), lerp(b, m, -0.25), 3.6, 3.6), hair, o["hair_sh"], hl, s=(1.2, -0.8), width=1.1)
            out.append(line([lerp(a, b, 0.3), lerp(a, b, 0.55)], o["hair_sh"], 0.8))
        circ = [(c[0] + 21, c[1] - 26), (c[0] + 6, c[1] - 31), (c[0] - 10, c[1] - 29)]
        out.append(line(circ, K.INK, 3.6))
        out.append(line(circ, o["glow"], 1.6))
        out.append(ellipse(c[0] + 20, c[1] - 26.5, 1.8, 1.8, o["glow_hi"], K.INK, 0.8))
    if kind == "loose":
        band = [(c[0] + 18, c[1] - 30), (c[0] - 4, c[1] - 32), (c[0] - 26, c[1] - 18)]
        out.append(line(band, K.INK, 3.6))
        out.append(line(band, o["trim"], 1.8))
    if kind == "veiled":
        # hair shows at the brow; the hood's rim frames the face
        out += cel(smooth([(c[0] - 4, c[1] - 30), (c[0] + 14, c[1] - 34), (c[0] + 24, c[1] - 24), (c[0] + 23, c[1] - 18, True), (c[0] + 10, c[1] - 24),
                           (c[0] - 4, c[1] - 20)]), hair, None, hl, s=(0, 0), l=(1.5, 1.5))
        hood = smooth([(c[0] + 18, c[1] - 30), (c[0] + 4, c[1] - 46), (c[0] - 20, c[1] - 48), (c[0] - 40, c[1] - 32), (c[0] - 46, c[1] + 2),
                       (c[0] - 42, c[1] + 34), (c[0] - 26, c[1] + 50), (c[0] - 10, c[1] + 50), (c[0] - 16, c[1] + 30), (c[0] - 20, c[1] + 6),
                       (c[0] - 14, c[1] - 18), (c[0] + 2, c[1] - 30), (c[0] + 14, c[1] - 28)])
        out += cel(hood, o["wrap"], o["wrap_sh"], o["wrap_lt"], [line([(c[0] + 16, c[1] - 30), (c[0] + 2, c[1] - 32), (c[0] - 14, c[1] - 20),
                                                                       (c[0] - 20, c[1] + 6), (c[0] - 14, c[1] + 40)], o["trim"], 2.6)],
                   s=(6, -2), l=(2, -2))
    out.append(ellipse(c[0] + 0.5, c[1] + 11, 1.8, 2.4, o["br_lt"], K.INK, 0.9))  # a small earring
    return out


def eyes(o, kind):
    return K.eye(head_at(o), 1.0, kind, o["skin_sh"], female=True, lashes=not o.get("aged"))


def mouth_open(o):
    return K.talk_mouth(head_at(o), 1.0, female=True)


def near_upper(o, J):
    sh, el = J["near_shoulder"], J["near_elbow"]
    if o.get("tech"):  # the chiton's sleeve, a layered pauldron over it
        out = cel(capsule(lerp(sh, el, 0.4), el, 7.4, 6.2), o["skin"], o["skin_sh"], o["skin_lt"], s=(4, -3))
        out += cel(capsule(sh, lerp(sh, el, 0.62), 11.0, 9.6), o["dress"], o["dress_sh"], o["dress_lt"], s=(5, -3))
        for j, (dy, k) in enumerate(((12, 0.85), (0, 1.0))):
            P = lambda dx, yy: (sh[0] + dx * k, sh[1] + yy * k + dy)  # noqa: E731
            pl = smooth([P(-15, -6), P(4, -12), P(17, 0), P(14, 14), P(-10, 15)])
            out += cel(pl, o["plate"], o["plate_sh"], o["plate_lt"], [line([P(-12, 9), P(13, 8)], o["glow"], 1.0)] if j else [], s=(4, -3))
        return out
    if o["armor"]:
        out = cel(capsule(sh, el, 10.5, 8.0), o["dress"], o["dress_sh"], o["dress_lt"], s=(5, -3))
        out += cel(smooth([(sh[0] - 14, sh[1] - 8), (sh[0] + 6, sh[1] - 12), (sh[0] + 16, sh[1] + 4), (sh[0] + 12, sh[1] + 20),
                           (sh[0] - 10, sh[1] + 22)]), o["br"], o["br_sh"], o["br_lt"],
                   [line([(sh[0] - 12, sh[1] + 8), (sh[0] + 14, sh[1] + 4)], o["br_sh"], 1.0)], s=(4, -3))
        return out
    # a short draped sleeve pinned along the upper arm
    out = cel(capsule(lerp(sh, el, 0.4), el, 7.8, 6.8), o["skin"], o["skin_sh"], o["skin_lt"], s=(4, -3))
    out += cel(capsule(sh, lerp(sh, el, 0.62), 11.5, 10.0), o["dress"], o["dress_sh"], o["dress_lt"],
               [ellipse(*lerp(sh, el, 0.18), 1.8, 1.8, o["br"]), ellipse(*lerp(sh, el, 0.42), 1.8, 1.8, o["br"])], s=(5, -3))
    return out


def near_lower(o, J):
    el, wr = J["near_elbow"], J["near_wrist"]
    out = K.limb(el, wr, 6.0, 4.6, o["skin"], o["skin_sh"], o["skin_lt"],
                 [line([lerp(el, wr, 0.2), lerp(el, wr, 0.5)], o["skin_sh"], 0.8)] if o.get("aged") else ())
    if o.get("tech"):  # a vambrace, a lit seam down it
        out += cel(capsule(lerp(el, wr, 0.3), lerp(el, wr, 0.86), 7.4, 6.2), o["plate"], o["plate_sh"], o["plate_lt"],
                   [line([lerp(el, wr, 0.36), lerp(el, wr, 0.8)], o["glow"], 1.0)], s=(3, -2))
    elif o["armor"]:
        out += cel(capsule(lerp(el, wr, 0.35), lerp(el, wr, 0.9), 7.4, 6.4), o["br"], o["br_sh"], o["br_lt"], s=(3, -2))
    elif not o.get("tech"):
        out += cel(capsule(lerp(el, wr, 0.7), lerp(el, wr, 0.82), 6.6, 6.0), o["br"], o["br_sh"], None, s=(2, -1), width=1.6)
    return out


def near_hand(o, J):
    out = K.hand_grip(BASE_J["grip"], 90.0, o["skin"], o["skin_sh"], o["skin_lt"], k=0.9, side=-1)
    if o.get("aged"):  # bony knuckles
        gx, gy = BASE_J["grip"]
        out += [ellipse(gx + 9.2, gy + y, 1.3, 1.0, o["skin_lt"], o["skin_sh"], 0.6) for y in (-4.5, 0.0, 4.5)]
    return out


def props_front(o):
    """The codex (C) or folio pages (B), drawn over the body."""
    out = []
    if o["far_prop"] == "codex":
        x, y = 228, 300
        book = smooth([(x, y, True), (x + 40, y - 6, True), (x + 44, y + 50, True), (x + 4, y + 56, True)])
        for dx, a in ((10, -10), (24, 6)):  # loose folios poking out of the top edge
            out += cel(smooth(xf((x + dx, y - 2), a - 90, [(0, -7, True), (16, -7, True), (16, 7, True), (0, 7, True)])), "#efe2bc",
                       "#c8b890", None, width=1.4)
        out += cel(book, "#7a3a26", "#552618", "#9a5034", [line([(x + 8, y), (x + 12, y + 54)], "#552618", 1.4),
                                                           path(smooth([(x + 16, y + 14, True), (x + 34, y + 11, True), (x + 36, y + 30, True),
                                                                        (x + 18, y + 33, True)]), "none", o["br"], 1.6),
                                                           ellipse(x + 26, y + 22, 4, 4, "none", o["br"], 1.2)], s=(4, -2))
    if o.get("tech"):
        # a plated belt over the drape at the waist, and a tasset on the hip
        belt = smooth([(244, 262, True), (298, 258, True), (300, 270, True), (244, 274, True)])
        out += cel(belt, o["plate_sh"], o["plate_dk"], o["plate"], s=(2, -1), width=1.6)
        out += meander((248, 270), (296, 266), 5.0, o, width=0.9)
        tasset = smooth([(270, 276), (296, 272), (304, 300), (300, 324, True), (276, 326), (266, 300)])
        out += cel(tasset, o["plate"], o["plate_sh"], o["plate_lt"], [line([(272, 300), (300, 296)], o["plate_sh"], 1.0),
                                                                    line([(280, 280), (284, 322)], o["glow"], 1.0)], s=(5, -3), l=(2, -1))
    if o["far_prop"] == "folio":
        for (x, y, a) in ((252, 262, 8), (262, 264, -6)):  # two loose leaves tucked in the girdle
            out += cel(smooth(xf((x, y), a + 90, [(0, -8, True), (30, -8, True), (30, 8, True), (18, 8, True), (14, 2), (8, 8, True), (0, 8, True)])),
                       "#e8dcb6", "#c0b088", None, [line(xf((x, y), a + 90, [(6, -4), (24, -4)]), "#8a7a58", 0.9)], width=1.4)
    return out


# ------------------------------------------------------------------- effects ---

def _astrolabe(o, c, r, turn):
    """A bronze astrolabe face-on: the mater's rim and ticks, the rete turned by ``turn``."""
    cx, cy = c
    out = [K.glow(cx, cy, r + 10, r + 10, o["glyph_fx"], 0.18),
           ellipse(cx, cy, r, r, "none", K.INK, 8.0), ellipse(cx, cy, r, r, "none", o["br"], 5.0),
           ellipse(cx, cy, r - 12, r - 12, "none", K.INK, 3.6), ellipse(cx, cy, r - 12, r - 12, "none", o["br_sh"], 1.6)]
    for i in range(36):
        a = math.radians(i * 10)
        L = 7 if i % 3 == 0 else 3.5
        out.append(line([(cx + math.cos(a) * (r - 2.5), cy + math.sin(a) * (r - 2.5)),
                         (cx + math.cos(a) * (r - 2.5 - L), cy + math.sin(a) * (r - 2.5 - L))], o["br_sh"], 1.1))
    # the rete: an off-centre ecliptic ring and star pointers
    ex, ey = cx + math.cos(math.radians(turn)) * 8, cy + math.sin(math.radians(turn)) * 8
    out += [ellipse(ex, ey, r * 0.52, r * 0.52, "none", K.INK, 4.4), ellipse(ex, ey, r * 0.52, r * 0.52, "none", o["br_lt"], 2.2)]
    for a, L in ((turn - 60, 0.62), (turn + 70, 0.7), (turn + 190, 0.55)):
        t = math.radians(a)
        p = (cx + math.cos(t) * r * L, cy + math.sin(t) * r * L)
        out += [line([(cx, cy), p], K.INK, 3.6), line([(cx, cy), p], o["br"], 1.6), ellipse(p[0], p[1], 2.6, 2.6, o["glyph_fx"], K.INK, 1.0)]
    out.append(ellipse(cx, cy, 4.0, 4.0, o["glyph_hi"], K.INK, 1.2))
    return out


def astrolabe_fx(o, turn):
    """The astrolabe she turns before her in guard (``fx_astro_a``/``fx_astro_b``)."""
    return _astrolabe(o, (382.0, 262.0), 54.0, turn)


def conic_fx(o):
    """Conic sections traced ahead of her (``fx_conic``): an ellipse, a
    parabola and a hyperbola's branch, in starlight."""
    out = []
    c = (400.0, 250.0)
    for col, w in ((o["glyph_fx"], 2.4), (o["glyph_hi"], 0.9)):
        out.append(ellipse(c[0], c[1], 40, 18, "none", col, w, rot=-20))
    par = [(c[0] - 34 + t * t * 0.02, c[1] + t) for t in range(-60, 61, 10)]
    hyp = [(c[0] + 30 + math.cosh(u) * 10, c[1] + math.sinh(u) * 22) for u in [x / 5 for x in range(-8, 9)]]
    for pts in (par, hyp):
        out.append(line(pts, o["glyph_fx"], 2.0))
        out.append(line(pts, o["glyph_hi"], 0.8))
    for p in ((c[0], c[1]), (c[0] - 26, c[1] + 4), (c[0] + 40, c[1])):  # the foci
        out.append(ellipse(p[0], p[1], 2.6, 2.6, o["glyph_hi"], K.INK, 0.8))
    return out


def lance_fx(o):
    """The line the lance commits to (``fx_lance``, on the staff): a beam off
    the armillary, along the staff, tapering ahead."""
    x = STAFF_X
    y0 = STAFF_TOP - (70 if o.get("tech") else 24)  # off the blade's tip, or the armillary's
    beam = smooth([(x - 7, y0 + 6, True), (x, y0 - 96, True), (x + 7, y0 + 6, True)])
    return [K.glow(x, y0 - 40, 14, 56, o["glyph_fx"], 0.22), path(beam, o["glyph_fx"], extra=' fill-opacity="0.85"'),
            line([(x, y0), (x, y0 - 82)], o["glyph_hi"], 2.2)]


def orbit_fx(o, phase):
    """Nested epicycles round her (``fx_orbit_a``/``fx_orbit_b``): a deferent
    ellipse at her waist, epicycles riding it, small bodies on those."""
    c = (280.0, 300.0)
    out = []
    for col, w in ((K.INK, 3.2), (o["glyph_fx"], 1.6)):
        out.append(ellipse(c[0], c[1], 110, 30, "none", col, w))
    for k in range(3):
        a = math.radians(phase + k * 120)
        p = (c[0] + math.cos(a) * 110, c[1] + math.sin(a) * 30)
        out += [ellipse(p[0], p[1], 16, 16, "none", o["glyph_fx"], 1.4)]
        b = math.radians(phase * 2 + k * 90)
        q = (p[0] + math.cos(b) * 16, p[1] + math.sin(b) * 16)
        out += [ellipse(p[0], p[1], 4.2, 4.2, o["br_lt"], K.INK, 1.0), ellipse(q[0], q[1], 2.8, 2.8, o["glyph_hi"], K.INK, 0.9)]
    return out


def shadows_fx(o):
    """The other reconstructions of her (``fx_shadows``): three flat
    silhouettes behind her that never settle into one - a scribe, an
    astronomer, an armoured guardian."""
    out = []
    c = BASE_J["head"]
    for (dx, dy, col, k) in ((-74, -6, o["ghost_a"], 1.0), (66, -14, o["ghost_b"], 1.04), (-34, -26, o["ghost_c"], 0.96)):
        def m(pts):
            return [(CX + (q[0] - CX) * k + dx, GROUND_Y + (q[1] - GROUND_Y) * k + dy) + tuple(q[2:]) for q in pts]
        body = m(BODICE[:8] + [(318, 420), (322, 486, True), (240, 488, True), (238, 420), (244, 340)] + BODICE[10:])
        head_pts = m(K.hd(c, 1.0, K.SKULL_F))
        for pts in (body, head_pts):
            out.append(path(smooth(pts), col, col, 2.0, extra=' fill-opacity="0.32" stroke-opacity="0.7"'))
    return out


def _folio(o, c, deg, k=1.0):
    """One loose leaf with a piece of it missing."""
    pts = [(-14, -18, True), (14, -18, True), (14, 18, True), (2, 18, True), (-2, 8), (-8, 18, True), (-14, 18, True)]
    sil = smooth(xf(c, deg, [(p[0] * k, p[1] * k) + tuple(p[2:]) for p in pts]))
    lines = [line(xf(c, deg, [(-9 * k, y * k), (9 * k, y * k)]), "#8a7a58", 0.9) for y in (-11, -5, 1)]
    return cel(sil, "#efe2bc", "#c8b890", None, lines, s=(2, -1.5), width=1.4)


def folio_fx(o, spread):
    """Missing folios flung from her hand (``fx_folio_a`` close, ``fx_folio_b``
    scattered); the gaps in them are what does the harm."""
    out = []
    if spread:
        for c, deg in (((356, 214), -30), ((400, 262), 18), ((372, 318), 40), ((430, 196), -8), ((372, 120), 12)):
            out += [K.glow(c[0], c[1], 22, 22, o["glyph_fx"], 0.16)] + _folio(o, c, deg)
    else:
        for c, deg in (((300, 250), -12), ((322, 230), 14), ((316, 276), 30)):
            out += _folio(o, c, deg, 0.9)
    return out


def reveal_fx(o):
    """The revelation (``fx_reveal``): the fragments aligned into one radiant
    model behind her - rings of a sphere, rays, and the stars on them."""
    cx, cy = 280.0, 190.0
    out = [K.glow(cx, cy, 120, 120, o["glyph_fx"], 0.16), K.glow(cx, cy, 80, 80, o["glyph_hi"], 0.18)]
    for i in range(16):
        a = math.radians(i * 22.5)
        L0, L1 = 82, 118 if i % 2 == 0 else 100
        out.append(line([(cx + math.cos(a) * L0, cy + math.sin(a) * L0), (cx + math.cos(a) * L1, cy + math.sin(a) * L1)], o["br_lt"], 2.2))
    for rx, ry, rot, col in ((92, 92, 0, o["br"]), (92, 30, -22, o["br_lt"]), (30, 92, 18, o["br"]), (70, 70, 0, o["glyph_fx"])):
        out += [ellipse(cx, cy, rx, ry, "none", K.INK, 4.6, rot), ellipse(cx, cy, rx, ry, "none", col, 2.4, rot)]
    for a in (20, 110, 200, 290):
        t = math.radians(a)
        out.append(ellipse(cx + math.cos(t) * 92, cy + math.sin(t) * 92, 4, 4, o["glyph_hi"], K.INK, 1.0))
    return out


# --------------------------------------------------------------------- parts ---

def layers(look: str = LOOK) -> List[Tuple[str, str, str, str, float, str]]:
    """The parts, in the order they are drawn: (group id, label, part, bone, z, opacity channel)."""
    o = LOOKS[look]
    fz = 16 if o["far_prop"] == "scroll" else 10
    return [
        ("fx-shadows", "FX - Shadows", "fx_shadows", "body", 1, "fx_shadows"),
        ("fx-reveal", "FX - Revelation", "fx_reveal", "body", 2, "fx_reveal"),
        ("backpack-ring", "Backpack Ring", "backpack_ring", "torso", 3, ""),
        ("halo", "Astrolabe Halo", "halo", "head", 5, ""),
        ("far-arm-upper", "Far Arm - Upper", "far_arm_u", "far_arm_u", fz, ""),
        ("far-arm-lower", "Far Arm - Lower", "far_arm_l", "far_arm_l", fz + 0.5, ""),
        ("far-hand", "Far Hand", "far_hand", "far_hand", fz + 1, ""),
        ("far-drape", "Drape", "far_drape", "torso", 15, ""),
        ("far-thigh", "Far Thigh", "far_leg_u", "far_leg_u", 17, ""),
        ("far-shin", "Far Shin", "far_leg_l", "far_leg_l", 18, ""),
        ("far-foot", "Far Foot", "far_foot", "far_foot", 19, ""),
        ("near-thigh", "Near Thigh", "near_leg_u", "near_leg_u", 20, ""),
        ("near-shin", "Near Shin", "near_leg_l", "near_leg_l", 21, ""),
        ("near-foot", "Near Foot", "near_foot", "near_foot", 22, ""),
        ("skirt-back", "Skirt - Back", "skirt_b", "skirt_b", 26, ""),
        ("skirt-front", "Skirt - Front", "skirt_f", "skirt_f", 27, ""),
        ("bodice", "Bodice", "torso", "torso", 30, ""),
        ("wrap", "Himation", "wrap", "torso", 40, ""),
        ("props", "Props", "props", "torso", 45, ""),
        ("head", "Head", "head", "head", 60, ""),
        ("eye-open", "Eye - Open", "eye_open", "head", 61, "eye_open"),
        ("eye-shut", "Eye - Shut", "eye_shut", "head", 61, "eye_shut"),
        ("eye-dead", "Eye - Dead", "eye_dead", "head", 61, "eye_dead"),
        ("mouth-open", "Mouth - Open", "mouth_open", "head", 61, "mouth_open"),
        ("staff", "Armillary Staff", "staff", "staff", 70, ""),
        ("fx-lance", "FX - Lance", "fx_lance", "staff", 71, "fx_lance"),
        ("near-arm-upper", "Near Arm - Upper", "near_arm_u", "near_arm_u", 80, ""),
        ("near-arm-lower", "Near Arm - Lower", "near_arm_l", "near_arm_l", 81, ""),
        ("near-hand", "Near Hand", "near_hand", "near_hand", 82, ""),
        ("fx-astro-a", "FX - Astrolabe A", "fx_astro_a", "body", 90, "fx_astro_a"),
        ("fx-astro-b", "FX - Astrolabe B", "fx_astro_b", "body", 90, "fx_astro_b"),
        ("fx-conic", "FX - Conics", "fx_conic", "body", 90, "fx_conic"),
        ("fx-orbit-a", "FX - Epicycles A", "fx_orbit_a", "body", 90, "fx_orbit_a"),
        ("fx-orbit-b", "FX - Epicycles B", "fx_orbit_b", "body", 90, "fx_orbit_b"),
        ("fx-folio-a", "FX - Folios Close", "fx_folio_a", "body", 90, "fx_folio_a"),
        ("fx-folio-b", "FX - Folios Flung", "fx_folio_b", "body", 90, "fx_folio_b"),
    ]


def drawn(o, J) -> Dict[str, list]:
    out = {"fx-shadows": shadows_fx(o), "fx-reveal": reveal_fx(o), "halo": halo(o), "backpack-ring": backpack_ring(o),
           "far-arm-upper": far_upper(o, J), "far-arm-lower": far_lower(o, J), "far-hand": far_hand(o, J),
           "far-drape": far_drape(o) + (wrap(o) if o["hood"] else []),
           "skirt-back": skirt_back(o), "skirt-front": skirt_front(o), "bodice": bodice(o),
           "wrap": [] if o["hood"] else wrap(o), "props": props_front(o), "head": head(o),
           "eye-open": eyes(o, "open"), "eye-shut": eyes(o, "shut"), "eye-dead": eyes(o, "dead"), "mouth-open": mouth_open(o),
           "staff": staff(o), "fx-lance": lance_fx(o),
           "near-arm-upper": near_upper(o, J), "near-arm-lower": near_lower(o, J), "near-hand": near_hand(o, J),
           "fx-astro-a": astrolabe_fx(o, 0.0), "fx-astro-b": astrolabe_fx(o, 40.0), "fx-conic": conic_fx(o),
           "fx-orbit-a": orbit_fx(o, 30.0), "fx-orbit-b": orbit_fx(o, 90.0),
           "fx-folio-a": folio_fx(o, False), "fx-folio-b": folio_fx(o, True)}
    for side in ("far", "near"):
        out[f"{side}-thigh"] = thigh(o, J, side)
        out[f"{side}-shin"] = shin(o, J, side)
        out[f"{side}-foot"] = foot(o, J, side)
    return out


def svg_text(look: str = LOOK) -> str:
    o = LOOKS[look]
    K.begin(o["ink"], OW)
    parts = drawn(o, _J(o))
    for group, label, name, bone, z, channel in layers(look):
        K.part(group, label, name, bone, z, parts[group], channel, default_on=channel == "eye_open")
    note = ("Hypatia Prime's look (Jon, 2026-10-18: an old woman in future armour, the Alexandrian drape)" if look == LOOK
            else "KEPT, NOT CAST: a Hypatia Prime look Jon kept (2026-10-18), not registered in the cast")
    text = K.document(
        design=f"hypatia-prime-{look}", layer_id="hypatia-prime", label=VIEW,
        comment=[f"  <!-- {note}: side view facing right, the ground at y=500.",
                 "       Drawn by scripts/svg_art/hypatia_prime_art.py; each part turns about its bone's joint. -->"],
        joints=joints(look),
    )
    sx, sy = o["build"]
    if (sx, sy) != (1.0, 1.0):  # the look's build: the whole figure stretched about her feet
        t = f'translate({CX * (1 - sx):.2f},{GROUND_Y * (1 - sy):.2f}) scale({sx},{sy})'
        text = text.replace('<g id="hypatia-prime" ', f'<g id="hypatia-prime" transform="{t}" ', 1)
    return text


def main() -> None:
    if len(sys.argv) > 2 and sys.argv[1] == "--all":
        out = Path(sys.argv[2])
        out.mkdir(parents=True, exist_ok=True)
        for look in LOOKS:
            (out / f"hypatia_prime_{look}.svg").write_text(svg_text(look), encoding="utf8")
            print(out / f"hypatia_prime_{look}.svg")
        return
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".svg.tmp")
    tmp.write_text(svg_text(), encoding="utf8")
    tmp.replace(OUT)
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
