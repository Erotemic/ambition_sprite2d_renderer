"""The hidden way under the Ninja Village (PvN dimension): down a loose board
in the street between the weaver's and the tea house, west under the street
to a stone slab in the gate shrine's floor (shut until the lever under it is
pulled). A ninja village has one; this one is lived in.

Drawn in room coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/ninja_village/make_specs.py` (`shrine`,
`street`, `hidden_way`): the shrine's floor (y 704, the room's foot 832) and
its slab (x 1320..1384); the street's ground (y 768, its foot 896) and its
loose board (x 1000..1064); the way's floor (y 512), its ceiling (to y 48),
the shaft up to the shrine (x 296..360) and the one up to the street
(x 1576..1640). Ladders are the engine's.

- `ninja_shrine_slab`: the stone slab in the shrine's floor (the look of
  the lock wall the way's lever opens), the paving round it.
- `ninja_shrine_shaft`: the shaft under the slab (seen once it is open).
- `ninja_street_board`: the loose board in the street and the dark under
  it (the board is a one-way floor: dropped through).
- `ninja_way_west`: a timbered passage dug in earth; the shaft up under the
  shrine; a straw dummy, a shuriken target with its stars in it; the
  nightingale floor (each board's nail drawn, a bird painted on one: it
  sings); a sleeping mat, a cold bowl of rice, a scroll.
- `ninja_way_east`: the weapons rack (a kusarigama, kunai, a blowpipe, a
  grappling hook); sliding panels, one open on a cupboard of disguises (a
  monk's hat, a rice farmer's, a fake moustache); the shaft up under the
  street, light through the board's gaps.

Animations: ``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .ninja_village_props import CEDAR, CEDAR_LIGHT, INDIGO, PAL, PAPER, SHOJI, STONE, TIMBER, VERMILION

SHRINE_FLOOR, SHRINE_H = 704, 832
SLAB = (1320, 1384)
STREET, STREET_H = 768, 896
BOARD = (1000, 1064)
W, FLOOR, CEIL = 1920, 512, 48
SHRINE_SHAFT = (296, 360)
STREET_SHAFT = (1576, 1640)
EARTH = (86, 66, 52)
EARTH_DARK = (58, 44, 36)
STRAW = (204, 176, 108)
STEEL = (150, 156, 166)
RICE = (244, 242, 236)
LAMP = (255, 206, 130)
DAYLIGHT = (250, 244, 220)
STONE_DARK = (98, 96, 90)


def slab(c, k):
    x0, x1 = SLAB
    c.put(c.mask(box(x0, SHRINE_FLOOR, x1, SHRINE_H)), STONE_DARK)
    s = c.mask(box(x0 + 2, SHRINE_FLOOR, x1 - 2, SHRINE_FLOOR + 14))
    c.put(s, STONE)
    c.put(c.mask(box(x0 + 2, SHRINE_FLOOR, x1 - 2, SHRINE_FLOOR + 2)), mix(STONE, (255, 255, 255), 0.3))
    # A finger hole in it, and a lotus cut in its face.
    c.put(c.mask(lambda p: p.ellipse(x1 - 12, SHRINE_FLOOR + 7, 3, 2.4)), (40, 40, 40))
    c.put(c.mask(lambda p: [p.ellipse((x0 + x1) / 2 + dx, SHRINE_FLOOR + 8, 4, 3) for dx in (-7, 0, 7)]), STONE_DARK)
    c.put(c.mask(lambda p: [p.rect(x0, y, x1, y + 1.2) for y in range(SHRINE_FLOOR + 28, SHRINE_H, 16)]), scale(STONE_DARK, 0.75))


def shrine_shaft(c, k):
    x0, x1 = SLAB
    sh = c.mask(box(x0, SHRINE_FLOOR, x1, SHRINE_H))
    c.put(sh, EARTH_DARK)
    c.put(sh * c.mask(lambda p: [p.rect(x0, y, x1, y + 4) for y in range(SHRINE_FLOOR + 20, SHRINE_H, 40)]), TIMBER)
    c.tone(sh * np.clip((c.y - SHRINE_FLOOR) / 100, 0, 1), -0.6)


def street_board(c, k):
    x0, x1 = BOARD
    sh = c.mask(box(x0, STREET, x1, STREET_H))
    c.put(sh, EARTH_DARK)
    c.tone(sh * np.clip((c.y - STREET) / 90, 0, 1), -0.6)
    # The loose board, a little proud of the street, one nail out.
    c.put(c.mask(box(x0 - 4, STREET - 2, x1 + 4, STREET + 6)), CEDAR)
    c.put(c.mask(lambda p: [p.rect(x, STREET - 2, x + 1.2, STREET + 6) for x in (x0 + 20, x0 + 44)]), scale(CEDAR, 0.7))
    c.put(c.mask(lambda p: (p.ellipse(x0 + 4, STREET + 2, 1.6), p.line([(x1 - 2, STREET - 2), (x1 + 2, STREET - 9)], 1.2))), STEEL)


def passage(c, x0, x1, seed):
    wall = c.mask(box(x0, CEIL, x1, FLOOR))
    c.put(wall, EARTH)
    c.tone(wall * (c.noise(seed, 30, 8, 3) - 0.5), 0.3)
    c.tone(wall * np.clip((CEIL + 120 - c.y) / 100, 0, 1), -0.4)
    # Timber sets: posts and caps, every 240.
    c.put(c.mask(lambda p: [p.rect(x, CEIL, x + 14, FLOOR) for x in range(int(x0) + 100, int(x1), 240)]), TIMBER)
    c.put(c.mask(lambda p: [p.rect(x - 20, CEIL, x + 34, CEIL + 12) for x in range(int(x0) + 100, int(x1), 240)]), TIMBER)
    c.put(c.mask(box(x0, 16, x1, CEIL)), scale(TIMBER, 0.8))
    c.put(c.mask(lambda p: [p.rect(x, 16, x + 1.2, CEIL) for x in range(int(x0), int(x1), 32)]), scale(TIMBER, 0.6))
    # Lamps on the posts.
    for x in range(int(x0) + 220, int(x1), 480):
        c.put(c.mask(lambda p: (p.rect(x - 6, 150, x + 6, 172), p.rect(x - 1, 140, x + 1, 150))), (40, 40, 44))
        c.put(c.mask(lambda p: p.rect(x - 4, 152, x + 4, 170)), PAPER)
        c.light(c.mask(lambda p: p.ellipse(x, 160, 80, 60), blur=16), LAMP, 0.25)


def shaft(c, s0, s1, light):
    c.put(c.mask(box(s0, 16, s1, CEIL)), EARTH_DARK)
    if light:
        c.light(c.mask(lambda p: p.poly([(s0, 16), (s1, 16), (s1 + 24, FLOOR), (s0 - 24, FLOOR)]), blur=10), DAYLIGHT, 0.16)


def west(c, k):
    passage(c, 16, 960, "way_w")
    shaft(c, *SHRINE_SHAFT, light=False)
    # The sleeping mat, the cold bowl of rice, chopsticks across it.
    c.put(c.mask(box(60, FLOOR - 8, 250, FLOOR)), STRAW)
    c.put(c.mask(lambda p: [p.rect(x, FLOOR - 8, x + 1, FLOOR) for x in range(64, 250, 8)]), scale(STRAW, 0.8))
    c.put(c.mask(lambda p: p.poly([(200, FLOOR - 8), (230, FLOOR - 8), (226, FLOOR - 22), (204, FLOOR - 22)])), INDIGO)
    c.put(c.mask(lambda p: p.ellipse(215, FLOOR - 23, 12, 5)), RICE)
    c.put(c.mask(lambda p: p.line([(196, FLOOR - 26), (236, FLOOR - 30)], 1.4)), CEDAR_LIGHT)
    # A scroll hung on the wall.
    c.put(c.mask(box(130, 200, 170, 330)), PAPER)
    c.put(c.mask(lambda p: [p.rect(126, y, 174, y + 5) for y in (196, 330)]), TIMBER)
    c.put(c.mask(lambda p: [p.rect(146, y, 154, y + 10) for y in range(214, 316, 18)]), (30, 30, 30))
    # The straw dummy, a shuriken target with its stars in it.
    dx = 460
    c.put(c.mask(lambda p: (p.rect(dx - 3, FLOOR - 130, dx + 3, FLOOR), p.ellipse(dx, FLOOR - 140, 14, 16),
                            p.rect(dx - 40, FLOOR - 112, dx + 40, FLOOR - 104), p.poly([(dx - 18, FLOOR - 120), (dx + 18, FLOOR - 120), (dx + 14, FLOOR - 60), (dx - 14, FLOOR - 60)]))), STRAW)
    c.put(c.mask(lambda p: [p.rect(dx - 18, y, dx + 18, y + 2) for y in (FLOOR - 100, FLOOR - 80)]), scale(STRAW, 0.6))
    tx, ty = 620, 260
    c.put(c.mask(lambda p: p.ellipse(tx, ty, 44)), CEDAR_LIGHT)
    c.put(c.mask(lambda p: (p.ring(tx, ty, 30, 4), p.ring(tx, ty, 14, 4))), VERMILION)
    for sx, sy in ((tx - 6, ty + 4), (tx + 20, ty - 18), (tx - 28, ty - 10), (dx + 8, FLOOR - 140)):
        c.put(c.mask(lambda p: p.poly([(sx, sy - 8), (sx + 2, sy - 2), (sx + 8, sy), (sx + 2, sy + 2), (sx, sy + 8), (sx - 2, sy + 2), (sx - 8, sy), (sx - 2, sy - 2)])), STEEL)
    # The nightingale floor: each board's nail, a bird on one (it sings).
    n0, n1 = 700, 940
    c.put(c.mask(box(n0, FLOOR - 6, n1, FLOOR)), CEDAR_LIGHT)
    c.put(c.mask(lambda p: [p.rect(x, FLOOR - 6, x + 1.2, FLOOR) for x in range(n0, n1, 24)]), scale(CEDAR_LIGHT, 0.6))
    c.put(c.mask(lambda p: [p.ellipse(x + 12, FLOOR - 3, 1.4) for x in range(n0, n1, 24)]), STEEL)
    c.put(c.mask(lambda p: (p.ellipse(820, FLOOR - 18, 8, 6), p.ellipse(827, FLOOR - 23, 4, 4))), (110, 120, 70))
    c.put(c.mask(lambda p: [p.line([(834, FLOOR - 26 - i * 6), (846 + i * 4, FLOOR - 34 - i * 8)], 1) for i in range(3)]), PAPER)


def east(c, k):
    passage(c, 960, W - 16, "way_e")
    shaft(c, *STREET_SHAFT, light=True)
    # The weapons rack.
    rx = 1120
    c.put(c.mask(lambda p: (p.rect(rx, 200, rx + 200, 210), p.rect(rx, 330, rx + 200, 340), p.rect(rx + 4, 200, rx + 12, FLOOR), p.rect(rx + 188, 200, rx + 196, FLOOR))), TIMBER)
    c.put(c.mask(lambda p: (p.line([(rx + 40, 196), (rx + 40, 330)], 3), p.poly([(rx + 40, 196), (rx + 62, 186), (rx + 44, 206)]))), STEEL)
    c.put(c.mask(lambda p: [p.ring(rx + 40, 340 + j * 10, 4, 1.4) for j in range(8)]), STEEL)
    c.put(c.mask(lambda p: [p.poly([(x, 214), (x + 4, 214), (x + 2, 250)]) for x in range(rx + 80, rx + 140, 12)]), STEEL)
    c.put(c.mask(lambda p: p.line([(rx + 160, 196), (rx + 160, 330)], 3)), CEDAR_LIGHT)
    c.put(c.mask(lambda p: (p.line([(rx + 120, 344), (rx + 120, 400)], 2), p.line([(rx + 120, 400), (rx + 104, 412)], 2),
                            p.line([(rx + 120, 400), (rx + 136, 412)], 2), p.line([(rx + 120, 400), (rx + 120, 416)], 2))), STEEL)
    # Sliding panels, one open on a cupboard of disguises.
    px0 = 1720
    c.put(c.mask(box(px0, 160, px0 + 160, FLOOR)), TIMBER)
    c.put(c.mask(box(px0 + 6, 166, px0 + 76, FLOOR - 6)), SHOJI)
    c.put(c.mask(lambda p: [p.rect(px0 + 6, y, px0 + 76, y + 2) for y in range(200, FLOOR, 48)]), TIMBER)
    c.put(c.mask(box(px0 + 82, 166, px0 + 154, FLOOR - 6)), (40, 30, 26))
    c.put(c.mask(lambda p: p.poly([(px0 + 92, 220), (px0 + 144, 220), (px0 + 118, 196)])), STRAW)
    c.put(c.mask(lambda p: p.ellipse(px0 + 118, 270, 26, 8)), STRAW)
    c.put(c.mask(lambda p: p.rect(px0 + 112, 270, px0 + 124, 290)), STRAW)
    c.put(c.mask(lambda p: p.poly([(px0 + 100, 340), (px0 + 118, 334), (px0 + 136, 340), (px0 + 118, 346)])), (40, 28, 20))
    c.put(c.mask(lambda p: p.poly([(px0 + 96, 400), (px0 + 140, 400), (px0 + 136, FLOOR - 8), (px0 + 100, FLOOR - 8)])), (150, 110, 60))


PIECES: Dict[str, Piece] = {
    "ninja_shrine_slab": Piece((SLAB[0], SHRINE_FLOOR, SLAB[1], SHRINE_H), slab),
    "ninja_shrine_shaft": Piece((SLAB[0], SHRINE_FLOOR, SLAB[1], SHRINE_H), shrine_shaft),
    "ninja_street_board": Piece((BOARD[0] - 4, STREET - 10, BOARD[1] + 4, STREET_H), street_board),
    "ninja_way_west": Piece((16, 16, 960, FLOOR), west),
    "ninja_way_east": Piece((960, 16, W - 16, FLOOR), east),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
