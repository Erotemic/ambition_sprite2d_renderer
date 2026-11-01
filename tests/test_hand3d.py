"""The Dealer's Hand's 3D model: every pose and view is the same hand."""

import numpy as np

from ambition_sprite2d_renderer.targets.characters import _hand3d as H3


def test_every_pose_keeps_each_phalanx_its_length():
    rest = H3.digits(H3.HandPose())
    for pose in H3.REFERENCE_POSES.values():
        for name, digit in H3.digits(pose).items():
            want = [np.linalg.norm(b - a) for a, b in zip(rest[name].joints, rest[name].joints[1:])]
            got = [np.linalg.norm(b - a) for a, b in zip(digit.joints, digit.joints[1:])]
            assert np.allclose(want, got), name


def test_the_palm_faces_us_at_roll_0_and_its_back_at_180():
    assert H3.Camera((0, 0), 0.0, 0.0).faces_us((0, 0, 1))
    assert not H3.Camera((0, 0), 0.0, 180.0).faces_us((0, 0, 1))


def test_the_reference_sheet_renders():
    sheet = H3.reference_sheet()
    assert np.asarray(sheet)[..., 3].min() == 255
