"""Hylbert's Hotel's ballroom (`math_hotel_ballroom`, the Math dimension):
tonight, a game show of three doors, and the closets behind them.

Drawn on the numbers of `tools/ambition_ldtk_tools/specs/math_town/make_specs.py`
(`hotel_ballroom`, `hotel_closet`): the ballroom's floor (y 512), ceiling (to
y 32), its door back to the lobby (x 40), the stage's three doors (x 360, 616
and 872, each 48 wide); a closet's floor (y 256).

- `math_ballroom_room`: a ballroom made a game-show stage: red curtains
  drawn back, a proscenium of gold, footlights, a number lit over each door,
  the audience's empty chairs at the front, a scoreboard of probabilities.
- `math_goat`: a goat, standing, unimpressed.
- `math_car`: a red convertible with a bow on it.
- `math_closet_curtain`: the velvet curtain of a closet, floor to ceiling
  (x 160 to its east wall). It is the look of a `LockWall` that the host
  opens; the goat and the car are the looks of the walls behind it.
- `math_prize_case`: the glass case of tonight's prize, east of the stage
  (x 1000, 96 wide, 88 tall): the look of a `LockWall` that opens for a
  winner. The prize chest (the game's) stands in it.

Animations: ``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .eureka_props import Batch, edge_line, panels
from .math_hotel_props import BRASS, CLARET, CREAM, GOLD, WOOD, WOOD_DARK, infinity
from .math_town_terraces import PAL

W, FLOOR, CEILING = 1280, 512, 32
STAGE_DOORS = (360, 616, 872)
DOOR_W = 48
CURTAIN = (150, 26, 40)
CURTAIN_DARK = (96, 16, 28)
LAMP = (255, 226, 150)
#: The prize case (x0, y0, x1, y1) and a closet's curtain (x0 to its east
#: wall, its ceiling to its floor): the walls of `make_specs.py`.
PRIZE_CASE = (1000, FLOOR - 88, 1096, FLOOR)
CLOSET_W, CLOSET_FLOOR = 480, 256
CLOSET_CURTAIN = (160, CEILING, CLOSET_W - 16, CLOSET_FLOOR)


def digit(c, n, cx, cy, s, colour):
    """A seven-segment digit 1, 2 or 3, `s` its height."""
    w, h = s * 0.5, s / 2
    seg = {
        "a": [(cx - w / 2, cy - h), (cx + w / 2, cy - h)], "b": [(cx + w / 2, cy - h), (cx + w / 2, cy)],
        "c": [(cx + w / 2, cy), (cx + w / 2, cy + h)], "d": [(cx - w / 2, cy + h), (cx + w / 2, cy + h)],
        "e": [(cx - w / 2, cy), (cx - w / 2, cy + h)], "g": [(cx - w / 2, cy), (cx + w / 2, cy)],
    }
    on = {1: "bc", 2: "abged", 3: "abgcd"}[n]
    c.put(c.mask(lambda p: [p.line(seg[k], s * 0.12) for k in on]), colour)


def ballroom(c, k):
    g = FLOOR
    # The back wall in the dark of a stage, the curtains drawn back to each side.
    c.put(c.mask(box(16, CEILING, W - 16, g)), (40, 22, 30))
    for x0, x1, d in ((16, 300, 1), (W - 300, W - 16, -1)):
        m = c.mask(lambda p: p.poly([(x0, CEILING), (x1, CEILING), (x1 - d * 120, g - 300), (x1 - d * 60, g), (x0, g)] if d > 0 else
                                    [(x0, CEILING), (x1, CEILING), (x1, g), (x0 + 60, g), (x0 + 120, g - 300)]))
        c.put(m, CURTAIN)
        c.put(m * c.mask(lambda p: [p.rect(x, CEILING, x + 6, g) for x in range(x0, x1, 22)]), CURTAIN_DARK, 0.7)
        c.tone(m * np.clip((c.y - CEILING) / (g - CEILING), 0, 1), -0.2)
        ty = g - 300
        c.put(c.mask(lambda p: p.line([(x1 - d * 120 - 14, ty), (x1 - d * 120 + 14, ty + 6)], 5)), GOLD)
    # The proscenium: a gold arch, its valance.
    c.put(c.mask(box(16, CEILING, W - 16, CEILING + 40)), CURTAIN_DARK)
    c.put(c.mask(lambda p: [p.ellipse(x, CEILING + 40, 30, 14) for x in range(40, W, 60)]) * c.mask(box(0, CEILING + 40, W, CEILING + 56)), CURTAIN)
    c.put(c.mask(box(16, CEILING + 40, W - 16, CEILING + 44)), GOLD)
    # The three doors' frames, a number lit over each, bulbs round the frames.
    for n, x in enumerate(STAGE_DOORS, start=1):
        x0, x1 = x - 16, x + DOOR_W + 16
        c.put(c.mask(box(x0, g - 140, x1, g)), GOLD)
        c.put(c.mask(box(x0 + 8, g - 132, x1 - 8, g)), (30, 20, 26))
        c.put(c.mask(lambda p: [p.ellipse(bx, g - 136, 2.6) for bx in np.arange(x0 + 6, x1, 10)] + [p.ellipse(x0 + 4, by, 2.6) for by in np.arange(g - 126, g, 12)] + [p.ellipse(x1 - 4, by, 2.6) for by in np.arange(g - 126, g, 12)]), LAMP)
        c.put(c.mask(lambda p: p.ellipse((x0 + x1) / 2, g - 186, 28, 28)), (30, 20, 26))
        c.put(c.mask(lambda p: p.ring((x0 + x1) / 2, g - 186, 28, 3)), GOLD)
        digit(c, n, (x0 + x1) / 2, g - 186, 30, LAMP)
        c.light(c.mask(lambda p: p.ellipse((x0 + x1) / 2, g - 186, 50), blur=12), LAMP, 0.25)
    # The scoreboard: stay 1/3, switch 2/3, as bars.
    sx0, sy0 = 1010, 150
    c.put(c.mask(box(sx0, sy0, sx0 + 180, sy0 + 110)), (24, 20, 30))
    c.put(c.mask(box(sx0 + 20, sy0 + 26, sx0 + 20 + 140 / 3, sy0 + 42)), (110, 160, 230))
    c.put(c.mask(box(sx0 + 20, sy0 + 66, sx0 + 20 + 280 / 3, sy0 + 82)), (240, 200, 80))
    c.put(c.mask(lambda p: [p.rect(sx0 + 20 + 140 * f, sy0 + 20, sx0 + 21 + 140 * f, sy0 + 90) for f in (1 / 3, 2 / 3, 1.0)]), (90, 90, 110))
    # Footlights along the stage's edge, the audience's empty chairs.
    c.put(c.mask(box(16, g - 10, W - 16, g)), WOOD_DARK)
    c.put(c.mask(lambda p: [p.ellipse(x, g - 8, 5, 3) for x in range(330, 960, 40)]), LAMP)
    c.light(c.mask(lambda p: p.poly([(320, g), (960, g), (920, g - 240), (360, g - 240)]), blur=20), LAMP, 0.18)
    # The audience's chairs; east of the stage they leave room for the prize case.
    for x in list(range(110, 300, 50)) + list(range(PRIZE_CASE[2] + 24, 1240, 50)):
        c.put(c.mask(lambda p: (p.rect(x, g - 30, x + 26, g - 24), p.rect(x + 22, g - 56, x + 26, g - 24), p.rect(x + 2, g - 24, x + 5, g), p.rect(x + 21, g - 24, x + 24, g))), CLARET)
    infinity(c, W / 2, CEILING + 22, 18, GOLD, 2.4)


def goat(c, k):
    g = 80
    body = c.mask(lambda p: (p.ellipse(44, g - 38, 28, 16), p.rect(22, g - 30, 26, g), p.rect(30, g - 30, 34, g), p.rect(56, g - 30, 60, g), p.rect(64, g - 30, 68, g)))
    c.put(body, (220, 214, 200))
    c.tone(body * np.clip((c.y - (g - 54)) / 40, 0, 1), -0.2)
    head = c.mask(lambda p: (p.poly([(66, g - 46), (76, g - 64), (90, g - 52), (86, g - 44), (74, g - 40)]), p.ellipse(88, g - 47, 4, 4)))
    c.put(head, (226, 220, 206))
    c.put(c.mask(lambda p: (p.line([(74, g - 62), (68, g - 74), (62, g - 70)], 2.4), p.line([(78, g - 63), (76, g - 76), (70, g - 74)], 2.4))), (150, 130, 100))
    c.put(c.mask(lambda p: p.line([(84, g - 42), (84, g - 34)], 2.2)), (200, 194, 180))
    c.put(c.mask(lambda p: p.rect(78, g - 57, 83, g - 55)), (40, 30, 20))
    c.put(c.mask(lambda p: p.line([(16, g - 42), (10, g - 50)], 3)), (200, 194, 180))
    c.put(c.mask(lambda p: [p.rect(x - 0.5, g - 3, x + 4.5, g) for x in (22, 30, 56, 64)]), (60, 50, 40))


def car(c, k):
    g = 90
    red = (196, 40, 44)
    body = c.mask(lambda p: p.poly([(10, g - 18), (14, g - 40), (60, g - 44), (90, g - 66), (130, g - 66), (150, g - 44), (192, g - 40), (196, g - 18)]))
    c.put(body, red)
    c.tone(body * np.clip((c.y - (g - 66)) / 48, 0, 1), -0.25)
    c.put(c.mask(lambda p: p.poly([(96, g - 64), (126, g - 64), (138, g - 46), (92, g - 46)])), (170, 210, 230), 0.8)
    c.put(c.mask(box(14, g - 42, 196, g - 39)), (240, 230, 220))
    for x in (46, 160):
        c.put(c.mask(lambda p: p.ellipse(x, g - 14, 16)), (30, 30, 34))
        c.put(c.mask(lambda p: p.ellipse(x, g - 14, 7)), (200, 200, 210))
    # The bow on top.
    bx, by = 112, g - 72
    c.put(c.mask(lambda p: (p.poly([(bx, by), (bx - 22, by - 12), (bx - 20, by + 10)]), p.poly([(bx, by), (bx + 22, by - 12), (bx + 20, by + 10)]), p.ellipse(bx, by, 5))), GOLD)
    c.put(c.mask(lambda p: (p.line([(bx, by), (bx - 8, by + 22)], 2), p.line([(bx, by), (bx + 10, by + 22)], 2))), GOLD)


def closet_curtain(c, k):
    """Red velvet in folds, two halves that meet in the middle, a gold-fringed
    valance at the top and a gold fringe at the floor."""
    x0, y0, x1, y1 = CLOSET_CURTAIN
    mid = (x0 + x1) / 2
    cloth = c.mask(box(x0, y0, x1, y1))
    c.put(cloth, CURTAIN)
    # The folds: each half gathers toward its outer edge.
    for a, b in ((x0, mid), (mid, x1)):
        phase = (c.x - a) / (b - a)
        fold = np.sin(phase * np.pi * 7.0) * (0.55 + 0.45 * np.abs(phase - 0.5) * 2)
        half = cloth * ((c.x >= a) & (c.x < b))
        c.tone(half * np.clip(-fold, 0, 1), -0.38)
        c.tone(half * np.clip(fold, 0, 1), 0.16)
    # Where the halves meet, and the shade of the floor.
    c.put(c.mask(lambda p: p.rect(mid - 1.2, y0, mid + 1.2, y1)), CURTAIN_DARK)
    c.tone(cloth * np.clip((c.y - (y1 - 60)) / 60, 0, 1), -0.2)
    # The valance: a deeper red, scalloped, with its gold edge and fringe.
    c.put(c.mask(box(x0, y0, x1, y0 + 26)), CURTAIN_DARK)
    c.put(c.mask(lambda p: [p.ellipse(x, y0 + 26, 13, 8) for x in np.arange(x0 + 13, x1, 26)]) * c.mask(box(x0, y0 + 26, x1, y0 + 34)), CURTAIN_DARK)
    c.put(c.mask(box(x0, y0 + 22, x1, y0 + 25)), GOLD)
    c.put(c.mask(lambda p: [p.line([(x, y0 + 25), (x, y0 + 34)], 1.2) for x in np.arange(x0 + 3, x1, 5)]), GOLD, 0.85)
    # The fringe at the floor.
    c.put(c.mask(box(x0, y1 - 8, x1, y1 - 6)), GOLD)
    c.put(c.mask(lambda p: [p.line([(x, y1 - 6), (x, y1)], 1.2) for x in np.arange(x0 + 2, x1, 4)]), GOLD, 0.85)
    # A gold tassel on a cord at the seam, at chest height.
    ty = y1 - 70
    c.put(c.mask(lambda p: (p.ellipse(mid, ty, 5, 6), p.poly([(mid - 4, ty + 4), (mid + 4, ty + 4), (mid + 7, ty + 22), (mid - 7, ty + 22)]))), GOLD)
    c.tone(c.mask(lambda p: p.poly([(mid, ty + 4), (mid + 4, ty + 4), (mid + 7, ty + 22), (mid, ty + 22)])), -0.25)
    c.put(c.mask(lambda p: p.line([(mid, y0 + 34), (mid, ty - 5)], 1.0)), GOLD, 0.8)


def prize_case(c, k):
    """A glass case on a gold-trimmed base: brass posts at its corners, a
    lid, panes with a cool tint and the streaks of the stage lights on them.
    The chest stands in it; through the glass it is all seen."""
    x0, y0, x1, y1 = PRIZE_CASE
    base = 10
    # The panes: a faint tint, brighter at the top, and two streaks.
    glass = c.mask(box(x0 + 3, y0 + 6, x1 - 3, y1 - base))
    c.put(glass, (190, 220, 240), 0.16)
    c.put(glass * np.clip(1 - (c.y - y0) / (y1 - y0), 0, 1), (230, 245, 255), 0.12)
    for sx, w in ((x0 + 16, 7), (x0 + 30, 3), (x1 - 26, 5)):
        c.put(c.mask(lambda p: p.poly([(sx, y0 + 8), (sx + w, y0 + 8), (sx + w - 14, y1 - base - 4), (sx - 14, y1 - base - 4)])) * glass, (250, 252, 255), 0.22)
    # The base: dark wood, a gold band, a brass plate on its front.
    c.put(c.mask(box(x0, y1 - base, x1, y1)), WOOD)
    c.tone(c.mask(box(x0, y1 - base / 2, x1, y1)), -0.3)
    c.put(c.mask(box(x0, y1 - base, x1, y1 - base + 2)), GOLD)
    c.put(c.mask(box((x0 + x1) / 2 - 14, y1 - base + 3, (x0 + x1) / 2 + 14, y1 - 2)), BRASS)
    # The posts and the lid.
    for px_ in (x0, x1 - 3):
        c.put(c.mask(box(px_, y0 + 4, px_ + 3, y1 - base)), BRASS)
    c.put(c.mask(box(x0 - 1, y0, x1 + 1, y0 + 6)), BRASS)
    c.tone(c.mask(box(x0 - 1, y0 + 4, x1 + 1, y0 + 6)), -0.3)
    c.put(c.mask(lambda p: p.ellipse((x0 + x1) / 2, y0 - 1, 6, 3)), GOLD)
    c.put(c.mask(lambda p: p.line([(x0 + 3, y0 + 6), (x1 - 3, y0 + 6)], 0.8)), (240, 250, 255), 0.6)


PIECES: Dict[str, Piece] = {
    "math_ballroom_room": Piece((16, CEILING, W - 16, FLOOR), ballroom),
    "math_goat": Piece((0, 0, 100, 80), goat),
    "math_car": Piece((0, 0, 210, 90), car),
    "math_closet_curtain": Piece(CLOSET_CURTAIN, closet_curtain),
    "math_prize_case": Piece(PRIZE_CASE, prize_case),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
