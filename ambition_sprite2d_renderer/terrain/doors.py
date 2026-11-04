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

import math
from typing import Callable

import numpy as np
from PIL import Image

from .door_swing import OPENING_FRAMES, SLIDE, SWING, Leaf, Room, opening_frames
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


def blast(tile: Tile, c: dict) -> np.ndarray:
    """A steel blast door of the military tower: one heavy leaf on three
    hinges, a raised panel, two ribs across it, a narrow vision slot, a
    lever, the star of the faction stencilled on it, and warning stripes
    (`c["warn"]`, else the accent) at its foot."""
    leaf = _frame(tile, c)
    # Rivets round the frame.
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, 0.6) for x in (2.4, W - 2.4) for y in np.arange(6.0, H - STEP - 2.0, 8.0)]), c["dark"], 0.6)
    # The raised panel: light on its top and left edge, dark on the others.
    x0, y0, x1, y1 = F + 4.0, F + 4.0, W - F - 4.0, H - STEP - 13.0
    panel = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0, y0, x1, y1))
    tile.put(panel, c["leaf_light"], 0.18)
    tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, x0, y0, x1, y0 + 0.8), _box(p, dx, dy, x0, y0, x0 + 0.8, y1))), c["leaf_light"], 0.55)
    tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, x0, y1 - 0.8, x1, y1), _box(p, dx, dy, x1 - 0.8, y0, x1, y1))), c["dark"], 0.55)
    for y in (46.0, 86.0):
        tile.put(leaf * (np.abs(tile.y - y) < 1.8), c["frame"])
        tile.put(leaf * (np.abs(tile.y - y + 1.5) < 0.35), c["frame_light"], 0.6)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, F + 3.0 + k * 6.2, y, 0.65) for k in range(9)]) * leaf, c["leaf_light"], 0.7)
    _window(tile, c, 21.0, 17.0, W - 21.0, 23.0)
    # The star, stencilled: a gap cuts each point from the middle.
    cx, cy, r = W * 0.5, 66.0, 11.0
    corners = [(cx + (r if k % 2 == 0 else r * 0.40) * np.cos(np.radians(-90 + k * 36)), cy + (r if k % 2 == 0 else r * 0.40) * np.sin(np.radians(-90 + k * 36))) for k in range(10)]
    inner = corners[1::2]
    star = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, corners))
    gaps = tile.mask(lambda p, dx, dy: _line(p, dx, dy, inner + inner[:1], 0.7))
    tile.put(star * (1.0 - gaps), _mix(c["leaf"], (232, 228, 212), 0.72))
    # Three hinges on the left jamb and a lever on the right.
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, F - 2.0, y, F + 2.6, y + 7.0) for y in (16.0, 58.0, 98.0)]), c["frame"])
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, F - 2.0, y, F + 2.6, y + 0.8) for y in (16.0, 58.0, 98.0)]), c["frame_light"], 0.7)
    tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, W - F - 6.5, 56.0, W - F - 3.5, 76.0), _dot(p, dx, dy, W - F - 5.0, 58.0, 2.2))), c["frame"])
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, W - F - 6.5, 56.0, W - F - 5.7, 76.0)), c["frame_light"], 0.6)
    warn = c.get("warn", c["accent"])
    stripes = tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, [(F + k * 8.0, H - STEP), (F + k * 8.0 + 4.0, H - STEP), (F + k * 8.0 + 9.0, H - STEP - 8.0), (F + k * 8.0 + 5.0, H - STEP - 8.0)]) for k in range(-1, 8)])
    tile.put(leaf * (tile.y > H - STEP - 8.0), _mix((214, 196, 140), c["dark"], 0.2), 0.9)
    tile.put(stripes * leaf * (tile.y > H - STEP - 8.0), warn, 0.9)
    return leaf


def void_gate(tile: Tile, c: dict) -> np.ndarray:
    """A door of the void: a black leaf in a black frame, a crisp white line
    on the outer edge of the frame and on the edge of the leaf, and a star
    that went out, drawn in a white line, for its light."""
    leaf = _frame(tile, c, arch=14.0)
    # The white line on the edge of the leaf.
    edge = tile.mask(lambda p, dx, dy: (_box(p, dx, dy, F - 0.9, F + 14.0, W - F + 0.9, H - STEP), p.ellipse([(F - 0.9) * K + dx, (F - 0.9) * K + dy, (W - F + 0.9) * K + dx, (F + 28.9) * K + dy], fill=255)))
    tile.put(edge * (1.0 - leaf), c["frame_light"])
    # A seam down the middle of the leaf, grey.
    tile.put(leaf * (np.abs(tile.x - W * 0.5) < 0.35) * (tile.y > 46.0), c["leaf_light"], 0.7)
    # The star: a white line round a black body, with a crack across it.
    cx, cy, r = W * 0.5, 31.0, 9.0
    star = [(cx + (r if k % 2 == 0 else r * 0.44) * math.cos(math.radians(-90.0 + k * 36.0)), cy + (r if k % 2 == 0 else r * 0.44) * math.sin(math.radians(-90.0 + k * 36.0))) for k in range(10)]
    tile.put(tile.mask(lambda p, dx, dy: (_poly(p, dx, dy, star), _line(p, dx, dy, star + star[:1], 1.4))), c["glow"])
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, star)), c["dark"])
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(cx - 6.0, cy - 2.0), (cx - 0.5, cy + 1.0), (cx + 6.5, cy - 1.0)], 0.6)), c["glow"])
    return leaf


def book(tile: Tile, c: dict) -> np.ndarray:
    """A door like the cover of a great book: leather with a border tooled
    in gold, gold corners, a title plate that gives light, and a clasp."""
    leaf = _frame(tile, c)
    x0, y0, x1, y1 = F + 3.0, F + 3.0, W - F - 3.0, H - STEP - 3.0
    border = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0, y0, x1, y1)) * (1.0 - tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 1.0, y0 + 1.0, x1 - 1.0, y1 - 1.0)))
    tile.put(border * leaf, c["accent"], 0.9)
    corners = [[(x, y), (x + sx * 9.0, y), (x, y + sy * 9.0)] for x, y, sx, sy in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1))]
    tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, pts) for pts in corners]) * leaf, c["accent"])
    # The spine side: raised bands across the leaf by the hinge.
    for y in (30.0, 60.0, 90.0):
        tile.put(leaf * (np.abs(tile.y - y) < 1.3) * (tile.x < F + 7.0), c["frame"])
        tile.put(leaf * (np.abs(tile.y - y + 1.0) < 0.35) * (tile.x < F + 7.0), c["frame_light"], 0.7)
    _window(tile, c, 20.0, 20.0, W - 20.0, 32.0)
    # A sun in gold on the cover, and a clasp on the right edge.
    cx, cy = W * 0.5 + 2.0, 62.0
    tile.put(tile.mask(lambda p, dx, dy: (_dot(p, dx, dy, cx, cy, 5.0), [_line(p, dx, dy, [(cx + 6.5 * math.cos(a), cy + 6.5 * math.sin(a)), (cx + 10.0 * math.cos(a), cy + 10.0 * math.sin(a))], 1.0) for a in np.linspace(0.0, math.tau, 13)[:-1]])) * leaf, c["accent"], 0.85)
    tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, W - F - 7.0, 56.0, W - F + 1.5, 66.0), _dot(p, dx, dy, W - F - 7.0, 61.0, 2.0))), c["accent"])
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, W - F - 7.0, 56.0, W - F + 1.5, 57.0)), (255, 255, 255), 0.4)
    return leaf


def organ(tile: Tile, c: dict) -> np.ndarray:
    """A door made of organ pipes of brass in a dark case, the tallest in the
    middle, each with its mouth; a round window of light over them."""
    leaf = _frame(tile, c, arch=14.0)
    tile.put(leaf, c["dark"], 0.5)
    count = 7
    pitch = (W - 2 * F) / count
    for k in range(count):
        x = F + pitch * (k + 0.5)
        top = 44.0 + abs(k - 3) * 7.0
        body = tile.mask(lambda p, dx, dy: (_box(p, dx, dy, x - pitch * 0.38, top, x + pitch * 0.38, H - STEP - 8.0), _poly(p, dx, dy, [(x - pitch * 0.38, H - STEP - 8.0), (x + pitch * 0.38, H - STEP - 8.0), (x + pitch * 0.12, H - STEP), (x - pitch * 0.12, H - STEP)]))) * leaf
        tile.put(body, c["leaf"])
        tile.put(body * (np.abs(tile.x - (x - pitch * 0.18)) < 0.7), c["leaf_light"], 0.7)
        tile.put(body * (tile.x > x + pitch * 0.2), c["dark"], 0.35)
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x - pitch * 0.45, top - 1.2, x + pitch * 0.45, top)) * leaf, c["leaf_light"])
        m = H - STEP - 22.0
        tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(x - pitch * 0.26, m + 4.0), (x + pitch * 0.26, m + 4.0), (x + pitch * 0.26, m), (x, m - 2.4), (x - pitch * 0.26, m)])) * leaf, c["dark"], 0.9)
    tile.put(leaf * (np.abs(tile.x - W * 0.5) < 0.4) * (tile.y > 40.0), c["dark"], 0.8)
    _window(tile, c, 24.0, 18.0, W - 24.0, 33.0, round_=True)
    return leaf


def star_door(tile: Tile, c: dict) -> np.ndarray:
    """A stage door: painted boards, a gold star on it for the one who is on
    tonight, and a lamp in a cage over it."""
    leaf = _frame(tile, c)
    for k in range(1, 4):
        x = F + k * (W - 2 * F) / 4.0
        tile.put(leaf * (np.abs(tile.x - x) < 0.4), c["dark"], 0.6)
    tile.tone((tile.noise(3, 10, 2) - 0.5) * 0.12 * leaf)
    for y0, y1 in ((40.0, 72.0), (80.0, 108.0)):
        tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, F + 5.0, y0, W - F - 5.0, y0 + 0.8), _box(p, dx, dy, F + 5.0, y0, F + 5.8, y1))) * leaf, c["leaf_light"], 0.45)
        tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, F + 5.0, y1 - 0.8, W - F - 5.0, y1), _box(p, dx, dy, W - F - 5.8, y0, W - F - 5.0, y1))) * leaf, c["dark"], 0.5)
    cx, cy, r = W * 0.5, 56.0, 11.0
    star = [(cx + (r if k % 2 == 0 else r * 0.42) * math.cos(math.radians(-90 + k * 36)), cy + (r if k % 2 == 0 else r * 0.42) * math.sin(math.radians(-90 + k * 36))) for k in range(10)]
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(x + 0.8, y + 0.8) for x, y in star])), c["dark"], 0.6)
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, star)), c["accent"])
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [star[9], star[0], star[1], (cx, cy)])), (255, 255, 230), 0.4)
    _window(tile, c, 25.0, 18.0, 38.0, 28.0)
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x - 0.4, 16.6, x + 0.4, 29.4) for x in (29.0, 34.0)]), c["frame"])
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, W - F - 6.0, 92.0, 1.8)), c["accent"])
    return leaf


def pylon(tile: Tile, c: dict) -> np.ndarray:
    """The door of a temple of Egypt: two leaves of wood with columns of
    signs cut in them, a cornice over the frame, and the winged sun over the
    leaves with its disc of light."""
    leaf = _frame(tile, c)
    tile.put(leaf * (np.abs(tile.x - W * 0.5) < 0.6), c["dark"], 0.8)
    # The cornice: a band that leans out over the top of the frame.
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, 0.0, W, 3.4)), c["frame_light"], 0.6)
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, 3.4, W, 4.4)), c["dark"], 0.5)
    # Columns of signs in each leaf.
    rng = tile.rng
    for x in (14.0, 22.0, 41.0, 49.0):
        tile.put(leaf * (np.abs(tile.x - x - 3.6) < 0.3) * (tile.y > 36.0) * (tile.y < 106.0), c["dark"], 0.5)
        signs = [(x + rng.uniform(0.6, 2.6), y) for y in np.arange(40.0, 104.0, 5.0)]
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, sx, sy, sx + rng.choice([1.0, 1.6, 2.4]), sy + rng.choice([1.0, 2.0])) for sx, sy in signs]) * leaf, c["leaf_light"], 0.55)
    # The winged sun: a disc of light and two wings of gold.
    cx, cy = W * 0.5, 22.0
    for side in (-1.0, 1.0):
        wing = [(cx + side * 4.0, cy - 2.0), (cx + side * 22.0, cy - 4.0), (cx + side * 24.0, cy - 1.0), (cx + side * 20.0, cy + 2.6), (cx + side * 4.0, cy + 2.0)]
        tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, wing)), c["accent"])
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(cx + side * (8.0 + k * 3.6), cy - 2.4), (cx + side * (7.0 + k * 3.6), cy + 1.8)], 0.4) for k in range(5)]), c["dark"], 0.45)
    _window(tile, c, cx - 4.0, cy - 4.0, cx + 4.0, cy + 4.0, round_=True)
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, cx + side * 5.4, cy + 3.0, 1.0, ry=1.8) for side in (-1.0, 1.0)]), c["accent"])
    return leaf


def temple(tile: Tile, c: dict) -> np.ndarray:
    """The door of a Greek temple: two leaves of bronze with panels and studs
    between two fluted columns, a lintel with the key pattern, and a small
    round light in the lintel."""
    leaf = _frame(tile, c)
    tile.put(leaf * (np.abs(tile.x - W * 0.5) < 0.6), c["dark"], 0.8)
    # The columns stand on the frame at each side.
    for x0 in (0.0, W - 7.0):
        col = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0, 8.0, x0 + 7.0, H - STEP))
        tile.put(col, c["frame"])
        for k in range(3):
            tile.put(col * (np.abs(tile.x - (x0 + 1.6 + k * 1.9)) < 0.35), c["dark"], 0.35)
        tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, x0 - 0.0, 8.0, x0 + 7.0, 10.0), _box(p, dx, dy, x0, H - STEP - 2.0, x0 + 7.0, H - STEP))), c["frame_light"])
    # The lintel and its key pattern.
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, 0.0, W, 8.0)), c["frame"])
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, 0.0, W, 1.0)), c["frame_light"])

    def key(p, dx, dy, x):
        _line(p, dx, dy, [(x, 6.6), (x, 2.0), (x + 4.4, 2.0), (x + 4.4, 5.0), (x + 1.8, 5.0), (x + 1.8, 3.4), (x + 3.0, 3.4)], 0.7)
        _line(p, dx, dy, [(x, 6.6), (x + 6.0, 6.6)], 0.7)

    tile.put(tile.mask(lambda p, dx, dy: [key(p, dx, dy, 1.5 + k * 6.0) for k in range(10)]), c["accent"])
    # The panels of the bronze leaves, with studs.
    for x0 in (F + 3.0, W * 0.5 + 2.6):
        for y0, y1 in ((16.0, 54.0), (60.0, 108.0)):
            x1 = x0 + W * 0.5 - F - 5.6
            tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, x0, y0, x1, y0 + 0.8), _box(p, dx, dy, x0, y0, x0 + 0.8, y1))) * leaf, c["leaf_light"], 0.6)
            tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, x0, y1 - 0.8, x1, y1), _box(p, dx, dy, x1 - 0.8, y0, x1, y1))) * leaf, c["dark"], 0.5)
            tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, 0.8) for x in (x0 + 3.0, x1 - 3.0) for y in (y0 + 3.0, y1 - 3.0)]) * leaf, c["leaf_light"], 0.8)
    _window(tile, c, W * 0.5 - 4.0, 9.0, W * 0.5 + 4.0, 15.0, round_=True)
    return leaf


def studded(tile: Tile, c: dict) -> np.ndarray:
    """A door of two leaves in lacquer or carved wood, set with rows of
    studs of brass, a ring to knock with on each leaf, and a small window
    of lattice over them."""
    leaf = _frame(tile, c)
    tile.put(leaf * (np.abs(tile.x - W * 0.5) < 0.6), c["dark"], 0.8)
    tile.tone((tile.noise(3, 10, 2) - 0.5) * 0.10 * leaf)
    # A carved band round the frame.
    band = tile.mask(lambda p, dx, dy: _box(p, dx, dy, 1.4, 1.4, W - 1.4, H - STEP)) * (1.0 - tile.mask(lambda p, dx, dy: _box(p, dx, dy, 3.6, 3.6, W - 3.6, H - STEP)))
    tile.put(band * (((tile.x + tile.y) % 3.0) < 1.2), c["dark"], 0.45)
    studs = [(x, y) for x in (F + 5.0, F + 11.0, F + 17.0, W - F - 17.0, W - F - 11.0, W - F - 5.0) for y in np.arange(36.0, 112.0, 9.0)]
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x + 0.4, y + 0.4, 1.4) for x, y in studs]) * leaf, c["dark"], 0.5)
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, 1.3) for x, y in studs]) * leaf, c["accent"])
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x - 0.4, y - 0.4, 0.45) for x, y in studs]) * leaf, (255, 250, 220), 0.6)
    for x in (W * 0.5 - 4.4, W * 0.5 + 4.4):
        tile.put(tile.mask(lambda p, dx, dy: p.ellipse([(x - 2.6) * K + dx, (66.0 - 2.6) * K + dy, (x + 2.6) * K + dx, (66.0 + 2.6) * K + dy], outline=255, width=int(0.8 * K))), c["accent"])
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, x, 63.0, 1.4)), c["accent"])
    _window(tile, c, 20.0, 14.0, W - 20.0, 26.0)
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x - 0.4, 14.0, x + 0.4, 26.0) for x in (25.0, 31.5, 38.0)] + [_box(p, dx, dy, 20.0, y - 0.4, W - 20.0, y + 0.4) for y in (18.0, 22.0)]), c["frame"])
    return leaf


def ger_door(tile: Tile, c: dict) -> np.ndarray:
    """The painted door of a ger: one leaf of orange wood, its border and a
    lattice of the endless knot in blue and white, and a small window over
    it in the frame."""
    leaf = _frame(tile, c)
    x0, y0, x1, y1 = F + 3.0, F + 22.0, W - F - 3.0, H - STEP - 4.0
    border = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0, y0, x1, y1)) * (1.0 - tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 1.4, y0 + 1.4, x1 - 1.4, y1 - 1.4)))
    tile.put(border * leaf, c["accent"])
    # The knot: two sets of bands at a slant that cross in a lattice, each
    # band light in its middle.
    cx, cy = W * 0.5, (y0 + y1) * 0.5
    inner = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 4.0, y0 + 6.0, x1 - 4.0, y1 - 6.0)) * leaf
    d1 = np.abs(((tile.x - cx) + (tile.y - cy)) % 9.0 - 4.5)
    d2 = np.abs(((tile.x - cx) - (tile.y - cy)) % 9.0 - 4.5)
    knot = inner * np.clip(1.2 - np.minimum(d1, d2), 0.0, 1.0)
    tile.put(knot, c["accent"])
    tile.put(inner * np.clip(0.6 - np.minimum(d1, d2), 0.0, 1.0), (240, 236, 220), 0.8)
    # Suns in the corners of the border.
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, 1.6) for x in (x0 + 0.7, x1 - 0.7) for y in (y0 + 0.7, y1 - 0.7)]), (240, 236, 220))
    _window(tile, c, 22.0, 10.0, W - 22.0, 20.0)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, W - F - 6.0, 66.0, 1.8)), c["accent"])
    return leaf


def hide_door(tile: Tile, c: dict) -> np.ndarray:
    """A door of hide stretched on a frame of branches: the hide in pieces
    sewn with sinew, cords that lash it to the frame, and a small round
    smoke hole that the fire inside lights."""
    leaf = _frame(tile, c, arch=16.0)
    tile.tone((tile.noise(4, 8, 3) - 0.5) * 0.22 * leaf)
    # The bark of the branches of the frame.
    frame = 1.0 - tile.mask(lambda p, dx, dy: (_box(p, dx, dy, F, F + 16.0, W - F, H - STEP), p.ellipse([F * K + dx, F * K + dy, (W - F) * K + dx, (F + 32.0) * K + dy], fill=255)))
    tile.put(frame * (np.abs(((tile.x + tile.y * 0.15) % 2.2) - 1.1) < 0.25) * (tile.y < H - STEP), c["dark"], 0.35)
    # The seams: one down the middle and one across, each with its stitches.
    seam_x = [(W * 0.5 + math.sin(y * 0.25) * 0.8, y) for y in np.arange(12.0, H - STEP - 2.0, 3.0)]
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, seam_x, 0.35)) * leaf, c["dark"], 0.6)
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x - 1.0, y - 0.25, x + 1.0, y + 0.25) for x, y in seam_x]) * leaf, c["leaf_light"], 0.7)
    seam_y = [(x, 74.0 + math.sin(x * 0.3) * 0.8) for x in np.arange(F, W - F, 3.0)]
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, seam_y, 0.35)) * leaf, c["dark"], 0.6)
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x - 0.25, y - 1.0, x + 0.25, y + 1.0) for x, y in seam_y]) * leaf, c["leaf_light"], 0.7)
    # Cords that lash the hide to the frame.
    for side in (0.0, 1.0):
        x0 = 1.0 if side == 0.0 else W - 1.0
        x1 = F + 2.6 if side == 0.0 else W - F - 2.6
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x0, y), (x1, y + 1.4)], 0.6) for y in (40.0, 60.0, 80.0, 100.0)]), c["frame_light"], 0.85)
    _window(tile, c, W * 0.5 - 5.0, 26.0, W * 0.5 + 5.0, 36.0, round_=True)
    return leaf


def reed_door(tile: Tile, c: dict) -> np.ndarray:
    """A door of reeds in bundles, side by side in a frame of poles, with
    three bands of cord across them and a small window of open weave."""
    leaf = _frame(tile, c)
    rng = tile.rng
    x = F
    while x < W - F:
        w = rng.uniform(2.2, 3.4)
        tone = rng.uniform(-0.12, 0.10)
        colour = _mix(c["leaf"], c["leaf_light"] if tone > 0 else c["dark"], abs(tone) * 1.8)
        tile.put(leaf * (tile.x >= x) * (tile.x < x + w), colour)
        tile.put(leaf * (np.abs(tile.x - x) < 0.3), c["dark"], 0.55)
        tile.put(leaf * (np.abs(tile.x - x - w * 0.35) < 0.25), c["leaf_light"], 0.35)
        x += w
    for y in (40.0, 70.0, 100.0):
        band = leaf * (np.abs(tile.y - y) < 1.4)
        tile.put(band, c["frame"])
        tile.put(band * (np.abs(((tile.x + tile.y) % 1.6) - 0.8) < 0.25), c["frame_light"], 0.6)
    _window(tile, c, 20.0, 14.0, W - 20.0, 26.0)
    weave = tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x0 - 0.4, 14.0, x0 + 0.4, 26.0) for x0 in (24.0, 28.0, 32.0, 36.0, 40.0)] + [_box(p, dx, dy, 20.0, y0 - 0.4, W - 20.0, y0 + 0.4) for y0 in (18.0, 22.0)])
    tile.put(weave, c["leaf"])
    return leaf


def wattle_door(tile: Tile, c: dict) -> np.ndarray:
    """A door of wattle and daub: upright stakes with withies woven through
    them, and clay pressed over the weave, that has fallen off in places so
    the weave shows."""
    leaf = _frame(tile, c, arch=8.0)
    for k in range(9):
        x = F + 2.0 + k * (W - 2 * F - 4.0) / 8.0
        tile.put(leaf * (np.abs(tile.x - x) < 0.9), c["dark"], 0.55)
    weave = np.abs(((tile.y + 2.0 * np.sin(tile.x * math.pi / 3.3)) % 3.6) - 1.8) < 0.7
    tile.put(leaf * weave, c["leaf_light"], 0.45)
    daub = np.clip((tile.noise(3, 6, 2) - 0.40) * 8.0, 0.0, 1.0)
    tile.put(leaf * daub, c["frame"], 0.85)
    tile.put(leaf * daub * np.clip((tile.noise(10, 18, 2) - 0.5) * 3.0, 0.0, 1.0), c["frame_light"], 0.35)
    _window(tile, c, W * 0.5 - 5.0, 22.0, W * 0.5 + 5.0, 32.0)
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, W * 0.5 + x, 27.0, 0.7) for x in (-2.4, 0.0, 2.4)]), c["accent"], 0.9)
    return leaf


def corbel(tile: Tile, c: dict) -> np.ndarray:
    """A Maya doorway: a frame of limestone whose top closes in steps, a
    corbel arch, over a hanging of woven cloth painted red, with a band of
    glyph blocks across its top and a small lamp in the cloth."""
    leaf = _frame(tile, c)
    # The steps of the corbel arch: each course of stone reaches a little
    # further in than the one under it.
    steps = tile.mask(lambda p, dx, dy: [(_box(p, dx, dy, F, F + k * 4.0, F + (5 - k) * 3.6, F + k * 4.0 + 4.0), _box(p, dx, dy, W - F - (5 - k) * 3.6, F + k * 4.0, W - F, F + k * 4.0 + 4.0)) for k in range(5)])
    tile.put(steps, c["frame"])
    tile.put(steps * tile.mask(lambda p, dx, dy: [_box(p, dx, dy, 0.0, F + k * 4.0 + 3.4, W, F + k * 4.0 + 4.0) for k in range(5)]), c["dark"], 0.45)
    cloth = leaf * (1.0 - steps)
    tile.put(cloth * (np.abs(((tile.x + tile.y * 0.0) % 2.0) - 1.0) < 0.25), c["dark"], 0.18)
    tile.put(cloth * (np.abs((tile.y % 2.4) - 1.2) < 0.2), c["leaf_light"], 0.18)
    for y0 in (44.0, 98.0):
        band = cloth * (tile.y > y0) * (tile.y < y0 + 6.0)
        tile.put(band, c["frame"], 0.9)
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, F + 3.0 + k * 9.0, y0 + 1.2, F + 7.4 + k * 9.0, y0 + 4.8) for k in range(6)]) * band, c["accent"], 0.85)
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, F + 4.0 + k * 9.0, H - STEP - 3.0, 1.2) for k in range(6)]) * leaf, c["frame_light"], 0.8)
    _window(tile, c, W * 0.5 - 4.0, 30.0, W * 0.5 + 4.0, 38.0, round_=True)
    return leaf


def mat_door(tile: Tile, c: dict) -> np.ndarray:
    """A door of plaited pandanus leaf hung in a frame of poles: strips that
    cross over and under in a check, a border of a darker plait, and a
    small round opening."""
    leaf = _frame(tile, c, arch=6.0)
    along = (np.floor(tile.x / 3.0) + np.floor(tile.y / 3.0)) % 2 == 0
    tile.put(leaf * along, c["leaf_light"], 0.35)
    tile.put(leaf * ~along, c["dark"], 0.18)
    tile.put(leaf * (np.abs((tile.x % 3.0) - 1.5) > 1.3), c["dark"], 0.30)
    tile.put(leaf * (np.abs((tile.y % 3.0) - 1.5) > 1.3), c["dark"], 0.30)
    inner = tile.mask(lambda p, dx, dy: _box(p, dx, dy, F + 4.0, F + 10.0, W - F - 4.0, H - STEP - 4.0))
    border = leaf * (1.0 - inner)
    tile.put(border * (np.abs(((tile.x + tile.y) % 2.6) - 1.3) < 0.45), c["accent"], 0.55)
    for y in (40.0, 80.0):
        tile.put(leaf * (np.abs(tile.y - y) < 1.0), c["frame"])
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x, y - 1.6), (x + 1.4, y + 1.6)], 0.5) for x in (F + 2.0, W - F - 3.4)]), c["frame_light"], 0.8)
    _window(tile, c, W * 0.5 - 4.5, 22.0, W * 0.5 + 4.5, 31.0, round_=True)
    return leaf


def benin_door(tile: Tile, c: dict) -> np.ndarray:
    """A door of Benin: one leaf of dark carved wood set in a wall of red
    earth. The wall has horizontal ridges. The leaf has a carved band of
    interlace down its middle, a panel on each side of it, rows of brass
    studs along its edges and a ring of brass to pull it."""
    leaf = _frame(tile, c)
    wall = (1.0 - leaf) * (tile.y < H - STEP)
    course = (tile.y % 7.0) / 7.0
    tile.put(wall * np.clip(1.0 - np.abs(course - 0.12) / 0.10, 0.0, 1.0), c["frame_light"], 0.45)
    tile.put(wall * np.clip(1.0 - np.abs(course - 0.92) / 0.08, 0.0, 1.0), c["dark"], 0.40)
    tile.tone((tile.noise(3, 10, 2) - 0.5) * 0.12 * leaf)
    # The grain of the wood, and the two panels in low relief.
    tile.put(leaf * (np.abs(((tile.x + (tile.noise(2, 8, 2) - 0.5) * 3.0) % 2.2) - 1.1) < 0.12), c["dark"], 0.25)
    for x0, x1 in ((F + 6.0, W * 0.5 - 6.0), (W * 0.5 + 6.0, W - F - 6.0)):
        panel = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0, 34.0, x1, 104.0))
        tile.put(panel * (1.0 - tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 1.0, 35.0, x1, 104.0))), c["dark"], 0.6)
        tile.put(panel * (1.0 - tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0, 34.0, x1 - 1.0, 103.0))), c["leaf_light"], 0.4)
    # The band of interlace: two cords that cross over and under, as on
    # the carved doors and the brass of the court.
    xs = W * 0.5
    t = np.linspace(30.0, 110.0, 120)
    for phase in (0.0, math.pi):
        pts = [(xs + 3.2 * math.sin(y * 0.42 + phase), y) for y in t]
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, pts, 1.1)) * leaf, c["leaf_light"], 0.75)
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(x + 0.4, y + 0.4) for x, y in pts], 0.4)) * leaf, c["dark"], 0.55)
    # The brass studs along the edges, and the ring.
    studs = [(x, y) for x in (F + 3.0, W - F - 3.0) for y in np.arange(14.0, 114.0, 8.0)] + [(x, y) for x in np.arange(F + 9.0, W - F - 6.0, 8.0) for y in (14.0, 112.0)]
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x + 0.4, y + 0.4, 1.3) for x, y in studs]) * leaf, c["dark"], 0.5)
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, 1.2) for x, y in studs]) * leaf, c["accent"])
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x - 0.35, y - 0.35, 0.4) for x, y in studs]) * leaf, (255, 250, 220), 0.6)
    x, y = W * 0.5 + 9.0, 70.0
    tile.put(tile.mask(lambda p, dx, dy: p.ellipse([(x - 3.0) * K + dx, (y - 3.0) * K + dy, (x + 3.0) * K + dx, (y + 3.0) * K + dy], outline=255, width=int(0.9 * K))), c["accent"])
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, x, y - 3.0, 1.3)), c["accent"])
    _window(tile, c, W * 0.5 - 6.0, 18.0, W * 0.5 + 6.0, 26.0)
    return leaf


def saint_domingue_door(tile: Tile, c: dict) -> np.ndarray:
    """A door of the north plain of Saint-Domingue: a leaf of upright
    planks in a wall of stone washed white with lime, under an eave of
    thatch. Two battens and a brace hold the planks together, two iron strap
    hinges hold the leaf, and a small square opening lets in the light. The
    lime has worn off the wall in places, so the stone shows. The eave
    stays in front of the door when it opens, so it is not part of the
    leaf."""
    leaf = _frame(tile, c)
    wall = (1.0 - leaf) * (tile.y < H - STEP)
    worn = np.clip((tile.noise(4, 8, 3) - 0.62) * 6.0, 0.0, 1.0)
    tile.put(wall * worn, _mix(c["frame"], (150, 130, 104), 0.55), 0.8)
    tile.tone((tile.noise(8, 16, 2) - 0.5) * 0.10 * wall)
    # The planks: upright boards with dark gaps between them and the grain
    # along them.
    tile.tone((tile.noise(2, 14, 2) - 0.5) * 0.24 * leaf)
    for k in range(1, 5):
        x = F + k * (W - 2 * F) / 5.0
        tile.put(leaf * (np.abs(tile.x - x) < 0.5), c["dark"], 0.85)
        tile.put(leaf * (np.abs(tile.x - x - 1.0) < 0.35), c["leaf_light"], 0.30)
    grain = np.abs(((tile.x + (tile.noise(3, 10, 2) - 0.5) * 2.6) % 2.6) - 1.3) < 0.12
    tile.put(leaf * grain, c["dark"], 0.22)
    # The two battens and the brace between them.
    battens = tile.mask(lambda p, dx, dy: [_box(p, dx, dy, F + 2.0, y, W - F - 2.0, y + 5.0) for y in (36.0, 92.0)])
    brace = tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(F + 6.0, 90.0), (W - F - 6.0, 43.0)], 2.2))
    for part in (brace * (1.0 - battens), battens):
        tile.put(part * leaf, c["leaf"])
        tile.put(part * leaf * np.clip((tile.noise(2, 10, 2) - 0.5) * 2.0 + 0.5, 0.0, 1.0), c["leaf_light"], 0.20)
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, F + 2.0, y + 4.2, W - F - 2.0, y + 5.0) for y in (36.0, 92.0)]) * leaf, c["dark"], 0.65)
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, F + 2.0, y, W - F - 2.0, y + 0.7) for y in (36.0, 92.0)]) * leaf, c["leaf_light"], 0.55)
    # The strap hinges of black iron on the left, with their nails, and a
    # latch on the right.
    iron = (46, 42, 44)
    tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, [(F, y + 0.6), (F + 26.0, y + 1.6), (F + 26.0, y + 3.4), (F, y + 4.4)]) for y in (36.0, 92.0)]), iron)
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, F + 6.0 + k * 6.5, y + 2.5, 0.6) for k in range(4) for y in (36.0, 92.0)]), (120, 116, 118), 0.8)
    tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, W - F - 12.0, 66.0, W - F - 3.0, 67.4), _dot(p, dx, dy, W - F - 4.0, 70.0, 1.4))), iron)
    _window(tile, c, W * 0.5 - 5.5, 22.0, W * 0.5 + 5.5, 31.0)
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, W * 0.5 - 0.5, 22.0, W * 0.5 + 0.5, 31.0)), c["leaf"], 0.9)
    # The eave of thatch over the door: a thick band of grass laid in bundles
    # whose ends hang in a ragged line, with the shade it casts on the wall.
    rng = tile.rng
    edge = [(x, 13.0 + rng.uniform(-1.4, 1.4)) for x in np.linspace(0.0, W, 22)]
    eave = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(0.0, 0.0), (W, 0.0)] + edge[::-1]))
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(0.0, 0.0), (W, 0.0)] + [(x, y + 3.0) for x, y in edge[::-1]]), blur=1.2) * (1.0 - eave), (0, 0, 0), 0.35)
    tile.put(eave, c["thatch"])
    strands = [(rng.uniform(0.0, W), rng.uniform(1.0, 9.0), rng.uniform(-0.8, 0.8)) for _ in range(70)]
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x, y0), (x + lean, y0 + 5.0)], 0.22) for x, y0, lean in strands]) * eave, _mix(c["thatch"], c["dark"], 0.45), 0.7)
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x + 0.4, y0), (x + 0.4 + lean, y0 + 4.0)], 0.18) for x, y0, lean in strands[::2]]) * eave,
             _mix(c["thatch"], (255, 240, 200), 0.4), 0.6)
    tile.put(eave * (tile.y < 1.2), _mix(c["thatch"], (255, 240, 200), 0.3), 0.6)
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(0.0, 5.0), (W, 4.4)], 0.6)) * eave, _mix(c["thatch"], c["dark"], 0.6), 0.6)
    return leaf * (1.0 - eave)


def gold_coast_door(tile: Tile, c: dict) -> np.ndarray:
    """The Door of No Return of a fort on the Gold Coast: a narrow, low
    doorway through a very thick wall of stone washed white with lime. It
    has no ornament. The thickness of the wall shows in the doorway: its
    left side catches the light, and the underside of the lintel is in
    shade. Inside, the passage is dark. At its far end a small, narrow
    opening shows the bright sea light beyond: pale sky, the grey-green sea
    and a white line of surf. That far light is the one light of this door.
    The lime has worn off the wall in places, so the grey stone shows."""
    _frame(tile, c)
    # The wall round the doorway: thick jambs and a deep lintel make the
    # opening narrow and low.
    jamb, lintel, reveal = 6.0, 22.0, 3.4
    x0, x1, y0, y1 = F + jamb, W - F - jamb, lintel, H - STEP
    wall = (1.0 - tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0, y0, x1, y1))) * (tile.y < H - STEP)
    inner = tile.mask(lambda p, dx, dy: _box(p, dx, dy, F, F, W - F, H - STEP))
    tile.put(wall * inner, c["frame"])
    tile.tone((tile.noise(6, 12, 3) - 0.5) * 0.08 * wall)
    worn = np.clip((tile.noise(4, 8, 3) - 0.60) * 6.0, 0.0, 1.0) * wall
    tile.put(worn, c["stone"], 0.75)
    tile.put(worn * (np.abs(((tile.y + (tile.noise(3, 3, 2) - 0.5) * 3.0) % 6.0) - 3.0) < 0.35), c["dark"], 0.35)
    # The thickness of the wall: the left side of the doorway, lit, and the
    # underside of the lintel, in shade. Both go in toward the far end.
    side = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(x0, y0), (x0 + reveal, y0 + reveal), (x0 + reveal, y1), (x0, y1)]))
    soffit = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(x0, y0), (x1, y0), (x1, y0 + reveal), (x0 + reveal, y0 + reveal)]))
    tile.put(side, _mix(c["frame"], c["dark"], 0.22))
    tile.put(side * np.clip((tile.y - y0) / (y1 - y0), 0.0, 1.0), c["glow"], 0.20)
    tile.put(soffit, _mix(c["frame"], c["dark"], 0.55))
    # The passage: dark, darkest at its top.
    leaf = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + reveal, y0 + reveal, x1, y1))
    tile.put(leaf, c["leaf"])
    tile.put(leaf * np.clip(1.0 - (tile.y - y0) / 40.0, 0.0, 1.0), c["dark"], 0.7)
    # The far opening at the end of the passage, and the sea light in it.
    fx0, fx1, fy0, fy1 = 27.0, 35.0, 52.0, 101.0
    far = tile.mask(lambda p, dx, dy: _box(p, dx, dy, fx0, fy0, fx1, fy1))
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, fx0 - 3.0, fy0 - 3.0, fx1 + 3.0, fy1 + 2.0), blur=3.0) * leaf, c["glow"], 0.22)
    sea_y = fy0 + (fy1 - fy0) * 0.58
    tile.put(far * (tile.y < sea_y), c["sky"])
    tile.put(far * (tile.y >= sea_y), c["sea"])
    tile.put(far * np.clip((tile.y - sea_y) / (fy1 - sea_y), 0.0, 1.0), c["leaf"], 0.35)
    tile.put(far * (np.abs(tile.y - sea_y - 5.0) < 0.6), c["sky"], 0.9)
    tile.put(far * (np.abs(tile.y - sea_y - 9.0) < 0.4), c["sky"], 0.6)
    # The far light on the floor of the passage: a faint path to the near
    # threshold.
    floor = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(fx0, fy1), (fx1, fy1), (x1 - 3.0, y1), (x0 + reveal + 4.0, y1)]))
    tile.put(floor * leaf * np.clip((tile.y - fy1) / (y1 - fy1), 0.0, 1.0) ** 0.5, c["glow"], 0.10)
    return leaf


def _fieldstones(tile: Tile, c: dict, mask: np.ndarray, count: int, light: float) -> None:
    """Stones laid dry, of each size and tone, over `mask`: dark gaps
    between them and a lit top on each one. The stones are in the colours
    `frame` and `frame_light`."""
    rng = tile.rng
    d1 = np.full(tile.alpha.shape, 1e9, dtype=np.float32)
    d2 = np.full(tile.alpha.shape, 1e9, dtype=np.float32)
    tone = np.zeros_like(d1)
    for _ in range(count):
        px, py, t = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(-0.18, 0.16)
        d = np.sqrt((tile.x - px) ** 2 + ((tile.y - py) * 1.5) ** 2)
        closer = d < d1
        d2 = np.where(closer, d1, np.minimum(d2, d))
        tone = np.where(closer, t, tone)
        d1 = np.where(closer, d, d1)
    tile.put(mask, c["frame"])
    tile.rgb = np.clip(tile.rgb * (1.0 + (tone * mask)[:, :, None]), 0.0, 255.0)
    tile.put(mask * np.clip(1.0 - (d2 - d1 - 0.3) / 1.0, 0.0, 1.0), c["dark"], 0.85)
    tile.put(mask * np.clip(1.0 - np.abs((d2 - d1) - 1.8) / 0.6, 0.0, 1.0) * (tile.noise(12, 24, 1) > 0.45), c["frame_light"], light)


def andes_door(tile: Tile, c: dict) -> np.ndarray:
    """A door of a round house of the high Andes: a low doorway in a wall of
    fieldstones laid dry, under a heavy lintel of one long flat stone and
    an eave of thick ichu thatch. A mat of ichu grass, twined in bundles
    with cord, hangs in the doorway as its leaf; a small gap in the mat
    shows the light of the hearth. The doorway is low, so a person bends
    to go in, and the cold stays out."""
    _frame(tile, c)
    rng = tile.rng
    lintel_top, lintel_bottom = 30.0, 38.0
    inner = tile.mask(lambda p, dx, dy: _box(p, dx, dy, F, F, W - F, H - STEP))
    jambs = tile.mask(lambda p, dx, dy: (_box(p, dx, dy, F, F, F + 5.0, H - STEP), _box(p, dx, dy, W - F - 5.0, F, W - F, H - STEP)))
    wall = np.clip(inner * (tile.y < lintel_top) + jambs, 0.0, 1.0)
    outer = tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, 0.0, W, H - STEP))
    _fieldstones(tile, c, np.clip(wall + outer * (1.0 - inner), 0.0, 1.0), 46, 0.5)
    # The lintel: one long flat stone over the doorway.
    lintel = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(F - 1.0, lintel_top + 0.6), (W - F + 1.0, lintel_top), (W - F + 1.4, lintel_bottom), (F - 1.4, lintel_bottom + 0.4)]))
    tile.put(lintel, _mix(c["frame"], c["frame_light"], 0.3))
    tile.tone((tile.noise(10, 3, 2) - 0.5) * 0.18 * lintel)
    tile.put(lintel * (tile.y < lintel_top + 1.4), c["frame_light"], 0.6)
    tile.put(lintel * (tile.y > lintel_bottom - 1.2), c["dark"], 0.5)
    # The mat: horizontal bundles of grass, each twined with a cord, and
    # the ends of the grass that hang at its two sides.
    leaf = tile.mask(lambda p, dx, dy: _box(p, dx, dy, F + 5.0, lintel_bottom, W - F - 5.0, H - STEP))
    tile.put(leaf, c["leaf"])
    # Each bundle is round, so its middle is lit, and the line between two
    # bundles waves a little. Fine straws run along each bundle.
    row = (tile.y - lintel_bottom + (tile.noise(6, 3, 2) - 0.5) * 2.0) % 5.0
    tile.put(leaf * np.clip(1.0 - np.abs(row - 2.3) / 2.5, 0.0, 1.0) ** 1.5, c["leaf_light"], 0.40)
    tile.put(leaf * np.clip((row - 4.2) / 0.8, 0.0, 1.0), c["dark"], 0.45)
    straws = np.abs(((tile.y + (tile.noise(20, 4, 2) - 0.5) * 1.6) % 0.9) - 0.45) < 0.08
    tile.put(leaf * straws, c["dark"], 0.18)
    cord = _mix(c["leaf"], c["dark"], 0.55)
    tile.tone((tile.noise(5, 24, 2) - 0.5) * 0.25 * leaf)
    for x in (F + 12.0, W * 0.5, W - F - 12.0):
        tile.put(leaf * tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x - 0.8, lintel_bottom + k * 5.0 + 1.0), (x + 0.8, lintel_bottom + k * 5.0 + 4.0)], 0.5)
                                                     for k in range(16)]), cord, 0.9)
    tile.put(leaf * tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x, lintel_bottom), (x, H - STEP)], 0.4) for x in (F + 12.0, W * 0.5, W - F - 12.0)]), cord, 0.6)
    # The loose ends of the grass at the two sides of the mat.
    ends = [(x0 + rng.uniform(-0.6, 0.6), lintel_bottom + k * 2.5 + rng.uniform(0.0, 1.5)) for k in range(30) for x0 in (F + 5.5, W - F - 5.5)]
    tile.put(leaf * tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x, y), (x + (1.2 if x < W * 0.5 else -1.2), y + 1.4)], 0.25) for x, y in ends]), c["leaf_light"], 0.6)
    # The gap in the mat, and the light of the hearth in it.
    _window(tile, {**c, "frame": c["leaf"]}, W * 0.5 - 4.0, 46.0, W * 0.5 + 4.0, 52.0)
    # The eave of thatch over the wall: thick bundles of ichu with ragged
    # ends, and the shade it casts.
    edge = [(x, 15.0 + rng.uniform(-1.6, 1.6)) for x in np.linspace(0.0, W, 26)]
    eave = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(0.0, 0.0), (W, 0.0)] + edge[::-1]))
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(0.0, 0.0), (W, 0.0)] + [(x, y + 3.0) for x, y in edge[::-1]]), blur=1.2) * (1.0 - eave), (0, 0, 0), 0.35)
    tile.put(eave, c["thatch"])
    strands = [(rng.uniform(0.0, W), rng.uniform(0.0, 10.0), rng.uniform(-0.8, 0.8)) for _ in range(90)]
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x, y0), (x + lean, y0 + 6.0)], 0.22) for x, y0, lean in strands]) * eave, _mix(c["thatch"], c["dark"], 0.45), 0.7)
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x + 0.4, y0), (x + 0.4 + lean, y0 + 5.0)], 0.18) for x, y0, lean in strands[::2]]) * eave,
             _mix(c["thatch"], (255, 244, 210), 0.45), 0.6)
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(0.0, 6.0), (W, 5.4)], 0.6)) * eave, _mix(c["thatch"], c["dark"], 0.6), 0.6)
    return leaf


def caral_door(tile: Tile, c: dict) -> np.ndarray:
    """A doorway of Caral, at the top of a stair of a platform: a wide
    opening in a wall of grey-tan stones laid in clay, with jambs and a
    lintel of big dressed stones. A plain cloth of cotton hangs in it as
    its leaf, white with two bands of natural brown cotton woven in. Three
    steps of stone go up to the doorway, and the cloth hangs over the top
    one. A small square gap at the top of the cloth lets out the light."""
    _frame(tile, c)
    inner = tile.mask(lambda p, dx, dy: _box(p, dx, dy, F, F, W - F, H - STEP))
    # The wall round the doorway: courses of stones in clay.
    wall = tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, 0.0, W, H - STEP)) * (1.0 - inner)
    rng = tile.rng
    tile.put(wall, c["clay"])
    y0 = 0.0
    while y0 < H - STEP:
        row_h = rng.choice((5.0, 7.0, 4.0))
        x = -rng.uniform(0.0, 6.0)
        while x < W:
            w = rng.uniform(4.0, 9.0)
            tone = rng.uniform(-0.14, 0.12)
            colour = _mix(c["frame"], c["frame_light"] if tone > 0 else c["dark"], abs(tone) * 1.4)
            stone = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x + 0.5, y0 + 0.5, x + w - 0.5, y0 + row_h - 0.5)) * wall
            tile.put(stone, colour)
            tile.put(stone * (tile.y < y0 + 1.2), c["frame_light"], 0.35)
            x += w
        y0 += row_h
    # The jambs and the lintel: big stones, dressed flat.
    big = tile.mask(lambda p, dx, dy: (_box(p, dx, dy, F, F, F + 7.0, H - STEP), _box(p, dx, dy, W - F - 7.0, F, W - F, H - STEP), _box(p, dx, dy, F, F, W - F, F + 9.0)))
    tile.put(big, _mix(c["frame"], c["frame_light"], 0.25))
    tile.tone((tile.noise(6, 14, 2) - 0.5) * 0.16 * big)
    for y in (36.0, 70.0):
        tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, F, y, F + 7.0, y + 0.6), _box(p, dx, dy, W - F - 7.0, y, W - F, y + 0.6))), c["dark"], 0.6)
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, F, F + 8.4, W - F, F + 9.0)), c["dark"], 0.6)
    tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, F + 6.4, F + 9.0, F + 7.0, H - STEP), _box(p, dx, dy, F, F, W - F, F + 0.7))), c["frame_light"], 0.5)
    # The three steps up to the doorway: a lit tread and a riser in shade
    # on each one.
    x0, x1 = F + 7.0, W - F - 7.0
    for k in range(3):
        top = H - STEP - (k + 1) * 4.0
        step = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + k * 1.2, top, x1 - k * 1.2, top + 4.0))
        tile.put(step, _mix(c["frame"], c["dark"], 0.30))
        tile.put(step * (tile.y < top + 1.4), _mix(c["frame_light"], (255, 250, 236), 0.3), 0.9)
        tile.put(step * (tile.y > top + 3.4), c["dark"], 0.55)
    # The cloth: plain weave of white cotton, soft folds, and two bands of
    # brown cotton across it.
    leaf = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0, F + 9.0, x1, H - STEP - 12.0))
    tile.put(leaf, c["leaf"])
    folds = 0.5 + 0.5 * np.sin((tile.x - x0) * np.pi / 4.2)
    tile.put(leaf * folds, c["dark"], 0.16)
    tile.put(leaf * (1.0 - folds) * (tile.noise(3, 10, 2) > 0.4), c["leaf_light"], 0.35)
    weave = (np.abs((tile.x % 1.2) - 0.6) < 0.12) | (np.abs((tile.y % 1.2) - 0.6) < 0.12)
    tile.put(leaf * weave, c["dark"], 0.08)
    for y in (58.0, 90.0):
        band = leaf * (np.abs(tile.y - y) < 2.4)
        tile.put(band, c["band"])
        tile.put(band * (np.abs(((tile.x + tile.y) % 3.0) - 1.5) < 0.4), c["leaf"], 0.35)
        tile.put(band * folds, c["dark"], 0.20)
    tile.put(leaf * (tile.y > H - STEP - 13.0), c["dark"], 0.4)
    _window(tile, {**c, "frame": c["band"]}, W * 0.5 - 4.0, 22.0, W * 0.5 + 4.0, 29.0)
    return leaf


def _hand_stencil(tile: Tile, c: dict, cx: float, cy: float, size: float, turn: float) -> None:
    """A hand stencil, as the first painters made them on the walls of
    the caves: a person put a hand on the rock and blew red ochre round
    it. So the hand is the bare rock, and a soft cloud of red is round it."""
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, cx, cy, size * 1.25, ry=size * 1.45), blur=size * 0.35), c["ochre"], 0.75)
    ct, st = math.cos(turn), math.sin(turn)

    def at(x: float, y: float) -> tuple[float, float]:
        return (cx + (x * ct - y * st) * size, cy + (x * st + y * ct) * size)

    fingers = [((-0.42, -0.30), (-0.62, -0.95)), ((-0.16, -0.40), (-0.20, -1.20)), ((0.10, -0.40), (0.16, -1.25)), ((0.34, -0.32), (0.48, -1.05)),
               ((0.40, 0.10), (0.95, -0.30))]
    hand = tile.mask(lambda p, dx, dy: (p.ellipse([(cx - size * 0.45) * K + dx, (cy - size * 0.40) * K + dy, (cx + size * 0.45) * K + dx, (cy + size * 0.55) * K + dy], fill=255),
                                         _poly(p, dx, dy, [at(-0.30, 0.40), at(0.30, 0.40), at(0.24, 1.0), at(-0.24, 1.0)]),
                                         [_line(p, dx, dy, [at(*a), at(*b)], size * 0.22) for a, b in fingers]))
    tile.put(hand, c["frame"])
    tile.put(hand * (tile.noise(14, 24, 2) > 0.55), c["frame_light"], 0.35)


def wallacea_door(tile: Tile, c: dict) -> np.ndarray:
    """The mouth of a cave in the limestone karst of Sulawesi. The rock is
    pale grey, cut by the rain into flutes and pits, with moss on its top.
    A hand stencil in red ochre is on the rock beside the mouth, as on the
    walls of the caves of Maros. A screen of plaited palm leaf hangs in
    the mouth as its leaf; a gap in the plait shows the light of a fire."""
    inner = _frame(tile, c)
    rng = tile.rng
    floor = H - STEP
    # The mouth: an uneven arch, wide at its foot.
    left = [(11.0 + rng.uniform(-1.0, 1.0) + 4.0 * (k / 8.0) ** 2, floor - k * (floor - 46.0) / 8.0) for k in range(9)]
    right = [(W - 11.0 + rng.uniform(-1.0, 1.0) - 3.0 * (k / 8.0) ** 2, floor - k * (floor - 50.0) / 8.0) for k in range(9)]
    arch = [(W * 0.5 + 17.0 * math.cos(a) + rng.uniform(-0.8, 0.8), 46.0 - 24.0 * math.sin(a) + rng.uniform(-0.8, 0.8)) for a in np.linspace(math.pi * 0.06, math.pi * 0.94, 11)]
    mouth_pts = left + arch[::-1] + right[::-1]
    mouth = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, mouth_pts))
    rock = tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, 0.0, W, floor)) * (1.0 - mouth)
    # The rock: pale limestone, with upright flutes, dark streaks of
    # water, pits and cracks.
    tile.put(rock, c["frame"])
    tile.tone((tile.noise(5, 10, 3) - 0.5) * 0.20 * rock)
    phase = tile.x * 2.0 * math.pi / 4.2 + (tile.noise(3, 6, 2) - 0.5) * 5.0
    tile.put(rock * np.clip(-np.cos(phase) - 0.6, 0, 1) * 2.4, c["dark"], 0.30)
    tile.put(rock * np.clip(np.sin(phase) - 0.7, 0, 1) * 3.0, c["frame_light"], 0.55)
    tile.put(rock * np.clip((tile.noise(12, 3, 2) - 0.62) * 5.0, 0, 1), _mix(c["frame"], c["dark"], 0.45), 0.5)
    pits = [(rng.uniform(1.0, W - 1.0), rng.uniform(4.0, floor - 2.0), rng.uniform(0.5, 1.2)) for _ in range(26)]
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, r, ry=r * 0.75) for x, y, r in pits]) * rock, c["dark"], 0.7)
    # The rock is in shade at the rim of the mouth.
    rim = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, mouth_pts), blur=1.6)
    tile.put(rock * np.clip(rim * 2.0, 0, 1), c["dark"], 0.45)
    # Moss along the top of the rock.
    moss = [(x, rng.uniform(0.5, 3.0), rng.uniform(2.0, 4.4)) for x in np.linspace(0.0, W, 14)]
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, r, ry=r * 0.6) for x, y, r in moss]), c["moss"])
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x - r * 0.2, y - r * 0.3, r * 0.5, ry=r * 0.25) for x, y, r in moss]), _mix(c["moss"], (220, 240, 160), 0.35), 0.8)
    _hand_stencil(tile, c, 9.5, 24.0, 4.2, -0.25)
    _hand_stencil(tile, c, W - 8.5, 34.0, 3.4, 0.30)
    # The screen: strips of palm leaf plaited in a check, hung from a
    # pole across the mouth, with a border of a darker plait.
    leaf = inner * mouth
    tile.put(leaf, c["leaf"])
    along = (np.floor(tile.x / 2.6) + np.floor(tile.y / 2.6)) % 2 == 0
    tile.put(leaf * along, c["leaf_light"], 0.35)
    tile.put(leaf * ~along, c["dark"], 0.16)
    tile.put(leaf * (np.abs((tile.x % 2.6) - 1.3) > 1.1), c["dark"], 0.30)
    tile.put(leaf * (np.abs((tile.y % 2.6) - 1.3) > 1.1), c["dark"], 0.30)
    # The border: the screen less a copy of it a little smaller.
    edge = leaf * (1.0 - np.clip(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(W * 0.5 + (x - W * 0.5) * 0.86, 46.0 + (y - 46.0) * 0.9 + 1.0) for x, y in mouth_pts])), 0, 1))
    tile.put(edge * (np.abs(((tile.x + tile.y) % 2.4) - 1.2) < 0.45), c["accent"], 0.45)
    for y in (58.0, 90.0):
        tile.put(leaf * (np.abs(tile.y - y) < 0.8), c["dark"], 0.55)
    tile.put(leaf * np.clip(1.0 - (tile.y - 22.0) / 18.0, 0, 1), c["dark"], 0.45)
    pole = tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(14.0, 36.0), (W - 14.0, 35.0)], 1.8))
    tile.put(pole, c["wood"])
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(14.0, 35.4), (W - 14.0, 34.4)], 0.5)), _mix(c["wood"], (255, 240, 210), 0.35), 0.8)
    _window(tile, {**c, "frame": c["wood"]}, W * 0.5 - 3.5, 46.0, W * 0.5 + 3.5, 53.0, round_=True)
    return leaf * (1.0 - pole)


def _thatch_eave(tile: Tile, c: dict, depth: float, lift: float) -> np.ndarray:
    """An eave of thatch across the top of the door, with ragged ends of
    grass and the shade that it throws. `lift` raises its two ends: a
    saddle roof curves up at each end. Returns its mask."""
    rng = tile.rng
    edge = [(x, depth + rng.uniform(-1.4, 1.4) - lift * ((x - W * 0.5) / (W * 0.5)) ** 2) for x in np.linspace(0.0, W, 24)]
    eave = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(0.0, 0.0), (W, 0.0)] + edge[::-1]))
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(0.0, 0.0), (W, 0.0)] + [(x, y + 3.0) for x, y in edge[::-1]]), blur=1.2) * (1.0 - eave), (0, 0, 0), 0.35)
    tile.put(eave, c["thatch"])
    strands = [(rng.uniform(0.0, W), rng.uniform(0.0, depth - 3.0), rng.uniform(-0.8, 0.8)) for _ in range(80)]
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x, y0), (x + lean, y0 + 5.0)], 0.22) for x, y0, lean in strands]) * eave, _mix(c["thatch"], c["dark"], 0.45), 0.7)
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x + 0.4, y0), (x + 0.4 + lean, y0 + 4.0)], 0.18) for x, y0, lean in strands[::2]]) * eave,
             _mix(c["thatch"], (255, 240, 200), 0.4), 0.6)
    return eave


def _under_house(tile: Tile, c: dict, sill: float, steps: int, rail: RGB, tread: RGB) -> None:
    """The space under a house on posts, from its sill to the ground: the
    dark under the floor, the floor beam with the round ends of the floor
    poles, and a short ladder of `steps` treads up to the door."""
    floor = H - STEP
    under = tile.mask(lambda p, dx, dy: _box(p, dx, dy, F, sill + 4.0, W - F, floor))
    tile.put(under, _mix(c["dark"], c["frame"], 0.15))
    tile.put(under * np.clip((tile.y - sill - 4.0) / (floor - sill - 4.0), 0, 1), _mix(c["frame"], c["dark"], 0.5), 0.5)
    beam = tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, sill, W, sill + 4.0))
    tile.put(beam, c["frame"])
    tile.put(beam * (tile.y < sill + 0.8), c["frame_light"], 0.6)
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, sill + 2.0, 1.5) for x in np.arange(3.0, W, 4.2)]), _mix(c["frame"], c["dark"], 0.35))
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x - 0.4, sill + 1.6, 0.7) for x in np.arange(3.0, W, 4.2)]), c["frame_light"], 0.5)
    x0, x1 = W * 0.5 - 11.0, W * 0.5 + 11.0
    rails = tile.mask(lambda p, dx, dy: (_line(p, dx, dy, [(x0 + 3.0, sill + 3.0), (x0, floor)], 1.8), _line(p, dx, dy, [(x1 - 3.0, sill + 3.0), (x1, floor)], 1.8)))
    for k in range(steps):
        y = sill + 4.0 + (floor - sill - 4.0) * (k + 0.75) / (steps + 0.4)
        lean = 3.0 * (1.0 - (y - sill) / (floor - sill))
        step = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + lean - 1.0, y - 1.4, x1 - lean + 1.0, y + 1.4))
        tile.put(step, tread)
        tile.put(step * (tile.y < y - 0.6), _mix(tread, (255, 245, 220), 0.35), 0.8)
        tile.put(step * (tile.y > y + 0.7), c["dark"], 0.45)
    tile.put(rails, rail)


def austronesia_door(tile: Tile, c: dict) -> np.ndarray:
    """The door of a house on posts on an island of the Austronesians: a
    leaf of bamboo canes side by side, bound on two battens, in a wall of
    woven split bamboo, under a deep eave of thatch. The floor of the house
    is high off the ground, out of the wet and away from the pigs, so a
    short ladder of bamboo goes up to the door."""
    inner = _frame(tile, c)
    sill = 84.0
    # The wall: split bamboo woven in a twill, pale and shining.
    wall = inner * (tile.y < sill)
    tile.put(wall, c["wall"])
    twill = ((np.floor(tile.x / 1.6) + np.floor(tile.y / 4.8) * 2 + np.floor(tile.y / 1.6)) % 4 < 2)
    tile.put(wall * twill, _mix(c["wall"], (255, 250, 220), 0.35), 0.6)
    tile.put(wall * ~twill, c["dark"], 0.12)
    tile.put(wall * (np.abs((tile.y % 1.6) - 0.8) > 0.68), c["dark"], 0.25)
    # The leaf: upright canes with nodes, bound on two battens.
    leaf = tile.mask(lambda p, dx, dy: _box(p, dx, dy, 15.0, 22.0, W - 15.0, sill))
    tile.put(leaf, c["leaf"])
    cane = (tile.x - 15.0) % 3.3
    tile.put(leaf * np.clip(1.0 - np.abs(cane - 1.1) / 0.6, 0, 1), c["leaf_light"], 0.55)
    tile.put(leaf * (cane > 2.9), c["dark"], 0.65)
    nodes = np.abs(((tile.y + np.floor((tile.x - 15.0) / 3.3) * 5.3) % 13.0) - 6.5) > 6.1
    tile.put(leaf * nodes, c["dark"], 0.45)
    for y in (34.0, 72.0):
        batten = tile.mask(lambda p, dx, dy: _box(p, dx, dy, 15.0, y, W - 15.0, y + 3.0))
        tile.put(batten, _mix(c["leaf"], c["dark"], 0.25))
        tile.put(batten * (tile.y < y + 0.7), c["leaf_light"], 0.5)
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x, y - 0.4), (x + 0.8, y + 3.4)], 0.4) for x in (17.5, W * 0.5, W - 17.5)]), c["cord"])
    tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, 13.6, 20.6, W - 13.6, 22.0), _box(p, dx, dy, 13.6, 20.6, 15.0, sill), _box(p, dx, dy, W - 15.0, 20.6, W - 13.6, sill))), c["frame"])
    _window(tile, {**c, "frame": c["frame"]}, W * 0.5 - 4.0, 44.0, W * 0.5 + 4.0, 51.0)
    _under_house(tile, c, sill, 3, c["leaf"], c["leaf_light"])
    eave = _thatch_eave(tile, c, 15.0, 0.0)
    return leaf * (1.0 - eave)


def red_river_door(tile: Tile, c: dict) -> np.ndarray:
    """The door of a house on posts of the Dong Son people of the Red
    River, as their bronze drums show such houses: a leaf of dark wooden
    planks in a wall of boards, under a saddle roof of thatch whose ends
    curve up like the ends of a boat. A long-billed water bird is carved
    on the lintel, as birds fly round the faces of the drums. Wooden steps
    go up to the door, because the house stands high over the floods."""
    inner = _frame(tile, c)
    sill = 86.0
    # The wall: boards laid one on another.
    wall = inner * (tile.y < sill)
    tile.put(wall, c["wall"])
    course = tile.y % 6.0
    tile.put(wall * (course < 0.6), c["frame_light"], 0.35)
    tile.put(wall * (course > 5.4), c["dark"], 0.45)
    tile.tone((tile.noise(3, 20, 2) - 0.5) * 0.18 * wall)
    # The lintel: a wide board with a bird carved in it in low relief.
    lintel = tile.mask(lambda p, dx, dy: _box(p, dx, dy, F + 2.0, 13.0, W - F - 2.0, 25.0))
    tile.put(lintel, c["frame"])
    tile.put(lintel * (tile.y < 13.8), c["frame_light"], 0.6)
    tile.put(lintel * (tile.y > 24.2), c["dark"], 0.6)
    body = [(25.0, 20.0), (29.0, 18.4), (36.0, 18.2), (39.0, 19.4), (35.0, 21.0), (28.0, 21.2)]
    # The wings are raised, as the birds on the drums fly.
    wing = [(28.0, 19.0), (28.6, 13.8), (30.4, 15.0), (31.6, 13.4), (33.4, 14.8), (35.0, 13.6), (36.4, 18.6)]
    tail = [(25.0, 19.8), (18.0, 20.4), (25.0, 20.8)]
    legs = [(25.4, 20.6), (18.8, 22.6), (19.4, 23.0), (25.8, 21.2)]
    neck = [(38.4, 19.2), (40.6, 16.6), (42.4, 15.6), (43.4, 16.4), (41.6, 17.6), (39.8, 20.2)]
    bill = [(43.4, 15.6), (51.0, 17.6), (43.4, 16.6)]
    crest = [(42.0, 15.8), (40.0, 14.2), (42.8, 15.2)]
    bird = tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, q) for q in (body, wing, tail, legs, neck, bill, crest)])
    tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, [(x + 0.4, y + 0.5) for x, y in q]) for q in (body, wing, tail, legs, neck, bill, crest)]) * lintel, c["dark"], 0.65)
    tile.put(bird, c["carving"])
    tile.put(bird * (tile.y < 18.4), c["frame_light"], 0.4)
    tile.put(tile.mask(lambda p, dx, dy: (_line(p, dx, dy, [(29.4, 19.2), (31.4, 16.4)], 0.25), _line(p, dx, dy, [(32.2, 19.2), (33.8, 16.2)], 0.25), _dot(p, dx, dy, 42.4, 16.1, 0.4))), c["dark"], 0.8)
    for x in (12.0, W - 12.0):
        tile.put(tile.mask(lambda p, dx, dy: [p.ellipse([(x - r) * K + dx, (20.0 - r) * K + dy, (x + r) * K + dx, (20.0 + r) * K + dy], outline=255, width=max(1, int(0.4 * K))) for r in (1.2, 2.8)]), c["carving"], 0.8)
    # The leaf: upright planks of dark wood, with a carved band across it
    # of circles joined by lines, as on the bronze of the drums.
    leaf = tile.mask(lambda p, dx, dy: _box(p, dx, dy, 14.0, 27.0, W - 14.0, sill))
    tile.put(leaf, c["leaf"])
    tile.tone((tile.noise(2, 12, 2) - 0.5) * 0.22 * leaf)
    for k in range(1, 4):
        x = 14.0 + k * (W - 28.0) / 4.0
        tile.put(leaf * (np.abs(tile.x - x) < 0.45), c["dark"], 0.8)
        tile.put(leaf * (np.abs(tile.x - x - 0.9) < 0.3), c["leaf_light"], 0.3)
    band = tile.mask(lambda p, dx, dy: _box(p, dx, dy, 14.0, 60.0, W - 14.0, 67.0))
    tile.put(band, _mix(c["leaf"], c["dark"], 0.25))
    centres = [16.6 + k * (W - 33.2) / 5.0 for k in range(6)]
    tile.put(tile.mask(lambda p, dx, dy: ([p.ellipse([(x - 2.2) * K + dx, (63.5 - 2.2) * K + dy, (x + 2.2) * K + dx, (63.5 + 2.2) * K + dy], outline=255, width=max(1, int(0.35 * K))) for x in centres],
                                          [_dot(p, dx, dy, x, 63.5, 0.6) for x in centres],
                                          [_line(p, dx, dy, [(a + 1.6, 65.0), (b - 1.6, 62.0)], 0.3) for a, b in zip(centres, centres[1:])])), c["carving"], 0.85)
    tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, 14.0, 60.0, W - 14.0, 60.6), _box(p, dx, dy, 14.0, 66.4, W - 14.0, 67.0))), c["dark"], 0.7)
    tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, 12.6, 25.6, W - 12.6, 27.0), _box(p, dx, dy, 12.6, 25.6, 14.0, sill), _box(p, dx, dy, W - 14.0, 25.6, W - 12.6, sill))), c["frame"])
    _window(tile, c, W * 0.5 - 4.0, 36.0, W * 0.5 + 4.0, 43.0)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, W - 18.0, 74.0, 1.2)), c["accent"])
    _under_house(tile, c, sill, 3, _mix(c["frame"], c["dark"], 0.2), c["frame"])
    eave = _thatch_eave(tile, c, 10.0, 7.0)
    return leaf * (1.0 - eave)


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
    blast: (SWING, False),
    void_gate: (SWING, True),
    book: (SWING, False),
    organ: (SLIDE, True),
    star_door: (SWING, False),
    pylon: (SWING, True),
    temple: (SWING, True),
    studded: (SWING, True),
    ger_door: (SWING, False),
    hide_door: (SWING, False),
    reed_door: (SWING, False),
    wattle_door: (SWING, False),
    corbel: (SWING, False),
    mat_door: (SWING, False),
    benin_door: (SWING, False),
    saint_domingue_door: (SWING, False),
    gold_coast_door: (SWING, False),
    andes_door: (SWING, False),
    caral_door: (SWING, False),
    wallacea_door: (SWING, False),
    austronesia_door: (SWING, False),
    red_river_door: (SWING, False),
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
    # The station: a sliding bulkhead, amber hazard trim, a cyan lamp.
    "orbital": (bulkhead, _colours((70, 84, 104), (110, 128, 150), (18, 24, 36), (246, 176, 76), (110, 220, 240))),
    "orbital_truss": (bulkhead, _colours((64, 78, 98), (100, 120, 144), (14, 18, 30), (246, 176, 76), (110, 220, 240))),
    # Eureka: an oak door of the institute in a frame of sandstone, and the
    # sliding bulkhead of the space elevator's car.
    "eureka": (plank, _colours((222, 204, 164), (120, 74, 48), (52, 36, 28), (176, 112, 70), (255, 236, 190))),
    "eureka_heights": (bulkhead, _colours((70, 84, 104), (110, 128, 150), (18, 24, 36), (255, 120, 92), (150, 210, 255))),
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
    # The void: black, with a white line on each edge, and a white step.
    "void": (void_gate, {**_colours((4, 4, 5), (14, 14, 16), (2, 2, 3), (236, 236, 236), (244, 244, 244)), "frame_light": (246, 246, 246), "leaf_light": (84, 84, 86)}),
    "void_castle": (iron, _colours((92, 58, 104), (52, 28, 64), (18, 8, 24), (255, 206, 116), (255, 150, 80))),
    # The Noodly Temple: the door of a kitchen, planks with a round window.
    # The town of the Math dimension: a blue door of planks in a limestone arch.
    "math_town": (plank, _colours((226, 216, 194), (70, 112, 170), (40, 52, 70), (78, 124, 186), (255, 236, 190))),
    "math_undercroft": (plank, _colours((196, 178, 148), (70, 112, 170), (34, 38, 54), (214, 170, 84), (255, 204, 128))),
    # A house door from inside: green plank in a plaster arch.
    "math_interior": (plank, _colours((236, 222, 198), (60, 90, 80), (40, 52, 70), (90, 130, 90), (255, 214, 150))),
    # The Art dimension: a door of painted planks in a frame of gold, like a
    # picture; a door of the pages in pale wood; a stone door in the caves.
    "art": (plank, _colours((226, 176, 64), (118, 64, 196), (38, 26, 66), (232, 54, 172), (255, 236, 190))),
    "art_sketchbook": (plank, _colours((226, 196, 140), (232, 226, 210), (92, 94, 110), (92, 94, 110), (255, 250, 236))),
    "art_inkfall": (stone, _colours((70, 50, 120), (40, 24, 80), (14, 8, 34), (246, 70, 200), (255, 170, 236))),
    # The four quarters: the cover of a book in red leather and gold; a door
    # of organ pipes in brass; a stage door with its star; a workshop door of
    # iron bands and rivets in a frame of fired brick.
    "art_stacks": (book, _colours((84, 50, 34), (128, 40, 50), (40, 24, 20), (222, 172, 70), (255, 226, 160))),
    "art_resonance": (organ, _colours((40, 34, 52), (196, 152, 72), (12, 12, 22), (80, 230, 255), (170, 240, 255))),
    "art_stage": (star_door, _colours((60, 30, 34), (40, 34, 44), (20, 12, 16), (236, 182, 70), (255, 230, 170))),
    "art_forge": (iron, _colours((150, 74, 48), (70, 50, 44), (30, 14, 10), (184, 100, 60), (255, 156, 70))),
    # The History dimension. The Crescent: a door of cedar in an arch of
    # mudbrick, a step of lapis; the Nile: a temple door under the winged
    # sun; the Classical Shore: bronze between two columns; the Silk Road:
    # red lacquer with studs of brass; the steppe: the painted orange door of
    # a ger; the Monsoon Coast: carved wood with brass bosses; the Age of
    # Sail: the green door of a counting house; the Industrial Age: an iron
    # mill door with rivets in a frame of brick.
    "history_crescent": (plank, _colours((186, 138, 92), (120, 66, 42), (50, 30, 22), (52, 84, 164), (255, 214, 150))),
    "history_nile": (pylon, _colours((214, 176, 120), (110, 76, 48), (54, 36, 24), (226, 180, 70), (255, 206, 120))),
    "history_classical": (temple, _colours((226, 222, 212), (126, 94, 52), (40, 36, 34), (180, 82, 52), (255, 236, 190))),
    "history_silk": (studded, _colours((70, 40, 30), (160, 38, 34), (36, 16, 14), (220, 172, 72), (255, 196, 110))),
    "history_steppe": (ger_door, _colours((150, 70, 34), (222, 118, 40), (50, 26, 14), (52, 96, 170), (255, 220, 160))),
    "history_monsoon": (studded, _colours((122, 82, 52), (138, 96, 58), (48, 32, 22), (230, 186, 80), (255, 214, 140))),
    "history_sail": (plank, _colours((164, 154, 140), (52, 82, 66), (26, 30, 28), (202, 160, 72), (255, 214, 150))),
    "history_industrial": (iron, _colours((132, 64, 48), (72, 74, 82), (24, 22, 24), (190, 150, 80), (255, 206, 120))),
    # The History dimension, second pass. A hide on a frame of branches in
    # the Rift Valley, Sahul and the painted cave, and on a frame of ivory in
    # the Ice Age; a screen of reeds in the Green Sahara, on the Yellow River,
    # in the maize fields and in the highlands; a stone in an arch on the
    # downs; planks in the north and on the Indus.
    "history_savanna": (hide_door, _colours((120, 86, 56), (178, 130, 86), (50, 32, 20), (190, 90, 50), (255, 190, 110))),
    "history_green_sahara": (reed_door, _colours((110, 80, 50), (196, 170, 104), (60, 44, 26), (176, 64, 44), (255, 220, 150))),
    "history_ice_age": (hide_door, _colours((226, 216, 190), (140, 102, 72), (40, 30, 24), (130, 180, 220), (255, 190, 110))),
    "history_megalith": (stone, _colours((150, 150, 142), (120, 118, 110), (40, 40, 38), (110, 150, 70), (255, 226, 160))),
    "history_northwoods": (plank, _colours((90, 96, 100), (120, 84, 56), (30, 24, 20), (172, 54, 44), (255, 210, 150))),
    "history_indus": (plank, _colours((186, 96, 62), (130, 86, 54), (56, 30, 20), (226, 196, 150), (255, 214, 150))),
    "history_yellow_river": (reed_door, _colours((150, 110, 66), (206, 182, 120), (70, 52, 30), (150, 70, 50), (255, 224, 160))),
    "history_maize": (reed_door, _colours((120, 100, 80), (206, 186, 120), (50, 40, 30), (60, 140, 110), (255, 220, 150))),
    "history_sahul": (hide_door, _colours((150, 110, 80), (160, 96, 60), (50, 24, 16), (200, 90, 50), (255, 170, 80))),
    "history_highlands": (reed_door, _colours((90, 70, 48), (170, 150, 100), (30, 30, 20), (84, 138, 58), (255, 220, 160))),
    "history_painted_cave": (hide_door, _colours((122, 92, 70), (150, 108, 72), (30, 18, 14), (170, 60, 36), (255, 180, 90))),
    # The History dimension, third pass. Wattle and daub on the Gulf coast;
    # a corbel arch and a red hanging in the Maya city; cane on the Taino
    # islands; plaited pandanus on the Lapita shore and in the shelter on a
    # voyaging canoe; a frame of basalt with a leaf of tuff on Rapa Nui.
    "history_olmec": (wattle_door, _colours((168, 126, 86), (110, 88, 60), (40, 30, 22), (70, 150, 110), (255, 214, 150))),
    "history_maya": (corbel, _colours((214, 204, 182), (170, 62, 46), (40, 30, 26), (60, 140, 120), (255, 214, 150))),
    "history_caribbean": (reed_door, _colours((150, 120, 80), (206, 186, 128), (50, 40, 28), (40, 170, 180), (255, 230, 170))),
    "history_lapita": (mat_door, _colours((110, 80, 56), (196, 166, 108), (40, 30, 24), (176, 92, 56), (255, 200, 130))),
    "history_open_ocean": (mat_door, _colours((96, 74, 54), (170, 146, 98), (16, 20, 30), (60, 120, 160), (255, 180, 110))),
    "history_rapa_nui": (stone, _colours((88, 88, 92), (150, 128, 100), (30, 30, 30), (172, 72, 52), (255, 226, 170))),
    # The Atlantic world. Benin City: a carved door of dark wood with brass
    # studs, in a wall of red earth with horizontal ridges.
    "history_benin": (benin_door, _colours((164, 74, 46), (78, 48, 32), (34, 18, 12), (226, 176, 72), (255, 214, 140))),
    # Saint-Domingue: a door of planks in a whitewashed wall of stone, under
    # an eave of thatch, on a step of red earth.
    "history_saint_domingue": (saint_domingue_door, {**_colours((232, 226, 206), (124, 92, 62), (40, 28, 20), (164, 80, 50), (255, 214, 150)), "thatch": (178, 148, 92)}),
    # The Gold Coast: the Door of No Return, a narrow, low doorway through a
    # thick wall washed white; dark inside, with the sea light far beyond.
    "history_gold_coast": (gold_coast_door, {**_colours((232, 230, 222), (40, 38, 38), (14, 14, 16), (150, 146, 138), (226, 236, 230)),
                                             "stone": (150, 148, 142), "sky": (236, 240, 236), "sea": (128, 164, 156)}),
    # South America. The high Andes: a mat of ichu in a low doorway of
    # fieldstones, under a lintel of flat stone and an eave of thatch. Caral:
    # a cloth of cotton in a doorway of dressed stone, at the top of three
    # steps.
    "history_andes": (andes_door, {**_colours((128, 118, 106), (190, 158, 96), (40, 32, 26), (150, 64, 48), (255, 200, 130)), "thatch": (196, 166, 102)}),
    "history_supe": (caral_door, {**_colours((168, 152, 126), (232, 226, 210), (60, 48, 38), (178, 84, 58), (255, 222, 170)), "clay": (138, 112, 84), "band": (150, 104, 66)}),
    # Southeast Asia. Wallacea: a screen of plaited palm leaf in the mouth
    # of a limestone cave, hand stencils in red ochre beside it. The
    # Austronesian islands: a door of bamboo canes in a wall of woven
    # bamboo, under thatch, up a short ladder. The Red River: a door of
    # dark planks under a saddle roof, a bird carved on its lintel, up
    # wooden steps.
    "history_wallacea": (wallacea_door, {**_colours((190, 188, 178), (178, 154, 100), (28, 30, 26), (170, 64, 42), (255, 206, 140)),
                                         "moss": (56, 94, 50), "ochre": (176, 66, 44), "wood": (110, 80, 54)}),
    "history_austronesia": (austronesia_door, {**_colours((104, 78, 52), (196, 180, 116), (34, 26, 20), (186, 82, 52), (255, 220, 160)),
                                               "wall": (214, 196, 140), "thatch": (184, 156, 96), "cord": (120, 84, 50)}),
    "history_red_river": (red_river_door, {**_colours((122, 88, 56), (88, 58, 38), (34, 24, 18), (196, 150, 70), (255, 214, 150)),
                                           "wall": (140, 104, 70), "thatch": (170, 144, 92), "carving": (190, 150, 96)}),
    "noodly": (plank, _colours((196, 150, 86), (132, 78, 46), (48, 24, 16), (172, 44, 32), (255, 226, 150))),
    "primeval": (stone, _colours((92, 84, 66), (120, 130, 86), (34, 28, 18), (255, 170, 80), (255, 236, 190))),
    "forest": (shoji, _colours((58, 36, 26), (150, 140, 110), (26, 16, 12), (214, 70, 60), (244, 236, 208))),
    # The port: a door of tarred planks with a round window, like a cabin's.
    "pirate_port": (cabin, _colours((76, 54, 38), (132, 96, 64), (34, 24, 18), (214, 176, 108), (255, 214, 150))),
    # The village: sliding paper screens in a frame of dark cedar.
    "ninja_village": (shoji, _colours((52, 36, 30), (226, 216, 190), (24, 18, 16), (176, 60, 44), (255, 214, 160))),
    "evil_forest": (iron, _colours((40, 30, 32), (70, 24, 26), (10, 4, 6), (220, 50, 36), (255, 110, 60))),
    "castle_godwin": (iron, _colours((82, 92, 112), (40, 44, 56), (10, 10, 16), (200, 40, 32), (255, 132, 48))),
    "castle_godwin_lab": (iron, _colours((70, 88, 86), (40, 52, 50), (8, 12, 10), (120, 255, 150), (190, 230, 255))),
    "castle_godwin_throne": (iron, _colours((78, 70, 84), (44, 36, 48), (10, 8, 12), (200, 40, 32), (255, 132, 48))),
    # The military tower: an olive blast door in a gunmetal frame, a brass
    # step, the lamp of the corridor behind its slot.
    "military_tower": (blast, {**_colours((70, 78, 84), (84, 90, 52), (20, 22, 20), (176, 150, 84), (255, 200, 132)), "warn": (168, 56, 44)}),
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
    the open door (`terrain.door_swing`)."""
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
