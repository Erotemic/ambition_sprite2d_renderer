#!/usr/bin/env python3
"""How the Stochastic Parrot's SVGs were first drawn (reference, not authority).

``data/characters/stochastic_parrot_v2/stochastic_parrot_v2.svg`` (side),
``stochastic_parrot_v2_front.svg`` (facing the viewer) and
``stochastic_parrot_v2_three_quarter.svg`` (turned halfway between) own the
art; this script reproduces them as first committed (less the rig catalog
``scripts/build_stochastic_parrot_v2_rig.py`` installs).

    uv run python scripts/svg_art/stochastic_parrot_art.py SIDE.svg FRONT.svg THREE_QUARTER.svg

A scarlet macaw on a 512x512 canvas, ground y=416, centre line x=256
(published at 0.25: a 128 px frame). The side view swaps a folded wing (on
the body) for a spread fan (two bones a wing: the arm to the wrist, the
primaries to the tip) when it flies.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import svgkit as svg
from svgkit import clipped, ellipse, line, part, path, smooth

W, H = 512, 512
INK = "#1d1418"
OW = 1.6

C = dict(
    red="#d8352b",
    red_light="#f0634a",
    red_dark="#9c1c1a",
    red_deep="#6e1214",
    yellow="#f6c632",
    yellow_dark="#c8901c",
    green="#5fa64a",
    blue="#2f6fd0",
    blue_light="#5e9cf0",
    blue_dark="#1b3f8a",
    face="#f4ede4",
    face_line="#b9302a",
    beak="#efe4cf",
    beak_shadow="#c9b79a",
    beak_dark="#2b2326",
    eye="#f7e7a6",
    iris="#f0c040",
    pupil="#120d0f",
    leg="#7c7f8c",
    leg_dark="#4d4f5a",
    mouth="#3a1418",
    tongue="#2b2326",
    stripe="#1b3f8a",
)

J = dict(
    body=(250.0, 328.0),
    neck=(282.0, 246.0),
    beak_tip=(352.0, 250.0),
    jaw=(320.0, 232.0),
    tail1=(230.0, 368.0),
    tail2=(168.0, 392.0),
    tail_tip=(96.0, 404.0),
    near_shoulder=(268.0, 266.0),
    near_wrist=(236.0, 168.0),
    near_wingtip=(148.0, 94.0),
    far_shoulder=(256.0, 260.0),
    far_wrist=(214.0, 170.0),
    far_wingtip=(128.0, 104.0),
    near_hip=(258.0, 362.0),
    near_knee=(266.0, 386.0),
    near_ankle=(270.0, 404.0),
    far_hip=(242.0, 360.0),
    far_knee=(248.0, 386.0),
    far_ankle=(250.0, 404.0),
)


def outlined(sil, fill, items=(), cid=None, width=None):
    body = [path(sil, fill)]
    if items:
        body = clipped(cid, sil, [path(sil, fill)] + list(items))
    return body + [path(sil, "none", INK, width or 2 * OW)]


def feather(base, angle, length, width, fill, tip=None, edge=INK, sw=1.2):
    """One long feather from ``base`` toward ``angle`` (degrees, y down)."""
    a = math.radians(angle)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    bx, by = base

    def at(t, w):
        return (bx + ux * length * t + nx * w, by + uy * length * t + ny * w)

    pts = [at(0.0, width * 0.45), at(0.5, width * 0.55), at(0.9, width * 0.35), at(1.0, 0.0) + (True,),
           at(0.9, -width * 0.35), at(0.5, -width * 0.55), at(0.0, -width * 0.45)]
    out = [path(smooth(pts), fill, edge, sw)]
    if tip:
        tp = [at(0.62, width * 0.52), at(0.9, width * 0.35), at(1.0, 0.0) + (True,), at(0.9, -width * 0.35),
              at(0.62, -width * 0.52)]
        out.append(path(smooth(tp), tip))
        out.append(path(smooth(pts), "none", edge, sw))
    out.append(line([at(0.05, 0.0), at(0.92, 0.0)], C["red_deep"] if fill == C["red"] else C["blue_dark"], 0.8))
    return out


# ---- side view ------------------------------------------------------------------------
BODY = [(286, 244), (304, 262), (310, 290), (302, 326), (282, 356), (256, 374), (230, 376), (212, 360), (210, 330),
        (222, 296), (244, 266), (264, 248)]
HEAD = [(262, 222), (266, 196), (282, 176), (306, 170), (326, 180), (336, 200), (334, 224), (322, 242), (300, 252),
        (278, 250)]


def side_parts():
    # The tail: graduated red feathers tipped with blue, fanning back.
    tail = []
    for k, (ang, ln, wd) in enumerate(((176.0, 150.0, 22.0), (170.0, 168.0, 24.0), (164.0, 140.0, 20.0))):
        tail += feather((236 - 4 * k, 362 + 3 * k), ang - 6.0, ln, wd, C["red"], C["blue"])
    part("tail", "Tail", "tail", "tail1", 10, tail)
    tip = []
    for k, (ang, ln, wd) in enumerate(((172.0, 70.0, 16.0), (166.0, 82.0, 18.0))):
        tip += feather((150 + 4 * k, 392 + 2 * k), ang, ln, wd, C["blue"], C["blue_light"])
    part("tail-tip", "Tail Tip", "tail_tip", "tail2", 9, tip)

    # Far wing, spread (behind the body): a darker fan.
    open_wing("far", 14, dark=True)
    # Legs (the far one behind).
    for side, z in (("far", 18), ("near", 40)):
        legs(side, z)

    sil = smooth(BODY)
    items = [
        path(smooth([(290, 252), (306, 270), (308, 300), (294, 300), (284, 270)]), C["red_light"]),
        path(smooth([(214, 330), (226, 300), (236, 330), (230, 372), (214, 360)]), C["red_dark"]),
        # the belly's feather scallops
        line([(262, 300), (276, 306), (290, 300)], C["red_dark"], 1.2),
        line([(250, 322), (266, 330), (284, 324)], C["red_dark"], 1.2),
        line([(244, 346), (258, 352), (272, 346)], C["red_dark"], 1.2),
    ]
    part("body", "Body", "body", "body", 30, outlined(sil, C["red"], items, "clip-body"))

    # The folded wing on the body: red shoulder coverts, a yellow band with
    # green tips, blue flight feathers running back over the tail.
    folded = smooth([(270, 258), (284, 276), (280, 306), (262, 334), (232, 366), (196, 396), (178, 404), (194, 380),
                     (214, 340), (232, 300), (248, 270)])
    items = [
        path(smooth([(270, 258), (284, 276), (280, 300), (258, 300), (246, 284), (252, 266)]), C["red_dark"]),
        path(smooth([(280, 300), (270, 322), (244, 330), (232, 312), (246, 296), (262, 298)]), C["yellow"]),
        line([(244, 314), (256, 320), (268, 316)], C["yellow_dark"], 1.3),
        path(smooth([(270, 322), (256, 342), (238, 346), (232, 330), (244, 330)]), C["green"]),
        path(smooth([(256, 342), (232, 366), (196, 396), (178, 404), (196, 378), (222, 344), (238, 346)]), C["blue"]),
        line([(250, 344), (214, 372), (186, 398)], C["blue_dark"], 1.3),
        line([(240, 340), (206, 366)], C["blue_light"], 1.6),
    ]
    part("near-wing-folded", "Wing - Folded", "near_wing_folded", "body", 52,
         outlined(folded, C["red"], items, "clip-folded"), ' data-rig-opacity="wing.folded" data-rig-default="1"')
    open_wing("near", 60, dark=False)

    head_parts()


def open_wing(side, z, dark):
    """The spread wing, drawn raised up and back. The arm (shoulder to
    wrist) carries the coverts in bands (red, yellow, green) over a row of
    blue secondaries trailing back; the hand (wrist to tip) the long blue
    primaries, fingered apart. A flap turns the arm about the shoulder and
    the hand about the wrist."""
    sh, wr, tip = J[f"{side}_shoulder"], J[f"{side}_wrist"], J[f"{side}_wingtip"]
    red = C["red_dark"] if dark else C["red"]
    yellow = C["yellow_dark"] if dark else C["yellow"]
    green = "#3f7a36" if dark else C["green"]
    blue = C["blue_dark"] if dark else C["blue"]
    blue_tip = C["blue"] if dark else C["blue_light"]

    def lerp(a, b, u):
        return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)

    # Secondaries: a row of broad feathers along the trailing edge, from the
    # wrist (pointing up and back) to the body (pointing back, a little down).
    items = []
    for k in range(6):
        u = k / 5.0
        base = lerp((wr[0] - 10, wr[1] + 16), (sh[0] - 30, sh[1] + 2), u)
        items += feather(base, 214.0 - 40.0 * u, 70.0 - 14.0 * u, 22.0, blue, blue_tip, sw=1.1)
    # The arm: leading edge from shoulder bulging forward to the wrist,
    # trailing edge back over the secondaries' roots.
    arm = smooth([(sh[0] + 4, sh[1] + 8), (sh[0] + 14, sh[1] - 44), (wr[0] + 12, wr[1] + 2), wr + (True,),
                  (wr[0] - 22, wr[1] + 26), (sh[0] - 40, sh[1] - 2), (sh[0] - 22, sh[1] + 16)])
    bands = [
        # lesser coverts: red along the leading edge
        path(smooth([(sh[0] + 4, sh[1] + 8), (sh[0] + 14, sh[1] - 44), (wr[0] + 12, wr[1] + 2), wr,
                     (wr[0] - 6, wr[1] + 14), (sh[0] - 6, sh[1] - 22), (sh[0] - 10, sh[1] + 4)]), red),
        # median coverts: the yellow band
        path(smooth([(wr[0] - 6, wr[1] + 14), (sh[0] - 6, sh[1] - 22), (sh[0] - 10, sh[1] + 4),
                     (sh[0] - 26, sh[1] + 4), (sh[0] - 22, sh[1] - 24), (wr[0] - 16, wr[1] + 22)]), yellow),
        # greater coverts: green
        path(smooth([(wr[0] - 16, wr[1] + 22), (sh[0] - 22, sh[1] - 24), (sh[0] - 26, sh[1] + 4),
                     (sh[0] - 42, sh[1] + 2), (wr[0] - 24, wr[1] + 30)]), green),
        line([(sh[0] - 4, sh[1] - 8), (sh[0] - 6, sh[1] - 34), (wr[0] + 0, wr[1] + 18)], C["red_deep"], 1.0),
        line([(sh[0] - 18, sh[1] - 2), (sh[0] - 18, sh[1] - 26), (wr[0] - 12, wr[1] + 24)],
             C["yellow_dark"] if not dark else "#8a6414", 1.0),
    ]
    if not dark:
        bands.append(line([(sh[0] + 6, sh[1] - 10), (sh[0] + 10, sh[1] - 40), (wr[0] + 8, wr[1] + 6)],
                          C["red_light"], 2.4))
    items += outlined(arm, red, bands, f"clip-{side}-arm")
    part(f"{side}-wing-arm", f"Wing Arm - {side}", f"{side}_wing_arm", f"{side}_wing", z + 1, items,
         ' data-rig-opacity="wing.open"')
    # The primaries: six long feathers fanned out from the wrist, the outer
    # (longest) toward the tip, each a little apart from the next.
    hand = []
    ang0 = math.degrees(math.atan2(tip[1] - wr[1], tip[0] - wr[0]))
    reach = math.hypot(tip[0] - wr[0], tip[1] - wr[1])
    for k in range(5, -1, -1):
        base = (wr[0] - 3.0 * k, wr[1] + 5.0 * k)
        hand += feather(base, ang0 - 4.0 + 7.5 * k, reach * (1.12 - 0.07 * k), 21.0, blue, blue_tip, sw=1.2)
    # the alula and primary coverts over the feathers' roots
    hand += outlined(smooth([(wr[0] + 8, wr[1] + 4), (wr[0] - 4, wr[1] - 12), (wr[0] - 30, wr[1] - 20),
                             (wr[0] - 34, wr[1] - 6), (wr[0] - 18, wr[1] + 16)]), blue,
                     [line([(wr[0] - 2, wr[1] - 4), (wr[0] - 26, wr[1] - 10)], blue_tip, 1.4)], f"clip-{side}-alula")
    part(f"{side}-wing-hand", f"Wing Hand - {side}", f"{side}_wing_hand", f"{side}_hand", z, hand,
         ' data-rig-opacity="wing.open"')


def legs(side, z):
    """Feathered thighs (trousers) mostly under the belly, grey scaled
    shanks, and zygodactyl feet (two toes forward, two back)."""
    hip, knee, ankle = J[f"{side}_hip"], J[f"{side}_knee"], J[f"{side}_ankle"]
    fill = C["red_dark"] if side == "far" else C["red"]
    thigh = svg.capsule(hip, knee, 14.0, 10.0)
    part(f"{side}-leg-u", f"Thigh - {side}", f"{side}_leg_u", f"{side}_leg_u", z - 14 if side == "near" else z,
         outlined(thigh, fill, [line([(hip[0] - 6, hip[1] + 4), (knee[0] - 4, knee[1] - 2)], C["red_dark"], 1.0)],
                  f"clip-{side}-thigh"))
    leg = svg.capsule(knee, ankle, 6.0, 5.0)
    scales = [line([(knee[0] - 5 + 0.2 * k, knee[1] + 4 + 4 * k), (knee[0] + 5 + 0.2 * k, knee[1] + 3 + 4 * k)],
                   C["leg_dark"], 0.9) for k in range(4)]
    part(f"{side}-leg-l", f"Shank - {side}", f"{side}_leg_l", f"{side}_leg_l", z,
         outlined(leg, C["leg"], scales, f"clip-{side}-shank"))
    ax, ay = ankle
    toes = []
    for dx, dy in ((-12, 10), (-6, 12), (20, 9), (13, 12)):
        toes += outlined(svg.capsule((ax, ay), (ax + dx, ay + dy), 4.0, 3.0), C["leg"])
        s = 1.0 if dx > 0 else -1.0
        toes.append(path(smooth([(ax + dx - s * 1, ay + dy - 2), (ax + dx + s * 4, ay + dy + 1),
                                 (ax + dx + s * 1, ay + dy + 5)], closed=False), "none", C["beak_dark"], 2.0))
    part(f"{side}-foot", f"Foot - {side}", f"{side}_foot", f"{side}_foot", z + 2, toes)


def head_parts():
    sil = smooth(HEAD)
    items = [
        path(smooth([(278, 182), (300, 174), (318, 180), (300, 190), (282, 194)]), C["red_light"]),
        path(smooth([(264, 214), (276, 236), (300, 250), (276, 250), (262, 236)]), C["red_dark"]),
        # The bare white face patch round the eye, lined with tiny red feathers.
        path(smooth([(300, 186), (322, 184), (334, 200), (330, 224), (314, 234), (300, 222), (296, 202)]), C["face"]),
        line([(304, 214), (312, 218), (322, 216)], C["face_line"], 1.0),
        line([(306, 222), (314, 226), (322, 224)], C["face_line"], 1.0),
        line([(310, 230), (318, 232)], C["face_line"], 1.0),
    ]
    body = outlined(sil, C["red"], items, "clip-head")
    # The upper mandible: the great hooked beak, its tip dark.
    upper = smooth([(320, 190), (338, 196), (350, 212), (356, 234), (352, 252, True), (344, 240), (334, 232), (324, 230)])
    body += outlined(upper, C["beak"], [
        path(smooth([(352, 230), (356, 236), (352, 252), (344, 242)]), C["beak_dark"]),
        path(smooth([(326, 214), (340, 218), (344, 230), (330, 228)]), C["beak_shadow"]),
        ellipse(330, 202, 1.8, 1.4, C["beak_dark"]),
    ], "clip-beak")
    part("head", "Head", "head", "head", 70, body)
    # The lower mandible, hinged at the jaw: dark, scooped.
    lower = smooth([(318, 232), (332, 234), (342, 244), (338, 252), (326, 250), (316, 242)])
    part("jaw", "Lower Beak", "jaw", "jaw", 69, outlined(lower, C["beak_dark"], [
        line([(322, 238), (336, 244)], "#4a3f42", 1.4)], "clip-jaw"))
    # Eye states.
    ex, ey = 314.0, 204.0
    part("eye-open", "Eye - Open", "eye_open", "head", 72,
         [ellipse(ex, ey, 6.5, 6.5, C["iris"], INK, 1.4), ellipse(ex + 1, ey, 3.2, 3.6, C["pupil"]),
          ellipse(ex - 1.5, ey - 2, 1.4, 1.4, "#ffffff")], ' data-rig-opacity="eye.open" data-rig-default="1"')
    part("eye-angry", "Eye - Angry", "eye_angry", "head", 72,
         [ellipse(ex, ey, 6.5, 6.5, C["iris"], INK, 1.4), ellipse(ex + 1.5, ey + 0.5, 2.2, 2.6, C["pupil"]),
          path(smooth([(ex - 10, ey - 10, True), (ex + 10, ey - 3, True), (ex + 10, ey - 8, True)]), C["red_deep"], INK, 1.0)],
         ' data-rig-opacity="eye.angry"')
    part("eye-shut", "Eye - Shut", "eye_shut", "head", 72, [line([(ex - 7, ey), (ex, ey + 3), (ex + 7, ey)], INK, 2.0)],
         ' data-rig-opacity="eye.shut"')
    part("eye-dead", "Eye - Dead", "eye_dead", "head", 72,
         [line([(ex - 5, ey - 5), (ex + 5, ey + 5)], INK, 2.2), line([(ex - 5, ey + 5), (ex + 5, ey - 5)], INK, 2.2)],
         ' data-rig-opacity="eye.dead"')


def draw_side() -> str:
    svg.configure(dx=0.0, dy=0.0, ink=INK, ow=OW, colors=C)
    side_parts()
    return svg.document(
        size=(W, H),
        design="stochastic-parrot-v2-side",
        layer_id="parrot-side",
        label="Stochastic Parrot - Side Right",
        comment=[
            "  <!-- The Stochastic Parrot, a scarlet macaw, side view facing right, on a",
            "       512x512 drawing whose ground is y=416 (published at 0.25). Each part is a",
            "       layer with a data-rig-part name; rigged/stochastic_parrot_v2/ turns them",
            "       about their joints. The wing swaps between folded (on the body) and",
            "       spread (wing.folded / wing.open); the eye has open / angry / shut / dead.",
            "       The hidden Rig Joints layer marks every joint the skeleton is built on. -->",
        ],
        joints=svg.joints_layer(J),
    )


# ---- front view -------------------------------------------------------------------------
CX = 256.0
JF = dict(
    body=(256.0, 330.0),
    neck=(256.0, 262.0),
    head_top=(256.0, 172.0),
    jaw=(256.0, 236.0),
    near_shoulder=(286.0, 268.0),
    near_wingtip=(372.0, 150.0),
    far_shoulder=(226.0, 268.0),
    far_wingtip=(140.0, 150.0),
)


def mirror(points):
    return [(2 * CX - q[0],) + tuple(q[1:]) for q in points]


def front_parts():
    # The tail, seen end-on behind the body.
    tail = []
    for dx in (-8.0, 0.0, 8.0):
        tail += feather((CX + dx, 352), 90.0 + dx * 0.8, 70.0, 16.0, C["red"], C["blue"])
    part("tail", "Tail", "tail", "body", 10, tail)
    # Spread wings (for flight), behind the body: arms up and out.
    for side, sx in (("near", 1.0), ("far", -1.0)):
        sh, tp = JF[f"{side}_shoulder"], JF[f"{side}_wingtip"]
        fan = smooth([sh, (sh[0] + sx * 34, sh[1] - 70), tp + (True,), (tp[0] - sx * 4, tp[1] + 40),
                      (sh[0] + sx * 60, sh[1] - 4), (sh[0] + sx * 20, sh[1] + 24)])
        items = [path(smooth([sh, (sh[0] + sx * 34, sh[1] - 70), (sh[0] + sx * 56, sh[1] - 56),
                              (sh[0] + sx * 30, sh[1] - 6)]), C["red"]),
                 path(smooth([(sh[0] + sx * 30, sh[1] - 6), (sh[0] + sx * 56, sh[1] - 56), (sh[0] + sx * 66, sh[1] - 40),
                              (sh[0] + sx * 40, sh[1] + 6)]), C["yellow"])]
        for k in range(4):
            ang = (-50.0 + 12.0 * k) if sx > 0 else (230.0 - 12.0 * k)
            items += feather((sh[0] + sx * (50 + 6 * k), sh[1] - 50 + 14 * k), ang, 60.0, 16.0, C["blue"], C["blue_light"], sw=1.0)
        part(f"{side}-wing-open", f"Wing Open - {side}", f"{side}_wing_open", f"{side}_wing", 12,
             outlined(fan, C["blue"], items, f"clip-front-{side}-fan"), ' data-rig-opacity="wing.open"')
    # Feet gripping, two toes forward each.
    feet = []
    for sx in (-1.0, 1.0):
        ax, ay = CX + sx * 16, 404.0
        feet += outlined(svg.capsule((ax, 384), (ax, ay), 6.0, 5.0), C["leg"])
        for dx in (-6.0, 6.0):
            feet += outlined(svg.capsule((ax, ay), (ax + dx, ay + 12), 3.6, 2.8), C["leg"])
    part("feet", "Feet", "feet", "body", 20, feet)
    body = smooth([(CX - 36, 280), (CX - 20, 262), (CX + 20, 262), (CX + 36, 280), (CX + 44, 320), (CX + 36, 364),
                   (CX + 14, 384), (CX - 14, 384), (CX - 36, 364), (CX - 44, 320)])
    items = [path(smooth([(CX - 22, 288), (CX + 22, 288), (CX + 28, 340), (CX, 370), (CX - 28, 340)]), C["red_light"]),
             line([(CX - 18, 320), (CX, 328), (CX + 18, 320)], C["red_dark"], 1.2),
             line([(CX - 16, 344), (CX, 352), (CX + 16, 344)], C["red_dark"], 1.2)]
    part("body", "Body", "body", "body", 30, outlined(body, C["red"], items, "clip-front-body"))
    # Folded wings at the sides (perched).
    for side, sx in (("near", 1.0), ("far", -1.0)):
        pts = [(CX + sx * 30, 270), (CX + sx * 48, 290), (CX + sx * 50, 330), (CX + sx * 40, 376), (CX + sx * 28, 392),
               (CX + sx * 26, 350), (CX + sx * 30, 300)]
        items = [path(smooth([(CX + sx * 30, 270), (CX + sx * 48, 290), (CX + sx * 48, 312), (CX + sx * 30, 306)]), C["red_dark"]),
                 path(smooth([(CX + sx * 30, 306), (CX + sx * 48, 312), (CX + sx * 50, 330), (CX + sx * 28, 330)]), C["yellow"]),
                 path(smooth([(CX + sx * 28, 330), (CX + sx * 50, 330), (CX + sx * 40, 376), (CX + sx * 28, 392)]), C["blue"])]
        part(f"{side}-wing-folded", f"Wing Folded - {side}", f"{side}_wing_folded", "body", 40,
             outlined(smooth(pts), C["red"], items, f"clip-front-{side}-folded"),
             ' data-rig-opacity="wing.folded" data-rig-default="1"')
    # The head: round, a white face patch round each eye, the beak in the middle.
    head = smooth([(CX - 40, 222), (CX - 36, 192), (CX - 18, 174), (CX + 18, 174), (CX + 36, 192), (CX + 40, 222),
                   (CX + 30, 250), (CX, 262), (CX - 30, 250)])
    items = []
    for sx in (-1.0, 1.0):
        items.append(path(smooth([(CX + sx * 10, 196), (CX + sx * 30, 194), (CX + sx * 38, 214), (CX + sx * 30, 236),
                                  (CX + sx * 12, 234)]), C["face"]))
        for dy in (220, 228):
            items.append(line([(CX + sx * 18, dy), (CX + sx * 30, dy - 2)], C["face_line"], 1.0))
    items.append(path(smooth([(CX - 18, 178), (CX + 18, 178), (CX + 24, 188), (CX - 24, 188)]), C["red_light"]))
    hbody = outlined(head, C["red"], items, "clip-front-head")
    for sx in (-1.0, 1.0):
        ex = CX + sx * 22
        hbody += [ellipse(ex, 210, 6.0, 6.5, C["iris"], INK, 1.4), ellipse(ex, 210, 3.0, 3.6, C["pupil"]),
                  ellipse(ex - 1.5, 208, 1.2, 1.2, "#ffffff")]
    upper = smooth([(CX - 12, 214), (CX, 206), (CX + 12, 214), (CX + 9, 236), (CX, 252, True), (CX - 9, 236)])
    hbody += outlined(upper, C["beak"], [path(smooth([(CX - 4, 240), (CX + 4, 240), (CX, 252)]), C["beak_dark"])],
                      "clip-front-beak")
    part("head", "Head", "head", "head", 50, hbody)
    jaw = smooth([(CX - 8, 236), (CX + 8, 236), (CX + 5, 250), (CX - 5, 250)])
    part("jaw", "Lower Beak", "jaw", "jaw", 49, outlined(jaw, C["beak_dark"]))


def draw_front() -> str:
    svg.configure(dx=0.0, dy=0.0, ink=INK, ow=OW, colors=C)
    front_parts()
    return svg.document(
        size=(W, H),
        design="stochastic-parrot-v2-front",
        layer_id="parrot-front",
        label="Stochastic Parrot - Front",
        comment=[
            "  <!-- The Stochastic Parrot facing the viewer (the middle of a turnaround), on",
            "       the side view's canvas. The wings swap between folded and spread",
            "       (wing.folded / wing.open). The hidden Rig Joints layer marks its joints. -->",
        ],
        joints=svg.joints_layer(JF),
    )


# ---- three-quarter view ----------------------------------------------------------------
#: Turned 45 degrees from the side toward the viewer: the face and the belly
#: come round to the right, the near (left) wing stays on the viewer's side,
#: the far wing goes behind, the tail runs back and away to the left.
JQ = dict(
    body=(252.0, 330.0),
    neck=(272.0, 256.0),
    head_top=(276.0, 170.0),
    jaw=(304.0, 234.0),
    near_shoulder=(236.0, 272.0),
    near_wingtip=(112.0, 138.0),
    far_shoulder=(284.0, 266.0),
    far_wingtip=(372.0, 150.0),
)


def fan_wing(side, sh, tp, sx, k, dark, z, cid):
    """A spread wing seen from the front quarter: red shoulder, yellow band,
    blue flight feathers fanned out to the tip (``sx`` the side it opens to,
    ``k`` its foreshortening)."""
    red = C["red_dark"] if dark else C["red"]
    yellow = C["yellow_dark"] if dark else C["yellow"]
    blue = C["blue_dark"] if dark else C["blue"]
    blue_tip = C["blue"] if dark else C["blue_light"]

    def at(dx, dy):
        return (sh[0] + sx * dx * k, sh[1] + dy * k)

    fan = smooth([sh, at(34, -76), tp + (True,), (tp[0] - sx * 4 * k, tp[1] + 46 * k), at(64, -4), at(20, 24)])
    items = [path(smooth([sh, at(34, -76), at(60, -60), at(30, -6)]), red),
             path(smooth([at(30, -6), at(60, -60), at(72, -44), at(42, 6)]), yellow)]
    for j in range(5):
        ang = (-50.0 + 11.0 * j) if sx > 0 else (230.0 - 11.0 * j)
        items += feather(at(54 + 6 * j, -56 + 14 * j), ang, 66.0 * k, 17.0 * k, blue, blue_tip, sw=1.0)
    part(f"{side}-wing-open", f"Wing Open - {side}", f"{side}_wing_open", f"{side}_wing", z,
         outlined(fan, blue, items, cid), ' data-rig-opacity="wing.open"')


def three_quarter_parts():
    # The tail runs back and away, foreshortened, behind the body.
    tail = []
    for j, (ang, ln) in enumerate(((172.0, 112.0), (164.0, 124.0), (156.0, 104.0))):
        tail += feather((232 - 3 * j, 366 + 4 * j), ang, ln, 22.0, C["red"], C["blue"])
    part("tail", "Tail", "tail", "body", 8, tail)
    # The far wing spreads behind the head, foreshortened and in shadow.
    fan_wing("far", JQ["far_shoulder"], JQ["far_wingtip"], 1.0, 0.85, True, 12, "clip-q-far-fan")
    # Feet gripping, the far one a little behind.
    feet = []
    for ax, ay, top in ((270.0, 398.0, 378.0), (238.0, 402.0, 382.0)):
        feet += outlined(svg.capsule((ax, top), (ax, ay), 6.0, 5.0), C["leg"])
        for dx, dy in ((16.0, 8.0), (20.0, 12.0), (-9.0, 11.0)):
            feet += outlined(svg.capsule((ax, ay), (ax + dx, ay + dy), 3.8, 2.8), C["leg"])
    part("feet", "Feet", "feet", "body", 20, feet)
    body = smooth([(228, 272), (248, 252), (270, 244), (290, 262), (300, 292), (304, 330), (294, 366), (270, 388), (240, 390),
                   (216, 372), (206, 334), (210, 296)])
    items = [path(smooth([(262, 282), (290, 300), (296, 340), (278, 374), (252, 378), (246, 340), (250, 300)]),
                  C["red_light"]),
             line([(256, 322), (272, 328), (290, 322)], C["red_dark"], 1.2),
             line([(254, 346), (270, 352), (286, 346)], C["red_dark"], 1.2),
             line([(258, 368), (272, 372)], C["red_dark"], 1.2)]
    part("body", "Body", "body", "body", 30, outlined(body, C["red"], items, "clip-q-body"))
    # The near wing folded on the body's near side, its flight feathers
    # running down over the tail.
    folded = smooth([(232, 268), (250, 286), (252, 320), (240, 356), (214, 394), (196, 406), (202, 372), (206, 330),
                     (214, 294)])
    items = [path(smooth([(232, 268), (250, 286), (250, 306), (230, 306), (216, 292)]), C["red_dark"]),
             path(smooth([(250, 306), (252, 322), (232, 330), (210, 322), (214, 300), (230, 306)]), C["yellow"]),
             path(smooth([(252, 322), (246, 340), (226, 346), (208, 340), (210, 322), (232, 330)]), C["green"]),
             path(smooth([(246, 340), (240, 356), (214, 394), (196, 406), (204, 370), (208, 340), (226, 346)]), C["blue"]),
             line([(236, 350), (214, 384), (202, 400)], C["blue_dark"], 1.3)]
    part("near-wing-folded", "Wing Folded - near", "near_wing_folded", "body", 40,
         outlined(folded, C["red"], items, "clip-q-folded"), ' data-rig-opacity="wing.folded" data-rig-default="1"')
    fan_wing("near", JQ["near_shoulder"], JQ["near_wingtip"], -1.0, 1.1, False, 44, "clip-q-near-fan")
    # The head, its face and beak turned toward the viewer's right.
    head = smooth([(246, 224), (248, 194), (266, 176), (292, 172), (314, 184), (322, 206), (316, 232), (300, 248),
                   (276, 254), (256, 244)])
    items = [path(smooth([(262, 186), (288, 176), (306, 182), (288, 190), (266, 196)]), C["red_light"]),
             path(smooth([(250, 226), (260, 244), (276, 252), (256, 250)]), C["red_dark"]),
             path(smooth([(276, 190), (300, 184), (316, 196), (318, 222), (304, 236), (284, 232), (276, 212)]), C["face"]),
             line([(282, 218), (292, 222), (302, 220)], C["face_line"], 1.0),
             line([(284, 226), (294, 230), (304, 228)], C["face_line"], 1.0)]
    hbody = outlined(head, C["red"], items, "clip-q-head")
    ex, ey = 292.0, 205.0
    hbody += [ellipse(ex, ey, 6.5, 6.5, C["iris"], INK, 1.4), ellipse(ex + 1, ey, 3.2, 3.6, C["pupil"]),
              ellipse(ex - 1.5, ey - 2, 1.4, 1.4, "#ffffff")]
    upper = smooth([(300, 192), (320, 196), (334, 212), (340, 234), (336, 252, True), (328, 240), (318, 232), (306, 230)])
    hbody += outlined(upper, C["beak"], [
        path(smooth([(336, 230), (340, 236), (336, 252), (328, 242)]), C["beak_dark"]),
        path(smooth([(306, 214), (322, 218), (328, 230), (312, 228)]), C["beak_shadow"]),
    ], "clip-q-beak")
    part("head", "Head", "head", "head", 50, hbody)
    jaw = smooth([(304, 232), (318, 234), (328, 244), (324, 252), (312, 250), (302, 242)])
    part("jaw", "Lower Beak", "jaw", "jaw", 49, outlined(jaw, C["beak_dark"], [
        line([(308, 238), (320, 244)], "#4a3f42", 1.4)], "clip-q-jaw"))


def draw_three_quarter() -> str:
    svg.configure(dx=0.0, dy=0.0, ink=INK, ow=OW, colors=C)
    three_quarter_parts()
    return svg.document(
        size=(W, H),
        design="stochastic-parrot-v2-three-quarter",
        layer_id="parrot-three-quarter",
        label="Stochastic Parrot - Three Quarter Right",
        comment=[
            "  <!-- The Stochastic Parrot turned three-quarters toward the viewer, facing",
            "       right (a turnaround's step between the side and the front; mirrored for",
            "       the step back out). The wings swap between folded and spread",
            "       (wing.folded / wing.open). The hidden Rig Joints layer marks its joints. -->",
        ],
        joints=svg.joints_layer(JQ),
    )


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    Path(sys.argv[1]).write_text(draw_side())
    Path(sys.argv[2]).write_text(draw_front())
    Path(sys.argv[3]).write_text(draw_three_quarter())
