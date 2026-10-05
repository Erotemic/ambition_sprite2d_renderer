"""The quadruped family's anatomy, for ``creature_rig``.

The bear mauler's body: a pelvis at the hips carrying a torso to the withers,
a short neck, a head with a hinged jaw, and four two-bone legs on IK, each
ending in a paw bone at the ankle or wrist. Hind legs hang from the pelvis
(their knees fold forward), fore legs from the torso (their elbows fold back).
The SVG marks the joints ``pelvis``, ``neck_base``, ``head``, ``snout``,
``jaw``, and per side (``far`` / ``near``) ``hip``, ``knee``, ``ankle``,
``shoulder``, ``elbow`` and ``wrist``. Every ankle and wrist is drawn at one
height above the ground (the document's ``ankle_h``).

Bones and IK prefixes are named ``<side>_<hind|fore>_<upper|lower|paw>`` and
``<side>_<hind|fore>``: a clip moves a paw with ``near_fore_x``,
``near_fore_lift`` and ``near_fore_pitch``.
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

SIDES = ("far", "near")
KINDS = ("hind", "fore")
JOINTS = {"hind": ("hip", "knee", "ankle"), "fore": ("shoulder", "elbow", "wrist")}

LEGS = tuple(
    Leg(f"{side}_{kind}_upper", f"{side}_{kind}_lower", f"{side}_{kind}_paw", f"{side}_{kind}",
        f"{side}_{JOINTS[kind][2]}", 1.0 if kind == "hind" else -1.0)
    for side in SIDES
    for kind in KINDS
)


def skeleton(J: Dict[str, Point], jaw_length: float) -> List[BoneSpec]:
    bones = [("pelvis", None, J["pelvis"], 0.0, 0.0)]
    bones.append(segment("torso", "pelvis", J["pelvis"], J["neck_base"]))
    bones.append(segment("neck", "torso", J["neck_base"], J["head"]))
    head = segment("head", "neck", J["head"], J["snout"])
    bones.append(head)
    bones.append(("jaw", "head", J["jaw"], head[3], jaw_length))
    for side in SIDES:
        for kind in KINDS:
            top, mid, end = (J[f"{side}_{name}"] for name in JOINTS[kind])
            bones += limb(f"{side}_{kind}_upper", f"{side}_{kind}_lower", f"{side}_{kind}_paw",
                          "pelvis" if kind == "hind" else "torso", top, mid, end)
    return bones


def quadruped_spec(*, jaw_length: float = 30.0, **fields) -> CreatureSpec:
    """A ``CreatureSpec`` with the quadruped skeleton and legs. ``jaw_length``
    (sprite pixels) only sizes the jaw bone the editor draws."""
    return CreatureSpec(skeleton=lambda J: skeleton(J, jaw_length), legs=LEGS, **fields)


#: A walk's footfall order: each leg's phase offset (the bear's lateral
#: sequence: hind, then the fore on that side, then the other hind and fore).
WALK_PHASES = {"near_hind": 0.0, "near_fore": 0.25, "far_hind": 0.5, "far_fore": 0.75}
#: A gallop: the hinds land together, then the fores.
GALLOP_PHASES = {"near_hind": 0.0, "far_hind": 0.08, "near_fore": 0.5, "far_fore": 0.58}


def gait(
    t: float,
    *,
    rest_x: Dict[str, float],
    stride: float,
    lift: float,
    bob: float,
    sway: float,
    phases: Dict[str, float] = WALK_PHASES,
) -> Pose:
    """A four-legged loop: each paw planted then swung (``step``) at its own
    phase, the body bobbing twice a cycle, the head nodding with the fores."""
    p: Pose = {}
    for prefix, phase in phases.items():
        x, h, pitch = step(t + phase, rest_x[prefix], stride, lift)
        p[f"{prefix}_x"] = x
        p[f"{prefix}_lift"] = h
        p[f"{prefix}_pitch"] = pitch
    w = math.tau * t
    p["root_y"] = bob * (0.5 - abs(math.sin(w)))
    p["pelvis"] = sway * math.sin(w)
    p["torso"] = -0.5 * sway * math.sin(w)
    p["neck"] = 1.4 * sway * math.sin(w + 0.9)
    p["head"] = -0.8 * sway * math.sin(w + 1.4)
    return p
