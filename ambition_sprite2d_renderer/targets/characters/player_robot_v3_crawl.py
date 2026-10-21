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
from .player_robot_v3_body import Arm, RigBody, WorldPose, rot, write_frames
from .player_robot_v3_wall_climb import ROW as WALL_CLIMB_ROW
from .player_robot_v3_wall_climb import WALL_X, climb_channels, climb_pose

ROW = "crouch_walk"
#: The rows drawn from the pure side view: the climb, and the crawl.
PURE_SIDE_ROWS: Tuple[str, ...] = (WALL_CLIMB_ROW, ROW)

Point = Tuple[float, float]

#: The turn from the wall to the floor (world degrees, clockwise on screen):
#: up becomes forward, and forward (the wall) becomes down (the floor).
QUARTER = 90.0
#: How far the head tilts up from the turned climb, to look ahead.
HEAD_LIFT = 45.0
#: Where the pelvis goes, back from the middle of the frame, so the crawl from
#: the boots to the face is over the middle of the body box, as the crouch is.
BODY_BACK = 15.0
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

    return WorldPose(
        root_x=target[0] - body.root[0] - pelvis_offset[0],
        root_y=target[1] - body.root[1] - pelvis_offset[1],
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


def _pose(body: RigBody, ground: float, phase: float) -> Dict[str, float]:
    return climb_channels(body, _turned(body, climb_pose(body, phase), ground))


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
