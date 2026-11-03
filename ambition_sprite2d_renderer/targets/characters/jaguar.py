"""The Jaguar: the great cat of the forests of the Americas (the History dimension).

A stocky, strong cat with a broad head and a deep chest. Its coat is gold
with black rosettes (a broken ring round a deeper gold), a pale belly and
throat, and a long tail with black rings at its end. Its eyes are gold.

It is a pouncer. It pads and swishes its long tail. When it sees you its
ears go up and it bares its teeth. Its windup is a crouch: low, its rump
wiggles, its ears go flat and its tail lashes. Its strike is the pounce: a
long leap with its forepaws out and its jaws open, and it lands on you. A
hit makes it flinch; at its death its legs fold and it lies down.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from . import _art_cast_kit as K
from . import _history_americas_kit as A
from . import _history_felid as F

TARGET_NAME = "jaguar"
FRAME_SIZE = (160, 128)
ROWS = K.ENEMY_ROWS
GROUND = 122.0
#: The middle of the cat on the ground, and its size: the frame must hold
#: its pounce and its tail.
ORIGIN = (70.0, GROUND)
SIZE = 0.96

ACTOR_METADATA = A.enemy_metadata(
    TARGET_NAME, "Jaguar", "first_maize", "Quadruped", "Large", "Medium", "Walk", ["cat", "jaguar", "pounce"],
    "The jaguar of the History dimension's Americas: a stocky gold cat with black rosettes. It crouches low with its "
    "tail lashing, then pounces a long way with its forepaws out.",
)

LOOK = F.Look(
    coat=(232, 172, 64, 255),
    coat_shade=(184, 126, 40, 255),
    belly=(248, 234, 204, 255),
    mark=(42, 30, 26, 255),
    eye=(240, 196, 60, 255),
    nose=(150, 84, 70, 255),
    marks="rosettes",
    tail=40.0,
    muzzle=(246, 210, 140, 255),
    bulk=1.12,
    slope=1.0,
    head=1.3,
    length=44.0,
    depth=1.12,
    seed="jaguar",
)


def _render_frame(anim: str, i: int, n: int):
    pose, alarm, fade = F.pose_for(anim, i, n)
    f = A.ScaledFrame(FRAME_SIZE, SIZE, ORIGIN)
    top = F.draw(f, LOOK, pose, ORIGIN)
    if anim == "death" and K.phase(i, n, False) > 0.3:
        A.dust(f, ORIGIN[0], GROUND - 5.0, 24.0, min(1.0, (K.phase(i, n, False) - 0.3) * 2.0), f"jaguar:death:{i}")
    if anim == "attack_side" and i >= n - 2:
        A.dust(f, ORIGIN[0] + 22.0, GROUND - 5.0, 16.0, 0.7, f"jaguar:land:{i}")
    out = A.finish(f, fade=fade)
    if alarm:
        g = K.Frame(FRAME_SIZE)
        A.alarm_mark(g, min(150.0, ORIGIN[0] + (top[0] - ORIGIN[0]) * SIZE + 10.0), 18.0)
        out.alpha_composite(A.finish(g))
    return out


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
