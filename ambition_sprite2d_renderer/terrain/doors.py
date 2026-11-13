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


def _courses_of(tile: Tile, c: dict, mask: np.ndarray, rows: tuple[float, ...], widths: tuple[float, ...], colour: RGB, light: RGB) -> None:
    """Dressed blocks laid in courses over `mask`, each course of the
    height in `rows` in turn, each block of a width from `widths` and of
    its own tone, with a lit top and left edge and a dark joint."""
    rng = tile.rng
    tile.put(mask, c["dark"])
    y0, k = 0.0, 0
    while y0 < H:
        row_h = rows[k % len(rows)]
        x = -rng.uniform(0.0, 8.0)
        while x < W:
            w = rng.choice(widths)
            tone = rng.uniform(-0.14, 0.12)
            fill = _mix(colour, light if tone > 0 else c["dark"], abs(tone) * 1.4)
            block = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x + 0.35, y0 + 0.35, x + w - 0.35, y0 + row_h - 0.35)) * mask
            tile.put(block, fill)
            tile.put(block * ((tile.y < y0 + 1.0) | (tile.x < x + 1.0)), light, 0.35)
            x += w
        y0 += row_h
        k += 1


def strait_door(tile: Tile, c: dict) -> np.ndarray:
    """The door of a house that floats on a raft on the Musi at Palembang:
    a leaf of dark planks, with a panel of nipa thatch in its upper part,
    in a wall of planks under a deep eave of palm thatch. The house stands
    on a raft of logs, and the round ends of the logs show under its sill.
    A small window in the leaf shows the light of a lamp."""
    inner = _frame(tile, c)
    sill = 98.0
    floor = H - STEP
    # The wall: wide boards that stand upright.
    wall = inner * (tile.y < sill)
    tile.put(wall, c["wall"])
    board = (tile.x - F) % 6.5
    tile.put(wall * (board < 0.6), c["dark"], 0.55)
    tile.put(wall * (board > 0.6) * (board < 1.4), c["frame_light"], 0.25)
    tile.tone((tile.noise(3, 20, 2) - 0.5) * 0.18 * wall)
    # The leaf: planks with a panel of nipa thatch held by battens.
    leaf = tile.mask(lambda p, dx, dy: _box(p, dx, dy, 14.0, 26.0, W - 14.0, sill))
    tile.put(leaf, c["leaf"])
    tile.tone((tile.noise(2, 12, 2) - 0.5) * 0.20 * leaf)
    for k in range(1, 5):
        x = 14.0 + k * (W - 28.0) / 5.0
        tile.put(leaf * (np.abs(tile.x - x) < 0.4), c["dark"], 0.75)
        tile.put(leaf * (np.abs(tile.x - x - 0.8) < 0.3), c["leaf_light"], 0.30)
    panel = tile.mask(lambda p, dx, dy: _box(p, dx, dy, 16.0, 32.0, W - 16.0, 58.0))
    tile.put(panel, c["thatch"])
    rows = (tile.y - 32.0) % 3.2
    tile.put(panel * np.clip(1.0 - rows / 1.2, 0, 1), _mix(c["thatch"], (255, 240, 200), 0.35), 0.55)
    tile.put(panel * (rows > 2.6), c["dark"], 0.40)
    tile.put(panel * (np.abs(((tile.x * 1.7) % 1.0) - 0.5) < 0.08), c["dark"], 0.15)
    for y in (30.0, 58.0, 76.0, 94.0):
        batten = tile.mask(lambda p, dx, dy: _box(p, dx, dy, 14.0, y, W - 14.0, y + 2.4))
        tile.put(batten, _mix(c["leaf"], c["dark"], 0.2))
        tile.put(batten * (tile.y < y + 0.6), c["leaf_light"], 0.45)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y + 1.2, 0.55) for x in (16.5, W * 0.5, W - 16.5)]), c["leaf_light"], 0.7)
    tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, 12.6, 24.6, W - 12.6, 26.0), _box(p, dx, dy, 12.6, 24.6, 14.0, sill), _box(p, dx, dy, W - 14.0, 24.6, W - 12.6, sill))), c["frame"])
    _window(tile, c, W * 0.5 - 4.0, 64.0, W * 0.5 + 4.0, 71.0)
    # The raft: a deck beam on the round ends of the logs, and the river
    # dark in the gaps between them.
    raft = tile.mask(lambda p, dx, dy: _box(p, dx, dy, F, sill, W - F, floor))
    tile.put(raft, _mix(c["dark"], (60, 70, 66), 0.3))
    beam = tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, sill, W, sill + 3.0))
    tile.put(beam, c["frame"])
    tile.put(beam * (tile.y < sill + 0.8), c["frame_light"], 0.6)
    ends = [(x, sill + 3.0 + 4.6) for x in np.arange(F + 4.0, W - F - 2.0, 7.6)]
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, 3.6) for x, y in ends]) * raft, _mix(c["frame"], c["wall"], 0.4))
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, 2.4) for x, y in ends]) * raft, _mix(c["wall"], (255, 240, 210), 0.25))
    tile.put(tile.mask(lambda p, dx, dy: [p.ellipse([(x - r) * K + dx, (y - r) * K + dy, (x + r) * K + dx, (y + r) * K + dy], outline=255, width=max(1, int(0.3 * K))) for x, y in ends for r in (1.0, 1.8)]) * raft, c["frame"], 0.6)
    eave = _thatch_eave(tile, c, 16.0, 0.0)
    return leaf * (1.0 - eave)


def borobudur_door(tile: Tile, c: dict) -> np.ndarray:
    """A gateway of grey andesite, as the gates of the terraces of
    Borobudur are built: the courses of the wall step in over the opening
    in a corbelled arch, each course a little further in than the one under
    it, with no keystone. A moulding with a band of lotus petals runs over
    the gate. A leaf of dark teak with studs of bronze closes it."""
    inner = _frame(tile, c)
    floor = H - STEP
    x0, x1, spring = 13.0, W - 13.0, 50.0
    steps = [(x0 + k * 4.6, x1 - k * 4.6, spring - k * 6.0) for k in range(4)]
    opening_pts = [(x0, floor), (x0, spring)]
    for k, (a, b, y) in enumerate(steps[1:], 1):
        opening_pts += [(steps[k - 1][0], y), (a, y)]
    top = steps[-1][2]
    opening_pts += [(steps[-1][0], top - 1.0), (steps[-1][1], top - 1.0)]
    for k in range(len(steps) - 1, 0, -1):
        opening_pts += [(steps[k][1], steps[k][2]), (steps[k - 1][1], steps[k][2])]
    opening_pts += [(x1, spring), (x1, floor)]
    opening = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, opening_pts))
    wall = tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, 0.0, W, floor)) * (1.0 - opening)
    _courses_of(tile, c, wall, (6.0,), (10.0, 13.0, 16.0), c["frame"], c["frame_light"])
    holes = [(tile.rng.uniform(0, W), tile.rng.uniform(0, floor), tile.rng.uniform(0.2, 0.45)) for _ in range(40)]
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, r) for x, y, r in holes]) * wall, c["dark"], 0.6)
    tile.put(wall * np.clip((tile.noise(10, 18, 2) - 0.66) * 6.0, 0, 1), _mix(c["frame_light"], (210, 216, 180), 0.5), 0.45)
    # The edge of the opening is in shade, as the wall is deep.
    rim = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, opening_pts), blur=1.4)
    tile.put(wall * np.clip(rim * 2.0, 0, 1), c["dark"], 0.40)
    # The moulding over the gate: a round torus and a band of petals.
    band_y = 10.0
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, band_y, W, band_y + 7.0)), c["frame"])
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, band_y, W, band_y + 1.0)), c["frame_light"], 0.7)
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, band_y + 2.6, W, band_y + 3.2)), c["dark"], 0.7)
    petals = [k * 4.2 + 2.1 for k in range(16)]
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, band_y + 3.2, W, band_y + 7.0)), c["dark"], 0.55)
    shape = tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, [(x - 1.7, band_y + 7.0), (x - 1.6, band_y + 5.0), (x, band_y + 3.4), (x + 1.6, band_y + 5.0), (x + 1.7, band_y + 7.0)]) for x in petals])
    tile.put(shape, c["frame"])
    tile.put(shape * np.clip(1.0 - ((tile.x + 2.1) % 4.2) / 2.0, 0, 1), c["frame_light"], 0.45)
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, band_y + 7.0, W, band_y + 7.8)), c["dark"], 0.6)
    # The leaf: upright planks of teak, studs of bronze in rows.
    leaf = inner * opening
    tile.put(leaf, c["leaf"])
    tile.tone((tile.noise(2, 14, 2) - 0.5) * 0.20 * leaf)
    for k in range(1, 5):
        x = x0 + k * (x1 - x0) / 5.0
        tile.put(leaf * (np.abs(tile.x - x) < 0.4), c["dark"], 0.75)
        tile.put(leaf * (np.abs(tile.x - x - 0.8) < 0.3), c["leaf_light"], 0.30)
    for y in (54.0, 78.0, 102.0):
        tile.put(leaf * (np.abs(tile.y - y) < 1.4), _mix(c["leaf"], c["dark"], 0.3))
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x0 + 3.0 + j * 5.2, y, 0.9) for j in range(8)]) * leaf, c["accent"], 0.9)
    _window(tile, {**c, "frame": c["leaf"]}, W * 0.5 - 3.5, 36.0, W * 0.5 + 3.5, 43.0, round_=True)
    return leaf


def angkor_door(tile: Tile, c: dict) -> np.ndarray:
    """A doorway of a Khmer temple in a wall of red laterite: a frame of
    grey-pink sandstone, with a round colonnette in rings at each side and
    a lintel over it carved with a winding vine. Over the lintel the
    courses of the wall step in to a point, a corbelled arch. A leaf of
    dark wood closes the doorway."""
    inner = _frame(tile, c)
    floor = H - STEP
    x0, x1 = 15.0, W - 15.0
    lintel_top, lintel_bottom = 30.0, 38.0
    # The opening: straight jambs up to the lintel. Over the lintel the
    # corbelled arch is a tall stepped triangle, filled with a tympanum of
    # plain sandstone.
    tymp_pts = [(x0 - 1.0, lintel_top)]
    for k in range(6):
        y = lintel_top - k * 3.4
        tymp_pts += [(x0 - 1.0 + k * 2.7, y), (x0 - 1.0 + k * 2.7, y - 3.4)]
    tymp_pts += [(W * 0.5, lintel_top - 6 * 3.4 - 1.2)]
    for k in range(5, -1, -1):
        y = lintel_top - k * 3.4
        tymp_pts += [(x1 + 1.0 - k * 2.7, y - 3.4), (x1 + 1.0 - k * 2.7, y)]
    tymp_pts += [(x1 + 1.0, lintel_top)]
    tympanum = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, tymp_pts))
    opening = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0, lintel_bottom, x1, floor))
    frame_mask = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 - 7.0, lintel_top - 1.0, x1 + 7.0, floor))
    wall = tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, 0.0, W, floor)) * (1.0 - np.maximum(frame_mask, tympanum))
    # The wall: big blocks of laterite, full of pits.
    _courses_of(tile, c, wall, (6.0, 5.0), (10.0, 13.0, 16.0), c["laterite"], _mix(c["laterite"], (255, 210, 170), 0.3))
    pits = np.clip((tile.noise(20, 36, 2) - 0.64) * 8.0, 0, 1)
    tile.put(wall * pits, _mix(c["dark"], (40, 16, 10), 0.4), 0.8)
    tile.put(wall * np.clip((np.roll(tile.noise(20, 36, 2), -2, axis=0) - 0.64) * 8.0, 0, 1) * (1.0 - pits), (255, 200, 160), 0.18)
    # The tympanum: plain sandstone in its courses, each course a step of
    # the arch.
    tile.put(tympanum, _mix(c["frame"], c["dark"], 0.10))
    for k in range(7):
        y = lintel_top - k * 3.4
        tile.put(tympanum * (np.abs(tile.y - y) < 0.3), c["dark"], 0.55)
        tile.put(tympanum * (np.abs(tile.y - y + 0.6) < 0.3), c["frame_light"], 0.35)
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, tymp_pts), blur=0.8) * (1.0 - tympanum) * wall, c["dark"], 0.45)
    # The sandstone frame and the colonnettes.
    frame_only = frame_mask * (1.0 - opening)
    tile.put(frame_only, c["frame"])
    tile.tone((tile.noise(6, 14, 2) - 0.5) * 0.14 * frame_only)
    for cx in (x0 - 3.5, x1 + 3.5):
        col = tile.mask(lambda p, dx, dy: _box(p, dx, dy, cx - 2.4, lintel_bottom, cx + 2.4, floor))
        tile.put(col * np.clip(1.0 - np.abs(tile.x - cx + 0.9) / 1.0, 0, 1), c["frame_light"], 0.55)
        tile.put(col * np.clip((tile.x - cx - 0.6) / 1.8, 0, 1), c["dark"], 0.45)
        for y in np.arange(lintel_bottom + 3.0, floor, 6.0):
            tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, cx - 2.8, y, cx + 2.8, y + 1.2)), _mix(c["frame"], c["frame_light"], 0.3))
            tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, cx - 2.8, y + 1.2, cx + 2.8, y + 1.6)), c["dark"], 0.5)
    lintel = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 - 7.0, lintel_top, x1 + 7.0, lintel_bottom))
    tile.put(lintel, c["frame"])
    tile.put(lintel * (tile.y < lintel_top + 0.8), c["frame_light"], 0.65)
    tile.put(lintel * (tile.y > lintel_bottom - 0.8), c["dark"], 0.55)
    vine = [(x, (lintel_top + lintel_bottom) * 0.5 + 1.6 * math.sin((x - x0) * math.pi / 5.0)) for x in np.linspace(x0 - 5.0, x1 + 5.0, 60)]
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, vine, 0.5)), c["dark"], 0.55)
    curls = [(x0 - 5.0 + k * 5.0 + 2.5, (lintel_top + lintel_bottom) * 0.5 + (1.4 if k % 2 else -1.4)) for k in range(int((x1 - x0 + 10.0) / 5.0))]
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, 0.9, ry=0.6) for x, y in curls]), _mix(c["frame"], c["dark"], 0.4))
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x - 0.2, y - 0.2, 0.4, ry=0.25) for x, y in curls]), c["frame_light"], 0.5)
    # The leaf: planks of dark wood with two iron bands.
    leaf = inner * opening
    tile.put(leaf, c["leaf"])
    tile.tone((tile.noise(2, 14, 2) - 0.5) * 0.20 * leaf)
    for k in range(1, 4):
        x = x0 + k * (x1 - x0) / 4.0
        tile.put(leaf * (np.abs(tile.x - x) < 0.4), c["dark"], 0.75)
        tile.put(leaf * (np.abs(tile.x - x - 0.8) < 0.3), c["leaf_light"], 0.30)
    for y in (58.0, 96.0):
        tile.put(leaf * (np.abs(tile.y - y) < 1.3), _mix(c["leaf"], c["dark"], 0.45))
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, x1 - 5.0, 78.0, 1.2)), c["accent"])
    _window(tile, {**c, "frame": c["frame"]}, W * 0.5 - 3.5, 44.0, W * 0.5 + 3.5, 51.0)
    return leaf


#: A style draws the door on a tile and returns the mask of its leaf.
Draw = Callable[[Tile, dict], np.ndarray]

#: How the leaf of each style opens: one leaf that swings on the left jamb, or
#: two leaves (one on each jamb) that swing or slide.
def _thatch_roof(tile: Tile, c: dict, mask: np.ndarray, apex: tuple[float, float], row: float) -> None:
    """Thatch over `mask`, laid in rows of bundles as on a steep roof: the
    straws point down and out from the `apex`, each row has a ragged dark
    lower edge, and the straws catch the light in fine lines."""
    ax, ay = apex
    tile.put(mask, c["thatch"])
    fan = (tile.x - ax) / np.maximum(tile.y - ay, 1.0)
    straw = np.abs(((fan * 40.0 + tile.noise(10, 4, 2) * 2.0) % 1.0) - 0.5)
    tile.put(mask * (straw < 0.12), _mix(c["thatch"], c["dark"], 0.40), 0.55)
    tile.put(mask * (straw > 0.40), _mix(c["thatch"], (255, 240, 200), 0.35), 0.50)
    edge = ((tile.y + (tile.noise(16, 2, 2) - 0.5) * 2.0) % row) / row
    tile.put(mask * np.clip((edge - 0.78) / 0.22, 0.0, 1.0), c["dark"], 0.55)
    tile.put(mask * np.clip(1.0 - edge / 0.18, 0.0, 1.0), _mix(c["thatch"], (255, 240, 200), 0.2), 0.40)


def jomon_door(tile: Tile, c: dict) -> np.ndarray:
    """The low entrance of a pit house of Sannai-Maruyama. The house is
    dug into the ground, and its steep roof of grass thatch comes down
    almost to the earth, so the roof fills the frame. A small porch of
    thatch on two forked chestnut posts shelters the low doorway, and a
    mat of woven bark hangs in it. The light of the fire shows through
    the smoke hole high in the roof."""
    inner = _frame(tile, c)
    floor = H - STEP
    _thatch_roof(tile, c, inner, (W * 0.5, -30.0), 5.5)
    # The earth bank of the pit, low at each side of the door.
    bank = tile.mask(lambda p, dx, dy: (_dot(p, dx, dy, F + 2.0, floor, 9.0, ry=7.0), _dot(p, dx, dy, W - F - 2.0, floor, 9.0, ry=7.0))) * inner
    tile.put(bank, c["earth"])
    tile.put(bank * (tile.y < floor - 4.0), _mix(c["earth"], (140, 160, 80), 0.45), 0.7)
    # The doorway and its posts.
    x0, x1, top = 16.0, W - 16.0, 66.0
    opening = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0, top, x1, floor))
    tile.put(opening, c["dark"])
    for px in (x0 - 3.0, x1):
        post = tile.mask(lambda p, dx, dy: _box(p, dx, dy, px, top - 6.0, px + 3.0, floor))
        tile.put(post, c["frame"])
        tile.put(post * (tile.x < px + 1.0), c["frame_light"], 0.5)
        tile.put(post * np.clip((tile.noise(2, 16, 2) - 0.5) * 3.0, 0, 1), c["dark"], 0.35)
    # The mat: strips of bark woven over and under, with a heavy pole at
    # its foot. It is the leaf.
    leaf = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 1.0, top + 3.0, x1 - 1.0, floor - 0.6))
    tile.put(leaf, c["leaf"])
    weave = ((np.floor((tile.x - x0) / 2.4) + np.floor((tile.y - top) / 2.4)) % 2 == 0)
    tile.put(leaf * weave, c["leaf_light"], 0.35)
    tile.put(leaf * ~weave, c["dark"], 0.15)
    tile.put(leaf * (np.abs(((tile.x - x0) % 2.4) - 2.4) < 0.25), c["dark"], 0.35)
    tile.put(leaf * (np.abs(((tile.y - top) % 2.4)) < 0.2), c["dark"], 0.30)
    pole = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 0.4, floor - 3.6, x1 - 0.4, floor - 1.6))
    tile.put(pole, c["frame"])
    tile.put(pole * (tile.y < floor - 3.0), c["frame_light"], 0.5)
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 1.0, top + 1.0, x1 - 1.0, top + 3.0)), c["frame"])
    # The porch: a small gable of thatch over the door, and the crossed
    # ends of its two rafters over the ridge.
    ridge = 44.0
    porch_pts = [(x0 - 9.0, top + 1.0), (W * 0.5, ridge), (x1 + 9.0, top + 1.0), (x1 + 7.0, top + 3.6), (W * 0.5, ridge + 4.0), (x0 - 7.0, top + 3.6)]
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(x, y + 2.6) for x, y in porch_pts]), blur=1.0) * inner, (0, 0, 0), 0.35)
    porch = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, porch_pts))
    _thatch_roof(tile, {**c, "thatch": _mix(c["thatch"], (255, 240, 200), 0.12)}, porch, (W * 0.5, ridge - 20.0), 4.0)
    tile.put(tile.mask(lambda p, dx, dy: (_line(p, dx, dy, [(W * 0.5 + 6.0, ridge - 5.0), (W * 0.5 - 1.0, ridge + 2.0)], 1.4),
                                           _line(p, dx, dy, [(W * 0.5 - 6.0, ridge - 5.0), (W * 0.5 + 1.0, ridge + 2.0)], 1.4))), c["frame"])
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(W * 0.5 - 2.0, ridge - 1.0), (W * 0.5 + 2.0, ridge + 1.6)], 0.6)), c["cord"], 0.9)
    # The smoke hole high in the roof, lit by the fire inside.
    _window(tile, c, W * 0.5 - 5.0, 16.0, W * 0.5 + 5.0, 22.0)
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(W * 0.5 - 8.0, 16.0), (W * 0.5, 9.0), (W * 0.5 + 8.0, 16.0), (W * 0.5 + 6.0, 16.6), (W * 0.5 - 6.0, 16.6)])), _mix(c["thatch"], c["dark"], 0.2))
    return leaf


def taiwan_door(tile: Tile, c: dict) -> np.ndarray:
    """The door of a house on posts on the coast of eastern Taiwan: a
    leaf of three broad planks, shaped with stone adzes, held by two
    battens lashed with rattan. A lintel over it is painted in bands of
    red and black, as the people of the island wove their cloth. The
    house stands on posts, so a short ladder goes up to the door, and a
    deep eave of thatch is over it."""
    inner = _frame(tile, c)
    sill = 82.0
    wall = inner * (tile.y < sill)
    tile.put(wall, c["wall"])
    board = (tile.x - F) % 7.0
    tile.put(wall * (board < 0.6), c["dark"], 0.55)
    tile.put(wall * (board > 0.6) * (board < 1.6), c["frame_light"], 0.25)
    tile.tone((tile.noise(3, 20, 2) - 0.5) * 0.18 * wall)
    leaf = tile.mask(lambda p, dx, dy: _box(p, dx, dy, 15.0, 30.0, W - 15.0, sill))
    tile.put(leaf, c["leaf"])
    tile.tone((tile.noise(2, 14, 2) - 0.5) * 0.22 * leaf)
    adze = np.abs(((tile.y + np.floor((tile.x - 15.0) / 11.0) * 2.3) % 4.6) - 2.3) < 0.35
    tile.put(leaf * adze, c["leaf_light"], 0.18)
    for k in (1, 2):
        x = 15.0 + k * (W - 30.0) / 3.0
        tile.put(leaf * (np.abs(tile.x - x) < 0.45), c["dark"], 0.80)
        tile.put(leaf * (np.abs(tile.x - x - 0.9) < 0.3), c["leaf_light"], 0.35)
    for y in (40.0, 72.0):
        batten = tile.mask(lambda p, dx, dy: _box(p, dx, dy, 15.0, y, W - 15.0, y + 3.0))
        tile.put(batten, _mix(c["leaf"], c["dark"], 0.25))
        tile.put(batten * (tile.y < y + 0.7), c["leaf_light"], 0.5)
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x - 1.0 + j * 0.8, y - 0.6), (x - 0.2 + j * 0.8, y + 3.6)], 0.4) for x in (18.0, W * 0.5, W - 18.0) for j in range(3)]), c["cord"])
    tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, 13.6, 28.6, 15.0, sill), _box(p, dx, dy, W - 15.0, 28.6, W - 13.6, sill))), c["frame"])
    # The lintel: bands of red and black, with a row of small diamonds.
    lintel = tile.mask(lambda p, dx, dy: _box(p, dx, dy, F, 21.0, W - F, 29.0))
    tile.put(lintel, c["frame"])
    tile.put(lintel * ((tile.y < 23.0) | (tile.y > 27.0)), c["paint_black"], 0.85)
    tile.put(lintel * (tile.y >= 23.0) * (tile.y <= 27.0), c["paint_red"])
    diamonds = [(x, 25.0) for x in np.arange(F + 3.0, W - F, 5.0)]
    tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, [(x - 1.6, y), (x, y - 1.6), (x + 1.6, y), (x, y + 1.6)]) for x, y in diamonds]), c["paint_black"], 0.9)
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, 0.5) for x, y in diamonds]), (232, 214, 170), 0.9)
    _window(tile, c, W * 0.5 - 4.0, 50.0, W * 0.5 + 4.0, 57.0)
    _under_house(tile, c, sill, 3, c["leaf"], c["leaf_light"])
    eave = _thatch_eave(tile, c, 17.0, 0.0)
    return leaf * (1.0 - eave)


def gyeongju_door(tile: Tile, c: dict) -> np.ndarray:
    """A gate of Silla at Gyeongju: two leaves of thick planks painted
    red, with rows of iron studs and a ring of bronze on each, between red
    posts. A lattice of upright bars over the leaves lets in the light. A
    roof of grey clay tiles is over the gate: rows of round tile ends
    along its eave, and its two ends turn up. The gate stands on a sill of
    granite."""
    inner = _frame(tile, c)
    floor = H - STEP
    # The roof: a band of tiles from the top, its eave curved up at the ends.
    eave_y = 24.0
    curve = [(x, eave_y - 7.0 * ((x - W * 0.5) / (W * 0.5)) ** 4) for x in np.linspace(0.0, W, 28)]
    roof = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(0.0, 0.0), (W, 0.0)] + curve[::-1]))
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(0.0, 0.0), (W, 0.0)] + [(x, y + 4.0) for x, y in curve[::-1]]), blur=1.4) * (1.0 - roof), (0, 0, 0), 0.45)
    tile.put(roof, c["tile"])
    lanes = np.abs(((tile.x - W * 0.5) % 4.0) - 2.0)
    tile.put(roof * np.clip(1.0 - lanes / 0.9, 0, 1), _mix(c["tile"], (255, 255, 255), 0.30), 0.55)
    tile.put(roof * (lanes > 1.6), c["dark"], 0.55)
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, 0.0, W, 5.0)), _mix(c["tile"], c["dark"], 0.30))
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, 0.0, W, 1.2)), _mix(c["tile"], (255, 255, 255), 0.25), 0.6)
    ends = [(x, eave_y - 7.0 * ((x - W * 0.5) / (W * 0.5)) ** 4 - 1.4) for x in np.arange(2.0, W - 1.0, 4.0)]
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, 1.8) for x, y in ends]), _mix(c["tile"], c["dark"], 0.15))
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, 1.1) for x, y in ends]), _mix(c["tile"], (255, 255, 255), 0.22))
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, 0.45) for x, y in ends]), c["dark"], 0.6)
    # Under the eave: a beam painted green with a red band, on the posts.
    beam = tile.mask(lambda p, dx, dy: _box(p, dx, dy, F, eave_y, W - F, eave_y + 6.0)) * (1.0 - roof)
    tile.put(beam, c["bracket"])
    tile.put(beam * (tile.y > eave_y + 4.0), c["frame"])
    tile.put(beam * (np.abs(((tile.x - F) % 9.0) - 4.5) < 0.4) * (tile.y < eave_y + 4.0), (232, 214, 170), 0.7)
    # The lattice over the leaves, with the light behind its bars.
    lat0, lat1 = eave_y + 8.0, eave_y + 20.0
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, F + 1.0, lat0 - 1.4, W - F - 1.0, lat1 + 1.4)), c["frame"])
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, F + 2.4, lat0, W - F - 2.4, lat1)), c["glow"])
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x - 0.6, lat0, x + 0.6, lat1) for x in np.arange(F + 5.0, W - F - 3.0, 3.6)]), c["frame"])
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, F + 2.4, lat0, W - F - 2.4, lat0 + 4.0)), (255, 255, 255), 0.25)
    # The two leaves: planks, bands, studs and the rings.
    top = lat1 + 1.4
    leaf = tile.mask(lambda p, dx, dy: _box(p, dx, dy, F + 1.0, top, W - F - 1.0, floor))
    tile.put(leaf, c["leaf"])
    tile.tone((tile.noise(2, 12, 2) - 0.5) * 0.16 * leaf)
    plank = (tile.x - F - 1.0) % 6.4
    tile.put(leaf * (plank < 0.5), c["dark"], 0.55)
    tile.put(leaf * (plank > 0.5) * (plank < 1.3), c["leaf_light"], 0.25)
    tile.put(leaf * (np.abs(tile.x - W * 0.5) < 0.6), c["dark"], 0.9)
    for y in (top + 8.0, floor - 12.0):
        band = tile.mask(lambda p, dx, dy: _box(p, dx, dy, F + 1.0, y, W - F - 1.0, y + 3.4))
        tile.put(band, _mix(c["leaf"], c["dark"], 0.25))
        tile.put(band * (tile.y < y + 0.7), c["leaf_light"], 0.45)
        studs = [(x, y + 1.7) for x in np.arange(F + 4.0, W - F - 2.0, 4.6) if abs(x - W * 0.5) > 1.6]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, 0.9) for x, yy in studs]), (60, 54, 52))
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x - 0.25, yy - 0.25, 0.35) for x, yy in studs]), (200, 196, 190), 0.6)
    for x in (W * 0.5 - 4.6, W * 0.5 + 4.6):
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, x, 72.0, 1.4)), c["bronze"])
        tile.put(tile.mask(lambda p, dx, dy: p.ellipse([(x - 2.6) * K + dx, (72.0) * K + dy, (x + 2.6) * K + dx, (77.4) * K + dy], outline=255, width=max(1, int(0.7 * K)))), c["bronze"])
        tile.put(tile.mask(lambda p, dx, dy: p.arc([(x - 2.6) * K + dx, (72.0) * K + dy, (x + 2.6) * K + dx, (77.4) * K + dy], 120, 200, fill=255, width=max(1, int(0.35 * K)))), (255, 236, 180), 0.7)
    # The posts each side, and the sill of granite.
    for x0 in (0.0, W - F - 1.0):
        post = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0, eave_y, x0 + F + 1.0, floor))
        tile.put(post, c["frame"])
        tile.put(post * (tile.x < x0 + 1.4), c["frame_light"], 0.45)
        tile.put(post * (tile.x > x0 + F - 0.4), c["dark"], 0.35)
    sill = tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, floor - 2.6, W, floor))
    tile.put(sill, c["accent"])
    tile.put(sill * (tile.y < floor - 2.0), _mix(c["accent"], (255, 255, 255), 0.4), 0.7)
    return leaf * (1.0 - sill)


def _tiled_roof(tile: Tile, c: dict, x0: float, x1: float, ridge: float, eave: float, lift: float, colour: RGB, lane: float = 3.6) -> np.ndarray:
    """A roof of clay tiles seen from the front, from `x0` to `x1`: a ridge
    at `ridge`, lanes of round tiles that run down to the eave, and a row
    of round tile ends along the eave. The eave is at `eave` in the middle
    and turns up by `lift` at the two ends. Returns the mask of the roof."""
    mid, half = (x0 + x1) * 0.5, (x1 - x0) * 0.5
    curve = [(x, eave - lift * ((x - mid) / half) ** 4) for x in np.linspace(x0, x1, 32)]
    pts = [(x0 + 3.0, ridge), (x1 - 3.0, ridge)] + curve[::-1]
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(x, y + 3.0) for x, y in pts]), blur=1.2), (0, 0, 0), 0.40)
    roof = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, pts))
    tile.put(roof, colour)
    lanes = np.abs(((tile.x - mid) % lane) - lane * 0.5)
    tile.put(roof * np.clip(1.0 - lanes / (lane * 0.22), 0, 1), _mix(colour, (255, 255, 255), 0.28), 0.55)
    tile.put(roof * (lanes > lane * 0.40), c["dark"], 0.55)
    ridge_band = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 2.0, ridge - 1.2, x1 - 2.0, ridge + 3.0))
    tile.put(ridge_band, _mix(colour, c["dark"], 0.35))
    tile.put(ridge_band * (tile.y < ridge - 0.2), _mix(colour, (255, 255, 255), 0.30), 0.6)
    ends = [(x, eave - lift * ((x - mid) / half) ** 4 - 1.0) for x in np.arange(mid - np.floor(half / lane) * lane, x1, lane)]
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, lane * 0.42) for x, y in ends]), _mix(colour, c["dark"], 0.10))
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x - 0.2, y - 0.2, lane * 0.26) for x, y in ends]), _mix(colour, (255, 255, 255), 0.22))
    return roof


def hangzhou_door(tile: Tile, c: dict) -> np.ndarray:
    """A moon gate of a garden by West Lake: a round opening, framed by a
    ring of grey brick, in a wall of white plaster under a coping of grey
    tiles. Two leaves of dark wood close the round opening, each with a
    small lattice window in its upper part, where the light of the garden
    shows. Over the gate a window of grey tile lattice in the wall shows
    the green of the garden. A branch of willow hangs over the wall, and a
    low sill of stone is at the foot of the gate."""
    _frame(tile, c)
    floor = H - STEP
    wall = tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, 0.0, W, floor))
    tile.put(wall, c["wall"])
    tile.tone((tile.noise(6, 12, 3) - 0.5) * 0.08 * wall)
    # Damp at the foot of the wall, and its two ends a little in shade.
    tile.put(wall * np.clip((tile.y - (floor - 12.0)) / 12.0, 0, 1), _mix(c["wall"], (120, 128, 110), 0.6), 0.45)
    tile.put(wall * np.clip(1.0 - tile.x / 3.0, 0, 1), c["dark"], 0.25)
    tile.put(wall * np.clip((tile.x - W + 3.0) / 3.0, 0, 1), c["dark"], 0.25)
    # The coping of grey tiles along the top of the wall.
    _tiled_roof(tile, c, -1.0, W + 1.0, 4.0, 15.0, 0.0, c["tile"], lane=3.5)
    # A window in the wall: a hexagon framed in grey, with a lattice of
    # grey tiles set in rings, and the leaves of the garden behind it.
    hx, hy, hr = W * 0.5, 40.0, 13.0
    hexagon = [(hx + math.cos(a) * hr, hy + math.sin(a) * hr * 0.92) for a in np.linspace(0.0, 2.0 * math.pi, 6, endpoint=False)]
    inner_hex = [(hx + math.cos(a) * (hr - 1.8), hy + math.sin(a) * (hr - 1.8) * 0.92) for a in np.linspace(0.0, 2.0 * math.pi, 6, endpoint=False)]
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(x + 0.8, y + 0.8) for x, y in hexagon]), blur=0.6), (0, 0, 0), 0.25)
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, hexagon)), c["frame"])
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, hexagon)) * (tile.y < hy - 4.0), c["frame_light"], 0.35)
    view = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, inner_hex))
    tile.put(view, _mix(c["willow"], (40, 70, 50), 0.5))
    tile.put(view * np.clip((tile.noise(10, 20, 2) - 0.45) * 4.0, 0, 1), c["willow"], 0.8)
    tile.put(view * np.clip(1.0 - (tile.y - (hy - 9.0)) / 6.0, 0, 1), (230, 240, 230), 0.35)
    rings = []
    for row in range(-4, 5):
        for col in range(-4, 5):
            rings.append((hx + col * 3.2 + (row % 2) * 1.6, hy + row * 2.8))
    lattice = tile.mask(lambda p, dx, dy: [p.ellipse([(x - 1.9) * K + dx, (y - 1.9) * K + dy, (x + 1.9) * K + dx, (y + 1.9) * K + dy], outline=255, width=max(1, int(0.55 * K))) for x, y in rings]) * view
    tile.put(lattice, c["tile"])
    tile.put(lattice * (tile.y < hy), _mix(c["tile"], (255, 255, 255), 0.25), 0.4)
    # The ring of the gate and the opening in it.
    cx, cy, r = W * 0.5, floor - 21.0, 26.0
    ring = tile.mask(lambda p, dx, dy: _dot(p, dx, dy, cx, cy, r + 3.0)) * (tile.y < floor)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, cx + 0.8, cy + 0.8, r + 3.6), blur=0.8) * wall * (1.0 - ring), (0, 0, 0), 0.25)
    tile.put(ring, c["frame"])
    angle = np.arctan2(tile.y - cy, tile.x - cx)
    tile.put(ring * (np.abs(((angle / (2.0 * math.pi) * 36.0) % 1.0) - 0.5) > 0.44), c["dark"], 0.55)
    tile.put(ring * (np.abs(np.sqrt((tile.x - cx) ** 2 + (tile.y - cy) ** 2) - (r + 1.5)) < 0.25), c["dark"], 0.35)
    tile.put(ring * (angle < -0.3) * (angle > -2.6) * (np.sqrt((tile.x - cx) ** 2 + (tile.y - cy) ** 2) > r + 2.2), c["frame_light"], 0.45)
    opening = tile.mask(lambda p, dx, dy: _dot(p, dx, dy, cx, cy, r)) * (tile.y < floor)
    # The two leaves: planks of dark wood, the seam between them, a band
    # of iron, and a ring on each leaf.
    leaf = opening
    tile.put(leaf, c["leaf"])
    tile.tone((tile.noise(2, 14, 2) - 0.5) * 0.18 * leaf)
    plank = (tile.x - cx) % 5.0
    tile.put(leaf * (plank < 0.4), c["dark"], 0.5)
    tile.put(leaf * (plank > 0.4) * (plank < 1.1), c["leaf_light"], 0.18)
    tile.put(leaf * (np.abs(tile.x - cx) < 0.6), c["dark"], 0.9)
    tile.put(leaf * np.clip(1.0 - (np.sqrt((tile.x - cx) ** 2 + (tile.y - cy) ** 2) - (r - 2.0)) * -0.5, 0, 1), c["dark"], 0.35)
    for y in (cy - 4.0, cy + 12.0):
        tile.put(leaf * (np.abs(tile.y - y) < 1.2), _mix(c["leaf"], c["dark"], 0.4))
        tile.put(leaf * (np.abs(tile.y - y + 1.0) < 0.25), c["leaf_light"], 0.3)
    # A lattice window in the upper part of each leaf.
    for x0, x1 in ((cx - 13.0, cx - 3.0), (cx + 3.0, cx + 13.0)):
        win = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0, cy - 19.0, x1, cy - 10.0)) * opening
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 - 1.0, cy - 20.0, x1 + 1.0, cy - 9.0)) * opening, _mix(c["leaf"], c["dark"], 0.3))
        tile.put(win, c["glow"])
        tile.put(win * (tile.y < cy - 16.0), (255, 255, 255), 0.25)
        bars = (np.abs(((tile.x - x0) % 2.5) - 1.25) > 0.95) | (np.abs(((tile.y - (cy - 19.0)) % 3.0) - 1.5) > 1.15)
        tile.put(win * bars, _mix(c["leaf"], c["dark"], 0.2))
    for x in (cx - 3.2, cx + 3.2):
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, x, cy + 4.0, 1.0)), c["accent"])
        tile.put(tile.mask(lambda p, dx, dy: p.ellipse([(x - 1.9) * K + dx, (cy + 4.0) * K + dy, (x + 1.9) * K + dx, (cy + 7.8) * K + dy], outline=255, width=max(1, int(0.5 * K)))), c["accent"])
    # The sill of stone in the opening.
    sill = tile.mask(lambda p, dx, dy: _box(p, dx, dy, cx - r + 2.0, floor - 2.4, cx + r - 2.0, floor)) * opening
    tile.put(sill, c["accent"])
    tile.put(sill * (tile.y < floor - 1.8), _mix(c["accent"], (255, 255, 255), 0.4), 0.7)
    # A branch of willow that hangs over the wall from the left.
    rng = tile.rng
    branch = [(-1.0, 14.0), (4.0, 15.6), (9.0, 16.0), (14.0, 15.0)]
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, branch, 0.7)), (90, 70, 50))
    strands = []
    for bx, by in ((2.0, 15.2), (5.0, 15.8), (8.0, 16.0), (11.0, 15.6), (13.4, 15.2)):
        length = rng.uniform(14.0, 26.0)
        strands.append([(bx + 0.6 * math.sin(t * 2.0), by + t * length) for t in np.linspace(0.0, 1.0, 12)])
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, pts, 0.25) for pts in strands]), _mix(c["willow"], (90, 70, 50), 0.4))
    leaves = [(x + (0.4 if j % 2 else -0.4), y) for pts in strands for j, (x, y) in enumerate(pts[1:])]
    tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, [(x, y - 1.2), (x + 0.35, y), (x, y + 0.8), (x - 0.35, y)]) for x, y in leaves]), c["willow"])
    tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, [(x, y - 1.2), (x + 0.35, y), (x, y + 0.8), (x - 0.35, y)]) for x, y in leaves[::3]]), _mix(c["willow"], (255, 255, 210), 0.35))
    return leaf * (1.0 - sill)


def heian_door(tile: Tile, c: dict) -> np.ndarray:
    """A gate in the wall of a mansion of Heian-kyo: two round posts
    painted vermilion with a vermilion beam across them, under a roof of
    black tiles that curves up a little at its ends. Between the beam and
    the head of the leaves is a panel of white plaster with a window of
    upright bars. The two leaves are of plain cypress planks with black
    iron straps. The posts stand on round stones."""
    _frame(tile, c)
    floor = H - STEP
    back = tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, 0.0, W, floor))
    tile.put(back, c["dark"])
    # The rafters: their pale ends in a row under the eave.
    rafter_y = 22.0
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, 1.0, rafter_y - 3.0, W - 1.0, rafter_y + 3.0)), _mix(c["dark"], c["frame"], 0.25))
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x - 1.0, rafter_y, x + 1.0, rafter_y + 2.6) for x in np.arange(3.0, W - 1.0, 3.6)]), c["rafter"])
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x - 1.0, rafter_y + 2.0, x + 1.0, rafter_y + 2.6) for x in np.arange(3.0, W - 1.0, 3.6)]), c["dark"], 0.35)
    # The roof of black tiles.
    _tiled_roof(tile, c, -1.0, W + 1.0, 4.0, 20.0, 4.0, c["tile"], lane=3.6)
    # The beam under the rafters, the plaster panel with its window, and
    # the lower beam over the leaves.
    beam0, beam1 = 25.4, 30.0
    panel0, panel1 = beam1, 42.0
    nuki0, nuki1 = panel1, 46.0
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, F, panel0, W - F, panel1)), c["plaster"])
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, F, panel0, W - F, panel0 + 1.2)), c["dark"], 0.25)
    wx0, wx1 = W * 0.5 - 9.0, W * 0.5 + 9.0
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, wx0 - 1.2, panel0 + 2.2, wx1 + 1.2, panel1 - 2.2)), c["frame"])
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, wx0, panel0 + 3.2, wx1, panel1 - 3.2)), c["glow"])
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, wx0, panel0 + 3.2, wx1, panel0 + 5.0)), (255, 255, 255), 0.25)
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x - 0.55, panel0 + 3.2, x + 0.55, panel1 - 3.2) for x in np.arange(wx0 + 2.0, wx1 - 0.5, 2.6)]), c["frame"])
    for y0, y1 in ((beam0, beam1), (nuki0, nuki1)):
        beam = tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, y0, W, y1))
        tile.put(beam, c["frame"])
        tile.put(beam * (tile.y < y0 + 0.8), c["frame_light"], 0.55)
        tile.put(beam * (tile.y > y1 - 0.8), c["dark"], 0.40)
    # The two leaves of cypress.
    top = nuki1
    leaf = tile.mask(lambda p, dx, dy: _box(p, dx, dy, F + 1.6, top, W - F - 1.6, floor))
    tile.put(leaf, c["leaf"])
    tile.tone((tile.noise(2, 14, 2) - 0.5) * 0.14 * leaf)
    plank = (tile.x - F - 1.6) % 6.6
    tile.put(leaf * (plank < 0.45), c["dark"], 0.45)
    tile.put(leaf * (plank > 0.45) * (plank < 1.2), c["leaf_light"], 0.25)
    grain = np.clip(1.0 - np.abs(((tile.x + (tile.noise(8, 3, 2) - 0.5) * 3.0) % 1.4) - 0.7) / 0.12, 0, 1)
    tile.put(leaf * grain, _mix(c["leaf"], c["dark"], 0.3), 0.18)
    tile.put(leaf * (np.abs(tile.x - W * 0.5) < 0.6), c["dark"], 0.9)
    tile.put(leaf * (tile.y < top + 1.6), c["dark"], 0.4)
    for y in (top + 9.0, floor - 12.0):
        strap = tile.mask(lambda p, dx, dy: (_box(p, dx, dy, F + 1.6, y, W * 0.5 - 2.0, y + 2.4), _box(p, dx, dy, W * 0.5 + 2.0, y, W - F - 1.6, y + 2.4)))
        tile.put(strap, c["iron"])
        tile.put(strap * (tile.y < y + 0.6), _mix(c["iron"], (255, 255, 255), 0.25), 0.6)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y + 1.2, 0.5) for x in (F + 4.0, W * 0.5 - 4.0, W * 0.5 + 4.0, W - F - 4.0)]), _mix(c["iron"], (255, 255, 255), 0.35))
    for x in (W * 0.5 - 3.0, W * 0.5 + 3.0):
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, x, 80.0, 1.6)), c["iron"])
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, x - 0.4, 79.6, 0.6)), _mix(c["iron"], (255, 255, 255), 0.4))
    # The posts: round and vermilion, lit on the left, on round stones.
    for x0 in (0.0, W - F - 1.6):
        post = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0, rafter_y + 3.0, x0 + F + 1.6, floor - 3.0))
        tile.put(post, c["frame"])
        tile.put(post * np.clip(1.0 - np.abs(tile.x - x0 - 2.0) / 1.0, 0, 1), c["frame_light"], 0.6)
        tile.put(post * np.clip((tile.x - x0 - F + 0.4) / 2.0, 0, 1), c["dark"], 0.45)
        base = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(x0 - 0.6, floor), (x0 + 0.2, floor - 3.4), (x0 + F + 1.4, floor - 3.4), (x0 + F + 2.2, floor)]))
        tile.put(base, c["accent"])
        tile.put(base * (tile.y < floor - 2.6), _mix(c["accent"], (255, 255, 255), 0.35), 0.7)
    return leaf


def _dancheong(tile: Tile, c: dict, x0: float, x1: float, y0: float, y1: float) -> None:
    """A beam painted in dancheong, the colours of the palaces of Korea: a
    ground of green, and on it at each end and at even steps bands of red,
    white and blue, with a row of small round flowers in white and red."""
    beam = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0, y0, x1, y1))
    tile.put(beam, c["green"])
    step = 7.0
    u = (tile.x - x0) % step
    tile.put(beam * (u < 1.4), c["red"])
    tile.put(beam * (u >= 1.4) * (u < 1.9), c["white"])
    tile.put(beam * (u >= 1.9) * (u < 2.8), c["blue"])
    tile.put(beam * (u >= 2.8) * (u < 3.2), c["white"])
    mid = (y0 + y1) * 0.5
    flowers = [(x, mid) for x in np.arange(x0 + 5.0, x1 - 1.0, step)]
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, (y1 - y0) * 0.30) for x, y in flowers]), c["white"])
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, (y1 - y0) * 0.15) for x, y in flowers]), c["red"])
    tile.put(beam * (tile.y < y0 + 0.5), c["white"], 0.5)
    tile.put(beam * (tile.y > y1 - 0.5), c["dark"], 0.6)


def hanyang_door(tile: Tile, c: dict) -> np.ndarray:
    """The main gate of Gyeongbokgung: a base of dressed granite with an
    arched passage in it, closed by two red leaves with iron studs and
    rings, and over the base a gatehouse of wood with two roofs of grey
    tiles, one over the other, whose eaves sweep up at their corners.
    Under each eave the beams and brackets are painted in dancheong, green
    with red, blue and white. A lattice window in the upper floor shows a
    light."""
    _frame(tile, c)
    floor = H - STEP
    back = tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, 0.0, W, floor))
    tile.put(back, c["dark"])
    # The upper floor: red posts, a lattice window with its light, and a
    # painted beam, under the upper roof.
    up0, up1 = 14.0, 23.0
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, 10.0, up0, W - 10.0, up1)), _mix(c["red"], c["dark"], 0.35))
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, W * 0.5 - 12.0, up0 + 3.0, W * 0.5 + 12.0, up1 - 0.6)), c["glow"])
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x - 0.4, up0 + 3.0, x + 0.4, up1) for x in np.arange(W * 0.5 - 10.0, W * 0.5 + 11.0, 2.0)]), _mix(c["red"], c["dark"], 0.2))
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x - 1.0, up0, x + 1.0, up1) for x in (11.0, W * 0.5, W - 11.0)]), c["red"])
    _dancheong(tile, c, 10.0, W - 10.0, up0, up0 + 3.0)
    _tiled_roof(tile, c, 4.0, W - 4.0, 3.0, 14.0, 5.0, c["tile"], lane=3.4)
    # The lower roof, wider, with the painted beam and the brackets under
    # it.
    br0, br1 = 35.0, 41.0
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, 3.0, 30.0, W - 3.0, br1)), _mix(c["green"], c["dark"], 0.5))
    brackets = [x for x in np.arange(5.0, W - 3.0, 5.6)]
    tile.put(tile.mask(lambda p, dx, dy: [(_box(p, dx, dy, x - 1.6, br0, x + 1.6, br0 + 2.0), _box(p, dx, dy, x - 0.8, br0 + 2.0, x + 0.8, br1)) for x in brackets]), c["green"])
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x - 1.6, br0, x + 1.6, br0 + 0.6) for x in brackets]), c["red"])
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x - 0.8, br0 + 2.0, x + 0.8, br0 + 2.5) for x in brackets]), c["white"])
    _tiled_roof(tile, c, -1.0, W + 1.0, 21.0, 34.0, 6.0, c["tile"], lane=3.4)
    _dancheong(tile, c, 1.0, W - 1.0, br1 - 0.2, br1 + 3.6)
    # The parapet of granite on top of the base, with its low merlons.
    par0 = br1 + 3.6
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x, par0, x + 4.6, par0 + 3.0) for x in np.arange(0.6, W - 3.0, 6.4)]), c["frame"])
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x, par0, x + 4.6, par0 + 0.6) for x in np.arange(0.6, W - 3.0, 6.4)]), c["frame_light"], 0.6)
    # The granite base with the arched passage.
    base0 = par0 + 3.0
    base = tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, base0, W, floor))
    ax0, ax1 = 14.0, W - 14.0
    arch_r = (ax1 - ax0) * 0.5
    spring = base0 + 4.0 + arch_r
    passage = tile.mask(lambda p, dx, dy: (_box(p, dx, dy, ax0, spring, ax1, floor), _dot(p, dx, dy, W * 0.5, spring, arch_r)))
    stone = base * (1.0 - passage)
    _courses_of(tile, c, stone, (6.0, 6.6), (11.0, 14.0, 9.0), c["frame"], c["frame_light"])
    voussoir = tile.mask(lambda p, dx, dy: _dot(p, dx, dy, W * 0.5, spring, arch_r + 3.0)) * (tile.y < spring) * (1.0 - passage)
    tile.put(voussoir, _mix(c["frame"], c["frame_light"], 0.25))
    angle = np.arctan2(tile.y - spring, tile.x - W * 0.5)
    tile.put(voussoir * (np.abs(((angle / math.pi * 9.0) % 1.0) - 0.5) > 0.44), c["dark"], 0.55)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, W * 0.5, spring, arch_r + 3.4)) * (tile.y < spring) * (1.0 - voussoir) * (1.0 - passage) * base, c["dark"], 0.35)
    # The two red leaves in the passage.
    leaf = passage
    tile.put(leaf, c["leaf"])
    tile.tone((tile.noise(2, 12, 2) - 0.5) * 0.14 * leaf)
    plank = (tile.x - ax0) % 5.6
    tile.put(leaf * (plank < 0.45), c["dark"], 0.5)
    tile.put(leaf * (plank > 0.45) * (plank < 1.2), c["leaf_light"], 0.22)
    tile.put(leaf * (np.abs(tile.x - W * 0.5) < 0.6), c["dark"], 0.9)
    tile.put(leaf * np.clip(1.0 - (np.minimum(tile.x - ax0, ax1 - tile.x)) / 1.6, 0, 1), c["dark"], 0.45)
    for y in (spring + 4.0, floor - 22.0, floor - 8.0):
        studs = [(x, y) for x in np.arange(ax0 + 3.0, ax1 - 1.0, 4.4) if abs(x - W * 0.5) > 1.6]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, 0.9) for x, yy in studs]), c["iron"])
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x - 0.25, yy - 0.25, 0.35) for x, yy in studs]), (200, 196, 190), 0.6)
    for x in (W * 0.5 - 3.6, W * 0.5 + 3.6):
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, x, 86.0, 1.2)), c["iron"])
        tile.put(tile.mask(lambda p, dx, dy: p.ellipse([(x - 2.2) * K + dx, 86.0 * K + dy, (x + 2.2) * K + dx, 90.6 * K + dy], outline=255, width=max(1, int(0.6 * K)))), c["iron"])
    return leaf


def _qcurve(a, ctrl, b, n: int = 12) -> list[tuple[float, float]]:
    """Points along a quadratic curve from `a` to `b` that bends to `ctrl`."""
    return [((1 - t) ** 2 * a[0] + 2 * (1 - t) * t * ctrl[0] + t * t * b[0], (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * ctrl[1] + t * t * b[1]) for t in np.linspace(0.0, 1.0, n)]


def _pointed(cx: float, foot: float, half: float, spring: float, rise: float, pinch: float = 0.0) -> list[tuple[float, float]]:
    """The outline of a pointed arch: straight sides from `foot` up to
    `spring`, and two curves that meet in a point `rise` over the spring.
    `pinch` more than 0 makes a horseshoe arch, narrower at its foot."""
    left = _qcurve((cx - half, spring), (cx - half, spring - rise * 0.75), (cx, spring - rise))
    right = _qcurve((cx, spring - rise), (cx + half, spring - rise * 0.75), (cx + half, spring))
    low = half * (1.0 - pinch)
    shoulder = spring + (foot - spring) * 0.15 if pinch > 0.0 else spring
    return [(cx - low, foot), (cx - half, shoulder)] + left + right[1:] + [(cx + half, shoulder), (cx + low, foot)]


def _brickwork(tile: Tile, c: dict, mask: np.ndarray, colour: RGB, course: float = 2.6, length: float = 7.0) -> None:
    """Thin bricks laid in courses over `mask`, each half a brick along from
    the course under it, each brick of its own tone, in pale lime mortar."""
    row = np.floor(tile.y / course)
    xs = tile.x + (row % 2) * length * 0.5
    col = np.floor(xs / length)
    hashed = np.sin(row * 12.9898 + col * 78.233) * 43758.5453
    tone = (hashed - np.floor(hashed)) - 0.5
    tile.put(mask, colour)
    tile.tone(tone * 0.22 * mask)
    joints = ((tile.y % course) < 0.42) | ((xs % length) < 0.42)
    tile.put(mask * joints, c["mortar"], 0.65)


def _studded_leaves(tile: Tile, c: dict, leaf: np.ndarray, x0: float, x1: float, top: float, floor: float) -> None:
    """Two leaves of dark teak planks over `leaf`: the seams, the seam in
    the middle, and rows of round iron studs."""
    tile.put(leaf, c["leaf"])
    tile.tone((tile.noise(2, 14, 2) - 0.5) * 0.16 * leaf)
    plank = (tile.x - x0) % 5.2
    tile.put(leaf * (plank < 0.45), c["dark"], 0.5)
    tile.put(leaf * (plank > 0.45) * (plank < 1.2), c["leaf_light"], 0.20)
    tile.put(leaf * (np.abs(tile.x - W * 0.5) < 0.6), c["dark"], 0.9)
    for y in np.arange(top + 6.0, floor - 2.0, 9.0):
        studs = [(x, y) for x in np.arange(x0 + 2.6, x1 - 1.0, 4.2) if abs(x - W * 0.5) > 1.6]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, 0.8) for x, yy in studs]) * leaf, c["iron"])
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x - 0.25, yy - 0.25, 0.3) for x, yy in studs]) * leaf, (210, 200, 186), 0.6)


def _jali(tile: Tile, c: dict, cx: float, foot: float, half: float, spring: float, rise: float) -> None:
    """A small pointed window with a screen of lattice in it, and the light
    of the room behind showing through the holes."""
    outline = _pointed(cx, foot, half, spring, rise)
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(x, y) for x, y in _pointed(cx, foot + 1.2, half + 1.2, spring, rise + 1.2)])), c["frame"])
    win = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, outline))
    tile.put(win, c["glow"])
    tile.put(win * (tile.y < spring), (255, 255, 255), 0.25)
    holes = (np.abs(((tile.x - cx + tile.y) % 2.2) - 1.1) > 0.75) | (np.abs(((tile.x - cx - tile.y) % 2.2) - 1.1) > 0.75)
    tile.put(win * holes, _mix(c["leaf"], c["dark"], 0.2))


def lalbagh_door(tile: Tile, c: dict) -> np.ndarray:
    """The gate of the Lalbagh fort of Dhaka (1678): a wall of thin red
    brick, and in it a tall frame of plaster round a great pointed arch.
    Over the frame runs a parapet of rounded merlons, and a slender turret
    with a small domed top stands at each side. Two leaves of teak with
    iron studs close the arch, and a small pointed window with a lattice
    screen is in their upper part. No sign is on the gate."""
    _frame(tile, c)
    floor = H - STEP
    wall = tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, 10.0, W, floor))
    _brickwork(tile, c, wall, c["frame"])
    # The parapet: a cornice and a row of rounded merlons over it.
    cornice = tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, 12.0, W, 15.0))
    tile.put(cornice, c["plaster"])
    tile.put(cornice * (tile.y > 14.0), c["dark"], 0.35)
    merlons = [x for x in np.arange(10.0, W - 8.0, 5.4)]
    tile.put(tile.mask(lambda p, dx, dy: [(_box(p, dx, dy, x - 1.7, 7.2, x + 1.7, 12.0), _dot(p, dx, dy, x, 7.2, 1.7)) for x in merlons]), c["frame"])
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x - 1.7, 6.6, x - 0.9, 12.0) for x in merlons]), c["frame_light"], 0.45)
    # The frame of plaster round the arch, with a band of small panels.
    fx0, fx1, fy0 = 8.0, W - 8.0, 19.0
    frame = tile.mask(lambda p, dx, dy: _box(p, dx, dy, fx0, fy0, fx1, floor))
    tile.put(frame, c["plaster"])
    inner = tile.mask(lambda p, dx, dy: _box(p, dx, dy, fx0 + 2.0, fy0 + 2.0, fx1 - 2.0, floor))
    tile.put(inner, _mix(c["plaster"], c["frame"], 0.45))
    tile.put(frame * (1.0 - inner) * ((tile.y < fy0 + 0.6) | (tile.x < fx0 + 0.6)), (255, 255, 255), 0.35)
    tile.put(inner * ((tile.y < fy0 + 2.8) | (tile.x < fx0 + 2.8)), c["dark"], 0.30)
    for x in np.arange(fx0 + 6.0, fx1 - 3.0, 7.6):
        tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, _pointed(x, fy0 + 9.0, 2.0, fy0 + 6.0, 2.0))), _mix(c["frame"], c["dark"], 0.35))
    # The arch: a band of plaster round it, and the leaves in it.
    cx, half, spring, rise = W * 0.5, 15.0, 52.0, 18.0
    band = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, _pointed(cx, floor, half + 2.6, spring, rise + 2.8)))
    tile.put(band, c["plaster"])
    angle = np.arctan2(tile.y - spring, tile.x - cx)
    tile.put(band * (tile.y < spring) * (np.abs(((angle / math.pi * 14.0) % 1.0) - 0.5) > 0.44), c["dark"], 0.30)
    tile.put(band * (tile.x < cx - half), (255, 255, 255), 0.20)
    for x in (cx - half - 6.0, cx + half + 6.0):
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, x, spring - rise * 0.55, 2.4)), c["plaster"])
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, x, spring - rise * 0.55, 1.2)), c["frame"])
    leaf = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, _pointed(cx, floor, half, spring, rise)))
    _studded_leaves(tile, c, leaf, cx - half, cx + half, spring - rise, floor)
    tile.put(leaf * np.clip(1.0 - (tile.y - (spring - rise)) / 3.0, 0, 1), c["dark"], 0.5)
    _jali(tile, c, cx, spring + 8.0, 5.0, spring - 2.0, 6.0)
    for x in (cx - 3.6, cx + 3.6):
        tile.put(tile.mask(lambda p, dx, dy: p.ellipse([(x - 1.9) * K + dx, 84.0 * K + dy, (x + 1.9) * K + dx, 88.0 * K + dy], outline=255, width=max(1, int(0.6 * K)))), c["iron"])
    # The turrets at the two sides, each with a small dome and a knob.
    for x in (4.0, W - 4.0):
        shaft = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x - 2.6, 9.0, x + 2.6, floor))
        tile.put(shaft, c["frame"])
        tile.put(shaft * (tile.x < x - 1.2), c["frame_light"], 0.40)
        tile.put(shaft * (tile.x > x + 1.4), c["dark"], 0.30)
        tile.put(shaft * (np.abs(((tile.y - 9.0) % 14.0) - 7.0) > 6.2), c["plaster"], 0.8)
        dome = tile.mask(lambda p, dx, dy: (_dot(p, dx, dy, x, 8.0, 3.2, ry=3.0), _box(p, dx, dy, x - 3.4, 8.0, x + 3.4, 9.6), _box(p, dx, dy, x - 0.35, 2.4, x + 0.35, 5.6), _dot(p, dx, dy, x, 2.4, 0.8)))
        tile.put(dome, c["plaster"])
        tile.put(dome * (tile.x > x + 0.8), c["dark"], 0.25)
    return leaf


def company_gate_door(tile: Tile, c: dict) -> np.ndarray:
    """A gateway of a house of the Company in Calcutta, of white lime
    plaster: two pilasters with plain capitals, an entablature and a low
    pediment over them, and between them a round arch with a keystone. A
    fanlight of glass with bars like the rays of the sun fills the round
    of the arch, and under it are two leaves of green louvred shutters,
    as the houses of Calcutta had against the sun and the rain. The rains
    have left a damp stain at the foot of the wall."""
    _frame(tile, c)
    floor = H - STEP
    wall = tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, 16.0, W, floor))
    tile.put(wall, c["plaster"])
    tile.tone((tile.noise(6, 12, 3) - 0.5) * 0.08 * wall)
    tile.put(wall * np.clip((tile.y - (floor - 16.0)) / 16.0, 0, 1) * (0.6 + 0.4 * tile.noise(8, 2, 2)), c["damp"], 0.55)
    # The pediment and the entablature, on a plain parapet wall.
    parapet = tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, 0.0, W, 16.0))
    tile.put(parapet, _mix(c["plaster"], c["dark"], 0.18))
    tile.put(parapet * (tile.y < 1.0), _mix(c["plaster"], (255, 255, 255), 0.3))
    ped = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(1.0, 16.0), (W * 0.5, 4.0), (W - 1.0, 16.0)]))
    tile.put(ped, c["plaster"])
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(6.0, 14.6), (W * 0.5, 6.8), (W - 6.0, 14.6)])), _mix(c["plaster"], c["dark"], 0.12))
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(0.0, 16.4), (W * 0.5, 3.4), (W, 16.4)], 1.2)), (255, 255, 255), 0.6)
    for y0, y1, tone in ((16.0, 19.0, 0.0), (19.0, 24.0, -0.08), (24.0, 26.0, 0.0)):
        band = tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, y0, W, y1))
        tile.put(band, _mix(c["plaster"], c["dark"], -tone) if tone < 0 else c["plaster"])
        tile.put(band * (tile.y > y1 - 0.6), c["dark"], 0.30)
    # The pilasters, with a capital and a base.
    for x0 in (1.0, W - 10.0):
        pil = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0, 26.0, x0 + 9.0, floor))
        tile.put(pil, _mix(c["plaster"], (255, 255, 255), 0.25))
        tile.put(pil * (tile.x > x0 + 7.4), c["dark"], 0.18)
        tile.put(pil * (tile.x < x0 + 1.2), (255, 255, 255), 0.35)
        for y0, y1 in ((26.0, 29.0), (floor - 4.0, floor)):
            tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 - 0.8, y0, x0 + 9.8, y1)), c["plaster"])
            tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 - 0.8, y1 - 0.6, x0 + 9.8, y1)), c["dark"], 0.30)
    # The arch: its moulding, its keystone, and the fanlight in its round.
    cx, r, spring = W * 0.5, 19.0, 54.0
    x0, x1 = cx - r, cx + r
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, cx, spring, r + 3.0)) * (tile.y < spring), _mix(c["plaster"], (255, 255, 255), 0.3))
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, cx, spring, r + 0.8)) * (tile.y < spring), c["dark"], 0.35)
    fan = tile.mask(lambda p, dx, dy: _dot(p, dx, dy, cx, spring, r)) * (tile.y < spring)
    tile.put(fan, c["glow"])
    tile.put(fan * (tile.y < spring - r * 0.6), (255, 255, 255), 0.25)
    angle = np.arctan2(tile.y - spring, tile.x - cx)
    dist = np.sqrt((tile.x - cx) ** 2 + (tile.y - spring) ** 2)
    rays = np.abs(((angle / math.pi * 8.0) % 1.0) - 0.5) > 0.40
    tile.put(fan * (rays | (np.abs(dist - r * 0.45) < 0.5) | (dist < r * 0.18) | (dist > r - 0.9)), c["leaf"])
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(cx - 2.6, spring - r - 3.4), (cx + 2.6, spring - r - 3.4), (cx + 1.8, spring - r + 1.6), (cx - 1.8, spring - r + 1.6)])), _mix(c["plaster"], (255, 255, 255), 0.4))
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, cx - 2.6, spring - r - 3.4, cx + 2.6, spring - r - 2.8)), c["dark"], 0.25)
    # The impost: a band at the spring of the arch.
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 - 2.4, spring - 0.2, x1 + 2.4, spring + 2.0)), c["plaster"])
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 - 2.4, spring + 1.4, x1 + 2.4, spring + 2.0)), c["dark"], 0.35)
    # The two leaves: green shutters with louvres in two panels each.
    top = spring + 2.0
    leaf = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0, top, x1, floor))
    tile.put(leaf, c["leaf"])
    stile = (np.abs(tile.x - x0 - 1.0) < 1.0) | (np.abs(tile.x - x1 + 1.0) < 1.0) | (np.abs(tile.x - cx) < 1.4)
    rail = (np.abs(tile.y - top - 1.0) < 1.0) | (np.abs(tile.y - (top + floor) * 0.5) < 1.0) | (np.abs(tile.y - floor + 1.0) < 1.0)
    slat = (tile.y - top) % 2.0
    tile.put(leaf * (~stile) * (~rail) * (slat < 0.8), c["leaf_light"], 0.45)
    tile.put(leaf * (~stile) * (~rail) * (slat > 1.4), c["dark"], 0.45)
    tile.put(leaf * stile, _mix(c["leaf"], c["dark"], 0.10))
    tile.put(leaf * (np.abs(tile.x - cx) < 0.3), c["dark"], 0.9)
    tile.put(leaf * np.clip(1.0 - (tile.y - top) / 2.0, 0, 1), c["dark"], 0.45)
    for x in (cx - 3.0, cx + 3.0):
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x - 0.5, 84.0, x + 0.5, 90.0)), c["brass"])
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x - 0.5, 84.0, x - 0.1, 90.0)), (255, 240, 190), 0.6)
    return leaf


def curzon_door(tile: Tile, c: dict) -> np.ndarray:
    """A door of Curzon Hall of Dhaka (1904): a wall of red brick with
    bands of pale stone, a frame of pale stone, and in it a pointed arch of
    the horseshoe kind whose voussoirs are red brick and pale stone in
    turn. Over the frame runs a row of small blind arches under a parapet,
    and a small domed kiosk with a plain knob stands at each corner. Two
    leaves of dark wood with panels close the arch, with a small pointed
    window of coloured glass in their upper part."""
    _frame(tile, c)
    floor = H - STEP
    wall = tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, 0.0, W, floor))
    _brickwork(tile, c, wall, c["frame"], 2.4, 6.4)
    for y0 in (24.0, 36.0):
        band = tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, y0, W, y0 + 2.2))
        tile.put(band, c["stone"])
        tile.put(band * (tile.y > y0 + 1.6), c["dark"], 0.30)
    # The parapet and the row of small blind arches under it.
    par = tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, 14.0, W, 16.4))
    tile.put(par, c["stone"])
    tile.put(par * (tile.y > 15.8), c["dark"], 0.3)
    merlons = [x for x in np.arange(11.0, W - 9.0, 4.4)]
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x - 1.2, 10.8, x + 1.2, 14.0) for x in merlons]), c["frame"])
    for x in np.arange(10.0, W - 6.0, 6.2):
        tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, _pointed(x, 23.0, 1.8, 19.6, 2.4))), _mix(c["frame"], c["dark"], 0.45))
    # The frame of pale stone round the arch.
    fx0, fx1, fy0 = 9.0, W - 9.0, 40.0
    frame = tile.mask(lambda p, dx, dy: _box(p, dx, dy, fx0, fy0, fx1, floor))
    inner = tile.mask(lambda p, dx, dy: _box(p, dx, dy, fx0 + 2.0, fy0 + 2.0, fx1 - 2.0, floor))
    tile.put(frame * (1.0 - inner), c["stone"])
    tile.put(frame * (1.0 - inner) * (tile.x < fx0 + 0.6), (255, 255, 255), 0.35)
    tile.put(inner, _mix(c["frame"], c["dark"], 0.10))
    # The arch: voussoirs of brick and stone in turn, and the leaves.
    cx, half, spring, rise = W * 0.5, 15.0, 64.0, 15.0
    ring = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, _pointed(cx, floor, half + 3.4, spring, rise + 3.6, 0.10)))
    angle = np.arctan2(tile.y - spring, tile.x - cx)
    stripes = np.abs(((angle / math.pi * 13.0) % 1.0) - 0.5) < 0.25
    tile.put(ring, c["stone"])
    tile.put(ring * stripes * (tile.y < spring), c["frame"])
    tile.put(ring * (tile.y >= spring) * (np.abs(((tile.y - spring) % 6.0) - 3.0) < 1.5), c["frame"])
    tile.put(ring * (tile.x < cx - half - 1.8), (255, 255, 255), 0.18)
    leaf = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, _pointed(cx, floor, half, spring, rise, 0.10)))
    tile.put(leaf, c["leaf"])
    tile.tone((tile.noise(2, 12, 2) - 0.5) * 0.14 * leaf)
    tile.put(leaf * (np.abs(tile.x - cx) < 0.6), c["dark"], 0.9)
    for py0, py1 in ((spring + 12.0, spring + 27.0), (spring + 31.0, floor - 4.0)):
        for px0, px1 in ((cx - half + 3.0, cx - 2.4), (cx + 2.4, cx + half - 3.0)):
            panel = tile.mask(lambda p, dx, dy: _box(p, dx, dy, px0, py0, px1, py1))
            tile.put(panel * (1.0 - tile.mask(lambda p, dx, dy: _box(p, dx, dy, px0 + 0.7, py0 + 0.7, px1 - 0.7, py1 - 0.7))), c["dark"], 0.45)
            tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, px0 + 0.7, py0 + 0.7, px1 - 0.7, py0 + 1.2)), c["leaf_light"], 0.30)
    tile.put(leaf * np.clip(1.0 - (tile.y - (spring - rise)) / 3.0, 0, 1), c["dark"], 0.5)
    win = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, _pointed(cx, spring + 8.0, 4.4, spring - 1.0, 5.6)))
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, _pointed(cx, spring + 9.0, 5.6, spring - 1.0, 7.0))), c["stone"])
    tile.put(win, c["glow"])
    tile.put(win * (tile.y < spring + 1.0), (255, 255, 255), 0.25)
    tile.put(win * (np.abs(tile.x - cx) < 0.35), c["dark"], 0.8)
    tile.put(win * (np.abs(tile.y - (spring + 3.0)) < 0.35), c["dark"], 0.8)
    tile.put(win * (tile.x < cx) * (tile.y > spring + 3.0), c["glass"], 0.35)
    for x in (cx - 3.0, cx + 3.0):
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, x, 92.0, 0.9)), c["brass"])
    # The kiosks at the two corners.
    for x in (5.0, W - 5.0):
        post = tile.mask(lambda p, dx, dy: (_box(p, dx, dy, x - 3.6, 9.8, x + 3.6, 11.0), _box(p, dx, dy, x - 3.0, 6.0, x - 1.8, 10.0), _box(p, dx, dy, x + 1.8, 6.0, x + 3.0, 10.0)))
        tile.put(post, c["stone"])
        dome = tile.mask(lambda p, dx, dy: (_dot(p, dx, dy, x, 5.4, 3.4, ry=3.0), _box(p, dx, dy, x - 3.8, 5.2, x + 3.8, 6.2), _box(p, dx, dy, x - 0.3, 1.4, x + 0.3, 3.0), _dot(p, dx, dy, x, 1.4, 0.7)))
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x - 1.8, 6.2, x + 1.8, 9.8)), c["dark"], 0.8)
        tile.put(dome, c["stone"])
        tile.put(dome * (tile.x > x + 0.8), c["dark"], 0.25)
        tile.put(dome * (np.abs(tile.x - x) < 0.3) * (tile.y > 2.6), c["frame"], 0.6)
    return leaf


def _marajoara_band(tile: Tile, c: dict, mask: np.ndarray, x0: float, x1: float, y0: float, y1: float) -> None:
    """A band painted in the manner of Marajoara pottery over `mask`: a
    white slip with a red border at the top and the foot, and between them
    a black meander of steps and a row of small red dots."""
    band = mask * tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0, y0, x1, y1))
    tile.put(band, c["slip"])
    tile.put(band * ((tile.y < y0 + 1.0) | (tile.y > y1 - 1.0)), c["paint_red"])
    mid = (y0 + y1) * 0.5
    step = (y1 - y0) * 0.30
    pts = []
    x = x0
    k = 0
    while x < x1:
        pts += [(x, mid + step if k % 2 else mid - step), (x + 2.4, mid + step if k % 2 else mid - step)]
        x += 2.4
        k += 1
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, pts, 0.55)) * band, c["paint_black"])
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, xx, mid, 0.35) for xx in np.arange(x0 + 3.6, x1 - 1.0, 4.8)]) * band, c["paint_red"])


def longhouse_door(tile: Tile, c: dict) -> np.ndarray:
    """The doorway of a big house of thatch on a mound of Marajó, about
    1000 CE. The roof of palm thatch comes down almost to the ground, so
    it fills the frame. The doorway is cut into it and framed by posts of
    palm wood, with a lintel painted in the manner of Marajoara pottery. A
    mat woven of palm leaf hangs in it. The light of the fire shows through
    a gap high in the roof."""
    inner = _frame(tile, c)
    floor = H - STEP
    _thatch_roof(tile, c, inner, (W * 0.5, -36.0), 5.0)
    # The low wall of palm stems at each side, where the roof meets the
    # ground.
    for x0, x1 in ((F, 14.0), (W - 14.0, W - F)):
        wall = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0, floor - 18.0, x1, floor)) * inner
        tile.put(wall, c["wall"])
        tile.put(wall * (np.abs(((tile.x - x0) % 2.2) - 1.1) < 0.25), c["dark"], 0.45)
        tile.put(wall * (tile.y < floor - 16.6), c["dark"], 0.5)
    # The doorway: dark, between two posts, under a painted lintel.
    x0, x1, top = 17.0, W - 17.0, 58.0
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 - 3.0, top - 7.0, x1 + 3.0, top - 2.0), blur=1.0), (0, 0, 0), 0.35)
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0, top, x1, floor)), c["dark"])
    for px in (x0 - 3.0, x1):
        post = tile.mask(lambda p, dx, dy: _box(p, dx, dy, px, top - 4.0, px + 3.0, floor))
        tile.put(post, c["frame"])
        tile.put(post * (tile.x < px + 1.0), c["frame_light"], 0.5)
        tile.put(post * np.clip((tile.noise(2, 16, 2) - 0.5) * 3.0, 0, 1), c["dark"], 0.35)
    lintel = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 - 5.0, top - 7.0, x1 + 5.0, top))
    tile.put(lintel, c["frame"])
    _marajoara_band(tile, c, lintel, x0 - 4.0, x1 + 4.0, top - 6.2, top - 0.8)
    # The mat: strips of palm leaf woven in a twill, so the weave makes
    # small steps, with a pole at its foot. It is the leaf.
    leaf = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 1.0, top + 1.0, x1 - 1.0, floor - 0.6))
    tile.put(leaf, c["leaf"])
    twill = ((np.floor((tile.x - x0) / 1.8) + np.floor((tile.y - top) / 1.8) * 2) % 4 < 2)
    tile.put(leaf * twill, c["leaf_light"], 0.40)
    tile.put(leaf * ~twill, c["dark"], 0.18)
    tile.put(leaf * (np.abs(((tile.y - top) % 9.0)) < 0.35), c["dark"], 0.30)
    pole = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 0.4, floor - 3.4, x1 - 0.4, floor - 1.4))
    tile.put(pole, c["frame"])
    tile.put(pole * (tile.y < floor - 2.8), c["frame_light"], 0.5)
    # The gap high in the roof, lit by the fire inside.
    _window(tile, c, W * 0.5 - 5.0, 20.0, W * 0.5 + 5.0, 26.0)
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(W * 0.5 - 8.0, 20.0), (W * 0.5, 13.0), (W * 0.5 + 8.0, 20.0), (W * 0.5 + 6.0, 20.6), (W * 0.5 - 6.0, 20.6)])), _mix(c["thatch"], c["dark"], 0.2))
    return leaf


def palisade_gate_door(tile: Tile, c: dict) -> np.ndarray:
    """A gate in the palisade of a village of Palmares, about 1680. Logs
    cut to a point stand side by side and fill the frame. A heavy beam
    lies over the gate on two thick posts. The gate is two leaves of
    logs lashed to cross bars with cord of palm fibre, and a small hole
    in it, high up, shows the light of the village behind."""
    _frame(tile, c)
    floor = H - STEP
    # The palisade: logs side by side, each with its own height and tone.
    x = F - 1.0
    k = 0
    while x < W - F:
        w = 4.6 + (k % 3) * 0.5
        tip = 12.0 + (k * 7 % 5) * 1.4
        log = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(x, floor), (x, tip + 3.0), (x + w * 0.5, tip), (x + w, tip + 3.0), (x + w, floor)]))
        tile.put(log, _mix(c["frame"], c["dark"], 0.10 * (k % 3)))
        tile.put(log * (tile.x < x + 1.2), c["frame_light"], 0.40)
        tile.put(log * (tile.x > x + w - 0.8), c["dark"], 0.45)
        tile.put(log * np.clip((tile.noise(3, 24, 2) - 0.5) * 3.0, 0, 1), c["dark"], 0.30)
        x += w
        k += 1
    # A band of cord lashed round the logs.
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, F, 26.0, W - F, 28.0)), c["cord"])
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(xx, 26.0), (xx + 0.8, 28.0)], 0.25) for xx in np.arange(F, W - F, 1.2)]), c["dark"], 0.35)
    # The posts and the beam over the gate.
    gx0, gx1, top = 13.0, W - 13.0, 44.0
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, gx0, top, gx1, floor)), c["dark"])
    for px in (gx0 - 5.0, gx1):
        post = tile.mask(lambda p, dx, dy: _box(p, dx, dy, px, top - 8.0, px + 5.0, floor))
        tile.put(post, _mix(c["frame"], c["dark"], 0.25))
        tile.put(post * (tile.x < px + 1.6), c["frame_light"], 0.45)
        tile.put(post * (tile.x > px + 4.0), c["dark"], 0.45)
    beam = tile.mask(lambda p, dx, dy: (_box(p, dx, dy, gx0 - 8.0, top - 8.0, gx1 + 8.0, top - 3.0), _dot(p, dx, dy, gx0 - 8.0, top - 5.5, 2.5), _dot(p, dx, dy, gx1 + 8.0, top - 5.5, 2.5)))
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, gx0 - 8.0, top - 3.0, gx1 + 8.0, top - 0.6), blur=0.8), (0, 0, 0), 0.40)
    tile.put(beam, c["frame"])
    tile.put(beam * (tile.y < top - 6.8), c["frame_light"], 0.5)
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, xx, top - 5.5, 1.5) for xx in (gx0 - 8.0, gx1 + 8.0)]), _mix(c["frame_light"], (240, 220, 180), 0.4))
    for px in (gx0 - 2.5, gx1 + 2.5):
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(px - 3.0, top - 7.6 + j * 0.9), (px + 3.0, top - 3.6 + j * 0.9)], 0.35) for j in range(3)]), c["cord"])
    # The leaves: logs side by side, with two cross bars lashed on.
    leaf = tile.mask(lambda p, dx, dy: _box(p, dx, dy, gx0 + 0.6, top + 0.6, gx1 - 0.6, floor - 0.4))
    tile.put(leaf, c["leaf"])
    lane = (tile.x - gx0) % 4.3
    tile.put(leaf * (lane < 0.5), c["dark"], 0.6)
    tile.put(leaf * (lane > 0.5) * (lane < 1.4), c["leaf_light"], 0.35)
    tile.put(leaf * (np.abs(tile.x - W * 0.5) < 0.45), c["dark"], 0.8)
    for yy in (top + 14.0, floor - 16.0):
        bar = tile.mask(lambda p, dx, dy: _box(p, dx, dy, gx0 + 1.0, yy, gx1 - 1.0, yy + 3.2)) * leaf
        tile.put(bar, _mix(c["leaf"], c["dark"], 0.30))
        tile.put(bar * (tile.y < yy + 0.9), c["leaf_light"], 0.45)
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(xx - 0.8, yy - 0.4), (xx + 0.8, yy + 3.6)], 0.30) for xx in np.arange(gx0 + 3.0, gx1 - 2.0, 4.3)]) * leaf, c["cord"])
    _window(tile, c, W * 0.5 - 3.0, top + 5.0, W * 0.5 + 3.0, top + 9.0)
    return leaf


def azulejo_door(tile: Tile, c: dict) -> np.ndarray:
    """The door of a town house of Rio de Janeiro in 1888. The front of the
    house is faced with glazed tiles, blue on white, in a small pattern of
    four-petalled stars. A frame of grey granite with a cornice goes round
    the doorway. The door is of wood painted green, two leaves with
    raised panels, and over it a fanlight with bars of iron like the rays
    of the sun."""
    _frame(tile, c)
    floor = H - STEP
    wall = tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, 0.0, W, floor))
    tile.put(wall, c["tile_white"])
    # The tiles: a grid of squares of four units, each with a blue star
    # of four petals at its middle and a quarter flower at each corner.
    gx = (tile.x % 4.0) - 2.0
    gy = (tile.y % 4.0) - 2.0
    star = (np.abs(gx) * np.abs(gy) < 0.30) & (np.abs(gx) + np.abs(gy) < 1.7)
    corner = (np.abs(gx) > 1.45) & (np.abs(gy) > 1.45)
    tile.put(wall * (star | corner), c["tile_blue"])
    tile.put(wall * ((np.abs(gx) > 1.86) | (np.abs(gy) > 1.86)), _mix(c["tile_white"], c["dark"], 0.25), 0.6)
    tile.tone((tile.noise(10, 10, 2) - 0.5) * 0.06 * wall)
    # The granite frame, with a cornice that juts out, and its shade.
    fx0, fx1, ftop = 8.0, W - 8.0, 22.0
    frame = tile.mask(lambda p, dx, dy: _box(p, dx, dy, fx0, ftop, fx1, floor))
    tile.put(frame, c["stone"])
    tile.put(frame * np.clip((tile.noise(14, 14, 2) - 0.5) * 2.5, 0, 1), c["dark"], 0.18)
    cornice = tile.mask(lambda p, dx, dy: _box(p, dx, dy, fx0 - 4.0, ftop - 5.0, fx1 + 4.0, ftop))
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, fx0 - 4.0, ftop, fx1 + 4.0, ftop + 2.2), blur=0.8), (0, 0, 0), 0.35)
    tile.put(cornice, c["stone"])
    tile.put(cornice * (tile.y < ftop - 4.2), (255, 255, 255), 0.45)
    tile.put(cornice * (tile.y > ftop - 1.2), c["dark"], 0.30)
    tile.put(frame * (tile.x < fx0 + 0.8), (255, 255, 255), 0.30)
    # The opening: a fanlight at the top and the green leaves under it.
    ox0, ox1, otop = fx0 + 4.0, fx1 - 4.0, ftop + 4.0
    fan_foot = otop + 14.0
    fan = tile.mask(lambda p, dx, dy: _box(p, dx, dy, ox0, otop, ox1, fan_foot))
    tile.put(fan, c["glow"])
    tile.put(fan * (tile.y < otop + 4.0), (255, 255, 255), 0.25)
    cx = W * 0.5
    rays = tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(cx, fan_foot), (cx + math.cos(a) * 30.0, fan_foot - math.sin(a) * 30.0)], 0.45) for a in np.linspace(0.15, math.pi - 0.15, 7)])
    tile.put(rays * fan, c["iron"])
    tile.put(tile.mask(lambda p, dx, dy: p.ellipse([(cx - 6.0) * K + dx, (fan_foot - 6.0) * K + dy, (cx + 6.0) * K + dx, (fan_foot + 6.0) * K + dy], outline=255, width=max(1, int(0.5 * K)))) * fan, c["iron"])
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, ox0, fan_foot, ox1, fan_foot + 1.6)), c["stone"])
    leaf = tile.mask(lambda p, dx, dy: _box(p, dx, dy, ox0, fan_foot + 1.6, ox1, floor))
    tile.put(leaf, c["leaf"])
    tile.put(leaf * (np.abs(tile.x - cx) < 0.45), c["dark"], 0.8)
    for side in (-1.0, 1.0):
        for y0, y1 in ((fan_foot + 5.0, fan_foot + 30.0), (fan_foot + 34.0, floor - 5.0)):
            xa, xb = (ox0 + 3.0, cx - 3.0) if side < 0 else (cx + 3.0, ox1 - 3.0)
            panel = tile.mask(lambda p, dx, dy: _box(p, dx, dy, xa, y0, xb, y1))
            tile.put(panel, c["leaf_light"], 0.35)
            tile.put(panel * ((tile.x < xa + 0.8) | (tile.y < y0 + 0.8)), c["dark"], 0.35)
            tile.put(panel * ((tile.x > xb - 0.8) | (tile.y > y1 - 0.8)), (255, 255, 255), 0.25)
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, cx + side * 2.0, fan_foot + 32.0, 0.8) for side in (-1.0, 1.0)]), c["brass"])
    return leaf


def _shingles(tile: Tile, c: dict, x0: float, x1: float, ridge: float, eave: float) -> np.ndarray:
    """A small gable roof of wooden shingles seen from the front, from `x0`
    to `x1`: a straight eave at `eave`, rows of thin shingles that overlap
    down the slope, each row a half shingle along from the one over it,
    and a ridge board along the top at `ridge`. Returns the mask of the
    roof."""
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0, ridge + 2.0, x1, eave + 3.0), blur=1.0), (0, 0, 0), 0.40)
    roof = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(x0 + 2.5, ridge), (x1 - 2.5, ridge), (x1, eave), (x0, eave)]))
    tile.put(roof, c["shingle"])
    row = np.floor((tile.y - ridge) / 1.8)
    xs = tile.x + (row % 2) * 1.4
    hashed = np.sin(row * 12.9898 + np.floor(xs / 2.8) * 78.233) * 43758.5453
    tile.tone(((hashed - np.floor(hashed)) - 0.5) * 0.20 * roof)
    tile.put(roof * (((tile.y - ridge) % 1.8) > 1.45), c["dark"], 0.45)
    tile.put(roof * ((xs % 2.8) < 0.35), c["dark"], 0.30)
    tile.put(roof * (((tile.y - ridge) % 1.8) < 0.35), _mix(c["shingle"], (255, 244, 220), 0.35), 0.45)
    # The edge of the eave is a thick board, and the ridge has a board on
    # its top with a small cap at each end.
    fascia = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 - 0.6, eave - 1.6, x1 + 0.6, eave + 0.6))
    tile.put(fascia, c["frame"])
    tile.put(fascia * (tile.y < eave - 1.0), c["frame_light"], 0.5)
    cap = tile.mask(lambda p, dx, dy: (_box(p, dx, dy, x0 + 1.5, ridge - 2.6, x1 - 1.5, ridge + 0.6), _box(p, dx, dy, x0 + 0.8, ridge - 3.4, x0 + 3.0, ridge + 0.6),
                                       _box(p, dx, dy, x1 - 3.0, ridge - 3.4, x1 - 0.8, ridge + 0.6)))
    tile.put(cap, _mix(c["shingle"], c["dark"], 0.40))
    tile.put(cap * (tile.y < ridge - 1.8), c["frame_light"], 0.35)
    return roof


def kamakura_gate_door(tile: Tile, c: dict) -> np.ndarray:
    """The gate of the house of a warrior of Kyushu in the Kamakura
    period. Two square posts of plain wood stand on round stones, with a
    tie beam across them, and over them a small gable roof of wooden
    shingles. Between the tie beam and the head of the gate is a window of
    upright bars, with the light of the house behind it. The two leaves
    are of plain planks with two battens each. A fence of upright boards
    with a top rail goes off at each side."""
    _frame(tile, c)
    floor = H - STEP
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, 0.0, W, floor)), c["dark"])
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, 0.0, W, floor)) * np.clip(1.0 - tile.y / 60.0, 0, 1), c["frame"], 0.25)
    # The fence: upright boards, each of its own tone, under a top rail.
    px0, px1 = 11.0, W - 11.0
    for x0, x1 in ((0.0, px0), (px1, W)):
        fence = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0, 46.0, x1, floor))
        lane = np.floor(tile.x / 2.6)
        hashed = np.sin(lane * 12.9898) * 43758.5453
        tile.put(fence, c["fence"])
        tile.tone(((hashed - np.floor(hashed)) - 0.5) * 0.22 * fence)
        tile.put(fence * ((tile.x % 2.6) < 0.35), c["dark"], 0.6)
        tile.put(fence * np.clip((tile.noise(3, 20, 2) - 0.5) * 2.0, 0, 1), c["dark"], 0.18)
        rail = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0, 43.0, x1, 46.4))
        tile.put(rail, c["frame"])
        tile.put(rail * (tile.y < 43.8), c["frame_light"], 0.5)
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0, 46.4, x1, 47.6), blur=0.4) * fence, (0, 0, 0), 0.35)
    # The window of upright bars between the tie beam and the head.
    gx0, gx1 = px0 + 4.5, px1 - 4.5
    win = tile.mask(lambda p, dx, dy: _box(p, dx, dy, gx0, 33.0, gx1, 41.0))
    tile.put(win, c["glow"])
    tile.put(win * (tile.y < 35.0), (255, 255, 255), 0.25)
    tile.put(win * ((np.abs(((tile.x - gx0) % 2.8) - 1.4)) > 0.85), c["frame"])
    # The tie beam and the head beam across the posts.
    for y0, y1, x0, x1 in ((28.0, 33.0, px0 - 2.0, px1 + 2.0), (41.0, 44.6, gx0, gx1)):
        beam = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0, y0, x1, y1))
        tile.put(beam, c["frame"])
        tile.put(beam * (tile.y < y0 + 0.8), c["frame_light"], 0.55)
        tile.put(beam * (tile.y > y1 - 0.8), c["dark"], 0.40)
    # The roof of shingles over the posts.
    _shingles(tile, c, px0 - 9.0, px1 + 9.0, 6.0, 24.0)
    # The leaves: plain planks, the seam in the middle, two battens.
    top = 44.6
    leaf = tile.mask(lambda p, dx, dy: _box(p, dx, dy, gx0, top, gx1, floor))
    tile.put(leaf, c["leaf"])
    tile.tone((tile.noise(2, 14, 2) - 0.5) * 0.16 * leaf)
    plank = (tile.x - gx0) % 4.0
    tile.put(leaf * (plank < 0.40), c["dark"], 0.50)
    tile.put(leaf * (plank > 0.40) * (plank < 1.1), c["leaf_light"], 0.25)
    grain = np.clip(1.0 - np.abs(((tile.x + (tile.noise(8, 3, 2) - 0.5) * 3.0) % 1.3) - 0.65) / 0.12, 0, 1)
    tile.put(leaf * grain, _mix(c["leaf"], c["dark"], 0.3), 0.15)
    tile.put(leaf * (np.abs(tile.x - W * 0.5) < 0.6), c["dark"], 0.9)
    tile.put(leaf * (tile.y < top + 1.4), c["dark"], 0.4)
    for y in (top + 10.0, floor - 14.0):
        for x0, x1 in ((gx0 + 1.0, W * 0.5 - 1.6), (W * 0.5 + 1.6, gx1 - 1.0)):
            batten = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0, y, x1, y + 3.0))
            tile.put(batten, _mix(c["leaf"], c["dark"], 0.25))
            tile.put(batten * (tile.y < y + 0.7), c["leaf_light"], 0.45)
            tile.put(batten * (tile.y > y + 2.4), c["dark"], 0.35)
            tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y + 1.5, 0.45) for x in np.arange(x0 + 2.0, x1 - 1.0, 4.0)]), c["dark"], 0.75)
    for x in (W * 0.5 - 3.0, W * 0.5 + 3.0):
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x - 0.6, 74.0, x + 0.6, 82.0)), c["frame"])
    # The posts, square and plain, on round stones.
    for x0 in (px0, px1 - 4.5):
        post = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0, 24.0, x0 + 4.5, floor - 2.6))
        tile.put(post, c["frame"])
        tile.put(post * (tile.x < x0 + 1.2), c["frame_light"], 0.5)
        tile.put(post * (tile.x > x0 + 3.4), c["dark"], 0.45)
        tile.put(post * np.clip((tile.noise(2, 18, 2) - 0.5) * 2.0, 0, 1), c["dark"], 0.20)
        stone = tile.mask(lambda p, dx, dy: _dot(p, dx, dy, x0 + 2.25, floor - 1.0, 4.0, ry=2.4)) * (tile.y < floor)
        tile.put(stone, c["accent"])
        tile.put(stone * (tile.y < floor - 2.4), _mix(c["accent"], (255, 255, 255), 0.35), 0.7)
    return leaf


def _flemish(tile: Tile, c: dict, mask: np.ndarray, course: float = 2.4) -> None:
    """Red brick over `mask` in Flemish bond: in each course a long brick
    and a short end in turn, each end over the middle of a long brick of the
    course under it. The ends are a little darker. Pale lime mortar."""
    row = np.floor(tile.y / course)
    period = course * 3.0
    xs = tile.x + (row % 2) * period * 0.5
    phase = xs % period
    header = phase > course * 2.0
    col = np.floor(xs / period) * 2 + header
    hashed = np.sin(row * 12.9898 + col * 78.233) * 43758.5453
    tile.put(mask, c["brick"])
    tile.tone((((hashed - np.floor(hashed)) - 0.5) * 0.24 - header * 0.14) * mask)
    joints = ((tile.y % course) < 0.38) | (phase < 0.38) | (np.abs(phase - course * 2.0) < 0.19)
    tile.put(mask * joints, c["mortar"], 0.75)


def bricktown_door(tile: Tile, c: dict) -> np.ndarray:
    """The door of a shop of the Ginza Bricktown in Tokyo, 1872. It is under
    the colonnade on the street: a white column at each side, and over them
    the beam of the verandah in white stucco with its cornice. The wall is
    of red brick in Flemish bond. A surround of white stucco frames the
    doorway, with a fanlight of small panes over it. The door is two leaves
    of varnished wood, each glazed with small panes in its upper part, with
    a panel under the glass, and a brass knob."""
    _frame(tile, c)
    floor = H - STEP
    wall = tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, 0.0, W, floor))
    _flemish(tile, c, wall)
    # The shade of the verandah on the top of the wall.
    tile.put(wall * np.clip(1.0 - (tile.y - 16.0) / 18.0, 0, 1), (0, 0, 0), 0.35)
    # The surround of the doorway, the fanlight, and the opening.
    ox0, ox1, otop = 15.0, W - 15.0, 26.0
    surround = tile.mask(lambda p, dx, dy: _box(p, dx, dy, ox0 - 3.0, otop - 4.0, ox1 + 3.0, floor))
    tile.put(surround, c["stucco"])
    tile.put(surround * (tile.x < ox0 - 2.2), (255, 255, 255), 0.35)
    tile.put(surround * (tile.x > ox1 + 2.2), c["dark"], 0.25)
    key = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(W * 0.5 - 2.4, otop - 4.6), (W * 0.5 + 2.4, otop - 4.6), (W * 0.5 + 1.6, otop + 0.6), (W * 0.5 - 1.6, otop + 0.6)]))
    tile.put(key, _mix(c["stucco"], c["dark"], 0.12))
    fan_foot = otop + 9.0
    fan = tile.mask(lambda p, dx, dy: _box(p, dx, dy, ox0, otop, ox1, fan_foot))
    tile.put(fan, c["glow"])
    tile.put(fan * (tile.y < otop + 3.0), (255, 255, 255), 0.25)
    tile.put(fan * ((np.abs(((tile.x - ox0) % ((ox1 - ox0) / 5.0)) - (ox1 - ox0) / 10.0) > (ox1 - ox0) / 10.0 - 0.5) | (np.abs(tile.y - (otop + 4.5)) < 0.35)), c["leaf"])
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, ox0, fan_foot, ox1, fan_foot + 1.6)), c["leaf"])
    leaf = tile.mask(lambda p, dx, dy: _box(p, dx, dy, ox0, fan_foot + 1.6, ox1, floor))
    tile.put(leaf, c["leaf"])
    tile.tone((tile.noise(2, 14, 2) - 0.5) * 0.12 * leaf)
    tile.put(leaf * (np.abs(tile.x - W * 0.5) < 0.5), c["dark"], 0.9)
    gy0, gy1 = fan_foot + 5.0, fan_foot + 44.0
    for xa, xb in ((ox0 + 2.6, W * 0.5 - 2.2), (W * 0.5 + 2.2, ox1 - 2.6)):
        glass = tile.mask(lambda p, dx, dy: _box(p, dx, dy, xa, gy0, xb, gy1))
        tile.put(glass, c["glow"])
        tile.put(glass * np.clip(1.0 - (tile.y - gy0) / 30.0, 0, 1), (255, 255, 255), 0.20)
        bars = (np.abs(((tile.x - xa) % ((xb - xa) / 3.0)) - (xb - xa) / 6.0) > (xb - xa) / 6.0 - 0.45) | (np.abs(((tile.y - gy0) % ((gy1 - gy0) / 5.0)) - (gy1 - gy0) / 10.0) > (gy1 - gy0) / 10.0 - 0.45)
        tile.put(glass * bars, c["leaf"])
        tile.put(glass * (tile.x < xa + 1.0), c["dark"], 0.25)
        panel = tile.mask(lambda p, dx, dy: _box(p, dx, dy, xa, gy1 + 4.0, xb, floor - 5.0))
        tile.put(panel, c["leaf_light"], 0.25)
        tile.put(panel * ((tile.x < xa + 0.8) | (tile.y < gy1 + 4.8)), c["dark"], 0.40)
        tile.put(panel * ((tile.x > xb - 0.8) | (tile.y > floor - 5.8)), (255, 255, 255), 0.20)
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, W * 0.5 + side * 2.0, gy1 + 1.6, 0.9) for side in (-1.0, 1.0)]), c["brass"])
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, ox0 - 3.0, floor - 1.6, ox1 + 3.0, floor)), c["accent"])
    # The white columns of the colonnade, round, with a base and a capital.
    for cx in (4.4, W - 4.4):
        shaft = tile.mask(lambda p, dx, dy: _box(p, dx, dy, cx - 2.8, 16.0, cx + 2.8, floor - 3.0))
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, cx - 2.0, 16.0, cx + 4.6, floor - 3.0), blur=0.8) * wall * (1.0 - shaft), (0, 0, 0), 0.30)
        tile.put(shaft, c["stucco"])
        tile.put(shaft * np.clip(1.0 - np.abs(tile.x - (cx - 1.0)) / 1.0, 0, 1), (255, 255, 255), 0.45)
        tile.put(shaft * np.clip((tile.x - cx - 0.6) / 2.2, 0, 1), c["dark"], 0.35)
        for y0, y1, half in ((floor - 3.0, floor, 3.8), (16.0, 18.4, 3.6)):
            ring = tile.mask(lambda p, dx, dy: _box(p, dx, dy, cx - half, y0, cx + half, y1))
            tile.put(ring, c["stucco"])
            tile.put(ring * (tile.y < y0 + 0.7), (255, 255, 255), 0.45)
            tile.put(ring * (tile.y > y1 - 0.6), c["dark"], 0.30)
    # The beam of the verandah over the street, with its cornice, and the
    # iron rail of the balcony over it.
    beam = tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, 8.0, W, 16.0))
    tile.put(beam, c["stucco"])
    tile.put(beam * (np.abs(tile.y - 12.0) < 0.4), c["dark"], 0.25)
    tile.put(beam * (tile.y > 15.2), c["dark"], 0.35)
    cornice = tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, 5.6, W, 8.4))
    tile.put(cornice, c["stucco"])
    tile.put(cornice * (tile.y < 6.4), (255, 255, 255), 0.5)
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, 8.4, W, 9.4), blur=0.4), (0, 0, 0), 0.30)
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, 0.0, W, 5.6)), (0, 0, 0), 0.45)
    rail = tile.mask(lambda p, dx, dy: (_box(p, dx, dy, 0.0, 0.4, W, 1.6), _box(p, dx, dy, 0.0, 4.2, W, 5.6), [_box(p, dx, dy, x - 0.45, 0.4, x + 0.45, 5.6) for x in np.arange(1.5, W, 3.0)]))
    tile.put(rail, c["iron"])
    tile.put(rail * (tile.y < 1.0), (150, 150, 156), 0.5)
    return leaf


def kongo_gate_door(tile: Tile, c: dict) -> np.ndarray:
    """The gate of the king's enclosure at Mbanza Kongo, about 1520. Tall
    panels of palm mat, woven in bands on the two diagonals so they make a
    chevron, fill the frame between posts. Over the gate is a lintel of
    palm ribs bound with cord. The gate is two leaves of palm ribs set side
    by side and lashed to cross bars, with a small opening of open lattice
    high in it."""
    _frame(tile, c)
    floor = H - STEP
    wall = tile.mask(lambda p, dx, dy: _box(p, dx, dy, F, F, W - F, floor))
    tile.put(wall, c["mat"])
    d1 = (tile.x + tile.y) / 3.0
    d2 = (tile.x - tile.y) / 3.0
    cell = (np.floor(d1) + np.floor(d2)) % 2
    strand = np.where(cell > 0.5, np.abs((d1 % 1.0) - 0.5) < 0.32, np.abs((d2 % 1.0) - 0.5) < 0.32)
    tile.put(wall * strand, c["mat_light"], 0.65)
    tile.put(wall * ~strand, c["mat_dark"], 0.55)
    tile.put(wall * (np.abs(((tile.y - F) % 30.0) - 15.0) > 14.2), c["mat_dark"], 0.8)
    # The posts that hold the panels, at the sides of the frame.
    for px in (F + 1.0, W - F - 3.4):
        post = tile.mask(lambda p, dx, dy: _box(p, dx, dy, px, F, px + 2.4, floor))
        tile.put(post, c["frame"])
        tile.put(post * (tile.x < px + 0.8), c["frame_light"], 0.5)
    # The gateway: dark between two posts, under the lintel of ribs.
    gx0, gx1, top = 14.0, W - 14.0, 44.0
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, gx0, top, gx1, floor)), c["dark"])
    for px in (gx0 - 3.6, gx1):
        post = tile.mask(lambda p, dx, dy: _box(p, dx, dy, px, top - 9.0, px + 3.6, floor))
        tile.put(post, _mix(c["frame"], c["dark"], 0.15))
        tile.put(post * (tile.x < px + 1.2), c["frame_light"], 0.45)
        tile.put(post * (tile.x > px + 2.8), c["dark"], 0.45)
    lintel_y = top - 9.0
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, gx0 - 7.0, top - 1.0, gx1 + 7.0, top + 1.6), blur=0.8), (0, 0, 0), 0.40)
    for k in range(5):
        y0 = lintel_y + k * 1.8
        rib = tile.mask(lambda p, dx, dy: _box(p, dx, dy, gx0 - 7.0, y0, gx1 + 7.0, y0 + 1.6))
        tile.put(rib, _mix(c["leaf"], c["dark"], 0.10 * (k % 2)))
        tile.put(rib * (tile.y < y0 + 0.5), c["leaf_light"], 0.6)
        tile.put(rib * (tile.y > y0 + 1.2), c["dark"], 0.35)
    for px in (gx0 - 4.5, W * 0.5, gx1 + 4.5):
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(px - 1.4 + j * 0.9, lintel_y - 0.2), (px - 0.8 + j * 0.9, top + 0.2)], 0.30) for j in range(3)]), c["cord"])
    # The leaves: palm ribs side by side, with two cross bars lashed on.
    leaf = tile.mask(lambda p, dx, dy: _box(p, dx, dy, gx0 + 0.6, top + 0.6, gx1 - 0.6, floor - 0.4))
    tile.put(leaf, c["leaf"])
    lane = (tile.x - gx0) % 2.4
    tile.put(leaf * (lane < 0.35), c["dark"], 0.55)
    tile.put(leaf * (lane > 0.5) * (lane < 1.0), c["leaf_light"], 0.45)
    tile.put(leaf * np.clip(1.0 - np.abs(((tile.y - top) % 23.0) - 11.5) / 0.4, 0, 1) * (np.floor((tile.x - gx0) / 2.4) % 3 == 0), c["dark"], 0.35)
    tile.put(leaf * (np.abs(tile.x - W * 0.5) < 0.45), c["dark"], 0.8)
    for yy in (top + 18.0, floor - 14.0):
        bar = tile.mask(lambda p, dx, dy: _box(p, dx, dy, gx0 + 1.0, yy, gx1 - 1.0, yy + 2.4)) * leaf
        tile.put(bar, _mix(c["frame"], c["dark"], 0.10))
        tile.put(bar * (tile.y < yy + 0.7), c["frame_light"], 0.45)
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(xx - 0.7, yy - 0.4), (xx + 0.7, yy + 2.8)], 0.28) for xx in np.arange(gx0 + 3.0, gx1 - 2.0, 4.8)]) * leaf, c["cord"])
    _window(tile, c, W * 0.5 - 4.0, top + 6.0, W * 0.5 + 4.0, top + 11.0)
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(W * 0.5 - 4.0 + k * 2.0, top + 6.0), (W * 0.5 - 4.0 + k * 2.0 + 3.0, top + 11.0)], 0.3) for k in range(-1, 4)] + [_line(p, dx, dy, [(W * 0.5 - 4.0 + k * 2.0 + 3.0, top + 6.0), (W * 0.5 - 4.0 + k * 2.0, top + 11.0)], 0.3) for k in range(-1, 4)]) * tile.mask(lambda p, dx, dy: _box(p, dx, dy, W * 0.5 - 4.0, top + 6.0, W * 0.5 + 4.0, top + 11.0)), c["leaf"])
    return leaf


def trading_post_door(tile: Tile, c: dict) -> np.ndarray:
    """The door of a trading post on the Congo, about 1900. The wall is of
    weatherboards, grey with the damp, under the low roof of a verandah of
    corrugated iron on thin posts, so the top of the wall is in shade. The
    door is of plain planks with two ledges and a brace, in a plain casing,
    with a small pane of glass over it. Muted and plain."""
    _frame(tile, c)
    floor = H - STEP
    wall = tile.mask(lambda p, dx, dy: _box(p, dx, dy, F, F, W - F, floor))
    tile.put(wall, c["board"])
    board = (tile.y - F) % 5.0
    tile.put(wall * (board < 0.6), c["dark"], 0.45)
    tile.put(wall * (board > 0.6) * (board < 1.3), _mix(c["board"], (255, 255, 255), 0.25), 0.45)
    tile.tone((tile.noise(3, 12, 2) - 0.5) * 0.14 * wall)
    # The verandah: its roof of corrugated iron, seen from under its edge,
    # the shade it throws on the wall, and its two thin posts.
    roof_low = 20.0
    tile.put(wall * np.clip(1.0 - (tile.y - roof_low) / 16.0, 0, 1) * (tile.y > roof_low - 1.0), (0, 0, 0), 0.40)
    roof = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(0.0, F), (W, F), (W, roof_low), (0.0, roof_low)]))
    tile.put(roof, c["tin"])
    tile.put(roof * (np.abs((tile.x % 3.0) - 1.5) < 0.5), _mix(c["tin"], (255, 255, 255), 0.30), 0.7)
    tile.put(roof * (np.abs((tile.x % 3.0) - 1.5) > 1.2), c["dark"], 0.35)
    tile.put(roof * np.clip((tile.noise(8, 3, 2) - 0.6) * 4.0, 0, 1), c["rust"], 0.45)
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, roof_low - 1.4, W, roof_low)), _mix(c["tin"], c["dark"], 0.45))
    for px in (F + 1.4, W - F - 3.4):
        post = tile.mask(lambda p, dx, dy: _box(p, dx, dy, px, roof_low, px + 2.0, floor))
        tile.put(post, c["post"])
        tile.put(post * (tile.x < px + 0.6), _mix(c["post"], (255, 255, 255), 0.30), 0.6)
    # The casing and the door.
    x0, x1, top = 16.0, W - 16.0, 40.0
    casing = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 - 2.4, top - 12.0, x1 + 2.4, floor))
    tile.put(casing, c["frame"])
    tile.put(casing * (tile.x < x0 - 1.6), c["frame_light"], 0.45)
    _window(tile, c, x0 + 1.0, top - 10.0, x1 - 1.0, top - 3.0)
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, W * 0.5 - 0.3, top - 10.0, W * 0.5 + 0.3, top - 3.0)), c["frame"])
    leaf = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0, top - 1.0, x1, floor - 0.4))
    tile.put(leaf, c["leaf"])
    plank = (tile.x - x0) % 5.2
    tile.put(leaf * (plank < 0.4), c["dark"], 0.65)
    tile.put(leaf * (plank > 0.5) * (plank < 1.1), c["leaf_light"], 0.30)
    tile.tone((tile.noise(4, 14, 2) - 0.5) * 0.16 * leaf)
    for yy in (top + 8.0, floor - 12.0):
        ledge = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 0.8, yy, x1 - 0.8, yy + 3.0)) * leaf
        tile.put(ledge, _mix(c["leaf"], c["dark"], 0.15))
        tile.put(ledge * (tile.y < yy + 0.7), c["leaf_light"], 0.40)
        tile.put(ledge * (tile.y > yy + 2.4), c["dark"], 0.45)
    brace = tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(x0 + 2.0, floor - 12.0), (x1 - 2.0, top + 11.0)], 1.4)) * leaf
    tile.put(brace, _mix(c["leaf"], c["dark"], 0.15))
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy + 1.5, 0.5) for x in np.arange(x0 + 2.6, x1 - 1.0, 5.2) for yy in (top + 8.0, floor - 12.0)]), c["iron"])
    tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, x1 - 5.0, 76.0, x1 - 3.4, 81.0), _dot(p, dx, dy, x1 - 4.2, 78.5, 1.0))), c["iron"])
    return leaf


def treaty_house_door(tile: Tile, c: dict) -> np.ndarray:
    """The front door of James Busby's house at Waitangi, 1840. The wall is
    of white weatherboards under the roof of the verandah, which throws a
    shade on its top; two thin white posts of the verandah stand at the
    sides. The door is of six panels in a plain white casing, with a light
    of glass over it and a small knob of brass."""
    _frame(tile, c)
    floor = H - STEP
    wall = tile.mask(lambda p, dx, dy: _box(p, dx, dy, F, F, W - F, floor))
    tile.put(wall, c["board"])
    board = (tile.y - F) % 4.6
    tile.put(wall * (board < 0.5), c["dark"], 0.30)
    tile.put(wall * (board > 0.5) * (board < 1.2), (255, 255, 255), 0.35)
    tile.tone((tile.noise(3, 12, 2) - 0.5) * 0.06 * wall)
    # The verandah: the edge of its roof of boards at the top, its shade
    # on the wall, and its two posts.
    roof_low = 18.0
    tile.put(wall * np.clip(1.0 - (tile.y - roof_low) / 18.0, 0, 1) * (tile.y > roof_low - 1.0), (0, 0, 0), 0.30)
    roof = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(0.0, F), (W, F), (W, roof_low), (0.0, roof_low)]))
    tile.put(roof, c["roof"])
    tile.put(roof * (np.abs(((tile.y - F) % 3.2) - 1.6) < 0.3), c["dark"], 0.30)
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, roof_low - 2.2, W, roof_low)), c["post"])
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, roof_low - 0.6, W, roof_low)), c["dark"], 0.35)
    for px in (F + 1.2, W - F - 3.2):
        post = tile.mask(lambda p, dx, dy: _box(p, dx, dy, px, roof_low, px + 2.0, floor))
        tile.put(post, c["post"])
        tile.put(post * (tile.x > px + 1.4), c["dark"], 0.25)
    # The casing, the light over the door, and the door of six panels.
    x0, x1, top = 16.0, W - 16.0, 42.0
    casing = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 - 2.6, top - 13.0, x1 + 2.6, floor))
    tile.put(casing, c["frame"])
    tile.put(casing * (tile.x < x0 - 1.8), c["frame_light"], 0.5)
    tile.put(casing * (tile.x > x1 + 1.8), c["dark"], 0.25)
    _window(tile, c, x0 + 1.0, top - 11.0, x1 - 1.0, top - 3.0)
    for k in range(1, 4):
        xx = x0 + 1.0 + k * (x1 - x0 - 2.0) / 4.0
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, xx - 0.3, top - 11.0, xx + 0.3, top - 3.0)), c["frame"])
    leaf = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0, top - 1.0, x1, floor - 0.4))
    tile.put(leaf, c["leaf"])
    rows = ((top + 2.0, top + 15.0), (top + 18.0, top + 40.0), (top + 43.0, floor - 3.0))
    for y0, y1 in rows:
        for xa, xb in ((x0 + 2.4, W * 0.5 - 1.2), (W * 0.5 + 1.2, x1 - 2.4)):
            panel = tile.mask(lambda p, dx, dy: _box(p, dx, dy, xa, y0, xb, y1)) * leaf
            tile.put(panel, _mix(c["leaf"], c["dark"], 0.10))
            tile.put(panel * ((tile.x < xa + 0.8) | (tile.y < y0 + 0.8)), c["dark"], 0.45)
            tile.put(panel * ((tile.x > xb - 0.8) | (tile.y > y1 - 0.8)), c["leaf_light"], 0.45)
            inner = tile.mask(lambda p, dx, dy: _box(p, dx, dy, xa + 1.8, y0 + 1.8, xb - 1.8, y1 - 1.8)) * panel
            tile.put(inner, c["leaf"])
            tile.put(inner * (tile.x < xa + 2.4), c["leaf_light"], 0.30)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, x1 - 3.4, 82.0, 1.1)), c["brass"])
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, x1 - 3.7, 81.7, 0.45)), (255, 240, 200), 0.6)
    return leaf


def tent_flap_door(tile: Tile, c: dict) -> np.ndarray:
    """The door of a tent of the camp at Sydney Cove, 1788: plain canvas,
    worn and a little stained, held on its poles by the frame. Two flaps
    meet at the middle and close with three pairs of tapes; the seams of
    the cloth run down each flap; a hem and a lacing of rope are at the
    foot. Where the flaps part a little at the top, the light of a lamp
    inside shows. Muted and plain."""
    leaf = _frame(tile, c)
    floor = H - STEP
    tile.put(leaf, c["leaf"])
    tile.tone((tile.noise(4, 10, 3) - 0.5) * 0.16 * leaf)
    tile.put(leaf * np.clip((tile.noise(3, 6, 2) - 0.62) * 4.0, 0, 1), c["stain"], 0.30)
    # The folds of each flap: soft shades that run down from the top, and
    # the seams of the cloth.
    fold = np.sin((tile.x - F) / (W - 2 * F) * math.pi * 5.0 + tile.y * 0.02)
    tile.put(leaf * np.clip(fold, 0, 1), c["dark"], 0.10)
    tile.put(leaf * np.clip(-fold, 0, 1), c["leaf_light"], 0.12)
    for sx in (F + 9.0, W - F - 9.0):
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, sx - 0.25, F, sx + 0.25, floor)) * leaf, c["dark"], 0.35)
    # The two flaps meet at the middle: the right flap laps over the left,
    # with its edge a little dark below it.
    tile.put(leaf * (np.abs(tile.x - W * 0.5) < 0.5), c["dark"], 0.55)
    tile.put(leaf * (tile.x > W * 0.5 + 0.5) * (tile.x < W * 0.5 + 1.6), c["leaf_light"], 0.35)
    # The gap at the top where the flaps part, with the lamp light in it.
    gap = [(W * 0.5 - 3.6, F + 1.0), (W * 0.5 + 3.6, F + 1.0), (W * 0.5 + 0.4, F + 16.0), (W * 0.5 - 0.4, F + 16.0)]
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, gap)), c["glow"])
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, gap), blur=2.0) * leaf, c["glow"], 0.25)
    # The tapes that tie the flaps.
    for y in (42.0, 66.0, 90.0):
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(W * 0.5 - 3.0, y - 1.0), (W * 0.5, y), (W * 0.5 + 3.0, y - 1.0)], 0.45), _line(p, dx, dy, [(W * 0.5, y), (W * 0.5 - 1.4, y + 4.0)], 0.40), _line(p, dx, dy, [(W * 0.5, y), (W * 0.5 + 1.6, y + 3.6)], 0.40)]), c["tape"])
    # The hem at the foot and the rope that laces it.
    hem = leaf * (tile.y > floor - 5.0)
    tile.put(hem, _mix(c["leaf"], c["dark"], 0.15))
    tile.put(leaf * (np.abs(tile.y - (floor - 5.0)) < 0.35), c["dark"], 0.45)
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, floor - 2.5, 0.6) for x in np.arange(F + 3.0, W - F, 5.0)]), c["dark"], 0.7)
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x, floor - 2.5), (x + 2.5, floor + 0.2)], 0.3) for x in np.arange(F + 3.0, W - F, 5.0)]), c["tape"], 0.8)
    return leaf


def nan_madol_door(tile: Tile, c: dict) -> np.ndarray:
    """A doorway in a wall of Nan Madol at dusk. Black basalt columns laid
    crosswise fill the frame: a course of long columns that lie along the
    wall, then a course of the ends of columns that lie across it, each end
    of five or six sides. In the middle is a low dark doorway under a lintel
    of two long columns, and in it hangs a mat of plaited coconut leaf. The
    light of a fire inside shows through a gap at the top of the mat."""
    inner = _frame(tile, c)
    floor = H - STEP
    rng = tile.rng
    tile.put(inner, c["dark"])
    y = floor
    k = 0
    while y > F + 0.5:
        y0 = max(F, y - 6.0)
        if k % 2 == 0:
            x = F - rng.uniform(0.0, 8.0)
            while x < W - F:
                length = rng.uniform(10.0, 18.0)
                x0, x1 = x + 0.3, x + length - 0.3
                tone = rng.uniform(-0.12, 0.12)
                body = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(x0 + 0.6, y0 + 0.4), (x1 - 0.6, y0 + 0.4), (x1, y0 + 1.2), (x1, y - 1.0), (x1 - 0.6, y - 0.4), (x0 + 0.6, y - 0.4), (x0, y - 1.0), (x0, y0 + 1.2)])) * inner
                tile.put(body, _mix(c["frame"], c["frame_light"] if tone > 0 else c["dark"], abs(tone) * 2.0))
                tile.put(body * (tile.y < y0 + 2.0), c["frame_light"], 0.35)
                tile.put(body * (tile.y > y - 1.6), c["dark"], 0.40)
                x += length
        else:
            x = F + rng.uniform(0.0, 3.0)
            while x < W - F + 3.0:
                r = rng.uniform(2.6, 2.95)
                cy = (y0 + y) * 0.5
                turn = rng.uniform(0.0, 60.0)
                pts = [(x + r * math.cos(math.radians(turn + 60.0 * i)), cy + r * math.sin(math.radians(turn + 60.0 * i))) for i in range(6)]
                end = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, pts)) * inner
                tone = rng.uniform(-0.12, 0.12)
                tile.put(end, _mix(c["frame"], c["frame_light"] if tone > 0 else c["dark"], abs(tone) * 2.0))
                tile.put(end * (1.0 - tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(px + 0.6, py + 0.6) for px, py in pts]))), c["frame_light"], 0.45)
                tile.put(end * (1.0 - tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(px - 0.5, py - 0.5) for px, py in pts]))), c["dark"], 0.45)
                x += r * 2.05
        y = y0
        k += 1
    tile.tone((tile.noise(4, 8, 2) - 0.5) * 0.14 * inner)
    # The doorway, the shade under its lintel, and the lintel of two long
    # columns that reach past its sides.
    x0, x1, top = 18.0, W - 18.0, 52.0
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0, top, x1, floor)), c["dark"])
    for y0, y1 in ((top - 10.0, top - 5.2), (top - 5.2, top - 0.4)):
        beam = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(x0 - 7.0, y0 + 0.4), (x1 + 7.0, y0 + 0.4), (x1 + 7.6, y0 + 1.2), (x1 + 7.6, y1 - 0.8), (x1 + 7.0, y1), (x0 - 7.0, y1), (x0 - 7.6, y1 - 0.8), (x0 - 7.6, y0 + 1.2)]))
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 - 8.0, y0, x1 + 8.0, y1)), c["dark"])
        tile.put(beam, c["frame"])
        tile.put(beam * (tile.y < y0 + 1.8), c["frame_light"], 0.45)
        tile.put(beam * (tile.y > y1 - 1.4), c["dark"], 0.45)
    # The mat: strips of coconut leaf plaited on the slant, with a pole
    # at its top and its foot. It is the leaf.
    leaf = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 1.0, top + 1.0, x1 - 1.0, floor - 0.6))
    tile.put(leaf, c["leaf"])
    plait = (np.floor((tile.x + tile.y) / 2.2) + np.floor((tile.x - tile.y) / 2.2)) % 2 == 0
    tile.put(leaf * plait, c["leaf_light"], 0.30)
    tile.put(leaf * ~plait, c["dark"], 0.20)
    tile.put(leaf * np.clip((tile.y - top) / (floor - top), 0, 1), c["dark"], 0.25)
    for yy in (top + 1.0, floor - 3.0):
        pole = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 0.4, yy, x1 - 0.4, yy + 2.0))
        tile.put(pole, c["frame"])
        tile.put(pole * (tile.y < yy + 0.6), c["frame_light"], 0.5)
    _window(tile, c, W * 0.5 - 4.0, top + 5.0, W * 0.5 + 4.0, top + 10.0)
    return leaf


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
    strait_door: (SWING, False),
    borobudur_door: (SWING, False),
    angkor_door: (SWING, False),
    jomon_door: (SWING, False),
    taiwan_door: (SWING, False),
    gyeongju_door: (SWING, True),
    hangzhou_door: (SWING, True),
    heian_door: (SWING, True),
    hanyang_door: (SWING, True),
    lalbagh_door: (SWING, True),
    company_gate_door: (SWING, True),
    curzon_door: (SWING, True),
    longhouse_door: (SWING, False),
    palisade_gate_door: (SWING, True),
    azulejo_door: (SWING, True),
    kamakura_gate_door: (SWING, True),
    bricktown_door: (SWING, True),
    kongo_gate_door: (SWING, True),
    trading_post_door: (SWING, False),
    treaty_house_door: (SWING, False),
    tent_flap_door: (SLIDE, True),
    nan_madol_door: (SWING, False),
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
    # The Boss dimension: a stage door with the star of a dressing room on it.
    "boss_stage": (star_door, _colours((36, 28, 46), (52, 36, 70), (10, 8, 16), (236, 48, 150), (255, 214, 120))),
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
    # A guest room of the haunted floors: dark plank in a brass frame, the
    # teal of the ghosts under it.
    "math_haunted": (plank, _colours((204, 156, 72), (70, 40, 34), (22, 14, 30), (92, 238, 214), (92, 238, 214))),
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
    # The Strait: a door of planks and nipa thatch in a house on a raft,
    # the ends of the logs under its sill. Borobudur: a gate of andesite
    # with a corbelled arch and a band of lotus petals, a leaf of teak with
    # studs of bronze. Angkor: a sandstone doorway with colonnettes and a
    # lintel carved with a vine, a corbelled arch over it, in a wall of
    # laterite.
    "history_strait": (strait_door, {**_colours((96, 68, 46), (82, 58, 40), (30, 22, 16), (176, 136, 70), (255, 214, 150)),
                                     "wall": (132, 100, 68), "thatch": (178, 146, 90)}),
    "history_borobudur": (borobudur_door, {**_colours((132, 132, 128), (88, 58, 38), (36, 36, 38), (184, 146, 70), (255, 220, 160))}),
    "history_angkor": (angkor_door, {**_colours((182, 158, 150), (92, 56, 38), (44, 30, 26), (200, 160, 80), (255, 212, 140)),
                                     "laterite": (150, 76, 52)}),
    # Sannai-Maruyama: the low door of a pit house, under a roof of
    # thatch that comes down to the earth, with a mat of woven bark.
    # Taiwan: a door of adzed planks in a house on posts, a lintel painted
    # red and black, an eave of thatch. Gyeongju: a gate of red-painted
    # planks with studs and bronze rings, under a roof of grey tiles.
    "history_jomon": (jomon_door, {**_colours((104, 76, 50), (150, 118, 76), (34, 24, 18), (150, 96, 56), (255, 186, 104)),
                                   "thatch": (176, 146, 92), "earth": (100, 74, 48), "cord": (196, 168, 120)}),
    "history_taiwan": (taiwan_door, {**_colours((110, 80, 52), (150, 108, 66), (34, 26, 20), (176, 60, 44), (255, 220, 160)),
                                     "wall": (168, 128, 84), "thatch": (180, 154, 96), "cord": (120, 84, 50), "paint_red": (176, 52, 40), "paint_black": (40, 32, 28)}),
    "history_gyeongju": (gyeongju_door, {**_colours((178, 58, 40), (156, 50, 36), (36, 26, 24), (176, 170, 160), (255, 214, 150)),
                                         "tile": (82, 84, 90), "bracket": (56, 118, 98), "bronze": (196, 156, 82)}),
    # West Lake: a moon gate in a white wall under grey tiles. Heian-kyo: a
    # gate of vermilion posts and beams under black tiles, with leaves of
    # cypress. Hanyang: the gate of Gyeongbokgung, red leaves in a granite
    # arch under two roofs with painted eaves.
    "history_hangzhou": (hangzhou_door, {**_colours((112, 114, 118), (82, 56, 40), (30, 28, 30), (150, 148, 140), (255, 214, 150)),
                                         "wall": (228, 224, 212), "tile": (84, 88, 94), "willow": (130, 166, 74)}),
    "history_heian": (heian_door, {**_colours((186, 58, 38), (190, 154, 106), (32, 26, 24), (140, 136, 128), (255, 220, 160)),
                                   "tile": (56, 56, 62), "plaster": (234, 228, 214), "rafter": (226, 210, 170), "iron": (46, 44, 44)}),
    "history_hanyang": (hanyang_door, {**_colours((170, 166, 156), (168, 46, 36), (34, 28, 26), (150, 146, 138), (255, 222, 160)),
                                       "tile": (80, 82, 88), "green": (52, 124, 100), "red": (176, 52, 40), "blue": (56, 92, 150), "white": (236, 232, 220), "iron": (56, 52, 50)}),
    # Dhaka on the Buriganga: the gate of the Lalbagh fort, a pointed arch
    # in red brick and plaster. Calcutta: a white gateway of the Company
    # with a fanlight and green shutters. Dhaka in spring: a horseshoe arch
    # of Curzon Hall, its voussoirs brick and stone in turn.
    "history_dhaka_river": (lalbagh_door, {**_colours((172, 76, 54), (92, 60, 40), (40, 26, 22), (196, 176, 150), (255, 214, 150)),
                                           "plaster": (226, 210, 184), "mortar": (214, 196, 170), "iron": (52, 46, 44)}),
    "history_calcutta": (company_gate_door, {**_colours((216, 210, 196), (66, 112, 84), (40, 40, 38), (196, 184, 160), (255, 226, 170)),
                                             "plaster": (236, 230, 216), "damp": (150, 150, 128), "brass": (206, 168, 80)}),
    "history_dhaka_spring": (curzon_door, {**_colours((178, 72, 52), (86, 54, 38), (40, 24, 20), (204, 196, 182), (255, 216, 140)),
                                           "stone": (232, 222, 200), "mortar": (210, 186, 160), "glass": (70, 140, 170), "brass": (206, 168, 80)}),
    # Brazil. Marajó: the doorway of a big house of thatch, a mat of palm
    # leaf in it and a lintel painted like Marajoara pots. Palmares: a gate
    # of lashed logs in a palisade. Rio: a green door with a fanlight in a
    # frame of granite, in a front of blue and white tiles.
    "history_marajo": (longhouse_door, {**_colours((120, 90, 60), (176, 150, 96), (34, 26, 20), (196, 84, 48), (255, 190, 110)),
                                        "thatch": (186, 154, 98), "wall": (140, 106, 70), "slip": (232, 220, 196), "paint_red": (176, 62, 40), "paint_black": (40, 30, 26)}),
    "history_palmares": (palisade_gate_door, {**_colours((126, 94, 64), (138, 104, 70), (38, 26, 18), (176, 86, 50), (255, 206, 130)), "cord": (204, 172, 110)}),
    "history_rio_1888": (azulejo_door, {**_colours((172, 168, 160), (46, 104, 70), (34, 34, 38), (176, 172, 164), (255, 230, 170)),
                                        "tile_white": (238, 236, 228), "tile_blue": (46, 86, 166), "stone": (176, 172, 164), "iron": (44, 44, 50), "brass": (214, 174, 80)}),
    # Japan. Hakata Bay: the gate of a warrior's house of the Kamakura
    # period, plain plank leaves under a small roof of wooden shingles, a
    # fence of boards at the sides. Tokyo: a glazed shop door between white
    # columns, in a wall of red brick in Flemish bond.
    "history_kamakura": (kamakura_gate_door, {**_colours((104, 80, 58), (152, 120, 84), (30, 24, 22), (138, 132, 122), (255, 212, 150)),
                                              "shingle": (128, 108, 86), "fence": (112, 100, 86)}),
    "history_meiji": (bricktown_door, {**_colours((236, 228, 210), (84, 54, 38), (34, 24, 22), (150, 146, 138), (255, 222, 150)),
                                       "brick": (160, 74, 54), "mortar": (214, 204, 184), "stucco": (236, 228, 210), "iron": (44, 44, 50), "brass": (214, 174, 80)}),
    # Central Africa. Ishango: the hide door of a shelter of bent poles,
    # with the light of the fire in its smoke hole (the door of the first
    # people of the savanna). Mbanza Kongo: the gate of the king's
    # enclosure, leaves of palm rib in a wall of woven palm mat. Matamba:
    # the gate of a kilombo, logs cut to a point (the gate of Palmares,
    # whose quilombo took its name from the kilombo of Angola). The Congo:
    # a plank door in a wall of weatherboards under a verandah of
    # corrugated iron.
    "history_ishango": (hide_door, _colours((118, 92, 62), (166, 132, 92), (44, 32, 22), (150, 126, 90), (255, 190, 110))),
    "history_mbanza_kongo": (kongo_gate_door, {**_colours((116, 84, 56), (204, 178, 120), (40, 28, 20), (168, 78, 48), (255, 212, 140)),
                                               "mat": (196, 166, 112), "mat_dark": (128, 98, 62), "mat_light": (232, 212, 160), "cord": (110, 80, 48)}),
    "history_matamba": (palisade_gate_door, {**_colours((132, 98, 66), (144, 110, 74), (44, 30, 20), (170, 98, 60), (255, 204, 120)), "cord": (198, 164, 104)}),
    "history_congo_river_1900": (trading_post_door, {**_colours((168, 164, 150), (110, 100, 84), (32, 32, 30), (120, 118, 110), (220, 206, 160)),
                                                     "board": (124, 120, 106), "tin": (130, 132, 130), "rust": (130, 84, 58), "post": (150, 146, 134), "iron": (40, 40, 42)}),
    # Australia and Aotearoa. Lake Mungo: the hide door of a shelter of
    # bent poles, as at Sahul, with the light of the fire in its smoke
    # hole. Aotearoa: a door of bundled raupō reeds in a frame of poles, the
    # door of a whare; no carving. Tonga: a mat of plaited pandanus hung in
    # the doorway of a fale, the door of the Lapita. Waitangi: the door of
    # six panels of James Busby's house under its verandah. Sydney Cove:
    # the two flaps of a plain canvas tent of the camp.
    "history_willandra": (hide_door, _colours((124, 102, 80), (172, 140, 104), (46, 34, 26), (200, 140, 98), (255, 190, 110))),
    "history_aotearoa": (reed_door, _colours((98, 76, 54), (176, 150, 100), (34, 28, 22), (168, 64, 52), (255, 214, 150))),
    "history_tonga": (mat_door, _colours((112, 84, 58), (206, 178, 122), (40, 32, 24), (122, 74, 48), (255, 214, 150))),
    "history_waitangi": (treaty_house_door, {**_colours((226, 222, 212), (86, 98, 88), (36, 34, 32), (176, 170, 160), (255, 226, 170)),
                                             "board": (232, 230, 220), "roof": (122, 116, 110), "post": (238, 236, 228), "brass": (200, 170, 90)}),
    "history_sydney_cove": (tent_flap_door, {**_colours((118, 100, 80), (188, 180, 160), (40, 36, 32), (172, 130, 84), (236, 196, 130)),
                                             "stain": (150, 132, 104), "tape": (150, 132, 104)}),
    # Budj Bim: a door of sewn possum skins, as at Sahul and the Willandra,
    # in a frame the grey of basalt: the low doorway of a house of stacked
    # stone, with the light of the fire in its smoke hole.
    "history_budj_bim": (hide_door, _colours((96, 92, 88), (128, 108, 90), (30, 28, 26), (160, 120, 80), (255, 190, 110))),
    # Micronesia. The Marianas: the door of a house on latte, high off the
    # ground, with a short ladder up to it under a deep eave of thatch. The
    # Marshalls: a mat of plaited pandanus in the doorway of a house of
    # thatch, as at Tonga. Nan Madol: a low doorway in a wall of basalt
    # columns under a lintel of two columns, with a mat in it. Yap: a door
    # of bundled reeds in a frame of poles. Nauru: the plank door of a shed
    # of the works, under a verandah of corrugated iron. Bikini: a mat door
    # of an empty house, muted, with grey daylight in its opening.
    "history_marianas": (austronesia_door, {**_colours((118, 90, 62), (196, 176, 122), (36, 28, 22), (186, 180, 160), (255, 220, 160)),
                                            "wall": (206, 186, 132), "thatch": (178, 146, 94), "cord": (122, 86, 54)}),
    "history_marshalls": (mat_door, _colours((116, 88, 60), (212, 188, 132), (40, 32, 24), (110, 160, 160), (255, 218, 160))),
    "history_nan_madol": (nan_madol_door, _colours((70, 66, 72), (150, 128, 90), (18, 18, 22), (140, 132, 118), (255, 186, 110))),
    "history_yap": (reed_door, _colours((96, 80, 58), (178, 160, 108), (34, 30, 22), (132, 128, 116), (255, 220, 160))),
    "history_nauru": (trading_post_door, {**_colours((176, 172, 160), (120, 108, 90), (34, 34, 34), (196, 192, 180), (226, 214, 176)),
                                          "board": (190, 186, 172), "tin": (150, 152, 152), "rust": (138, 92, 64), "post": (176, 172, 160), "iron": (44, 44, 46)}),
    "history_bikini": (mat_door, _colours((120, 114, 104), (168, 160, 140), (44, 44, 42), (150, 150, 144), (200, 206, 204))),
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
