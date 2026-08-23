"""Player robot v3's gameplay body, per pose, solved from his own rig.

`player_robot_v3.body_metrics` authors ONE rectangle — 57 x 91 around the torso
and legs, deliberately tighter than the 71 x 103 silhouette, because a body that
followed the art inflated every time he flourished. That box is right and this
module does not replace it: it answers the question the single box cannot, which
is *where is his body when he is not standing*.

The mechanism is rigid offsets from the SKELETON, calibrated on `idle` so the
idle row reproduces the authored rectangle exactly. The art is welded to the
bones, so the distance from the head joint to the crest of his head is a
constant — measuring it once and carrying it to every pose is the same claim the
authored box already makes, extended to poses it was never asked about. The
alternative (`pose_bodies="art"`, the measured alpha union per row) is what the
authored box exists to overrule.

⛔ ARMS AND ANTENNA ARE NOT BODY. The envelope is head + torso + pelvis + legs,
which is exactly the set the 57 px width was chosen to cover; including the arms
is how the width was 71 before.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Dict, Iterable, List, Tuple

# The bones his BODY is made of. `*_arm_*` are excluded on purpose (see above),
# and the antenna is art on the head rather than a bone of its own.
BODY_BONES = (
    "head",
    "torso",
    "pelvis",
    "far_leg_u",
    "far_leg_l",
    "far_leg_foot",
    "near_leg_u",
    "near_leg_l",
    "near_leg_foot",
)


def _doc():
    from .player_robot_v3 import load_doc

    return load_doc()


def _joint_envelope(world) -> Tuple[float, float, float, float]:
    """`(x0, y0, x1, y1)` over the body bones' joints, in rig-frame pixels."""
    xs: List[float] = []
    ys: List[float] = []
    for name in BODY_BONES:
        bone = world.get(name)
        if bone is None:
            continue
        xs.append(bone.origin[0])
        ys.append(bone.origin[1])
    return min(xs), min(ys), max(xs), max(ys)


def _row_envelope(animation: str, frames: int) -> Tuple[float, float, float, float]:
    """The joint envelope over every frame of one row.

    The union, not frame 0: a row's body is what it occupies across the whole
    animation, which is the same rule the measured road uses and the reason a
    two-frame flinch does not get a body that only fits its first frame.
    """
    doc = _doc()
    box = None
    for index in range(max(1, frames)):
        world, _params = doc.solve(animation, doc.frame_time(animation, index, frames))
        env = _joint_envelope(world)
        box = env if box is None else (
            min(box[0], env[0]), min(box[1], env[1]),
            max(box[2], env[2]), max(box[3], env[3]),
        )
    return box


@lru_cache(maxsize=1)
def _calibration() -> Tuple[float, float, float, float]:
    """How far the authored idle box sits outside idle's joint envelope.

    Four constants, in rig pixels, and they are what turn a skeleton into a
    body: the crest of his head is ~42 px above the head JOINT, his soles ~7 px
    below the ankle. Solved against the authored box rather than chosen, so
    `idle` reproduces `body_metrics` to the pixel and every other pose is stated
    relative to the same rectangle.
    """
    from .player_robot_v3 import (
        BODY_BOX_BOTTOM_PX,
        BODY_BOX_CENTER_X,
        BODY_BOX_TOP_PX,
        BODY_BOX_WIDTH_PX,
    )

    idle_frames = _row_frames("idle")
    x0, y0, x1, y1 = _row_envelope("idle", idle_frames)
    left = BODY_BOX_CENTER_X - BODY_BOX_WIDTH_PX / 2.0
    right = left + BODY_BOX_WIDTH_PX
    return (left - x0, BODY_BOX_TOP_PX - y0, right - x1, BODY_BOX_BOTTOM_PX - y1)


def _row_frames(animation: str) -> int:
    from .player_robot_v3 import ROWS

    for name, frames, _duration in ROWS:
        if name == animation:
            return int(frames)
    return 1


def body_rect(animation: str, frames: int) -> Dict[str, int]:
    """One pose's gameplay body, in PUBLISHED (padded) frame pixels."""
    from .player_robot_v3 import PUBLISH_PADDING

    pad_left, pad_top, _pad_right, _pad_bottom = PUBLISH_PADDING
    dx0, dy0, dx1, dy1 = _calibration()
    x0, y0, x1, y1 = _row_envelope(animation, frames)
    left, top = x0 + dx0, y0 + dy0
    right, bottom = x1 + dx1, y1 + dy1
    return {
        "name": "body",
        "x": int(round(left)) + pad_left,
        "y": int(round(top)) + pad_top,
        "w": max(1, int(round(right - left))),
        "h": max(1, int(round(bottom - top))),
    }


def hurtbox_parts_for_rows(rows: Iterable[Tuple[str, int, int]]) -> Dict[str, dict]:
    """One authored body rectangle per row, keyed by the row's own name."""
    out: Dict[str, dict] = {}
    for name, frames, _duration in rows:
        out[name] = {"parts": [body_rect(name, int(frames))]}
    return out
