"""The Tiger: a Bengal tiger of the plains and the reed beds of South Asia.

A big orange cat with black stripes, a white belly, white cheeks and a
white chin, round ears with a white spot on the back of each, and a long
ringed tail with a black tip. Its eyes are amber.

It walks low and slow, the shoulders rolling. When it sees you its ears
go up and its tail stops. Its windup is a crouch: the belly near the
ground, the rear up, the tail lashing. Its strike is the pounce: it leaps
at you with its forepaws out and its claws open, and lands. A hit makes
it flatten its ears and snarl; at its death it lies down on its side.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Tuple

from . import _art_cast_kit as K
from . import _history_asia_kit as A
from . import _stage_kit as S

TARGET_NAME = "tiger"
FRAME_SIZE = (192, 128)
ROWS = K.ENEMY_ROWS
GROUND = 122.0

ACTOR_METADATA = A.enemy_metadata(
    TARGET_NAME, "Tiger", "Quadruped", "Large", "Heavy", "Walk", ["tiger", "cat", "pounce", "beast"],
    "A Bengal tiger of the South Asia floor of the History dimension: orange with black stripes and a white chin. "
    "It stalks low, crouches with its tail lashing, and pounces with its forepaws out.",
    "south_asia",
)

FUR = (236, 132, 44, 255)
FUR_SHADE = (190, 96, 30, 255)
FUR_LIGHT = (250, 176, 92, 255)
WHITE = (250, 244, 232, 255)
WHITE_SHADE = (214, 204, 186, 255)
STRIPE = (40, 26, 24, 255)
EYE = (240, 196, 60, 255)
NOSE = (206, 120, 112, 255)
MOUTH = (150, 44, 52, 255)
CLAW = (246, 240, 226, 255)
DUST = (220, 196, 150, 255)

Point = Tuple[float, float]


def _gait(ph: float, stride: float, lift: float) -> Point:
    """The place of a paw in a walk at phase `ph`: on the ground it moves
    back under the body; in the air it comes forward and up."""
    ph %= 1.0
    if ph < 0.6:
        u = ph / 0.6
        return (stride * (0.5 - u), 0.0)
    u = (ph - 0.6) / 0.4
    return (stride * (-0.5 + (1.0 - math.cos(math.pi * u)) / 2.0), -lift * math.sin(math.pi * u))


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = K.Frame(FRAME_SIZE)
    dx, dy, tilt, crouch, rear = 0.0, 0.0, 0.0, 0.0, 0.0
    walk, head_up, jaw, ears, eyes = None, 0.0, 0.0, 0.0, "open"
    tail_lash, tail_up, alarm, lie, fade = 0.0, 0.0, False, 0.0, 1.0
    leap, reach, land = 0.0, 0.0, 0.0
    if anim == "idle":
        dy = 0.6 * math.sin(cyc)
        tail_lash = 0.5 * math.sin(cyc)
        head_up = 1.2 * math.sin(cyc + 1.0)
        eyes = "shut" if i == 4 else "open"
    elif anim == "walk":
        walk = t
        dy = -1.2 * abs(math.sin(cyc))
        tilt = 1.5 * math.sin(cyc)
        head_up = -4.0
        tail_lash = 0.3 * math.sin(cyc)
    elif anim == "notice":
        k = math.sin(math.pi * min(1.0, t * 1.3))
        head_up, ears, alarm, eyes, tail_up = 7.0 * k, 1.0, True, "wide", 0.4 * k
        jaw = 0.2 * k
    elif anim == "windup":
        # The crouch: belly down, the rear up and swaying, the tail lashing.
        crouch, rear, head_up = 14.0, 6.0 + 2.0 * math.sin(cyc * 2.0), -3.0
        dx = -8.0 + 1.5 * math.sin(cyc * 2.0)
        eyes, ears, jaw = "narrow", -0.7, 0.2
        tail_lash, tail_up = 1.2 * math.sin(cyc * 2.0), 0.5
    elif anim == "attack_side":
        # The pounce: off the ground (0), in the air with the paws out (1..2),
        # down on its forepaws (3), and back up (4..5).
        arc = [(0.0, 0.3, -10.0), (0.8, 1.0, -2.0), (1.0, 1.0, 2.0), (0.2, 0.7, 4.0), (0.0, 0.2, 2.0), (0.0, 0.0, -2.0)][i]
        leap, reach, dx = arc
        land = 1.0 if i == 3 else (0.5 if i == 4 else 0.0)
        dy = -22.0 * leap
        tilt = -10.0 * leap + 8.0 * land
        jaw = 1.0 if i in (1, 2, 3) else 0.3
        eyes, ears, tail_up = "narrow", -0.8, 0.8 * leap
        crouch = 8.0 if i == 0 else 0.0
    elif anim == "hit":
        k = math.sin(math.pi * (i + 1) / (n + 1))
        dx, tilt, head_up, jaw, eyes, ears = -7.0 * k, -5.0 * k, 5.0 * k, 0.7, "shut", -1.0
        tail_up = -0.4
    elif anim == "death":
        lie = min(1.0, t * 1.5)
        crouch, head_up = 17.0 * lie, -8.0 * lie
        eyes, ears, jaw, tail_up = "shut", -1.0, 0.2, -0.3
        fade = 1.0 - max(0.0, t - 0.7) / 0.3

    hip = (72.0 + dx, GROUND - 50.0 + dy + crouch * (0.5 + 0.5 * lie) - rear)
    shoulder = (126.0 + dx + 6.0 * leap, GROUND - 52.0 + dy + crouch)
    pivot = ((hip[0] + shoulder[0]) / 2.0, GROUND - 40.0 + dy)
    rot = tilt + 3.0 * lie
    shift = (0.0, 0.0)
    pen = S.Pen(f, pivot, rot, shift)
    flat = S.Pen(f)

    def paw(foot: Point, colour, claws: bool) -> None:
        x, y = foot
        flat.poly([(x - 5.0, y - 4.0), (x + 7.0, y - 3.6), (x + 8.6, y + 1.0), (x + 6.0, y + 2.6), (x - 5.6, y + 2.6)], colour)
        for k in range(3):
            flat.ink([(x + 2.0 + k * 2.2, y - 0.6), (x + 2.6 + k * 2.2, y + 2.4)], 0.7, STRIPE)
        if claws:
            for k in range(3):
                cx0 = x + 6.0 + k * 0.6
                cy0 = y - 3.0 + k * 2.4
                flat.poly([(cx0, cy0 - 0.8), (cx0 + 4.6, cy0 + 0.4), (cx0, cy0 + 1.0)], CLAW, body=False)

    def leg(top: Point, phase_offset: float, hind: bool, colour, near: bool) -> None:
        top_w = pen.at(*top)
        fx, fy = (0.0, 0.0)
        if walk is not None:
            fx, fy = _gait(walk + phase_offset, 30.0, 9.0)
        claws = False
        if leap or reach:
            if hind:
                # The hind legs push off behind, long and straight.
                fx, fy = -26.0 * leap - 6.0 * reach, -6.0 * leap
            else:
                # The forepaws reach out in front, claws open.
                fx, fy = 30.0 * reach + (4.0 if near else -4.0), -26.0 * reach + 10.0 * (1.0 - leap)
                claws = reach > 0.5
        if land and not hind:
            fx, fy, claws = 12.0 + (6.0 if near else 0.0), 0.0, True
        if crouch and not leap:
            fx += -6.0 if hind else 8.0
        if lie:
            # Lying down: the forelegs go out in front, the hind legs fold under.
            foot = (top_w[0] + (22.0 if not hind else 14.0) * lie + fx * (1.0 - lie), GROUND - 3.0)
        elif leap > 0.5 and not hind:
            foot = (top_w[0] + fx, top_w[1] + 34.0 + fy)
        elif leap > 0.5:
            foot = (top_w[0] + fx, top_w[1] + 30.0 + fy)
        else:
            foot = (top_w[0] + fx + (3.0 if not hind else -2.0), GROUND - 3.0 + fy)
        foot = (foot[0], min(foot[1], GROUND - 3.0))
        d = math.hypot(foot[0] - top_w[0], foot[1] - top_w[1])
        l1, l2 = max(12.0, d * 0.56), max(12.0, d * 0.56)
        knee, foot = S.joint(top_w, foot, l1, l2, 1.0 if hind else -1.0)
        flat.limb([top_w, knee], 15.0 if hind else 12.5, colour)
        flat.limb([knee, foot], 9.0, colour)
        # Stripes round the leg.
        for u in (0.35, 0.65):
            lx, ly = knee[0] + (foot[0] - knee[0]) * u, knee[1] + (foot[1] - knee[1]) * u
            flat.ink([(lx - 3.0, ly - 1.0), (lx + 3.0, ly + 1.0)], 1.4, STRIPE)
        paw(foot, colour, claws)

    # The far legs, in shade.
    leg((hip[0] + 6.0, hip[1] + 12.0), 0.45, True, FUR_SHADE, False)
    leg((shoulder[0] - 6.0, shoulder[1] + 12.0), 0.95, False, FUR_SHADE, False)

    # The tail: long, low, curving up at its tip; ringed and black at the end.
    root = (hip[0] - 10.0, hip[1] - 4.0)
    lash, up = tail_lash, tail_up
    pts = [root]
    for k in range(1, 6):
        u = k / 5.0
        x = root[0] - 36.0 * u + 3.0 * lash * u * u
        y = root[1] + 34.0 * u - 30.0 * u ** 3 * (1.0 + up) + 10.0 * lash * u * u
        pts.append((x, min(GROUND - 6.0, y)))
    for k in range(5):
        pen.limb([pts[k], pts[k + 1]], 7.0 - 0.3 * k, FUR)
    for k in (1, 2, 3, 4):
        x, y = pts[k]
        pen.ink([(x - 1.0, y - 3.4), (x + 1.4, y + 3.4)], 2.0, STRIPE)
    pen.ellipse(pts[5][0], pts[5][1], 3.6, 3.6, STRIPE)

    # The body: a long, deep barrel with a heavy chest and a low belly.
    body = [(hip[0] - 14.0, hip[1] + 2.0), (hip[0] - 8.0, hip[1] - 10.0), (hip[0] + 14.0, hip[1] - 12.0), (shoulder[0] - 12.0, shoulder[1] - 11.0),
            (shoulder[0] + 4.0, shoulder[1] - 14.0), (shoulder[0] + 15.0, shoulder[1] - 4.0), (shoulder[0] + 15.0, shoulder[1] + 12.0),
            (shoulder[0] + 4.0, shoulder[1] + 24.0), (shoulder[0] - 14.0, shoulder[1] + 24.0), (hip[0] + 18.0, hip[1] + 22.0),
            (hip[0] + 2.0, hip[1] + 22.0), (hip[0] - 12.0, hip[1] + 16.0)]
    pen.poly(body, FUR)
    # The white belly, the shade under it, and the light along the back.
    pen.poly([(shoulder[0] + 8.0, shoulder[1] + 18.0), (shoulder[0] + 4.0, shoulder[1] + 24.0), (shoulder[0] - 14.0, shoulder[1] + 24.0),
              (hip[0] + 18.0, hip[1] + 22.0), (hip[0] + 6.0, hip[1] + 21.0), (hip[0] + 16.0, hip[1] + 17.0), (shoulder[0] - 12.0, shoulder[1] + 19.0)],
             WHITE, body=False)
    pen.poly([(hip[0] - 6.0, hip[1] - 8.0), (hip[0] + 14.0, hip[1] - 10.0), (shoulder[0] - 12.0, shoulder[1] - 9.0), (shoulder[0] + 2.0, shoulder[1] - 12.0),
              (shoulder[0] + 2.0, shoulder[1] - 8.0), (hip[0] + 12.0, hip[1] - 5.0)], FUR_LIGHT, body=False)
    # The haunch, in shade.
    pen.poly([(hip[0] - 12.0, hip[1] + 4.0), (hip[0] - 6.0, hip[1] - 6.0), (hip[0] + 8.0, hip[1] - 4.0), (hip[0] + 12.0, hip[1] + 10.0),
              (hip[0] + 4.0, hip[1] + 18.0), (hip[0] - 8.0, hip[1] + 15.0)], FUR_SHADE, body=False)
    # The stripes: dark wedges from the back down the side.
    xs = [hip[0] - 6.0, hip[0] + 4.0, hip[0] + 14.0, hip[0] + 24.0, hip[0] + 33.0, hip[0] + 42.0, shoulder[0] - 4.0, shoulder[0] + 6.0]
    for k, x in enumerate(xs):
        u = (x - hip[0]) / max(1.0, shoulder[0] - hip[0])
        top_y = hip[1] - 10.0 + (shoulder[1] - hip[1]) * u - (2.0 if 0.3 < u < 0.9 else 0.0) + 2.4
        length = 14.0 + 4.0 * math.sin(k * 1.7)
        lean = -3.0 if k % 2 else 2.0
        pen.poly([(x - 2.4, top_y), (x + 2.4, top_y), (x + lean + 0.8, top_y + length), (x + lean, top_y + length + 2.0)], STRIPE, body=False)
        if k % 2 == 0 and k < 7:
            pen.poly([(x + 3.0, top_y + length * 0.55), (x + 7.0, top_y + length * 0.5), (x + 4.0, top_y + length * 0.75)], STRIPE, body=False)

    # The near legs.
    leg((hip[0], hip[1] + 13.0), 0.95, True, FUR, True)
    leg((shoulder[0] + 2.0, shoulder[1] + 13.0), 0.45, False, FUR, True)
    # The stripes on the near thigh.
    for k in range(3):
        pen.ink([(hip[0] - 8.0 + k * 5.0, hip[1] + 2.0 + k), (hip[0] - 4.0 + k * 5.0, hip[1] + 10.0 + k)], 1.6, STRIPE)

    # The head: big and round, with a white ruff of cheeks and a short muzzle.
    hx, hy = shoulder[0] + 24.0 + 4.0 * reach, shoulder[1] - 4.0 - head_up
    pen.poly([(shoulder[0] - 2.0, shoulder[1] - 12.0), (hx - 6.0, hy - 10.0), (hx + 4.0, hy + 10.0), (shoulder[0] + 12.0, shoulder[1] + 16.0)], FUR)
    ear_back = 4.0 * max(0.0, -ears)
    for ex0, colour in ((-8.0, FUR_SHADE), (2.0, FUR)):
        ex, ey = hx + ex0 - ear_back, hy - 14.5 + ear_back * 0.8 - 2.0 * max(0.0, ears)
        pen.ellipse(ex, ey, 5.0, 4.4 - ear_back * 0.3, colour)
        pen.ellipse(ex + 0.6, ey + 0.6, 2.6, 2.0, STRIPE, body=False)
    pen.ellipse(hx, hy, 16.0, 14.5, FUR)
    # The white cheek ruff, and the stripes of the face.
    pen.poly([(hx - 12.0, hy + 2.0), (hx - 9.0, hy + 12.0), (hx - 2.0, hy + 14.0), (hx + 4.0, hy + 10.0), (hx - 2.0, hy + 6.0)], WHITE)
    for k in range(3):
        pen.ink([(hx - 12.0 + k * 1.4, hy + 2.0 + k * 3.4), (hx - 6.0 + k * 1.0, hy + 3.4 + k * 3.0)], 1.3, STRIPE)
    for k in range(3):
        pen.ink([(hx - 6.0 + k * 4.0, hy - 12.0), (hx - 5.0 + k * 3.6, hy - 7.0)], 1.4, STRIPE)
    # The muzzle and the jaw: a round white muzzle under a broad nose.
    gape = 9.0 * jaw
    mx, my = hx + 11.0, hy + 5.0
    if jaw > 0.05:
        pen.poly([(mx - 3.0, my + 1.0), (mx + 9.0, my + 0.0), (mx + 7.0, my + 2.0 + gape), (mx - 2.0, my + 3.0 + gape * 0.6)], MOUTH)
        pen.ellipse(mx + 2.0, my + 3.0 + gape, 6.0, 3.2, WHITE)
    else:
        pen.ellipse(mx + 1.0, my + 5.0, 5.0, 3.0, WHITE)
    pen.ellipse(mx + 1.0, my, 8.0, 5.6, WHITE)
    pen.poly([(hx + 2.0, hy - 9.0), (mx + 4.0, my - 7.0), (mx + 8.0, my - 3.6), (mx + 7.0, my - 1.0), (mx - 2.0, my - 2.0)], FUR)
    pen.poly([(mx + 4.0, my - 4.4), (mx + 9.0, my - 3.4), (mx + 6.6, my - 0.4)], NOSE, body=False)
    pen.ink([(mx + 6.6, my - 0.4), (mx + 6.0, my + 2.0), (mx + 2.0, my + 3.0)], 0.9, STRIPE)
    for k in range(3):
        pen.dot(mx - 1.0 + k * 2.0, my + 0.4 + (k % 2) * 1.2, 0.55, STRIPE)
    if jaw > 0.3:
        for fx0 in (mx + 2.0, mx + 6.0):
            pen.poly([(fx0 - 1.2, my + 1.4), (fx0 + 1.2, my + 1.4), (fx0, my + 5.4)], CLAW, body=False)
        pen.poly([(mx + 3.6 - 1.2, my + 1.2 + gape), (mx + 3.6 + 1.2, my + 1.2 + gape), (mx + 3.6, my - 2.4 + gape)], CLAW, body=False)
        pen.ink([(mx - 2.0, my - 5.0), (mx, my - 6.4), (mx + 3.0, my - 5.4)], 0.8, FUR_SHADE)
    # Whiskers.
    for k in (-1.0, 0.0, 1.0):
        pen.ink([(mx + 3.0, my + 1.0 + k), (mx + 13.0, my + 0.4 + 3.0 * k)], 0.5, WHITE_SHADE)
    # The eye: amber, with the white mark over it.
    ex, ey = hx + 4.0, hy - 3.0
    pen.ellipse(ex - 1.0, ey - 4.0, 3.0, 1.6, WHITE, body=False)
    if eyes == "shut":
        pen.ink([(ex - 3.0, ey), (ex + 3.0, ey + 0.8)], 1.2, STRIPE)
    else:
        h = 2.6 if eyes == "wide" else (1.2 if eyes == "narrow" else 2.0)
        pen.poly([(ex - 3.4, ey + 0.6), (ex, ey - h - 0.6), (ex + 3.6, ey - 0.2), (ex + 0.2, ey + h)], STRIPE, body=False)
        pen.poly([(ex - 2.2, ey + 0.4), (ex, ey - h + 0.2), (ex + 2.4, ey - 0.1), (ex + 0.1, ey + h * 0.7)], EYE, body=False)
        pen.ellipse(ex + 0.4, ey, 0.7, max(0.6, h * 0.6), STRIPE, body=False)
    if eyes == "narrow":
        pen.ink([(ex - 4.0, ey - 3.4), (ex + 3.6, ey - 1.4)], 1.2, STRIPE)

    if leap > 0.5:
        # Speed lines behind the leap.
        for k in range(3):
            y = hip[1] - 4.0 + k * 10.0
            x0 = max(6.0, hip[0] - 34.0)
            f.ink([(x0, y), (x0 + 16.0, y)], 1.4, K.alpha(K.WHITE, 0.6))
    if land:
        for k in range(5):
            x = shoulder[0] + 6.0 + k * 6.0
            f.ellipse(min(184.0, x), GROUND - 3.0 - (k % 2) * 3.0, 3.0 * land + 1.0, 2.0 * land + 0.6, K.alpha(DUST, 0.6 * land), body=False)
    if anim == "hit":
        sx, sy = pen.at(hx, hy - 24.0)
        for k in (-1.0, 0.0, 1.0):
            f.ink([(sx + k * 5.0, sy + 2.0), (sx + k * 7.0, sy - 3.0)], 1.2, K.alpha(K.WHITE, 0.9))
    if alarm:
        ax, ay = pen.at(hx + 14.0, hy - 26.0)
        A.alarm_mark(f, min(184.0, ax), max(14.0, ay))
    return f.finish(outline=A.SEPIA_INK, width=1.5, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
