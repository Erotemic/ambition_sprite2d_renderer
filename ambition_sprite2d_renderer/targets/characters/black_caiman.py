"""The Black Caiman of the History dimension: the great crocodilian of the Amazon.

The black caiman (Melanosuchus niger) lives in the slow rivers, the
flooded forest and the lakes of the Amazon basin. It is the largest
predator of the basin. Its skin is dark, almost black. Its lower jaw has
pale grey-yellow bands, and faint pale bands cross its flanks and its
tail. Its head is heavy and broad, with a snout much shorter and wider
than a gharial's. Bony ridges stand over its eyes. Its tail is long and
heavy, with a double crest of scutes.

At rest it lurks low in the shallows and breathes slowly. On land it
walks low on its short legs. When it sees you it lifts its heavy head.
Its windup is a lurk: it draws back, presses low and parts its jaws. Its
strike is a lunge: it surges forward with its jaws wide open, and the
jaws shut. A hit makes it shut its eyes and flinch; at its death it lies
flat on the ground, goes still and fades.

The frame is 320 by 96 px: the body box is 112 by 28 world units, and the
caiman faces right.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Tuple

from . import _art_cast_kit as K
from . import _history_africa_kit as H

TARGET_NAME = "black_caiman"
FRAME_SIZE = (320, 96)
ROWS = K.ENEMY_ROWS
#: Nothing is drawn nearer the edge of the frame than this.
MARGIN = 6.0
GROUND = 88.0
#: The caiman is drawn at its size in the frame.
SIZE = 1.0
PIVOT = (160.0, GROUND)

ACTOR_METADATA = K.enemy_metadata(
    TARGET_NAME, "Black Caiman", "Quadruped", "Standard", "Heavy", "Walk", ["crocodilian", "caiman", "lurk", "lunge"],
    "The black caiman of the Amazon, of the History dimension's Amazonia rooms: dark, almost black, with pale "
    "grey-yellow bands on its lower jaw and faint pale bands on its flanks, a heavy broad head with bony ridges over "
    "the eyes, and a heavy tail. It lurks low, draws back, then lunges forward with its jaws open.",
)
ACTOR_METADATA["tags"] = ["enemy", "history", "amazonia"]

Point = Tuple[float, float]

#: The dark skin. It is a little green and a little warm, so that the sepia
#: outline still shows round it.
SKIN = (64, 66, 56, 255)
SKIN_SHADE = (44, 46, 40, 255)
SKIN_LIGHT = (98, 100, 84, 255)
#: The faint pale bands on the flanks and the tail.
FLANK_BAND = (110, 108, 88, 255)
#: The pale grey-yellow bands on the lower jaw.
JAW_BAND = (170, 162, 120, 255)
BELLY = (176, 168, 132, 255)
BELLY_SHADE = (140, 132, 102, 255)
EYE = (196, 152, 64, 255)
PUPIL = (24, 20, 16, 255)
MOUTH = (216, 176, 146, 255)
MOUTH_DARK = (158, 110, 94, 255)
TEETH = (246, 240, 222, 255)
MUD = (120, 104, 78, 255)
#: The tail tip and the neck, on the body's long axis (frame x).
TAIL_X = 22.0
NECK_X = 192.0
#: The length of the head behind the snout, and of the snout. The snout is
#: short and broad, not long and thin as a gharial's.
SKULL = 32.0
SNOUT = 30.0
#: The height of the body over its centre line (`top`) and under it
#: (`bottom`), from the tail tip (0) to the neck (1). The body is heavy.
PROFILE = [(0.0, 2.5, 2.5), (0.15, 5.0, 4.5), (0.4, 10.0, 8.5), (0.58, 15.0, 12.5), (0.88, 15.5, 13.0), (1.0, 12.5, 10.5)]


def _profile(u: float) -> Tuple[float, float]:
    """The heights over and under the centre line at `u` along the body."""
    for (u0, t0, b0), (u1, t1, b1) in zip(PROFILE, PROFILE[1:]):
        if u <= u1:
            k = (u - u0) / (u1 - u0)
            k = k * k * (3.0 - 2.0 * k)
            return t0 + (t1 - t0) * k, b0 + (b1 - b0) * k
    return PROFILE[-1][1], PROFILE[-1][2]


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = H.ScaledFrame(FRAME_SIZE, SIZE, PIVOT)

    # The pose. `lift` turns the head up (degrees); `jaw` 1 is wide open;
    # `low` presses the body down (a lurk); `sink` lays it flat on the
    # ground; `sway` moves the tail.
    dx, lift, jaw, low, sink, sway, breathe = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    eyes, fade, alarm, walk_ph, lunge = "open", 1.0, False, None, -1
    if anim == "idle":
        # It lurks low and breathes; the tail stirs.
        breathe = math.sin(cyc)
        sway = 0.4 * math.sin(cyc + 0.8)
        lift = -1.0 * math.sin(cyc - 0.5)
        low = 0.3
        eyes = "shut" if i == 3 else "open"
    elif anim == "walk":
        # It walks low. The legs move in diagonal pairs and the body surges
        # a little on each step.
        walk_ph = t
        dx = 1.5 * math.sin(cyc * 2.0)
        sway = math.sin(cyc * 2.0)
        lift = -1.0 * math.sin(cyc * 2.0 + 1.0)
    elif anim == "notice":
        # It lifts its heavy head and looks.
        k = math.sin(math.pi * min(1.0, t * 1.3))
        lift, eyes, alarm, sway = -10.0 * k, "wide", True, 0.6 * k
    elif anim == "windup":
        # It draws back, presses low and parts its jaws.
        dx = -7.0 + 1.5 * math.sin(cyc)
        lift = -3.0 - 1.5 * math.sin(cyc)
        jaw = 0.25 + 0.08 * math.sin(cyc * 2.0)
        low, sway, eyes = 1.0, 1.0, "narrow"
    elif anim == "attack_side":
        # The lunge, as key frames: dx, lift, jaw, low. The jaws open, the
        # body surges forward, and the jaws shut.
        table = [
            (-7.0, -4.0, 0.4, 1.0),
            (8.0, -8.0, 1.0, 0.3),
            (18.0, -6.0, 1.0, 0.0),
            (20.0, -1.0, 0.0, 0.0),
            (12.0, -1.0, 0.1, 0.2),
            (3.0, 0.0, 0.0, 0.3),
        ]
        dx, lift, jaw, low = table[i]
        eyes, sway, lunge = "narrow", 1.0 - 0.3 * i, i
    elif anim == "hit":
        k = math.sin(math.pi * (i + 1) / (n + 1))
        dx, lift, jaw, eyes, sway = -7.0 * k, 5.0 * k, 0.2 * k, "shut", -0.8 * k
    elif anim == "death":
        # It lies flat on the ground, the head comes down, it goes still and
        # fades.
        u = min(1.0, t / 0.6)
        sink = u * u * (3.0 - 2.0 * u)
        lift, eyes = 3.0 * sink, "shut"
        fade = 1.0 - max(0.0, t - 0.7) / 0.3

    # The centre line of the body, from the tail tip to the neck.
    def centre(u: float) -> Point:
        x = TAIL_X + (NECK_X - TAIL_X) * u + dx * u
        k = min(1.0, u / 0.55)
        k = k * k * (3.0 - 2.0 * k)
        y = GROUND - 12.0 - 14.0 * k + (3.0 * low + 6.0 * sink) * k
        y += 2.5 * sway * (1.0 - u) ** 2 - 0.4 * breathe * k
        return x, y

    steps = 48
    us = [s / steps for s in range(steps + 1)]
    tops, bottoms = [], []
    for u in us:
        x, y = centre(u)
        top, bottom = _profile(u)
        top += 0.5 * breathe * (u > 0.5)
        bottom = bottom - 3.0 * sink * (u > 0.4)
        tops.append((x, y - top))
        bottoms.append((x, min(GROUND - 1.0, y + bottom)))

    def at(s: int, k: float) -> Point:
        """The point `k` of the way from the top (0) to the bottom (1) of the
        body at step `s`."""
        (xt, yt), (xb, yb) = tops[s], bottoms[s]
        return xt + (xb - xt) * k, yt + (yb - yt) * k

    def strip(u0: float, u1: float, k0: float, k1: float, colour) -> None:
        """A band of the body from `u0` to `u1` along it, and from `k0` to
        `k1` of the way from its top (0) to its bottom (1)."""
        idx = [s for s, u in enumerate(us) if u0 <= u <= u1]
        if len(idx) < 2:
            return
        f.poly([at(s, k0) for s in idx] + [at(s, k1) for s in reversed(idx)], colour, body=False)

    def leg(fore: bool, near: bool) -> None:
        """A short thick leg. The near legs have their own outline, so that
        they show on the dark body."""
        colour = SKIN if near else SKIN_SHADE
        u = 0.9 if fore else 0.58
        s = int(round(u * steps))
        root = (bottoms[s][0] + (0.0 if near else -6.0), bottoms[s][1] - 5.0)
        fx, lift_ = root[0] + (5.0 if fore else -4.0), 0.0
        if walk_ph is not None:
            pair = 0.0 if fore == near else 0.5
            sx, sy = H.gait(walk_ph * 2.0 + pair, 14.0, 3.5)
            fx, lift_ = fx + sx, -sy
        fx += (12.0 if fore else -14.0) * sink + (3.0 if fore else -3.0) * low
        foot = (fx, GROUND - 2.0 - lift_)
        knee = ((root[0] + foot[0]) / 2.0 + (-5.0 if fore else -6.0) * (1.0 - sink),
                max(root[1] + 2.0, foot[1] - 5.0 + 2.0 * sink + 1.5 * low))
        thick, thin = (8.4, 6.4) if fore else (10.0, 7.2)
        if near:
            f.limb([root, knee], thick + 2.4, H.SEPIA_INK, body=False)
            f.limb([knee, foot], thin + 2.4, H.SEPIA_INK, body=False)
            f.ellipse(foot[0] + 2.8, foot[1] + 0.4, 6.6, 3.0, H.SEPIA_INK, body=False)
        f.limb([root, knee], thick, colour)
        f.limb([knee, foot], thin, colour)
        f.ellipse(foot[0] + 2.8, foot[1] + 0.4, 5.6, 2.2, colour)
        for k in range(3):
            f.ink([(foot[0] + 3.4 + 2.0 * k, foot[1] + 0.2), (foot[0] + 5.2 + 2.4 * k, foot[1] + 1.8)], 0.7, SKIN_LIGHT if near else SKIN)

    leg(True, False)
    leg(False, False)

    # The body and the tail: one long shape.
    f.poly(tops + list(reversed(bottoms)), SKIN)
    # The pale belly, the shade under the flank and the light on the back.
    strip(0.36, 1.0, 0.7, 1.0, BELLY)
    strip(0.36, 1.0, 0.58, 0.7, SKIN_SHADE)
    strip(0.06, 0.36, 0.62, 1.0, SKIN_SHADE)
    strip(0.42, 0.98, 0.06, 0.18, SKIN_LIGHT)
    # The faint pale bands across the flanks and the tail.
    for u0 in (0.08, 0.17, 0.26, 0.35, 0.45, 0.56, 0.68, 0.8):
        strip(u0, u0 + 0.03, 0.2 if u0 > 0.4 else 0.1, 0.6 if u0 > 0.36 else 0.85, FLANK_BAND)
    # The plates of the belly: short lines across it.
    for k in range(17):
        s = int(round((0.4 + 0.035 * k) * steps))
        f.ink([at(s, 0.74), at(s, 0.98)], 0.6, BELLY_SHADE)
    # The scutes: a double crest of points on the tail and rows of bumps on
    # the back. They are part of the shape, so the outline goes round them.
    for s in range(2, steps - 1):
        u = us[s]
        x, y = tops[s]
        if u < 0.42:
            if s % 2 == 0:
                h = 2.0 + 4.0 * u
                f.poly([(x - 2.2, y + 1.0), (x, y - h), (x + 2.2, y + 1.0)], SKIN)
        elif s % 2 == 0:
            f.ellipse(x, y + 0.4, 2.6, 2.0, SKIN)
            f.ink([(x - 1.4, y + 1.2), (x + 1.4, y + 1.2)], 0.6, SKIN_SHADE)
    # Rows of rough plates on the flank.
    for row, k in ((0, 0.26), (1, 0.42)):
        for s in range(20 + row, steps - 2, 3):
            px, py = at(s, k)
            f.ellipse(px, py, 1.8, 1.3, SKIN_SHADE, body=False)

    leg(False, True)

    # The head, turned by `lift` about the neck. An open mouth lifts the
    # upper jaw too, so that the lower jaw stays off the ground.
    lift -= 12.0 * jaw
    nx, ny = centre(1.0)
    ny += 1.0
    tip = SKULL + SNOUT

    def Hd(*p: Point) -> List[Point]:
        return K.turn([(nx + x, ny + y) for x, y in p], nx, ny, lift)

    # The lower jaw turns down about its hinge, under the back of the skull.
    hinge = (-2.0, 3.0)
    jaw_ang = 30.0 * jaw

    def Jw(*p: Point) -> List[Point]:
        q = K.turn([(x, y) for x, y in p], hinge[0], hinge[1], jaw_ang)
        return Hd(*q)

    if jaw > 0.05:
        # The inside of the mouth, between the jaws.
        f.poly(Hd((-2.0, 2.0), (tip - 3.0, 1.4)) + Jw((tip - 5.0, 2.0), (-2.0, 3.0)), MOUTH)
        f.poly(Hd((-2.0, 2.0), (8.0, 2.4)) + Jw((8.0, 3.6), (-2.0, 3.0)), MOUTH_DARK, body=False)
    # The heavy lower jaw, with its pale bands.
    f.poly(Jw((-10.0, 1.0), (10.0, 2.0), (tip - 6.0, 1.6), (tip - 2.0, 2.6), (tip - 5.0, 7.0), (30.0, 11.0), (10.0, 13.4), (-4.0, 13.6), (-10.0, 8.0)), SKIN)
    for x in (2.0, 11.0, 20.0, 29.0, 38.0, 47.0):
        lo = 13.4 if x < 10.0 else (13.4 - 0.13 * (x - 10.0))
        f.poly(Jw((x, 3.6), (x + 3.6, 3.4), (x + 3.4, lo - 1.0), (x - 0.2, lo - 0.6)), JAW_BAND, body=False)
    f.ink(Jw((-4.0, 12.8), (10.0, 12.6), (30.0, 10.2), (tip - 5.0, 6.2)), 0.8, BELLY_SHADE)
    # The throat, under the head and the neck.
    f.poly(Hd((-12.0, 0.0), (-12.0, 12.0), (-2.0, 13.4), (4.0, 6.0)), SKIN)
    f.poly(Hd((-12.0, 7.0), (-12.0, 12.0), (-2.0, 13.4), (2.0, 9.0)), BELLY, body=False)

    # The skull and the upper jaw: deep at the back, broad and blunt at the
    # front.
    upper = Hd((-12.0, -15.0), (-2.0, -18.0), (8.0, -18.4), (18.0, -15.6), (SKULL, -12.0), (tip - 10.0, -9.4), (tip - 4.0, -7.6),
               (tip - 0.4, -4.0), (tip, 0.0), (tip - 2.0, 2.0), (SKULL, 2.4), (8.0, 2.6), (-12.0, 2.0))
    f.poly(upper, SKIN)
    # The light on top of the head and the shade along the lip.
    f.poly(Hd((-8.0, -15.4), (6.0, -16.6), (16.0, -14.4), (SKULL, -11.0), (tip - 8.0, -8.6), (tip - 8.0, -7.2), (SKULL, -9.0),
              (14.0, -12.0), (-8.0, -12.6)), SKIN_LIGHT, body=False)
    f.poly(Hd((-6.0, -1.0), (SKULL, -0.6), (tip - 3.0, -0.4), (tip - 3.0, 1.4), (SKULL, 2.0), (-6.0, 1.6)), SKIN_SHADE, body=False)
    # The bony ridge from the eye down the snout.
    f.ink(Hd((14.0, -14.6), (SKULL, -10.8), (tip - 12.0, -8.4)), 0.9, SKIN_SHADE)
    # The teeth.
    if jaw > 0.05:
        for x in [4.0 + 4.6 * k for k in range(12)]:
            if x < tip - 4.0:
                a, b = Hd((x, 1.6), (x + 2.0, 1.6))
                c = Hd((x + 1.0, 4.8))[0]
                f.poly([a, c, b], TEETH, body=False)
            if x < tip - 8.0:
                a, b = Jw((x + 1.0, 3.0), (x + 3.0, 3.0))
                c = Jw((x + 2.0, 0.0))[0]
                f.poly([a, c, b], TEETH, body=False)
    else:
        f.ink(Hd((-4.0, 2.4), (SKULL, 2.2), (tip - 3.0, 1.4)), 0.8, PUPIL)
        # With the jaws shut, a few teeth show over the lip.
        for x in (16.0, 30.0, 46.0):
            a, b = Hd((x, 1.8), (x + 1.8, 1.8))
            c = Hd((x + 0.9, 4.8))[0]
            f.poly([a, c, b], TEETH, body=False)
    # The nostrils on a bump at the tip of the snout.
    f.ellipse(*Hd((tip - 5.0, -7.8))[0], 3.6, 2.6, SKIN)
    f.dot(*Hd((tip - 4.0, -8.4))[0], 0.8, PUPIL)
    # The raised eye on the top of the head, under its bony ridge.
    ex, ey = Hd((8.0, -17.0))[0]
    f.ellipse(ex, ey, 5.4, 4.0, SKIN)
    f.ellipse(ex, ey + 1.2, 4.4, 1.6, SKIN_SHADE, body=False)
    if eyes == "shut":
        f.ink(Hd((5.0, -17.0), (8.0, -16.2), (11.0, -16.8)), 1.0, PUPIL)
    else:
        r = {"open": 1.8, "wide": 2.4, "narrow": 1.1}[eyes]
        f.ellipse(ex + 0.6, ey - 0.2, 2.6, r, EYE, body=False)
        f.ellipse(ex + 1.0, ey - 0.2, 0.6, min(r, 1.6), PUPIL, body=False)
    ridge = Hd((2.0, -19.0), (7.0, -22.6), (13.0, -21.8), (16.0, -18.0), (8.0, -19.6))
    f.poly(ridge, SKIN)
    f.ink(Hd((3.0, -19.4), (7.0, -21.8), (13.0, -21.0)), 0.8, SKIN_LIGHT)
    if eyes == "narrow":
        f.ink(Hd((4.0, -18.8), (12.0, -18.4)), 1.0, SKIN_SHADE)
    # The plates on the neck.
    for k in range(3):
        f.ellipse(*Hd((-12.0 + 4.6 * k, -15.6 - 0.8 * k))[0], 2.4, 1.9, SKIN)

    leg(True, True)

    if walk_ph is not None and walk_ph % 0.5 < 0.15:
        H.dust(f, nx - 70.0, GROUND - 1.0, 0.3, f"cai:walk:{i}", spread=1.0, colour=MUD)
    if anim == "attack_side":
        if lunge in (1, 2):
            # The rush of the lunge: lines over the back, behind the head.
            s = int(round(0.75 * steps))
            bx, by = tops[s]
            for k in (0.0, 1.0, 2.0):
                y = by - 6.0 - 5.0 * k
                f.ink([(bx - 30.0 + 6.0 * k, y), (bx + 4.0 - 2.0 * k, y)], 1.2, K.alpha(K.WHITE, 0.85))
        if lunge == 3:
            # The jaws shut: short lines out from the snout.
            tx, ty = Hd((tip - 4.0, 0.0))[0]
            for k in (-1.0, 0.0, 1.0):
                f.ink([(tx + 3.0, ty - 3.0 + 4.0 * k), (min(FRAME_SIZE[0] - MARGIN - 1.0, tx + 10.0), ty - 4.0 + 7.0 * k)], 1.3, K.alpha(K.WHITE, 0.95))
        if lunge in (1, 3):
            H.dust(f, nx - 20.0, GROUND - 1.0, 0.6, f"cai:lunge:{i}", spread=1.4, colour=MUD)
    if anim == "death" and 0.15 < t < 0.8:
        H.dust(f, nx - 60.0, GROUND - 1.0, min(1.0, (t - 0.15) * 2.0), f"cai:death:{i}", spread=2.4, colour=MUD)
    if alarm:
        hx, hy = Hd((8.0, -22.0))[0]
        H.alarm_mark(f, hx, max(MARGIN + 11.0, hy - 16.0))
    return f.finish(outline=H.SEPIA_INK, width=1.5, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
