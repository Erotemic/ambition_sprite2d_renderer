"""Explicit joint skeleton for viking_heavy_warrior (faithful extraction).

Like ``_viking_warrior_rig``, this lifts the character's implicit joint
computation out of the paint pass into a declared, poseable rig — so the
animation lives on named joints that can be edited and sampled, not buried in
``_render_frame``. Nothing about the drawn result changes: ``_render_frame``
reads every limb/head anchor from :func:`evaluate` instead of recomputing it.

The heavy viking uses the position-shift model (NOT a rotate-around-joint FK):
every anchor sits in a single body frame ``root + rot(local, body_ang)``, and a
pose channel nudges a joint's LOCAL position (e.g. ``far_elbow`` slides with
``pose.right_arm``) rather than rotating a bone. Reproduced as-is so the look is
byte-identical. Head anchors live in their own frame rotated by
``body_ang + pose.head``. Legs are drawn by ``_draw_leg`` from a hip anchor plus
an angle, so only the hip anchors are lifted here. Angles are screen degrees,
+y down, clockwise positive.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Tuple

Point = Tuple[float, float]


def _rot(x: float, y: float, deg: float) -> Point:
    rad = math.radians(deg)
    c, s = math.cos(rad), math.sin(rad)
    return (x * c - y * s, x * s + y * c)


@dataclass(frozen=True)
class VikingHeavyWarriorJoints:
    """Evaluated anchors for one posed frame. ``root``/``body_ang`` and
    ``head_root``/``head_ang`` are the two frames the paint pass rebuilds its
    ``P``/``H`` helpers from; the rest are limb anchors."""

    root: Point
    body_ang: float
    head_root: Point
    head_ang: float
    far_hip: Point
    near_hip: Point
    far_shoulder: Point
    far_elbow: Point
    far_hand: Point
    near_shoulder: Point
    near_elbow: Point
    near_hand: Point


def evaluate(pose, work_w: float, work_h: float) -> VikingHeavyWarriorJoints:
    """Evaluate the body/head frames and limb anchors for ``pose``.

    ``work_w``/``work_h`` are the module's ``WORK_FRAME_SIZE`` (the stance is
    anchored as a fraction of it), passed in to keep this a pure function with no
    import cycle back into the paint module.
    """
    root = (
        work_w * 0.48 + pose.root_x,
        work_h * 0.80 + pose.root_y + pose.bob,
    )
    body_ang = pose.lean

    def P(x: float, y: float) -> Point:
        rx, ry = _rot(x, y, body_ang)
        return (root[0] + rx, root[1] + ry)

    return VikingHeavyWarriorJoints(
        root=root,
        body_ang=body_ang,
        head_root=P(-4, -304),
        head_ang=body_ang + pose.head,
        far_hip=P(18, -120),
        near_hip=P(-20, -120),
        far_shoulder=P(44, -224),
        far_elbow=P(70 + pose.right_arm * 0.18, -180 + pose.right_arm * 0.16),
        far_hand=P(84 + pose.right_arm * 0.28, -126 + pose.right_arm * 0.22),
        near_shoulder=P(-48, -224),
        near_elbow=P(-74 + pose.left_arm * 0.18, -180 + pose.left_arm * 0.16),
        near_hand=P(-90 + pose.left_arm * 0.32, -124 + pose.left_arm * 0.22),
    )


__all__ = ["VikingHeavyWarriorJoints", "evaluate"]
