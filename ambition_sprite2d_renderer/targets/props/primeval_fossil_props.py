"""The fossil beds (`primeval_fossil_beds`, the Jungle dimension): under the
ridge road, down a sinkhole in it: the rock the trail stands on, cut open,
its layers and what is in them.

Drawn in room coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/primeval/tar_pits.py` (`fossil_beds`): the
ridge's road (y 480) and its sinkhole (x 1400..1464); the beds' floor (y
576), their roof (to y 64), the shaft (x 400..464), the survey scaffold
(walked on: x 900..1220 at y 432, x 980..1140 at y 320).

- `ridge_sinkhole`: the hole in the ridge road, roots round its lip (its
  ladder is the room's `Climbable`, which the engine draws).
- `fossil_beds`: the strata, banded, dipping; in them an ammonite, a row of
  trilobites, a fern's print, a long-necked skeleton laid out along a seam,
  a great skull half out of the wall; the survey scaffold against it, its
  string grid and lamps; the geologist's table, her core samples, her
  board of the layers with the dinosaurs crossed out of the top one and
  written back in, crossed out, written back in; the shaft down, daylight
  in it (its ladder is the engine's, as the sinkhole's).

Animations: ``idle``, 1 frame. No drop shadows.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .primeval_props import BONE, MOSS, PAL
from .primeval_tar_props import tapered

RIDGE_ROAD = 480
SINKHOLE = (1400, 1464)
W, FLOOR, ROOF = 1600, 576, 64
SHAFT = (400, 464)
SCAFFOLD = ((900, 1220, 432), (980, 1140, 320))
STRATA = ((160, 120, 92), (186, 150, 108), (140, 104, 82), (204, 176, 128), (120, 96, 80), (176, 140, 104), (150, 118, 96))
ROCK_DARK = (70, 56, 46)
ROOT = (96, 70, 46)
BONE_DARK = (176, 160, 124)
SHELL = (214, 186, 140)
STRING = (230, 80, 60)
LAMP = (255, 200, 120)
CHALK = (236, 236, 228)
SLATE = (46, 52, 50)
CANVAS = (214, 196, 150)
WOOD = (130, 96, 60)


def sinkhole(c, k):
    x0, x1 = SINKHOLE
    g = RIDGE_ROAD
    hole = c.mask(box(x0, g, x1, g + 32))
    c.put(hole, ROCK_DARK)
    c.tone(hole * np.clip((c.y - g) / 32, 0, 1), -0.5)
    # Roots over its lip, hanging in.
    for i, (rx, ln) in enumerate(((x0 + 6, 26), (x0 + 22, 14), (x1 - 18, 22), (x1 - 6, 30))):
        c.put(c.mask(lambda p: p.line([(rx, g - 2), (rx + (3 if i % 2 else -3), g + ln * 0.5), (rx, g + ln)], 2)), ROOT)
    c.put(c.mask(lambda p: [p.ellipse(x, g - 3, 10, 5) for x in (x0 - 4, x1 + 4)]), MOSS)


def ammonite(c, x, y, r):
    """A coiled shell in section."""
    c.put(c.mask(lambda p: p.ellipse(x, y, r)), SHELL)
    pts = [(x + r * 0.95 * math.exp(-0.22 * t) * math.cos(t), y + r * 0.95 * math.exp(-0.22 * t) * math.sin(t)) for t in np.linspace(0, 14, 90)]
    c.put(c.mask(lambda p: p.line(pts, 1.6)), scale(SHELL, 0.62))
    c.put(c.mask(lambda p: [p.line([(x + r * 0.5 * math.cos(a), y + r * 0.5 * math.sin(a)), (x + r * 0.95 * math.cos(a), y + r * 0.95 * math.sin(a))], 0.8)
                            for a in np.linspace(0, 2 * math.pi, 18, endpoint=False)]), scale(SHELL, 0.75))


def trilobite(c, x, y, s):
    c.put(c.mask(lambda p: p.ellipse(x, y, s * 0.55, s)), SHELL)
    c.put(c.mask(lambda p: p.ellipse(x, y - s * 0.75, s * 0.6, s * 0.32)), scale(SHELL, 0.85))
    c.put(c.mask(lambda p: [p.rect(x - s * 0.55, yy, x + s * 0.55, yy + 0.8) for yy in np.arange(y - s * 0.5, y + s, s * 0.22)]), scale(SHELL, 0.6))
    c.put(c.mask(lambda p: p.rect(x - s * 0.12, y - s * 0.6, x + s * 0.12, y + s)), scale(SHELL, 0.72))


def beds(c, k):
    rng = c.rand("fossil_beds")
    rock = c.mask(box(16, 16, W - 16, FLOOR))
    # The strata: bands that dip to the east, each its colour and grain.
    dip = lambda: (c.x - 16) * 0.06
    bounds = [16, 70, 150, 230, 300, 390, 470, FLOOR]
    for i in range(len(bounds) - 1):
        band = rock * ((c.y - dip()) >= bounds[i] - 40) * ((c.y - dip()) < bounds[i + 1] - 40) if i else rock * ((c.y - dip()) < bounds[1] - 40)
        c.put(band, STRATA[i % len(STRATA)])
    lowest = rock * ((c.y - dip()) >= bounds[-2] - 40)
    c.put(lowest, STRATA[(len(bounds) - 2) % len(STRATA)])
    c.tone(rock * (c.noise("fossil_grain", 50, 14, 3) - 0.5), 0.18)
    for b in bounds[1:-1]:
        c.put(rock * c.mask(lambda p: p.line([(16, b - 40), (W - 16, b - 40 + (W - 32) * 0.06)], 1.4)), ROCK_DARK, 0.5)
    # The roof, darker; the shaft's daylight.
    c.tone(rock * np.clip((ROOF + 60 - c.y) / 60, 0, 1), -0.35)
    s0, s1 = SHAFT
    c.put(c.mask(box(s0, 16, s1, ROOF)), ROCK_DARK)
    c.light(c.mask(lambda p: p.poly([(s0, 16), (s1, 16), (s1 + 34, FLOOR), (s0 - 34, FLOOR)]), blur=12), (250, 240, 210), 0.24)
    # Fossils in the layers.
    ammonite(c, 210, 200, 34)
    ammonite(c, 1480, 150, 22)
    for i in range(5):
        trilobite(c, 600 + i * 40, 150 + i * 4, 10)
    # A fern's print, pressed in the rock.
    stem = [(1300 + t * 90, 330 - t * 60 + 12 * math.sin(t * 3)) for t in np.linspace(0, 1, 14)]
    c.put(c.mask(lambda p: p.line(stem, 1.6)), ROCK_DARK, 0.7)
    c.put(c.mask(lambda p: [p.ellipse(x + s * 8, y + 7, 7 * (1 - j / 14) + 2, 2.4) for j, (x, y) in enumerate(stem[1:], 1) for s in (-1, 1)]), ROCK_DARK, 0.55)
    # A long neck laid out along a seam: vertebrae from the skull to the tail.
    spine = [(560 + i * 34, 262 + 10 * math.sin(i / 2.4)) for i in range(16)]
    c.put(c.mask(lambda p: [p.ellipse(x, y, 11, 8) for x, y in spine]), BONE)
    c.put(c.mask(lambda p: [p.line([(x, y + 4), (x + 4, y + 22)], 3) for x, y in spine[4:11]]), BONE_DARK)
    c.put(c.mask(lambda p: p.ellipse(536, 258, 18, 11)), BONE)
    c.put(c.mask(lambda p: p.ellipse(530, 255, 4)), ROCK_DARK)
    # The great skull half out of the wall over the scaffold.
    sx, sy = 1060, 236
    c.put(c.mask(lambda p: p.poly([(sx - 120, sy - 20), (sx - 40, sy - 56), (sx + 70, sy - 40), (sx + 110, sy), (sx + 60, sy + 34), (sx - 90, sy + 30)])), BONE)
    c.put(c.mask(lambda p: (p.ellipse(sx - 40, sy - 14, 18, 14), p.ellipse(sx + 34, sy - 10, 14, 12))), ROCK_DARK)
    c.put(c.mask(lambda p: [p.poly([(x, sy + 22), (x + 6, sy + 22), (x + 3, sy + 40)]) for x in range(int(sx - 80), int(sx + 60), 14)]), BONE)
    c.put(c.mask(lambda p: p.line([(sx - 120, sy - 20), (sx - 90, sy + 30)], 3)), BONE_DARK)
    # The survey scaffold (walked on), its string grid over the skull, lamps.
    for x0, x1, y in SCAFFOLD:
        c.put(c.mask(box(x0, y, x1, y + 8)), WOOD)
        c.put(c.mask(lambda p: [p.rect(x, y + 8, x + 6, FLOOR) for x in (x0 + 8, x1 - 14)]), WOOD)
        c.put(c.mask(lambda p: p.line([(x0 + 10, y + 10), (x1 - 12, FLOOR - 4)], 2)), WOOD)
    c.put(c.mask(lambda p: ([p.line([(x, 150), (x, 300)], 0.8) for x in range(940, 1200, 40)], [p.line([(920, y), (1200, y)], 0.8) for y in range(160, 300, 40)])), STRING)
    for lx in (930, 1190):
        c.put(c.mask(lambda p: p.ellipse(lx, 140, 6, 8)), LAMP)
        c.light(c.mask(lambda p: p.ellipse(lx, 160, 80, 60), blur=14), LAMP, 0.22)
    # The geologist's table: core samples in their tray, a hammer, a lens.
    tx0, tx1 = 560, 760
    c.put(c.mask(lambda p: (p.rect(tx0, FLOOR - 50, tx1, FLOOR - 42), p.rect(tx0 + 8, FLOOR - 42, tx0 + 14, FLOOR), p.rect(tx1 - 14, FLOOR - 42, tx1 - 8, FLOOR))), WOOD)
    for i in range(5):
        cy = FLOOR - 56
        x = tx0 + 16 + i * 22
        for j, col in enumerate(STRATA[i:i + 3]):
            c.put(c.mask(lambda p: p.rect(x, cy - 4 + j * 0 - 2, x + 18, cy + 2)), col)
        c.put(c.mask(lambda p: p.rect(x + j * 6, cy - 6, x + j * 6 + 6, cy)), STRATA[(i + 2) % len(STRATA)])
    c.put(c.mask(lambda p: (p.rect(tx1 - 60, FLOOR - 58, tx1 - 52, FLOOR - 50), p.rect(tx1 - 70, FLOOR - 62, tx1 - 44, FLOOR - 56))), (70, 70, 76))
    c.put(c.mask(lambda p: (p.ring(tx1 - 26, FLOOR - 58, 6, 1.6), p.line([(tx1 - 22, FLOOR - 54), (tx1 - 14, FLOOR - 50)], 2))), (150, 120, 70))
    # Her board of the layers: the top layer's dinosaurs crossed out and
    # written back in, crossed out, written back in.
    bx0, by0, bx1, by1 = 470, 330, 640, 450
    c.put(c.mask(box(bx0 - 6, by0 - 6, bx1 + 6, by1 + 6)), WOOD)
    c.put(c.mask(box(bx0, by0, bx1, by1)), SLATE)
    for i in range(6):
        y = by0 + 14 + i * 18
        c.put(c.mask(lambda p: p.rect(bx0 + 10, y, bx1 - 10, y + 1.2)), CHALK, 0.8)
    for i in range(4):
        y = by0 + 22 + i * 7
        c.put(c.mask(lambda p: p.line([(bx0 + 20 + i * 8, y), (bx0 + 60 + i * 8, y - 2)], 1.4)), CHALK)
        c.put(c.mask(lambda p: p.line([(bx0 + 16 + i * 8, y + 2), (bx0 + 64 + i * 8, y - 4)], 1.2)), (230, 120, 110))
    c.put(c.mask(lambda p: p.line([(bx1 - 50, by0 + 20), (bx1 - 30, by0 + 34), (bx1 - 14, by0 + 12)], 1.6)), CHALK)
    # Her wheelbarrow and sieve.
    c.put(c.mask(lambda p: p.poly([(1260, FLOOR - 40), (1340, FLOOR - 40), (1326, FLOOR - 14), (1270, FLOOR - 14)])), (90, 110, 90))
    c.put(c.mask(lambda p: (p.ring(1330, FLOOR - 10, 9, 3), p.line([(1260, FLOOR - 40), (1236, FLOOR - 24)], 3))), (50, 50, 54))
    c.put(c.mask(lambda p: p.ellipse(1290, FLOOR - 42, 30, 6)), STRATA[3])
    c.put(c.mask(lambda p: p.ring(1400, FLOOR - 30, 22, 3)), WOOD)
    c.put(c.mask(lambda p: [p.line([(1380 + i * 6, FLOOR - 44), (1380 + i * 6, FLOOR - 16)], 0.6) for i in range(7)]), (70, 70, 76))


PIECES: Dict[str, Piece] = {
    "ridge_sinkhole": Piece((SINKHOLE[0] - 20, RIDGE_ROAD - 70, SINKHOLE[1] + 20, RIDGE_ROAD + 32), sinkhole),
    "fossil_beds": Piece((16, 16, W - 16, FLOOR), beds),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
