"""The Smilodon: the sabre-toothed cat of Ice Age America.

A big, heavy cat, built more like a bear than a lion: thick forelegs and a
deep chest, shoulders higher than its hips, and a short bobbed tail. Its
coat is a plain tawny with faint dapples and a pale belly. Two long flat
sabres come down out of its upper jaw, past its chin.

It is a pouncer. It pads about and swishes its stub of a tail. When it sees
you it lifts its head and shows its sabres. Its windup is a crouch: low on
its belly, its rump wiggles and its ears go flat. Its strike is the pounce:
a long leap, forepaws out, its jaw open wider than any cat's, and it lands
on you. A hit makes it snarl and flinch; at its death its legs fold and it
lies down.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from . import _art_cast_kit as K
from . import _history_americas_kit as A
from . import _history_felid as F

TARGET_NAME = "smilodon"
FRAME_SIZE = (192, 128)
ROWS = K.ENEMY_ROWS
GROUND = 122.0
#: The middle of the cat on the ground, and its size: the frame must hold
#: its pounce.
ORIGIN = (78.0, GROUND)
SIZE = 1.18

ACTOR_METADATA = A.enemy_metadata(
    TARGET_NAME, "Smilodon", "beringia", "Quadruped", "Large", "Heavy", "Walk", ["cat", "sabre", "pounce"],
    "The sabre-toothed cat of the History dimension's Ice Age Americas: a heavy tawny cat with two long sabres. It "
    "crouches low with its rump wiggling, then pounces a long way with its jaw open wide.",
)

LOOK = F.Look(
    coat=(204, 150, 86, 255),
    coat_shade=(160, 110, 58, 255),
    belly=(240, 222, 186, 255),
    mark=(150, 100, 52, 255),
    eye=(232, 190, 70, 255),
    marks="dapples",
    tail=13.0,
    sabre=16.0,
    bulk=1.25,
    slope=4.0,
    head=1.36,
    length=42.0,
    depth=1.22,
    seed="smilodon",
)


def _render_frame(anim: str, i: int, n: int):
    pose, alarm, fade = F.pose_for(anim, i, n)
    if anim == "notice":
        # It shows its sabres: the jaw drops a long way.
        pose.jaw = min(1.0, pose.jaw * 2.4)
    f = A.ScaledFrame(FRAME_SIZE, SIZE, ORIGIN)
    top = F.draw(f, LOOK, pose, ORIGIN)
    if anim == "death" and K.phase(i, n, False) > 0.3:
        A.dust(f, ORIGIN[0], GROUND - 5.0, 26.0, min(1.0, (K.phase(i, n, False) - 0.3) * 2.0), f"smilodon:death:{i}")
    if anim == "attack_side" and i >= n - 2:
        A.dust(f, ORIGIN[0] + 24.0, GROUND - 5.0, 18.0, 0.7, f"smilodon:land:{i}")
    out = A.finish(f, fade=fade)
    if alarm:
        g = K.Frame(FRAME_SIZE)
        A.alarm_mark(g, min(180.0, ORIGIN[0] + (top[0] - ORIGIN[0]) * SIZE + 10.0), 18.0)
        out.alpha_composite(A.finish(g))
    return out


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
