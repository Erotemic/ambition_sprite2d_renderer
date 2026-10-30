"""The amber vault (`primeval_amber_vault`, the jungle dimension): behind a
cracked wall at the fossil beds' west end, a pocket of amber the survey
missed, and what is in it.

Drawn in room coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/primeval/tar_pits.py` (`fossil_beds`,
`amber_vault`): the beds' floor (y 576) and the cracked wall over their way
west (x 16..48, 112 high); the vault's floor (y 576), its roof (to y 64).

- `fossil_cracked_wall`: the strata over the way west, cracked through, a
  glow of amber in the crack (the look of a breakable wall: hit it).
- `amber_vault_room`: walls of amber, lit from inside; in it, set like
  jewels: a mosquito (very full), a beetle, a fern, a tiny three-toed foot,
  and a ranger's sandwich (recent; nobody can explain it). A survey peg with
  its flag, planted by the first one in.

Animations: ``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .primeval_props import PAL

FLOOR, ROOF = 576, 64
CRACK = (16, 48, FLOOR - 112)
W = 640
ROCK = (150, 118, 96)
ROCK_DARK = (110, 84, 66)
AMBER = (232, 150, 40)
AMBER_DEEP = (190, 100, 20)
AMBER_LIGHT = (255, 210, 110)
INSECT = (50, 34, 22)
FERN = (90, 110, 40)
BREAD = (220, 190, 130)
LETTUCE = (120, 170, 70)
FLAG = (230, 80, 60)


def cracked_wall(c, k):
    x0, x1, y0 = CRACK
    m = c.mask(box(x0, y0, x1, FLOOR))
    c.put(m, ROCK)
    c.put(m * c.mask(lambda p: [p.rect(x0, y, x1, y + 2) for y in range(int(y0) + 14, FLOOR, 22)]), ROCK_DARK)
    crack = [(x0 + 20, y0), (x0 + 10, y0 + 30), (x0 + 22, y0 + 58), (x0 + 9, y0 + 88), (x0 + 16, FLOOR)]
    c.put(c.mask(lambda p: p.line(crack, 3)), AMBER_DEEP)
    c.put(c.mask(lambda p: p.line(crack, 1.2)), AMBER_LIGHT)
    c.light(c.mask(lambda p: p.line(crack, 4), blur=4), AMBER, 0.35)


def gem(c, x, y, rx, ry):
    """A lump of amber set in the wall: its body, a highlight."""
    c.put(c.mask(lambda p: p.ellipse(x, y, rx, ry)), AMBER_DEEP)
    c.put(c.mask(lambda p: p.ellipse(x - rx * 0.1, y - ry * 0.1, rx * 0.85, ry * 0.8)), AMBER)
    c.put(c.mask(lambda p: p.ellipse(x - rx * 0.4, y - ry * 0.45, rx * 0.25, ry * 0.15)), AMBER_LIGHT)


def room(c, k):
    wall = c.mask(box(16, ROOF, W - 16, FLOOR))
    c.put(wall, mix(AMBER_DEEP, (60, 30, 10), 0.4))
    c.put(wall * (c.noise("amber_vault", 10, 6, 3) > 0.5), AMBER_DEEP, 0.7)
    c.light(c.mask(lambda p: p.ellipse(W / 2, 320, 300, 220), blur=40), AMBER_LIGHT, 0.3)
    c.put(c.mask(box(16, 16, W - 16, ROOF)), ROCK_DARK)
    # The mosquito (very full).
    gem(c, 320, 210, 70, 56)
    c.put(c.mask(lambda p: (p.ellipse(320, 216, 22, 14), p.ellipse(296, 206, 8, 7), p.line([(288, 204), (262, 196)], 1.4),
                            *[p.line([(312 + i * 8, 222), (300 + i * 12, 244)], 1.2) for i in range(3)],
                            *[p.line([(312 + i * 8, 210), (300 + i * 14, 186)], 1.2) for i in range(3)])), INSECT)
    c.put(c.mask(lambda p: p.ellipse(330, 218, 14, 9)), (150, 30, 30))
    c.put(c.mask(lambda p: [p.ellipse(318 + dx, 196, 16, 6) for dx in (-6, 10)]), (230, 230, 230), 0.4)
    # A beetle; a fern; the tiny foot.
    gem(c, 130, 300, 40, 34)
    c.put(c.mask(lambda p: (p.ellipse(130, 302, 14, 10), p.ellipse(130, 290, 7, 6), *[p.line([(122, 296 + i * 6), (106, 300 + i * 8)], 1.2) for i in range(3)])), INSECT)
    gem(c, 510, 300, 44, 40)
    c.put(c.mask(lambda p: (p.line([(496, 330), (520, 270)], 1.6), *[p.line([(500 + i * 4, 318 - i * 9), (490 + i * 4 + (i % 2) * 22, 310 - i * 9)], 1.4) for i in range(5)])), FERN)
    gem(c, 200, 450, 36, 30)
    c.put(c.mask(lambda p: [p.line([(200, 470), (200 + dx, 440)], 2.4) for dx in (-12, 0, 12)]), INSECT)
    # The ranger's sandwich (recent).
    gem(c, 440, 460, 46, 34)
    c.put(c.mask(lambda p: p.poly([(410, 476), (470, 476), (440, 446)])), BREAD)
    c.put(c.mask(lambda p: p.line([(414, 470), (466, 470)], 2)), LETTUCE)
    # The survey peg and its flag, planted by the first one in.
    c.put(c.mask(lambda p: p.rect(590, FLOOR - 70, 594, FLOOR)), (150, 120, 80))
    c.put(c.mask(lambda p: p.poly([(594, FLOOR - 70), (618, FLOOR - 62), (594, FLOOR - 54)])), FLAG)


PIECES: Dict[str, Piece] = {
    "fossil_cracked_wall": Piece((CRACK[0], CRACK[2], CRACK[1], FLOOR), cracked_wall),
    "amber_vault_room": Piece((16, 16, W - 16, FLOOR), room),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
