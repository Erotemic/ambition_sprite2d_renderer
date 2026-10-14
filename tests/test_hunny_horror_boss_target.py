from __future__ import annotations

from ambition_sprite2d_renderer.targets.characters import hunny_horror_boss as target


def test_hunny_horror_boss_bindings_name_rows_the_sheet_publishes():
    rows = {name for name, _frames, _duration in target.ROWS}
    for binding, spec in target.ACTOR_METADATA["animation_bindings"].items():
        assert spec["animation"] in rows, binding


def test_hunny_horror_boss_frames_stay_inside_the_frame():
    """A frame clipped at its edge loses a paw or an ear in the game."""
    for name, frames, _duration in target.ROWS:
        for i in range(frames):
            box = target.render_frame(name, i, frames).getchannel("A").getbbox()
            assert box is not None, (name, i)
            w, h = target.FRAME_SIZE
            assert box[0] > 0 and box[1] > 0 and box[2] < w and box[3] < h, (name, i, box)
