"""Draw scenery for the burial chambers and the high road."""

from __future__ import annotations

from ._district_props import Piece, targets
from ._town_kit import box


def polygon(canvas, points, color):
    canvas.put(canvas.mask(lambda pen: pen.poly(points)), color)


def line(canvas, points, width, color):
    canvas.put(canvas.mask(lambda pen: pen.line(points, width)), color)


def oval(canvas, x, y, rx, ry, color):
    canvas.put(canvas.mask(lambda pen: pen.ellipse(x, y, rx, ry)), color)


def grave_niche(canvas, _):
    arch = [(3, 111), (8, 43), (26, 20), (48, 6), (83, 4), (111, 21),
            (123, 42), (126, 111)]
    polygon(canvas, arch, (92, 90, 86))
    polygon(canvas, [(20, 102), (24, 46), (44, 24), (76, 20), (100, 36),
                     (108, 57), (110, 102)], (42, 45, 49))
    for seam in [[(8, 55), (24, 60)], [(13, 83), (23, 80)], [(23, 22), (40, 33)],
                 [(50, 6), (54, 22)], [(81, 6), (77, 20)], [(113, 25), (97, 37)],
                 [(121, 63), (106, 64)], [(123, 93), (108, 87)]]:
        line(canvas, seam, 2, (60, 64, 63))
    polygon(canvas, [(34, 108), (39, 84), (74, 78), (96, 89), (93, 109)], (113, 106, 92))
    line(canvas, [(39, 84), (74, 78), (95, 89)], 2, (153, 141, 114))
    line(canvas, [(61, 14), (65, 9), (70, 15)], 2, (182, 159, 113))
    for x, y in [(12, 102), (109, 89), (120, 106), (21, 95)]:
        oval(canvas, x, y, 5, 3, (85, 100, 75))


def strata(canvas, _):
    outline = [(0, 118), (4, 68), (21, 46), (25, 32), (58, 18),
               (94, 8), (127, 23), (137, 50), (134, 72), (143, 119)]
    silhouette = canvas.mask(lambda pen: pen.poly(outline))
    canvas.put(silhouette, (87, 100, 110))
    for y, col in [(34, (130, 146, 151)), (49, (101, 115, 121)),
                   (64, (141, 142, 131)), (78, (72, 90, 101)),
                   (96, (113, 122, 119)), (111, (67, 78, 83))]:
        points = [(0, y + 22), (32, y + 8), (60, y + 1), (110, y - 12), (144, y - 5)]
        canvas.put(canvas.mask(lambda pen: pen.line(points, 7)) * silhouette, col)
    for points in [[(32, 56), (45, 62), (42, 82)], [(92, 29), (94, 53), (78, 68)],
                   [(114, 85), (101, 94), (98, 111)]]:
        line(canvas, points, 1.6, (61, 74, 83))
    rng = canvas.rand("talus")
    for _ in range(21):
        x, y = rng.uniform(6, 138), rng.uniform(103, 118)
        oval(canvas, x, y, rng.uniform(2, 6), rng.uniform(1, 4), (112, 123, 127))


def pines(canvas, _):
    for x, top, span, dark in [(96, 4, 33, (56, 89, 88)), (48, 24, 29, (61, 95, 89)),
                               (119, 60, 24, (68, 101, 93)), (22, 83, 18, (71, 111, 99))]:
        line(canvas, [(x, top + 16), (x - 2, 156)], 4, (82, 86, 73))
        height = 150 - top
        for scale, depth in [(0.49, 0.22), (0.66, 0.41), (0.85, 0.60), (1, 0.79)]:
            y = top + height * depth
            w = span * scale
            polygon(canvas, [(x, y - height * 0.23), (x - w, y), (x - w * 0.38, y + 3),
                             (x, y - 1), (x + w, y + 6), (x + w * 0.43, y - 8)], dark)
            line(canvas, [(x - w * 0.66, y - 2), (x - 3, y - height * 0.12)], 1.3, (109, 140, 123))


def shelter_face(canvas, _):
    polygon(canvas, [(1, 131), (8, 88), (44, 58), (58, 31), (105, 7),
                     (172, 16), (195, 47), (222, 56), (231, 130)], (91, 107, 116))
    polygon(canvas, [(68, 129), (69, 83), (84, 54), (112, 43), (143, 52),
                     (155, 70), (171, 130)], (42, 54, 62))
    for points in [[(9, 103), (43, 78), (66, 70)], [(65, 44), (110, 19), (166, 28)],
                   [(150, 45), (183, 48), (219, 74)], [(167, 89), (201, 92), (224, 104)]]:
        line(canvas, points, 3, (143, 154, 155))
    for x, y, r in [(27, 122, 15), (49, 122, 12), (186, 119, 16), (217, 122, 12)]:
        oval(canvas, x, y, r, 7, (113, 123, 117))


def junk_heap(canvas, _):
    for x, y, rx, ry, color in [(31, 84, 27, 15, (97, 89, 83)), (126, 86, 34, 13, (95, 82, 73)),
                                (87, 87, 39, 10, (78, 78, 75))]:
        oval(canvas, x, y, rx, ry, color)
    for x0, y0, x1, y1, color in [(29, 38, 79, 90, (111, 114, 104)),
                                   (55, 25, 96, 72, (132, 115, 94)),
                                   (104, 61, 148, 91, (116, 105, 91))]:
        canvas.put(canvas.mask(box(x0, y0, x1, y1)), color)
        line(canvas, [(x0 + 2, y1 - 2), (x0 + 2, y0 + 2), (x1 - 3, y0 + 2)], 2, (153, 146, 122))
    canvas.put(canvas.mask(box(61, 31, 88, 47)), (50, 61, 59))
    for x in (40, 48, 91, 113, 135):
        oval(canvas, x, 83, 3, 3, (60, 59, 54))
    line(canvas, [(12, 96), (34, 92), (50, 95), (57, 79), (78, 79), (100, 96), (150, 98)], 2, (66, 58, 54))
    line(canvas, [(39, 44), (34, 60), (51, 68), (51, 88), (61, 94)], 2, (56, 53, 47))
    line(canvas, [(107, 65), (136, 65)], 2, (57, 56, 52))


PIECES = {
    "fantasy_grave_niche": Piece((0, 0, 128, 112), grave_niche, px=1.5),
    "fantasy_strata": Piece((0, 0, 144, 120), strata, px=1.5),
    "fantasy_pines": Piece((0, 0, 146, 158), pines, px=1.5),
    "fantasy_shelter_face": Piece((0, 0, 232, 132), shelter_face, px=1.5),
    "fantasy_junk_heap": Piece((0, 0, 160, 100), junk_heap, px=1.5),
}

TARGETS = targets(PIECES, {})
