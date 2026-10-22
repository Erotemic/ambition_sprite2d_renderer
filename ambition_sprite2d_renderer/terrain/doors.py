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

Each door also has its opening (`opening`): a strip of frames in which the
leaf moves into the room behind it, for a body that goes through the door.
"""

from __future__ import annotations

from typing import Callable

import numpy as np
from PIL import Image

from ..core.door_swing import OPENING_FRAMES, SLIDE, SWING, Leaf, Room, opening_frames
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


def bulkhead(tile: Tile, c: dict) -> np.ndarray:
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
    return leaf


def iron(tile: Tile, c: dict) -> np.ndarray:
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
    return leaf


def plank(tile: Tile, c: dict) -> np.ndarray:
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
    return leaf


def shoji(tile: Tile, c: dict) -> np.ndarray:
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
    return leaf


def cabin(tile: Tile, c: dict) -> np.ndarray:
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
    return leaf


def stone(tile: Tile, c: dict) -> np.ndarray:
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
    return leaf


#: A style draws the door on a tile and returns the mask of its leaf.
Draw = Callable[[Tile, dict], np.ndarray]

#: How the leaf of each style opens: one leaf that swings on the left jamb, or
#: two leaves (one on each jamb) that swing or slide.
MOTIONS: dict[Draw, tuple[str, bool]] = {
    bulkhead: (SLIDE, True),
    iron: (SWING, False),
    plank: (SWING, False),
    shoji: (SLIDE, True),
    cabin: (SWING, False),
    stone: (SWING, True),
}


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
    "alarm": (bulkhead, _colours((34, 38, 54), (72, 78, 104), (8, 9, 17), (236, 178, 70), (255, 96, 80))),
    "undertown": (iron, _colours((52, 56, 56), (94, 98, 94), (14, 18, 18), (224, 170, 80), (140, 230, 200))),
    "hub": (bulkhead, _colours((44, 44, 100), (84, 86, 150), (14, 14, 44), (255, 206, 140), (196, 206, 255))),
    "basement": (iron, _colours((48, 34, 32), (86, 58, 48), (20, 10, 9), (224, 150, 60), (255, 170, 80))),
    "boss": (iron, _colours((40, 12, 20), (96, 32, 44), (16, 4, 8), (220, 70, 60), (255, 120, 76))),
    "cave": (plank, _colours((60, 58, 104), (108, 80, 66), (22, 16, 30), (140, 226, 250), (150, 232, 255))),
    "cove": (cabin, _colours((70, 50, 36), (128, 92, 60), (30, 20, 16), (224, 180, 90), (150, 220, 230))),
    "water": (stone, _colours((30, 80, 100), (58, 124, 140), (8, 30, 46), (150, 240, 200), (170, 250, 220))),
    "starlight": (stone, _colours((236, 178, 208), (150, 124, 214), (96, 70, 130), (255, 240, 170), (255, 250, 220))),
    "stardune": (stone, _colours((240, 196, 140), (214, 140, 104), (124, 70, 70), (255, 244, 180), (255, 250, 220))),
    "starless": (iron, _colours((40, 30, 82), (24, 18, 52), (8, 5, 20), (255, 86, 170), (255, 190, 226))),
    "void_castle": (iron, _colours((92, 58, 104), (52, 28, 64), (18, 8, 24), (255, 206, 116), (255, 150, 80))),
    # The Noodly Temple: the door of a kitchen, planks with a round window.
    # The town of the Math dimension: a blue door of planks in a limestone arch.
    "math_town": (plank, _colours((226, 216, 194), (70, 112, 170), (40, 52, 70), (78, 124, 186), (255, 236, 190))),
    "math_undercroft": (plank, _colours((196, 178, 148), (70, 112, 170), (34, 38, 54), (214, 170, 84), (255, 204, 128))),
    # A house door from inside: green plank in a plaster arch.
    "math_interior": (plank, _colours((236, 222, 198), (60, 90, 80), (40, 52, 70), (90, 130, 90), (255, 214, 150))),
    "noodly": (plank, _colours((196, 150, 86), (132, 78, 46), (48, 24, 16), (172, 44, 32), (255, 226, 150))),
    "primeval": (stone, _colours((92, 84, 66), (120, 130, 86), (34, 28, 18), (255, 170, 80), (255, 236, 190))),
    "forest": (shoji, _colours((58, 36, 26), (150, 140, 110), (26, 16, 12), (214, 70, 60), (244, 236, 208))),
    "evil_forest": (iron, _colours((40, 30, 32), (70, 24, 26), (10, 4, 6), (220, 50, 36), (255, 110, 60))),
    "castle_godwin": (iron, _colours((82, 92, 112), (40, 44, 56), (10, 10, 16), (200, 40, 32), (255, 132, 48))),
    "castle_godwin_lab": (iron, _colours((70, 88, 86), (40, 52, 50), (8, 12, 10), (120, 255, 150), (190, 230, 255))),
    "castle_godwin_throne": (iron, _colours((78, 70, 84), (44, 36, 48), (10, 8, 12), (200, 40, 32), (255, 132, 48))),
    "skybridge": (stone, _colours((150, 164, 200), (96, 128, 190), (60, 76, 120), (255, 214, 110), (255, 246, 200))),
    "open_sky": (plank, _colours((176, 164, 150), (150, 112, 74), (84, 70, 70), (255, 214, 110), (255, 246, 200))),
    "eclipse": (stone, _colours((22, 26, 70), (44, 50, 112), (8, 10, 30), (172, 112, 255), (110, 240, 210))),
}


def _drawn(theme_key: str) -> tuple[Tile, np.ndarray, Draw, dict]:
    draw, colours = DOORS[theme_key]
    tile = Tile((W, H), False, False, theme_key, "door")
    leaf = draw(tile, colours)
    return tile, leaf, draw, colours


def door(theme_key: str) -> Image.Image:
    """The door picture of a theme."""
    tile, _, _, _ = _drawn(theme_key)
    image = tile.publish()
    assert image.size == (WIDTH_PX, HEIGHT_PX), image.size
    return image


def opening(theme_key: str) -> Image.Image:
    """The opening of the door of a theme: `OPENING_FRAMES` frames of
    `WIDTH_PX` by `HEIGHT_PX` in one row, from the door picture (frame 0) to
    the open door (`core.door_swing`)."""
    tile, leaf, draw, c = _drawn(theme_key)
    motion, double = MOTIONS[draw]
    left, right, middle = F * K, (W - F) * K, W * 0.5 * K
    if double:
        half = tile.x < W * 0.5
        leaves = [Leaf(leaf * half, left, middle, motion), Leaf(leaf * ~half, right, middle, motion)]
    else:
        leaves = [Leaf(leaf, left, right, motion)]
    room = Room(c["dark"], c["glow"], top=F * K, bottom=(H - STEP) * K)
    strip = Image.new("RGBA", (WIDTH_PX * OPENING_FRAMES, HEIGHT_PX))
    for index, (rgb, alpha) in enumerate(opening_frames(tile.rgb, tile.alpha, leaf, leaves, room)):
        tile.rgb, tile.alpha = rgb, alpha
        strip.paste(tile.publish(), (index * WIDTH_PX, 0))
    return strip
