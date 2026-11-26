"""Draw the rock-candy outcrops and trail fixtures of the Fizzuvius Slopes."""

from ._district_props import Piece, targets
from ._town_kit import box

SHADE = (62, 43, 55)
ROCK = (119, 70, 81)
FACET = (152, 84, 89)
CREST = (214, 148, 112)
WOOD = (111, 75, 61)
BRASS = (238, 179, 106)
TUBE = (115, 189, 183)


def outcrop(c, left, right, top, depth):
    """Draw each outcrop below its walk line."""
    span = right - left
    c.put(c.mask(lambda p: p.poly([
        (left, top), (right, top), (right - 7, top + 14),
        (left + span * 0.72, top + depth * 0.73),
        (left + span * 0.31, top + depth), (left + 15, top + 19),
    ])), SHADE)
    c.put(c.mask(lambda p: p.poly([
        (left, top), (right, top), (right - 9, top + 13),
        (left + span * 0.57, top + 18), (left + 15, top + 16),
    ])), ROCK)
    c.put(c.mask(lambda p: p.poly([
        (left + 25, top + 13), (left + span * 0.53, top + 10),
        (left + span * 0.35, top + depth - 5),
    ])), FACET)
    c.put(c.mask(box(left, top, right, top + 3)), CREST)


def ladder(c):
    """Show the rungs from the dry shelf to the first landing."""
    for x in (802, 840):
        c.put(c.mask(box(x, 672, x + 5, 1088)), SHADE)
        c.put(c.mask(box(x + 1, 672, x + 4, 1088)), WOOD)
    for y in range(679, 1081, 16):
        c.put(c.mask(box(804, y, 843, y + 5)), SHADE)
        c.put(c.mask(box(804, y, 843, y + 2)), BRASS)


def channel(c, left, right, west, east):
    """Mark the near bank and the high lip on the far bank."""
    c.put(c.mask(box(left - 14, west, left, west + 19)), ROCK)
    c.put(c.mask(box(right, east, right + 14, east + 28)), ROCK)
    c.put(c.mask(box(left - 14, west, left, west + 3)), CREST)
    c.put(c.mask(box(right, east, right + 14, east + 3)), CREST)
    c.put(c.mask(box(left, west + 15, right, west + 18)), TUBE)
    for x, y, r in ((left + 18, west + 8, 3), (left + 45, west - 2, 4), (right - 23, west + 6, 3)):
        c.put(c.mask(lambda p: p.ring(x, y, r, 1.25)), TUBE)


def signboard(c, left, right, top, post_floor=None):
    """Draw a dark face behind the sign text."""
    if post_floor is not None:
        for x in (left + 16, right - 20):
            c.put(c.mask(box(x, top, x + 4, post_floor)), SHADE)
    c.put(c.mask(box(left, top, right, top + 30)), SHADE)
    c.put(c.mask(box(left + 4, top, right - 4, top + 2)), BRASS)


def exit_frame(c, floor, color):
    """Mark the wall opening on the Caldera side of the room."""
    c.put(c.mask(lambda p: p.poly([
        (1840, floor), (1848, floor - 54), (1877, floor - 94), (1904, floor - 96),
        (1904, floor - 81), (1883, floor - 76), (1861, floor - 47), (1853, floor),
    ])), SHADE)
    c.put(c.mask(lambda p: p.line([
        (1853, floor - 4), (1865, floor - 50), (1884, floor - 77), (1903, floor - 82),
    ], 3)), color)


def slopes(c, kit):
    channel(c, 576, 704, 1152, 1088)
    channel(c, 1216, 1344, 1024, 960)
    ladder(c)
    for left, right, top, depth in (
        (768, 912, 704, 45), (912, 1040, 640, 29),
        (1600, 1760, 768, 47), (1408, 1568, 704, 38), (1216, 1376, 640, 44),
        (1024, 1184, 576, 48), (1216, 1376, 512, 40), (1408, 1568, 448, 31),
        (1600, 1760, 384, 43),
    ):
        outcrop(c, left, right, top, depth)
    signboard(c, 340, 564, 1061, 1152)
    for x in (1034, 1170):
        c.put(c.mask(box(x, 465, x + 4, 576)), SHADE)
    signboard(c, 842, 1366, 445)
    exit_frame(c, 320, BRASS)
    exit_frame(c, 832, TUBE)


PIECES = {"noodle_fizzuvius_slopes_fixtures": Piece((336, 208, 1904, 1184), slopes, px=1.25)}
TARGETS = targets(PIECES, {"accent": BRASS})
