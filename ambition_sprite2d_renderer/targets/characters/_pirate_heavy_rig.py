"""The skeleton of a pirate heavy.

A pose says where the pelvis is, how far she leans and turns, where each hand
and each foot must be, and which way each elbow bends. :func:`evaluate` makes
the joints from it: the shoulders and the head ride the lean of the torso, and
two-bone IK puts the elbows and the knees.

Every point is in the frame of the body: the origin is the ground between her
feet, +x is the way she faces, +y is down. ``PirateHeavyJoints.world`` takes a
point to the work frame. Angles are screen degrees, clockwise positive. Sizes
are work pixels (before the supersample).

A variant changes the skeleton through its ``VariantSpec``: ``shoulder`` is the
width of the shoulders and ``tall`` is the length of the torso and the legs.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Tuple

Point = Tuple[float, float]

#: The lengths of the bones, for a variant whose ``tall`` is 1.
UPPER_ARM = 34.0
FOREARM = 32.0
THIGH = 25.0
SHIN = 25.0
#: The pelvis above the ground, and the shoulders above the pelvis.
HIP_Y = -56.0
CHEST = 56.0
#: Half the width of the shoulders, square to the camera.
SHOULDER = 42.0
#: The cleaver from the lead hand: back to the pommel, forward to the tip.
HAFT_BACK = 36.0
HAFT_FRONT = 106.0
#: The ankle above the ground.
ANKLE = 8.0


def rot(p: Point, deg: float) -> Point:
    rad = math.radians(deg)
    c, s = math.cos(rad), math.sin(rad)
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


def add(a: Point, b: Point) -> Point:
    return (a[0] + b[0], a[1] + b[1])


def angle(a: Point, b: Point) -> float:
    """The screen degrees of the line from ``a`` to ``b``."""
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


def ik(a: Point, target: Point, l1: float, l2: float, bend: float) -> Tuple[Point, Point]:
    """Two bones from ``a`` toward ``target``: ``(middle joint, end)``. The end
    is the target, or the nearest point the bones reach. ``bend`` +1 puts the
    middle joint clockwise of the line from ``a`` to the end, -1 the other way."""
    dx, dy = target[0] - a[0], target[1] - a[1]
    d = max(abs(l1 - l2) + 0.5, min(l1 + l2 - 0.5, math.hypot(dx, dy)))
    base = math.atan2(dy, dx)
    inner = math.acos(max(-1.0, min(1.0, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d))))
    mid = (a[0] + l1 * math.cos(base + bend * inner), a[1] + l1 * math.sin(base + bend * inner))
    return mid, (a[0] + d * math.cos(base), a[1] + d * math.sin(base))


@dataclass(frozen=True)
class PirateHeavyJoints:
    """The joints of one posed frame, in the frame of the body."""

    stance: Point  # where she stands in the work frame: the root of a pose that does not move it
    root: Point  # the origin of the body, in the work frame
    body_rot: float  # the whole body about its origin (the fall)
    pelvis: Point
    lean: float
    shoulder_half: float  # half the width of the shoulders, as turned
    chest_x: float  # where the middle of the chest is drawn (she is a little turned)
    head: Point
    head_rot: float
    left_shoulder: Point
    left_elbow: Point
    left_hand: Point
    right_shoulder: Point
    right_elbow: Point
    right_hand: Point  # the lead hand: the grip of the cleaver
    weapon: float  # the degrees of the haft
    left_hip: Point
    left_knee: Point
    left_ankle: Point
    right_hip: Point
    right_knee: Point
    right_ankle: Point

    def world(self, p: Point) -> Point:
        q = rot(p, self.body_rot)
        return (self.root[0] + q[0], self.root[1] + q[1])


def evaluate(pose, spec, work_w: float, work_h: float) -> PirateHeavyJoints:
    """The joints of ``pose`` for the variant ``spec``. ``work_w``/``work_h``
    are the size of the work frame: the stance is at a fixed part of it."""
    tall = spec.tall
    # on a whole pixel: see the boot painter
    stance = (float(round(work_w * 0.46)), float(round(work_h * 0.67)))
    root = (stance[0] + pose.root[0], stance[1] + pose.root[1])
    pelvis = (pose.pelvis[0], pose.pelvis[1] * tall)
    lean = pose.lean
    half = SHOULDER * spec.shoulder * (1.0 - 0.3 * pose.twist)
    chest_x = 5.0 + 5.0 * pose.twist
    chest = add(pelvis, rot((0.0, -CHEST * tall), lean))
    right_shoulder = add(chest, rot((half, 2.0), lean))
    left_shoulder = add(chest, rot((-half, 2.0), lean))
    head = add(chest, rot((pose.head_dx + chest_x * 0.6, -31.0 * (0.4 + 0.6 * spec.head)), lean * 0.7))

    right_elbow, right_hand = ik(right_shoulder, (pose.r_hand[0], pose.r_hand[1] * tall), UPPER_ARM, FOREARM, pose.r_bend)
    left_target = (pose.l_hand[0], pose.l_hand[1] * tall)
    if pose.two_hand:
        # The far hand takes the haft behind the lead hand, as near to it as
        # the arm reaches.
        along = rot((1.0, 0.0), pose.weapon)
        for back in (24.0, 28.0, 32.0, HAFT_BACK - 2.0):
            left_target = add(right_hand, (-back * along[0], -back * along[1]))
            if math.hypot(left_target[0] - left_shoulder[0], left_target[1] - left_shoulder[1]) <= UPPER_ARM + FOREARM - 1.0:
                break
    left_elbow, left_hand = ik(left_shoulder, left_target, UPPER_ARM, FOREARM, pose.l_bend)

    left_hip = add(pelvis, (-16.0, 3.0))
    right_hip = add(pelvis, (16.0, 3.0))
    left_ankle = (pose.l_foot[0], -ANKLE - pose.l_foot[1])
    right_ankle = (pose.r_foot[0], -ANKLE - pose.r_foot[1])
    # the knees go out, away from each other
    left_knee = ik(left_hip, left_ankle, THIGH * tall, SHIN * tall, +1.0)[0]
    right_knee = ik(right_hip, right_ankle, THIGH * tall, SHIN * tall, -1.0)[0]

    return PirateHeavyJoints(
        stance=stance,
        root=root,
        body_rot=pose.body_rot,
        pelvis=pelvis,
        lean=lean,
        shoulder_half=half,
        chest_x=chest_x,
        head=head,
        head_rot=lean * 0.45 + pose.head_tilt,
        left_shoulder=left_shoulder,
        left_elbow=left_elbow,
        left_hand=left_hand,
        right_shoulder=right_shoulder,
        right_elbow=right_elbow,
        right_hand=right_hand,
        weapon=pose.weapon,
        left_hip=left_hip,
        left_knee=left_knee,
        left_ankle=left_ankle,
        right_hip=right_hip,
        right_knee=right_knee,
        right_ankle=right_ankle,
    )


__all__ = ["PirateHeavyJoints", "evaluate", "ik", "rot", "add", "angle"]
