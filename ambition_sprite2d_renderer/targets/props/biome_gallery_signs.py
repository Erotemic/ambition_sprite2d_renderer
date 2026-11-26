"""Signs above the four groups of doors in the Hall of Biomes."""

from ._district_props import Piece, targets
from ._town_kit import box
from .castle_godwin import lettering

INK = (36, 39, 70)
TRIM = (205, 183, 133)
WHITE = (246, 237, 218)

GROUPS = (
    (472, "CITY AND LAB", (123, 178, 219), "city"),
    (1048, "BELOW GROUND", (219, 165, 117), "rock"),
    (1496, "FOREST AND SEA", (116, 192, 161), "wave"),
    (1880, "SKY", (191, 166, 231), "stars"),
)


def symbols(c, x, kind, color):
    """Draw the symbol that identifies the group."""
    if kind == "city":
        for dx, top, width in ((-12, 159, 7), (-4, 153, 8), (5, 157, 7)):
            c.put(c.mask(box(x + dx, top, x + dx + width, 176)), color)
    elif kind == "rock":
        c.put(c.mask(lambda p: p.poly([
            (x - 13, 175), (x - 7, 157), (x + 4, 153), (x + 13, 162), (x + 10, 175),
        ])), color)
        c.put(c.mask(lambda p: p.line([(x - 7, 172), (x + 3, 165), (x + 11, 166)], 2)), INK)
    elif kind == "wave":
        c.put(c.mask(lambda p: p.poly([(x - 4, 152), (x - 14, 166), (x + 5, 166)])), color)
        c.put(c.mask(lambda p: p.line([(x - 14, 174), (x - 5, 171), (x + 4, 174), (x + 13, 171)], 3)), color)
    else:
        c.put(c.mask(lambda p: p.poly([
            (x, 151), (x + 3, 160), (x + 11, 164), (x + 3, 167),
            (x, 176), (x - 3, 167), (x - 11, 164), (x - 3, 160),
        ])), color)
        c.put(c.mask(lambda p: p.ellipse(x + 12, 155, 2)), color)


def signs(c, _kit):
    for x, text, color, kind in GROUPS:
        c.put(c.mask(box(x - 110, 144, x + 110, 186)), TRIM)
        c.put(c.mask(box(x - 108, 146, x + 108, 184)), INK)
        c.put(c.mask(box(x - 108, 182, x + 108, 184)), color)
        c.put(c.mask(lambda p: p.poly([(x - 6, 186), (x, 192), (x + 6, 186)])), TRIM)
        symbols(c, x - 84, kind, color)
        lettering(c, text, x + 17, 158, 12, WHITE)


TARGETS = targets({"biome_gallery_signs": Piece((358, 140, 1994, 196), signs)}, {})
