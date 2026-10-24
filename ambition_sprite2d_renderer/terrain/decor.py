"""The ground decor of each biome: small things that stand on its ground.

A decor picture is a strip of `VARIANTS` squares of `CELL` units. Each
square has one thing in it that stands on the bottom edge of the square, in
the middle. The game puts a few of them on the open top edges of the blocks
of a room (`terrain_skin` in `ambition_render`): a barrel on a pier, a
crystal in a cave, a stone lantern in a forest.

A thing of the decor is not a thing of the play: a player can not touch it,
take it or open it. So it must not look like one. Each thing is low in
contrast and a little dark, it has no outline, and it is not a chest, a
door, a switch or a pickup.
"""

from __future__ import annotations

import math
from typing import Callable

import numpy as np
from PIL import Image

from .skins import K, Tile, _box, _dot, _line, _mix, _poly

RGB = tuple[int, int, int]

#: The side of one square, in the units the things are drawn in.
CELL = 24
VARIANTS = 6
#: A thing of the decor is drawn in the game larger than a unit of its
#: drawing to a world unit (`DECOR_SIZE` in `terrain_skin.rs` is the side of a
#: square in world units), so its picture has more pixels to the unit than a
#: terrain skin has.
SUPERSAMPLE = 2
#: The side of one square of the published strip, in pixels.
CELL_PX = CELL * K // SUPERSAMPLE
#: The ground line: the bottom of the square.
G = float(CELL)
#: The middle of the square.
M = CELL / 2.0

Draw = Callable[[Tile, dict], None]


def _shadow(tile: Tile, half: float) -> None:
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, G - 0.4, half, ry=0.9), blur=0.4), (0, 0, 0), 0.35)


def barrel(tile: Tile, c: dict) -> None:
    _shadow(tile, 6.0)
    body = tile.mask(lambda p, dx, dy: (_box(p, dx, dy, M - 4.6, G - 11.5, M + 4.6, G), _dot(p, dx, dy, M, G - 11.5, 4.6, ry=1.2)))
    tile.put(body, c["wood"])
    tile.put(body * (tile.x < M - 1.5), c["wood_light"], 0.45)
    tile.put(body * (tile.x > M + 2.4), c["dark"], 0.45)
    hoops = tile.mask(lambda p, dx, dy: [_box(p, dx, dy, M - 4.9, G - y, M + 4.9, G - y + 1.0) for y in (10.2, 3.2)])
    tile.put(hoops, c["metal"])
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, G - 11.5, 3.6, ry=0.8)), c["dark"], 0.6)


def crate(tile: Tile, c: dict) -> None:
    _shadow(tile, 6.5)
    body = tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 5.5, G - 10.0, M + 5.5, G))
    tile.put(body, c["wood"])
    frame = tile.mask(lambda p, dx, dy: (_box(p, dx, dy, M - 5.5, G - 10.0, M + 5.5, G - 8.6), _box(p, dx, dy, M - 5.5, G - 1.4, M + 5.5, G), _box(p, dx, dy, M - 5.5, G - 10.0, M - 4.1, G), _box(p, dx, dy, M + 4.1, G - 10.0, M + 5.5, G)))
    tile.put(frame, c["wood_light"], 0.7)
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M - 4.1, G - 8.6), (M + 4.1, G - 1.4)], 1.0)), c["dark"], 0.5)


def lamp_post(tile: Tile, c: dict) -> None:
    _shadow(tile, 2.6)
    tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, M - 0.6, G - 17.0, M + 0.6, G), _box(p, dx, dy, M - 1.8, G - 1.4, M + 1.8, G), _box(p, dx, dy, M - 2.0, G - 20.2, M + 2.0, G - 19.4))), c["metal"])
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, G - 17.4, 5.5), blur=1.6), c["glow"], 0.45)
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 1.5, G - 19.4, M + 1.5, G - 16.0)), _mix(c["glow"], (255, 255, 255), 0.4))


def crystal(tile: Tile, c: dict) -> None:
    shards = [(-3.2, 9.0, -14.0), (0.4, 15.0, 4.0), (3.6, 8.0, 20.0), (-0.8, 6.0, -30.0)]
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, G - 6.0, 8.0), blur=1.8), c["glow"], 0.30)
    for x, length, lean in shards:
        tipx = M + x + math.sin(math.radians(lean)) * length
        tipy = G - math.cos(math.radians(lean)) * length
        w = length * 0.16
        full = [(M + x - w, G), (M + x - w * 0.8, G - length * 0.7), (tipx, tipy), (M + x + w * 0.8, G - length * 0.7), (M + x + w, G)]
        tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, full)), _mix(c["glow"], c["dark"], 0.45))
        lit = [(M + x - w, G), (M + x - w * 0.8, G - length * 0.7), (tipx, tipy), (M + x, G)]
        tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, lit)), _mix(c["glow"], (255, 255, 255), 0.3), 0.85)


def mushrooms(tile: Tile, c: dict) -> None:
    for x, h, r in ((-3.5, 5.0, 3.2), (2.5, 8.0, 4.2), (6.0, 3.6, 2.2)):
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M + x - 0.6, G - h, M + x + 0.6, G)), c["stone_light"])
        cap = tile.mask(lambda p, dx, dy: p.pieslice([(M + x - r) * tile.W / tile.w + dx, (G - h - r * 0.9) * tile.H / tile.h + dy, (M + x + r) * tile.W / tile.w + dx, (G - h + r * 0.9) * tile.H / tile.h + dy], 180, 360, fill=255))
        tile.put(cap, _mix(c["plant"], c["dark"], 0.2))
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M + x - r * 0.9, G - h - 0.2, M + x + r * 0.9, G - h + 0.5)), c["glow"], 0.9)
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + x, G - h + 1.2, r * 0.9, ry=1.6), blur=0.8), c["glow"], 0.32)


def bush(tile: Tile, c: dict) -> None:
    _shadow(tile, 7.5)
    lumps = [(-4.5, 3.6, 3.8), (0.0, 5.6, 5.0), (4.6, 3.8, 3.9), (-1.6, 3.0, 3.4), (2.2, 3.0, 3.2)]
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M + x, G - y, r) for x, y, r in lumps]), _mix(c["plant"], c["dark"], 0.35))
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M + x - 0.8, G - y - 0.8, r * 0.72) for x, y, r in lumps]), c["plant"])
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M + x - 1.4, G - y - 1.6, r * 0.34) for x, y, r in lumps[:3]]), _mix(c["plant"], (255, 255, 220), 0.3), 0.8)
    tile.alpha *= tile.y < G


def flowers(tile: Tile, c: dict) -> None:
    for x, h in ((-5.0, 5.0), (-1.5, 8.0), (2.2, 6.0), (5.4, 4.2)):
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M + x, G), (M + x + 0.6, G - h)], 0.45)), _mix(c["plant"], c["dark"], 0.2))
        tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M + x, G - h * 0.4), (M + x + 2.2, G - h * 0.6), (M + x + 0.4, G - h * 0.55)])), c["plant"])
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + x + 0.6, G - h, 1.25)), c["bloom"])
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + x + 0.6, G - h, 0.45)), c["glow"])


def grass_tuft(tile: Tile, c: dict) -> None:
    blades = [(-5.0, 4.0, -1.6), (-3.2, 7.0, -0.8), (-1.2, 9.5, 0.4), (0.8, 7.5, 1.2), (2.8, 10.0, 2.4), (4.6, 5.5, 2.8), (-0.2, 5.0, -2.4)]
    for k, (x, h, lean) in enumerate(blades):
        colour = c["plant"] if k % 2 else _mix(c["plant"], c["dark"], 0.3)
        tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M + x - 0.7, G), (M + x + 0.7, G), (M + x + lean, G - h)])), colour)


def stone_lantern(tile: Tile, c: dict) -> None:
    _shadow(tile, 4.5)
    stone = tile.mask(lambda p, dx, dy: (_box(p, dx, dy, M - 3.2, G - 1.6, M + 3.2, G), _box(p, dx, dy, M - 1.1, G - 8.0, M + 1.1, G - 1.6), _box(p, dx, dy, M - 3.0, G - 13.0, M + 3.0, G - 8.0), _poly(p, dx, dy, [(M - 4.8, G - 13.0), (M + 4.8, G - 13.0), (M, G - 17.0)])))
    tile.put(stone, c["stone"])
    tile.put(stone * (tile.x < M - 1.0), c["stone_light"], 0.4)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, G - 10.5, 6.0), blur=1.5), c["glow"], 0.36)
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 1.5, G - 12.0, M + 1.5, G - 9.0)), _mix(c["glow"], (255, 255, 255), 0.3))


def rock(tile: Tile, c: dict) -> None:
    _shadow(tile, 7.0)
    body = [(M - 6.5, G), (M - 5.0, G - 4.5), (M - 1.5, G - 7.5), (M + 3.0, G - 6.5), (M + 6.0, G - 3.0), (M + 6.8, G)]
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, body)), c["stone"])
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 6.5, G), (M - 5.0, G - 4.5), (M - 1.5, G - 7.5), (M - 0.5, G - 3.0), (M - 2.5, G)])), c["stone_light"], 0.55)
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M - 0.5, G - 3.0), (M + 3.0, G - 6.5)], 0.35)), c["dark"], 0.5)


def column_stub(tile: Tile, c: dict) -> None:
    _shadow(tile, 5.5)
    body = tile.mask(lambda p, dx, dy: (_box(p, dx, dy, M - 4.6, G - 2.0, M + 4.6, G), _box(p, dx, dy, M - 3.4, G - 12.0, M + 3.4, G - 2.0), _poly(p, dx, dy, [(M - 3.4, G - 12.0), (M - 1.0, G - 14.5), (M + 1.4, G - 12.6), (M + 3.4, G - 13.6), (M + 3.4, G - 12.0)])))
    tile.put(body, c["stone"])
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, M + x - 0.25, G - 11.5, M + x + 0.25, G - 2.4) for x in (-1.7, 0.0, 1.7)]), c["dark"], 0.4)
    tile.put(body * (tile.x < M - 2.0), c["stone_light"], 0.5)


def coral(tile: Tile, c: dict) -> None:
    def branch(x: float, y: float, angle: float, length: float, depth: int, out: list) -> None:
        tip = (x + math.cos(math.radians(angle)) * length, y + math.sin(math.radians(angle)) * length)
        out.append(((x, y), tip, 0.5 + depth * 0.35))
        if depth:
            for turn in (-30.0, 26.0):
                branch(tip[0], tip[1], angle + turn, length * 0.72, depth - 1, out)

    lines: list = []
    branch(M - 3.0, G, -98.0, 4.2, 2, lines)
    branch(M + 2.5, G, -80.0, 4.8, 3, lines)
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [a, b], w) for a, b, w in lines]), c["bloom"])
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, b[0], b[1], 0.5) for _, b, w in lines if w < 0.6]), _mix(c["bloom"], (255, 255, 255), 0.4))


def obelisk(tile: Tile, c: dict) -> None:
    _shadow(tile, 4.5)
    body = [(M - 3.4, G), (M - 2.4, G - 15.0), (M, G - 18.5), (M + 2.4, G - 15.0), (M + 3.4, G)]
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, body)), c["stone"])
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 3.4, G), (M - 2.4, G - 15.0), (M, G - 18.5), (M - 0.4, G)])), c["stone_light"], 0.45)
    signs = tile.mask(lambda p, dx, dy: [_box(p, dx, dy, M - 1.2, G - y, M + 1.2, G - y + 0.6) for y in (5.0, 8.0, 11.0, 14.0)])
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, M - 1.2, G - y, M + 1.2, G - y + 0.6) for y in (5.0, 8.0, 11.0, 14.0)], blur=0.8), c["glow"], 0.5)
    tile.put(signs, c["glow"])


def brazier(tile: Tile, c: dict) -> None:
    _shadow(tile, 4.5)
    tile.put(tile.mask(lambda p, dx, dy: (_line(p, dx, dy, [(M - 3.4, G), (M, G - 7.0), (M + 3.4, G)], 0.8), _poly(p, dx, dy, [(M - 4.6, G - 10.5), (M + 4.6, G - 10.5), (M + 2.6, G - 6.5), (M - 2.6, G - 6.5)]))), c["metal"])
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, G - 12.5, 7.0), blur=1.8), c["glow"], 0.42)
    flame = [(M - 3.2, G - 10.5), (M - 1.6, G - 14.5), (M - 0.4, G - 12.4), (M + 0.6, G - 17.0), (M + 2.0, G - 13.0), (M + 3.2, G - 10.5)]
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, flame)), c["glow"])
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 1.6, G - 10.5), (M + 0.4, G - 14.0), (M + 1.6, G - 10.5)])), _mix(c["glow"], (255, 255, 230), 0.6))


def bones(tile: Tile, c: dict) -> None:
    bone = _mix(c["stone_light"], (230, 220, 200), 0.5)
    tile.put(tile.mask(lambda p, dx, dy: (_dot(p, dx, dy, M - 2.5, G - 3.2, 3.2, ry=2.9), _box(p, dx, dy, M - 4.2, G - 1.6, M - 0.8, G))), bone)
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M - 3.6 + k * 2.2, G - 3.4, 0.85) for k in range(2)]), c["dark"])
    tile.put(tile.mask(lambda p, dx, dy: (_line(p, dx, dy, [(M + 1.0, G - 0.8), (M + 7.5, G - 2.6)], 0.9), _dot(p, dx, dy, M + 7.6, G - 2.7, 0.9), _dot(p, dx, dy, M + 1.0, G - 0.8, 0.9))), bone)


def console(tile: Tile, c: dict) -> None:
    _shadow(tile, 5.5)
    body = tile.mask(lambda p, dx, dy: (_box(p, dx, dy, M - 4.6, G - 9.0, M + 4.6, G), _poly(p, dx, dy, [(M - 4.6, G - 9.0), (M + 4.6, G - 9.0), (M + 3.2, G - 12.0), (M - 3.2, G - 12.0)])))
    tile.put(body, c["metal"])
    tile.put(body * (tile.x < M - 3.0), c["stone_light"], 0.35)
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 2.6, G - 11.2, M + 2.6, G - 9.6)), c["dark"])
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, M - 2.2 + k * 1.6, G - 10.9, M - 1.2 + k * 1.6, G - 9.9) for k in range(3)]), c["glow"], 0.9)
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, M - 3.2, G - 7.0 + k * 2.0, M + 3.2, G - 6.4 + k * 2.0) for k in range(3)]), c["dark"], 0.5)


def cone(tile: Tile, c: dict) -> None:
    _shadow(tile, 4.0)
    tile.put(tile.mask(lambda p, dx, dy: (_poly(p, dx, dy, [(M - 2.6, G - 1.0), (M + 2.6, G - 1.0), (M + 0.7, G - 9.5), (M - 0.7, G - 9.5)]), _box(p, dx, dy, M - 3.6, G - 1.0, M + 3.6, G))), c["bloom"])
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 1.9, G - 4.0), (M + 1.9, G - 4.0), (M + 1.4, G - 6.2), (M - 1.4, G - 6.2)])), (236, 240, 240), 0.9)


def floor_light(tile: Tile, c: dict) -> None:
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 3.6, G - 1.6, M + 3.6, G)), c["metal"])
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 2.4, G - 1.6), (M + 2.4, G - 1.6), (M + 7.0, G - 16.0), (M - 7.0, G - 16.0)]), blur=1.2) * np.clip((tile.y - (G - 16.0)) / 14.0, 0, 1), c["glow"], 0.26)
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 2.4, G - 2.3, M + 2.4, G - 1.6)), _mix(c["glow"], (255, 255, 255), 0.4))


def coil(tile: Tile, c: dict) -> None:
    _shadow(tile, 5.5)
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M, G - 1.2 - k * 1.5, 5.0 - k * 0.5, ry=1.2) for k in range(4)]), c["wood"])
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M, G - 1.5 - k * 1.5, 4.2 - k * 0.5, ry=0.5) for k in range(4)]), c["dark"], 0.45)


def planter(tile: Tile, c: dict) -> None:
    _shadow(tile, 6.0)
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 5.2, G - 5.0), (M + 5.2, G - 5.0), (M + 4.2, G), (M - 4.2, G)])), c["stone"])
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 5.6, G - 6.0, M + 5.6, G - 5.0)), c["stone_light"])
    lumps = [(-3.0, 8.0, 2.8), (0.2, 10.0, 3.4), (3.2, 8.2, 2.7)]
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M + x, G - y, r) for x, y, r in lumps]), _mix(c["plant"], c["dark"], 0.3))
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M + x - 0.6, G - y - 0.6, r * 0.7) for x, y, r in lumps]), c["plant"])


def reeds(tile: Tile, c: dict) -> None:
    for x, h, lean in ((-4.0, 10.0, -1.0), (-1.5, 15.0, 0.6), (1.0, 12.0, 1.4), (3.6, 8.0, 2.0)):
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M + x, G), (M + x + lean * 0.4, G - h * 0.6), (M + x + lean, G - h)], 0.5)), _mix(c["plant"], c["dark"], 0.25))
        if h > 9.0:
            tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + x + lean, G - h - 1.0, 0.7, ry=1.8)), c["wood"])


def shells(tile: Tile, c: dict) -> None:
    star = [(M - 3.0 + math.cos(math.radians(a)) * r, G - 2.2 + math.sin(math.radians(a)) * r * 0.75) for k in range(10) for a, r in [(k * 36 - 90, 3.0 if k % 2 == 0 else 1.2)]]
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, star)), c["bloom"])
    tile.put(tile.mask(lambda p, dx, dy: p.pieslice([(M + 1.5) * tile.W / tile.w + dx, (G - 4.4) * tile.H / tile.h + dy, (M + 7.5) * tile.W / tile.w + dx, (G + 2.2) * tile.H / tile.h + dy], 180, 360, fill=255)), c["stone_light"])
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(M + 4.5, G), (M + 4.5 + k * 1.1, G - 3.0)], 0.3) for k in (-2, -1, 0, 1, 2)]), c["dark"], 0.4)


def anvil(tile: Tile, c: dict) -> None:
    _shadow(tile, 6.0)
    body = tile.mask(lambda p, dx, dy: (_box(p, dx, dy, M - 3.2, G - 1.6, M + 3.2, G), _box(p, dx, dy, M - 1.6, G - 5.2, M + 1.6, G - 1.6), _poly(p, dx, dy, [(M - 7.0, G - 7.6), (M + 4.6, G - 8.4), (M + 4.6, G - 5.2), (M - 3.0, G - 5.2)])))
    tile.put(body, c["metal"])
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M - 6.6, G - 7.6), (M + 4.4, G - 8.3)], 0.5)), c["stone_light"], 0.7)


def coal(tile: Tile, c: dict) -> None:
    lumps = [(-4.0, 1.6, 2.4), (-0.6, 2.8, 3.2), (3.4, 1.8, 2.6), (1.2, 4.6, 2.0), (-2.2, 4.0, 1.8)]
    tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, [(M + x - r, G - y + r * 0.6), (M + x - r * 0.4, G - y - r * 0.7), (M + x + r * 0.7, G - y - r * 0.5), (M + x + r, G - y + r * 0.6)]) for x, y, r in lumps]), c["dark"])
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(M + x - r * 0.4, G - y - r * 0.6), (M + x + r * 0.6, G - y - r * 0.45)], 0.3) for x, y, r in lumps]), c["stone_light"], 0.5)
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M + x, G - y + 0.4, 0.5) for x, y, r in lumps[::2]], blur=0.5), c["glow"], 0.9)
    tile.alpha *= tile.y < G


def amphora(tile: Tile, c: dict) -> None:
    _shadow(tile, 5.0)
    body = tile.mask(lambda p, dx, dy: (_dot(p, dx, dy, M + 1.0, G - 3.4, 5.6, ry=3.2), _box(p, dx, dy, M - 6.0, G - 4.2, M - 4.0, G - 2.4)))
    tile.put(body, c["wood"])
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M - 5.6, G - 3.3, 1.0, ry=1.4)), c["dark"])
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + 0.4, G - 4.6, 3.4, ry=1.0)), c["wood_light"], 0.5)
    tile.alpha *= tile.y < G


#: The colours a thing is drawn with, for each theme.
def star_post(tile: Tile, c: dict) -> None:
    """A short post with a star on it that gives light: a wand in the ground."""
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 0.7, G - 12.0, M + 0.7, G)), c["metal"])
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 0.7, G - 12.0, M - 0.2, G)), c["stone_light"], 0.6)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, G - 12.4, 1.5)), c["bloom"])
    star = [(M + (4.6 if k % 2 == 0 else 2.1) * math.cos(math.radians(-90 + k * 36)), G - 16.4 + (4.6 if k % 2 == 0 else 2.1) * math.sin(math.radians(-90 + k * 36))) for k in range(10)]
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(x * 1.0, y) for x, y in star])), _mix(c["glow"], c["dark"], 0.35))
    inner = [(M + (x - M) * 0.78, G - 16.4 + (y - (G - 16.4)) * 0.78) for x, y in star]
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, inner)), c["glow"])
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M - 0.9, G - 17.4, 0.9)), (255, 255, 255), 0.7)


def meatballs(tile: Tile, c: dict) -> None:
    """Three meatballs in a heap, with sauce on the top one."""
    _shadow(tile, 7.0)
    for x, y, r in ((-3.6, 3.2, 3.4), (3.4, 3.0, 3.2), (0.0, 7.8, 3.5)):
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + x, G - y, r)), _mix(c["wood"], c["dark"], 0.35))
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + x - 0.6, G - y - 0.6, r * 0.78)), c["wood"])
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M + x + ox, G - y + oy, 0.5) for ox, oy in ((-1.4, 0.6), (0.8, -1.2), (1.2, 1.0))]), c["dark"], 0.5)
    tile.put(tile.mask(lambda p, dx, dy: (_dot(p, dx, dy, M, G - 10.2, 2.6, ry=1.3), _box(p, dx, dy, M + 1.2, G - 10.0, M + 2.2, G - 6.4), _dot(p, dx, dy, M + 1.7, G - 6.4, 0.7))), c["bloom"])
    tile.alpha *= tile.y < G


def noodle_nest(tile: Tile, c: dict) -> None:
    """A nest of noodles: a low heap of strands that go round."""
    _shadow(tile, 7.5)
    heap = tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, G - 0.5, 7.0, ry=5.0))
    tile.put(heap, _mix(c["stone_light"], c["dark"], 0.45))
    for k in range(6):
        ry = 4.4 - k * 0.62
        ring = tile.mask(lambda p, dx, dy: p.arc([(M - 6.4 + k * 0.5) * tile.W / tile.w + dx, (G - 0.6 - ry * 2.0) * tile.H / tile.h + dy, (M + 6.4 - k * 0.5) * tile.W / tile.w + dx, (G - 0.6) * tile.H / tile.h + dy], 180, 360, fill=255, width=max(1, int(0.5 * tile.W / tile.w))))
        tile.put(ring, c["stone_light"] if k % 2 else _mix(c["stone_light"], (255, 250, 220), 0.3))
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M + 4.0, G - 4.0), (M + 6.6, G - 6.2), (M + 7.6, G - 4.6)], 0.5)), c["stone_light"])
    tile.alpha *= tile.y < G


def pot(tile: Tile, c: dict) -> None:
    """A pot of water on the boil: its steam gives a little light."""
    _shadow(tile, 6.5)
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M + x, G - y, r) for x, y, r in ((-1.5, 13.0, 2.6), (1.6, 16.0, 2.2), (-0.4, 19.0, 1.8))], blur=1.2), c["glow"], 0.34)
    body = tile.mask(lambda p, dx, dy: (_box(p, dx, dy, M - 5.2, G - 8.4, M + 5.2, G - 1.2), _dot(p, dx, dy, M, G - 1.4, 5.2, ry=1.3)))
    tile.put(body, c["metal"])
    tile.put(body * (tile.x < M - 2.4), _mix(c["metal"], (255, 255, 255), 0.25), 0.6)
    tile.put(body * (tile.x > M + 2.8), c["dark"], 0.45)
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 5.8, G - 9.4, M + 5.8, G - 8.2)), _mix(c["metal"], (255, 255, 255), 0.2))
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, M + s * 5.8 - 0.9, G - 7.4, M + s * 5.8 + 0.9, G - 6.4) for s in (-1.0, 1.0)]), c["dark"])
    tile.alpha *= tile.y < G


def garlic(tile: Tile, c: dict) -> None:
    """A head of garlic and a clove by it."""
    _shadow(tile, 5.0)
    bulb = tile.mask(lambda p, dx, dy: (_dot(p, dx, dy, M - 1.0, G - 3.6, 4.2, ry=3.6), _poly(p, dx, dy, [(M - 2.2, G - 6.4), (M + 0.2, G - 6.4), (M - 0.6, G - 10.2)])))
    tile.put(bulb, _mix(c["stone_light"], (255, 252, 240), 0.5))
    for x in (-3.0, -1.0, 1.0):
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M + x, G - 0.6), (M - 1.0 + (x + 1.0) * 0.3, G - 6.6)], 0.35)) * bulb, c["stone"], 0.6)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + 5.4, G - 1.6, 1.9, ry=1.5)), _mix(c["stone_light"], (255, 252, 240), 0.4))
    tile.alpha *= tile.y < G


def breadsticks(tile: Tile, c: dict) -> None:
    """Breadsticks that stand in a jar."""
    _shadow(tile, 4.5)
    for x, top, lean in ((-2.2, 17.0, -1.6), (-0.4, 19.5, 0.2), (1.4, 16.0, 1.4), (2.6, 18.0, 2.6)):
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M + x, G - 6.0), (M + x + lean, G - top)], 1.1)), _mix(c["stone_light"], c["wood"], 0.3))
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M + x + 0.3, G - 6.0), (M + x + lean + 0.3, G - top)], 0.3)), c["wood"], 0.7)
    jar = tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 3.8, G - 8.6, M + 3.8, G))
    tile.put(jar, c["stone"])
    tile.put(jar * (tile.x < M - 1.8), c["stone_light"], 0.5)
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 4.2, G - 9.4, M + 4.2, G - 8.4)), c["stone_light"])
    tile.put(jar * (np.abs(tile.y - (G - 4.4)) < 0.9), c["bloom"], 0.8)


# -- The port of the pirate dimension, and the village of the ninja
# dimension. These things have no shade under them (no drop shadows).


def rope_coil(tile: Tile, c: dict) -> None:
    """A coil of rope laid flat on the boards, its end hanging over."""
    for k, (ry, r) in enumerate(((2.6, 6.4), (2.2, 5.2), (1.9, 4.0), (1.6, 2.8))):
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, G - 2.0 - k * 1.2, r, ry=ry)), _mix(c["wood_light"], c["dark"], 0.15 + k * 0.08))
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, G - 2.0 - k * 1.2, r - 0.6, ry=ry - 0.5)), c["dark"], 0.35)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, G - 5.6, 1.2, ry=0.6)), c["dark"], 0.7)
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M + 5.6, G - 2.2), (M + 7.8, G - 0.8), (M + 8.6, G - 0.3)], 0.7)), c["wood_light"])


def bollard(tile: Tile, c: dict) -> None:
    """An iron post a ship is tied to, with a turn of rope on it."""
    body = tile.mask(lambda p, dx, dy: (_box(p, dx, dy, M - 2.6, G - 8.0, M + 2.6, G), _dot(p, dx, dy, M, G - 8.0, 3.6, ry=1.6), _box(p, dx, dy, M - 3.4, G - 1.2, M + 3.4, G)))
    tile.put(body, c["metal"])
    tile.put(body * (tile.x < M - 1.0), c["stone_light"], 0.35)
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 2.8, G - 5.6, M + 2.8, G - 4.2)), c["wood_light"])
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M + 2.8, G - 4.9), (M + 8.0, G - 3.0), (M + 11.0, G - 2.4)], 0.6)), c["wood_light"], 0.9)


def fish_basket(tile: Tile, c: dict) -> None:
    """A wicker basket of the day's catch."""
    body = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 5.6, G - 7.0), (M + 5.6, G - 7.0), (M + 4.4, G), (M - 4.4, G)]))
    tile.put(body, c["wood"])
    weave = tile.mask(lambda p, dx, dy: [_box(p, dx, dy, M - 6.0, G - y, M + 6.0, G - y + 0.5) for y in (1.6, 3.4, 5.2)])
    tile.put(weave * body, c["dark"], 0.45)
    fish = [(M - 3.0, G - 7.6, 0.4), (M + 0.4, G - 8.0, -0.3), (M + 3.2, G - 7.4, 0.2)]
    for x, y, lean in fish:
        tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(x - 2.4, y + lean), (x + 1.6, y - 1.0 - lean), (x + 2.6, y), (x + 1.6, y + 1.0 - lean)])), c["stone_light"])
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 5.6, G - 7.4, M + 5.6, G - 6.6)), c["wood_light"])


def net_heap(tile: Tile, c: dict) -> None:
    """A fishing net heaped up to dry, with its floats."""
    heap = [(M - 7.0, G), (M - 5.0, G - 4.0), (M - 1.0, G - 6.0), (M + 3.0, G - 5.0), (M + 6.6, G - 2.0), (M + 7.4, G)]
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, heap)), _mix(c["wood"], c["metal"], 0.5))
    mesh = tile.mask(lambda p, dx, dy: ([_line(p, dx, dy, [(M + x, G), (M + x + 3.0, G - 6.0)], 0.3) for x in range(-8, 8, 2)], [_line(p, dx, dy, [(M + x, G), (M + x - 3.0, G - 6.0)], 0.3) for x in range(-6, 10, 2)]))
    tile.put(mesh * tile.mask(lambda p, dx, dy: _poly(p, dx, dy, heap)), c["dark"], 0.55)
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M + x, G - y, 1.1) for x, y in ((-3.0, 4.2), (1.6, 5.2), (5.0, 2.6))]), c["bloom"])


def harbour_lantern(tile: Tile, c: dict) -> None:
    """A ship's lantern hung on a short post at the edge of the quay."""
    tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, M - 0.7, G - 15.0, M + 0.7, G), _box(p, dx, dy, M - 2.2, G - 1.2, M + 2.2, G), _box(p, dx, dy, M - 0.7, G - 15.0, M + 4.0, G - 14.2))), c["wood"])
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + 3.4, G - 11.0, 5.0), blur=1.6), c["glow"], 0.42)
    tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, M + 2.2, G - 12.8, M + 4.6, G - 9.0), _poly(p, dx, dy, [(M + 1.9, G - 12.8), (M + 4.9, G - 12.8), (M + 3.4, G - 14.2)]))), c["metal"])
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M + 2.7, G - 12.3, M + 4.1, G - 9.5)), _mix(c["glow"], (255, 255, 255), 0.35))


def toro(tile: Tile, c: dict) -> None:
    """A stone lantern of a garden: a foot, a post, a light box with its
    window, and a roof whose corners turn up."""
    stone = tile.mask(lambda p, dx, dy: (
        _box(p, dx, dy, M - 3.4, G - 1.8, M + 3.4, G), _box(p, dx, dy, M - 1.2, G - 8.0, M + 1.2, G - 1.8),
        _box(p, dx, dy, M - 3.2, G - 9.2, M + 3.2, G - 8.0), _box(p, dx, dy, M - 2.6, G - 13.0, M + 2.6, G - 9.2),
        _poly(p, dx, dy, [(M - 5.6, G - 13.0), (M - 4.6, G - 14.0), (M - 2.0, G - 15.6), (M + 2.0, G - 15.6), (M + 4.6, G - 14.0), (M + 5.6, G - 13.0)]),
        _dot(p, dx, dy, M, G - 16.4, 1.0)))
    tile.put(stone, c["stone"])
    tile.put(stone * (tile.x < M - 1.0), c["stone_light"], 0.40)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, G - 11.0, 6.0), blur=1.5), c["glow"], 0.34)
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 1.4, G - 12.2, M + 1.4, G - 9.9)), _mix(c["glow"], (255, 255, 255), 0.3))
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M + x, G - 1.0, 1.0, ry=0.6) for x in (-3.0, 2.4)]), c["plant"], 0.6)


def maple_shrub(tile: Tile, c: dict) -> None:
    """A small maple in its autumn red, round and low."""
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M, G), (M - 0.4, G - 5.0)], 0.9)), c["wood"])
    lumps = [(-4.0, 5.4, 3.6), (0.0, 8.4, 4.6), (4.2, 5.8, 3.6), (-1.8, 4.6, 3.0), (2.0, 4.4, 2.8)]
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M + x, G - y, r) for x, y, r in lumps]), _mix(c["bloom"], c["dark"], 0.35))
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M + x - 0.7, G - y - 0.7, r * 0.72) for x, y, r in lumps]), c["bloom"])
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M + x - 1.3, G - y - 1.4, r * 0.32) for x, y, r in lumps[:3]]), _mix(c["bloom"], (255, 220, 160), 0.4), 0.8)
    tile.alpha *= tile.y < G


def water_bucket(tile: Tile, c: dict) -> None:
    """A wooden bucket of water with a ladle in it, by a door."""
    body = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 4.0, G - 7.0), (M + 4.0, G - 7.0), (M + 3.4, G), (M - 3.4, G)]))
    tile.put(body, c["wood"])
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, M - 4.2, G - y, M + 4.2, G - y + 0.8) for y in (6.0, 2.0)]), c["metal"])
    tile.put(body * (tile.x < M - 1.6), c["wood_light"], 0.4)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, G - 7.0, 4.0, ry=0.9)), _mix(c["stone_light"], c["dark"], 0.3))
    tile.put(tile.mask(lambda p, dx, dy: (_line(p, dx, dy, [(M + 1.0, G - 7.0), (M + 4.0, G - 13.0)], 0.5), _dot(p, dx, dy, M + 0.8, G - 7.2, 1.2, ry=0.6))), c["wood_light"])


def sandal_rack(tile: Tile, c: dict) -> None:
    """A low shelf by a door with wooden sandals on it, two pairs."""
    tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, M - 7.0, G - 5.2, M + 7.0, G - 4.4), _box(p, dx, dy, M - 7.0, G - 1.0, M + 7.0, G - 0.2),
                                          _box(p, dx, dy, M - 7.0, G - 5.2, M - 6.0, G), _box(p, dx, dy, M + 6.0, G - 5.2, M + 7.0, G))), c["wood"])
    for x, y in ((-4.6, 5.2), (-1.8, 5.2), (1.6, 1.0), (4.4, 1.0)):
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M + x - 1.2, G - y - 1.0, M + x + 1.2, G - y)), c["wood_light"])
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M + x - 0.8, G - y - 1.0), (M + x, G - y - 2.0), (M + x + 0.8, G - y - 1.0)], 0.35)), c["bloom"])


def bamboo_fence(tile: Tile, c: dict) -> None:
    """A short piece of fence of split bamboo tied with cord."""
    for k in range(7):
        x = M - 7.2 + k * 2.4
        h = 9.0 + (k % 2) * 1.0
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x - 0.9, G - h, x + 0.9, G)), c["plant"] if k % 2 else _mix(c["plant"], c["dark"], 0.25))
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x - 0.9, G - h * 0.55, x + 0.9, G - h * 0.55 + 0.35)), c["dark"], 0.4)
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, M - 8.4, G - y, M + 8.4, G - y + 0.9) for y in (7.0, 3.0)]), c["wood"])
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M - 7.2 + k * 2.4, G - 6.6, 0.5) for k in range(7)]), c["bloom"], 0.7)


def _palette(dark: RGB, stone: RGB, stone_light: RGB, wood: RGB, metal: RGB, plant: RGB, bloom: RGB, glow: RGB) -> dict:
    return {"dark": dark, "stone": stone, "stone_light": stone_light, "wood": wood, "wood_light": _mix(wood, (255, 235, 200), 0.3), "metal": metal, "plant": plant, "bloom": bloom, "glow": glow}


#: The six things of each theme, and its colours.
DECOR: dict[str, tuple[tuple[Draw, ...], dict]] = {
    "lab": ((console, floor_light, cone, coil, crate, floor_light), _palette((8, 28, 38), (30, 70, 82), (70, 130, 140), (40, 84, 92), (38, 80, 92), (60, 150, 130), (236, 150, 70), (120, 236, 220))),
    # The station: consoles, floor lights, crates of freight, coiled cable.
    "orbital": ((console, crate, floor_light, coil, crate, console), _palette((14, 18, 30), (58, 70, 90), (130, 150, 172), (90, 76, 60), (70, 84, 104), (70, 140, 110), (246, 176, 76), (110, 220, 240))),
    "orbital_truss": ((floor_light, coil, console, floor_light, crate, coil), _palette((10, 12, 24), (52, 64, 86), (120, 140, 162), (90, 76, 60), (64, 78, 98), (70, 140, 110), (246, 176, 76), (110, 220, 240))),
    "alarm": ((crate, cone, coil, console, cone, floor_light), _palette((6, 7, 14), (34, 38, 56), (84, 90, 118), (52, 50, 66), (44, 48, 70), (110, 60, 60), (236, 150, 70), (255, 92, 72))),
    "undertown": ((barrel, crate, mushrooms, lamp_post, coil, rock), _palette((10, 16, 16), (72, 68, 62), (122, 112, 98), (104, 76, 50), (52, 64, 66), (64, 110, 72), (200, 150, 90), (255, 196, 120))),
    "hub": ((planter, lamp_post, crate, floor_light, planter, cone), _palette((15, 15, 46), (52, 52, 110), (100, 102, 170), (70, 64, 120), (60, 60, 120), (90, 150, 130), (236, 150, 90), (255, 206, 140))),
    "basement": ((anvil, coal, barrel, crate, brazier, coal), _palette((26, 12, 10), (70, 40, 34), (130, 80, 60), (104, 62, 40), (62, 46, 44), (90, 110, 60), (200, 90, 50), (255, 160, 70))),
    "boss": ((brazier, bones, column_stub, bones, rock, obelisk), _palette((22, 6, 12), (80, 30, 42), (140, 60, 70), (90, 40, 40), (50, 20, 26), (110, 60, 60), (200, 60, 60), (255, 120, 76))),
    # The Noodly Temple: what is on the floor of a kitchen. `stone` is the
    # colour of pasta, `wood` of a meatball and `bloom` of sauce.
    # The town of the Math dimension: amphorae, planters, a column stub, a lamp.
    "math_town": ((amphora, planter, column_stub, flowers, bush, lamp_post), _palette((70, 76, 90), (214, 204, 182), (246, 240, 226), (150, 110, 80), (60, 70, 90), (90, 140, 90), (226, 90, 110), (255, 220, 150))),
    # The gate hall under the Math town: amphorae, crates of luggage, lamps.
    "math_undercroft": ((amphora, crate, lamp_post, column_stub, crate, lamp_post), _palette((34, 38, 54), (150, 134, 110), (196, 178, 148), (120, 86, 60), (60, 64, 80), (90, 120, 90), (214, 170, 84), (255, 204, 128))),
    # Inside the town's houses: pots and a planter by the walls.
    "math_interior": ((amphora, planter, flowers, amphora, planter, flowers), _palette((60, 44, 36), (236, 222, 198), (255, 240, 220), (176, 108, 78), (90, 70, 58), (90, 140, 90), (226, 90, 110), (255, 214, 150))),
    "noodly": ((meatballs, noodle_nest, pot, garlic, breadsticks, bush), _palette((52, 26, 18), (196, 150, 86), (238, 204, 132), (124, 66, 40), (120, 112, 118), (70, 132, 66), (172, 44, 32), (255, 226, 150))),
    "cave": ((crystal, mushrooms, rock, mushrooms, crystal, rock), _palette((16, 15, 36), (54, 52, 98), (100, 100, 160), (80, 66, 90), (60, 60, 100), (60, 130, 130), (236, 130, 232), (124, 222, 255))),
    "cove": ((barrel, crate, coil, shells, reeds, lamp_post), _palette((12, 30, 40), (60, 96, 104), (120, 164, 164), (122, 88, 58), (70, 84, 92), (70, 140, 110), (236, 130, 120), (255, 200, 120))),
    "water": ((coral, amphora, column_stub, shells, coral, rock), _palette((8, 34, 52), (40, 96, 114), (96, 164, 172), (150, 110, 80), (50, 100, 116), (50, 150, 120), (255, 132, 126), (150, 240, 200))),
    "starlight": ((star_post, flowers, bush, grass_tuft, mushrooms, flowers), _palette((96, 70, 130), (206, 170, 214), (255, 232, 244), (190, 130, 150), (232, 196, 226), (120, 204, 170), (255, 130, 176), (255, 240, 170))),
    "stardune": ((star_post, amphora, rock, grass_tuft, obelisk, shells), _palette((124, 70, 70), (226, 170, 124), (255, 226, 176), (176, 112, 76), (232, 196, 150), (112, 176, 132), (255, 150, 130), (255, 244, 180))),
    "starless": ((crystal, brazier, rock, mushrooms, crystal, obelisk), _palette((12, 8, 28), (58, 46, 104), (120, 100, 180), (70, 44, 80), (52, 40, 92), (120, 60, 130), (255, 100, 180), (255, 120, 196))),
    "void_castle": ((brazier, column_stub, bones, obelisk, brazier, column_stub), _palette((30, 14, 40), (104, 66, 116), (170, 124, 176), (110, 60, 60), (70, 44, 80), (150, 60, 90), (255, 120, 60), (255, 190, 96))),
    "primeval": ((bones, bush, rock, grass_tuft, mushrooms, bush), _palette((22, 28, 16), (104, 96, 78), (214, 204, 176), (104, 70, 44), (92, 86, 74), (62, 140, 58), (236, 150, 60), (255, 200, 110))),
    "forest": ((stone_lantern, bush, flowers, grass_tuft, rock, bush), _palette((20, 26, 20), (92, 98, 90), (150, 156, 140), (100, 70, 46), (70, 70, 64), (78, 136, 62), (236, 120, 150), (255, 190, 100))),
    # The Evil dimension: dead bushes, bones, stones and a brazier at the road.
    # The port: rope, mooring posts, the catch, nets, a lantern.
    "pirate_port": ((rope_coil, bollard, fish_basket, harbour_lantern, net_heap, bollard), _palette((40, 30, 24), (120, 112, 104), (196, 186, 170), (128, 94, 62), (58, 62, 70), (70, 110, 96), (214, 96, 60), (255, 200, 120))),
    # The village: a stone lantern, maples, a bucket, sandals, a fence.
    "ninja_village": ((toro, maple_shrub, water_bucket, sandal_rack, maple_shrub, bamboo_fence), _palette((30, 24, 30), (132, 128, 122), (190, 186, 176), (110, 76, 52), (70, 66, 64), (138, 150, 92), (206, 70, 48), (255, 186, 110))),
    "evil_forest": ((bones, bush, rock, grass_tuft, brazier, rock), _palette((8, 4, 6), (60, 50, 52), (110, 92, 90), (60, 36, 30), (50, 44, 48), (54, 44, 34), (200, 40, 32), (255, 110, 60))),
    # Castle Godwin: braziers, crates of the regime, anvils of its forge.
    "castle_godwin": ((brazier, crate, barrel, anvil, brazier, crate), _palette((10, 10, 16), (82, 92, 112), (134, 146, 168), (84, 54, 40), (46, 50, 62), (60, 60, 50), (200, 40, 32), (255, 132, 48))),
    # The lab: coils, consoles, barrels of what the vats drink.
    "castle_godwin_lab": ((coil, console, barrel, coil, crate, console), _palette((6, 12, 10), (70, 88, 86), (118, 150, 140), (84, 54, 40), (60, 70, 70), (60, 120, 80), (120, 255, 150), (190, 230, 255))),
    "castle_godwin_throne": ((brazier, bones, column_stub, brazier, bones, column_stub), _palette((8, 6, 10), (78, 70, 84), (130, 118, 134), (84, 54, 40), (40, 40, 48), (60, 50, 50), (200, 40, 32), (255, 132, 48))),
    "skybridge": ((bush, flowers, column_stub, grass_tuft, planter, flowers), _palette((86, 100, 142), (160, 172, 204), (224, 230, 244), (150, 120, 90), (130, 144, 180), (106, 176, 96), (255, 150, 170), (255, 236, 150))),
    "open_sky": ((grass_tuft, rock, flowers, bush, grass_tuft, rock), _palette((104, 92, 92), (176, 164, 150), (232, 222, 204), (150, 112, 74), (140, 136, 140), (116, 178, 90), (255, 190, 110), (255, 240, 170))),
    "eclipse": ((obelisk, crystal, rock, obelisk, rock, crystal), _palette((10, 12, 36), (40, 46, 104), (84, 90, 164), (60, 60, 110), (44, 50, 110), (60, 150, 140), (172, 112, 255), (92, 232, 200))),
}


#: The things of the decor that give light: where the light is in the square
#: (x, and how far over the ground), and how strong the pool of light round
#: it is.
LIGHTS: dict[Draw, tuple[float, float, float]] = {
    lamp_post: (M, 17.4, 0.36),
    harbour_lantern: (M + 3.4, 11.0, 0.34),
    toro: (M, 11.0, 0.32),
    stone_lantern: (M, 10.5, 0.32),
    brazier: (M, 12.5, 0.40),
    floor_light: (M, 7.0, 0.26),
    crystal: (M, 7.0, 0.22),
    mushrooms: (M + 1.0, 6.0, 0.14),
    console: (M, 10.4, 0.12),
}
#: A pool of light is drawn this many times the side of a decor square, with
#: its middle on the middle of the square.
GLOW_SCALE = 3


def glow_strip(theme_key: str) -> Image.Image:
    """The pools of light of the decor of a theme: a strip of the same
    squares as `strip`, one for each thing. The square of a thing that gives
    no light is empty. The game draws a square `GLOW_SCALE` times the size of
    the decor square, behind the thing."""
    draws, colours = DECOR[theme_key]
    px = CELL_PX
    out = np.zeros((px, px * VARIANTS, 4), dtype=np.float32)
    ys, xs = np.mgrid[0:px, 0:px]
    u = (xs + 0.5) / px
    v = (ys + 0.5) / px
    for index, draw in enumerate(draws):
        if draw not in LIGHTS:
            continue
        x, up, strength = LIGHTS[draw]
        # The decor square is the middle third of this one.
        cu = 0.5 + (x / CELL - 0.5) / GLOW_SCALE
        cv = 0.5 + ((G - up) / CELL - 0.5) / GLOW_SCALE
        # The pool ends inside the square on each side.
        reach = min(cu, 1.0 - cu, cv, 1.0 - cv) * 0.96
        d = np.sqrt((u - cu) ** 2 + (v - cv) ** 2) / reach
        fall = np.clip(1.0 - d, 0.0, 1.0) ** 2.2
        out[:, index * px : (index + 1) * px, :3] = colours["glow"]
        out[:, index * px : (index + 1) * px, 3] = fall * strength * 255.0
    return Image.fromarray(np.rint(out).astype(np.uint8), "RGBA")


def strip(theme_key: str) -> Image.Image:
    """The decor picture of a theme."""
    draws, colours = DECOR[theme_key]
    assert len(draws) == VARIANTS
    px = CELL_PX
    out = Image.new("RGBA", (px * VARIANTS, px), (0, 0, 0, 0))
    for index, draw in enumerate(draws):
        tile = Tile((CELL, CELL), False, False, theme_key, "decor", index)
        draw(tile, colours)
        # Low contrast and a little dark: it is scenery, not a thing to use.
        tile.rgb = tile.rgb * 0.88
        cell = tile.publish(SUPERSAMPLE)
        # The empty part of each square takes no colour from the next square.
        out.paste(cell, (index * px, 0))
    return out
