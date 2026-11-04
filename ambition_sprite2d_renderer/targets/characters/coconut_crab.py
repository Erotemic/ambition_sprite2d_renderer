"""The Coconut Crab of the History dimension: the robber crab of the Pacific islands.

The largest crab that lives on land: a hermit crab that grew too big for
any shell. Its back is a hard blue-violet shield; its legs are long and
orange-red, with purple at the joints. Its left claw is huge (it can crack
a coconut), the right one is smaller. Its soft tail is tucked up under its
body, and two long feelers sweep in front of its eyes on their stalks.

It walks sideways. When it sees you it lifts both claws and spreads its
legs wide. Its windup holds the big claw up and open; its strike is a step
to the front and the pinch: the big claw snaps shut. A hit knocks it back
with its legs pulled in; at its death its legs fold and it sinks down.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import List, Tuple

from . import _art_cast_kit as K
from . import _history_americas_kit as A
from . import _history_steppe_kit as H

TARGET_NAME = "coconut_crab"
FRAME_SIZE = (160, 96)
ROWS = K.ENEMY_ROWS
GROUND = 88.0

ACTOR_METADATA = A.enemy_metadata(
    TARGET_NAME, "Coconut Crab", "lapita_voyagers", "Multileg", "Standard", "Medium", "Walk", ["crab", "claw", "pinch", "island"],
    "The coconut crab (the robber crab) of the History dimension's Lapita islands: a blue-violet shield, long orange "
    "legs and one huge claw. It walks sideways, lifts the big claw open, and pinches.",
)

SHELL = (82, 74, 150, 255)
SHELL_SHADE = (54, 46, 104, 255)
SHELL_LIGHT = (132, 126, 196, 255)
LEG = (222, 104, 56, 255)
LEG_SHADE = (170, 70, 40, 255)
JOINT = (122, 70, 132, 255)
CLAW = (226, 112, 62, 255)
CLAW_SHADE = (176, 76, 44, 255)
CLAW_TIP = (48, 30, 40, 255)
TAIL = (196, 132, 150, 255)
TAIL_SHADE = (150, 92, 116, 255)
FEELER = (196, 96, 60, 255)

Point = Tuple[float, float]


def _claw(pen: H.ScaledPen, base: Point, tip: Point, size: float, open_: float, colour, shade) -> None:
    """A claw from `base` toward `tip`: a fat palm with nubbly ridges and two
    fingers; the upper finger opens by `open_` (0 shut, 1 wide)."""
    ang = math.atan2(tip[1] - base[1], tip[0] - base[0])
    ux, uy = math.cos(ang), math.sin(ang)
    nx, ny = uy, -ux

    def at(a: float, b: float) -> Point:
        return (base[0] + ux * a + nx * b, base[1] + uy * a + ny * b)

    palm = [at(0.0, -4.4 * size), at(10.0 * size, -6.4 * size), at(15.0 * size, -4.0 * size), at(15.0 * size, 2.6 * size), at(9.0 * size, 6.4 * size),
            at(0.0, 4.6 * size)]
    pen.poly(palm, colour)
    pen.poly([at(0.0, -4.4 * size), at(10.0 * size, -6.4 * size), at(15.0 * size, -4.0 * size), at(9.0 * size, -1.2 * size), at(0.0, -1.8 * size)],
             shade, body=False)
    # The ridges of little knobs along the palm.
    for k in range(4):
        pen.dot(*at((2.6 + k * 3.0) * size, (2.6 - 0.2 * k) * size), 0.7 * size, K.shade(colour, 1.25))
    lower = [at(14.0 * size, -1.6 * size), at(23.0 * size, -2.2 * size), at(24.0 * size, 0.4 * size), at(14.0 * size, 2.8 * size)]
    pen.poly(lower, colour)
    pen.poly([at(19.0 * size, -1.8 * size), at(24.0 * size, -2.2 * size), at(24.0 * size, 0.4 * size), at(19.0 * size, 1.4 * size)], CLAW_TIP, body=False)
    gap = 28.0 * open_
    piv = at(14.0 * size, 4.0 * size)
    upper = [at(14.0 * size, 1.6 * size), at(22.0 * size, 3.0 * size), at(24.6 * size, 0.6 * size), at(22.6 * size, 4.6 * size), at(14.0 * size, 6.0 * size)]
    upper = K.turn(upper, piv[0], piv[1], -gap if ux >= 0 else gap)
    pen.poly(upper, colour)
    pen.poly(upper[1:4], CLAW_TIP, body=False)
    # The teeth on the inner edge of the fixed finger.
    for k in range(3):
        pen.dot(*at((15.5 + k * 2.4) * size, 1.6 * size), 0.5 * size, K.shade(colour, 1.35))


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = K.Frame(FRAME_SIZE)
    dx, dy, tilt, scuttle = 0.0, 0.0, 0.0, None
    big_up, small_up, big_open, small_open, eyes, stalks = 0.0, 0.0, 0.15, 0.15, "open", 0.0
    alarm, flip, fade, snap, spread, tuck = False, 0.0, 1.0, 0.0, 0.0, 0.0
    feel = math.sin(cyc)
    if anim == "idle":
        dy = 0.6 * math.sin(cyc)
        big_open = 0.1 + 0.2 * max(0.0, math.sin(cyc))
        small_up = 0.3 + 0.3 * max(0.0, math.sin(cyc + 2.0))
        stalks = 1.0 * math.sin(cyc + 1.0)
    elif anim == "walk":
        scuttle = t
        dy = -1.6 * abs(math.sin(cyc * 2.0))
        dx = 2.0 * math.sin(cyc)
        tilt = 2.0 * math.sin(cyc * 2.0)
        stalks = 1.4 * math.sin(cyc * 2.0)
        feel = math.sin(cyc * 2.0)
    elif anim == "notice":
        k = math.sin(math.pi * min(1.0, t * 1.3))
        big_up, small_up, big_open, small_open, eyes, alarm, stalks, spread = 0.9 * k, k, 0.7 * k, 0.6 * k, "wide", True, 3.0 * k, k
        dy = -3.0 * k
    elif anim == "windup":
        big_up, small_up, spread = 1.0, 0.7, 0.6
        big_open = 0.85 + 0.12 * math.sin(cyc * 2.0)
        small_open = 0.5 + 0.15 * math.sin(cyc * 2.0 + 1.0)
        dy, dx, tilt, eyes = -3.0, -3.0, -1.5, "narrow"
    elif anim == "attack_side":
        # The step to the front (0..2), the pinch (2..3), and back.
        u = min(1.0, t / 0.45)
        back = max(0.0, (t - 0.55) / 0.45)
        dx = -5.0 + 11.0 * math.sin(math.pi * 0.5 * u) - 6.0 * back
        big_up = 1.0 - 1.1 * u + 0.3 * back
        big_open = 0.95 if i < 2 else 0.0
        small_up, small_open, eyes, tilt = 0.6, 0.4, "narrow", 4.0 * u * (1.0 - back)
        scuttle = t * 2.0
        snap = 1.0 if i in (2, 3) else 0.0
    elif anim == "hit":
        k = math.sin(math.pi * (i + 1) / (n + 1))
        dx, tilt, eyes, big_open, small_open, stalks, tuck = -6.0 * k, -4.0 * k, "shut", 0.5, 0.5, -3.0, k
    elif anim == "death":
        sink = min(1.0, t * 1.5)
        tuck, dy, tilt, stalks = 1.3 * sink, 9.0 * sink, -5.0 * sink, -4.0 * sink
        eyes, big_open, small_open = "x", 0.4, 0.4
        fade = 1.0 - max(0.0, t - 0.7) / 0.3

    cx, cy = 73.0 + dx, GROUND - 24.0 + dy
    rot = tilt + 180.0 * flip
    shift = (0.0, -24.0 * math.sin(math.pi * flip) - 8.0 * flip)
    pen = H.ScaledPen(f, (cx, cy), rot, shift)

    # The legs: four on each side, long, jointed and arched, purple at the joints.
    def legs(side: float, colour, shade) -> None:
        for k in (3, 2, 1, 0):
            root = (cx + side * (8.0 + k * 3.0), cy + 2.0)
            reach = 18.0 + k * 8.0 + 6.0 * spread - 8.0 * tuck
            ph = 0.0 if scuttle is None else (scuttle + k * 0.25 + (0.5 if side > 0 else 0.0)) % 1.0
            lift = 5.0 * max(0.0, math.sin(math.tau * ph)) if scuttle is not None else 0.0
            step = 3.0 * math.cos(math.tau * ph) if scuttle is not None else 0.0
            knee = (cx + side * (reach * 0.86), cy - 22.0 + k * 2.0 - lift * 0.6 - 3.0 * spread + 6.0 * tuck)
            foot = (cx + side * (reach + 9.0) + step, GROUND - lift - 2.0 * tuck)
            if flip:
                knee = (cx + side * (reach * 0.55), cy - 2.0 + k * 1.6)
                foot = (cx + side * (reach * 0.42) + 3.0 * math.sin(cyc * 3.0 + k), cy + 10.0 - 1.6 * k)
            c = colour if k % 2 else shade
            pen.limb([root, knee], 4.2, c)
            pen.limb([knee, foot], 3.0, c)
            pen.dot(knee[0], knee[1], 1.6, JOINT)
            pen.dot(foot[0], foot[1], 1.1, CLAW_TIP)

    # The back legs, the far side, behind the body.
    legs(-1.0, LEG_SHADE, K.shade(LEG_SHADE, 0.85))

    # The soft tail, curled up under the back of the body.
    pen.ellipse(cx - 20.0, cy + 8.0, 12.0, 9.0, TAIL)
    pen.ellipse(cx - 21.0, cy + 11.0, 9.0, 5.0, TAIL_SHADE, body=False)
    for k in range(3):
        pen.ink([(cx - 30.0 + k * 5.0, cy + 2.0 + k), (cx - 27.0 + k * 5.0, cy + 15.0 - k)], 0.8, TAIL_SHADE)

    # The small claw, behind the big one.
    sbase = (cx + 14.0, cy - 2.0)
    selbow = (sbase[0] + 7.0, sbase[1] - 2.0 - 7.0 * small_up)
    stip = (selbow[0] + 9.0, selbow[1] - 4.0 - 10.0 * small_up)
    pen.limb([sbase, selbow], 5.0, CLAW_SHADE)
    _claw(pen, selbow, stip, 0.7, small_open, CLAW_SHADE, K.shade(CLAW_SHADE, 0.8))

    # The body: a broad shield, raised at the front where the eyes are.
    body = [(cx - 26.0, cy + 4.0), (cx - 24.0, cy - 8.0), (cx - 12.0, cy - 16.0), (cx + 8.0, cy - 17.0), (cx + 22.0, cy - 12.0), (cx + 26.0, cy - 2.0),
            (cx + 22.0, cy + 10.0), (cx + 4.0, cy + 14.0), (cx - 16.0, cy + 12.0)]
    pen.poly(body, SHELL)
    pen.poly([(cx - 26.0, cy + 4.0), (cx - 16.0, cy + 12.0), (cx + 4.0, cy + 14.0), (cx + 22.0, cy + 10.0), (cx + 24.0, cy + 4.0), (cx + 2.0, cy + 7.0),
              (cx - 18.0, cy + 4.0)], SHELL_SHADE, body=False)
    pen.poly([(cx - 14.0, cy - 13.0), (cx + 6.0, cy - 15.0), (cx + 16.0, cy - 11.0), (cx + 2.0, cy - 10.0), (cx - 10.0, cy - 9.0)], SHELL_LIGHT, body=False)
    # The grooves of the shield.
    pen.ink([(cx - 6.0, cy - 15.0), (cx - 2.0, cy - 4.0), (cx - 8.0, cy + 8.0)], 0.9, SHELL_SHADE)
    pen.ink([(cx + 10.0, cy - 15.0), (cx + 8.0, cy - 4.0), (cx + 12.0, cy + 8.0)], 0.9, SHELL_SHADE)
    for k in range(5):
        pen.dot(cx - 18.0 + k * 9.0, cy - 2.0 + (k % 2) * 3.0, 0.9, K.shade(SHELL_LIGHT, 1.1))

    # The near legs, in front of the body.
    legs(1.0, LEG, K.shade(LEG, 0.9))

    # The eyes on their stalks, and the long feelers that sweep in front.
    for k, ex0 in enumerate((cx + 16.0, cx + 21.0)):
        top = (ex0 + 2.0 + stalks * 0.3, cy - 22.0 - 2.0 * (k == 1) - abs(stalks) * 0.4 + (4.0 if eyes == "shut" else 0.0))
        pen.limb([(ex0, cy - 14.0), top], 2.4, SHELL_SHADE)
        r = 3.0 if eyes == "wide" else 2.5
        pen.ellipse(top[0], top[1], r, r, (30, 26, 34, 255))
        if eyes == "shut":
            pen.ink([(top[0] - 1.6, top[1]), (top[0] + 1.6, top[1])], 0.9, K.WHITE)
        elif eyes == "x":
            pen.ink([(top[0] - 1.4, top[1] - 1.4), (top[0] + 1.4, top[1] + 1.4)], 0.7, K.WHITE)
            pen.ink([(top[0] - 1.4, top[1] + 1.4), (top[0] + 1.4, top[1] - 1.4)], 0.7, K.WHITE)
        else:
            pen.dot(top[0] + 0.8, top[1] - 0.8, 0.8, K.WHITE)
            if eyes == "narrow":
                pen.ink([(top[0] - 2.6, top[1] - 2.6), (top[0] + 2.4, top[1] - 1.2)], 0.9, SHELL_SHADE)
    for k in range(2):
        root = (cx + 22.0 + k * 2.0, cy - 12.0)
        sweep = 6.0 * feel * (1 if k else -1)
        mid = (root[0] + 14.0, root[1] - 14.0 - 4.0 * k + sweep * 0.4)
        tip = (min(150.0, root[0] + 30.0 + sweep), max(6.0, root[1] - 24.0 + 8.0 * k + sweep))
        pen.ink([root, mid, tip], 1.0, FEELER)

    # The big claw, at the front: it can crack a coconut.
    bbase = (cx + 20.0, cy + 2.0)
    belbow = (bbase[0] + 9.0, bbase[1] + 4.0 - 14.0 * big_up)
    btip = (belbow[0] + 14.0 - 6.0 * big_up, belbow[1] - 1.0 - 14.0 * big_up)
    pen.limb([bbase, belbow], 8.0, CLAW)
    pen.dot(belbow[0], belbow[1], 2.8, JOINT)
    _claw(pen, belbow, btip, 1.45, big_open, CLAW, CLAW_SHADE)

    if snap:
        tx, ty = pen.at(btip[0] + 14.0, btip[1])
        for k in range(4):
            a = math.radians(-60.0 + k * 40.0)
            f.glow_line([(tx + math.cos(a) * 3.0, ty + math.sin(a) * 3.0), (min(154.0, tx + math.cos(a) * 9.0), ty + math.sin(a) * 9.0)], 1.4,
                        K.alpha(K.WHITE, 0.9))
    if anim == "hit":
        rng = random.Random(f"coconut_crab:hit:{i}")
        for k in range(4):
            px, py = cx + rng.uniform(-10.0, 14.0), cy - 22.0 - rng.uniform(0.0, 10.0)
            f.glow_line([(px, py), (px + rng.uniform(-3.0, 3.0), py - 5.0)], 1.2, K.alpha(K.WHITE, 0.7))
    if anim == "death" and t > 0.3:
        A.dust(f, cx, GROUND - 4.0, 30.0, min(1.0, (t - 0.3) * 2.0), f"coconut_crab:death:{i}")
    if alarm:
        A.alarm_mark(f, min(146.0, cx + 30.0), max(14.0, cy - 40.0))
    return A.finish(f, fade=fade, width=1.3)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
