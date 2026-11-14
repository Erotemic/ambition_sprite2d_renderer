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
- `hill_village_well`: over the well (x 1250..1314, top 464): its posts, roof,
  windlass and bucket.
- `hill_village_notice_board`: the board under the room's three notices
  (their middles at x 2000, y 312..396): oak posts, a little roof.

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
  hut whose limbs are the room's boards (`OAK_LIMBS`, each 140 long: x
  1080 at 544, 920 at 480, 1080 at 416, 920 at 352, 1080 at 288).
- `hill_gate_office` (`intro_gate_clearing`): the guard post under its
  roof board (x 1380..1560 at 480): new prefabricated steel on a stone
  footing, a window with a counter, a cable run, a lamp.

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
    k.chimney(500, ROOF - 30, 14, 40, LIMESTONE_WARM, smoke=(236, 236, 236), tag="cottage_chim")
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
    k.chimney(1530, ROOF - 40, 16, 50, LIMESTONE_WARM, smoke=(236, 236, 236), tag="inn_chim")
    k.chimney(1760, ROOF - 40, 16, 50, LIMESTONE_WARM, tag="inn_chim2")
    porch(c, 1460, 1540, x0, "inn")
    # Barrels by the bar's door.
    for bx in (1606, 1620):
        barrel = c.mask(lambda p: p.ellipse(bx, G - 12, 7, 12))
        c.put(barrel, BOARD)
        c.put(c.mask(lambda p: [p.rect(bx - 7, y, bx + 7, y + 1.4) for y in (G - 19, G - 6)]) * barrel, IRON)


def well(c, k):
    x0, x1 = 1250, 1314
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
    x0, x1, y0, y1 = 1770, 2230, 300, 404
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
    g = UPPER
    limbs = [(1080, 544), (920, 480), (1080, 416), (920, 352), (1080, 288)]
    tx = 1066
    bark = (96, 74, 54)
    leaf = (74, 112, 60)
    # The crown first, behind the boughs: clumps round each limb and the top,
    # so each board reads against leaves, not sky.
    rng = c.rand("oak", "crown")
    clumps = []
    for x, y in limbs:
        for _ in range(9):
            clumps.append((rng.uniform(x - 10, x + 150), rng.uniform(y - 46, y + 6), rng.uniform(20, 32), rng.uniform(14, 22)))
    for _ in range(10):
        clumps.append((rng.uniform(960, 1180), rng.uniform(214, 270), rng.uniform(26, 40), rng.uniform(18, 26)))
    crown = c.mask(lambda p: [p.ellipse(*cl) for cl in clumps], blur=1.4)
    c.put(crown, leaf)
    c.tone(crown * (c.noise(("oak", "leaf"), 30, 30, 3) - 0.5), 0.32)
    c.tone(crown * np.clip((c.x - 1070) / 170, -1, 1), -0.16)
    c.put(crown * c.mask(lambda p: [p.ellipse(cx - rx * 0.3, cy - ry * 0.35, rx * 0.5, ry * 0.4) for cx, cy, rx, ry in clumps], blur=2.0), mix(leaf, (220, 236, 160), 0.35), 0.5)
    # The trunk, forking into the crown.
    trunk = c.mask(lambda p: (p.poly([(tx - 30, g), (tx - 16, 330), (tx + 20, 330), (tx + 34, g)]),
                              p.poly([(tx - 16, 336), (tx - 40, 250), (tx - 26, 246), (tx, 320)]),
                              p.poly([(tx + 20, 336), (tx + 44, 254), (tx + 30, 250), (tx + 2, 320)])))
    c.put(trunk, bark)
    c.put(trunk * c.mask(lambda p: [p.line([(tx - 24 + i * 7, g), (tx - 12 + i * 4, 330)], 0.9) for i in range(9)]), scale(bark, 0.7), 0.6)
    c.tone(trunk * np.clip((c.x - tx) / 30, 0, 1), -0.2)
    # Each limb: a bough from the trunk out along its board; its top is the
    # walk line.
    for x, y in limbs:
        east = x >= tx - 20
        near, far = (tx + 20, x + 140) if east else (tx - 16, x)
        bough = c.mask(lambda p: p.poly([(near, y + 26), (far, y + 8), (far, y), (near, y - 2)]))
        c.put(bough, bark)
        c.tone(bough * np.clip((c.y - y) / 26, 0, 1), -0.25)
        c.put(c.mask(box(min(near, far), y, max(near, far), y + 1.8)), mix(bark, (255, 236, 200), 0.4))


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
    "hill_village_well": Piece((1236, 370, 1328, 470), well),
    "hill_village_notice_board": Piece((1750, 280, 2250, 512), notice_board),
    # intro_millstream
    "hill_village_mill": Piece((1500, 220, 2080, 512), mill),
    # intro_hobford_lane
    "hill_survey_station": Piece((960, 560, 1200, 672), survey_station),
    # intro_high_meadow
    "hill_meadow_oak": Piece((880, 200, 1260, 672), meadow_oak),
    # intro_gate_clearing
    "hill_gate_office": Piece((1370, 460, 1570, 672), gate_office),
}


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
