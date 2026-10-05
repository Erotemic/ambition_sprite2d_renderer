#!/usr/bin/env python3
"""How the raptor stalker's SVG was first drawn (reference, not authority).

``data/characters/raptor_stalker/raptor_stalker.svg`` owns the art and may
have been edited since; this script reproduces the drawing as it was first
committed (less the rig catalog ``scripts/build_raptor_stalker_rig.py``
installs). Keep it as a worked example for drawing a new creature with
``svgkit``: feathers (``feather``), a mane and fringes (``fringe``).

    uv run python scripts/svg_art/raptor_stalker_art.py OUT.svg

Drawn in design units, shifted by (40, 0) into a 600x400 SVG whose ground is
y=372.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import svgkit as svg
from svgkit import capsule, clipped, ellipse, feather, fringe, ink, line, part, path, smooth, smooth_run, tooth

W, H = 600, 400
INK = "#141a18"
OW = 2.0  # half the silhouette ink width

C = dict(
    body="#3e6b5d",
    light="#5f8f78",
    back="#2b4c43",
    stripe="#1c332d",
    belly="#e6d8ad",
    belly_sh="#c2b082",
    accent="#c4572a",
    accent_l="#ee8c48",
    accent_d="#8e3a1b",
    feather="#29473f",
    claw="#f0e7cf",
    claw_sh="#b3a68a",
    eye="#e8f25a",
    eye_rim="#fbffb0",
    pupil="#140c06",
    mask="#1b2c27",
    mouth="#4a161c",
    mouth2="#6b2028",
    gum="#b04d58",
    tongue="#c8707a",
    tooth="#f4ecd4",
    nostril="#141a18",
)
FAR = dict(body="#2f5649", light="#447062", belly="#bcae86", belly_sh="#9d8e66", accent="#9c4522",
           accent_l="#c26a35", feather="#203a33", claw="#d0c7ae", stripe="#16291f")

J = dict(
    pelvis=(250.0, 228.0),
    neck_base=(326.0, 214.0),
    head=(368.0, 160.0),
    jaw=(382.0, 172.0),
    snout=(458.0, 167.0),
    tail0=(216.0, 220.0),
    tail1=(172.0, 212.0),
    tail2=(128.0, 207.0),
    tail3=(86.0, 206.0),
    tail_tip=(40.0, 208.0),
    near_hip=(254.0, 230.0),
    near_knee=(286.0, 284.0),
    near_ankle=(254.0, 338.0),
    far_hip=(240.0, 227.0),
    far_knee=(272.0, 281.0),
    far_ankle=(238.0, 338.0),
    near_shoulder=(326.0, 236.0),
    near_elbow=(314.0, 263.0),
    near_wrist=(344.0, 272.0),
    far_shoulder=(320.0, 232.0),
    far_elbow=(308.0, 258.0),
    far_wrist=(337.0, 267.0),
)


# ---- tail ------------------------------------------------------------------
TAIL = ["tail0", "tail1", "tail2", "tail3", "tail_tip"]
TAIL_R = [24.0, 16.0, 10.5, 7.0, 3.0]


def tail_part(i):
    a, b = J[TAIL[i]], J[TAIL[i + 1]]
    r0, r1 = TAIL_R[i], TAIL_R[i + 1]
    sil = capsule(a, b, r0, r1)
    name = f"tail{i + 1}"
    ink(name, name, 20 + (4 - i) * 0.1, sil)
    ax, ay = a
    bx, by = b
    d = math.hypot(bx - ax, by - ay)
    ux, uy = (bx - ax) / d, (by - ay) / d
    nx, ny = uy, -ux  # points DOWN for a tail running -x

    def at(t, off):
        r = r0 + (r1 - r0) * min(1.0, max(0.0, t))
        return (ax + (bx - ax) * t + nx * off * r, ay + (by - ay) * t + ny * off * r)

    items = [path(sil, C["body"])]
    items.append(path(smooth([at(-0.6, -0.5), at(0.5, -0.58), at(1.6, -0.5), at(1.6, -1.6), at(-0.6, -1.6)]),
                      C["light"]))
    items.append(path(smooth([at(-0.6, 0.3), at(0.5, 0.38), at(1.6, 0.3), at(1.6, 1.6), at(-0.6, 1.6)]),
                      C["belly"]))
    # dark bands across the tail (the stalker's barring)
    for t in ((0.3, 0.8) if i < 3 else (0.4,)):
        q = [at(t - 0.07, -1.2) + (True,), at(t - 0.02, 0.25), at(t + 0.03, 0.42) + (True,),
             at(t + 0.07, 0.1), at(t + 0.09, -1.2) + (True,)]
        items.append(path(smooth(q), C["stripe"]))
    # feather texture
    for t in (0.2, 0.55, 0.85):
        items.append(line([at(t - 0.05, -0.2), at(t + 0.04, 0.05), at(t - 0.05, 0.3)], C["back"], 1.1))
    body = []
    # The tail's feather fan: vanes splaying from the last two segments,
    # longest at the tip, rust-tipped.
    if i >= 2:
        n = 3 if i == 2 else 5
        back = math.degrees(math.atan2(-uy, -ux))
        fan = []
        for k in range(n):
            t = (k + 0.6) / n
            grow = (k + 1) / n
            length = (16 + 10 * grow) if i == 2 else (30 + 22 * grow)
            spread = (52 - 8 * grow) if i == 2 else (48 - 26 * grow)
            tip = C["accent"] if i == 3 else None
            fan += feather(at(t, -0.5), back + spread, length, 8.5, C["feather"], tip)
            fan += feather(at(t, 0.5), back - spread, length, 8.5, C["feather"], tip)
        if i == 3:
            fan += feather(at(0.9, 0), back, 50, 11, C["feather"], C["accent"])
        body += fan
    body += clipped(f"clip-tail{i + 1}", sil, items)
    part(name, f"Tail {i + 1}", name, name, 30 + (4 - i) * 0.1, body)


# ---- torso -----------------------------------------------------------------
TORSO = [(198, 206), (234, 195), (270, 190), (302, 194), (328, 203), (346, 222), (346, 246), (330, 262),
         (300, 266), (270, 258), (240, 246), (210, 236), (194, 222)]


def torso_part():
    sil = smooth(TORSO)
    ink("torso", "torso", 24, sil)
    items = [path(sil, C["body"])]
    items.append(path(smooth([(190, 198), (232, 186), (270, 182), (306, 186), (336, 198), (334, 210), (304, 202),
                              (270, 199), (234, 204), (196, 214)]), C["light"]))
    items.append(path(smooth([(196, 228), (226, 232), (260, 240), (296, 244), (324, 238), (344, 222), (360, 226),
                              (360, 290), (190, 290)]), C["belly"]))
    items.append(line([(200, 230), (228, 236), (262, 244), (296, 248), (326, 242), (344, 228)], C["belly_sh"], 1.4))
    # barring over the back
    for x, top, length in ((214, 200, 26), (240, 192, 30), (268, 188, 32), (296, 190, 30), (322, 198, 22)):
        items.append(path(smooth([(x - 5, top - 6, True), (x - 1, top + length * 0.6), (x + 2, top + length, True),
                                  (x + 4, top + length * 0.55), (x + 7, top - 6, True)]), C["stripe"]))
    # feather chevrons
    for x, y in ((226, 218), (252, 214), (280, 214), (308, 216), (240, 228), (268, 230), (296, 232), (322, 222)):
        items.append(line([(x - 5, y - 4), (x, y + 1), (x - 5, y + 6)], C["back"], 1.1))
    for x, y in ((250, 254), (276, 258), (302, 258), (326, 250)):
        items.append(line([(x - 4, y - 3), (x, y + 1), (x - 4, y + 5)], C["belly_sh"], 1.0))
    body = clipped("clip-torso", sil, items)
    # a short dark feather fringe along the spine
    body = fringe([(204, 204), (234, 196), (270, 191), (302, 195), (326, 203)], 9, 6.5, 0.6, C["feather"],
                  ow=1.0, flip=False, jitter=0.25) + body
    part("torso", "Torso", "torso", "torso", 34, body)


# ---- neck ------------------------------------------------------------------
NECK = [(312, 210), (326, 196), (340, 178), (352, 160), (366, 148), (382, 152), (386, 170), (376, 188),
        (364, 206), (354, 228), (336, 238), (318, 226)]


def neck_part():
    sil = smooth(NECK)
    ink("neck", "neck", 25, sil)
    items = [path(sil, C["body"])]
    items.append(path(smooth([(308, 202), (326, 188), (340, 170), (354, 152), (368, 142), (372, 152), (358, 162),
                              (344, 180), (328, 200), (314, 214)]), C["light"]))
    items.append(path(smooth([(392, 168), (384, 180), (372, 196), (362, 214), (352, 236), (380, 240), (400, 190)]),
                      C["belly"]))
    items.append(line([(384, 172), (374, 188), (364, 206), (356, 226)], C["belly_sh"], 1.2))
    for x, y in ((352, 178), (344, 196), (360, 196)):
        items.append(line([(x - 4, y - 4), (x + 1, y + 1), (x - 4, y + 6)], C["back"], 1.1))
    body = clipped("clip-neck", sil, items)
    # the rust ruff: a mane of raised feathers down the back of the neck
    body = fringe([(316, 206), (328, 194), (340, 178), (350, 162), (362, 150)], 7, 15.0, 1.1, C["accent"],
                  C["accent_d"], ow=1.1, flip=False, jitter=0.2, inset=10) + body
    part("neck", "Neck", "neck", "neck", 35, body)


# ---- head ------------------------------------------------------------------
SKULL = [(358, 160), (360, 147), (370, 138), (386, 133), (404, 134), (422, 140), (440, 148), (454, 156),
         (461, 163), (459, 170, True), (446, 171), (424, 172), (402, 173), (390, 176), (378, 180), (366, 172)]
UPPER_TEETH = [(398, 173.5, 4.2, 2.8), (405, 173.2, 5.0, 3.0), (412, 172.9, 5.4, 3.2), (419, 172.6, 5.4, 3.2),
               (426, 172.3, 5.0, 3.0), (433, 172.0, 5.0, 3.0), (440, 171.6, 4.6, 2.8), (447, 171.2, 4.2, 2.6),
               (453, 170.6, 3.6, 2.4)]


def head_part():
    sil = smooth(SKULL)
    ink("head", "head", 27, sil)
    items = [path(sil, C["body"])]
    items.append(path(smooth([(364, 146), (378, 134), (404, 128), (430, 136), (452, 148), (462, 158), (452, 156),
                              (432, 146), (404, 140), (380, 142)]), C["light"]))
    # pale lip and chin edge
    items.append(path(smooth([(392, 172), (420, 169), (446, 168), (462, 164), (466, 180), (390, 184)]), C["belly"]))
    # the dark eye mask sweeping back to the ear
    items.append(path(smooth([(372, 152, True), (384, 143), (400, 141), (410, 146), (404, 154), (390, 156),
                              (378, 160)]), C["mask"]))
    items.append(path(smooth([(412, 152), (424, 150), (436, 154), (430, 160), (416, 160)]), C["back"]))
    items.append(ellipse(450, 158, 2.8, 1.8, C["nostril"], rot=-20))
    items.append(line([(380, 166), (388, 162), (396, 166)], C["back"], 1.2))
    # scale texture along the snout
    for x, y in ((420, 144), (430, 147), (440, 151), (426, 152), (436, 156)):
        items.append(ellipse(x, y, 1.3, 0.9, C["light"]))
    items.append(line([(396, 175), (420, 172.5), (446, 171), (459, 168)], INK, 1.8))
    body = clipped("clip-head", sil, items)
    # The crest: swept-back rust plumes from the crown.
    for base, ang, length in (((376, 140), 196, 26), ((370, 144), 204, 24), ((384, 137), 190, 22),
                              ((364, 150), 212, 20)):
        body = feather(base, ang, length, 8, C["accent"], C["accent_d"], INK, 1.0, 0.3) + body
    for x, y, h, w in UPPER_TEETH:
        body.append(tooth(x, y, h, w, True, curve=0.6))
    part("head", "Head", "head", "head", 48, body)


JAW = [(370, 178), (376, 170, True), (390, 175), (414, 174), (436, 172.5), (452, 171), (458, 169, True),
       (456, 175), (444, 180), (420, 185), (396, 188), (380, 186)]
LOWER_TEETH = [(404, 174.5, 4.0, 2.8), (412, 174.0, 4.6, 3.0), (420, 173.6, 4.6, 3.0), (428, 173.2, 4.4, 2.8),
               (436, 172.7, 4.0, 2.6), (444, 172.0, 3.6, 2.4)]


def jaw_part():
    sil = smooth(JAW)
    ink("jaw", "jaw", 26, sil)
    items = [path(sil, C["body"])]
    items.append(path(smooth([(370, 182), (396, 182), (424, 179), (450, 174), (462, 170), (462, 196), (370, 196)]),
                      C["belly"]))
    items.append(line([(378, 176), (404, 177), (430, 175), (452, 172)], C["belly"], 2.2))
    jaw_body = clipped("clip-jaw", sil, items)
    roof = smooth([(386, 175, True), (412, 174), (436, 172.5), (454, 170.5, True), (450, 162), (430, 160),
                   (406, 160), (390, 166)])
    tongue = smooth([(390, 174, True), (408, 171), (424, 170), (432, 171), (428, 174), (408, 175)])
    teeth = [tooth(x, y, h, w, False, curve=0.6) for x, y, h, w in LOWER_TEETH]
    body = [path(roof, C["mouth"]), path(tongue, C["tongue"], C["mouth2"], 0.9)] + teeth + jaw_body
    part("jaw", "Lower Jaw", "jaw", "jaw", 44, body)


def mouth_floor_part():
    floor = smooth([(390, 175, True), (412, 174.5), (436, 173), (452, 171.5, True), (448, 176), (430, 180),
                    (408, 183), (392, 181)])
    gum = smooth([(390, 174, True), (412, 173.5), (436, 172), (452, 170.5, True), (450, 173.5), (436, 175),
                  (412, 176.5), (392, 177)])
    part("mouth-floor", "Mouth Floor", "mouth_floor", "head", 42,
         [path(floor, C["mouth"]), path(gum, C["gum"]), line([(398, 180), (420, 180), (440, 177)], C["mouth2"], 1.4)])


EYE = (392.0, 149.0)


def eye_parts():
    x, y = EYE
    base = ellipse(x, y, 7.5, 6.5, C["mask"])
    lid = smooth([(x - 7.5, y + 1), (x - 3, y - 5.5), (x + 4, y - 5.5), (x + 7.5, y), (x + 3, y + 4.5),
                  (x - 4, y + 4.5)])
    open_ = [base, ellipse(x, y, 5.6, 4.6, C["eye"], INK, 1.2), ellipse(x - 1, y - 1, 3.0, 1.8, C["eye_rim"]),
             ellipse(x + 0.6, y, 1.3, 3.8, C["pupil"]), ellipse(x - 2.2, y - 1.6, 0.9, 0.7, "#ffffff"),
             line([(x - 8, y - 3), (x - 1, y - 7), (x + 8, y - 4.5)], INK, 1.8)]
    angry = [base, ellipse(x, y + 0.6, 5.6, 4.0, C["eye"], INK, 1.2), ellipse(x + 0.6, y + 0.8, 1.1, 3.2, C["pupil"]),
             path(smooth([(x - 9, y - 8, True), (x + 8, y - 0.5, True), (x + 8, y - 9, True)]), C["mask"]),
             line([(x - 8, y - 6), (x + 8, y + 0.5)], INK, 2.0), ellipse(x - 3, y + 1.4, 0.8, 0.6, "#ffffff")]
    shut = [base, path(lid, C["body"], INK, 1.1), line([(x - 6, y + 0.5), (x, y + 3), (x + 6, y + 0.5)], INK, 1.8)]
    dead = [base, path(lid, C["body"], INK, 1.1), line([(x - 4.5, y - 3.5), (x + 4.5, y + 3.5)], INK, 2.0),
            line([(x - 4.5, y + 3.5), (x + 4.5, y - 3.5)], INK, 2.0)]
    part("eye-open", "Eye - Open", "eye_open", "head", 50, open_, ' data-rig-opacity="eye.open" data-rig-default="1"')
    part("eye-angry", "Eye - Angry", "eye_angry", "head", 50, angry, ' data-rig-opacity="eye.angry"')
    part("eye-shut", "Eye - Shut", "eye_shut", "head", 50, shut, ' data-rig-opacity="eye.shut"')
    part("eye-dead", "Eye - Dead", "eye_dead", "head", 50, dead, ' data-rig-opacity="eye.dead"')


# ---- legs ------------------------------------------------------------------
def leg_parts(side):
    near = side == "near"
    col = C if near else {**C, **FAR}
    dx = 0.0 if near else -14.0
    dy = 0.0 if near else -3.0
    zb = 70 if near else 10
    knee, ankle = J[f"{side}_knee"], J[f"{side}_ankle"]

    def S(pts):
        return [(p[0] + dx, p[1] + dy) + tuple(p[2:]) for p in pts]

    thigh_pts = S([(232, 214), (254, 206), (274, 212), (288, 230), (294, 256), (292, 280), (283, 290), (272, 285),
                   (262, 268), (246, 252), (232, 238), (226, 224)])
    thigh = smooth(thigh_pts)
    hi = smooth(S([(238, 212), (258, 206), (278, 214), (290, 234), (292, 250), (282, 234), (266, 220), (248, 216)]))
    t_items = [path(thigh, col["body"]), path(hi, col["light"])]
    for x, y in ((252, 226), (268, 236), (278, 254), (260, 248)):
        t_items.append(line(S([(x - 5, y - 4), (x, y + 1), (x - 5, y + 6)]), C["back"] if near else col["stripe"], 1.1))
    t_items.append(path(smooth(S([(256, 210, True), (262, 236), (264, 256, True), (268, 236), (266, 210, True)])),
                        col["stripe"]))
    t_body = clipped(f"clip-{side}-thigh", thigh, t_items)
    # feather "trousers": a fringe off the back of the thigh
    t_body = fringe(S([(230, 230), (240, 246), (254, 262), (266, 276), (276, 288)]), 5, 9.0, 0.7, col["feather"],
                    ow=1.0, flip=True, jitter=0.2) + t_body
    t_body += [path(smooth_run(thigh_pts, 3, 8), "none", INK, 2 * OW),
               path(smooth_run(thigh_pts, 11, 4), "none", C["back"] if near else col["stripe"], 2.0)]
    part(f"{side}-thigh", f"Thigh - {side}", f"{side}_thigh", f"{side}_thigh", zb + 4, t_body)

    shin = capsule(knee, ankle, 8.0, 6.0)
    s_items = [path(shin, col["body"]), line([(knee[0] + 4, knee[1] + 4), (ankle[0] + 4, ankle[1] - 3)], col["light"], 2.4)]
    for k in range(3):
        t = 0.55 + k * 0.14
        cx = knee[0] + (ankle[0] - knee[0]) * t
        cy = knee[1] + (ankle[1] - knee[1]) * t
        s_items.append(line([(cx - 6, cy - 1), (cx + 6, cy + 2)], C["back"] if near else col["stripe"], 1.0))
    s_body = clipped(f"clip-{side}-shin", shin, s_items) + [path(shin, "none", INK, 2 * OW)]
    part(f"{side}-shin", f"Shin - {side}", f"{side}_shin", f"{side}_shin", zb + 2, s_body)

    ax, ay = ankle
    foot = smooth([(ax - 6, ay - 2), (ax - 1, ay - 7), (ax + 6, ay - 3), (ax + 10, ay + 14), (ax + 16, ay + 24),
                   (ax + 30, ay + 27), (ax + 38, ay + 31), (ax + 35, ay + 34, True), (ax + 8, ay + 34, True),
                   (ax + 1, ay + 30), (ax - 4, ay + 14)])
    f_items = [path(foot, col["body"]), line([(ax + 3, ay - 3), (ax + 8, ay + 14), (ax + 16, ay + 22)], col["light"], 2.2)]
    for k, yy in enumerate((ay + 6, ay + 12, ay + 18)):
        f_items.append(line([(ax - 3, yy), (ax + 6 + k, yy + 2)], C["back"] if near else col["stripe"], 1.0))
    f_body = clipped(f"clip-{side}-foot", foot, f_items) + [path(foot, "none", INK, 2 * OW)]
    for tx, ty, s in ((ax + 37, ay + 30, 0.8), (ax + 27, ay + 31.5, 0.7)):
        claw = smooth([(tx - 2 * s, ty - 4 * s, True), (tx + 6 * s, ty - 2 * s), (tx + 9 * s, ty + 4.5 * s, True),
                       (tx + 3 * s, ty + 2 * s), (tx - 2 * s, ty + 3 * s, True)])
        f_body.append(path(claw, col["claw"], INK, 1.0))
    # The sickle claw: the second toe's great hook, held clear of the ground.
    sickle = smooth([(ax + 11, ay + 26, True), (ax + 10, ay + 16), (ax + 16, ay + 8), (ax + 25, ay + 7),
                     (ax + 31, ay + 13, True), (ax + 24, ay + 12), (ax + 19, ay + 15), (ax + 18, ay + 26, True)])
    f_body.append(path(sickle, col["claw"], INK, 1.3))
    f_body.append(line([(ax + 14, ay + 22), (ax + 15, ay + 14), (ax + 21, ay + 10)], col["claw_sh"] if near else C["claw_sh"], 1.1))
    part(f"{side}-foot", f"Foot - {side}", f"{side}_foot", f"{side}_foot", zb, f_body)


# ---- arms ------------------------------------------------------------------
def arm_parts(side):
    near = side == "near"
    col = C if near else {**C, **FAR}
    zb = 62 if near else 16
    sh, el, wr = J[f"{side}_shoulder"], J[f"{side}_elbow"], J[f"{side}_wrist"]
    up = capsule(sh, el, 6.0, 4.6)
    up_body = []
    for k in range(3):
        t = 0.3 + 0.3 * k
        base = (sh[0] + (el[0] - sh[0]) * t, sh[1] + (el[1] - sh[1]) * t)
        up_body += feather(base, 160, 11 + 2 * k, 6, col["feather"], None, INK, 0.9)
    up_body += [path(up, col["body"], INK, 2 * OW),
                line([(sh[0] - 1, sh[1] + 2), (el[0] + 2, el[1] - 3)], col["light"], 2.0)]
    part(f"{side}-arm-u", f"Upper Arm - {side}", f"{side}_arm_u", f"{side}_arm_u", zb, up_body)
    lo = capsule(el, wr, 4.4, 3.4)
    wx, wy = wr
    lo_body = []
    # primaries: a wing of vanes trailing down and back from the forearm
    for k in range(5):
        t = 0.1 + 0.22 * k
        base = (el[0] + (wx - el[0]) * t, el[1] + (wy - el[1]) * t + 1)
        lo_body += feather(base, 128 - 6 * k, 18 + 4 * k, 7, col["feather"], col["accent"], INK, 0.9)
    fingers = []
    for (dx, dy, ang) in ((1, -1, 26), (2, 1.5, 44), (0, 3, 62)):
        cx, cy = wx + dx, wy + dy
        r = math.radians(ang)
        tip = (cx + 10 * math.cos(r), cy + 10 * math.sin(r))
        fingers.append(line([(cx, cy), tip], col["body"], 3.2))
        fingers.append(path(smooth([(tip[0] - 1.6, tip[1] - 1.2, True), (tip[0] + 3.5, tip[1] + 0.5),
                                    (tip[0] + 3.5, tip[1] + 5.5, True), (tip[0] + 1.5, tip[1] + 1.8),
                                    (tip[0] - 1.2, tip[1] + 1.5, True)]), col["claw"], INK, 0.9))
    lo_body += [line([(el[0], el[1]), (wx, wy)], INK, 4.4 * 2 + 2 * OW)] + fingers + \
               [path(lo, col["body"]), ellipse(wx, wy, 4.0, 3.6, col["body"], INK, 1.2)]
    part(f"{side}-arm-l", f"Forearm - {side}", f"{side}_arm_l", f"{side}_arm_l", zb + 1, lo_body)


def draw() -> str:
    svg.configure(dx=40.0, dy=0.0, ink=INK, ow=OW, colors=C)
    leg_parts("far")
    arm_parts("far")
    for i in range(4):
        tail_part(i)
    torso_part()
    neck_part()
    mouth_floor_part()
    jaw_part()
    head_part()
    eye_parts()
    arm_parts("near")
    leg_parts("near")
    return svg.document(
        size=(W, H),
        design="raptor-stalker-side-v2",
        layer_id="raptor-side",
        label="Raptor - Side Right",
        comment=[
            "  <!-- The raptor stalker: a feathered dromaeosaur in side view, facing right. The",
            "       rig publishes this 600x400 drawing at 0.38 px per unit (a 228x152 sprite",
            "       frame); the ground is y=372.",
            "       Each part is a layer with a data-rig-part name; the rig in",
            "       targets/characters/rigged/raptor_stalker/ turns these parts about their joints.",
            "       *_ink layers are each body part's silhouette grown by the outline width,",
            "       painted beneath every body fill so tail, torso, neck, head and jaw read as",
            "       one outlined silhouette with no seams at their joints. The eye states sit",
            "       on top of each other: the rig shows one at a time (data-rig-opacity).",
            "       The hidden Rig Joints layer marks every joint the skeleton is built on. -->",
        ],
        joints=svg.joints_layer(J),
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    Path(sys.argv[1]).write_text(draw())
