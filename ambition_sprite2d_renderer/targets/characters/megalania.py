"""The Megalania: the giant monitor lizard of Ice Age Australia.

A monitor lizard as long as a car, long and low: a heavy body on sprawled
legs with curved claws, a long tail as long again as its body, and a long
head with a pale jaw, small sharp teeth and a forked tongue. Its scales are
a dark olive brown with bands of pale yellow speckles across its back.

It walks with a sway, its legs out to its sides and its tail swinging. It
flicks its tongue to taste the air. When it sees you it lifts its head and
hisses. Its windup lifts the front of its body on its forelegs and opens
its jaws; its strike is a lunge: it throws its head forward low and snaps.
A hit makes it flinch and hiss; at its death it sinks flat and lies still.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Sequence, Tuple

from . import _art_cast_kit as K
from . import _history_americas_kit as A
from . import _stage_kit as S

TARGET_NAME = "megalania"
FRAME_SIZE = (256, 96)
ROWS = K.ENEMY_ROWS
GROUND = 91.0

ACTOR_METADATA = A.enemy_metadata(
    TARGET_NAME, "Megalania", "sahul", "Quadruped", "Large", "Heavy", "Walk", ["lizard", "monitor", "lunge"],
    "The giant monitor lizard of the History dimension's Sahul: long and low, dark olive with pale speckled bands. "
    "It lifts the front of its body and opens its jaws, then lunges low and snaps.",
)

SCALE = (92, 90, 62, 255)
SCALE_SHADE = (64, 62, 44, 255)
SCALE_DARK = (44, 42, 32, 255)
SPECKLE = (226, 206, 120, 255)
BELLY = (196, 182, 134, 255)
JAW = (210, 196, 150, 255)
MOUTH = (176, 70, 84, 255)
TONGUE = (120, 96, 170, 255)
EYE = (232, 170, 50, 255)
CLAW = (230, 220, 196, 255)

Point = Tuple[float, float]

#: The spine from the neck back to the tip of the tail (x, y, half the
#: depth of the body there). The head is drawn at the front of it.
SPINE = [(184.0, 56.0, 11.0), (168.0, 57.0, 15.0), (150.0, 58.0, 18.0), (130.0, 58.0, 19.5), (110.0, 59.0, 18.0), (94.0, 61.0, 14.0),
         (78.0, 64.0, 10.5), (62.0, 68.0, 7.5), (46.0, 72.0, 5.0), (32.0, 75.0, 3.4), (18.0, 76.0, 2.0)]
#: The size of the head.
HEAD = 1.15
SHOULDER_K, HIP_K = 2, 5


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = K.Frame(FRAME_SIZE)

    dx, rear, jaw, tongue, sway, walk, head_up, eyes, flat, fade, alarm = 0.0, 0.0, 0.0, 0.0, 0.0, None, 0.0, "open", 0.0, 1.0, False
    tail_lift = 0.0
    if anim == "idle":
        tongue = max(0.0, math.sin(cyc * 2.0)) if i in (1, 2, 4) else 0.0
        sway = 0.4 * math.sin(cyc)
        head_up = 2.0 * math.sin(cyc)
    elif anim == "walk":
        walk = t
        sway = math.sin(cyc)
        tongue = 1.0 if i == 5 else 0.0
    elif anim == "notice":
        k = math.sin(math.pi * min(1.0, t * 1.3))
        head_up, jaw, eyes, alarm, tongue = 10.0 * k, 0.4 * k, "wide", True, 0.0
        tail_lift = 0.4 * k
    elif anim == "windup":
        rear = 1.0 + 0.1 * math.sin(cyc * 2.0)
        head_up, jaw, eyes = 6.0, 0.6 + 0.15 * math.sin(cyc * 2.0), "narrow"
        dx, tail_lift = -6.0, 0.6
        sway = 0.5 * math.sin(cyc * 2.0)
    elif anim == "attack_side":
        # The lunge: low and forward, the jaws snap shut at the end.
        u = t
        go = math.sin(math.pi * 0.5 * min(1.0, u * 1.7))
        dx = -6.0 + 16.0 * go - 10.0 * max(0.0, u - 0.6) / 0.4
        rear = max(0.0, 1.0 - u * 3.0)
        head_up = 6.0 * (1.0 - go) - 6.0 * go
        jaw = 1.0 if u < 0.45 else max(0.0, 1.0 - (u - 0.45) * 4.0)
        eyes, tail_lift = "narrow", 0.5
        sway = 0.6 * math.sin(cyc * 1.5)
    elif anim == "hit":
        k = math.sin(math.pi * t)
        dx, head_up, jaw, eyes = -5.0 * k, 10.0 * k, 0.5 * k, "shut"
        tail_lift = 0.3 * k
    elif anim == "death":
        u = min(1.0, t / 0.8)
        flat, eyes, head_up = u, "shut", -4.0 * u
        fade = 1.0 - max(0.0, t - 0.75) / 0.25

    # The spine of this frame: moved, the front lifted by the rear, the tail swayed.
    spine: List[Tuple[float, float, float]] = []
    hip_x = SPINE[HIP_K][0]
    for k, (x, y, r) in enumerate(SPINE):
        x += dx * (1.0 if k <= HIP_K else 1.0 - 0.6 * (k - HIP_K) / (len(SPINE) - 1 - HIP_K))
        y += 4.0 * flat
        if x > hip_x + dx and rear:
            y -= rear * 0.30 * (x - hip_x - dx)
        if k > HIP_K:
            w = (k - HIP_K) / (len(SPINE) - 1 - HIP_K)
            y += 3.0 * sway * math.sin(math.pi * w * 1.5) - 10.0 * tail_lift * w * w
        if walk is not None and k <= HIP_K:
            y -= 1.0 * abs(math.sin(math.tau * walk * 2.0))
        spine.append((x, y, r * (1.0 - 0.12 * flat)))

    def normal(k: int) -> Point:
        a = spine[max(0, k - 1)]
        b = spine[min(len(spine) - 1, k + 1)]
        dxs, dys = a[0] - b[0], a[1] - b[1]
        d = math.hypot(dxs, dys) or 1.0
        return (-dys / d, dxs / d)

    def top_of(k: int, s: float = 1.0) -> Point:
        x, y, r = spine[k]
        nx, ny = normal(k)
        return (x - nx * r * s, y - ny * r * s)

    def bottom_of(k: int, s: float = 1.0) -> Point:
        x, y, r = spine[k]
        nx, ny = normal(k)
        return (x + nx * r * s * 0.9, y + ny * r * s * 0.9)

    def leg(k: int, ph: float, front: bool, near: bool) -> None:
        colour = SCALE if near else SCALE_SHADE
        root = (spine[k][0] + (2.0 if near else -3.0), spine[k][1] + 8.0)
        fx = root[0] + (6.0 if front else -4.0)
        fy = GROUND - 3.0
        if walk is not None:
            gx, gy = A.gait(ph, 20.0, 6.0)
            fx += gx
            fy += gy
        if flat:
            fx += (10.0 if front else -10.0) * flat
        # A sprawled leg: the elbow sticks up and out above the body line.
        elbow, foot = S.joint(root, (fx, fy), 15.0, 16.0, 1.0 if front else -1.0)
        elbow = (elbow[0], min(elbow[1], GROUND - 6.0))
        f.limb([root, elbow], 12.0, colour)
        f.limb([elbow, foot], 8.5, colour)
        f.ellipse(foot[0] + 3.0, foot[1] + 0.4, 7.0, 2.6, colour)
        if near:
            for c in range(3):
                cx = foot[0] + 6.0 + c * 2.0
                f.ink([(cx, foot[1] + 0.2), (cx + 2.6, foot[1] + 1.6)], 0.9, CLAW)

    ph = walk or 0.0
    leg(SHOULDER_K, ph + 0.5, True, False)
    leg(HIP_K, ph, False, False)

    # The body and the tail: one long shape round the spine.
    upper = [top_of(k) for k in range(len(spine))]
    lower = [bottom_of(k) for k in range(len(spine))]
    tip = spine[-1]
    f.poly(upper + [(tip[0] - 6.0, tip[1] + 1.0)] + lower[::-1], SCALE)
    f.poly([bottom_of(k, 0.55) for k in range(len(spine) - 2)] + [bottom_of(k) for k in range(len(spine) - 3, -1, -1)], BELLY, body=False)
    f.poly([top_of(k) for k in range(len(spine) - 1)] + [top_of(k, 0.6) for k in range(len(spine) - 2, -1, -1)], SCALE_SHADE, body=False)
    # The bands of pale speckles across the back.
    for k in range(1, len(spine) - 2):
        a = top_of(k, 0.75)
        b = top_of(k, 0.05)
        for s in range(4):
            u = (s + 0.5) / 4.0
            x, y = A.lerp(a, b, u)
            f.ellipse(x + (s % 2) * 1.6, y, 1.4, 1.1, SPECKLE, body=False)
    # Rows of scales: short lines along the flank.
    for k in range(0, len(spine) - 3):
        x, y = A.lerp(top_of(k, 0.1), bottom_of(k, 0.2), 0.5)
        f.ink([(x - 3.0, y), (x + 3.0, y - 0.4)], 0.6, SCALE_DARK)

    leg(SHOULDER_K, ph, True, True)
    leg(HIP_K, ph + 0.5, False, True)

    # The head: long, at the front of the neck, turned up by `head_up`.
    nx0, ny0, _ = spine[0]
    ang = -head_up - (rear * 14.0)

    def Hd(*pts: Point) -> List[Point]:
        return K.turn([(nx0 + x * HEAD, ny0 + y * HEAD) for x, y in pts], nx0, ny0, ang)

    hinge = Hd((10.0, 4.0))[0]
    gape = 34.0 * jaw
    lower_jaw = K.turn(Hd((6.0, 4.0), (40.0, 4.0), (40.0, 6.6), (24.0, 9.0), (6.0, 9.0)), hinge[0], hinge[1], gape)
    if jaw > 0.05:
        f.poly([Hd((10.0, 4.0))[0], Hd((40.0, 3.0))[0], lower_jaw[2], lower_jaw[3]], MOUTH, body=False)
        # Small sharp teeth on both jaws.
        for c in range(5):
            x0 = 16.0 + c * 5.0
            up = Hd((x0, 3.4), (x0 + 1.2, 6.0), (x0 + 2.4, 3.4))
            f.poly(up, K.WHITE, body=False)
            lo = K.turn(Hd((x0 - 1.0, 4.6), (x0 + 0.2, 2.0), (x0 + 1.4, 4.6)), hinge[0], hinge[1], gape)
            f.poly(lo, K.WHITE, body=False)
    f.poly(lower_jaw, JAW)
    f.poly(Hd((-4.0, -8.0), (12.0, -10.0), (30.0, -6.0), (42.0, -1.0), (44.0, 2.0), (40.0, 4.0), (10.0, 4.6), (-4.0, 8.0)), SCALE)
    f.poly(Hd((-2.0, -7.0), (12.0, -9.0), (30.0, -5.0), (12.0, -5.6)), SCALE_SHADE, body=False)
    f.ink(Hd((8.0, 3.6), (40.0, 2.4)), 0.9, SCALE_DARK)
    f.dot(*Hd((40.0, -1.0))[0], 0.9, SCALE_DARK)
    ex, ey = Hd((14.0, -4.0))[0]
    if eyes == "shut":
        f.ink([(ex - 2.4, ey), (ex + 2.4, ey + 0.3)], 1.0, A.SEPIA_INK)
    else:
        r = {"open": 1.8, "wide": 2.4, "narrow": 1.1}[eyes]
        f.ellipse(ex, ey, 2.4, r, EYE, body=False)
        f.ellipse(ex + 0.4, ey, 0.7, min(r, 1.6), A.SEPIA_INK, body=False)
        if eyes == "narrow":
            f.ink([(ex - 3.0, ey - 2.4), (ex + 2.6, ey - 1.2)], 1.0, A.SEPIA_INK)
    if tongue > 0.1 and jaw < 0.2:
        # The forked tongue tastes the air.
        tx, ty = Hd((43.0, 3.0))[0]
        L = 5.0 + 8.0 * tongue
        end = (min(250.0, tx + L), ty + 1.0)
        f.ink([(tx, ty), end], 1.4, TONGUE)
        f.ink([end, (end[0] + 3.0, end[1] - 2.0)], 1.0, TONGUE)
        f.ink([end, (end[0] + 3.0, end[1] + 2.0)], 1.0, TONGUE)
    if anim == "attack_side" and 0.4 < t < 0.8:
        # The snap: lines round the closing jaws.
        mx, my = Hd((44.0, 4.0))[0]
        for c in (-1.0, 0.0, 1.0):
            f.glow_line([(min(244.0, mx + 3.0), my + c * 4.0), (min(249.0, mx + 8.0), my + c * 6.0)], 1.2, K.alpha(K.WHITE, 0.8))
    if anim == "death" and t > 0.3:
        A.dust(f, 120.0, GROUND - 4.0, 40.0, min(1.0, (t - 0.3) * 2.0), f"megalania:death:{i}")
    if alarm:
        hx, hy = Hd((20.0, -10.0))[0]
        A.alarm_mark(f, min(244.0, hx + 6.0), max(17.0, hy - 16.0))
    return A.finish(f, fade=fade, width=1.5)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
