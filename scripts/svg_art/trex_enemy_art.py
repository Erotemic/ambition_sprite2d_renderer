#!/usr/bin/env python3
"""How the T-rex boss's SVG was first drawn (reference, not authority).

``data/characters/trex_enemy/trex_enemy.svg`` owns the art and may have been
edited since; this script reproduces the drawing as it was first committed
(less the rig catalog ``scripts/build_trex_enemy_rig.py`` installs). Keep it as
a worked example for drawing a new creature with ``svgkit``.

    uv run python scripts/svg_art/trex_enemy_art.py OUT.svg

Drawn in design units, shifted by (10, 16) into a 640x400 SVG whose ground is
y=372; the head, jaw and eyes are drawn 16% larger about the head joint than
the first sketch of them (``HEAD_SCALE``).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import svgkit as svg
from svgkit import capsule, clipped, ellipse, ink, line, part, path, smooth, smooth_run, tooth

W, H = 640, 400
INK = "#1b1710"
OW = 1.15  # half the silhouette ink width
LW = 1.1   # detail outline width

C = dict(
    back="#3f5527",
    body="#5e7c35",
    light="#83a14a",
    belly="#dccb93",
    belly_sh="#b9a46c",
    stripe="#33461f",
    scute="#2b3a19",
    scar="#d39a86",
    mouth="#4a161c",
    mouth2="#6b2028",
    gum="#b04d58",
    tongue="#c8707a",
    tooth="#f4ecd4",
    tooth_sh="#cdbf9b",
    eye="#f5a623",
    eye_rim="#ffd05a",
    pupil="#140c06",
    claw="#ece3cb",
    claw_sh="#a2957b",
    horn="#9a5a2c",
    horn_hi="#c47a3e",
    nostril="#20190f",
)
FAR = dict(
    body="#4b6329",
    light="#62803a",
    belly="#b9a874",
    belly_sh="#998858",
    stripe="#2b3a19",
    claw="#cfc5ad",
    claw_sh="#857a63",
)


HEAD_SCALE = (400.0, 128.0, 1.16)


# ---- joints (design coordinates) --------------------------------------------
J = dict(
    pelvis=(250.0, 196.0),
    neck_base=(356.0, 176.0),
    head=(400.0, 128.0),
    jaw=(412.0, 145.0),
    tail0=(212.0, 182.0),
    tail1=(162.0, 174.0),
    tail2=(114.0, 177.0),
    tail3=(72.0, 187.0),
    tail_tip=(28.0, 201.0),
    near_hip=(254.0, 197.0),
    near_knee=(287.0, 262.0),
    near_ankle=(262.0, 320.0),
    near_toe=(318.0, 355.0),
    far_hip=(238.0, 195.0),
    far_knee=(271.0, 260.0),
    far_ankle=(246.0, 320.0),
    far_toe=(302.0, 355.0),
    near_shoulder=(352.0, 214.0),
    near_elbow=(361.0, 234.0),
    near_wrist=(377.0, 236.0),
    far_shoulder=(344.0, 210.0),
    far_elbow=(354.0, 229.0),
    far_wrist=(369.0, 232.0),
    snout=(508.0, 128.0),
)

# ---- tail ------------------------------------------------------------------
TAIL = ["tail0", "tail1", "tail2", "tail3", "tail_tip"]
TAIL_R = [40.0, 29.0, 19.5, 11.0, 2.4]


def tail_part(i):
    a, b = J[TAIL[i]], J[TAIL[i + 1]]
    r0, r1 = TAIL_R[i], TAIL_R[i + 1]
    sil = capsule(a, b, r0, r1)
    name = f"tail{i + 1}"
    ink(name, name, 20 + (4 - i) * 0.1, sil)
    # countershading along the underside, stripes over the back.
    ax, ay = a
    bx, by = b
    d = math.hypot(bx - ax, by - ay)
    ux, uy = (bx - ax) / d, (by - ay) / d
    nx, ny = uy, -ux  # for a tail running -x, n points DOWN (+y)

    def at(t, off):
        r = r0 + (r1 - r0) * min(1.0, max(0.0, t))
        return (ax + (bx - ax) * t + nx * off * r, ay + (by - ay) * t + ny * off * r)

    belly = [at(-0.6, 0.35), at(0.5, 0.42), at(1.6, 0.35), at(1.6, 1.6), at(-0.6, 1.6)]
    hi = [at(-0.6, -0.55), at(0.5, -0.62), at(1.6, -0.55), at(1.6, -0.82), at(0.5, -0.92), at(-0.6, -0.82)]
    items = [path(sil, C["body"])]
    items.append(path(smooth([(p[0], p[1]) for p in hi]), C["light"]))
    items.append(path(smooth([(p[0], p[1]) for p in belly]), C["belly"]))
    items.append(line([at(-0.6, 0.42), at(0.5, 0.5), at(1.6, 0.42)], C["belly_sh"], 1.0))
    # ventral scale bands
    for t in (0.15, 0.5, 0.85):
        items.append(line([at(t, 0.48), at(t + 0.04, 0.9)], C["belly_sh"], 0.9))
    # tiger stripes from the spine
    for t in ((0.25, 0.75) if i < 3 else (0.5,)):
        q0, q1, q2 = at(t - 0.1, -1.1), at(t + 0.04, -0.15), at(t + 0.12, -1.1)
        items.append(path(smooth([q0 + (True,), q1 + (True,), q2 + (True,)]), C["stripe"]))
    # spine scutes
    for t in (0.2, 0.55, 0.9):
        if i < 3:
            q = at(t, -0.92)
            items.append(ellipse(q[0], q[1], 3.2 - i * 0.6, 2.0 - i * 0.3, C["scute"]))
    body = clipped(f"clip-tail{i + 1}", sil, items)
    part(name.replace("_", "-"), f"Tail {i + 1}", name, name, 30 + (4 - i) * 0.1, body)


# ---- torso -----------------------------------------------------------------
TORSO = [
    (196, 150), (228, 137), (266, 130), (304, 134), (334, 146), (360, 154),
    (380, 176), (384, 206), (372, 240), (346, 260), (306, 266), (272, 258), (240, 242),
    (214, 226), (192, 214),
]


def torso_part():
    sil = smooth(TORSO)
    ink("torso", "torso", 24, sil)
    items = [path(sil, C["body"])]
    # back highlight band
    items.append(path(smooth([(190, 140), (230, 128), (268, 122), (306, 126), (340, 138), (366, 150),
                              (360, 160), (334, 154), (304, 145), (268, 141), (232, 147), (196, 160)]), C["light"]))
    # belly
    items.append(path(smooth([(186, 198), (214, 206), (246, 218), (284, 226), (322, 220), (350, 206), (372, 186),
                              (392, 190), (392, 280), (180, 280)]), C["belly"]))
    items.append(line([(190, 203), (214, 210), (246, 222), (284, 230), (322, 224), (350, 210), (372, 190)], C["belly_sh"], 1.2))
    for x0, y0, x1, y1 in ((236, 228, 232, 246), (258, 233, 256, 256), (282, 236, 282, 262), (306, 233, 309, 264),
                           (330, 226, 336, 258), (352, 214, 362, 246), (368, 200, 380, 224)):
        items.append(line([(x0, y0), ((x0 + x1) / 2 + 1, (y0 + y1) / 2), (x1, y1)], C["belly_sh"], 1.0))
    # tiger stripes
    for x, top, length, lean in ((206, 146, 30, -4), (232, 136, 38, -3), (262, 130, 44, -2), (294, 132, 42, 0),
                                 (322, 142, 34, 2), (346, 152, 22, 4)):
        items.append(path(smooth([(x - 7, top - 8, True), (x + lean * 0.5 - 2, top + length * 0.55),
                                  (x + lean, top + length, True), (x + lean * 0.5 + 3, top + length * 0.5),
                                  (x + 8, top - 8, True)]), C["stripe"]))
    # shoulder / ribcage contour
    items.append(line([(330, 168), (346, 190), (350, 214)], C["back"], 1.3))
    items.append(line([(214, 196), (234, 214), (250, 222)], C["back"], 1.1))
    # battle scars: three raked claw marks across the flank
    for k in range(3):
        items.append(line([(276 + k * 7, 170 + k * 2), (290 + k * 7, 186 + k * 2), (298 + k * 7, 204 + k * 2)],
                          C["scar"], 1.6))
    body = clipped("clip-torso", sil, items)
    # spine scutes poke above the silhouette: drawn over the clip
    for x, y, r in ((214, 145, 3.4), (238, 136, 3.8), (262, 131, 4.0), (286, 130, 4.0), (310, 134, 3.8),
                    (332, 142, 3.4)):
        body.append(ellipse(x, y, r * 1.25, r * 0.8, C["scute"], INK, 0.8))
    part("torso", "Torso", "torso", "torso", 34, body)


# ---- neck ------------------------------------------------------------------
NECK = [(330, 150), (352, 134), (376, 114), (396, 104), (414, 118), (416, 146), (406, 166), (392, 186),
        (382, 210), (356, 214), (338, 186)]


def neck_part():
    sil = smooth(NECK)
    ink("neck", "neck", 25, sil)
    items = [path(sil, C["body"])]
    items.append(path(smooth([(326, 146), (350, 128), (376, 108), (398, 98), (402, 108), (380, 120), (356, 140),
                              (336, 158)]), C["light"]))
    # throat
    items.append(path(smooth([(420, 140), (414, 158), (402, 176), (390, 196), (384, 214), (420, 230), (440, 160)]),
                      C["belly"]))
    items.append(line([(412, 150), (404, 168), (392, 188), (386, 206)], C["belly_sh"], 1.1))
    for y in (156, 168, 180, 192):
        x = 412 - (y - 150) * 0.55
        items.append(line([(x - 1, y), (x + 9, y + 3)], C["belly_sh"], 0.9))
    for x, y in ((350, 140), (372, 122)):
        items.append(path(smooth([(x - 7, y - 10, True), (x - 1, y + 14), (x + 2, y + 24, True), (x + 4, y + 10),
                                  (x + 9, y - 10, True)]), C["stripe"]))
    # neck folds
    items.append(line([(388, 130), (392, 146), (390, 160)], C["back"], 1.0))
    body = clipped("clip-neck", sil, items)
    for x, y, r in ((352, 141, 3.2), (370, 126, 3.0), (386, 113, 2.8)):
        body.append(ellipse(x, y, r * 1.2, r * 0.8, C["scute"], INK, 0.8, rot=-40))
    part("neck", "Neck", "neck", "neck", 35, body)


# ---- head ------------------------------------------------------------------
SKULL = [
    (384, 132), (386, 112), (398, 94), (418, 86), (432, 84, True), (440, 80), (447, 86, True), (466, 92),
    (490, 100), (504, 107), (510, 117), (509, 130), (503, 139), (488, 141), (462, 142), (436, 144),
    (418, 147), (410, 158), (398, 158), (388, 148),
]
UPPER_TEETH = [(424, 146, 7, 4.2), (432, 145.5, 9, 5), (441, 145, 11, 5.6), (450, 144.6, 10, 5.4),
               (459, 144.2, 9, 5), (468, 143.6, 8, 4.6), (477, 143, 9, 4.6), (486, 142.2, 7, 4.2),
               (494, 141.4, 6, 3.6), (501, 140, 5, 3.2)]


def head_part():
    svg.transform(HEAD_SCALE)
    sil = smooth(SKULL)
    ink("head", "head", 27, sil)
    items = [path(sil, C["body"])]
    # crown/snout highlight
    items.append(path(smooth([(392, 100), (412, 88), (440, 84), (468, 92), (494, 100), (508, 110), (506, 118),
                              (486, 108), (462, 100), (436, 94), (412, 98), (396, 110)]), C["light"]))
    # pale lip along the upper jaw
    items.append(path(smooth([(416, 146), (440, 142), (466, 139), (490, 137), (506, 131), (512, 150), (410, 156)]),
                      C["belly"]))
    items.append(line([(418, 143), (440, 139.5), (466, 137), (490, 135), (505, 129)], C["belly_sh"], 1.0))
    # cheek / jaw muscle behind the eye
    items.append(line([(398, 114), (410, 120), (414, 134), (408, 146)], C["back"], 1.4))
    items.append(line([(390, 126), (398, 136), (398, 148)], C["back"], 1.1))
    # antorbital fenestra (a sunken window ahead of the eye)
    items.append(path(smooth([(440, 108), (452, 101), (468, 103), (474, 112), (462, 119), (446, 118)]), C["back"]))
    items.append(line([(444, 116), (458, 117), (470, 113)], C["light"], 0.9))
    # nostril
    items.append(ellipse(498, 112, 4.2, 2.6, C["nostril"], rot=-18))
    # eye socket shadow and heavy brow
    items.append(ellipse(428, 106, 10, 8, C["back"]))
    items.append(path(smooth([(414, 98, True), (428, 92), (444, 96, True), (436, 100), (422, 101)]), C["stripe"]))
    # stripes and scars
    for x, y in ((404, 98), (416, 90)):
        items.append(path(smooth([(x - 5, y - 8, True), (x, y + 10), (x + 1, y + 16, True), (x + 3, y + 6),
                                  (x + 6, y - 8, True)]), C["stripe"]))
    items.append(line([(456, 90), (464, 104), (466, 116)], C["scar"], 1.5))
    items.append(line([(464, 92), (471, 104)], C["scar"], 1.3))
    # snout scales
    for x, y in ((476, 100), (484, 103), (492, 106), (480, 108), (488, 112), (470, 96)):
        items.append(ellipse(x, y, 1.4, 1.0, C["light"]))
    # lip line + teeth
    items.append(line([(414, 148), (436, 145), (462, 143), (488, 141), (503, 139), (509, 131)], INK, 1.4))
    body = clipped("clip-head", sil, items)
    # brow horn (lacrimal) above the eye: rusty, pokes out of the silhouette
    horn = smooth([(421, 91, True), (427, 83), (434, 77), (442, 72, True), (441, 80), (446, 91, True)])
    body.append(path(horn, C["horn"], INK, LW))
    body.append(line([(429, 85), (436, 78), (440, 75)], C["horn_hi"], 1.2))
    # postorbital boss
    body.append(path(smooth([(408, 96, True), (412, 88), (420, 86), (418, 94, True)]), C["horn"], INK, 0.9))
    for x, y, h, w in UPPER_TEETH:
        body.append(tooth(x, y, h, w, True))
    part("head", "Head", "head", "head", 48, body)


# ---- jaw + mouth -----------------------------------------------------------
JAW = [(400, 150), (404, 142, True), (416, 146), (440, 145), (466, 144), (490, 142), (504, 140, True),
       (504, 148), (495, 157), (470, 166), (440, 172), (414, 172), (402, 164)]
LOWER_TEETH = [(430, 146, 6, 4.0), (440, 145.6, 8, 4.6), (450, 145.2, 9, 5), (460, 144.8, 8, 4.8),
               (470, 144.2, 7, 4.4), (480, 143.4, 6, 4.0), (490, 142.4, 5, 3.4)]


def jaw_part():
    svg.transform(HEAD_SCALE)
    sil = smooth(JAW)
    ink("jaw", "jaw", 26, sil)
    items = [path(sil, C["body"])]
    items.append(path(smooth([(398, 158), (420, 158), (450, 156), (480, 150), (506, 143), (506, 170), (398, 176)]),
                      C["belly"]))
    items.append(line([(402, 158), (430, 159), (460, 156), (488, 150), (502, 145)], C["belly_sh"], 1.0))
    items.append(line([(410, 148.5), (440, 148), (470, 146.5), (498, 143.5)], C["belly"], 2.2))
    for x in (424, 444, 464, 482):
        items.append(line([(x, 160 - (x - 424) * 0.12), (x + 3, 166 - (x - 424) * 0.14)], C["belly_sh"], 0.9))
    jaw_body = clipped("clip-jaw", sil, items)
    # The mouth's inside rides on the jaw: hidden behind the head when shut.
    roof = smooth([(414, 147, True), (440, 146), (470, 144), (500, 141, True), (496, 132), (470, 130), (440, 131),
                   (420, 136)])
    tongue = smooth([(418, 146, True), (440, 143), (462, 141), (476, 141), (472, 146), (450, 147)])
    teeth = [tooth(x, y, h, w, False) for x, y, h, w in LOWER_TEETH]
    body = [path(roof, C["mouth"]), path(tongue, C["tongue"], C["mouth2"], 0.8)] + teeth + jaw_body
    part("jaw", "Lower Jaw", "jaw", "jaw", 44, body)


def mouth_floor_part():
    svg.transform(HEAD_SCALE)
    floor = smooth([(418, 147, True), (440, 146), (470, 144), (500, 142, True), (496, 148), (470, 158), (440, 163),
                    (420, 160)])
    gum = smooth([(418, 146, True), (440, 145), (470, 143), (500, 141, True), (497, 145), (470, 147), (440, 149),
                  (420, 150)])
    body = [path(floor, C["mouth"]), path(gum, C["gum"]),
            line([(424, 156), (446, 157), (470, 153)], C["mouth2"], 1.6)]
    part("mouth-floor", "Mouth Floor", "mouth_floor", "head", 42, body)


# ---- eyes ------------------------------------------------------------------
EYE = (428.0, 105.0)


def eye_parts():
    svg.transform(HEAD_SCALE)
    x, y = EYE
    base = ellipse(x, y, 8.5, 7.0, C["back"])
    lid_shape = smooth([(x - 9, y + 1), (x - 4, y - 6.5), (x + 5, y - 6.5), (x + 9, y), (x + 4, y + 5), (x - 4, y + 5)])
    # open: amber, slit pupil, rim light
    open_ = [base, ellipse(x, y, 6.4, 5.0, C["eye"], INK, 1.0), ellipse(x - 1.0, y - 1.2, 3.6, 2.2, C["eye_rim"]),
             ellipse(x + 0.8, y, 1.5, 4.3, C["pupil"]), ellipse(x - 2.4, y - 1.8, 1.0, 0.8, "#fffbe8"),
             line([(x - 8, y - 3), (x - 1, y - 7), (x + 8, y - 4)], INK, 1.3)]
    angry = [base, ellipse(x, y + 0.5, 6.4, 4.6, C["eye"], INK, 1.0),
             ellipse(x + 0.8, y + 0.8, 1.3, 3.6, C["pupil"]),
             path(smooth([(x - 10, y - 8, True), (x + 9, y - 1, True), (x + 9, y - 9, True)]), C["stripe"]),
             line([(x - 9, y - 6.5), (x + 9, y + 0.5)], INK, 1.6),
             ellipse(x - 3.4, y + 1.6, 0.9, 0.7, "#fffbe8")]
    shut = [base, path(lid_shape, C["body"], INK, 0.9), line([(x - 7, y + 0.5), (x, y + 3.2), (x + 7, y + 0.5)], INK, 1.4)]
    dead = [base, path(lid_shape, C["body"], INK, 0.9),
            line([(x - 5, y - 4), (x + 5, y + 4)], INK, 1.8), line([(x - 5, y + 4), (x + 5, y - 4)], INK, 1.8)]
    part("eye-open", "Eye - Open", "eye_open", "head", 50, open_, ' data-rig-opacity="eye.open" data-rig-default="1"')
    part("eye-angry", "Eye - Angry", "eye_angry", "head", 50, angry, ' data-rig-opacity="eye.angry"')
    part("eye-shut", "Eye - Shut", "eye_shut", "head", 50, shut, ' data-rig-opacity="eye.shut"')
    part("eye-dead", "Eye - Dead", "eye_dead", "head", 50, dead, ' data-rig-opacity="eye.dead"')


# ---- legs ------------------------------------------------------------------
def leg_parts(side):
    near = side == "near"
    col = C if near else {**C, **FAR}
    dx = 0.0 if near else -16.0
    zb = 70 if near else 10
    hip, knee, ankle = J[f"{side}_hip"], J[f"{side}_knee"], J[f"{side}_ankle"]

    def S(pts):
        return [(p[0] + dx, p[1]) + tuple(p[2:]) for p in pts]

    # thigh: a big drumstick from hip to knee
    thigh_pts = S([(226, 176), (250, 166), (276, 170), (296, 190), (304, 220), (302, 248), (296, 266),
                   (284, 274), (272, 268), (262, 252), (244, 232), (226, 214), (218, 194)])
    thigh = smooth(thigh_pts)
    hi = smooth(S([(234, 174), (258, 166), (282, 174), (298, 194), (302, 214), (292, 206), (276, 188), (254, 180)]))
    t_items = [path(thigh, col["body"]), path(hi, col["light"]),
               line(S([(296, 222), (290, 244), (280, 262)]), C["back"] if near else C["stripe"], 1.3),
               line(S([(236, 216), (252, 238), (266, 258)]), C["back"] if near else C["stripe"], 1.0)]
    for x, y in ((250, 182), (270, 186)):
        t_items.append(path(smooth(S([(x - 6, y - 14, True), (x, y + 8), (x + 2, y + 18, True), (x + 4, y + 6),
                                      (x + 8, y - 14, True)])), col["stripe"]))
    # The thigh's lower edge is a silhouette (ink); its top is a muscle
    # contour on the flank, drawn softer so the leg grows out of the body.
    t_body = clipped(f"clip-{side}-thigh", thigh, t_items) + [
        path(smooth_run(thigh_pts, 3, 9), "none", INK, 2 * OW),
        path(smooth_run(thigh_pts, 12, 4), "none", C["back"] if near else C["stripe"], 1.6),
    ]
    part(f"{side}-thigh", f"Thigh - {side}", f"{side}_thigh", f"{side}_thigh", zb + 4, t_body)

    # shin
    shin = capsule(knee, ankle, 13.0, 9.0)
    s_items = [path(shin, col["body"]),
               line([(knee[0] + 6, knee[1] + 6), (ankle[0] + 7, ankle[1] - 4)], col["light"], 2.2)]
    for k in range(4):
        t = 0.45 + k * 0.13
        cx = knee[0] + (ankle[0] - knee[0]) * t
        cy = knee[1] + (ankle[1] - knee[1]) * t
        s_items.append(line([(cx - 9, cy - 1), (cx + 9, cy + 2)], col["stripe"] if k == 0 else C["back"], 0.9))
    s_body = clipped(f"clip-{side}-shin", shin, s_items) + [path(shin, "none", INK, 2 * OW)]
    part(f"{side}-shin", f"Shin - {side}", f"{side}_shin", f"{side}_shin", zb + 2, s_body)

    # foot: metatarsus down to the ball, three forward toes, a dewclaw
    ax, ay = ankle
    foot = smooth([(ax - 9, ay - 2), (ax - 2, ay - 10), (ax + 9, ay - 4), (ax + 16, ay + 14), (ax + 26, ay + 22),
                   (ax + 46, ay + 26), (ax + 52, ay + 31), (ax + 48, ay + 35, True), (ax + 10, ay + 35, True),
                   (ax - 1, ay + 32), (ax - 6, ay + 16)])
    f_items = [path(foot, col["body"]),
               line([(ax + 4, ay - 4), (ax + 12, ay + 14), (ax + 26, ay + 21)], col["light"], 2.0),
               line([(ax + 18, ay + 28), (ax + 40, ay + 29)], C["back"], 1.0)]
    for k, yy in enumerate((ay + 6, ay + 12, ay + 18)):
        f_items.append(line([(ax - 5, yy), (ax + 8 + k * 2, yy + 2)], C["back"], 0.9))
    f_body = clipped(f"clip-{side}-foot", foot, f_items) + [path(foot, "none", INK, 2 * OW)]
    # toe claws (the near toe forward, the inner toe behind it), dewclaw
    for tx, ty, s in ((ax + 50, ay + 30, 1.0), (ax + 36, ay + 32, 0.85), (ax + 22, ay + 33, 0.75)):
        claw = smooth([(tx - 2 * s, ty - 4 * s, True), (tx + 6 * s, ty - 2 * s), (tx + 9 * s, ty + 4.5 * s, True),
                       (tx + 3 * s, ty + 2 * s), (tx - 2 * s, ty + 3 * s, True)])
        f_body.append(path(claw, col["claw"], INK, 0.9))
    f_body.append(path(smooth([(ax - 4, ay + 18, True), (ax - 10, ay + 22), (ax - 11, ay + 27, True),
                               (ax - 6, ay + 25), (ax - 2, ay + 23, True)]), col["claw"], INK, 0.8))
    part(f"{side}-foot", f"Foot - {side}", f"{side}_foot", f"{side}_foot", zb, f_body)


# ---- arms ------------------------------------------------------------------
def arm_parts(side):
    near = side == "near"
    col = C if near else {**C, **FAR}
    zb = 62 if near else 16
    sh, el, wr = J[f"{side}_shoulder"], J[f"{side}_elbow"], J[f"{side}_wrist"]
    up = capsule(sh, el, 6.5, 4.8)
    part(f"{side}-arm-u", f"Upper Arm - {side}", f"{side}_arm_u", f"{side}_arm_u", zb,
         [path(up, col["body"], INK, 2 * OW), line([(sh[0] + 2, sh[1] - 2), (el[0] + 3, el[1] - 2)], col["light"], 1.6)])
    lo = capsule(el, wr, 4.6, 3.6)
    wx, wy = wr
    claws = []
    for k, (cx, cy) in enumerate(((wx + 2, wy - 1), (wx + 1, wy + 2.5))):
        claws.append(path(smooth([(cx - 2, cy - 2.5, True), (cx + 5, cy - 1.5), (cx + 7, cy + 4, True),
                                  (cx + 3, cy + 1.5), (cx - 1, cy + 2.5, True)]), col["claw"], INK, 0.8))
    part(f"{side}-arm-l", f"Forearm - {side}", f"{side}_arm_l", f"{side}_arm_l", zb + 1,
         claws + [path(lo, col["body"], INK, 2 * OW), ellipse(wx, wy, 4.2, 3.6, col["body"], INK, 1.0)])


def draw() -> str:
    svg.configure(dx=10.0, dy=16.0, ink=INK, ow=OW, colors=C)
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
    svg.transform(None)
    arm_parts("near")
    leg_parts("near")
    return svg.document(
        size=(W, H),
        design="trex-enemy-side-v2",
        layer_id="trex-side",
        label="T-Rex - Side Right",
        comment=[
            "  <!-- The Tyrant King, a T-rex boss in side view, facing right. The rig publishes",
            "       this 640x400 drawing at 0.75 px per unit (a 480x300 sprite frame); the",
            "       ground is y=372.",
            "       Each part is a layer with a data-rig-part name; the rig in",
            "       targets/characters/rigged/trex_enemy/ turns these parts about their joints.",
            "       *_ink layers are each body part's silhouette grown by the outline width,",
            "       painted beneath every body fill so tail, torso, neck, head and jaw read as",
            "       one outlined silhouette with no seams at their joints. The eye states sit",
            "       on top of each other: the rig shows one at a time (data-rig-opacity).",
            "       The hidden Rig Joints layer marks every joint the skeleton is built on. -->",
        ],
        joints=svg.joints_layer(J, {"jaw": HEAD_SCALE, "snout": HEAD_SCALE}),
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    Path(sys.argv[1]).write_text(draw())
