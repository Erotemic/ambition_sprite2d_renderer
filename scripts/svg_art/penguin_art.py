#!/usr/bin/env python3
"""How the penguin's SVG was first drawn (reference, not authority).

``data/characters/penguin/penguin.svg`` owns the art; this script reproduces
it as first committed (less the rig catalog ``scripts/build_penguin_rig.py``
installs).

    uv run python scripts/svg_art/penguin_art.py SIDE.svg

A penguin on a 512x512 canvas, ground y=416, centre line x=256 (published at
0.25: a 128 px frame), on the joints of ``rigbuild.bird``. It stands upright:
a black back and head, a white front with a gold wash at the throat, a pale
cheek, an orange beak and orange feet. Its wing is a flipper: one stiff blade
that hangs at its side (the part rides the ``<side>_wing`` bone; there is no
folded and spread pair).
"""
from __future__ import annotations

import sys
from pathlib import Path

import svgkit as svg
from birdkit import ellipse, eye_states, feather, legs, line, outlined, part, path, smooth

W, H = 512, 512
INK = "#1d1418"
OW = 1.6

C = dict(
    black="#22283a",
    sheen="#3d4866",
    deep="#141826",
    white="#f6f3ea",
    white_shade="#d5d0c4",
    gold="#f6c94a",
    beak="#f2a13a",
    beak_dark="#3a2a26",
    foot="#f2a13a",
    foot_dark="#b86e1c",
    claw="#3a2a26",
    pupil="#120d0f",
)

J = dict(
    body=(252.0, 330.0),
    neck=(262.0, 264.0),
    beak_tip=(332.0, 244.0),
    jaw=(292.0, 247.0),
    tail1=(224.0, 386.0),
    tail2=(208.0, 398.0),
    tail_tip=(190.0, 410.0),
    near_shoulder=(258.0, 290.0),
    near_wrist=(262.0, 336.0),
    near_wingtip=(256.0, 378.0),
    far_shoulder=(248.0, 288.0),
    far_wrist=(250.0, 334.0),
    far_wingtip=(244.0, 374.0),
    near_hip=(264.0, 384.0),
    near_knee=(270.0, 396.0),
    near_ankle=(272.0, 404.0),
    far_hip=(242.0, 384.0),
    far_knee=(246.0, 396.0),
    far_ankle=(248.0, 404.0),
)

BODY = [(280, 262), (296, 290), (302, 330), (296, 372), (276, 394), (246, 398), (222, 386), (210, 354), (210, 312),
        (220, 278), (244, 258)]
HEAD = [(236, 246), (238, 222), (252, 206), (274, 204), (290, 214), (296, 232), (292, 252), (278, 266), (254, 266),
        (240, 258)]
TOES = ((-9, 9), (12, 11), (23, 8))


def flipper(side, z, dark):
    """The flipper: a stiff blade from the shoulder, hanging at the side."""
    sh, tip = J[f"{side}_shoulder"], J[f"{side}_wingtip"]
    sil = svg.capsule(sh, tip, 12.0, 6.0)
    items = [line([(sh[0] - 5, sh[1] + 10), (tip[0] - 3, tip[1] - 8)], C["sheen"], 2.4)]
    part(f"{side}-flipper", f"Flipper - {side}", f"{side}_flipper", f"{side}_wing", z,
         outlined(sil, C["deep"] if dark else C["black"], [] if dark else items, f"clip-{side}-flipper"))


def parts():
    tail = []
    for ang, ln in ((140.0, 30.0), (156.0, 36.0), (172.0, 30.0)):
        tail += feather((228, 386), ang, ln, 14.0, C["deep"], None, C["sheen"], sw=1.0)
    part("tail", "Tail", "tail", "tail1", 10, tail)
    part("tail-tip", "Tail Tip", "tail_tip", "tail2", 9, feather((212, 398), 152.0, 22.0, 10.0, C["deep"], None, None, sw=1.0))
    flipper("far", 14, True)
    for side, z in (("far", 18), ("near", 40)):
        far = side == "far"
        legs(J, side, z, thigh=C["white_shade"] if far else C["white"], thigh_shade=C["white_shade"],
             shank=C["foot_dark"] if far else C["foot"], shank_dark=C["foot_dark"], claw=C["claw"], toes=TOES,
             thigh_r=(13.0, 8.0), shank_r=(6.0, 5.5), toe_r=(5.2, 3.6), claw_len=4.0)
    sil = smooth(BODY)
    belly = smooth([(274, 268), (294, 294), (298, 332), (292, 370), (274, 392), (254, 388), (246, 352), (248, 306), (258, 280)])
    items = [
        path(belly, C["white"]),
        path(smooth([(272, 270), (290, 290), (292, 310), (270, 300), (260, 282)]), C["gold"]),
        path(smooth([(270, 300), (292, 310), (296, 332), (270, 322)]), C["white"]),
        path(smooth([(252, 360), (262, 384), (276, 392), (290, 372), (278, 380), (262, 372)]), C["white_shade"]),
        path(smooth([(220, 280), (236, 264), (232, 300), (216, 340), (212, 312)]), C["sheen"]),
    ]
    part("body", "Body", "body", "body", 30, outlined(sil, C["black"], items, "clip-body"))
    flipper("near", 52, False)
    head_parts()


def head_parts():
    sil = smooth(HEAD)
    items = [
        path(smooth([(244, 220), (258, 208), (276, 208), (262, 216), (250, 226)]), C["sheen"]),
        # the pale cheek, with gold behind it
        path(smooth([(262, 232), (280, 236), (290, 250), (278, 264), (260, 262), (256, 246)]), C["gold"]),
        path(smooth([(268, 238), (284, 242), (288, 252), (278, 262), (266, 258)]), C["white"]),
    ]
    body = outlined(sil, C["black"], items, "clip-head")
    upper = smooth([(288, 232, True), (312, 235), (332, 244, True), (310, 247), (288, 247, True)])
    body += outlined(upper, C["beak_dark"], [path(smooth([(292, 241), (314, 241), (328, 245), (310, 247), (292, 247)]), C["beak"])],
                     "clip-beak")
    part("head", "Head", "head", "head", 70, body)
    lower = smooth([(290, 247, True), (324, 247, True), (306, 254), (290, 253, True)])
    part("jaw", "Lower Beak", "jaw", "jaw", 69, outlined(lower, C["beak"]))
    ex, ey = 277.0, 226.0
    ring = [ellipse(ex, ey, 5.6, 5.6, "#ffffff", INK, 1.3), ellipse(ex + 1.0, ey, 2.8, 2.8, C["pupil"])]
    eye_states("eye", "head", 72, {
        "open": ring + [ellipse(ex - 0.6, ey - 1.6, 1.1, 1.1, "#ffffff")],
        "angry": ring + [path(smooth([(ex - 8, ey - 8, True), (ex + 8, ey - 1, True), (ex + 8, ey - 7, True)]), C["deep"], INK, 0.9)],
        "shut": [line([(ex - 6, ey), (ex, ey + 3), (ex + 6, ey)], "#ffffff", 2.0)],
        "dead": [line([(ex - 5, ey - 5), (ex + 5, ey + 5)], "#ffffff", 2.0), line([(ex - 5, ey + 5), (ex + 5, ey - 5)], "#ffffff", 2.0)],
    })


def draw_side() -> str:
    svg.configure(dx=0.0, dy=0.0, ink=INK, ow=OW, colors=C)
    parts()
    return svg.document(
        size=(W, H),
        design="penguin-side",
        layer_id="penguin-side",
        label="Penguin - Side Right",
        comment=[
            "  <!-- The penguin, side view facing right, on a 512x512 drawing whose ground is",
            "       y=416 (published at 0.25). Each part is a layer with a data-rig-part name;",
            "       rigged/penguin/ turns them about their joints. Its wing is a flipper: one",
            "       blade on the wing bone. The eye has open / angry / shut / dead. The hidden",
            "       Rig Joints layer marks every joint the skeleton is built on. -->",
        ],
        joints=svg.joints_layer(J),
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    Path(sys.argv[1]).write_text(draw_side())
