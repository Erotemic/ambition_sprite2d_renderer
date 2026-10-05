"""The bird family's anatomy, for ``creature_rig``: a perching bird that flies.

The Stochastic Parrot's body. Seen from the side: a ``body`` bone at its
centre of mass (the root; a clip pitches the whole bird with it, upright on a
perch, level in flight), a ``head`` on the neck with a hinged lower beak
(``jaw``), a two-bone tail (``tail1``,
``tail2``), a two-bone wing per side (``<side>_wing`` the arm from shoulder
to wrist, ``<side>_hand`` the primaries from wrist to tip) and a two-bone leg
per side on IK with a zygodactyl foot. The SVG marks the joints ``body``,
``neck``, ``beak_tip``, ``jaw``, ``tail1``,
``tail2``, ``tail_tip``, and per side ``shoulder``, ``wrist``, ``wingtip``,
``hip``, ``knee`` and ``ankle``.

Facing the viewer, or turned three-quarters toward it (a turnaround's
steps), the bird is a ``body`` with a ``head`` (``neck`` to ``head_top``), a
``jaw`` and a wing per side (``<side>_wing``, ``shoulder`` to ``wingtip``);
its feet ride the body (``front_skeleton``).

A wing has two looks, a swap set on its own channels: ``wing.folded`` (the
wing on the body, perched) and ``wing.open`` (spread, drawn raised). The
flap channels turn the spread wing; ``flap`` authors a beat.
"""

from __future__ import annotations

import math
from typing import Dict, List, Tuple

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
    Leg("far_leg_u", "far_leg_l", "far_foot", "far_foot", "far_ankle", bend=1.0),
    Leg("near_leg_u", "near_leg_l", "near_foot", "near_foot", "near_ankle", bend=1.0),
)


def skeleton(J: Dict[str, Point]) -> List[BoneSpec]:
    bones = [("body", None, J["body"], 0.0, 0.0)]
    bones.append(segment("head", "body", J["neck"], J["beak_tip"]))
    bones.append(segment("jaw", "head", J["jaw"], J["beak_tip"]))
    bones.append(segment("tail1", "body", J["tail1"], J["tail2"]))
    bones.append(segment("tail2", "tail1", J["tail2"], J["tail_tip"]))
    for side in ("far", "near"):
        bones.append(segment(f"{side}_wing", "body", J[f"{side}_shoulder"], J[f"{side}_wrist"]))
        bones.append(segment(f"{side}_hand", f"{side}_wing", J[f"{side}_wrist"], J[f"{side}_wingtip"]))
        bones += limb(f"{side}_leg_u", f"{side}_leg_l", f"{side}_foot", "body",
                      J[f"{side}_hip"], J[f"{side}_knee"], J[f"{side}_ankle"])
    return bones


def front_skeleton(J: Dict[str, Point]) -> List[BoneSpec]:
    bones = [("body", None, J["body"], 0.0, 0.0)]
    bones.append(segment("head", "body", J["neck"], J["head_top"]))
    bones.append(("jaw", "head", J["jaw"], 90.0, 14.0))
    for side in ("far", "near"):
        bones.append(segment(f"{side}_wing", "body", J[f"{side}_shoulder"], J[f"{side}_wingtip"]))
    return bones


def bird_spec(**fields) -> CreatureSpec:
    """A ``CreatureSpec`` with the side-view bird skeleton and its legs."""
    return CreatureSpec(skeleton=skeleton, legs=LEGS, **fields)


def bird_front_spec(**fields) -> CreatureSpec:
    """The bird facing the viewer or turned three-quarters toward it: no IK
    (its feet ride the body)."""
    return CreatureSpec(skeleton=front_skeleton, legs=(), ankle_joint="body", **fields)


def flap(t: float, *, beats: float = 1.0, lift: float = 0.0, depth: float = 140.0, lag: float = 0.12) -> Pose:
    """One spread-wing beat per ``1 / beats`` of ``t``: the wings start raised
    (the drawing), drive down ``depth`` degrees (fast) and recover (slower),
    the primaries trailing on the upstroke and reaching on the downstroke.
    ``lift`` raises the whole stroke (a hover holds higher). The far wing
    follows ``lag`` of a beat behind."""
    p: Pose = {}
    for side, delay, k in (("near", 0.0, 1.0), ("far", lag, 0.9)):
        u = (t * beats - delay) % 1.0
        # down in the first 45% of the beat, up in the rest
        down = smooth01(u / 0.45) if u < 0.45 else 1.0 - smooth01((u - 0.45) / 0.55)
        p[f"{side}_wing"] = lift - k * depth * down
        # reaching (positive) through the downstroke, trailing (negative) up
        sweep = math.sin(math.tau * (u + 0.1))
        p[f"{side}_hand"] = 18.0 * sweep + 10.0 * down
    return p


def foot_at(p: Pose, side: str, local: Point, *, body_origin: Point, center_x: float, ankle_y: float,
            pitch: float = 0.0) -> None:
    """Put ``side``'s IK foot where a point ``local`` (SVG units, relative to
    the body joint at rest) is carried by the body's pose: a foot tucked in
    flight, a leg stuck up in the air. ``ankle_y`` is the drawn ankle's
    height (the IK's zero lift), ``body_origin`` the body joint, both in
    SVG units like the clip."""
    a = math.radians(p.get("body", 0.0))
    lx, ly = local
    wx = body_origin[0] + p.get("root_x", 0.0) + lx * math.cos(a) - ly * math.sin(a)
    wy = body_origin[1] + p.get("root_y", 0.0) + lx * math.sin(a) + ly * math.cos(a)
    p[f"{side}_foot_x"] = wx - center_x
    p[f"{side}_foot_lift"] = ankle_y - wy
    p[f"{side}_foot_pitch"] = p.get("body", 0.0) + pitch


def wings(state: str) -> Pose:
    """``folded`` (perched) or ``open`` (spread)."""
    return {"wing.folded": 1.0 if state == "folded" else 0.0, "wing.open": 1.0 if state == "open" else 0.0}


__all__: Tuple[str, ...] = (
    "LEGS",
    "bird_front_spec",
    "bird_spec",
    "eyes",
    "flap",
    "foot_at",
    "front_skeleton",
    "pulse",
    "skeleton",
    "smooth01",
    "step",
    "track",
    "wings",
    "write",
)
