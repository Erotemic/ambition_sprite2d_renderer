#!/usr/bin/env python3
"""How the Creator's SVG was first drawn (reference, not authority).

    uv run python scripts/svg_art/creator_art.py            # his look (B)
    uv run python scripts/svg_art/creator_art.py --all DIR  # every look, to DIR

Writes ``data/characters/creator/creator.svg``; the SVG owns the art after
this has run once. ``joints(look)`` says where each part turns and ``LAYERS``
lists the parts; ``scripts/build_creator_rig.py`` reads both and authors the
rows.

Who he is (docs/storylines/cannon_expansions.md I2-I7): the player's maker, an
independent researcher in a basement lab, "not a grand genius - just some
guy", a man of about 50, 180 cm. Jon, 2026-10-18, of three redraws: "B for
creator ... keep the rest". B is ``mantle``: today's navy and violet as a
long navy coat, a violet scarf, silver swept-back hair and a trimmed beard, a
glowing pendant (today's chest sigil) and a tablet (today's pale card). A
(``labcoat``: lab coat, mug, ID badge) and C (``tinkerer``: cardigan, laptop,
headphones) are KEPT, NOT CAST: this script draws them (``--all``) on the
same parts and bones, and nothing registers them.

Human and not cutesy: adult proportions, a small eye.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Dict, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _cel_profile_kit as K  # noqa: E402
from _cel_profile_kit import capsule, cel, ellipse, hd, lerp, line, path, poly, smooth  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "ambition_sprite2d_renderer" / "data" / "characters" / "creator" / "creator.svg"
VIEW = "Creator - Side Right"
LOOK = "mantle"
OW = 1.5
#: The ground under his soles, in SVG units.
GROUND_Y = 500.0

LOOKS = {
    "labcoat": dict(
        label="A: basement researcher - lab coat, mug, badge",
        ink="#18161a", skin="#e0b090", skin_sh="#b4826a", skin_lt="#f2caa8",
        hair="#5a4436", hair_lt="#8a7262", grey="#a39a92", stubble="#6a5444",
        coat="#eceae4", coat_sh="#bdbab8", coat_lt="#ffffff", shirt="#3a6d78", shirt_sh="#284e57", shirt_lt="#5490a0",
        legs="#a8916c", legs_sh="#7c6a4c", legs_lt="#c4ae88", shoe="#4a4e58", shoe_sh="#30333b", shoe_lt="#6e7480", sole="#e8e4dc",
        glasses=("#3a3a40", 1.4), hair_kind="short", beard="stubble", prop="mug", build=(1.04, 1.0), belly=6,
        badge="#8a5ad8", badge_glow="#c9a8ff"),
    "mantle": dict(
        label="B: today's navy + violet - long coat, scarf, pendant, tablet",
        ink="#14141c", skin="#d29f82", skin_sh="#a5735c", skin_lt="#e8bea0",
        hair="#c9c6c2", hair_lt="#ecebe8", grey="#c9c6c2", stubble="#9c9894",
        coat="#2f3866", coat_sh="#1f2546", coat_lt="#46528a", shirt="#25222e", shirt_sh="#16141c", shirt_lt="#3a3646",
        scarf="#7b3fa0", scarf_sh="#55286f", scarf_lt="#9c5cc4",
        legs="#2a2c38", legs_sh="#1a1b24", legs_lt="#3c3f4e", shoe="#3a2a22", shoe_sh="#241913", shoe_lt="#5a4234", sole="#16100c",
        glasses=None, hair_kind="swept", beard="short", prop="tablet", build=(0.95, 1.03), belly=0,
        badge="#55d8e8", badge_glow="#c8f6ff"),
    "tinkerer": dict(
        label="C: late-night tinkerer - cardigan, laptop, headphones",
        ink="#1a1614", skin="#b47a58", skin_sh="#8a5a40", skin_lt="#cc9470",
        hair="#2c2420", hair_lt="#4c3e36", grey="#8c847c", stubble="#2c2420",
        coat="#b0843a", coat_sh="#83602a", coat_lt="#cca050", shirt="#5c4a7a", shirt_sh="#40335a", shirt_lt="#7a68a0",
        legs="#3c4f6e", legs_sh="#2a3850", legs_lt="#56709a", shoe="#d8d2c6", shoe_sh="#a8a296", shoe_lt="#f2eee6", sole="#5a5650",
        glasses=("#141214", 2.4), hair_kind="bald", beard="full", prop="laptop", build=(1.1, 0.98), belly=12,
        badge="#8a5ad8", badge_glow="#c9a8ff"),
}

#: Where the drawing's joints are, before a look's ``build`` stretch.
BASE_J = dict(head=(287.0, 160.0), neck=(280.0, 200.0), pelvis=(268.0, 326.0),
              near_shoulder=(279.0, 228.0), far_shoulder=(262.0, 224.0),
              near_elbow=(286.0, 292.0), near_wrist=(320.0, 306.0), far_elbow=(246.0, 288.0), far_wrist=(256.0, 330.0),
              near_hip=(276.0, 326.0), far_hip=(258.0, 324.0), near_knee=(284.0, 410.0), far_knee=(258.0, 410.0),
              near_ankle=(286.0, 482.0), far_ankle=(250.0, 482.0))

#: Each bone: (parent, the joint of the drawing it turns about). Parents first.
BONES = {
    "body": ("", "pelvis"),
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

CX = 270.0  # the build stretch is about (CX, GROUND_Y)


def stretch(o, p):
    sx, sy = o["build"]
    return (CX + (p[0] - CX) * sx, GROUND_Y + (p[1] - GROUND_Y) * sy)


def joints(look: str = LOOK) -> Dict[str, Tuple[float, float]]:
    """Where each joint is DRAWN (after the look's build stretch)."""
    o = LOOKS[look]
    J = dict(BASE_J)
    if o["prop"] == "laptop":  # the near arm hangs, the laptop at his side
        J.update(near_elbow=(286.0, 292.0), near_wrist=(294.0, 350.0))
    return {k: stretch(o, v) for k, v in J.items()}


def _J(look):
    o = LOOKS[look]
    J = dict(BASE_J)
    if o["prop"] == "laptop":
        J.update(near_elbow=(286.0, 292.0), near_wrist=(294.0, 350.0))
    return J


def shoe(o, an, near):
    b = (o["shoe"], o["shoe_sh"], o["shoe_lt"]) if near else (o["shoe_sh"], o["shoe_sh"], None)
    ax, ay = an
    g = GROUND_Y
    sil = smooth([(ax - 12, ay - 8), (ax + 8, ay - 9), (ax + 16, g - 13), (ax + 30, g - 9), (ax + 34, g - 3, True), (ax + 32, g, True),
                  (ax - 14, g, True), (ax - 15, g - 8)])
    items = [path(poly([(ax - 20, g - 4), (ax + 40, g - 4), (ax + 40, g + 4), (ax - 20, g + 4)]), o["sole"])]
    if o["prop"] == "laptop":  # sneakers: a stripe and laces
        items.append(line([(ax - 6, g - 9), (ax + 8, g - 5), (ax + 18, g - 10)], o["shirt"], 2.4))
    return cel(sil, *b, items, s=(4, -3), l=(2, -1.6))


def leg_colors(o, near):
    return (o["legs"], o["legs_sh"], o["legs_lt"]) if near else (o["legs_sh"], o["legs_sh"], None)


def thigh(o, J, side):
    base, sh, lt = leg_colors(o, side == "near")
    return cel(capsule(J[f"{side}_hip"], J[f"{side}_knee"], 15.5, 12.0), base, sh, lt, s=(7, -4))


def shin(o, J, side):
    base, sh, lt = leg_colors(o, side == "near")
    kn, an = J[f"{side}_knee"], J[f"{side}_ankle"]
    return cel(capsule(kn, (an[0], an[1] - 6), 12.0, 10.5), base, sh, lt, [line([(kn[0] + 4, kn[1] + 4), (an[0] + 4, an[1] - 10)], sh, 1.0)],
               s=(6, -3))


def far_upper(o, J):
    c = o["coat_sh"]
    return cel(capsule(J["far_shoulder"], J["far_elbow"], 12.0, 10.0), c, c)


def far_lower(o, J):
    c = o["coat_sh"]
    return cel(capsule(J["far_elbow"], J["far_wrist"], 10.0, 9.0), c, c)  # the hand is in the pocket


def torso(o):
    out = []
    b = o["belly"]
    out += cel(capsule((279, 190), (278, 216), 12.5, 14.0), o["skin"], o["skin_sh"], None, s=(7, -2))
    shirt = smooth([(256, 212), (276, 206), (292, 210), (304, 224), (310, 248), (310 + b * 0.6, 280), (309 + b, 306),
                    (302 + b * 0.6, 332), (252, 336), (244, 304), (242, 266), (244, 236)])
    out += cel(shirt, o["shirt"], o["shirt_sh"], o["shirt_lt"], [line([(296, 214), (306, 234)], o["shirt_sh"], 1.4)], s=(10, -4))
    out += cel(smooth([(250, 322, True), (305 + b * 0.6, 318, True), (305 + b * 0.6, 330, True), (250, 334, True)]),
               "#2a2220", "#18120f", None)
    return out


def coat(o):
    """The near side of the coat (or cardigan): over the shirt from the back
    to an open front edge."""
    p = o["prop"]
    b = o["belly"]
    if p == "laptop":  # a cardigan to the hip, pockets, buttons on its edge
        sil = smooth([(252, 212), (274, 206), (290, 214), (296, 240), (298 + b * 0.5, 280), (300 + b * 0.6, 346, True),
                      (242, 350, True), (238, 300), (240, 252), (244, 226)])
        items = [line([(290, 216), (297 + b * 0.5, 280), (298 + b * 0.6, 342)], o["coat_lt"], 2.4)]
        for y in (244, 268, 292, 316):
            items.append(ellipse(292 + b * 0.5 * (y - 220) / 80, y, 2.4, 2.4, o["coat_sh"], K.INK, 0.8))
        for y in range(216, 346, 8):  # the knit
            items.append(line([(244, y), (254, y + 2)], o["coat_sh"], 0.9))
        items.append(path(smooth([(256, 302, True), (282, 300, True), (283, 326, True), (257, 328, True)]), o["coat_sh"]))
        items.append(line([(256, 304), (282, 302)], o["coat_lt"], 1.4))
        return cel(sil, o["coat"], o["coat_sh"], o["coat_lt"], items, s=(10, -4))
    long_ = 440 if p == "tablet" else 410
    sil = smooth([(252, 212), (274, 204), (292, 212), (298, 240), (299 + b * 0.5, 280), (301 + b * 0.5, 330), (300, long_ - 10),
                  (298, long_, True), (232, long_ + 4, True), (232, 360), (236, 300), (238, 252), (244, 226)])
    items = [line([(292, 214), (298, 250), (301, 330), (298, long_ - 4)], o["coat_lt"], 2.2),
             line([(254, 340), (246, long_)], o["coat_sh"], 1.6),
             # the lapel and its notch
             path(smooth([(278, 206), (292, 212), (298, 244, True), (290, 236), (288, 226, True), (282, 224), (278, 214)]), o["coat_sh"]),
             # a hip pocket
             path(smooth([(252, 338, True), (284, 336, True), (285, 342, True), (253, 344, True)]), o["coat_sh"])]
    if p == "mug":  # the chest pocket and its pens
        items += [line([(276, 246), (276, 260)], "#2a4aa0", 3.0), line([(282, 246), (282, 258)], "#c0302a", 3.0),
                  path(smooth([(270, 256, True), (290, 255, True), (290, 259, True), (270, 260, True)]), o["coat_sh"])]
    return cel(sil, o["coat"], o["coat_sh"], o["coat_lt"], items, s=(12, -4), l=(3, -2))


def scarf(o):
    """Draped over the shoulders: the long end down the back, the short end
    down the front."""
    if "scarf" not in o:
        return []
    back = smooth([(254, 204), (272, 200), (276, 212), (260, 226), (250, 268), (246, 330), (238, 364, True), (232, 330), (236, 260),
                   (244, 222)])
    front = smooth([(272, 200), (286, 204), (290, 216), (288, 262), (290, 300, True), (278, 296), (278, 232), (270, 214)])
    out = cel(back, o["scarf"], o["scarf_sh"], o["scarf_lt"], [line([(246, 240), (240, 340)], o["scarf_sh"], 1.4)], s=(5, -2))
    out += cel(front, o["scarf"], o["scarf_sh"], o["scarf_lt"], [line([(282, 220), (284, 290)], o["scarf_sh"], 1.2)], s=(5, -2))
    for x in (280, 284, 288):  # fringe
        out.append(line([(x, 296 + (x - 280) * 0.3), (x, 304 + (x - 280) * 0.3)], o["scarf_sh"], 1.6))
    return out


def lanyard_or_pendant(o):
    out = []
    if o["prop"] == "tablet":  # a pendant on a cord: today's chest sigil
        out.append(line([(276, 210), (294, 240), (302, 252)], "#8c7a5a", 1.4))
        out += cel(smooth([(302, 244), (309, 252), (302, 261), (295, 252)]), "#3a3550", "#24203a", None, s=(2, -1))
        out.append(ellipse(302, 252.5, 2.8, 2.8, o["badge"]))
        out.append(ellipse(301.5, 251.8, 1.0, 1.0, o["badge_glow"]))
    elif o["prop"] == "mug":  # an ID badge clipped to the lapel, its lanyard round the neck
        out.append(line([(282, 208), (300, 236), (306, 254)], o["badge"], 2.2))
        bx, by = 300, 252
        out += cel(smooth([(bx, by, True), (bx + 15, by - 1, True), (bx + 16, by + 23, True), (bx + 1, by + 24, True)]), "#f4f2ee", "#c8c4bc",
                   None, [path(smooth([(bx + 3, by + 3, True), (bx + 13, by + 2.5, True), (bx + 13, by + 10, True), (bx + 3, by + 10.5, True)]),
                               o["badge"]),
                          ellipse(bx + 8, by + 6.5, 2.2, 2.2, o["badge_glow"]),
                          line([(bx + 3, by + 15), (bx + 13, by + 14.5)], "#8a8680", 1.2),
                          line([(bx + 3, by + 18.5), (bx + 10, by + 18)], "#8a8680", 1.2)], s=(2, -1))
    else:  # a badge clipped on the cardigan's pocket
        out += cel(smooth([(266, 288, True), (280, 287, True), (281, 304, True), (267, 305, True)]), "#f4f2ee", "#c8c4bc", None,
                   [path(smooth([(268.5, 290, True), (278.5, 289.5, True), (278.5, 296, True), (268.5, 296.5, True)]), o["badge"]),
                    ellipse(273.5, 293, 2.0, 2.0, o["badge_glow"])], s=(2, -1))
    return out


HEAD_K = 1.04


def head(o):
    c, k = BASE_J["head"], HEAD_K
    out = []
    kind = o["hair_kind"]
    if kind == "swept":  # silver hair swept back to the collar
        back = smooth([(c[0] - 20, c[1] - 30), (c[0] - 36, c[1] - 14), (c[0] - 39, c[1] + 12), (c[0] - 33, c[1] + 32, True),
                       (c[0] - 22, c[1] + 22), (c[0] - 12, c[1] + 6)])
        out += cel(back, o["hair"], "#a8a49e", o["hair_lt"], s=(3, -2))
    face_items = K.face(c, k, o["skin_sh"], o["skin_lt"])
    if o["beard"] == "stubble":
        face_items.append(path(smooth(hd(c, k, [(4, 4), (14, 12), (24, 17), (33, 22), (34, 42), (10, 44), (-6, 26)])), o["stubble"],
                               extra=' fill-opacity="0.3"'))
    out += cel(K.skull(c, k), o["skin"], o["skin_sh"], o["skin_lt"], face_items, s=(6, -4), l=(2.6, -2))
    out += K.features(c, k, o["skin"], o["skin_sh"], brow=o["grey"] if kind != "bald" else o["hair"], stern=-0.4,
                      mouth=o["beard"] == "stubble")
    # the laugh line and the bags of a man who works late
    out.append(line(hd(c, k, [(22, 13), (24, 19)]), o["skin_sh"], 1.1))
    out.append(line(hd(c, k, [(15, -2), (20, -1.4)]), o["skin_sh"], 0.9))
    if o["beard"] == "short":  # a trimmed grey beard on the jaw and chin
        bd = smooth(hd(c, k, [(2, 10), (10, 14), (20, 21), (28.5, 24.5), (30.5, 28), (31.5, 34), (27, 40), (15, 41), (3, 34),
                              (-4, 22), (-3, 14)]))
        out += cel(bd, o["hair"], "#a8a49e", o["hair_lt"], s=(3, -2))
        out += cel(smooth(hd(c, k, [(22, 16.5), (30, 15.5), (32, 19.5), (28, 21), (22, 20.5)])), o["hair"], "#a8a49e", None, s=(1, -1))
        out.append(line(hd(c, k, [(24, 25), (30, 24.6)]), K.INK, 1.3))
    if o["beard"] == "full":  # a close dark beard, the cheek bare above it
        bd = smooth(hd(c, k, [(0, 12), (8, 15), (18, 20), (24, 22), (29, 24), (32, 28), (32.5, 36), (27, 43), (14, 44), (2, 36),
                              (-5, 24), (-4, 15)]))
        out += cel(bd, o["hair"], None, o["hair_lt"], [line(hd(c, k, [(12, 26), (16, 38)]), o["hair_lt"], 1.0),
                                                      line(hd(c, k, [(20, 28), (24, 40)]), o["hair_lt"], 1.0)], s=(3, -2))
        out += cel(smooth(hd(c, k, [(21, 16), (30, 15.5), (32.5, 19.5), (28, 21.5), (21, 20.5)])), o["hair"], None, o["hair_lt"], s=(1, -1))
        out.append(path(smooth(hd(c, k, [(24, 23.4), (30, 23), (30.5, 25.2), (25, 25.6)])), "#b0645a"))
    if kind == "short":  # short, the line receding, grey at the temple
        cap = smooth(hd(c, k, [(-30, 10), (-34, -12), (-26, -32), (-8, -43), (8, -43), (18, -38), (21, -31, True), (10, -33),
                               (2, -30), (-4, -22), (-7, -12), (-9, -4, True), (-16, -2), (-20, 8), (-24, 18)]))
        out += cel(cap, o["hair"], "#3a2c22", o["hair_lt"], [path(smooth(hd(c, k, [(-8, -14), (-4, -24), (2, -28), (-2, -18), (-7, -8)])),
                                                                o["grey"]),
                                                           line(hd(c, k, [(-26, -20), (-10, -36), (10, -40)]), o["hair_lt"], 1.2)],
                   s=(3, -2), l=(2, 2))
    elif kind == "swept":
        cap = smooth(hd(c, k, [(-34, 4), (-34, -16), (-22, -36), (-2, -44), (16, -42), (26, -32), (20, -28, True), (8, -29), (-4, -24),
                               (-10, -14), (-12, -4, True), (-20, 4), (-26, 16)]))
        out += cel(cap, o["hair"], "#a8a49e", o["hair_lt"], [line(hd(c, k, [(16, -36), (-6, -36), (-26, -24)]), "#a8a49e", 1.2),
                                                          line(hd(c, k, [(10, -32), (-10, -28), (-28, -12)]), "#a8a49e", 1.2)],
                   s=(3, -2), l=(2, 2))
    else:  # bald crown, a short fringe round the back
        fr = smooth(hd(c, k, [(-28, 12), (-32, -6), (-29, -14), (-22, -10), (-14, -4), (-12, 2), (-17, 10), (-22, 17)]))
        out += cel(fr, o["grey"], None, None, [line(hd(c, k, [(-28, -6), (-18, -2)]), o["hair"], 1.0),
                                               line(hd(c, k, [(-28, 2), (-18, 6)]), o["hair"], 1.0)], s=(2, -2))
    if o["prop"] == "laptop":  # headphones round the neck
        band = [(c[0] - 14, c[1] + 46), (c[0] - 2, c[1] + 54), (c[0] + 14, c[1] + 53)]
        out.append(line(band, K.INK, 6.0))
        out.append(line(band, "#34343c", 3.4))
        out += cel(smooth([(c[0] + 6, c[1] + 44), (c[0] + 20, c[1] + 44), (c[0] + 22, c[1] + 60), (c[0] + 6, c[1] + 61)]), "#34343c",
                   "#1c1c22", "#54545e", [ellipse(c[0] + 14, c[1] + 52, 3.4, 4.4, "#1c1c22")], s=(3, -2))
    return out


def eyes(o, kind):
    c, k = BASE_J["head"], HEAD_K
    return K.eye(c, k, kind, o["skin_sh"])


def glasses(o):
    if not o["glasses"]:
        return []
    c, k = BASE_J["head"], HEAD_K
    g, gw = o["glasses"]
    ex, ey = 18.5, -6
    return [path(smooth(hd(c, k, [(ex - 6, ey - 4.5, True), (ex + 7, ey - 4.5, True), (ex + 7.5, ey + 3.5, True), (ex - 5, ey + 4.0, True)])),
                 "#cfe6ee", g, gw, extra=' fill-opacity="0.28"'),
            line(hd(c, k, [(ex - 6, ey - 2.5), (-5, -6), (-8, -4)]), g, gw)]


def mouth_open(o):
    """His mouth open on a word, through the beard."""
    c, k = BASE_J["head"], HEAD_K
    if o["beard"] == "stubble":
        return K.talk_mouth(c, k)
    return [path(smooth(hd(c, k, [(23.5, 24.6), (30.4, 24.0, True), (29.6, 27.6), (25.0, 28.2)])), "#3a1a1a", K.INK, 1.0)]


def mug(o, grip):
    gx, gy = grip
    body = smooth([(gx + 6, gy - 14, True), (gx + 26, gy - 14, True), (gx + 25, gy + 12, True), (gx + 7, gy + 12, True)])
    out = [line([(gx + 7, gy - 8), (gx - 2, gy - 6), (gx - 2, gy + 4), (gx + 7, gy + 6)], K.INK, 6.0),
           line([(gx + 7, gy - 8), (gx - 2, gy - 6), (gx - 2, gy + 4), (gx + 7, gy + 6)], "#d8d2c4", 3.0)]
    out += cel(body, "#e8e2d4", "#b8b0a0", "#ffffff", [path(smooth([(gx + 9, gy - 4, True), (gx + 23, gy - 4, True), (gx + 23, gy + 4, True),
                                                                   (gx + 9, gy + 4, True)]), o["badge"])], s=(5, -2))
    out += cel(smooth([(gx + 6, gy - 16, True), (gx + 26, gy - 16, True), (gx + 26, gy - 12, True), (gx + 6, gy - 12, True)]), "#5a3a26",
               None, None, width=1.6)
    return out


def tablet(o, grip):
    gx, gy = grip
    # held upright, tipped back, its screen toward the viewer's side
    pts = [(gx - 4, gy - 46, True), (gx + 20, gy - 52, True), (gx + 26, gy + 8, True), (gx + 2, gy + 14, True)]
    out = cel(smooth(pts), "#e8e6f0", "#b4b0c4", None, s=(3, -1))
    scr = smooth([(gx, gy - 41, True), (gx + 17, gy - 45, True), (gx + 22, gy + 3, True), (gx + 5, gy + 7, True)])
    out += cel(scr, "#2a3050", None, None, [line([(gx + 4, gy - 34), (gx + 15, gy - 36)], o["badge"], 1.6),
                                             line([(gx + 5, gy - 28), (gx + 13, gy - 30)], o["badge_glow"], 1.2),
                                             line([(gx + 6, gy - 22), (gx + 16, gy - 24)], o["badge_glow"], 1.2),
                                             path(smooth([(gx + 8, gy - 14), (gx + 14, gy - 16), (gx + 16, gy - 8), (gx + 10, gy - 6)]),
                                                  "none", o["badge"], 1.2)], width=1.2)
    return out


def laptop(o, wr):
    """A closed laptop carried by its edge at his side, the lid's stickers out."""
    wx, wy = wr
    slab = smooth([(wx - 40, wy - 4, True), (wx + 32, wy - 8, True), (wx + 34, wy + 44, True), (wx - 38, wy + 48, True)])
    return cel(slab, "#b8bec6", "#868c94", "#dde0e4",
               [ellipse(wx - 2, wy + 20, 6, 6, "#f2f2f2"),
                path(smooth([(wx - 30, wy + 6, True), (wx - 18, wy + 5, True), (wx - 17, wy + 16, True), (wx - 29, wy + 17, True)]), o["badge"]),
                path(smooth([(wx + 14, wy + 26), (wx + 24, wy + 24), (wx + 26, wy + 34), (wx + 15, wy + 36)]), "#e0b040"),
                path(smooth([(wx - 28, wy + 30), (wx - 16, wy + 28), (wx - 14, wy + 38), (wx - 26, wy + 40)]), "#d04a3a"),
                line([(wx + 8, wy - 2), (wx + 22, wy - 3)], "#868c94", 1.4)],
               s=(4, -2))


def near_upper(o, J):
    return cel(capsule(J["near_shoulder"], J["near_elbow"], 14.0, 11.5), o["coat"], o["coat_sh"], o["coat_lt"], s=(6, -3))


def near_lower(o, J):
    """The forearm, the sleeve over most of it (rolled back on a cardigan)."""
    el, wr = J["near_elbow"], J["near_wrist"]
    p = o["prop"]
    sleeve_end = lerp(el, wr, 0.72) if p != "laptop" else lerp(el, wr, 0.3)
    out = K.limb(el, wr, 9.5, 7.5, o["skin"], o["skin_sh"], o["skin_lt"],
                 items=[line([lerp(el, wr, 0.4), lerp(el, wr, 0.8)], o["stubble"], 0.8)] if p == "laptop" else ())
    out += cel(capsule(el, sleeve_end, 12.0, 11.0), o["coat"], o["coat_sh"], o["coat_lt"], s=(5, -3))
    if p == "laptop":  # the rolled cuff
        out += cel(capsule(lerp(el, wr, 0.24), lerp(el, wr, 0.36), 11.6, 11.2), o["coat_lt"], o["coat_sh"], None, s=(3, -2))
    return out


def near_hand(o, J):
    el, wr = J["near_elbow"], J["near_wrist"]
    deg = K.deg_of(el, wr)
    p = o["prop"]
    if p == "mug":
        return mug(o, (wr[0] + 8, wr[1] - 1)) + K.hand_fist((wr[0] - 2, wr[1]), deg - 20, o["skin"], o["skin_sh"], o["skin_lt"], k=1.05)
    if p == "tablet":
        out = K.hand_fist((wr[0] - 2, wr[1]), deg - 30, o["skin"], o["skin_sh"], o["skin_lt"], k=1.05)
        out += tablet(o, (wr[0] + 10, wr[1] - 4))
        out += cel(capsule((wr[0] + 8, wr[1] - 6), (wr[0] + 15, wr[1] - 12), 3.2, 2.6), o["skin"], o["skin_sh"], None, s=(1, -1))
        return out
    return laptop(o, (wr[0] + 4, wr[1] + 2)) + K.hand_fist((wr[0] - 1, wr[1]), deg - 10, o["skin"], o["skin_sh"], o["skin_lt"], k=1.05)


#: The parts, in the order they are drawn: (group id, label, part, bone, z, opacity channel).
LAYERS = [
    ("far-arm-upper", "Far Arm - Upper", "far_arm_u", "far_arm_u", 10, ""),
    ("far-arm-lower", "Far Arm - Lower", "far_arm_l", "far_arm_l", 11, ""),
    ("far-thigh", "Far Thigh", "far_leg_u", "far_leg_u", 20, ""),
    ("far-shin", "Far Shin", "far_leg_l", "far_leg_l", 21, ""),
    ("far-foot", "Far Foot", "far_foot", "far_foot", 22, ""),
    ("near-thigh", "Near Thigh", "near_leg_u", "near_leg_u", 30, ""),
    ("near-shin", "Near Shin", "near_leg_l", "near_leg_l", 31, ""),
    ("near-foot", "Near Foot", "near_foot", "near_foot", 32, ""),
    ("torso", "Torso, Coat and Scarf", "torso", "torso", 50, ""),
    ("head", "Head", "head", "head", 60, ""),
    ("eye-open", "Eye - Open", "eye_open", "head", 61, "eye_open"),
    ("eye-shut", "Eye - Shut", "eye_shut", "head", 61, "eye_shut"),
    ("mouth-open", "Mouth - Open", "mouth_open", "head", 61, "mouth_open"),
    ("glasses", "Glasses", "glasses", "head", 62, ""),
    ("near-arm-upper", "Near Arm - Upper", "near_arm_u", "near_arm_u", 80, ""),
    ("near-arm-lower", "Near Arm - Lower", "near_arm_l", "near_arm_l", 81, ""),
    ("near-hand", "Near Hand", "near_hand", "near_hand", 82, ""),
]


def drawn(o, J) -> Dict[str, list]:
    out = {"far-arm-upper": far_upper(o, J), "far-arm-lower": far_lower(o, J),
           "torso": torso(o) + coat(o) + scarf(o) + lanyard_or_pendant(o), "head": head(o),
           "eye-open": eyes(o, "open"), "eye-shut": eyes(o, "shut"), "mouth-open": mouth_open(o), "glasses": glasses(o),
           "near-arm-upper": near_upper(o, J), "near-arm-lower": near_lower(o, J), "near-hand": near_hand(o, J)}
    for side in ("far", "near"):
        out[f"{side}-thigh"] = thigh(o, J, side)
        out[f"{side}-shin"] = shin(o, J, side)
        out[f"{side}-foot"] = shoe(o, J[f"{side}_ankle"], side == "near")
    return out


def svg_text(look: str = LOOK) -> str:
    o = LOOKS[look]
    K.begin(o["ink"], OW)
    parts = drawn(o, _J(look))
    for group, label, name, bone, z, channel in LAYERS:
        K.part(group, label, name, bone, z, parts[group], channel, default_on=channel == "eye_open")
    note = ("the Creator's look (Jon chose B, 2026-10-18)" if look == LOOK
            else "KEPT, NOT CAST: a Creator look Jon kept (2026-10-18), not registered in the cast")
    text = K.document(
        design=f"creator-{look}", layer_id="creator", label=VIEW,
        comment=[f"  <!-- {note}: side view facing right, the ground at y=500.",
                 "       Drawn by scripts/svg_art/creator_art.py; each part turns about its bone's joint. -->"],
        joints=joints(look),
    )
    sx, sy = o["build"]
    if (sx, sy) != (1.0, 1.0):  # the look's build: the whole figure stretched about his feet
        t = f'translate({CX * (1 - sx):.2f},{GROUND_Y * (1 - sy):.2f}) scale({sx},{sy})'
        text = text.replace('<g id="creator" ', f'<g id="creator" transform="{t}" ', 1)
    return text


def main() -> None:
    if len(sys.argv) > 2 and sys.argv[1] == "--all":
        out = Path(sys.argv[2])
        out.mkdir(parents=True, exist_ok=True)
        for look in LOOKS:
            (out / f"creator_{look}.svg").write_text(svg_text(look), encoding="utf8")
            print(out / f"creator_{look}.svg")
        return
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".svg.tmp")
    tmp.write_text(svg_text(), encoding="utf8")
    tmp.replace(OUT)
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
