"""The terrain skins and the motes keep the contract the game lays them by."""

from __future__ import annotations

import numpy as np
import pytest

from ambition_sprite2d_renderer.terrain import decor, motes, skins


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


@pytest.mark.parametrize("theme", sorted(decor.DECOR))
def test_each_thing_of_the_decor_stands_on_the_ground_line_inside_its_square(theme: str) -> None:
    # The game puts the bottom of a square on the top of a block. A thing
    # that does not reach the bottom of its square is in the air, and a thing
    # that is cut by a side of its square shows the cut.
    strip = np.asarray(decor.strip(theme))
    px = decor.CELL_PX
    assert strip.shape == (px, px * decor.VARIANTS, 4)
    for variant in range(decor.VARIANTS):
        cell = strip[:, variant * px : (variant + 1) * px, 3]
        assert cell[-5:].max() > 120, f"square {variant} does not stand on the ground line"
        assert max(cell[:, 0].max(), cell[:, -1].max()) < 90, f"square {variant} is cut by a side"
        assert cell[0].max() < 90, f"square {variant} is cut by the top"


def test_each_door_has_the_shape_of_the_door_of_the_entity_sheet() -> None:
    # The game keeps the size and the place of a door and changes its
    # picture. A door of another shape would be stretched.
    from ambition_sprite2d_renderer.terrain import doors

    for theme in doors.DOORS:
        image = np.asarray(doors.door(theme))
        assert image.shape == (doors.HEIGHT_PX, doors.WIDTH_PX, 4), theme
        alpha = image[:, :, 3]
        assert alpha[-1].min() == 255, f"{theme}: the step at the foot goes from side to side"
        assert alpha[doors.HEIGHT_PX // 2].min() == 255, f"{theme}: a door has no hole in its middle"
