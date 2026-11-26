"""The ranger station inside (`primeval_ranger_station`, the jungle
dimension): the trail ranger's hut at the trailhead, from within.

Drawn in room coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/primeval/tar_pits.py` (`ranger_station`):
the floor (y 448), the ceiling (to y 32), the door out (x 40).

- `ranger_station_room`: plank walls under a thatch; the door out; a
  map of the trails above and below the ridge; the radio on
  its desk, its microphone and a lamp; specimen shelves (jars of ferns, of
  eggs, and of small things, very annoyed); a cot; the
  lost-property box (one boot, a monocle, an umbrella); a coat peg.

Animations: ``idle``, 1 frame. No drop shadows.
"""

from __future__ import annotations

from typing import Dict

from ._district_props import Piece, targets
from ._town_kit import box, scale
from .castle_godwin import lettering
from .primeval_props import LEAF_LIGHT, PAL

W, FLOOR, CEIL = 1024, 448, 32
WOOD = (128, 92, 58)
WOOD_DARK = (82, 58, 38)
WOOD_LIGHT = (170, 130, 84)
THATCH = (176, 150, 84)
PAPER = (232, 222, 190)
GLASS = (200, 226, 220)
INK = (60, 50, 40)


def trail_map(c):
    """Show the known paths from the station. Omit hidden passages."""
    c.put(c.mask(box(326, 75, 670, 242)), WOOD_DARK)
    c.put(c.mask(box(330, 79, 666, 238)), PAPER)
    c.put(c.mask(lambda p: [
        p.ellipse(x, y, 1.8) for x in (335, 661) for y in (84, 233)
    ]), WOOD)
    trailhead, run, rookery, ridge = (370, 160), (420, 160), (495, 160), (569, 160)
    treetops, canopy, mountain = (457, 119), (569, 119), (633, 119)
    fossil_beds, tar_pits = (513, 213), (624, 213)
    lower_ink = (143, 80, 31)
    upper_ink = (44, 104, 86)
    trail_ink = (135, 50, 38)
    c.put(c.mask(lambda p: p.line([trailhead, run, rookery, ridge], 2.4)), trail_ink)
    c.put(c.mask(lambda p: (
        p.line([run, (420, 119), treetops, (495, 119), rookery], 2.4),
        p.line([ridge, canopy, mountain], 2.4),
    )), upper_ink)
    c.put(c.mask(lambda p: p.line([ridge, fossil_beds, tar_pits, ridge], 2.4)), lower_ink)
    c.put(c.mask(lambda p: p.ring(*trailhead, 8, 1.5)), trail_ink)
    stops = (
        (trailhead, "TRAILHEAD", (370, 138), trail_ink),
        (run, "RUN", (420, 171), trail_ink),
        (rookery, "ROOKERY", (495, 171), trail_ink),
        (ridge, "RIDGE", (606, 153), trail_ink),
        (treetops, "TREETOPS", (457, 104), upper_ink),
        (canopy, "CANOPY", (569, 104), upper_ink),
        (mountain, "MOUNTAIN", (633, 104), upper_ink),
        (fossil_beds, "FOSSIL BEDS", (513, 221), lower_ink),
        (tar_pits, "TAR PITS", (624, 221), lower_ink),
    )
    for (x, y), name, label, colour in stops:
        c.put(c.mask(lambda p: p.ellipse(x, y, 3.8)), colour)
        lettering(c, name, *label, 9, INK)


def room(c, k):
    wall = c.mask(box(16, CEIL, W - 16, FLOOR))
    c.put(wall, WOOD)
    c.put(wall * c.mask(lambda p: [p.rect(16, y, W - 16, y + 1.2) for y in range(CEIL + 20, FLOOR, 22)]), WOOD_DARK)
    c.tone(wall * (c.noise("station_planks", 30, 6, 2) - 0.5), 0.12)
    c.put(c.mask(lambda p: [p.rect(x, CEIL, x + 10, FLOOR) for x in (16, 340, 680, W - 26)]), WOOD_DARK)
    thatch = c.mask(box(16, CEIL, W - 16, CEIL + 26))
    c.put(thatch, THATCH)
    c.put(thatch * c.mask(lambda p: [p.line([(x, CEIL), (x + 6, CEIL + 26)], 1) for x in range(16, W, 7)]), scale(THATCH, 0.75))
    # The door out (the room's door zone, x 40..88).
    c.put(c.mask(box(34, FLOOR - 104, 94, FLOOR)), WOOD_DARK)
    c.put(c.mask(box(40, FLOOR - 96, 88, FLOOR)), (60, 44, 30))
    c.put(c.mask(lambda p: [p.rect(40, y, 88, y + 2) for y in (FLOOR - 70, FLOOR - 30)]), WOOD_DARK)
    c.put(c.mask(lambda p: p.ellipse(80, FLOOR - 50, 2.4)), (200, 170, 90))
    trail_map(c)
    # The radio desk: the set, its dials, the microphone, a lamp.
    c.put(c.mask(lambda p: (p.rect(700, FLOOR - 44, 880, FLOOR - 38), p.rect(706, FLOOR - 38, 712, FLOOR), p.rect(868, FLOOR - 38, 874, FLOOR))), WOOD_DARK)
    c.put(c.mask(box(720, FLOOR - 96, 810, FLOOR - 44)), (70, 76, 70))
    c.put(c.mask(lambda p: [p.ring(x, FLOOR - 76, 7, 2) for x in (740, 766, 792)]), (200, 196, 180))
    c.put(c.mask(lambda p: p.rect(730, FLOOR - 58, 800, FLOOR - 52)), (150, 200, 120))
    c.put(c.mask(lambda p: (p.line([(814, FLOOR - 96), (814, FLOOR - 150)], 1.4), p.ellipse(814, FLOOR - 152, 2.4))), (180, 180, 186))
    c.put(c.mask(lambda p: (p.line([(830, FLOOR - 44), (838, FLOOR - 64)], 2), p.ellipse(840, FLOOR - 68, 4, 5))), (40, 40, 44))
    c.put(c.mask(lambda p: (p.line([(860, FLOOR - 44), (852, FLOOR - 76)], 2), p.poly([(842, FLOOR - 76), (866, FLOOR - 76), (858, FLOOR - 88), (850, FLOOR - 88)]))), (60, 90, 60))
    c.light(c.mask(lambda p: p.ellipse(854, FLOOR - 60, 40, 24), blur=10), (255, 230, 160), 0.3)
    # Specimen shelves: jars of ferns, of eggs, of small annoyed things.
    for y in (150, 210):
        c.put(c.mask(lambda p: p.rect(120, y, 300, y + 6)), WOOD_DARK)
    for i, x in enumerate(range(130, 296, 30)):
        for y in (150, 210):
            jar = c.mask(lambda p: p.rect(x, y - 30, x + 20, y))
            c.put(jar, GLASS, 0.5)
            c.put(c.mask(lambda p: p.rect(x - 1, y - 33, x + 21, y - 29)), (120, 110, 90))
            what = (i + (y == 210)) % 3
            if what == 0:
                c.put(c.mask(lambda p: [p.line([(x + 10, y - 2), (x + 10 + dx, y - 22)], 1.6) for dx in (-6, 0, 6)]), LEAF_LIGHT)
            elif what == 1:
                c.put(c.mask(lambda p: p.ellipse(x + 10, y - 10, 6, 8)), (236, 226, 200))
            else:
                c.put(c.mask(lambda p: (p.ellipse(x + 10, y - 8, 6, 4), p.line([(x + 14, y - 10), (x + 18, y - 18)], 2), p.line([(x + 4, y - 8), (x + 1, y - 4)], 1.6))), (110, 150, 70))
                c.put(c.mask(lambda p: p.ellipse(x + 17, y - 19, 1)), (20, 20, 20))
    # The cot, and the lost-property box (a boot, a monocle, an umbrella).
    c.put(c.mask(lambda p: (p.rect(120, FLOOR - 30, 300, FLOOR - 22), [p.line([(x, FLOOR - 22), (x + 10, FLOOR)], 2) for x in (126, 284)])), WOOD_DARK)
    c.put(c.mask(lambda p: p.rect(124, FLOOR - 36, 296, FLOOR - 30)), (100, 120, 90))
    c.put(c.mask(lambda p: p.ellipse(140, FLOOR - 38, 14, 6)), (220, 214, 200))
    c.put(c.mask(box(920, FLOOR - 40, 990, FLOOR)), WOOD_LIGHT)
    c.put(c.mask(lambda p: p.rect(926, FLOOR - 32, 984, FLOOR - 28)), INK)
    c.put(c.mask(lambda p: (p.poly([(930, FLOOR - 40), (944, FLOOR - 40), (946, FLOOR - 60), (936, FLOOR - 60)]), p.rect(930, FLOOR - 44, 952, FLOOR - 40))), (60, 40, 30))
    c.put(c.mask(lambda p: (p.ring(962, FLOOR - 50, 5, 1.2), p.line([(967, FLOOR - 50), (972, FLOOR - 40)], 0.6))), (200, 180, 100))
    c.put(c.mask(lambda p: (p.line([(978, FLOOR - 40), (996, FLOOR - 90)], 1.6), p.poly([(984, FLOOR - 92), (1008, FLOOR - 92), (996, FLOOR - 104)]))), (60, 60, 120))
    # A coat peg by the door: a ranger's hat and a lantern.
    c.put(c.mask(lambda p: p.rect(110, 260, 160, 264)), WOOD_DARK)
    c.put(c.mask(lambda p: (p.ellipse(124, 268, 16, 4), p.ellipse(124, 262, 9, 7))), (140, 120, 80))
    c.put(c.mask(lambda p: (p.line([(150, 264), (150, 276)], 1), p.rect(144, 276, 156, 292))), (180, 140, 60))


PIECES: Dict[str, Piece] = {
    "ranger_station_room": Piece((16, CEIL, W - 16, FLOOR), room),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
