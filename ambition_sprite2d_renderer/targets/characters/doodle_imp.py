"""The Doodle Imp: a scribble of the Art dimension that came alive.

A cat with a grin, drawn by somebody bored in a margin: a round head with
two pointed ears, dots for eyes, a jagged grin, a stick for a body, sticks
for arms and legs, and a tail with an arrow at its end. It is ink on paper,
so its head is the white of a page inside a thick ink line, and the whole
scribble has a thin edge of the page round it, as a drawing cut out of a pad.

Its line boils: each frame draws the line again, a little different, as a
cartoon drawn by hand does. In a fight it grins wider, crouches, and goes
at you claws first; a hit squashes it, and its death is an eraser that
rubs it out.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import List

from . import _art_cast_kit as K

TARGET_NAME = "doodle_imp"
FRAME_SIZE = (96, 96)
ROWS = K.ENEMY_ROWS
GROUND = 93.0

ACTOR_METADATA = K.enemy_metadata(
    TARGET_NAME, "Doodle Imp", "Biped", "Small", "Light", "Walk", ["doodle", "ink", "paper"],
    "A scribble from the margin of a sketchbook in the Art dimension that came alive: a grinning cat of ink on paper. "
    "Fast, one hit, in threes; it swarms and draws more of itself.",
)


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    rng = random.Random(f"{anim}:{i}")
    f = K.Frame(FRAME_SIZE)
    cyc = math.tau * t
    bob, lean, crouch, reach, squash, grin, eyes = 0.0, 0.0, 0.0, 0.0, 0.0, 0.5, "dot"
    stride, arm_up, fade, alarm = 0.0, 0.0, 1.0, False
    if anim == "idle":
        bob = 1.5 * math.sin(cyc)
        arm_up = 0.2 + 0.2 * math.sin(cyc)
    elif anim == "walk":
        bob = -2.0 * abs(math.sin(cyc))
        stride = math.sin(cyc)
        lean = 6.0
    elif anim == "notice":
        bob = -8.0 * math.sin(math.pi * t)
        alarm, eyes, grin = True, "wide", 0.2
    elif anim == "windup":
        crouch, lean, grin, arm_up = 9.0 + 0.6 * math.sin(cyc * 2.0), -10.0, 1.0, 1.0
    elif anim == "attack_side":
        strike = math.sin(math.pi * min(1.0, t * 1.6))
        reach, lean, grin, crouch = 18.0 * strike, 24.0 * strike, 1.0, 4.0 * (1.0 - strike)
        stride = 0.9
    elif anim == "hit":
        squash, eyes, lean, grin = 0.35 * math.sin(math.pi * t) + 0.15, "x", -14.0, 0.0
    elif anim == "death":
        squash, eyes, grin, fade = 0.2, "x", 0.0, 1.0 - t

    hip_y = GROUND - 22.0 + crouch * 0.8 + bob
    hip_x = 40.0 + reach * 0.5
    head_r = 15.0 * (1.0 + squash * 0.3)
    head_ry = 15.0 * (1.0 - squash)
    head_x = hip_x + math.sin(math.radians(lean)) * 22.0 + reach * 0.4
    head_y = hip_y - 20.0 - head_ry + crouch * 0.3 + squash * 10.0

    jitter = 0.9
    # The tail first: it is behind. A curve, and an arrow at its end.
    tail = [(hip_x - 2.0, hip_y), (hip_x - 12.0, hip_y - 4.0 + 3.0 * math.sin(cyc)), (hip_x - 18.0, hip_y - 14.0), (hip_x - 14.0, hip_y - 22.0 + 2.0 * math.cos(cyc))]
    f.limb(tail, 2.0, K.INK)
    tx, ty = tail[-1]
    f.poly([(tx - 4.0, ty + 1.0), (tx + 4.0, ty + 1.0), (tx + 0.5, ty - 6.0)], K.INK)

    # Legs: sticks to the ground, a stride that swings.
    for side in (-1.0, 1.0):
        swing = stride * side
        foot_x = hip_x + 8.0 * swing + side * 3.0 + reach * 0.2
        knee = (hip_x + 4.0 * swing + side * 2.0, hip_y + 10.0 - crouch * 0.4)
        f.limb([(hip_x, hip_y), knee, (foot_x, GROUND - 1.0)], 2.2, K.INK)
        f.limb([(foot_x, GROUND - 1.0), (foot_x + 4.0, GROUND - 1.0)], 2.2, K.INK)
    # The body: one stick from the hip to the neck.
    neck = (head_x - math.sin(math.radians(lean)) * 2.0, head_y + head_ry - 2.0)
    f.limb([(hip_x, hip_y), ((hip_x + neck[0]) / 2.0 + rng.uniform(-0.6, 0.6), (hip_y + neck[1]) / 2.0), neck], 2.4, K.INK)
    # Arms: from the shoulder, up when it is ready, out when it strikes.
    shoulder = ((hip_x * 0.35 + neck[0] * 0.65), (hip_y * 0.35 + neck[1] * 0.65))
    for side in (-1.0, 1.0):
        if reach > 0.0:
            hand = (shoulder[0] + 16.0 + reach * 0.5, shoulder[1] - 2.0 + side * 4.0)
        else:
            hand = (shoulder[0] + side * 12.0 - arm_up * 4.0, shoulder[1] - 4.0 - 12.0 * arm_up + 6.0 * (1.0 - arm_up))
        elbow = ((shoulder[0] + hand[0]) / 2.0 + rng.uniform(-1.0, 1.0), (shoulder[1] + hand[1]) / 2.0 + 3.0)
        f.limb([shoulder, elbow, hand], 2.0, K.INK)
        # Three claws at each hand.
        for k in (-1, 0, 1):
            f.ink([hand, (hand[0] + 4.0, hand[1] + k * 2.6 - 1.0)], 1.1)

    # The head: the white of the page in a wavering line, with two ears.
    for side in (-1.0, 1.0):
        base_x = head_x + side * head_r * 0.55
        ear = [(base_x - 5.0, head_y - head_ry * 0.55), (base_x + 5.0, head_y - head_ry * 0.55), (base_x + side * 3.0 + rng.uniform(-0.8, 0.8), head_y - head_ry - 9.0)]
        f.poly(K.grow(ear, 1.8), K.INK)
        f.poly(ear, K.PAPER)
    f.poly(K.ellipse_points(head_x, head_y, head_r + 1.8, head_ry + 1.8, 22, jitter, rng), K.INK)
    f.poly(K.ellipse_points(head_x, head_y, head_r, head_ry, 22, jitter, rng), K.PAPER)
    # A little hatching on the shade side of the head.
    for k in range(3):
        x0 = head_x - head_r * 0.75 + k * 3.0
        f.ink([(x0, head_y + head_ry * 0.35), (x0 + 3.0, head_y + head_ry * 0.75)], 0.8, K.alpha(K.INK, 0.45))
    ex = head_x + 3.0
    for k, ox in enumerate((-4.5, 5.5)):
        cx, cy = ex + ox, head_y - 3.0
        if eyes == "x":
            f.ink([(cx - 2.2, cy - 2.2), (cx + 2.2, cy + 2.2)], 1.2)
            f.ink([(cx - 2.2, cy + 2.2), (cx + 2.2, cy - 2.2)], 1.2)
        elif eyes == "wide":
            f.ellipse(cx, cy, 3.2, 3.6, K.WHITE, body=False)
            f.dot(cx + 0.6, cy, 1.4)
        else:
            f.dot(cx, cy, 1.9 if k else 1.7)
    # The grin: a zigzag across the face, wider when it means it.
    width = 6.0 + 6.0 * grin
    teeth = 5 if grin > 0.6 else 4
    my = head_y + 5.0
    pts = []
    for k in range(teeth * 2 + 1):
        x = ex - width + 2.0 * width * k / (teeth * 2)
        pts.append((x, my + (2.6 * grin + 0.8 if k % 2 else 0.0) + rng.uniform(-0.3, 0.3)))
    if grin > 0.6:
        f.poly([pts[0]] + pts + [(ex + width, my + 4.0 + 3.0 * grin), (ex - width, my + 4.0 + 3.0 * grin)], K.INK, body=False)
        f.ink(pts, 1.0, K.WHITE)
    else:
        f.ink(pts, 1.3)

    if alarm:
        ax, ay = head_x + head_r + 9.0, max(14.0, head_y - head_ry)
        f.limb([(ax, ay - 10.0), (ax, ay)], 2.6, K.MAGENTA)
        f.ellipse(ax, ay + 5.0, 1.7, 1.7, K.MAGENTA)
    if anim == "attack_side" and t > 0.2:
        # Scratches in the air in front of its claws: the stroke of its blow.
        sx = min(head_x + 18.0 + reach * 0.4, 80.0)
        for k in range(3):
            y0 = head_y - 4.0 + k * 6.0
            f.glow_line([(sx, y0), (sx + 10.0, y0 + 8.0)], 1.6, K.alpha(K.MAGENTA, 0.9 * (1.0 - abs(t - 0.5))))
    if anim == "death":
        # The eraser: crumbs of rubber that fly as it is rubbed out.
        for _ in range(int(10 * t) + 2):
            x, y = rng.uniform(26.0, 70.0), rng.uniform(40.0, GROUND)
            f.ellipse(x, y, 1.4, 1.0, K.alpha(K.MAGENTA_LIGHT, 1.0), body=False)
    # Ink on a page: the outline is the white of the paper round the ink, so
    # the scribble reads on the dark of a cave as on the light of the sky.
    return f.finish(outline=K.PAPER, width=1.5, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
