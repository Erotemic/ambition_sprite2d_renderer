"""Player robot v3 from the front: the frames of a row that draw the front view.

The front view is a third SVG view with a rig of its own
(``rigged/player_robot_v3/player_robot_v3_front.rig.json``), at the scale and
in the frame of the side view. A row named in ``FRONT_FRAMES`` draws the listed
frames from it and the others from the side view. The turnaround passes
through it: the robot faces the camera between its two side views.

From the front the robot is one picture for each facing (the ear cup stays on
its right ear, at the left of the frame), so a front frame is not mirrored.
The row of the other facing plays the front frames in the other order instead,
so that the body still sways toward where it turns.

The antenna stays rigid on the head, by ruling (see ``player_robot_v3_gait``).

Data and mathematics only: the rig builder calls ``author_front_rows``.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

#: For each row, the frames drawn from the front view.
FRONT_FRAMES: Dict[str, Tuple[int, ...]] = {"turnaround": (2, 3, 4)}

# The front frames of the turnaround, toward the side the robot turns to:
# (root x, root y, pelvis, torso, head) in rig pixels and degrees. The body
# sways across, and the head comes after it.
TURN_BEATS: Tuple[Tuple[float, float, float, float, float], ...] = (
    (-2.0, 1.2, -1.5, -4.0, -3.0),
    (0.0, 0.6, 0.0, 0.0, -2.5),
    (2.0, 0.8, 1.5, 4.0, 1.5),
)


def _keys(values: List[float]) -> Dict[str, list]:
    count = len(values)
    times = [i / max(1, count - 1) for i in range(count)]
    return {"keys": [[round(t, 6), round(v, 5)] for t, v in zip(times, values)]}


def front_frame(row: str, frame_idx: int, mirrored: bool) -> int:
    """The frame of the front clip of ``row`` that sheet frame ``frame_idx``
    draws. The row of the other facing plays them in the other order."""
    frames = FRONT_FRAMES[row]
    index = frames.index(frame_idx)
    return len(frames) - 1 - index if mirrored else index


def author_front_rows(doc: dict) -> None:
    """Write the clips of ``FRONT_FRAMES`` into the front rig document ``doc``."""
    clips = doc.setdefault("clips", {})
    series = list(zip(*TURN_BEATS))
    clips["turnaround"] = {
        "loop": False,
        "frames": len(TURN_BEATS),
        "duration_ms": 40,
        "channels": {
            name: _keys(list(values))
            for name, values in zip(("root_x", "root_y", "pelvis", "torso", "head"), series)
        },
    }


__all__ = ["FRONT_FRAMES", "author_front_rows", "front_frame"]
