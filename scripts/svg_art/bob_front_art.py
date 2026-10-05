#!/usr/bin/env python3
"""How Bob's front-view SVG was first drawn (reference, not authority).

``data/characters/bob/bob_front.svg`` owns the art; this script reproduces it
as first committed (less the rig catalog ``scripts/build_bob_rig.py``
installs). It is the same Bob as ``bob_art.py`` (same palette, same wrench),
facing the viewer: the view the game shows when he stands and talks.

    uv run python scripts/svg_art/bob_front_art.py OUT.svg

Drawn on the side view's canvas (720x640 units, ground y=569, centre line
x=340) so both views publish into the same frame. ``near`` is the arm and leg
on the viewer's right (his left), which holds the wrench; ``far`` the other.
"""
from __future__ import annotations

import sys
from pathlib import Path

import svgkit as svg
from bob_art import C, INK, OW, outlined, wrench_body
from svgkit import capsule, clipped, ellipse, line, part, path, smooth

W, H = 720, 640
CX = 340.0

J = dict(
    pelvis=(340.0, 400.0),
    neck=(340.0, 282.0),
    head_top=(340.0, 194.0),
    near_shoulder=(376.0, 298.0),
    near_elbow=(388.0, 356.0),
    near_wrist=(392.0, 408.0),
    far_shoulder=(304.0, 298.0),
    far_elbow=(292.0, 356.0),
    far_wrist=(288.0, 408.0),
    near_hip=(360.0, 406.0),
    near_knee=(364.0, 480.0),
    near_ankle=(364.0, 550.0),
    far_hip=(320.0, 406.0),
    far_knee=(316.0, 480.0),
    far_ankle=(316.0, 550.0),
)


def mirror(points):
    """Points reflected across the centre line (a corner flag kept)."""
    return [(2 * CX - q[0],) + tuple(q[1:]) for q in points]


# ---- head ----------------------------------------------------------------------
FACE = [(306, 228), (312, 206), (340, 197), (368, 206), (374, 228), (372, 254), (362, 278), (340, 288),
        (318, 278), (308, 254)]


def head_part():
    sil = smooth(FACE)
    beard = smooth([(307, 238), (312, 256), (324, 266), (340, 268), (356, 266), (368, 256), (373, 238),
                    (376, 262), (368, 286), (340, 300), (312, 286), (304, 262)])
    items = [
        path(smooth([(344, 206), (366, 212), (372, 232), (360, 236), (350, 220)]), C["skin_light"]),
        path(smooth([(306, 236), (318, 238), (318, 262), (308, 256)]), C["skin_shadow"]),
        # the nose
        line([(336, 236), (334, 252), (340, 256), (346, 252)], C["skin_shadow"], 1.6),
        ellipse(336, 254, 1.8, 1.1, C["skin_shadow"]),
        ellipse(344, 254, 1.8, 1.1, C["skin_shadow"]),
    ]
    body = []
    for x in (301.0, 379.0):
        body.append(ellipse(x, 240, 6.5, 10.0, C["skin"], INK, 1.6))
        body.append(line([(x, 234), (x + (2 if x < CX else -2), 240), (x, 246)], C["skin_shadow"], 1.4))
    body += clipped("clip-front-head", sil, [path(sil, C["skin"])] + items)
    body.append(path(sil, "none", INK, 2 * OW))
    # the beard over the jaw (it hangs below the chin), then the mustache
    body.append(path(beard, C["beard"]))
    body.append(path(smooth([(304, 262), (312, 286), (340, 300), (368, 286), (376, 262)], closed=False), "none",
                     INK, 2 * OW))
    body.append(line([(318, 276), (330, 286), (340, 289)], C["beard_dark"], 1.6))
    body.append(line([(362, 276), (350, 286), (340, 289)], C["beard_dark"], 1.6))
    body.append(path(smooth([(324, 262), (332, 258), (340, 260), (348, 258), (356, 262), (350, 266), (340, 264),
                             (330, 266)]), C["beard_dark"], INK, 1.0))
    # hair: a tousled crown down to the sideburns
    hair = smooth([(302, 244), (300, 222), (306, 204), (318, 192, True), (328, 194), (338, 184, True), (346, 192),
                   (358, 186, True), (366, 196), (376, 204), (380, 222), (378, 244), (372, 228), (364, 214),
                   (350, 208), (340, 212), (330, 208), (316, 214), (308, 228)])
    body.append(path(hair, C["hair"], INK, 2 * OW))
    for pts in ([(310, 214), (320, 202), (332, 198)], [(350, 198), (362, 202), (370, 212)], [(336, 192), (342, 200)]):
        body.append(line(pts, C["hair_light"], 1.8))
    # brows
    for pts in ([(318, 224, True), (326, 220), (334, 223, True), (326, 226)],):
        body.append(path(smooth(pts), C["hair"], INK, 1.0))
        body.append(path(smooth(mirror(pts)), C["hair"], INK, 1.0))
    # safety glasses pushed up on the forehead: strap, two lenses, the bridge
    body.append(line([(302, 216), (316, 210)], C["leather_dark"], 4.0))
    body.append(line([(364, 210), (378, 216)], C["leather_dark"], 4.0))
    for lx in (327.0, 353.0):
        body.append(path(smooth([(lx - 12, 206), (lx, 202), (lx + 12, 206), (lx + 11, 214), (lx, 217), (lx - 11, 214)]),
                         C["glass"], INK, 1.8))
        body.append(line([(lx - 7, 206), (lx + 1, 204)], "#ffffff", 1.6))
    body.append(line([(339, 208), (341, 208)], INK, 2.4))
    part("head", "Head", "head", "head", 60, body)


def face_parts():
    eyes = ((327.0, 234.0), (353.0, 234.0))
    open_, shut, angry = [], [], []
    for x, y in eyes:
        open_ += [path(smooth([(x - 7, y), (x, y - 4.5), (x + 7, y), (x, y + 3.5)]), C["eye_white"], INK, 1.2),
                  ellipse(x, y - 0.2, 2.8, 3.2, C["iris"]), ellipse(x - 0.8, y - 1.3, 0.9, 0.9, "#ffffff")]
        shut.append(line([(x - 7, y + 0.5), (x, y + 2.8), (x + 7, y + 0.5)], INK, 1.8))
        angry += [path(smooth([(x - 7, y), (x, y - 3), (x + 7, y), (x, y + 3.5)]), C["eye_white"], INK, 1.2),
                  ellipse(x, y + 0.4, 2.8, 2.8, C["iris"])]
    part("eye-open", "Eye - Open", "eye_open", "head", 62, open_, ' data-rig-opacity="eye.open" data-rig-default="1"')
    part("eye-shut", "Eye - Shut", "eye_shut", "head", 62, shut, ' data-rig-opacity="eye.shut"')
    part("eye-angry", "Eye - Angry", "eye_angry", "head", 62, angry, ' data-rig-opacity="eye.angry"')
    mx, my = CX, 271.0
    closed = [line([(mx - 7, my), (mx, my + 1), (mx + 7, my)], INK, 1.8)]
    smile = [line([(mx - 8, my - 1), (mx, my + 3), (mx + 8, my - 1)], INK, 1.8)]
    open_m = [path(smooth([(mx - 8, my - 2), (mx + 8, my - 2), (mx + 5, my + 7), (mx - 5, my + 7)]), C["mouth"], INK,
                   1.4),
              path(smooth([(mx - 6, my - 1.5), (mx + 6, my - 1.5), (mx + 5, my + 0.8), (mx - 5, my + 0.8)]), C["tooth"]),
              path(smooth([(mx - 3, my + 5), (mx + 3, my + 5), (mx, my + 7)]), C["tongue"])]
    part("mouth-closed", "Mouth - Closed", "mouth_closed", "head", 63, closed,
         ' data-rig-opacity="mouth.closed" data-rig-default="1"')
    part("mouth-smile", "Mouth - Smile", "mouth_smile", "head", 63, smile, ' data-rig-opacity="mouth.smile"')
    part("mouth-open", "Mouth - Open", "mouth_open", "head", 63, open_m, ' data-rig-opacity="mouth.open"')


# ---- torso, satchel, hips --------------------------------------------------------
TORSO = [(298, 300), (318, 286), (340, 284), (362, 286), (382, 300), (388, 332), (386, 370), (380, 406), (300, 406),
         (294, 370), (292, 332)]


def torso_parts():
    sil = smooth(TORSO)
    vest_l = [(300, 300), (318, 288), (330, 292), (332, 340), (330, 380), (328, 406), (300, 406), (294, 370), (292, 332)]
    items = [
        path(smooth([(334, 292), (346, 292), (346, 404), (334, 404)]), C["shirt_light"]),
        path(smooth(vest_l), C["vest"], INK, 1.6),
        path(smooth(mirror(vest_l)), C["vest"], INK, 1.6),
        path(smooth([(292, 340), (304, 342), (306, 400), (296, 396)]), C["vest_dark"]),
        path(smooth([(376, 312), (386, 330), (384, 372), (374, 360)]), C["vest_light"]),
        # the hi-vis band round the vest, broken by the open front
        path(smooth([(290, 348, True), (330, 348, True), (330, 360, True), (290, 360, True)]), C["hi_vis"]),
        path(smooth([(350, 348, True), (390, 348, True), (390, 360, True), (350, 360, True)]), C["hi_vis"]),
        line([(292, 354), (329, 354)], C["hi_vis_dark"], 1.2),
        line([(351, 354), (388, 354)], C["hi_vis_dark"], 1.2),
        # pockets and a pen
        path(smooth([(306, 372, True), (322, 372, True), (322, 384, True), (306, 384, True)]), C["vest_dark"], INK, 1.2),
        path(smooth(mirror([(306, 372, True), (322, 372, True), (322, 384, True), (306, 384, True)])), C["vest_dark"],
             INK, 1.2),
        line([(312, 312), (313, 326)], C["steel"], 2.2),
        path(smooth([(306, 318, True), (322, 318, True), (322, 328, True), (306, 328, True)]), C["vest_dark"], INK, 1.2),
        # the shirt collar
        path(smooth([(326, 286, True), (340, 300), (354, 286, True), (350, 296), (340, 308, True), (330, 296)]),
             C["shirt_light"], INK, 1.2),
    ]
    body = [path(smooth([(328, 268), (352, 268), (354, 294), (326, 294)]), C["skin"], INK, 2 * OW)]  # the neck
    body += outlined(sil, C["shirt"], items, "clip-front-torso")
    # the satchel strap from his left shoulder across the chest to the far hip
    strap = [(368, 292), (350, 326), (318, 372), (300, 396)]
    body.append(line(strap, C["leather_dark"], 7.0))
    body.append(line(strap, C["leather"], 4.6))
    body.append(path(smooth([(334, 344, True), (344, 346, True), (341, 356, True), (331, 354, True)]), "none",
                     C["brass"], 2.2))
    part("torso", "Torso", "torso", "torso", 50, body)
    bag = smooth([(272, 380), (286, 372), (306, 374), (308, 392), (306, 422), (296, 430), (276, 428), (268, 412)])
    flap = smooth([(272, 380), (286, 372), (306, 374), (308, 392), (304, 402), (272, 400)])
    satchel = outlined(bag, C["leather"]) + [path(flap, C["leather_light"], INK, 1.8),
                                             path(smooth([(286, 398, True), (292, 398, True), (292, 408, True),
                                                          (286, 408, True)]), C["brass"], INK, 1.2)]
    part("satchel", "Satchel", "satchel", "torso", 52, satchel)


def hips_part():
    sil = smooth([(300, 396, True), (380, 396, True), (384, 414), (378, 434), (302, 434), (296, 414)])
    items = [path(smooth([(294, 396, True), (386, 396, True), (386, 408, True), (294, 408, True)]), C["leather_dark"]),
             path(smooth([(333, 396, True), (347, 396, True), (347, 408, True), (333, 408, True)]), "none", C["brass"],
                  2.2),
             line([(340, 410), (340, 434)], C["pants_dark"], 1.6)]
    body = outlined(sil, C["pants"], items, "clip-front-hips")
    body.append(ellipse(368, 416, 6.0, 6.0, "none", C["brass"], 2.2))
    for dx, k in ((-4, 0), (0, 1), (4, 0)):
        body.append(line([(368 + dx * 0.4, 422), (368 + dx, 434)], C["brass"] if not k else C["steel"], 2.6))
    part("hips", "Hips", "hips", "pelvis", 48, body)


# ---- legs and arms -----------------------------------------------------------------
def leg_parts(side):
    hip, knee, ankle = J[f"{side}_hip"], J[f"{side}_knee"], J[f"{side}_ankle"]
    s = 1.0 if side == "near" else -1.0
    thigh = capsule(hip, knee, 23.0, 18.0)
    items = [line([(hip[0] + s * 8, hip[1] + 10), (knee[0] + s * 8, knee[1] - 6)], C["pants_light"], 4.0)]
    part(f"{side}-leg-u", f"Thigh - {side}", f"{side}_leg_u", f"{side}_leg_u", 32,
         outlined(thigh, C["pants"], items, f"clip-front-{side}-thigh"))
    shin = capsule(knee, ankle, 18.0, 14.5)
    items = [path(smooth([(knee[0] - 15, knee[1] - 8), (knee[0] + 15, knee[1] - 8), (knee[0] + 15, knee[1] + 14),
                          (knee[0] - 15, knee[1] + 14)]), C["pants_dark"]),
             line([(knee[0] + s * 7, knee[1] + 16), (ankle[0] + s * 6, ankle[1] - 10)], C["pants_light"], 3.4)]
    part(f"{side}-leg-l", f"Shin - {side}", f"{side}_leg_l", f"{side}_leg_l", 31,
         outlined(shin, C["pants"], items, f"clip-front-{side}-shin"))
    ax, ay = ankle
    # A work boot seen toe-on: the shaft, the rounded toe cap, the sole.
    boot = smooth([(ax - 17, ay - 24), (ax + 17, ay - 24), (ax + 19, ay - 2), (ax + 22, ay + 12), (ax + 18, ay + 19, True),
                   (ax - 18, ay + 19, True), (ax - 22, ay + 12), (ax - 19, ay - 2)])
    items = [path(smooth([(ax - 24, ay + 12, True), (ax + 24, ay + 12, True), (ax + 24, ay + 21, True),
                          (ax - 24, ay + 21, True)]), C["sole"]),
             path(smooth([(ax - 19, ay - 28, True), (ax + 19, ay - 28, True), (ax + 19, ay - 19, True),
                          (ax - 19, ay - 19, True)]), C["boot_light"], INK, 1.4),
             ellipse(ax, ay + 4, 12, 6, C["boot_light"])]
    for k in range(3):
        items.append(line([(ax - 6, ay - 16 + k * 5), (ax + 6, ay - 16 + k * 5)], C["sole"], 1.4))
    part(f"{side}-foot", f"Boot - {side}", f"{side}_foot", f"{side}_foot", 34,
         outlined(boot, C["boot"], items, f"clip-front-{side}-boot"))


def arm_parts(side):
    sh, el, wr = J[f"{side}_shoulder"], J[f"{side}_elbow"], J[f"{side}_wrist"]
    s = 1.0 if side == "near" else -1.0
    upper = capsule(sh, el, 16.5, 13.5)
    cuff = (el[0] - (el[0] - sh[0]) * 0.22, el[1] - (el[1] - sh[1]) * 0.22)
    items = [line([(sh[0] + s * 6, sh[1] + 4), (el[0] + s * 6, el[1])], C["shirt_light"], 4.0),
             path(smooth([(cuff[0] - 17, cuff[1], True), (cuff[0] + 17, cuff[1], True), (el[0] + 17, el[1] + 4, True),
                          (el[0] - 17, el[1] + 4, True)]), C["shirt_light"]),
             line([(cuff[0] - 17, cuff[1]), (cuff[0] + 17, cuff[1])], C["stripe"], 1.6)]
    part(f"{side}-arm-u", f"Upper Arm - {side}", f"{side}_arm_u", f"{side}_arm_u", 72,
         outlined(upper, C["shirt"], items, f"clip-front-{side}-arm-u"))
    fore = capsule(el, wr, 13.0, 10.5)
    items = [line([(el[0] + s * 5, el[1] + 4), (wr[0] + s * 4, wr[1] - 4)], C["skin_light"], 3.0)]
    part(f"{side}-arm-l", f"Forearm - {side}", f"{side}_arm_l", f"{side}_arm_l", 70,
         outlined(fore, C["skin"], items, f"clip-front-{side}-arm-l"))
    wx, wy = wr
    fist = smooth([(wx - 11, wy - 4), (wx, wy - 8), (wx + 11, wy - 4), (wx + 12, wy + 10), (wx + 6, wy + 20),
                   (wx - 6, wy + 20), (wx - 12, wy + 10)])
    knuckles = [line([(wx - 8, wy + 14), (wx + 8, wy + 14)], C["skin_shadow"], 1.3),
                path(smooth([(wx - s * 12, wy + 2), (wx - s * 6, wy - 2), (wx - s * 4, wy + 10), (wx - s * 10, wy + 12)]),
                     C["skin_light"], INK, 1.2)]
    part(f"{side}-hand-fist", f"Hand Fist - {side}", f"{side}_hand_fist", f"{side}_hand", 76,
         outlined(fist, C["skin"], knuckles, f"clip-front-{side}-fist"),
         f' data-rig-opacity="hand.{side}.fist" data-rig-default="1"')
    open_hand = smooth([(wx - 10, wy - 4), (wx + 10, wy - 4), (wx + 12, wy + 14), (wx + 8, wy + 28), (wx - 8, wy + 28),
                        (wx - 12, wy + 14)])
    fingers = [line([(wx + d, wy + 16), (wx + d, wy + 27)], C["skin_shadow"], 1.1) for d in (-4, 0, 4)]
    part(f"{side}-hand-open", f"Hand Open - {side}", f"{side}_hand_open", f"{side}_hand", 76,
         outlined(open_hand, C["skin"], fingers, f"clip-front-{side}-open"), f' data-rig-opacity="hand.{side}.open"')


def wrench_part():
    """The wrench hanging from his near fist, head down beside the leg."""
    wx, wy = J["near_wrist"]
    part("wrench", "Wrench", "wrench", "near_hand", 74, wrench_body((wx, wy + 8), 180.0),
         ' data-rig-opacity="prop.wrench" data-rig-default="1"')


def draw() -> str:
    svg.configure(dx=0.0, dy=0.0, ink=INK, ow=OW, colors=C)
    leg_parts("far")
    leg_parts("near")
    hips_part()
    torso_parts()
    head_part()
    face_parts()
    arm_parts("far")
    arm_parts("near")
    wrench_part()
    return svg.document(
        size=(W, H),
        design="bob-fighter-front-v1",
        layer_id="bob-front",
        label="Bob - Front",
        comment=[
            "  <!-- Bob facing the viewer: the same character, palette and wrench as",
            "       bob.svg (his side view), on the same 720x640 canvas, ground y=569,",
            "       centre line x=340, so both views publish into one frame. near is the",
            "       arm and leg on the viewer's right (his left), which holds the wrench.",
            "       Swap sets: open / shut / angry eyes, closed / smile / open mouths,",
            "       fist / open hands, the wrench. The hidden Rig Joints layer marks the",
            "       joints the humanoid rig in targets/characters/rigged/bob/ turns. -->",
        ],
        joints=svg.joints_layer(J),
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    Path(sys.argv[1]).write_text(draw())
