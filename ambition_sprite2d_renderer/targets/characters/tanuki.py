"""The Tanuki of the History dimension: the raccoon dog of the Heian gardens.

The tanuki (Nyctereutes viverrinus) is the raccoon dog of Japan. It is a
wild dog, not a raccoon. It is round and low, with thick grey-brown fur, a
black mask round the eyes, dark legs, a dark band over the shoulders and a
bushy tail with a dark tip. It lives at the edges of woods and towns, and
it came into the gardens of Heian-kyo.

At rest it stands on all fours and breathes slowly in its thick coat. It
waddles: its round body rocks from side to side on its short legs. When it
sees you it lifts its head and puts its ears up. Its windup is a puff: its
fur stands out, its tail grows bushy and it rocks back. Its strike is a
bowl: it tucks its head down and rushes at you like a round ball of fur,
bumps into you and bounces back. A hit makes it shut its eyes and flinch;
at its death it falls over on its back with its legs in the air (the
tanuki is famous for this) and fades.

The frame is 160 by 96 px: the body box is 48 by 32 world units, and the
tanuki faces right.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import List, Tuple

from . import _art_cast_kit as K
from . import _history_africa_kit as H

TARGET_NAME = "tanuki"
FRAME_SIZE = (160, 96)
ROWS = K.ENEMY_ROWS
#: Nothing is drawn nearer the edge of the frame than this.
MARGIN = 6.0
GROUND = 88.0
#: The tanuki is drawn in design units and made larger about this point on
#: the ground, so that it fills its body box.
SIZE = 1.0
PIVOT = (80.0, GROUND)

ACTOR_METADATA = K.enemy_metadata(
    TARGET_NAME, "Tanuki", "Quadruped", "Standard", "Light", "Walk", ["raccoon_dog", "tanuki", "puff", "bowl"],
    "The tanuki (the Japanese raccoon dog) of the History dimension's Heian room: round and low, with thick grey-brown "
    "fur, a black mask round the eyes, dark legs and a bushy tail. It waddles, puffs up its fur and rocks back, then "
    "bowls into you like a ball of fur and bounces off.",
)
ACTOR_METADATA["tags"] = ["enemy", "history", "heian"]

Point = Tuple[float, float]

FUR = (150, 128, 102, 255)
FUR_SHADE = (108, 90, 72, 255)
FUR_LIGHT = (204, 190, 164, 255)
FUR_DARK = (74, 60, 50, 255)
MASK = (46, 34, 30, 255)
LEG = (58, 46, 40, 255)
CHEEK = (226, 216, 196, 255)
NOSE = (30, 22, 20, 255)
EYE = (250, 236, 200, 255)
PUPIL = (40, 26, 18, 255)
MOUTH = (110, 40, 40, 255)
DUST = (196, 176, 140, 255)
#: The length of a leg from the body to the ground.
LEG_LEN = 15.0


def _tufts(f: K.Frame, cx: float, cy: float, rx: float, ry: float, ang: float, a0: float, a1: float, size: float, colour,
           seed: str, spike: float = 0.0) -> None:
    """Round tufts of thick fur round part of an oval: from angle `a0` to
    `a1` (degrees, about the oval turned by `ang`). They make the edge of the
    coat soft and full. With `spike` above 0 each tuft is a point that
    stands out from the oval: the fur of a puffed-up tanuki."""
    rng = random.Random(seed)
    steps = max(2, int(abs(a1 - a0) / 20.0))
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    for k in range(steps + 1):
        a = math.radians(a0 + (a1 - a0) * k / steps + rng.uniform(-4.0, 4.0))
        ex, ey = (rx - size * 0.3) * math.cos(a), (ry - size * 0.3) * math.sin(a)
        r = size * rng.uniform(0.8, 1.1)
        px, py = cx + ex * c - ey * s, cy + ex * s + ey * c
        f.ellipse(px, py, r, r * 0.9, colour)
        if spike > 0.0:
            # A point of fur out along the normal of the oval.
            nx, ny = math.cos(a) * ry, math.sin(a) * rx
            d = math.hypot(nx, ny) or 1.0
            nx, ny = nx / d, ny / d
            nx, ny = nx * c - ny * s, nx * s + ny * c
            tx, ty = -ny, nx
            reach = r + spike * rng.uniform(1.6, 2.8)
            f.poly([(px + tx * r * 0.8, py + ty * r * 0.8), (px + nx * reach, py + ny * reach), (px - tx * r * 0.8, py - ty * r * 0.8)], colour)


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = H.ScaledFrame(FRAME_SIZE, SIZE, PIVOT)

    # The pose. `puff` makes the fur stand out; `tuck` lowers the head for
    # the bowl; `air` lifts the whole tanuki; `lie` 1 is on its back.
    dx, air, tilt, bob, breathe = 0.0, 0.0, 0.0, 0.0, 0.0
    puff, tuck, squash, lie, head_up, ears_back = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    eyes, mouth, fade, alarm, walk_ph, tail_lift = "open", 0.0, 1.0, False, None, 0.0
    if anim == "idle":
        # It stands and breathes slowly; its tail sways.
        breathe = math.sin(cyc)
        tail_lift = 0.15 * math.sin(cyc + 1.0)
        head_up = 0.15 * math.sin(cyc - 0.6)
        eyes = "shut" if i == 4 else "open"
    elif anim == "walk":
        # A waddle: the body rocks from side to side and bobs on each step.
        walk_ph = t
        tilt = 3.0 * math.sin(cyc * 2.0)
        bob = -1.6 * abs(math.sin(cyc * 2.0))
        tail_lift = 0.2 * math.sin(cyc * 2.0 + 1.0)
    elif anim == "notice":
        # It lifts its head and puts its ears up; the fur stirs.
        k = math.sin(math.pi * min(1.0, t * 1.3))
        head_up, puff, eyes, alarm, tail_lift = 1.0 * k, 0.3 * k, "wide", True, 0.4 * k
    elif anim == "windup":
        # It puffs up and rocks back on its hind legs, ready to rush.
        puff = 0.85 + 0.15 * math.sin(cyc)
        dx = -4.0 + 2.0 * math.sin(cyc)
        tilt = -5.0 - 2.0 * math.sin(cyc)
        tail_lift = 0.9
        eyes, mouth = "narrow", 0.3
    elif anim == "attack_side":
        # The bowl, as key frames: dx, air, tuck, squash, puff, tilt.
        table = [
            (-6.0, 0.0, 0.4, 0.0, 1.0, -6.0),
            (6.0, 3.0, 1.0, 0.0, 0.9, 8.0),
            (18.0, 2.0, 1.0, 0.0, 0.8, 10.0),
            (24.0, 0.0, 1.0, 1.0, 0.7, 4.0),
            (16.0, 5.0, 0.6, 0.0, 0.5, -6.0),
            (8.0, 0.0, 0.2, 0.0, 0.3, 0.0),
        ]
        dx, air, tuck, squash, puff, tilt = table[i]
        eyes = "shut" if i == 3 else "narrow"
        tail_lift = 0.6
    elif anim == "hit":
        k = math.sin(math.pi * (i + 1) / (n + 1))
        dx, eyes, ears_back, tilt, squash, mouth = -7.0 * k, "shut", k, -6.0 * k, 0.5 * k, 0.4 * k
    elif anim == "death":
        # It falls over on its back with its legs in the air, then fades.
        lie = min(1.0, t / 0.45)
        lie = lie * lie * (3.0 - 2.0 * lie)
        eyes = "shut"
        fade = 1.0 - max(0.0, t - 0.7) / 0.3

    # The body: a round barrel of fur.
    rx = 23.0 + 3.0 * puff + 3.0 * squash + 3.0 * lie
    ry = 19.0 + 0.5 * breathe + 3.0 * puff - 3.0 * squash - 4.0 * lie
    leg_len = LEG_LEN * (1.0 - 0.25 * tuck) * (1.0 - 0.3 * squash)
    cx = 66.0 + dx
    cy = GROUND - leg_len - ry * 0.75 - air + bob
    cy = cy + (GROUND - ry - 2.0 - cy) * lie
    ang = tilt + 4.0 * tuck - 8.0 * lie
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))

    def B(x: float, y: float) -> Point:
        """A point on the body, in the frame of the turned body."""
        return cx + x * ca - y * sa, cy + x * sa + y * ca

    def leg(fore: bool, near: bool) -> None:
        colour = LEG if near else K.shade(LEG, 0.75)
        bx = (rx * 0.55 if fore else -rx * 0.5) + (0.0 if near else -4.0)
        # The root of the leg moves from the belly to the top as it rolls.
        root = B(bx, ry * 0.55 * (1.0 - 2.0 * lie))
        if lie > 0.0:
            # The leg swings forward and up; the paw is in the air.
            a = math.radians(90.0 - 200.0 * lie + (8.0 if fore else -8.0) * lie + (6.0 if near else -6.0) * lie)
            length = leg_len * (1.0 - 0.15 * lie)
            foot = (root[0] + length * math.cos(a), root[1] + length * math.sin(a))
            mid = ((root[0] + foot[0]) / 2.0 + 2.0 * lie, (root[1] + foot[1]) / 2.0)
        else:
            fx, lift = root[0], 0.0
            if walk_ph is not None:
                # Diagonal pairs move together, as a dog walks.
                pair = (0.0 if fore == near else 0.5)
                sx, sy = H.gait(walk_ph * 2.0 + pair, 9.0, 4.0)
                fx, lift = root[0] + sx, -sy
            if tuck and air:
                # In the rush the legs tuck up under the ball of fur.
                fx += (6.0 if fore else -6.0) * tuck
                lift = max(lift, air + 5.0 * tuck)
            if squash:
                fx += (5.0 if fore else -5.0) * squash
            foot = (fx, min(GROUND - 2.0, GROUND - 2.0 - lift))
            if puff and not air:
                # Puffed up, it braces its legs out.
                foot = (foot[0] + (2.0 if fore else -3.0) * puff, foot[1])
            mid = ((root[0] + foot[0]) / 2.0 + (1.5 if fore else -1.5), (root[1] + foot[1]) / 2.0)
        f.limb([root, mid, foot], 7.0, colour)
        f.ellipse(foot[0] + (2.0 if lie < 0.5 else 0.0), foot[1] + (0.6 if lie < 0.5 else 0.0), 4.0, 2.4 if lie < 0.5 else 3.2, colour)

    if lie <= 0.5:
        leg(True, False)
        leg(False, False)

    # The tail: a thick brush with a dark tip that hangs out and down
    # behind. It rises when the tanuki puffs up.
    tr = B(-rx * 0.8, -ry * 0.25)
    t_ang = math.radians(172.0 - 40.0 * tail_lift + 30.0 * lie + ang)
    t_len = 26.0 + 3.0 * puff
    t_mid = (tr[0] + t_len * 0.5 * math.cos(t_ang), tr[1] + t_len * 0.5 * math.sin(t_ang) + 1.0)
    t_tip = (tr[0] + t_len * math.cos(t_ang - 0.2), tr[1] + t_len * math.sin(t_ang - 0.2) + 5.0)
    t_tip = (max(MARGIN + 8.0, t_tip[0]), min(GROUND - 6.0, t_tip[1]))
    t_w = 14.0 + 5.0 * puff
    f.limb([tr, t_mid], t_w * 0.8, FUR)
    f.ellipse(t_mid[0], t_mid[1], t_w * 0.6, t_w * 0.55, FUR)
    f.limb([t_mid, t_tip], t_w * 0.85, FUR)
    f.ellipse(t_tip[0], t_tip[1], t_w * 0.45, t_w * 0.42, FUR_DARK)
    _tufts(f, t_mid[0], t_mid[1], t_w * 0.6, t_w * 0.55, 0.0, 190.0, 340.0, 2.4, FUR, f"tan:tail:{anim}:{i}", spike=puff)
    f.ellipse(t_mid[0] + 1.0, t_mid[1] + t_w * 0.22, t_w * 0.45, t_w * 0.2, FUR_SHADE, body=False)

    # The coat: an oval with soft tufts at its edge. Puffed up, the tufts
    # stand out as points.
    f.poly(K.turn(K.ellipse_points(cx, cy, rx, ry, 32), cx, cy, ang), FUR)
    _tufts(f, cx, cy, rx, ry, ang, 180.0, 360.0, 3.6, FUR, f"tan:back:{anim}:{i}", spike=puff)
    _tufts(f, cx, cy, rx, ry, ang, 20.0, 160.0, 3.0, FUR, f"tan:belly:{anim}:{i}", spike=puff * 0.5)
    # The shade of the belly; the dark chest that runs down into the dark
    # forelegs; the dark stripe down the middle of the back.
    def patch(points, colour) -> None:
        f.poly(K.turn([(cx + x * rx, cy + y * ry) for x, y in points], cx, cy, ang), colour, body=False)

    patch(((-0.85, 0.3), (-0.3, 0.5), (0.3, 0.5), (0.7, 0.45), (0.5, 0.82), (0.0, 0.97), (-0.6, 0.8)), FUR_SHADE)
    patch(((0.55, -0.35), (0.8, -0.5), (0.97, -0.1), (0.9, 0.4), (0.6, 0.82), (0.25, 0.9), (0.3, 0.45), (0.45, 0.0)), FUR_DARK)
    patch(((-0.7, -0.72), (-0.2, -0.97), (0.45, -0.92), (0.75, -0.6), (0.4, -0.72), (-0.2, -0.82)), FUR_DARK)
    patch(((-0.75, -0.45), (-0.3, -0.72), (0.0, -0.7), (-0.4, -0.52)), FUR_LIGHT)
    # Strokes of fur on the flank.
    for k in range(4):
        u = -0.6 + k * 0.25
        p0, p1 = B(rx * u, -ry * 0.25 + 3.0 * (k % 2)), B(rx * u - 3.0, ry * 0.1 + 3.0 * (k % 2))
        f.ink([p0, p1], 0.8, FUR_SHADE)

    if lie <= 0.5:
        leg(True, True)
        leg(False, True)
    else:
        for fore in (True, False):
            leg(fore, False)
            leg(fore, True)

    # The head: in front of the shoulders. It goes down for the bowl, up when
    # it notices you, and lies on the ground at its death.
    hx = cx + rx * 0.95 + 4.0 - 2.0 * tuck
    hy = cy - ry * 0.35 - 5.0 * head_up + 9.0 * tuck
    hy = hy + (GROUND - 13.0 - hy) * lie
    hx = hx + 3.0 * lie
    hturn = 8.0 * tuck - 10.0 * head_up + 25.0 * lie - 6.0 * ears_back

    def Hd(*p: Point) -> List[Point]:
        return K.turn([(hx + x, hy + y) for x, y in p], hx, hy, hturn)

    # The ears: small and round, with dark rims. They go back when it is hit.
    for ex_, near in ((-6.0, False), (2.0, True)):
        back = 5.0 * ears_back
        ear = Hd((ex_ - 4.0, -8.0), (ex_ - 2.0 - back, -15.0 + 2.0 * ears_back), (ex_ + 3.0 - back, -14.0 + 3.0 * ears_back), (ex_ + 4.0, -7.0))
        f.poly(ear, FUR_DARK if near else K.shade(FUR_DARK, 0.8))
        if near:
            f.poly(Hd((ex_ - 2.0, -9.0), (ex_ - 0.6 - back, -13.0 + 2.0 * ears_back), (ex_ + 1.8 - back, -12.4 + 3.0 * ears_back), (ex_ + 2.0, -8.0)), FUR_SHADE, body=False)
    # The round head with a ruff of pale fur at the cheeks.
    f.ellipse(hx, hy, 12.5, 11.5, FUR)
    _tufts(f, hx, hy + 2.0, 12.0, 10.0, hturn, 40.0, 150.0, 3.0, CHEEK, f"tan:ruff:{anim}:{i}", spike=puff * 0.4)
    f.ellipse(*Hd((-1.0, -6.0))[0], 7.0, 3.2, FUR_LIGHT, body=False)
    # The muzzle: pale, short and pointed, with a black nose.
    f.poly(Hd((4.0, -2.0), (13.0, 0.0), (17.0, 2.6), (16.0, 5.0), (9.0, 7.0), (3.0, 6.0)), CHEEK)
    f.ellipse(*Hd((16.4, 2.6))[0], 2.4, 2.0, NOSE)
    # The black mask: from round the eye down over the cheek.
    f.poly(Hd((-4.0, -1.0), (1.0, -4.0), (8.0, -3.6), (10.0, -0.6), (6.0, 3.0), (2.0, 7.0), (-2.0, 6.0), (-4.0, 3.0)), MASK, body=False)
    # The eye in the mask.
    ex, ey = Hd((5.0, -1.0))[0]
    if eyes == "shut":
        f.ink(Hd((2.6, -0.6), (5.0, 0.4), (7.4, -0.6)), 1.1, EYE)
    else:
        r = {"open": 1.7, "wide": 2.2, "narrow": 1.1}[eyes]
        f.ellipse(ex, ey, 2.0, r, EYE, body=False)
        f.ellipse(ex + 0.5, ey, 1.2, min(r, 1.4), PUPIL, body=False)
        f.dot(ex + 0.9, ey - 0.6, 0.35, EYE)
        if eyes == "narrow":
            f.ink(Hd((2.4, -3.6), (7.6, -2.4)), 1.0, MASK)
    # The mouth: a short line under the muzzle, or open a little.
    if mouth > 0.05:
        f.poly(Hd((10.0, 5.0), (15.0, 4.4), (12.0, 5.6 + 2.6 * mouth)), MOUTH, body=False)
    else:
        f.ink(Hd((10.0, 5.6), (14.0, 4.8)), 0.8, FUR_DARK)
    # Whiskers.
    for k in (-1.0, 1.0):
        f.ink(Hd((12.0, 3.4), (19.0, 2.4 + 1.6 * k)), 0.5, FUR_DARK)

    if walk_ph is not None and walk_ph % 0.5 < 0.12:
        H.dust(f, cx - 4.0, GROUND - 1.0, 0.3, f"tan:walk:{i}", spread=0.6, colour=DUST)
    if anim == "attack_side":
        if i in (1, 2):
            # Speed lines behind the ball of fur.
            for k in (-1.0, 0.0, 1.0):
                y = cy + k * 7.0
                x1 = cx - rx - 4.0
                f.ink([(max(MARGIN, x1 - 14.0 - 4.0 * abs(k)), y), (x1, y)], 1.2, K.alpha(K.WHITE, 0.9))
        if i == 3:
            # The bump: short lines out from the front of the ball.
            bx, by = hx + 18.0, hy + 2.0
            for k in (-1.0, 0.0, 1.0):
                f.ink([(bx, by + k * 5.0), (min(FRAME_SIZE[0] - MARGIN - 1.0, bx + 6.0), by + k * 8.0)], 1.3, K.alpha(K.WHITE, 0.95))
        if i in (0, 3, 5):
            H.dust(f, cx, GROUND - 1.0, 0.6, f"tan:bowl:{i}", spread=0.9, colour=DUST)
    if anim == "death" and 0.2 < t < 0.8:
        H.dust(f, cx, GROUND - 1.0, min(1.0, (t - 0.2) * 2.5), f"tan:death:{i}", spread=1.4, colour=DUST)
    if alarm:
        H.alarm_mark(f, min(FRAME_SIZE[0] - MARGIN - 4.0, hx + 2.0), max(MARGIN + 11.0, hy - 28.0))
    return f.finish(outline=H.SEPIA_INK, width=1.5, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
