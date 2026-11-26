"""Publish dense part atlases for the character clips in the startup card."""

from pathlib import Path

from ...authoring.part_flipbook import build_rig_flipbook
from ..characters import director, player_robot_v3 as robot

PUBLICATION_TIERS = ["full"]
SHEET_FILES = [
    "director_closeup_parts.ron",
    "director_closeup_parts.png",
    "player_robot_v3_closeup_parts.ron",
    "player_robot_v3_closeup_parts.png",
]

def _publish(out_dir, name, rows, render_frame, selected, feet, texel_scale, tweens=()):
    rows = [row for row in rows if row[0] in selected]
    if {row[0] for row in rows} != selected:
        raise ValueError(f"{name} must publish all of {sorted(selected)}")

    def draw(clip, index, count):
        return render_frame(clip, index, count, scale=texel_scale, supersample=2)

    first_clip, count, _ = rows[0]
    size = draw(first_clip, 0, count).size
    flipbook = build_rig_flipbook(
        name, rows, draw, None, tuple(value * texel_scale for value in feet),
        size, [row for row in tweens if row in selected],
    )
    flipbook.texel_scale = texel_scale
    return list(flipbook.write(out_dir).values())


def render(out_dir, **_opts):
    out_dir = Path(out_dir)
    director_feet = director._body_metrics(*director._publication_frame_size())["feet_pixel"]
    robot_feet = robot.body_metrics(*robot.FRAME_SIZE)["feet_pixel"]
    # The robot renders without its gameplay sheet padding.
    pad_x, pad_y, _, _ = robot.PUBLISH_PADDING
    return _publish(
        out_dir, "director_closeup", director._doc().rows(), director._raw_frame,
        {"idle", "talk", "receive_low", "item_hold"}, (director_feet["x"], director_feet["y"]),
        texel_scale=16,
    ) + _publish(
        out_dir, "player_robot_v3_closeup", robot.ROWS, robot.render_frame,
        {"idle", "walk", "item_hold", "grab_hold"}, (robot_feet["x"] - pad_x, robot_feet["y"] - pad_y),
        texel_scale=9, tweens=robot.TWEENED_ROWS,
    )
