"""The Japanese Macaque of the History dimension: the snow monkey of the Jomon woods.

The Japanese macaque (Macaca fuscata) lives farther north than any other
monkey: in the snowy woods of Honshu, where the Jomon people lived. Its fur
is thick and grey-brown, with a hood of fur round its face. Its face is bare
and red, and so is its rump. Its tail is short. It walks and runs on all
fours, and it is quick and bold.

At rest it sits hunched in its thick fur and looks round. It moves in short
hops. When it sees you it sits up, raises its brows and opens its mouth (a
macaque's threat). Its windup is a crouch: low, the rump up, the teeth
bared. Its strike is a leap: it springs at you with its hands out to grab,
and lands. A hit makes it shut its eyes and duck; at its death it slumps
forward and fades.

The frame is 128 by 112 px: the body box is 40 by 40 world units, and the
macaque faces right.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import List, Tuple

from . import _art_cast_kit as K
from . import _history_africa_kit as H
from . import _stage_kit as S

TARGET_NAME = "japanese_macaque"
FRAME_SIZE = (128, 112)
ROWS = K.ENEMY_ROWS
#: Nothing is drawn nearer the edge of the frame than this.
MARGIN = 6.0
GROUND = 104.0
#: The macaque is drawn in design units and made larger about this point
#: on the ground, so that it fills its body box.
SIZE = 1.3
PIVOT = (52.0, GROUND)

ACTOR_METADATA = K.enemy_metadata(
    TARGET_NAME, "Japanese Macaque", "Quadruped", "Standard", "Light", "Walk", ["monkey", "macaque", "leap", "grab"],
    "The Japanese macaque (the snow monkey) of the History dimension's Jomon room: thick grey-brown fur, a bare red face "
    "and a red rump, and a short tail. It moves in short hops, crouches low with its teeth bared, and leaps at you with "
    "its hands out to grab.",
)
ACTOR_METADATA["tags"] = ["enemy", "history", "jomon"]

Point = Tuple[float, float]

FUR = (150, 128, 106, 255)
FUR_SHADE = (110, 92, 78, 255)
FUR_LIGHT = (190, 172, 148, 255)
FACE = (214, 98, 90, 255)
FACE_SHADE = (172, 66, 64, 255)
FACE_LIGHT = (236, 140, 124, 255)
PALM = (120, 84, 74, 255)
MOUTH = (110, 34, 38, 255)
TEETH = (246, 238, 220, 255)
EYE = (70, 44, 26, 255)
DUST = (196, 176, 140, 255)
#: The length of the back from the hips to the shoulders, and of each bone
#: of a limb.
BACK = 24.0
ARM = 13.0
LEG = 13.5


def _tufts(f: K.Frame, cx: float, cy: float, rx: float, ry: float, ang: float, a0: float, a1: float, size: float, colour, seed: str) -> None:
    """Soft round tufts of thick fur round part of an oval: from angle `a0`
    to `a1` (degrees, about the oval turned by `ang`). They make the edge
    of the coat soft and full."""
    rng = random.Random(seed)
    steps = max(2, int(abs(a1 - a0) / 22.0))
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    for k in range(steps + 1):
        a = math.radians(a0 + (a1 - a0) * k / steps + rng.uniform(-4.0, 4.0))
        ex, ey = (rx - size * 0.3) * math.cos(a), (ry - size * 0.3) * math.sin(a)
        r = size * rng.uniform(0.8, 1.1)
        f.ellipse(cx + ex * c - ey * s, cy + ex * s + ey * c, r, r * 0.9, colour)


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = H.ScaledFrame(FRAME_SIZE, SIZE, PIVOT)

    # The pose: `up` 0 is on all fours, 1 is sitting up; `crouch` lowers the
    # body; `air` lifts the whole monkey off the ground.
    dx, up, crouch, air, tilt, head_turn = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    brow, mouth, eyes, fade, alarm, slump = 0.0, 0.0, "open", 1.0, False, 0.0
    hop, reach, grab, push = None, 0.0, 0.0, 0.0
    if anim == "idle":
        # It sits hunched in its fur and looks round.
        up = 0.85 + 0.02 * math.sin(cyc)
        head_turn = 6.0 * math.sin(cyc)
        eyes = "shut" if i == 3 else "open"
    elif anim == "walk":
        # Two short hops.
        hop = (t * 2.0) % 1.0
        h = math.sin(math.pi * (hop - 0.2) / 0.6) if 0.2 < hop < 0.8 else 0.0
        air = 7.0 * h
        tilt = -7.0 * math.cos(math.pi * hop) * (1.0 if 0.1 < hop < 0.9 else 0.4)
        dx = -2.0 + 4.0 * hop
    elif anim == "notice":
        # It sits up, raises its brows and opens its mouth: a threat.
        k = math.sin(math.pi * min(1.0, t * 1.3))
        up, brow, mouth, eyes, alarm = 0.5 * k, k, 0.8 * k, "wide", True
        head_turn = -8.0 * k
    elif anim == "windup":
        # Low, the rump up, the teeth bared; it rocks, ready to spring.
        crouch = 1.0
        tilt = 8.0 + 2.0 * math.sin(cyc * 2.0)
        dx = -3.0 + 1.5 * math.sin(cyc * 2.0)
        mouth, brow, eyes = 0.6, 0.8, "narrow"
    elif anim == "attack_side":
        # The leap, as key frames: dx, air, tilt, crouch, reach, push, grab.
        table = [
            (-3.0, 0.0, 8.0, 1.0, 0.2, 0.3, 0.0),
            (2.0, 12.0, -12.0, 0.0, 1.0, 1.0, 0.0),
            (6.0, 14.0, -2.0, 0.0, 1.0, 0.8, 0.4),
            (9.0, 6.0, 8.0, 0.0, 0.8, 0.3, 1.0),
            (10.0, 0.0, 6.0, 0.5, 0.3, 0.0, 1.0),
            (8.0, 0.0, 2.0, 0.2, 0.0, 0.0, 0.4),
        ]
        dx, air, tilt, crouch, reach, push, grab = table[i]
        mouth, eyes = (0.8 if i in (1, 2, 3) else 0.4), "narrow"
    elif anim == "hit":
        k = math.sin(math.pi * (i + 1) / (n + 1))
        up, head_turn, dx, eyes, mouth, tilt = 0.25 * k, -12.0 * k, -6.0 * k, "shut", 0.5 * k, -4.0 * k
    elif anim == "death":
        u = min(1.0, t / 0.8)
        slump, eyes, head_turn = u, "shut", 20.0 * u
        fade = 1.0 - max(0.0, t - 0.75) / 0.25

    # The body: the hips, and the shoulders on the angle of the back.
    hip = (46.0 + dx + 4.0 * up, 82.0 + 10.0 * up + 6.0 * crouch - air + 10.0 * slump)
    theta = math.radians(-6.0 - 76.0 * up + tilt + 10.0 * slump)
    sh = (hip[0] + BACK * math.cos(theta), hip[1] + BACK * math.sin(theta) + 4.0 * crouch)
    theta = math.atan2(sh[1] - hip[1], sh[0] - hip[0])
    ax, ay = math.cos(theta), math.sin(theta)

    def leg(near: bool) -> None:
        colour = FUR if near else FUR_SHADE
        root = (hip[0] + (1.0 if near else -2.0), hip[1] + 3.0)
        fx, fy = root[0] + 4.0 + 6.0 * up, GROUND - 2.0
        if hop is not None:
            p = hop
            if p < 0.3:
                fx = root[0] - 2.0 - 10.0 * (p / 0.3)
            elif p < 0.8:
                fx = root[0] - 12.0 + 18.0 * (p - 0.3) / 0.5
            else:
                fx = root[0] + 6.0 - 6.0 * (p - 0.8) / 0.2
            fx += 0.0 if near else -2.0
        if push or air:
            # In a leap the hind legs push out behind.
            fx = fx + (root[0] - 22.0 + (0.0 if near else -2.0) - fx) * push
            fy = min(GROUND - 2.0, fy + (root[1] + 6.0 - fy) * min(1.0, push + air / 10.0))
        if crouch and not air:
            fx = root[0] + 12.0
        if slump:
            fx -= 6.0 * slump
        # The knee goes forward and up, whichever way the leg points.
        knee, foot = max((S.joint(root, (fx, fy), LEG, LEG, b) for b in (-1.0, 1.0)), key=lambda kf: 0.6 * kf[0][0] - kf[0][1])
        f.limb([root, knee], 8.0, colour)
        f.limb([knee, foot], 5.4, colour)
        f.ellipse(foot[0] + 2.6, foot[1] + 0.4, 4.4, 2.2, colour)
        f.ink([(foot[0] + 4.6, foot[1] + 0.6), (foot[0] + 6.6, foot[1] + 1.2)], 0.6, PALM)

    def arm(near: bool) -> None:
        colour = FUR if near else FUR_SHADE
        root = (sh[0] + (1.0 if near else -2.0), sh[1] + 3.0)
        hx, hy = root[0] + 3.0, GROUND - 2.0
        if up > 0.5:
            # Sitting, the hands rest in front of the body.
            hx, hy = hip[0] + 14.0 + (2.0 if near else -1.0), GROUND - 4.0
        if hop is not None:
            p = hop
            if p < 0.2:
                hx = root[0] + 4.0 - 8.0 * (p / 0.2)
            elif p < 0.8:
                hx = root[0] - 4.0 + 16.0 * (p - 0.2) / 0.6
                hy = min(GROUND - 2.0, root[1] + 18.0)
            else:
                hx = root[0] + 12.0 - 8.0 * (p - 0.8) / 0.2
            hx += 0.0 if near else 3.0
        if reach:
            # In a leap the hands reach out in front, to grab.
            rx, ry = root[0] + 20.0 + (0.0 if near else -3.0), root[1] + 9.0 + (0.0 if near else 1.5)
            hx, hy = hx + (rx - hx) * reach, min(GROUND - 2.0, hy + (ry - hy) * reach)
        if crouch and not air and not reach:
            hx, hy = root[0] + 10.0, GROUND - 2.0
        if slump:
            hx += 8.0 * slump
        # The elbow goes back and up, whichever way the arm points.
        elbow, hand = max((S.joint(root, (hx, hy), ARM, ARM, b) for b in (-1.0, 1.0)), key=lambda eh: -0.6 * eh[0][0] - eh[0][1])
        f.limb([root, elbow], 6.6, colour)
        f.limb([elbow, hand], 5.2, colour)
        if grab > 0.5 and reach:
            # The fingers close on what it grabs.
            f.ellipse(hand[0] + 1.6, hand[1], 3.0, 3.0, PALM if near else FUR_SHADE)
        else:
            f.ellipse(hand[0] + 2.0, hand[1] + 0.2, 3.6, 2.2, PALM if near else FUR_SHADE)
            if reach > 0.5:
                for k in range(3):
                    f.ink([(hand[0] + 3.0, hand[1] - 1.0 + k * 1.2), (hand[0] + 6.0, hand[1] - 2.0 + k * 2.0)], 0.9, PALM)

    leg(False)
    arm(False)

    # The tail: short and thick, up and back from the hips.
    root = (hip[0] - 9.0 * ax + ay * 4.0, hip[1] - 9.0 * ay - ax * 4.0)
    tail_ang = math.radians(math.degrees(theta) + 200.0 + 40.0 * up + 30.0 * slump + 3.0 * air)
    tip = (root[0] + 8.0 * math.cos(tail_ang), root[1] + 8.0 * math.sin(tail_ang))
    f.limb([root, tip], 5.4, FUR_SHADE)

    # The body: an oval along the back, thick with fur.
    cx, cy = (hip[0] + sh[0]) / 2.0, (hip[1] + sh[1]) / 2.0
    ang = math.degrees(theta)
    rx, ry = BACK / 2.0 + 9.0, 10.5
    f.poly(K.turn(K.ellipse_points(cx, cy, rx, ry, 30), cx, cy, ang), FUR)
    _tufts(f, cx, cy, rx, ry, ang, 190.0, 350.0, 3.6, FUR, f"mac:back:{anim}:{i}")
    _tufts(f, cx, cy, rx, ry, ang, 30.0, 150.0, 3.0, FUR, f"mac:belly:{anim}:{i}")
    # The shade of the belly and the light of the back.
    f.poly(K.turn([(cx - rx * 0.7, cy + ry * 0.4), (cx + rx * 0.7, cy + ry * 0.4), (cx + rx * 0.5, cy + ry * 0.9), (cx - rx * 0.5, cy + ry * 0.9)],
                  cx, cy, ang), FUR_SHADE, body=False)
    f.poly(K.turn([(cx - rx * 0.6, cy - ry * 0.6), (cx + rx * 0.5, cy - ry * 0.75), (cx + rx * 0.2, cy - ry * 0.45), (cx - rx * 0.5, cy - ry * 0.35)],
                  cx, cy, ang), FUR_LIGHT, body=False)
    for k in range(3):
        u = -0.4 + k * 0.35
        px, py = cx + ax * rx * u, cy + ay * rx * u
        f.ink([(px - ay * 3.0, py + ax * 3.0), (px - ay * 7.0 - ax * 2.0, py + ax * 7.0 - ay * 2.0)], 0.8, FUR_SHADE)
    # The red rump, under the tail.
    rpx, rpy = hip[0] - 10.0 * ax - ay * 3.0, hip[1] - 10.0 * ay + ax * 3.0
    f.ellipse(rpx, rpy, 3.4, 4.4, FACE)
    f.ellipse(rpx - 0.6, rpy + 0.8, 1.8, 2.6, FACE_SHADE, body=False)

    leg(True)

    # The head: in front of the shoulders on all fours, on top when it sits.
    hc = (sh[0] + 8.0 - 4.0 * up + 3.0 * slump, sh[1] - 6.0 - 3.0 * up + 7.0 * slump - 2.0 * crouch)
    hturn = head_turn

    def Hd(*p: Point) -> List[Point]:
        return K.turn([(hc[0] + x, hc[1] + y) for x, y in p], hc[0], hc[1], hturn)

    # The hood of thick fur round the face.
    f.ellipse(hc[0], hc[1], 10.0, 10.0, FUR)
    _tufts(f, hc[0], hc[1], 10.0, 10.0, hturn, 140.0, 300.0, 3.0, FUR, f"mac:hood:{anim}:{i}")
    _tufts(f, hc[0], hc[1], 10.0, 10.0, hturn, 60.0, 130.0, 2.8, FUR_LIGHT, f"mac:cheek:{anim}:{i}")
    f.ellipse(*Hd((-2.0, -5.0))[0], 6.0, 3.0, FUR_LIGHT, body=False)
    # The bare red face: a flat brow, close eyes, a short muzzle.
    face = Hd((1.0, -6.0), (7.0, -7.0 - 1.6 * brow), (11.0, -4.0), (12.5, 1.0), (13.0, 5.0), (10.0, 8.6), (5.0, 9.0), (2.0, 6.0), (0.0, 1.0))
    f.poly(face, FACE)
    f.poly(Hd((3.0, -5.0), (8.0, -5.6 - 1.6 * brow), (10.0, -3.6), (6.0, -3.6)), FACE_LIGHT, body=False)
    f.poly(Hd((2.0, 5.0), (8.0, 6.0), (10.0, 8.6), (5.0, 9.0)), FACE_SHADE, body=False)
    # The eye under the brow.
    ex, ey = Hd((8.0, -2.0 - 0.6 * brow))[0]
    if eyes == "shut":
        f.ink([(ex - 1.8, ey), (ex + 1.8, ey + 0.4)], 1.0, MOUTH)
    else:
        r = {"open": 1.4, "wide": 1.9, "narrow": 0.9}[eyes]
        f.ellipse(ex, ey, 1.7, r, (238, 224, 200, 255), body=False)
        f.ellipse(ex + 0.5, ey, 1.0, min(r, 1.2), EYE, body=False)
        if eyes == "narrow":
            f.ink([(ex - 2.2, ey - 1.8), (ex + 2.0, ey - 0.6)], 1.0, FACE_SHADE)
    # The nostrils.
    f.dot(*Hd((12.4, 1.8))[0], 0.5, MOUTH)
    # The mouth: a line, or open with the teeth bared.
    if mouth > 0.05:
        mx, my = Hd((10.0, 5.6))[0]
        f.ellipse(mx, my, 2.2 + 0.6 * mouth, 0.8 + 2.2 * mouth, MOUTH, body=False)
        f.poly([(mx - 1.8, my - 0.6 - 1.6 * mouth), (mx + 1.8, my - 0.6 - 1.6 * mouth), (mx + 1.4, my + 0.2 - 1.6 * mouth),
                (mx - 1.4, my + 0.2 - 1.6 * mouth)], TEETH, body=False)
    else:
        f.ink(Hd((7.0, 6.0), (11.6, 5.4)), 0.8, MOUTH)
    # The small ear, half hidden in the fur.
    f.ellipse(*Hd((-2.0, -2.0))[0], 1.8, 2.4, FUR_SHADE, body=False)
    f.ink(Hd((-2.4, -3.4), (-1.2, -0.6)), 0.7, FACE_SHADE)

    arm(True)

    if hop is not None and (hop < 0.12 or hop > 0.88):
        H.dust(f, hip[0] + 6.0, GROUND - 1.0, 0.35, f"mac:hop:{i}", spread=0.6, colour=DUST)
    if anim == "attack_side" and i in (0, 4):
        H.dust(f, hip[0] + 4.0, GROUND - 1.0, 0.6, f"mac:leap:{i}", spread=0.8, colour=DUST)
    if anim == "attack_side" and i == 3:
        # The grab: short lines out from the hands.
        bx, by = sh[0] + 22.0, sh[1] + 2.0
        for k in (-1.0, 0.0, 1.0):
            f.ink([(bx + 1.0, by + k * 4.0), (min(FRAME_SIZE[0] - MARGIN - 1.0, bx + 6.0), by + k * 6.0)], 1.2, K.alpha(K.WHITE, 0.95))
    if anim == "death" and t > 0.3:
        H.dust(f, 60.0, GROUND - 1.0, min(1.0, (t - 0.3) * 2.0), f"mac:death:{i}", spread=1.6, colour=DUST)
    if alarm:
        H.alarm_mark(f, min(FRAME_SIZE[0] - MARGIN - 4.0, hc[0] + 4.0), max(MARGIN + 11.0, hc[1] - 22.0))
    return f.finish(outline=H.SEPIA_INK, width=1.5, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
