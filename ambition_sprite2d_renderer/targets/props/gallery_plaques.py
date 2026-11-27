"""Plaques for the hub galleries and the Gram Reaper practice room."""

from ._district_props import Piece, targets
from ._town_kit import box, mix
from .castle_godwin import lettering

CREAM = (248, 238, 211)
METAL = (187, 146, 78)
PLUM_METAL = (145, 117, 153)


def plaque(c, x, y, title, enamel, metal, icon):
    """Draw a beveled metal frame around the enamel and lettering."""
    half = 48 + 5 * max(0, len(title) - 8)
    left, right = x - half, x + half
    ends = [(left, y + 4), (left + 4, y), (right - 4, y), (right, y + 4),
            (right, y + 19), (right - 4, y + 23), (left + 4, y + 23), (left, y + 19)]
    c.put(c.mask(lambda p: p.poly(ends)), mix(metal, (28, 23, 29), 0.6))
    c.put(c.mask(lambda p: p.poly([
        (left + 2, y + 5), (left + 5, y + 2), (right - 5, y + 2), (right - 2, y + 5),
        (right - 2, y + 18), (right - 5, y + 21), (left + 5, y + 21), (left + 2, y + 18),
    ])), metal)
    c.put(c.mask(box(left + 6, y + 2, right - 6, y + 3)), mix(metal, CREAM, 0.7))
    c.put(c.mask(box(left + 7, y + 4, right - 7, y + 20)), mix(enamel, (8, 10, 20), 0.65))
    c.put(c.mask(box(left + 8, y + 5, right - 8, y + 19)), enamel)
    c.put(c.mask(box(left + 9, y + 5, right - 9, y + 6)), mix(enamel, CREAM, 0.22))
    for stud in (left + 4, right - 4):
        c.put(c.mask(lambda p: p.ellipse(stud, y + 12, 1.6)), mix(metal, (28, 23, 29), 0.65))
        c.put(c.mask(lambda p: p.ellipse(stud - 0.3, y + 11.5, 0.65)), CREAM)
    c.put(c.mask(lambda p: p.ring(left + 18, y + 12, 5.8, 0.7)), mix(enamel, metal, 0.7))
    c.put(c.mask(lambda p: icon(p, left + 18, y + 12)), mix(CREAM, metal, 0.28))
    lettering(c, title, x + 7, y + 7, 9, CREAM)


def portraits(p, x, y):
    for offset in (-2.4, 0, 2.4):
        p.ellipse(x + offset, y - 1.5, 1.0)
        p.arch(x + offset - 1.2, y, x + offset + 1.2, y + 2.7)


def landscape(p, x, y):
    p.ellipse(x + 2.1, y - 2.5, 0.9)
    p.poly([(x - 3.6, y + 2.6), (x - 1.4, y - 2.4), (x + 0.4, y + 0.1),
            (x + 1.8, y - 1), (x + 3.6, y + 2.6)])


def shield(p, x, y):
    p.poly([(x - 3, y - 2.9), (x + 3, y - 2.9), (x + 2.4, y + 0.8),
            (x, y + 3.6), (x - 2.4, y + 0.8)])


def crescent(p, x, y):
    p.ellipse(x, y, 3.4)
    p.ellipse(x + 1.6, y - 1.25, 2.9, value=0)


def hub_plaques(c, _kit):
    plaque(c, 805, 800, "CHARACTERS", (32, 43, 70), METAL, portraits)
    plaque(c, 968, 800, "BIOMES", (38, 78, 69), METAL, landscape)
    plaque(c, 1084, 800, "BOSSES", (94, 44, 56), METAL, shield)


def gram_reaper_plaque(c, _kit):
    plaque(c, 1688, 207, "GRAM REAPER", (42, 25, 53), PLUM_METAL, crescent)


TARGETS = targets({
    "hub_gallery_plaques": Piece((745, 798, 1134, 825), hub_plaques),
    "gram_reaper_hall_plaque": Piece((1623, 205, 1753, 232), gram_reaper_plaque),
}, {})
