"""The Howler Monkey: the loudest animal of the forests of the Americas.

A mantled howler monkey: dark brown-black fur with a fringe of golden-brown
hair along its flanks (the mantle), long thin arms and legs, a bare dark
face with a deep jaw and a bearded throat (the throat holds the bone that
makes the howl so loud), and a long tail that grips: its tip curls.

It keeps its distance and throws fruit. It walks on all fours with its
tail up in a curl. When it sees you it sits up, lifts its head and howls,
with its mouth a wide round O. Its windup stands it up on its hind legs
with a ripe red fruit drawn back over its shoulder; its strike throws the
fruit (the shot ``tomato``: a red fruit). A hit makes it shut its eyes and
duck; at its death it slumps forward and lies still.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Tuple

from . import _art_cast_kit as K
from . import _history_americas_kit as A
from . import _stage_kit as S

TARGET_NAME = "howler_monkey"
FRAME_SIZE = (128, 128)
ROWS = K.ENEMY_ROWS
GROUND = 123.0

ACTOR_METADATA = A.enemy_metadata(
    TARGET_NAME, "Howler Monkey", "olmec_heartland", "Quadruped", "Standard", "Light", "Walk", ["monkey", "howler", "throw"],
    "A mantled howler monkey of the History dimension's Olmec forest: dark fur with a golden fringe, a bare dark face and "
    "a curling tail. It howls, stands up on its hind legs and throws ripe red fruit at you.",
)

FUR = (74, 56, 44, 255)
FUR_SHADE = (52, 40, 32, 255)
FUR_LIGHT = (104, 80, 62, 255)
MANTLE = (182, 128, 60, 255)
MANTLE_LIGHT = (214, 166, 88, 255)
FACE = (46, 38, 38, 255)
FACE_LIGHT = (84, 70, 68, 255)
PALM = (66, 54, 52, 255)
MOUTH = (150, 52, 52, 255)
EYE = (92, 56, 32, 255)
FRUIT = (212, 62, 44, 255)
FRUIT_LIGHT = (246, 140, 110, 255)
FRUIT_LEAF = (88, 150, 70, 255)
HOWL = (232, 214, 170, 255)

Point = Tuple[float, float]
#: The length of the body from the hips to the shoulders, and of each bone of a limb.
BACK = 32.0
ARM = 16.5
LEG = 16.0
#: The tail: its pieces, each at an angle (degrees on the screen: 180 is
#: back, 270 is up, 360 is forward), as a curl over the back.
TAIL_CURL = [196.0, 210.0, 228.0, 248.0, 270.0, 292.0, 318.0, 346.0, 12.0]
TAIL_SEG = 7.0


def _fruit(f: K.Frame, x: float, y: float, r: float = 4.6) -> None:
    """A ripe red fruit with a leaf at its stalk."""
    f.ellipse(x, y, r, r * 0.92, FRUIT)
    f.ellipse(x - r * 0.35, y - r * 0.35, r * 0.32, r * 0.26, FRUIT_LIGHT, body=False)
    f.poly([(x, y - r * 0.8), (x + r * 0.9, y - r * 1.4), (x + r * 0.3, y - r * 0.7)], FRUIT_LEAF)


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = K.Frame(FRAME_SIZE)

    # The pose: `up` 0 is on all fours, 1 is up on the hind legs.
    dx, up, head_up, mouth, eyes, walk, fade, alarm = 0.0, 0.0, 0.0, 0.0, "open", None, 1.0, False
    arm, hold, fruit_at, howl, slump, tail_wave = None, False, None, 0.0, 0.0, 0.0
    if anim == "idle":
        up = 0.12 + 0.03 * math.sin(cyc)
        head_up = 3.0 * math.sin(cyc)
        tail_wave = math.sin(cyc)
        eyes = "shut" if i == 4 else "open"
        mouth = 0.25 if i == 2 else 0.0
    elif anim == "walk":
        walk = t
        tail_wave = 0.6 * math.sin(cyc)
    elif anim == "notice":
        k = math.sin(math.pi * min(1.0, t * 1.25))
        up, head_up, mouth, howl, alarm, eyes = 0.45 * k, 22.0 * k, k, k, True, "wide" if t < 0.2 else "shut"
        tail_wave = k
    elif anim == "windup":
        # Up on the hind legs, the fruit back over the shoulder.
        up = 1.0
        arm, hold = -128.0 + 6.0 * math.sin(cyc * 2.0), True
        head_up, mouth, eyes, dx = 4.0, 0.35, "narrow", -2.0 + 0.8 * math.sin(cyc * 2.0)
        tail_wave = 0.5 * math.sin(cyc * 2.0)
    elif anim == "attack_side":
        # The throw: the arm comes over, the fruit flies.
        u = t
        swing = min(1.0, u / 0.45)
        arm = -128.0 + 150.0 * (1.0 - (1.0 - swing) ** 2)
        hold = u < 0.3
        up = 1.0 - 0.45 * max(0.0, (u - 0.5) / 0.5)
        head_up, mouth, eyes, dx = 2.0 - 6.0 * swing, 0.6 * swing, "open", -2.0 + 6.0 * swing
        if 0.3 <= u <= 0.85:
            fruit_at = (u - 0.3) / 0.55
    elif anim == "hit":
        k = math.sin(math.pi * t)
        up, head_up, dx, eyes, mouth = 0.25 * k, -10.0 * k, -5.0 * k, "shut", 0.4 * k
    elif anim == "death":
        u = min(1.0, t / 0.8)
        slump, eyes, head_up = u, "shut", -18.0 * u
        fade = 1.0 - max(0.0, t - 0.75) / 0.25

    # The body: the hips, and the shoulders on the back's angle.
    hip = (50.0 + dx + 4.0 * up, 94.0 - 2.0 * up + 6.0 * slump)
    if walk is not None:
        hip = (hip[0], hip[1] - 1.4 * abs(math.sin(math.tau * walk * 2.0)))
    theta = math.radians(-6.0 - 74.0 * up + 6.0 * slump)
    sh = (hip[0] + BACK * math.cos(theta), hip[1] + BACK * math.sin(theta) + 2.0 * slump)
    ax, ay = math.cos(theta), math.sin(theta)

    def leg(ph: float, near: bool) -> None:
        colour = FUR if near else FUR_SHADE
        root = (hip[0] + (1.5 if near else -2.0), hip[1] + 2.0)
        fx, fy = root[0] + 4.0 + 6.0 * up, GROUND - 2.0
        if walk is not None:
            gx, gy = A.gait(ph, 18.0, 6.0)
            fx += gx
            fy += gy
        if slump:
            fx -= 8.0 * slump
        knee, foot = S.joint(root, (fx, fy), LEG, LEG, -1.0)
        f.limb([root, knee], 7.0, colour)
        f.limb([knee, foot], 5.4, colour)
        f.ellipse(foot[0] + 3.0, foot[1] + 0.2, 4.6, 2.2, colour)
        f.ink([(foot[0] + 5.0, foot[1] + 0.4), (foot[0] + 7.0, foot[1] + 1.0)], 0.6, PALM)

    def front_limb(ph: float, near: bool) -> None:
        """A front leg on the ground (on all fours) or an arm that hangs."""
        colour = FUR if near else FUR_SHADE
        root = (sh[0] + (1.0 if near else -2.0), sh[1] + 2.0)
        if up < 0.6:
            hx, hy = root[0] + 3.0, GROUND - 2.0
            if walk is not None:
                gx, gy = A.gait(ph, 18.0, 6.0)
                hx += gx
                hy += gy
            if slump:
                hx += 10.0 * slump
        else:
            # Up on its hind legs the free arm reaches forward for balance.
            hx, hy = root[0] + 14.0, root[1] + 18.0
        elbow, hand = S.joint(root, (hx, hy), ARM, ARM, 1.0)
        f.limb([root, elbow], 5.6, colour)
        f.limb([elbow, hand], 4.6, colour)
        f.ellipse(hand[0] + 1.6, hand[1] + 0.2, 3.2, 2.2, colour)

    ph = walk or 0.0
    # The far limbs, in shade.
    leg(ph + 0.5, False)
    if arm is None:
        front_limb(ph, False)
    else:
        front_limb(0.0, False)

    # The tail: from the hips, up in a curl; its tip grips.
    pts = [(hip[0] - 4.0 * math.cos(theta), hip[1] - 2.0)]
    x, y = pts[0]
    for k, a in enumerate(TAIL_CURL):
        a += 8.0 * tail_wave * (k / len(TAIL_CURL)) + 40.0 * slump * (1.0 - k / len(TAIL_CURL)) - 50.0 * slump
        x += math.cos(math.radians(a)) * TAIL_SEG
        y += math.sin(math.radians(a)) * TAIL_SEG
        pts.append((x, min(GROUND - 3.0, y)))
    f.limb(pts, 4.6, FUR_SHADE)
    f.limb(pts[:4], 6.0, FUR_SHADE)

    # The body: an oval along the back, with the golden mantle on its flank.
    cx, cy = (hip[0] + sh[0]) / 2.0, (hip[1] + sh[1]) / 2.0
    ang = math.degrees(theta)
    body = K.turn(K.ellipse_points(cx, cy, BACK / 2.0 + 7.0, 11.0, 30), cx, cy, ang)
    f.poly(body, FUR)
    side = (-math.sin(theta), math.cos(theta))
    if side[1] < 0.0 and up < 0.5:
        side = (-side[0], -side[1])
    # The fringe of long golden hair on the flank, below the back.
    for k in range(7):
        s = -0.75 + k * 0.25
        px, py = cx + ax * (BACK / 2.0 + 4.0) * s, cy + ay * (BACK / 2.0 + 4.0) * s
        r0 = 9.0 * math.sqrt(max(0.0, 1.0 - s * s * 0.8))
        bx, by = px + side[0] * r0, py + side[1] * r0
        tip = (bx + side[0] * 5.0 - ax * 2.0, by + side[1] * 5.0 - ay * 2.0)
        f.poly([(bx - ax * 3.4, by - ay * 3.4), tip, (bx + ax * 3.4, by + ay * 3.4)], MANTLE)
        f.ellipse(bx - side[0] * 2.0, by - side[1] * 2.0, 3.6, 3.0, MANTLE, body=False)
    for k in range(4):
        s = -0.5 + k * 0.33
        px, py = cx + ax * BACK / 2.0 * s, cy + ay * BACK / 2.0 * s
        f.ink([(px - side[0] * 4.0, py - side[1] * 4.0), (px - side[0] * 1.0 + ax * 2.0, py - side[1] * 1.0 + ay * 2.0)], 0.7, FUR_LIGHT)

    leg(ph, True)

    # The head: on the shoulders, in front on all fours and on top when up.
    hc = (sh[0] + 9.0 - 5.0 * up + 2.0 * slump, sh[1] - 7.0 - 5.0 * up + 6.0 * slump)
    tilt = -head_up

    def Hd(*p: Point) -> List[Point]:
        return K.turn([(hc[0] + x, hc[1] + y) for x, y in p], hc[0], hc[1], tilt)

    # The bearded throat, then the round head and the bare dark face.
    f.ellipse(*Hd((3.0, 8.0))[0], 7.0, 6.0, FUR)
    f.poly(Hd((-2.0, 9.0), (2.0, 15.0), (6.0, 14.0), (9.0, 9.0)), FUR)
    f.ellipse(hc[0], hc[1], 9.0, 9.0, FUR)
    f.ellipse(*Hd((-2.0, -6.0))[0], 6.0, 3.2, FUR_LIGHT, body=False)
    f.poly(Hd((0.0, -4.0), (7.0, -5.0), (12.0, -1.0), (14.0, 4.0), (12.0, 9.0), (6.0, 10.0), (2.0, 7.0), (0.0, 2.0)), FACE)
    f.poly(Hd((2.0, -3.6), (8.0, -4.4), (11.0, -2.0), (6.0, -2.4)), FACE_LIGHT, body=False)
    # The eye under a heavy brow.
    ex, ey = Hd((6.0, -1.0))[0]
    if eyes == "shut":
        f.ink([(ex - 1.8, ey), (ex + 1.8, ey + 0.4)], 1.0, (226, 210, 190, 255))
    else:
        r = {"open": 1.6, "wide": 2.1, "narrow": 1.0}[eyes]
        f.ellipse(ex, ey, 2.0, r, (236, 226, 210, 255), body=False)
        f.ellipse(ex + 0.5, ey, 1.1, min(r, 1.4), EYE, body=False)
        f.dot(ex + 0.6, ey, 0.5, A.SEPIA_INK)
        if eyes == "narrow":
            f.ink([(ex - 2.4, ey - 1.8), (ex + 2.2, ey - 0.6)], 1.0, FACE)
    f.dot(*Hd((13.0, 2.0))[0], 0.6, (20, 16, 16, 255))
    # The mouth: a line, or the wide round O of a howl.
    if mouth > 0.05:
        mx, my = Hd((11.0, 6.4))[0]
        f.ellipse(mx, my, 2.0 + 1.0 * mouth, 1.2 + 2.6 * mouth, MOUTH, body=False)
        f.ellipse(mx, my + 0.6 * mouth, 1.2 + 0.6 * mouth, 0.8 + 1.4 * mouth, (90, 30, 30, 255), body=False)
        for s in (-1.0, 1.0):
            f.poly([(mx + s * 1.4, my - 1.0 - 2.2 * mouth), (mx + s * 0.8, my + 0.4 - 2.2 * mouth), (mx + s * 2.0, my - 0.4 - 2.2 * mouth)], K.WHITE,
                   body=False)
    else:
        f.ink(Hd((8.0, 6.6), (12.6, 6.0)), 0.9, (20, 16, 16, 255))
    if howl:
        # The howl: rings of sound out of the mouth.
        mx, my = Hd((15.0, 4.0))[0]
        for k in range(3):
            r = 5.0 + k * 5.0 * (0.6 + 0.4 * howl)
            a0 = -50.0 - head_up
            arc = [(mx + r * math.cos(math.radians(a0 + j * 25.0)), my + r * math.sin(math.radians(a0 + j * 25.0))) for j in range(5)]
            arc = [(min(122.0, x2), max(6.0, y2)) for x2, y2 in arc]
            f.glow_line(arc, 1.3, K.alpha(HOWL, 0.9 - 0.2 * k))

    # The near arm: on the ground, hanging, or throwing.
    if arm is None:
        front_limb(ph + 0.5, True)
    else:
        root = (sh[0] + 1.0, sh[1] + 2.0)
        a = math.radians(arm)
        reach = 2.0 * ARM * 0.92
        elbow, hand = S.joint(root, (root[0] + math.cos(a) * reach, root[1] + math.sin(a) * reach), ARM, ARM, -1.0 if arm < -40.0 else 1.0)
        f.limb([root, elbow], 5.6, FUR)
        f.limb([elbow, hand], 4.6, FUR)
        f.ellipse(hand[0], hand[1], 3.0, 2.8, FUR)
        if hold:
            _fruit(f, hand[0] + math.cos(a) * 3.0, hand[1] + math.sin(a) * 3.0)
    if fruit_at is not None:
        # The fruit flies out level and fast, ahead of the hand.
        x0, y0 = sh[0] + 32.0, sh[1] + 4.0
        fx = min(118.0, x0 + 40.0 * fruit_at)
        fy = y0 - 6.0 * math.sin(math.pi * fruit_at)
        _fruit(f, fx, fy)
        for k in range(3):
            f.glow_line([(fx - 8.0 - k * 2.0, fy - 2.0 + k * 2.0), (fx - 14.0 - k * 3.0, fy - 2.0 + k * 2.0)], 1.0, K.alpha(K.WHITE, 0.7))
    if anim == "death" and t > 0.3:
        A.dust(f, 64.0, GROUND - 4.0, 26.0, min(1.0, (t - 0.3) * 2.0), f"howler_monkey:death:{i}")
    if alarm:
        A.alarm_mark(f, min(118.0, hc[0] + 14.0), max(17.0, hc[1] - 24.0))
    return A.finish(f, fade=fade, width=1.4)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
