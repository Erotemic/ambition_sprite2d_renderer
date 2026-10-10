"""The fixtures of a room that the game drew as flat colour: ladders, water.

    ladder         16 by 32 units, repeats down a ladder (and along one that
                   is more than 16 wide): two rails and a rung each 8 units
    water_clear    64 by 64 units, repeats each way: the body of clear water,
                   mostly clear, with light in streaks
    water_murky    64 by 64 units, repeats each way: the body of murky water,
                   which hides what is in it
    water_surface  64 by 8 units, repeats along the top of a body of water:
                   the line of the surface, with light on it

    blink_soft     64 by 64 units, repeats each way: a wall a blink goes
                   through. A field of violet light, part clear
    blink_hard     64 by 64 units, repeats each way: a wall no blink goes
                   through. Plates of violet armour, not clear
    blink_edge     64 by 6 units, repeats along an open edge of a blink wall:
                   a line of light. Its top row is the outer side

    hazard_fill    64 by 64 units, repeats each way: the body of a surface
                   that sends a body back to its start. Dark red, part clear
    hazard_edge    64 by 12 units, repeats along an open edge of that
                   surface: a row of spikes. Its top row is the outer side

A ladder is of the make of its biome: steel where the ground is steel or
cut stone, wood and rope where it is rock or earth. The water, the blink
walls and the spikes are the same in each biome: violet is the colour of a
blink and red the colour of danger in each room, and a player must know
each at a look.
"""

from __future__ import annotations

import math

import numpy as np
from PIL import Image

from .skins import SKINS, Tile, _box, _dot, _line, _mix, _poly

RGB = tuple[int, int, int]

LADDER = (16, 32)
WATER = (64, 64)
SURFACE = (64, 8)
BLINK = (64, 64)
BLINK_EDGE = (64, 6)
HAZARD = (64, 64)
HAZARD_EDGE = (64, 12)

#: The skins whose ladder is steel. Each other one has a ladder of wood.
STEEL = {"lab", "alarm", "hub", "basement", "boss", "eclipse", "hub_clean"}


def ladder(theme_key: str) -> Image.Image:
    skin = next(skin for skin in SKINS if skin.key == theme_key)
    tile = Tile(LADDER, True, True, theme_key, "ladder")
    steel = theme_key in STEEL
    rail = _mix(skin.light, (150, 160, 170), 0.5) if steel else (128, 90, 56)
    rung = _mix(rail, (255, 255, 255), 0.25) if steel else (170, 126, 78)
    dark = _mix(skin.dark, (10, 10, 14), 0.4)
    for x in (2.2, 13.8):
        w = 1.1 if steel else 0.9
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x - w, 0.0, x + w, 32.0)), rail)
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x - w, 0.0, x - w + 0.5, 32.0)), _mix(rail, (255, 255, 255), 0.4))
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x + w - 0.5, 0.0, x + w, 32.0)), dark, 0.6)
    for k in range(4):
        y = 4.0 + k * 8.0
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, 2.2, y + 1.2, 13.8, y + 1.9)), dark, 0.45)
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, 1.6, y - 1.0, 14.4, y + 1.0)), rung)
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, 1.6, y - 1.0, 14.4, y - 0.45)), _mix(rung, (255, 255, 255), 0.4))
        if steel:
            tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, 0.55) for x in (2.2, 13.8)]), dark, 0.7)
        else:
            # Rope round each end of a wooden rung.
            tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x - 1.2, y - 1.4, x + 1.2, y + 1.4) for x in (2.2, 13.8)]), (206, 180, 128))
            tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x - 1.2, y - 0.5), (x + 1.2, y + 0.5)], 0.3) for x in (2.2, 13.8)]), (120, 96, 60))
    return tile.publish()


def water_clear() -> Image.Image:
    tile = Tile(WATER, True, True, "water", "clear")
    tile.put(np.ones_like(tile.alpha), (60, 178, 220), 0.30)
    streaks = tile.noise(3, 14, 2)
    tile.put(np.clip((streaks - 0.56) * 6.0, 0.0, 1.0), (190, 240, 255), 0.22)
    tile.put(np.clip((0.40 - streaks) * 6.0, 0.0, 1.0), (20, 90, 150), 0.18)
    return tile.publish()


def water_murky() -> Image.Image:
    tile = Tile(WATER, True, True, "water", "murky")
    tile.put(np.ones_like(tile.alpha), (24, 52, 46), 0.90)
    silt = tile.noise(4, 4, 4)
    tile.put(np.clip((silt - 0.5) * 3.0, 0.0, 1.0), (52, 88, 66), 0.5)
    tile.put(np.clip((0.42 - silt) * 4.0, 0.0, 1.0), (8, 20, 20), 0.5)
    specks = [(tile.rng.uniform(0, 64), tile.rng.uniform(0, 64), tile.rng.uniform(0.3, 0.8)) for _ in range(26)]
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, r) for x, y, r in specks]), (120, 150, 110), 0.5)
    return tile.publish()


def water_surface() -> Image.Image:
    tile = Tile(SURFACE, True, False, "water", "surface")
    wave = 2.6 + 1.1 * np.sin(tile.x / 64.0 * math.tau * 3.0) + 0.5 * np.sin(tile.x / 64.0 * math.tau * 7.0 + 1.0)
    line = np.clip(1.0 - np.abs(tile.y - wave) / 0.9, 0.0, 1.0)
    below = np.clip((tile.y - wave) / 4.5, 0.0, 1.0)
    tile.put((tile.y > wave) * (1.0 - below), (150, 226, 246), 0.5)
    tile.put(line, (236, 252, 255), 0.95)
    glints = [(tile.rng.uniform(0, 64), tile.rng.uniform(4.0, 6.5), tile.rng.uniform(1.0, 2.6)) for _ in range(9)]
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x, y, x + w, y + 0.35) for x, y, w in glints]), (236, 252, 255), 0.6)
    return tile.publish()


def blink_soft() -> Image.Image:
    tile = Tile(BLINK, True, True, "blink", "soft")
    tile.put(np.ones_like(tile.alpha), (98, 62, 212), 0.50)
    # Wisps in the field, and two bands of light that go up it at a slant.
    wisps = tile.noise(3, 3, 3)
    tile.put(np.clip((wisps - 0.54) * 5.0, 0.0, 1.0), (176, 140, 255), 0.30)
    tile.put(np.clip((0.44 - wisps) * 5.0, 0.0, 1.0), (44, 20, 128), 0.34)
    band = 0.5 + 0.5 * np.sin((tile.x + tile.y) / 64.0 * math.tau * 2.0)
    tile.put(np.clip((band - 0.72) * 3.6, 0.0, 1.0), (214, 190, 255), 0.26)
    # Thin lines across it, as of a thing that is projected.
    lines = (np.mod(tile.y, 4.0) < 0.5).astype(np.float32)
    tile.put(lines, (224, 206, 255), 0.10)
    stars = [(tile.rng.uniform(3, 61), tile.rng.uniform(3, 61), tile.rng.uniform(1.2, 2.4)) for _ in range(9)]
    tile.put(
        tile.mask(
            lambda p, dx, dy: [
                (
                    _line(p, dx, dy, [(x - r, y), (x + r, y)], 0.34),
                    _line(p, dx, dy, [(x, y - r), (x, y + r)], 0.34),
                    _dot(p, dx, dy, x, y, 0.55),
                )
                for x, y, r in stars
            ]
        ),
        (240, 228, 255),
        0.85,
    )
    return tile.publish()


def blink_hard() -> Image.Image:
    tile = Tile(BLINK, True, True, "blink", "hard")
    tile.put(np.ones_like(tile.alpha), (108, 30, 164), 1.0)
    grain = tile.noise(5, 5, 3)
    tile.put(np.clip((grain - 0.5) * 3.0, 0.0, 1.0), (140, 48, 196), 0.5)
    tile.put(np.clip((0.45 - grain) * 3.0, 0.0, 1.0), (70, 12, 116), 0.5)
    joint, light, dark, stud = (34, 0, 52), (204, 120, 255), (56, 6, 92), (255, 150, 255)
    for px in (0.0, 32.0):
        for py in (0.0, 32.0):
            # One plate: light on its upper and left edges, dark on the others.
            tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, px + 1.0, py + 1.0, px + 31.0, py + 2.4)), light, 0.6)
            tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, px + 1.0, py + 1.0, px + 2.4, py + 31.0)), light, 0.45)
            tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, px + 1.0, py + 29.6, px + 31.0, py + 31.0)), dark, 0.75)
            tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, px + 29.6, py + 1.0, px + 31.0, py + 31.0)), dark, 0.6)
            cx, cy = px + 16.0, py + 16.0
            diamond = [(cx, cy - 6.0), (cx + 6.0, cy), (cx, cy + 6.0), (cx - 6.0, cy)]
            tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, diamond + diamond[:1], 2.6)), dark, 0.8)
            tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, diamond + diamond[:1], 1.1)), stud, 0.9)
            tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, cx, cy, 1.5)), stud, 0.95)
            for sx, sy in ((5.0, 5.0), (27.0, 5.0), (5.0, 27.0), (27.0, 27.0)):
                tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, px + sx, py + sy, 1.1)), dark, 0.85)
                tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, px + sx - 0.3, py + sy - 0.3, 0.5)), light, 0.8)
    for at in (0.0, 32.0, 64.0):
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, at - 1.0, 0.0, at + 1.0, 64.0)), joint)
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, at - 1.0, 64.0, at + 1.0)), joint)
    return tile.publish()


def blink_edge() -> Image.Image:
    tile = Tile(BLINK_EDGE, True, False, "blink", "edge")
    glow = np.clip(1.0 - tile.y / 6.0, 0.0, 1.0) ** 1.6
    tile.put(glow, (170, 120, 255), 0.62)
    tile.put(np.clip(1.0 - np.abs(tile.y - 0.8) / 0.9, 0.0, 1.0), (244, 232, 255), 0.96)
    # A node on the line each 16 units.
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, 1.3, 1.25) for x in (8.0, 24.0, 40.0, 56.0)]), (255, 255, 255), 0.95)
    return tile.publish()


def hazard_fill() -> Image.Image:
    tile = Tile(HAZARD, True, True, "hazard", "fill")
    tile.put(np.ones_like(tile.alpha), (44, 8, 16), 0.62)
    heat = tile.noise(3, 3, 3)
    tile.put(np.clip((heat - 0.52) * 4.0, 0.0, 1.0), (150, 24, 30), 0.34)
    tile.put(np.clip((0.44 - heat) * 4.0, 0.0, 1.0), (12, 2, 6), 0.4)
    # Stripes at a slant, as on a warning sign. Two in a tile, so the tile
    # repeats.
    stripe = np.mod((tile.x + tile.y) / 64.0 * 4.0, 1.0)
    tile.put((stripe < 0.22).astype(np.float32), (232, 60, 52), 0.20)
    return tile.publish()


def hazard_edge() -> Image.Image:
    tile = Tile(HAZARD_EDGE, True, False, "hazard", "edge")
    steel, light, dark, hot = (150, 158, 172), (226, 232, 240), (64, 68, 84), (255, 74, 58)
    # A glow of the red of the tips behind the row, so it shows on dark ground.
    tile.put(np.clip(1.0 - np.abs(tile.y - 3.0) / 6.0, 0.0, 1.0), hot, 0.22)
    for k in range(8):
        x = k * 8.0
        spike = [(x + 0.6, 12.0), (x + 4.0, 0.4), (x + 7.4, 12.0)]
        tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, spike)), steel)
        tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(x + 0.6, 12.0), (x + 4.0, 0.4), (x + 3.2, 12.0)])), light, 0.8)
        tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(x + 5.4, 12.0), (x + 4.0, 0.4), (x + 7.4, 12.0)])), dark, 0.8)
        tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(x + 2.9, 4.2), (x + 4.0, 0.4), (x + 5.1, 4.2)])), hot, 0.95)
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, x + 4.0, 1.2, 0.5)), (255, 220, 200), 0.9)
    # The bar the spikes stand on.
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, 10.4, 64.0, 12.0)), dark)
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, 0.0, 10.4, 64.0, 10.9)), steel, 0.7)
    return tile.publish()
