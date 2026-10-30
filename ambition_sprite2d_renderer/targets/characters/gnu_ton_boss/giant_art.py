"""The giant gnu (GNU-ton's mount): its drawing, its poses and its frames.

A giant that is like a gnu and is not one, almost a centaur: a beast on four
long legs in a coat of long locks, a chest that stands up at its front to two
broad shoulders, the horns of a gnu, and a plain face whose parts make its
expression. Its back is a low HUMP from the rump to the foot of an upright,
centaur-like torso (Jon, 2026-10-25: a long slope to the shoulder moved with
the torso and looked wrong). The torso leans over the hump; the hump does not
lean with it. Jon chose the design in stills (2026-10-11);
`docs/planning/game/bosses.md` has the fight it is for.

The drawing is SVG made here (`_svg.py` is the kit) and rasterized by resvg.
A frame is a POSE: a stance (where the body's points are), an expression,
and where the head is. `pose_for` gives the pose of each row's frame, and
`render_giant` draws it into the sheet's frame.

The drawing is in DESIGN units, twice the published frame: the floor is
y=978 and x grows to the giant's front (it faces right). `to_frame` takes a
design point to a pixel of the published frame.

What the drawing shows and does not build:

* where an actor can stand has a trim on it (`stand_trim`: a gold rail with
  studs over a crimson band with gilt points) on the hump of the back, the
  level part of each horn and the top of each epaulet;
* it has no bird, and no portal: those are the game's.
"""
from __future__ import annotations

import io
import math
from typing import Dict, List, Optional, Tuple

from PIL import Image

from . import _pieces as pc
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
    bronze="#c9953f",
    bronze_dark="#7f5a1f",
    gold="#e2b64a",
    gold_light="#f6dc8a",
    gold_dark="#a67a20",
    cloth="#7a2e2e",
    cloth_dark="#4f1c1c",
    trim="#a8393a",
    trim_dark="#6a2020",
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
    # It looks back over its shoulder at what is on its back.
    "wary": _face((0.20, 0.20), slant=0.18, look=((-0.42, -0.26), (-0.42, -0.26)), pupil=(0.22, 0.22), ears=(-12, 8),
                  tilt=-6.0),
    # Its rider is down: the lids fall, their inner ends up; the ears hang.
    "grief": _face((0.46, 0.46), slant=-0.34, low=0.10, look=((0.04, 0.38), (0.04, 0.38)), pupil=(0.30, 0.30),
                   ears=(44, 44), mouth="sad", tilt=10.0),
    # And then it roars.
    "roar": _face((0.30, 0.30), slant=0.56, low=0.16, look=((0.10, 0.04), (0.10, 0.04)), pupil=(0.15, 0.15), ears=(-44, -44),
                  mouth="roar", tilt=-8.0, hot=True, flare=1.55),
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


#: Where the top of the beast goes in under the left side of the torso
#: (before a stance lifts it). The torso stands up from here and leans over
#: it; the hump ends under the torso, so a lean does not show its end.
JOIN = (844.0, 594.0)
#: The crest of the hump: the part of the way from the rump to the join it
#: is at, and how far it is over the join.
HUMP_CREST = (0.7, 6.0)
#: The points of the top line of the beast, from the rump to the join.
HUMP_POINTS = 20


def hump_top(st):
    """The top of the beast in stance ``st``, from the rump to the join: up
    from the rump to the crest (steep first, then level), and down a little
    to the join. A trim is on it: an actor stands on it."""
    lx, ly = st["lift"]
    rx, ry = st["rump"]
    jx, jy = JOIN[0] + lx, JOIN[1] + ly
    u, over = HUMP_CREST
    cx, cy = rx + (jx - rx) * u, jy - over
    out = []
    for k in range(HUMP_POINTS + 1):
        x = rx + (jx - rx) * k / HUMP_POINTS
        if x <= cx:
            y = ry + (cy - ry) * math.sin(0.5 * math.pi * (x - rx) / (cx - rx))
        else:
            y = cy + (jy - cy) * ((x - cx) / (jx - cx)) ** 2
        out.append((x, y))
    return out


def beast(st):
    """The body of the beast: one shape. Its top is the hump from the rump to
    the join (`hump_top`), and the mane comes down over the front of it."""
    lx, ly = st["lift"]
    rx, ry = st["rump"]
    jx, jy = JOIN[0] + lx, JOIN[1] + ly
    b0, b1 = st["belly"]
    top = hump_top(st)
    n = len(top) - 1
    bottom = locks_line(b1, b0, 12, 40.0)
    sil = smooth(top + [(jx + 60, jy + 16), (jx + 120, jy + 80), (b1[0] + 14, b1[1] - 120)] + bottom +
                 [(rx - 14, b0[1] - 26), (rx - 30, ry + 96), (rx - 14, ry + 26)])
    k0 = 13
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
    mane = smooth([(x, y - 30) for x, y in top[k0:]] + [(jx + 340, jy), (b1[0] + 200, b1[1] + 200), (a[0], a[1] + 200, True)] + edge)
    items = [
        # The pale of the back near the rump, and the dark of the belly.
        path(smooth([(x, y - 20) for x, y in top[:k0]] + [(x + 20, y + 60) for x, y in top[:k0]][::-1]), C["light"]),
        path(svg.poly([(b0[0] - 120, b0[1] - 40), (b1[0] + 80, b1[1] - 40), (b1[0] + 80, b1[1] + 120), (b0[0] - 120, b0[1] + 120)]),
             C["dark"]),
    ]
    # Brindle on the flank.
    for i, k in enumerate((2, 5, 8, 11)):
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

    # The trim along the top of the hump: where the trim is, you can stand.
    ridge = [(x, y - 2) for x, y in top[1:]]
    body = stand_trim(ridge, _downs(ridge), "clip-beast-trim")
    part("beast-trim", "Trim on the hump", "beast_trim", "torso", 32, body)


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
    body += epaulet_trim(name, x0, x1, top)
    part(name, name, name.replace("-", "_"), "chest", 46, body)


def epaulet_trim(name, x0, x1, top):
    """The trim on the top of an epaulet. Its top is the board's top, the line
    the game's shoulder ledge is on (`shoulder_decks_world`)."""
    n = 10
    ridge = [(x0 + 4 + (x1 - x0 - 8) * k / n, top) for k in range(n + 1)]
    return stand_trim(ridge, _downs(ridge), f"clip-{name}-trim")


#: The trim that shows where an actor can stand: how deep its rail and its
#: band are under the top line, and how far each gilt point hangs under the
#: band (design units).
TRIM_RAIL = 17.0
TRIM_BAND = 33.0
TRIM_POINT = 12.0
#: How far the trim's ink edge reaches out of its silhouette, and how thick
#: the ink of its top line is (design units): bolder than any other line on
#: him, so a surface to stand on reads at a glance.
TRIM_EDGE = 3.0
TRIM_INK = 10.0


def _downs(top):
    """The unit normal of the line ``top`` at each of its points, to the
    side under it (+y down)."""
    out = []
    n = len(top) - 1
    for i in range(n + 1):
        (ax, ay), (bx, by) = top[max(0, i - 1)], top[min(n, i + 1)]
        d = math.hypot(bx - ax, by - ay) or 1.0
        nx, ny = -(by - ay) / d, (bx - ax) / d
        out.append((nx, ny) if ny >= 0 else (-nx, -ny))
    return out


def stand_trim(top, down, cid):
    """The giant's sign for "you can stand here": the heaviest ink on him along
    the line ``top`` (the top of the surface), a gold rail with studs under it
    over a crimson band, and a gilt point
    under the band between each two points of the line. ``down`` is the unit
    normal at each point, to the side under the line. The top of its ink is
    `TRIM_OVER` over the surface the game stands a body on."""

    def at(i, depth):
        return (top[i][0] + down[i][0] * depth, top[i][1] + down[i][1] * depth)

    def mid(i, depth):
        (ax, ay), (bx, by) = at(i, depth), at(i + 1, depth)
        return ((ax + bx) * 0.5, (ay + by) * 0.5)

    n = len(top) - 1
    under = []
    for i in range(n + 1):
        under.append(at(i, TRIM_BAND))
        if i < n:
            under.append(mid(i, TRIM_BAND + TRIM_POINT) + (True,))
    sil = smooth([tuple(top[0]) + (True,)] + [tuple(p) for p in top[1:-1]] + [tuple(top[-1]) + (True,)] + under[::-1])
    rail = smooth(list(top) + [at(i, TRIM_RAIL) for i in range(n, -1, -1)], closed=True)
    shine = smooth([at(i, TRIM_INK - TRIM_EDGE) for i in range(n + 1)]
                   + [at(i, TRIM_INK - TRIM_EDGE + 2.5) for i in range(n, -1, -1)], closed=True)
    items = [path(rail, C["gold"]), path(shine, C["gold_light"]),
             line([at(i, TRIM_RAIL) for i in range(n + 1)], INK, TRIM_INK * 0.5, closed=False)]
    for i in range(n):
        x, y = mid(i, TRIM_BAND + 1.0)
        items.append(line([mid(i, TRIM_RAIL + 1.0), (x, y)], C["trim_dark"], 3.4, closed=False))
    # The top line is the heaviest ink on him: the surface itself. Its upper
    # edge stays where the outline's is, so it thickens down into the rail.
    items.append(line([at(i, TRIM_INK * 0.5 - TRIM_EDGE) for i in range(n + 1)], INK, TRIM_INK, closed=False))
    body = outlined(sil, C["trim"], items, cid, width=2 * TRIM_EDGE)
    for i in range(n):
        x, y = mid(i, TRIM_BAND + TRIM_POINT - 1.0)
        body.append(ellipse(x, y, 6.0, 6.0, C["gold"], INK, 3.0))
    for i in range(1, n, 2):
        x, y = at(i, (TRIM_RAIL - TRIM_INK * 0.25 + TRIM_INK - TRIM_EDGE) * 0.5)
        body.append(ellipse(x, y, 3.6, 3.6, C["white"], INK, 2.2))
    return body


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
    """An arm from a shoulder to its fist: the fist is the fist of the fight.
    Rigid: ``elbow`` only says the side the elbow is on (`rigid_joints`)."""
    far = shoulder[0] < 1000
    elbow, wrist = rigid_joints(shoulder, wrist, _side_of(shoulder, elbow, wrist))
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


def horn_trim(cid, pts, s, u0, u1, steps):
    """The trim on the top of a horn, from ``u0`` to ``u1`` along its spline
    (`catmull`): a place an actor can stand."""
    top, down = [], []
    for k in range(steps + 1):
        u = u0 + (u1 - u0) * k / steps
        (x, y), (dx, dy) = catmull(pts, u)
        d = math.hypot(dx, dy)
        nx, ny = s * dy / d, -s * dx / d
        r = 38.0 + (4.0 - 38.0) * u / (len(pts) - 1)
        top.append((x + nx * (r + 3), y + ny * (r + 3)))
        down.append((-nx, -ny))
    return stand_trim(top, down, cid)


def _ear(s, cid):
    """One ear (``s`` -1 left, 1 right), unturned, and the root it turns about."""
    cx, cy = HEAD

    def P(dx, dy, corner=False):
        p = (cx + dx * K, cy + dy * K)
        return p + (True,) if corner else p

    ear = smooth([P(s * 86, -40, True), P(s * 132, -62), P(s * 168, -44), P(s * 176, -22, True), P(s * 130, -14),
                  P(s * 92, -18)])
    body = outlined(ear, C["face"], [path(smooth([P(s * 104, -36), P(s * 136, -46), P(s * 160, -32), P(s * 130, -24)]),
                                          C["blaze"])], cid)
    return body, P(s * 86, -30)


def gnu_horn_body():
    """The horns of a gnu, with their trim: out to each side, down a little,
    and then up to a point. No ears, unturned."""
    cx, cy = HEAD

    def P(dx, dy):
        return (cx + dx * K, cy + dy * K)

    back = []
    for s, cid in ((-1, "clip-horn-l"), (1, "clip-horn-r")):
        pts = [P(s * 40, -104), P(s * 124, -90), P(s * 206, -66), P(s * 268, -92), P(s * 292, -170), P(s * 270, -250),
               P(s * 244, -296)]
        back += horn(cid, pts, s < 0)
        back += horn_trim(cid + "-trim", [tuple(p[:2]) for p in pts], s, 0.55, 2.5, 12)
    return back


#: How far each ear of a gnu's head is turned at rest (degrees, outward):
#: under these horns the ears have room, and they hang a little lower.
GNU_EAR_REST = 26.0


def gnu_horns(expr):
    """The horns of a gnu and its ears, as one picture (a still)."""
    e = EXPRESSIONS[expr] if isinstance(expr, str) else expr
    cx, cy = HEAD
    back = gnu_horn_body()
    for s, cid, turn in ((-1, "clip-ear-l", e["ears"][0]), (1, "clip-ear-r", e["ears"][1])):
        body, (bx, by) = _ear(s, cid)
        back += grp(body, f"rotate({s * (turn + GNU_EAR_REST)} {bx} {by})")
    return grp(back, f"rotate({e['tilt']} {cx} {cy + 120})")


def curl_horn_body():
    """The horns of the first design, greater: up and out from the brow, round,
    and in again, each one over a shoulder. Not the horns of the design now.
    No ears, unturned."""
    cx, cy = HEAD

    def P(dx, dy):
        return (cx + dx * K, cy + dy * K)

    back = []
    for s, cid in ((-1, "clip-horn-l"), (1, "clip-horn-r")):
        pts = [P(s * 46, -108), P(s * 132, -176), P(s * 232, -156), P(s * 284, -62), P(s * 262, 26), P(s * 204, 62),
               P(s * 158, 40)]
        back += horn(cid, pts, s < 0)
        back += horn_trim(cid + "-trim", [tuple(p[:2]) for p in pts], s, 0.95, 2.55, 14)
    return back


def curl_horns(expr):
    """The curled horns and the ears, as one picture (a still). The ears turn
    about their roots: level, back, or one that has dropped."""
    e = EXPRESSIONS[expr] if isinstance(expr, str) else expr
    cx, cy = HEAD
    back = curl_horn_body()
    for s, cid, turn in ((-1, "clip-ear-l", e["ears"][0]), (1, "clip-ear-r", e["ears"][1])):
        body, (bx, by) = _ear(s, cid)
        back += grp(body, f"rotate({s * turn} {bx} {by})")
    return grp(back, f"rotate({e['tilt']} {cx} {cy + 120})")


def head_parts(expr, horns="gnu"):
    """The head, as parts: ``(name, z, body, map)``. Each body is drawn
    unturned; its map turns it in the head's frame (the tilt of the face about
    the jaw, an ear about its root). The neck does not tilt."""
    e = EXPRESSIONS[expr] if isinstance(expr, str) else expr
    cx, cy = HEAD
    tilt = pc.R(e["tilt"], cx, cy + 120)
    out = []

    def P(dx, dy, corner=False):
        p = (cx + dx * K, cy + dy * K)
        return p + (True,) if corner else p

    out.append(("horns", 56, gnu_horn_body() if horns == "gnu" else curl_horn_body(), tilt))
    rest = GNU_EAR_REST if horns == "gnu" else 0.0
    for s, cid, turn in ((-1, "clip-ear-l", e["ears"][0]), (1, "clip-ear-r", e["ears"][1])):
        body, root = _ear(s, cid)
        out.append((f"ear-{'left' if s < 0 else 'right'}", 56, body, pc.chain(tilt, pc.R(s * (turn + rest), *root))))

    neck = smooth([P(-78, 30), P(96, 30), P(118, 220), P(-96, 220)])
    out.append(("neck", 40, outlined(neck, C["mane"], [], None), pc.IDENT))

    beard = smooth([P(-20, 120, True), P(110, 150, True), P(118, 220), P(100, 290), P(80, 334, True), P(62, 290),
                    P(42, 360, True), P(24, 296), P(0, 330, True), P(-22, 240)])
    body = outlined(beard, C["mane"], strands(cx - 4, cx + 96, cy + 160, cy + 290, 4, C["mane_light"], lean=-6.0),
                    "clip-beard")
    body += outlined(smooth([P(30, 352, True), P(54, 352, True), P(56, 372), P(42, 410, True), P(28, 372)]), C["mane"], [],
                     None)
    body += [path(svg.poly([P(24, 344), P(60, 344), P(60, 358), P(24, 358)]), C["bronze"], INK, 2.2),
             line([P(28, 351), P(56, 351)], C["bronze_dark"], 2.0)]
    out.append(("beard", 58, body, tilt))

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
    elif mouth == "sad":
        body += [line([P(110, 186), P(66, 186), P(32, 178), P(20, 196)], INK, 3.6)]
    elif mouth == "roar":
        # The jaw drops: a dark mouth, its teeth, its tongue.
        jaw = smooth([P(122, 182, True), P(70, 186), P(22, 162, True), P(20, 230), P(56, 286), P(112, 292), P(134, 250)])
        body += outlined(jaw, "#3a1210", [path(smooth([P(36, 262), P(78, 240), P(118, 262), P(100, 290), P(56, 288)]), "#b8524a"),
                                          path(svg.poly([P(104, 186), P(114, 186), P(109, 206)]), C["white"], INK, 1.6),
                                          path(svg.poly([P(72, 188), P(82, 188), P(77, 206)]), C["white"], INK, 1.6),
                                          path(svg.poly([P(42, 176), P(52, 180), P(46, 196)]), C["white"], INK, 1.6),
                                          path(svg.poly([P(104, 290), P(114, 288), P(109, 270)]), C["white"], INK, 1.6),
                                          path(svg.poly([P(64, 286), P(74, 288), P(69, 270)]), C["white"], INK, 1.6)],
                         "clip-roar")
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
    # The track `head`: the head of the body for the game (its landmark, where
    # a helmet sits).
    out.append(("head", 60, body, tilt))
    return out


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
#: An arm in its line: the upper arm down and out from its root, and the fore
#: arm level and out, so that it goes through its line SQUARE to it, about
#: half of its length past the elbow (the elbow and its hair stay out of the
#: line).
_OUT_L = (ARM_ROOT_L, (747.0, 643.0), (604.0, 643.0))
_OUT_R = (ARM_ROOT_R, (1337.0, 643.0), (1480.0, 643.0))


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


#: Each blow. `arm`: the limb (``right``, ``left``, or ``leg``: the near fore
#: leg).
#:
#: An ARM is two rigid bones (`ARM_UPPER`, `ARM_FORE`) with a joint at the
#: shoulder, the elbow and the wrist; it never bends between them and never
#: stretches (Jon, 2026-10-24: "I really don't like the bendy arm"). Only the
#: forearm and the fist go through the near line of a blow, square to it; the
#: upper arm (shoulder to elbow, and the hair at the elbow) stays on the
#: giant's side of the line's plane in every frame
#: (`tests/test_gnu_ton_giant_blows.py`). So the line is DERIVED from the
#: arm (`_derive_lines`): `way` is the way the forearm goes through it,
#: `elbow` the angle between the upper arm and `way` (and `side`, the side of
#: `way` the elbow is on: +1 is the side of `way` turned +90 degrees) when the
#: wrist is in the middle of its way through. The line is square to `way`, in
#: front of the wrist there.
#:
#: The leg keeps a line of its own (`line`: the middle of its near line and
#: its normal).
#:
#: `back`: how far the wrist (the fetlock of the leg) is on the near side of
#: the line when the blow is cocked, at the end of its windup. `hitch`: how
#: much of `back` is the last pull before the blow goes. `deep`: how far past
#: the line the wrist is at the full blow. `out`: how far on the near side it
#: is when the limb has come back out. `past`: how far the middle of the fist
#: (of the hoof) is past the wrist (the fetlock), along the limb's end.
#: `strike`, `hold`, `recover`: the lengths of its rows, in seconds (each
#: row's frames times its frame time in `sprite_generator`; the game types
#: them again). `open_from`: the part of the windup from which the arm is
#: out of the place of the line's opening, so the game opens the pair from
#: there (the hanging arm is where a hammer's line is); `close_at`: the part
#: of the recover by which the pair is closed (the arm goes home after it,
#: `HOME_FROM`).
#:
#: Each arm has a blow down, one across and one up, each with a body of its
#: own: the HAMMER rears back and slams its forearm down with the whole body;
#: the JAB is cocked by the jaw and drives out; the left HOOK is wound across
#: the chest and thrown out behind; the UPPERCUT crouches and rises.
MIDDLE_X = 1042.0
_ARM_DEEP = 60.0
BLOWS = {
    # Down and forward, the elbow up in front of the right shoulder: its line
    # is by the shoulder, so a body that comes up out of it is by the back.
    "hammer": dict(arm="right", way=(0.643, 0.766), elbow=110.0, side=-1, back=260.0, hitch=40.0, deep=_ARM_DEEP,
                   out=140.0, past=56.0, strike=0.24, hold=0.36, recover=0.5, open_from=0.3, close_at=0.82),
    # Out in front, a little down, the elbow under the shoulder.
    "jab": dict(arm="right", way=(0.966, 0.259), elbow=80.0, side=1, back=210.0, hitch=18.0, deep=_ARM_DEEP,
                out=140.0, past=56.0, strike=0.2, hold=0.24, recover=0.32, open_from=0.3, close_at=0.82),
    # Up in front of the chest, the elbow out in front.
    "upper": dict(arm="right", way=(0.0, -1.0), elbow=90.0, side=1, back=230.0, hitch=40.0, deep=_ARM_DEEP,
                  out=140.0, past=56.0, strike=0.26, hold=0.24, recover=0.4, open_from=0.05, close_at=0.82),
    # The left shoulder is at the middle of the giant's body, so a clean line
    # of its arm is over the body (a line in its body would take the giant
    # through its own portal): its blows go up. The hammer goes up from the
    # left shoulder, and comes down on the player out of the far line.
    "left_hammer": dict(arm="left", way=(-0.174, -0.985), elbow=60.0, side=-1, back=260.0, hitch=40.0, deep=_ARM_DEEP,
                        out=140.0, past=56.0, strike=0.24, hold=0.36, recover=0.5, open_from=0.26, close_at=0.82),
    # Out behind and up, over the slope of the back: wound across the chest.
    # Each left line is out past the horns, so its light does not cross the
    # face.
    "left_hook": dict(arm="left", way=(-0.342, -0.94), elbow=40.0, side=-1, back=210.0, hitch=20.0, deep=_ARM_DEEP,
                      out=140.0, past=56.0, strike=0.2, hold=0.24, recover=0.36, open_from=0.05, close_at=0.82),
    # Up, the elbow out to the left.
    "left_upper": dict(arm="left", way=(0.0, -1.0), elbow=90.0, side=-1, back=230.0, hitch=40.0, deep=_ARM_DEEP,
                       out=140.0, past=56.0, strike=0.26, hold=0.24, recover=0.4, open_from=0.05, close_at=0.82),
    # Forward with the near fore leg, low: a kick. The fetlock is the end of
    # the leg; the hoof is past it.
    "kick": dict(arm="leg", line=((1290.0, 800.0), (-1.0, 0.0)), back=50.0, hitch=10.0, deep=100.0, out=50.0, past=24.0,
                 strike=0.3, hold=0.24, recover=0.42, open_from=0.0, close_at=1.0),
}
#: How far the end of a limb gives back toward its line in the row `*_hold`.
HOLD_GIVE = 14.0
#: The part of the row `*_strike` at which the blow is full (it is still after).
STRIKE_FULL = 0.8
#: The part of the row `*_recover` at which the limb is out of its line.
RECOVER_OUT = 0.45
#: The parts of a row `*_windup`: at `SET_AT` the blow is set on its line
#: (`back` less its `hitch`) and trembles; from `HITCH_AT` it draws back the
#: last of the way, and is cocked at the end of the row.
SET_AT = 0.66
HITCH_AT = 0.84
#: Kept for the readers of the old name: the windup is set (cocked but for
#: its hitch) here.
COCKED_AT = SET_AT


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


def _mirror_point(p):
    return (2 * MIDDLE_X - p[0], p[1])


#: The right arm's wrist at rest (final), and its elbow's side.
_A_HANG = _final((1282.0, 800.0))
_L_HANG = _mirror_point(_A_HANG)

#: Where each blow's wrist goes on its way to the windup's set place, as a
#: part of the windup: (until, wrist from the shoulder, final). The set
#: place itself is on the line's axis (`_axis_point`).
_WIND = {
    "hammer": [(0.25, (70.0, -40.0)), (0.5, (90.0, -200.0))],
    "jab": [(0.3, (-10.0, 60.0)), (0.5, (-40.0, -10.0))],
    "upper": [(0.3, (-40.0, 200.0))],
    "left_hammer": [(0.3, (-60.0, 180.0))],
    "left_hook": [(0.3, (120.0, 160.0)), (0.5, (260.0, 20.0))],
    "left_upper": [(0.3, (40.0, 200.0))],
}
#: The part of the row ``*_recover`` the arm holds out of its line, in front
#: of it, while the pair closes (`close_at` of each blow); then it goes home.
HOME_FROM = 0.8

#: How far before the line the wrist is when the forearm is square to it
#: and stays so: the forearm and the fist go through square. More than the
#: forearm's half width at the wrist (44): the end of the forearm reaches the
#: line square.
SQUARE_BEFORE = 60.0
#: The fist turns at its wrist to the way of the blow before it reaches the
#: line: square from the wrist this far before the line (its front is 126
#: past the wrist).
FIST_SQUARE_BEFORE = 160.0


def rigid_joints(shoulder, wrist, side):
    """The elbow of a rigid arm from ``shoulder`` to ``wrist`` (two bones,
    `ARM_UPPER` and `ARM_FORE`), on ``side`` of the line from the shoulder
    to the wrist (+1: the side turned +90 degrees). A wrist out of reach is
    brought in to it. Returns (elbow, wrist)."""
    sx, sy = shoulder
    dx, dy = wrist[0] - sx, wrist[1] - sy
    dist = math.hypot(dx, dy) or 1e-6
    ux, uy = dx / dist, dy / dist
    reach = ARM_UPPER + ARM_FORE - 0.01
    least = abs(ARM_UPPER - ARM_FORE) + 0.01
    dist = min(reach, max(least, dist))
    wrist = (sx + ux * dist, sy + uy * dist)
    along = (ARM_UPPER ** 2 - ARM_FORE ** 2 + dist ** 2) / (2.0 * dist)
    h = math.sqrt(max(0.0, ARM_UPPER ** 2 - along ** 2))
    nx, ny = -uy, ux
    return (sx + ux * along + nx * h * side, sy + uy * along + ny * h * side), wrist


def _side_of(shoulder, elbow, wrist):
    cross = (wrist[0] - shoulder[0]) * (elbow[1] - shoulder[1]) - (wrist[1] - shoulder[1]) * (elbow[0] - shoulder[0])
    return 1 if cross >= 0 else -1


def _shoulder(blow, part, phase):
    """The shoulder of the arm of ``blow`` (final) in a row of it: its root,
    moved by the body's lift and lean."""
    drop, lean, _head = _body_at(blow, part, phase)
    root = _lean_point(_final(ARM_ROOT_L if BLOWS[blow]["arm"] == "left" else ARM_ROOT_R), lean)
    return (root[0], root[1] + drop)


def _strike_phase_at(blow, depth):
    """The part of the row ``*_strike`` at which its wrist is ``depth`` past
    the line."""
    b = BLOWS[blow]
    u = (depth + b["back"]) / (b["deep"] + b["back"])
    return STRIKE_FULL * max(0.0, min(1.0, u)) ** (1.0 / 3.0)


def _derive_lines():
    """Each arm blow's near line, from its arm: when the wrist is in the
    middle of its way through, the forearm is along `way` and the upper arm
    at `elbow` degrees from it. The line is square to `way`."""
    for blow, b in BLOWS.items():
        if b["arm"] == "leg":
            continue
        dx, dy = b["way"]
        n = (-dy, dx)
        mid = (b["deep"] - SQUARE_BEFORE) * 0.5
        sx, sy = _shoulder(blow, "strike", _strike_phase_at(blow, mid))
        t = math.radians(b["elbow"])
        ax, ay = math.cos(t) * dx + math.sin(t) * b["side"] * n[0], math.cos(t) * dy + math.sin(t) * b["side"] * n[1]
        ex, ey = sx + ARM_UPPER * ax, sy + ARM_UPPER * ay
        wx, wy = ex + ARM_FORE * dx, ey + ARM_FORE * dy
        b["line"] = ((round(wx - mid * dx, 2), round(wy - mid * dy, 2)), (-dx, -dy))
        b["bend"] = _side_of((sx, sy), (ex, ey), (wx, wy))


def _axis_point(blow, depth, lateral=0.0):
    """The point ``depth`` past the line of ``blow`` and ``lateral`` to the
    side of its middle (+: the side of the way turned +90 degrees)."""
    (cx, cy), (nx, ny) = BLOWS[blow]["line"]
    dx, dy = -nx, -ny
    return (cx + dx * depth - dy * lateral, cy + dy * depth + dx * lateral)


def _square_arm(blow, shoulder, depth):
    """The arm through its line: the forearm along the way, the wrist
    ``depth`` past the line and as far to the side of its middle as the
    rigid upper arm puts it. Returns (elbow, wrist, lateral)."""
    b = BLOWS[blow]
    (cx, cy), (nx, ny) = b["line"]
    dx, dy = -nx, -ny
    px, py = shoulder[0] - cx, shoulder[1] - cy
    along = px * dx + py * dy - depth + ARM_FORE
    across = px * -dy + py * dx
    h = math.sqrt(max(0.0, ARM_UPPER ** 2 - along ** 2))
    # Of the two places of the elbow, the one that keeps the wrist nearer
    # the middle of the line.
    lateral = min((across - h, across + h), key=abs)
    wrist = _axis_point(blow, depth, lateral)
    elbow = (wrist[0] - dx * ARM_FORE, wrist[1] - dy * ARM_FORE)
    return elbow, wrist, lateral


def _ik_arm(blow, shoulder, wrist):
    elbow, wrist = rigid_joints(shoulder, wrist, BLOWS[blow]["bend"])
    return elbow, wrist


def _tremble_point(p, phase, amount=1.0):
    return (p[0] + 3.0 * amount * math.sin(phase * 97.0), p[1] + 2.0 * amount * math.cos(phase * 71.0))


def _lerp_dir(a, b, u):
    x, y = a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u
    d = math.hypot(x, y) or 1.0
    return (x / d, y / d)


def _unit(a, b):
    d = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
    return ((b[0] - a[0]) / d, (b[1] - a[1]) / d)


def _blow_arm(blow, part, phase):
    """The striking arm in a row of a blow: (shoulder, elbow, wrist, the way
    the fist goes from the wrist). Rigid in every frame; square through its
    line."""
    b = BLOWS[blow]
    way = (-b["line"][1][0], -b["line"][1][1])
    shoulder = _shoulder(blow, part, phase)
    hang = _L_HANG if b["arm"] == "left" else _A_HANG
    # Where the arm enters its square part: its lateral place there.
    entry = _square_arm(blow, _shoulder(blow, "strike", _strike_phase_at(blow, -SQUARE_BEFORE)), -SQUARE_BEFORE)[2]

    def off_line(depth):
        elbow, wrist = _ik_arm(blow, shoulder, _axis_point(blow, depth, entry))
        return elbow, wrist

    def fist_way(depth, forearm):
        u = (depth + b["back"]) / max(1.0, b["back"] - FIST_SQUARE_BEFORE)
        return _lerp_dir(forearm, way, _ease(max(0.0, min(1.0, u))))

    if part == "windup":
        held = _axis_point(blow, -(b["back"] - b["hitch"]), entry)
        cocked = _axis_point(blow, -b["back"], entry)
        if phase <= SET_AT:
            keys = [(0.0, hang)] + [(until, (shoulder[0] + ox, shoulder[1] + oy)) for until, (ox, oy) in _WIND[blow]]
            wrist = _between(keys + [(SET_AT, held)], phase)
        elif phase <= HITCH_AT:
            wrist = _tremble_point(held, phase)
        else:
            wrist = _tremble_point(_between([(HITCH_AT, held), (1.0, cocked)], phase), phase, 0.4)
        elbow, wrist = _ik_arm(blow, shoulder, wrist)
        return shoulder, elbow, wrist, _unit(elbow, wrist)
    depth = blow_wrist_depth(blow, part, phase)
    if depth is not None and depth >= -SQUARE_BEFORE:
        elbow, wrist, _ = _square_arm(blow, shoulder, depth)
        return shoulder, elbow, wrist, way
    if depth is not None:
        elbow, wrist = off_line(depth)
        return shoulder, elbow, wrist, fist_way(depth, _unit(elbow, wrist))
    # Out of its line, it holds in front of it while the pair closes; then
    # it goes home.
    out = _axis_point(blow, -b["out"], entry)
    elbow, wrist = _ik_arm(blow, shoulder, _between([(RECOVER_OUT, out), (HOME_FROM, out), (1.0, hang)], phase))
    forearm = _unit(elbow, wrist)
    # The fist stays square until it goes home.
    home = _ease(max(0.0, (phase - HOME_FROM) / (1.0 - HOME_FROM)))
    return shoulder, elbow, wrist, _lerp_dir(fist_way(-b["out"], forearm), forearm, home)


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


def _blow_leg(part, phase):
    """The near fore leg in a row of the kick: hip, knee, fetlock."""
    b = BLOWS["kick"]
    cocked = _leg_at(-b["back"])
    held = _leg_at(-(b["back"] - b["hitch"]))
    if part == "windup":
        if phase <= SET_AT:
            return _between([(0.0, _L_REST), (0.4, _L_LIFT), (SET_AT, held)], phase)
        hip, knee, (fx, fy) = _between([(HITCH_AT, held), (1.0, cocked)], phase)
        return (hip, knee, (fx + 3.0 * math.sin(phase * 97.0), fy + 2.0 * math.cos(phase * 71.0)))
    depth = blow_wrist_depth("kick", part, phase)
    if depth is not None:
        return _leg_at(depth)
    return _between([(RECOVER_OUT, _leg_at(-b["out"])), (0.72, _L_LIFT), (1.0, _L_REST)], phase)


#: How the body moves in each part of a blow: (until, (lift down, lean in
#: degrees about the seat, the head's offset)). A lean that is more than 0 is
#: toward the giant's front. Each blow has a body of its own, so it is read
#: from across the room: the hammer rears up and slams down with all of it,
#: the jab draws back and lunges, the hook twists, the uppercut crouches and
#: rises.
_REST_BODY = (0.0, 0.0, (0.0, 0.0))
_BODY = {
    "hammer": dict(
        windup=[(0.0, _REST_BODY), (0.4, (-14.0, -3.0, (-6.0, -12.0))), (SET_AT, (-30.0, -6.0, (-12.0, -22.0))),
                (HITCH_AT, (-32.0, -6.5, (-12.0, -24.0))), (1.0, (-40.0, -8.0, (-16.0, -30.0)))],
        strike=[(0.0, (-40.0, -8.0, (-16.0, -30.0))), (0.8, (28.0, 8.0, (22.0, 36.0)))],
        recover=[(0.0, (28.0, 8.0, (22.0, 36.0))), (0.5, (12.0, 3.0, (8.0, 14.0))), (1.0, _REST_BODY)]),
    "jab": dict(
        windup=[(0.0, _REST_BODY), (SET_AT, (8.0, -6.0, (-18.0, 6.0))), (1.0, (10.0, -8.0, (-24.0, 6.0)))],
        strike=[(0.0, (10.0, -8.0, (-24.0, 6.0))), (0.8, (4.0, 8.0, (28.0, 4.0)))],
        recover=[(0.0, (4.0, 8.0, (28.0, 4.0))), (1.0, _REST_BODY)]),
    "upper": dict(
        windup=[(0.0, _REST_BODY), (SET_AT, (26.0, 5.0, (12.0, 30.0))), (1.0, (34.0, 6.0, (14.0, 38.0)))],
        strike=[(0.0, (34.0, 6.0, (14.0, 38.0))), (0.8, (-30.0, -6.0, (-6.0, -26.0)))],
        recover=[(0.0, (-30.0, -6.0, (-6.0, -26.0))), (1.0, _REST_BODY)]),
    # The left hammer leans the other way: the right side of the body braces
    # while the left arm is up, and the slam turns the body to the left.
    "left_hammer": dict(
        windup=[(0.0, _REST_BODY), (0.4, (-12.0, 2.0, (-14.0, -10.0))), (SET_AT, (-28.0, 4.0, (-24.0, -20.0))),
                (HITCH_AT, (-30.0, 4.5, (-26.0, -22.0))), (1.0, (-38.0, 6.0, (-30.0, -28.0)))],
        strike=[(0.0, (-38.0, 6.0, (-30.0, -28.0))), (0.8, (26.0, -7.0, (-30.0, 34.0)))],
        recover=[(0.0, (26.0, -7.0, (-30.0, 34.0))), (0.5, (10.0, -3.0, (-12.0, 12.0))), (1.0, _REST_BODY)]),
    # The hook twists toward the front while it winds across the chest, and
    # turns hard the other way as it is thrown out behind.
    "left_hook": dict(
        windup=[(0.0, _REST_BODY), (0.5, (6.0, 6.0, (18.0, 4.0))), (SET_AT, (4.0, 3.0, (6.0, 2.0))),
                (1.0, (8.0, 1.0, (0.0, 4.0)))],
        strike=[(0.0, (8.0, 1.0, (0.0, 4.0))), (0.8, (2.0, -9.0, (-34.0, 0.0)))],
        recover=[(0.0, (2.0, -9.0, (-34.0, 0.0))), (1.0, _REST_BODY)]),
    "left_upper": dict(
        windup=[(0.0, _REST_BODY), (SET_AT, (26.0, -3.0, (-14.0, 30.0))), (1.0, (34.0, -4.0, (-16.0, 38.0)))],
        strike=[(0.0, (34.0, -4.0, (-16.0, 38.0))), (0.8, (-30.0, 5.0, (8.0, -26.0)))],
        recover=[(0.0, (-30.0, 5.0, (8.0, -26.0))), (1.0, _REST_BODY)]),
    "kick": dict(
        windup=[(0.0, _REST_BODY), (SET_AT, (-12.0, -4.0, (-10.0, -8.0))), (1.0, (-16.0, -5.0, (-12.0, -10.0)))],
        strike=[(0.0, (-16.0, -5.0, (-12.0, -10.0))), (0.8, (6.0, 3.0, (14.0, 10.0)))],
        recover=[(0.0, (6.0, 3.0, (14.0, 10.0))), (1.0, _REST_BODY)]),
}

#: The arm that does not strike (before the lift, as `_whole_arms` has it): at
#: rest, braced forward, guarding up, swung back and up. Drawn for the left
#: arm; the right arm's is its mirror.
_LEFT = dict(
    hang=_HANG_L,
    brace=(ARM_ROOT_L, (760.0, 650.0), (850.0, 760.0)),
    guard=(ARM_ROOT_L, (900.0, 600.0), (960.0, 470.0)),
    back=(ARM_ROOT_L, (740.0, 640.0), (680.0, 740.0)),
    up=(ARM_ROOT_L, (740.0, 520.0), (700.0, 400.0)),
)
_RIGHT = {name: tuple((2 * MIDDLE_X - x, y) for x, y in pts) for name, pts in _LEFT.items()}
#: What the other arm does in each part of each blow: (until, pose name).
_OTHER_KEYS = {
    "hammer": dict(windup=[(0.0, "hang"), (SET_AT, "guard")], strike=[(0.0, "guard"), (0.8, "back")],
                   recover=[(0.0, "back"), (1.0, "hang")]),
    "jab": dict(windup=[(0.0, "hang"), (SET_AT, "guard")], strike=[(0.0, "guard"), (0.8, "back")],
                recover=[(0.0, "back"), (1.0, "hang")]),
    "upper": dict(windup=[(0.0, "hang"), (SET_AT, "brace")], strike=[(0.0, "brace"), (0.8, "up")],
                  recover=[(0.0, "up"), (1.0, "hang")]),
    "left_hammer": dict(windup=[(0.0, "hang"), (SET_AT, "brace")], strike=[(0.0, "brace"), (0.8, "back")],
                        recover=[(0.0, "back"), (1.0, "hang")]),
    "left_hook": dict(windup=[(0.0, "hang"), (SET_AT, "back")], strike=[(0.0, "back"), (0.8, "guard")],
                      recover=[(0.0, "guard"), (1.0, "hang")]),
    "left_upper": dict(windup=[(0.0, "hang"), (SET_AT, "brace")], strike=[(0.0, "brace"), (0.8, "up")],
                       recover=[(0.0, "up"), (1.0, "hang")]),
    "kick": dict(windup=[(0.0, "hang"), (SET_AT, "back")], strike=[(0.0, "back"), (0.8, "brace")],
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


#: The parts of a blow's rows, in order.
BLOW_PARTS = ("windup", "strike", "hold", "recover")


def blow_parts(anim: str):
    """``(blow, part, armed)`` of a row of a blow, or ``None``: ``hammer_*``,
    ``jab_*``, ``upper_*``, ``left_hammer_*``, ``left_hook_*``,
    ``left_upper_*``; ``kick_*`` with the arms in their lines and
    ``armed_kick_*`` with the arms on."""
    armed = True
    if anim.startswith("armed_kick_"):
        anim = anim[len("armed_"):]
    elif anim.startswith("kick_"):
        armed = False
    for blow in BLOWS:
        prefix = blow + "_"
        if anim.startswith(prefix):
            part = anim[len(prefix):]
            if part in BLOW_PARTS:
                return blow, part, armed
    return None


def _body_at(blow, part, phase):
    """(drop, lean, head) of the body in a row of a blow."""
    body = _BODY[blow]
    if part == "hold":
        # The blow lands: the body jolts and comes back (its recoil). A hammer
        # lands with all of the body.
        drop, lean, head = body["strike"][-1][1]
        jolt = math.sin(math.pi * min(1.0, phase * 2.5)) * (1.0 - phase)
        heavy = 1.6 if blow.endswith("hammer") else 1.0
        return (drop + 10.0 * heavy * jolt, lean - 2.5 * jolt * (1 if lean >= 0 else -1),
                (head[0] - 8.0 * jolt, head[1] + 8.0 * heavy * jolt))
    return _keys_at(body[part], phase)


def _blow_pose(pose, blow, part, armed, phase):
    """Fill ``pose`` (from `pose_for`) for a row of a blow."""
    sloped = STANCES["sloped"]
    b = BLOWS[blow]
    drop, lean, head = _body_at(blow, part, phase)
    s = dict(sloped)
    s["lift"] = (sloped["lift"][0], sloped["lift"][1] + drop)
    pose["stance"] = s
    pose["lean"] = lean
    pose["head"] = head
    hitching = part == "windup" and phase > HITCH_AT
    name = "angry" if part != "windup" or phase > SET_AT * 0.6 else "serious"
    tremble = 2.0 * math.sin(phase * 61.0) if part == "windup" and phase > SET_AT else 0.0
    expr = dict(EXPRESSIONS[name], tilt=EXPRESSIONS[name]["tilt"] + lean * 0.8 + tremble)
    if hitching:
        # The last pull: the nostrils flare and the eyes go wide on the line.
        expr.update(flare=1.45, lids=(0.12, 0.12))
    pose["expr"] = expr
    other_part = "strike" if part == "hold" else part
    other_phase = 1.0 if part == "hold" else phase
    other_table = _RIGHT if b["arm"] == "left" else _LEFT
    other = _named_at(_OTHER_KEYS[blow][other_part], other_table, other_phase)
    other_spec = dict(kind="limb", name="arm-right" if b["arm"] == "left" else "arm-left", pts=other)
    if blow == "kick":
        pose["kick"] = _blow_leg(part, phase)
        if armed:
            right = mix(_HANG_R, _RIGHT_UP, _ease(min(1.0, phase / 0.5)) if part == "windup" else
                        (1.0 if part != "recover" else 1.0 - _ease(phase)))
            pose["arms"] = [other_spec, dict(kind="limb", name="arm-right", pts=right)]
        else:
            pose["arms"] = _clamped_arms(1.0)
        return pose
    # The arm of a blow is FIXED to the giant (its fist is on its line), so
    # it is drawn outside the body's lift and lean: its shoulder is moved by
    # them in `_blow_arm`.
    shoulder, elbow, wrist, fist_way = _blow_arm(blow, part, phase)
    # A jab is cocked by the jaw, a hook across the chest: their arm is in
    # front of the head.
    z = 62 if blow in ("jab", "left_hook") else 40
    name = "arm-left" if b["arm"] == "left" else "arm-right"
    pose["arms"] = [other_spec, dict(kind="rigid", name=name, fixed=True, z=z, pts=(shoulder, elbow, wrist), fist_way=fist_way)]
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

#: Where the left side of the torso covers the hump at rest (final): the walk
#: line ends there, and a body goes up from it to the shoulders.
TORSO_EDGE_X = 824.0
#: How far over the top line the top of the trim is drawn (its edge and ink).
TRIM_OVER = 3.5


#: The standing surfaces of the giant, by the name the sheet publishes them
#: under (`surface:<name>:a` / `:b`): the top of each epaulet. The game's
#: drawn ledges (`mount.drawn_ledges` of `npc_giant_gnu`) name them.
SURFACES = {"shoulder_left": SHOULDER_L, "shoulder_right": SHOULDER_R}


def surfaces(pose: dict) -> dict:
    """Where each standing surface of ``pose`` is, in pixels of the published
    frame: ``{name: (a, b)}``, the left end first. The epaulets lean and lift
    with the torso (`_body_map`), and so do their tops. ``hump`` is the two
    ends of the walk line of the hump (`hump_line_world`) where the barrel is
    drawn: the game carries the whole line by the move of its ends."""
    body_map = _body_map(pose)
    out = {}
    for name, (x0, x1, top) in SURFACES.items():
        a, b = (to_frame(pc.apply(body_map, p)) for p in ((x0, top), (x1, top)))
        out[name] = (a, b) if a[0] <= b[0] else (b, a)
    barrel = _barrel_placed(pose["stance"]).full()
    out["hump"] = tuple(to_frame(pc.apply(barrel, p)) for p in _hump_ends())
    return out


def _hump_ends():
    """The two ends of the walk line of the hump at rest, in design units:
    the rump's end and the torso's edge (`hump_line_world`)."""
    top = hump_top(_SLOPED)
    (ax, ay), (bx, by) = top[0], top[1]
    i = min(len(top) - 2, max(0, int((TORSO_EDGE_X - top[0][0]) / (top[1][0] - top[0][0]))))
    (cx, cy), (dx, dy) = top[i], top[i + 1]
    return ((ax, ay - TRIM_OVER), (TORSO_EDGE_X, cy + (dy - cy) * (TORSO_EDGE_X - cx) / (dx - cx) - TRIM_OVER))


def surface_anchors(found: dict, frame_size) -> dict:
    """The anchors of a frame for ``found`` (``{name: (a, b)}`` in pixels of a
    frame of ``frame_size``): ``surface:<name>:a`` and ``surface:<name>:b``,
    as parts of the frame (0 to 1), as the seams are (`limb_seam_anchors`)."""
    w, h = frame_size
    out = {}
    for name, (a, b) in found.items():
        out[f"surface:{name}:a"] = {"x": round(a[0] / w, 5), "y": round(a[1] / h, 5)}
        out[f"surface:{name}:b"] = {"x": round(b[0] / w, 5), "y": round(b[1] / h, 5)}
    return out


def hump_line_world(points: int = 11):
    """The walk line of the hump at rest, from the rump to the torso's edge,
    in world units about the middle of the giant's body (+y down): the
    numbers the game types (`mount.slope` of `npc_giant_gnu`)."""
    top = hump_top(_SLOPED)
    cx = BODY_BBOX[0] + BODY_BBOX[2] * 0.5
    cy = BODY_BBOX[1] + BODY_BBOX[3] * 0.5
    x0 = top[0][0]
    out = []
    for k in range(points):
        x = x0 + (TORSO_EDGE_X - x0) * k / (points - 1)
        i = min(len(top) - 2, max(0, int((x - x0) / (top[1][0] - x0))))
        (ax, ay), (bx, by) = top[i], top[i + 1]
        y = ay + (by - ay) * (x - ax) / (bx - ax) - TRIM_OVER
        px, py = to_frame((x, y))
        out.append((round((px - cx) * WORLD_PER_PIXEL, 1), round((py - cy) * WORLD_PER_PIXEL, 1)))
    return out


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
    """How far past its line the wrist of the hammer is in a row `hammer_*`
    (less than 0: over it). A fist that is not on its way through is far over
    it. For the fist's own rows `through_*`."""
    part = anim[len("hammer_"):]
    depth = blow_wrist_depth("hammer", part, phase) if part != "windup" else None
    return depth if depth is not None else -9000.0


#: How far past its line the wrist is at the end of the hammer. The fist's own
#: sheet draws the far side of the punch from this.
PUNCH_DEPTH_DOWN = BLOWS["hammer"]["deep"]


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
#: The giant in the air (in space): its legs drawn up under it.
FLOAT = dict(STANCES["sloped"], lift=(-8.0, -186.0),
             hind=((452, 740), (356, 800), (420, 846)),
             hind_far=((548, 734), (456, 792), (518, 840)),
             fore=(((1098, 720), (1196, 770), (1208, 840)), ((960, 716), (1056, 768), (1068, 834))),
             tail=((346, 612), 48.0))
#: The arms that hold something in front of the chest (its rider, fallen).
_CRADLE = ((ARM_ROOT_L, (900.0, 660.0), (1064.0, 704.0)), (ARM_ROOT_R, (1300.0, 650.0), (1154.0, 708.0)))


def _far_hind(st):
    """The far hind leg of a stance: its own, or the near one moved to where
    the far one stands."""
    if "hind_far" in st:
        return st["hind_far"]
    hip, mid, end = st["hind"]
    return ((hip[0] + 96, hip[1] - 6), (mid[0] + 96, mid[1] - 4), (end[0] + 100, end[1]))


#: A stride of the walk: how far a hoof goes back while it stands (design
#: units), how high it lifts, and the part of a step it stands. The game moves
#: the giant at the speed this makes (`STRIDE_SPEED`).
STRIDE = 140.0
STRIDE_LIFT = 46.0
STRIDE_STAND = 0.7
#: The walk's frames and their length (`sprite_generator.ANIMATIONS`).
WALK_FRAMES, WALK_MS = 12, 80
#: World units a second the walk carries the giant: a hoof that stands goes
#: back STRIDE over the part of the cycle it stands (design units are half a
#: frame pixel, and a frame pixel is `WORLD_PER_PIXEL` world units).
STRIDE_SPEED = STRIDE * 0.5 * 1.3 / (STRIDE_STAND * WALK_FRAMES * WALK_MS / 1000.0)


def _stride_leg(leg, phase, lag, back=1.0):
    """One leg of the walk at ``phase`` (0..1), ``lag`` of a cycle behind the
    first. ``back`` -1 walks backward. The hip stays; the hoof stands and goes
    back, then lifts and comes forward; the knee goes with it, half as far."""
    hip, mid, end = leg
    u = (phase - lag) % 1.0
    if u < STRIDE_STAND:
        dx, lift = STRIDE * (0.5 - u / STRIDE_STAND), 0.0
    else:
        v = (u - STRIDE_STAND) / (1.0 - STRIDE_STAND)
        dx, lift = STRIDE * (v - 0.5), STRIDE_LIFT * math.sin(math.pi * v)
    dx *= back
    return (hip, (mid[0] + dx * 0.5 + lift * 0.2, mid[1] - lift * 0.55), (end[0] + dx, end[1] - lift))


def _walk_stance(st, phase, back=1.0):
    """A stance walking: each leg a quarter of a step after the one before it
    (near hind, near fore, far hind, far fore), the body bobbing on each step."""
    two_pi = 2.0 * math.pi
    out = dict(st)
    out["hind"] = _stride_leg(st["hind"], phase, 0.0, back)
    out["hind_far"] = _stride_leg(_far_hind(st), phase, 0.5, back)
    out["fore"] = (_stride_leg(st["fore"][0], phase, 0.25, back), _stride_leg(st["fore"][1], phase, 0.75, back))
    out["lift"] = (st["lift"][0], st["lift"][1] + 5.0 * math.sin(2.0 * two_pi * phase))
    out["rump"] = (st["rump"][0], st["rump"][1] + 3.0 * math.sin(2.0 * two_pi * phase + 0.8))
    (root, swing) = st["tail"]
    out["tail"] = (root, swing + 9.0 * math.sin(two_pi * phase))
    return out


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
    elif anim in ("walk", "walk_back"):
        # It strides; `walk_back` is the same steps the other way (it backs
        # off and keeps its face to the player). Its head nods with the steps.
        back = -1.0 if anim == "walk_back" else 1.0
        pose["stance"] = _walk_stance(sloped, phase, back)
        pose["head"] = (0.0, 6.0 * math.sin(4.0 * math.pi * phase + 0.5))
        pose["expr"] = face("ordered", 2.0 * math.sin(two_pi * phase))
        if armed:
            pose["arms"] = _whole_arms(sway=10.0 * math.sin(two_pi * phase) * back)
            return pose
    elif anim == "look_back":
        # Something is on its back: it turns its head to see it, and holds.
        turn = _ease(min(1.0, phase / 0.4))
        pose["stance"] = breathe(sloped, 0.5)
        pose["head"] = (-26.0 * turn, -14.0 * turn)
        pose["expr"] = face("wary", -4.0 * turn)
    elif anim == "roar":
        # It rears and roars: up over 0.3 of the row, held, and down.
        up = _ease(min(1.0, phase / 0.3)) * (1.0 - _ease((phase - 0.8) / 0.2))
        shake = math.sin(2.0 * two_pi * 3.0 * phase) * (1.0 if 0.3 <= phase < 0.85 else 0.0)
        pose["stance"] = mix_stance(sloped, STANCES["reared"], 0.7 * up)
        pose["head"] = (4.0 * shake, -30.0 * up + 3.0 * shake)
        pose["expr"] = face("roar" if up > 0.3 else "angry", 2.0 * shake)
    elif anim == "grieve":
        # It holds its fallen rider to its chest, the head low over him.
        low = _ease(min(1.0, phase / 0.5))
        s = breathe(sloped, 0.4)
        s["lift"] = (s["lift"][0], s["lift"][1] + 18.0 * low)
        pose["stance"] = s
        pose["head"] = (16.0 * low, 70.0 * low)
        pose["expr"] = face("grief")
        pose["arms"] = [dict(kind="limb", name="arm-left", pts=mix(_HANG_L, _CRADLE[0], low)),
                        dict(kind="limb", name="arm-right", pts=mix(_HANG_R, _CRADLE[1], low))]
        return pose
    elif anim == "float":
        # In the air: the legs drawn up and paddling, slowly.
        st = dict(FLOAT)
        paddle = math.sin(two_pi * phase)
        st["fore"] = tuple(((h, (m[0] + 10.0 * paddle * k, m[1]), (e[0] + 22.0 * paddle * k, e[1] - 6.0 * paddle * k))
                            for (h, m, e), k in zip(FLOAT["fore"], (1.0, -1.0))))
        st["lift"] = (FLOAT["lift"][0], FLOAT["lift"][1] + 6.0 * math.sin(two_pi * phase + 0.7))
        pose["stance"] = st
        pose["head"] = (0.0, 4.0 * math.sin(two_pi * phase))
        pose["expr"] = face("ordered", 2.0 * paddle)
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
    n0 = len(svg.PARTS)
    arm(name, *spec["pts"])
    body = svg.PARTS.pop(n0)[6]
    if spec.get("cut"):
        body = [_cut(f"cut-{name}", spec["cut"]), f'<g clip-path="url(#cut-{name})">'] + body + ["</g>"]
    part(name, name, name.replace("-", "_"), name.replace("-", "_"), spec.get("z", 40), body)


# ---------------------------------------------------------------------------
# The giant from PIECES (`_pieces.py`). Each piece is drawn once in its own
# place and a frame puts each one with a rigid map (and a stretch along a
# bone): the legs and the arms are bones, the barrel of the beast turns about
# its rump, the chest, the head and the arms ride the stance's lift and lean,
# the face is one piece for each expression and turns by its tilt. The sheet
# is composed from the pieces, so its part flipbook keeps each piece once.


def _harvest(draw, *args, **kwargs):
    """``(name, z, body)`` of each part the kit function ``draw`` adds."""
    n0 = len(svg.PARTS)
    draw(*args, **kwargs)
    new = svg.PARTS[n0:]
    del svg.PARTS[n0:]
    return [(name, z, tuple(body)) for _pid, _label, name, _bone, z, _extra, body in new]


def _rest_length(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


#: Each leg's two bones at rest (the stance `sloped`): the length a bone is
#: drawn at, so a leg at rest is drawn unstretched.
_SLOPED = STANCES["sloped"]
#: How far under the fetlock a hind hoof's sole is at rest.
_HIND_FLOOR = FLOOR - _SLOPED["hind"][2][1]
LEG_LENGTHS = {
    "hind": (_rest_length(*_SLOPED["hind"][:2]), _rest_length(*_SLOPED["hind"][1:])),
    "fore-near": (_rest_length(*_SLOPED["fore"][0][:2]), _rest_length(*_SLOPED["fore"][0][1:])),
    "fore-far": (_rest_length(*_SLOPED["fore"][1][:2]), _rest_length(*_SLOPED["fore"][1][1:])),
}


def _leg_bone(far, upper, length):
    skin, shade = (C["far"], C["far_dark"]) if far else (C["fur"], C["dark"])
    if upper:
        return pc.Piece(tuple(outlined(svg.capsule((0.0, 0.0), (0.0, length), 54.0, 31.0), skin,
                                       [path(svg.capsule((-24.0, 0.0), (-14.0, length), 22.0, 12.0), shade)],
                                       f"clip-leg-u-{far:d}-{length:.1f}")),
                        reach=length + 120.0)
    return pc.Piece(tuple(outlined(svg.capsule((0.0, 0.0), (0.0, length), 28.0, 25.0), skin,
                                   [path(svg.capsule((-13.0, 0.0), (-12.0, length), 10.0, 9.0), shade)],
                                   f"clip-leg-l-{far:d}-{length:.1f}")),
                    reach=length + 120.0)


def _knee(far):
    skin = C["far"] if far else C["fur"]
    return pc.Piece((ellipse(0.0, 0.0, 33, 31, skin, INK, 2 * OW), ellipse(-7.0, -8.0, 13, 10, C["far"] if far else C["light"])),
                    reach=80.0)


def _foot(far, floor):
    """The hoof and its cuff of hair, its fetlock at (0, 0) and its sole
    ``floor`` under it."""
    hair = C["far_dark"] if far else C["mane"]
    hoof = smooth([(-40, floor - 40, True), (46, floor - 40, True), (60, floor, True), (-50, floor, True)])
    body = outlined(hoof, C["hoof"], [path(svg.poly([(-50, floor - 38), (58, floor - 38), (58, floor - 27), (-50, floor - 27)]),
                                           C["far_dark"] if far else C["hoof_light"]),
                                      line([(10, floor - 38), (14, floor)], INK, 2.6)], f"clip-hoof-{far:d}-{floor:.1f}")
    cuff = smooth([(44, floor - 84, True), (-40, floor - 84, True)] + locks(-52, 58, floor - 40, floor - 20, 5))
    body += outlined(cuff, hair, strands(-36, 42, floor - 76, floor - 40, 4, C["far"] if far else C["mane_light"]),
                     f"clip-cuff-{far:d}-{floor:.1f}")
    return pc.Piece(tuple(body), reach=200.0)


def leg_pieces(scene, name, kind, hip, mid, end, far, z, floor=None, turn=0.0):
    """A long leg as pieces: its two bones, its knee, and its hoof with a cuff
    of long hair. ``floor``: how far under the fetlock the sole is (the floor
    for a leg that stands). ``turn`` turns the hoof about the fetlock
    (degrees): 0 is a hoof under it, -90 a hoof whose sole faces the front."""
    upper, lower = LEG_LENGTHS[kind]
    floor = FLOOR - end[1] if floor is None else floor
    m, k = pc.bone(hip, mid, upper)
    scene.add(f"{name}-upper", z, _leg_bone(far, True, upper), m, k)
    m, k = pc.bone(mid, end, lower)
    scene.add(f"{name}-lower", z, _leg_bone(far, False, lower), m, k)
    scene.add(f"{name}-knee", z, _knee(far), pc.T(*mid))
    scene.add(f"{name}-foot", z, _foot(far, round(floor, 1)), pc.at_point(end, turn))


#: The lengths an arm's two bones are drawn at: the arm that hangs at rest.
ARM_UPPER = _rest_length((826.0, 506.0), (792.0, 660.0))
ARM_FORE = _rest_length((792.0, 660.0), (822.0, 800.0))


def _arm_upper():
    return pc.Piece(tuple(outlined(svg.capsule((0.0, 0.0), (0.0, ARM_UPPER), 46.0, 36.0), C["fur"],
                                   [path(svg.capsule((16.0, 0.0), (14.0, ARM_UPPER), 20.0, 14.0), C["dark"])], "clip-arm-u")),
                    reach=ARM_UPPER + 110.0)


def _arm_fore():
    return pc.Piece(tuple(outlined(svg.capsule((0.0, 0.0), (0.0, ARM_FORE), 38.0, 44.0), C["fur"],
                                   [path(svg.capsule((14.0, 0.0), (16.0, ARM_FORE), 14.0, 20.0), C["dark"]),
                                    path(svg.capsule((-14.0, 10.0), (-16.0, ARM_FORE - 20.0), 7.0, 9.0), C["light"])],
                                   "clip-arm-f")),
                    reach=ARM_FORE + 110.0)


def _tuft():
    """Long hair at an elbow, about the elbow."""
    tuft = smooth([(-30, -14, True), (30, -14, True), (26, 22), (10, 50, True), (0, 26), (-12, 56, True), (-26, 20)])
    return pc.Piece(tuple(outlined(tuft, C["mane"], [], None)), reach=100.0)


def _fist_piece(flip=False):
    """A fist about its middle, its knuckles to the left (``flip``: turned over)."""
    body = fist("fist")
    if flip:
        body = grp(body, "scale(1 -1)")
    return pc.Piece(tuple(body), reach=140.0)


def arm_pieces(scene, name, shoulder, elbow, wrist, outer, z=40, fist_way=None):
    """An arm from a shoulder to its fist, as pieces (its bones, the hair at
    its elbow, the fist of the fight), moved by ``outer``. The arm is RIGID:
    ``elbow`` only says which side the elbow is on, and the bones keep their
    lengths (a wrist out of reach is brought in). ``fist_way``: the way the
    fist goes from the wrist (it turns at the wrist); the forearm's way by
    default."""
    far = shoulder[0] < 1000
    elbow, wrist = rigid_joints(shoulder, wrist, _side_of(shoulder, elbow, wrist))
    m, _k = pc.bone(shoulder, elbow, ARM_UPPER)
    scene.add(f"{name}-upper", z, _arm_upper(), pc.chain(outer, m))
    m, _k = pc.bone(elbow, wrist, ARM_FORE)
    scene.add(f"{name}-fore", z, _arm_fore(), pc.chain(outer, m))
    scene.add(f"{name}-tuft", z, _tuft(), pc.chain(outer, pc.T(*elbow)))
    ux, uy = fist_way or _unit(elbow, wrist)
    turn = math.degrees(math.atan2(-uy, -ux))
    scene.add(f"{name}-fist", z, _fist_piece(far), pc.chain(outer, pc.at_point((wrist[0] + ux * 56, wrist[1] + uy * 56), turn)))


#: The middle of the giant's body (design units): the pivot of the pieces
#: drawn where they are.
_MIDDLE = (1042.0, 600.0)


def _cut_arm_piece(spec):
    """An arm cut at its portal's line: one piece as it is drawn."""
    n0 = len(svg.PARTS)
    arm(spec["name"], *spec["pts"])
    body = svg.PARTS.pop(n0)[6]
    cid = f"cut-{spec['name']}"
    return pc.Piece(tuple([_cut(cid, spec["cut"]), f'<g clip-path="url(#{cid})">'] + body + ["</g>"]), origin=_MIDDLE,
                    reach=900.0)


#: Where the barrel of the beast turns: its rump, and the join under the
#: torso (of the stance it is drawn in). The join follows the lift, not the
#: lean: the torso leans over the hump.
def _barrel_ends(st):
    lx, ly = st["lift"]
    return st["rump"], (JOIN[0] + lx, JOIN[1] + ly)


_BARREL_REST = _barrel_ends(_SLOPED)
#: A stretch of the barrel less than this from 1 is not drawn (2 % of its
#: length is about 4 px of the frame, under the chest).
BARREL_SNAP = 0.02
_BARREL_AXIS = math.degrees(math.atan2(_BARREL_REST[1][1] - _BARREL_REST[0][1], _BARREL_REST[1][0] - _BARREL_REST[0][0]))


def _barrel_placed(st, name="beast", z=30.0, body=()):
    """The barrel of the beast (drawn once at rest, in `_SLOPED`) placed in
    stance ``st``: turned about its rump to the slope of the stance, and
    stretched along it."""
    rump, top = _barrel_ends(st)
    (r0, t0) = _BARREL_REST
    turn = math.degrees(math.atan2(top[1] - rump[1], top[0] - rump[0])) - _BARREL_AXIS
    stretch = _rest_length(rump, top) / _rest_length(r0, t0)
    barrel_map = pc.chain(pc.T(rump[0] - r0[0], rump[1] - r0[1]), pc.R(turn, *r0))
    # Near its rest length the barrel is painted as drawn, not turned to its
    # axis. Turned, its quad reaches far past the frame (187 px in `death`),
    # and the game then cannot read the giant as one image: no impostor cell
    # holds it, so a portal does not draw it through and a hit does not flash.
    axis = _BARREL_AXIS
    if abs(stretch - 1.0) < BARREL_SNAP:
        axis, stretch = 90.0, 1.0
    return pc.Placed(name, z, pc.Piece(tuple(body), origin=r0, axis=axis, reach=1150.0), barrel_map, stretch)


def _body_map(pose: dict):
    """The map of the chest, the head and the arms: lifted to the stance, and
    leaned about the seat (the scholar stays on it)."""
    lx, ly = pose["stance"]["lift"]
    sx, sy = (SHOULDER_R[0] + SHOULDER_R[1]) * 0.5, SHOULDER_R[2]
    return pc.chain(pc.T(lx, ly), pc.R(pose.get("lean", 0.0), sx, sy))


def scene_for(pose: dict, *, arms: bool = False, horns: str = "gnu") -> pc.Scene:
    """The giant in ``pose`` as placed pieces. ``arms`` draws an arm from each
    shoulder to its fist for a pose that says none."""
    st = pose["stance"]
    hx, hy = pose["head"]
    svg.configure(dx=0.0, dy=0.0, ink=INK, ow=OW, colors=C)
    scene = pc.Scene()
    hip, mid, end = st["hind"]
    # A hind hoof stands its sole at the floor at rest; a stance that lifts it
    # (a step, the air) lifts its sole with it.
    walking = "hind_far" in st
    leg_pieces(scene, "far-hind", "hind", *_far_hind(st), True, 10, _HIND_FLOOR if walking else None)
    leg_pieces(scene, "near-hind", "hind", hip, mid, end, False, 28, _HIND_FLOOR if walking else None)
    leg_pieces(scene, "far-fore", "fore-far", *st["fore"][1], True, 10, st["fore_floors"][1])
    if pose.get("kick"):
        hip, knee, fet = pose["kick"]
        turn = math.degrees(math.atan2(fet[1] - knee[1], fet[0] - knee[0])) - 90.0
        leg_pieces(scene, "near-fore", "fore-near", hip, knee, fet, False, 28, 44.0, turn=turn)
    else:
        leg_pieces(scene, "near-fore", "fore-near", *st["fore"][0], False, 28, st["fore_floors"][0])
    # The tail turns about its root.
    (tx, ty), swing = st["tail"]
    tail_map = pc.chain(pc.T(tx - 352, ty - 716), pc.R(swing, 352, 716))
    for name, z, body in _harvest(tail):
        scene.add(name, z, pc.Piece(body, origin=(352.0, 716.0), reach=400.0), tail_map)
    for name, z, body in _harvest(beast, _SLOPED):
        scene.items.append(_barrel_placed(st, name, z, body))
    # The chest, the head and the arms are drawn in one place and lifted to the
    # stance, and leaned about the seat (the scholar stays on it).
    body_map = _body_map(pose)
    for name, z, body in _harvest(chest) + _harvest(epaulet, "epaulet-left", SHOULDER_L, SHOULDER_L[0]) + \
            _harvest(epaulet, "epaulet-right", SHOULDER_R, SHOULDER_R[1]):
        scene.add(name, z, pc.Piece(body, origin=_MIDDLE, reach=700.0), body_map)
    drawn = pose.get("arms") or (_whole_arms(pts=st["arms"]) if arms else [])
    for spec in drawn:
        if spec.get("fixed"):
            continue
        if spec.get("cut"):
            scene.add(spec["name"], spec.get("z", 40), _cut_arm_piece(spec), body_map)
        else:
            arm_pieces(scene, spec["name"], *spec["pts"], body_map, spec.get("z", 40))
    head_map = pc.chain(body_map, pc.T(hx, hy))
    for name, z, body, local in head_parts(pose["expr"], horns):
        scene.add(name, z, pc.Piece(tuple(body), reach=700.0 if name == "horns" else 400.0, origin=HEAD), pc.chain(head_map, local))
    # The arm of a blow is fixed to the giant: its fist is on its portal's line.
    for spec in drawn:
        if spec.get("fixed"):
            arm_pieces(scene, spec["name"], *spec["pts"], pc.IDENT, spec.get("z", 40), spec.get("fist_way"))
    if pose.get("dust", 0.0) > 0.0:
        fx, _fy = st["fore"][0][2]
        scene.add("dust", 90, pc.Piece(tuple(_dust((fx, FLOOR), pose["dust"])), origin=(fx, FLOOR), reach=400.0))
    for placed in scene.items:
        placed.name = limb_track(placed.name)
    return scene


# ---------------------------------------------------------------------------
# The seams. A limb that is cut at a portal's line ends at the line, and the
# game draws the line there: at the middle of the cut, along it, and as wide
# as the limb is there (its outline included). The sheets publish the two ends
# of each cut as anchors of each frame (`seam:<slot>:a`, `seam:<slot>:b`, as
# parts of the frame: `limb_seam_anchors`), so the line is on the limb that is
# drawn and not where a constant says it is.


def band_seam(a, b, r0, r1, cut):
    """Where the line of ``cut`` (``("x" or "y", where, keep)``) goes across
    the band from ``a`` to ``b``, a capsule of radius ``r0`` at ``a`` and
    ``r1`` at ``b``: the two ends of the cut, on the line, the outline
    included. ``None`` when the line does not cross the band between its
    ends."""
    axis, where = cut[0], cut[1]
    i = 0 if axis == "x" else 1
    da, db = a[i] - where, b[i] - where
    if da == db or da * db > 0.0:
        return None
    t = da / (da - db)
    p = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
    # A band that goes across the line at a slant is cut longer than it is
    # wide: by its width over the cosine of the slant.
    across = abs(b[i] - a[i]) / math.hypot(b[0] - a[0], b[1] - a[1])
    half = (r0 + (r1 - r0) * t + OW * 0.5) / max(across, 0.2)
    if axis == "x":
        return (p[0], p[1] - half), (p[0], p[1] + half)
    return (p[0] - half, p[1]), (p[0] + half, p[1])


def limb_seams(pose: dict) -> dict:
    """Where each arm of ``pose`` that is cut at a portal's line is cut, in
    pixels of the published frame: ``{slot: (end, end)}`` (`LIMB_SLOTS`).

    The middle of the cut is where the arm's rigid bones (`rigid_joints`) go
    across the line; its two ends are MEASURED on the arm as it is drawn (its
    piece alone, rastered at the design's scale), a little into the side that
    is kept. So the hair of an elbow or a fist that is at the line is in the
    cut, and the line is as wide as what it cuts."""
    out = {}
    body_map = _body_map(pose)
    linear = body_map[:4] + (0.0, 0.0)
    for spec in pose.get("arms") or []:
        cut = spec.get("cut")
        if not cut or cut[0] == "hole":
            continue
        shoulder, elbow, wrist = spec["pts"]
        elbow, wrist = rigid_joints(shoulder, wrist, _side_of(shoulder, elbow, wrist))
        seam = band_seam(shoulder, elbow, 46.0, 36.0, cut) or band_seam(elbow, wrist, 38.0, 44.0, cut)
        if not seam:
            continue
        axis, _where, low = cut
        along = pc.apply(linear, (0.0, 1.0) if axis == "x" else (1.0, 0.0))
        side = -1.0 if low else 1.0
        inward = pc.apply(linear, (side, 0.0) if axis == "x" else (0.0, side))
        middle = pc.apply(body_map, ((seam[0][0] + seam[1][0]) * 0.5, (seam[0][1] + seam[1][1]) * 0.5))
        scene = pc.Scene()
        scene.add(spec["name"], 40, _cut_arm_piece(spec), body_map)
        drawn = _drawn_across(pc.compose(scene, CANVAS, CANVAS_ORIGIN), middle, along, inward)
        if drawn:
            ends = [(middle[0] + along[0] * k, middle[1] + along[1] * k) for k in drawn]
            out[LIMB_SLOTS[spec["name"]]] = tuple(to_frame(p) for p in ends)
    return out


#: How far into its kept side a cut is measured, in design units.
SEAM_INSIDE = 2.0


def _drawn_across(canvas, middle, along, inward, reach=200.0):
    """The run of ``canvas`` (the design at one pixel a unit) that is drawn
    on the line through ``middle`` along ``along``, ``SEAM_INSIDE`` toward
    ``inward``: where it starts and ends, in design units along the line from
    ``middle``. ``None`` when nothing is drawn at ``middle``."""
    alpha = canvas.getchannel("A")
    ox, oy = CANVAS_ORIGIN
    steps = int(reach * 2)

    def drawn(k):
        u = k * 0.5
        x = middle[0] + along[0] * u + inward[0] * SEAM_INSIDE + ox
        y = middle[1] + along[1] * u + inward[1] * SEAM_INSIDE + oy
        inside = 0 <= x < canvas.width and 0 <= y < canvas.height
        return inside and alpha.getpixel((int(x), int(y))) >= 128

    if not drawn(0):
        return None
    lo = 0
    while lo > -steps and drawn(lo - 1):
        lo -= 1
    hi = 0
    while hi < steps and drawn(hi + 1):
        hi += 1
    return lo * 0.5, (hi + 1) * 0.5


def limb_seam_anchors(seams: dict, frame_size) -> dict:
    """The anchors of a frame for ``seams`` (``{slot: (end, end)}`` in pixels
    of a frame of ``frame_size``): ``seam:<slot>:a`` and ``seam:<slot>:b``, as
    parts of the frame (0 to 1), so a sheet of any quality has the same."""
    w, h = frame_size
    out = {}
    for slot, (a, b) in seams.items():
        out[f"seam:{slot}:a"] = {"x": round(a[0] / w, 5), "y": round(a[1] / h, 5)}
        out[f"seam:{slot}:b"] = {"x": round(b[0] / w, 5), "y": round(b[1] / h, 5)}
    return out


#: The limbs of the giant that are bodies of their own in the game, by the
#: name of their pieces: an arm, and the near fore leg (the kick). The game
#: takes a limb's parts (and only them) through a portal pair by these names
#: (`limb:<slot>`, `rigged::is_limb_track`).
LIMB_SLOTS = {"arm-right": "hand_right", "arm-left": "hand_left", "near-fore": "hoof_right"}


def limb_track(name: str) -> str:
    """The track of a piece: ``limb:<slot>:<part>`` for a piece of a limb that
    is a body of its own in the game, else its name."""
    for prefix, slot in LIMB_SLOTS.items():
        if name == prefix:
            return f"limb:{slot}"
        if name.startswith(prefix + "-"):
            return f"limb:{slot}:{name[len(prefix) + 1:]}"
    return name


#: The canvas the frame is composed on: the design, at one pixel a unit (twice
#: the published frame), and the canvas pixel of the design's (0, 0).
CANVAS = (2 * FRAME[0], 2 * FRAME[1])
CANVAS_ORIGIN = (2.0 * OFFSET[0], 2.0 * OFFSET[1])


def giant_svg(pose: dict, *, arms: bool = False, horns: str = "gnu", view=None) -> str:
    """The giant in ``pose`` as one SVG (its pieces, placed). ``view`` is
    (x, y, w, h) in design units; the default is the published frame."""
    if view is None:
        view = (-CANVAS_ORIGIN[0], -CANVAS_ORIGIN[1], float(CANVAS[0]), float(CANVAS[1]))
    return pc.svg_of(scene_for(pose, arms=arms, horns=horns), view)


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
    """One frame of the giant's body (no fists, no scholar), at ``FRAME``:
    its pieces composed at twice the frame and brought down (``rigdoc``'s
    seams, which a part flipbook records)."""
    from ....authoring import rigdoc

    pose = pose_for(anim, frame_idx / max(1, frame_count))
    canvas = pc.compose(scene_for(pose), CANVAS, CANVAS_ORIGIN)
    return rigdoc.downsampled_canvas(canvas, FRAME)


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
    svg.configure(dx=0.0, dy=0.0, ink=INK, ow=OW, colors=C)
    if anim == "none":
        return Image.new("RGBA", FIST_FRAME, (0, 0, 0, 0))
    if anim.startswith("through_"):
        line_y, wrist_y = _through_wrist(anim, phase)
        body = outlined(svg.capsule((0.0, wrist_y - 400.0), (0.0, wrist_y), *_FIST_STUB_RADII), C["fur"],
                        [path(svg.capsule((18.0, wrist_y - 400.0), (18.0, wrist_y), 16.0, 20.0), C["dark"])], "clip-through")
        body += [f'<g transform="translate(0 {wrist_y + 56.0:.1f}) rotate(-90)">'] + fist("fist") + ["</g>"]
        part("through", "Through", "through", "fist", 10,
             [_cut("cut-through", ("y", line_y, False)), '<g clip-path="url(#cut-through)">'] + body + ["</g>"])
        return _raster(_fist_document(), FIST_FRAME)

    dx, dy, turn = _fist_motion(anim, phase)
    extra: List[str] = []
    if anim == "fall":
        # Lines of speed over a fist that comes down.
        for i, x in enumerate((-60.0, 0.0, 52.0)):
            y0 = -96.0 - (i % 2) * 8.0
            extra.append(line([(x, y0), (x, y0 - 22.0 - 8.0 * math.sin(math.pi * phase))], "#f0e2be", 3.0))
    elif anim == "stuck":
        # In the floor and pulling to come out: grit jumps.
        for i, x in enumerate((-80.0, -24.0, 36.0, 88.0)):
            up = (phase * 1.7 + i * 0.27) % 1.0
            extra.append(ellipse(x + dx, 92.0 - 56.0 * up, 6.0 - 3.0 * up, 5.0 - 2.4 * up, C["dark"], INK, 1.2))
    # The fore arm behind the wrist, cut at its portal's line (drawn knuckles
    # to the left, then turned over with the fist).
    (a, b), (r0, r1) = _FIST_STUB, _FIST_STUB_RADII
    stub = outlined(svg.capsule(a, b, r0, r1), C["fur"],
                    [path(svg.capsule((a[0], 18.0), (b[0], 18.0), 16.0, 20.0), C["dark"])], "clip-fore-arm")
    fore = [_cut("cut-fore-arm", _FIST_STUB_CUT), '<g clip-path="url(#cut-fore-arm)">'] + stub + ["</g>"]
    part("fist", "Fist", "fist", "fist", 10,
         grp(fore + fist("fist"), f"translate({dx:.2f} {dy:.2f}) rotate({turn:.2f}) scale(-1 1)") + extra)
    return _raster(_fist_document(), FIST_FRAME)


#: Where the line of a fist's own portal is behind its wrist, in design
#: units from the fist's middle (the fist drawn with its knuckles to the left).
FIST_STUB_LINE = 150.0
#: The fore arm behind a lone fist (drawn with its knuckles to the left): from
#: its far end to its wrist, its radius at each, and its cut at its line.
_FIST_STUB = ((300.0, 0.0), (92.0, 0.0))
_FIST_STUB_RADII = (40.0, 44.0)
_FIST_STUB_CUT = ("x", FIST_STUB_LINE, True)


def _fist_motion(anim: str, phase: float) -> Tuple[float, float, float]:
    """How a lone fist of row ``anim`` is moved at ``phase``: its shift (x, y)
    and its turn in degrees, in design units about its middle."""
    two_pi = 2.0 * math.pi
    if anim == "rest":
        return 0.0, 4.0 * math.sin(two_pi * phase), 2.0 * math.sin(two_pi * phase + 0.8)
    if anim == "fall":
        return 0.0, 4.0 * math.sin(math.pi * phase), 0.0
    if anim == "hit":
        return 6.0 * math.sin(two_pi * phase * 2.0) * (1.0 - phase), 0.0, -5.0 * (1.0 - phase)
    if anim == "stuck":
        # In the floor and pulling to come out: it shakes.
        return 5.0 * math.sin(two_pi * phase * 3.0), 10.0, 0.0
    return 0.0, 0.0, 0.0


def _through_wrist(anim: str, phase: float) -> Tuple[float, float]:
    """The row ``through_*`` at ``phase``: where its line is (design y), and
    where the wrist is under it. The line is over the body by
    FIST_LINE_OVER; at the full depth of the blow the fist is on the body's
    middle."""
    depth = punch_depth("hammer_" + anim[len("through_"):], phase)
    line_y = -2.0 * FIST_LINE_OVER
    if depth <= -PUNCH_DEPTH_DOWN:
        return line_y, line_y - 400.0
    return line_y, line_y + (PUNCH_DEPTH_DOWN + depth) * (2.0 * FIST_LINE_OVER - 56.0) / (2.0 * PUNCH_DEPTH_DOWN)


def fist_seams(anim: str, frame_idx: int, frame_count: int) -> dict:
    """Where the fore arm of a lone fist of row ``anim`` is cut by its line, in
    pixels of the fist's frame: ``{"self": (end, end)}``, the two ends of the
    cut. The game draws the far line of the arm there (`limb_seams`). Empty
    when no arm is in the line."""
    phase = frame_idx / max(1, frame_count)
    cx, cy = FIST_BBOX[0] + FIST_BBOX[2] * 0.5, FIST_BBOX[1] + FIST_BBOX[3] * 0.5
    frame = lambda p: (p[0] * 0.5 + cx, p[1] * 0.5 + cy)  # noqa: E731
    if anim == "none":
        return {}
    if anim.startswith("through_"):
        line_y, wrist_y = _through_wrist(anim, phase)
        seam = band_seam((0.0, wrist_y - 400.0), (0.0, wrist_y), *_FIST_STUB_RADII, ("y", line_y, False))
        return {"self": tuple(frame(p) for p in seam)} if seam else {}
    dx, dy, turn = _fist_motion(anim, phase)
    seam = band_seam(*_FIST_STUB, *_FIST_STUB_RADII, _FIST_STUB_CUT)
    # As the fist's group is moved: mirrored, turned, then shifted.
    m = pc.chain(pc.T(dx, dy), pc.R(turn), (-1.0, 0.0, 0.0, 1.0, 0.0, 0.0))
    return {"self": tuple(frame(pc.apply(m, p)) for p in seam)}


# The near line of each arm blow comes from its arm (`_derive_lines`): after
# every number it reads is defined.
_derive_lines()
