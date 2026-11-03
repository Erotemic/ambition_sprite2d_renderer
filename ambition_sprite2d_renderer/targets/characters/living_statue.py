"""The Living Statue: a marble bust of the Sculpture Garden that moves.

A great head and shoulders of white marble, as tall as three robots, that
nobody finished: the face is cut and polished, and the back of the head is
still the rough block, with the marks of the chisel on it. A stripe of
magenta paint runs across its face, moss grows on one shoulder, and its
eyes are lit cyan from inside.

It has no legs. It goes along by rocking on its base, as a heavy thing is
walked across a floor. Its windup is a rise and a lean back; its strike is
a fall forward onto whatever is in front of it, with a burst of dust and
cracks in the floor. A hit knocks chips off it; at its death it cracks and
falls into blocks.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import List

from . import _art_cast_kit as K

TARGET_NAME = "living_statue"
FRAME_SIZE = (192, 192)
ROWS = K.ENEMY_ROWS
GROUND = 189.0

ACTOR_METADATA = K.enemy_metadata(
    TARGET_NAME, "Living Statue", "Amorphous", "Large", "Heavy", "Walk", ["marble", "statue", "unfinished"],
    "A marble bust of the Sculpture Garden of the Art dimension that nobody finished, as tall as three robots. It rocks "
    "along on its base, rises, and falls forward onto what is in front of it. Slow, heavy, and very clear about it.",
)

ROUGH = (186, 182, 198, 255)
EYE = (120, 240, 255, 255)


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    rng = random.Random(f"statue:{anim}:{i}")
    f = K.Frame(FRAME_SIZE)
    tilt, lift, glow, apart, fade, chips, dust = 0.0, 0.0, 0.5, 0.0, 1.0, 0, 0.0
    cx = 70.0
    if anim == "idle":
        glow = 0.45 + 0.15 * math.sin(cyc)
    elif anim == "walk":
        tilt, lift = 5.0 * math.sin(cyc), 3.0 * abs(math.sin(cyc))
        cx += 2.0 * math.sin(cyc)
        dust = 0.3 * abs(math.cos(cyc))
    elif anim == "notice":
        glow, lift = 0.5 + 0.5 * math.sin(math.pi * t), 4.0 * math.sin(math.pi * t)
    elif anim == "windup":
        tilt, lift, glow = -12.0 + 0.8 * math.sin(cyc * 2.0), 12.0, 0.95
    elif anim == "attack_side":
        fall = min(1.0, t * 1.8)
        tilt, lift, glow = -12.0 + 40.0 * fall * fall, 12.0 * (1.0 - fall), 1.0
        cx += 8.0 * fall
        dust = max(0.0, (t - 0.45) / 0.55) * 1.2
    elif anim == "hit":
        tilt, chips, glow = -4.0, 6, 0.2
    elif anim == "death":
        apart, glow = t, 0.4 * (1.0 - t)
        fade = 1.0 - max(0.0, t - 0.7) / 0.3

    base = GROUND - lift
    # It rocks on the edge of its base that it leans toward.
    pivot = (cx + 54.0 if tilt > 0 else cx - 52.0, base)

    def at(points):
        return K.turn(points, pivot[0], pivot[1], tilt)

    def piece(points, dx, dy, spin):
        """A piece of the bust that comes away from it as it breaks."""
        if not apart:
            return at(points)
        mx = sum(x for x, _ in points) / len(points)
        my = sum(y for _, y in points) / len(points)
        moved = K.turn(points, mx, my, spin * apart)
        return at([(x + dx * apart, y + dy * apart * apart) for x, y in moved])

    # The base: a low slab of stone.
    f.poly(piece([(cx - 52.0, base), (cx + 54.0, base), (cx + 50.0, base - 12.0), (cx - 48.0, base - 12.0)], 0, 0, 0), K.MARBLE_SHADE)
    # The shoulders: a broad slab, rough at the back.
    shoulders = [(cx - 50.0, base - 12.0), (cx + 52.0, base - 12.0), (cx + 44.0, base - 52.0), (cx + 16.0, base - 64.0), (cx - 22.0, base - 64.0), (cx - 46.0, base - 50.0)]
    f.poly(piece(shoulders, -6, 30, -8), K.MARBLE)
    f.poly(piece([(cx - 50.0, base - 12.0), (cx - 10.0, base - 12.0), (cx - 14.0, base - 60.0), (cx - 22.0, base - 64.0), (cx - 46.0, base - 50.0)], -22, 34, -20), ROUGH)
    # The neck and the head.
    f.poly(piece([(cx - 12.0, base - 60.0), (cx + 16.0, base - 60.0), (cx + 14.0, base - 82.0), (cx - 10.0, base - 82.0)], 4, 44, 10), K.MARBLE_SHADE)
    head = [(cx - 26.0, base - 92.0), (cx - 22.0, base - 134.0), (cx - 4.0, base - 150.0), (cx + 20.0, base - 146.0), (cx + 32.0, base - 128.0),
            (cx + 40.0, base - 112.0), (cx + 34.0, base - 106.0), (cx + 34.0, base - 92.0), (cx + 24.0, base - 78.0), (cx - 8.0, base - 74.0)]
    f.poly(piece(head, 18, 70, 25), K.MARBLE)
    # The back of the head: the block, with the marks of the chisel.
    block = [(cx - 26.0, base - 92.0), (cx - 22.0, base - 134.0), (cx - 4.0, base - 150.0), (cx + 2.0, base - 140.0), (cx - 6.0, base - 96.0), (cx - 8.0, base - 74.0)]
    f.poly(piece(block, 10, 60, 30), ROUGH)
    for k in range(5):
        y0 = base - 98.0 - k * 9.0
        f.ink(piece([(cx - 20.0 + k, y0), (cx - 10.0 + k, y0 - 6.0)], 10, 60, 30), 0.9, K.MARBLE_SHADE)
    # The face: brow, nose and lips cut in the marble, in shade below.
    face_shade = [(cx + 20.0, base - 120.0), (cx + 40.0, base - 112.0), (cx + 34.0, base - 106.0), (cx + 34.0, base - 92.0), (cx + 24.0, base - 78.0), (cx + 12.0, base - 84.0)]
    f.poly(piece(face_shade, 18, 70, 25), K.MARBLE_SHADE, body=False)
    f.ink(piece([(cx + 14.0, base - 124.0), (cx + 30.0, base - 126.0)], 18, 70, 25), 1.2, K.MARBLE_SHADE)
    f.ink(piece([(cx + 26.0, base - 92.0), (cx + 33.0, base - 94.0)], 18, 70, 25), 1.2, K.MARBLE_SHADE)
    # A stripe of paint across the face, as somebody had begun to colour it.
    f.poly(piece([(cx - 2.0, base - 118.0), (cx + 36.0, base - 116.0), (cx + 36.0, base - 110.0), (cx - 2.0, base - 111.0)], 18, 70, 25), K.MAGENTA, body=False)
    for k in range(3):
        x = cx + 4.0 + k * 11.0
        f.poly(piece([(x - 1.2, base - 111.0), (x + 1.2, base - 111.0), (x + 0.6, base - 104.0 + k * 2.0), (x - 0.6, base - 104.0 + k * 2.0)], 18, 70, 25), K.MAGENTA, body=False)
    # Moss on the far shoulder.
    for k in range(6):
        mx = cx - 40.0 + k * 6.0
        f.ellipse(*piece([(mx, base - 52.0 - (k % 2) * 3.0)], -22, 34, -20)[0], 4.6, 3.4, K.MOSS)
    # The eyes, lit from inside.
    ex, ey = piece([(cx + 22.0, base - 117.0)], 18, 70, 25)[0]
    f.ellipse(ex, ey, 4.2, 2.8, K.alpha(EYE, 0.4 + 0.6 * glow), body=False)
    f.glow(ex, ey, 5.0 + 7.0 * glow, K.alpha(EYE, 0.55 * glow))
    # Cracks, and the dust of the floor.
    if anim in ("hit", "death"):
        cracks = [[(cx + 4.0, base - 74.0), (cx + 10.0, base - 96.0), (cx + 4.0, base - 112.0), (cx + 12.0, base - 132.0)],
                  [(cx - 16.0, base - 14.0), (cx - 8.0, base - 36.0), (cx - 14.0, base - 56.0)]]
        for crack in cracks[: 1 if anim == "hit" else 2]:
            f.ink(at(crack), 1.2, K.INK)
    for _ in range(chips):
        a = rng.uniform(-2.6, -0.4)
        r = rng.uniform(30.0, 56.0) * (0.4 + t)
        f.poly(K.ellipse_points(cx + 30.0 + math.cos(a) * r, base - 110.0 + math.sin(a) * r, 2.6, 2.0, 5), K.MARBLE)
    if dust > 0.0:
        for k in range(7):
            side = -1.0 if k % 2 else 1.0
            x = cx + 30.0 + side * (20.0 + 6.0 * k * dust)
            f.ellipse(x, GROUND - 4.0 - 3.0 * (k % 3), 7.0 + 4.0 * dust, 4.0 + 2.0 * dust, K.alpha(K.PAPER_SHADE, 0.6 * min(1.0, dust)), body=False)
    if anim == "attack_side" and t > 0.5:
        for k in range(3):
            x0 = cx + 60.0 + k * 10.0
            f.ink([(x0, GROUND), (x0 + 6.0, GROUND - 4.0), (x0 + 3.0, GROUND - 8.0)], 1.0, K.INK)
    if anim == "notice":
        f.limb([(cx + 56.0, base - 160.0), (cx + 56.0, base - 148.0)], 3.4, K.CYAN)
        f.ellipse(cx + 56.0, base - 142.0, 2.2, 2.2, K.CYAN)
    return f.finish(width=2.0, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
