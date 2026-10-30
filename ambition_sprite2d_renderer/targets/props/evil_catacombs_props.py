"""The catacombs under the moor (`evil_catacombs`, the Evil dimension): the
old burial tunnels between the founder's crypt (east) and the Castle
Allotments, which they come up under (Crabbe's plot, number 13).

Drawn in room coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/evil_moor/make_specs.py` (`catacombs`): the
floor (y 512), the ceiling (to y 32), the shaft up to the allotments at the
west end (x 40..104), the way east into the crypt at the floor.

- `catacombs_west`: the way west, dark behind its cracked wall; the shaft
  up under plot 13, the roots of Crabbe's prize
  marrows hanging through the ceiling, one marrow come right through; walls
  of skulls in rows; an arch.
- `catacombs_east`: a fall of rubble where the vault came down, propped
  with beams; a forgotten shrine with a guttered candle; more skulls, a
  long arch toward the crypt.

Animations: ``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .evil_inn_props import PAL

W, FLOOR, CEILING = 2560, 512, 32
SHAFT = (40, 104)
STONE = (72, 66, 70)
STONE_DARK = (46, 42, 46)
BONE = (214, 204, 180)
BONE_DARK = (150, 140, 120)
ROOT = (110, 84, 58)
MARROW = (120, 150, 60)
MARROW_DARK = (80, 110, 40)
WOOD = (90, 64, 44)
CANDLE = (255, 214, 140)


def vault(c, x0, x1):
    wall = c.mask(box(x0, CEILING, x1, FLOOR))
    c.put(wall, STONE)
    c.put(wall * c.mask(lambda p: [p.rect(x0, y, x1, y + 1.4) for y in range(CEILING + 22, FLOOR, 26)]), STONE_DARK, 0.7)
    c.tone(wall * (c.noise(("catacomb", x0), 12, 5, 3) - 0.5), 0.25)
    c.tone(wall * np.clip((180 - c.y) / 150, 0, 1), -0.4)


def skull_wall(c, x0, x1, y0, y1):
    """Rows of skulls set in the wall, long bones between the rows."""
    rows = list(range(int(y0), int(y1), 26))
    c.put(c.mask(lambda p: [p.rect(x0, y + 15, x1, y + 20) for y in rows]), BONE_DARK)
    c.put(c.mask(lambda p: [p.ellipse(x, y + 6, 9, 9) for y in rows for x in range(int(x0) + 10, int(x1) - 6, 20)]), BONE)
    c.put(c.mask(lambda p: [p.ellipse(x + dx, y + 5, 2.2, 2.6) for y in rows for x in range(int(x0) + 10, int(x1) - 6, 20) for dx in (-3.5, 3.5)]), (30, 24, 26))
    c.put(c.mask(lambda p: [p.rect(x - 2, y + 11, x + 2, y + 13) for y in rows for x in range(int(x0) + 10, int(x1) - 6, 20)]), (30, 24, 26))


def arch(c, x, w, top):
    c.put(c.mask(lambda p: p.arch(x - 8, top - 8, x + w + 8, FLOOR)), STONE_DARK)
    c.put(c.mask(lambda p: p.arch(x, top, x + w, FLOOR)), (22, 18, 20))


def west(c, k):
    vault(c, 16, 1280)
    s0, s1 = SHAFT
    # The shaft up under plot 13, and the roots of the marrows through the vault.
    c.put(c.mask(box(s0, 0, s1, CEILING)), STONE_DARK)
    for i, rx in enumerate(range(120, 420, 34)):
        ln = 60 + (i * 37) % 90
        c.put(c.mask(lambda p: p.line([(rx, CEILING), (rx + (8 if i % 2 else -8), CEILING + ln * 0.5), (rx + (3 if i % 2 else -5), CEILING + ln)], 2.4)), ROOT)
    c.put(c.mask(lambda p: p.line([(300, CEILING), (300, CEILING + 70)], 4)), ROOT)
    marrow = c.mask(lambda p: p.ellipse(300, CEILING + 104, 22, 40))
    c.put(marrow, MARROW)
    c.put(marrow * c.mask(lambda p: [p.rect(x, CEILING + 60, x + 2, CEILING + 148) for x in range(284, 318, 8)]), MARROW_DARK)
    # Walls of skulls, and arches.
    skull_wall(c, 140, 600, 150, 420)
    arch(c, 680, 120, 220)
    skull_wall(c, 860, 1260, 150, 420)
    # The way west, left open in the art: the breakable wall over it
    # (`evil_ossuary_props.py`) draws under the room's scenery, and the dark
    # of the room shows through once it is broken.
    c.alpha *= 1.0 - c.mask(box(16, FLOOR - 112, 48, FLOOR))


def east(c, k):
    vault(c, 1280, W - 16)
    # The fall of rubble, propped with beams.
    rng = c.rand("catacomb_rubble")
    c.put(c.mask(lambda p: p.poly([(1380, FLOOR), (1420, FLOOR - 70), (1500, FLOOR - 96), (1580, FLOOR - 60), (1620, FLOOR)])), STONE_DARK)
    c.put(c.mask(lambda p: [p.ellipse(rng.uniform(1400, 1600), rng.uniform(FLOOR - 80, FLOOR - 10), rng.uniform(8, 18), rng.uniform(6, 12)) for _ in range(14)]), STONE)
    c.put(c.mask(lambda p: (p.line([(1360, FLOOR), (1440, CEILING + 40)], 8), p.line([(1640, FLOOR), (1560, CEILING + 40)], 8), p.rect(1420, CEILING + 30, 1580, CEILING + 42))), WOOD)
    # The forgotten shrine: a niche, a guttered candle, a bunch of dry flowers.
    c.put(c.mask(lambda p: p.arch(1800, 250, 1880, 400)), (24, 20, 22))
    c.put(c.mask(box(1796, 400, 1884, 412)), STONE_DARK)
    c.put(c.mask(lambda p: (p.rect(1834, 380, 1842, 400), p.ellipse(1838, 376, 2, 3))), (230, 220, 200))
    c.light(c.mask(lambda p: p.ellipse(1838, 380, 50, 40), blur=10), CANDLE, 0.3)
    c.put(c.mask(lambda p: [p.line([(1856, 400), (1860 + i * 4, 370)], 1.2) for i in range(4)]), (140, 110, 70))
    skull_wall(c, 1940, 2340, 150, 420)
    arch(c, 2400, 120, 240)


PIECES: Dict[str, Piece] = {
    "catacombs_west": Piece((16, 0, 1280, FLOOR), west),
    "catacombs_east": Piece((1280, CEILING, W - 16, FLOOR), east),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
