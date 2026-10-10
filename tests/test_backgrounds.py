"""The parallax scenes keep the contract the game draws them by."""

from __future__ import annotations

import numpy as np
import pytest

from ambition_sprite2d_renderer.backgrounds import scenes

SMALL = 96


@pytest.mark.parametrize("theme", sorted(scenes.SCENES))
def test_a_scene_has_an_opaque_sky_and_layers_the_sky_shows_through(theme: str) -> None:
    # The sky is the last thing behind a room: a hole in it shows the clear
    # colour. Each other layer is in front of it, so a layer with no empty
    # part hides the sky and each layer behind it.
    for layer in scenes.LAYERS:
        image = scenes.render(theme, layer, size=SMALL)
        assert image.size == (SMALL, SMALL)
        alpha = np.asarray(image)[:, :, 3]
        if layer == "sky":
            assert alpha.min() == 255, f"{theme} sky has a hole"
        else:
            assert alpha.max() > 0, f"{theme} {layer} draws nothing"
            assert (alpha < 16).mean() > 0.05, f"{theme} {layer} hides what is behind it"


def test_a_scene_is_the_same_picture_each_time() -> None:
    first = np.asarray(scenes.render("cove", "near_background", size=SMALL))
    second = np.asarray(scenes.render("cove", "near_background", size=SMALL))
    assert (first == second).all()


def test_the_view_shows_the_middle_band_of_each_panel() -> None:
    # A panel that is white only in the band a 16:9 view shows of it at the
    # middle of a room must fill the view, and the same band moved off the
    # middle must not.
    from PIL import Image

    def panel(v0: float, v1: float, size: int = 256) -> Image.Image:
        image = Image.new("RGBA", (size, size), (0, 0, 0, 255))
        image.paste((255, 255, 255, 255), (0, int(v0 * size), size, int(v1 * size)))
        return image

    clear = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    layers = {key: clear for key in scenes.LAYERS}
    layers["sky"] = panel(0.25, 0.75)
    assert np.asarray(scenes.view(layers, (320, 180))).min() == 255
    layers["sky"] = panel(0.0, 0.25)
    assert np.asarray(scenes.view(layers, (320, 180)))[:, :, :3].max() == 0
