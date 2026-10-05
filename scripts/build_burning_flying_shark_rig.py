#!/usr/bin/env python3
"""Build the burning flying shark's rig document from its SVG.

The SVG ``data/characters/burning_flying_shark/burning_flying_shark.svg`` owns
the art and says where every joint is; ``rigbuild.creature_rig``, with the
``fish`` anatomy, derives the skeleton from it, binds every part to its bone,
and refreshes the SVG's rig catalog. This script supplies only what the
drawing cannot state: the frame, the rows and the clips. It never draws.

    uv run python scripts/build_burning_flying_shark_rig.py

The clips keep the sheet contract the game already reads: the same four rows,
frame counts and durations as before the SVG redesign.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Callable, Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ambition_sprite2d_renderer.rigbuild import fish as F  # noqa: E402
from ambition_sprite2d_renderer.rigbuild.fish import Pose, eyes, track  # noqa: E402

PKG = ROOT / "ambition_sprite2d_renderer"


def idle(i: int, n: int, t: float) -> Pose:
    """Hovering: a slow tail beat, the fins sculling, the flames lazy."""
    p = F.swim(t, tail=8.0, fin=10.0, bob=4.0)
    p["jaw"] = 4.0 + 3.0 * max(0.0, math.sin(math.tau * t + 0.8))
    p["fx.flame"] = 0.85
    p.update(eyes("open"))
    return p


def fly(i: int, n: int, t: float) -> Pose:
    p = F.swim(t, tail=13.0, fin=20.0, bob=6.0, pitch=-2.0)
    p["jaw"] = 3.0
    p["fx.flame"] = 1.0
    p.update(eyes("open"))
    return p


def chomp(i: int, n: int, t: float) -> Pose:
    """Rear back with the jaws wide (the telegraph), lunge, snap shut."""
    p = F.swim(t, tail=10.0, fin=14.0, bob=2.0)
    p["root_x"] = track([0, -12, 16, 22, 10, 0], t)
    p["root_y"] = track([0, -4, 2, 4, 2, 0], t)
    p["body"] += track([0, -12, 6, 8, 3, 0], t)
    p["head"] += track([0, -10, 4, 2, 1, 0], t)
    p["jaw"] = track([4, 30, 36, 2, 8, 4], t)
    p["near_pec"] += track([0, -16, 18, 14, 6, 0], t)
    p["far_pec"] += track([0, -12, 14, 10, 4, 0], t)
    p["fx.flame"] = 1.0
    p["fx.flare"] = track([0, 0.4, 1, 0.8, 0.3, 0], t)
    p["fx.bite"] = track([0, 0, 0.4, 1, 0.3, 0], t)
    # The eye rolls back under its membrane for the bite.
    p.update(eyes("shut" if 0.3 < t < 0.7 else "angry" if 0.05 < t < 0.95 else "open"))
    return p


def dive(i: int, n: int, t: float) -> Pose:
    """Nose down, fins swept back, the tail driving: the flames stream long."""
    p = F.swim(t, beats=2.0, tail=10.0, fin=6.0, bob=3.0, pitch=26.0)
    p["near_pec"] += 22.0
    p["far_pec"] += 18.0
    p["dorsal"] += 8.0
    p["jaw"] = 10.0
    p["root_y"] += 18.0
    p["fx.flame"] = 1.0
    p["fx.flare"] = 1.0
    p["fx.speed"] = 0.75 + 0.25 * math.sin(math.tau * 2.0 * t)
    p.update(eyes("angry"))
    return p


CLIPS: Dict[str, Callable[[int, int, float], Pose]] = {
    "idle": idle,
    "fly": fly,
    "chomp": chomp,
    "dive": dive,
}

DEFAULTS: Pose = {"eye.open": 1.0, "jaw": 4.0}

SPEC = F.fish_spec(
    name="burning_flying_shark",
    svg_path=PKG / "data" / "characters" / "burning_flying_shark" / "burning_flying_shark.svg",
    rig_path=PKG / "targets" / "characters" / "rigged" / "burning_flying_shark" / "burning_flying_shark_side.rig.json",
    view_label="Shark - Side Right",
    # Drawn at 620x360 units, published at the size the shark always had.
    scale=0.36,
    svg_center_x=310.0,
    svg_ground_y=340.0,
    frame_size=(223, 130),
    # The old sheet sampled every row as a loop (frame i at t = i / n).
    rows=[
        ("idle", 6, 135, True),
        ("fly", 8, 90, True),
        ("chomp", 6, 82, False),
        ("dive", 8, 82, True),
    ],
    clips=CLIPS,
    defaults=DEFAULTS,
    jaw_length=22.0,
)


def main(argv: List[str] | None = None) -> int:
    del argv
    for path in F.write(SPEC):
        print(path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
