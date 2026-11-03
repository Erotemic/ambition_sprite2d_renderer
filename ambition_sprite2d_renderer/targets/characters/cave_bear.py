"""The Cave Bear: the huge bear of the caves of Ice Age Europe.

A bear larger than any bear alive now, dark brown with a grizzled light tip
on its hump. Its forehead is steep, as the skulls in the caves show, and
its muzzle is long. Its claws are pale and long.

It is heavy and walks with a roll of its shoulders. At rest it sways and
sniffs the air. When it sees you it lifts its head and roars. Its windup
rears it up on its hind legs with its forepaws high and its claws out; its
strike brings it down on you with both paws, and the ground shakes. A hit
makes it flinch and shut its eyes; at its death it lies down on its side.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Sequence, Tuple

from . import _art_cast_kit as K
from . import _history_cast_kit as H
from . import _history_europe_kit as E
from . import _stage_kit as S

TARGET_NAME = "cave_bear"
FRAME_SIZE = (192, 160)
ROWS = K.ENEMY_ROWS
GROUND = 156.0

ACTOR_METADATA = H.enemy_metadata(
    TARGET_NAME, "Cave Bear", "Quadruped", "Large", "Heavy", "Walk", ["bear", "claws", "rears", "ice_age"],
    "The huge bear of the caves of Ice Age Europe in the History dimension: dark brown, with a steep forehead and long "
    "pale claws. It roars when it sees you, rears up on its hind legs with its claws out, and comes down on you with both paws.",
    "ice_age",
)

Point = Tuple[float, float]

SIZE = 0.8
PIVOT = (92.0, GROUND)
UPPER, LOWER = 21.0, 22.0
NOSE = (30, 22, 20, 255)
MOUTH = (150, 50, 56, 255)
TEETH = (244, 236, 216, 255)
CLAW = (236, 226, 204, 255)
EYE = (36, 22, 16, 255)
HIP = (58.0, 102.0)


def _paw(f: K.Frame, x: float, y: float, near: bool, up: float) -> None:
    """A paw at (`x`, `y`): a round pad and three pale claws, which point
    forward on the ground and up and forward when the paw is raised."""
    colour = E.BEAR_FUR_DARK if near else K.shade(E.BEAR_FUR_DARK, 0.85)
    big = 1.0 + 0.3 * up
    f.ellipse(x + 2.0, y, 8.0 * big, 5.0 * big + 2.0 * up, colour)
    for k in range(3):
        a = math.radians(-50.0 * up + (k - 1) * (14.0 + 10.0 * up))
        bx, by = x + 2.0 + 7.0 * big * math.cos(a), y + 5.0 * big * math.sin(a)
        ln = 3.0 + 5.0 * up
        tip = (bx + ln * math.cos(a + 0.5), by + ln * math.sin(a + 0.5))
        f.limb([(bx, by), tip], 1.8, CLAW if near else E.IVORY_SHADE)


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = E.ScaledFrame(FRAME_SIZE, SIZE, PIVOT)

    dx, dy, tilt, pitch, breathe = 0.0, 0.0, 0.0, 0.0, 0.0
    gait, gait_amp, rear, jaw, eyes, fade = 0.0, 0.0, 0.0, 0.0, "open", 1.0
    sniff, fold, slam, alarm = 0.0, 0.0, 0.0, False
    if anim == "idle":
        breathe = math.sin(cyc)
        pitch = 4.0 * math.sin(cyc)
        sniff = max(0.0, math.sin(cyc * 2.0))
    elif anim == "walk":
        gait, gait_amp = cyc, 1.0
        dy = -1.4 * abs(math.sin(cyc))
        tilt = 1.5 * math.sin(cyc)
        pitch = 6.0 + 3.0 * math.sin(cyc * 2.0)
    elif anim == "notice":
        # The head comes up and it roars.
        k = math.sin(math.pi * min(1.0, t * 1.3))
        pitch, jaw, eyes, alarm = -14.0 * k, k, "wide", True
        rear = 0.12 * k
    elif anim == "windup":
        # Up on the hind legs, the forepaws high, the claws out, a roar.
        rear = 0.92 + 0.06 * math.sin(cyc)
        jaw = 0.7 + 0.3 * math.sin(cyc * 2.0)
        pitch, eyes, dx = -4.0, "narrow", -4.0
    elif anim == "attack_side":
        # It comes down on you with both paws: the ground shakes.
        u = min(1.0, t * 1.3)
        down = min(1.0, u / 0.45)
        rear = 0.95 * (1.0 - down * down)
        dx = -4.0 + 20.0 * down
        jaw = 0.8 * (1.0 - down) + 0.5 * max(0.0, 1.0 - abs(u - 0.5) / 0.3)
        slam = max(0.0, 1.0 - abs(u - 0.5) / 0.35) if u > 0.4 else 0.0
        pitch, eyes = 10.0 * down, "narrow"
        dy = 3.0 * slam
    elif anim == "hit":
        k = math.sin(math.pi * t)
        pitch, dx, tilt, eyes, jaw = -16.0 * k, -6.0 * k, -3.0 * k, "shut", 0.4 * k
    elif anim == "death":
        u = min(1.0, t / 0.8)
        fold = min(1.0, u * 1.4)
        dy = 22.0 * fold
        tilt = 6.0 * fold
        pitch, eyes = 18.0 * fold, "shut"
        fade = 1.0 - max(0.0, t - 0.75) / 0.25

    hip = (HIP[0] + dx, HIP[1] + dy)
    angle = tilt - 66.0 * rear

    def B(pts: Sequence[Point]) -> List[Point]:
        """Points of the body: moved, breathing, then turned about the hip."""
        out = [(x + dx, y + dy + (0.0 if y < 90 else 1.0 * breathe)) for x, y in pts]
        return K.turn(out, hip[0], hip[1], angle)

    shoulder = B([(128.0, 100.0)])[0]

    def hind(root: Point, phase: float, near: bool) -> None:
        colour = E.BEAR_FUR if near else E.BEAR_FUR_DARK
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
        colour = E.BEAR_FUR if near else E.BEAR_FUR_DARK
        sw = math.sin(phase) * gait_amp
        lift = max(0.0, math.cos(phase)) * 7.0 * gait_amp
        ground = (root[0] + 10.0 * sw + 2.0, GROUND - 8.0 - lift)
        raised = (root[0] + 36.0 + offset, root[1] - 18.0 + 2.0 * offset)
        target = H.lerp(ground, raised, min(1.0, rear * 1.2))
        if fold:
            target = (root[0] + 24.0 * fold, GROUND - 8.0)
        knee, foot = S.joint(root, target, UPPER, LOWER, -1.0 + 2.0 * min(1.0, rear * 1.5))
        f.limb([root, knee], 20.0, colour)
        f.limb([knee, foot], 15.0, colour)
        _paw(f, foot[0] + 2.0, foot[1] + 2.0, near, min(1.0, rear * 1.4))

    # The far legs.
    hind(B([(60.0, 108.0)])[0], gait + math.pi, False)
    fore(B([(124.0, 104.0)])[0], gait, False, -6.0)

    # The body: a heavy barrel with a hump over the shoulders.
    body = B([(32.0, 100.0), (38.0, 76.0), (60.0, 62.0), (96.0, 60.0), (116.0, 52.0), (134.0, 56.0), (150.0, 72.0), (152.0, 100.0),
              (140.0, 122.0), (100.0, 128.0), (60.0, 126.0), (38.0, 118.0)])
    f.poly(body, E.BEAR_FUR)
    f.poly(B([(40.0, 112.0), (60.0, 120.0), (100.0, 122.0), (140.0, 116.0), (138.0, 124.0), (100.0, 129.0), (60.0, 127.0), (40.0, 119.0)]),
           E.BEAR_FUR_DARK, body=False)
    # The grizzled hump, and the rough fur along the back.
    f.poly(B([(100.0, 62.0), (116.0, 54.0), (132.0, 58.0), (144.0, 72.0), (126.0, 70.0), (108.0, 70.0)]), E.BEAR_FUR_LIGHT, body=False)
    E.fur(f, B([(44.0, 74.0), (64.0, 64.0), (96.0, 62.0), (116.0, 55.0), (134.0, 58.0)]), 7.0, E.BEAR_FUR_LIGHT, "cb:back", 1.0)
    for k in range(4):
        x = 66.0 + k * 18.0
        f.ink(B([(x, 84.0), (x - 4.0, 104.0)]), 1.1, E.BEAR_FUR_DARK)
    # The stub of a tail.
    f.ellipse(*B([(33.0, 84.0)])[0], 5.0, 4.0, E.BEAR_FUR_DARK)

    # The near legs.
    hind(B([(54.0, 112.0)])[0], gait, True)
    fore(B([(132.0, 108.0)])[0], gait + math.pi, True, 6.0)

    # The head, on the neck: turned with the body, then by `pitch`. When it
    # rears it keeps its eyes on you.
    neck = B([(148.0, 78.0)])[0]
    pr = angle + pitch + 50.0 * rear

    def Hd(pts: Sequence[Point]) -> List[Point]:
        return K.turn([(neck[0] + x, neck[1] + y) for x, y in pts], neck[0], neck[1], pr)

    # The neck and the ruff.
    f.poly(Hd([(-14.0, -14.0), (4.0, -18.0), (8.0, 16.0), (-10.0, 22.0), (-18.0, 8.0)]), E.BEAR_FUR)
    # The lower jaw, open by `jaw`.
    jaw_pts = K.turn(Hd([(6.0, 8.0), (34.0, 7.0), (40.0, 9.0), (34.0, 13.0), (14.0, 15.0)]), *Hd([(10.0, 10.0)])[0], 34.0 * jaw)
    if jaw > 0.1:
        f.poly(Hd([(10.0, 6.0), (38.0, 6.0), (30.0, 16.0), (12.0, 18.0)]), MOUTH)
        jtop = jaw_pts[1]
        f.poly([(jtop[0] - 1.0, jtop[1]), (jtop[0] - 3.0, jtop[1] - 4.0), (jtop[0] - 5.0, jtop[1])], TEETH, body=False)
    f.poly(jaw_pts, E.BEAR_FUR)
    f.ink(jaw_pts[1:4], 1.0, E.BEAR_FUR_DARK)
    # The skull: a steep forehead and a long muzzle.
    head = Hd([(-6.0, -12.0), (4.0, -22.0), (16.0, -22.0), (24.0, -12.0), (36.0, -6.0), (46.0, -2.0), (48.0, 4.0), (44.0, 8.0), (30.0, 10.0),
               (12.0, 12.0), (-4.0, 8.0)])
    f.poly(head, E.BEAR_FUR)
    f.poly(Hd([(24.0, -10.0), (36.0, -5.0), (46.0, -1.0), (48.0, 4.0), (44.0, 8.0), (30.0, 9.0), (26.0, 2.0)]), E.BEAR_FUR_LIGHT, body=False)
    if jaw > 0.1:
        # The upper fangs.
        for x in (36.0, 28.0):
            p = Hd([(x, 9.0), (x + 1.6, 14.0), (x + 3.0, 9.0)])
            f.poly(p, TEETH, body=False)
    # The nose, the ear and the eye.
    nx, ny = Hd([(46.0, 1.0)])[0]
    f.ellipse(nx, ny, 3.4, 2.8, NOSE, body=False)
    for k in range(2):
        ex0, ey0 = Hd([(4.0 + k * 8.0, -22.0)])[0]
        f.ellipse(ex0, ey0, 5.0, 5.0, E.BEAR_FUR if k else E.BEAR_FUR_DARK)
        f.ellipse(ex0 + 0.6, ey0 + 0.6, 2.4, 2.4, E.BEAR_FUR_DARK, body=False)
    ex, ey = Hd([(22.0, -8.0)])[0]
    f.ink(Hd([(17.0, -13.0), (25.0, -12.0)]), 1.2, E.BEAR_FUR_DARK)
    if eyes == "shut":
        f.ink([(ex - 2.2, ey), (ex + 2.2, ey + 0.5)], 1.1, EYE)
    else:
        r = {"open": 1.6, "wide": 2.2, "narrow": 1.1}[eyes]
        f.ellipse(ex, ey, 2.0, r, (220, 170, 70, 255), body=False)
        f.dot(ex + 0.5, ey, 0.9, EYE)
        if eyes == "narrow":
            f.ink([(ex - 2.8, ey - 2.6), (ex + 2.4, ey - 0.6)], 1.2, EYE)
    if sniff > 0.3:
        E.breath(f, nx + 3.0, ny - 1.0, 0.5 * sniff, limit=210.0)
    if jaw > 0.5 and anim in ("notice", "windup"):
        # The roar: lines out of the open mouth.
        mx, my = Hd([(42.0, 12.0)])[0]
        for k in range(3):
            a = math.radians(-30.0 + k * 30.0)
            f.ink([(mx + math.cos(a) * 8.0, my + math.sin(a) * 8.0), (mx + math.cos(a) * (8.0 + 8.0 * jaw), my + math.sin(a) * (8.0 + 8.0 * jaw))],
                  1.6, K.alpha(E.SNOW, jaw))
    if slam > 0.05:
        H.dust(f, shoulder[0] + 24.0, GROUND - 2.0, 18.0, slam, f"cb:slam:{i}", colour=E.SNOW)
        for k in range(3):
            x = shoulder[0] + 6.0 + k * 14.0
            f.ink([(x, GROUND - 14.0 - 6.0 * slam), (x + 2.0, GROUND - 22.0 - 10.0 * slam)], 1.6, K.alpha(K.WHITE, 0.8 * slam))
    if anim == "death" and t > 0.3:
        H.dust(f, 96.0, GROUND - 2.0, 30.0, min(1.0, (t - 0.3) * 2.0), f"cb:death:{i}", colour=E.SNOW)
    if alarm:
        H.alarm_mark(f, neck[0] + 6.0, neck[1] - 40.0)
    return f.finish(outline=E.OUTLINE, width=1.6, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
