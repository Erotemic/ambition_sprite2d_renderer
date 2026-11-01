"""The hand generator: one skeleton in every pose and view."""

import numpy as np
import pytest

from ambition_sprite2d_renderer.handgen import POSES, SPECS, STYLES, Camera, HandPose, HandSpec, digits, draw_hand, landmarks
from ambition_sprite2d_renderer.handgen.__main__ import main


def _lengths(digit):
    return [np.linalg.norm(b - a) for a, b in zip(digit.joints, digit.joints[1:])]


@pytest.mark.parametrize("spec", list(SPECS.values()) + [HandSpec().mirrored()])
def test_every_pose_keeps_each_phalanx_its_length(spec):
    rest = digits(spec, HandPose())
    for pose in POSES.values():
        for name, digit in digits(spec, pose).items():
            assert np.allclose(_lengths(rest[name]), _lengths(digit)), name


def test_a_left_hand_is_the_right_one_mirrored():
    right, left = HandSpec(), HandSpec().mirrored()
    for name, d in digits(right, POSES["grasp"]).items():
        for a, b in zip(d.joints, digits(left, POSES["grasp"])[name].joints):
            assert np.allclose(a * [1, -1, 1], b)


def test_the_palm_faces_us_at_roll_0_and_its_back_at_180():
    assert Camera((0, 0), 0.0, 0.0).palm_faces_us()
    assert not Camera((0, 0), 0.0, 180.0).palm_faces_us()


def test_a_curl_toward_us_shows_the_nail_side_from_the_palm():
    cam = Camera((0, 0), 0.0, 0.0)
    fist = digits(HandSpec(), POSES["fist"])["middle"]
    assert cam.faces_us(digits(HandSpec(), POSES["open"])["middle"].pads[-1])
    assert not cam.faces_us(fist.pads[-1])


@pytest.mark.parametrize("style", sorted(STYLES))
@pytest.mark.parametrize("roll", [0.0, 45.0, 90.0, 135.0, 180.0])
def test_a_hand_draws_inside_its_canvas(style, roll):
    cam = Camera((60, 110), -40.0, roll)
    drawing = draw_hand(HandSpec(), POSES["open"], cam, (192, 168), STYLES[style])
    a = np.asarray(drawing.frame())[..., 3]
    assert a.max() == 255
    assert a[0].max() == 0 and a[-1].max() == 0 and a[:, 0].max() == 0 and a[:, -1].max() == 0
    assert set(drawing.landmarks) >= {"wrist", "palm", "grip", "index_tip", "thumb_tip"}


def test_landmarks_follow_the_camera():
    a = landmarks(HandSpec(), POSES["open"], Camera((10, 10), 0.0))
    b = landmarks(HandSpec(), POSES["open"], Camera((30, 10), 0.0))
    assert np.isclose(b["index_tip"][0] - a["index_tip"][0], 20.0)


def test_the_cli_writes_both_sheets(tmp_path):
    for cmd in ("model", "poses"):
        out = tmp_path / f"{cmd}.png"
        assert main([cmd, "--out", str(out)]) == 0 and out.exists()


@pytest.mark.parametrize("radius", [2.5, 4.0, 7.0])
def test_a_grip_closes_each_finger_onto_the_rod_without_entering_it(radius):
    from ambition_sprite2d_renderer.handgen.solve import _clearance, grip

    pose, rod = grip(HandSpec(), radius)
    ds = digits(HandSpec(), pose)
    for name in ("index", "middle", "ring", "little"):
        gap = _clearance(ds[name], rod)
        assert -0.05 <= gap <= 0.3, (name, gap)
    # A thicker rod opens the hand.
    assert pose.curls[1] < grip(HandSpec(), radius * 0.6)[0].curls[1]


def test_a_pinch_meets_the_thumb_and_index_tips():
    from ambition_sprite2d_renderer.handgen.solve import pinch

    _pose, miss = pinch(HandSpec(), "index")
    assert miss < 0.05
