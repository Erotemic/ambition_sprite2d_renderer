"""The props of the East Asian coast (the History dimension): Jomon Japan,
ancient Taiwan and Silla; Song China, Heian Japan and Joseon Korea.

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

Hangzhou was the capital of the Southern Song (about 1200 CE), and by
some estimates the largest city in the world. Pleasure boats with small
cabins crossed West Lake. The Song state printed the first paper money
from plates of bronze, with printed borders and red seals. Song books
tell of the south-pointing fish: a thin leaf of magnetized iron, cut like a
fish, that floats in a bowl of water and turns to the south.

At Heian-kyo (about 1000 CE) the court lived in mansions of wood, with
folding screens (byobu) painted with hills, water and clouds. Nobles rode
in tall ox carriages (gissha): a cabin on two big wheels, with blinds of
bamboo at its front, drawn by one ox.

At Hanyang in the reign of King Sejong, his engineer Jang Yeong-sil made a
rain gauge of bronze (cheugugi, 1441) that stood on a stone stand, and a
water clock that struck the hours by itself (Jagyeongnu, 1434). Water ran
from great vessels on steps into tall vessels; a float rose in them and
set off wooden figures that struck a bell, a drum and a gong.

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
- ``history_lake_boat``: the look of a platform, a West Lake pleasure boat:
  a long, flat hull of wood with a red band, a cabin of wood with a curved
  roof of woven matting in its middle, a pole of bamboo at the stern and a
  red lantern at the bow. Its deck is the platform (`LAKE_BOAT_SPAN` =
  (24, 360), `LAKE_BOAT_TOP` = 104, in a 384 x 160 frame).
- ``history_money_press``: scenery, a printer's bench with a bronze plate
  inked black, an ink stone, brushes, a stack of new paper money and two
  sheets that hang to dry. The notes carry printed borders, blocks and
  strokes and red seals, but no real writing.
- ``history_compass_bowl``: scenery, the south-pointing fish: a shallow
  celadon bowl of water on a small stand, with a fish of iron leaf that
  floats on the water.
- ``history_byobu_screen``: scenery, a folding screen of six panels in a
  zigzag, painted with hills, pines, a pond and bands of gold cloud. There
  are no figures on it.
- ``history_ox_carriage``: scenery, a Heian ox carriage: a tall cabin of
  woven wood with a curved roof of palm leaf, a bamboo blind and a silk
  drape at its front, two big lacquered wheels, long shafts and one black
  ox.
- ``history_rain_gauge``: scenery, the rain gauge of 1441: a cylinder of
  bronze in sections, in the socket of a carved granite stand.
- ``history_water_clock``: scenery, the self-striking water clock as it is
  rebuilt today: bronze vessels on stone steps on the left, two tall
  receiving vessels, and a cabinet on the right with three wooden figures
  on its top, by a bell, a drum and a gong.

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
# Song, Heian and Joseon: the colours.
# ---------------------------------------------------------------------------

LAKE_BOAT_FRAME = (384, 160)
#: The deck of the lake boat is the platform: it is level from x0 to x1 at
#: the height `LAKE_BOAT_TOP` (frame pixels).
LAKE_BOAT_SPAN = (24.0, 360.0)
LAKE_BOAT_TOP = 104.0
MONEY_PRESS_FRAME = (160, 128)
COMPASS_BOWL_FRAME = (64, 48)
BYOBU_FRAME = (192, 128)
OX_CARRIAGE_FRAME = (224, 160)
RAIN_GAUGE_FRAME = (64, 112)
WATER_CLOCK_FRAME = (256, 256)

BOAT_WOOD = (156, 108, 64, 255)
BOAT_WOOD_LIGHT = (192, 146, 94, 255)
BOAT_WOOD_SHADE = (114, 76, 46, 255)
BOAT_WOOD_DARK = (80, 54, 34, 255)
VERMILION = (190, 62, 44, 255)
VERMILION_LIGHT = (226, 104, 72, 255)
VERMILION_SHADE = (136, 40, 32, 255)
MATTING = (204, 176, 118, 255)
MATTING_LIGHT = (232, 208, 154, 255)
MATTING_SHADE = (160, 130, 82, 255)
MATTING_DARK = (118, 92, 58, 255)
BAMBOO = (176, 166, 96, 255)
BAMBOO_LIGHT = (212, 202, 132, 255)
BAMBOO_SHADE = (128, 118, 64, 255)
PAPER = (236, 224, 194, 255)
PAPER_SHADE = (204, 188, 154, 255)
PAPER_DARK = (166, 150, 118, 255)
PRINT = (58, 48, 46, 255)
SEAL = (194, 44, 38, 255)
SEAL_LIGHT = (230, 98, 84, 255)
INTERIOR = (70, 50, 40, 255)

BRONZE = (160, 116, 64, 255)
BRONZE_LIGHT = (206, 164, 100, 255)
BRONZE_SHADE = (116, 80, 46, 255)
BRONZE_DARK = (80, 56, 34, 255)
VERDIGRIS = (104, 150, 126, 255)
PRINTER_INK = (38, 34, 36, 255)
INK_SHEEN = (98, 96, 104, 255)
INKSTONE = (74, 72, 78, 255)
INKSTONE_LIGHT = (120, 118, 126, 255)

CELADON = (150, 186, 162, 255)
CELADON_LIGHT = (198, 224, 204, 255)
CELADON_SHADE = (106, 142, 122, 255)
WATER = (116, 162, 192, 255)
WATER_LIGHT = (186, 216, 232, 255)
WATER_SHADE = (78, 120, 156, 255)
IRON = (92, 94, 104, 255)
IRON_LIGHT = (156, 158, 170, 255)
IRON_SHADE = (60, 62, 72, 255)

SILK = (230, 218, 182, 255)
SILK_SHADE = (196, 184, 148, 255)
LACQUER = (46, 36, 34, 255)
LACQUER_LIGHT = (96, 80, 72, 255)
BROCADE = (142, 64, 52, 255)
BROCADE_LIGHT = (184, 112, 80, 255)
HILL_FAR = (124, 154, 168, 255)
HILL = (106, 148, 104, 255)
HILL_SHADE = (76, 116, 82, 255)
PINE = (50, 92, 66, 255)
TRUNK = (98, 70, 50, 255)
POND = (104, 150, 180, 255)
POND_LIGHT = (176, 206, 222, 255)

PALM = (216, 208, 176, 255)
PALM_LIGHT = (240, 234, 210, 255)
PALM_SHADE = (172, 162, 130, 255)
PALM_DARK = (128, 118, 94, 255)
WICKER = (178, 140, 86, 255)
WICKER_SHADE = (132, 100, 60, 255)
BLIND = (196, 172, 100, 255)
BLIND_SHADE = (150, 126, 68, 255)
DRAPE = (150, 52, 70, 255)
DRAPE_LIGHT = (196, 96, 108, 255)
DRAPE_ALT = (214, 170, 76, 255)
OX = (54, 46, 46, 255)
OX_LIGHT = (100, 90, 88, 255)
OX_SHADE = (34, 28, 30, 255)
OX_HORN = (214, 200, 166, 255)
CORD_RED = (176, 48, 42, 255)

CABINET = (150, 98, 58, 255)
CABINET_LIGHT = (186, 132, 84, 255)
CABINET_SHADE = (108, 70, 42, 255)
DANCHEONG = (64, 138, 118, 255)
DANCHEONG_LIGHT = (116, 184, 160, 255)
DANCHEONG_SHADE = (40, 98, 84, 255)
ROOF_TILE = (82, 84, 92, 255)
ROOF_TILE_LIGHT = (128, 130, 140, 255)
ROOF_TILE_SHADE = (54, 56, 64, 255)
FACE_WOOD = (226, 184, 140, 255)
ROBE_RED = (180, 56, 46, 255)
ROBE_BLUE = (66, 96, 152, 255)
ROBE_GREEN = (70, 132, 96, 255)
HAT = (36, 30, 30, 255)
OUTLINE_SHADE = (40, 26, 30, 255)


def _lerp(a: float, b: float, u: float) -> float:
    return a + (b - a) * u


# ---------------------------------------------------------------------------
# The lake boat of West Lake (a platform).
# ---------------------------------------------------------------------------


def _lake_deck_y(x: float) -> float:
    """The top of the hull at `x`: level over the platform span, and swept
    up a little at the bow and the stern, outside the span."""
    x0, x1 = LAKE_BOAT_SPAN
    if x < x0:
        return LAKE_BOAT_TOP - (x0 - x) * 0.8
    if x > x1:
        return LAKE_BOAT_TOP - (x - x1) * 0.8
    return LAKE_BOAT_TOP


def _bamboo_pole(f: K.Frame, a: Point, b: Point, width: float) -> None:
    """A pole of bamboo from `a` to `b`, with a ring at each node."""
    f.limb([a, b], width, BAMBOO)
    f.ink([(a[0] - width * 0.25, a[1]), (b[0] - width * 0.25, b[1])], width * 0.3, BAMBOO_LIGHT)
    for k in range(1, 9):
        p = _mix(a, b, k / 9.0)
        f.ink([(p[0] - width * 0.6, p[1] + 0.4), (p[0] + width * 0.6, p[1] - 0.4)], 0.8, BAMBOO_SHADE)


def _lattice_window(f: K.Frame, x0: float, y0: float, x1: float, y1: float) -> None:
    """A window of paper behind a wooden lattice of squares."""
    f.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], PAPER)
    f.poly([(x0, y0), (x1, y0), (x1, y0 + 3.0), (x0, y0 + 3.0)], PAPER_SHADE, body=False)
    step = (x1 - x0) / 4.0
    for k in range(1, 4):
        f.ink([(x0 + k * step, y0), (x0 + k * step, y1)], 0.9, BOAT_WOOD_SHADE)
    y = y0 + step
    while y < y1 - 1.0:
        f.ink([(x0, y), (x1, y)], 0.9, BOAT_WOOD_SHADE)
        y += step
    f.ink([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], 1.2, BOAT_WOOD_DARK)


def _draw_lake_boat(anim: str, i: int, n: int):
    f = K.Frame(LAKE_BOAT_FRAME)
    x0, x1 = LAKE_BOAT_SPAN
    top = LAKE_BOAT_TOP
    keel = top + 30.0
    xs = [10.0 + (374.0 - 10.0) * k / 90.0 for k in range(91)]
    # The pole at the stern: the boatman pushes it on the bed of the lake.
    # It goes down past the hull, so its foot shows under the stern.
    _bamboo_pole(f, (82.0, 20.0), (40.0, 150.0), 3.6)
    # The cabin: a small house of wood on the deck, with a curved roof of
    # woven matting. Guests sat in it to look at the lake.
    cx0, cx1 = 138.0, 246.0
    wall_top = 68.0
    f.poly([(cx0, wall_top), (cx1, wall_top), (cx1, top), (cx0, top)], BOAT_WOOD)
    # The open bay in the middle shows the dark inside, a rolled blind of
    # bamboo over it, and a low table.
    mx0, mx1 = 168.0, 216.0
    f.poly([(mx0, wall_top + 2.0), (mx1, wall_top + 2.0), (mx1, top), (mx0, top)], INTERIOR, body=False)
    f.poly([(mx0, top - 9.0), (mx1, top - 9.0), (mx1, top), (mx0, top)], BOAT_WOOD_SHADE, body=False)
    f.poly([(mx0 + 14.0, top - 14.0), (mx1 - 14.0, top - 14.0), (mx1 - 14.0, top - 11.0), (mx0 + 14.0, top - 11.0)], VERMILION_SHADE, body=False)
    for x in (mx0 + 16.0, mx1 - 16.0):
        f.ink([(x, top - 11.0), (x, top - 5.0)], 1.4, VERMILION_SHADE)
    f.limb([(mx0 + 1.0, wall_top + 5.0), (mx1 - 1.0, wall_top + 5.0)], 4.6, BLIND)
    for k in range(1, 12):
        x = mx0 + 4.0 * k
        f.ink([(x, wall_top + 3.0), (x, wall_top + 7.0)], 0.6, BLIND_SHADE)
    for x in (mx0 + 8.0, mx1 - 8.0):
        f.ink([(x, wall_top + 2.0), (x, wall_top + 9.0)], 0.9, VERMILION)
    # The two bays at the sides: a window of paper over a low wall of
    # boards.
    for wx0, wx1 in ((cx0 + 4.0, mx0 - 4.0), (mx1 + 4.0, cx1 - 4.0)):
        _lattice_window(f, wx0, wall_top + 4.0, wx1, top - 14.0)
        for k in range(1, 3):
            f.ink([(wx0, top - 14.0 + 4.6 * k), (wx1, top - 14.0 + 4.6 * k)], 0.7, BOAT_WOOD_SHADE)
    # The posts are lacquered red.
    for x in (cx0 + 1.5, mx0 - 1.5, mx1 + 1.5, cx1 - 1.5):
        f.limb([(x, wall_top), (x, top)], 3.6, VERMILION)
        f.ink([(x - 0.8, wall_top + 1.0), (x - 0.8, top - 1.0)], 0.8, VERMILION_LIGHT)
    # The roof: an arch of woven matting on bent ribs, with ends that turn
    # up a little, over a fascia board.
    rx0, rx1 = cx0 - 14.0, cx1 + 14.0

    def roof_y(u: float) -> float:
        return wall_top - 4.0 - 24.0 * math.sin(math.pi * u) ** 0.6 + 4.0 * (abs(u - 0.5) * 2.0) ** 6

    us = [k / 40.0 for k in range(41)]
    arch = [(_lerp(rx0, rx1, u), roof_y(u)) for u in us]
    f.poly(arch + [(rx1 - 3.0, wall_top + 1.0), (rx0 + 3.0, wall_top + 1.0)], MATTING)
    # The shade on the right of the arch, and light on its left shoulder.
    f.poly([(_lerp(rx0, rx1, u), roof_y(u)) for u in us if u >= 0.62] + [(rx1 - 3.0, wall_top + 1.0), (_lerp(rx0, rx1, 0.62), wall_top + 1.0)], MATTING_SHADE, body=False)
    f.ink([(_lerp(rx0, rx1, u), roof_y(u) + 2.0) for u in us[4:24]], 1.6, MATTING_LIGHT)
    # The weave: the ribs run over the arch, and the strips of matting go
    # under and over them.
    for k in range(1, 16):
        u = k / 16.0
        x = _lerp(rx0, rx1, u)
        f.ink([(x, roof_y(u) + 1.0), (x, wall_top - 3.0)], 1.0, MATTING_DARK)
    for t in (0.33, 0.66):
        f.ink([(_lerp(rx0, rx1, u), _lerp(roof_y(u), wall_top - 3.0, t)) for u in us[2:-2]], 0.7, MATTING_DARK)
    for k in range(32):
        u = (k + 0.5) / 32.0
        x = _lerp(rx0, rx1, u)
        for t in (0.17, 0.5, 0.83):
            f.dot(x, _lerp(roof_y(u), wall_top - 3.0, t), 0.6, MATTING_SHADE if u < 0.62 else MATTING_DARK)
    f.poly([(rx0 + 3.0, wall_top - 4.0), (rx1 - 3.0, wall_top - 4.0), (rx1 - 3.0, wall_top + 1.0), (rx0 + 3.0, wall_top + 1.0)], BOAT_WOOD_DARK)
    f.ink([(rx0 + 4.0, wall_top - 3.0), (rx1 - 4.0, wall_top - 3.0)], 0.8, BOAT_WOOD_LIGHT)
    # The tips of the roof turn up, as a Song roof does.
    for s, x in ((-1.0, rx0), (1.0, rx1)):
        f.limb([(x - s * 6.0, roof_y(0.5 + s * 0.5) + 3.0), (x + s * 1.0, roof_y(0.5 + s * 0.5) - 3.0)], 2.6, BOAT_WOOD_DARK)
    # A red lantern hangs at the bow from a short post.
    px = x1 - 14.0
    f.limb([(px, top), (px, 66.0)], 2.6, BOAT_WOOD_DARK)
    f.limb([(px, 67.0), (px + 9.0, 67.0)], 2.0, BOAT_WOOD_DARK)
    f.ink([(px + 8.0, 67.0), (px + 8.0, 72.0)], 0.8, PRINT)
    f.ellipse(px + 8.0, 79.0, 5.4, 7.0, VERMILION)
    f.ellipse(px + 6.6, 77.6, 2.0, 3.6, VERMILION_LIGHT, body=False)
    for dy in (-3.0, 0.0, 3.0):
        f.ink([(px + 3.4, 79.0 + dy), (px + 12.6, 79.0 + dy)], 0.5, VERMILION_SHADE)
    f.poly([(px + 5.0, 71.4), (px + 11.0, 71.4), (px + 11.0, 73.0), (px + 5.0, 73.0)], BOAT_WOOD_DARK)
    f.poly([(px + 5.0, 85.4), (px + 11.0, 85.4), (px + 11.0, 87.0), (px + 5.0, 87.0)], BOAT_WOOD_DARK)
    f.ink([(px + 8.0, 87.0), (px + 8.0, 91.0)], 1.0, GOLD)
    # The hull: long, low and flat, of planks laid edge to edge. Its top is
    # the deck, and the deck is the platform.
    bottom = [(374.0, _lake_deck_y(374.0)), (368.0, top), (356.0, keel - 14.0), (338.0, keel - 3.0), (318.0, keel), (66.0, keel),
              (44.0, keel - 3.0), (26.0, keel - 14.0), (14.0, top), (10.0, _lake_deck_y(10.0))]
    hull = [(x, _lake_deck_y(x)) for x in xs] + bottom
    f.poly(hull, BOAT_WOOD)
    f.poly([(x, top + 18.0) for x in xs if 34.0 <= x <= 350.0] + [(338.0, keel - 3.0), (318.0, keel), (66.0, keel), (44.0, keel - 3.0)],
           BOAT_WOOD_SHADE, body=False)
    for off, lo, hi in ((17.0, 30.0, 354.0), (24.0, 40.0, 344.0)):
        f.ink([(x, top + off) for x in xs if lo <= x <= hi], 0.9, BOAT_WOOD_DARK)
    # The gunwale: a thick rail along the deck, and under it a band painted
    # red with gold studs, for this is a pleasure boat.
    f.limb([(x, _lake_deck_y(x) + 2.0) for x in xs[1:-1]], 3.6, BOAT_WOOD_LIGHT)
    band = [(x, _lake_deck_y(x) + 6.0) for x in xs[2:-2]] + [(x, _lake_deck_y(x) + 12.0) for x in xs[-3:1:-1]]
    f.poly(band, VERMILION, body=False)
    f.ink([(x, _lake_deck_y(x) + 11.4) for x in xs[2:-2]], 1.0, VERMILION_SHADE)
    f.ink([(x, _lake_deck_y(x) + 6.6) for x in xs[2:-2]], 0.8, VERMILION_LIGHT)
    for x in xs[4:-4:3]:
        f.dot(x, _lake_deck_y(x) + 9.0, 0.9, GOLD)
    # The stem and the stern board, a little proud of the planks.
    f.limb([(370.0, _lake_deck_y(370.0) + 2.0), (366.0, top + 1.0), (355.0, keel - 15.0)], 2.2, BOAT_WOOD_LIGHT, body=False)
    f.limb([(14.0, _lake_deck_y(14.0) + 2.0), (18.0, top + 1.0), (29.0, keel - 15.0)], 2.2, BOAT_WOOD_LIGHT, body=False)
    return A.finish(f, width=1.4)


# ---------------------------------------------------------------------------
# The press of the paper money.
# ---------------------------------------------------------------------------


def _bank_note(f: K.Frame, x0: float, y0: float, w: float, h: float, body: bool = True) -> None:
    """A sheet of Song paper money, upright: a thick printed border of
    small blocks, a top panel, columns of short strokes for the words and
    a picture panel at the foot. Two red seals are stamped over the print.
    There is no real writing on it."""
    x1, y1 = x0 + w, y0 + h
    f.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], PAPER, body)
    f.poly([(x0 + 2.0, y0 + 2.0), (x1 - 2.0, y0 + 2.0), (x1 - 2.0, y1 - 2.0), (x0 + 2.0, y1 - 2.0)], PRINT, body=False)
    f.poly([(x0 + 4.0, y0 + 4.0), (x1 - 4.0, y0 + 4.0), (x1 - 4.0, y1 - 4.0), (x0 + 4.0, y1 - 4.0)], PAPER, body=False)
    # The border: a chain of small light blocks on the dark band.
    k = x0 + 3.0
    while k < x1 - 3.0:
        f.dot(k, y0 + 3.0, 0.45, PAPER_SHADE)
        f.dot(k, y1 - 3.0, 0.45, PAPER_SHADE)
        k += 2.2
    k = y0 + 3.0
    while k < y1 - 3.0:
        f.dot(x0 + 3.0, k, 0.45, PAPER_SHADE)
        f.dot(x1 - 3.0, k, 0.45, PAPER_SHADE)
        k += 2.2
    # The top panel: a dark bar with a row of light blocks.
    f.poly([(x0 + 6.0, y0 + 6.0), (x1 - 6.0, y0 + 6.0), (x1 - 6.0, y0 + 10.0), (x0 + 6.0, y0 + 10.0)], PRINT, body=False)
    cols = max(2, int((w - 12.0) / 3.4))
    for c in range(cols):
        cx = x0 + 7.6 + c * (w - 15.2) / max(1, cols - 1)
        f.dot(cx, y0 + 8.0, 0.6, PAPER)
    # The columns of strokes: the text of the note, as marks only.
    rng = random.Random(f"bank note {x0:.0f} {y0:.0f}")
    text_y0, text_y1 = y0 + 13.0, y1 - h * 0.34
    for c in range(cols):
        cx = x0 + 7.6 + c * (w - 15.2) / max(1, cols - 1)
        y = text_y0
        while y < text_y1:
            ln = rng.uniform(1.0, 2.2)
            f.ink([(cx, y), (cx, min(text_y1, y + ln))], 0.8, PRINT)
            y += ln + 1.2
    # The picture panel at the foot: a frame with a pattern of stacked
    # blocks in it (strings of coins, drawn as marks).
    py0 = y1 - h * 0.3
    f.ink([(x0 + 6.0, py0), (x1 - 6.0, py0), (x1 - 6.0, y1 - 6.0), (x0 + 6.0, y1 - 6.0), (x0 + 6.0, py0)], 0.8, PRINT)
    for c in range(3):
        cx = x0 + w * (0.3 + 0.2 * c)
        for r in range(int((y1 - 8.0 - py0) / 2.4)):
            f.dot(cx, py0 + 2.4 + r * 2.4, 0.8, PRINT)
    # Two red seals: one square, one long.
    f.poly([(x0 + w * 0.52, y0 + h * 0.22), (x0 + w * 0.52 + 6.0, y0 + h * 0.22), (x0 + w * 0.52 + 6.0, y0 + h * 0.22 + 6.0), (x0 + w * 0.52, y0 + h * 0.22 + 6.0)], K.alpha(SEAL, 0.86), body=False)
    f.ink([(x0 + w * 0.52 + 1.5, y0 + h * 0.22 + 1.5), (x0 + w * 0.52 + 4.5, y0 + h * 0.22 + 1.5), (x0 + w * 0.52 + 4.5, y0 + h * 0.22 + 4.5)], 0.6, SEAL_LIGHT)
    f.poly([(x0 + w * 0.18, y0 + h * 0.46), (x0 + w * 0.18 + 4.4, y0 + h * 0.46), (x0 + w * 0.18 + 4.4, y0 + h * 0.46 + 8.0), (x0 + w * 0.18, y0 + h * 0.46 + 8.0)], K.alpha(SEAL, 0.86), body=False)


def _draw_money_press(anim: str, i: int, n: int):
    w, h = MONEY_PRESS_FRAME
    f = K.Frame(MONEY_PRESS_FRAME)
    ground = h - 6.0
    bx0, bx1 = 8.0, 152.0
    top = 76.0
    # A cord for drying the new sheets, on two thin posts at the back of
    # the bench. Two sheets hang on it.
    for x in (bx0 + 8.0, bx1 - 8.0):
        f.limb([(x, top - 4.0), (x, 10.0)], 2.6, BENCH_SHADE)
        f.ellipse(x, 10.0, 2.2, 2.2, BENCH)
    f.ink([(bx0 + 8.0, 12.0), (80.0, 15.0), (bx1 - 8.0, 12.0)], 0.9, CORD)
    for sx in (34.0, 96.0):
        _bank_note(f, sx, 14.0, 28.0, 44.0)
        for dx in (6.0, 22.0):
            f.limb([(sx + dx, 12.6), (sx + dx, 17.0)], 2.0, BENCH_LIGHT)
    # The bench: a thick top seen a little from above, on four legs.
    for x in (bx0 + 12.0, bx1 - 10.0):
        f.limb([(x + 3.0, top + 6.0), (x + 3.0, ground - 6.0)], 5.0, BENCH_SHADE)
    f.poly([(bx0 + 4.0, top - 6.0), (bx1, top - 6.0), (bx1 - 4.0, top), (bx0, top)], BENCH_LIGHT)
    f.poly([(bx0, top), (bx1 - 4.0, top), (bx1 - 4.0, top + 8.0), (bx0, top + 8.0)], BENCH)
    f.poly([(bx0, top + 6.0), (bx1 - 4.0, top + 6.0), (bx1 - 4.0, top + 8.0), (bx0, top + 8.0)], BENCH_SHADE, body=False)
    f.poly([(bx1 - 4.0, top), (bx1, top - 6.0), (bx1, top + 2.0), (bx1 - 4.0, top + 8.0)], BENCH_SHADE)
    for x in (bx0 + 6.0, bx1 - 14.0):
        f.limb([(x, top + 7.0), (x, ground - 2.0)], 5.4, BENCH)
        f.ink([(x - 1.2, top + 9.0), (x - 1.2, ground - 1.0)], 0.8, BENCH_LIGHT)
    f.limb([(bx0 + 6.0, ground - 18.0), (bx1 - 14.0, ground - 18.0)], 3.0, BENCH_SHADE)
    # The plate of bronze lies flat. Its face is cut in relief and inked
    # black; the printer lays a sheet on it and rubs the back with a pad.
    p0, p1 = 16.0, 60.0
    f.poly([(p0 + 3.0, top - 10.0), (p1 + 3.0, top - 10.0), (p1, top - 3.0), (p0, top - 3.0)], BRONZE_LIGHT)
    f.poly([(p0 + 3.8, top - 9.0), (p1 + 1.6, top - 9.0), (p1 - 0.8, top - 4.0), (p0 + 1.6, top - 4.0)], PRINTER_INK, body=False)
    f.poly([(p0, top - 3.0), (p1, top - 3.0), (p1, top - 1.0), (p0, top - 1.0)], BRONZE)
    f.poly([(p1, top - 3.0), (p1 + 3.0, top - 10.0), (p1 + 3.0, top - 8.0), (p1, top - 1.0)], BRONZE_SHADE)
    f.ink([(p0 + 1.0, top - 2.0), (p1 - 1.0, top - 2.0)], 0.6, BRONZE_LIGHT)
    # The raised lines of the plate shine through the ink.
    f.ink([(p0 + 5.4, top - 8.0), (p1 + 0.4, top - 8.0), (p1 - 1.4, top - 4.8), (p0 + 3.4, top - 4.8), (p0 + 5.4, top - 8.0)], 0.6, INK_SHEEN)
    for k in range(7):
        x = p0 + 10.0 + k * 4.6
        f.ink([(x + 1.4, top - 8.0), (x, top - 5.0)], 0.6, INK_SHEEN)
    f.dot(p0 + 7.0, top - 6.4, 0.8, K.alpha(SEAL, 0.7))
    # A rubbing pad of rolled cloth on the plate's corner.
    f.ellipse(p0 + 4.0, top - 10.0, 4.2, 2.8, PAPER_SHADE)
    f.ink([(p0 + 1.0, top - 10.6), (p0 + 7.0, top - 10.6)], 0.7, PAPER)
    # The ink stone: a slab of dark stone with a well at one end, where
    # the ink is ground with water.
    s0, s1 = 68.0, 86.0
    f.poly([(s0 + 2.0, top - 9.0), (s1 + 2.0, top - 9.0), (s1, top - 4.0), (s0, top - 4.0)], INKSTONE_LIGHT)
    f.poly([(s0, top - 4.0), (s1, top - 4.0), (s1, top - 1.0), (s0, top - 1.0)], INKSTONE)
    f.ellipse(s0 + 6.0, top - 6.6, 3.6, 1.4, PRINTER_INK, body=False)
    f.dot(s0 + 5.0, top - 7.0, 0.5, INK_SHEEN)
    f.limb([(s1 - 6.0, top - 6.8), (s1 - 1.0, top - 7.4)], 2.0, PRINTER_INK)
    # The brushes: two in a pot of bamboo, and a broad one for the ink
    # lying on the bench.
    bpx = 94.0
    for dx, lean in ((-1.4, -4.0), (1.6, 3.0)):
        f.limb([(bpx + dx, top - 10.0), (bpx + dx + lean, top - 28.0)], 1.6, BAMBOO_SHADE)
        f.ellipse(bpx + dx + lean * 1.08, top - 29.4, 1.2, 2.0, PRINTER_INK)
    f.poly([(bpx - 4.0, top - 13.0), (bpx + 4.0, top - 13.0), (bpx + 3.6, top - 2.0), (bpx - 3.6, top - 2.0)], BAMBOO)
    f.ink([(bpx - 2.6, top - 12.0), (bpx - 2.4, top - 3.0)], 0.7, BAMBOO_LIGHT)
    f.ink([(bpx - 3.8, top - 8.0), (bpx + 3.8, top - 8.0)], 0.6, BAMBOO_SHADE)
    f.limb([(62.0, top - 1.6), (78.0, top - 3.4)], 1.6, BAMBOO_SHADE)
    f.poly([(78.0, top - 5.4), (84.0, top - 4.4), (84.0, top - 2.2), (78.0, top - 1.6)], PRINTER_INK)
    # The stack of new sheets: the top one shows its print, the edges of
    # the others show as lines.
    k0, k1 = 104.0, 144.0
    for j in range(5):
        y = top - 1.0 - j * 1.6
        f.poly([(k0, y - 1.6), (k1, y - 1.6), (k1, y), (k0, y)], PAPER if j % 2 else PAPER_SHADE)
    ty = top - 9.0
    f.poly([(k0 + 2.0, ty - 9.0), (k1 + 2.0, ty - 9.0), (k1, ty), (k0, ty)], PAPER)
    f.ink([(k0 + 3.6, ty - 7.6), (k1 + 0.6, ty - 7.6), (k1 - 0.8, ty - 1.4), (k0 + 2.0, ty - 1.4), (k0 + 3.6, ty - 7.6)], 1.2, PRINT)
    for c in range(8):
        x = k0 + 9.0 + c * 3.4
        f.ink([(x + 0.8, ty - 6.0), (x + 0.2, ty - 3.4)], 0.7, PRINT)
    f.poly([(k1 - 9.0, ty - 6.6), (k1 - 4.6, ty - 6.6), (k1 - 5.4, ty - 3.4), (k1 - 9.8, ty - 3.4)], K.alpha(SEAL, 0.86), body=False)
    f.poly([(k0 + 4.6, ty - 6.0), (k0 + 7.6, ty - 6.0), (k0 + 7.0, ty - 3.0), (k0 + 4.0, ty - 3.0)], K.alpha(SEAL, 0.86), body=False)
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# The south-pointing fish.
# ---------------------------------------------------------------------------


def _draw_compass_bowl(anim: str, i: int, n: int):
    w, h = COMPASS_BOWL_FRAME
    f = K.Frame(COMPASS_BOWL_FRAME)
    cx = w / 2.0
    ground = h - 4.0
    # The stand: a low table of dark wood with short curved legs.
    st = ground - 9.0
    for x, s in ((cx - 15.0, -1.0), (cx + 15.0, 1.0)):
        f.limb([(x - s * 2.0, st + 2.0), (x, st + 6.0), (x + s * 1.6, ground - 0.6)], 2.6, STAND)
    f.poly([(cx - 19.0, st - 1.0), (cx + 19.0, st - 1.0), (cx + 18.0, st + 3.0), (cx - 18.0, st + 3.0)], STAND)
    f.ink([(cx - 17.0, st), (cx + 8.0, st)], 0.7, STAND_LIGHT)
    f.poly([(cx + 6.0, st - 1.0), (cx + 19.0, st - 1.0), (cx + 18.0, st + 3.0), (cx + 6.0, st + 3.0)], STAND_SHADE, body=False)
    # The bowl: shallow and wide, glazed in celadon.
    rim_y, rx, ry = 17.0, 22.0, 5.0
    body = _ring(cx, rim_y, rx, ry, 0.0, 180.0, 24)
    foot = [(cx + 8.0, st - 1.0), (cx - 8.0, st - 1.0)]
    side = [(cx + rx, rim_y)] + [(cx + rx * math.cos(a) , rim_y + (st - 4.0 - rim_y) * math.sin(a)) for a in [math.radians(10.0 * k) for k in range(1, 9)]]
    f.poly(side + [(cx + 9.0, st - 2.0)] + foot + [(cx - 9.0, st - 2.0)] + [(2.0 * cx - x, y) for x, y in side[::-1]], CELADON)
    f.poly([(cx + 9.0, st - 2.0), (cx + 9.0, st - 1.0), (cx - 9.0, st - 1.0), (cx - 9.0, st - 2.0)], CELADON_SHADE)
    f.poly([p for p in side if p[0] > cx + 6.0] + [(cx + 9.0, st - 2.0), (cx + 6.0, st - 3.0)], CELADON_SHADE, body=False)
    f.ink([(cx - rx + 3.0, rim_y + 3.0), (cx - rx + 7.0, rim_y + 7.0)], 1.0, CELADON_LIGHT)
    # The rim and the water in the bowl.
    f.ellipse(cx, rim_y, rx, ry, CELADON)
    f.ellipse(cx, rim_y + 0.6, rx - 2.2, ry - 1.4, WATER, body=False)
    f.ellipse(cx - 2.0, rim_y + 1.2, rx - 6.0, ry - 2.8, WATER_SHADE, body=False)
    f.limb(_ring(cx, rim_y, rx - 0.6, ry - 0.4, 180.0, 360.0, 18), 1.0, CELADON_LIGHT, body=False)
    f.ink([(cx - 12.0, rim_y - 1.0), (cx - 6.0, rim_y - 1.6)], 0.6, WATER_LIGHT)
    # The fish: a thin leaf of iron cut like a fish, heated and cooled in
    # the line of north and south, so it is a magnet. It floats on the
    # water, and its head turns to the south.
    fx, fy = cx + 1.0, rim_y + 0.6
    fish = [(fx - 8.0, fy), (fx - 5.0, fy - 1.6), (fx + 1.0, fy - 2.0), (fx + 6.0, fy - 1.0), (fx + 8.6, fy), (fx + 6.0, fy + 1.0),
            (fx + 1.0, fy + 1.8), (fx - 5.0, fy + 1.4)]
    f.poly(fish, IRON, body=False)
    f.poly([(fx - 7.0, fy), (fx - 11.0, fy - 2.6), (fx - 10.0, fy), (fx - 11.0, fy + 2.4)], IRON, body=False)
    f.ink([(fx - 4.0, fy - 0.8), (fx + 5.0, fy - 0.6)], 0.6, IRON_LIGHT)
    f.ink([(fx - 1.0, fy - 1.6), (fx - 1.6, fy + 1.4)], 0.5, IRON_SHADE)
    f.dot(fx + 5.4, fy - 0.2, 0.6, IRON_SHADE)
    return A.finish(f, width=1.0)


# ---------------------------------------------------------------------------
# The folding screen (byobu).
# ---------------------------------------------------------------------------

BYOBU_PANELS = 6


def _clip_band(pts: Sequence[Point], lo: float, hi: float) -> List[Point]:
    """The part of a polygon between the lines x = lo and x = hi."""
    def clip(poly: Sequence[Point], keep, cross) -> List[Point]:
        out: List[Point] = []
        for k in range(len(poly)):
            a, b = poly[k - 1], poly[k]
            if keep(b):
                if not keep(a):
                    out.append(cross(a, b))
                out.append(b)
            elif keep(a):
                out.append(cross(a, b))
        return out

    def at(xv: float):
        return lambda a, b: (xv, a[1] + (b[1] - a[1]) * (xv - a[0]) / (b[0] - a[0]))

    part = clip(pts, lambda p: p[0] >= lo, at(lo))
    return clip(part, lambda p: p[0] <= hi, at(hi)) if part else []


class _Byobu:
    """The geometry of the screen. The panels stand in a zigzag. The folds
    that come toward us stand lower in the picture than the folds that go
    back, as the screen is seen a little from above. The painting is laid
    out flat, in units of panels (`u` from 0 to 6) and of height (`v` from
    0 at the top to 1 at the foot), and is mapped onto each panel."""

    def __init__(self, w: float, h: float) -> None:
        x0, x1 = 8.0, w - 8.0
        self.xs = [_lerp(x0, x1, k / BYOBU_PANELS) for k in range(BYOBU_PANELS + 1)]
        self.tops = [14.0 if k % 2 == 0 else 6.0 for k in range(BYOBU_PANELS + 1)]
        self.foots = [h - 6.0 if k % 2 == 0 else h - 14.0 for k in range(BYOBU_PANELS + 1)]

    def corner(self, k: int, u: float, v: float) -> Point:
        """A point on panel `k`: `u` across it from 0 to 1, `v` down it."""
        xa, xb = self.xs[k], self.xs[k + 1]
        ta, tb = self.tops[k], self.tops[k + 1]
        fa, fb = self.foots[k], self.foots[k + 1]
        x = _lerp(xa, xb, u)
        return (x, _lerp(_lerp(ta, tb, u), _lerp(fa, fb, u), v))

    def inner(self, k: int, u: float, v: float, margin: float) -> Point:
        """A point of the painting on panel `k`, inside a border of
        `margin` pixels."""
        width = self.xs[k + 1] - self.xs[k]
        height = self.foots[k] - self.tops[k]
        mu, mv = margin / width, margin / height
        return self.corner(k, _lerp(mu, 1.0 - mu, u), _lerp(mv, 1.0 - mv, v))


def _byobu_paint(f: K.Frame, s: _Byobu, pts: Sequence[Point], colour: RGBA, margin: float) -> None:
    """Paint one flat shape of the picture across the panels."""
    dense: List[Point] = []
    for k in range(len(pts)):
        a, b = pts[k], pts[(k + 1) % len(pts)]
        steps = max(1, int(abs(b[0] - a[0]) * 8))
        for j in range(steps):
            dense.append(_mix(a, b, j / float(steps)))
    for k in range(BYOBU_PANELS):
        part = _clip_band(dense, float(k), float(k + 1))
        if len(part) >= 3:
            f.poly([s.inner(k, u - k, v, margin) for u, v in part], colour, body=False)


def _byobu_line(f: K.Frame, s: _Byobu, pts: Sequence[Point], width: float, colour: RGBA, margin: float) -> None:
    """Paint one line of the picture across the panels; it breaks at each
    fold."""
    for k in range(BYOBU_PANELS):
        run: List[Point] = []
        for j in range(len(pts) - 1):
            a, b = pts[j], pts[j + 1]
            for q in range(6):
                u, v = _mix(a, b, q / 6.0)
                if k <= u <= k + 1:
                    run.append(s.inner(k, u - k, v, margin))
                elif run:
                    if len(run) > 1:
                        f.ink(run, width, colour)
                    run = []
        if len(run) > 1:
            f.ink(run, width, colour)


def _draw_byobu_screen(anim: str, i: int, n: int):
    w, h = BYOBU_FRAME
    f = K.Frame(BYOBU_FRAME)
    s = _Byobu(w, h)
    rng = random.Random("history_byobu_screen")
    m = 4.6
    # Each panel: a frame of black lacquer, and a border of brocade round
    # the painted silk.
    for k in range(BYOBU_PANELS):
        quad = [s.corner(k, 0.0, 0.0), s.corner(k, 1.0, 0.0), s.corner(k, 1.0, 1.0), s.corner(k, 0.0, 1.0)]
        f.poly(quad, LACQUER)
        f.poly([s.inner(k, 0.0, 0.0, 1.8), s.inner(k, 1.0, 0.0, 1.8), s.inner(k, 1.0, 1.0, 1.8), s.inner(k, 0.0, 1.0, 1.8)], BROCADE, body=False)
        f.poly([s.inner(k, 0.0, 0.0, m), s.inner(k, 1.0, 0.0, m), s.inner(k, 1.0, 1.0, m), s.inner(k, 0.0, 1.0, m)], SILK, body=False)
        # A small pattern of light dots on the brocade.
        for t in range(1, 6):
            for v in (-0.04, 1.04):
                p = s.inner(k, t / 6.0, v, m - 0.3)
                f.dot(p[0], p[1], 0.5, BROCADE_LIGHT)
    # The picture, in the court style of the time (yamato-e): far blue
    # hills, near green hills with pines, a garden pond with waves and a
    # shore of pale sand, and bands of gold cloud that run across the
    # panels and join the scene.
    far = [(0.0, 0.76), (0.0, 0.44), (0.5, 0.34), (1.0, 0.40), (1.7, 0.28), (2.4, 0.38), (3.0, 0.31), (3.7, 0.40), (4.4, 0.30), (5.1, 0.37),
           (5.6, 0.29), (6.0, 0.34), (6.0, 0.76)]
    _byobu_paint(f, s, far, HILL_FAR, m)
    _byobu_paint(f, s, [(0.0, 0.76), (0.0, 0.56), (1.2, 0.52), (2.5, 0.58), (3.6, 0.52), (4.8, 0.56), (6.0, 0.52), (6.0, 0.76)], K.shade(HILL_FAR, 0.9), m)
    left_hill = [(0.0, 0.78), (0.0, 0.46), (0.4, 0.42), (0.9, 0.48), (1.4, 0.44), (2.0, 0.56), (2.6, 0.70), (2.9, 0.78)]
    right_hill = [(3.3, 0.78), (3.8, 0.60), (4.3, 0.50), (4.8, 0.52), (5.4, 0.40), (6.0, 0.46), (6.0, 0.78)]
    for hill in (left_hill, right_hill):
        _byobu_paint(f, s, hill, HILL, m)
    _byobu_paint(f, s, [(0.0, 0.78), (0.0, 0.62), (0.8, 0.60), (1.8, 0.66), (2.9, 0.78)], HILL_SHADE, m)
    _byobu_paint(f, s, [(3.3, 0.78), (4.4, 0.64), (5.2, 0.62), (6.0, 0.66), (6.0, 0.78)], HILL_SHADE, m)
    # The pond, and the shore of pale sand in front of it.
    _byobu_paint(f, s, [(0.0, 1.0), (0.0, 0.74), (1.4, 0.72), (3.0, 0.70), (4.6, 0.72), (6.0, 0.74), (6.0, 1.0)], POND, m)
    for y in (0.76, 0.81):
        for x in [0.25 + 0.5 * j for j in range(12)]:
            xx = x + rng.uniform(-0.1, 0.1)
            _byobu_line(f, s, [(xx, y + 0.01), (xx + 0.08, y - 0.012), (xx + 0.16, y + 0.01)], 0.6, POND_LIGHT, m)
    _byobu_paint(f, s, [(0.0, 1.0), (0.0, 0.88), (1.0, 0.86), (2.2, 0.91), (3.4, 0.88), (4.6, 0.85), (6.0, 0.88), (6.0, 1.0)], SILK_SHADE, m)
    # Pines on the hills: a short trunk and flat layers of dark needles.
    for u, v, size in ((0.45, 0.44, 1.0), (1.35, 0.48, 0.8), (2.2, 0.62, 0.7), (4.4, 0.52, 1.0), (5.35, 0.42, 1.0), (4.95, 0.56, 0.7)):
        _byobu_line(f, s, [(u, v + 0.12 * size), (u + 0.02, v - 0.02)], 1.2, TRUNK, m)
        for dy, half in ((0.0, 0.14), (0.05, 0.2), (0.10, 0.17)):
            yy = v - 0.03 + dy * size
            _byobu_paint(f, s, [(u - half * size, yy + 0.02), (u, yy - 0.025), (u + half * size, yy + 0.02), (u, yy + 0.03)], PINE, m)
    # The gold clouds: long bands with round ends, over the top of the
    # scene and through the hills.
    for u0, u1, v, th in ((-0.3, 2.6, 0.13, 0.12), (3.2, 6.3, 0.10, 0.12), (1.8, 4.3, 0.22, 0.08), (3.9, 6.3, 0.62, 0.06),
                          (-0.3, 1.5, 0.66, 0.06)):
        band = [(u0 - 0.06, v)]
        for j in range(9):
            band.append((_lerp(u0, u1, j / 8.0), v - th * 0.5 - (0.015 if j % 2 else 0.0)))
        band.append((u1 + 0.06, v))
        for j in range(8, -1, -1):
            band.append((_lerp(u0, u1, j / 8.0), v + th * 0.5 + (0.012 if j % 2 == 0 else 0.0)))
        _byobu_paint(f, s, band, GOLD, m)
        _byobu_line(f, s, [(_lerp(u0, u1, t), v - th * 0.2) for t in (0.1, 0.5, 0.9)], 0.7, GOLD_LIGHT, m)
    # The panels that face away from the light are in shade.
    for k in range(1, BYOBU_PANELS, 2):
        quad = [s.corner(k, 0.0, 0.0), s.corner(k, 1.0, 0.0), s.corner(k, 1.0, 1.0), s.corner(k, 0.0, 1.0)]
        f.poly(quad, K.alpha(OUTLINE_SHADE, 0.34), body=False)
    # The folds: a thin light edge on each fold that comes toward us.
    for k in range(0, BYOBU_PANELS + 1, 2):
        f.ink([(s.xs[k], s.tops[k] + 1.0), (s.xs[k], s.foots[k] - 1.0)], 0.8, LACQUER_LIGHT)
    # Small hinges of gilt metal on the frame.
    for k in range(1, BYOBU_PANELS):
        for v in (0.18, 0.82):
            x, y = s.xs[k], _lerp(s.tops[k], s.foots[k], v)
            f.poly([(x - 1.4, y - 2.4), (x + 1.4, y - 2.4), (x + 1.4, y + 2.4), (x - 1.4, y + 2.4)], GOLD_SHADE, body=False)
    return A.finish(f, width=1.2)



# ---------------------------------------------------------------------------
# The ox carriage (gissha) of the Heian court.
# ---------------------------------------------------------------------------


def _spoked_wheel(f: K.Frame, cx: float, cy: float, r: float, rim: RGBA, spoke: RGBA, light: RGBA, n_spokes: int = 16) -> None:
    """A tall wheel of the court: a thick lacquered rim, many thin spokes
    and a big hub."""
    for k in range(n_spokes):
        a = math.tau * k / n_spokes + 0.12
        f.limb([(cx + math.cos(a) * 6.0, cy + math.sin(a) * 6.0), (cx + math.cos(a) * (r - 4.0), cy + math.sin(a) * (r - 4.0))], 2.0, spoke)
    ring = K.ellipse_points(cx, cy, r - 3.0, r - 3.0, 64)
    f.limb(ring + ring[:2], 6.0, rim)
    f.ink(K.ellipse_points(cx, cy, r - 1.6, r - 1.6, 64)[34:54], 1.2, light)
    f.ink(K.ellipse_points(cx, cy, r - 5.6, r - 5.6, 64)[34:54], 0.8, light)
    f.ellipse(cx, cy, 9.0, 9.0, rim)
    f.ellipse(cx, cy, 5.0, 5.0, GOLD_SHADE, body=False)
    f.ellipse(cx - 1.0, cy - 1.0, 2.2, 2.2, GOLD, body=False)


def _hatch(f: K.Frame, x0: float, y0: float, x1: float, y1: float, step: float, slope: float, width: float, colour: RGBA) -> None:
    """Parallel lines x = c + slope * y, `step` apart, cut to a box: the
    weave of thin strips."""
    c = min(x0 - slope * y0, x0 - slope * y1)
    c_end = max(x1 - slope * y0, x1 - slope * y1)
    while c <= c_end:
        ya, yb = sorted(((x0 - c) / slope, (x1 - c) / slope))
        ya, yb = max(y0, ya), min(y1, yb)
        if yb - ya > 0.5:
            f.ink([(c + slope * ya, ya), (c + slope * yb, yb)], width, colour)
        c += step


def _black_ox(f: K.Frame, x: float, ground: float) -> Point:
    """A black ox that walks to the right; `x` is its rump. It gives the
    point on its neck where the yoke sits. Its coordinates go up from the
    ground."""
    def P(pts: Sequence[Point]) -> List[Point]:
        return [(x + px, ground - py) for px, py in pts]

    def leg(pts: Sequence[Point], width: float, colour: RGBA, light: bool) -> None:
        f.limb(P(pts), width, colour)
        if light:
            f.ink(P([(px - width * 0.3, py) for px, py in pts[:-1]]), 0.8, OX_LIGHT)
        hx, hy = pts[-1]
        f.poly(P([(hx - 2.6, 0.0), (hx - 2.0, hy + 2.0), (hx + 2.4, hy + 2.0), (hx + 3.4, 0.0)]), OX_SHADE)

    # The far legs, in shade: a hind leg with its hock bent back, and a
    # straight foreleg.
    leg([(16.0, 34.0), (18.0, 18.0), (15.0, 10.0), (15.0, 3.0)], 5.0, OX_SHADE, False)
    leg([(52.0, 32.0), (54.0, 16.0), (55.0, 3.0)], 4.6, OX_SHADE, False)
    # The body: a deep chest, a high ridge at the withers, a straight back
    # and square hips. The belly hangs a little.
    body = [(0.0, 50.0), (3.0, 57.0), (12.0, 60.0), (30.0, 58.0), (44.0, 60.0), (52.0, 65.0), (60.0, 63.0), (66.0, 56.0), (64.0, 44.0),
            (59.0, 32.0), (52.0, 27.0), (40.0, 26.0), (26.0, 27.0), (16.0, 30.0), (8.0, 34.0), (2.0, 41.0)]
    f.poly(P(body), OX)
    # The thigh shows as a round mass over the hind leg.
    f.ellipse(x + 11.0, ground - 44.0, 11.0, 13.0, OX)
    # The head, carried low and forward: a broad brow, a long face and a
    # pale muzzle.
    head = [(60.0, 63.0), (68.0, 62.0), (74.0, 56.0), (79.0, 44.0), (79.0, 38.0), (73.0, 36.0), (68.0, 42.0), (62.0, 50.0)]
    f.poly(P(head), OX)
    f.poly(P([(73.0, 45.0), (79.0, 44.0), (79.0, 38.0), (73.0, 36.0), (71.0, 40.0)]), OX_LIGHT, body=False)
    f.dot(x + 76.6, ground - 41.6, 0.8, OX_SHADE)
    f.dot(x + 69.0, ground - 54.0, 1.3, OX_HORN)
    f.dot(x + 69.4, ground - 54.0, 0.6, OX_SHADE)
    f.ink(P([(66.0, 61.0), (74.0, 54.0), (78.0, 46.0)]), 0.9, OX_LIGHT)
    # The horns curve out and up; the ear stands out under them.
    f.limb(P([(66.0, 62.0), (70.0, 67.0), (74.0, 68.0)]), 2.4, K.shade(OX_HORN, 0.8))
    f.limb(P([(64.0, 62.0), (66.0, 68.0), (70.0, 72.0)]), 2.8, OX_HORN)
    f.poly(P([(63.0, 58.0), (55.0, 59.0), (53.0, 55.0), (61.0, 54.0)]), OX_SHADE)
    # Light along the back and over the hip; the belly in shade.
    f.ink(P([(4.0, 56.0), (12.0, 58.6), (30.0, 56.6), (44.0, 58.6), (52.0, 63.0)]), 1.4, OX_LIGHT)
    f.ink(P([(4.0, 50.0), (6.0, 40.0), (12.0, 33.0)]), 1.0, OX_LIGHT)
    f.ink(P([(46.0, 56.0), (48.0, 42.0), (52.0, 32.0)]), 0.9, OX_SHADE)
    f.poly(P([(16.0, 31.0), (26.0, 28.0), (40.0, 27.0), (52.0, 28.0), (46.0, 31.0), (26.0, 31.0)]), OX_SHADE, body=False)
    # The tail, with a tuft.
    f.limb(P([(1.0, 54.0), (-3.0, 42.0), (-3.0, 24.0)]), 1.6, OX_SHADE)
    f.ellipse(x - 3.0, ground - 22.0, 2.0, 3.4, OX_SHADE)
    # The near legs.
    leg([(12.0, 36.0), (14.0, 18.0), (10.0, 10.0), (10.0, 3.0)], 5.6, OX, True)
    leg([(56.0, 34.0), (57.0, 16.0), (58.0, 3.0)], 5.2, OX, True)
    # A cord of red silk on the head and the hips, as the court's oxen
    # wore.
    f.ink(P([(65.0, 61.0), (72.0, 55.0), (75.0, 46.0)]), 1.2, CORD_RED)
    f.ink(P([(4.0, 52.0), (8.0, 44.0), (16.0, 38.0)]), 1.2, CORD_RED)
    return (x + 58.0, ground - 61.0)


def _draw_ox_carriage(anim: str, i: int, n: int):
    w, h = OX_CARRIAGE_FRAME
    f = K.Frame(OX_CARRIAGE_FRAME)
    ground = h - 6.0
    wx, wr = 72.0, 44.0
    wy = ground - wr
    # The far wheel shows behind the cabin.
    _spoked_wheel(f, wx + 7.0, wy - 3.0, wr, K.shade(LACQUER, 0.9), LACQUER, LACQUER_LIGHT)
    # The far shaft, behind the ox.
    yoke_far = (190.0, 94.0)
    f.limb([(26.0, 104.0), yoke_far], 3.4, LACQUER)
    # The ox.
    yoke = _black_ox(f, 136.0, ground)
    # The cabin: a tall box. Its sides are of woven strips of thin wood
    # (ajiro) in a frame of black lacquer, and its front is open behind a
    # blind of split bamboo.
    c0, c1 = 26.0, 118.0
    ct, cb = 38.0, 104.0
    depth = (16.0, -6.0)
    f.poly([(c0, ct), (c1, ct), (c1, cb), (c0, cb)], WICKER)
    _hatch(f, c0, ct, c1, cb, 6.0, 1.0, 0.7, WICKER_SHADE)
    _hatch(f, c0, ct, c1, cb, 6.0, -1.0, 0.5, K.alpha(WICKER_SHADE, 0.6))
    # The frame of black lacquer: posts, a sill and a head rail.
    for x in (c0 + 2.0, c0 + 48.0, c1 - 2.0):
        f.limb([(x, ct), (x, cb)], 4.0, LACQUER)
    f.limb([(c0, cb - 2.0), (c1, cb - 2.0)], 5.0, LACQUER)
    f.limb([(c0, ct + 2.0), (c1, ct + 2.0)], 4.0, LACQUER)
    f.ink([(c0 + 1.0, cb - 3.6), (c1 - 1.0, cb - 3.6)], 0.8, LACQUER_LIGHT)
    # The side window (monomi), with a small blind half up.
    f.poly([(c0 + 60.0, ct + 12.0), (c1 - 12.0, ct + 12.0), (c1 - 12.0, ct + 34.0), (c0 + 60.0, ct + 34.0)], INTERIOR)
    f.poly([(c0 + 60.0, ct + 12.0), (c1 - 12.0, ct + 12.0), (c1 - 12.0, ct + 22.0), (c0 + 60.0, ct + 22.0)], BLIND, body=False)
    for k in range(1, 9):
        y = ct + 12.0 + k * 1.2
        f.ink([(c0 + 60.0, y), (c1 - 12.0, y)], 0.4, BLIND_SHADE)
    f.ink([(c0 + 60.0, ct + 12.0), (c1 - 12.0, ct + 12.0), (c1 - 12.0, ct + 34.0), (c0 + 60.0, ct + 34.0), (c0 + 60.0, ct + 12.0)], 1.4, LACQUER)
    # Gilt fittings at the corners of the frame.
    for x, y in ((c0 + 2.0, ct + 3.0), (c0 + 2.0, cb - 3.0), (c0 + 48.0, ct + 3.0), (c0 + 48.0, cb - 3.0), (c1 - 2.0, ct + 3.0), (c1 - 2.0, cb - 3.0)):
        f.ellipse(x, y, 1.8, 1.8, GOLD, body=False)
    # The front, seen a little from the side: the bamboo blind, and under
    # it the long drape of silk that hangs out over the front step.
    fq = [(c1, ct), (c1 + depth[0], ct + depth[1]), (c1 + depth[0], cb + depth[1]), (c1, cb)]
    f.poly(fq, BLIND)
    for k in range(1, 22):
        y = ct + 3.0 * k
        f.ink([(c1, y), (c1 + depth[0], y + depth[1])], 0.5, BLIND_SHADE)
    for t in (0.33, 0.66):
        f.ink([(c1 + depth[0] * t, ct + depth[1] * t), (c1 + depth[0] * t, cb + depth[1] * t - 4.0)], 0.8, BLIND_SHADE)
    for j, colour in enumerate((DRAPE, DRAPE_ALT, DRAPE_LIGHT)):
        t0, t1 = j / 3.0, (j + 1) / 3.0
        top0 = ct + 30.0 + depth[1] * t0
        top1 = ct + 30.0 + depth[1] * t1
        f.poly([(c1 + depth[0] * t0, top0), (c1 + depth[0] * t1, top1), (c1 + depth[0] * t1 + 6.0, cb + 12.0 + depth[1] * t1), (c1 + depth[0] * t0 + 6.0, cb + 12.0 + depth[1] * t0)], colour)
    f.limb([(c1, ct), (c1, cb)], 3.6, LACQUER)
    f.limb([(c1 + depth[0], ct + depth[1]), (c1 + depth[0], cb + depth[1])], 3.0, LACQUER)
    f.limb([(c1, ct + 2.0), (c1 + depth[0], ct + 2.0 + depth[1])], 3.0, LACQUER)
    # The roof: a long shell that curves over the box, and reaches out over
    # the front and the back. It is thatched with strips of pale palm leaf.
    r0, r1 = 12.0, 146.0
    eave = ct + 2.0

    def roof_top(u: float) -> float:
        return eave - 6.0 - 18.0 * math.sin(math.pi * min(1.0, max(0.0, (u - 0.04) / 0.92))) ** 0.45

    us = [k / 40.0 for k in range(41)]
    shell = [(_lerp(r0, r1, u), roof_top(u)) for u in us]
    f.poly(shell + [(r1, eave - 2.0), (r1 - 4.0, eave + 2.0), (r0 + 4.0, eave + 2.0), (r0, eave - 2.0)], PALM)
    f.poly([(_lerp(r0, r1, u), roof_top(u)) for u in us if u >= 0.66] + [(r1, eave - 2.0), (r1 - 4.0, eave + 2.0), (_lerp(r0, r1, 0.66), eave + 2.0)], PALM_SHADE, body=False)
    for k in range(1, 22):
        u = k / 22.0
        x = _lerp(r0, r1, u)
        f.ink([(x, roof_top(u) + 1.0), (x + 1.0, eave)], 0.7, PALM_DARK if u >= 0.66 else PALM_SHADE)
    f.ink([(_lerp(r0, r1, u), roof_top(u) + 2.0) for u in us[3:26]], 1.4, PALM_LIGHT)
    # The edge of the roof is bound with a black lacquered rim, and the
    # front eave curves up a little.
    f.limb([(r0, eave - 1.0), (r1, eave - 1.0)], 3.0, LACQUER)
    f.limb([(r1 - 4.0, eave - 1.0), (r1 + 2.0, eave - 6.0)], 3.0, LACQUER)
    f.limb([(r0 + 4.0, eave - 1.0), (r0 - 2.0, eave - 5.0)], 3.0, LACQUER)
    # The near shaft: it runs under the cabin, out past the front, to the
    # yoke on the neck of the ox. Its back end is the step.
    f.limb([(14.0, 108.0), (yoke[0] + 4.0, yoke[1] + 6.0)], 4.0, LACQUER)
    f.ink([(16.0, 106.6), (yoke[0] + 2.0, yoke[1] + 4.6)], 0.8, LACQUER_LIGHT)
    # The yoke across the ox's neck.
    f.limb([(yoke[0] - 1.0, yoke[1] - 4.0), (yoke[0] + 5.0, yoke[1] + 10.0)], 3.6, LACQUER)
    f.ink([(yoke[0] - 0.4, yoke[1] - 2.4), (yoke[0] + 3.6, yoke[1] + 7.4)], 0.7, LACQUER_LIGHT)
    # The near wheel, in front of the cabin.
    _spoked_wheel(f, wx, wy, wr, LACQUER, K.shade(LACQUER, 1.4), LACQUER_LIGHT)
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# The rain gauge (cheugugi) of 1441.
# ---------------------------------------------------------------------------


def _draw_rain_gauge(anim: str, i: int, n: int):
    w, h = RAIN_GAUGE_FRAME
    f = K.Frame(RAIN_GAUGE_FRAME)
    cx = w / 2.0
    ground = h - 5.0
    # The stand of granite (cheugudae): a long block with a moulded top,
    # and a round socket in its top that holds the gauge upright.
    sx0, sx1 = cx - 20.0, cx + 20.0
    st = 72.0
    f.poly([(sx0, st + 6.0), (sx1, st + 6.0), (sx1, ground), (sx0, ground)], GRANITE)
    f.poly([(sx1 - 9.0, st + 6.0), (sx1, st + 6.0), (sx1, ground), (sx1 - 9.0, ground)], GRANITE_SHADE, body=False)
    f.poly([(sx0 - 3.0, st), (sx1 + 3.0, st), (sx1 + 3.0, st + 6.0), (sx0 - 3.0, st + 6.0)], GRANITE)
    f.poly([(sx1 - 6.0, st), (sx1 + 3.0, st), (sx1 + 3.0, st + 6.0), (sx1 - 6.0, st + 6.0)], GRANITE_SHADE, body=False)
    f.ink([(sx0 - 2.0, st + 1.0), (sx1 + 2.0, st + 1.0)], 0.9, GRANITE_LIGHT)
    f.ink([(sx0 - 3.0, st + 6.0), (sx1 + 3.0, st + 6.0)], 0.9, GRANITE_DARK)
    # A sunk panel on the front, with a carved border, and a plinth at the
    # foot.
    f.poly([(sx0 + 5.0, st + 12.0), (sx1 - 5.0, st + 12.0), (sx1 - 5.0, ground - 8.0), (sx0 + 5.0, ground - 8.0)], GRANITE_SHADE, body=False)
    f.poly([(sx0 + 6.0, st + 13.0), (sx1 - 6.0, st + 13.0), (sx1 - 6.0, ground - 9.0), (sx0 + 6.0, ground - 9.0)], K.shade(GRANITE, 0.94), body=False)
    f.ink([(sx0 + 5.0, ground - 8.0), (sx1 - 5.0, ground - 8.0), (sx1 - 5.0, st + 12.0)], 0.8, GRANITE_LIGHT)
    f.ink([(sx0 + 9.0, (st + ground) / 2.0 + 2.0), (sx1 - 9.0, (st + ground) / 2.0 + 2.0)], 0.6, GRANITE_SHADE)
    f.poly([(sx0 - 2.0, ground - 4.0), (sx1 + 2.0, ground - 4.0), (sx1 + 2.0, ground), (sx0 - 2.0, ground)], GRANITE)
    f.ink([(sx0 - 1.0, ground - 3.2), (sx1 + 1.0, ground - 3.2)], 0.8, GRANITE_LIGHT)
    f.poly([(sx1 - 7.0, ground - 4.0), (sx1 + 2.0, ground - 4.0), (sx1 + 2.0, ground), (sx1 - 7.0, ground)], GRANITE_SHADE, body=False)
    rng = random.Random("history_rain_gauge")
    for _ in range(30):
        f.dot(rng.uniform(sx0 + 1.0, sx1 - 1.0), rng.uniform(st + 2.0, ground - 1.0), 0.45, K.alpha(GRANITE_DARK, 0.5))
    # The gauge: a cylinder of bronze, open at its top, made in sections.
    # The rain that falls in it is measured with a ruler.
    gx0, gx1 = cx - 10.0, cx + 10.0
    gt = 16.0
    f.poly([(gx0, gt), (gx1, gt), (gx1, st + 1.0), (gx0, st + 1.0)], BRONZE)
    f.poly([(cx + 3.0, gt), (gx1, gt), (gx1, st + 1.0), (cx + 3.0, st + 1.0)], BRONZE_SHADE, body=False)
    f.poly([(gx0 + 2.0, gt + 3.0), (gx0 + 5.0, gt + 3.0), (gx0 + 5.0, st - 1.0), (gx0 + 2.0, st - 1.0)], BRONZE_LIGHT, body=False)
    # The bands where the sections join.
    for y in (gt + 3.0, gt + 20.0, gt + 38.0, st - 3.0):
        f.poly([(gx0 - 1.2, y - 1.8), (gx1 + 1.2, y - 1.8), (gx1 + 1.2, y + 1.8), (gx0 - 1.2, y + 1.8)], BRONZE)
        f.poly([(cx + 3.0, y - 1.8), (gx1 + 1.2, y - 1.8), (gx1 + 1.2, y + 1.8), (cx + 3.0, y + 1.8)], BRONZE_SHADE, body=False)
        f.ink([(gx0 - 0.4, y - 0.8), (cx + 2.0, y - 0.8)], 0.6, BRONZE_LIGHT)
        f.ink([(gx0 - 1.2, y + 1.8), (gx1 + 1.2, y + 1.8)], 0.6, BRONZE_DARK)
    # A little green of age on the bronze.
    for x, y in ((gx0 + 7.0, gt + 12.0), (gx1 - 4.0, gt + 30.0), (gx0 + 4.0, gt + 46.0)):
        f.ellipse(x, y, 1.4, 0.9, K.alpha(VERDIGRIS, 0.6), body=False)
    # The open top.
    f.ellipse(cx, gt, 11.0, 2.8, BRONZE)
    f.ellipse(cx, gt + 0.3, 9.0, 1.8, BRONZE_DARK, body=False)
    f.ink(_ring(cx, gt, 10.6, 2.6, 180.0, 300.0, 10), 0.7, BRONZE_LIGHT)
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# The self-striking water clock (Jagyeongnu).
# ---------------------------------------------------------------------------


def _jar(f: K.Frame, cx: float, foot: float, r: float, height: float) -> Point:
    """A great water vessel of bronze: a wide round body with a short
    neck and a flat lip. It gives the point of its spout, low on its right
    side."""
    top = foot - height
    prof = [(foot, r * 0.62), (foot - height * 0.18, r * 0.92), (foot - height * 0.5, r), (foot - height * 0.78, r * 0.86),
            (top + 4.0, r * 0.56), (top + 2.0, r * 0.62)]
    left = [(cx - rr, y) for y, rr in prof]
    right = [(cx + rr, y) for y, rr in prof[::-1]]
    f.poly(left + right, BRONZE)
    f.poly([(cx + rr * 0.35, y) for y, rr in prof] + [(cx + rr, y) for y, rr in prof[::-1]], BRONZE_SHADE, body=False)
    f.poly([(cx - rr * 0.84, y) for y, rr in prof[1:-1]] + [(cx - rr * 0.6, y) for y, rr in prof[-2:0:-1]], BRONZE_LIGHT, body=False)
    f.ellipse(cx, top + 2.0, r * 0.62, r * 0.12 + 1.2, BRONZE)
    f.ellipse(cx, top + 2.2, r * 0.48, r * 0.07 + 0.8, BRONZE_DARK, body=False)
    # Two raised bands round the body.
    for t in (0.34, 0.66):
        y = foot - height * t
        rr = r * (0.96 if t < 0.5 else 0.94)
        f.ink([(cx - rr + 1.0, y), (cx, y + 1.6), (cx + rr - 1.0, y)], 1.2, BRONZE_DARK)
    return (cx + r * 0.9, foot - height * 0.2)


def _stone_step(f: K.Frame, x0: float, x1: float, top: float, foot: float) -> None:
    """One step of the stone platform: a block of dressed granite."""
    f.poly([(x0, top), (x1, top), (x1, foot), (x0, foot)], GRANITE)
    f.poly([(x1 - 6.0, top), (x1, top), (x1, foot), (x1 - 6.0, foot)], GRANITE_SHADE, body=False)
    f.ink([(x0 + 1.0, top + 1.2), (x1 - 1.0, top + 1.2)], 1.0, GRANITE_LIGHT)
    y = top + 14.0
    row = 0
    while y < foot - 2.0:
        f.ink([(x0 + 1.0, y), (x1 - 1.0, y)], 0.7, GRANITE_DARK)
        for x in range(int(x0 + (10 if row % 2 else 18)), int(x1 - 4), 18):
            f.ink([(x, y - 13.4), (x, y - 0.6)], 0.6, GRANITE_DARK)
        y += 14.0
        row += 1


def _clock_figure(f: K.Frame, x: float, foot: float, robe: RGBA, hand: Point) -> None:
    """A small wooden figure of a court official, as on the clock: a
    painted robe, a black hat with two short wings, and an arm raised to
    `hand`, where it holds a mallet. It has a calm face."""
    f.poly([(x - 5.0, foot), (x - 4.0, foot - 13.0), (x - 2.6, foot - 16.0), (x + 2.6, foot - 16.0), (x + 4.0, foot - 13.0), (x + 5.0, foot)], robe)
    f.poly([(x + 1.0, foot - 15.0), (x + 2.6, foot - 16.0), (x + 4.0, foot - 13.0), (x + 5.0, foot), (x + 1.6, foot)], K.shade(robe, 0.72), body=False)
    f.ink([(x - 4.4, foot - 7.0), (x + 4.4, foot - 7.0)], 1.0, GOLD_SHADE)
    sh = (x + 2.0, foot - 14.0)
    f.limb([sh, ((sh[0] + hand[0]) / 2.0, (sh[1] + hand[1]) / 2.0 + 1.0), hand], 2.4, robe)
    f.ellipse(hand[0], hand[1], 1.3, 1.3, FACE_WOOD)
    f.ellipse(x, foot - 19.0, 3.2, 3.4, FACE_WOOD)
    f.dot(x + 1.4, foot - 19.4, 0.5, A.OUTLINE)
    # The hat: a round crown and two short wings at the back.
    f.poly([(x - 3.2, foot - 21.0), (x - 2.6, foot - 25.0), (x + 2.6, foot - 25.0), (x + 3.2, foot - 21.0)], HAT)
    f.limb([(x - 3.6, foot - 22.0), (x - 6.4, foot - 23.0)], 1.4, HAT)


def _mallet(f: K.Frame, hand: Point, head: Point) -> None:
    f.ink([hand, head], 1.0, BOAT_WOOD_DARK)
    f.ellipse(head[0], head[1], 1.6, 1.6, BOAT_WOOD_SHADE)


def _draw_water_clock(anim: str, i: int, n: int):
    w, h = WATER_CLOCK_FRAME
    f = K.Frame(WATER_CLOCK_FRAME)
    ground = h - 6.0
    # The stepped platform of stone on the left. Water runs from the great
    # vessel on the top step down to the smaller vessels, so it comes into
    # the tall receiving vessels at a steady rate.
    steps = ((8.0, 50.0, 104.0), (50.0, 84.0, 142.0), (84.0, 110.0, 178.0))
    for x0, x1, top in steps[::-1]:
        _stone_step(f, x0, x1, top, ground)
    v1 = _jar(f, 29.0, steps[0][2], 19.0, 42.0)
    v2 = _jar(f, 67.0, steps[1][2], 14.0, 28.0)
    v3 = _jar(f, 97.0, steps[2][2], 10.0, 20.0)
    # The pipes from each vessel to the next.
    for (sx, sy), (tx, ty) in ((v1, (67.0, steps[1][2] - 28.0)), (v2, (97.0, steps[2][2] - 20.0)), (v3, (120.0, 112.0))):
        f.limb([(sx, sy), (sx + 4.0, sy), (tx, ty - 4.0), (tx, ty)], 2.6, BRONZE_SHADE)
        f.ink([(sx, sy - 0.8), (sx + 4.0, sy - 0.8), (tx - 0.8, ty - 4.8)], 0.6, BRONZE_LIGHT)
    # The two tall receiving vessels: a float rises in them with the
    # water, and a rod on the float works the striking gear.
    f.poly([(110.0, ground - 12.0), (146.0, ground - 12.0), (146.0, ground), (110.0, ground)], GRANITE)
    f.ink([(111.0, ground - 10.8), (145.0, ground - 10.8)], 0.9, GRANITE_LIGHT)
    f.poly([(138.0, ground - 12.0), (146.0, ground - 12.0), (146.0, ground), (138.0, ground)], GRANITE_SHADE, body=False)
    for cx in (120.0, 136.0):
        top = 112.0
        f.limb([(cx, ground - 12.0), (cx, top - 14.0)], 2.0, BRONZE_DARK)
        f.poly([(cx - 6.5, top), (cx + 6.5, top), (cx + 6.5, ground - 12.0), (cx - 6.5, ground - 12.0)], BRONZE)
        f.poly([(cx + 2.0, top), (cx + 6.5, top), (cx + 6.5, ground - 12.0), (cx + 2.0, ground - 12.0)], BRONZE_SHADE, body=False)
        f.ink([(cx - 4.0, top + 3.0), (cx - 4.0, ground - 15.0)], 1.2, BRONZE_LIGHT)
        for y in (top + 4.0, (top + ground) / 2.0, ground - 16.0):
            f.limb([(cx - 7.0, y), (cx + 7.0, y)], 2.4, BRONZE_DARK)
        f.ellipse(cx, top, 6.9, 1.8, BRONZE)
        f.ellipse(cx, top + 0.2, 5.2, 1.0, BRONZE_DARK, body=False)
    f.limb([(136.0, 98.0), (156.0, 98.0)], 2.0, BRONZE_DARK)
    # The cabinet of the striking gear: a tall case of wood painted in
    # the palace colours, red posts and green panels, under a roof of grey
    # tiles. On top is an open storey where three wooden figures stand.
    k0, k1 = 154.0, 238.0
    kt, kb = 112.0, ground - 6.0
    f.poly([(k0 - 4.0, kb), (k1 + 4.0, kb), (k1 + 4.0, ground), (k0 - 4.0, ground)], GRANITE)
    f.ink([(k0 - 3.0, kb + 1.2), (k1 + 3.0, kb + 1.2)], 0.9, GRANITE_LIGHT)
    f.poly([(k0, kt), (k1, kt), (k1, kb), (k0, kb)], DANCHEONG)
    f.poly([(k1 - 12.0, kt), (k1, kt), (k1, kb), (k1 - 12.0, kb)], DANCHEONG_SHADE, body=False)
    # Panels in two tiers. Each upper panel has a small round window,
    # where a figure of the hour comes out.
    posts = [_lerp(k0 + 2.0, k1 - 2.0, j / 3.0) for j in range(4)]
    for r0, r1 in ((kt + 8.0, kt + 62.0), (kt + 68.0, kb - 6.0)):
        for a, b in zip(posts[:-1], posts[1:]):
            f.poly([(a + 5.0, r0), (b - 5.0, r0), (b - 5.0, r1), (a + 5.0, r1)], K.shade(DANCHEONG, 0.88), body=False)
            f.ink([(a + 5.0, r1), (a + 5.0, r0), (b - 5.0, r0)], 0.8, DANCHEONG_LIGHT)
            if r0 < kt + 20.0:
                f.ellipse((a + b) / 2.0, r0 + 14.0, 5.0, 5.0, INTERIOR, body=False)
                f.limb(_ring((a + b) / 2.0, r0 + 14.0, 5.6, 5.6, 0.0, 360.0, 24), 1.4, GOLD_SHADE, body=False)
    for x in posts:
        f.limb([(x, kt), (x, kb)], 4.0, VERMILION)
        f.ink([(x - 0.9, kt + 1.0), (x - 0.9, kb - 1.0)], 0.8, VERMILION_LIGHT)
    for y in (kt + 2.0, kt + 65.0, kb - 2.0):
        f.limb([(k0, y), (k1, y)], 4.0, VERMILION)
        f.ink([(k0 + 1.0, y - 1.0), (k1 - 1.0, y - 1.0)], 0.7, VERMILION_LIGHT)
    # The open storey on top: a floor, two red posts, and a lintel.
    g0, g1 = k0 - 2.0, k1 + 2.0
    gt, gf = 62.0, kt - 2.0
    f.poly([(g0 + 2.0, gt), (g1 - 2.0, gt), (g1 - 2.0, gf), (g0 + 2.0, gf)], INTERIOR)
    f.poly([(g0 + 2.0, gt), (g1 - 2.0, gt), (g1 - 2.0, gt + 6.0), (g0 + 2.0, gt + 6.0)], K.shade(INTERIOR, 0.8), body=False)
    f.poly([(g0, gf - 4.0), (g1, gf - 4.0), (g1, gf + 2.0), (g0, gf + 2.0)], CABINET)
    f.ink([(g0 + 1.0, gf - 3.0), (g1 - 1.0, gf - 3.0)], 0.9, CABINET_LIGHT)
    for x in (g0 + 2.0, g1 - 2.0):
        f.limb([(x, gt), (x, gf - 4.0)], 3.6, VERMILION)
    f.limb([(g0, gt + 2.0), (g1, gt + 2.0)], 4.6, DANCHEONG)
    for x in range(int(g0 + 4), int(g1 - 2), 6):
        f.ink([(x, gt + 0.6), (x + 3.0, gt + 0.6)], 0.9, VERMILION_LIGHT)
    floor = gf - 4.0
    # Each figure stands to the left of its instrument and strikes it with
    # a mallet. The bell hangs from the lintel; it rings the hours.
    bx = g0 + 21.0
    f.ink([(bx, gt + 4.0), (bx, gt + 12.0)], 1.0, BRONZE_DARK)
    f.poly([(bx - 3.4, gt + 12.0), (bx + 3.4, gt + 12.0), (bx + 5.4, gt + 24.0), (bx - 5.4, gt + 24.0)], BRONZE)
    f.ellipse(bx, gt + 12.0, 3.4, 1.4, BRONZE)
    f.poly([(bx + 1.0, gt + 12.0), (bx + 3.4, gt + 12.0), (bx + 5.4, gt + 24.0), (bx + 1.6, gt + 24.0)], BRONZE_SHADE, body=False)
    f.ink([(bx - 5.0, gt + 21.0), (bx + 5.0, gt + 21.0)], 0.8, BRONZE_DARK)
    hand = (bx - 9.0, floor - 18.0)
    _clock_figure(f, bx - 13.0, floor, ROBE_RED, hand)
    _mallet(f, hand, (bx - 5.4, gt + 19.0))
    # The drum on a low frame: its figure beats the watches of the night.
    dx = g0 + 50.0
    f.limb([(dx - 5.0, floor), (dx - 3.0, floor - 8.0)], 1.6, CABINET_SHADE)
    f.limb([(dx + 5.0, floor), (dx + 3.0, floor - 8.0)], 1.6, CABINET_SHADE)
    f.ellipse(dx, floor - 15.0, 6.4, 8.0, CABINET_LIGHT)
    f.poly([(dx + 1.0, floor - 23.0), (dx + 6.4, floor - 15.0), (dx + 1.0, floor - 7.0)], CABINET, body=False)
    f.ellipse(dx - 5.4, floor - 15.0, 2.0, 7.6, PAPER)
    for dy in (-5.0, 0.0, 5.0):
        f.dot(dx - 3.0, floor - 15.0 + dy, 0.6, GOLD)
    hand2 = (dx - 10.0, floor - 18.0)
    _clock_figure(f, dx - 14.0, floor, ROBE_BLUE, hand2)
    _mallet(f, hand2, (dx - 6.6, floor - 16.0))
    # The gong hangs in a small frame: its figure marks the parts of each
    # watch.
    jx = g1 - 13.0
    f.limb([(jx - 5.0, floor), (jx - 5.0, gt + 10.0), (jx + 5.0, gt + 10.0), (jx + 5.0, floor)], 1.6, CABINET_SHADE)
    f.ink([(jx - 2.0, gt + 10.0), (jx - 1.0, gt + 15.0)], 0.7, BRONZE_DARK)
    f.ink([(jx + 2.0, gt + 10.0), (jx + 1.0, gt + 15.0)], 0.7, BRONZE_DARK)
    f.ellipse(jx, gt + 21.0, 4.8, 5.4, BRONZE)
    f.ellipse(jx + 0.4, gt + 21.4, 2.2, 2.4, BRONZE_LIGHT, body=False)
    f.limb(_ring(jx, gt + 21.0, 4.4, 5.0, -60.0, 100.0, 10), 1.0, BRONZE_SHADE, body=False)
    hand3 = (jx - 10.0, floor - 18.0)
    _clock_figure(f, jx - 14.0, floor, ROBE_GREEN, hand3)
    _mallet(f, hand3, (jx - 5.0, gt + 22.0))
    # The roof of grey tiles, with eaves that curve up at the corners.
    r0, r1 = g0 - 5.0, g1 + 5.0
    ry = gt - 2.0
    f.poly([(r0 - 2.0, ry - 8.0), (r0 + 6.0, ry - 5.0), (r1 - 6.0, ry - 5.0), (r1 + 2.0, ry - 8.0), (r1 - 2.0, ry + 1.0), (r0 + 2.0, ry + 1.0)], ROOF_TILE)
    f.poly([(r0 + 10.0, ry - 5.0), (r1 - 10.0, ry - 5.0), (r1 - 18.0, ry - 22.0), (r0 + 18.0, ry - 22.0)], ROOF_TILE)
    f.poly([(r1 - 30.0, ry - 5.0), (r1 - 10.0, ry - 5.0), (r1 - 18.0, ry - 22.0), (r1 - 34.0, ry - 22.0)], ROOF_TILE_SHADE, body=False)
    for k in range(1, 14):
        x = _lerp(r0 + 12.0, r1 - 12.0, k / 14.0)
        xt = _lerp(r0 + 19.0, r1 - 19.0, k / 14.0)
        f.ink([(x, ry - 5.6), (xt, ry - 21.0)], 0.8, ROOF_TILE_SHADE)
    f.limb([(r0 + 16.0, ry - 23.0), (r1 - 16.0, ry - 23.0)], 4.0, ROOF_TILE_SHADE)
    for x in (r0 + 15.0, r1 - 15.0):
        f.limb([(x, ry - 23.0), (x + (2.0 if x < (r0 + r1) / 2.0 else -2.0), ry - 28.0)], 3.0, ROOF_TILE_SHADE)
    f.ink([(r0 + 2.0, ry - 1.0), (r1 - 2.0, ry - 1.0)], 0.9, ROOF_TILE_LIGHT)
    f.limb([(r0 + 2.0, ry + 1.0), (r1 - 2.0, ry + 1.0)], 2.4, DANCHEONG_SHADE)
    for x in range(int(r0 + 6), int(r1 - 4), 5):
        f.dot(x, ry - 3.0, 0.9, ROOF_TILE_LIGHT)
    return A.finish(f, width=1.4)


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
    "history_lake_boat": LAKE_BOAT_FRAME,
    "history_money_press": MONEY_PRESS_FRAME,
    "history_compass_bowl": COMPASS_BOWL_FRAME,
    "history_byobu_screen": BYOBU_FRAME,
    "history_ox_carriage": OX_CARRIAGE_FRAME,
    "history_rain_gauge": RAIN_GAUGE_FRAME,
    "history_water_clock": WATER_CLOCK_FRAME,
}
DRAW: Dict[str, Callable] = {
    "history_pit_dwelling": _draw_pit_dwelling,
    "history_flame_pot": _draw_flame_pot,
    "history_six_pillars": _draw_six_pillars,
    "history_jade_workshop": _draw_jade_workshop,
    "history_cheomseongdae": _draw_cheomseongdae,
    "history_royal_tumulus": _draw_royal_tumulus,
    "history_gold_crown": _draw_gold_crown,
    "history_lake_boat": _draw_lake_boat,
    "history_money_press": _draw_money_press,
    "history_compass_bowl": _draw_compass_bowl,
    "history_byobu_screen": _draw_byobu_screen,
    "history_ox_carriage": _draw_ox_carriage,
    "history_rain_gauge": _draw_rain_gauge,
    "history_water_clock": _draw_water_clock,
}
DISPLAY = {
    "history_pit_dwelling": "Pit Dwelling",
    "history_flame_pot": "Flame Pot",
    "history_six_pillars": "Six Pillars",
    "history_jade_workshop": "Jade Workshop",
    "history_cheomseongdae": "Cheomseongdae",
    "history_royal_tumulus": "Royal Tumulus",
    "history_gold_crown": "Gold Crown",
    "history_lake_boat": "Lake Boat",
    "history_money_press": "Money Press",
    "history_compass_bowl": "Compass Bowl",
    "history_byobu_screen": "Byobu Screen",
    "history_ox_carriage": "Ox Carriage",
    "history_rain_gauge": "Rain Gauge",
    "history_water_clock": "Water Clock",
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
    "history_lake_boat": "song",
    "history_money_press": "song",
    "history_compass_bowl": "song",
    "history_byobu_screen": "heian",
    "history_ox_carriage": "heian",
    "history_rain_gauge": "joseon",
    "history_water_clock": "joseon",
}
ROWS: Dict[str, List[Tuple[str, int, int]]] = {}


def _foot(name: str) -> Dict[str, Tuple[float, float]]:
    w, h = FRAMES[name]
    return {"foot": (w / 2.0, float(h))}


#: The anchors of each prop. A platform has a "top" anchor at the middle of
#: the surface that a player stands on; the other props have a "foot".
ANCHORS: Dict[str, Dict[str, Tuple[float, float]]] = {name: _foot(name) for name in DISPLAY}
ANCHORS["history_lake_boat"] = {"top": ((LAKE_BOAT_SPAN[0] + LAKE_BOAT_SPAN[1]) / 2.0, LAKE_BOAT_TOP)}
TAGS: Dict[str, List[str]] = {name: ["prop", "scenery", "history", ROOMS[name]] for name in DISPLAY}
TAGS["history_lake_boat"] = ["prop", "platform", "history", ROOMS["history_lake_boat"]]

TARGETS: Dict[str, dict] = {
    name: _publisher(name, DISPLAY[name], ROWS.get(name, STILL), FRAMES[name], DRAW[name], ANCHORS[name], "Scenery", TAGS[name]) for name in DISPLAY
}
