"""The parallax scenes: what is behind the play in each biome.

A scene has four layers, from the far one to the near one: `sky`,
`far_backplate`, `near_background` and `foreground_atmosphere`. The game
draws each one as a square panel larger than the view, and moves the near
ones more than the far ones when the camera moves.

What the view shows of a panel
------------------------------

A 16:9 view shows only the middle band of a square panel: about `v` 0.27 to
0.73 of the sky, and about 0.32 to 0.68 of the near layer when the camera is
at the middle of the room (0.18 to 0.82 over the full height of a room). A
thing above or below that band is seen only in a taller view. So a scene has
its horizon near `HORIZON`, its sun or moon above it in the band, and plain
ground below.

How a scene stays behind the play
---------------------------------

- A far thing has the colour of the air: each layer is mixed with the sky
  colour of the scene, the far one most.
- No layer has the lightest or the darkest values of the scene's play art in
  a large area, and no layer has small parts with hard contrast.
- The near layer is the darkest one, with a thin light on the edges that
  face the light of the scene.

The art is made here, with `artkit`, and published as PNG files. The game
draws no part of it.
"""

from __future__ import annotations

from typing import Callable

import numpy as np
from PIL import Image

from . import arenas, interiors, outdoors, room_look_sky
from .artkit import Art
from .parts import LAYER_BLUR, LAYER_SIZE

# ---------------------------------------------------------------------------
# The table of scenes
# ---------------------------------------------------------------------------

Scene = Callable[[str, Art], np.ndarray]

SCENES: dict[str, Scene] = {
    "hub": arenas.hub,
    "lab": interiors.lab,
    "basement": interiors.foundry,
    "cave": interiors.cave,
    "cove": outdoors.cove,
    "water": outdoors.water,
    "forest": outdoors.forest,
    "skybridge": outdoors.skybridge,
    "open_sky": outdoors.open_sky,
    "boss": arenas.boss,
    "eclipse": arenas.eclipse,
}


#: Each theme this package publishes: the scenes, and the two states of the
#: sky of the two-state room look, which has its own art.
THEMES: tuple[str, ...] = (*SCENES, *room_look_sky.THEME_KEYS)

LAYERS: tuple[str, ...] = tuple(LAYER_SIZE)


def render(theme_key: str, layer_key: str, size: int | None = None) -> Image.Image:
    """The published picture of one layer of one scene. `size` is for a test
    or a quick look: a scene is the same picture at each size."""
    if theme_key in room_look_sky.THEME_KEYS:
        return room_look_sky.render_look_layer(theme_key, layer_key)
    art = Art(size or LAYER_SIZE[layer_key], theme_key, layer_key)
    layer = SCENES[theme_key](layer_key, art)
    return art.publish(layer, blur=LAYER_BLUR[layer_key], opaque=layer_key == "sky")


#: The panel of each layer as the game draws it: `(panel scale, factor)`
#: (`RUNTIME_PARALLAX_LAYERS` in `ambition_render`).
RUNTIME = {
    "sky": (1.20, 0.10),
    "far_backplate": (1.34, 0.20),
    "near_background": (1.52, 0.42),
    "foreground_atmosphere": (1.72, 0.60),
}


def view(layers: dict[str, Image.Image], size: tuple[int, int] = (1280, 720), camera: tuple[float, float] = (0.0, 0.0)) -> Image.Image:
    """What the game shows of a scene in a view of `size`. `camera` is where
    the camera is in its room: -1 is the left or the top, 1 the right or the
    bottom. This is the arithmetic of `sync_parallax_transform_to_camera`."""
    w, h = size
    out = Image.new("RGBA", size, (0, 0, 0, 255))
    for key, (panel_scale, factor) in RUNTIME.items():
        panel = max(w, h) * panel_scale
        travel = ((panel - w) * 0.5, (panel - h) * 0.5)
        centre = (panel * 0.5 + camera[0] * travel[0] * factor, panel * 0.5 + camera[1] * travel[1] * factor)
        image = layers[key].resize((int(panel), int(panel)), Image.BILINEAR)
        box = (int(centre[0] - w * 0.5), int(centre[1] - h * 0.5))
        out.alpha_composite(image.crop((box[0], box[1], box[0] + w, box[1] + h)))
    return out
