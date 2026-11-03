"""The Coral Crab: a crab of the Monsoon Coast that wears a reef on its back.

The houses of the Swahili coast were built of coral stone cut from the reef.
This crab took the idea the other way: its shell is a small reef of coral,
with branches of pink coral, a purple fan and a yellow tube on it. Under
the reef it is a crab: red legs, a big claw and a small one, and two eyes on
stalks.

It walks sideways, fast, as a crab does. When it sees you it lifts both
claws. Its windup holds the claws up and open; its strike is a scuttle to
the front and the big claw snapping shut. A hit knocks a piece of coral off;
at its death it falls over onto its back.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import List, Tuple

from . import _art_cast_kit as K
from . import _history_steppe_kit as H

TARGET_NAME = "coral_crab"
FRAME_SIZE = (96, 96)
ROWS = K.ENEMY_ROWS
GROUND = 92.0

ACTOR_METADATA = K.enemy_metadata(
    TARGET_NAME, "Coral Crab", "Multileg", "Small", "Light", "Walk", ["history", "monsoon", "crab", "coral", "sea"],
    "A crab of the Monsoon Coast in the History dimension with a small reef of coral for a shell. It scuttles sideways, "
    "lifts its claws, and snaps the big one shut on what is in front of it.",
)

SHELL = (218, 92, 62, 255)
SHELL_SHADE = (160, 56, 42, 255)
SHELL_LIGHT = (246, 146, 108, 255)
CLAW_TIP = (60, 34, 34, 255)
PURPLE = (172, 96, 176, 255)
PURPLE_DARK = (118, 60, 128, 255)
TUBE = (246, 200, 92, 255)
TUBE_DARK = (196, 140, 52, 255)
POLYP = (255, 244, 236, 255)

Point = Tuple[float, float]


def _claw(pen: H.ScaledPen, base: Point, tip: Point, size: float, open_: float, colour, shade) -> None:
    """A claw from `base` toward `tip`: a fat palm and two fingers, the upper
    finger opening by `open_` (0 shut, 1 wide)."""
    ang = math.atan2(tip[1] - base[1], tip[0] - base[0])
    ux, uy = math.cos(ang), math.sin(ang)
    nx, ny = uy, -ux

    def at(a: float, b: float) -> Point:
        return (base[0] + ux * a + nx * b, base[1] + uy * a + ny * b)

    palm = [at(0.0, -4.0 * size), at(9.0 * size, -5.6 * size), at(13.0 * size, -3.0 * size), at(13.0 * size, 2.0 * size), at(8.0 * size, 5.4 * size),
            at(0.0, 4.0 * size)]
    pen.poly(palm, colour)
    pen.poly([at(0.0, -4.0 * size), at(9.0 * size, -5.6 * size), at(13.0 * size, -3.0 * size), at(8.0 * size, -1.0 * size), at(0.0, -1.6 * size)],
             shade, body=False)
    # The fixed finger, below; the moving finger, above, that opens.
    lower = [at(12.0 * size, -1.0 * size), at(20.0 * size, -1.6 * size), at(21.0 * size, 0.6 * size), at(12.0 * size, 2.6 * size)]
    pen.poly(lower, colour)
    pen.poly([at(17.0 * size, -1.4 * size), at(21.0 * size, -1.6 * size), at(21.0 * size, 0.6 * size), at(17.0 * size, 1.2 * size)], CLAW_TIP, body=False)
    gap = 26.0 * open_
    piv = at(12.0 * size, 3.4 * size)
    upper = [at(12.0 * size, 1.4 * size), at(19.0 * size, 2.6 * size), at(21.4 * size, 0.6 * size), at(20.0 * size, 4.0 * size), at(12.0 * size, 5.0 * size)]
    upper = K.turn(upper, piv[0], piv[1], -gap if ux >= 0 else gap)
    pen.poly(upper, colour)
    pen.poly(upper[1:4], CLAW_TIP, body=False)
    pen.dot(*at(6.0 * size, -0.6 * size), 0.8 * size, K.alpha(SHELL_LIGHT, 0.9))


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    rng = random.Random("coral_crab")
    f = K.Frame(FRAME_SIZE)
    dx, dy, tilt, scuttle = 0.0, 0.0, 0.0, None
    big_up, small_up, big_open, small_open, eyes, stalks = 0.0, 0.0, 0.2, 0.2, "open", 0.0
    alarm, chips, flip, fade, snap = False, 0, 0.0, 1.0, 0.0
    if anim == "idle":
        dy = 0.5 * math.sin(cyc)
        big_open = 0.15 + 0.25 * max(0.0, math.sin(cyc))
        small_open = 0.15 + 0.25 * max(0.0, math.sin(cyc + 2.0))
        stalks = 1.0 * math.sin(cyc + 1.0)
    elif anim == "walk":
        scuttle = t
        dy = -1.4 * abs(math.sin(cyc * 2.0))
        dx = 2.0 * math.sin(cyc)
        tilt = 3.0 * math.sin(cyc * 2.0)
        stalks = 1.5 * math.sin(cyc * 2.0)
    elif anim == "notice":
        k = math.sin(math.pi * min(1.0, t * 1.3))
        big_up, small_up, big_open, small_open, eyes, alarm, stalks = k, k, 0.6 * k, 0.6 * k, "wide", True, 3.0 * k
        dy = -2.0 * k
    elif anim == "windup":
        big_up, small_up = 1.0, 0.8
        big_open = 0.8 + 0.15 * math.sin(cyc * 2.0)
        small_open = 0.6 + 0.15 * math.sin(cyc * 2.0 + 1.0)
        dy, dx, tilt, eyes = -3.0, -4.0, -4.0, "narrow"
    elif anim == "attack_side":
        # The scuttle to the front (0..2), the snap (2), and back.
        u = min(1.0, t / 0.5)
        back = max(0.0, (t - 0.5) / 0.5)
        dx = -6.0 + 8.0 * math.sin(math.pi * 0.5 * u) - 2.0 * back
        big_up = 1.0 - 0.9 * u
        big_open = 0.9 if i < 2 else 0.0
        small_up, small_open, eyes, tilt = 0.6, 0.4, "narrow", 4.0 * u * (1.0 - back)
        scuttle = t * 2.0
        snap = 1.0 if i in (2, 3) else 0.0
    elif anim == "hit":
        k = math.sin(math.pi * (i + 1) / (n + 1))
        dx, tilt, eyes, big_open, small_open, stalks = -5.0 * k, -10.0 * k, "shut", 0.6, 0.6, -3.0
        chips = 3
    elif anim == "death":
        flip = min(1.0, t * 1.5)
        eyes, big_open, small_open = "x", 0.5, 0.5
        fade = 1.0 - max(0.0, t - 0.7) / 0.3

    cx, cy = 44.0 + dx, GROUND - 27.0 + dy
    # At its death it rolls over onto its back, about the middle of its shell.
    rot = tilt + 180.0 * flip
    shift = (4.0 * flip, -16.0 * math.sin(math.pi * flip) - 6.0 * flip)
    pen = H.ScaledPen(f, (cx, cy), rot, shift)
    flat = H.ScaledPen(f)

    # The legs: four on each side, thin and jointed, down to the ground.
    def legs(side: float, colour) -> None:
        # From the back leg to the front one, each arched up and out at its
        # knee and down to the ground, so that they fan out.
        for k in (3, 2, 1, 0):
            root = (cx + side * (9.0 + k * 2.0), cy + 3.0)
            spread = 15.0 + k * 6.5
            ph = 0.0 if scuttle is None else (scuttle + k * 0.25 + (0.5 if side > 0 else 0.0)) % 1.0
            lift = 4.0 * max(0.0, math.sin(math.tau * ph)) if scuttle is not None else 0.0
            step = 2.6 * math.cos(math.tau * ph) if scuttle is not None else 0.0
            knee = (cx + side * (spread - 3.0), cy - 7.0 + k * 1.4 - lift * 0.6)
            foot = (cx + side * (spread + 1.0) + step, cy + 23.0 - lift)
            if flip:
                # Folded in, and kicking.
                knee = (cx + side * (spread * 0.62), cy - 2.0 + k * 1.6)
                foot = (cx + side * (spread * 0.5) + 3.0 * math.sin(cyc * 3.0 + k), cy + 8.0 - 1.6 * k)
            shade = colour if k % 2 else K.shade(colour, 1.2)
            pen.limb([root, knee], 2.6, shade)
            pen.limb([knee, foot], 1.9, shade)
            pen.dot(foot[0], foot[1], 0.8, CLAW_TIP)

    legs(-1.0, SHELL_SHADE)
    legs(1.0, SHELL_SHADE)

    # The small claw, behind, at the back side.
    sbase = (cx - 16.0, cy + 2.0)
    stip = (sbase[0] - 10.0, sbase[1] - 4.0 - 14.0 * small_up)
    selbow = (sbase[0] - 7.0, sbase[1] + 2.0 - 6.0 * small_up)
    pen.limb([sbase, selbow], 4.0, SHELL)
    _claw(pen, selbow, stip, 0.62, small_open, SHELL, SHELL_SHADE)

    # The body under the reef: a broad shell, lighter at its front.
    pen.ellipse(cx, cy + 2.0, 18.0, 10.0, SHELL)
    pen.ellipse(cx + 2.0, cy + 6.0, 15.0, 5.0, SHELL_SHADE, body=False)
    pen.poly([(cx - 8.0, cy + 10.0), (cx + 10.0, cy + 10.0), (cx + 6.0, cy + 12.6), (cx - 4.0, cy + 12.6)], SHELL_LIGHT, body=False)

    # The reef on its back: a brain coral dome, branches of pink coral, a
    # purple fan, a yellow tube, and polyps.
    pen.ellipse(cx - 4.0, cy - 5.0, 15.0, 8.0, H.CORAL)
    for k in range(4):
        y0 = cy - 9.0 + k * 2.6
        pts = [(cx - 15.0 + k * 1.4, y0)]
        for s in range(6):
            pts.append((cx - 13.0 + k * 1.4 + s * 4.4, y0 + (1.0 if s % 2 else -1.0)))
        pen.ink(pts, 0.7, H.CORAL_DARK)
    # The fan, at the back.
    fan_sway = 1.4 * math.sin(cyc)
    fan = [(cx - 14.0, cy - 6.0), (cx - 24.0 + fan_sway, cy - 16.0), (cx - 20.0 + fan_sway, cy - 24.0), (cx - 12.0 + fan_sway * 0.5, cy - 22.0),
           (cx - 8.0, cy - 9.0)]
    pen.poly(fan, PURPLE)
    for k in range(4):
        a = (cx - 22.0 + k * 3.4 + fan_sway * 0.8, cy - 22.0 + abs(k - 1.5) * 1.6)
        pen.ink([(cx - 12.0, cy - 7.0), a], 0.6, PURPLE_DARK)
    pen.ink([(cx - 20.0 + fan_sway, cy - 16.0), (cx - 13.0 + fan_sway * 0.5, cy - 18.0)], 0.5, PURPLE_DARK)
    # Branches of pink coral, round at their tips.
    branches = [[(cx - 2.0, cy - 10.0), (cx - 3.0, cy - 18.0), (cx - 7.0, cy - 23.0)], [(cx - 3.0, cy - 17.0), (cx + 1.0, cy - 24.0)],
                [(cx + 4.0, cy - 9.0), (cx + 6.0, cy - 16.0), (cx + 4.0, cy - 20.0)], [(cx + 6.0, cy - 15.0), (cx + 10.0, cy - 19.0)]]
    for br in branches:
        pen.limb(br, 3.4, H.CORAL_LIGHT)
        pen.dot(br[-1][0], br[-1][1], 1.0, POLYP)
    # The yellow tube, at the front of the reef.
    pen.limb([(cx - 8.0, cy - 8.0), (cx - 9.0, cy - 16.0)], 4.6, TUBE)
    pen.ellipse(cx - 9.0, cy - 16.0, 2.4, 1.2, TUBE_DARK, body=False)
    for k in range(int(5)):
        px, py = cx - 12.0 + rng.uniform(0.0, 20.0), cy - 6.0 + rng.uniform(-2.0, 3.0)
        pen.dot(px, py, 0.8, POLYP)

    # The eyes on their stalks, looking to the front.
    for k, ex0 in enumerate((cx + 10.0, cx + 15.0)):
        top = (ex0 + 1.0 + stalks * 0.3, cy - 9.0 - 3.0 * (k == 1) - abs(stalks) * 0.4 + (4.0 if eyes == "shut" else 0.0))
        pen.limb([(ex0, cy - 1.0), top], 2.0, SHELL)
        r = 3.0 if eyes == "wide" else 2.5
        pen.ellipse(top[0], top[1], r, r, K.WHITE)
        if eyes == "shut":
            pen.ink([(top[0] - 1.6, top[1]), (top[0] + 1.6, top[1])], 0.9)
        elif eyes == "x":
            pen.ink([(top[0] - 1.4, top[1] - 1.4), (top[0] + 1.4, top[1] + 1.4)], 0.8)
            pen.ink([(top[0] - 1.4, top[1] + 1.4), (top[0] + 1.4, top[1] - 1.4)], 0.8)
        else:
            pen.dot(top[0] + 0.9, top[1] + (0.0 if eyes != "narrow" else 0.6), 1.4, H.SEPIA_INK)
            if eyes == "narrow":
                pen.ink([(top[0] - 2.4, top[1] - 2.4), (top[0] + 2.4, top[1] - 1.0)], 0.8)
    # The mouth, a little line under the eyes.
    pen.ink([(cx + 12.0, cy + 4.0), (cx + 15.0, cy + 4.6), (cx + 18.0, cy + 4.0)], 0.8, SHELL_SHADE)

    # The big claw, at the front.
    bbase = (cx + 17.0, cy + 2.0)
    belbow = (bbase[0] + 8.0, bbase[1] + 1.0 - 8.0 * big_up)
    btip = (belbow[0] + 12.0 - 6.0 * big_up, belbow[1] - 2.0 - 12.0 * big_up)
    pen.limb([bbase, belbow], 5.0, SHELL)
    _claw(pen, belbow, btip, 1.12, big_open, SHELL_LIGHT, SHELL)

    if snap:
        tx, ty = pen.at(btip[0] + 12.0, btip[1])
        for k in range(4):
            a = math.radians(-60.0 + k * 40.0)
            f.glow_line([(tx + math.cos(a) * 3.0, ty + math.sin(a) * 3.0), (min(92.0, tx + math.cos(a) * 8.0), ty + math.sin(a) * 8.0)], 1.4,
                        K.alpha(K.WHITE, 0.9))
    for k in range(chips):
        # Bits of coral that fly off it.
        cr = random.Random(f"chip:{i}:{k}")
        px, py = cx - 6.0 + cr.uniform(-12.0, 12.0) - 4.0 * i, cy - 18.0 - cr.uniform(0.0, 10.0) - 3.0 * i
        flat.poly(K.turn([(px - 2.0, py - 1.4), (px + 2.0, py - 1.6), (px + 1.4, py + 1.6), (px - 1.6, py + 1.4)], px, py, cr.uniform(0, 90)),
                  H.CORAL_LIGHT if k % 2 else PURPLE)
    if alarm:
        H.alarm_mark(f, cx + 22.0, max(14.0, cy - 34.0))
    return f.finish(outline=H.SEPIA_INK, width=1.2, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
