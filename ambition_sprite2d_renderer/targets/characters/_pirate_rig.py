"""Explicit bone skeleton for the pirate family.

The pirate is the first character lifted from an *implicit* joint tree — the
inline ``transform(...)`` calls scattered through ``_pirate_common``'s paint
pass — into a *declared, poseable* skeleton. Nothing about the drawn result
changes: ``paint_character`` now reads every joint from :func:`evaluate` instead
of recomputing it, so the animation lives on bones that can be edited, sampled,
and (next) exported to an SVG paper-doll assembled by this same skeleton.

The proportions are of 2026-10-10 (the pirates were drawn again): legs of 80,
a torso of 66, a head whose middle is 62 over the line of the shoulders.

A joint is ``parent_point + rot(offset, world_angle)`` where the offset is
rotated by the CHILD's own world angle: the bones of a limb swing in world
space while their sockets ride the tilted body. A pose thus says where a
forearm or a shin points on the screen, whatever the body does.

Angles use the renderer's screen convention: degrees, +y down, clockwise
positive. Offsets are in supersampled paint pixels (the space ``paint_character``
works in), so ``evaluate`` takes the already-scaled frame size and root.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Mapping, Optional, Tuple

from ...authoring.sheet_build import SCALE, transform

Point = Tuple[float, float]

@dataclass(frozen=True)
class PirateBone:
    """One joint. ``parent`` is another bone's name, or ``None`` for the root
    (``char_origin``). ``offset(pose, kind)`` is the local vector from the parent
    point; ``angle(pose, kind, tilt)`` is the world angle that vector is rotated
    by (the pirate convention — the child's own angle, not the parent's)."""

    name: str
    parent: Optional[str]
    offset: Callable[[Mapping[str, float], str], Point]
    angle: Callable[[Mapping[str, float], str, float], float]


@dataclass(frozen=True)
class BonePose:
    """Evaluated joint: world ``point`` plus the ``angle`` its offset used —
    everything a part placement (or an SVG ``<use>``) needs."""

    point: Point
    angle: float


#: The length of a thigh and of a shin, and of an upper arm and a forearm, in
#: paint pixels.
THIGH = SHIN = 40.0
UPPER_ARM, FOREARM = 46.0, 42.0

# Parent-first declaration; a single in-order pass evaluates the tree.
#
# A limb angle is a world angle: 0 is down, a negative angle is to the front
# (the right of the picture, where the pirate looks), a positive one is to the
# back. Each bone of a limb has its own channel in the pose, so a knee and an
# elbow bend where the pose says.
PIRATE_BONES: Tuple[PirateBone, ...] = (
    # The pelvis and the chest ride the body tilt from the root.
    PirateBone("hip", None, lambda p, k: (0.0, -84.0), lambda p, k, tilt: tilt),
    PirateBone(
        "chest", None,
        lambda p, k: (0.0, -150.0 + p["shoulder_bounce"]),
        lambda p, k, tilt: tilt,
    ),
    # The head is on the chest: it turns about the base of the neck, so no
    # pose can take it away from the body.
    PirateBone(
        "head", "chest",
        lambda p, k: (6.0, -62.0 + p["head_y"]),
        lambda p, k, tilt: tilt + p["head_tilt"],
    ),
    # The shoulders are on the chest. The arm with the sword is on the side
    # the pirate looks to; the other arm is on the side behind.
    PirateBone("back_shoulder", "chest", lambda p, k: (-24.0, -10.0), lambda p, k, tilt: tilt),
    PirateBone("front_shoulder", "chest", lambda p, k: (22.0, -10.0), lambda p, k, tilt: tilt),
    PirateBone("left_hip", None, lambda p, k: (-14.0, -80.0), lambda p, k, tilt: tilt),
    PirateBone("right_hip", None, lambda p, k: (14.0, -80.0), lambda p, k, tilt: tilt),
    PirateBone("left_knee", "left_hip", lambda p, k: (0.0, THIGH), lambda p, k, tilt: p["left_thigh"]),
    PirateBone("right_knee", "right_hip", lambda p, k: (0.0, THIGH), lambda p, k, tilt: p["right_thigh"]),
    PirateBone("left_foot", "left_knee", lambda p, k: (0.0, SHIN), lambda p, k, tilt: p["left_shin"]),
    PirateBone("right_foot", "right_knee", lambda p, k: (0.0, SHIN), lambda p, k, tilt: p["right_shin"]),
    # The arm with no sword, then the arm with the sword.
    PirateBone("back_elbow", "back_shoulder", lambda p, k: (0.0, UPPER_ARM), lambda p, k, tilt: p["off_upper"]),
    PirateBone("back_hand", "back_elbow", lambda p, k: (0.0, FOREARM), lambda p, k, tilt: p["off_fore"]),
    PirateBone("front_elbow", "front_shoulder", lambda p, k: (0.0, UPPER_ARM), lambda p, k, tilt: p["sword_upper"]),
    PirateBone("front_hand", "front_elbow", lambda p, k: (0.0, FOREARM), lambda p, k, tilt: p["sword_fore"]),
)


def ground_y(h: float) -> float:
    """Where the ground is in a frame ``h`` paint pixels high."""
    return h * 0.83


def root_origin(pose: Mapping[str, float], kind: str, w: float, h: float) -> Point:
    """The whole-body root (``char_origin``): the middle of the stance on the
    ground, moved by the pose (``root_x`` and ``bob`` are in frame pixels)."""
    return (w * 0.50 + pose["root_x"] * SCALE, ground_y(h) + pose["bob"] * SCALE)


def evaluate(
    pose: Mapping[str, float],
    kind: str,
    w: float,
    h: float,
    global_tilt: float,
) -> Dict[str, BonePose]:
    """Evaluate the whole tree for one posed frame.

    Returns ``{bone_name: BonePose}`` plus ``"root"`` for ``char_origin``.
    ``global_tilt`` is the body lean the caller already resolved (it folds in the
    scarfed-taunt nudge), kept as a parameter so this stays pure kinematics.
    """
    root = root_origin(pose, kind, w, h)
    out: Dict[str, BonePose] = {"root": BonePose(root, global_tilt)}
    for bone in PIRATE_BONES:
        parent_pt = out[bone.parent].point if bone.parent else root
        ang = bone.angle(pose, kind, global_tilt)
        pt = transform(bone.offset(pose, kind), parent_pt, deg=ang)
        out[bone.name] = BonePose(pt, ang)
    return out


__all__ = ["PirateBone", "BonePose", "PIRATE_BONES", "ground_y", "root_origin", "evaluate"]
