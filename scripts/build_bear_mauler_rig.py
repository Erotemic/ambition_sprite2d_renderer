#!/usr/bin/env python3
"""Build the bear mauler's rig document from its SVG.

The SVG ``data/characters/bear_mauler/bear_mauler.svg`` owns the art and says
where every joint is; ``rigbuild.creature_rig``, with the ``quadruped``
anatomy, derives the skeleton from it, binds every part to its bone, and
refreshes the SVG's rig catalog. This script supplies only what the drawing
cannot state: the frame, the rows and the clips. It never draws.

    uv run python scripts/build_bear_mauler_rig.py

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

from ambition_sprite2d_renderer.rigbuild import quadruped as Q  # noqa: E402
from ambition_sprite2d_renderer.rigbuild.quadruped import Pose, eyes, track  # noqa: E402

PKG = ROOT / "ambition_sprite2d_renderer"

#: Where each paw plants, from the drawing's centre (SVG units).
REST_X = {"near_hind": -72.0, "far_hind": -88.0, "near_fore": 54.0, "far_fore": 38.0}


def paws(t: float, **tracks: List[float]) -> Pose:
    """``<leg>_<x|lift|pitch>`` channels from key rows; an ``x`` row is an
    offset from that paw's rest."""
    p: Pose = {}
    for key, keys in tracks.items():
        leg, channel = key.rsplit("_", 1)
        p[key] = track(keys, t) + (REST_X[leg] if channel == "x" else 0.0)
    return p


def idle(i: int, n: int, t: float) -> Pose:
    w = math.tau * t
    breath = math.sin(w)
    p: Pose = {
        "root_y": 1.6 * breath,
        "pelvis": -0.6 * breath,
        "torso": 0.9 * breath,
        # Sniffing the air: the head dips and lifts.
        "neck": track([0, 3, 5, 1, -3, -1, 0], t),
        "head": track([0, -2, -6, -6, 0, 3, 0], t),
        "jaw": 3.0 + 3.0 * max(0.0, math.sin(w * 2.0 + 0.5)),
    }
    p.update(eyes("shut" if i == 4 else "open"))
    return p


def walk(i: int, n: int, t: float) -> Pose:
    p = Q.gait(t, rest_x=REST_X, stride=26.0, lift=20.0, bob=5.0, sway=1.5)
    p["jaw"] = 3.0
    p.update(eyes("open"))
    return p


def swipe(i: int, n: int, t: float) -> Pose:
    """Rock back, raise the near forepaw, rake it down and forward."""
    p: Pose = {
        "root_x": track([0, -4, -6, 8, 10, 4, 0], t),
        "root_y": track([0, -2, -3, 2, 3, 1, 0], t),
        "pelvis": track([0, -6, -10, 4, 6, 2, 0], t),
        "torso": track([0, -2, -4, 2, 2, 0, 0], t),
        "neck": track([0, -6, -8, 6, 4, 1, 0], t),
        "head": track([0, -4, -6, 6, 4, 0, 0], t),
        "jaw": track([3, 14, 22, 26, 12, 6, 3], t),
        "fx.swipe": track([0, 0, 0.4, 1, 0.5, 0, 0], t),
    }
    p.update(paws(t, near_fore_x=[0, 24, 40, 80, 64, 28, 0], near_fore_lift=[0, 100, 150, 40, 6, 6, 0],
                  near_fore_pitch=[0, -60, -90, 40, 10, 4, 0]))
    p.update(eyes("angry" if 0.1 < t < 0.9 else "open"))
    return p


def slam(i: int, n: int, t: float) -> Pose:
    """Rear up on the hind legs and come down on both forepaws."""
    p: Pose = {
        "root_x": track([0, -6, -10, -10, 4, 10, 8, 4], t),
        "root_y": track([0, -4, -6, -6, 2, 8, 4, 0], t),
        "pelvis": track([0, -20, -40, -44, -8, 4, 2, 0], t),
        "torso": track([0, -4, -6, -6, 2, 2, 1, 0], t),
        "neck": track([0, -2, 6, 8, 12, 14, 6, 0], t),
        "head": track([0, -4, -6, -6, 6, 8, 4, 0], t),
        "jaw": track([3, 16, 30, 34, 24, 14, 6, 3], t),
        "fx.shock": track([0, 0, 0, 0, 0.6, 1, 0.4, 0], t),
        "fx.dust": track([0, 0, 0, 0, 0.7, 1, 0.6, 0.2], t),
    }
    p.update(paws(t,
                  near_fore_x=[0, -14, -40, -44, -4, 10, 6, 0], near_fore_lift=[0, 50, 110, 122, 30, 0, 0, 0],
                  near_fore_pitch=[0, -20, -40, -50, -10, 0, 0, 0],
                  far_fore_x=[0, -12, -38, -42, -2, 10, 6, 0], far_fore_lift=[0, 46, 104, 116, 26, 0, 0, 0],
                  far_fore_pitch=[0, -20, -40, -50, -10, 0, 0, 0]))
    p.update(eyes("angry" if 0.05 < t < 0.95 else "open"))
    return p


def charge(i: int, n: int, t: float) -> Pose:
    """A gallop, head down."""
    p = Q.gait(t, rest_x=REST_X, stride=34.0, lift=26.0, bob=8.0, sway=3.0, phases=Q.GALLOP_PHASES)
    w = math.tau * t
    p["root_x"] = 8.0
    p["pelvis"] += 4.0
    p["neck"] += 8.0
    p["head"] -= 4.0
    p["jaw"] = 10.0 + 6.0 * max(0.0, math.sin(w))
    p["fx.dust"] = 0.4 + 0.6 * abs(math.cos(w))
    p.update(eyes("angry"))
    return p


def hurt(i: int, n: int, t: float) -> Pose:
    p: Pose = {
        "root_x": track([0, -10, -6, -2], t),
        "root_y": track([0, -2, 1, 0], t),
        "pelvis": track([0, -8, -4, -1], t),
        "torso": track([0, -3, -1, 0], t),
        "neck": track([0, -12, -6, -2], t),
        "head": track([0, -14, -6, 0], t),
        "jaw": track([3, 24, 12, 4], t),
        "fx.hit": track([0, 1, 0.35, 0], t),
    }
    p.update(eyes("shut" if 0.2 < t < 0.8 else "open"))
    return p


def death(i: int, n: int, t: float) -> Pose:
    p: Pose = {
        "root_x": track([0, -6, -8, -6, -4, -2, -2, -2], t),
        "root_y": track([0, -2, 12, 34, 54, 60, 62, 62], t),
        "pelvis": track([0, -8, 0, 4, 3, 2, 2, 2], t),
        "torso": track([0, -2, 2, 3, 2, 2, 2, 2], t),
        "neck": track([0, -12, -4, 4, 6, 7, 7, 7], t),
        "head": track([0, -8, 0, 4, 5, 5, 5, 5], t),
        "jaw": track([3, 22, 16, 12, 10, 9, 8, 8], t),
        "fx.thud": track([0, 0, 0, 0, 1, 0.5, 0, 0], t),
    }
    p.update(paws(t, near_hind_x=[0, 0, 2, 6, 8, 8, 8, 8], far_hind_x=[0, 0, 2, 6, 8, 8, 8, 8],
                  near_fore_x=[0, 0, 4, 8, 12, 12, 12, 12], far_fore_x=[0, 0, 4, 8, 12, 12, 12, 12]))
    p.update(eyes("dead" if t > 0.6 else "shut" if t > 0.1 else "open"))
    return p


CLIPS: Dict[str, Callable[[int, int, float], Pose]] = {
    "idle": idle,
    "walk": walk,
    "swipe": swipe,
    "slam": slam,
    "charge": charge,
    "hurt": hurt,
    "death": death,
}

DEFAULTS: Pose = {**{f"{leg}_x": x for leg, x in REST_X.items()}, "eye.open": 1.0, "jaw": 3.0}

SPEC = Q.quadruped_spec(
    name="bear_mauler",
    svg_path=PKG / "data" / "characters" / "bear_mauler" / "bear_mauler.svg",
    rig_path=PKG / "targets" / "characters" / "rigged" / "bear_mauler" / "bear_mauler_side.rig.json",
    view_label="Bear - Side Right",
    # Drawn at 560x400 units, published at the size the bear always had.
    scale=0.36,
    svg_center_x=280.0,
    svg_ground_y=372.0,
    frame_size=(202, 144),
    rows=[
        ("idle", 6, 130, True),
        ("walk", 8, 95, True),
        ("swipe", 7, 80, False),
        ("slam", 8, 90, False),
        ("charge", 7, 75, True),
        ("hurt", 4, 90, False),
        ("death", 8, 110, False),
    ],
    clips=CLIPS,
    defaults=DEFAULTS,
    jaw_length=22.0,
)


def main(argv: List[str] | None = None) -> int:
    del argv
    for path in Q.write(SPEC):
        print(path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
