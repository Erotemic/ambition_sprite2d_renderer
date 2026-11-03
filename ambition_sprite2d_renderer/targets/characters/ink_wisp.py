"""The Ink Wisp: a drop of living ink from the Inkfall Caverns.

A round drop of violet ink as big as a head, with a tail that thins and
curls under it, two white eyes and nothing else on its face. Magenta light
moves on its skin, and it glows. It floats, and it spits ink.

Its windup is a swell: it fills like a cheek. Its strike is the spit, its
mouth wide and its body thrown back. A hit splashes it; its death is a fall
into a puddle that sinks into the floor.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List

from . import _art_cast_kit as K

TARGET_NAME = "ink_wisp"
FRAME_SIZE = (96, 96)
ROWS = K.ENEMY_ROWS

ACTOR_METADATA = K.enemy_metadata(
    TARGET_NAME, "Ink Wisp", "Blob", "Small", "Light", "Float", ["ink", "floating", "glowing"],
    "A drop of living ink from the Inkfall Caverns of the Art dimension: a violet drop with white eyes and a curl of a "
    "tail. It floats, keeps its distance and spits ink.",
)

INK_BODY = K.VIOLET
INK_DARK = K.VIOLET_DARK


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = K.Frame(FRAME_SIZE)
    cx, cy, r = 46.0, 42.0, 17.0
    sx, sy = 1.0, 1.0
    lean, eyes, mouth, fade, tail_swing = 0.0, "open", 0.0, 1.0, math.sin(cyc)
    if anim == "idle":
        cy += 2.5 * math.sin(cyc)
    elif anim == "walk":
        cy += 1.5 * math.sin(cyc * 2.0)
        lean = 12.0
    elif anim == "notice":
        sy = 1.0 + 0.18 * math.sin(math.pi * t)
        sx = 1.0 - 0.10 * math.sin(math.pi * t)
        eyes = "wide"
    elif anim == "windup":
        sx, sy = 1.18 + 0.02 * math.sin(cyc * 2.0), 0.86
        lean, eyes = -10.0, "narrow"
    elif anim == "attack_side":
        strike = math.sin(math.pi * min(1.0, t * 1.5))
        lean, mouth, eyes = -16.0 * strike + 8.0, strike, "narrow"
        cx -= 4.0 * strike
    elif anim == "hit":
        sx, sy = 1.25, 0.75
        eyes = "shut"
    elif anim == "death":
        drop = t
        cy += 38.0 * drop * drop
        sx, sy = 1.0 + 1.4 * drop, 1.0 - 0.75 * drop
        eyes, fade = "shut", 1.0 - max(0.0, t - 0.6) / 0.4

    rx, ry = r * sx, r * sy
    # The tail: a tapering curl from under the drop, behind it.
    tail = []
    for k in range(9):
        u = k / 8.0
        tail.append((cx - 6.0 * u - lean * 0.2 + 7.0 * tail_swing * u * u, cy + ry * 0.6 + 26.0 * u * sy))
    width = [12.0 * (1.0 - u / 9.0) for u in range(9)]
    for k in range(8):
        f.limb([tail[k], tail[k + 1]], width[k], INK_BODY)
    curl_x, curl_y = tail[-1]
    f.limb([(curl_x, curl_y), (curl_x + 4.0, curl_y + 2.0), (curl_x + 6.0, curl_y - 2.0)], 2.2, INK_BODY)
    # The drop: round, a little pointed at its top as a drop is.
    body = K.ellipse_points(cx, cy, rx, ry, 30)
    top = (cx - lean * 0.15, cy - ry - 7.0 * sy)
    body = [p for p in body if p[1] > cy - ry * 0.5] + [top]
    body.sort(key=lambda p: math.atan2(p[1] - cy, p[0] - cx))
    body = K.turn(body, cx, cy, lean * 0.4)
    f.poly(body, INK_BODY)
    # Dark under, light moving on its skin.
    f.poly(K.turn(K.ellipse_points(cx + 2.0, cy + ry * 0.45, rx * 0.85, ry * 0.45, 20), cx, cy, lean * 0.4), INK_DARK, body=False)
    sheen_a = -0.9 + 0.25 * math.sin(cyc)
    f.poly([(cx + math.cos(a) * rx * 0.72, cy + math.sin(a) * ry * 0.72) for a in (sheen_a - 0.9, sheen_a - 0.45, sheen_a)] +
           [(cx + math.cos(a) * rx * 0.55, cy + math.sin(a) * ry * 0.55) for a in (sheen_a, sheen_a - 0.45, sheen_a - 0.9)], K.MAGENTA_LIGHT, body=False)
    f.dot(cx - rx * 0.45, cy - ry * 0.5, 2.0, K.WHITE)
    # The eyes: two white shapes, and no pupils.
    ex = cx + 4.0 + lean * 0.1
    for ox in (-5.5, 6.0):
        x, y = ex + ox, cy - 2.0
        if eyes == "shut":
            f.ink([(x - 3.0, y), (x + 3.0, y + 0.8)], 1.6, K.WHITE)
        elif eyes == "narrow":
            f.poly([(x - 3.4, y - 1.0), (x + 3.4, y - 2.6), (x + 3.0, y + 2.0), (x - 3.0, y + 2.0)], K.WHITE, body=False)
        else:
            big = 1.25 if eyes == "wide" else 1.0
            f.ellipse(x, y, 3.0 * big, 4.2 * big, K.WHITE, body=False)
            f.glow(x, y, 4.0 * big, K.alpha(K.WHITE, 0.25))
    if mouth > 0.05:
        mx, my = cx + rx * 0.62, cy + 6.0
        f.ellipse(mx, my, 3.0 + 3.0 * mouth, 2.0 + 3.0 * mouth, K.INK, body=False)
        # The spit: a glob that leaves the mouth.
        gx = mx + 8.0 + 26.0 * mouth
        f.ellipse(gx, my, 4.0, 3.2, K.MAGENTA)
        f.glow(gx, my, 6.0, K.alpha(K.MAGENTA, 0.5))
    if anim == "hit":
        for k in range(6):
            a = math.tau * k / 6.0 + 0.3
            f.ellipse(cx + math.cos(a) * (rx + 7.0), cy + math.sin(a) * (ry + 7.0), 2.2, 2.2, INK_BODY)
    if anim == "death" and t > 0.3:
        f.ellipse(cx, min(90.0, cy + ry), rx * 1.2, 3.0 + 2.0 * t, INK_BODY)
    # The glow of living ink round it.
    f.glow(cx, cy, rx * 1.15, K.alpha(K.MAGENTA, 0.22 * fade))
    return f.finish(outline=K.shade(INK_DARK, 0.45), width=1.4, glow_blur=3.0, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
