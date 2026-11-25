"""The Intrusive Thought: a cloud of talk that drifts through the Neural
Cathedral (the Neural dimension, gate address LATENT).

A lumpy purple cloud as big as a head, two narrow yellow eyes and a frown,
and three little speech bubbles that orbit it and will not stop. It drifts
toward you and barges in: its windup is a swell, its bubbles crowding in;
its strike is a rush, mouth first. A hit scatters its bubbles; its death is
a thinning into nothing, the bubbles last to go.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List

from . import _art_cast_kit as K

TARGET_NAME = "intrusive_thought"
FRAME_SIZE = (112, 112)
ROWS = K.ENEMY_ROWS

ACTOR_METADATA = K.enemy_metadata(
    TARGET_NAME, "Intrusive Thought", "Blob", "Small", "Light", "Float", ["thought", "floating", "cloud"],
    "A cloud of talk in the Neural Cathedral of the Neural dimension: a lumpy purple cloud with narrow yellow eyes and a "
    "frown, little speech bubbles circling it. It drifts toward you and barges in.",
)
ACTOR_METADATA["tags"] = ["enemy", "neural"]

CLOUD = (128, 84, 176, 255)
CLOUD_DARK = (78, 46, 120, 255)
CLOUD_LIGHT = (184, 150, 226, 255)
EYE = (255, 222, 80, 255)
BUBBLE = (246, 244, 252, 255)


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = K.Frame(FRAME_SIZE)
    cx, cy, r = 56.0, 54.0, 22.0
    sx, sy, lean, orbit, spread, fade, frown = 1.0, 1.0, 0.0, cyc, 1.0, 1.0, 1.0
    eyes = "narrow"
    if anim == "idle":
        cy += 2.5 * math.sin(cyc)
    elif anim == "walk":
        cy += 1.5 * math.sin(cyc * 2.0)
        lean = 10.0
    elif anim == "notice":
        sx = sy = 1.0 + 0.12 * math.sin(math.pi * t)
        eyes = "wide"
    elif anim == "windup":
        sx, sy = 1.16, 1.12
        spread = 0.7
        frown = 1.6
        orbit = cyc * 2.0
    elif anim == "attack_side":
        strike = math.sin(math.pi * min(1.0, t * 1.4))
        cx += 12.0 * strike
        sx, sy = 1.0 + 0.25 * strike, 1.0 - 0.15 * strike
        lean = 18.0 * strike
        spread = 0.6
        eyes = "wide"
    elif anim == "hit":
        sx, sy = 0.86, 0.86
        spread = 1.7
        eyes = "shut"
    elif anim == "death":
        sx = sy = 1.0 + 0.4 * t
        spread = 1.0 + 1.5 * t
        fade = 1.0 - t
        eyes = "shut"
    rx, ry = r * sx, r * sy * 0.82
    # The cloud: overlapping lumps, darker under.
    lumps = [(-0.55, 0.15, 0.62), (0.0, -0.25, 0.75), (0.55, 0.1, 0.62), (-0.25, 0.35, 0.6), (0.3, 0.38, 0.6)]
    for dx, dy, k in lumps:
        f.ellipse(cx + dx * rx + lean * 0.2, cy + dy * ry, rx * k, ry * k, CLOUD)
    f.ellipse(cx + lean * 0.2, cy + ry * 0.45, rx * 0.9, ry * 0.35, CLOUD_DARK, body=False)
    f.ellipse(cx - rx * 0.25, cy - ry * 0.45, rx * 0.35, ry * 0.2, CLOUD_LIGHT, body=False)
    # The face: narrow eyes, a frown.
    ex = cx + 3.0 + lean * 0.15
    for ox in (-7.0, 7.0):
        x, y = ex + ox, cy - 2.0
        if eyes == "shut":
            f.ink([(x - 3.5, y), (x + 3.5, y + 1.0)], 1.6, EYE)
        elif eyes == "wide":
            f.ellipse(x, y, 3.6, 3.6, EYE, body=False)
            f.dot(x + 0.8, y, 1.2, K.INK)
        else:
            tilt = 1.6 if ox < 0 else -1.6
            f.poly([(x - 3.8, y - 1.0 - tilt), (x + 3.8, y - 1.0 + tilt), (x + 3.2, y + 2.4), (x - 3.2, y + 2.4)], EYE, body=False)
    mx, my = ex, cy + 8.0
    f.ink([(mx - 6.0, my + 1.5 * frown), (mx, my - 1.0 * frown), (mx + 6.0, my + 1.5 * frown)], 1.8, K.INK)
    # The bubbles: three, circling, each with its tail toward the cloud.
    for k in range(3):
        a = orbit + math.tau * k / 3.0
        bx = cx + math.cos(a) * (rx + 12.0) * spread
        by = cy + math.sin(a) * (ry + 10.0) * spread * 0.8 - 4.0
        f.ellipse(bx, by, 7.0, 5.2, K.alpha(BUBBLE, fade))
        tx, ty = bx + (cx - bx) * 0.25, by + (cy - by) * 0.25
        f.poly([(bx - 2.0, by + 3.0), (bx + 2.0, by + 3.0), (tx, ty)], K.alpha(BUBBLE, fade))
        for d in (-2.6, 0.0, 2.6):
            f.dot(bx + d, by, 0.9, K.alpha(CLOUD_DARK, fade))
    f.glow(cx, cy, rx * 1.2, K.alpha(CLOUD_LIGHT, 0.18 * fade))
    return f.finish(outline=K.shade(CLOUD_DARK, 0.5), width=1.4, glow_blur=3.0, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
