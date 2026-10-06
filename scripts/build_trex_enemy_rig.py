#!/usr/bin/env python3
"""Build the T-rex boss's rig document from its SVG.

The SVG ``data/characters/trex_enemy/trex_enemy.svg`` owns the art and says where
every joint is; ``rigbuild.creature_rig``, with the ``theropod`` anatomy,
derives the skeleton from it, binds every part to its bone, and refreshes the
SVG's rig catalog. This script supplies only what the drawing cannot state:
the frame, the rows and the clips. It never draws.

    uv run python scripts/build_trex_enemy_rig.py

The clips keep the sheet contract the game already reads: the first nine rows,
frame counts and durations are those from before the SVG redesign; the boss
rework appended ``stunned``, ``snap_up`` and ``leap``.
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
NEAR_X = 2.0
FAR_X = -14.0


def gait(t: float, **kw) -> Pose:
    return T.gait(t, near_x=NEAR_X, far_x=FAR_X, **kw)


def idle(i: int, n: int, t: float) -> Pose:
    w = math.tau * t
    breath = math.sin(w)
    p: Pose = {
        "root_y": 1.6 * breath,
        "pelvis": -0.6 * breath,
        "torso": 0.8 * breath,
        "neck": -1.8 * math.sin(w - 0.5),
        "head": 1.4 * math.sin(w - 1.0),
        "jaw": 3.0 + 3.0 * max(0.0, math.sin(w - 0.4)),
        "near_arm_u": 4.0 * math.sin(w - 0.3),
        "near_arm_l": 5.0 * math.sin(w - 0.9),
        "far_arm_u": 3.0 * math.sin(w - 0.6),
        "far_arm_l": 4.0 * math.sin(w - 1.2),
    }
    for k in range(4):
        p[f"tail{k + 1}"] = (1.5 + 0.8 * k) * math.sin(w - 0.6 * (k + 1))
    p.update(eyes("shut" if i == n - 1 else "open"))
    return p


def walk(i: int, n: int, t: float) -> Pose:
    p = gait(t, stride=24.0, lift=18.0, bob=4.0, sway=1.6, tail=4.0)
    p["jaw"] = 3.0
    p.update(eyes("open"))
    return p


def charge(i: int, n: int, t: float) -> Pose:
    p = gait(t, stride=36.0, lift=26.0, bob=7.0, sway=2.4, tail=6.0)
    w = math.tau * t
    p["root_x"] = 10.0
    p["root_y"] += 4.0
    p["pelvis"] += 9.0
    p["torso"] += 2.0
    p["neck"] += 12.0
    p["head"] += -8.0 + 2.0 * math.sin(w)
    p["jaw"] = 10.0 + 6.0 * max(0.0, math.sin(w * 2.0))
    for k in range(4):
        p[f"tail{k + 1}"] -= 2.0 + k
    p["near_arm_u"] -= 18.0
    p["far_arm_u"] -= 18.0
    # Dust kicks up as each foot strikes (twice a cycle).
    p["fx.dust"] = 0.35 + 0.65 * abs(math.cos(w))
    p.update(eyes("angry"))
    return p


def bite(i: int, n: int, t: float) -> Pose:
    p: Pose = {
        "root_x": track([0, -12, 18, 28, 16, 6, 0], t),
        "root_y": track([0, -2, 4, 6, 3, 1, 0], t),
        "pelvis": track([0, -6, 8, 11, 6, 2, 0], t),
        "torso": track([0, -2, 3, 4, 2, 0, 0], t),
        "neck": track([0, -18, 10, 16, 8, 2, 0], t),
        "head": track([0, -10, 2, 2, 1, 0, 0], t),
        "jaw": track([3, 28, 40, 2, 8, 5, 3], t),
        "near_foot_x": track([NEAR_X, 10, 24, 24, 24, 12, NEAR_X], t),
        "near_foot_lift": track([0, 12, 0, 0, 0, 8, 0], t),
        "tail1": track([0, 6, -6, -4, -2, 0, 0], t),
        "tail2": track([0, 8, -8, -6, -2, 0, 0], t),
        "tail3": track([0, 10, -10, -8, -3, 0, 0], t),
        "tail4": track([0, 12, -14, -10, -4, 0, 0], t),
        "near_arm_u": track([0, -14, -26, -20, -10, -4, 0], t),
        "far_arm_u": track([0, -12, -24, -18, -8, -2, 0], t),
        "fx.bite": track([0, 0, 0.35, 1, 0.3, 0, 0], t),
    }
    p.update(eyes("angry" if 0.1 < t < 0.9 else "open"))
    return p


def roar(i: int, n: int, t: float) -> Pose:
    shake = (1.0 if i % 2 else -1.0) * (1.5 if i in (2, 3, 4) else 0.0)
    p: Pose = {
        "root_x": track([0, -8, 4, 6, 4, 0], t) + shake,
        "root_y": track([0, -3, 4, 5, 3, 0], t),
        "pelvis": track([0, -8, 5, 6, 4, 0], t),
        "torso": track([0, -3, 2, 3, 2, 0], t),
        "neck": track([0, -20, 4, 6, 2, 0], t),
        "head": track([0, -10, -10, -10, -6, 0], t),
        "jaw": track([3, 12, 40, 42, 34, 4], t),
        "tail1": track([0, -6, 6, 7, 4, 0], t),
        "tail2": track([0, -6, 8, 9, 5, 0], t),
        "tail3": track([0, -6, 10, 11, 6, 0], t),
        "tail4": track([0, -6, 12, 14, 8, 0], t),
        "near_arm_u": track([0, -20, -34, -36, -24, 0], t),
        "near_arm_l": track([0, -10, -20, -22, -12, 0], t),
        "far_arm_u": track([0, -18, -30, -32, -20, 0], t),
        "far_arm_l": track([0, -8, -18, -20, -10, 0], t),
        "near_foot_x": NEAR_X + 4.0,
        "fx.roar": track([0, 0, 0.75, 1, 0.8, 0], t),
    }
    p.update(eyes("angry" if 0.1 < t < 0.95 else "open"))
    return p


def tail_swipe(i: int, n: int, t: float) -> Pose:
    p: Pose = {
        "root_x": track([0, 8, 2, -12, -12, -5, 0], t),
        "root_y": track([0, 2, 4, 3, 2, 1, 0], t),
        "pelvis": track([0, 9, 4, -7, -6, -2, 0], t),
        "torso": track([0, 2, 1, -2, -2, 0, 0], t),
        "neck": track([0, 10, 6, -8, -8, -3, 0], t),
        "head": track([0, -4, -2, 4, 4, 1, 0], t),
        "jaw": track([3, 10, 16, 18, 10, 5, 3], t),
        "tail1": track([0, 14, 6, -8, -10, -4, 0], t),
        "tail2": track([0, 16, 2, -10, -12, -5, 0], t),
        "tail3": track([0, 16, -4, -12, -14, -6, 0], t),
        "tail4": track([0, 14, -10, -14, -16, -8, 0], t),
        "near_foot_x": track([NEAR_X, NEAR_X, 8, 8, 8, 4, NEAR_X], t),
        "far_foot_x": track([FAR_X, FAR_X - 10, FAR_X - 14, FAR_X - 14, FAR_X - 14, FAR_X - 6, FAR_X], t),
        "far_foot_lift": track([0, 10, 0, 0, 0, 0, 0], t),
        "near_arm_u": track([0, -10, -16, -12, -8, -2, 0], t),
        "fx.swipe": track([0, 0, 0.55, 1, 0.6, 0.1, 0], t),
    }
    p.update(eyes("angry" if 0.1 < t < 0.9 else "open"))
    return p


def stomp(i: int, n: int, t: float) -> Pose:
    p: Pose = {
        # He rears back onto the far leg, the near foot raised high (the
        # tell), then drives it down with his whole weight.
        "root_x": track([0, -4, 12, 12, 6, 0], t),
        "root_y": track([0, -8, 10, 9, 3, 0], t),
        "pelvis": track([0, -5, 7, 6, 2, 0], t),
        "torso": track([0, -2, 4, 3, 1, 0], t),
        "neck": track([0, -12, 12, 9, 3, 0], t),
        "head": track([0, -6, 6, 3, 1, 0], t),
        "jaw": track([3, 18, 30, 20, 8, 3], t),
        "near_foot_x": track([NEAR_X, 18, 28, 28, 14, NEAR_X], t),
        "near_foot_lift": track([0, 72, 0, 0, 10, 0], t),
        "near_foot_pitch": track([0, 22, 0, 0, 4, 0], t),
        "near_arm_u": track([0, -24, 6, 4, 0, 0], t),
        "far_arm_u": track([0, -20, 8, 6, 0, 0], t),
        "tail1": track([0, -8, 6, 4, 1, 0], t),
        "tail2": track([0, -8, 8, 5, 1, 0], t),
        "tail3": track([0, -8, 10, 6, 2, 0], t),
        "tail4": track([0, -8, 12, 8, 2, 0], t),
        "fx.stomp": track([0, 0, 0.7, 1, 0.45, 0], t),
        "fx.dust": track([0, 0, 0.8, 1, 0.6, 0.15], t),
    }
    p.update(eyes("angry" if 0.1 < t < 0.9 else "open"))
    return p


def hurt(i: int, n: int, t: float) -> Pose:
    p: Pose = {
        "root_x": track([0, -14, -8, -2], t),
        "root_y": track([0, -2, 1, 0], t),
        "pelvis": track([0, -9, -4, -1], t),
        "torso": track([0, -3, -1, 0], t),
        "neck": track([0, -14, -6, -2], t),
        "head": track([0, -14, -5, 0], t),
        "jaw": track([3, 26, 14, 4], t),
        "tail1": track([0, 10, 4, 0], t),
        "tail2": track([0, 12, 5, 0], t),
        "tail3": track([0, 14, 6, 0], t),
        "tail4": track([0, 16, 8, 0], t),
        "near_arm_u": track([0, -30, -14, -2], t),
        "far_arm_u": track([0, -26, -12, -2], t),
        "fx.hit": track([0, 1, 0.35, 0], t),
    }
    p.update(eyes("shut" if 0.2 < t < 0.8 else "open"))
    return p


def death(i: int, n: int, t: float) -> Pose:
    p: Pose = {
        "root_x": track([0, -8, -12, -10, -6, -4, -4, -4], t),
        # 81, not 82: one unit lower, the fallen body's lower edge lands on a
        # half-covered pixel row the part flipbook's replay misses by a blob.
        "root_y": track([0, -3, 24, 56, 78, 81, 81, 81], t),
        "pelvis": track([0, -9, 2, 8, 6, 4, 4, 4], t),
        "torso": track([0, -3, 2, 4, 3, 2, 2, 2], t),
        "neck": track([0, -17, -8, 6, 12, 14, 15, 15], t),
        "head": track([0, -12, -4, 4, 6, 8, 8, 8], t),
        "jaw": track([3, 34, 24, 18, 14, 10, 9, 9], t),
        "near_foot_x": track([NEAR_X, NEAR_X, 6, 12, 16, 16, 16, 16], t),
        "far_foot_x": track([FAR_X, FAR_X, FAR_X + 2, FAR_X + 8, FAR_X + 12, FAR_X + 12, FAR_X + 12, FAR_X + 12], t),
        "tail1": track([0, -6, -8, -8, -6, -4, -4, -4], t),
        "tail2": track([0, -6, -8, -6, -2, 0, 0, 0], t),
        "tail3": track([0, -6, -6, -4, 2, 4, 4, 4], t),
        "tail4": track([0, -6, -4, -2, 4, 6, 6, 6], t),
        "near_arm_u": track([0, -30, -10, 10, 20, 24, 24, 24], t),
        "near_arm_l": track([0, -10, 0, 10, 16, 18, 18, 18], t),
        "far_arm_u": track([0, -26, -8, 10, 18, 22, 22, 22], t),
        "far_arm_l": track([0, -8, 2, 10, 14, 16, 16, 16], t),
        "fx.thud": track([0, 0, 0, 0, 1, 0.5, 0, 0], t),
    }
    p.update(eyes("dead" if t > 0.6 else "shut" if t > 0.1 else "open"))
    return p


def stunned(i: int, n: int, t: float) -> Pose:
    """Knocked senseless by the wall: slumped on bent legs, head hanging and
    lolling, jaw slack, stars circling (``fx.stars``). It loops until he
    shakes it off."""
    w = math.tau * t
    p: Pose = {
        "root_x": -6.0,
        "root_y": 24.0 + 2.0 * math.sin(w),
        "pelvis": 7.0 + 1.5 * math.sin(w),
        "torso": 5.0,
        "neck": 24.0 + 5.0 * math.sin(w),
        "head": 14.0 + 8.0 * math.sin(w + 1.1),
        "jaw": 20.0 + 4.0 * math.sin(w + 0.4),
        "near_foot_x": NEAR_X + 4.0,
        "far_foot_x": FAR_X - 6.0,
        "near_arm_u": 22.0 + 4.0 * math.sin(w),
        "near_arm_l": 18.0,
        "far_arm_u": 20.0 + 4.0 * math.sin(w + 0.5),
        "far_arm_l": 16.0,
        "fx.stars": 1.0,
    }
    for k in range(4):
        p[f"tail{k + 1}"] = 4.0 + 2.5 * k + 1.5 * math.sin(w - 0.5 * k)
    p.update(eyes("dead"))
    return p


def snap_up(i: int, n: int, t: float) -> Pose:
    """At a ledge above: he crouches with his head cocked up at you (frames
    0-1, the tell), then throws it up and forward, jaws wide, and snaps them
    shut at the top (frames 2-5). Up-and-forward, not straight up: straight
    up, the head leaves the 300 px frame."""
    p: Pose = {
        "root_x": track([0, -6, 2, 4, 2, 0], t),
        "root_y": track([0, 10, 6, 4, 2, 0], t),
        "pelvis": track([0, 4, -3, -4, -2, 0], t),
        "torso": track([0, -4, -3, -3, -2, 0], t),
        "neck": track([0, -16, -16, -18, -10, 0], t),
        "head": track([0, -12, -14, -12, -6, 0], t),
        "jaw": track([3, 10, 34, 2, 6, 3], t),
        "near_foot_x": NEAR_X + 6.0,
        "near_arm_u": track([0, -12, -40, -44, -20, 0], t),
        "far_arm_u": track([0, -10, -36, -40, -18, 0], t),
        "tail1": track([0, 4, 12, 14, 6, 0], t),
        "tail2": track([0, 4, 14, 16, 8, 0], t),
        "tail3": track([0, 4, 16, 18, 8, 0], t),
        "tail4": track([0, 4, 18, 20, 10, 0], t),
        "fx.bite": track([0, 0, 0.3, 1, 0.3, 0], t),
    }
    p.update(eyes("angry"))
    return p


def leap(i: int, n: int, t: float) -> Pose:
    """The enrage leap, drawn in place (the conductor flies him): a deep
    crouch, the spring, legs tucked in the air with the tail up for balance,
    the landing that shakes the hall (``fx.thud``, ``fx.stomp``), and the
    rise out of it."""
    p: Pose = {
        "root_x": track([0, 4, 8, 8, 6, 2, 0, 0], t),
        "root_y": track([18, 0, -6, -6, -2, 22, 8, 0], t),
        "pelvis": track([8, -5, -3, 2, 6, 10, 4, 0], t),
        "torso": track([4, -4, -2, 0, 2, 4, 2, 0], t),
        "neck": track([10, -6, -2, 4, 8, 14, 4, 0], t),
        "head": track([4, -8, 0, 4, 6, 6, 2, 0], t),
        "jaw": track([6, 20, 30, 34, 26, 12, 6, 3], t),
        "near_foot_x": track([NEAR_X + 4, NEAR_X - 6, NEAR_X + 18, NEAR_X + 20, NEAR_X + 14, NEAR_X + 6, NEAR_X + 2, NEAR_X], t),
        "far_foot_x": track([FAR_X - 4, FAR_X - 12, FAR_X + 10, FAR_X + 12, FAR_X + 6, FAR_X - 2, FAR_X, FAR_X], t),
        "near_foot_lift": track([0, 8, 46, 50, 30, 0, 0, 0], t),
        "far_foot_lift": track([0, 14, 54, 56, 34, 0, 0, 0], t),
        "near_foot_pitch": track([0, -20, 24, 26, 12, 0, 0, 0], t),
        "far_foot_pitch": track([0, -24, 28, 30, 14, 0, 0, 0], t),
        "near_arm_u": track([10, -30, -20, -16, -10, 18, 6, 0], t),
        "far_arm_u": track([8, -26, -18, -14, -8, 16, 4, 0], t),
        "tail1": track([6, -10, -14, -12, -6, 8, 2, 0], t),
        "tail2": track([6, -12, -16, -14, -6, 10, 3, 0], t),
        "tail3": track([6, -14, -18, -16, -8, 12, 3, 0], t),
        "tail4": track([6, -16, -20, -18, -8, 14, 4, 0], t),
        "fx.dust": track([0.4, 0.8, 0, 0, 0, 1, 0.5, 0.1], t),
        "fx.thud": track([0, 0, 0, 0, 0, 1, 0.45, 0], t),
        "fx.stomp": track([0, 0, 0, 0, 0, 1, 0.4, 0], t),
    }
    p.update(eyes("angry"))
    return p


CLIPS: Dict[str, Callable[[int, int, float], Pose]] = {
    "idle": idle,
    "walk": walk,
    "charge": charge,
    "bite": bite,
    "roar": roar,
    "tail_swipe": tail_swipe,
    "stomp": stomp,
    "hurt": hurt,
    "death": death,
    "stunned": stunned,
    "snap_up": snap_up,
    "leap": leap,
}

DEFAULTS: Pose = {
    "near_foot_x": NEAR_X,
    "far_foot_x": FAR_X,
    "eye.open": 1.0,
    "jaw": 3.0,
}


SPEC = T.theropod_spec(
    name="trex_enemy",
    svg_path=PKG / "data" / "characters" / "trex_enemy" / "trex_enemy.svg",
    rig_path=PKG / "targets" / "characters" / "rigged" / "trex_enemy" / "trex_enemy_side.rig.json",
    view_label="T-Rex - Side Right",
    # The art is drawn roomy (640x400 units); the sprite keeps the on-screen
    # size the T-rex had before the SVG redesign.
    scale=0.75,
    svg_center_x=270.0,
    svg_ground_y=372.0,
    frame_size=(480, 300),
    rows=[
        ("idle", 6, 120, True),
        ("walk", 8, 90, True),
        ("charge", 8, 76, True),
        ("bite", 7, 78, False),
        ("roar", 6, 104, False),
        ("tail_swipe", 7, 82, False),
        ("stomp", 6, 92, False),
        ("hurt", 4, 90, False),
        ("death", 8, 110, False),
        # The rework's rows (2026-10-05): appended, so the nine above keep
        # their places.
        ("stunned", 6, 130, True),
        ("snap_up", 6, 90, False),
        ("leap", 8, 90, False),
    ],
    clips=CLIPS,
    defaults=DEFAULTS,
)


def main(argv: List[str] | None = None) -> int:
    del argv
    for path in T.write(SPEC):
        print(path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
