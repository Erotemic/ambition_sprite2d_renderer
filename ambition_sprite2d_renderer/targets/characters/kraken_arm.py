"""The Kraken Arm: one arm of the sea monster of the old maps, in a hatch.

A huge tentacle, deep plum on its back and pale pink under, with a row of
round suckers, rises out of an open cargo hatch: a box of tarred planks
with iron corners. What is under the hatch, nobody has seen. Water drips
off it. "Here be dragons," says the map; the map was wrong about the shape.

It is slow and heavy. It walks by scooting its hatch along the deck. Its
windup rears back high over the hatch; its strike slams it down flat onto
the deck in front, with a splash. A hit makes it curl up tight; at its
death it slides back down into the hatch, and the lid falls shut.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import List

from . import _art_cast_kit as K
from . import _history_modern_kit as H
from . import _stage_kit as S

TARGET_NAME = "kraken_arm"
FRAME_SIZE = (160, 224)
ROWS = K.ENEMY_ROWS
GROUND = 219.0

ACTOR_METADATA = K.enemy_metadata(
    TARGET_NAME, "Kraken Arm", "Serpent", "Large", "Heavy", "Walk", ["history", "sail", "kraken", "tentacle"],
    "One arm of a kraken in the Age of Sail of the History dimension: a huge plum tentacle with suckers that rises "
    "out of a cargo hatch. It is slow; it rears up high and slams down onto the deck in front of it.",
)
ACTOR_METADATA["tags"] = ["enemy", "history"]

SKIN = (132, 52, 98, 255)
SKIN_DARK = (88, 30, 66, 255)
BELLY = (236, 168, 168, 255)
SUCKER = (250, 214, 206, 255)
SUCKER_DARK = (200, 120, 128, 255)
WATER = (150, 214, 220, 255)
SEGMENTS = 22
LENGTH = 168.0
HATCH_W = 34.0
HATCH_H = 22.0


def _spine(base, angles, out: float = 1.0):
    """The points of the tentacle from its base: each segment turns by its
    angle (degrees from straight up, clockwise). `out` is how much of its
    length is out of the hatch."""
    pts = [base]
    seg = LENGTH * out / SEGMENTS
    x, y = base
    for a in angles:
        r = math.radians(a)
        x, y = x + math.sin(r) * seg, y - math.cos(r) * seg
        pts.append((x, y))
    return pts


def _angles(pose: str, u: float, cyc: float) -> List[float]:
    """The angle of each segment for a pose. `u` (0..1) moves through a pose
    that changes; `cyc` is the phase of a loop."""
    out = []
    for k in range(SEGMENTS):
        s = k / (SEGMENTS - 1)
        if pose == "sway":
            # Up from the hatch in a slow S, the tip curled forward.
            a = 6.0 * math.sin(cyc + s * 3.0) + 10.0 * s + 300.0 * max(0.0, s - 0.62) ** 1.2 * (0.85 + 0.15 * math.sin(cyc))
        elif pose == "lean":
            a = 14.0 + 8.0 * math.sin(cyc + s * 3.0) + 20.0 * s + 220.0 * max(0.0, s - 0.65) ** 1.2
        elif pose == "tall":
            a = -4.0 + 4.0 * s + 200.0 * max(0.0, s - 0.75) ** 1.5 + 2.0 * math.sin(cyc * 3.0 + s * 8.0)
        elif pose == "rear":
            # Back over the hatch like a raised whip, the tip hooked forward.
            a = -6.0 - 22.0 * s + 330.0 * max(0.0, s - 0.5) ** 1.5 + 3.0 * math.sin(cyc * 2.0 + s * 5.0)
        elif pose == "slam":
            # From the rear pose over the top and down flat in front.
            rear = -6.0 - 22.0 * s + 330.0 * max(0.0, s - 0.5) ** 1.5
            down = 30.0 + 120.0 * min(1.0, s * 1.8) - 30.0 * max(0.0, s - 0.55)
            a = rear + (down - rear) * u
        elif pose == "curl":
            a = -10.0 * (1.0 - s) + 520.0 * s ** 1.6 * u
        else:
            a = 0.0
        out.append(a)
    return out


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    rng = random.Random(f"kraken:{anim}:{i}")
    f = K.Frame(FRAME_SIZE)
    flat = S.Pen(f)

    hx, hop, tilt = 42.0, 0.0, 0.0
    pose, u, out, alarm, fade, lid = "sway", 0.0, 1.0, False, 1.0, 0.0
    splash, drips = 0.0, True
    if anim == "idle":
        pose = "sway"
    elif anim == "walk":
        # The hatch scoots: it rocks up on its back edge and slides forward.
        pose = "lean"
        hop = 3.0 * max(0.0, math.sin(cyc * 2.0))
        tilt = 5.0 * math.sin(cyc * 2.0)
        hx += 3.0 * math.sin(cyc)
    elif anim == "notice":
        pose, alarm = "tall", True
    elif anim == "windup":
        pose = "rear"
        hop = 0.6 * math.sin(cyc * 2.0)
    elif anim == "attack_side":
        pose = "slam"
        u = min(1.0, (t / 0.5) ** 1.6)
        splash = max(0.0, (t - 0.45) / 0.55) if t > 0.45 else 0.0
    elif anim == "hit":
        pose, u = "curl", 0.5 + 0.5 * math.sin(math.pi * t)
        hx -= 3.0 * math.sin(math.pi * t)
    elif anim == "death":
        pose, u = "curl", min(1.0, t * 2.0) * 0.6
        out = max(0.0, 1.0 - t * 1.5)
        lid = max(0.0, min(1.0, (t - 0.55) / 0.25))
        drips = False
        fade = 1.0 - max(0.0, t - 0.85) / 0.15

    base_y = GROUND - HATCH_H - hop
    hatch_pen = S.Pen(f, (hx, GROUND), tilt)

    # The hatch: the back of its coaming, the dark hole.
    hatch_pen.poly([(hx - HATCH_W, base_y - 4.0), (hx + HATCH_W, base_y - 4.0), (hx + HATCH_W - 4.0, base_y - 9.0), (hx - HATCH_W + 4.0, base_y - 9.0)], H.OAK_DARK)
    hatch_pen.poly([(hx - HATCH_W + 4.0, base_y - 4.5), (hx + HATCH_W - 4.0, base_y - 4.5), (hx + HATCH_W - 6.0, base_y - 8.0), (hx - HATCH_W + 6.0, base_y - 8.0)], H.TAR, body=False)

    # The tentacle: how much of it is out of the hatch.
    angles = _angles(pose, u, cyc)
    base = hatch_pen.at(hx, base_y - 4.0)
    # As it slides back into the hold, less of it is out, and it thins.
    pts = _spine(base, angles, max(0.08, out))
    pts = [(min(150.0, max(10.0, x)), min(GROUND - 6.0, y)) for x, y in pts]
    widths = [(24.0 * (1.0 - k / len(pts)) ** 0.9 + 2.0) * (0.6 + 0.4 * min(1.0, out)) for k in range(len(pts))]
    left, right = H.tapered(pts, widths)
    clip_y = base[1] + 1.0

    def above(poly):
        return list(poly)

    body = above(left + right[::-1])
    f.poly(body, SKIN)
    # The pale underside: the side of the curl, with the suckers.
    under = [((a[0] * 0.62 + b[0] * 0.38), (a[1] * 0.62 + b[1] * 0.38)) for a, b in zip(left, right)]
    f.poly(above(left + under[::-1]), BELLY, body=False)
    # A dark stripe of shade along its back.
    back = [((a[0] * 0.2 + b[0] * 0.8), (a[1] * 0.2 + b[1] * 0.8)) for a, b in zip(left, right)]
    f.ink(above(back[1:-2]), 2.0, SKIN_DARK)
    for k in range(2, len(pts) - 2, 1):
        a, b = left[k], right[k]
        x, y = a[0] * 0.82 + b[0] * 0.18, a[1] * 0.82 + b[1] * 0.18
        if y > clip_y:
            continue
        r = max(0.9, widths[k] * 0.16)
        f.ellipse(x, y, r, r, SUCKER_DARK, body=False)
        f.ellipse(x - r * 0.15, y - r * 0.15, r * 0.6, r * 0.6, SUCKER, body=False)
    # A shine on its back.
    f.ink(above([((a[0] * 0.08 + b[0] * 0.92), (a[1] * 0.08 + b[1] * 0.92)) for a, b in zip(left, right)][3:10]), 1.0, K.alpha(H.WHITE, 0.4))

    if drips:
        for k in range(3):
            j = 4 + k * 5
            if j < len(pts):
                x, y = left[j]
                dy = ((t * 2.0 + k * 0.33) % 1.0) * 14.0
                f.ellipse(x, min(GROUND - 4.0, y + 3.0 + dy), 1.2, 1.8, K.alpha(WATER, 0.9), body=False)

    # The hatch: the front of its coaming, tarred planks and iron corners.
    front = [(hx - HATCH_W, GROUND - 2.0), (hx + HATCH_W, GROUND - 2.0), (hx + HATCH_W, base_y - 4.0), (hx - HATCH_W, base_y - 4.0)]
    hatch_pen.poly(front, H.OAK)
    for k in range(1, 3):
        y = base_y - 4.0 + k * (GROUND - base_y + 2.0) / 3.0
        hatch_pen.ink([(hx - HATCH_W, y), (hx + HATCH_W, y)], 1.0, H.OAK_DARK)
    hatch_pen.poly([(hx - HATCH_W, GROUND - 2.0), (hx - HATCH_W + 8.0, GROUND - 2.0), (hx - HATCH_W + 8.0, base_y - 4.0), (hx - HATCH_W, base_y - 4.0)],
                   K.alpha(H.OAK_DARK, 0.7), body=False)
    for x in (hx - HATCH_W + 1.0, hx + HATCH_W - 5.0):
        hatch_pen.poly([(x, base_y - 4.0), (x + 4.0, base_y - 4.0), (x + 4.0, GROUND - 2.0), (x, GROUND - 2.0)], H.IRON_DARK, body=False)
        for y in (base_y, GROUND - 6.0):
            hatch_pen.dot(x + 2.0, y, 0.8, H.IRON_LIGHT)
    hatch_pen.ink([(hx - HATCH_W, base_y - 4.0), (hx + HATCH_W, base_y - 4.0)], 1.4, H.ROPE)
    if lid > 0.0:
        # The lid swings shut over the hole: a board on its hinge at the back.
        a = math.radians(-90.0 + 90.0 * lid)
        hinge = (hx - HATCH_W, base_y - 6.0)
        tip = (hinge[0] + math.cos(a) * HATCH_W * 2.0, hinge[1] + math.sin(a) * HATCH_W * 2.0)
        hatch_pen.limb([hinge, tip], 5.0, H.OAK_DARK)
        hatch_pen.ink([hinge, tip], 1.0, H.OAK_LIGHT)

    if splash > 0.0:
        # The slam: water and splinters thrown up where it hits the deck.
        tipx = pts[-1][0]
        for k in range(7):
            a = math.radians(-160.0 + k * 24.0)
            d = 6.0 + 18.0 * splash
            x = min(150.0, max(10.0, tipx - 20.0 + k * 6.0 + math.cos(a) * d * 0.4))
            y = GROUND - 6.0 - math.sin(math.pi * splash) * (12.0 + 6.0 * (k % 3)) * abs(math.sin(a))
            flat.ellipse(x, y, 2.4 * (1.0 - splash * 0.5), 3.0 * (1.0 - splash * 0.5), K.alpha(WATER, 0.95))
        for k in range(3):
            x = tipx - 30.0 + k * 14.0
            f.ink([(x, GROUND - 4.0), (x - 3.0 + 6.0 * k * 0.5, GROUND - 14.0 * (1.0 - splash))], 1.4, K.alpha(H.CANVAS, 0.9))
    if alarm:
        H.alarm_mark(f, min(146.0, pts[-1][0] + 14.0), max(16.0, min(p[1] for p in pts) - 12.0))
    del rng
    return H.finish(f, fade=fade, width=1.6)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
