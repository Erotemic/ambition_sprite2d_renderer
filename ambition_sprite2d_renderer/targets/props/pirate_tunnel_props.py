"""The smugglers' tunnel under the Pirate Port's waterfront (PvN dimension):
east from the cellars under customs, through the arch they knocked through,
to the drain in the waterfront's street; behind a plank wall at its east
end, the hoard.

Drawn in room coordinates (`_district_props`) on the numbers of
`ambition_content/generators/pirate_port/make_specs.py` (`waterfront`,
`tunnel`, `hoard`): the waterfront's street (y 768, the room's foot 896) and
its drain (x 1696..1760); the tunnel's floor (y 576), vault (to y 64), the
drain's shaft (x 1696..1760; its ladder the engine's); the hoard's floor and
vault the tunnel's.

- `port_drain_shaft`: the drain's hole in the street: its stone kerb, the
  shaft going down dark (seen once its grate is open).
- `port_drain_grate`: the iron grate over the drain (the look of the lock
  wall the tunnel's lever opens).
- `tunnel_west`: a brick tunnel, its rails; a handcart of undeclared goods
  (a crate of parrots, a rolled carpet, a harp); lanterns on hooks; the
  chute from the Drowned Compass's cellar, a barrel stuck in it.
- `tunnel_east`: the drain's shaft up in its fall of street light, the
  lever by it; the smugglers' chalk tally of runs (and of near things);
  the plank wall at the end, a draught and a light through its gaps.
- `tunnel_freight_cut` has the flooded channel, loading docks, and cable.
- `pirate_tunnel_freight_carrier` moves along the cable.
- `hoard_room`: the hoard behind the planks: coin heaped, a figurehead, a
  painting of somebody's grandmother, candlesticks, a crown on a skull;
  the last smuggler, sat against the chest, who kept it.

Animations: ``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .pirate_cellars_props import BRICK, BRICK_DARK, COPPER, LAMP, MORTAR, STONE, STONE_DARK, barrel
from .pirate_port_props import PAL, PLANK, PLANK_DARK, ROPE, SAIL, TIMBER

STREET, WATERFRONT_H = 768, 896
DRAIN = (1696, 1760)
W, FLOOR, CEIL = 2048, 576, 64
HOARD_W = 512
IRON = (64, 64, 70)
IRON_LIGHT = (120, 120, 128)
RAIL = (90, 84, 80)
GOLD = (232, 190, 70)
GOLD_DARK = (176, 132, 40)
BONE = (226, 216, 190)
CHALK = (236, 232, 220)
DAYLIGHT = (250, 244, 220)
PARROT = (60, 170, 80)
CUT = (688, 1344)
BED = 704
DOCK_TOP = 544
LOADING_DOCKS = ((624, 752), (1280, 1440))


def bricks(c, x0, x1, top, g, seed):
    wall = c.mask(box(x0, top, x1, g))
    c.put(wall, BRICK)
    c.put(wall * c.mask(lambda p: [p.rect(x0, y, x1, y + 1.4) for y in range(top, g, 12)]), MORTAR, 0.8)
    c.put(wall * c.mask(lambda p: [p.rect(x + (12 if (y // 12) % 2 else 0), y, x + 1.4 + (12 if (y // 12) % 2 else 0), y + 12)
                                   for y in range(top, g, 12) for x in range(x0, x1, 24)]), MORTAR, 0.7)
    c.tone(wall * (c.noise(seed, 40, 12, 2) - 0.5), 0.22)
    c.put(wall * (c.noise(seed + "_damp", 12, 4, 3) > 0.7), BRICK_DARK, 0.3)
    c.tone(wall * np.clip((CEIL + 160 - c.y) / 120, 0, 1), -0.45)
    vault = c.mask(box(x0, 16, x1, top))
    c.put(vault, STONE_DARK)
    c.put(vault * c.mask(lambda p: [p.rect(x, 16, x + 1.2, top) for x in range(x0, x1, 40)]), scale(STONE_DARK, 0.75))
    return wall


def ribs(c, x0, x1):
    """Stone ribs of the vault on their piers, every 400."""
    for px in range(int(x0) + 280, int(x1) - 60, 400):
        c.put(c.mask(box(px, CEIL, px + 26, FLOOR)), STONE)
        c.put(c.mask(box(px - 4, FLOOR - 20, px + 30, FLOOR)), STONE_DARK)
        c.put(c.mask(box(px - 4, CEIL, px + 30, CEIL + 14)), STONE_DARK)


def lantern(c, x, y):
    c.put(c.mask(lambda p: (p.rect(x - 6, y, x + 6, y + 18), p.rect(x - 1, y - 14, x + 1, y))), (40, 40, 44))
    c.put(c.mask(lambda p: p.rect(x - 4, y + 2, x + 4, y + 16)), LAMP)
    c.light(c.mask(lambda p: p.ellipse(x, y + 10, 90, 70), blur=18), LAMP, 0.22)


def rails(c, x0, x1):
    c.put(c.mask(lambda p: [p.rect(x, FLOOR - 4, x + 10, FLOOR) for x in range(int(x0), int(x1), 28)]), PLANK_DARK)
    c.put(c.mask(lambda p: p.rect(x0, FLOOR - 6, x1, FLOOR - 4)), RAIL)


def drain_shaft(c, k):
    x0, x1 = DRAIN
    shaft = c.mask(box(x0, STREET, x1, WATERFRONT_H))
    c.put(shaft, STONE_DARK)
    c.put(shaft * c.mask(lambda p: [p.rect(x0, y, x1, y + 1.2) for y in range(STREET + 14, WATERFRONT_H, 14)]), scale(STONE_DARK, 0.7))
    c.tone(shaft * np.clip((c.y - STREET) / 100, 0, 1), -0.6)
    c.put(c.mask(lambda p: [p.rect(x, STREET - 6, x + 14, STREET) for x in (x0 - 14, x1)]), STONE)
    c.put(c.mask(lambda p: [p.rect(x, STREET - 6, x + 14, STREET - 4) for x in (x0 - 14, x1)]), mix(STONE, (255, 255, 255), 0.3))


def drain_grate(c, k):
    x0, x1 = DRAIN
    c.put(c.mask(box(x0, STREET, x1, STREET + 10)), IRON)
    c.put(c.mask(lambda p: [p.rect(x, STREET + 1, x + 4, STREET + 9) for x in range(x0 + 6, x1 - 4, 10)]), (20, 20, 24))
    c.put(c.mask(box(x0, STREET, x1, STREET + 2)), IRON_LIGHT)
    # The street's stone under it, so the closed drain reads as street.
    c.put(c.mask(box(x0, STREET + 10, x1, WATERFRONT_H)), STONE_DARK)
    c.put(c.mask(lambda p: [p.rect(x0, y, x1, y + 1.2) for y in range(STREET + 24, WATERFRONT_H, 16)]), scale(STONE_DARK, 0.7))


def west(c, k):
    bricks(c, 16, 1024, CEIL, FLOOR, "tunnel_w")
    rails(c, 16, CUT[0])
    ribs(c, 16, 1024)
    for x in (200, 620, 980):
        lantern(c, x, 200)
    # The handcart of undeclared goods on the rails.
    hx = 420
    c.put(c.mask(lambda p: (p.rect(hx, FLOOR - 60, hx + 180, FLOOR - 24), p.line([(hx + 180, FLOOR - 50), (hx + 230, FLOOR - 80)], 4))), PLANK)
    c.put(c.mask(lambda p: [p.ellipse(x, FLOOR - 16, 14) for x in (hx + 36, hx + 144)]), IRON)
    c.put(c.mask(lambda p: [p.ellipse(x, FLOOR - 16, 4) for x in (hx + 36, hx + 144)]), IRON_LIGHT)
    # A crate of parrots, their heads through the slats.
    c.put(c.mask(box(hx + 6, FLOOR - 120, hx + 80, FLOOR - 60)), PLANK_DARK)
    c.put(c.mask(lambda p: [p.rect(hx + 6, y, hx + 80, y + 6) for y in (FLOOR - 120, FLOOR - 92, FLOOR - 66)]), PLANK)
    for j, px in enumerate((hx + 22, hx + 44, hx + 66)):
        py = FLOOR - 106 + (j % 2) * 26
        c.put(c.mask(lambda p: p.ellipse(px, py, 7, 7)), (PARROT, (220, 60, 50), (60, 120, 220))[j])
        c.put(c.mask(lambda p: p.poly([(px + 5, py - 2), (px + 11, py + 2), (px + 5, py + 4)])), (40, 40, 40))
        c.put(c.mask(lambda p: p.ellipse(px + 2, py - 2, 1.3)), (20, 20, 20))
    # A rolled carpet, a harp.
    c.put(c.mask(lambda p: p.rect(hx + 84, FLOOR - 82, hx + 176, FLOOR - 60)), (150, 50, 60))
    c.put(c.mask(lambda p: [p.rect(x, FLOOR - 82, x + 3, FLOOR - 60) for x in (hx + 100, hx + 140)]), GOLD_DARK)
    c.put(c.mask(lambda p: (p.line([(hx + 150, FLOOR - 82), (hx + 150, FLOOR - 170)], 4),
                            p.line([(hx + 150, FLOOR - 170), (hx + 190, FLOOR - 150), (hx + 176, FLOOR - 82)], 4))), GOLD)
    c.put(c.mask(lambda p: [p.line([(hx + 150, y), (hx + 150 + (y - (FLOOR - 170)) * 0.3, y)], 0.8) for y in range(FLOOR - 160, FLOOR - 90, 10)]), CHALK)
    # The chute from the Drowned Compass's cellar, a barrel stuck in it.
    cx = 760
    c.put(c.mask(lambda p: p.poly([(cx, 16), (cx + 80, 16), (cx + 120, 300), (cx + 40, 300)])), PLANK_DARK)
    c.put(c.mask(lambda p: [p.line([(cx + 4 + i * 0.0, 16), (cx + 44, 300)], 1.2) for i in range(1)]), PLANK)
    barrel(c, cx + 70, 230, 26)
    c.put(c.mask(box(cx + 20, 60, cx + 120, 82)), SAIL)
    c.put(c.mask(lambda p: [p.rect(x, 68, x + 6, 74) for x in range(cx + 28, cx + 112, 10)]), (40, 30, 30))


def east(c, k):
    bricks(c, 1024, W - 16, CEIL, FLOOR, "tunnel_e")
    rails(c, CUT[1], 1600)
    ribs(c, 1024, 1700)
    # Barrels and crates waiting by the shaft for a quiet night.
    for x in (1380, 1426):
        barrel(c, x, FLOOR - 22, 21)
    barrel(c, 1403, FLOOR - 62, 21)
    for (cx0, cy0, cx1) in ((1820, FLOOR - 56, 1880), (1830, FLOOR - 104, 1874)):
        cm = c.mask(box(cx0, cy0, cx1, cy0 + 48 if cy0 < FLOOR - 56 else FLOOR))
        c.put(cm, PLANK)
        c.put(cm * c.mask(lambda p: (p.line([(cx0, cy0), (cx1, cy0 + 48)], 2.4), p.line([(cx1, cy0), (cx0, cy0 + 48)], 2.4))), PLANK_DARK)
    lantern(c, 1300, 200)
    # The drain's shaft, in its fall of street light.
    s0, s1 = DRAIN
    c.put(c.mask(box(s0, 16, s1, CEIL)), STONE_DARK)
    c.light(c.mask(lambda p: p.poly([(s0, 16), (s1, 16), (s1 + 30, FLOOR), (s0 - 30, FLOOR)]), blur=10), DAYLIGHT, 0.2)
    # The chalk tally of runs (and of near things).
    tx = 1120
    c.put(c.mask(lambda p: [p.rect(tx + i * 10 + (i // 5) * 8, 300, tx + i * 10 + (i // 5) * 8 + 2, 340) for i in range(23)]), CHALK)
    c.put(c.mask(lambda p: [p.line([(tx - 2 + g * 58, 336), (tx + 46 + g * 58, 302)], 1.6) for g in range(4)]), CHALK)
    c.put(c.mask(lambda p: [p.ring(tx + 20 + i * 40, 370, 8, 1.6) for i in range(3)]), CHALK)
    c.put(c.mask(lambda p: [p.line([(tx + 12 + i * 40, 362), (tx + 28 + i * 40, 378)], 1.6) for i in range(3)]), CHALK)
    # Coils of rope, a stack of crates under the shaft's lever.
    c.put(c.mask(lambda p: [p.ring(1500, FLOOR - 14 - j * 6, 26 - j * 2, 3) for j in range(4)]), ROPE)
    # The plank wall at the end: boards, gaps, a draught and a light through.
    px0 = W - 140
    planks = c.mask(box(px0, CEIL, W - 16, FLOOR))
    c.put(planks, PLANK_DARK)
    c.put(c.mask(lambda p: [p.rect(px0, y, W - 16, y + 30) for y in range(CEIL + 4, FLOOR, 36)]), PLANK)
    c.put(c.mask(lambda p: [p.rect(px0, y + 30, W - 16, y + 36) for y in range(CEIL + 4, FLOOR, 36)]), (24, 18, 16))
    c.light(c.mask(lambda p: [p.rect(px0 + 10, y + 31, W - 26, y + 34) for y in range(CEIL + 4, FLOOR, 72)]), GOLD, 0.6)
    c.put(c.mask(lambda p: [p.line([(px0 - 6, y), (px0 - 40, y - 6)], 1) for y in (300, 380, 460)]), (200, 200, 200), 0.35)


def freight_cut(c, k):
    """Draw the flooded brick cut and both loading docks."""
    left, right = CUT
    wet = c.mask(box(left, FLOOR, right, BED))
    c.paint(wet, c.ramp([(FLOOR, (67, 112, 113)), (BED, (28, 57, 65))]))
    c.put(wet * c.mask(lambda p: [p.rect(left, y, right, y + 1) for y in range(FLOOR + 16, BED, 16)]),
          (26, 53, 58), 0.52)
    c.put(wet * c.mask(lambda p: [p.rect(x, y, x + 2, y + 16)
                                  for y in range(FLOOR, BED, 16)
                                  for x in range(left + (y // 16 % 2) * 16, right, 32)]), (26, 53, 58), 0.48)
    c.put(c.mask(box(left, FLOOR, right, FLOOR + 2)), (133, 186, 180), 0.65)
    c.put(c.mask(lambda p: [p.line([(x, FLOOR + 5), (x + 26, FLOOR + 5)], 1)
                            for x in range(left + 46, right - 40, 79)]), (158, 194, 175), 0.4)
    for x in (644, 1412):
        c.put(c.mask(box(x, 384, x + 14, FLOOR)), TIMBER)
        c.put(c.mask(box(x - 7, 393, x + 21, 414)), IRON)
        c.put(c.mask(lambda p: p.ellipse(x + 7, 403, 7)), IRON_LIGHT)
    c.put(c.mask(box(651, 399, 1419, 403)), IRON)
    c.put(c.mask(box(651, 399, 1419, 400)), IRON_LIGHT)
    for x0, x1 in LOADING_DOCKS:
        c.put(c.mask(box(x0, DOCK_TOP, x1, DOCK_TOP + 4)), mix(PLANK, SAIL, 0.28))
        c.put(c.mask(box(x0, DOCK_TOP + 4, x1, DOCK_TOP + 16)), PLANK)
        c.put(c.mask(box(x0, DOCK_TOP + 16, x1, DOCK_TOP + 20)), IRON)
        c.put(c.mask(lambda p: [p.rect(x, DOCK_TOP + 4, x + 2, DOCK_TOP + 16)
                                for x in range(x0 + 32, x1, 32)]), PLANK_DARK)


def freight_carrier(c, k):
    """Draw the pulley, cables, and cargo deck."""
    for x, foot in ((34, 18), (126, 142)):
        c.put(c.mask(lambda p: p.ellipse(x, 20, 9)), IRON)
        c.put(c.mask(lambda p: p.ellipse(x, 20, 4)), IRON_LIGHT)
        c.put(c.mask(lambda p: p.line([(x, 27), (foot, 164)], 2.4)), ROPE)
        c.put(c.mask(box(foot - 3, 158, foot + 3, 169)), IRON)
    c.put(c.mask(box(8, 164, 152, 169)), mix(PLANK, SAIL, 0.28))
    c.put(c.mask(box(8, 169, 152, 180)), PLANK)
    c.put(c.mask(box(8, 180, 152, 183)), IRON)
    c.put(c.mask(lambda p: [p.ellipse(x, 174, 2) for x in (14, 43, 80, 117, 146)]), IRON_LIGHT)


def coin_pile(c):
    """Draw the top of the pile at the height of the walk line."""
    top = [(112, 576), (144, 576), (200, 552), (244, 520), (280, 496),
           (384, 496), (436, 532), (496, 576)]
    heap = c.mask(lambda p: p.poly(top))
    c.put(heap, GOLD_DARK)
    c.tone(heap * (c.noise("coin_pile", 17, 8, 3) - 0.5), 0.4)
    rng = c.rand("hoard_coins")
    for color in (GOLD, mix(GOLD, LAMP, 0.35), scale(GOLD_DARK, 0.75)):
        coins = [(rng.uniform(112, 496), rng.uniform(496, 580), rng.uniform(2.0, 5.3), rng.uniform(0.9, 2.6))
                 for _ in range(460)]
        c.put(heap * c.mask(lambda p: [p.ellipse(*coin) for coin in coins]), color, 0.76)
    c.put(c.mask(lambda p: p.line(top, 2)) * heap, GOLD)


def hoard(c, k):
    bricks(c, 16, HOARD_W - 16, CEIL, FLOOR, "hoard")
    lantern(c, 260, 160)
    c.put(c.mask(box(16, 480, 84, FLOOR)), TIMBER)
    c.put(c.mask(box(16, 490, 66, FLOOR)), (39, 30, 32))
    c.put(c.mask(lambda p: p.line([(20, 481), (81, 481), (81, FLOOR)], 3)), PLANK)
    # The figurehead rests in a timber cradle.
    c.put(c.mask(box(91, 549, 145, FLOOR)), TIMBER)
    c.put(c.mask(lambda p: p.poly([(100, 460), (135, 460), (143, 553), (95, 553)])), (166, 117, 77))
    c.put(c.mask(lambda p: p.poly([(98, 428), (134, 425), (142, 478), (93, 477)])), (104, 61, 41))
    c.put(c.mask(lambda p: p.ellipse(116, 449, 15, 21)), (206, 158, 112))
    c.put(c.mask(lambda p: p.poly([(111, 472), (130, 480), (136, 543), (110, 527)])), COPPER)
    # The painting hangs from the wall.
    c.put(c.mask(lambda p: p.line([(320, 152), (350, 127), (380, 152)], 2)), ROPE)
    c.put(c.mask(box(300, 150, 400, 270)), GOLD_DARK)
    c.put(c.mask(box(310, 160, 390, 260)), (70, 90, 110))
    c.put(c.mask(lambda p: (p.ellipse(350, 200, 22, 26), p.poly([(316, 260), (384, 260), (370, 220), (330, 220)]))), (200, 170, 150))
    c.put(c.mask(lambda p: p.ellipse(350, 180, 24, 14)), (230, 230, 236))
    c.put(c.mask(lambda p: [p.ring(x, 204, 6, 1.4) for x in (340, 360)]), (40, 40, 40))
    c.put(c.mask(box(93, 329, 419, 361)), TIMBER)
    c.put(c.mask(box(97, 329, 415, 332)), PLANK)
    coin_pile(c)
    # The crown and candles rest on the pile.
    for x, y in ((226, 533), (449, 542)):
        c.put(c.mask(box(x - 6, y - 3, x + 7, y)), GOLD_DARK)
        c.put(c.mask(box(x - 2, y - 29, x + 3, y - 3)), BONE)
        c.put(c.mask(lambda p: p.ellipse(x, y - 32, 2.3, 5)), LAMP)
        c.light(c.mask(lambda p: p.ellipse(x, y - 32, 22), blur=8), LAMP, 0.26)
    c.put(c.mask(lambda p: p.ellipse(261, 496, 13, 13)), BONE)
    c.put(c.mask(lambda p: [p.ellipse(261 + dx, 495, 2.7, 2.8) for dx in (-5, 5)]), (30, 24, 24))
    c.put(c.mask(lambda p: p.poly([(247, 488), (248, 474), (255, 481), (261, 471),
                                  (267, 481), (274, 474), (275, 488)])), GOLD)
    # The smuggler sits beside the chest.
    c.put(c.mask(lambda p: (p.ellipse(403, 459, 11, 12), p.line([(403, 470), (400, 501)], 5),
                            p.line([(400, 501), (417, 504), (432, 529)], 4),
                            p.line([(401, 480), (377, 486)], 3))), BONE)
    c.put(c.mask(lambda p: [p.ellipse(403 + dx, 458, 2.4, 2.8) for dx in (-4, 4)]), (30, 24, 24))
    c.put(c.mask(lambda p: p.poly([(384, 454), (423, 454), (413, 442), (394, 442)])), (40, 30, 30))


PIECES: Dict[str, Piece] = {
    "port_drain_shaft": Piece((DRAIN[0] - 14, STREET - 6, DRAIN[1] + 14, WATERFRONT_H), drain_shaft),
    "port_drain_grate": Piece((DRAIN[0], STREET, DRAIN[1], WATERFRONT_H), drain_grate),
    "tunnel_west": Piece((16, 16, 1024, FLOOR), west),
    "tunnel_east": Piece((1024, 16, W - 16, FLOOR), east),
    "tunnel_freight_cut": Piece((624, 380, 1440, BED), freight_cut),
    "pirate_tunnel_freight_carrier": Piece((0, 0, 160, 184), freight_carrier),
    "hoard_room": Piece((16, 16, HOARD_W - 16, FLOOR), hoard),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
