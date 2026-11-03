"""The Hippo: a hippopotamus of the lakes of the Green Sahara, very angry.

A huge grey-purple barrel on four short legs, pink in its folds, with a
vast head: a broad square muzzle with the nostrils on top, little eyes and
little ears up on bumps, and a mouth that opens almost straight up and
down. Inside: pink gums, two long ivory tusks in the lower jaw and pegs of
teeth. It is always a little angry, and its mouth is always a little open.

It is heavy. Its walk is a slow waddle. When it sees you it yawns at you:
the jaws open wide (the threat of a hippo). Its windup lifts its head with
the mouth as wide as it goes and it paws the mud; its strike is a short
heavy charge, and the jaws come down shut. A hit makes it flinch and snort
water; at its death it rolls on its side.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Sequence, Tuple

from . import _art_cast_kit as K
from . import _history_africa_kit as H

TARGET_NAME = "hippo"
FRAME_SIZE = (192, 160)
ROWS = K.ENEMY_ROWS
GROUND = 153.0

ACTOR_METADATA = H.enemy_metadata(
    TARGET_NAME, "Hippo", "green_sahara", "Quadruped", "Large", "Heavy", "Walk", ["hippo", "beast", "charge", "jaws"],
    "A hippopotamus of the lakes of the Green Sahara in the History dimension, very angry, its mouth always a little open. "
    "It yawns its jaws wide as a threat, then charges a short way and bites down.",
)

HIDE = (126, 110, 134, 255)
HIDE_SHADE = (92, 78, 104, 255)
HIDE_LIGHT = (164, 148, 170, 255)
PINK = (226, 150, 150, 255)
PINK_SHADE = (190, 108, 116, 255)
GUM = (206, 92, 104, 255)
THROAT = (110, 36, 50, 255)
TUSK = (246, 238, 214, 255)
TUSK_SHADE = (204, 192, 160, 255)
DARK = (42, 30, 40, 255)
EYE = (240, 214, 120, 255)
WATER = (156, 210, 236, 255)

Point = Tuple[float, float]

#: The hippo is drawn at this size about the middle of its ground row.
SIZE = 0.74
#: The head is drawn this many times its first size: a hippo is mostly head.
HEAD = 1.22


def _rot(points: Sequence[Point], cx: float, cy: float, deg: float) -> List[Point]:
    return K.turn(points, cx, cy, deg)


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = H.ScaledFrame(FRAME_SIZE, SIZE, (96.0, GROUND))
    dx, dy, tilt, pitch, gape = 0.0, 0.0, 0.0, 0.0, 10.0
    gait, gait_amp, paw, speed, ears, eyes = 0.0, 0.0, 0.0, 0.0, 0.0, "angry"
    alarm, fade, fold, snort = False, 1.0, 0.0, 0.0
    if anim == "idle":
        # It stands and fumes: the ears flick, the mouth works.
        dy = 0.8 * math.sin(cyc)
        gape = 10.0 + 6.0 * max(0.0, math.sin(cyc))
        ears = math.sin(cyc * 3.0) if i in (2, 3) else 0.0
        snort = max(0.0, math.sin(cyc * 2.0 + 1.0)) * (1.0 if i < 2 else 0.0)
    elif anim == "walk":
        gait, gait_amp = cyc, 1.0
        dy = -1.4 * abs(math.sin(cyc))
        tilt = 1.5 * math.sin(cyc)
        pitch = 2.0 * math.sin(cyc * 2.0)
        gape = 8.0
    elif anim == "notice":
        # The yawn of a hippo: a threat. The jaws open wide.
        k = math.sin(math.pi * min(1.0, t * 1.2))
        gape, pitch, alarm, eyes = 10.0 + 60.0 * k, -8.0 * k, True, "wide"
    elif anim == "windup":
        # Head up and the mouth as wide as it goes; a forefoot paws the mud.
        gape, pitch, tilt, dx = 78.0 + 4.0 * math.sin(cyc * 2.0), -10.0, -2.0, -6.0
        paw = math.sin(cyc * 2.0)
        eyes = "angry"
    elif anim == "attack_side":
        # A short heavy charge, and the jaws slam shut (frame 3).
        u = min(1.0, t * 1.25)
        dx = -8.0 + 18.0 * math.sin(math.pi * 0.5 * u) - 10.0 * max(0.0, u - 0.75) / 0.25
        gape = 78.0 if i < 2 else (0.0 if i in (3, 4) else 14.0)
        pitch = -10.0 + 18.0 * min(1.0, i / 3.0)
        gait, gait_amp, speed = cyc * 1.5, 1.2, math.sin(math.pi * min(1.0, u * 1.4))
    elif anim == "hit":
        k = math.sin(math.pi * t)
        dx, tilt, pitch, gape, eyes, snort = -5.0 * k, -3.0 * k, -12.0 * k, 24.0, "shut", k
    elif anim == "death":
        fold = min(1.0, t / 0.75)
        tilt = -10.0 * fold
        dy = 10.0 * fold
        pitch, gape, eyes = 14.0 * fold, 20.0, "shut"
        fade = 1.0 - max(0.0, t - 0.75) / 0.25

    cx, cy = 66.0 + dx, GROUND - 60.0 + dy
    sh_x, hp_x = cx + 36.0, cx - 36.0

    def B(pts: Sequence[Point]) -> List[Point]:
        return _rot([(x + dx, y + dy) for x, y in pts], cx, cy, tilt)

    def leg(x: float, phase: float, near: bool) -> None:
        colour = HIDE if near else HIDE_SHADE
        top = B([(x - dx, GROUND - 40.0)])[0]
        swing = math.sin(phase) * gait_amp
        lift = max(0.0, math.cos(phase)) * 5.0 * gait_amp
        fx = top[0] + 7.0 * swing
        fy = GROUND - 4.0 - lift
        if paw and near and x - dx > cx - dx:
            fx, fy = top[0] + 5.0 * paw, GROUND - 4.0 - 7.0 * max(0.0, math.sin(cyc * 2.0 + 0.6))
        if fold:
            fx, fy = top[0] + 8.0 * fold, min(GROUND - 4.0, top[1] + 30.0 - 12.0 * fold)
        f.limb([top, (fx, fy - 6.0)], 20.0, colour)
        # The foot: a round stump with four toes.
        f.ellipse(fx + 1.0, fy - 1.0, 11.0, 5.0, colour)
        for k in range(3):
            f.ink([(fx - 5.0 + k * 5.0, fy + 1.0), (fx - 4.0 + k * 5.0, fy + 3.6)], 1.0, DARK)

    # The far legs.
    leg(hp_x + 8.0, gait + math.pi, False)
    leg(sh_x - 4.0, gait, False)

    # The little tail, a paddle with bristles.
    tail_root = B([(cx - 60.0, cy - 14.0)])[0]
    f.limb([tail_root, (tail_root[0] - 8.0, tail_root[1] + 10.0 + 2.0 * math.sin(cyc * 2.0))], 4.0, HIDE_SHADE)

    # The body: a huge barrel.
    body = B(K.ellipse_points(cx, cy, 62.0, 44.0, 36))
    f.poly(body, HIDE)
    f.poly(B([(cx - 60.0, cy + 16.0), (cx - 30.0, cy + 34.0), (cx + 20.0, cy + 38.0), (cx + 56.0, cy + 26.0), (cx + 50.0, cy + 34.0),
              (cx + 10.0, cy + 40.0), (cx - 34.0, cy + 37.0)]), PINK_SHADE, body=False)
    f.poly(B([(cx - 40.0, cy - 34.0), (cx + 10.0, cy - 40.0), (cx + 44.0, cy - 30.0), (cx + 20.0, cy - 32.0), (cx - 20.0, cy - 30.0)]), HIDE_LIGHT, body=False)
    # Folds of skin at the shoulder and the haunch, and a few scars.
    f.ink(B([(cx + 30.0, cy - 32.0), (cx + 24.0, cy - 6.0), (cx + 32.0, cy + 22.0)]), 1.6, HIDE_SHADE)
    f.ink(B([(cx - 36.0, cy - 30.0), (cx - 30.0, cy - 4.0), (cx - 38.0, cy + 22.0)]), 1.6, HIDE_SHADE)
    for k in range(3):
        f.ink(B([(cx - 8.0 + k * 10.0, cy - 18.0 + k * 4.0), (cx - 2.0 + k * 10.0, cy - 12.0 + k * 4.0)]), 1.2, PINK_SHADE)

    # The near legs.
    leg(hp_x, gait, True)
    leg(sh_x + 4.0, gait + math.pi, True)

    # The head: the jaws hinge at the back of the mouth. Each jaw turns about
    # the hinge: the upper one up, the lower one down. `pitch` turns both.
    hinge = B([(cx + 56.0, cy - 4.0)])[0]
    hx, hy = hinge
    up = -0.62 * gape + pitch + tilt
    lo = 0.38 * gape + pitch + tilt

    def U(pts: Sequence[Point]) -> List[Point]:
        return _rot([(hx + x * HEAD, hy + y * HEAD) for x, y in pts], hx, hy, up)

    def L(pts: Sequence[Point]) -> List[Point]:
        return _rot([(hx + x * HEAD, hy + y * HEAD) for x, y in pts], hx, hy, lo)

    # The neck and the back of the head, which do not open.
    f.poly(B([(cx + 46.0, cy - 34.0), (cx + 62.0, cy - 30.0), (cx + 74.0, cy - 6.0), (cx + 70.0, cy + 22.0), (cx + 48.0, cy + 30.0)]), HIDE)
    # The throat, in the dark of the open mouth.
    if gape > 4.0:
        f.poly([U([(4.0, -2.0)])[0], U([(30.0, -6.0)])[0], U([(50.0, -2.0)])[0], L([(50.0, 2.0)])[0], L([(30.0, 6.0)])[0], L([(4.0, 2.0)])[0]], THROAT)
        f.poly([U([(4.0, -1.0)])[0], U([(28.0, -4.0)])[0], L([(28.0, 4.0)])[0], L([(4.0, 1.0)])[0]], K.shade(THROAT, 0.7), body=False)
    # The lower jaw: a deep heavy chin, pink gums, two tusks.
    lower = L([(-4.0, 4.0), (16.0, 2.0), (46.0, 2.0), (56.0, 4.0), (58.0, 12.0), (52.0, 24.0), (30.0, 28.0), (6.0, 22.0), (-6.0, 14.0)])
    f.poly(lower, HIDE)
    f.poly(L([(10.0, 2.0), (54.0, 2.0), (56.0, 6.0), (10.0, 6.0)]), GUM, body=False)
    f.poly(L([(6.0, 20.0), (30.0, 26.0), (52.0, 22.0), (40.0, 27.0), (20.0, 27.0)]), PINK_SHADE, body=False)
    if gape > 6.0:
        for x in (20.0, 28.0, 36.0):
            f.poly(L([(x - 2.0, 3.0), (x + 2.0, 3.0), (x, -1.0)]), TUSK, body=False)
    # The tusks: long curved canines at the front of the lower jaw.
    for x0, near in ((46.0, False), (52.0, True)):
        tusk = L([(x0 - 3.0, 4.0), (x0 + 3.0, 4.0), (x0 + 4.0, -4.0), (x0 + 1.0, -12.0), (x0 - 2.0, -4.0)])
        f.poly(tusk, TUSK if near else TUSK_SHADE)
    # The upper jaw: the broad square muzzle with the nostrils on top.
    upper = U([(-6.0, -4.0), (-2.0, -26.0), (20.0, -32.0), (44.0, -30.0), (58.0, -26.0), (62.0, -16.0), (60.0, -4.0), (50.0, -2.0), (10.0, -2.0)])
    f.poly(upper, HIDE)
    f.poly(U([(10.0, -2.0), (50.0, -2.0), (58.0, -4.0), (56.0, -8.0), (10.0, -6.0)]), GUM, body=False)
    f.poly(U([(30.0, -28.0), (44.0, -30.0), (58.0, -26.0), (62.0, -16.0), (54.0, -22.0), (40.0, -26.0)]), HIDE_LIGHT, body=False)
    f.poly(U([(40.0, -6.0), (60.0, -4.0), (62.0, -16.0), (58.0, -10.0), (44.0, -10.0)]), PINK, body=False)
    if gape > 6.0:
        # The upper tusks and the pegs of teeth.
        for x in (22.0, 30.0, 38.0):
            f.poly(U([(x - 2.0, -3.0), (x + 2.0, -3.0), (x, 1.0)]), TUSK, body=False)
        f.poly(U([(50.0, -3.0), (55.0, -3.0), (53.0, 5.0)]), TUSK)
    # The nostrils, up on the top of the muzzle, and a snort of water.
    for x in (50.0, 56.0):
        nx, ny = U([(x, -29.0)])[0]
        f.ellipse(nx, ny, 2.4, 1.6, DARK, body=False)
    if snort > 0.1:
        nx, ny = U([(54.0, -34.0)])[0]
        for k in range(3):
            f.ellipse(nx + 4.0 + k * 5.0 * snort, ny - 4.0 - k * 4.0 * snort, 2.0 + k, 1.8 + k * 0.8, K.alpha(WATER, 0.85 * snort), body=False)
    # The eye and the ear on their bumps on top of the head (on the upper
    # jaw's turn, so they ride up when the mouth opens wide).
    ebx, eby = U([(4.0, -30.0)])[0]
    f.ellipse(ebx, eby, 9.0, 7.0, HIDE)
    ear = U([(-6.0, -30.0), (-10.0, -40.0 - 3.0 * ears), (-2.0, -34.0)])
    f.poly(ear, HIDE)
    f.poly(U([(-6.0, -32.0), (-8.6, -37.0 - 2.4 * ears), (-4.0, -34.0)]), PINK, body=False)
    ex, ey = ebx + 1.0, eby - 1.0
    if eyes == "shut":
        f.ink([(ex - 3.0, ey), (ex + 3.0, ey + 0.8)], 1.2, DARK)
    else:
        r = 2.6 if eyes == "wide" else 2.0
        f.ellipse(ex, ey, r + 0.6, r, EYE, body=False)
        f.dot(ex + 0.6, ey + 0.2, 1.2, DARK)
        if eyes == "angry":
            # A heavy brow, down at the front: it is angry.
            f.ink([(ex - 4.0, ey - 4.0), (ex + 4.0, ey - 1.6)], 1.8, DARK)

    if paw or speed > 0.1:
        H.dust(f, sh_x + 6.0, GROUND - 2.0, (0.6 + 0.4 * abs(paw)) if paw else speed, f"hippo:dust:{anim}:{i}", spread=1.4, colour=(170, 140, 110, 255))
    if anim == "attack_side" and i == 3:
        # The jaws slam shut: lines out from the bite.
        bx, by = U([(64.0, -2.0)])[0]
        for k in (-1.0, 0.0, 1.0):
            f.ink([(bx + 2.0, by + k * 6.0), (min(200.0, bx + 8.0), by + k * 10.0)], 1.6, K.alpha(K.WHITE, 0.95))
    if anim == "death" and t > 0.3:
        H.dust(f, cx, GROUND - 2.0, min(1.0, (t - 0.3) * 2.0), f"hippo:death:{i}", spread=3.0, colour=(170, 140, 110, 255))
    if alarm:
        H.alarm_mark(f, min(176.0, hx + 4.0), 22.0)
    return f.finish(outline=H.SEPIA_INK, width=1.7, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
