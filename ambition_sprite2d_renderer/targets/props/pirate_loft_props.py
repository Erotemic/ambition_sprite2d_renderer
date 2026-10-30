"""The sail loft inside the net loft (`pirate_sail_loft`, PvN dimension), on
the Pirate Port's waterfront: where the port's sails and flags are sewn.

Drawn in room coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/pirate_port/make_specs.py` (`sail_loft`):
the floor (y 384), the ceiling (to y 32), the door out (x 40).

- `sail_loft_room`: plank walls under the rafters, nets hung to dry from
  them; bolts of canvas on shelves; a great sail spread across the floor,
  half sewn, its seams chalked; the sewing bench (a palm, needles, a ball
  of twine); and the flags to order pinned up: skulls with an eyepatch, a
  monocle, a moustache, a party hat, and one that is smiling, which was
  sent back.

Animations: ``idle``, 1 frame. No drop shadows.
"""

from __future__ import annotations

from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .pirate_port_props import PAL, PLANK, PLANK_DARK, ROPE, SAIL, TIMBER

W, FLOOR, CEIL = 1024, 384, 32
FLAG = (24, 22, 26)
BONE = (236, 230, 214)
CHALK = (240, 240, 236)


def skull(c, x, y, s, extra):
    """A Jolly Roger's skull and crossbones at (x, y), size s, and its touch."""
    c.put(c.mask(lambda p: (p.line([(x - s, y + s * 0.4), (x + s, y + s * 1.6)], s * 0.18), p.line([(x + s, y + s * 0.4), (x - s, y + s * 1.6)], s * 0.18))), BONE)
    c.put(c.mask(lambda p: (p.ellipse(x, y, s * 0.62, s * 0.58), p.rect(x - s * 0.34, y + s * 0.3, x + s * 0.34, y + s * 0.62))), BONE)
    c.put(c.mask(lambda p: [p.ellipse(x + dx, y, s * 0.16) for dx in (-s * 0.24, s * 0.24)]), FLAG)
    if extra == "patch":
        c.put(c.mask(lambda p: (p.ellipse(x - s * 0.24, y, s * 0.2), p.line([(x - s * 0.62, y - s * 0.3), (x + s * 0.6, y - s * 0.1)], 1))), FLAG)
    elif extra == "monocle":
        c.put(c.mask(lambda p: (p.ring(x + s * 0.24, y, s * 0.22, 1.2), p.line([(x + s * 0.44, y + s * 0.1), (x + s * 0.5, y + s * 0.6)], 0.8))), (220, 190, 90))
    elif extra == "moustache":
        c.put(c.mask(lambda p: p.poly([(x - s * 0.5, y + s * 0.3), (x, y + s * 0.2), (x + s * 0.5, y + s * 0.3), (x + s * 0.3, y + s * 0.4), (x, y + s * 0.32), (x - s * 0.3, y + s * 0.4)])), FLAG)
    elif extra == "party":
        c.put(c.mask(lambda p: p.poly([(x - s * 0.3, y - s * 0.5), (x + s * 0.3, y - s * 0.5), (x + s * 0.1, y - s * 1.3)])), (220, 80, 120))
    elif extra == "smile":
        c.put(c.mask(lambda p: p.line([(x - s * 0.24, y + s * 0.34), (x, y + s * 0.46), (x + s * 0.24, y + s * 0.34)], 1.2)), FLAG)


def room(c, k):
    rng = c.rand("loft")
    wall = c.mask(box(16, CEIL, W - 16, FLOOR))
    c.put(wall, PLANK)
    c.put(wall * c.mask(lambda p: [p.rect(x, CEIL, x + 1.2, FLOOR) for x in range(16, W, 18)]), PLANK_DARK)
    c.tone(wall * (c.noise("loft_planks", 30, 8, 2) - 0.5), 0.12)
    # The rafters, and nets hung from them to dry.
    c.put(c.mask(lambda p: [p.rect(16, y, W - 16, y + 10) for y in (CEIL, CEIL + 60)]), TIMBER)
    for nx in (140, 520, 840):
        net = c.mask(lambda p: p.poly([(nx, CEIL + 70), (nx + 120, CEIL + 70), (nx + 104, CEIL + 160), (nx + 16, CEIL + 150)]))
        grid = c.mask(lambda p: ([p.line([(x, CEIL + 68), (x - 6, CEIL + 162)], 0.5) for x in np.arange(nx, nx + 124, 6)],
                                 [p.line([(nx, y), (nx + 120, y)], 0.5) for y in np.arange(CEIL + 70, CEIL + 162, 6)]))
        c.put(grid * net, (60, 64, 58), 0.8)
        c.put(c.mask(lambda p: [p.ellipse(nx + 20 + j * 24, CEIL + 150 + (j % 2) * 4, 3) for j in range(4)]), (220, 140, 60))
    # The door out (the room's door zone, x 40..88).
    c.put(c.mask(box(34, FLOOR - 104, 94, FLOOR)), TIMBER)
    c.put(c.mask(box(40, FLOOR - 96, 88, FLOOR)), (110, 80, 54))
    c.put(c.mask(lambda p: p.ellipse(80, FLOOR - 50, 2.4)), (200, 170, 90))
    # Bolts of canvas on their shelves.
    for y in (210, 270):
        c.put(c.mask(lambda p: p.rect(120, y, 300, y + 6)), TIMBER)
        c.put(c.mask(lambda p: [p.ellipse(x, y - 12, 12, 12) for x in range(134, 296, 26)]), SAIL)
        c.put(c.mask(lambda p: [p.ring(x, y - 12, 6, 1) for x in range(134, 296, 26)]), mix(SAIL, (0, 0, 0), 0.2))
    # The great sail spread on the floor, half sewn, its seams chalked.
    sail = c.mask(lambda p: p.poly([(330, FLOOR), (740, FLOOR), (720, FLOOR - 26), (360, FLOOR - 20)]))
    c.put(sail, SAIL)
    c.put(sail * c.mask(lambda p: [p.line([(x, FLOOR), (x + 10, FLOOR - 24)], 0.8) for x in range(360, 740, 40)]), CHALK)
    c.put(c.mask(lambda p: [p.line([(x, FLOOR - 2), (x + 8, FLOOR - 22)], 1.4) for x in range(360, 560, 40)]), ROPE)
    # The sewing bench: a palm, needles, a ball of twine.
    c.put(c.mask(lambda p: (p.rect(760, FLOOR - 34, 900, FLOOR - 28), p.rect(766, FLOOR - 28, 772, FLOOR), p.rect(888, FLOOR - 28, 894, FLOOR))), TIMBER)
    c.put(c.mask(lambda p: p.ellipse(800, FLOOR - 40, 10, 6)), (150, 110, 70))
    c.put(c.mask(lambda p: [p.line([(830 + i * 6, FLOOR - 36), (840 + i * 6, FLOOR - 46)], 0.8) for i in range(3)]), (200, 200, 210))
    c.put(c.mask(lambda p: p.ellipse(870, FLOOR - 42, 8)), ROPE)
    # The flags to order, pinned up; one smiling, sent back.
    for i, (extra, fx) in enumerate((("patch", 400), ("monocle", 490), ("moustache", 580), ("party", 670), ("smile", 790))):
        fy = 200 if extra != "smile" else 230
        c.put(c.mask(box(fx - 36, fy - 30, fx + 36, fy + 30)), FLAG)
        c.put(c.mask(lambda p: [p.ellipse(fx + dx, fy - 28, 2) for dx in (-30, 30)]), (200, 60, 50))
        skull(c, fx, fy - 6, 18, extra)
    c.put(c.mask(lambda p: p.poly([(764, 268), (818, 258), (822, 270), (768, 280)])), (220, 60, 50), 0.9)


PIECES: Dict[str, Piece] = {
    "sail_loft_room": Piece((16, CEIL, W - 16, FLOOR), room),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
