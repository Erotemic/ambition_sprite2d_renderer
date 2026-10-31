"""Starlight Square (`magical_starlight_square`, the Magical dimension, Mary-O's):
its shop fronts and its old well.

Drawn in room coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/magical/make_specs.py` (`square`): the
ground (y 640), the awnings a body walks on (one-way, y 480: x 480..720 and
980..1220), the old well's hole (x 1600..1664), the balcony (y 448, x
1900..2188). In the starlight biome's colours: pink with mint icing, round
shapes, stars; no hearts (Jon, 2026-10-11: "the hearts are a bit much").

- `square_wand_shop`: WAND REPAIR, its awning the walk at y 480; wands in
  the window, one bent; a sign on the door, CLOSED (out fighting the void).
- `square_bakery`: the STAR BAKERY, its awning the other walk; crescents and
  moons in the window, a star on the chimney.
- `square_well`: the old well's rim either side of its hole (the hole stays
  open: it is the way down), a little round roof over it on two posts, a
  bucket on its rope.
- `square_house`: a tall round-roofed house under the balcony (the balcony
  is its own, at y 448), a star lamp by its door.

Animations: ``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

import math
from typing import Dict

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale

FLOOR = 640
AWNING_Y = 480
WAND_SHOP = (430, 770)
BAKERY = (930, 1270)
WELL = (1600, 1664)
HOUSE = (1880, 2210)
BALCONY_Y = 448

PINK = (246, 170, 206)
PINK_DARK = (214, 120, 170)
PINK_LIGHT = (255, 214, 232)
MINT = (170, 236, 210)
MINT_DARK = (110, 196, 170)
CREAM = (255, 246, 228)
LILAC = (196, 170, 240)
LILAC_DARK = (150, 120, 210)
GOLD = (255, 214, 110)
GOLD_DARK = (220, 170, 60)
GLASS = (150, 200, 240)
INK = (90, 60, 110)
STONE = (210, 196, 220)
STONE_DARK = (170, 150, 190)
WOOD = (196, 140, 110)
PAL = {"stone": STONE, "stone_light": CREAM, "dark": INK, "lamp": GOLD}


def star(c, x, y, r, colour=GOLD, k=0.45):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * k
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    c.put(c.mask(lambda p: p.poly(pts)), colour)


def icing(c, x0, x1, y, depth=10, colour=MINT):
    """A band of icing along `y`, dripping in round drops."""
    c.put(c.mask(box(x0, y, x1, y + depth)), colour)
    c.put(c.mask(lambda p: [p.ellipse(x, y + depth, 7, 6 + (int(x) * 7 % 5)) for x in range(int(x0) + 10, int(x1) - 4, 22)]), colour)
    c.put(c.mask(box(x0, y, x1, y + 3)), mix(colour, (255, 255, 255), 0.45))


def facade(c, x0, x1, top, colour, roof):
    """A round-shouldered shop front from `top` to the ground."""
    c.put(c.mask(lambda p: (p.rect(x0, top + 40, x1, FLOOR), p.ellipse((x0 + x1) / 2, top + 40, (x1 - x0) / 2, 40))), colour)
    c.put(c.mask(box(x1 - 14, top + 40, x1, FLOOR)), scale(colour, 0.88))
    icing(c, x0 + 8, x1 - 8, top + 30, 12, roof)


def window(c, x0, y0, x1, y1):
    c.put(c.mask(lambda p: (p.rect(x0, y0 + 20, x1, y1), p.ellipse((x0 + x1) / 2, y0 + 20, (x1 - x0) / 2, 20))), CREAM)
    c.put(c.mask(lambda p: (p.rect(x0 + 5, y0 + 22, x1 - 5, y1 - 5), p.ellipse((x0 + x1) / 2, y0 + 22, (x1 - x0) / 2 - 5, 16))), GLASS)
    c.put(c.mask(lambda p: p.line([(x0 + 14, y0 + 30), (x0 + 30, y0 + 14)], 3)), (255, 255, 255), 0.6)


def awning(c, x0, x1, y, colour):
    """A striped awning whose top is the walk at `y`."""
    c.put(c.mask(lambda p: p.poly([(x0, y), (x1, y), (x1 + 14, y + 34), (x0 - 14, y + 34)])), CREAM)
    c.put(c.mask(lambda p: [p.poly([(x, y), (x + 20, y), (x + 20 + (x - (x0 + x1) / 2) * 0.06, y + 34), (x + (x - (x0 + x1) / 2) * 0.06, y + 34)]) for x in range(int(x0), int(x1), 40)]), colour)
    c.put(c.mask(lambda p: [p.ellipse(x, y + 34, 10, 6) for x in range(int(x0) - 4, int(x1) + 14, 20)]), colour)


def door(c, x, w=48, colour=LILAC):
    """A round-topped shop door (art only: the shop is shut)."""
    c.put(c.mask(lambda p: (p.rect(x, FLOOR - 76, x + w, FLOOR), p.ellipse(x + w / 2, FLOOR - 76, w / 2, 22))), colour)
    c.put(c.mask(lambda p: p.ellipse(x + w - 10, FLOOR - 40, 3.5)), GOLD)


def wand_shop(c, k):
    x0, x1 = WAND_SHOP
    facade(c, x0, x1, 250, PINK, MINT)
    c.put(c.mask(box(x0 + 30, 300, x1 - 30, 336)), CREAM)
    c.put(c.mask(box(x0 + 34, 304, x1 - 34, 332)), PINK_DARK, 0.25)
    window(c, x0 + 40, 360, x0 + 190, AWNING_Y - 8)
    # Wands in the window: a row of them, one bent.
    for i, x in enumerate(range(x0 + 60, x0 + 180, 26)):
        bend = 14 if i == 2 else 0
        c.put(c.mask(lambda p: p.line([(x, AWNING_Y - 14), (x + bend, AWNING_Y - 70)], 3)), WOOD)
        star(c, x + bend, AWNING_Y - 74, 7)
    awning(c, 480, 720, AWNING_Y, PINK_DARK)
    door(c, x1 - 110, 52)
    c.put(c.mask(box(x1 - 108, FLOOR - 62, x1 - 60, FLOOR - 46)), CREAM)
    star(c, (x0 + x1) / 2, 268, 14)


def bakery(c, k):
    x0, x1 = BAKERY
    facade(c, x0, x1, 260, MINT, PINK_LIGHT)
    # The chimney, its star.
    c.put(c.mask(box(x1 - 90, 200, x1 - 60, 280)), MINT_DARK)
    star(c, x1 - 75, 192, 12)
    window(c, x0 + 160, 360, x1 - 40, AWNING_Y - 8)
    # Crescents and moons in the window, from new to full.
    for i, x in enumerate(range(x0 + 180, x1 - 50, 30)):
        y = AWNING_Y - 30
        c.put(c.mask(lambda p: p.ellipse(x, y, 11)), GOLD)
        if i < 3:
            c.put(c.mask(lambda p: p.ellipse(x + 11 - i * 4, y - 2, 10)), GLASS)
    awning(c, 980, 1220, AWNING_Y, MINT_DARK)
    door(c, x0 + 50, 52, PINK_DARK)


def well(c, k):
    x0, x1 = WELL
    for a, b in ((x0 - 44, x0), (x1, x1 + 44)):
        c.put(c.mask(lambda p: p.rect(a, FLOOR - 40, b, FLOOR)), STONE)
        c.put(c.mask(lambda p: [p.rect(a, y, b, y + 1.5) for y in (FLOOR - 26, FLOOR - 13)]), STONE_DARK)
        c.put(c.mask(lambda p: p.rect(a, FLOOR - 42, b, FLOOR - 36)), CREAM)
    for x in (x0 - 30, x1 + 22):
        c.put(c.mask(box(x, FLOOR - 170, x + 8, FLOOR - 40)), WOOD)
    c.put(c.mask(lambda p: p.ellipse((x0 + x1) / 2, FLOOR - 172, 70, 30)), LILAC)
    c.put(c.mask(lambda p: p.ellipse((x0 + x1) / 2, FLOOR - 178, 64, 20)), mix(LILAC, (255, 255, 255), 0.3))
    star(c, (x0 + x1) / 2, FLOOR - 206, 10)
    c.put(c.mask(box(x0 - 30, FLOOR - 150, x1 + 30, FLOOR - 146)), WOOD)
    c.put(c.mask(lambda p: p.line([((x0 + x1) / 2, FLOOR - 146), ((x0 + x1) / 2, FLOOR - 104)], 1.5)), INK)
    c.put(c.mask(lambda p: p.poly([(x0 + 20, FLOOR - 104), (x1 - 20, FLOOR - 104), (x1 - 24, FLOOR - 84), (x0 + 24, FLOOR - 84)])), PINK_DARK)


def house(c, k):
    x0, x1 = HOUSE
    c.put(c.mask(lambda p: (p.rect(x0 + 20, 200, x1 - 20, FLOOR), p.ellipse((x0 + x1) / 2, 200, (x1 - x0) / 2 - 20, 70))), LILAC)
    c.put(c.mask(box(x1 - 34, 200, x1 - 20, FLOOR)), LILAC_DARK)
    icing(c, x0 + 26, x1 - 26, 186, 12, PINK_LIGHT)
    window(c, x0 + 60, 260, x0 + 140, 360)
    window(c, x1 - 140, 260, x1 - 60, 360)
    # The balcony's rail, over the walk at y 448.
    c.put(c.mask(box(x0 + 8, BALCONY_Y, x1 - 12, BALCONY_Y + 8)), CREAM)
    c.put(c.mask(lambda p: [p.rect(x, BALCONY_Y - 34, x + 4, BALCONY_Y) for x in range(x0 + 14, x1 - 12, 24)]), CREAM)
    c.put(c.mask(box(x0 + 8, BALCONY_Y - 38, x1 - 12, BALCONY_Y - 32)), CREAM)
    door(c, (x0 + x1) / 2 - 26, 52, PINK)
    # A star lamp by the door.
    lx = (x0 + x1) / 2 + 60
    c.put(c.mask(box(lx - 2, FLOOR - 120, lx + 2, FLOOR)), INK)
    star(c, lx, FLOOR - 128, 11, GOLD, 0.5)
    c.light(c.mask(lambda p: p.ellipse(lx, FLOOR - 128, 40), blur=10), GOLD, 0.35)


PIECES: Dict[str, Piece] = {
    "square_wand_shop": Piece((WAND_SHOP[0] - 20, 180, WAND_SHOP[1] + 20, FLOOR), wand_shop),
    "square_bakery": Piece((BAKERY[0] - 20, 170, BAKERY[1] + 20, FLOOR), bakery),
    "square_well": Piece((WELL[0] - 60, FLOOR - 230, WELL[1] + 60, FLOOR), well),
    "square_house": Piece((HOUSE[0], 110, HOUSE[1], FLOOR), house),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
