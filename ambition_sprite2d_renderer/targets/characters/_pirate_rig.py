"""Explicit bone skeleton for the pirate family.

The pirate is the first character lifted from an *implicit* joint tree — the
inline ``transform(...)`` calls scattered through ``_pirate_common``'s paint
pass — into a *declared, poseable* skeleton. Nothing about the drawn result
changes: ``paint_character`` now reads every joint from :func:`evaluate` instead
of recomputing it, so the animation lives on bones that can be edited, sampled,
and (next) exported to an SVG paper-doll assembled by this same skeleton.

The pirate keeps its OWN kinematic convention — deliberately not the shared
humanoid FK rig. A joint is ``parent_point + rot(offset, world_angle)`` where the
offset is rotated by the CHILD's own world angle: limb segments swing in world
space while their sockets ride the tilted pelvis. That mix (tilted sockets,
world-space swing) is exactly what gives the pirate its current read, so
reproducing it faithfully means modelling it as-is rather than reshaping it into
a relative-FK tree whose legs would lean with the body.

Angles use the renderer's screen convention: degrees, +y down, clockwise
positive. Offsets are in supersampled paint pixels (the space ``paint_character``
works in), so ``evaluate`` takes the already-scaled frame size and root.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Mapping, Optional, Tuple

from ...authoring.sheet_build import SCALE, transform

Point = Tuple[float, float]

# Admiral sits its shoulders slightly narrower; every other pirate shares one
# socket layout. Kept here so the skeleton — not the paint pass — owns the one
# per-kind geometry difference.
_ADMIRAL = "pirate_admiral"


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


# Parent-first declaration; a single in-order pass evaluates the tree.
PIRATE_BONES: Tuple[PirateBone, ...] = (
    # Pelvis / spine / head ride the body tilt from the root.
    PirateBone("hip", None, lambda p, k: (0.0, -60.0), lambda p, k, tilt: tilt),
    PirateBone(
        "chest", None,
        lambda p, k: (0.0, -124.0 + p["shoulder_bounce"]),
        lambda p, k, tilt: tilt,
    ),
    PirateBone(
        "head", None,
        lambda p, k: (8.0, -202.0 + p["head_y"]),
        lambda p, k, tilt: tilt + p["head_tilt"],
    ),
    # Shoulder + hip sockets: fixed offsets, tilt-oriented.
    PirateBone(
        "back_shoulder", None,
        lambda p, k: ((20.0 if k == _ADMIRAL else 24.0), -136.0),
        lambda p, k, tilt: tilt,
    ),
    PirateBone(
        "front_shoulder", None,
        lambda p, k: ((-22.0 if k == _ADMIRAL else -26.0), -136.0),
        lambda p, k, tilt: tilt,
    ),
    PirateBone("left_hip", None, lambda p, k: (-16.0, -56.0), lambda p, k, tilt: tilt),
    PirateBone("right_hip", None, lambda p, k: (18.0, -56.0), lambda p, k, tilt: tilt),
    # Legs swing in world angles off their sockets.
    PirateBone("left_knee", "left_hip", lambda p, k: (-4.0, 30.0), lambda p, k, tilt: p["left_leg"]),
    PirateBone("right_knee", "right_hip", lambda p, k: (4.0, 30.0), lambda p, k, tilt: p["right_leg"]),
    PirateBone(
        "left_foot", "left_knee",
        lambda p, k: (-8.0, 30.0 - p["left_foot_lift"]),
        lambda p, k, tilt: p["left_leg"] * 0.3,
    ),
    PirateBone(
        "right_foot", "right_knee",
        lambda p, k: (8.0, 30.0 - p["right_foot_lift"]),
        lambda p, k, tilt: p["right_leg"] * 0.3,
    ),
    # Back arm (weapon-free) then front arm (weapon).
    PirateBone("back_elbow", "back_shoulder", lambda p, k: (4.0, 52.0), lambda p, k, tilt: p["left_arm"]),
    PirateBone("back_hand", "back_elbow", lambda p, k: (0.0, 48.0), lambda p, k, tilt: p["left_arm"] * 0.55),
    PirateBone("front_elbow", "front_shoulder", lambda p, k: (6.0, 50.0), lambda p, k, tilt: p["right_arm"]),
    PirateBone("front_hand", "front_elbow", lambda p, k: (0.0, 46.0), lambda p, k, tilt: p["weapon"] * 0.35),
)


def root_origin(pose: Mapping[str, float], kind: str, w: float, h: float) -> Point:
    """The whole-body root (``char_origin``): stance centre + walk/idle drift and
    the death lean, in supersampled paint pixels."""
    death_t = pose.get("death_t", 0.0)
    cx = w * (0.48 if kind == _ADMIRAL else 0.50)
    ground = h * 0.83
    return (
        cx + pose["root_x"] * SCALE + death_t * 12.0 * SCALE,
        ground + pose["bob"] * SCALE + death_t * 5.0 * SCALE,
    )


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


__all__ = ["PirateBone", "BonePose", "PIRATE_BONES", "root_origin", "evaluate"]
