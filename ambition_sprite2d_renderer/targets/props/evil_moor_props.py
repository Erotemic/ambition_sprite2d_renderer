"""The Searchlight Moor (`evil_searchlight_moor`, Evil dimension): out of
town, west of the gate forest, under Castle Godwin's searchlights.

Drawn in the room's coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/evil_moor/make_specs.py`: the ground (y 656),
the bog (x 600..1100, its water from y 640), the watchtower's landings, the
fallen statue's back (y 600).

- `moor_watchtower`: a ruined watchtower of black timber, its landings the
  room's ledges, a searchlight on top throwing a beam.
- `moor_statue`: the castle's founder in bronze, toppled on his face off his
  plinth, his arm on the ground still pointing; his back is walked on.
- `moor_wire`: barbed wire on stakes along the moor.
- `moor_bog`: the bog's murky water, reeds, a drowned cart, mist.

Near-black under the red sky, with a red rim; the searchlight's beam is the
one cold light. Animations: ``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .eureka_props import edge_line
from .evil_forest_props import NEAR_BLACK, PAL, RIM, rim

FLOOR = 656
TOWER_LANDINGS = ((1500, 1620, 560), (1540, 1660, 464), (1500, 1620, 368), (1520, 1680, 272))
STATUE_BACK = (1880, 2200, 600)
BOG = (600, 1100, 640)
BRONZE = (70, 60, 44)
TIMBER = (34, 26, 24)
BEAM = (200, 220, 255)


def watchtower(c, k):
    g = FLOOR
    legs = [(1508, g), (1512, 250), (1668, 250), (1672, g)]
    c.put(c.mask(lambda p: (p.line([legs[0], legs[1]], 8), p.line([legs[3], legs[2]], 8),
                            [p.line([(1510, y), (1670, y + 90)], 3) for y in range(300, g - 90, 90)],
                            [p.line([(1670, y), (1510, y + 90)], 3) for y in range(300, g - 90, 90)])), TIMBER)
    for x0, x1, y in TOWER_LANDINGS:
        c.put(c.mask(box(x0, y, x1, y + 10)), TIMBER)
        edge_line(c, x0, x1, y, (90, 60, 50), 4)
    # The hut on top: planks with gaps (the sky through them), a window lit
    # red, its roof half gone.
    hx0, hx1 = 1520, 1680
    rng = c.rand("hut")
    planks = [(x, x + rng.uniform(12, 18), 272 - rng.uniform(54, 66)) for x in np.arange(hx0, hx1 - 8, 20)]
    hut = c.mask(lambda p: [p.rect(x, top, xr, 272) for x, xr, top in planks])
    c.put(hut, TIMBER)
    c.tone(hut * (c.noise("hut_grain", 4, 1, 2) - 0.5), 0.3)
    c.put(c.mask(lambda p: (p.rect(hx0, 214, hx0 + 6, 272), p.rect(hx1 - 6, 210, hx1, 272), p.rect(hx0, 236, hx1, 240))), NEAR_BLACK)
    win = c.mask(box(1610, 222, 1646, 248))
    c.put(win, (150, 30, 24))
    c.light(win, (255, 90, 50), 0.5)
    c.put(c.mask(lambda p: (p.rect(1626, 222, 1629, 248), p.rect(1610, 233, 1646, 236))), NEAR_BLACK)
    c.put(c.mask(lambda p: (p.line([(hx0 - 8, 214), (1580, 198), (1590, 202)], 5), p.line([(1640, 196), (hx1 + 10, 210)], 5),
                            p.line([(1596, 204), (1614, 226)], 4))), TIMBER)
    rim(c, hut, 0.5)
    sx, sy = 1600, 196
    c.put(c.mask(lambda p: (p.rect(sx - 4, sy, sx + 4, 214), p.ellipse(sx, sy - 6, 16, 12))), (50, 50, 56))
    c.put(c.mask(lambda p: p.ellipse(sx - 10, sy - 8, 6, 8)), (240, 250, 255))
    beam = c.mask(lambda p: p.poly([(sx - 12, sy - 14), (sx - 6, sy - 2), (sx - 300, 40), (sx - 380, 0)]), blur=8)
    c.put(beam, BEAM, 0.22)


def statue(c, k):
    g = FLOOR
    x0, x1, back = STATUE_BACK
    # The plinth he fell off, cracked, a plaque on it.
    plinth = c.mask(lambda p: p.poly([(x1 + 14, g), (x1 + 80, g), (x1 + 76, g - 86), (x1 + 18, g - 92)]))
    c.put(plinth, (64, 56, 62))
    c.tone(plinth * (c.noise("plinth", 8, 2, 2) - 0.5), 0.3)
    c.put(c.mask(lambda p: p.line([(x1 + 40, g - 90), (x1 + 50, g - 60), (x1 + 44, g - 40)], 1.6)), (34, 30, 34))
    c.put(c.mask(box(x1 + 30, g - 52, x1 + 66, g - 34)), (150, 120, 60))
    # Face down along the ground, head west: the back of his head, shoulders,
    # the coat over his back (walked on), its tails, legs, his boot heels up.
    figure = c.mask(lambda p: (
        p.ellipse(x0 - 14, g - 24, 26, 24),
        p.poly([(x0 - 6, g), (x0 + 2, back + 12), (x0 + 30, back + 1), (x0 + 60, back), (x0 + 180, back), (x0 + 200, back + 2),
                (x0 + 214, back + 4), (x1 - 10, back + 8), (x1, back + 14), (x1, g)]),
        p.poly([(x1 - 8, g - 8), (x1 - 6, back - 14), (x1 + 14, back - 16), (x1 + 16, g - 6)]),
        p.poly([(x1 - 8, g - 22), (x1 - 6, back + 6), (x1 + 12, back + 4), (x1 + 14, g - 20)])))
    c.put(figure, BRONZE)
    c.tone(figure * np.clip((back + 30 - c.y) / 30, 0, 1), 0.25)
    c.tone(figure * (c.noise("bronze", 10, 3, 2) - 0.5), 0.25)
    # The coat's seam and belt, its tails over the legs, the boots' soles.
    dark = (44, 38, 26)
    c.put(c.mask(lambda p: (p.line([(x0 + 24, back + 6), (x0 + 180, back + 6)], 1.2), p.rect(x0 + 150, back, x0 + 160, g - 6),
                            p.poly([(x0 + 160, back + 2), (x0 + 236, back + 10), (x0 + 228, back + 30), (x0 + 160, back + 22)]),
                            p.line([(x0 + 236, back + 24), (x1 - 8, back + 26)], 1.2))), dark)
    c.put(c.mask(lambda p: (p.rect(x1 + 10, back - 16, x1 + 16, g - 6), p.line([(x0 - 30, g - 34), (x0 - 4, g - 44)], 1.2))), dark)
    # Verdigris run down his sides.
    rng = c.rand("verdigris")
    c.put(c.mask(lambda p: [p.line([(x, back + 4), (x + rng.uniform(-2, 2), back + rng.uniform(20, 50))], rng.uniform(2, 5)) for x in [rng.uniform(x0, x1) for _ in range(14)]], blur=1.5) * figure,
          (70, 130, 104), 0.55)
    # The arm out ahead of him on the ground, still pointing (west, at the castle's enemies).
    arm = [(x0 + 10, g - 16), (x0 - 50, g - 12), (x0 - 90, g - 10)]
    c.put(c.mask(lambda p: (p.line(arm, 11), p.ellipse(x0 - 96, g - 10, 9, 7))), BRONZE)
    c.put(c.mask(lambda p: p.line([(x0 - 100, g - 12), (x0 - 122, g - 13)], 3.2)), BRONZE)
    c.put(c.mask(lambda p: p.ellipse(x0 - 60, g - 13, 30, 2)), (130, 110, 80), 0.6)
    edge_line(c, x0 + 10, x1 - 10, back, (130, 110, 80), 3)
    rim(c, figure, 0.5)


def wire(c, k):
    g = FLOOR
    for xa, xb in ((360, 560), (1150, 1460)):
        stakes = list(np.arange(xa, xb + 1, 60))
        c.put(c.mask(lambda p: [p.line([(x, g), (x + 4, g - 44)], 3) for x in stakes]), TIMBER)
        for h in (14, 28, 40):
            pts = [(x + 4 * h / 44, g - h + 3 * math.sin(i)) for i, x in enumerate(np.linspace(xa, xb, 40))]
            c.put(c.mask(lambda p: p.line(pts, 1.0)), (90, 86, 90))
            c.put(c.mask(lambda p: [p.line([(x - 3, y - 3), (x + 3, y + 3)], 0.8) for x, y in pts[::3]] + [p.line([(x + 3, y - 3), (x - 3, y + 3)], 0.8) for x, y in pts[::3]]), (110, 106, 110))


def bog(c, k):
    x0, x1, top = BOG
    rng = c.rand("reeds")
    reeds = [x for x in list(np.arange(x0 - 30, x0 + 40, 6)) + list(np.arange(x1 - 40, x1 + 30, 6))]
    c.put(c.mask(lambda p: [p.line([(x, FLOOR + 10), (x + rng.uniform(-6, 6), FLOOR - rng.uniform(20, 46))], 1.4) for x in reeds]), (40, 46, 34))
    c.put(c.mask(lambda p: [p.ellipse(x + rng.uniform(-6, 6), FLOOR - rng.uniform(30, 46), 2, 6) for x in reeds[::3]]), (60, 40, 30))
    # The drowned cart: a wheel and a shaft out of the water.
    c.put(c.mask(lambda p: (p.ring(860, top + 4, 24, 3), [p.line([(860, top + 4), (860 + 24 * math.cos(a), top + 4 + 24 * math.sin(a))], 1.6) for a in np.linspace(math.pi, 2 * math.pi, 5)])) * (c.y < top + 8), TIMBER)
    c.put(c.mask(lambda p: p.line([(900, top + 6), (960, top - 30)], 4)), TIMBER)
    # The water, murky (the room's water is the murky kind, and has no
    # picture of its own): brown-green, scum on it, a bubble or two.
    water = c.mask(box(x0, top, x1, 720))
    c.put(water, (44, 40, 26), 0.88)
    c.tone(water * np.clip((c.y - top) / 60, 0, 1), -0.4)
    edge_line(c, x0, x1, top, (96, 96, 60), 2)
    c.put(c.mask(lambda p: [p.ellipse(rng.uniform(x0 + 20, x1 - 20), top + 2, rng.uniform(10, 30), 2.5) for _ in range(9)]), (80, 96, 44), 0.8)
    c.put(c.mask(lambda p: [p.ring(x, top - 2, 3, 0.8) for x in (700, 1010, 1040)]), (120, 120, 80), 0.8)
    for _ in range(10):
        fx, fw = rng.uniform(x0, x1), rng.uniform(40, 120)
        c.put(c.mask(lambda p: p.ellipse(fx, top - 4, fw, 10), blur=8), (150, 140, 150), 0.14)


PIECES: Dict[str, Piece] = {
    "moor_watchtower": Piece((1180, 0, 1700, FLOOR), watchtower),
    "moor_statue": Piece((1740, 500, 2300, FLOOR), statue),
    "moor_wire": Piece((200, 600, 1480, FLOOR), wire),
    "moor_bog": Piece((560, 580, 1140, 720), bog),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
