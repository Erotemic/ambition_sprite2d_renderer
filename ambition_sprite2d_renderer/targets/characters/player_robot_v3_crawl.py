"""Player Robot v3's crawl: the row `crouch_walk`, on hands and knees.

The row was the crouch hold with each ankle moved 5.5 px along the ground. At
the size of the game the feet did not read as steps, and the body did not
move: a statue that slid.

A crouched body that moves goes down on all fours. The trunk is pitched
forward until it is near level, the knees and the hands are on the ground
line, and the head stays upright in front of the body, so the face still
reads. A hand and the knee of the other side go forward together, which is how
a crawl carries weight.

The standing robot is 88 px tall and its head alone is 45. This pose is about
62 px tall, which is lower than the crouch hold (about 70). The crouch box of
the game is half of the standing height, so the art is taller than the box
here as it is in the crouch hold.

The antenna stays rigid on the head, by ruling.

Data plus maths: the rig builder calls ``author_crawl`` after the crouch
family, and nothing here touches the filesystem.
"""

from __future__ import annotations

import math
from typing import Dict, List, Tuple

from ...authoring.rigdoc import RigDocument
from ...authoring.skeleton import two_bone_ik
from .player_robot_v3_body import SIDES, Arm, RigBody, WorldPose, write_frames

Point = Tuple[float, float]

#: The row this authors. `CharacterAnim::Crawl` falls back to it.
ROW = "crouch_walk"

# The trunk, in world degrees from upright. 90 is level.
PITCH = 64.0
# How far the pelvis is lowered, and how far back it sits, so that the hands
# and the knees land on the ground line with the head over the body box.
# The pelvis pitches less than the trunk. The hips of the art are 8 px each
# side of its centre, so a pelvis at the pitch of the trunk puts the far hip
# on the ground and the near hip 15 px over it, and no leg solves from there.
PELVIS_PITCH = 18.0
DROP = 12.0
BACK = 11.0
# The art is a three-quarter view: the near shoulder is 16 px behind the
# centre of the trunk and the far one 10 px ahead. On a pitched trunk that
# puts one shoulder over the other. Each is moved along the trunk to the
# middle, so the two arms hang from one height.
SHOULDER_DX = {"near": 12.0, "far": -8.0}
# The head: a little back from upright (it looks along the floor), sunk onto
# the shoulders and squashed as in the crouch hold.
HEAD_TILT = -4.0
HEAD_SINK = -5.0
HEAD_SQUASH = 0.86
# One cycle. A knee moves this far along the ground and lifts this high.
KNEE_STRIDE = 5.0
KNEE_LIFT = 3.5
# A hand reaches this far ahead of and behind its shoulder, and lifts this
# high between two places on the ground.
HAND_REACH = 8.0
HAND_LIFT = 6.0
# The wrist of a planted hand is this far above the ground line: the hand
# lies along the ground in front of it.
WRIST_UP = 6.0
HAND_FLAT = 48.0
# The trunk rocks with the steps and the body bobs twice in one cycle.
ROCK = 3.5
BOB = 2.0
# A foot trails behind its knee, sole up.
FOOT_ANGLE = 186.0
# Where the ankle rests behind the hip, and how high the shin holds it.
ANKLE_BACK = {"near": 13.0, "far": 12.0}
ANKLE_UP = 4.0
# The near hand leads; the far knee goes with it.
ARM_PHASE = {"near": 0.0, "far": 0.5}
LEG_PHASE = {"near": 0.5, "far": 0.0}


def _joints(body: RigBody, ch: Dict[str, float], pose: WorldPose, bone: str) -> Dict[str, Point]:
    """Where `bone` of each side starts in the frame for the trunk of `pose`
    (`arm_u` is the shoulder, `leg_u` the hip). The trunk does not depend on
    the limbs, so the channels of a first solve give it."""
    angles = {k: v for k, v in ch.items() if k in body.sk.bones}
    offsets = {"head": (0.0, ch["bone.head.y"])}
    for side in SIDES:
        offsets[f"{side}_arm_u"] = (ch[f"bone.{side}_arm_u.x"], ch[f"bone.{side}_arm_u.y"])
    root = (body.root[0] + pose.root_x, body.root[1] + pose.root_y)
    world = body.sk.world(angles, root=root, offsets=offsets)
    return {side: world[f"{side}_{bone}"].origin for side in SIDES}


def _pose(body: RigBody, phase: float) -> Dict[str, float]:
    tau = 2.0 * math.pi
    bob = math.cos(2.0 * tau * phase)
    rock = math.sin(tau * phase)
    pitch = PITCH + ROCK * rock
    pose = WorldPose(
        root_x=-BACK,
        root_y=DROP + 0.5 * BOB * bob,
        pelvis=PELVIS_PITCH + 0.5 * ROCK * rock,
        torso=pitch,
        head=HEAD_TILT - 2.0 * math.sin(2.0 * tau * (phase - 0.08)),
        head_dy=HEAD_SINK + 0.5 * BOB * math.cos(2.0 * tau * (phase - 0.08)),
        shoulder_dx=dict(SHOULDER_DX),
    )
    ground = body.root[1]
    first = body.channels(pose)
    hips = _joints(body, first, pose, "leg_u")
    for side in SIDES:
        p = tau * (phase - LEG_PHASE[side])
        # The knee goes forward in the air and comes back on the ground: the
        # ankle is the IK target, and the knee follows it.
        swing = math.sin(p)
        raised = max(0.0, math.cos(p))
        hip_x = hips[side][0]
        ankle = (
            hip_x - ANKLE_BACK[side] + KNEE_STRIDE * swing,
            body.ankle_rest[side][1] - ANKLE_UP - KNEE_LIFT * raised,
        )
        pose.ankles[side] = (ankle, FOOT_ANGLE + 8.0 * raised)

    # The arms: each wrist is put on its place on the ground (or on the arc
    # between two places), and the elbow is solved under the shoulder.
    shoulders = _joints(body, first, pose, "arm_u")
    for side in SIDES:
        a = tau * (phase - ARM_PHASE[side])
        raised = max(0.0, math.cos(a))
        sx, sy = shoulders[side]
        upper = body.sk.bones[f"{side}_arm_u"].length
        lower = body.sk.bones[f"{side}_arm_l"].length
        wrist = (
            sx + 2.0 + HAND_REACH * math.sin(a),
            ground - WRIST_UP - HAND_LIFT * raised,
        )
        # A straight arm has no elbow to solve: keep the wrist inside reach.
        reach = math.dist((sx, sy), wrist)
        limit = 0.98 * (upper + lower)
        if reach > limit:
            k = limit / reach
            wrist = (sx + (wrist[0] - sx) * k, sy + (wrist[1] - sy) * k)
        a1, a2 = two_bone_ik((sx, sy), wrist, upper, lower, bend=-1.0)
        # The hand lies along the ground while it carries weight, and hangs
        # from the wrist while it is in the air.
        pose.arms[side] = Arm(a1, a2, HAND_FLAT + 25.0 * raised)
    return body.channels(pose)


def solve_crawl(doc: RigDocument, frame_count: int) -> Dict[str, List[float]]:
    """The channel values of each frame of the crawl."""
    body = RigBody(doc)
    frames = [_pose(body, i / frame_count) for i in range(frame_count)]
    channels = {
        key: [frame[key] for frame in frames]
        for key in frames[0]
        if not key.startswith("_")
    }
    channels["bone.head.scale_y"] = [HEAD_SQUASH] * frame_count
    channels["eye_squint"] = [0.1] * frame_count
    return channels


def author_crawl(doc: RigDocument) -> None:
    """Replace the `crouch_walk` clip of a built v3 rig with the crawl."""
    write_frames(doc, ROW, solve_crawl(doc, int(doc.data["clips"][ROW]["frames"])))


__all__ = ["ROW", "author_crawl", "solve_crawl"]
