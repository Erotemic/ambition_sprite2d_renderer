"""Player robot v3 from behind (the ladder climb)."""

from __future__ import annotations

from PIL import ImageChops

from ambition_sprite2d_renderer.targets.characters import player_robot_v3 as robot
from ambition_sprite2d_renderer.targets.characters.player_robot_v3_back import BACK_ROWS
from ambition_sprite2d_renderer.targets.characters.player_robot_v3_motion import MIRRORED


def test_the_back_view_is_the_size_of_the_side_view():
    side, back = robot.load_doc(), robot.load_back_doc()
    assert back.svg_source["scale"] == side.svg_source["scale"]
    assert back.frame["width"] == side.frame["width"]
    assert back.frame["ground_y"] == side.frame["ground_y"]
    # The hips of the two rigs are at one height: a row of one view does not
    # stand above or below a row of the other.
    assert back.bone("pelvis")["offset"] == side.bone("pelvis")["offset"]


def test_a_back_row_is_one_picture_for_the_two_facings():
    """The robot has one ear cup. A mirror of the back view puts it on the
    other ear, so the row of the other facing is the same picture."""
    for row in BACK_ROWS:
        frames = int(robot.load_back_doc().clips[row]["frames"])
        for index in (0, frames // 2):
            one = robot.render_frame(row, index, frames)
            other = robot.render_frame(MIRRORED.format(row), index, frames)
            assert ImageChops.difference(one, other).getbbox() is None
            assert one.getbbox() is not None
