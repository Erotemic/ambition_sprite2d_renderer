"""The Water Monitor of the History dimension: the great lizard of the rivers of Srivijaya.

The Asian water monitor (Varanus salvator) is one of the largest lizards
in the world. It lives along the rivers, the mangroves and the coasts of
South Asia and of Southeast Asia, from Sri Lanka to Sumatra, Java and the
Philippines, and it swims well. It is dark grey to black, with rows of
small yellow spots in bands across its back. Its neck is long, and its head
is long and narrow, with the nostrils near the tip of the snout. Its tail
is as long as its body and flat from side to side, with a low ridge on
top: it uses the tail to swim and to strike. Its tongue is long and forked,
and it flicks it out to smell the air. Srivijaya was a kingdom of the seas
on Sumatra, and its ports were on the rivers where these lizards live.

It walks with its body up off the ground and its legs out to the sides,
and its body and tail swing from side to side. At rest it flicks its
tongue. When it sees you it lifts its head and flicks its tongue (the
notice row). Its windup lifts the head high and swings the tail. Its
strike is a whip of the tail, then a bite forward. A hit makes it pull
back with its head up. At its death it sinks flat and fades.

The frame is 224 by 64 px: the body box is 96 by 24 world units, and the
monitor faces right.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Sequence, Tuple

from . import _art_cast_kit as K
from . import _history_africa_kit as H

TARGET_NAME = "water_monitor"
FRAME_SIZE = (224, 64)
ROWS = K.ENEMY_ROWS
#: Nothing is drawn nearer the edge of the frame than this.
MARGIN = 6.0
GROUND = 56.0

ACTOR_METADATA = K.enemy_metadata(
    TARGET_NAME, "Water Monitor", "Quadruped", "Large", "Medium", "Walk", ["lizard", "reptile", "tail_whip", "bite"],
    "The Asian water monitor of the History dimension's room of Srivijaya: a big dark grey-black lizard with rows of "
    "yellow spots in bands, a long neck, a long narrow head with a forked tongue, and a long flat tail. It walks with "
    "its legs out to the sides. It lifts its head when it sees you, swings its tail, whips you with its tail and bites.",
)
ACTOR_METADATA["tags"] = ["enemy", "history", "srivijaya"]

HIDE = (72, 72, 64, 255)
HIDE_SHADE = (46, 46, 42, 255)
HIDE_LIGHT = (102, 102, 88, 255)
SPECK = (228, 202, 92, 255)
TAIL_BAND = (182, 168, 112, 255)
BELLY = (210, 196, 140, 255)
MOUTH = (196, 112, 122, 255)
TONGUE = (176, 84, 132, 255)
IRIS = (200, 144, 64, 255)
PUPIL = (24, 20, 16, 255)
CLAW = (34, 32, 28, 255)
DUST = (196, 176, 140, 255)

Point = Tuple[float, float]

# The spine: points from the tip of the tail to the back of the head. LOW is
# the pose of the walk. The other poses move only some of the points: the
# rows add part of each change to LOW.
LOW = [(14.0, 53.5), (29.0, 52.5), (44.0, 50.5), (60.0, 47.5), (76.0, 43.5), (92.0, 39.5), (108.0, 37.5), (124.0, 36.5), (140.0, 36.5),
       (153.0, 36.0), (164.0, 33.5), (174.0, 31.0)]
#: The tail goes up in a curve behind the body.
TAIL_UP = [(24.0, 12.5), (22.0, 24.5), (30.0, 34.5), (46.0, 40.5), (64.0, 41.5), (82.0, 39.5)] + LOW[6:]
#: The neck and the head go up high.
HEAD_UP = LOW[:7] + [(124.0, 36.5), (139.0, 35.5), (151.0, 31.5), (158.0, 24.5), (164.0, 17.5)]
#: The neck goes out straight and the head goes forward to bite.
LUNGE = LOW[:7] + [(127.0, 36.5), (143.0, 36.0), (158.0, 35.5), (170.0, 34.5), (181.0, 34.0)]
#: The point of each part of the spine, as a part of its length: the hips, the shoulders.
HIP_U, SHOULDER_U = 0.6, 0.82

# The width of the body along its length (a part of the length, the width
# in px). The tail is flat from side to side, so from the side it is deep.
WIDTHS = [(0.0, 2.2), (0.15, 4.6), (0.35, 7.4), (0.57, 10.6), (0.64, 13.6), (0.72, 14.6), (0.8, 13.0), (0.87, 9.6), (1.0, 9.6)]


def _smooth(u: float) -> float:
    u = max(0.0, min(1.0, u))
    return u * u * (3.0 - 2.0 * u)


def _table(table: Sequence[Point], u: float) -> float:
    """The value of the table at `u`, with straight lines between its rows."""
    for (u0, v0), (u1, v1) in zip(table, table[1:]):
        if u <= u1:
            return v0 + (v1 - v0) * (u - u0) / max(1e-6, u1 - u0)
    return table[-1][1]


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
    """At each point, the unit normal on the belly side of the line (down,
    when the line goes to the right)."""
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
        f.limb([a, b], 0.5 * (widths[k] + widths[j]) * scale, colour, body=body)


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = K.Frame(FRAME_SIZE)
    dx, dy, head_angle, gape, tongue = 0.0, 0.0, 6.0, 0.0, 0.0
    tail_up, head_up, lunge, sink, fade = 0.0, 0.0, 0.0, 0.0, 1.0
    walk, stride, lift, speed = None, 0.0, 0.0, 0.0
    eyes, alarm, snap, whip, swing = "open", False, False, 0.0, 0.0
    if anim == "idle":
        # It stands and breathes, and flicks its tongue.
        dy = 0.4 * math.sin(cyc)
        head_angle = 6.0 + 2.0 * math.sin(cyc)
        tongue = 1.0 if i in (2, 3) else 0.0
        swing = 0.3 * math.sin(cyc)
        eyes = "shut" if i == 5 else "open"
    elif anim == "walk":
        # The walk: the legs go out to the sides and move in diagonal pairs.
        # The body swings from side to side, so the shoulders and the hips go
        # up and down in turn and the tail moves in a wave.
        walk, stride, lift = t, 16.0, 4.0
        swing = math.sin(cyc)
        head_angle = 6.0 + 3.0 * math.sin(cyc)
        tongue = 1.0 if i == 6 else 0.0
    elif anim == "notice":
        # The head comes up and the tongue flicks out.
        k = _smooth(min(1.0, t * 1.4))
        head_up, head_angle, eyes, alarm = 0.55 * k, 6.0 - 10.0 * k, "wide", True
        tongue = 1.0 if i in (1, 2, 3) else 0.0
    elif anim == "windup":
        # The head goes up high and the tail swings up behind.
        head_up, head_angle, eyes = 1.0, -8.0 + 2.0 * math.sin(cyc), "narrow"
        tail_up = 0.55 + 0.35 * math.sin(cyc)
        tongue = 1.0 if i == 1 else 0.0
    elif anim == "attack_side":
        # The strike: the tail goes up (0) and whips down (1); then the head
        # goes forward with the jaws open (2), they shut (3), and back (4..5).
        tail_up = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0][i]
        whip = 1.0 if i == 1 else 0.0
        head_up = [0.6, 0.3, 0.0, 0.0, 0.2, 0.3][i]
        lunge = [0.0, 0.2, 1.0, 1.0, 0.5, 0.15][i]
        head_angle = [-4.0, 0.0, 4.0, 8.0, 6.0, 4.0][i]
        gape = [0.0, 8.0, 24.0, 0.0, 0.0, 0.0][i]
        dx = [-2.0, 0.0, 4.0, 5.0, 2.0, 0.0][i]
        snap, eyes = i == 3, "narrow"
        speed = [0.0, 0.8, 0.6, 0.4, 0.2, 0.0][i]
    elif anim == "hit":
        k = math.sin(math.pi * (i + 1) / (n + 1))
        dx, head_up, head_angle, tail_up = -6.0 * k, 0.6 * k, 6.0 - 20.0 * k, 0.3 * k
        eyes, gape = "shut", 14.0 * k
    elif anim == "death":
        sink = _smooth(min(1.0, t * 1.4))
        head_angle, eyes, gape = 6.0 + 6.0 * sink, "shut", 10.0 * sink
        fade = 1.0 - max(0.0, t - 0.7) / 0.3

    # The pose: the walk pose, with a part of each change added.
    ctrl = []
    for k, (x, y) in enumerate(LOW):
        x += (TAIL_UP[k][0] - x) * tail_up + (HEAD_UP[k][0] - x) * head_up + (LUNGE[k][0] - x) * lunge
        y += (TAIL_UP[k][1] - y) * tail_up + (HEAD_UP[k][1] - y) * head_up + (LUNGE[k][1] - y) * lunge
        if swing:
            # The swing of the body: the shoulders and the hips go up and
            # down in turn, and a wave goes along the tail.
            if k <= 5:
                y += 1.6 * swing * math.sin(k * 1.1 - cyc) * k / 5.0
            elif k in (6, 7):
                y += 0.8 * swing
            elif k in (8, 9):
                y -= 0.8 * swing
        if sink and k >= 3:
            # It sinks down onto its belly.
            y += 9.0 * sink * min(1.0, (k - 2) / 3.0)
        ctrl.append((x + dx, y + dy))
    pts = _spine(ctrl)
    total = len(pts) - 1
    nrm = _normals(pts)
    widths = [_table(WIDTHS, k / max(1.0, total)) for k in range(len(pts))]

    def at(u: float, across: float = 0.0) -> Point:
        """The point at the part `u` of the spine, moved `across` (a part of
        the width there) to the belly side."""
        k = int(round(u * total))
        (x, y), (nx, ny), w = pts[k], nrm[k], widths[k]
        return (x + nx * w * across, y + ny * w * across)

    def leg(u: float, phase: float, fore: bool, near: bool) -> None:
        colour = HIDE if near else HIDE_SHADE
        top = at(u, 0.2 if near else 0.05)
        gx, gy = (0.0, 0.0)
        if walk is not None:
            gx, gy = H.gait(walk + phase, stride, lift)
        foot = (top[0] + gx + (3.0 if fore else -3.0), GROUND - 1.0 + gy)
        if sink:
            # The legs splay out to the sides as it sinks flat.
            foot = (top[0] + (9.0 if fore else -9.0) * sink, min(GROUND - 1.0, foot[1]))
        # The legs go out to the sides: the elbow and the knee stand out
        # level with the bottom of the body, and the lower leg goes down to
        # the foot.
        low = min(foot[1] - 4.0, top[1] + 5.0)
        joint = (top[0] - 5.0, low) if fore else (top[0] + 6.0, low)
        f.limb([top, joint], 7.0 if fore else 8.4, colour)
        f.limb([joint, (foot[0], foot[1] - 1.6)], 4.4 if fore else 5.0, colour)
        fx, fy = foot
        # The foot: long thin toes that spread forward, each with a claw.
        f.poly([(fx - 3.0, fy - 2.6), (fx + 2.0, fy - 2.6), (fx + 3.0, fy + 0.6), (fx - 3.0, fy + 0.6)], colour)
        reach = 5.0 if fore else 6.4
        for k, (tx, ty) in enumerate(((reach, -1.4), (reach + 1.4, 0.2), (reach - 1.0, 0.8))):
            f.limb([(fx + 0.6, fy - 0.6), (fx + tx, fy + ty)], 1.5, colour)
            f.ink([(fx + tx - 0.2, fy + ty), (fx + tx + 1.2, fy + ty + 0.4)], 0.7, CLAW)
        if near:
            for sx, sy in ((0.35, 0.3), (0.65, 0.5)):
                f.dot(top[0] + (joint[0] - top[0]) * sx, top[1] + (joint[1] - top[1]) * sx - sy, 0.7, SPECK)

    # The far legs.
    leg(HIP_U - 0.02, 0.0, False, False)
    leg(SHOULDER_U - 0.01, 0.0, True, False)

    # The ridge on top of the tail: a row of low points.
    for k in range(8, int(total * 0.56), 3):
        (x, y), (nx, ny), w = pts[k], nrm[k], widths[k]
        h = 1.6 + 1.4 * k / total
        f.poly([(x - nx * w * 0.42 - ny * 1.3, y - ny * w * 0.42 + nx * 1.3), (x - nx * w * 0.42 + ny * 1.3, y - ny * w * 0.42 - nx * 1.3),
                (x - nx * (w * 0.5 + h), y - ny * (w * 0.5 + h))], HIDE_SHADE)

    # The body: the tail, the body and the neck in one, then the shade on the
    # belly side, a light line down the back, and the pale throat.
    _strip(f, pts, nrm, widths, 0.0, 1.0, HIDE, True)
    _strip(f, pts, nrm, widths, 0.27, 0.46, HIDE_SHADE, False)
    _strip(f, pts, nrm, widths, -0.3, 0.2, HIDE_LIGHT, False, start=int(total * 0.12))
    _strip(f, pts, nrm, widths, 0.33, 0.26, BELLY, False, start=int(total * 0.86))

    # The pale bands across the tail, and the rows of yellow spots in bands
    # across the back and the neck.
    s = 12.0
    while s < total * 0.55:
        k = int(s)
        (x, y), (nx, ny), w = pts[k], nrm[k], widths[k]
        f.ink([(x - nx * w * 0.42, y - ny * w * 0.42), (x + nx * w * 0.26, y + ny * w * 0.26)], max(1.0, 0.6 + 0.12 * w), TAIL_BAND)
        s += 10.0
    s = total * 0.55
    row = 0
    while s < total * 0.97:
        k = int(s)
        (x, y), (nx, ny), w = pts[k], nrm[k], widths[k]
        tx, ty = ny, -nx
        r = 0.7 + 0.04 * w
        for c, across in enumerate((-0.36, -0.14, 0.08)):
            lean = 1.2 if (c + row) % 2 else -0.6
            f.dot(x + nx * w * across + tx * lean, y + ny * w * across + ty * lean, r, SPECK)
        s += 6.0 if s < total * 0.85 else 4.5
        row += 1

    # The head: long and narrow, with the nostril near the tip of the snout.
    hx, hy = pts[-1]

    def D(p: Sequence[Point]) -> List[Point]:
        """Head points: x goes forward along the head and y goes down."""
        return K.turn([(hx + x, hy + y) for x, y in p], hx, hy, head_angle)

    def L(p: Sequence[Point]) -> List[Point]:
        """Points of the lower jaw: turned down about the hinge by the gape."""
        return K.turn(D(p), *D([(3.0, 1.8)])[0], gape)

    if gape > 3.0:
        f.poly(D([(3.0, 1.6), (27.0, 1.6)]) + L([(26.0, 1.8), (3.0, 1.8)]), MOUTH)
    f.poly(L([(-4.0, 1.6), (6.0, 1.6), (27.0, 1.8), (25.0, 3.6), (16.0, 4.8), (6.0, 5.6), (-4.0, 5.8)]), BELLY)
    for x in (10.0, 16.0, 22.0):
        # The dark bars on the lips.
        f.ink(L([(x, 2.2), (x - 1.0, 4.4)]), 0.9, HIDE_SHADE)
    f.poly(D([(-4.0, -5.2), (4.0, -6.0), (10.0, -5.8), (15.0, -4.8), (21.0, -3.8), (26.0, -2.6), (28.6, -1.0), (29.0, 0.8), (27.4, 1.9),
              (6.0, 1.9), (-4.0, 2.4)]), HIDE)
    f.poly(D([(0.0, -5.4), (10.0, -5.4), (20.0, -3.6), (26.0, -2.2), (20.0, -2.6), (10.0, -3.8)]), HIDE_LIGHT, body=False)
    f.ink(D([(4.0, 1.8), (27.4, 1.8)]), 0.8, HIDE_SHADE)
    for x, y in ((4.0, -3.0), (7.0, -4.2), (18.0, -3.0), (2.0, -0.6)):
        f.dot(*D([(x, y)])[0], 0.6, SPECK)
    # The ear: a dark hole behind the jaw.
    f.ellipse(*D([(-1.6, -0.2)])[0], 1.2, 1.5, HIDE_SHADE, body=False)
    f.dot(*D([(25.8, -1.4)])[0], 0.7, PUPIL)
    ex, ey = D([(12.0, -2.6)])[0]
    if eyes == "shut":
        f.ink([(ex - 1.8, ey), (ex + 1.8, ey + 0.3)], 1.0, PUPIL)
    else:
        r = 1.8 if eyes == "wide" else (1.2 if eyes == "narrow" else 1.5)
        f.ellipse(ex, ey, 1.8, r, IRIS, body=False)
        f.dot(ex + 0.2, ey, min(r, 0.9), PUPIL)
        f.ink(D([(9.0, -4.8), (15.0, -4.2)]), 1.0, HIDE_SHADE)
    if tongue:
        # The long forked tongue flicks out from the tip of the snout.
        base, tip = D([(28.6, 1.2)])[0], D([(35.0, 1.6)])[0]
        f.ink([base, tip], 1.0, TONGUE)
        f.ink([tip, D([(38.4, -0.4)])[0]], 0.8, TONGUE)
        f.ink([tip, D([(38.2, 3.4)])[0]], 0.8, TONGUE)

    # The near legs.
    leg(HIP_U + 0.01, 0.5, False, True)
    leg(SHOULDER_U, 0.5, True, True)

    if speed > 0.1:
        x = min(FRAME_SIZE[0] - MARGIN - 20.0, max(MARGIN + 14.0, at(SHOULDER_U)[0]))
        H.dust(f, x, GROUND - 1.0, speed * 0.7, f"water monitor dust {anim} {i}", spread=1.0, colour=DUST)
    if whip:
        # The whip of the tail: lines that show the path of the tail, from up
        # high down to the ground.
        for k, r in enumerate((30.0, 24.0, 18.0)):
            cx, cy = 74.0, 48.0
            arc = [(cx - r * math.cos(a), cy - r * math.sin(a)) for a in [math.radians(d) for d in range(20, 75, 6)]]
            f.ink(arc, 1.4 - 0.3 * k, K.alpha(K.WHITE, 0.9 - 0.2 * k))
        H.dust(f, 30.0, GROUND - 1.0, 0.8, f"water monitor whip {i}", spread=1.2, colour=DUST)
    if snap:
        # The jaws shut: short lines out from the tip of the snout.
        bx, by = D([(30.0, 1.0)])[0]
        for k in (-1.0, 0.0, 1.0):
            f.ink([(bx + 2.0, by + k * 4.0), (min(FRAME_SIZE[0] - MARGIN - 1.0, bx + 7.0), by + k * 6.0)], 1.3, K.alpha(K.WHITE, 0.95))
    if anim == "death" and t > 0.3:
        H.dust(f, at(0.7)[0], GROUND - 1.0, min(1.0, (t - 0.3) * 2.0), f"water monitor death {i}", spread=2.0, colour=DUST)
    if alarm:
        H.alarm_mark(f, min(FRAME_SIZE[0] - MARGIN - 4.0, hx - 12.0), MARGIN + 11.0)
    return f.finish(outline=H.SEPIA_INK, width=1.7, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
