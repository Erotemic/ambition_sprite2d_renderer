"""The props of the Haitian Revolution (the History dimension).

In 1789 Saint-Domingue, the west of the island of Ayiti, was the richest
colony of France. Its plantations made much of the sugar and the coffee
that Europe used, by the forced work of about half a million enslaved
people. In August 1791 the enslaved people of the north rose up. In 1802
Napoleon sent an army to bring slavery back, and the people of
Saint-Domingue defeated it. On 18 May 1803 at Arcahaie, the leaders took
the white out of the French flag, and Catherine Flon sewed the blue and
the red together: the first flag of Haiti. On 1 January 1804 Haiti
declared its independence, and every year on that day people eat soup
joumou, the squash soup that the enslaved were not allowed to eat.

These props are drawn in the cel style of the dimension's cast
(`targets/characters/_history_americas_kit.py`): flat colour, one shade, a
bold warm outline. They show things as they were, with no joke.

- ``history_sugar_works``: scenery, the sugar works of a plantation of the
  northern plain: a long low boiling house of stone with a roof of
  red tiles, a tall square chimney of brick at its end, and a round cattle
  mill beside it (a round platform of stone, a roof on posts over the
  three upright rollers, and the long sweep beam that the oxen pulled).
- ``history_sugarcane``: scenery, a dense stand of sugar cane: tall
  jointed stalks and long leaves that arch and hang.
- ``history_soup_pot``: scenery, a big iron pot of soup joumou on three
  stones over a fire, with steam that rises from it, and a whole orange
  squash (a joumou) beside it. Its ``idle`` row moves the flames and the
  steam.
- ``history_first_flag``: scenery, the first flag of Haiti (1803): two
  vertical bands, blue at the pole and red at the fly, sewn together with
  a seam that shows, on a pole of wood planted in a small mound of earth.
  Its ``idle`` row moves the cloth in the wind.

The numbers are frame pixels; the game shows each prop at half its frame.
No drop shadows: the game draws them.
"""

from __future__ import annotations

import math
import random
from typing import Callable, Dict, List, Tuple

from ..characters import _art_cast_kit as K
from ..characters import _history_americas_kit as A
from .art_props import _publisher

Point = Tuple[float, float]
STILL: List[Tuple[str, int, int]] = [("idle", 1, 1000)]
LOOP: List[Tuple[str, int, int]] = [("idle", 8, 120)]

WORKS_FRAME = (512, 384)
CANE_FRAME = (192, 256)
POT_FRAME = (160, 128)
FLAG_FRAME = (128, 320)

STONE = (204, 188, 158, 255)
STONE_LIGHT = (230, 218, 192, 255)
STONE_SHADE = (160, 142, 114, 255)
STONE_DARK = (112, 98, 78, 255)
PLASTER = (232, 222, 198, 255)
TILE = (184, 90, 56, 255)
TILE_LIGHT = (214, 122, 80, 255)
TILE_SHADE = (138, 62, 40, 255)
BRICK = (166, 80, 54, 255)
BRICK_LIGHT = (196, 108, 74, 255)
BRICK_SHADE = (120, 54, 36, 255)
WOOD = (130, 88, 54, 255)
WOOD_LIGHT = (168, 122, 80, 255)
WOOD_DARK = (84, 56, 36, 255)
THATCH = (196, 164, 100, 255)
THATCH_SHADE = (150, 120, 66, 255)
DARK = (54, 40, 34, 255)
CANE = (150, 176, 74, 255)
CANE_LIGHT = (196, 210, 110, 255)
CANE_SHADE = (104, 132, 54, 255)
CANE_JOINT = (122, 96, 64, 255)
LEAF = (92, 150, 64, 255)
LEAF_LIGHT = (140, 186, 88, 255)
LEAF_DARK = (62, 106, 50, 255)
LEAF_DRY = (186, 170, 104, 255)
IRON = (62, 58, 60, 255)
IRON_LIGHT = (110, 106, 108, 255)
IRON_DARK = (36, 32, 34, 255)
SOUP = (236, 160, 56, 255)
SOUP_LIGHT = (252, 200, 100, 255)
SQUASH = (226, 124, 40, 255)
SQUASH_LIGHT = (246, 168, 76, 255)
SQUASH_SHADE = (176, 84, 26, 255)
STEM = (110, 96, 50, 255)
FLAME = (255, 150, 50, 255)
FLAME_HOT = (255, 222, 120, 255)
EMBER = (220, 80, 36, 255)
ASH = (120, 112, 106, 255)
STEAM = (246, 244, 238, 255)
EARTH = (150, 84, 54, 255)
EARTH_LIGHT = (186, 116, 76, 255)
EARTH_SHADE = (110, 60, 40, 255)
FLAG_BLUE = (30, 62, 150, 255)
FLAG_BLUE_LIGHT = (58, 94, 182, 255)
FLAG_BLUE_SHADE = (20, 42, 108, 255)
FLAG_RED = (200, 36, 44, 255)
FLAG_RED_LIGHT = (226, 74, 74, 255)
FLAG_RED_SHADE = (146, 24, 34, 255)
THREAD = (244, 236, 214, 255)


def _rect(x0: float, y0: float, x1: float, y1: float) -> List[Point]:
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def _phase(i: int, n: int) -> float:
    return i / float(max(1, n))


# ---------------------------------------------------------------------------
# The sugar works.
# ---------------------------------------------------------------------------


def _courses(f: K.Frame, x0: float, x1: float, y0: float, y1: float, row: float, block: float, colour, seed: str) -> None:
    """Courses of cut stone on a wall: a joint along each course, and a
    joint between each two blocks, offset from course to course."""
    rng = random.Random(seed)
    y = y1 - row
    k = 0
    while y > y0 + 1.0:
        f.ink([(x0 + 1.0, y), (x1 - 1.0, y)], 0.8, colour)
        x = x0 + (block * 0.5 if k % 2 else 0.0) + rng.uniform(0.0, block * 0.3)
        while x < x1 - 2.0:
            if x > x0 + 2.0:
                f.ink([(x, y), (x, y + row)], 0.8, colour)
            x += block * rng.uniform(0.8, 1.2)
        y -= row
        k += 1


def _arch(f: K.Frame, cx: float, foot: float, w: float, h: float, inside, glow: float = 0.0) -> None:
    """An arched opening in a wall of stone: dressed stones round it and a
    dark inside. With `glow` a little firelight shows deep in it."""
    r = w / 2.0
    spring = foot - h + r
    pts = [(cx - r, foot)] + [(cx - r * math.cos(a), spring - r * math.sin(a)) for a in [math.pi * k / 12.0 for k in range(13)]] + [(cx + r, foot)]
    out = [(cx - r - 4.0, foot)] + [(cx - (r + 4.0) * math.cos(a), spring - (r + 4.0) * math.sin(a)) for a in [math.pi * k / 12.0 for k in range(13)]] + \
        [(cx + r + 4.0, foot)]
    f.poly(out, STONE_LIGHT, body=False)
    for k in range(1, 12, 2):
        a = math.pi * k / 12.0
        f.ink([(cx - r * math.cos(a), spring - r * math.sin(a)), (cx - (r + 4.0) * math.cos(a), spring - (r + 4.0) * math.sin(a))], 0.8, STONE_SHADE)
    f.poly(pts, inside, body=False)
    if glow:
        f.ellipse(cx, foot - 2.0, r * 0.8, 2.4, K.alpha(EMBER, 0.9 * glow), body=False)
        f.glow(cx, foot - 6.0, r * 0.8, K.alpha(FLAME, 0.18 * glow))


def _draw_works(anim: str, i: int, n: int):
    w, h = WORKS_FRAME
    f = K.Frame(WORKS_FRAME)
    foot = h - 8.0
    # The chimney first: it stands at the far end, behind the roof.
    cx0, cx1, top = 374.0, 412.0, 22.0
    chim = [(cx0, foot), (cx1, foot), (cx1 - 4.0, top + 10.0), (cx0 + 4.0, top + 10.0)]
    f.poly(chim, BRICK)
    f.poly([(cx1 - 12.0, foot), (cx1, foot), (cx1 - 4.0, top + 10.0), (cx1 - 14.0, top + 10.0)], BRICK_SHADE, body=False)
    y = foot - 6.0
    k = 0
    while y > top + 12.0:
        frac = (foot - y) / (foot - top - 10.0)
        xl, xr = cx0 + 4.0 * frac, cx1 - 4.0 * frac
        f.ink([(xl + 1.0, y), (xr - 1.0, y)], 0.7, BRICK_SHADE)
        for x in [xl + 6.0 + 12.0 * j + (6.0 if k % 2 else 0.0) for j in range(4)]:
            if x < xr - 2.0:
                f.ink([(x, y), (x, y + 6.0)], 0.7, BRICK_SHADE)
        y -= 6.0
        k += 1
    # Its cap: a band of brick that steps out, and a dark mouth.
    f.poly(_rect(cx0, top + 2.0, cx1, top + 12.0), BRICK_LIGHT)
    f.poly(_rect(cx0 + 2.0, top + 9.0, cx1 - 2.0, top + 12.0), BRICK_SHADE, body=False)
    f.poly(_rect(cx0 + 5.0, top + 2.0, cx1 - 5.0, top + 5.0), DARK, body=False)
    # A thin, quiet wisp of smoke from its mouth.
    t = _phase(i, n)
    for k in range(4):
        s = (k + t) / 4.0
        f.ellipse(cx0 + 20.0 - 14.0 * s, top - 2.0 - 4.0 * s, 4.0 + 4.0 * s, 2.6 + 1.6 * s, K.alpha(STEAM, 0.35 * (1.0 - s)), body=False)

    # The boiling house: long and low, walls of stone under a roof of tiles.
    x0, x1, eave, ridge = 168.0, 440.0, 268.0, 206.0
    f.poly(_rect(x0, eave - 4.0, x1, foot), STONE)
    f.poly(_rect(x0, eave - 4.0, x1, eave + 10.0), STONE_SHADE, body=False)
    _courses(f, x0, x1, eave + 10.0, foot, 11.0, 26.0, STONE_SHADE, "history_sugar_works:wall")
    # Quoins of lighter stone at the corners.
    for xc in (x0, x1 - 12.0):
        for j, yq in enumerate(range(int(foot) - 14, int(eave) + 8, -14)):
            ww = 12.0 if j % 2 else 8.0
            xa = xc if xc == x0 else x1 - ww
            f.poly(_rect(xa, yq, xa + ww, yq + 12.0), STONE_LIGHT, body=False)
    # The arched openings: the door of the boiling house, and the arches
    # where the coppers' fires were fed; a little fire glows in one.
    for k, cx in enumerate((206.0, 262.0, 318.0, 374.0)):
        if k == 1:
            _arch(f, cx, foot, 36.0, 74.0, DARK)
            f.poly(_rect(cx - 16.0, foot - 54.0, cx - 2.0, foot), WOOD, body=False)
            f.ink([(cx - 9.0, foot - 54.0), (cx - 9.0, foot)], 0.8, WOOD_DARK)
        else:
            _arch(f, cx, foot - 30.0, 20.0, 34.0, DARK)
    # The low mouth of a furnace under the coppers, with its embers.
    _arch(f, 298.0, foot, 22.0, 18.0, DARK, glow=1.0)
    for k in range(3):
        x = 292.0 + k * 6.0
        f.poly([(x - 3.0, foot - 1.0), (x + 3.0, foot - 1.0), (x + 0.6, foot - 7.0 - 2.0 * (k % 2))], FLAME, body=False)
    # The ground line along the foot of the wall.
    f.ink([(x0 + 1.0, foot - 1.0), (x1 - 1.0, foot - 1.0)], 1.2, STONE_DARK)
    # The roof of red tiles: rows of round tiles down the slope, with a
    # hip at each end and a ridge of tiles on top.
    roof = [(x0 - 14.0, eave + 2.0), (x1 + 10.0, eave + 2.0), (x1 - 30.0, ridge), (x0 + 30.0, ridge)]
    f.poly(roof, TILE)
    # The hip at the far end is in shade.
    f.poly([(x1 + 10.0, eave + 2.0), (x1 - 30.0, ridge), (x1 - 8.0, eave + 2.0)], TILE_SHADE, body=False)

    def edges(y: float) -> Tuple[float, float]:
        u = (y - ridge) / (eave + 2.0 - ridge)
        return x0 + 30.0 - 44.0 * u, x1 - 30.0 + 40.0 * u

    for k in range(1, 6):
        y = ridge + (eave + 2.0 - ridge) * k / 6.0
        xl, xr = edges(y)
        f.ink([(xl + 2.0, y), (xr - 2.0, y)], 1.2, TILE_SHADE)
        f.ink([(xl + 2.0, y - 2.0), (xr - 2.0, y - 2.0)], 0.8, TILE_LIGHT)
    # The rows of round tiles down the slope, kept inside the roof.
    x = x0 - 6.0
    while x < x1 + 6.0:
        top_x, bot_x = x + 6.0, x - 2.0
        ya, yb = ridge + 2.0, eave
        la, ra = edges(ya)
        lb, rb = edges(yb)
        if la + 2.0 < top_x < ra - 2.0 and lb + 2.0 < bot_x < rb - 2.0:
            f.ink([(top_x, ya), (bot_x, yb)], 0.9, K.alpha(TILE_SHADE, 0.8))
        elif lb + 2.0 < bot_x < rb - 2.0:
            # Clip the row where it meets the hip.
            for y in (ya + (yb - ya) * j / 10.0 for j in range(1, 10)):
                xx = top_x + (bot_x - top_x) * (y - ya) / (yb - ya)
                l, r = edges(y)
                if l + 2.0 < xx < r - 2.0:
                    f.ink([(xx, y), (bot_x, yb)], 0.9, K.alpha(TILE_SHADE, 0.8))
                    break
        x += 9.0
    f.limb([(x0 + 30.0, ridge), (x1 - 30.0, ridge)], 5.0, TILE_LIGHT)
    f.ink([(x0 + 30.0, ridge + 1.6), (x1 - 30.0, ridge + 1.6)], 1.0, TILE_SHADE)
    f.ink([(x0 - 12.0, eave + 1.0), (x1 + 8.0, eave + 1.0)], 1.4, TILE_SHADE)

    # The cattle mill: a round platform of stone with the three rollers in
    # its middle under a roof on posts, and the sweep beam the oxen pulled.
    mx, top_y, rx, ry = 100.0, 344.0, 80.0, 16.0
    f.poly([(mx - rx, top_y), (mx + rx, top_y), (mx + rx, foot), (mx - rx, foot)], STONE)
    f.poly([(mx + rx * 0.4, top_y), (mx + rx, top_y), (mx + rx, foot), (mx + rx * 0.4, foot)], STONE_SHADE, body=False)
    _courses(f, mx - rx, mx + rx, top_y, foot, 10.0, 22.0, STONE_SHADE, "history_sugar_works:mill")
    f.ellipse(mx, top_y, rx, ry, STONE_LIGHT)
    f.ellipse(mx, top_y + 1.0, rx - 8.0, ry - 4.0, (196, 176, 140, 255), body=False)
    # The posts at the back, the rollers in their frame, the posts in front.
    posts = [(mx - 60.0, top_y - 4.0), (mx + 60.0, top_y - 4.0)]
    for x, y in posts:
        f.limb([(x, y), (x, 276.0)], 5.0, WOOD_DARK)
    f.poly(_rect(mx - 22.0, 292.0, mx + 22.0, 298.0), WOOD)
    # The three rollers: upright drums of iron, each lit on its left side.
    for k, dx in enumerate((-13.0, 13.0, 0.0)):
        f.poly(_rect(mx + dx - 6.4, 300.0, mx + dx + 6.4, top_y - 2.0), IRON_LIGHT if k == 2 else IRON)
        f.poly(_rect(mx + dx + 2.0, 300.0, mx + dx + 6.4, top_y - 2.0), IRON_DARK, body=False)
        f.limb([(mx + dx - 3.4, 302.0), (mx + dx - 3.4, top_y - 5.0)], 1.6, (164, 160, 160, 255), body=False)
        f.ellipse(mx + dx, 300.0, 6.4, 2.4, IRON_LIGHT)
    f.limb([(mx - 22.0, 294.0), (mx - 22.0, top_y - 2.0)], 4.0, WOOD)
    f.limb([(mx + 22.0, 294.0), (mx + 22.0, top_y - 2.0)], 4.0, WOOD)
    # A trough of wood that takes the juice out to the boiling house.
    f.poly([(mx + 24.0, top_y - 6.0), (x0 + 4.0, top_y + 4.0), (x0 + 4.0, top_y + 8.0), (mx + 24.0, top_y - 2.0)], WOOD)
    f.ink([(mx + 24.0, top_y - 5.0), (x0 + 4.0, top_y + 5.0)], 0.8, WOOD_DARK)
    # The sweep beam: from the top of the middle roller out over the ring.
    f.limb([(mx, 296.0), (mx - 74.0, 318.0)], 4.6, WOOD)
    f.ink([(mx - 2.0, 295.0), (mx - 72.0, 316.6)], 0.8, WOOD_LIGHT)
    f.limb([(mx - 70.0, 318.0), (mx - 66.0, 332.0)], 2.4, WOOD_DARK)
    for x, y in ((mx - 40.0, top_y + 8.0), (mx + 40.0, top_y + 8.0)):
        f.limb([(x, y), (x, 280.0)], 5.0, WOOD)
        f.ink([(x - 1.2, y - 2.0), (x - 1.2, 282.0)], 0.8, WOOD_LIGHT)
    # The roof over the mill: a low cone of thatch.
    roof = [(mx - 74.0, 284.0), (mx - 40.0, 254.0), (mx, 226.0), (mx + 40.0, 254.0), (mx + 74.0, 284.0), (mx, 290.0)]
    f.poly(roof, THATCH)
    f.poly([(mx, 226.0), (mx + 40.0, 254.0), (mx + 74.0, 284.0), (mx + 20.0, 288.0)], THATCH_SHADE, body=False)
    for k in range(12):
        u = -1.0 + 2.0 * k / 11.0
        f.ink([(mx + u * 4.0, 230.0), (mx + u * 70.0, 286.0)], 0.8, THATCH_SHADE)
    f.ink([(mx - 74.0, 284.0), (mx, 290.0), (mx + 74.0, 284.0)], 1.4, THATCH_SHADE)
    f.ellipse(mx, 226.0, 4.0, 3.0, WOOD_DARK)
    return A.finish(f, width=1.4)


# ---------------------------------------------------------------------------
# Sugar cane.
# ---------------------------------------------------------------------------


def _leaf(f: K.Frame, base: Point, reach: float, rise: float, drop: float, width: float, colour, shade) -> None:
    """A long leaf of cane: from `base` it rises by `rise`, goes out by
    `reach` and hangs down by `drop` at its tip. Wide at its base, thin at
    its tip, with a pale midrib."""
    pts = []
    for k in range(13):
        u = k / 12.0
        x = base[0] + reach * u
        y = base[1] - rise * math.sin(math.pi * min(1.0, u * 1.2) * 0.5) * (1.0 - u) * 2.0 + drop * u * u
        pts.append((x, y))
    top, bot = [], []
    for k, (x, y) in enumerate(pts):
        wv = width * (1.0 - k / 12.0) ** 0.8 + 0.3
        top.append((x, y - wv))
        bot.append((x, y + wv))
    f.poly(top + bot[::-1], colour)
    f.poly(bot[:10][::-1] + [(x, y) for x, y in pts[:10]], shade, body=False)
    f.ink(pts[:9], 0.5, LEAF_LIGHT)


def _draw_cane(anim: str, i: int, n: int):
    w, h = CANE_FRAME
    f = K.Frame(CANE_FRAME)
    foot = h - 8.0
    rng = random.Random("history_sugarcane")
    stalks = []
    for k in range(15):
        x = 26.0 + 140.0 * (k + rng.uniform(-0.3, 0.3)) / 14.0
        stalks.append((x, rng.uniform(40.0, 92.0), rng.uniform(-0.12, 0.12), rng.random() < 0.5, k))
    # The back row first, darker.
    stalks.sort(key=lambda s: s[4] % 3)
    for x, top, lean, purple, k in stalks:
        back = k % 3 == 0
        dim = 0.82 if back else 1.0
        col, light, shade = K.shade(CANE, dim), K.shade(CANE_LIGHT, dim), K.shade(CANE_SHADE, dim)
        if purple:
            col = (col[0] + 20, max(0, col[1] - 24), col[2], 255)
        tip = (x + lean * (foot - top), top)
        f.limb([(x, foot), tip], 6.0, col)
        f.ink([(x - 1.6, foot), (tip[0] - 1.6, top)], 1.0, light)
        # The joints: a ring each 14 px, closer near the ground.
        y = foot - 10.0
        seg = 10.0
        while y > top + 10.0:
            u = (foot - y) / (foot - top)
            jx = x + (tip[0] - x) * u
            f.ink([(jx - 3.2, y), (jx + 3.2, y + 0.6)], 1.4, K.shade(CANE_JOINT, dim))
            f.ink([(jx - 3.0, y - 1.6), (jx + 3.0, y - 1.0)], 0.7, shade)
            y -= seg
            seg = min(18.0, seg + 1.2)
        # The leaves from the upper joints, to both sides, and the fan on top.
        lc, ld = K.shade(LEAF, dim), K.shade(LEAF_DARK, dim)
        for j in range(5):
            u = 0.55 + 0.1 * j
            bx, by = x + (tip[0] - x) * u, foot - (foot - top) * u
            side = 1.0 if (j + k) % 2 else -1.0
            reach = side * rng.uniform(26.0, 44.0)
            reach = max(8.0 - bx, min(w - 8.0 - bx, reach))
            _leaf(f, (bx, by), reach, rng.uniform(8.0, 18.0), rng.uniform(16.0, 34.0), 2.6, lc, ld)
        for d in (-1.0, 0.0, 1.0):
            reach = d * rng.uniform(10.0, 20.0) + 0.5
            reach = max(8.0 - tip[0], min(w - 8.0 - tip[0], reach))
            _leaf(f, tip, reach, rng.uniform(16.0, 24.0), rng.uniform(4.0, 12.0), 2.2, lc, ld)
        # A dry leaf that hangs low on the stalk.
        if k % 2:
            bx, by = x + (tip[0] - x) * 0.3, foot - (foot - top) * 0.3
            _leaf(f, (bx, by), max(8.0 - bx, min(w - 8.0 - bx, (12.0 if k % 4 == 1 else -12.0))), 4.0, 40.0, 2.0, K.shade(LEAF_DRY, dim),
                  K.shade(STEM, dim))
    # Trash of dry leaves at the foot.
    for k in range(9):
        x = 18.0 + k * 19.0
        f.ellipse(x, foot - 2.0, 10.0, 2.6, LEAF_DRY if k % 2 else STEM)
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# The pot of soup joumou.
# ---------------------------------------------------------------------------


def _squash(f: K.Frame, cx: float, cy: float, rx: float, ry: float) -> None:
    """A whole joumou: a round squash, flat at top and foot, with deep
    ribs, an orange skin with paler flecks, and a short dry stem."""
    f.ellipse(cx, cy, rx, ry, SQUASH)
    f.poly(K.ellipse_points(cx + rx * 0.35, cy + ry * 0.2, rx * 0.6, ry * 0.8, 20), SQUASH_SHADE, body=False)
    for k in (-0.62, -0.25, 0.12, 0.5):
        pts = [(cx + rx * k * math.cos(a) * 1.05, cy + ry * math.sin(a)) for a in [(-0.5 + j / 10.0) * math.pi for j in range(11)]]
        f.ink(pts, 1.0, SQUASH_SHADE)
    f.ellipse(cx - rx * 0.4, cy - ry * 0.4, rx * 0.22, ry * 0.18, SQUASH_LIGHT, body=False)
    for x, y in ((-0.2, 0.3), (0.3, -0.1), (-0.5, 0.0), (0.1, 0.55)):
        f.dot(cx + rx * x, cy + ry * y, 0.8, SQUASH_LIGHT)
    f.limb([(cx, cy - ry + 2.0), (cx + 2.0, cy - ry - 4.0), (cx + 5.0, cy - ry - 5.0)], 2.6, STEM)


def _draw_pot(anim: str, i: int, n: int):
    w, h = POT_FRAME
    f = K.Frame(POT_FRAME)
    foot = h - 8.0
    t = _phase(i, n)
    cyc = math.tau * t
    px = 70.0
    # The logs of the fire, pushed in from the sides, and the ash.
    f.ellipse(px, foot - 2.0, 30.0, 3.4, ASH)
    for x0, x1 in ((px - 42.0, px - 6.0), (px + 42.0, px + 6.0), (px - 30.0, px + 4.0)):
        f.limb([(x0, foot - 3.0), (x1, foot - 7.0)], 5.0, WOOD)
        f.ellipse(x1, foot - 7.0, 2.4, 2.4, EMBER, body=False)
    # The flames under the pot, lit from inside.
    for k in range(5):
        x = px - 16.0 + k * 8.0
        hh = 14.0 + 6.0 * math.sin(cyc * 2.0 + k * 1.9) + 4.0 * math.sin(cyc + k)
        sway = 2.0 * math.sin(cyc * 2.0 + k)
        f.poly([(x - 5.0, foot - 4.0), (x + 5.0, foot - 4.0), (x + 2.0 + sway, foot - 4.0 - hh * 0.6), (x + sway, foot - 4.0 - hh)], FLAME, body=False)
        f.poly([(x - 2.6, foot - 4.0), (x + 2.6, foot - 4.0), (x + sway * 0.6, foot - 4.0 - hh * 0.6)], FLAME_HOT, body=False)
    # The three stones that hold the pot.
    for x, r in ((px - 32.0, 9.0), (px + 30.0, 9.0), (px - 2.0, 7.0)):
        f.ellipse(x, foot - r * 0.8, r, r * 0.85, (150, 140, 128, 255) if r > 8.0 else (128, 118, 108, 255))
        f.ellipse(x - r * 0.3, foot - r * 1.15, r * 0.4, r * 0.25, (186, 178, 166, 255), body=False)
    # The pot: a round belly of black iron, a thick rim, two lugs.
    cy, rx, ry = foot - 38.0, 34.0, 24.0
    f.ellipse(px, cy, rx, ry, IRON)
    f.poly(K.ellipse_points(px + rx * 0.35, cy + ry * 0.15, rx * 0.62, ry * 0.85, 24), IRON_DARK, body=False)
    f.ellipse(px - rx * 0.5, cy - ry * 0.35, rx * 0.16, ry * 0.32, IRON_LIGHT, body=False)
    f.ellipse(px, cy + ry - 3.0, rx * 0.6, 4.0, K.alpha(FLAME, 0.35), body=False)
    rim = cy - ry + 4.0
    for side in (-1.0, 1.0):
        f.limb([(px + side * (rx - 2.0), rim + 4.0), (px + side * (rx + 5.0), rim + 2.0), (px + side * (rx + 5.0), rim + 8.0)], 2.6, IRON)
    f.ellipse(px, rim, rx - 2.0, 6.0, IRON_LIGHT)
    f.ellipse(px, rim + 0.6, rx - 5.0, 4.2, SOUP)
    f.ellipse(px - 8.0, rim, 9.0, 1.6, SOUP_LIGHT, body=False)
    for x in (px + 6.0, px + 14.0, px - 14.0):
        f.dot(x, rim + 1.0, 1.0, (120, 150, 60, 255))
    # The steam: soft puffs that rise and spread and fade.
    for k in range(6):
        s = (t + k / 6.0) % 1.0
        x = px + (k % 3 - 1) * 9.0 + 8.0 * math.sin(math.tau * (s * 0.7 + k * 0.31)) * s
        y = rim - 4.0 - s * (rim - 14.0)
        r = 3.0 + 7.0 * s
        f.ellipse(x, y, r, r * 0.75, K.alpha(STEAM, 0.55 * (1.0 - s) ** 1.2), body=False)
    # The joumou beside the fire.
    _squash(f, 132.0, foot - 13.0, 18.0, 13.0)
    return A.finish(f, width=1.3)


# ---------------------------------------------------------------------------
# The first flag of Haiti.
# ---------------------------------------------------------------------------


def _draw_flag(anim: str, i: int, n: int):
    w, h = FLAG_FRAME
    f = K.Frame(FLAG_FRAME)
    foot = h - 8.0
    t = _phase(i, n)
    cyc = math.tau * t
    pole_x, pole_top = 22.0, 18.0
    # The mound of earth that holds the pole, with stones round its foot.
    f.poly([(6.0, foot), (pole_x - 4.0, foot - 12.0), (pole_x + 6.0, foot - 13.0), (52.0, foot)], EARTH)
    f.poly([(pole_x + 6.0, foot - 13.0), (52.0, foot), (pole_x + 8.0, foot)], EARTH_SHADE, body=False)
    f.ink([(10.0, foot - 2.0), (pole_x - 4.0, foot - 11.0)], 1.0, EARTH_LIGHT)
    for x, r in ((12.0, 3.6), (40.0, 4.0), (30.0, 3.0)):
        f.ellipse(x, foot - r * 0.8, r, r * 0.8, (150, 140, 128, 255))
    # The pole: a straight stem of wood with a round knob on top.
    f.limb([(pole_x, foot - 6.0), (pole_x, pole_top + 4.0)], 4.6, WOOD)
    f.ink([(pole_x - 1.0, foot - 8.0), (pole_x - 1.0, pole_top + 6.0)], 0.9, WOOD_LIGHT)
    f.ellipse(pole_x, pole_top, 4.4, 4.4, WOOD_DARK)
    f.ellipse(pole_x - 1.2, pole_top - 1.2, 1.4, 1.4, WOOD_LIGHT, body=False)
    # The cloth: a grid of thin strips from the pole to the fly. A wave
    # runs out along it; it grows toward the fly, which is free.
    x0, x1, y0, y1 = pole_x + 2.0, 116.0, 26.0, 92.0
    cols = 28
    seam = 0.5

    def wave(u: float) -> float:
        return 7.5 * u ** 1.1 * math.sin(math.tau * (u * 1.1 - t) + 0.3) + 1.5 * u * math.sin(cyc * 2.0 + u * 7.0)

    def slope(u: float) -> float:
        return (wave(u + 0.01) - wave(u)) / 0.01

    def xs(u: float) -> float:
        # The fly comes in a little when the cloth waves.
        return x0 + (x1 - x0) * u * (0.97 + 0.03 * math.cos(cyc))

    for k in range(cols):
        u0, u1 = k / cols, (k + 1) / cols
        um = (u0 + u1) / 2.0
        blue = um < seam
        base, light, shade = (FLAG_BLUE, FLAG_BLUE_LIGHT, FLAG_BLUE_SHADE) if blue else (FLAG_RED, FLAG_RED_LIGHT, FLAG_RED_SHADE)
        s = max(-1.0, min(1.0, slope(um) / 14.0))
        tone, k_ = (light, -s) if s < 0.0 else (shade, s)
        colour = tuple(int(b + (c - b) * 0.45 * k_) for b, c in zip(base[:3], tone[:3])) + (255,)
        sag = 3.0 * um
        f.poly([(xs(u0), y0 + wave(u0)), (xs(u1) + 0.4, y0 + wave(u1)), (xs(u1) + 0.4, y1 + wave(u1) + sag * (u1 / max(um, 1e-3))), (xs(u0), y1 + wave(u0) + sag)],
               colour)
    # The seam where Catherine Flon sewed the blue to the red: a fold of
    # cloth along it, and the stitches of white thread across it.
    pts = []
    for k in range(17):
        v = k / 16.0
        y = y0 + (y1 - y0) * v + wave(seam) + 3.0 * seam * v
        pts.append((xs(seam), y))
    f.ink(pts, 1.4, FLAG_RED_SHADE)
    for k in range(1, 16):
        x, y = pts[k]
        f.ink([(x - 2.2, y - 1.0), (x + 2.2, y + 1.0)], 0.7, THREAD)
    # The edge of the cloth at the hoist, round the pole, and the ties.
    f.limb([(pole_x + 1.0, y0 - 1.0), (pole_x + 1.0, y1 + 1.0)], 3.0, K.shade(FLAG_BLUE, 0.85))
    for y in (y0 + 2.0, (y0 + y1) / 2.0, y1 - 2.0):
        f.ink([(pole_x - 3.0, y), (pole_x + 4.0, y + 1.0)], 1.4, THREAD)
    return A.finish(f, width=1.3)


# ---------------------------------------------------------------------------
# Publication.
# ---------------------------------------------------------------------------

SCENERY = ["prop", "scenery", "history", "americas"]

FRAMES: Dict[str, Tuple[int, int]] = {
    "history_sugar_works": WORKS_FRAME,
    "history_sugarcane": CANE_FRAME,
    "history_soup_pot": POT_FRAME,
    "history_first_flag": FLAG_FRAME,
}
DRAW: Dict[str, Callable] = {
    "history_sugar_works": _draw_works,
    "history_sugarcane": _draw_cane,
    "history_soup_pot": _draw_pot,
    "history_first_flag": _draw_flag,
}
DISPLAY = {
    "history_sugar_works": "Sugar Works",
    "history_sugarcane": "Sugar Cane",
    "history_soup_pot": "Pot of Soup Joumou",
    "history_first_flag": "First Flag of Haiti",
}
ROWS = {"history_soup_pot": LOOP, "history_first_flag": LOOP}


def _foot(name: str) -> Dict[str, Tuple[float, float]]:
    w, h = FRAMES[name]
    return {"foot": (w / 2.0, float(h))}


TARGETS: Dict[str, dict] = {
    name: _publisher(name, DISPLAY[name], ROWS.get(name, STILL), FRAMES[name], DRAW[name], _foot(name), "Scenery", SCENERY) for name in DISPLAY
}
