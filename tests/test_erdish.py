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
