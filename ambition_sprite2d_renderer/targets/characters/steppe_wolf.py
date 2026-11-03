"""The Steppe Wolf: the blue wolf of the Steppe.

In the founding story of the Mongols, their first ancestor was a blue-grey
wolf. This one is that colour: a lean grey-blue wolf with a dark saddle on
its back, a pale belly and throat, long legs, a low brush of a tail, tall
ears and amber eyes.

It is fast. Its walk is a long lope. When it sees you its ears go up and
it growls. Its windup is a crouch, the hackles up and the lips back; its
strike is a lunge, the body stretched long and the jaws snapping shut at
the end of it. A hit makes it yelp; at its death it falls on its side.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Tuple

from . import _art_cast_kit as K
from . import _history_steppe_kit as H
from . import _stage_kit as S

TARGET_NAME = "steppe_wolf"
FRAME_SIZE = (128, 96)
ROWS = K.ENEMY_ROWS
GROUND = 92.0

ACTOR_METADATA = K.enemy_metadata(
    TARGET_NAME, "Steppe Wolf", "Quadruped", "Standard", "Medium", "Walk", ["history", "steppe", "wolf", "beast"],
    "The blue-grey wolf of the Mongol founding story, on the Steppe of the History dimension. It lopes fast, crouches "
    "with its hackles up, and lunges with its jaws open.",
)

FUR = (128, 144, 172, 255)
FUR_SHADE = (88, 100, 132, 255)
FUR_DARK = (62, 68, 94, 255)
FUR_LIGHT = (208, 214, 226, 255)
EYE = (246, 184, 56, 255)
NOSE = (34, 30, 38, 255)
MOUTH = (150, 46, 56, 255)

Point = Tuple[float, float]


def _gait(ph: float, stride: float, lift: float) -> Point:
    """The place of a paw in a lope at phase `ph`: on the ground it moves back
    under the body; in the air it comes forward and up."""
    ph %= 1.0
    if ph < 0.5:
        u = ph / 0.5
        return (stride * (0.5 - u), 0.0)
    u = (ph - 0.5) / 0.5
    return (stride * (-0.5 + (1.0 - math.cos(math.pi * u)) / 2.0), -lift * math.sin(math.pi * u))


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = K.Frame(FRAME_SIZE)
    dx, dy, tilt, crouch, stretch = 0.0, 0.0, 0.0, 0.0, 0.0
    lope, head_up, jaw, tail_up, ears, eyes, hackles = None, 0.0, 0.0, 0.0, 0.0, "open", 0.0
    alarm, lie, fade, reach = False, 0.0, 1.0, 0.0
    if anim == "idle":
        dy = 0.5 * math.sin(cyc)
        tail_up = 0.2 * math.sin(cyc)
        head_up = 1.0 * math.sin(cyc + 1.0)
        ears = 0.5 + 0.5 * max(0.0, math.sin(cyc * 2.0 + 0.5)) * (1.0 if i in (2, 3) else 0.0)
    elif anim == "walk":
        lope = t
        dy = -2.4 * abs(math.sin(cyc))
        tilt = 2.5 * math.sin(cyc)
        tail_up = 0.4 + 0.2 * math.sin(cyc)
        head_up = -2.0
    elif anim == "notice":
        k = math.sin(math.pi * min(1.0, t * 1.3))
        head_up, ears, alarm, eyes, tail_up = 6.0 * k, 1.0, True, "wide", 0.6 * k
        jaw = 0.25 * k
    elif anim == "windup":
        crouch, tilt, head_up, jaw, hackles = 9.0, 4.0, -5.0, 0.35 + 0.05 * math.sin(cyc * 2.0), 1.0
        eyes, tail_up, ears = "narrow", 0.9, -0.6
        dx = -7.0 + 1.0 * math.sin(cyc * 2.0)
    elif anim == "attack_side":
        # The lunge: the body stretches out (0..2), the jaws snap shut (3), and back.
        u = min(1.0, t / 0.55)
        back = max(0.0, (t - 0.55) / 0.45)
        stretch = 9.0 * math.sin(math.pi * 0.5 * u) * (1.0 - back)
        reach = math.sin(math.pi * 0.5 * u) * (1.0 - back)
        dx = -8.0 + 4.0 * u - 4.0 * back * (1.0 - u * 0.0)
        dy = -4.0 * math.sin(math.pi * u) * (1.0 - back)
        tilt = -4.0 * reach
        jaw = 1.0 if i in (1, 2) else (0.0 if i == 3 else 0.3)
        eyes, ears, tail_up, hackles = "narrow", -0.8, 1.0, 0.6
    elif anim == "hit":
        k = math.sin(math.pi * (i + 1) / (n + 1))
        dx, tilt, head_up, jaw, eyes, ears, tail_up = -6.0 * k, -6.0 * k, 4.0 * k, 0.5, "shut", -1.0, -0.6
    elif anim == "death":
        lie = min(1.0, t * 1.5)
        eyes, ears, jaw, tail_up = "shut", -1.0, 0.3, -0.5
        fade = 1.0 - max(0.0, t - 0.7) / 0.3

    hip = (40.0 + dx, GROUND - 40.0 + dy + crouch * 0.6)
    shoulder = (80.0 + dx + stretch, GROUND - 42.0 + dy + crouch)
    pivot = ((hip[0] + shoulder[0]) / 2.0, GROUND - 30.0)
    # At its death it lies down: the body turns onto its side and sinks.
    rot = tilt - 8.0 * lie
    shift = (0.0, 16.0 * lie)
    pen = H.ScaledPen(f, pivot, rot, shift)
    flat = H.ScaledPen(f)

    def leg(top: Point, phase_offset: float, hind: bool, colour) -> None:
        top_w = pen.at(*top)
        if lope is not None:
            fx, fy = _gait(lope + phase_offset, 24.0, 10.0)
        else:
            fx, fy = 0.0, 0.0
        if reach:
            fx += (16.0 if not hind else -10.0) * reach
            fy -= (10.0 if not hind else 0.0) * reach
        if lie:
            # The legs go out straight, to the side, as it lies.
            ang = math.radians(90.0 - (40.0 if hind else -30.0) * lie)
            ln = 30.0
            foot = (top_w[0] + math.cos(ang) * ln * 0.6 + (8.0 * lie if not hind else -6.0 * lie), top_w[1] + math.sin(ang) * ln * (1.0 - 0.55 * lie))
            foot = (foot[0], min(foot[1], GROUND - 2.0))
        else:
            foot = (top_w[0] + fx + (2.0 if not hind else -1.0), GROUND - 2.0 + fy)
        reach_down = math.hypot(foot[0] - top_w[0], foot[1] - top_w[1])
        l1, l2 = max(14.0, reach_down * 0.52), max(14.0, reach_down * 0.54)
        knee, foot = S.joint(top_w, foot, l1, l2, 1.0 if hind else -1.0)
        flat.limb([top_w, knee], 7.4 if hind else 6.2, colour)
        flat.limb([knee, foot], 4.0, colour)
        flat.poly([(foot[0] - 2.4, foot[1] - 2.2), (foot[0] + 4.4, foot[1] - 1.6), (foot[0] + 4.8, foot[1] + 1.6), (foot[0] - 2.6, foot[1] + 1.6)], colour)
        for k in range(2):
            flat.ink([(foot[0] + 1.4 + k * 1.6, foot[1] - 0.4), (foot[0] + 1.8 + k * 1.6, foot[1] + 1.4)], 0.5, FUR_DARK)

    # The far legs, in shade.
    leg((hip[0] + 4.0, hip[1] + 12.0), 0.1, True, FUR_SHADE)
    leg((shoulder[0] - 4.0, shoulder[1] + 12.0), 0.5, False, FUR_SHADE)

    # The tail: a low brush, with a dark tip.
    lift = tail_up
    root = (hip[0] - 6.0, hip[1] - 2.0)
    tail = [root, (root[0] - 8.0, root[1] + 5.0 - 6.0 * lift), (root[0] - 14.0, root[1] + 13.0 - 12.0 * lift), (root[0] - 16.0, root[1] + 22.0 - 16.0 * lift)]
    pen.limb(tail[:2], 7.0, FUR)
    pen.limb(tail[1:3], 8.4, FUR)
    pen.limb(tail[2:], 7.0, FUR_SHADE)
    pen.ellipse(tail[3][0], tail[3][1], 3.4, 3.4, FUR_DARK)

    # The body: a lean barrel, a deep chest, the belly tucked up.
    body = [(hip[0] - 8.0, hip[1] + 2.0), (hip[0] - 4.0, hip[1] - 7.0), (hip[0] + 14.0, hip[1] - 6.0), (shoulder[0] - 4.0, shoulder[1] - 8.0),
            (shoulder[0] + 8.0, shoulder[1] - 4.0), (shoulder[0] + 12.0, shoulder[1] + 6.0), (shoulder[0] + 6.0, shoulder[1] + 18.0),
            (shoulder[0] - 8.0, shoulder[1] + 18.0), (hip[0] + 18.0, hip[1] + 13.0), (hip[0] + 4.0, hip[1] + 16.0), (hip[0] - 7.0, hip[1] + 12.0)]
    pen.poly(body, FUR)
    # The pale belly and throat, and the dark saddle along the back.
    pen.poly([(shoulder[0] + 12.0, shoulder[1] + 6.0), (shoulder[0] + 6.0, shoulder[1] + 18.0), (shoulder[0] - 8.0, shoulder[1] + 18.0),
              (hip[0] + 18.0, hip[1] + 13.0), (hip[0] + 6.0, hip[1] + 13.0), (hip[0] + 18.0, hip[1] + 9.0), (shoulder[0] - 6.0, shoulder[1] + 12.0)],
             FUR_LIGHT, body=False)
    saddle = [(hip[0] - 4.0, hip[1] - 7.0), (hip[0] + 14.0, hip[1] - 6.0), (shoulder[0] - 4.0, shoulder[1] - 8.0), (shoulder[0] + 2.0, shoulder[1] - 6.0),
              (shoulder[0] - 6.0, shoulder[1] - 1.0), (hip[0] + 14.0, hip[1] - 1.0), (hip[0] - 2.0, hip[1] - 2.0)]
    pen.poly(saddle, FUR_DARK, body=False)
    if hackles:
        # The hackles stand up along the neck and the back.
        for k in range(6):
            x = shoulder[0] - 12.0 + k * 3.6
            y = shoulder[1] - 7.0 - 0.6 * k
            pen.poly([(x - 2.0, y + 1.0), (x + 0.6, y - 4.0 * hackles), (x + 2.0, y + 1.0)], FUR_DARK)
    pen.ink([(hip[0] + 2.0, hip[1] + 2.0), (hip[0] + 6.0, hip[1] + 10.0)], 0.8, FUR_SHADE)

    # The near legs.
    leg((hip[0] + 1.0, hip[1] + 12.0), 0.6, True, FUR)
    leg((shoulder[0] + 1.0, shoulder[1] + 12.0), 0.0, False, FUR)

    # The head: a broad skull, a long muzzle, tall ears.
    hx, hy = shoulder[0] + 16.0 + 3.0 * reach, shoulder[1] - 6.0 - head_up
    neck = [(shoulder[0] - 2.0, shoulder[1] - 6.0), (hx - 6.0, hy - 6.0), (hx + 2.0, hy + 6.0), (shoulder[0] + 8.0, shoulder[1] + 10.0)]
    pen.poly(neck, FUR)
    ear_lean = -6.0 * min(0.0, ears) * -1.0
    for ex0, colour in ((-5.0, FUR_SHADE), (0.0, FUR)):
        ear = [(hx + ex0 - 3.0, hy - 5.0), (hx + ex0 - 2.0 - ear_lean, hy - 15.0 - 2.0 * max(0.0, ears)), (hx + ex0 + 3.6, hy - 6.0)]
        pen.poly(ear, colour)
        pen.poly([(hx + ex0 - 1.4, hy - 6.0), (hx + ex0 - 1.4 - ear_lean * 0.8, hy - 12.0 - 1.6 * max(0.0, ears)), (hx + ex0 + 1.8, hy - 6.4)], FUR_DARK, body=False)
    pen.ellipse(hx, hy, 8.0, 7.0, FUR)
    gape = 7.0 * jaw
    # The mouth inside, then the lower jaw that opens.
    if jaw > 0.05:
        pen.poly([(hx + 3.0, hy + 3.0), (hx + 19.0, hy + 2.0), (hx + 17.0, hy + 3.0 + gape * 0.7), (hx + 4.0, hy + 6.0 + gape * 0.4)], MOUTH)
    lower = [(hx + 1.0, hy + 4.0), (hx + 17.0, hy + 3.4 + gape * 0.7), (hx + 15.0, hy + 6.0 + gape), (hx + 2.0, hy + 8.0 + gape * 0.4)]
    pen.poly(lower, FUR_LIGHT)
    muzzle = [(hx + 2.0, hy - 4.0), (hx + 10.0, hy - 2.6), (hx + 19.0, hy - 0.6), (hx + 20.0, hy + 2.6), (hx + 4.0, hy + 4.0)]
    pen.poly(muzzle, FUR)
    pen.poly([(hx + 6.0, hy + 0.6), (hx + 20.0, hy + 1.0), (hx + 20.0, hy + 2.6), (hx + 4.0, hy + 4.0)], FUR_LIGHT, body=False)
    pen.ellipse(hx + 19.0, hy - 0.2, 2.2, 1.8, NOSE)
    if jaw > 0.2:
        # Fangs, up and down.
        for fx0 in (hx + 13.0, hx + 16.0):
            pen.poly([(fx0 - 1.0, hy + 2.6), (fx0 + 1.0, hy + 2.6), (fx0, hy + 5.0)], K.WHITE, body=False)
        pen.poly([(hx + 14.0 - 1.0, hy + 3.6 + gape * 0.7), (hx + 14.0 + 1.0, hy + 3.6 + gape * 0.7), (hx + 14.0, hy + 1.6 + gape * 0.7)], K.WHITE, body=False)
        # The lip drawn back in a snarl, and the wrinkles of the nose.
        pen.ink([(hx + 9.0, hy - 2.4), (hx + 11.0, hy - 3.6), (hx + 13.0, hy - 2.0)], 0.6, FUR_DARK)
    # The pale cheek ruff, and the eye.
    pen.poly([(hx - 7.0, hy + 1.0), (hx - 2.0, hy + 7.0), (hx + 3.0, hy + 4.0), (hx - 1.0, hy + 1.0)], FUR_LIGHT, body=False)
    ex, ey = hx + 4.0, hy - 2.6
    if eyes == "shut":
        pen.ink([(ex - 2.0, ey), (ex + 2.0, ey + 0.6)], 0.9)
    else:
        h = 2.0 if eyes == "wide" else (1.0 if eyes == "narrow" else 1.5)
        pen.poly([(ex - 2.6, ey + 0.6), (ex, ey - h), (ex + 2.8, ey - 0.2), (ex + 0.2, ey + h * 0.7)], FUR_DARK, body=False)
        pen.poly([(ex - 1.6, ey + 0.4), (ex, ey - h + 0.6), (ex + 1.8, ey - 0.1), (ex + 0.1, ey + h * 0.5)], EYE, body=False)
        pen.dot(ex + 0.3, ey, 0.6, NOSE)
    if eyes in ("narrow",):
        pen.ink([(ex - 3.0, ey - 2.4), (ex + 3.0, ey - 1.0)], 0.9, FUR_DARK)

    if anim == "attack_side" and i == 3:
        # The snap of the jaws: lines out from the shut mouth.
        mx, my = pen.at(hx + 22.0, hy + 3.0)
        for k in (-1.0, 0.0, 1.0):
            f.glow_line([(mx, my + k * 4.0), (min(124.0, mx + 4.0), my + k * 6.0)], 1.2, K.alpha(K.WHITE, 0.9))
    if anim == "hit":
        mx, my = pen.at(hx + 8.0, hy - 16.0)
        for k in (-1.0, 0.0, 1.0):
            f.ink([(mx + k * 4.0, my), (mx + k * 6.0, my - 4.0)], 1.0, K.alpha(K.WHITE, 0.9))
    if alarm:
        ax, ay = pen.at(hx + 10.0, hy - 20.0)
        H.alarm_mark(f, min(120.0, ax), max(14.0, ay))
    return f.finish(outline=H.SEPIA_INK, width=1.4, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
