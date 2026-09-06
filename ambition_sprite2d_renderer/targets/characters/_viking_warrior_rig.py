"""Explicit joint skeleton for viking_warrior (faithful extraction).

Like ``_pirate_rig``, this lifts the character's implicit joint computation out of
the paint pass into a declared, poseable rig — so the animation lives on named
joints that can be edited and sampled, not buried in ``_render_frame``. Nothing
about the drawn result changes: ``_render_frame`` reads every limb/head anchor
from :func:`evaluate` instead of recomputing it.

The viking uses the position-shift model (NOT the pirate's rotate-around-joint
FK): every anchor sits in a single body frame ``root + rot(local, body_ang)``,
and a pose channel nudges a joint's LOCAL position (e.g. ``far_elbow`` slides
with ``pose.right_arm``) rather than rotating a bone. Reproduced as-is so the
look is byte-identical. Head anchors live in their own frame rotated by
``body_ang + pose.head``. Angles are screen degrees, +y down, clockwise positive.
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
class VikingWarriorJoints:
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


def evaluate(pose, work_w: float, work_h: float) -> VikingWarriorJoints:
    """Evaluate the body/head frames and limb anchors for ``pose``.

    ``work_w``/``work_h`` are the module's ``WORK_FRAME_SIZE`` (the stance is
    anchored as a fraction of it), passed in to keep this a pure function with no
    import cycle back into the paint module.
    """
    root = (
        work_w * 0.47 + pose.root_x,
        work_h * 0.79 + pose.root_y + pose.bob,
    )
    body_ang = pose.lean

    def P(x: float, y: float) -> Point:
        rx, ry = _rot(x, y, body_ang)
        return (root[0] + rx, root[1] + ry)

    return VikingWarriorJoints(
        root=root,
        body_ang=body_ang,
        head_root=P(-2, -248),
        head_ang=body_ang + pose.head,
        far_hip=P(12, -108),
        near_hip=P(-12, -108),
        far_shoulder=P(30, -186),
        far_elbow=P(44 + pose.right_arm * 0.22, -148 + pose.right_arm * 0.16),
        far_hand=P(52 + pose.right_arm * 0.34, -102 + pose.right_arm * 0.18),
        near_shoulder=P(-32, -186),
        near_elbow=P(-44 + pose.left_arm * 0.20, -148 + pose.left_arm * 0.18),
        near_hand=P(-52 + pose.left_arm * 0.34, -102 + pose.left_arm * 0.22),
    )


__all__ = ["VikingWarriorJoints", "evaluate"]
