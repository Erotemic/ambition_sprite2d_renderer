"""The Origami Bird: a paper crane of the Art dimension that flies.

A crane folded from one square of paper: a body of two long faces, a neck
and a tail that go up to points, a head folded down at the end of the
neck, and two wings of flat triangles. Each face is a flat colour, lit or
in shade, with a crease along each fold; the paper is printed pink and
cyan on one side, as a sheet of origami paper is.

It flies with slow beats of flat wings. It does not attack first: when it
is struck, it pitches its nose down, flares its wings and dives. Its death
is an unfolding: the crane opens out into its square and falls.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List

from . import _art_cast_kit as K

TARGET_NAME = "origami_bird"
FRAME_SIZE = (96, 96)
ROWS = K.ENEMY_ROWS

ACTOR_METADATA = K.enemy_metadata(
    TARGET_NAME, "Origami Bird", "Avian", "Small", "Light", "Fly", ["paper", "flying", "neutral"],
    "A paper crane of the Art dimension, folded from one square, that flies. It does not attack first; struck, it "
    "dives at whoever struck it. Some carry things, and some show the way.",
)

FACE = (252, 244, 248, 255)
FACE_SHADE = (214, 196, 222, 255)
PRINT = (246, 120, 196, 255)
PRINT_SHADE = (196, 70, 150, 255)
WING_UNDER = (120, 214, 240, 255)


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = K.Frame(FRAME_SIZE)
    cx, cy = 42.0, 52.0
    beat = math.sin(cyc)
    pitch, flap, unfold, fade = 0.0, beat, 0.0, 1.0
    if anim == "idle":
        cy += 2.0 * math.sin(cyc)
        flap = 0.6 * beat
    elif anim == "walk":
        cy += 3.0 * math.sin(cyc + 0.6)
        flap = beat
        pitch = 6.0
    elif anim == "notice":
        flap, cy = 1.0 - 2.0 * t, cy - 4.0 * math.sin(math.pi * t)
        pitch = -12.0 * math.sin(math.pi * t)
    elif anim == "windup":
        pitch, flap = 46.0, -0.9 + 0.08 * math.sin(cyc * 2.0)
    elif anim == "attack_side":
        pitch, flap = 50.0 - 40.0 * t, -0.6
        cx += 10.0 * math.sin(math.pi * t)
        cy += 14.0 * math.sin(math.pi * t)
    elif anim == "hit":
        pitch, flap = -24.0, 0.3
    elif anim == "death":
        unfold, cy = t, cy + 30.0 * t * t
        fade = 1.0 - max(0.0, t - 0.7) / 0.3

    if unfold > 0.0:
        # The crane opens out into its square of paper, turning as it falls.
        s = 14.0 + 14.0 * unfold
        square = K.turn([(cx - s, cy), (cx, cy - s * 0.6), (cx + s, cy), (cx, cy + s * 0.6)], cx, cy, 40.0 * unfold)
        f.poly(square, K.alpha(FACE, 1.0))
        f.poly([square[0], square[1], (cx, cy)], PRINT, body=False)
        f.poly([square[2], square[3], (cx, cy)], PRINT_SHADE, body=False)
        for a, b in ((square[0], square[2]), (square[1], square[3])):
            f.ink([a, b], 0.6, K.alpha(K.INK, 0.5))
        return f.finish(width=1.2, fade=fade)

    def at(points):
        return K.turn(points, cx, cy, pitch)

    # The far wing first (behind the body): a triangle up or down with the beat.
    lift = -30.0 * flap
    far = at([(cx - 9.0, cy - 2.0), (cx + 9.0, cy - 2.0), (cx - 8.0 + 6.0 * flap, cy - 6.0 + lift * 0.85)])
    f.poly(far, PRINT_SHADE)
    # The tail and the neck: long points up and back, up and forward.
    tail = at([(cx - 6.0, cy + 2.0), (cx - 4.0, cy - 2.0), (cx - 32.0, cy - 16.0)])
    f.poly(tail, FACE_SHADE)
    neck = at([(cx + 6.0, cy + 2.0), (cx + 4.0, cy - 2.0), (cx + 30.0, cy - 20.0)])
    f.poly(neck, FACE)
    head = at([(cx + 30.0, cy - 20.0), (cx + 27.0, cy - 17.0), (cx + 38.0, cy - 13.0)])
    f.poly(head, PRINT)
    # The body: two faces that meet along the keel.
    f.poly(at([(cx - 12.0, cy), (cx + 12.0, cy), (cx, cy + 11.0)]), FACE)
    f.poly(at([(cx - 12.0, cy), (cx, cy + 11.0), (cx - 3.0, cy + 2.0)]), FACE_SHADE, body=False)
    # The near wing, over the body, its printed side out when it is up.
    near = at([(cx - 10.0, cy), (cx + 11.0, cy), (cx - 4.0 + 8.0 * flap, cy + 3.0 + lift)])
    f.poly(near, PRINT if flap > 0 else WING_UNDER)
    crease = at([(cx + 1.0, cy), (cx - 4.0 + 8.0 * flap, cy + 3.0 + lift)])
    f.ink(crease, 0.7, K.alpha(K.INK, 0.6))
    for edge in (at([(cx - 4.0, cy - 2.0), (cx - 32.0, cy - 16.0)]), at([(cx + 4.0, cy - 2.0), (cx + 30.0, cy - 20.0)]), at([(cx - 10.0, cy), (cx + 10.0, cy)])):
        f.ink(edge, 0.6, K.alpha(K.INK, 0.45))
    eye = at([(cx + 31.5, cy - 17.0)])[0]
    f.dot(eye[0], eye[1], 0.9)
    if anim == "notice":
        f.ink([(cx + 40.0, cy - 30.0), (cx + 40.0, cy - 24.0)], 1.6, K.CYAN)
        f.dot(cx + 40.0, cy - 21.0, 1.0, K.CYAN)
    if anim == "attack_side":
        for k in range(3):
            y0 = cy - 8.0 + k * 6.0
            f.glow_line([(cx - 28.0 - k * 3.0, y0 - 6.0), (cx - 14.0, y0)], 1.2, K.alpha(K.CYAN_LIGHT, 0.7))
    return f.finish(width=1.3, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
