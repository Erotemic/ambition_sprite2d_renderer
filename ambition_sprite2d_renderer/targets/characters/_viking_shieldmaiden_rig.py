"""Explicit joint skeleton for viking_shieldmaiden.

The animation lives on named joints, not in the paint pass: ``evaluate``
turns a ``Pose`` into the body and head frames, the hips and shoulders, the
axe hand and the shield hand.

Every body anchor sits in one body frame ``root + rot(local, body_ang)``; the
head frame is turned ``body_ang + pose.head`` about ``head_root``. The axe
arm follows the axe: the arm turns with the axe a fixed angle ahead of it (raised
for a chop, forward, then down on the follow-through). The
shield hand holds the shield before the near side of the body and drives it
forward and up on a bash. Angles are screen degrees, +y down, clockwise
positive.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from . import _viking_common as V

Point = Tuple[float, float]

#: Upper arm and forearm lengths (design units).
UPPER_ARM, FOREARM = 38.0, 38.0
#: How far the arm turns ahead of the axe (degrees, clockwise).
ARM_LEAD = 62.0


#: Lying flat, the depth of the back below the root plus the root's depth
#: below the soles (``lying_lift``).
LIE = 88.0


@dataclass(frozen=True)
class VikingShieldmaidenJoints:
    """Evaluated anchors for one posed frame."""

    root: Point
    body_ang: float
    head_root: Point
    head_ang: float
    far_hip: Point
    near_hip: Point
    far_shoulder: Point
    near_shoulder: Point
    axe_deg: float
    far_hand: Point
    near_hand: Point
    shield_center: Point
    far_bend: Point
    near_bend: Point


def axe_angle(pose) -> float:
    return -32.0 + pose.weapon_arm * 1.15 - pose.weapon_raise * 28.0


def arm_angle(axe_deg: float) -> float:
    """Where the axe arm points for an axe at ``axe_deg``: a fixed turn
    behind the axe, so the arm sweeps with the swing (up and back for a
    chop, forward, then down on the follow-through)."""
    return max(-100.0, min(95.0, axe_deg + ARM_LEAD))


def evaluate(pose, work_w: float, work_h: float) -> VikingShieldmaidenJoints:
    """Evaluate the body/head frames and the joints for ``pose``."""
    root = (work_w * 0.48 + pose.root_x, work_h * 0.78 + pose.root_y + pose.bob - V.lying_lift(pose.lean, LIE))
    body_ang = pose.lean
    P = V.frame_point(root, body_ang)
    far_shoulder, near_shoulder = P(24, -184), P(-24, -182)
    axe_deg = axe_angle(pose)
    arm_deg = arm_angle(axe_deg)
    far_hand = V.along(far_shoulder, arm_deg, (UPPER_ARM + FOREARM) * 0.9)
    sa, push = pose.shield_arm, pose.shield_push
    near_hand = P(-28 + 0.15 * sa + 34 * push, -122 + 0.6 * sa - 26 * push)
    return VikingShieldmaidenJoints(
        root=root,
        body_ang=body_ang,
        head_root=P(2, -242),
        head_ang=body_ang + pose.head,
        far_hip=P(10, -106),
        near_hip=P(-10, -106),
        far_shoulder=far_shoulder,
        near_shoulder=near_shoulder,
        axe_deg=axe_deg,
        far_hand=far_hand,
        near_hand=near_hand,
        shield_center=P(-30 + 0.15 * sa + 34 * push, -124 + 0.6 * sa - 26 * push),
        far_bend=V.along(far_shoulder, arm_deg + 90.0, 40.0),
        near_bend=P(-56, -150),
    )


__all__ = ["VikingShieldmaidenJoints", "arm_angle", "axe_angle", "evaluate"]
