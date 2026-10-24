"""Scenery of the Ninja Village (gate address SILENT): a Japanese mountain village.

The rooms are `ninja_village_gate_shrine`, `ninja_village_street`,
`ninja_village_dojo` and `ninja_village_forest`
(`tools/ambition_ldtk_tools/specs/ninja_village/make_specs.py`). Each piece
is drawn in its room's coordinates (`_district_props`): where the room places
a walk line, the piece draws the light top edge of what is walked on there.

- The shrine: the stone stair (treads 640, 576, 512) and the wall of the
  terrace (y 448), the torii at the top of the stair, the small shrine on
  the terrace, stone lanterns and the bench of the gate-sick.
- The street: houses of white plaster and dark timber under tiled roofs.
  Each roof's ridge is a walk line (the room's `ROOFS`): the baker's (with
  the ladder up its wall), the weaver's, the tea house, the village dojo
  round its door, the storehouse and the watch house; a notice board.
- The forest: cedars whose low boughs are the room's branches (each 64
  lower than the one before, from y 384), and the gatehouse of the Shadow
  Clan's hall round its door.
- The dojo: its plank walls, the alcove and its scroll, a rack of wooden
  swords, the rank board of name plaques, the exam beam (y 400).

Everyday architecture, drawn with care: no costume and no joke at the
culture's cost. The scroll is brush strokes, not writing. No rings and no
portal: the torii is a shrine gate of the path, not the network's ring.

Animations: ``idle``, 1 frame each.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale

PAL = {
    "stone": (150, 148, 138), "stone_light": (206, 202, 188), "trim": (226, 220, 204), "dark": (30, 32, 38),
    "glass_top": (200, 190, 160), "glass_low": (150, 130, 100), "lamp": (255, 200, 130), "wood": (92, 62, 42),
    "leaf": (64, 104, 66), "iron": (36, 36, 40), "brass": (186, 146, 70), "glaze": (190, 160, 80),
}
PLASTER = (236, 230, 216)
TIMBER = (56, 40, 32)
CEDAR = (122, 82, 54)
CEDAR_LIGHT = (176, 128, 86)
TILE = (68, 76, 88)
TILE_LIGHT = (122, 132, 146)
SHOJI = (236, 226, 196)
INDIGO = (38, 54, 92)
VERMILION = (196, 72, 44)
PAPER = (246, 228, 182)
STONE = (148, 146, 136)
MOSS = (88, 112, 64)
FOLIAGE = (40, 72, 52)
FOLIAGE_LIGHT = (70, 108, 70)
BARK = (92, 56, 40)
MAPLE = (198, 70, 46)


def post(c, x, y0, y1, w=5.0, colour=TIMBER):
    c.put(c.mask(box(x - w / 2, y0, x + w / 2, y1)), colour)
    c.put(c.mask(box(x - w / 2, y0, x - w / 2 + 0.9, y1)), mix(colour, (255, 230, 190), 0.25))


def walk_edge(c, x0, x1, y, colour):
    """The walked top of a thing at `y`: the one light line."""
    c.put(c.mask(box(x0, y, x1, y + 4)), colour)
    c.put(c.mask(box(x0, y, x1, y + 1.2)), mix(colour, (255, 244, 220), 0.55))


def tiled_roof(c, x0, x1, ridge, depth=56, overhang=34, tag="roof"):
    """A tiled roof seen from the street: its ridge (the walk line, x0..x1 at
    `ridge`) and the slope down to the eaves, rows of round tiles, the ridge
    cap with its end tiles turned up."""
    ex0, ex1, eave = x0 - overhang, x1 + overhang, ridge + depth
    m = c.mask(lambda p: p.poly([(x0, ridge), (x1, ridge), (ex1, eave - 4), (ex1 + 6, eave + 2), (ex0 - 6, eave + 2), (ex0, eave - 4)]))
    c.put(m, TILE)
    cols = np.abs(((c.x - ex0) % 6.0) - 3.0) / 3.0
    c.tone(m * (0.5 - cols), 0.3)
    rows = c.mask(lambda p: [p.rect(ex0 - 6, y, ex1 + 6, y + 0.8) for y in np.arange(ridge + 8, eave, 7)])
    c.put(rows * m, scale(TILE, 0.65), 0.8)
    c.tone(m * np.clip((eave - c.y) / depth, 0, 1), 0.18)
    c.put(c.mask(box(ex0 - 6, eave - 1, ex1 + 6, eave + 3)), scale(TILE, 0.55))
    # The ridge cap: the walk line, its two end tiles turned up.
    walk_edge(c, x0 - 4, x1 + 4, ridge, TILE_LIGHT)
    c.put(c.mask(box(x0 - 4, ridge + 4, x1 + 4, ridge + 8)), scale(TILE, 0.8))
    for ex in (x0 - 4, x1 + 4):
        c.put(c.mask(lambda p: p.poly([(ex - 7, ridge + 8), (ex + 7, ridge + 8), (ex + 5, ridge - 6), (ex - 5, ridge - 6)])), scale(TILE, 0.7))
    return eave


def minka(c, k, x0, x1, ridge, ground, tag, front="lattice", depth=56):
    """A house of the street: the roof over a front of dark posts, white
    plaster above and wooden lattice or paper screens below."""
    eave = ridge + depth
    wx0, wx1 = x0 - 10, x1 + 10
    k.wall(wx0, eave, wx1, ground, PLASTER, "plaster", tag=tag)
    beam = eave + (ground - eave) * 0.38
    for x in np.linspace(wx0 + 2, wx1 - 2, max(3, int((wx1 - wx0) / 70) + 1)):
        post(c, x, eave, ground, 6)
    c.put(c.mask(lambda p: (p.rect(wx0, beam - 3, wx1, beam + 3), p.rect(wx0, eave, wx1, eave + 5))), TIMBER)
    c.put(c.mask(box(wx0, ground - 16, wx1, ground)), scale(STONE, 0.8))
    lower = c.mask(box(wx0 + 4, beam + 3, wx1 - 4, ground - 16))
    if front == "lattice":
        c.put(lower, CEDAR)
        c.put(c.mask(lambda p: [p.rect(x, beam + 3, x + 1.4, ground - 16) for x in np.arange(wx0 + 6, wx1 - 4, 4.0)]) * lower, scale(CEDAR, 0.6))
    elif front == "shoji":
        c.put(lower, SHOJI)
        c.put(c.mask(lambda p: ([p.rect(x, beam + 3, x + 1.2, ground - 16) for x in np.arange(wx0 + 6, wx1 - 4, 12.0)],
                                [p.rect(wx0, y, wx1, y + 1.2) for y in np.arange(beam + 12, ground - 16, 14.0)])) * lower, CEDAR, 0.9)
        c.light(lower, PAL["lamp"], 0.25)
    elif front == "storehouse":
        c.put(lower, (54, 56, 62))
        c.put(c.mask(lambda p: [p.line([(x, beam + 3), (x + 12, beam + 15)], 1.2) for x in np.arange(wx0 - 60, wx1, 12)]) * lower, PLASTER, 0.85)
        c.put(c.mask(lambda p: [p.line([(x + 12, beam + 3), (x, beam + 15)], 1.2) for x in np.arange(wx0 - 60, wx1, 12)]) * lower, PLASTER, 0.85)
    # Upper windows: small lattice openings in the plaster.
    for cx in np.arange(wx0 + 40, wx1 - 30, 90):
        c.put(c.mask(box(cx - 12, eave + 18, cx + 12, beam - 12)), TIMBER)
        c.put(c.mask(box(cx - 9, eave + 21, cx + 9, beam - 15)), SHOJI)
        c.put(c.mask(lambda p: [p.rect(x, eave + 21, x + 1, beam - 15) for x in np.arange(cx - 9, cx + 9, 4.5)]), TIMBER)
    tiled_roof(c, x0, x1, ridge, depth, tag=(tag, "roof"))
    return eave, beam


def paper_lantern(c, x, y, colour=PAPER, lit=0.7, r=10):
    """A paper lantern hanging from `y`."""
    c.put(c.mask(lambda p: p.rect(x - 0.5, y - 8, x + 0.5, y)), TIMBER)
    body = c.mask(lambda p: p.ellipse(x, y + r * 1.2, r, r * 1.3))
    c.put(body, colour)
    c.put(c.mask(lambda p: [p.rect(x - r, yy, x + r, yy + 0.6) for yy in np.arange(y + 2, y + r * 2.4, 2.4)]) * body, scale(colour, 0.85), 0.6)
    c.put(c.mask(lambda p: (p.rect(x - r * 0.6, y, x + r * 0.6, y + 1.6), p.rect(x - r * 0.6, y + r * 2.4, x + r * 0.6, y + r * 2.4 + 1.6))), TIMBER)
    c.light(c.mask(lambda p: p.ellipse(x, y + r * 1.2, r * 2.6), blur=6), PAL["lamp"], lit * 0.5)


def noren(c, x0, x1, y, h, colour=INDIGO):
    """A split shop curtain over a doorway."""
    n = max(2, int((x1 - x0) / 14))
    w = (x1 - x0) / n
    c.put(c.mask(box(x0 - 2, y - 2, x1 + 2, y + 1)), TIMBER)
    for i in range(n):
        m = c.mask(box(x0 + i * w + 0.6, y, x0 + (i + 1) * w - 0.6, y + h))
        c.put(m, colour)
        c.tone(m * np.clip((c.y - y) / h, 0, 1), -0.15)
    cx = (x0 + x1) / 2
    c.put(c.mask(lambda p: p.ellipse(cx, y + h * 0.45, min(h, x1 - x0) * 0.18)), PLASTER, 0.9)


def stone_lantern(c, x, ground, h=46):
    """A stone lantern: foot, post, firebox with its window, cap, jewel."""
    s = STONE
    c.put(c.mask(box(x - 9, ground - 6, x + 9, ground)), s)
    c.put(c.mask(box(x - 3.5, ground - h * 0.55, x + 3.5, ground - 6)), s)
    c.put(c.mask(box(x - 8, ground - h * 0.62, x + 8, ground - h * 0.55)), s)
    c.put(c.mask(box(x - 6, ground - h * 0.85, x + 6, ground - h * 0.62)), s)
    c.put(c.mask(box(x - 3, ground - h * 0.8, x + 3, ground - h * 0.68)), mix(PAL["lamp"], (255, 240, 200), 0.3))
    c.put(c.mask(lambda p: p.poly([(x - 13, ground - h * 0.85), (x + 13, ground - h * 0.85), (x + 6, ground - h * 0.97), (x - 6, ground - h * 0.97)])), scale(s, 0.9))
    c.put(c.mask(lambda p: p.ellipse(x, ground - h, 3.2)), s)
    m = c.mask(box(x - 13, ground - h - 3, x + 13, ground))
    c.tone(m * (c.noise(("lantern", x), 4, 6, 2) - 0.5), 0.2)
    c.put(c.mask(lambda p: p.ellipse(x - 4, ground - h * 0.86, 5, 1.6)), MOSS, 0.7)


# ---------------------------------------------------------------------------
# The shrine
# ---------------------------------------------------------------------------

SHRINE_FLOOR, TERRACE = 704, 448


def shrine_stair(c, k):
    """The stone stair (treads at y 640, 576, 512) and the dressed stone wall
    of the terrace (its kerb the walk line, y 448, x 1192..1600)."""
    g = SHRINE_FLOOR
    wall = c.mask(box(1192, TERRACE, 1600, g))
    c.put(wall, scale(STONE, 0.86))
    rng = c.rand("terrace_wall")
    blocks = c.mask(lambda p: [p.rect(x + rng.uniform(0.4, 1.2), y + 0.6, x + rng.uniform(26, 40), y + 15.4)
                               for y in np.arange(TERRACE + 6, g, 16) for x in np.arange(1192 + (y % 32) * 0.7, 1600, 38)])
    c.put(blocks * wall, STONE)
    c.tone(wall * (c.noise("terrace_n", 20, 10, 3) - 0.5), 0.18)
    c.put(c.mask(lambda p: [p.ellipse(rng.uniform(1200, 1590), rng.uniform(TERRACE + 20, g - 6), rng.uniform(6, 16), rng.uniform(2, 4)) for _ in range(14)]), MOSS, 0.6)
    walk_edge(c, 1192, 1600, TERRACE, STONE)
    for i, (sx, top) in enumerate(((960, 640), (1040, 576), (1120, 512))):
        m = c.mask(box(sx, top, sx + 96, g))
        c.put(m, STONE)
        c.tone(m * (c.noise(("step", i), 4, 6, 3) - 0.5), 0.18)
        c.tone(m * np.clip((c.y - top) / (g - top), 0, 1), -0.15)
        walk_edge(c, sx, sx + 96, top, mix(STONE, (230, 226, 210), 0.3))


def torii(c, k):
    """The torii at the top of the stair: two vermilion pillars on black
    feet, the upper lintel with its curve and the tie beam."""
    g = TERRACE
    l, r = 1222, 1318
    top = g - 150
    for x in (l, r):
        c.put(c.mask(box(x - 5, top + 10, x + 5, g)), VERMILION)
        c.put(c.mask(box(x - 5, top + 10, x - 2.5, g)), mix(VERMILION, (255, 220, 190), 0.25))
        c.put(c.mask(box(x - 6.5, g - 14, x + 6.5, g)), (30, 28, 28))
    c.put(c.mask(box(l - 16, top + 30, r + 16, top + 38)), VERMILION)
    c.put(c.mask(box((l + r) / 2 - 4, top + 14, (l + r) / 2 + 4, top + 30)), VERMILION)
    lintel = c.mask(lambda p: p.poly([(l - 30, top - 6), (r + 30, top - 6), (r + 24, top + 4), (l - 24, top + 4)]))
    c.put(lintel, (30, 28, 28))
    c.put(c.mask(lambda p: p.poly([(l - 26, top + 4), (r + 26, top + 4), (r + 20, top + 14), (l - 20, top + 14)])), VERMILION)


def shrine_hall(c, k):
    """The small shrine on the terrace: a cedar hall on a stone base, its
    curved roof, the offering box, the bell and its rope, a sacred rope over
    the front."""
    g = TERRACE
    x0, x1 = 1380, 1570
    c.put(c.mask(box(x0 - 10, g - 14, x1 + 10, g)), STONE)
    walls = c.mask(box(x0, g - 120, x1, g - 14))
    c.put(walls, CEDAR)
    c.tone(walls * (c.noise("hall_grain", 8, 30, 2) - 0.5), 0.25)
    for x in np.linspace(x0 + 3, x1 - 3, 5):
        post(c, x, g - 120, g - 14, 7, scale(CEDAR, 0.7))
    c.put(c.mask(box(x0 + 50, g - 96, x1 - 50, g - 14)), SHOJI)
    c.put(c.mask(lambda p: [p.rect(x, g - 96, x + 1, g - 14) for x in np.arange(x0 + 50, x1 - 50, 11)]), CEDAR, 0.9)
    # The roof: a deep curve with the eaves turned up.
    roof = c.mask(lambda p: p.poly([(x0 - 34, g - 116), (x0 + 10, g - 150), (x1 - 10, g - 150), (x1 + 34, g - 116), (x1 + 42, g - 124), (x1 + 30, g - 110), (x0 - 30, g - 110), (x0 - 42, g - 124)]))
    c.put(roof, scale(TILE, 0.9))
    c.tone(roof * np.clip((g - 110 - c.y) / 40, 0, 1), 0.2)
    c.put(c.mask(box(x0 + 6, g - 156, x1 - 6, g - 148)), TILE_LIGHT)
    # The sacred rope with its paper streamers.
    rope = [(x0 + 10 + (x1 - x0 - 20) * t, g - 104 + 10 * math.sin(math.pi * t)) for t in np.linspace(0, 1, 30)]
    c.put(c.mask(lambda p: p.line(rope, 3.2)), (214, 196, 140))
    for t in (0.25, 0.5, 0.75):
        x, y = rope[int(t * 29)]
        c.put(c.mask(lambda p: p.line([(x, y + 2), (x + 3, y + 7), (x - 2, y + 12), (x + 2, y + 18)], 1.6)), (250, 250, 246))
    # The bell and its rope, the offering box.
    cx = (x0 + x1) / 2
    c.put(c.mask(lambda p: p.ellipse(cx, g - 88, 6)), PAL["brass"])
    c.put(c.mask(lambda p: p.line([(cx, g - 82), (cx + 1, g - 40)], 3)), (220, 200, 150))
    c.put(c.mask(lambda p: p.line([(cx + 1, g - 40), (cx + 1, g - 34)], 4)), VERMILION)
    box_m = c.mask(box(cx - 26, g - 34, cx + 26, g - 14))
    c.put(box_m, scale(CEDAR, 0.75))
    c.put(c.mask(lambda p: [p.rect(x, g - 34, x + 1.6, g - 26) for x in np.arange(cx - 24, cx + 24, 4)]), scale(CEDAR, 0.45))


def shrine_small_things(c, k):
    """Stone lanterns by the path and the bench of the gate-sick (x 760..840)."""
    g = SHRINE_FLOOR
    stone_lantern(c, 548, g)
    stone_lantern(c, 924, g)
    bench = c.mask(lambda p: (p.rect(750, g - 22, 850, g - 17), p.rect(756, g - 17, 761, g), p.rect(839, g - 17, 844, g)))
    c.put(bench, CEDAR)
    c.put(c.mask(box(750, g - 22, 850, g - 21)), CEDAR_LIGHT)
    # A maple by the bench, its leaves turning.
    c.put(c.mask(lambda p: p.line([(880, g), (878, g - 70), (868, g - 110)], 7)), BARK)
    c.put(c.mask(lambda p: p.line([(878, g - 70), (900, g - 104)], 4)), BARK)
    rng = c.rand("maple")
    for _ in range(60):
        x, y = rng.uniform(840, 930), rng.uniform(g - 150, g - 90)
        c.put(c.mask(lambda p: p.ellipse(x, y, rng.uniform(4, 9), rng.uniform(3, 6))), mix(MAPLE, (230, 140, 60), rng.uniform(0, 0.5)))


# ---------------------------------------------------------------------------
# The street
# ---------------------------------------------------------------------------

STREET = 768
ROOFS = {
    "baker": (16, 480, 512),
    "weaver": (560, 1000, 480),
    "tea_house": (1080, 1480, 544),
    "dojo": (1560, 1960, 448),
    "storehouse": (2040, 2400, 416),
    "watch_house": (2480, 2800, 384),
}


def baker(c, k):
    x0, x1, ridge = ROOFS["baker"]
    minka(c, k, x0, x1, ridge, STREET, "baker", front="lattice")
    noren(c, 150, 230, STREET - 120, 40, (120, 74, 48))
    # Steam from the ovens, and the ladder up the wall (x 400..432).
    for i in range(6):
        c.put(c.mask(lambda p: p.ellipse(110 + i * 3, ridge - 14 - i * 9, 6 + i * 1.5, 4 + i), blur=1.2), (236, 236, 236), 0.12)
    rails = c.mask(lambda p: (p.rect(402, ridge - 10, 406, STREET), p.rect(426, ridge - 10, 430, STREET)))
    c.put(rails, (150, 140, 90))
    c.put(c.mask(lambda p: [p.rect(402, y, 430, y + 2.4) for y in np.arange(ridge, STREET, 14)]), (170, 158, 104))
    c.put(c.mask(lambda p: [p.rect(402, y, 406, y + 1) for y in np.arange(ridge, STREET, 24)]), (120, 110, 70))


def weaver(c, k):
    x0, x1, ridge = ROOFS["weaver"]
    eave, beam = minka(c, k, x0, x1, ridge, STREET, "weaver", front="shoji")
    # Cloth drying on a pole: indigo and madder.
    c.put(c.mask(box(600, beam - 6, 960, beam - 3)), (150, 140, 90))
    for i, x in enumerate(np.arange(620, 940, 64)):
        m = c.mask(box(x, beam - 3, x + 40, beam + 60))
        c.put(m, [INDIGO, (176, 76, 66), (226, 214, 180), (70, 90, 120)][i % 4])
        c.tone(m * np.clip((c.y - beam) / 60, 0, 1), -0.15)


def tea_house(c, k):
    x0, x1, ridge = ROOFS["tea_house"]
    eave, beam = minka(c, k, x0, x1, ridge, STREET, "tea", front="shoji")
    noren(c, 1240, 1320, STREET - 110, 44, (110, 50, 40))
    for x in (1150, 1410):
        paper_lantern(c, x, beam + 10, PAPER, 0.8)
    # A bench with a red cloth and a tall paper umbrella.
    c.put(c.mask(box(1340, STREET - 26, 1440, STREET - 20)), (176, 50, 44))
    c.put(c.mask(lambda p: (p.rect(1346, STREET - 20, 1350, STREET), p.rect(1430, STREET - 20, 1434, STREET))), CEDAR)
    c.put(c.mask(lambda p: p.line([(1420, STREET), (1416, STREET - 96)], 1.6)), CEDAR)
    c.put(c.mask(lambda p: p.poly([(1370, STREET - 92), (1462, STREET - 92), (1416, STREET - 116)])), (190, 54, 44))
    c.put(c.mask(lambda p: [p.line([(1416, STREET - 116), (1416 + dx, STREET - 92)], 0.5) for dx in range(-44, 46, 11)]), (150, 40, 34))
    # The sign board under the eave.
    c.put(c.mask(box(1180, eave + 10, 1280, eave + 30)), CEDAR_LIGHT)
    c.put(c.mask(lambda p: [p.line([(x, eave + 14), (x + 4, eave + 26)], 2.2) for x in (1200, 1225, 1250)]), (40, 30, 26))


def dojo_front(c, k):
    """The village dojo round its door (x 1736..1784): dark cedar, a tall
    name board beside the door, a drum under the eave."""
    x0, x1, ridge = ROOFS["dojo"]
    eave, beam = minka(c, k, x0, x1, ridge, STREET, "dojo", front="lattice", depth=64)
    c.put(c.mask(box(1724, STREET - 112, 1796, STREET)), TIMBER)
    c.put(c.mask(box(1730, STREET - 106, 1790, STREET)), (24, 22, 22))
    board = c.mask(box(1806, beam + 8, 1826, STREET - 20))
    c.put(board, CEDAR_LIGHT)
    c.put(c.mask(lambda p: [p.line([(1810, y), (1822, y + 6)], 2.2) for y in np.arange(beam + 18, STREET - 30, 22)]), (30, 24, 22))
    drum = c.mask(lambda p: p.ellipse(1640, beam + 24, 16, 14))
    c.put(drum, (150, 60, 40))
    c.put(c.mask(lambda p: p.ellipse(1640, beam + 24, 11, 10)), (226, 210, 170))
    c.put(c.mask(lambda p: p.rect(1638, eave + 5, 1642, beam + 10)), TIMBER)


def storehouse(c, k):
    x0, x1, ridge = ROOFS["storehouse"]
    minka(c, k, x0, x1, ridge, STREET, "store", front="storehouse")
    # The heavy door, shut, and the family's crest in plaster.
    c.put(c.mask(box(2196, STREET - 110, 2244, STREET - 16)), (54, 56, 62))
    c.put(c.mask(lambda p: p.ellipse(2220, ridge + 90, 12)), PLASTER)
    c.put(c.mask(lambda p: p.poly([(2220, ridge + 80), (2230, ridge + 90), (2220, ridge + 100), (2210, ridge + 90)])), (54, 56, 62))


def notice_board(c, k):
    """The village notice board (the room's label says what it says)."""
    g = STREET
    for x in (2212, 2268):
        post(c, x, g - 92, g, 5, CEDAR)
    c.put(c.mask(box(2200, g - 92, 2280, g - 40)), CEDAR_LIGHT)
    c.put(c.mask(lambda p: p.poly([(2192, g - 92), (2288, g - 92), (2276, g - 102), (2204, g - 102)])), TILE)
    for i, (x, y) in enumerate(((2206, g - 86), (2232, g - 84), (2256, g - 88), (2216, g - 64), (2246, g - 62))):
        c.put(c.mask(box(x, y, x + 20, y + 20)), PAPER if i % 2 else (240, 236, 224))
        c.put(c.mask(lambda p: [p.rect(x + 3, yy, x + 17, yy + 0.8) for yy in np.arange(y + 4, y + 18, 3)]), (60, 50, 44), 0.7)


def watch_house(c, k):
    x0, x1, ridge = ROOFS["watch_house"]
    eave, beam = minka(c, k, x0, x1, ridge, STREET, "watch", front="lattice")
    # The fire bell on its frame at the gable end, and a lantern.
    c.put(c.mask(lambda p: (p.rect(2770, ridge - 60, 2774, ridge), p.rect(2796, ridge - 60, 2800, ridge), p.rect(2766, ridge - 62, 2804, ridge - 58))), TIMBER)
    c.put(c.mask(lambda p: p.poly([(2778, ridge - 56), (2792, ridge - 56), (2795, ridge - 38), (2775, ridge - 38)])), PAL["brass"])
    paper_lantern(c, 2560, beam + 10, PAPER, 0.7)


# ---------------------------------------------------------------------------
# The forest
# ---------------------------------------------------------------------------

FOREST_FLOOR = 832
BRANCH_W, BRANCH_STEP = 320, 384


def branch_at(i):
    return i * BRANCH_STEP + (16 if i == 0 else 0), 384 + 64 * i


def cedar(i):
    """Cedar `i`: its trunk at the east end of the room's branch `i`, the
    bough the branch (its top the walk line), foliage in tiers above."""

    def draw(c, k):
        x, y = branch_at(i)
        tx = x + BRANCH_W - 24
        top = y - 250
        trunk = c.mask(lambda p: p.poly([(tx - 13, FOREST_FLOOR), (tx + 13, FOREST_FLOOR), (tx + 6, top), (tx - 6, top)]))
        c.put(trunk, BARK)
        c.put(c.mask(lambda p: [p.line([(tx + dx, FOREST_FLOOR), (tx + dx * 0.4, top)], 0.8) for dx in (-9, -4, 2, 7)]) * trunk, scale(BARK, 0.7))
        c.tone(trunk * np.clip((c.x - tx) / 12, -1, 1), -0.25)
        # Roots over the floor.
        c.put(c.mask(lambda p: [p.poly([(tx + s * 10, FOREST_FLOOR - 16), (tx + s * 36, FOREST_FLOOR), (tx + s * 8, FOREST_FLOOR)]) for s in (-1, 1)]), BARK)
        # Foliage tiers over the bough (behind the play over it).
        rng = c.rand("cedar", i)
        for tier in range(4):
            ty = y - 40 - tier * 54
            half = 110 - tier * 22
            for _ in range(26):
                fx = tx + rng.uniform(-half, half * 0.6)
                fy = ty + rng.uniform(-18, 10)
                c.put(c.mask(lambda p: p.ellipse(fx, fy, rng.uniform(14, 24), rng.uniform(6, 10))), mix(FOLIAGE, FOLIAGE_LIGHT, rng.uniform(0, 0.7)))
        # The bough: the room's branch, from the trunk west.
        bough = c.mask(lambda p: p.poly([(x - 4, y), (tx, y), (tx + 6, y + 34), (tx - 40, y + 22), (x + 60, y + 14), (x - 6, y + 9)]))
        c.put(bough, BARK)
        c.tone(bough * np.clip((c.y - y) / 20, 0, 1), -0.3)
        walk_edge(c, x, x + BRANCH_W, y, mix(BARK, (190, 150, 110), 0.35))
        for _ in range(26):
            fx = rng.uniform(x + 6, x + BRANCH_W - 20)
            c.put(c.mask(lambda p: p.ellipse(fx, y + 18 + rng.uniform(0, 12), rng.uniform(14, 24), rng.uniform(6, 10))), mix(FOLIAGE, FOLIAGE_LIGHT, rng.uniform(0.1, 0.6)))
        for end in (x + 16, x + 44):
            c.put(c.mask(lambda p: p.ellipse(end, y + 10, 18, 9)), mix(FOLIAGE, FOLIAGE_LIGHT, 0.4))
        # Ferns and a stone at the foot.
        for _ in range(8):
            fx = tx + rng.uniform(-80, 60)
            c.put(c.mask(lambda p: p.poly([(fx, FOREST_FLOOR), (fx + rng.uniform(-14, 14), FOREST_FLOOR - rng.uniform(12, 24)), (fx + 4, FOREST_FLOOR)])), mix(MOSS, FOLIAGE_LIGHT, 0.4))

    return draw


def clan_gatehouse(c, k):
    """The gatehouse of the Shadow Clan's hall round its door (x 2700..2748):
    black-stained cedar, a roof of dark tiles, a dark curtain with a plain
    diamond."""
    g = FOREST_FLOOR
    x0, x1 = 2640, 2808
    walls = c.mask(box(x0, g - 150, x1, g))
    c.put(walls, (34, 30, 30))
    c.tone(walls * (c.noise("clan", 8, 30, 2) - 0.5), 0.3)
    for x in (x0 + 4, x0 + 50, x1 - 50, x1 - 4):
        post(c, x, g - 150, g, 8, (24, 22, 22))
    c.put(c.mask(box(2690, g - 112, 2758, g)), (14, 14, 16))
    noren(c, 2692, 2756, g - 112, 34, (20, 20, 24))
    c.put(c.mask(lambda p: p.poly([(2724, g - 102), (2732, g - 94), (2724, g - 86), (2716, g - 94)])), (150, 36, 32))
    tiled_roof(c, x0 + 30, x1 - 30, g - 196, 46, overhang=40, tag="clan_roof")
    stone_lantern(c, 2620, g, 50)


# ---------------------------------------------------------------------------
# The dojo
# ---------------------------------------------------------------------------

DOJO_FLOOR, DOJO_CEILING = 512, 32


def dojo_wall(c, x0, x1, tag):
    g = DOJO_FLOOR
    wall = c.mask(box(x0, DOJO_CEILING, x1, g))
    c.put(wall, (176, 134, 92))
    c.put(c.mask(lambda p: [p.rect(x, DOJO_CEILING, x + 0.7, g) for x in np.arange(x0, x1, 9)]) * wall, (140, 100, 66), 0.8)
    c.tone(wall * (c.noise((tag, "grain"), 30, 8, 2) - 0.5), 0.15)
    c.put(c.mask(box(x0, g - 60, x1, g)), (120, 84, 56))
    c.put(c.mask(box(x0, g - 62, x1, g - 58)), TIMBER)
    c.put(c.mask(box(x0, DOJO_CEILING, x1, DOJO_CEILING + 18)), TIMBER)
    for x in np.arange(x0 + 2, x1, 160):
        post(c, x, DOJO_CEILING, g, 10, scale(CEDAR, 0.7))
    # High window slits under the ceiling.
    for x in np.arange(x0 + 40, x1 - 60, 160):
        c.put(c.mask(box(x, DOJO_CEILING + 40, x + 80, DOJO_CEILING + 70)), SHOJI)
        c.put(c.mask(lambda p: [p.rect(xx, DOJO_CEILING + 40, xx + 2, DOJO_CEILING + 70) for xx in np.arange(x, x + 80, 8)]), TIMBER)
        c.light(c.mask(box(x, DOJO_CEILING + 40, x + 80, DOJO_CEILING + 70), blur=6), (255, 236, 200), 0.3)


def dojo_entry(c, k):
    """The teacher's end of the dojo: the alcove and its scroll of brush
    strokes, a shelf with a vase, a rack of wooden swords by the bell."""
    dojo_wall(c, 16, 528, "dojo_entry")
    g = DOJO_FLOOR
    c.put(c.mask(box(170, 120, 330, g - 62)), (196, 168, 120))
    c.put(c.mask(box(170, 112, 330, 122)), TIMBER)
    scroll = c.mask(box(226, 140, 274, 330))
    c.put(scroll, (240, 234, 216))
    c.put(c.mask(lambda p: (p.rect(222, 136, 278, 142), p.rect(222, 328, 278, 334))), (60, 44, 36))
    c.put(c.mask(lambda p: (p.line([(250, 160), (246, 210), (254, 250)], 5), p.line([(238, 260), (262, 270)], 4), p.line([(244, 286), (258, 312)], 3.4))), (24, 22, 24))
    c.put(c.mask(lambda p: p.ellipse(268, 318, 3.4)), (190, 50, 40))
    c.put(c.mask(box(180, g - 100, 320, g - 92)), CEDAR)
    c.put(c.mask(lambda p: (p.ellipse(296, g - 110, 8, 10), p.rect(293, g - 126, 299, g - 116))), (90, 110, 120))
    c.put(c.mask(lambda p: [p.line([(296, g - 124), (296 + dx, g - 150)], 1.0) for dx in (-6, 0, 7)]), (80, 110, 60))
    # The sword rack.
    c.put(c.mask(lambda p: (p.rect(400, g - 150, 404, g - 62), p.rect(470, g - 150, 474, g - 62), p.rect(396, g - 150, 478, g - 144), p.rect(396, g - 100, 478, g - 96))), TIMBER)
    for j, x in enumerate(np.arange(412, 466, 9)):
        c.put(c.mask(lambda p: p.line([(x, g - 152), (x + 2, g - 66)], 3.2)), (200, 170, 120) if j % 2 else (150, 112, 74))


def dojo_exam(c, k):
    """The exam floor's end: the rank board of hanging name plaques, a drum,
    and the exam beam on its posts (its top the walk line, y 400,
    x 1040..1280)."""
    dojo_wall(c, 528, 1584, "dojo_exam")
    g = DOJO_FLOOR
    # The rank board: plaques on hooks, a gap where the next name goes.
    c.put(c.mask(box(720, 120, 1000, 128)), TIMBER)
    rng = c.rand("plaques")
    for j, x in enumerate(np.arange(730, 990, 18)):
        if j == 9:
            c.put(c.mask(lambda p: p.ellipse(x + 6, 132, 1.6)), (30, 26, 24))
            continue
        h = rng.uniform(70, 90)
        c.put(c.mask(box(x, 132, x + 12, 132 + h)), (230, 212, 172))
        c.put(c.mask(box(x, 132 + h - 1.2, x + 12, 132 + h)), (150, 116, 80))
        c.put(c.mask(lambda p: [p.line([(x + 6, yy), (x + 6 + rng.uniform(-2, 2), yy + 6)], 1.6) for yy in np.arange(140, 128 + h, 12)]), (40, 32, 28))
    # The beam: its top is the room's ledge.
    for x in (1050, 1270):
        post(c, x, 400, g, 10, CEDAR)
    walk_edge(c, 1040, 1280, 400, CEDAR_LIGHT)
    c.put(c.mask(box(1040, 404, 1280, 412)), CEDAR)
    # A drum on its stand at the far end.
    c.put(c.mask(lambda p: (p.line([(1460, g - 62), (1480, g - 120)], 4), p.line([(1520, g - 62), (1500, g - 120)], 4))), TIMBER)
    c.put(c.mask(lambda p: p.ellipse(1490, g - 130, 34, 30)), (150, 60, 40))
    c.put(c.mask(lambda p: p.ellipse(1490, g - 130, 26, 23)), (228, 212, 172))


#: Every piece: its frame in its room, and how it is drawn.
PIECES: Dict[str, Piece] = {
    # ninja_village_gate_shrine
    "village_shrine_stair": Piece((950, 440, 1600, 704), shrine_stair),
    "village_torii": Piece((1180, 280, 1360, 448), torii),
    "village_shrine_hall": Piece((1330, 280, 1600, 448), shrine_hall),
    "village_shrine_small_things": Piece((530, 540, 940, 704), shrine_small_things),
    # ninja_village_street
    "village_house_baker": Piece((0, 470, 520, 768), baker),
    "village_house_weaver": Piece((520, 440, 1040, 768), weaver),
    "village_tea_house": Piece((1040, 500, 1520, 768), tea_house),
    "village_dojo_front": Piece((1520, 404, 2000, 768), dojo_front),
    "village_storehouse": Piece((2000, 376, 2440, 768), storehouse),
    "village_notice_board": Piece((2186, 660, 2294, 768), notice_board),
    "village_watch_house": Piece((2440, 310, 2816, 768), watch_house),
    # ninja_village_forest
    **{f"village_cedar_{i}": Piece((branch_at(i)[0] - 40, branch_at(i)[1] - 300, branch_at(i)[0] + BRANCH_W + 80, FOREST_FLOOR), cedar(i)) for i in range(7)},
    "village_clan_gatehouse": Piece((2590, 590, 2816, 832), clan_gatehouse),
    # ninja_village_dojo
    "village_dojo_entry": Piece((16, 32, 528, 512), dojo_entry),
    "village_dojo_exam": Piece((528, 32, 1584, 512), dojo_exam),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PAL", "PIECES", "TARGETS"]
