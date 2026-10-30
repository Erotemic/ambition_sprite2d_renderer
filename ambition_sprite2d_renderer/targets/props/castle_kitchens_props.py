"""The kitchens under Castle Godwin's gatehouse (`castle_godwin_kitchens`, the
Evil dimension): where the people who keep a tyrant's castle running eat,
gossip and organise.

Drawn in room coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/castle_kitchens/make_specs.py`: the floor
(y 512), the ceiling (to y 48), the stair up to the gatehouse through the
ceiling at the west end (x 40..104; its ladder is the engine's), the way
east to the Complaints Department at the floor, the cook at the hearth, the
porter at his desk, the steward at the long table.

- `castle_kitchens_room`: a vaulted stone kitchen. The great hearth with a
  cauldron over the fire; a rack of pans and ladles; shelves of jars and
  sacks of turnips; hams and onions from the vault; the night porter's nook (the visitors' book open, a
  lantern, the key board); the long table and its benches under the
  henchpersons' guild notice board; the castle's poster with a moustache
  drawn on it; the dumbwaiter up to the great hall; the Complaints
  Department's plaque by the way east; a mouse hole, its trap sprung and
  empty.

Animations: ``idle``, 1 frame. No drop shadows.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from . import castle_godwin as CG
from .eureka_props import Batch, ashlar, edge_line

W, FLOOR, CEILING = 1280, 512, 48
DOOR_X = 40
HEARTH = (520, 800)
TABLE = (860, 1160)
PAL = {"stone": CG.STONE, "stone_light": CG.STONE_LIGHT, "dark": (22, 18, 26), "lamp": (255, 200, 120)}
STONE, STONE_DARK, STONE_LIGHT = CG.STONE, CG.STONE_DARK, CG.STONE_LIGHT
RED = CG.RED
WOOD = (96, 64, 44)
WOOD_DARK = (60, 40, 30)
WOOD_LIGHT = (140, 100, 70)
IRON = (52, 52, 60)
COPPER = (190, 104, 60)
PAPER = (222, 210, 176)
FIRE = (255, 150, 50)
FIRE_CORE = (255, 230, 150)
LAMP = (255, 200, 120)


def room(c, k):
    g = FLOOR
    # The vault: stone, darker overhead, ribs between bays.
    ashlar(c, 16, CEILING, W - 16, g, STONE, course=20, block=40, tag="kitchen", vary=0.06)
    c.tone(c.mask(box(16, CEILING, W - 16, g)) * np.clip((200 - c.y) / 150, 0, 1), -0.35)
    for x in range(16, W, 320):
        c.put(c.mask(lambda p: p.poly([(x - 14, g), (x - 14, 140), (x, CEILING), (x + 14, 140), (x + 14, g)])), STONE_DARK)
    c.put(c.mask(box(16, g - 26, W - 16, g)), STONE_DARK)
    # The hearth: a chimney hood, the fire, the cauldron on its chain.
    h0, h1 = HEARTH
    c.put(c.mask(lambda p: p.poly([(h0 - 20, 392), (h1 + 20, 392), (h1 - 30, 290), (h0 + 30, 290)])), STONE_DARK)
    c.put(c.mask(lambda p: p.rect(h0 + 60, CEILING, h1 - 60, 290)), STONE_DARK)
    c.put(c.mask(box(h0 - 24, 388, h1 + 24, 400)), WOOD_DARK)
    opening = c.mask(lambda p: (p.rect(h0, 400, h1, g), p.ellipse((h0 + h1) / 2, 404, (h1 - h0) / 2, 14)))
    c.put(opening, (26, 16, 14))
    rng = c.rand("flames")
    cx = (h0 + h1) / 2
    flames = c.mask(lambda p: [p.poly([(cx + dx - 14, g - 8), (cx + dx + rng.uniform(-5, 5), g - rng.uniform(30, 46)), (cx + dx + 14, g - 8)]) for dx in (-60, -30, 0, 30, 60)])
    c.put(flames, FIRE)
    c.put(c.mask(lambda p: [p.poly([(cx + dx - 7, g - 8), (cx + dx, g - rng.uniform(16, 24)), (cx + dx + 7, g - 8)]) for dx in (-50, -15, 20, 50)]), FIRE_CORE)
    c.put(c.mask(lambda p: [p.rect(cx + dx - 18, g - 9, cx + dx + 18, g - 3) for dx in (-40, 0, 40)]), WOOD_DARK)
    c.light(c.mask(lambda p: p.ellipse(cx, g - 30, 200, 100), blur=26), FIRE, 0.35)
    c.put(c.mask(box(cx - 1, 404, cx + 1, 436)), IRON)
    pot = c.mask(lambda p: (p.ellipse(cx, 456, 30, 22), p.rect(cx - 33, 434, cx + 33, 440)))
    c.put(pot, (34, 32, 36))
    c.tone(pot * np.clip((c.x - cx) / 30, -1, 1), -0.25)
    c.put(c.mask(lambda p: p.ellipse(cx, 437, 30, 3)), (120, 110, 70))
    for i in range(3):
        pts = [(cx - 14 + i * 14 + 3 * math.sin(t * 2 + i), 430 - t * 12) for t in np.linspace(0, 3, 16)]
        c.put(c.mask(lambda p: p.line(pts, 4), blur=4), (220, 216, 206), 0.3)
    # The rack of pans and ladles.
    c.put(c.mask(box(300, 300, 470, 304)), IRON)
    for i, x in enumerate(range(312, 470, 22)):
        c.put(c.mask(box(x - 0.6, 304, x + 0.6, 312)), IRON)
        if i % 2 == 0:
            c.put(c.mask(lambda p: (p.ellipse(x, 324, 8, 8), p.rect(x - 1.2, 312, x + 1.2, 318))), COPPER)
            c.tone(c.mask(lambda p: p.ellipse(x, 324, 8, 8)) * np.clip((c.x - x) / 8, -1, 1), -0.25)
        else:
            c.put(c.mask(lambda p: (p.rect(x - 1, 312, x + 1, 334), p.ellipse(x, 336, 4, 3))), (150, 150, 160))
    # Shelves of jars, sacks of turnips under them.
    b = Batch(c)
    for y in (380, 420):
        b.add(WOOD, 1.0, box(300, y, 470, y + 4))
        for j, x in enumerate(range(308, 464, 13)):
            col = ((150, 70, 60), (90, 120, 70), (200, 170, 90), (110, 90, 130))[(j + y) % 4]
            b.add(col, 0.9, box(x, y - 14 + (j % 3) * 2, x + 8, y))
            b.add((200, 196, 186), 1.0, box(x - 0.5, y - 15 + (j % 3) * 2, x + 8.5, y - 13 + (j % 3) * 2))
    b.draw()
    for x in (330, 380):
        sack = c.mask(lambda p: p.poly([(x - 16, g), (x + 16, g), (x + 14, g - 26), (x + 4, g - 34), (x - 4, g - 34), (x - 14, g - 26)]))
        c.put(sack, (170, 150, 110))
        c.tone(sack * np.clip((c.x - x) / 16, -1, 1), -0.2)
    c.put(c.mask(lambda p: [p.ellipse(x, g - 35, 4) for x in (325, 334, 382)]), (170, 110, 150))
    c.put(c.mask(lambda p: [p.line([(x, g - 38), (x + 2, g - 45)], 1.4) for x in (325, 334, 382)]), (90, 140, 70))
    # The night porter's nook: a desk with the visitors' book, a lantern, the key board.
    d = g - 34
    c.put(c.mask(lambda p: (p.rect(150, d, 250, d + 5), p.rect(156, d + 5, 162, g), p.rect(238, d + 5, 244, g))), WOOD)
    c.put(c.mask(lambda p: (p.poly([(170, d), (194, d - 1), (194, d - 5), (170, d - 4)]), p.poly([(196, d - 1), (220, d), (220, d - 4), (196, d - 5)]))), PAPER)
    c.put(c.mask(lambda p: (p.rect(234, d - 14, 242, d), p.rect(236, d - 18, 240, d - 14))), IRON)
    c.put(c.mask(box(235, d - 12, 241, d - 2)), LAMP)
    c.light(c.mask(lambda p: p.ellipse(238, d - 7, 34), blur=10), LAMP, 0.4)
    c.put(c.mask(box(160, 380, 230, 430)), WOOD_DARK)
    c.put(c.mask(lambda p: [p.ellipse(x, y, 1.6) for x in range(170, 226, 11) for y in (392, 410, 424)]), (200, 196, 186))
    c.put(c.mask(lambda p: [p.line([(x, y + 1), (x + 1, y + 8)], 1.2) for x in range(170, 226, 22) for y in (392, 410)]), (196, 150, 70))
    # The long table and its benches; the guild's notice board over it.
    t0, t1 = TABLE
    c.put(c.mask(lambda p: (p.rect(t0, g - 32, t1, g - 26), p.rect(t0 + 14, g - 26, t0 + 20, g), p.rect(t1 - 20, g - 26, t1 - 14, g))), WOOD)
    edge_line(c, t0, t1, g - 32, WOOD_LIGHT, 2)
    c.put(c.mask(lambda p: [p.rect(x0, g - 18, x1, g - 14) for x0, x1 in ((t0 - 10, t0 + 120), (t0 + 170, t1 + 10))]), WOOD_DARK)
    for x in (t0 + 40, t0 + 90, t1 - 60):
        c.put(c.mask(lambda p: (p.rect(x - 4, g - 42, x + 4, g - 32), p.line([(x + 4, g - 40), (x + 7, g - 37), (x + 4, g - 34)], 1.4))), (200, 196, 186))
    nb0, nb1 = t0 + 30, t1 - 30
    c.put(c.mask(box(nb0, 380, nb1, 456)), (120, 90, 60))
    c.put(c.mask(box(nb0 + 3, 383, nb1 - 3, 453)), (160, 130, 90))
    rng = c.rand("notices")
    for i in range(10):
        x, y = nb0 + 10 + (i % 5) * 34 + rng.uniform(-3, 3), 388 + (i // 5) * 32 + rng.uniform(-2, 2)
        c.put(c.mask(box(x, y, x + 24, y + 28)), PAPER)
        c.put(c.mask(lambda p: [p.rect(x + 3, yy, x + 21 - rng.uniform(0, 8), yy + 0.8) for yy in np.arange(y + 5, y + 26, 4)]), (100, 96, 90))
        c.put(c.mask(lambda p: p.ellipse(x + 12, y + 1.5, 1.8)), RED)
    # The guild's badge: a fist round a mug, on red.
    bx, by = nb1 - 24, 418
    c.put(c.mask(lambda p: p.ellipse(bx, by, 14)), RED)
    c.put(c.mask(lambda p: (p.rect(bx - 5, by - 6, bx + 3, by + 6), p.ring(bx + 6, by, 3.5, 1.5))), (236, 228, 210))
    # Hams and strings of onions hung from the vault over the table.
    for x, drop in ((900, 300), (1000, 280), (1100, 310)):
        c.put(c.mask(box(x - 0.8, CEILING, x + 0.8, drop - 30)), (180, 160, 120))
        ham = c.mask(lambda p: p.poly([(x - 4, drop - 32), (x + 4, drop - 32), (x + 14, drop - 4), (x, drop + 4), (x - 14, drop - 4)]))
        c.put(ham, (150, 80, 60))
        c.tone(ham * np.clip((c.x - x) / 14, -1, 1), -0.25)
    for x in (950, 1050):
        c.put(c.mask(box(x - 0.6, CEILING, x + 0.6, 300)), (180, 160, 120))
        c.put(c.mask(lambda p: [p.ellipse(x + (5 if i % 2 else -5), y, 6, 7) for i, y in enumerate(range(250, 300, 9))]), (214, 180, 120))
    # The castle's poster, a moustache drawn on its stern face.
    px0, py0 = 640, 140
    c.put(c.mask(box(px0 - 26, py0, px0 + 26, py0 + 70)), RED)
    CG.emblem(c, px0, py0 + 26, 16)
    c.put(c.mask(lambda p: p.line([(px0 - 12, py0 + 52), (px0 - 4, py0 + 48), (px0, py0 + 51), (px0 + 4, py0 + 48), (px0 + 12, py0 + 52)], 2.4)), (20, 18, 20))
    # The dumbwaiter up to the great hall, its rope.
    c.put(c.mask(box(1186, 140, 1250, g - 120)), (30, 26, 28))
    c.put(c.mask(lambda p: (p.rect(1182, 136, 1254, 144), p.rect(1182, g - 124, 1254, g - 116))), WOOD_DARK)
    c.put(c.mask(lambda p: (p.rect(1198, 144, 1200, g - 124), p.rect(1236, 144, 1238, g - 124))), (190, 170, 120))
    c.put(c.mask(box(1194, g - 180, 1242, g - 128)), WOOD)
    # The Complaints Department's plaque, by the way east to it, its hand
    # pointing on.
    c.put(c.mask(box(1124, FLOOR - 110, 1184, FLOOR - 70)), WOOD_DARK)
    c.put(c.mask(box(1130, FLOOR - 104, 1178, FLOOR - 76)), PAPER)
    c.put(c.mask(lambda p: [p.rect(1136, y, 1172, y + 1) for y in (FLOOR - 98, FLOOR - 94)]), (90, 80, 70))
    c.put(c.mask(lambda p: p.poly([(1140, FLOOR - 86), (1162, FLOOR - 86), (1162, FLOOR - 90), (1172, FLOOR - 83), (1162, FLOOR - 76), (1162, FLOOR - 80), (1140, FLOOR - 80)])), RED)
    # A mouse hole, and its trap, sprung and empty.
    c.put(c.mask(lambda p: p.ellipse(1100, g, 10, 12)) * (c.y < g), (14, 10, 12))
    c.put(c.mask(lambda p: (p.rect(1060, g - 4, 1084, g), p.line([(1062, g - 4), (1078, g - 10)], 1.4))), WOOD_LIGHT)


#: The Complaints Department (`castle_godwin_complaints`): its floor,
#: ceiling, the counter (x 420..900) and its two windows.
COMPLAINTS_W, COMPLAINTS_FLOOR = 960, 384


def complaints(c, k):
    g = COMPLAINTS_FLOOR
    wall = c.mask(box(16, CEILING, COMPLAINTS_W - 16, g))
    c.put(wall, (120, 118, 100))
    c.put(wall * c.mask(lambda p: [p.rect(16, y, COMPLAINTS_W - 16, y + 1) for y in range(CEILING + 30, g, 30)]), (100, 98, 84), 0.6)
    c.put(c.mask(box(16, g - 60, COMPLAINTS_W - 16, g)), (80, 70, 60))
    # The counter: two windows, both shuttered, CLOSED on each.
    c.put(c.mask(box(420, g - 70, 900, g)), WOOD_DARK)
    edge_line(c, 414, 906, g - 72, WOOD_LIGHT, 4)
    for wx in (470, 690):
        c.put(c.mask(box(wx, 120, wx + 160, g - 76)), (40, 36, 40))
        c.put(c.mask(lambda p: [p.rect(wx + 4, y, wx + 156, y + 4) for y in range(124, int(g - 80), 8)]), (140, 136, 130))
        c.put(c.mask(box(wx + 40, 196, wx + 120, 222)), RED)
        c.put(c.mask(lambda p: [p.rect(wx + 48 + i * 14, 205, wx + 56 + i * 14, 213) for i in range(5)]), (236, 228, 210))
    # The ticket machine and NOW SERVING: 3.
    c.put(c.mask(lambda p: (p.rect(314, g - 44, 318, g), p.rect(304, g - 4, 328, g), p.rect(306, g - 62, 326, g - 44), p.ellipse(316, g - 62, 10, 4))), RED)
    c.put(c.mask(box(312, g - 52, 320, g - 48)), (236, 228, 210))
    c.put(c.mask(lambda p: p.poly([(318, g - 50), (326, g - 46), (324, g - 40), (316, g - 44)])), (236, 228, 210))
    c.put(c.mask(box(560, 60, 740, 104)), (20, 20, 24))
    c.put(c.mask(lambda p: (p.line([(700, 70), (712, 66), (716, 76), (708, 82), (716, 88), (712, 98), (700, 94)], 3))), (255, 120, 60))
    # Chairs in a queue, a drift of forms, the suggestions box padlocked.
    for x in range(80, 280, 46):
        c.put(c.mask(lambda p: (p.rect(x, g - 30, x + 30, g - 26), p.rect(x + 26, g - 56, x + 30, g - 26), p.rect(x + 2, g - 26, x + 5, g), p.rect(x + 25, g - 26, x + 28, g))), (90, 96, 110))
    rng = c.rand("forms")
    for i in range(40):
        x, y = rng.uniform(910, 940), g - 6 - i * 5
        c.put(c.mask(lambda p: p.rect(x - 14, y, x + 14, y + 4)), (226, 214, 180))
    # The suggestions box on its post, padlocked.
    c.put(c.mask(lambda p: (p.rect(377, g - 34, 383, g), p.rect(368, g - 4, 392, g))), WOOD_DARK)
    c.put(c.mask(box(360, g - 64, 400, g - 34)), WOOD)
    c.put(c.mask(box(372, g - 66, 388, g - 62)), (20, 20, 20))
    c.put(c.mask(lambda p: (p.line([(360, g - 49), (400, g - 49)], 2), p.ring(380, g - 38, 5, 2))), (160, 160, 170))


PIECES: Dict[str, Piece] = {
    "complaints_room": Piece((16, CEILING, COMPLAINTS_W - 16, COMPLAINTS_FLOOR), complaints),
    "castle_kitchens_room": Piece((16, CEILING, W - 16, FLOOR), room),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
