"""The Pacific Rat of the History dimension: the kiore, the Polynesian rat.

A small, slim brown rat with a pale belly, big round ears, a pointed pink
nose with long whiskers, and a long scaly tail. It came across the Pacific
on the voyaging canoes, island by island, with the people; on Rapa Nui it
ate the nuts of the great palms.

It is small and quick. Its idle row sniffs the air; its walk scurries in
bounds. When it sees you it sits up on its hind legs. Its windup crouches
low with its tail lashing; its strike is the dart: a long quick lunge and
a bite with its front teeth. A hit knocks it back with its fur on end; at
its death it rolls onto its back.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Tuple

from . import _art_cast_kit as K
from . import _history_americas_kit as A
from . import _history_steppe_kit as H

TARGET_NAME = "pacific_rat"
FRAME_SIZE = (96, 64)
ROWS = K.ENEMY_ROWS
GROUND = 58.0

ACTOR_METADATA = A.enemy_metadata(
    TARGET_NAME, "Pacific Rat", "rapa_nui", "Quadruped", "Small", "Light", "Walk", ["rat", "rodent", "bite", "fast"],
    "The Pacific rat (the kiore) of the History dimension's Rapa Nui: small, brown and quick, with big ears and a long "
    "tail. It crouches low, then darts in and bites.",
)

FUR = (140, 104, 76, 255)
FUR_SHADE = (100, 72, 52, 255)
FUR_LIGHT = (176, 140, 106, 255)
BELLY = (214, 192, 160, 255)
PINK = (226, 150, 150, 255)
PINK_SHADE = (184, 108, 112, 255)
TAIL = (204, 150, 140, 255)
TOOTH = (250, 230, 170, 255)
EYE = (20, 16, 18, 255)

Point = Tuple[float, float]


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = K.Frame(FRAME_SIZE)
    dx, dy, tilt, run, rear, crouch = 0.0, 0.0, 0.0, None, 0.0, 0.0
    sniff, mouth, eyes, alarm, fade, flip, bristle, lash = 0.0, 0.0, "open", False, 1.0, 0.0, 0.0, 0.0
    if anim == "idle":
        sniff = math.sin(cyc * 3.0)
        dy = 0.4 * math.sin(cyc)
        lash = 0.3 * math.sin(cyc)
    elif anim == "walk":
        run = t
        dy = -2.0 * abs(math.sin(cyc))
        tilt = 4.0 * math.sin(cyc)
        lash = 0.5 * math.sin(cyc)
    elif anim == "notice":
        k = math.sin(math.pi * min(1.0, t * 1.3))
        rear, eyes, alarm, sniff = k, "wide", True, 0.6 * math.sin(cyc * 4.0)
    elif anim == "windup":
        crouch, eyes = 1.0, "narrow"
        lash = math.sin(cyc * 2.0)
        dx = -1.0
        bristle = 0.5
    elif anim == "attack_side":
        # The dart (0..2), the bite (2..3), and back.
        u = min(1.0, t / 0.4)
        back = max(0.0, (t - 0.6) / 0.4)
        dx = -1.0 + 8.0 * math.sin(math.pi * 0.5 * u) - 7.0 * back
        crouch = max(0.0, 1.0 - 2.0 * u) + 0.3 * back
        tilt = 6.0 * u * (1.0 - back)
        mouth = 1.0 if 1 <= i <= 3 else 0.0
        eyes, run = "narrow", t * 2.0
    elif anim == "hit":
        k = math.sin(math.pi * (i + 1) / (n + 1))
        dx, tilt, eyes, bristle, mouth = -5.0 * k, -10.0 * k, "shut", k, 0.5
    elif anim == "death":
        flip = min(1.0, t * 1.5) ** 0.35
        eyes = "x"
        fade = 1.0 - max(0.0, t - 0.7) / 0.3

    cx, cy = 48.0 + dx, GROUND - 12.0 + dy + 4.0 * crouch
    rot = tilt - 24.0 * rear + 180.0 * flip
    shift = (-4.0 * flip, -9.0 * math.sin(math.pi * flip) - 12.0 * flip)
    pivot = (cx + 5.0, cy + 2.0) if flip else (cx - 12.0, cy + 8.0)
    pen = H.ScaledPen(f, pivot, rot, shift)

    # The tail: long and scaly, low behind it, with a lash at its tip.
    tail = []
    for k in range(9):
        u = k / 8.0
        x = cx - 16.0 - 22.0 * u * (1.0 - 0.55 * min(1.0, flip * 2.0))
        y = cy + 3.0 + 4.0 * u - 12.0 * u * u * (0.6 + 0.4 * math.sin(math.pi * u * 2.0 + lash)) - 6.0 * lash * u ** 2
        tail.append((x, y))
    pen.limb(tail[:5], 2.8, TAIL)
    pen.limb(tail[4:], 1.8, TAIL)
    for k in range(1, 8):
        x, y = tail[k]
        pen.ink([(x, y - 1.0), (x + 0.4, y + 1.0)], 0.5, PINK_SHADE)

    # The legs: two pairs, small pink feet.
    def leg(hip: Point, ph: float, near: bool, front: bool) -> None:
        colour = FUR if near else FUR_SHADE
        fx, fy = hip[0] + (2.0 if front else -2.0), GROUND - 1.0
        if run is not None:
            gx, gy = A.gait(ph, 12.0, 5.0)
            fx += gx
            fy += gy
        if rear and front:
            # Sitting up: the forepaws held up at the chest.
            fx, fy = hip[0] + 5.0, hip[1] + 4.0 - 4.0 * rear
        if crouch and not front:
            fx -= 3.0 * crouch
        mid = ((hip[0] + fx) / 2.0 + (2.0 if front else -3.0), (hip[1] + fy) / 2.0)
        pen.limb([hip, mid, (fx, fy)], 3.4 if not front else 2.6, colour)
        pen.limb([(fx - 1.0, fy), (fx + 2.6, fy)], 1.8, PINK)

    ph = run or 0.0
    leg((cx - 10.0, cy + 3.0), ph + 0.5, False, False)
    leg((cx + 9.0, cy + 4.0), ph, False, True)

    # The body: slim, arched over the hips, the belly pale.
    body = [(cx - 18.0, cy + 6.0), (cx - 18.0, cy - 2.0), (cx - 10.0, cy - 8.0 - 2.0 * bristle), (cx + 4.0, cy - 8.0 - 1.0 * bristle),
            (cx + 13.0, cy - 4.0), (cx + 14.0, cy + 4.0), (cx + 4.0, cy + 8.0), (cx - 10.0, cy + 9.0)]
    pen.poly(body, FUR)
    pen.poly([(cx - 14.0, cy + 6.0), (cx + 2.0, cy + 6.0), (cx + 12.0, cy + 3.0), (cx + 10.0, cy + 6.6), (cx + 2.0, cy + 8.6), (cx - 10.0, cy + 9.0)],
             BELLY, body=False)
    pen.poly([(cx - 14.0, cy - 3.0), (cx - 8.0, cy - 7.0), (cx + 4.0, cy - 7.0), (cx - 4.0, cy - 5.0)], FUR_LIGHT, body=False)
    if bristle:
        for k in range(6):
            x = cx - 14.0 + k * 4.4
            y = cy - 7.0 - (2.0 if 1 <= k <= 4 else 0.0) * bristle
            pen.limb([(x, y + 2.0), (x - 1.0, y - 2.0 * bristle)], 1.4, FUR_SHADE)

    leg((cx - 9.0, cy + 4.0), ph, True, False)
    leg((cx + 10.0, cy + 5.0), ph + 0.5, True, True)

    # The head: pointed, with a big round ear, a pink nose and whiskers.
    hx, hy = cx + 18.0, cy - 2.0
    head = [(hx - 8.0, hy - 6.0), (hx + 2.0, hy - 5.0), (hx + 10.0, hy + 1.0 + 0.4 * sniff), (hx + 9.0, hy + 3.4), (hx, hy + 6.0), (hx - 8.0, hy + 6.0)]
    pen.poly(head, FUR)
    pen.poly([(hx - 6.0, hy + 3.0), (hx + 6.0, hy + 3.0), (hx + 9.0, hy + 3.4), (hx, hy + 6.0), (hx - 6.0, hy + 6.0)], BELLY, body=False)
    pen.ellipse(hx + 10.4, hy + 1.6 + 0.4 * sniff, 1.6, 1.4, PINK)
    # The ear: round and thin, pink inside.
    ear_c = (hx - 5.0, hy - 8.0 - (1.0 if eyes == "wide" else 0.0))
    pen.ellipse(ear_c[0], ear_c[1], 4.6, 5.0, FUR_SHADE)
    pen.ellipse(ear_c[0] + 0.6, ear_c[1] + 0.4, 3.0, 3.4, PINK, body=False)
    # The mouth, and the front teeth when it bites.
    if mouth:
        pen.poly([(hx + 4.0, hy + 3.6), (hx + 9.0, hy + 3.6), (hx + 8.0, hy + 6.4), (hx + 3.0, hy + 5.4)], (90, 40, 44, 255))
        pen.poly([(hx + 7.0, hy + 3.4), (hx + 8.6, hy + 3.4), (hx + 8.2, hy + 5.4), (hx + 7.2, hy + 5.4)], TOOTH, body=False)
    else:
        pen.ink([(hx + 4.0, hy + 4.4), (hx + 8.0, hy + 3.8)], 0.6, FUR_SHADE)
    ex, ey = hx + 1.6, hy - 1.0
    if eyes == "shut":
        pen.ink([(ex - 1.4, ey), (ex + 1.4, ey + 0.4)], 0.8, EYE)
    elif eyes == "x":
        pen.ink([(ex - 1.2, ey - 1.2), (ex + 1.2, ey + 1.2)], 0.7, EYE)
        pen.ink([(ex - 1.2, ey + 1.2), (ex + 1.2, ey - 1.2)], 0.7, EYE)
    else:
        r = 1.9 if eyes == "wide" else 1.5
        pen.ellipse(ex, ey, r, r * (0.6 if eyes == "narrow" else 1.0), EYE, body=False)
        pen.dot(ex + 0.5, ey - 0.5, 0.45, K.WHITE)
    # The whiskers.
    wx, wy = hx + 9.0, hy + 2.0
    for k in range(3):
        a = math.radians(-14.0 + k * 14.0 + 6.0 * sniff)
        f.ink(pen.p([(wx, wy), (wx + math.cos(a) * 6.5, wy + math.sin(a) * 6.5)]), 0.4, K.alpha(K.WHITE, 0.8))

    if anim == "attack_side" and 1 <= i <= 3:
        tx, ty = pen.at(hx + 14.0, hy + 4.0)
        for k in range(3):
            a = math.radians(-50.0 + k * 50.0)
            f.glow_line([(tx + math.cos(a) * 2.0, ty + math.sin(a) * 2.0), (min(92.0, tx + math.cos(a) * 6.0), ty + math.sin(a) * 6.0)], 1.0,
                        K.alpha(K.WHITE, 0.9))
    if anim == "walk":
        A.dust(f, cx - 14.0, GROUND - 1.0, 8.0, 0.3 + 0.3 * abs(math.sin(cyc)), f"pacific_rat:walk:{i}", count=4)
    if alarm:
        A.alarm_mark(f, min(88.0, hx + 6.0), max(13.0, hy - 22.0))
    return A.finish(f, fade=fade, width=1.1)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
