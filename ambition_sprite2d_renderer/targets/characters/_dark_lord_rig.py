"""Explicit joint skeleton for dark_lord (faithful extraction).

Like ``_viking_warrior_rig``, this lifts the boss's implicit joint computation
out of the paint pass into a declared, poseable rig — so the animation lives on
named joints that can be edited and sampled, not buried in ``_render_frame`` /
``_draw_limbs``. Nothing about the drawn result changes: the paint pass reads
every limb anchor from :func:`evaluate` instead of recomputing it.

The dark lord uses the position-shift model (NOT rotate-around-joint FK): every
anchor sits in a single body frame ``root + rot(local, body_ang)``, and a pose
channel nudges a joint's LOCAL position (e.g. ``near_elbow`` slides with
``pose.near_arm`` and ``pose.weapon_lift``) rather than rotating a bone.
Reproduced verbatim so the look is byte-identical. There is no separate head
frame: the helmet is painted in the same body frame. Angles are screen degrees,
+y down, clockwise positive.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Tuple

Point = Tuple[float, float]


def _rot(x: float, y: float, deg: float) -> Point:
    rad = math.radians(deg)
    c = math.cos(rad)
    s = math.sin(rad)
    return (x * c - y * s, x * s + y * c)


@dataclass(frozen=True)
class DarkLordJoints:
    """Evaluated anchors for one posed frame. ``root``/``body_ang`` is the body
    frame the paint pass rebuilds its ``P`` helper from; the rest are limb
    anchors placed in that frame."""

    root: Point
    body_ang: float
    far_hip: Point
    near_hip: Point
    far_knee: Point
    near_knee: Point
    far_foot: Point
    near_foot: Point
    far_shoulder: Point
    far_elbow: Point
    far_hand: Point
    near_shoulder: Point
    near_elbow: Point
    near_hand: Point


def evaluate(pose, work_w: float, work_h: float) -> DarkLordJoints:
    """Evaluate the body frame and limb anchors for ``pose``.

    ``work_w``/``work_h`` are the module's ``WORK_FRAME_SIZE`` (the stance is
    anchored as a fraction of it), passed in to keep this a pure function with no
    import cycle back into the paint module.
    """
    root = (
        work_w * 0.47 + pose.root_x + pose.dead_t * 7.0,
        work_h * 0.70 + pose.root_y + pose.bob,
    )
    body_ang = pose.tilt

    def P(x: float, y: float) -> Point:
        rx, ry = _rot(x, y, body_ang)
        return (root[0] + rx, root[1] + ry)

    return DarkLordJoints(
        root=root,
        body_ang=body_ang,
        far_hip=P(-16, -45),
        near_hip=P(18, -45),
        far_knee=P(-18 + pose.far_leg * 0.22, -7),
        near_knee=P(20 + pose.near_leg * 0.22, -5),
        far_foot=P(-23 + pose.far_leg * 0.20, 54 - pose.far_lift),
        near_foot=P(24 + pose.near_leg * 0.20, 55 - pose.near_lift),
        far_shoulder=P(-35, -99),
        far_elbow=P(-49 + pose.far_arm * 0.09, -70 + pose.far_arm * 0.16),
        far_hand=P(-35 + pose.far_arm * 0.18, -36 + pose.far_arm * 0.21),
        near_shoulder=P(38, -99),
        near_elbow=P(
            54 + pose.near_arm * 0.08,
            -68 + pose.near_arm * 0.16 + pose.weapon_lift * 0.15,
        ),
        near_hand=P(
            39 + pose.near_arm * 0.19,
            -34 + pose.near_arm * 0.23 + pose.weapon_lift,
        ),
    )


__all__ = ["DarkLordJoints", "evaluate"]
