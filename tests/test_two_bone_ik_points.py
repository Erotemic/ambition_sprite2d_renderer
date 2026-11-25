"""The shared point and angle interfaces describe the same two-bone chain."""

import math

import pytest

from ambition_sprite2d_renderer.authoring.rig import add, vec
from ambition_sprite2d_renderer.authoring.skeleton import (
    two_bone_ik,
    two_bone_ik_points,
)


@pytest.mark.parametrize("bend", [-1.0, 1.0])
@pytest.mark.parametrize("target", [(3, 12), (100, 0), (0, 0), (0, 1)])
def test_point_interface_matches_angle_interface(bend, target):
    root = (0.0, 0.0)
    upper, lower = 10.0, 8.0
    a1, a2 = two_bone_ik(root, target, upper, lower, bend=bend)
    joint, tip = two_bone_ik_points(root, target, upper, lower, bend=bend)
    assert joint == pytest.approx(add(root, vec(upper, a1)))
    assert tip == pytest.approx(add(joint, vec(lower, a2)))
    assert math.dist(root, joint) == pytest.approx(upper)
    assert math.dist(joint, tip) == pytest.approx(lower)
    expected_reach = max(2.0 + 1e-6, min(18.0 - 1e-6, math.dist(root, target)))
    assert math.dist(root, tip) == pytest.approx(expected_reach)


@pytest.mark.parametrize("bend", [-1.0, 1.0])
@pytest.mark.parametrize("target,reach", [((0, 15), 15), ((0, 100), 17.8), ((0, .5), 2.1)])
def test_authored_reach_margins_and_bend(bend, target, reach):
    root = (0.0, 0.0)
    joint, tip = two_bone_ik_points(
        root, target, 10.0, 8.0, bend=bend,
        fold_margin=.1, extension_margin=.2,
    )
    assert tip == pytest.approx((0.0, reach), abs=1e-9)
    assert joint[0] * bend > 0
    assert math.dist(root, joint) == pytest.approx(10.0)
    assert math.dist(joint, tip) == pytest.approx(8.0)
