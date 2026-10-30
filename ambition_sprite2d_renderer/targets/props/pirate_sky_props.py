"""The Pirate Sky Lookout (`pirate_sky_lookout`, PvN dimension): up the
ladder from the cove, a lookout deck in the open sky where the pirates keep
their burning sharks.

Drawn in room coordinates (`_district_props`) on the level's own numbers
(edited in place: `tools/ambition_ldtk_tools/specs/scenery_overlay.py`): the
deck (y 720, the whole width), the captain's perch (x 80..272, y 480), the
crow's nest (x 960..1152, y 384), the companionway down to the cove (its door
x 592..688).

- `sky_lookout_deck`: the deck, planked, its rail on stanchions; the mast up
  through the crow's nest, the Jolly Roger at its head; the captain's perch on
  braces, the ship's wheel on it (steering nothing); the companionway's
  little house round the door; a hitching rail for the sharks with its fire
  bucket; a spyglass on a tripod; an anti-shark cannon pointed up; barrels.

Animations: ``idle``, 1 frame. No drop shadows.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .eureka_props import Batch, edge_line
from .pirate_port_props import HULL, HULL_BAND, HULL_DARK, PAL, PLANK, PLANK_DARK, PLANK_LIGHT, RED_PAINT, ROPE, SAIL, TAR, TIMBER, planks, sag

W, DECK = 1280, 720
PERCH = (80, 272, 480)
NEST = (960, 1152, 384)
DOOR = (592, 688)
MAST_X = 1056
BRASS = (206, 160, 76)
IRON = (52, 54, 60)


def barrel(c, x, ground, w=30, h=40):
    m = np.maximum(c.mask(lambda p: p.ellipse(x, ground - h / 2, w / 2, h / 2)), c.mask(box(x - w / 2 + 2, ground - h + 4, x + w / 2 - 2, ground - 4)))
    c.put(m, PLANK)
    c.put(c.mask(lambda p: [p.rect(x - w / 2, y, x + w / 2, y + 2.4) for y in (ground - h + 7, ground - 9)]) * m, IRON)
    c.tone(m * np.clip((c.x - x) / (w / 2), -1, 1), -0.25)


def deck(c, k):
    g = DECK
    # The deck's side under the walked edge: a hull band, gunports.
    planks(c, k, 0, g, W, 768, HULL, step=9, tag="sky_hull")
    c.put(c.mask(box(0, g + 22, W, g + 28)), HULL_BAND)
    c.put(c.mask(lambda p: [p.rect(x, g + 34, x + 22, g + 46) for x in range(120, W, 240)]), HULL_DARK)
    edge_line(c, 0, W, g, PLANK, 6)
    # The mast, up through the nest to its head, and the Jolly Roger.
    c.put(c.mask(box(MAST_X - 9, 200, MAST_X + 9, g)), TIMBER)
    c.put(c.mask(box(MAST_X - 9, 200, MAST_X - 6, g)), PLANK_LIGHT)
    c.put(c.mask(lambda p: [p.line([(MAST_X, 220), (x, g)], 1.6) for x in (900, 1220)]), ROPE)
    flag = [(MAST_X + 9, 214), (MAST_X + 120, 222), (MAST_X + 112, 254), (MAST_X + 122, 286), (MAST_X + 9, 280)]
    c.put(c.mask(lambda p: p.poly(flag)), (24, 22, 24))
    fx, fy = MAST_X + 60, 246
    c.put(c.mask(lambda p: (p.ellipse(fx, fy - 4, 12, 11), p.rect(fx - 7, fy + 2, fx + 7, fy + 10))), SAIL)
    c.put(c.mask(lambda p: (p.ellipse(fx - 5, fy - 4, 3.2), p.ellipse(fx + 5, fy - 4, 3.2), p.rect(fx - 4, fy + 6, fx + 4, fy + 7))), (24, 22, 24))
    c.put(c.mask(lambda p: (p.line([(fx - 20, fy + 20), (fx + 20, fy + 10)], 4), p.line([(fx - 20, fy + 10), (fx + 20, fy + 20)], 4))), SAIL)
    # The crow's nest: its floor is the ledge, its basket under it, a rail over.
    x0, x1, y = NEST
    basket = c.mask(lambda p: p.poly([(x0, y), (x1, y), (x1 - 20, y + 54), (x0 + 20, y + 54)]))
    c.put(basket, PLANK_DARK)
    c.put(basket * c.mask(lambda p: [p.rect(x, y, x + 1.2, y + 54) for x in range(x0 + 8, x1, 12)]), scale(PLANK_DARK, 0.6))
    c.put(basket * c.mask(lambda p: [p.rect(x0, yy, x1, yy + 4) for yy in (y + 18, y + 40)]), IRON)
    c.tone(basket * np.clip((c.x - (x0 + x1) / 2) / ((x1 - x0) / 2), -1, 1), -0.2)
    edge_line(c, x0, x1, y, PLANK, 6)
    c.put(c.mask(lambda p: (p.rect(x0, y - 40, x1, y - 36), [p.rect(x, y - 40, x + 4, y) for x in range(x0, x1 + 1, 48)])), TIMBER)
    # The captain's perch on its braces, the wheel on it.
    px0, px1, py = PERCH
    planks(c, k, px0, py, px1, py + 16, PLANK, step=5, tag="perch")
    edge_line(c, px0, px1, py, PLANK, 5)
    c.put(c.mask(lambda p: (p.line([(px0 + 20, py + 16), (px0 + 80, g)], 8), p.line([(px1 - 20, py + 16), (px1 - 80, g)], 8),
                            p.line([(px0 + 50, py + 16), (px1 - 50, py + 120)], 5))), TIMBER)
    wx, wy = (px0 + px1) / 2, py - 46
    c.put(c.mask(lambda p: p.rect(wx - 6, wy, wx + 6, py)), TIMBER)
    c.put(c.mask(lambda p: (p.ring(wx, wy, 26, 4), p.ellipse(wx, wy, 6))), PLANK)
    c.put(c.mask(lambda p: [p.line([(wx + 10 * math.cos(t), wy + 10 * math.sin(t)), (wx + 38 * math.cos(t), wy + 38 * math.sin(t))], 3.4) for t in np.linspace(0, 2 * math.pi, 8, endpoint=False)]), PLANK_LIGHT)
    c.put(c.mask(lambda p: [p.ellipse(wx + 40 * math.cos(t), wy + 40 * math.sin(t), 3.6) for t in np.linspace(0, 2 * math.pi, 8, endpoint=False)]), PLANK)
    # The rail round the deck, on stanchions, the gap at the companionway.
    d0, d1 = DOOR
    b = Batch(c)
    xs = [x for x in range(16, W, 64) if not d0 - 40 < x < d1 + 40]
    for x in xs:
        b.add(TIMBER, 1.0, box(x - 3, g - 44, x + 3, g))
    b.draw()
    for a, bx in zip(xs, xs[1:]):
        if bx - a <= 64:
            c.put(c.mask(lambda p: (p.line(sag((a, g - 42), (bx, g - 42), 5), 2.2), p.line(sag((a, g - 22), (bx, g - 22), 4), 1.6))), ROPE)
    # The companionway's little house round the door down to the cove.
    roof = [(d0 - 24, g - 116), ((d0 + d1) / 2, g - 150), (d1 + 24, g - 116)]
    planks(c, k, d0 - 16, g - 116, d1 + 16, g, PLANK_DARK, step=10, vertical=True, tag="companion")
    c.put(c.mask(lambda p: p.poly(roof + [(d1 + 24, g - 108), (d0 - 24, g - 108)])), RED_PAINT)
    c.put(c.mask(lambda p: p.line(roof, 3)), scale(RED_PAINT, 0.6))
    # The sharks' hitching rail and its fire bucket.
    hx0, hx1 = 760, 900
    c.put(c.mask(lambda p: (p.rect(hx0, g - 52, hx0 + 8, g), p.rect(hx1 - 8, g - 52, hx1, g), p.rect(hx0 - 4, g - 56, hx1 + 4, g - 48))), TIMBER)
    c.put(c.mask(lambda p: [p.ring(x, g - 40, 6, 2) for x in (800, 830, 860)]), IRON)
    bucket = c.mask(lambda p: p.poly([(916, g), (944, g), (948, g - 30), (912, g - 30)]))
    c.put(bucket, RED_PAINT)
    c.put(c.mask(lambda p: p.ellipse(930, g - 30, 18, 4)), (90, 150, 190))
    c.put(c.mask(lambda p: p.line(sag((912, g - 30), (948, g - 30), -16), 1.6)), IRON)
    # A spyglass on its tripod, looking out.
    sx = 400
    c.put(c.mask(lambda p: [p.line([(sx, g - 60), (sx + dx, g)], 3) for dx in (-22, 0, 22)]), TIMBER)
    c.put(c.mask(lambda p: p.line([(sx - 30, g - 52), (sx + 40, g - 78)], 9)), BRASS)
    c.put(c.mask(lambda p: p.line([(sx + 40, g - 78), (sx + 60, g - 85)], 12)), BRASS)
    c.put(c.mask(lambda p: p.ellipse(sx + 61, g - 85, 3, 6)), (180, 220, 240))
    # The anti-shark cannon, pointed up, its balls stacked.
    cx = 1190
    c.put(c.mask(lambda p: p.line([(cx - 20, g - 22), (cx + 26, g - 92)], 22)), IRON)
    c.put(c.mask(lambda p: p.ellipse(cx + 27, g - 93, 12, 12)), TAR)
    c.put(c.mask(lambda p: (p.rect(cx - 44, g - 26, cx + 20, g - 6), p.ellipse(cx - 32, g - 8, 9), p.ellipse(cx + 8, g - 8, 9))), PLANK_DARK)
    c.put(c.mask(lambda p: [p.ellipse(x, y, 8) for x, y in ((1110, g - 8), (1128, g - 8), (1119, g - 22))]), IRON)
    for x in (300, 470, 494):
        barrel(c, x, g)


PIECES: Dict[str, Piece] = {
    "sky_lookout_deck": Piece((0, 190, W, 768), deck),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
