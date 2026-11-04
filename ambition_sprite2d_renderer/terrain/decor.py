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


# The things of a military building. They have no shade on the ground under
# them: a thing has form shade on its own faces only.


def _ammo_box(tile: Tile, c: dict, x0: float, y1: float, w: float, h: float) -> None:
    """A box of ammunition of the `wood` colour: its foot at `y1`, from `x0`,
    `w` wide and `h` high. A lid with two latches, a rope handle at the end
    and a stencilled mark of the light stone colour on the front."""
    body = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0, y1 - h, x0 + w, y1))
    tile.put(body, c["wood"])
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0, y1 - h, x0 + w, y1 - h + 1.4)), c["wood_light"], 0.45)
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0, y1 - h + 1.4, x0 + w, y1 - h + 1.8)), c["dark"], 0.55)
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0, y1 - h, x0 + 0.6, y1)), c["wood_light"], 0.35)
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + w - 0.8, y1 - h, x0 + w, y1)), c["dark"], 0.45)
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x, y1 - h + 0.6, x + 1.2, y1 - h + 2.6) for x in (x0 + w * 0.22, x0 + w * 0.72)]), c["metal"])
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 1.2, y1 - h * 0.45, x0 + 2.2, y1 - h * 0.45 + 1.0)), c["dark"], 0.6)
    tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, x0 + w * 0.35, y1 - h * 0.55, x0 + w * 0.82, y1 - h * 0.55 + 0.7), _box(p, dx, dy, x0 + w * 0.35, y1 - h * 0.30, x0 + w * 0.62, y1 - h * 0.30 + 0.6))), c["stone_light"], 0.75)


def ammo_crate(tile: Tile, c: dict) -> None:
    """One box of ammunition."""
    _ammo_box(tile, c, M - 6.0, G, 12.0, 7.5)


def ammo_stack(tile: Tile, c: dict) -> None:
    """Two boxes of ammunition, a small one on a large one."""
    _ammo_box(tile, c, M - 7.0, G, 14.0, 6.5)
    _ammo_box(tile, c, M - 4.6, G - 6.5, 9.0, 5.0)


def sandbags(tile: Tile, c: dict) -> None:
    """Bags of sand of the light stone colour, three on the floor and two on
    them. Each bag has light on its top and shade on its lower half."""
    bags = [(M - 5.6, G - 1.9), (M, G - 1.9), (M + 5.6, G - 1.9), (M - 2.8, G - 5.3), (M + 2.8, G - 5.3)]
    canvas = _mix(c["stone_light"], c["dark"], 0.18)
    for x, y in bags:
        bag = tile.mask(lambda p, dx, dy: _dot(p, dx, dy, x, y, 3.0, ry=1.95))
        tile.put(bag, canvas)
        tile.put(bag * (tile.y > y + 0.3), c["dark"], 0.28)
        tile.put(bag * (tile.y < y - 1.0), (255, 248, 226), 0.16)
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(x + 2.0, y - 1.2), (x + 2.4, y + 1.2)], 0.3)), c["dark"], 0.45)
    tile.alpha *= tile.y < G


def jerrycan(tile: Tile, c: dict) -> None:
    """A can of fuel of the `wood` colour: the pressed X on its side, three
    handles on top and a spout cap at one corner."""
    x0, x1, top = M - 3.6, M + 3.6, G - 10.5
    body = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(x0, G), (x1, G), (x1, top + 1.0), (x1 - 1.0, top), (x0, top)]))
    tile.put(body, c["wood"])
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, M - 2.8 + k * 2.0, top - 1.6, M - 1.8 + k * 2.0, top) for k in range(3)]), c["metal"])
    tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, x1 - 1.6, top - 1.8, x1 - 0.2, top + 0.4))), c["metal"])
    x_pts = [((x0 + 1.0, top + 2.0), (x1 - 1.0, G - 1.6)), ((x1 - 1.0, top + 2.0), (x0 + 1.0, G - 1.6))]
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [a, b], 0.5) for a, b in x_pts]), c["dark"], 0.35)
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(a[0] - 0.4, a[1]), (b[0] - 0.4, b[1])], 0.3) for a, b in x_pts]), c["wood_light"], 0.35)
    tile.put(body * (tile.x < x0 + 0.7), c["wood_light"], 0.4)
    tile.put(body * (tile.x > x1 - 0.8), c["dark"], 0.4)


def oil_drum(tile: Tile, c: dict) -> None:
    """A drum of steel with two ribs and a band of the light stone colour:
    light on its left, shade on its right, as a round thing."""
    x0, x1, top = M - 4.4, M + 4.4, G - 11.0
    body = tile.mask(lambda p, dx, dy: (_box(p, dx, dy, x0, top, x1, G), _dot(p, dx, dy, M, top, 4.4, ry=0.9)))
    tile.put(body, c["metal"])
    tile.put(body * (tile.y > G - 7.0) * (tile.y < G - 4.4), _mix(c["stone_light"], c["dark"], 0.2), 0.8)
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x0, y, x1, y + 0.6) for y in (top + 3.2, G - 3.2)]), c["dark"], 0.45)
    across = (tile.x - x0) / (x1 - x0)
    tile.put(body * np.clip(1.0 - np.abs(across - 0.25) / 0.18, 0.0, 1.0), (255, 255, 255), 0.14)
    tile.put(body * np.clip((across - 0.6) / 0.4, 0.0, 1.0), c["dark"], 0.45)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, top, 3.6, ry=0.55)), c["dark"], 0.5)


def extinguisher(tile: Tile, c: dict) -> None:
    """A fire extinguisher of the `bloom` colour: a round-topped body with a
    pale label, a valve and a hose that hangs to one side."""
    x0, x1, top = M - 1.9, M + 1.9, G - 9.5
    body = tile.mask(lambda p, dx, dy: (_box(p, dx, dy, x0, top, x1, G), _dot(p, dx, dy, M, top, 1.9, ry=1.3)))
    tile.put(body, c["bloom"])
    tile.put(body * (tile.x < x0 + 0.8), (255, 236, 220), 0.22)
    tile.put(body * (tile.x > x1 - 0.9), c["dark"], 0.40)
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 0.4, G - 6.4, x1 - 0.4, G - 3.6)), _mix(c["stone_light"], (240, 236, 220), 0.4), 0.75)
    tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, M - 0.6, top - 2.6, M + 0.6, top - 1.0), _box(p, dx, dy, M - 1.8, top - 2.8, M + 1.4, top - 2.2))), c["metal"])
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M + 0.6, top - 1.8), (x1 + 1.4, top - 0.6), (x1 + 1.8, top + 3.0), (x1 + 1.4, top + 5.0)], 0.5)), c["dark"])
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0, G - 0.8, x1, G)), c["dark"], 0.6)


# -- Eureka, the institute town of the Science dimension. These things have
# no shade under them (no drop shadows).


def campus_bench(tile: Tile, c: dict) -> None:
    """A park bench of slats on iron legs, by a path of the campus."""
    tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, M - 8.0, G - 5.4, M - 7.0, G), _box(p, dx, dy, M + 7.0, G - 5.4, M + 8.0, G),
                                          _box(p, dx, dy, M - 8.0, G - 10.0, M - 7.2, G - 5.4), _box(p, dx, dy, M + 7.2, G - 10.0, M + 8.0, G - 5.4))), c["metal"])
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 9.0, G - 5.8, M + 9.0, G - 4.8)), c["wood"])
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, M - 8.6, G - 10.0 + k * 1.6, M + 8.6, G - 9.1 + k * 1.6) for k in range(3)]), c["wood"])
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, M - 8.6, G - 10.0 + k * 1.6, M + 8.6, G - 9.6 + k * 1.6) for k in range(3)]), c["wood_light"], 0.5)


def telescope(tile: Tile, c: dict) -> None:
    """A small brass telescope on a tripod, pointed at the sky."""
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(M, G - 9.0), (M + x, G)], 0.55) for x in (-4.4, 0.6, 4.6)]), c["metal"])
    tube = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 5.6, G - 7.6), (M - 4.8, G - 9.2), (M + 6.4, G - 15.4), (M + 5.6, G - 17.0)]))
    tile.put(tube, c["wood"])
    tile.put(tube * (tile.y < G - 12.0), c["wood_light"], 0.35)
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M + 4.6, G - 14.0), (M + 7.2, G - 15.6), (M + 6.2, G - 17.8), (M + 3.6, G - 16.2)])), c["glow"], 0.6)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, G - 9.0, 1.0)), c["dark"])


def bike_rack(tile: Tile, c: dict) -> None:
    """A rack of bent steel hoops with one bicycle in it."""
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(M + x, G), (M + x, G - 5.0), (M + x + 2.0, G - 6.6), (M + x + 4.0, G - 5.0), (M + x + 4.0, G)], 0.5) for x in (-9.0, -3.0, 3.0)]), c["metal"])
    wheels = tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M + x, G - 2.8, 2.8) for x in (-2.8, 4.4)])
    hubs = tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M + x, G - 2.8, 2.1) for x in (-2.8, 4.4)])
    tile.put(np.clip(wheels - hubs, 0.0, 1.0), c["dark"], 0.85)
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M - 2.8, G - 2.8), (M + 0.6, G - 6.2), (M + 4.4, G - 2.8), (M + 1.0, G - 2.8), (M + 0.6, G - 6.2), (M + 1.4, G - 7.6)], 0.5)), c["bloom"])
    tile.alpha *= tile.y < G


def notice_board(tile: Tile, c: dict) -> None:
    """A board of the campus on two posts, papers pinned to it."""
    tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, M - 6.0, G - 8.0, M - 5.0, G), _box(p, dx, dy, M + 5.0, G - 8.0, M + 6.0, G))), c["wood"])
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 7.0, G - 16.0, M + 7.0, G - 8.0)), c["wood"])
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 6.2, G - 15.2, M + 6.2, G - 8.8)), _mix(c["wood_light"], c["stone_light"], 0.5))
    for x, y, w, h in ((-5.4, 14.6, 3.6, 4.4), (-1.2, 14.2, 3.0, 3.2), (2.4, 14.8, 3.4, 4.8), (-0.8, 10.6, 3.6, 1.6)):
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M + x, G - y, M + x + w, G - y + h)), c["stone_light"])
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + x + w * 0.5, G - y + 0.4, 0.35)), c["bloom"])


def _void_thing(tile: Tile, c: dict, polys: list, cracks: list = ()) -> None:
    """Draw `polys` as things of the void: black (`dark`), with a thin edge
    of `stone_light` round each one and along each crack. The edge is grey,
    not the white of a void enemy: the decor is not a thing of the play."""
    tile.put(tile.mask(lambda p, dx, dy: [(_poly(p, dx, dy, pts), _line(p, dx, dy, pts + pts[:1], 1.3)) for pts in polys]), c["stone_light"])
    body = tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, pts) for pts in polys])
    cut = tile.mask(lambda p, dx, dy: [_line(p, dx, dy, pts, 0.55) for pts in cracks])
    tile.put(body * (1.0 - cut), c["dark"])
    tile.alpha *= tile.y < G


def void_obelisk(tile: Tile, c: dict) -> None:
    """An obelisk of the void with a crack down it, its tip broken off."""
    body = [(M - 3.4, G + 1.0), (M - 2.5, G - 14.5), (M - 0.6, G - 17.5), (M + 0.4, G - 15.8), (M + 1.4, G - 17.0), (M + 2.5, G - 14.5), (M + 3.4, G + 1.0)]
    _void_thing(tile, c, [body], [[(M + 0.4, G - 15.8), (M - 0.6, G - 11.0), (M + 0.8, G - 6.5), (M - 0.4, G - 1.0)]])


def fallen_star(tile: Tile, c: dict) -> None:
    """A star that went out and fell: one point in the ground, on its side,
    with a crack across it. It has no eyes and it is grey at its edge: it is
    not the Void Star."""
    cx, cy, r = M + 0.6, G - 6.2, 7.0
    star = [(cx + (r if k % 2 == 0 else r * 0.44) * math.cos(math.radians(-90.0 + 160.0 + k * 36.0)), cy + (r if k % 2 == 0 else r * 0.44) * math.sin(math.radians(-90.0 + 160.0 + k * 36.0))) for k in range(10)]
    _void_thing(tile, c, [star], [[(cx - 5.0, cy - 3.0), (cx - 0.5, cy + 0.6), (cx + 4.6, cy - 1.0)]])


def void_shards(tile: Tile, c: dict) -> None:
    """Splinters of the void that come up out of the ground."""
    shards = []
    for x, h, lean, w in ((-3.6, 8.0, -18.0, 1.4), (0.2, 13.0, 4.0, 1.8), (3.8, 6.0, 24.0, 1.2)):
        tip = (M + x + math.sin(math.radians(lean)) * h, G - math.cos(math.radians(lean)) * h)
        shards.append([(M + x - w, G + 1.0), (tip[0] - w * 0.2, tip[1] + h * 0.35), tip, (M + x + w, G + 1.0)])
    _void_thing(tile, c, shards)


def broken_column(tile: Tile, c: dict) -> None:
    """The stub of a column of the castle, broken at the top, with a crack."""
    body = [(M - 4.6, G + 1.0), (M - 4.6, G - 2.0), (M - 3.4, G - 2.0), (M - 3.4, G - 11.5), (M - 1.4, G - 13.6), (M + 0.2, G - 11.8), (M + 1.6, G - 13.0), (M + 3.4, G - 10.2), (M + 3.4, G - 2.0), (M + 4.6, G - 2.0), (M + 4.6, G + 1.0)]
    _void_thing(tile, c, [body], [[(M + 0.2, G - 11.8), (M + 1.4, G - 8.0), (M - 0.4, G - 4.6)]])


# The Art dimension. `bloom` is magenta paint, `glow` yellow, `plant`
# cyan; `wood` is a brush handle and `stone_light` paper.


def paint_pots(tile: Tile, c: dict) -> None:
    """Two pots of paint: one stands, one lies on its side, its paint out."""
    _shadow(tile, 8.0)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + 3.4, G - 0.6, 6.0, ry=1.2)), c["bloom"], 0.75)
    pot = tile.mask(lambda p, dx, dy: (_box(p, dx, dy, M - 7.0, G - 8.0, M - 0.8, G), _dot(p, dx, dy, M - 3.9, G - 8.0, 3.1, ry=0.9)))
    tile.put(pot, c["metal"])
    tile.put(pot * (tile.x < M - 5.2), _mix(c["metal"], (255, 255, 255), 0.25), 0.5)
    tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, M - 7.0, G - 6.6, M - 0.8, G - 4.2), _dot(p, dx, dy, M - 3.9, G - 8.0, 2.5, ry=0.6))), c["plant"])
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, M - 6.0 + k * 2.0, G - 8.0, M - 5.2 + k * 2.0, G - 5.6 - k) for k in range(3)]), c["plant"], 0.8)
    lying = tile.mask(lambda p, dx, dy: (_box(p, dx, dy, M + 1.0, G - 5.0, M + 7.0, G), _dot(p, dx, dy, M + 7.0, G - 2.5, 0.9, ry=2.5)))
    tile.put(lying, _mix(c["metal"], c["dark"], 0.2))
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + 7.0, G - 2.5, 0.7, ry=2.0)), c["bloom"])
    tile.alpha *= tile.y < G


def brush_jar(tile: Tile, c: dict) -> None:
    """A jar of water with brushes in it, each with paint on its hairs."""
    _shadow(tile, 5.0)
    for x, top, lean, colour in ((-1.8, 17.0, -2.4, c["bloom"]), (0.2, 19.0, 0.4, c["plant"]), (1.8, 16.0, 2.6, c["glow"])):
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M + x, G - 6.0), (M + x + lean, G - top)], 0.8)), c["wood"])
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + x + lean * 1.05, G - top - 1.0, 0.9, ry=1.8)), colour)
    jar = tile.mask(lambda p, dx, dy: (_box(p, dx, dy, M - 3.6, G - 7.4, M + 3.6, G), _dot(p, dx, dy, M, G - 7.4, 3.6, ry=0.7)))
    tile.put(jar, _mix(c["stone_light"], c["plant"], 0.35), 0.75)
    tile.put(jar * (tile.y > G - 5.0), _mix(c["plant"], c["bloom"], 0.4), 0.45)
    tile.put(jar * (tile.x < M - 2.4), (255, 255, 255), 0.30)
    tile.alpha *= tile.y < G


def crayon_stubs(tile: Tile, c: dict) -> None:
    """Three stubs of crayon that stand on their ends, each worn to a point."""
    _shadow(tile, 6.5)
    for x, h, colour in ((-4.2, 7.0, c["bloom"]), (0.0, 10.0, c["glow"]), (4.0, 6.0, c["plant"])):
        body = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M + x - 1.6, G), (M + x + 1.6, G), (M + x + 1.6, G - h), (M + x + 0.4, G - h - 2.2), (M + x - 0.6, G - h - 1.8), (M + x - 1.6, G - h)]))
        tile.put(body, _mix(colour, c["dark"], 0.15))
        tile.put(body * (tile.y > G - h * 0.65) * (tile.y < G - h * 0.25), _mix(c["stone_light"], c["dark"], 0.2), 0.8)
        tile.put(body * (tile.x < M + x - 0.6), (255, 255, 255), 0.18)
    tile.alpha *= tile.y < G


def crumpled_paper(tile: Tile, c: dict) -> None:
    """A page that someone screwed up and threw down: a ball of folds."""
    _shadow(tile, 5.5)
    ball = [(M - 5.0, G), (M - 5.6, G - 3.4), (M - 3.6, G - 7.0), (M - 0.4, G - 8.2), (M + 3.4, G - 7.0), (M + 5.4, G - 4.0), (M + 4.6, G)]
    body = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, ball))
    tile.put(body, c["stone_light"])
    tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, pts) for pts in ([(M - 0.4, G - 8.2), (M + 1.0, G - 3.4), (M + 5.4, G - 4.0), (M + 3.4, G - 7.0)], [(M - 5.0, G), (M - 2.0, G - 3.0), (M + 1.0, G - 3.4), (M + 4.6, G)])]), c["stone"], 0.55)
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M - 3.6, G - 7.0), (M - 2.0, G - 3.0), (M + 1.0, G - 3.4)], 0.3)), c["dark"], 0.35)
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M - 4.4, G - 5.0), (M - 2.6, G - 5.6)], 0.25)) * body, c["metal"], 0.6)
    tile.alpha *= tile.y < G


def pencil_cup(tile: Tile, c: dict) -> None:
    """A cup of pencils, sharpened."""
    _shadow(tile, 5.0)
    for x, top, lean in ((-2.0, 16.0, -2.0), (0.0, 18.5, 0.6), (2.0, 15.0, 2.4)):
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M + x, G - 6.0), (M + x + lean * 0.85, G - top + 2.0)], 1.2)), c["glow"])
        tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M + x + lean * 0.85 - 0.6, G - top + 2.0), (M + x + lean * 0.85 + 0.6, G - top + 2.0), (M + x + lean, G - top)])), c["wood"])
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + x + lean, G - top + 0.3, 0.3)), c["dark"])
    cup = tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 3.6, G - 7.6, M + 3.6, G))
    tile.put(cup, c["metal"])
    tile.put(cup * (tile.x < M - 2.2), (255, 255, 255), 0.25)
    tile.put(cup * (tile.x > M + 2.4), c["dark"], 0.35)
    tile.alpha *= tile.y < G


def ink_bottle(tile: Tile, c: dict) -> None:
    """A squat bottle of ink with a quill in it; the ink in it glows."""
    _shadow(tile, 5.5)
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M + 0.4, G - 7.0), (M + 1.2, G - 7.0), (M + 6.4, G - 21.0), (M + 4.4, G - 16.0)])), c["stone_light"], 0.85)
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M + 0.8, G - 7.0), (M + 6.0, G - 20.4)], 0.3)), c["dark"], 0.5)
    body = tile.mask(lambda p, dx, dy: (_dot(p, dx, dy, M, G - 3.6, 4.6, ry=3.6), _box(p, dx, dy, M - 1.8, G - 8.6, M + 1.8, G - 5.0)))
    tile.put(body, _mix(c["stone"], c["dark"], 0.3))
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, G - 3.0, 3.6, ry=2.6)), c["bloom"], 0.8)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M - 1.6, G - 4.6, 0.8, ry=1.4)), (255, 255, 255), 0.5)
    tile.alpha *= tile.y < G


# The four quarters of the Art dimension. In the Story Stacks `wood` is
# leather and `stone_light` paper; in the Resonant Reach `metal` is brass;
# on the stage `bloom` is the red of a rose; in the Workshop Deeps `wood` is
# clay.


def book_pile(tile: Tile, c: dict) -> None:
    """Three books that lie in a pile, each a little turned, the pages of
    each a pale line on its side."""
    _shadow(tile, 7.5)
    y = G
    for k, (w, h, shift, colour) in enumerate(((7.0, 3.2, -0.6, c["wood"]), (6.0, 2.8, 0.8, c["bloom"]), (5.2, 2.6, -0.2, c["plant"]))):
        x0, x1 = M - w + shift, M + w + shift
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0, y - h, x1, y)), _mix(colour, c["dark"], 0.25))
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 0.6, y - h + 0.5, x1, y - 0.5)), c["stone_light"], 0.85)
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0, y - h, x0 + 1.4, y)), _mix(colour, c["dark"], 0.1))
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 0.4, y - h + 0.6, x0 + 0.8, y - 0.6)), c["glow"], 0.7)
        y -= h
    tile.alpha *= tile.y < G


def candle_stub(tile: Tile, c: dict) -> None:
    """A stub of a candle in a dish, with wax down its side; its flame is lit."""
    _shadow(tile, 5.0)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, G - 1.0, 5.0, ry=1.0)), c["metal"])
    tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, M - 1.8, G - 8.0, M + 1.8, G - 1.0), _dot(p, dx, dy, M + 1.8, G - 3.0, 0.7, ry=1.6))), c["stone_light"])
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M + 0.6, G - 8.0, M + 1.8, G - 1.0)), c["dark"], 0.25)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, G - 10.6, 4.0), blur=1.4), c["glow"], 0.40)
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 0.9, G - 8.6), (M, G - 12.6), (M + 0.9, G - 8.6), (M, G - 8.0)])), c["glow"])
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, G - 9.0, 0.45)), (255, 255, 240))
    tile.alpha *= tile.y < G


def loose_pages(tile: Tile, c: dict) -> None:
    """Pages that fell out of a book: two lie flat, one curls up, each with
    lines of writing on it."""
    _shadow(tile, 8.0)
    flat = [[(M - 8.0, G), (M - 6.0, G - 1.6), (M + 1.0, G - 1.4), (M + 0.0, G)], [(M - 1.0, G), (M + 1.6, G - 1.8), (M + 8.0, G - 1.2), (M + 7.0, G)]]
    tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, pts) for pts in flat]), c["stone_light"])
    curl = [(M - 3.0, G - 1.2), (M - 1.0, G - 8.0), (M + 1.4, G - 10.6), (M + 3.6, G - 9.2), (M + 2.0, G - 6.0), (M + 1.6, G - 1.4)]
    page = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, curl))
    tile.put(page, _mix(c["stone_light"], c["stone"], 0.25))
    lines = tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(M - 1.8 + k * 0.6, G - 3.0 - k * 1.6), (M + 1.4 + k * 0.4, G - 3.4 - k * 1.6)], 0.25) for k in range(4)])
    tile.put(lines * page, c["dark"], 0.55)
    tile.alpha *= tile.y < G


def tuning_fork(tile: Tile, c: dict) -> None:
    """A tuning fork that stands on its foot, two rings of sound round it."""
    _shadow(tile, 3.5)
    tile.put(tile.mask(lambda p, dx, dy: [p.ellipse([(M - r) * K + dx, (G - 15.0 - r) * K + dy, (M + r) * K + dx, (G - 15.0 + r) * K + dy], outline=255, width=max(1, int(0.4 * K))) for r in (5.0, 7.6)], blur=0.3), c["glow"], 0.30)
    fork = tile.mask(lambda p, dx, dy: (_dot(p, dx, dy, M, G - 1.0, 2.2, ry=1.0), _box(p, dx, dy, M - 0.5, G - 8.0, M + 0.5, G - 1.0), _box(p, dx, dy, M - 2.6, G - 19.0, M - 1.6, G - 9.4), _box(p, dx, dy, M + 1.6, G - 19.0, M + 2.6, G - 9.4), p.arc([(M - 2.6) * K + dx, (G - 11.6) * K + dy, (M + 2.6) * K + dx, (G - 7.6) * K + dy], 0, 180, fill=255, width=int(1.0 * K))))
    tile.put(fork, c["metal"])
    tile.put(fork * (tile.x < M - 1.9), (255, 244, 210), 0.45)
    tile.alpha *= tile.y < G


def sheet_music(tile: Tile, c: dict) -> None:
    """Sheets of music that lie on the ground, one on its edge: staves of
    five lines, with notes."""
    _shadow(tile, 8.0)
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 8.0, G), (M - 6.6, G - 2.0), (M + 7.0, G - 2.0), (M + 8.0, G)])), c["stone_light"])
    stand = [(M - 4.6, G - 0.8), (M - 5.4, G - 12.0), (M + 3.4, G - 13.0), (M + 4.4, G - 1.2)]
    page = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, stand))
    tile.put(page, _mix(c["stone_light"], c["stone"], 0.2))
    lines = tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(M - 4.6 - (9.0 - y) * 0.07, G - y), (M + 3.6 + (9.0 - y) * 0.09, G - y - 0.6)], 0.18) for y in (3.0, 3.8, 4.6, 5.4, 6.2, 8.4, 9.2, 10.0, 10.8)])
    tile.put(lines * page, c["dark"], 0.6)
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M + x, G - y, 0.55, ry=0.4) for x, y in ((-2.6, 4.2), (-0.4, 5.4), (1.6, 3.8), (-1.6, 9.6), (1.0, 10.4))]) * page, c["dark"], 0.85)
    tile.alpha *= tile.y < G


def hand_bells(tile: Tile, c: dict) -> None:
    """Two hand bells of brass, one stands and one lies on its side."""
    _shadow(tile, 7.0)
    bell = [(M - 7.0, G), (M - 6.2, G - 2.0), (M - 5.2, G - 7.0), (M - 4.0, G - 8.4), (M - 2.0, G - 8.4), (M - 0.8, G - 7.0), (M + 0.2, G - 2.0), (M + 1.0, G)]
    tile.put(tile.mask(lambda p, dx, dy: (_poly(p, dx, dy, bell), _box(p, dx, dy, M - 3.6, G - 12.6, M - 2.4, G - 8.4), _dot(p, dx, dy, M - 3.0, G - 13.0, 1.4))), c["metal"])
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, bell[:4] + [(M - 4.4, G - 1.0)])), (255, 244, 210), 0.35)
    lying = tile.mask(lambda p, dx, dy: (_poly(p, dx, dy, [(M + 2.0, G - 1.6), (M + 7.0, G - 3.2), (M + 7.8, G), (M + 2.8, G)]), _dot(p, dx, dy, M + 7.6, G - 1.6, 1.0, ry=1.6)))
    tile.put(lying, _mix(c["metal"], c["dark"], 0.2))
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + 7.6, G - 1.6, 0.6, ry=1.1)), c["dark"], 0.7)
    tile.alpha *= tile.y < G


def metronome(tile: Tile, c: dict) -> None:
    """A metronome: a case like a small pyramid, and its arm that swings."""
    _shadow(tile, 5.0)
    case = [(M - 4.6, G), (M + 4.6, G), (M + 1.8, G - 15.0), (M - 1.8, G - 15.0)]
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, case)), c["wood"])
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 4.6, G), (M - 2.4, G), (M - 0.6, G - 15.0), (M - 1.8, G - 15.0)])), c["wood_light"], 0.45)
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 2.0, G - 3.0), (M + 2.0, G - 3.0), (M + 1.0, G - 12.6), (M - 1.0, G - 12.6)])), c["dark"], 0.6)
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M, G - 4.0), (M + 3.2, G - 17.6)], 0.45)), c["metal"])
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M + 1.6, G - 13.0, M + 3.2, G - 11.6)), c["metal"])
    tile.alpha *= tile.y < G


def footlight(tile: Tile, c: dict) -> None:
    """A footlight: a low hood of metal open to the stage, a warm lamp in it."""
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 2.4, G - 1.6), (M + 2.4, G - 1.6), (M + 6.0, G - 14.0), (M - 6.0, G - 14.0)]), blur=1.2) * np.clip((tile.y - (G - 14.0)) / 12.0, 0, 1), c["glow"], 0.22)
    hood = tile.mask(lambda p, dx, dy: (_box(p, dx, dy, M - 5.0, G - 1.4, M + 5.0, G), _poly(p, dx, dy, [(M - 4.0, G - 1.4), (M + 4.0, G - 1.4), (M + 4.0, G - 4.0), (M - 2.0, G - 6.0), (M - 4.0, G - 4.6)])))
    tile.put(hood, c["metal"])
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + 1.4, G - 3.4, 1.8, ry=1.2)), _mix(c["glow"], (255, 255, 255), 0.4))
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 5.0, G - 1.4, M + 5.0, G - 0.9)), c["stone_light"], 0.6)


def roses(tile: Tile, c: dict) -> None:
    """Roses thrown on the stage: three heads on their stems, a petal by them."""
    for x, y, angle in ((-5.0, 1.6, 0.3), (0.5, 2.2, -0.2), (4.6, 1.4, 0.1)):
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M + x, G - y), (M + x + 4.0 * math.cos(angle), G - y + 0.6 + 4.0 * math.sin(angle))], 0.4)), c["plant"])
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + x, G - y - 0.4, 1.8, ry=1.6)), c["bloom"])
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + x - 0.4, G - y - 0.8, 0.8, ry=0.6)), _mix(c["bloom"], (255, 220, 220), 0.35))
        tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M + x + 1.0, G - y + 0.4), (M + x + 2.6, G - y - 0.6), (M + x + 2.0, G - y + 0.8)])), c["plant"])
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + 8.0, G - 0.4, 0.9, ry=0.4)), c["bloom"])
    tile.alpha *= tile.y < G


def prop_crown(tile: Tile, c: dict) -> None:
    """A crown of the props: gold paint on board, its jewels of glass."""
    _shadow(tile, 6.0)
    pts = [(M - 6.0, G - 0.4), (M - 6.6, G - 8.0), (M - 3.4, G - 4.6), (M, G - 10.0), (M + 3.4, G - 4.6), (M + 6.6, G - 8.0), (M + 6.0, G - 0.4)]
    body = tile.mask(lambda p, dx, dy: (_poly(p, dx, dy, pts), _dot(p, dx, dy, M, G - 1.0, 6.0, ry=1.2)))
    tile.put(body, c["metal"])
    tile.put(body * (tile.x < M - 2.0), (255, 244, 200), 0.30)
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, 0.7) for x, y in ((M - 6.6, G - 8.4), (M, G - 10.4), (M + 6.6, G - 8.4))]), c["metal"])
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M + x, G - 2.6, 0.9) for x in (-3.4, 0.0, 3.4)]), c["bloom"])
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, G - 2.6, 0.9)), c["plant"])
    tile.alpha *= tile.y < G


def stage_masks(tile: Tile, c: dict) -> None:
    """The two masks of the theatre that lean on each other: the one that
    smiles is pale, the one that weeps is dark."""
    _shadow(tile, 7.0)
    for x, tilt, colour, mouth in ((-3.2, -0.25, c["stone_light"], 1.0), (3.4, 0.25, c["stone"], -1.0)):
        cx, cy = M + x, G - 7.4
        face = tile.mask(lambda p, dx, dy: (_dot(p, dx, dy, cx, cy, 4.0, ry=5.2), _box(p, dx, dy, cx - 2.4, cy + 2.0, cx + 2.4, G)))
        tile.put(face, colour)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, cx + ex, cy - 1.4 - ex * tilt * 0.4, 0.9, ry=0.6) for ex in (-1.6, 1.6)]), c["dark"], 0.85)
        tile.put(tile.mask(lambda p, dx, dy: p.arc([(cx - 1.8) * K + dx, (cy + 0.6 - (1.6 if mouth < 0 else 0.0)) * K + dy, (cx + 1.8) * K + dx, (cy + 3.0 + (0.0 if mouth > 0 else -0.6)) * K + dy], 20 if mouth > 0 else 200, 160 if mouth > 0 else 340, fill=255, width=int(0.5 * K))), c["dark"], 0.8)
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M - 7.0, G - 9.0), (M - 9.0, G - 4.0), (M - 8.0, G - 1.0)], 0.4)), c["bloom"], 0.8)
    tile.alpha *= tile.y < G


def clay_pots(tile: Tile, c: dict) -> None:
    """Pots fresh from the wheel: a tall one with lines thrown in it, and a
    bowl."""
    _shadow(tile, 7.5)
    tall = tile.mask(lambda p, dx, dy: (_dot(p, dx, dy, M - 2.6, G - 4.6, 4.0, ry=4.6), _box(p, dx, dy, M - 4.0, G - 12.0, M - 1.2, G - 7.0), _box(p, dx, dy, M - 4.8, G - 12.6, M - 0.4, G - 11.6)))
    tile.put(tall, c["wood"])
    tile.put(tall * (tile.x < M - 4.6), c["wood_light"], 0.5)
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, M - 6.4, G - y, M + 1.2, G - y + 0.3) for y in (3.0, 5.0, 7.0)]) * tall, c["dark"], 0.30)
    bowl = tile.mask(lambda p, dx, dy: p.pieslice([(M + 1.4) * K + dx, (G - 9.6) * K + dy, (M + 9.0) * K + dx, (G - 0.2) * K + dy], 0, 180, fill=255))
    tile.put(bowl, _mix(c["wood"], c["bloom"], 0.25))
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + 5.2, G - 4.9, 3.8, ry=0.7)), c["dark"], 0.5)
    tile.alpha *= tile.y < G


def thread_spools(tile: Tile, c: dict) -> None:
    """Spools of thread for a loom, two that stand and one on its side."""
    _shadow(tile, 7.5)
    for x, h, colour in ((-4.4, 9.0, c["bloom"]), (0.6, 7.0, c["plant"])):
        spool = tile.mask(lambda p, dx, dy: (_box(p, dx, dy, M + x - 2.6, G - h, M + x + 2.6, G - h + 1.0), _box(p, dx, dy, M + x - 2.6, G - 1.0, M + x + 2.6, G), _box(p, dx, dy, M + x - 2.0, G - h, M + x + 2.0, G)))
        tile.put(spool, c["wood"])
        thread = tile.mask(lambda p, dx, dy: _box(p, dx, dy, M + x - 2.0, G - h + 1.0, M + x + 2.0, G - 1.0))
        tile.put(thread, colour)
        tile.put(thread * ((tile.y * 3.0) % 1.0 < 0.4), c["dark"], 0.20)
        tile.put(thread * (tile.x < M + x - 1.0), (255, 255, 255), 0.18)
    tile.put(tile.mask(lambda p, dx, dy: (_dot(p, dx, dy, M + 6.6, G - 2.4, 2.4), _box(p, dx, dy, M + 4.0, G - 4.4, M + 9.2, G))), c["glow"])
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M + 4.2, G - 0.6), (M + 1.0, G - 0.3), (M - 2.0, G - 0.2)], 0.3)), c["glow"])
    tile.alpha *= tile.y < G


def gear_wheel(tile: Tile, c: dict) -> None:
    """A gear of brass that stands on its edge against a small one."""
    _shadow(tile, 8.0)

    def gear(p, dx, dy, cx, cy, r, teeth):
        pts = []
        for k in range(teeth):
            a0 = math.tau * k / teeth
            for frac, rad in ((0.0, r), (0.18, r + 1.2), (0.48, r + 1.2), (0.66, r)):
                a = a0 + math.tau / teeth * frac
                pts.append((cx + math.cos(a) * rad, cy + math.sin(a) * rad))
        _poly(p, dx, dy, pts)

    tile.put(tile.mask(lambda p, dx, dy: gear(p, dx, dy, M + 5.4, G - 3.2, 2.0, 8)), _mix(c["metal"], c["dark"], 0.25))
    tile.put(tile.mask(lambda p, dx, dy: gear(p, dx, dy, M - 1.6, G - 7.4, 6.0, 12)), c["metal"])
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M - 1.6, G - 7.4, 4.2)), _mix(c["metal"], c["dark"], 0.35))
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(M - 1.6, G - 7.4), (M - 1.6 + math.cos(a) * 4.4, G - 7.4 + math.sin(a) * 4.4)], 0.9) for a in (0.3, 2.4, 4.5)]), c["metal"])
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M - 1.6, G - 7.4, 1.2)), c["dark"], 0.8)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M - 3.0, G - 9.4, 2.4, ry=1.6)), (255, 240, 200), 0.18)
    tile.alpha *= tile.y < G


def blueprint_rolls(tile: Tile, c: dict) -> None:
    """Rolls of plans: one lies open a little, its blue lines show."""
    _shadow(tile, 8.0)
    sheet = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 6.0, G), (M - 5.0, G - 2.6), (M + 7.6, G - 2.6), (M + 8.0, G)]))
    tile.put(sheet, (60, 104, 150))
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(M - 3.0 + k * 2.6, G - 0.4), (M - 2.4 + k * 2.6, G - 2.2)], 0.2) for k in range(4)]) * sheet, (200, 230, 250), 0.6)
    for x, y, r in ((-6.0, 1.6, 1.6), (-3.0, 4.6, 1.5), (-5.0, 7.4, 1.4)):
        roll = tile.mask(lambda p, dx, dy: (_box(p, dx, dy, M + x - 3.0, G - y - r, M + x + 5.0, G - y + r), _dot(p, dx, dy, M + x + 5.0, G - y, r * 0.55, ry=r)))
        tile.put(roll, _mix((226, 230, 236), c["dark"], 0.15))
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + x + 5.0, G - y, r * 0.35, ry=r * 0.6)), (60, 104, 150), 0.8)
        tile.put(roll * (tile.y > G - y + r * 0.3), c["dark"], 0.20)
    tile.alpha *= tile.y < G


# The History dimension, one era to each group. In the Crescent `glow` is
# the gold of wheat and `wood` is clay; on the Nile `metal` is gold and
# `bloom` the blue of a lotus; on the Classical Shore `wood` is terracotta
# and `metal` the black of a painted pot; on the Silk Road `bloom` is
# crimson silk; on the steppe `glow` is the blue of a scarf; on the Monsoon
# Coast `stone_light` is salt and `metal` gold; in the Age of Sail `bloom`
# is a tomato; in the Industrial Age `metal` is iron.


def wheat_sheaf(tile: Tile, c: dict) -> None:
    """A sheaf of wheat that stands: the stalks spread at the foot, a band of
    straw round the waist, and the ears fan out at the top."""
    _shadow(tile, 5.5)
    stalks = []
    for k in range(9):
        t = (k - 4) / 4.0
        stalks.append([(M + t * 4.2, G), (M + t * 0.9, G - 8.0), (M + t * 5.0, G - 16.5 + abs(t) * 2.6)])
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, pts, 0.6) for pts in stalks]), _mix(c["glow"], c["dark"], 0.30))
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, pts[2][0], pts[2][1] - 0.6, 0.9, ry=2.0) for pts in stalks]), c["glow"])
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(pts[2][0], pts[2][1] - 2.4), (pts[2][0] + (pts[2][0] - M) * 0.12, pts[2][1] - 4.4)], 0.2) for pts in stalks]), c["glow"], 0.8)
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 1.8, G - 9.2, M + 1.8, G - 7.4)), _mix(c["wood"], c["dark"], 0.25))
    tile.alpha *= tile.y < G


def clay_tablets(tile: Tile, c: dict) -> None:
    """Tablets of clay: three in a pile and one that leans on them, the
    wedges of its writing pressed in rows."""
    _shadow(tile, 7.5)
    y = G
    for w, h, shift in ((6.6, 2.2, -1.6), (6.0, 2.0, -1.0), (5.4, 1.9, -1.9)):
        body = tile.mask(lambda p, dx, dy: p.rounded_rectangle(((M + shift - w) * K + dx, (y - h) * K + dy, (M + shift + w) * K + dx, y * K + dy), radius=0.8 * K, fill=255))
        tile.put(body, c["wood"])
        tile.put(body * (tile.y < y - h + 0.6), c["wood_light"], 0.6)
        y -= h
    lean = [(M + 3.0, G), (M + 7.4, G), (M + 9.2, G - 10.0), (M + 4.8, G - 10.8)]
    body = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, lean))
    tile.put(body, _mix(c["wood"], c["wood_light"], 0.35))
    wedges = [(M + 4.6 + col * 1.1 + row * 0.35, G - 2.0 - row * 1.8) for row in range(5) for col in range(3)]
    tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, [(x - 0.35, y - 0.3), (x + 0.45, y - 0.3), (x, y + 0.45)]) for x, y in wedges]) * body, c["dark"], 0.65)
    tile.alpha *= tile.y < G


def grain_basket(tile: Tile, c: dict) -> None:
    """A basket of woven reed full of grain, and a sickle that leans on it."""
    _shadow(tile, 7.0)
    basket = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 6.0, G - 8.0), (M + 4.0, G - 8.0), (M + 3.0, G), (M - 5.0, G)]))
    tile.put(basket, _mix(c["glow"], c["dark"], 0.45))
    weave = ((np.abs(((tile.x + tile.y) % 1.6) - 0.8) < 0.2) | (np.abs(((tile.x - tile.y) % 1.6) - 0.8) < 0.2)).astype(np.float32)
    tile.put(basket * weave, c["dark"], 0.30)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M - 1.0, G - 8.0, 5.2, ry=1.8)), c["glow"])
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 6.4, G - 8.6, M + 4.4, G - 7.6)), _mix(c["glow"], c["dark"], 0.3))
    tile.put(tile.mask(lambda p, dx, dy: (_line(p, dx, dy, [(M + 5.0, G), (M + 6.6, G - 6.0)], 0.8), p.arc([(M + 3.0) * K + dx, (G - 13.6) * K + dy, (M + 10.6) * K + dx, (G - 6.0) * K + dy], 180, 330, fill=255, width=int(0.7 * K)))), c["metal"])
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M + 5.0, G), (M + 6.6, G - 6.0)], 0.9)), c["wood"])
    tile.alpha *= tile.y < G


def papyrus_clump(tile: Tile, c: dict) -> None:
    """A clump of papyrus: tall stems, each with a fan of threads."""
    for x, h, lean in ((-4.0, 13.0, -1.6), (-1.0, 18.0, -0.4), (2.0, 15.0, 0.8), (4.6, 10.0, 2.0)):
        head = (M + x + lean, G - h)
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M + x, G), head], 0.5)), _mix(c["plant"], c["dark"], 0.25))
        fan = [head] + [(head[0] + 3.0 * math.cos(math.radians(a)), head[1] + 3.0 * math.sin(math.radians(a)) + 1.2 * abs(math.cos(math.radians(a)))) for a in range(-170, -9, 16)]
        tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, fan)), c["plant"])
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [head, pt], 0.18) for pt in fan[1:]]), _mix(c["plant"], (230, 240, 180), 0.35), 0.7)
    tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, [(M + x - 1.2, G), (M + x + 1.2, G), (M + x, G - 3.0)]) for x in (-4.0, -1.0, 2.0, 4.6)]), _mix(c["plant"], c["dark"], 0.4))


def cat_statue(tile: Tile, c: dict) -> None:
    """A small statue of a cat that sits, of black stone, with a ring of
    gold in its ear and a collar of gold."""
    _shadow(tile, 5.0)
    body = tile.mask(lambda p, dx, dy: (
        _dot(p, dx, dy, M, G - 5.0, 4.0, ry=5.0),
        _box(p, dx, dy, M - 3.6, G - 2.0, M + 3.6, G),
        _box(p, dx, dy, M - 1.6, G - 12.6, M + 1.8, G - 8.0),
        _dot(p, dx, dy, M + 0.2, G - 13.6, 2.4, ry=2.1),
        _poly(p, dx, dy, [(M - 2.0, G - 14.6), (M - 1.4, G - 17.8), (M - 0.2, G - 15.4)]),
        _poly(p, dx, dy, [(M + 0.6, G - 15.4), (M + 1.8, G - 17.8), (M + 2.4, G - 14.6)]),
        _line(p, dx, dy, [(M + 3.4, G - 1.0), (M + 6.2, G - 1.6), (M + 7.2, G - 3.6)], 0.8),
    ))
    tile.put(body, _mix(c["dark"], c["stone"], 0.25))
    tile.put(body * (tile.x < M - 1.4), c["stone"], 0.25)
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 1.8, G - 11.0, M + 2.0, G - 10.2)), c["metal"])
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + 2.0, G - 15.4, 0.5)), c["metal"])
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M + x, G - 14.0, 0.45, ry=0.3) for x in (-0.8, 1.2)]), c["metal"], 0.9)
    tile.alpha *= tile.y < G


def canopic_jars(tile: Tile, c: dict) -> None:
    """Four jars of stone in a row, each lid the head of a god: a man, a
    baboon, a jackal and a falcon."""
    _shadow(tile, 9.0)
    for k, x in enumerate((-7.2, -2.4, 2.4, 7.2)):
        cx = M + x
        jar = tile.mask(lambda p, dx, dy: (_dot(p, dx, dy, cx, G - 4.0, 2.2, ry=4.0), _box(p, dx, dy, cx - 1.4, G - 1.2, cx + 1.4, G)))
        tile.put(jar, c["stone_light"])
        tile.put(jar * (tile.x > cx + 0.8), c["stone"], 0.6)
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, cx - 1.8, G - 5.4, cx + 1.8, G - 4.8)), c["bloom"], 0.8)
        if k == 0:
            head = lambda p, dx, dy: (_dot(p, dx, dy, cx, G - 9.6, 1.6, ry=1.8), _box(p, dx, dy, cx - 1.8, G - 10.0, cx + 1.8, G - 7.6))
        elif k == 1:
            head = lambda p, dx, dy: (_dot(p, dx, dy, cx, G - 9.6, 1.8, ry=1.6), _dot(p, dx, dy, cx + 1.2, G - 9.0, 1.0, ry=0.8))
        elif k == 2:
            head = lambda p, dx, dy: (_dot(p, dx, dy, cx, G - 9.2, 1.5), _poly(p, dx, dy, [(cx + 0.6, G - 9.6), (cx + 2.4, G - 9.0), (cx + 0.6, G - 8.4)]), _poly(p, dx, dy, [(cx - 1.0, G - 10.0), (cx - 0.6, G - 13.0), (cx + 0.2, G - 10.4)]), _poly(p, dx, dy, [(cx + 0.0, G - 10.4), (cx + 0.6, G - 13.0), (cx + 1.0, G - 10.0)]))
        else:
            head = lambda p, dx, dy: (_dot(p, dx, dy, cx, G - 9.4, 1.6, ry=1.7), _poly(p, dx, dy, [(cx + 1.2, G - 9.8), (cx + 2.4, G - 9.0), (cx + 1.0, G - 8.6)]))
        tile.put(tile.mask(head), c["metal"] if k % 2 else _mix(c["metal"], c["stone"], 0.4))
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, cx - 1.9, G - 8.2, cx + 1.9, G - 7.6)), c["dark"], 0.4)
    tile.alpha *= tile.y < G


def lotus(tile: Tile, c: dict) -> None:
    """Lotus by the water: round leaves that lie flat, and two flowers on
    their stems, their petals pointed."""
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M + x, G - 0.8, r, ry=r * 0.32) for x, r in ((-5.0, 3.4), (2.6, 4.0), (7.0, 2.4))]), _mix(c["plant"], c["dark"], 0.15))
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(M + x - r * 0.1, G - 0.8), (M + x + r * 0.5, G - 1.4)], 0.25) for x, r in ((-5.0, 3.4), (2.6, 4.0))]), c["dark"], 0.5)
    for x, h in ((-2.0, 11.0), (3.4, 7.0)):
        top = (M + x, G - h)
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M + x - 0.6, G - 1.0), top], 0.45)), _mix(c["plant"], c["dark"], 0.3))
        petals = [[(top[0], top[1] + 0.4), (top[0] + math.sin(math.radians(a)) * 3.4, top[1] - math.cos(math.radians(a)) * 3.0), (top[0] + math.sin(math.radians(a + 14)) * 1.4, top[1] - 0.6)] for a in (-70, -35, 0, 35, 70)]
        tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, pts) for pts in petals]), c["bloom"])
        tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, petals[2])), _mix(c["bloom"], (255, 255, 255), 0.4))
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, top[0], top[1] - 0.2, 0.7)), c["metal"])
    tile.alpha *= tile.y < G


def standing_amphora(tile: Tile, c: dict) -> None:
    """An amphora that stands in a ring of stone: a tall body that ends in a
    point, a neck, two handles, and a band of the key pattern in black."""
    _shadow(tile, 4.5)
    body = tile.mask(lambda p, dx, dy: (
        _dot(p, dx, dy, M, G - 10.0, 4.0, ry=5.6),
        _poly(p, dx, dy, [(M - 3.0, G - 7.0), (M + 3.0, G - 7.0), (M + 0.7, G - 1.4), (M - 0.7, G - 1.4)]),
        _box(p, dx, dy, M - 1.3, G - 19.0, M + 1.3, G - 14.0),
        _box(p, dx, dy, M - 1.9, G - 19.6, M + 1.9, G - 18.8),
    ))
    tile.put(body, c["wood"])
    tile.put(body * (tile.x < M - 1.6), c["wood_light"], 0.45)
    tile.put(body * (tile.x > M + 2.2), c["dark"], 0.35)
    tile.put(tile.mask(lambda p, dx, dy: [p.arc([(M + side * 2.2 - 1.4) * K + dx, (G - 18.0) * K + dy, (M + side * 2.2 + 1.4) * K + dx, (G - 13.2) * K + dy], 90 if side < 0 else 270, 270 if side < 0 else 90, fill=255, width=int(0.55 * K)) for side in (-1, 1)]), c["wood"])
    band = tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 4.0, G - 12.4, M + 4.0, G - 10.6)) * body
    tile.put(band, c["metal"])
    tile.put(band * ((tile.x * 2.0) % 1.6 < 0.5) * (tile.y > G - 11.9) * (tile.y < G - 11.1), c["wood_light"], 0.7)
    tile.put(tile.mask(lambda p, dx, dy: (_dot(p, dx, dy, M, G - 1.0, 3.6, ry=1.0), _box(p, dx, dy, M - 3.6, G - 1.0, M + 3.6, G))), c["stone"])
    tile.alpha *= tile.y < G


def bust(tile: Tile, c: dict) -> None:
    """A bust of marble on a plinth: a head with curls and a beard, the
    shoulders in a fold of cloth, and a moustache that a vandal painted on."""
    _shadow(tile, 4.5)
    stone = tile.mask(lambda p, dx, dy: (
        _box(p, dx, dy, M - 3.6, G - 2.0, M + 3.6, G),
        _box(p, dx, dy, M - 2.6, G - 8.0, M + 2.6, G - 2.0),
        _box(p, dx, dy, M - 3.4, G - 9.0, M + 3.4, G - 8.0),
        _dot(p, dx, dy, M, G - 11.0, 4.6, ry=2.2),
        _box(p, dx, dy, M - 1.0, G - 14.0, M + 1.0, G - 11.0),
        _dot(p, dx, dy, M, G - 16.6, 2.6, ry=3.0),
    ))
    tile.put(stone, c["stone_light"])
    tile.put(stone * (tile.x > M + 1.2), c["stone"], 0.55)
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M + x, G - 19.0 + abs(x) * 0.3, 0.8) for x in (-1.8, -0.6, 0.6, 1.8)]), c["stone"], 0.5)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, G - 14.8, 1.8, ry=1.4)), c["stone"], 0.35)
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M - 3.4, G - 11.6), (M - 0.4, G - 9.4), (M + 2.6, G - 12.0)], 0.4)), c["stone"], 0.6)
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M - 2.0, G - 15.0), (M - 0.8, G - 15.6), (M, G - 15.2), (M + 0.8, G - 15.6), (M + 2.0, G - 15.0)], 0.5)), c["metal"])
    tile.alpha *= tile.y < G


def fallen_drum(tile: Tile, c: dict) -> None:
    """A drum of a column that fell and lies on its side, its flutes along
    it and its round face to the view."""
    _shadow(tile, 8.0)
    body = tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 8.0, G - 8.4, M + 3.0, G))
    tile.put(body, c["stone"])
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, M - 8.0, G - y - 0.3, M + 3.0, G - y + 0.3) for y in (1.6, 3.4, 5.2, 7.0)]), c["dark"], 0.30)
    tile.put(body * (tile.y < G - 7.2), c["stone_light"], 0.5)
    face = tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + 3.0, G - 4.2, 2.4, ry=4.2))
    tile.put(face, c["stone_light"])
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + 3.4, G - 4.2, 0.8, ry=1.4)), c["stone"], 0.6)
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M + 6.0, G), (M + 9.0, G), (M + 8.2, G - 2.2), (M + 6.6, G - 1.8)])), c["stone"])
    tile.alpha *= tile.y < G


def spice_sacks(tile: Tile, c: dict) -> None:
    """Three sacks of spice with their mouths rolled down: saffron, red
    pepper and cinnamon in heaps."""
    _shadow(tile, 9.0)
    for x, w, h, spice in ((-5.4, 3.6, 9.0, (236, 160, 40)), (5.2, 3.4, 8.0, (170, 70, 40)), (0.0, 3.8, 11.0, c["bloom"])):
        sack = tile.mask(lambda p, dx, dy: (_dot(p, dx, dy, M + x, G - h * 0.42, w, ry=h * 0.45), _box(p, dx, dy, M + x - w, G - h * 0.45, M + x + w, G - 0.5), _box(p, dx, dy, M + x - w * 0.9, G - h, M + x + w * 0.9, G - h * 0.5)))
        tile.put(sack, c["stone"])
        tile.put(sack * (tile.x > M + x + w * 0.4), c["dark"], 0.30)
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M + x - w * 1.0, G - h - 0.2, M + x + w * 1.0, G - h + 1.2)), c["stone_light"])
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + x, G - h - 0.2, w * 0.85, ry=1.6)), spice)
    tile.alpha *= tile.y < G


def silk_rolls(tile: Tile, c: dict) -> None:
    """Bolts of silk that lie in a pile, their round ends to the view, each
    of its own colour, and the end of one hangs loose."""
    _shadow(tile, 8.0)
    colours = (c["bloom"], c["plant"], (52, 60, 130), (236, 170, 50), c["bloom"], c["plant"])
    rolls = [(-5.2, 2.6), (0.0, 2.6), (5.2, 2.6), (-2.6, 7.2), (2.6, 7.2), (0.0, 11.8)]
    for (x, y), colour in zip(rolls, colours):
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + x, G - y, 2.5)), colour)
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + x - 0.6, G - y - 0.6, 1.2)), (255, 255, 255), 0.25)
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + x, G - y, 0.6)), c["wood"])
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M + 7.2, G - 3.0), (M + 9.6, G - 1.6), (M + 10.0, G), (M + 7.6, G)])), c["bloom"], 0.85)
    tile.alpha *= tile.y < G


def paper_lantern(tile: Tile, c: dict) -> None:
    """A red paper lantern that hangs from the arm of a short post, a tassel
    under it; it gives light."""
    _shadow(tile, 3.6)
    tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, M - 4.4, G - 20.0, M - 3.4, G), _box(p, dx, dy, M - 5.4, G - 1.0, M - 2.4, G), _box(p, dx, dy, M - 4.4, G - 20.0, M + 2.4, G - 19.0))), c["wood"])
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M + 1.4, G - 19.0), (M + 1.4, G - 17.0)], 0.3)), c["dark"])
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + 1.4, G - 13.2, 6.0), blur=1.6), c["glow"], 0.35)
    body = tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + 1.4, G - 13.2, 3.0, ry=3.8))
    tile.put(body, c["bloom"])
    tile.put(body * (np.abs(((tile.y - (G - 13.2)) % 1.6) - 0.8) < 0.15), _mix(c["bloom"], c["dark"], 0.4), 0.7)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + 1.0, G - 13.6, 1.6, ry=2.2), blur=0.5), c["glow"], 0.75)
    tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, M - 0.2, G - 17.4, M + 3.0, G - 16.6), _box(p, dx, dy, M - 0.2, G - 9.8, M + 3.0, G - 9.0))), c["metal"])
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M + 1.4, G - 9.0), (M + 1.4, G - 6.0)], 0.4)), c["metal"])


def tea_bricks(tile: Tile, c: dict) -> None:
    """Bricks of pressed tea in a stack, each with a seal pressed in its
    face, and one in its paper wrap."""
    _shadow(tile, 8.0)
    for row, (x0, count) in enumerate(((-7.6, 3), (-5.0, 2), (-2.4, 1))):
        for k in range(count):
            x = M + x0 + k * 5.2
            y = G - row * 3.4
            tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x + 0.2, y - 3.2, x + 5.0, y)), _mix(c["wood"], c["dark"], 0.25 + 0.1 * ((row + k) % 2)))
            tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x + 0.2, y - 3.2, x + 5.0, y - 2.6)), c["wood_light"], 0.5)
            tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, x + 2.6, y - 1.5, 0.9)), c["dark"], 0.45)
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M + 3.4, G - 3.2, M + 8.6, G)), c["stone_light"])
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M + 5.6, G - 3.2, M + 6.4, G)), c["bloom"])
    tile.alpha *= tile.y < G


def ovoo_cairn(tile: Tile, c: dict) -> None:
    """A small ovoo: a cairn of stones, a stick in it, and blue scarves tied
    on the stick."""
    _shadow(tile, 7.0)
    stones = [(-4.0, 1.6, 2.4), (0.4, 1.8, 2.8), (4.4, 1.5, 2.2), (-2.0, 4.6, 2.2), (2.2, 4.6, 2.2), (0.0, 7.2, 1.8)]
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M + x, G - y, r, ry=r * 0.75) for x, y, r in stones]), c["stone"])
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M + x - 0.5, G - y - 0.5, r * 0.5, ry=r * 0.35) for x, y, r in stones]), c["stone_light"], 0.6)
    tile.put(tile.mask(lambda p, dx, dy: (_line(p, dx, dy, [(M, G - 7.0), (M - 0.6, G - 20.0)], 0.6), _line(p, dx, dy, [(M - 0.3, G - 14.0), (M + 2.6, G - 18.4)], 0.4))), c["wood"])
    scarves = [[(M - 0.4, G - 18.6), (M + 3.6, G - 17.4), (M + 4.8, G - 15.0), (M + 0.2, G - 16.8)], [(M - 0.2, G - 15.6), (M - 4.4, G - 14.6), (M - 5.6, G - 12.2), (M - 0.4, G - 13.8)], [(M + 1.6, G - 17.0), (M + 2.2, G - 12.6), (M + 3.4, G - 12.8), (M + 2.6, G - 17.2)]]
    tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, pts) for pts in scarves]), c["glow"])
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, scarves[0])), (255, 255, 255), 0.25)
    tile.alpha *= tile.y < G


def saddle(tile: Tile, c: dict) -> None:
    """A saddle of the steppe on its stand: a high front and back, red
    leather with studs of silver, and the stirrups that hang."""
    _shadow(tile, 7.0)
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(M + x, G), (M + x * 0.6, G - 7.0)], 0.8) for x in (-5.4, 5.4)]), c["wood"])
    seat = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 7.0, G - 7.0), (M + 7.0, G - 7.0), (M + 6.6, G - 13.4), (M + 4.6, G - 13.0), (M + 3.6, G - 9.6), (M - 3.0, G - 9.6), (M - 4.4, G - 14.4), (M - 6.6, G - 14.6)]))
    tile.put(seat, c["bloom"])
    tile.put(seat * (tile.y < G - 9.0) * (np.abs(tile.x - M) > 3.6), _mix(c["bloom"], c["dark"], 0.3))
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M + x, G - 8.2, 0.55) for x in (-5.4, -2.7, 0.0, 2.7, 5.4)]), c["metal"])
    tile.put(tile.mask(lambda p, dx, dy: [(_line(p, dx, dy, [(M + x, G - 8.0), (M + x, G - 3.0)], 0.3), p.arc([(M + x - 1.2) * K + dx, (G - 3.4) * K + dy, (M + x + 1.2) * K + dx, (G - 1.0) * K + dy], 0, 360, fill=255, width=int(0.4 * K))) for x in (-2.2, 2.2)]), c["metal"], 0.9)
    tile.alpha *= tile.y < G


def milk_pail(tile: Tile, c: dict) -> None:
    """A pail of wood for mare's milk, with hoops, and a ladle in it."""
    _shadow(tile, 5.5)
    body = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 4.6, G - 10.0), (M + 4.6, G - 10.0), (M + 3.8, G), (M - 3.8, G)]))
    tile.put(body, c["wood"])
    tile.put(body * (tile.x < M - 2.0), c["wood_light"], 0.45)
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, M - 4.7, G - y, M + 4.7, G - y + 0.8) for y in (9.0, 3.0)]), c["metal"])
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, G - 10.0, 4.6, ry=1.0)), c["stone_light"])
    tile.put(tile.mask(lambda p, dx, dy: (_line(p, dx, dy, [(M + 1.0, G - 10.0), (M + 5.6, G - 17.0)], 0.5), _dot(p, dx, dy, M + 5.8, G - 17.4, 1.0))), c["wood"])
    tile.alpha *= tile.y < G


def horse_skull(tile: Tile, c: dict) -> None:
    """The skull of a horse that lies in the grass, long in the face."""
    bone = _mix(c["stone_light"], (236, 228, 206), 0.4)
    body = tile.mask(lambda p, dx, dy: (_dot(p, dx, dy, M - 3.6, G - 3.2, 3.6, ry=3.0), _poly(p, dx, dy, [(M - 2.4, G - 5.6), (M + 7.6, G - 2.6), (M + 7.6, G - 0.6), (M - 2.4, G - 0.6)])))
    tile.put(body, bone)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M - 3.0, G - 3.8, 1.2, ry=1.0)), c["dark"], 0.8)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + 6.4, G - 2.0, 0.7, ry=0.5)), c["dark"], 0.7)
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, M + x, G - 1.0, M + x + 0.5, G - 0.4) for x in (1.0, 2.2, 3.4, 4.6)]), c["dark"], 0.5)
    tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, [(M + x - 0.6, G), (M + x + 0.6, G), (M + x + lean, G - h)]) for x, h, lean in ((-7.6, 4.0, -0.6), (-6.6, 6.0, 0.4), (8.6, 5.0, 0.6), (9.4, 3.6, 1.0))]), c["plant"])
    tile.alpha *= tile.y < G


def salt_slabs(tile: Tile, c: dict) -> None:
    """Slabs of salt from the mines of the desert, two tied in a pair with
    rope and one that leans, grey veins in the white."""
    _shadow(tile, 8.0)
    slabs = [[(M - 8.0, G), (M - 1.0, G), (M - 1.0, G - 3.4), (M - 8.0, G - 3.4)], [(M - 8.0, G - 3.4), (M - 1.0, G - 3.4), (M - 1.0, G - 6.8), (M - 8.0, G - 6.8)], [(M + 0.6, G), (M + 4.2, G), (M + 8.2, G - 12.0), (M + 4.6, G - 12.6)]]
    for pts in slabs:
        body = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, pts))
        tile.put(body, c["stone_light"])
        tile.put(body * (np.abs(np.sin(tile.x * 1.3 + tile.y * 0.6)) < 0.08), c["stone"], 0.7)
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x, G - 7.2, x + 0.7, G) for x in (M - 6.4, M - 3.0)]), c["wood"])
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 8.0, G - 3.6, M - 1.0, G - 3.2)), c["stone"], 0.7)
    tile.alpha *= tile.y < G


def gold_bowl(tile: Tile, c: dict) -> None:
    """A bowl of wood heaped with gold dust that gives a little light, and
    flecks of gold spilled by it."""
    _shadow(tile, 6.5)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, G - 7.0, 6.0), blur=1.6), c["glow"], 0.25)
    bowl = tile.mask(lambda p, dx, dy: p.pieslice([(M - 6.0) * K + dx, (G - 11.0) * K + dy, (M + 6.0) * K + dx, (G - 0.6) * K + dy], 0, 180, fill=255))
    tile.put(bowl, c["wood"])
    tile.put(bowl * (tile.x < M - 2.0), c["wood_light"], 0.35)
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 2.0, G - 1.0, M + 2.0, G)), c["wood"])
    heap = tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, G - 5.8, 5.4, ry=3.0)) * (tile.y < G - 5.6)
    tile.put(heap, c["metal"])
    tile.put(heap * np.clip(1.0 - np.abs(tile.x - M + 1.4) / 2.0, 0, 1), (255, 244, 190), 0.6)
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M + x, G - 0.4, 0.35) for x in (-8.4, -7.4, 7.2, 8.6, 9.2)]), c["metal"])
    tile.alpha *= tile.y < G


def manuscripts(tile: Tile, c: dict) -> None:
    """A pile of manuscripts: loose pages between covers of leather, tied
    with cord, and one open on the top."""
    _shadow(tile, 8.0)
    y = G
    for w, h, shift in ((8.0, 2.6, 0.0), (7.2, 2.4, -0.6), (7.6, 2.2, 0.6)):
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - w + shift, y - h, M + w + shift, y)), c["wood"])
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - w + shift + 0.6, y - h + 0.6, M + w + shift - 0.3, y - 0.6)), c["stone_light"], 0.85)
        y -= h
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 1.0, y - 0.2, M - 0.2, G)), c["bloom"], 0.8)
    pages = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 6.0, y), (M, y - 1.2), (M + 6.0, y), (M + 6.0, y - 1.4), (M, y - 2.6), (M - 6.0, y - 1.4)]))
    tile.put(pages, c["stone_light"])
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(M - 5.0 + k * 1.2, y - 1.0 - k * 0.2), (M - 4.4 + k * 1.2, y - 1.2 - k * 0.2)], 0.15) for k in range(4)]), c["dark"], 0.6)
    tile.alpha *= tile.y < G


def crop_crate(tile: Tile, c: dict) -> None:
    """A crate full of the crops of the new world: potatoes, tomatoes and a
    cob of maize on the top."""
    _shadow(tile, 7.0)
    body = tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 6.6, G - 8.0, M + 6.6, G))
    tile.put(body, c["wood"])
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, M - 6.6, G - y, M + 6.6, G - y + 0.5) for y in (5.4, 2.6)]), c["dark"], 0.5)
    tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, M - 6.6, G - 8.0, M - 5.4, G), _box(p, dx, dy, M + 5.4, G - 8.0, M + 6.6, G))), c["wood_light"], 0.6)
    potatoes = [(-4.6, 8.6), (-2.6, 9.4), (-0.8, 8.6)]
    tomatoes = [(1.4, 8.8), (3.2, 9.6), (4.8, 8.6), (2.4, 10.8)]
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M + x, G - y, 1.3, ry=1.0) for x, y in potatoes]), (150, 112, 70))
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M + x, G - y, 1.1) for x, y in tomatoes]), c["bloom"])
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M + x - 0.3, G - y - 0.4, 0.35) for x, y in tomatoes]), (255, 220, 200), 0.6)
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 3.6, G - 10.4), (M + 0.4, G - 12.0), (M + 0.8, G - 11.0), (M - 3.2, G - 9.4)])), (236, 196, 70))
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M + 0.4, G - 12.0), (M + 2.4, G - 13.4), (M + 1.4, G - 11.2)])), c["plant"])
    tile.alpha *= tile.y < G


def anchor(tile: Tile, c: dict) -> None:
    """An anchor that stands on its crown: a shank, a ring on the top, the
    stock across it, and two flukes."""
    _shadow(tile, 7.0)
    iron = tile.mask(lambda p, dx, dy: (
        _box(p, dx, dy, M - 0.7, G - 17.0, M + 0.7, G - 1.0),
        p.ellipse([(M - 1.6) * K + dx, (G - 20.4) * K + dy, (M + 1.6) * K + dx, (G - 17.2) * K + dy], outline=255, width=int(0.7 * K)),
        p.arc([(M - 5.4) * K + dx, (G - 11.4) * K + dy, (M + 5.4) * K + dx, (G - 0.6) * K + dy], 0, 180, fill=255, width=int(1.1 * K)),
        _poly(p, dx, dy, [(M - 6.4, G - 5.4), (M - 6.6, G - 9.4), (M - 4.0, G - 5.8)]),
        _poly(p, dx, dy, [(M + 6.4, G - 5.4), (M + 6.6, G - 9.4), (M + 4.0, G - 5.8)]),
    ))
    tile.put(iron, c["metal"])
    tile.put(iron * (tile.x < M - 0.2), c["stone_light"], 0.25)
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 5.0, G - 16.0, M + 5.0, G - 14.8)), c["wood"])
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 3.0, G - 1.2, M + 3.0, G)), c["metal"])
    tile.alpha *= tile.y < G


def cotton_spools(tile: Tile, c: dict) -> None:
    """Bobbins of a spinning mill: spindles of wood with cones of white
    cotton thread, two that stand and one that lies."""
    _shadow(tile, 7.5)
    for x in (-4.0, 1.6):
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M + x - 0.5, G - 15.0, M + x + 0.5, G)), c["wood"])
        cone = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M + x - 2.6, G - 1.4), (M + x + 2.6, G - 1.4), (M + x + 1.6, G - 12.0), (M + x - 1.6, G - 12.0)]))
        tile.put(cone, c["stone_light"])
        tile.put(cone * (np.abs(((tile.y * 2.0) % 1.0) - 0.5) < 0.1), c["stone"], 0.5)
        tile.put(cone * (tile.x > M + x + 0.8), c["stone"], 0.4)
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M + x - 2.8, G - 1.4, M + x + 2.8, G)), c["wood"])
    lying = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M + 5.0, G - 1.0), (M + 10.0, G - 1.6), (M + 10.0, G - 4.2), (M + 5.0, G - 4.8)]))
    tile.put(lying, c["stone_light"])
    tile.put(lying * (tile.y > G - 2.2), c["stone"], 0.5)
    tile.alpha *= tile.y < G


def oil_can(tile: Tile, c: dict) -> None:
    """An oil can for the machines: a round body, a long thin spout and a
    handle; a drop of oil at its foot."""
    _shadow(tile, 6.0)
    body = tile.mask(lambda p, dx, dy: (_dot(p, dx, dy, M - 1.0, G - 3.4, 5.0, ry=3.4), _box(p, dx, dy, M - 6.0, G - 3.4, M + 4.0, G)))
    tile.put(body, c["metal"])
    tile.put(body * (tile.y < G - 4.4), c["stone_light"], 0.30)
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 6.0, G - 2.2, M + 4.0, G - 1.4)), c["bloom"])
    tile.put(tile.mask(lambda p, dx, dy: (_poly(p, dx, dy, [(M - 2.6, G - 6.4), (M + 0.6, G - 6.4), (M - 0.4, G - 9.0), (M - 1.6, G - 9.0)]), _line(p, dx, dy, [(M - 1.0, G - 8.6), (M + 7.0, G - 15.0)], 0.5))), c["metal"])
    tile.put(tile.mask(lambda p, dx, dy: p.arc([(M + 1.0) * K + dx, (G - 8.0) * K + dy, (M + 6.0) * K + dx, (G - 2.0) * K + dy], 270, 90, fill=255, width=int(0.6 * K))), c["metal"])
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + 8.6, G - 0.4, 1.4, ry=0.4)), c["dark"], 0.8)
    tile.alpha *= tile.y < G


# The History dimension, second pass, one place to each group. In the Rift
# Valley `metal` is flint and `wood` is red earth; in the Green Sahara and
# on the downs `wood` is the clay of pots; in the Ice Age `stone_light` is
# ivory; on the Indus `wood` is terracotta and `stone_light` steatite; on
# the Yellow River `wood` is red clay and `bloom` the black of its paint; in
# the maize fields `glow` and `bloom` are yellow and red maize; in the
# highlands `metal` is polished greenstone; in the painted cave `bloom` is
# red ochre.


def hand_axe(tile: Tile, c: dict) -> None:
    """A hand axe of flint, the shape of a tear, that leans on a stone: the
    scars of the flakes that were knocked off it show on its face."""
    _shadow(tile, 6.0)
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 6.0, G), (M - 5.0, G - 3.0), (M - 1.0, G - 4.4), (M + 2.0, G - 3.6), (M + 3.0, G)])), c["stone"])
    axe = [(M + 0.4, G), (M + 4.6, G - 1.0), (M + 6.6, G - 6.0), (M + 5.6, G - 12.0), (M + 3.6, G - 14.6), (M + 1.4, G - 11.6), (M - 0.2, G - 6.0)]
    body = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, axe))
    tile.put(body, c["metal"])
    scars = [(M + 2.4, G - 3.0, 1.6), (M + 4.4, G - 6.0, 1.4), (M + 2.6, G - 8.4, 1.2), (M + 4.0, G - 10.6, 1.0), (M + 1.6, G - 5.6, 1.1)]
    tile.put(body * (tile.x < M + 2.6), c["stone_light"], 0.18)
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x - r, y + r * 0.4), (x, y - r * 0.2), (x + r, y + r * 0.3)], 0.25) for x, y, r in scars]) * body, c["dark"], 0.35)
    tile.alpha *= tile.y < G


def termite_mound(tile: Tile, c: dict) -> None:
    """A mound of the termites of red earth, tall and lumpy, with a few
    spires and the holes of its air shafts."""
    _shadow(tile, 6.5)
    body = tile.mask(lambda p, dx, dy: (
        _poly(p, dx, dy, [(M - 6.4, G), (M - 5.0, G - 6.0), (M - 3.6, G - 12.0), (M - 1.8, G - 17.0), (M - 0.4, G - 19.6), (M + 1.0, G - 16.0), (M + 2.4, G - 18.0), (M + 3.4, G - 12.0), (M + 5.0, G - 6.0), (M + 6.6, G)]),
        _dot(p, dx, dy, M - 3.6, G - 4.0, 3.0, ry=4.0),
        _dot(p, dx, dy, M + 3.8, G - 3.0, 2.8, ry=3.0),
    ))
    tile.put(body, c["wood"])
    tile.put(body * (tile.x < M - 1.2), c["wood_light"], 0.35)
    tile.put(body * (tile.x > M + 2.0), c["dark"], 0.25)
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, 0.55, ry=0.8) for x, y in ((M - 1.6, G - 9.0), (M + 1.8, G - 6.0), (M - 0.2, G - 14.0))]), c["dark"], 0.6)
    tile.alpha *= tile.y < G


def hearth(tile: Tile, c: dict) -> None:
    """A hearth on the ground: a ring of stones, sticks that cross, and a
    low fire that gives light."""
    _shadow(tile, 7.0)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, G - 6.0, 7.0), blur=1.8), c["glow"], 0.38)
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(M - 5.0, G - 0.6), (M + 4.0, G - 3.2)], 0.9), _line(p, dx, dy, [(M + 5.0, G - 0.6), (M - 4.0, G - 3.2)], 0.9)]), c["wood"])
    flame = [(M - 3.6, G - 2.0), (M - 2.2, G - 6.0), (M - 0.8, G - 4.6), (M + 0.2, G - 9.6), (M + 1.6, G - 5.4), (M + 2.6, G - 7.0), (M + 3.6, G - 2.0)]
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, flame)), c["glow"])
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 1.6, G - 2.0), (M + 0.2, G - 6.4), (M + 1.6, G - 2.0)])), _mix(c["glow"], (255, 255, 230), 0.6))
    stones = [(M - 7.0, 1.4), (M - 4.6, 1.6), (M - 1.6, 1.3), (M + 1.6, 1.4), (M + 4.6, 1.6), (M + 7.0, 1.4)]
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, G - r * 0.8, r, ry=r * 0.8) for x, r in stones]), c["stone"])
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x - 0.3, G - r * 1.1, r * 0.5, ry=r * 0.3) for x, r in stones]), c["stone_light"], 0.5)
    tile.alpha *= tile.y < G


def cow_skull(tile: Tile, c: dict) -> None:
    """The skull of a cow of the herders in the grass, its long horns in the
    shape of a lyre."""
    bone = _mix(c["stone_light"], (236, 228, 206), 0.4)
    _shadow(tile, 6.0)
    tile.put(tile.mask(lambda p, dx, dy: (_dot(p, dx, dy, M, G - 3.8, 3.0, ry=2.6), _poly(p, dx, dy, [(M - 2.0, G - 2.6), (M + 2.0, G - 2.6), (M + 1.2, G), (M - 1.2, G)]))), bone)
    for side in (-1.0, 1.0):
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M + side * 2.4, G - 5.0), (M + side * 6.4, G - 7.6), (M + side * 7.0, G - 12.0), (M + side * 5.4, G - 15.0)], 0.9)), _mix(bone, c["dark"], 0.15))
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M + x, G - 4.2, 0.8) for x in (-1.3, 1.3)]), c["dark"], 0.8)
    tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, [(M + x - 0.5, G), (M + x + 0.5, G), (M + x + lean, G - h)]) for x, h, lean in ((-8.0, 4.0, -0.4), (-7.0, 6.0, 0.4), (7.6, 5.0, 0.6), (8.6, 3.4, 0.8))]), c["plant"])
    tile.alpha *= tile.y < G


def tusk(tile: Tile, c: dict) -> None:
    """A tusk of a mammoth that lies on the snow, long and curved, its tip
    up, with a crack along it."""
    ivory = c["stone_light"]
    _shadow(tile, 9.0)
    pts = [(M - 9.0, G - 1.6), (M - 4.0, G - 1.8), (M + 1.0, G - 2.8), (M + 5.0, G - 5.0), (M + 7.6, G - 8.4), (M + 8.4, G - 11.6)]
    for k in range(len(pts) - 1):
        w = 1.6 - k * 0.24
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [pts[k], pts[k + 1]], w * 2.0)), ivory)
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(x, y + 0.6) for x, y in pts[:4]], 0.3)), c["dark"], 0.35)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M - 9.2, G - 1.6, 1.6, ry=1.5)), _mix(ivory, c["dark"], 0.35))
    tile.alpha *= tile.y < G


def standing_stone(tile: Tile, c: dict) -> None:
    """A small standing stone, taller than it is wide, with spots of lichen
    on it and grass at its foot."""
    _shadow(tile, 5.0)
    body = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 4.0, G), (M + 4.0, G), (M + 3.4, G - 12.0), (M + 1.6, G - 18.0), (M - 1.4, G - 18.6), (M - 3.4, G - 13.0)]))
    tile.put(body, c["stone"])
    tile.put(body * (tile.x < M - 1.0), c["stone_light"], 0.35)
    tile.put(body * (tile.x > M + 1.8), c["dark"], 0.25)
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M + x, G - y, r) for x, y, r in ((-1.6, 14.0, 0.9), (1.2, 9.0, 1.2), (-2.0, 6.0, 0.7), (2.0, 15.0, 0.6))]) * body, _mix(c["bloom"], c["stone_light"], 0.4), 0.7)
    tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, [(M + x - 0.5, G), (M + x + 0.5, G), (M + x + lean, G - h)]) for x, h, lean in ((-5.0, 3.0, -0.4), (-4.2, 4.4, 0.3), (4.4, 3.6, 0.5), (5.2, 2.4, 0.8))]), c["plant"])
    tile.alpha *= tile.y < G


def quern(tile: Tile, c: dict) -> None:
    """A grinding stone of the first farmers: a long low slab worn hollow on
    its top, a round stone to rub with on it, and grain spilled by it."""
    _shadow(tile, 9.0)
    slab = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 9.0, G), (M - 9.4, G - 3.6), (M - 6.0, G - 4.6), (M, G - 3.4), (M + 6.0, G - 4.6), (M + 9.2, G - 3.8), (M + 9.0, G)]))
    tile.put(slab, c["stone"])
    tile.put(slab * (tile.y < G - 3.2), c["stone_light"], 0.45)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M - 1.0, G - 5.4, 3.2, ry=1.8)), _mix(c["stone"], c["stone_light"], 0.3))
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M - 1.6, G - 6.2, 1.8, ry=0.6)), c["stone_light"], 0.5)
    grain = [(M + x, G - 0.4) for x in (-10.2, -9.8, 9.6, 10.0, 10.4)] + [(M + x, G - 3.9) for x in (3.0, 4.2, 5.0, 6.0)]
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, 0.35, ry=0.25) for x, y in grain]), c["glow"])
    tile.alpha *= tile.y < G


def round_shield(tile: Tile, c: dict) -> None:
    """A round shield of the north that stands on its rim against a stone:
    planks painted in two colours, a rim of hide and an iron boss."""
    _shadow(tile, 7.0)
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M + 2.0, G), (M + 3.4, G - 5.0), (M + 7.4, G - 6.2), (M + 9.6, G - 3.0), (M + 9.8, G)])), c["stone"])
    cx, cy, r = M - 1.4, G - 8.2, 8.0
    disc = tile.mask(lambda p, dx, dy: _dot(p, dx, dy, cx, cy, r, ry=r * 1.02))
    tile.put(disc, c["wood"])
    tile.put(disc * (((tile.x - cx) > 0) == ((tile.y - cy) > 0)), c["bloom"], 0.85)
    tile.put(disc * (np.abs(((tile.x - cx) % 2.4) - 1.2) < 0.12), c["dark"], 0.35)
    ring = disc * (1.0 - tile.mask(lambda p, dx, dy: _dot(p, dx, dy, cx, cy, r - 0.9)))
    tile.put(ring, _mix(c["wood"], c["dark"], 0.4))
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, cx, cy, 1.8)), c["metal"])
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, cx - 0.5, cy - 0.5, 0.7)), c["stone_light"], 0.7)
    tile.alpha *= tile.y < G


def indus_seal(tile: Tile, c: dict) -> None:
    """A seal of the Indus cities, large, on a stand: a square of white
    stone with a bull of one horn cut in it, and signs of the script over
    the bull that no one can read yet."""
    _shadow(tile, 6.5)
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 4.0, G - 2.0, M + 4.0, G)), c["wood"])
    body = tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 6.0, G - 14.0, M + 6.0, G - 2.0))
    tile.put(body, c["stone_light"])
    tile.put(body * (tile.y > G - 3.0), c["stone"], 0.5)
    tile.put(tile.mask(lambda p, dx, dy: (
        _dot(p, dx, dy, M - 0.4, G - 6.4, 3.0, ry=1.5),
        _dot(p, dx, dy, M + 3.0, G - 7.2, 1.0, ry=0.8),
        _line(p, dx, dy, [(M + 3.4, G - 7.8), (M + 1.0, G - 9.6)], 0.35),
        [_line(p, dx, dy, [(M + x, G - 5.4), (M + x, G - 3.4)], 0.4) for x in (-2.6, -1.4, 1.0, 2.0)],
    )), c["dark"], 0.6)
    tile.put(tile.mask(lambda p, dx, dy: [(_line(p, dx, dy, [(M + x, G - 12.6), (M + x, G - 10.6)], 0.35), _line(p, dx, dy, [(M + x - 0.6, G - 12.6), (M + x + 0.6, G - 12.6)], 0.3)) for x in (-4.0, -2.0, 0.4, 3.0)]), c["dark"], 0.55)
    tile.alpha *= tile.y < G


def toy_cart(tile: Tile, c: dict) -> None:
    """A toy of terracotta from the Indus: a small bull that pulls a cart on
    two solid wheels."""
    _shadow(tile, 8.0)
    tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, M - 1.0, G - 7.6, M + 7.0, G - 3.6), _box(p, dx, dy, M - 3.6, G - 5.0, M - 0.6, G - 4.4))), c["wood"])
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 1.0, G - 7.6, M + 7.0, G - 6.8)), c["wood_light"], 0.6)
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, G - 2.6, 2.6) for x in (M + 1.6, M + 5.0)]), _mix(c["wood"], c["dark"], 0.3))
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, G - 2.6, 0.7) for x in (M + 1.6, M + 5.0)]), c["dark"], 0.7)
    bull = tile.mask(lambda p, dx, dy: (
        _dot(p, dx, dy, M - 6.4, G - 5.6, 3.0, ry=1.8),
        _dot(p, dx, dy, M - 9.0, G - 6.4, 1.2, ry=1.1),
        [_box(p, dx, dy, M + x - 0.4, G - 4.4, M + x + 0.4, G) for x in (-8.4, -7.4, -5.4, -4.4)],
        _line(p, dx, dy, [(M - 9.4, G - 7.2), (M - 10.0, G - 9.0)], 0.4),
        _line(p, dx, dy, [(M - 8.6, G - 7.2), (M - 8.2, G - 9.0)], 0.4),
    ))
    tile.put(bull, c["wood"])
    tile.put(bull * (tile.y < G - 6.0), c["wood_light"], 0.4)
    tile.alpha *= tile.y < G


def brick_stack(tile: Tile, c: dict) -> None:
    """A stack of fired bricks for a new wall, in rows that cross."""
    _shadow(tile, 9.0)
    rng = tile.rng
    for row in range(4):
        y1 = G - row * 2.4
        n = 3 if row % 2 == 0 else 5
        w = 16.0 / n
        for i in range(n):
            x0 = M - 8.0 + i * w + (0.6 if row == 3 else 0.0)
            tone = rng.uniform(-0.15, 0.12)
            colour = _mix(c["wood"], c["wood_light"] if tone > 0 else c["dark"], abs(tone) * 1.6)
            tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 0.2, y1 - 2.2, x0 + w - 0.2, y1)), colour)
            tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 0.2, y1 - 2.2, x0 + w - 0.2, y1 - 1.8)), c["wood_light"], 0.5)
    tile.alpha *= tile.y < G


def painted_jar(tile: Tile, c: dict) -> None:
    """A jar of red clay of the first farmers of the Yellow River, painted in
    black: whirls and waves on its shoulder, and two small handles."""
    _shadow(tile, 6.0)
    body = tile.mask(lambda p, dx, dy: (_dot(p, dx, dy, M, G - 8.0, 6.4, ry=6.0), _poly(p, dx, dy, [(M - 3.0, G - 2.0), (M + 3.0, G - 2.0), (M + 2.0, G), (M - 2.0, G)]), _box(p, dx, dy, M - 2.4, G - 15.6, M + 2.4, G - 12.0)))
    tile.put(body, c["wood"])
    tile.put(body * (tile.x < M - 2.6), c["wood_light"], 0.40)
    tile.put(body * (tile.x > M + 3.0), c["dark"], 0.25)
    shoulder = body * (tile.y < G - 7.4) * (tile.y > G - 12.6)
    whirls = tile.mask(lambda p, dx, dy: [p.arc([(M + x - 1.8) * K + dx, (G - 11.6) * K + dy, (M + x + 1.8) * K + dx, (G - 8.0) * K + dy], 200, 520, fill=255, width=int(0.45 * K)) for x in (-3.6, 0.0, 3.6)])
    tile.put(whirls * shoulder, c["bloom"], 0.85)
    tile.put(body * (np.abs(tile.y - (G - 7.0) + 0.5 * np.sin(tile.x * 1.6)) < 0.3), c["bloom"], 0.85)
    tile.put(tile.mask(lambda p, dx, dy: [p.arc([(M + side * 6.2 - 1.0) * K + dx, (G - 8.6) * K + dy, (M + side * 6.2 + 1.0) * K + dx, (G - 6.6) * K + dy], 0, 360, fill=255, width=int(0.4 * K)) for side in (-1.0, 1.0)]), c["wood"])
    tile.alpha *= tile.y < G


def maize_cobs(tile: Tile, c: dict) -> None:
    """Cobs of maize that lean on each other, the husks pulled back: one
    yellow, one red, one of mixed colours, as the first farmers grew them."""
    _shadow(tile, 6.0)
    cobs = ((M - 3.4, -10.0, c["glow"]), (M, 0.0, c["bloom"]), (M + 3.4, 10.0, _mix(c["glow"], c["bloom"], 0.5)))
    for x, lean, colour in cobs:
        top = (x + lean * 0.10, G - 13.0)
        tile.put(tile.mask(lambda p, dx, dy: (_poly(p, dx, dy, [(x - 1.0, G), (x + 1.0, G), (top[0] + 1.6, top[1] + 1.0), (top[0], top[1] - 0.6), (top[0] - 1.6, top[1] + 1.0)]))), colour)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x + (top[0] - x) * t + o, G - 13.0 * t, 0.35) for t in np.linspace(0.1, 0.9, 8) for o in (-0.6, 0.6)]), _mix(colour, c["dark"], 0.3), 0.6)
        for side in (-1.0, 1.0):
            tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(x - 0.8 * side, G - 1.0), (x + side * 3.0, G - 4.0), (x + side * 4.2, G - 7.0), (x + side * 0.6, G - 3.0)])), _mix(c["plant"], (230, 220, 160), 0.5), 0.9)
    tile.alpha *= tile.y < G


def agave_plant(tile: Tile, c: dict) -> None:
    """An agave: a rosette of thick leaves, each with a sharp tip and small
    teeth on its edges, blue-green with a pale bloom."""
    leaves = []
    for k in range(9):
        ang = math.radians(-170.0 + k * 20.0)
        length = 7.0 + 4.0 * math.sin(-ang)
        tip = (M + math.cos(ang) * length, G - 1.0 + math.sin(ang) * length)
        nx, ny = -math.sin(ang) * 1.2, math.cos(ang) * 1.2
        leaves.append([(M - nx, G - 1.0 - ny), (M + nx, G - 1.0 + ny), tip])
    tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, pts) for pts in leaves[::2]]), c["plant"])
    tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, pts) for pts in leaves[1::2]]), _mix(c["plant"], c["stone_light"], 0.25))
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, G - 0.6, 3.0, ry=1.2)), c["plant"])
    tile.alpha *= tile.y < G


def taro(tile: Tile, c: dict) -> None:
    """A taro plant of the highland gardens: big leaves in the shape of a
    heart on long stalks, the veins light."""
    _shadow(tile, 6.0)
    for x, h, lean, r in ((-3.4, 12.0, -3.0, 4.0), (1.0, 17.0, 1.0, 4.6), (4.0, 10.0, 4.0, 3.4)):
        top = (M + x + lean, G - h)
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M + x * 0.3, G), top], 0.5)), _mix(c["plant"], c["dark"], 0.3))
        leaf = tile.mask(lambda p, dx, dy: (_dot(p, dx, dy, top[0] - r * 0.35, top[1] + r * 0.1, r * 0.62, ry=r * 0.5), _dot(p, dx, dy, top[0] + r * 0.35, top[1] + r * 0.1, r * 0.62, ry=r * 0.5), _poly(p, dx, dy, [(top[0] - r * 0.9, top[1] + r * 0.2), (top[0] + r * 0.9, top[1] + r * 0.2), (top[0], top[1] + r * 1.1)])))
        tile.put(leaf, c["plant"])
        tile.put(leaf * (tile.y < top[1] + r * 0.2), _mix(c["plant"], (230, 240, 190), 0.25))
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(top[0], top[1] - r * 0.2), (top[0], top[1] + r * 0.9)], 0.2)) * leaf, _mix(c["plant"], (240, 250, 210), 0.5), 0.8)
    tile.alpha *= tile.y < G


def stone_adze(tile: Tile, c: dict) -> None:
    """An adze of the highlands that leans on a log: a handle of wood bent
    at its top, and a blade of polished greenstone bound to it."""
    _shadow(tile, 8.0)
    tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, M - 9.0, G - 4.0, M + 2.0, G), _dot(p, dx, dy, M + 2.0, G - 2.0, 1.4, ry=2.0))), c["wood"])
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + 2.2, G - 2.0, 0.8, ry=1.2)), c["wood_light"], 0.7)
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M + 6.0, G), (M + 2.6, G - 13.0), (M - 1.4, G - 15.6)], 0.9)), _mix(c["wood"], c["wood_light"], 0.3))
    blade = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 1.2, G - 16.4), (M - 0.4, G - 14.6), (M - 4.6, G - 12.2), (M - 5.4, G - 13.0)]))
    tile.put(blade, c["metal"])
    tile.put(blade * (tile.y < G - 14.0), c["stone_light"], 0.35)
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(M - 2.0 + k * 0.5, G - 16.2 + k * 0.4), (M - 0.4 + k * 0.5, G - 14.4 + k * 0.4)], 0.3) for k in range(3)]), _mix(c["wood"], (200, 180, 140), 0.4))
    tile.alpha *= tile.y < G


def stone_lamp(tile: Tile, c: dict) -> None:
    """A lamp of the painters of the caves: a hollow in a stone with a
    handle, fat in it, and a small flame of a wick of moss."""
    _shadow(tile, 6.0)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M - 1.0, G - 6.5, 5.0), blur=1.4), c["glow"], 0.40)
    body = tile.mask(lambda p, dx, dy: (_dot(p, dx, dy, M - 1.0, G - 2.6, 4.6, ry=2.6), _poly(p, dx, dy, [(M + 2.6, G - 3.4), (M + 8.0, G - 2.6), (M + 8.0, G - 1.0), (M + 2.6, G - 1.0)])))
    tile.put(body, c["stone"])
    tile.put(body * (tile.y < G - 3.6), c["stone_light"], 0.4)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M - 1.0, G - 4.6, 3.4, ry=0.7)), c["dark"], 0.7)
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 2.0, G - 4.8), (M - 1.0, G - 9.6), (M + 0.0, G - 4.8)])), c["glow"])
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M - 1.0, G - 5.4, 0.45)), (255, 255, 240))
    tile.alpha *= tile.y < G


def ochre_palette(tile: Tile, c: dict) -> None:
    """The paints of the cave on a flat stone: lumps of red and yellow
    ochre, a lump of charcoal, a shell with red paint in it, and a brush of
    chewed twig."""
    _shadow(tile, 9.0)
    slab = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 9.0, G), (M - 8.4, G - 2.4), (M + 8.6, G - 2.8), (M + 9.4, G)]))
    tile.put(slab, c["stone"])
    tile.put(slab * (tile.y < G - 2.0), c["stone_light"], 0.4)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M - 5.6, G - 3.6, 1.8, ry=1.3)), c["bloom"])
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M - 2.4, G - 3.4, 1.4, ry=1.1)), _mix(c["glow"], c["bloom"], 0.35))
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + 0.4, G - 3.2, 1.1, ry=0.9)), c["dark"])
    shell = tile.mask(lambda p, dx, dy: p.pieslice([(M + 2.4) * K + dx, (G - 6.0) * K + dy, (M + 7.6) * K + dx, (G - 1.6) * K + dy], 180, 360, fill=255))
    tile.put(shell, _mix(c["stone_light"], (240, 230, 220), 0.4))
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + 5.0, G - 4.0, 2.0, ry=0.6)), c["bloom"])
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M - 7.0, G - 2.6), (M - 1.0, G - 8.6)], 0.5)), c["wood"])
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M - 1.0, G - 8.6, 0.8)), c["bloom"])
    tile.alpha *= tile.y < G


# The History dimension, third pass. In the Olmec heartland `metal` is
# jade, `wood` the clay and `bloom` a ripe pod of cacao; in the Maya city
# `wood` is red paint and `metal` jade; on the Taino islands `bloom` is the
# pink of a conch; on the Lapita shore `wood` is red-slipped clay and `metal`
# obsidian; on the open ocean `wood` is a gourd; on Rapa Nui `metal` is
# basalt and `bloom` lichen.


def cacao_pod(tile: Tile, c: dict) -> None:
    """A pod of cacao on the ground, ridged and pointed, and a half pod
    that is open with its pale beans in a row."""
    _shadow(tile, 7.0)
    pod = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 8.0, G - 3.0), (M - 6.0, G - 6.6), (M - 2.0, G - 7.4), (M + 1.4, G - 5.4), (M + 1.0, G - 1.4), (M - 3.0, G), (M - 6.6, G - 0.4)]))
    tile.put(pod, c["bloom"])
    tile.put(pod * (tile.y < G - 5.0), _mix(c["bloom"], (255, 230, 150), 0.35), 0.6)
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(M - 7.0, G - 3.0 + k * 0.4), (M - 3.0, G - 4.4 + k * 1.3), (M + 0.6, G - 3.0 + k * 0.8)], 0.25) for k in range(-1, 3)]) * pod, c["dark"], 0.40)
    half = tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + 6.0, G - 2.2, 4.4, ry=2.2))
    tile.put(half, _mix(c["bloom"], c["dark"], 0.25))
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + 6.0, G - 2.8, 3.6, ry=1.4)), (236, 226, 204))
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M + 3.6 + k * 1.2, G - 2.9, 0.55, ry=0.75) for k in range(5)]), (150, 96, 80), 0.9)
    tile.alpha *= tile.y < G


def rubber_ball(tile: Tile, c: dict) -> None:
    """A ball of rubber, black and a little shiny, by a bowl of white
    latex: the people of the Gulf coast made rubber first, of latex and the
    juice of a vine."""
    _shadow(tile, 8.0)
    bowl = tile.mask(lambda p, dx, dy: p.pieslice([(M + 1.0) * K + dx, (G - 9.0) * K + dy, (M + 10.0) * K + dx, (G + 0.0) * K + dy], 0, 180, fill=255))
    tile.put(bowl, c["wood"])
    tile.put(bowl * (tile.x < M + 4.0), c["wood_light"], 0.4)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + 5.5, G - 4.5, 4.4, ry=0.9)), (238, 234, 222))
    ball = tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M - 3.6, G - 5.2, 5.2))
    tile.put(ball, (40, 36, 34))
    tile.put(ball * np.clip(1.0 - ((tile.x - (M - 5.4)) ** 2 + (tile.y - (G - 7.2)) ** 2) / 6.0, 0.0, 1.0), (170, 170, 160), 0.6)
    tile.alpha *= tile.y < G


def jade_celts(tile: Tile, c: dict) -> None:
    """Celts of polished jade, the blades of axes made to be given, that
    stand on their ends in a row as an offering is laid out."""
    _shadow(tile, 8.0)
    for k, (x, h, lean) in enumerate(((-5.4, 10.0, -1.0), (-1.8, 13.0, -0.3), (1.8, 12.0, 0.3), (5.4, 9.0, 1.0))):
        body = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M + x - 1.3, G), (M + x + 1.3, G), (M + x + 0.9 + lean, G - h), (M + x - 0.9 + lean, G - h)]))
        tone = (0.0, 0.18, -0.10, 0.08)[k]
        tile.put(body, _mix(c["metal"], (230, 250, 230) if tone > 0 else c["dark"], abs(tone)))
        tile.put(body * (tile.x < M + x - 0.2 + lean * (G - tile.y) / h), (240, 255, 240), 0.25)
    tile.alpha *= tile.y < G


def glyph_block(tile: Tile, c: dict) -> None:
    """A block of a fallen inscription: a square of limestone with a glyph
    in it, a face in profile in a round cartouche, and a number in bars and
    dots on its side."""
    _shadow(tile, 7.5)
    body = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 7.0, G), (M + 7.0, G), (M + 7.4, G - 11.0), (M + 6.0, G - 12.0), (M - 6.4, G - 12.0), (M - 7.2, G - 10.6)]))
    tile.put(body, c["stone"])
    tile.put(body * (tile.y < G - 11.2), c["stone_light"], 0.5)
    tile.put(body * (tile.x > M + 6.0), c["dark"], 0.25)
    tile.put(tile.mask(lambda p, dx, dy: p.ellipse([(M - 4.6) * K + dx, (G - 10.0) * K + dy, (M + 3.0) * K + dx, (G - 2.4) * K + dy], outline=255, width=max(1, int(0.5 * K)))), c["dark"], 0.45)
    face = [(M - 2.6, G - 8.6), (M - 0.6, G - 8.8), (M + 0.4, G - 7.0), (M + 1.2, G - 6.4), (M + 0.2, G - 5.6), (M + 0.6, G - 4.6), (M - 1.0, G - 4.0), (M - 2.8, G - 4.6)]
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, face)), c["dark"], 0.40)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M - 0.8, G - 7.4, 0.4)), c["stone_light"], 0.8)
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, M + 4.2, G - 10.0 + j * 1.4, M + 6.0, G - 9.4 + j * 1.4) for j in range(2)] + [_dot(p, dx, dy, M + 5.1, G - 4.0 + j * 1.2, 0.35) for j in range(2)]), c["dark"], 0.5)
    tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, [(M + x - 0.5, G), (M + x + 0.5, G), (M + x + lean, G - h)]) for x, h, lean in ((-8.0, 3.0, -0.6), (-7.4, 4.2, 0.2), (7.8, 3.6, 0.6))]), c["plant"])
    tile.alpha *= tile.y < G


def cylinder_vase(tile: Tile, c: dict) -> None:
    """A tall painted vase of the kind that held a drink of cacao: a
    cylinder of cream clay with red bands and a row of glyphs round its
    rim."""
    _shadow(tile, 5.5)
    body = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 4.0, G), (M + 4.0, G), (M + 4.6, G - 14.0), (M - 4.6, G - 14.0)]))
    tile.put(body, c["stone_light"])
    tile.put(body * (tile.x < M - 2.4), (255, 252, 240), 0.35)
    tile.put(body * (tile.x > M + 2.6), c["dark"], 0.25)
    for y0, y1 in ((13.6, 12.4), (2.0, 0.8)):
        tile.put(body * (tile.y > G - y0) * (tile.y < G - y1), c["wood"])
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, M + x - 0.7, G - 11.4, M + x + 0.7, G - 10.0) for x in (-3.0, -1.0, 1.0, 3.0)]), c["dark"], 0.55)
    figure = [(M - 1.6, G - 3.0), (M - 1.0, G - 7.6), (M + 0.2, G - 8.4), (M + 1.2, G - 7.6), (M + 1.6, G - 3.0)]
    tile.put(tile.mask(lambda p, dx, dy: (_poly(p, dx, dy, figure), _dot(p, dx, dy, M + 0.2, G - 9.0, 0.9))) * body, c["wood"], 0.75)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, G - 14.0, 4.6, ry=0.8)), c["dark"], 0.6)
    tile.alpha *= tile.y < G


def copal_burner(tile: Tile, c: dict) -> None:
    """A burner of incense: a bowl of clay on three feet with a small fire
    of copal resin in it, and its white smoke."""
    _shadow(tile, 5.5)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, G - 8.0, 6.0), blur=1.6), c["glow"], 0.36)
    smoke = tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M + math.sin(k * 0.9) * 1.4, G - 10.0 - k * 1.6, 0.9 + k * 0.25) for k in range(7)], blur=0.6)
    tile.put(smoke, (236, 236, 228), 0.45)
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, M + x - 0.6, G - 2.4, M + x + 0.6, G) for x in (-3.4, 0.0, 3.4)]), c["wood"])
    bowl = tile.mask(lambda p, dx, dy: p.pieslice([(M - 5.0) * K + dx, (G - 11.0) * K + dy, (M + 5.0) * K + dx, (G - 1.6) * K + dy], 0, 180, fill=255))
    tile.put(bowl, c["wood"])
    tile.put(bowl * (tile.x < M - 2.0), c["wood_light"], 0.35)
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M + x, G - 4.4, 0.45) for x in (-3.0, -1.0, 1.0, 3.0)]), c["dark"], 0.5)
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 2.0, G - 6.4), (M - 0.6, G - 9.0), (M, G - 7.8), (M + 0.8, G - 10.2), (M + 2.0, G - 6.4)])), c["glow"])
    tile.alpha *= tile.y < G


def conch(tile: Tile, c: dict) -> None:
    """A queen conch on the sand: a heavy shell with knobs on its spire and
    the wide pink lip that the Taino made trumpets of."""
    _shadow(tile, 8.0)
    shell = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 8.0, G - 1.0), (M - 4.0, G - 6.4), (M + 1.0, G - 8.4), (M + 6.6, G - 7.0), (M + 8.4, G - 3.0), (M + 6.0, G), (M - 6.0, G)]))
    tile.put(shell, c["stone_light"])
    tile.put(shell * (tile.y > G - 3.0), _mix(c["stone_light"], c["dark"], 0.25))
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M + x, G - y, 0.9) for x, y in ((-4.6, 6.4), (-2.0, 7.8), (1.0, 8.6), (4.0, 8.2))]), c["stone_light"])
    lip = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M + 1.0, G - 1.0), (M + 4.0, G - 6.0), (M + 8.6, G - 6.4), (M + 9.0, G - 2.0), (M + 6.0, G - 0.4)]))
    tile.put(lip, c["bloom"])
    tile.put(lip * (tile.x > M + 6.0), (255, 236, 220), 0.4)
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M - 7.0, G - 1.2), (M - 9.2, G - 0.6)], 0.8)), c["stone_light"])
    tile.alpha *= tile.y < G


def cassava_plant(tile: Tile, c: dict) -> None:
    """A cassava (yuca) plant of a Taino garden mound: thin knotted stems
    and leaves split like a hand into long lobes."""
    _shadow(tile, 6.0)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, G, 7.0, ry=2.0)), c["wood"])
    tips = []
    for k, (x, h) in enumerate(((-2.0, 15.0), (1.0, 18.0), (3.4, 13.0))):
        top = (M + x + (k - 1) * 1.2, G - h)
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M + x * 0.5, G - 1.0), top], 0.45)), _mix(c["wood"], c["plant"], 0.4))
        tips.append(top)
    for x0, y0 in tips:
        for j in range(7):
            ang = math.radians(-160.0 + j * 23.0)
            length = 3.6 if j in (2, 3, 4) else 2.6
            tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(x0, y0), (x0 + math.cos(ang + 0.18) * length * 0.5, y0 + math.sin(ang + 0.18) * length * 0.5), (x0 + math.cos(ang) * length, y0 + math.sin(ang) * length), (x0 + math.cos(ang - 0.18) * length * 0.5, y0 + math.sin(ang - 0.18) * length * 0.5)])), c["plant"] if j % 2 else _mix(c["plant"], (230, 240, 190), 0.2))
    tile.alpha *= tile.y < G


def lapita_sherd(tile: Tile, c: dict) -> None:
    """The broken half of a Lapita pot that leans on a stone: red clay with
    bands of fine stamped teeth in white lime, in faces and in zigzags."""
    _shadow(tile, 7.5)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + 5.0, G - 2.0, 3.4, ry=2.2)), c["stone"])
    pot = tile.mask(lambda p, dx, dy: p.pieslice([(M - 8.0) * K + dx, (G - 13.0) * K + dy, (M + 6.0) * K + dx, (G + 1.0) * K + dy], 200, 360, fill=255))
    tile.put(pot, c["wood"])
    tile.put(pot * (tile.y > G - 3.0), c["dark"], 0.25)
    rows = []
    for row, yy in enumerate((G - 9.0, G - 7.4, G - 5.2)):
        for k in range(14):
            x = M - 6.4 + k * 0.85
            zig = (0.6 if (k + row) % 2 else 0.0) if row == 2 else 0.0
            rows.append((x, yy - zig))
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, 0.22) for x, y in rows]) * pot, (244, 236, 220), 0.9)
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M - 1.0 + x, G - 7.4, 0.45) for x in (-0.9, 0.9)]) * pot, (244, 236, 220), 0.8)
    tile.alpha *= tile.y < G


def obsidian(tile: Tile, c: dict) -> None:
    """A core of obsidian and the flakes knocked off it: black volcanic
    glass, sharp, with a shine on each face."""
    _shadow(tile, 7.0)
    core = [(M - 6.4, G), (M - 6.0, G - 4.6), (M - 3.4, G - 7.4), (M - 0.4, G - 6.6), (M + 0.8, G - 3.0), (M + 0.2, G)]
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, core)), c["metal"])
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 5.6, G - 4.2), (M - 3.4, G - 6.8), (M - 2.6, G - 4.0)])), (180, 190, 200), 0.45)
    flakes = [((M + 3.0, G), (M + 4.4, G - 3.0), (M + 5.4, G)), ((M + 6.0, G), (M + 7.0, G - 2.0), (M + 8.4, G - 0.4), (M + 7.6, G)), ((M + 1.6, G), (M + 2.4, G - 1.4), (M + 3.0, G))]
    tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, list(pts)) for pts in flakes]), c["metal"])
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [pts[0], pts[1]], 0.25) for pts in flakes]), (200, 210, 220), 0.55)
    tile.alpha *= tile.y < G


def coconuts(tile: Tile, c: dict) -> None:
    """Coconuts for the voyage: two in their green husks and one husked,
    brown and hairy, with its three eyes."""
    _shadow(tile, 8.0)
    for x, r, colour in ((-4.6, 4.2, c["plant"]), (3.0, 4.6, _mix(c["plant"], c["dark"], 0.2))):
        nut = tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + x, G - r * 0.9, r, ry=r * 0.9))
        tile.put(nut, colour)
        tile.put(nut * (tile.x < M + x - r * 0.3) * (tile.y < G - r), (220, 230, 160), 0.30)
    brown = tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M - 0.4, G - 2.6, 2.8, ry=2.6))
    tile.put(brown, c["wood"])
    tile.put(brown * (np.abs(((tile.x + tile.y * 0.7) % 0.9) - 0.45) < 0.12), c["dark"], 0.35)
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M - 0.4 + x, G - 3.6 + y, 0.35) for x, y in ((-0.7, 0.0), (0.7, 0.0), (0.0, 0.9))]), c["dark"], 0.8)
    tile.alpha *= tile.y < G


def water_gourd(tile: Tile, c: dict) -> None:
    """A gourd that holds water for the voyage, in a net of cord, with a
    stopper of rolled leaf."""
    _shadow(tile, 6.0)
    body = tile.mask(lambda p, dx, dy: (_dot(p, dx, dy, M, G - 5.6, 5.6, ry=5.4), _dot(p, dx, dy, M + 0.4, G - 12.4, 2.6, ry=2.8), _box(p, dx, dy, M - 1.0, G - 12.0, M + 1.6, G - 9.0)))
    tile.put(body, c["wood"])
    tile.put(body * (tile.x < M - 1.6), c["wood_light"], 0.40)
    tile.put(body * (tile.x > M + 2.6), c["dark"], 0.30)
    net = (np.abs(((tile.x + tile.y) % 2.4) - 1.2) < 0.14) | (np.abs(((tile.x - tile.y) % 2.4) - 1.2) < 0.14)
    tile.put(body * net * (tile.y > G - 9.0), c["stone_light"], 0.55)
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 0.4, G - 16.4, M + 1.2, G - 14.6)), c["plant"])
    tile.alpha *= tile.y < G


def paenga(tile: Tile, c: dict) -> None:
    """A kerbstone of a boat-shaped house: a long dressed block of basalt,
    curved, with holes in its top where the poles of the frame stood."""
    _shadow(tile, 9.5)
    body = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 9.6, G), (M - 9.0, G - 4.0), (M - 4.0, G - 5.0), (M + 4.0, G - 5.0), (M + 9.0, G - 4.0), (M + 9.6, G)]))
    tile.put(body, c["metal"])
    tile.put(body * (tile.y < G - 4.2), c["stone_light"], 0.30)
    tile.put(body * (tile.y > G - 1.4), c["dark"], 0.30)
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M + x, G - 4.5, 0.9, ry=0.35) for x in (-6.0, -2.0, 2.0, 6.0)]), c["dark"], 0.8)
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M + x, G - y, r) for x, y, r in ((-5.0, 2.6, 0.7), (3.4, 2.2, 0.9))]) * body, c["bloom"], 0.55)
    tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, [(M + x - 0.5, G), (M + x + 0.5, G), (M + x + lean, G - h)]) for x, h, lean in ((-10.4, 2.6, -0.4), (10.2, 3.2, 0.6))]), c["plant"])
    tile.alpha *= tile.y < G


# The Atlantic world. In Benin City `wood` is red-brown clay, `metal`
# brass, `bloom` the red of kola nuts and `stone_light` the white of cowries.


def yams(tile: Tile, c: dict) -> None:
    """Three yams in a heap: long tubers, thick in the middle and narrow at
    the ends, with rough dark brown skin and fine roots; one is cut across
    so its white flesh shows."""
    _shadow(tile, 8.5)
    skin_colour = _mix(c["wood"], (96, 66, 44), 0.65)

    def tuber(x0: float, y0: float, x1: float, y1: float, thick: float) -> list:
        mx, my = (x0 + x1) * 0.5, (y0 + y1) * 0.5
        nx, ny = -(y1 - y0), x1 - x0
        d = math.hypot(nx, ny) or 1.0
        nx, ny = nx / d * thick, ny / d * thick
        return [(x0, y0), (mx * 0.6 + x0 * 0.4 + nx, my * 0.6 + y0 * 0.4 + ny), (mx * 0.6 + x1 * 0.4 + nx * 0.9, my * 0.6 + y1 * 0.4 + ny * 0.9), (x1, y1),
                (mx * 0.6 + x1 * 0.4 - nx * 0.8, my * 0.6 + y1 * 0.4 - ny * 0.8), (mx * 0.6 + x0 * 0.4 - nx, my * 0.6 + y0 * 0.4 - ny)]

    for x0, y0, x1, y1, thick in ((M - 10.0, G - 1.4, M + 1.0, G - 2.6, 2.4), (M - 1.0, G - 1.2, M + 9.0, G - 3.0, 2.6), (M - 7.0, G - 6.0, M + 6.0, G - 5.0, 2.4)):
        pts = tuber(x0, y0, x1, y1, thick)
        body = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, pts))
        tile.put(body, skin_colour)
        tile.put(body * (tile.y < (y0 + y1) * 0.5 - thick * 0.4), _mix(skin_colour, (220, 190, 150), 0.30), 0.6)
        tile.put(body * (np.abs(((tile.x * 1.1 + tile.y * 0.5) % 1.7) - 0.85) < 0.10), c["dark"], 0.35)
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x1, y1), (x1 + 1.2, y1 + 0.6)], 0.15), _line(p, dx, dy, [(x0, y0), (x0 - 1.0, y0 + 0.8)], 0.15)]), c["dark"], 0.6)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + 9.2, G - 3.0, 1.0, ry=2.0)), (244, 236, 214))
    tile.alpha *= tile.y < G


def cowries(tile: Tile, c: dict) -> None:
    """A heap of cowrie shells, the money of the coast and of Benin: small
    white shells, each an egg with a slit and a row of teeth on its face."""
    _shadow(tile, 8.0)
    shells = [(-6.0, 1.2), (-3.6, 1.2), (-1.2, 1.2), (1.2, 1.2), (3.6, 1.2), (6.0, 1.2), (-4.8, 3.2), (-2.4, 3.2), (0.0, 3.2), (2.4, 3.2), (4.8, 3.2),
              (-3.6, 5.2), (-1.2, 5.2), (1.2, 5.2), (3.6, 5.2), (-2.4, 7.2), (0.0, 7.2), (2.4, 7.2), (-1.2, 9.0), (1.2, 9.0), (9.2, 1.0)]
    for k, (x, y) in enumerate(shells):
        body = tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + x, G - y, 1.4, ry=1.0))
        tile.put(body, c["dark"], 0.45)
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + x - 0.1, G - y - 0.15, 1.2, ry=0.85)), c["stone_light"] if k % 3 else _mix(c["stone_light"], (220, 200, 160), 0.35))
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M + x - 0.8, G - y), (M + x + 0.8, G - y)], 0.18)), c["dark"], 0.7)
    tile.alpha *= tile.y < G


def kola_nuts(tile: Tile, c: dict) -> None:
    """Kola nuts in a shallow bowl of carved wood, as they are offered to a
    guest: red and pale nuts, each in lobes."""
    _shadow(tile, 7.5)
    nuts = [(-3.4, 6.0, c["bloom"]), (0.0, 6.6, _mix(c["bloom"], (240, 210, 170), 0.55)), (3.4, 6.0, c["bloom"]), (-1.6, 8.0, _mix(c["bloom"], c["dark"], 0.2)),
            (1.8, 8.0, c["bloom"])]
    for x, y, colour in nuts:
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + x, G - y, 2.0, ry=1.6)), colour)
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M + x, G - y - 1.4), (M + x + 0.3, G - y + 1.2)], 0.2)), c["dark"], 0.5)
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + x - 0.7, G - y - 0.6, 0.5)), (255, 240, 220), 0.35)
    bowl = tile.mask(lambda p, dx, dy: p.pieslice([(M - 7.0) * K + dx, (G - 13.0) * K + dy, (M + 7.0) * K + dx, (G - 1.0) * K + dy], 0, 180, fill=255))
    tile.put(bowl, _mix(c["wood"], c["dark"], 0.35))
    tile.put(bowl * (tile.x < M - 3.0), c["wood_light"], 0.30)
    tile.put(bowl * (np.abs(((tile.x + tile.y) % 2.4) - 1.2) < 0.2) * (tile.y > G - 6.0), c["dark"], 0.35)
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 2.4, G - 1.2, M + 2.4, G)), _mix(c["wood"], c["dark"], 0.35))
    tile.alpha *= tile.y < G


def brass_bell(tile: Tile, c: dict) -> None:
    """A small bell of cast brass, of the kind rung at a shrine: a tall
    square bell that narrows to its top, with a loop to hang it, a pattern
    cast on its face, and a short striker that leans on it."""
    _shadow(tile, 5.0)
    body = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 4.6, G - 0.6), (M + 4.6, G - 0.6), (M + 2.6, G - 11.0), (M - 2.6, G - 11.0)]))
    tile.put(body, c["metal"])
    tile.put(body * (tile.x < M - 1.4), (255, 236, 170), 0.45)
    tile.put(body * (tile.x > M + 1.6), c["dark"], 0.30)
    tile.put(tile.mask(lambda p, dx, dy: p.ellipse([(M - 1.8) * K + dx, (G - 14.6) * K + dy, (M + 1.8) * K + dx, (G - 10.8) * K + dy], outline=255, width=max(1, int(0.7 * K)))), c["metal"])
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, M - 3.6 + k * 0.3, G - 3.4 - k * 2.4, M + 3.6 - k * 0.3, G - 3.0 - k * 2.4) for k in range(3)]), _mix(c["metal"], c["dark"], 0.45), 0.8)
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M + x, G - 5.8, 0.45) for x in (-1.6, 0.0, 1.6)]), _mix(c["metal"], c["dark"], 0.5), 0.8)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, G - 0.9, 4.4, ry=0.6)), c["dark"], 0.6)
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M + 5.4, G - 0.4), (M + 8.6, G - 7.6)], 0.7)), _mix(c["wood"], c["dark"], 0.3))
    tile.alpha *= tile.y < G


# Saint-Domingue. There `metal` is the orange of a squash, `bloom` the red of
# ripe coffee cherries, and `wood` the clay of the pots and the tan of the
# gourds.


def joumou(tile: Tile, c: dict) -> None:
    """A joumou: a big squash of the island, wide and flat, with deep ribs
    from its stem to its foot, orange with a mottle of green, and a short
    thick stem. Its soup is the soup of 1 January."""
    _shadow(tile, 9.0)
    lobes = [(-6.2, 3.4), (-3.4, 4.2), (0.0, 4.6), (3.4, 4.2), (6.2, 3.4)]
    for k, (x, rx) in enumerate(lobes):
        body = tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + x, G - 5.6, rx, ry=5.4))
        colour = c["metal"] if k % 2 == 0 else _mix(c["metal"], c["dark"], 0.12)
        tile.put(body, colour)
        tile.put(body * (tile.x < M + x - rx * 0.3), _mix(c["metal"], (255, 236, 190), 0.35), 0.5)
    whole = tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, G - 5.6, 9.6, ry=5.4))
    tile.put(whole * (tile.y > G - 2.6), c["dark"], 0.30)
    mottle = np.clip((tile.noise(5, 5, 2) - 0.55) * 5.0, 0.0, 1.0)
    tile.put(whole * mottle, _mix(c["plant"], c["metal"], 0.35), 0.5)
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(M + x * 1.18, G - 10.2), (M + x * 1.30, G - 5.6), (M + x * 1.18, G - 1.2)], 0.25) for x in (-4.8, -1.7, 1.7, 4.8)]),
             c["dark"], 0.40)
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 1.0, G - 10.4), (M + 0.6, G - 10.4), (M + 1.8, G - 13.6), (M + 0.6, G - 13.8)])), _mix(c["plant"], c["wood"], 0.4))
    tile.alpha *= tile.y < G


def coffee_bush(tile: Tile, c: dict) -> None:
    """A young coffee bush: thin branches that reach out from a stem and
    bend down a little, pairs of long dark glossy leaves along them, and
    small tight clusters of ripe red cherries where the leaves meet the
    branch."""
    _shadow(tile, 7.0)
    bark = _mix(c["wood"], c["dark"], 0.5)
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M, G), (M - 0.2, G - 8.0), (M + 0.3, G - 16.0)], 0.5)), bark)
    rng = tile.rng
    for y, half in ((4.4, 7.2), (8.0, 6.6), (11.4, 5.2), (14.4, 3.4)):
        for side in (-1.0, 1.0):
            tip = (M + side * half, G - y + 1.4)
            tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M, G - y), (M + side * half * 0.6, G - y - 0.4), tip], 0.28)), bark)
            for t in (0.35, 0.65, 0.95):
                x, yy = M + side * half * t, G - y - 0.4 + 1.8 * max(0.0, t - 0.6)
                for up in (-1.0, 1.0):
                    lx, ly = x + side * 1.4, yy + up * 1.3
                    leaf = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(x, yy), (lx - side * 0.2, ly - 0.7), (lx + side * 1.4, ly + up * 0.3), (lx, ly + 0.7)]))
                    tile.put(leaf, c["plant"] if up < 0 else _mix(c["plant"], c["dark"], 0.35))
                    tile.put(leaf * (tile.y < ly - 0.2), (220, 240, 200), 0.18)
                if t < 0.9 and rng.random() < 0.8:
                    berries = [(x + rng.uniform(-0.5, 0.5), yy + 0.5 + rng.uniform(-0.2, 0.4)) for _ in range(3)]
                    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, bx, by, 0.5) for bx, by in berries]), c["bloom"])
                    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, bx - 0.15, by - 0.15, 0.15) for bx, by in berries]), (255, 210, 190), 0.6)
    tile.alpha *= tile.y < G


def cane_cuttings(tile: Tile, c: dict) -> None:
    """Cuttings of sugar cane for planting: short lengths of stalk, each
    with two or three joints, laid in a heap with a few dry leaves. A new
    plant grows from each joint."""
    _shadow(tile, 9.0)
    stalk = _mix(c["plant"], (220, 200, 120), 0.35)
    for x0, y0, x1, y1 in ((M - 9.0, G - 1.2, M + 5.0, G - 2.0), (M - 6.0, G - 3.4, M + 9.0, G - 2.6), (M - 8.0, G - 5.4, M + 6.0, G - 6.2), (M - 3.0, G - 7.6, M + 8.0, G - 6.8)):
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(x0, y0), (x1, y1)], 1.0)), stalk)
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(x0, y0 - 0.5), (x1, y1 - 0.5)], 0.35)), (255, 240, 190), 0.35)
        for t in (0.0, 0.35, 0.7, 1.0):
            jx, jy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(jx, jy - 1.0), (jx + 0.1, jy + 1.0)], 0.3)), c["dark"], 0.55)
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, x1, y1, 0.9)), _mix(stalk, (250, 240, 210), 0.5))
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(M + x, G - 1.0), (M + x + 3.0, G - 6.0), (M + x + 7.0, G - 7.5)], 0.25) for x in (-8.0, -5.0)]), _mix(c["wood"], (220, 190, 120), 0.5), 0.8)
    tile.alpha *= tile.y < G


# The Gold Coast. There `wood` is the tan of rope and net, and `metal` the
# faded orange of the floats of a net.


def fishing_net(tile: Tile, c: dict) -> None:
    """A fishing net piled on the sand to dry: a low soft heap of mesh, with
    the line of its floats along the top and a few loose loops at its foot."""
    _shadow(tile, 9.0)
    heap = tile.mask(lambda p, dx, dy: (_dot(p, dx, dy, M - 3.0, G - 2.6, 6.8, ry=3.2), _dot(p, dx, dy, M + 3.4, G - 2.2, 6.0, ry=2.8),
                                       _box(p, dx, dy, M - 9.4, G - 3.0, M + 9.2, G)))
    tile.put(heap, _mix(c["wood"], c["dark"], 0.45))
    mesh = (np.abs(((tile.x + tile.y) % 1.6) - 0.8) < 0.18) | (np.abs(((tile.x - tile.y) % 1.6) - 0.8) < 0.18)
    tile.put(heap * mesh, _mix(c["wood"], c["stone"], 0.4), 0.8)
    tile.put(heap * (tile.y > G - 1.8), c["dark"], 0.30)
    floats = [(M - 7.0, G - 3.6), (M - 3.6, G - 6.0), (M + 0.4, G - 6.2), (M + 4.2, G - 5.2), (M + 7.6, G - 3.0)]
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, floats, 0.3)), c["dark"], 0.5)
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, 0.7, ry=0.5) for x, y in floats[1::2]]), _mix(c["metal"], c["dark"], 0.25))
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M + 8.0, G - 0.4), (M + 10.0, G - 1.6), (M + 11.0, G - 0.3)], 0.2)), c["wood"], 0.8)
    tile.alpha *= tile.y < G


def rope_coil(tile: Tile, c: dict) -> None:
    """A thick rope laid down in a flat coil, seen from the side and a
    little above: rings that grow smaller to the top, each with the twist
    of the rope across it, and the free end that runs out on the sand."""
    _shadow(tile, 7.0)
    for k in range(4):
        y, rx = G - 1.0 - k * 1.5, 6.4 - k * 0.6
        ring = tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, y, rx, ry=1.5))
        tile.put(ring, c["wood"] if k % 2 == 0 else _mix(c["wood"], c["dark"], 0.12))
        twist = np.abs(((tile.x * 1.3 + tile.y * 2.0) % 1.3) - 0.65) < 0.14
        tile.put(ring * twist, c["dark"], 0.30)
        tile.put(ring * (tile.y < y - 0.6), c["wood_light"], 0.45)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, G - 5.6, 2.6, ry=0.7)), c["dark"], 0.55)
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M + 5.6, G - 0.8), (M + 8.0, G - 0.6), (M + 10.6, G - 1.2)], 0.7)), c["wood"])
    tile.alpha *= tile.y < G


def beach_stones(tile: Tile, c: dict) -> None:
    """A few round stones of the beach, smoothed by the sea: grey, each of
    its own tone, with a pale light on its top."""
    _shadow(tile, 8.0)
    stones = [(-5.0, 2.2, 3.4, 0.0), (0.8, 3.0, 4.2, 0.10), (5.8, 1.6, 2.4, -0.10), (-1.6, 1.0, 1.8, 0.18)]
    for x, ry, rx, tone in stones:
        body = tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + x, G - ry, rx, ry=ry))
        tile.put(body, _mix(c["stone"], c["stone_light"] if tone > 0 else c["dark"], abs(tone) * 2.0))
        tile.put(body * (tile.y < G - ry * 1.4), c["stone_light"], 0.45)
        tile.put(body * (tile.y > G - ry * 0.5), c["dark"], 0.25)
    tile.alpha *= tile.y < G


def sea_shells(tile: Tile, c: dict) -> None:
    """A few shells on the sand: a ribbed clam shell, a small spiral shell
    and two cowries."""
    clam = tile.mask(lambda p, dx, dy: p.pieslice([(M - 7.0) * K + dx, (G - 4.2) * K + dy, (M - 1.0) * K + dx, (G + 2.0) * K + dy], 180, 360, fill=255))
    tile.put(clam, c["stone_light"])
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(M - 4.0, G), (M - 4.0 + k * 1.0, G - 2.8)], 0.25) for k in (-2, -1, 0, 1, 2)]), c["bloom"], 0.7)
    spiral = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M + 0.4, G), (M + 4.6, G), (M + 3.0, G - 2.4), (M + 1.4, G - 3.4)]))
    tile.put(spiral, _mix(c["bloom"], c["stone_light"], 0.4))
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(M + 1.0 + k, G - 0.4), (M + 1.8 + k * 0.6, G - 2.6)], 0.2) for k in (0.0, 1.2)]), c["dark"], 0.4)
    for x in (M + 6.4, M + 8.6):
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, x, G - 1.0, 1.0, ry=0.8)), c["stone_light"])
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(x - 0.6, G - 1.0), (x + 0.6, G - 1.0)], 0.15)), c["dark"], 0.6)
    tile.alpha *= tile.y < G


# South America. In the high Andes `bloom` is the red of quinoa and `metal`
# its gold; at Caral `metal` is the tan-orange of a squash, `bloom` the
# yellow of its flower, and `wood` the straw of twisted reed.


def potatoes(tile: Tile, c: dict) -> None:
    """A small heap of potatoes, as the first farmers of the Andes grew
    them: of many kinds, each of its own colour and shape. Purple, red,
    yellow and white ones, round, long or knobbly, with small dark eyes."""
    _shadow(tile, 8.5)
    heap = [(-5.6, 2.2, 2.8, (104, 58, 112)), (-1.2, 2.4, 3.2, (214, 180, 96)), (3.6, 2.0, 2.6, (168, 56, 52)), (7.2, 1.7, 2.0, (226, 214, 186)),
            (-3.4, 5.6, 2.4, (176, 64, 60)), (1.2, 5.8, 2.8, (88, 50, 96)), (4.6, 5.0, 2.0, (222, 190, 104)), (-0.8, 8.8, 2.2, (232, 220, 196))]
    rng = tile.rng
    for x, up, r, colour in heap:
        ry = r * rng.uniform(0.70, 0.85)
        pts = [(M + x + math.cos(t) * r * (1.0 + rng.uniform(-0.10, 0.10)), G - up + math.sin(t) * ry * (1.0 + rng.uniform(-0.10, 0.10))) for t in np.linspace(0.0, 2.0 * math.pi, 11)[:-1]]
        body = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, pts))
        tile.put(body, colour)
        tile.put(body * (tile.y < G - up - ry * 0.25) * (tile.x < M + x + r * 0.3), _mix(colour, (255, 248, 230), 0.35), 0.7)
        tile.put(body * (tile.y > G - up + ry * 0.35), c["dark"], 0.35)
        eyes = [(M + x + rng.uniform(-0.6, 0.6) * r, G - up + rng.uniform(-0.5, 0.4) * ry) for _ in range(2)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, ex, ey, 0.3) for ex, ey in eyes]) * body, c["dark"], 0.65)
    tile.alpha *= tile.y < G


def ichu_tussock(tile: Tile, c: dict) -> None:
    """A tussock of ichu, the bunch grass of the high plain: a dense clump
    of thin, stiff, tawny blades that fan up and out from one base, with
    dry pale tips and a dark heart."""
    _shadow(tile, 8.0)
    rng = tile.rng
    blades = []
    for k in range(30):
        t = k / 29.0 - 0.5
        h = rng.uniform(13.0, 17.5) * (1.0 - abs(t) * 0.55)
        tip = (M + t * 18.0 + rng.uniform(-0.5, 0.5), G - h)
        mid = (M + t * 8.0, G - h * 0.55)
        blades.append(([(M + t * 3.0, G), mid, tip], k % 3))
    for shade in (2, 1, 0):
        colour = (_mix(c["plant"], c["dark"], 0.40), _mix(c["plant"], c["dark"], 0.12), c["plant"])[shade]
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, pts, 0.45) for pts, kind in blades if kind == shade]), colour)
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [pts[1], pts[2]], 0.3) for pts, kind in blades if kind == 0]) * (tile.y < G - 9.0), c["stone_light"], 0.45)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, G - 1.4, 3.6, ry=1.6)), c["dark"], 0.5)
    tile.alpha *= tile.y < G


def quinoa_plant(tile: Tile, c: dict) -> None:
    """Quinoa, a grain that the people of the Andes made a crop: tall
    stalks with leaves shaped like a goose's foot, each topped by a long,
    dense head of small seeds. One head is red and one is gold."""
    _shadow(tile, 6.0)
    green = (104, 132, 70)
    stem = _mix(green, c["dark"], 0.30)
    for x, h, head in ((-3.0, 19.0, c["bloom"]), (3.2, 16.0, c["metal"]), (0.2, 12.0, _mix(c["bloom"], c["metal"], 0.5))):
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M + x * 0.3, G), (M + x, G - h * 0.6), (M + x + 0.3, G - h + 4.0)], 0.5)), stem)
        for k, y in enumerate((h * 0.20, h * 0.38, h * 0.55)):
            side = 1.0 if (k % 2) else -1.0
            bx, by = M + x * (0.3 + 0.7 * y / h), G - y
            leaf = [(bx, by), (bx + side * 1.6, by - 1.8), (bx + side * 3.4, by - 1.0), (bx + side * 2.6, by + 0.4)]
            tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, leaf)), green)
            tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(bx, by), (bx + side * 2.8, by - 0.8)], 0.15)), c["dark"], 0.4)
        # The head: a dense column of small clusters of seed, narrow at its
        # tip.
        lumps = [(M + x + 0.3 + math.sin(j * 2.3) * 0.7, G - h + 4.5 - j * 0.55, 1.5 - j * 0.07) for j in range(15)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, lx, ly, r) for lx, ly, r in lumps]), _mix(head, c["dark"], 0.30))
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, lx - 0.3, ly - 0.3, r * 0.75) for lx, ly, r in lumps]), head)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, lx - 0.6, ly - 0.5, r * 0.30) for lx, ly, r in lumps]), _mix(head, (255, 240, 200), 0.5), 0.6)
    tile.alpha *= tile.y < G


def cotton_plant(tile: Tile, c: dict) -> None:
    """A cotton plant of the Supe valley: a low bush with broad dark leaves
    of three to five lobes, and open bolls: white tufts of fibre in a cup
    of brown, dry husk. The people of Caral grew it to make nets and
    cloth."""
    _shadow(tile, 7.5)
    stem = _mix(c["wood"], c["dark"], 0.45)
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(M, G), (M + x * 0.4, G - h * 0.5), (M + x, G - h)], 0.45) for x, h in ((-6.0, 12.0), (0.0, 16.0), (6.0, 11.0), (-2.6, 9.0), (3.4, 14.0))]),
             stem)
    for x, y, side in ((-5.0, 7.0, -1.0), (4.6, 6.4, 1.0), (-1.6, 11.0, -1.0), (2.4, 10.0, 1.0), (0.0, 5.0, 1.0)):
        lobes = [(M + x + side * dx_, G - y + dy_, r) for dx_, dy_, r in ((0.0, 0.0, 1.9), (1.4, -1.2, 1.4), (-1.2, -1.3, 1.4), (1.8, 0.7, 1.1), (-1.6, 0.8, 1.1))]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, lx, ly, r) for lx, ly, r in lobes]), _mix(c["plant"], c["dark"], 0.25))
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, lx - 0.3, ly - 0.4, r * 0.6) for lx, ly, r in lobes[:3]]), c["plant"], 0.8)
    for x, h in ((-6.0, 12.0), (0.0, 16.0), (6.0, 11.0), (3.4, 14.0), (-2.6, 9.0)):
        bx, by = M + x, G - h
        tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(bx - 2.0, by), (bx + 2.0, by), (bx + 1.2, by + 1.6), (bx - 1.2, by + 1.6)])), _mix(c["wood"], c["dark"], 0.30))
        puffs = [(bx - 1.1, by - 0.6, 1.3), (bx + 1.1, by - 0.6, 1.3), (bx, by - 1.6, 1.4), (bx, by - 0.2, 1.2)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, px, py, r) for px, py, r in puffs]), _mix(c["stone_light"], c["dark"], 0.10))
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, px - 0.3, py - 0.4, r * 0.6) for px, py, r in puffs]), (252, 250, 242), 0.85)
    tile.alpha *= tile.y < G


def squash_vine(tile: Tile, c: dict) -> None:
    """A squash of the valley on its vine: a long, ribbed fruit, tan-orange
    with a few green streaks, lying on the ground, with a big lobed leaf, a
    curl of tendril, and one yellow flower."""
    _shadow(tile, 9.0)
    vine = _mix(c["plant"], c["dark"], 0.30)
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M - 11.0, G - 1.0), (M - 6.0, G - 2.6), (M - 1.0, G - 2.0), (M + 4.0, G - 3.6), (M + 10.0, G - 2.6)], 0.5)), vine)
    # The leaf, behind the fruit.
    lx, ly = M - 4.0, G - 9.0
    lobes = [(lx, ly, 3.4), (lx - 2.6, ly + 1.4, 2.4), (lx + 2.8, ly + 1.0, 2.4), (lx - 1.4, ly - 2.2, 2.2), (lx + 1.6, ly - 2.0, 2.2)]
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M - 6.0, G - 2.6), (lx, ly + 2.0)], 0.4)), vine)
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, r) for x, y, r in lobes]), c["plant"])
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(lx, ly + 2.0), (x, y)], 0.15) for x, y, _ in lobes[1:]]), c["dark"], 0.4)
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x - 0.6, y - 0.6, r * 0.45) for x, y, r in lobes]), (220, 240, 190), 0.25)
    # The fruit: long, a little wider at its far end, with ribs.
    body = tile.mask(lambda p, dx, dy: (_dot(p, dx, dy, M + 2.4, G - 3.4, 3.4, ry=3.2), _dot(p, dx, dy, M + 7.6, G - 3.2, 2.6, ry=2.6),
                                         _box(p, dx, dy, M + 2.4, G - 6.0, M + 7.6, G - 0.6)))
    tile.put(body, c["metal"])
    tile.put(body * (tile.y < G - 4.6), _mix(c["metal"], (255, 236, 190), 0.35), 0.6)
    tile.put(body * (tile.y > G - 1.8), c["dark"], 0.30)
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(M + 0.0, G - 3.4 + d), (M + 10.0, G - 3.2 + d * 0.8)], 0.22) for d in (-1.8, 0.0, 1.6)]) * body, _mix(c["plant"], c["metal"], 0.4), 0.55)
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 1.4, G - 3.0), (M - 0.6, G - 4.6), (M - 2.6, G - 5.4), (M - 2.8, G - 4.4)])), vine)
    # A tendril and a flower.
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M + 4.0, G - 3.6), (M + 5.0, G - 7.0), (M + 6.4, G - 7.6), (M + 6.6, G - 6.4), (M + 5.8, G - 6.2)], 0.2)), vine)
    fx, fy = M - 9.0, G - 5.0
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M - 9.5, G - 1.4), (fx, fy)], 0.35)), vine)
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, fx + math.cos(a) * 1.3, fy - 0.6 + math.sin(a) * 1.0, 0.9) for a in np.linspace(0.0, 2.0 * math.pi, 6)[:-1]]), c["bloom"])
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, fx, fy - 0.6, 0.6)), _mix(c["bloom"], c["dark"], 0.3))
    tile.alpha *= tile.y < G


def shicra_bag(tile: Tile, c: dict) -> None:
    """A shicra: an open bag of twisted reed fibre, knotted in a wide mesh
    and full of stones. The builders of Caral filled the platforms of their
    pyramids with many thousands of them, each the load of one person. The
    stones show through the mesh, and the ends of the bag are tied in a
    knot at its top."""
    _shadow(tile, 8.0)
    bag = tile.mask(lambda p, dx, dy: (_dot(p, dx, dy, M, G - 5.6, 8.0, ry=5.6), _poly(p, dx, dy, [(M - 3.0, G - 10.0), (M + 3.0, G - 10.0), (M + 1.0, G - 13.0), (M - 1.0, G - 13.0)])))
    rng = tile.rng
    stones = [(M + rng.uniform(-6.4, 6.4), G - rng.uniform(1.6, 9.4), rng.uniform(1.3, 2.4), rng.uniform(-0.18, 0.16)) for _ in range(16)]
    tile.put(bag, c["dark"], 0.85)
    for x, y, r, tone in stones:
        stone = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(x - r, y), (x - r * 0.4, y - r * 0.8), (x + r * 0.6, y - r * 0.7), (x + r, y + r * 0.1), (x + r * 0.3, y + r * 0.8), (x - r * 0.7, y + r * 0.6)]))
        tile.put(stone * bag, _mix(c["stone"], c["stone_light"] if tone > 0 else c["dark"], abs(tone) * 2.0))
        tile.put(stone * bag * (tile.y < y - r * 0.3), c["stone_light"], 0.40)
    # The mesh: two sets of twisted cords that cross in diamonds.
    mesh = (np.abs(((tile.x + tile.y) % 3.2) - 1.6) < 0.22) | (np.abs(((tile.x - tile.y) % 3.2) - 1.6) < 0.22)
    tile.put(bag * mesh, c["wood"], 0.95)
    tile.put(bag * mesh * (np.abs(((tile.x * 2.0) % 1.0) - 0.5) < 0.18), _mix(c["wood"], c["dark"], 0.4), 0.6)
    tile.put(bag * (tile.x < M - 2.0) * (tile.y < G - 6.0), (255, 240, 210), 0.10)
    tile.put(bag * (tile.y > G - 2.0), c["dark"], 0.35)
    # The knot at the top and its loose ends.
    tile.put(tile.mask(lambda p, dx, dy: (_dot(p, dx, dy, M, G - 12.6, 1.4), _line(p, dx, dy, [(M, G - 13.4), (M - 2.0, G - 15.6)], 0.4), _line(p, dx, dy, [(M + 0.4, G - 13.4), (M + 2.6, G - 15.0)], 0.4))),
             c["wood"])
    tile.alpha *= tile.y < G


# Southeast Asia. In Wallacea `metal` is the skin of a ripe fig and
# `bloom` red ochre; on the Austronesian shore `metal` is a ripe banana and
# `bloom` the pink of a shell; on the Red River `bloom` is ripe rice and
# `wood` split bamboo.


def fern(tile: Tile, c: dict) -> None:
    """A fern of the rainforest floor: long fronds that arch up and out
    from one crown. Each frond has pairs of leaflets that get smaller to
    its tip."""
    _shadow(tile, 7.5)
    stem = _mix(c["plant"], c["dark"], 0.35)
    for k, (angle, length) in enumerate(((-62.0, 10.5), (-30.0, 14.0), (2.0, 16.0), (32.0, 13.5), (64.0, 10.0))):
        a = math.radians(angle)
        tip = (M + math.sin(a) * length, G - 1.0 - math.cos(a) * length * 0.95)
        bend = (M + math.sin(a) * length * 0.45, G - 1.0 - math.cos(a) * length * 0.75)
        pts = [(M + (1 - t) ** 2 * 0.0 + 2 * (1 - t) * t * (bend[0] - M) + t * t * (tip[0] - M) * 1.0, (1 - t) ** 2 * (G - 1.0) + 2 * (1 - t) * t * bend[1] + t * t * (tip[1] + length * 0.18)) for t in np.linspace(0.0, 1.0, 9)]
        colour = c["plant"] if k % 2 == 0 else _mix(c["plant"], c["dark"], 0.18)
        leaflets = []
        for j in range(1, 8):
            x0, y0 = pts[j]
            x1, y1 = pts[j + 1]
            size = 2.4 * (1.0 - j / 9.0) + 0.5
            nx, ny = -(y1 - y0), x1 - x0
            n = math.hypot(nx, ny) or 1.0
            nx, ny = nx / n, ny / n
            for side in (-1.0, 1.0):
                leaflets.append([(x0, y0), (x1, y1), (x0 + nx * side * size + (x1 - x0) * 0.6, y0 + ny * side * size + (y1 - y0) * 0.6)])
        tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, q) for q in leaflets]), colour)
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, pts, 0.3)), stem, 0.8)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, G - 0.8, 1.8, ry=1.0)), c["dark"], 0.6)
    tile.alpha *= tile.y < G


def fallen_fruit(tile: Tile, c: dict) -> None:
    """Ripe figs that fell from a fig tree of the forest, on one dead
    leaf: round fruits with a light on top, and one fruit split open to
    show its pale flesh full of seeds. Birds, bats and people of the
    forest eat them."""
    _shadow(tile, 8.5)
    leaf = [(M - 9.0, G - 0.4), (M - 4.0, G - 3.0), (M + 3.0, G - 2.6), (M + 8.0, G - 0.6), (M + 2.0, G), (M - 5.0, G)]
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, leaf)), _mix(c["wood"], c["plant"], 0.25))
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M - 9.0, G - 0.4), (M + 8.0, G - 0.6)], 0.2)), c["dark"], 0.5)
    for x, r in ((-4.6, 2.6), (0.6, 3.0), (-1.8, 2.2)):
        up = 1.6 if x == -1.8 else 0.0
        fruit = tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + x, G - r * 0.95 - up, r, ry=r * 0.92))
        tile.put(fruit, c["metal"])
        tile.put(fruit * (tile.y > G - r * 0.6 - up), c["dark"], 0.30)
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + x - r * 0.35, G - r * 1.35 - up, r * 0.35, ry=r * 0.25)), (255, 236, 220), 0.45)
    # The fruit that is split open: red rind, pale flesh, dark seeds.
    sx = M + 5.6
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, sx, G - 2.2, 2.8, ry=2.2)), c["metal"])
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, sx - 0.2, G - 2.5, 2.1, ry=1.5)), (232, 196, 170))
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, sx - 0.2, G - 2.5, 1.3, ry=0.9)), _mix(c["bloom"], (232, 196, 170), 0.5))
    seeds = [(sx - 1.0, G - 2.8), (sx + 0.4, G - 2.2), (sx - 0.4, G - 3.0), (sx + 0.8, G - 2.9), (sx - 1.2, G - 2.1)]
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, 0.22) for x, y in seeds]), c["dark"], 0.8)
    tile.alpha *= tile.y < G


def ochre_lump(tile: Tile, c: dict) -> None:
    """A lump of red ochre, the paint of the oldest pictures in the caves.
    One face of it is ground flat and smooth on a stone, so it is lighter
    and has fine scratches. Red powder lies on the ground round it, and a
    small chip lies next to it."""
    _shadow(tile, 7.0)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + 0.5, G - 0.3, 8.0, ry=1.1), blur=0.5), c["bloom"], 0.45)
    lump = [(M - 5.6, G), (M - 6.0, G - 3.0), (M - 3.4, G - 6.6), (M + 0.6, G - 7.8), (M + 4.4, G - 5.6), (M + 5.6, G - 2.0), (M + 4.8, G)]
    body = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, lump))
    tile.put(body, c["bloom"])
    face = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 3.4, G - 6.6), (M + 0.6, G - 7.8), (M + 4.4, G - 5.6), (M + 1.0, G - 3.6), (M - 2.4, G - 4.0)]))
    tile.put(face, _mix(c["bloom"], (255, 210, 180), 0.30))
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(M - 2.4 + k * 1.2, G - 4.4 - k * 0.3), (M - 0.6 + k * 1.2, G - 6.8 - k * 0.2)], 0.15) for k in range(4)]) * face, _mix(c["bloom"], c["dark"], 0.3), 0.6)
    tile.put(body * (tile.y > G - 2.4), _mix(c["bloom"], c["dark"], 0.45), 0.6)
    chip = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M + 6.6, G), (M + 7.2, G - 1.8), (M + 8.8, G - 1.4), (M + 9.0, G)]))
    tile.put(chip, _mix(c["bloom"], c["dark"], 0.2))
    tile.alpha *= tile.y < G


def banana_plant(tile: Tile, c: dict) -> None:
    """A young banana plant of an island garden: a thick soft stem of
    leaf sheaths, a few long broad leaves that arch out (the wind tears
    them along their ribs), and a hanging bunch of fruit with a dark red
    bud at its end. The Austronesians carried bananas, taro and yams from
    island to island in their canoes."""
    _shadow(tile, 6.5)
    stem = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 2.0, G), (M + 2.0, G), (M + 1.3, G - 13.0), (M - 1.3, G - 13.0)]))
    tile.put(stem, _mix(c["plant"], (190, 190, 120), 0.35))
    tile.put(stem * (tile.x > M + 0.4), c["dark"], 0.25)
    for side, lift, length in ((-1.0, 13.0, 10.5), (1.0, 14.5, 10.5), (-1.0, 17.5, 7.0), (1.0, 18.5, 6.0)):
        base = (M, G - lift)
        tip = (M + side * length, G - lift + 2.6 - (0.0 if lift < 15 else 2.0))
        ctrl = (M + side * length * 0.5, G - lift - 3.6)
        rib = [((1 - t) ** 2 * base[0] + 2 * (1 - t) * t * ctrl[0] + t * t * tip[0], (1 - t) ** 2 * base[1] + 2 * (1 - t) * t * ctrl[1] + t * t * tip[1]) for t in np.linspace(0.0, 1.0, 9)]
        width = [0.0, 1.6, 2.1, 2.3, 2.3, 2.1, 1.7, 1.1, 0.0]
        upper = [(x, y - w) for (x, y), w in zip(rib, width)]
        lower = [(x, y + w * 0.9) for (x, y), w in zip(rib, width)]
        leaf = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, upper + lower[::-1]))
        tile.put(leaf, c["plant"])
        tile.put(leaf * tile.mask(lambda p, dx, dy: _poly(p, dx, dy, rib + lower[::-1])), c["dark"], 0.22)
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, rib, 0.25)), _mix(c["plant"], (240, 240, 190), 0.45), 0.8)
        tears = [(rib[j][0], rib[j][1] + width[j] * 0.9) for j in (3, 5)]
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x, y - 0.8), (x + side * 0.4, y + 0.1)], 0.3) for x, y in tears]), (0, 0, 0), 0.6)
    # The bunch: rows of short curved fruits that point up, on a stalk
    # that hangs down, and the bud at its end.
    sx, sy = M + 3.0, G - 12.0
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M + 1.0, G - 14.0), (sx, sy), (sx + 0.4, sy + 7.0)], 0.35)), _mix(c["plant"], c["dark"], 0.4))
    hands = [(sx + 0.2 + ox, sy + 1.2 + row * 1.6) for row in range(3) for ox in (-1.2, 0.0, 1.2)]
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, 0.6, ry=0.95) for x, y in hands]), _mix(c["plant"], c["metal"], 0.35))
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x - 0.2, y - 0.3, 0.25, ry=0.4) for x, y in hands]), (240, 240, 190), 0.5)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, sx + 0.4, sy + 7.6, 0.9, ry=1.5)), (130, 40, 56))
    tile.alpha *= tile.y < G


def rice_sheaf(tile: Tile, c: dict) -> None:
    """A sheaf of rice at the harvest: the stalks are tied with a band of
    straw, they spread at the foot so the sheaf stands, and the heavy
    heads of grain hang over at the top in golden arcs."""
    _shadow(tile, 5.5)
    straw = _mix(c["bloom"], c["dark"], 0.30)
    stalks, heads = [], []
    for k in range(9):
        t = (k - 4) / 4.0
        top = (M + t * 3.2, G - 14.5 + abs(t) * 1.6)
        stalks.append([(M + t * 4.0, G), (M + t * 0.8, G - 7.0), top])
        side = 1.0 if t >= 0.0 else -1.0
        if abs(t) < 0.05:
            side = 1.0 if k % 2 else -1.0
        heads.append([top, (top[0] + side * 2.2, top[1] - 1.2), (top[0] + side * 3.6, top[1] + 1.4), (top[0] + side * 3.8, top[1] + 4.0)])
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, pts, 0.5) for pts in stalks]), straw)
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, pts, 0.35) for pts in heads]), _mix(c["bloom"], c["dark"], 0.15))
    grains = [(x, y) for pts in heads for x, y in pts[1:]]
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, 0.5, ry=0.8) for x, y in grains]), c["bloom"])
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x - 0.15, y - 0.25, 0.22, ry=0.35) for x, y in grains]), (255, 244, 200), 0.6)
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 1.8, G - 8.0, M + 1.8, G - 6.4)), _mix(straw, c["dark"], 0.35))
    tile.alpha *= tile.y < G


def rice_basket(tile: Tile, c: dict) -> None:
    """A round basket of woven split bamboo, wide at its middle and
    narrow at its mouth, full of grains of rice, and a flat winnowing tray
    of the same weave that leans on it."""
    _shadow(tile, 8.5)
    tray = tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + 5.0, G - 6.0, 3.2, ry=6.0))
    tile.put(tray, _mix(c["wood"], c["dark"], 0.20))
    tile.put(tray * (np.abs(((tile.x * 0.8 + tile.y) % 1.4) - 0.7) < 0.18), c["dark"], 0.28)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + 5.0, G - 6.0, 3.2, ry=6.0)) * (1.0 - tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + 5.0, G - 6.0, 2.5, ry=5.3))), c["wood_light"], 0.6)
    body = tile.mask(lambda p, dx, dy: (_dot(p, dx, dy, M - 2.0, G - 4.6, 6.0, ry=4.6), _box(p, dx, dy, M - 6.0, G - 4.6, M + 2.0, G - 0.6), _poly(p, dx, dy, [(M - 6.2, G - 6.0), (M + 2.2, G - 6.0), (M + 1.0, G - 10.0), (M - 5.0, G - 10.0)])))
    tile.put(body, c["wood"])
    weave = ((np.abs(((tile.x + tile.y) % 1.6) - 0.8) < 0.22) | (np.abs(((tile.x - tile.y) % 1.6) - 0.8) < 0.22)).astype(np.float32)
    tile.put(body * weave, c["dark"], 0.28)
    tile.put(body * (tile.x < M - 4.0), c["wood_light"], 0.30)
    tile.put(body * (tile.x > M + 0.8), c["dark"], 0.30)
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 5.4, G - 10.6, M + 1.4, G - 9.4)), c["wood_light"])
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M - 2.0, G - 10.6, 3.0, ry=1.1)), c["bloom"])
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M - 2.6, G - 10.9, 1.4, ry=0.45)), (255, 248, 220), 0.5)
    tile.alpha *= tile.y < G


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
    # The Art dimension: what a painter leaves on the ground; on the pages,
    # what a person who draws leaves; in the caves, ink and crystals.
    "art": ((paint_pots, brush_jar, crayon_stubs, bush, paint_pots, crayon_stubs), _palette((38, 26, 66), (120, 100, 160), (232, 226, 240), (176, 130, 84), (150, 148, 172), (40, 200, 236), (232, 54, 172), (255, 210, 50))),
    "art_sketchbook": ((crumpled_paper, pencil_cup, crayon_stubs, crumpled_paper, rock, pencil_cup), _palette((92, 94, 110), (190, 180, 160), (246, 241, 228), (226, 196, 140), (160, 160, 172), (40, 200, 236), (236, 82, 170), (240, 200, 70))),
    "art_inkfall": ((ink_bottle, crystal, rock, mushrooms, ink_bottle, crystal), _palette((14, 8, 34), (58, 38, 102), (226, 214, 240), (96, 64, 160), (70, 50, 120), (60, 220, 250), (246, 70, 200), (255, 170, 236))),
    # The four quarters: the things a writer leaves, a musician, an actor
    # and a maker.
    "art_stacks": ((book_pile, candle_stub, loose_pages, ink_bottle, book_pile, candle_stub), _palette((40, 24, 20), (196, 180, 150), (240, 226, 192), (124, 66, 42), (150, 126, 90), (54, 94, 72), (128, 40, 50), (255, 200, 110))),
    "art_resonance": ((metronome, tuning_fork, hand_bells, sheet_music, tuning_fork, hand_bells), _palette((12, 12, 22), (150, 150, 170), (236, 228, 206), (70, 44, 34), (214, 170, 80), (60, 120, 110), (180, 40, 60), (80, 230, 255))),
    "art_stage": ((footlight, roses, prop_crown, stage_masks, footlight, roses), _palette((24, 14, 18), (120, 100, 110), (236, 226, 214), (110, 70, 62), (220, 170, 70), (60, 110, 60), (190, 30, 50), (255, 220, 150))),
    "art_forge": ((clay_pots, thread_spools, gear_wheel, blueprint_rolls, anvil, coal), _palette((30, 14, 10), (110, 76, 60), (196, 150, 120), (176, 92, 60), (196, 150, 72), (60, 176, 206), (222, 62, 84), (255, 140, 50))),
    # The History dimension: what each era leaves on the ground. The
    # Crescent: wheat, pots, tablets, a basket and reeds; the Nile: papyrus,
    # a cat of stone, canopic jars, lotus and an obelisk; the Classical
    # Shore: amphorae, a bust, a drum of a column and laurel; the Silk Road:
    # spice, silk, a lantern and tea; the steppe: an ovoo, a saddle, a pail,
    # a skull and grass; the Monsoon Coast: salt, gold, manuscripts, coir rope
    # and shells; the Age of Sail: a barrel, crops of the new world, an
    # anchor, rope and a bollard; the Industrial Age: coal, gears, cotton, an
    # oil can and a gas lamp.
    "history_crescent": ((wheat_sheaf, clay_pots, clay_tablets, reeds, grain_basket, wheat_sheaf), _palette((60, 40, 30), (150, 120, 96), (220, 196, 160), (184, 128, 82), (140, 132, 120), (110, 130, 70), (52, 84, 164), (232, 190, 100))),
    "history_nile": ((papyrus_clump, cat_statue, canopic_jars, lotus, papyrus_clump, obelisk), _palette((50, 34, 24), (196, 160, 110), (236, 214, 170), (150, 110, 70), (226, 180, 70), (80, 130, 70), (90, 120, 210), (255, 214, 120))),
    "history_classical": ((standing_amphora, bust, fallen_drum, bush, column_stub, standing_amphora), _palette((40, 40, 46), (190, 186, 178), (240, 236, 228), (186, 88, 56), (52, 46, 44), (104, 124, 76), (180, 60, 50), (255, 240, 200))),
    "history_silk": ((spice_sacks, silk_rolls, paper_lantern, tea_bricks, spice_sacks, paper_lantern), _palette((60, 36, 26), (196, 160, 112), (236, 214, 172), (130, 80, 50), (204, 162, 72), (60, 150, 120), (178, 40, 40), (255, 190, 90))),
    "history_steppe": ((ovoo_cairn, saddle, grass_tuft, milk_pail, horse_skull, grass_tuft), _palette((36, 40, 24), (150, 150, 140), (226, 222, 210), (130, 90, 56), (196, 196, 206), (130, 160, 70), (170, 52, 40), (70, 126, 206))),
    "history_monsoon": ((salt_slabs, gold_bowl, manuscripts, rope_coil, shells, salt_slabs), _palette((50, 36, 26), (176, 168, 156), (240, 236, 226), (124, 82, 50), (236, 186, 60), (80, 120, 80), (196, 90, 60), (255, 210, 100))),
    "history_sail": ((barrel, crop_crate, anchor, rope_coil, crop_crate, bollard), _palette((30, 30, 28), (120, 120, 116), (196, 190, 176), (122, 90, 60), (70, 72, 78), (90, 120, 60), (190, 50, 40), (255, 210, 140))),
    "history_industrial": ((coal, gear_wheel, cotton_spools, oil_can, lamp_post, coal), _palette((24, 22, 24), (110, 106, 104), (196, 192, 186), (140, 100, 60), (110, 112, 120), (80, 90, 60), (160, 50, 40), (255, 200, 110))),
    # The History dimension, second pass: what each place leaves on the
    # ground. The Rift Valley: a hand axe, a termite mound, a hearth and
    # bones; the Green Sahara: reeds, pots, a skull of a cow and a fish trap;
    # the Ice Age: tusks, bones and a hearth; the downs: a standing stone, a
    # grinding stone and beakers; the north: a round shield, a stone and a
    # barrel; the Indus: a seal, a toy cart, bricks and jars; the Yellow
    # River: millet and painted jars; the first maize: cobs, an agave and a
    # grinding stone; Sahul: a hearth, shells, a grinding stone and a termite
    # mound; the highlands: taro and a stone adze; the painted cave: lamps of
    # stone, the paints, and a hearth.
    "history_savanna": ((grass_tuft, hand_axe, termite_mound, hearth, bones, grass_tuft), _palette((50, 34, 24), (150, 124, 100), (216, 196, 166), (176, 92, 54), (110, 104, 96), (150, 150, 70), (190, 80, 50), (255, 180, 90))),
    "history_green_sahara": ((reeds, clay_pots, cow_skull, fish_basket, grass_tuft, flowers), _palette((46, 40, 26), (176, 140, 100), (232, 220, 196), (170, 110, 70), (90, 90, 90), (110, 150, 70), (220, 200, 90), (255, 210, 140))),
    "history_ice_age": ((tusk, bones, hearth, rock, grass_tuft, tusk), _palette((30, 36, 54), (130, 136, 150), (236, 230, 214), (110, 82, 60), (90, 90, 100), (130, 120, 80), (170, 90, 70), (255, 190, 110))),
    "history_megalith": ((standing_stone, flowers, quern, clay_pots, bush, grass_tuft), _palette((34, 40, 30), (150, 150, 142), (220, 218, 208), (170, 110, 70), (90, 90, 96), (110, 140, 70), (230, 220, 120), (230, 200, 120))),
    "history_northwoods": ((round_shield, grass_tuft, standing_stone, barrel, rock, bush), _palette((24, 30, 30), (110, 116, 118), (200, 204, 200), (120, 84, 56), (150, 150, 156), (70, 100, 64), (170, 50, 40), (255, 210, 150))),
    "history_indus": ((clay_pots, indus_seal, toy_cart, brick_stack, grass_tuft, clay_pots), _palette((56, 30, 22), (170, 150, 130), (232, 222, 204), (180, 90, 56), (120, 110, 96), (110, 130, 70), (60, 60, 60), (255, 200, 140))),
    "history_yellow_river": ((wheat_sheaf, painted_jar, grain_basket, grass_tuft, painted_jar, wheat_sheaf), _palette((50, 40, 28), (160, 140, 110), (230, 214, 180), (178, 96, 60), (90, 90, 80), (130, 140, 70), (40, 30, 26), (226, 190, 90))),
    "history_maize": ((maize_cobs, agave_plant, quern, clay_pots, grass_tuft, agave_plant), _palette((40, 36, 28), (110, 100, 92), (210, 200, 186), (176, 110, 70), (80, 80, 80), (100, 140, 80), (170, 50, 60), (240, 200, 80))),
    "history_sahul": ((grass_tuft, hearth, shells, quern, rock, termite_mound), _palette((50, 24, 18), (150, 100, 80), (230, 210, 190), (176, 86, 50), (110, 100, 96), (160, 160, 100), (200, 90, 50), (255, 170, 80))),
    "history_highlands": ((taro, stone_adze, bush, flowers, taro, grass_tuft), _palette((20, 34, 24), (96, 104, 96), (190, 196, 180), (110, 80, 56), (60, 110, 90), (80, 140, 70), (200, 80, 80), (255, 210, 150))),
    "history_painted_cave": ((stone_lamp, ochre_palette, bones, rock, hearth, stone_lamp), _palette((30, 18, 14), (120, 92, 70), (210, 180, 150), (110, 76, 50), (90, 80, 70), (90, 90, 60), (170, 60, 36), (255, 180, 90))),
    # The History dimension, third pass. The Olmec heartland: cattails,
    # cacao, a rubber ball by its latex, jade celts and a grinding stone; the
    # Maya city: glyph blocks, a painted vase and a burner of copal; the
    # Taino islands: conchs, cassava, shells and pots; the Lapita shore:
    # stamped sherds, obsidian, taro, shells and coral; the open ocean (on a
    # canoe deck): coconuts, a water gourd, rope and the catch; Rapa Nui: a
    # toki, obsidian, a stone of a house and the grass.
    "history_olmec": ((reeds, cacao_pod, rubber_ball, jade_celts, quern, grass_tuft), _palette((34, 40, 26), (84, 84, 86), (176, 176, 166), (180, 124, 84), (70, 150, 110), (90, 130, 70), (200, 110, 50), (255, 220, 160))),
    "history_maya": ((bush, glyph_block, cylinder_vase, copal_burner, flowers, glyph_block), _palette((24, 36, 28), (196, 186, 166), (236, 230, 214), (176, 64, 46), (60, 140, 120), (60, 120, 70), (220, 80, 60), (255, 210, 150))),
    "history_caribbean": ((conch, cassava_plant, shells, clay_pots, grass_tuft, conch), _palette((30, 40, 36), (200, 190, 170), (244, 236, 214), (170, 110, 70), (210, 170, 60), (70, 140, 80), (236, 140, 140), (255, 236, 190))),
    "history_lapita": ((shells, lapita_sherd, taro, obsidian, coral, grass_tuft), _palette((30, 26, 24), (100, 94, 90), (220, 210, 196), (176, 96, 60), (30, 30, 36), (80, 130, 70), (240, 150, 130), (255, 210, 150))),
    "history_open_ocean": ((rope_coil, coconuts, water_gourd, fish_basket, coconuts, rope_coil), _palette((14, 22, 36), (96, 100, 112), (204, 206, 210), (156, 116, 70), (120, 110, 90), (110, 128, 60), (230, 170, 110), (255, 190, 130))),
    "history_rapa_nui": ((grass_tuft, stone_adze, obsidian, rock, paenga, grass_tuft), _palette((30, 34, 26), (110, 104, 96), (200, 190, 170), (130, 96, 60), (66, 68, 72), (130, 150, 70), (214, 150, 60), (255, 230, 180))),
    # The Atlantic world. Benin City: clay pots, yams, a heap of cowries,
    # kola nuts in a bowl, a small brass bell, and grass.
    "history_benin": ((clay_pots, yams, cowries, kola_nuts, brass_bell, grass_tuft), _palette((44, 24, 16), (150, 90, 64), (246, 240, 224), (170, 92, 58), (226, 176, 72), (110, 140, 64), (176, 54, 44), (255, 214, 150))),
    # Saint-Domingue: a joumou squash, a coffee bush with red cherries,
    # cuttings of cane, pots, a gourd and grass.
    "history_saint_domingue": ((joumou, coffee_bush, cane_cuttings, clay_pots, water_gourd, grass_tuft),
                               _palette((40, 26, 18), (150, 120, 96), (236, 226, 204), (176, 110, 64), (226, 128, 44), (88, 128, 56), (196, 40, 36), (255, 214, 150))),
    # The Gold Coast: a fishing net drying with its floats, a coil of rope,
    # stones and shells of the beach, and a rock.
    "history_gold_coast": ((fishing_net, rope_coil, beach_stones, sea_shells, fishing_net, rock),
                           _palette((52, 50, 48), (150, 148, 140), (226, 222, 210), (176, 150, 104), (204, 128, 76), (110, 124, 96), (210, 166, 148), (255, 244, 220))),
    # South America. The high Andes: a heap of potatoes of many kinds, a
    # tussock of ichu, a quinoa plant with red and gold heads, and stones.
    # Caral: a cotton plant with open bolls, a squash on its vine, a bag of
    # stones (a shicra) and a stone.
    "history_andes": ((potatoes, ichu_tussock, quinoa_plant, rock, potatoes, ichu_tussock),
                      _palette((40, 34, 30), (124, 116, 106), (214, 206, 190), (150, 110, 70), (216, 166, 64), (198, 164, 98), (176, 60, 52), (255, 210, 150))),
    "history_supe": ((cotton_plant, squash_vine, shicra_bag, rock, cotton_plant, shicra_bag),
                     _palette((50, 40, 30), (164, 150, 126), (226, 216, 194), (170, 140, 92), (206, 136, 58), (84, 118, 58), (236, 196, 64), (255, 226, 170))),
    # Southeast Asia. Wallacea: ferns, fallen figs, a lump of red ochre and
    # stones under the karst. The Austronesian islands: a banana plant,
    # taro, coconuts and shells. The Red River: sheaves of rice, reeds and
    # a basket of rice.
    "history_wallacea": ((fern, fallen_fruit, ochre_lump, rock, fern, beach_stones),
                         _palette((30, 36, 28), (156, 156, 148), (222, 220, 210), (122, 92, 60), (138, 58, 76), (66, 118, 60), (170, 64, 42), (255, 236, 180))),
    "history_austronesia": ((banana_plant, taro, coconuts, sea_shells, banana_plant, taro),
                            _palette((32, 28, 26), (112, 106, 100), (234, 224, 206), (124, 88, 58), (226, 196, 84), (86, 142, 62), (226, 128, 108), (255, 226, 170))),
    "history_red_river": ((rice_sheaf, reeds, rice_basket, rice_sheaf, reeds, rice_basket),
                          _palette((46, 38, 30), (134, 124, 106), (220, 212, 190), (184, 160, 100), (92, 92, 80), (104, 146, 68), (230, 192, 96), (240, 206, 120))),
    "cave": ((crystal, mushrooms, rock, mushrooms, crystal, rock), _palette((16, 15, 36), (54, 52, 98), (100, 100, 160), (80, 66, 90), (60, 60, 100), (60, 130, 130), (236, 130, 232), (124, 222, 255))),
    "cove": ((barrel, crate, coil, shells, reeds, lamp_post), _palette((12, 30, 40), (60, 96, 104), (120, 164, 164), (122, 88, 58), (70, 84, 92), (70, 140, 110), (236, 130, 120), (255, 200, 120))),
    "water": ((coral, amphora, column_stub, shells, coral, rock), _palette((8, 34, 52), (40, 96, 114), (96, 164, 172), (150, 110, 80), (50, 100, 116), (50, 150, 120), (255, 132, 126), (150, 240, 200))),
    "starlight": ((star_post, flowers, bush, grass_tuft, mushrooms, flowers), _palette((96, 70, 130), (206, 170, 214), (255, 232, 244), (190, 130, 150), (232, 196, 226), (120, 204, 170), (255, 130, 176), (255, 240, 170))),
    "stardune": ((star_post, amphora, rock, grass_tuft, obelisk, shells), _palette((124, 70, 70), (226, 170, 124), (255, 226, 176), (176, 112, 76), (232, 196, 150), (112, 176, 132), (255, 150, 130), (255, 244, 180))),
    "starless": ((crystal, brazier, rock, mushrooms, crystal, obelisk), _palette((12, 8, 28), (58, 46, 104), (120, 100, 180), (70, 44, 80), (52, 40, 92), (120, 60, 130), (255, 100, 180), (255, 120, 196))),
    # The void: black things with a grey edge, and no colour.
    "void": ((void_obelisk, void_shards, broken_column, fallen_star, void_shards, void_obelisk), _palette((4, 4, 5), (8, 8, 9), (150, 150, 152), (4, 4, 5), (4, 4, 5), (4, 4, 5), (150, 150, 152), (200, 200, 200))),
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
    # The military tower: boxes of ammunition, sandbags, cans of fuel, a
    # drum and a fire extinguisher. `wood` is olive paint, `stone_light`
    # khaki and `bloom` the red of an extinguisher.
    "military_tower": ((ammo_crate, sandbags, jerrycan, oil_drum, extinguisher, ammo_stack), _palette((20, 22, 18), (110, 108, 98), (183, 167, 122), (84, 90, 52), (74, 82, 88), (91, 97, 54), (150, 52, 42), (255, 198, 124))),
    "skybridge": ((bush, flowers, column_stub, grass_tuft, planter, flowers), _palette((86, 100, 142), (160, 172, 204), (224, 230, 244), (150, 120, 90), (130, 144, 180), (106, 176, 96), (255, 150, 170), (255, 236, 150))),
    "open_sky": ((grass_tuft, rock, flowers, bush, grass_tuft, rock), _palette((104, 92, 92), (176, 164, 150), (232, 222, 204), (150, 112, 74), (140, 136, 140), (116, 178, 90), (255, 190, 110), (255, 240, 170))),
    # Eureka, the institute town: benches, a telescope, a bike rack, a
    # notice board, flowers and tufts of the lawn. `wood` is the benches'
    # slats, `glow` a telescope's lens and `bloom` a bicycle's paint.
    "eureka": ((campus_bench, flowers, telescope, bike_rack, grass_tuft, notice_board), _palette((40, 46, 40), (204, 190, 160), (240, 232, 214), (120, 84, 56), (64, 72, 82), (92, 150, 72), (196, 60, 52), (190, 226, 246))),
    # High on the space elevator: the car's deck lights, consoles and freight.
    "eureka_heights": ((floor_light, console, floor_light, crate, coil, floor_light), _palette((10, 14, 28), (64, 76, 96), (132, 150, 172), (90, 76, 60), (70, 84, 104), (70, 140, 110), (255, 120, 92), (150, 210, 255))),
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
    ink_bottle: (M, 3.4, 0.22),
    candle_stub: (M, 10.6, 0.34),
    tuning_fork: (M, 15.0, 0.14),
    footlight: (M + 1.4, 3.4, 0.30),
    paper_lantern: (M + 1.4, 13.2, 0.34),
    gold_bowl: (M, 6.0, 0.16),
    hearth: (M, 5.0, 0.38),
    stone_lamp: (M - 1.0, 6.0, 0.32),
    copal_burner: (M, 8.0, 0.30),
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
