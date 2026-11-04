"""The King Cobra of the History dimension: the great snake of the forests of Angkor.

The king cobra (Ophiophagus hannah) is the longest venomous snake in the
world. It lives in the forests and the paddy fields of India and of
Southeast Asia, and it eats other snakes. It is olive-brown, with pale
cross-bands on its back and a pale yellow throat; its tail is darker. Its
head is large and round, with large scales on top. When it is alarmed it
lifts the front third of its body high off the ground and spreads its
hood. The hood of the king cobra is long and narrow, not round like the
hood of other cobras. The people of Angkor carved the naga, a great snake
with a spread hood, on the walls and the bridges of their temples.

It slithers on the ground with its head low. When it sees you it rears up
and spreads its hood (the notice row). Its windup draws its head back and
it sways; its strike throws the head forward and down with the mouth open,
and the mouth shuts at the end. A hit makes it pull its head back. At its
death it falls out of its rear and lies flat, and it fades.

The frame is 128 by 128 px: the body box is 48 by 48 world units, and the
cobra faces right.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Sequence, Tuple

from . import _art_cast_kit as K
from . import _history_africa_kit as H

TARGET_NAME = "king_cobra"
FRAME_SIZE = (128, 128)
ROWS = K.ENEMY_ROWS
#: Nothing is drawn nearer the edge of the frame than this.
MARGIN = 6.0
GROUND = 120.0

ACTOR_METADATA = K.enemy_metadata(
    TARGET_NAME, "King Cobra", "Serpentine", "Standard", "Medium", "Walk", ["snake", "cobra", "hood", "strike"],
    "The king cobra of the History dimension's room of Angkor: a long olive-brown snake with pale cross-bands, a large "
    "round head and a long narrow hood. It slithers low on the ground. When it sees you it rears up high and spreads "
    "its hood, draws its head back, and strikes forward and down with its mouth open.",
)
ACTOR_METADATA["tags"] = ["enemy", "history", "angkor"]

HIDE = (112, 100, 58, 255)
HIDE_SHADE = (80, 70, 40, 255)
HIDE_LIGHT = (148, 134, 84, 255)
TAIL = (64, 56, 36, 255)
BAND = (214, 204, 150, 255)
BELLY = (226, 208, 146, 255)
THROAT_BAR = (92, 78, 44, 255)
MOUTH = (204, 120, 116, 255)
FANG = (246, 240, 220, 255)
TONGUE = (40, 30, 32, 255)
EYE = (40, 28, 18, 255)
DUST = (196, 176, 140, 255)

#: The width of the body at its thickest, in px.
BODY_W = 12.0
#: The scale of the head. The head of a king cobra is large.
HEAD = 1.2

Point = Tuple[float, float]

# The poses of the spine: points from the tip of the tail to the back of the
# head. Each pose has the same number of points, so that a row can go from
# one pose to the next. The last number is the angle of the head (degrees,
# down is plus).
FLAT_ON_GROUND = ([(12.0, 114.0), (21.0, 113.5), (29.0, 113.5), (39.0, 113.5), (49.0, 113.5), (59.0, 113.5), (67.0, 113.5), (74.0, 113.0),
                   (80.0, 111.5), (85.0, 109.5), (89.0, 107.5), (92.0, 106.5)], -4.0)
REARED = ([(14.0, 114.5), (25.0, 114.0), (36.0, 114.0), (46.0, 113.5), (55.0, 112.0), (62.0, 107.0), (65.0, 97.0), (64.0, 84.0), (61.0, 70.0),
           (61.0, 56.0), (64.0, 45.0), (70.0, 38.0)], 6.0)
STRIKE = ([(14.0, 114.5), (25.0, 114.0), (36.0, 114.0), (46.0, 113.5), (55.0, 112.0), (63.0, 108.0), (70.0, 102.0), (77.0, 96.0), (84.0, 91.0),
           (90.0, 88.0), (95.0, 86.5), (100.0, 86.0)], 18.0)
RECOIL = ([(14.0, 114.5), (25.0, 114.0), (36.0, 114.0), (46.0, 113.5), (53.0, 112.0), (57.0, 106.0), (57.0, 96.0), (53.0, 84.0), (50.0, 72.0),
           (50.0, 60.0), (53.0, 51.0), (58.0, 46.0)], -24.0)
DEAD = ([(11.0, 114.5), (21.0, 114.5), (31.0, 114.5), (41.0, 114.5), (50.0, 114.5), (59.0, 114.5), (67.0, 114.5), (74.0, 114.5), (80.0, 114.5),
         (85.0, 114.5), (89.0, 114.8), (92.0, 115.0)], 4.0)


def _blend(a, b, k: float):
    """The pose `k` of the way from pose `a` to pose `b`."""
    pts = [(xa + (xb - xa) * k, ya + (yb - ya) * k) for (xa, ya), (xb, yb) in zip(a[0], b[0])]
    return pts, a[1] + (b[1] - a[1]) * k


def _smooth(u: float) -> float:
    u = max(0.0, min(1.0, u))
    return u * u * (3.0 - 2.0 * u)


def _spine(ctrl: Sequence[Point], step: float = 1.0) -> List[Point]:
    """A smooth line through the points `ctrl`, with its points at equal steps
    along it."""
    c = [ctrl[0]] + list(ctrl) + [ctrl[-1]]
    dense: List[Point] = []
    for k in range(1, len(c) - 2):
        p0, p1, p2, p3 = c[k - 1], c[k], c[k + 1], c[k + 2]
        for j in range(10):
            u = j / 10.0
            u2, u3 = u * u, u * u * u
            dense.append(tuple(0.5 * (2 * p1[d] + (-p0[d] + p2[d]) * u + (2 * p0[d] - 5 * p1[d] + 4 * p2[d] - p3[d]) * u2
                                      + (-p0[d] + 3 * p1[d] - 3 * p2[d] + p3[d]) * u3) for d in (0, 1)))
    dense.append(ctrl[-1])
    out = [dense[0]]
    left = step
    for (x0, y0), (x1, y1) in zip(dense, dense[1:]):
        seg = math.hypot(x1 - x0, y1 - y0)
        pos = 0.0
        while seg - pos >= left:
            pos += left
            out.append((x0 + (x1 - x0) * pos / seg, y0 + (y1 - y0) * pos / seg))
            left = step
        left -= seg - pos
    if math.hypot(out[-1][0] - dense[-1][0], out[-1][1] - dense[-1][1]) > 0.2:
        out.append(dense[-1])
    return out


def _normals(pts: Sequence[Point]) -> List[Point]:
    """At each point, the unit normal on the belly side of the line. The line
    goes from the tail to the head, so the normal points down on the ground
    and forward on the reared neck."""
    out = []
    for k in range(len(pts)):
        (x0, y0), (x1, y1) = pts[max(0, k - 1)], pts[min(len(pts) - 1, k + 1)]
        tx, ty = x1 - x0, y1 - y0
        r = math.hypot(tx, ty) or 1.0
        out.append((-ty / r, tx / r))
    return out


def _strip(f: K.Frame, pts, nrm, widths, offset: float, scale: float, colour, body: bool, start: int = 0, stop: int = -1) -> None:
    """A band along the spine: `offset` and `scale` are parts of the width of
    the body there. It is drawn as short thick lines with round ends."""
    stop = len(pts) - 1 if stop < 0 else stop
    for k in range(start, stop, 2):
        j = min(stop, k + 2)
        a = (pts[k][0] + nrm[k][0] * widths[k] * offset, pts[k][1] + nrm[k][1] * widths[k] * offset)
        b = (pts[j][0] + nrm[j][0] * widths[j] * offset, pts[j][1] + nrm[j][1] * widths[j] * offset)
        w = 0.5 * (widths[k] + widths[j]) * scale
        f.limb([a, b], w, colour(k) if callable(colour) else colour, body=body)


def _mix(a, b, k: float):
    k = max(0.0, min(1.0, k))
    return tuple(int(a[c] + (b[c] - a[c]) * k) for c in range(3)) + (255,)


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = K.Frame(FRAME_SIZE)
    pose = FLAT_ON_GROUND
    hood, gape, tongue, eyes, alarm = 0.0, 0.0, 0.0, "open", False
    hump, sway, fade, snap, speed, sink = 0.0, 0.0, 1.0, False, 0.0, 0.0
    if anim == "idle":
        # It lies low and still; its head bobs and its tongue flicks.
        pts, ang = FLAT_ON_GROUND
        pose = ([(x, y - (0.8 * math.sin(cyc) if k >= 9 else 0.0)) for k, (x, y) in enumerate(pts)], ang + 2.0 * math.sin(cyc))
        tongue = 1.0 if i in (2, 3) else 0.0
        eyes = "open"
    elif anim == "walk":
        # It slithers: a wave goes back along the body from the head to the tail.
        hump = 1.0
        pts, ang = FLAT_ON_GROUND
        pose = ([(x, y - (0.8 * math.sin(cyc * 2.0) if k >= 10 else 0.0)) for k, (x, y) in enumerate(pts)], ang)
        tongue = 1.0 if i in (5,) else 0.0
    elif anim == "notice":
        # It rears up and its hood spreads.
        k = _smooth(min(1.0, t * 1.35))
        pose = _blend(FLAT_ON_GROUND, REARED, k)
        hood, eyes, alarm = k, "wide", True
        tongue = 1.0 if i in (2, 3) else 0.0
    elif anim == "windup":
        # The head goes back and the reared body sways.
        pose = _blend(REARED, RECOIL, 0.35 + 0.12 * math.sin(cyc))
        hood, eyes, gape = 1.0, "narrow", 10.0 + 4.0 * math.sin(cyc)
        sway = math.sin(cyc)
    elif anim == "attack_side":
        # The strike: the head goes back (0), forward and down with the mouth
        # open (1..2), the mouth shuts (3), and the head comes back up (4..5).
        k = [0.45, 0.5, 1.0, 1.0, 0.55, 0.15][i]
        pose = _blend(REARED, RECOIL, k) if i == 0 else _blend(REARED, STRIKE, k)
        gape = [12.0, 30.0, 34.0, 0.0, 0.0, 4.0][i]
        hood, eyes = [1.0, 0.9, 0.8, 0.8, 0.9, 1.0][i], "narrow"
        snap, speed = i == 3, [0.0, 0.6, 1.0, 0.7, 0.3, 0.0][i]
    elif anim == "hit":
        k = math.sin(math.pi * (i + 1) / (n + 1))
        pose = _blend(REARED, RECOIL, k)
        hood, eyes, gape = 1.0 - 0.5 * k, "shut", 10.0 * k
    elif anim == "death":
        sink = _smooth(min(1.0, t * 1.4))
        pose = _blend(REARED, DEAD, sink)
        hood, eyes, gape = 1.0 - sink, "shut", 8.0 * sink
        fade = 1.0 - max(0.0, t - 0.7) / 0.3

    ctrl, head_angle = pose
    if sway:
        # The sway moves the reared neck, more at the top than at the bottom.
        ctrl = [(x + sway * 2.0 * max(0.0, (k - 6) / 5.0), y) for k, (x, y) in enumerate(ctrl)]
    pts = _spine(ctrl)
    total = len(pts) - 1
    if hump:
        # The wave: humps go back along the body; there is none at the tip
        # of the tail and none at the head.
        moved = []
        for k, (x, y) in enumerate(pts):
            s = float(k)
            w = _smooth(s / 18.0) * _smooth((total - 8.0 - s) / 20.0)
            moved.append((x, y - 5.0 * w * (0.5 - 0.5 * math.cos(math.tau * (s / 32.0 + t)))))
        pts = moved
    nrm = _normals(pts)

    def width(k: int) -> float:
        u = k / max(1.0, total)
        w = BODY_W * (0.2 + 0.8 * _smooth(u / 0.4))
        return w * (1.0 - 0.14 * _smooth((u - 0.82) / 0.12))

    widths = [width(k) for k in range(len(pts))]
    neck_k = max(0, total - 34)

    def hide(k: int):
        # The tail is darker than the body.
        return _mix(TAIL, HIDE, _smooth((k / max(1.0, total) - 0.05) / 0.35))

    # The body, then the shade on its belly side and a light line down its
    # back.
    _strip(f, pts, nrm, widths, 0.0, 1.0, hide, True)
    _strip(f, pts, nrm, widths, 0.26, 0.48, HIDE_SHADE, False)
    _strip(f, pts, nrm, widths, -0.28, 0.2, HIDE_LIGHT, False, start=int(total * 0.2))
    # The pale cross-bands: thin, and they lean back like a chevron. They go
    # down from the back to the middle of the side.
    s = 10.0
    while s < neck_k:
        k = int(s)
        (x, y), (nx, ny), w = pts[k], nrm[k], widths[k]
        tx, ty = ny, -nx
        f.ink([(x - nx * w * 0.44 - tx * 2.2, y - ny * w * 0.44 - ty * 2.2), (x + nx * w * 0.12, y + ny * w * 0.12)],
              max(1.0, 0.15 * w), BAND)
        s += 10.0

    # The hood: long and narrow, it spreads out at the two sides of the neck.
    # The back half is olive with a dark edge; the front half is the pale
    # throat with two dark bars across it.
    if hood > 0.05:
        a, b = total - 36, total
        back, front = [], []
        for k in range(a, b + 1):
            u = (k - a) / float(b - a)
            # Widest a little above its middle, and still wide beside the
            # back of the head.
            shape = _smooth(u / 0.55) if u < 0.55 else 1.0 - 0.5 * _smooth((u - 0.55) / 0.45)
            hw = widths[k] * 0.5 + hood * 8.0 * shape
            (x, y), (nx, ny) = pts[k], nrm[k]
            back.append((x - nx * hw, y - ny * hw))
            front.append((x + nx * hw, y + ny * hw))
        mid = pts[a:b + 1]
        f.poly(back + front[::-1], HIDE)
        # The dark edge of the back half, and the pale chevron in it.
        rim = [((px * 0.3 + bx * 0.7), (py * 0.3 + by * 0.7)) for (px, py), (bx, by) in zip(mid, back)]
        f.poly(back + rim[::-1], HIDE_SHADE, body=False)
        if hood > 0.4:
            chevron = [((px * 0.55 + bx * 0.45), (py * 0.55 + by * 0.45)) for (px, py), (bx, by) in zip(mid, back)]
            f.ink(chevron[4:-6], 1.2, BAND)
        throat = [((px * 0.15 + fx * 0.85), (py * 0.15 + fy * 0.85)) for (px, py), (fx, fy) in zip(mid, front)]
        f.poly(mid + throat[::-1], BELLY, body=False)
        if hood > 0.4:
            for u in (0.3, 0.55):
                k = int(u * (b - a))
                f.ink([mid[k], throat[k]], 2.0, THROAT_BAR)
    else:
        # The throat is pale when the hood is shut.
        _strip(f, pts, nrm, widths, 0.25, 0.4, BELLY, False, start=total - 22)

    # The head: large and round, on the end of the neck.
    hx, hy = pts[-1]
    ang = head_angle

    def D(p: Sequence[Point]) -> List[Point]:
        """Head points: x goes forward along the head and y goes down."""
        return K.turn([(hx + x * HEAD, hy + y * HEAD) for x, y in p], hx, hy, ang)

    def L(p: Sequence[Point]) -> List[Point]:
        """Points of the lower jaw: turned down about the hinge by the gape."""
        return K.turn(D(p), *D([(1.0, 1.6)])[0], gape)

    if gape > 3.0:
        f.poly(D([(1.0, 1.4), (14.0, 1.4)]) + L([(13.0, 1.6), (1.0, 1.6)]), MOUTH)
    f.poly(L([(-3.0, 1.0), (3.0, 1.4), (13.5, 1.5), (13.0, 3.4), (8.0, 4.6), (2.0, 5.0), (-3.0, 4.8)]), BELLY)
    f.poly(D([(-4.0, -4.6), (2.0, -5.8), (8.0, -5.8), (12.5, -4.4), (15.2, -2.0), (15.8, 0.4), (14.6, 1.8), (3.0, 1.9), (-4.0, 2.2)]), HIDE)
    f.poly(D([(0.0, -4.8), (8.0, -5.0), (12.6, -3.6), (8.0, -3.8)]), HIDE_LIGHT, body=False)
    # The large scales on top of the head, and the line of the mouth.
    f.ink(D([(3.0, -5.6), (4.4, -2.8)]), 0.7, HIDE_SHADE)
    f.ink(D([(-1.4, -5.0), (0.0, -1.8)]), 0.7, HIDE_SHADE)
    f.ink(D([(1.0, 1.7), (14.6, 1.7)]), 0.7, HIDE_SHADE)
    if gape > 8.0:
        # The fangs are short, at the front of the upper jaw.
        for x in (11.0, 12.6):
            f.poly(D([(x - 0.6, 1.6), (x + 0.6, 1.6), (x, 3.6)]), FANG, body=False)
    f.dot(*D([(13.8, -1.0)])[0], 0.6, EYE)
    ex, ey = D([(9.0, -1.8)])[0]
    if eyes == "shut":
        f.ink([(ex - 1.8, ey), (ex + 1.8, ey + 0.3)], 1.0, EYE)
    else:
        r = 1.9 if eyes == "wide" else (1.4 if eyes == "narrow" else 1.6)
        f.ellipse(ex, ey, r, r, EYE, body=False)
        f.dot(ex - 0.5, ey - 0.5, 0.45, (240, 230, 200, 255))
        if eyes == "narrow":
            f.ink(D([(7.0, -4.0), (11.6, -2.8)]), 1.1, HIDE_SHADE)
    if tongue:
        # The forked tongue flicks out from the front of the mouth.
        base = D([(15.4, 1.0)])[0]
        tip = D([(21.0, 1.2)])[0]
        f.ink([base, tip], 0.9, TONGUE)
        f.ink([tip, D([(23.4, -0.4)])[0]], 0.8, TONGUE)
        f.ink([tip, D([(23.2, 2.8)])[0]], 0.8, TONGUE)

    if speed > 0.1:
        x = min(FRAME_SIZE[0] - MARGIN - 16.0, max(MARGIN + 12.0, pts[int(total * 0.55)][0]))
        H.dust(f, x, GROUND - 1.0, speed * 0.6, f"king cobra dust {anim} {i}", spread=0.8, colour=DUST)
    if snap:
        # The mouth shuts: short lines out from the tip of the snout.
        bx, by = D([(16.5, 0.5)])[0]
        for k in (-1.0, 0.0, 1.0):
            f.ink([(bx + 1.5, by + k * 4.0), (min(FRAME_SIZE[0] - MARGIN - 1.0, bx + 6.0), by + k * 6.5)], 1.3, K.alpha(K.WHITE, 0.95))
    if anim == "death" and t > 0.3:
        H.dust(f, 60.0, GROUND - 1.0, min(1.0, (t - 0.3) * 2.0), f"king cobra death {i}", spread=1.4, colour=DUST)
    if alarm:
        H.alarm_mark(f, min(FRAME_SIZE[0] - MARGIN - 4.0, hx + 24.0), MARGIN + 13.0)
    return f.finish(outline=H.SEPIA_INK, width=1.7, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
