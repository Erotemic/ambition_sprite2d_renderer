"""The cut-rope rope is a kit for a rope of any length (``column_tile``)."""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pytest

from ambition_sprite2d_renderer.authoring.sheet_build import _published_column_tile
from ambition_sprite2d_renderer.targets.props import cut_rope_rope as rope


def _rows() -> np.ndarray:
    return np.asarray(rope._draw_frame("idle", 0, 1)).astype(int)


def test_the_tile_joins_the_next_copy_of_itself():
    """The game draws the tile again under itself. The row after the tile is
    then the first row of the tile, so the art must have that same row there,
    and the same row before: a filtered sample at the edge of a tile reads the
    row on the other side. One period of plain braid is on each side, so a
    reduced copy of the sheet (six rows to one texel) joins also.
    """
    rows = _rows()
    start, end = rope.COLUMN_TILE
    assert end - start == rope.TILE_ROWS and (end - start) % rope.PERIOD == 0
    for k in range(-rope.PERIOD, rope.PERIOD):
        assert np.array_equal(rows[start + k], rows[end + k]), (
            f"row {start + k} (the tile's first row {k:+d}) is not row {end + k} "
            f"(its end {k:+d}): the braid shows a step where the tile repeats"
        )
    # Not vacuous: the rows are a drawing, and the braid is not the same on
    # each row.
    assert rows[start:end, :, 3].max() == 255
    assert not np.array_equal(rows[start], rows[start + rope.PERIOD // 2])


def test_the_cap_and_the_end_are_not_the_tile():
    """The tie is in the cap and the knot is in the end. If one of them
    reached the tile, each copy of the tile would show it."""
    rows = _rows()
    start, end = rope.COLUMN_TILE
    opaque = rows[:, :, 3] > 128
    # The tie and the knot are wider than the braid.
    braid_width = int(opaque[start:end].any(axis=0).sum())
    assert int(opaque[:start].any(axis=0).sum()) > braid_width, "the cap has no tie"
    assert int(opaque[end:].any(axis=0).sum()) > braid_width, "the end has no knot"


def test_each_boundary_is_on_a_whole_texel_in_each_reduced_copy():
    start, end = rope.COLUMN_TILE
    height = rope.FRAME_SIZE[1]
    for divisor in (2, 4, 6):  # the half, quarter and one-sixth copies
        for rows in (start, end, height):
            assert rows % divisor == 0, f"{rows} rows is not whole at 1/{divisor}"


def test_the_published_sheet_states_the_tile_as_fractions(tmp_path: Path):
    rope.render(tmp_path)
    ron = (tmp_path / "cut_rope_rope_spritesheet.ron").read_text()
    stated = re.search(r"column_tile: Some\(\(start: ([0-9.]+), end: ([0-9.]+)\)\)", ron)
    assert stated, f"the sheet does not state a column tile:\n{ron}"
    start, end = rope.COLUMN_TILE
    height = float(re.search(r"frame_height: (\d+)", ron).group(1))
    assert height == rope.FRAME_SIZE[1], "premise: the sheet publishes the frame the target draws"
    assert float(stated.group(1)) == pytest.approx(start / height)
    assert float(stated.group(2)) == pytest.approx(end / height)


def test_a_sheet_that_declares_no_tile_states_none(tmp_path: Path):
    """The control: another prop of the same arena."""
    from ambition_sprite2d_renderer.targets.props import cut_rope_anvil

    cut_rope_anvil.render(tmp_path)
    assert "column_tile" not in (tmp_path / "cut_rope_anvil_spritesheet.ron").read_text()


def test_the_tile_moves_with_the_frame_and_must_stay_inside_it():
    # Padding or a crop moves each row by `dy`.
    assert _published_column_tile((36, 60), 4.0, 100, "t") == {"start": 0.4, "end": 0.64}
    assert _published_column_tile(None, 0.0, 96, "t") is None
    with pytest.raises(ValueError, match="not inside the frame"):
        _published_column_tile((36, 60), -40.0, 96, "t")
    with pytest.raises(ValueError, match="not inside the frame"):
        _published_column_tile((60, 36), 0.0, 96, "t")
