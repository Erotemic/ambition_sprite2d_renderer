"""Percy the Perceptron: an old learning machine of one layer, on the floor
of the Weights (the Neural dimension, gate address LATENT).

A cabinet of grey steel as tall as a person. In its upper half, its retina:
a grid of photocells, some lit. Under it, a patch board with a tangle of
wires between its sockets (its weights, set by hand). At the bottom, one
round lamp, its answer: green for yes, red for no. It does not walk.

It answers yes or no, and only to a question it can draw a straight line
through. It cannot do XOR.

Rows: ``idle`` (cells flicker, the lamp off), ``talk`` (the lamp blinks its
answer), ``hit`` (every cell lights at once) and ``death`` (the cells go out
row by row).
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Tuple

from . import _art_cast_kit as K
from . import _picture_palace_kit as M

TARGET_NAME = "neural_perceptron"
FRAME_SIZE = (112, 192)
ROWS: List[Tuple[str, int, int]] = [("idle", 8, 160), ("talk", 6, 110), ("hit", 3, 90), ("death", 8, 200)]
LOOPS = {"idle", "talk"}

ACTOR_METADATA = M.machine_metadata(
    "npc_neural_perceptron", "Percy the Perceptron", "PropActor", "PropLike", ["machine", "cabinet", "photocells", "lamp"],
    "An old learning machine of one layer on the floor of the Weights, in the Neural dimension: a grey steel cabinet with "
    "a grid of photocells for an eye, a patch board of wires for its weights and one lamp for its answer. It answers "
    "yes or no, and it cannot do XOR.",
    walks=False,
)
ACTOR_METADATA["tags"] = ["townsfolk", "neural", "peaceful", "machine"]

CABINET = (150, 154, 160, 255)
CABINET_DARK = (96, 100, 108, 255)
CABINET_LIGHT = (200, 204, 210, 255)
CELL_OFF = (40, 44, 52, 255)
CELL_ON = (255, 220, 120, 255)
WIRES = ((220, 60, 60, 255), (60, 120, 220, 255), (240, 200, 60, 255), (60, 180, 100, 255))
YES = (90, 230, 120, 255)
NO = (240, 70, 70, 255)


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in LOOPS)
    f = K.Frame(FRAME_SIZE)
    x0, x1, top, foot = 18.0, 94.0, 20.0, 186.0
    # The cabinet, its plinth and its top.
    f.poly([(x0, top), (x1, top), (x1, foot), (x0, foot)], CABINET)
    f.poly([(x1 - 10.0, top), (x1, top), (x1, foot), (x1 - 10.0, foot)], CABINET_DARK, body=False)
    f.poly([(x0 - 4.0, top - 6.0), (x1 + 4.0, top - 6.0), (x1 + 4.0, top), (x0 - 4.0, top)], CABINET_LIGHT)
    f.poly([(x0 - 3.0, foot - 8.0), (x1 + 3.0, foot - 8.0), (x1 + 3.0, foot), (x0 - 3.0, foot)], CABINET_DARK)
    # The retina: a grid of photocells.
    gx0, gy0, cells, step = 28.0, 32.0, 7, 7.6
    f.poly([(gx0 - 4.0, gy0 - 4.0), (gx0 + cells * step + 2.0, gy0 - 4.0), (gx0 + cells * step + 2.0, gy0 + cells * step + 2.0), (gx0 - 4.0, gy0 + cells * step + 2.0)], K.INK, body=False)
    for row in range(cells):
        for col in range(cells):
            seed = (row * 7 + col * 13 + int(t * 8) * 5) % 11
            on = seed < 4
            if anim == "hit":
                on = True
            elif anim == "death":
                on = on and row >= int(t * (cells + 1))
            f.ellipse(gx0 + col * step + 2.6, gy0 + row * step + 2.6, 2.4, 2.4, CELL_ON if on else CELL_OFF, body=False)
            if on:
                f.glow(gx0 + col * step + 2.6, gy0 + row * step + 2.6, 3.0, K.alpha(CELL_ON, 0.3))
    # The patch board: sockets in rows, wires between them.
    py0 = 98.0
    f.poly([(26.0, py0), (86.0, py0), (86.0, py0 + 44.0), (26.0, py0 + 44.0)], K.shade(CABINET, 0.75), body=False)
    sockets = [(30.0 + 8.0 * c_, py0 + 6.0 + 10.0 * r_) for r_ in range(4) for c_ in range(8)]
    for sx_, sy_ in sockets:
        f.dot(sx_, sy_, 1.4, K.INK)
    for k, (a, b) in enumerate(((0, 27), (3, 12), (6, 17), (9, 30), (14, 24), (20, 5))):
        (ax, ay), (bx, by) = sockets[a], sockets[b]
        sag = 6.0 + 2.0 * k
        f.ink([(ax, ay), ((ax + bx) / 2, max(ay, by) + sag), (bx, by)], 1.4, WIRES[k % len(WIRES)])
    # The answer lamp.
    lamp = CELL_OFF
    if anim == "talk":
        lamp = YES if (i // 2) % 2 == 0 else NO
    elif anim == "hit":
        lamp = NO
    f.ellipse(56.0, 160.0, 8.0, 8.0, K.INK, body=False)
    f.ellipse(56.0, 160.0, 6.0, 6.0, lamp, body=False)
    if lamp != CELL_OFF:
        f.glow(56.0, 160.0, 11.0, K.alpha(lamp, 0.45))
    # Two dials beside it.
    for dx in (-22.0, 22.0):
        f.ellipse(56.0 + dx, 160.0, 5.0, 5.0, CABINET_LIGHT, body=False)
        a = math.radians(-130.0 + 260.0 * ((t + (0.3 if dx > 0 else 0.0)) % 1.0)) if anim != "death" else math.radians(-130.0)
        f.ink([(56.0 + dx, 160.0), (56.0 + dx + 4.0 * math.sin(a), 160.0 - 4.0 * math.cos(a))], 1.2, K.INK)
    return f.finish(outline=K.shade(CABINET_DARK, 0.45), width=1.6)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
