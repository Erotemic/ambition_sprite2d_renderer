"""Zeno's Aqueduct (`math_zeno_aqueduct`, Math dimension): out of town, the
town's aqueduct goes on west over a valley to the dam of its reservoir.

Drawn in the room's coordinates (`_district_props`) on the numbers of
`specs/math_town/make_specs.py`: the deck (y 560, the street's), the valley
(y 832), the dam (x 1856..1920), the reservoir's surface (y 624) and The
Limit, its island (x 176..560, top y 600).

- `math_zeno_aqueduct`: the deck on piers that stand half as far apart each
  time toward the dam, each thinner than the last, so the arches close up
  into a comb against it; the dam with its sluice; the ladder up the first
  pier from the valley.
- `math_zeno_reservoir`: the water behind the dam, reeds, a moored rowboat,
  and The Limit: a rock with a little round temple on it.

The town's stone and arches (`math_town_terraces`). Animations: ``idle``,
1 frame each. No drop shadows.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .math_town_terraces import AIR, PAL, WALK, ashlar, vines, walk_line

DECK, FLOOR = 560, 832
DECK_H, BAND_H = 16, 32
DAM_X = 1920
DAM_W = 64
PIERS = [DAM_X + (3200 - DAM_X) / 2**k for k in range(12)]
WATER_TOP = 624
ISLAND = (176, 560, 600)
LADDER_X = 3200 - 16 - 96
STONE = (232, 226, 210)
WATER = (70, 130, 170)


def pier_width(k: int) -> float:
    """The `k`th pier from town: each thinner than the last."""
    return max(2.0, 28.0 * 0.72**k)


def zeno_aqueduct(c, k):
    """The deck, its closing piers and arches, the dam and the ladder."""
    via = c.mask(box(DAM_X, DECK, 3200, DECK + DECK_H))
    # Each pier, and the arch from it to the next one toward the dam.
    for i in range(len(PIERS) - 1):
        east, west = PIERS[i], PIERS[i + 1]
        pw = pier_width(i)
        via = np.maximum(via, c.mask(box(east - pw, DECK + DECK_H, east, FLOOR)))
        span = east - pw - west
        if span <= 1:
            continue
        band = c.mask(box(west, DECK + DECK_H, east - pw, DECK + DECK_H + BAND_H))
        rx = span / 2
        arch = c.mask(lambda p: p.ellipse(west + rx, DECK + DECK_H + BAND_H, rx, BAND_H - 5)) * (c.y > DECK + DECK_H + 4)
        via = np.maximum(via, np.clip(band - arch, 0, 1))
        # A second tier half way down, as a valley's aqueduct has; it closes
        # up with the rest.
        mid = DECK + DECK_H + (FLOOR - DECK - DECK_H) * 0.46
        band2 = c.mask(box(west, mid, east - pw, mid + 24))
        arch2 = c.mask(lambda p: p.ellipse(west + rx, mid + 24, rx, 19)) * (c.y > mid + 4)
        via = np.maximum(via, np.clip(band2 - arch2, 0, 1))
    ashlar(c, via, STONE, course=12, length=22, salt=91)
    walk_line(c, DAM_X - DAM_W, 3200, DECK, STONE)
    c.put(c.mask(box(DAM_X, DECK + DECK_H - 2, 3200, DECK + DECK_H)), scale(STONE, 0.82))
    c.tint(via, AIR, 0.06)
    # The water in its channel, glinting over the coping.
    c.put(c.mask(box(DAM_X, DECK - 3, 3200, DECK - 1)), mix(WATER, WALK, 0.5), 0.7)
    vines(c, PIERS[1] - 8, DECK + DECK_H + BAND_H, 120, "zeno_v1")
    vines(c, PIERS[3] - 4, DECK + DECK_H + BAND_H, 70, "zeno_v2")
    # The dam: a battered wall of big blocks, the reservoir's side to the
    # west, a sluice gate with water spilling through it.
    dam = c.mask(lambda p: p.poly([(DAM_X - DAM_W, DECK), (DAM_X, DECK), (DAM_X + 6, FLOOR), (DAM_X - DAM_W - 6, FLOOR)]))
    ashlar(c, dam, scale(STONE, 0.92), course=18, length=30, salt=93)
    gx = DAM_X - DAM_W / 2
    c.put(c.mask(box(gx - 12, FLOOR - 70, gx + 12, FLOOR - 30)), (90, 70, 52))
    c.put(c.mask(lambda p: [p.rect(gx - 12, y, gx + 12, y + 1.4) for y in (FLOOR - 62, FLOOR - 50, FLOOR - 38)]), (60, 46, 34))
    c.put(c.mask(lambda p: (p.rect(gx - 1.5, DECK - 30, gx + 1.5, FLOOR - 70), p.ring(gx, DECK - 34, 7, 1.6))), PAL["iron"])
    spill = c.mask(lambda p: p.poly([(gx - 10, FLOOR - 30), (gx + 10, FLOOR - 30), (gx + 22, FLOOR), (gx - 4, FLOOR)]))
    c.put(spill, mix(WATER, WALK, 0.35), 0.8)
    c.put(c.mask(lambda p: [p.line([(gx - 6 + i * 5, FLOOR - 28), (gx + i * 6, FLOOR - 2)], 0.8) for i in range(4)]), WALK, 0.6)
    # The ladder up the first pier from the valley.
    for side in (4, 28):
        c.put(c.mask(box(LADDER_X + side - 2, DECK - 16, LADDER_X + side + 2, FLOOR)), (110, 80, 56))
    c.put(c.mask(lambda p: [p.rect(LADDER_X + 4, y, LADDER_X + 28, y + 3) for y in np.arange(DECK + 4, FLOOR, 20)]), (140, 104, 72))
    # Milestones on the deck's coping: one cut fraction per pier, smaller
    # each time (the signs over them say the words).
    for i, x in enumerate(PIERS[1:7], start=1):
        r = max(1.5, 7.0 * 0.8**i)
        c.put(c.mask(lambda p: p.ellipse(x - pier_width(i) / 2, DECK + DECK_H / 2, r)), mix(STONE, (120, 100, 80), 0.5))


def zeno_reservoir(c, k):
    """The reservoir behind the dam, and The Limit."""
    x1 = DAM_X - DAM_W
    water = c.mask(box(16, WATER_TOP, x1, FLOOR))
    c.paint(water, c.ramp([(WATER_TOP, (110, 170, 200)), (FLOOR, (30, 70, 110))]), 0.85)
    ripples = c.mask(lambda p: [p.rect(x, WATER_TOP + 6 + (i % 5) * 9, x + 40 + (i * 13) % 30, WATER_TOP + 7.2 + (i % 5) * 9) for i, x in enumerate(np.arange(40, x1 - 60, 73))])
    c.put(ripples, WALK, 0.45)
    c.put(c.mask(box(16, WATER_TOP, x1, WATER_TOP + 1.5)), WALK, 0.6)
    # The Limit: a rock with a little round temple of six columns.
    ix0, ix1, top = ISLAND
    rock = c.mask(lambda p: p.poly([(ix0 - 20, FLOOR), (ix0, top + 4), (ix0 + 30, top), (ix1 - 30, top), (ix1, top + 6), (ix1 + 24, FLOOR)]))
    c.put(rock, (150, 140, 124))
    c.tone(rock * (c.noise("limit_rock", 12, 6, 3) - 0.5), 0.35)
    walk_line(c, ix0, ix1, top, (190, 180, 160))
    cx = (ix0 + ix1) / 2
    base, cap = top - 8, top - 130
    c.put(c.mask(box(cx - 90, base, cx + 90, top)), STONE)
    walk_line(c, cx - 90, cx + 90, base, STONE)
    cols = c.mask(lambda p: [p.rect(x - 5, cap + 18, x + 5, base) for x in np.linspace(cx - 76, cx + 76, 6)])
    ashlar(c, cols, WALK, course=8, length=10, salt=95)
    c.tone(cols * np.clip(np.sin((c.x - cx) / 12.0), -1, 1), -0.12)
    c.put(c.mask(box(cx - 92, cap + 8, cx + 92, cap + 18)), STONE)
    dome = c.mask(lambda p: p.ellipse(cx, cap + 8, 92, 46)) * (c.y < cap + 8)
    c.put(dome, (176, 100, 72))
    c.tone(dome * np.clip((cx - c.x) / 92, -1, 1), 0.15)
    c.put(c.mask(lambda p: (p.rect(cx - 1, cap - 52, cx + 1, cap - 38), p.ellipse(cx, cap - 54, 3.2))), PAL["brass"])
    # An infinity sign on the frieze, and reeds round the rock.
    inf = [(cx + 16 * math.cos(t), cap + 13 + 5 * math.sin(2 * t)) for t in np.linspace(0, math.tau, 60)]
    c.put(c.mask(lambda p: p.line(inf, 1.2)), (120, 100, 80))
    rng = c.rand("reeds")
    c.put(c.mask(lambda p: [p.line([(x, WATER_TOP + 8), (x + rng.uniform(-4, 4), WATER_TOP - rng.uniform(16, 34))], 1.1) for x in list(np.arange(ix0 - 60, ix0 - 4, 7)) + list(np.arange(ix1 + 6, ix1 + 70, 8))]), (90, 130, 70))
    # A rowboat moored by the dam.
    bx = x1 - 160
    hull = c.mask(lambda p: p.poly([(bx, WATER_TOP - 10), (bx + 90, WATER_TOP - 10), (bx + 78, WATER_TOP + 6), (bx + 10, WATER_TOP + 6)]))
    c.put(hull, (120, 76, 50))
    c.put(c.mask(lambda p: p.line([(bx + 2, WATER_TOP - 10), (bx + 88, WATER_TOP - 10)], 2.2)), (176, 130, 84))
    c.put(c.mask(lambda p: p.line(list(zip(np.linspace(bx + 90, x1, 12), WATER_TOP - 12 + 6 * np.sin(np.linspace(0, math.pi, 12)))), 0.8)), (176, 146, 98))


PIECES: Dict[str, Piece] = {
    "math_zeno_aqueduct": Piece((DAM_X - 80, DECK - 200, 3200, FLOOR), zeno_aqueduct),
    "math_zeno_reservoir": Piece((0, ISLAND[2] - 200, DAM_X - DAM_W + 4, FLOOR), zeno_reservoir),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
