"""People of the cast in the round (``_round_cast.Round``): each person in
``PEOPLE`` draws in the views they have no art for, inside their
frames, standing where their own rows stand; and a true left view is not the
mirror of the right one (each rests with the two hands doing different
things)."""
from __future__ import annotations

import importlib

import numpy as np
import pytest
from PIL import ImageOps

from ambition_sprite2d_renderer.targets.characters import _person_round as O

PEOPLE = ("anne_druid", "davy_hylbert", "erdish", "galwah", "jeff_hinter", "joseph_furrier", "leib_knives", "m_leblanc", "mami_marzakhani", "marie_curry",
          "neil_ongras_turfson", "paradox_barber", "pipi_tau", "python_goras", "ramen_nujan")


def _round(who):
    """``module`` (its ``ROUND``) or ``module:target`` (its ``ROUNDS[target]``:
    a module of many people, the crypto crew)."""
    module, _, target = who.partition(":")
    m = importlib.import_module(f"ambition_sprite2d_renderer.targets.characters.{module}")
    return m.ROUNDS[target] if target else m.ROUND


def _box(img):
    return img.getchannel("A").point(lambda a: 255 if a > 16 else 0).getbbox()


@pytest.mark.parametrize("who", PEOPLE)
def test_draws_in_the_round_inside_the_frame(who):
    r = _round(who)
    figure = r.figure()
    w, h = figure.frame
    floor = _box(r.body.own_frames()["front_3q"])[3]
    for key in ("side", "back"):
        box = _box(O.draw(r.body.K, figure, O.VIEW_BY_KEY[key]))
        assert box is not None, key
        assert box[0] > 0 and box[1] > 0 and box[2] < w and box[3] < h, (key, box)
        # The person stands where the person's own rows stand.
        assert abs(box[3] - floor) <= 1, (key, box, floor)


@pytest.mark.parametrize("who", PEOPLE)
def test_a_true_left_view_is_not_the_mirror_of_the_right(who):
    r = _round(who)
    figure = r.figure()
    right = O.draw(r.body.K, figure, O.VIEW_BY_KEY["front_3q"])
    left = O.draw(r.body.K, figure, O.VIEW_BY_KEY["front_3q_left"])
    mirrored = np.asarray(ImageOps.mirror(right), float)
    differs = np.abs(np.asarray(left, float) - mirrored).max(axis=-1) > 60.0
    body = np.asarray(right.getchannel("A")) > 16
    # Measured 2026-10-25 (Hylbert): 417 of his 2658 pixels.
    assert differs.sum() > 0.05 * body.sum()
