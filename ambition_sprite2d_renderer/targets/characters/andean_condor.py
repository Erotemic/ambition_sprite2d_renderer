"""The Andean Condor of the History dimension: the great bird of the high Andes.

The Andean condor is one of the largest flying birds: its wings are about
three metres from tip to tip. It is black, with a ruff of white down round
the base of its neck and broad white patches on the upper side of its
wings. Its head and neck are bare skin, grey and dull red, and the male has
a fleshy comb on his head. Its bill is hooked, dark at the base and pale at
the tip. It rarely beats its wings: it soars for hours on the rising air of
the mountains, on wings that it holds flat, with the long feathers at the
tips spread apart like fingers. The peoples of the Andes honour it as a
messenger of the high world.

The bird is drawn from a little in front and above, so that both wings
spread across the frame: the far wing to the left of the body, the near
wing to the right, and the head to the right. It faces right.

It flies. Its idle row soars on flat wings that flex a little; its walk
flies on with slow beats. When it sees you it banks and looks down at you
(the notice row). Its windup lifts its wings high and brings its feet
forward; its strike is a swoop down and forward with the wings half shut,
and it opens them and pulls up after. A hit knocks feathers out of it; at
its death it tumbles out of the air and fades.

The frame is 224 by 128 px: the body box is 80 by 40 world units, and the
wings go out past it.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import List, Tuple

from . import _art_cast_kit as K
from . import _history_americas_kit as A
from . import _history_steppe_kit as H

TARGET_NAME = "andean_condor"
FRAME_SIZE = (224, 128)
ROWS = K.ENEMY_ROWS
#: Nothing is drawn nearer the edge of the frame than this.
MARGIN = 6.0

ACTOR_METADATA = A.enemy_metadata(
    TARGET_NAME, "Andean Condor", "andean_highlands", "Avian", "Large", "Medium", "Float",
    ["bird", "condor", "floating", "soaring"],
    "The Andean condor of the History dimension's Andean highlands: a huge black bird with a white ruff round its neck, white "
    "patches on its upper wings and a bare grey-red head. It soars on flat wings with the tips spread like fingers, banks to "
    "look down at you, lifts its wings high, and swoops at you feet first.",
)

Point = Tuple[float, float]

FEATHER = (54, 48, 52, 255)
FEATHER_SHADE = (34, 30, 34, 255)
FEATHER_LIGHT = (92, 86, 92, 255)
PATCH = (232, 228, 218, 255)
PATCH_SHADE = (184, 180, 174, 255)
RUFF = (246, 242, 232, 255)
RUFF_SHADE = (206, 200, 188, 255)
SKIN = (176, 96, 82, 255)
SKIN_GREY = (128, 108, 104, 255)
SKIN_DARK = (110, 52, 46, 255)
BILL = (68, 58, 56, 255)
BILL_TIP = (222, 210, 182, 255)
FOOT = (150, 140, 138, 255)
CLAW = (40, 34, 34, 255)
EYE = (120, 60, 40, 255)
#: The head is drawn in small units and made this much larger, so that it
#: reads at the size of the game.
HEAD = 1.4


def _wing(pen: H.ScaledPen, shoulder: Point, side: float, angle: float, length: float, fold: float, spread: float, far: bool) -> None:
    """One wing from `shoulder`. `side` is -1 for the wing to the left of the
    body and +1 for the wing to the right. `angle` lifts the wing above the
    level, in degrees. `fold` shortens the wing as the bird shuts it (1 is
    open). `spread` opens the long feathers at the tip like fingers. The far
    wing is drawn a little darker."""
    a = math.radians(angle)
    ux, uy = side * math.cos(a), -math.sin(a)
    vx, vy = side * math.sin(a), math.cos(a)
    span = length * fold
    chord = 22.0 * (0.75 + 0.25 * fold)
    sx, sy = shoulder

    def P(u: float, v: float) -> Point:
        return (sx + ux * u + vx * v, sy + uy * u + vy * v)

    dark = K.shade(FEATHER, 1.15) if far else FEATHER
    shade = K.shade(FEATHER_SHADE, 1.1) if far else FEATHER_SHADE
    patch = PATCH_SHADE if far else PATCH
    patch_shade = K.shade(PATCH_SHADE, 1.12) if far else PATCH_SHADE
    wrist = span * 0.62
    lead, trail = -chord * 0.36, chord * 0.64
    # The long feathers of the hand: seven fingers that spread apart, the
    # front ones longest. Their tips bend up a little.
    for k in range(7):
        q = k / 6.0
        root_v = lead + 2.0 + q * (trail - lead - 6.0)
        tip_u = span - q * span * 0.10
        tip_v = lead - 3.0 * spread + q * (chord * (0.55 + 0.55 * spread))
        bend = -2.2 * (1.0 - q)
        w = 2.0 + 0.4 * (1.0 - q)
        mid_u = (wrist + tip_u) * 0.5
        mid_v = (root_v + tip_v) * 0.5 + 0.8
        pen.poly([P(wrist - 4.0, root_v - w), P(mid_u, mid_v - w), P(tip_u - 1.6, tip_v + bend - 0.6), P(tip_u, tip_v + bend + 0.6),
                  P(mid_u, mid_v + w * 0.8), P(wrist - 4.0, root_v + w)], shade if k % 2 else dark)
        pen.ink([P(wrist, root_v), P(tip_u - 3.0, tip_v + bend * 0.7)], 0.5, K.shade(FEATHER_LIGHT, 1.1))
    # The arm of the wing: a long plank with the black coverts in front and
    # the white patch behind them, and the round ends of the feathers along
    # the trailing edge.
    pen.poly([P(-2.0, lead + 1.0), P(wrist * 0.5, lead - 1.2), P(wrist + 2.0, lead - 0.4), P(wrist + 6.0, lead + 6.0),
              P(wrist + 2.0, trail - 1.0), P(-2.0, trail)], dark)
    pen.poly([P(2.0, lead + chord * 0.40), P(wrist * 0.55, lead + chord * 0.36), P(wrist - 2.0, lead + chord * 0.50),
              P(wrist - 4.0, trail - 3.0), P(2.0, trail - 2.0)], patch, body=False)
    pen.poly([P(2.0, trail - 6.0), P(wrist - 4.0, trail - 7.0), P(wrist - 4.0, trail - 3.0), P(2.0, trail - 2.0)], patch_shade, body=False)
    for k in range(9):
        u = 3.0 + k * (wrist - 4.0) / 8.0
        drop = 1.6 + 0.8 * ((k * 7) % 3) / 2.0
        pen.poly([P(u - 2.6, trail - 2.4), P(u + 2.6, trail - 2.4), P(u + 1.8, trail + drop), P(u - 1.8, trail + drop)], shade)
    # The quills of the white feathers, and the line of the coverts.
    for k in range(4):
        u = 8.0 + k * (wrist - 12.0) / 3.0
        pen.ink([P(u, lead + chord * 0.48), P(u - 1.0, trail - 4.0)], 0.4, K.shade(patch, 1.18))
    pen.ink([P(3.0, lead + chord * 0.40), P(wrist, lead + chord * 0.42)], 0.7, shade)
    pen.ink([P(4.0, lead + 0.6), P(wrist * 0.8, lead - 0.4)], 0.6, FEATHER_LIGHT)


def _feet(pen: H.ScaledPen, hip: Point, foot: Point, open_: bool) -> None:
    """A leg and a foot: grey, with blunt dark claws. The toes open to
    grab, or curl under the body to fly."""
    pen.limb([hip, foot], 2.6, FOOT)
    for a in ((-40.0, 5.0, 40.0) if open_ else (40.0, 80.0, 120.0)):
        r = math.radians(a)
        toe = (foot[0] + math.cos(r) * 4.4, foot[1] + math.sin(r) * 4.4)
        pen.limb([foot, toe], 1.6, FOOT)
        claw = (toe[0] + math.cos(r + 1.0) * 1.6, toe[1] + math.sin(r + 1.0) * 1.6)
        pen.limb([toe, claw], 1.0, CLAW)


def _head(f: K.Frame, base: Point, look: float, beak_open: float, eyes: str) -> None:
    """The bare head on its bare neck, from `base` at the ruff. `look` turns
    the head down, in degrees (0 looks ahead)."""
    hp = H.ScaledPen(f, base, look, (0.0, 0.0), HEAD)
    bx, by = base
    # The neck: bare grey skin with folds.
    hp.limb([(bx - 1.0, by + 1.0), (bx + 6.0, by - 1.0), (bx + 10.0, by - 2.0)], 6.0, SKIN_GREY)
    hp.ink([(bx + 3.0, by - 3.0), (bx + 4.0, by + 1.6)], 0.6, K.shade(SKIN_GREY, 1.4))
    hp.ink([(bx + 6.0, by - 3.4), (bx + 6.6, by + 0.8)], 0.6, K.shade(SKIN_GREY, 1.4))
    hx, hy = bx + 13.0, by - 3.0
    # The head: long and low, dull red skin with grey on the cheek.
    hp.poly([(hx - 5.0, hy - 2.6), (hx + 1.0, hy - 4.2), (hx + 5.0, hy - 3.2), (hx + 6.4, hy + 0.6), (hx + 4.0, hy + 3.2),
             (hx - 2.0, hy + 3.4), (hx - 5.6, hy + 2.0)], SKIN)
    hp.poly([(hx - 5.6, hy + 2.0), (hx - 2.0, hy + 3.4), (hx + 4.0, hy + 3.2), (hx + 2.0, hy + 1.2), (hx - 4.0, hy + 0.6)], SKIN_DARK, body=False)
    # The comb of the male: a fleshy crest on the crown and the forehead.
    hp.poly([(hx - 3.0, hy - 3.0), (hx - 1.0, hy - 6.4), (hx + 2.0, hy - 6.8), (hx + 5.0, hy - 5.0), (hx + 6.6, hy - 2.0), (hx + 4.6, hy - 2.6),
             (hx + 1.0, hy - 3.6)], SKIN_DARK)
    hp.ink([(hx - 1.0, hy - 5.6), (hx + 4.0, hy - 4.6)], 0.5, K.shade(SKIN, 0.8))
    # The bill: a short strong hook, dark at the base and pale at the tip.
    gape = 2.2 * beak_open
    hp.poly([(hx + 5.0, hy + 1.0 + gape * 0.4), (hx + 10.0, hy + 2.0 + gape), (hx + 9.0, hy + 3.2 + gape), (hx + 4.4, hy + 2.8 + gape * 0.5)], BILL)
    hp.poly([(hx + 5.0, hy - 2.4), (hx + 9.0, hy - 2.0), (hx + 12.0, hy + 0.4), (hx + 11.6, hy + 3.6), (hx + 10.0, hy + 1.4), (hx + 5.0, hy + 1.2)], BILL)
    hp.poly([(hx + 9.6, hy - 1.4), (hx + 12.0, hy + 0.4), (hx + 11.6, hy + 3.6), (hx + 10.0, hy + 1.4)], BILL_TIP, body=False)
    hp.dot(hx + 7.0, hy - 0.8, 0.5, (30, 24, 24, 255))
    if beak_open > 0.3:
        hp.poly([(hx + 5.6, hy + 1.4), (hx + 9.4, hy + 1.8), (hx + 8.8, hy + 1.8 + gape), (hx + 5.4, hy + 2.0 + gape * 0.5)], (140, 50, 50, 255), body=False)
    ex, ey = hx + 1.6, hy - 0.8
    if eyes == "shut":
        hp.ink([(ex - 1.4, ey), (ex + 1.4, ey + 0.4)], 0.7, SKIN_DARK)
    else:
        r = 1.5 if eyes == "wide" else 1.2
        hp.ellipse(ex, ey, r, r, (238, 214, 180, 255), body=False)
        hp.dot(ex + 0.3, ey + 0.1, r * 0.6, EYE)
        hp.dot(ex + 0.4, ey + 0.1, r * 0.3, (20, 14, 14, 255))
        if eyes == "narrow":
            hp.poly([(ex - 2.2, ey - 2.0), (ex + 2.4, ey - 1.2), (ex + 2.4, ey - 0.4), (ex - 1.8, ey - 1.0)], SKIN_DARK, body=False)


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    rng = random.Random(f"condor:{anim}:{i}")
    f = K.Frame(FRAME_SIZE)
    cx, cy, tilt = 112.0, 70.0, 0.0
    # The lift of each wing above the level, in degrees (left, right).
    lift_l, lift_r = 4.0, 4.0
    flex, fold, spread, legs, look, beak_open, eyes, alarm, fade = 0.0, 1.0, 1.0, "tuck", 0.0, 0.0, "open", False, 1.0
    feathers, swipe = 0, 0.0
    if anim == "idle":
        # It soars: the wings stay flat and flex a little in the air.
        cy += 2.0 * math.sin(cyc + math.pi / 2.0)
        flex = 3.0 * math.sin(cyc)
        tilt = 2.0 * math.sin(cyc)
    elif anim == "walk":
        # It flies on with slow, deep beats.
        cy += 2.4 * math.sin(cyc + 1.0)
        beat = math.sin(cyc)
        lift_l = lift_r = 6.0 + 22.0 * beat
        fold = 0.94 + 0.06 * beat
        spread = 0.8 + 0.2 * beat
        tilt = 3.0
    elif anim == "notice":
        # It banks, and turns its head down to look at you.
        k = math.sin(math.pi * 0.5 * min(1.0, t * 1.6))
        lift_l, lift_r = 4.0 + 12.0 * k, 4.0 - 12.0 * k
        look, eyes, alarm, spread = 42.0 * k, "wide", True, 1.2
        cy -= 3.0 * k
        tilt = 4.0 * k
    elif anim == "windup":
        # The wings go up high, and the feet come forward.
        lift_l = lift_r = 46.0 + 4.0 * math.sin(cyc * 2.0)
        fold, spread, legs, look, eyes, beak_open = 0.86, 1.3, "reach", 18.0, "narrow", 0.3
        cx, cy, tilt = 108.0, 86.0 + 1.0 * math.sin(cyc * 2.0), 8.0
    elif anim == "attack_side":
        # The swoop (0..3), down and forward with the wings half shut; then
        # it opens them and pulls up.
        u = min(1.0, t / 0.6)
        back = max(0.0, (t - 0.6) / 0.4)
        cx = 96.0 + 22.0 * u - 2.0 * back
        cy = 74.0 + 14.0 * math.sin(math.pi * 0.5 * u) - 12.0 * back
        tilt = 14.0 * (1.0 - back) - 6.0 * back
        lift_l = lift_r = 30.0 * (1.0 - back) + 6.0 * back
        fold = 0.6 + 0.4 * back
        spread, legs, look, eyes, beak_open = 0.4 + 0.6 * back, "strike", 10.0, "narrow", 0.6 * u * (1.0 - back)
        swipe = math.sin(math.pi * min(1.0, t * 1.4))
    elif anim == "hit":
        k = math.sin(math.pi * (i + 1) / (n + 1))
        cx, tilt, eyes, beak_open = 112.0 - 6.0 * k, -8.0 * k, "shut", 0.7
        lift_l, lift_r, fold, spread, look = 4.0 - 14.0 * k, 4.0 + 6.0 * k, 0.92, 0.5, -10.0 * k
        feathers = 5
    elif anim == "death":
        # It tumbles: it shuts its wings, turns over and falls, and fades.
        fall = t
        shut = min(1.0, fall * 2.0)
        fold = 1.0 - 0.6 * shut
        lift_l, lift_r = 4.0 + 30.0 * shut, 4.0 - 10.0 * shut
        cx = 112.0 - 4.0 * fall
        cy = 62.0 + 14.0 * fall * fall
        tilt = -16.0 - 100.0 * fall
        spread, eyes, beak_open, legs, look = 1.4, "shut", 0.5, "limp", 20.0
        feathers = 3 + int(5 * fall)
        fade = 1.0 - max(0.0, t - 0.7) / 0.3

    pen = H.ScaledPen(f, (cx, cy), tilt, (0.0, 0.0), 1.0)
    flat = H.ScaledPen(f)

    # The far wing, to the left of the body, behind it all.
    _wing(pen, (cx - 8.0, cy - 5.0), -1.0, lift_l + flex, 90.0, fold, spread, True)

    # The tail: short and broad, a fan of blunt feathers down and back.
    tail = [(cx - 12.0, cy - 2.0), (cx - 26.0, cy + 2.0), (cx - 28.0, cy + 8.0), (cx - 22.0, cy + 12.0), (cx - 10.0, cy + 6.0)]
    pen.poly(tail, FEATHER_SHADE)
    for k in range(3):
        pen.ink([(cx - 13.0, cy + 1.0 + k * 1.6), (cx - 26.0, cy + 3.0 + k * 3.6)], 0.6, FEATHER_LIGHT)

    # The legs: tucked under to fly, out in front to grab.
    hip = (cx + 2.0, cy + 7.0)
    if legs == "reach":
        _feet(pen, hip, (cx + 14.0, cy + 17.0), True)
    elif legs == "strike":
        _feet(pen, hip, (cx + 18.0, cy + 15.0), True)
    elif legs == "limp":
        _feet(pen, hip, (cx + 3.0, cy + 17.0), False)
    else:
        _feet(pen, hip, (cx - 5.0, cy + 12.0), False)

    # The body: a heavy black oval with a sheen on the back.
    body = [(cx + 13.0, cy - 7.0), (cx + 15.0, cy + 1.0), (cx + 9.0, cy + 9.0), (cx - 4.0, cy + 10.0), (cx - 14.0, cy + 5.0),
            (cx - 15.0, cy - 2.0), (cx - 7.0, cy - 9.0), (cx + 5.0, cy - 10.0)]
    pen.poly(body, FEATHER)
    pen.poly([(cx + 15.0, cy + 1.0), (cx + 9.0, cy + 9.0), (cx - 4.0, cy + 10.0), (cx - 14.0, cy + 5.0), (cx - 2.0, cy + 4.0), (cx + 8.0, cy + 3.0)],
             FEATHER_SHADE, body=False)
    pen.ink([(cx - 9.0, cy - 6.0), (cx + 2.0, cy - 8.4)], 0.8, FEATHER_LIGHT)

    # The near wing, to the right of the body.
    _wing(pen, (cx + 4.0, cy - 1.0), 1.0, lift_r - flex, 80.0, fold, spread, False)

    # The ruff: a collar of white down round the base of the neck.
    rx, ry = cx + 14.0, cy - 12.0
    puffs = [(rx - 5.0, ry + 2.0), (rx - 3.0, ry - 2.6), (rx + 1.0, ry - 4.0), (rx + 4.6, ry - 2.0), (rx + 5.6, ry + 2.0), (rx + 3.0, ry + 4.6),
             (rx - 1.0, ry + 5.0)]
    for px, py in puffs:
        pen.ellipse(px, py, 3.0, 2.6, RUFF)
    for px, py in puffs[4:]:
        pen.ellipse(px - 0.4, py + 0.8, 2.0, 1.4, RUFF_SHADE, body=False)

    # The bare head, turned with the body and by its own look.
    base = pen.at(rx + 2.0, ry - 1.0)
    _head(f, base, tilt + look - 8.0, beak_open, eyes)

    if swipe > 0.1:
        # The streaks of the swoop behind it.
        for k in range(3):
            x0, y0 = pen.at(cx - 22.0, cy - 6.0 + k * 6.0)
            f.glow_line([(x0, y0), (x0 - 18.0, y0 - 10.0)], 1.6, K.alpha(K.WHITE, 0.7 * swipe))
    for k in range(feathers):
        qx = cx + rng.uniform(-40.0, 40.0)
        qy = cy + rng.uniform(-30.0, 22.0) + (8.0 * t if anim == "death" else 0.0)
        qx = min(FRAME_SIZE[0] - MARGIN - 6.0, max(MARGIN + 6.0, qx))
        qy = min(FRAME_SIZE[1] - MARGIN - 6.0, max(MARGIN + 6.0, qy))
        a = rng.uniform(0.0, 180.0)
        quill = K.turn([(qx - 4.0, qy), (qx, qy - 1.6), (qx + 4.0, qy), (qx, qy + 1.6)], qx, qy, a)
        flat.poly(quill, FEATHER if k % 2 else PATCH)
        flat.ink([quill[0], quill[2]], 0.5, FEATHER_SHADE)
    if alarm:
        ax, ay = pen.at(cx + 26.0, cy - 30.0)
        A.alarm_mark(f, min(FRAME_SIZE[0] - 14.0, ax), max(16.0, ay))
    return A.finish(f, fade=fade, width=1.4)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
