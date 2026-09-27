"""Player Robot v3's body, posed in WORLD terms and solved into rig channels.

The rig's channels are local deltas on authored rest angles, which is the wrong
language to choreograph in: "the torso leans 12 degrees and the blade points
straight ahead" becomes a chain of subtractions through every parent. A
[`WorldPose`] says what the body does in frame space — world angles, a pelvis
drop, where each ankle is — and [`RigBody.channels`] turns it into the rig's
channels, solving the knees by two-bone IK so a planted boot stays planted.

The solved rows (``player_robot_v3_gait``, ``player_robot_v3_strikes``) author
WorldPoses; this module is the one place that knows how the rig composes them.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from ...authoring.rigdoc import RigDocument
from ...authoring.skeleton import two_bone_ik

Point = Tuple[float, float]
SIDES = ("near", "far")


def rot(p: Point, deg: float) -> Point:
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


def about(point: Point, pivot: Point, deg: float) -> Point:
    r = rot((point[0] - pivot[0], point[1] - pivot[1]), deg)
    return (pivot[0] + r[0], pivot[1] + r[1])


@dataclass(frozen=True)
class Arm:
    """World angles of one arm. ``hand`` ``None`` keeps the hand on its
    authored relationship to the forearm."""

    upper: float
    lower: float
    hand: Optional[float] = None


@dataclass
class WorldPose:
    """One frame of the body, in frame pixels and world degrees.

    Angles: 0 points screen-right (the way the robot faces), 90 straight down,
    -90 straight up. ``root_y`` positive lowers the body. ``squash`` scales the
    torso about the waist; whatever rides on it (neck, shoulders) rides the
    squash. ``shoulder_dx`` slides a shoulder along the torso — the visible half
    of a torso TURNING, since a paper doll cannot rotate out of its plane.
    ``ankles`` default to where the boots stand at rest, flat.
    """

    root_x: float = 0.0
    root_y: float = 0.0
    pelvis: float = 0.0
    torso: float = 0.0
    head: float = 0.0
    squash: float = 1.0
    head_dy: float = 0.0
    shoulder_dx: Dict[str, float] = field(default_factory=dict)
    arms: Dict[str, Arm] = field(default_factory=dict)
    ankles: Dict[str, Tuple[Point, float]] = field(default_factory=dict)


class RigBody:
    """The rig's standing geometry, read once from a built document."""

    def __init__(self, doc: RigDocument) -> None:
        self.sk = doc.build_skeleton()
        self.rest = {name: b.rest_angle for name, b in self.sk.bones.items()}
        fr = doc.frame
        self.root = (float(fr["center_x"]), float(fr["ground_y"]))
        self.stand = self.sk.world({}, root=self.root)
        self.foot_rest = {s: self.stand[f"{s}_leg_foot"].angle for s in SIDES}
        self.ankle_rest = {s: self.stand[f"{s}_leg_foot"].origin for s in SIDES}
        self.hip_rest = {s: self.stand[f"{s}_leg_u"].origin for s in SIDES}
        self.arm_rest = {
            s: Arm(
                self.stand[f"{s}_arm_u"].angle,
                self.stand[f"{s}_arm_l"].angle,
                self.stand[f"{s}_arm_hand"].angle,
            )
            for s in SIDES
        }
        self.leg = {
            s: (self.sk.bones[f"{s}_leg_u"].length, self.sk.bones[f"{s}_leg_l"].length)
            for s in SIDES
        }
        # Where the boot meets the floor, in the foot bone's frame: the back of
        # the sole under the ankle, and the front of the sole under the toe cap.
        # Measured off the rasterised boots.
        self.heel = {"far": (0.3, 5.7), "near": (-0.8, 6.2)}
        self.toe = {s: (self.sk.bones[f"{s}_leg_foot"].length, -0.3) for s in SIDES}
        self.shoulder = {s: self.sk.bones[f"{s}_arm_u"].offset for s in SIDES}
        self.neck_y = self.sk.bones["head"].offset[1]

    def foot_point(self, local: Point, ankle: Point, angle: float) -> Point:
        r = rot(local, angle)
        return (ankle[0] + r[0], ankle[1] + r[1])

    def channels(self, pose: WorldPose) -> Dict[str, float]:
        """The rig channels for `pose`, plus ``_reach_<side>`` diagnostics."""
        rest = self.rest
        ch: Dict[str, float] = {
            "root_x": pose.root_x,
            "root_y": pose.root_y,
            "pelvis": pose.pelvis - rest["pelvis"],
            "torso": pose.torso - pose.pelvis - rest["torso"],
            "head": pose.head - pose.torso - rest["head"],
            "bone.torso.scale_y": pose.squash,
            "bone.head.y": self.neck_y * (pose.squash - 1.0) + pose.head_dy,
        }
        offsets = {"head": (0.0, ch["bone.head.y"])}
        for side in SIDES:
            dx = pose.shoulder_dx.get(side, 0.0)
            dy = self.shoulder[side][1] * (pose.squash - 1.0)
            ch[f"bone.{side}_arm_u.x"] = dx
            ch[f"bone.{side}_arm_u.y"] = dy
            offsets[f"{side}_arm_u"] = (dx, dy)

        angles = {k: v for k, v in ch.items() if k in self.sk.bones}
        root = (self.root[0] + pose.root_x, self.root[1] + pose.root_y)
        world = self.sk.world(angles, root=root, offsets=offsets)
        for side in SIDES:
            ankle, foot_w = pose.ankles.get(
                side, (self.ankle_rest[side], self.foot_rest[side])
            )
            hip = world[f"{side}_leg_u"].origin
            upper, lower = self.leg[side]
            ch[f"_reach_{side}"] = math.dist(hip, ankle) / (upper + lower)
            a1, a2 = two_bone_ik(hip, ankle, upper, lower, bend=1.0)
            ch[f"{side}_leg_u"] = a1 - pose.pelvis - rest[f"{side}_leg_u"]
            ch[f"{side}_leg_l"] = a2 - a1 - rest[f"{side}_leg_l"]
            ch[f"{side}_leg_foot"] = foot_w - a2 - rest[f"{side}_leg_foot"]

        for side in SIDES:
            arm = pose.arms.get(side)
            if arm is None:
                # Held at rest RELATIVE TO THE TORSO: a leaning body carries
                # its arms with it.
                r = self.arm_rest[side]
                arm = Arm(r.upper + pose.torso, r.lower + pose.torso, None)
            ch[f"{side}_arm_u"] = arm.upper - pose.torso - rest[f"{side}_arm_u"]
            ch[f"{side}_arm_l"] = arm.lower - arm.upper - rest[f"{side}_arm_l"]
            ch[f"{side}_arm_hand"] = (
                0.0 if arm.hand is None
                else arm.hand - arm.lower - rest[f"{side}_arm_hand"]
            )
        return ch


__all__ = ["Arm", "RigBody", "SIDES", "WorldPose", "about", "rot"]
