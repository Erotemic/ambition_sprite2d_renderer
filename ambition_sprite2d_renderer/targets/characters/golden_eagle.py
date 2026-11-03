"""The Golden Eagle: a falconer's eagle of the Steppe, off its leash.

A big dark-brown eagle with the gold feathers on the back of its head and
neck that give it its name, a hooked yellow beak with a dark tip, a heavy
brow, feathered legs and yellow feet with black talons. Its leather hood is
off: it sits pushed back on its head like a cap, with its red plume, and
the falconer's leather straps (the jesses) hang from its legs.

It flies. Its idle row hovers on slow, deep beats of its wings; its walk
flies on. When it sees you it flares its wings and screams. Its windup lifts
its wings high and points its head down at you; its strike is the dive, the
wings swept back and the talons out in front, and it pulls up after. A hit
knocks feathers out of it; at its death it tumbles out of the air.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import List

from . import _art_cast_kit as K
from . import _history_steppe_kit as H

TARGET_NAME = "golden_eagle"
FRAME_SIZE = (128, 128)
ROWS = K.ENEMY_ROWS
#: The bird is drawn in small units and made this much larger.
BIRD = 1.22

ACTOR_METADATA = K.enemy_metadata(
    TARGET_NAME, "Golden Eagle", "Avian", "Small", "Light", "Float", ["history", "steppe", "bird", "eagle", "floating"],
    "A falconer's golden eagle of the Steppe in the History dimension, its leather hood pushed back on its head. It "
    "hovers on deep wing beats, lifts its wings high, and dives at you talons first.",
)

FEATHER = (110, 74, 48, 255)
FEATHER_SHADE = (72, 46, 30, 255)
FEATHER_DARK = (48, 30, 22, 255)
NAPE = (222, 168, 74, 255)
NAPE_LIGHT = (246, 210, 120, 255)
BEAK = (250, 204, 72, 255)
BEAK_TIP = (66, 62, 72, 255)
FOOT = (246, 200, 72, 255)
TALON = (34, 26, 24, 255)
LEATHER = (156, 82, 44, 255)
LEATHER_DARK = (104, 52, 30, 255)
TAIL_BASE = (178, 146, 104, 255)
WING = (142, 98, 58, 255)


def _wing(pen: H.ScaledPen, sx: float, sy: float, angle: float, colour, shade, spread: float = 1.0) -> None:
    """A wing from the shoulder at (`sx`, `sy`). It is drawn as if it points
    straight up, then turned back by `angle` degrees (0 up, 90 back along the
    body, 130 down and back). `spread` opens the long finger feathers."""

    def T(pts):
        return K.turn([(sx + x, sy + y) for x, y in pts], sx, sy, -angle)

    # The long feathers at the tip, spread as fingers, under the arm.
    for k in range(5):
        x0 = 5.0 - k * 2.8
        tip_x = 6.0 - k * 4.6 * spread
        tip_y = -44.0 + k * 2.2
        pen.poly(T([(x0 + 1.8, -20.0), (tip_x + 1.8, tip_y + 2.0), (tip_x, tip_y), (tip_x - 1.8, tip_y + 2.6), (x0 - 1.8, -20.0)]), shade)
        pen.ink(T([(x0 - 1.6, -21.0), (tip_x - 1.6, tip_y + 2.8)]), 0.6, K.shade(shade, 1.5))
    # The secondaries: a row of rounded feathers along the trailing edge.
    for k in range(4):
        y0 = -2.0 - k * 5.4
        pen.poly(T([(-10.0, y0 + 2.6), (-16.0, y0 + 0.6), (-16.4, y0 - 2.6), (-10.0, y0 - 3.4)]), shade)
    # The arm of the wing, with the coverts on it.
    arm = [(4.0, 2.0), (8.0, -12.0), (6.0, -23.0), (-6.0, -25.0), (-13.0, -14.0), (-12.0, 2.0)]
    pen.poly(T(arm), colour)
    pen.poly(T([(4.0, 2.0), (8.0, -12.0), (6.0, -23.0), (2.0, -23.0), (3.4, -12.0), (0.0, 2.0)]), NAPE, body=False)
    for k in range(3):
        y0 = -6.0 - k * 6.0
        pen.ink(T([(-1.0, y0), (-6.0, y0 + 1.6), (-11.0, y0 + 1.0)]), 0.7, K.alpha(shade, 0.9))


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    rng = random.Random(f"eagle:{anim}:{i}")
    f = K.Frame(FRAME_SIZE)
    cx, cy, tilt = 62.0, 72.0, 0.0
    wing, spread, legs, beak_open, eyes, alarm, fade = 45.0, 1.0, "tuck", 0.0, "fierce", False, 1.0
    feathers, swipe = 0, 0.0
    if anim == "idle":
        cy += 3.0 * math.sin(cyc + math.pi / 2.0)
        wing = 58.0 + 36.0 * math.sin(cyc)
        tilt = -3.0
    elif anim == "walk":
        cy += 2.0 * math.sin(cyc * 2.0 + 1.0)
        wing = 66.0 + 46.0 * math.sin(cyc * 2.0)
        tilt, cx = 6.0, 64.0
    elif anim == "notice":
        k = math.sin(math.pi * min(1.0, t * 1.4))
        wing, spread, tilt, beak_open, eyes, alarm = 58.0 - 36.0 * k, 1.3, -12.0 * k, k, "wide", True
        cy -= 4.0 * k
    elif anim == "windup":
        wing = 22.0 + 4.0 * math.sin(cyc * 2.0)
        tilt, legs, eyes, spread = 22.0, "reach", "narrow", 1.3
        cx, cy = 58.0, 64.0 + 1.0 * math.sin(cyc * 2.0)
    elif anim == "attack_side":
        # The dive (0..3), down and forward, wings back; then it pulls up.
        u = min(1.0, t / 0.6)
        back = max(0.0, (t - 0.6) / 0.4)
        cx = 58.0 + 14.0 * u - 4.0 * back
        cy = 64.0 + 18.0 * math.sin(math.pi * 0.5 * u) - 12.0 * back
        tilt = 34.0 * (1.0 - u) + 8.0 * u - 22.0 * back
        wing = 120.0 - 70.0 * back
        legs, eyes, spread, beak_open = "strike", "narrow", 0.5, 0.6 * u
        swipe = math.sin(math.pi * min(1.0, t * 1.4))
    elif anim == "hit":
        k = math.sin(math.pi * (i + 1) / (n + 1))
        cx, tilt, wing, eyes, beak_open = 62.0 - 6.0 * k, -18.0 * k, 20.0, "shut", 0.7
        feathers = 5
    elif anim == "death":
        fall = t
        cx = 66.0 - 4.0 * fall
        cy = 62.0 + 26.0 * fall * fall
        tilt = -40.0 - 120.0 * fall
        wing, spread, eyes, beak_open, legs = 30.0 + 80.0 * fall, 1.5, "shut", 0.5, "limp"
        feathers = 3 + int(5 * fall)
        fade = 1.0 - max(0.0, t - 0.7) / 0.3

    pen = H.ScaledPen(f, (cx, cy), tilt, (0.0, 0.0), BIRD)
    flat = H.ScaledPen(f)
    shoulder = (cx + 2.0, cy - 7.0)

    # The far wing, behind it all, a little out of step.
    _wing(pen, shoulder[0] + 3.0, shoulder[1] - 1.0, wing - 10.0, FEATHER_SHADE, FEATHER_DARK, spread)

    # The tail: a broad fan with a pale band.
    tail = [(cx - 14.0, cy - 2.0), (cx - 33.0, cy - 6.0), (cx - 35.0, cy + 1.0), (cx - 32.0, cy + 7.0), (cx - 13.0, cy + 5.0)]
    pen.poly(tail, FEATHER_SHADE)
    pen.poly([(cx - 15.0, cy - 2.4), (cx - 24.0, cy - 4.2), (cx - 25.0, cy + 5.8), (cx - 15.0, cy + 4.6)], TAIL_BASE, body=False)
    for k in range(3):
        pen.ink([(cx - 30.0, cy - 3.0 + k * 3.6), (cx - 34.0, cy - 4.0 + k * 4.6)], 0.6, FEATHER_DARK)

    # The legs: feathered trousers, the yellow feet, the jesses.
    if legs == "tuck":
        hips, feet = [(cx + 2.0, cy + 6.0)], [(cx - 4.0, cy + 15.0)]
    elif legs == "reach":
        hips, feet = [(cx + 4.0, cy + 6.0)], [(cx + 12.0, cy + 17.0)]
    elif legs == "strike":
        hips, feet = [(cx + 5.0, cy + 6.0)], [(cx + 20.0, cy + 12.0)]
    else:
        hips, feet = [(cx + 2.0, cy + 6.0)], [(cx + 4.0, cy + 17.0)]
    for hip, foot in zip(hips, feet):
        pen.limb([hip, ((hip[0] + foot[0]) / 2.0, (hip[1] + foot[1]) / 2.0)], 6.0, FEATHER)
        pen.limb([((hip[0] + foot[0]) / 2.0, (hip[1] + foot[1]) / 2.0), foot], 2.4, FOOT)
        # Toes and talons: open to strike, curled to fly.
        open_ = legs in ("reach", "strike")
        for k, a in enumerate((-50.0, 0.0, 45.0, 160.0)):
            a = math.radians(a + (0.0 if open_ else 40.0) + (tilt * 0.0))
            r = 4.6 if open_ else 3.0
            toe = (foot[0] + math.cos(a) * r, foot[1] + math.sin(a) * r)
            pen.limb([foot, toe], 1.6, FOOT)
            claw = (toe[0] + math.cos(a + 1.2) * 1.8, toe[1] + math.sin(a + 1.2) * 1.8)
            pen.limb([toe, claw], 1.0, TALON)
        # The jesses: two leather straps that trail behind.
        sway = math.sin(cyc + 1.0) * 1.5
        pen.ink([foot, (foot[0] - 5.0, foot[1] + 3.0 + sway), (foot[0] - 10.0, foot[1] + 3.0 + sway * 1.5)], 1.0, LEATHER)
        pen.ink([foot, (foot[0] - 4.0, foot[1] + 5.0 + sway), (foot[0] - 8.0, foot[1] + 6.0 + sway * 1.5)], 1.0, LEATHER_DARK)

    # The body: a heavy chest, the back, and the gold nape.
    body = [(cx + 14.0, cy - 6.0), (cx + 16.0, cy + 2.0), (cx + 8.0, cy + 9.0), (cx - 6.0, cy + 9.0), (cx - 16.0, cy + 4.0),
            (cx - 17.0, cy - 2.0), (cx - 8.0, cy - 8.0), (cx + 6.0, cy - 10.0)]
    pen.poly(body, FEATHER)
    pen.poly([(cx + 16.0, cy + 2.0), (cx + 8.0, cy + 9.0), (cx - 6.0, cy + 9.0), (cx - 16.0, cy + 4.0), (cx - 4.0, cy + 4.0), (cx + 8.0, cy + 3.0)],
             FEATHER_SHADE, body=False)
    for k in range(4):
        x = cx + 8.0 - k * 5.0
        pen.ink([(x, cy + 1.0), (x - 2.0, cy + 4.0), (x - 4.0, cy + 1.6)], 0.6, FEATHER_DARK)

    # The head: big and flat on top, the gold of the nape, a hooked beak.
    hx, hy = cx + 18.0, cy - 10.0
    pen.poly([(cx + 4.0, cy - 9.0), (hx - 4.0, hy - 6.0), (hx + 4.0, hy - 6.4), (hx + 7.0, hy - 2.0), (hx + 6.0, hy + 4.0), (hx - 2.0, hy + 7.0),
              (cx + 10.0, cy - 2.0)], FEATHER)
    pen.poly([(cx + 3.0, cy - 9.0), (hx - 5.0, hy - 6.4), (hx + 1.0, hy - 6.6), (hx - 1.0, hy - 2.0), (cx + 8.0, cy - 4.0)], NAPE, body=False)
    pen.ink([(hx - 6.0, hy - 5.0), (hx - 2.0, hy - 6.0)], 0.7, NAPE_LIGHT)
    # The beak: a yellow cere, the upper bill hooked down over the lower.
    gape = 2.4 * beak_open
    pen.poly([(hx + 4.0, hy + 2.0 + gape * 0.4), (hx + 11.0, hy + 3.0 + gape), (hx + 9.0, hy + 5.0 + gape), (hx + 3.0, hy + 4.4 + gape * 0.5)], BEAK)
    pen.poly([(hx + 4.0, hy - 3.0), (hx + 9.0, hy - 2.6), (hx + 13.0, hy + 0.6), (hx + 12.6, hy + 4.6), (hx + 10.6, hy + 2.0), (hx + 4.0, hy + 2.0)], BEAK)
    pen.poly([(hx + 11.0, hy - 1.0), (hx + 13.0, hy + 0.6), (hx + 12.6, hy + 4.6), (hx + 10.6, hy + 2.0)], BEAK_TIP, body=False)
    pen.dot(hx + 7.0, hy - 1.0, 0.6, FEATHER_DARK)
    if beak_open > 0.3:
        pen.poly([(hx + 5.0, hy + 2.2), (hx + 10.0, hy + 2.6), (hx + 9.0, hy + 2.4 + gape), (hx + 5.0, hy + 2.6 + gape * 0.5)], (150, 40, 40, 255), body=False)
    # The eye under a heavy brow.
    ex, ey = hx + 1.6, hy - 2.0
    if eyes == "shut":
        pen.ink([(ex - 1.6, ey), (ex + 1.6, ey + 0.4)], 0.8)
    else:
        r = 1.8 if eyes == "wide" else 1.5
        pen.ellipse(ex, ey, r, r, NAPE_LIGHT, body=False)
        pen.dot(ex + 0.4, ey + 0.2, 0.9, FEATHER_DARK)
        drop = 1.2 if eyes in ("fierce", "narrow") else 0.0
        pen.poly([(ex - 2.6, ey - 2.4), (ex + 2.8, ey - 1.6 + drop * 0.6), (ex + 2.8, ey - 0.6 + drop), (ex - 2.0, ey - 1.4)], FEATHER_DARK, body=False)

    # The hood, pushed back on its head like a cap, with its red plume.
    hood = [(hx - 7.0, hy - 4.0), (hx - 6.0, hy - 9.0), (hx - 1.0, hy - 11.0), (hx + 3.0, hy - 9.0), (hx + 2.0, hy - 5.6), (hx - 3.0, hy - 4.6)]
    pen.poly(hood, LEATHER)
    pen.poly([(hx - 7.0, hy - 4.0), (hx - 6.0, hy - 6.0), (hx + 2.4, hy - 7.0), (hx + 2.0, hy - 5.6), (hx - 3.0, hy - 4.6)], LEATHER_DARK, body=False)
    pen.ink([(hx - 6.0, hy - 6.2), (hx + 2.4, hy - 7.2)], 0.6, H.STEPPE_GOLD)
    # The knot of the hood's braces.
    pen.ellipse(hx - 1.0, hy - 11.0, 1.4, 1.2, H.STEPPE_GOLD)

    # The near wing, over the body.
    _wing(pen, shoulder[0], shoulder[1], wing, WING, FEATHER_DARK, spread)

    if swipe > 0.1:
        # The streak of the dive behind it.
        for k in range(3):
            x0, y0 = pen.at(cx - 20.0, cy - 6.0 + k * 6.0)
            f.glow_line([(x0, y0), (x0 - 16.0, y0 - 12.0)], 1.6, K.alpha(K.WHITE, 0.7 * swipe))
        tx, ty = pen.at(cx + 22.0, cy + 14.0)
        for k in range(3):
            f.glow_line([(tx - 2.0 + k * 3.0, ty - 5.0), (tx + 4.0 + k * 3.0, ty + 5.0)], 1.6, K.alpha(H.STEPPE_GOLD, 0.85 * swipe))
    for k in range(feathers):
        px = cx + rng.uniform(-30.0, 30.0)
        py = cy + rng.uniform(-30.0, 22.0) + (10.0 * t if anim == "death" else 0.0)
        px, py = min(118.0, max(10.0, px)), min(118.0, max(10.0, py))
        a = rng.uniform(0.0, 180.0)
        quill = K.turn([(px - 4.0, py), (px, py - 1.6), (px + 4.0, py), (px, py + 1.6)], px, py, a)
        flat.poly(quill, FEATHER if k % 2 else NAPE)
        flat.ink([quill[0], quill[2]], 0.5, FEATHER_DARK)
    if alarm:
        ax, ay = pen.at(hx + 10.0, hy - 18.0)
        H.alarm_mark(f, min(116.0, ax), max(14.0, ay))
    return f.finish(outline=H.SEPIA_INK, width=1.4, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
