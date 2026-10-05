#!/usr/bin/env python3
"""Build the raptor stalker's rig document from its SVG.

The SVG ``data/characters/raptor_stalker/raptor_stalker.svg`` owns the art and says where
every joint is; ``rigbuild.creature_rig``, with the ``theropod`` anatomy,
derives the skeleton from it, binds every part to its bone, and refreshes the
SVG's rig catalog. This script supplies only what the drawing cannot state:
the frame, the rows and the clips. It never draws.

    uv run python scripts/build_raptor_stalker_rig.py

The clips keep the sheet contract the game already reads: the same seven
rows, frame counts and durations as before the SVG redesign.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Callable, Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ambition_sprite2d_renderer.rigbuild import theropod as T  # noqa: E402
from ambition_sprite2d_renderer.rigbuild.theropod import Pose, eyes, track  # noqa: E402

PKG = ROOT / "ambition_sprite2d_renderer"

#: Where each foot plants, from the drawing's centre (SVG units).
NEAR_X = -6.0
FAR_X = -22.0


def tail(values: List[List[float]], t: float, scale: float = 1.0) -> Pose:
    """The four tail bones from four key rows."""
    return {f"tail{i + 1}": track(row, t) * scale for i, row in enumerate(values)}


def idle(i: int, n: int, t: float) -> Pose:
    w = math.tau * t
    breath = math.sin(w)
    p: Pose = {
        "root_y": 1.4 * breath,
        "pelvis": -0.8 * breath,
        "torso": 1.0 * breath,
        "neck": -2.4 * math.sin(w - 0.5),
        # A bird's head: it holds, then cocks, then holds.
        "head": track([0, 0, 7, 7, -3, 0, 0], t),
        "jaw": 2.0 + 2.0 * max(0.0, math.sin(w * 2.0)),
        "near_arm_u": 3.0 * math.sin(w - 0.3),
        "near_arm_l": 4.0 * math.sin(w - 0.9),
        "far_arm_u": 3.0 * math.sin(w - 0.6),
        "far_arm_l": 4.0 * math.sin(w - 1.2),
    }
    for k in range(4):
        p[f"tail{k + 1}"] = (1.5 + 1.0 * k) * math.sin(w - 0.7 * (k + 1))
    p.update(eyes("shut" if i == 4 else "open"))
    return p


def walk(i: int, n: int, t: float) -> Pose:
    """A low, quick stalking run (the game binds it to ``locomotion.run``)."""
    p = T.gait(t, near_x=NEAR_X, far_x=FAR_X, stride=30.0, lift=24.0, bob=6.0, sway=2.0, tail=2.5, arm=4.0)
    p["pelvis"] += 5.0
    p["neck"] += 8.0
    p["head"] -= 6.0
    p["near_arm_u"] -= 12.0
    p["far_arm_u"] -= 12.0
    p["jaw"] = 3.0
    p.update(eyes("angry"))
    return p


def bite(i: int, n: int, t: float) -> Pose:
    p: Pose = {
        "root_x": track([0, -10, 16, 22, 12, 4, 0], t),
        "root_y": track([0, 5, 2, 2, 1, 0, 0], t),
        "pelvis": track([0, -5, 8, 10, 5, 2, 0], t),
        "torso": track([0, -2, 3, 3, 2, 0, 0], t),
        "neck": track([0, -18, 14, 18, 8, 2, 0], t),
        "head": track([0, -6, -4, 0, 2, 0, 0], t),
        "jaw": track([2, 26, 38, 2, 8, 4, 2], t),
        "near_foot_x": track([NEAR_X, NEAR_X + 6, NEAR_X + 18, NEAR_X + 18, NEAR_X + 18, NEAR_X + 8, NEAR_X], t),
        "near_foot_lift": track([0, 10, 0, 0, 0, 6, 0], t),
        "near_arm_u": track([0, 10, -40, -46, -28, -10, 0], t),
        "near_arm_l": track([0, 8, -20, -26, -14, -4, 0], t),
        "far_arm_u": track([0, 8, -36, -42, -24, -8, 0], t),
        "far_arm_l": track([0, 6, -18, -22, -12, -4, 0], t),
        "fx.bite": track([0, 0, 0.35, 1, 0.3, 0, 0], t),
    }
    p.update(tail([[0, 6, -6, -4, -2, 0, 0], [0, 8, -8, -6, -2, 0, 0], [0, 10, -10, -8, -3, 0, 0],
                   [0, 12, -12, -10, -4, 0, 0]], t))
    p.update(eyes("angry" if 0.1 < t < 0.9 else "open"))
    return p


def tail_sweep(i: int, n: int, t: float) -> Pose:
    p: Pose = {
        "root_x": track([0, 4, -8, -12, -8, -3, 0], t),
        "root_y": track([0, 3, 4, 3, 2, 1, 0], t),
        "pelvis": track([0, -5, 9, 11, 6, 2, 0], t),
        "torso": track([0, -2, 2, 3, 1, 0, 0], t),
        "neck": track([0, -8, 10, 12, 5, 1, 0], t),
        "head": track([0, 4, -6, -6, -2, 0, 0], t),
        "jaw": track([2, 8, 14, 16, 8, 4, 2], t),
        "far_foot_x": track([FAR_X, FAR_X - 10, FAR_X - 14, FAR_X - 14, FAR_X - 14, FAR_X - 6, FAR_X], t),
        "far_foot_lift": track([0, 10, 0, 0, 0, 0, 0], t),
        "near_arm_u": track([0, -8, -20, -24, -14, -4, 0], t),
        "far_arm_u": track([0, -6, -18, -22, -12, -4, 0], t),
        "fx.sweep": track([0, 0, 0.7, 1, 0.5, 0.05, 0], t),
    }
    p.update(tail([[0, -8, 10, 14, 6, 2, 0], [0, -10, 14, 18, 8, 2, 0], [0, -12, 16, 22, 10, 3, 0],
                   [0, -12, 18, 24, 12, 4, 0]], t))
    p.update(eyes("angry" if 0.1 < t < 0.9 else "open"))
    return p


def pounce(i: int, n: int, t: float) -> Pose:
    """Crouch, leap with the sickle claws thrown forward, land."""
    p: Pose = {
        "root_x": track([0, -6, -10, 4, 14, 20, 18, 10], t),
        "root_y": track([0, 12, 20, -18, -48, -38, 8, 0], t),
        "pelvis": track([0, 5, 7, -12, -8, 4, 6, 0], t),
        "torso": track([0, 2, 3, -3, -2, 2, 2, 0], t),
        "neck": track([0, 8, 10, -10, -4, 8, 6, 0], t),
        "head": track([0, -4, -6, 4, 2, -4, -2, 0], t),
        "jaw": track([2, 4, 6, 20, 28, 30, 10, 2], t),
        # Airborne, the feet tuck up under the body and swing forward so the
        # sickle claws lead (a foot's lift is from the ground, so it climbs
        # with the body).
        "near_foot_x": track([NEAR_X, NEAR_X, NEAR_X, NEAR_X + 6, NEAR_X + 46, NEAR_X + 52, NEAR_X + 24, NEAR_X + 10], t),
        "near_foot_lift": track([0, 0, 0, 4, 88, 70, 0, 0], t),
        "near_foot_pitch": track([0, 0, 0, 0, -34, -40, -6, 0], t),
        "far_foot_x": track([FAR_X, FAR_X, FAR_X, FAR_X - 2, FAR_X + 38, FAR_X + 46, FAR_X + 18, FAR_X + 10], t),
        "far_foot_lift": track([0, 0, 0, 2, 80, 64, 0, 0], t),
        "far_foot_pitch": track([0, 0, 0, 0, -30, -36, -4, 0], t),
        # The arms flare as wings for balance.
        "near_arm_u": track([0, 6, 8, -30, -52, -40, -10, 0], t),
        "near_arm_l": track([0, 4, 6, -20, -30, -20, -6, 0], t),
        "far_arm_u": track([0, 6, 8, -26, -46, -36, -8, 0], t),
        "far_arm_l": track([0, 4, 6, -18, -26, -18, -4, 0], t),
        "fx.dust": track([0, 0, 0.3, 1, 0.3, 0, 0.9, 0.3], t),
        "fx.rake": track([0, 0, 0, 0, 0.8, 1, 0.2, 0], t),
    }
    p.update(tail([[0, -4, -6, 10, 6, -4, -6, 0], [0, -4, -8, 12, 8, -4, -8, 0], [0, -4, -8, 14, 10, -4, -8, 0],
                   [0, -4, -8, 16, 12, -4, -8, 0]], t))
    p.update(eyes("angry" if 0.05 < t < 0.95 else "open"))
    return p


def hurt(i: int, n: int, t: float) -> Pose:
    p: Pose = {
        "root_x": track([0, -12, -6, -2], t),
        "root_y": track([0, -2, 1, 0], t),
        "pelvis": track([0, -9, -4, -1], t),
        "torso": track([0, -3, -1, 0], t),
        "neck": track([0, -14, -6, -2], t),
        "head": track([0, -14, -5, 0], t),
        "jaw": track([2, 24, 12, 3], t),
        "near_arm_u": track([0, -34, -14, -2], t),
        "near_arm_l": track([0, -16, -6, 0], t),
        "far_arm_u": track([0, -30, -12, -2], t),
        "far_arm_l": track([0, -14, -6, 0], t),
        "fx.hit": track([0, 1, 0.35, 0], t),
    }
    p.update(tail([[0, 10, 4, 0], [0, 12, 5, 0], [0, 14, 6, 0], [0, 16, 8, 0]], t))
    p.update(eyes("shut" if 0.2 < t < 0.8 else "open"))
    return p


def death(i: int, n: int, t: float) -> Pose:
    p: Pose = {
        "root_x": track([0, -8, -10, -8, -4, -2, -2, -2], t),
        "root_y": track([0, -4, 16, 40, 60, 63, 63, 63], t),
        "pelvis": track([0, -9, 2, 8, 6, 4, 4, 4], t),
        "torso": track([0, -3, 2, 4, 3, 2, 2, 2], t),
        "neck": track([0, -20, -6, 8, 16, 19, 20, 20], t),
        "head": track([0, -10, -2, 6, 8, 10, 10, 10], t),
        "jaw": track([2, 28, 20, 14, 12, 10, 9, 9], t),
        "near_foot_x": track([NEAR_X, NEAR_X, NEAR_X + 4, NEAR_X + 10, NEAR_X + 14, NEAR_X + 14, NEAR_X + 14, NEAR_X + 14], t),
        "far_foot_x": track([FAR_X, FAR_X, FAR_X + 2, FAR_X + 8, FAR_X + 12, FAR_X + 12, FAR_X + 12, FAR_X + 12], t),
        "near_arm_u": track([0, -30, -10, 10, 20, 24, 24, 24], t),
        "near_arm_l": track([0, -10, 0, 10, 16, 18, 18, 18], t),
        "far_arm_u": track([0, -26, -8, 10, 18, 22, 22, 22], t),
        "far_arm_l": track([0, -8, 2, 10, 14, 16, 16, 16], t),
        "fx.thud": track([0, 0, 0, 0, 1, 0.5, 0, 0], t),
    }
    p.update(tail([[0, -6, -8, -8, -6, -4, -4, -4], [0, -6, -8, -6, -2, 0, 0, 0], [0, -6, -6, -4, 2, 4, 4, 4],
                   [0, -6, -4, -2, 4, 6, 6, 6]], t))
    p.update(eyes("dead" if t > 0.6 else "shut" if t > 0.1 else "open"))
    return p


CLIPS: Dict[str, Callable[[int, int, float], Pose]] = {
    "idle": idle,
    "walk": walk,
    "bite": bite,
    "tail_sweep": tail_sweep,
    "pounce": pounce,
    "hurt": hurt,
    "death": death,
}

DEFAULTS: Pose = {
    "near_foot_x": NEAR_X,
    "far_foot_x": FAR_X,
    "eye.open": 1.0,
    "jaw": 2.0,
}

SPEC = T.theropod_spec(
    name="raptor_stalker",
    svg_path=PKG / "data" / "characters" / "raptor_stalker" / "raptor_stalker.svg",
    rig_path=PKG / "targets" / "characters" / "rigged" / "raptor_stalker" / "raptor_stalker_side.rig.json",
    view_label="Raptor - Side Right",
    # Drawn at 600x400 units, published at the size the raptor always had.
    scale=0.38,
    svg_center_x=300.0,
    svg_ground_y=372.0,
    frame_size=(228, 152),
    rows=[
        ("idle", 6, 130, True),
        ("walk", 8, 95, True),
        ("bite", 7, 80, False),
        ("tail_sweep", 7, 85, False),
        ("pounce", 8, 85, False),
        ("hurt", 4, 90, False),
        ("death", 8, 110, False),
    ],
    clips=CLIPS,
    defaults=DEFAULTS,
    jaw_length=40.0,
)


def main(argv: List[str] | None = None) -> int:
    del argv
    for path in T.write(SPEC):
        print(path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
