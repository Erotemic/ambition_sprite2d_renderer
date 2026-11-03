"""The Cave Lion: the great lion of the Ice Age, with no mane.

The lions that the painters of the caves drew had no manes: a big pale
cat, sandy grey, with faint stripes on its flanks and a long tail with a
dark tuft. A broad head with small round ears, a pale muzzle, whiskers and
amber eyes. It is longer and heavier than a lion of today.

It pounces. It walks with its head low and its shoulders rolling. When it
sees you it lifts its head and its ears go up. Its windup is the crouch of
a cat: belly to the ground, the hips up and wiggling, the tail tip
twitching. Its strike is the pounce: it leaps forward with its forepaws
out and its claws open, and lands. A hit makes it flinch and snarl; at its
death it rolls on its side.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Tuple

from . import _art_cast_kit as K
from . import _history_africa_kit as H
from . import _stage_kit as S

TARGET_NAME = "cave_lion"
FRAME_SIZE = (192, 128)
ROWS = K.ENEMY_ROWS
GROUND = 120.0

ACTOR_METADATA = H.enemy_metadata(
    TARGET_NAME, "Cave Lion", "ice_age", "Quadruped", "Large", "Heavy", "Walk", ["lion", "cat", "beast", "pounce"],
    "The great maneless lion of the Ice Age in the History dimension, as the cave painters drew it: a big pale cat with "
    "faint stripes and a tufted tail. It crouches with its hips wiggling, then pounces with its claws out.",
)

COAT = (214, 190, 148, 255)
COAT_SHADE = (170, 144, 104, 255)
COAT_LIGHT = (240, 228, 200, 255)
STRIPE = (178, 150, 110, 255)
TUFT = (82, 60, 42, 255)
NOSE = (150, 88, 80, 255)
DARK = (46, 32, 26, 255)
MOUTH = (150, 52, 56, 255)
EYE = (236, 178, 56, 255)
CLAW = (250, 246, 232, 255)

Point = Tuple[float, float]

#: The lion is drawn at this size about the middle of its ground row: the
#: frame must hold its pounce.
SIZE = 0.82
#: The head is drawn this many times its first size: a lion's head is big.
HS = 1.22


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = H.ScaledFrame(FRAME_SIZE, SIZE, (96.0, GROUND))
    dx, dy, tilt, crouch, rise = 0.0, 0.0, 0.0, 0.0, 0.0
    lope, head_up, jaw, ears, eyes = None, 0.0, 0.0, 0.0, "open"
    tail_swing, tail_twitch, alarm, lie, fade = 0.0, 0.0, False, 0.0, 1.0
    fore_reach, hind_push, hips_up = 0.0, 0.0, 0.0
    if anim == "idle":
        dy = 0.6 * math.sin(cyc)
        tail_swing = 0.5 * math.sin(cyc)
        head_up = 1.0 * math.sin(cyc + 1.0)
        tail_twitch = math.sin(cyc * 2.0)
    elif anim == "walk":
        lope = t
        dy = -1.4 * abs(math.sin(cyc))
        tilt = 1.2 * math.sin(cyc)
        head_up = -4.0
        tail_swing = 0.3 * math.sin(cyc + 1.0)
    elif anim == "notice":
        k = math.sin(math.pi * min(1.0, t * 1.3))
        head_up, ears, alarm, eyes = 7.0 * k, 1.0, True, "wide"
        jaw, tail_twitch = 0.25 * k, k
    elif anim == "windup":
        # The crouch: belly low, hips up and wiggling, tail tip twitching.
        crouch, head_up, hips_up = 14.0, -6.0, 6.0
        dx = -10.0 + 2.0 * math.sin(cyc * 2.0)
        tilt = -2.0 + 1.5 * math.sin(cyc * 2.0)
        eyes, ears, tail_twitch, jaw = "narrow", -0.6, math.sin(cyc * 3.0), 0.15
    elif anim == "attack_side":
        # The pounce: off the ground (1..3), forepaws out; it lands (4, 5).
        u = t
        air = math.sin(math.pi * min(1.0, u / 0.7)) if u < 0.7 else 0.0
        land = max(0.0, (u - 0.6) / 0.4)
        dx = -10.0 + 28.0 * min(1.0, u / 0.65) - 18.0 * land
        rise = 18.0 * air
        tilt = -12.0 * air + 6.0 * land * (1.0 - land) * 4.0
        fore_reach = air
        hind_push = air
        crouch = 6.0 * land
        jaw, eyes, ears = 0.9 * air + 0.3 * land, "narrow", -0.8
        tail_swing = 0.8
    elif anim == "hit":
        k = math.sin(math.pi * (i + 1) / (n + 1))
        dx, tilt, head_up, jaw, eyes, ears = -8.0 * k, -5.0 * k, 4.0 * k, 0.7, "shut", -1.0
    elif anim == "death":
        lie = min(1.0, t * 1.5)
        eyes, ears, jaw = "shut", -1.0, 0.2
        fade = 1.0 - max(0.0, t - 0.7) / 0.3

    hip = (54.0 + dx, GROUND - 52.0 + dy + crouch * 0.6 - hips_up - rise)
    shoulder = (116.0 + dx, GROUND - 54.0 + dy + crouch - rise)
    pivot = ((hip[0] + shoulder[0]) / 2.0, GROUND - 40.0)
    rot = tilt - 6.0 * lie
    pen = H.ScaledPen(f, pivot, rot, (0.0, 14.0 * lie))
    flat = H.ScaledPen(f)

    def leg(top: Point, phase_offset: float, hind: bool, colour) -> None:
        top_w = pen.at(*top)
        fx, fy = H.gait(lope + phase_offset, 30.0, 12.0) if lope is not None else (0.0, 0.0)
        foot_y = GROUND - 3.0 + fy
        if crouch and not lope:
            fx += (6.0 if not hind else -2.0)
        if rise:
            if hind:
                # The hind legs push out behind.
                fx, foot_y = -24.0 * hind_push, top_w[1] + 34.0 - 4.0 * hind_push
            else:
                # The forepaws reach out in front.
                fx, foot_y = 30.0 * fore_reach, top_w[1] + 22.0 - 12.0 * fore_reach
        if lie:
            ang = math.radians(90.0 - (40.0 if hind else -30.0) * lie)
            foot = (top_w[0] + math.cos(ang) * 24.0 + (10.0 * lie if not hind else -8.0 * lie), top_w[1] + math.sin(ang) * 44.0 * (1.0 - 0.55 * lie))
            foot = (foot[0], min(foot[1], GROUND - 3.0))
        else:
            foot = (top_w[0] + fx + (3.0 if not hind else -2.0), min(GROUND - 3.0, foot_y))
        down = math.hypot(foot[0] - top_w[0], foot[1] - top_w[1])
        l1, l2 = max(20.0, down * 0.52), max(20.0, down * 0.54)
        knee, foot = S.joint(top_w, foot, l1, l2, 1.0 if hind else -1.0)
        flat.limb([top_w, knee], 18.0 if hind else 15.0, colour)
        flat.limb([knee, foot], 10.0, colour)
        # The big round paw, and its claws out in the pounce.
        flat.ellipse(foot[0] + 2.0, foot[1] - 0.6, 7.0, 4.2, colour)
        for k in range(3):
            flat.ink([(foot[0] + 2.0 + k * 2.4, foot[1] - 1.0), (foot[0] + 2.6 + k * 2.4, foot[1] + 2.6)], 0.6, COAT_SHADE)
        if fore_reach > 0.3 and not hind:
            for k in range(3):
                cx, cy = foot[0] + 7.0, foot[1] - 2.0 + k * 2.4
                flat.poly([(cx, cy - 0.8), (cx + 4.0, cy + 0.6), (cx, cy + 0.9)], CLAW)

    # The far legs, in shade.
    leg((hip[0] + 6.0, hip[1] + 14.0), 0.1, True, COAT_SHADE)
    leg((shoulder[0] - 6.0, shoulder[1] + 16.0), 0.5, False, COAT_SHADE)

    # The tail: long, low, with a dark tuft. Its tip twitches.
    root = (hip[0] - 12.0, hip[1] - 4.0)
    sw = tail_swing
    tail = [root, (root[0] - 12.0, root[1] + 10.0 - 8.0 * sw), (root[0] - 22.0, root[1] + 26.0 - 14.0 * sw),
            (root[0] - 28.0 - 4.0 * tail_twitch, root[1] + 34.0 - 22.0 * sw - 6.0 * abs(tail_twitch))]
    pen.limb(tail, 5.0, COAT)
    pen.ellipse(tail[-1][0], tail[-1][1], 4.0, 4.6, TUFT)

    # The body: long and heavy, the belly loose.
    body = [(hip[0] - 14.0, hip[1] + 4.0), (hip[0] - 10.0, hip[1] - 8.0), (hip[0] + 10.0, hip[1] - 12.0), (shoulder[0] - 20.0, shoulder[1] - 12.0),
            (shoulder[0] - 2.0, shoulder[1] - 14.0), (shoulder[0] + 14.0, shoulder[1] - 6.0), (shoulder[0] + 16.0, shoulder[1] + 10.0),
            (shoulder[0] + 8.0, shoulder[1] + 26.0), (shoulder[0] - 14.0, shoulder[1] + 28.0), (hip[0] + 22.0, hip[1] + 26.0),
            (hip[0] + 4.0, hip[1] + 24.0), (hip[0] - 12.0, hip[1] + 18.0)]
    pen.poly(body, COAT)
    pen.poly([(shoulder[0] + 8.0, shoulder[1] + 26.0), (shoulder[0] - 14.0, shoulder[1] + 28.0), (hip[0] + 22.0, hip[1] + 26.0),
              (hip[0] + 6.0, hip[1] + 23.0), (hip[0] + 22.0, hip[1] + 20.0), (shoulder[0] - 14.0, shoulder[1] + 21.0)], COAT_LIGHT, body=False)
    pen.poly([(hip[0] - 10.0, hip[1] - 8.0), (hip[0] + 10.0, hip[1] - 12.0), (shoulder[0] - 2.0, shoulder[1] - 14.0), (shoulder[0] + 6.0, shoulder[1] - 10.0),
              (shoulder[0] - 10.0, shoulder[1] - 8.0), (hip[0] + 8.0, hip[1] - 6.0)], COAT_SHADE, body=False)
    # The faint stripes on the flank (the cave painters drew some).
    for k in range(5):
        x = hip[0] + 12.0 + k * 10.0
        top_y = hip[1] - 6.0 + (shoulder[1] - hip[1]) * (k / 5.0)
        pen.ink([(x, top_y), (x - 2.0, top_y + 8.0), (x + 1.0, top_y + 14.0)], 1.4, STRIPE)
    # The haunch and the shoulder blade.
    pen.ink([(hip[0] - 4.0, hip[1] - 2.0), (hip[0] + 10.0, hip[1] + 4.0), (hip[0] + 12.0, hip[1] + 16.0)], 1.2, COAT_SHADE)
    pen.ink([(shoulder[0] - 6.0, shoulder[1] - 8.0), (shoulder[0] - 2.0, shoulder[1] + 6.0), (shoulder[0] + 6.0, shoulder[1] + 14.0)], 1.2, COAT_SHADE)

    # The near legs.
    leg((hip[0] + 2.0, hip[1] + 14.0), 0.6, True, COAT)
    leg((shoulder[0] + 2.0, shoulder[1] + 16.0), 0.0, False, COAT)

    # The head: broad, low on a thick neck; small round ears.
    hx, hy = shoulder[0] + 24.0 + 4.0 * fore_reach, shoulder[1] - 8.0 - head_up
    neck = [(shoulder[0] - 6.0, shoulder[1] - 12.0), (hx - 10.0, hy - 12.0), (hx + 2.0, hy + 12.0), (shoulder[0] + 12.0, shoulder[1] + 20.0)]
    pen.poly(neck, COAT)
    for ex0, colour in ((-8.0, COAT_SHADE), (-2.0, COAT)):
        ex1 = hx + HS * ex0 - 4.0 * max(0.0, -ears)
        ey1 = hy - HS * 12.0 - 2.0 * max(0.0, ears) + 3.0 * max(0.0, -ears)
        pen.ellipse(ex1, ey1, 4.2 * HS, 4.0 * HS, colour)
        pen.ellipse(ex1 + 0.6, ey1 + 0.8, 2.2 * HS, 2.0 * HS, TUFT, body=False)
    pen.ellipse(hx, hy, 12.0 * HS, 11.0 * HS, COAT)
    pen.poly([(hx - HS * 10.0, hy - HS * 6.0), (hx - HS * 2.0, hy - HS * 10.0), (hx + HS * 4.0, hy - HS * 9.0), (hx - HS * 4.0, hy - HS * 5.0)], COAT_SHADE, body=False)
    gape = 10.0 * jaw
    if jaw > 0.05:
        pen.poly([(hx + HS * 4.0, hy + HS * 5.0), (hx + HS * 21.0, hy + HS * 4.0), (hx + HS * 18.0, hy + HS * 5.0 + gape * 0.8), (hx + HS * 5.0, hy + HS * 8.0 + gape * 0.5)], MOUTH)
    # The lower jaw and chin, pale.
    pen.poly([(hx + HS * 2.0, hy + HS * 6.0), (hx + HS * 19.0, hy + HS * 5.0 + gape * 0.8), (hx + HS * 16.0, hy + HS * 9.0 + gape), (hx + HS * 4.0, hy + HS * 11.0 + gape * 0.5)], COAT_LIGHT)
    # The muzzle: short and broad, pale, with a pink-brown nose.
    muzzle = [(hx + HS * 4.0, hy - HS * 6.0), (hx + HS * 14.0, hy - HS * 5.0), (hx + HS * 19.0, hy - HS * 3.0), (hx + HS * 21.6, hy + HS * 0.0),
              (hx + HS * 21.0, hy + HS * 4.0), (hx + HS * 17.0, hy + HS * 7.0), (hx + HS * 10.0, hy + HS * 7.6), (hx + HS * 4.0, hy + HS * 6.0)]
    pen.poly(muzzle, COAT_LIGHT)
    pen.ink([(hx + HS * 6.0, hy - HS * 6.0), (hx + HS * 18.0, hy - HS * 3.0)], 1.0, COAT_SHADE)
    pen.poly([(hx + HS * 18.0, hy - HS * 3.0), (hx + HS * 22.4, hy - HS * 1.6), (hx + HS * 22.0, hy + HS * 1.6), (hx + HS * 19.0, hy + HS * 1.0)], NOSE)
    pen.ink([(hx + HS * 20.0, hy + HS * 1.2), (hx + HS * 20.0, hy + HS * 4.0), (hx + HS * 16.0, hy + HS * 5.4)], 0.8, DARK)
    if jaw > 0.25:
        for fx0, up in ((hx + HS * 17.0, True), (hx + HS * 14.0, False)):
            if up:
                pen.poly([(fx0 - 1.2, hy + HS * 5.0), (fx0 + 1.2, hy + HS * 5.0), (fx0, hy + HS * 8.6)], CLAW, body=False)
            else:
                yy = hy + HS * 5.0 + gape * 0.8
                pen.poly([(fx0 - 1.2, yy + 1.0), (fx0 + 1.2, yy + 1.0), (fx0, yy - 2.6)], CLAW, body=False)
        pen.ink([(hx + HS * 10.0, hy - HS * 4.0), (hx + HS * 12.0, hy - HS * 6.0), (hx + HS * 14.0, hy - HS * 4.0)], 0.8, COAT_SHADE)
    # Whisker dots and whiskers.
    for k in range(3):
        pen.dot(hx + HS * 13.0 + k * 1.8, hy + HS * 2.0 + (k % 2) * 1.2, 0.5, DARK)
    pen.ink([(hx + HS * 14.0, hy + HS * 2.0), (hx + HS * 26.0, hy + HS * 0.0)], 0.5, K.alpha(K.WHITE, 0.8))
    pen.ink([(hx + HS * 14.0, hy + HS * 3.0), (hx + HS * 25.0, hy + HS * 4.0)], 0.5, K.alpha(K.WHITE, 0.8))
    # The eye: amber, with a dark line under it.
    ex, ey = hx + HS * 7.0, hy - HS * 4.0
    if eyes == "shut":
        pen.ink([(ex - 2.6, ey), (ex + 2.6, ey + 0.6)], 1.0, DARK)
    else:
        h = 2.6 if eyes == "wide" else (1.2 if eyes == "narrow" else 1.9)
        pen.ellipse(ex, ey, 3.0 * HS, h * HS, EYE, body=False)
        pen.ellipse(ex + 0.6, ey, 0.9, max(0.6, h - 0.4), DARK, body=False)
        pen.ink([(ex - 3.0, ey + h), (ex + 3.0, ey + h - 0.4)], 0.8, DARK)
    if eyes == "narrow":
        pen.ink([(ex - 3.4, ey - 3.0), (ex + 3.4, ey - 1.4)], 1.0, DARK)
    pen.ink([(ex + 3.0, ey + 1.0), (hx + HS * 12.0, hy + HS * 4.0)], 0.8, DARK)

    if anim == "windup" or (anim == "attack_side" and rise > 4.0):
        H.dust(f, hip[0] - 4.0, GROUND - 2.0, 0.6 if anim == "windup" else 0.8, f"cave_lion:{anim}:{i}", spread=1.4)
    if anim == "attack_side" and i == 4:
        H.dust(f, shoulder[0] + 20.0, GROUND - 2.0, 1.0, f"cave_lion:land:{i}", spread=2.0)
    if anim == "hit":
        mx, my = pen.at(hx, hy - 24.0)
        for k in (-1.0, 0.0, 1.0):
            f.ink([(mx + k * 5.0, max(6.0, my)), (mx + k * 7.0, max(3.0, my - 5.0))], 1.2, K.alpha(K.WHITE, 0.9))
    if alarm:
        ax, ay = pen.at(hx - 4.0, hy - 28.0)
        H.alarm_mark(f, min(184.0, ax), max(14.0, ay))
    return f.finish(outline=H.SEPIA_INK, width=1.6, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
