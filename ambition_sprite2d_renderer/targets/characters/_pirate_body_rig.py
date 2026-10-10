"""The pirate family's semantic body rig, read from the declared skeleton.

The joints are ``_pirate_rig.PIRATE_BONES`` with their parents, and each clip
frame is evaluated by the same ``_pirate_rig.evaluate`` the paint pass places
its parts at. So the weapon hand of the rig is the hand the frame draws.

A joint's frame is ``translation(point) * rotation(angle)`` of its evaluated
bone, expressed local to its parent. The pirate convention rotates a child's
offset by the child's own world angle; publishing each joint's evaluated world
frame and taking it relative to its parent's frame reproduces every point
exactly, whatever the convention that produced it.

The weapon arm is the FRONT arm, drawn nearer the viewer, so it publishes
``hand_near``. The rig has no hurt parts: its first gameplay reader is the
hand-held muzzle, and adding articulated hurt geometry to the pirates is a
separate decision.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, List, Mapping, Tuple

from ...authoring.body_rig import BodyRigProduct, JointPose
from ...authoring.sheet_build import ANIMATIONS, BASE_FRAME, SCALE
from . import _pirate_rig as pirate_rig

#: Rows that repeat while their state holds; the rest play once.
_LOOPING_ROWS = frozenset({"idle", "walk"})

_ATTACHMENTS = (
    ("hand_near", "front_hand"),
    ("hand_far", "back_hand"),
    ("head", "head"),
)

Affine = Tuple[float, float, float, float, float, float]  # a, b, c, d, tx, ty


def _frame(point: Tuple[float, float], angle_rad: float) -> Affine:
    c, s = math.cos(angle_rad), math.sin(angle_rad)
    return (c, s, -s, c, point[0], point[1])


def _inverse(m: Affine) -> Affine:
    a, b, c, d, tx, ty = m
    det = a * d - b * c
    ia, ib, ic, id_ = d / det, -b / det, -c / det, a / det
    return (ia, ib, ic, id_, -(ia * tx + ic * ty), -(ib * tx + id_ * ty))


def _compose(m: Affine, n: Affine) -> Affine:
    a, b, c, d, tx, ty = m
    e, f, g, h, ux, uy = n
    return (
        a * e + c * f,
        b * e + d * f,
        a * g + c * h,
        b * g + d * h,
        a * ux + c * uy + tx,
        b * ux + d * uy + ty,
    )


def body_rig_for_pirate(
    kind: str,
    frame_fits: Mapping[Tuple[str, int], Mapping[str, float]],
    frame_transform: Mapping[str, float],
    feet: Tuple[float, float],
    frame_size=BASE_FRAME,
) -> BodyRigProduct:
    """Place the evaluated skeleton in the rig's space (published pixels from
    the feet).

    A paint point goes through three maps, the same three its pixels go
    through: the frame's own fit (``frame_fits[(row, index)]``, from
    ``downsample``, which crops each frame to its drawn extent and scales it),
    then ``build_sheet``'s drawn-to-published translation ``frame_transform``,
    then the published ``feet`` pixel as origin. The fit scale does not turn,
    so a joint keeps its evaluated angle.
    """
    from ._pirate_common import animation_pose

    w, h = frame_size[0] * SCALE, frame_size[1] * SCALE
    dx, dy = float(frame_transform["dx"]), float(frame_transform["dy"])
    bones = pirate_rig.PIRATE_BONES
    clips: Dict[str, tuple] = {}
    for anim, frame_count, duration_ms in ANIMATIONS:
        frames: List[List[JointPose]] = []
        for index in range(int(frame_count)):
            fit = frame_fits[(anim, index)]
            pose = animation_pose(anim, index, frame_count)
            tilt = pose["body_tilt"]
            joints = pirate_rig.evaluate(pose, kind, w, h, tilt)
            world: Dict[str, Affine] = {}
            poses: List[JointPose] = []
            for bone in bones:
                evaluated = joints[bone.name]
                point = (
                    (evaluated.point[0] - fit["x0"]) * fit["sx"] + fit["ox"] + dx - feet[0],
                    (evaluated.point[1] - fit["y0"]) * fit["sy"] + fit["oy"] + dy - feet[1],
                )
                world[bone.name] = _frame(point, math.radians(evaluated.angle))
                local = (
                    world[bone.name]
                    if bone.parent is None
                    else _compose(_inverse(world[bone.parent]), world[bone.name])
                )
                a, b, _c, _d, tx, ty = local
                poses.append(JointPose(translation=(tx, ty), rotation=math.atan2(b, a)))
            frames.append(poses)
        clips[anim] = (anim in _LOOPING_ROWS, float(duration_ms) / 1000.0, frames)
    return BodyRigProduct(
        target=kind,
        joints=[(bone.name, bone.parent) for bone in bones],
        attachments=[(name, joint, (0.0, 0.0)) for name, joint in _ATTACHMENTS],
        clips=clips,
    )
