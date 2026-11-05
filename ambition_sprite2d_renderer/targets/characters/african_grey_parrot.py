"""The African Grey Parrot of the History dimension: the grey parrot of the Congo forests.

The grey parrot (Psittacus erithacus) lives in the forests of Central and
West Africa, from the coast to the great forest of the Congo. It is the
size of a pigeon, but heavier. Its feathers are grey, paler on the head,
with a pale scalloped edge to each feather; the bare skin round its pale
eye is white; its strong hooked bill is black. Its short square tail is
bright red. Flocks fly fast and straight over the forest, and they call
and whistle; a grey parrot can copy many sounds and words.

It flies. Its idle row hovers on quick beats of its rounded wings; its
walk flies on. When it sees you it fans its red tail and lifts its crown.
Its windup pulls up, wings high, bill down at you; its strike is the swoop
and the peck: it dives on you wings back and snaps its hooked bill. A hit
knocks grey feathers out of it; at its death it tumbles out of the air.

The frame is 128 by 112 px; the parrot faces right.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import List

from . import _art_cast_kit as K
from . import _history_americas_kit as A
from . import _history_steppe_kit as H

TARGET_NAME = "african_grey_parrot"
FRAME_SIZE = (128, 112)
ROWS = K.ENEMY_ROWS
#: Nothing is drawn nearer the edge of the frame than this.
MARGIN = 5.0
#: The bird is drawn in small units and made this much larger.
BIRD = 1.35

ACTOR_METADATA = A.enemy_metadata(
    TARGET_NAME, "African Grey Parrot", "kongo", "Avian", "Small", "Light", "Float", ["bird", "parrot", "floating", "swoop"],
    "A grey parrot of the Congo forests in the History dimension's kingdom of Kongo: grey, with pale scalloped feathers, a white "
    "face, a black hooked bill and a bright red tail. It hovers, pulls up with its wings high, then swoops at you and pecks.",
)

GREY = (150, 152, 156, 255)
GREY_SHADE = (108, 110, 118, 255)
GREY_DARK = (78, 80, 88, 255)
GREY_LIGHT = (200, 202, 204, 255)
FACE = (238, 236, 230, 255)
RED = (206, 40, 38, 255)
RED_SHADE = (150, 26, 30, 255)
BILL = (36, 32, 34, 255)
BILL_LIGHT = (84, 80, 82, 255)
EYE = (236, 222, 168, 255)
FOOT = (120, 112, 112, 255)


def _wing(pen: H.ScaledPen, sx: float, sy: float, angle: float, colour, shade) -> None:
    """A broad wing with a rounded tip, from the shoulder at (`sx`, `sy`).
    It is drawn as if it points straight up, then turned back by `angle`
    degrees (0 up, 90 back along the body, 150 down and back)."""

    def T(pts):
        return K.turn([(sx + x, sy + y) for x, y in pts], sx, sy, -angle)

    blade = [(5.0, 3.0), (7.0, -12.0), (5.0, -24.0), (0.0, -31.0), (-6.0, -32.0), (-10.0, -27.0), (-12.0, -18.0), (-12.0, -8.0),
             (-9.0, 2.0)]
    pen.poly(T(blade), colour)
    # The flight feathers in a darker grey along the tip and the trailing
    # edge, the coverts paler with scalloped edges.
    pen.poly(T([(5.0, -22.0), (0.0, -31.0), (-6.0, -32.0), (-10.0, -27.0), (-12.0, -18.0), (-12.0, -10.0), (-5.0, -14.0), (1.0, -19.0)]), shade,
             body=False)
    for k in range(4):
        y = -6.0 - k * 4.0
        pen.ink(T([(3.0, y), (-1.0, y + 1.6), (-5.0, y + 0.6)]), 0.6, GREY_LIGHT)
    for k in range(4):
        x = -11.0 + k * 3.6
        pen.ink(T([(x + 1.0, -14.0 - k * 2.0), (x - 0.4, -26.0 - k * 1.0)]), 0.5, GREY_DARK)


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    rng = random.Random(f"african_grey_parrot:{anim}:{i}")
    f = K.Frame(FRAME_SIZE)
    cx, cy, tilt = 60.0, 64.0, 0.0
    wing, fan, crest, bill_open, eyes, alarm, fade = 60.0, 0.4, 0.0, 0.0, "open", False, 1.0
    feathers, swipe, peck = 0, 0.0, 0.0
    if anim == "idle":
        # It hovers on quick beats.
        cy += 2.0 * math.sin(cyc * 2.0 + math.pi / 2.0)
        wing = 70.0 + 50.0 * math.sin(cyc * 2.0)
        tilt = -12.0
    elif anim == "walk":
        # It flies on, fast and straight.
        cy += 1.6 * math.sin(cyc * 2.0 + 1.0)
        wing = 74.0 + 46.0 * math.sin(cyc * 2.0)
        tilt, cx = 4.0, 62.0
    elif anim == "notice":
        # It flares its wings, fans its red tail and lifts its crown.
        k = math.sin(math.pi * min(1.0, t * 1.4))
        wing, tilt, fan, crest, bill_open, eyes, alarm = 40.0 - 20.0 * k, -16.0 * k, 0.4 + 0.6 * k, k, 0.5 * k, "wide", True
        cy -= 3.0 * k
    elif anim == "windup":
        # It pulls up, wings high, bill pointed down at you.
        wing = 18.0 + 6.0 * math.sin(cyc * 2.0)
        tilt, eyes, fan, crest = 24.0, "narrow", 0.9, 0.6
        cx, cy = 56.0, 56.0 + 1.0 * math.sin(cyc * 2.0)
    elif anim == "attack_side":
        # The swoop (0..3), down and forward, wings back, and the peck;
        # then it pulls up.
        u = min(1.0, t / 0.6)
        back = max(0.0, (t - 0.6) / 0.4)
        cx = 54.0 + 18.0 * u - 8.0 * back
        cy = 52.0 + 18.0 * math.sin(math.pi * 0.5 * u) - 12.0 * back
        tilt = 34.0 * (1.0 - u) + 10.0 * u - 22.0 * back
        wing = 124.0 - 64.0 * back
        eyes, fan = "narrow", 0.3
        swipe = math.sin(math.pi * min(1.0, t * 1.4))
        peck = 1.0 if i in (2, 3) else 0.0
        bill_open = 0.9 if i == 2 else (0.2 if i == 3 else 0.4 * u)
    elif anim == "hit":
        k = math.sin(math.pi * (i + 1) / (n + 1))
        cx, tilt, wing, eyes, bill_open, fan = 60.0 - 6.0 * k, -14.0 * k, 40.0, "shut", 0.6, 0.8
        feathers = 5
    elif anim == "death":
        fall = t
        cx = 62.0 - 4.0 * fall
        cy = 56.0 + 14.0 * fall * fall
        tilt = 15.0 + 75.0 * fall
        wing, eyes, bill_open, fan = 40.0 + 70.0 * fall, "shut", 0.4, 0.5
        feathers = 3 + int(4 * fall)
        fade = 1.0 - max(0.0, t - 0.7) / 0.3

    pen = H.ScaledPen(f, (cx, cy), tilt, (0.0, 0.0), BIRD)
    flat = H.ScaledPen(f)
    shoulder = (cx + 2.0, cy - 5.0)

    # The far wing, behind it all, a little out of step.
    _wing(pen, shoulder[0] + 3.0, shoulder[1] - 1.0, wing - 14.0, GREY_SHADE, GREY_DARK)

    # The short square red tail: it fans when the bird is alarmed.
    root = (cx - 12.0, cy + 2.0)
    spread = 6.0 + 10.0 * fan
    for s, colour in ((-1.0, RED_SHADE), (0.0, RED), (1.0, RED)):
        a = math.radians(180.0 + 6.0 + s * spread)
        tip = (root[0] + 16.0 * math.cos(a), root[1] + 16.0 * math.sin(a))
        nx, ny = -math.sin(a), math.cos(a)
        pen.poly([(root[0] + nx * 3.4, root[1] + ny * 3.4), (tip[0] + nx * 3.2, tip[1] + ny * 3.2), (tip[0] - nx * 3.2, tip[1] - ny * 3.2),
                  (root[0] - nx * 3.4, root[1] - ny * 3.4)], colour)
    # The red under the tail (the vent).
    pen.poly([(cx - 14.0, cy + 1.0), (cx - 6.0, cy + 6.0), (cx - 9.0, cy + 7.6), (cx - 15.0, cy + 4.0)], RED)

    # The grey feet, tucked under the body.
    pen.limb([(cx + 2.0, cy + 7.0), (cx - 2.0, cy + 10.0)], 2.2, FOOT)
    pen.ink([(cx - 2.0, cy + 10.0), (cx + 1.0, cy + 11.0)], 0.8, FOOT)

    # The body: plump and grey, paler on the breast, the feathers edged pale.
    body = [(cx + 13.0, cy - 6.0), (cx + 15.0, cy + 2.0), (cx + 9.0, cy + 8.0), (cx - 4.0, cy + 9.0), (cx - 14.0, cy + 4.0), (cx - 15.0, cy - 1.0),
            (cx - 6.0, cy - 7.0), (cx + 4.0, cy - 9.0)]
    pen.poly(body, GREY)
    pen.poly([(cx + 15.0, cy + 2.0), (cx + 9.0, cy + 8.0), (cx - 4.0, cy + 9.0), (cx - 14.0, cy + 4.0), (cx - 2.0, cy + 4.0), (cx + 8.0, cy + 3.0)],
             GREY_SHADE, body=False)
    for k in range(5):
        x, y = cx + 10.0 - k * 4.4, cy - 2.0 + (k % 2) * 3.0
        pen.ink([(x - 2.0, y - 0.6), (x, y + 1.0), (x + 2.0, y - 0.6)], 0.6, GREY_LIGHT)

    # The head: big and round, paler grey, with a crown that lifts.
    hx, hy = cx + 16.0, cy - 9.0
    pen.ellipse(hx, hy, 8.4, 7.6, GREY_LIGHT)
    pen.poly([(hx - 8.0, hy + 1.0), (hx - 4.0, hy + 6.6), (hx + 2.0, hy + 7.4), (hx - 2.0, hy + 3.0)], GREY, body=False)
    if crest > 0.05:
        for k in range(3):
            bx, by = hx - 5.0 + k * 3.0, hy - 6.0
            pen.ink([(bx, by), (bx - 2.0 - 1.0 * k, by - 3.0 * crest - 1.0)], 1.4, GREY_LIGHT)
    for k in range(3):
        pen.ink([(hx - 6.0 + k * 2.6, hy - 2.0 + k * 0.6), (hx - 4.6 + k * 2.6, hy - 0.6 + k * 0.6)], 0.5, GREY)
    # The bare white face round the eye.
    pen.ellipse(hx + 2.6, hy - 1.2, 4.4, 3.6, FACE, body=False)
    # The black hooked bill: the upper bill hooks down over the lower.
    gape = 3.0 * bill_open
    bx, by = hx + 6.6, hy + 1.0
    pen.poly([(bx, by + 0.6), (bx + 5.0, by + 1.0 + gape), (bx + 4.0, by + 3.4 + gape), (bx, by + 3.6)], BILL)
    pen.poly([(bx - 0.6, by - 4.0), (bx + 3.6, by - 4.4), (bx + 6.6, by - 1.8), (bx + 7.4, by + 2.0), (bx + 6.0, by + 4.0), (bx + 5.0, by + 1.4),
              (bx, by + 1.2)], BILL)
    pen.ink([(bx + 1.0, by - 3.4), (bx + 5.0, by - 2.6)], 0.6, BILL_LIGHT)
    ex, ey = hx + 3.0, hy - 1.6
    if eyes == "shut":
        pen.ink([(ex - 1.6, ey), (ex + 1.6, ey + 0.4)], 0.8, GREY_DARK)
    else:
        r = 1.8 if eyes == "wide" else 1.4
        pen.ellipse(ex, ey, r, r, EYE, body=False)
        pen.dot(ex + 0.3, ey, r * 0.5, (20, 18, 20, 255))
        if eyes == "narrow":
            pen.poly([(ex - 2.4, ey - 2.4), (ex + 2.6, ey - 1.4), (ex + 2.6, ey - 0.4), (ex - 2.0, ey - 1.2)], GREY_LIGHT, body=False)

    # The near wing, over the body.
    _wing(pen, shoulder[0], shoulder[1], wing, GREY, GREY_SHADE)

    if swipe > 0.1:
        # The streak of the swoop behind it.
        for k in range(3):
            x0, y0 = pen.at(cx - 18.0, cy - 4.0 + k * 5.0)
            f.glow_line([(x0, y0), (max(MARGIN + 2.0, x0 - 14.0), max(MARGIN + 2.0, y0 - 10.0))], 1.4, K.alpha(K.WHITE, 0.7 * swipe))
    if peck:
        # The snap of the bill: short lines out from its tip.
        tx, ty = pen.at(bx + 8.0, by + 1.0)
        for k in (-1.0, 0.0, 1.0):
            f.glow_line([(tx + 1.0, ty + 3.0 * k), (min(FRAME_SIZE[0] - MARGIN - 2.0, tx + 6.0), ty + 5.0 * k)], 1.2, K.alpha(K.WHITE, 0.9))
    for k in range(feathers):
        qx = cx + rng.uniform(-28.0, 24.0)
        qy = cy + rng.uniform(-28.0, 20.0) + (8.0 * t if anim == "death" else 0.0)
        qx, qy = min(FRAME_SIZE[0] - 12.0, max(12.0, qx)), min(FRAME_SIZE[1] - 10.0, max(10.0, qy))
        a = rng.uniform(0.0, 180.0)
        quill = K.turn([(qx - 3.6, qy), (qx, qy - 1.5), (qx + 3.6, qy), (qx, qy + 1.5)], qx, qy, a)
        flat.poly(quill, GREY if k % 2 else GREY_LIGHT)
        flat.ink([quill[0], quill[2]], 0.5, GREY_DARK)
    if alarm:
        ax, ay = pen.at(hx + 6.0, hy - 18.0)
        A.alarm_mark(f, min(FRAME_SIZE[0] - 10.0, ax), max(16.0, ay))
    return A.finish(f, fade=fade, width=1.4)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
