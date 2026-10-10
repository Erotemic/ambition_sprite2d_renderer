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


def test_limbs_swing_in_world_space_not_relative_to_tilt() -> None:
    """The convention of the family: the world angle of a limb bone is its
    channel of the pose, whatever the body tilt is (a relative-FK humanoid has
    legs that lean with the torso). Poison the tilt; the angles must not move."""
    pose = animation_pose("walk", 3, 8)
    a = R.evaluate(pose, "pirate_raider", W, H, pose["body_tilt"])
    b = R.evaluate(pose, "pirate_raider", W, H, pose["body_tilt"] + 40.0)
    for joints in (a, b):
        assert abs(joints["left_knee"].angle - pose["left_thigh"]) < 1e-9
        assert abs(joints["left_foot"].angle - pose["left_shin"]) < 1e-9
        assert abs(joints["front_elbow"].angle - pose["sword_upper"]) < 1e-9
        assert abs(joints["front_hand"].angle - pose["sword_fore"]) < 1e-9


def test_the_head_stays_on_the_body_in_every_frame() -> None:
    """The head is a bone of the chest: it turns about the base of the neck.
    The pirates before 2026-10-10 had a head on the root, and a pose that
    turned it took it far from the body. No frame may do that."""
    from ambition_sprite2d_renderer.authoring.sheet_build import ANIMATIONS

    neck = math.hypot(6.0, 62.0)
    for anim, count, _ms in ANIMATIONS:
        for index in range(count):
            pose = animation_pose(anim, index, count)
            joints = R.evaluate(pose, "pirate_raider", W, H, pose["body_tilt"])
            (hx, hy), (cx, cy) = joints["head"].point, joints["chest"].point
            assert abs(math.hypot(hx - cx, hy - cy) - neck) < 2.5, (anim, index)
            # The head does not turn far from the line of the body.
            assert abs(pose["head_tilt"]) <= 16.0, (anim, index)


def test_a_standing_pose_has_a_foot_on_the_ground() -> None:
    """Each pose but the death is planted: the lower foot is on the ground."""
    from ambition_sprite2d_renderer.authoring.sheet_build import ANIMATIONS

    for anim, count, _ms in ANIMATIONS:
        if anim == "death":
            continue
        for index in range(count):
            pose = animation_pose(anim, index, count)
            joints = R.evaluate(pose, "pirate_raider", W, H, pose["body_tilt"])
            low = max(joints["left_foot"].point[1], joints["right_foot"].point[1])
            assert abs(low - R.ground_y(H)) < 0.5, (anim, index, low)


def test_the_sword_arm_is_on_the_side_the_pirate_looks_to() -> None:
    """The arm with the sword is to the front and the other arm is behind, so
    the two arms do not cross over the chest in the guard."""
    pose = animation_pose("idle", 0, 6)
    joints = R.evaluate(pose, "pirate_raider", W, H, pose["body_tilt"])
    assert joints["front_shoulder"].point[0] > joints["back_shoulder"].point[0]
    assert joints["front_hand"].point[0] > joints["chest"].point[0] > joints["back_hand"].point[0]


def test_golden_walk_pose() -> None:
    """Locks the exact geometry of EVERY joint for one known frame, so a silent
    offset/angle drift in any bone — not just the six a smaller sample would
    cover — fails here rather than relying on the SVG-fidelity test to notice."""
    pose = animation_pose("walk", 3, 8)
    J = R.evaluate(pose, "pirate_raider", W, H, pose["body_tilt"])
    golden = {
        "root": ((256.000, 427.519), 5.000),
        "hip": ((263.321, 343.838), 5.000),
        "chest": ((269.073, 278.089), 5.000),
        "head": ((277.233, 216.337), 2.000),
        "back_shoulder": ((246.036, 266.036), 5.000),
        "front_shoulder": ((291.861, 270.045), 5.000),
        "left_hip": ((249.026, 346.603), 5.000),
        "right_hip": ((276.919, 349.043), 5.000),
        "left_knee": ((236.410, 384.561), 18.385),
        "right_knee": ((289.535, 387.002), -18.385),
        "left_foot": ((204.156, 408.219), 53.740),
        "right_foot": ((302.151, 424.960), -18.385),
        "back_elbow": ((248.420, 311.974), -2.971),
        "back_hand": ((266.151, 350.048), -24.971),
        "front_elbow": ((299.657, 315.379), -9.757),
        "front_hand": ((340.702, 324.286), -77.757),
    }
    assert set(golden) == set(J), "every evaluated joint must be pinned"
    for name, ((gx, gy), ga) in golden.items():
        b = J[name]
        assert math.isclose(b.point[0], gx, abs_tol=1e-2), (name, b.point)
        assert math.isclose(b.point[1], gy, abs_tol=1e-2), (name, b.point)
        assert math.isclose(b.angle, ga, abs_tol=1e-2), (name, b.angle)
