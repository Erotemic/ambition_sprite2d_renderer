"""Player Robot v3's dash: a kick off the floor, then a lunge drawn as a smear.

The row borrowed the robot family's dash: an upright lean with the arms down,
and a start that wound BACK. The game shows the start for its first 50 ms and
the dash's first frame or two after it, so most of what a player saw of a dash
was a robot standing still and then leaning.

Here the start is already going: the body is low and pitched at the way it is
going, the back boot pushing. The dash is a lunge, head first, the arms thrown
back and the legs trailing, and the sheet draws it as a smear on the frames of
``SMEAR`` (a purple wash over the shell, ghosts of the body behind it and
streaks from its back edge; see ``player_robot_v3._compose``). Its last frames
come up out of the lunge toward the run.

Data plus maths: the rig builder calls ``author_dash``, and nothing here
touches the filesystem.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from ...authoring.rigdoc import RigDocument
from .player_robot_v3_body import SIDES, Arm, RigBody, WorldPose, write_frames

ROWS = ("dash_startup", "dash")

#: How strongly the smear is drawn on each frame of each row (0: none). The
#: start only streaks; the dash smears hardest while it is fastest.
SMEAR: Dict[str, Tuple[float, ...]] = {
    "dash_startup": (0.45, 0.6, 0.75, 0.9),
    "dash": (1.0, 1.0, 0.85, 0.55, 0.3, 0.12),
}


@dataclass(frozen=True)
class Beat:
    """One frame, in frame pixels and world degrees (0 points the way the
    robot faces, 90 hangs straight down)."""

    # The body: how far ahead of and above its standing place, its lean (a
    # positive torso pitches it forward), the head's own pitch, the squash.
    ahead: float
    rise: float
    torso: float
    head: float
    squash: float
    # Each ankle relative to its own hip: (ahead, under), and the foot's pitch
    # from rest.
    near_leg: Tuple[float, float, float]
    far_leg: Tuple[float, float, float]
    # The arms: (upper, lower) world angles of the near one, then the far one.
    near: Tuple[float, float]
    far: Tuple[float, float]
    squint: float = 0.55


BEATS: Dict[str, Tuple[Beat, ...]] = {
    # The kick: already low and pitched forward on the first frame, the back
    # boot pushing off and the front knee driving; then rising into the lunge.
    "dash_startup": (
        Beat(1.0, -1.0, 24.0, 3.0, 0.92, (-11.0, 15.0, -24.0), (8.0, 14.0, 10.0), (150.0, 170.0), (118.0, 150.0), 0.45),
        Beat(2.5, 0.5, 28.0, 4.0, 0.93, (-13.0, 14.0, -30.0), (9.0, 12.0, 8.0), (158.0, 174.0), (128.0, 156.0), 0.5),
        Beat(3.5, 2.0, 31.0, 5.0, 0.95, (-15.0, 12.5, -36.0), (9.0, 11.0, 6.0), (163.0, 177.0), (136.0, 160.0), 0.55),
        Beat(4.0, 3.0, 33.0, 5.0, 0.97, (-16.0, 11.5, -40.0), (8.5, 10.5, 4.0), (166.0, 178.0), (140.0, 162.0), 0.6),
    ),
    # The lunge, then up out of it toward the run.
    "dash": (
        Beat(4.0, 4.0, 34.0, 5.0, 0.98, (-17.0, 11.0, -42.0), (8.0, 10.0, 4.0), (168.0, 179.0), (142.0, 164.0), 0.65),
        Beat(4.5, 4.0, 34.0, 5.0, 0.98, (-17.5, 11.0, -44.0), (8.0, 10.0, 3.0), (169.0, 180.0), (143.0, 165.0), 0.65),
        Beat(4.5, 3.5, 30.0, 4.0, 0.99, (-15.0, 12.5, -36.0), (8.0, 11.5, 2.0), (162.0, 172.0), (135.0, 155.0), 0.6),
        Beat(4.0, 2.5, 24.0, 3.0, 1.0, (-12.0, 14.5, -26.0), (7.5, 13.0, 0.0), (150.0, 156.0), (118.0, 138.0), 0.5),
        Beat(3.0, 1.5, 17.0, 2.0, 1.0, (-8.0, 16.5, -14.0), (6.0, 14.5, -2.0), (138.0, 132.0), (95.0, 112.0), 0.4),
        Beat(2.0, 0.5, 11.0, 1.0, 1.0, (-5.0, 18.0, -6.0), (4.0, 16.0, -2.0), (130.0, 118.0), (75.0, 92.0), 0.3),
    ),
}


def _pose(body: RigBody, beat: Beat, dash_fx: float) -> Dict[str, float]:
    pose = WorldPose(
        root_x=beat.ahead,
        root_y=-beat.rise,
        pelvis=0.45 * beat.torso,
        torso=beat.torso,
        head=beat.head,
        squash=beat.squash,
        arms={"near": Arm(*beat.near), "far": Arm(*beat.far)},
    )
    for side, (ahead, under, pitch) in (("near", beat.near_leg), ("far", beat.far_leg)):
        hip_x, hip_y = body.hip_rest[side]
        pose.ankles[side] = (
            (hip_x + beat.ahead + ahead, hip_y - beat.rise + under),
            body.foot_rest[side] + pitch,
        )
    channels = body.channels(pose)
    channels["eye_squint"] = beat.squint
    channels["dash_fx"] = dash_fx
    return channels


def solve_dash(doc: RigDocument, row: str) -> Dict[str, List[float]]:
    body = RigBody(doc)
    frames = [_pose(body, beat, smear) for beat, smear in zip(BEATS[row], SMEAR[row])]
    return {
        key: [frame[key] for frame in frames]
        for key in frames[0]
        if not key.startswith("_")
    }


def author_dash(doc: RigDocument) -> None:
    """Replace the `dash_startup` and `dash` clips of a built v3 rig."""
    for row in ROWS:
        frames = int(doc.data["clips"][row]["frames"])
        assert frames == len(BEATS[row]) == len(SMEAR[row]), (row, frames, len(BEATS[row]), len(SMEAR[row]))
        write_frames(doc, row, solve_dash(doc, row))


__all__ = ["BEATS", "ROWS", "SMEAR", "author_dash", "solve_dash"]
