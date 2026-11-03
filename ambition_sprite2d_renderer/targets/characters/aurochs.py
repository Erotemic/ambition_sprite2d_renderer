"""The Aurochs: the wild ox of the Fertile Crescent, before anyone tamed it.

A huge black bull with a high hump of muscle over its shoulders and a pale
stripe along its spine (the eel stripe of the aurochs). Its muzzle is pale,
and its long horns are the colour of old ivory, dark at the tips: they
sweep out and forward and up, the horns that the painters of the caves
drew. A tuft at the end of its tail.

It is heavy and slow until it is not. It grazes and swishes its tail. When
it sees you it lifts its head and snorts. Its windup lowers its horns at
you and paws the ground with a forefoot, and the dust flies; its strike is
the charge: it rushes forward head down and tosses its horns up. A hit
jerks its head back; at its death its forelegs fold and it goes down.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import List, Sequence, Tuple

from . import _art_cast_kit as K
from . import _history_ancient_kit as H
from . import _stage_kit as S

TARGET_NAME = "aurochs"
FRAME_SIZE = (192, 160)
ROWS = K.ENEMY_ROWS
GROUND = 154.0

ACTOR_METADATA = H.enemy_metadata(
    TARGET_NAME, "Aurochs", "crescent", "Quadruped", "Large", "Heavy", "Walk", ["ox", "horns", "charge"],
    "The wild ox of the History dimension's Fertile Crescent, before anyone tamed it: a huge black bull with long "
    "ivory horns. It lowers its horns and paws the ground, then charges and tosses its horns up.",
)

COAT = (58, 40, 34, 255)
COAT_LIGHT = (100, 70, 54, 255)
COAT_SHADE = (36, 26, 24, 255)
STRIPE = (204, 170, 118, 255)
MUZZLE = (214, 194, 162, 255)
HORN = (238, 226, 196, 255)
HORN_SHADE = (190, 172, 136, 255)
HORN_TIP = (54, 44, 40, 255)
HOOF = (44, 36, 34, 255)
NOSTRIL = (40, 22, 22, 255)
EYE = (226, 140, 40, 255)
STEAM = (240, 236, 230, 255)

Point = Tuple[float, float]

UPPER, LOWER = 26.0, 30.0

#: The bull is drawn at this size about the middle of its ground row: the
#: frame must hold its charge and its lifted tail.
SIZE = 0.86
PIVOT = (100.0, GROUND)


class _Scaled(K.Frame):
    """A frame that draws every shape at `SIZE` about `PIVOT`."""

    def _w(self, points):
        px, py = PIVOT
        return [((px + (x - px) * SIZE) * K.SUPER, (py + (y - py) * SIZE) * K.SUPER) for x, y in points]

    def _p(self, x, y):
        return PIVOT[0] + (x - PIVOT[0]) * SIZE, PIVOT[1] + (y - PIVOT[1]) * SIZE

    def ellipse(self, cx, cy, rx, ry, fill, body=True):
        x, y = self._p(cx, cy)
        super().ellipse(x, y, rx * SIZE, ry * SIZE, fill, body)

    def dot(self, cx, cy, r, fill=K.INK):
        x, y = self._p(cx, cy)
        super().dot(x, y, r * SIZE, fill)

    def glow(self, cx, cy, r, fill):
        x, y = self._p(cx, cy)
        super().glow(x, y, r * SIZE, fill)

    def limb(self, points, width, fill, body=True):
        super().limb(points, width * SIZE, fill, body)

    def ink(self, points, width=1.2, fill=K.INK):
        super().ink(points, width * SIZE, fill)


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = _Scaled(FRAME_SIZE)
    rng = random.Random(f"aurochs:{anim}:{i}")

    dx, dy, tilt, pitch, breathe, swish = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    gait, gait_amp, paw, toss, snort, eyes, fade = 0.0, 0.0, 0.0, 0.0, 0.0, "open", 1.0
    fold_front, fold_back, tail_up, speed, alarm = 0.0, 0.0, 0.0, 0.0, False
    if anim == "idle":
        breathe = math.sin(cyc)
        swish = math.sin(cyc)
        pitch = 6.0 + 4.0 * math.sin(cyc)
    elif anim == "walk":
        gait, gait_amp = cyc, 1.0
        dy = -1.2 * abs(math.sin(cyc * 2.0))
        pitch = 4.0 + 3.0 * math.sin(cyc * 2.0)
        swish = 0.6 * math.sin(cyc + 1.0)
    elif anim == "notice":
        k = math.sin(math.pi * min(1.0, t * 1.3))
        pitch, snort, eyes, alarm = -12.0 * k, k, "wide", True
        tail_up = 0.4 * k
    elif anim == "windup":
        # Head down, horns aimed; one forefoot paws the ground.
        pitch, tilt, dx = 22.0, 3.0, -4.0
        paw = math.sin(cyc * 2.0)
        tail_up, eyes = 0.6, "narrow"
        snort = 0.5 + 0.5 * math.sin(cyc * 2.0)
    elif anim == "attack_side":
        # The charge: forward fast with the head down, then a toss up.
        u = min(1.0, t * 1.25)
        dx = -4.0 + 16.0 * math.sin(math.pi * 0.5 * u) - 8.0 * max(0.0, u - 0.7) / 0.3
        toss = max(0.0, math.sin(math.pi * (u - 0.35) / 0.65)) if u > 0.35 else 0.0
        pitch = 22.0 * (1.0 - u) + 4.0 * u - 46.0 * toss
        tilt = 3.0 - 7.0 * toss
        gait, gait_amp = cyc * 1.5, 1.4 * (1.0 - toss * 0.5)
        speed = math.sin(math.pi * min(1.0, u * 1.5))
        tail_up, eyes = 1.0, "narrow"
    elif anim == "hit":
        k = math.sin(math.pi * t)
        pitch, dx, tilt, eyes = -18.0 * k, -5.0 * k, -2.0 * k, "shut"
    elif anim == "death":
        u = min(1.0, t / 0.8)
        fold_front = min(1.0, u * 1.6)
        fold_back = max(0.0, min(1.0, (u - 0.3) / 0.6))
        tilt = 10.0 * fold_front - 8.0 * fold_back
        dy = 24.0 * (0.6 * fold_front + 0.4 * fold_back)
        pitch, eyes = 26.0 * fold_front, "shut"
        fade = 1.0 - max(0.0, t - 0.75) / 0.25

    # The bull stands a little left of the middle, to leave room for its charge.
    dx -= 6.0
    shoulder = (124.0 + dx, 90.0 + dy)
    hip = (52.0 + dx, 88.0 + dy)

    def B(pts: Sequence[Point]) -> List[Point]:
        """Points of the body: turned by the tilt about the shoulder."""
        return K.turn([(x + dx, y + dy + (0.0 if y < 90 else 1.2 * breathe)) for x, y in pts], shoulder[0], shoulder[1], tilt)

    sh_w = B([(124.0, 90.0)])[0]
    hp_w = B([(52.0, 88.0)])[0]

    def leg(root: Point, phase: float, front: bool, near: bool) -> None:
        colour = COAT if near else COAT_SHADE
        swing = math.sin(phase) * gait_amp
        lift = max(0.0, math.cos(phase)) * 6.0 * gait_amp
        fx = root[0] + 12.0 * swing + (2.0 if front else -2.0)
        fy = GROUND - 3.0 - lift
        if front and near and paw:
            # The paw: the foot goes up and back, then scrapes forward.
            fx = root[0] + 6.0 * paw
            fy = GROUND - 3.0 - 8.0 * max(0.0, math.sin(cyc * 2.0 + 0.6))
        fold = fold_front if front else fold_back
        if fold:
            fx = root[0] + (14.0 if front else -10.0) * fold
            fy = min(GROUND - 3.0, fy)
        bend = -1.0 if front else 1.0
        knee, foot = S.joint(root, (fx, fy), UPPER, LOWER, bend)
        if fold:
            # A folded leg lies under the body.
            knee = (root[0] + (6.0 if front else -6.0) + 10.0 * fold, min(GROUND - 6.0, root[1] + 16.0))
            foot = (knee[0] - 12.0 * fold * (1 if front else -1), GROUND - 4.0)
        f.limb([root, knee], 13.0 if not front else 12.0, colour)
        f.limb([knee, foot], 8.0, colour)
        # The hoof: a dark wedge, cloven.
        hx, hy = foot
        f.poly([(hx - 5.0, hy - 3.0), (hx + 5.0, hy - 3.0), (hx + 6.5, hy + 3.0), (hx - 5.0, hy + 3.0)], HOOF)
        f.ink([(hx + 1.0, hy), (hx + 1.0, hy + 3.0)], 0.8, COAT_LIGHT)
        # The dew claw and a pale fetlock.
        f.ink([(hx - 4.0, hy - 6.0), (hx + 4.0, hy - 6.0)], 1.6, MUZZLE if near else COAT_LIGHT)

    # Far legs.
    leg((hp_w[0] + 6.0, hp_w[1] + 6.0), gait + math.pi, False, False)
    leg((sh_w[0] - 4.0, sh_w[1] + 8.0), gait, True, False)

    # The tail: from the rump, down, with a tuft.
    rump = B([(36.0, 70.0)])[0]
    lift = 26.0 * tail_up
    tail = [rump, (rump[0] - 6.0 - 0.4 * lift, rump[1] + 14.0 - lift), (rump[0] - 8.0 + 4.0 * swish - 0.6 * lift, rump[1] + 30.0 - 1.4 * lift),
            (rump[0] - 6.0 + 7.0 * swish - 0.8 * lift, rump[1] + 44.0 - 2.0 * lift)]
    f.limb(tail, 3.4, COAT)
    tx, ty = tail[-1]
    f.poly([(tx - 3.0, ty - 4.0), (tx + 3.0, ty - 4.0), (tx + 4.0 + 2.0 * swish, ty + 7.0), (tx - 4.0 + 2.0 * swish, ty + 8.0)], COAT_SHADE)

    # The body: a deep barrel with a hump over the shoulders.
    body = B([(36.0, 72.0), (48.0, 64.0), (80.0, 64.0), (104.0, 56.0), (118.0, 48.0), (130.0, 52.0), (140.0, 66.0), (144.0, 94.0),
              (134.0, 112.0), (110.0, 116.0), (78.0, 116.0), (54.0, 112.0), (38.0, 102.0), (32.0, 86.0)])
    f.poly(body, COAT)
    f.poly(B([(54.0, 110.0), (78.0, 114.0), (110.0, 114.0), (134.0, 110.0), (130.0, 116.0), (110.0, 117.0), (78.0, 117.0), (54.0, 113.0)]), COAT_SHADE, body=False)
    f.poly(B([(100.0, 60.0), (118.0, 50.0), (128.0, 54.0), (134.0, 70.0), (124.0, 80.0), (110.0, 70.0)]), COAT_LIGHT, body=False)
    f.poly(B([(36.0, 74.0), (48.0, 68.0), (62.0, 76.0), (60.0, 96.0), (44.0, 100.0)]), K.shade(COAT, 1.15), body=False)
    # The eel stripe along the spine.
    f.ink(B([(40.0, 68.0), (60.0, 65.0), (82.0, 65.0), (104.0, 58.0), (118.0, 51.0)]), 2.2, STRIPE)
    # Ribs and the shoulder, in shade.
    for k in range(3):
        f.ink(B([(78.0 + k * 9.0, 84.0), (82.0 + k * 9.0, 102.0)]), 1.0, COAT_SHADE)
    f.ink(B([(124.0, 72.0), (118.0, 92.0), (128.0, 106.0)]), 1.2, COAT_SHADE)

    # Near legs.
    leg((hp_w[0] - 2.0, hp_w[1] + 10.0), gait, False, True)
    leg((sh_w[0] + 4.0, sh_w[1] + 10.0), gait + math.pi, True, True)

    # The head, on its neck: turned by `pitch` (down is positive) about the
    # neck.
    neck = B([(138.0, 72.0)])[0]
    pr = pitch + tilt

    def Hd(pts: Sequence[Point]) -> List[Point]:
        return K.turn([(neck[0] + x, neck[1] + y) for x, y in pts], neck[0], neck[1], pr)

    f.poly(Hd([(-8.0, -12.0), (12.0, -10.0), (22.0, 0.0), (22.0, 20.0), (4.0, 24.0), (-8.0, 22.0)]), COAT)
    head = Hd([(12.0, -8.0), (22.0, -9.0), (32.0, 0.0), (40.0, 12.0), (42.0, 20.0), (36.0, 24.0), (24.0, 22.0), (14.0, 14.0)])
    f.poly(head, COAT)
    f.poly(Hd([(30.0, 8.0), (40.0, 12.0), (42.0, 20.0), (36.0, 24.0), (28.0, 22.0), (27.0, 13.0)]), MUZZLE, body=False)
    f.ellipse(*Hd([(38.5, 15.0)])[0], 1.6, 1.2, NOSTRIL, body=False)
    f.ink(Hd([(33.0, 21.0), (40.0, 20.0)]), 0.9, NOSTRIL)
    # The forelock: a curly tuft between the horns.
    for k in range(3):
        cx0, cy0 = Hd([(16.0 + k * 2.6, -8.0 + k * 1.4)])[0]
        f.ink([(cx0 - 1.6, cy0 + 1.0), (cx0, cy0 - 1.2), (cx0 + 1.6, cy0 + 1.0)], 1.2, COAT_LIGHT)
    # The ear, out at the side.
    f.poly(Hd([(10.0, -2.0), (0.0, -6.0), (-4.0, 0.0), (6.0, 2.0)]), COAT_SHADE)
    ex, ey = Hd([(22.0, 2.0)])[0]
    if eyes == "shut":
        f.ink([(ex - 2.2, ey), (ex + 2.2, ey + 0.6)], 1.1, NOSTRIL)
    else:
        r = {"open": 1.8, "wide": 2.4, "narrow": 1.3}[eyes]
        f.ellipse(ex, ey, 2.4, r, EYE, body=False)
        f.dot(ex + 0.6, ey, 1.0, NOSTRIL)
        if eyes == "narrow":
            f.ink([(ex - 3.0, ey - 2.4), (ex + 2.6, ey - 1.0)], 1.2, NOSTRIL)

    # The horns: out, forward and up, ivory with dark tips. The far horn
    # first, then the near one.
    def horn(base: Point, near: bool) -> None:
        pts = Hd([base, (base[0] + 8.0, base[1] - 7.0), (base[0] + 20.0, base[1] - 10.0), (base[0] + 28.0, base[1] - 18.0), (base[0] + 30.0, base[1] - 28.0)])
        widths = (6.4, 5.4, 4.4, 3.2)
        for k in range(4):
            f.limb([pts[k], pts[k + 1]], widths[k] * (1.0 if near else 0.85), HORN if near else HORN_SHADE)
        f.limb([pts[3], pts[4]], 2.6 if near else 2.2, HORN_TIP)
        if near:
            for k in range(1, 3):
                x, y = pts[k]
                f.ink([(x - 1.6, y - 1.4), (x + 1.0, y + 2.0)], 0.7, HORN_SHADE)

    horn((19.0, -12.0), False)
    horn((12.0, -6.0), True)

    if snort > 0.05:
        # Steam out of the nostrils, in two puffs.
        nx, ny = Hd([(42.0, 16.0)])[0]
        for k in range(2):
            r = 2.5 + 2.5 * snort + k * 1.5
            px = min(184.0 - r, nx + 5.0 + k * 6.0 * snort)
            f.ellipse(px, ny + 3.0 + k * 2.0, r, r * 0.75, K.alpha(STEAM, 0.75 * snort), body=False)
    if paw or speed > 0.1:
        for k in range(2):
            amount = (0.6 + 0.4 * abs(paw)) if paw else speed
            H.dust(f, sh_w[0] - 6.0 - k * 50.0 - (12.0 if speed else 0.0), GROUND - 2.0, amount * (1.0 - 0.3 * k), f"aurochs:dust:{anim}:{i}:{k}", spread=1.2)
    if speed > 0.1:
        for k in range(3):
            y = 70.0 + k * 16.0 + dy
            f.ink([(max(6.0, hp_w[0] - 24.0 - 10.0 * speed), y), (max(6.0, hp_w[0] - 10.0), y)], 1.4, K.alpha(K.WHITE, 0.6 * speed))
    if anim == "death" and t > 0.3:
        H.dust(f, 96.0, GROUND - 2.0, min(1.0, (t - 0.3) * 2.0), f"aurochs:death:{i}", spread=3.0)
    del rng
    if alarm:
        H.alarm_mark(f, min(176.0, neck[0] + 30.0), 26.0)
    return f.finish(outline=H.OUTLINE, width=1.6, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
