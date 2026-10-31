"""GNU-ton's vector well (the Science dimension): every wall is a floor, so
each wall is furnished as one.

Drawn in room coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/gnu_ton_gravity/make_specs.py`
(`vector_well`: 1280 by 1600; the floor y 1536, the vault's underside y 48;
the east wall's face x 1264 under the field that pulls right, y 1024..1536;
the west rock's face x 320 under the band that pulls left, y 560..1024; the
vault over the field that pulls up, x 320..640):

- `well_east_study`: a study standing on the east wall: a bookcase, a fern
  in its pot, a reading lamp, all of them upright for a body the field holds
  to that wall.
- `well_west_parlour`: an armchair and a standard lamp standing on the west
  rock, for the band that pulls left.
- `well_vault_table`: a little table standing on the vault, upside down to
  the rest of us: an apple on it, and a cup that does not spill.
- `well_mistakes`: on the well's floor, where every mistake ends: apples, a
  top hat, a book open on its face, a slipper, a quill.

Animations: ``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

from typing import Dict

from ._district_props import Piece, targets
from ._town_kit import mix, scale
from .orbital_station import AMBER, HULL, HULL_LIGHT, INK, STEEL_DARK

FLOOR, VAULT = 1536, 48
EAST_FACE, WEST_FACE = 1264, 320
PAL = {"stone": HULL, "stone_light": HULL_LIGHT, "dark": STEEL_DARK, "lamp": AMBER}

WOOD = (122, 80, 50)
WOOD_DARK = (84, 54, 34)
WOOD_LIGHT = (160, 112, 74)
PAPER = (240, 230, 204)
VELVET = (120, 40, 60)
VELVET_LIGHT = (160, 70, 90)
LEAF = (70, 130, 70)
LEAF_LIGHT = (110, 170, 100)
POT = (190, 100, 70)
APPLE = (200, 40, 40)
APPLE_LIGHT = (240, 110, 100)
SHADE = (236, 214, 160)
GLOW = (255, 220, 150)
BOOKS = ((110, 40, 40), (40, 70, 110), (60, 100, 60), (150, 120, 50), (90, 60, 110))
HAT = (34, 30, 36)


class Floor:
    """A floor for the things standing on it, in its own coordinates: `u`
    along it, `v` up from it (away from whatever pulls). `origin` is the room
    point of (0, 0); `along` and `up` are the room directions of u and v."""

    def __init__(self, origin, along, up):
        self.o, self.a, self.n = origin, along, up

    def at(self, u, v):
        return (self.o[0] + u * self.a[0] + v * self.n[0], self.o[1] + u * self.a[1] + v * self.n[1])

    def box(self, u0, v0, u1, v1):
        return lambda p: p.poly([self.at(u0, v0), self.at(u1, v0), self.at(u1, v1), self.at(u0, v1)])

    def poly(self, pts):
        return lambda p: p.poly([self.at(u, v) for u, v in pts])

    def oval(self, u, v, ru, rv):
        x, y = self.at(u, v)
        rx, ry = (ru, rv) if self.a[0] else (rv, ru)
        return lambda p: p.ellipse(x, y, rx, ry)

    def line(self, pts, w):
        return lambda p: p.line([self.at(u, v) for u, v in pts], w)


def bookcase(c, f, u):
    c.put(c.mask(f.box(u, 0, u + 90, 150)), WOOD)
    c.put(c.mask(f.box(u + 6, 6, u + 84, 144)), WOOD_DARK)
    for s, v in enumerate((6, 52, 98)):
        c.put(c.mask(f.box(u + 4, v - 2, u + 86, v + 2)), WOOD_LIGHT)
        for i in range(7):
            h = 32 + (i * 7 + s * 5) % 10
            c.put(c.mask(f.box(u + 9 + i * 11, v + 2, u + 18 + i * 11, v + 2 + h)), BOOKS[(i + s) % len(BOOKS)])


def fern(c, f, u):
    c.put(c.mask(f.poly([(u, 0), (u + 40, 0), (u + 46, 34), (u - 6, 34)])), POT)
    c.put(c.mask(f.box(u - 8, 30, u + 48, 38)), scale(POT, 0.8))
    for i, (du, dv, r) in enumerate(((20, 60, 16), (4, 80, 14), (36, 82, 14), (14, 104, 12), (30, 112, 11), (20, 130, 9))):
        c.put(c.mask(f.oval(u + du, dv, r * 0.7, r * 1.4)), LEAF if i % 2 else LEAF_LIGHT)


def standard_lamp(c, f, u, tall=150):
    c.put(c.mask(f.box(u - 14, 0, u + 14, 6)), INK)
    c.put(c.mask(f.box(u - 2, 6, u + 2, tall)), INK)
    c.put(c.mask(f.poly([(u - 22, tall - 6), (u + 22, tall - 6), (u + 14, tall + 26), (u - 14, tall + 26)])), SHADE)
    c.light(c.mask(f.oval(u, tall - 10, 30, 22), blur=8), GLOW, 0.5)


def armchair(c, f, u):
    c.put(c.mask(f.box(u, 0, u + 8, 14)), WOOD_DARK)
    c.put(c.mask(f.box(u + 82, 0, u + 90, 14)), WOOD_DARK)
    c.put(c.mask(f.box(u, 14, u + 90, 44)), VELVET)
    c.put(c.mask(f.box(u + 60, 44, u + 90, 116)), VELVET)
    c.put(c.mask(f.oval(u + 75, 116, 16, 8)), VELVET)
    c.put(c.mask(f.box(u - 4, 30, u + 14, 66)), VELVET_LIGHT)
    c.put(c.mask(f.box(u + 6, 44, u + 60, 56)), VELVET_LIGHT)


def little_table(c, f, u):
    for lu in (u + 4, u + 70):
        c.put(c.mask(f.box(lu, 0, lu + 6, 60)), WOOD_DARK)
    c.put(c.mask(f.box(u - 6, 60, u + 86, 68)), WOOD)
    c.put(c.mask(f.oval(u + 26, 80, 11, 12)), APPLE)
    c.put(c.mask(f.oval(u + 22, 84, 4, 4)), APPLE_LIGHT)
    c.put(c.mask(f.line([(u + 26, 92), (u + 28, 98)], 2)), WOOD_DARK)
    c.put(c.mask(f.box(u + 50, 68, u + 64, 84)), PAPER)
    c.put(c.mask(f.box(u + 46, 68, u + 68, 70)), PAPER)


def east_study(c, k):
    # The east wall is the floor: up is west, along is down the wall.
    f = Floor((EAST_FACE, 1060), (0, 1), (-1, 0))
    bookcase(c, f, 40)
    fern(c, f, 190)
    standard_lamp(c, f, 330, 140)


def west_parlour(c, k):
    # The west rock's face is the floor: up is east, along is up the rock.
    f = Floor((WEST_FACE, 1000), (0, -1), (1, 0))
    armchair(c, f, 60)
    standard_lamp(c, f, 220, 130)


def vault_table(c, k):
    # The vault is the floor: up is down.
    f = Floor((380, VAULT), (1, 0), (0, 1))
    little_table(c, f, 0)


def mistakes(c, k):
    f = Floor((300, FLOOR), (1, 0), (0, -1))
    for u, r in ((20, 12), (44, 11), (32, 30), (300, 12), (420, 11)):
        v = r if r < 20 else 22
        rr = 12 if r >= 20 else r
        c.put(c.mask(f.oval(u, v, rr, rr)), APPLE)
        c.put(c.mask(f.oval(u - 4, v + 4, 3.5, 3.5)), APPLE_LIGHT)
        c.put(c.mask(f.line([(u, v + rr), (u + 2, v + rr + 6)], 2)), WOOD_DARK)
    # A top hat on its side.
    c.put(c.mask(f.box(110, 0, 160, 44)), HAT)
    c.put(c.mask(f.box(104, 0, 110, 56)), HAT)
    c.put(c.mask(f.box(110, 6, 160, 12)), (150, 40, 40))
    # A book, open on its face.
    c.put(c.mask(f.poly([(190, 0), (250, 0), (240, 14), (220, 8), (200, 14)])), BOOKS[1])
    c.put(c.mask(f.box(194, 0, 246, 3)), PAPER)
    # A slipper, and a quill.
    c.put(c.mask(f.poly([(340, 0), (380, 0), (384, 8), (372, 14), (346, 12)])), VELVET)
    c.put(c.mask(f.oval(366, 10, 10, 3)), VELVET_LIGHT)
    c.put(c.mask(f.poly([(260, 2), (296, 30), (290, 32), (258, 4)])), PAPER)
    c.put(c.mask(f.line([(258, 2), (264, 6)], 1.2)), INK)


PIECES: Dict[str, Piece] = {
    "well_east_study": Piece((EAST_FACE - 190, 1080, EAST_FACE, 1420), east_study),
    "well_west_parlour": Piece((WEST_FACE, 600, WEST_FACE + 190, 1000), west_parlour),
    "well_vault_table": Piece((360, VAULT, 480, VAULT + 110), vault_table),
    "well_mistakes": Piece((270, FLOOR - 70, 760, FLOOR), mistakes),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
