"""Paint skulls for the chargen head species."""

from ..characters import _humanoid_bone_art as bones


# Each profile gives the upper muzzle ridge, upper jaw tip, and tooth row.
MUZZLES = {
    "dog": ((6, -8), (19, -4), (22, 4), (15, 9), (5, 6)),
    "cat": ((6, -7), (12, -3), (14, 3), (10, 8), (4, 7)),
    "horse": ((5, -8), (14, 0), (23, 9), (19, 15), (9, 10)),
    "sea_lion": ((7, -7), (16, -3), (19, 3), (14, 9), (4, 7)),
    "rabbit": ((6, -7), (13, -4), (16, 2), (11, 7), (4, 7)),
    "bear": ((8, -8), (17, -5), (20, 2), (17, 9), (5, 8)),
    "ram": ((6, -7), (13, 0), (17, 7), (11, 12), (3, 8)),
    "alligator": ((4, -5), (24, -5), (26, 0), (22, 5), (2, 7)),
    "kangaroo": ((5, -8), (13, -4), (21, 2), (16, 7), (4, 7)),
}

BEAKS = {
    "bird": ((6, -6), (19, -3), (24, 1), (23, 7), (18, 2), (7, 3)),
    "pigeon": ((7, -5), (13, -4), (22, 2), (11, 4), (6, 3)),
    "finch": ((6, -6), (15, -4), (22, 1), (12, 7), (6, 4)),
    "owl": ((7, -6), (18, -4), (22, 1), (20, 8), (15, 4), (7, 3)),
}


def paint(canvas, species, center, palette=bones.FLASH):
    """Paint one skull with its neck joint below the center."""
    if species == "human":
        bones.skull(canvas, center, palette=palette)
        return

    def at(point):
        return (center[0] + point[0], center[1] + point[1])

    def poly(points, color, edge=None, width=1.0):
        canvas.poly([at(point) for point in points], color, edge, width)

    def line(points, color, width):
        canvas.line([at(point) for point in points], color, width)

    def disk(x, y, r, color):
        canvas.disk(at((x, y)), r, color, None)

    p = palette
    if species == "ram":
        horn = [(-12, -2), (-20, -5), (-23, -13), (-21, -20),
                (-14, -23), (-8, -21), (-5, -16), (-7, -10), (-12, -8)]
        line(horn, p.ink, 6.1)
        line(horn, p.shade, 4.5)
        line(horn[:7], p.bone, 2.0)

    if species in BEAKS:
        poly([(-18, -7), (-14, -14), (-7, -17), (3, -16), (9, -11),
              (12, -5), (11, 1), (6, 8), (-2, 12), (-13, 9), (-17, 3)],
             p.bone, p.ink, 1.3)
        poly([(-16, -6), (-13, 2), (-4, 6), (4, 4), (-2, 12), (-13, 9)],
             p.shade)
        disk(1, -5, 6.4 if species == "owl" else 5.2, p.cavity)
        if species == "owl":
            disk(9, -7, 3.2, p.cavity)
        poly(BEAKS[species], p.bone, p.ink, 1.0)
        line([(-10, -12), (-4, -14), (3, -13)], p.light, 1.4)
        return

    jaw = MUZZLES[species]
    tip_x, tip_y = jaw[2]
    chin = jaw[3][1] + 5
    poly([(-12, 1), (-10, 9), (-3, chin), (tip_x - 2, chin),
          (tip_x, tip_y + 4), (tip_x - 4, tip_y + 3), (-4, chin - 4),
          (-7, 6), (-7, 0)], p.shade, p.ink, 1.1)

    crown = {
        "cat": [(-15, -5), (-13, -12), (-7, -16), (2, -15), (7, -11)],
        "rabbit": [(-15, -4), (-13, -11), (-8, -15), (0, -14), (7, -10)],
        "bear": [(-17, -5), (-15, -12), (-9, -17), (1, -17), (9, -12)],
        "alligator": [(-16, -3), (-15, -8), (-9, -11), (-2, -10), (2, -12), (6, -9)],
        "kangaroo": [(-15, -5), (-12, -11), (-7, -14), (0, -13), (6, -10)],
    }.get(species, [(-16, -5), (-13, -11), (-8, -15), (0, -15), (6, -11)])
    poly([*crown, *jaw, (0, 10), (-7, 10), (-13, 5)], p.bone, p.ink, 1.3)
    poly([crown[0], (-10, -1), (-5, 5), (-7, 10), (-13, 5)], p.shade)
    poly([(-7, -7), (-1, -9), (4, -6), (2, -1), (-3, 2), (-7, -1)], p.cavity)
    poly([(-12, 0), (-8, 2), (-6, 6), (-11, 5)], p.cavity)
    poly([(tip_x - 6, tip_y - 4), (tip_x - 2, tip_y - 4),
          (tip_x - 1, tip_y - 1), (tip_x - 4, tip_y)], p.cavity)
    line([(-10, crown[1][1] + 1), (-4, crown[2][1] + 2), (2, crown[2][1] + 3)], p.light, 1.15)
    line([(-6, 2), (-2, 3), (3, 0)], p.light, 1.2)

    if species in ("rabbit", "kangaroo"):
        poly([(tip_x - 3, tip_y + 1), (tip_x, tip_y + 1),
              (tip_x - 1, tip_y + 8), (tip_x - 4, tip_y + 7)], p.light, p.ink, 0.85)
    else:
        count = 7 if species == "alligator" else 4
        for index in range(count):
            t = (index + 1) / (count + 1)
            x = 4 + (tip_x - 4) * t
            y = 6 + (tip_y - 4) * t
            length = 3.6 if species != "horse" and index == count - 1 else 2.2
            poly([(x - 1, y), (x + 1, y), (x, y + length)], p.light, p.ink, 0.72)
