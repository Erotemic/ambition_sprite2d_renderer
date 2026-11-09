"""The Fanihi of the History dimension: the fruit bat of the Marianas.

The Mariana fruit bat (Pteropus mariannus), fanihi in Chamorro, is a large
flying fox of Guåhan (Guam) and the other Mariana Islands. Its body is about
20 cm long and its wings span about 1 m. It is dark brown, almost black, with
a golden-tan mantle over its neck and shoulders. It has a face like a fox's:
a long muzzle, big dark eyes and small round ears. It eats fruit, flowers
and leaves, and it roosts in the trees in colonies. It flies with slow,
deep beats of its wings, which are skin stretched between the long bones of
its fingers.

It flies. Its idle row hovers on slow beats of its wings; its walk flies on.
When it sees you it opens its wings wide and lifts its head. Its windup
draws back with its wings high; its strike is a swoop down at you with its
wings swept back and its mouth open, and it pulls up after. A hit makes it
flinch and crumple its wings; at its death it folds its wings and falls.

The frame is 160 by 128 px, and the bat faces right. Its body box (the body
and the head and the feet, without the wings) is about 76 by 40 px (frame
pixels): from x 45 to 120 and from y 47 to 87 in the middle of the idle row;
it rises and falls about 3 px as the wings beat. Its wings reach from about
y 8 to y 120.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import List, Sequence, Tuple

from . import _art_cast_kit as K
from . import _history_americas_kit as A
from . import _history_steppe_kit as H
from . import _stage_kit as S

TARGET_NAME = "fanihi"
FRAME_SIZE = (160, 128)
ROWS = K.ENEMY_ROWS
#: Nothing is drawn nearer the edge of the frame than this.
MARGIN = 6.0
#: The bat is drawn in small units about the middle of its body and made
#: this much larger.
BAT = 1.25

ACTOR_METADATA = A.enemy_metadata(
    TARGET_NAME, "Fanihi", "marianas", "Flyer", "Small", "Light", "Float", ["bat", "fruit_bat", "floating", "swoop"],
    "The fanihi of the History dimension's Marianas, the Mariana fruit bat: a large flying fox, dark brown with a "
    "golden-tan mantle and a face like a fox's. It hovers on slow beats of its wings, opens them wide when it sees you, "
    "draws back with its wings high, and swoops down at you with its wings swept back.",
)

Point = Tuple[float, float]

FUR = (64, 46, 38, 255)
FUR_SHADE = (44, 32, 28, 255)
FUR_DARK = (30, 22, 20, 255)
#: The golden-tan mantle over the neck and the shoulders.
MANTLE = (190, 142, 78, 255)
MANTLE_LIGHT = (222, 182, 112, 255)
MANTLE_SHADE = (150, 106, 56, 255)
#: The wing skin and the long bones of the fingers in it.
SKIN = (74, 56, 52, 255)
SKIN_SHADE = (54, 40, 38, 255)
SKIN_FAR = (36, 28, 28, 255)
BONE = (136, 108, 92, 255)
FACE = (78, 56, 44, 255)
MUZZLE = (104, 76, 58, 255)
NOSE = (28, 22, 22, 255)
EYE = (24, 18, 18, 255)
GLINT = (236, 226, 210, 255)
MOUTH = (120, 44, 44, 255)
TOOTH = (236, 230, 216, 255)
CLAW = (30, 24, 22, 255)

# The wing, drawn as if it points straight up from the shoulder, its front
# edge to the right; frame pixels. The fingers fan out from the wrist.
WRIST: Point = (7.0, -21.0)
THUMB: Point = (11.0, -23.0)
FINGER_TIPS: Sequence[Point] = ((11.0, -43.0), (2.0, -47.0), (-14.0, -41.0), (-25.0, -22.0))


def _wing(pen: H.ScaledPen, shoulder: Point, ankle: Point, angle: float, spread: float, skin, shade, bone) -> None:
    """A wing from `shoulder`, turned back by `angle` degrees (0 up, 90 back
    along the body, 150 down and back). Its skin goes back to `ankle`, which
    stays on the body when the wing turns. `spread` opens the fingers (1 open,
    under 0.5 folded)."""
    sx, sy = shoulder

    def T(pts):
        return K.turn([(sx + x, sy + y) for x, y in pts], sx, sy, -angle)

    wrist = WRIST
    tips = [(wrist[0] + (x - wrist[0]) * spread, wrist[1] + (y - wrist[1]) * spread) for x, y in FINGER_TIPS]
    # The trailing edge between two finger tips sags toward the wrist.
    edge: List[Point] = [(0.0, 0.0), wrist, tips[0]]
    for a, b in zip(tips, tips[1:]):
        mid = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
        edge.append((mid[0] + (wrist[0] - mid[0]) * 0.22, mid[1] + (wrist[1] - mid[1]) * 0.22))
        edge.append(b)
    skin_pts = T(edge)
    # The last panel of skin runs from the last finger back to the ankle, in
    # a curve that sags toward the shoulder.
    last = skin_pts[-1]
    mid = ((last[0] + ankle[0]) / 2.0, (last[1] + ankle[1]) / 2.0)
    sag = (mid[0] + (sx - mid[0]) * 0.25, mid[1] + (sy - mid[1]) * 0.25)
    pen.poly(skin_pts + [sag, ankle], skin)
    # The panel between the arm and the first two fingers is a little darker.
    pen.poly(T([(0.0, 0.0), wrist, tips[0], edge[3], tips[1], (-3.0, -12.0)]), shade, body=False)
    # The bones: the forearm, then the long fingers from the wrist.
    pen.limb(T([(0.0, 0.0), wrist]), 2.6, bone, body=False)
    for tip in tips:
        pen.ink(T([wrist, tip]), 1.1, bone)
    # The thumb, with its hooked claw.
    th = T([wrist, THUMB, (THUMB[0] + 2.0, THUMB[1] + 1.6)])
    pen.limb(th[:2], 1.8, bone, body=False)
    pen.ink(th[1:], 1.2, CLAW)


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    rng = random.Random(f"fanihi:{anim}:{i}")
    f = K.Frame(FRAME_SIZE)
    # The pose: `cx`, `cy` the middle of the body; `tilt` turns the bat (+ is
    # head down); `wing` turns the wings; `spread` opens the fingers.
    cx, cy, tilt = 76.0, 75.0, 0.0
    wing, spread, mouth, eyes, alarm, fade, head_up = 60.0, 1.0, 0.0, "open", False, 1.0, 0.0
    swipe = 0.0
    if anim == "idle":
        # It hovers: the body rises as the wings beat down.
        cy += 3.0 * math.sin(cyc + math.pi / 2.0)
        wing = 80.0 + 54.0 * math.sin(cyc)
        tilt = -4.0
    elif anim == "walk":
        cy += 2.0 * math.sin(cyc * 2.0 + 1.0)
        wing = 82.0 + 54.0 * math.sin(cyc * 2.0)
        tilt = 6.0
    elif anim == "notice":
        k = math.sin(math.pi * min(1.0, t * 1.4))
        wing, spread, tilt, eyes, alarm, mouth = 80.0 - 44.0 * k, 1.0 + 0.1 * k, -10.0 * k, "wide", True, 0.4 * k
        head_up = 4.0 * k
        cy -= 2.0 * k
    elif anim == "windup":
        # It draws back and up, its wings high, its head toward you.
        wing = 38.0 + 4.0 * math.sin(cyc * 2.0)
        tilt, eyes, cx = -16.0, "narrow", 68.0
        cy = 73.0 + 1.0 * math.sin(cyc * 2.0)
    elif anim == "attack_side":
        # The swoop, down and forward with the wings swept back, then it
        # pulls up.
        u = min(1.0, t / 0.6)
        back = max(0.0, (t - 0.6) / 0.4)
        cx = 68.0 + 14.0 * u - 6.0 * back
        cy = 69.0 + 10.0 * math.sin(math.pi * 0.5 * u) - 6.0 * back
        tilt = 26.0 * (1.0 - u) + 8.0 * u - 22.0 * back
        wing = 104.0 - 58.0 * back
        spread, eyes, mouth = 0.75 + 0.25 * back, "narrow", 1.0 - back
        swipe = math.sin(math.pi * min(1.0, t * 1.4))
    elif anim == "hit":
        k = math.sin(math.pi * (i + 1) / (n + 1))
        cx, tilt, wing, spread, eyes, mouth = 76.0 - 6.0 * k, -18.0 * k, 120.0, 0.6, "shut", 0.6
    elif anim == "death":
        fall = t
        cx = 76.0 - 4.0 * fall
        cy = 66.0 + 22.0 * fall * fall
        tilt = -20.0 - 140.0 * fall
        wing, spread, eyes, mouth = 110.0 + 30.0 * fall, 0.9 - 0.5 * fall, "shut", 0.3
        fade = 1.0 - max(0.0, t - 0.7) / 0.3

    pen = H.ScaledPen(f, (cx, cy), tilt, (0.0, 0.0), BAT)
    flat = S.Pen(f)
    shoulder = (cx + 6.0, cy - 5.0)
    ankle = (cx - 17.0, cy + 4.0)

    # The far wing, behind it all, a little out of step.
    _wing(pen, (shoulder[0] + 3.0, shoulder[1] - 1.0), (ankle[0] + 2.0, ankle[1] - 1.0), wing - 12.0, spread, SKIN_FAR, FUR_DARK, FUR_SHADE)

    # The hind feet, small, with hooked claws, trailing behind.
    for dx, colour in ((2.0, FUR_SHADE), (0.0, FUR)):
        foot = (ankle[0] - 4.0 + dx, ankle[1] + 1.0)
        pen.limb([(ankle[0] + 3.0 + dx, ankle[1] - 1.0), foot], 2.4, colour)
        for k in range(3):
            pen.ink([foot, (foot[0] - 2.4, foot[1] - 1.4 + k * 1.4), (foot[0] - 3.4, foot[1] - 0.2 + k * 1.4)], 0.7, CLAW)

    # The body: a long furry torso, dark below, with the golden mantle over
    # the shoulders and the neck.
    body = [(cx + 14.0, cy - 7.0), (cx + 17.0, cy), (cx + 12.0, cy + 7.0), (cx - 2.0, cy + 9.0), (cx - 14.0, cy + 7.0),
            (cx - 19.0, cy + 2.0), (cx - 15.0, cy - 4.0), (cx - 2.0, cy - 8.0)]
    pen.poly(body, FUR)
    pen.poly([(cx + 12.0, cy + 7.0), (cx - 2.0, cy + 9.0), (cx - 14.0, cy + 7.0), (cx - 19.0, cy + 2.0), (cx - 4.0, cy + 4.0),
              (cx + 10.0, cy + 3.0)], FUR_SHADE, body=False)
    pen.poly([(cx + 17.0, cy - 1.0), (cx + 14.0, cy - 8.0), (cx + 2.0, cy - 9.0), (cx - 6.0, cy - 6.0), (cx - 2.0, cy - 2.0),
              (cx + 8.0, cy + 1.0), (cx + 15.0, cy + 3.0)], MANTLE, body=False)
    pen.poly([(cx + 13.0, cy - 8.0), (cx + 2.0, cy - 9.0), (cx - 4.0, cy - 7.0), (cx + 4.0, cy - 5.0), (cx + 12.0, cy - 4.0)],
             MANTLE_LIGHT, body=False)
    for k in range(4):
        x = cx + 10.0 - k * 4.0
        pen.ink([(x, cy - 3.0 + k * 0.5), (x - 2.0, cy - 0.5 + k * 0.5)], 0.6, MANTLE_SHADE)
    for k in range(3):
        x = cx + 4.0 - k * 6.0
        pen.ink([(x, cy + 5.0), (x - 2.0, cy + 7.0)], 0.6, FUR_DARK)

    # The head: a fox's face, with a long muzzle, a big dark eye and a small
    # round ear.
    hx, hy = cx + 20.0, cy - 6.0 - head_up
    pen.poly([(cx + 13.0, cy - 6.0), (hx - 4.0, hy - 6.0), (hx + 2.0, hy - 6.6), (hx + 6.0, hy - 3.6), (hx + 13.0, hy - 0.6),
              (hx + 14.0, hy + 2.0), (hx + 11.0, hy + 4.0), (hx + 2.0, hy + 6.0), (cx + 15.0, cy + 2.0)], FACE)
    # The ear: short, round and dark.
    pen.poly([(hx - 3.0, hy - 5.0), (hx - 4.4, hy - 11.0), (hx - 1.0, hy - 12.4), (hx + 1.6, hy - 6.4)], FUR_SHADE)
    pen.ink([(hx - 2.6, hy - 6.4), (hx - 2.4, hy - 10.4)], 0.6, FUR_DARK)
    # The muzzle, lighter, and the dark nose at its tip.
    pen.poly([(hx + 5.0, hy - 1.6), (hx + 13.0, hy - 0.4), (hx + 13.6, hy + 2.4), (hx + 10.0, hy + 3.6), (hx + 4.0, hy + 2.4)], MUZZLE,
             body=False)
    pen.poly([(hx + 12.2, hy - 1.0), (hx + 14.4, hy + 0.2), (hx + 14.0, hy + 2.0), (hx + 12.2, hy + 1.6)], NOSE, body=False)
    if mouth > 0.3:
        gape = 2.4 * mouth
        pen.poly([(hx + 4.0, hy + 3.0), (hx + 12.0, hy + 2.4), (hx + 11.0, hy + 3.0 + gape), (hx + 5.0, hy + 3.6 + gape * 0.6)], MOUTH)
        pen.poly([(hx + 10.4, hy + 2.6), (hx + 11.2, hy + 2.6), (hx + 10.8, hy + 4.2)], TOOTH, body=False)
    else:
        pen.ink([(hx + 5.0, hy + 3.0), (hx + 11.0, hy + 2.6)], 0.6, FUR_DARK)
    # The eye: big and dark, with a bright glint.
    ex, ey = hx + 3.4, hy - 2.0
    if eyes == "shut":
        pen.ink([(ex - 1.8, ey), (ex + 1.8, ey + 0.4)], 0.8, FUR_DARK)
    else:
        r = 2.4 if eyes == "wide" else 2.0
        pen.ellipse(ex, ey, r, r * (0.7 if eyes == "narrow" else 1.0), EYE, body=False)
        pen.dot(ex + 0.7, ey - 0.6, 0.7, GLINT)
        if eyes == "narrow":
            pen.ink([(ex - 2.6, ey - 2.0), (ex + 2.4, ey - 1.0)], 0.8, FUR_DARK)

    # The near wing, over the body.
    _wing(pen, shoulder, ankle, wing, spread, SKIN, SKIN_SHADE, BONE)

    if swipe > 0.1:
        # The streak of the swoop behind it.
        for k in range(3):
            x0, y0 = pen.at(cx - 20.0, cy - 6.0 + k * 6.0)
            f.glow_line([(x0, y0), (max(MARGIN + 4.0, x0 - 26.0), max(MARGIN + 4.0, y0 - 16.0))], 2.0, K.alpha(K.WHITE, 0.7 * swipe))
    if anim == "hit":
        # A few tufts of fur knocked loose.
        for k in range(4):
            px = min(FRAME_SIZE[0] - MARGIN - 6.0, max(MARGIN + 6.0, cx + rng.uniform(-30.0, 30.0)))
            py = min(FRAME_SIZE[1] - MARGIN - 6.0, max(MARGIN + 6.0, cy + rng.uniform(-24.0, 16.0)))
            flat.ellipse(px, py, 2.4, 1.6, MANTLE if k % 2 else FUR)
    if alarm:
        ax, ay = pen.at(hx + 4.0, hy - 20.0)
        A.alarm_mark(f, min(FRAME_SIZE[0] - 16.0, ax), max(18.0, ay))
    return A.finish(f, fade=fade, width=1.6)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
