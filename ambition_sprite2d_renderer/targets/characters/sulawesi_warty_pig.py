"""The Sulawesi Warty Pig of the History dimension: the pig of the oldest painted story.

The Sulawesi warty pig (Sus celebensis) lives only on Sulawesi and the
islands near it. It is small and stocky, with short legs. Its coat is dark
grey-brown and thin. Its face is long, and the adult has three pairs of
warts on it: under the eye, on the snout and on the jaw. A pale band of
hair runs along the side of the snout. A crest of stiff dark hair runs
from the top of the head down the neck to the back. The people of Sulawesi
painted this pig on the walls of their caves more than 45,000 years ago,
and it is in the oldest painted story that we know.

It walks at a quick trot with its head low, and it roots in the ground at
rest. When it sees you its head comes up and its crest stands up (the
notice row). Its windup puts the head down and paws the ground; its strike
is a short charge with the head down. A hit makes it jump back and squeal.
At its death it sinks down and fades.

The frame is 160 by 96 px: the body box is 64 by 40 world units, and the
pig faces right.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import List, Sequence, Tuple

from . import _art_cast_kit as K
from . import _history_africa_kit as H

TARGET_NAME = "sulawesi_warty_pig"
FRAME_SIZE = (160, 96)
ROWS = K.ENEMY_ROWS
#: Nothing is drawn nearer the edge of the frame than this.
MARGIN = 6.0
GROUND = 88.0

ACTOR_METADATA = K.enemy_metadata(
    TARGET_NAME, "Sulawesi Warty Pig", "Quadruped", "Medium", "Medium", "Walk", ["pig", "beast", "charge", "tusks"],
    "The Sulawesi warty pig of the History dimension's Sulawesi room: a small, stocky, dark grey-brown pig with short legs, "
    "a long warty face with a pale band on the snout, and a crest of stiff hair on its head and neck. People painted it on "
    "the walls of their caves more than 45,000 years ago. It lifts its head and raises its crest when it sees you, puts "
    "its head down and paws the ground, and charges a short way.",
)
ACTOR_METADATA["tags"] = ["enemy", "history", "sulawesi"]

HIDE = (88, 76, 70, 255)
HIDE_SHADE = (62, 52, 50, 255)
HIDE_LIGHT = (126, 110, 98, 255)
CREST = (44, 36, 34, 255)
CREST_LIGHT = (104, 90, 80, 255)
STRIPE = (190, 172, 136, 255)
SNOUT = (164, 126, 114, 255)
SNOUT_SHADE = (120, 90, 84, 255)
WART = (114, 98, 88, 255)
TUSK = (242, 232, 206, 255)
HOOF = (44, 36, 34, 255)
EYE = (30, 22, 20, 255)
MOUTH = (120, 52, 52, 255)
DUST = (196, 176, 140, 255)

Point = Tuple[float, float]


def _gait(ph: float, stride: float, lift: float) -> Point:
    """The place of a hoof at phase `ph` of a stride: on the ground it moves
    back under the body; in the air it comes forward and up."""
    return H.gait(ph, stride, lift)


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = K.Frame(FRAME_SIZE)
    dx, dy, tilt, pitch, gape = 0.0, 0.0, 0.0, 0.0, 0.0
    walk, stride, lift, paw, speed = None, 0.0, 0.0, 0.0, 0.0
    bristle, ears, eyes, tail = 0.0, 0.0, "open", 0.0
    alarm, sink, fade = False, 0.0, 1.0
    if anim == "idle":
        # It roots in the ground: the head goes down and up, the tail flicks.
        dy = 0.5 * math.sin(cyc)
        pitch = 10.0 + 6.0 * math.sin(cyc)
        tail = math.sin(cyc * 2.0)
        ears = 0.3 * math.sin(cyc * 2.0 + 1.0)
        eyes = "shut" if i == 3 else "open"
    elif anim == "walk":
        # A quick trot with the head low.
        walk, stride, lift = t, 16.0, 5.0
        dy = -1.2 * abs(math.sin(cyc * 2.0))
        tilt = 1.0 * math.sin(cyc * 2.0)
        pitch = 6.0 + 2.0 * math.sin(cyc * 2.0)
        tail = 0.6 * math.sin(cyc * 2.0)
    elif anim == "notice":
        # The head comes up, the ears go up and the crest stands up.
        k = math.sin(math.pi * min(1.0, t * 1.3))
        pitch, bristle, ears, eyes, alarm = -12.0 * k, k, k, "wide", True
        tail = 1.0
    elif anim == "windup":
        # The head goes down, the body goes back, a forefoot paws the ground.
        pitch, dx, tilt = 24.0, -4.0, 2.0
        paw = math.sin(cyc * 2.0)
        bristle, ears, eyes = 1.0, -0.6, "angry"
    elif anim == "attack_side":
        # A short charge with the head down: out (0..2), the hit (3), back (4..5).
        dx = [-4.0, 1.0, 6.0, 8.0, 5.0, 1.0][i]
        pitch = [22.0, 26.0, 28.0, 18.0, 12.0, 8.0][i]
        walk, stride, lift, speed = t * 2.0, 22.0, 6.0, [0.4, 0.9, 1.0, 0.6, 0.3, 0.1][i]
        bristle, ears, eyes = 1.0, -0.8, "angry"
        gape = 0.4 if i == 3 else 0.0
    elif anim == "hit":
        k = math.sin(math.pi * (i + 1) / (n + 1))
        dx, tilt, pitch, eyes, gape, ears = -6.0 * k, -5.0 * k, -14.0 * k, "shut", 1.0 * k, -1.0
        bristle = 0.6
    elif anim == "death":
        sink = min(1.0, t * 1.4)
        pitch, eyes, gape, tail = 10.0 * sink, "shut", 0.3, -1.0
        tilt = 4.0 * sink
        fade = 1.0 - max(0.0, t - 0.7) / 0.3

    # The whole pig is drawn this far to the left of its body box, so that
    # the snout stays inside the frame at the end of the charge.
    dx -= 4.0
    cx, cy = 62.0 + dx, 50.0 + dy + 12.0 * sink

    def B(pts: Sequence[Point]) -> List[Point]:
        """Body points: moved with the body and turned about its middle."""
        return K.turn([(x + dx, y + dy + 12.0 * sink) for x, y in pts], cx, cy, tilt)

    neck = B([(100.0, 42.0)])[0]

    def D(pts: Sequence[Point]) -> List[Point]:
        """Head points, relative to the neck: turned by the pitch of the head."""
        return K.turn([(neck[0] + x, neck[1] + y) for x, y in pts], neck[0], neck[1], pitch + tilt)

    def leg(x: float, phase: float, fore: bool, near: bool) -> None:
        colour = HIDE if near else HIDE_SHADE
        top = B([(x, 62.0)])[0]
        gx, gy = (0.0, 0.0)
        if walk is not None:
            gx, gy = _gait(walk + phase, stride, lift)
        foot = (top[0] + gx, GROUND - 1.0 + gy)
        if paw and fore and near:
            foot = (top[0] + 4.0 + 5.0 * paw, GROUND - 1.0 - 6.0 * max(0.0, math.sin(cyc * 2.0 + 0.6)))
        if sink:
            # The legs fold under the body as it goes down.
            foot = (top[0] + (6.0 if fore else -6.0) * sink, min(GROUND - 1.0, foot[1]))
        # The fore knee bends forward, the hock of the hind leg bends back.
        mid = ((top[0] + foot[0]) / 2.0 + (1.5 if fore else -2.5) - 3.0 * sink * (1 if fore else -1), (top[1] + foot[1]) / 2.0)
        f.limb([top, mid], 11.0 if not fore else 9.0, colour)
        f.limb([mid, (foot[0], foot[1] - 2.0)], 5.0, colour)
        hx, hy = foot
        f.poly([(hx - 3.0, hy - 3.0), (hx + 2.6, hy - 3.0), (hx + 4.0, hy + 0.6), (hx - 2.8, hy + 0.6)], HOOF)
        f.ink([(hx + 0.6, hy - 2.4), (hx + 1.0, hy + 0.4)], 0.6, colour)

    # The far legs.
    leg(46.0, 0.0, False, False)
    leg(88.0, 0.5, True, False)

    # The tail: thin, with a tuft of hair at its end.
    root = B([(22.0, 40.0)])[0]
    swing = 4.0 * tail
    tip = (root[0] - 4.0, root[1] + 12.0 - swing)
    f.limb([root, (root[0] - 4.0, root[1] + 5.0 - swing * 0.5), tip], 2.2, HIDE)
    f.poly([(tip[0] - 1.6, tip[1] - 1.0), (tip[0] + 1.6, tip[1] - 1.0), (tip[0] + 0.8, tip[1] + 4.0), (tip[0] - 1.8, tip[1] + 3.6)], CREST)

    # The body: a stocky barrel, higher at the shoulder than at the rump.
    f.ellipse(*B([(42.0, 50.0)])[0], 20.0, 20.0, HIDE)
    f.ellipse(*B([(64.0, 49.0)])[0], 34.0, 21.0, HIDE)
    f.ellipse(*B([(90.0, 46.0)])[0], 18.0, 22.0, HIDE)
    # The shade under the belly, and the light along the back.
    f.poly(B([(28.0, 62.0), (50.0, 69.0), (80.0, 70.0), (100.0, 62.0), (96.0, 68.0), (78.0, 72.0), (48.0, 72.0), (30.0, 66.0)]), HIDE_SHADE, body=False)
    f.poly(B([(34.0, 36.0), (56.0, 30.0), (84.0, 28.0), (96.0, 30.0), (82.0, 32.0), (58.0, 34.0)]), HIDE_LIGHT, body=False)
    # A fold of skin at the shoulder and at the haunch.
    f.ink(B([(86.0, 32.0), (82.0, 48.0), (86.0, 62.0)]), 1.2, HIDE_SHADE)
    f.ink(B([(44.0, 36.0), (38.0, 50.0), (42.0, 62.0)]), 1.2, HIDE_SHADE)

    # The crest: stiff dark hair from the neck down the middle of the back.
    # It stands up when the pig is alarmed or angry.
    rng = random.Random(f"warty pig crest {anim} {i}")
    path = [(102.0, 27.0), (96.0, 25.0), (90.0, 24.0), (84.0, 24.5), (78.0, 25.5), (72.0, 26.5), (66.0, 27.5), (60.0, 28.5), (54.0, 29.5)]
    for k, (x, y) in enumerate(path):
        length = (6.0 + 4.0 * bristle) * (1.0 - 0.6 * k / len(path)) + rng.uniform(-0.8, 0.8)
        lean = -2.5 + 2.0 * bristle
        f.poly(B([(x - 2.2, y + 2.0), (x + 2.2, y + 2.0), (x + lean, y - length)]), CREST)
    for x, y in path[:5]:
        f.ink(B([(x, y + 1.0), (x - 0.6 + 2.0 * bristle * 0.5, y - 3.0)]), 0.6, CREST_LIGHT)

    # The near legs.
    leg(40.0, 0.5, False, True)
    leg(94.0, 0.0, True, True)

    # The head: long, with a flat disc at the end of the snout.
    head = D([(-8.0, -18.0), (4.0, -18.0), (16.0, -14.0), (28.0, -7.0), (38.0, -2.0), (42.0, -1.0), (43.0, 8.0), (36.0, 11.0), (28.0, 14.0),
              (18.0, 17.0), (6.0, 19.0), (-8.0, 18.0)])
    f.poly(head, HIDE)
    # The warts: a pair under the eye, on the snout and on the jaw. They
    # bulge out of the outline of the face.
    for wx, wy, r in ((13.0, -2.0, 3.4), (27.0, -7.0, 2.8), (22.0, 15.0, 3.2)):
        f.ellipse(*D([(wx, wy)])[0], r, r * 0.85, WART)
        lx, ly = D([(wx - 0.6, wy - 0.8)])[0]
        f.ellipse(lx, ly, r * 0.45, r * 0.35, HIDE_LIGHT, body=False)
    # The pale band along the side of the snout: wide on the cheek, under
    # the eye, and narrow near the disc.
    f.poly(D([(6.0, 2.0), (16.0, 2.6), (28.0, 1.6), (39.0, 2.4), (28.0, 4.4), (16.0, 7.0), (6.0, 8.0)]), STRIPE, body=False)
    # The shade under the jaw.
    f.poly(D([(4.0, 15.0), (18.0, 14.0), (30.0, 12.0), (28.0, 14.0), (18.0, 17.0), (6.0, 19.0)]), HIDE_SHADE, body=False)
    # The disc of the snout and its nostril.
    sx, sy = D([(42.0, 3.6)])[0]
    f.ellipse(sx, sy, 2.8, 5.0, SNOUT)
    f.ellipse(sx + 0.6, sy + 1.6, 1.4, 2.6, SNOUT_SHADE, body=False)
    f.dot(*D([(42.6, 2.6)])[0], 0.9, EYE)
    # The mouth, open a little when it squeals or strikes, and a short tusk.
    if gape > 0.1:
        f.poly(D([(38.0, 9.0), (26.0, 11.0), (36.0, 9.0 + 4.0 * gape)]), MOUTH, body=False)
    f.ink(D([(39.0, 9.0), (26.0, 11.5)]), 0.8, HIDE_SHADE)
    f.poly(D([(29.0, 11.0), (31.6, 10.6), (32.4, 4.6), (30.2, 6.2)]), TUSK)
    # The ear: small and pointed. It goes up when the pig is alert.
    lift_ear = 4.0 * ears
    f.poly(D([(-4.0, -15.0), (-10.0 + lift_ear * 0.6, -25.0 - lift_ear), (2.0, -18.0)]), HIDE)
    f.poly(D([(-4.0, -16.5), (-8.0 + lift_ear * 0.6, -22.5 - lift_ear), (0.0, -18.0)]), SNOUT_SHADE, body=False)
    # The crest goes on over the top of the head.
    for k, (x, y) in enumerate(((2.0, -18.0), (8.0, -17.0), (13.0, -15.0))):
        length = (5.0 + 3.0 * bristle) * (1.0 - 0.25 * k)
        f.poly(D([(x - 2.0, y + 1.5), (x + 2.0, y + 1.5), (x - 2.0 + 1.5 * bristle, y - length)]), CREST)
    # The eye: small and dark, with a light in it.
    ex, ey = D([(17.0, -8.0)])[0]
    if eyes == "shut":
        f.ink([(ex - 2.2, ey), (ex + 2.2, ey + 0.6)], 1.1, EYE)
    else:
        r = 1.9 if eyes == "wide" else 1.5
        f.ellipse(ex, ey, r, r, EYE, body=False)
        f.dot(ex - 0.5, ey - 0.5, 0.5, (240, 230, 210, 255))
        if eyes == "angry":
            # A low brow: it is angry.
            f.ink(D([(13.0, -12.0), (21.0, -9.0)]), 1.4, CREST)

    # Dust under the hooves when it paws or charges.
    if paw or speed > 0.1:
        x = min(FRAME_SIZE[0] - MARGIN - 24.0, max(MARGIN + 14.0, B([(94.0, 0.0)])[0][0]))
        H.dust(f, x, GROUND - 1.0, (0.5 + 0.4 * abs(paw)) if paw else speed * 0.8, f"warty pig dust {anim} {i}", spread=0.9, colour=DUST)
    if anim == "attack_side" and i == 3:
        # The hit of the charge: short lines out from the snout.
        bx, by = D([(46.0, 2.0)])[0]
        for k in (-1.0, 0.0, 1.0):
            f.ink([(bx + 2.0, by + k * 5.0), (min(FRAME_SIZE[0] - MARGIN - 2.0, bx + 7.0), by + k * 8.0)], 1.4, K.alpha(K.WHITE, 0.95))
    if anim == "death" and t > 0.3:
        H.dust(f, cx, GROUND - 1.0, min(1.0, (t - 0.3) * 2.0), f"warty pig death {i}", spread=1.6, colour=DUST)
    if alarm:
        ax, _ = D([(4.0, -30.0)])[0]
        H.alarm_mark(f, min(FRAME_SIZE[0] - MARGIN - 4.0, max(MARGIN + 4.0, ax)), MARGIN + 13.0)
    return f.finish(outline=H.SEPIA_INK, width=1.7, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
