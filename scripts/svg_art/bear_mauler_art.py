#!/usr/bin/env python3
"""How the bear mauler's SVG was first drawn (reference, not authority).

``data/characters/bear_mauler/bear_mauler.svg`` owns the art and may have been
edited since; this script reproduces the drawing as it was first committed
(less the rig catalog ``scripts/build_bear_mauler_rig.py`` installs). Keep it
as a worked example for drawing a new quadruped with ``svgkit``: shaggy fur
from ``fringe``, limbs whose top edge is a soft muscle contour.

    uv run python scripts/svg_art/bear_mauler_art.py OUT.svg

Drawn straight in SVG units: a 560x400 SVG whose ground is y=372.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import svgkit as svg
from svgkit import capsule, clipped, ellipse, fringe, ink, line, part, path, smooth, smooth_run, tooth

W, H = 560, 400
INK = "#1a120c"
OW = 2.2  # half the silhouette ink width

C = dict(
    body="#6e4a2e",
    light="#8d6440",
    back="#4a3020",
    stripe="#3a2416",
    grizzle="#cdb084",
    grizzle_d="#a88a60",
    belly="#5a3b24",
    belly_sh="#47301d",
    muzzle="#b88a5c",
    muzzle_l="#d4ab7c",
    nose="#1a1412",
    claw="#ece2c8",
    claw_sh="#b5a785",
    pad="#2a1c14",
    eye="#f0a830",
    eye_rim="#ffd27a",
    pupil="#140c06",
    mask="#3a2416",
    mouth="#4a161c",
    mouth2="#6b2028",
    gum="#b04d58",
    tongue="#c8707a",
    tooth="#f4ecd4",
    scar="#d9a090",
)
FAR = dict(body="#553823", light="#6d4c31", back="#3a2618", grizzle="#a88a60", claw="#cfc5ab", belly="#46301d")

J = dict(
    pelvis=(196.0, 236.0),
    neck_base=(340.0, 206.0),
    head=(388.0, 222.0),
    jaw=(410.0, 250.0),
    snout=(476.0, 244.0),
    near_hip=(204.0, 240.0),
    near_knee=(226.0, 292.0),
    near_ankle=(208.0, 350.0),
    far_hip=(190.0, 236.0),
    far_knee=(212.0, 288.0),
    far_ankle=(192.0, 350.0),
    near_shoulder=(334.0, 236.0),
    near_elbow=(322.0, 292.0),
    near_wrist=(334.0, 350.0),
    far_shoulder=(320.0, 232.0),
    far_elbow=(308.0, 288.0),
    far_wrist=(318.0, 350.0),
)


def tufts(points, color, w=1.4, length=7.0, angle=110.0):
    """Short fur strokes."""
    out = []
    a = math.radians(angle)
    for x, y in points:
        out.append(line([(x, y), (x + math.cos(a) * length * 0.5 + 1.5, y + math.sin(a) * length * 0.5),
                         (x + math.cos(a) * length, y + math.sin(a) * length)], color, w))
    return out


# ---- torso -----------------------------------------------------------------
TORSO = [(150, 256), (140, 226), (150, 200), (176, 184), (212, 180), (246, 180), (276, 170), (300, 158),
         (322, 156), (342, 166), (358, 186), (366, 214), (362, 248), (348, 272), (316, 286), (276, 290),
         (236, 288), (196, 282), (166, 274)]


def torso_part():
    sil = smooth(TORSO)
    ink("torso", "torso", 24, sil)
    items = [path(sil, C["body"])]
    # back light, grizzled hump
    items.append(path(smooth([(146, 206), (176, 190), (214, 186), (248, 186), (280, 174), (304, 164), (326, 162),
                              (346, 174), (330, 184), (304, 182), (276, 192), (240, 198), (200, 198), (160, 214)]),
                      C["light"]))
    items.append(path(smooth([(264, 176), (288, 162), (312, 156), (336, 162), (348, 176), (326, 178), (300, 178),
                              (278, 186)]), C["grizzle_d"]))
    items.append(path(smooth([(276, 172), (296, 162), (318, 158), (338, 166), (322, 170), (300, 170)]), C["grizzle"]))
    # underside darker
    items.append(path(smooth([(150, 262), (196, 270), (240, 276), (280, 278), (318, 272), (350, 258), (370, 270),
                              (360, 310), (140, 310)]), C["belly"]))
    items += tufts([(180, 210), (204, 222), (232, 206), (258, 222), (286, 204), (312, 214), (300, 240), (270, 248),
                    (236, 244), (206, 252), (176, 240), (330, 236), (344, 206)], C["back"], 1.6, 9, 110)
    items += tufts([(292, 172), (308, 166), (324, 168)], C["light"], 1.4, 7, 120)
    # shoulder scars from an old fight
    for k in range(3):
        items.append(line([(306 + k * 8, 196 + k * 3), (318 + k * 8, 214 + k * 3), (322 + k * 8, 232 + k * 3)],
                          C["scar"], 2.2))
    body = clipped("clip-torso", sil, items)
    # shaggy fringe: grizzled along the back, dark under the belly, a tail nub
    body = fringe([(148, 204), (178, 186), (214, 182), (248, 182), (278, 170), (302, 158), (324, 156), (344, 168)],
                  20, 5.5, 1.1, C["grizzle_d"], None, ow=1.4, flip=False, jitter=0.35, inset=10) + body
    body = fringe([(352, 262), (320, 282), (280, 288), (240, 286), (200, 280), (168, 272)], 10, 9.0, 0.5,
                  C["belly"], None, ow=1.4, flip=False, jitter=0.3, inset=10) + body
    body = [path(smooth([(152, 210), (134, 206), (128, 216), (138, 228), (152, 226)]), C["back"], INK, 2.0)] + body
    part("torso", "Torso", "torso", "torso", 34, body)


# ---- neck ------------------------------------------------------------------
NECK = [(326, 172), (352, 172), (378, 190), (398, 210), (406, 238), (398, 262), (374, 278), (346, 272),
        (326, 244), (320, 204)]


def neck_part():
    sil = smooth(NECK)
    ink("neck", "neck", 25, sil)
    items = [path(sil, C["body"]),
             path(smooth([(326, 168), (352, 166), (380, 184), (396, 200), (382, 200), (356, 186), (330, 184)]),
                  C["grizzle_d"]),
             path(smooth([(380, 262), (398, 250), (414, 260), (400, 290), (360, 296)]), C["belly"])]
    items += tufts([(350, 196), (366, 212), (380, 232), (360, 240), (344, 222)], C["back"], 1.6, 9, 100)
    body = clipped("clip-neck", sil, items)
    body = fringe([(402, 254), (390, 270), (370, 280), (348, 276)], 6, 8.0, 0.4, C["belly"], None, ow=1.4,
                  flip=False, jitter=0.3, inset=10) + body
    part("neck", "Neck", "neck", "neck", 35, body)


# ---- head ------------------------------------------------------------------
SKULL = [(378, 222), (380, 204), (390, 190), (406, 184), (424, 186), (440, 194), (452, 206), (464, 220),
         (474, 228), (481, 236), (479, 246, True), (468, 253), (450, 255), (430, 257), (412, 258), (398, 253),
         (386, 240)]


def head_part():
    sil = smooth(SKULL)
    ink("head", "head", 27, sil)
    items = [path(sil, C["body"])]
    items.append(path(smooth([(384, 204), (394, 190), (410, 186), (430, 190), (442, 200), (424, 198), (404, 200),
                              (390, 212)]), C["light"]))
    # muzzle
    items.append(path(smooth([(436, 214), (456, 214), (476, 226), (486, 240), (480, 256), (440, 262), (424, 248),
                              (426, 228)]), C["muzzle"]))
    items.append(path(smooth([(442, 218), (460, 218), (476, 230), (470, 236), (452, 232), (440, 228)]), C["muzzle_l"]))
    items.append(line([(426, 256), (446, 254.5), (466, 253), (477, 248)], INK, 1.8))
    items.append(line([(470, 240), (468, 248)], INK, 1.4))
    # brow and cheek fur
    items.append(path(smooth([(412, 204, True), (424, 198), (438, 204, True), (426, 206)]), C["stripe"]))
    items += tufts([(392, 222), (400, 236), (410, 228), (388, 236)], C["back"], 1.5, 8, 120)
    items.append(line([(448, 206), (456, 214), (458, 224)], C["scar"], 2.0))
    body = clipped("clip-head", sil, items)
    # ears behind the skull: far ear darker, near ear torn
    far_ear = smooth([(410, 188), (410, 174), (420, 168), (430, 174), (430, 188)])
    near_ear = smooth([(388, 196), (386, 180), (393, 172, True), (398, 177, True), (402, 172, True), (410, 178),
                       (410, 194)])
    body = [path(far_ear, FAR["body"], INK, 2.0), path(near_ear, C["body"], INK, 2.0),
            path(smooth([(392, 192), (392, 182), (398, 180), (404, 182), (404, 192)]), C["muzzle"])] + body
    body.append(ellipse(474, 237, 7.5, 5.5, C["nose"], INK, 1.2, rot=-12))
    body.append(ellipse(472, 234, 2.6, 1.4, "#5a4a44", rot=-12))
    # canines and incisors under the lip
    for x, y, h, w in ((462, 253.5, 9, 5.0), (434, 256.5, 6, 4.0), (470, 252, 4, 3.0)):
        body.append(tooth(x, y, h, w, True, curve=0.8))
    part("head", "Head", "head", "head", 48, body)


JAW = [(396, 256), (404, 248, True), (428, 255), (450, 254), (468, 252, True), (468, 259), (454, 268), (428, 274),
       (408, 272), (398, 264)]


def jaw_part():
    sil = smooth(JAW)
    ink("jaw", "jaw", 26, sil)
    items = [path(sil, C["muzzle"]),
             path(smooth([(398, 266), (424, 268), (452, 262), (472, 256), (472, 280), (398, 280)]), C["muzzle_l"]),
             line([(406, 256), (430, 258), (452, 257), (466, 255)], C["muzzle_l"], 2.2)]
    jaw_body = clipped("clip-jaw", sil, items)
    roof = smooth([(410, 256, True), (432, 256), (452, 255), (466, 253, True), (462, 240), (440, 238), (420, 242)])
    tongue = smooth([(414, 255, True), (432, 252), (448, 251), (456, 253), (450, 256), (430, 257)])
    teeth = [tooth(x, y, h, w, False, curve=0.8) for x, y, h, w in ((456, 254, 8, 4.6), (436, 256, 5, 3.6))]
    part("jaw", "Lower Jaw", "jaw", "jaw", 44,
         [path(roof, C["mouth"]), path(tongue, C["tongue"], C["mouth2"], 1.0)] + teeth + jaw_body)


def mouth_floor_part():
    floor = smooth([(412, 256, True), (432, 256), (452, 255), (466, 253, True), (462, 260), (446, 266), (426, 270),
                    (412, 266)])
    gum = smooth([(412, 255, True), (432, 255), (452, 254), (466, 252, True), (462, 256), (446, 258), (426, 259),
                  (412, 259)])
    part("mouth-floor", "Mouth Floor", "mouth_floor", "head", 42,
         [path(floor, C["mouth"]), path(gum, C["gum"]), line([(420, 264), (440, 265), (456, 261)], C["mouth2"], 1.6)])


EYE = (428.0, 212.0)


def eye_parts():
    x, y = EYE
    base = ellipse(x, y, 6.5, 5.5, C["mask"])
    lid = smooth([(x - 6.5, y + 1), (x - 3, y - 4.5), (x + 3, y - 4.5), (x + 6.5, y), (x + 3, y + 4), (x - 3, y + 4)])
    open_ = [base, ellipse(x, y, 4.4, 3.8, C["eye"], INK, 1.3), ellipse(x + 0.6, y, 2.2, 2.4, C["pupil"]),
             ellipse(x - 1.4, y - 1.4, 0.9, 0.8, "#ffffff"), line([(x - 7, y - 3), (x, y - 6), (x + 7, y - 4)], INK, 2.0)]
    angry = [base, ellipse(x, y + 0.6, 4.4, 3.2, C["eye"], INK, 1.3), ellipse(x + 0.6, y + 0.8, 2.0, 2.0, C["pupil"]),
             path(smooth([(x - 8, y - 7, True), (x + 7, y - 0.5, True), (x + 7, y - 8, True)]), C["stripe"]),
             line([(x - 7, y - 5), (x + 7, y + 0.5)], INK, 2.2), ellipse(x - 1.6, y + 0.8, 0.8, 0.6, "#ffffff")]
    shut = [base, path(lid, C["body"], INK, 1.2), line([(x - 5, y + 0.5), (x, y + 2.6), (x + 5, y + 0.5)], INK, 2.0)]
    dead = [base, path(lid, C["body"], INK, 1.2), line([(x - 4, y - 3), (x + 4, y + 3)], INK, 2.2),
            line([(x - 4, y + 3), (x + 4, y - 3)], INK, 2.2)]
    part("eye-open", "Eye - Open", "eye_open", "head", 50, open_, ' data-rig-opacity="eye.open" data-rig-default="1"')
    part("eye-angry", "Eye - Angry", "eye_angry", "head", 50, angry, ' data-rig-opacity="eye.angry"')
    part("eye-shut", "Eye - Shut", "eye_shut", "head", 50, shut, ' data-rig-opacity="eye.shut"')
    part("eye-dead", "Eye - Dead", "eye_dead", "head", 50, dead, ' data-rig-opacity="eye.dead"')


# ---- legs ------------------------------------------------------------------
def paw(ax, ay, col, claw_len, fore):
    """A plantigrade paw from the ankle/wrist at (ax, ay) to the ground (y=372)."""
    if fore:
        pts = [(ax - 12, ay - 4), (ax - 2, ay - 12), (ax + 12, ay - 6), (ax + 20, ay + 6), (ax + 30, ay + 13),
               (ax + 34, ay + 20), (ax + 30, ay + 22, True), (ax - 10, ay + 22, True), (ax - 14, ay + 12)]
        toes = [(ax + 32, ay + 18), (ax + 25, ay + 20), (ax + 17, ay + 21)]
    else:
        pts = [(ax - 14, ay - 2), (ax - 2, ay - 10), (ax + 10, ay - 4), (ax + 22, ay + 8), (ax + 36, ay + 14),
               (ax + 40, ay + 20), (ax + 36, ay + 22, True), (ax - 16, ay + 22, True), (ax - 18, ay + 12)]
        toes = [(ax + 38, ay + 18), (ax + 31, ay + 20), (ax + 24, ay + 21)]
    sil = smooth(pts)
    items = [path(sil, col["body"]), line([(ax - 6, ay - 4), (ax + 14, ay + 4)], col["light"], 2.6),
             path(smooth([(ax - 14, ay + 18), (ax + 30, ay + 18), (ax + 36, ay + 24), (ax - 14, ay + 24)]), C["pad"])]
    out = clipped(f"clip-paw-{ax}-{int(fore)}", sil, items) + [path(sil, "none", INK, 2 * OW)]
    for k, (tx, ty) in enumerate(toes):
        L = claw_len * (1.0 - 0.15 * k)
        claw = smooth([(tx - 2, ty - 3, True), (tx + L * 0.55, ty - 1.5), (tx + L, ty + 3.5, True),
                       (tx + L * 0.45, ty + 1.2), (tx - 1, ty + 1.8, True)])
        out.append(path(claw, col["claw"], INK, 1.2))
    return out


def leg_parts(side, kind):
    near = side == "near"
    col = C if near else {**C, **FAR}
    zb = (70 if kind == "hind" else 80) if near else (10 if kind == "hind" else 14)
    hip, knee, ankle = J[f"{side}_{'hip' if kind == 'hind' else 'shoulder'}"], \
        J[f"{side}_{'knee' if kind == 'hind' else 'elbow'}"], J[f"{side}_{'ankle' if kind == 'hind' else 'wrist'}"]
    upper, lower, foot = (f"{side}_{kind}_upper", f"{side}_{kind}_lower", f"{side}_{kind}_paw")
    hx, hy = hip
    kx, ky = knee
    if kind == "hind":
        # the haunch: a big rounded thigh from the rump to the knee
        up_pts = [(hx - 40, hy - 20), (hx - 10, hy - 42), (hx + 26, hy - 36), (hx + 40, hy - 4), (kx + 14, ky - 8),
                  (kx + 8, ky + 10), (kx - 8, ky + 12), (kx - 22, ky - 4), (hx - 36, hy + 18)]
    else:
        # the shoulder: a heavy wedge of muscle down to the elbow
        up_pts = [(hx - 22, hy - 30), (hx + 8, hy - 36), (hx + 30, hy - 20), (hx + 24, hy + 18), (kx + 14, ky - 4),
                  (kx + 10, ky + 12), (kx - 8, ky + 14), (kx - 16, ky - 4), (hx - 24, hy + 10)]
    up = smooth(up_pts)
    items = [path(up, col["body"]),
             path(smooth([(hx - 30, hy - 22), (hx - 6, hy - 38), (hx + 22, hy - 30), (hx + 30, hy - 12), (hx + 10, hy - 20),
                          (hx - 14, hy - 18)]), col["light"])]
    items += tufts([(hx - 10, hy - 4), (hx + 10, hy + 8), (kx - 4, ky - 18), (kx + 4, ky - 6)], col["back"], 1.6, 9, 100)
    body = clipped(f"clip-{upper}", up, items)
    body = fringe([(kx - 22, ky - 4), (kx - 8, ky + 12), (kx + 8, ky + 12)], 4, 7.0, 0.3, col["body"], None,
                  ow=1.4, flip=True, jitter=0.3, inset=8) + body
    # Only the limb's lower edge is a silhouette (ink); where it lies on the
    # body it is a muscle contour, drawn softer, so the limb grows out of it.
    body.append(path(smooth_run(up_pts, 3, 5), "none", INK, 2 * OW))
    body.append(path(smooth_run(up_pts, 8, 4), "none", col["back"], 2.0))
    part(f"{side}-{kind}-upper", f"{kind.title()} Upper - {side}", upper, upper, zb + 4, body)

    low = capsule(knee, ankle, 15.0 if kind == "fore" else 14.0, 11.5)
    l_items = [path(low, col["body"]), line([(kx + 6, ky + 4), (ankle[0] + 6, ankle[1] - 4)], col["light"], 2.6)]
    l_items += tufts([(kx - 4, ky + 14), (kx, ky + 30), (ankle[0] - 4, ankle[1] - 14)], col["back"], 1.5, 8, 100)
    l_body = clipped(f"clip-{lower}", low, l_items) + [path(low, "none", INK, 2 * OW)]
    part(f"{side}-{kind}-lower", f"{kind.title()} Lower - {side}", lower, lower, zb + 2, l_body)

    part(f"{side}-{kind}-paw", f"{kind.title()} Paw - {side}", foot, foot, zb,
         paw(ankle[0], ankle[1], col, 15.0 if kind == "fore" else 8.0, kind == "fore"))


def draw() -> str:
    svg.configure(dx=0.0, dy=0.0, ink=INK, ow=OW, colors=C)
    leg_parts("far", "hind")
    leg_parts("far", "fore")
    torso_part()
    neck_part()
    mouth_floor_part()
    jaw_part()
    head_part()
    eye_parts()
    leg_parts("near", "hind")
    leg_parts("near", "fore")
    return svg.document(
        size=(W, H),
        design="bear-mauler-side-v2",
        layer_id="bear-side",
        label="Bear - Side Right",
        comment=[
            "  <!-- The bear mauler: a battle-scarred grizzly in side view, facing right. The",
            "       rig publishes this 560x400 drawing at 0.36 px per unit (a 202x144 sprite",
            "       frame); the ground is y=372.",
            "       Each part is a layer with a data-rig-part name; the rig in",
            "       targets/characters/rigged/bear_mauler/ turns these parts about their joints.",
            "       *_ink layers are each body part's silhouette grown by the outline width,",
            "       painted beneath every body fill so torso, neck, head and jaw read as one",
            "       outlined silhouette with no seams at their joints. The eye states sit on",
            "       top of each other: the rig shows one at a time (data-rig-opacity).",
            "       The hidden Rig Joints layer marks every joint the skeleton is built on. -->",
        ],
        joints=svg.joints_layer(J),
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    Path(sys.argv[1]).write_text(draw())
