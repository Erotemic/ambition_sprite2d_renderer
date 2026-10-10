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


#: The mote of each theme: how it is drawn, and its colour.
MOTES = {
    "hub": (_dot, (206, 214, 255)),
    "lab": (_dot, (196, 255, 244)),
    "basement": (_glow, (255, 190, 110)),
    # Drops of water that fall from the vault.
    "undertown": (_dot, (196, 232, 218)),
    # Sparks from the cables that are cut.
    "alarm": (_glow, (255, 170, 120)),
    "boss": (_glow, (255, 150, 100)),
    "cave": (_twinkle, (150, 232, 255)),
    "eclipse": (_twinkle, (130, 246, 214)),
    "forest": (_glow, (226, 255, 140)),
    "water": (_bubble, (206, 252, 244)),
    "cove": (_dot, (226, 244, 236)),
    "skybridge": (_petal, (255, 214, 226)),
    # The clean state of the two-state hub: dust in the light of its halls.
    "hub_clean": (_dot, (255, 240, 206)),
}


#: The shadow a body throws on the ground under it, for each theme: its
#: colour. The picture is a soft ellipse, `SHADOW_PX` wide and high, with a
#: dark core. The game draws one under each actor, smaller and fainter
#: when the actor is in the air (`ground_shadows` in `ambition_render`).
SHADOWS = {
    "hub": (8, 8, 30),
    "lab": (4, 12, 22),
    "alarm": (3, 3, 9),
    "undertown": (6, 10, 10),
    "basement": (20, 8, 6),
    "boss": (16, 2, 8),
    "cave": (8, 6, 22),
    "eclipse": (2, 4, 18),
    "forest": (10, 18, 12),
    "water": (2, 16, 30),
    "cove": (4, 14, 24),
    "skybridge": (40, 52, 84),
    "hub_clean": (60, 60, 80),
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
