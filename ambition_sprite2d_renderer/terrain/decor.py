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
def _palette(dark: RGB, stone: RGB, stone_light: RGB, wood: RGB, metal: RGB, plant: RGB, bloom: RGB, glow: RGB) -> dict:
    return {"dark": dark, "stone": stone, "stone_light": stone_light, "wood": wood, "wood_light": _mix(wood, (255, 235, 200), 0.3), "metal": metal, "plant": plant, "bloom": bloom, "glow": glow}


#: The six things of each theme, and its colours.
DECOR: dict[str, tuple[tuple[Draw, ...], dict]] = {
    "lab": ((console, floor_light, cone, coil, crate, floor_light), _palette((8, 28, 38), (30, 70, 82), (70, 130, 140), (40, 84, 92), (38, 80, 92), (60, 150, 130), (236, 150, 70), (120, 236, 220))),
    "alarm": ((crate, cone, coil, console, cone, floor_light), _palette((6, 7, 14), (34, 38, 56), (84, 90, 118), (52, 50, 66), (44, 48, 70), (110, 60, 60), (236, 150, 70), (255, 92, 72))),
    "hub": ((planter, lamp_post, crate, floor_light, planter, cone), _palette((15, 15, 46), (52, 52, 110), (100, 102, 170), (70, 64, 120), (60, 60, 120), (90, 150, 130), (236, 150, 90), (255, 206, 140))),
    "basement": ((anvil, coal, barrel, crate, brazier, coal), _palette((26, 12, 10), (70, 40, 34), (130, 80, 60), (104, 62, 40), (62, 46, 44), (90, 110, 60), (200, 90, 50), (255, 160, 70))),
    "boss": ((brazier, bones, column_stub, bones, rock, obelisk), _palette((22, 6, 12), (80, 30, 42), (140, 60, 70), (90, 40, 40), (50, 20, 26), (110, 60, 60), (200, 60, 60), (255, 120, 76))),
    "cave": ((crystal, mushrooms, rock, mushrooms, crystal, rock), _palette((16, 15, 36), (54, 52, 98), (100, 100, 160), (80, 66, 90), (60, 60, 100), (60, 130, 130), (236, 130, 232), (124, 222, 255))),
    "cove": ((barrel, crate, coil, shells, reeds, lamp_post), _palette((12, 30, 40), (60, 96, 104), (120, 164, 164), (122, 88, 58), (70, 84, 92), (70, 140, 110), (236, 130, 120), (255, 200, 120))),
    "water": ((coral, amphora, column_stub, shells, coral, rock), _palette((8, 34, 52), (40, 96, 114), (96, 164, 172), (150, 110, 80), (50, 100, 116), (50, 150, 120), (255, 132, 126), (150, 240, 200))),
    "forest": ((stone_lantern, bush, flowers, grass_tuft, rock, bush), _palette((20, 26, 20), (92, 98, 90), (150, 156, 140), (100, 70, 46), (70, 70, 64), (78, 136, 62), (236, 120, 150), (255, 190, 100))),
    "skybridge": ((bush, flowers, column_stub, grass_tuft, planter, flowers), _palette((86, 100, 142), (160, 172, 204), (224, 230, 244), (150, 120, 90), (130, 144, 180), (106, 176, 96), (255, 150, 170), (255, 236, 150))),
    "eclipse": ((obelisk, crystal, rock, obelisk, rock, crystal), _palette((10, 12, 36), (40, 46, 104), (84, 90, 164), (60, 60, 110), (44, 50, 110), (60, 150, 140), (172, 112, 255), (92, 232, 200))),
}


#: The things of the decor that give light: where the light is in the square
#: (x, and how far over the ground), and how strong the pool of light round
#: it is.
LIGHTS: dict[Draw, tuple[float, float, float]] = {
    lamp_post: (M, 17.4, 0.36),
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
