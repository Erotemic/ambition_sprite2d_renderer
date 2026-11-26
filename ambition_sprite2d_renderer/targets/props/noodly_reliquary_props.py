"""Draw the offering stalls and the vault of the Noodly Reliquary."""

from __future__ import annotations

from ._district_props import Piece, targets
from ._town_kit import box, mix

TIMBER = (68, 45, 51)
WOOD = (115, 65, 53)
BRONZE = (169, 114, 67)
GOLD = (235, 177, 96)
IRON = (79, 76, 91)
CREAM = (248, 220, 172)
FLOOR = 608

STALLS = (
    (384, 464, 544),
    (448, 592, 464),
    (528, 640, 400),
    (608, 752, 336),
    (720, 848, 400),
    (768, 912, 464),
    (896, 992, 544),
)


def stall(c, left, right, top):
    """Draw the top and apron of an offering stall."""
    c.put(c.mask(box(left, top, right, top + 4)), GOLD)
    c.put(c.mask(box(left, top + 4, right, top + 13)), WOOD)
    c.put(c.mask(box(left, top + 13, right, top + 17)), TIMBER)
    for x in range(left + 14, right - 8, 28):
        c.put(c.mask(lambda p: p.ellipse(x, top + 8, 2)), GOLD)


def lantern(c, x, top):
    """Draw a lamp on a hook."""
    c.put(c.mask(box(x - 1, top - 11, x + 1, top)), IRON)
    c.put(c.mask(box(x - 5, top, x + 5, top + 17)), TIMBER)
    c.put(c.mask(box(x - 3, top + 2, x + 3, top + 15)), CREAM)
    c.light(c.mask(lambda p: p.ellipse(x, top + 8, 26, 21), blur=11), GOLD, 0.42)


def reliquary(c, k):
    for x in (407, 962):
        c.put(c.mask(box(x, 304, x + 13, FLOOR)), TIMBER)
        c.put(c.mask(box(x + 2, 305, x + 5, FLOOR)), WOOD)
    c.put(c.mask(box(395, 294, 987, 306)), TIMBER)
    c.put(c.mask(box(395, 296, 987, 299)), BRONZE)
    for x, top in ((470, 464), (556, 400), (625, 336), (735, 336), (804, 400), (893, 464)):
        c.put(c.mask(box(x, 302, x + 3, top)), IRON)
    for x in (625, 735):
        c.put(c.mask(lambda p: [p.rect(x - 1, y, x + 4, y + 2) for y in range(304, 332, 6)]), BRONZE)
    for left, right, top in STALLS:
        stall(c, left, right, top)
    for x, y in ((407, 350), (968, 350), (680, 368)):
        lantern(c, x, y)

    for x in (321, 379):
        c.put(c.mask(box(x - 8, 567, x + 8, FLOOR)), WOOD)
        c.put(c.mask(box(x - 11, 566, x + 11, 571)), BRONZE)
        lantern(c, x, 549)
    c.put(c.mask(box(321, FLOOR - 3, 379, FLOOR)), BRONZE)

    arch = c.mask(box(1100, 426, 1236, FLOOR))
    c.put(arch * c.mask(lambda p: p.arch(1100, 426, 1236, FLOOR)), TIMBER)
    c.put(arch * c.mask(lambda p: p.arch(1110, 439, 1226, FLOOR)), (83, 74, 89))
    c.put(c.mask(lambda p: p.ellipse(1168, 503, 32)), mix(IRON, GOLD, 0.34))
    for dx, dy in ((0, -9), (-9, -2), (9, -2), (-5, 8), (5, 8)):
        c.put(c.mask(lambda p: p.ellipse(1168 + dx, 503 + dy, 2)), CREAM)
    c.put(c.mask(box(1148, 568, 1188, FLOOR)), WOOD)
    c.put(c.mask(box(1142, 566, 1194, 573)), BRONZE)
    for x in (1114, 1222):
        lantern(c, x, 531)


PIECES = {"noodly_reliquary_fixtures": Piece((304, 280, 1240, FLOOR), reliquary, px=1.5)}
TARGETS = targets(PIECES, {"accent": CREAM})
