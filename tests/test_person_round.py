"""A person of the cast in the round (``_person_round``): Davy Hylbert, the
first, draws in the views he has no art for, inside his frame, and his true
left views are not mirrors of his right ones (he rests with one hand in a
pocket and the other behind his back)."""
from __future__ import annotations

import numpy as np
from PIL import ImageOps

from ambition_sprite2d_renderer.targets.characters import _person_round as O
from ambition_sprite2d_renderer.targets.characters import davy_hylbert as H


def _box(img):
    return img.getchannel("A").point(lambda a: 255 if a > 16 else 0).getbbox()


def test_hylbert_draws_in_the_round_inside_his_frame():
    figure = H.round_figure()
    w, h = H.X.frame
    rows = {name: n for name, n, _ms in H.X.rows}
    own = _box(H.X.render_frame("idle", 0, rows["idle"]))
    for key in ("side", "back"):
        box = _box(O.draw(H.K, figure, O.VIEW_BY_KEY[key]))
        assert box is not None, key
        assert box[0] > 0 and box[1] > 0 and box[2] < w and box[3] < h, (key, box)
        # He stands where his own rows stand.
        assert abs(box[3] - own[3]) <= 1, (key, box, own)


def test_a_true_left_view_is_not_the_mirror_of_the_right():
    figure = H.round_figure()
    right = O.draw(H.K, figure, O.VIEW_BY_KEY["front_3q"])
    left = O.draw(H.K, figure, O.VIEW_BY_KEY["front_3q_left"])
    mirrored = np.asarray(ImageOps.mirror(right), float)
    differs = np.abs(np.asarray(left, float) - mirrored).max(axis=-1) > 60.0
    body = np.asarray(right.getchannel("A")) > 16
    # Measured 2026-10-25: 417 of his 2658 pixels.
    assert differs.sum() > 0.05 * body.sum()
