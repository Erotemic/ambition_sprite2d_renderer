"""The Mummy: a wrapped body from the Pyramid Tomb of the Nile.

A tall body wrapped from head to foot in old linen. The bands of the wrap
cross it at a slant, and some of them are stained with resin. Its face is
wrapped too: there is one dark slit in the wrap, and two eyes glow in it,
the green of old faience. A gold collar of the funeral lies on its chest. A
loose end of bandage hangs from its far arm and trails behind it.

It walks slowly, stiff in the knees, its arms out in front of it, and one
foot drags. When it sees you its eyes flare. Its windup lifts both arms high
over its head; its strike brings them down and forward in a grab. A hit
knocks bands of linen loose; at its death it comes unwrapped and falls into
a heap of linen, and its eyes go out.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import List

from . import _art_cast_kit as K
from . import _history_ancient_kit as H
from . import _stage_kit as S

TARGET_NAME = "mummy"
FRAME_SIZE = (128, 128)
ROWS = K.ENEMY_ROWS
GROUND = 124.0

ACTOR_METADATA = H.enemy_metadata(
    TARGET_NAME, "Mummy", "nile", "Biped", "Standard", "Medium", "Walk", ["undead", "linen", "tomb"],
    "A body wrapped in old linen from the Pyramid Tomb of the History dimension's Nile, with two green eyes in the "
    "slit of its wrap and a loose bandage that trails behind it. It walks slowly with its arms out, lifts both arms "
    "high and brings them down in a grab.",
)

THIGH, SHIN = 22.0, 22.0
UPPER_ARM, FOREARM = 17.0, 17.0
TORSO = 34.0
HEAD_R = 11.0
WRAP = H.LINEN
WRAP_SHADE = H.LINEN_SHADE
WRAP_DARK = (150, 132, 100, 255)
RESIN = (150, 104, 56, 255)
EYE = (120, 236, 170, 255)
SLIT = (40, 30, 26, 255)


def _bands(pen: S.Pen, a, b, width: float, rng: random.Random, count: int) -> None:
    """The bands of the wrap across a limb from `a` to `b`: slanted lines."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    ln = math.hypot(dx, dy) or 1.0
    ux, uy = dx / ln, dy / ln
    nx, ny = -uy, ux
    for k in range(count):
        u = (k + 0.5) / count
        cx, cy = a[0] + dx * u, a[1] + dy * u
        h = width * 0.5
        s = 0.35 * width
        pen.ink([(cx - nx * h - ux * s, cy - ny * h - uy * s), (cx + nx * h + ux * s, cy + ny * h + uy * s)], 0.8, WRAP_DARK)
        if rng.random() < 0.25:
            pen.ink([(cx - nx * h * 0.4, cy - ny * h * 0.4), (cx + nx * h * 0.4, cy + ny * h * 0.4)], 1.4, K.alpha(RESIN, 0.6))


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    rng = random.Random(f"mummy:{anim}:{i}")
    f = K.Frame(FRAME_SIZE)

    hip_x, crouch, lean, stride, bob, sway, rot = 58.0, 0.0, 4.0, 0.0, 0.0, 0.0, 0.0
    arms = "out"
    eyes, glow, fade, loose, unwrap = 1.0, 1.0, 1.0, 0, 0.0
    head_turn, trail_wave = 0.0, math.sin(cyc)
    groan = 0.0
    if anim == "idle":
        # It stands and sways, and the loose end lifts in a draught.
        sway = 2.0 * math.sin(cyc)
        bob = 0.6 * math.sin(cyc * 2.0)
        arms = ("out", 0.6 + 0.15 * math.sin(cyc))
    elif anim == "walk":
        # A shamble: the near leg steps, the far one drags.
        stride = math.sin(cyc)
        bob = -1.5 * abs(math.sin(cyc))
        sway = 2.5 * math.sin(cyc)
        lean = 8.0
        arms = ("out", 1.0)
        trail_wave = math.sin(cyc * 2.0)
    elif anim == "notice":
        k = math.sin(math.pi * t)
        head_turn, glow, eyes, groan = 3.0 * k, 1.0 + 1.2 * k, 1.0 + 0.4 * k, k
        arms = ("out", 0.6 + 0.4 * k)
        lean = 2.0
    elif anim == "windup":
        lean, crouch = -6.0, 2.0 + 0.6 * math.sin(cyc * 2.0)
        arms = "up"
        glow, groan = 1.6, 0.6
        bob = 0.6 * math.sin(cyc * 2.0)
    elif anim == "attack_side":
        # Up (0), down and forward in a grab (1), and it stays bent.
        g = min(1.0, t * 1.6)
        lean = -6.0 + 26.0 * math.sin(math.pi * 0.5 * g)
        crouch = 2.0 + 4.0 * g
        stride = 0.6 * g
        hip_x += 6.0 * g
        arms = ("grab", g)
        glow, groan = 1.6, 1.0 - 0.5 * g
    elif anim == "hit":
        k = math.sin(math.pi * t)
        lean, crouch = -12.0 * k, 2.0 * k
        hip_x -= 5.0 * k
        arms = ("flail", k)
        loose, glow, eyes = 3, 0.5, 0.6
    elif anim == "death":
        unwrap = min(1.0, t / 0.8)
        glow = max(0.0, 1.0 - t * 1.6)
        eyes = glow
        lean = 8.0 + 20.0 * unwrap
        crouch = 40.0 * unwrap * unwrap
        arms = ("limp", unwrap)
        rot = 30.0 * max(0.0, unwrap - 0.4)
        fade = 1.0 - max(0.0, t - 0.75) / 0.25

    pen = S.Pen(f, (hip_x, GROUND), rot)
    hip_y = GROUND - (THIGH + SHIN - 2.0) + crouch + bob
    lr = math.radians(lean + sway * 0.4)

    def up(p, length):
        return (p[0] + math.sin(lr) * length, p[1] - math.cos(lr) * length)

    def across(p, w):
        return (p[0] + math.cos(lr) * w, p[1] + math.sin(lr) * w)

    hip = (hip_x, hip_y)
    shoulder = up(hip, TORSO - 5.0)
    neck = up(hip, TORSO)
    head = up(across(neck, 1.0 + head_turn), HEAD_R + 1.0)
    hx, hy = head

    def hands():
        """The near hand and the far hand."""
        if isinstance(arms, tuple) and arms[0] == "out":
            k = arms[1]
            reach = 30.0 * k + 6.0
            near = (shoulder[0] + reach, shoulder[1] + 6.0 - 3.0 * k)
            far = (shoulder[0] + reach - 4.0, shoulder[1] + 3.0 - 3.0 * k)
        elif arms == "up":
            near = (shoulder[0] + 20.0, shoulder[1] - 26.0 + 1.5 * math.sin(cyc * 2.0))
            far = (shoulder[0] - 14.0, shoulder[1] - 27.0 + 1.5 * math.sin(cyc * 2.0 + 1.0))
        elif arms[0] == "grab":
            g = arms[1]
            a = math.radians(-70.0 + 90.0 * g)
            near = (shoulder[0] + math.cos(a) * 32.0, shoulder[1] + math.sin(a) * 32.0)
            far = (near[0] - 4.0, near[1] - 3.0)
        elif arms[0] == "flail":
            near = (shoulder[0] + 18.0, shoulder[1] - 20.0)
            far = (shoulder[0] - 14.0, shoulder[1] - 18.0)
        else:
            near = (hip_x + 12.0, hip_y + 4.0)
            far = (hip_x - 6.0, hip_y + 6.0)
        return near, far

    nh, fh = hands()

    # The loose end of bandage: from the far wrist, trailing behind.
    def trail(root, length: float, phase: float, width: float = 3.6) -> None:
        pts = [root]
        for k in range(1, 8):
            u = k / 7.0
            pts.append((root[0] - length * u, root[1] + 14.0 * u * u + 5.0 * math.sin(phase + u * 4.0) * u))
        for k in range(len(pts) - 1):
            f.limb(pen.p([pts[k], pts[k + 1]]), width * (1.0 - 0.3 * k / 7.0), WRAP_SHADE if k % 2 else WRAP)
        # The frayed end of the band.
        ex, ey = pts[-1]
        for d in (-1.2, 0.0, 1.2):
            f.ink(pen.p([(ex, ey + d), (ex - 3.0, ey + d * 1.8 + 0.6)]), 0.7, WRAP_DARK)

    def leg(side: float, colour, drag: bool):
        swing = stride * side
        if drag:
            foot = (hip_x - 6.0 + 3.0 * swing, GROUND - 2.0)
        else:
            foot = (hip_x + 8.0 * swing + side * 2.0 + 2.0, GROUND - 2.0 - 4.0 * max(0.0, swing if anim == "walk" else 0.0))
        knee, foot = S.joint((hip_x + side * 2.0, hip_y), foot, THIGH, SHIN, -0.4)
        ankle = (foot[0], foot[1] - 5.0)
        pen.limb([(hip_x + side * 2.0, hip_y), knee, ankle], 12.0, colour)
        _bands(pen, (hip_x + side * 2.0, hip_y), knee, 12.0, rng, 3)
        _bands(pen, knee, ankle, 11.0, rng, 3)
        pen.poly([(foot[0] - 6.0, foot[1] - 8.0), (foot[0] + 6.0, foot[1] - 6.0), (foot[0] + 10.0, foot[1] - 2.0), (foot[0] + 10.0, foot[1]),
                  (foot[0] - 6.0, foot[1])], colour)
        pen.ink([(foot[0] + 2.0, foot[1] - 6.0), (foot[0] + 4.0, foot[1])], 0.8, WRAP_DARK)

    def arm(hand, colour):
        elbow, hand = S.joint(shoulder, hand, UPPER_ARM, FOREARM, 1.0)
        pen.limb([shoulder, elbow, hand], 9.5, colour)
        _bands(pen, shoulder, elbow, 9.5, rng, 2)
        _bands(pen, elbow, hand, 8.5, rng, 3)
        pen.ellipse(hand[0], hand[1], 5.2, 4.6, colour)
        # Three wrapped fingers that hang from the hand.
        for k in range(3):
            pen.limb([(hand[0] + 2.0, hand[1] - 1.5 + k * 1.6), (hand[0] + 6.0, hand[1] + 0.5 + k * 1.8)], 2.0, colour)
        return elbow, hand

    # Far side, behind the body.
    if unwrap < 0.7:
        leg(-1.0, WRAP_SHADE, anim == "walk")
        _elbow, fwrist = arm(fh, WRAP_SHADE)
        # A short loose end hangs from the far wrist.
        trail(fwrist, 8.0 + 2.0 * trail_wave, cyc + 1.0, 2.6)

    # The body: a wrapped trunk, a little wider at the chest.
    hb, hf = across(hip, -11.0), across(hip, 10.0)
    sb, sf = across(shoulder, -12.0), across(shoulder, 11.0)
    nb, nf = across(neck, -5.0), across(neck, 5.0)
    trunk = [hb, hf, across(up(hip, 14.0), 11.0), sf, nf, nb, sb, across(up(hip, 14.0), -12.0)]
    if unwrap < 0.85:
        pen.poly(trunk, WRAP)
        pen.poly([hb, across(hip, -3.0), across(up(hip, 14.0), -4.0), across(shoulder, -4.0), sb, across(up(hip, 14.0), -10.0)], WRAP_SHADE, body=False)
        for k in range(8):
            y0 = 3.0 + k * 4.0
            pen.ink([across(up(hip, y0), -11.0), across(up(hip, y0 + 3.0), 10.5)], 0.8, WRAP_DARK)
        pen.ink([across(up(hip, 10.0), -6.0), across(up(hip, 13.0), 4.0)], 1.8, K.alpha(RESIN, 0.6))
        # The gold collar of the funeral, with bands of lapis.
        c0 = up(neck, -2.0)
        collar = [across(c0, -7.0), across(c0, 7.5), across(up(neck, -9.0), 6.5), across(up(neck, -10.0), 0.0), across(up(neck, -9.0), -6.0)]
        pen.poly(collar, H.GOLD, body=False)
        pen.ink([across(up(neck, -5.0), -6.0), across(up(neck, -6.5), 0.0), across(up(neck, -5.0), 6.5)], 1.2, H.LAPIS)
        pen.ink([across(up(neck, -8.0), -5.0), across(up(neck, -9.2), 0.0), across(up(neck, -8.0), 5.5)], 0.9, H.GOLD_DARK)

    if unwrap < 0.7:
        leg(1.0, WRAP, False)

    # The head: wrapped, with one dark slit and two eyes in it. The long
    # loose end comes off the back of the head and trails behind it.
    if unwrap < 0.9:
        trail((hx - 8.0, hy + 1.0), 30.0 + 5.0 * trail_wave, cyc, 4.6)
        pen.ellipse(hx, hy, HEAD_R, HEAD_R * 1.1, WRAP)
        pen.ellipse(hx - 3.0, hy + 2.0, HEAD_R * 0.6, HEAD_R * 0.7, WRAP_SHADE, body=False)
        for k in range(5):
            y = hy - 8.0 + k * 4.0
            pen.ink([(hx - 9.0, y + 1.5), (hx + 9.0, y - 1.5)], 0.8, WRAP_DARK)
        slit = [(hx - 1.0, hy - 3.0), (hx + 10.0, hy - 4.0), (hx + 10.0, hy + 0.5), (hx - 1.0, hy + 1.0)]
        pen.poly(slit, SLIT, body=False)
        for ex in (hx + 3.0, hx + 7.6):
            r = 1.4 * eyes
            if r > 0.2:
                pen.ellipse(ex, hy - 1.6, r * 1.2, r, K.alpha(EYE, min(1.0, 0.4 + glow)), body=False)
                pen.glow(ex, hy - 1.6, 1.6 + 0.6 * glow, K.alpha(EYE, min(0.5, 0.25 * glow)))
        if groan > 0.05:
            # A groan: the wrap over the mouth sags open.
            pen.ellipse(hx + 6.0, hy + 5.0, 2.2, 1.2 + 1.6 * groan, SLIT, body=False)

    if unwrap < 0.7:
        _elbow, nwrist = arm(nh, WRAP)

    # Loose bands that a hit knocks off.
    for k in range(loose):
        a0 = rng.uniform(-0.6, 0.6) + math.pi * (0.8 + 0.4 * k / max(1, loose))
        r0 = 12.0 + 16.0 * t
        cx0, cy0 = hip_x + math.cos(a0) * r0, hip_y - 24.0 + math.sin(a0) * r0 * 0.6 - 6.0 * k
        pts = [(cx0, cy0), (cx0 - 6.0, cy0 + 3.0), (cx0 - 12.0, cy0 - 1.0), (cx0 - 16.0, cy0 + 3.0)]
        f.limb(pts, 3.2, WRAP)
        H.dust(f, cx0 + 6.0, cy0 + 6.0, 0.6, f"mummy:hit:{i}:{k}", WRAP_SHADE)

    if unwrap > 0.0:
        # It comes unwrapped: a heap of linen grows, and bands fall on it.
        u = unwrap
        heap_r = 10.0 + 22.0 * u
        f.poly(K.ellipse_points(hip_x + 4.0, GROUND - 6.0 - 6.0 * u, heap_r, 3.0 + 6.0 * u, 20, 1.0, rng), WRAP)
        f.poly(K.ellipse_points(hip_x + 8.0, GROUND - 6.0, heap_r * 0.7, 2.0 + 3.0 * u, 16, 0.8, rng), WRAP_SHADE, body=False)
        for k in range(int(3 + 6 * u)):
            x0 = hip_x - heap_r * 0.8 + rng.uniform(0.0, heap_r * 1.6)
            y0 = GROUND - 6.0 - rng.uniform(0.0, 10.0 * u)
            f.ink([(x0, y0), (x0 + rng.uniform(4.0, 10.0), y0 + rng.uniform(-3.0, 3.0))], 0.9, WRAP_DARK)
        # The bands that fall from above.
        for k in range(4):
            fall = min(1.0, u * 1.4 - k * 0.12)
            if fall <= 0.0:
                continue
            x0 = hip_x - 14.0 + k * 9.0
            y0 = 40.0 + (GROUND - 50.0) * fall
            f.limb([(x0, y0), (x0 + 6.0, y0 + 4.0 - 3.0 * fall), (x0 + 12.0, y0 + 1.0)], 3.0, WRAP)
        if u > 0.9 and glow > 0.0:
            f.glow(hip_x + 8.0, GROUND - 14.0, 3.0, K.alpha(EYE, 0.6 * glow))
        H.dust(f, hip_x + 4.0, GROUND - 3.0, 0.4 + 0.6 * u, f"mummy:death:{i}", WRAP_SHADE, spread=2.0)

    if anim == "notice":
        H.alarm_mark(f, hx + 18.0, hy - 10.0)
    return f.finish(outline=H.OUTLINE, width=1.4, glow_blur=2.0, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
