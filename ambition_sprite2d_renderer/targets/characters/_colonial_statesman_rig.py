"""Explicit joint skeleton for colonial_statesman (faithful extraction).

Like ``_viking_warrior_rig``, this lifts the character's implicit joint
computation out of the paint pass into a declared, poseable rig — so the
animation lives on named joints that can be edited and sampled, not buried in
``_render_frame``. Nothing about the drawn result changes: ``_render_frame``
reads every limb/head anchor from :func:`evaluate` instead of recomputing it.

The statesman uses the position-shift model (NOT the pirate's rotate-around-joint
FK): every anchor sits in a single body frame ``root + rot(local, body_ang)``,
and a pose channel nudges a joint's LOCAL position (e.g. ``far_elbow`` slides
with ``pose.right_arm``) rather than rotating a bone. Reproduced as-is so the
look is byte-identical. Head anchors live in their own frame rotated by
``body_ang + pose.head``. The two hips are the anchors handed to the inline
``_draw_leg`` helper (which derives its own knees/feet). Angles are screen
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
class ColonialStatesmanJoints:
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


def evaluate(pose, work_w: float, work_h: float) -> ColonialStatesmanJoints:
    """Evaluate the body/head frames and limb anchors for ``pose``.

    ``work_w``/``work_h`` are the module's ``WORK_FRAME_SIZE`` (the stance is
    anchored as a fraction of it), passed in to keep this a pure function with no
    import cycle back into the paint module.
    """
    root = (
        work_w * 0.47 + pose.root_x,
        work_h * 0.77 + pose.root_y + pose.bob,
    )
    body_ang = pose.tilt

    def P(x: float, y: float) -> Point:
        rx, ry = _rot(x, y, body_ang)
        return (root[0] + rx, root[1] + ry)

    return ColonialStatesmanJoints(
        root=root,
        body_ang=body_ang,
        head_root=P(-2, -246),
        head_ang=body_ang + pose.head,
        far_hip=P(10, -104),
        near_hip=P(-12, -104),
        far_shoulder=P(28, -182),
        far_elbow=P(40 + pose.right_arm * 0.18, -138 + pose.right_arm * 0.10),
        far_hand=P(46 + pose.right_arm * 0.28, -92 + pose.right_arm * 0.12),
        near_shoulder=P(-28, -182),
        near_elbow=P(-40 + pose.left_arm * 0.20, -140 + pose.left_arm * 0.10),
        near_hand=P(-46 + pose.left_arm * 0.36, -96 + pose.left_arm * 0.14),
    )


__all__ = ["ColonialStatesmanJoints", "evaluate"]
