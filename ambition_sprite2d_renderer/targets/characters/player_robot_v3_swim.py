"""Player Robot v3 swims: a paddle, the body leaned forward in the water.

Jon, 2026-10-26: "We need to improve the swimming pose for the robot." The
row was the old side robot's swim, resampled: the body upright and folded,
the legs under it, the arms hardly moving. It read as a robot sitting in the
water, not one that swims.

The swim is a list of facts about a body in water, and the joints are solved
from them, as the climb's are (``player_robot_v3_wall_climb``):

* the body leans well forward (``BODY_TILT`` about the pelvis), and the head
  lifts to look ahead (``HEAD_LIFT``);
* each hand paddles round a loop in front of the chest, half a cycle after
  the other hand: it reaches ahead over the top of the loop and presses down
  and back under it (``_stroke``). The robot's head is big and its arms are
  short, so a front crawl would go on under the head, where it is not seen;
* the boots kick up and down behind the hips, the two of them opposite, two
  kicks to each stroke, the toes pointed back (``_kick``);
* the body rocks a little with each pull.

It is drawn from the PURE SIDE view, as the climb and the crawl are: both
shoulders on one socket, so a hand that reaches ahead reaches from the
shoulder and not from behind the body.

Data plus maths: the rig builder calls ``author_swim``; nothing here touches
the filesystem.
"""

from __future__ import annotations

import math
from typing import Dict, List, Tuple

from ...authoring.rigdoc import RigDocument
from ...authoring.skeleton import two_bone_ik
from .player_robot_v3_body import SIDES, Arm, RigBody, WorldPose, rot, write_frames

ROW = "swim"

Point = Tuple[float, float]

#: The body leans forward about its pelvis by this (world degrees). His head
#: is big and his arms short: a body near level would hide the stroke under
#: the head, so the body leans as a paddling swimmer's does, the head up.
BODY_TILT = 50.0
#: The head is turned back up from the body by this, so the visor looks ahead
#: and not down into the water.
HEAD_LIFT = 42.0
#: The pelvis is moved by this from where it stands (frame pixels): back and
#: up, so the body is over the middle of the body box and in the water, not
#: on the floor.
BODY_SHIFT = (-10.0, -16.0)
#: The body rocks this many degrees with the strokes, and bobs this much.
ROCK, BOB = 3.0, 1.4

#: The loop of a hand, in arm lengths about its shoulder, in the picture
#: (``+x`` ahead, ``+y`` down): its middle ahead of and under the shoulder,
#: its half widths. A hand goes ahead over the top of the loop (the reach)
#: and presses down and back under it (the pull): a paddle.
LOOP_MIDDLE = (0.42, 0.30)
LOOP_HALF = (0.48, 0.34)
HOLD_PHASE = {"near": 0.0, "far": 0.5}

#: The kick: each boot this far up and down (frame pixels) behind and under
#: the hips, the legs a little bent, the toes pointed back.
KICK = 6.0
LEG_STRAIGHT = 0.92
TOE_POINT = 85.0
KICK_PHASE = {"near": 0.0, "far": 0.5}


def _smooth(q: float) -> float:
    q = max(0.0, min(1.0, q))
    return q * q * (3.0 - 2.0 * q)


def _ahead(tilt: float) -> Point:
    """The way the body points, head first (its up turned by ``tilt``)."""
    return rot((0.0, -1.0), tilt)


def _under(tilt: float) -> Point:
    """The way the belly faces (its front turned by ``tilt``)."""
    return rot((1.0, 0.0), tilt)


def _stroke(phase: float) -> Point:
    """Where a hand is at ``phase`` of its stroke, as (ahead, down) in arm
    lengths from the shoulder: round the loop, ahead at the top and back at
    the bottom (``phase`` 0 is the end of the reach)."""
    a = phase * math.tau
    return LOOP_MIDDLE[0] + LOOP_HALF[0] * math.cos(a), LOOP_MIDDLE[1] - LOOP_HALF[1] * math.sin(-a)


def _world(body: RigBody, pose: WorldPose) -> Dict[str, Point]:
    """Where each bone of ``pose`` starts."""
    channels = body.channels(pose)
    angles = {k: v for k, v in channels.items() if k in body.sk.bones}
    offsets = {"head": (0.0, channels["bone.head.y"])}
    for side in SIDES:
        offsets[f"{side}_arm_u"] = (channels[f"bone.{side}_arm_u.x"], channels[f"bone.{side}_arm_u.y"])
    root = (body.root[0] + pose.root_x, body.root[1] + pose.root_y)
    return {name: bone.origin for name, bone in body.sk.world(angles, root=root, offsets=offsets).items()}


def swim_pose(body: RigBody, phase: float) -> WorldPose:
    """The body at ``phase`` of the swim, in world terms."""
    pull = math.sin(phase * math.tau * 2.0)
    tilt = BODY_TILT + ROCK * pull
    pose = WorldPose(
        root_x=BODY_SHIFT[0],
        root_y=BODY_SHIFT[1] + BOB * pull,
        pelvis=tilt,
        torso=tilt,
        head=tilt - HEAD_LIFT,
    )
    joints = _world(body, pose)
    ahead, under = _ahead(tilt), _under(tilt)
    for side in SIDES:
        upper = body.sk.bones[f"{side}_arm_u"].length
        lower = body.sk.bones[f"{side}_arm_l"].length
        length = upper + lower
        shoulder = joints[f"{side}_arm_u"]
        a, u = _stroke(phase + HOLD_PHASE[side])
        wrist = (shoulder[0] + a * length, shoulder[1] + u * length)
        # The elbow bends down, under the arm, as a paddling arm's does.
        a1, a2 = two_bone_ik(shoulder, wrist, upper, lower, bend=1.0)
        pose.arms[side] = Arm(a1, a2, None)
    for side in SIDES:
        hip = joints[f"{side}_leg_u"]
        upper, lower = body.leg[side]
        reach = (upper + lower) * LEG_STRAIGHT
        kick = KICK * math.sin((phase * 2.0 + KICK_PHASE[side]) * math.tau)
        ankle = (hip[0] - ahead[0] * reach + under[0] * kick, hip[1] - ahead[1] * reach + under[1] * kick)
        pose.ankles[side] = (ankle, body.foot_rest[side] + tilt + TOE_POINT)
    return pose


def solve_swim(doc: RigDocument, frames: int) -> Dict[str, List[float]]:
    body = RigBody(doc)
    poses = []
    for i in range(frames):
        channels = body.channels(swim_pose(body, i / frames))
        channels["head_look"] = 0.0
        poses.append(channels)
    return {key: [p[key] for p in poses] for key in poses[0] if not key.startswith("_")}


def author_swim(doc: RigDocument) -> None:
    """Make the `swim` clip of the pure side rig the solved swim."""
    frames = int(doc.data["clips"][ROW]["frames"])
    write_frames(doc, ROW, solve_swim(doc, frames))


__all__ = ["ROW", "author_swim", "solve_swim", "swim_pose"]
