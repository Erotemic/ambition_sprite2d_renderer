"""The cellars under customs (`pirate_customs_cellars`, PvN dimension): under
the Pirate Port's gate plaza, where the ring's freight is declared, the
freight that is not goes by, down the plaza's old well.

Drawn in room coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/pirate_port/make_specs.py` (`plaza`,
`cellars`): the plaza's floor (y 704) and its well (x 16..80, against
the plaza's west wall, off the low road); the cellars' floor (y 576), their
vault (to y 64), the shaft down from the well (x 16..80), the barrel rack
(walked on, y 480).

- `plaza_well`: the old well in the plaza: its stone curbs, posts and
  shingle roof, the winch and its rope, a bucket left on the curb, and the
  shaft going down dark, a ladder down it.
- `cellars_vault`: a brick vault on pillars, lanterns; the shaft's ladder in
  its fall of daylight at the west end; the desk where the customs stamps
  are forged; an idol under a sheet, plainly cursed, glowing; a crate of
  undeclared chickens; crates with customs tags left blank; the barrels,
  racked; the still; a bricked-up arch to the sea.

Animations: ``idle``, 1 frame. No drop shadows.
"""

from __future__ import annotations

from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .pirate_port_props import PAL, PLANK, PLANK_DARK, ROPE, SAIL, TIMBER

PLAZA_FLOOR, PLAZA_H = 704, 832
WELL = (16, 80)
W, FLOOR, CEIL = 1600, 576, 64
BARRELS = (920, 1140, 480)
BRICK = (132, 84, 64)
BRICK_DARK = (92, 58, 46)
MORTAR = (170, 150, 128)
STONE = (150, 140, 124)
STONE_DARK = (98, 92, 84)
SHINGLE = (120, 70, 50)
COPPER = (196, 112, 64)
IDOL = (176, 150, 60)
CURSE = (120, 230, 140)
INK = (40, 30, 30)
STAMP_RED = (190, 50, 44)
HAY = (206, 178, 100)
CHICKEN = (244, 240, 232)
COMB = (210, 50, 44)
LAMP = (255, 206, 130)


def ladder(c, x0, x1, y0, y1):
    """A ladder: two rails and its rungs."""
    c.put(c.mask(lambda p: (p.rect(x0 + 6, y0, x0 + 11, y1), p.rect(x1 - 11, y0, x1 - 6, y1))), TIMBER)
    c.put(c.mask(lambda p: [p.rect(x0 + 8, y, x1 - 8, y + 4) for y in np.arange(y0 + 10, y1, 22)]), PLANK)


def well(c, k):
    x0, x1 = WELL
    g = PLAZA_FLOOR
    # The shaft going down, dark, its stones; the ladder down it.
    shaft = c.mask(box(x0, g, x1, PLAZA_H))
    c.put(shaft, STONE_DARK)
    c.put(shaft * c.mask(lambda p: [p.rect(x0, y, x1, y + 1.2) for y in range(g + 14, PLAZA_H, 14)]), scale(STONE_DARK, 0.7))
    c.tone(shaft * np.clip((c.y - g) / 120, 0, 1), -0.55)
    ladder(c, x0 + 16, x1 - 16, g - 8, PLAZA_H)
    # The curbs either side of the hole, and their stones.
    # The west curb is in the wall.
    for a, b in ((x1, x1 + 24),):
        curb = c.mask(box(a, g - 26, b, g))
        c.put(curb, STONE)
        c.put(curb * c.mask(lambda p: (p.rect(a, g - 14, b, g - 13), p.rect((a + b) / 2, g - 26, (a + b) / 2 + 1, g - 14))), STONE_DARK)
        c.put(c.mask(box(a, g - 28, b, g - 24)), mix(STONE, (255, 255, 255), 0.3))
    # The posts, the roof, the winch and its rope.
    c.put(c.mask(lambda p: [p.rect(x, 620, x + 7, g - 26) for x in (x0, x1 + 11)]), TIMBER)
    roof = c.mask(lambda p: p.poly([(x0, 614), ((x0 + x1) / 2 + 8, 602), (x1 + 36, 626), (x1 + 30, 632), ((x0 + x1) / 2 + 8, 610), (x0, 622)]))
    c.put(roof, SHINGLE)
    c.put(roof * c.mask(lambda p: [p.line([(x, 600), (x - 4, 634)], 1) for x in range(x0 - 30, x1 + 36, 9)]), scale(SHINGLE, 0.7))
    c.put(c.mask(lambda p: p.rect(x0, 644, x1 + 18, 652)), PLANK_DARK)
    c.put(c.mask(lambda p: p.ellipse(x1 + 30, 648, 6)), TIMBER)
    c.put(c.mask(lambda p: p.line([(x1 + 30, 648), (x1 + 40, 636)], 2)), TIMBER)
    c.put(c.mask(lambda p: [p.ellipse(x, 648, 2, 5) for x in range(x0 + 10, x1 + 16, 5)]), ROPE)
    c.put(c.mask(lambda p: p.line([((x0 + x1) / 2 + 20, 652), ((x0 + x1) / 2 + 20, g + 30)], 1.6)), ROPE)
    # The bucket, left on the east curb.
    c.put(c.mask(lambda p: p.poly([(x1 + 2, g - 46), (x1 + 22, g - 46), (x1 + 19, g - 26), (x1 + 5, g - 26)])), PLANK)
    c.put(c.mask(lambda p: [p.rect(x1 + 2, y, x1 + 22, y + 2) for y in (g - 42, g - 32)]), (70, 70, 76))
    c.put(c.mask(box(x1, g - 60, x1 + 24, g - 46)) * c.mask(lambda p: p.ring(x1 + 12, g - 46, 9, 1.2)), (70, 70, 76))


def barrel(c, x, y, r):
    """A barrel end-on, at (x, y), radius r."""
    c.put(c.mask(lambda p: p.ellipse(x, y, r)), PLANK)
    c.put(c.mask(lambda p: (p.ring(x, y, r - 1, 2.2), p.ring(x, y, r * 0.55, 1.4))), (70, 70, 76))
    c.put(c.mask(lambda p: p.ellipse(x, y, r * 0.14)), TIMBER)


def vault(c, k):
    rng = c.rand("cellars")
    wall = c.mask(box(16, CEIL, W - 16, FLOOR))
    c.put(wall, BRICK)
    # Brick courses, staggered.
    c.put(wall * c.mask(lambda p: [p.rect(16, y, W - 16, y + 1.4) for y in range(CEIL, FLOOR, 12)]), MORTAR, 0.8)
    c.put(wall * c.mask(lambda p: [p.rect(x + (12 if (y // 12) % 2 else 0), y, x + 1.4 + (12 if (y // 12) % 2 else 0), y + 12)
                                   for y in range(CEIL, FLOOR, 12) for x in range(16, W, 24)]), MORTAR, 0.7)
    c.tone(wall * (c.noise("cellars_bricks", 40, 12, 2) - 0.5), 0.22)
    c.put(wall * (c.noise("cellars_damp", 12, 4, 3) > 0.7), BRICK_DARK, 0.3)
    # The vault's stone over the arches.
    ceiling = c.mask(box(16, 16, W - 16, CEIL))
    c.put(ceiling, STONE_DARK)
    c.put(ceiling * c.mask(lambda p: [p.rect(x, 16, x + 1.2, CEIL) for x in range(16, W, 40)]), scale(STONE_DARK, 0.75))
    # The vault: arches on pillars, the bays darker under them.
    for i, px in enumerate(range(16, W, 320)):
        c.put(c.mask(box(px, CEIL, px + 28, FLOOR)), STONE)
        c.put(c.mask(box(px, FLOOR - 24, px + 34, FLOOR)), STONE_DARK)
        if px + 320 < W:
            cx = px + 14 + 160
            upper = c.mask(box(px, 0, px + 320, CEIL + 150))
            c.put(upper * c.mask(lambda p: p.ring(cx, CEIL + 150, 160, 16)), STONE)
            c.put(upper * c.mask(lambda p: p.ring(cx, CEIL + 150, 151, 2)), STONE_DARK)
    c.tone(wall * np.clip((CEIL + 140 - c.y) / 90, 0, 1), -0.35)
    # Lanterns on the pillars.
    for px in (336, 656, 976, 1296):
        c.put(c.mask(lambda p: (p.rect(px - 6, 250, px + 6, 268), p.rect(px - 2, 240, px + 2, 250))), (40, 40, 44))
        c.put(c.mask(lambda p: p.rect(px - 4, 252, px + 4, 266)), LAMP)
        c.light(c.mask(lambda p: p.ellipse(px, 262, 90, 70), blur=18), LAMP, 0.22)

    # The still, at the east end: a copper pot on its fire, the coil, a jug.
    c.put(c.mask(lambda p: p.rect(1200, FLOOR - 30, 1320, FLOOR)), STONE_DARK)
    c.put(c.mask(lambda p: [p.poly([(x, FLOOR - 30), (x + 8, FLOOR - 48), (x + 16, FLOOR - 30)]) for x in (1224, 1244, 1264, 1284)]), (240, 140, 50))
    c.put(c.mask(lambda p: p.ellipse(1260, FLOOR - 84, 52, 48)), COPPER)
    c.put(c.mask(lambda p: p.ellipse(1244, FLOOR - 102, 18, 14)), mix(COPPER, (255, 255, 255), 0.35))
    c.put(c.mask(lambda p: p.poly([(1248, FLOOR - 130), (1272, FLOOR - 130), (1266, FLOOR - 164), (1254, FLOOR - 164)])), COPPER)
    c.put(c.mask(lambda p: p.line([(1260, FLOOR - 164), (1290, FLOOR - 184), (1356, FLOOR - 150)], 4)), COPPER)
    c.put(c.mask(lambda p: [p.ring(1372, FLOOR - 130 + j * 18, 16, 3) for j in range(4)]), COPPER)
    c.put(c.mask(lambda p: p.rect(1356, FLOOR - 60, 1390, FLOOR)), PLANK_DARK)
    c.put(c.mask(lambda p: (p.ellipse(1416, FLOOR - 18, 14, 18), p.rect(1410, FLOOR - 44, 1422, FLOOR - 30))), (150, 120, 80))

    # The barrels, racked (their top walked on), and the rack.
    x0, x1, top = BARRELS
    c.put(c.mask(lambda p: (p.rect(x0, top, x1, top + 8), p.rect(x0, top + 8, x0 + 8, FLOOR), p.rect(x1 - 8, top + 8, x1, FLOOR))), TIMBER)
    for row, y in enumerate((FLOOR - 22, FLOOR - 66)):
        for x in np.arange(x0 + 32 + row * 0, x1 - 20, 46):
            barrel(c, x, y, 21)

    # Crates, their customs tags left blank.
    for (cx0, cy0, cx1) in ((700, FLOOR - 64, 780), (786, FLOOR - 64, 866), (730, FLOOR - 120, 830)):
        cy1 = cy0 + 56 if cy0 < FLOOR - 64 else FLOOR
        cm = c.mask(box(cx0, cy0, cx1, cy1))
        c.put(cm, PLANK)
        c.put(cm * c.mask(lambda p: (p.line([(cx0, cy0), (cx1, cy1)], 2.4), p.line([(cx1, cy0), (cx0, cy1)], 2.4))), PLANK_DARK)
        c.put(cm * c.mask(lambda p: (p.rect(cx0, cy0, cx1, cy0 + 4), p.rect(cx0, cy1 - 4, cx1, cy1))), PLANK_DARK)
        c.put(c.mask(lambda p: p.ring((cx0 + cx1) / 2, cy0 + 18, 4, 1)), (70, 70, 76))
        c.put(c.mask(lambda p: p.rect((cx0 + cx1) / 2 - 12, cy0 + 22, (cx0 + cx1) / 2 + 12, cy0 + 38)), SAIL)
        c.put(c.mask(lambda p: p.line([((cx0 + cx1) / 2, cy0 + 22), ((cx0 + cx1) / 2, cy0 + 14)], 0.8)), ROPE)

    # A crate of undeclared chickens: slats, straw, heads through the slats.
    hx0, hx1, hy = 520, 650, FLOOR - 70
    c.put(c.mask(box(hx0, hy, hx1, FLOOR)), PLANK_DARK)
    c.put(c.mask(lambda p: [p.rect(hx0, y, hx1, y + 6) for y in (hy, hy + 30, FLOOR - 8)]), PLANK)
    c.put(c.mask(lambda p: [p.rect(x, hy, x + 6, FLOOR) for x in (hx0, hx1 - 6)]), PLANK)
    c.put(c.mask(lambda p: [p.ellipse(x, FLOOR - 12, 9, 4) for x in range(hx0 + 10, hx1, 14)]), HAY)
    for j, cx in enumerate((hx0 + 24, hx0 + 56, hx0 + 92, hx0 + 116)):
        cy = hy + 18 + (j % 2) * 30
        c.put(c.mask(lambda p: p.ellipse(cx, cy, 9, 8)), CHICKEN)
        c.put(c.mask(lambda p: p.poly([(cx - 3, cy - 7), (cx, cy - 13), (cx + 3, cy - 7)])), COMB)
        c.put(c.mask(lambda p: p.poly([(cx + 8, cy), (cx + 14, cy + 2), (cx + 8, cy + 4)])), (230, 170, 60))
        c.put(c.mask(lambda p: p.ellipse(cx + 3, cy - 2, 1.3)), INK)
    c.put(c.mask(lambda p: [p.ellipse(hx0 + 30 + i * 30, FLOOR + 0 - 3, 4, 2) for i in range(3)]), CHICKEN)

    # The idol under its sheet, the sheet half off; it glows.
    ix = 420
    c.put(c.mask(lambda p: p.rect(ix - 34, FLOOR - 44, ix + 34, FLOOR)), STONE)
    c.put(c.mask(lambda p: (p.ellipse(ix, FLOOR - 92, 24, 28), p.rect(ix - 20, FLOOR - 76, ix + 20, FLOOR - 44))), IDOL)
    c.put(c.mask(lambda p: [p.ellipse(ix + dx, FLOOR - 96, 4, 3) for dx in (-9, 9)]), CURSE)
    c.put(c.mask(lambda p: p.line([(ix - 10, FLOOR - 80), (ix, FLOOR - 76), (ix + 10, FLOOR - 80)], 1.6)), scale(IDOL, 0.6))
    sheet = c.mask(lambda p: p.poly([(ix - 4, FLOOR - 122), (ix + 40, FLOOR - 70), (ix + 46, FLOOR - 44), (ix + 4, FLOOR - 50), (ix + 14, FLOOR - 90)]))
    c.put(sheet, SAIL)
    c.put(sheet * c.mask(lambda p: [p.line([(ix + 6 + i * 8, FLOOR - 100), (ix + 14 + i * 8, FLOOR - 48)], 0.8) for i in range(4)]), mix(SAIL, (0, 0, 0), 0.18))
    c.light(c.mask(lambda p: p.ellipse(ix, FLOOR - 92, 70, 60), blur=16), CURSE, 0.28)

    # The forger's desk: the lamp, the stamps, the ledger, a stamped sheet.
    dx0, dx1 = 150, 300
    c.put(c.mask(lambda p: (p.rect(dx0, FLOOR - 48, dx1, FLOOR - 40), p.rect(dx0 + 6, FLOOR - 40, dx0 + 12, FLOOR),
                            p.rect(dx1 - 12, FLOOR - 40, dx1 - 6, FLOOR))), TIMBER)
    c.put(c.mask(lambda p: (p.rect(dx0 + 14, FLOOR - 68, dx0 + 20, FLOOR - 48), p.poly([(dx0 + 4, FLOOR - 68), (dx0 + 30, FLOOR - 68), (dx0 + 22, FLOOR - 80), (dx0 + 12, FLOOR - 80)]))), (60, 90, 70))
    c.light(c.mask(lambda p: p.ellipse(dx0 + 18, FLOOR - 50, 50, 20), blur=10), LAMP, 0.3)
    for j, sx in enumerate((dx0 + 46, dx0 + 62, dx0 + 78)):
        c.put(c.mask(lambda p: (p.rect(sx - 4, FLOOR - 58, sx + 4, FLOOR - 48), p.ellipse(sx, FLOOR - 62, 4))), PLANK_DARK)
    c.put(c.mask(lambda p: p.rect(dx0 + 92, FLOOR - 54, dx0 + 130, FLOOR - 48)), (130, 40, 36))
    c.put(c.mask(lambda p: p.poly([(dx0 + 96, FLOOR - 48), (dx0 + 132, FLOOR - 48), (dx0 + 128, FLOOR - 44), (dx0 + 92, FLOOR - 44)])), SAIL)
    c.put(c.mask(lambda p: p.ring(dx0 + 112, FLOOR - 58, 6, 1.4)), STAMP_RED)
    for sy in (FLOOR - 140, FLOOR - 120):
        c.put(c.mask(lambda p: p.rect(dx0 + 20, sy, dx0 + 120, sy + 14)), SAIL)
        c.put(c.mask(lambda p: [p.ring(dx0 + 40 + i * 30, sy + 7, 5, 1.2) for i in range(3)]), STAMP_RED)
        c.put(c.mask(lambda p: [p.rect(x, sy - 4, x + 3, sy) for x in (dx0 + 24, dx0 + 114)]), (70, 70, 76))

    # The shaft from the well: its gap in the vault, daylight down it, the
    # ladder.
    s0, s1 = WELL
    c.put(c.mask(box(s0, 16, s1, CEIL)), STONE_DARK)
    c.light(c.mask(lambda p: p.poly([(s0, 16), (s1, 16), (s1 + 30, FLOOR), (s0 - 30, FLOOR)]), blur=10), (250, 244, 220), 0.22)
    ladder(c, s0 + 16, s1 - 16, 16, FLOOR)

    # The bricked-up arch to the sea, and its grate.
    ax = 1500
    c.put(c.mask(lambda p: (p.ellipse(ax, FLOOR - 120, 60), p.rect(ax - 60, FLOOR - 120, ax + 60, FLOOR))), STONE)
    inner = c.mask(lambda p: (p.ellipse(ax, FLOOR - 120, 50), p.rect(ax - 50, FLOOR - 120, ax + 50, FLOOR)))
    c.put(inner, BRICK_DARK)
    c.put(inner * c.mask(lambda p: [p.rect(ax - 50, y, ax + 50, y + 1.4) for y in range(FLOOR - 170, FLOOR, 10)]), MORTAR, 0.6)
    c.put(c.mask(lambda p: [p.rect(x, FLOOR - 60, x + 3, FLOOR) for x in range(ax - 40, ax + 44, 14)]), (60, 60, 64))
    c.put(c.mask(lambda p: p.rect(ax - 44, FLOOR - 62, ax + 44, FLOOR - 58)), (60, 60, 64))


PIECES: Dict[str, Piece] = {
    "plaza_well": Piece((WELL[0], 596, WELL[1] + 48, PLAZA_H), well),
    "cellars_vault": Piece((16, 16, W - 16, FLOOR), vault),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
