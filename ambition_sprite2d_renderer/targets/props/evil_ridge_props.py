"""The Searchlight Ridge (`evil_searchlight_ridge`, the Evil dimension): high
over the moor and the allotments, the line of searchlights the moor is named
for, reached up the moor's watchtower; at its west end a gap in the ridge
drops onto the allotments' greenhouse roof.

Drawn in room coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/evil_moor/make_specs.py` (`ridge`): the
ridge's ground (y 480 down to the room's foot at 544), the gap over the
greenhouse (x 70..450), the hole the watchtower's top comes up through
(x 3100..3220).

- `ridge_west`: the broken end of the ridge over the gap, its edge fallen
  away; barbed wire; a searchlight emplacement, its beam sweeping the sky.
- `ridge_east`: the sentry hut; two more searchlights, their beams; a line
  of cable on poles between them; the top of the watchtower coming up
  through the ridge.

Silhouettes against the red sky, lit on their left by it, as the moor.
Animations: ``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .evil_forest_props import NEAR_BLACK, PAL, rim

W, G, FOOT = 3600, 480, 544
GAP = (70, 450)
TOWER = (3100, 3220)
ROCK = (46, 34, 38)
ROCK_LIGHT = (90, 60, 62)
IRON = (40, 36, 40)
LAMP = (255, 236, 190)
BEAM = (255, 240, 200)
WIRE = (110, 100, 104)
TIMBER = (34, 26, 24)
WINDOW = (255, 170, 80)


def ground(c, x0, x1):
    """The ridge's rock from `x0` to `x1`, its crest at G."""
    m = c.mask(lambda p: p.poly([(x0, FOOT), (x0, G + 4), *[(x, G + 3 * math.sin(x / 37.0)) for x in np.linspace(x0, x1, 40)], (x1, G + 4), (x1, FOOT)]))
    c.put(m, ROCK)
    c.tone(m * (c.noise(("ridge", x0), (x1 - x0) / 60, 3, 2) - 0.5), 0.25)
    c.put(c.mask(lambda p: p.line([(x, G + 3 * math.sin(x / 37.0)) for x in np.linspace(x0, x1, 40)], 3)), ROCK_LIGHT)
    rim(c, m, 0.35)


def searchlight(c, x, sweep):
    """A searchlight on its post at `x`, its beam up into the sky at `sweep`
    radians from the vertical."""
    c.put(c.mask(lambda p: (p.rect(x - 4, G - 70, x + 4, G), p.poly([(x - 18, G), (x + 18, G), (x + 8, G - 12), (x - 8, G - 12)]))), IRON)
    c.put(c.mask(lambda p: p.ellipse(x, G - 82, 16, 14)), IRON)
    c.put(c.mask(lambda p: p.ellipse(x + 8 * math.sin(sweep), G - 84 - 8 * math.cos(sweep), 8, 7)), LAMP)
    tip = (x + 700 * math.sin(sweep), G - 84 - 700 * math.cos(sweep))
    side = (math.cos(sweep) * 60, math.sin(sweep) * 60)
    # The beam: a translucent fill over the sky (a light brightens only what
    # is drawn, and the sky is the parallax behind).
    c.put(c.mask(lambda p: p.poly([(x - 6, G - 84), (x + 6, G - 84), (tip[0] + side[0], tip[1] + side[1]), (tip[0] - side[0], tip[1] - side[1])]), blur=8), BEAM, 0.16)


def wire(c, x0, x1, y):
    c.put(c.mask(lambda p: [p.ring(x, y - 12, 12, 1.2) for x in np.arange(x0, x1, 14)]), WIRE)
    c.put(c.mask(lambda p: [p.rect(x, y - 30, x + 3, y) for x in np.arange(x0, x1, 120)]), TIMBER)


def west(c, k):
    g0, g1 = GAP
    # The broken end over the gap: the rock falls away to the west.
    c.put(c.mask(lambda p: p.poly([(16, FOOT), (16, G + 30), (g0, G + 60), (g0 + 20, FOOT)])), ROCK)
    ground(c, g1, 1800)
    c.put(c.mask(lambda p: p.poly([(g1, G), (g1 - 30, G + 30), (g1 - 10, FOOT), (g1 + 10, FOOT)])), ROCK)
    wire(c, g1 + 40, g1 + 400, G)
    searchlight(c, 900, -0.5)
    wire(c, 1200, 1700, G)


def east(c, k):
    t0, t1 = TOWER
    ground(c, 1800, t0)
    ground(c, t1, W - 16)
    # The top of the watchtower, coming up through the ridge: its posts and
    # its ladder (the engine draws the ladder; the posts are here).
    c.put(c.mask(lambda p: [p.rect(x, G - 40, x + 8, FOOT) for x in (t0, t1 - 8)]), TIMBER)
    c.put(c.mask(lambda p: p.rect(t0 - 6, G - 44, t1 + 6, G - 38)), TIMBER)
    # The sentry hut: planks, a lit window, a tin roof.
    h0, h1 = 2300, 2460
    hut = c.mask(box(h0, G - 110, h1, G))
    c.put(hut, TIMBER)
    c.put(hut * c.mask(lambda p: [p.rect(x, G - 110, x + 1.4, G) for x in range(h0, h1, 12)]), NEAR_BLACK, 0.6)
    c.put(c.mask(lambda p: p.poly([(h0 - 14, G - 106), (h1 + 14, G - 120), (h1 + 14, G - 112), (h0 - 14, G - 98)])), IRON)
    c.put(c.mask(box(h0 + 30, G - 80, h0 + 70, G - 50)), WINDOW)
    c.light(c.mask(lambda p: p.ellipse(h0 + 50, G - 65, 50, 30), blur=10), WINDOW, 0.25)
    rim(c, hut, 0.4)
    # Two more searchlights, and the cable on poles between them.
    searchlight(c, 2000, 0.35)
    searchlight(c, 2800, -0.25)
    c.put(c.mask(lambda p: [p.rect(x, G - 120, x + 4, G) for x in (2150, 2600)]), TIMBER)
    c.put(c.mask(lambda p: p.line([(2000, G - 90), (2152, G - 116), (2380, G - 100), (2602, G - 116), (2800, G - 90)], 1.4)), NEAR_BLACK)
    wire(c, 3260, 3560, G)


PIECES: Dict[str, Piece] = {
    "ridge_west": Piece((16, 0, 1800, FOOT), west),
    "ridge_east": Piece((1800, 0, W - 16, FOOT), east),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
