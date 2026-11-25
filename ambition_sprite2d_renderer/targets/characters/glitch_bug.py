"""The Bug: a beetle loose on the Unfinished dimension (gate address
INSTALLING, `docs/planning/game/unfinished-dimension.md`).

A beetle the size of a cat whose shell is the texture the world shows when a
texture is missing: a checkerboard of a dull magenta and near-black, held
down to suit the dimension's paper and grey (Jon found the concept sheets
too colourful). Six legs, two feelers. Now and then a slice of it slips
sideways and slips back: it does not render quite right.

It scuttles; when it sees you it rears with its feelers up. Its windup
crouches and shivers, its strike is a bite with a short rush. A hit tears it
into slices that slide apart; at its death it breaks into squares that fall
and go out.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Sequence, Tuple

from PIL import Image

from . import _art_cast_kit as K

TARGET_NAME = "glitch_bug"
FRAME_SIZE = (96, 96)
ROWS = K.ENEMY_ROWS
GROUND = 90.0

ACTOR_METADATA = K.enemy_metadata(
    TARGET_NAME, "Bug", "Multileg", "Small", "Light", "Walk", ["beetle", "bug", "glitch"],
    "A beetle loose on the Unfinished dimension, its shell the checkerboard of a missing texture. It scuttles, rears, "
    "and bites with a short rush; a slice of it slips sideways now and then.",
)
ACTOR_METADATA["tags"] = ["enemy", "unfinished"]

CHECK_A = (176, 84, 158, 255)
CHECK_B = (34, 30, 40, 255)
LEG = (40, 36, 46, 255)
EYE = (230, 230, 236, 255)

Point = Tuple[float, float]


def _shell(f: K.Frame, cx: float, cy: float, rx: float, ry: float) -> None:
    """The shell: an oval cut into a checkerboard of squares."""
    f.poly(K.ellipse_points(cx, cy, rx, ry, 28), CHECK_B)
    s = 5.0
    y = cy - ry
    row = 0
    while y < cy + ry:
        x = cx - rx + (s if row % 2 else 0.0)
        while x < cx + rx:
            sq = [(x, y), (x + s, y), (x + s, y + s), (x, y + s)]
            inside = [(px, py) for px, py in sq if ((px - cx) / rx) ** 2 + ((py - cy) / ry) ** 2 <= 1.05]
            if len(inside) >= 3:
                f.poly(sq, CHECK_A, body=False)
            x += 2 * s
        y += s
        row += 1
    f.ink([(cx, cy - ry + 1.0), (cx, cy + ry - 1.0)], 1.0, K.shade(CHECK_B, 0.6))


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = K.Frame(FRAME_SIZE)
    cx, cy = 44.0, GROUND - 12.0
    gait, rear, rush, feelers, bite = 0.0, 0.0, 0.0, 0.3, 0.0
    if anim == "idle":
        gait = 0.2 * math.sin(cyc)
    elif anim == "walk":
        gait = math.sin(cyc * 2.0)
        cy -= abs(math.sin(cyc * 2.0)) * 1.0
    elif anim == "notice":
        rear = math.sin(math.pi * min(1.0, t * 1.4))
        feelers = 1.0
    elif anim == "windup":
        cy += 2.0
        cx -= 3.0 + 1.0 * math.sin(cyc * 6.0)
        feelers = 0.6
    elif anim == "attack_side":
        s = math.sin(math.pi * min(1.0, t * 1.4))
        rush = 14.0 * s
        bite = s
    cx += rush
    tilt = -18.0 * rear
    # The legs: three a side, alternating.
    for k, lx in enumerate((-14.0, 0.0, 14.0)):
        sw = gait * (1.0 if k % 2 else -1.0) * 4.0
        for side, depth in ((1.0, 0.0), (-1.0, 2.0)):
            hip = (cx + lx * 0.7, cy - 2.0 - depth)
            knee = (cx + lx * 1.45 + sw * side, cy - 13.0 - depth)
            foot = (cx + lx * 2.0 + sw * side, GROUND - depth * 0.5)
            f.limb(K.turn([hip, knee, foot], cx, GROUND, tilt), 1.7, LEG if side > 0 else K.shade(LEG, 0.8))
    # The head, its jaws and feelers.
    hx, hy = K.turn([(cx + 25.0, cy + 1.0)], cx, GROUND, tilt)[0]
    f.ellipse(hx, hy, 7.0, 5.5, CHECK_B)
    jaw = 2.0 + 4.0 * bite
    f.limb([(hx + 6.0, hy + 1.0), (hx + 11.0, hy - jaw)], 2.0, LEG)
    f.limb([(hx + 6.0, hy + 3.0), (hx + 11.0, hy + 3.0 + jaw)], 2.0, LEG)
    for d in (-1.0, 1.0):
        up = 10.0 + 8.0 * feelers
        f.ink([(hx + 2.0, hy - 5.0), (hx + 8.0 + d * 2.0, hy - up * 0.6), (hx + 14.0 + d * 3.0, hy - up)], 1.0, LEG)
    f.dot(hx + 4.0, hy - 2.0, 1.4, EYE)
    # The shell, turned with the body.
    shell_cx, shell_cy = K.turn([(cx, cy)], cx, GROUND, tilt)[0]
    _shell(f, shell_cx, shell_cy, 22.0, 9.0)
    image = f.finish(outline=K.shade(CHECK_B, 0.5), width=1.3, glow_blur=1.5)
    return _glitch(image, anim, i, t)


def _glitch(image: Image.Image, anim: str, i: int, t: float) -> Image.Image:
    """Slip slices of the picture sideways: now and then at rest, apart on a
    hit, into falling squares at death."""
    w, h = image.size
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if anim == "death":
        size = max(2, w // 24)
        fall = t * t * h * 0.6
        keep = 1.0 - t
        for y in range(0, h, size):
            for x in range(0, w, size):
                tile = image.crop((x, y, x + size, y + size))
                if tile.getbbox() is None:
                    continue
                if ((x * 7 + y * 13) % 97) / 97.0 > keep:
                    continue
                drift = int(fall * (0.5 + ((x * 31 + y) % 17) / 17.0))
                out.alpha_composite(tile, (x, min(h - size, y + drift)))
        return out
    bands: Sequence[Tuple[int, int, int]]
    if anim == "hit":
        k = int(8 * math.sin(math.pi * t) + 4)
        bands = ((0, h // 3, -k), (h // 3, 2 * h // 3, k), (2 * h // 3, h, -k // 2))
    elif anim in ("idle", "walk") and i % 3 == 2:
        bands = ((0, h // 2 - 6, 0), (h // 2 - 6, h // 2 + 2, 5), (h // 2 + 2, h, 0))
    else:
        return image
    for y0, y1, dx in bands:
        out.alpha_composite(image.crop((0, y0, w, y1)), (dx, y0))
    return out


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
