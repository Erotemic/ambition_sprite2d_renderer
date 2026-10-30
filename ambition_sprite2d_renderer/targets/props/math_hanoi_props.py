"""The Tower of Hanoi (`math_tower_of_hanoi`, the Math dimension): an
undercroft west of the gate hall, where the monks move the golden disks
between three diamond needles, one at a time, never a larger on a smaller;
when the last disk is moved, the world ends.

Drawn in room coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/math_town/make_specs.py` (`tower_of_hanoi`):
the floor (y 704), the vault (to y 48), the needles (NEEDLES) and the disks
on them (STACKS: needle, the disks' sizes bottom up), each disk walked on.

- `hanoi_temple`: the vault and its arches; the three needles of diamond on
  their dais; the golden disks, the puzzle part done; the monks' tally of
  moves on the wall; lamps.

Animations: ``idle``, 1 frame. No drop shadows.
"""

from __future__ import annotations

from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .eureka_props import ashlar
from .math_town_terraces import PAL

W, FLOOR, VAULT = 1600, 704, 48
NEEDLES = (360, 800, 1240)
#: Each needle's disks, bottom up, by size (1 the smallest).
STACKS = ((8, 7, 6, 5, 2), (4, 3), (1,))
DISK_H = 24
STONE = (176, 168, 150)
STONE_DARK = (130, 122, 108)
GOLD = (226, 180, 70)
GOLD_LIGHT = (255, 226, 140)
GOLD_DARK = (170, 122, 40)
DIAMOND = (210, 236, 250)
LAMP = (255, 220, 150)


def disk_width(size):
    return 60 + 30 * size


def temple(c, k):
    ashlar(c, 16, VAULT, W - 16, FLOOR, STONE, course=24, block=48, tag="hanoi", vary=0.05)
    c.tone(c.mask(box(16, VAULT, W - 16, FLOOR)) * np.clip((240 - c.y) / 190, 0, 1), -0.3)
    for x in range(160, W, 440):
        c.put(c.mask(lambda p: p.arch(x, 120, x + 280, FLOOR - 60)), STONE_DARK)
        c.put(c.mask(lambda p: p.arch(x + 10, 130, x + 270, FLOOR - 60)), scale(STONE_DARK, 0.75))
    # The dais under the needles.
    c.put(c.mask(box(180, FLOOR - 8, 1420, FLOOR)), STONE_DARK)
    # The needles of diamond, and the golden disks on them.
    for nx, stack in zip(NEEDLES, STACKS):
        c.put(c.mask(lambda p: p.poly([(nx - 5, FLOOR - 8), (nx + 5, FLOOR - 8), (nx + 2, FLOOR - 280), (nx, FLOOR - 296), (nx - 2, FLOOR - 280)])), DIAMOND)
        c.put(c.mask(lambda p: p.line([(nx - 2, FLOOR - 10), (nx - 1, FLOOR - 280)], 1)), (255, 255, 255))
        c.light(c.mask(lambda p: p.ellipse(nx, FLOOR - 290, 10), blur=6), (230, 245, 255), 0.6)
        for i, size in enumerate(stack):
            w = disk_width(size)
            top = FLOOR - DISK_H * (i + 1)
            disk = c.mask(lambda p: p.rect(nx - w / 2, top, nx + w / 2, top + DISK_H - 1))
            c.put(disk, GOLD)
            c.tone(disk * np.clip((c.x - nx) / (w / 2), -1, 1), -0.2)
            c.put(c.mask(lambda p: p.rect(nx - w / 2, top, nx + w / 2, top + 3)), GOLD_LIGHT)
            c.put(c.mask(lambda p: p.rect(nx - w / 2, top + DISK_H - 4, nx + w / 2, top + DISK_H - 1)), GOLD_DARK)
            c.put(c.mask(lambda p: p.rect(nx - 6, top + 4, nx + 6, top + DISK_H - 5)), GOLD_DARK)
    # The monks' tally of moves on the wall, in columns of strokes.
    rng = c.rand("tally")
    c.put(c.mask(box(560, 160, 1040, 300)), (200, 192, 172))
    c.put(c.mask(lambda p: [p.rect(x, y, x + 1.4, y + 10) for x in np.arange(572, 1030, 5) for y in np.arange(172, 290, 16) if rng.uniform(0, 1) < 0.97]), (90, 80, 70), 0.8)
    # Lamps hung in the arches.
    for x in (300, 740, 1180):
        c.put(c.mask(lambda p: (p.rect(x - 1, VAULT, x + 1, 150), p.rect(x - 8, 150, x + 8, 168))), (120, 100, 70))
        c.put(c.mask(lambda p: p.rect(x - 5, 153, x + 5, 165)), LAMP)
        c.light(c.mask(lambda p: p.ellipse(x, 160, 80, 60), blur=20), LAMP, 0.3)


PIECES: Dict[str, Piece] = {
    "hanoi_temple": Piece((16, VAULT, W - 16, FLOOR), temple),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
