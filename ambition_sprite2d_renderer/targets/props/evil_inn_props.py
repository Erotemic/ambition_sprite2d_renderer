"""The Crooked Lantern (the Evil dimension): an inn at the far west end of the
Searchlight Moor, the one warm light on it, where the people who live under
the castle drink.

Drawn in room coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/evil_moor/make_specs.py`: on the moor, the
ground (y 656) and the inn's door (x 120..168); inside, the floor (y 448),
the ceiling (to y 32), the door out (x 40), the bar (x 560..840), the
innkeeper behind it, the trapper by the fire.

- `moor_inn_front`: a crooked timber inn leaning on its chimney, shutters
  lit from inside, its lantern hung askew on a bracket, the sign of a bent
  lantern, a water butt, a bench.
- `moor_crypt_gate`, `crypt_room`: the gate down to the founder's crypt
  beside his plinth, and the crypt: niches of bones, his busts (pointing),
  the sarcophagus (its lid walked on), candles.
- `inn_room`: low beams, a fire, the bar and its barrels, mugs on hooks,
  the castle's WANTED posters (the robot's among them) and, tucked behind a
  picture of the castle, the locals' map of the searchlights' blind spots.

Near-black and red outside like the moor; warm inside. Animations:
``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .eureka_props import Batch, edge_line, panels
from .evil_forest_props import NEAR_BLACK, PAL, rim

MOOR_FLOOR = 656
INN_DOOR = (120, 168)
W, FLOOR, CEILING = 1024, 448, 32
BAR = (560, 840)
TIMBER = (52, 36, 30)
TIMBER_LIGHT = (110, 76, 52)
PLASTER = (120, 104, 90)
LAMP = (255, 196, 110)
WOOD = (120, 84, 56)
WOOD_DARK = (74, 50, 34)


def inn_front(c, k):
    g = MOOR_FLOOR
    d0, d1 = INN_DOOR
    # The house, leaning: plaster between timbers, a crooked roof.
    house = c.mask(lambda p: p.poly([(24, g), (268, g), (272, g - 150), (30, g - 140)]))
    c.put(house, PLASTER)
    c.tone(house * (c.noise("inn_plaster", 6, 4, 2) - 0.5), 0.25)
    c.put(c.mask(lambda p: (p.line([(24, g), (30, g - 140)], 8), p.line([(268, g), (272, g - 150)], 8), p.line([(28, g - 72), (270, g - 76)], 6),
                            p.line([(30, g - 140), (150, g - 72)], 5), p.line([(150, g - 72), (272, g - 150)], 5))), TIMBER)
    c.put(c.mask(lambda p: p.poly([(6, g - 132), (150, g - 226), (294, g - 140), (272, g - 150), (30, g - 140)])), NEAR_BLACK)
    c.put(c.mask(lambda p: [p.line([(x, g - 132 - (x - 6) * 0.65 if x < 150 else g - 226 + (x - 150) * 0.6), (x + 4, g - 128)], 1.2) for x in range(14, 290, 10)]), (60, 40, 40))
    # The chimney it leans on, smoke.
    c.put(c.mask(lambda p: p.poly([(230, g - 150), (256, g - 150), (262, g - 240), (238, g - 244)])), (70, 56, 52))
    c.put(c.mask(lambda p: p.line([(250, g - 250), (240, g - 280), (256, g - 310), (244, g - 340)], 10), blur=8), (150, 140, 150), 0.3)
    # Shutters lit from inside, the door's frame.
    for x0 in (50, 196):
        win = c.mask(box(x0, g - 120, x0 + 40, g - 86))
        c.put(win, LAMP)
        c.light(c.mask(lambda p: p.ellipse(x0 + 20, g - 103, 50, 36), blur=14), LAMP, 0.35)
        c.put(c.mask(lambda p: (p.rect(x0 + 19, g - 120, x0 + 21, g - 86), p.rect(x0, g - 104, x0 + 40, g - 102))), TIMBER)
        c.put(c.mask(lambda p: (p.poly([(x0 - 14, g - 122), (x0, g - 120), (x0, g - 84), (x0 - 14, g - 82)]), p.poly([(x0 + 40, g - 120), (x0 + 54, g - 122), (x0 + 54, g - 82), (x0 + 40, g - 84)]))), (70, 30, 30))
    c.put(c.mask(box(d0 - 8, g - 104, d1 + 8, g)), TIMBER)
    c.put(c.mask(box(d0, g - 96, d1, g)), (40, 26, 20))
    c.light(c.mask(box(d0 + 4, g - 92, d1 - 4, g - 2)), LAMP, 0.2)
    # The lantern on its bracket, hung askew: the warm light of the moor.
    c.put(c.mask(lambda p: (p.line([(272, g - 160), (316, g - 168)], 3), p.line([(272, g - 130), (300, g - 166)], 2))), TIMBER)
    lx, ly = 316, g - 150
    c.put(c.mask(lambda p: p.line([(316, g - 168), (lx - 3, ly - 12)], 1.2)), (40, 40, 40))
    lan = c.mask(lambda p: p.poly([(lx - 12, ly - 12), (lx + 6, ly - 16), (lx + 10, ly + 8), (lx - 8, ly + 12)]))
    c.put(lan, LAMP)
    c.light(c.mask(lambda p: p.ellipse(lx, ly, 90), blur=26), LAMP, 0.35)
    c.put(c.mask(lambda p: p.line([(lx - 12, ly - 12), (lx + 6, ly - 16), (lx + 10, ly + 8), (lx - 8, ly + 12), (lx - 12, ly - 12)], 1.6)), NEAR_BLACK)
    # The sign: a lantern, bent, on a board.
    c.put(c.mask(lambda p: (p.line([(170, g - 150), (230, g - 150)], 3), p.rect(176, g - 150, 178, g - 136), p.rect(222, g - 150, 224, g - 136))), TIMBER)
    c.put(c.mask(box(168, g - 136, 232, g - 104)), (90, 60, 40))
    c.put(c.mask(lambda p: (p.line([(192, g - 128), (200, g - 122), (196, g - 110)], 2), p.poly([(196, g - 122), (210, g - 118), (206, g - 108), (194, g - 112)]))), LAMP)
    # A water butt and a bench.
    c.put(c.mask(lambda p: (p.rect(236, g - 40, 264, g), p.ellipse(250, g - 40, 14, 4))), WOOD_DARK)
    c.put(c.mask(lambda p: [p.rect(236, y, 264, y + 2) for y in (g - 32, g - 12)]), (40, 40, 44))
    c.put(c.mask(lambda p: (p.rect(40, g - 20, 104, g - 16), p.rect(44, g - 16, 48, g), p.rect(96, g - 16, 100, g))), WOOD)
    rim(c, house, 0.4)


def inn_room(c, k):
    g = FLOOR
    # Plaster and beams, a low ceiling.
    wall = c.mask(box(16, CEILING, W - 16, g))
    c.put(wall, (150, 120, 92))
    c.tone(wall * (c.noise("inn_wall", 8, 4, 2) - 0.5), 0.2)
    b = Batch(c)
    for x in range(16, W, 160):
        b.add(TIMBER, 1.0, box(x, CEILING, x + 14, g))
    b.add(TIMBER, 1.0, box(16, CEILING, W - 16, CEILING + 20))
    b.add(TIMBER, 1.0, box(16, g - 110, W - 16, g - 102))
    b.draw()
    panels(c, 16, g - 102, W - 16, g, WOOD_DARK, 12, "inn_wainscot")
    # The fire, west of the bar.
    fx = 330
    c.put(c.mask(lambda p: p.poly([(fx - 70, g), (fx - 70, g - 120), (fx - 50, g - 140), (fx + 50, g - 140), (fx + 70, g - 120), (fx + 70, g)])), (90, 80, 76))
    c.put(c.mask(lambda p: (p.rect(fx - 44, g - 90, fx + 44, g), p.ellipse(fx, g - 90, 44, 16))), (30, 20, 18))
    c.put(c.mask(lambda p: [p.poly([(fx + dx - 10, g - 4), (fx + dx, g - 34 - abs(dx) * 0.2), (fx + dx + 10, g - 4)]) for dx in (-24, -6, 12, 28)]), (255, 150, 50))
    c.light(c.mask(lambda p: p.ellipse(fx, g - 30, 180, 90), blur=24), LAMP, 0.35)
    # The bar and its barrels, mugs on hooks.
    b0, b1 = BAR
    panels(c, b0, g - 44, b1, g, WOOD, 6, "inn_bar")
    edge_line(c, b0 - 6, b1 + 6, g - 46, (170, 120, 80), 4)
    for x in (b0 + 30, b0 + 80, b1 - 80):
        m = c.mask(lambda p: p.ellipse(x, g - 140, 20, 16))
        c.put(m, WOOD)
        c.put(m * c.mask(lambda p: [p.rect(x - 20, y, x + 20, y + 2) for y in (g - 150, g - 132)]), (40, 40, 44))
        c.put(c.mask(lambda p: p.ellipse(x, g - 140, 4)), (60, 40, 30))
    c.put(c.mask(lambda p: (p.rect(b0 + 4, g - 124, b1 - 60, g - 120), [p.rect(x, g - 120, x + 4, g - 102) for x in (b0 + 8, b1 - 66)])), TIMBER)
    c.put(c.mask(box(b0, g - 160, b1, g - 156)), TIMBER)
    c.put(c.mask(lambda p: [p.rect(x - 4, g - 154, x + 4, g - 142) for x in range(b0 + 140, b1 - 100, 18)]), (200, 196, 186))
    # WANTED posters (the robot's among them), and the picture of the castle
    # with a map tucked behind it.
    for i, (x, wanted_robot) in enumerate(((640, True), (700, False), (760, False))):
        y = 120
        c.put(c.mask(box(x, y, x + 46, y + 60)), (226, 210, 170))
        c.put(c.mask(box(x + 6, y + 4, x + 40, y + 12)), (120, 40, 36))
        if wanted_robot:
            c.put(c.mask(lambda p: (p.ellipse(x + 23, y + 32, 12, 10), p.rect(x + 14, y + 40, x + 32, y + 54))), (230, 232, 236))
            c.put(c.mask(lambda p: [p.ellipse(x + 23 + d, y + 31, 2.4) for d in (-5, 5)]), (40, 200, 230))
        else:
            c.put(c.mask(lambda p: (p.ellipse(x + 23, y + 32, 10, 11), p.rect(x + 13, y + 42, x + 33, y + 54))), (90, 80, 70))
    px0, py0 = 140, 110
    c.put(c.mask(lambda p: p.poly([(px0 + 70, py0 + 6), (px0 + 112, py0 - 4), (px0 + 116, py0 + 54), (px0 + 74, py0 + 60)])), (220, 210, 180))
    c.put(c.mask(lambda p: [p.ellipse(px0 + 82 + i * 8, py0 + 30 + 6 * math.sin(i), 1.4) for i in range(4)]), (160, 40, 40))
    c.put(c.mask(box(px0, py0, px0 + 90, py0 + 64)), (90, 60, 40))
    c.put(c.mask(box(px0 + 5, py0 + 5, px0 + 85, py0 + 59)), (90, 30, 30))
    c.put(c.mask(lambda p: p.poly([(px0 + 20, py0 + 59), (px0 + 30, py0 + 30), (px0 + 40, py0 + 36), (px0 + 50, py0 + 22), (px0 + 62, py0 + 40), (px0 + 70, py0 + 59)])), (30, 20, 24))
    # Candles on the tables; a table and stools in the east of the room.
    for tx in (910,):
        c.put(c.mask(lambda p: (p.rect(tx - 50, g - 30, tx + 50, g - 26), p.rect(tx - 40, g - 26, tx - 36, g), p.rect(tx + 36, g - 26, tx + 40, g))), WOOD)
        c.put(c.mask(lambda p: p.rect(tx - 2, g - 40, tx + 2, g - 30)), (236, 230, 210))
        c.light(c.mask(lambda p: p.ellipse(tx, g - 42, 30), blur=8), LAMP, 0.35)


#: The crypt's gate on the moor (x 2290..2338, east of the founder's
#: plinth) and the crypt inside: its floor, ceiling, the sarcophagus (x
#: 1100..1300, its lid walked on at y 400).
CRYPT_GATE = (2290, 2338)
CRYPT_W, CRYPT_FLOOR, CRYPT_CEILING = 1600, 512, 32
SARCOPHAGUS = (1100, 1300, 440)
STONE = (78, 72, 76)
STONE_LIGHT = (130, 122, 124)
CANDLE = (255, 214, 140)


def crypt_gate(c, k):
    g = MOOR_FLOOR
    d0, d1 = CRYPT_GATE
    # A low stone porch over steps down, an iron gate ajar.
    porch = c.mask(lambda p: p.poly([(d0 - 20, g), (d0 - 20, g - 104), (d0 - 26, g - 104), ((d0 + d1) / 2, g - 136), (d1 + 26, g - 104), (d1 + 20, g - 104), (d1 + 20, g)]))
    c.put(porch, STONE)
    c.tone(porch * (c.noise("crypt_porch", 4, 4, 2) - 0.5), 0.3)
    c.put(c.mask(box(d0, g - 96, d1, g)), (14, 10, 12))
    c.put(c.mask(lambda p: [p.rect(d0 + 4, y, d1 - 4, y + 3) for y in range(int(g - 30), int(g), 8)]), STONE_LIGHT, 0.5)
    c.put(c.mask(lambda p: [p.rect(x, g - 96, x + 2, g) for x in range(d0 + 2, d0 + 24, 6)] + [p.rect(d0 + 2, g - 96, d0 + 24, g - 92)]), (60, 60, 64))
    c.put(c.mask(lambda p: p.line([(d0 - 26, g - 104), ((d0 + d1) / 2, g - 136), (d1 + 26, g - 104)], 3)), STONE_LIGHT)
    rim(c, porch, 0.4)


def crypt_room(c, k):
    g, top = CRYPT_FLOOR, CRYPT_CEILING
    # Vaulted stone, niches of bones, candles.
    wall = c.mask(box(16, top, CRYPT_W - 16, g))
    c.put(wall, STONE)
    c.put(wall * c.mask(lambda p: [p.rect(16, y, CRYPT_W - 16, y + 1.4) for y in range(top + 20, g, 24)]), scale(STONE, 0.7))
    c.tone(wall * (c.noise("crypt_wall", 10, 4, 2) - 0.5), 0.25)
    c.tone(wall * np.clip((200 - c.y) / 170, 0, 1), -0.35)
    for x in range(140, CRYPT_W - 100, 220):
        c.put(c.mask(lambda p: p.arch(x, 180, x + 90, 300)), (24, 20, 22))
        c.put(c.mask(lambda p: [p.ellipse(x + 20 + i * 14, 292 - (i % 2) * 6, 7, 6) for i in range(5)]), (220, 210, 186))
        c.put(c.mask(lambda p: [p.ellipse(x + 28 + i * 20, 296 - 14, 3, 2) for i in range(3)]), (40, 34, 30))
    # Busts of the founder along the wall, each pointing.
    for x in (320, 760, 1460):
        c.put(c.mask(box(x - 26, g - 70, x + 26, g)), STONE_LIGHT)
        bust = c.mask(lambda p: (p.ellipse(x, g - 104, 16, 20), p.poly([(x - 26, g - 70), (x + 26, g - 70), (x + 16, g - 88), (x - 16, g - 88)])))
        c.put(bust, (70, 60, 44))
        c.put(c.mask(lambda p: p.line([(x + 16, g - 80), (x + 44, g - 96)], 5)), (70, 60, 44))
    # The sarcophagus: its lid is walked on.
    s0, s1, lid = SARCOPHAGUS
    c.put(c.mask(box(s0, lid, s1, g)), (90, 84, 90))
    c.put(c.mask(lambda p: [p.rect(x, lid + 20, x + 28, g - 10) for x in range(s0 + 14, s1 - 20, 44)]), (70, 64, 70))
    c.put(c.mask(lambda p: p.poly([(s0 - 6, lid), (s1 + 6, lid), (s1, lid + 10), (s0, lid + 10)])), (110, 104, 108))
    c.put(c.mask(lambda p: p.line([(s0 + 30, lid + 2), ((s0 + s1) / 2, lid - 10), (s1 - 30, lid + 2)], 3)), (110, 104, 108))
    # Candles, their light.
    for x in (240, 560, 980, 1400):
        c.put(c.mask(lambda p: (p.rect(x - 3, g - 22, x + 3, g), p.ellipse(x, g - 26, 2, 4))), (236, 228, 210))
        c.put(c.mask(lambda p: p.ellipse(x, g - 28, 2, 4)), CANDLE)
        c.light(c.mask(lambda p: p.ellipse(x, g - 30, 60), blur=14), CANDLE, 0.35)


PIECES: Dict[str, Piece] = {
    "moor_crypt_gate": Piece((2250, 500, 2384, MOOR_FLOOR), crypt_gate),
    "crypt_room": Piece((16, CRYPT_CEILING, CRYPT_W - 16, CRYPT_FLOOR), crypt_room),
    "moor_inn_front": Piece((0, 400, 340, MOOR_FLOOR), inn_front),
    "inn_room": Piece((16, CEILING, W - 16, FLOOR), inn_room),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
