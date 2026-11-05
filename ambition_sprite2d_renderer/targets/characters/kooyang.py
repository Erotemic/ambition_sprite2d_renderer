"""The Kooyang of the History dimension: the short-finned eel of Budj Bim.

Kooyang is the Gunditjmara name of the short-finned eel (Anguilla
australis). It is long and round like a snake, olive-brown on its back and
pale yellow-grey under its belly, with a small pointed head, small eyes, a
small round fin on each side behind its head, and one soft fin that runs
along its back and under its tail and round the tip of the tail. The fin
on its back and the fin under it start at about the same place, which is
what gives the eel its name. The eels swim up the rivers from the sea and
live for many years in the swamps and lakes of the lava flow of Budj Bim,
where the Gunditjmara trapped and grew them for at least 6,600 years.

It lurks in a channel and sways in the water. When it sees you it rears its
head up. Its windup coils its body back into a tight curve; its strike is a
lunge forward with its mouth open. A hit makes it flinch and kink; at its
death it goes limp, turns a little onto its side, and sinks.

The frame is 192 by 96 px, and the eel faces right. Its body box is about
150 by 28 px (frame pixels), with its middle at about (100, 60).
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import List, Tuple

from . import _art_cast_kit as K
from . import _history_americas_kit as A

TARGET_NAME = "kooyang"
FRAME_SIZE = (192, 96)
ROWS = K.ENEMY_ROWS
#: The level of the middle of the eel's body as it rests in the water.
MID = 60.0

ACTOR_METADATA = A.enemy_metadata(
    TARGET_NAME, "Kooyang", "budj_bim", "Serpentine", "Medium", "Light", "Slither", ["eel", "fish", "water", "lunge", "bite"],
    "The kooyang (short-finned eel) of the History dimension's Budj Bim: long and round, olive-brown above and pale "
    "below, with a small pointed head and one soft fin along its back and under its tail. It lurks in a channel and sways "
    "in the water, rears its head when it sees you, coils back, and lunges forward with its mouth open.",
)

SKIN = (96, 82, 46, 255)
SKIN_SHADE = (68, 58, 34, 255)
SKIN_LIGHT = (128, 112, 66, 255)
BELLY = (194, 184, 136, 255)
BELLY_SHADE = (164, 152, 106, 255)
FIN = (122, 106, 62, 210)
FIN_EDGE = (84, 72, 42, 255)
MOUTH = (150, 82, 72, 255)
MOUTH_DARK = (82, 40, 36, 255)
EYE = (40, 34, 24, 255)
IRIS = (190, 168, 92, 255)
GLINT = (240, 236, 214, 255)
BUBBLE = (210, 226, 226, 200)

Point = Tuple[float, float]
#: The number of points along the spine, from the tip of the tail (0) to
#: the snout (the last).
COUNT = 32


def _width(u: float) -> float:
    """The half thickness of the eel at `u` along it (0 is the tail tip, 1
    the snout): thin at the tail, thickest a little behind the head, and a
    rounded, pointed head."""
    if u > 0.92:
        return 7.0 * max(0.18, 1.0 - (u - 0.92) / 0.08) ** 0.6
    return 1.4 + 6.4 * math.sin(math.pi * 0.5 * min(1.0, u / 0.70)) ** 0.8 - 0.6 * max(0.0, (u - 0.80) / 0.12)


def _tube(spine: List[Point], widths: List[float], lo: float = -1.0, hi: float = 1.0) -> List[Point]:
    """The band round `spine` from `lo` to `hi` of each half width (-1 is
    the upper edge, 1 the lower edge, for an eel that swims to the right)."""
    upper, lower = [], []
    n = len(spine)
    for k, (x, y) in enumerate(spine):
        x0, y0 = spine[max(0, k - 1)]
        x1, y1 = spine[min(n - 1, k + 1)]
        ln = math.hypot(x1 - x0, y1 - y0) or 1.0
        nx, ny = -(y1 - y0) / ln, (x1 - x0) / ln
        w = widths[k]
        upper.append((x + nx * w * lo, y + ny * w * lo))
        lower.append((x + nx * w * hi, y + ny * w * hi))
    return upper + lower[::-1]


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    rng = random.Random(f"kooyang:{anim}:{i}")
    f = K.Frame(FRAME_SIZE)

    # The pose. `x0`/`x1` are the tail tip and the snout; `amp` and `waves`
    # are the size and the count of the bends along the body, `ph` their
    # phase; `lift` raises the front of the body; `coil` draws the head back
    # into a tight curve; `gape` opens the mouth; `sink` lowers it all and
    # `roll` turns the pale belly up.
    x0, x1, amp, waves, ph, lift, coil, gape, sink, roll = 22.0, 172.0, 3.0, 1.2, cyc, 0.0, 0.0, 0.0, 0.0, 0.0
    eyes, fade, alarm, bubbles = "open", 1.0, False, 0
    if anim == "idle":
        # It lurks and sways in the water: a slow wave runs down its body.
        amp = 3.5 + 0.8 * math.sin(cyc)
        lift = 2.0 * math.sin(cyc + 0.6)
        bubbles = 1 if i in (1, 4) else 0
    elif anim == "walk":
        # It swims: a bigger wave runs down its body.
        amp, waves = 6.0, 1.5
        lift = 1.0 * math.sin(cyc * 2.0)
        x0, x1 = 22.0 + 2.0 * math.sin(cyc), 172.0 + 2.0 * math.sin(cyc)
    elif anim == "notice":
        # It rears its head up and looks at you.
        k = math.sin(math.pi * 0.5 * min(1.0, t * 1.4))
        lift, amp, eyes, alarm = 20.0 * k, 3.0, "wide", True
        x1 = 172.0 - 10.0 * k
        ph = 0.8
    elif anim == "windup":
        # It coils back: the body bends into a tight curve, the head drawn
        # back over it, the mouth a little open.
        coil = 0.9 + 0.1 * math.sin(cyc * 2.0)
        amp, waves, ph, lift, eyes, gape = 9.0, 1.6, 0.6, 8.0, "narrow", 0.25
        x0, x1 = 30.0, 146.0
    elif anim == "attack_side":
        # The lunge: the body straightens and shoots forward, the mouth wide
        # open, and snaps shut as it comes back.
        u = t
        k = math.sin(math.pi * min(1.0, u * 1.7)) if u < 0.6 else max(0.0, 1.0 - (u - 0.6) / 0.4) * 0.35
        coil = max(0.0, 0.8 - u * 3.0)
        x0, x1 = 30.0 + 10.0 * k, 146.0 + 34.0 * k
        amp, waves, ph = 9.0 - 6.0 * k, 1.6, 0.6
        lift = 8.0 - 6.0 * k
        gape = 1.0 if 0.1 < u < 0.6 else 0.2
        eyes = "narrow"
    elif anim == "hit":
        k = math.sin(math.pi * (i + 1) / (n + 1))
        x1, amp, waves, ph, lift, eyes, gape = 172.0 - 10.0 * k, 3.0 + 7.0 * k, 2.2, 1.4, -4.0 * k, "shut", 0.4 * k
        bubbles = 3
    elif anim == "death":
        u = min(1.0, t / 0.8)
        amp, waves, ph = 3.0 * (1.0 - u), 1.0, 0.4
        sink, roll, eyes = 14.0 * u, u, "shut"
        lift = -6.0 * u
        fade = 1.0 - max(0.0, t - 0.75) / 0.25
        bubbles = 2 if t < 0.6 else 0

    # The spine, from the tail tip to the snout. The wave grows toward the
    # tail; `lift` raises the front third; `coil` bends the front back.
    spine: List[Point] = []
    for k in range(COUNT):
        u = k / (COUNT - 1)
        x = x0 + (x1 - x0) * u
        wave = amp * (0.4 + 0.6 * (1.0 - u)) * math.sin(math.tau * waves * u - ph)
        front = max(0.0, (u - 0.62) / 0.38)
        y = MID + sink + wave - lift * front ** 1.6 + 4.0 * sink / 14.0 * front
        if coil:
            # The front of the body curls up and back into an S.
            y -= coil * 14.0 * math.sin(math.pi * front) * front
            x -= coil * 10.0 * front ** 2
        spine.append((x, y))
    widths = [_width(k / (COUNT - 1)) for k in range(COUNT)]

    # The fin: one soft fringe along the back and under the tail, round the
    # tip of the tail. It begins well behind the head, top and bottom alike.
    fin_w = [w + (3.2 if u < 0.58 else max(0.0, 3.2 * (1.0 - (u - 0.58) / 0.06))) * (1.0 if u > 0.03 else 0.6)
             for w, u in zip(widths, (k / (COUNT - 1) for k in range(COUNT)))]
    f.poly(_tube(spine[:22], fin_w[:22]), FIN, body=False)
    tail = spine[0]
    f.ellipse(tail[0] - 1.0, tail[1], 3.6, 3.0, FIN, body=False)
    for k in range(1, 20, 2):
        (xa, ya), (xb, yb) = spine[k], spine[k + 1]
        ln = math.hypot(xb - xa, yb - ya) or 1.0
        nx, ny = -(yb - ya) / ln, (xb - xa) / ln
        for side in (-1.0, 1.0):
            f.ink([(xa + nx * widths[k] * side, ya + ny * widths[k] * side), (xa + nx * fin_w[k] * side * 0.95 - 1.0, ya + ny * fin_w[k] * side * 0.95)], 0.5, FIN_EDGE)

    # The body: olive-brown above, the pale belly below. A body that rolls
    # in death shows more of its belly.
    f.poly(_tube(spine, widths), SKIN)
    belly_from = 0.40 - 1.1 * roll
    f.poly(_tube(spine, widths, belly_from, 1.0), BELLY, body=False)
    f.poly(_tube(spine, widths, 0.65, 1.0), BELLY_SHADE, body=False)
    f.poly(_tube(spine, widths, -0.95, -0.55), SKIN_LIGHT, body=False)
    f.ink([(x, y) for x, y in spine[3:COUNT - 3]], 0.6, SKIN_SHADE)
    # The faint marks of the scales: small dots in the skin of the back.
    for k in range(4, COUNT - 5, 2):
        x, y = spine[k]
        f.dot(x + rng.uniform(-1.0, 1.0), y - widths[k] * 0.5, 0.4, SKIN_SHADE)

    # The head: a small pointed snout at the end of the spine, the mouth
    # along its lower side, a small eye over it, and the small round fin
    # on the side behind the head.
    (hx, hy), (px, py) = spine[-1], spine[-4]
    ln = math.hypot(hx - px, hy - py) or 1.0
    ax, ay = (hx - px) / ln, (hy - py) / ln
    nx, ny = -ay, ax

    def H(u: float, v: float) -> Point:
        # u along the head (forward), v across it (+ down).
        return (hx + ax * u + nx * v, hy + ay * u + ny * v)

    if gape > 0.05:
        open_ = 4.0 + 6.0 * gape
        mouth = [H(-11.0, 0.8), H(2.0, 0.2), H(1.0, 1.0 + open_), H(-6.0, 4.0)]
        f.poly(mouth, MOUTH_DARK)
        f.poly([H(-9.0, 1.4), H(0.0, 1.0), H(-1.0, 0.6 + open_ * 0.8), H(-6.0, 3.6)], MOUTH, body=False)
        f.limb([H(-10.0, 3.6), H(0.0, 1.6 + open_)], 2.4, BELLY)
        for k in range(4):
            tx, ty = H(-1.5 - k * 2.4, 0.6)
            f.dot(tx, ty + 0.4, 0.45, GLINT)
    else:
        f.ink([H(-9.0, 2.0), H(1.0, 1.2)], 0.7, MOUTH_DARK)
    f.poly(_tube(spine[-6:], [w * 0.98 for w in widths[-6:]], -1.0, -0.3), SKIN, body=False)
    ex, ey = H(-5.5, -2.0)
    if eyes == "shut":
        f.ink([(ex - 1.4, ey), (ex + 1.4, ey + 0.3)], 0.8, A.SEPIA_INK)
    else:
        r = {"open": 1.3, "wide": 1.7, "narrow": 0.9}[eyes]
        f.ellipse(ex, ey, r + 0.3, r, IRIS, body=False)
        f.dot(ex + 0.2, ey, r * 0.6, EYE)
        f.dot(ex + 0.5, ey - 0.4, 0.35, GLINT)
        if eyes == "narrow":
            f.ink([(ex - 2.0, ey - 1.8), (ex + 1.8, ey - 1.0)], 0.8, A.SEPIA_INK)
    # The nostril, and the small side fin behind the head.
    nx_, ny_ = H(-1.0, -1.2)
    f.dot(nx_, ny_, 0.4, SKIN_SHADE)
    k_fin = COUNT - 7
    fx, fy = spine[k_fin]
    f.poly(K.turn([(fx, fy + 1.0), (fx - 6.0, fy + 3.0), (fx - 5.0, fy + 5.0), (fx - 1.0, fy + 3.5)], fx, fy, math.degrees(math.atan2(ay, ax))), FIN)

    # Bubbles that rise from the water about it.
    for k in range(bubbles):
        bx = hx - 10.0 - k * 9.0 + rng.uniform(-3.0, 3.0)
        by = hy - 10.0 - k * 6.0 - 4.0 * t
        f.ellipse(bx, max(6.0, by), 1.6 + 0.4 * k, 1.6 + 0.4 * k, BUBBLE, body=False)
        f.dot(bx - 0.5, max(6.0, by) - 0.5, 0.4, GLINT)
    if anim == "attack_side" and 0.1 < t < 0.6:
        # The swish of the lunge.
        for k, dy in enumerate((-13.0, -10.0, 11.0)):
            f.glow_line([(hx - 44.0 + k * 6.0, hy + dy + 1.0), (hx - 20.0, hy + dy)], 1.0, K.alpha(K.WHITE, 0.55))
    if alarm:
        A.alarm_mark(f, hx - 4.0, max(16.0, hy - 22.0))
    return A.finish(f, fade=fade, width=1.4)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
