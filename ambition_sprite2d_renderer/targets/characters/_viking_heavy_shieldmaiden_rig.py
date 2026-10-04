"""Explicit joint skeleton for viking_heavy_shieldmaiden.

The animation lives on named joints, not in the paint pass: ``evaluate``
turns a ``Pose`` into the body and head frames, the hips and shoulders, the
spear hand and angle, and the shield.

Every body anchor sits in one body frame ``root + rot(local, body_ang)``; the
head frame is turned ``body_ang + pose.head`` about ``head_root``. The shield
is held before the near side of the body and barged forward. The spear arm
holds the spear upright at the side; it raises it aloft for the bellow and
couches it for the jab, which drives the spear forward. Angles are screen
degrees, +y down, clockwise positive.

The heavy is designed in a frame of 760 units (as it always was) and drawn
in the shared 640-unit frame: every design length is scaled by ``S``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from . import _viking_common as V

Point = Tuple[float, float]

S = 640.0 / 760.0
#: Upper arm and forearm lengths (design units).
UPPER_ARM, FOREARM = 50.0, 50.0
#: Lying flat, the depth of the back below the root plus the root's depth
#: below the soles (``lying_lift``), and how far the body slides forward.
LIE = 130.0
SLIDE = 36.0


@dataclass(frozen=True)
class VikingHeavyShieldmaidenJoints:
    """Evaluated anchors for one posed frame."""

    root: Point
    body_ang: float
    head_root: Point
    head_ang: float
    far_hip: Point
    near_hip: Point
    far_shoulder: Point
    near_shoulder: Point
    spear_deg: float
    far_hand: Point
    near_hand: Point
    shield_center: Point
    far_bend: Point
    near_bend: Point


def spear_and_arm(pose, anim: str) -> Tuple[float, float]:
    """``(spear_deg, arm_deg)``: the spear's angle and where the spear arm
    points."""
    wa, pitch = pose.weapon_arm, pose.weapon_pitch
    if anim == "spear_jab":
        return -14.0 + 0.5 * pitch, 110.0 - (wa + 34.0) * 1.25
    if anim == "diva_bellow":
        return -78.0 + pitch, -50.0 + (wa + 46.0) * 2.0
    return -78.0 + pitch, 84.0 - wa * 0.9


def evaluate(pose, work_w: float, work_h: float, anim: str = "idle") -> VikingHeavyShieldmaidenJoints:
    """Evaluate the body/head frames and the joints for ``pose`` of ``anim``."""
    root = (
        work_w * 0.48 + S * pose.root_x + V.lying_lift(pose.lean, S * SLIDE),
        work_h * 0.80 + S * (pose.root_y + pose.bob) - V.lying_lift(pose.lean, S * LIE),
    )
    body_ang = pose.lean
    turned = V.frame_point(root, body_ang)

    def P(x: float, y: float) -> Point:
        return turned(S * x, S * y)

    far_shoulder, near_shoulder = P(44, -228), P(-46, -226)
    spear_deg, arm_deg = spear_and_arm(pose, anim)
    far_hand = V.along(far_shoulder, arm_deg, S * (UPPER_ARM + FOREARM) * 0.86)
    sa, push = pose.shield_arm, pose.shield_push
    near_hand = P(-48 + 0.2 * sa + 40 * push, -150 + 0.5 * sa - 20 * push)
    return VikingHeavyShieldmaidenJoints(
        root=root,
        body_ang=body_ang,
        head_root=P(2, -276),
        head_ang=body_ang + pose.head,
        far_hip=P(20, -118),
        near_hip=P(-18, -118),
        far_shoulder=far_shoulder,
        near_shoulder=near_shoulder,
        spear_deg=spear_deg,
        far_hand=far_hand,
        near_hand=near_hand,
        shield_center=P(-52 + 0.2 * sa + 40 * push, -152 + 0.5 * sa - 20 * push),
        far_bend=V.along(far_shoulder, arm_deg + 90.0, S * 50.0),
        near_bend=P(-90, -180),
    )


__all__ = ["S", "VikingHeavyShieldmaidenJoints", "evaluate", "spear_and_arm"]
