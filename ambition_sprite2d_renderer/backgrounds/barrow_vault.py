"""Draw stone vaults behind the burial rooms."""
from math import cos, pi, sin

from .artkit import Art


def arch(cx, base, rx, rise, floor):
    curve = [(cx + rx * cos(pi * i / 24), base - rise * sin(pi * i / 24)) for i in range(25)]
    return [(cx + rx, floor), *curve, (cx - rx, floor)]


def barrow_vault(layer_key: str, art: Art):
    if layer_key == "sky":
        layer = art.opaque(art.ramp([
            (0.0, (18, 21, 24)), (0.31, (49, 49, 44)),
            (0.68, (75, 66, 54)), (1.0, (32, 34, 33)),
        ]))
        for i, x in enumerate((0.19, 0.51, 0.83)):
            art.light(layer, art.spot(x, 0.56, 0.26, 2.7), (136, 104 + i * 7, 67), 0.26)
        art.grain(layer, "weathered ashlar", 2.1)
        return layer

    layer = art.blank()
    if layer_key == "far_backplate":
        for cx, base, rx, floor in [(0.16, 0.48, 0.152, 0.86), (0.50, 0.46, 0.160, 0.86),
                                     (0.84, 0.48, 0.152, 0.86)]:
            stone, pen = art.drawing()
            pen.poly(arch(cx, base, rx, 0.21, floor))
            art.put(layer, art.mask_of(stone, 0.9), (94, 84, 66), 0.76)
            chamber, pen = art.drawing()
            pen.poly(arch(cx + 0.01, base + 0.015, rx - 0.027, 0.182, floor + 0.02))
            hollow = art.mask_of(chamber, 1.2)
            art.put(layer, hollow, (24, 28, 31), 0.94)
            art.put(layer, hollow * art.spot(cx + 0.037, 0.669, 0.169, 2.2), (54, 65, 64), 0.65)
            ribs, pen = art.drawing()
            for i in range(11):
                angle = pi * i / 10
                pen.line([(cx + rx * cos(angle), base - 0.21 * sin(angle)),
                          (cx + (rx - 0.03) * cos(angle), base - 0.18 * sin(angle))], 0.0036)
            for y in (0.52, 0.595, 0.666, 0.74, 0.812):
                pen.line([(cx - rx, y), (cx - rx + 0.028, y)], 0.003)
                pen.line([(cx + rx - 0.028, y), (cx + rx, y)], 0.003)
            art.put(layer, art.mask_of(ribs), (43, 43, 40), 0.8)
        wall, pen = art.drawing()
        for row in range(12):
            y = 0.11 + row * 0.064
            pen.line([(0, y), (1, y)], 0.002)
            for col in range(11):
                x = (col + row % 2 * 0.5) * 0.101
                pen.line([(x, y), (x, y + 0.063)], 0.002)
        art.put(layer, art.mask_of(wall, 0.5) * (1 - layer[..., 3]), (24, 27, 27), 0.28)
    elif layer_key == "near_background":
        # A ledge at the base of the far wall gives the vault depth.
        ledge, pen = art.drawing()
        pen.poly([(0, 0.848), (0.2, 0.852), (0.46, 0.847), (0.71, 0.856), (1, 0.848),
                  (1, 0.916), (0.7, 0.913), (0.4, 0.919), (0, 0.917)])
        art.put(layer, art.mask_of(ledge, 0.8), (55, 50, 44), 0.7)
        rim, pen = art.drawing()
        pen.line([(0, 0.851), (0.35, 0.855), (0.67, 0.851), (1, 0.853)], 0.004)
        art.put(layer, art.mask_of(rim), (112, 86, 63), 0.38)
    elif layer_key == "foreground_atmosphere":
        art.put(layer, art.spot(0.38, 0.77, 0.36, 2.0), (105, 82, 58), 0.08)
    return layer
