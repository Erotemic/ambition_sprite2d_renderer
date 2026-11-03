"""The Soot Sprite: a ball of soot from a mill chimney of the Industrial Age.

A round ball of black soot with a fuzzy edge, two big white eyes, and an
ember deep inside it that glows when it is angry. Specks of soot float
round it and fall off it. It floats and it rushes at you.

Its windup squashes it and lights the ember; its strike is a rush with a
trail of soot behind it. A hit blows a puff of soot off it; at its death it
comes apart into a cloud of specks, and the eyes go last.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import List

from . import _art_cast_kit as K
from . import _history_modern_kit as H

TARGET_NAME = "soot_sprite"
FRAME_SIZE = (96, 96)
ROWS = K.ENEMY_ROWS

ACTOR_METADATA = K.enemy_metadata(
    TARGET_NAME, "Soot Sprite", "Blob", "Small", "Light", "Float", ["history", "industrial", "soot", "floating"],
    "A ball of soot from a mill chimney in the Industrial Age of the History dimension, with big white eyes and an "
    "ember inside. It floats and rushes at you, and leaves a trail of soot.",
)
ACTOR_METADATA["tags"] = ["enemy", "history"]

#: The outline is a smoky grey, so that a black ball reads on a dark sky.
OUTLINE = (128, 118, 128, 255)


def _fuzz(cx: float, cy: float, r: float, sx: float, sy: float, rng: random.Random, spikes: int = 30) -> list:
    """A round shape with a fuzzy edge: points that go in and out."""
    pts = []
    for k in range(spikes * 2):
        a = math.tau * k / (spikes * 2)
        rr = r * (1.12 if k % 2 == 0 else 0.92) + rng.uniform(-0.8, 0.8)
        pts.append((cx + math.cos(a) * rr * sx, cy + math.sin(a) * rr * sy))
    return pts


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    rng = random.Random(f"soot:{anim}:{i}")
    f = K.Frame(FRAME_SIZE)

    cx, cy, r = 48.0, 50.0, 13.5
    sx, sy, lean = 1.0, 1.0, 0.0
    eyes, brows, ember, fade, alarm = "open", 0.0, 0.0, 1.0, False
    trail, burst, look = 0.0, 0.0, 1.0
    blink = False
    if anim == "idle":
        cy += 2.0 * math.sin(cyc)
        sx, sy = 1.0 + 0.04 * math.sin(cyc * 2.0), 1.0 - 0.04 * math.sin(cyc * 2.0)
        blink = i == 3
        look = math.sin(cyc)
    elif anim == "walk":
        cy += 1.5 * math.sin(cyc * 2.0)
        sx, sy = 1.08, 0.94
        trail, lean = 0.6, 1.0
    elif anim == "notice":
        k = math.sin(math.pi * t)
        sx, sy = 1.0 + 0.2 * k, 1.0 + 0.2 * k
        eyes, alarm = "wide", True
    elif anim == "windup":
        sx, sy = 1.18 + 0.03 * math.sin(cyc * 2.0), 0.84
        eyes, brows, ember = "narrow", 1.0, 0.7 + 0.3 * math.sin(cyc * 2.0)
        cx -= 4.0
    elif anim == "attack_side":
        u = min(1.0, t * 1.5)
        rush = math.sin(math.pi * 0.5 * u)
        cx += -4.0 + 24.0 * rush
        sx, sy = 1.0 + 0.3 * rush * (1.0 - u * 0.5), 1.0 - 0.18 * rush
        eyes, brows, ember = "narrow", 1.0, 1.0 - 0.5 * u
        trail = 1.0
    elif anim == "hit":
        sx, sy = 1.2, 0.8
        eyes, burst = "x", 1.0 - t * 0.6
        cx -= 4.0 * math.sin(math.pi * t)
    elif anim == "death":
        eyes = "x" if t < 0.4 else "open"
        burst = 1.0
        fade = 1.0 - max(0.0, t - 0.65) / 0.35

    # The trail: smudges of soot behind it.
    if trail > 0.0:
        for k in range(5):
            u = (k + 1) / 5.0
            x = cx - r * sx - 4.0 - 7.0 * k * trail
            y = cy + rng.uniform(-3.0, 3.0)
            rr = r * (0.6 - 0.1 * k) * trail
            x = max(x, rr + 4.0)
            if rr > 0.6:
                f.ellipse(x, y, rr, rr * 0.8, K.alpha(H.SOOT_LIGHT, 0.75 - 0.12 * k), body=False)
            del u

    if anim == "death":
        # The ball comes apart: its specks fly out and drift down, and only the
        # eyes hold together a moment longer.
        whole = max(0.0, 1.0 - t * 2.2)
        if whole > 0.0:
            f.poly(_fuzz(cx, cy, r * whole + 2.0, 1.0, 1.0, rng), H.SOOT)
        for k in range(26):
            a = rng.uniform(0.0, math.tau)
            d = r * (0.3 + rng.uniform(0.2, 1.0) * (0.4 + 1.6 * t))
            x, y = cx + math.cos(a) * d, cy + math.sin(a) * d + 14.0 * t * t
            s = rng.uniform(1.0, 2.6) * (1.0 - 0.4 * t)
            f.ellipse(x, y, s + 0.6, s + 0.6, H.SOOT)
    else:
        f.poly(_fuzz(cx, cy, r, sx, sy, rng), H.SOOT)
        f.ellipse(cx - r * 0.35 * sx, cy - r * 0.4 * sy, r * 0.45 * sx, r * 0.3 * sy, K.alpha(H.SOOT_LIGHT, 0.8), body=False)

    if ember > 0.0:
        ex, ey = cx + 1.0, cy + r * 0.45 * sy
        f.ellipse(ex, ey, 4.0 * sx, 2.4 * sy, K.alpha(H.FIRE_DARK, ember), body=False)
        f.ellipse(ex, ey - 0.4, 2.4 * sx, 1.2 * sy, K.alpha(H.GASLIGHT, ember), body=False)
        f.glow(ex, ey, 6.0, K.alpha(H.FIRE, 0.6 * ember))

    # The eyes: big and white, looking where it goes.
    if not (anim == "death" and t > 0.85):
        for ox in (-4.6, 4.6):
            x, y = cx + 2.0 + ox * sx + 1.0 * lean, cy - 2.0 * sy
            if anim == "death":
                y += 10.0 * max(0.0, t - 0.4)
            if blink:
                f.ink([(x - 2.6, y), (x + 2.6, y)], 1.2, H.WHITE)
            elif eyes == "x":
                f.ink([(x - 2.0, y - 2.0), (x + 2.0, y + 2.0)], 1.2, H.WHITE)
                f.ink([(x - 2.0, y + 2.0), (x + 2.0, y - 2.0)], 1.2, H.WHITE)
            else:
                big = 1.3 if eyes == "wide" else 1.0
                ry = 2.2 if eyes == "narrow" else 3.6 * big
                f.ellipse(x, y, 3.0 * big, ry, H.WHITE, body=False)
                f.dot(x + 1.0 + 0.6 * look, y + (0.4 if eyes == "narrow" else 0.6), 1.5 * big, H.SOOT)
                f.dot(x + 0.2, y - 1.2, 0.6, H.WHITE)
            if brows > 0.0:
                inner = 1.0 if ox > 0 else -1.0
                f.ink([(x - 3.2 * inner, y - 5.0), (x + 2.4 * inner, y - 2.6)], 1.4, H.SOOT)

    # Specks that float round it, or blow off it.
    count = 6 if burst == 0.0 else 12
    for k in range(count):
        a = math.tau * k / count + cyc * 0.5 + rng.uniform(-0.2, 0.2)
        d = r + 4.0 + 3.0 * math.sin(cyc + k) + 12.0 * burst
        s = rng.uniform(0.8, 1.8)
        if anim != "death":
            f.ellipse(cx + math.cos(a) * d * sx, cy + math.sin(a) * d * sy, s, s, K.alpha(H.SOOT_LIGHT, 0.95), body=False)
    if alarm:
        H.alarm_mark(f, cx + 14.0, cy - r - 16.0)
    return H.finish(f, fade=fade, outline=OUTLINE, width=1.2)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
