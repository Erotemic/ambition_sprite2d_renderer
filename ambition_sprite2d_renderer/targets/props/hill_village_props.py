"""Hobford (level 1, `intro.ldtk`): a farming village in hill country, newly
on the gate network. Clear morning, the sun from the left.

Drawn in room coordinates (`_district_props`) on the numbers of
`game/ambition_map_assets/ambition_content/generators/intro/make_specs.py`.
Both rooms have their ground at y 512 (`LOW_FLOOR`). Where the room walks
on a one-way board, the piece draws what the board is: its top edge is the
walk line.

`intro_hobford` (`HOUSES`, `village()`):

- `hill_village_cottage`: porch board x 260..340 at 464, roof x 300..540 at 400.
  Limestone, a thatched roof, a door and two windows, a bench by the door.
- `hill_village_smithy`: porch 860..940 at 464, roof 900..1160 at 400, and the
  hay loft over it, x 1000..1120 at 336, with its hoist beam. The old
  smithy sells gate goods now: crates of batteries and lamp oil outside.
- `hill_village_inn`: porch 1460..1540 at 464, roof 1500..1800 at 400. The
  Plough: two storeys under a slate roof, its bay window.
- `hill_village_well`: over the well (x 1248..1312, top 464): its stone curb
  (the solid block), posts, roof, windlass and bucket.
- `hill_village_notice_board`: the board under the room's three notices
  (their middles at x 2090, y 312..396), east of the inn: oak posts, a little roof.

`intro_millstream` (`millstream()`):

- `hill_village_mill`: porch 1520..1680 at 464, the upper floor's gallery
  1600..1820 at 400, the loft door's landing 1720..1840 at 336. A stone
  mill with a timber upper storey, a hoist over the loft door, and the
  wheel on its east end.

The upper row's rooms have their ground at y 672 (`COUNTRY_FLOOR`):

- `hill_survey_station` (`intro_hobford_lane`): Alice's station east of
  where she stands (x 940): her tent, the theodolite on its tripod, a
  ranging pole and a folding table of maps.
- `hill_meadow_oak` (`intro_high_meadow`): the oak beside the shepherd's
  hut. Nothing stands on it, so its boughs are drawn as boughs, not boards.
- `hill_gate_office` (`intro_gate_clearing`): the guard post under its
  roof board (x 1380..1560 at 480): new prefabricated steel on a stone
  footing, a window with a counter, a cable run, a lamp.

`intro_woods` (`HOLLOW`): `hill_woods_hollow_oak`, the oak split open, its
three shelves the climb's boards, and the gap between its roots that is the
way down into the salt run. `intro_millstream`: `hill_salt_run_hatch`, the
trapdoor in the hollow's floor at the other end.

`intro_fell` (`fell()`): `hill_fell_rocks`, `hill_fell_gorse` (and each
as `_slope`, its foot on the drove road's rise of 0.4), `hill_fell_sheep`
and `hill_fell_sheep_grazing`, and `hill_fell_fold_wall` and `hill_fell_cairn`
over the solid blocks they are: drawn about their own origin, placed many
times (`fell()`'s `DRESSING` table says where the ground under each one's
middle is in its frame).

The blocks of the land (a stepping stone, a stream rock, a root, a standing
stone, the meadow's wall and hut) are drawn over the solid blocks they are,
and `hill_gate_barrier` is the look of the clearing's barrier (`LockWall`):
see "the blocks of the land, drawn" below.

Animations: ``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale

G = 512
PORCH = G - 48
ROOF = G - 112
LOFT = G - 176

PAL = {
    "stone": (176, 168, 150), "stone_light": (226, 220, 202), "trim": (214, 206, 186), "dark": (34, 32, 30),
    "glass_top": (178, 206, 226), "glass_low": (120, 146, 164), "lamp": (255, 206, 140), "wood": (110, 78, 50),
    "leaf": (78, 120, 62), "iron": (44, 44, 46), "brass": (176, 140, 72), "glaze": (190, 160, 80),
}
LIMESTONE = (214, 202, 174)
LIMESTONE_WARM = (200, 182, 150)
THATCH = (186, 150, 86)
THATCH_DARK = (132, 100, 56)
OAK = (88, 62, 42)
OAK_LIGHT = (150, 112, 74)
SLATE = (84, 92, 104)
DOOR_GREEN = (62, 92, 70)
DOOR_RED = (128, 52, 40)
BOARD = (132, 98, 64)
PAPER = (232, 222, 196)
IRON = (46, 46, 48)


def walk_edge(c, x0, x1, y, colour=OAK):
    """The walked top of a board at `y`: a plank's face and its lit edge."""
    c.put(c.mask(box(x0, y, x1, y + 6)), colour)
    c.put(c.mask(box(x0, y, x1, y + 1.4)), mix(colour, (255, 240, 210), 0.5))
    c.put(c.mask(box(x0, y + 5, x1, y + 6)), scale(colour, 0.6))


def post(c, x, y0, y1, w=6.0, colour=OAK):
    c.put(c.mask(box(x - w / 2, y0, x + w / 2, y1)), colour)
    c.put(c.mask(box(x - w / 2, y0, x - w / 2 + 1.2, y1)), mix(colour, (255, 236, 200), 0.3))


def thatch(c, x0, x1, eave, ridge, tag):
    """A thatched roof whose eave is the walk line at `eave`: a thick, rounded
    mass rising to `ridge`, combed in straw lines, its ridge bound."""
    cx = (x0 + x1) / 2
    pts = [(x0 - 14, eave + 4), (x0 - 6, eave - 6), (x0 + 30, ridge + 8), (cx, ridge), (x1 - 30, ridge + 8), (x1 + 6, eave - 6), (x1 + 14, eave + 4)]
    m = c.mask(lambda p: p.poly(pts), blur=0.6)
    c.put(m, THATCH)
    rng = c.rand(tag, "straw")
    straw = c.mask(lambda p: [p.line([(x, eave + 2), (cx + (x - cx) * 0.55 + rng.uniform(-3, 3), ridge + 10)], 0.7) for x in np.arange(x0 - 10, x1 + 12, 3.2)])
    c.put(straw * m, THATCH_DARK, 0.45)
    c.tone(m * (c.noise((tag, "thatch"), 24, 10, 3) - 0.5), 0.22)
    # The sun side of the roof is lighter, the far side in shade.
    c.tone(m * np.clip((cx - c.x) / max(1.0, x1 - x0), -0.5, 0.5), 0.18)
    # The bound ridge and the cut eave.
    c.put(c.mask(lambda p: p.poly([(x0 + 26, ridge + 10), (cx, ridge - 2), (x1 - 26, ridge + 10), (cx, ridge + 6)])), scale(THATCH, 0.78))
    c.put(c.mask(box(x0 - 14, eave, x1 + 14, eave + 5)), THATCH_DARK)
    c.put(c.mask(box(x0 - 14, eave, x1 + 14, eave + 1.4)), mix(THATCH, (255, 244, 210), 0.45))
    return m


def bench(c, x0, x1, y_seat):
    c.put(c.mask(box(x0, y_seat, x1, y_seat + 4)), OAK_LIGHT)
    for x in (x0 + 4, x1 - 6):
        c.put(c.mask(box(x, y_seat + 4, x + 3, G)), OAK)


def porch(c, x0, x1, wall_x, tag):
    """A lean-to porch roof on two posts: its boards at PORCH from x0 to x1."""
    roof = c.mask(lambda p: p.poly([(x0 - 6, PORCH + 6), (x1, PORCH + 6), (x1, PORCH - 10), (x0 - 6, PORCH - 2)]))
    c.put(roof, SLATE)
    c.tone(roof * (c.noise((tag, "porch"), 20, 4, 2) - 0.5), 0.2)
    walk_edge(c, x0 - 6, x1, PORCH)
    for x in (x0 + 4, wall_x - 6 if wall_x < x1 else x1 - 6):
        post(c, x, PORCH + 6, G, 5)


def cottage(c, k):
    x0, x1 = 300, 540
    k.wall(x0, ROOF, x1, G, LIMESTONE, texture="stone", tag="cottage")
    k.eave_shade(x0, x1, ROOF + 4, 8)
    k.door(470, 26, 52, DOOR_GREEN, arch=False, tag="cottage_door")
    for cx in (340, 410):
        k.window(cx, ROOF + 30, 22, 24, shutters=DOOR_GREEN, flowers=(214, 70, 80), tag=f"cottage_win{cx}")
    thatch(c, x0, x1, ROOF, ROOF - 70, "cottage_thatch")
    k.chimney(500, ROOF - 12, 14, 58, LIMESTONE_WARM, smoke=(236, 236, 236), tag="cottage_chim")
    porch(c, 260, 340, x0, "cottage")
    bench(c, 268, 296, G - 18)


def smithy(c, k):
    x0, x1 = 900, 1160
    k.wall(x0, ROOF, x1, G, LIMESTONE_WARM, texture="stone", tag="smithy")
    k.eave_shade(x0, x1, ROOF + 4, 8)
    # The wide old forge door, open: the dark inside and the cold forge.
    c.put(c.mask(box(1060, G - 62, 1130, G)), OAK)
    c.put(c.mask(box(1064, G - 58, 1126, G)), (30, 26, 24))
    c.put(c.mask(lambda p: p.ellipse(1095, G - 14, 16, 8)), (90, 50, 34))
    k.window(950, ROOF + 32, 26, 22, shutters=OAK, tag="smithy_win")
    thatch(c, x0, x1, ROOF, ROOF - 54, "smithy_thatch")
    # The loft: a timber gable on the roof, its floor the walk line at LOFT,
    # its hoist beam out over the street.
    k.wall(1000, LOFT, 1120, ROOF, OAK_LIGHT, texture="none", tag="loft")
    k.timber(1000, LOFT, 1120, ROOF, OAK, posts=3, tag="loft_frame")
    c.put(c.mask(box(1044, LOFT + 12, 1076, ROOF)), (40, 34, 30))
    k.gable(1000, 1120, LOFT, 46, SLATE, tiles="slate", overhang=6, tag="loft_roof")
    walk_edge(c, 994, 1126, LOFT)
    c.put(c.mask(box(1110, LOFT - 30, 1150, LOFT - 25)), OAK)
    c.put(c.mask(lambda p: p.line([(1146, LOFT - 25), (1146, LOFT + 20)], 0.8)), IRON)
    c.put(c.mask(lambda p: p.ring(1146, LOFT + 23, 3, 1.0)), IRON)
    k.chimney(920, ROOF - 24, 18, 46, LIMESTONE, tag="smithy_chim")
    porch(c, 860, 940, x0, "smithy")
    # Gate goods outside: crates stencilled with a battery and a drop of oil.
    for i, (bx, by) in enumerate(((960, G - 26), (990, G - 26), (972, G - 50))):
        crate = c.mask(box(bx, by, bx + 26, by + 24))
        c.put(crate, BOARD)
        c.put(c.mask(lambda p: (p.line([(bx + 1, by + 1), (bx + 25, by + 23)], 1.0), p.rect(bx, by, bx + 26, by + 2))) * crate, scale(BOARD, 0.7))
        if i == 2:
            c.put(c.mask(box(bx + 9, by + 8, bx + 17, by + 18)), (40, 40, 40))
            c.put(c.mask(box(bx + 11, by + 6, bx + 15, by + 8)), (40, 40, 40))
        else:
            c.put(c.mask(lambda p: p.ellipse(bx + 13, by + 14, 4, 5)), (40, 40, 40))


def inn(c, k):
    x0, x1 = 1500, 1800
    k.wall(x0, ROOF, x1, G, LIMESTONE, texture="stone", tag="inn")
    k.timber(x0, ROOF, x1, ROOF + 40, OAK, posts=6, tag="inn_frame")
    k.eave_shade(x0, x1, ROOF + 4, 8)
    k.door(1570, 30, 56, DOOR_RED, arch=True, glass_lit=0.4, tag="inn_door")
    # The bay window of the bar, lit.
    bay = c.mask(lambda p: p.poly([(1640, G - 20), (1640, G - 74), (1650, G - 82), (1730, G - 82), (1740, G - 74), (1740, G - 20)]))
    c.put(bay, OAK)
    k.glass(c.mask(box(1648, G - 76, 1732, G - 26)), 0.55, G - 76, G - 26, "inn_bay")
    c.put(c.mask(lambda p: [p.rect(x, G - 76, x + 1.6, G - 26) for x in (1676, 1704)]), OAK)
    for cx in (1540, 1680, 1760):
        k.window(cx, ROOF + 8, 20, 22, lit=0.3, tag=f"inn_up{cx}")
    k.hipped(x0, x1, ROOF, 54, SLATE, tiles="slate", overhang=10, tag="inn_roof")
    walk_edge(c, x0 - 10, x1 + 10, ROOF, scale(SLATE, 0.8))
    k.chimney(1530, ROOF - 18, 16, 72, LIMESTONE_WARM, smoke=(236, 236, 236), tag="inn_chim")
    k.chimney(1760, ROOF - 18, 16, 72, LIMESTONE_WARM, tag="inn_chim2")
    porch(c, 1460, 1540, x0, "inn")
    # Barrels by the bar's door.
    for bx in (1606, 1620):
        barrel = c.mask(lambda p: p.ellipse(bx, G - 12, 7, 12))
        c.put(barrel, BOARD)
        c.put(c.mask(lambda p: [p.rect(bx - 7, y, bx + 7, y + 1.4) for y in (G - 19, G - 6)]) * barrel, IRON)


def well(c, k):
    x0, x1 = 1248, 1312
    # The curb is the solid block the well stands on: dry stone, so no bare
    # earth shows under the posts.
    dry_stone(c, x1 - x0, G - PORCH, "well_curb", coping=False, at=(x0, PORCH))
    for x in (x0 + 5, x1 - 5):
        post(c, x, PORCH - 64, PORCH, 6)
    roof = c.mask(lambda p: p.poly([(x0 - 10, PORCH - 60), ((x0 + x1) / 2, PORCH - 86), (x1 + 10, PORCH - 60)]))
    c.put(roof, SLATE)
    c.tone(roof * (c.noise(("well", "roof"), 12, 6, 2) - 0.5), 0.2)
    c.put(c.mask(box(x0 - 10, PORCH - 61, x1 + 10, PORCH - 58)), scale(SLATE, 0.6))
    # The windlass, its rope and the bucket.
    c.put(c.mask(box(x0 + 5, PORCH - 44, x1 - 5, PORCH - 39)), OAK_LIGHT)
    c.put(c.mask(lambda p: p.line([(x1 - 5, PORCH - 41), (x1 + 4, PORCH - 33)], 1.6)), IRON)
    c.put(c.mask(lambda p: p.line([((x0 + x1) / 2, PORCH - 39), ((x0 + x1) / 2, PORCH - 16)], 0.8)), (150, 130, 96))
    bucket = c.mask(lambda p: p.poly([((x0 + x1) / 2 - 7, PORCH - 16), ((x0 + x1) / 2 + 7, PORCH - 16), ((x0 + x1) / 2 + 5, PORCH - 4), ((x0 + x1) / 2 - 5, PORCH - 4)]))
    c.put(bucket, BOARD)
    c.put(c.mask(box(x0 - 2, PORCH - 3, x1 + 2, PORCH + 1)), PAL["stone_light"])


def notice_board(c, k):
    x0, x1, y0, y1 = 1860, 2320, 300, 404
    for x in (x0 + 8, x1 - 8):
        post(c, x, y0 - 6, G, 7)
    face = c.mask(box(x0, y0, x1, y1))
    c.put(face, BOARD)
    c.put(c.mask(lambda p: [p.rect(x0, y, x1, y + 0.8) for y in np.arange(y0 + 10, y1, 10)]) * face, scale(BOARD, 0.75))
    c.put(c.mask(lambda p: p.poly([(x0 - 10, y0), (x1 + 10, y0), (x1, y0 - 14), (x0, y0 - 14)])), SLATE)
    # Old notices, pinned under the three the room writes.
    rng = c.rand("board", "papers")
    for _ in range(9):
        px, py = rng.uniform(x0 + 6, x1 - 30), rng.uniform(y0 + 4, y1 - 20)
        c.put(c.mask(box(px, py, px + rng.uniform(16, 26), py + rng.uniform(12, 18))), mix(PAPER, (180, 170, 140), rng.uniform(0, 0.5)), 0.85)


def mill(c, k):
    x0, x1 = 1600, 1900
    upper = G - 112
    # The stone ground floor, the timber storey over it, the loft in the gable.
    k.wall(x0, upper, x1, G, LIMESTONE_WARM, texture="stone", tag="mill")
    k.wall(x0 + 10, LOFT, x1 - 10, upper, OAK_LIGHT, texture="none", tag="mill_upper")
    k.timber(x0 + 10, LOFT, x1 - 10, upper, OAK, posts=5, tag="mill_frame")
    k.door(1710, 32, 58, OAK, arch=True, tag="mill_door")
    for cx in (1790, 1856):
        k.window(cx, upper + 34, 22, 24, shutters=OAK, tag=f"mill_win{cx}")
    # The upper floor's gallery (its boards at `upper`, x 1600..1820) and rail.
    walk_edge(c, 1600, 1820, upper)
    c.put(c.mask(lambda p: [p.rect(x, upper - 20, x + 2, upper) for x in np.arange(1604, 1820, 18)]), OAK)
    c.put(c.mask(box(1600, upper - 22, 1820, upper - 18)), OAK_LIGHT)
    # The loft door and its landing (x 1720..1840 at LOFT), the hoist over it.
    k.gable(x0 + 10, x1 - 10, LOFT, 92, SLATE, tiles="slate", overhang=14, tag="mill_roof")
    c.put(c.mask(box(1758, LOFT - 46, 1802, LOFT)), OAK)
    c.put(c.mask(box(1762, LOFT - 42, 1798, LOFT)), (40, 34, 30))
    walk_edge(c, 1720, 1840, LOFT)
    c.put(c.mask(box(1774, LOFT - 70, 1830, LOFT - 64)), OAK)
    c.put(c.mask(lambda p: p.line([(1826, LOFT - 64), (1826, LOFT - 20)], 0.8)), IRON)
    sack = c.mask(lambda p: p.ellipse(1826, LOFT - 12, 8, 10))
    c.put(sack, (210, 196, 160))
    # The porch on the west front (boards x 1520..1680 at PORCH).
    porch(c, 1520, 1680, x0, "mill")
    for i, sx in enumerate((1536, 1554, 1545)):
        sy = G - 12 if i < 2 else G - 30
        c.put(c.mask(lambda p: p.ellipse(sx, sy, 10, 12)), (214, 200, 166))
        c.put(c.mask(lambda p: p.rect(sx - 3, sy - 13, sx + 3, sy - 9)), (150, 130, 96))
    # The wheel on the east end, and the wooden flume over it.
    wx, wy, r = 1960, G - 70, 66
    rim = c.mask(lambda p: (p.ring(wx, wy, r, 7), p.ring(wx, wy, r - 22, 3)))
    c.put(rim, OAK)
    spokes = c.mask(lambda p: [p.line([(wx, wy), (wx + (r - 4) * math.cos(a), wy + (r - 4) * math.sin(a))], 2.4) for a in np.arange(0, math.tau, math.tau / 8)])
    c.put(spokes, scale(OAK, 0.85))
    paddles = c.mask(lambda p: [p.line([(wx + (r - 2) * math.cos(a), wy + (r - 2) * math.sin(a)), (wx + (r + 10) * math.cos(a), wy + (r + 10) * math.sin(a))], 4.0) for a in np.arange(0, math.tau, math.tau / 16)])
    c.put(paddles, OAK_LIGHT)
    c.put(c.mask(lambda p: p.ellipse(wx, wy, 8)), IRON)
    c.put(c.mask(box(1930, wy - r - 22, 2060, wy - r - 12)), BOARD)
    for x in (1950, 2040):
        post(c, x, wy - r - 12, G, 5)
    k.chimney(1640, LOFT - 30, 16, 50, LIMESTONE, tag="mill_chim")


UPPER = 672


def survey_station(c, k):
    g = UPPER
    # The tent: a ridge tent of green canvas, its door flap tied back.
    tent = c.mask(lambda p: p.poly([(1060, g), (1110, g - 58), (1160, g)]))
    c.put(tent, (96, 122, 82))
    c.tone(tent * np.clip((c.x - 1110) / 50, 0, 1), -0.2)
    c.put(c.mask(lambda p: p.poly([(1100, g), (1110, g - 40), (1122, g)])), (40, 44, 34))
    c.put(c.mask(lambda p: p.line([(1110, g - 58), (1110, g - 66)], 1.6)), OAK)
    c.put(c.mask(lambda p: (p.line([(1060, g), (1046, g - 2)], 0.6), p.line([(1160, g), (1174, g - 2)], 0.6))), (200, 190, 160))
    # The theodolite on its tripod.
    tx = 990
    for dx in (-14, 0, 14):
        c.put(c.mask(lambda p: p.line([(tx, g - 46), (tx + dx, g)], 1.8)), OAK_LIGHT)
    c.put(c.mask(box(tx - 6, g - 52, tx + 6, g - 46)), IRON)
    c.put(c.mask(box(tx - 4, g - 62, tx + 4, g - 52)), (196, 160, 70))
    c.put(c.mask(box(tx - 9, g - 60, tx + 9, g - 56)), (60, 60, 64))
    # A ranging pole, red and white, and the table of maps.
    for i in range(6):
        c.put(c.mask(box(1176, g - 90 + i * 15, 1180, g - 75 + i * 15)), (200, 60, 50) if i % 2 == 0 else (236, 232, 222))
    c.put(c.mask(box(1016, g - 30, 1052, g - 27)), OAK_LIGHT)
    for x in (1020, 1048):
        c.put(c.mask(lambda p: p.line([(x, g - 27), (x + (4 if x < 1030 else -4), g)], 1.2)), OAK)
    c.put(c.mask(lambda p: p.poly([(1018, g - 31), (1050, g - 31), (1046, g - 34), (1022, g - 34)])), PAPER)


def meadow_oak(c, k):
    """The old oak by the shepherd's hut. Nothing stands on it: its boughs
    climb and taper as an oak's do, so none reads as a board."""
    g = UPPER
    tx = 1066
    bark = (96, 74, 54)
    leaf = (74, 112, 60)
    rng = c.rand("oak", "crown")
    # Each bough: from the trunk, rising and thinning to the crown.
    boughs = [(-1, 470, 940, 380), (1, 452, 1190, 360), (-1, 400, 960, 300), (1, 380, 1170, 280), (-1, 340, 1010, 250)]
    clumps = []
    for _, _, x, y in boughs:
        for _ in range(9):
            clumps.append((rng.uniform(x - 60, x + 60), rng.uniform(y - 50, y + 20), rng.uniform(22, 34), rng.uniform(15, 24)))
    for _ in range(14):
        clumps.append((rng.uniform(930, 1200), rng.uniform(200, 290), rng.uniform(26, 40), rng.uniform(18, 26)))
    crown = c.mask(lambda p: [p.ellipse(*cl) for cl in clumps], blur=1.4)
    c.put(crown, leaf)
    c.tone(crown * (c.noise(("oak", "leaf"), 30, 30, 3) - 0.5), 0.32)
    c.tone(crown * np.clip((c.x - 1070) / 170, -1, 1), -0.16)
    c.put(crown * c.mask(lambda p: [p.ellipse(cx - rx * 0.3, cy - ry * 0.35, rx * 0.5, ry * 0.4) for cx, cy, rx, ry in clumps], blur=2.0), mix(leaf, (220, 236, 160), 0.35), 0.5)
    # The trunk, flaring into its roots, forking into the crown.
    trunk = c.mask(lambda p: (p.poly([(tx - 44, g), (tx - 26, g - 16), (tx - 18, 330), (tx + 22, 330), (tx + 30, g - 16), (tx + 50, g)]),
                              p.poly([(tx - 18, 336), (tx - 40, 250), (tx - 26, 246), (tx, 320)]),
                              p.poly([(tx + 22, 336), (tx + 44, 254), (tx + 30, 250), (tx + 2, 320)])))
    c.put(trunk, bark)
    c.put(trunk * c.mask(lambda p: [p.line([(tx - 24 + i * 7, g), (tx - 12 + i * 4, 330)], 0.9) for i in range(9)]), scale(bark, 0.7), 0.6)
    c.tone(trunk * np.clip((c.x - tx) / 30, 0, 1), -0.2)
    for side, y0, x1, y1 in boughs:
        near = tx + (14 if side > 0 else -10)
        # A tapering curve: thick at the trunk, thin in the leaves.
        ts = np.linspace(0.0, 1.0, 14)
        ctrl = ((near + x1) / 2, min(y0, y1) + (y0 - y1) * 0.15 - 10)
        spine = [((1 - t) ** 2 * near + 2 * (1 - t) * t * ctrl[0] + t * t * x1,
                  (1 - t) ** 2 * y0 + 2 * (1 - t) * t * ctrl[1] + t * t * y1) for t in ts]
        half = [8.0 * (1 - t) + 1.5 * t for t in ts]
        upper = [(x, y - w) for (x, y), w in zip(spine, half)]
        lower = [(x, y + w) for (x, y), w in zip(spine, half)]
        thick = c.mask(lambda p: p.poly(upper + lower[::-1]), blur=0.5)
        c.put(thick, bark)
        c.tone(thick * np.clip((c.y - min(y0, y1)) / 60, 0, 1), -0.18)


def gate_office(c, k):
    g = UPPER
    x0, x1, roof = 1388, 1552, g - 192
    # A stone footing, prefabricated steel walls, the new roof board.
    k.wall(x0 - 4, g - 20, x1 + 4, g, PAL["stone"], texture="stone", tag="post_foot")
    walls = c.mask(box(x0, roof + 6, x1, g - 20))
    c.put(walls, (150, 160, 168))
    c.put(walls * c.mask(lambda p: [p.rect(x, roof + 6, x + 1.2, g - 20) for x in np.arange(x0 + 12, x1, 12)]), (112, 122, 130), 0.8)
    c.tone(walls * np.clip((c.y - roof) / 192, 0, 1), -0.12)
    k.eave_shade(x0, x1, roof + 6, 10)
    walk_edge(c, 1380, 1560, roof, (70, 78, 86))
    # The window and its counter, a door, a lamp, the cable run.
    k.window(1430, roof + 60, 46, 36, frame=(60, 66, 72), bars=False, tag="post_win")
    c.put(c.mask(box(1400, roof + 100, 1460, roof + 105)), OAK_LIGHT)
    k.door(1510, 30, 64, (60, 70, 80), arch=False, step=True, tag="post_door")
    k.lamp(1480, h=40, lit=0.0, tag="post_lamp")
    c.put(c.mask(lambda p: p.line([(x1, roof + 20), (x1 + 6, roof + 30), (x1 + 6, g - 20)], 1.4)), IRON)
    # Yellow and black hazard band along the footing.
    band = c.mask(box(x0, g - 26, x1, g - 20))
    c.put(band, (220, 180, 40))
    c.put(band * c.mask(lambda p: [p.poly([(x, g - 26), (x + 6, g - 26), (x + 2, g - 20), (x - 4, g - 20)]) for x in np.arange(x0, x1, 12)]), (30, 30, 30))


#: Every piece: its frame in its room, and how it is drawn.
PIECES: Dict[str, Piece] = {
    # intro_hobford
    "hill_village_cottage": Piece((240, 300, 560, 512), cottage),
    "hill_village_smithy": Piece((840, 270, 1180, 512), smithy),
    "hill_village_inn": Piece((1440, 300, 1820, 512), inn),
    "hill_village_well": Piece((1236, 370, 1328, 512), well),
    "hill_village_notice_board": Piece((1840, 280, 2340, 512), notice_board),
    # intro_millstream
    "hill_village_mill": Piece((1500, 220, 2080, 512), mill),
    # intro_hobford_lane
    "hill_survey_station": Piece((960, 560, 1200, 672), survey_station),
    # intro_high_meadow
    "hill_meadow_oak": Piece((880, 200, 1260, 672), meadow_oak),
    # intro_gate_clearing
    "hill_gate_office": Piece((1370, 460, 1570, 672), gate_office),
}


# ----------------------------------------------- the fell: open hillside
#
# Unlike the pieces above, these are drawn about their own origin and placed
# many times (`intro_fell`, `fell()`): `foot` is the ground under the
# piece's middle, in its frame. A `_slope` piece stands on the fell's
# drove road, which rises east at `FELL_GRADE`: its foot follows the line,
# so no corner floats over the road or sinks into it.

FELL_GRADE = 0.4
STONE_GREY = (150, 146, 136)
GORSE = (58, 84, 44)
GORSE_FLOWER = (238, 196, 52)
FLEECE = (226, 218, 198)
FACE = (36, 32, 30)


def _ground(width, foot, grade):
    """The ground under a piece `width` wide whose middle stands at `foot`,
    rising east at `grade`: y at each x."""
    return lambda x: foot - grade * (x - width / 2)


def _on_the_ground(c, ground):
    """1 above the ground line (with a little sunk in), 0 below it."""
    return (c.y <= ground(c.x) + 1.5).astype(np.float32)


def rocks(c, width, foot, grade, tag):
    """Three boulders, bedded in the turf, lichen on them, lit from the west."""
    ground = _ground(width, foot, grade)
    rng = c.rand(tag, "rocks")
    stones = [(width * 0.30, 26, 18), (width * 0.62, 20, 14), (width * 0.82, 12, 9)]
    for n, (x, rx, ry) in enumerate(stones):
        x += rng.uniform(-4, 4)
        base = ground(x)
        pts = [(x - rx, base + 4), (x - rx * 0.9, base - ry * 0.9), (x - rx * 0.3, base - ry * 1.6),
               (x + rx * 0.5, base - ry * 1.5), (x + rx, base - ry * 0.6), (x + rx * 1.05, base + 4)]
        m = c.mask(lambda pen: pen.poly(pts), blur=0.5) * _on_the_ground(c, ground)
        c.put(m, scale(STONE_GREY, 1.0 - 0.06 * n))
        c.tone(m * (c.noise((tag, "rock", n), 6, 4, 3) - 0.5), 0.35)
        c.tone(m * np.clip((x - c.x) / rx, -1, 1), 0.18)
        lichen = c.mask(lambda pen: [pen.ellipse(x + rng.uniform(-rx * 0.7, rx * 0.4), base - rng.uniform(ry * 0.4, ry * 1.3),
                                                 rng.uniform(1.0, 2.2), rng.uniform(0.7, 1.5)) for _ in range(6)])
        c.put(lichen * m, (178, 176, 118), 0.5)
    # Grass at their feet.
    blades = c.mask(lambda pen: [pen.line([(x, ground(x) + 2), (x + rng.uniform(-2, 2), ground(x) - rng.uniform(3, 8))], 0.8)
                                 for x in np.arange(4, width - 4, 3.0)])
    c.put(blades, (96, 130, 64), 0.8)


def gorse(c, width, foot, grade, tag):
    """A gorse bush in flower: dark spiny green, yellow all over the sun side."""
    ground = _ground(width, foot, grade)
    rng = c.rand(tag, "gorse")
    clumps = [(rng.uniform(width * 0.2, width * 0.8), 0, rng.uniform(12, 20), rng.uniform(10, 16)) for _ in range(9)]
    clumps = [(x, ground(x) - ry * rng.uniform(0.7, 1.6), rx, ry) for x, _, rx, ry in clumps]
    # Its stems meet the ground along the whole bush, so no clump floats.
    base = [(x, ground(x) + 3) for x in (width * 0.12, width * 0.88)] + [(x, ground(x) - 14) for x in (width * 0.8, width * 0.2)]
    m = c.mask(lambda pen: ([pen.ellipse(*cl) for cl in clumps], pen.poly(base)), blur=0.8) * _on_the_ground(c, ground)
    c.put(m, GORSE)
    spines = c.mask(lambda pen: [pen.line([(x, y), (x + rng.uniform(-3, 3), y - rng.uniform(2, 5))], 0.5)
                                 for x, y in ((rng.uniform(4, width - 4), rng.uniform(foot - 40, foot)) for _ in range(160))])
    c.put(spines * m, scale(GORSE, 0.6), 0.8)
    c.tone(m * np.clip((width / 2 - c.x) / width, -0.5, 0.5), 0.3)
    flowers = c.mask(lambda pen: [pen.ellipse(x, y, 1.4, 1.2) for x, y in
                                  ((rng.uniform(4, width * 0.8), rng.uniform(foot - 44, foot - 4)) for _ in range(70))])
    c.put(flowers * m, GORSE_FLOWER, 0.95)


def sheep(c, width, foot, grazing, tag):
    """A fell sheep, black-faced and black-legged, facing west; its head down
    to the grass when `grazing`."""
    rng = c.rand(tag, "sheep")
    cx, top = width / 2 + 4, foot - 30
    for x in (cx - 12, cx - 6, cx + 8, cx + 13):
        c.put(c.mask(box(x - 1.5, foot - 12, x + 1.5, foot)), FACE)
    body = c.mask(lambda pen: [pen.ellipse(cx + rng.uniform(-14, 14), top + 9 + rng.uniform(-4, 4), rng.uniform(7, 10), rng.uniform(6, 8))
                               for _ in range(12)] + [pen.ellipse(cx, top + 10, 18, 9)], blur=0.7)
    c.put(body, FLEECE)
    c.tone(body * (c.noise((tag, "wool"), 10, 6, 2) - 0.5), 0.25)
    c.tone(body * np.clip((c.y - top - 8) / 12, 0, 1), -0.22)
    # The head: a long black face, the muzzle west, an ear back; on a neck
    # from the fleece's front, raised or down to the grass.
    hx, hy = (cx - 24, foot - 5) if grazing else (cx - 25, top + 1)
    tilt = 0.9 if grazing else 0.35
    neck = c.mask(lambda pen: pen.line([(cx - 13, top + 9), (hx + 6, hy - 1)], 6))
    c.put(neck, FLEECE if not grazing else scale(FLEECE, 0.9))
    head = c.mask(lambda pen: pen.poly([(hx + 7, hy - 4), (hx + 2, hy - 5), (hx - 5, hy - 2 + tilt * 3),
                                        (hx - 6, hy + 1 + tilt * 3), (hx - 3, hy + 3 + tilt * 2), (hx + 6, hy + 3)]), blur=0.4)
    c.put(head, FACE)
    c.put(c.mask(lambda pen: pen.ellipse(hx + 8, hy - 3, 3.2, 1.4)), FACE)
    c.put(c.mask(lambda pen: pen.ellipse(hx + 1, hy - 2, 0.9)), (230, 214, 160))
    # A tuft of fleece on the crown.
    c.put(c.mask(lambda pen: pen.ellipse(hx + 6, hy - 4, 3, 2.2), blur=0.4), FLEECE)


def _fell_piece(width, height, draw):
    """A piece `width` wide and `height` tall over its foot, with its draw."""
    return Piece((0, 0, width, height), lambda c, k: draw(c, width, height))


PIECES.update({
    # intro_fell: dressing for its terraces and its drove road
    "hill_fell_rocks": _fell_piece(128, 56, lambda c, w, h: rocks(c, w, h - 4, 0.0, "rocks")),
    "hill_fell_rocks_slope": _fell_piece(128, 56 + 26, lambda c, w, h: rocks(c, w, h - 4 - 26, FELL_GRADE, "rocks_slope")),
    "hill_fell_gorse": _fell_piece(96, 56, lambda c, w, h: gorse(c, w, h - 4, 0.0, "gorse")),
    "hill_fell_gorse_slope": _fell_piece(96, 56 + 20, lambda c, w, h: gorse(c, w, h - 4 - 20, FELL_GRADE, "gorse_slope")),
    "hill_fell_sheep": _fell_piece(64, 40, lambda c, w, h: sheep(c, w, h - 2, False, "sheep")),
    "hill_fell_sheep_grazing": _fell_piece(64, 40, lambda c, w, h: sheep(c, w, h - 2, True, "sheep_grazing")),
})


def dry_stone(c, width, height, tag, coping, at=(0.0, 0.0)):
    """Flat stones laid without mortar, filling the box of a solid block
    (`width` x `height` from its top left `at`, its top the walk line) so the
    block reads as stone, with upright coping stones along the top of a wall."""
    ox, oy = at
    rng = c.rand(tag, "stones")
    gaps = scale(STONE_GREY, 0.42)
    c.put(c.mask(box(ox, oy, ox + width, oy + height)), gaps)
    y = 0.0
    rows = []
    while y < height:
        rows.append((y, min(height, y + rng.uniform(6.5, 9.5))))
        y = rows[-1][1]
    for n, (y0, y1) in enumerate(rows):
        x = -rng.uniform(0, 6)
        while x < width:
            x1 = min(width + 1, x + rng.uniform(5, 18))
            j = lambda: rng.uniform(-1.4, 1.4)
            stone = [(x + 0.8 + j(), y0 + 0.9 + j() * 0.5), ((x + x1) / 2 + j(), y0 + 0.5), (x1 - 0.8 + j(), y0 + 0.9 + j() * 0.5),
                     (x1 - 0.4, (y0 + y1) / 2 + j()), (x1 - 0.9 + j(), y1 - 0.8), (x + 0.6 + j(), y1 - 0.7), (x + 0.2, (y0 + y1) / 2 + j())]
            stone = [(px + ox, py + oy) for px, py in stone]
            m = c.mask(lambda pen: pen.poly(stone), blur=0.45) * c.mask(box(ox, oy, ox + width, oy + height))
            shade = rng.uniform(0.82, 1.08)
            c.put(m, scale(STONE_GREY, shade))
            c.tone(m * np.clip((oy + y0 + 2 - c.y) / 3, 0, 1), 0.25)
            c.tone(m * np.clip((c.y - oy - y1 + 2) / 3, 0, 1), -0.25)
            x = x1 + rng.uniform(0.4, 1.2)
    if coping:
        x = 0.0
        while x < width:
            x1 = min(width, x + rng.uniform(3.5, 5.5))
            slab = [(x + ox, oy + 6), (x + 1.0 + ox, oy - 0.2), (x1 + ox, oy - 0.2), (x1 - 1.0 + ox, oy + 6)]
            m = c.mask(lambda pen: pen.poly(slab))
            c.put(m, scale(STONE_GREY, rng.uniform(0.85, 1.05)))
            c.tone(m * np.clip((ox + x + 1.5 - c.x) / 1.5, 0, 1), 0.3)
            x = x1 + 0.6
    c.tone(c.mask(box(ox, oy, ox + width, oy + height)) * (c.noise((tag, "weather"), 4, 3, 2) - 0.5), 0.2)
    moss = c.mask(lambda pen: [pen.ellipse(ox + rng.uniform(0, width), oy + rng.uniform(0, height), rng.uniform(1.0, 2.4), rng.uniform(0.6, 1.4))
                               for _ in range(int(width * height / 260))])
    c.put(moss, (110, 132, 72), 0.4)


def cairn(c, width, height):
    """A walkers' cairn: rounded stones heaped to fill a solid block's box,
    each one put there by someone who reached the top."""
    rng = c.rand("cairn", "stones")
    c.put(c.mask(box(0, 0, width, height)), scale(STONE_GREY, 0.4))
    stones = []
    y = height - 4
    while y > -3:
        x = rng.uniform(-3, 2)
        r = rng.uniform(4.0, 6.5) * (0.75 + 0.25 * y / height)
        while x < width + 2:
            stones.append((x + r, y, r * rng.uniform(1.0, 1.4), r * rng.uniform(0.7, 0.95)))
            x += r * 2 + rng.uniform(-1.5, 0.5)
        y -= r * 1.35
    for n, (cx, cy, rx, ry) in enumerate(stones):
        inside = c.mask(box(0, 0, width, height))
        c.put(c.mask(lambda pen: pen.ellipse(cx, cy, rx + 0.9, ry + 0.9), blur=0.3) * inside, scale(STONE_GREY, 0.45))
        m = c.mask(lambda pen: pen.ellipse(cx, cy, rx, ry), blur=0.3) * inside
        c.put(m, scale(STONE_GREY, rng.uniform(0.8, 1.1)))
        c.tone(m * np.clip((cx - c.x) / rx, -1, 1) * np.clip((cy - c.y) / ry + 0.3, 0, 1), 0.3)
    lichen = c.mask(lambda pen: [pen.ellipse(rng.uniform(0, width), rng.uniform(0, height), rng.uniform(0.8, 1.8), rng.uniform(0.5, 1.1))
                                 for _ in range(10)])
    c.put(lichen, (178, 176, 118), 0.45)


PIECES.update({
    # intro_fell: the sheepfold's wall and the cairn on the top, each over
    # the solid block it is (48 x 48 and 64 x 48)
    "hill_fell_fold_wall": Piece((0, 0, 48, 48), lambda c, k: dry_stone(c, 48, 48, "fold_wall", coping=True)),
    "hill_fell_cairn": Piece((0, 0, 64, 48), lambda c, k: cairn(c, 64, 48)),
})


# ------------------------------------------- the blocks of the land, drawn
#
# A solid block in an outdoor room is drawn in the room's terrain skin, so a
# well's curb, a stone in a stream or a root in the woods was a cube of earth
# with grass on it. Each piece below fills the box of one such block (its top
# the walk line, `width` x `height` from its top left), and the room places
# it over the block. Scenery draws in front of blocks, so the earth is hidden.

WET = (84, 92, 88)
ALGAE = (70, 96, 64)
BARK = (92, 70, 50)
TURF = (96, 128, 64)


def boulder(c, width, height, tag, water_line=None):
    """A rounded boulder filling its box; below `water_line` (y in the box)
    it is wet and green with weed."""
    rng = c.rand(tag, "boulder")
    # The corners are cut only a little: the block behind is square, and its
    # earth must not show past the stone.
    pts = [(0, height), (-0.5, height * 0.45), (0.5, 3.0), (3.0, 0.2), (width * 0.5, -0.3), (width - 3.0, 0.2), (width - 0.5, 3.0),
           (width + 0.5, height * 0.5), (width, height)]
    pts = [(x + rng.uniform(-1, 1), y + rng.uniform(-0.6, 0.6)) for x, y in pts]
    m = c.mask(lambda pen: pen.poly(pts), blur=0.5)
    c.put(m, STONE_GREY)
    c.tone(m * (c.noise((tag, "grain"), 5, 4, 3) - 0.5), 0.35)
    c.tone(m * np.clip((width * 0.4 - c.x) / width, -0.5, 0.5), 0.3)
    c.tone(m * np.clip((c.y - height * 0.3) / height, 0, 1), -0.2)
    cracks = c.mask(lambda pen: [pen.line([(x, rng.uniform(4, height * 0.4)), (x + rng.uniform(-6, 6), rng.uniform(height * 0.5, height))], 0.6)
                                 for x in (rng.uniform(width * 0.2, width * 0.8) for _ in range(2))])
    c.put(cracks * m, scale(STONE_GREY, 0.55), 0.7)
    if water_line is not None:
        wet = m * (c.y > water_line).astype(np.float32)
        c.put(wet, WET, 0.55)
        weed = c.mask(lambda pen: [pen.line([(x, height), (x + rng.uniform(-2, 2), height - rng.uniform(4, 12))], 0.7)
                                   for x in (rng.uniform(0, width) for _ in range(int(width / 4)))])
        c.put(weed * wet, ALGAE, 0.75)
    else:
        lichen = c.mask(lambda pen: [pen.ellipse(rng.uniform(2, width - 2), rng.uniform(2, height * 0.6), rng.uniform(0.8, 2.0), rng.uniform(0.5, 1.2))
                                     for _ in range(8)])
        c.put(lichen * m, (178, 176, 118), 0.5)


def stepping_stone(c, width, height, tag):
    """A stepping stone: a pier of laid stone from the stream bed to the
    bank's height, its top slab worn flat by boots, dark and weedy below the
    water."""
    rng = c.rand(tag, "pier")
    dry_stone(c, width, height, tag, coping=False)
    wet = c.mask(box(0, 8, width, height))
    c.put(wet, WET, 0.45)
    c.tone(wet * np.clip((c.y - 8) / height, 0, 1), -0.3)
    weed = c.mask(lambda pen: [pen.line([(x, height), (x + rng.uniform(-2, 2), height - rng.uniform(6, 20))], 0.8)
                               for x in (rng.uniform(0, width) for _ in range(int(width / 4)))])
    c.put(weed, ALGAE, 0.75)
    c.put(c.mask(box(-0.5, 0, width + 0.5, 5)), scale(STONE_GREY, 1.05))
    c.put(c.mask(lambda pen: pen.poly([(2, 1), (width - 2, 1), (width - 4, 3.5), (4, 3.5)])), mix(STONE_GREY, (240, 236, 220), 0.25), 0.8)


def standing_stone(c, width, height, tag):
    """One of the old standing stones by the road to the gate: a squat slab,
    lichened, a spiral cut in it long before anyone could read."""
    boulder(c, width, height, tag)
    cx, cy = width * 0.5, height * 0.52
    spiral = [(cx + math.cos(t) * t * 1.35, cy + math.sin(t) * t * 1.35) for t in np.arange(0.5, 10.5, 0.25)]
    c.put(c.mask(lambda pen: pen.line(spiral, 0.9)), scale(STONE_GREY, 0.55), 0.8)


def woods_root(c, width, height, tag):
    """A root of one of the great trees, arched out of the woods' floor:
    bark ridged along it, moss on its back, which is where a foot goes."""
    rng = c.rand(tag, "root")
    m = c.mask(lambda pen: pen.poly([(0, height), (0, 6), (width * 0.2, 0.5), (width * 0.8, 0.5), (width, 6), (width, height)]), blur=0.5)
    c.put(m, BARK)
    ridges = c.mask(lambda pen: [pen.line([(x, height), (x + rng.uniform(-4, 4), height * 0.5), (x + rng.uniform(-6, 6), 2)], 1.0)
                                 for x in np.arange(3, width, 5.5)])
    c.put(ridges * m, scale(BARK, 0.65), 0.7)
    c.tone(m * np.clip((width * 0.35 - c.x) / width, -0.5, 0.5), 0.28)
    c.tone(m * np.clip((c.y - 6) / height, 0, 1), -0.25)
    moss = c.mask(lambda pen: [pen.ellipse(rng.uniform(0, width), rng.uniform(0, 5), rng.uniform(3, 7), rng.uniform(1.5, 3)) for _ in range(9)], blur=0.5)
    c.put(moss * m, (88, 120, 60), 0.9)


def shepherds_hut(c, width, height, tag):
    """The shepherd's hut on the meadow terrace: a low bothy of dry stone
    under a turf roof, its door on the west, a small window. Its roof is
    the step a walker climbs."""
    dry_stone(c, width, height, tag, coping=False)
    roof = c.mask(lambda pen: pen.poly([(-1, 9), (2, 0), (width - 2, 0), (width + 1, 9)]), blur=0.4)
    c.put(roof, TURF)
    c.tone(roof * (c.noise((tag, "turf"), 14, 2, 2) - 0.5), 0.3)
    c.put(c.mask(lambda pen: [pen.line([(x, 1), (x + 0.6, -2.5)], 0.6) for x in np.arange(2, width - 2, 2.2)]), mix(TURF, (190, 214, 120), 0.4), 0.8)
    c.put(c.mask(box(0, 9, width, 11)), scale(TURF, 0.6), 0.8)
    c.put(c.mask(lambda pen: pen.arch(18, 22, 38, height)), (34, 30, 26))
    c.put(c.mask(box(17, 21, 39, 22.5)), OAK_LIGHT)
    c.put(c.mask(box(width - 54, 26, width - 38, 38)), (46, 52, 56))
    c.put(c.mask(box(width - 55, 38, width - 37, 40)), OAK_LIGHT)


def _block_piece(width, height, draw, tag):
    return Piece((0, 0, width, height), lambda c, k: draw(c, width, height, tag))


PIECES.update({
    # intro_millstream: the stepping stones and the rock in the stream
    "hill_stepping_stone": _block_piece(80, 96, stepping_stone, "stepping_stone"),
    "hill_stepping_stone_narrow": _block_piece(64, 96, stepping_stone, "stepping_stone_narrow"),
    "hill_stream_rock": _block_piece(64, 48, lambda c, w, h, t: boulder(c, w, h, t, water_line=-1), "stream_rock"),
    # intro_woods: the roots across the path
    "hill_woods_root": _block_piece(80, 48, woods_root, "woods_root"),
    # intro_gate_clearing: the standing stones
    "hill_standing_stone": _block_piece(48, 48, standing_stone, "standing_stone"),
    # intro_high_meadow: the wall on the hilltop, the shepherd's hut
    "hill_meadow_wall": _block_piece(32, 48, lambda c, w, h, t: dry_stone(c, w, h, t, coping=True), "meadow_wall"),
    "hill_meadow_hut": _block_piece(176, 64, shepherds_hut, "meadow_hut"),
})


CRATE = (152, 114, 72)
STENCIL = (44, 38, 34)
BURLAP = (178, 152, 106)


def freight_crates(c, width, height, tag):
    """Freight crates off the train on the siding's ground, two side by
    side: planked, framed, braced corner to corner and iron-banded, a
    stencilled arrow for which way is up. Their lids are the step a walker
    climbs."""
    rng = c.rand(tag, "crates")
    for i, (x0, x1) in enumerate(((0.5, width / 2 - 0.5), (width / 2 + 0.5, width - 0.5))):
        wood = scale(CRATE, rng.uniform(0.88, 1.04))
        face = c.mask(box(x0, 0.5, x1, height))
        c.put(face, wood)
        c.tone(face * (c.noise((tag, "grain", i), 3, 9, 2) - 0.5), 0.2)
        c.put(c.mask(lambda p: [p.rect(x0, y, x1, y + 0.6) for y in np.arange(height / 4, height - 1, height / 4)]) * face, scale(wood, 0.6))
        c.put(c.mask(lambda p: p.line([(x0 + 3, height - 3), (x1 - 3, 3.5)], 2.2)) * face, scale(wood, 0.84))
        frame = c.mask(lambda p: [p.rect(x0, 0.5, x0 + 3, height), p.rect(x1 - 3, 0.5, x1, height),
                                  p.rect(x0, 0.5, x1, 3.5), p.rect(x0, height - 3, x1, height)])
        c.put(frame, scale(wood, 0.78))
        for bx in (x0 + 9, x1 - 9):
            c.put(c.mask(box(bx - 0.7, 0.5, bx + 0.7, height)), IRON, 0.8)
        cx, cy = (x0 + x1) / 2, height * 0.5
        arrow = [(cx, cy - 9), (cx - 5, cy - 3), (cx - 1.6, cy - 3), (cx - 1.6, cy + 6), (cx + 1.6, cy + 6), (cx + 1.6, cy - 3), (cx + 5, cy - 3)]
        c.put(c.mask(lambda p: p.poly(arrow)), STENCIL, 0.65)
    whole = c.mask(box(0, 0, width, height))
    c.tone(whole * np.clip((width * 0.3 - c.x) / width, -0.4, 0.4), 0.22)
    c.tone(whole * np.clip((c.y - height * 0.6) / height, 0, 1), -0.25)


GOBLIN_DAUB = (150, 46, 34)
ROPE = (164, 134, 86)


def goblins_crate(c, width, height, tag):
    """The crate the raiders packed the Creator's notes in (the siding's
    chest): a freight crate like the others, lashed with a rope, its stencil
    painted over with a goblin's red daub (a toothy grin), the lid nailed
    down crooked."""
    lid = 7.0
    face = c.mask(box(0.5, lid, width - 0.5, height))
    c.put(face, CRATE)
    c.tone(face * (c.noise((tag, "grain"), 3, 8, 2) - 0.5), 0.2)
    c.put(c.mask(lambda p: [p.rect(0.5, y, width - 0.5, y + 0.6) for y in np.arange(lid + 12, height - 1, 12)]) * face, scale(CRATE, 0.6))
    c.put(c.mask(lambda p: p.line([(4, height - 4), (width - 4, lid + 4)], 2.4)) * face, scale(CRATE, 0.84))
    frame = c.mask(lambda p: [p.rect(0.5, lid, 4, height), p.rect(width - 4, lid, width - 0.5, height),
                              p.rect(0.5, height - 3.5, width - 0.5, height)])
    c.put(frame, scale(CRATE, 0.78))
    # The lid, nailed down askew.
    c.put(c.mask(lambda p: p.poly([(-0.5, lid + 1), (width + 0.5, lid - 2.5), (width + 0.5, lid + 1.5), (-0.5, lid + 4.5)])), scale(CRATE, 0.9))
    for nx in (6.0, width - 6.0):
        c.put(c.mask(lambda p: p.ellipse(nx, lid + (2.6 if nx < 10 else 0.0), 0.9)), IRON)
    # The daub: a grin of teeth, in red paint, over the up-arrow.
    cx, cy = width / 2, lid + (height - lid) * 0.55
    c.put(c.mask(lambda p: p.line([(cx - 13, cy - 3), (cx - 6, cy + 4), (cx + 6, cy + 4), (cx + 13, cy - 3)], 2.6)), GOBLIN_DAUB, 0.9)
    c.put(c.mask(lambda p: [p.line([(x, cy + 3.5), (x + 1.5, cy - 0.5)], 1.6) for x in np.arange(cx - 7, cx + 8, 4)]), GOBLIN_DAUB, 0.9)
    c.put(c.mask(lambda p: [p.ellipse(cx - 7, cy - 9, 2.2), p.ellipse(cx + 7, cy - 9, 2.2)]), GOBLIN_DAUB, 0.9)
    # The rope round it, knotted on the front.
    for rx in (14.0, width - 14.0):
        c.put(c.mask(box(rx - 1.3, lid - 1, rx + 1.3, height - 1)), ROPE)
        c.put(c.mask(lambda p: [p.line([(rx - 1.3, y), (rx + 1.3, y + 1.6)], 0.6) for y in np.arange(lid, height - 2, 3)]), scale(ROPE, 0.7))
    c.put(c.mask(lambda p: p.ellipse(width - 14.0, lid + 12, 2.6)), scale(ROPE, 0.85))
    whole = c.mask(box(0, 0, width, height))
    c.tone(whole * np.clip((width * 0.3 - c.x) / width, -0.4, 0.4), 0.22)
    c.tone(whole * np.clip((c.y - height * 0.6) / height, 0, 1), -0.25)


def loading_stage(c, width, height, tag):
    """The siding's loading stage: a deck of planks on trestle legs, the
    height of a wagon's bed, so goods go across onto the freight without
    lifting. Its deck is the walk line; a walker goes under it. Sacks wait
    on the ground beneath for the noon window."""
    rng = c.rand(tag, "stage")
    deck = 8.0
    legs = np.linspace(4, width - 10, 4)
    for lx in legs:
        c.put(c.mask(box(lx, deck, lx + 6, height)), OAK)
        c.put(c.mask(box(lx, deck, lx + 1.6, height)), OAK_LIGHT, 0.6)
    for a, b in zip(legs[:-1], legs[1:]):
        c.put(c.mask(lambda p: p.line([(a + 6, deck + 4), (b, height - 10)], 2.0)), scale(OAK, 0.85))
        c.put(c.mask(lambda p: p.line([(a + 6, height - 10), (b, deck + 4)], 2.0)), scale(OAK, 0.75))
    c.put(c.mask(box(0, deck, width, deck + 3)), scale(OAK, 0.7))
    planks = c.mask(box(0, 0, width, deck))
    c.put(planks, OAK_LIGHT)
    c.put(c.mask(lambda p: [p.rect(x, 0, x + 0.6, deck) for x in np.arange(14, width, 14 + rng.uniform(-1, 1))]) * planks, scale(OAK_LIGHT, 0.7))
    c.tone(planks * np.clip((c.y - 1.0) / deck, 0, 1), -0.3)
    # Sacks under the stage, on the ground.
    for sx in (24.0, 40.0, width - 46.0):
        sack = c.mask(lambda p: p.poly([(sx - 9, height), (sx - 10, height - 12), (sx - 6, height - 19), (sx, height - 21),
                                        (sx + 6, height - 19), (sx + 10, height - 12), (sx + 9, height)]), blur=0.5)
        c.put(sack, scale(BURLAP, rng.uniform(0.9, 1.05)))
        c.tone(sack * np.clip((c.x - sx) / 10.0, -1, 1), -0.18)
        c.put(c.mask(lambda p: p.line([(sx - 3, height - 19), (sx + 3, height - 19)], 1.2)), scale(BURLAP, 0.55))


def notice_on_posts(c, width, height, tag):
    """A railway notice board on two posts: planks painted the railway's
    dark green in an iron frame, for pale words (the room writes them over
    it)."""
    board = 52.0
    for x in (14.0, width - 20.0):
        c.put(c.mask(box(x, board - 4, x + 6, height)), OAK)
    face = c.mask(box(2, 2, width - 2, board))
    c.put(c.mask(box(0, 0, width, board + 2)), IRON)
    c.put(face, (40, 62, 50))
    c.put(c.mask(lambda p: [p.rect(2, y, width - 2, y + 0.6) for y in np.arange(14, board, 13)]) * face, (30, 46, 38))
    c.tone(face * np.clip((c.y - 2) / board, 0, 1), -0.15)


def fingerpost(c, width, height, tag):
    """A fingerpost at the foot of the drove road: an oak post and one dark
    arm pointing east, up the fell (the room writes the way on the arm in
    pale letters)."""
    post_x = 16.0
    c.put(c.mask(box(post_x, 6, post_x + 7, height)), OAK)
    c.put(c.mask(box(post_x, 6, post_x + 2, height)), OAK_LIGHT, 0.6)
    c.put(c.mask(lambda p: p.poly([(post_x - 1, 6), (post_x + 3.5, 1), (post_x + 8, 6)])), scale(OAK, 0.8))
    arm = c.mask(lambda p: p.poly([(post_x - 4, 12), (width - 14, 12), (width - 1, 23), (width - 14, 34), (post_x - 4, 34)]))
    c.put(c.mask(lambda p: p.poly([(post_x - 6, 10.5), (width - 13, 10.5), (width + 1, 23), (width - 13, 35.5), (post_x - 6, 35.5)])), scale(OAK, 0.6))
    c.put(arm, scale(OAK, 0.8))
    c.tone(arm * np.clip((c.y - 12) / 22, 0, 1), -0.15)


def fallen_trunk(c, width, height, tag):
    """A tree the wind brought down across the woods' path: its trunk lies
    level, its top the walk line, on its torn-up root plate at the west end
    and a broken stump at the east. A walker goes under it."""
    rng = c.rand(tag, "trunk")
    log = 22.0
    # The root plate: a disc of earth and roots, torn up on edge.
    plate = c.mask(lambda pen: pen.ellipse(21, height * 0.52, 20, height * 0.47), blur=0.6)
    c.put(plate, (86, 66, 48))
    c.tone(plate * (c.noise((tag, "soil"), 6, 8, 2) - 0.5), 0.35)
    roots = c.mask(lambda pen: [pen.line([(20, height * 0.5), (20 + math.cos(a) * rng.uniform(18, 26), height * 0.5 + math.sin(a) * rng.uniform(22, 32))], rng.uniform(1.2, 2.4))
                                for a in np.linspace(0, math.tau, 13)])
    c.put(roots * plate, scale(BARK, 0.8))
    # The broken stump at the east end, its splintered top under the log.
    sx0, sx1 = width - 40, width - 12
    stump = c.mask(lambda pen: pen.poly([(sx0 - 3, height), (sx0, log - 4), (sx0 + 7, log - 9), (sx0 + 13, log - 3), (sx0 + 20, log - 10), (sx1, log - 4), (sx1 + 3, height)]), blur=0.4)
    c.put(stump, BARK)
    c.put(c.mask(lambda pen: [pen.line([(x, height), (x + rng.uniform(-1, 1), log)], 0.9) for x in np.arange(sx0 + 2, sx1, 4)]) * stump, scale(BARK, 0.65), 0.7)
    # The trunk, level, across the two.
    trunk = c.mask(lambda pen: pen.poly([(0, 0.5), (width - 2, 0.5), (width, log * 0.5), (width - 2, log), (0, log + 0.5)]), blur=0.5)
    c.put(trunk, mix(BARK, OAK_LIGHT, 0.15))
    c.put(c.mask(lambda pen: [pen.line([(x, 2), (x + rng.uniform(4, 9), log - 1)], 0.8) for x in np.arange(16, width - 6, 7)]) * trunk, scale(BARK, 0.6), 0.7)
    c.tone(trunk * np.clip((c.y - 2) / log, 0, 1), -0.3)
    moss = c.mask(lambda pen: [pen.ellipse(rng.uniform(20, width - 10), rng.uniform(0.5, 3), rng.uniform(5, 10), rng.uniform(1.4, 2.6)) for _ in range(8)], blur=0.5)
    c.put(moss * trunk, (88, 120, 60), 0.9)
    # The broken end of the trunk, pale wood, at the stump.
    c.put(c.mask(lambda pen: pen.ellipse(width - 1, log * 0.5, 2.5, log * 0.48)), (206, 176, 128))


def stake_board(c, width, height, tag):
    """A board of the surveyors': a dark-stained oak board nailed to two
    stakes driven into the ground, for a few pale words (the room writes
    them over it)."""
    board = 64.0
    for x in (22.0, width - 28.0):
        stake = c.mask(lambda pen: pen.poly([(x, board - 4), (x + 6, board - 4), (x + 6, height - 3), (x + 3, height), (x, height - 3)]))
        c.put(stake, OAK)
        c.put(c.mask(box(x, board - 4, x + 1.6, height - 3)), OAK_LIGHT, 0.6)
    face = c.mask(box(2, 2, width - 2, board))
    c.put(c.mask(box(0, 0, width, board + 2)), scale(OAK, 0.55))
    c.put(face, scale(OAK, 0.82))
    c.put(c.mask(lambda pen: [pen.rect(2, y, width - 2, y + 0.6) for y in (22.0, 43.0)]) * face, scale(OAK, 0.6))
    c.tone(face * (c.noise((tag, "grain"), 8, 2, 2) - 0.5), 0.15)
    for x in (24.5, width - 25.5):
        for y in (8.0, board - 8.0):
            c.put(c.mask(lambda pen: pen.ellipse(x, y, 1.1)), IRON)


SLATE = (40, 46, 44)
CHALK = (214, 216, 206)


def chalk_slate(c, width, height, tag):
    """A slate in an oak frame, nailed to the workshop's wall, for a line of
    chalk (the room writes it over it): the old wiping shows as a haze."""
    face = c.mask(box(3, 3, width - 3, height - 3))
    c.put(c.mask(box(0, 0, width, height)), OAK)
    c.put(c.mask(box(0, 0, width, 1.2)), OAK_LIGHT, 0.7)
    c.put(face, SLATE)
    c.put(face * c.noise((tag, "wiped"), 18, 3, 3), CHALK, 0.12)
    for x in (1.5, width - 1.5):
        for y in (1.5, height - 1.5):
            c.put(c.mask(lambda pen: pen.ellipse(x, y, 0.9)), IRON)


PIECES.update({
    # The workshop's slates (intro_wake_room), one per width of words.
    **{f"workshop_slate_{w}": _block_piece(w, 32, chalk_slate, f"slate_{w}") for w in (96, 120, 180, 260, 300)},
})


PIECES.update({
    # The surveyors' boards (the lane's line and station, the woods' camp)
    "hill_stake_board": _block_piece(200, 100, stake_board, "stake_board"),
})


PIECES.update({
    # intro_woods: the tree down across the path
    "hill_woods_fallen_trunk": _block_piece(240, 64, fallen_trunk, "woods_fallen_trunk"),
})


PIECES.update({
    # intro_freight_yard: the freight crates (solid blocks), the loading
    # stages (one-way decks), the platform's notice, the drove road's post
    "hill_freight_crates": _block_piece(96, 48, freight_crates, "freight_crates"),
    "hill_goblins_crate": _block_piece(76, 58, goblins_crate, "goblins_crate"),
    "hill_loading_stage": _block_piece(160, 112, loading_stage, "loading_stage"),
    "hill_siding_notice": _block_piece(240, 112, notice_on_posts, "siding_notice"),
    "hill_fingerpost": _block_piece(150, 120, fingerpost, "fingerpost"),
})


def gate_barrier(c, width, height, tag):
    """The barrier across the road by the gate office: a tall leaf of the
    same prefabricated steel, too high to climb, mesh between square posts,
    a red and white bar across it and a hazard band at its foot. It is the
    look of the clearing's `LockWall` and fills its box; the lever slides it
    away."""
    steel = (150, 160, 168)
    c.put(c.mask(lambda pen: [pen.line([(x, 0), (x + height * 0.5, height)], 0.5) for x in np.arange(-height, width, 4)]
                 + [pen.line([(x, 0), (x - height * 0.5, height)], 0.5) for x in np.arange(0, width + height, 4)]), (90, 98, 104), 0.9)
    for x0 in (0, width - 4):
        post = c.mask(box(x0, 0, x0 + 4, height))
        c.put(post, steel)
        c.tone(post * np.clip((x0 + 2 - c.x) / 2, -1, 1), 0.2)
    for y in (2, height * 0.5, height - 14):
        c.put(c.mask(box(0, y, width, y + 3)), scale(steel, 0.85))
    bar_y = height - 64
    bar = c.mask(box(-0.5, bar_y, width + 0.5, bar_y + 7))
    c.put(bar, (236, 236, 230))
    c.put(bar * c.mask(lambda pen: [pen.poly([(x, bar_y), (x + 4, bar_y), (x + 1, bar_y + 7), (x - 3, bar_y + 7)]) for x in np.arange(-4, width + 4, 8)]), (196, 40, 36))
    band = c.mask(box(0, height - 10, width, height))
    c.put(band, (220, 180, 40))
    c.put(band * c.mask(lambda pen: [pen.poly([(x, height - 10), (x + 4, height - 10), (x + 1, height), (x - 3, height)]) for x in np.arange(-4, width + 4, 8)]), (30, 30, 30))
    c.put(c.mask(lambda pen: pen.ellipse(width / 2, 5, 3)), (230, 70, 50))
    c.put(c.mask(lambda pen: pen.ellipse(width / 2 - 0.8, 4.2, 1.2)), (255, 200, 180))


def hollow_oak(c, k):
    """The woods' hollow oak (`intro_woods`, `HOLLOW`): an old trunk split
    open from the ground to the crown's fork. Its inside is climbed on three
    shelves of its own wood (the boards x 1700..1796 at 448, 1600..1696 at
    384, 1700..1796 at 320); between the roots at its foot a dark gap goes
    down (x 1640..1688): the way into the salt run."""
    g = G
    rng = c.rand("hollow_oak", "crown")
    leaf = (66, 104, 56)
    clumps = [(rng.uniform(1470, 1930), rng.uniform(40, 230), rng.uniform(30, 48), rng.uniform(20, 32)) for _ in range(44)]
    crown = c.mask(lambda pen: [pen.ellipse(*cl) for cl in clumps], blur=1.4)
    c.put(crown, leaf)
    c.tone(crown * (c.noise(("hollow_oak", "leaf"), 30, 30, 3) - 0.5), 0.32)
    c.tone(crown * np.clip((c.x - 1700) / 220, -1, 1), -0.16)
    # The trunk, broad and flared, into its two forks.
    outer = [(1500, g), (1556, g - 30), (1572, 300), (1590, 210), (1560, 120), (1600, 112), (1660, 200),
             (1740, 200), (1810, 110), (1850, 118), (1818, 210), (1832, 300), (1846, g - 30), (1906, g)]
    trunk = c.mask(lambda pen: pen.poly(outer), blur=0.5)
    c.put(trunk, BARK)
    c.put(trunk * c.mask(lambda pen: [pen.line([(x, g), (x + rng.uniform(-6, 6), 380), (x + rng.uniform(-8, 8), 220)], 1.1)
                                      for x in np.arange(1560, 1850, 9)]), scale(BARK, 0.68), 0.6)
    c.tone(trunk * np.clip((c.x - 1700) / 120, -1, 1), -0.2)
    # The hollow: the split, dark inside, its rim lighter where the bark
    # curls in.
    hollow = c.mask(lambda pen: pen.arch(1592, 268, 1808, g), blur=0.6)
    c.put(hollow, (40, 28, 20))
    c.tone(hollow * np.clip((c.y - 268) / 244, 0, 1), 0.18)
    rim = c.mask(lambda pen: pen.arch(1586, 262, 1814, g), blur=0.6) * (1 - hollow)
    c.put(rim, OAK_LIGHT, 0.8)
    c.put(hollow * c.mask(lambda pen: [pen.line([(x, g), (x + rng.uniform(-4, 4), 300)], 0.8) for x in np.arange(1600, 1800, 13)]),
          (58, 42, 30), 0.7)
    # Its shelves: lips of its own wood, their tops the walk line.
    for x0, top in ((1700, 448), (1600, 384), (1700, 320)):
        lip = c.mask(lambda pen: pen.poly([(x0 - 2, top), (x0 + 98, top), (x0 + 90, top + 10), (x0 + 6, top + 12)]), blur=0.4)
        c.put(lip, mix(BARK, OAK_LIGHT, 0.5))
        c.put(c.mask(box(x0, top, x0 + 96, top + 2)), OAK_LIGHT)
    # The roots, flaring out over the ground, and the gap between two of
    # them that goes down.
    roots = c.mask(lambda pen: [pen.poly([(1440, g + 6), (1520, g - 24), (1580, g - 10), (1600, g + 4)]),
                                pen.poly([(1820, g + 4), (1846, g - 14), (1900, g - 22), (1970, g + 6)]),
                                pen.poly([(1616, g + 8), (1630, g - 6), (1640, g + 10)]),
                                pen.poly([(1688, g + 10), (1700, g - 6), (1716, g + 8)])], blur=0.6)
    c.put(roots, BARK)
    c.tone(roots * np.clip((c.y - (g - 20)) / 30, 0, 1), -0.25)
    gap = c.mask(lambda pen: pen.ellipse(1664, g + 10, 26, 22), blur=1.0)
    c.put(gap, (14, 10, 8))
    c.put(c.mask(lambda pen: [pen.line([(x, g - 2), (x + rng.uniform(-3, 3), g + 18)], 0.7) for x in np.arange(1644, 1686, 7)]),
          (70, 52, 36), 0.8)


def hatch(c, width, height, tag):
    """A trapdoor of tarred boards in the floor of the millstream's hollow,
    its iron ring: the way down into the salt run."""
    c.put(c.mask(box(0, 2, width, height)), (52, 40, 30))
    c.put(c.mask(lambda pen: [pen.line([(x, 2), (x, height)], 0.6) for x in np.arange(8, width, 8)]), (30, 22, 16), 0.9)
    c.put(c.mask(box(0, 2, width, 4)), (96, 74, 50))
    c.put(c.mask(lambda pen: pen.ring(width / 2, 7, 3.2, 1.2)), IRON)


def lantern(c, width, height, tag):
    """A smugglers' tin lantern on an iron bracket driven into the rock: the
    salt run's lamps (each a `LightSource` in the room). The bracket comes
    from the wall at the top left; the lantern hangs from its end."""
    tin = (70, 66, 60)
    c.put(c.mask(lambda pen: pen.line([(1, 3), (width * 0.62, 3)], 1.4)), IRON)
    c.put(c.mask(lambda pen: pen.line([(width * 0.62, 3), (width * 0.62, 9)], 0.8)), IRON)
    cx = width * 0.62
    body = c.mask(lambda pen: pen.poly([(cx - 6, 14), (cx + 6, 14), (cx + 7, height - 6), (cx - 7, height - 6)]), blur=0.4)
    glass = c.mask(lambda pen: pen.poly([(cx - 4, 16), (cx + 4, 16), (cx + 5, height - 8), (cx - 5, height - 8)]), blur=0.4)
    c.put(body, tin)
    c.put(glass, PAL["lamp"])
    c.put(glass * c.mask(lambda pen: pen.ellipse(cx, height * 0.6, 2.4, 4.0), blur=1.0), (255, 244, 214))
    c.put(c.mask(lambda pen: pen.poly([(cx - 7, 14), (cx, 8), (cx + 7, 14)])), tin)
    c.put(c.mask(box(cx - 8, height - 6, cx + 8, height - 3)), tin)
    c.put(c.mask(lambda pen: pen.ring(cx, 8, 2.0, 0.8)), IRON)


def ladder(c, width, height, tag):
    """The smugglers' ladder up to a trapdoor overhead: two rails of rough
    timber and their rungs, and the trapdoor from below, daylight at its
    seams. The salt run's ways out at both ends."""
    wood, dark = (92, 68, 44), (46, 34, 24)
    door = 14
    c.put(c.mask(box(2, 0, width - 2, door)), dark)
    c.put(c.mask(lambda pen: [pen.line([(x, 1), (x, door - 1)], 0.5) for x in np.arange(10, width - 4, 9)]), (26, 18, 12), 0.9)
    seams = c.mask(lambda pen: [pen.line([(2, door), (width - 2, door)], 0.8), pen.line([(2, 0), (2, door)], 0.6),
                                pen.line([(width - 2, 0), (width - 2, door)], 0.6)], blur=0.8)
    c.put(seams, (255, 236, 190), 0.85)
    for x in (10, width - 10):
        c.put(c.mask(lambda pen: pen.line([(x, door), (x + 1, height)], 2.2), blur=0.3), wood)
        c.put(c.mask(lambda pen: pen.line([(x - 1.5, door), (x - 0.5, height)], 0.6)), dark, 0.6)
    c.put(c.mask(lambda pen: [pen.line([(10, y), (width - 10, y + 1)], 1.6) for y in np.arange(door + 12, height - 4, 16)],
                 blur=0.3), wood)


PIECES.update({
    # intro_salt_run: its ladders up to the hatch and up through the roots
    # (48 x 192, floor to the room's top)
    "hill_salt_run_ladder": _block_piece(48, 192, ladder, "salt_run_ladder"),
})


PIECES.update({
    # intro_woods: the hollow oak, in room coordinates
    "hill_woods_hollow_oak": Piece((1440, 20, 1970, 548), hollow_oak),
    # intro_salt_run: a lamp on its bracket (24 x 40)
    "hill_salt_run_lantern": _block_piece(24, 40, lantern, "salt_run_lantern"),
    # intro_millstream: the hatch in the hollow's floor (48 x 16)
    "hill_salt_run_hatch": _block_piece(48, 16, hatch, "salt_run_hatch"),
})


PIECES.update({
    # intro_gate_clearing: the barrier's look (`LockWall` look, 24 x 176)
    "hill_gate_barrier": _block_piece(24, 176, gate_barrier, "gate_barrier"),
})


# ------------------------------------------------ the village built uphill
#
# `intro_hobford` is a hill room (`village()`): its lower street is at VG
# and the upper street runs along the top of the terrace wall behind it, at
# VU. These pieces are drawn in that room's coordinates; each one says the
# boards it draws (their tops are the walk lines the room places).

VG, VU = 1280, 976
ROOF_SLATE = (84, 92, 104)
WHITEWASH = (232, 228, 214)
DOOR_BLUE = (58, 82, 120)
GLOW = (120, 236, 220)
LASER = (255, 92, 120)


def _porch_at(c, x0, x1, wall_x, floor, tag):
    """`porch` over a floor of the caller's: its boards 48 over `floor`."""
    top = floor - 48
    roof = c.mask(lambda p: p.poly([(x0 - 6, top + 6), (x1, top + 6), (x1, top - 10), (x0 - 6, top - 2)]))
    c.put(roof, ROOF_SLATE)
    c.tone(roof * (c.noise((tag, "porch"), 20, 4, 2) - 0.5), 0.2)
    walk_edge(c, x0 - 6, x1, top)
    for x in (x0 + 4, wall_x - 6 if wall_x < x1 else x1 - 6):
        post(c, x, top + 6, floor, 5)


def _landing(c, x0, x1, y, posts_to=None, tag="landing"):
    """A timber landing whose boards are at `y`: on posts down to `posts_to`,
    or on two brackets from the wall behind it."""
    walk_edge(c, x0, x1, y)
    c.put(c.mask(box(x0, y + 6, x1, y + 10)), scale(OAK, 0.8))
    if posts_to is not None:
        for x in (x0 + 5, x1 - 5):
            post(c, x, y + 6, posts_to, 5)
    else:
        for x in (x0 + 10, x1 - 10):
            c.put(c.mask(lambda p: p.poly([(x - 3, y + 6), (x + 3, y + 6), (x + 3, y + 26), (x - 3, y + 10)])), OAK)
    c.put(c.mask(lambda p: [p.rect(x, y - 18, x + 1.6, y) for x in np.arange(x0 + 2, x1, 12)]), OAK, 0.85)
    c.put(c.mask(box(x0, y - 20, x1, y - 17)), OAK_LIGHT, 0.9)


#: The terrace wall's run, and its buttresses. The wall is drawn in four
#: pieces whose seams are under buttresses: each piece masks only its own
#: stones on its own canvas (one piece of the whole wall took 400 s).
TERRACE_X = (1140, 2400)
BUTTRESSES = (1440, 1740, 2040, 2340)
TERRACE_STAIR = (1120, 1216, VG - 240)


def terrace_bank(c, k):
    """The grass of the bank the upper town is built into, behind the upper
    street (VU), rising east: a field wall along it, bushes, and on the
    street a lamp and two tubs of flowers."""
    x0, x1 = TERRACE_X
    rng = c.rand("terrace", "bank")
    ridge = [(x0, VU), (x0 + 120, VU - 46), (1500, VU - 92), (1800, VU - 118), (2100, VU - 160), (x1, VU - 182), (x1, VU)]
    bank = c.mask(lambda p: p.poly(ridge), blur=0.8)
    c.put(bank, TURF)
    c.tone(bank * (c.noise(("terrace", "turf"), 40, 8, 3) - 0.5), 0.22)
    c.tone(bank * np.clip((c.y - (VU - 180)) / 180, 0, 1), -0.18)
    wall_line = [(x0 + 80, VU - 30), (1500, VU - 70), (1800, VU - 94), (2100, VU - 132), (x1, VU - 152)]
    c.put(c.mask(lambda p: p.line(wall_line, 3.2), blur=0.4), STONE_GREY)
    c.put(c.mask(lambda p: p.line(wall_line, 1.0)), mix(STONE_GREY, (255, 255, 240), 0.4))
    for _ in range(9):
        bx = rng.uniform(x0 + 100, x1 - 40)
        top = np.interp(bx, [px for px, _ in ridge[:-1]], [py for _, py in ridge[:-1]])
        bush = c.mask(lambda p: [p.ellipse(bx + rng.uniform(-12, 12), top + rng.uniform(0, 14), rng.uniform(8, 16), rng.uniform(6, 10)) for _ in range(4)], blur=1.0)
        c.put(bush * bank, GORSE)
        c.tone(bush * bank * np.clip((bx - c.x) / 16, -1, 1), 0.15)
    k.ground = VU
    k.lamp(1470, h=58, lit=0.0, tag="terrace_lamp")
    for tx in (1880, 1930):
        tub = c.mask(lambda p: p.poly([(tx - 10, VU - 16), (tx + 10, VU - 16), (tx + 8, VU), (tx - 8, VU)]))
        c.put(tub, BOARD)
        k.flowerbox(tx - 10, tx + 10, VU - 18, (226, 86, 96), f"terrace_tub{tx}")


def terrace_wall(sx0, sx1):
    """The terrace wall from `sx0` to `sx1`: dressed stone from the lower
    street (VG) up to the upper street (VU), its coping the upper street's
    walk line, ivy and a spout. Its west end carries the stone stair off the
    smithy's loft: a landing x 1120..1216 at VG - 240 on a corbel, and steps
    cut in the wall's face up to the coping."""

    def draw(c, k):
        x0, x1 = max(TERRACE_X[0], sx0), sx1
        rng = c.rand("terrace", "wall", sx0)
        k.wall(x0, VU + 6, x1, VG, mix(LIMESTONE_WARM, STONE_GREY, 0.45), texture="stone", tag=f"terrace_wall{sx0}")
        if sx0 <= 1560 < sx1:
            spout = (1560, VU + 70)
            c.put(c.mask(box(spout[0] - 6, spout[1], spout[0] + 6, spout[1] + 8)), IRON)
            streak = c.mask(lambda p: p.poly([(spout[0] - 5, spout[1] + 8), (spout[0] + 5, spout[1] + 8), (spout[0] + 9, VG), (spout[0] - 9, VG)]), blur=2.0)
            c.put(streak, ALGAE, 0.45)
        ivy = c.mask(lambda p: [p.ellipse(rng.uniform(x0, x1), rng.uniform(VU + 10, VG - 20), rng.uniform(2, 5), rng.uniform(1.5, 3.5))
                                for _ in range(int((x1 - x0) / 5))], blur=0.4)
        ivy_band = np.clip(1 - np.abs(((c.x - TERRACE_X[0]) % 420) - 120) / 90, 0, 1)
        c.put(ivy * ivy_band, (70, 110, 58), 0.85)
        walk_edge(c, x0 - 4, x1, VU, mix(STONE_GREY, LIMESTONE, 0.4))
        for bx in BUTTRESSES:
            if bx + 24 < sx0 or bx - 24 > sx1:
                continue
            butt = c.mask(lambda p: p.poly([(bx - 22, VG), (bx - 14, VU + 30), (bx + 14, VU + 30), (bx + 22, VG)]))
            c.put(butt, mix(LIMESTONE_WARM, STONE_GREY, 0.3))
            c.put(butt * c.mask(lambda p: [p.rect(bx - 24, y, bx + 24, y + 0.7) for y in np.arange(VU + 40, VG, 14)]), scale(STONE_GREY, 0.7), 0.6)
            c.tone(butt * np.clip((bx - c.x) / 22, -1, 1), 0.14)
            c.put(c.mask(lambda p: p.poly([(bx - 16, VU + 30), (bx, VU + 16), (bx + 16, VU + 30)])), STONE_GREY)
        if sx0 <= TERRACE_STAIR[0]:
            lx0, lx1, ly = TERRACE_STAIR
            wx = TERRACE_X[0]
            c.put(c.mask(box(wx - 2, ly, wx + 30, VG)), mix(LIMESTONE_WARM, STONE_GREY, 0.3))
            corbel = c.mask(lambda p: p.poly([(lx0, ly + 10), (lx1, ly + 10), (lx1 - 20, ly + 34), (lx0 + 30, ly + 34)]))
            c.put(corbel, STONE_GREY)
            c.tone(corbel * np.clip((c.y - ly - 10) / 24, 0, 1), -0.25)
            walk_edge(c, lx0, lx1, ly, mix(STONE_GREY, LIMESTONE, 0.4))
            c.put(c.mask(box(lx0, ly + 6, lx1, ly + 10)), scale(STONE_GREY, 0.75))
            for n in range(4):
                sy = ly - 16 * (n + 1)
                c.put(c.mask(box(lx1 - 30 + n * 10, sy, lx1 + 10 + n * 10, sy + 16)), mix(STONE_GREY, LIMESTONE, 0.25 + 0.05 * n))
                c.put(c.mask(box(lx1 - 30 + n * 10, sy, lx1 + 10 + n * 10, sy + 1.4)), mix(LIMESTONE, (255, 250, 230), 0.5))

    return draw


def upper_cottage(c, k):
    """A whitewashed cottage on the upper street: porch boards x 1240..1320 at
    VU - 48, roof x 1280..1440 at VU - 112. On its thatch a satellite dish
    off the freight, pointed at the gate."""
    k.ground = VU
    x0, x1, eave = 1280, 1440, VU - 112
    k.wall(x0, eave, x1, VU, WHITEWASH, texture="plaster", tag="upper_cottage")
    k.eave_shade(x0, x1, eave + 4, 8)
    k.door(1400, 26, 52, DOOR_BLUE, arch=False, tag="upper_cottage_door")
    k.window(1340, eave + 30, 22, 24, shutters=DOOR_BLUE, flowers=(240, 200, 70), tag="upper_cottage_win")
    thatch(c, x0, x1, eave, eave - 62, "upper_cottage_thatch")
    k.chimney(1300, eave - 26, 14, 36, LIMESTONE_WARM, smoke=(236, 236, 236), tag="upper_cottage_chim")
    # The dish: a pale bowl on a bracket strapped to the ridge, its feed arm,
    # and a cable stapled down the thatch to the window.
    dx, dy = 1396, eave - 66
    c.put(c.mask(lambda p: p.line([(dx, dy + 18), (dx, dy + 36)], 1.4)), IRON)
    bowl = c.mask(lambda p: p.ellipse(dx - 4, dy + 6, 11, 14), blur=0.3)
    c.put(bowl, (226, 228, 230))
    c.tone(bowl * np.clip((c.x - dx + 4) / 11, -1, 1), -0.2)
    c.put(c.mask(lambda p: p.line([(dx - 4, dy + 6), (dx + 12, dy + 2)], 0.8)), IRON)
    c.put(c.mask(lambda p: p.ellipse(dx + 13, dy + 2, 1.8)), (60, 60, 64))
    c.put(c.mask(lambda p: p.line([(dx, dy + 36), (1372, eave + 4), (1352, eave + 28)], 0.6)), (30, 30, 30), 0.9)
    _porch_at(c, 1240, 1320, x0, VU, "upper_cottage")


def guild_hall(c, k):
    """The adventurers' guild: three storeys stacked into the bank, x
    1520..1840. Its boards (on the 16 px grid, as the room's boards are): the
    stair's west landing x 1480..1560 at VU - 64,
    the first-floor gallery 1520..1840 at VU - 112, the east landing
    1800..1880 at VU - 176, and the top gallery 1520..1840 at VU - 224, where
    the trophy room's door is (x 1576..1624). By the front door a rack of
    laser swords and a drinks machine off the freight."""
    x0, x1 = 1520, 1840
    first, top, eaves = VU - 112, VU - 224, VU - 336
    # The ground floor: rough stone, the double door, two windows.
    k.ground = VU
    k.wall(x0, first, x1, VU, mix(LIMESTONE_WARM, STONE_GREY, 0.25), texture="stone", tag="guild_ground")
    k.door(1680, 40, 70, OAK, arch=True, glass_lit=0.5, tag="guild_door")
    for cx in (1580, 1780):
        k.window(cx, first + 34, 24, 30, kind="arch", lit=0.45, tag=f"guild_win{cx}")
    # The first floor: oak frame on plaster, jettied out over the gallery.
    k.wall(x0 + 6, top, x1 - 6, first, mix(WHITEWASH, LIMESTONE, 0.4), texture="plaster", tag="guild_first")
    k.timber(x0 + 6, top, x1 - 6, first, OAK, posts=6, tag="guild_first_frame")
    for cx in (1600, 1680, 1760):
        k.window(cx, top + 34, 22, 28, lit=0.35, tag=f"guild_first_win{cx}")
    # The top floor: the trophy room, its window lit the plate's cold green;
    # through it a chair stands on the ceiling.
    k.wall(x0 + 14, eaves, x1 - 14, top, mix(WHITEWASH, LIMESTONE, 0.4), texture="plaster", tag="guild_top")
    k.timber(x0 + 14, eaves, x1 - 14, top, OAK, posts=5, tag="guild_top_frame")
    wx0, wx1, wy0, wy1 = 1690, 1790, eaves + 26, eaves + 82
    pane = c.mask(box(wx0, wy0, wx1, wy1))
    c.put(c.mask(box(wx0 - 3, wy0 - 3, wx1 + 3, wy1 + 3)), OAK)
    c.put(pane, (30, 52, 54))
    c.light(pane * np.clip((wy1 - c.y) / (wy1 - wy0), 0, 1), GLOW, 0.55)
    chair = c.mask(lambda p: (p.rect(1726, wy0, 1729, wy0 + 18), p.rect(1748, wy0, 1751, wy0 + 18),
                              p.rect(1724, wy0 + 18, 1753, wy0 + 22), p.rect(1724, wy0 + 22, 1727, wy0 + 40)))
    c.put(chair * pane, (40, 30, 24))
    c.put(c.mask(lambda p: [p.rect(x, wy0, x + 1.4, wy1) for x in (1723, 1757)]) * pane, OAK)
    c.put(c.mask(box(wx0, (wy0 + wy1) / 2, wx1, (wy0 + wy1) / 2 + 1.4)), OAK)
    # The trophy room's door on the top gallery.
    k.ground = top
    k.door(1600, 30, 58, DOOR_RED, arch=True, step=False, glass_lit=0.3, tag="guild_top_door")
    # The roof, and on its ridge a weathervane cut as a laser sword.
    k.gable(x0 + 14, x1 - 14, eaves, 72, ROOF_SLATE, tiles="slate", overhang=16, tag="guild_roof")
    vx, vy = 1680, eaves - 72
    c.put(c.mask(lambda p: p.line([(vx, vy), (vx, vy - 26)], 1.2)), IRON)
    c.put(c.mask(lambda p: p.line([(vx - 14, vy - 26), (vx - 4, vy - 26)], 2.0)), (60, 60, 66))
    blade = c.mask(lambda p: p.line([(vx - 4, vy - 26), (vx + 22, vy - 26)], 1.8), blur=0.6)
    c.put(blade, LASER)
    c.light(c.mask(lambda p: p.line([(vx - 4, vy - 26), (vx + 22, vy - 26)], 4.0), blur=3), LASER, 0.5)
    k.chimney(1560, eaves - 20, 16, 46, LIMESTONE_WARM, smoke=(236, 236, 236), tag="guild_chim")
    # The galleries and the stair's landings.
    for y in (first, top):
        walk_edge(c, x0, x1, y)
        c.put(c.mask(box(x0, y + 6, x1, y + 12)), scale(OAK, 0.85))
        c.put(c.mask(lambda p: [p.poly([(x, y + 12), (x + 6, y + 12), (x + 3, y + 22)]) for x in np.arange(x0 + 10, x1 - 10, 40)]), OAK)
        c.put(c.mask(lambda p: [p.rect(x, y - 20, x + 1.8, y) for x in np.arange(x0 + 4, x1, 14)]), OAK, 0.85)
        c.put(c.mask(box(x0, y - 22, x1, y - 18)), OAK_LIGHT)
    _landing(c, 1480, 1560, VU - 64, posts_to=VU, tag="guild_west_landing")
    _landing(c, 1800, 1880, VU - 176, tag="guild_east_landing")
    # The guild's sign: crossed swords on a board, one blade glowing.
    sx, sy = 1846, first + 20
    c.put(c.mask(lambda p: (p.line([(x1, sy - 6), (sx + 30, sy - 6)], 1.4), p.line([(x1, sy + 8), (sx + 4, sy - 6)], 0.8))), IRON)
    board = c.mask(box(sx, sy, sx + 32, sy + 26))
    c.put(board, BOARD)
    c.put(c.mask(lambda p: p.line([(sx + 6, sy + 22), (sx + 26, sy + 4)], 1.4)), (196, 196, 200))
    c.put(c.mask(lambda p: p.line([(sx + 6, sy + 4), (sx + 26, sy + 22)], 1.6), blur=0.5), LASER)
    c.light(c.mask(lambda p: p.line([(sx + 6, sy + 4), (sx + 26, sy + 22)], 3.0), blur=2), LASER, 0.4)
    # By the door: the rack of laser swords, hilts up, blades dark but one,
    # and the drinks machine humming beside the old oak.
    k.ground = VU
    rx = 1622
    c.put(c.mask(box(rx - 16, VU - 40, rx + 16, VU - 36)), OAK)
    c.put(c.mask(box(rx - 16, VU - 6, rx + 16, VU)), OAK)
    for n, hx in enumerate((rx - 10, rx, rx + 10)):
        c.put(c.mask(box(hx - 1.6, VU - 52, hx + 1.6, VU - 36)), (70, 70, 76))
        c.put(c.mask(box(hx - 3, VU - 38, hx + 3, VU - 36)), (176, 140, 72))
        if n == 1:
            c.put(c.mask(box(hx - 1.2, VU - 36, hx + 1.2, VU - 6), blur=0.4), (120, 210, 255))
            c.light(c.mask(box(hx - 3, VU - 36, hx + 3, VU - 6), blur=3), (120, 210, 255), 0.5)
    mx0, mx1 = 1712, 1748
    c.put(c.mask(box(mx0, VU - 70, mx1, VU)), (176, 34, 40))
    c.put(c.mask(box(mx0, VU - 70, mx1, VU - 68)), (220, 90, 90))
    c.put(c.mask(box(mx0 + 4, VU - 62, mx1 - 14, VU - 26)), (230, 236, 240))
    c.light(c.mask(box(mx0 + 4, VU - 62, mx1 - 14, VU - 26)), (255, 255, 255), 0.3)
    c.put(c.mask(lambda p: [p.rect(mx0 + 6, y, mx1 - 16, y + 3) for y in np.arange(VU - 58, VU - 30, 7)]), (70, 120, 200), 0.8)
    c.put(c.mask(box(mx1 - 11, VU - 56, mx1 - 5, VU - 40)), (40, 40, 44))
    c.put(c.mask(box(mx0 + 4, VU - 18, mx1 - 4, VU - 10)), (30, 30, 32))


def watch_tower(c, k):
    """The old watch tower at the upper street's east end, x 2060..2220: a
    stone base to VU - 128 (its top a floor across it), a timber stage above
    it with landings climbing alternate sides (x 2140..2220 at VU - 192, x
    2060..2140 at VU - 256, x 2140..2220 at VU - 320, x 2060..2140 at VU -
    384) to the lookout x 2040..2240 at VU - 448 under a pyramid roof; its
    first step a landing x 2040..2120 at VU - 64. On the lookout an imported
    floodlight is clamped to the rail."""
    x0, x1 = 2060, 2220
    base_top, look = VU - 128, VU - 448
    # The timber stage first, so the base and landings draw over its feet.
    for x in (x0 + 6, x1 - 6):
        post(c, x, look, base_top, 8)
    rng = c.rand("tower", "braces")
    for y0 in range(base_top, look, -64):
        y1 = y0 - 64
        c.put(c.mask(lambda p: p.line([(x0 + 8, y0), (x1 - 8, y1)] if (y0 // 64) % 2 else [(x0 + 8, y1), (x1 - 8, y0)], 2.6)), scale(OAK, 0.9))
    # The base: big squared stones, a round-headed doorway, an arrow slit.
    k.ground = VU
    k.wall(x0, base_top, x1, VU, mix(STONE_GREY, LIMESTONE, 0.35), texture="stone", tag="tower_base")
    door = c.mask(lambda p: p.arch(2120, VU - 74, 2160, VU))
    c.put(c.mask(lambda p: p.arch(2116, VU - 78, 2164, VU)), mix(STONE_GREY, LIMESTONE, 0.6))
    c.put(door, (36, 30, 26))
    c.put(c.mask(box(2186, VU - 104, 2192, VU - 74)), (30, 26, 24))
    walk_edge(c, x0 - 2, x1 + 2, base_top, mix(STONE_GREY, LIMESTONE, 0.5))
    _landing(c, 2040, 2120, VU - 64, posts_to=VU, tag="tower_step")
    for n, (lx0, lx1, ly) in enumerate(((2140, 2220, VU - 192), (2060, 2140, VU - 256),
                                         (2140, 2220, VU - 320), (2060, 2140, VU - 384))):
        walk_edge(c, lx0, lx1, ly)
        c.put(c.mask(box(lx0, ly + 6, lx1, ly + 10)), scale(OAK, 0.8))
    # The lookout: its deck, rail, the posts of its roof and the roof.
    walk_edge(c, 2040, 2240, look)
    c.put(c.mask(box(2040, look + 6, 2240, look + 12)), scale(OAK, 0.8))
    c.put(c.mask(lambda p: [p.rect(x, look - 22, x + 2, look) for x in np.arange(2042, 2240, 12)]), OAK, 0.9)
    c.put(c.mask(box(2040, look - 24, 2240, look - 20)), OAK_LIGHT)
    for x in (2046, 2234):
        post(c, x, look - 76, look, 5)
    roof = c.mask(lambda p: p.poly([(2026, look - 72), (2254, look - 72), (2140, look - 128)]))
    c.put(roof, ROOF_SLATE)
    c.tone(roof * (c.noise(("tower", "roof"), 18, 8, 2) - 0.5), 0.18)
    c.put(c.mask(lambda p: p.line([(2026, look - 72), (2140, look - 128)], 2.0)), mix(ROOF_SLATE, (255, 240, 220), 0.4))
    c.put(c.mask(box(2026, look - 74, 2254, look - 70)), scale(ROOF_SLATE, 0.6))
    # The bell under the roof, and a pennant on the finial.
    bell = c.mask(lambda p: p.poly([(2132, look - 48), (2148, look - 48), (2152, look - 34), (2128, look - 34)]))
    c.put(c.mask(lambda p: p.line([(2140, look - 70), (2140, look - 48)], 0.8)), IRON)
    c.put(bell, (176, 140, 72))
    c.put(c.mask(lambda p: p.line([(2140, look - 128), (2140, look - 158)], 1.0)), IRON)
    c.put(c.mask(lambda p: p.poly([(2140, look - 158), (2168, look - 152), (2140, look - 146)])), DOOR_RED)
    # The floodlight off the freight: a grey can on a yoke clamped to the
    # rail, its cable looped down the post.
    fx, fy = 2222, look - 34
    c.put(c.mask(lambda p: p.line([(fx - 8, look - 22), (fx - 8, fy + 6)], 1.4)), (90, 90, 96))
    can = c.mask(lambda p: p.poly([(fx - 16, fy - 6), (fx + 2, fy - 10), (fx + 4, fy + 8), (fx - 16, fy + 6)]))
    c.put(can, (150, 154, 160))
    c.put(c.mask(lambda p: p.ellipse(fx + 3, fy - 1, 3, 9)), (250, 250, 230))
    c.light(c.mask(lambda p: p.ellipse(fx + 3, fy - 1, 10, 14), blur=6), (255, 250, 220), 0.4)
    cable = [(fx - 8, fy + 6), (fx - 2, look + 20), (x1 - 6, look + 60), (x1 - 4, base_top)]
    c.put(c.mask(lambda p: p.line(cable, 0.7)), (24, 24, 24), 0.9)


#: The guild's trophy room (`intro_guild_trophy_room`): floor at 384, the
#: ceiling's underside at 64, the gravity plate's field over x 480..1248.
TROPHY_FLOOR, TROPHY_CEILING, PLATE_X = 384, 64, 480


def trophy_room(c, k):
    """The guild's top room, from inside. By the door (the west end) all is
    as it should be: a counter, a coat stand, the guild's book. Past it the
    imported gravity plate in the floor, fitted upside down: there down is
    up, so the guild furnished the ceiling (a rug, a table and its chairs, a
    tankard) and hung its trophies on the floor (the chandelier stands up
    off the boards, the banners rise, the heads on their shields are the
    wrong way up)."""
    f, ceil, x1 = TROPHY_FLOOR, TROPHY_CEILING, 1248
    # The back wall: oak panels under a plaster frieze.
    wall = c.mask(box(32, ceil, x1, f))
    c.put(wall, mix(OAK_LIGHT, LIMESTONE, 0.35))
    c.put(c.mask(lambda p: [p.rect(x, ceil, x + 2, f) for x in np.arange(32, x1, 64)]) * wall, scale(OAK, 0.9), 0.7)
    c.put(c.mask(lambda p: [p.rect(32, y, x1, y + 2) for y in (ceil + 40, f - 70)]), scale(OAK, 0.9), 0.8)
    c.tone(wall * (c.noise(("trophy", "panel"), 20, 6, 3) - 0.5), 0.14)
    # The plate's field: a cold shimmer rising off the floor.
    field = c.mask(box(PLATE_X, ceil, x1, f))
    streaks = np.clip(1 - np.abs(((c.x - PLATE_X) % 37.0) - 18) / 2.0, 0, 1) * np.clip((c.y - ceil) / (f - ceil), 0, 1)
    c.light(field * streaks, GLOW, 0.22)
    c.light(field * np.clip((c.y - (f - 60)) / 60, 0, 1), GLOW, 0.25)
    # The plate in the floor, its hexes lit, stencilled THIS SIDE UP with
    # the arrow pointing at the boards.
    plate = c.mask(box(PLATE_X + 8, f - 6, x1 - 8, f))
    c.put(plate, (60, 70, 76))
    c.light(plate * c.mask(lambda p: [p.ellipse(x, f - 3, 5, 2) for x in np.arange(PLATE_X + 20, x1 - 10, 14)]), GLOW, 0.9)
    for ax in (PLATE_X + 60, 860, 1160):
        c.put(c.mask(lambda p: (p.rect(ax - 1.5, f - 34, ax + 1.5, f - 14), p.poly([(ax - 6, f - 14), (ax + 6, f - 14), (ax, f - 8)]))), (240, 200, 60))
    # The west end: the counter, the guild's book on it, a coat stand.
    c.put(c.mask(box(180, f - 46, 300, f)), OAK)
    c.put(c.mask(box(176, f - 50, 304, f - 44)), OAK_LIGHT)
    c.put(c.mask(box(220, f - 56, 252, f - 50)), (120, 40, 36))
    c.put(c.mask(box(222, f - 57, 250, f - 55)), PAPER)
    c.put(c.mask(lambda p: p.ellipse(280, f - 53, 4, 3)), (176, 140, 72))
    c.put(c.mask(lambda p: (p.rect(372, f - 96, 375, f), p.rect(362, f - 4, 386, f), p.line([(373, f - 92), (360, f - 84)], 1.2),
                             p.line([(373, f - 92), (386, f - 84)], 1.2))), OAK)
    cloak = c.mask(lambda p: p.poly([(360, f - 84), (366, f - 86), (370, f - 40), (354, f - 44)]))
    c.put(cloak, (70, 60, 110))
    # The ceiling's furniture, standing on the ceiling: the rug, the table
    # (its legs up into the ceiling) and two chairs, a tankard on the table.
    c.put(c.mask(box(700, ceil, 1000, ceil + 4)), (150, 50, 50))
    c.put(c.mask(lambda p: [p.rect(x, ceil, x + 6, ceil + 4) for x in np.arange(704, 1000, 18)]), (210, 170, 90), 0.8)
    for lx in (790, 900):
        c.put(c.mask(box(lx, ceil + 4, lx + 5, ceil + 40)), OAK)
    c.put(c.mask(box(770, ceil + 40, 926, ceil + 47)), OAK_LIGHT)
    tank = c.mask(box(840, ceil + 47, 852, ceil + 62))
    c.put(tank, (150, 150, 156))
    c.put(c.mask(lambda p: p.ring(855, ceil + 54, 4, 1.2)), (150, 150, 156))
    for cx, back in ((734, 0), (944, 15)):
        c.put(c.mask(lambda p: (p.rect(cx, ceil + 4, cx + 3, ceil + 26), p.rect(cx + 15, ceil + 4, cx + 18, ceil + 26),
                                 p.rect(cx - 1, ceil + 26, cx + 19, ceil + 30), p.rect(cx + back, ceil + 30, cx + back + 3, ceil + 58),
                                 p.rect(cx + back - 1, ceil + 52, cx + back + 4, ceil + 55))), OAK)
    # The trophies, hung on the floor: the chandelier stands up off the
    # boards on its chain, its candles' flames pointing down.
    chx = 640
    c.put(c.mask(lambda p: p.line([(chx, f), (chx, f - 60)], 1.0)), IRON)
    c.put(c.mask(lambda p: p.ellipse(chx, f - 70, 34, 6)), IRON)
    for dx in (-30, -15, 0, 15, 30):
        c.put(c.mask(box(chx + dx - 2, f - 88, chx + dx + 2, f - 72)), PAPER)
        flame = c.mask(lambda p: p.poly([(chx + dx - 2.5, f - 88), (chx + dx + 2.5, f - 88), (chx + dx, f - 98)]), blur=0.4)
        flame = c.mask(lambda p: p.ellipse(chx + dx, f - 92, 2.2, 4), blur=0.5)
        c.put(flame, (255, 210, 120))
        c.light(c.mask(lambda p: p.ellipse(chx + dx, f - 92, 8), blur=5), (255, 200, 120), 0.4)
    # Banners rising from the floor, the guild's crossed swords on them.
    for bx, colour in ((1060, (60, 80, 140)), (1180, (130, 40, 40))):
        c.put(c.mask(box(bx - 1, f - 150, bx + 1, f)), IRON)
        ban = c.mask(lambda p: p.poly([(bx - 20, f - 20), (bx + 20, f - 20), (bx + 20, f - 140), (bx, f - 156), (bx - 20, f - 140)]))
        c.put(ban, colour)
        c.put(c.mask(lambda p: (p.line([(bx - 10, f - 110), (bx + 10, f - 50)], 1.4), p.line([(bx + 10, f - 110), (bx - 10, f - 50)], 1.4))), (220, 200, 140))
        c.put(c.mask(box(bx - 22, f - 22, bx + 22, f - 18)), OAK)
    # The heads on their shields, upside down on the back wall: a goblin's
    # helmet and a cloud sheep's fleece in a jar.
    for hx, kind in ((760, "helmet"), (930, "cloud")):
        hy = f - 120
        shield = c.mask(lambda p: p.poly([(hx - 22, hy + 30), (hx + 22, hy + 30), (hx + 22, hy - 4), (hx, hy - 24), (hx - 22, hy - 4)]))
        c.put(shield, OAK)
        c.put(c.mask(lambda p: p.poly([(hx - 18, hy + 26), (hx + 18, hy + 26), (hx + 18, hy - 2), (hx, hy - 19), (hx - 18, hy - 2)])), mix(OAK_LIGHT, OAK, 0.4))
        if kind == "helmet":
            helm = c.mask(lambda p: (p.ellipse(hx, hy + 6, 12, 10), p.poly([(hx - 14, hy + 6), (hx - 22, hy - 6), (hx - 10, hy + 2)]),
                                     p.poly([(hx + 14, hy + 6), (hx + 22, hy - 6), (hx + 10, hy + 2)])))
            c.put(helm, (110, 120, 70))
            c.put(c.mask(box(hx - 8, hy + 8, hx + 8, hy + 11)), (30, 30, 30))
        else:
            jar = c.mask(lambda p: p.ellipse(hx, hy + 6, 11, 14))
            c.put(jar, (200, 220, 236), 0.6)
            c.put(c.mask(lambda p: [p.ellipse(hx + dx, hy + 6 + dy, 6) for dx, dy in ((-3, 2), (3, 4), (0, -3))], blur=1.0), (250, 250, 252))
            c.put(c.mask(box(hx - 7, hy + 18, hx + 7, hy + 22)), (176, 140, 72))


PIECES.update({
    # intro_hobford, the hill room: the terrace wall under the upper street
    # and the bank behind it; the upper street's cottage, guild and tower.
    "hill_village_terrace_bank": Piece((1100, VU - 200, 2400, VU + 2), terrace_bank),
    **{f"hill_village_terrace_wall_{n}": Piece((x0, VU - 8, x1, VG), terrace_wall(x0, x1))
       for n, (x0, x1) in enumerate(((1100, 1440), (1440, 1740), (1740, 2040), (2040, 2400)))},
    "hill_village_upper_cottage": Piece((1220, VU - 220, 1460, VU), upper_cottage),
    "hill_village_guild_hall": Piece((1440, VU - 460, 1900, VU), guild_hall),
    "hill_village_watch_tower": Piece((2010, VU - 620, 2270, VU), watch_tower),
    # intro_guild_trophy_room: the room seen from inside, in its coordinates
    "hill_guild_trophy_room": Piece((32, TROPHY_CEILING, 1248, TROPHY_FLOOR), trophy_room),
})


def _ground_at_the_floor(draw, ground):
    """A piece stands on its room's ground: doors and lamps on it."""

    def drawn(c, k):
        k.ground = ground
        draw(c, k)

    return drawn


PIECES = {
    name: Piece(p.frame, _ground_at_the_floor(p.draw, UPPER if p.frame[3] == UPPER else G), p.px, p.traits)
    for name, p in PIECES.items()
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PAL", "PIECES", "TARGETS"]
