"""Player Robot v3 crawls: the wall climb, turned onto the floor.

Jon, 2026-10-21: "make the crawl animation look more like the wall climb, but
on the floor instead of the wall", then: "the robot body should be rotated
90degrees so it is parallel to the floor, but have the head kept up so it can
see in front of it", and: "Its neck and head should be attached at
semantically the same pivot point. Really it should look a lot like the wall
crawl rotated 90 degrees, maybe with the head tilted up slightly more." The
game draws the `crouch_walk` row for a body that moves in its crouch (a crawl
falls back to it).

So the crawl IS the climb (``player_robot_v3_wall_climb.climb_pose``), turned
a quarter turn about the pelvis: the wall becomes the floor and up the wall
becomes forward. Each world angle turns by 90 degrees and each boot target
turns about the pelvis, so the hands and the boots that hold the wall hold the
floor, and the joints are where the climb puts them. Only the head is not
turned the whole quarter: on the wall it looks up the wall, and turned it
would look down at the floor, so it tilts up by ``HEAD_LIFT``.

It is drawn from the PURE SIDE view, as the climb is.

Data plus maths: the rig builder calls ``author_crawl``; nothing here touches
the filesystem.
"""

from __future__ import annotations

import copy
from typing import Dict, List, Tuple

from ...authoring.rigdoc import RigDocument
from ...authoring.skeleton import two_bone_ik
from .player_robot_v3_body import FACE_SWITCHES, SCALE_RESTS, Arm, RigBody, WorldPose, rot, write_frames
from .player_robot_v3_swim import ROW as SWIM_ROW
from .player_robot_v3_wall_climb import ROW as WALL_CLIMB_ROW
from .player_robot_v3_wall_climb import WALL_X, climb_channels, climb_pose

ROW = "crouch_walk"
#: From the crouch hold to the crawl's first frame (`author_crawl_start`).
START_ROW = "crawl_start"
#: The rows drawn from the pure side view: the climb, the crawl, the way into
#: it, and the swim (``player_robot_v3_swim``).
PURE_SIDE_ROWS: Tuple[str, ...] = (WALL_CLIMB_ROW, ROW, START_ROW, SWIM_ROW)

Point = Tuple[float, float]

#: The turn from the wall to the floor (world degrees, clockwise on screen):
#: up becomes forward, and forward (the wall) becomes down (the floor).
QUARTER = 90.0
#: How far the head tilts up from the turned climb, to look ahead.
HEAD_LIFT = 45.0
#: Where the pelvis goes, back from the middle of the frame, so the crawl from
#: the boots to the face is over the middle of the body box, as the crouch is.
BODY_BACK = 15.0
#: The body is nearer the floor than the climb's is to its wall by this, and
#: the head is squashed onto its neck by this scale, as in the crouch hold: the
#: crawl is about as tall as the crouch's box, not a head over it. The hands and
#: the boots stay on the floor, so the elbows and the knees bend more.
FLOOR_HUG = 8.0
HEAD_SQUASH = 0.9
#: The fists of the climb go a little into the wall. On the floor the body is
#: up by this, so a held fist and a held boot touch the ground line (measured
#: from the render).
FLOOR_LIFT = 3.0


def _turned(body: RigBody, climb: WorldPose, ground: float) -> WorldPose:
    """`climb` turned a quarter turn about its pelvis, the wall on `ground`."""
    pelvis_offset = (
        body.stand["pelvis"].origin[0] - body.root[0],
        body.stand["pelvis"].origin[1] - body.root[1],
    )
    pivot = (
        body.root[0] + climb.root_x + pelvis_offset[0],
        body.root[1] + climb.root_y + pelvis_offset[1],
    )
    # The wall is WALL_X - pivot.x in front of the pelvis; turned, that is
    # under it, and it is the floor.
    target = (body.root[0] - BODY_BACK, ground - FLOOR_LIFT - (WALL_X - pivot[0]))

    def moved(point: Point) -> Point:
        d = rot((point[0] - pivot[0], point[1] - pivot[1]), QUARTER)
        return (target[0] + d[0], target[1] + d[1])

    turned = WorldPose(
        root_x=target[0] - body.root[0] - pelvis_offset[0],
        root_y=target[1] + FLOOR_HUG - body.root[1] - pelvis_offset[1],
        pelvis=climb.pelvis + QUARTER,
        torso=climb.torso + QUARTER,
        head=climb.head + QUARTER - HEAD_LIFT,
        squash=climb.squash,
        head_dy=climb.head_dy,
        shoulder_dx=dict(climb.shoulder_dx),
        arms={
            side: Arm(
                arm.upper + QUARTER,
                arm.lower + QUARTER,
                None if arm.hand is None else arm.hand + QUARTER,
            )
            for side, arm in climb.arms.items()
        },
        ankles={side: (moved(at), angle + QUARTER) for side, (at, angle) in climb.ankles.items()},
    )
    # The body hugs the floor nearer than the climb hugs its wall, so the
    # wrists are put where the climb's are, turned, and the arms solved to them.
    held = _world(body, climb)
    shoulders = _world(body, turned)
    for side, arm in climb.arms.items():
        wrist = moved(held[f"{side}_arm_hand"])
        upper = body.sk.bones[f"{side}_arm_u"].length
        lower = body.sk.bones[f"{side}_arm_l"].length
        a1, a2 = two_bone_ik(shoulders[f"{side}_arm_u"], wrist, upper, lower, bend=-1.0)
        turned.arms[side] = Arm(a1, a2, None if arm.hand is None else arm.hand + QUARTER)
    return turned


def _world(body: RigBody, pose: WorldPose) -> Dict[str, Point]:
    """Where each bone of `pose` starts."""
    channels = body.channels(pose)
    angles = {k: v for k, v in channels.items() if k in body.sk.bones}
    offsets = {"head": (0.0, channels["bone.head.y"])}
    for side in ("near", "far"):
        offsets[f"{side}_arm_u"] = (channels[f"bone.{side}_arm_u.x"], channels[f"bone.{side}_arm_u.y"])
    root = (body.root[0] + pose.root_x, body.root[1] + pose.root_y)
    return {name: bone.origin for name, bone in body.sk.world(angles, root=root, offsets=offsets).items()}


def _pose(body: RigBody, ground: float, phase: float) -> Dict[str, float]:
    channels = climb_channels(body, _turned(body, climb_pose(body, phase), ground))
    channels["bone.head.scale_y"] = HEAD_SQUASH
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


def _held_pose(body: RigBody, channels: Dict[str, float]) -> WorldPose:
    """The world pose of a frame given as rig channels."""
    angles = {k: v for k, v in channels.items() if k in body.sk.bones}
    offsets = {"head": (channels.get("bone.head.x", 0.0), channels.get("bone.head.y", 0.0))}
    for side in ("near", "far"):
        offsets[f"{side}_arm_u"] = (
            channels.get(f"bone.{side}_arm_u.x", 0.0),
            channels.get(f"bone.{side}_arm_u.y", 0.0),
        )
    root_x, root_y = channels.get("root_x", 0.0), channels.get("root_y", 0.0)
    world = body.sk.world(angles, root=(body.root[0] + root_x, body.root[1] + root_y), offsets=offsets)
    return WorldPose(
        root_x=root_x,
        root_y=root_y,
        pelvis=world["pelvis"].angle,
        torso=world["torso"].angle,
        head=world["head"].angle,
        head_dy=channels.get("bone.head.y", 0.0),
        arms={
            side: Arm(world[f"{side}_arm_u"].angle, world[f"{side}_arm_l"].angle, world[f"{side}_arm_hand"].angle)
            for side in ("near", "far")
        },
        ankles={side: (world[f"{side}_leg_foot"].origin, world[f"{side}_leg_foot"].angle) for side in ("near", "far")},
    )


def _mixed(a: WorldPose, b: WorldPose, f: float) -> WorldPose:
    def mix(x: float, y: float) -> float:
        return x + (y - x) * f

    def point(p: Point, q: Point) -> Point:
        return (mix(p[0], q[0]), mix(p[1], q[1]))

    return WorldPose(
        root_x=mix(a.root_x, b.root_x),
        root_y=mix(a.root_y, b.root_y),
        pelvis=mix(a.pelvis, b.pelvis),
        torso=mix(a.torso, b.torso),
        head=mix(a.head, b.head),
        head_dy=mix(a.head_dy, b.head_dy),
        arms={
            side: Arm(
                mix(a.arms[side].upper, b.arms[side].upper),
                mix(a.arms[side].lower, b.arms[side].lower),
                mix(a.arms[side].hand, b.arms[side].hand),
            )
            for side in a.arms
        },
        ankles={
            side: (point(a.ankles[side][0], b.ankles[side][0]), mix(a.ankles[side][1], b.ankles[side][1]))
            for side in a.ankles
        },
    )


def author_crawl_start(doc: RigDocument, side: RigDocument) -> None:
    """Make the `crawl_start` clip of the pure side rig: the crouch hold of the
    side rig (`side`) going down onto the hands, into the crawl's first frame.

    The two rigs have the same bones at the same rest angles, so the hold's
    channels pose the pure side rig as well. The two poses are mixed in world
    terms by an eased fraction: the angles, the pelvis and where each boot is.
    The knees are solved for the boots, so a boot on the floor stays on it.
    The head's own channels (its squash, how far back it sits) are mixed too.
    """
    body = RigBody(doc)
    hold = side.sample("crouch", 0.0)
    crawl = doc.sample(ROW, 0.0)
    a, b = _held_pose(body, hold), _held_pose(body, crawl)
    own = ("bone.head.x", "bone.head.scale_y", "eye_squint")
    frames = int(doc.data["clips"][START_ROW]["frames"])
    poses = []
    for i in range(frames):
        q = i / (frames - 1)
        f = q * q * (3.0 - 2.0 * q)
        channels = body.channels(_mixed(a, b, f))
        for k in own:
            rest = SCALE_RESTS.get(k, 0.0)
            channels[k] = hold.get(k, rest) + (crawl.get(k, rest) - hold.get(k, rest)) * f
        poses.append(channels)
    write_frames(doc, START_ROW, {k: [p[k] for p in poses] for k in poses[0] if not k.startswith("_")})


def lend_pure_side_rows(pure: RigDocument, side: RigDocument) -> None:
    """Give the side rig the pure side rig's rows, channel for channel. The
    two rigs have the same bones at the same rest angles (the pure view's
    limbs are the side view's, moved), so the side rig takes the same pose."""
    for row in PURE_SIDE_ROWS:
        side.data["clips"][row] = copy.deepcopy(pure.data["clips"][row])


__all__ = ["START_ROW", "author_crawl_start", "PURE_SIDE_ROWS", "ROW", "author_crawl", "lend_pure_side_rows", "solve_crawl"]
