"""The Attention Head: an eye on rotors that watches the Weights (the Neural
dimension, gate address LATENT).

A round red eye in a dark shell, a ring of targeting brackets round it, two
small rotors on arms over it and a stub of an antenna. It hovers, turns to
what it is looking at, and fires a bolt at it. Its windup is a focus: the
brackets close in and the pupil narrows. A hit makes it blink and wobble;
its death is a spin and a fall, the eye going out.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List

from . import _art_cast_kit as K

TARGET_NAME = "attention_head"
FRAME_SIZE = (96, 96)
ROWS = K.ENEMY_ROWS

ACTOR_METADATA = K.enemy_metadata(
    TARGET_NAME, "Attention Head", "Drone", "Small", "Light", "Float", ["eye", "floating", "machine"],
    "An eye on rotors in the Weights of the Neural dimension: a red eye in a dark shell with targeting brackets round it. "
    "It hovers, watches what it attends to, and fires at it.",
)
ACTOR_METADATA["tags"] = ["enemy", "neural"]

SHELL = (52, 50, 72, 255)
SHELL_LIGHT = (120, 118, 150, 255)
IRIS = (226, 40, 64, 255)
IRIS_LIGHT = (255, 120, 130, 255)
SCLERA = (244, 236, 236, 255)
BRACKET = (255, 80, 90, 255)


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = K.Frame(FRAME_SIZE)
    cx, cy, r = 48.0, 50.0, 15.0
    look, pupil, tilt, brackets, fade, lid = 2.0, 4.0, 0.0, 1.0, 1.0, 0.0
    if anim == "idle":
        cy += 2.0 * math.sin(cyc)
        look = 2.0 * math.sin(cyc * 0.5)
    elif anim == "walk":
        cy += 1.5 * math.sin(cyc * 2.0)
        tilt = 8.0
        look = 4.0
    elif anim == "notice":
        pupil = 5.0 + 1.5 * math.sin(math.pi * t)
        brackets = 1.3 - 0.3 * t
        look = 4.0
    elif anim == "windup":
        pupil = 2.4
        brackets = 0.72 + 0.04 * math.sin(cyc * 3.0)
        look = 4.5
    elif anim == "attack_side":
        strike = math.sin(math.pi * min(1.0, t * 1.5))
        pupil = 2.2
        brackets = 0.7
        look = 5.0
        tilt = -6.0 * strike
        cx -= 3.0 * strike
    elif anim == "hit":
        lid = 0.8
        tilt = 14.0 * math.sin(cyc * 2.0)
    elif anim == "death":
        tilt = 280.0 * t
        cy += 30.0 * t * t
        lid = min(1.0, t * 1.3)
        fade = 1.0 - max(0.0, t - 0.6) / 0.4
    # The rotors on their arms, over the shell.
    blur = abs(math.sin(cyc * 6.0))
    for side in (-1.0, 1.0):
        ax, ay = cx + side * 15.0, cy - 14.0
        f.limb(K.turn([(cx + side * 6.0, cy - 8.0), (ax, ay)], cx, cy, tilt), 3.0, SHELL)
        hub = K.turn([(ax, ay - 2.0)], cx, cy, tilt)[0]
        f.ellipse(hub[0], hub[1], 11.0, 2.0 + 1.5 * blur, K.alpha(SHELL_LIGHT, 0.75))
        f.dot(hub[0], hub[1], 1.6, SHELL)
    # The antenna.
    f.limb(K.turn([(cx - 4.0, cy - r + 2.0), (cx - 8.0, cy - r - 8.0)], cx, cy, tilt), 1.6, SHELL)
    tip = K.turn([(cx - 8.0, cy - r - 9.0)], cx, cy, tilt)[0]
    f.dot(tip[0], tip[1], 1.8, IRIS)
    # The shell and the eye.
    f.ellipse(cx, cy, r, r, SHELL)
    f.ellipse(cx - 3.0, cy - 4.0, r * 0.5, r * 0.35, K.alpha(SHELL_LIGHT, 0.6), body=False)
    f.ellipse(cx + look * 0.4, cy, r * 0.72, r * 0.72, SCLERA, body=False)
    f.ellipse(cx + look, cy, pupil + 3.0, pupil + 3.0, IRIS, body=False)
    f.dot(cx + look, cy, pupil * 0.6, K.INK)
    f.dot(cx + look - 1.5, cy - 1.8, 1.2, IRIS_LIGHT)
    if lid > 0.0:
        f.poly([(cx - r * 0.75, cy - r * 0.75), (cx + r * 0.75, cy - r * 0.75), (cx + r * 0.75, cy - r * 0.75 + r * 1.5 * lid), (cx - r * 0.75, cy - r * 0.75 + r * 1.5 * lid)], SHELL, body=False)
    # The brackets of its attention: four corners round the eye.
    d = (r + 7.0) * brackets
    for sxn, syn in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        x, y = cx + sxn * d, cy + syn * d
        f.ink([(x, y - syn * 5.0), (x, y), (x - sxn * 5.0, y)], 1.6, K.alpha(BRACKET, fade))
    if anim == "attack_side" and t > 0.2:
        bx = cx + r + 6.0 + 28.0 * (t - 0.2)
        f.limb([(bx - 8.0, cy), (bx + 4.0, cy)], 3.0, IRIS)
        f.glow(bx, cy, 6.0, K.alpha(IRIS_LIGHT, 0.6))
    f.glow(cx + look, cy, 7.0, K.alpha(IRIS, 0.35 * fade))
    return f.finish(outline=K.shade(SHELL, 0.5), width=1.4, glow_blur=2.5, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
