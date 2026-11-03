"""The Hyena: a spotted hyena of the savanna of the Cradle, laughing.

A sandy hyena with dark spots, a back that slopes down from high shoulders
to low hips, a short bristly mane along its neck and back, a heavy neck, a
big head with a dark muzzle, round ears and a short tail with a black tip.
Its mouth is open in a grin, and it laughs: "hee hee hee".

It is fast. Its walk is a rocking lope, head low. When it sees you its ears
go up and it giggles. Its windup is a crouch, the mane up and the jaws
wide; its strike is a lunge and a bite. A hit makes it yelp; at its death
it falls on its side.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Tuple

from . import _art_cast_kit as K
from . import _history_africa_kit as H
from . import _stage_kit as S

TARGET_NAME = "hyena"
FRAME_SIZE = (128, 96)
ROWS = K.ENEMY_ROWS
GROUND = 91.0

ACTOR_METADATA = H.enemy_metadata(
    TARGET_NAME, "Hyena", "cradle", "Quadruped", "Standard", "Medium", "Walk", ["hyena", "beast", "laugh"],
    "A spotted hyena of the savanna of the Cradle in the History dimension: sandy, spotted, with a sloping back and a "
    "grin. It lopes fast and laughs; it crouches with its mane up, then lunges and bites.",
)

COAT = (204, 170, 112, 255)
COAT_SHADE = (160, 126, 80, 255)
COAT_LIGHT = (232, 212, 166, 255)
SPOT = (92, 64, 42, 255)
MANE = (96, 70, 48, 255)
MUZZLE = (58, 42, 34, 255)
NOSE = (30, 22, 20, 255)
MOUTH = (150, 50, 54, 255)
EYE = (232, 176, 60, 255)
TOOTH = (250, 244, 228, 255)

Point = Tuple[float, float]


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = K.Frame(FRAME_SIZE)
    dx, dy, tilt, crouch, stretch = 0.0, 0.0, 0.0, 0.0, 0.0
    lope, head_up, jaw, tail_up, ears, eyes, mane = None, 0.0, 0.3, 0.0, 0.0, "open", 0.0
    alarm, lie, fade, reach, laugh = False, 0.0, 1.0, 0.0, 0.0
    if anim == "idle":
        # It stands and laughs to itself: the jaw bobs.
        dy = 0.5 * math.sin(cyc)
        tail_up = 0.2 * math.sin(cyc)
        head_up = 1.5 * math.sin(cyc * 2.0)
        jaw = 0.35 + 0.25 * max(0.0, math.sin(cyc * 3.0))
        laugh = max(0.0, math.sin(cyc * 3.0))
    elif anim == "walk":
        lope = t
        dy = -2.0 * abs(math.sin(cyc))
        tilt = 2.0 * math.sin(cyc)
        tail_up = 0.3 + 0.2 * math.sin(cyc)
        head_up = -3.0
        jaw = 0.3
    elif anim == "notice":
        k = math.sin(math.pi * min(1.0, t * 1.3))
        head_up, ears, alarm, eyes, tail_up = 6.0 * k, 1.0, True, "wide", 0.5 * k
        jaw = 0.4 + 0.4 * k
        laugh = k
    elif anim == "windup":
        crouch, tilt, head_up, mane = 8.0, 4.0, -5.0, 1.0
        jaw = 0.75 + 0.1 * math.sin(cyc * 2.0)
        eyes, tail_up, ears = "narrow", 0.9, -0.6
        dx = -7.0 + 1.0 * math.sin(cyc * 2.0)
    elif anim == "attack_side":
        # The lunge: the body stretches out (0..2), the jaws snap shut (3), and back.
        u = min(1.0, t / 0.55)
        back = max(0.0, (t - 0.55) / 0.45)
        stretch = 8.0 * math.sin(math.pi * 0.5 * u) * (1.0 - back)
        reach = math.sin(math.pi * 0.5 * u) * (1.0 - back)
        dx = -8.0 + 4.0 * u - 4.0 * back
        dy = -4.0 * math.sin(math.pi * u) * (1.0 - back)
        tilt = -4.0 * reach
        jaw = 1.0 if i in (1, 2) else (0.0 if i == 3 else 0.4)
        eyes, ears, tail_up, mane = "narrow", -0.8, 1.0, 0.6
    elif anim == "hit":
        k = math.sin(math.pi * (i + 1) / (n + 1))
        dx, tilt, head_up, jaw, eyes, ears, tail_up = -6.0 * k, -6.0 * k, 4.0 * k, 0.6, "shut", -1.0, -0.6
    elif anim == "death":
        lie = min(1.0, t * 1.5)
        eyes, ears, jaw, tail_up = "shut", -1.0, 0.3, -0.5
        fade = 1.0 - max(0.0, t - 0.7) / 0.3

    # High shoulders, low hips: the back slopes down to the tail.
    hip = (40.0 + dx, GROUND - 34.0 + dy + crouch * 0.6)
    shoulder = (78.0 + dx + stretch, GROUND - 44.0 + dy + crouch)
    pivot = ((hip[0] + shoulder[0]) / 2.0, GROUND - 28.0)
    rot = tilt - 8.0 * lie
    pen = H.ScaledPen(f, pivot, rot, (0.0, 9.0 * lie))
    flat = H.ScaledPen(f)

    def leg(top: Point, phase_offset: float, hind: bool, colour) -> None:
        top_w = pen.at(*top)
        fx, fy = H.gait(lope + phase_offset, 22.0, 9.0) if lope is not None else (0.0, 0.0)
        if reach:
            fx += (16.0 if not hind else -10.0) * reach
            fy -= (10.0 if not hind else 0.0) * reach
        if lie:
            ang = math.radians(90.0 - (40.0 if hind else -30.0) * lie)
            foot = (top_w[0] + math.cos(ang) * 18.0 + (8.0 * lie if not hind else -6.0 * lie), top_w[1] + math.sin(ang) * 30.0 * (1.0 - 0.55 * lie))
            foot = (foot[0], min(foot[1], GROUND - 2.0))
        else:
            foot = (top_w[0] + fx + (2.0 if not hind else -1.0), GROUND - 2.0 + fy)
        down = math.hypot(foot[0] - top_w[0], foot[1] - top_w[1])
        l1, l2 = max(12.0, down * 0.52), max(12.0, down * 0.54)
        knee, foot = S.joint(top_w, foot, l1, l2, 1.0 if hind else -1.0)
        flat.limb([top_w, knee], 8.0 if hind else 7.2, colour)
        flat.limb([knee, foot], 4.4, colour)
        # Spots on the leg, and a dark paw.
        mid = ((top_w[0] + knee[0]) / 2.0, (top_w[1] + knee[1]) / 2.0)
        flat.dot(mid[0] + 0.5, mid[1], 1.3, SPOT)
        flat.poly([(foot[0] - 2.6, foot[1] - 2.2), (foot[0] + 4.6, foot[1] - 1.6), (foot[0] + 5.0, foot[1] + 1.6), (foot[0] - 2.8, foot[1] + 1.6)], MUZZLE)

    # The far legs, in shade.
    leg((hip[0] + 4.0, hip[1] + 10.0), 0.1, True, COAT_SHADE)
    leg((shoulder[0] - 4.0, shoulder[1] + 14.0), 0.5, False, COAT_SHADE)

    # The tail: short, with a black brush at the tip.
    root = (hip[0] - 6.0, hip[1] - 1.0)
    tail = [root, (root[0] - 6.0, root[1] + 5.0 - 6.0 * tail_up), (root[0] - 9.0, root[1] + 13.0 - 12.0 * tail_up)]
    pen.limb(tail[:2], 4.0, COAT)
    pen.limb(tail[1:], 6.0, MANE)

    # The body: deep at the chest, falling to narrow hips.
    body = [(hip[0] - 8.0, hip[1] + 2.0), (hip[0] - 5.0, hip[1] - 6.0), (hip[0] + 12.0, hip[1] - 9.0), (shoulder[0] - 8.0, shoulder[1] - 8.0),
            (shoulder[0] + 6.0, shoulder[1] - 6.0), (shoulder[0] + 12.0, shoulder[1] + 6.0), (shoulder[0] + 8.0, shoulder[1] + 20.0),
            (shoulder[0] - 8.0, shoulder[1] + 21.0), (hip[0] + 18.0, hip[1] + 13.0), (hip[0] + 4.0, hip[1] + 15.0), (hip[0] - 7.0, hip[1] + 11.0)]
    pen.poly(body, COAT)
    pen.poly([(shoulder[0] + 12.0, shoulder[1] + 6.0), (shoulder[0] + 8.0, shoulder[1] + 20.0), (shoulder[0] - 8.0, shoulder[1] + 21.0),
              (hip[0] + 18.0, hip[1] + 13.0), (hip[0] + 8.0, hip[1] + 12.0), (shoulder[0] - 6.0, shoulder[1] + 14.0)], COAT_LIGHT, body=False)
    pen.poly([(hip[0] - 7.0, hip[1] + 11.0), (hip[0] + 4.0, hip[1] + 15.0), (hip[0] + 14.0, hip[1] + 13.0), (hip[0] + 2.0, hip[1] + 6.0)], COAT_SHADE, body=False)
    # The spots: in rows down the flank.
    for (u, v) in ((0.15, 0.3), (0.3, 0.55), (0.45, 0.25), (0.55, 0.6), (0.7, 0.35), (0.8, 0.65), (0.35, 0.85), (0.62, 0.9), (0.9, 0.15)):
        x = hip[0] + (shoulder[0] - hip[0]) * u
        top_y = hip[1] - 7.0 + (shoulder[1] - hip[1] - 1.0) * u
        bot_y = hip[1] + 12.0 + (shoulder[1] + 18.0 - hip[1] - 12.0) * u
        pen.ellipse(x, top_y + (bot_y - top_y) * v * 0.85, 2.0, 1.6, SPOT, body=False)
    # The mane: a bristly crest from the head down the back. It stands up in a threat.
    for k in range(9):
        u = k / 8.0
        x = shoulder[0] + 2.0 - (shoulder[0] - hip[0] - 4.0) * u
        y = shoulder[1] - 7.0 + (hip[1] - shoulder[1] - 1.0) * u
        hgt = (3.0 + 4.0 * mane) * (1.0 - 0.6 * u)
        pen.poly([(x - 2.4, y + 1.6), (x - 0.4, y - hgt), (x + 2.2, y + 1.6)], MANE)

    # The near legs.
    leg((hip[0] + 1.0, hip[1] + 10.0), 0.6, True, COAT)
    leg((shoulder[0] + 1.0, shoulder[1] + 14.0), 0.0, False, COAT)

    # The head: big and blunt, on a thick neck, with round ears.
    hx, hy = shoulder[0] + 15.0 + 3.0 * reach, shoulder[1] - 1.0 - head_up
    neck = [(shoulder[0] - 4.0, shoulder[1] - 7.0), (hx - 7.0, hy - 7.0), (hx + 2.0, hy + 8.0), (shoulder[0] + 8.0, shoulder[1] + 14.0)]
    pen.poly(neck, COAT)
    for k in range(3):
        pen.ink([(shoulder[0] + 2.0 + k * 3.0, shoulder[1] - 2.0), (shoulder[0] + 4.0 + k * 3.0, shoulder[1] + 6.0)], 0.9, SPOT)
    ear_lean = 5.0 * max(0.0, -ears)
    for ex0, colour in ((-6.0, COAT_SHADE), (-1.0, COAT)):
        ecx, ecy = hx + ex0 - ear_lean, hy - 9.0 - 2.0 * max(0.0, ears)
        pen.ellipse(ecx, ecy, 3.6, 4.4, colour)
        pen.ellipse(ecx + 0.3, ecy + 0.6, 2.0, 2.6, MUZZLE, body=False)
    pen.ellipse(hx, hy, 8.4, 7.4, COAT)
    gape = 8.0 * jaw
    # The mouth inside, then the lower jaw that opens.
    if jaw > 0.05:
        pen.poly([(hx + 2.0, hy + 3.0), (hx + 17.0, hy + 2.6), (hx + 15.0, hy + 3.0 + gape * 0.7), (hx + 3.0, hy + 6.0 + gape * 0.4)], MOUTH)
    lower = [(hx, hy + 4.0), (hx + 15.0, hy + 3.4 + gape * 0.7), (hx + 13.0, hy + 6.4 + gape), (hx + 1.0, hy + 8.4 + gape * 0.4)]
    pen.poly(lower, COAT_SHADE)
    pen.poly([(hx + 7.0, hy + 4.0 + gape * 0.45), (hx + 15.0, hy + 3.4 + gape * 0.7), (hx + 13.0, hy + 6.4 + gape), (hx + 7.0, hy + 7.0 + gape * 0.6)], MUZZLE, body=False)
    # The short broad muzzle, dark at the end.
    muzzle = [(hx + 2.0, hy - 5.0), (hx + 10.0, hy - 3.6), (hx + 17.0, hy - 1.6), (hx + 18.0, hy + 2.6), (hx + 3.0, hy + 4.0)]
    pen.poly(muzzle, COAT)
    pen.poly([(hx + 9.0, hy - 3.6), (hx + 17.0, hy - 1.6), (hx + 18.0, hy + 2.6), (hx + 9.0, hy + 3.2)], MUZZLE, body=False)
    pen.ellipse(hx + 17.0, hy - 0.8, 2.2, 1.8, NOSE)
    if jaw > 0.2:
        # A grin full of teeth.
        for fx0 in (hx + 8.0, hx + 11.0, hx + 14.0):
            pen.poly([(fx0 - 1.1, hy + 2.8), (fx0 + 1.1, hy + 2.8), (fx0, hy + 5.0)], TOOTH, body=False)
        for fx0 in (hx + 9.0, hx + 12.0):
            yy = hy + 3.6 + gape * 0.6
            pen.poly([(fx0 - 1.0, yy + 1.0), (fx0 + 1.0, yy + 1.0), (fx0, yy - 1.2)], TOOTH, body=False)
    # The spots on the cheek, and the eye.
    pen.dot(hx - 4.0, hy + 1.0, 1.2, SPOT)
    pen.dot(hx - 2.0, hy + 4.0, 1.0, SPOT)
    ex, ey = hx + 4.0, hy - 3.0
    if eyes == "shut":
        pen.ink([(ex - 2.0, ey), (ex + 2.0, ey + 0.6)], 0.9, NOSE)
    else:
        h = 2.2 if eyes == "wide" else (1.1 if eyes == "narrow" else 1.7)
        pen.ellipse(ex, ey, 2.2, h, MUZZLE, body=False)
        pen.ellipse(ex + 0.2, ey, 1.4, max(0.6, h - 0.6), EYE, body=False)
        pen.dot(ex + 0.5, ey, 0.6, NOSE)
    if eyes == "narrow":
        pen.ink([(ex - 3.0, ey - 2.6), (ex + 3.0, ey - 1.0)], 0.9, MUZZLE)

    if laugh > 0.2:
        # "hee hee": little marks of a laugh over the head.
        lx, ly = pen.at(hx + 10.0, hy - 16.0)
        for k in range(2):
            a = 0.6 + 0.4 * laugh
            x0, y0 = min(116.0, lx + 6.0 * k), max(10.0, ly - 5.0 * k)
            f.ink([(x0, y0), (x0 + 3.0, y0 - 2.0)], 1.2, K.alpha(K.WHITE, a))
            f.ink([(x0 + 1.0, y0 + 3.0), (x0 + 4.0, y0 + 1.0)], 1.2, K.alpha(K.WHITE, a))
    if anim == "attack_side" and i == 3:
        mx, my = pen.at(hx + 20.0, hy + 3.0)
        for k in (-1.0, 0.0, 1.0):
            f.glow_line([(mx, my + k * 4.0), (min(124.0, mx + 4.0), my + k * 6.0)], 1.2, K.alpha(K.WHITE, 0.9))
    if anim == "hit":
        mx, my = pen.at(hx + 4.0, hy - 18.0)
        for k in (-1.0, 0.0, 1.0):
            f.ink([(mx + k * 4.0, max(6.0, my)), (mx + k * 6.0, max(3.0, my - 4.0))], 1.0, K.alpha(K.WHITE, 0.9))
    if alarm:
        ax, ay = pen.at(hx - 6.0, hy - 22.0)
        H.alarm_mark(f, min(120.0, ax), max(14.0, ay))
    return f.finish(outline=H.SEPIA_INK, width=1.4, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
