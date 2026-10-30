"""The Bamboo Pass (`ninja_bamboo_pass`, PvN dimension): out of the Ninja
Village, east of the cedar forest: the Shadow Clan's sparring ground, where
everyone who passes is an opponent.

Drawn in room coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/ninja_pass/make_specs.py`: the ground (y
832), the gorge (x 900..1400, its stream from y 880, its bed at 944), the
rope bridge over it (y 832), the stepping stone out of it (x 1340..1390,
y 880), the bamboo lookout's platforms (x 1540..1700: y 704 and 576).

- `pass_bamboo`: a grove of bamboo, culms in three greens, leaves in
  sprays.
- `pass_bridge`: the gorge's rock walls, the stream at its foot, the rope
  bridge of planks across it.
- `pass_lookout`: a lookout of lashed bamboo, two platforms (the room's
  ladder beside them is the engine's Climbable), a conch on a hook.
- `pass_falls`: a small fall over mossed rock into a pool at the east wall,
  and by the path a row of stone jizo with red bibs.
- `pass_scoreboard`: the referee's tally board by the way in: the day's
  bouts counted in 正, the visitors' column a nought.

Everyday mountain things, drawn with care: no costume and no joke at the
culture's cost. Animations: ``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .eureka_props import Batch, edge_line
from .ninja_village_props import MOSS, PAL, STONE, TIMBER, VERMILION

W, FLOOR = 2400, 832
GORGE = (900, 1400)
STREAM, BED = 880, 944
STEP = (1340, 1390, 880)
LOOKOUT = (1540, 1700, (704, 576))
BAMBOO = ((96, 140, 70), (122, 160, 84), (78, 116, 60))
LEAF = (90, 138, 72)
ROCK = (104, 104, 98)
ROCK_DARK = (66, 66, 62)
WATER = (120, 170, 190)
ROPE = (190, 160, 110)
PLANK = (150, 112, 74)


def culm(b, x, top, w, colour):
    b.add(colour, 1.0, box(x - w / 2, top, x + w / 2, FLOOR))
    b.add(scale(colour, 0.7), 1.0, lambda p, x=x, w=w, top=top: [p.rect(x - w / 2 - 0.5, y, x + w / 2 + 0.5, y + 1.6) for y in np.arange(top + 30, FLOOR, 42)])
    b.add(mix(colour, (255, 255, 230), 0.3), 1.0, box(x - w / 2, top, x - w / 2 + 1.2, FLOOR))


def bamboo(c, k):
    rng = c.rand("bamboo")
    b = Batch(c)
    xs = sorted(rng.uniform(20, 860) for _ in range(70))
    for x in xs:
        culm(b, x, rng.uniform(310, 470), rng.uniform(7, 13), BAMBOO[int(rng.uniform(0, 3))])
    b.draw()
    sprays = []
    for x in xs:
        for _ in range(6):
            sx, sy = x + rng.uniform(-12, 12), rng.uniform(310, 700)
            sprays += [[(sx, sy), (sx + d * rng.uniform(14, 26), sy + rng.uniform(4, 14))] for d in (-1, 1)]
    c.put(c.mask(lambda p: [p.line(s, 3.4) for s in sprays]), LEAF)
    c.put(c.mask(lambda p: [p.line(s, 1.2) for s in sprays[::3]]), mix(LEAF, (255, 255, 220), 0.3))


def bridge(c, k):
    g0, g1 = GORGE
    # The gorge's walls of rock, the stream at its foot.
    for x0, x1 in ((g0 - 20, g0 + 16), (g1 - 16, g1 + 20)):
        wall = c.mask(lambda p: p.poly([(x0, FLOOR), (x1, FLOOR), (x1 + (8 if x0 < g0 else -8), BED + 16), (x0, BED + 16)]))
        c.put(wall, ROCK)
        c.tone(wall * (c.noise(("gorge", x0), 4, 10, 3) - 0.5), 0.35)
    c.put(c.mask(box(g0 + 10, FLOOR, g1 - 10, STREAM)), (40, 46, 42), 0.6)
    water = c.mask(box(g0 + 10, STREAM, g1 - 10, BED))
    c.put(water, WATER, 0.85)
    c.tone(water * np.clip((c.y - STREAM) / 60, 0, 1), -0.35)
    c.put(c.mask(lambda p: [p.ellipse(x, STREAM + 1, 16, 1.2) for x in range(g0 + 40, g1 - 30, 70)]), (230, 240, 245), 0.7)
    s0, s1, sy = STEP
    c.put(c.mask(lambda p: p.ellipse((s0 + s1) / 2, sy + 8, (s1 - s0) / 2 + 4, 10)), ROCK)
    c.put(c.mask(lambda p: p.ellipse((s0 + s1) / 2, sy + 2, (s1 - s0) / 2, 3)), MOSS)
    # The rope bridge: planks hung from two ropes, posts at each end.
    planks = c.mask(lambda p: [p.rect(x, FLOOR - 1, x + 14, FLOOR + 5) for x in range(g0 - 10, g1 + 10, 18)])
    c.put(planks, PLANK)
    for x in (g0 - 24, g1 + 18):
        c.put(c.mask(box(x, FLOOR - 52, x + 7, FLOOR)), TIMBER)
    for h in (46, 26):
        pts = [(g0 - 20 + t * (g1 - g0 + 40), FLOOR - h + 10 * math.sin(t * math.pi)) for t in np.linspace(0, 1, 30)]
        c.put(c.mask(lambda p: p.line(pts, 2.0)), ROPE)
    c.put(c.mask(lambda p: [p.line([(x, FLOOR - 26 + 10 * math.sin((x - g0 + 20) / (g1 - g0 + 40) * math.pi)), (x, FLOOR)], 1.0) for x in range(g0, g1, 36)]), ROPE)


def lookout(c, k):
    x0, x1, (low, high) = LOOKOUT
    b = Batch(c)
    for x in (x0 + 6, x1 - 10):
        culm(b, x, high - 60, 8, BAMBOO[0])
    b.draw()
    for y in (low, high):
        c.put(c.mask(box(x0, y, x1, y + 8)), BAMBOO[1])
        c.put(c.mask(lambda p: [p.rect(x, y, x + 1, y + 8) for x in range(x0, x1, 9)]), scale(BAMBOO[1], 0.7))
        edge_line(c, x0, x1, y, BAMBOO[1], 3)
        c.put(c.mask(lambda p: [p.line([(x, y + 8), (x + 6, y + 14)], 1.4) for x in (x0 + 6, x1 - 12)]), ROPE)
    c.put(c.mask(lambda p: (p.line([(x0 + 10, FLOOR), (x1 - 14, low + 8)], 2.4), p.line([(x1 - 14, FLOOR), (x0 + 10, low + 8)], 2.4))), BAMBOO[2])
    c.put(c.mask(lambda p: p.ellipse(x0 + 30, high - 22, 10, 7)), (236, 214, 200))
    c.put(c.mask(lambda p: p.poly([(x0 + 38, high - 26), (x0 + 50, high - 30), (x0 + 46, high - 18)])), (236, 214, 200))
    c.put(c.mask(lambda p: p.ellipse(x0 + 30, high - 22, 4, 3)), (200, 140, 130))


def falls(c, k):
    # The rock the fall comes over, at the east wall.
    rock = c.mask(lambda p: p.poly([(2140, FLOOR), (2170, 520), (2240, 430), (2384, 400), (2384, FLOOR)]))
    c.put(rock, ROCK)
    c.tone(rock * (c.noise("falls_rock", 6, 10, 3) - 0.5), 0.35)
    c.put(rock * np.clip((c.noise("falls_moss", 10, 14, 2) - 0.55) * 4, 0, 1), MOSS)
    fall = c.mask(lambda p: p.poly([(2230, 440), (2290, 430), (2296, FLOOR - 30), (2224, FLOOR - 30)]))
    c.put(fall, WATER, 0.9)
    c.put(fall * c.mask(lambda p: [p.rect(x, 430, x + 1.5, FLOOR - 30) for x in range(2228, 2296, 7)]), (230, 245, 250), 0.6)
    pool = c.mask(lambda p: p.ellipse(2262, FLOOR - 16, 110, 18))
    c.put(pool, WATER, 0.9)
    c.put(c.mask(lambda p: p.ellipse(2262, FLOOR - 26, 70, 8), blur=6), (240, 250, 255), 0.5)
    # Jizo by the path: small stone figures, red bibs, a pebble offering.
    for i, x in enumerate((1900, 1940, 1980)):
        h = 46 - (i % 2) * 6
        body = c.mask(lambda p: (p.poly([(x - 13, FLOOR), (x + 13, FLOOR), (x + 10, FLOOR - h + 14), (x - 10, FLOOR - h + 14)]), p.ellipse(x, FLOOR - h + 10, 10, 11)))
        c.put(body, STONE)
        c.tone(body * np.clip((c.x - x) / 13, -1, 1), -0.2)
        c.put(c.mask(lambda p: p.poly([(x - 11, FLOOR - h + 18), (x + 11, FLOOR - h + 18), (x, FLOOR - h + 34)])), VERMILION)
        c.put(c.mask(lambda p: (p.line([(x - 5, FLOOR - h + 9), (x - 2, FLOOR - h + 10)], 1.0), p.line([(x + 2, FLOOR - h + 10), (x + 5, FLOOR - h + 9)], 1.0))), (80, 80, 76))
    c.put(c.mask(lambda p: [p.ellipse(x, FLOOR - 3, 3, 2.5) for x in (1918, 1924, 1962)]), (170, 168, 160))


def scoreboard(c, k):
    """The referee's tally board by the way in: a board of bamboo slats on
    two posts, the day's bouts counted in 正, the visitors' column
    a nought."""
    x0, x1, top = 214, 286, FLOOR - 96
    c.put(c.mask(lambda p: [p.rect(x, top - 6, x + 5, FLOOR) for x in (x0 + 4, x1 - 9)]), TIMBER)
    board = c.mask(box(x0, top, x1, top + 54))
    c.put(board, (200, 180, 130))
    c.put(board * c.mask(lambda p: [p.rect(x, top, x + 1, top + 54) for x in range(x0 + 6, x1, 6)]), (170, 150, 104))
    c.put(c.mask(lambda p: p.rect(x0 + 44, top + 4, x0 + 45.2, top + 50)), TIMBER)
    # The day's bouts counted in 正, five strokes to the character.
    marks = []
    for g in range(3):
        cx, cy = x0 + 10 + g * 11, top + 8
        marks += [[(cx - 4, cy), (cx + 4, cy)], [(cx, cy), (cx, cy + 12)], [(cx, cy + 6), (cx + 3.5, cy + 6)],
                  [(cx - 3, cy + 5), (cx - 3, cy + 12)], [(cx - 5, cy + 12), (cx + 5, cy + 12)]]
    c.put(c.mask(lambda p: [p.line(m, 1.0) for m in marks]), (30, 26, 24))
    c.put(c.mask(lambda p: p.rect(x0 + 8, top + 34, x0 + 30, top + 36)), VERMILION)
    c.put(c.mask(lambda p: p.ring(x0 + 59, top + 30, 6, 1.4)), (30, 26, 24))


PIECES: Dict[str, Piece] = {
    "pass_scoreboard": Piece((200, FLOOR - 110, 300, FLOOR), scoreboard),
    "pass_bamboo": Piece((0, 300, 880, FLOOR), bamboo),
    "pass_bridge": Piece((870, 770, 1430, 960), bridge),
    "pass_lookout": Piece((1530, 500, 1740, FLOOR), lookout),
    "pass_falls": Piece((1880, 390, W, FLOOR), falls),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
