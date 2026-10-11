#!/usr/bin/env python3
"""How the vulture's SVG was first drawn (reference, not authority).

``data/characters/vulture/vulture.svg`` owns the art; this script reproduces
it as first committed (less the rig catalog ``scripts/build_vulture_rig.py``
installs).

    uv run python scripts/svg_art/vulture_art.py SIDE.svg

A vulture on a 512x512 canvas, ground y=416, centre line x=256 (published at
0.5: a 256 px frame), on the joints of ``rigbuild.bird``. It stands hunched:
dark plumage, a white ruff round the root of a bare red neck that reaches
forward, a bald head with a heavy brow, a pale hooked beak, broad wings with
long fingered flight feathers, grey legs. The neck and the head are one part
(the ``head`` bone turns it about its root in the ruff). The wing swaps
between folded on the body and spread in two bones.
"""
from __future__ import annotations

import sys
from pathlib import Path

import svgkit as svg
from birdkit import (along, ellipse, eye_states, feather, legs, line, open_wing, outlined, part, path, shag, smooth,
                     tube)

W, H = 512, 512
INK = "#1d1418"
OW = 1.6

C = dict(
    dark="#3b302e",
    light="#5c4b48",
    deep="#231b1a",
    edge="#7a6660",
    white="#f1ece2",
    white_shade="#cdc5b6",
    skin="#d9655c",
    skin_light="#ee8f84",
    skin_dark="#a13c3a",
    beak="#ece0c4",
    beak_dark="#3a2e2c",
    leg="#b9b0a2",
    leg_dark="#857c70",
    claw="#1c1614",
    iris="#2a1c14",
)

J = dict(
    body=(246.0, 318.0),
    neck=(272.0, 262.0),
    beak_tip=(352.0, 272.0),
    jaw=(324.0, 258.0),
    tail1=(222.0, 366.0),
    tail2=(200.0, 388.0),
    tail_tip=(174.0, 408.0),
    near_shoulder=(262.0, 270.0),
    near_wrist=(210.0, 178.0),
    near_wingtip=(98.0, 106.0),
    far_shoulder=(250.0, 266.0),
    far_wrist=(192.0, 182.0),
    far_wingtip=(84.0, 118.0),
    near_hip=(258.0, 360.0),
    near_knee=(266.0, 384.0),
    near_ankle=(268.0, 404.0),
    far_hip=(240.0, 358.0),
    far_knee=(246.0, 384.0),
    far_ankle=(248.0, 404.0),
)

BODY = [(284, 264), (300, 292), (302, 330), (290, 362), (266, 380), (236, 382), (212, 364), (198, 330), (202, 292),
        (220, 260), (250, 248)]
WING = dict(arm=C["dark"], arm_shade=C["deep"], covert=C["light"], sec=C["dark"], sec_tip=C["deep"], prim=C["deep"],
            prim_tip="#120e0e", rib=C["edge"])
WING_FAR = dict(arm=C["deep"], arm_shade="#120e0e", covert=C["dark"], sec=C["deep"], sec_tip="#120e0e", prim="#120e0e",
                prim_tip="#0a0808", rib=C["light"])
BROAD = dict(secondaries=7, sec_len=92.0, sec_w=26.0, primaries=7, prim_w=22.0, prim_spread=8.5, prim_reach=1.1)
TOES = ((-10, 8), (12, 11), (21, 7))


def parts():
    tail = []
    for ang, ln, wd in ((126.0, 54.0, 24.0), (138.0, 62.0, 26.0), (150.0, 56.0, 24.0)):
        tail += feather((230, 362), ang, ln, wd, C["dark"], C["deep"], C["edge"], tip_frac=0.3)
    part("tail", "Tail", "tail", "tail1", 10, tail)
    tip = []
    for ang, ln, wd in ((132.0, 36.0, 18.0), (146.0, 40.0, 18.0)):
        tip += feather((210, 382), ang, ln, wd, C["deep"], None, C["edge"])
    part("tail-tip", "Tail Tip", "tail_tip", "tail2", 9, tip)

    open_wing(J, "far", 14, WING_FAR, **BROAD)
    for side, z in (("far", 18), ("near", 40)):
        far = side == "far"
        legs(J, side, z, thigh=C["deep"] if far else C["dark"], thigh_shade=C["deep"],
             shank=C["leg_dark"] if far else C["leg"], shank_dark=C["leg_dark"], claw=C["claw"], toes=TOES,
             thigh_r=(16.0, 11.0), shank_r=(6.0, 5.0), toe_r=(4.4, 3.2), claw_len=6.0)

    sil = smooth(BODY)
    items = [
        path(smooth([(272, 270), (294, 294), (296, 328), (284, 356), (264, 372), (262, 330), (264, 292)]), C["light"]),
        path(smooth([(200, 330), (212, 300), (230, 340), (246, 378), (222, 368)]), C["deep"]),
        line([(270, 300), (280, 306), (290, 300)], C["deep"], 1.3),
        line([(266, 322), (278, 328), (290, 322)], C["deep"], 1.3),
        line([(264, 344), (274, 350), (284, 344)], C["deep"], 1.3),
    ]
    part("body", "Body", "body", "body", 30, outlined(sil, C["dark"], items, "clip-body"))

    # The folded wing: a great dark cloak down the back, its feathers edged pale.
    folded = smooth([(256, 254), (266, 290), (260, 330), (244, 366), (218, 398), (194, 406), (194, 372), (194, 332),
                     (202, 292), (224, 258)])
    items = [path(smooth([(244, 366), (218, 398), (194, 406), (196, 376), (216, 364)]), C["deep"])]
    for k, (x, y) in enumerate(((246, 286), (230, 302), (250, 312), (224, 324), (244, 336), (218, 346), (236, 360),
                                (212, 370), (226, 384))):
        items.append(line([(x - 10, y - 2), (x, y + 4), (x + 10, y - 2)], C["edge"], 1.6))
    part("near-wing-folded", "Wing - Folded", "near_wing_folded", "body", 52,
         outlined(folded, C["dark"], items, "clip-folded"), ' data-rig-opacity="wing.folded" data-rig-default="1"')
    open_wing(J, "near", 60, WING, **BROAD)

    # The ruff: a collar of white down round the root of the neck.
    ruff = smooth([(246, 264), (252, 248), (270, 240), (290, 246), (300, 262), (292, 278), (270, 284), (252, 278)])
    fluff = shag([(246, 270), (256, 284), (276, 288), (296, 278), (302, 262)], 7, 9.0, C["white"], lean=0.1)
    part("ruff", "Ruff", "ruff", "body", 64, fluff + outlined(ruff, C["white"], [
        line([(254, 262), (262, 270), (272, 264), (282, 272), (292, 264)], C["white_shade"], 1.6)], "clip-ruff"))

    head_parts()


def head_parts():
    # The bare neck reaches forward out of the ruff; the head is at its end.
    centre = [(272, 262), (284, 246), (300, 238), (316, 240)]
    neck = smooth(tube(centre, 11.0, 12.0))
    items = [line([along(centre, 0.1), along(centre, 0.5), along(centre, 0.9)], C["skin_light"], 4.0)]
    for u in (0.25, 0.45, 0.65):
        x, y = along(centre, u)
        items.append(line([(x - 6, y - 8), (x - 2, y), (x - 6, y + 8)], C["skin_dark"], 1.2))
    body = outlined(neck, C["skin"], items, "clip-neck")
    head = smooth([(304, 244), (304, 228), (316, 220), (332, 222), (340, 234), (338, 250), (326, 258), (310, 256)])
    body += outlined(head, C["skin"], [path(smooth([(306, 228), (318, 222), (332, 224), (320, 230)]), C["skin_light"]),
                                       path(smooth([(304, 246), (312, 256), (326, 258), (314, 250)]), C["skin_dark"])],
                     "clip-head")
    upper = smooth([(332, 228, True), (346, 232), (354, 248), (352, 274, True), (344, 262), (334, 254, True)])
    body += outlined(upper, C["beak"], [path(smooth([(350, 254), (354, 262), (352, 274), (346, 264)]), C["beak_dark"]),
                                        ellipse(338, 238, 1.8, 1.4, C["beak_dark"])], "clip-beak")
    part("head", "Head", "head", "head", 70, body)
    lower = smooth([(324, 256, True), (342, 258, True), (338, 268), (324, 266, True)])
    part("jaw", "Lower Beak", "jaw", "jaw", 69, outlined(lower, C["beak_dark"]))
    ex, ey = 322.0, 236.0
    brow = path(smooth([(312, 228, True), (332, 232, True), (332, 228, True), (314, 223, True)]), C["skin_dark"], INK, 0.9)
    ring = [ellipse(ex, ey, 4.6, 4.6, "#f1e6b0", INK, 1.2), ellipse(ex + 0.6, ey + 0.2, 2.4, 2.4, C["iris"])]
    eye_states("eye", "head", 72, {
        "open": ring + [ellipse(ex - 1.0, ey - 1.4, 1.0, 1.0, "#ffffff"), brow],
        "angry": ring + [path(smooth([(ex - 8, ey - 8, True), (ex + 8, ey - 1, True), (ex + 8, ey - 7, True)]),
                              C["skin_dark"], INK, 0.9)],
        "shut": [line([(ex - 5, ey), (ex, ey + 2.5), (ex + 5, ey)], INK, 1.8)],
        "dead": [line([(ex - 4, ey - 4), (ex + 4, ey + 4)], INK, 1.8), line([(ex - 4, ey + 4), (ex + 4, ey - 4)], INK, 1.8)],
    })


def draw_side() -> str:
    svg.configure(dx=0.0, dy=0.0, ink=INK, ow=OW, colors=C)
    parts()
    return svg.document(
        size=(W, H),
        design="vulture-side",
        layer_id="vulture-side",
        label="Vulture - Side Right",
        comment=[
            "  <!-- The vulture, side view facing right, on a 512x512 drawing whose ground is",
            "       y=416 (published at 0.5). Each part is a layer with a data-rig-part name;",
            "       rigged/vulture/ turns them about their joints. The wing swaps between folded",
            "       (on the body) and spread (wing.folded / wing.open); the eye has open / angry",
            "       / shut / dead. The hidden Rig Joints layer marks every joint. -->",
        ],
        joints=svg.joints_layer(J),
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    Path(sys.argv[1]).write_text(draw_side())
