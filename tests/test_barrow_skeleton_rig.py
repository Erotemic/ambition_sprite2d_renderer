"""The skeleton family shares fixed-length IK and equipment contact goals."""
import math

import pytest

from ambition_sprite2d_renderer.targets.characters import barrow_skeleton as skeleton
from ambition_sprite2d_renderer.targets.characters import barrow_skeleton_archer as archer


@pytest.mark.parametrize('target', [skeleton, archer])
def test_shared_skeleton_pose_constraints(target, monkeypatch):
    real_ik = skeleton.two_bone_ik_points
    calls = []

    def counted(*args, **kwargs):
        calls.append(1)
        return real_ik(*args, **kwargs)

    monkeypatch.setattr(skeleton, 'two_bone_ik_points', counted)
    for anim, count, _ in target.ROWS:
        for i in range(count):
            calls.clear()
            pose = target.pose(anim, i, count)
            if target is archer:
                joints, _, nock = archer.solve(pose)
                if pose.contact:
                    finger = archer._bow_point(joints['far_arm'][-1], pose.angle, 5., 0.)
                    assert finger == pytest.approx(nock, abs=1e-7)
            else:
                joints = skeleton._solve(pose)
            assert len(calls) == 4
            for part, lengths in (('arm', skeleton.ARM_LENGTHS), ('leg', skeleton.LEG_LENGTHS)):
                for side in ('near', 'far'):
                    root, middle, tip = joints[f'{side}_{part}']
                    assert math.dist(root, middle) == pytest.approx(lengths[0])
                    assert math.dist(middle, tip) == pytest.approx(lengths[1])
            if anim in ('walk', 'run'):
                assert min(abs(joints[name][-1][1] - (skeleton.GROUND-4))
                           for name in ('near_leg', 'far_leg')) < .01
