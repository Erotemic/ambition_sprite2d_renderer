"""The rest of the Magical dimension's first rooms (Mary-O's): the gate
garden, the Starless Hollow under it, the dune road out of town.

Drawn in room coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/magical/make_specs.py`:

- `magical_gate_garden` (ground y 640; the star steps, one-way, at y 512 x
  960..1120 and y 416 x 1180..1308; the hatch's hole x 1376..1440):
  `garden_hill_low`, `garden_hill_high`, a round hill under each step, its
  flat top the step; `garden_hatch`, the hatch's boards over the hole and its
  lid propped open; `garden_star_tree`, a round tree whose fruit are stars;
  `garden_beds`, star flowers by the arrival.
- `magical_starless_hollow` (floor y 576, roof y 64; the shafts x 352..416
  and 2624..2688): where the stars go when nobody is looking, and sleep.
  `hollow_star_heap`, `hollow_star_heap_east`, stars asleep in a heap;
  `hollow_shaft_light_west`, `hollow_shaft_light_east`, the day falling down
  each shaft; `hollow_star_roots`, stars stuck in the roof like roots.
- `magical_stardune_road` (ground y 640; the dunes, one-way, at y 528 x
  1200..1392, y 448 x 1500..1692, y 512 x 2200..2456): `road_dunes`,
  `road_dune_far`, a dune under each; `road_cart`, a star cart left on the
  road, a wheel off, its stars spilled; `road_lamp`, the last star lamp,
  bent, the void's ink climbing it.

Animations: ``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

import math
from typing import Dict

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .magical_square_props import CREAM, GOLD, GOLD_DARK, INK, LILAC, LILAC_DARK, MINT, MINT_DARK, PINK, PINK_DARK, PINK_LIGHT, WOOD, star

FLOOR = 640
HOLLOW_FLOOR, HOLLOW_ROOF = 576, 64
STEP_LOW = (960, 1120, 512)
STEP_HIGH = (1180, 1308, 416)
HATCH = (1376, 1440)
TREE_X = 1720
SHAFT_WEST, SHAFT_EAST = (352, 416), (2624, 2688)
HEAP_X, HEAP_EAST_X = 1250, 2300
DUNE_A, DUNE_B, DUNE_C = (1200, 1392, 528), (1500, 1692, 448), (2200, 2456, 512)
CART_X = 520
LAMP_X = 2940
PAL = {"stone": LILAC, "stone_light": CREAM, "dark": INK, "lamp": GOLD}

WOOD_DARK = scale(WOOD, 0.75)
STAR_ASLEEP = (232, 214, 150)
STAR_ASLEEP_DARK = (176, 160, 110)
SAND = (240, 204, 170)
SAND_DARK = (214, 168, 140)
SAND_LIGHT = (252, 230, 204)
VOID = (40, 18, 60)
VOID_GLOSS = (110, 70, 150)


def slope(x_top, x_foot, top, n=14, s_curve=False):
    """The points of a side from a walk's end at `top` down to the ground at
    `x_foot`: a hill's round shoulder (a quarter ellipse), or a dune's S
    (`s_curve`: round over the top, easing out at the foot)."""
    pts = []
    for i in range(n + 1):
        t = i / n
        if s_curve:
            u = t * t * (3 - 2 * t)
            pts.append((x_top + (x_foot - x_top) * t, top + (FLOOR - top) * u))
        else:
            a = t * math.pi / 2
            pts.append((x_top + (x_foot - x_top) * math.sin(a), top + (FLOOR - top) * (1 - math.cos(a))))
    return pts


def mound(x0, x1, top, flare, s_curve=False):
    """A flat-topped mound: its top `x0..x1` at `top`, its feet `flare` out."""
    return [*slope(x0, x0 - flare, top, s_curve=s_curve)[::-1], *slope(x1, x1 + flare, top, s_curve=s_curve)]


def hill(c, x0, x1, top, body, cap, dots):
    """A round hill under a step: its flat top the step's walk (`x0..x1` at
    `top`), its sides rolling down to the ground; a cap of grass, dots."""
    flare = min(60, (FLOOR - top) * 0.4)
    c.put(c.mask(lambda p: p.poly(mound(x0, x1, top, flare))), body)
    c.put(c.mask(lambda p: p.poly([*slope(x1, x1 + flare, top), *slope(x1 - 18, x1 + flare - 18, top + 14)[::-1]])), scale(body, 0.9))
    # The grass cap, rolling over the shoulders in round tufts.
    c.put(c.mask(lambda p: (p.rect(x0, top - 2, x1, top + 10), [p.ellipse(x, top + 10, 10, 9) for x in range(int(x0) - 6, int(x1) + 10, 16)])), cap)
    c.put(c.mask(box(x0, top - 2, x1, top + 2)), mix(cap, (255, 255, 255), 0.4))
    # Its dots, as the old games had them.
    h = FLOOR - top
    for i in range(max(2, int((x1 - x0 + flare) * h / 7000))):
        dx = x0 + 14 + (i * 53) % max(1, int(x1 - x0 - 28))
        dy = top + 44 + (i * 37) % max(1, int(h - 64))
        c.put(c.mask(lambda p: p.ellipse(dx, dy, 6, 9)), dots)


def flower(c, x, y, colour, r=7):
    c.put(c.mask(lambda p: p.line([(x, y), (x, FLOOR)], 2)), MINT_DARK)
    star(c, x, y, r, colour, 0.5)
    c.put(c.mask(lambda p: p.ellipse(x, y, r * 0.3)), CREAM)


def hill_low(c, k):
    x0, x1, top = STEP_LOW
    hill(c, x0, x1, top, PINK, MINT, PINK_DARK)


def hill_high(c, k):
    x0, x1, top = STEP_HIGH
    hill(c, x0, x1, top, LILAC, MINT, LILAC_DARK)
    flower(c, x1 + 40, FLOOR - 12, GOLD)


def hatch(c, k):
    x0, x1 = HATCH
    # The boards across the hole (you stand on them; down drops you through).
    c.put(c.mask(box(x0 - 4, FLOOR, x1 + 4, FLOOR + 10)), WOOD)
    c.put(c.mask(lambda p: [p.rect(x, FLOOR, x + 1.5, FLOOR + 10) for x in range(x0 + 12, x1, 14)]), WOOD_DARK)
    c.put(c.mask(box(x0 - 4, FLOOR, x1 + 4, FLOOR + 2)), mix(WOOD, (255, 255, 255), 0.3))
    # Its frame, a stone kerb either side.
    for a, b in ((x0 - 22, x0 - 2), (x1 + 2, x1 + 22)):
        c.put(c.mask(box(a, FLOOR - 14, b, FLOOR)), CREAM)
        c.put(c.mask(box(a, FLOOR - 4, b, FLOOR)), LILAC_DARK, 0.5)
    # The lid, propped open against the west kerb, a star on its face.
    lid = [(x0 - 22, FLOOR - 14), (x0 - 10, FLOOR - 14), (x0 - 46, FLOOR - 86), (x0 - 58, FLOOR - 80)]
    c.put(c.mask(lambda p: p.poly(lid)), WOOD)
    c.put(c.mask(lambda p: p.line([(x0 - 16, FLOOR - 16), (x0 - 52, FLOOR - 82)], 1.5)), WOOD_DARK)
    star(c, x0 - 34, FLOOR - 50, 8, GOLD)
    c.put(c.mask(lambda p: p.ellipse(x0 - 12, FLOOR - 26, 3)), GOLD_DARK)


def star_tree(c, k):
    x, f = TREE_X, FLOOR
    # The trunk, a little bent, pink-barked.
    c.put(c.mask(lambda p: p.poly([(x - 16, f), (x + 18, f), (x + 10, f - 150), (x - 4, f - 220), (x - 14, f - 214), (x - 6, f - 150)])), PINK_DARK)
    c.put(c.mask(lambda p: p.poly([(x + 6, f), (x + 18, f), (x + 10, f - 150), (x + 2, f - 150)])), scale(PINK_DARK, 0.85))
    # The crown: round puffs, mint over cream.
    puffs = [(-90, -250, 70), (0, -300, 90), (90, -250, 72), (-40, -210, 60), (50, -205, 62)]
    c.put(c.mask(lambda p: [p.ellipse(x + dx, f + dy, r) for dx, dy, r in puffs]), MINT_DARK)
    c.put(c.mask(lambda p: [p.ellipse(x + dx - 6, f + dy - 8, r - 8) for dx, dy, r in puffs]), MINT)
    c.put(c.mask(lambda p: [p.ellipse(x + dx - 22, f + dy - 26, r * 0.35) for dx, dy, r in puffs]), mix(MINT, (255, 255, 255), 0.45))
    # Its fruit, stars; one fallen on the grass.
    for dx, dy in ((-110, -240), (-50, -320), (20, -260), (70, -330), (110, -220), (-20, -200), (60, -190)):
        star(c, x + dx, f + dy, 11, GOLD)
    star(c, x + 70, f - 8, 9, GOLD_DARK)


def beds(c, k):
    c.put(c.mask(box(64, FLOOR - 8, 300, FLOOR)), WOOD_DARK)
    c.put(c.mask(lambda p: [p.rect(x, FLOOR - 26, x + 5, FLOOR) for x in range(64, 300, 26)]), CREAM)
    c.put(c.mask(box(60, FLOOR - 22, 304, FLOOR - 18)), CREAM)
    for i, x in enumerate(range(80, 290, 22)):
        flower(c, x, FLOOR - 34 - (i * 7) % 14, (GOLD, PINK_LIGHT, LILAC)[i % 3])


def asleep(c, x, y, r, tilt=0.0, light=0.25):
    """A star asleep: dim, its eyes shut, a faint glow left in it."""
    c.put(c.mask(lambda p: p.ellipse(x, y, r * 1.5), blur=r * 0.45), GOLD, light)
    pts = []
    for i in range(10):
        a = -math.pi / 2 + tilt + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.5
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    c.put(c.mask(lambda p: p.poly(pts)), STAR_ASLEEP)
    c.put(c.mask(lambda p: p.ellipse(x + r * 0.15, y + r * 0.2, r * 0.42)), STAR_ASLEEP_DARK, 0.35)
    # Shut eyes: two little arcs, and a smile.
    for ex in (-0.22, 0.22):
        c.put(c.mask(lambda p: p.line([(x + (ex - 0.1) * r, y - 0.02 * r), (x + ex * r, y + 0.06 * r), (x + (ex + 0.1) * r, y - 0.02 * r)], max(1.0, r * 0.05))), INK)
    c.put(c.mask(lambda p: p.line([(x - 0.08 * r, y + 0.22 * r), (x, y + 0.27 * r), (x + 0.08 * r, y + 0.22 * r)], max(0.8, r * 0.04))), INK, 0.7)


def zzz(c, x, y, s):
    for i, (dx, dy, k) in enumerate(((0, 0, 1.0), (10, -14, 0.8), (18, -26, 0.6))):
        w = s * k
        c.put(c.mask(lambda p: p.line([(x + dx, y + dy), (x + dx + w, y + dy), (x + dx, y + dy + w), (x + dx + w, y + dy + w)], 1.4)), CREAM, 0.7 - i * 0.15)


def heap(c, cx, n_back, seed):
    f = HOLLOW_FLOOR
    for i in range(n_back):
        dx = ((i * 41 + seed) % 180) - 90
        r = 20 + (i * 7 + seed) % 10
        asleep(c, cx + dx, f - r * 0.7 - (14 if abs(dx) < 50 else 0), r, tilt=((i * 13) % 7 - 3) * 0.12, light=0.08)
    asleep(c, cx - 10, f - 54, 38, tilt=0.15, light=0.16)
    zzz(c, cx + 26, f - 110, 11)


def star_heap(c, k):
    heap(c, HEAP_X, 7, 3)


def star_heap_east(c, k):
    heap(c, HEAP_EAST_X, 5, 11)


def shaft_light(c, x0, x1):
    top, f = HOLLOW_ROOF, HOLLOW_FLOOR
    cx = (x0 + x1) / 2
    # The day comes down the shaft and spreads a little as it falls.
    c.put(c.mask(lambda p: p.poly([(x0, 0), (x1, 0), (x1 + 40, f), (x0 - 40, f)]), blur=18), PINK_LIGHT, 0.16)
    c.put(c.mask(lambda p: p.poly([(x0 + 14, 0), (x1 - 14, 0), (x1 + 10, f), (x0 - 10, f)]), blur=10), CREAM, 0.12)
    c.put(c.mask(lambda p: p.ellipse(cx, f, 90, 10), blur=6), CREAM, 0.3)
    # The shaft's stone lip, where the roof breaks.
    for a, b in ((x0 - 18, x0), (x1, x1 + 18)):
        c.put(c.mask(box(a, top - 8, b, top + 6)), LILAC_DARK)
        c.put(c.mask(box(a, top - 8, b, top - 4)), LILAC)


def shaft_light_west(c, k):
    shaft_light(c, *SHAFT_WEST)


def shaft_light_east(c, k):
    shaft_light(c, *SHAFT_EAST)


ROOTS = (700, 2420)


def star_roots(c, k):
    top = HOLLOW_ROOF
    x0, x1 = ROOTS
    for i, x in enumerate(range(x0 + 20, x1 - 20, 97)):
        ln = 30 + (i * 37) % 60
        c.put(c.mask(lambda p: p.line([(x, top), (x + (i % 3 - 1) * 8, top + ln)], 2.2)), LILAC_DARK)
        if i % 2 == 0:
            asleep(c, x + (i % 3 - 1) * 8, top + ln + 10, 9 + i % 4, tilt=0.3 * (i % 3 - 1), light=0.15)
        else:
            c.put(c.mask(lambda p: p.ellipse(x + (i % 3 - 1) * 8, top + ln, 3)), GOLD_DARK, 0.6)


def dune(c, x0, x1, top):
    """A soft dune under a walk (`x0..x1` at `top`): a round rise, its lee
    in shade, ripples of wind."""
    w = x1 - x0
    flare = 110
    c.put(c.mask(lambda p: p.poly(mound(x0, x1, top, flare, True))), SAND)
    c.put(c.mask(lambda p: p.poly([*slope(x1, x1 + flare, top, s_curve=True), *slope(x1 - 30, x1 + flare - 60, top + 10, s_curve=True)[::-1]])), SAND_DARK)
    c.put(c.mask(box(x0, top, x1, top + 3)), SAND_LIGHT)
    for j in range(3):
        y = top + 30 + j * 24
        if y > FLOOR - 10:
            break
        c.put(c.mask(lambda p: p.line([(x0 - 10 - j * 14, y), (x0 + w * 0.4, y - 5), (x1 - 20 + j * 4, y + 2)], 1.4)), SAND_DARK, 0.5)
    star(c, x0 + w * 0.7, top + 40, 4, GOLD_DARK)


def dunes(c, k):
    dune(c, *DUNE_A)
    dune(c, *DUNE_B)


def dune_far(c, k):
    dune(c, *DUNE_C)


def cart(c, k):
    x, f = CART_X, FLOOR
    # The bed, tipped: its east wheel off and lying by it.
    bed = [(x - 70, f - 52), (x + 64, f - 30), (x + 60, f - 6), (x - 74, f - 28)]
    c.put(c.mask(lambda p: p.poly(bed)), PINK)
    c.put(c.mask(lambda p: p.poly([(x - 74, f - 28), (x + 60, f - 6), (x + 60, f - 12), (x - 72, f - 34)])), PINK_DARK)
    c.put(c.mask(lambda p: p.line([(x - 70, f - 52), (x + 64, f - 30)], 3)), CREAM)
    # The shafts it was pulled by, down in the sand.
    c.put(c.mask(lambda p: p.line([(x - 72, f - 40), (x - 130, f - 4)], 3)), WOOD)
    # Its west wheel, still on.
    c.put(c.mask(lambda p: p.ring(x - 40, f - 22, 20, 4)), WOOD_DARK)
    c.put(c.mask(lambda p: [p.line([(x - 40 + 18 * math.cos(a), f - 22 + 18 * math.sin(a)), (x - 40, f - 22)], 2) for a in (0.3, 1.35, 2.4, 3.45, 4.5, 5.55)]), WOOD)
    c.put(c.mask(lambda p: p.ellipse(x - 40, f - 22, 4)), GOLD)
    # The other, off and flat on the road.
    c.put(c.mask(lambda p: p.ellipse(x + 104, f - 4, 22, 5)), WOOD_DARK)
    c.put(c.mask(lambda p: p.ellipse(x + 104, f - 6, 16, 3)), WOOD)
    # The load, spilled: stars, asleep where they rolled.
    for dx, dy, r in ((-20, -66, 12), (10, -58, 10), (36, -46, 9), (82, -10, 9), (130, -10, 8)):
        asleep(c, x + dx, f + dy, r, tilt=dx * 0.01, light=0.12)


def lamp(c, k):
    x, f = LAMP_X, FLOOR
    # The post, bent toward the castle; its star cold.
    post = [(x - 4, f), (x + 4, f), (x + 6, f - 90), (x + 30, f - 150), (x + 24, f - 154), (x - 2, f - 94)]
    c.put(c.mask(lambda p: p.poly(post)), LILAC_DARK)
    c.put(c.mask(box(x - 12, f - 8, x + 12, f)), LILAC_DARK)
    star(c, x + 34, f - 164, 11, STAR_ASLEEP_DARK, 0.5)
    # The void's ink, climbing it from the ground, glossy.
    goo = [(x - 26, f), (x + 26, f), (x + 14, f - 10), (x + 8, f - 40), (x + 10, f - 62), (x + 2, f - 58), (x - 2, f - 30), (x - 12, f - 12)]
    c.put(c.mask(lambda p: p.poly(goo)), VOID)
    c.put(c.mask(lambda p: [p.ellipse(x + 9, f - 64, 4, 6), p.ellipse(x - 20, f - 3, 9, 4)]), VOID)
    c.put(c.mask(lambda p: p.line([(x + 4, f - 50), (x + 6, f - 24)], 1.4)), VOID_GLOSS, 0.8)
    # A little of it drips from the arm; the castle is that way.
    c.put(c.mask(lambda p: [p.ellipse(x + 22, f - 140, 3, 5), p.ellipse(x + 22, f - 118, 2, 3)]), VOID)


PIECES: Dict[str, Piece] = {
    "garden_hill_low": Piece((STEP_LOW[0] - 80, STEP_LOW[2] - 4, STEP_LOW[1] + 80, FLOOR), hill_low),
    "garden_hill_high": Piece((STEP_HIGH[0] - 80, STEP_HIGH[2] - 4, STEP_HIGH[1] + 80, FLOOR), hill_high),
    "garden_hatch": Piece((HATCH[0] - 64, FLOOR - 92, HATCH[1] + 28, FLOOR + 12), hatch),
    "garden_star_tree": Piece((TREE_X - 190, FLOOR - 400, TREE_X + 190, FLOOR), star_tree),
    "garden_beds": Piece((56, FLOOR - 60, 310, FLOOR), beds),
    "hollow_star_heap": Piece((HEAP_X - 150, HOLLOW_FLOOR - 140, HEAP_X + 150, HOLLOW_FLOOR), star_heap),
    "hollow_star_heap_east": Piece((HEAP_EAST_X - 150, HOLLOW_FLOOR - 140, HEAP_EAST_X + 150, HOLLOW_FLOOR), star_heap_east),
    "hollow_shaft_light_west": Piece((SHAFT_WEST[0] - 100, 0, SHAFT_WEST[1] + 100, HOLLOW_FLOOR + 12), shaft_light_west),
    "hollow_shaft_light_east": Piece((SHAFT_EAST[0] - 100, 0, SHAFT_EAST[1] + 100, HOLLOW_FLOOR + 12), shaft_light_east),
    "hollow_star_roots": Piece((ROOTS[0], HOLLOW_ROOF, ROOTS[1], HOLLOW_ROOF + 120), star_roots),
    "road_dunes": Piece((DUNE_A[0] - 120, DUNE_B[2] - 4, DUNE_B[1] + 120, FLOOR), dunes),
    "road_dune_far": Piece((DUNE_C[0] - 120, DUNE_C[2] - 4, DUNE_C[1] + 120, FLOOR), dune_far),
    "road_cart": Piece((CART_X - 140, FLOOR - 90, CART_X + 140, FLOOR), cart),
    "road_lamp": Piece((LAMP_X - 40, FLOOR - 190, LAMP_X + 60, FLOOR), lamp),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
