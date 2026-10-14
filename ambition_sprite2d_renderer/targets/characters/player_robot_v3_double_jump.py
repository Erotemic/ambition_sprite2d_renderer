"""Player Robot v3's second jump: a burst of the boot jets.

The row borrowed the kick off a wall: the body lay back 72 degrees and came
upright again. Off a wall that is a push; in open air it read as a fall
backward, on the jump the player uses most.

The robot has jets in its boots (the slow fall and the flight burn them), so
its second jump is one short burn. The knees come up, the jets fire and the
legs go straight down with the toes pointed, the arms go up with the body, and
then the body settles toward the fall. The sheet draws the jets on the frames
of ``JETS`` (see ``player_robot_v3._compose``).

Data plus maths: the rig builder calls ``author_double_jump``, and nothing
here touches the filesystem.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from ...authoring.rigdoc import RigDocument
from .player_robot_v3_body import SIDES, Arm, RigBody, WorldPose, write_frames

ROW = "double_jump"

#: How strongly the boot jets burn on each frame of the row (0 is no jet).
JETS: Tuple[float, ...] = (0.0, 1.0, 0.85, 0.6, 0.35, 0.0, 0.0)


@dataclass(frozen=True)
class Beat:
    """One frame, in frame pixels and world degrees (90 hangs straight down)."""

    # The body: how far it is over its standing height, its lean, the head.
    rise: float
    torso: float
    head: float
    squash: float
    # The legs: how far each ankle is under its hip, how far ahead of it, and
    # how far the toes point down.
    leg: float
    ahead: float
    toes: float
    # The arms: upper and lower of the near one, then of the far one.
    near: Tuple[float, float]
    far: Tuple[float, float]
    squint: float = 0.1


BEATS: Tuple[Beat, ...] = (
    # The knees come up and the arms come in: something to spring from.
    Beat(10.0, 9.0, 5.0, 0.94, 13.0, 4.0, -8.0, (132.0, 84.0), (62.0, 14.0), 0.3),
    # The burn: legs straight, toes down, arms thrown up, the head back.
    Beat(15.0, -5.0, -10.0, 1.07, 22.3, 0.0, 38.0, (198.0, 226.0), (-22.0, -50.0), 0.2),
    Beat(17.0, -4.0, -9.0, 1.04, 22.0, 0.0, 34.0, (214.0, 240.0), (-38.0, -64.0), 0.15),
    # The jets die and the arms come down.
    Beat(17.5, -2.0, -5.0, 1.01, 21.0, 0.5, 24.0, (188.0, 204.0), (-8.0, -26.0)),
    Beat(16.5, 0.0, -2.0, 1.0, 19.5, 1.0, 14.0, (160.0, 152.0), (20.0, 6.0)),
    # Toward the fall.
    Beat(15.0, 2.0, 0.0, 1.0, 18.0, 1.5, 8.0, (142.0, 122.0), (36.0, 26.0)),
    Beat(13.5, 3.0, 1.0, 1.0, 17.0, 2.0, 4.0, (132.0, 112.0), (44.0, 36.0)),
)

# Where an ankle hangs under its hip when the leg is straight. The near boot
# of the art stands behind its hip (the three-quarter view).
HANG_X = {"near": -5.0, "far": 1.0}
# A leg under this length is folded. The near one folds a little more than the
# far one, so the two read apart.
FOLDED_UNDER = 20.0
FOLD = {"near": 0.9, "far": 0.9 / 0.82}


def _pose(body: RigBody, beat: Beat) -> Dict[str, float]:
    pose = WorldPose(
        root_y=-beat.rise,
        pelvis=0.3 * beat.torso,
        torso=beat.torso,
        head=beat.head,
        squash=beat.squash,
        arms={"near": Arm(*beat.near), "far": Arm(*beat.far)},
    )
    for side in SIDES:
        hip_x, hip_y = body.hip_rest[side]
        straight = sum(body.leg[side]) * 0.97
        # The far leg is drawn shorter, so `straight` is of each side.
        fold = FOLD[side] if beat.leg <= FOLDED_UNDER else 1.0
        length = min(straight, beat.leg * fold)
        pose.ankles[side] = (
            (hip_x + HANG_X[side] + beat.ahead, hip_y - beat.rise + length),
            body.foot_rest[side] + beat.toes,
        )
    channels = body.channels(pose)
    channels["eye_squint"] = beat.squint
    return channels


def solve_double_jump(doc: RigDocument) -> Dict[str, List[float]]:
    body = RigBody(doc)
    frames = [_pose(body, beat) for beat in BEATS]
    return {
        key: [frame[key] for frame in frames]
        for key in frames[0]
        if not key.startswith("_")
    }


def author_double_jump(doc: RigDocument) -> None:
    """Replace the `double_jump` clip of a built v3 rig with the jet burst."""
    frames = int(doc.data["clips"][ROW]["frames"])
    assert frames == len(BEATS) == len(JETS), (frames, len(BEATS), len(JETS))
    write_frames(doc, ROW, solve_double_jump(doc))


__all__ = ["BEATS", "JETS", "ROW", "author_double_jump", "solve_double_jump"]
