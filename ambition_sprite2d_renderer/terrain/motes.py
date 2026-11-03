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
