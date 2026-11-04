"""The Asian Black Bear of the History dimension: the moon bear of the Jomon woods.

The Asian black bear (Ursus thibetanus) lives in the forests of Japan, Korea,
China and the Himalaya. Its coat is black and thick, with a ruff of longer
hair on its neck and shoulders. A white or cream V (a crescent: the "moon")
is on its chest. Its ears are large and round and set wide apart, and its
muzzle is short and tan. The Jomon people of north Japan hunted it and
shared the woods with it for thousands of years.

It walks on all fours with a slow roll. At rest it sniffs the air. When it
sees you it rears up on its hind legs to look and to smell (the notice
row). Its windup rears it up again with a forepaw high and back and its
claws out; its strike is a swipe of that forepaw, forward and down, and it
comes down on its four feet. A hit makes it flinch; at its death it lies
down and fades.

The frame is 192 by 160 px: the body box is 72 by 56 world units, and the
bear faces right.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

from . import _art_cast_kit as K
from . import _history_africa_kit as H
from . import _stage_kit as S

TARGET_NAME = "asian_black_bear"
FRAME_SIZE = (192, 160)
ROWS = K.ENEMY_ROWS
#: Nothing is drawn nearer the edge of the frame than this.
MARGIN = 6.0
GROUND = 154.0
#: The bear is drawn in design units and made smaller about this point on
#: the ground, so that it rears up inside the frame.
SIZE = 0.76
PIVOT = (96.0, GROUND)

ACTOR_METADATA = K.enemy_metadata(
    TARGET_NAME, "Asian Black Bear", "Quadruped", "Large", "Heavy", "Walk", ["bear", "claws", "rears", "swipe"],
    "The Asian black bear (the moon bear) of the History dimension's Jomon room: a black bear with a ruff of long hair, "
    "a cream V on its chest, large round ears set wide and a short tan muzzle. It rears up on its hind legs when it "
    "sees you, rears again with a forepaw high, and swipes at you with its claws.",
)
ACTOR_METADATA["tags"] = ["enemy", "history", "jomon"]

Point = Tuple[float, float]

FUR = (62, 56, 60, 255)
FUR_SHADE = (40, 36, 40, 255)
FUR_LIGHT = (100, 92, 96, 255)
MOON = (238, 228, 198, 255)
MOON_SHADE = (200, 186, 150, 255)
MUZZLE = (184, 146, 104, 255)
MUZZLE_SHADE = (146, 110, 76, 255)
EAR_INSIDE = (92, 78, 78, 255)
NOSE = (26, 22, 24, 255)
MOUTH = (150, 50, 56, 255)
TEETH = (244, 236, 216, 255)
CLAW = (236, 226, 204, 255)
CLAW_SHADE = (190, 178, 152, 255)
EYE = (30, 22, 20, 255)
DUST = (196, 176, 140, 255)
UPPER, LOWER = 21.0, 22.0
HIP = (58.0, 102.0)


def _fur(f: K.Frame, points: Sequence[Point], length: float, colour, seed: str, width: float = 1.3) -> None:
    """Strands of long fur that hang from the line `points`."""
    rng = random.Random(seed)
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        steps = max(1, int(math.hypot(x1 - x0, y1 - y0) / 5.0))
        for k in range(steps):
            u = (k + rng.uniform(0.0, 0.8)) / steps
            x, y = x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
            ln = length * rng.uniform(0.7, 1.15)
            f.ink([(x, y), (x + rng.uniform(-1.0, 1.0), y + ln * 0.55), (x - 1.0 + rng.uniform(-1.5, 1.5), y + ln)], width, colour)


def _paw(f: K.Frame, x: float, y: float, near: bool, up: float, toward: float = 0.0) -> None:
    """A paw at (`x`, `y`): a round pad and three pale claws. The claws point
    forward on the ground; `up` turns them up and forward, and `toward`
    (degrees) turns them more, as in a swipe."""
    colour = FUR_SHADE if not near else K.shade(FUR, 0.92)
    big = 1.0 + 0.3 * up
    f.ellipse(x + 2.0, y, 8.0 * big, 5.0 * big + 2.0 * up, colour)
    for k in range(3):
        a = math.radians(-50.0 * up + toward + (k - 1) * (14.0 + 10.0 * up))
        bx, by = x + 2.0 + 7.0 * big * math.cos(a), y + 5.0 * big * math.sin(a)
        ln = 3.0 + 6.0 * up
        tip = (bx + ln * math.cos(a + 0.5), by + ln * math.sin(a + 0.5))
        f.limb([(bx, by), tip], 1.9, CLAW if near else CLAW_SHADE)


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = H.ScaledFrame(FRAME_SIZE, SIZE, PIVOT)

    dx, dy, tilt, pitch, breathe = 0.0, 0.0, 0.0, 0.0, 0.0
    gait, gait_amp, rear, jaw, eyes, fade = 0.0, 0.0, 0.0, 0.0, "open", 1.0
    sniff, fold, alarm = 0.0, 0.0, False
    #: The angle of the near forearm in a windup or a swipe (degrees on the
    #: screen: -90 is up, 0 is forward), or None.
    swipe: Optional[float] = None
    trail = 0.0
    if anim == "idle":
        breathe = math.sin(cyc)
        pitch = 4.0 * math.sin(cyc)
        sniff = max(0.0, math.sin(cyc * 2.0))
        eyes = "shut" if i == 4 else "open"
    elif anim == "walk":
        gait, gait_amp = cyc, 1.0
        dy = -1.4 * abs(math.sin(cyc))
        tilt = 1.5 * math.sin(cyc)
        pitch = 6.0 + 3.0 * math.sin(cyc * 2.0)
    elif anim == "notice":
        # It rears up on its hind legs to look and to smell the air.
        k = math.sin(math.pi * min(1.0, t * 1.3))
        rear, pitch, eyes, alarm = 0.8 * k, -10.0 * k, "wide", True
        sniff = k
        dx = -4.0 * k
    elif anim == "windup":
        # Up on its hind legs, the near forepaw high and back, a roar.
        rear = 0.9 + 0.04 * math.sin(cyc)
        swipe = -104.0 + 5.0 * math.sin(cyc * 2.0)
        jaw = 0.6 + 0.3 * math.sin(cyc * 2.0)
        pitch, eyes, dx = -2.0, "narrow", -6.0
    elif anim == "attack_side":
        # The swipe: the paw comes forward and down (0..3), and the bear comes
        # down on its four feet (3..5).
        rear = [0.9, 0.82, 0.66, 0.42, 0.18, 0.0][i]
        swipe = [-104.0, -86.0, -5.0, 40.0, 60.0, 70.0][i]
        trail = [0.0, 0.7, 1.0, 0.6, 0.0, 0.0][i]
        dx = [-6.0, -2.0, 4.0, 8.0, 8.0, 6.0][i]
        jaw = [0.7, 0.9, 0.8, 0.5, 0.2, 0.0][i]
        pitch, eyes = [-2.0, 2.0, 6.0, 8.0, 6.0, 4.0][i], "narrow"
        if i >= 4:
            swipe = None
    elif anim == "hit":
        k = math.sin(math.pi * (i + 1) / (n + 1))
        pitch, dx, tilt, eyes, jaw = -16.0 * k, -6.0 * k, -3.0 * k, "shut", 0.4 * k
    elif anim == "death":
        u = min(1.0, t / 0.8)
        fold = min(1.0, u * 1.4)
        dy = 22.0 * fold
        tilt = 6.0 * fold
        pitch, eyes = 18.0 * fold, "shut"
        fade = 1.0 - max(0.0, t - 0.75) / 0.25

    # Reared up, the hind feet come forward under the body: the bear stands
    # over the middle of its box.
    dx += 22.0 * rear
    hip = (HIP[0] + dx, HIP[1] + dy)
    angle = tilt - 66.0 * rear

    def B(pts: Sequence[Point]) -> List[Point]:
        """Points of the body: moved, breathing, then turned about the hip."""
        out = [(x + dx, y + dy + (0.0 if y < 90 else 1.0 * breathe)) for x, y in pts]
        return K.turn(out, hip[0], hip[1], angle)

    def hind(root: Point, phase: float, near: bool) -> None:
        colour = FUR if near else FUR_SHADE
        sw = math.sin(phase) * gait_amp
        lift = max(0.0, math.cos(phase)) * 6.0 * gait_amp
        foot = (root[0] + 9.0 * sw - 4.0 * rear, GROUND - 8.0 - lift)
        if fold:
            knee = (root[0] - 4.0, min(GROUND - 10.0, root[1] + 14.0))
            foot = (root[0] + 16.0 * fold, GROUND - 8.0)
        else:
            knee, foot = S.joint(root, foot, UPPER, LOWER, 1.0)
        f.limb([root, knee], 22.0, colour)
        f.limb([knee, foot], 16.0, colour)
        _paw(f, foot[0] + 2.0, foot[1] + 2.0, near, 0.0)

    def fore(root: Point, phase: float, near: bool, offset: float) -> None:
        colour = FUR if near else FUR_SHADE
        sw = math.sin(phase) * gait_amp
        lift = max(0.0, math.cos(phase)) * 7.0 * gait_amp
        ground = (root[0] + 10.0 * sw + 2.0, GROUND - 8.0 - lift)
        # Reared up, the forepaws hang in front of the chest.
        raised = (root[0] + 22.0 + offset, root[1] + 14.0 + 2.0 * offset)
        u = min(1.0, rear * 1.2)
        target = (ground[0] + (raised[0] - ground[0]) * u, ground[1] + (raised[1] - ground[1]) * u)
        if fold:
            target = (root[0] + 24.0 * fold, GROUND - 8.0)
        knee, foot = S.joint(root, target, UPPER, LOWER, -1.0 + 2.0 * min(1.0, rear * 1.5))
        f.limb([root, knee], 20.0, colour)
        f.limb([knee, foot], 15.0, colour)
        _paw(f, foot[0] + 2.0, foot[1] + 2.0, near, min(1.0, rear * 1.4))

    def swiping(root: Point, a: float) -> Point:
        """The near foreleg out at the angle `a`, claws first. Returns the paw."""
        r = math.radians(a)
        upper, lower = UPPER + 5.0, LOWER + 5.0
        reach = (upper + lower) * 0.92
        target = (root[0] + math.cos(r) * reach, root[1] + math.sin(r) * reach)
        elbow, paw = S.joint(root, target, upper, lower, 1.0)
        # The leg is in front of the body and as black as it: a line of ink
        # round it keeps its shape clear.
        f.limb([root, elbow], 23.0, H.SEPIA_INK)
        f.limb([elbow, paw], 18.0, H.SEPIA_INK)
        f.ellipse(paw[0] + 2.0, paw[1], 12.0, 10.0, H.SEPIA_INK)
        f.limb([root, elbow], 20.0, FUR)
        f.limb([elbow, paw], 15.0, FUR)
        f.ink([root, elbow], 1.2, FUR_LIGHT)
        _paw(f, paw[0], paw[1], True, 1.0, a + 40.0)
        return paw

    # The far legs.
    hind(B([(60.0, 108.0)])[0], gait + math.pi, False)
    fore(B([(124.0, 104.0)])[0], gait, False, -6.0)

    # The body: a heavy barrel, a little higher at the shoulder.
    body = B([(32.0, 100.0), (38.0, 78.0), (60.0, 66.0), (96.0, 64.0), (118.0, 58.0), (136.0, 62.0), (150.0, 76.0), (157.0, 90.0), (154.0, 104.0),
              (140.0, 122.0), (100.0, 128.0), (60.0, 126.0), (38.0, 118.0)])
    f.poly(body, FUR)
    f.poly(B([(40.0, 112.0), (60.0, 120.0), (100.0, 122.0), (140.0, 116.0), (138.0, 124.0), (100.0, 129.0), (60.0, 127.0), (40.0, 119.0)]),
           FUR_SHADE, body=False)
    # The sheen of light on the back, and the long fur along it.
    f.poly(B([(52.0, 72.0), (70.0, 66.0), (100.0, 66.0), (120.0, 60.0), (134.0, 64.0), (122.0, 68.0), (100.0, 71.0), (70.0, 72.0)]),
           FUR_LIGHT, body=False)
    _fur(f, B([(44.0, 78.0), (64.0, 68.0), (96.0, 66.0), (118.0, 60.0)]), 7.0, FUR_SHADE, f"abb:back:{anim}:{i}")
    for k in range(3):
        x = 70.0 + k * 20.0
        f.ink(B([(x, 86.0), (x - 4.0, 106.0)]), 1.1, FUR_SHADE)
    # The stub of a tail.
    f.ellipse(*B([(33.0, 86.0)])[0], 5.0, 4.0, FUR_SHADE)

    # The near hind leg; the near foreleg goes on after the chest.
    hind(B([(54.0, 112.0)])[0], gait, True)

    # The head, on the neck: turned with the body, then by `pitch`. When it
    # rears it keeps its eyes on you.
    neck = B([(146.0, 80.0)])[0]
    # Reared up, the head comes forward over the chest: a raised forepaw
    # then shows behind it.
    neck = (neck[0] + 12.0 * rear, neck[1] + 6.0 * rear)
    pr = angle + pitch + 54.0 * rear

    def Hd(pts: Sequence[Point]) -> List[Point]:
        return K.turn([(neck[0] + x, neck[1] + y) for x, y in pts], neck[0], neck[1], pr)

    # The neck and the ruff: the long hair stands out round the neck.
    f.poly(Hd([(-18.0, -16.0), (-4.0, -24.0), (6.0, -18.0), (10.0, 16.0), (-8.0, 24.0), (-22.0, 10.0)]), FUR)
    for k in range(5):
        a = math.radians(110.0 + k * 22.0)
        cx, cy = Hd([(-6.0 + 20.0 * math.cos(a), 2.0 + 20.0 * math.sin(a) * 1.1)])[0]
        f.ellipse(cx, cy, 5.0, 5.0, FUR)
    _fur(f, Hd([(-16.0, -12.0), (-20.0, 0.0), (-16.0, 12.0)]), 6.0, FUR_SHADE, f"abb:ruff:{anim}:{i}", 1.1)

    # A forepaw raised high goes behind the head and the moon, so that both
    # stay clear; lower, it is in front of them.
    paw = None
    arm_root = B([(126.0, 98.0)])[0]
    if swipe is not None and swipe < -70.0:
        paw = swiping(arm_root, swipe)

    # The moon: a cream V on the chest, below the throat. Its two arms meet
    # low on the chest; the far arm shows round the front of the chest.
    # Reared up, the chest turns to you and the V stands upright.
    apex = B([(150.0, 106.0)])[0]

    def V(pts: Sequence[Point]) -> List[Point]:
        # Reared, the V sits lower on the chest, under the jaw.
        return [(x - 10.0 * rear * math.cos(math.radians(angle)), y - 10.0 * rear * math.sin(math.radians(angle)))
                for x, y in K.turn(B(pts), apex[0], apex[1], 50.0 * rear)]

    f.poly(V([(133.0, 82.0), (140.0, 79.0), (150.0, 100.0), (155.0, 85.0), (159.0, 88.0), (152.0, 112.0), (147.0, 112.0)]), MOON, body=False)
    f.poly(V([(150.0, 100.0), (155.0, 85.0), (159.0, 88.0), (152.0, 112.0)]), MOON_SHADE, body=False)

    # The near foreleg: on the ground, hanging in front of the chest, or
    # swiping.
    if swipe is None:
        fore(B([(132.0, 108.0)])[0], gait + math.pi, True, 6.0)

    # The lower jaw, open by `jaw`.
    jaw_pts = K.turn(Hd([(6.0, 8.0), (28.0, 7.0), (33.0, 9.0), (28.0, 13.0), (12.0, 15.0)]), *Hd([(8.0, 10.0)])[0], 32.0 * jaw)
    if jaw > 0.1:
        f.poly(Hd([(8.0, 6.0), (32.0, 6.0), (26.0, 16.0), (10.0, 18.0)]), MOUTH)
        jtop = jaw_pts[1]
        f.poly([(jtop[0] - 1.0, jtop[1]), (jtop[0] - 3.0, jtop[1] - 4.0), (jtop[0] - 5.0, jtop[1])], TEETH, body=False)
    f.poly(jaw_pts, MUZZLE)
    f.ink(jaw_pts[1:4], 1.0, MUZZLE_SHADE)
    # The ears: large and round, set wide on the head. The far ear stands
    # up behind the brow; the near ear stands out at the back of the head.
    for ex0, ey0, near in ((10.0, -24.0, False), (-6.0, -20.0, True)):
        x0, y0 = Hd([(ex0, ey0)])[0]
        f.ellipse(x0, y0, 7.6, 7.6, FUR if near else FUR_SHADE)
        if near:
            f.ellipse(x0 + 0.6, y0 + 0.6, 4.0, 4.0, EAR_INSIDE, body=False)
    # The skull: round, with a short muzzle.
    head = Hd([(-8.0, -10.0), (0.0, -20.0), (14.0, -21.0), (24.0, -12.0), (34.0, -6.0), (39.0, -1.0), (40.0, 5.0), (35.0, 8.0), (24.0, 10.0),
               (10.0, 12.0), (-6.0, 8.0)])
    f.poly(head, FUR)
    # The tan muzzle.
    f.poly(Hd([(22.0, -10.0), (32.0, -6.0), (39.0, -1.0), (40.0, 5.0), (35.0, 8.0), (24.0, 9.6), (20.0, 2.0)]), MUZZLE, body=False)
    f.poly(Hd([(22.0, 4.0), (35.0, 6.0), (24.0, 9.6)]), MUZZLE_SHADE, body=False)
    if jaw > 0.1:
        # The upper fangs.
        for x in (31.0, 24.0):
            f.poly(Hd([(x, 8.0), (x + 1.6, 13.0), (x + 3.0, 8.0)]), TEETH, body=False)
    # The nose and the eye.
    nx, ny = Hd([(39.0, 0.0)])[0]
    f.ellipse(nx, ny, 3.4, 2.8, NOSE, body=False)
    ex, ey = Hd([(18.0, -8.0)])[0]
    if eyes == "shut":
        f.ink([(ex - 2.2, ey), (ex + 2.2, ey + 0.5)], 1.2, EYE)
    else:
        r = {"open": 1.8, "wide": 2.4, "narrow": 1.2}[eyes]
        f.ellipse(ex, ey, 2.1, r, (150, 104, 60, 255), body=False)
        f.dot(ex + 0.5, ey, 1.0, EYE)
        f.dot(ex - 0.4, ey - 0.6, 0.4, (240, 230, 210, 255))
        if eyes == "narrow":
            f.ink([(ex - 3.0, ey - 2.8), (ex + 2.6, ey - 0.8)], 1.3, NOSE)
    if swipe is not None and swipe >= -70.0:
        paw = swiping(arm_root, swipe)
    if sniff > 0.3:
        # The bear sniffs: short lines of air at its nose.
        for k in range(2):
            y = ny - 2.0 + k * 4.0
            f.ink([(nx + 5.0, y), (nx + 9.0 + 2.0 * sniff, y - 1.0)], 1.1, K.alpha(K.WHITE, 0.7 * sniff))
    if jaw > 0.5 and anim == "windup":
        # The roar: lines out of the open mouth.
        mx, my = Hd([(36.0, 12.0)])[0]
        for k in range(3):
            a = math.radians(-30.0 + k * 30.0)
            f.ink([(mx + math.cos(a) * 8.0, my + math.sin(a) * 8.0), (mx + math.cos(a) * (8.0 + 8.0 * jaw), my + math.sin(a) * (8.0 + 8.0 * jaw))],
                  1.6, K.alpha(K.WHITE, jaw))
    if paw is not None and trail > 0.05:
        # The swipe: three pale arcs behind the claws.
        root = arm_root
        a1 = math.radians(swipe)
        for k in range(3):
            r = (UPPER + LOWER + 10.0) * 0.92 + 8.0 + k * 5.0
            arc = [(root[0] + math.cos(a1 - s * 0.9 * trail) * r, root[1] + math.sin(a1 - s * 0.9 * trail) * r) for s in (0.0, 0.25, 0.5, 0.75, 1.0)]
            f.glow_line(arc, 1.6, K.alpha(K.WHITE, 0.85 * trail * (1.0 - 0.2 * k)))
    if anim == "attack_side" and i >= 4:
        H.dust(f, B([(140.0, 0.0)])[0][0], GROUND - 2.0, 0.8 if i == 4 else 0.4, f"abb:land:{i}", spread=1.4, colour=DUST)
    if anim == "death" and t > 0.3:
        H.dust(f, 96.0, GROUND - 2.0, min(1.0, (t - 0.3) * 2.0), f"abb:death:{i}", spread=2.4, colour=DUST)
    out = f.finish(outline=H.SEPIA_INK, width=1.7, fade=fade)
    if alarm:
        # The "!" is drawn on a frame of its own, at full size.
        g = K.Frame(FRAME_SIZE)
        ax, ay = Hd([(8.0, -36.0)])[0]
        ax = PIVOT[0] + (ax - PIVOT[0]) * SIZE
        ay = PIVOT[1] + (ay - PIVOT[1]) * SIZE
        H.alarm_mark(g, min(FRAME_SIZE[0] - MARGIN - 4.0, ax), max(MARGIN + 11.0, ay))
        out.alpha_composite(g.finish(outline=H.SEPIA_INK, width=1.4))
    return out


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
