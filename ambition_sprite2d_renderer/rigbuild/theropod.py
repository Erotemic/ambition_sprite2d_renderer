"""The theropod family's anatomy, for ``creature_rig``.

The T-rex boss and the raptor stalker share one body: a pelvis carrying a
torso, an S-necked head with a hinged jaw, a four-bone tail, two-bone
digitigrade legs on IK with a foot below the ankle, and small two-bone arms.
Their SVGs mark the joints ``pelvis``, ``neck_base``, ``head``, ``snout``,
``jaw``, ``tail0`` .. ``tail3`` and ``tail_tip``, and per side (``far`` /
``near``) ``hip``, ``knee``, ``ankle``, ``shoulder``, ``elbow`` and ``wrist``.
"""

from __future__ import annotations

import math
from typing import Dict, List

from .creature_rig import (  # noqa: F401  (re-exported for builder scripts)
    BoneSpec,
    CreatureSpec,
    Leg,
    Point,
    Pose,
    eyes,
    limb,
    pulse,
    segment,
    smooth01,
    step,
    track,
    write,
)

TAIL_JOINTS = ("tail0", "tail1", "tail2", "tail3", "tail_tip")

LEGS = (
    Leg("far_thigh", "far_shin", "far_foot", "far_foot", "far_ankle"),
    Leg("near_thigh", "near_shin", "near_foot", "near_foot", "near_ankle"),
)


def skeleton(J: Dict[str, Point], jaw_length: float) -> List[BoneSpec]:
    bones = [("pelvis", None, J["pelvis"], 0.0, 0.0)]
    bones.append(segment("torso", "pelvis", J["pelvis"], J["neck_base"]))
    bones.append(segment("neck", "torso", J["neck_base"], J["head"]))
    head = segment("head", "neck", J["head"], J["snout"])
    bones.append(head)
    bones.append(("jaw", "head", J["jaw"], head[3], jaw_length))
    parent = "pelvis"
    for i in range(4):
        name = f"tail{i + 1}"
        bones.append(segment(name, parent, J[TAIL_JOINTS[i]], J[TAIL_JOINTS[i + 1]]))
        parent = name
    for side in ("far", "near"):
        bones += limb(f"{side}_thigh", f"{side}_shin", f"{side}_foot", "pelvis",
                      J[f"{side}_hip"], J[f"{side}_knee"], J[f"{side}_ankle"])
        bones.append(segment(f"{side}_arm_u", "torso", J[f"{side}_shoulder"], J[f"{side}_elbow"]))
        bones.append(segment(f"{side}_arm_l", f"{side}_arm_u", J[f"{side}_elbow"], J[f"{side}_wrist"]))
    return bones


def theropod_spec(*, jaw_length: float = 80.0, **fields) -> CreatureSpec:
    """A ``CreatureSpec`` with the theropod skeleton and legs. ``jaw_length``
    (sprite pixels) only sizes the jaw bone the editor draws."""
    return CreatureSpec(skeleton=lambda J: skeleton(J, jaw_length), legs=LEGS, **fields)


def gait(
    t: float,
    *,
    near_x: float,
    far_x: float,
    stride: float,
    lift: float,
    bob: float,
    sway: float,
    tail: float,
    arm: float = 6.0,
) -> Pose:
    """A two-legged loop: the feet half a cycle apart, the body highest at
    mid-stance, the neck and tail following the sway a little late."""
    p: Pose = {}
    nx, nl, npitch = step(t, near_x, stride, lift)
    fx, fl, fpitch = step(t + 0.5, far_x, stride, lift)
    p.update(near_foot_x=nx, near_foot_lift=nl, near_foot_pitch=npitch,
             far_foot_x=fx, far_foot_lift=fl, far_foot_pitch=fpitch)
    w = math.tau * t
    p["root_y"] = bob * (0.5 - abs(math.sin(w)))
    p["pelvis"] = sway * math.sin(w)
    p["torso"] = -0.4 * sway * math.sin(w)
    p["neck"] = -1.2 * sway * math.sin(w + 0.6)
    p["head"] = 0.8 * sway * math.sin(w + 1.2)
    for i in range(4):
        p[f"tail{i + 1}"] = tail * math.sin(w - 0.7 * (i + 1)) * (0.6 + 0.25 * i)
    p["near_arm_u"] = arm * math.sin(w)
    p["near_arm_l"] = arm * math.sin(w - 0.8)
    p["far_arm_u"] = -arm * math.sin(w)
    p["far_arm_l"] = -arm * math.sin(w - 0.8)
    return p
