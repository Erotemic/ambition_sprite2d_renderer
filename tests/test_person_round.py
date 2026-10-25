"""People of the cast in the round (``_person_round``): Davy Hylbert, Erdish
and Anne Druid draw in the views they have no art for, inside their frames,
standing where their own rows stand; and a true left view is not the mirror
of the right one (each rests with the two hands doing different things)."""
from __future__ import annotations

import numpy as np
import pytest
from PIL import ImageOps

from ambition_sprite2d_renderer.targets.characters import _person_round as O
from ambition_sprite2d_renderer.targets.characters import anne_druid as A
from ambition_sprite2d_renderer.targets.characters import davy_hylbert as H
from ambition_sprite2d_renderer.targets.characters import erdish as E


def _box(img):
    return img.getchannel("A").point(lambda a: 255 if a > 16 else 0).getbbox()


def _hylbert():
    rows = {name: n for name, n, _ms in H.X.rows}
    return H.K, H.round_figure(), H.X.render_frame("idle", 0, rows["idle"])


def _erdish():
    rows = {name: n for name, n, _ms in E.ROWS}
    return E.K, E.round_figure(), E._render_frame("idle", 0, rows["idle"])


def _anne():
    rows = {name: n for name, n, _ms in A.X.rows}
    return A.K, A.round_figure(), A.X.render_frame("idle", 0, rows["idle"])


PEOPLE = {"anne_druid": _anne, "davy_hylbert": _hylbert, "erdish": _erdish}


@pytest.mark.parametrize("who", sorted(PEOPLE))
def test_draws_in_the_round_inside_the_frame(who):
    K, figure, own = PEOPLE[who]()
    w, h = figure.frame
    floor = _box(own)[3]
    for key in ("side", "back"):
        box = _box(O.draw(K, figure, O.VIEW_BY_KEY[key]))
        assert box is not None, key
        assert box[0] > 0 and box[1] > 0 and box[2] < w and box[3] < h, (key, box)
        # The person stands where the person's own rows stand.
        assert abs(box[3] - floor) <= 1, (key, box, floor)


@pytest.mark.parametrize("who", sorted(PEOPLE))
def test_a_true_left_view_is_not_the_mirror_of_the_right(who):
    K, figure, _own = PEOPLE[who]()
    right = O.draw(K, figure, O.VIEW_BY_KEY["front_3q"])
    left = O.draw(K, figure, O.VIEW_BY_KEY["front_3q_left"])
    mirrored = np.asarray(ImageOps.mirror(right), float)
    differs = np.abs(np.asarray(left, float) - mirrored).max(axis=-1) > 60.0
    body = np.asarray(right.getchannel("A")) > 16
    # Measured 2026-10-25 (Hylbert): 417 of his 2658 pixels.
    assert differs.sum() > 0.05 * body.sum()
