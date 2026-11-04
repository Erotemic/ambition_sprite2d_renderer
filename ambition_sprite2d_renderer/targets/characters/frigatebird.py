"""The Frigatebird of the History dimension: the great frigatebird of the open Pacific.

A black seabird made of wings: long, narrow, crooked at the wrist and
sharp at the tips, with a deeply forked tail like open scissors. Its body
is small, with a gloss of purple on its back; its bill is long, grey and
hooked. The male puffs his throat pouch into a big red balloon. The bird
cannot land on the water (its feathers are not waterproof), so it sleeps
on land: a navigator who sees one at dusk knows land is near.

It flies. Its idle row glides on slow beats of its wings; its walk flies
on. When it sees you it flares its wings and puffs its pouch. Its windup
lifts its wings high and points its bill down at you; its strike is the
swoop: the wings swept back, the hooked bill first, as it snatches a fish
from another bird. A hit knocks feathers out of it; at its death it
tumbles out of the air.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import List

from . import _art_cast_kit as K
from . import _history_americas_kit as A
from . import _history_steppe_kit as H

TARGET_NAME = "frigatebird"
FRAME_SIZE = (192, 128)
ROWS = K.ENEMY_ROWS
#: The bird is drawn in small units and made this much larger.
BIRD = 1.2

ACTOR_METADATA = A.enemy_metadata(
    TARGET_NAME, "Frigatebird", "wayfinders", "Avian", "Small", "Light", "Float", ["bird", "seabird", "floating", "pouch"],
    "A great frigatebird of the History dimension's open ocean: black, with long crooked wings, a forked tail and a red "
    "throat pouch puffed up. It glides, lifts its wings high, and swoops at you hooked bill first.",
)

FEATHER = (44, 40, 50, 255)
FEATHER_SHADE = (26, 24, 32, 255)
GLOSS = (92, 78, 124, 255)
GLOSS_GREEN = (70, 104, 96, 255)
BILL = (176, 182, 188, 255)
BILL_SHADE = (120, 126, 136, 255)
POUCH = (226, 40, 44, 255)
POUCH_LIGHT = (252, 120, 104, 255)
POUCH_SHADE = (166, 22, 30, 255)
FOOT = (196, 150, 150, 255)
EYE_RING = (90, 84, 96, 255)


def _wing(pen: H.ScaledPen, sx: float, sy: float, angle: float, colour, shade, crook: float = 1.0) -> None:
    """A long narrow wing from the shoulder at (`sx`, `sy`). It is drawn as
    if it points straight up, then turned back by `angle` degrees (0 up, 90
    back along the body, 150 down and back). `crook` bends it at the wrist."""

    def T(pts):
        return K.turn([(sx + x, sy + y) for x, y in pts], sx, sy, -angle)

    wx, wy = 6.0 * crook, -22.0
    tip = (-16.0 * crook - 6.0, -56.0)
    # One long blade: the arm up to the crook of the wrist, the hand back
    # to the sharp tip.
    blade = [(4.0, 3.0), (wx + 2.0, wy + 2.0), (wx, wy - 4.0), tip, (-7.0 * crook - 6.0, -31.0), (-6.0, wy + 1.0), (-14.0, -2.0), (-10.0, 4.0)]
    pen.poly(T(blade), colour)
    # The hand feathers in shade along the trailing edge, a gloss on the arm.
    pen.poly(T([(wx - 3.0, wy - 2.0), tip, (-7.0 * crook - 6.0, -31.0), (-6.0, wy + 1.0)]), shade, body=False)
    pen.poly(T([(3.0, 1.0), (wx + 1.0, wy + 2.0), (wx - 2.0, wy), (-1.0, -2.0)]), GLOSS, body=False)
    pen.ink(T([(wx - 1.0, wy - 2.0), ((wx + tip[0]) / 2.0 - 1.0, (wy + tip[1]) / 2.0)]), 0.6, K.shade(colour, 1.4))


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    rng = random.Random(f"frigatebird:{anim}:{i}")
    f = K.Frame(FRAME_SIZE)
    cx, cy, tilt = 98.0, 78.0, 0.0
    wing, crook, pouch, bill_open, eyes, alarm, fade = 60.0, 1.0, 0.75, 0.0, "open", False, 1.0
    feathers, swipe, fork = 0, 0.0, 1.0
    if anim == "idle":
        cy += 3.0 * math.sin(cyc + math.pi / 2.0)
        wing = 66.0 + 32.0 * math.sin(cyc)
        tilt = -2.0
        fork = 0.8 + 0.2 * math.sin(cyc)
    elif anim == "walk":
        cy += 2.0 * math.sin(cyc * 2.0 + 1.0)
        wing = 74.0 + 36.0 * math.sin(cyc * 2.0)
        tilt, cx = 5.0, 100.0
        fork = 0.6
    elif anim == "notice":
        k = math.sin(math.pi * min(1.0, t * 1.4))
        wing, crook, tilt, pouch, bill_open, eyes, alarm = 66.0 - 34.0 * k, 1.3, -10.0 * k, 0.75 + 0.35 * k, 0.6 * k, "wide", True
        cy -= 4.0 * k
        fork = 1.0 + 0.4 * k
    elif anim == "windup":
        wing = 30.0 + 4.0 * math.sin(cyc * 2.0)
        tilt, eyes, crook, pouch = 20.0, "narrow", 1.3, 0.9
        cx, cy = 96.0, 84.0 + 1.0 * math.sin(cyc * 2.0)
        fork = 1.3
    elif anim == "attack_side":
        # The swoop (0..3), down and forward, wings back; then it pulls up.
        u = min(1.0, t / 0.6)
        back = max(0.0, (t - 0.6) / 0.4)
        cx = 92.0 + 16.0 * u - 6.0 * back
        cy = 62.0 + 16.0 * math.sin(math.pi * 0.5 * u) - 12.0 * back
        tilt = 30.0 * (1.0 - u) + 8.0 * u - 20.0 * back
        wing = 118.0 - 60.0 * back
        eyes, crook, bill_open, pouch, fork = "narrow", 0.6, 0.8 * u * (1.0 - back), 0.55, 0.3
        swipe = math.sin(math.pi * min(1.0, t * 1.4))
    elif anim == "hit":
        k = math.sin(math.pi * (i + 1) / (n + 1))
        cx, tilt, wing, eyes, bill_open, pouch = 98.0 - 6.0 * k, -12.0 * k, 44.0, "shut", 0.7, 0.5
        feathers = 5
    elif anim == "death":
        fall = t
        cx = 100.0 - 6.0 * fall
        cy = 68.0 + 8.0 * fall * fall
        tilt = 15.0 + 75.0 * fall
        wing, crook, eyes, bill_open, pouch = 40.0 + 70.0 * fall, 1.4, "shut", 0.5, 0.75 - 0.5 * fall
        feathers = 3 + int(5 * fall)
        fade = 1.0 - max(0.0, t - 0.7) / 0.3

    pen = H.ScaledPen(f, (cx, cy), tilt, (0.0, 0.0), BIRD)
    flat = H.ScaledPen(f)
    shoulder = (cx + 2.0, cy - 4.0)

    # The far wing, behind it all, a little out of step.
    _wing(pen, shoulder[0] + 3.0, shoulder[1] - 1.0, wing - 12.0, FEATHER_SHADE, FEATHER_SHADE, crook)

    # The tail: two long prongs, open like scissors.
    root = (cx - 12.0, cy + 1.0)
    for s, colour in ((-1.0, FEATHER_SHADE), (1.0, FEATHER)):
        a = math.radians(180.0 + s * 15.0 * fork)
        tip = (root[0] + 36.0 * math.cos(a), root[1] + 36.0 * math.sin(a))
        mid = (root[0] + 15.0 * math.cos(a), root[1] + 15.0 * math.sin(a))
        nx, ny = -math.sin(a), math.cos(a)
        pen.poly([(root[0] + nx * 3.4, root[1] + ny * 3.4), (mid[0] + nx * 2.6, mid[1] + ny * 2.6), tip, (mid[0] - nx * 2.2, mid[1] - ny * 2.2),
                  (root[0] - nx * 3.4, root[1] - ny * 3.4)], colour)

    # The small feet, tucked under the body.
    pen.limb([(cx + 1.0, cy + 5.0), (cx - 4.0, cy + 8.0)], 1.8, FOOT)

    # The body: small and slim, black with a purple gloss on the back.
    body = [(cx + 14.0, cy - 4.0), (cx + 15.0, cy + 2.0), (cx + 8.0, cy + 6.0), (cx - 6.0, cy + 6.0), (cx - 16.0, cy + 3.0), (cx - 16.0, cy - 1.0),
            (cx - 6.0, cy - 6.0), (cx + 6.0, cy - 7.0)]
    pen.poly(body, FEATHER)
    pen.poly([(cx - 12.0, cy - 2.4), (cx - 4.0, cy - 5.6), (cx + 8.0, cy - 6.4), (cx + 2.0, cy - 3.4)], GLOSS, body=False)
    pen.poly([(cx + 15.0, cy + 2.0), (cx + 8.0, cy + 6.0), (cx - 6.0, cy + 6.0), (cx - 16.0, cy + 3.0), (cx - 4.0, cy + 3.2), (cx + 8.0, cy + 2.6)],
             FEATHER_SHADE, body=False)

    # The red throat pouch, puffed up under the bill.
    hx, hy = cx + 18.0, cy - 8.0
    pr = 7.5 * pouch
    px, py = hx - 1.0, hy + 4.0 + pr * 0.7
    pen.ellipse(px, py, pr * 1.05, pr, POUCH)
    pen.ellipse(px + pr * 0.15, py + pr * 0.35, pr * 0.8, pr * 0.55, POUCH_SHADE, body=False)
    pen.ellipse(px - pr * 0.3, py - pr * 0.35, pr * 0.35, pr * 0.28, POUCH_LIGHT, body=False)

    # The head and neck: small, black, with a long hooked grey bill.
    pen.poly([(cx + 6.0, cy - 6.0), (hx - 4.0, hy - 4.0), (hx + 2.0, hy - 5.0), (hx + 5.0, hy - 1.0), (hx + 4.0, hy + 3.0), (hx - 2.0, hy + 4.0),
              (cx + 10.0, cy - 1.0)], FEATHER)
    pen.ink([(hx - 6.0, hy - 3.0), (hx + 1.0, hy - 4.2)], 0.6, GLOSS_GREEN)
    gape = 3.0 * bill_open
    # The lower bill, then the upper bill with its hook.
    pen.poly([(hx + 3.0, hy + 1.0 + gape * 0.3), (hx + 20.0, hy + 2.0 + gape), (hx + 19.0, hy + 3.4 + gape), (hx + 3.0, hy + 3.4)], BILL_SHADE)
    pen.poly([(hx + 3.0, hy - 2.6), (hx + 18.0, hy - 1.4), (hx + 22.0, hy + 0.4), (hx + 22.0, hy + 3.6), (hx + 19.6, hy + 1.6), (hx + 3.0, hy + 1.4)], BILL)
    pen.ink([(hx + 5.0, hy - 0.6), (hx + 18.0, hy + 0.2)], 0.5, BILL_SHADE)
    if bill_open > 0.3:
        pen.poly([(hx + 4.0, hy + 1.4), (hx + 16.0, hy + 1.8), (hx + 16.0, hy + 1.8 + gape * 0.8), (hx + 4.0, hy + 2.6)], POUCH_SHADE, body=False)
    ex, ey = hx + 0.4, hy - 1.0
    if eyes == "shut":
        pen.ink([(ex - 1.6, ey), (ex + 1.6, ey + 0.4)], 0.8, BILL)
    else:
        r = 1.8 if eyes == "wide" else 1.4
        pen.ellipse(ex, ey, r + 0.5, r + 0.5, EYE_RING, body=False)
        pen.dot(ex + 0.2, ey, r * 0.6, (16, 14, 18, 255))
        pen.dot(ex - 0.3, ey - 0.4, 0.4, K.WHITE)
        if eyes == "narrow":
            pen.poly([(ex - 2.6, ey - 2.4), (ex + 2.8, ey - 1.4), (ex + 2.8, ey - 0.4), (ex - 2.0, ey - 1.2)], FEATHER, body=False)

    # The near wing, over the body.
    _wing(pen, shoulder[0], shoulder[1], wing, FEATHER, FEATHER_SHADE, crook)

    if swipe > 0.1:
        # The streak of the swoop behind it, and the snap of the bill.
        for k in range(3):
            x0, y0 = pen.at(cx - 20.0, cy - 4.0 + k * 5.0)
            f.glow_line([(x0, y0), (x0 - 16.0, y0 - 12.0)], 1.6, K.alpha(K.WHITE, 0.7 * swipe))
        tx, ty = pen.at(hx + 24.0, hy + 2.0)
        for k in range(3):
            f.glow_line([(tx + k * 3.0, ty - 5.0), (min(186.0, tx + 5.0 + k * 3.0), ty + 4.0)], 1.4, K.alpha(A.SEA, 0.85 * swipe))
    for k in range(feathers):
        qx = cx + rng.uniform(-34.0, 30.0)
        qy = cy + rng.uniform(-34.0, 24.0) + (10.0 * t if anim == "death" else 0.0)
        qx, qy = min(180.0, max(12.0, qx)), min(118.0, max(10.0, qy))
        a = rng.uniform(0.0, 180.0)
        quill = K.turn([(qx - 4.0, qy), (qx, qy - 1.6), (qx + 4.0, qy), (qx, qy + 1.6)], qx, qy, a)
        flat.poly(quill, FEATHER if k % 2 else GLOSS)
        flat.ink([quill[0], quill[2]], 0.5, FEATHER_SHADE)
    if alarm:
        ax, ay = pen.at(hx + 10.0, hy - 20.0)
        A.alarm_mark(f, min(180.0, ax), max(14.0, ay))
    return A.finish(f, fade=fade, width=1.4)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
