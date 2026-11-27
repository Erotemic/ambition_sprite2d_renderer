"""Draw the distant slopes behind the high road."""

from .artkit import Art


def mountain_pass(layer_key: str, art: Art):
    if layer_key == "sky":
        layer = art.opaque(art.ramp([
            (0.0, (105, 151, 179)), (0.38, (157, 192, 211)),
            (0.57, (203, 218, 221)), (1.0, (170, 192, 199)),
        ]))
        art.light(layer, art.spot(0.30, 0.34, 0.28, 2.2), (235, 226, 198), 0.42)
        art.grain(layer, "high air", 0.9)
        return layer

    layer = art.blank()
    if layer_key == "far_backplate":
        far, _ = art.ridge("north range", 0.49, 0.11, cells=5.0, sharp=0.66)
        art.put(layer, far, (142, 171, 184))
        peaks = [
            (0.03, 0.51), (0.18, 0.39), (0.23, 0.32), (0.29, 0.39), (0.35, 0.44),
            (0.46, 0.33), (0.51, 0.28), (0.57, 0.34), (0.65, 0.45), (0.73, 0.40),
            (0.81, 0.30), (0.85, 0.36), (0.89, 0.38), (1.0, 0.52),
        ]
        mask, pen = art.drawing()
        pen.poly([*peaks, (1.0, 1.0), (0.0, 1.0)])
        rock = art.mask_of(mask, 0.8)
        art.put(layer, rock, (119, 149, 164))
        faces, pen = art.drawing()
        for face in [[(0.23, 0.32), (0.31, 0.402), (0.40, 0.63), (0.29, 0.58), (0.32, 0.49)],
                     [(0.51, 0.28), (0.58, 0.35), (0.65, 0.45), (0.72, 0.64), (0.58, 0.61), (0.61, 0.52)],
                     [(0.81, 0.30), (0.89, 0.38), (1.0, 0.52), (0.95, 0.67), (0.88, 0.56)]]:
            pen.poly(face)
        art.put(layer, art.mask_of(faces, 2.0) * rock, (93, 126, 146), 0.58)
        seams, pen = art.drawing()
        for i in range(6):
            y = 0.43 + i * 0.035
            pen.line([(0.05, y + 0.09), (0.27, y + 0.06), (0.43, y + 0.02),
                      (0.63, y), (0.79, y - 0.055), (0.98, y - 0.02)], 0.006)
        art.put(layer, art.mask_of(seams, 1.8) * rock, (159, 178, 187), 0.28)
        snow, pen = art.drawing()
        for cap in [[(0.23, 0.32), (0.29, 0.39), (0.25, 0.377), (0.24, 0.401), (0.18, 0.39)],
                    [(0.51, 0.28), (0.57, 0.34), (0.54, 0.328), (0.50, 0.36), (0.46, 0.33)],
                    [(0.81, 0.30), (0.85, 0.36), (0.82, 0.344), (0.79, 0.371), (0.76, 0.36)]]:
            pen.poly(cap)
        art.put(layer, art.mask_of(snow, 0.6), (196, 214, 221), 0.82)
    elif layer_key == "near_background":
        shoulder, _ = art.ridge("lower fir slopes", 0.63, 0.10, cells=3.2, sharp=0.25)
        art.put(layer, shoulder, (92, 127, 135))
        alder, _ = art.ridge("alder ravine", 0.75, 0.09, cells=5.4, sharp=0.12)
        art.put(layer, alder, (77, 111, 110))
    elif layer_key == "foreground_atmosphere":
        mist = art.spot(0.56, 0.71, 0.32, 2.0)
        art.put(layer, mist, (195, 213, 214), 0.13)
    return layer
