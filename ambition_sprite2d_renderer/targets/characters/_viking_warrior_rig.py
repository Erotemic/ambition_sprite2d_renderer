"""Explicit joint skeleton for viking_warrior.

The animation lives on named joints, not in the paint pass: ``evaluate``
turns a ``Pose`` into the body and head frames, the hips and shoulders, and
where both hands grip the dane axe.

Every body anchor sits in one body frame ``root + rot(local, body_ang)``; the
head frame is turned ``body_ang + pose.head`` about ``head_root``. The axe is
held in both hands: its grip sits out from the chest ALONG the axe (raised
behind the head, the axe lifts the hands above the shoulders), and each
hand takes the point of the haft its arm reaches (``hand_on_haft``). Angles
are screen degrees, +y down, clockwise positive.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from . import _viking_common as V

Point = Tuple[float, float]

#: Upper arm and forearm lengths (design units).
UPPER_ARM, FOREARM = 40.0, 40.0
#: Where the haft passes the chest, how far out (more when raised), and how
#: far apart the hands hold it.
CHEST: Point = (4.0, -168.0)
GRIP_REACH, GRIP_RAISED, GRIP_SPREAD = 44.0, 36.0, 18.0
#: A raised axe is held behind the head, not through it: the grip moves
#: back this far (body frame) as the axe rises.
GRIP_BACK = 36.0


#: Lying flat, the depth of the back below the root plus the root's depth
#: below the soles (``lying_lift``).
LIE = 68.0


@dataclass(frozen=True)
class VikingWarriorJoints:
    """Evaluated anchors for one posed frame."""

    root: Point
    body_ang: float
    head_root: Point
    head_ang: float
    far_hip: Point
    near_hip: Point
    far_shoulder: Point
    near_shoulder: Point
    weapon_deg: float
    grip: Point
    near_hand: Point
    far_hand: Point
    near_bend: Point
    far_bend: Point


def raised(weapon_deg: float) -> float:
    """How far the axe is raised behind the head, 0 to 1."""
    return max(0.0, min(1.0, (-weapon_deg - 60.0) / 40.0))


def evaluate(pose, work_w: float, work_h: float) -> VikingWarriorJoints:
    """Evaluate the body/head frames and the joints for ``pose``."""
    root = (work_w * 0.47 + pose.root_x, work_h * 0.79 + pose.root_y + pose.bob - V.lying_lift(pose.lean, LIE))
    body_ang = pose.lean
    P = V.frame_point(root, body_ang)
    near_shoulder, far_shoulder = P(-26, -186), P(26, -188)
    deg = pose.weapon_angle
    up = raised(deg)
    chest = P(CHEST[0] - GRIP_BACK * up, CHEST[1])
    grip, _upper, _lower = V.two_hand_grip(chest, deg, GRIP_REACH + GRIP_RAISED * up, GRIP_SPREAD)
    reach = UPPER_ARM + FOREARM - 1.0
    near_hand = V.hand_on_haft(near_shoulder, grip, deg, -GRIP_SPREAD / 2.0, reach)
    far_hand = V.hand_on_haft(far_shoulder, grip, deg, GRIP_SPREAD / 2.0, reach)
    return VikingWarriorJoints(
        root=root,
        body_ang=body_ang,
        head_root=P(4, -246),
        head_ang=body_ang + pose.head,
        far_hip=P(10, -108),
        near_hip=P(-10, -108),
        far_shoulder=far_shoulder,
        near_shoulder=near_shoulder,
        weapon_deg=deg,
        grip=grip,
        near_hand=near_hand,
        far_hand=far_hand,
        near_bend=P(-40, -110),
        far_bend=P(46, -110),
    )


__all__ = ["VikingWarriorJoints", "evaluate", "raised"]
