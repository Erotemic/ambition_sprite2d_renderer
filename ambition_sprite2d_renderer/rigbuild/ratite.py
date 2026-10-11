"""The ratite family's anatomy, for ``creature_rig``: a bird that runs and
does not fly (the ostrich, the emu, the cassowary, the kiwi).

Seen from the side: a ``body`` bone at its centre of mass (the root), a
``neck`` in its own bone (from the body to the back of the head), a ``head``
on it (to the beak tip) with a hinged lower beak (``jaw``), a ``tail``, a
one-bone wing per side (``<side>_wing``, shoulder to tip: small, raised for
balance) and a two-bone leg per side on IK whose middle joint is the hock: it
folds BACKWARD, so a bird that sits goes down on its hocks. The SVG marks the
joints ``body``, ``neck``, ``head``, ``beak_tip``, ``jaw``, ``tail``,
``tail_tip`` and, per side, ``shoulder``, ``wingtip``, ``hip``, ``knee`` (the
hock) and ``ankle``.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from .bird import foot_at  # noqa: F401  (re-exported for builder scripts)
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

LEGS = (
    Leg("far_leg_u", "far_leg_l", "far_foot", "far_foot", "far_ankle", bend=-1.0),
    Leg("near_leg_u", "near_leg_l", "near_foot", "near_foot", "near_ankle", bend=-1.0),
)


def skeleton(J: Dict[str, Point]) -> List[BoneSpec]:
    bones = [("body", None, J["body"], 0.0, 0.0)]
    bones.append(segment("neck", "body", J["neck"], J["head"]))
    bones.append(segment("head", "neck", J["head"], J["beak_tip"]))
    bones.append(segment("jaw", "head", J["jaw"], J["beak_tip"]))
    bones.append(segment("tail", "body", J["tail"], J["tail_tip"]))
    for side in ("far", "near"):
        bones.append(segment(f"{side}_wing", "body", J[f"{side}_shoulder"], J[f"{side}_wingtip"]))
        bones += limb(f"{side}_leg_u", f"{side}_leg_l", f"{side}_foot", "body",
                      J[f"{side}_hip"], J[f"{side}_knee"], J[f"{side}_ankle"])
    return bones


def ratite_spec(**fields) -> CreatureSpec:
    """A ``CreatureSpec`` with the side-view ratite skeleton and its legs."""
    return CreatureSpec(skeleton=skeleton, legs=LEGS, **fields)


__all__: Tuple[str, ...] = (
    "LEGS",
    "eyes",
    "foot_at",
    "pulse",
    "ratite_spec",
    "skeleton",
    "smooth01",
    "step",
    "track",
    "write",
)
