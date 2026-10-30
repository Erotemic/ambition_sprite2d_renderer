#!/usr/bin/env python3
"""Build the triceratops's rig document from its SVG.

The SVG ``data/characters/triceratops/triceratops.svg`` owns the art and says
where every joint is; ``rigbuild.creature_rig``, with the ``quadruped``
anatomy and one more bone for the tail, derives the skeleton from it, binds
every part to its bone, and refreshes the SVG's rig catalog. This script
supplies only what the drawing cannot state: the frame, the rows and the
clips. It never draws.

    uv run python scripts/build_triceratops_rig.py

The rows have the names the game reads: ``slash`` is the thrust of its horns,
``taunt`` is a forefoot that paws the ground, ``windup`` is the horns
lowered before the thrust and ``notice`` is the start when it sees its foe.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Callable, Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ambition_sprite2d_renderer.rigbuild import quadruped as Q  # noqa: E402
from ambition_sprite2d_renderer.rigbuild.quadruped import Pose, eyes, segment, track  # noqa: E402

PKG = ROOT / "ambition_sprite2d_renderer"

#: Where each foot plants, from the drawing's centre (SVG units).
REST_X = {"near_hind": -68.0, "far_hind": -90.0, "near_fore": 42.0, "far_fore": 22.0}
LEGS = tuple(REST_X)


def feet(t: float, **tracks: List[float]) -> Pose:
    """``<leg>_<x|lift|pitch>`` channels from key rows; an ``x`` row is an
    offset from that foot's rest."""
    p: Pose = {}
    for key, keys in tracks.items():
        leg, channel = key.rsplit("_", 1)
        p[key] = track(keys, t) + (REST_X[leg] if channel == "x" else 0.0)
    return p


def idle(i: int, n: int, t: float) -> Pose:
    w = math.tau * t
    breath = math.sin(w)
    p: Pose = {
        "root_y": 1.8 * breath,
        "torso": 0.6 * breath,
        "neck": track([0, 2, 4, 2, -1, -2, -1, 0, 0], t),
        "head": track([0, -1, -3, -4, -1, 2, 1, 0, 0], t),
        "jaw": 2.0 + 2.0 * max(0.0, math.sin(w + 0.5)),
        "tail": 4.0 * math.sin(w - 0.8),
    }
    p.update(eyes("shut" if i == 5 else "open"))
    return p


def walk(i: int, n: int, t: float) -> Pose:
    p = Q.gait(t, rest_x=REST_X, stride=22.0, lift=14.0, bob=3.0, sway=1.2)
    p["tail"] = 5.0 * math.sin(math.tau * t - 0.8)
    p["jaw"] = 2.0
    p.update(eyes("open"))
    return p


def run(i: int, n: int, t: float) -> Pose:
    """The charge: a gallop with the head down and the horns level."""
    p = Q.gait(t, rest_x=REST_X, stride=32.0, lift=22.0, bob=6.0, sway=2.6, phases=Q.GALLOP_PHASES)
    w = math.tau * t
    p["root_x"] = 8.0
    p["neck"] += 8.0
    p["head"] += 14.0
    p["tail"] = -8.0 + 6.0 * math.sin(w - 0.8)
    p["jaw"] = 4.0
    p["fx.dust"] = 0.4 + 0.6 * abs(math.cos(w))
    p.update(eyes("angry"))
    return p


def jump(i: int, n: int, t: float) -> Pose:
    p: Pose = {"pelvis": track([-4, -8, -8, -6], t), "neck": -4.0, "head": -6.0, "tail": track([6, 10, 10, 8], t), "jaw": 4.0}
    p.update(feet(t, near_hind_x=[0, -14, -18, -16], far_hind_x=[0, -14, -18, -16], near_fore_x=[0, 10, 14, 12],
                  far_fore_x=[0, 10, 14, 12], near_fore_lift=[0, 14, 20, 18], far_fore_lift=[0, 12, 18, 16],
                  near_hind_lift=[0, 4, 10, 10], far_hind_lift=[0, 4, 10, 10]))
    p.update(eyes("open"))
    return p


def fall(i: int, n: int, t: float) -> Pose:
    p: Pose = {"pelvis": track([-2, 2, 4, 4], t), "neck": 2.0, "head": 4.0, "tail": track([8, 14, 16, 16], t), "jaw": 8.0}
    p.update(feet(t, near_hind_x=[-10, -6, -4, -4], far_hind_x=[-10, -6, -4, -4], near_fore_x=[10, 14, 16, 16],
                  far_fore_x=[10, 14, 16, 16], near_fore_lift=[12, 8, 6, 6], far_fore_lift=[12, 8, 6, 6],
                  near_hind_lift=[10, 8, 6, 6], far_hind_lift=[10, 8, 6, 6]))
    p.update(eyes("open"))
    return p


def gore(i: int, n: int, t: float) -> Pose:
    """It rocks back with its head low, then drives forward and throws its
    horns up."""
    p: Pose = {
        "root_x": track([0, -12, -8, 24, 30, 14, 0], t),
        "root_y": track([0, 2, 4, -2, -4, 0, 0], t),
        "pelvis": track([0, 2, 4, -4, -6, -2, 0], t),
        "neck": track([0, 10, 16, -4, -12, -4, 0], t),
        "head": track([0, 16, 26, -8, -22, -6, 0], t),
        "jaw": track([2, 4, 6, 12, 16, 6, 2], t),
        "tail": track([0, 6, 10, -8, -12, -4, 0], t),
        "fx.peck": track([0, 0, 0, 1, 0.6, 0, 0], t),
        "fx.dust": track([0, 0, 0.4, 1, 0.5, 0.2, 0], t),
    }
    lean = track([0, -12, -8, 24, 30, 14, 0], t)
    for leg in LEGS:
        p[f"{leg}_x"] = REST_X[leg] + 0.5 * lean
    p.update(eyes("angry" if 0.1 < t < 0.9 else "open"))
    return p


def paw(i: int, n: int, t: float) -> Pose:
    """It paws the ground with a forefoot and shakes its frill."""
    w = math.tau * t
    scrape = 0.5 + 0.5 * math.sin(2.0 * w - 1.2)
    p: Pose = {
        "neck": 8.0 + 3.0 * math.sin(2.0 * w),
        "head": 10.0 + 8.0 * math.sin(2.0 * w + 0.6),
        "jaw": 6.0 + 8.0 * max(0.0, math.sin(w)),
        "tail": 10.0 * math.sin(2.0 * w),
        "near_fore_x": REST_X["near_fore"] + 18.0 - 28.0 * scrape,
        "near_fore_lift": 16.0 * max(0.0, math.sin(2.0 * w + 0.4)),
        "near_fore_pitch": 20.0 * max(0.0, math.sin(2.0 * w + 0.4)),
        "fx.dust": 0.9 * max(0.0, -math.sin(2.0 * w + 0.4)),
    }
    p.update(eyes("angry"))
    return p


def hurt(i: int, n: int, t: float) -> Pose:
    p: Pose = {
        "root_x": track([0, -10, -6, -2], t),
        "pelvis": track([0, -5, -3, -1], t),
        "neck": track([0, -10, -5, -2], t),
        "head": track([0, -14, -6, 0], t),
        "jaw": track([2, 20, 10, 4], t),
        "tail": track([0, 12, 6, 0], t),
        "fx.hit": track([0, 1, 0.35, 0], t),
        "fx.feathers": track([0.4, 1, 0.5, 0], t),
    }
    p.update(eyes("shut" if 0.2 < t < 0.8 else "open"))
    return p


def death(i: int, n: int, t: float) -> Pose:
    """Its legs go from under it and it settles on its belly, the head down
    on its beak."""
    p: Pose = {
        "root_x": track([0, -8, -10, -6, -4, -2, -2, -2], t),
        "root_y": track([0, -2, 10, 30, 50, 54, 52, 52], t),
        "pelvis": track([0, -6, -2, 2, 3, 2, 2, 2], t),
        "neck": track([0, -12, -4, 4, 7, 8, 8, 8], t),
        "head": track([0, -10, 0, 4, 6, 8, 7, 7], t),
        "jaw": track([2, 20, 14, 10, 8, 6, 6, 6], t),
        "tail": track([0, 12, 8, 0, -10, -14, -12, -12], t),
        "fx.hit": track([1, 0.3, 0, 0, 0, 0, 0, 0], t),
        "fx.feathers": track([0.6, 1, 0.6, 0.2, 0, 0, 0, 0], t),
        "fx.dust": track([0, 0, 0, 0.4, 1, 0.6, 0.2, 0], t),
    }
    p.update(feet(t, near_hind_x=[0, 0, -4, -10, -14, -14, -14, -14], far_hind_x=[0, 0, -4, -10, -14, -14, -14, -14],
                  near_fore_x=[0, 0, 6, 14, 20, 20, 20, 20], far_fore_x=[0, 0, 6, 14, 20, 20, 20, 20]))
    p.update(eyes("dead" if t > 0.5 else "shut"))
    return p


def notice(i: int, n: int, t: float) -> Pose:
    """Startled by its foe: the head thrown up so the frill stands tall, the
    beak open, the tail up, a forefoot set back. Held, with a shiver."""
    up = track([0.92, 1.0, 0.96], t)
    p: Pose = {
        "root_x": -4.0 * up,
        "root_y": -3.0 * up,
        "pelvis": -4.0 * up,
        "neck": -12.0 * up,
        "head": -18.0 * up + track([0, 0, 2], t),
        "jaw": track([12, 20, 16], t),
        "tail": 14.0 * up,
    }
    p.update(feet(t, near_fore_x=[-6, -8, -8]))
    p.update(eyes("open"))
    return p


def windup(i: int, n: int, t: float) -> Pose:
    """The telegraph of the gore: rocked back on its haunches, the head down
    so the horns point at its foe, and a forefoot pawing the ground."""
    sink = 0.92 if i == 0 else 1.0
    shake = track([0, 1.2, -1.2], t)
    p: Pose = {
        "root_x": -14.0 * sink + shake,
        "root_y": -2.0 * sink,
        "pelvis": 4.0 * sink,
        "neck": 12.0,
        "head": 16.0,
        "jaw": 6.0,
        "tail": 14.0 + shake,
        "fx.dust": track([0, 0.9, 0.2], t),
    }
    p.update(feet(t, near_hind_x=[-6, -6, -6], far_hind_x=[-6, -6, -6], far_fore_x=[-4, -4, -4],
                  near_fore_x=[14, -14, 8], near_fore_lift=[18, 0, 14], near_fore_pitch=[22, 0, 18]))
    p.update(eyes("angry"))
    return p


CLIPS: Dict[str, Callable[[int, int, float], Pose]] = {
    "idle": idle,
    "walk": walk,
    "run": run,
    "jump": jump,
    "fall": fall,
    "slash": gore,
    "taunt": paw,
    "hurt": hurt,
    "death": death,
    "notice": notice,
    "windup": windup,
}

DEFAULTS: Pose = {**{f"{leg}_x": x for leg, x in REST_X.items()}, "eye.open": 1.0, "jaw": 2.0}


def skeleton(J):
    """The quadruped's bones and a tail on the pelvis."""
    return Q.skeleton(J, 30.0) + [segment("tail", "pelvis", J["tail"], J["tail_tip"])]


SPEC = Q.CreatureSpec(
    name="triceratops",
    svg_path=PKG / "data" / "characters" / "triceratops" / "triceratops.svg",
    rig_path=PKG / "targets" / "characters" / "rigged" / "triceratops" / "triceratops_side.rig.json",
    view_label="Triceratops - Side Right",
    skeleton=skeleton,
    legs=Q.LEGS,
    scale=0.5,
    svg_center_x=256.0,
    svg_ground_y=416.0,
    frame_size=(256, 256),
    rows=[
        ("idle", 8, 130, True),
        ("walk", 8, 95, True),
        ("run", 8, 64, True),
        ("jump", 4, 80, False),
        ("fall", 4, 80, False),
        ("slash", 7, 68, False),
        ("taunt", 8, 110, False),
        ("hurt", 4, 92, False),
        ("death", 8, 110, False),
        # The game holds ``notice`` while it first sees its foe, and
        # ``windup`` over a melee move's startup before the attack row.
        ("notice", 3, 120, False),
        ("windup", 3, 90, False),
    ],
    clips=CLIPS,
    defaults=DEFAULTS,
)


def main(argv: List[str] | None = None) -> int:
    del argv
    for path in Q.write(SPEC):
        print(path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
