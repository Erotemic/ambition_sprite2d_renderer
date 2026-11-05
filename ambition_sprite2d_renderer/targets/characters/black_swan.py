"""The Black Swan of the History dimension: the swan of the wetlands of Budj Bim.

The black swan (Cygnus atratus) lives on the lakes and swamps of
Australia, and many nest on the wetlands of Tae Rak (Lake Condah) below
Budj Bim. It is black all over, with a few pale curled feathers on its
back, and its flight feathers are white: they show only when it opens its
wings. Its bill is red, with a white band near its tip, and its neck is the
longest of all swans for its size. It walks with a waddle on short black
legs with webbed feet.

It walks and hisses. When it sees you it raises its neck high and half
opens its wings, so the white shows. Its windup draws its neck back with
its wings up; its strike is a lunge of the neck with the bill open while
its wings beat. A hit makes it flinch; at its death it sinks onto its
breast and its neck lies on the ground.

The frame is 160 by 160 px, and the swan faces right. Its body box is about
80 by 100 px (frame pixels): from x 38 to 118 and from y 52 to the ground
row at y 152.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import List, Tuple

from . import _art_cast_kit as K
from . import _history_americas_kit as A
from . import _stage_kit as S

TARGET_NAME = "black_swan"
FRAME_SIZE = (160, 160)
ROWS = K.ENEMY_ROWS
GROUND = 152.0

ACTOR_METADATA = A.enemy_metadata(
    TARGET_NAME, "Black Swan", "budj_bim", "Avian", "Medium", "Light", "Walk", ["bird", "swan", "hiss", "wings", "lunge"],
    "The black swan of the History dimension's Budj Bim: black all over, with white flight feathers that show when it "
    "opens its wings and a red bill with a white band. It walks and hisses, raises its neck and half opens its wings when "
    "it sees you, draws its neck back with its wings up, and lunges with its bill open while its wings beat.",
)

PLUME = (50, 48, 56, 255)
PLUME_SHADE = (30, 28, 34, 255)
PLUME_LIGHT = (98, 96, 108, 255)
#: The pale edges of the curled feathers on the back.
CURL = (128, 124, 132, 255)
WHITE = (240, 238, 232, 255)
WHITE_SHADE = (200, 198, 194, 255)
BILL = (196, 52, 48, 255)
BILL_SHADE = (150, 34, 34, 255)
BILL_BAND = (238, 232, 224, 255)
MOUTH = (110, 30, 36, 255)
LEG = (36, 34, 36, 255)
EYE = (170, 40, 36, 255)
GLINT = (240, 230, 220, 255)

Point = Tuple[float, float]


def _curve(a: Point, b: Point, c: Point, steps: int = 10) -> List[Point]:
    """A smooth curve from `a` to `c`, pulled toward `b`."""
    out = []
    for k in range(steps + 1):
        u = k / steps
        out.append(((1 - u) ** 2 * a[0] + 2 * u * (1 - u) * b[0] + u * u * c[0], (1 - u) ** 2 * a[1] + 2 * u * (1 - u) * b[1] + u * u * c[1]))
    return out


def _tube(spine: List[Point], w0: float, w1: float) -> List[Point]:
    """A shape round the curve `spine` whose half width goes from `w0` to
    `w1`."""
    left, right = [], []
    n = len(spine)
    for k, (x, y) in enumerate(spine):
        x0, y0 = spine[max(0, k - 1)]
        x1, y1 = spine[min(n - 1, k + 1)]
        ln = math.hypot(x1 - x0, y1 - y0) or 1.0
        nx, ny = (y1 - y0) / ln, -(x1 - x0) / ln
        w = w0 + (w1 - w0) * k / (n - 1)
        left.append((x + nx * w, y + ny * w))
        right.append((x - nx * w, y - ny * w))
    return left + right[::-1]


def _wing(f: K.Frame, shoulder: Point, spread: float, raise_: float, near: bool, back: Point) -> None:
    """A wing from `shoulder`. `spread` 0 is folded on the back (to the
    point `back`), 1 is open wide; `raise_` lifts it (degrees). Open, its
    black coverts lie along the leading edge and its white flight feathers
    fan out behind them, the long primaries at the tip."""
    sx, sy = shoulder
    black = PLUME if near else PLUME_SHADE
    white = WHITE if near else WHITE_SHADE
    if spread < 0.08:
        # Folded: a long black shape high over the back to the tail, with
        # the curled pale-edged feathers on it.
        bx, by = back
        pts = [(sx + 4.0, sy + 1.0), (sx - 6.0, sy - 5.0), (_lerp(sx, bx, 0.5), _lerp(sy, by, 0.5) - 9.0), (bx - 2.0, by - 6.0), (bx - 6.0, by + 1.0),
               (_lerp(sx, bx, 0.5), _lerp(sy, by, 0.5) + 6.0), (sx - 4.0, sy + 7.0)]
        f.poly(pts, black)
        if near:
            for k in range(5):
                x, y = _lerp(sx - 6.0, bx + 4.0, k / 4.0), _lerp(sy - 3.0, by - 4.0, k / 4.0)
                f.ink(_curve((x + 2.0, y + 3.0), (x - 4.0, y - 3.0), (x - 1.0, y + 1.0), 6), 0.9, CURL)
        return
    a = math.radians(178.0 - raise_ * spread - 30.0 * spread)
    ux, uy = math.cos(a), -math.sin(a)
    vx, vy = uy, -ux
    span = 26.0 + 30.0 * spread

    def P(u: float, v: float) -> Point:
        return (sx + ux * u * span + vx * v, sy + uy * u * span + vy * v)

    # The white flight feathers: from the arm and the hand, longest at the
    # tip, each with a dark line between it and the next.
    trail = [P(1.0, 4.0), P(0.92, 14.0), P(0.78, 20.0), P(0.62, 22.0), P(0.46, 21.0), P(0.30, 19.0), P(0.14, 16.0), P(0.0, 11.0)]
    f.poly([P(0.0, 2.0), P(0.5, 0.0), P(1.0, 2.0)] + trail, white)
    for k in range(1, len(trail) - 1):
        u = 1.0 - k / float(len(trail) - 1)
        f.ink([P(u * 0.95, 5.0), trail[k]], 0.6, WHITE_SHADE if near else (156, 154, 150, 255))
    # The black coverts along the leading edge, with a few curled feathers.
    f.poly([P(-0.06, -1.0), P(0.5, -2.0), P(0.86, 0.0), P(0.70, 7.0), P(0.40, 9.0), P(0.10, 10.0), P(-0.04, 8.0)], black)
    if near:
        for u in (0.2, 0.4, 0.6):
            x, y = P(u, 4.0)
            f.ink(_curve((x, y), (x - 3.0, y + 3.0), (x + 1.0, y + 3.0), 5), 0.8, CURL)


def _lerp(a: float, b: float, u: float) -> float:
    return a + (b - a) * u


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    rng = random.Random(f"black_swan:{anim}:{i}")
    f = K.Frame(FRAME_SIZE)

    # The pose. `dx`/`dy` move the body; `lean` turns it (+ is breast
    # down); `neck` is how far the neck reaches forward (0 upright, 1 out
    # level); `rear` draws the head back; `tall` lifts the neck; `spread`
    # and `raise_` open the wings; `gape` opens the bill; `walk` is the
    # phase of the gait; `sink` folds the legs under it.
    dx, dy, lean, neck, rear, tall, spread, raise_, gape, walk, sink = 0.0, 0.0, 0.0, 0.15, 0.0, 0.0, 0.0, 30.0, 0.0, None, 0.0
    eyes, fade, alarm, feathers, hiss = "open", 1.0, False, 0, False
    if anim == "idle":
        # It stands; its neck sways a little and the bill dips.
        neck = 0.15 + 0.06 * math.sin(cyc)
        dy = 0.4 * math.sin(cyc * 2.0)
        eyes = "shut" if i == 3 else "open"
    elif anim == "walk":
        # It waddles: the body rocks from side to side and bobs, and it
        # hisses with its neck held forward.
        walk = t
        dy = -1.2 * abs(math.sin(cyc))
        lean = 3.0 * math.sin(cyc)
        neck = 0.35 + 0.05 * math.sin(cyc * 2.0)
        gape = 0.3 if i % 4 in (1, 2) else 0.0
        hiss = gape > 0.0
    elif anim == "notice":
        # It raises its neck high and half opens its wings.
        k = math.sin(math.pi * 0.5 * min(1.0, t * 1.4))
        neck, tall, spread, raise_, eyes, alarm = 0.15 - 0.15 * k, 8.0 * k, 0.5 * k, 40.0, "wide", True
    elif anim == "windup":
        # The neck is drawn back in an S, the wings up and open, the bill
        # a little open: it hisses.
        rear = 0.9 + 0.1 * math.sin(cyc * 2.0)
        spread, raise_, gape, eyes, hiss = 0.85, 70.0 + 6.0 * math.sin(cyc * 2.0), 0.5, "narrow", True
        lean = -4.0
        dx = -3.0
    elif anim == "attack_side":
        # The lunge: the neck shoots forward level with the bill open, and
        # the wings beat down and up.
        u = t
        k = math.sin(math.pi * min(1.0, u * 1.6)) if u < 0.62 else max(0.0, 1.0 - (u - 0.62) / 0.38) * 0.3
        rear = max(0.0, 1.0 - u * 3.0)
        neck = 0.15 + 0.85 * k
        spread = 0.85
        raise_ = 70.0 - 60.0 * abs(math.sin(math.pi * u * 2.0))
        gape = 0.9 if k > 0.3 else 0.3
        lean = 8.0 * k - 4.0 * rear
        dx = 3.0 * k
        eyes = "narrow"
    elif anim == "hit":
        k = math.sin(math.pi * (i + 1) / (n + 1))
        dx, lean, neck, tall, eyes, spread, raise_ = -4.0 * k, -6.0 * k, 0.1, 4.0 * k, "shut", 0.4 * k, 40.0
        feathers = 4
    elif anim == "death":
        u = min(1.0, t / 0.8)
        sink = u
        neck, eyes, spread, raise_ = 0.15 + 0.55 * u, "shut", 0.3 * u, 0.0
        lean = 4.0 * u
        fade = 1.0 - max(0.0, t - 0.75) / 0.25

    # The body: a long low boat of black plumage on short legs, its tail
    # turned up at the back, its breast round at the front.
    bx, by = 62.0 + dx, GROUND - 32.0 + dy + 14.0 * sink

    def Bd(pts):
        return K.turn([(bx + x, by + y) for x, y in pts], bx, by, lean)

    hip = Bd([(4.0, 8.0)])[0]

    def leg(near: bool, ph: float) -> None:
        if sink > 0.5:
            return
        fx, fy = hip[0] + (3.0 if near else -4.0), GROUND - 3.0
        if walk is not None:
            gx, gy = A.gait(ph, 12.0, 5.0)
            fx += gx
            fy += gy
        knee, foot = S.joint(hip, (fx, fy), 9.0, 12.0, 1.0)
        knee = (knee[0], min(knee[1], GROUND - 6.0))
        colour = LEG if near else PLUME_SHADE
        f.limb([hip, knee], 5.0, colour)
        f.limb([knee, foot], 3.2, colour)
        # The webbed foot: three toes joined by a web.
        f.poly([foot, (foot[0] + 10.0, foot[1] + 2.0), (foot[0] + 8.0, foot[1] + 3.2), (foot[0] - 1.0, foot[1] + 2.8)], colour)

    ph = walk or 0.0
    shoulder = Bd([(12.0, -10.0)])[0]
    tail_top = Bd([(-36.0, -14.0)])[0]
    leg(False, ph + 0.5)
    if spread >= 0.08:
        _wing(f, (shoulder[0] + 3.0, shoulder[1] - 2.0), spread, raise_ + 10.0, False, tail_top)
    outline = []
    for k in range(32):
        ang = math.tau * k / 32.0
        x, y = 36.0 * math.cos(ang), (12.0 if math.sin(ang) > 0 else 13.0) * math.sin(ang)
        if x < -18.0:
            # The tail turns up at the back.
            y -= (-18.0 - x) * 0.55
        if x > 0 and y > 0:
            # The breast is deep and round.
            y += 2.0 * math.sin(ang)
        outline.append((x - 4.0, y))
    body = Bd(outline)
    if sink:
        body = [(x, min(y, GROUND - 1.0)) for x, y in body]
    f.poly(body, PLUME)
    f.poly(Bd([(28.0, 3.0), (12.0, 10.0), (-12.0, 9.0), (-30.0, 3.0), (-8.0, 5.0), (14.0, 4.0)]), PLUME_SHADE, body=False)
    f.poly(Bd([(24.0, -10.0), (6.0, -13.0), (-18.0, -12.0), (-2.0, -9.0)]), PLUME_LIGHT, body=False)
    leg(True, ph)
    _wing(f, shoulder, spread, raise_, True, tail_top)

    # The neck: long and thin, in an S: forward at its foot, back in its
    # middle, forward again under the head. `neck` sends it forward and
    # level, `rear` draws it back over the body, `tall` stretches it up.
    base = Bd([(26.0, -6.0)])[0]
    if sink:
        base = (base[0], min(base[1], GROUND - 6.0))
    up = 62.0 + tall
    up_mid = (base[0] + 2.0, base[1] - up * 0.52)
    up_head = (base[0] + 12.0, base[1] - up)
    fw_mid = (base[0] + 22.0, base[1] - 14.0)
    fw_head = (base[0] + 46.0, base[1] - 14.0)
    rr_mid = (base[0] + 8.0, base[1] - up * 0.42)
    rr_head = (base[0] - 8.0, base[1] - up * 0.80)
    mid = A.lerp(A.lerp(up_mid, fw_mid, neck), rr_mid, rear)
    head = A.lerp(A.lerp(up_head, fw_head, neck), rr_head, rear)
    if sink:
        k = sink
        mid = (mid[0] + 6.0 * k, min(mid[1] + 40.0 * k, GROUND - 8.0))
        head = (head[0] + 6.0 * k, min(head[1] + 70.0 * k, GROUND - 9.0))
    low = _curve(base, (base[0] + 12.0 - 4.0 * neck, base[1] - (up * 0.25) * (1.0 - neck)), mid, 8)
    high = _curve(mid, (mid[0] - 8.0 * (1.0 - neck) * (1.0 - sink), (mid[1] + head[1]) * 0.5), head, 8)
    spine = low + high[1:]
    f.poly(_tube(spine, 6.4, 3.6), PLUME)
    f.ink(spine[2:-2], 0.6, PLUME_LIGHT)

    # The head: small, the bill red with a white band near its tip; the
    # bill points down when the neck is upright and forward in a lunge.
    pitch = (24.0 - 22.0 * neck + 10.0 * rear) * (1.0 - sink) + 6.0 * sink

    def Hd(*pts: Point) -> List[Point]:
        return K.turn([(head[0] + x, head[1] + y) for x, y in pts], head[0], head[1], pitch)

    f.poly(Hd((-6.0, -1.0), (-3.0, -5.0), (3.0, -5.0), (7.0, -2.0), (7.0, 3.0), (0.0, 4.0), (-5.0, 3.0)), PLUME)
    hinge = Hd((6.0, 1.0))[0]
    f.poly(K.turn(Hd((6.0, 1.0), (19.0, 2.6), (18.0, 4.0), (6.0, 3.6)), hinge[0], hinge[1], 24.0 * gape), BILL_SHADE)
    if gape > 0.2:
        f.poly(K.turn(Hd((7.0, 1.4), (16.0, 1.6), (8.0, 3.0)), hinge[0], hinge[1], 12.0 * gape), MOUTH, body=False)
    f.poly(Hd((6.0, -3.0), (14.0, -1.6), (20.0, 0.6), (20.0, 2.0), (6.0, 1.4)), BILL)
    f.poly(Hd((14.4, -1.4), (16.4, -0.8), (16.4, 1.7), (14.4, 1.6)), BILL_BAND, body=False)
    f.dot(*Hd((19.6, 1.2))[0], 0.8, BILL_SHADE)
    ex, ey = Hd((1.4, -1.4))[0]
    if eyes == "shut":
        f.ink([(ex - 1.6, ey), (ex + 1.6, ey + 0.3)], 0.9, CURL)
    else:
        r = {"open": 1.2, "wide": 1.6, "narrow": 0.8}[eyes]
        f.ellipse(ex, ey, r + 0.2, r, EYE, body=False)
        f.dot(ex + 0.4, ey - 0.3, 0.4, GLINT)
        if eyes == "narrow":
            f.ink([(ex - 2.2, ey - 2.0), (ex + 2.2, ey - 1.2)], 0.9, CURL)
    if hiss:
        # The hiss: short soft lines in front of the open bill.
        tip = Hd((22.0, 2.0))[0]
        for k in range(3):
            f.glow_line([(tip[0] + 3.0, tip[1] - 3.0 + k * 3.0), (tip[0] + 8.0, tip[1] - 4.0 + k * 4.0)], 0.8, K.alpha(K.WHITE, 0.6))
    if anim == "attack_side" and 0.15 < t < 0.65:
        # The swish of the lunge.
        for k in range(3):
            y = head[1] + 8.0 + k * 5.0
            f.glow_line([(head[0] - 30.0, y), (head[0] - 10.0, y - 2.0)], 1.0, K.alpha(K.WHITE, 0.55))
    for k in range(feathers):
        # Loose feathers knocked out by a hit: black, and one white.
        px = bx + rng.uniform(-20.0, 30.0)
        py = by + rng.uniform(-36.0, 0.0)
        a = rng.uniform(0.0, 180.0)
        quill = K.turn([(px - 4.0, py), (px, py - 1.2), (px + 4.0, py), (px, py + 1.2)], px, py, a)
        f.poly(quill, WHITE if k == 0 else PLUME_LIGHT)
    if anim == "death" and t > 0.3:
        A.dust(f, bx + 4.0, GROUND - 10.0, 20.0, min(1.0, (t - 0.3) * 2.0), f"black_swan:death:{i}")
    if alarm:
        A.alarm_mark(f, head[0] + 12.0, max(16.0, head[1] - 18.0))
    return A.finish(f, fade=fade, width=1.4)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
