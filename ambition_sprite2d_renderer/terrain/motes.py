"""The motes of each biome: the small things that drift in its air.

A mote picture is a strip of `VARIANTS` squares of `CELL` px. The game makes
many small sprites, each one a square of the strip, and moves them
(`ambient_motes` in `ambition_render`): dust in the lab, embers in the
foundry, fireflies in the forest, bubbles in the water.

A mote is light on a clear ground. It has no hard edge: it is small on the
screen, and a hard edge of a small moving thing flickers.
"""

from __future__ import annotations

import math

import numpy as np
from PIL import Image

RGB = tuple[int, int, int]

CELL = 32
VARIANTS = 4
SUPERSAMPLE = 4


def _cell() -> tuple[np.ndarray, np.ndarray]:
    n = CELL * SUPERSAMPLE
    ys, xs = np.mgrid[0:n, 0:n]
    return (xs + 0.5) / n - 0.5, (ys + 0.5) / n - 0.5


def _soft(x: np.ndarray, y: np.ndarray, r: float, power: float = 2.0, squash: float = 1.0) -> np.ndarray:
    d = np.sqrt((x / squash) ** 2 + y**2) / r
    return np.clip(1.0 - d, 0.0, 1.0) ** power


def _dot(colour: RGB, variant: int) -> tuple[np.ndarray, RGB]:
    x, y = _cell()
    r = (0.16, 0.24, 0.32, 0.40)[variant]
    return _soft(x, y, r, 1.6) * (1.0, 0.85, 0.7, 0.5)[variant], colour


def _glow(colour: RGB, variant: int) -> tuple[np.ndarray, RGB]:
    """A bright core in a wide soft light: an ember, a firefly."""
    x, y = _cell()
    core = (0.07, 0.09, 0.11, 0.06)[variant]
    squash = (1.0, 1.0, 0.7, 1.6)[variant]
    return np.clip(_soft(x, y, 0.46, 2.6) * 0.55 + _soft(x, y, core * 2.0, 1.2, squash), 0.0, 1.0), colour


def _twinkle(colour: RGB, variant: int) -> tuple[np.ndarray, RGB]:
    """A point with four thin rays."""
    x, y = _cell()
    reach = (0.30, 0.38, 0.46, 0.24)[variant]
    turn = (0.0, 0.0, math.pi / 4.0, 0.0)[variant]
    rx = x * math.cos(turn) - y * math.sin(turn)
    ry = x * math.sin(turn) + y * math.cos(turn)
    rays = np.maximum(
        np.clip(1.0 - np.abs(ry) / 0.022, 0, 1) * np.clip(1.0 - np.abs(rx) / reach, 0, 1) ** 2,
        np.clip(1.0 - np.abs(rx) / 0.022, 0, 1) * np.clip(1.0 - np.abs(ry) / reach, 0, 1) ** 2,
    )
    return np.clip(rays + _soft(x, y, 0.12, 1.4) + _soft(x, y, 0.4, 3.0) * 0.35, 0.0, 1.0), colour


def _bubble(colour: RGB, variant: int) -> tuple[np.ndarray, RGB]:
    x, y = _cell()
    r = (0.20, 0.28, 0.36, 0.44)[variant]
    d = np.sqrt(x * x + y * y)
    ring = np.clip(1.0 - np.abs(d - r) / 0.035, 0.0, 1.0)
    inside = (d < r) * 0.12
    shine = _soft(x + r * 0.42, y + r * 0.42, r * 0.34, 1.2) * 0.9
    return np.clip(ring * 0.8 + inside + shine, 0.0, 1.0), colour


def _petal(colour: RGB, variant: int) -> tuple[np.ndarray, RGB]:
    x, y = _cell()
    turn = (0.3, 1.2, 2.2, -0.7)[variant]
    rx = x * math.cos(turn) - y * math.sin(turn)
    ry = x * math.sin(turn) + y * math.cos(turn)
    half = (0.34, 0.30, 0.38, 0.26)[variant]
    width = 0.13 * np.clip(1.0 - (rx / half) ** 2, 0.0, 1.0) ** 0.6
    leaf = np.clip((width - np.abs(ry)) / 0.03, 0.0, 1.0) * (np.abs(rx) < half)
    return leaf * 0.92, colour


def _speck(colour: RGB, variant: int) -> tuple[np.ndarray, RGB]:
    """A small point of white with almost no light round it: a speck of a
    star that the void ate."""
    x, y = _cell()
    r = (0.10, 0.13, 0.16, 0.08)[variant]
    return np.clip(_soft(x, y, r, 1.1) * 1.3 + _soft(x, y, r * 2.4, 2.4) * 0.25, 0.0, 1.0), colour


def _strokes(lines: list[list[tuple[float, float]]], width: float, glow: float) -> np.ndarray:
    """Soft strokes through `lines` (each in the coordinates of a cell, the
    middle at 0), with a faint light round them."""
    x, y = _cell()
    near = np.full(x.shape, 9.0)
    for pts in lines:
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            dx, dy = x1 - x0, y1 - y0
            t = np.clip(((x - x0) * dx + (y - y0) * dy) / max(dx * dx + dy * dy, 1e-9), 0.0, 1.0)
            near = np.minimum(near, np.hypot(x - x0 - t * dx, y - y0 - t * dy))
    core = np.clip(1.0 - (near - width) / 0.03, 0.0, 1.0)
    return np.clip(core + np.clip(1.0 - near / 0.2, 0.0, 1.0) ** 2 * glow, 0.0, 1.0)


def _letter(colour: RGB, variant: int) -> tuple[np.ndarray, RGB]:
    """A letter that floats: A, V, K or M, a little turned."""
    shapes = (
        [[(-0.16, 0.20), (0.0, -0.22), (0.16, 0.20)], [(-0.09, 0.05), (0.09, 0.05)]],
        [[(-0.18, -0.18), (0.0, 0.20), (0.18, -0.18)]],
        [[(-0.12, -0.22), (-0.12, 0.22)], [(0.14, -0.22), (-0.12, 0.02), (0.14, 0.22)]],
        [[(-0.20, 0.20), (-0.20, -0.20), (0.0, 0.06), (0.20, -0.20), (0.20, 0.20)]],
    )[variant]
    turn = (0.2, -0.3, 0.1, -0.15)[variant]
    c, s = math.cos(turn), math.sin(turn)
    lines = [[(px * c - py * s, px * s + py * c) for px, py in stroke] for stroke in shapes]
    return _strokes(lines, 0.022, 0.25), colour


def _note(colour: RGB, variant: int) -> tuple[np.ndarray, RGB]:
    """A small note that glows: a head, a stem, and a flag or a beam."""
    x, y = _cell()
    heads = ((-0.06, 0.14),) if variant != 2 else ((-0.16, 0.16), (0.12, 0.10))
    mask = np.zeros_like(x)
    for hx, hy in heads:
        rx, ry = x - hx, y - hy
        u = rx * math.cos(0.45) + ry * math.sin(0.45)
        v = -rx * math.sin(0.45) + ry * math.cos(0.45)
        mask = np.maximum(mask, np.clip(1.0 - (np.sqrt((u / 0.085) ** 2 + (v / 0.06) ** 2) - 1.0) / 0.25, 0.0, 1.0))
    if variant == 2:
        lines = [[(-0.085, 0.14), (-0.085, -0.18)], [(0.195, 0.08), (0.195, -0.24)], [(-0.085, -0.18), (0.195, -0.24)]]
    elif variant == 3:
        lines = [[(0.015, 0.12), (0.015, -0.22)]]
    else:
        lines = [[(0.015, 0.12), (0.015, -0.22), (0.12, -0.10), (0.14, 0.0)]]
        if variant == 1:
            lines.append([(0.015, -0.14), (0.12, -0.02)])
    return np.clip(np.maximum(mask, _strokes(lines, 0.012, 0.0)) + _soft(x, y, 0.45, 2.4) * 0.35, 0.0, 1.0), colour


def _confetti(colour: RGB, variant: int) -> tuple[np.ndarray, RGB]:
    """A bit of confetti: a small strip of paper, turned."""
    x, y = _cell()
    turn = (0.5, -0.9, 1.6, 0.1)[variant]
    rx = x * math.cos(turn) - y * math.sin(turn)
    ry = x * math.sin(turn) + y * math.cos(turn)
    half = ((0.16, 0.06), (0.12, 0.08), (0.20, 0.05), (0.10, 0.10))[variant]
    strip = np.clip((half[0] - np.abs(rx)) / 0.03, 0.0, 1.0) * np.clip((half[1] - np.abs(ry)) / 0.03, 0.0, 1.0)
    return np.clip(strip * 0.95 + _soft(x, y, 0.40, 2.6) * 0.2, 0.0, 1.0), colour


def _chaff(colour: RGB, variant: int) -> tuple[np.ndarray, RGB]:
    """A seed or a bit of chaff on the wind: a small grain, a little turned,
    with a fine whisker off its end."""
    x, y = _cell()
    turn = (0.4, -0.6, 1.2, -1.4)[variant]
    rx = x * math.cos(turn) - y * math.sin(turn)
    ry = x * math.sin(turn) + y * math.cos(turn)
    half = (0.10, 0.13, 0.08, 0.11)[variant]
    grain = np.clip(1.0 - (np.sqrt((rx / half) ** 2 + (ry / (half * 0.42)) ** 2) - 1.0) / 0.35, 0.0, 1.0)
    whisker = np.clip(1.0 - np.abs(ry) / 0.012, 0.0, 1.0) * (rx > half * 0.8) * (rx < half * 0.8 + 0.20)
    return np.clip(grain + whisker * 0.7 + _soft(x, y, 0.36, 2.6) * 0.2, 0.0, 1.0), colour


def _feather(colour: RGB, variant: int) -> tuple[np.ndarray, RGB]:
    """A small feather of a gull that turns as it falls: a quill and a
    vane that is wider on one side."""
    x, y = _cell()
    turn = (0.6, -0.4, 1.4, -1.1)[variant]
    rx = x * math.cos(turn) - y * math.sin(turn)
    ry = x * math.sin(turn) + y * math.cos(turn)
    half = (0.30, 0.26, 0.34, 0.22)[variant]
    along = np.clip(1.0 - (rx / half) ** 2, 0.0, 1.0)
    vane = np.clip((0.09 * along**0.7 - np.abs(ry - 0.02 * along)) / 0.025, 0.0, 1.0) * (np.abs(rx) < half)
    quill = np.clip(1.0 - np.abs(ry) / 0.012, 0.0, 1.0) * (np.abs(rx) < half * 1.15)
    return np.clip(vane * 0.85 + quill, 0.0, 1.0), colour


def _flake(colour: RGB, variant: int) -> tuple[np.ndarray, RGB]:
    """A flake of snow: six arms, each with two small branches, a little
    turned."""
    reach = (0.20, 0.26, 0.16, 0.23)[variant]
    turn = (0.0, 0.3, 0.6, 0.15)[variant]
    lines = []
    for k in range(6):
        a = turn + k * math.pi / 3.0
        ca, sa = math.cos(a), math.sin(a)
        lines.append([(0.0, 0.0), (ca * reach, sa * reach)])
        for side in (-1.0, 1.0):
            b = a + side * 0.8
            base = (ca * reach * 0.55, sa * reach * 0.55)
            lines.append([base, (base[0] + math.cos(b) * reach * 0.3, base[1] + math.sin(b) * reach * 0.3)])
    return _strokes(lines, 0.012, 0.35), colour


def _raindrop(colour: RGB, variant: int) -> tuple[np.ndarray, RGB]:
    """A drop of the monsoon rain: a short thin streak that leans with the
    wind."""
    length = (0.20, 0.26, 0.16, 0.30)[variant]
    lean = (0.30, 0.25, 0.35, 0.28)[variant]
    top = (lean * length * 0.5, -length * 0.5)
    return _strokes([[top, (-top[0], -top[1])]], 0.010, 0.25), colour


def _butterfly(colour: RGB, variant: int) -> tuple[np.ndarray, RGB]:
    """A small butterfly of the rainforest, its wings open, or half shut
    as it beats them: two round upper wings and two smaller lower ones on
    a thin body."""
    x, y = _cell()
    turn = (0.2, -0.3, 0.5, -0.1)[variant]
    open_ = (1.0, 0.55, 0.8, 0.3)[variant]
    rx = x * math.cos(turn) - y * math.sin(turn)
    ry = x * math.sin(turn) + y * math.cos(turn)
    wings = np.zeros_like(rx)
    for side in (-1.0, 1.0):
        wings = np.maximum(wings, _soft(rx - side * 0.13 * open_, ry + 0.06, 0.14, 0.6, squash=open_ * 0.9 + 0.1))
        wings = np.maximum(wings, _soft(rx - side * 0.09 * open_, ry - 0.10, 0.10, 0.6, squash=open_ * 0.9 + 0.1))
    body = np.clip(1.0 - np.abs(rx) / 0.018, 0.0, 1.0) * (np.abs(ry) < 0.14)
    return np.clip(np.clip(wings * 3.0, 0.0, 1.0) * 0.9 + body, 0.0, 1.0), colour


def _dust_spark(colour: RGB, variant: int) -> tuple[np.ndarray, RGB]:
    """Fine warm dust in the air, and now and then a spark from a furnace.
    Three variants are grains of dust: small and soft. The fourth is a
    spark: a bright core with a short soft tail."""
    x, y = _cell()
    if variant < 3:
        r = (0.07, 0.10, 0.13)[variant]
        return _soft(x, y, r, 1.4) * (0.9, 0.75, 0.6)[variant] + _soft(x, y, r * 2.2, 2.4) * 0.15, colour
    tail = np.clip(1.0 - np.abs(x) / 0.025, 0.0, 1.0) * np.clip((y + 0.02) / 0.24, 0.0, 1.0) * (y < 0.24)
    return np.clip(_soft(x, y, 0.06, 1.0) * 1.4 + _soft(x, y, 0.20, 2.6) * 0.45 + tail * 0.5, 0.0, 1.0), colour


def _fluff(colour: RGB, variant: int) -> tuple[np.ndarray, RGB]:
    """A seed that the wind carries on a tuft of fine hairs, as the seeds
    of grasses and of the silk-cotton tree drift over the plain. A small
    seed, and a soft fan of hairs that opens up from it. The fourth variant
    is a loose puff of fluff with no seed."""
    x, y = _cell()
    if variant == 3:
        return np.clip(_soft(x, y, 0.20, 1.6) * 0.55 + _soft(x + 0.05, y - 0.03, 0.12, 1.4) * 0.4, 0.0, 1.0), colour
    turn = (0.2, -0.5, 0.9)[variant]
    rx = x * math.cos(turn) - y * math.sin(turn)
    ry = x * math.sin(turn) + y * math.cos(turn)
    seed = _soft(rx, ry - 0.10, 0.045, 1.2, squash=0.6)
    # The hairs: thin rays from the seed up and out, in a fan.
    angle = np.arctan2(ry - 0.10, rx)
    reach = np.sqrt(rx**2 + (ry - 0.10) ** 2)
    fan = np.clip(1.0 - np.abs(angle + math.pi / 2.0) / 1.0, 0.0, 1.0)
    rays = np.clip(np.cos(angle * 18.0) * 0.5 + 0.5, 0.0, 1.0) ** 3
    hairs = fan * rays * np.clip(1.0 - reach / 0.30, 0.0, 1.0) * (reach > 0.03)
    halo = _soft(rx, ry + 0.04, 0.24, 2.0) * 0.30
    return np.clip(seed * 1.2 + hairs * 0.65 + halo, 0.0, 1.0), colour


def _spray(colour: RGB, variant: int) -> tuple[np.ndarray, RGB]:
    """Fine spray of the sea that the wind carries in off the surf: a very
    small round drop with a faint mist round it. The drops are of three
    sizes; the fourth variant is a loose puff of mist with a few drops in
    it."""
    x, y = _cell()
    if variant == 3:
        drops = sum(_soft(x - dx, y - dy, 0.05, 1.4) for dx, dy in ((-0.12, 0.04), (0.08, -0.10), (0.14, 0.09)))
        return np.clip(_soft(x, y, 0.26, 1.8) * 0.35 + drops * 0.9, 0.0, 1.0), colour
    r = (0.05, 0.07, 0.09)[variant]
    return np.clip(_soft(x, y, r, 1.3) * 1.1 + _soft(x, y, r * 3.2, 2.2) * 0.30, 0.0, 1.0), colour


def _frost(colour: RGB, variant: int) -> tuple[np.ndarray, RGB]:
    """Grains of snow and frost that the cold wind of the high plain lifts
    and carries: a very small hard grain with a little soft light round it,
    in three sizes. The fourth variant is a glint: a grain that catches the
    low sun, with four short thin rays."""
    x, y = _cell()
    if variant == 3:
        rays = np.maximum(np.clip(1.0 - np.abs(y) / 0.018, 0, 1) * np.clip(1.0 - np.abs(x) / 0.26, 0, 1) ** 2,
                          np.clip(1.0 - np.abs(x) / 0.018, 0, 1) * np.clip(1.0 - np.abs(y) / 0.26, 0, 1) ** 2)
        return np.clip(rays * 0.9 + _soft(x, y, 0.07, 1.2) * 1.2 + _soft(x, y, 0.24, 2.4) * 0.25, 0.0, 1.0), colour
    r = (0.05, 0.07, 0.09)[variant]
    return np.clip(_soft(x, y, r, 1.2, squash=0.8) * 1.2 + _soft(x, y, r * 2.6, 2.4) * 0.22, 0.0, 1.0), colour


def _dust(colour: RGB, variant: int) -> tuple[np.ndarray, RGB]:
    """Fine dust of the desert that the wind lifts off the dry ground: a
    small soft grain in three sizes. The fourth variant is a loose puff of
    dust with a few grains in it."""
    x, y = _cell()
    if variant == 3:
        grains = sum(_soft(x - dx, y - dy, 0.05, 1.4) for dx, dy in ((-0.10, 0.05), (0.09, -0.08), (0.12, 0.10)))
        return np.clip(_soft(x, y, 0.28, 1.8) * 0.30 + grains * 0.7, 0.0, 1.0), colour
    r = (0.06, 0.08, 0.11)[variant]
    return np.clip(_soft(x, y, r, 1.4) * (0.9, 0.8, 0.65)[variant] + _soft(x, y, r * 2.2, 2.4) * 0.18, 0.0, 1.0), colour


def _haze(colour: RGB, variant: int) -> tuple[np.ndarray, RGB]:
    """The warm wet air of a rainforest under the karst: soft specks of
    haze that drift, in three sizes. The fourth variant is a firefly: a
    small bright core of yellow-green in a wide soft light. Its colour is
    its own, not the colour of the haze."""
    x, y = _cell()
    if variant == 3:
        return np.clip(_soft(x, y, 0.44, 2.6) * 0.5 + _soft(x, y, 0.08, 1.2) * 1.2, 0.0, 1.0), (214, 250, 120)
    r = (0.12, 0.18, 0.26)[variant]
    return np.clip(_soft(x, y, r, 1.8) * (0.85, 0.65, 0.45)[variant] + _soft(x, y, r * 1.6, 2.6) * 0.18, 0.0, 1.0), colour


def _paddy_mist(colour: RGB, variant: int) -> tuple[np.ndarray, RGB]:
    """Mist over the paddies of a river delta, and chaff of rice that the
    wind lifts at the harvest. The first two variants are soft wisps of
    mist, wider than tall. The other two are husks of rice: a small golden
    grain with a fine whisker. A husk has its own colour."""
    x, y = _cell()
    if variant < 2:
        r = (0.20, 0.28)[variant]
        return np.clip(_soft(x, y, r, 1.6, squash=1.9) * (0.55, 0.42)[variant], 0.0, 1.0), colour
    return _chaff((236, 204, 120), variant)


def _midge_glint(colour: RGB, variant: int) -> tuple[np.ndarray, RGB]:
    """The air over a hot river: small midges that dance, and glints of
    the sun off the water. The first two variants are midges: a dark speck
    of a body with two pale, blurred wings. The other two are glints: a
    bright point with four short rays. A midge has its own dark colour."""
    x, y = _cell()
    if variant < 2:
        turn = (0.3, -0.5)[variant]
        rx = x * math.cos(turn) - y * math.sin(turn)
        ry = x * math.sin(turn) + y * math.cos(turn)
        body = _soft(rx, ry, 0.07, 1.0, squash=1.8)
        wings = _soft(rx - 0.02, ry + 0.08, 0.10, 1.2, squash=0.6) + _soft(rx + 0.04, ry + 0.07, 0.09, 1.2, squash=0.6)
        return np.clip(body * 1.4 + wings * 0.45, 0.0, 1.0), (64, 54, 42)
    reach = (0.24, 0.30)[variant - 2]
    rays = np.maximum(np.clip(1.0 - np.abs(y) / 0.018, 0, 1) * np.clip(1.0 - np.abs(x) / reach, 0, 1) ** 2,
                      np.clip(1.0 - np.abs(x) / 0.018, 0, 1) * np.clip(1.0 - np.abs(y) / (reach * 0.7), 0, 1) ** 2)
    return np.clip(rays + _soft(x, y, 0.07, 1.2) * 1.3 + _soft(x, y, 0.26, 2.4) * 0.25, 0.0, 1.0), colour


def _morning_mist(colour: RGB, variant: int) -> tuple[np.ndarray, RGB]:
    """Mist of the morning that drifts over the plain and in the trees:
    soft wisps, wider than tall, in three sizes. The fourth variant is two
    wisps that drift together."""
    x, y = _cell()
    if variant == 3:
        return np.clip(_soft(x + 0.09, y + 0.04, 0.22, 1.6, squash=1.4) * 0.40 + _soft(x - 0.12, y - 0.06, 0.18, 1.6, squash=1.5) * 0.35, 0.0, 1.0), colour
    r = (0.16, 0.21, 0.25)[variant]
    return np.clip(_soft(x, y, r, 1.6, squash=1.6) * (0.60, 0.48, 0.40)[variant], 0.0, 1.0), colour


def _dragonfly_pollen(colour: RGB, variant: int) -> tuple[np.ndarray, RGB]:
    """The air over the ponds of Angkor in the afternoon. The first
    variant is a dragonfly: a long thin body and four narrow wings held
    out flat. Its colour is its own, a warm red. The other three are
    grains of pollen in the gold light: small soft points."""
    x, y = _cell()
    if variant == 0:
        turn = 0.25
        rx = x * math.cos(turn) - y * math.sin(turn)
        ry = x * math.sin(turn) + y * math.cos(turn)
        body = np.clip(1.0 - np.abs(ry) / 0.022, 0.0, 1.0) * (rx > -0.30) * (rx < 0.22)
        head = _soft(rx - 0.24, ry, 0.045, 1.0)
        wings = np.zeros_like(rx)
        for ox in (0.10, 0.02):
            for side in (-1.0, 1.0):
                wings = np.maximum(wings, _soft(rx - ox, ry - side * 0.15, 0.16, 1.0, squash=0.28))
        return np.clip(body + head + wings * 0.45, 0.0, 1.0), (176, 78, 52)
    r = (0.06, 0.08, 0.10)[variant - 1]
    return np.clip(_soft(x, y, r, 1.3) * 1.1 + _soft(x, y, r * 2.6, 2.4) * 0.25, 0.0, 1.0), colour


def _turned(x: np.ndarray, y: np.ndarray, turn: float) -> tuple[np.ndarray, np.ndarray]:
    return x * math.cos(turn) - y * math.sin(turn), x * math.sin(turn) + y * math.cos(turn)


def _autumn_leaf(colour: RGB, variant: int) -> tuple[np.ndarray, RGB]:
    """A leaf of chestnut or beech that falls in an autumn of north Japan:
    long, with a point at each end, and a paler rib down its middle. Each
    variant has its own turn and its own colour: rust, gold, brown, and the
    colour of the theme."""
    x, y = _cell()
    rx, ry = _turned(x, y, (0.5, -0.9, 1.9, -0.2)[variant])
    half = (0.36, 0.30, 0.33, 0.27)[variant]
    width = (0.12, 0.13, 0.10, 0.12)[variant] * np.clip(1.0 - (rx / half) ** 2, 0.0, 1.0) ** 0.8
    blade = np.clip((width - np.abs(ry)) / 0.025, 0.0, 1.0) * (np.abs(rx) < half)
    rib = np.clip(1.0 - np.abs(ry) / 0.012, 0.0, 1.0) * (np.abs(rx) < half * 0.9)
    stem = np.clip(1.0 - np.abs(ry) / 0.012, 0.0, 1.0) * (rx < -half + 0.01) * (rx > -half - 0.07)
    tone = ((196, 96, 40), (222, 170, 64), (150, 92, 48), colour)[variant]
    return np.clip(blade * 0.95 - rib * 0.35 + stem * 0.9, 0.0, 1.0), tone


def _spray_glint(colour: RGB, variant: int) -> tuple[np.ndarray, RGB]:
    """The air over the surf of the Pacific on a clear morning. The first
    two variants are drops of spray that the wind carries: a small round
    drop in a faint mist. The other two are glints of the low sun on the
    drops: a bright point with four short rays."""
    x, y = _cell()
    if variant < 2:
        r = (0.06, 0.08)[variant]
        return np.clip(_soft(x, y, r, 1.3) * 1.1 + _soft(x, y, r * 3.2, 2.2) * 0.30, 0.0, 1.0), colour
    reach = (0.26, 0.34)[variant - 2]
    rx, ry = _turned(x, y, (0.0, math.pi / 4.0)[variant - 2])
    rays = np.maximum(np.clip(1.0 - np.abs(ry) / 0.018, 0, 1) * np.clip(1.0 - np.abs(rx) / reach, 0, 1) ** 2,
                      np.clip(1.0 - np.abs(rx) / 0.018, 0, 1) * np.clip(1.0 - np.abs(ry) / reach, 0, 1) ** 2)
    return np.clip(rays + _soft(x, y, 0.07, 1.2) * 1.3 + _soft(x, y, 0.24, 2.4) * 0.25, 0.0, 1.0), colour


def _maple_leaf(colour: RGB, variant: int) -> tuple[np.ndarray, RGB]:
    """A leaf of a Korean maple that falls in autumn: five pointed lobes
    that spread from one point, and a thin stem in the gap between the two
    lower lobes. Each variant has its own turn and its own red or gold."""
    x, y = _cell()
    rx, ry = _turned(x, y, (0.2, -0.7, 1.4, 2.6)[variant])
    r = np.sqrt(rx * rx + ry * ry)
    theta = np.arctan2(ry, rx) + math.pi / 2.0
    size = (0.34, 0.30, 0.32, 0.27)[variant]
    edge = size * (0.36 + 0.64 * np.abs(np.cos(theta * 2.5)) ** 2.4)
    blade = np.clip((edge - r) / 0.025, 0.0, 1.0)
    veins = sum(np.clip(1.0 - np.abs(rx * math.sin(a) - ry * math.cos(a)) / 0.010, 0.0, 1.0) * ((rx * math.cos(a) + ry * math.sin(a)) > 0) for a in (-math.pi / 2.0 + k * 2.0 * math.pi / 5.0 for k in range(5)))
    stem = np.clip(1.0 - np.abs(rx) / 0.014, 0.0, 1.0) * (ry > 0.0) * (ry < size * 0.95)
    tone = ((200, 48, 36), (226, 110, 40), (170, 36, 40), colour)[variant]
    return np.clip(blade * 0.95 - veins * blade * 0.30 + stem * 0.9, 0.0, 1.0), tone


def _catkin(colour: RGB, variant: int) -> tuple[np.ndarray, RGB]:
    """The fluff of a willow catkin, which drifts by West Lake in spring:
    a soft, loose tuft of white cotton round a small seed, of no clear
    shape, with two or three fine wisps that trail out of it. Each variant
    has its own size and turn, and the fourth is a thin wisp with no
    seed."""
    x, y = _cell()
    rx, ry = _turned(x, y, (0.3, -0.8, 1.4, 2.2)[variant])
    size = (0.15, 0.18, 0.12, 0.15)[variant]
    lumps = ((-0.45, 0.10, 0.70), (0.35, -0.15, 0.80), (0.10, 0.35, 0.60), (-0.10, -0.40, 0.55), (0.55, 0.30, 0.45))
    tuft = np.zeros_like(x)
    for ox, oy, k in lumps[: 5 if variant != 3 else 3]:
        tuft = tuft + _soft(rx - ox * size, ry - oy * size * (0.6 if variant == 3 else 1.0), size * k * 1.35, 2.2)
    # The wisps: thin soft lines that bend a little as they leave the tuft.
    wisps = np.zeros_like(x)
    for angle, length, bend in ((0.4, 2.2, 0.5), (2.6, 1.8, -0.6), (4.4, 1.6, 0.4))[: 2 + (variant % 2)]:
        ux, uy = _turned(rx, ry, -angle)
        along = ux / (size * length)
        off = uy - bend * size * along * along
        wisps = np.maximum(wisps, np.clip(1.0 - np.abs(off) / 0.012, 0.0, 1.0) * np.clip(along, 0.0, 1.0) * (along < 1.0) * (1.0 - along))
    seed = _soft(rx, ry, 0.028, 1.0) * (variant != 3)
    halo = _soft(rx, ry, size * 2.0, 2.0) * 0.22
    # Fine hairs in the cotton: soft streaks that go out from the seed.
    streaks = 0.72 + 0.28 * np.cos(np.arctan2(ry, rx) * 13.0 + variant) ** 2
    alpha = np.clip(tuft * 1.1, 0.0, 1.0) ** 0.9 * streaks * (0.6 if variant == 3 else 0.85) + wisps * 0.6 + halo
    return np.clip(alpha + seed * 0.2, 0.0, 1.0), colour


def _momiji(colour: RGB, variant: int) -> tuple[np.ndarray, RGB]:
    """A leaf of the Japanese maple, which falls in the autumn of
    Heian-kyo: seven lobes, long and pointed and cut deep, that spread from
    a small palm like the fingers of a hand; the two lowest lobes are
    short. A thin stem comes from the gap at its foot. Each variant has
    its own turn and its own red, scarlet or orange."""
    x, y = _cell()
    rx, ry = _turned(x, y, (0.1, -0.9, 1.2, 2.8)[variant])
    size = (0.32, 0.28, 0.30, 0.25)[variant]
    blade = _soft(rx, ry + size * 0.05, size * 0.22, 0.3)
    veins = np.zeros_like(x)
    for angle, length in ((0.0, 1.0), (0.72, 0.92), (-0.72, 0.92), (1.42, 0.74), (-1.42, 0.74), (2.08, 0.46), (-2.08, 0.46)):
        # u runs out along the lobe from the palm, v across it.
        u = rx * math.sin(angle) - ry * math.cos(angle)
        v = rx * math.cos(angle) + ry * math.sin(angle)
        t = np.clip(u / (size * length), 0.0, 1.0)
        half = size * 0.17 * np.sqrt(t) * (1.0 - t) ** 0.9 * 1.9 + size * 0.05 * (1.0 - t)
        lobe = np.clip((half - np.abs(v)) / 0.012, 0.0, 1.0) * (u > -size * 0.05) * (u < size * length)
        blade = np.maximum(blade, lobe)
        veins = np.maximum(veins, np.clip(1.0 - np.abs(v) / 0.008, 0.0, 1.0) * (u > 0.0) * (t < 0.85))
    stem = np.clip(1.0 - np.abs(rx) / 0.011, 0.0, 1.0) * (ry > 0.0) * (ry < size * 0.8)
    tone = ((186, 34, 30), (220, 70, 34), (150, 24, 34), colour)[variant]
    return np.clip(blade * 0.95 - veins * blade * 0.30 + stem * 0.85, 0.0, 1.0), tone


def _pine_pollen(colour: RGB, variant: int) -> tuple[np.ndarray, RGB]:
    """The pollen of the pines on Bugaksan, which drifts over the palace
    in early summer: fine yellow grains in a soft haze. The first three
    variants are single grains of each size. The fourth is a small puff
    of a few grains together."""
    x, y = _cell()
    if variant < 3:
        r = (0.05, 0.07, 0.09)[variant]
        return np.clip(_soft(x, y, r, 1.3) * 1.1 + _soft(x, y, r * 2.8, 2.4) * 0.28, 0.0, 1.0), colour
    grains = sum(_soft(x - ox, y - oy, 0.04, 1.2) for ox, oy in ((-0.08, 0.02), (0.06, -0.06), (0.03, 0.08), (0.12, 0.05), (-0.03, -0.09)))
    return np.clip(grains * 1.1 + _soft(x, y, 0.26, 2.0) * 0.35, 0.0, 1.0), colour


def _cotton_fluff(colour: RGB, variant: int) -> tuple[np.ndarray, RGB]:
    """A puff of cotton lint, which drifts from the fields and the spinners
    of Dhaka: a round soft cloud of white fibres, denser in its middle,
    with fine hairs at its edge. Each variant has its own size; the fourth
    is two small puffs with a thread of fibre between them."""
    x, y = _cell()
    if variant == 3:
        puffs = _soft(x + 0.13, y + 0.04, 0.12, 1.3) + _soft(x - 0.12, y - 0.05, 0.10, 1.3)
        thread = np.clip(1.0 - np.abs(y - x * 0.35) / 0.012, 0.0, 1.0) * (np.abs(x) < 0.12)
        return np.clip(puffs * 1.2 + thread * 0.5, 0.0, 1.0), colour
    size = (0.15, 0.19, 0.12)[variant]
    rx, ry = _turned(x, y, (0.4, 1.3, -0.6)[variant])
    lumps = sum(_soft(rx - ox * size, ry - oy * size, size * k, 2.2) for ox, oy, k in ((0.0, 0.0, 1.2), (-0.60, 0.25, 0.80), (0.55, -0.20, 0.85), (0.15, 0.60, 0.70), (-0.25, -0.55, 0.65), (0.60, 0.45, 0.55)))
    angle = np.arctan2(ry, rx)
    reach = np.sqrt(rx * rx + ry * ry)
    hairs = np.clip(np.cos(angle * 23.0 + variant) * 0.5 + 0.5, 0.0, 1.0) ** 4 * np.clip(1.0 - reach / (size * 2.1), 0.0, 1.0) * (reach > size * 0.6)
    return np.clip(lumps * 1.6 + hairs * 0.16 + _soft(rx, ry, size * 1.7, 2.0) * 0.15, 0.0, 1.0), colour


def _rain_streak(colour: RGB, variant: int) -> tuple[np.ndarray, RGB]:
    """A drop of the light monsoon rain over the Hooghly: a long thin
    streak that leans a little with the wind, faint at its top and
    brighter at its foot, where the drop is. The fourth variant is two
    short streaks side by side."""
    if variant == 3:
        lines = [[(-0.06 + 0.04, -0.12), (-0.06 - 0.02, 0.10)], [(0.08 + 0.04, -0.16), (0.08 - 0.02, 0.06)]]
        return _strokes(lines, 0.008, 0.15), colour
    length = (0.36, 0.42, 0.30)[variant]
    lean = 0.18
    x, y = _cell()
    t = np.clip((y + length * 0.5) / length, 0.0, 1.0)
    centre = lean * (length * 0.5 - (y + length * 0.5)) * 0.5
    line = np.clip(1.0 - np.abs(x - centre) / 0.010, 0.0, 1.0) * (np.abs(y) < length * 0.5)
    head = _soft(x - centre, y - length * 0.45, 0.030, 1.2)
    return np.clip(line * (0.25 + 0.6 * t) + head * 0.9, 0.0, 1.0), colour


def _shimul_petal(colour: RGB, variant: int) -> tuple[np.ndarray, RGB]:
    """A petal of the shimul, the red silk-cotton tree, which falls over
    the campus in February: thick and fleshy, a broad oval that is narrow
    at its foot, cupped, so its middle is darker than its rim. Each
    variant has its own turn and its own red; the fourth is a small whole
    flower seen from above, five petals round a gold heart."""
    x, y = _cell()
    if variant == 3:
        petals = np.zeros_like(x)
        for k in range(5):
            a = 0.3 + k * 2.0 * math.pi / 5.0
            px, py = _turned(x - math.cos(a) * 0.12, y - math.sin(a) * 0.12, -a)
            petals = np.maximum(petals, _soft(px, py, 0.12, 0.6, squash=1.4))
        heart = _soft(x, y, 0.06, 0.8)
        return np.clip(petals * 0.95 - heart * 0.35, 0.0, 1.0), (206, 40, 32)
    rx, ry = _turned(x, y, (0.5, -1.0, 2.0)[variant])
    half = (0.30, 0.26, 0.34)[variant]
    t = np.clip((rx / half + 1.0) * 0.5, 0.0, 1.0)
    width = 0.17 * np.sqrt(np.clip(t, 0.0, 1.0)) * np.clip(1.0 - (rx / half) ** 2, 0.0, 1.0) ** 0.35
    blade = np.clip((width - np.abs(ry)) / 0.03, 0.0, 1.0) * (np.abs(rx) < half)
    cupped = np.clip(1.0 - np.abs(ry) / np.maximum(width, 1e-3), 0.0, 1.0)
    tone = ((214, 42, 34), (190, 30, 30), (232, 74, 44))[variant]
    return np.clip(blade * (0.75 + 0.25 * cupped), 0.0, 1.0), tone


def _kapok_seed(colour: RGB, variant: int) -> tuple[np.ndarray, RGB]:
    """A seed of the samaúma, the kapok tree, that drifts over the flood: a
    small dark seed in a soft tuft of silky white floss. Each of the first
    three variants has its own size and turn. The fourth is a firefly of
    the dawn: a small bright core in a wide soft light of yellow-green."""
    x, y = _cell()
    if variant == 3:
        return np.clip(_soft(x, y, 0.44, 2.6) * 0.55 + _soft(x, y, 0.13, 1.2, 1.3), 0.0, 1.0), (214, 240, 120)
    size = (0.16, 0.20, 0.13)[variant]
    rx, ry = _turned(x, y, (0.6, -0.9, 1.8)[variant])
    floss = _soft(rx, ry, size * 1.4, 1.4, squash=1.4) * 0.75
    angle = np.arctan2(ry, rx)
    reach = np.sqrt(rx * rx + ry * ry)
    hairs = np.clip(np.cos(angle * 19.0 + variant) * 0.5 + 0.5, 0.0, 1.0) ** 3 * np.clip(1.0 - reach / (size * 2.2), 0.0, 1.0)
    seed = _soft(rx + size * 0.15, ry, size * 0.30, 0.6, squash=1.5)
    alpha = np.clip(floss + hairs * 0.35 + seed, 0.0, 1.0)
    # The seed is dark in the middle of the white floss: the colour of a
    # mote is one colour, so the seed shows as a denser core.
    return alpha, colour


def _palm_fibre(colour: RGB, variant: int) -> tuple[np.ndarray, RGB]:
    """Dust and fibre that drift over a village of Palmares in the dry
    afternoon. The first two variants are soft grains of warm red dust, of
    two sizes. The third and the fourth are thin curved strands of palm
    fibre, pale straw, from the thatch and the cord."""
    x, y = _cell()
    if variant < 2:
        r = (0.10, 0.15)[variant]
        return np.clip(_soft(x, y, r, 1.6) * 0.9 + _soft(x + 0.12, y - 0.08, r * 0.5, 1.6) * 0.6, 0.0, 1.0), (206, 150, 104)
    bend = (0.10, -0.14)[variant - 2]
    pts = [(-0.30 + 0.6 * t, (t - 0.5) * 0.25 * (1.0 if variant == 2 else -1.0) + bend * math.sin(math.pi * t)) for t in np.linspace(0.0, 1.0, 9)]
    return _strokes([pts], 0.010, 0.18), colour


def _blossom_petal(colour: RGB, variant: int) -> tuple[np.ndarray, RGB]:
    """A petal that falls over the streets of Rio in May. The first two
    variants are papery bracts of bougainvillea, pink and magenta: a broad
    heart shape with fine veins, each with its own turn. The third is a
    yellow petal of a flowering tree, a long oval. The fourth is a small
    white petal."""
    x, y = _cell()
    turn = (0.4, -1.1, 1.9, -0.3)[variant]
    rx, ry = _turned(x, y, turn)
    if variant < 2:
        lobes = _soft(rx - 0.07, ry + 0.06, 0.15, 0.5) + _soft(rx + 0.07, ry + 0.06, 0.15, 0.5)
        point = np.clip(1.0 - np.abs(rx) / np.maximum(0.001, 0.20 * np.clip(0.26 - ry, 0.0, 1.0) / 0.26), 0.0, 1.0) * (ry < 0.10) * (ry > -0.24)
        body = np.clip(np.maximum(lobes * 3.0, point), 0.0, 1.0)
        veins = np.clip(1.0 - np.abs(rx) / 0.012, 0.0, 1.0) * 0.25
        tone = ((226, 90, 156), (196, 52, 118))[variant]
        return np.clip(body * (0.85 - veins), 0.0, 1.0), tone
    half = (0.26, 0.20)[variant - 2]
    width = 0.11 * np.clip(1.0 - (rx / half) ** 2, 0.0, 1.0) ** 0.5
    blade = np.clip((width - np.abs(ry)) / 0.03, 0.0, 1.0) * (np.abs(rx) < half)
    tone = ((246, 206, 80), (250, 244, 232))[variant - 2]
    return blade * 0.9, tone


#: The mote of each theme: how it is drawn, and its colour.
MOTES = {
    "hub": (_dot, (206, 214, 255)),
    "lab": (_dot, (196, 255, 244)),
    # Dust in the light of a station deck, and starlight glints in the trusses.
    "orbital": (_dot, (210, 230, 255)),
    "orbital_truss": (_twinkle, (200, 226, 255)),
    # Pollen in the sun on the campus of Eureka, and glints of ice high on
    # the space elevator.
    "eureka": (_dot, (255, 240, 180)),
    "eureka_heights": (_twinkle, (220, 240, 255)),
    "basement": (_glow, (255, 190, 110)),
    # Drops of water that fall from the vault.
    "undertown": (_dot, (196, 232, 218)),
    # Sparks from the cables that are cut.
    "alarm": (_glow, (255, 170, 120)),
    "boss": (_glow, (255, 150, 100)),
    "cave": (_twinkle, (150, 232, 255)),
    "eclipse": (_twinkle, (130, 246, 214)),
    "forest": (_glow, (226, 255, 140)),
    "primeval": (_dot, (240, 232, 150)),
    # Steam from the pots, in the light of the holes.
    "noodly": (_glow, (255, 240, 214)),
    # Chalk dust in the morning light.
    "math_town": (_dot, (252, 250, 240)),
    # Dust in the shafts of day from the grates.
    "math_undercroft": (_dot, (255, 236, 200)),
    # Dust in the lamplight of a room.
    "math_interior": (_dot, (255, 230, 190)),
    # Embers of a dark light.
    "starless": (_glow, (255, 120, 196)),
    # Sparks that go up from the fire under the floor.
    "void_castle": (_glow, (255, 150, 80)),
    # Small white specks in the void, with no colour.
    "void": (_speck, (240, 240, 240)),
    # Ash and sparks from the fires of the Evil dimension.
    "evil_forest": (_glow, (255, 104, 60)),
    # Spray off the sea in the late sun, at the port.
    "pirate_port": (_dot, (250, 244, 228)),
    # Maple leaves that fall in the village.
    "ninja_village": (_petal, (214, 84, 52)),
    "castle_godwin": (_glow, (255, 140, 70)),
    # Sparks from the coils; ash in the throne room.
    "castle_godwin_lab": (_glow, (190, 230, 255)),
    "castle_godwin_throne": (_glow, (255, 110, 70)),
    # Dust in the light of the caged lamps of the military tower.
    "military_tower": (_dot, (255, 226, 178)),
    # The sparkles of a wand.
    "starlight": (_twinkle, (255, 240, 200)),
    # Grains of sand in the light.
    "stardune": (_dot, (255, 240, 200)),
    "water": (_bubble, (206, 252, 244)),
    "cove": (_dot, (226, 244, 236)),
    "skybridge": (_petal, (255, 214, 226)),
    # Seeds on the wind.
    "open_sky": (_dot, (255, 252, 236)),
    # The clean state of the two-state hub: dust in the light of its halls.
    "hub_clean": (_dot, (255, 240, 206)),
    # The Art dimension: flecks of paint in the air; dust of graphite off
    # the pages; drops of ink that glow as they rise from the falls.
    "art": (_petal, (246, 110, 196)),
    "art_sketchbook": (_speck, (110, 112, 128)),
    "art_inkfall": (_glow, (255, 120, 220)),
    # The four quarters: letters that float off the pages; small notes that
    # glow; confetti in the light of the stage; sparks from the kilns.
    "art_stacks": (_letter, (64, 46, 40)),
    "art_resonance": (_note, (150, 236, 255)),
    "art_stage": (_confetti, (255, 214, 120)),
    "art_forge": (_glow, (255, 156, 70)),
    # The History dimension: chaff and seeds on the wind of the first
    # farms; sand and gold dust on the Nile; olive leaves on the shore;
    # paper that drifts on the Silk Road; grass seeds on the steppe; gold
    # flecks and spray on the Monsoon Coast; feathers of gulls over the
    # harbour; soot over the mills.
    "history_crescent": (_chaff, (240, 206, 130)),
    "history_nile": (_dot, (255, 220, 140)),
    "history_classical": (_petal, (150, 168, 112)),
    "history_silk": (_confetti, (246, 236, 214)),
    "history_steppe": (_chaff, (236, 230, 180)),
    "history_monsoon": (_twinkle, (255, 226, 150)),
    "history_sail": (_feather, (246, 244, 236)),
    "history_industrial": (_dot, (70, 64, 64)),
    # The History dimension, second pass: seeds of grass in the Rift Valley;
    # pollen over the Green Sahara; snow in the Ice Age; blossom of hawthorn
    # on the downs; mist in the north; monsoon rain on the Indus; dust of
    # the loess; pollen of maize; sparks of a fire in Sahul; fireflies in the
    # highlands; sparks of the torches in the painted cave.
    "history_savanna": (_chaff, (236, 200, 120)),
    "history_green_sahara": (_dot, (250, 240, 170)),
    "history_ice_age": (_flake, (240, 246, 255)),
    "history_megalith": (_petal, (242, 238, 228)),
    "history_northwoods": (_dot, (214, 222, 220)),
    "history_indus": (_raindrop, (200, 214, 230)),
    "history_yellow_river": (_dot, (232, 204, 140)),
    "history_maize": (_chaff, (240, 220, 140)),
    "history_sahul": (_glow, (255, 170, 80)),
    "history_highlands": (_glow, (210, 250, 160)),
    "history_painted_cave": (_glow, (255, 176, 96)),
    # The History dimension, third pass: the damp haze of the Gulf swamps;
    # blue butterflies over the Maya forest; salt spray on the Taino shore;
    # petals on the lagoon; spray of the open sea; seeds of grass on the
    # wind of Rapa Nui.
    "history_olmec": (_dot, (236, 232, 196)),
    "history_maya": (_butterfly, (96, 170, 250)),
    "history_caribbean": (_dot, (248, 252, 250)),
    "history_lapita": (_petal, (255, 236, 196)),
    "history_open_ocean": (_dot, (214, 228, 242)),
    "history_rapa_nui": (_chaff, (226, 214, 150)),
    # The Atlantic world: warm red dust over Benin City, and the sparks of
    # the casters' furnaces.
    "history_benin": (_dust_spark, (255, 196, 128)),
    # Saint-Domingue: seeds on tufts of fluff drift over the plain in the
    # warm light of the late afternoon.
    "history_saint_domingue": (_fluff, (255, 244, 222)),
    # The Gold Coast: fine spray of the sea, carried in off the surf.
    "history_gold_coast": (_spray, (242, 248, 248)),
    # South America: grains of snow and frost in the cold air of the high
    # Andes, and fine dust over the desert of the Supe valley.
    "history_andes": (_frost, (246, 250, 255)),
    "history_supe": (_dust, (240, 220, 186)),
    # Southeast Asia: specks of humid haze and a few fireflies under the
    # karst of Wallacea; spray of the sea on the Austronesian shore; mist
    # and rice chaff over the paddies of the Red River.
    "history_wallacea": (_haze, (240, 244, 230)),
    "history_austronesia": (_spray, (240, 250, 250)),
    "history_red_river": (_paddy_mist, (232, 238, 240)),
    # Midges and glints of the sun over the Musi at Palembang; mist of the
    # morning over the Kedu plain at Borobudur; a dragonfly and pollen in
    # the gold light of Angkor.
    "history_strait": (_midge_glint, (255, 250, 228)),
    "history_borobudur": (_morning_mist, (244, 236, 228)),
    "history_angkor": (_dragonfly_pollen, (255, 226, 150)),
    # Leaves of chestnut and beech that fall at Sannai-Maruyama; spray
    # and glints of the sun over the surf of eastern Taiwan; red leaves of
    # maple that fall among the tombs of Gyeongju.
    "history_jomon": (_autumn_leaf, (206, 120, 50)),
    "history_taiwan": (_spray_glint, (246, 252, 252)),
    "history_gyeongju": (_maple_leaf, (232, 168, 56)),
    # Willow catkins that drift by West Lake in spring; red leaves of the
    # Japanese maple that fall in the gardens of Heian-kyo; yellow pine
    # pollen over Gyeongbokgung in early summer.
    "history_hangzhou": (_catkin, (250, 248, 238)),
    "history_heian": (_momiji, (232, 120, 40)),
    "history_hanyang": (_pine_pollen, (246, 222, 110)),
    # Cotton lint that drifts over the Buriganga; light monsoon rain over
    # the Hooghly; red petals of the shimul over the Dhaka campus.
    "history_dhaka_river": (_cotton_fluff, (248, 246, 238)),
    "history_calcutta": (_rain_streak, (206, 218, 226)),
    "history_dhaka_spring": (_shimul_petal, (214, 42, 34)),
    # Kapok seeds and a few fireflies over the flood on Marajó; red dust and
    # palm fibre at Palmares; petals of bougainvillea and of flowering
    # trees over Rio.
    "history_marajo": (_kapok_seed, (246, 242, 230)),
    "history_palmares": (_palm_fibre, (226, 204, 150)),
    "history_rio_1888": (_blossom_petal, (226, 90, 156)),
}


#: The shadow a body throws on the ground under it, for each theme: its
#: colour. The picture is a soft ellipse, `SHADOW_PX` wide and high, with a
#: dark core. The game draws one under each actor, smaller and fainter
#: when the actor is in the air (`ground_shadows` in `ambition_render`).
SHADOWS = {
    "hub": (8, 8, 30),
    "lab": (4, 12, 22),
    "orbital": (10, 14, 24),
    "orbital_truss": (6, 8, 20),
    "alarm": (3, 3, 9),
    "undertown": (6, 10, 10),
    "basement": (20, 8, 6),
    "boss": (16, 2, 8),
    "cave": (8, 6, 22),
    "eclipse": (2, 4, 18),
    "forest": (10, 18, 12),
    "primeval": (16, 22, 10),
    "noodly": (40, 18, 12),
    "math_town": (70, 80, 100),
    "math_undercroft": (20, 22, 32),
    "math_interior": (60, 44, 36),
    "starlight": (88, 64, 120),
    "stardune": (124, 78, 70),
    "starless": (5, 2, 14),
    "void_castle": (14, 3, 8),
    "evil_forest": (10, 2, 4),
    "castle_godwin": (6, 6, 12),
    "castle_godwin_lab": (4, 10, 8),
    "castle_godwin_throne": (8, 4, 8),
    "military_tower": (10, 12, 10),
    "water": (2, 16, 30),
    "cove": (4, 14, 24),
    "skybridge": (40, 52, 84),
    "open_sky": (60, 64, 80),
    "hub_clean": (60, 60, 80),
    "art": (40, 24, 70),
    "art_sketchbook": (120, 112, 100),
    "art_inkfall": (8, 2, 20),
    "art_stacks": (60, 38, 28),
    "art_resonance": (6, 8, 24),
    "art_stage": (30, 8, 16),
    "art_forge": (24, 10, 6),
    "history_crescent": (70, 44, 34),
    "history_nile": (90, 52, 34),
    "history_classical": (60, 70, 80),
    "history_silk": (110, 70, 44),
    "history_steppe": (40, 52, 28),
    "history_monsoon": (60, 50, 44),
    "history_sail": (24, 34, 34),
    "history_industrial": (20, 16, 18),
    "history_savanna": (70, 40, 24),
    "history_green_sahara": (40, 52, 28),
    "history_ice_age": (60, 80, 120),
    "history_megalith": (40, 52, 34),
    "history_northwoods": (20, 30, 30),
    "history_indus": (70, 36, 26),
    "history_yellow_river": (80, 60, 36),
    "history_maize": (50, 48, 30),
    "history_sahul": (80, 30, 20),
    "history_highlands": (20, 36, 24),
    "history_painted_cave": (24, 14, 10),
    "history_olmec": (40, 46, 28),
    "history_maya": (20, 36, 26),
    "history_caribbean": (60, 70, 66),
    "history_lapita": (40, 30, 26),
    "history_open_ocean": (14, 22, 40),
    "history_rapa_nui": (40, 44, 30),
    "history_benin": (60, 26, 16),
    "history_saint_domingue": (56, 28, 18),
    "history_gold_coast": (44, 46, 48),
    "history_andes": (40, 36, 34),
    "history_supe": (60, 46, 32),
    "history_wallacea": (38, 44, 34),
    "history_austronesia": (36, 30, 28),
    "history_red_river": (52, 42, 32),
    "history_strait": (44, 34, 24),
    "history_borobudur": (40, 46, 38),
    "history_angkor": (58, 40, 28),
    "history_jomon": (40, 30, 22),
    "history_taiwan": (34, 42, 36),
    "history_gyeongju": (50, 44, 34),
    "history_hangzhou": (36, 42, 40),
    "history_heian": (46, 36, 30),
    "history_hanyang": (44, 42, 38),
    "history_dhaka_river": (40, 36, 26),
    "history_calcutta": (40, 34, 30),
    "history_dhaka_spring": (52, 36, 30),
    "history_marajo": (28, 24, 20),
    "history_palmares": (56, 30, 22),
    "history_rio_1888": (40, 40, 44),
}
SHADOW_PX = (96, 28)


def shadow(theme_key: str) -> Image.Image:
    """The ground shadow picture of a theme."""
    w, h = SHADOW_PX
    ys, xs = np.mgrid[0:h, 0:w]
    x = (xs + 0.5) / w * 2.0 - 1.0
    y = (ys + 0.5) / h * 2.0 - 1.0
    d = np.sqrt(x * x + y * y)
    # A dark core out to near half of the way, then a smooth edge: a cone has
    # so thin a middle that the shadow does not show on a floor.
    t = np.clip((d - 0.45) / 0.55, 0.0, 1.0)
    alpha = 1.0 - t * t * (3.0 - 2.0 * t)
    out = np.zeros((h, w, 4), dtype=np.float32)
    out[:, :, :3] = SHADOWS[theme_key]
    out[:, :, 3] = alpha * 255.0
    return Image.fromarray(np.rint(out).astype(np.uint8), "RGBA")


def strip(theme_key: str) -> Image.Image:
    """The mote picture of a theme."""
    make, colour = MOTES[theme_key]
    out = np.zeros((CELL, CELL * VARIANTS, 4), dtype=np.float32)
    s = SUPERSAMPLE
    for variant in range(VARIANTS):
        alpha, rgb = make(colour, variant)
        small = alpha.reshape(CELL, s, CELL, s).mean(axis=(1, 3))
        out[:, variant * CELL : (variant + 1) * CELL, :3] = rgb
        out[:, variant * CELL : (variant + 1) * CELL, 3] = small * 255.0
    return Image.fromarray(np.rint(out).astype(np.uint8), "RGBA")
