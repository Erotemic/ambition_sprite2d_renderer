#!/usr/bin/env python3
"""How the owl's SVG was first drawn (reference, not authority).

``data/characters/owl/owl.svg`` owns the art; this script reproduces it as
first committed (less the rig catalog ``scripts/build_owl_rig.py`` installs).

    uv run python scripts/svg_art/owl_art.py SIDE.svg

A horned owl on a 512x512 canvas, ground y=416, centre line x=256 (published
at 0.25: a 128 px frame). Its body is seen from the side and its face is
turned to the viewer, as an owl's is: two great amber eyes in a pale disc
under dark brows, ear tufts, a small hooked beak, a barred buff chest, broad
barred wings and feathered legs with long talons. The wing swaps between
folded on the body and spread in two bones.
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
    brown="#8b5e3c",
    brown_light="#a9774a",
    brown_dark="#6a4429",
    deep="#43291a",
    buff="#d9b27a",
    cream="#efdcb4",
    cream_shade="#cfae78",
    beak="#cfa94e",
    beak_dark="#7a5a20",
    toe="#c9a44a",
    claw="#2a1c14",
    iris="#f7b733",
    iris_dark="#d98a1c",
    pupil="#120d0f",
)

J = dict(
    body=(248.0, 322.0),
    neck=(258.0, 258.0),
    beak_tip=(304.0, 238.0),
    jaw=(280.0, 233.0),
    tail1=(226.0, 366.0),
    tail2=(206.0, 386.0),
    tail_tip=(182.0, 406.0),
    near_shoulder=(262.0, 272.0),
    near_wrist=(216.0, 186.0),
    near_wingtip=(118.0, 118.0),
    far_shoulder=(250.0, 268.0),
    far_wrist=(198.0, 190.0),
    far_wingtip=(102.0, 130.0),
    near_hip=(260.0, 360.0),
    near_knee=(268.0, 384.0),
    near_ankle=(270.0, 404.0),
    far_hip=(240.0, 358.0),
    far_knee=(246.0, 384.0),
    far_ankle=(248.0, 404.0),
)

BODY = [(284, 262), (300, 290), (304, 326), (292, 358), (268, 380), (238, 382), (212, 364), (200, 330), (204, 294),
        (220, 268), (250, 256)]
HEAD = [(226, 222), (228, 196), (240, 178), (258, 170), (284, 168), (304, 176), (316, 194), (318, 218), (308, 240),
        (288, 254), (262, 256), (240, 246)]

WING = dict(arm=C["brown"], arm_shade=C["deep"], covert=C["brown_light"], sec=C["brown"], sec_tip=C["brown_dark"],
            prim=C["brown_light"], prim_tip=C["brown_dark"], rib=C["buff"])
WING_FAR = dict(arm=C["brown_dark"], arm_shade=C["deep"], covert=C["brown"], sec=C["brown_dark"], sec_tip=C["deep"],
                prim=C["brown"], prim_tip=C["deep"], rib=C["cream_shade"])
TOES = ((-10, 8), (12, 11), (21, 7))


def bars(points, colour, width=2.2):
    """Short dashes across a feather tract: the owl's barring."""
    return [line([(x - half, y + 1), (x, y - 1), (x + half, y + 1)], colour, width) for x, y, half in points]


def parts():
    # The tail: short, broad, barred, down and back off the rump.
    tail = []
    for ang, ln, wd in ((126.0, 52.0, 22.0), (138.0, 60.0, 24.0), (150.0, 54.0, 22.0)):
        tail += feather((232, 362), ang, ln, wd, C["brown"], C["brown_dark"], C["buff"], tip_frac=0.3)
    part("tail", "Tail", "tail", "tail1", 10, tail)
    tip = []
    for ang, ln, wd in ((132.0, 36.0, 18.0), (146.0, 40.0, 18.0)):
        tip += feather((212, 382), ang, ln, wd, C["brown_light"], C["deep"], C["buff"], tip_frac=0.3)
    part("tail-tip", "Tail Tip", "tail_tip", "tail2", 9, tip)

    open_wing(J, "far", 14, WING_FAR, secondaries=7, sec_len=86.0, sec_w=24.0, primaries=7, prim_w=24.0, prim_spread=6.5)
    for side, z in (("far", 18), ("near", 40)):
        far = side == "far"
        legs(J, side, z, thigh=C["cream_shade"] if far else C["buff"], thigh_shade=C["brown_dark"],
             shank=C["beak_dark"] if far else C["toe"], shank_dark=C["beak_dark"], claw=C["claw"], toes=TOES,
             thigh_r=(15.0, 11.0), shank_r=(7.0, 6.0), toe_r=(4.4, 3.2), claw_len=6.0)

    sil = smooth(BODY)
    chest = smooth([(270, 264), (296, 292), (300, 326), (288, 356), (266, 378), (250, 352), (248, 312), (256, 282)])
    items = [
        path(chest, C["cream"]),
        path(smooth([(208, 330), (216, 300), (232, 340), (246, 376), (222, 366)]), C["brown_dark"]),
    ]
    items += bars([(278, 290, 7), (272, 306, 8), (288, 312, 6), (270, 324, 8), (288, 332, 6), (268, 342, 7),
                   (282, 350, 6), (266, 362, 6)], C["brown_dark"])
    part("body", "Body", "body", "body", 30, outlined(sil, C["brown"], items, "clip-body"))

    # The folded wing: long, down the back to the tail, barred.
    folded = smooth([(256, 262), (264, 292), (258, 330), (242, 364), (216, 394), (196, 402), (198, 372), (198, 334),
                     (206, 296), (226, 268)])
    items = [
        path(smooth([(256, 262), (262, 292), (256, 312), (240, 300), (232, 272)]), C["brown_light"]),
        path(smooth([(240, 364), (216, 394), (198, 402), (202, 374), (218, 362)]), C["brown_dark"]),
    ]
    items += bars([(244, 292, 9), (232, 310, 10), (246, 320, 8), (226, 330, 9), (240, 342, 8), (220, 352, 8),
                   (230, 366, 7), (212, 378, 6)], C["buff"], 2.4)
    part("near-wing-folded", "Wing - Folded", "near_wing_folded", "body", 52,
         outlined(folded, C["brown"], items, "clip-folded"), ' data-rig-opacity="wing.folded" data-rig-default="1"')
    open_wing(J, "near", 60, WING, secondaries=7, sec_len=86.0, sec_w=24.0, primaries=7, prim_w=24.0, prim_spread=6.5)

    head_parts()


#: The eyes: (centre x, centre y, x radius, y radius), the near one first.
EYES = ((260.0, 216.0, 12.5, 12.5), (298.0, 213.0, 9.5, 11.5))


def head_parts():
    body = []
    # The ear tufts, behind the crown.
    for pts in ([(234, 190), (220, 144, True), (256, 172)], [(290, 172), (314, 138, True), (314, 190)]):
        body += outlined(smooth(pts), C["brown_dark"], [line([pts[1][:2], ((pts[0][0] + pts[2][0]) / 2, 182)], C["deep"], 1.6)],
                         f"clip-tuft-{pts[1][0]}")
    sil = smooth(HEAD)
    disc = smooth([(236, 206), (250, 190), (270, 192), (284, 204), (296, 190), (310, 194), (316, 214), (308, 236),
                   (290, 246), (282, 238), (268, 248), (246, 242), (234, 226)])
    items = [
        path(smooth([(240, 180), (262, 172), (290, 172), (306, 180), (284, 186), (258, 186)]), C["brown_light"]),
        path(disc, C["cream"], C["brown_dark"], 2.4),
        # the brows: a dark V down to the beak
        line([(236, 192), (262, 196), (282, 210)], C["deep"], 4.6),
        line([(316, 188), (300, 194), (284, 210)], C["deep"], 4.6),
        line([(240, 232), (250, 238), (262, 240)], C["cream_shade"], 1.4),
    ]
    body += outlined(sil, C["brown"], items, "clip-head")
    upper = smooth([(276, 220, True), (287, 219, True), (289, 232), (283, 244, True), (278, 232)])
    body += outlined(upper, C["beak"], [line([(281, 224), (283, 236)], C["beak_dark"], 1.2)], "clip-beak")
    part("head", "Head", "head", "head", 70, body)
    lower = smooth([(279, 234, True), (287, 236, True), (283, 247, True)])
    part("jaw", "Lower Beak", "jaw", "jaw", 69, outlined(lower, C["beak_dark"]))

    open_, angry, shut, dead = [], [], [], []
    for k, (ex, ey, rx, ry) in enumerate(EYES):
        ring = [ellipse(ex, ey, rx, ry, C["iris"], INK, 1.6), ellipse(ex, ey + ry * 0.35, rx * 0.8, ry * 0.5, C["iris_dark"])]
        open_ += ring + [ellipse(ex + 1.5, ey, rx * 0.52, ry * 0.52, C["pupil"]),
                         ellipse(ex - rx * 0.25, ey - ry * 0.35, rx * 0.2, ry * 0.2, "#ffffff")]
        s = 1.0 if k == 0 else -1.0
        lid = smooth([(ex - s * (rx + 3), ey - ry - 2, True), (ex + s * (rx + 3), ey - ry * 0.1, True),
                      (ex + s * (rx + 3), ey - ry - 3, True)])
        angry += ring + [ellipse(ex + 1.5, ey + 1.5, rx * 0.36, ry * 0.36, C["pupil"]), path(lid, C["deep"], INK, 1.0)]
        shut += [line([(ex - rx, ey - 1), (ex, ey + 4), (ex + rx, ey - 1)], INK, 2.4)]
        dead += [line([(ex - rx * 0.7, ey - ry * 0.7), (ex + rx * 0.7, ey + ry * 0.7)], INK, 2.4),
                 line([(ex - rx * 0.7, ey + ry * 0.7), (ex + rx * 0.7, ey - ry * 0.7)], INK, 2.4)]
    eye_states("eye", "head", 72, {"open": open_, "angry": angry, "shut": shut, "dead": dead})


def draw_side() -> str:
    svg.configure(dx=0.0, dy=0.0, ink=INK, ow=OW, colors=C)
    parts()
    return svg.document(
        size=(W, H),
        design="owl-side",
        layer_id="owl-side",
        label="Owl - Side Right",
        comment=[
            "  <!-- The owl, a horned owl, its body seen from the side facing right and its",
            "       face turned to the viewer, on a 512x512 drawing whose ground is y=416",
            "       (published at 0.25). Each part is a layer with a data-rig-part name;",
            "       rigged/owl/ turns them about their joints. The wing swaps between folded",
            "       (on the body) and spread (wing.folded / wing.open); the eyes have open /",
            "       angry / shut / dead. The hidden Rig Joints layer marks every joint the",
            "       skeleton is built on. -->",
        ],
        joints=svg.joints_layer(J),
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    Path(sys.argv[1]).write_text(draw_side())
