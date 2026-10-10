"""The door of each biome.

A door is a thing of the play: a player goes through it to the next room. Each
biome has a door of its own make (a steel bulkhead in the lab, an iron door in
the foundry, paper screens in the forest), and each one says "door" the same
way, so a player who has seen one knows the others:

- one shape and one size, `WIDTH_PX` by `HEIGHT_PX`, the same as the door of
  the entity sheet (`DOOR_SPRITE_ASPECT` in `ambition_render`): the bottom of
  the picture is the floor;
- a frame all round with a light edge, darker than the leaf inside it;
- a step of the accent colour at the foot;
- one small light or window in the upper part of the leaf.
"""

from __future__ import annotations

from typing import Callable

import numpy as np
from PIL import Image

from .skins import K, Tile, _box, _dot, _line, _mix, _poly

RGB = tuple[int, int, int]

WIDTH_PX = 126
HEIGHT_PX = 242
#: The picture in drawing units (two pixels to the unit).
W = 63
H = 121
#: The frame.
F = 5.0
#: The step at the foot.
STEP = 4.0


def _frame(tile: Tile, c: dict, arch: float = 0.0) -> np.ndarray:
    """Draw the frame and the step. Returns the mask of the leaf: the part
    inside the frame. `arch` more than 0 makes the top round by that much."""
    def outline(p, dx, dy, inset: float):
        top = inset + arch
        _box(p, dx, dy, inset, top, W - inset, H - STEP)
        if arch > 0.0:
            p.ellipse([inset * K + dx, inset * K + dy, (W - inset) * K + dx, (inset + arch * 2.0) * K + dy], fill=255)

    outer = tile.mask(lambda p, dx, dy: outline(p, dx, dy, 0.0))
    inner = tile.mask(lambda p, dx, dy: outline(p, dx, dy, F))
    tile.put(outer, c["frame"])
    tile.put(outer * (1.0 - tile.mask(lambda p, dx, dy: outline(p, dx, dy, 1.0))), c["frame_light"])
    tile.put(inner, c["leaf"])
    # The leaf is set back: the frame throws a shade on its top and left.
    shade = inner * (1.0 - tile.mask(lambda p, dx, dy: outline(p, dx, dy, F + 1.6)))
    tile.put(shade * ((tile.x < W * 0.5) | (tile.y < H * 0.3)), c["dark"], 0.55)
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, -0.0, H - STEP, W, H)), c["accent"])
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, H - STEP, W, H - STEP + 1.0)), _mix(c["accent"], (255, 255, 255), 0.45))
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, H - 1.0, W, H)), c["dark"], 0.5)
    return inner


def _window(tile: Tile, c: dict, x0: float, y0: float, x1: float, y1: float, round_: bool = False) -> None:
    if round_:
        cx, cy, r = (x0 + x1) * 0.5, (y0 + y1) * 0.5, (x1 - x0) * 0.5
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, cx, cy, r + 1.6)), c["frame"])
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, cx, cy, r)), c["glow"])
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, cx - r * 0.3, cy - r * 0.3, r * 0.4)), (255, 255, 255), 0.5)
    else:
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 - 1.4, y0 - 1.4, x1 + 1.4, y1 + 1.4)), c["frame"])
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0, y0, x1, y1)), c["glow"])
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0, y0, x1, y0 + (y1 - y0) * 0.35)), (255, 255, 255), 0.3)


def bulkhead(tile: Tile, c: dict) -> None:
    """Two steel leaves that slide apart."""
    leaf = _frame(tile, c)
    tile.put(leaf * (np.abs(tile.x - W * 0.5) < 0.7), c["dark"])
    tile.put(leaf * (np.abs(tile.x - W * 0.5 + 1.5) < 0.5), c["leaf_light"], 0.6)
    for y in (46.0, 78.0):
        tile.put(leaf * (np.abs(tile.y - y) < 0.6), c["dark"], 0.7)
        tile.put(leaf * (np.abs(tile.y - y - 1.2) < 0.4), c["leaf_light"], 0.45)
    _window(tile, c, 14.0, 18.0, W - 14.0, 30.0)
    stripes = tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, [(F + k * 8.0, H - STEP), (F + k * 8.0 + 4.0, H - STEP), (F + k * 8.0 + 9.0, H - STEP - 8.0), (F + k * 8.0 + 5.0, H - STEP - 8.0)]) for k in range(-1, 8)])
    tile.put(stripes * leaf * (tile.y > H - STEP - 8.0), c["accent"], 0.85)
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, 0.9) for x in (F + 4.0, W - F - 4.0) for y in (38.0, 62.0, 96.0)]), c["leaf_light"], 0.7)


def iron(tile: Tile, c: dict) -> None:
    """An iron door in a round arch, with bands and a grille."""
    leaf = _frame(tile, c, arch=14.0)
    for y in (40.0, 72.0, 100.0):
        band = leaf * (np.abs(tile.y - y) < 2.6)
        tile.put(band, c["frame"])
        tile.put(leaf * (np.abs(tile.y - y + 2.2) < 0.4), c["leaf_light"], 0.5)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, F + 4.0 + k * 7.4, y, 1.0) for k in range(7)]) * leaf, c["leaf_light"], 0.8)
    _window(tile, c, 20.0, 16.0, W - 20.0, 31.0)
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, 24.0 + k * 5.0, 16.0, 25.2 + k * 5.0, 31.0) for k in range(4)]), c["frame"])
    tile.put(tile.mask(lambda p, dx, dy: (_dot(p, dx, dy, W - F - 7.0, 60.0, 2.6), _dot(p, dx, dy, W - F - 7.0, 60.0, 1.2, value=0))), c["accent"])


def plank(tile: Tile, c: dict) -> None:
    """A door of planks in a stone frame, with a lamp over it."""
    leaf = _frame(tile, c, arch=10.0)
    for k in range(1, 6):
        x = F + k * (W - 2 * F) / 6.0
        tile.put(leaf * (np.abs(tile.x - x) < 0.45), c["dark"], 0.8)
        tile.put(leaf * (np.abs(tile.x - x - 0.9) < 0.3), c["leaf_light"], 0.35)
    tile.tone((tile.noise(3, 12, 2) - 0.5) * 0.18 * leaf)
    for y in (34.0, 92.0):
        tile.put(leaf * (np.abs(tile.y - y) < 2.2), c["frame"])
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, F + 4.0 + k * 9.0, y, 0.9) for k in range(6)]) * leaf, c["leaf_light"], 0.8)
    _window(tile, c, 25.0, 46.0, 38.0, 59.0, round_=True)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, W - F - 6.0, 70.0, 1.8)), c["accent"])


def shoji(tile: Tile, c: dict) -> None:
    """Paper screens in a frame of dark wood."""
    leaf = _frame(tile, c)
    tile.put(leaf, c["glow"], 0.92)
    tile.put(leaf * np.clip((tile.y - 20.0) / 90.0, 0.0, 1.0), c["leaf"], 0.35)
    bars = (np.abs(tile.x - W * 0.5) < 1.0).astype(np.float32)
    for k in range(1, 4):
        x = F + k * (W - 2 * F) / 4.0
        bars = np.maximum(bars, (np.abs(tile.x - x) < 0.5).astype(np.float32))
    for k in range(1, 8):
        y = F + k * (H - STEP - F) / 8.0
        bars = np.maximum(bars, (np.abs(tile.y - y) < 0.5).astype(np.float32))
    tile.put(bars * leaf, c["frame"])
    tile.put(leaf * (tile.y > H - STEP - 22.0), c["frame"], 0.85)
    tile.put(leaf * (np.abs(tile.y - (H - STEP - 22.0)) < 0.6), c["frame_light"])
    # A branch in ink on the paper.
    tile.put(tile.mask(lambda p, dx, dy: (_line(p, dx, dy, [(40.0, 78.0), (46.0, 58.0), (43.0, 40.0), (50.0, 26.0)], 0.7), _line(p, dx, dy, [(45.0, 52.0), (52.0, 46.0)], 0.5), _line(p, dx, dy, [(44.0, 40.0), (38.0, 33.0)], 0.5))) * leaf, c["dark"], 0.55)
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, 1.3) for x, y in ((52.0, 45.0), (38.0, 32.0), (50.0, 25.0), (47.0, 57.0))]) * leaf, c["accent"], 0.9)


def cabin(tile: Tile, c: dict) -> None:
    """The door of a ship's cabin: boards, a porthole, a brass plate."""
    leaf = _frame(tile, c)
    for k in range(1, 5):
        x = F + k * (W - 2 * F) / 5.0
        tile.put(leaf * (np.abs(tile.x - x) < 0.45), c["dark"], 0.75)
    tile.tone((tile.noise(3, 12, 2) - 0.5) * 0.16 * leaf)
    _window(tile, c, 21.0, 22.0, 42.0, 43.0, round_=True)
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, 31.5 + 12.6 * np.cos(a), 32.5 + 12.6 * np.sin(a), 0.8) for a in np.linspace(0, 6.28, 9)[:-1]]), c["accent"])
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, F + 3.0, H - STEP - 16.0, W - F - 3.0, H - STEP - 3.0)), c["accent"], 0.8)
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, F + 3.0, H - STEP - 16.0, W - F - 3.0, H - STEP - 15.0)), (255, 255, 255), 0.35)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, W - F - 6.0, 66.0, 2.0)), c["accent"])


def stone(tile: Tile, c: dict) -> None:
    """A door of cut stone in an arch, with a ring of light."""
    leaf = _frame(tile, c, arch=18.0)
    tile.put(leaf * (np.abs(tile.x - W * 0.5) < 0.6), c["dark"], 0.8)
    for y in (52.0, 84.0):
        tile.put(leaf * (np.abs(tile.y - y) < 0.5), c["dark"], 0.6)
        tile.put(leaf * (np.abs(tile.y - y - 1.0) < 0.35), c["leaf_light"], 0.5)
    cx, cy = W * 0.5, 32.0
    d = np.sqrt((tile.x - cx) ** 2 + (tile.y - cy) ** 2)
    tile.put(np.clip(1.0 - np.abs(d - 9.0) / 1.2, 0.0, 1.0) * leaf, c["glow"])
    tile.put(np.clip(1.0 - d / 16.0, 0.0, 1.0) ** 2 * leaf, c["glow"], 0.35)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, cx, cy, 3.0)), c["glow"])
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x - 0.5, 62.0, x + 0.5, 74.0) for x in (cx - 8.0, cx + 8.0)]), c["accent"], 0.8)


Draw = Callable[[Tile, dict], None]


def _colours(frame: RGB, leaf: RGB, dark: RGB, accent: RGB, glow: RGB) -> dict:
    return {
        "frame": frame,
        "frame_light": _mix(frame, (255, 255, 255), 0.4),
        "leaf": leaf,
        "leaf_light": _mix(leaf, (255, 255, 255), 0.35),
        "dark": dark,
        "accent": accent,
        "glow": glow,
    }


#: The door of each theme: how it is drawn, and its colours.
DOORS: dict[str, tuple[Draw, dict]] = {
    "lab": (bulkhead, _colours((40, 58, 78), (74, 104, 126), (12, 20, 32), (236, 178, 70), (130, 236, 224))),
    "hub": (bulkhead, _colours((44, 44, 100), (84, 86, 150), (14, 14, 44), (255, 206, 140), (196, 206, 255))),
    "basement": (iron, _colours((48, 34, 32), (86, 58, 48), (20, 10, 9), (224, 150, 60), (255, 170, 80))),
    "boss": (iron, _colours((40, 12, 20), (96, 32, 44), (16, 4, 8), (220, 70, 60), (255, 120, 76))),
    "cave": (plank, _colours((60, 58, 104), (108, 80, 66), (22, 16, 30), (140, 226, 250), (150, 232, 255))),
    "cove": (cabin, _colours((70, 50, 36), (128, 92, 60), (30, 20, 16), (224, 180, 90), (150, 220, 230))),
    "water": (stone, _colours((30, 80, 100), (58, 124, 140), (8, 30, 46), (150, 240, 200), (170, 250, 220))),
    "forest": (shoji, _colours((58, 36, 26), (150, 140, 110), (26, 16, 12), (214, 70, 60), (244, 236, 208))),
    "skybridge": (stone, _colours((150, 164, 200), (96, 128, 190), (60, 76, 120), (255, 214, 110), (255, 246, 200))),
    "eclipse": (stone, _colours((22, 26, 70), (44, 50, 112), (8, 10, 30), (172, 112, 255), (110, 240, 210))),
}


def door(theme_key: str) -> Image.Image:
    """The door picture of a theme."""
    draw, colours = DOORS[theme_key]
    tile = Tile((W, H), False, False, theme_key, "door")
    draw(tile, colours)
    image = tile.publish()
    assert image.size == (WIDTH_PX, HEIGHT_PX), image.size
    return image
