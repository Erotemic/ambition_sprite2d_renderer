"""Haast's Eagle of the History dimension: the great eagle of Aotearoa.

Haast's eagle (Hieraaetus moorei) of the South Island of Aotearoa was the
largest eagle that lived: a female weighed perhaps 15 kg, and its wings
spanned up to about 3 m. Its wings were short and broad for its weight, so
that it could fly fast between the trees. Its feet were huge, and its
talons were as long as a tiger's claws. It hunted moa, birds up to fifteen
times its own weight: it struck the moa's hips at speed with one foot and
the head or the neck with the other. It died out with the moa, about 1400.

It flies. Its idle row hovers on slow, deep beats of its broad wings; its
walk flies on. When it sees you it flares its wings and screams. Its
windup lifts its wings high, points its head down at you and swings its
feet forward; its strike is the stoop: it dives with its wings swept back
and its talons forward, and pulls up after. A hit knocks feathers out of
it; at its death it tumbles out of the air.

The bird is drawn in the units of the golden eagle (`golden_eagle.py`) and
made `R` times larger, in a frame of 240 by 240 px: its body is about
110 px long and its wings about 200 px from tip to tip when they are open.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import List

from . import _art_cast_kit as K
from . import _history_americas_kit as A
from . import _history_steppe_kit as H

TARGET_NAME = "haast_eagle"
FRAME_SIZE = (240, 240)
ROWS = K.ENEMY_ROWS
#: The frame is this much larger than the golden eagle's (128 px); every
#: place in the frame is given in the golden eagle's units and made this much larger.
R = 240.0 / 128.0
#: The bird is drawn in small units and made this much larger.
BIRD = 1.22 * R
#: Nothing is drawn nearer the edge of the frame than this.
MARGIN = 6.0

ACTOR_METADATA = A.enemy_metadata(
    TARGET_NAME, "Haast's Eagle", "aotearoa", "Avian", "Large", "Medium", "Float", ["bird", "eagle", "floating", "stoop", "talons"],
    "Haast's eagle of the History dimension's Aotearoa, the largest eagle that lived, which hunted the moa: dark brown, with "
    "short broad wings, a heavy pale beak and huge yellow feet with talons as long as a tiger's claws. It hovers on deep wing "
    "beats, lifts its wings high, and stoops on you with its talons forward.",
)

FEATHER = (96, 64, 44, 255)
FEATHER_SHADE = (66, 44, 32, 255)
FEATHER_DARK = (40, 28, 22, 255)
#: The rusty brown of the head and the nape.
NAPE = (160, 104, 62, 255)
NAPE_LIGHT = (204, 150, 96, 255)
#: The pale streaks of the breast and the bars of the tail.
STREAK = (212, 186, 140, 255)
BEAK = (226, 206, 150, 255)
BEAK_SHADE = (176, 152, 100, 255)
BEAK_TIP = (66, 62, 72, 255)
CERE = (238, 196, 76, 255)
FOOT = (240, 196, 70, 255)
FOOT_SHADE = (196, 150, 50, 255)
TALON = (34, 26, 24, 255)
WING = (124, 84, 54, 255)


def _wing(pen: H.ScaledPen, sx: float, sy: float, angle: float, colour, shade, spread: float = 1.0) -> None:
    """A broad wing from the shoulder at (`sx`, `sy`). It is drawn as if it
    points straight up, then turned back by `angle` degrees (0 up, 90 back
    along the body, 130 down and back). `spread` opens the finger feathers.
    It is shorter and broader than the golden eagle's: a forest eagle's."""

    def T(pts):
        return K.turn([(sx + x, sy + y) for x, y in pts], sx, sy, -angle)

    # The finger feathers at the tip: short, broad and wide apart.
    for k in range(6):
        x0 = 6.0 - k * 3.0
        tip_x = 7.0 - k * 4.4 * spread
        tip_y = -38.0 + k * 2.0
        pen.poly(T([(x0 + 2.2, -18.0), (tip_x + 2.2, tip_y + 2.2), (tip_x, tip_y), (tip_x - 2.2, tip_y + 2.8), (x0 - 2.2, -18.0)]), shade)
        pen.ink(T([(x0 - 1.8, -19.0), (tip_x - 1.8, tip_y + 3.0)]), 0.6, K.shade(shade, 1.5))
    # The secondaries: a row of broad rounded feathers along the trailing edge.
    for k in range(4):
        y0 = -1.0 - k * 5.0
        pen.poly(T([(-12.0, y0 + 2.8), (-19.0, y0 + 0.6), (-19.4, y0 - 3.0), (-12.0, y0 - 3.6)]), shade)
    # The arm of the wing, with the coverts on it.
    arm = [(5.0, 2.0), (9.0, -11.0), (7.0, -22.0), (-7.0, -24.0), (-15.0, -13.0), (-14.0, 2.0)]
    pen.poly(T(arm), colour)
    pen.poly(T([(5.0, 2.0), (9.0, -11.0), (7.0, -22.0), (3.0, -22.0), (4.0, -11.0), (1.0, 2.0)]), NAPE, body=False)
    for k in range(3):
        y0 = -5.0 - k * 6.0
        pen.ink(T([(-1.0, y0), (-7.0, y0 + 1.6), (-13.0, y0 + 1.0)]), 0.7, K.alpha(shade, 0.9))


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    rng = random.Random(f"haast:{anim}:{i}")
    f = K.Frame(FRAME_SIZE)
    # The pose, in the golden eagle's units: `cx`, `cy` the middle of the
    # body; `tilt` turns the bird (+ is head down); `wing` turns the wings.
    cx, cy, tilt = 62.0, 70.0, 0.0
    wing, spread, legs, beak_open, eyes, alarm, fade = 45.0, 1.0, "tuck", 0.0, "fierce", False, 1.0
    feathers, swipe = 0, 0.0
    if anim == "idle":
        cy += 3.0 * math.sin(cyc + math.pi / 2.0)
        wing = 58.0 + 34.0 * math.sin(cyc)
        tilt = -3.0
    elif anim == "walk":
        cy += 2.0 * math.sin(cyc * 2.0 + 1.0)
        wing = 66.0 + 44.0 * math.sin(cyc * 2.0)
        tilt, cx = 6.0, 64.0
    elif anim == "notice":
        k = math.sin(math.pi * min(1.0, t * 1.4))
        wing, spread, tilt, beak_open, eyes, alarm = 58.0 - 34.0 * k, 1.3, -12.0 * k, k, "wide", True
        cy -= 3.0 * k
    elif anim == "windup":
        wing = 24.0 + 4.0 * math.sin(cyc * 2.0)
        tilt, legs, eyes, spread = 22.0, "reach", "narrow", 1.3
        cx, cy = 58.0, 64.0 + 1.0 * math.sin(cyc * 2.0)
    elif anim == "attack_side":
        # The stoop (0..3), down and forward, wings back, talons forward;
        # then it pulls up.
        u = min(1.0, t / 0.6)
        back = max(0.0, (t - 0.6) / 0.4)
        cx = 56.0 + 12.0 * u - 4.0 * back
        cy = 62.0 + 14.0 * math.sin(math.pi * 0.5 * u) - 10.0 * back
        tilt = 30.0 * (1.0 - u) + 6.0 * u - 22.0 * back
        wing = 118.0 - 70.0 * back
        legs, eyes, spread, beak_open = "strike", "narrow", 0.5, 0.6 * u
        swipe = math.sin(math.pi * min(1.0, t * 1.4))
    elif anim == "hit":
        k = math.sin(math.pi * (i + 1) / (n + 1))
        cx, tilt, wing, eyes, beak_open = 62.0 - 6.0 * k, -18.0 * k, 22.0, "shut", 0.7
        feathers = 5
    elif anim == "death":
        fall = t
        cx = 64.0 - 4.0 * fall
        cy = 60.0 + 22.0 * fall * fall
        tilt = -40.0 - 120.0 * fall
        wing, spread, eyes, beak_open, legs = 30.0 + 70.0 * fall, 1.4, "shut", 0.5, "limp"
        feathers = 3 + int(5 * fall)
        fade = 1.0 - max(0.0, t - 0.7) / 0.3

    cx, cy = cx * R, cy * R
    pen = H.ScaledPen(f, (cx, cy), tilt, (0.0, 0.0), BIRD)
    flat = H.ScaledPen(f)
    shoulder = (cx + 2.0, cy - 7.0)

    # The far wing, behind it all, a little out of step.
    _wing(pen, shoulder[0] + 3.0, shoulder[1] - 1.0, wing - 10.0, FEATHER_SHADE, FEATHER_DARK, spread)

    # The tail: long and broad, with pale bars.
    tail = [(cx - 14.0, cy - 2.0), (cx - 37.0, cy - 6.0), (cx - 39.0, cy + 1.0), (cx - 36.0, cy + 8.0), (cx - 13.0, cy + 5.0)]
    pen.poly(tail, FEATHER_SHADE)
    for k in range(3):
        x = cx - 20.0 - k * 6.0
        pen.ink([(x, cy - 3.0 - k * 0.6), (x - 0.6, cy + 5.4 + k * 0.6)], 1.0, K.alpha(STREAK, 0.8))
    for k in range(3):
        pen.ink([(cx - 33.0, cy - 3.0 + k * 3.8), (cx - 38.0, cy - 4.0 + k * 4.8)], 0.6, FEATHER_DARK)

    # The legs: feathered trousers, then the bare yellow feet, thick and
    # huge, with long black talons.
    if legs == "tuck":
        hip, foot = (cx + 2.0, cy + 6.0), (cx - 4.0, cy + 15.0)
    elif legs == "reach":
        hip, foot = (cx + 4.0, cy + 6.0), (cx + 13.0, cy + 17.0)
    elif legs == "strike":
        hip, foot = (cx + 5.0, cy + 6.0), (cx + 21.0, cy + 11.0)
    else:
        hip, foot = (cx + 2.0, cy + 6.0), (cx + 4.0, cy + 17.0)
    open_ = legs in ("reach", "strike")
    for side, (dx, colour) in enumerate(((-2.0, FOOT_SHADE), (0.0, FOOT))):
        h = (hip[0] + dx, hip[1])
        ft = (foot[0] + dx * 1.5, foot[1] + (0.0 if side else -1.0))
        knee = ((h[0] + ft[0]) / 2.0, (h[1] + ft[1]) / 2.0)
        pen.limb([h, knee], 7.0, FEATHER if side else FEATHER_SHADE)
        pen.limb([knee, ft], 3.0, colour)
        # Toes and talons: wide open to strike, curled to fly.
        for k, a in enumerate((-55.0, -5.0, 45.0, 165.0)):
            a = math.radians(a + (0.0 if open_ else 40.0))
            r = 6.0 if open_ else 3.6
            toe = (ft[0] + math.cos(a) * r, ft[1] + math.sin(a) * r)
            pen.limb([ft, toe], 2.2, colour)
            claw = [toe, (toe[0] + math.cos(a + 0.9) * 2.4, toe[1] + math.sin(a + 0.9) * 2.4),
                    (toe[0] + math.cos(a + 1.7) * 3.4, toe[1] + math.sin(a + 1.7) * 3.4)]
            pen.limb(claw, 1.2, TALON)

    # The body: a heavy deep chest, the back, the streaked breast.
    body = [(cx + 14.0, cy - 6.0), (cx + 17.0, cy + 2.0), (cx + 9.0, cy + 10.0), (cx - 6.0, cy + 10.0), (cx - 16.0, cy + 4.0),
            (cx - 17.0, cy - 2.0), (cx - 8.0, cy - 8.0), (cx + 6.0, cy - 10.0)]
    pen.poly(body, FEATHER)
    pen.poly([(cx + 17.0, cy + 2.0), (cx + 9.0, cy + 10.0), (cx - 6.0, cy + 10.0), (cx - 16.0, cy + 4.0), (cx - 4.0, cy + 4.0), (cx + 8.0, cy + 3.0)],
             FEATHER_SHADE, body=False)
    for k in range(5):
        x = cx + 12.0 - k * 4.0
        pen.ink([(x, cy - 1.0 + k * 0.6), (x - 1.0, cy + 3.0 + k * 0.6)], 0.8, K.alpha(STREAK, 0.85))
    for k in range(4):
        x = cx + 6.0 - k * 5.0
        pen.ink([(x, cy + 5.0), (x - 2.0, cy + 8.0), (x - 4.0, cy + 5.6)], 0.6, FEATHER_DARK)

    # The head: big and flat on top, rusty brown, with a deep pale beak.
    hx, hy = cx + 18.0, cy - 10.0
    pen.poly([(cx + 4.0, cy - 9.0), (hx - 4.0, hy - 6.0), (hx + 4.0, hy - 6.4), (hx + 7.0, hy - 2.0), (hx + 6.0, hy + 4.0), (hx - 2.0, hy + 7.0),
              (cx + 10.0, cy - 2.0)], NAPE)
    pen.poly([(cx + 3.0, cy - 9.0), (hx - 5.0, hy - 6.4), (hx + 1.0, hy - 6.6), (hx - 1.0, hy - 2.0), (cx + 8.0, cy - 4.0)], NAPE_LIGHT, body=False)
    pen.poly([(cx + 10.0, cy - 2.0), (hx - 2.0, hy + 7.0), (hx - 6.0, hy + 9.0), (cx + 6.0, cy + 1.0)], FEATHER, body=False)
    # The beak: a yellow cere, a deep upper bill hooked down over the lower.
    gape = 2.6 * beak_open
    pen.poly([(hx + 4.0, hy + 2.0 + gape * 0.4), (hx + 12.0, hy + 3.4 + gape), (hx + 10.0, hy + 5.6 + gape), (hx + 3.0, hy + 4.8 + gape * 0.5)],
             BEAK_SHADE)
    pen.poly([(hx + 4.0, hy - 3.6), (hx + 10.0, hy - 3.0), (hx + 14.0, hy + 0.8), (hx + 13.6, hy + 5.2), (hx + 11.4, hy + 2.4), (hx + 4.0, hy + 2.4)],
             BEAK)
    pen.poly([(hx + 12.0, hy - 1.0), (hx + 14.0, hy + 0.8), (hx + 13.6, hy + 5.2), (hx + 11.4, hy + 2.4)], BEAK_TIP, body=False)
    pen.poly([(hx + 3.6, hy - 3.6), (hx + 6.6, hy - 3.4), (hx + 6.6, hy + 2.4), (hx + 3.6, hy + 2.4)], CERE, body=False)
    if beak_open > 0.3:
        pen.poly([(hx + 5.0, hy + 2.6), (hx + 11.0, hy + 3.0), (hx + 10.0, hy + 2.8 + gape), (hx + 5.0, hy + 3.0 + gape * 0.5)], (150, 40, 40, 255),
                 body=False)
    # The eye under a heavy brow.
    ex, ey = hx + 1.4, hy - 2.0
    if eyes == "shut":
        pen.ink([(ex - 1.6, ey), (ex + 1.6, ey + 0.4)], 0.8)
    else:
        r = 1.8 if eyes == "wide" else 1.5
        pen.ellipse(ex, ey, r, r, CERE, body=False)
        pen.dot(ex + 0.4, ey + 0.2, 0.9, FEATHER_DARK)
        drop = 1.2 if eyes in ("fierce", "narrow") else 0.0
        pen.poly([(ex - 2.6, ey - 2.4), (ex + 2.8, ey - 1.6 + drop * 0.6), (ex + 2.8, ey - 0.6 + drop), (ex - 2.0, ey - 1.4)], FEATHER_DARK, body=False)

    # The near wing, over the body.
    _wing(pen, shoulder[0], shoulder[1], wing, WING, FEATHER_DARK, spread)

    if swipe > 0.1:
        # The streak of the stoop behind it, and the flash of the talons.
        for k in range(3):
            x0, y0 = pen.at(cx - 20.0, cy - 6.0 + k * 6.0)
            f.glow_line([(x0, y0), (max(MARGIN + 4.0, x0 - 30.0), max(MARGIN + 4.0, y0 - 22.0))], 2.4, K.alpha(K.WHITE, 0.7 * swipe))
        tx, ty = pen.at(cx + 24.0, cy + 14.0)
        tx = min(FRAME_SIZE[0] - MARGIN - 14.0, tx)
        for k in range(3):
            f.glow_line([(tx - 4.0 + k * 5.0, ty - 9.0), (tx + 6.0 + k * 5.0, ty + 9.0)], 2.4, K.alpha(CERE, 0.85 * swipe))
    lo, hi = MARGIN + 10.0, FRAME_SIZE[0] - MARGIN - 10.0
    for k in range(feathers):
        px = cx + rng.uniform(-56.0, 56.0)
        py = cy + rng.uniform(-56.0, 40.0) + (18.0 * t if anim == "death" else 0.0)
        px, py = min(hi, max(lo, px)), min(hi, max(lo, py))
        a = rng.uniform(0.0, 180.0)
        quill = K.turn([(px - 7.0, py), (px, py - 2.8), (px + 7.0, py), (px, py + 2.8)], px, py, a)
        flat.poly(quill, FEATHER if k % 2 else NAPE)
        flat.ink([quill[0], quill[2]], 0.8, FEATHER_DARK)
    if alarm:
        ax, ay = pen.at(hx + 10.0, hy - 18.0)
        A.alarm_mark(f, min(FRAME_SIZE[0] - 16.0, ax), max(20.0, ay))
    return A.finish(f, fade=fade, width=1.6)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
