"""The people who are drawn on ``_person_rig``: each sheet has the rows it
names, and no frame of it is cut by the edge of its cell."""
from __future__ import annotations

import importlib

import pytest

from ambition_sprite2d_renderer.targets.characters import _person_rig

#: module -> the sheets it publishes.
MODULES = {
    "girdle": ("girdle",),
    "neil_ongras_turfson": ("neil_ongras_turfson",),
    "m_leblanc": ("m_leblanc",),
    "python_goras": ("python_goras",),
    "galwah": ("galwah",),
    "jeff_hinter": ("jeff_hinter",),
    "marie_curry": ("marie_curry",),
    "leib_knives": ("leib_knives",),
}
SHEETS = [(module, sheet) for module, sheets in MODULES.items() for sheet in sheets]


def _person(module: str, sheet: str):
    importlib.import_module(f"ambition_sprite2d_renderer.targets.characters.{module}")
    return _person_rig.CAST[sheet]


@pytest.mark.parametrize("module,sheet", SHEETS)
def test_every_row_of_the_sheet_has_a_pose(module, sheet):
    _person(module, sheet).check()


@pytest.mark.parametrize("module,sheet", SHEETS)
def test_no_frame_is_cut_by_the_edge_of_its_cell(module, sheet):
    """A pose or an effect that goes past the cell is cut there, and the cut
    shows in the game as a straight edge."""
    assert _person(module, sheet).cut_frames() == []


def test_an_idle_row_is_one_the_game_knows():
    """The game plays `idle` (or `rest`) for a body at rest."""
    for module, sheet in SHEETS:
        rows = {name for name, _frames, _ms in _person(module, sheet).rows}
        assert rows & {"idle", "rest"}, sheet
