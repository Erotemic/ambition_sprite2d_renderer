#!/usr/bin/env python3
"""A CANDIDATE redraw of the giant gnu (GNU-ton's mount). Not the art of the game.

No SVG under ``data/characters/`` comes from this yet, and no rig: the giant
the game draws is ``targets/characters/gnu_ton_boss``. This script is the
design Jon chose in stills (2026-10-11), kept so the real target can start
from it.

    uv run python scripts/svg_art/giant_gnu_art.py OUT.svg [STANCE] [EXPRESSION] [--curl] [--head]

What the design is:

* A giant that is like a gnu and is not one, almost a centaur: a beast on
  four long legs in a coat of long locks, a chest that stands up at its front
  to two broad shoulders, and two arms, each to a great fist.
* Its back is a slope, not a floor: low at the rump and high at the left
  shoulder, one line from one to the other. The mane comes down from the
  shoulders over the front of the beast.
* Two stances (``STANCES``): ``sloped`` on all fours, and ``reared`` up on its
  hind legs, where the slope is steeper and the shoulders are higher.
* The horns of a gnu: out to each side, down a little, then up to a point.
  (``--curl`` draws the curled horns of the first design, which Jon may go
  back to.)
* A face whose parts make its expression (``EXPRESSIONS``). It has no brows
  and shows no teeth. Two of them are its faces at rest: ``ordered`` when it
  does what the scholar says (a small lid on each eye, tilted in a little:
  focused), and ``free`` when it is on its own (no lids, the eyes drifting:
  more vacant). The others are for when the giant reacts to something.
* Where an actor can stand is shown, not built: moss grows there (along the
  slope of the back, on the level part of each horn), and each shoulder has
  an epaulet.
* It has no bird. A bird that rides it is to be an actor of its own.

It is drawn at twice the published frame of today (768x576) with the floor
at y=978, and it is taller than that frame: ``TOP`` is the room above it.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import svgkit as svg
from birdkit import ellipse, line, outlined, part, path, smooth, tube

#: Room above the frame of today: the giant is taller than it, more so reared.
TOP = 300.0
W, H = 1800, 1152 + int(TOP)
INK = "#17100d"
OW = 2.4

FLOOR = 978.0
#: Each shoulder before a stance lifts it: from x, to x, and its top.
SHOULDER_L = (792.0, 962.0, 444.0)
SHOULDER_R = (1122.0, 1292.0, 444.0)
HEAD = (1042.0, 262.0)
#: The scale of the head about ``HEAD``.
K = 0.9
#: Where each eye is from ``HEAD``, and its radius. The far one (on the right
#: of the picture) is a little smaller: the head is turned.
EYES = (((-36, -34), 34.0), ((42, -37), 31.0))

#: A stance. lift: where the chest, the head and the arms are from their
#: drawn place. rump: the low end of the slope. belly: the line of the
#: beast's underside, rear to front. hind / fore: hip, knee and fetlock of
#: the near leg(s). fore_floor: None when the fore hooves are on the floor.
#: tail: its root, and how far it swings out. arms: shoulder, elbow and wrist
#: of the left and of the right arm (before ``lift``).
C = dict(
    fur="#5f4734",
    light="#80624a",
    dark="#433124",
    deep="#2c2018",
    far="#3a2a20",
    far_dark="#281c15",
    mane="#261b16",
    mane_light="#4d3a2d",
    face="#6a503c",
    face_light="#8a6c52",
    blaze="#33251d",
    nose="#2a1f1b",
    nose_light="#55433b",
    horn="#e4d2a4",
    horn_light="#f3e7c4",
    horn_shade="#b89f6c",
    horn_deep="#8c7648",
    hoof="#241c1c",
    hoof_light="#4f4242",
    iris="#f2b63a",
    iris_dark="#b47a1c",
    pupil="#120d0f",
    moss="#77a04e",
    moss_dark="#4a7232",
    bronze="#c9953f",
    bronze_dark="#7f5a1f",
    gold="#e2b64a",
    gold_light="#f6dc8a",
    gold_dark="#a67a20",
    cloth="#7a2e2e",
    cloth_dark="#4f1c1c",
    iris_hot="#f58a1f",
    flower="#f6efe0",
    white="#f4ecd8",
)

STANCES = {
    "sloped": dict(
        lift=(-8.0, -180.0), rump=(352.0, 585.0), belly=((396.0, 772.0), (1096.0, 784.0)), expr="ordered",
        hind=((452, 740), (418, 858), (446, 934)), fore=(((1098, 720), (1106, 846), (1100, 934)), ((960, 716), (968, 846), (962, 934))),
        fore_floor=None, tail=((346, 612), 14.0),
        arms=(((826, 506), (792, 660), (822, 800)), ((1258, 506), (1304, 660), (1282, 800)))),
    "reared": dict(
        lift=(-10.0, -250.0), rump=(334.0, 655.0), belly=((396.0, 812.0), (1120.0, 606.0)), expr="angry",
        hind=((452, 792), (412, 884), (446, 934)), fore=(((1092, 592), (1180, 668), (1156, 766)), ((984, 588), (1064, 668), (1040, 760))),
        fore_floor=46.0, tail=((330, 690), 34.0),
        arms=(((826, 506), (700, 452), (668, 300)), ((1258, 506), (1404, 470), (1452, 324)))),
}


def _face(lids, slant=0.0, low=0.0, look=((0.0, 0.0), (0.0, 0.0)), pupil=(0.28, 0.28), ears=(0, 0), mouth="none", tilt=0.0,
          hot=False, flare=1.0):
    return dict(lids=lids, slant=slant, low=low, look=look, pupil=pupil, ears=ears, mouth=mouth, tilt=tilt, hot=hot,
                flare=flare)


#: An expression: what each part of the face does.
#: lids: how much of each eye its upper lid covers (left, right); slant: how
#: much the lids tilt in toward the nose; low: how much the lower lid covers.
#: look: where each pupil is, as a part of the eye's radius. pupil: its size.
#: ears: how far each ear is turned down (degrees). hot: the iris of anger.
EXPRESSIONS = {
    # AT REST, UNDER ORDERS: focused. Both eyes on one thing.
    "ordered": _face((0.15, 0.15), slant=0.12, look=((0.14, 0.10), (0.14, 0.10)), pupil=(0.25, 0.25)),
    # AT REST, ON ITS OWN: more vacant. No lids, the eyes drifting low.
    "free": _face((0.0, 0.0), look=((0.22, 0.18), (0.22, 0.18)), pupil=(0.30, 0.30)),
    # The rest are for a giant that reacts. It does not smile at rest.
    "smile": _face((0.06, 0.06), look=((0.18, 0.14), (0.18, 0.14)), pupil=(0.30, 0.30), mouth="smile"),
    "serious": _face((0.22, 0.22), look=((0.10, 0.08), (0.10, 0.08)), pupil=(0.24, 0.24), mouth="firm"),
    "angry": _face((0.26, 0.26), slant=0.34, low=0.12, look=((0.14, 0.14), (0.14, 0.14)), pupil=(0.19, 0.19),
                   ears=(-30, -30), mouth="firm", tilt=4.0, hot=True, flare=1.3),
    "dazed": _face((0.0, 0.10), look=((-0.25, -0.10), (0.30, 0.20)), pupil=(0.34, 0.20), ears=(10, 30), tilt=-5.0),
    "sleepy": _face((0.50, 0.50), look=((0.05, 0.30), (0.05, 0.30)), pupil=(0.28, 0.28), ears=(16, 16)),
}
def grp(items, transform):
    return [f'<g transform="{transform}">'] + list(items) + ["</g>"]


def locks(x_from, x_to, y_valley, y_tip, n, sway=0.0):
    """The lower edge of a coat: ``n`` hanging locks from x_from to x_to."""
    pts = []
    step = (x_to - x_from) / n
    for k in range(n):
        x = x_from + step * k
        drop = y_tip + 14.0 * math.sin(k * 1.9)
        pts += [(x + step * 0.1, y_valley, True), (x + step * (0.55 + sway), drop, True)]
    pts.append((x_to, y_valley, True))
    return pts


def locks_line(p_from, p_to, n, drop):
    """Hanging locks along the line from one point to another: each hangs straight down."""
    pts = []
    for k in range(n):
        t0, t1 = k / n, (k + 0.55) / n
        x0, y0 = p_from[0] + (p_to[0] - p_from[0]) * t0, p_from[1] + (p_to[1] - p_from[1]) * t0
        x1, y1 = p_from[0] + (p_to[0] - p_from[0]) * t1, p_from[1] + (p_to[1] - p_from[1]) * t1
        pts += [(x0, y0, True), (x1, y1 + drop + 12.0 * math.sin(k * 1.9), True)]
    pts.append((p_to[0], p_to[1], True))
    return pts


def strands(x_from, x_to, y0, y1, n, colour, lean=0.0):
    out = []
    for k in range(n):
        x = x_from + (x_to - x_from) * (k + 0.5) / n
        j = 10.0 * math.sin(k * 2.7)
        out.append(line([(x, y0 + j), (x + lean * 0.5 + 4, (y0 + y1) / 2), (x + lean, y1 + j)], colour, 2.6))
    return out


def catmull(pts, u):
    """The point ``u`` (0..len-1) of the spline ``smooth`` draws through ``pts``, and its direction."""
    n = len(pts)
    i = min(n - 2, max(0, int(u)))
    t = u - i
    p0, p1, p2, p3 = pts[max(0, i - 1)], pts[i], pts[i + 1], pts[min(n - 1, i + 2)]
    out, d = [], []
    for a, b, c, e in zip(p0, p1, p2, p3):
        out.append(0.5 * (2 * b + (c - a) * t + (2 * a - 5 * b + 4 * c - e) * t * t + (3 * b - a - 3 * c + e) * t ** 3))
        d.append(0.5 * ((c - a) + 2 * (2 * a - 5 * b + 4 * c - e) * t + 3 * (3 * b - a - 3 * c + e) * t * t))
    return out, d


def leg2(name, hip, mid, end, far, z, floor=None):
    """A long leg in two parts, with a knee, a cuff of long hair and a great hoof."""
    skin, shade, hair = (C["far"], C["far_dark"], C["far_dark"]) if far else (C["fur"], C["dark"], C["mane"])
    ex, ey = end
    floor = FLOOR if floor is None else ey + floor
    body = outlined(svg.capsule(hip, mid, 54.0, 31.0), skin,
                    [path(svg.capsule((hip[0] - 24, hip[1]), (mid[0] - 14, mid[1]), 22.0, 12.0), shade)], f"clip-{name}-u")
    body += outlined(svg.capsule(mid, end, 28.0, 25.0), skin,
                     [path(svg.capsule((mid[0] - 13, mid[1]), (ex - 12, ey), 10.0, 9.0), shade)], f"clip-{name}-l")
    body += [ellipse(mid[0], mid[1], 33, 31, skin, INK, 2 * OW), ellipse(mid[0] - 7, mid[1] - 8, 13, 10, C["far"] if far else C["light"])]
    hoof = smooth([(ex - 40, floor - 40, True), (ex + 46, floor - 40, True), (ex + 60, floor, True), (ex - 50, floor, True)])
    body += outlined(hoof, C["hoof"], [path(svg.poly([(ex - 50, floor - 38), (ex + 58, floor - 38), (ex + 58, floor - 27),
                                                      (ex - 50, floor - 27)]), C["far_dark"] if far else C["hoof_light"]),
                                       line([(ex + 10, floor - 38), (ex + 14, floor)], INK, 2.6)], f"clip-{name}-hoof")
    cuff = smooth([(ex + 44, floor - 84, True), (ex - 40, floor - 84, True)] + locks(ex - 52, ex + 58, floor - 40, floor - 20, 5))
    body += outlined(cuff, hair, strands(ex - 36, ex + 42, floor - 76, floor - 40, 4, C["far"] if far else C["mane_light"]),
                     f"clip-{name}-cuff")
    part(name, name, name.replace("-", "_"), name.replace("-", "_"), z, body)


def tail():
    stem = smooth(tube([(352, 716), (318, 776), (306, 850)], 18.0, 12.0))
    part("tail", "Tail", "tail", "tail", 20, outlined(stem, C["fur"], [], None))
    brush = smooth([(288, 836, True), (326, 836, True), (346, 900), (338, 956), (320, 976, True), (312, 946),
                    (298, 978, True), (288, 940), (270, 966, True), (274, 896)])
    part("tail-brush", "Tail brush", "tail_brush", "tail_tip", 21,
         outlined(brush, C["mane"], strands(286, 330, 850, 950, 3, C["mane_light"]), "clip-brush"))


def beast(st):
    """The body of the beast: one shape. Its top is the slope from the rump to
    the left shoulder, and the mane comes down over the front of it."""
    lx, ly = st["lift"]
    rx, ry = st["rump"]
    sx, sy = SHOULDER_L[0] + lx - 8, SHOULDER_L[2] + ly + 4
    b0, b1 = st["belly"]
    n = 20
    top = [(rx + (sx - rx) * k / n, ry + (sy - ry) * (k / n) ** 1.35) for k in range(n + 1)]
    bottom = locks_line(b1, b0, 12, 40.0)
    sil = smooth(top + [(sx + 70, sy + 30), (sx + 130, sy + 260), (b1[0] + 14, b1[1] - 120)] + bottom +
                 [(rx - 14, b0[1] - 26), (rx - 30, ry + 96), (rx - 14, ry + 26)])
    k0 = 7
    # The edge of the mane: from the slope down to the chest, in locks.
    a, b = (b1[0] - 150.0, b1[1] + 10.0), top[k0]
    edge = []
    teeth = 7
    d = math.hypot(b[0] - a[0], b[1] - a[1])
    nx, ny = -(b[1] - a[1]) / d, (b[0] - a[0]) / d
    if nx > 0:
        nx, ny = -nx, -ny
    for i in range(teeth):
        t0, t1 = i / teeth, (i + 0.5) / teeth
        edge += [(a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0, True),
                 (a[0] + (b[0] - a[0]) * t1 + nx * 44 - 8, a[1] + (b[1] - a[1]) * t1 + ny * 44 + 30, True)]
    mane = smooth([(x, y - 30) for x, y in top[k0:]] + [(sx + 400, sy), (b1[0] + 200, b1[1] + 200), (a[0], a[1] + 200, True)] + edge)
    items = [
        # The pale of the back near the rump, and the dark of the belly.
        path(smooth([(x, y - 20) for x, y in top[:k0 + 3]] + [(x + 20, y + 60) for x, y in top[:k0 + 3]][::-1]), C["light"]),
        path(svg.poly([(b0[0] - 120, b0[1] - 40), (b1[0] + 80, b1[1] - 40), (b1[0] + 80, b1[1] + 120), (b0[0] - 120, b0[1] + 120)]),
             C["dark"]),
    ]
    # Brindle on the flank.
    for i, k in enumerate((2, 4, 6)):
        x, y = top[k]
        h = 110 + 20 * math.sin(i * 1.3)
        items.append(path(smooth([(x - 7, y + 34, True), (x + 9, y + 38), (x + 4, y + 34 + h * 0.7), (x - 4, y + 34 + h, True),
                                  (x - 11, y + 34 + h * 0.5)]), C["dark"]))
    items.append(path(mane, C["mane"]))
    for k in range(k0 + 2, n, 2):
        x, y = top[k]
        items.append(line([(x + 4, y + 30), (x + 18, y + 110), (x + 22, y + 190)], C["mane_light"], 2.6))
    for k in range(1, 12, 2):
        t = k / 12
        x, y = b0[0] + (b1[0] - b0[0]) * t, b0[1] + (b1[1] - b0[1]) * t
        items.append(line([(x, y - 70), (x - 4, y - 20), (x - 2, y + 20)], C["deep"], 2.6))
    part("beast", "Beast", "beast", "torso", 30, outlined(sil, C["fur"], items, "clip-beast"))

    # Moss along the top of the slope: where the moss is, you can stand.
    ridge = top[1:]
    under = []
    for k, (x, y) in enumerate(ridge):
        drip = 15.0 + (10.0 if k % 3 == 1 else 0.0) + 4.0 * math.sin(k * 1.9)
        under.append((x + 3, y + drip))
    moss = smooth([(x, y - 2) for x, y in ridge] + under[::-1])
    light = smooth([(x, y - 2) for x, y in ridge] + [(x + 1, y + 6) for x, y in ridge[::-1]])
    body = outlined(moss, C["moss"], [path(light, "#9cc46a")], "clip-beast-moss", width=3.0)
    for k in (2, 5):
        x, y = ridge[k]
        for dx, h in ((-7, 13), (0, 18), (7, 12)):
            body.append(line([(x + dx, y), (x + dx * 1.6 - 4, y - h)], C["moss_dark"], 3.0))
    part("beast-moss", "Moss on the slope", "beast_moss", "torso", 32, body)


def chest():
    x0, x1, top = SHOULDER_L[0], SHOULDER_R[1], SHOULDER_L[2]
    bottom = locks(858, 1236, 800, 862, 6)[::-1]
    sil = smooth([(848, 700), (838, 610), (812, 540), (x0 - 4, 492), (x0 + 6, top + 8, True), (x1 - 6, top + 8, True),
                  (x1 + 4, 492), (1276, 560), (1246, 650), (1236, 740)] + bottom)
    items = [
        ellipse(x0 + 54, top + 56, 62, 44, C["mane_light"]),
        ellipse(x1 - 54, top + 56, 62, 44, C["mane_light"]),
        path(smooth([(960, 500), (1124, 500), (1150, 600), (1120, 720), (1042, 770), (964, 720), (934, 600)]), C["fur"]),
        path(smooth([(960, 500), (1124, 500), (1140, 560), (1042, 540), (944, 560)]), C["light"]),
        line([(1042, 548), (1042, 740)], C["dark"], 3.0),
        line([(972, 640), (1010, 656), (1042, 650), (1074, 656), (1112, 640)], C["dark"], 3.0),
    ]
    items += strands(850, 940, 560, 830, 3, C["mane_light"], lean=10.0)
    items += strands(1150, 1240, 560, 830, 3, C["mane_light"], lean=-10.0)
    part("chest", "Chest", "chest", "chest", 34, outlined(sil, C["mane"], items, "clip-chest"))


def epaulet(name, deck, outer):
    """A floor of a shoulder: an epaulet. Its board is flat, and its top is the
    line the player's soles are on."""
    x0, x1, top = deck
    s = -1.0 if outer < (x0 + x1) / 2 else 1.0
    inner = x1 if s < 0 else x0
    # The fringe that hangs from its outer end.
    body = []
    n = 9
    for k in range(n):
        x = outer - s * (10 + k * 15.0)
        drop = 62.0 - 2.2 * k + 5.0 * math.sin(k * 1.7)
        body.append(path(svg.capsule((x, top + 22), (x - s * 3, top + 22 + drop), 7.5, 6.5), C["gold"], INK, 2.0))
        body.append(line([(x - 2, top + 28), (x - s * 3 - 2, top + 16 + drop)], C["gold_light"], 2.0))
    board = smooth([(inner, top, True), (outer - s * 26, top, True), (outer + s * 6, top + 6), (outer + s * 10, top + 22),
                    (outer - s * 4, top + 34, True), (inner, top + 30, True)])
    body += outlined(board, C["gold"], [
        path(svg.poly([(x0 - 30, top), (x1 + 30, top), (x1 + 30, top + 8), (x0 - 30, top + 8)]), C["gold_light"]),
        path(svg.poly([(x0 - 30, top + 22), (x1 + 30, top + 22), (x1 + 30, top + 40), (x0 - 30, top + 40)]), C["gold_dark"]),
        path(svg.poly([(inner - s * 4, top + 9), (outer - s * 44, top + 9), (outer - s * 44, top + 21), (inner - s * 4, top + 21)]),
             C["cloth"]),
    ], f"clip-{name}")
    body += [ellipse(inner + s * 20, top + 15, 7, 7, C["gold_light"], INK, 1.8)]
    part(name, name, name.replace("-", "_"), "chest", 46, body)


def fist(name):
    """A fist of the giant, about its own middle: a mitt of fur, two knuckles of
    hoof, a cuff of bronze. Its knuckles are to the left and its cuff to the right."""
    cuff = smooth([(46, -62, True), (88, -56, True), (92, 56, True), (46, 62, True)])
    body = outlined(cuff, C["bronze"], [path(svg.poly([(70, -70), (100, -70), (100, 70), (70, 70)]), C["bronze_dark"]),
                                        line([(58, -40), (58, 40)], C["bronze_dark"], 3.0)], f"clip-{name}-cuff")
    mitt = smooth([(-56, -52), (0, -66), (52, -56), (64, 0), (54, 54), (0, 66), (-52, 54), (-70, 0)])
    body += outlined(mitt, C["fur"], [path(smooth([(-44, -50), (0, -62), (46, -50), (30, -30), (-32, -32)]), C["light"]),
                                      path(smooth([(-54, 32), (0, 48), (54, 34), (44, 70), (-44, 70)]), C["dark"])],
                     f"clip-{name}")
    for i, (y0, y1) in enumerate(((-52, -3), (3, 52))):
        k = smooth([(-84, y0 + 6), (-44, y0), (-28, (y0 + y1) / 2), (-44, y1), (-84, y1 - 6), (-94, (y0 + y1) / 2)])
        body += outlined(k, C["hoof"], [ellipse(-66, y0 + 15, 16, 6, C["hoof_light"])], f"clip-{name}-k{i}")
    body += outlined(smooth([(-20, -80), (18, -84), (38, -64), (22, -46), (-18, -50)]), C["fur"], [], None)
    return body


def arm(name, shoulder, elbow, wrist):
    """An arm from a shoulder to its fist: the fist is the fist of the fight."""
    far = shoulder[0] < 1000
    upper = outlined(svg.capsule(shoulder, elbow, 46.0, 36.0), C["fur"],
                     [path(svg.capsule((shoulder[0] + 16, shoulder[1]), (elbow[0] + 14, elbow[1]), 20.0, 14.0), C["dark"])],
                     f"clip-{name}-u")
    fore = outlined(svg.capsule(elbow, wrist, 38.0, 44.0), C["fur"],
                    [path(svg.capsule((elbow[0] + 14, elbow[1]), (wrist[0] + 16, wrist[1]), 14.0, 20.0), C["dark"]),
                     path(svg.capsule((elbow[0] - 14, elbow[1] + 10), (wrist[0] - 16, wrist[1] - 20), 7.0, 9.0), C["light"])],
                    f"clip-{name}-f")
    # Long hair at the elbow.
    ex, ey = elbow
    tuft = smooth([(ex - 30, ey - 14, True), (ex + 30, ey - 14, True), (ex + 26, ey + 22), (ex + 10, ey + 50, True),
                   (ex, ey + 26), (ex - 12, ey + 56, True), (ex - 26, ey + 20)])
    d = math.hypot(wrist[0] - elbow[0], wrist[1] - elbow[1])
    ux, uy = (wrist[0] - elbow[0]) / d, (wrist[1] - elbow[1]) / d
    fx, fy = wrist[0] + ux * 56, wrist[1] + uy * 56
    turn = math.degrees(math.atan2(-uy, -ux))
    # The fist of the candidate, turned so its cuff is on the arm.
    fist_body = fist(f"{name}-fist")
    flip = " scale(1 -1)" if far else ""
    body = upper + fore + outlined(tuft, C["mane"], [], None)
    body += [f'<g transform="translate({fx:.1f} {fy:.1f}) rotate({turn:.1f}){flip}">'] + fist_body + ["</g>"]
    part(name, name, name.replace("-", "_"), name.replace("-", "_"), 40, body)


def horn(cid, pts, mirror):
    """A great ridged horn along ``pts``."""
    sil = smooth(tube(pts, 38.0, 4.0))
    items = [path(smooth(tube([(p[0], p[1] + 16) for p in pts], 20.0, 2.0)), C["horn_shade"]),
             path(smooth(tube([(p[0], p[1] - 16) for p in pts[:4]], 9.0, 3.0)), C["horn_light"])]
    # The ridges across it, close at the root and wide toward the tip.
    n = len(pts) - 1
    for k in range(1, 12):
        u = (k / 12.0) ** 0.85 * 0.86
        i = min(n - 1, int(u * n))
        t = u * n - i
        x = pts[i][0] + (pts[i + 1][0] - pts[i][0]) * t
        y = pts[i][1] + (pts[i + 1][1] - pts[i][1]) * t
        dx, dy = pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]
        d = math.hypot(dx, dy)
        nx, ny = -dy / d, dx / d
        r = 40.0 * (1.0 - u) + 6.0
        bow = 7.0 if mirror else -7.0
        items.append(line([(x + nx * r, y + ny * r), (x + dx / d * bow, y + dy / d * bow), (x - nx * r, y - ny * r)],
                          C["horn_deep"], 2.8))
    return outlined(sil, C["horn"], items, cid)


def gnu_horn_moss(cid, pts, s):
    top, under = [], []
    steps = 12
    for k in range(steps + 1):
        u = 0.55 + (2.5 - 0.55) * k / steps
        (x, y), (dx, dy) = catmull(pts, u)
        d = math.hypot(dx, dy)
        nx, ny = s * dy / d, -s * dx / d
        r = 38.0 + (4.0 - 38.0) * u / (len(pts) - 1)
        top.append((x + nx * (r + 3), y + ny * (r + 3)))
        drip = 10.0 + (9.0 if k % 3 == 1 else 0.0) + 4.0 * math.sin(k * 1.9)
        under.append((x + nx * (r - drip), y + ny * (r - drip)))
    return outlined(smooth(top + under[::-1]), C["moss"],
                    [path(smooth(top + [(x, y + 7) for x, y in top[::-1]]), "#9cc46a")], cid, width=3.0)


def gnu_horns(expr):
    """The horns of a gnu: out to each side, down a little, and then up to a point."""
    e = EXPRESSIONS[expr]
    cx, cy = HEAD

    def P(dx, dy, corner=False):
        p = (cx + dx * K, cy + dy * K)
        return p + (True,) if corner else p

    back = []
    for s, cid in ((-1, "clip-horn-l"), (1, "clip-horn-r")):
        pts = [P(s * 40, -104), P(s * 124, -90), P(s * 206, -66), P(s * 268, -92), P(s * 292, -170), P(s * 270, -250),
               P(s * 244, -296)]
        back += horn(cid, pts, s < 0)
        back += gnu_horn_moss(cid + "-moss", [tuple(p[:2]) for p in pts], s)
    for s, cid, turn in ((-1, "clip-ear-l", e["ears"][0]), (1, "clip-ear-r", e["ears"][1])):
        ear = smooth([P(s * 86, -40, True), P(s * 132, -62), P(s * 168, -44), P(s * 176, -22, True), P(s * 130, -14),
                      P(s * 92, -18)])
        bx, by = P(s * 86, -30)
        # Under these horns the ears have room: they hang a little lower.
        back += grp(outlined(ear, C["face"], [path(smooth([P(s * 104, -36), P(s * 136, -46), P(s * 160, -32), P(s * 130, -24)]),
                                                     C["blaze"])], cid), f"rotate({s * (turn + 26)} {bx} {by})")
    return grp(back, f"rotate({e['tilt']} {cx} {cy + 120})")


def horn_moss(cid, pts, s):
    """Moss on the top of a horn: a place an actor can stand."""
    top, under = [], []
    steps = 14
    for k in range(steps + 1):
        u = 0.95 + (2.55 - 0.95) * k / steps
        (x, y), (dx, dy) = catmull(pts, u)
        d = math.hypot(dx, dy)
        nx, ny = s * dy / d, -s * dx / d
        r = 38.0 + (4.0 - 38.0) * u / (len(pts) - 1)
        top.append((x + nx * (r + 3), y + ny * (r + 3)))
        drip = 10.0 + (9.0 if k % 3 == 1 else 0.0) + 4.0 * math.sin(k * 1.9)
        under.append((x + nx * (r - drip), y + ny * (r - drip)))
    sil = smooth(top + under[::-1])
    light = smooth(top + [(x, y + 7) for x, y in top[::-1]])
    return outlined(sil, C["moss"], [path(light, "#9cc46a")], cid, width=3.0)


def curl_horns(expr):
    """The horns of the first design, greater: up and out from the brow, round,
    and in again, each one over a shoulder. Not the horns of the design now."""
    e = EXPRESSIONS[expr]
    cx, cy = HEAD

    def P(dx, dy, corner=False):
        p = (cx + dx * K, cy + dy * K)
        return p + (True,) if corner else p

    back = []
    for s, cid in ((-1, "clip-horn-l"), (1, "clip-horn-r")):
        pts = [P(s * 46, -108), P(s * 132, -176), P(s * 232, -156), P(s * 284, -62), P(s * 262, 26), P(s * 204, 62),
               P(s * 158, 40)]
        back += horn(cid, pts, s < 0)
        back += horn_moss(cid + "-moss", [tuple(p[:2]) for p in pts], s)
    # The ears turn about their roots: level, back, or one that has dropped.
    for s, cid, turn in ((-1, "clip-ear-l", e["ears"][0]), (1, "clip-ear-r", e["ears"][1])):
        ear = smooth([P(s * 86, -40, True), P(s * 132, -62), P(s * 168, -44), P(s * 176, -22, True), P(s * 130, -14),
                      P(s * 92, -18)])
        bx, by = P(s * 86, -30)
        back += grp(outlined(ear, C["face"], [path(smooth([P(s * 104, -36), P(s * 136, -46), P(s * 160, -32), P(s * 130, -24)]),
                                                   C["blaze"])], cid), f"rotate({s * turn} {bx} {by})")
    return grp(back, f"rotate({e['tilt']} {cx} {cy + 120})")


def head(expr, horns="gnu"):
    e = EXPRESSIONS[expr]
    cx, cy = HEAD

    def P(dx, dy, corner=False):
        p = (cx + dx * K, cy + dy * K)
        return p + (True,) if corner else p

    tilt = f"rotate({e['tilt']} {cx} {cy + 120})"
    part("horns", "Horns", "horns", "head", 56, gnu_horns(expr) if horns == "gnu" else curl_horns(expr))

    neck = smooth([P(-78, 30), P(96, 30), P(118, 220), P(-96, 220)])
    part("neck", "Neck", "neck", "neck", 40, outlined(neck, C["mane"], [], None))

    beard = smooth([P(-20, 120, True), P(110, 150, True), P(118, 220), P(100, 290), P(80, 334, True), P(62, 290),
                    P(42, 360, True), P(24, 296), P(0, 330, True), P(-22, 240)])
    body = outlined(beard, C["mane"], strands(cx - 4, cx + 96, cy + 160, cy + 290, 4, C["mane_light"], lean=-6.0),
                    "clip-beard")
    body += outlined(smooth([P(30, 352, True), P(54, 352, True), P(56, 372), P(42, 410, True), P(28, 372)]), C["mane"], [],
                     None)
    body += [path(svg.poly([P(24, 344), P(60, 344), P(60, 358), P(24, 358)]), C["bronze"], INK, 2.2),
             line([P(28, 351), P(56, 351)], C["bronze_dark"], 2.0)]
    part("beard", "Beard", "beard", "head", 58, grp(body, tilt))

    face = smooth([P(-84, -98), P(0, -114), P(86, -100), P(108, -40), P(104, 14), P(130, 72), P(152, 130), P(140, 178),
                   P(98, 198), P(46, 190), P(6, 154), P(-34, 94), P(-80, 40), P(-102, -30)])
    nx, ny = P(108, 160)
    fl = e["flare"]
    items = [
        path(smooth([P(-84, -98), P(0, -114), P(86, -100), P(100, -60), P(40, -72), P(-40, -70), P(-98, -52)]),
             C["face_light"]),
        path(smooth([P(-12, -66), P(30, -66), P(52, 20), P(96, 100), P(60, 120), P(6, 40)]), C["blaze"]),
        path(smooth([P(-102, -20), P(-70, 30), P(-34, 94), P(6, 154), P(-40, 150), P(-110, 60)]), C["dark"]),
        ellipse(nx, ny, 50 * K, 36 * K, C["nose"], rot=22.0),
        ellipse(nx - 10 * K, ny - 14 * K, 30 * K, 12 * K, C["nose_light"], rot=22.0),
        ellipse(nx - 24 * K, ny + 4 * K, 9 * K * fl, 13 * K * fl, C["pupil"], rot=30.0),
        ellipse(nx + 20 * K, ny - 6 * K, 10 * K * fl, 14 * K * fl, C["pupil"], rot=-12.0),
    ]
    body = outlined(face, C["face"], items, "clip-face")

    # The mouth. At rest it has none: the muzzle is closed and says nothing.
    mouth = e["mouth"]
    if mouth == "smile":
        body += [line([P(108, 190), P(64, 194), P(30, 170), P(16, 148)], INK, 3.4), line([P(10, 152), P(22, 144)], INK, 3.0)]
    elif mouth == "firm":
        body += [line([P(110, 190), P(62, 190), P(26, 166), P(22, 176)], INK, 3.8)]
    if fl > 1.0:
        # Breath from the nose.
        body += [line([P(150, 158), P(170, 150), P(184, 156)], C["horn_light"], 3.0),
                 line([P(152, 172), P(174, 172), P(186, 182)], C["horn_light"], 3.0)]

    boss = smooth([P(-96, -92), P(-52, -128), P(0, -116), P(52, -128), P(96, -92), P(62, -74), P(0, -84), P(-62, -74)])
    body += outlined(boss, C["horn"], [path(smooth([P(-90, -88), P(0, -92), P(90, -88), P(62, -74), P(0, -84),
                                                    P(-62, -74)]), C["horn_shade"]),
                                       line([P(0, -116), P(0, -84)], C["horn_deep"], 3.0),
                                       line([P(-40, -122), P(-34, -80)], C["horn_deep"], 2.2),
                                       line([P(40, -122), P(34, -80)], C["horn_deep"], 2.2)], "clip-boss")

    # The eyes: round, with a pale ring, the far one a little smaller because
    # the head is turned. A lid and where the pupil is make the look.
    eyes = ((EYES[0][0], EYES[0][1] * K, 1.0, 0), (EYES[1][0], EYES[1][1] * K, -1.0, 1))
    for (dx, dy), r, sgn, i in eyes:
        ex, ey = P(dx, dy)
        body.append(ellipse(ex, ey, r * 1.26, r * 1.26, C["face_light"]))
        lx, ly = e["look"][i][0] * r, e["look"][i][1] * r
        iris = C["iris_hot"] if e["hot"] else C["iris"]
        body += [ellipse(ex, ey, r, r, C["white"], INK, 2 * OW),
                 ellipse(ex + lx, ey + ly, r * 0.64, r * 0.64, iris, C["iris_dark"], 2.2),
                 ellipse(ex + lx * 1.25, ey + ly * 1.25, r * e["pupil"][i], r * e["pupil"][i], C["pupil"]),
                 ellipse(ex + lx * 1.25 - r * 0.16, ey + ly * 1.25 - r * 0.2, r * 0.09, r * 0.09, "#ffffff")]
        cover, slant, low = e["lids"][i], e["slant"], e["low"]
        cid = f"clip-lid-{i}"
        lids = []
        if cover > 0:
            y_in = ey - r + 2 * r * (cover + slant * 0.5)
            y_out = ey - r + 2 * r * (cover - slant * 0.5)
            a, b = (ex + sgn * (r + 2), y_in), (ex - sgn * (r + 2), y_out)
            right, left = (a, b) if sgn > 0 else (b, a)
            lids += [path(svg.poly([(ex - r - 3, ey - r - 3), (ex + r + 3, ey - r - 3), right, left]), C["dark"]),
                     path(f"M{a[0]:.1f},{a[1]:.1f} L{b[0]:.1f},{b[1]:.1f}", "none", INK, 3.0)]
        if low > 0:
            y = ey + r - 2 * r * low
            lids += [path(svg.poly([(ex - r - 3, y), (ex + r + 3, y), (ex + r + 3, ey + r + 3), (ex - r - 3, ey + r + 3)]),
                          C["dark"]), path(f"M{ex - r:.1f},{y:.1f} L{ex + r:.1f},{y:.1f}", "none", INK, 2.6)]
        if lids:
            body += [f'<clipPath id="{cid}"><circle cx="{ex:.1f}" cy="{ey:.1f}" r="{r:.1f}" /></clipPath>',
                     f'<g clip-path="url(#{cid})">'] + lids + ["</g>", ellipse(ex, ey, r, r, "none", INK, 2 * OW)]
    part("head", "Head", "head", "head", 60, grp(body, tilt))


def draw(stance="sloped", expr=None, horns="gnu", head_only=False) -> str:
    st = STANCES[stance]
    lx, ly = st["lift"]
    expr = expr or st["expr"]
    svg.configure(dx=0.0, dy=0.0, ink=INK, ow=OW, colors=C)
    if not head_only:
        hip, mid, end = st["hind"]
        leg2("far-hind", (hip[0] + 96, hip[1] - 6), (mid[0] + 96, mid[1] - 4), (end[0] + 100, end[1]), True, 10)
        leg2("near-hind", hip, mid, end, False, 28)
        leg2("far-fore", *st["fore"][1], True, 10, st["fore_floor"])
        leg2("near-fore", *st["fore"][0], False, 28, st["fore_floor"])
        n0 = len(svg.PARTS)
        tail()
        (tx, ty), swing = st["tail"]
        for i in range(n0, len(svg.PARTS)):
            pid, label, name, bone, z, extra, body = svg.PARTS[i]
            svg.PARTS[i] = (pid, label, name, bone, z, extra,
                            grp(body, f"translate({tx - 352} {ty - 716}) rotate({swing} 352 716)"))
        beast(st)
    n0 = len(svg.PARTS)
    if not head_only:
        chest()
        epaulet("epaulet-left", SHOULDER_L, SHOULDER_L[0])
        epaulet("epaulet-right", SHOULDER_R, SHOULDER_R[1])
        arm("arm-left", *st["arms"][0])
        arm("arm-right", *st["arms"][1])
    head(expr, horns)
    # The chest, the head and the arms are drawn in one place and lifted to the stance.
    for i in range(n0, len(svg.PARTS)):
        pid, label, name, bone, z, extra, body = svg.PARTS[i]
        svg.PARTS[i] = (pid, label, name, bone, z, extra, grp(body, f"translate({lx} {ly})"))
    svg.PARTS[:] = [(pid, label, name, bone, z, extra, grp(body, f"translate(0 {TOP})"))
                    for pid, label, name, bone, z, extra, body in svg.PARTS]
    return svg.document(size=(W, H), design="giant-gnu-candidate", layer_id="giant-gnu", label=f"Giant gnu - {stance}",
                        comment=["  <!-- A candidate. Not the art of the game. -->"], joints=[])


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        raise SystemExit(__doc__)
    Path(args[0]).write_text(draw(args[1] if len(args) > 1 else "sloped", args[2] if len(args) > 2 else None,
                                  "curl" if "--curl" in sys.argv else "gnu", "--head" in sys.argv))
