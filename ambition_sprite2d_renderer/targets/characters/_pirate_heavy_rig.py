"""Explicit joint skeleton for pirate_heavy (faithful extraction).

Like ``_viking_warrior_rig``/``_pirate_rig``, this lifts the character's implicit
joint computation out of the paint pass into a declared, poseable rig — so the
animation lives on named joints that can be edited and sampled, not buried in
``_draw_variant``/``_draw_limbs``. Nothing about the drawn result changes: the
paint pass reads every limb/head anchor from :func:`evaluate` instead of
recomputing it.

pirate_heavy renders a FAMILY of variants driven by a ``VariantSpec`` — the
joint offsets carry per-variant proportion factors (``spec.shoulder_scale``,
``spec.hip_scale``). So :func:`evaluate` takes BOTH ``pose`` AND ``spec`` (plus
the work-frame size the stance is anchored against) and reproduces the exact
expressions verbatim, scale factors included.

Uses the position-shift model (NOT a rotate-around-joint FK): every anchor sits
in a single body frame ``root + rot(local, tilt)``, and a pose channel nudges a
joint's LOCAL position (e.g. ``left_elbow`` slides with ``pose.left_arm``) rather
than rotating a bone. Reproduced as-is so the look is byte-identical. Angles are
screen degrees, +y down, clockwise positive; offsets are in WORK_FRAME_SIZE paint
units (pre-supersample).
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
class PirateHeavyJoints:
    """Evaluated anchors for one posed variant frame. ``root``/``tilt`` are the
    body frame the paint pass rebuilds its ``P`` helper from; the rest are the
    head and limb anchors. ``right_hand`` doubles as the front (slash) weapon
    grip — the paint pass uses the identical expression there."""

    root: Point
    tilt: float
    head: Point
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
    back_hand: Point


def evaluate(pose, spec, work_w: float, work_h: float) -> PirateHeavyJoints:
    """Evaluate the body frame, head, and limb anchors for ``pose``/``spec``.

    ``work_w``/``work_h`` are the module's ``WORK_FRAME_SIZE`` (the stance is
    anchored as a fraction of it), passed in to keep this a pure function with no
    import cycle back into the paint module. ``spec`` supplies the per-variant
    proportion factors (``shoulder_scale``, ``hip_scale``).
    """
    root = (
        work_w * 0.46 + pose.root_x + pose.death_t * 8.0,
        work_h * 0.67 + pose.root_y + pose.bob,
    )
    tilt = pose.tilt

    def P(x: float, y: float) -> Point:
        rx, ry = _rot(x, y, tilt)
        return (root[0] + rx, root[1] + ry)

    return PirateHeavyJoints(
        root=root,
        tilt=tilt,
        head=P(0, -125 + pose.head_tilt * 0.10),
        left_hip=P(-22 * spec.hip_scale, -47),
        right_hip=P(21 * spec.hip_scale, -47),
        left_knee=P(-25 * spec.hip_scale + pose.left_leg * 0.18, -18),
        right_knee=P(24 * spec.hip_scale + pose.right_leg * 0.18, -18),
        left_foot=P(-29 * spec.hip_scale + pose.left_leg * 0.16, 5 - pose.left_foot_lift),
        right_foot=P(31 * spec.hip_scale + pose.right_leg * 0.16, 5 - pose.right_foot_lift),
        left_shoulder=P(-44 * spec.shoulder_scale, -95),
        left_elbow=P(
            -55 * spec.shoulder_scale + pose.left_arm * 0.06, -63 + pose.left_arm * 0.15
        ),
        left_hand=P(
            -42 * spec.shoulder_scale + pose.left_arm * 0.22, -41 + pose.left_arm * 0.24
        ),
        right_shoulder=P(44 * spec.shoulder_scale, -96),
        right_elbow=P(
            55 * spec.shoulder_scale + pose.right_arm * 0.05,
            -64 + pose.right_arm * 0.16 + pose.weapon_lift * 0.2,
        ),
        right_hand=P(
            43 * spec.shoulder_scale + pose.right_arm * 0.24,
            -41 + pose.right_arm * 0.27 + pose.weapon_lift,
        ),
        back_hand=P(
            38 * spec.shoulder_scale + pose.right_arm * 0.12, -44 + pose.weapon_lift
        ),
    )


__all__ = ["PirateHeavyJoints", "evaluate"]
