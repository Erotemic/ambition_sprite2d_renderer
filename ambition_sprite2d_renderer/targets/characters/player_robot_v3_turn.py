"""Player Robot v3's turnaround: the body turns, and the head comes after it.

The game flips a body's facing at once and draws this row over the first
0.22 s after the flip (`TURN_SECS` in `ambition_sim_view`), slaved to that
time. The row is drawn in the NEW facing. On its first frames the chest is
open to the camera and the head still looks back the way the robot was facing
(the head seen from its other side, as in the back air); its middle frames are
the front view (`player_robot_v3_front`); on its last frames the head has come
round and the body settles.

The turn of the back to the camera (`turn_away`) starts here too: its first
frames are of the side view, its last of the back view.

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
AWAY_ROW = "turn_away"


def turnaround(body: RigBody) -> List[Key]:
    """Keys of the side frames on the turn's timeline. Frames 0-1 are before
    the front view, frames 5-7 after it (`FRONT_FRAMES`)."""
    near, far = body.arm_rest["near"], body.arm_rest["far"]
    stowed = dict(blade=0.0, face="open")
    return [
        # Turning away from the old side: chest to the camera, the head still
        # looking back, the arms swung with the turn, the body a little down.
        Key(at=0.0, near=(near.upper - 22.0, near.lower - 26.0, BLADE_DRAWN_DEG),
            far=(far.upper + 20.0, far.lower + 22.0), torso=-3.0, head=2.0, drop=1.0,
            squash=0.97, turn="open", look_back=True, squint=0.1, **stowed),
        Key(at=0.25, near=(near.upper - 30.0, near.lower - 36.0, BLADE_DRAWN_DEG),
            far=(far.upper + 28.0, far.lower + 30.0), torso=-4.0, head=3.0, drop=1.6,
            squash=0.96, turn="open", look_back=True, squint=0.15, **stowed),
        # Out of the front view onto the new side: the chest still open, the
        # arms swinging on past rest, the head leading.
        Key(at=0.62, near=(near.upper + 14.0, near.lower + 16.0, BLADE_DRAWN_DEG),
            far=(far.upper - 12.0, far.lower - 14.0), torso=3.0, head=-3.0, drop=0.8,
            squash=1.02, turn="open", squint=0.05, ease="out", **stowed),
        Key(at=0.8, near=(near.upper + 6.0, near.lower + 7.0, BLADE_DRAWN_DEG),
            far=(far.upper - 5.0, far.lower - 6.0), torso=1.5, head=-1.0, drop=0.3,
            squash=1.01, **stowed),
        replace(rest(body, 1.0), face="open"),
    ]


def turn_away(body: RigBody) -> List[Key]:
    """Keys of the side frames of the turn of the back to the camera. Frames
    0-1 are of the side view; frames 2-3 are of the back view
    (`player_robot_v3_back.BACK_FRAMES`), so the keys stop at frame 1.

    The chest turns from the camera (the profile torso) and the arms swing
    behind with the turn; the head comes after the body.
    """
    near, far = body.arm_rest["near"], body.arm_rest["far"]
    stowed = dict(blade=0.0, face="open")
    return [
        replace(rest(body, 0.0), face="open"),
        Key(at=0.125, near=(near.upper + 6.0, near.lower + 8.0, BLADE_DRAWN_DEG),
            far=(far.upper - 5.0, far.lower - 6.0), torso=2.0, head=-1.0, drop=0.6,
            squash=0.98, turn="profile", **stowed),
        Key(at=0.375, near=(near.upper + 16.0, near.lower + 20.0, BLADE_DRAWN_DEG),
            far=(far.upper - 14.0, far.lower - 16.0), torso=4.0, head=-2.5, drop=1.2,
            squash=0.97, turn="profile", ease="out", **stowed),
    ]


def _solve(doc: RigDocument, row: str, keys: List[Key]) -> Dict[str, List[float]]:
    body = RigBody(doc)
    frames = [_pose(body, sample(keys, phase)) for phase in frame_phases(int(doc.clips[row]["frames"]), False)]
    return {key: [frame[key] for frame in frames] for key in frames[0] if not key.startswith("_")}


def solve_turnaround(doc: RigDocument) -> Dict[str, List[float]]:
    return _solve(doc, ROW, turnaround(RigBody(doc)))


def author_turnaround(doc: RigDocument) -> None:
    """Replace the `turnaround` clip of a built v3 rig with the turn, and the
    `turn_away` clip with its side frames."""
    write_frames(doc, ROW, solve_turnaround(doc))
    write_frames(doc, AWAY_ROW, _solve(doc, AWAY_ROW, turn_away(RigBody(doc))))


__all__ = ["AWAY_ROW", "ROW", "author_turnaround", "solve_turnaround", "turn_away", "turnaround"]
