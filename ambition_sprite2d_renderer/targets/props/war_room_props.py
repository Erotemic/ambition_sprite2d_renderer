"""Draw the War Room wall, relay bays, and gallery decks."""

from __future__ import annotations

from ._district_props import Piece, targets
from ._town_kit import box
from .evil_forest_props import PAL

FLOOR = 704
UPLINKS = (344, 1576)
STEPS = ((432, 560, 624), (704, 832, 496), (1088, 1216, 496), (1360, 1488, 624))
SIDE_DECKS = ((512, 720, 560), (1200, 1408, 560))
GALLERY = (848, 1072, 432)
STEEL = (59, 65, 70)
SEAM = (20, 23, 28)
TRIM = (110, 104, 89)
BOLT = (135, 124, 100)


def relay(c, x):
    c.put(c.mask(box(x - 94, 408, x + 94, 650)), SEAM)
    c.put(c.mask(box(x - 87, 414, x + 87, 644)), STEEL)
    c.put(c.mask(box(x - 80, 424, x + 80, 638)), (34, 42, 46))
    c.put(c.mask(box(x - 69, 450, x + 69, 516)), SEAM)
    c.put(c.mask(box(x - 62, 457, x + 62, 509)), (46, 67, 64))
    c.put(c.mask(lambda p: p.line([
        (x - 52, 497), (x - 37, 478), (x - 24, 486), (x - 7, 470),
        (x + 10, 488), (x + 31, 476), (x + 52, 476),
    ], 2)), (83, 119, 107))
    c.put(c.mask(lambda p: [p.rect(x - 61, y, x + 61, y + 3)
                            for y in range(554, 614, 11)]), SEAM)
    c.put(c.mask(lambda p: [p.rect(x + dx, 529, x + dx + 10, 534)
                            for dx in (-50, -24, 2, 28)]), (105, 86, 63))
    c.put(c.mask(lambda p: [p.rect(x + dx, 645, x + dx + 5, 689)
                            for dx in (-47, 42)]), SEAM)
    c.put(c.mask(box(x - 58, 682, x + 58, 702)), (42, 44, 46))
    c.put(c.mask(lambda p: [p.line([(x + dx, 700), (x + dx + 8, 685)], 2)
                            for dx in range(-53, 48, 13)]), (93, 83, 62))


def command_map(c):
    c.put(c.mask(box(614, 218, 1306, 412)), SEAM)
    c.put(c.mask(box(622, 226, 1298, 404)), STEEL)
    c.put(c.mask(box(632, 236, 1288, 396)), (29, 36, 40))
    c.put(c.mask(box(692, 236, 1228, 298)), (36, 33, 34))
    c.put(c.mask(box(632, 300, 1288, 304)), SEAM)
    c.put(c.mask(lambda p: (
        [p.line([(x, 310), (x, 387)], 1) for x in range(652, 1280, 32)],
        [p.line([(644, y), (1276, y)], 1) for y in (324, 344, 364, 384)],
    )), (49, 59, 60))
    c.put(c.mask(lambda p: p.line([
        (702, 367), (778, 367), (825, 336), (913, 336), (960, 356),
        (1007, 336), (1095, 336), (1142, 367), (1218, 367),
    ], 2)), (99, 119, 107))
    c.put(c.mask(lambda p: (
        p.ring(702, 367, 8, 2), p.ring(1218, 367, 8, 2),
        p.ring(960, 356, 11, 2),
    )), (150, 122, 75))
    c.put(c.mask(lambda p: [p.ellipse(x, y, 2) for x in (627, 1293)
                            for y in (231, 399)]), BOLT)


def command_wall(c, _):
    wall = c.mask(box(16, 32, 1904, FLOOR))
    c.put(wall, (39, 45, 53))
    c.tone(wall * (c.noise("paint", 36, 3, 2) - 0.5), 0.19)
    c.tone(wall * (c.y - 32) / (FLOOR - 32), -0.22)
    c.put(c.mask(lambda p: [p.rect(x, 32, x + 7, FLOOR)
                            for x in (185, 478, 781, 1132, 1422, 1726)]), SEAM)
    c.put(c.mask(lambda p: [p.rect(16, y, 1904, y + 8) for y in (122, 190, 663)]), SEAM)
    c.put(c.mask(lambda p: [p.rect(16, y, 1904, y + 3) for y in (117, 185, 659)]), STEEL)
    for x in (114, 1806):
        c.put(c.mask(lambda p: [p.rect(x - 58, y, x + 58, y + 5)
                                for y in (248, 260, 272, 284)]), SEAM)
    for x in UPLINKS:
        relay(c, x)
    command_map(c)


def deck(c, left, right, top, depth):
    c.put(c.mask(box(left, top, right, top + depth)), STEEL)
    c.put(c.mask(box(left, top + depth - 5, right, top + depth)), SEAM)
    c.put(c.mask(box(left, top, right, top + 3)), TRIM)
    c.put(c.mask(lambda p: [p.ellipse(x, top + 8, 1.5)
                            for x in range(left + 9, right - 5, 19)]), BOLT)


def galleries(c, _):
    for x, top in ((476, 624), (535, 560), (698, 560), (864, 432), (1048, 432),
                   (1224, 560), (1384, 560), (1446, 624)):
        c.put(c.mask(box(x, top + 11, x + 6, FLOOR)), SEAM)
        c.put(c.mask(box(x, top + 11, x + 2, FLOOR)), STEEL)
    for left, right, top in (*STEPS, *SIDE_DECKS, GALLERY):
        c.put(c.mask(lambda p: (
            p.line([(left + 9, top + 10), (left + 37, top + 41)], 4),
            p.line([(right - 9, top + 10), (right - 37, top + 41)], 4),
        )), SEAM)
    for left, right, top in (*STEPS, GALLERY):
        deck(c, left, right, top, 16)
    for left, right, top in SIDE_DECKS:
        deck(c, left, right, top, 32)


TARGETS = targets({
    "war_room_command_wall": Piece((16, 32, 1904, FLOOR), command_wall, px=1),
    "war_room_galleries": Piece((416, 416, 1504, FLOOR), galleries, px=1),
}, PAL)
