"""The Tower of Hanoi (`math_tower_of_hanoi`, the Math dimension): an
undercroft west of the gate hall, where the monks move the 64 golden disks
between three diamond needles, one at a time, never a larger on a smaller;
when the last disk is moved, the world ends.

Drawn in room coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/math_town/make_specs.py` (`tower_of_hanoi`):
the floor (y 704), the vault (to y 48), the needles (NEEDLES), the height
of a disk (DISK_H) and the width of each (`disk_width`). The room places
each needle and each disk as its own prop, so the puzzle is not painted
into the room: which disk is on which needle is the room's.

- `hanoi_temple`: the vault, the dark arches the needles stand in, the
  monks' tally of moves on the piers, the sconces.
- `hanoi_needle`: a needle of diamond in its brass socket (its frame is at
  the first needle; the room puts one at each).
- `hanoi_disk_01` .. `hanoi_disk_64`: the golden disks, smallest first. A
  disk's frame is the disk, its top centre at (0, 0).

Animations: ``idle``, 1 frame. No drop shadows.
"""

from __future__ import annotations

from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, scale
from .eureka_props import ashlar
from .math_town_terraces import PAL

W, FLOOR, VAULT = 1600, 704, 48
NEEDLES = (360, 800, 1240)
DISKS = 64
DISK_H = 8
#: How tall a needle stands over the floor: the 64 disks, and a hand more.
NEEDLE_H = 540
#: The needle's frame about its foot: half its width, and the room over its
#: point for its glint.
NEEDLE_HALF_W, NEEDLE_TIP_ROOM = 14, 14
#: The arch each needle stands in: half its width, and the top of its round.
ARCH_HALF_W, ARCH_TOP = 150, 140
STONE = (176, 168, 150)
STONE_DARK = (130, 122, 108)
GOLD = (226, 180, 70)
GOLD_LIGHT = (255, 230, 150)
GOLD_DARK = (150, 104, 34)
DIAMOND = (214, 238, 252)
DIAMOND_SHADE = (150, 188, 214)
BRASS = (176, 132, 62)
LAMP = (255, 220, 150)
TALLY = (84, 74, 64)


def disk_width(size):
    """The width of disk `size` (1 the smallest) in world units."""
    return 32 + 6 * size


def temple(c, k):
    del k
    ashlar(c, 16, VAULT, W - 16, FLOOR, STONE, course=24, block=48, tag="hanoi", vary=0.05)
    c.tone(c.mask(box(16, VAULT, W - 16, FLOOR)) * np.clip((240 - c.y) / 190, 0, 1), -0.3)
    # An arch behind each needle: a dark recess, its rim of dressed stone.
    for nx in NEEDLES:
        x0, x1 = nx - ARCH_HALF_W, nx + ARCH_HALF_W
        c.put(c.mask(lambda p: p.arch(x0 - 10, ARCH_TOP - 10, x1 + 10, FLOOR)), STONE_DARK)
        recess = c.mask(lambda p: p.arch(x0, ARCH_TOP, x1, FLOOR))
        c.put(recess, scale(STONE_DARK, 0.62))
        c.tone(recess * np.clip((c.y - ARCH_TOP) / (FLOOR - ARCH_TOP), 0, 1), -0.25)
    # The monks' tally of moves, in gates of five, over every pier.
    rng = c.rand("tally")
    piers = [(24, NEEDLES[0] - ARCH_HALF_W - 18)]
    piers += [(a + ARCH_HALF_W + 18, b - ARCH_HALF_W - 18) for a, b in zip(NEEDLES, NEEDLES[1:])]
    piers += [(NEEDLES[-1] + ARCH_HALF_W + 18, W - 24)]

    def gates(p):
        for px0, px1 in piers:
            for y in np.arange(176, FLOOR - 40, 20):
                for x in np.arange(px0 + 4, px1 - 14, 15):
                    if rng.uniform(0, 1) > 0.94:
                        continue
                    for i in range(4):
                        p.rect(x + 2.4 * i, y, x + 2.4 * i + 1.1, y + 12)
                    p.line([(x - 1, y + 10), (x + 9.5, y + 2)], 1.0)

    c.put(c.mask(gates), TALLY, 0.75)
    # A sconce on each pier, between the tally's columns.
    for px0, px1 in piers:
        x = (px0 + px1) / 2
        c.put(c.mask(lambda p: (p.rect(x - 9, 300, x + 9, 304), p.poly([(x - 7, 304), (x + 7, 304), (x + 3, 318), (x - 3, 318)]))), BRASS)
        c.put(c.mask(lambda p: p.ellipse(x, 294, 4, 7)), LAMP)
        c.light(c.mask(lambda p: p.ellipse(x, 296, 70, 60), blur=22), LAMP, 0.28)


def needle(c, k):
    """A needle of diamond, cut in facets, standing in a brass socket."""
    del k
    nx, top = NEEDLES[0], FLOOR - NEEDLE_H
    shaft = c.mask(lambda p: p.poly([(nx - 5, FLOOR - 6), (nx + 5, FLOOR - 6), (nx + 2.2, top + 20), (nx, top), (nx - 2.2, top + 20)]))
    c.put(shaft, DIAMOND)
    # The far facet is in shade; the near edge catches the light.
    c.put(shaft * (c.x > nx + 0.4), DIAMOND_SHADE, 0.8)
    c.put(c.mask(lambda p: p.line([(nx - 2.6, FLOOR - 10), (nx - 0.9, top + 22)], 1.0)), (255, 255, 255), 0.9)
    # Bands where the facets are cut.
    for y in np.arange(top + 60, FLOOR - 20, 64):
        c.tone(shaft * ((c.y > y) & (c.y < y + 1.5)), -0.18)
    c.light(c.mask(lambda p: p.ellipse(nx, top + 6, 9), blur=5), (230, 245, 255), 0.7)
    # The socket: a brass collar on a stone step.
    c.put(c.mask(box(nx - 13, FLOOR - 4, nx + 13, FLOOR)), STONE_DARK)
    collar = c.mask(lambda p: p.poly([(nx - 9, FLOOR - 4), (nx + 9, FLOOR - 4), (nx + 6, FLOOR - 12), (nx - 6, FLOOR - 12)]))
    c.put(collar, BRASS)
    c.tone(collar * np.clip((c.x - nx) / 9, -1, 1), -0.25)


def disk(size):
    """Golden disk `size`, seen from the side: a cylinder lit from the left,
    its top rim bright, its underside dark, its ends rounded."""
    w = disk_width(size)

    def draw(c, k):
        del k
        r = w / 2
        body = c.mask(lambda p: (p.rect(-r + 2, 0, r - 2, DISK_H), p.rect(-r, 1.5, r, DISK_H - 1.5),
                                 p.ellipse(-r + 2, 2, 2), p.ellipse(r - 2, 2, 2),
                                 p.ellipse(-r + 2, DISK_H - 2, 2), p.ellipse(r - 2, DISK_H - 2, 2)))
        u = c.x / r
        # Round in the light: brightest a third of the way from the lit end.
        shade = np.interp(u, [-1, -0.75, -0.35, 0.2, 0.75, 1], [0.62, 0.92, 1.12, 1.0, 0.78, 0.6])
        paint = np.clip(np.asarray(GOLD, np.float32)[None, None, :] * shade[:, :, None], 0, 255)
        c.paint(body, paint)
        c.put(body * (c.y < 1.6), GOLD_LIGHT, 0.85)
        c.put(body * (c.y > DISK_H - 1.6), GOLD_DARK, 0.9)
        # A gleam on the lit side of the rim.
        c.put(c.mask(lambda p: p.rect(-r * 0.55, 0.3, -r * 0.15, 1.4)), (255, 248, 214), 0.7)

    return Piece((-w / 2, 0, w / 2, DISK_H), draw)


PIECES: Dict[str, Piece] = {
    "hanoi_temple": Piece((16, VAULT, W - 16, FLOOR), temple),
    "hanoi_needle": Piece((NEEDLES[0] - NEEDLE_HALF_W, FLOOR - NEEDLE_H - NEEDLE_TIP_ROOM, NEEDLES[0] + NEEDLE_HALF_W, FLOOR), needle),
    **{f"hanoi_disk_{size:02d}": disk(size) for size in range(1, DISKS + 1)},
}

TARGETS = targets(PIECES, PAL)

__all__ = ["DISKS", "DISK_H", "NEEDLES", "NEEDLE_H", "PIECES", "TARGETS", "disk_width"]
