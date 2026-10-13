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
    "jeff_hinter_armored": ("jeff_hinter_armored",),
    "marie_curry": ("marie_curry",),
    "leib_knives": ("leib_knives",),
    "mami_marzakhani": ("mami_marzakhani",),
    "anne_druid": ("anne_druid",),
    "davy_hylbert": ("davy_hylbert",),
    "pipi_tau": ("pipi_tau",),
    "paradox_barber": ("paradox_barber",),
    "data_lovelace": ("data_lovelace",),
    "georg_canter": ("georg_canter",),
    "admiral_grass_hopper": ("admiral_grass_hopper",),
    "joseph_furrier": ("joseph_furrier",),
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


def test_the_armored_hinter_is_the_man_of_the_other_sheet():
    """A character with a transform is one character with two sides: the
    armored sheet has the build, the stance and the head of the plain one,
    and the frames of its change before the lock are frames of the plain
    man."""
    from ambition_sprite2d_renderer.targets.characters import jeff_hinter as plain
    from ambition_sprite2d_renderer.targets.characters import jeff_hinter_armored as armored

    assert armored.X.b is plain.X.b
    assert armored.X.rest == plain.X.rest
    pose = plain.X.full(plain.X.poses["idle"](0, 8))
    assert [name for _piece, name in armored.X.head_layers(pose)][: len(plain.X.head_layers(pose))] == [name for _piece, name in plain.X.head_layers(pose)]
    frames = dict((name, n) for name, n, _ms in armored.X.rows)["transform"]
    first = armored.X.render_frame("transform", 0, frames)
    assert first.tobytes() == plain.X.render_frame("transform", 0, frames).tobytes()
    assert armored.X.render_frame("transform", frames - 1, frames).tobytes() != first.tobytes()


def test_a_mans_chest_does_not_stand_out_of_his_trunk():
    """`make_torso` is the trunk of a man: its chest is not in front of the
    wider of the shoulder and the waist by more than `CHEST_OUT`, whatever a
    character asks for."""
    kit = _person_rig.Kit((208, 176))
    narrow = _person_rig.make_torso(kit, ("t_narrow",), (200, 60, 60, 255), (120, 30, 30, 255), front=(8.0, 13.0, 8.0, 9.0))
    flat = _person_rig.make_torso(kit, ("t_flat",), (200, 60, 60, 255), (120, 30, 30, 255), front=(8.0, 8.0 + _person_rig.CHEST_OUT, 8.0, 9.0))
    assert narrow(0, 0)[0].getchannel("A").tobytes() == flat(0, 0)[0].getchannel("A").tobytes()
