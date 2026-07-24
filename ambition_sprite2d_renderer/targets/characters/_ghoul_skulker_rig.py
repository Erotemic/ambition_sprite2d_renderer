"""Explicit joint skeleton for ghoul_skulker (faithful extraction).

Like ``_viking_warrior_rig``, this lifts the ghoul's implicit joint computation
out of the paint pass into a declared, poseable rig — so the animation lives on
named joints that can be sampled and edited, not buried in ``_render_frame``.
Nothing about the drawn result changes: ``_render_frame`` reads every limb/head
anchor from :func:`evaluate` instead of recomputing it.

The ghoul uses the position-shift model (NOT the pirate's rotate-around-joint
FK): every anchor sits in a single body frame ``root + rot(local, body_ang)``,
and a pose channel nudges a joint's LOCAL position (e.g. ``left_knee`` slides
with ``pose.left_leg``) rather than rotating a bone. Reproduced as-is so the
look is byte-identical. This is a crouched creature humanoid, so it carries
inline knee and foot anchors in addition to hips/shoulders/elbows/hands. Head
anchors live in their own frame rotated by ``body_ang + pose.head_tilt``. Angles
are screen degrees, +y down, clockwise positive.
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
class GhoulSkulkerJoints:
    """Evaluated anchors for one posed frame. ``root``/``body_ang`` and
    ``head_root``/``head_ang`` are the two frames the paint pass rebuilds its
    ``P``/``H`` helpers from; the rest are limb anchors."""

    root: Point
    body_ang: float
    head_root: Point
    head_ang: float
    left_hip: Point
    right_hip: Point
    left_knee: Point
    right_knee: Point
    left_foot: Point
    right_foot: Point
    right_shoulder: Point
    right_elbow: Point
    right_hand: Point
    left_shoulder: Point
    left_elbow: Point
    left_hand: Point


def evaluate(pose, work_w: float, work_h: float) -> GhoulSkulkerJoints:
    """Evaluate the body/head frames and limb anchors for ``pose``.

    ``work_w``/``work_h`` are the module's ``WORK_FRAME_SIZE`` (the stance is
    anchored as a fraction of it), passed in to keep this a pure function with no
    import cycle back into the paint module.
    """
    root = (
        work_w * 0.47 + pose.root_x + pose.dead_t * 8.0,
        work_h * 0.75 + pose.root_y + pose.bob,
    )
    body_ang = pose.lean

    def P(x: float, y: float) -> Point:
        rx, ry = _rot(x, y, body_ang)
        return (root[0] + rx, root[1] + ry)

    return GhoulSkulkerJoints(
        root=root,
        body_ang=body_ang,
        head_root=P(0, -128),
        head_ang=body_ang + pose.head_tilt,
        left_hip=P(-14, -56),
        right_hip=P(20, -52),
        left_knee=P(-30 + pose.left_leg * 0.32, -12),
        right_knee=P(18 + pose.right_leg * 0.26, -6),
        left_foot=P(-42 + pose.left_leg * 0.22, 26 - pose.left_lift),
        right_foot=P(42 + pose.right_leg * 0.18, 28 - pose.right_lift),
        right_shoulder=P(28, -104),
        right_elbow=P(48 + pose.right_arm * 0.10, -78 + pose.right_arm * 0.16),
        right_hand=P(58 + pose.right_arm * 0.28, -46 + pose.right_arm * 0.22),
        left_shoulder=P(-18, -106),
        left_elbow=P(-52 + pose.left_arm * 0.12, -74 + pose.left_arm * 0.18),
        left_hand=P(-70 + pose.left_arm * 0.34, -42 + pose.left_arm * 0.28),
    )


__all__ = ["GhoulSkulkerJoints", "evaluate"]
