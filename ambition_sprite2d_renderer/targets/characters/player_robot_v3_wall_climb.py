"""Player Robot v3 climbs a wall: hand over hand, its boots on the wall.

Jon, 2026-10-21: "I want to work on the robot pose for the climbing animation,
currently it looks bad. It doesn't look like it is climbing a wall at all."
The game had no row for a wall climb. The body drew its jump or its wall grab,
which hangs back from the wall and looks away from it.

The climb is a list of facts about a wall, and the joints are solved from them,
as the ladder climb of the back view is (``player_robot_v3_back``):

* the wall is a line in front of the robot, at the front of its body box
  (``WALL_X``), and the robot looks at it;
* a hand and the boot of the other side move as one pair. A limb that holds is
  on the wall and goes down at the speed of the climb; a limb that reaches comes
  off the wall and goes up in the other half of the cycle;
* the rig's two-bone IK puts the elbows down and the knees out from the wall.

The standing drawing is a three-quarter view, with the near shoulder at the
back of the body, where its hand cannot get to a wall. The climb is drawn from
the robot's PURE SIDE view (``Player Robot - Side Pure``, its own cell of the
SVG and its own rig): a torso and a pelvis seen from the side (Jon 2026-10-21:
"I think we need a side view torso for this pose so the arms can better reach
without stretching"), both shoulders on one socket, the hips close together.
Its other parts are clones of the side view's.

The game plays the row at the distance climbed (``BodyPoseView::climb_phase``),
so a body that stops on the wall holds its frame.

Data plus maths: the rig builder calls ``author_wall_climb`` after it has built
the document, and nothing here touches the filesystem.
"""

from __future__ import annotations

import math
from typing import Dict, List, Tuple

from ...authoring.rigdoc import RigDocument
from ...authoring.skeleton import two_bone_ik
from .player_robot_v3_body import SIDES, Arm, RigBody, WorldPose, rot, write_frames

ROW = "wall_climb"

Point = Tuple[float, float]

# Frame pixels; the robot faces +x and the wall is in front of it. The body box
# is 57 px wide about x 114.5 (``player_robot_v3.BODY_BOX_*``), so a body that
# touches a wall has the wall at its front edge.
WALL_X = 143.0
# The body goes toward the wall by this (a negative step back). The head looks
# up the wall, so its chin comes back from the wall and the body can go to it.
BODY_BACK = -6.0
BODY_UP = 5.0                       # the climb holds the body over its standing height
BODY_BOB = 1.2                      # it rises as a hand pulls
TORSO_LEAN, PELVIS_LEAN = 8.0, 4.0  # degrees into the wall
HEAD_UP = -35.0                     # the head looks up the wall
HEAD_BACK = 4.0                     # and comes back on its neck, off the wall

# A hand on the wall: its wrist this far back from the wall, between these
# heights. The fist points up the wall. The near arm is drawn over the head, so
# its hand reaches up past the face; the far hand is behind the head, so it
# stays under the chin, where it is seen.
WRIST_BACK = 4.5
HAND_HIGH = {"near": 96.0, "far": 100.0}
HAND_LOW = {"near": 124.0, "far": 126.0}
HAND_ANGLE = -70.0
REACH_OUT = 5.0                     # a hand that reaches comes off the wall by this

# A boot on the wall: its toe cap on the wall, the ankle between these heights.
ANKLE_HIGH, ANKLE_LOW = 138.0, 162.0
TOE_ANGLE = -75.0                   # the boot is flat on the wall, its toes up
STEP_OUT = 6.0

# A hand and the boot of the other side move together; the two pairs are half
# a cycle apart.
HOLD_PHASE = {"far": 0.0, "near": 0.5}
FOOT_PHASE = {"near": 0.0, "far": 0.5}


def _smooth(q: float) -> float:
    q = max(0.0, min(1.0, q))
    return q * q * (3.0 - 2.0 * q)


def _limb(phase: float, high: float, low: float, out: float) -> Tuple[float, float]:
    """(height, distance off the wall) of a limb at ``phase`` of its cycle.
    The first half it holds and goes from ``high`` down to ``low``; the second
    half it reaches back up, off the wall."""
    p = phase % 1.0
    if p < 0.5:
        return high + (low - high) * (p / 0.5), 0.0
    q = (p - 0.5) / 0.5
    return low + (high - low) * _smooth(q), out * math.sin(math.pi * q)


def _shoulders(body: RigBody, pose: WorldPose) -> Dict[str, Point]:
    channels = body.channels(pose)
    angles = {k: v for k, v in channels.items() if k in body.sk.bones}
    offsets = {"head": (0.0, channels["bone.head.y"])}
    for side in SIDES:
        offsets[f"{side}_arm_u"] = (channels[f"bone.{side}_arm_u.x"], channels[f"bone.{side}_arm_u.y"])
    root = (body.root[0] + pose.root_x, body.root[1] + pose.root_y)
    world = body.sk.world(angles, root=root, offsets=offsets)
    return {side: world[f"{side}_arm_u"].origin for side in SIDES}


def _pose(body: RigBody, phase: float) -> Dict[str, float]:
    rise = BODY_UP + BODY_BOB * math.sin(phase * math.tau * 2.0)
    pose = WorldPose(
        root_x=-BODY_BACK,
        root_y=-rise,
        pelvis=PELVIS_LEAN,
        torso=TORSO_LEAN,
        head=HEAD_UP,
    )
    shoulders = _shoulders(body, pose)
    for side in SIDES:
        height, off = _limb(phase + HOLD_PHASE[side], HAND_HIGH[side], HAND_LOW[side], REACH_OUT)
        wrist = (WALL_X - WRIST_BACK - off, height - rise)
        upper = body.sk.bones[f"{side}_arm_u"].length
        lower = body.sk.bones[f"{side}_arm_l"].length
        # Elbows bend down and away from the wall (``bend=-1``).
        a1, a2 = two_bone_ik(shoulders[side], wrist, upper, lower, bend=-1.0)
        pose.arms[side] = Arm(a1, a2, HAND_ANGLE)
    for side in SIDES:
        height, off = _limb(phase + FOOT_PHASE[side], ANKLE_HIGH, ANKLE_LOW, STEP_OUT)
        angle = body.foot_rest[side] + TOE_ANGLE
        toe = rot(body.toe[side], angle)
        pose.ankles[side] = ((WALL_X - toe[0] - off, height - rise), angle)
    channels = body.channels(pose)
    channels["bone.head.x"] = -HEAD_BACK
    channels["eye_squint"] = 0.12
    channels["head_look"] = 1.0
    return channels


def solve_wall_climb(doc: RigDocument, frames: int) -> Dict[str, List[float]]:
    body = RigBody(doc)
    poses = [_pose(body, i / frames) for i in range(frames)]
    return {key: [p[key] for p in poses] for key in poses[0] if not key.startswith("_")}


def author_wall_climb(doc: RigDocument) -> None:
    """Make the `wall_climb` clip of the pure side rig the solved climb."""
    frames = int(doc.data["clips"][ROW]["frames"])
    write_frames(doc, ROW, solve_wall_climb(doc, frames))


__all__ = ["ROW", "WALL_X", "author_wall_climb", "solve_wall_climb"]
