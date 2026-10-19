"""Willson is a pelican on a bicycle: what makes him one, frame by frame."""

import math

from ambition_sprite2d_renderer.registry.discovery import discover_module_targets
from ambition_sprite2d_renderer.targets.characters import willson as target


def test_the_pedals_are_opposite_each_other_about_the_bottom_bracket():
    for animation, nframes, _duration_ms in target.ROWS:
        for index in range(nframes):
            pose = target.ROW_POSES[animation](index, nframes)
            near, far = target.pedal_points(pose)
            at, _held, _tilt, _crank = target._bike_of(pose)
            bracket = at(target.BRACKET)
            middle = ((near[0] + far[0]) / 2.0, (near[1] + far[1]) / 2.0)
            assert math.dist(middle, bracket) < 1e-6, (animation, index)
            assert abs(math.dist(near, far) - 2.0 * target.CRANK) < 1e-6, (animation, index)


def test_his_feet_are_on_the_pedals_while_he_rides():
    """A rider whose feet leave the pedals is a bird beside a bicycle."""
    for animation in ("idle", "walk", "run"):
        nframes = next(n for name, n, _ms in target.ROWS if name == animation)
        for index in range(nframes):
            assert target.ROW_POSES[animation](index, nframes)["feet"] == "pedal", (animation, index)


def test_the_wheels_turn_from_each_frame_of_a_ride_to_the_next():
    for animation in ("walk", "run"):
        nframes = next(n for name, n, _ms in target.ROWS if name == animation)
        turns = [target.ROW_POSES[animation](index, nframes)["wheel"] % 24 for index in range(nframes)]
        assert all(a != b for a, b in zip(turns, turns[1:] + turns[:1])), (animation, turns)
        frames = [target._render_frame(animation, index, nframes) for index in range(nframes)]
        assert all(a.tobytes() != b.tobytes() for a, b in zip(frames, frames[1:]))


def test_willson_is_a_character_target():
    report = discover_module_targets()
    assert target.TARGET_NAME in report.targets
    assert report.targets[target.TARGET_NAME].category == "characters"
