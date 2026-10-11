#!/usr/bin/env python3
"""How the two swallows' SVGs were first drawn (reference, not authority).

``data/characters/european_swallow/european_swallow.svg`` and
``data/characters/african_swallow/african_swallow.svg`` own the art; this
script reproduces them as first committed (less the rig catalog
``scripts/build_swallow_rigs.py`` installs).

    uv run python scripts/svg_art/swallows_art.py OUT_DIR

Two small birds on a 512x512 canvas, ground y=416, centre line x=256
(published at 0.25: a 128 px frame), on the joints of ``rigbuild.bird``: long
pointed wings that fold on the body or spread in two bones, and a deeply
forked tail.

- European swallow: blue-black above, a chestnut forehead and throat over a
  dark band, cream below, long tail streamers. Unladen.
- African swallow: a rufous cap and rump, white below with dark streaks. The
  coconut it carries is not in this drawing: a coconut is a thing of the
  world that it picks up.
"""
from __future__ import annotations

import sys
from pathlib import Path

import svgkit as svg
from birdkit import ellipse, eye_states, feather, legs, line, open_wing, outlined, part, path, smooth

W, H = 512, 512
INK = "#1d1418"
OW = 1.5
J = dict(
    body=(252.0, 346.0), neck=(282.0, 306.0), beak_tip=(338.0, 298.0), jaw=(318.0, 298.0),
    tail1=(226.0, 372.0), tail2=(176.0, 392.0), tail_tip=(112.0, 408.0),
    near_shoulder=(272.0, 322.0), near_wrist=(236.0, 246.0), near_wingtip=(128.0, 164.0),
    far_shoulder=(262.0, 318.0), far_wrist=(220.0, 250.0), far_wingtip=(114.0, 176.0),
    near_hip=(262.0, 378.0), near_knee=(268.0, 392.0), near_ankle=(270.0, 404.0),
    far_hip=(248.0, 376.0), far_knee=(252.0, 392.0), far_ankle=(254.0, 404.0),
)

EUROPEAN = dict(blue="#22305a", sheen="#3f5ea8", deep="#141c38", belly="#f3e8d2", belly_shade="#d6c6a6", face="#b5452a",
                face_dark="#7e2a18", band="#1a2444", leg="#2a2a30", claw="#101014", beak="#1c1c22")
AFRICAN = dict(blue="#24345e", sheen="#4668b4", deep="#141c38", belly="#fbf6ee", belly_shade="#d9d0c2", face="#d2691e",
               face_dark="#9a4410", band="#24345e", leg="#2a2a30", claw="#101014", beak="#1c1c22")


def draw(african: bool) -> str:
    C = AFRICAN if african else EUROPEAN
    svg.configure(dx=0.0, dy=0.0, ink=INK, ow=OW, colors=C)
    # The tail: a deep fork. The streamers are the outer feathers.
    tail = []
    for ang, ln, wd in ((150.0, 62.0, 14.0), (168.0, 74.0, 14.0), (159.0, 56.0, 16.0)):
        tail += feather((232, 370), ang, ln, wd, C["blue"], C["deep"], C["deep"], sw=1.0)
    part("tail", "Tail", "tail", "tail1", 10, tail)
    tip = []
    for (bx, by), ang, ln in (((190, 382), 156.0, 96.0), ((184, 396), 172.0, 84.0)):
        tip += feather((bx, by), ang, ln, 8.0, C["deep"], None, None, sw=1.0)
    part("tail-tip", "Tail Tip", "tail_tip", "tail2", 9, tip)
    wing = dict(arm=C["blue"], arm_shade=C["deep"], covert=C["sheen"], sec=C["blue"], sec_tip=C["deep"], prim=C["deep"],
                prim_tip="#0c1022", rib=C["sheen"])
    wing_far = dict(wing, arm=C["deep"], covert=C["blue"], sec=C["deep"], prim="#0c1022")
    narrow = dict(secondaries=5, sec_len=50.0, sec_w=17.0, primaries=6, prim_w=14.0, prim_spread=5.0, prim_reach=1.16)
    open_wing(J, "far", 14, wing_far, **narrow)
    for side, z in (("far", 18), ("near", 40)):
        legs(J, side, z, thigh=C["belly_shade"] if side == "far" else C["belly"], thigh_shade=C["belly_shade"],
             shank=C["leg"], shank_dark=C["claw"], claw=C["claw"], toes=((-8, 7), (8, 9), (14, 6)), thigh_r=(8.0, 5.0),
             shank_r=(3.0, 2.6), toe_r=(2.4, 1.8), claw_len=3.0)
    sil = smooth([(288, 308), (302, 328), (300, 352), (284, 372), (258, 384), (234, 384), (218, 370), (218, 348),
                  (232, 326), (254, 310), (272, 304)])
    items = [path(smooth([(272, 304), (254, 310), (232, 326), (218, 348), (218, 370), (234, 384), (242, 360), (258, 334),
                          (282, 314)]), C["blue"])]
    if african:
        # a rufous rump, and streaks down the breast
        items.append(path(smooth([(218, 350), (218, 370), (234, 384), (242, 366), (232, 350)]), C["face"]))
        for x, y in ((284, 330), (292, 344), (278, 350), (286, 362), (270, 368), (264, 354)):
            items.append(line([(x, y), (x - 2, y + 9)], C["band"], 1.6))
    else:
        items.append(path(smooth([(278, 310), (296, 320), (302, 332), (288, 330), (274, 320)]), C["band"]))
        items.append(line([(270, 356), (282, 362), (294, 356)], C["belly_shade"], 1.2))
    part("body", "Body", "body", "body", 30, outlined(sil, C["belly"], items, "clip-body"))
    folded = smooth([(276, 316), (284, 336), (270, 356), (240, 378), (196, 398), (150, 408), (176, 388), (212, 360),
                     (244, 330), (262, 316)])
    items = [line([(270, 326), (246, 350), (204, 384)], C["sheen"], 1.6),
             path(smooth([(240, 378), (196, 398), (150, 408), (180, 390), (214, 372)]), C["deep"]),
             line([(262, 340), (236, 364), (196, 392)], C["deep"], 1.2)]
    part("near-wing-folded", "Wing - Folded", "near_wing_folded", "body", 52,
         outlined(folded, C["blue"], items, "clip-folded"), ' data-rig-opacity="wing.folded" data-rig-default="1"')
    open_wing(J, "near", 60, wing, **narrow)

    head = smooth([(274, 296), (276, 278), (290, 268), (308, 268), (320, 278), (322, 294), (314, 308), (298, 314),
                   (282, 310)])
    if african:
        items = [path(smooth([(274, 290), (278, 276), (292, 268), (310, 268), (320, 278), (304, 282), (286, 284)]), C["face"]),
                 path(smooth([(274, 296), (282, 310), (298, 314), (290, 300)]), C["blue"])]
        fill = C["belly"]
    else:
        items = [path(smooth([(306, 268), (320, 278), (322, 288), (310, 282)]), C["face"]),
                 path(smooth([(298, 298), (322, 292), (316, 308), (300, 314), (288, 308)]), C["face"]),
                 line([(300, 302), (312, 304)], C["face_dark"], 1.2)]
        fill = C["blue"]
    body = outlined(head, fill, items, "clip-head")
    upper = smooth([(318, 286, True), (330, 290), (338, 298, True), (326, 298), (318, 296, True)])
    body += outlined(upper, C["beak"])
    part("head", "Head", "head", "head", 70, body)
    lower = smooth([(318, 297, True), (334, 299, True), (325, 304), (318, 303, True)])
    part("jaw", "Lower Beak", "jaw", "jaw", 69, outlined(lower, C["beak"]))
    ex, ey = 308.0, 284.0
    ring = [ellipse(ex, ey, 4.6, 4.6, "#f6f1e7", INK, 1.2), ellipse(ex + 0.6, ey, 3.2, 3.2, "#120d0f")]
    eye_states("eye", "head", 72, {
        "open": ring + [ellipse(ex - 0.8, ey - 1.2, 1.0, 1.0, "#ffffff")],
        "angry": ring + [path(smooth([(ex - 7, ey - 7, True), (ex + 7, ey - 1, True), (ex + 7, ey - 6, True)]), C["deep"],
                              INK, 0.9)],
        "shut": [line([(ex - 5, ey), (ex, ey + 2.5), (ex + 5, ey)], INK, 1.8)],
        "dead": [line([(ex - 4, ey - 4), (ex + 4, ey + 4)], INK, 1.8), line([(ex - 4, ey + 4), (ex + 4, ey - 4)], INK, 1.8)],
    })
    name = "african_swallow" if african else "european_swallow"
    label = "African Swallow" if african else "European Swallow"
    return svg.document(
        size=(W, H), design=f"{name}-side", layer_id=f"{name}-side", label=f"{label} - Side Right",
        comment=[
            f"  <!-- The {label.lower()}, side view facing right, on a 512x512 drawing whose",
            "       ground is y=416 (published at 0.25). Each part is a layer with a",
            f"       data-rig-part name; rigged/{name}/ turns them about their joints. The wing",
            "       swaps between folded and spread (wing.folded / wing.open); the eye has open /",
            "       angry / shut / dead. The hidden Rig Joints layer marks every joint. -->",
        ],
        joints=svg.joints_layer(J),
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    (out / "european_swallow.svg").write_text(draw(False))
    (out / "african_swallow.svg").write_text(draw(True))
