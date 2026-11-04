"""The Gharial of the History dimension: the fish-eating crocodile of Bengal's rivers.

The gharial (Gavialis gangeticus) lives in the deep, fast rivers of the
north of South Asia: the Ganges, the Brahmaputra and their branches. It is
a crocodile, but it eats fish. Its snout is very long and thin, with many
small sharp teeth that fit between each other. An adult male has a round
knob (the ghara, a word for a clay pot) at the tip of the snout. Its skin
is olive-grey with dark bands, its belly is pale, its legs are weak and
its body is low and long. Its eyes sit high on the top of its head.

At rest it lies low and breathes slowly. On land it slides on its belly
and pushes with its short legs. When it sees you it lifts its head. Its
windup draws the head back and opens the jaws a little. Its strike is a
snap to the side, as a gharial catches a fish: it lunges, the open snout
sweeps round, and the jaws shut. A hit makes it shut its eyes and flinch;
at its death it sinks flat on the ground and fades.

The frame is 320 by 96 px: the body box is 120 by 28 world units, and the
gharial faces right.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Tuple

from . import _art_cast_kit as K
from . import _history_africa_kit as H

TARGET_NAME = "gharial"
FRAME_SIZE = (320, 96)
ROWS = K.ENEMY_ROWS
#: Nothing is drawn nearer the edge of the frame than this.
MARGIN = 6.0
GROUND = 88.0
#: The gharial is drawn at its size in the frame.
SIZE = 1.0
PIVOT = (160.0, GROUND)

ACTOR_METADATA = K.enemy_metadata(
    TARGET_NAME, "Gharial", "Quadruped", "Standard", "Heavy", "Walk", ["crocodilian", "gharial", "slide", "snap"],
    "The gharial, the fish-eating crocodile of the Ganges and the Brahmaputra, of the History dimension's Bengal rooms: "
    "low and long and olive-grey, with a very long thin snout and a round knob at its tip. It slides along on its belly, "
    "draws its head back, then lunges and snaps its snout to the side.",
)
ACTOR_METADATA["tags"] = ["enemy", "history", "bengal"]

Point = Tuple[float, float]

SKIN = (114, 122, 94, 255)
SKIN_SHADE = (84, 92, 72, 255)
SKIN_LIGHT = (152, 158, 124, 255)
BAND = (72, 78, 60, 255)
BELLY = (206, 200, 162, 255)
BELLY_SHADE = (170, 164, 128, 255)
GHARA = (100, 88, 70, 255)
GHARA_LIGHT = (138, 124, 100, 255)
EYE = (214, 196, 96, 255)
PUPIL = (30, 26, 20, 255)
MOUTH = (196, 126, 112, 255)
MOUTH_DARK = (140, 76, 70, 255)
TEETH = (246, 240, 222, 255)
MUD = (150, 130, 96, 255)
#: The tail tip and the neck, on the body's long axis (frame x).
TAIL_X = 18.0
NECK_X = 200.0
#: The length of the head behind the snout, and of the snout.
SKULL = 28.0
SNOUT = 58.0
#: The height of the body over its centre line (`top`) and under it
#: (`bottom`), from the tail tip (0) to the neck (1).
PROFILE = [(0.0, 2.0, 2.0), (0.2, 4.5, 3.5), (0.45, 9.0, 7.0), (0.62, 13.0, 11.0), (0.88, 13.0, 11.0), (1.0, 10.0, 8.5)]


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
    # `yaw` turns the snout to the side, so that it looks shorter; `sink`
    # lowers the body to the ground; `sway` moves the tail.
    dx, lift, jaw, yaw, sink, sway, breathe = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    eyes, fade, alarm, walk_ph, snap = "open", 1.0, False, None, 0
    if anim == "idle":
        # It lies low and breathes; the tail stirs.
        breathe = math.sin(cyc)
        sway = 0.4 * math.sin(cyc + 0.8)
        lift = -1.5 * math.sin(cyc - 0.5)
        eyes = "shut" if i == 3 else "open"
    elif anim == "walk":
        # It slides on its belly. The legs push in diagonal pairs and the
        # body surges a little on each push.
        walk_ph = t
        dx = 1.5 * math.sin(cyc * 2.0)
        sway = math.sin(cyc * 2.0)
        lift = -1.0 * math.sin(cyc * 2.0 + 1.0)
    elif anim == "notice":
        # It lifts its head and looks.
        k = math.sin(math.pi * min(1.0, t * 1.3))
        lift, eyes, alarm, sway = -12.0 * k, "wide", True, 0.6 * k
    elif anim == "windup":
        # It draws its head back and opens its jaws a little.
        dx = -6.0 + 1.5 * math.sin(cyc)
        lift = -6.0 - 2.0 * math.sin(cyc)
        jaw = 0.3 + 0.1 * math.sin(cyc * 2.0)
        sway, eyes = 1.0, "narrow"
    elif anim == "attack_side":
        # The snap, as key frames: dx, lift, jaw, yaw. The snout opens, the
        # head lunges, the snout sweeps to the side and the jaws shut.
        table = [
            (-6.0, -7.0, 0.6, 0.0),
            (8.0, -4.0, 1.0, 0.0),
            (14.0, -2.0, 1.0, 0.35),
            (14.0, 0.0, 0.0, 0.5),
            (8.0, -2.0, 0.15, 0.2),
            (2.0, -1.0, 0.0, 0.0),
        ]
        dx, lift, jaw, yaw = table[i]
        eyes, sway, snap = "narrow", 1.0 - 0.3 * i, i
    elif anim == "hit":
        k = math.sin(math.pi * (i + 1) / (n + 1))
        dx, lift, jaw, eyes, sway = -7.0 * k, 5.0 * k, 0.3 * k, "shut", -0.8 * k
    elif anim == "death":
        # It sinks flat on the ground, the head comes down, and it fades.
        u = min(1.0, t / 0.6)
        sink = u * u * (3.0 - 2.0 * u)
        lift, eyes = 4.0 * sink, "shut"
        fade = 1.0 - max(0.0, t - 0.7) / 0.3

    # The centre line of the body, from the tail tip to the neck.
    def centre(u: float) -> Point:
        x = TAIL_X + (NECK_X - TAIL_X) * u + dx * u
        k = min(1.0, u / 0.55)
        y = GROUND - 9.0 - 13.0 * (k * k * (3.0 - 2.0 * k)) + 6.0 * sink * k
        y += 2.5 * sway * (1.0 - u) ** 2 - 0.4 * breathe * k
        return x, y

    steps = 44
    us = [s / steps for s in range(steps + 1)]
    tops, bottoms = [], []
    for u in us:
        x, y = centre(u)
        top, bottom = _profile(u)
        top += 0.4 * breathe * (u > 0.5)
        bottom = bottom - 3.0 * sink * (u > 0.4)
        tops.append((x, y - top))
        bottoms.append((x, min(GROUND - 1.0, y + bottom)))

    def strip(u0: float, u1: float, k0: float, k1: float, colour) -> None:
        """A band of the body from `u0` to `u1` along it, and from `k0` to
        `k1` of the way from its top (0) to its bottom (1)."""
        idx = [s for s, u in enumerate(us) if u0 <= u <= u1]
        if len(idx) < 2:
            return
        def at(s: int, k: float) -> Point:
            (xt, yt), (xb, yb) = tops[s], bottoms[s]
            return xt + (xb - xt) * k, yt + (yb - yt) * k
        f.poly([at(s, k0) for s in idx] + [at(s, k1) for s in reversed(idx)], colour, body=False)

    def leg(fore: bool, near: bool) -> None:
        """A short splayed leg. On land the gharial pushes with them."""
        colour = SKIN if near else SKIN_SHADE
        u = 0.9 if fore else 0.58
        s = int(round(u * steps))
        root = (bottoms[s][0] + (0.0 if near else -5.0), bottoms[s][1] - 4.0)
        fx, lift_ = root[0] + (5.0 if fore else -4.0), 0.0
        if walk_ph is not None:
            pair = 0.0 if fore == near else 0.5
            sx, sy = H.gait(walk_ph * 2.0 + pair, 12.0, 3.5)
            fx, lift_ = fx + sx, -sy
        fx += (10.0 if fore else -12.0) * sink
        foot = (fx, GROUND - 2.0 - lift_)
        knee = ((root[0] + foot[0]) / 2.0 + (-4.0 if fore else -5.0) * (1.0 - sink), max(root[1] + 2.0, foot[1] - 5.0 + 2.0 * sink))
        f.limb([root, knee], 8.0 if not fore else 6.6, colour)
        f.limb([knee, foot], 5.4 if not fore else 4.8, colour)
        f.ellipse(foot[0] + 2.4, foot[1] + 0.6, 4.8, 1.8, colour)
        for k in range(3):
            f.ink([(foot[0] + 3.0 + 1.8 * k, foot[1] + 0.2), (foot[0] + 4.6 + 2.2 * k, foot[1] + 1.6)], 0.6, SKIN_SHADE if near else BAND)

    leg(True, False)
    leg(False, False)

    # The body and the tail: one long shape.
    f.poly(tops + list(reversed(bottoms)), SKIN)
    # The pale belly, the shade under the flank and the light on the back.
    strip(0.35, 1.0, 0.62, 1.0, BELLY)
    strip(0.35, 1.0, 0.52, 0.62, SKIN_SHADE)
    strip(0.08, 0.35, 0.6, 1.0, SKIN_SHADE)
    strip(0.45, 0.98, 0.08, 0.22, SKIN_LIGHT)
    # The dark bands across the tail and the back.
    for u0 in (0.06, 0.15, 0.24, 0.33, 0.42, 0.53, 0.66, 0.79):
        strip(u0, u0 + 0.045, 0.0, 0.55 if u0 > 0.35 else 0.85, BAND)
    # The plates of the belly: short lines across it.
    for u in [0.4 + 0.04 * k for k in range(15)]:
        s = int(round(u * steps))
        (xt, yt), (xb, yb) = tops[s], bottoms[s]
        f.ink([(xt + (xb - xt) * 0.66, yt + (yb - yt) * 0.66), (xb, yb - 0.6)], 0.6, BELLY_SHADE)
    # The scutes: a crest of points on the tail and rows of bumps on the
    # back. They are part of the shape, so the outline goes round them.
    for s in range(2, steps - 1):
        u = us[s]
        x, y = tops[s]
        if u < 0.42:
            if s % 2 == 0:
                h = 2.0 + 3.0 * u
                f.poly([(x - 2.0, y + 1.0), (x, y - h), (x + 2.0, y + 1.0)], SKIN)
        elif s % 2 == 0:
            f.ellipse(x, y + 0.4, 2.3, 1.7, SKIN)
            f.ink([(x - 1.2, y + 1.0), (x + 1.2, y + 1.0)], 0.6, SKIN_SHADE)
    # Rows of small plates on the flank.
    for row, k in ((0, 0.28), (1, 0.42)):
        for s in range(18 + row, steps - 2, 3):
            (xt, yt), (xb, yb) = tops[s], bottoms[s]
            px, py = xt + (xb - xt) * k, yt + (yb - yt) * k
            f.ellipse(px, py, 1.6, 1.2, SKIN_SHADE, body=False)

    leg(False, True)

    # The head, turned by `lift` about the neck. An open mouth lifts the
    # upper jaw too, so that the lower jaw stays off the ground.
    lift -= 9.0 * jaw
    nx, ny = centre(1.0)
    ny += 1.0
    snout = SNOUT * (1.0 - 0.32 * yaw)

    def Hd(*p: Point) -> List[Point]:
        return K.turn([(nx + x, ny + y) for x, y in p], nx, ny, lift)

    tip = SKULL + snout
    # The lower jaw turns down about its hinge.
    hinge = (16.0, 3.0)
    jaw_ang = 14.0 * jaw

    def Jw(*p: Point) -> List[Point]:
        q = K.turn([(hinge[0] + x, hinge[1] + y) for x, y in p], hinge[0], hinge[1], jaw_ang)
        return Hd(*q)

    lower = Jw((-6.0, -1.0), (12.0, -2.0), (tip - 16.0, -2.0), (tip - 16.0, 0.6), (12.0, 2.6), (-4.0, 6.0))
    if jaw > 0.05:
        # The inside of the mouth, between the jaws.
        f.poly([Hd((10.0, 1.0))[0], Hd((tip - 4.0, 0.6))[0], Jw((tip - 18.0, -1.8))[0], Jw((-2.0, -1.0))[0]], MOUTH)
        f.ink([Hd((14.0, 1.6))[0], Jw((tip - 24.0, -0.8))[0]], 0.8, MOUTH_DARK)
    f.poly(lower, SKIN)
    f.poly(Jw((-4.0, 2.0), (12.0, 0.6), (tip - 18.0, -0.6), (tip - 18.0, 0.4), (12.0, 2.4), (-4.0, 5.4)), BELLY, body=False)
    # The throat, under the head and the neck.
    f.poly(Hd((-8.0, 2.0), (-8.0, 9.0), (6.0, 8.0), (14.0, 4.0)), SKIN)
    f.poly(Hd((-8.0, 5.0), (-8.0, 9.0), (6.0, 8.0), (12.0, 5.0)), BELLY, body=False)

    # The skull and the upper jaw.
    upper = Hd((-8.0, -9.0), (2.0, -10.0), (10.0, -9.6), (20.0, -7.0), (SKULL, -4.4), (tip - 6.0, -3.2), (tip - 1.0, -2.6),
               (tip, 0.0), (tip - 2.0, 1.2), (SKULL, 1.4), (12.0, 2.6), (-8.0, 3.0))
    f.poly(upper, SKIN)
    f.poly(Hd((-6.0, -8.6), (8.0, -8.8), (18.0, -6.4), (SKULL, -3.8), (tip - 8.0, -2.8), (tip - 8.0, -1.8), (SKULL, -2.6), (12.0, -5.6), (-6.0, -6.6)),
           SKIN_LIGHT, body=False)
    f.poly(Hd((2.0, -1.0), (SKULL, -0.4), (tip - 4.0, 0.0), (tip - 4.0, 1.0), (SKULL, 1.2), (2.0, 2.4)), SKIN_SHADE, body=False)
    # Dark bands across the snout.
    for k in (0.25, 0.5, 0.72):
        x = SKULL + snout * k
        f.poly(Hd((x, -3.4 + 0.6 * k), (x + 3.0, -3.3 + 0.6 * k), (x + 3.0, -1.4), (x, -1.4)), BAND, body=False)
    # The teeth: small and many, fitting between each other.
    if jaw > 0.05:
        x = 14.0
        while x < tip - 6.0:
            a, b = Hd((x, 1.0), (x + 1.4, 1.0))
            c = Hd((x + 0.7, 3.4))[0]
            f.poly([a, c, b], TEETH, body=False)
            if x < tip - 20.0:
                a, b = Jw((x - 2.0, -2.0), (x - 0.6, -2.0))
                c = Jw((x - 1.3, -4.2))[0]
                f.poly([a, c, b], TEETH, body=False)
            x += 3.4
    else:
        f.ink(Hd((10.0, 1.6), (tip - 3.0, 0.8)), 0.7, PUPIL)
        x = 16.0
        while x < tip - 6.0:
            up = (int(x) // 3) % 2 == 0
            p = Hd((x, 1.2))[0]
            q = Hd((x + 0.6, -0.8 if up else 3.0))[0]
            f.ink([p, q], 0.7, TEETH)
            x += 3.0
    # The ghara: the round knob at the tip of the snout, with the nostrils.
    gx, gy = Hd((tip - 3.0, -3.6))[0]
    f.ellipse(gx, gy, 5.6, 4.6, GHARA)
    f.ellipse(gx - 1.2, gy - 1.6, 2.6, 1.6, GHARA_LIGHT, body=False)
    f.dot(*Hd((tip - 1.4, -4.6))[0], 0.7, PUPIL)
    # The raised eye on the top of the head.
    ex, ey = Hd((6.0, -10.0))[0]
    f.ellipse(ex, ey, 5.0, 3.6, SKIN)
    f.ellipse(ex, ey + 1.0, 4.0, 1.6, SKIN_SHADE, body=False)
    if eyes == "shut":
        f.ink(Hd((3.2, -10.6), (6.0, -9.8), (8.8, -10.4)), 1.0, PUPIL)
    else:
        r = {"open": 1.8, "wide": 2.4, "narrow": 1.1}[eyes]
        f.ellipse(ex + 0.6, ey - 0.4, 2.4, r, EYE, body=False)
        f.ellipse(ex + 1.0, ey - 0.4, 0.6, min(r, 1.6), PUPIL, body=False)
        if eyes == "narrow":
            f.ink(Hd((3.0, -12.6), (9.0, -11.6)), 1.0, BAND)
    # The plates on the neck.
    for k in range(3):
        f.ellipse(*Hd((-6.0 + 4.0 * k, -9.4))[0], 2.0, 1.5, SKIN)

    leg(True, True)

    if walk_ph is not None and walk_ph % 0.5 < 0.15:
        H.dust(f, nx - 70.0, GROUND - 1.0, 0.3, f"gha:walk:{i}", spread=1.0, colour=MUD)
    if anim == "attack_side":
        if snap in (1, 2):
            # The sweep of the snout: arcs round its tip.
            tx, ty = Hd((tip, -1.0))[0]
            for k in (0.0, 1.0):
                r = 9.0 + 5.0 * k
                pts = [(tx - 6.0 + r * math.cos(a) * 0.5, ty + r * math.sin(a)) for a in (math.radians(d) for d in range(-70, 71, 14))]
                pts = [(min(FRAME_SIZE[0] - MARGIN - 1.0, x), max(MARGIN + 1.0, y)) for x, y in pts]
                f.ink(pts, 1.1, K.alpha(K.WHITE, 0.8))
        if snap == 3:
            # The snap: short lines out from the shut jaws.
            tx, ty = Hd((tip - 10.0, 0.0))[0]
            for k in (-1.0, 0.0, 1.0):
                f.ink([(tx + 2.0, ty - 5.0 + 4.0 * k), (min(FRAME_SIZE[0] - MARGIN - 1.0, tx + 8.0), ty - 8.0 + 7.0 * k)], 1.3, K.alpha(K.WHITE, 0.95))
        if snap in (1, 3):
            H.dust(f, nx - 10.0, GROUND - 1.0, 0.5, f"gha:snap:{i}", spread=1.2, colour=MUD)
    if anim == "death" and 0.15 < t < 0.8:
        H.dust(f, nx - 60.0, GROUND - 1.0, min(1.0, (t - 0.15) * 2.0), f"gha:death:{i}", spread=2.4, colour=MUD)
    if alarm:
        hx, hy = Hd((8.0, -12.0))[0]
        H.alarm_mark(f, hx, max(MARGIN + 11.0, hy - 16.0))
    return f.finish(outline=H.SEPIA_INK, width=1.5, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
