"""The steam plant under the Eureka quad (`eureka_steam_plant`, the science
dimension): down the manhole in the quad's street, the plant that heats the
institute (and the experiments it is not told about), east into the
Collider; behind a bricked door at its west end, the institute's first lab.

Drawn in room coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/eureka/make_specs.py` (`quad`, `plant`,
`first_lab`): the quad's street (y 768, its foot 896) and its manhole
(x 880..944); the plant's floor (y 928), vault (to y 48), the manhole's
shaft (x 720..784; its ladder the engine's), the walks (`WALKS`: catwalks
and boiler tops, walked on), the bricked door (x 16..48, 112 high); the
first lab's floor (y 512), vault (to y 48).

- `quad_manhole`: the manhole in the street, its cover off and leant by,
  the shaft dark.
- `plant_west`: brick and riveted iron; the upper catwalk on its brackets;
  the manhole's shaft in its fall of daylight; the great pipes overhead,
  lagged, a valve wheel the size of a cartwheel; the tool board.
- `plant_east`: two boilers (their tops walked on), their gauges (one in
  the red, labelled FINE), fireboxes glowing; the lower catwalk and its
  step; the pipes running on east into the Collider.
- `plant_bricked_door`: an old doorway bricked over, LAB 0 over it in
  faded paint, cracked (the look of a breakable wall: hit it).
- `first_lab_room`: where the institute began: a kitchen table for a bench,
  a kettle, coil diagrams on a blackboard, the first coil in a jam jar,
  a camp bed and a sample cabinet.

Animations: ``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .castle_godwin import lettering
from .eureka_props import BOARD, CHALK, COPPER, COPPER_DARK, OAK, OAK_DARK, PAL, PAPER

STREET, QUAD_H = 768, 896
MANHOLE = (880, 944)
W, H, FLOOR, CEIL = 2400, 992, 928, 48
SHAFT = (720, 784)
#: The walks (x0, x1, y): the upper catwalk, the step, the lower catwalk,
#: the boilers' tops.
WALKS = ((16, 1500, 400), (1540, 1700, 528), (900, 2240, 656), (1080, 1280, 800), (1760, 1960, 800))
RETURN_STEPS = ((1440, 1536, 464), (1728, 1824, 592))
UPPER_RAIL_OPENING = (728, 776)
LOWER_RAIL_OPENING = (2104, 2152)
DOOR = (16, 48, FLOOR - 112)
LAB_W, LAB_FLOOR, LAB_CEIL = 640, 512, 48
BRICK = (150, 92, 70)
BRICK_DARK = (110, 66, 50)
MORTAR = (186, 170, 150)
IRON = (70, 74, 80)
IRON_LIGHT = (130, 136, 144)
RIVET = (170, 176, 184)
LAGGING = (214, 206, 180)
FIRE = (255, 150, 60)
GAUGE = (240, 236, 220)
RED = (214, 72, 60)
DAYLIGHT = (250, 244, 220)
STONE = (150, 150, 146)


def bricks(c, x0, x1, y0, y1, seed):
    wall = c.mask(box(x0, y0, x1, y1))
    c.put(wall, BRICK)
    c.put(wall * c.mask(lambda p: [p.rect(x0, y, x1, y + 1.4) for y in range(int(y0), int(y1), 12)]), MORTAR, 0.7)
    c.put(wall * c.mask(lambda p: [p.rect(x + (12 if (y // 12) % 2 else 0), y, x + 1.4 + (12 if (y // 12) % 2 else 0), y + 12)
                                   for y in range(int(y0), int(y1), 12) for x in range(int(x0), int(x1), 24)]), MORTAR, 0.6)
    c.tone(wall * (c.noise(seed, 30, 12, 2) - 0.5), 0.22)
    c.put(wall * (c.noise(seed + "_soot", 10, 6, 3) > 0.8), (40, 34, 32), 0.2)
    c.tone(wall * np.clip((y0 + 160 - c.y) / 140, 0, 1), -0.35)
    return wall


def vault(c, x0, x1):
    c.put(c.mask(box(x0, 16, x1, CEIL)), IRON)
    c.put(c.mask(lambda p: [p.ellipse(x, CEIL - 6, 2.4) for x in range(int(x0) + 10, int(x1), 24)]), RIVET)


def catwalk(c, x0, x1, y, opening=None):
    c.put(c.mask(box(x0, y, x1, y + 8)), IRON)
    c.put(c.mask(lambda p: [p.rect(x, y + 1, x + 10, y + 7) for x in range(int(x0) + 4, int(x1) - 10, 14)]), (36, 38, 42))
    rails = ((x0, x1),) if opening is None else ((x0, opening[0]), (opening[1], x1))
    c.put(c.mask(lambda p: ([(p.rect(a, y - 34, b, y - 31), p.rect(b - 3, y - 34, b, y)) for a, b in rails],
                           [p.rect(x, y - 34, x + 3, y) for a, b in rails for x in range(a, b, 80)])), IRON_LIGHT)
    c.put(c.mask(lambda p: [p.line([(x, y + 8), (x + 30, y + 40)], 3) for x in range(int(x0) + 40, int(x1) - 30, 240)]), IRON)


def pipe(c, pts, r, colour=IRON):
    c.put(c.mask(lambda p: p.line(pts, 2 * r)), colour)
    c.put(c.mask(lambda p: p.line([(x, y - r * 0.5) for x, y in pts], r * 0.5)), mix(colour, (255, 255, 255), 0.25))


def manhole(c, k):
    x0, x1 = MANHOLE
    sh = c.mask(box(x0, STREET, x1, QUAD_H))
    c.put(sh, (40, 40, 44))
    c.tone(sh * np.clip((c.y - STREET) / 80, 0, 1), -0.6)
    c.put(c.mask(lambda p: [p.rect(x, STREET - 4, x + 10, STREET + 4) for x in (x0 - 10, x1)]), STONE)
    # The cover, off and leant against the kerb.
    cover = c.mask(lambda p: p.ellipse(x1 + 26, STREET - 18, 8, 18))
    c.put(cover, IRON)
    c.put(cover * c.mask(lambda p: [p.rect(x1 + 18, y, x1 + 34, y + 1.4) for y in range(STREET - 34, STREET, 6)]), IRON_LIGHT)


def west(c, k):
    bricks(c, 16, 1200, CEIL, FLOOR, "plant_w")
    vault(c, 16, 1200)
    s0, s1 = SHAFT
    c.put(c.mask(box(s0, 16, s1, CEIL)), (40, 40, 44))
    c.light(c.mask(lambda p: p.poly([(s0, 16), (s1, 16), (s1 + 40, FLOOR), (s0 - 40, FLOOR)]), blur=12), DAYLIGHT, 0.14)
    # The great pipes overhead, lagged; the valve wheel.
    pipe(c, [(16, 120), (1200, 120)], 22, LAGGING)
    c.put(c.mask(lambda p: [p.rect(x, 98, x + 4, 142) for x in range(40, 1200, 90)]), scale(LAGGING, 0.8))
    pipe(c, [(16, 200), (600, 200), (640, 240), (1200, 240)], 12)
    wx, wy = 300, 280
    c.put(c.mask(lambda p: (p.ring(wx, wy, 46, 6), p.line([(wx - 46, wy), (wx + 46, wy)], 4), p.line([(wx, wy - 46), (wx, wy + 46)], 4), p.ellipse(wx, wy, 10))), RED)
    c.put(c.mask(lambda p: p.rect(wx - 4, 200, wx + 4, wy - 40)), IRON)
    # The tool board: spanners in a row, one missing (its outline).
    tb = (900, 500, 1160, 620)
    c.put(c.mask(box(*tb)), OAK)
    for i, x in enumerate(range(tb[0] + 20, tb[2] - 10, 34)):
        ln = 50 + i * 8
        col = IRON_LIGHT if i != 3 else (60, 40, 30)
        c.put(c.mask(lambda p: (p.line([(x, tb[1] + 14), (x, tb[1] + 14 + ln)], 4), p.ring(x, tb[1] + 12, 7, 3))), col)
    walks(c)


def walks(c):
    """The boilers and the catwalks, whole: each piece draws them all and
    keeps what is in its frame (the lower catwalk and a boiler cross the
    seam between the two)."""
    b1, b2 = WALKS[3], WALKS[4]
    boiler(c, b1[0], b1[1], b1[2], "b1", red=False)
    boiler(c, b2[0], b2[1], b2[2], "b2", red=True)
    catwalk(c, *WALKS[0], opening=UPPER_RAIL_OPENING)
    catwalk(c, *WALKS[1])
    catwalk(c, *WALKS[2], opening=LOWER_RAIL_OPENING)
    for left, right, top in RETURN_STEPS:
        catwalk(c, left, right, top)
        c.put(c.mask(box(left, top, right, top + 2)), RIVET)


def boiler(c, x0, x1, top, seed, red):
    m = c.mask(lambda p: (p.rect(x0, top + 30, x1, FLOOR), p.ellipse((x0 + x1) / 2, top + 30, (x1 - x0) / 2, 30)))
    c.put(m, COPPER_DARK)
    c.put(m * c.mask(lambda p: [p.rect(x0, y, x1, y + 3) for y in range(int(top) + 60, FLOOR, 40)]), COPPER)
    c.put(m * c.mask(lambda p: [p.ellipse(x, y, 2.2) for x in range(int(x0) + 8, int(x1), 16) for y in range(int(top) + 62, FLOOR, 40)]), RIVET)
    c.put(c.mask(box(x0 - 6, top, x1 + 6, top + 8)), IRON)
    fx0, fx1 = x0 + 50, x1 - 50
    c.put(c.mask(box(fx0, FLOOR - 80, fx1, FLOOR - 20)), (30, 24, 22))
    c.put(c.mask(lambda p: [p.poly([(x, FLOOR - 20), (x + 10, FLOOR - 56), (x + 20, FLOOR - 20)]) for x in range(int(fx0) + 6, int(fx1) - 20, 18)]), FIRE)
    c.light(c.mask(lambda p: p.ellipse((x0 + x1) / 2, FLOOR - 50, 140, 60), blur=16), FIRE, 0.3)
    gx, gy = (x0 + x1) / 2, top + 100
    c.put(c.mask(lambda p: p.ellipse(gx, gy, 24)), IRON)
    c.put(c.mask(lambda p: p.ellipse(gx, gy, 19)), GAUGE)
    c.put(c.mask(lambda p: p.poly([(gx + 6, gy - 16), (gx + 19, gy - 4), (gx + 15, gy + 6)])), RED)
    ang = 0.9 if red else -0.6
    c.put(c.mask(lambda p: p.line([(gx, gy), (gx + 16 * np.sin(ang), gy - 16 * np.cos(ang))], 2)), (30, 30, 30))
    if red:
        c.put(c.mask(box(gx - 22, gy + 30, gx + 22, gy + 44)), PAPER)
        c.put(c.mask(lambda p: [p.rect(x, gy + 34, x + 6, gy + 40) for x in (gx - 16, gx - 6, gx + 4, gx + 12)]), (40, 40, 40))


def east(c, k):
    bricks(c, 1200, W - 16, CEIL, FLOOR, "plant_e")
    vault(c, 1200, W - 16)
    pipe(c, [(1200, 120), (W - 16, 120)], 22, LAGGING)
    c.put(c.mask(lambda p: [p.rect(x, 98, x + 4, 142) for x in range(1220, W, 90)]), scale(LAGGING, 0.8))
    pipe(c, [(1200, 240), (2384, 240)], 12)
    # The great boilers behind the walks (not walked on): riveted drums up
    # to the vault's pipes, their manholes, a ladder of rungs up each.
    for bx0, bx1 in ((1300, 1500), (2120, 2340)):
        drum = c.mask(lambda p: (p.rect(bx0, 220, bx1, FLOOR), p.ellipse((bx0 + bx1) / 2, 220, (bx1 - bx0) / 2, 26)))
        c.put(drum, mix(COPPER_DARK, (40, 40, 40), 0.35))
        c.put(drum * c.mask(lambda p: [p.rect(bx0, y, bx1, y + 3) for y in range(250, FLOOR, 60)]), mix(COPPER, (40, 40, 40), 0.3))
        c.put(drum * c.mask(lambda p: [p.ellipse(x, y, 2) for x in range(bx0 + 8, bx1, 16) for y in range(252, FLOOR, 60)]), RIVET, 0.7)
        c.tone(drum * np.clip((c.x - bx0) / (bx1 - bx0), 0, 1), -0.3)
        c.put(c.mask(lambda p: p.ellipse((bx0 + bx1) / 2, 340, 26, 18)), IRON)
        pipe(c, [((bx0 + bx1) / 2, 200), ((bx0 + bx1) / 2, 120)], 10)
    pipe(c, [(1960, 800), (2100, 700), (2384, 700)], 14)
    walks(c)
    # A steam leak, its pail under it.
    c.put(c.mask(lambda p: [p.ellipse(1460 + i * 6, 260 + i * 14, 8 + i * 3, 6 + i * 2) for i in range(5)], blur=4), (240, 240, 240), 0.35)
    c.put(c.mask(lambda p: p.poly([(1440, FLOOR), (1480, FLOOR), (1476, FLOOR - 30), (1444, FLOOR - 30)])), IRON_LIGHT)


def bricked_door(c, k):
    x0, x1, y0 = DOOR
    m = c.mask(box(x0, y0, x1, FLOOR))
    c.put(m, BRICK_DARK)
    c.put(m * c.mask(lambda p: [p.rect(x0, y, x1, y + 1.4) for y in range(int(y0), FLOOR, 10)]), MORTAR, 0.7)
    c.put(c.mask(lambda p: p.line([(x0 + 22, y0), (x0 + 12, y0 + 34), (x0 + 24, y0 + 60), (x0 + 10, y0 + 90), (x0 + 18, FLOOR)], 2)), (20, 14, 12))
    c.light(c.mask(lambda p: p.line([(x0 + 12, y0 + 34), (x0 + 24, y0 + 60)], 3), blur=3), (255, 220, 160), 0.25)


def first_lab(c, k):
    w = LAB_W
    wall = c.mask(box(16, LAB_CEIL, w - 16, LAB_FLOOR))
    c.put(wall, (190, 180, 160))
    c.tone(wall * (c.noise("first_lab", 12, 6, 3) - 0.5), 0.2)
    c.tone(wall * np.clip((180 - c.y) / 140, 0, 1), -0.35)
    c.put(c.mask(box(16, 16, w - 16, LAB_CEIL)), IRON)
    # A bulb on its flex, lit.
    c.put(c.mask(lambda p: (p.line([(320, LAB_CEIL), (320, 140)], 1.2), p.ellipse(320, 148, 7, 9))), (255, 236, 180))
    c.light(c.mask(lambda p: p.ellipse(320, 200, 260, 200), blur=30), (255, 230, 170), 0.25)
    # The lower diagram adds a core to the coil.
    c.put(c.mask(box(80, 150, 300, 290)), OAK_DARK)
    c.put(c.mask(box(88, 158, 292, 282)), BOARD)
    for y in (194, 244):
        c.put(c.mask(lambda p: (
            p.line([(108, y), (256, y)], 1.1),
            [p.line([(x - 5, y + 12), (x - 5, y - 10), (x, y - 16),
                     (x + 5, y - 10), (x + 5, y + 12), (x - 5, y + 12)], 1.2)
             for x in range(148, 229, 16)],
        )), CHALK, 0.85)
    c.put(c.mask(lambda p: p.line([(127, 210), (236, 173)], 2)), (211, 137, 117))
    c.put(c.mask(lambda p: (p.line([(132, 225), (240, 225)], 1.6),
                           p.line([(132, 261), (240, 261)], 1.6))), CHALK)

    g = LAB_FLOOR
    # The bench holds the kettle and the coil in its jar.
    left, right, top = 352, 560, 448
    c.put(c.mask(lambda p: (p.rect(left, top, right, top + 8),
                           p.rect(left + 10, top + 8, left + 18, g),
                           p.rect(right - 18, top + 8, right - 10, g))), OAK)
    c.put(c.mask(box(left, top, right, top + 2)), mix(OAK, PAPER, 0.35))
    c.put(c.mask(lambda p: (p.ellipse(386, top - 14, 16, 14),
                           p.line([(399, top - 17), (414, top - 28)], 3))), IRON_LIGHT)
    c.put(c.mask(box(460, top - 40, 500, top)), (190, 220, 230), 0.45)
    c.put(c.mask(lambda p: [p.ring(480, y, 12, 1.6) for y in range(top - 34, top - 4, 4)]), COPPER)
    c.put(c.mask(box(456, top - 44, 504, top - 38)), RED)

    left, right, top = 240, 336, 416
    c.put(c.mask(box(left, top, right, g)), OAK_DARK)
    for y in range(top + 12, g - 20, 24):
        c.put(c.mask(box(left + 8, y, right - 8, y + 18)), OAK)
        c.put(c.mask(box(left + 42, y + 7, right - 42, y + 10)), IRON_LIGHT)
    c.put(c.mask(box(left, top, right, top + 3)), mix(OAK, PAPER, 0.35))

    left, right, top = 64, 224, 480
    c.put(c.mask(lambda p: (p.rect(left, top, right, top + 8),
                           p.line([(left + 10, g), (left + 28, top + 5)], 2),
                           p.line([(right - 10, g), (right - 28, top + 5)], 2))), (110, 120, 90))
    c.put(c.mask(lambda p: p.ellipse(left + 20, top - 4, 20, 6)), PAPER)

    # The east exit opens into a short passage.
    c.put(c.mask(box(580, g - 108, LAB_W - 16, g)), OAK_DARK)
    c.put(c.mask(box(588, g - 100, LAB_W - 16, g)), (56, 49, 44))
    c.put(c.mask(box(400, 200, 560, 240)), PAPER)
    lettering(c, "DO NOT THROW AWAY", 480, 215, 10, RED)


PIECES: Dict[str, Piece] = {
    "quad_manhole": Piece((MANHOLE[0] - 10, STREET - 40, MANHOLE[1] + 36, QUAD_H), manhole),
    "plant_west": Piece((16, 16, 1200, FLOOR), west),
    "plant_east": Piece((1200, 16, W - 16, FLOOR), east),
    "plant_bricked_door": Piece((DOOR[0], DOOR[2], DOOR[1], FLOOR), bricked_door),
    "first_lab_room": Piece((16, 16, LAB_W - 16, LAB_FLOOR), first_lab),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
