#!/usr/bin/env python3
"""Build the treasure chest's rig document from its SVG.

The SVG ``data/props/treasure_chest/treasure_chest.svg`` owns the art and
says where every joint is; ``rigbuild.creature_rig`` derives the skeleton,
binds every part to its bone and refreshes the SVG's rig catalog. This
script supplies only what the drawing cannot state: the skeleton (a box, a
hinged lid, a lock, the treasure heap), the frame, the rows and the clips.
It never draws.

    uv run python scripts/build_treasure_chest_rig.py

The lid swings through its swap set (``lid.closed`` / ``lid.ajar`` /
``lid.up`` / ``lid.open``) and bounces by its squash (``bone.lid.scale_y``
about the hinge). The clips also key the effects' strengths (``fx.*``),
which ``targets/props/treasure_chest.py`` draws: the glint on the lock, the
light leaking from under the lid, the burst of light, the coin fountain,
the sparkles.

Clips are key poses, one key per drawn frame (``K``): a one-shot row's
frame ``i`` IS key ``i``; a loop's last key repeats its first. Distances are
SVG units.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable, Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ambition_sprite2d_renderer.rigbuild.creature_rig import (  # noqa: E402
    BoneSpec,
    CreatureSpec,
    Point,
    Pose,
    segment,
    track,
    write,
)

PKG = ROOT / "ambition_sprite2d_renderer"
K = track

#: (row, frames, ms, loops).
ROWS = [
    ("closed", 8, 130, True),
    ("opening", 14, 62, False),
    ("open", 8, 110, True),
]

LIDS = ("closed", "ajar", "up", "open")


def lid(state: str) -> Pose:
    return {f"lid.{name}": 1.0 if name == state else 0.0 for name in LIDS}


def skeleton(J: Dict[str, Point]) -> List[BoneSpec]:
    return [
        ("base", None, J["base"], 0.0, 0.0),
        segment("lid", "base", J["hinge"], J["lid_top"]),
        segment("lock", "base", J["lock"], J["lock_end"]),
        segment("treasure", "base", J["treasure"], J["treasure_top"]),
    ]


def closed(i: int, n: int, t: float) -> Pose:
    """Shut and waiting: a glint runs over the lock now and then."""
    p = lid("closed")
    p["fx.glint"] = K([0, 0, 0, 0, 0, 0.6, 1, 0.3, 0], t)
    return p


def opening(i: int, n: int, t: float) -> Pose:
    """It rattles (something wants out), hops, the lock swings loose, the
    lid cracks with light leaking under it, flies back and bounces on its
    hinge in a burst of light, and the treasure spouts a fountain of coins
    that rain back into the heap."""
    state = ["closed", "closed", "closed", "closed", "ajar", "ajar", "up", "open", "open", "open", "open", "open",
             "open", "open"][i]
    p = lid(state)
    p["root_x"] = K([0, 4, -4, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], t)
    p["root_y"] = K([0, 0, 0, -14, 2, 0, -4, 0, 0, 0, 0, 0, 0, 0], t)
    p["base"] = K([0, 1.5, -1.5, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], t)
    # The closed lid rattles on its hinge before it gives.
    p["lid"] = K([0, -2.5, 2.5, -3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], t)
    # Thrown back, the open lid overshoots and settles (its squash about the hinge).
    p["bone.lid.scale_y"] = K([1, 1, 1, 1, 1, 1, 1, 1.1, 0.94, 1.03, 0.99, 1, 1, 1], t)
    # The lock jolts, then swings loose on its staple and settles.
    p["lock"] = K([0, 6, -6, 10, -26, 18, -12, 8, -5, 3, -1, 0, 0, 0], t)
    # The heap heaves as the coins burst from it.
    p["bone.treasure.scale_y"] = K([1, 1, 1, 1, 1, 1, 1, 1.08, 1.03, 1, 1, 1, 1, 1], t)
    p["fx.click"] = K([0, 0, 0, 0.4, 1, 0.3, 0, 0, 0, 0, 0, 0, 0, 0], t)
    p["fx.dust"] = K([0, 0, 0, 0, 1, 0.4, 0, 0, 0, 0, 0, 0, 0, 0], t)
    p["fx.leak"] = K([0, 0, 0, 0, 0.8, 1, 0, 0, 0, 0, 0, 0, 0, 0], t)
    p["fx.burst"] = K([0, 0, 0, 0, 0, 0, 0.6, 1, 0.7, 0.4, 0.2, 0, 0, 0], t)
    p["fx.glow"] = K([0, 0, 0, 0, 0.3, 0.5, 0.8, 1, 1, 0.9, 0.8, 0.75, 0.7, 0.7], t)
    p["fx.rays"] = K([0, 0, 0, 0, 0.3, 0.6, 0.9, 1, 1, 0.85, 0.7, 0.6, 0.5, 0.45], t)
    # The coin fountain's clock: 0 as the lid flies back, 1 as the last coin lands.
    p["fx.coins"] = K([0, 0, 0, 0, 0, 0, 0, 0.08, 0.24, 0.4, 0.56, 0.72, 0.88, 1], t)
    p["fx.sparkle"] = K([0, 0, 0, 0, 0, 0, 0, 0.5, 1, 1, 1, 1, 0.8, 0.6], t)
    return p


def open_(i: int, n: int, t: float) -> Pose:
    """Open, the treasure glowing and twinkling."""
    p = lid("open")
    p["fx.glow"] = K([0.7, 0.8, 0.9, 0.8, 0.7, 0.6, 0.65, 0.7, 0.7], t)
    p["fx.rays"] = K([0.45, 0.55, 0.65, 0.55, 0.45, 0.4, 0.42, 0.45, 0.45], t)
    p["fx.sparkle"] = 0.8
    p["fx.twinkle"] = t
    return p


CLIPS: Dict[str, Callable[[int, int, float], Pose]] = {"closed": closed, "opening": opening, "open": open_}

SPEC = CreatureSpec(
    name="treasure_chest",
    svg_path=PKG / "data" / "props" / "treasure_chest" / "treasure_chest.svg",
    rig_path=PKG / "targets" / "props" / "rigged" / "treasure_chest" / "treasure_chest.rig.json",
    view_label="Treasure Chest - Front",
    skeleton=skeleton,
    legs=(),
    ankle_joint="base",
    # Drawn at 512 units square, published in a 128 px frame.
    scale=0.25,
    svg_center_x=256.0,
    svg_ground_y=440.0,
    frame_size=(128, 128),
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
