"""Player Robot v3 crawls: on its hands and knees, its body along the floor.

Jon, 2026-10-21: "make the crawl animation look more like the wall climb, but
on the floor instead of the wall", then: "the robot body should be rotated
90degrees so it is parallel to the floor, but have the head kept up so it can
see in front of it. I.e. make it look like a real crawl." The game draws the
`crouch_walk` row for a body that moves in its crouch (a crawl falls back to
it).

The crawl is a list of facts about the floor, as the wall climb
(``player_robot_v3_wall_climb``) is about its wall:

* the pelvis and the torso turn a quarter turn, so the body is along the
  floor; the head stays up and looks where the robot goes;
* a hand and the knee of the other side move as one pair, as a hand and a boot
  do on the wall. A limb that holds is on the floor and goes back at the speed
  of the crawl; a limb that reaches comes off the floor and goes forward in the
  other half of the cycle;
* a knee is on the floor under the hip, and the shin and the boot lie back
  along the floor behind it.

It is drawn from the PURE SIDE view, as the climb is: both shoulders are on
one socket and the hips are close together, so the limbs of the two sides are
under one body.

Data plus maths: the rig builder calls ``author_crawl``; nothing here touches
the filesystem.
"""

from __future__ import annotations

import copy
import math
from typing import Dict, List, Tuple

from ...authoring.rigdoc import RigDocument
from ...authoring.skeleton import two_bone_ik
from .player_robot_v3_body import SIDES, Arm, RigBody, WorldPose, write_frames
from .player_robot_v3_wall_climb import ROW as WALL_CLIMB_ROW
from .player_robot_v3_wall_climb import _limb

ROW = "crouch_walk"
#: The rows drawn from the pure side view: the climb, and the crawl.
PURE_SIDE_ROWS: Tuple[str, ...] = (WALL_CLIMB_ROW, ROW)

Point = Tuple[float, float]

# Frame pixels and world degrees; the robot faces +x and the floor is the
# ground line. 90 degrees is a bone along the floor, forward.
PELVIS_ANGLE, TORSO_ANGLE = 90.0, 88.0  # along the floor, the chest down
HEAD_ANGLE = -4.0                       # upright, looking ahead
# The torso is about as long as it is deep and the head is more than twice as
# wide, so a head on its neck hides the body and the crawl reads as a head on a
# post. The head goes forward off its neck by this, and down by this, so the
# body shows behind it.
HEAD_FORWARD, HEAD_DOWN = 26.0, 4.0
BODY_BOB = 1.0                          # the body rises as a hand pulls
# The body goes back by this, so the crawl, from the boots to the face, is over
# the middle of the body box, as the crouch is: the head is far ahead of the hips.
BODY_BACK = 22.0

# A knee on the floor: its joint this far over the floor. The thigh swings
# between these angles from straight down (positive is forward).
KNEE_UP = 7.0
THIGH_FORWARD, THIGH_BACK = 22.0, -22.0
KNEE_LIFT = 5.0                         # a knee that reaches comes off the floor by this
# The shin goes back to an ankle this far over the floor. The boot hangs under
# its ankle, upside down; at 12 a held boot and a held hand touch the ground
# line and do not go through it (measured from the render).
ANKLE_UP = 12.0
BOOT_ANGLE = 185.0                      # the boot trails back along the floor, its sole up

# A hand on the floor: its wrist this far over the floor, between these
# distances ahead of its shoulder. The fist points ahead.
WRIST_UP = 8.0
HAND_AHEAD, HAND_BACK = 6.0, -4.0
HAND_ANGLE = 20.0
REACH_UP = 6.0                          # a hand that reaches comes off the floor by this

# A hand and the knee of the other side move together; the two pairs are half
# a cycle apart (as on the wall).
HOLD_PHASE = {"far": 0.0, "near": 0.5}
KNEE_PHASE = {"near": 0.0, "far": 0.5}


def _joints(body: RigBody, pose: WorldPose) -> Dict[str, Point]:
    """Where the shoulders and the hips of `pose` are."""
    channels = body.channels(pose)
    angles = {k: v for k, v in channels.items() if k in body.sk.bones}
    offsets = {"head": (0.0, channels["bone.head.y"])}
    for side in SIDES:
        offsets[f"{side}_arm_u"] = (channels[f"bone.{side}_arm_u.x"], channels[f"bone.{side}_arm_u.y"])
    root = (body.root[0] + pose.root_x, body.root[1] + pose.root_y)
    world = body.sk.world(angles, root=root, offsets=offsets)
    return {name: world[name].origin for side in SIDES for name in (f"{side}_arm_u", f"{side}_leg_u")}


def _pose(body: RigBody, ground: float, phase: float) -> Dict[str, float]:
    pose = WorldPose(root_x=-BODY_BACK, pelvis=PELVIS_ANGLE, torso=TORSO_ANGLE, head=HEAD_ANGLE)
    # The body goes down until a held knee is on the floor.
    thigh = max(body.leg[side][0] for side in SIDES)
    hip_y = max(_joints(body, pose)[f"{side}_leg_u"][1] for side in SIDES)
    hip_up = KNEE_UP + thigh * math.cos(math.radians(THIGH_FORWARD))
    pose.root_y = (ground - hip_up) - hip_y - BODY_BOB * abs(math.sin(phase * math.tau))
    joints = _joints(body, pose)
    for side in SIDES:
        ahead, off = _limb(phase + HOLD_PHASE[side], HAND_AHEAD, HAND_BACK, REACH_UP)
        shoulder = joints[f"{side}_arm_u"]
        wrist = (shoulder[0] + ahead, ground - WRIST_UP - off)
        upper = body.sk.bones[f"{side}_arm_u"].length
        lower = body.sk.bones[f"{side}_arm_l"].length
        # Elbows bend back, under the body (``bend=-1``, as on the wall).
        a1, a2 = two_bone_ik(shoulder, wrist, upper, lower, bend=-1.0)
        pose.arms[side] = Arm(a1, a2, HAND_ANGLE)
    for side in SIDES:
        # The thigh swings from forward to back while the knee holds, and the
        # knee comes up off the floor while it reaches forward.
        swing, off = _limb(phase + KNEE_PHASE[side], THIGH_FORWARD, THIGH_BACK, KNEE_LIFT)
        hip = joints[f"{side}_leg_u"]
        upper, lower = body.leg[side]
        rad = math.radians(swing)
        knee = (hip[0] + upper * math.sin(rad), hip[1] + upper * math.cos(rad) - off)
        # The shin goes back from the knee to the ankle's height. The two hips
        # are not at one height on a body along the floor, so each shin has
        # its own angle.
        rise = (ground - ANKLE_UP - off) - knee[1]
        shin = math.pi - math.asin(max(-1.0, min(1.0, rise / lower)))
        ankle = (knee[0] + lower * math.cos(shin), knee[1] + lower * math.sin(shin))
        # The top of the boot is on the floor, its toes back.
        pose.ankles[side] = (ankle, body.foot_rest[side] + BOOT_ANGLE)
    channels = body.channels(pose)
    # The head's offset is in the frame of the torso, which points forward:
    # its up is forward, and its right is down.
    channels["bone.head.y"] = -HEAD_FORWARD
    channels["bone.head.x"] = HEAD_DOWN
    channels["eye_squint"] = 0.12
    channels["head_look"] = 1.0
    return channels


def solve_crawl(doc: RigDocument, frames: int) -> Dict[str, List[float]]:
    body = RigBody(doc)
    ground = float(doc.frame["ground_y"])
    poses = [_pose(body, ground, i / frames) for i in range(frames)]
    return {key: [p[key] for p in poses] for key in poses[0] if not key.startswith("_")}


def author_crawl(doc: RigDocument) -> None:
    """Make the `crouch_walk` clip of the pure side rig the solved crawl."""
    frames = int(doc.data["clips"][ROW]["frames"])
    write_frames(doc, ROW, solve_crawl(doc, frames))


def lend_pure_side_rows(pure: RigDocument, side: RigDocument) -> None:
    """Give the side rig the pure side rig's rows, channel for channel. The
    two rigs have the same bones at the same rest angles (the pure view's
    limbs are the side view's, moved), so the side rig takes the same pose."""
    for row in PURE_SIDE_ROWS:
        side.data["clips"][row] = copy.deepcopy(pure.data["clips"][row])


__all__ = ["PURE_SIDE_ROWS", "ROW", "author_crawl", "lend_pure_side_rows", "solve_crawl"]
