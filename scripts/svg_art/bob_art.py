#!/usr/bin/env python3
"""How Bob's fighter SVG was first drawn (reference, not authority).

``data/characters/bob/bob.svg`` owns the art and may have been edited since;
this script reproduces the drawing as it was first committed (less the rig
catalog ``scripts/build_bob_rig.py`` installs). Keep it as a worked example
for drawing a humanoid fighter with ``svgkit``: limbs as overlapping capsules,
hand / eye / mouth swap sets (``data-rig-opacity``), and props riding a hand.

    uv run python scripts/svg_art/bob_art.py OUT.svg

Drawn in SVG units: a 720x640 SVG, Bob about 375 units tall facing right,
the ground at y=569 and his centre line at x=340.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import svgkit as svg
from svgkit import capsule, clipped, ellipse, line, part, path, smooth

W, H = 720, 640
#: The figure is designed about x=256 on a ground at y=471, then shifted so
#: the drawing leaves room for a full overhead swing and a long forward reach.
DX, DY = 84.0, 98.0
INK = "#14110f"
OW = 1.6  # outline width (parts carry their own outlines)

C = dict(
    skin="#c08f6b",
    skin_light="#dcac87",
    skin_shadow="#8e6247",
    hair="#2b201b",
    hair_mid="#4a362c",
    hair_light="#6f5142",
    beard="#3c2a22",
    beard_dark="#251a15",
    shirt="#3a6589",
    shirt_dark="#24425e",
    shirt_light="#5f8db0",
    vest="#a7784a",
    vest_dark="#6c4b2c",
    vest_light="#c99e6c",
    hi_vis="#f0c23e",
    hi_vis_dark="#a47f1f",
    pants="#343a42",
    pants_dark="#1f242b",
    pants_light="#545c66",
    boot="#4a2f22",
    boot_light="#76503a",
    sole="#15100d",
    leather="#7a4a2a",
    leather_light="#a86c3c",
    leather_dark="#43281a",
    steel="#c3c9cf",
    steel_light="#eef2f5",
    steel_dark="#5d6670",
    brass="#d99c3e",
    brass_light="#f2c86e",
    glass="#9fe3e6",
    glass_dark="#3a8a92",
    device="#ddd6bf",
    device_dark="#7b745f",
    screen="#41c4ac",
    led="#e0533f",
    eye_white="#f5efe6",
    iris="#3d2a1e",
    mouth="#4d1d1a",
    tongue="#c46a62",
    tooth="#f6efe0",
    stripe="#24425e",
    tooth_ink="#14110f",
)
FAR = dict(skin="#a77a5b", shirt="#2c5070", shirt_light="#4b7799", pants="#272c33", pants_light="#3d444d",
           boot="#3a251b", boot_light="#5f4030")

J = dict(
    pelvis=(250.0, 302.0),
    neck=(258.0, 182.0),
    head_top=(266.0, 108.0),
    near_shoulder=(266.0, 196.0),
    near_elbow=(276.0, 258.0),
    near_wrist=(292.0, 308.0),
    far_shoulder=(246.0, 192.0),
    far_elbow=(238.0, 254.0),
    far_wrist=(252.0, 304.0),
    near_hip=(258.0, 304.0),
    near_knee=(272.0, 382.0),
    near_ankle=(266.0, 452.0),
    far_hip=(242.0, 300.0),
    far_knee=(246.0, 380.0),
    far_ankle=(226.0, 452.0),
)


def wide(points, k=1.16, cx=258.0):
    """Points widened about x=cx: Bob's trunk is drawn narrow, then broadened."""
    return [(cx + (q[0] - cx) * k,) + tuple(q[1:]) for q in points]


def ws(points, **kw):
    return smooth(wide(points), **kw)


def wl(points, stroke, sw):
    return line(wide(points), stroke, sw)


def outlined(sil, fill, items=(), cid=None, width=None):
    """A filled shape, its shading clipped inside, then its outline."""
    body = [path(sil, fill)]
    if items:
        body = clipped(cid, sil, [path(sil, fill)] + list(items))
    return body + [path(sil, "none", INK, width or 2 * OW)]


# ---- head ----------------------------------------------------------------------
SKULL = [(232, 150), (231, 128), (238, 110), (252, 99), (272, 97), (288, 104), (297, 117), (300, 128, True),
         (311, 141, True), (301, 147), (303, 156), (300, 170), (286, 178), (268, 178), (252, 170), (240, 162)]


#: The head is drawn 12% larger than its first sketch, about the neck.
HEAD_XF = (258.0, 182.0, 1.12)


def head_part():
    svg.transform(HEAD_XF)
    sil = smooth(SKULL)
    items = [
        # cheek light and the shadow under the jaw
        path(smooth([(276, 132), (294, 130), (300, 146), (284, 150)]), C["skin_light"]),
        path(smooth([(250, 160), (290, 168), (300, 186), (240, 186)]), C["skin_shadow"]),
        # beard: sideburn, jaw and chin, a mustache over the mouth
        path(smooth([(262, 130, True), (270, 136), (276, 150), (286, 154), (298, 150), (304, 156), (302, 170),
                     (290, 180), (266, 180), (252, 170), (256, 146)]), C["beard"]),
        path(smooth([(284, 151), (296, 148), (304, 152), (300, 156), (288, 156)]), C["beard_dark"]),
        line([(262, 158), (270, 168), (284, 172)], C["beard_dark"], 1.6),
        line([(276, 160), (286, 166)], C["beard_dark"], 1.4),
        # nose shading and nostril
        line([(300, 129), (309, 141), (302, 145)], C["skin_shadow"], 1.6),
        ellipse(301, 143, 2.0, 1.2, C["skin_shadow"]),
        # ear
        ellipse(258, 140, 6.5, 9.0, C["skin"], INK, 1.6),
        line([(257, 135), (260, 141), (257, 146)], C["skin_shadow"], 1.6),
    ]
    body = clipped("clip-head", sil, [path(sil, C["skin"])] + items)
    # hair: tousled crown and a longish back, over the skull outline
    hair = smooth([(230, 146), (227, 128), (231, 112), (240, 100), (252, 92, True), (262, 96), (272, 88, True),
                   (280, 95), (292, 92, True), (296, 102), (300, 112, True), (288, 112), (274, 110), (260, 115),
                   (252, 124), (248, 136), (246, 150, True), (238, 156)])
    body += [path(sil, "none", INK, 2 * OW), path(hair, C["hair"], INK, 2 * OW)]
    for pts in ([(236, 112), (248, 104), (262, 102)], [(232, 132), (238, 120), (250, 112)], [(276, 96), (288, 100)]):
        body.append(line(pts, C["hair_light"], 1.8))
    # brow
    body.append(path(smooth([(282, 122, True), (290, 118), (300, 120, True), (291, 124)]), C["hair"], INK, 1.0))
    # safety glasses pushed up on the forehead: the strap, then the lens and rim
    body.append(line([(232, 120), (252, 110), (276, 106), (296, 108)], C["leather_dark"], 4.0))
    body.append(path(smooth([(276, 102), (292, 100), (300, 108), (296, 116), (280, 116), (274, 110)]), C["glass"],
                     INK, 1.8))
    body.append(line([(280, 104), (290, 103)], "#ffffff", 1.6))
    body.append(line([(286, 114), (295, 112)], C["glass_dark"], 1.6))
    svg.transform(None)
    part("head", "Head", "head", "head", 60, body)


EYE = (290.0, 132.0)


def face_parts():
    svg.transform(HEAD_XF)
    x, y = EYE
    white = path(smooth([(x - 6, y), (x - 1, y - 4), (x + 5, y - 2), (x + 6, y + 1), (x + 1, y + 3), (x - 4, y + 2.5)]),
                 C["eye_white"], INK, 1.2)
    open_ = [white, ellipse(x + 2.2, y - 0.2, 2.6, 3.0, C["iris"]), ellipse(x + 1.5, y - 1.2, 0.8, 0.8, "#ffffff")]
    angry = [white, ellipse(x + 2.2, y + 0.4, 2.6, 2.6, C["iris"]),
             path(smooth([(x - 8, y - 7, True), (x + 8, y - 1, True), (x + 8, y - 6, True)]), C["hair"], INK, 1.0)]
    shut = [line([(x - 6, y + 0.5), (x, y + 2.6), (x + 6, y)], INK, 1.8)]
    dead = [line([(x - 4, y - 3), (x + 4, y + 3)], INK, 2.0), line([(x - 4, y + 3), (x + 4, y - 3)], INK, 2.0)]
    dizzy = [path(smooth([(x - 5, y), (x, y - 4), (x + 5, y), (x, y + 3.5), (x - 2, y), (x, y - 1.5), (x + 1.5, y)],
                         closed=False), "none", INK, 1.4)]
    part("eye-open", "Eye - Open", "eye_open", "head", 62, open_, ' data-rig-opacity="eye.open" data-rig-default="1"')
    part("eye-angry", "Eye - Angry", "eye_angry", "head", 62, angry, ' data-rig-opacity="eye.angry"')
    part("eye-shut", "Eye - Shut", "eye_shut", "head", 62, shut, ' data-rig-opacity="eye.shut"')
    part("eye-dead", "Eye - Dead", "eye_dead", "head", 62, dead, ' data-rig-opacity="eye.dead"')
    part("eye-dizzy", "Eye - Dizzy", "eye_dizzy", "head", 62, dizzy, ' data-rig-opacity="eye.dizzy"')
    mx, my = 297.0, 160.0
    closed = [line([(mx - 7, my), (mx, my + 1), (mx + 5, my - 1)], INK, 1.8)]
    smile = [line([(mx - 7, my - 1), (mx - 1, my + 2.5), (mx + 5, my - 1.5)], INK, 1.8)]
    open_m = [path(smooth([(mx - 8, my - 2), (mx + 6, my - 3), (mx + 4, my + 7), (mx - 4, my + 8)]), C["mouth"], INK, 1.4),
              path(smooth([(mx - 6, my - 1.5), (mx + 5, my - 2.5), (mx + 4, my + 0.5), (mx - 5, my + 1)]), C["tooth"]),
              path(smooth([(mx - 3, my + 6), (mx + 3, my + 5), (mx + 1, my + 7.5)]), C["tongue"])]
    grit = [path(smooth([(mx - 8, my - 2, True), (mx + 6, my - 3, True), (mx + 5, my + 3, True), (mx - 7, my + 3, True)]),
                 C["tooth"], INK, 1.4),
            line([(mx - 7, my + 0.3), (mx + 5.5, my)], INK, 1.0),
            line([(mx - 3, my - 2.4), (mx - 3, my + 3)], INK, 0.9), line([(mx + 1, my - 2.7), (mx + 1, my + 3)], INK, 0.9)]
    part("mouth-closed", "Mouth - Closed", "mouth_closed", "head", 63, closed,
         ' data-rig-opacity="mouth.closed" data-rig-default="1"')
    part("mouth-smile", "Mouth - Smile", "mouth_smile", "head", 63, smile, ' data-rig-opacity="mouth.smile"')
    part("mouth-open", "Mouth - Open", "mouth_open", "head", 63, open_m, ' data-rig-opacity="mouth.open"')
    part("mouth-grit", "Mouth - Grit", "mouth_grit", "head", 63, grit, ' data-rig-opacity="mouth.grit"')
    svg.transform(None)


# ---- torso, satchel, hips ------------------------------------------------------
TORSO = [(236, 194), (250, 184), (268, 184), (282, 194), (292, 214), (294, 246), (290, 276), (284, 304),
         (228, 304), (222, 274), (224, 236), (228, 208)]


def torso_parts():
    sil = ws(TORSO)
    vest_front = ws([(266, 196), (284, 200), (292, 218), (294, 248), (290, 278), (284, 304), (264, 304),
                    (270, 262), (272, 226)])
    vest_back = ws([(236, 196), (252, 192), (256, 230), (252, 270), (250, 304), (226, 304), (222, 270),
                   (224, 232), (228, 208)])
    items = [
        path(ws([(276, 196), (292, 212), (294, 250), (286, 250), (282, 214)]), C["shirt_light"]),
        path(vest_back, C["vest"], INK, 1.6),
        path(vest_front, C["vest"], INK, 1.6),
        # shading on the vest and the hi-vis band round it
        path(ws([(224, 236), (234, 238), (236, 300), (224, 300)]), C["vest_dark"]),
        path(ws([(282, 220), (292, 222), (292, 276), (284, 296)]), C["vest_light"]),
        path(ws([(220, 254, True), (296, 250, True), (296, 262, True), (220, 266, True)]), C["hi_vis"]),
        wl([(222, 260), (294, 256)], C["hi_vis_dark"], 1.2),
        # pocket flaps and a pen
        path(ws([(274, 274, True), (288, 272, True), (288, 282, True), (274, 284, True)]), C["vest_dark"], INK, 1.2),
        wl([(278, 268), (279, 280)], C["steel"], 2.2),
        path(ws([(276, 214, True), (288, 214, True), (288, 224, True), (276, 224, True)]), C["vest_dark"], INK, 1.2),
        # shirt collar at the neck
        path(ws([(252, 186, True), (266, 192), (272, 206, True), (262, 200), (254, 196)]), C["shirt_light"], INK, 1.2),
    ]
    body = [path(ws([(248, 168), (266, 170), (270, 196), (246, 196)]), C["skin"], INK, 2 * OW)]  # neck
    body += outlined(sil, C["shirt"], items, "clip-torso")
    # satchel strap across the chest, shoulder to back hip, and its buckle
    body.append(wl([(268, 190), (256, 230), (236, 276), (226, 290)], C["leather_dark"], 7.0))
    body.append(wl([(268, 190), (256, 230), (236, 276), (226, 290)], C["leather"], 4.6))
    body.append(path(ws([(252, 236, True), (262, 238, True), (259, 247, True), (249, 245, True)]), "none",
                     C["brass"], 2.2))
    part("torso", "Torso", "torso", "torso", 50, body)
    # the satchel itself rides on Bob's back hip
    bag = ws([(198, 262), (212, 254), (236, 256), (240, 270), (238, 304), (226, 312), (202, 310), (194, 296)])
    flap = ws([(198, 262), (212, 254), (236, 256), (240, 270), (236, 284), (200, 282)])
    satchel = outlined(bag, C["leather"]) + [path(flap, C["leather_light"], INK, 1.8),
                                             path(ws([(216, 280, True), (222, 280, True), (222, 290, True),
                                                      (216, 290, True)]), C["brass"], INK, 1.2),
                                             wl([(204, 298), (232, 298)], C["leather_dark"], 1.4)]
    part("satchel", "Satchel", "satchel", "torso", 46, satchel)


def hips_part():
    sil = ws([(226, 292, True), (286, 292, True), (290, 312), (284, 330), (230, 332), (224, 314)])
    items = [path(ws([(222, 290, True), (292, 290, True), (292, 302, True), (222, 302, True)]), C["leather_dark"]),
             path(ws([(274, 291, True), (286, 291, True), (286, 302, True), (274, 302, True)]), "none", C["brass"], 2.2)]
    body = outlined(sil, C["pants"], items, "clip-hips")
    # the keyring at the front hip
    body.append(ellipse(270, 312, 6.0, 6.0, "none", C["brass"], 2.2))
    for k, (dx, ang) in enumerate(((-3, 100), (2, 80), (6, 60))):
        a = math.radians(ang)
        x0, y0 = 270 + dx * 0.5, 318
        x1, y1 = x0 + math.cos(a) * 14, y0 + math.sin(a) * 14
        body.append(wl([(x0, y0), (x1, y1)], C["brass"] if k != 1 else C["steel"], 2.6))
        body.append(ellipse(x0 + math.cos(a) * 3, y0 + math.sin(a) * 3, 2.6, 2.6, C["brass_light"] if k != 1 else C["steel"],
                            INK, 0.8))
    part("hips", "Hips", "hips", "pelvis", 48, body)


# ---- legs ------------------------------------------------------------------------
def leg_parts(side):
    near = side == "near"
    col = C if near else {**C, **FAR}
    zb = 30 if near else 20
    hip, knee, ankle = J[f"{side}_hip"], J[f"{side}_knee"], J[f"{side}_ankle"]
    thigh = capsule(hip, knee, 25.0, 19.0)
    items = [line([(hip[0] + 10, hip[1] + 8), (knee[0] + 8, knee[1] - 6)], col["pants_light"], 4.0),
             line([(hip[0] - 10, hip[1] + 10), (knee[0] - 10, knee[1] - 4)], C["pants_dark"], 2.0)]
    part(f"{side}-leg-u", f"Thigh - {side}", f"{side}_leg_u", f"{side}_leg_u", zb + 2,
         outlined(thigh, col["pants"], items, f"clip-{side}-thigh"))
    shin = capsule(knee, ankle, 19.0, 14.5)
    items = [line([(knee[0] + 8, knee[1] + 6), (ankle[0] + 7, ankle[1] - 8)], col["pants_light"], 3.4),
             # a reinforced knee
             path(smooth([(knee[0] - 12, knee[1] - 8), (knee[0] + 14, knee[1] - 10), (knee[0] + 14, knee[1] + 14),
                          (knee[0] - 12, knee[1] + 14)]), C["pants_dark"]),
             line([(knee[0] - 12, knee[1] + 13), (knee[0] + 14, knee[1] + 13)], col["pants_light"], 1.2)]
    part(f"{side}-leg-l", f"Shin - {side}", f"{side}_leg_l", f"{side}_leg_l", zb + 1,
         outlined(shin, col["pants"], items, f"clip-{side}-shin"))
    ax, ay = ankle
    # Work boots laced up over the trouser hems: drawn above the shin.
    boot = smooth([(ax - 17, ay - 24), (ax + 13, ay - 26), (ax + 17, ay - 6), (ax + 34, ay + 0), (ax + 44, ay + 9),
                   (ax + 44, ay + 18, True), (ax - 18, ay + 18, True), (ax - 19, ay + 2)])
    items = [path(smooth([(ax - 20, ay + 11, True), (ax + 44, ay + 11, True), (ax + 44, ay + 20, True),
                          (ax - 20, ay + 20, True)]), C["sole"]),
             path(smooth([(ax - 19, ay - 28, True), (ax + 15, ay - 30, True), (ax + 15, ay - 21, True),
                          (ax - 19, ay - 19, True)]), col["boot_light"], INK, 1.4),
             line([(ax + 18, ay - 2), (ax + 34, ay + 4)], col["boot_light"], 2.0)]
    for k in range(3):
        items.append(line([(ax + 2 + k * 4, ay - 14 + k * 4), (ax + 10 + k * 4, ay - 12 + k * 4)], C["sole"], 1.4))
    part(f"{side}-foot", f"Boot - {side}", f"{side}_foot", f"{side}_foot", zb + 3,
         outlined(boot, col["boot"], items, f"clip-{side}-boot"))


# ---- arms and hands ---------------------------------------------------------------
def arm_parts(side):
    near = side == "near"
    col = C if near else {**C, **FAR}
    zb = 80 if near else 10
    sh, el, wr = J[f"{side}_shoulder"], J[f"{side}_elbow"], J[f"{side}_wrist"]
    upper = capsule(sh, el, 17.5, 14.0)
    ux, uy = el[0] - sh[0], el[1] - sh[1]
    d = math.hypot(ux, uy)
    nx, ny = -uy / d, ux / d
    cuff_a = (el[0] - ux / d * 14, el[1] - uy / d * 14)
    items = [line([(sh[0] + nx * 7, sh[1] + ny * 7), (el[0] + nx * 6, el[1] + ny * 6)], col["shirt_light"], 4.0),
             # the rolled sleeve: a band of turned-back cloth above the elbow
             path(smooth([(cuff_a[0] + nx * 16, cuff_a[1] + ny * 16, True), (el[0] + nx * 16, el[1] + ny * 16, True),
                          (el[0] - nx * 16, el[1] - ny * 16, True), (cuff_a[0] - nx * 16, cuff_a[1] - ny * 16, True)]),
                  col["shirt_light"]),
             line([(cuff_a[0] + nx * 16, cuff_a[1] + ny * 16), (cuff_a[0] - nx * 16, cuff_a[1] - ny * 16)], C["stripe"], 1.6)]
    part(f"{side}-arm-u", f"Upper Arm - {side}", f"{side}_arm_u", f"{side}_arm_u", zb,
         outlined(upper, col["shirt"], items, f"clip-{side}-arm-u"))
    fore = capsule(el, wr, 14.0, 11.0)
    items = [line([(el[0] + 5, el[1] + 2), (wr[0] + 4, wr[1] - 2)], C["skin_light"] if near else col["skin"], 3.0)]
    part(f"{side}-arm-l", f"Forearm - {side}", f"{side}_arm_l", f"{side}_arm_l", zb - 2,
         outlined(fore, col["skin"], items, f"clip-{side}-arm-l"))
    wx, wy = wr
    # Hands are drawn pointing +x from the wrist (the hand bone's rest angle).
    fist = smooth([(wx - 6, wy - 10), (wx + 10, wy - 12), (wx + 20, wy - 7), (wx + 22, wy + 4), (wx + 16, wy + 11),
                   (wx + 2, wy + 12), (wx - 6, wy + 8)])
    fist_items = [line([(wx + 10, wy - 11), (wx + 12, wy + 10)], col["skin"] if not near else C["skin_shadow"], 1.4),
                  line([(wx + 15, wy - 9), (wx + 17, wy + 9)], C["skin_shadow"], 1.2),
                  path(smooth([(wx - 2, wy - 12), (wx + 12, wy - 16), (wx + 16, wy - 10), (wx + 4, wy - 6)]),
                       C["skin_light"] if near else col["skin"], INK, 1.4)]
    open_hand = smooth([(wx - 6, wy - 9), (wx + 14, wy - 10), (wx + 30, wy - 8), (wx + 32, wy - 3), (wx + 30, wy + 2),
                        (wx + 16, wy + 6), (wx + 2, wy + 10), (wx - 6, wy + 7)])
    open_items = [line([(wx + 16, wy - 4), (wx + 30, wy - 4)], C["skin_shadow"], 1.2),
                  line([(wx + 14, wy + 1), (wx + 28, wy + 0)], C["skin_shadow"], 1.2),
                  path(smooth([(wx + 2, wy - 8), (wx + 16, wy - 18), (wx + 20, wy - 14), (wx + 8, wy - 4)]),
                       col["skin"], INK, 1.4)]
    grip = "near" if near else "far"
    part(f"{side}-hand-fist", f"Hand Fist - {side}", f"{side}_hand_fist", f"{side}_hand", zb + 4,
         outlined(fist, col["skin"], fist_items, f"clip-{side}-fist"), f' data-rig-opacity="hand.{grip}.fist" data-rig-default="1"')
    part(f"{side}-hand-open", f"Hand Open - {side}", f"{side}_hand_open", f"{side}_hand", zb + 4,
         outlined(open_hand, col["skin"], open_items, f"clip-{side}-open"), f' data-rig-opacity="hand.{grip}.open"')


def wrench_body(grip, angle=0.0, k=1.22):
    """The big adjustable wrench drawn about its grip: the handle runs up -y
    from the grip, the open jaw at the top; scaled by ``k`` and turned by
    ``angle`` degrees about the grip."""
    gx, gy = grip
    ca, sa = math.cos(math.radians(angle)), math.sin(math.radians(angle))

    def m(pts):
        return [(gx + k * (q[0] * ca - q[1] * sa), gy + k * (q[0] * sa + q[1] * ca)) + tuple(q[2:]) for q in pts]

    def ms(pts):
        return smooth(m(pts))

    def ml(pts, stroke, sw):
        return line(m(pts), stroke, sw)

    handle = ms([(-6, 26, True), (6, 26, True), (6, -74, True), (-6, -74, True)])
    head = ms([(-16, -70), (-18, -90), (-10, -104, True), (-4, -104, True), (-4, -92, True), (8, -92, True),
               (8, -106, True), (16, -102), (18, -86), (14, -70)])
    return [path(handle, C["steel"], INK, 2 * OW),
            ml([(-2, 22), (-2, -70)], C["steel_light"], 2.0),
            ml([(3, -10), (3, -60)], C["steel_dark"], 1.2),
            path(ms([(-7, 4, True), (7, 4, True), (7, 28, True), (-7, 28, True)]), C["leather_dark"], INK, 1.4),
            path(head, C["steel"], INK, 2 * OW),
            ml([(-12, -74), (-13, -88)], C["steel_light"], 2.0),
            # the adjusting worm screw
            path(ms([(-8, -78, True), (8, -78, True), (8, -70, True), (-8, -70, True)]), C["brass"], INK, 1.2),
            ml([(-4, -78), (-4, -70)], C["brass_light"], 1.0),
            ml([(1, -78), (1, -70)], C["brass_light"], 1.0)]


def wrench_part():
    """The wrench gripped in the near fist (its handle up the hand's local
    -y, so a hand pitched 90 degrees holds it level and forward), and the
    same wrench stowed in its strap across Bob's back when his hands are busy:
    the rig shows one or the other (``prop.wrench`` / ``prop.wrench_back``)."""
    wx, wy = J["near_wrist"]
    part("wrench", "Wrench", "wrench", "near_hand", 82, wrench_body((wx + 9, wy)),
         ' data-rig-opacity="prop.wrench" data-rig-default="1"')
    part("wrench-back", "Wrench - Stowed", "wrench_back", "torso", 44, wrench_body((236, 292), -24.0),
         ' data-rig-opacity="prop.wrench_back"')


def analyzer_part():
    """The lock / cipher analyzer, held up in the far hand when Bob receives."""
    wx, wy = J["far_wrist"]
    box = smooth([(wx + 4, wy - 26, True), (wx + 36, wy - 26, True), (wx + 36, wy + 6, True), (wx + 4, wy + 6, True)])
    body = [path(box, C["device"], INK, 2 * OW),
            path(smooth([(wx + 9, wy - 21, True), (wx + 31, wy - 21, True), (wx + 31, wy - 8, True), (wx + 9, wy - 8, True)]),
                 C["screen"], INK, 1.2),
            line([(wx + 12, wy - 14), (wx + 17, wy - 11), (wx + 27, wy - 18)], "#e8fff7", 1.6),
            ellipse(wx + 12, wy - 1, 2.4, 2.4, C["led"]), ellipse(wx + 20, wy - 1, 2.4, 2.4, C["device_dark"]),
            ellipse(wx + 28, wy - 1, 2.4, 2.4, C["device_dark"]),
            line([(wx + 36, wy - 18), (wx + 46, wy - 30)], C["steel_dark"], 2.4)]
    part("analyzer", "Analyzer", "analyzer", "far_hand", 16, body, ' data-rig-opacity="prop.analyzer"')


def draw() -> str:
    svg.configure(dx=DX, dy=DY, ink=INK, ow=OW, colors=C)
    arm_parts("far")
    analyzer_part()
    leg_parts("far")
    leg_parts("near")
    torso_parts()
    hips_part()
    head_part()
    face_parts()
    wrench_part()
    arm_parts("near")
    return svg.document(
        size=(W, H),
        design="bob-fighter-side-v2",
        layer_id="bob-side",
        label="Bob - Side Right",
        comment=[
            "  <!-- Bob, the cryptography crew's hardware engineer, as a fighter: side view,",
            "       facing right, about 375 units tall on a 720x640 drawing whose ground is",
            "       y=569. Each part is a layer with a data-rig-part name; the rig in",
            "       targets/characters/rigged/bob/ turns these parts about their joints.",
            "       Swap sets sit on top of each other and the rig shows one of each at a",
            "       time (data-rig-opacity): the hands' fist/open, the eyes, the mouth, and",
            "       the props (the wrench in the near fist, the analyzer in the far hand).",
            "       The hidden Rig Joints layer marks every joint the skeleton is built on. -->",
        ],
        joints=svg.joints_layer(J, {"head_top": HEAD_XF}),
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    Path(sys.argv[1]).write_text(draw())
