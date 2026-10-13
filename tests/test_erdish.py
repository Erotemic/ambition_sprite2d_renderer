from __future__ import annotations

from ambition_sprite2d_renderer.targets.characters import erdish


def test_erdish_has_the_rows_the_game_plays_for_a_body_it_controls():
    required = {
        "idle",
        "walk",
        "run",
        "jump",
        "fall",
        "dash_startup",
        "dash",
        "crouch",
        "crouch_walk",
        "slide",
        "roll",
        "wall_grab",
        "wall_jump",
        "ledge_grab",
        "ledge_getup",
        "ledge_roll",
        "climb",
        "swim",
        "block",
        "hit",
        "death",
        "talk",
        "interact",
    }
    assert required <= {name for name, _frames, _ms in erdish.ROWS}


def test_no_erdish_frame_is_cut_by_the_edge_of_its_cell():
    """A pose or a piece of chalk that goes past the cell is cut there, and
    the cut shows in the game as a straight edge."""
    width, height = erdish.FRAME_SIZE
    for name, frames, _ms in erdish.ROWS:
        for index in range(frames):
            alpha = erdish._render_frame(name, index, frames).getchannel("A").point(lambda a: 255 if a > 16 else 0)
            box = alpha.getbbox()
            assert box is not None, (name, index)
            assert box[0] > 0 and box[1] > 0 and box[2] < width and box[3] < height, (name, index, box)
