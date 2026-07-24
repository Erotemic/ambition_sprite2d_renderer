"""The pirate's explicit skeleton reproduces its authored joint tree.

The pirate was the first character lifted from an implicit inline-``transform``
joint tree into a declared, poseable skeleton (``_pirate_rig``). ``paint_character``
now reads every joint from :func:`evaluate`, so these tests pin the kinematic
contract the paint pass depends on — structure, the load-bearing conventions
(sockets ride the body tilt; limbs swing in world space), and a golden pose so a
silent geometry drift fails here instead of shifting every pirate sprite.
"""
from __future__ import annotations

import math

from ambition_sprite2d_renderer.targets.characters import _pirate_rig as R
from ambition_sprite2d_renderer.targets.characters._pirate_common import (
    animation_pose,
)

W = H = 512.0


def _zero_pose():
    # A neutral pose with every channel evaluate() reads present and at rest.
    return animation_pose("__rest__", 0, 1)  # unknown anim -> base defaults


def test_tree_is_parent_first_and_fully_resolvable() -> None:
    seen = {"root"}
    for bone in R.PIRATE_BONES:
        assert bone.parent is None or bone.parent in seen, bone.name
        seen.add(bone.name)
    J = R.evaluate(_zero_pose(), "pirate_raider", W, H, 0.0)
    assert set(J) == seen
    assert len(R.PIRATE_BONES) == 15


def test_sockets_ride_the_body_tilt() -> None:
    """Pelvis/spine/head and the shoulder+hip sockets are placed at the body
    tilt: rotating the whole body must swing them about the root."""
    pose = _zero_pose()
    root = R.root_origin(pose, "pirate_raider", W, H)
    for tilt in (0.0, 20.0):
        J = R.evaluate(pose, "pirate_raider", W, H, tilt)
        for socket in ("hip", "chest", "back_shoulder", "front_shoulder",
                       "left_hip", "right_hip"):
            assert abs(J[socket].angle - tilt) < 1e-9, socket
        # the hip sits straight below the root at rest; a +tilt rotates it
        # clockwise (screen +y down), pushing its x to the right of the root.
        assert J["hip"].point[0] > root[0] if tilt > 0 else True


def test_legs_swing_in_world_space_not_relative_to_tilt() -> None:
    """The defining pirate convention: a leg's world angle is its pose angle,
    independent of the body tilt (unlike a relative-FK humanoid whose legs lean
    with the torso). Poison the tilt; the knee angle must not move."""
    pose = animation_pose("walk", 3, 8)
    a = R.evaluate(pose, "pirate_raider", W, H, pose["body_tilt"])
    b = R.evaluate(pose, "pirate_raider", W, H, pose["body_tilt"] + 40.0)
    assert abs(a["left_knee"].angle - pose["left_leg"]) < 1e-9
    assert abs(b["left_knee"].angle - pose["left_leg"]) < 1e-9
    assert abs(a["left_foot"].angle - pose["left_leg"] * 0.3) < 1e-9


def test_admiral_narrows_the_shoulders() -> None:
    pose = _zero_pose()
    raider = R.evaluate(pose, "pirate_raider", W, H, 0.0)
    admiral = R.evaluate(pose, "pirate_admiral", W, H, 0.0)
    span = lambda J: J["back_shoulder"].point[0] - J["front_shoulder"].point[0]
    assert span(admiral) < span(raider)


def test_golden_walk_pose() -> None:
    """Locks the exact joint geometry for one known frame; guards the offsets
    and root layout against silent drift."""
    pose = animation_pose("walk", 3, 8)
    J = R.evaluate(pose, "pirate_raider", W, H, pose["body_tilt"])
    golden = {
        "root": ((263.071, 435.931), 3.536),
        "hip": ((266.771, 376.045), 3.536),
        "chest": ((270.609, 313.931), 3.536),
        "head": ((276.929, 233.540), 1.657),
        "left_knee": ((250.727, 409.315), -7.920),
        "front_hand": ((288.679, 382.219), -14.340),
    }
    for name, ((gx, gy), ga) in golden.items():
        b = J[name]
        assert math.isclose(b.point[0], gx, abs_tol=1e-2), (name, b.point)
        assert math.isclose(b.point[1], gy, abs_tol=1e-2), (name, b.point)
        assert math.isclose(b.angle, ga, abs_tol=1e-2), (name, b.angle)
