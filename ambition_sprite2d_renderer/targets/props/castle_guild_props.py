"""The Guild's room (`castle_godwin_guild_room`, the Evil dimension): behind
a false wall at the kitchens' west end, under the gatehouse, where the
Henchpersons' Guild, Local 666, meets in secret.

Drawn in room coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/castle_kitchens/make_specs.py` (`guild`):
the floor (y 512), the ceiling (to y 48), the way back east through the
false wall at the floor.

- `castle_guild_room`: a low cellar lit by candles; rows of mismatched
  chairs facing a lectern; the Guild's banner (a ladle and a spanner
  crossed); the list of demands chalked on a slate (three lines, the third
  underlined twice); a ballot box with its slot; the strike fund's jar,
  three coins in it; a kettle on a brazier, because nothing is decided
  without tea.

Animations: ``idle``, 1 frame. No drop shadows.
"""

from __future__ import annotations

from typing import Dict

import numpy as np

from . import castle_godwin as CG
from ._district_props import Piece, targets
from ._town_kit import box, mix, scale

W, FLOOR, CEILING = 960, 512, 48
PAL = {"stone": CG.STONE, "stone_light": CG.STONE_LIGHT, "dark": (22, 18, 26), "lamp": (255, 200, 120)}
STONE, STONE_DARK = CG.STONE, CG.STONE_DARK
WOOD = (110, 74, 50)
WOOD_DARK = (70, 46, 32)
CLOTH = (60, 90, 70)
GOLD = (220, 180, 80)
SLATE = (40, 44, 46)
CHALK = (236, 236, 228)
CANDLE = (255, 210, 130)
BRASS = (190, 150, 70)
GLASS = (190, 220, 230)


def room(c, k):
    g = FLOOR
    wall = c.mask(box(16, CEILING, W - 16, g))
    c.put(wall, mix(STONE, (60, 40, 30), 0.35))
    c.put(wall * c.mask(lambda p: [p.rect(16, y, W - 16, y + 1.4) for y in range(CEILING, g, 24)]), STONE_DARK, 0.6)
    c.tone(wall * (c.noise("guild_wall", 12, 6, 3) - 0.5), 0.15)
    c.tone(wall * np.clip((240 - c.y) / 190, 0, 1), -0.45)
    # Candles in the wall niches, their light.
    for x in (120, 420, 720):
        c.put(c.mask(lambda p: (p.rect(x - 18, 180, x + 18, 230), p.ellipse(x, 180, 18, 10))), STONE_DARK)
        c.put(c.mask(lambda p: (p.rect(x - 3, 208, x + 3, 228), p.ellipse(x, 204, 2.4, 4))), CANDLE)
        c.light(c.mask(lambda p: p.ellipse(x, 210, 110, 90), blur=20), CANDLE, 0.25)
    # The banner: a ladle and a spanner crossed, on green.
    bx = 520
    banner = c.mask(lambda p: p.poly([(bx - 70, 80), (bx + 70, 80), (bx + 70, 250), (bx, 280), (bx - 70, 250)]))
    c.put(banner, CLOTH)
    c.put(c.mask(lambda p: (p.line([(bx - 40, 120), (bx + 40, 220)], 6), p.ellipse(bx + 40, 222, 12, 8))), GOLD)
    c.put(c.mask(lambda p: (p.line([(bx + 40, 120), (bx - 40, 220)], 6), p.ring(bx + 40, 118, 10, 4), p.ring(bx - 42, 224, 9, 4))), mix(GOLD, (255, 255, 255), 0.2))
    c.put(c.mask(lambda p: [p.rect(bx - 60 + i * 20, 236, bx - 52 + i * 20, 246) for i in range(7)]), GOLD)
    # The lectern, and the slate of demands beside it.
    c.put(c.mask(lambda p: (p.poly([(470, g), (490, g - 90), (550, g - 90), (570, g)]), p.poly([(478, g - 90), (562, g - 90), (570, g - 108), (470, g - 108)]))), WOOD)
    c.put(c.mask(box(640, 280, 820, 400)), WOOD_DARK)
    c.put(c.mask(box(648, 288, 812, 392)), SLATE)
    for i, ln in enumerate((120, 96, 140)):
        y = 306 + i * 30
        c.put(c.mask(lambda p: (p.rect(660, y, 668, y + 8), p.rect(676, y + 2, 676 + ln, y + 5))), CHALK)
    c.put(c.mask(lambda p: [p.rect(676, y, 816, y + 1.6) for y in (374, 378)]), CHALK)
    # Rows of mismatched chairs facing the lectern.
    rng = c.rand("guild_chairs")
    for i, x in enumerate(range(110, 440, 56)):
        h = rng.uniform(46, 60)
        col = mix(WOOD, (40, 30, 30), rng.uniform(0, 0.5))
        c.put(c.mask(lambda p: (p.rect(x, g - 30, x + 34, g - 24), p.rect(x + 28, g - h, x + 34, g - 24), p.rect(x + 2, g - 24, x + 6, g), p.rect(x + 28, g - 24, x + 32, g))), col)
    # The ballot box, its slot; the strike fund's jar, three coins in it.
    c.put(c.mask(box(860, g - 60, 920, g - 10)), WOOD)
    c.put(c.mask(box(872, g - 62, 908, g - 56)), WOOD_DARK)
    c.put(c.mask(lambda p: (p.rect(866, g - 10, 872, g), p.rect(908, g - 10, 914, g))), WOOD_DARK)
    c.put(c.mask(lambda p: p.rect(250, 300, 290, 344)), GLASS, 0.45)
    c.put(c.mask(lambda p: [p.ellipse(262 + i * 8, 338 - (i % 2) * 3, 5, 2.4) for i in range(3)]), GOLD)
    c.put(c.mask(lambda p: p.rect(240, 344, 300, 350)), WOOD_DARK)
    # The kettle on its brazier.
    c.put(c.mask(lambda p: (p.rect(40, g - 30, 90, g - 22), p.line([(44, g), (52, g - 22)], 3), p.line([(86, g), (78, g - 22)], 3))), (60, 56, 60))
    c.put(c.mask(lambda p: [p.ellipse(56 + i * 9, g - 34, 4, 3) for i in range(4)]), (255, 140, 60))
    c.put(c.mask(lambda p: (p.ellipse(65, g - 48, 18, 14), p.line([(80, g - 50), (96, g - 60)], 4))), BRASS)


PIECES: Dict[str, Piece] = {
    "castle_guild_room": Piece((16, CEILING, W - 16, FLOOR), room),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
