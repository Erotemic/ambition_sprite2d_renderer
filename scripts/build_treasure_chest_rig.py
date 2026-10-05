#!/usr/bin/env python3
"""Build the treasure chest's rig document from its SVG.

The SVG ``data/props/treasure_chest/treasure_chest.svg`` owns the art and
says where every joint is; ``rigbuild.creature_rig``, with the ``chest``
anatomy (a box, a hinged lid, a lock, the treasure heap), derives the
skeleton, binds every part to its bone and refreshes the SVG's rig catalog.
This script supplies only what the drawing cannot state: the frame, the rows
and the clips.
It never draws.

    uv run python scripts/build_treasure_chest_rig.py

The lid swings through its swap set (``lid.closed`` / ``lid.ajar`` /
``lid.up`` / ``lid.open``) and bounces by its squash (``bone.lid.scale_y``
about the hinge). The clips also key the effects' strengths (``fx.*``),
which ``targets/props/treasure_chest.py`` draws: the click and dust of the
lock giving way, and in the treasure rows the light leaking from under the
lid, the burst of light, the coin fountain, the sparkles. The treasure heap
shows only in the treasure rows (``treasure.shown``).

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

from ambition_sprite2d_renderer.rigbuild.chest import Pose, chest_spec, lid, track, write  # noqa: E402

PKG = ROOT / "ambition_sprite2d_renderer"
K = track

#: (row, frames, ms, loops).
#: (row, frames, ms, loops). The plain rows are an empty chest (an item can
#: be layered into it at runtime, or nothing); the treasure rows fill it with
#: the drawn heap. A player who takes the treasure flips the chest from
#: ``open_treasure`` to ``open``.
ROWS = [
    ("closed", 1, 100, True),
    ("opening", 10, 62, False),
    ("open", 1, 100, True),
    ("opening_treasure", 14, 62, False),
    ("open_treasure", 8, 110, True),
]

def closed(i: int, n: int, t: float) -> Pose:
    """Shut, held still."""
    p = lid("closed")
    p["treasure.shown"] = 0.0
    return p


def _opening_motion(p: Pose, t: float, frames: int) -> None:
    """The opening both versions share, over ``frames`` keys (10 or 14):
    it rattles, hops, the lock swings loose, the lid cracks, flies back and
    bounces on its hinge. The treasure version holds its last pose longer
    while its coins rain back."""
    pad = [0.0] * (frames - 10)
    one = [1.0] * (frames - 10)
    p["root_x"] = K([0, 4, -4, 3, 0, 0, 0, 0, 0, 0] + pad, t)
    p["root_y"] = K([0, 0, 0, -14, 2, 0, -4, 0, 0, 0] + pad, t)
    p["base"] = K([0, 1.5, -1.5, 1, 0, 0, 0, 0, 0, 0] + pad, t)
    # The closed lid rattles on its hinge before it gives.
    p["lid"] = K([0, -2.5, 2.5, -3, 0, 0, 0, 0, 0, 0] + pad, t)
    # Thrown back, the open lid overshoots and settles (its squash about the hinge).
    p["bone.lid.scale_y"] = K([1, 1, 1, 1, 1, 1, 1, 1.1, 0.94, 1.0] + one, t)
    # The lock jolts, then swings loose on its staple and settles.
    p["lock"] = K([0, 6, -6, 10, -26, 18, -12, 8, -3, 0] + pad, t)
    p["fx.click"] = K([0, 0, 0, 0.4, 1, 0.3, 0, 0, 0, 0] + pad, t)
    p["fx.dust"] = K([0, 0, 0, 0, 1, 0.4, 0, 0, 0, 0] + pad, t)


#: The lid's look on each frame of an opening.
OPENING_LIDS = ["closed", "closed", "closed", "closed", "ajar", "ajar", "up", "open", "open", "open"]


def opening(i: int, n: int, t: float) -> Pose:
    """The empty chest opening: no light, nothing inside (an item placed at
    runtime goes in the ``item`` socket's layer)."""
    p = lid(OPENING_LIDS[i])
    p["treasure.shown"] = 0.0
    _opening_motion(p, t, 10)
    return p


def open_(i: int, n: int, t: float) -> Pose:
    """Open and empty, held still."""
    p = lid("open")
    p["treasure.shown"] = 0.0
    return p


def opening_treasure(i: int, n: int, t: float) -> Pose:
    """The same opening on a chest full of treasure: light leaks under the
    cracked lid, the lid flies back in a burst of light and the heap spouts
    a fountain of coins that rain back into it."""
    p = lid((OPENING_LIDS + ["open"] * 4)[i])
    p["treasure.shown"] = 1.0
    _opening_motion(p, t, 14)
    # The heap heaves as the coins burst from it.
    p["bone.treasure.scale_y"] = K([1, 1, 1, 1, 1, 1, 1, 1.08, 1.03, 1, 1, 1, 1, 1], t)
    p["fx.leak"] = K([0, 0, 0, 0, 0.8, 1, 0, 0, 0, 0, 0, 0, 0, 0], t)
    p["fx.burst"] = K([0, 0, 0, 0, 0, 0, 0.6, 1, 0.7, 0.4, 0.2, 0, 0, 0], t)
    p["fx.glow"] = K([0, 0, 0, 0, 0.3, 0.5, 0.8, 1, 1, 0.9, 0.8, 0.75, 0.7, 0.7], t)
    p["fx.rays"] = K([0, 0, 0, 0, 0.3, 0.6, 0.9, 1, 1, 0.85, 0.7, 0.6, 0.5, 0.45], t)
    # The coin fountain's clock: 0 as the lid flies back, 1 as the last coin lands.
    p["fx.coins"] = K([0, 0, 0, 0, 0, 0, 0, 0.08, 0.24, 0.4, 0.56, 0.72, 0.88, 1], t)
    p["fx.sparkle"] = K([0, 0, 0, 0, 0, 0, 0, 0.5, 1, 1, 1, 1, 0.8, 0.6], t)
    return p


def open_treasure(i: int, n: int, t: float) -> Pose:
    """Open on the treasure, glowing and twinkling."""
    p = lid("open")
    p["treasure.shown"] = 1.0
    p["fx.glow"] = K([0.7, 0.8, 0.9, 0.8, 0.7, 0.6, 0.65, 0.7, 0.7], t)
    p["fx.rays"] = K([0.45, 0.55, 0.65, 0.55, 0.45, 0.4, 0.42, 0.45, 0.45], t)
    p["fx.sparkle"] = 0.8
    p["fx.twinkle"] = t
    return p


CLIPS: Dict[str, Callable[[int, int, float], Pose]] = {
    "closed": closed,
    "opening": opening,
    "open": open_,
    "opening_treasure": opening_treasure,
    "open_treasure": open_treasure,
}


SPEC = chest_spec(
    name="treasure_chest",
    svg_path=PKG / "data" / "props" / "treasure_chest" / "treasure_chest.svg",
    rig_path=PKG / "targets" / "props" / "rigged" / "treasure_chest" / "treasure_chest.rig.json",
    view_label="Treasure Chest - Front",
    # Drawn at 512 units square, published in a 128 px frame.
    scale=0.25,
    svg_center_x=256.0,
    svg_ground_y=440.0,
    frame_size=(128, 128),
    rows=ROWS,
    clips=CLIPS,
    defaults={"lid.closed": 1.0, "treasure.shown": 0.0},
)


def main(argv: List[str] | None = None) -> int:
    del argv
    for path in write(SPEC):
        print(path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
