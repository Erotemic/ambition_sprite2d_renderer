"""The upper grow deck and its stairs in the orbital station."""

from ._district_props import Piece, targets
from ._town_kit import box
from .castle_godwin import lettering
from .orbital_station import AMBER, HULL, HULL_LIGHT, INK, STEEL, STEEL_DARK, lamp

DECK = 512
FLOOR = 704


def stairs(c, foot, rise):
    """Draw the stair treads, stringer and handrail."""
    def x(offset):
        return foot + rise * offset

    c.put(c.mask(lambda p: p.poly([
        (x(0), FLOOR), (x(288), DECK), (x(288), DECK + 18), (x(22), FLOOR),
    ])), STEEL_DARK)
    c.put(c.mask(lambda p: [
        p.rect(min(x(i * 18), x((i + 1) * 18)), FLOOR - i * 12 - 6,
               max(x(i * 18), x((i + 1) * 18)), FLOOR - i * 12 + 9)
        for i in range(16)
    ]), STEEL)
    c.put(c.mask(lambda p: [
        p.line([(x(i * 18), FLOOR - i * 12 - 6), (x((i + 1) * 18), FLOOR - i * 12 - 6)], 2)
        for i in range(16)
    ]), HULL_LIGHT)
    c.put(c.mask(lambda p: [
        p.line([(x(i * 48), FLOOR - i * 32), (x(i * 48), FLOOR - i * 32 - 32)], 4)
        for i in range(7)
    ]), STEEL)
    c.put(c.mask(lambda p: p.line([(x(0), FLOOR - 32), (x(288), DECK - 32)], 3)), HULL)


def boarding_mark(c, x):
    """Mark the bottom of the stairs with an up arrow."""
    c.put(c.mask(box(x - 18, FLOOR - 54, x + 18, FLOOR - 35)), STEEL_DARK)
    c.put(c.mask(lambda p: p.poly([
        (x, FLOOR - 51), (x - 7, FLOOR - 44), (x - 3, FLOOR - 44), (x - 3, FLOOR - 38),
        (x + 3, FLOOR - 38), (x + 3, FLOOR - 44), (x + 7, FLOOR - 44),
    ])), AMBER)


def grow_deck(c, _kit):
    for x in (1328, 1776):
        c.put(c.mask(box(x - 6, DECK + 16, x + 6, FLOOR)), STEEL_DARK)
        c.put(c.mask(box(x - 4, DECK + 16, x + 1, FLOOR)), STEEL)
        c.put(c.mask(box(x - 12, FLOOR - 9, x + 12, FLOOR)), STEEL_DARK)
        c.put(c.mask(lambda p: p.line([(x, DECK + 61), (x + (30 if x == 1328 else -30), DECK + 12)], 5)), STEEL)
    stairs(c, 1024, 1)
    stairs(c, 2080, -1)
    c.put(c.mask(box(1312, DECK, 1792, DECK + 19)), STEEL_DARK)
    c.put(c.mask(box(1312, DECK, 1792, DECK + 7)), HULL)
    c.put(c.mask(lambda p: [
        p.rect(x, DECK + 9, x + 32, DECK + 14) for x in range(1328, 1760, 44)
    ]), INK)
    c.put(c.mask(lambda p: [p.rect(x, DECK - 32, x + 4, DECK) for x in range(1312, 1792, 48)]), STEEL)
    c.put(c.mask(box(1312, DECK - 33, 1792, DECK - 30)), HULL)
    for x in (1335, 1456, 1584, 1768):
        lamp(c, x, DECK + 20, AMBER, r=2, glow=6, k=0.7)
    c.put(c.mask(box(1652, 439, 1768, 464)), STEEL_DARK)
    c.put(c.mask(box(1654, 441, 1766, 462)), INK)
    lettering(c, "GROW DECK", 1710, 446, 11, HULL_LIGHT)
    c.put(c.mask(lambda p: p.line([(1710, 464), (1710, DECK - 33)], 2)), STEEL)
    boarding_mark(c, 1024)
    boarding_mark(c, 2080)


TARGETS = targets({"orbital_grow_deck": Piece((992, 434, 2112, 704), grow_deck)}, {})
