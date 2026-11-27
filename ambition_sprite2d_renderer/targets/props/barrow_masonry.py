"""Draw the Barrows' stonework, castings and keys."""
from math import cos, pi, sin

from ._district_props import Piece, targets
from ._town_kit import box
from .fantasy_country_props import line, oval, polygon

STONE = (108, 99, 82)
DARK_STONE = (55, 53, 47)
LIME = (147, 134, 105)
BRONZE = (146, 103, 58)
GOLD = (211, 168, 86)
IRON = (64, 71, 69)
OXIDE = (80, 122, 118)
INLAY = (221, 195, 135)


def rect(c, x0, y0, x1, y1, colour):
    c.put(c.mask(box(x0, y0, x1, y1)), colour)


def ring(c, x, y, radius, thickness, colour):
    c.put(c.mask(lambda pen: pen.ring(x, y, radius, thickness)), colour)


def stone_arch(c, width, height, spring, thickness):
    center = width / 2
    outside = center - 5
    inside = outside - thickness
    rise = spring - 5
    def point(angle, r, ry):
        return center + r * cos(angle), spring - ry * sin(angle)
    for i in range(13):
        a, b = pi * i / 13, pi * (i + 1) / 13
        corners = [point(t, outside, rise) for t in (a, b)] + [point(t, inside, rise - thickness) for t in (b, a)]
        polygon(c, corners, (101 + i % 4 * 7, 92 + i % 4 * 6, 77 + i % 4 * 5))
        line(c, [corners[0], corners[3]], 2, DARK_STONE)
        line(c, [corners[0], corners[1]], 1.5, LIME)
    for x in (5, width - thickness - 5):
        for j, y in enumerate(range(spring, height - 10, 23)):
            shift = (j % 3 - 1) * 1.7
            rect(c, x + shift, y, x + thickness + shift, min(y + 21, height - 8), STONE)
            line(c, [(x + shift + 2, min(y + 18, height - 9)), (x + shift + 2, y + 3),
                     (x + thickness - 2, y + 3)], 1.3, LIME)
        rect(c, x - 3, height - 12, x + thickness + 3, height - 2, DARK_STONE)
    rng = c.rand("lintel wear")
    for _ in range(13):
        a = rng.uniform(0, pi)
        x, y = point(a, outside - 3, rise - 4)
        line(c, [(x, y), (x - rng.uniform(1, 7), y + rng.uniform(1, 8))], 1, DARK_STONE)


def arch(c, _):
    stone_arch(c, 160, 192, 78, 20)
    polygon(c, [(69, 5), (91, 5), (87, 33), (73, 33)], LIME)
    line(c, [(75, 18), (80, 12), (85, 18), (80, 26), (75, 18)], 1.3, BRONZE)


def sarcophagus(c, _):
    polygon(c, [(4, 68), (20, 56), (154, 56), (169, 68), (161, 101), (10, 101)], DARK_STONE)
    polygon(c, [(11, 65), (32, 45), (151, 43), (165, 65), (152, 76), (23, 76)], STONE)
    line(c, [(15, 65), (36, 48), (151, 47)], 3, LIME)
    rect(c, 19, 78, 157, 96, STONE)
    for x in range(26, 155, 15):
        line(c, [(x, 91), (x + 6, 84), (x + 12, 91)], 1.1, (154, 127, 82))
    oval(c, 44, 60, 9, 5, (172, 154, 110))
    polygon(c, [(53, 60), (72, 53), (134, 54), (147, 62), (70, 67)], (157, 141, 105))
    line(c, [(66, 63), (110, 58), (142, 60)], 1.7, DARK_STONE)
    line(c, [(117, 44), (113, 54), (123, 66), (120, 74)], 2, DARK_STONE)


def canopy(c, _):
    stone_arch(c, 320, 280, 147, 31)
    polygon(c, [(38, 257), (45, 165), (68, 126), (110, 104), (211, 104), (252, 126),
                (276, 165), (282, 258)], (51, 47, 42))
    for x in (77, 243):
        rect(c, x - 20, 113, x + 20, 216, (74, 49, 44))
        line(c, [(x - 16, 122), (x - 16, 212)], 2, (116, 80, 57))
        line(c, [(x + 16, 122), (x + 16, 212)], 2, (116, 80, 57))
        polygon(c, [(x - 9, 164), (x, 157), (x + 9, 164), (x, 171)], BRONZE)
        line(c, [(x - 23, 112), (x + 23, 112)], 4, BRONZE)
    ring(c, 160, 90, 21, 2, BRONZE)
    crown(c, 160, 90, 19, GOLD)
    for x in (45, 275):
        rect(c, x - 13, 259, x + 13, 277, STONE)
        line(c, [(x - 13, 259), (x + 13, 259)], 2, LIME)


def crown(c, x, y, width, colour):
    r = width / 2
    polygon(c, [(x - r, y - 5), (x - r * 0.45, y), (x, y - 7), (x + r * 0.45, y),
                (x + r, y - 5), (x + r * 0.8, y + 5), (x - r * 0.8, y + 5)], colour)


def emblem(c, key, x, y, colour):
    if key == "crown":
        crown(c, x, y, 18, colour)
    elif key == "water":
        for dy in (-4, 2):
            line(c, [(x - 8, y + dy), (x - 4, y + dy - 2), (x, y + dy),
                     (x + 4, y + dy + 2), (x + 8, y + dy)], 1.5, colour)
    elif key == "weight":
        polygon(c, [(x - 3, y - 7), (x + 3, y - 7), (x + 7, y + 6), (x - 7, y + 6)], colour)
        oval(c, x, y - 3, 1.4, 1.4, DARK_STONE)
    else:
        ring(c, x - 4, y - 1, 3.4, 1.5, colour)
        line(c, [(x, y - 1), (x + 7, y - 1), (x + 7, y + 3)], 1.8, colour)


def seal(symbol, metal):
    def draw(c, _):
        rect(c, 3, 0, 45, 112, (35, 40, 39))
        for x in (6, 16, 29, 39):
            rect(c, x, 3, x + 3, 108, metal)
            line(c, [(x, 5), (x, 105)], 0.8, LIME)
        for y in (12, 95):
            rect(c, 2, y, 46, y + 8, metal)
            for x in (8, 25, 39):
                oval(c, x, y + 4, 1.8, 1.8, DARK_STONE)
        polygon(c, [(5, 48), (24, 38), (43, 48), (38, 68), (24, 79), (10, 68)], metal)
        oval(c, 24, 58, 13, 13, DARK_STONE)
        emblem(c, symbol, 24, 58, INLAY)
    return draw


def wheel(c, x, y, r, colour):
    ring(c, x, y, r, 5, colour)
    for i in range(6):
        angle = i * pi / 3
        line(c, [(x, y), (x + r * cos(angle), y + r * sin(angle))], 2.4, colour)
    oval(c, x, y, 6, 6, DARK_STONE)
    oval(c, x - 1, y - 1, 3, 3, INLAY)


def counterweights(c, _):
    for x in (12, 150):
        rect(c, x, 27, x + 20, 213, DARK_STONE)
        line(c, [(x + 2, 29), (x + 2, 210)], 2, STONE)
    rect(c, 5, 25, 174, 43, STONE)
    for x, lower in ((44, 105), (130, 158)):
        ring(c, x, 50, 11, 4, BRONZE)
        line(c, [(x, 52), (x, lower)], 2, LIME)
        polygon(c, [(x - 9, lower), (x + 9, lower), (x + 16, lower + 32), (x - 16, lower + 32)], STONE)
        emblem(c, "weight", x, lower + 16, INLAY)
    wheel(c, 78, 158, 28, BRONZE)
    rect(c, 22, 209, 157, 215, STONE)


def sluice(c, _):
    line(c, [(160, 17), (160, 79), (135, 102), (81, 102), (47, 135), (47, 199)], 24, IRON)
    line(c, [(153, 20), (153, 77), (132, 95), (78, 95), (40, 133), (40, 198)], 3, OXIDE)
    rect(c, 143, 28, 177, 41, OXIDE)
    rect(c, 28, 169, 64, 182, OXIDE)
    rect(c, 82, 86, 95, 118, OXIDE)
    wheel(c, 64, 148, 26, OXIDE)
    emblem(c, "water", 122, 66, INLAY)
    line(c, [(112, 147), (129, 152), (150, 149)], 1.2, (101, 139, 130))


def salvage(c, _):
    polygon(c, [(4, 153), (27, 134), (77, 130), (120, 119), (178, 141), (181, 155)], DARK_STONE)
    polygon(c, [(16, 146), (17, 85), (78, 77), (93, 140)], (77, 88, 82))
    polygon(c, [(31, 97), (67, 91), (79, 128), (34, 133)], (37, 50, 48))
    line(c, [(32, 99), (62, 95)], 2, OXIDE)
    rect(c, 85, 51, 147, 147, (141, 127, 95))
    rect(c, 89, 57, 142, 97, (44, 56, 49))
    for x in range(96, 138, 7):
        line(c, [(x, 63), (x, 90)], 1, (85, 109, 94))
    for y in (102, 109, 116):
        line(c, [(100, y), (131, y)], 2, (83, 76, 63))
    ring(c, 155, 119, 20, 5, (101, 77, 59))
    line(c, [(80, 78), (70, 124), (101, 148), (133, 149), (147, 140)], 2, (53, 47, 43))
    line(c, [(106, 50), (100, 19), (119, 11), (128, 16)], 2, BRONZE)
    oval(c, 96, 63, 1.6, 1.6, (202, 156, 78))


def ward_key(c, _):
    ring(c, 11, 11, 6, 3.5, BRONZE)
    ring(c, 11, 11, 7.3, 1.2, GOLD)
    line(c, [(15, 16), (27, 27), (32, 22)], 4.5, GOLD)
    line(c, [(22, 22), (27, 17)], 2.7, BRONZE)
    line(c, [(16, 16), (28, 26)], 1.4, INLAY)


PIECES = {
    "barrow_arch": Piece((0, 0, 160, 192), arch, px=1.5),
    "barrow_sarcophagus": Piece((0, 0, 174, 106), sarcophagus, px=1.5),
    "barrow_royal_canopy": Piece((0, 0, 320, 280), canopy, px=1.5),
    "barrow_counterweights": Piece((0, 0, 186, 216), counterweights, px=1.5),
    "barrow_sluice_pipe": Piece((0, 0, 190, 204), sluice, px=1.5),
    "barrow_salvage_stack": Piece((0, 0, 184, 156), salvage, px=1.5),
    "barrow_ward_key": Piece((0, 0, 36, 36), ward_key, px=2),
    "barrow_bronze_seal": Piece((0, 0, 48, 112), seal("ward", BRONZE), px=1.5),
    "barrow_crown_seal": Piece((0, 0, 48, 112), seal("crown", (153, 123, 61)), px=1.5),
    "barrow_latch_weight": Piece((0, 0, 48, 112), seal("weight", (126, 106, 73)), px=1.5),
    "barrow_latch_water": Piece((0, 0, 48, 112), seal("water", OXIDE), px=1.5),
}

TARGETS = targets(PIECES, {})
