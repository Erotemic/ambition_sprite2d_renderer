"""The terrain skins and the motes keep the contract the game lays them by."""

from __future__ import annotations

import numpy as np
import pytest

from ambition_sprite2d_renderer.terrain import motes, skins


@pytest.mark.parametrize("skin", skins.SKINS, ids=lambda skin: skin.key)
def test_each_part_of_a_skin_has_the_size_the_game_lays_it_at(skin: skins.Skin) -> None:
    # The game repeats each picture at `PX_PER_UNIT`, and puts the surface
    # line of a cap on the top of a block. A picture of another size would be
    # laid at another scale, with no error.
    sizes = {"fill": skins.FILL, "cap": skins.CAP, "under": skins.UNDER, "side": skins.SIDE, "oneway": skins.ONEWAY}
    for part, make in skins.PARTS.items():
        image = make(skin)
        w, h = sizes[part]
        assert image.size == (w * skins.PX_PER_UNIT, h * skins.PX_PER_UNIT), part


@pytest.mark.parametrize("skin", skins.SKINS, ids=lambda skin: skin.key)
def test_a_fill_is_opaque_and_a_cap_covers_its_surface_line(skin: skins.Skin) -> None:
    fill = np.asarray(skins.fill(skin))
    assert fill[:, :, 3].min() == 255, "a hole in a fill shows what is behind the ground"
    cap = np.asarray(skins.cap(skin))[:, :, 3]
    row = int(skins.CAP_SURFACE * skins.PX_PER_UNIT) + 1
    assert (cap[row] > 200).mean() > 0.9, "the cap has gaps on the line a body stands on"
    under = np.asarray(skins.under(skin))[:, :, 3]
    assert under[-1].max() < 255 or under[-1].mean() < 128, "an underside that is solid at its end reads as more ground"


@pytest.mark.parametrize("skin", skins.SKINS, ids=lambda skin: skin.key)
def test_a_part_repeats_with_no_seam(skin: skins.Skin) -> None:
    # The column at one end of a picture that repeats along x must be as
    # near to the column at the other end as two columns next to each other
    # inside it are.
    for part in ("fill", "cap", "under", "oneway"):
        image = np.asarray(skins.PARTS[part](skin)).astype(float)
        image = image[:, :, :3] * image[:, :, 3:4] / 255.0
        seam = np.abs(image[:, 0] - image[:, -1]).mean()
        inside = np.abs(image[:, 1:] - image[:, :-1]).mean(axis=(0, 2))
        assert seam <= np.percentile(inside, 99) + 4.0, f"{skin.key} {part}: seam {seam:.1f}"


@pytest.mark.parametrize("theme", sorted(motes.MOTES))
def test_a_mote_strip_has_its_squares_and_each_one_is_clear_at_its_edge(theme: str) -> None:
    strip = np.asarray(motes.strip(theme))
    assert strip.shape == (motes.CELL, motes.CELL * motes.VARIANTS, 4)
    for variant in range(motes.VARIANTS):
        cell = strip[:, variant * motes.CELL : (variant + 1) * motes.CELL, 3]
        assert cell.max() > 60, "a square with no mote"
        edge = np.concatenate([cell[0], cell[-1], cell[:, 0], cell[:, -1]])
        assert edge.max() < 40, "a mote that is cut by the edge of its square shows the cut"
