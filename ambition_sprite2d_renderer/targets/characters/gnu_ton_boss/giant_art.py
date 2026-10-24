"""The giant gnu (GNU-ton's mount): its drawing, its poses and its frames.

A giant that is like a gnu and is not one, almost a centaur: a beast on four
long legs in a coat of long locks, a chest that stands up at its front to two
broad shoulders, the horns of a gnu, and a plain face whose parts make its
expression. Its back is a slope from a low rump to the left shoulder. Jon
chose the design in stills (2026-10-11); `docs/planning/game/bosses.md` has
the fight it is for.

The drawing is SVG made here (`_svg.py` is the kit) and rasterized by resvg.
A frame is a POSE: a stance (where the body's points are), an expression,
and where the head is. `pose_for` gives the pose of each row's frame, and
`render_giant` draws it into the sheet's frame.

The drawing is in DESIGN units, twice the published frame: the floor is
y=978 and x grows to the giant's front (it faces right). `to_frame` takes a
design point to a pixel of the published frame.

What the drawing shows and does not build:

* where an actor can stand has moss on it (the slope of the back, the level
  part of each horn), and each shoulder has an epaulet;
* it has no bird, and no portal: those are the game's.
"""
from __future__ import annotations

import io
import math
from typing import Dict, List, Optional, Tuple

from PIL import Image

from . import _svg as svg
from ._svg import ellipse, line, outlined, part, path, smooth, tube

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

#: A stance. lift: where the chest, the head and the arms are from their
#: drawn place. rump: the low end of the slope. belly: the line of the
#: beast's underside, rear to front. hind / fore: hip, knee and fetlock of
#: the near leg(s). fore_floors: how far under its fetlock each fore hoof ends
#: (the near one, the far one); on the floor that is 44.
#: tail: its root, and how far it swings out. arms: shoulder, elbow and wrist
#: of the left and of the right arm (before ``lift``).
STANCES = {
    "sloped": dict(
        lift=(-8.0, -180.0), rump=(352.0, 585.0), belly=((396.0, 772.0), (1096.0, 784.0)), expr="ordered",
        hind=((452, 740), (418, 858), (446, 934)), fore=(((1098, 720), (1106, 846), (1100, 934)), ((960, 716), (968, 846), (962, 934))),
        fore_floors=(44.0, 44.0), tail=((346, 612), 14.0),
        arms=(((826, 506), (792, 660), (822, 800)), ((1258, 506), (1304, 660), (1282, 800)))),
    "reared": dict(
        lift=(-10.0, -250.0), rump=(334.0, 655.0), belly=((396.0, 812.0), (1120.0, 606.0)), expr="angry",
        hind=((452, 792), (412, 884), (446, 934)), fore=(((1092, 592), (1180, 668), (1156, 766)), ((984, 588), (1064, 668), (1040, 760))),
        fore_floors=(46.0, 46.0), tail=((330, 690), 34.0),
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


def leg2(name, hip, mid, end, far, z, floor=None, turn=0.0):
    """A long leg in two parts, with a knee, a cuff of long hair and a great hoof.
    ``turn`` turns the cuff and the hoof about the fetlock (degrees): 0 is a hoof
    under its fetlock, -90 a hoof whose sole faces the front (a kick)."""
    skin, shade, hair = (C["far"], C["far_dark"], C["far_dark"]) if far else (C["fur"], C["dark"], C["mane"])
    ex, ey = end
    floor = FLOOR if floor is None else ey + floor
    body = outlined(svg.capsule(hip, mid, 54.0, 31.0), skin,
                    [path(svg.capsule((hip[0] - 24, hip[1]), (mid[0] - 14, mid[1]), 22.0, 12.0), shade)], f"clip-{name}-u")
    body += outlined(svg.capsule(mid, end, 28.0, 25.0), skin,
                     [path(svg.capsule((mid[0] - 13, mid[1]), (ex - 12, ey), 10.0, 9.0), shade)], f"clip-{name}-l")
    body += [ellipse(mid[0], mid[1], 33, 31, skin, INK, 2 * OW), ellipse(mid[0] - 7, mid[1] - 8, 13, 10, C["far"] if far else C["light"])]
    foot = []
    hoof = smooth([(ex - 40, floor - 40, True), (ex + 46, floor - 40, True), (ex + 60, floor, True), (ex - 50, floor, True)])
    foot += outlined(hoof, C["hoof"], [path(svg.poly([(ex - 50, floor - 38), (ex + 58, floor - 38), (ex + 58, floor - 27),
                                                      (ex - 50, floor - 27)]), C["far_dark"] if far else C["hoof_light"]),
                                       line([(ex + 10, floor - 38), (ex + 14, floor)], INK, 2.6)], f"clip-{name}-hoof")
    cuff = smooth([(ex + 44, floor - 84, True), (ex - 40, floor - 84, True)] + locks(ex - 52, ex + 58, floor - 40, floor - 20, 5))
    foot += outlined(cuff, hair, strands(ex - 36, ex + 42, floor - 76, floor - 40, 4, C["far"] if far else C["mane_light"]),
                     f"clip-{name}-cuff")
    body += grp(foot, f"rotate({turn:.2f} {ex:.2f} {ey:.2f})") if turn else foot
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
    # Its hem hangs down over the top of the beast and of its near fore leg:
    # no gap is seen between the chest and what is under it.
    # Its right side comes in to the near fore leg, which is under it.
    bottom = locks(858, 1196, 836, 900, 6)[::-1]
    sil = smooth([(848, 700), (838, 610), (812, 540), (x0 - 4, 492), (x0 + 6, top + 8, True), (x1 - 6, top + 8, True),
                  (x1 + 4, 492), (1272, 560), (1232, 680), (1200, 790)] + bottom)
    items = [
        ellipse(x0 + 54, top + 56, 62, 44, C["mane_light"]),
        ellipse(x1 - 54, top + 56, 62, 44, C["mane_light"]),
        path(smooth([(960, 500), (1124, 500), (1150, 600), (1120, 720), (1042, 770), (964, 720), (934, 600)]), C["fur"]),
        path(smooth([(960, 500), (1124, 500), (1140, 560), (1042, 540), (944, 560)]), C["light"]),
        line([(1042, 548), (1042, 740)], C["dark"], 3.0),
        line([(972, 640), (1010, 656), (1042, 650), (1074, 656), (1112, 640)], C["dark"], 3.0),
    ]
    items += strands(850, 940, 560, 866, 3, C["mane_light"], lean=10.0)
    items += strands(1130, 1210, 560, 866, 3, C["mane_light"], lean=-16.0)
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
    e = EXPRESSIONS[expr] if isinstance(expr, str) else expr
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
    e = EXPRESSIONS[expr] if isinstance(expr, str) else expr
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
    e = EXPRESSIONS[expr] if isinstance(expr, str) else expr
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


# ---------------------------------------------------------------------------
# The published frame, and the poses of the rows.

#: The published frame of the giant's sheets, in pixels.
FRAME = (840, 680)
#: A design point (x, y) is the frame pixel (x / 2 + OFFSET[0], y / 2 + OFFSET[1]).
#: The floor is the same line of the frame in each row: y = 660.
OFFSET = (13.0, 171.0)
#: The giant's BODY in the frame: the beast and its chest, from the top of the
#: shoulders to the floor. Not its head, its horns or its tail: a body that
#: stands by a wall stands by its flank, not by the tip of a horn.
BODY_BBOX = (173, 303, 485, 357)


def to_frame(point):
    """A design point as a pixel of the published frame."""
    return (point[0] * 0.5 + OFFSET[0], point[1] * 0.5 + OFFSET[1])


def mix(a, b, u):
    """``a`` moved toward ``b`` by ``u``: numbers, and tuples of them to any depth."""
    if isinstance(a, (int, float)):
        return a + (b - a) * u
    return tuple(mix(x, y, u) for x, y in zip(a, b))


def mix_stance(a: dict, b: dict, u: float) -> dict:
    out = dict(a)
    for key in ("lift", "rump", "belly", "hind", "fore", "fore_floors", "tail", "arms"):
        out[key] = mix(a[key], b[key], u)
    return out


# ---------------------------------------------------------------------------
# The arms. The sheets of the fight draw them: whole (an arm to its fist), or
# into a PORTAL. The drawing has no portal in it: an arm that goes into one is
# cut at the portal's line, and the game draws the line there.

#: Where a shoulder's arm starts (before the stance lifts it).
ARM_ROOT_L = (826.0, 506.0)
ARM_ROOT_R = (1258.0, 506.0)
#: The line the right fist goes DOWN into in phase 1: its middle, and its
#: half length. A flat line (before the stance lifts it), over the giant's
#: right shoulder and out from it: a body that comes UP out of it is over the
#: height of the giant's back, and can go to the side and stand there.
#: Its opening starts 16 past the arm's root (1258 + 46): what is under the
#: opening and past it is only the arm that went in, so the game can cut the
#: giant at the line and draw that at the far line. It is wide: the giant
#: makes his portals as big as his fist needs.
PUNCH_LINE = ((1451.0, 340.0), 131.0)
#: The two lines the arms are in from the end of phase 1: each stands up,
#: past the elbow. Their middles (before the stance lifts them).
CLAMP_LINE_L = (676.0, 580.0)
CLAMP_LINE_R = (1412.0, 580.0)
CLAMP_HALF = 80.0
_HANG_L = (ARM_ROOT_L, (792.0, 660.0), (822.0, 800.0))
_HANG_R = (ARM_ROOT_R, (1304.0, 660.0), (1282.0, 800.0))
_OUT_L = (ARM_ROOT_L, (748.0, 560.0), (600.0, 580.0))
_OUT_R = (ARM_ROOT_R, (1340.0, 560.0), (1488.0, 580.0))


def _whole_arms(sway=0.0, pts=None):
    left, right = pts or (_HANG_L, _HANG_R)
    move = lambda p, k: (p[0] + sway * k, p[1])  # noqa: E731
    return [dict(kind="limb", name="arm-left", pts=(left[0], move(left[1], 0.5), move(left[2], 1.0))),
            dict(kind="limb", name="arm-right", pts=(right[0], move(right[1], 0.5), move(right[2], 1.0)))]


def _clamped_arms(amount=1.0):
    """Each arm out to its side and into its line. ``amount`` 0 is the arm
    that hangs, 1 is the arm in the line."""
    left, right = mix(_HANG_L, _OUT_L, amount), mix(_HANG_R, _OUT_R, amount)
    return [dict(kind="limb", name="arm-left", pts=left, cut=("x", CLAMP_LINE_L[0], False)),
            dict(kind="limb", name="arm-right", pts=right, cut=("x", CLAMP_LINE_R[0], True))]


# ---------------------------------------------------------------------------
# The blows. A blow is a limb of the giant (its right arm, or its near fore
# leg) that goes into the NEAR line of a portal pair and comes out of the far
# line, by the player. The game draws the two lines and what comes out of the
# far one (it cuts the giant's picture at the near line); this draws the giant
# whole. The limb goes into its line SQUARE to it: through the line, the end of
# the limb is held along the line's normal, and its middle is on the line's
# middle.
#
# Each place of a blow is FINAL: in design units, with the lift of the stance
# `sloped` already in it. A row that moves the body (a lift, a lean) moves the
# root of the limb, and the end of the limb stays on the line: the line is at
# one place of the giant in every row. The game has the same places, typed by
# hand (`choreography::blows` of `ambition_content_modules::gnu_ton`):
# `blow_lines_world` prints them.

#: The lift of the stance `sloped`: a place before the lift, plus this, is final.
SLOPED_LIFT = STANCES["sloped"]["lift"]
#: Where the scholar's soles are (final): the body leans about it, so he does
#: not move when the giant leans under him.
SEAT_FINAL = ((SHOULDER_R[0] + SHOULDER_R[1]) * 0.5 + SLOPED_LIFT[0], SHOULDER_R[2] + SLOPED_LIFT[1])


def _final(p):
    return (p[0] + SLOPED_LIFT[0], p[1] + SLOPED_LIFT[1])


#: Each blow. `line`: the middle of its near line and its normal (the side the
#: giant is on; the limb goes in against it). `back`: how far the wrist (the
#: fetlock of the leg) is on the giant's side of the line when the blow is
#: cocked. `deep`: how far it is past the line at the full blow. `out`: how far
#: on the giant's side it is when the limb has come back out. `past`: how far
#: the middle of the fist (of the hoof) is past the wrist (the fetlock), along
#: the limb's end. `strike`, `hold`, `recover`: the lengths of its rows, in
#: seconds (each row's frames times its frame time in `sprite_generator`).
BLOWS = {
    # Down, from over the right shoulder: a hammer.
    "punch": dict(line=((1443.0, 160.0), (0.0, -1.0)), back=190.0, deep=94.0, out=125.0, past=56.0,
                  strike=0.35, hold=0.28, recover=0.42),
    # Straight out from the right shoulder: a jab. The line is not farther out
    # than this: the fist of the full blow stays in the frame.
    "jab": dict(line=((1390.0, 318.0), (-1.0, 0.0)), back=190.0, deep=110.0, out=120.0, past=56.0,
                strike=0.24, hold=0.24, recover=0.40),
    # Up, in front of the chest: an uppercut.
    "upper": dict(line=((1430.0, 150.0), (0.0, 1.0)), back=150.0, deep=100.0, out=120.0, past=56.0,
                  strike=0.30, hold=0.24, recover=0.40),
    # Forward with the near fore leg, low: a kick. The fetlock is the end of
    # the leg; the hoof is past it.
    "kick": dict(line=((1290.0, 800.0), (-1.0, 0.0)), back=50.0, deep=100.0, out=50.0, past=24.0,
                 strike=0.30, hold=0.24, recover=0.42),
}
#: How far the end of a limb gives back toward its line in the row `*_hold`.
HOLD_GIVE = 14.0
#: The part of the row `*_strike` at which the blow is full (it is still after).
STRIKE_FULL = 0.8
#: The part of the row `*_recover` at which the limb is out of its line.
RECOVER_OUT = 0.45
#: The last part of a row `*_windup`: the blow is cocked, and trembles.
COCKED_AT = 0.78


def blow_wrist_depth(blow: str, part: str, phase: float) -> Optional[float]:
    """How far the end of the limb (the wrist, the fetlock) is past the near
    line in the row ``part`` (``strike``, ``hold``, ``recover``) at ``phase``
    (0..1 of the row); less than 0: on the giant's side. ``None``: the limb is
    not on its way through (the windup, and the end of the recover). The game
    poses the limb's body by the same numbers (`choreography::blows::depth`)."""
    b = BLOWS[blow]
    if part == "strike":
        u = min(1.0, phase / STRIKE_FULL)
        return -b["back"] + (b["deep"] + b["back"]) * u * u * u
    if part == "hold":
        return b["deep"] - HOLD_GIVE * abs(math.sin(2.0 * math.pi * min(1.0, phase)))
    if part == "recover" and phase < RECOVER_OUT:
        return b["deep"] + (-b["out"] - b["deep"]) * _ease(phase / RECOVER_OUT)
    return None


def _on_line(blow, depth):
    """The point ``depth`` past the near line of ``blow``, on its middle."""
    (cx, cy), (nx, ny) = BLOWS[blow]["line"]
    return (cx - nx * depth, cy - ny * depth)


def _square(blow, depth, first, length):
    """An arm key whose end is square to the line: the wrist ``depth`` past it,
    the end coming along the line's inward normal over ``length``."""
    _, (nx, ny) = BLOWS[blow]["line"]
    return (_on_line(blow, depth), first, (-nx * length, -ny * length))


#: The right arm at rest (final): wrist, first handle, the way its end goes.
_A_HANG = (_final((1282.0, 800.0)), (46.0, 150.0), (0.0, 140.0))

#: The arm keys of each blow, before it is cocked and while it comes back: (until,
#: key). The keys of the line itself (cocked, full, out) are made by `_square`.
_ARM_KEYS = {
    "punch": dict(
        wind=[(0.0, _A_HANG), (0.28, (_final((1480.0, 520.0)), (150.0, 60.0), (100.0, -90.0))),
              (0.52, (_final((1440.0, 160.0)), (120.0, -170.0), (-120.0, -60.0))),
              # Over the top, past the place it is cocked: the hammer is up.
              (0.68, ((1420.0, -70.0), (-30.0, -330.0), (20.0, 120.0)))],
        cocked_first=(-24.0, -340.0), full_first=(-6.0, -330.0), out_first=(-10.0, -300.0),
        cocked_len=120.0, full_len=220.0, out_len=120.0,
        home=[(0.62, (_final((1460.0, 250.0)), (130.0, -120.0), (-120.0, -40.0))),
              (0.82, (_final((1480.0, 520.0)), (150.0, 60.0), (100.0, -90.0))), (1.0, _A_HANG)]),
    "jab": dict(
        wind=[(0.0, _A_HANG), (0.3, ((1300.0, 470.0), (40.0, 60.0), (60.0, -60.0))),
              # Drawn back past where it is cocked: the elbow high and behind,
              # the fist by the jaw.
              (0.62, ((1160.0, 300.0), (-10.0, -230.0), (100.0, 10.0)))],
        cocked_first=(-20.0, -210.0), full_first=(90.0, 0.0), out_first=(-50.0, 90.0),
        cocked_len=110.0, full_len=150.0, out_len=110.0,
        home=[(0.7, ((1240.0, 480.0), (-30.0, 120.0), (30.0, 100.0))), (1.0, _A_HANG)]),
    "upper": dict(
        wind=[(0.0, _A_HANG), (0.3, ((1180.0, 690.0), (-40.0, 150.0), (0.0, 120.0))),
              # Down and back, low: the fist by the knee.
              (0.6, ((1250.0, 720.0), (-10.0, 190.0), (40.0, 110.0)))],
        cocked_first=(40.0, 220.0), full_first=(110.0, -40.0), out_first=(60.0, 140.0),
        cocked_len=130.0, full_len=200.0, out_len=120.0,
        home=[(0.7, ((1380.0, 520.0), (80.0, 120.0), (-20.0, 120.0))), (1.0, _A_HANG)]),
}

#: The near fore leg: hip, knee, fetlock (final; the legs are not lifted).
_L_REST = ((1098.0, 720.0), (1106.0, 846.0), (1100.0, 934.0))
_L_LIFT = ((1098.0, 716.0), (1168.0, 782.0), (1150.0, 880.0))


def _leg_at(fetlock_depth):
    """The near fore leg with its fetlock ``fetlock_depth`` past the kick's
    line, its lower leg along the line's inward normal (level)."""
    (fx, fy) = _on_line("kick", fetlock_depth)
    hip = (1098.0, 716.0)
    # The knee is behind the fetlock, level with it: the lower leg is square
    # to the line. It is never past the line.
    knee = (min(fx - 70.0, BLOWS["kick"]["line"][0][0] - 40.0), fy)
    return (hip, knee, (fx, fy))


def _blow_arm(blow, part, phase):
    """The right arm's key (wrist, first handle, the way its end goes) in a row
    of a punch."""
    b, k = BLOWS[blow], _ARM_KEYS[blow]
    cocked = _square(blow, -b["back"], k["cocked_first"], k["cocked_len"])
    full = _square(blow, b["deep"], k["full_first"], k["full_len"])
    out = _square(blow, -b["out"], k["out_first"], k["out_len"])
    if part == "windup":
        keys = list(k["wind"]) + [(COCKED_AT, cocked)]
        if phase <= COCKED_AT:
            return _between(keys, phase)
        # Cocked, and it trembles: a blow about to go.
        (wx, wy), first, last = cocked
        s = math.sin(phase * 97.0)
        return ((wx + 3.0 * s, wy + 2.0 * math.cos(phase * 71.0)), first, last)
    depth = blow_wrist_depth(blow, part, phase)
    if part == "strike":
        u = min(1.0, phase / STRIKE_FULL)
        key = mix(cocked, full, u * u * u)
        return (_on_line(blow, depth),) + tuple(key[1:])
    if part == "hold":
        return (_on_line(blow, depth),) + tuple(full[1:])
    # recover: back out along the line, then home.
    if depth is not None:
        u = _ease(phase / RECOVER_OUT)
        key = mix(full, out, u)
        return (_on_line(blow, depth),) + tuple(key[1:])
    return _between([(RECOVER_OUT, out)] + list(k["home"]), phase)


def _blow_leg(part, phase):
    """The near fore leg in a row of the kick: hip, knee, fetlock."""
    b = BLOWS["kick"]
    cocked = _leg_at(-b["back"])
    if part == "windup":
        if phase <= COCKED_AT:
            return _between([(0.0, _L_REST), (0.4, _L_LIFT), (COCKED_AT, cocked)], phase)
        hip, knee, (fx, fy) = cocked
        return (hip, knee, (fx + 3.0 * math.sin(phase * 97.0), fy + 2.0 * math.cos(phase * 71.0)))
    depth = blow_wrist_depth("kick", part, phase)
    if depth is not None:
        return _leg_at(depth)
    return _between([(RECOVER_OUT, _leg_at(-b["out"])), (0.72, _L_LIFT), (1.0, _L_REST)], phase)


#: How the body moves in each part of a blow: (until, (lift down, lean in
#: degrees about the seat, the head's offset, the face, the face's tilt)).
#: A lean that is more than 0 is toward the giant's front.
_BODY = {
    "punch": dict(
        windup=[(0.0, (0.0, 0.0, (0.0, 0.0))), (0.5, (-10.0, -2.0, (-4.0, -6.0))), (COCKED_AT, (-26.0, -5.0, (-12.0, -14.0)))],
        strike=[(0.0, (-26.0, -5.0, (-12.0, -14.0))), (0.8, (18.0, 5.0, (16.0, 24.0)))],
        recover=[(0.0, (18.0, 5.0, (16.0, 24.0))), (1.0, (0.0, 0.0, (0.0, 0.0)))]),
    "jab": dict(
        windup=[(0.0, (0.0, 0.0, (0.0, 0.0))), (COCKED_AT, (8.0, -6.0, (-18.0, 6.0)))],
        strike=[(0.0, (8.0, -6.0, (-18.0, 6.0))), (0.8, (4.0, 7.0, (24.0, 4.0)))],
        recover=[(0.0, (4.0, 7.0, (24.0, 4.0))), (1.0, (0.0, 0.0, (0.0, 0.0)))]),
    "upper": dict(
        windup=[(0.0, (0.0, 0.0, (0.0, 0.0))), (COCKED_AT, (26.0, 5.0, (12.0, 30.0)))],
        strike=[(0.0, (26.0, 5.0, (12.0, 30.0))), (0.8, (-26.0, -5.0, (-6.0, -22.0)))],
        recover=[(0.0, (-26.0, -5.0, (-6.0, -22.0))), (1.0, (0.0, 0.0, (0.0, 0.0)))]),
    "kick": dict(
        windup=[(0.0, (0.0, 0.0, (0.0, 0.0))), (COCKED_AT, (-12.0, -4.0, (-10.0, -8.0)))],
        strike=[(0.0, (-12.0, -4.0, (-10.0, -8.0))), (0.8, (6.0, 3.0, (14.0, 10.0)))],
        recover=[(0.0, (6.0, 3.0, (14.0, 10.0))), (1.0, (0.0, 0.0, (0.0, 0.0)))]),
}

#: The left arm (before the lift, as `_whole_arms` has it): at rest, braced
#: forward, guarding up, and swung back.
_LEFT = dict(
    hang=_HANG_L,
    brace=(ARM_ROOT_L, (760.0, 650.0), (850.0, 760.0)),
    guard=(ARM_ROOT_L, (900.0, 600.0), (960.0, 470.0)),
    back=(ARM_ROOT_L, (740.0, 640.0), (680.0, 740.0)),
    up=(ARM_ROOT_L, (740.0, 520.0), (700.0, 400.0)),
)
#: What the left arm does in each part of each blow: (until, pose name).
_LEFT_KEYS = {
    "punch": dict(windup=[(0.0, "hang"), (COCKED_AT, "brace")], strike=[(0.0, "brace"), (0.8, "back")],
                  recover=[(0.0, "back"), (1.0, "hang")]),
    "jab": dict(windup=[(0.0, "hang"), (COCKED_AT, "guard")], strike=[(0.0, "guard"), (0.8, "back")],
                recover=[(0.0, "back"), (1.0, "hang")]),
    "upper": dict(windup=[(0.0, "hang"), (COCKED_AT, "brace")], strike=[(0.0, "brace"), (0.8, "back")],
                  recover=[(0.0, "back"), (1.0, "hang")]),
    "kick": dict(windup=[(0.0, "hang"), (COCKED_AT, "back")], strike=[(0.0, "back"), (0.8, "brace")],
                 recover=[(0.0, "brace"), (1.0, "hang")]),
}
#: The right arm of an armed kick (before the lift): up and out of the way of
#: the kick's line, for balance.
_RIGHT_UP = (ARM_ROOT_R, (1340.0, 470.0), (1350.0, 370.0))


def _keys_at(keys, phase):
    return _between(keys, phase)


def _named_at(keys, table, phase):
    """A pose of ``table`` by name, eased from key to key."""
    return _between([(until, table[name]) for until, name in keys], phase)


def blow_parts(anim: str):
    """``(blow, part, armed)`` of a row of a blow, or ``None``. ``punch_*`` is
    the hammer; ``jab_*``, ``upper_*``; ``kick_*`` with the arms in their lines
    and ``armed_kick_*`` with the arms on."""
    armed = True
    if anim.startswith("armed_kick_"):
        anim = anim[len("armed_"):]
    elif anim.startswith("kick_"):
        armed = False
    for blow in BLOWS:
        prefix = blow + "_"
        if anim.startswith(prefix):
            part = anim[len(prefix):]
            if part in ("windup", "strike", "hold", "recover"):
                return blow, part, armed
    return None


def _blow_pose(pose, blow, part, armed, phase):
    """Fill ``pose`` (from `pose_for`) for a row of a blow."""
    sloped = STANCES["sloped"]
    body = _BODY[blow]
    if part == "hold":
        # The blow lands: the body jolts and comes back (its recoil).
        drop, lean, head = body["strike"][-1][1]
        jolt = math.sin(math.pi * min(1.0, phase * 2.5)) * (1.0 - phase)
        drop, lean, head = drop + 10.0 * jolt, lean - 2.5 * jolt, (head[0] - 8.0 * jolt, head[1] + 8.0 * jolt)
    else:
        drop, lean, head = _keys_at(body[part], phase)
    s = dict(sloped)
    s["lift"] = (sloped["lift"][0], sloped["lift"][1] + drop)
    pose["stance"] = s
    pose["lean"] = lean
    pose["head"] = head
    cocked = part == "windup" and phase > COCKED_AT * 0.6
    name = "angry" if part != "windup" or cocked else "serious"
    tilt = lean * 0.8 + (2.0 * math.sin(phase * 61.0) if part == "windup" and phase > COCKED_AT else 0.0)
    pose["expr"] = dict(EXPRESSIONS[name], tilt=EXPRESSIONS[name]["tilt"] + tilt)
    left_part = "strike" if part == "hold" else part
    left_phase = 1.0 if part == "hold" else phase
    left = _named_at(_LEFT_KEYS[blow][left_part], _LEFT, left_phase)
    left_spec = dict(kind="limb", name="arm-left", pts=left)
    if blow == "kick":
        pose["kick"] = _blow_leg(part, phase)
        if armed:
            right = mix(_HANG_R, _RIGHT_UP, _ease(min(1.0, phase / 0.5)) if part == "windup" else
                        (1.0 if part != "recover" else 1.0 - _ease(phase)))
            pose["arms"] = [left_spec, dict(kind="limb", name="arm-right", pts=right)]
        else:
            pose["arms"] = _clamped_arms(1.0)
        return pose
    wrist, first, last = _blow_arm(blow, part, phase)
    size = math.hypot(*last) or 1.0
    # The arm of a blow is FIXED to the giant (its end is on the line), so it
    # is drawn outside the body's lift and lean: its root is moved by them here.
    root = _lean_point(_final(ARM_ROOT_R), lean)
    root = (root[0], root[1] + drop)
    # The jab is cocked by the jaw: its arm is in front of the head.
    z = 62 if blow == "jab" else 40
    pose["arms"] = [left_spec, dict(kind="soft", name="arm-right", fixed=True, z=z, toward=(last[0] / size, last[1] / size),
                                    handles=(root, (root[0] + first[0], root[1] + first[1]),
                                             (wrist[0] - last[0], wrist[1] - last[1]), wrist))]
    return pose


def _lean_point(p, lean):
    """``p`` (final) turned by ``lean`` degrees about the seat."""
    a = math.radians(lean)
    sx, sy = SEAT_FINAL
    dx, dy = p[0] - sx, p[1] - sy
    return (sx + dx * math.cos(a) - dy * math.sin(a), sy + dx * math.sin(a) + dy * math.cos(a))


def blow_lines_world():
    """Each blow's near line in the world, from the middle of the giant's body
    (+y down), and the scale of a design unit: the numbers the game types."""
    cx = BODY_BBOX[0] + BODY_BBOX[2] * 0.5
    cy = BODY_BBOX[1] + BODY_BBOX[3] * 0.5
    out = {}
    for blow, b in BLOWS.items():
        (x, y), normal = b["line"]
        out[blow] = dict(at=((x * 0.5 + OFFSET[0] - cx) * WORLD_PER_PIXEL, (y * 0.5 + OFFSET[1] - cy) * WORLD_PER_PIXEL),
                         normal=normal, back=b["back"], deep=b["deep"], out=b["out"], past=b["past"],
                         strike=b["strike"], hold=b["hold"], recover=b["recover"])
    return dict(design=0.5 * WORLD_PER_PIXEL, blows=out)


#: World units of a pixel of the published frame (the catalog's `posed_body`).
WORLD_PER_PIXEL = 1.3


def _between(keys, phase):
    """``keys``: (until, key) in order. The pose at ``phase``, eased from each
    key to the next."""
    start, last = keys[0]
    if phase <= start:
        return last
    for until, key in keys[1:]:
        if phase <= until:
            return mix(last, key, _ease((phase - start) / max(1e-6, until - start)))
        start, last = until, key
    return last


def punch_depth(anim: str, phase: float) -> float:
    """How far past its line the wrist of the hammer is in a row `punch_*`
    (less than 0: over it). A fist that is not on its way through is far over
    it. For the fist's own rows `through_*`."""
    part = anim[len("punch_"):]
    depth = blow_wrist_depth("punch", part, phase) if part != "windup" else None
    return depth if depth is not None else -9000.0


#: How far past its line the wrist is at the end of the hammer. The fist's own
#: sheet draws the far side of the punch from this.
PUNCH_DEPTH_DOWN = BLOWS["punch"]["deep"]


#: Down, at the end of its fight: the body low, the legs folded under it.
FALLEN = dict(
    lift=(18.0, 70.0), rump=(352.0, 800.0), belly=((396.0, 930.0), (1096.0, 936.0)), expr="sleepy",
    hind=((452, 892), (372, 930), (446, 934)), fore=(((1098, 884), (1190, 924), (1104, 934)), ((960, 880), (1040, 924), (966, 934))),
    fore_floors=(44.0, 44.0), tail=((346, 826), 62.0),
    arms=(((826, 506), (792, 660), (822, 800)), ((1258, 506), (1304, 660), (1282, 800))))
#: A fore hoof up, for the stomp.
HOOF_UP = dict(STANCES["sloped"], lift=(-12.0, -196.0),
               fore=(((1098, 706), (1176, 770), (1150, 852)), STANCES["sloped"]["fore"][1]))
#: The eyes shut.
_SHUT = dict(EXPRESSIONS["sleepy"], lids=(0.94, 0.94))


def _ease(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3.0 - 2.0 * u)


def pose_for(anim: str, phase: float) -> dict:
    """The pose of one frame of a row. ``phase`` is 0..1 along the row.

    A pose: stance (the body), expr (the face), head (how far the head is
    from its place), dust (0..1: the dust of a hoof that came down).
    """
    two_pi = 2.0 * math.pi
    sloped = STANCES["sloped"]
    pose = dict(stance=sloped, expr=EXPRESSIONS["ordered"], head=(0.0, 0.0), dust=0.0, arms=[])
    blow = blow_parts(anim)
    if blow is not None:
        return _blow_pose(pose, *blow, phase)
    # A row draws the giant with its arms in the two lines: its fists are
    # bodies of their own. A row `armed_*` is the same body with whole arms
    # and its fists on them (phase 1). `*_b` is a copy of a row: a pinned row
    # does not loop, so the game goes from a row to its copy and back.
    armed = anim.startswith("armed_")
    if armed:
        anim = anim[len("armed_"):]
    if anim.endswith("_b"):
        anim = anim[:-2]

    def breathe(st, amount=1.0):
        s = dict(st)
        s["lift"] = (st["lift"][0], st["lift"][1] + 5.0 * amount * math.sin(two_pi * phase))
        s["rump"] = (st["rump"][0], st["rump"][1] + 2.0 * amount * math.sin(two_pi * phase + 1.0))
        (root, swing) = st["tail"]
        s["tail"] = (root, swing + 5.0 * amount * math.sin(two_pi * phase + 2.0))
        return s

    def face(name, tilt=0.0, **over):
        e = dict(EXPRESSIONS[name], **over)
        e["tilt"] = e["tilt"] + tilt
        return e

    if anim == "rest":
        pose["stance"] = breathe(sloped)
        pose["head"] = (0.0, 3.0 * math.sin(two_pi * phase - 0.6))
        # One blink in the loop.
        blink = 0.7 <= phase < 0.8
        pose["expr"] = face("ordered", 1.2 * math.sin(two_pi * phase), **({"lids": (0.92, 0.92), "slant": 0.0} if blink else {}))
    elif anim == "hand_slam":
        # It lifts with the fists and comes down with them.
        up = math.sin(math.pi * min(1.0, phase / 0.45)) if phase < 0.45 else 0.0
        down = math.sin(math.pi * (phase - 0.45) / 0.55) if phase >= 0.45 else 0.0
        s = dict(sloped)
        s["lift"] = (sloped["lift"][0], sloped["lift"][1] - 16.0 * up + 20.0 * down)
        pose["stance"] = s
        pose["head"] = (0.0, 26.0 * down - 8.0 * up)
        pose["expr"] = face("angry" if phase >= 0.3 else "serious", 3.0 * down)
    elif anim == "hand_sweep":
        swing = math.sin(two_pi * phase)
        pose["stance"] = breathe(sloped, 0.5)
        pose["head"] = (22.0 * swing, 4.0 * abs(swing))
        pose["expr"] = face("serious", 4.0 * swing)
    elif anim == "head_down":
        low = math.sin(math.pi * phase)
        s = dict(sloped)
        s["lift"] = (sloped["lift"][0], sloped["lift"][1] + 12.0 * low)
        pose["stance"] = s
        pose["head"] = (10.0 * low, 150.0 * low)
        pose["expr"] = face("angry", 8.0 * low)
    elif anim == "hit":
        jolt = (1.0 - phase) * math.cos(two_pi * phase * 1.5)
        s = dict(sloped)
        s["lift"] = (sloped["lift"][0] - 8.0 * jolt, sloped["lift"][1] - 14.0 * jolt)
        (root, swing) = sloped["tail"]
        s["tail"] = (root, swing + 26.0 * (1.0 - phase))
        pose["stance"] = s
        pose["head"] = (-10.0 * jolt, -6.0 * jolt)
        pose["expr"] = face("dazed" if phase < 0.7 else "ordered", -6.0 * jolt)
    elif anim == "death":
        fall = _ease((phase - 0.15) / 0.75)
        pose["stance"] = mix_stance(sloped, FALLEN, fall)
        pose["head"] = (30.0 * fall, 250.0 * fall)
        name = "dazed" if phase < 0.3 else "sleepy"
        pose["expr"] = _shut_face(18.0 * fall) if phase >= 0.7 else face(name, 18.0 * fall)
    elif anim == "buck":
        up = math.sin(math.pi * phase) ** 0.8
        pose["stance"] = mix_stance(sloped, STANCES["reared"], up)
        pose["expr"] = face("angry")
    elif anim == "stomp":
        # The hoof goes up, and is down at 0.7 of the row: the conductor's
        # stomp lands then.
        if phase < 0.7:
            up = math.sin(math.pi * min(1.0, phase / 0.62) * 0.5) if phase < 0.62 else 1.0 - (phase - 0.62) / 0.08
        else:
            up = 0.0
        pose["stance"] = mix_stance(sloped, HOOF_UP, max(0.0, up))
        pose["dust"] = max(0.0, 1.0 - (phase - 0.7) / 0.3) if phase >= 0.7 else 0.0
        pose["head"] = (0.0, 10.0 * (1.0 if phase >= 0.7 else 0.0) * (1.0 - (phase - 0.7) / 0.3))
        pose["expr"] = face("angry" if phase < 0.85 else "serious")
    elif anim == "clamp":
        # The arms go out to each side and into the lines; the lines close on them.
        out = _ease(min(1.0, phase / 0.7))
        pose["stance"] = breathe(sloped, 0.5)
        pose["expr"] = face("dazed" if phase < 0.5 else "angry")
        pose["arms"] = _clamped_arms(out)
        return pose

    if not armed:
        pose["arms"] = _clamped_arms(1.0)
    elif anim == "buck":
        pose["arms"] = _whole_arms(pts=pose["stance"]["arms"])
    else:
        pose["arms"] = _whole_arms(sway=6.0 * math.sin(two_pi * phase) if anim == "rest" else 0.0)
    return pose


def _shut_face(tilt):
    e = dict(_SHUT)
    e["tilt"] = e["tilt"] + tilt
    return e


def _dust(at, amount):
    """The dust of a hoof that came down: three puffs that grow and thin."""
    x, y = at
    grow = 1.0 - amount
    out = []
    for dx, r in ((-70.0, 26.0), (0.0, 34.0), (74.0, 24.0)):
        rr = r * (0.6 + 0.9 * grow)
        out.append(f'<ellipse cx="{x + dx * (1.0 + grow):.1f}" cy="{y - rr * 0.5 - 30.0 * grow:.1f}" rx="{rr * 1.3:.1f}" '
                   f'ry="{rr:.1f}" fill="#cbb994" stroke="{INK}" stroke-width="2" opacity="{0.85 * amount:.2f}" />')
    return out


def soft_arm(name, p0, p1, p2, p3, toward):
    """An arm as one curve (a cubic through four handles), and its fist. Its
    end goes the way ``toward``: the arm of a punch, which is longer in the
    blow than at rest."""
    def at(u):
        a, b, c, d = (1 - u) ** 3, 3 * u * (1 - u) ** 2, 3 * u * u * (1 - u), u ** 3
        return (a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1])

    n = 22
    mid = [at(k / n) for k in range(n + 1)]
    left, right, shade, light = [], [], [], []
    for k, (x, y) in enumerate(mid):
        ax, ay = mid[max(0, k - 1)]
        bx, by = mid[min(n, k + 1)]
        d = math.hypot(bx - ax, by - ay) or 1.0
        nx, ny = -(by - ay) / d, (bx - ax) / d
        u = k / n
        r = 46.0 - 2.0 * u - 9.0 * math.sin(math.pi * u)
        left.append((x + nx * r, y + ny * r))
        right.append((x - nx * r, y - ny * r))
        shade.append((x + nx * r * 0.45, y + ny * r * 0.45))
        light.append((x - nx * r * 0.55, y - ny * r * 0.55))
    sil = smooth(left + right[::-1])
    items = [path(smooth(left + shade[::-1]), C["dark"]),
             path(smooth(list(light[3:-3]), closed=False), "none", C["light"], 9.0)]
    ex, ey = mid[n // 2]
    tuft = smooth([(ex - 30, ey - 6, True), (ex + 30, ey - 6, True), (ex + 26, ey + 30), (ex + 10, ey + 58, True),
                   (ex, ey + 34), (ex - 12, ey + 64, True), (ex - 26, ey + 28)])
    body = outlined(tuft, C["mane"], [], None) + outlined(sil, C["fur"], items, f"clip-{name}")
    fx, fy = p3[0] + toward[0] * 56, p3[1] + toward[1] * 56
    turn = math.degrees(math.atan2(-toward[1], -toward[0]))
    body += [f'<g transform="translate({fx:.1f} {fy:.1f}) rotate({turn:.1f})">'] + fist(f"{name}-fist") + ["</g>"]
    return body


def _cut(cid, cut):
    """A clip at a portal's line: ("x" or "y", where, keep the lower side), or
    ("hole", x0, y0, x1, y1)."""
    if cut[0] == "hole":
        # All but one box: what went into the line of a punch.
        _, x0, y0, x1, y1 = cut
        return (f'<clipPath id="{cid}"><path clip-rule="evenodd" d="M -9000 -9000 H 9000 V 9000 H -9000 Z '
                f'M {x0} {y0} H {x1} V {y1} H {x0} Z" /></clipPath>')
    axis, where, low = cut
    if axis == "x":
        x0, x1 = (-9000.0, where) if low else (where, 9000.0)
        return f'<clipPath id="{cid}"><rect x="{x0}" y="-9000" width="{x1 - x0}" height="18000" /></clipPath>'
    y0, y1 = (-9000.0, where) if low else (where, 9000.0)
    return f'<clipPath id="{cid}"><rect x="-9000" y="{y0}" width="18000" height="{y1 - y0}" /></clipPath>'


def _draw_arm(spec):
    name = spec["name"]
    if spec["kind"] == "soft":
        body = soft_arm(name, *spec["handles"], spec["toward"])
    else:
        n0 = len(svg.PARTS)
        arm(name, *spec["pts"])
        body = svg.PARTS.pop(n0)[6]
    if spec.get("cut"):
        body = [_cut(f"cut-{name}", spec["cut"]), f'<g clip-path="url(#cut-{name})">'] + body + ["</g>"]
    part(name, name, name.replace("-", "_"), name.replace("-", "_"), spec.get("z", 40), body)


def giant_svg(pose: dict, *, arms: bool = False, horns: str = "gnu", view=None) -> str:
    """The giant in ``pose`` as an SVG. ``view`` is (x, y, w, h) in design
    units; the default is the published frame. ``arms`` draws an arm from each
    shoulder to its fist for a pose that says none."""
    st = pose["stance"]
    lx, ly = st["lift"]
    hx, hy = pose["head"]
    svg.configure(dx=0.0, dy=0.0, ink=INK, ow=OW, colors=C)
    hip, mid, end = st["hind"]
    leg2("far-hind", (hip[0] + 96, hip[1] - 6), (mid[0] + 96, mid[1] - 4), (end[0] + 100, end[1]), True, 10)
    leg2("near-hind", hip, mid, end, False, 28)
    leg2("far-fore", *st["fore"][1], True, 10, st["fore_floors"][1])
    if pose.get("kick"):
        # The near fore leg kicks: the hoof is turned along the lower leg.
        hip, knee, fet = pose["kick"]
        turn = math.degrees(math.atan2(fet[1] - knee[1], fet[0] - knee[0])) - 90.0
        leg2("near-fore", hip, knee, fet, False, 28, 44.0, turn=turn)
    else:
        leg2("near-fore", *st["fore"][0], False, 28, st["fore_floors"][0])
    n0 = len(svg.PARTS)
    tail()
    (tx, ty), swing = st["tail"]
    for i in range(n0, len(svg.PARTS)):
        pid, label, name, bone, z, extra, body = svg.PARTS[i]
        svg.PARTS[i] = (pid, label, name, bone, z, extra,
                        grp(body, f"translate({tx - 352:.2f} {ty - 716:.2f}) rotate({swing:.2f} 352 716)"))
    beast(st)
    n0 = len(svg.PARTS)
    chest()
    epaulet("epaulet-left", SHOULDER_L, SHOULDER_L[0])
    epaulet("epaulet-right", SHOULDER_R, SHOULDER_R[1])
    drawn = pose.get("arms") or (_whole_arms(pts=st["arms"]) if arms else [])
    for spec in drawn:
        if not spec.get("fixed"):
            _draw_arm(spec)
    n1 = len(svg.PARTS)
    head(pose["expr"], horns)
    if hx or hy:
        for i in range(n1, len(svg.PARTS)):
            pid, label, name, bone, z, extra, body = svg.PARTS[i]
            svg.PARTS[i] = (pid, label, name, bone, z, extra, grp(body, f"translate({hx:.2f} {hy:.2f})"))
    # The chest, the head and the arms are drawn in one place and lifted to the
    # stance, and leaned about the seat (the scholar stays on it).
    lean = pose.get("lean", 0.0)
    sx, sy = (SHOULDER_R[0] + SHOULDER_R[1]) * 0.5, SHOULDER_R[2]
    turned = f" rotate({lean:.2f} {sx:.2f} {sy:.2f})" if lean else ""
    for i in range(n0, len(svg.PARTS)):
        pid, label, name, bone, z, extra, body = svg.PARTS[i]
        svg.PARTS[i] = (pid, label, name, bone, z, extra, grp(body, f"translate({lx:.2f} {ly:.2f}){turned}"))
    # The arm of a blow is fixed to the giant: its end is on its portal's line.
    for spec in drawn:
        if spec.get("fixed"):
            _draw_arm(spec)
    if pose.get("dust", 0.0) > 0.0:
        fx, _fy = st["fore"][0][2]
        part("dust", "Dust", "dust", "dust", 90, _dust((fx, FLOOR), pose["dust"]))
    if view is None:
        view = (-2.0 * OFFSET[0], -2.0 * OFFSET[1], 2.0 * FRAME[0], 2.0 * FRAME[1])
    return _document(view)


def _document(view) -> str:
    x, y, w, h = view
    out = ['<svg xmlns="http://www.w3.org/2000/svg" '
           f'width="{w:g}" height="{h:g}" viewBox="{x:g} {y:g} {w:g} {h:g}">']
    for _pid, _label, _name, _bone, _z, _extra, body in sorted(svg.PARTS, key=lambda p: p[4]):
        out.extend(body)
    out.append("</svg>")
    return "\n".join(out)


def _raster(svg_text: str, size: Tuple[int, int]) -> Image.Image:
    import resvg_py

    data = resvg_py.svg_to_bytes(svg_string=svg_text, skip_system_fonts=True)
    image = Image.open(io.BytesIO(bytes(data))).convert("RGBA")
    return image if image.size == size else image.resize(size, Image.LANCZOS)


def render_giant(anim: str, frame_idx: int, frame_count: int) -> Image.Image:
    """One frame of the giant's body (no fists, no scholar), at ``FRAME``."""
    pose = pose_for(anim, frame_idx / max(1, frame_count))
    return _raster(giant_svg(pose), FRAME)


def head_place(pose: dict) -> Tuple[float, float]:
    """Where the middle of the face is in the published frame, in ``pose``."""
    lx, ly = pose["stance"]["lift"]
    hx, hy = pose["head"]
    return to_frame((HEAD[0] + lx + hx, HEAD[1] + 40.0 + ly + hy))


def seat_place(pose: dict) -> Tuple[float, float]:
    """Where a rider's soles are in the published frame: the middle of the
    right shoulder's top."""
    lx, ly = pose["stance"]["lift"]
    return to_frame(((SHOULDER_R[0] + SHOULDER_R[1]) * 0.5 + lx, SHOULDER_R[2] + ly))


# ---------------------------------------------------------------------------
# A fist of the giant, as a body of its own.

#: The frame of the lone fist's sheet. Its top edge is the line of the punch's
#: far portal: the row `through_*` comes down out of it.
FIST_FRAME = (160, 162)
#: The fist's BODY in its frame: the mitt and its knuckles. Not its fore arm.
#: How far it is under the top edge says how high the far line of a punch is
#: over the floor (the fist comes down to the floor): 145 world units, which a
#: player's two jumps from the floor reach (about 148 of rise, and half of its
#: own height).
FIST_BBOX = (34, 36, 92, 76)
#: Where the far line of a punch is, from the middle of the fist's body, in
#: pixels of the frame: over it. The game puts the portal there.
FIST_LINE_OVER = FIST_BBOX[1] + FIST_BBOX[3] * 0.5
#: The rows of the fist's sheet: its name, its frames, the time of a frame.
FIST_ROWS = (("rest", 10, 110), ("fall", 6, 70), ("hit", 6, 80), ("stuck", 8, 70),
             ("through_strike", 5, 70), ("through_hold", 4, 70), ("through_recover", 6, 70), ("none", 1, 110))


def _fist_document():
    w, h = FIST_FRAME
    cx, cy = FIST_BBOX[0] + FIST_BBOX[2] * 0.5, FIST_BBOX[1] + FIST_BBOX[3] * 0.5
    # The middle of the fist's body is the design origin.
    return _document((-2.0 * cx, -2.0 * cy, 2.0 * w, 2.0 * h))


def render_fist(anim: str, frame_idx: int, frame_count: int) -> Image.Image:
    """One frame of the RIGHT fist alone: its wrist to the left, its knuckles
    to the right, as the game holds it. The left fist is its mirror.

    The fist has a short fore arm behind it, cut where a portal's line is: in
    the fight the arm of the giant is in a portal, and this is the end of it
    that comes out. The rows `through_*` are the far side of the punch of
    phase 1: the fore arm and the fist come DOWN out of the top of the frame.
    `none` is nothing: a fist that is not there.
    """
    phase = frame_idx / max(1, frame_count)
    two_pi = 2.0 * math.pi
    svg.configure(dx=0.0, dy=0.0, ink=INK, ow=OW, colors=C)
    if anim == "none":
        return Image.new("RGBA", FIST_FRAME, (0, 0, 0, 0))
    if anim.startswith("through_"):
        depth = punch_depth("punch_" + anim[len("through_"):], phase)
        # The line is over the body by FIST_LINE_OVER; at the full depth of the
        # blow the fist is on the body's middle.
        line_y = -2.0 * FIST_LINE_OVER
        wrist_y = line_y + (PUNCH_DEPTH_DOWN + depth) * (2.0 * FIST_LINE_OVER - 56.0) / (2.0 * PUNCH_DEPTH_DOWN) if depth > -PUNCH_DEPTH_DOWN else line_y - 400.0
        body = outlined(svg.capsule((0.0, wrist_y - 400.0), (0.0, wrist_y), 40.0, 44.0), C["fur"],
                        [path(svg.capsule((18.0, wrist_y - 400.0), (18.0, wrist_y), 16.0, 20.0), C["dark"])], "clip-through")
        body += [f'<g transform="translate(0 {wrist_y + 56.0:.1f}) rotate(-90)">'] + fist("fist") + ["</g>"]
        part("through", "Through", "through", "fist", 10,
             [_cut("cut-through", ("y", line_y, False)), '<g clip-path="url(#cut-through)">'] + body + ["</g>"])
        return _raster(_fist_document(), FIST_FRAME)

    dx = dy = turn = 0.0
    extra: List[str] = []
    if anim == "rest":
        dy = 4.0 * math.sin(two_pi * phase)
        turn = 2.0 * math.sin(two_pi * phase + 0.8)
    elif anim == "fall":
        dy = 4.0 * math.sin(math.pi * phase)
        # Lines of speed over a fist that comes down.
        for i, x in enumerate((-60.0, 0.0, 52.0)):
            y0 = -96.0 - (i % 2) * 8.0
            extra.append(line([(x, y0), (x, y0 - 22.0 - 8.0 * math.sin(math.pi * phase))], "#f0e2be", 3.0))
    elif anim == "hit":
        dx = 6.0 * math.sin(two_pi * phase * 2.0) * (1.0 - phase)
        turn = -5.0 * (1.0 - phase)
    elif anim == "stuck":
        # In the floor and pulling to come out: it shakes, and grit jumps.
        dx = 5.0 * math.sin(two_pi * phase * 3.0)
        dy = 10.0
        for i, x in enumerate((-80.0, -24.0, 36.0, 88.0)):
            up = (phase * 1.7 + i * 0.27) % 1.0
            extra.append(ellipse(x + dx, 92.0 - 56.0 * up, 6.0 - 3.0 * up, 5.0 - 2.4 * up, C["dark"], INK, 1.2))
    # The fore arm behind the wrist, cut at its portal's line (drawn knuckles
    # to the left, then turned over with the fist).
    stub = outlined(svg.capsule((300.0, 0.0), (92.0, 0.0), 40.0, 44.0), C["fur"],
                    [path(svg.capsule((300.0, 18.0), (92.0, 18.0), 16.0, 20.0), C["dark"])], "clip-fore-arm")
    fore = [_cut("cut-fore-arm", ("x", FIST_STUB_LINE, True)), '<g clip-path="url(#cut-fore-arm)">'] + stub + ["</g>"]
    part("fist", "Fist", "fist", "fist", 10,
         grp(fore + fist("fist"), f"translate({dx:.2f} {dy:.2f}) rotate({turn:.2f}) scale(-1 1)") + extra)
    return _raster(_fist_document(), FIST_FRAME)


#: Where the line of a fist's own portal is behind its wrist, in design
#: units from the fist's middle (the fist drawn with its knuckles to the left).
FIST_STUB_LINE = 150.0
