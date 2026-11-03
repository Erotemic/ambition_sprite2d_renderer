"""The Red Herring: a fish of the Story Stacks that swims through the air.

A bright red fish, too red and too obvious to trust: a big round eye that
looks right at you, a pale belly, red fins, and scales drawn on in rows. A
glint flashes on it now and then, as if it wants you to look. It is the
false clue of every mystery, and it knows it.

It swims in the air: its body bends in a wave from its nose to its tail.
When it sees you its fins flare. Its windup bends it back into a curve, as
a fish does before it darts; its strike is the dart, mouth first. A hit
bends it the other way and knocks scales off it. At its death it turns
belly up and floats away, and fades.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import List, Tuple

from . import _art_cast_kit as K

TARGET_NAME = "red_herring"
FRAME_SIZE = (96, 96)
ROWS = K.ENEMY_ROWS

ACTOR_METADATA = K.enemy_metadata(
    TARGET_NAME, "Red Herring", "Flyer", "Small", "Light", "Float", ["fish", "floating", "decoy"],
    "A bright red fish from the Story Stacks of the Art dimension that swims through the air, too obvious to trust. It "
    "floats, bends back into a curve, and darts at you mouth first.",
)

RED: K.RGBA = (230, 48, 50, 255)
RED_DARK: K.RGBA = (150, 22, 38, 255)
RED_LIGHT: K.RGBA = (255, 120, 104, 255)
BELLY: K.RGBA = (255, 220, 196, 255)
IRIS: K.RGBA = (255, 210, 50, 255)

#: The length of the body from the nose to the root of the tail, and its
#: half height at its deepest.
LENGTH = 54.0
DEPTH = 15.0


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    rng = random.Random(f"herring:{anim}:{i}")
    f = K.Frame(FRAME_SIZE)
    cx, cy = 46.0, 46.0
    wave, bend, lean, sy, stretch = 1.5, 0.0, 0.0, 1.0, 1.0
    eye, mouth, flare, fade, glint, alarm = "open", 0.15, 0.0, 1.0, 0.0, False
    if anim == "idle":
        cy += 2.5 * math.sin(cyc)
        glint = max(0.0, math.sin(cyc * 1.0 - 0.5)) ** 3
    elif anim == "walk":
        wave, lean = 4.5, 4.0
        cy += 1.5 * math.sin(cyc * 2.0)
    elif anim == "notice":
        k = math.sin(math.pi * t)
        stretch, flare, eye, alarm, glint = 1.0 + 0.08 * k, 1.0, "wide", True, k
        cy -= 4.0 * k
    elif anim == "windup":
        bend, eye, mouth, flare = 1.0, "narrow", 0.4, 0.7
        cx -= 6.0
        cy += 0.8 * math.sin(cyc * 4.0)
        wave = 0.8
    elif anim == "attack_side":
        strike = math.sin(math.pi * min(1.0, t * 1.5))
        cx += 10.0 * strike - 4.0 * (1.0 - strike)
        stretch, mouth, eye, bend, wave = 1.0 + 0.1 * strike, 0.3 + 0.7 * strike, "narrow", 0.6 * (1.0 - strike), 2.0
    elif anim == "hit":
        k = math.sin(math.pi * t)
        bend, eye, mouth, lean = -0.9 * k - 0.2, "x", 0.6, -10.0 * k
        cx -= 4.0 * k
    elif anim == "death":
        # It turns belly up: its height goes through zero to minus one.
        sy = math.cos(math.pi * min(1.0, t * 1.8))
        cy -= 14.0 * t
        eye, mouth, wave, lean = "x", 0.5, 0.0, 8.0 * t
        fade = 1.0 - max(0.0, t - 0.55) / 0.45

    length = LENGTH * stretch

    def spine(u: float) -> Tuple[float, float]:
        """The middle line of the body: `u` 0 at the nose, 1 at the root of
        the tail, in the fish's own frame (x forward, y down)."""
        x = length * 0.55 - u * length
        y = wave * math.sin(cyc - u * 3.2) * u * u
        # A bend makes a C: the nose and the tail both pull back and up.
        y -= bend * 12.0 * (2.0 * u - 1.0) ** 2 - bend * 4.0
        x += bend * 6.0 * u * u
        return x, y

    def depth(u: float) -> float:
        # A blunt nose, a deep middle, a thin root of the tail.
        return DEPTH * max(0.18, math.sin(math.pi * (0.1 + 0.8 * u)) ** 0.8) * (1.0 - 0.75 * max(0.0, u - 0.7) / 0.3)

    def world(x: float, y: float) -> Tuple[float, float]:
        a = math.radians(lean)
        y *= sy
        return (cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a))

    steps = [k / 16.0 for k in range(17)]
    top = [spine(u) for u in steps]
    top = [(x, y - depth(u)) for (x, y), u in zip(top, steps)]
    bottom = [(x, y + depth(u)) for (x, y), u in zip([spine(u) for u in steps], steps)]
    nose = spine(0.0)

    # The tail fin: two lobes from the root of the tail, swung by the wave.
    rx, ry = spine(1.0)
    swing = wave * 0.9 * math.sin(cyc - 3.6) + bend * 6.0
    tail = [(rx + 2.0, ry - 3.0), (rx - 12.0, ry - 13.0 + swing), (rx - 8.0, ry + swing * 0.5), (rx - 12.0, ry + 13.0 + swing), (rx + 2.0, ry + 3.0)]
    f.poly([world(*p) for p in tail], RED)
    f.ink([world(rx - 1.0, ry), world(rx - 9.0, ry - 9.0 + swing)], 0.9, RED_DARK)
    f.ink([world(rx - 1.0, ry), world(rx - 9.0, ry + 9.0 + swing)], 0.9, RED_DARK)

    # The fin on its back, and the fin under it: both stand up when it flares.
    up = 1.0 + 0.6 * flare
    d0, d1 = spine(0.3), spine(0.62)
    dorsal = [(d0[0], d0[1] - depth(0.3) + 1.0), (d0[0] - 6.0, d0[1] - depth(0.3) - 10.0 * up), (d1[0] + 2.0, d1[1] - depth(0.62) - 6.0 * up), (d1[0], d1[1] - depth(0.62) + 1.0)]
    f.poly([world(*p) for p in dorsal], RED)
    for k in range(3):
        a = d0[0] - 2.0 - k * 5.0
        f.ink([world(a, d0[1] - depth(0.4)), world(a - 3.0, d0[1] - depth(0.4) - 6.0 * up)], 0.8, RED_DARK)
    a0, a1 = spine(0.6), spine(0.78)
    anal = [(a0[0], a0[1] + depth(0.6) - 1.0), (a0[0] - 6.0, a0[1] + depth(0.6) + 6.0 * up), (a1[0], a1[1] + depth(0.78) - 1.0)]
    f.poly([world(*p) for p in anal], RED)

    # The body.
    outline = top + list(reversed(bottom))
    f.poly([world(*p) for p in outline], RED)
    # The pale belly, and the dark of its back.
    mid = [(x, yt + (yb - yt) * 0.62) for (x, yt), (_, yb) in zip(top, bottom)]
    f.poly([world(*p) for p in mid[1:14] + list(reversed(bottom[1:14]))], BELLY, body=False)
    back = [(x, yt + 4.0) for x, yt in top]
    f.poly([world(*p) for p in top[1:15] + list(reversed(back[1:15]))], RED_DARK, body=False)
    # The scales: rows of small arcs.
    for row in (-0.45, 0.0, 0.45):
        for k in range(5):
            u = 0.3 + k * 0.11
            sx, syy = spine(u)
            syy += row * depth(u)
            arc = [(sx + 2.6 * math.cos(a) - 2.0, syy + 2.6 * math.sin(a)) for a in (-1.2, -0.6, 0.0, 0.6, 1.2)]
            f.ink([world(*p) for p in arc], 0.7, K.alpha(RED_DARK, 0.7))
    # The gill: one curve behind the head.
    g = spine(0.22)
    f.ink([world(g[0] + 1.0, g[1] - depth(0.22) * 0.7), world(g[0] - 2.0, g[1]), world(g[0] + 1.0, g[1] + depth(0.22) * 0.7)], 1.2, RED_DARK)
    # The fin at its side, that paddles.
    p0 = spine(0.3)
    paddle = 3.0 * math.sin(cyc * 2.0) + 4.0 * flare
    pect = [(p0[0] + 1.0, p0[1] + 1.0), (p0[0] - 12.0, p0[1] + 7.0 + paddle), (p0[0] - 9.0, p0[1] - 1.0 + paddle * 0.3)]
    f.poly([world(*p) for p in K.grow(pect, 1.0)], RED_DARK, body=False)
    f.poly([world(*p) for p in pect], RED_LIGHT, body=False)

    # The mouth at its nose: lips, open when it strikes.
    mx, my = nose[0] - 1.0, nose[1] + 3.0
    gape = 1.0 + 12.0 * mouth
    f.poly([world(mx + 3.0, my - gape * 0.5), world(mx - 9.0, my), world(mx + 3.0, my + gape * 0.5)], K.shade(RED_DARK, 0.5))
    f.ink([world(mx + 3.0, my - gape * 0.5), world(mx - 9.0, my), world(mx + 3.0, my + gape * 0.5)], 1.6, RED_LIGHT)

    # The eye: big, round, and looking right at you.
    ex, ey = nose[0] - 11.0, nose[1] - 4.0
    w = world(ex, ey)
    if eye == "x":
        f.ellipse(w[0], w[1], 5.5, 5.5, K.WHITE, body=False)
        f.ink([(w[0] - 3.0, w[1] - 3.0), (w[0] + 3.0, w[1] + 3.0)], 1.4)
        f.ink([(w[0] - 3.0, w[1] + 3.0), (w[0] + 3.0, w[1] - 3.0)], 1.4)
    elif eye == "narrow":
        f.ellipse(w[0], w[1], 5.5, 5.5, K.WHITE, body=False)
        f.ellipse(w[0] + 0.8, w[1] + 0.4, 3.4, 3.4, IRIS, body=False)
        f.dot(w[0] + 1.2, w[1] + 0.4, 1.8)
        # A lid down over the top half: it means it.
        f.poly([(w[0] - 6.0, w[1] - 6.0), (w[0] + 6.0, w[1] - 6.0), (w[0] + 6.0, w[1] + 0.5), (w[0] - 6.0, w[1] - 1.8)], RED_DARK, body=False)
    else:
        big = 1.2 if eye == "wide" else 1.0
        f.ellipse(w[0], w[1], 5.8 * big, 5.8 * big, K.WHITE, body=False)
        f.ellipse(w[0] + 0.6, w[1], 3.4 * big, 3.4 * big, IRIS, body=False)
        f.dot(w[0] + 0.8, w[1], 1.8 * big)
        f.dot(w[0] - 0.4, w[1] - 1.4, 0.8, K.WHITE)
    if glint > 0.05:
        # A star of light on its back: look at me.
        gx, gy = world(*spine(0.45))
        gy -= 6.0 * sy
        for a in (0.0, math.pi / 2.0):
            dx, dy = math.cos(a) * 5.0 * glint, math.sin(a) * 5.0 * glint
            f.glow_line([(gx - dx, gy - dy), (gx + dx, gy + dy)], 1.2, K.alpha(K.WHITE, glint))
        f.glow(gx, gy, 3.0, K.alpha(K.YELLOW, 0.6 * glint))
    if alarm:
        ax, ay = cx + 26.0, cy - 30.0
        f.limb([(ax, ay - 9.0), (ax, ay)], 2.6, K.MAGENTA)
        f.ellipse(ax, ay + 5.0, 1.7, 1.7, K.MAGENTA)
    if anim == "attack_side" and t > 0.15:
        # Lines of speed behind it.
        a = 1.0 - t
        for k in (-8.0, 0.0, 8.0):
            x0 = cx - 34.0
            f.glow_line([(x0, cy + k), (x0 - 14.0 + abs(k), cy + k)], 1.4, K.alpha(K.WHITE, 0.7 * a))
    if anim == "hit":
        # Scales knocked off it.
        for _ in range(5):
            a = rng.uniform(-2.8, -0.2)
            d = 20.0 + 12.0 * t
            f.ellipse(cx + math.cos(a) * d, cy + math.sin(a) * d * 0.9, 2.0, 1.4, RED_LIGHT, body=False)
    return f.finish(outline=K.shade(RED_DARK, 0.4), width=1.5, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
