#!/usr/bin/env python3
"""Build the boss chest's rig document from its SVG.

The SVG ``data/props/boss_chest/boss_chest.svg`` owns the art and says where
every joint is; ``rigbuild.creature_rig``, with the ``chest`` anatomy,
derives the skeleton, binds every part to its bone and refreshes the SVG's
rig catalog. This script supplies only what the drawing cannot state: the
frame, the rows and the clips. It never draws.

    uv run python scripts/build_boss_chest_rig.py

The big-item chest's opening is heavier and grander than the treasure
chest's: the ruby in the lock wakes, the chest shudders and heaves, the
lock falls loose, light cracks round the lid, and the lid is flung back in
a burst of light that dies away, leaving the chest open and empty for the
item the game places in it. ``closed`` and ``open`` are single still
frames. The clips key the effects' strengths (``fx.*``), which
``targets/props/boss_chest.py`` draws.

Clips are key poses, one key per drawn frame (``K``). Distances are SVG units.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable, Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ambition_sprite2d_renderer.rigbuild.chest import Pose, chest_spec, lid, track, write  # noqa: E402

PKG = ROOT / "ambition_sprite2d_renderer"
K = track

#: (row, frames, ms, loops).
ROWS = [
    ("closed", 1, 100, True),
    ("opening", 14, 66, False),
    ("open", 1, 100, True),
]

#: The lid's look on each frame of the opening.
OPENING_LIDS = ["closed"] * 5 + ["ajar", "ajar", "up"] + ["open"] * 6


def closed(i: int, n: int, t: float) -> Pose:
    """Shut, held still."""
    return lid("closed")


def opening(i: int, n: int, t: float) -> Pose:
    p = lid(OPENING_LIDS[i])
    # The ruby wakes; the chest shudders, heaves up off its feet, lands.
    p["root_x"] = K([0, 2, -4, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], t)
    p["root_y"] = K([0, 0, 0, 0, -12, 3, 0, -5, 0, 0, 0, 0, 0, 0], t)
    p["base"] = K([0, 0.5, -1.2, 1.2, 0.6, 0, 0, 0, 0, 0, 0, 0, 0, 0], t)
    p["lid"] = K([0, 0, -2, 2.5, -3, 0, 0, 0, 0, 0, 0, 0, 0, 0], t)
    # Flung back, the heavy lid overshoots, rebounds and settles on its hinge.
    p["bone.lid.scale_y"] = K([1, 1, 1, 1, 1, 1, 1, 1, 1.12, 0.93, 1.04, 0.99, 1, 1], t)
    # The great lock jolts, drops loose and swings to rest.
    p["lock"] = K([0, 0, 4, -4, 8, -24, 18, -12, 8, -4, 2, -1, 0, 0], t)
    p["fx.gem"] = K([0, 0.7, 1, 1, 0.8, 0.4, 0, 0, 0, 0, 0, 0, 0, 0], t)
    p["fx.click"] = K([0, 0, 0, 0, 0.5, 1, 0.3, 0, 0, 0, 0, 0, 0, 0], t)
    p["fx.dust"] = K([0, 0, 0, 0, 0, 1, 0.5, 0, 0, 0, 0, 0, 0, 0], t)
    p["fx.leak"] = K([0, 0, 0, 0, 0, 0.8, 1, 0, 0, 0, 0, 0, 0, 0], t)
    p["fx.burst"] = K([0, 0, 0, 0, 0, 0, 0, 0.6, 1, 0.6, 0.3, 0.1, 0, 0], t)
    p["fx.glow"] = K([0, 0, 0, 0, 0, 0.3, 0.5, 0.7, 1, 0.9, 0.7, 0.45, 0.2, 0], t)
    p["fx.rays"] = K([0, 0, 0, 0, 0, 0.2, 0.4, 0.7, 1, 0.9, 0.7, 0.4, 0.15, 0], t)
    p["fx.sparkle"] = K([0, 0, 0, 0, 0, 0, 0, 0, 0.6, 1, 0.8, 0.5, 0.2, 0], t)
    return p


def open_(i: int, n: int, t: float) -> Pose:
    """Open and empty, held still."""
    return lid("open")


CLIPS: Dict[str, Callable[[int, int, float], Pose]] = {"closed": closed, "opening": opening, "open": open_}

SPEC = chest_spec(
    name="boss_chest",
    svg_path=PKG / "data" / "props" / "boss_chest" / "boss_chest.svg",
    rig_path=PKG / "targets" / "props" / "rigged" / "boss_chest" / "boss_chest.rig.json",
    view_label="Boss Chest - Front",
    # Drawn at 640 units square, published in a 160 px frame (the same
    # pixels per unit as the treasure chest, so it stands bigger beside it).
    scale=0.25,
    svg_center_x=320.0,
    svg_ground_y=600.0,
    frame_size=(160, 160),
    rows=ROWS,
    clips=CLIPS,
    defaults={"lid.closed": 1.0},
)


def main(argv: List[str] | None = None) -> int:
    del argv
    for path in write(SPEC):
        print(path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
