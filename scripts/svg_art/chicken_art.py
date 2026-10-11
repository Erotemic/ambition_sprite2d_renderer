#!/usr/bin/env python3
"""How the chicken's SVG was first drawn (reference, not authority).

``data/characters/chicken/chicken.svg`` owns the art; this script reproduces
it as first committed (less the rig catalog ``scripts/build_chicken_rig.py``
installs).

    uv run python scripts/svg_art/chicken_art.py SIDE.svg [HEN.svg]

``HEN.svg`` is ``data/characters/chicken_hen/chicken_hen.svg``: the hen of the
same breed (a small comb and wattle, a short tail and no sickle feathers), on
the same joints.

A white cockerel with a dark tail (the Columbian pattern) on a 512x512 canvas,
ground y=416, centre line x=256 (published at 0.25: a 128 px frame). A red
comb and wattle, a short yellow beak, a striped hackle on the neck, yellow
legs. The wing swaps between folded on the body and spread in two bones.
"""
from __future__ import annotations

import sys
from pathlib import Path

import svgkit as svg
from birdkit import ellipse, eye_states, feather, legs, line, open_wing, outlined, part, path, smooth

W, H = 512, 512
INK = "#1d1418"
OW = 1.6

C = dict(
    white="#f6f1e7",
    white_light="#fffdf8",
    shade="#d6cdc0",
    shade_deep="#b3a898",
    dark="#2c3b46",
    dark_light="#4b6a78",
    dark_deep="#182028",
    sheen="#5f9a8a",
    red="#d8352b",
    red_light="#f0634a",
    red_dark="#9c1c1a",
    beak="#f2b233",
    beak_dark="#b77a14",
    leg="#f0b429",
    leg_dark="#b77a14",
    claw="#5a3d14",
    iris="#f08a2b",
    pupil="#120d0f",
    mouth="#5a1418",
)

J = dict(
    body=(250.0, 322.0),
    neck=(282.0, 282.0),
    beak_tip=(348.0, 218.0),
    jaw=(324.0, 218.0),
    tail1=(208.0, 292.0),
    tail2=(186.0, 258.0),
    tail_tip=(142.0, 196.0),
    near_shoulder=(264.0, 290.0),
    near_wrist=(228.0, 216.0),
    near_wingtip=(160.0, 158.0),
    far_shoulder=(254.0, 286.0),
    far_wrist=(212.0, 218.0),
    far_wingtip=(146.0, 170.0),
    near_hip=(260.0, 352.0),
    near_knee=(270.0, 378.0),
    near_ankle=(270.0, 404.0),
    far_hip=(236.0, 350.0),
    far_knee=(242.0, 378.0),
    far_ankle=(242.0, 404.0),
)

BODY = [(294, 284), (308, 306), (308, 332), (294, 356), (268, 372), (238, 372), (212, 358), (198, 332), (198, 304),
        (212, 282), (238, 272), (268, 270)]
#: The neck and the head, one part: the neck turns about its base.
HEAD = [(264, 288), (268, 258), (278, 232), (282, 208), (294, 192), (312, 188), (326, 198), (330, 214), (324, 232),
        (312, 244), (306, 264), (302, 288), (284, 296)]

WING = dict(arm=C["white"], arm_shade=C["shade_deep"], covert=C["shade"], sec=C["white"], sec_tip=C["dark"],
            prim=C["dark"], prim_tip=C["dark_light"], rib=C["shade_deep"])
WING_FAR = dict(arm=C["shade"], arm_shade=C["shade_deep"], covert=C["shade_deep"], sec=C["shade"], sec_tip=C["dark_deep"],
                prim=C["dark_deep"], prim_tip=C["dark"], rib=C["shade_deep"])
#: Two toes forward (the third hides behind them), one back.
TOES = ((-10, 9), (13, 12), (22, 8))


#: The hen: the joints of the cockerel with a short tail.
J_HEN = dict(J, tail2=(196.0, 272.0), tail_tip=(170.0, 244.0))


def parts(hen: bool = False):
    # The tail: dark sickle feathers standing up and back off the rump.
    tail = []
    # (The hen's is a short fan with no sickles.)
    k = 0.6 if hen else 1.0
    for ang, ln, wd in ((208.0, 78.0, 26.0), (222.0, 92.0, 28.0), (236.0, 84.0, 26.0), (250.0, 66.0, 24.0)):
        tail += feather((212, 294), ang, ln * k, wd, C["dark"], C["dark_light"], C["dark_deep"])
    part("tail", "Tail", "tail", "tail1", 10, tail)
    tip = []
    if hen:
        for ang, ln, wd in ((216.0, 34.0, 18.0), (236.0, 38.0, 18.0)):
            tip += feather((200, 276), ang, ln, wd, C["dark"], C["dark_light"], C["dark_deep"])
    else:
        for ang, ln, wd in ((212.0, 78.0, 20.0), (228.0, 96.0, 22.0), (244.0, 82.0, 20.0)):
            tip += feather((194, 266), ang, ln, wd, C["dark"], C["sheen"], C["dark_deep"])
    part("tail-tip", "Tail Tip", "tail_tip", "tail2", 9, tip)

    open_wing(J, "far", 14, WING_FAR, secondaries=5, sec_len=58.0, sec_w=22.0, primaries=5, prim_w=22.0, prim_spread=9.0)
    for side, z in (("far", 18), ("near", 40)):
        far = side == "far"
        legs(J, side, z, thigh=C["shade"] if far else C["white"], thigh_shade=C["shade_deep"],
             shank=C["leg_dark"] if far else C["leg"], shank_dark=C["claw"] if far else C["leg_dark"], claw=C["claw"],
             toes=TOES, thigh_r=(15.0, 10.0), shank_r=(5.0, 4.5), toe_r=(3.6, 2.6))

    sil = smooth(BODY)
    items = [
        path(smooth([(290, 290), (304, 308), (304, 330), (292, 334), (284, 310)]), C["white_light"]),
        path(smooth([(200, 330), (214, 310), (232, 344), (262, 366), (238, 374), (212, 360)]), C["shade"]),
        line([(270, 318), (282, 326), (296, 320)], C["shade_deep"], 1.2),
        line([(262, 340), (276, 348), (290, 342)], C["shade_deep"], 1.2),
        line([(248, 358), (262, 364), (276, 358)], C["shade_deep"], 1.2),
    ]
    part("body", "Body", "body", "body", 30, outlined(sil, C["white"], items, "clip-body"))

    # The folded wing: white coverts in scallops, dark flight feathers behind.
    folded = smooth([(276, 292), (284, 312), (274, 336), (250, 350), (222, 350), (198, 342), (212, 320), (234, 302),
                     (256, 292)])
    items = [
        path(smooth([(250, 350), (222, 350), (198, 342), (212, 326), (236, 334)]), C["dark"]),
        line([(206, 340), (228, 342), (246, 346)], C["dark_light"], 1.4),
        line([(262, 304), (268, 316), (262, 328)], C["shade_deep"], 1.2),
        line([(244, 308), (250, 320), (244, 332)], C["shade_deep"], 1.2),
        line([(228, 314), (234, 324), (228, 334)], C["shade_deep"], 1.2),
        path(smooth([(272, 296), (280, 312), (272, 330), (266, 312)]), C["white_light"]),
    ]
    part("near-wing-folded", "Wing - Folded", "near_wing_folded", "body", 52,
         outlined(folded, C["white"], items, "clip-folded"), ' data-rig-opacity="wing.folded" data-rig-default="1"')
    open_wing(J, "near", 60, WING, secondaries=5, sec_len=58.0, sec_w=22.0, primaries=5, prim_w=22.0, prim_spread=9.0)

    head_parts(hen)


def head_parts(hen: bool = False):
    # The comb: three red lobes behind the crown.
    body = []
    lobes = ((294, 186, 7.5, 13.0, -24.0), (307, 179, 8.0, 15.0, -4.0), (320, 185, 7.0, 12.0, 22.0))
    if hen:
        # a small comb, low on the crown
        lobes = ((300, 189, 5.0, 6.5, -20.0), (309, 186, 5.5, 7.5, -4.0), (318, 189, 5.0, 6.0, 20.0))
    for cx, cy, rx, ry, rot in lobes:
        body.append(ellipse(cx, cy, rx, ry, C["red"], INK, 2 * OW, rot=rot))
        body.append(ellipse(cx - 1.5, cy - 3, rx * 0.4, ry * 0.45, C["red_light"], rot=rot))
    sil = smooth(HEAD)
    items = [
        path(smooth([(292, 196), (312, 192), (324, 202), (310, 206), (294, 208)]), C["white_light"]),
        path(smooth([(264, 288), (268, 258), (276, 240), (284, 262), (284, 296)]), C["shade"]),
        # the hackle: dark strokes down the neck
        line([(280, 250), (276, 268), (278, 286)], C["dark"], 2.2),
        line([(290, 254), (288, 272), (290, 290)], C["dark"], 2.2),
        line([(299, 262), (298, 276), (299, 290)], C["dark"], 2.0),
        # the red face round the eye
        path(smooth([(306, 200), (322, 200), (328, 214), (322, 228), (310, 226), (304, 214)]), C["red"]),
    ]
    body += outlined(sil, C["white"], items, "clip-head")
    # The wattle, hanging under the chin.
    wattle = [(316, 230), (325, 232), (326, 242), (321, 248), (315, 243)] if hen else \
        [(316, 230), (326, 232), (328, 248), (322, 258), (314, 250)]
    body += outlined(smooth(wattle), C["red"], [ellipse(319, 238 if hen else 240, 2.0 if hen else 2.4,
                                                        3.0 if hen else 5.0, C["red_light"])], "clip-wattle")
    upper = smooth([(324, 204, True), (338, 208), (348, 218, True), (336, 220), (324, 220, True)])
    body += outlined(upper, C["beak"], [line([(328, 212), (340, 215)], C["beak_dark"], 1.2)], "clip-beak")
    part("head", "Head", "head", "head", 70, body)
    lower = smooth([(322, 218, True), (340, 220, True), (332, 227), (322, 228, True)])
    part("jaw", "Lower Beak", "jaw", "jaw", 69, outlined(lower, C["beak_dark"]))
    ex, ey = 314.0, 210.0
    eye_states("eye", "head", 72, {
        "open": [ellipse(ex, ey, 5.6, 5.6, C["iris"], INK, 1.4), ellipse(ex + 0.6, ey, 2.2, 2.2, C["pupil"]),
                 ellipse(ex - 1.4, ey - 1.8, 1.2, 1.2, "#ffffff")],
        "angry": [ellipse(ex, ey, 5.6, 5.6, C["iris"], INK, 1.4), ellipse(ex + 1.2, ey + 0.4, 1.6, 1.6, C["pupil"]),
                  path(smooth([(ex - 9, ey - 9, True), (ex + 9, ey - 2, True), (ex + 9, ey - 8, True)]), C["red_dark"],
                       INK, 1.0)],
        "shut": [line([(ex - 6, ey), (ex, ey + 3), (ex + 6, ey)], INK, 2.0)],
        "dead": [line([(ex - 5, ey - 5), (ex + 5, ey + 5)], INK, 2.2), line([(ex - 5, ey + 5), (ex + 5, ey - 5)], INK, 2.2)],
    })


def draw_side(hen: bool = False) -> str:
    svg.configure(dx=0.0, dy=0.0, ink=INK, ow=OW, colors=C)
    parts(hen)
    if hen:
        return svg.document(
            size=(W, H),
            design="chicken-hen-side",
            layer_id="chicken-hen-side",
            label="Chicken Hen - Side Right",
            comment=[
                "  <!-- The hen of the chicken: the cockerel's breed with a small comb and wattle",
                "       and a short tail, side view facing right, on a 512x512 drawing whose ground",
                "       is y=416 (published at 0.25). rigged/chicken_hen/ turns its parts about their",
                "       joints. The hidden Rig Joints layer marks every joint. -->",
            ],
            joints=svg.joints_layer(J_HEN),
        )
    return svg.document(
        size=(W, H),
        design="chicken-side",
        layer_id="chicken-side",
        label="Chicken - Side Right",
        comment=[
            "  <!-- The chicken, a white cockerel with a dark tail, side view facing right, on",
            "       a 512x512 drawing whose ground is y=416 (published at 0.25). Each part is a",
            "       layer with a data-rig-part name; rigged/chicken/ turns them about their",
            "       joints. The wing swaps between folded (on the body) and spread",
            "       (wing.folded / wing.open); the eye has open / angry / shut / dead. The",
            "       hidden Rig Joints layer marks every joint the skeleton is built on. -->",
        ],
        joints=svg.joints_layer(J),
    )


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        raise SystemExit(__doc__)
    Path(sys.argv[1]).write_text(draw_side())
    if len(sys.argv) == 3:
        Path(sys.argv[2]).write_text(draw_side(hen=True))
