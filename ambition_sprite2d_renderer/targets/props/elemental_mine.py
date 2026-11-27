"""Draw the mine equipment and exposed mineral deposits."""
from math import cos, pi, sin

from ._district_props import Piece, targets
from .barrow_masonry import rect, ring, wheel
from .fantasy_country_props import line, oval, polygon

INK = (31, 39, 42)
STEEL = (69, 91, 94)
LIGHT = (128, 153, 150)
RUST = (128, 76, 46)
OCHRE = (191, 133, 59)
LAMP = (248, 212, 131)
ROCK = (49, 61, 66)


def beam(c, a, b, w=10, colour=STEEL):
    line(c, [a, b], w + 3, INK)
    line(c, [a, b], w, colour)
    line(c, [(a[0] - 2, a[1] - 1), (b[0] - 2, b[1] - 1)], 1.5, LIGHT)


def rivets(c, points):
    for x, y in points:
        oval(c, x, y, 2.4, 2.4, INK)
        oval(c, x - 0.7, y - 0.8, 0.9, 0.9, LIGHT)


def headframe(c, _):
    for a, b in (((34, 286), (99, 51)), ((286, 286), (221, 51)),
                 ((90, 52), (231, 52)), ((66, 176), (253, 176)),
                 ((43, 257), (252, 178)), ((66, 178), (276, 260)),
                 ((69, 166), (226, 64)), ((94, 65), (251, 165))):
        beam(c, a, b, 12, RUST)
    for x in (115, 201):
        wheel(c, x, 39, 30, STEEL)
        line(c, [(x + 29, 40), (x + 29, 290)], 2.3, INK)
        ring(c, x, 39, 31, 2.1, LIGHT)
    for x in (29, 263):
        polygon(c, [(x - 13, 286), (x - 8, 271), (x + 21, 271), (x + 32, 286)], ROCK)


def hopper(c, _):
    for x in (34, 170):
        beam(c, (x, 83), (x, 155), 10)
    polygon(c, [(16, 22), (203, 22), (185, 78), (148, 111),
                (63, 111), (33, 75)], INK)
    polygon(c, [(24, 29), (195, 29), (175, 74), (144, 102),
                (66, 102), (41, 73)], STEEL)
    for x in (47, 88, 129, 170):
        beam(c, (x, 33), (105 + (x - 106) * 0.42, 100), 5)
    rect(c, 12, 18, 207, 30, OCHRE)
    beam(c, (42, 148), (166, 96), 7)
    beam(c, (42, 96), (166, 148), 7)


def rail(c, _):
    for x in range(4, 316, 23):
        polygon(c, [(x, 29), (x + 7, 3), (x + 15, 3), (x + 11, 29)], RUST)
    for y in (10, 22):
        line(c, [(0, y), (320, y)], 5, INK)
        line(c, [(0, y - 2), (320, y - 2)], 1.7, LIGHT)


def rack(c, _):
    for x in (17, 153):
        beam(c, (x, 4), (x, 119), 6)
    rng = c.rand("assay samples")
    for y in (37, 74, 112):
        rect(c, 8, y - 3, 162, y + 3, RUST)
        for x in range(27, 148, 24):
            w, h = rng.randint(12, 21), rng.randint(11, 22)
            polygon(c, [(x, y - 4), (x + 2, y - h), (x + w - 4, y - h - 2),
                        (x + w, y - 4)], (60 + x % 36, 78 + x % 39, 88))
            rect(c, x + 3, y - 11, x + w - 2, y - 7, (166, 146, 112))


def brace(c, _):
    for a, b in (((16, 216), (16, 25)), ((144, 216), (144, 25)), ((7, 22), (153, 22)),
                 ((16, 97), (76, 24)), ((143, 97), (83, 24))):
        beam(c, a, b, 12)
    for x in (16, 144):
        rivets(c, [(x, 26), (x, 88), (x, 207)])
    line(c, [(80, 25), (80, 45)], 2, INK)
    rect(c, 71, 46, 89, 51, INK)
    rect(c, 74, 52, 86, 60, LAMP)


def fan(c, _):
    beam(c, (91, 80), (91, 154), 28)
    for x in (28, 153):
        beam(c, (x, 152), (91, 111), 9)
    oval(c, 90, 68, 62, 62, STEEL)
    oval(c, 90, 68, 50, 50, INK)
    for i in range(5):
        angle = i * 2 * pi / 5
        points = [(90 + cos(angle + a) * r, 68 + sin(angle + a) * r)
                  for a, r in ((0, 5), (0.29, 48), (0.75, 44), (0.92, 21))]
        polygon(c, points, LIGHT)
    oval(c, 90, 68, 10, 10, RUST)
    for radius in (43, 56):
        ring(c, 90, 68, radius, 2.5, LIGHT)
    rivets(c, [(90, 13), (38, 67), (141, 67), (90, 124)])


def crystals(c, _):
    tiles = ((62, 84, 103), (83, 112, 115), (104, 125, 112),
             (137, 109, 112), (111, 92, 128), (116, 130, 151))
    for k, (x, y, levels) in enumerate(((53, 129, 5), (105, 101, 7), (171, 145, 4), (207, 152, 3))):
        for j in range(levels):
            w = (levels - j) * 6 + 5
            top = [(x - w, y), (x - w * 0.2, y - w * 0.38), (x + w, y - w * 0.30),
                   (x + w * 0.25, y + w * 0.35)]
            polygon(c, [top[0], top[3], (top[3][0], top[3][1] + 7), (x - w, y + 7)], ROCK)
            polygon(c, [top[3], top[2], (top[2][0], top[2][1] + 7), (top[3][0], top[3][1] + 7)], INK)
            polygon(c, top, tiles[(k + j) % len(tiles)])
            line(c, [top[0], top[1], top[2]], 1.5, LIGHT)
            x, y = x + 3, y - 6


def silver(c, _):
    rng = c.rand("nickel silver seam")
    for _ in range(51):
        x = rng.uniform(12, 227)
        y = 119 - 0.29 * x + sin(x * 0.049) * 12 + rng.uniform(-10, 10)
        w = rng.uniform(1, 10)
        polygon(c, [(x - w, y + 2), (x, y - 4), (x + w, y - 1), (x + w * 0.4, y + 3)],
                [(61, 82, 90), (95, 115, 116), (134, 150, 146)][rng.randrange(3)])


def listening_seam(c, _):
    polygon(c, [(7, 187), (23, 149), (61, 101), (74, 115), (129, 31),
                (158, 10), (183, 117), (203, 132), (231, 187)], ROCK)
    for x, y, h in ((56, 169, 68), (111, 140, 86), (157, 89, 67), (190, 164, 49)):
        polygon(c, [(x - 10, y + 17), (x - 11, y + 7 - h), (x + 2, y - h - 10),
                    (x + 13, y - h + 4), (x + 13, y + 10)], (53, 88, 105))
        line(c, [(x - 2, y + 9), (x + 1, y - h + 1)], 2, (113, 170, 169))


def screen(c, _):
    for x in (4, 16, 28, 40):
        rect(c, x, 0, x + 5, 112, STEEL)
        line(c, [(x + 1, 2), (x + 1, 110)], 1, LIGHT)
    for y in (9, 52, 95):
        rect(c, 2, y, 46, y + 9, INK)
        for x in (4, 18, 32):
            polygon(c, [(x, y + 7), (x + 7, y + 1), (x + 12, y + 1), (x + 5, y + 7)], OCHRE)


def cage(c, _):
    for x in (18, 238):
        beam(c, (x, 140), (x, 27), 6)
    for a, b in (((17, 27), (237, 27)), ((17, 27), (128, 8)), ((238, 27), (128, 8))):
        beam(c, a, b, 5)
    rect(c, 16, 140, 240, 155, INK)
    rect(c, 16, 140, 240, 143, LIGHT)
    for x in range(25, 235, 20):
        polygon(c, [(x, 153), (x + 10, 144), (x + 17, 144), (x + 7, 153)], OCHRE)


def cart(c, _):
    for x in (52, 172):
        wheel(c, x, 72, 13, STEEL)
    polygon(c, [(16, 30), (208, 30), (191, 69), (33, 69)], INK)
    polygon(c, [(19, 37), (205, 37), (187, 65), (36, 65)], RUST)
    for x in (48, 109, 166):
        beam(c, (x, 40), (x + 7, 63), 3)
    rect(c, 15, 28, 209, 35, LIGHT)
    rivets(c, [(26, 41), (111, 42), (197, 42)])


def falling_crystal(c, _):
    points = [(13, 9), (29, 4), (42, 18), (33, 40), (23, 59), (12, 44), (8, 23)]
    polygon(c, points, (63, 117, 131))
    polygon(c, [points[0], points[1], points[2], (22, 21)], (164, 217, 193))
    polygon(c, [points[2], points[3], points[4], (22, 21)], (80, 154, 145))
    line(c, [(22, 21), (23, 59)], 2, (186, 230, 205))


def lamp(c, _):
    line(c, [(24, 0), (24, 40)], 2.2, INK)
    polygon(c, [(7, 52), (14, 38), (34, 38), (41, 52)], RUST)
    rect(c, 11, 52, 37, 69, INK)
    rect(c, 14, 54, 34, 64, LAMP)
    for x in (19, 29):
        line(c, [(x, 51), (x, 66)], 1.3, OCHRE)
    rect(c, 7, 67, 41, 71, STEEL)


def air_line(c, _):
    line(c, [(10, 68), (10, 34), (25, 16), (295, 16), (312, 34), (312, 68)], 17, INK)
    line(c, [(10, 69), (10, 34), (25, 16), (295, 16), (312, 34), (312, 69)], 11, STEEL)
    line(c, [(8, 66), (8, 35), (23, 13), (298, 13), (309, 33)], 2.3, LIGHT)
    for x in (45, 104, 166, 224, 280):
        rect(c, x, 6, x + 7, 26, RUST)
    for x in (73, 195):
        line(c, [(x, 40), (x, 17)], 4, INK)
        oval(c, x, 53, 10, 10, STEEL)
        oval(c, x, 53, 7, 7, INK)
        line(c, [(x, 54), (x + 3, 49)], 1.0, LAMP)


PIECES = {
    "mine_lamp": Piece((0, 0, 48, 76), lamp, px=1.5),
    "mine_air_line": Piece((0, 0, 320, 76), air_line, px=1.5),

    "mine_falling_crystal": Piece((0, 0, 48, 64), falling_crystal, px=1.5),

    "mine_headframe": Piece((0, 0, 320, 292), headframe, px=1.5),
    "mine_hopper": Piece((0, 0, 220, 160), hopper, px=1.5),
    "mine_rail": Piece((0, 0, 320, 32), rail, px=1.5),
    "mine_rack": Piece((0, 0, 170, 120), rack, px=1.5),
    "mine_brace": Piece((0, 0, 160, 220), brace, px=1.5),
    "mine_fan": Piece((0, 0, 180, 158), fan, px=1.5),
    "mine_bismuth": Piece((0, 0, 240, 160), crystals, px=1.5),
    "mine_silver_vein": Piece((0, 0, 240, 144), silver, px=1.5),
    "mine_lode_echo": Piece((0, 0, 240, 190), listening_seam, px=1.5),
    "mine_lock_screen": Piece((0, 0, 48, 112), screen, px=1.5),
    "mine_cage": Piece((0, 0, 256, 160), cage, px=1),
    "mine_ore_cart": Piece((0, 0, 224, 88), cart, px=1),
}

TARGETS = targets(PIECES, {})
