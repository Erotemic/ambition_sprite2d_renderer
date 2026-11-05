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


# The age of the temples and the trade. At the Strait `stone` is matting
# and `metal` the glaze of a jar; at Borobudur `stone` is andesite and
# `bloom` a lotus; at Angkor `stone` is sandstone and `metal` laterite.


def trade_jar(tile: Tile, c: dict) -> None:
    """A big storage jar of glazed stoneware from China, of the kind that
    ships brought to the port to hold oil, wine and goods: a wide shoulder,
    a short neck with a rolled rim, and small lugs on the shoulder for a
    cord. The glaze runs down unevenly and stops above the foot, so a band
    of bare clay shows at the foot."""
    _shadow(tile, 6.5)
    body = tile.mask(lambda p, dx, dy: (_dot(p, dx, dy, M, G - 9.5, 6.0, ry=7.0), _poly(p, dx, dy, [(M - 4.4, G - 4.0), (M + 4.4, G - 4.0), (M + 3.2, G), (M - 3.2, G)])))
    tile.put(body, _mix(c["stone_light"], c["wood"], 0.35))
    drip = G - 3.0 + np.sin(tile.x * 1.7) * 0.6 + np.sin(tile.x * 0.7 + 1.0) * 0.4
    glaze = body * (tile.y < drip)
    tile.put(glaze, c["metal"])
    tile.put(glaze * (tile.x < M - 2.0), _mix(c["metal"], (255, 240, 200), 0.25), 0.6)
    tile.put(glaze * (tile.x > M + 2.6), c["dark"], 0.35)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M - 2.6, G - 12.6, 1.2, ry=2.2)), (255, 248, 226), 0.35)
    neck = tile.mask(lambda p, dx, dy: (_box(p, dx, dy, M - 2.2, G - 18.0, M + 2.2, G - 15.4), _dot(p, dx, dy, M, G - 18.2, 2.9, ry=0.9)))
    tile.put(neck, c["metal"])
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, G - 18.3, 1.9, ry=0.5)), c["dark"], 0.8)
    for x in (-4.6, 4.6):
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + x, G - 14.0, 1.0, ry=0.7)), _mix(c["metal"], c["dark"], 0.3))
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M - 5.6, G - 11.0), (M + 5.6, G - 11.0)], 0.3)), c["dark"], 0.35)
    tile.alpha *= tile.y < G


def pepper_sacks(tile: Tile, c: dict) -> None:
    """Two sacks of woven matting full of black pepper, the spice that
    came to the port from the hills: one is tied shut, and the mouth of
    the other is rolled down to show a heap of dark corns. A few corns lie
    spilled on the ground."""
    _shadow(tile, 9.0)
    for x, w, h, open_ in ((-4.4, 4.0, 11.0, False), (3.6, 4.4, 9.0, True)):
        sack = tile.mask(lambda p, dx, dy: (_dot(p, dx, dy, M + x, G - h * 0.42, w, ry=h * 0.44), _box(p, dx, dy, M + x - w, G - h * 0.45, M + x + w, G - 0.6), _box(p, dx, dy, M + x - w * 0.85, G - h, M + x + w * 0.85, G - h * 0.5)))
        tile.put(sack, c["stone"])
        weave = ((np.floor(tile.x / 0.9) + np.floor(tile.y / 0.9)) % 2 == 0).astype(np.float32)
        tile.put(sack * weave, c["dark"], 0.10)
        tile.put(sack * (tile.x < M + x - w * 0.45), c["stone_light"], 0.35)
        tile.put(sack * (tile.x > M + x + w * 0.45), c["dark"], 0.30)
        if open_:
            tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M + x - w * 0.95, G - h - 0.2, M + x + w * 0.95, G - h + 1.6)), _mix(c["stone"], c["dark"], 0.25))
            heap = tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + x, G - h - 0.2, w * 0.85, ry=1.8))
            tile.put(heap * (tile.y < G - h + 0.4), c["bloom"])
            corns = [(M + x + k * 0.9 - 2.8, G - h - 0.6 - (k % 3) * 0.4) for k in range(7)]
            tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, cx, cy, 0.35) for cx, cy in corns]), _mix(c["bloom"], (255, 240, 220), 0.35), 0.8)
        else:
            tile.put(tile.mask(lambda p, dx, dy: (_poly(p, dx, dy, [(M + x - 1.4, G - h), (M + x + 1.4, G - h), (M + x + 2.2, G - h - 2.0), (M + x - 2.2, G - h - 2.0)]),)), c["stone"])
            tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M + x - 1.8, G - h - 0.6, M + x + 1.8, G - h + 0.4)), c["wood"])
    spilled = [(M + 0.6, G - 0.4), (M + 9.2, G - 0.4), (M + 8.4, G - 0.6), (M - 9.4, G - 0.4)]
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, 0.4) for x, y in spilled]), c["bloom"])
    tile.alpha *= tile.y < G


def mooring_post(tile: Tile, c: dict) -> None:
    """A post of hard wood driven into the bank, its top worn round, with
    turns of rope of palm fibre on it and the rope that goes off along the
    ground to a boat."""
    _shadow(tile, 4.0)
    post = tile.mask(lambda p, dx, dy: (_box(p, dx, dy, M - 2.2, G - 17.0, M + 2.2, G), _dot(p, dx, dy, M, G - 17.0, 2.2, ry=1.2)))
    tile.put(post, c["wood"])
    tile.put(post * (tile.x < M - 0.8), c["wood_light"], 0.45)
    tile.put(post * (tile.x > M + 1.0), c["dark"], 0.45)
    tile.put(post * np.clip((tile.noise(2, 10, 2) - 0.5) * 3.0, 0.0, 1.0), c["dark"], 0.25)
    tile.put(post * (tile.y > G - 4.0), _mix(c["wood"], (90, 76, 58), 0.6), 0.6)
    rope = (196, 168, 112)
    turns = tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(M - 2.5, G - 11.0 + k * 1.1), (M + 2.5, G - 10.4 + k * 1.1)], 0.6) for k in range(4)])
    tile.put(turns, rope)
    tile.put(turns * (tile.x > M + 1.0), c["dark"], 0.35)
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M + 2.4, G - 8.2), (M + 5.0, G - 4.0), (M + 7.4, G - 1.2), (M + 9.4, G - 0.5)], 0.55)), rope)
    tile.alpha *= tile.y < G


def moss_stone(tile: Tile, c: dict) -> None:
    """A round stone of andesite under a thick cushion of moss, with the
    small stalks of the moss standing up from it and a fern that sprouts
    beside it, as the wet morning air keeps everything green."""
    _shadow(tile, 7.5)
    stone = tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, G - 4.4, 7.0, ry=4.6))
    tile.put(stone * (tile.y < G), c["stone"])
    tile.put(stone * (tile.x < M - 3.0), c["stone_light"], 0.30)
    moss = tile.mask(lambda p, dx, dy: (_dot(p, dx, dy, M - 0.6, G - 6.6, 6.2, ry=2.8), _dot(p, dx, dy, M + 3.4, G - 5.6, 3.6, ry=2.2), _dot(p, dx, dy, M - 4.6, G - 4.6, 2.6, ry=2.0)))
    tile.put(moss * stone, c["plant"])
    tile.put(moss * stone * np.clip((tile.noise(10, 10, 2) - 0.45) * 4.0, 0.0, 1.0), _mix(c["plant"], (210, 230, 150), 0.35), 0.6)
    tile.put(moss * stone * (tile.y > G - 5.4), c["dark"], 0.25)
    stalks = [(M + x, G - 8.6 - abs(x) * 0.15) for x in (-4.0, -2.4, -0.6, 1.0, 2.6, 4.2)]
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x, y + 1.2), (x + 0.3, y - 1.4)], 0.2) for x, y in stalks]), _mix(c["plant"], c["wood"], 0.5))
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x + 0.3, y - 1.5, 0.35, ry=0.5) for x, y in stalks]), c["wood"])
    for k, (angle, length) in enumerate(((-30.0, 6.0), (0.0, 7.4), (28.0, 5.6))):
        a = math.radians(angle)
        base = (M + 7.4, G - 0.6)
        tip = (base[0] + math.sin(a) * length * 0.5, base[1] - math.cos(a) * length)
        rib = [(base[0] + (tip[0] - base[0]) * t, base[1] + (tip[1] - base[1]) * t + 1.2 * t * t) for t in np.linspace(0.0, 1.0, 7)]
        leaves = [[(x, y), (x + 1.0 * (1 - j / 7), y - 0.4), (x + 0.2, y + 0.4)] for j, (x, y) in enumerate(rib[1:])] + [[(x, y), (x - 1.0 * (1 - j / 7), y - 0.4), (x - 0.2, y + 0.4)] for j, (x, y) in enumerate(rib[1:])]
        tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, q) for q in leaves]), _mix(c["plant"], c["dark"], 0.1 * k))
    tile.alpha *= tile.y < G


def lotus_basin(tile: Tile, c: dict) -> None:
    """A basin of andesite with a moulded rim that holds water, with lotus
    leaves at its edge and two closed buds that stand up on their stalks.
    The water shows the light of the sky."""
    _shadow(tile, 8.5)
    basin = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 8.4, G - 7.6), (M + 8.4, G - 7.6), (M + 7.0, G - 1.2), (M + 7.6, G), (M - 7.6, G), (M - 7.0, G - 1.2)]))
    tile.put(basin, c["stone"])
    tile.put(basin * (tile.x < M - 4.0), c["stone_light"], 0.30)
    tile.put(basin * (tile.x > M + 4.6), c["dark"], 0.30)
    rim = tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 9.0, G - 8.6, M + 9.0, G - 6.8))
    tile.put(rim, c["stone"])
    tile.put(rim * (tile.y < G - 8.0), c["stone_light"], 0.6)
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 8.0, G - 5.2, M + 8.0, G - 4.6)), c["dark"], 0.5)
    water = tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, G - 8.6, 8.0, ry=0.9))
    tile.put(water, _mix(c["glow"], c["stone"], 0.35))
    for x, r in ((-5.0, 2.6), (4.4, 3.0)):
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + x, G - 8.9, r, ry=r * 0.35)), c["plant"])
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M + x, G - 8.9), (M + x + r * 0.7, G - 9.1)], 0.25)), c["dark"], 0.5)
    for x, h in ((-1.4, 18.0), (2.2, 14.0)):
        top = (M + x, G - h)
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M + x * 0.6, G - 8.8), top], 0.4)), _mix(c["plant"], c["dark"], 0.3))
        bud = [(top[0] - 1.4, top[1] + 0.8), (top[0], top[1] - 3.6), (top[0] + 1.4, top[1] + 0.8), (top[0], top[1] + 1.6)]
        tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, bud)), c["bloom"])
        tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [bud[0], bud[1], (top[0] - 0.2, top[1] + 1.2)])), _mix(c["bloom"], (255, 255, 255), 0.35))
    tile.alpha *= tile.y < G


def fallen_block(tile: Tile, c: dict) -> None:
    """A block of andesite that fell from a terrace and lies tilted on the
    ground. One face of it has its carving: a round moulding and a band of
    lotus petals. Moss grows on its top, and a small fern at its foot."""
    _shadow(tile, 8.5)
    cx, cy, w, h, a = M - 0.6, G - 5.0, 14.0, 9.0, math.radians(-7.0)

    def at(x: float, y: float) -> tuple[float, float]:
        return (cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a))

    body = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [at(-w / 2, -h / 2), at(w / 2, -h / 2), at(w / 2, h / 2), at(-w / 2, h / 2)]))
    tile.put(body, c["stone"])
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [at(-w / 2, -h / 2), at(w / 2, -h / 2), at(w / 2, -h / 2 + 1.0), at(-w / 2, -h / 2 + 1.0)])), c["stone_light"], 0.7)
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [at(-w / 2, -h / 2 + 2.6), at(w / 2, -h / 2 + 2.6)], 1.0)), c["stone_light"], 0.45)
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [at(-w / 2, -h / 2 + 3.6), at(w / 2, -h / 2 + 3.6)], 0.5)), c["dark"], 0.6)
    petals = [[at(x - 0.8, h / 2 - 0.6), at(x - 0.7, -h / 2 + 5.6), at(x, -h / 2 + 4.4), at(x + 0.7, -h / 2 + 5.6), at(x + 0.8, h / 2 - 0.6)] for x in np.linspace(-w / 2 + 1.2, w / 2 - 1.2, 7)]
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [at(-w / 2, -h / 2 + 4.0), at(w / 2, -h / 2 + 4.0), at(w / 2, h / 2), at(-w / 2, h / 2)])), c["dark"], 0.40)
    tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, q) for q in petals]), _mix(c["stone"], c["stone_light"], 0.2))
    moss = tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, *at(x, -h / 2), r, ry=0.9) for x, r in ((-4.0, 2.4), (0.6, 1.6), (4.4, 2.0))])
    tile.put(moss, c["plant"])
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(M + 8.0, G - 0.4), (M + 8.0 + dxx, G - 5.0)], 0.5) for dxx in (-1.4, 0.0, 1.4)]), c["plant"])
    tile.alpha *= tile.y < G


def sugar_palm_sapling(tile: Tile, c: dict) -> None:
    """A young sugar palm that has no trunk yet: a few stiff fan leaves on
    long stalks come up from its base, and each fan is a half round of
    pleated blades with split tips."""
    _shadow(tile, 6.0)
    stalk_colour = _mix(c["plant"], c["wood"], 0.45)
    for k, (bx, tx, ty, r) in enumerate(((M - 0.6, M - 5.2, G - 13.0, 4.4), (M + 0.6, M + 4.8, G - 15.0, 4.8), (M, M - 0.4, G - 18.0, 3.8))):
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(bx, G - 0.4), (tx, ty)], 0.55)), stalk_colour)
        # The fan: a half round of blades, each with a split tip, so its
        # edge is a row of small notches.
        edge = []
        for j in range(19):
            ang = math.radians(-170.0 + j * 160.0 / 18.0)
            reach = r * (1.0 if j % 2 == 0 else 0.82)
            edge.append((tx + math.cos(ang) * reach, ty + math.sin(ang) * reach))
        colour = _mix(c["plant"], c["dark"], 0.12 * k)
        tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(tx, ty + 0.4)] + edge)), colour)
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(tx, ty), q], 0.16) for q in edge[::2]]), _mix(colour, (240, 240, 190), 0.4), 0.7)
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(tx, ty), q], 0.14) for q in edge[1::2]]), c["dark"], 0.35)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, G - 1.0, 2.0, ry=1.2)), _mix(c["wood"], c["dark"], 0.3))
    tile.alpha *= tile.y < G


def sandstone_fragments(tile: Tile, c: dict) -> None:
    """Pieces of grey-pink sandstone that broke from a lintel: one has a
    part of its carved vine and a flower of four petals, one is a plain
    chunk, and small chips lie round them."""
    _shadow(tile, 9.0)
    big = [(M - 9.0, G), (M - 9.4, G - 5.6), (M - 6.0, G - 8.4), (M + 1.4, G - 8.0), (M + 2.4, G - 4.0), (M + 1.6, G)]
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, big)), c["stone"])
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 9.4, G - 5.6), (M - 6.0, G - 8.4), (M + 1.4, G - 8.0), (M + 0.8, G - 6.8), (M - 8.6, G - 4.8)])), c["stone_light"], 0.6)
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M - 8.4, G - 3.0), (M - 6.0, G - 4.4), (M - 3.0, G - 2.6), (M + 0.6, G - 4.0)], 0.4)), c["dark"], 0.55)
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M - 4.0 + ox, G - 4.2 + oy, 0.7) for ox, oy in ((-0.9, 0.0), (0.9, 0.0), (0.0, -0.9), (0.0, 0.9))]), _mix(c["stone"], c["dark"], 0.35))
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M - 4.0, G - 4.2, 0.45)), c["stone_light"])
    small = [(M + 3.4, G), (M + 4.0, G - 4.4), (M + 7.6, G - 5.0), (M + 9.0, G - 1.6), (M + 8.6, G)]
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, small)), _mix(c["stone"], c["dark"], 0.12))
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M + 4.0, G - 4.4), (M + 7.6, G - 5.0), (M + 7.0, G - 3.6), (M + 4.6, G - 3.4)])), c["stone_light"], 0.45)
    chips = [(M + 2.6, G - 0.5, 0.6), (M - 10.4, G - 0.4, 0.5), (M + 10.0, G - 0.4, 0.45)]
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, r, ry=r * 0.7) for x, y, r in chips]), c["stone"])
    tile.alpha *= tile.y < G


def stone_jar(tile: Tile, c: dict) -> None:
    """A big jar of the Khmer for water: a squat round body of stoneware
    under a dark brown glaze, a wide low mouth, and bands cut round its
    shoulder. It stands on a flat stone of laterite."""
    _shadow(tile, 8.0)
    glaze = _mix(c["wood"], c["dark"], 0.35)
    base = tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 7.6, G - 2.0, M + 7.6, G))
    tile.put(base, c["metal"])
    tile.put(base * (tile.y < G - 1.4), _mix(c["metal"], (255, 220, 190), 0.25), 0.6)
    body = tile.mask(lambda p, dx, dy: (_dot(p, dx, dy, M, G - 8.6, 6.4, ry=6.2), _box(p, dx, dy, M - 3.6, G - 4.0, M + 3.6, G - 2.0)))
    tile.put(body, glaze)
    tile.put(body * (tile.x < M - 2.2), _mix(glaze, (255, 230, 190), 0.25), 0.6)
    tile.put(body * (tile.x > M + 3.0), c["dark"], 0.35)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M - 2.4, G - 11.4, 1.0, ry=1.8)), (255, 236, 200), 0.35)
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(M - 5.6, G - y), (M + 5.6, G - y)], 0.25) for y in (11.2, 12.2)]), c["dark"], 0.6)
    mouth = tile.mask(lambda p, dx, dy: (_box(p, dx, dy, M - 3.4, G - 16.0, M + 3.4, G - 14.0), _dot(p, dx, dy, M, G - 16.0, 3.8, ry=0.9)))
    tile.put(mouth, glaze)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, G - 16.1, 2.8, ry=0.55)), c["dark"], 0.85)
    tile.alpha *= tile.y < G


# East Asia and its coast. At Sannai-Maruyama `metal` is the green-brown
# of a chestnut burr and `bloom` the rust of a fallen leaf; in Taiwan
# `metal` is the green of nephrite and `bloom` the gold of millet; at
# Gyeongju `wood` is the bark of a red pine and `bloom` the red of maple.


def chestnut_burrs(tile: Tile, c: dict) -> None:
    """Burrs of the chestnut that fell from the trees the people of
    Sannai-Maruyama tended: round husks covered in fine spines. The large
    husk has split open across its top and shows three shiny brown nuts.
    A small husk is still closed, and a nut lies loose."""
    _shadow(tile, 9.0)

    def burr(cx: float, cy: float, r: float) -> None:
        spines = []
        for k in range(36):
            a = k * 2.0 * math.pi / 36.0
            spines.append([(cx + math.cos(a) * r * 0.6, cy + math.sin(a) * r * 0.6), (cx + math.cos(a + 0.12) * (r + 1.2), cy + math.sin(a + 0.12) * (r + 1.2))])
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, pts, 0.24) for pts in spines]), _mix(c["metal"], (240, 220, 160), 0.15), 0.9)
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, cx, cy, r)), c["metal"])
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, cx + r * 0.25, cy + r * 0.3, r * 0.75)), _mix(c["metal"], c["dark"], 0.25), 0.5)

    burr(M - 6.6, G - 2.6, 2.4)
    cx, cy, r = M + 0.6, G - 4.8, 4.4
    burr(cx, cy, r)
    # The split: a dark opening across the top of the husk, its pale
    # inner lining, and the three nuts packed in it.
    mouth = tile.mask(lambda p, dx, dy: _dot(p, dx, dy, cx, cy - 1.4, 3.8, ry=2.4))
    tile.put(mouth, (214, 196, 156))
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, cx, cy - 1.0, 3.2, ry=1.8)), c["dark"], 0.7)
    for nx, ny, w in ((-2.0, -1.2, 1.6), (2.0, -1.2, 1.6), (0.0, -2.0, 1.8)):
        x, y = cx + nx, cy + ny
        nut = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(x - w, y + 1.4), (x - w * 0.9, y - 0.4), (x, y - 2.0), (x + w * 0.9, y - 0.4), (x + w, y + 1.4)]))
        tile.put(nut, c["wood"])
        tile.put(nut * (tile.x < x - w * 0.2) * (tile.y < y + 0.4), _mix(c["wood"], (255, 230, 190), 0.4), 0.7)
        tile.put(nut * (tile.x > x + w * 0.4), c["dark"], 0.35)
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(x, y - 2.0), (x + 0.2, y - 2.6)], 0.3)), (226, 206, 160), 0.9)
    loose = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M + 8.0, G), (M + 8.2, G - 1.8), (M + 9.4, G - 3.0), (M + 10.6, G - 1.8), (M + 10.8, G)]))
    tile.put(loose, c["wood"])
    tile.put(loose * (tile.y > G - 0.8), (214, 196, 160), 0.85)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + 8.9, G - 1.9, 0.5, ry=0.35)), (255, 236, 200), 0.6)
    tile.alpha *= tile.y < G


def log_mushrooms(tile: Tile, c: dict) -> None:
    """A short piece of a fallen chestnut log, soft with age and green with
    moss, and brown mushrooms that grow on it. The people of the Jomon
    gathered mushrooms in autumn with their nuts."""
    _shadow(tile, 10.0)
    log = tile.mask(lambda p, dx, dy: (_box(p, dx, dy, M - 9.0, G - 6.0, M + 7.0, G), _dot(p, dx, dy, M + 7.0, G - 3.0, 1.6, ry=3.0)))
    tile.put(log, _mix(c["wood"], c["dark"], 0.25))
    tile.put(log * (tile.y < G - 4.6), _mix(c["wood"], (255, 230, 190), 0.2), 0.6)
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(M - 8.0, G - y), (M + 6.0, G - y + 0.3)], 0.25) for y in (2.0, 3.6)]), c["dark"], 0.45)
    end = tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M - 9.0, G - 3.0, 1.8, ry=3.0))
    tile.put(end, _mix(c["wood"], (230, 200, 150), 0.45))
    tile.put(tile.mask(lambda p, dx, dy: p.ellipse([(M - 10.0) * K + dx, (G - 4.6) * K + dy, (M - 8.0) * K + dx, (G - 1.4) * K + dy], outline=255, width=max(1, int(0.25 * K)))), c["wood"], 0.7)
    moss = [(M - 6.0, G - 6.0, 2.4), (M - 1.0, G - 6.2, 1.8), (M + 4.4, G - 5.8, 2.2)]
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, r, ry=r * 0.45) for x, y, r in moss]), c["plant"])
    for x, h, r in ((-4.0, 3.4, 2.8), (0.8, 4.6, 3.4), (4.6, 2.6, 2.2)):
        top = G - 6.0 - h
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M + x - 0.5, top, M + x + 0.5, G - 5.6)), (222, 210, 186))
        cap = tile.mask(lambda p, dx, dy: p.pieslice([(M + x - r) * K + dx, (top - r * 0.75) * K + dy, (M + x + r) * K + dx, (top + r * 0.75) * K + dy], 180, 360, fill=255))
        tile.put(cap, _mix(c["bloom"], c["wood"], 0.55))
        tile.put(cap * (tile.y < top - r * 0.4), _mix(c["bloom"], (255, 230, 190), 0.25), 0.6)
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M + x - r * 0.9, top - 0.15, M + x + r * 0.9, top + 0.35)), (226, 210, 180), 0.8)
    tile.alpha *= tile.y < G


def clam_heap(tile: Tile, c: dict) -> None:
    """A heap of shells that the people of Sannai-Maruyama threw away
    after a meal of clams from Mutsu Bay. Such heaps, the shell middens,
    are where much of what we know of the Jomon was found. Pale ribbed
    clam shells lie on a low mound, with a few dark mussels among them."""
    _shadow(tile, 10.0)
    mound = tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, G, 10.0, ry=5.0))
    tile.put(mound, _mix(c["stone"], c["dark"], 0.35))
    rng = tile.rng
    shells = [(M + rng.uniform(-8.0, 8.0), G - rng.uniform(0.6, 4.0), rng.uniform(1.3, 2.1), rng.uniform(-0.6, 0.6), rng.random() < 0.18) for _ in range(20)]
    shells = [s for s in shells if ((s[0] - M) / 9.5) ** 2 + ((G - s[1]) / 4.8) ** 2 < 1.0]
    shells.sort(key=lambda s: s[1])
    for x, y, r, a, mussel in shells:
        colour = _mix(c["dark"], (60, 70, 90), 0.4) if mussel else _mix(c["stone_light"], c["stone"], rng.uniform(0.0, 0.4))
        shell = tile.mask(lambda p, dx, dy: p.pieslice([(x - r) * K + dx, (y - r) * K + dy, (x + r) * K + dx, (y + r) * K + dy], 180 + a * 30.0, 360 + a * 30.0, fill=255))
        tile.put(shell, colour)
        if not mussel:
            tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x, y), (x + math.cos(math.pi + (k + 0.5) * math.pi / 5.0 + a * 0.52) * r * 0.9, y + math.sin(math.pi + (k + 0.5) * math.pi / 5.0 + a * 0.52) * r * 0.9)], 0.18) for k in range(5)]), c["stone"], 0.6)
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(x - r, y), (x + r, y)], 0.2)), c["dark"], 0.5)
    tile.alpha *= tile.y < G


def millet_heads(tile: Tile, c: dict) -> None:
    """Foxtail millet, which the first farmers of Taiwan grew with rice:
    stalks with long arching leaves, each stalk bent over at its top by a
    heavy, nodding head of small gold grains with fine bristles."""
    _shadow(tile, 6.0)
    stalk = _mix(c["plant"], c["bloom"], 0.35)

    def curve(a, b, ctrl, n=9):
        return [((1 - t) ** 2 * a[0] + 2 * (1 - t) * t * ctrl[0] + t * t * b[0], (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * ctrl[1] + t * t * b[1]) for t in np.linspace(0.0, 1.0, n)]

    for x, h, side in ((-3.4, 15.0, -1.0), (0.2, 19.0, 1.0), (3.2, 14.0, 1.0)):
        base = (M + x, G)
        apex = (M + x + side * 2.0, G - h)
        pts = curve(base, apex, (M + x - side * 0.4, G - h * 0.9))
        for ly, ls in ((0.30, -side), (0.55, side)):
            y0 = G - h * ly
            x0 = M + x + side * 0.2
            blade = curve((x0, y0), (x0 + ls * 6.0, y0 + 0.6), (x0 + ls * 3.6, y0 - 4.0))
            upper = [(px, py - 0.55 * (1.0 - k / 8.0)) for k, (px, py) in enumerate(blade)]
            tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, blade + upper[::-1])), c["plant"])
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, pts, 0.45)), stalk)
        # The head nods: it hangs from the bent top, down and out.
        head = curve(apex, (apex[0] + side * 2.6, apex[1] + 6.0), (apex[0] + side * 2.6, apex[1] + 0.6), 7)
        widths = (1.0, 1.8, 2.2, 2.2, 2.0, 1.6, 1.0)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, hx, hy, w * 0.75) for (hx, hy), w in zip(head, widths)]), c["bloom"])
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, hx - side * 0.4, hy - 0.3, w * 0.3) for (hx, hy), w in zip(head, widths)]), _mix(c["bloom"], (255, 240, 190), 0.45), 0.8)
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(hx, hy), (hx + side * 1.6, hy + 0.8)], 0.14) for hx, hy in head[1:]]), _mix(c["bloom"], c["dark"], 0.3), 0.7)
    tile.alpha *= tile.y < G


def pandanus(tile: Tile, c: dict) -> None:
    """A young pandanus, the screw pine of the coasts of Taiwan: a short
    trunk that stands on curved prop roots, and a crown of long, narrow
    leaves that arch out and droop at their tips. People wove its leaves
    into mats and sails."""
    _shadow(tile, 7.0)
    bark = _mix(c["wood"], c["stone"], 0.3)
    roots = []
    for end, bend in ((-5.0, -1.6), (-1.8, -0.6), (2.4, 0.8), (5.2, 1.8)):
        roots.append([(M + end * (t ** 1.3) + bend * math.sin(t * math.pi) * 0.6, G - 6.0 + 6.0 * t) for t in np.linspace(0.0, 1.0, 7)])
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, pts, 0.8) for pts in roots]), _mix(bark, c["dark"], 0.15))
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x - 0.3, y) for x, y in pts], 0.3) for pts in roots]), _mix(bark, (255, 240, 210), 0.3), 0.5)
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 1.0, G - 12.0, M + 1.0, G - 5.6)), bark)
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(M - 1.0, G - y), (M + 1.0, G - y - 0.5)], 0.2) for y in (7.0, 8.6, 10.2, 11.6)]), c["dark"], 0.5)
    for k, (angle, length, droop) in enumerate(((-78.0, 10.0, 4.0), (-50.0, 11.0, 3.4), (-24.0, 10.0, 1.6), (16.0, 10.5, 1.8), (46.0, 11.0, 3.4), (76.0, 10.0, 4.2), (-4.0, 8.5, -1.0))):
        a = math.radians(angle)
        base = (M, G - 12.0)
        mid = (M + math.sin(a) * length * 0.6, G - 12.0 - math.cos(a) * length * 0.9 - 2.0)
        tip = (M + math.sin(a) * length, G - 12.0 - math.cos(a) * length * 0.5 + droop)
        pts = [((1 - t) ** 2 * base[0] + 2 * (1 - t) * t * mid[0] + t * t * tip[0], (1 - t) ** 2 * base[1] + 2 * (1 - t) * t * mid[1] + t * t * tip[1]) for t in np.linspace(0.0, 1.0, 9)]
        colour = c["plant"] if k % 2 == 0 else _mix(c["plant"], c["dark"], 0.22)
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, pts, 1.0)), colour)
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, pts[-3:], 0.6)), colour)
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, pts[1:-2], 0.25)), _mix(c["plant"], (255, 255, 220), 0.3), 0.5)
    tile.alpha *= tile.y < G


def jade_pebble(tile: Tile, c: dict) -> None:
    """A pebble of green nephrite from the river at Fengtian, rounded by
    the water: the stone from which the people of Taiwan made adzes and
    ornaments that were traded across the sea. It glows a little where
    the light goes into it. Two grey river stones lie by it."""
    _shadow(tile, 8.0)
    for x, rx, ry in ((-6.0, 2.6, 1.6), (6.4, 2.2, 1.3)):
        body = tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + x, G - ry, rx, ry=ry))
        tile.put(body, c["stone"])
        tile.put(body * (tile.y < G - ry * 1.3), c["stone_light"], 0.45)
    jade = tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, G - 2.8, 4.2, ry=2.8))
    tile.put(jade, _mix(c["metal"], c["dark"], 0.25))
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + 0.6, G - 2.4, 3.0, ry=1.8), blur=0.6) * jade, _mix(c["metal"], (200, 255, 210), 0.30), 0.8)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M - 1.6, G - 4.2, 1.3, ry=0.5)), (240, 255, 240), 0.65)
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M - 2.6, G - 1.6), (M + 0.4, G - 2.6), (M + 3.0, G - 2.0)], 0.2)) * jade, _mix(c["metal"], c["dark"], 0.5), 0.5)
    tile.alpha *= tile.y < G


def _maple_shape(cx: float, cy: float, r: float, turn: float) -> list[tuple[float, float]]:
    """The outline of a maple leaf of five pointed lobes."""
    pts = []
    for k in range(10):
        a = turn - math.pi / 2.0 + k * math.pi / 5.0
        rr = r if k % 2 == 0 else r * 0.42
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr * 0.55))
    return pts


def maple_leaves(tile: Tile, c: dict) -> None:
    """Leaves of maple that fell in the autumn of Gyeongju: a small drift
    of red, scarlet and gold leaves on the ground, each of five points."""
    _shadow(tile, 9.0)
    rng = tile.rng
    colours = (c["bloom"], _mix(c["bloom"], (240, 140, 40), 0.5), _mix(c["bloom"], c["dark"], 0.25), (226, 168, 60))
    leaves = [(M + rng.uniform(-8.0, 8.0), G - rng.uniform(0.6, 2.8), rng.uniform(1.8, 2.8), rng.uniform(-0.6, 0.6), k % 4) for k in range(9)]
    leaves.append((M + 1.0, G - 3.6, 3.0, 0.2, 0))
    for x, y, r, turn, k in leaves:
        tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, _maple_shape(x, y, r, turn))), colours[k])
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(x, y), (x + math.sin(turn) * r * 0.5, y + 1.4)], 0.18)), c["dark"], 0.5)
    tile.alpha *= tile.y < G


def pine_cones(tile: Tile, c: dict) -> None:
    """Cones of the red pine that grows among the royal tombs: small and
    egg-shaped, their scales open. A few long needles in pairs lie by
    them."""
    _shadow(tile, 8.0)
    needles = [[(M - 9.0 + k * 1.6, G - 0.3), (M - 5.0 + k * 2.2, G - 1.6 - (k % 2) * 0.6)] for k in range(6)]
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, pts, 0.2) for pts in needles]), _mix(c["plant"], c["wood"], 0.4), 0.8)
    for cx, cy, rx, ry, lean in ((M - 3.0, G - 3.0, 2.4, 3.0, -0.4), (M + 3.6, G - 2.4, 2.2, 2.4, 0.9)):
        cone = tile.mask(lambda p, dx, dy: _dot(p, dx, dy, cx, cy, rx, ry=ry))
        tile.put(cone, _mix(c["wood"], c["dark"], 0.35))
        scales = []
        for row in range(4):
            yy = cy - ry + 1.0 + row * (ry * 2.0 - 1.4) / 3.0
            half = rx * math.sqrt(max(0.0, 1.0 - ((yy - cy) / ry) ** 2))
            for j in range(-1, 2):
                sx = cx + j * half * 0.6 + (row % 2) * 0.5 + lean * (yy - cy) * 0.15
                scales.append((sx, yy))
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, 0.75, ry=0.55) for x, y in scales]) * cone, c["wood"])
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x - 0.2, y - 0.2, 0.35, ry=0.22) for x, y in scales]) * cone, _mix(c["wood"], (255, 220, 180), 0.35), 0.8)
    tile.alpha *= tile.y < G


def granite_fragments(tile: Tile, c: dict) -> None:
    """Pieces of grey granite left where the masons of Silla dressed the
    blocks for a kerb: one has a flat dressed face and a straight edge,
    one is a rough chunk, and chips lie round them. The stone is speckled
    with black and white grains."""
    _shadow(tile, 9.0)
    big = [(M - 9.0, G), (M - 9.0, G - 6.6), (M - 1.0, G - 6.6), (M + 1.6, G - 3.4), (M + 1.0, G)]
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, big)), c["stone"])
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 9.0, G - 6.6), (M - 1.0, G - 6.6), (M - 1.4, G - 5.6), (M - 9.0, G - 5.6)])), c["stone_light"], 0.7)
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 1.0, G - 6.6), (M + 1.6, G - 3.4), (M + 1.0, G), (M - 0.6, G)])), c["dark"], 0.35)
    small = [(M + 2.6, G), (M + 3.6, G - 3.8), (M + 6.6, G - 4.4), (M + 8.8, G - 1.8), (M + 8.0, G)]
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, small)), _mix(c["stone"], c["dark"], 0.10))
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M + 3.6, G - 3.8), (M + 6.6, G - 4.4), (M + 6.2, G - 3.2), (M + 4.0, G - 2.8)])), c["stone_light"], 0.5)
    rng = tile.rng
    grains = [(rng.uniform(M - 8.6, M + 8.4), rng.uniform(G - 6.0, G - 0.4)) for _ in range(40)]
    inside = tile.mask(lambda p, dx, dy: (_poly(p, dx, dy, big), _poly(p, dx, dy, small)))
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, 0.22) for x, y in grains[::2]]) * inside, c["dark"], 0.7)
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, 0.22) for x, y in grains[1::2]]) * inside, (244, 238, 228), 0.6)
    chips = [(M + 1.8, G - 0.4, 0.6), (M - 10.2, G - 0.4, 0.5), (M + 10.0, G - 0.4, 0.5)]
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, r, ry=r * 0.7) for x, y, r in chips]), c["stone"])
    tile.alpha *= tile.y < G


def seokdeung(tile: Tile, c: dict) -> None:
    """A plain stone lantern of Silla, of granite: a base of two steps, a
    slim post, an eight-sided box for the light with two windows that
    show, a roof of eight sides whose corners turn up a little, and a
    small knob on top. It has no carved figures."""
    _shadow(tile, 6.0)
    stone = tile.mask(lambda p, dx, dy: (
        _box(p, dx, dy, M - 4.6, G - 1.6, M + 4.6, G), _box(p, dx, dy, M - 3.4, G - 3.0, M + 3.4, G - 1.6),
        _box(p, dx, dy, M - 1.0, G - 9.6, M + 1.0, G - 3.0), _box(p, dx, dy, M - 3.0, G - 10.6, M + 3.0, G - 9.6),
        _poly(p, dx, dy, [(M - 2.6, G - 10.6), (M - 3.0, G - 14.6), (M + 3.0, G - 14.6), (M + 2.6, G - 10.6)]),
        _poly(p, dx, dy, [(M - 6.0, G - 14.2), (M - 5.0, G - 15.0), (M - 2.0, G - 17.0), (M + 2.0, G - 17.0), (M + 5.0, G - 15.0), (M + 6.0, G - 14.2), (M + 4.6, G - 14.6), (M - 4.6, G - 14.6)]),
        _box(p, dx, dy, M - 0.8, G - 18.4, M + 0.8, G - 17.0), _dot(p, dx, dy, M, G - 19.2, 1.1, ry=1.3)))
    tile.put(stone, c["stone"])
    tile.put(stone * (tile.x < M - 1.0), c["stone_light"], 0.40)
    tile.put(stone * (tile.x > M + 2.0), c["dark"], 0.25)
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(M - 4.6, G - y), (M + 4.6, G - y)], 0.2) for y in (1.6, 3.0)]), c["dark"], 0.5)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, G - 12.6, 6.0), blur=1.5), c["glow"], 0.30)
    for x0, x1 in ((M - 2.2, M - 0.6), (M + 0.6, M + 2.2)):
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0, G - 13.8, x1, G - 11.4)), _mix(c["glow"], (255, 255, 255), 0.25))
    tile.alpha *= tile.y < G


# West Lake, Heian-kyo and Gyeongbokgung. At Hangzhou `plant` is the
# yellow-green of a willow in spring and `bloom` the red of a paper
# lantern; at Heian-kyo `bloom` is the red of maple and `glow` the sky in
# still water; at Hanyang `bloom` is the pink of a peony and `metal` the
# grey of a fired roof tile.


def _curve(a, b, ctrl, n: int = 9) -> list[tuple[float, float]]:
    """Points along a quadratic curve from `a` to `b` that bends to `ctrl`."""
    return [((1 - t) ** 2 * a[0] + 2 * (1 - t) * t * ctrl[0] + t * t * b[0], (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * ctrl[1] + t * t * b[1]) for t in np.linspace(0.0, 1.0, n)]


def willow_sapling(tile: Tile, c: dict) -> None:
    """A young weeping willow of the banks of West Lake in spring: a short
    trunk, a few branches that arch out from its top, and from them long
    thin strands that hang down, each one set with small narrow leaves of
    fresh yellow-green."""
    _shadow(tile, 7.0)
    bark = _mix(c["wood"], c["dark"], 0.25)
    trunk = [(M - 1.1, G), (M + 1.1, G), (M + 0.7, G - 9.0), (M + 0.2, G - 14.6), (M - 0.6, G - 14.6), (M - 0.5, G - 9.0)]
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, trunk)), bark)
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M - 0.6, G - 0.4), (M - 0.3, G - 13.0)], 0.3)), c["wood_light"], 0.45)
    top = (M, G - 14.2)
    rng = tile.rng
    strands = []
    for end_x, end_y, ctrl_y in ((-8.0, -15.6, -20.0), (-4.4, -17.6, -21.0), (0.6, -19.0, -21.6), (4.8, -17.4, -21.0), (8.2, -15.0, -19.6)):
        arc = _curve(top, (M + end_x, G + end_y), (M + end_x * 0.4, G + ctrl_y), 8)
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, arc, 0.45)), bark)
        for bx, by in arc[2::1]:
            length = rng.uniform(7.0, 13.0) * (0.7 + 0.3 * abs(bx - M) / 8.0)
            drift = (bx - M) * 0.08
            strands.append(_curve((bx, by), (bx + drift, min(by + length, G - 2.4)), (bx + drift * 2.0, by + length * 0.3), 9))
    for k, pts in enumerate(strands):
        colour = c["plant"] if k % 2 else _mix(c["plant"], c["dark"], 0.28)
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, pts, 0.2)), _mix(c["plant"], c["wood"], 0.5), 0.8)
        leaves = [(x + (0.3 if j % 2 else -0.3), y) for j, (x, y) in enumerate(pts[1:])]
        tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, [(x, y - 0.9), (x + 0.22, y), (x, y + 0.6), (x - 0.22, y)]) for x, y in leaves]), colour)
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x - 0.1, y - 0.6), (x - 0.1, y + 0.1)], 0.12) for pts in strands[::3] for x, y in pts[2::2]]), _mix(c["plant"], (255, 255, 210), 0.45), 0.8)
    tile.alpha *= tile.y < G


def tea_bush(tile: Tile, c: dict) -> None:
    """A tea bush of the hills round West Lake, where the famous green
    tea grows: clipped round and low, thick with small glossy dark leaves.
    Fresh shoots of pale green stand on its top, a bud and two leaves,
    which are the part that is picked; two small white flowers with gold
    middles are on its side."""
    _shadow(tile, 8.0)
    deep = _mix(c["plant"], (24, 60, 34), 0.55)
    lumps = [(-5.0, 3.6, 3.6), (-1.4, 6.0, 4.6), (3.0, 5.4, 4.4), (6.0, 3.0, 3.0), (0.6, 3.0, 4.0)]
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M + x, G - y, r, ry=r * 0.85) for x, y, r in lumps]), _mix(deep, c["dark"], 0.35))
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M + x - 0.6, G - y - 0.6, r * 0.78, ry=r * 0.66) for x, y, r in lumps]), deep)
    rng = tile.rng
    leaves = [(M + rng.uniform(-7.0, 7.0), G - rng.uniform(1.5, 9.0), rng.uniform(-0.8, 0.8)) for _ in range(40)]
    body = tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M + x, G - y, r, ry=r * 0.85) for x, y, r in lumps])
    tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, [(x - math.cos(a) * 0.9, y - math.sin(a) * 0.9), (x, y - 0.35), (x + math.cos(a) * 0.9, y + math.sin(a) * 0.9), (x, y + 0.35)]) for x, y, a in leaves]) * body,
             _mix(deep, (210, 240, 190), 0.30), 0.7)
    for x, h, lean in ((-3.2, 9.8, -0.6), (-0.4, 11.4, 0.2), (2.6, 10.8, 0.6), (5.0, 8.4, 0.9)):
        base = (M + x, G - h + 1.6)
        tip = (M + x + lean, G - h - 1.0)
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [base, tip], 0.22)), _mix(c["plant"], c["wood"], 0.3))
        tile.put(tile.mask(lambda p, dx, dy: (_dot(p, dx, dy, tip[0], tip[1], 0.35, ry=0.7),
                                               _poly(p, dx, dy, [(base[0] + lean * 0.4, base[1] - 1.0), (base[0] - 1.5, base[1] - 1.8), (base[0] - 0.4, base[1] - 0.6)]),
                                               _poly(p, dx, dy, [(base[0] + lean * 0.6, base[1] - 1.6), (base[0] + 1.6, base[1] - 2.4), (base[0] + 0.6, base[1] - 1.1)]))), _mix(c["plant"], (230, 250, 170), 0.35))
    for x, y in ((-5.6, 4.4), (4.4, 2.8)):
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M + x + math.cos(a) * 0.55, G - y + math.sin(a) * 0.55, 0.42) for a in np.linspace(0.0, 2.0 * math.pi, 5, endpoint=False)]), (240, 236, 222))
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + x, G - y, 0.4)), (226, 186, 80))
    tile.alpha *= tile.y < G


def song_stone_lantern(tile: Tile, c: dict) -> None:
    """A plain stone lantern by the lake, square in plan: a base of two
    steps, a square post, a slab, a box for the light with a square window,
    a low roof of four slopes with straight eaves, and a round knob on
    top. It has no carved figures."""
    _shadow(tile, 6.0)
    roof = [(M - 5.6, G - 14.0), (M - 2.0, G - 16.4), (M + 2.0, G - 16.4), (M + 5.6, G - 14.0), (M + 5.6, G - 13.4), (M - 5.6, G - 13.4)]
    stone = tile.mask(lambda p, dx, dy: (
        _box(p, dx, dy, M - 4.4, G - 1.4, M + 4.4, G), _box(p, dx, dy, M - 3.4, G - 2.6, M + 3.4, G - 1.4),
        _box(p, dx, dy, M - 1.2, G - 7.6, M + 1.2, G - 2.6), _box(p, dx, dy, M - 3.6, G - 8.6, M + 3.6, G - 7.6),
        _box(p, dx, dy, M - 2.8, G - 13.4, M + 2.8, G - 8.6), _poly(p, dx, dy, roof),
        _box(p, dx, dy, M - 0.7, G - 17.4, M + 0.7, G - 16.4), _dot(p, dx, dy, M, G - 18.2, 1.0, ry=1.1)))
    tile.put(stone, c["stone"])
    tile.put(stone * (tile.x < M - 1.2), c["stone_light"], 0.40)
    tile.put(stone * (tile.x > M + 1.8), c["dark"], 0.25)
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, M - 4.4, G - y, M + 4.4, G - y + 0.2) for y in (1.4, 2.6)]), c["dark"], 0.45)
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 5.6, G - 13.6, M + 5.6, G - 13.4)), c["dark"], 0.5)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, G - 11.0, 6.0), blur=1.5), c["glow"], 0.32)
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 1.6, G - 12.4, M + 1.6, G - 9.6)), _mix(c["glow"], (255, 255, 255), 0.25))
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 0.15, G - 12.4, M + 0.15, G - 9.6)), c["stone"], 0.8)
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M + x, G - 0.8, 1.1, ry=0.6) for x in (-4.2, 3.8)]), _mix(c["plant"], c["dark"], 0.3), 0.6)
    tile.alpha *= tile.y < G


def lantern_stand(tile: Tile, c: dict) -> None:
    """Two red paper lanterns that hang from the bar of a small wooden
    stand, as at a tea house by the lake in the evening. Each lantern is
    round, with ribs of bamboo, dark caps at top and foot, and a red
    tassel. They give a warm light."""
    _shadow(tile, 8.0)
    wood = _mix(c["wood"], c["dark"], 0.15)
    frame = tile.mask(lambda p, dx, dy: (_box(p, dx, dy, M - 8.4, G - 19.4, M - 7.4, G), _box(p, dx, dy, M + 7.4, G - 19.4, M + 8.4, G),
                                           _box(p, dx, dy, M - 9.6, G - 20.4, M + 9.6, G - 19.4), _box(p, dx, dy, M - 9.2, G - 1.0, M - 6.6, G), _box(p, dx, dy, M + 6.6, G - 1.0, M + 9.2, G)))
    tile.put(frame, wood)
    tile.put(frame * (tile.y < G - 20.0), c["wood_light"], 0.6)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, G - 13.0, 8.0), blur=2.0), c["glow"], 0.30)
    for x, cy in ((-3.6, 13.6), (3.6, 12.6)):
        cx, cy = M + x, G - cy
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(cx, G - 19.4), (cx, cy - 4.6)], 0.25)), c["dark"])
        body = tile.mask(lambda p, dx, dy: _dot(p, dx, dy, cx, cy, 3.0, ry=3.6))
        tile.put(body, c["bloom"])
        tile.put(body * np.clip(1.0 - np.abs(tile.x - cx + 0.8) / 1.6, 0, 1), _mix(c["bloom"], c["glow"], 0.55), 0.7)
        tile.put(body * (np.abs(((tile.y - cy) % 1.5) - 0.75) < 0.12), _mix(c["bloom"], c["dark"], 0.4), 0.6)
        tile.put(body * (tile.x > cx + 1.6), c["dark"], 0.25)
        tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, cx - 1.6, cy - 4.4, cx + 1.6, cy - 3.3), _box(p, dx, dy, cx - 1.6, cy + 3.3, cx + 1.6, cy + 4.4))), c["metal"])
        tile.put(tile.mask(lambda p, dx, dy: (_line(p, dx, dy, [(cx, cy + 4.4), (cx, cy + 6.2)], 0.25), _poly(p, dx, dy, [(cx - 0.5, cy + 6.0), (cx + 0.5, cy + 6.0), (cx + 0.8, cy + 8.0), (cx - 0.8, cy + 8.0)]))), _mix(c["bloom"], c["dark"], 0.2))
    tile.alpha *= tile.y < G


def _momiji_shape(cx: float, cy: float, r: float, turn: float, squash: float) -> list[tuple[float, float]]:
    """The outline of a leaf of the Japanese maple: seven pointed lobes cut
    deep, the two lowest short, a gap at the foot. `squash` flattens it in
    y, as a leaf that lies on the ground is seen at a slant."""
    pts = []
    lobes = ((-2.08, 0.5), (-1.42, 0.78), (-0.72, 0.94), (0.0, 1.0), (0.72, 0.94), (1.42, 0.78), (2.08, 0.5))
    for k, (a, length) in enumerate(lobes):
        if k == 0:
            pts.append((a - 0.5, 0.18))
        pts.append((a - 0.16, 0.42))
        pts.append((a, length))
        pts.append((a + 0.16, 0.42))
        pts.append((a + 0.36, 0.24))
    out = []
    for a, rr in pts:
        a2 = a + turn
        out.append((cx + math.sin(a2) * rr * r, cy - math.cos(a2) * rr * r * squash))
    return out


def momiji_drift(tile: Tile, c: dict) -> None:
    """Leaves of the Japanese maple that fell in a garden of Heian-kyo in
    autumn: a small drift of red, scarlet and orange leaves on the ground,
    each of seven deep, pointed lobes."""
    _shadow(tile, 9.0)
    rng = tile.rng
    colours = (c["bloom"], _mix(c["bloom"], (236, 120, 40), 0.55), _mix(c["bloom"], c["dark"], 0.3), (214, 128, 40))
    leaves = [(M + rng.uniform(-8.0, 8.0), G - rng.uniform(0.8, 2.8), rng.uniform(1.8, 2.6), rng.uniform(-0.7, 0.7), k % 4) for k in range(14)]
    leaves.append((M + 0.8, G - 3.0, 3.2, 0.25, 0))
    leaves.sort(key=lambda leaf: leaf[1])
    for x, y, r, turn, k in leaves:
        squash = 0.55 if r < 3.0 else 0.7
        tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, _momiji_shape(x, y, r, turn, squash))), colours[k])
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x, y), (x + math.sin(a + turn) * r * 0.7, y - math.cos(a + turn) * r * 0.7 * squash)], 0.12) for a in (-1.42, 0.0, 1.42)]), c["dark"], 0.35)
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(x, y), (x - math.sin(turn) * r * 0.7, y + r * 0.5 * squash)], 0.16)), _mix(colours[k], c["dark"], 0.4), 0.8)
    tile.alpha *= tile.y < G


def pampas_grass(tile: Tile, c: dict) -> None:
    """Japanese pampas grass, susuki, one of the seven flowers of autumn
    that the poets of the court wrote of: a clump of long narrow leaves
    that arch over, each with a pale line down its middle, and tall stems
    with soft plumes of silver and pale rose that nod in the wind."""
    _shadow(tile, 7.0)
    leaf = _mix(c["plant"], (150, 150, 110), 0.25)
    for k, (end_x, h, ctrl) in enumerate(((-9.0, 7.0, -3.0), (-7.0, 11.0, -1.0), (-3.0, 14.0, -1.0), (2.0, 13.0, 1.0), (6.6, 11.0, 2.0), (9.0, 6.0, 4.0), (-5.0, 5.0, -4.0), (4.6, 6.0, 4.0))):
        base = (M + end_x * 0.12, G)
        tip = (M + end_x, G - h * 0.55)
        pts = _curve(base, tip, (M + ctrl, G - h), 10)
        colour = leaf if k % 2 else _mix(leaf, c["dark"], 0.25)
        upper = [(x, y - 0.9 * (1.0 - j / 9.0)) for j, (x, y) in enumerate(pts)]
        tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, pts + upper[::-1])), colour)
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, upper[1:-2], 0.12)), _mix(leaf, (240, 240, 220), 0.5), 0.6)
    plume = _mix((214, 204, 200), c["bloom"], 0.12)
    for x, h, lean in ((-2.6, 18.6, -2.4), (0.6, 21.0, 0.8), (3.4, 18.0, 3.0), (-0.6, 15.6, -1.0)):
        top = (M + x + lean, G - h)
        stem = _curve((M + x * 0.3, G), top, (M + x, G - h * 0.6), 8)
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, stem, 0.22)), _mix(leaf, c["wood"], 0.4))
        # The plume: many fine threads that hang from the top of the stem
        # to one side, soft and pale.
        side = 1.0 if lean >= 0 else -1.0
        threads = [_curve((top[0] - side * j * 0.12, top[1] + j * 0.7), (top[0] + side * (2.4 + j * 0.25), top[1] + 2.6 + j * 0.9), (top[0] + side * (1.2 + j * 0.2), top[1] - 0.6 + j * 0.6), 7) for j in range(6)]
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, pts, 0.36) for pts in threads], blur=0.12), plume, 0.80)
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, pts[:5], 0.14) for pts in threads[1::2]]), (248, 244, 238), 0.7)
    tile.alpha *= tile.y < G


def tsukubai(tile: Tile, c: dict) -> None:
    """A low stone water basin of a garden: a rough round stone with a
    round hollow cut in its top that holds still water, where the sky
    shows. A pipe of bamboo on a short post brings water to it, and small
    round stones lie in front of it."""
    _shadow(tile, 9.0)
    stone = tile.mask(lambda p, dx, dy: (_dot(p, dx, dy, M - 0.4, G - 3.8, 7.4, ry=4.4), _box(p, dx, dy, M - 7.4, G - 3.8, M + 6.6, G)))
    tile.put(stone, c["stone"])
    tile.tone((tile.noise(8, 8, 2) - 0.5) * 0.30 * stone)
    tile.put(stone * (tile.x < M - 3.0) * (tile.y < G - 3.0), c["stone_light"], 0.35)
    tile.put(stone * (tile.y > G - 2.2), c["dark"], 0.30)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M - 0.4, G - 7.2, 4.6, ry=1.4)), _mix(c["stone"], c["dark"], 0.45))
    water = tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M - 0.4, G - 7.0, 3.8, ry=1.0))
    tile.put(water, _mix(c["glow"], c["stone"], 0.25))
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M - 1.4, G - 7.2, 1.6, ry=0.35)), (255, 255, 255), 0.5)
    moss = tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M + x, G - 0.4, r, ry=r * 0.5) for x, r in ((-6.0, 2.4), (-2.0, 1.8), (4.4, 2.6))])
    tile.put(moss * stone * np.clip(tile.noise(10, 10, 2) * 2.0 - 0.4, 0, 1), c["plant"], 0.75)
    bamboo = _mix(c["plant"], (190, 180, 100), 0.35)
    post = tile.mask(lambda p, dx, dy: _box(p, dx, dy, M + 8.0, G - 10.6, M + 9.4, G))
    tile.put(post, _mix(bamboo, c["wood"], 0.4))
    tile.put(post * (tile.x < M + 8.5), c["wood_light"], 0.4)
    pipe = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M + 9.6, G - 11.2), (M + 2.0, G - 10.0), (M + 2.0, G - 9.0), (M + 9.6, G - 10.2)]))
    tile.put(pipe, bamboo)
    tile.put(pipe * (tile.y < G - 10.4 + (M + 9.6 - tile.x) * 0.13), (240, 236, 190), 0.4)
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M + 5.6, G - 10.9, M + 6.0, G - 9.4)), c["dark"], 0.5)
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M + 2.0, G - 9.4), (M + 1.7, G - 7.4)], 0.22)), _mix(c["glow"], (255, 255, 255), 0.3), 0.8)
    for x, r in ((-9.6, 1.2), (-5.0, 0.9), (4.6, 1.0), (9.8, 1.0)):
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + x, G - r * 0.6, r, ry=r * 0.65)), _mix(c["stone"], c["dark"], 0.2))
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + x - r * 0.3, G - r * 0.9, r * 0.4, ry=r * 0.2)), c["stone_light"], 0.5)
    tile.alpha *= tile.y < G


def garden_pine(tile: Tile, c: dict) -> None:
    """A small pine of a garden, trained by its gardener: a crooked trunk
    of red-brown bark, and its needles in flat round pads, each one dark
    under and lit on its top, like small clouds."""
    _shadow(tile, 7.0)
    bark = _mix(c["wood"], (150, 70, 40), 0.25)
    trunk = [(M - 1.0, G), (M - 1.4, G - 4.0), (M + 0.6, G - 8.0), (M - 1.4, G - 12.0), (M - 0.4, G - 16.0)]
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, trunk, 1.5)), bark)
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(x - 0.4, y) for x, y in trunk], 0.4)), _mix(bark, (255, 220, 180), 0.3), 0.6)
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(M - 1.0, G - y), (M + 0.2, G - y - 0.4)], 0.18) for y in (2.0, 5.0, 9.0, 13.0)]), c["dark"], 0.5)
    for a, b in (((M + 0.4, G - 8.0), (M + 5.6, G - 9.6)), ((M - 1.2, G - 11.6), (M - 6.4, G - 13.4)), ((M - 0.6, G - 15.0), (M + 3.0, G - 17.0))):
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [a, b], 0.7)), bark)
    pads = [(M + 5.4, G - 10.2, 4.4, 1.9), (M - 6.0, G - 13.8, 4.6, 2.0), (M + 1.6, G - 17.6, 4.2, 2.1), (M - 1.4, G - 20.0, 2.6, 1.4)]
    green = _mix(c["plant"], (30, 70, 50), 0.35)
    for x, y, rx, ry in pads:
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, x, y + 0.4, rx, ry=ry)), _mix(green, c["dark"], 0.45))
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, x - 0.2, y - 0.3, rx * 0.92, ry=ry * 0.7)), green)
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x + u, y - 0.2), (x + u + 0.5, y - ry * 0.9)], 0.16) for u in np.linspace(-rx * 0.8, rx * 0.8, 9)]), _mix(green, (220, 240, 190), 0.25), 0.45)
    tile.alpha *= tile.y < G


def peonies(tile: Tile, c: dict) -> None:
    """Peonies in flower in early summer, as they grew in the courts of
    the palace: a low bush of deeply cut dark leaves, three full flowers
    of many ruffled pink petals with a pale heart, and a round bud."""
    _shadow(tile, 8.0)
    leaf = c["plant"]
    rng = tile.rng
    mound = [(-4.6, 3.4, 3.6), (0.0, 5.0, 4.4), (4.6, 3.6, 3.6)]
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M + x, G - y, r, ry=r * 0.8) for x, y, r in mound]), _mix(leaf, c["dark"], 0.40))
    leaves = [(M + rng.uniform(-7.4, 7.4), G - rng.uniform(1.6, 8.0), rng.uniform(-1.2, 1.2)) for _ in range(26)]
    for k, (x, y, a) in enumerate(leaves):
        pts = [(x, y + 0.4), (x + math.cos(a - 0.5) * 2.4, y - math.sin(a - 0.5) * 1.2 - 0.6), (x + math.cos(a) * 3.0, y - math.sin(a) * 1.4 - 0.4),
               (x + math.cos(a + 0.5) * 2.4, y - math.sin(a + 0.5) * 1.2 + 0.4), (x, y + 0.8)]
        tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, pts)), _mix(leaf, (230, 240, 190), 0.15) if k % 2 else _mix(leaf, c["dark"], 0.15))
    for x, y, r in ((-4.0, 9.6, 3.2), (2.6, 11.8, 3.6), (5.6, 7.4, 2.6)):
        cx, cy = M + x, G - y
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(cx, cy + r * 0.6), (M + x * 0.5, G - 2.0)], 0.3)), _mix(leaf, c["wood"], 0.3))
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, cx + math.cos(a) * r * 0.55, cy + math.sin(a) * r * 0.42, r * 0.55, ry=r * 0.45) for a in np.linspace(0.0, 2.0 * math.pi, 8, endpoint=False)]), _mix(c["bloom"], c["dark"], 0.25))
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, cx + math.cos(a) * r * 0.35, cy - 0.3 + math.sin(a) * r * 0.28, r * 0.45, ry=r * 0.38) for a in np.linspace(0.3, 2.0 * math.pi + 0.3, 7, endpoint=False)]), c["bloom"])
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, cx + math.cos(a) * r * 0.18, cy - 0.6 + math.sin(a) * r * 0.14, r * 0.3, ry=r * 0.25) for a in np.linspace(0.0, 2.0 * math.pi, 5, endpoint=False)]), _mix(c["bloom"], (255, 236, 240), 0.45))
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, cx, cy - 0.6, r * 0.18)), (250, 222, 140))
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M - 7.0, G - 13.4), (M - 6.0, G - 2.0)], 0.25)), _mix(leaf, c["wood"], 0.3))
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M - 7.0, G - 14.0, 1.2, ry=1.4)), _mix(c["bloom"], c["dark"], 0.2))
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 8.2, G - 13.4), (M - 7.0, G - 12.6), (M - 5.8, G - 13.4), (M - 7.0, G - 13.0)])), leaf)
    tile.alpha *= tile.y < G


def rain_gauge_stand(tile: Tile, c: dict) -> None:
    """The stand of a rain gauge of Joseon: a block of granite cut square,
    with a round socket in its top where the iron cylinder of the gauge
    stood. From 1441 one such gauge stood in each province, and its keeper
    measured the depth of each rain. Here the stand has no cylinder in it.
    The block has a smooth margin cut round each face."""
    _shadow(tile, 7.6)
    x0, x1, top, face = M - 5.0, M + 5.0, G - 13.0, G - 11.2
    body = tile.mask(lambda p, dx, dy: (_box(p, dx, dy, x0, face, x1, G), _poly(p, dx, dy, [(x0, face), (x0 + 1.4, top), (x1 + 1.0, top), (x1, face)])))
    side = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(x1, face), (x1 + 1.0, top), (x1 + 1.0, G - 1.0), (x1, G)]))
    tile.put(body, c["stone"])
    tile.put(side, _mix(c["stone"], c["dark"], 0.35))
    lid = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(x0, face), (x0 + 1.4, top), (x1 + 1.0, top), (x1, face)]))
    tile.put(lid, _mix(c["stone"], c["stone_light"], 0.55))
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + 0.6, (top + face) * 0.5, 2.6, ry=0.65)), c["dark"], 0.75)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + 0.6, (top + face) * 0.5 + 0.25, 2.2, ry=0.4)), _mix(c["stone"], c["dark"], 0.55))
    margin = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 1.0, face + 1.0, x1 - 1.0, G - 1.4))
    tile.put(margin, _mix(c["stone"], c["dark"], 0.08))
    tile.put(margin * (np.abs(((tile.x + tile.y) % 1.1) - 0.55) < 0.12), c["dark"], 0.08)
    tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, x0 + 1.0, face + 1.0, x1 - 1.0, face + 1.3), _box(p, dx, dy, x0 + 1.0, face + 1.0, x0 + 1.3, G - 1.4))), c["dark"], 0.35)
    tile.put(tile.mask(lambda p, dx, dy: (_box(p, dx, dy, x0 + 1.0, G - 1.7, x1 - 1.0, G - 1.4), _box(p, dx, dy, x1 - 1.3, face + 1.0, x1 - 1.0, G - 1.4))), c["stone_light"], 0.5)
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0, face, x1, face + 0.4)), c["stone_light"], 0.6)
    rng = tile.rng
    grains = [(rng.uniform(x0 + 0.3, x1 + 0.6), rng.uniform(top + 0.3, G - 0.3)) for _ in range(40)]
    every = tile.mask(lambda p, dx, dy: (_box(p, dx, dy, x0, face, x1 + 1.0, G), _poly(p, dx, dy, [(x0, face), (x0 + 1.4, top), (x1 + 1.0, top), (x1, face)])))
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, 0.15) for x, y in grains[::2]]) * every, c["dark"], 0.4)
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, 0.16) for x, y in grains[1::2]]) * every, (244, 240, 230), 0.35)
    tile.alpha *= tile.y < G


def roof_tile_fragments(tile: Tile, c: dict) -> None:
    """Pieces of grey fired roof tiles, left where the roofers of the
    palace mended a roof: the broken half of a curved tile seen from its
    end, a flat broken piece, and a round end tile that lies tilted, with
    a raised rim, a ring of small beads and a boss in its middle."""
    _shadow(tile, 9.6)
    tile_grey = c["metal"]
    # The curved tile: a broken piece of a hollow tile that lies on its
    # back, a thick crescent seen from its end, with a jagged break.
    outer = [(M - 10.4 + 8.6 * u, G - 3.4 + 3.2 * (1.0 - (2.0 * u - 1.0) ** 2)) for u in np.linspace(0.0, 1.0, 12)]
    inner = [(M - 9.6 + 7.0 * u, G - 3.6 + 1.6 * (1.0 - (2.0 * u - 1.0) ** 2)) for u in np.linspace(0.0, 1.0, 12)]
    piece = outer + [(M - 1.6, G - 3.8), (M - 2.2, G - 4.4), (M - 2.6, G - 3.6)] + inner[::-1] + [(M - 10.0, G - 3.9)]
    curved = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, piece))
    tile.put(curved, tile_grey)
    tile.put(curved * (tile.y < G - 2.6), _mix(tile_grey, (255, 255, 255), 0.25), 0.6)
    tile.put(curved * (tile.y > G - 1.2), c["dark"], 0.30)
    # The flat broken piece, with a jagged end.
    flat = [(M - 2.4, G), (M - 1.6, G - 1.8), (M + 2.6, G - 2.2), (M + 3.2, G - 1.2), (M + 2.6, G - 0.6), (M + 3.0, G)]
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, flat)), _mix(tile_grey, c["dark"], 0.15))
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M - 1.6, G - 1.8), (M + 2.6, G - 2.2)], 0.25)), _mix(tile_grey, (255, 255, 255), 0.3), 0.7)
    # The round end tile: an ellipse (a disc tilted back) on a short stub.
    cx, cy, rx, ry = M + 6.6, G - 4.0, 4.0, 3.4
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(cx - 2.6, G), (cx - 3.0, cy + 1.0), (cx + 3.6, cy - 1.6), (cx + 4.0, G)])), _mix(tile_grey, c["dark"], 0.35))
    disc = tile.mask(lambda p, dx, dy: _dot(p, dx, dy, cx, cy, rx, ry=ry))
    tile.put(disc, tile_grey)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, cx, cy, rx - 0.8, ry=ry - 0.7)), _mix(tile_grey, c["dark"], 0.25))
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, cx + 0.2, cy + 0.2, rx - 1.0, ry=ry - 0.9)), tile_grey)
    beads = [(cx + math.cos(a) * (rx - 1.8), cy + math.sin(a) * (ry - 1.6)) for a in np.linspace(0.0, 2.0 * math.pi, 8, endpoint=False)]
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, 0.26) for x, y in beads]), _mix(tile_grey, (255, 255, 255), 0.18))
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, cx, cy, 1.0, ry=0.85)), _mix(tile_grey, (255, 255, 255), 0.25))
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, cx + 0.3, cy + 0.3, 0.6, ry=0.5)), c["dark"], 0.35)
    tile.put(disc * (tile.x < cx - rx * 0.5) * (tile.y < cy), (255, 255, 255), 0.12)
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M + x, G - 0.4, 0.5, ry=0.35) for x in (-0.6, 4.4, -10.6)]), tile_grey)
    tile.alpha *= tile.y < G


# Bengal: the Buriganga at Dhaka, Calcutta and the Dhaka spring. On the
# river `metal` is the red of fired clay and `glow` the misty sky in still
# water; at Calcutta `metal` is brass and `bloom` the pink-purple of
# indigo; in the spring `metal` is the dark iron of a bicycle and `bloom`
# the red of the shimul.


def cotton_bolls(tile: Tile, c: dict) -> None:
    """A bush of the cotton of Bengal, from which the thread of the muslin
    was spun: thin woody stems, dark leaves of three to five lobes, a pale
    yellow flower with a dark red eye, and bolls that have split open, each
    a soft white tuft held in a star of dry brown bracts."""
    _shadow(tile, 7.0)
    stem = _mix(c["wood"], c["dark"], 0.2)
    branches = [((M, G), (M - 1.0, G - 9.0), (M - 6.0, G - 15.0)), ((M, G), (M + 0.6, G - 10.0), (M + 6.4, G - 14.0)), ((M, G), (M + 0.2, G - 12.0), (M - 0.6, G - 19.0))]
    for a, ctrl, b in branches:
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, _curve(a, b, ctrl, 8), 0.45)), stem)
    leaf = _mix(c["plant"], c["dark"], 0.15)

    def lobed(x, y, r, turn):
        pts = []
        for k in range(10):
            ang = turn + k * math.pi / 5.0
            rr = r if k % 2 == 0 else r * 0.55
            pts.append((x + math.cos(ang) * rr, y + math.sin(ang) * rr * 0.8))
        return pts

    leaves = [(M - 3.6, G - 8.0, 2.4, 0.3), (M + 3.6, G - 9.4, 2.6, -0.2), (M - 1.0, G - 13.4, 2.2, 0.1), (M + 4.6, G - 4.4, 2.0, 0.5), (M - 5.0, G - 4.0, 2.0, -0.4)]
    for k, (x, y, r, t) in enumerate(leaves):
        tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, lobed(x, y, r, t))), leaf if k % 2 else _mix(leaf, (210, 230, 170), 0.18))
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x, y), (x + math.cos(t + a) * r * 0.8, y + math.sin(t + a) * r * 0.65)], 0.12) for a in (-1.6, 0.0, 1.6)]), c["dark"], 0.35)
    for x, y, r in ((M - 6.0, G - 15.6, 2.2), (M + 6.4, G - 14.6, 2.4), (M - 0.6, G - 19.6, 2.0), (M + 1.6, G - 6.6, 1.8)):
        bract = [(x + math.cos(a) * r * (1.25 if k % 2 == 0 else 0.6), y + 0.6 + math.sin(a) * r * (1.25 if k % 2 == 0 else 0.6) * 0.7) for k, a in enumerate(np.linspace(0.0, 2.0 * math.pi, 10, endpoint=False))]
        tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, bract)), _mix(c["wood"], (150, 110, 70), 0.4))
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x + ox * r, y + oy * r, r * 0.55) for ox, oy in ((-0.35, 0.05), (0.35, 0.0), (0.0, -0.35), (0.0, 0.25))]), (238, 234, 222))
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x + ox * r - 0.2, y + oy * r - 0.3, r * 0.25) for ox, oy in ((-0.35, 0.05), (0.0, -0.35))]), (255, 255, 252), 0.8)
    fx, fy = M + 5.6, G - 8.8
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, fx + math.cos(a) * 1.0, fy + math.sin(a) * 0.8, 1.0) for a in np.linspace(0.0, 2.0 * math.pi, 5, endpoint=False)]), (240, 226, 140))
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, fx, fy, 0.55)), (150, 40, 40))
    tile.alpha *= tile.y < G


def banana_clump(tile: Tile, c: dict) -> None:
    """A young banana plant: a short stem of pale leaf sheaths, and long
    broad leaves with a pale rib that stand up and spread and hang, the
    oldest one torn into strips by the wind."""
    _shadow(tile, 6.0)
    sheath = _mix(c["plant"], (210, 214, 150), 0.35)
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 1.6, G), (M + 1.6, G), (M + 1.0, G - 9.0), (M - 1.0, G - 9.0)])), sheath)
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M - 0.8, G - 0.4), (M - 0.5, G - 8.6)], 0.35)), _mix(sheath, (255, 255, 220), 0.3), 0.6)
    top = (M, G - 9.0)
    blades = (((M - 1.6, G - 20.0), (M - 1.0, G - 21.4), 1.6), ((M + 8.0, G - 18.0), (M + 4.0, G - 20.6), 2.2), ((M - 9.0, G - 15.6), (M - 5.0, G - 19.4), 2.2),
              ((M + 10.4, G - 10.0), (M + 7.0, G - 16.4), 2.0), ((M - 10.2, G - 7.6), (M - 7.4, G - 14.8), 1.9))
    for k, (tip, ctrl, width) in enumerate(blades):
        rib = _curve(top, tip, ctrl, 12)
        left, right = [], []
        for i, (x, y) in enumerate(rib):
            t = i / (len(rib) - 1)
            x0, y0 = rib[max(i - 1, 0)]
            x1, y1 = rib[min(i + 1, len(rib) - 1)]
            n = math.hypot(x1 - x0, y1 - y0) or 1.0
            nx, ny = -(y1 - y0) / n, (x1 - x0) / n
            w = width * math.sin(math.pi * t**0.8)
            left.append((x + nx * w, y + ny * w))
            right.append((x - nx * w, y - ny * w))
        colour = c["plant"] if k % 2 else _mix(c["plant"], c["dark"], 0.18)
        tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, left + right[::-1])), colour)
        tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, left + rib[::-1])), (230, 240, 180), 0.12)
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, rib[:-1], 0.22)), _mix(c["plant"], (240, 240, 190), 0.45))
        if k >= 3:
            cuts = [(rib[i], left[i]) for i in (4, 6, 8, 10)]
            tile.alpha *= 1.0 - tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [((a[0] * 2 + b[0]) / 3, (a[1] * 2 + b[1]) / 3), (b[0] + (b[0] - a[0]) * 0.3, b[1] + (b[1] - a[1]) * 0.3)], 0.16) for a, b in cuts])
            tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, right[7:] + rib[7:][::-1])), _mix(c["wood"], (200, 170, 100), 0.4), 0.5)
    tile.alpha *= tile.y < G


def water_pots(tile: Tile, c: dict) -> None:
    """Pots of fired red clay for water, as women of the river carry on the
    hip: a big round kolshi with a short neck and a rolled rim, a dark band
    painted round its shoulder, and a smaller one beside it, with a small
    clay cup in front."""
    _shadow(tile, 9.0)
    clay = c["metal"]
    for cx, cy, r, neck in ((M - 3.0, G - 7.4, 7.0, 2.4), (M + 6.0, G - 4.6, 4.4, 1.6)):
        body = tile.mask(lambda p, dx, dy: (_dot(p, dx, dy, cx, cy, r, ry=r * 0.98), _box(p, dx, dy, cx - neck, cy - r - 1.6, cx + neck, cy - r + 1.0), _dot(p, dx, dy, cx, cy - r - 1.6, neck * 1.45, ry=0.8)))
        tile.put(body, clay)
        tile.put(body * np.clip(1.0 - ((tile.x - (cx - r * 0.35)) ** 2 + (tile.y - (cy - r * 0.35)) ** 2) / (r * r * 0.35), 0, 1), _mix(clay, (255, 220, 180), 0.45), 0.6)
        tile.put(body * (tile.x > cx + r * 0.35), c["dark"], 0.30)
        tile.put(body * (np.abs(tile.y - (cy - r * 0.45)) < 0.45), _mix(clay, c["dark"], 0.55), 0.8)
        tile.put(body * (np.abs(tile.y - (cy - r * 0.30)) < 0.25), (236, 220, 196), 0.45)
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, cx, cy - r - 1.6, neck * 1.0, ry=0.45)), c["dark"], 0.7)
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 9.6, G - 2.4), (M - 6.0, G - 2.4), (M - 6.6, G), (M - 9.0, G)])), _mix(clay, c["dark"], 0.1))
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M - 7.8, G - 2.4, 1.8, ry=0.5)), c["dark"], 0.55)
    tile.alpha *= tile.y < G


def lotus_pond(tile: Tile, c: dict) -> None:
    """A small pool by the river where lotus grows: still water that shows
    the misty sky, round floating leaves, a leaf that stands up like a cup,
    a pink flower open on its stalk and a closed bud."""
    _shadow(tile, 10.0)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, G - 1.4, 10.6, ry=1.7)), _mix(c["stone"], c["dark"], 0.35))
    water = tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, G - 1.5, 9.8, ry=1.3))
    tile.put(water, c["glow"])
    tile.put(water * (np.abs(tile.y - (G - 1.8)) < 0.2), (255, 255, 255), 0.4)
    leaf = c["plant"]
    for x, y, r in ((M - 5.6, G - 1.6, 2.6), (M + 4.6, G - 1.4, 2.2), (M - 1.0, G - 1.0, 1.6)):
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, x, y, r, ry=r * 0.32)), leaf)
        tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(x, y), (x + r, y - 0.2), (x + r, y + 0.3)])), c["glow"])
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, x - r * 0.2, y - 0.25, r * 0.6, ry=r * 0.12)), _mix(leaf, (220, 240, 190), 0.4), 0.6)
    stalk = _mix(leaf, c["dark"], 0.2)
    for a, b, ctrl in (((M + 1.0, G - 1.4), (M + 1.6, G - 14.0), (M + 0.4, G - 8.0)), ((M - 3.0, G - 1.4), (M - 5.6, G - 10.0), (M - 3.6, G - 6.0)), ((M + 5.0, G - 1.2), (M + 7.0, G - 8.0), (M + 6.6, G - 4.0))):
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, _curve(a, b, ctrl, 8), 0.3)), stalk)
    cup = [(M - 9.0, G - 11.4), (M - 7.4, G - 9.8), (M - 5.6, G - 9.6), (M - 3.6, G - 10.0), (M - 2.4, G - 11.6), (M - 4.0, G - 11.0), (M - 5.6, G - 11.4), (M - 7.4, G - 11.0)]
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, cup)), leaf)
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, cup[4:] + [cup[0]])), _mix(leaf, (220, 240, 190), 0.3), 0.6)
    fx, fy = M + 1.6, G - 14.4
    petals = [(-60.0, 3.4), (-30.0, 4.0), (0.0, 4.4), (30.0, 4.0), (60.0, 3.4)]
    for k, (ang, length) in enumerate(petals):
        a = math.radians(ang - 90.0)
        tip = (fx + math.cos(a) * length, fy + math.sin(a) * length)
        side = (math.cos(a + math.pi / 2) * 1.0, math.sin(a + math.pi / 2) * 1.0)
        pts = [(fx, fy + 0.8), (fx + (tip[0] - fx) * 0.5 + side[0], fy + (tip[1] - fy) * 0.5 + side[1]), tip, (fx + (tip[0] - fx) * 0.5 - side[0], fy + (tip[1] - fy) * 0.5 - side[1])]
        tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, pts)), c["bloom"] if k % 2 == 0 else _mix(c["bloom"], (255, 236, 240), 0.35))
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, fx, fy - 0.6, 0.9, ry=0.6)), (236, 200, 90))
    bx, by = M + 7.0, G - 8.0
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(bx, by - 3.6), (bx + 1.3, by - 1.2), (bx + 0.8, by + 0.2), (bx - 0.8, by + 0.2), (bx - 1.3, by - 1.2)])), _mix(c["bloom"], c["dark"], 0.1))
    tile.alpha *= tile.y < G


def banyan_roots(tile: Tile, c: dict) -> None:
    """A prop root of a banyan: an aerial root that came down from a limb
    above (out of the square, so it fades out at its top), took hold in the
    earth and grew as thick as a trunk. Thinner roots twist round it and
    beside it, and at its foot its roots spread out over the ground and
    grip it."""
    _shadow(tile, 9.0)
    bark = _mix(c["wood"], (150, 140, 120), 0.35)
    light = _mix(bark, (240, 230, 210), 0.35)
    fade = np.clip((tile.y - 1.5) / 8.0, 0, 1)
    pillar = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 2.4, 1.0), (M + 1.8, 1.0), (M + 2.4, G - 6.0), (M + 4.4, G - 2.0), (M + 7.6, G), (M - 7.4, G), (M - 4.2, G - 2.2), (M - 2.8, G - 6.0)]))
    tile.put(pillar * fade, bark)
    furrows = np.abs(((tile.x - M + np.sin(tile.y * 0.6) * 0.4) % 1.3) - 0.65) < 0.14
    tile.put(pillar * fade * furrows, c["dark"], 0.30)
    tile.put(pillar * fade * (tile.x < M - 1.2) * (tile.y < G - 3.0), light, 0.35)
    tile.put(pillar * fade * (tile.x > M + 1.2), c["dark"], 0.25)
    rng = tile.rng
    strands = []
    for x0, x1, width in ((M - 7.0, M - 8.4, 0.5), (M - 4.6, M - 3.2, 0.7), (M + 4.0, M + 3.0, 0.8), (M + 7.4, M + 9.0, 0.45), (M + 0.4, M - 0.6, 0.45)):
        pts = [(x0 + (x1 - x0) * t + math.sin(t * 5.0 + x0) * 0.6, 1.0 + t * (G - 1.6)) for t in np.linspace(0.0, 1.0, 12)]
        strands.append((pts, width + rng.uniform(-0.05, 0.05)))
    roots = tile.mask(lambda p, dx, dy: [_line(p, dx, dy, pts, w) for pts, w in strands])
    tile.put(roots * fade, _mix(bark, c["stone_light"], 0.15))
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x - w * 0.4, y) for x, y in pts], w * 0.35) for pts, w in strands]) * fade, light, 0.45)
    for a, b, ctrl in (((M - 3.0, G - 2.0), (M - 10.6, G - 0.2), (M - 7.0, G - 2.0)), ((M + 3.0, G - 2.0), (M + 10.6, G - 0.2), (M + 7.0, G - 2.2))):
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, _curve(a, b, ctrl, 10), 0.8)), _mix(bark, c["dark"], 0.15))
    tile.alpha *= tile.y < G


def indigo_plant(tile: Tile, c: dict) -> None:
    """A plant of indigo, which the Company made the farmers of Bengal grow
    for its blue dye: a small bush of thin stems with leaves of many small
    oval leaflets in pairs, and short spikes of pink-purple flowers."""
    _shadow(tile, 7.0)
    rng = tile.rng
    stem = _mix(c["plant"], c["wood"], 0.4)
    tips = [(M - 7.6, G - 12.0), (M - 4.0, G - 17.0), (M, G - 19.6), (M + 4.2, G - 16.4), (M + 7.8, G - 11.6), (M - 2.0, G - 13.6), (M + 2.4, G - 13.0)]
    stems = [_curve((M + (tx - M) * 0.15, G), (tx, ty), (M + (tx - M) * 0.35, ty + 6.0), 10) for tx, ty in tips]
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, pts, 0.32) for pts in stems]), stem)
    leaflets = []
    for pts in stems:
        for i in range(3, len(pts) - 1):
            x, y = pts[i]
            for side in (-1.0, 1.0):
                leaflets.append((x + side * 0.9, y + rng.uniform(-0.2, 0.2), side))
    for k, part in enumerate((leaflets[::2], leaflets[1::2])):
        colour = c["plant"] if k else _mix(c["plant"], (210, 236, 190), 0.25)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, 0.85, ry=0.45) for x, y, side in part]), colour)
    for tx, ty in tips[:5]:
        spike = [(tx + rng.uniform(-0.2, 0.2), ty - 0.6 - j * 0.9) for j in range(4)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, 0.55, ry=0.45) for x, y in spike]), c["bloom"])
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x - 0.15, y - 0.15, 0.22) for x, y in spike]), _mix(c["bloom"], (255, 230, 250), 0.5))
    tile.alpha *= tile.y < G


def cotton_bales(tile: Tile, c: dict) -> None:
    """Bales of raw cotton for the ships: pressed hard and sewn into coarse
    jute cloth, bound with ropes, their sides bulging. Two lie on the
    ground and one on top of them, and white cotton shows at a torn
    corner."""
    _shadow(tile, 10.4)
    jute = _mix(c["stone_light"], (196, 170, 120), 0.55)
    rope = _mix(c["wood"], c["dark"], 0.2)
    for x0, y0, x1, y1 in ((M - 10.6, G - 7.0, M - 0.4, G), (M + 0.2, G - 7.0, M + 10.4, G), (M - 6.0, G - 13.8, M + 5.0, G - 7.0)):
        body = tile.mask(lambda p, dx, dy: (_box(p, dx, dy, x0 + 0.6, y0, x1 - 0.6, y1), _box(p, dx, dy, x0, y0 + 0.6, x1, y1 - 0.4)))
        tile.put(body, jute)
        tile.tone((tile.noise(14, 14, 1) - 0.5) * 0.18 * body)
        tile.put(body * (tile.y < y0 + 1.2), (255, 246, 220), 0.30)
        tile.put(body * (tile.x > x1 - 1.6), c["dark"], 0.25)
        weave = (np.abs((tile.x % 0.7) - 0.35) < 0.08) | (np.abs((tile.y % 0.7) - 0.35) < 0.08)
        tile.put(body * weave, c["dark"], 0.06)
        tile.put(body * (np.abs(tile.y - (y0 + y1) * 0.5) < 0.25), c["dark"], 0.20)
        for x in (x0 + (x1 - x0) * 0.28, x0 + (x1 - x0) * 0.72):
            tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(x - 0.3, y0 - 0.1), (x + 0.3, (y0 + y1) * 0.5), (x - 0.2, y1)], 0.55)), rope)
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M + 4.2 + ox, G - 12.8 + oy, 1.0) for ox, oy in ((0.0, 0.0), (-0.6, 0.6), (0.4, 0.8))]), (244, 242, 232))
    tile.alpha *= tile.y < G


def brass_lota(tile: Tile, c: dict) -> None:
    """A brass water pot of a household of Bengal, polished so that it
    shines: a round body, a short waisted neck and a wide flat lip; and
    a small brass cup beside it. It is a pot for water, with nothing in
    it."""
    _shadow(tile, 7.4)
    brass, shine, deep = c["metal"], _mix(c["metal"], (255, 248, 210), 0.6), _mix(c["metal"], c["dark"], 0.5)
    cx, cy, r = M - 1.6, G - 5.6, 5.4
    body = tile.mask(lambda p, dx, dy: (_dot(p, dx, dy, cx, cy, r, ry=r * 0.95), _poly(p, dx, dy, [(cx - 2.0, cy - r * 0.8), (cx + 2.0, cy - r * 0.8), (cx + 1.5, cy - r - 2.2), (cx - 1.5, cy - r - 2.2)]),
                                          _dot(p, dx, dy, cx, cy - r - 2.6, 3.2, ry=0.9), _box(p, dx, dy, cx - 2.2, G - 0.9, cx + 2.2, G)))
    tile.put(body, brass)
    tile.put(body * (tile.x > cx + r * 0.3), deep, 0.45)
    tile.put(body * np.clip(1.0 - ((tile.x - (cx - r * 0.4)) ** 2 + (tile.y - (cy - r * 0.3)) ** 2) / 3.0, 0, 1), shine, 0.85)
    tile.put(body * (np.abs(tile.x - (cx + r * 0.55)) < 0.4) * (np.abs(tile.y - cy) < r * 0.6), shine, 0.35)
    tile.put(body * (np.abs(tile.y - (cy - r * 0.55)) < 0.25), deep, 0.6)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, cx, cy - r - 2.6, 2.4, ry=0.5)), deep)
    ux = M + 7.0
    cup = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(ux - 2.8, G - 3.6), (ux + 2.8, G - 3.6), (ux + 2.0, G - 0.6), (ux + 1.0, G), (ux - 1.0, G), (ux - 2.0, G - 0.6)]))
    tile.put(cup, brass)
    tile.put(cup * (tile.x > ux + 0.8), deep, 0.45)
    tile.put(cup * (tile.x < ux - 0.8) * (tile.y > G - 3.0), shine, 0.6)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, ux, G - 3.6, 2.8, ry=0.5)), deep)
    tile.alpha *= tile.y < G


def _shimul_flower(tile: Tile, c: dict, x: float, y: float, r: float, turn: float, open_: bool) -> None:
    """One shimul flower as it lies on the ground: five thick red petals
    in a deep cup on a dark green calyx, and, when it lies open, the bunch
    of stamens in its heart."""
    red = c["bloom"]
    if open_:
        petals = [(x + math.cos(turn + k * 2.0 * math.pi / 5.0) * r * 0.55, y + math.sin(turn + k * 2.0 * math.pi / 5.0) * r * 0.35) for k in range(5)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, px, py, r * 0.55, ry=r * 0.38) for px, py in petals]), _mix(red, c["dark"], 0.15))
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, px - 0.15, py - 0.15, r * 0.40, ry=r * 0.25) for px, py in petals]), red)
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, x, y, r * 0.30, ry=r * 0.22)), (236, 196, 90))
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, x, y, r * 0.14, ry=r * 0.10)), (120, 60, 30))
    else:
        # On its side: a bell of petals that opens out from a dark calyx,
        # with the rounded tips of the petals curled back at its mouth.
        side = 1.0 if math.cos(turn) >= 0 else -1.0
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, x - side * r * 0.75, y, r * 0.42, ry=r * 0.38)), (66, 74, 40))
        bell = [(x - side * r * 0.6, y - r * 0.30), (x + side * r * 0.5, y - r * 0.62), (x + side * r * 0.9, y - r * 0.82), (x + side * r * 1.05, y - r * 0.3),
                (x + side * r * 1.1, y + r * 0.2), (x + side * r * 0.9, y + r * 0.45), (x - side * r * 0.6, y + r * 0.25)]
        tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, bell)), red)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x + side * r * 1.0, y + oy * r, r * 0.26) for oy in (-0.55, -0.05, 0.38)]), _mix(red, (255, 190, 160), 0.35))
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(x - side * r * 0.4, y - r * 0.18), (x + side * r * 0.7, y - r * 0.45)], 0.22)), _mix(red, (255, 200, 170), 0.5), 0.7)
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(x - side * r * 0.4, y + r * 0.08), (x + side * r * 0.8, y + r * 0.12)], 0.16)), _mix(red, c["dark"], 0.45), 0.6)


def shimul_fall(tile: Tile, c: dict) -> None:
    """Shimul flowers that fell on the grass of the campus in February: the
    red silk-cotton tree drops its big fleshy flowers whole, some on their
    side and some face up, and a few loose petals."""
    _shadow(tile, 9.0)
    rng = tile.rng
    flowers = [(M - 6.0, G - 1.6, 2.6, rng.uniform(0, math.pi), False), (M + 1.0, G - 2.4, 3.0, rng.uniform(0, math.pi), True),
               (M + 7.2, G - 1.4, 2.4, math.pi, False), (M - 1.6, G - 0.9, 2.0, 0.3, False)]
    flowers.sort(key=lambda f: f[1])
    for x, y, r, turn, open_ in flowers:
        _shimul_flower(tile, c, x, y, r, turn, open_)
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M + x, G - 0.5, 0.9, ry=0.4) for x in (-9.6, 4.0, 9.8)]), c["bloom"])
    tile.alpha *= tile.y < G


def marigold_bed(tile: Tile, c: dict) -> None:
    """Marigolds in flower: a clump of fine, deeply cut dark leaves and
    round, full heads of many petals, orange and yellow, as they are grown
    in beds and strung in garlands for the spring."""
    _shadow(tile, 8.0)
    rng = tile.rng
    leaf = c["plant"]
    heads = [(M - 6.0, G - 9.0, 2.4, 0), (M - 1.6, G - 13.0, 2.8, 1), (M + 3.4, G - 10.6, 2.6, 0), (M + 7.0, G - 7.0, 2.2, 1), (M - 3.0, G - 6.0, 2.0, 1), (M + 1.4, G - 6.4, 2.2, 0)]
    for x, y, r, k in heads:
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(x, y + r * 0.6), (M + (x - M) * 0.4, G)], 0.35)), _mix(leaf, c["dark"], 0.2))
    fronds = [(M + rng.uniform(-8.0, 8.0), G - rng.uniform(1.0, 7.0), rng.uniform(-1.0, 1.0)) for _ in range(16)]
    for k, (x, y, a) in enumerate(fronds):
        pts = [(x + math.cos(a) * t * 3.0 + (0.5 if j % 2 else -0.5) * math.sin(a), y - math.sin(a) * t * 1.5 - 0.6 * t + (0.4 if j % 2 else -0.4) * math.cos(a)) for j, t in enumerate(np.linspace(0.0, 1.0, 7))]
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, pts, 0.42)), leaf if k % 2 else _mix(leaf, (200, 230, 160), 0.2))
    for x, y, r, k in heads:
        colour = (236, 132, 24) if k else (246, 186, 40)
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, x, y, r, ry=r * 0.85)), _mix(colour, c["dark"], 0.25))
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x + math.cos(a) * r * 0.45, y + math.sin(a) * r * 0.38, r * 0.45) for a in np.linspace(0.0, 2.0 * math.pi, 7, endpoint=False)]), colour)
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, x - r * 0.2, y - r * 0.25, r * 0.4)), _mix(colour, (255, 240, 170), 0.45))
        ruffle = (np.abs(((np.arctan2(tile.y - y, tile.x - x) * 4.0) % 1.0) - 0.5) < 0.12) * tile.mask(lambda p, dx, dy: _dot(p, dx, dy, x, y, r * 0.9))
        tile.put(ruffle, _mix(colour, c["dark"], 0.3), 0.4)
    tile.alpha *= tile.y < G


def parked_bicycle(tile: Tile, c: dict) -> None:
    """A black bicycle that a student left on its stand by the path: two
    thin wheels with spokes, a frame of two triangles, a saddle, the
    handlebar, and a basket of woven cane on the front."""
    _shadow(tile, 10.0)
    iron = c["metal"]
    r = 4.2
    back, front = (M - 6.0, G - r), (M + 6.0, G - r)
    for wx, wy in (back, front):
        tile.put(tile.mask(lambda p, dx, dy: p.ellipse([(wx - r) * K + dx, (wy - r) * K + dy, (wx + r) * K + dx, (wy + r) * K + dy], outline=255, width=max(1, int(0.7 * K)))), _mix(iron, c["dark"], 0.3))
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(wx, wy), (wx + math.cos(a) * r, wy + math.sin(a) * r)], 0.10) for a in np.linspace(0.0, 2.0 * math.pi, 12, endpoint=False)]), c["stone_light"], 0.45)
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, wx, wy, 0.5)), c["stone_light"], 0.8)
    crank = (M - 0.6, G - r)
    seat = (M - 2.2, G - 11.0)
    head = (M + 4.0, G - 11.4)
    frame = [[back, crank], [crank, seat], [seat, back], [crank, (head[0] - 0.2, head[1] + 1.4)], [seat, (head[0] - 0.2, head[1] + 0.6)], [head, front]]
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, pts, 0.55) for pts in frame]), iron)
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(a[0], a[1] - 0.2), (b[0], b[1] - 0.2)], 0.15) for a, b in frame]), c["stone_light"], 0.35)
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(seat[0] - 1.8, seat[1] - 0.6), (seat[0] + 1.6, seat[1] - 0.8), (seat[0] + 1.0, seat[1] + 0.2), (seat[0] - 1.6, seat[1] + 0.2)])), c["dark"])
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(head[0] - 1.4, head[1] - 1.0), (head[0], head[1]), (head[0] + 1.2, head[1] - 0.4)], 0.40)), iron)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, crank[0], crank[1], 1.0)), iron)
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [crank, (crank[0] + 1.2, crank[1] + 1.8)], 0.35)), iron)
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(back[0] + 1.0, back[1] + 0.6), (back[0] + 2.2, G)], 0.3)), iron)
    cane = c["wood"]
    basket = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(head[0] + 0.6, head[1] + 0.6), (head[0] + 4.6, head[1] + 0.6), (head[0] + 4.0, head[1] + 4.0), (head[0] + 1.2, head[1] + 4.0)]))
    tile.put(basket, cane)
    tile.put(basket * ((np.abs(((tile.x - tile.y) % 1.0) - 0.5) < 0.15) | (np.abs(((tile.x + tile.y) % 1.0) - 0.5) < 0.15)), c["dark"], 0.35)
    tile.alpha *= tile.y < G


def book_stack(tile: Tile, c: dict) -> None:
    """A pile of books that a student set down on the grass: five books of
    each size in plain cloth covers, their page edges cream, and on their
    spines a neat line of short strokes and blocks where the title would
    be (no real letters)."""
    _shadow(tile, 8.6)
    rng = tile.rng
    covers = ((116, 60, 50), (60, 84, 104), (92, 104, 64), (140, 110, 60), (96, 56, 74))
    y = G
    for k, (h, w, shift) in enumerate(((2.6, 15.0, 0.0), (2.2, 13.0, -1.0), (2.8, 14.0, 1.2), (2.0, 11.4, -0.6), (2.4, 12.6, 0.4))):
        x0, x1 = M - w * 0.5 + shift, M + w * 0.5 + shift
        cover = covers[k % len(covers)]
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0, y - h, x1, y)), cover)
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x1 - 2.6, y - h + 0.4, x1 - 0.2, y - 0.4)), (236, 226, 200))
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x1 - 2.6, yy, x1 - 0.2, yy + 0.16) for yy in np.arange(y - h + 0.6, y - 0.4, 0.4)]), (180, 168, 140), 0.6)
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0, y - h, x1, y - h + 0.4)), _mix(cover, (255, 255, 255), 0.25))
        strokes = []
        x = x0 + 1.4
        while x < x1 - 4.4:
            ww = rng.uniform(0.3, 0.9)
            strokes.append((x, ww))
            x += ww + rng.uniform(0.25, 0.5)
        mid = y - h * 0.5
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, sx, mid - 0.35, sx + ww, mid + 0.35) for sx, ww in strokes]), (226, 200, 130), 0.75)
        y -= h
    tile.alpha *= tile.y < G


# Brazil: Marajó, Palmares and Rio de Janeiro. On Marajó `metal` is the
# red of fired clay and `bloom` the red of the heliconia; at Palmares
# `metal` is fired clay and `bloom` the gold of maize; in Rio `metal` is
# the dark green paint of iron and `bloom` the pink of bougainvillea.


def _palmate(x: float, y: float, r: float, turn: float, lobes: int = 7) -> list[list[tuple[float, float]]]:
    """The lobes of a palmate leaf, as of manioc: narrow blades that spread
    like the fingers of a hand from one point."""
    blades = []
    for k in range(lobes):
        a = turn + (k - (lobes - 1) * 0.5) * 0.42
        tip = (x + math.cos(a) * r, y + math.sin(a) * r)
        side = (math.cos(a + math.pi * 0.5) * r * 0.13, math.sin(a + math.pi * 0.5) * r * 0.13)
        mid = (x + math.cos(a) * r * 0.5, y + math.sin(a) * r * 0.5)
        blades.append([(x, y), (mid[0] + side[0], mid[1] + side[1]), tip, (mid[0] - side[0], mid[1] - side[1])])
    return blades


def manioc_plant(tile: Tile, c: dict) -> None:
    """A manioc plant, the staple crop of the Amazon and of Palmares: thin
    knotty stems, red at their tips, and leaves like an open hand, each of
    five to seven narrow lobes on a long red stalk."""
    _shadow(tile, 7.0)
    stem = _mix(c["wood"], (150, 60, 50), 0.35)
    stems = [((M, G), (M - 1.0, G - 9.0), (M - 4.4, G - 15.6)), ((M + 0.4, G), (M + 1.2, G - 8.0), (M + 4.6, G - 14.0)), ((M - 0.2, G), (M + 0.2, G - 10.6), (M + 0.6, G - 18.2))]
    for a, ctrl, b in stems:
        pts = _curve(a, b, ctrl, 8)
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, pts, 0.55)), stem)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, 0.55) for x, y in pts[2:7:2]]), _mix(stem, c["dark"], 0.3))
    leaf = _mix(c["plant"], c["dark"], 0.10)
    for k, (x, y, r, turn) in enumerate(((M - 4.4, G - 15.6, 4.4, -2.2), (M + 4.6, G - 14.0, 4.2, -0.9), (M + 0.6, G - 18.2, 3.8, -1.57), (M - 5.6, G - 8.4, 3.4, -2.6), (M + 5.4, G - 7.6, 3.2, -0.5))):
        blades = _palmate(x, y, r, turn)
        tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, b) for b in blades]), leaf if k % 2 else _mix(leaf, (220, 236, 170), 0.18))
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [b[0], b[2]], 0.12) for b in blades]), _mix(leaf, (240, 230, 190), 0.35), 0.6)
    tile.alpha *= tile.y < G


def heliconia_clump(tile: Tile, c: dict) -> None:
    """A heliconia of the edge of the forest: three long paddle leaves on
    tall stalks, and between them a chain of red bracts with yellow tips
    that hangs from its stalk, turned left and right in turn."""
    _shadow(tile, 7.0)
    leaf = _mix(c["plant"], c["dark"], 0.15)
    for base, tip, ctrl, width in (((M - 0.6, G), (M - 9.0, G - 20.0), (M - 3.0, G - 14.0), 2.2), ((M + 0.6, G), (M + 9.4, G - 19.0), (M + 3.0, G - 14.0), 2.2),
                                   ((M - 0.2, G), (M - 3.2, G - 22.6), (M - 1.0, G - 13.0), 1.8)):
        rib = _curve(base, tip, ctrl, 14)
        left, right = [], []
        for i, (x, y) in enumerate(rib):
            t = i / (len(rib) - 1)
            w = width * math.sin(math.pi * min(1.0, max(0.0, (t - 0.35) / 0.65))) if t > 0.35 else 0.35
            (x0, y0), (x1, y1) = rib[max(i - 1, 0)], rib[min(i + 1, len(rib) - 1)]
            n = math.hypot(x1 - x0, y1 - y0) or 1.0
            nx, ny = -(y1 - y0) / n, (x1 - x0) / n
            left.append((x + nx * w, y + ny * w))
            right.append((x - nx * w, y - ny * w))
        tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, left + right[::-1])), leaf)
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, rib[5:], 0.18)), _mix(leaf, (230, 236, 180), 0.35), 0.7)
    stalk = _curve((M + 0.4, G), (M + 2.6, G - 19.0), (M + 1.0, G - 12.0), 8)
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, stalk, 0.45)), _mix(c["plant"], c["dark"], 0.3))
    x0, y = M + 2.6, G - 19.0
    for i in range(5):
        side = 1.0 if i % 2 == 0 else -1.0
        size = 3.0 - i * 0.25
        bract = [(x0, y), (x0 + side * size * 1.25, y - size * 0.40), (x0 + side * size * 1.35, y + size * 0.15), (x0, y + size * 0.62)]
        tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, bract)), c["bloom"])
        tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, bract[:2] + [(x0 + side * size * 0.4, y + size * 0.05)])), _mix(c["bloom"], (255, 220, 200), 0.3), 0.6)
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, x0 + side * size * 1.25, y - size * 0.32, 0.55)), (242, 206, 72))
        y += size * 0.70
    tile.alpha *= tile.y < G


def pottery_sherds(tile: Tile, c: dict) -> None:
    """Broken pieces of Marajoara pots on the dark earth, as they lie in
    terra preta: a large curved piece of a bowl with its rim, painted with
    bands of red and black on a white slip, and smaller plain pieces round
    it."""
    _shadow(tile, 8.0)
    slip, red, black = (232, 220, 196), _mix(c["metal"], (160, 40, 30), 0.3), (44, 32, 28)
    # The big piece lies flat: a low, broken outline, its rim along its top.
    body = [(M - 7.4, G), (M - 6.6, G - 2.6), (M - 3.0, G - 3.8), (M + 1.6, G - 3.6), (M + 4.6, G - 2.2), (M + 5.4, G)]
    shard = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, body))
    tile.put(shard, slip)
    tile.put(shard * (tile.y > G - 1.0), c["dark"], 0.25)
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, body[1:5], 0.8)), red)
    steps = [(M - 5.6, G - 1.2), (M - 4.4, G - 1.2), (M - 4.4, G - 2.4), (M - 3.0, G - 2.4), (M - 3.0, G - 1.2), (M - 1.6, G - 1.2), (M - 1.6, G - 2.4), (M - 0.2, G - 2.4),
             (M - 0.2, G - 1.2), (M + 1.2, G - 1.2), (M + 1.2, G - 2.4), (M + 2.6, G - 2.4)]
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, steps, 0.35)) * shard, black)
    for x, y, w, colour in ((M + 6.4, G - 1.2, 2.4, c["metal"]), (M - 8.6, G - 1.0, 1.8, _mix(c["metal"], slip, 0.5)), (M + 9.2, G - 0.8, 1.4, c["metal"])):
        piece = [(x - w, G), (x - w * 0.6, y - w * 0.4), (x + w * 0.7, y - w * 0.2), (x + w, G)]
        tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, piece)), colour)
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, piece[1:3], 0.25)), (255, 236, 210), 0.4)
    tile.alpha *= tile.y < G


def charcoal_basket(tile: Tile, c: dict) -> None:
    """A basket woven of palm leaf, full of charcoal and broken pots: what a
    gardener of the Amazon dug into the earth to make terra preta. The
    weave goes over and under, and a black heap of charcoal with a few red
    pieces of pot shows over its rim."""
    _shadow(tile, 8.0)
    body = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 7.6, G - 10.0), (M + 7.6, G - 10.0), (M + 6.0, G), (M - 6.0, G)]))
    heap = tile.mask(lambda p, dx, dy: (_dot(p, dx, dy, M - 3.0, G - 10.6, 3.6, ry=2.4), _dot(p, dx, dy, M + 2.6, G - 10.8, 4.0, ry=2.8), _dot(p, dx, dy, M, G - 12.0, 3.0, ry=2.4)))
    tile.put(heap, (30, 28, 30))
    lumps = [(M - 4.0, G - 11.6), (M - 1.0, G - 13.0), (M + 2.6, G - 12.6), (M + 5.0, G - 10.8), (M + 0.6, G - 11.0)]
    tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, 0.5) for x, y in lumps]), (130, 130, 140), 0.6)
    tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, [(x - 1.0, y + 0.4), (x, y - 0.8), (x + 1.2, y), (x + 0.4, y + 0.8)]) for x, y in ((M - 1.8, G - 11.0), (M + 3.6, G - 11.6))]), c["metal"])
    straw = _mix(c["wood"], (214, 184, 120), 0.45)
    tile.put(body, straw)
    weave = ((np.floor((tile.x - M) / 1.6) + np.floor((tile.y - G) / 1.6)) % 2 == 0)
    tile.put(body * weave, _mix(straw, c["dark"], 0.35), 0.6)
    tile.put(body * (tile.x > M + 3.0), c["dark"], 0.25)
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 7.8, G - 10.6, M + 7.8, G - 9.2)), _mix(straw, c["dark"], 0.15))
    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 7.8, G - 10.6, M + 7.8, G - 10.1)), (240, 220, 170), 0.5)
    tile.alpha *= tile.y < G


def maize_stalks(tile: Tile, c: dict) -> None:
    """Three stalks of maize in a field of Palmares: tall jointed stalks,
    long blades that arch out and hang, a tassel at the top of each, and
    an ear in its husk, with silk at its tip, on the side of one."""
    _shadow(tile, 6.0)
    leaf = _mix(c["plant"], c["dark"], 0.10)
    for x, h, lean in ((M - 4.0, 17.6, -0.8), (M + 0.6, 19.8, 0.4), (M + 5.0, 16.0, 1.2)):
        top = (x + lean, G - h)
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(x, G), top], 0.6)), _mix(leaf, (200, 200, 120), 0.25))
        for k in range(4):
            t = 0.25 + k * 0.17
            bx, by = x + lean * t, G - h * t
            side = -1.0 if (k + int(x)) % 2 else 1.0
            blade = _curve((bx, by), (bx + side * 4.6, by + 1.8), (bx + side * 2.4, by - 3.0), 10)
            tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, blade, 0.55)), leaf if k % 2 else _mix(leaf, (230, 236, 170), 0.15))
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [top, (top[0] + dxx, top[1] - 2.6)], 0.25) for dxx in (-1.2, -0.4, 0.4, 1.2)]), c["bloom"])
    ex, ey = M + 1.0, G - 11.0
    tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(ex, ey + 3.0), (ex + 1.4, ey + 1.6), (ex + 2.4, ey - 3.4), (ex + 1.0, ey - 2.4)])), _mix(c["plant"], (230, 220, 150), 0.5))
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(ex + 2.2, ey - 3.2), (ex + 3.0, ey - 4.6)], 0.25)), (176, 110, 60))
    tile.alpha *= tile.y < G


def palmares_pots(tile: Tile, c: dict) -> None:
    """Pots of a village of Palmares, made of the red clay of the hill: a
    big round pot for water with a wide mouth, a dark band burnished on
    its shoulder, and a small cooking pot black with soot from the fire,
    beside it a wooden ladle."""
    _shadow(tile, 9.0)
    clay = c["metal"]
    for cx, cy, r, mouth, sooty in ((M - 2.6, G - 7.0, 6.8, 3.4, False), (M + 6.2, G - 3.8, 3.8, 2.6, True)):
        body = tile.mask(lambda p, dx, dy: (_dot(p, dx, dy, cx, cy, r, ry=r * 0.95), _box(p, dx, dy, cx - mouth, cy - r - 1.0, cx + mouth, cy - r + 1.4), _dot(p, dx, dy, cx, cy - r - 1.0, mouth * 1.15, ry=0.8)))
        colour = _mix(clay, (40, 30, 28), 0.70) if sooty else clay
        tile.put(body, colour)
        tile.put(body * np.clip(1.0 - ((tile.x - (cx - r * 0.35)) ** 2 + (tile.y - (cy - r * 0.35)) ** 2) / (r * r * 0.35), 0, 1), _mix(colour, (255, 220, 180), 0.40), 0.55)
        tile.put(body * (tile.x > cx + r * 0.35), c["dark"], 0.30)
        if not sooty:
            tile.put(body * (np.abs(tile.y - (cy - r * 0.50)) < 0.7), _mix(clay, c["dark"], 0.45), 0.8)
            tile.put(body * (np.abs(tile.y - (cy - r * 0.50)) < 0.18), (255, 230, 200), 0.4)
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, cx, cy - r - 1.0, mouth * 0.85, ry=0.45)), c["dark"], 0.75)
    tile.put(tile.mask(lambda p, dx, dy: (_line(p, dx, dy, [(M + 9.0, G - 7.4), (M + 6.6, G - 0.4)], 0.45), _dot(p, dx, dy, M + 6.4, G - 0.9, 1.0, ry=0.6))), c["wood"])
    tile.alpha *= tile.y < G


def berimbau_post(tile: Tile, c: dict) -> None:
    """A berimbau, a musical bow of Central African origin, that leans on a
    post: a long bow of wood, bent by a thin wire from end to end, and a
    round gourd tied near its foot, with its open face to the bow. A
    short forked post of wood holds it up."""
    _shadow(tile, 6.0)
    post = tile.mask(lambda p, dx, dy: (_box(p, dx, dy, M + 2.0, G - 14.0, M + 3.6, G), _line(p, dx, dy, [(M + 2.4, G - 13.6), (M + 1.0, G - 16.2)], 0.6), _line(p, dx, dy, [(M + 3.2, G - 13.6), (M + 4.4, G - 16.0)], 0.6)))
    tile.put(post, _mix(c["wood"], c["dark"], 0.25))
    tile.put(post * (tile.x < M + 2.6), _mix(c["wood"], (240, 220, 180), 0.3), 0.6)
    foot, top = (M - 5.0, G - 0.4), (M + 3.2, G - 22.6)
    bow = _curve(foot, top, (M - 3.6, G - 13.0), 14)
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, bow, 0.65)), c["wood"])
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [foot, top], 0.15)), (170, 170, 176))
    gx, gy = M - 2.6, G - 5.4
    gourd = tile.mask(lambda p, dx, dy: _dot(p, dx, dy, gx, gy, 2.8, ry=3.0))
    tile.put(gourd, _mix(c["wood"], (214, 170, 100), 0.55))
    tile.put(gourd * (tile.x > gx + 0.8), c["dark"], 0.30)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, gx - 0.8, gy - 1.0, 0.8)), (255, 240, 200), 0.35)
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(gx - 1.0, gy - 2.6), (gx + 1.8, gy - 3.4)], 0.25)), c["dark"], 0.7)
    tile.alpha *= tile.y < G


def bunting_line(tile: Tile, c: dict) -> None:
    """Bunting for the thirteenth of May: a line of small pennants, green
    and yellow in turn, that hangs between two short poles."""
    _shadow(tile, 9.0)
    for x in (M - 9.4, M + 9.4):
        pole = tile.mask(lambda p, dx, dy: (_box(p, dx, dy, x - 0.45, G - 16.0, x + 0.45, G), _dot(p, dx, dy, x, G - 16.2, 0.7)))
        tile.put(pole, c["wood"])
        tile.put(pole * (tile.x < x), (255, 240, 210), 0.3)
    line = _curve((M - 9.4, G - 15.0), (M + 9.4, G - 15.0), (M, G - 9.0), 12)
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, line, 0.18)), c["dark"], 0.8)
    for i in range(1, len(line) - 1):
        x, y = line[i]
        colour = (36, 128, 68) if i % 2 else (248, 206, 48)
        tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(x - 0.75, y), (x + 0.75, y), (x + 0.1, y + 2.4)])), colour)
    tile.alpha *= tile.y < G


def petal_scatter(tile: Tile, c: dict) -> None:
    """Petals on the pavement after the flowers of the day: pink bracts of
    bougainvillea, thin and papery, and a few yellow petals, lying flat
    and scattered, more of them near the middle."""
    rng = tile.rng
    for _ in range(16):
        x = min(M + 9.0, max(M - 9.0, M + rng.gauss(0.0, 4.6)))
        y = G - rng.uniform(0.3, 1.6)
        r = rng.uniform(0.8, 1.4)
        turn = rng.uniform(0.0, math.pi)
        colour = c["bloom"] if rng.random() < 0.75 else (246, 206, 80)
        pts = [(x + math.cos(turn + k * math.pi / 3.0) * r * (1.0 if k % 3 == 0 else 0.55), y + math.sin(turn + k * math.pi / 3.0) * r * 0.35) for k in range(6)]
        tile.put(tile.mask(lambda p, dx, dy: _poly(p, dx, dy, pts)), colour)
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [pts[0], pts[3]], 0.12)), _mix(colour, (255, 255, 255), 0.4), 0.5)
    tile.alpha *= tile.y < G


def gas_lamp(tile: Tile, c: dict) -> None:
    """A gas street lamp of Rio in the 1880s: a fluted iron post painted
    dark green on a round base, and on it a lantern of four panes of glass
    under a small roof with a finial, lit by its flame."""
    _shadow(tile, 2.8)
    post = tile.mask(lambda p, dx, dy: (_box(p, dx, dy, M - 0.7, G - 15.0, M + 0.7, G), _box(p, dx, dy, M - 1.8, G - 2.2, M + 1.8, G), _dot(p, dx, dy, M, G - 2.2, 1.6, ry=0.8),
                                        _box(p, dx, dy, M - 1.4, G - 15.6, M + 1.4, G - 15.0)))
    tile.put(post, c["metal"])
    tile.put(post * (tile.x < M - 0.2), _mix(c["metal"], (200, 220, 200), 0.3), 0.5)
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M, G - 18.0, 3.8), blur=1.2), c["glow"], 0.40)
    glass = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 1.6, G - 15.6), (M + 1.6, G - 15.6), (M + 2.3, G - 20.4), (M - 2.3, G - 20.4)]))
    tile.put(glass, _mix(c["glow"], (255, 255, 255), 0.35))
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M, G - 15.6), (M, G - 20.4)], 0.2)) * glass, c["metal"], 0.8)
    tile.put(tile.mask(lambda p, dx, dy: (_poly(p, dx, dy, [(M - 2.9, G - 20.4), (M + 2.9, G - 20.4), (M, G - 22.4)]), _dot(p, dx, dy, M, G - 22.6, 0.5))), c["metal"])
    tile.alpha *= tile.y < G


def palm_tub(tile: Tile, c: dict) -> None:
    """A young palm in a tub of painted wood with iron hoops, as stood at
    the doors of Rio for a feast: a short trunk and fronds that arch out
    and hang, with fine leaflets."""
    _shadow(tile, 6.0)
    tub = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 5.0, G - 7.0), (M + 5.0, G - 7.0), (M + 4.0, G), (M - 4.0, G)]))
    tile.put(tub, c["wood"])
    tile.put(tub * (np.abs(((tile.x - M) % 2.0) - 1.0) < 0.15), c["dark"], 0.35)
    tile.put(tub * (tile.x > M + 2.0), c["dark"], 0.30)
    tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, M - 5.0, y, M + 5.0, y + 0.7) for y in (G - 6.0, G - 2.0)]) * tub, c["metal"])
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M, G - 7.0), (M + 0.3, G - 12.0)], 0.9)), _mix(c["wood"], (140, 110, 80), 0.5))
    top = (M + 0.3, G - 12.0)
    leaf = _mix(c["plant"], c["dark"], 0.1)
    for k, (tx, ty) in enumerate(((-9.0, -6.0), (-7.0, -9.4), (-2.0, -11.0), (3.0, -10.6), (7.4, -8.4), (9.6, -4.4))):
        tip = (top[0] + tx, top[1] + ty * 0.35 + abs(tx) * 0.55)
        ctrl = (top[0] + tx * 0.5, top[1] + ty * 0.9)
        rib = _curve(top, tip, ctrl, 10)
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, rib, 0.35)), leaf)
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x, y), (x + 0.5, y + 1.6)], 0.22) for x, y in rib[2:]] + [_line(p, dx, dy, [(x, y), (x - 0.5, y + 1.6)], 0.22) for x, y in rib[2:]]),
                 leaf if k % 2 else _mix(leaf, (220, 236, 170), 0.18))
    tile.alpha *= tile.y < G


# Japan: Hakata Bay in 1281 and Tokyo in 1872. At Hakata Bay `metal` is
# the dark of the floats of a net and `bloom` the red of a banner; in Tokyo
# `metal` is the dark iron of a lamp and `bloom` the pale canvas of the
# mail sacks.


def kobo_grass(tile: Tile, c: dict) -> None:
    """Beach grass of the dunes of Hakata Bay (kobo-shiba): low tufts of
    narrow stiff blades that fan out and bend over, along a runner that
    creeps on the sand from one tuft to the next."""
    _shadow(tile, 8.0)
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(M - 8.0, G - 0.4), (M - 3.0, G - 0.7), (M + 3.6, G - 0.5), (M + 8.4, G - 0.6)], 0.35)), _mix(c["wood"], c["plant"], 0.4))
    leaf = _mix(c["plant"], c["dark"], 0.10)
    for k, (x, h) in enumerate(((M - 5.8, 6.4), (M - 0.2, 8.6), (M + 5.8, 5.6))):
        blades = []
        for j in range(9):
            lean = (j - 4) * 0.50
            top = (x + lean * 1.1, G - h * (1.0 - abs(j - 4) * 0.07))
            tip = (top[0] + lean * 0.9, top[1] + abs(lean) * 0.7)
            blades.append(_curve((x + (j - 4) * 0.12, G), tip, (x + lean * 0.3, top[1] - 0.6), 8))
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, pts, 0.42) for pts in blades[::2]]), leaf)
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, pts, 0.42) for pts in blades[1::2]]), _mix(leaf, (226, 230, 160), 0.22))
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, pts[:4], 0.16) for pts in blades[::3]]), (236, 230, 180), 0.35)
    tile.alpha *= tile.y < G


def pine_seedling(tile: Tile, c: dict) -> None:
    """A young black pine that has seeded itself in the sand behind the
    beach: a short trunk that leans and bends, and three flat tiers of
    dark needles in tufts, the widest at the bottom."""
    _shadow(tile, 6.0)
    trunk = _curve((M - 0.6, G), (M + 1.6, G - 16.0), (M - 1.4, G - 8.0), 10)
    bark = _mix(c["wood"], c["dark"], 0.35)
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, trunk, 1.0)), bark)
    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(x - 0.3, y) for x, y in trunk], 0.3)), _mix(c["wood"], (230, 210, 170), 0.3), 0.5)
    needle = _mix(c["plant"], c["dark"], 0.30)
    for k, (t, half, side) in enumerate(((0.45, 7.0, -1.0), (0.70, 5.6, 1.0), (0.95, 3.8, 0.0))):
        x, y = trunk[int(round(t * 9))]
        cx = x + side * 1.8
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(x, y), (cx, y - 0.6)], 0.45)), bark)
        tufts = [(cx + (j - 2) * half * 0.40, y - 0.8 - (1.0 - abs(j - 2) / 2.0) * 1.2) for j in range(5)]
        body = tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, tx, ty, half * 0.32, ry=1.4) for tx, ty in tufts])
        tile.put(body, needle)
        tile.put(body * tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(tx, ty), (tx + math.cos(a) * 1.6, ty - math.sin(a) * 1.2)], 0.18) for tx, ty in tufts for a in (0.6, 1.2, 1.9, 2.5)]), _mix(c["plant"], (220, 230, 170), 0.35), 0.6)
        tile.put(body * (tile.y > y + 0.2), c["dark"], 0.30)
    tile.alpha *= tile.y < G


def borui_stones(tile: Tile, c: dict) -> None:
    """A heap of stones carried up from the beach for the wall: round
    stones of the shore and split blocks of granite and sandstone, piled
    by hand, the big ones at the foot."""
    _shadow(tile, 9.0)
    stones = [(-6.4, 2.0, 2.8, 0.00, False), (-1.6, 2.4, 3.2, -0.10, True), (3.6, 2.0, 2.8, 0.12, False), (7.8, 1.4, 2.0, -0.06, False),
              (-4.0, 5.6, 2.6, 0.10, True), (1.0, 6.0, 2.8, 0.04, False), (5.4, 5.0, 2.2, -0.12, True), (-1.4, 9.2, 2.4, 0.14, False), (2.8, 9.0, 1.8, -0.04, True)]
    for x, y, r, tone, split in stones:
        hue = _mix(c["stone"], (186, 156, 116), 0.5) if tone > 0.08 else c["stone"]
        colour = _mix(hue, c["stone_light"] if tone > 0 else c["dark"], abs(tone) * 1.8)
        if split:
            pts = [(M + x - r, G - y + r * 0.8), (M + x - r * 0.8, G - y - r * 0.7), (M + x + r * 0.6, G - y - r * 0.85), (M + x + r, G - y + r * 0.1), (M + x + r * 0.7, G - y + r * 0.8)]
            body = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, pts))
            tile.put(body, colour)
            tile.put(body * tile.mask(lambda p, dx, dy: _poly(p, dx, dy, pts[1:3] + [(M + x, G - y)])), c["stone_light"], 0.40)
        else:
            body = tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + x, G - y, r, ry=r * 0.82))
            tile.put(body, colour)
            tile.put(body * tile.mask(lambda p, dx, dy: _dot(p, dx, dy, M + x - r * 0.3, G - y - r * 0.35, r * 0.5, ry=r * 0.35)), c["stone_light"], 0.40)
        tile.put(body * (tile.y > G - y + r * 0.35), c["dark"], 0.30)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, M + x + r * dxx, G - y + r * dyy, 0.18) for dxx, dyy in ((-0.3, 0.1), (0.2, -0.2), (0.4, 0.3))]) * body, c["dark"], 0.5)
    tile.alpha *= tile.y < G


def tate_shields(tile: Tile, c: dict) -> None:
    """Two standing shields (tate) of the warriors of Kamakura, set up in a
    row on the wall: tall plain boards of planks joined by two battens,
    each held upright by a prop of wood behind it. They bear no crest."""
    _shadow(tile, 9.0)
    for x0, top, tone in ((M - 8.4, G - 15.0, 0.0), (M + 0.6, G - 16.4, -0.08)):
        x1 = x0 + 7.6
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(x1 - 1.6, top + 3.0), (x1 + 2.4, G)], 0.55)), _mix(c["wood"], c["dark"], 0.45))
        board = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(x0, G), (x0 + 0.3, top), (x1 - 0.3, top), (x1, G)]))
        colour = _mix(c["wood"], c["dark"], -tone * 2.0) if tone < 0 else c["wood"]
        tile.put(board, colour)
        tile.put(board * (np.abs(((tile.x - x0) % 2.53) - 1.26) > 1.08), c["dark"], 0.40)
        tile.put(board * (tile.x < x0 + 0.9), c["wood_light"], 0.45)
        tile.put(board * np.clip((tile.noise(3, 14, 2) - 0.5) * 2.0, 0, 1), c["dark"], 0.18)
        for y in (top + 2.4, G - 4.0):
            batten = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 0.3, y, x1 - 0.3, y + 1.3)) * board
            tile.put(batten, _mix(c["wood"], c["dark"], 0.25))
            tile.put(batten * (tile.y < y + 0.4), c["wood_light"], 0.45)
        tile.put(board * (tile.y > G - 1.2), c["dark"], 0.25)
    tile.alpha *= tile.y < G


def telegraph_pole(tile: Tile, c: dict) -> None:
    """A telegraph pole of 1872 by the railway: a tall plain post of wood,
    two short cross arms near its top, each with two white insulators of
    porcelain, and the wires that sag away from them each way."""
    _shadow(tile, 2.4)
    post = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(M - 0.75, G), (M + 0.75, G), (M + 0.5, G - 21.6), (M - 0.5, G - 21.6)]))
    tile.put(post, c["wood"])
    tile.put(post * (tile.x < M - 0.1), c["wood_light"], 0.45)
    tile.put(post * np.clip((tile.noise(2, 16, 2) - 0.5) * 2.0, 0, 1), c["dark"], 0.25)
    for y in (G - 20.4, G - 17.6):
        tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, M - 3.8, y, M + 3.8, y + 0.8)), _mix(c["wood"], c["dark"], 0.25))
        for x in (M - 3.0, M + 3.0):
            tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, _curve((x, y - 0.6), (x + (6.6 if x > M else -6.6), y + 0.4), (x + (3.0 if x > M else -3.0), y + 1.4), 8), 0.14)), c["dark"], 0.7)
            tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, x, y - 0.5, 0.5, ry=0.65)), c["stone_light"])
    tile.alpha *= tile.y < G


def mail_sacks(tile: Tile, c: dict) -> None:
    """Sacks of the new post (1871) by the station, ready for the train:
    three plump sacks of pale canvas, tied at the neck with cord, two on
    the ground and one laid over them, each with a dark band of paint on
    it and no writing."""
    _shadow(tile, 9.0)
    canvas = c["bloom"]
    for x, y, rx, ry, tilt in ((M - 4.2, G - 3.8, 4.6, 3.8, -0.2), (M + 4.4, G - 3.6, 4.4, 3.6, 0.15), (M + 0.2, G - 9.0, 5.2, 3.0, 0.0)):
        body = tile.mask(lambda p, dx, dy: _dot(p, dx, dy, x, y, rx, ry=ry))
        neck = (x + rx * 0.95, y - ry * 0.3 + tilt * 2.0)
        ear = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(neck[0] - 0.8, neck[1] - 1.0), (neck[0] + 2.2, neck[1] - 1.8), (neck[0] + 2.0, neck[1] + 0.9), (neck[0] - 0.8, neck[1] + 1.0)]))
        tile.put(np.maximum(body, ear), canvas)
        tile.put(body * (tile.y > y + ry * 0.35), c["dark"], 0.25)
        tile.put(body * tile.mask(lambda p, dx, dy: _dot(p, dx, dy, x - rx * 0.3, y - ry * 0.35, rx * 0.45, ry=ry * 0.35)), (255, 252, 240), 0.35)
        tile.put(body * (np.abs(tile.x - (x - rx * 0.15)) < 0.9), _mix(c["dark"], (60, 70, 110), 0.5), 0.6)
        tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(neck[0] + 0.2, neck[1] - 1.2), (neck[0] + 0.4, neck[1] + 1.1)], 0.35)), c["wood"])
        tile.put(body * tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x - rx * 0.5, y + ry * 0.1), (x - rx * 0.2, y + ry * 0.4)], 0.14), _line(p, dx, dy, [(x + rx * 0.2, y - ry * 0.4), (x + rx * 0.5, y - ry * 0.1)], 0.14)]), c["dark"], 0.35)
    tile.alpha *= tile.y < G


def parked_rickshaw(tile: Tile, c: dict) -> None:
    """A rickshaw (jinrikisha) of the streets of Tokyo, new in 1870, that
    waits with its shafts down on the ground: a big wheel with thin spokes,
    a seat with a back on springs over it, its hood folded back, and two
    long shafts that rest on the street in front."""
    _shadow(tile, 9.0)
    wx, wy, r = M - 0.6, G - 6.0, 5.8
    lacquer = _mix(c["dark"], (60, 30, 28), 0.5)
    tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(wx + 2.4, wy - 2.6), (M + 10.4, G - 0.4)], 0.5), _line(p, dx, dy, [(wx + 2.0, wy - 1.8), (M + 10.2, G - 0.2)], 0.3)]), c["wood"])
    seat = tile.mask(lambda p, dx, dy: (_poly(p, dx, dy, [(wx - 4.6, wy - 4.0), (wx + 3.2, wy - 4.0), (wx + 2.6, wy - 1.8), (wx - 4.0, wy - 1.8)]),
                                       _poly(p, dx, dy, [(wx - 4.6, wy - 4.0), (wx - 3.4, wy - 4.0), (wx - 4.2, wy - 9.6), (wx - 5.6, wy - 9.4)])))
    tile.put(seat, lacquer)
    tile.put(seat * (tile.y < wy - 3.4), c["stone_light"], 0.25)
    hood = tile.mask(lambda p, dx, dy: _poly(p, dx, dy, [(wx - 5.4, wy - 10.2)] + [(wx - 5.4 - 3.4 * math.sin(t), wy - 10.2 + 5.4 * (1.0 - math.cos(t))) for t in np.linspace(0.0, math.pi * 0.5, 7)] + [(wx - 4.6, wy - 4.4)]))
    tile.put(hood, _mix(c["dark"], c["wood"], 0.30))
    tile.put(hood * (np.abs(((tile.y - wy) % 1.6) - 0.8) < 0.18), c["dark"], 0.5)
    rim = tile.mask(lambda p, dx, dy: p.ellipse([(wx - r) * K + dx, (wy - r) * K + dy, (wx + r) * K + dx, (wy + r) * K + dy], outline=255, width=max(1, int(0.7 * K))))
    spokes = tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(wx, wy), (wx + math.cos(a) * r, wy + math.sin(a) * r)], 0.18) for a in np.linspace(0.0, math.tau, 13)[:-1]])
    tile.put(spokes, c["wood"], 0.9)
    tile.put(rim, c["metal"])
    tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, wx, wy, 0.9)), c["metal"])
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
    # The Strait: storage jars of China, coiled rope, sacks of pepper and a
    # mooring post on the wharf. Borobudur: ferns, a stone under moss,
    # lotus buds in a stone basin and a fallen carved block. Angkor: lotus,
    # a young sugar palm, pieces of a sandstone lintel and a glazed jar.
    "history_strait": ((trade_jar, rope_coil, pepper_sacks, mooring_post, trade_jar, pepper_sacks),
                       _palette((40, 30, 22), (176, 150, 106), (222, 204, 160), (104, 76, 52), (116, 100, 56), (80, 112, 60), (44, 34, 30), (255, 226, 160))),
    "history_borobudur": ((fern, lotus_basin, fallen_block, moss_stone, fern, fallen_block),
                          _palette((34, 38, 34), (128, 128, 124), (190, 188, 180), (96, 78, 58), (150, 140, 120), (70, 118, 62), (236, 168, 180), (255, 226, 176))),
    "history_angkor": ((lotus, sugar_palm_sapling, sandstone_fragments, stone_jar, lotus, sugar_palm_sapling),
                       _palette((46, 32, 26), (184, 160, 154), (230, 212, 204), (112, 80, 56), (150, 78, 54), (78, 122, 64), (234, 150, 172), (255, 214, 140))),
    # Sannai-Maruyama: chestnut burrs, ferns, mushrooms on an old log, a
    # heap of clam shells. Taiwan: millet, pandanus, river stones, a pebble
    # of green nephrite. Gyeongju: maple leaves, pine cones, granite chips
    # and a plain stone lantern.
    "history_jomon": ((chestnut_burrs, fern, log_mushrooms, clam_heap, fern, chestnut_burrs),
                      _palette((30, 22, 16), (120, 112, 100), (216, 208, 192), (112, 64, 34), (150, 132, 66), (96, 124, 54), (196, 96, 40), (255, 200, 130))),
    "history_taiwan": ((millet_heads, pandanus, beach_stones, jade_pebble, pandanus, millet_heads),
                       _palette((30, 36, 30), (120, 124, 116), (198, 200, 188), (120, 84, 52), (70, 152, 104), (86, 142, 64), (214, 172, 72), (255, 230, 170))),
    "history_gyeongju": ((maple_leaves, pine_cones, granite_fragments, seokdeung, maple_leaves, pine_cones),
                         _palette((40, 30, 26), (168, 160, 148), (222, 216, 204), (150, 72, 42), (110, 80, 50), (96, 128, 60), (200, 48, 36), (255, 214, 150))),
    # West Lake: weeping willows, tea bushes, a plain stone lantern and red
    # paper lanterns on a stand. Heian-kyo: fallen maple leaves, pampas
    # grass, a stone water basin and a trained pine. Hanyang: peonies,
    # pine cones, the granite stand of a rain gauge and pieces of tiles.
    "history_hangzhou": ((willow_sapling, tea_bush, song_stone_lantern, lantern_stand, tea_bush, willow_sapling),
                         _palette((34, 38, 34), (150, 152, 148), (210, 212, 206), (104, 80, 58), (52, 46, 44), (130, 166, 74), (196, 48, 38), (255, 212, 150))),
    "history_heian": ((momiji_drift, pampas_grass, tsukubai, garden_pine, momiji_drift, pampas_grass),
                      _palette((36, 28, 26), (138, 134, 126), (204, 198, 186), (96, 64, 44), (60, 58, 56), (100, 120, 64), (198, 52, 36), (214, 226, 232))),
    "history_hanyang": ((peonies, pine_cones, rain_gauge_stand, roof_tile_fragments, peonies, pine_cones),
                        _palette((40, 34, 30), (170, 166, 158), (226, 222, 212), (112, 74, 48), (100, 102, 108), (80, 124, 60), (222, 96, 132), (255, 222, 160))),
    # The Buriganga: cotton bolls, banana plants, clay water pots and a
    # lotus pool. Calcutta: the roots of a banyan, indigo, bales of cotton
    # and a brass water pot. The Dhaka spring: fallen shimul flowers,
    # marigolds, a bicycle and a pile of books.
    "history_dhaka_river": ((cotton_bolls, banana_clump, water_pots, lotus_pond, cotton_bolls, banana_clump),
                            _palette((34, 30, 24), (150, 130, 104), (214, 200, 170), (110, 80, 54), (178, 92, 58), (88, 132, 60), (236, 150, 170), (200, 212, 206))),
    "history_calcutta": ((banyan_roots, indigo_plant, cotton_bales, brass_lota, indigo_plant, cotton_bales),
                         _palette((36, 30, 26), (176, 160, 140), (226, 214, 196), (120, 96, 74), (206, 164, 72), (62, 100, 64), (172, 98, 150), (255, 220, 160))),
    "history_dhaka_spring": ((shimul_fall, marigold_bed, parked_bicycle, book_stack, marigold_bed, shimul_fall),
                             _palette((40, 30, 26), (190, 176, 160), (236, 226, 210), (150, 116, 70), (52, 54, 60), (80, 128, 58), (214, 42, 34), (255, 222, 160))),
    # Marajó: manioc, heliconias, broken painted pots and a basket of
    # charcoal. Palmares: maize, manioc, pots of red clay and a berimbau.
    # Rio: bunting, fallen petals, a gas lamp and a palm in a tub.
    "history_marajo": ((manioc_plant, heliconia_clump, pottery_sherds, charcoal_basket, heliconia_clump, manioc_plant),
                       _palette((30, 26, 22), (150, 130, 104), (214, 200, 170), (112, 82, 56), (186, 96, 58), (82, 132, 60), (206, 52, 40), (255, 210, 156))),
    "history_palmares": ((maize_stalks, manioc_plant, palmares_pots, berimbau_post, maize_stalks, manioc_plant),
                         _palette((40, 28, 22), (170, 150, 126), (226, 210, 180), (128, 90, 58), (178, 90, 54), (90, 136, 60), (230, 196, 96), (255, 214, 150))),
    "history_rio_1888": ((bunting_line, petal_scatter, gas_lamp, palm_tub, petal_scatter, bunting_line),
                         _palette((36, 36, 38), (196, 192, 184), (240, 236, 228), (120, 84, 56), (40, 70, 52), (78, 130, 66), (214, 70, 140), (255, 226, 160))),
    # Hakata Bay: beach grass, a heap of stones for the wall, standing
    # shields, a pine seedling, a net and a coil of rope. Tokyo: a young
    # willow, a gas lamp, mail sacks, a telegraph pole and a rickshaw.
    "history_kamakura": ((kobo_grass, borui_stones, tate_shields, pine_seedling, fishing_net, rope_coil),
                         _palette((36, 30, 26), (150, 142, 128), (214, 204, 186), (128, 102, 74), (64, 58, 54), (86, 122, 70), (176, 64, 48), (255, 214, 150))),
    "history_meiji": ((willow_sapling, gas_lamp, mail_sacks, telegraph_pole, parked_rickshaw, willow_sapling),
                      _palette((36, 32, 32), (176, 170, 160), (232, 226, 214), (112, 84, 60), (40, 44, 42), (100, 138, 74), (222, 210, 184), (255, 224, 160))),
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
    gas_lamp: (M, 18.2, 0.34),
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
    seokdeung: (M, 12.6, 0.30),
    song_stone_lantern: (M, 11.0, 0.30),
    lantern_stand: (M, 13.0, 0.34),
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
