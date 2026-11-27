"""Draw the cut galleries and the natural cavern behind the mine."""
from math import sin

from .artkit import Art


def mine(layer_key: str, art: Art, *, deep: bool):
    layer = art.blank()
    rng = art.rand("strata")
    if layer_key == "sky":
        tones = [(0, (17, 25, 30)), (0.32, (38, 52, 57)), (0.76, (51, 59, 61)), (1, (25, 33, 37))]
        if deep:
            tones = [(0, (13, 24, 34)), (0.36, (27, 43, 55)), (0.76, (42, 58, 64)), (1, (22, 32, 42))]
        layer = art.opaque(art.ramp(tones))
        art.grain(layer, "shale grain", 2.0)
        return layer

    if layer_key == "far_backplate":
        banks, pen = art.drawing()
        for i in range(19):
            y = 0.12 + i * 0.041 + rng.uniform(-0.017, 0.017)
            path = [(j / 17, y + sin(j * 0.55 + i * 0.18) * 0.038 + rng.uniform(-0.009, 0.009))
                    for j in range(18)]
            pen.line(path, rng.uniform(0.0015, 0.006))
        art.put(layer, art.mask_of(banks), (85, 82, 80) if deep else (87, 93, 86), 0.28)
        shade, pen = art.drawing()
        for x in (-0.11, 0.35, 0.78):
            pen.poly([(x, 0.83), (x + 0.09, 0.35), (x + 0.15, 0.19), (x + 0.23, 0.23),
                      (x + 0.32, 0.36), (x + 0.37, 0.91)])
        art.put(layer, art.mask_of(shade, 4.1), (13, 26, 33), 0.52)
        if not deep:
            fixtures, pen = art.drawing()
            for x in (0.08, 0.42, 0.76):
                pen.line([(x, 0.13), (x, 0.8)], 0.013)
                pen.line([(x + 0.12, 0.13), (x + 0.12, 0.8)], 0.013)
                pen.line([(x + 0.007, 0.3), (x + 0.112, 0.176)], 0.008)
                pen.line([(x + 0.112, 0.3), (x + 0.007, 0.176)], 0.008)
                for y in (0.43, 0.66):
                    pen.line([(x, y), (x + 0.12, y)], 0.009)
                pen.line([(x + 0.06, 0.22), (x + 0.06, 0.45)], 0.004)
                art.put(layer, art.spot(x + 0.06, 0.45, 0.075, 2.4), (157, 114, 65), 0.28)
            art.put(layer, art.mask_of(fixtures), (20, 32, 38), 0.68)
        else:
            for x, y in ((0.14, 0.66), (0.47, 0.39), (0.86, 0.61)):
                art.put(layer, art.spot(x, y, 0.16, 2.7), (81, 128, 134), 0.30)
    elif layer_key == "near_background":
        ledge, pen = art.drawing()
        crest = [(j / 45, 0.83 + rng.uniform(-0.022, 0.027) + sin(j * 0.36) * 0.036)
                 for j in range(46)]
        pen.poly([*crest, (1.0, 1.0), (0, 1.0)])
        art.put(layer, art.mask_of(ledge, 0.7), (23, 39, 47), 0.63)
        needles, pen = art.drawing()
        if deep:
            for j in range(2, 44, 3):
                x, y = crest[j]
                h = rng.uniform(0.021, 0.077)
                pen.poly([(x - 0.012, y), (x - 0.008, y - h * 0.73), (x + 0.008, y - h),
                          (x + 0.016, y - h * 0.69), (x + 0.014, y)])
            art.put(layer, art.mask_of(needles), (69, 109, 114), 0.48)
    elif layer_key == "foreground_atmosphere":
        art.put(layer, art.spot(0.33, 0.79, 0.45, 2.2), (63, 115, 119) if deep else (116, 86, 61), 0.09)
    return layer


def mine_cut(layer_key: str, art: Art):
    return mine(layer_key, art, deep=False)


def mine_lode(layer_key: str, art: Art):
    return mine(layer_key, art, deep=True)
