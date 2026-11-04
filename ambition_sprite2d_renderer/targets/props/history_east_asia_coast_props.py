"""The props of the East Asian coast (the History dimension): Jomon Japan,
ancient Taiwan and Silla.

At Sannai-Maruyama, in the north of Honshu, a Jomon village stood from
about 3900 to 2200 BCE. Its people lived in pit houses: a round floor dug
into the ground, and a steep cone of thatch over it, with a hole at the top
for the smoke of the hearth. They raised a great structure on six posts of
chestnut, each post about one metre thick, in two rows of three. In the
Middle Jomon (about 3000 BCE) potters of the region made the flame pots
(kaen doki): deep pots with cord marks, ridges of clay in swirls, and four
great crests that rise from the rim like flames.

In Taiwan (about 2500 BCE) the Austronesians worked green nephrite from
Fengtian. They cut it with a cord and wet sand, ground it on sandstone and
polished it into adzes, rings and ear ornaments. Later the lingling-o, a
slit ring with three knobs, went from here across the islands of the South
China Sea.

At Gyeongju, the capital of Silla, Queen Seondeok (r. 632 to 647 CE) built
Cheomseongdae, a tower of granite from which the sky was watched. Round the
city are the great tomb mounds of the kings and queens of Silla. In some of
them were gold crowns: a band with uprights shaped like trees and antlers,
hung with gold spangles and curved jade (gogok).

These props are drawn in the cel style of the dimension's cast
(`targets/characters/_history_americas_kit.py`): flat colour, one shade, a
bold warm outline. They show the skill of the people who made them.

- ``history_pit_dwelling``: scenery, a Jomon pit house: a steep cone of
  thatch that comes down almost to the ground, a low doorway under a small
  hood, and a smoke hole at the top with a thin wisp of smoke.
- ``history_flame_pot``: scenery, a Middle Jomon flame pot: a deep body
  with cord marks and swirls of raised clay, and four flame-like crests on
  its rim.
- ``history_six_pillars``: scenery, the great six-post structure of
  Sannai-Maruyama as it is rebuilt today: six chestnut posts in two rows of
  three, three open floors of beams and planks, braces, no walls and no
  roof. It stands behind ledges, so it is plain.
- ``history_jade_workshop``: scenery, a low bench with green nephrite: a
  block with a saw groove and a cord saw in it, a flat slab with a groove,
  three polished adzes, a slit ring, a lingling-o and a flat ring, and a
  sandstone grinder on the ground.
- ``history_cheomseongdae``: scenery, the observatory of Gyeongju: a
  bottle-shaped tower of 27 courses of granite on a square base of two
  steps, a square window at courses 13 to 15, and a frame of long beams in
  two tiers on its top. It stands behind ledges.
- ``history_royal_tumulus``: scenery, a great Silla tomb mound: a wide, low
  dome of grass with a low kerb of stones at its foot.
- ``history_gold_crown``: scenery, a Silla gold crown on a low wooden
  stand: a band, three uprights shaped like trees, two shaped like
  antlers, gold spangles, green curved jades and two long pendants.

The numbers are frame pixels; the game shows each prop at half its frame.
No drop shadows: the game draws them.
"""

from __future__ import annotations

import math
import random
from typing import Callable, Dict, List, Sequence, Tuple

from ..characters import _art_cast_kit as K
from ..characters import _history_americas_kit as A
from .art_props import _publisher

Point = Tuple[float, float]
RGBA = Tuple[int, int, int, int]
STILL: List[Tuple[str, int, int]] = [("idle", 1, 1000)]

PIT_DWELLING_FRAME = (192, 160)
FLAME_POT_FRAME = (64, 96)
SIX_PILLARS_FRAME = (256, 512)
JADE_WORKSHOP_FRAME = (160, 80)
CHEOMSEONGDAE_FRAME = (192, 448)
TUMULUS_FRAME = (384, 160)
GOLD_CROWN_FRAME = (96, 112)

THATCH = (176, 144, 88, 255)
THATCH_LIGHT = (212, 182, 120, 255)
THATCH_SHADE = (130, 102, 60, 255)
THATCH_DARK = (92, 70, 42, 255)
EARTH = (128, 98, 70, 255)
EARTH_LIGHT = (160, 126, 90, 255)
EARTH_SHADE = (96, 72, 52, 255)
DOORWAY = (52, 36, 28, 255)
SMOKE = (226, 220, 210, 255)
POLE = (120, 84, 52, 255)
POLE_DARK = (82, 56, 36, 255)

POT_CLAY = (188, 112, 62, 255)
POT_LIGHT = (220, 150, 94, 255)
POT_SHADE = (140, 78, 42, 255)
POT_DARK = (96, 52, 30, 255)

CHESTNUT = (128, 88, 58, 255)
CHESTNUT_LIGHT = (164, 120, 80, 255)
CHESTNUT_SHADE = (96, 64, 42, 255)
CHESTNUT_BACK = (88, 62, 44, 255)
CHESTNUT_BACK_SHADE = (70, 50, 36, 255)
TIMBER = (150, 110, 70, 255)
TIMBER_LIGHT = (184, 144, 96, 255)
TIMBER_SHADE = (110, 78, 50, 255)
LASHING = (70, 52, 36, 255)

JADE = (82, 146, 100, 255)
JADE_LIGHT = (150, 204, 160, 255)
JADE_SHADE = (52, 104, 74, 255)
JADE_DARK = (32, 72, 52, 255)
JADE_RAW = (104, 132, 96, 255)
JADE_RAW_SHADE = (72, 96, 70, 255)
GLINT = (236, 248, 236, 255)
BENCH = (138, 98, 62, 255)
BENCH_LIGHT = (176, 132, 86, 255)
BENCH_SHADE = (100, 70, 44, 255)
SANDSTONE = (196, 154, 112, 255)
SANDSTONE_LIGHT = (222, 186, 146, 255)
SANDSTONE_SHADE = (150, 112, 80, 255)
WET_SAND = (214, 200, 170, 255)
CORD = (198, 172, 120, 255)

GRANITE = (178, 168, 152, 255)
GRANITE_LIGHT = (206, 198, 182, 255)
GRANITE_SHADE = (140, 130, 118, 255)
GRANITE_DARK = (98, 90, 82, 255)
WINDOW = (40, 34, 32, 255)

GRASS = (120, 156, 82, 255)
GRASS_LIGHT = (156, 188, 106, 255)
GRASS_SHADE = (90, 124, 64, 255)
GRASS_DARK = (64, 94, 50, 255)
KERB = (166, 158, 144, 255)
KERB_LIGHT = (196, 190, 176, 255)
KERB_SHADE = (126, 118, 106, 255)

GOLD = (222, 172, 54, 255)
GOLD_LIGHT = (252, 226, 130, 255)
GOLD_SHADE = (170, 120, 32, 255)
GOLD_DARK = (118, 80, 24, 255)
GOGOK = (60, 150, 96, 255)
GOGOK_LIGHT = (140, 210, 160, 255)
GOGOK_SHADE = (36, 100, 66, 255)
STAND = (110, 72, 46, 255)
STAND_LIGHT = (148, 104, 68, 255)
STAND_SHADE = (78, 50, 34, 255)


def _ring(cx: float, cy: float, rx: float, ry: float, a0: float = 0.0, a1: float = 360.0, count: int = 36) -> List[Point]:
    """Points on an ellipse from the angle `a0` to `a1` (degrees; 0 is to
    the right, 90 is down)."""
    out: List[Point] = []
    for k in range(count + 1):
        a = math.radians(a0 + (a1 - a0) * k / float(count))
        out.append((cx + math.cos(a) * rx, cy + math.sin(a) * ry))
    return out


def _mix(p: Point, q: Point, u: float) -> Point:
    return (p[0] + (q[0] - p[0]) * u, p[1] + (q[1] - p[1]) * u)


# ---------------------------------------------------------------------------
# The pit dwelling.
# ---------------------------------------------------------------------------


def _draw_pit_dwelling(anim: str, i: int, n: int):
    w, h = PIT_DWELLING_FRAME
    f = K.Frame(PIT_DWELLING_FRAME)
    rng = random.Random("history_pit_dwelling")
    ground = h - 6.0
    cx = w / 2.0
    top_y = 30.0
    eave_y = ground - 13.0
    half = 82.0

    def side(u: float, s: float) -> Point:
        """A point on the edge of the cone: `u` is 0 at the top and 1 at the
        eave; `s` is -1 on the left and 1 on the right. The cone swells a
        little, as thatch does over its rafters."""
        x = cx + s * half * (u + 0.10 * math.sin(math.pi * u))
        return (x, top_y + (eave_y - top_y) * u)

    def sag(u: float) -> float:
        """The sag of a ring round the cone at `u`: a ring seen a little
        from above curves down in its middle."""
        return 7.0 * u

    def ring(u: float, dy: float = 0.0) -> List[Point]:
        (lx, ly), (rx, _) = side(u, -1.0), side(u, 1.0)
        pts = []
        for k in range(17):
            t = k / 16.0
            x = lx + (rx - lx) * t
            pts.append((x, ly + dy + sag(u) * math.sin(math.pi * t)))
        return pts

    # The bank of earth round the pit. The earth that came out of the pit
    # is heaped round its edge, and the eave of the roof rests on it.
    f.poly([(6.0, ground), (16.0, ground - 10.0), (cx, ground - 12.0), (w - 16.0, ground - 10.0), (w - 6.0, ground)], EARTH)
    f.poly([(cx + 30.0, ground - 11.0), (w - 16.0, ground - 10.0), (w - 6.0, ground), (cx + 36.0, ground)], EARTH_SHADE, body=False)
    f.ink([(12.0, ground - 7.0), (cx - 20.0, ground - 10.0)], 1.0, EARTH_LIGHT)
    # The cone of thatch.
    left = [side(k / 20.0, -1.0) for k in range(21)]
    right = [side(k / 20.0, 1.0) for k in range(21)]
    cone = left + ring(1.0)[1:-1] + right[::-1]
    f.poly(cone, THATCH)
    # The cone is lit from the left: a shade over its right third, and a
    # light band down its left side.
    shade_l = [_mix((cx, top_y), (cx + 26.0, eave_y + 5.0), k / 10.0) for k in range(11)]
    f.poly(shade_l + [p for p in ring(1.0) if p[0] > cx + 26.0] + right[::-1], THATCH_SHADE, body=False)
    lit = [_mix((cx - 6.0, top_y + 8.0), (cx - 60.0, eave_y + 4.0), k / 10.0) for k in range(11)]
    lit2 = [_mix((cx - 10.0, top_y + 14.0), (cx - 74.0, eave_y + 2.0), k / 10.0) for k in range(11)]
    f.poly(lit + lit2[::-1], THATCH_LIGHT, body=False)
    # The straw runs down the cone from the top to the eave.
    for k in range(40):
        t = (k + 0.5) / 40.0
        b = _mix(ring(1.0)[0], ring(1.0)[-1], t)
        b = (b[0], b[1] + sag(1.0) * math.sin(math.pi * t))
        a = _mix((cx, top_y), b, 0.22 + rng.uniform(0.0, 0.1))
        colour = THATCH_DARK if b[0] > cx + 30.0 else (THATCH_SHADE if k % 2 else THATCH_LIGHT)
        f.ink([a, _mix(a, b, 0.97)], 0.6, colour)
    # The courses of thatch: each course hangs over the one below it, and
    # its cut ends make a ragged line.
    for u in (0.36, 0.56, 0.76):
        line = ring(u)
        f.limb(line, 2.4, THATCH_SHADE, body=False)
        f.ink([(x, y - 1.6) for x, y in line[1:-1]], 1.0, THATCH_LIGHT)
        for x, y in line[1:-1]:
            for j in range(2):
                ex = x + rng.uniform(-3.0, 3.0)
                f.ink([(ex, y), (ex + rng.uniform(-0.6, 0.6), y + rng.uniform(2.0, 4.0))], 0.8, THATCH_DARK)
    # The ragged eave on the bank.
    for x, y in ring(1.0)[1:-1]:
        for j in range(3):
            ex = x + rng.uniform(-4.0, 4.0)
            f.limb([(ex, y - 3.0), (ex + rng.uniform(-1.0, 1.0), y + rng.uniform(0.5, 2.5))], 1.4, THATCH_SHADE)
    # The top: two poles cross over the smoke hole and hold a cap of
    # thatch. The hole is open toward us, and smoke from the hearth comes
    # out of it.
    f.poly([(cx - 9.0, top_y + 12.0), (cx, top_y + 2.0), (cx + 9.0, top_y + 12.0)], DOORWAY, body=False)
    f.poly([(cx - 13.0, top_y + 6.0), (cx, top_y - 4.0), (cx + 13.0, top_y + 6.0), (cx + 9.0, top_y + 8.0), (cx, top_y + 1.0), (cx - 9.0, top_y + 8.0)], THATCH)
    f.ink([(cx - 10.0, top_y + 5.0), (cx, top_y - 2.0)], 0.9, THATCH_LIGHT)
    f.limb([(cx - 4.0, top_y + 4.0), (cx + 8.0, top_y - 10.0)], 2.2, POLE)
    f.limb([(cx + 4.0, top_y + 4.0), (cx - 8.0, top_y - 10.0)], 2.2, POLE_DARK)
    wisp = [(cx + 1.0, top_y - 3.0), (cx - 2.0, top_y - 8.0), (cx + 1.0, top_y - 13.0), (cx + 5.0, top_y - 17.0), (cx + 4.0, top_y - 22.0)]
    for k in range(len(wisp) - 1):
        f.limb([wisp[k], wisp[k + 1]], 3.4 - 0.5 * k, K.alpha(K.shade(SMOKE, 0.86), 0.9 - 0.16 * k), body=False)
    # The door: a low opening under a small hood of thatch. One goes down
    # a step into the pit.
    dy0 = ground - 26.0
    door = [(cx - 11.0, ground - 2.0), (cx - 11.0, dy0 + 6.0), (cx - 7.0, dy0), (cx + 7.0, dy0), (cx + 11.0, dy0 + 6.0), (cx + 11.0, ground - 2.0)]
    f.poly(door, DOORWAY)
    f.poly([(cx - 11.0, ground - 2.0), (cx - 11.0, dy0 + 6.0), (cx - 6.0, dy0 + 1.0), (cx - 6.0, ground - 2.0)], K.shade(DOORWAY, 0.7), body=False)
    for x in (cx - 11.0, cx + 11.0):
        f.limb([(x, ground - 1.0), (x, dy0 + 4.0)], 2.2, POLE)
    hood = [(cx - 22.0, dy0 + 6.0), (cx, dy0 - 18.0), (cx + 22.0, dy0 + 6.0)]
    f.poly(hood, THATCH)
    f.poly([(cx, dy0 - 18.0), (cx + 22.0, dy0 + 6.0), (cx + 6.0, dy0 + 6.0)], THATCH_SHADE, body=False)
    for k in range(12):
        ex = cx - 20.0 + k * 40.0 / 11.0
        f.limb([(ex, dy0 + 4.0), (ex + rng.uniform(-0.8, 0.8), dy0 + 7.5)], 1.2, THATCH_SHADE)
    f.ink([(cx - 1.0, dy0 - 15.0), (cx - 18.0, dy0 + 3.0)], 0.9, THATCH_LIGHT)
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# The flame pot.
# ---------------------------------------------------------------------------


def _crest(f: K.Frame, x: float, y: float, s: float, mirror: float, colour: RGBA, light: RGBA, shade: RGBA) -> None:
    """One crest of a flame pot, that rises from the rim at (x, y). It is
    a thick coil of clay that rises, leans out like a flame and curls
    over at its tip, with a row of pointed teeth on its back like the comb
    of a cock. A loop of clay at its foot leaves a round hole. `mirror` is
    1 for a crest that leans to the right, -1 for one that leans left."""
    def P(pts: Sequence[Point]) -> List[Point]:
        return [(x + mirror * px * s, y + py * s) for px, py in pts]

    stem = [(0.0, 0.0), (-1.4, -8.0), (-0.6, -16.0), (2.6, -23.0), (8.0, -27.4), (13.4, -27.0)]
    curl = [(13.4, -27.0), (16.4, -23.6), (15.6, -19.2), (12.0, -18.0), (10.4, -20.6), (12.2, -22.4)]
    # The teeth stand on the outer side of the coil.
    for k in range(1, 5):
        (ax, ay), (bx, by) = stem[k], stem[k + 1]
        tx, ty = bx - ax, by - ay
        ln = math.hypot(tx, ty)
        tx, ty = tx / ln, ty / ln
        nx, ny = ty, -tx
        mx, my = (ax + bx) / 2.0, (ay + by) / 2.0
        f.poly(P([(mx - tx * 2.0, my - ty * 2.0), (mx + nx * 5.4 + tx * 0.6, my + ny * 5.4 + ty * 0.6), (mx + tx * 2.0, my + ty * 2.0)]), colour)
    f.limb(P(_ring(5.4, -9.0, 4.4, 4.6, 0.0, 360.0, 24)), 2.6 * s, colour)
    f.limb(P(stem), 4.2 * s, colour)
    f.limb(P(curl), 3.0 * s, colour)
    # Light on the inner edge of the coil, a shade under the curl.
    f.ink(P([(-2.2, -7.0), (-1.6, -15.4), (1.8, -22.6), (7.6, -26.8), (13.0, -26.8)]), 0.9 * s, light)
    f.ink(P([(15.4, -21.0), (12.8, -19.0)]), 0.8 * s, shade)
    f.ink(P(_ring(5.4, -9.0, 5.0, 5.2, 0.0, 90.0, 8)), 0.7 * s, shade)


def _draw_flame_pot(anim: str, i: int, n: int):
    w, h = FLAME_POT_FRAME
    f = K.Frame(FLAME_POT_FRAME)
    rng = random.Random("history_flame_pot")
    cx = w / 2.0
    foot = h - 5.0
    rim_y = 48.0
    # The half width of the body at each height: a deep pot, narrow at the
    # foot, a little waist under the rim, and a rim that opens out.
    prof = [(foot, 10.0), (foot - 6.0, 12.4), (78.0, 14.6), (66.0, 15.6), (58.0, 15.0), (53.0, 16.4), (rim_y, 19.0)]
    # The fourth crest is at the back: it shows only a little over the
    # rim, behind the front crest.
    _crest(f, cx + 2.0, rim_y - 2.0, 0.8, -1.0, POT_SHADE, POT_CLAY, POT_DARK)
    body = [(cx - r, y) for y, r in prof] + [(cx + r, y) for y, r in prof[::-1]]
    f.poly(body, POT_CLAY)
    f.ellipse(cx, foot - 0.6, 10.0, 1.6, POT_CLAY)
    # One shade on the right, and light down the left.
    f.poly([(cx + r * 0.42, y) for y, r in prof] + [(cx + r, y) for y, r in prof[::-1]], POT_SHADE, body=False)
    f.poly([(cx - r * 0.86, y) for y, r in prof[1:-1]] + [(cx - r * 0.62, y) for y, r in prof[-2:0:-1]], POT_LIGHT, body=False)
    # Cord marks: the potter rolled a twisted cord over the wet clay. The
    # marks are rows of short slanting strokes, the slant changes from
    # band to band.
    for band, (y0, y1) in enumerate(((foot - 3.0, 74.0), (74.0, 62.0))):
        y = y0
        while y > y1:
            r = 10.0 + (15.4 - 10.0) * (foot - y) / (foot - 62.0)
            for k in range(-6, 7):
                x = cx + k * r / 6.6
                d = 1.6 if band % 2 else -1.6
                f.ink([(x - d, y), (x + d, y - 2.4)], 0.5, POT_DARK if x > cx + r * 0.4 else POT_SHADE)
            y -= 3.2
    # A raised ridge divides the bands of cord marks.
    f.limb([(cx - 14.8, 74.6), (cx, 76.0), (cx + 14.8, 74.6)], 1.6, POT_LIGHT, body=False)
    f.ink([(cx - 14.0, 76.0), (cx, 77.4), (cx + 14.0, 76.0)], 0.6, POT_DARK)
    # The upper body: ridges of clay pressed on in swirls and S-curves,
    # each a coil with light on its top and a shade under it.
    for k, sx in enumerate((cx - 10.0, cx, cx + 10.0)):
        turn = 1.0 if k % 2 else -1.0
        coil = [(sx + turn * math.cos(t) * (4.2 - t * 0.42), 57.4 + math.sin(t) * (4.0 - t * 0.40)) for t in [j * 0.35 for j in range(22)]]
        f.limb(coil, 1.5, POT_LIGHT if sx < cx + 5.0 else POT_CLAY, body=False)
        f.ink([(x + 0.4, y + 0.8) for x, y in coil], 0.5, POT_DARK)
    f.limb([(cx - 15.0, 63.6), (cx, 64.8), (cx + 15.0, 63.6)], 1.4, POT_LIGHT, body=False)
    f.ink([(cx - 14.6, 64.8), (cx, 66.0), (cx + 14.6, 64.8)], 0.6, POT_DARK)
    for x in (cx - 10.0, cx + 1.0, cx + 11.0):
        f.limb([(x, 66.0), (x - 0.6, 72.6)], 1.2, POT_LIGHT, body=False)
    # The rim: a thick lip that opens out, with the dark mouth of the pot.
    f.ellipse(cx, rim_y, 19.4, 3.6, POT_CLAY)
    f.ellipse(cx, rim_y - 0.4, 16.4, 2.4, POT_DARK, body=False)
    f.limb(_ring(cx, rim_y, 19.0, 3.4, 0.0, 180.0, 18), 1.4, POT_LIGHT, body=False)
    # The crests at the two sides curl outward; the front crest stands in
    # the middle of the rim.
    _crest(f, cx - 12.5, rim_y + 1.0, 0.8, -1.0, POT_CLAY, POT_LIGHT, POT_DARK)
    _crest(f, cx + 12.5, rim_y + 1.0, 0.8, 1.0, POT_SHADE, POT_CLAY, POT_DARK)
    _crest(f, cx - 5.0, rim_y + 3.0, 0.96, 1.0, POT_CLAY, POT_LIGHT, POT_DARK)
    del rng
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# The six pillars.
# ---------------------------------------------------------------------------


def _post(f: K.Frame, x: float, top: float, foot: float, half: float, wood: RGBA, light: RGBA, shade: RGBA, seed: str) -> None:
    """One chestnut post: a whole trunk with its bark taken off, a little
    narrower at its top, with lines of grain and a shade on its right."""
    rng = random.Random(seed)
    th = half * 0.9
    f.poly([(x - half, foot), (x - th, top + 3.0), (x - th + 3.0, top), (x + th - 3.0, top), (x + th, top + 3.0), (x + half, foot)], wood)
    f.poly([(x + half * 0.35, foot), (x + th * 0.35, top + 1.0), (x + th - 3.0, top), (x + th, top + 3.0), (x + half, foot)], shade, body=False)
    f.poly([(x - half + 2.0, foot), (x - th + 2.0, top + 4.0), (x - th + 5.0, top + 4.0), (x - half + 5.0, foot)], light, body=False)
    f.ellipse(x, top + 0.6, th - 1.0, 1.8, light, body=False)
    for _ in range(int((foot - top) / 40.0)):
        gx = x + rng.uniform(-half * 0.5, half * 0.3)
        gy = rng.uniform(top + 10.0, foot - 30.0)
        f.ink([(gx, gy), (gx + rng.uniform(-0.6, 0.6), gy + rng.uniform(14.0, 30.0))], 0.7, shade)


def _floor(f: K.Frame, y: float, x0: float, x1: float, wood: RGBA, light: RGBA, shade: RGBA, planks: bool) -> None:
    """One open floor seen from its side: a deck of planks on a thick beam
    that is lashed to the posts. The beam's ends go a little past the
    posts."""
    f.poly([(x0, y), (x1, y), (x1, y + 9.0), (x0, y + 9.0)], wood)
    f.poly([(x0, y + 6.0), (x1, y + 6.0), (x1, y + 9.0), (x0, y + 9.0)], shade, body=False)
    f.ink([(x0 + 1.0, y + 1.2), (x1 - 1.0, y + 1.2)], 1.0, light)
    if planks:
        # The planks of the deck lie across the beam: their ends show as a
        # thin row above it.
        f.poly([(x0 + 4.0, y - 4.0), (x1 - 4.0, y - 4.0), (x1 - 4.0, y), (x0 + 4.0, y)], light)
        x = x0 + 4.0
        while x < x1 - 6.0:
            x += 9.0
            f.ink([(x, y - 3.6), (x, y - 0.4)], 0.6, shade)


def _draw_six_pillars(anim: str, i: int, n: int):
    w, h = SIX_PILLARS_FRAME
    f = K.Frame(SIX_PILLARS_FRAME)
    ground = h - 6.0
    top = 22.0
    xs = (34.0, 128.0, 222.0)
    half = 13.0
    floors = (372.0, 256.0, 140.0)
    back_dx, back_dy = 9.0, -7.0
    # The back row: the same posts and floors, behind and a little up, in
    # a darker colour.
    for k, x in enumerate(xs):
        _post(f, x + back_dx, top + back_dy, ground + back_dy, half * 0.92, CHESTNUT_BACK, CHESTNUT_BACK, CHESTNUT_BACK_SHADE, f"history_six_pillars back {k}")
    for y in floors:
        _floor(f, y + back_dy, xs[0] - 20.0 + back_dx, xs[-1] + 20.0 + back_dx, CHESTNUT_BACK, CHESTNUT_BACK, CHESTNUT_BACK_SHADE, False)
    # Cross beams go from the front row to the back row at each floor and
    # at the top. Their ends show beside the posts.
    for y in floors + (top + 18.0,):
        for x in xs:
            f.poly([(x + half - 1.0, y - 1.0), (x + half + back_dx, y - 1.0 + back_dy), (x + half + back_dx, y + 7.0 + back_dy), (x + half - 1.0, y + 7.0)], TIMBER_SHADE)
    # The front row of posts.
    for k, x in enumerate(xs):
        _post(f, x, top, ground, half, CHESTNUT, CHESTNUT_LIGHT, CHESTNUT_SHADE, f"history_six_pillars front {k}")
        # The foot of the post is set deep in the ground: a ring of earth.
        f.poly([(x - half - 6.0, ground), (x - half, ground - 4.0), (x + half, ground - 4.0), (x + half + 6.0, ground)], EARTH)
        f.poly([(x + 2.0, ground - 4.0), (x + half, ground - 4.0), (x + half + 6.0, ground), (x + 4.0, ground)], EARTH_SHADE, body=False)
    # Braces under the lowest floor: one long diagonal in each bay.
    for (xa, xb) in ((xs[0], xs[1]), (xs[1], xs[2])):
        f.limb([(xa + half - 1.0, floors[0] + 22.0), (xb - half + 1.0, ground - 52.0)], 5.0, TIMBER)
        f.ink([(xa + half, floors[0] + 21.0), (xb - half + 2.0, ground - 53.0)], 1.0, TIMBER_LIGHT)
    # The middle bays carry a light X of two thin braces.
    for (xa, xb) in ((xs[0], xs[1]), (xs[1], xs[2])):
        ya, yb = floors[1] + 16.0, floors[0] - 14.0
        f.limb([(xa + half - 1.0, ya), (xb - half + 1.0, yb)], 3.4, TIMBER_SHADE)
        f.limb([(xa + half - 1.0, yb), (xb - half + 1.0, ya)], 3.4, TIMBER)
    # The three floors, and a tie beam over the top floor.
    for y in floors:
        _floor(f, y, xs[0] - 22.0, xs[-1] + 22.0, TIMBER, TIMBER_LIGHT, TIMBER_SHADE, True)
    _floor(f, top + 18.0, xs[0] - 18.0, xs[-1] + 18.0, TIMBER, TIMBER_LIGHT, TIMBER_SHADE, False)
    # Ropes of bark fibre lash each beam to each post.
    for y in floors + (top + 18.0,):
        for x in xs:
            for d in (-4.0, 4.0):
                f.ink([(x + d - 2.0, y - 1.0), (x + d + 2.0, y + 10.0)], 1.4, LASHING)
    return A.finish(f, width=1.4)


# ---------------------------------------------------------------------------
# The jade workshop.
# ---------------------------------------------------------------------------


def _loop(f: K.Frame, cx: float, cy: float, r: float, width: float, colour: RGBA, light: RGBA, shade: RGBA, gap: float = 0.0, squash: float = 1.0) -> None:
    """A ring of polished jade: a thick round coil with an open middle.
    With `gap` (degrees), the ring has a slit at its bottom, as an ear
    ornament does."""
    a0, a1 = 90.0 + gap / 2.0, 450.0 - gap / 2.0
    pts = _ring(cx, cy, r, r * squash, a0, a1, 36)
    f.limb(pts, width, colour)
    f.ink(_ring(cx, cy, r, r * squash, 190.0, 290.0, 10), width * 0.3, light)
    f.ink(_ring(cx, cy, r + width * 0.25, (r + width * 0.25) * squash, 10.0, 80.0, 8), width * 0.25, shade)


def _draw_jade_workshop(anim: str, i: int, n: int):
    w, h = JADE_WORKSHOP_FRAME
    f = K.Frame(JADE_WORKSHOP_FRAME)
    rng = random.Random("history_jade_workshop")
    ground = h - 6.0
    bx0, bx1 = 30.0, 154.0
    top = 44.0
    # The bench: a thick plank on four short legs. The back legs are in
    # shade.
    for x in (bx0 + 10.0, bx1 - 8.0):
        f.limb([(x + 3.0, top + 6.0), (x + 3.0, ground - 6.0)], 5.0, BENCH_SHADE)
    f.poly([(bx0 + 3.0, top - 5.0), (bx1, top - 5.0), (bx1 - 3.0, top), (bx0, top)], BENCH_LIGHT)
    f.poly([(bx0, top), (bx1 - 3.0, top), (bx1 - 3.0, top + 7.0), (bx0, top + 7.0)], BENCH)
    f.poly([(bx0, top + 5.0), (bx1 - 3.0, top + 5.0), (bx1 - 3.0, top + 7.0), (bx0, top + 7.0)], BENCH_SHADE, body=False)
    f.poly([(bx1 - 3.0, top), (bx1, top - 5.0), (bx1, top + 2.0), (bx1 - 3.0, top + 7.0)], BENCH_SHADE)
    for x in (bx0 + 6.0, bx1 - 12.0):
        f.limb([(x, top + 6.0), (x, ground - 2.0)], 5.4, BENCH)
        f.ink([(x - 1.2, top + 8.0), (x - 1.2, ground - 1.0)], 0.8, BENCH_LIGHT)
    f.ink([(bx0 + 4.0, top - 3.0), (bx1 - 4.0, top - 3.0)], 0.6, BENCH)
    # A block of raw nephrite with a groove sawn half way down it. The
    # worker draws a cord to and fro in the groove, with wet sand: the hard
    # sand grains cut the stone.
    jcx, jy, jr = 52.0, 22.0, 13.0
    block = [(jcx - jr, top - 1.0), (jcx - jr - 1.0, jy + 12.0), (jcx - jr + 1.0, jy + 5.0), (jcx - 6.0, jy + 1.0), (jcx + 2.0, jy),
             (jcx + 9.0, jy + 2.0), (jcx + jr, jy + 8.0), (jcx + jr + 1.0, top - 1.0)]
    f.poly(block, JADE_RAW)
    f.poly([(jcx + 4.0, jy + 0.6), (jcx + 9.0, jy + 2.0), (jcx + jr, jy + 8.0), (jcx + jr + 1.0, top - 1.0), (jcx + 6.0, top - 1.0)], JADE_RAW_SHADE, body=False)
    f.ink([(jcx - jr, jy + 12.0), (jcx - jr + 2.0, jy + 5.6), (jcx - 6.0, jy + 2.2)], 0.9, JADE_LIGHT)
    for _ in range(10):
        f.dot(jcx + rng.uniform(-10.0, 10.0), rng.uniform(jy + 4.0, top - 3.0), 0.5, JADE_RAW_SHADE)
    # The groove: a dark slot from the top half way down. The cut face on
    # its left shows the true green of the stone.
    gx = jcx + 1.0
    f.poly([(gx - 5.0, jy + 0.6), (gx - 1.0, jy + 0.2), (gx - 1.0, jy + 11.0), (gx - 5.0, jy + 11.6)], JADE, body=False)
    f.ink([(gx - 4.6, jy + 1.4), (gx - 4.6, jy + 10.6)], 0.7, JADE_LIGHT)
    f.poly([(gx - 1.0, jy + 0.2), (gx + 1.4, jy + 0.2), (gx + 1.4, jy + 11.0), (gx - 1.0, jy + 11.0)], JADE_DARK, body=False)
    # The cord saw: a cord of plant fibre with a wooden grip at each end.
    # It comes up out of the groove and its grips lie on the bench.
    for cord in ([(gx, jy + 10.0), (gx + 0.2, jy - 1.0), (jcx - 8.0, jy + 1.0), (jcx - jr - 3.0, top - 6.0), (jcx - jr - 5.0, top - 2.4)],
                 [(gx, jy + 10.0), (gx + 0.6, jy - 1.0), (jcx + 9.0, jy + 1.4), (jcx + jr + 3.0, top - 6.0), (jcx + jr + 6.0, top - 2.4)]):
        f.limb(cord, 1.0, CORD)
        ex, ey = cord[-1]
        f.limb([(ex - 2.6, ey), (ex + 2.6, ey)], 2.6, POLE_DARK)
        f.ink([(ex - 2.0, ey - 0.6), (ex + 1.6, ey - 0.6)], 0.5, POLE)
    # A small heap of wet sand beside the block.
    hx = jcx + jr + 10.0
    f.poly([(hx, top - 1.0), (hx + 3.0, top - 4.0), (hx + 6.0, top - 5.0), (hx + 9.0, top - 3.0), (hx + 11.0, top - 1.0)], WET_SAND)
    for _ in range(6):
        f.dot(hx + rng.uniform(2.0, 9.0), top - rng.uniform(1.4, 3.6), 0.5, SANDSTONE_SHADE)
    # A flat slab with a groove along its top: the first cut of a long
    # adze.
    sx0, sx1 = 90.0, 105.0
    f.poly([(sx0, top - 1.0), (sx0 + 2.0, top - 6.0), (sx1 + 2.0, top - 6.0), (sx1, top - 1.0)], JADE)
    f.poly([(sx0 + 2.0, top - 6.0), (sx1 + 2.0, top - 6.0), (sx1 + 1.0, top - 5.0), (sx0 + 1.6, top - 5.0)], JADE_LIGHT, body=False)
    f.ink([(sx0 + 3.0, top - 5.4), (sx1, top - 5.4)], 0.9, JADE_DARK)
    f.poly([(sx0 + 10.0, top - 1.0), (sx1 + 2.0, top - 6.0), (sx1, top - 1.0)], JADE_SHADE, body=False)
    # Three finished adzes: long, with a sharp bevel at one end, and
    # polished till they shine. They lie in a fan.
    for ax, ay, ang, col, sh in ((110.0, top - 2.0, -6.0, JADE, JADE_SHADE), (113.0, top - 6.0, 10.0, JADE_SHADE, JADE_DARK),
                                 (108.0, top - 9.0, -18.0, JADE_LIGHT, JADE)):
        L, Wd = 15.0, 4.0
        pts = [(ax, ay - Wd * 0.4), (ax + L, ay - Wd * 0.55), (ax + L + 1.0, ay), (ax + L, ay + Wd * 0.45), (ax, ay + Wd * 0.4)]
        f.poly(K.turn(pts, ax, ay, ang), col)
        f.poly(K.turn([(ax + L - 3.0, ay - Wd * 0.52), (ax + L, ay - Wd * 0.55), (ax + L + 1.0, ay), (ax + L, ay + Wd * 0.45), (ax + L - 3.0, ay + Wd * 0.43)], ax, ay, ang), sh, body=False)
        f.ink(K.turn([(ax + 2.0, ay - 0.8), (ax + L - 5.0, ay - 1.0)], ax, ay, ang), 0.7, GLINT)
    # The ornaments: a slit ring for the ear, a flat ring that lies on the
    # bench, and a lingling-o, a slit ring with three knobs.
    _loop(f, 131.0, top - 10.0, 5.6, 2.6, JADE, JADE_LIGHT, JADE_DARK, gap=84.0)
    f.dot(129.0, top - 14.8, 0.7, GLINT)
    _loop(f, 140.0, top - 2.6, 5.0, 2.2, JADE_LIGHT, GLINT, JADE_SHADE, squash=0.34)
    lx, ly, lr = 146.0, top - 13.0, 4.8
    for a in (150.0, 30.0, 270.0):
        r = math.radians(a)
        f.limb([(lx + math.cos(r) * lr, ly + math.sin(r) * lr), (lx + math.cos(r) * (lr + 2.6), ly + math.sin(r) * (lr + 2.6))], 2.4, JADE_SHADE)
    _loop(f, lx, ly, lr, 2.4, JADE_SHADE, JADE, JADE_DARK, gap=70.0)
    f.dot(lx - 2.2, ly - 4.0, 0.7, GLINT)
    # The grinder on the ground: a slab of sandstone, its top worn into a
    # long hollow by the grinding, and a wet adze blank in the hollow.
    gx0, gx1 = 6.0, 36.0
    f.poly([(gx0, ground), (gx0 + 2.0, ground - 10.0), (gx1 - 2.0, ground - 11.0), (gx1, ground)], SANDSTONE)
    f.poly([(gx0 + 4.0, ground - 10.0), (gx0 + 10.0, ground - 7.0), (gx1 - 10.0, ground - 7.0), (gx1 - 4.0, ground - 11.0)], SANDSTONE_SHADE, body=False)
    f.ink([(gx0 + 2.0, ground - 9.6), (gx0 + 6.0, ground - 9.6)], 0.8, SANDSTONE_LIGHT)
    f.poly([(gx1 - 9.0, ground), (gx1 - 2.0, ground - 11.0), (gx1, ground)], SANDSTONE_SHADE, body=False)
    for _ in range(14):
        f.dot(rng.uniform(gx0 + 3.0, gx1 - 3.0), rng.uniform(ground - 6.0, ground - 1.0), 0.45, SANDSTONE_SHADE)
    f.poly([(gx0 + 12.0, ground - 8.0), (gx0 + 22.0, ground - 9.0), (gx0 + 23.0, ground - 7.0), (gx0 + 12.0, ground - 6.6)], JADE_RAW)
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# Cheomseongdae.
# ---------------------------------------------------------------------------

CHEOM_COURSES = 27
CHEOM_FOOT = 416.0
CHEOM_TOP = 35.0
CHEOM_BOTTOM_R = 80.0
CHEOM_NECK_R = 47.0


def _hermite(t: float, p0: float, m0: float, p1: float, m1: float) -> float:
    """A cubic from p0 (slope m0) at t = 0 to p1 (slope m1) at t = 1."""
    t2, t3 = t * t, t * t * t
    return (2 * t3 - 3 * t2 + 1) * p0 + (t3 - 2 * t2 + t) * m0 + (-2 * t3 + 3 * t2) * p1 + (t3 - t2) * m1


def _cheom_radius(y: float) -> float:
    """The half width of the tower at the height `y`. The tower is shaped
    like a bottle. The lower third is round and full: its wall curves in
    a little, faster as it goes up. The middle third narrows in an S-curve
    that ends in a concave sweep. The upper third is an almost straight
    neck. The real tower is about 4.9 m across at its foot and 2.9 m at
    its top; the frame is narrow, so the height is stretched a little."""
    t = (CHEOM_FOOT - y) / (CHEOM_FOOT - CHEOM_TOP)
    r0, r1 = CHEOM_BOTTOM_R, CHEOM_NECK_R
    lower, upper = 0.30, 0.74
    drop = 8.0
    if t <= lower:
        return r0 - drop * (t / lower) ** 2
    if t <= upper:
        u = (t - lower) / (upper - lower)
        # The slope at the start matches the lower third, so the curve
        # does not break; at the end the wall is upright.
        return _hermite(u, r0 - drop, -2.0 * drop * (upper - lower) / lower, r1, 0.0)
    return r1 - 1.6 * (t - upper) / (1.0 - upper)


def _draw_cheomseongdae(anim: str, i: int, n: int):
    w, h = CHEOMSEONGDAE_FRAME
    f = K.Frame(CHEOMSEONGDAE_FRAME)
    rng = random.Random("history_cheomseongdae")
    cx = w / 2.0
    ground = h - 6.0
    # The square base: two steps of long dressed blocks.
    for (y0, y1, hw) in ((ground - 13.0, ground, 89.0), (ground - 26.0, ground - 13.0, 84.0)):
        f.poly([(cx - hw, y0), (cx + hw, y0), (cx + hw, y1), (cx - hw, y1)], GRANITE)
        f.poly([(cx + hw - 16.0, y0), (cx + hw, y0), (cx + hw, y1), (cx + hw - 16.0, y1)], GRANITE_SHADE, body=False)
        f.ink([(cx - hw + 1.0, y0 + 1.2), (cx + hw - 1.0, y0 + 1.2)], 1.0, GRANITE_LIGHT)
        for k in range(1, 5):
            x = cx - hw + k * 2.0 * hw / 5.0 + (6.0 if y0 < ground - 20.0 else 0.0)
            f.ink([(x, y0 + 2.0), (x, y1 - 1.0)], 0.9, GRANITE_DARK)
    # The body of the tower.
    ch = (CHEOM_FOOT - CHEOM_TOP) / CHEOM_COURSES
    ys = [CHEOM_FOOT - k * (CHEOM_FOOT - CHEOM_TOP) / 90.0 for k in range(91)]
    left = [(cx - _cheom_radius(y), y) for y in ys]
    right = [(cx + _cheom_radius(y), y) for y in ys]
    f.poly(left + right[::-1], GRANITE)
    # Light on the left, shade on the right: the wall is round.
    f.poly([(cx + _cheom_radius(y) * 0.45, y) for y in ys] + [(cx + _cheom_radius(y), y) for y in ys[::-1]], GRANITE_SHADE, body=False)
    f.poly([(cx - _cheom_radius(y) * 0.86, y) for y in ys] + [(cx - _cheom_radius(y) * 0.62, y) for y in ys[::-1]], GRANITE_LIGHT, body=False)
    # The courses: each joint is a ring round the tower, seen a little
    # from below, so it bows up in the middle. The blocks of each course
    # sit over the joints of the course below, and they look narrower
    # toward the sides of the round wall.
    for c in range(CHEOM_COURSES + 1):
        y = CHEOM_FOOT - c * ch
        r = _cheom_radius(y)
        bow = 1.6 * r / CHEOM_BOTTOM_R
        joint = [(cx + r * math.sin(a), y - bow * math.cos(a)) for a in [math.radians(-88.0 + 176.0 * k / 20.0) for k in range(21)]]
        if 0 < c < CHEOM_COURSES:
            f.ink(joint, 0.9, GRANITE_DARK)
        if c < CHEOM_COURSES:
            off = 0.5 if c % 2 else 0.0
            for j in range(-6, 7):
                phi = (j + off) * math.radians(25.0) + rng.uniform(-0.04, 0.04)
                if abs(phi) > math.radians(80.0):
                    continue
                x = cx + r * math.sin(phi)
                f.ink([(x, y - bow * math.cos(phi) - 0.5), (x, y - ch - bow * math.cos(phi) + 0.5)], 0.7, GRANITE_SHADE if phi < 0.5 else GRANITE_DARK)
    # The window: a square opening on the south face, from the 13th to
    # the 15th course. A ladder reached it from outside; the tower is
    # filled with earth up to its sill.
    wy1 = CHEOM_FOOT - 12.0 * ch
    wy0 = CHEOM_FOOT - 15.0 * ch
    ww = 19.0
    f.poly([(cx - ww - 3.0, wy1), (cx + ww + 3.0, wy1), (cx + ww + 3.0, wy1 + 3.0), (cx - ww - 3.0, wy1 + 3.0)], GRANITE_LIGHT, body=False)
    f.poly([(cx - ww, wy0), (cx + ww, wy0), (cx + ww, wy1), (cx - ww, wy1)], WINDOW, body=False)
    f.poly([(cx - ww, wy0), (cx + ww, wy0), (cx + ww, wy0 + 4.0), (cx - ww + 4.0, wy0 + 4.0), (cx - ww + 4.0, wy1), (cx - ww, wy1)], K.shade(WINDOW, 0.6), body=False)
    f.ink([(cx - ww, wy0), (cx + ww, wy0), (cx + ww, wy1)], 1.0, GRANITE_DARK)
    f.ink([(cx - ww - 3.0, wy1 + 0.6), (cx + ww + 3.0, wy1 + 0.6)], 1.0, GRANITE_DARK)
    # The top: a frame of long granite beams in two tiers, in the shape
    # of the character 井. In each tier a beam goes across in front and
    # one behind, and two beams go from front to back over the wall. The
    # beams cross near their ends, so each end sticks out past the corner
    # of the frame: the cross beam goes on past the front-to-back beams,
    # and their square ends stand out in front of it.
    for y0 in (CHEOM_TOP - 13.0, CHEOM_TOP - 26.0):
        y1 = y0 + 13.0
        hw = 62.0
        f.poly([(cx - hw, y0), (cx + hw, y0), (cx + hw, y1), (cx - hw, y1)], GRANITE)
        f.poly([(cx - hw, y1 - 4.0), (cx + hw, y1 - 4.0), (cx + hw, y1), (cx - hw, y1)], GRANITE_SHADE, body=False)
        f.poly([(cx + hw - 9.0, y0), (cx + hw, y0), (cx + hw, y1), (cx + hw - 9.0, y1)], GRANITE_SHADE, body=False)
        f.ink([(cx - hw + 1.0, y0 + 1.2), (cx + hw - 1.0, y0 + 1.2)], 1.0, GRANITE_LIGHT)
        for s in (-1.0, 1.0):
            ex = cx + s * 43.0
            face = GRANITE_LIGHT if s < 0 else GRANITE
            f.poly([(ex - 7.0, y0 - 0.6), (ex + 7.0, y0 - 0.6), (ex + 7.0, y1 + 0.6), (ex - 7.0, y1 + 0.6)], face)
            f.poly([(ex + 3.0, y0 - 0.6), (ex + 7.0, y0 - 0.6), (ex + 7.0, y1 + 0.6), (ex + 3.0, y1 + 0.6)], GRANITE_SHADE, body=False)
            f.ink([(ex - 7.0, y0 - 0.6), (ex - 7.0, y1 + 0.6)], 1.0, GRANITE_DARK)
            f.ink([(ex + 7.0, y0 - 0.6), (ex + 7.0, y1 + 0.6)], 1.0, GRANITE_DARK)
        f.ink([(cx - hw, y1), (cx + hw, y1)], 1.0, GRANITE_DARK)
    # Lichen and weather marks on the old stone.
    for _ in range(46):
        y = rng.uniform(CHEOM_TOP + 6.0, CHEOM_FOOT - 4.0)
        r = _cheom_radius(y)
        x = cx + rng.uniform(-0.85, 0.85) * r
        if abs(x - cx) < ww + 4.0 and wy0 - 4.0 < y < wy1 + 6.0:
            continue
        f.ellipse(x, y, rng.uniform(1.0, 2.4), rng.uniform(0.6, 1.2), K.alpha(GRANITE_DARK, 0.35), body=False)
    return A.finish(f, width=1.4)


# ---------------------------------------------------------------------------
# The royal tumulus.
# ---------------------------------------------------------------------------


def _draw_royal_tumulus(anim: str, i: int, n: int):
    w, h = TUMULUS_FRAME
    f = K.Frame(TUMULUS_FRAME)
    rng = random.Random("history_royal_tumulus")
    cx = w / 2.0
    ground = h - 6.0
    R = 178.0
    foot = ground - 12.0
    top = 26.0

    def dome_y(x: float, mid: float = cx, half: float = R, peak: float = top) -> float:
        u = min(1.0, abs(x - mid) / half)
        return foot - (foot - peak) * (1.0 - u * u) ** 0.62

    def base_y(x: float) -> float:
        return foot + 5.0 * (1.0 - ((x - cx) / R) ** 2)

    def cap(mid: float, half: float, peak: float, lift: float) -> List[Point]:
        """A dome inside the hill: lit parts are smaller domes moved to the
        left, so the shade is a soft crescent on the right."""
        xs = [mid - half + 2.0 * half * k / 60.0 for k in range(61)]
        return [(x, dome_y(x, mid, half, peak) - lift * 0.0) for x in xs] + [(x, base_y(x) - lift) for x in xs[::-1]]

    xs = [cx - R + 2.0 * R * k / 80.0 for k in range(81)]
    dome = [(x, dome_y(x)) for x in xs]
    base = [(x, base_y(x)) for x in xs]
    # The hill in shade, then the lit hill, then a broad light on its upper
    # left: three domes, each one smaller and further to the left.
    f.poly(dome + base[::-1], GRASS_SHADE)
    f.poly(cap(cx - R * 0.10, R * 0.86, top + 3.0, 6.0), GRASS, body=False)
    light = [(x, dome_y(x, cx - R * 0.30, R * 0.52, top + 7.0)) for x in [cx - R * 0.82 + R * 1.04 * k / 40.0 for k in range(41)]]
    f.poly(light, K.alpha(GRASS_LIGHT, 0.8), body=False)
    # The lower slope is a little darker, where it meets the ground.
    f.poly([(x, base_y(x) - 10.0) for x in xs[3:-3]] + [(x, base_y(x)) for x in xs[-4:2:-1]], K.alpha(GRASS_SHADE, 0.5), body=False)
    # Short strokes of grass over the hill.
    for _ in range(140):
        x = rng.uniform(cx - R * 0.94, cx + R * 0.94)
        y = rng.uniform(dome_y(x) + 6.0, foot - 2.0)
        colour = GRASS_DARK if x > cx + 40.0 else GRASS_SHADE
        f.ink([(x, y), (x + rng.uniform(-0.8, 0.8), y - rng.uniform(1.6, 3.0))], 0.7, K.alpha(colour, 0.7))
    # The kerb: one course of rough stones round the foot of the mound. It
    # keeps the earth of the mound in its place.
    stones = 30
    for k in range(stones):
        x0 = cx - R + 2.0 * R * k / stones
        x1 = cx - R + 2.0 * R * (k + 1) / stones
        y0 = foot + 5.0 * (1.0 - ((x0 - cx) / R) ** 2)
        y1 = foot + 5.0 * (1.0 - ((x1 - cx) / R) ** 2)
        hh = 9.0 + rng.uniform(-1.0, 1.0)
        stone = [(x0 + 0.6, y0 - hh + 4.0), (x1 - 0.6, y1 - hh + 4.0), (x1 - 0.4, y1 + 4.0), (x0 + 0.4, y0 + 4.0)]
        mid = (x0 + x1) / 2.0
        f.poly(stone, KERB_SHADE if mid > cx + R * 0.45 else KERB)
        f.ink([(x0 + 1.6, y0 - hh + 5.4), (x1 - 1.6, y1 - hh + 5.4)], 0.9, KERB_LIGHT)
        f.ink([(x0 + 1.0, y0 + 3.4), (x1 - 1.0, y1 + 3.4)], 0.8, KERB_SHADE)
        f.ink([(x1, y1 - hh + 4.0), (x1, y1 + 4.0)], 0.8, GRANITE_DARK)
    # A band of grass on the ground in front of the kerb.
    gl = [(x, foot + 5.0 * (1.0 - ((x - cx) / R) ** 2) + 4.0) for x in xs]
    f.poly(gl + [(cx + R + 4.0, ground), (cx - R - 4.0, ground)], GRASS)
    f.poly([p for p in gl if p[0] > cx + 40.0] + [(cx + R + 4.0, ground), (cx + 40.0, ground)], GRASS_SHADE, body=False)
    return A.finish(f, width=1.4)


# ---------------------------------------------------------------------------
# The gold crown.
# ---------------------------------------------------------------------------


def _spangle(f: K.Frame, x: float, y: float, r: float = 1.7) -> None:
    """A gold spangle: a thin round disc that hangs on a twist of gold
    wire, so that it shakes and flashes when the wearer moves."""
    f.ink([(x, y - r - 1.2), (x, y - r + 0.2)], 0.5, GOLD_DARK)
    f.ellipse(x, y, r, r, GOLD)
    f.ellipse(x - r * 0.3, y - r * 0.3, r * 0.45, r * 0.45, GOLD_LIGHT, body=False)


def _gogok(f: K.Frame, x: float, y: float, s: float, mirror: float = 1.0) -> None:
    """A curved jade (gogok): a round head with a hole for the cord, and a
    tail that curls round under it like a comma."""
    tail = [(x, y), (x + mirror * 1.6 * s, y + 2.0 * s), (x + mirror * 1.2 * s, y + 4.4 * s), (x - mirror * 0.6 * s, y + 5.8 * s)]
    f.ink([(x, y - 2.6 * s), (x, y - 1.4 * s)], 0.5, GOLD_DARK)
    f.limb(tail, 1.8 * s, GOGOK)
    f.ellipse(x, y, 1.7 * s, 1.7 * s, GOGOK)
    f.dot(x - 0.5 * s, y - 0.5 * s, 0.6 * s, GOGOK_LIGHT)
    f.ink(tail[1:], 0.5 * s, GOGOK_SHADE)


def _tree_upright(f: K.Frame, x: float, foot: float, top: float, reach: float, colour: RGBA, light: RGBA) -> List[Point]:
    """An upright shaped like a tree, or the character 出: a stem, three
    pairs of short branches that go out at a slant and then straight up,
    and a bud on the end of each, and on the top of the stem. `reach` is
    how far the branches go out (smaller when the upright is seen from its
    edge). It gives the points where spangles hang."""
    hangs: List[Point] = []
    f.limb([(x, foot), (x, top + 3.0)], 2.8, colour)
    f.ellipse(x, top + 1.6, 2.4, 3.0, colour)
    f.dot(x - 0.7, top + 0.8, 0.8, light)
    span = foot - top
    for yy in (foot - span * 0.28, foot - span * 0.52, foot - span * 0.76):
        for s in (-1.0, 1.0):
            ex = x + s * reach
            f.limb([(x, yy), (ex, yy - reach * 0.7), (ex, yy - reach * 0.7 - 4.0)], 2.0, colour)
            f.ellipse(ex, yy - reach * 0.7 - 5.0, 1.7, 2.1, colour)
            f.dot(ex - 0.5, yy - reach * 0.7 - 5.6, 0.6, light)
            hangs.append((ex + s * 1.8, yy - reach * 0.2))
    f.ink([(x - 0.7, foot - 1.0), (x - 0.7, top + 4.0)], 0.6, light)
    return hangs


def _antler(f: K.Frame, x: float, foot: float, s: float, colour: RGBA) -> List[Point]:
    """An upright shaped like the antlers of a deer: a beam that rises and
    leans out a little, with three tines that turn up from it."""
    beam = [(x, foot), (x + s * 1.0, foot - 12.0), (x + s * 3.6, foot - 22.0), (x + s * 7.0, foot - 30.0)]
    f.limb(beam, 2.4, colour)
    tines = [((x + s * 0.8, foot - 10.0), (x - s * 2.4, foot - 17.0)), ((x + s * 2.6, foot - 19.0), (x + s * 0.4, foot - 27.0)),
             ((x + s * 5.4, foot - 27.0), (x + s * 4.4, foot - 35.0))]
    for a, b in tines:
        f.limb([a, b], 1.9, colour)
    return [beam[-1], tines[2][1]]


def _draw_gold_crown(anim: str, i: int, n: int):
    w, h = GOLD_CROWN_FRAME
    f = K.Frame(GOLD_CROWN_FRAME)
    cx = w / 2.0
    ground = h - 5.0
    # The stand: a low block of dark wood and a short post that holds the
    # crown at the height of a head.
    f.poly([(cx - 26.0, ground), (cx - 24.0, ground - 9.0), (cx + 24.0, ground - 9.0), (cx + 26.0, ground)], STAND)
    f.poly([(cx + 10.0, ground - 9.0), (cx + 24.0, ground - 9.0), (cx + 26.0, ground), (cx + 12.0, ground)], STAND_SHADE, body=False)
    f.ink([(cx - 23.0, ground - 7.6), (cx + 8.0, ground - 7.6)], 0.9, STAND_LIGHT)
    f.poly([(cx - 7.0, ground - 9.0), (cx - 5.0, 78.0), (cx + 5.0, 78.0), (cx + 7.0, ground - 9.0)], STAND)
    f.poly([(cx + 1.0, ground - 9.0), (cx + 2.0, 78.0), (cx + 5.0, 78.0), (cx + 7.0, ground - 9.0)], STAND_SHADE, body=False)
    band_y, rx, ry, bh = 66.0, 26.0, 5.0, 10.0
    # The back of the band, seen over the front: its inside is in shade.
    f.ellipse(cx, band_y, rx, ry, GOLD_SHADE)
    f.ellipse(cx, band_y + 1.0, rx - 2.0, ry - 1.4, STAND_SHADE, body=False)
    # The two antlers stand at the back, between the trees.
    hangs: List[Point] = []
    hangs += _antler(f, cx - 13.0, band_y - 3.0, -1.0, GOLD_SHADE)
    hangs += _antler(f, cx + 13.0, band_y - 3.0, 1.0, GOLD_SHADE)
    # The three trees: one in the front and one at each side. The trees at
    # the sides are seen from their edge, so their branches look short.
    hangs += _tree_upright(f, cx - 23.0, band_y + 2.0, 20.0, 3.4, GOLD_SHADE, GOLD)
    hangs += _tree_upright(f, cx + 23.0, band_y + 2.0, 20.0, 3.4, GOLD_SHADE, GOLD)
    hangs += _tree_upright(f, cx, band_y + 5.0, 12.0, 6.0, GOLD, GOLD_LIGHT)
    # The front of the band.
    front = _ring(cx, band_y, rx, ry, 0.0, 180.0, 24)
    f.poly([(x, y - bh * 0.5) for x, y in front] + [(x, y + bh * 0.5) for x, y in front[::-1]], GOLD)
    f.poly([(x, y + bh * 0.1) for x, y in front if x > cx + 6.0] + [(x, y + bh * 0.5) for x, y in front[::-1] if x > cx + 6.0], GOLD_SHADE, body=False)
    f.ink([(x, y - bh * 0.5 + 1.0) for x, y in front[3:-3]], 0.8, GOLD_LIGHT)
    # Rows of small dots punched from behind along both edges of the band.
    for k in range(2, 23, 2):
        a = math.radians(180.0 * k / 24.0)
        x, y = cx + math.cos(a) * rx, band_y + math.sin(a) * ry
        for dy in (-bh * 0.32, bh * 0.32):
            f.dot(x, y + dy, 0.5, GOLD_DARK)
    # Spangles hang all over the uprights and along the band.
    for x, y in hangs:
        _spangle(f, x, y + 2.6, 1.5)
    for k in (3, 8, 16, 21):
        a = math.radians(180.0 * k / 24.0)
        _spangle(f, cx + math.cos(a) * rx * 0.98, band_y + math.sin(a) * ry + 1.4, 1.6)
    # Curved jades hang from the trees and from the band.
    for x, y, m in ((cx - 8.0, 58.0, 1.0), (cx + 8.0, 58.0, -1.0), (cx - 8.0, 44.0, 1.0), (cx + 8.0, 44.0, -1.0), (cx - 27.0, 50.0, 1.0), (cx + 27.0, 50.0, -1.0)):
        _gogok(f, x, y, 0.9, m)
    for k in (5, 10, 14, 19):
        a = math.radians(180.0 * k / 24.0)
        _gogok(f, cx + math.cos(a) * rx * 0.98, band_y + math.sin(a) * ry + 6.0, 0.9, 1.0 if k < 12 else -1.0)
    # The two long pendants: chains of gold links with spangles, that end
    # in a leaf of gold.
    for s in (-1.0, 1.0):
        x0 = cx + s * 20.0
        y0 = band_y + 7.0
        links = [(x0 + s * 0.6 * math.sin(k * 0.9), y0 + k * 3.4) for k in range(8)]
        f.limb(links, 1.2, GOLD_SHADE)
        for k, (x, y) in enumerate(links[1::2]):
            f.ellipse(x, y, 1.2, 1.6, GOLD)
        ex, ey = links[-1]
        f.poly([(ex, ey), (ex - 2.6, ey + 4.0), (ex, ey + 8.0), (ex + 2.6, ey + 4.0)], GOLD)
        f.ink([(ex - 0.6, ey + 2.0), (ex - 0.6, ey + 6.0)], 0.6, GOLD_LIGHT)
    # The shine: small points of light on the gold.
    for x, y, r in ((cx - 0.8, 16.0, 3.0), (cx - 15.0, band_y - 1.0, 3.2), (cx + 18.0, 30.0, 2.4), (cx - 24.0, 26.0, 2.2)):
        f.glow(x, y, r, K.alpha(GOLD_LIGHT, 0.5))
        f.glow_line([(x - r * 1.4, y), (x + r * 1.4, y)], 0.6, K.alpha((255, 250, 220, 255), 0.9))
        f.glow_line([(x, y - r * 1.4), (x, y + r * 1.4)], 0.6, K.alpha((255, 250, 220, 255), 0.9))
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# Publication.
# ---------------------------------------------------------------------------

FRAMES: Dict[str, Tuple[int, int]] = {
    "history_pit_dwelling": PIT_DWELLING_FRAME,
    "history_flame_pot": FLAME_POT_FRAME,
    "history_six_pillars": SIX_PILLARS_FRAME,
    "history_jade_workshop": JADE_WORKSHOP_FRAME,
    "history_cheomseongdae": CHEOMSEONGDAE_FRAME,
    "history_royal_tumulus": TUMULUS_FRAME,
    "history_gold_crown": GOLD_CROWN_FRAME,
}
DRAW: Dict[str, Callable] = {
    "history_pit_dwelling": _draw_pit_dwelling,
    "history_flame_pot": _draw_flame_pot,
    "history_six_pillars": _draw_six_pillars,
    "history_jade_workshop": _draw_jade_workshop,
    "history_cheomseongdae": _draw_cheomseongdae,
    "history_royal_tumulus": _draw_royal_tumulus,
    "history_gold_crown": _draw_gold_crown,
}
DISPLAY = {
    "history_pit_dwelling": "Pit Dwelling",
    "history_flame_pot": "Flame Pot",
    "history_six_pillars": "Six Pillars",
    "history_jade_workshop": "Jade Workshop",
    "history_cheomseongdae": "Cheomseongdae",
    "history_royal_tumulus": "Royal Tumulus",
    "history_gold_crown": "Gold Crown",
}
#: The room of each prop: its last tag.
ROOMS = {
    "history_pit_dwelling": "jomon",
    "history_flame_pot": "jomon",
    "history_six_pillars": "jomon",
    "history_jade_workshop": "taiwan",
    "history_cheomseongdae": "silla",
    "history_royal_tumulus": "silla",
    "history_gold_crown": "silla",
}
ROWS: Dict[str, List[Tuple[str, int, int]]] = {}


def _foot(name: str) -> Dict[str, Tuple[float, float]]:
    w, h = FRAMES[name]
    return {"foot": (w / 2.0, float(h))}


#: The anchors of each prop: all are scenery, with a "foot".
ANCHORS: Dict[str, Dict[str, Tuple[float, float]]] = {name: _foot(name) for name in DISPLAY}
TAGS: Dict[str, List[str]] = {name: ["prop", "scenery", "history", ROOMS[name]] for name in DISPLAY}

TARGETS: Dict[str, dict] = {
    name: _publisher(name, DISPLAY[name], ROWS.get(name, STILL), FRAMES[name], DRAW[name], ANCHORS[name], "Scenery", TAGS[name]) for name in DISPLAY
}
