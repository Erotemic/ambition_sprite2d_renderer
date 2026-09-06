"""Explicit joint skeleton for pirate_cutlass_viper (faithful extraction).

Like ``_viking_warrior_rig``, this lifts the duelist's implicit joint computation
out of the paint pass into a declared, poseable rig — so the animation lives on
named joints that can be edited and sampled, not buried inline in ``_render_front``
/ ``_render_side``. Nothing about the drawn result changes: the paint pass reads
every limb anchor from :func:`evaluate_front` / :func:`evaluate_side` instead of
recomputing it.

This target uses the position-shift model (NOT the pirate-family rotate-around-
joint FK): every anchor sits in a single body frame ``root + rot(local, tilt)``,
and a pose channel nudges a joint's LOCAL position (e.g. ``left_elbow`` slides
with ``pose.left_arm``) rather than rotating a bone. It draws two genuinely
different silhouettes — a front view and a dedicated side/profile view — so the
rig exposes one ``evaluate_*`` per view, each with its own root, tilt, and limb
set. Reproduced verbatim so the look is byte-identical. Angles are screen
degrees, +y down, clockwise positive.
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
class PirateCutlassViperFrontJoints:
    """Evaluated anchors for one posed front-view frame. ``root``/``body_ang``
    is the body frame the paint pass rebuilds its ``P`` helper from; the rest are
    limb anchors. ``back_hand`` is the off-hand cutlass grip used when the blade
    is carried (non-slash rows)."""

    root: Point
    body_ang: float
    back_hand: Point
    left_hip: Point
    right_hip: Point
    left_knee: Point
    right_knee: Point
    left_foot: Point
    right_foot: Point
    left_shoulder: Point
    left_elbow: Point
    left_hand: Point
    right_shoulder: Point
    right_elbow: Point
    right_hand: Point


@dataclass(frozen=True)
class PirateCutlassViperSideJoints:
    """Evaluated anchors for one posed side/profile frame. ``root``/``body_ang``
    is the body frame the paint pass rebuilds its ``P`` helper from; the rest are
    the dedicated side-view limb anchors (``back_*`` = off side, ``front_*`` =
    leading/weapon side)."""

    root: Point
    body_ang: float
    back_hip: Point
    front_hip: Point
    back_knee: Point
    front_knee: Point
    back_foot: Point
    front_foot: Point
    back_shoulder: Point
    back_elbow: Point
    back_hand: Point
    front_shoulder: Point
    front_elbow: Point
    front_hand: Point


def evaluate_front(pose, work_w: float, work_h: float) -> PirateCutlassViperFrontJoints:
    """Evaluate the body frame and limb anchors for a front-view ``pose``.

    ``work_w``/``work_h`` are the module's ``WORK_FRAME_SIZE``, passed in to keep
    this a pure function with no import cycle back into the paint module.
    """
    root = (
        work_w * 0.47 + pose.root_x + pose.dead_t * 8.0,
        work_h * 0.68 + pose.root_y + pose.bob,
    )
    body_ang = pose.lean

    def P(x: float, y: float) -> Point:
        rx, ry = _rot(x, y, body_ang)
        return (root[0] + rx, root[1] + ry)

    return PirateCutlassViperFrontJoints(
        root=root,
        body_ang=body_ang,
        back_hand=P(23 + pose.right_arm * 0.18, -44 + pose.blade_lift),
        left_hip=P(-14, -47),
        right_hip=P(16, -47),
        left_knee=P(-18 + pose.left_leg * 0.18, -18),
        right_knee=P(18 + pose.right_leg * 0.18, -18),
        left_foot=P(-22 + pose.left_leg * 0.18, 5 - pose.left_foot_lift),
        right_foot=P(24 + pose.right_leg * 0.18, 6 - pose.right_foot_lift),
        left_shoulder=P(-33, -96),
        left_elbow=P(-41 + pose.left_arm * 0.08, -68 + pose.left_arm * 0.14),
        left_hand=P(-25 + pose.left_arm * 0.24, -43 + pose.left_arm * 0.20),
        right_shoulder=P(34, -96),
        right_elbow=P(
            42 + pose.right_arm * 0.08,
            -67 + pose.right_arm * 0.16 + pose.blade_lift * 0.18,
        ),
        right_hand=P(
            26 + pose.right_arm * 0.24,
            -44 + pose.right_arm * 0.23 + pose.blade_lift,
        ),
    )


def evaluate_side(pose, work_w: float, work_h: float) -> PirateCutlassViperSideJoints:
    """Evaluate the body frame and limb anchors for a side/profile ``pose``.

    ``pose.side`` (+1 / -1) flips the silhouette; ``pose.openness`` blends from
    near-front (0) to full profile (1). ``work_w``/``work_h`` are the module's
    ``WORK_FRAME_SIZE``.
    """
    side = pose.side
    openness = pose.openness
    root = (
        work_w * 0.47 + pose.root_x,
        work_h * 0.68 + pose.root_y + pose.bob,
    )
    body_ang = pose.lean

    def P(x: float, y: float) -> Point:
        rx, ry = _rot(x, y, body_ang)
        return (root[0] + rx, root[1] + ry)

    return PirateCutlassViperSideJoints(
        root=root,
        body_ang=body_ang,
        back_hip=P(-7 * side * (1.0 - openness), -47),
        front_hip=P(7 * side * (0.6 + 0.25 * openness), -46),
        back_knee=P(-6 * side, -18 + pose.back_leg * 0.25),
        front_knee=P(10 * side, -16 + pose.front_leg * 0.28),
        back_foot=P(-3 * side, 5 - pose.back_foot_lift),
        front_foot=P(18 * side, 6 - pose.front_foot_lift),
        back_shoulder=P(-8 * side, -98),
        back_elbow=P(
            -11 * side + pose.back_arm * 0.12 * side, -70 + pose.back_arm * 0.14
        ),
        back_hand=P(
            -5 * side + pose.back_arm * 0.20 * side, -45 + pose.back_arm * 0.18
        ),
        front_shoulder=P(12 * side, -98),
        front_elbow=P(
            20 * side + pose.front_arm * 0.13 * side,
            -70 + pose.front_arm * 0.12 + pose.sword_lift * 0.3,
        ),
        front_hand=P(
            16 * side + pose.front_arm * 0.18 * side,
            -46 + pose.front_arm * 0.18 + pose.sword_lift,
        ),
    )


__all__ = [
    "PirateCutlassViperFrontJoints",
    "PirateCutlassViperSideJoints",
    "evaluate_front",
    "evaluate_side",
]
