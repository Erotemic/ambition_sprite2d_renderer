"""The Monsoon Squall: a small, cross storm cloud of the Monsoon Coast.

The monsoon winds carried the dhows of the Indian Ocean trade: to the east
for half the year and back to the west for the other half. The winds were
on time. This cloud is not happy about it.

A small grey cloud of round puffs, lighter on top and dark underneath, with
a cross face: heavy brows, a frown, and cheeks it fills to spit. Drops of
rain fall from its underside. It floats, keeps its distance and spits rain.
Its windup is a breath: it swells and goes dark, and lightning flickers in
it. Its strike spits a jet of rain at you, and it kicks back. A hit shakes
the rain out of it; at its death it rains itself away to nothing.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import List

from . import _art_cast_kit as K
from . import _history_steppe_kit as H

TARGET_NAME = "monsoon_squall"
FRAME_SIZE = (128, 128)
ROWS = K.ENEMY_ROWS

ACTOR_METADATA = K.enemy_metadata(
    TARGET_NAME, "Monsoon Squall", "Amorphous", "Small", "Light", "Float", ["history", "monsoon", "cloud", "weather", "floating"],
    "A small, cross storm cloud of the Monsoon Coast in the History dimension. It floats, keeps its distance, swells "
    "dark with lightning in it, and spits a jet of rain at you.",
)

CLOUD = H.MONSOON
CLOUD_LIGHT = H.MONSOON_LIGHT
CLOUD_DARK = H.MONSOON_DARK
STORM = (98, 104, 124, 255)
STORM_DARK = (60, 64, 84, 255)
RAIN = (150, 206, 240, 255)
RAIN_LIGHT = (230, 248, 255, 255)
RAIN_EDGE = (40, 96, 150, 255)
BOLT = (255, 232, 110, 255)

#: The puffs of the cloud: a centre and a radius, about the cloud's middle.
PUFFS = [(-22.0, 6.0, 13.0), (-10.0, -6.0, 16.0), (8.0, -10.0, 17.0), (23.0, 2.0, 13.0), (4.0, 8.0, 15.0), (-12.0, 10.0, 11.0)]


def _drop(f: K.Frame, x: float, y: float, s: float = 1.0, a: float = 1.0) -> None:
    """A drop of rain: light blue, with no outline, so it reads as water."""
    pts = [(x, y - 4.0 * s), (x + 2.2 * s, y + 0.6 * s), (x, y + 2.6 * s), (x - 2.2 * s, y + 0.6 * s)]
    f.poly(K.grow(pts, 0.6), K.alpha(RAIN_EDGE, a), body=False)
    f.poly(pts, K.alpha(RAIN, a), body=False)
    f.dot(x - 0.6 * s, y, 0.6 * s, K.alpha(RAIN_LIGHT, a))


def _bolt(f: K.Frame, x: float, y: float, a: float) -> None:
    pts = [(x, y), (x + 4.0, y + 6.0), (x + 1.0, y + 6.6), (x + 5.0, y + 13.0)]
    f.glow_line(pts, 1.8, K.alpha(BOLT, a))


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    rng = random.Random(f"squall:{anim}:{i}")
    f = K.Frame(FRAME_SIZE)
    cx, cy, sx, sy, lean = 62.0, 54.0, 1.0, 1.0, 0.0
    dark, brows, eyes, mouth, cheeks, alarm, fade = 0.0, "cross", "open", "frown", 0.0, False, 1.0
    drip, bolts, jet, shed, kick = 2, 0.0, 0.0, 0.0, 0.0
    if anim == "idle":
        cy += 2.5 * math.sin(cyc)
        sx = 1.0 + 0.03 * math.sin(cyc * 2.0)
    elif anim == "walk":
        cy += 1.5 * math.sin(cyc * 2.0)
        lean = 8.0
        drip = 3
    elif anim == "notice":
        k = math.sin(math.pi * min(1.0, t * 1.3))
        eyes, alarm, mouth, bolts, dark = "wide", True, "o", 0.8 * k, 0.3 * k
        cy -= 4.0 * k
        sy = 1.0 + 0.08 * k
    elif anim == "windup":
        sx, sy = 1.12 + 0.02 * math.sin(cyc * 2.0), 1.08
        dark, cheeks, mouth, eyes, lean = 1.0, 1.0, "shut", "narrow", -8.0
        bolts = 0.6 + 0.4 * math.sin(cyc * 3.0)
        cx -= 3.0
        drip = 0
    elif anim == "attack_side":
        spit = math.sin(math.pi * min(1.0, t * 1.4))
        jet = spit
        kick = spit
        lean, mouth, eyes, dark = -12.0 * spit, "wide", "narrow", 1.0 - 0.6 * t
        cx -= 6.0 * spit
        drip = 1
    elif anim == "hit":
        k = math.sin(math.pi * (i + 1) / (n + 1))
        sx, sy, eyes, mouth, shed = 1.0 + 0.2 * k, 1.0 - 0.15 * k, "shut", "o", k
        cx -= 4.0 * k
        drip = 0
    elif anim == "death":
        u = t
        sx, sy = 1.0 - 0.6 * u, 1.0 - 0.7 * u
        cy = 50.0 + 20.0 * u
        eyes, mouth, brows = "shut", "o", "sad"
        shed = 1.0
        fade = 1.0 - max(0.0, t - 0.6) / 0.4
        drip = 0

    body = K.shade(CLOUD, 1.0) if not dark else tuple(int(CLOUD[j] + (STORM[j] - CLOUD[j]) * dark) for j in range(3)) + (255,)
    under = tuple(int(CLOUD_DARK[j] + (STORM_DARK[j] - CLOUD_DARK[j]) * dark) for j in range(3)) + (255,)
    top = tuple(int(CLOUD_LIGHT[j] + (CLOUD[j] - CLOUD_LIGHT[j]) * dark * 0.7) for j in range(3)) + (255,)

    def P(x: float, y: float):
        return K.turn([(cx + x * sx, cy + y * sy)], cx, cy, lean)[0]

    # The rain that falls from its underside, behind the cloud.
    for k in range(drip):
        x = -18.0 + k * 16.0 + 4.0 * math.sin(k * 2.1)
        fall = ((t + k * 0.37) % 1.0)
        dx, dy = P(x, 14.0)
        _drop(f, dx - lean * 0.2 * fall, dy + 4.0 + 26.0 * fall, 1.0, 1.0 - fall * 0.6)

    # The puffs: one dark shape underneath, the body, and the light tops.
    for x, y, r in PUFFS:
        px, py = P(x, y + 2.0)
        f.ellipse(px, py, r * sx, r * sy, under)
    for x, y, r in PUFFS:
        px, py = P(x, y)
        f.ellipse(px, py, r * sx * 0.96, r * sy * 0.92, body, body=False)
    for x, y, r in PUFFS[:4]:
        px, py = P(x - r * 0.25, y - r * 0.35)
        f.ellipse(px, py, r * sx * 0.55, r * sy * 0.42, top, body=False)
    # Curls on the puffs, as a cloud is drawn in an old map.
    for x, y, r in PUFFS[1:4]:
        a0 = -2.4
        curl = [P(x + math.cos(a0 + q * 0.35) * r * 0.62, y + math.sin(a0 + q * 0.35) * r * 0.62) for q in range(5)]
        f.ink(curl, 0.9, K.alpha(under, 0.9))

    # Lightning in it.
    if bolts > 0.05:
        bx, by = P(-14.0, -2.0)
        _bolt(f, bx, by, bolts)
        bx, by = P(16.0, 2.0)
        _bolt(f, bx, by, bolts * 0.7)
        f.glow(cx, cy, 20.0 * sx, K.alpha(BOLT, 0.06 * bolts))

    # The face.
    for side in (-1.0, 1.0):
        ex, ey = P(4.0 + side * 8.0, -2.0)
        if eyes == "shut":
            f.ink([(ex - 3.0, ey + 0.6), (ex, ey - 0.6), (ex + 3.0, ey + 0.6)], 1.3, H.SEPIA_INK)
        else:
            big = 1.3 if eyes == "wide" else 1.0
            h = 3.4 * big if eyes != "narrow" else 2.2
            f.ellipse(ex, ey, 2.8 * big, h, K.WHITE, body=False)
            f.dot(ex + 1.0, ey + 0.4, 1.5 * big, H.SEPIA_INK)
        # The brows: down at the middle (cross), or up at it (sad).
        inner = (ex - side * 3.6, ey - 4.0 + (2.4 if brows == "cross" and eyes != "wide" else 0.0) - (1.6 if brows == "sad" else 0.0))
        outer = (ex + side * 3.6, ey - 5.6 + (1.8 if brows == "sad" else 0.0))
        f.limb([inner, outer], 2.0, STORM_DARK, body=False)
    mx, my = P(4.0, 8.0)
    if cheeks > 0.05:
        for side in (-1.0, 1.0):
            bx, by = P(4.0 + side * 12.0, 6.0)
            f.ellipse(bx, by, 4.0 * cheeks, 3.2 * cheeks, K.shade(body, 1.15), body=False)
    if mouth == "frown":
        f.ink([(mx - 4.0, my + 1.6), (mx, my - 0.6), (mx + 4.0, my + 1.6)], 1.3, H.SEPIA_INK)
    elif mouth == "o":
        f.ellipse(mx, my, 2.2, 2.6, H.SEPIA_INK, body=False)
    elif mouth == "shut":
        f.ink([(mx - 3.0, my), (mx + 3.0, my)], 1.3, H.SEPIA_INK)
    else:
        f.ellipse(mx + 1.0, my, 3.4, 3.0, H.SEPIA_INK, body=False)

    if jet > 0.05:
        # The jet of rain, out of its mouth to the front.
        x0, y0 = P(10.0, 8.0)
        reach = 14.0 + 44.0 * jet
        end = min(118.0, x0 + 8.0 + reach)
        # A spray that widens as it goes, and drops in it.
        f.glow_poly([(x0 + 4.0, y0 - 2.0), (end, y0 - 6.0), (end, y0 + 10.0), (x0 + 4.0, y0 + 2.0)], K.alpha(RAIN_LIGHT, 0.35 * jet))
        for k in range(12):
            u = k / 11.0
            x = x0 + 8.0 + reach * u
            y = y0 + 2.0 * u * u * 4.0 + rng.uniform(-1.0, 1.0) * (1.0 + 5.0 * u)
            if x < 118.0:
                drop = K.turn([(x - 4.4, y), (x, y - 2.0), (x + 2.8, y), (x, y + 2.0)], x, y, 8.0)
                f.poly(K.grow(drop, 0.6), RAIN_EDGE, body=False)
                f.poly(drop, RAIN, body=False)
    if shed > 0.05:
        # Rain shaken out of it, all round.
        for k in range(int(6 + 6 * shed)):
            a = rng.uniform(0.2, math.pi - 0.2)
            r = rng.uniform(26.0, 40.0)
            x, y = cx + math.cos(a) * r * 1.2, cy + math.sin(a) * r * 0.8 + 8.0
            if anim == "death":
                y += 30.0 * t * rng.uniform(0.5, 1.0)
            _drop(f, min(122.0, max(6.0, x)), min(120.0, y), 1.0, 0.9)
    if alarm:
        ax, ay = P(28.0, -26.0)
        H.alarm_mark(f, ax, max(14.0, ay))
    return f.finish(outline=H.SEPIA_INK, width=1.4, glow_blur=2.0, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
