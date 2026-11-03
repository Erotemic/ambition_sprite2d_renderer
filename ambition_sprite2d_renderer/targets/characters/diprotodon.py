"""The Diprotodon: the giant wombat of Ice Age Australia.

The largest marsupial that ever lived, as big as a hippo: a huge barrel of
a body in coarse brown fur, short thick legs with turned-in feet, a big
blunt head with a broad pale nose pad, small round ears and small kind
eyes. It looks like a wombat that kept growing. A stub of a tail.

It is heavy and slow. It grazes and snuffles. When it sees you it lifts its
head and huffs. Its windup rocks it back on its haunches with its head low;
its strike is a shove: it rushes forward and butts you with its great
head. A hit makes it grunt and blink; at its death it sinks down onto its
belly.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Sequence, Tuple

from . import _art_cast_kit as K
from . import _history_americas_kit as A
from . import _stage_kit as S

TARGET_NAME = "diprotodon"
FRAME_SIZE = (224, 160)
ROWS = K.ENEMY_ROWS
GROUND = 155.0

ACTOR_METADATA = A.enemy_metadata(
    TARGET_NAME, "Diprotodon", "sahul", "Quadruped", "Large", "Heavy", "Walk", ["marsupial", "wombat", "shove"],
    "The giant wombat of the History dimension's Sahul, as big as a hippo, in coarse brown fur. It rocks back with "
    "its head low, then rushes forward and butts you with its great head.",
)

FUR = (132, 100, 72, 255)
FUR_LIGHT = (170, 134, 98, 255)
FUR_SHADE = (96, 70, 50, 255)
FUR_DARK = (72, 52, 38, 255)
NOSE = (70, 56, 52, 255)
NOSE_LIGHT = (110, 92, 86, 255)
CLAW = (226, 214, 190, 255)
EYE = (36, 24, 20, 255)
STEAM = (240, 236, 230, 255)

Point = Tuple[float, float]


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = K.Frame(FRAME_SIZE)

    dx, dy, tilt, pitch, gait, gait_amp, eyes, huff, sink, fade, alarm, speed = 0.0, 0.0, 0.0, 8.0, 0.0, 0.0, "open", 0.0, 0.0, 1.0, False, 0.0
    if anim == "idle":
        pitch = 14.0 + 6.0 * math.sin(cyc)
        dy = 0.8 * math.sin(cyc)
        eyes = "shut" if i == 4 else "open"
    elif anim == "walk":
        gait, gait_amp = cyc, 1.0
        dy = -1.4 * abs(math.sin(cyc * 2.0))
        tilt = 1.2 * math.sin(cyc * 2.0)
        pitch = 10.0 + 3.0 * math.sin(cyc * 2.0)
    elif anim == "notice":
        k = math.sin(math.pi * min(1.0, t * 1.3))
        pitch, huff, eyes, alarm = 8.0 - 18.0 * k, k, "wide", True
    elif anim == "windup":
        # It rocks back on its haunches, head low.
        dx, tilt, pitch = -8.0, -5.0 + 1.5 * math.sin(cyc * 2.0), 28.0
        huff = 0.5 + 0.5 * math.sin(cyc * 2.0)
        eyes = "narrow"
    elif anim == "attack_side":
        # The shove: a rush forward, the head down and then up into you.
        u = t
        dx = -8.0 + 20.0 * math.sin(math.pi * 0.5 * min(1.0, u * 1.5)) - 10.0 * max(0.0, u - 0.66) / 0.34
        butt = math.sin(math.pi * max(0.0, min(1.0, (u - 0.2) / 0.6)))
        pitch = 28.0 - 42.0 * butt
        tilt = 4.0 - 6.0 * butt
        gait, gait_amp = cyc * 1.2, 1.2 * (1.0 - 0.4 * butt)
        speed = math.sin(math.pi * min(1.0, u * 1.4))
        eyes = "narrow"
    elif anim == "hit":
        k = math.sin(math.pi * t)
        pitch, dx, tilt, eyes = 8.0 - 16.0 * k, -5.0 * k, -2.0 * k, "shut"
    elif anim == "death":
        u = min(1.0, t / 0.8)
        sink = u
        pitch, tilt, eyes = 8.0 + 18.0 * u, 2.0 * u, "shut"
        fade = 1.0 - max(0.0, t - 0.75) / 0.25

    centre = (96.0 + dx, 94.0 + dy + 18.0 * sink)

    def B(pts: Sequence[Point]) -> List[Point]:
        return A.turned(pts, centre, tilt)

    def leg(root_local: Point, ph: float, front: bool, near: bool) -> None:
        colour = FUR if near else FUR_SHADE
        root = B([root_local])[0]
        swing = math.sin(ph) * gait_amp
        lift = max(0.0, math.cos(ph)) * 5.0 * gait_amp
        fx = root[0] + 9.0 * swing
        fy = GROUND - 9.0 - lift
        if sink:
            fx = root[0] + (10.0 if front else -8.0) * sink
            fy = GROUND - 9.0
        knee, foot = S.joint(root, (fx, fy), 18.0, 16.0, -1.0 if front else 1.0)
        knee = (knee[0], min(knee[1], GROUND - 14.0))
        f.limb([root, knee], 22.0, colour)
        f.limb([knee, foot], 16.0, colour)
        # The broad foot, with pale claws.
        f.ellipse(foot[0] + 3.0, foot[1] + 4.0, 11.0, 4.6, colour)
        if near:
            for k in range(3):
                cx = foot[0] + 7.0 + k * 3.0
                f.poly([(cx - 1.4, foot[1] + 3.0), (cx + 1.4, foot[1] + 3.0), (cx + 2.4, foot[1] + 6.4)], CLAW, body=False)

    # Far legs.
    leg((-40.0, 22.0), gait + math.pi, False, False)
    leg((38.0, 22.0), gait, True, False)

    # The stub of a tail.
    f.ellipse(*B([(-66.0, -4.0)])[0], 5.0, 4.0, FUR_SHADE)

    # The body: a huge barrel, highest over the shoulders.
    body = B([(-66.0, 0.0), (-60.0, -24.0), (-36.0, -38.0), (0.0, -42.0), (34.0, -44.0), (56.0, -34.0), (66.0, -10.0), (62.0, 18.0),
              (44.0, 32.0), (0.0, 36.0), (-40.0, 32.0), (-60.0, 20.0)])
    f.poly(body, FUR)
    f.poly(B([(-56.0, 22.0), (-40.0, 30.0), (0.0, 34.0), (44.0, 30.0), (58.0, 18.0), (44.0, 36.0), (0.0, 37.0), (-40.0, 34.0)]), FUR_SHADE, body=False)
    f.poly(B([(-40.0, -34.0), (0.0, -40.0), (34.0, -42.0), (52.0, -33.0), (30.0, -34.0), (0.0, -32.0), (-34.0, -28.0)]), FUR_LIGHT, body=False)
    # Coarse fur: short strokes over the flank.
    for k in range(12):
        x = -54.0 + (k % 6) * 20.0 + (k // 6) * 9.0
        y = -14.0 + (k // 6) * 22.0 + 3.0 * math.sin(k * 1.7)
        f.ink(B([(x, y), (x - 4.0, y + 6.0)]), 1.0, FUR_SHADE)
    f.ink(B([(-48.0, -6.0), (-52.0, 12.0), (-44.0, 26.0)]), 1.4, FUR_SHADE)

    # Near legs.
    leg((-38.0, 24.0), gait, False, True)
    leg((40.0, 24.0), gait + math.pi, True, True)

    # The head: big and blunt, turned by its pitch about the neck.
    neck = B([(58.0, -12.0)])[0]
    pr = pitch + tilt

    def Hd(*pts: Point) -> List[Point]:
        return K.turn([(neck[0] + x, neck[1] + y) for x, y in pts], neck[0], neck[1], pr)

    f.poly(Hd((-10.0, -22.0), (14.0, -26.0), (34.0, -20.0), (46.0, -8.0), (50.0, 8.0), (44.0, 22.0), (24.0, 28.0), (4.0, 26.0), (-10.0, 18.0)), FUR)
    f.poly(Hd((4.0, 14.0), (24.0, 20.0), (40.0, 18.0), (44.0, 22.0), (24.0, 27.0), (4.0, 25.0)), FUR_SHADE, body=False)
    # The crease of the neck and the paler cheek: the head reads apart from the body.
    f.ink(Hd((-2.0, -22.0), (-8.0, -4.0), (-4.0, 16.0)), 1.8, FUR_DARK)
    f.poly(Hd((10.0, -4.0), (30.0, -8.0), (40.0, 2.0), (36.0, 14.0), (16.0, 14.0), (8.0, 6.0)), FUR_LIGHT, body=False)
    # The small round ear.
    f.ellipse(*Hd((6.0, -24.0))[0], 6.0, 5.0, FUR_SHADE)
    f.ellipse(*Hd((6.5, -23.0))[0], 3.0, 2.4, FUR_DARK, body=False)
    # The broad nose pad and the mouth.
    f.poly(Hd((40.0, -10.0), (48.0, -6.0), (52.0, 4.0), (50.0, 12.0), (42.0, 12.0), (38.0, 0.0)), NOSE)
    f.ellipse(*Hd((47.0, 0.0))[0], 2.4, 3.0, NOSE_LIGHT, body=False)
    f.ellipse(*Hd((49.0, 6.0))[0], 1.4, 1.8, A.SEPIA_INK, body=False)
    f.ink(Hd((44.0, 16.0), (36.0, 19.0), (30.0, 18.0)), 1.2, A.SEPIA_INK)
    # The small eye, set far back.
    ex, ey = Hd((22.0, -10.0))[0]
    if eyes == "shut":
        f.ink([(ex - 2.6, ey), (ex + 2.6, ey + 0.6)], 1.2, A.SEPIA_INK)
    else:
        r = {"open": 2.2, "wide": 2.8, "narrow": 1.4}[eyes]
        f.ellipse(ex, ey, 2.4, r, EYE, body=False)
        f.dot(ex + 0.8, ey - 0.6, 0.7, K.WHITE)
        if eyes == "narrow":
            f.ink([(ex - 3.4, ey - 3.0), (ex + 3.0, ey - 1.6)], 1.3, A.SEPIA_INK)
    f.ink(Hd((14.0, -4.0), (18.0, 4.0)), 0.9, FUR_SHADE)

    if huff > 0.05:
        nx, ny = Hd((52.0, 6.0))[0]
        for k in range(2):
            r = 3.0 + 3.0 * huff + k * 1.5
            f.ellipse(min(218.0 - r, nx + 6.0 + k * 7.0 * huff), ny + 2.0 + k * 2.0, r, r * 0.75, K.alpha(STEAM, 0.75 * huff), body=False)
    if speed > 0.1:
        for k in range(2):
            A.dust(f, centre[0] - 30.0 - k * 46.0, GROUND - 5.0, 18.0, speed * (1.0 - 0.3 * k), f"diprotodon:dust:{i}:{k}")
    if anim == "death" and t > 0.3:
        A.dust(f, centre[0], GROUND - 5.0, 40.0, min(1.0, (t - 0.3) * 2.0), f"diprotodon:death:{i}")
    if alarm:
        top = Hd((10.0, -26.0))[0]
        A.alarm_mark(f, min(212.0, top[0] + 18.0), max(18.0, top[1] - 12.0))
    return A.finish(f, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
