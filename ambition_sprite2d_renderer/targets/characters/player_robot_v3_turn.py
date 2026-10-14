"""Player Robot v3's turnaround: the body turns, and the head comes after it.

The game flips a body's facing at once and draws this row over the first
0.16 s after the flip (`TURN_SECS` in `ambition_sim_view`), slaved to that
time. The row is drawn in the NEW facing. On its first half the chest is open
to the camera and the head still looks back the way the robot was facing (the
head seen from its other side, as in the back air); on the second half the
head has come round and the body settles.

Keys of the strike machinery (`player_robot_v3_strikes`) with the blade
stowed. The rig builder calls ``author_turnaround``; nothing here touches the
filesystem.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Dict, List

from ...authoring.rigdoc import RigDocument
from .player_robot_v3_body import RigBody, write_frames
from .player_robot_v3_strikes import BLADE_DRAWN_DEG, Key, _pose, frame_phases, rest, sample

ROW = "turnaround"


def turnaround(body: RigBody) -> List[Key]:
    near, far = body.arm_rest["near"], body.arm_rest["far"]
    stowed = dict(blade=0.0, face="open")
    return [
        # Mid-turn: chest to the camera, the head still looking back, the arms
        # swung with the turn, the body a little down.
        Key(at=0.0, near=(near.upper - 30.0, near.lower - 36.0, BLADE_DRAWN_DEG),
            far=(far.upper + 28.0, far.lower + 30.0), torso=-4.0, head=3.0, drop=2.0,
            squash=0.95, turn="open", look_back=True, squint=0.15, **stowed),
        Key(at=0.45, near=(near.upper - 20.0, near.lower - 22.0, BLADE_DRAWN_DEG),
            far=(far.upper + 18.0, far.lower + 18.0), torso=-2.0, head=1.0, drop=1.5,
            squash=0.97, turn="open", look_back=True, squint=0.1, **stowed),
        # The head has come round; the arms swing on past rest.
        Key(at=0.6, near=(near.upper + 10.0, near.lower + 12.0, BLADE_DRAWN_DEG),
            far=(far.upper - 8.0, far.lower - 10.0), torso=3.0, head=-3.0, drop=0.5,
            squash=1.03, ease="out", **stowed),
        replace(rest(body, 1.0), face="open"),
    ]


def solve_turnaround(doc: RigDocument) -> Dict[str, List[float]]:
    body = RigBody(doc)
    keys = turnaround(body)
    frames = [_pose(body, sample(keys, phase)) for phase in frame_phases(int(doc.clips[ROW]["frames"]), False)]
    return {key: [frame[key] for frame in frames] for key in frames[0] if not key.startswith("_")}


def author_turnaround(doc: RigDocument) -> None:
    """Replace the `turnaround` clip of a built v3 rig with the turn."""
    write_frames(doc, ROW, solve_turnaround(doc))


__all__ = ["ROW", "author_turnaround", "solve_turnaround", "turnaround"]
