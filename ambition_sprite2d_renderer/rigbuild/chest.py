"""The chest family's anatomy, for ``creature_rig``: a box with a hinged lid.

A chest is drawn from the front and a little above: a ``base`` bone at the
box's bottom centre (the root), a ``lid`` hinged on the box's back top edge,
a ``lock`` hanging on the box's front, and (where the drawing has one) a
``treasure`` heap inside. The SVG marks the joints ``base``, ``hinge``,
``lid_top``, ``lock``, ``lock_end`` and optionally ``treasure`` /
``treasure_top``.

A lid swinging toward the viewer is drawn four times, as a swap set on the
``lid.*`` channels (``lid``): closed, ajar (lifted a hand's breadth), up
(past the vertical, its underside toward us) and open (thrown back). The
``lid`` bone turns the lid on its hinge for a rattle; ``bone.lid.scale_y``
squashes it about the hinge for the open lid's bounce.

Used by the treasure chest and the boss chest
(``scripts/build_treasure_chest_rig.py``, ``scripts/build_boss_chest_rig.py``).
"""

from __future__ import annotations

from typing import Dict, List

from .creature_rig import BoneSpec, CreatureSpec, Point, Pose, segment, track, write  # noqa: F401

LIDS = ("closed", "ajar", "up", "open")


def lid(state: str) -> Pose:
    """One lid drawing shown, the rest hidden."""
    return {f"lid.{name}": 1.0 if name == state else 0.0 for name in LIDS}


def skeleton(J: Dict[str, Point]) -> List[BoneSpec]:
    bones = [
        ("base", None, J["base"], 0.0, 0.0),
        segment("lid", "base", J["hinge"], J["lid_top"]),
        segment("lock", "base", J["lock"], J["lock_end"]),
    ]
    if "treasure" in J:
        bones.append(segment("treasure", "base", J["treasure"], J["treasure_top"]))
    return bones


def chest_spec(**fields) -> CreatureSpec:
    """A ``CreatureSpec`` with the chest skeleton: no legs, no IK."""
    return CreatureSpec(skeleton=skeleton, legs=(), ankle_joint="base", **fields)
