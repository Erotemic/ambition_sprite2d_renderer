#!/usr/bin/env python3
"""How the ratites' SVGs were first drawn (reference, not authority).

``data/characters/<bird>/<bird>.svg`` for the ``ostrich``, the ``emu``, the
``cassowary``, the ``kiwi`` and the ``shoebill`` own the art; this script reproduces them as
first committed (less the rig catalog ``scripts/build_ratite_rigs.py``
installs).

    uv run python scripts/svg_art/ratites_art.py OUT_DIR

Four birds that do not fly, and the shoebill (not a ratite: a great wading
bird that has their build and hunts on foot), each a side view facing right on
a 512x512 canvas, ground y=416, centre line x=256. The tall ones are published
at 0.5 (a 256 px frame), the kiwi at 0.25 (a 128 px frame). They are one
anatomy (``rigbuild.ratite``): a body, a neck in its own bone, a head with a
hinged lower beak, a tail, a small wing per side and a two-bone leg per side
whose middle joint is the hock (it bends backward). The joint the leg helper
calls ``knee`` is the hock.

- ostrich: black, white plumes on its wings and its tail, a long bare neck
  and bare legs with two toes. The ``ostrich_hen`` is the same drawing in the
  hen's colours: grey-brown, with dull plumes.
- emu: shaggy grey-brown, a blue-grey bare neck over a collar of feathers, a
  dark tuft on its crown.
- cassowary: black and shaggy, a bright blue neck with red wattles, a tall
  casque on its head, thick legs with a dagger claw.
- kiwi: a small brown pear with no wing or tail to see, a long thin beak,
  whiskers and big feet.
- shoebill: slate grey, a great clog of a bill with a hooked nail, a pale eye
  under a brow that never lifts, a small crest, long dark legs.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Tuple

import svgkit as svg
from birdkit import along, ellipse, eye_states, feather, legs, line, outlined, part, path, shag, smooth, tube

W, H = 512, 512
INK = "#1d1418"
OW = 1.6
Point = Tuple[float, float]


def simple_eyes(ex: float, ey: float, r: float, iris: str, lid: str) -> Dict[str, list]:
    pupil = "#120d0f"
    return {
        "open": [ellipse(ex, ey, r, r, iris, INK, 1.3), ellipse(ex + 0.6, ey, r * 0.5, r * 0.5, pupil),
                 ellipse(ex - r * 0.3, ey - r * 0.35, r * 0.22, r * 0.22, "#ffffff")],
        "angry": [ellipse(ex, ey, r, r, iris, INK, 1.3), ellipse(ex + 1.0, ey + 0.4, r * 0.36, r * 0.36, pupil),
                  path(smooth([(ex - r - 3, ey - r - 3, True), (ex + r + 3, ey - r * 0.2, True),
                               (ex + r + 3, ey - r - 3, True)]), lid, INK, 1.0)],
        "shut": [line([(ex - r, ey), (ex, ey + r * 0.5), (ex + r, ey)], INK, 2.0)],
        "dead": [line([(ex - r * 0.8, ey - r * 0.8), (ex + r * 0.8, ey + r * 0.8)], INK, 2.0),
                 line([(ex - r * 0.8, ey + r * 0.8), (ex + r * 0.8, ey - r * 0.8)], INK, 2.0)],
    }


def finish(name: str, label: str, J: Dict[str, Point], comment: List[str]) -> str:
    return svg.document(size=(W, H), design=f"{name}-side", layer_id=f"{name}-side", label=f"{label} - Side Right",
                        comment=comment, joints=svg.joints_layer(J))


# ---- ostrich --------------------------------------------------------------------------

OSTRICH = dict(
    body=(246.0, 232.0), neck=(290.0, 208.0), head=(322.0, 92.0), beak_tip=(360.0, 98.0), jaw=(334.0, 98.0),
    tail=(188.0, 226.0), tail_tip=(146.0, 250.0),
    near_shoulder=(268.0, 212.0), near_wingtip=(204.0, 254.0), far_shoulder=(258.0, 208.0), far_wingtip=(194.0, 248.0),
    near_hip=(258.0, 262.0), near_knee=(244.0, 332.0), near_ankle=(264.0, 404.0),
    far_hip=(240.0, 260.0), far_knee=(226.0, 330.0), far_ankle=(244.0, 404.0),
)


def draw_ostrich(hen: bool = False) -> str:
    C = dict(black="#26222a", sheen="#403b48", deep="#16131a", white="#f4efe6", white_shade="#cfc7ba", skin="#e0aa9e",
             skin_shade="#bd8478", skin_dark="#9a6558", beak="#e8b8a0", beak_dark="#b07a64", claw="#4a3a36", iris="#8a5a2c")
    if hen:
        # The hen: grey-brown where the cock is black, and her plumes are dull.
        C.update(black="#8a7a68", sheen="#a8977f", deep="#5e5244", white="#cdbd9f", white_shade="#a8977f", skin="#d6b2a2",
                 skin_shade="#b48e7e", skin_dark="#8e6a5c")
    J = OSTRICH
    svg.configure(dx=0.0, dy=0.0, ink=INK, ow=OW, colors=C)
    tail = []
    for ang, ln, wd in ((150.0, 52.0, 26.0), (168.0, 58.0, 28.0), (186.0, 52.0, 26.0), (204.0, 44.0, 24.0)):
        tail += feather((196, 228), ang, ln, wd, C["white"], C["white_shade"], C["white_shade"], tip_frac=0.3)
    part("tail", "Tail", "tail", "tail", 10, tail)
    for side, z in (("far", 18), ("near", 40)):
        far = side == "far"
        legs(J, side, z, thigh=C["skin_shade"] if far else C["skin"], thigh_shade=C["skin_dark"],
             shank=C["skin_shade"] if far else C["skin"], shank_dark=C["skin_dark"], claw=C["claw"],
             toes=((10, 11), (28, 10)), thigh_r=(22.0, 9.0), shank_r=(7.0, 6.0), toe_r=(5.0, 3.6), claw_len=5.0)
    for side, z, dark in (("far", 16, True), ("near", 52, False)):
        sh, tp = J[f"{side}_shoulder"], J[f"{side}_wingtip"]
        dx, dy = sh[0] - 268.0, sh[1] - 212.0
        plumes = []
        for ang, ln, wd in ((140.0, 40.0, 22.0), (160.0, 46.0, 24.0), (180.0, 42.0, 22.0)):
            plumes += feather((230 + dx, 244 + dy), ang, ln, wd, C["white_shade"] if dark else C["white"], C["white_shade"],
                              C["white_shade"], tip_frac=0.3)
        sil = smooth([(274 + dx, 206 + dy), (282 + dx, 226 + dy), (266 + dx, 244 + dy), (238 + dx, 256 + dy),
                      (216 + dx, 252 + dy), (226 + dx, 234 + dy), (248 + dx, 216 + dy)])
        items = [line([(262 + dx, 220 + dy), (246 + dx, 236 + dy), (228 + dx, 246 + dy)], C["sheen"], 1.6)]
        del tp
        part(f"{side}-wing", f"Wing - {side}", f"{side}_wing", f"{side}_wing", z,
             plumes + outlined(sil, C["deep"] if dark else C["black"], items, f"clip-{side}-wing"))
    sil = smooth([(300, 214), (306, 238), (294, 264), (266, 280), (232, 282), (200, 270), (180, 246), (182, 218),
                  (200, 196), (232, 186), (266, 188), (288, 198)])
    items = [
        path(smooth([(214, 198), (250, 190), (282, 200), (262, 208), (226, 210)]), C["sheen"]),
        path(smooth([(184, 246), (204, 268), (236, 282), (268, 280), (240, 270), (206, 252)]), C["deep"]),
        line([(232, 234), (252, 244), (274, 238)], C["sheen"], 1.4),
        line([(222, 254), (244, 264), (266, 258)], C["sheen"], 1.4),
    ]
    part("body", "Body", "body", "body", 30, outlined(sil, C["black"], items, "clip-body"))
    centre = [(288, 216), (304, 184), (311, 144), (315, 112), (322, 94)]
    sil = smooth(tube(centre, 15.0, 7.0))
    items = [line([along(centre, 0.1), along(centre, 0.5), along(centre, 0.95)], C["skin_shade"], 5.0)]
    items += [line([(along(centre, u)[0] - 8, along(centre, u)[1]), (along(centre, u)[0] + 8, along(centre, u)[1] + 3)],
                   C["skin_shade"], 1.0) for u in (0.3, 0.45, 0.6, 0.75)]
    # a ruff of black feathers where the neck leaves the body
    ruff = shag([(274, 214), (290, 226), (304, 214)], 5, 12.0, C["black"])
    part("neck", "Neck", "neck", "neck", 60, ruff + outlined(sil, C["skin"], items, "clip-neck"))
    head = smooth([(312, 94), (314, 80), (326, 73), (338, 76), (344, 86), (340, 98), (328, 102), (316, 100)])
    body = outlined(head, C["skin"], [path(smooth([(316, 78), (328, 74), (338, 78), (326, 82)]), C["white"])], "clip-head")
    upper = smooth([(338, 84, True), (352, 90), (360, 98, True), (348, 99), (336, 97, True)])
    body += outlined(upper, C["beak"], [line([(342, 90), (354, 95)], C["beak_dark"], 1.1)], "clip-beak")
    part("head", "Head", "head", "head", 70, body)
    lower = smooth([(334, 97, True), (356, 99, True), (346, 105), (334, 104, True)])
    part("jaw", "Lower Beak", "jaw", "jaw", 69, outlined(lower, C["beak_dark"]))
    states = simple_eyes(329.0, 86.0, 5.2, C["iris"], C["skin_dark"])
    states["open"].append(line([(322, 80), (329, 78), (336, 81)], INK, 1.6))
    eye_states("eye", "head", 72, states)
    name, label = ("ostrich_hen", "Ostrich Hen") if hen else ("ostrich", "Ostrich")
    return finish(name, label, J, [
        f"  <!-- The {label.lower()}, side view facing right, on a 512x512 drawing whose",
        "       ground is y=416 (published at 0.5). Each part is a layer with a data-rig-part",
        f"       name; rigged/{name}/ turns them about their joints. The eye has open /",
        "       angry / shut / dead. The hidden Rig Joints layer marks every joint. -->"])


# ---- emu and cassowary: one build, two looks ----------------------------------------------

EMU = dict(
    body=(244.0, 252.0), neck=(286.0, 226.0), head=(318.0, 134.0), beak_tip=(354.0, 142.0), jaw=(330.0, 142.0),
    tail=(190.0, 258.0), tail_tip=(164.0, 312.0),
    near_shoulder=(266.0, 234.0), near_wingtip=(224.0, 268.0), far_shoulder=(256.0, 230.0), far_wingtip=(214.0, 262.0),
    near_hip=(256.0, 286.0), near_knee=(236.0, 344.0), near_ankle=(260.0, 404.0),
    far_hip=(240.0, 284.0), far_knee=(222.0, 342.0), far_ankle=(242.0, 404.0),
)
CASSOWARY = dict(
    body=(242.0, 258.0), neck=(284.0, 232.0), head=(312.0, 154.0), beak_tip=(350.0, 164.0), jaw=(326.0, 164.0),
    tail=(190.0, 266.0), tail_tip=(170.0, 318.0),
    near_shoulder=(264.0, 240.0), near_wingtip=(222.0, 274.0), far_shoulder=(254.0, 236.0), far_wingtip=(212.0, 268.0),
    near_hip=(256.0, 294.0), near_knee=(238.0, 348.0), near_ankle=(260.0, 404.0),
    far_hip=(240.0, 292.0), far_knee=(224.0, 346.0), far_ankle=(242.0, 404.0),
)


def shaggy_body(J: Dict[str, Point], C: Dict[str, str], *, thigh_r, shank_r, toe_r, claw_len, toes) -> None:
    """The tail that droops, the legs and the shaggy body the emu and the
    cassowary share, placed by the body joint."""
    bx, by = J["body"][0] - 244.0, J["body"][1] - 252.0

    def at(pts):
        return [(p[0] + bx, p[1] + by) + tuple(p[2:]) for p in pts]

    droop = at([(200, 232), (178, 250), (160, 292), (158, 320), (174, 314), (190, 292), (208, 268)])
    part("tail", "Tail", "tail", "tail", 10,
         shag(at([(160, 322), (158, 290), (176, 250)]), 6, 14.0, C["body_dark"]) + outlined(smooth(droop), C["body_dark"], [
             line(at([(196, 246), (178, 276), (168, 308)]), C["body"], 1.6)], "clip-tail"))
    for side, z in (("far", 18), ("near", 40)):
        far = side == "far"
        legs(J, side, z, thigh=C["body_dark"] if far else C["body"], thigh_shade=C["body_deep"],
             shank=C["leg_dark"] if far else C["leg"], shank_dark=C["leg_dark"] if not far else C["claw"], claw=C["claw"],
             toes=toes, thigh_r=thigh_r, shank_r=shank_r, toe_r=toe_r, claw_len=claw_len)
    sil = smooth(at([(296, 232), (304, 256), (292, 284), (262, 300), (226, 304), (196, 298), (176, 280), (170, 254),
                     (182, 228), (208, 210), (244, 206), (276, 212)]))
    # plumage like hair: a fringe under the belly and off the rump, and strokes down the flank
    under = shag(at([(300, 268), (264, 300), (214, 306), (178, 290), (168, 256)]), 13, 20.0, C["body"], C["body_deep"])
    items = [
        path(smooth(at([(212, 214), (246, 208), (278, 216), (258, 226), (224, 228)])), C["body_light"]),
        path(smooth(at([(174, 262), (196, 290), (232, 304), (264, 298), (236, 286), (200, 268)])), C["body_dark"]),
    ]
    for k in range(7):
        x = 198 + 14 * k
        items.append(line(at([(x, 226 + 2 * (k % 2)), (x - 6, 252), (x - 14, 280)]), C["body_deep"], 1.2))
    part("body", "Body", "body", "body", 30, under + outlined(sil, C["body"], items, "clip-body"))
    # the wing: a small flap lost in the plumage
    for side, z in (("far", 16), ("near", 52)):
        sh = J[f"{side}_shoulder"]
        dx, dy = sh[0] - 266.0, sh[1] - 234.0
        sil = smooth([(270 + dx, 230 + dy), (274 + dx, 246 + dy), (256 + dx, 262 + dy), (230 + dx, 272 + dy),
                      (222 + dx, 264 + dy), (240 + dx, 246 + dy)])
        part(f"{side}-wing", f"Wing - {side}", f"{side}_wing", f"{side}_wing", z,
             outlined(sil, C["body_dark"] if side == "far" else C["body"],
                      [line([(262 + dx, 240 + dy), (246 + dx, 254 + dy), (230 + dx, 266 + dy)], C["body_deep"], 1.3)],
                      f"clip-{side}-wing"))


def draw_emu() -> str:
    C = dict(body="#7d6c58", body_light="#a08e76", body_dark="#5c4e40", body_deep="#3e342a", skin="#7c97b4",
             skin_shade="#58708c", leg="#5a5a60", leg_dark="#3a3a40", claw="#22222a", beak="#3e3e46", beak_dark="#26262c",
             iris="#d2552a", tuft="#2a2622")
    J = EMU
    svg.configure(dx=0.0, dy=0.0, ink=INK, ow=OW, colors=C)
    shaggy_body(J, C, thigh_r=(22.0, 10.0), shank_r=(6.5, 5.5), toe_r=(4.6, 3.2), claw_len=5.0,
                toes=((-8, 9), (14, 12), (27, 9)))
    centre = [(284, 234), (300, 204), (308, 172), (313, 150), (318, 136)]
    sil = smooth(tube(centre, 17.0, 8.0))
    # a collar of feathers over the lower neck, ragged at its top
    collar = [(260, 250), (262, 212), (274, 200), (282, 210), (292, 194), (300, 204), (312, 190), (322, 204), (322, 250)]
    items = [path(svg.poly(collar), C["body"]), line([along(centre, 0.55), along(centre, 0.95)], C["skin_shade"], 4.0),
             line([(286, 212), (282, 236)], C["body_deep"], 1.2), line([(300, 208), (296, 234)], C["body_deep"], 1.2)]
    part("neck", "Neck", "neck", "neck", 60, outlined(sil, C["skin"], items, "clip-neck"))
    head = smooth([(306, 138), (308, 124), (320, 116), (334, 118), (342, 128), (340, 142), (328, 148), (312, 146)])
    tuft = shag([(304, 134), (310, 120), (324, 114), (338, 120)], 7, 11.0, C["tuft"], lean=-0.4)
    body = tuft + outlined(head, C["skin"], [path(smooth([(306, 130), (316, 118), (334, 118), (322, 126)]), C["tuft"])],
                           "clip-head")
    upper = smooth([(336, 126, True), (350, 132), (356, 142, True), (344, 143), (334, 140, True)])
    body += outlined(upper, C["beak"], [], None)
    part("head", "Head", "head", "head", 70, body)
    lower = smooth([(330, 141, True), (352, 143, True), (342, 149), (330, 148, True)])
    part("jaw", "Lower Beak", "jaw", "jaw", 69, outlined(lower, C["beak_dark"]))
    eye_states("eye", "head", 72, simple_eyes(326.0, 129.0, 5.0, C["iris"], C["tuft"]))
    return finish("emu", "Emu", J, [
        "  <!-- The emu, side view facing right, on a 512x512 drawing whose ground is",
        "       y=416 (published at 0.5). Each part is a layer with a data-rig-part name;",
        "       rigged/emu/ turns them about their joints. The eye has open / angry / shut",
        "       / dead. The hidden Rig Joints layer marks every joint. -->"])


def draw_cassowary() -> str:
    C = dict(body="#24212b", body_light="#45414f", body_dark="#18161d", body_deep="#0c0b10", skin="#2f74d6",
             skin_light="#69a6f2", skin_shade="#1d4c98", red="#dc3b2a", red_dark="#9c1c1a", leg="#7a7868", leg_dark="#4e4c40",
             claw="#1c1a18", beak="#4a4a50", beak_dark="#2a2a30", iris="#c98a2c", casque="#8f7a58", casque_light="#b8a47c",
             casque_dark="#5e4e36")
    J = CASSOWARY
    svg.configure(dx=0.0, dy=0.0, ink=INK, ow=OW, colors=C)
    shaggy_body(J, C, thigh_r=(25.0, 12.0), shank_r=(8.5, 7.5), toe_r=(5.4, 3.8), claw_len=8.0,
                toes=((-9, 9), (15, 12), (29, 9)))
    centre = [(282, 240), (296, 212), (303, 186), (307, 168), (312, 156)]
    sil = smooth(tube(centre, 18.0, 9.5))
    items = [
        line([along(centre, 0.15), along(centre, 0.6), along(centre, 0.95)], C["skin_light"], 5.0),
        # the nape: red down the back of the neck
        path(smooth([(272, 238), (282, 208), (292, 184), (296, 196), (290, 222), (284, 246)]), C["red"]),
        path(svg.poly([(258, 258), (260, 226), (272, 216), (280, 228), (292, 216), (302, 228), (314, 218), (318, 258)]),
             C["body"]),
    ]
    # two wattles hanging off the front of the neck
    wattles = []
    for x, y, ln in ((304.0, 200.0, 30.0), (311.0, 196.0, 26.0)):
        wattles += outlined(svg.capsule((x, y), (x + 3, y + ln), 4.0, 6.5), C["red"], [
            line([(x, y + 4), (x + 2, y + ln - 6)], C["red_dark"], 1.4)], f"clip-wattle-{int(x)}")
    part("neck", "Neck", "neck", "neck", 60, outlined(sil, C["skin"], items, "clip-neck") + wattles)
    # the casque: a tall blade of horn on the crown
    casque = smooth([(300, 148, True), (300, 120), (310, 100), (324, 96, True), (332, 116), (332, 140, True)])
    body = outlined(casque, C["casque"], [
        path(smooth([(304, 140), (304, 120), (312, 104), (316, 122), (314, 142)]), C["casque_light"]),
        line([(322, 102), (326, 120), (326, 138)], C["casque_dark"], 1.6)], "clip-casque")
    head = smooth([(298, 158), (300, 144), (312, 136), (328, 138), (338, 148), (336, 164), (324, 170), (306, 168)])
    body += outlined(head, C["skin"], [path(smooth([(300, 160), (308, 168), (324, 170), (312, 162)]), C["skin_shade"]),
                                       path(smooth([(304, 146), (316, 138), (330, 142), (318, 146)]), C["skin_light"])],
                     "clip-head")
    upper = smooth([(332, 146, True), (346, 152), (352, 164, True), (340, 165), (330, 162, True)])
    body += outlined(upper, C["beak"], [], None)
    part("head", "Head", "head", "head", 70, body)
    lower = smooth([(326, 163, True), (348, 165, True), (338, 171), (326, 170, True)])
    part("jaw", "Lower Beak", "jaw", "jaw", 69, outlined(lower, C["beak_dark"]))
    eye_states("eye", "head", 72, simple_eyes(322.0, 150.0, 5.0, C["iris"], C["skin_shade"]))
    return finish("cassowary", "Cassowary", J, [
        "  <!-- The cassowary, side view facing right, on a 512x512 drawing whose ground is",
        "       y=416 (published at 0.5). Each part is a layer with a data-rig-part name;",
        "       rigged/cassowary/ turns them about their joints. The eye has open / angry /",
        "       shut / dead. The hidden Rig Joints layer marks every joint. -->"])


# ---- kiwi -----------------------------------------------------------------------------

KIWI = dict(
    body=(236.0, 332.0), neck=(280.0, 306.0), head=(302.0, 292.0), beak_tip=(398.0, 362.0), jaw=(318.0, 302.0),
    tail=(178.0, 344.0), tail_tip=(160.0, 358.0),
    near_shoulder=(250.0, 312.0), near_wingtip=(228.0, 334.0), far_shoulder=(244.0, 310.0), far_wingtip=(222.0, 332.0),
    near_hip=(254.0, 366.0), near_knee=(242.0, 386.0), near_ankle=(260.0, 404.0),
    far_hip=(224.0, 364.0), far_knee=(212.0, 386.0), far_ankle=(228.0, 404.0),
)


def draw_kiwi() -> str:
    C = dict(body="#8c6a48", body_light="#b08c62", body_dark="#684c32", body_deep="#46321f", beak="#ead9b8",
             beak_dark="#b99c70", leg="#c29a66", leg_dark="#8a6a40", claw="#3a2a1a", iris="#1a1210")
    J = KIWI
    svg.configure(dx=0.0, dy=0.0, ink=INK, ow=OW, colors=C)
    # no tail to see: a tuft of the body's own shag on the tail bone
    part("tail", "Tail", "tail", "tail", 10, shag([(170, 364), (166, 340), (180, 322)], 4, 12.0, C["body_dark"]))
    for side, z in (("far", 18), ("near", 40)):
        far = side == "far"
        legs(J, side, z, thigh=C["body_dark"] if far else C["body"], thigh_shade=C["body_deep"],
             shank=C["leg_dark"] if far else C["leg"], shank_dark=C["claw"] if far else C["leg_dark"], claw=C["claw"],
             toes=((-9, 9), (14, 12), (25, 8)), thigh_r=(15.0, 8.0), shank_r=(6.0, 5.5), toe_r=(4.6, 3.2), claw_len=5.0)
    sil = smooth([(292, 302), (304, 332), (296, 362), (268, 384), (228, 388), (192, 376), (172, 350), (170, 320),
                  (186, 296), (216, 280), (256, 278)])
    under = shag([(302, 344), (270, 384), (226, 390), (186, 376), (168, 342), (172, 312)], 14, 13.0, C["body"],
                 C["body_deep"])
    items = [
        path(smooth([(214, 286), (250, 282), (282, 296), (258, 300), (226, 298)]), C["body_light"]),
        path(smooth([(172, 350), (194, 376), (230, 388), (266, 384), (238, 374), (200, 356)]), C["body_dark"]),
    ]
    for k in range(8):
        x = 196 + 12 * k
        items.append(line([(x, 300 + 3 * (k % 2)), (x - 5, 326), (x - 12, 352)], C["body_deep"], 1.2))
    part("body", "Body", "body", "body", 30, under + outlined(sil, C["body"], items, "clip-body"))
    # the neck is only where the head sits on the body
    neck = smooth([(266, 314), (270, 294), (286, 284), (302, 290), (306, 308), (294, 322), (276, 324)])
    part("neck", "Neck", "neck", "neck", 60, [path(neck, C["body"])])
    head = smooth([(282, 300), (286, 282), (300, 272), (316, 276), (324, 290), (320, 304), (306, 312), (290, 310)])
    body = outlined(head, C["body"], [path(smooth([(288, 284), (300, 276), (314, 280), (302, 286)]), C["body_light"])],
                    "clip-head")
    # whiskers at the root of the beak
    for dy in (-8, -2, 6):
        body.append(line([(312, 296), (328, 290 + dy), (340, 286 + 2 * dy)], C["body_deep"], 0.9))
    upper = smooth([(314, 288, True), (330, 294), (398, 358, True), (396, 364, True), (318, 302, True)])
    body += outlined(upper, C["beak"], [line([(322, 296), (390, 356)], C["beak_dark"], 1.0)], "clip-beak")
    part("head", "Head", "head", "head", 70, body)
    lower = smooth([(316, 300, True), (392, 362, True), (386, 364, True), (318, 306, True)])
    part("jaw", "Lower Beak", "jaw", "jaw", 69, outlined(lower, C["beak_dark"]))
    eye_states("eye", "head", 72, simple_eyes(306.0, 287.0, 3.2, C["iris"], C["body_deep"]))
    return finish("kiwi", "Kiwi", J, [
        "  <!-- The kiwi, side view facing right, on a 512x512 drawing whose ground is",
        "       y=416 (published at 0.25). Each part is a layer with a data-rig-part name;",
        "       rigged/kiwi/ turns them about their joints. The eye has open / angry / shut",
        "       / dead. The hidden Rig Joints layer marks every joint. -->"])


# ---- shoebill ---------------------------------------------------------------------------

SHOEBILL = dict(
    body=(244.0, 250.0), neck=(280.0, 226.0), head=(300.0, 150.0), beak_tip=(374.0, 198.0), jaw=(316.0, 172.0),
    tail=(194.0, 262.0), tail_tip=(158.0, 284.0),
    near_shoulder=(268.0, 226.0), near_wingtip=(190.0, 284.0), far_shoulder=(258.0, 222.0), far_wingtip=(180.0, 278.0),
    near_hip=(254.0, 290.0), near_knee=(240.0, 348.0), near_ankle=(258.0, 404.0),
    far_hip=(238.0, 288.0), far_knee=(224.0, 346.0), far_ankle=(240.0, 404.0),
)


def draw_shoebill() -> str:
    C = dict(grey="#6f8192", light="#98a9b7", dark="#4f5f6e", deep="#33404c", bill="#dcc78e", bill_light="#efe0b0",
             bill_dark="#a38d5a", bill_blotch="#7d6a40", leg="#3d434b", leg_dark="#24282e", claw="#15171a", iris="#f3e38c")
    J = SHOEBILL
    svg.configure(dx=0.0, dy=0.0, ink=INK, ow=OW, colors=C)
    tail = []
    for ang, ln, wd in ((148.0, 44.0, 20.0), (164.0, 50.0, 22.0), (180.0, 44.0, 20.0)):
        tail += feather((200, 264), ang, ln, wd, C["dark"], C["deep"], C["deep"], tip_frac=0.35)
    part("tail", "Tail", "tail", "tail", 10, tail)
    for side, z in (("far", 18), ("near", 40)):
        far = side == "far"
        legs(J, side, z, thigh=C["dark"] if far else C["grey"], thigh_shade=C["deep"],
             shank=C["leg_dark"] if far else C["leg"], shank_dark=C["claw"] if far else C["leg_dark"], claw=C["claw"],
             toes=((-14, 9), (18, 12), (34, 8)), thigh_r=(18.0, 8.0), shank_r=(5.5, 5.0), toe_r=(4.2, 2.8), claw_len=5.0)
    # the wing: broad, folded along the flank, dark flight feathers at its end
    for side, z, dark in (("far", 16, True), ("near", 52, False)):
        sh = J[f"{side}_shoulder"]
        dx, dy = sh[0] - 268.0, sh[1] - 226.0

        def at(pts, dx=dx, dy=dy):
            return [(q[0] + dx, q[1] + dy) + tuple(q[2:]) for q in pts]

        flight = []
        for ang, ln, wd in ((146.0, 46.0, 20.0), (160.0, 52.0, 22.0), (174.0, 46.0, 20.0)):
            flight += feather((224 + dx, 270 + dy), ang, ln, wd, C["deep"], C["dark"], C["dark"], tip_frac=0.3)
        sil = smooth(at([(274, 220), (282, 244), (268, 268), (240, 284), (212, 288), (206, 274), (224, 250), (250, 228)]))
        items = [line(at([(266, 238), (270, 252), (262, 264)]), C["deep"], 1.3),
                 line(at([(248, 244), (252, 258), (244, 272)]), C["deep"], 1.3),
                 line(at([(230, 256), (234, 268), (226, 280)]), C["deep"], 1.3),
                 path(smooth(at([(270, 224), (278, 242), (270, 256), (262, 238)])), C["light"])]
        part(f"{side}-wing", f"Wing - {side}", f"{side}_wing", f"{side}_wing", z,
             flight + outlined(sil, C["dark"] if dark else C["grey"], items, f"clip-{side}-wing"))
    sil = smooth([(292, 226), (300, 252), (290, 282), (262, 300), (228, 302), (198, 292), (180, 270), (178, 244),
                  (192, 220), (220, 206), (254, 204), (280, 212)])
    items = [
        path(smooth([(276, 236), (294, 250), (288, 280), (264, 298), (262, 270)]), C["light"]),
        path(smooth([(180, 270), (200, 292), (230, 302), (256, 300), (228, 288), (200, 272)]), C["dark"]),
        line([(270, 262), (280, 268), (290, 262)], C["dark"], 1.2),
        line([(262, 280), (272, 286), (282, 280)], C["dark"], 1.2),
    ]
    part("body", "Body", "body", "body", 30, outlined(sil, C["grey"], items, "clip-body"))
    centre = [(278, 234), (288, 206), (294, 182), (298, 164), (300, 152)]
    sil = smooth(tube(centre, 21.0, 16.0))
    items = [line([along(centre, 0.1), along(centre, 0.6), along(centre, 0.95)], C["light"], 6.0)]
    part("neck", "Neck", "neck", "neck", 60, outlined(sil, C["grey"], items, "clip-neck"))
    # a small crest at the back of the head
    body = []
    for ang, ln in ((218.0, 22.0), (236.0, 26.0), (254.0, 20.0)):
        body += feather((286, 130), ang, ln, 9.0, C["dark"], None, C["deep"], sw=1.0)
    head = smooth([(278, 150), (280, 130), (294, 118), (314, 116), (330, 126), (334, 146), (324, 162), (304, 168),
                   (286, 164)])
    body += outlined(head, C["grey"], [path(smooth([(286, 128), (300, 120), (318, 122), (304, 130)]), C["light"]),
                                       path(smooth([(280, 152), (290, 164), (306, 168), (294, 158)]), C["dark"])],
                     "clip-head")
    # the bill: a great clog with a hooked nail at its tip
    upper = smooth([(316, 130, True), (340, 132), (360, 150), (372, 176), (374, 200, True), (362, 190), (338, 178),
                    (316, 170, True)])
    body += outlined(upper, C["bill"], [
        path(smooth([(322, 136), (342, 138), (360, 156), (342, 152), (324, 146)]), C["bill_light"]),
        ellipse(338, 160, 6.0, 4.0, C["bill_blotch"]), ellipse(354, 172, 5.0, 3.6, C["bill_blotch"]),
        ellipse(326, 156, 3.6, 2.6, C["bill_blotch"]),
        line([(320, 150), (346, 158), (366, 180)], C["bill_dark"], 1.4),
        path(smooth([(366, 184), (374, 190), (374, 200), (366, 194)]), C["bill_dark"]),
    ], "clip-bill")
    part("head", "Head", "head", "head", 70, body)
    lower = smooth([(314, 168, True), (338, 180), (366, 196, True), (354, 206), (330, 198), (314, 184, True)])
    part("jaw", "Lower Beak", "jaw", "jaw", 69, outlined(lower, C["bill_dark"], [
        line([(320, 178), (344, 190), (358, 198)], C["bill_blotch"], 1.2)], "clip-jaw"))
    # the stare: a pale eye under a brow that never lifts
    states = simple_eyes(308.0, 138.0, 6.6, C["iris"], C["deep"])
    brow = path(smooth([(296, 128, True), (320, 134, True), (320, 129, True), (298, 123, True)]), C["deep"], INK, 0.9)
    states["open"] = [ellipse(308.0, 138.0, 6.6, 6.6, C["iris"], INK, 1.4), ellipse(309.0, 138.5, 2.2, 2.2, "#120d0f"),
                      ellipse(306.0, 135.8, 1.3, 1.3, "#ffffff"), brow]
    eye_states("eye", "head", 72, states)
    return finish("shoebill", "Shoebill", J, [
        "  <!-- The shoebill, side view facing right, on a 512x512 drawing whose ground is",
        "       y=416 (published at 0.5). Each part is a layer with a data-rig-part name;",
        "       rigged/shoebill/ turns them about their joints. The eye has open / angry /",
        "       shut / dead. The hidden Rig Joints layer marks every joint. -->"])


DRAW = {"ostrich": draw_ostrich, "ostrich_hen": lambda: draw_ostrich(hen=True), "emu": draw_emu,
        "cassowary": draw_cassowary, "kiwi": draw_kiwi, "shoebill": draw_shoebill}

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    for name, draw in DRAW.items():
        (out / f"{name}.svg").write_text(draw())
