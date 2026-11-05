"""The props of Brazil and Amazonia (the History dimension): Marajó, the
Quilombo dos Palmares and Rio de Janeiro in May 1888.

About 1000 CE the Amazon floodplain was a garden. On Marajó island the
Marajoara built earth mounds (tesos) above the yearly flood, lived on
them, and made pottery painted in red, black and white. The giant leaves
of the Victoria water lily floated on the still water.

From 1605 to 1694 the Quilombo dos Palmares, in the hills of the Serra da
Barriga, was a free state of people who escaped slavery. Thousands lived
in its villages (mocambos), in houses of mud and wattle under palm thatch.
Their smiths knew the ironwork of Central Africa and made the hoes of the
fields.

On 13 May 1888 the "Golden Law" (Lei Áurea) ended slavery in Brazil. It
was signed with a gold pen. Years before, in 1881, the jangadeiros of
Ceará refused to carry enslaved people on their rafts. In Rio, mule-drawn
trams (bondes) ran on rails through the streets.

These props are drawn in the cel style of the dimension's cast
(`targets/characters/_history_americas_kit.py`): flat colour, one shade, a
bold warm outline. They show the skill and the dignity of the people who
made them. No script is drawn: writing is lines of short strokes.

- ``history_victoria_lily``: the look of a platform, a giant leaf of the
  Victoria water lily (Victoria amazonica) seen from the side: a flat
  round leaf with an upturned rim, red-purple outside and green on top, a
  white-and-pink flower beside it, and still water under it. Its top is
  the platform (`VICTORIA_LILY_SPAN` = (30, 190), `VICTORIA_LILY_TOP` =
  34, in a 256 x 64 frame). Its ``idle`` row moves the ripples; the leaf
  stays level.
- ``history_jangada``: the look of a platform, a jangada of Ceará: a flat
  raft of pale lashed logs, a tall triangular white sail on a mast, a
  bench for the mast, a bench for the master, and a steering oar. Its deck
  is the platform (`JANGADA_SPAN` = (22, 362), `JANGADA_TOP` = 156, in a
  384 x 192 frame). Its ``idle`` row fills the sail and moves the
  pennant and the ripples; the deck stays level.
- ``history_marajoara_pots``: scenery, Marajoara painted pottery: a tall
  jar and two bowls painted with red, black and white bands of lines,
  steps and spirals, on a low mound of dark earth (terra preta).
- ``history_teso_house``: scenery, a thatched house on a raised earth
  mound (teso) above the floodwater, with an açaí palm and a dugout
  canoe.
- ``history_mocambo_hut``: scenery, a house of a village of Palmares (a
  mocambo): a wall of mud and wattle, a roof of palm thatch, and a wooden
  mortar and pestle by the door.
- ``history_village_forge``: scenery, a village forge: two bowl bellows
  of hide, a clay hearth with glowing coals, a stone anvil, and iron hoes.
  Its ``idle`` row makes the coals glow and the sparks rise.
- ``history_lei_aurea``: scenery, a writing table with a green cloth, a
  writing slope with a parchment (lines of short strokes and a small
  seal on a ribbon), and a gold pen in an inkstand.
- ``history_bonde``: scenery, a mule-drawn tram car (bonde) of Rio in the
  1880s: open sides, cross benches, a roof on thin posts, a running
  board, on rails, with one mule in harness in front.

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
LOOP: List[Tuple[str, int, int]] = [("idle", 8, 120)]

VICTORIA_LILY_FRAME = (256, 64)
#: The top of the lily leaf is the platform: it is level from x0 to x1 at
#: the height `VICTORIA_LILY_TOP` (frame pixels).
VICTORIA_LILY_SPAN = (30.0, 190.0)
VICTORIA_LILY_TOP = 34.0
JANGADA_FRAME = (384, 192)
#: The deck of the jangada is the platform: it is level from x0 to x1 at
#: the height `JANGADA_TOP` (frame pixels).
JANGADA_SPAN = (22.0, 362.0)
JANGADA_TOP = 156.0
MARAJOARA_POTS_FRAME = (128, 96)
TESO_HOUSE_FRAME = (192, 160)
MOCAMBO_HUT_FRAME = (160, 128)
VILLAGE_FORGE_FRAME = (128, 96)
LEI_AUREA_FRAME = (96, 128)
BONDE_FRAME = (256, 160)

# The Victoria lily and its water.
LILY_GREEN = (98, 150, 62, 255)
LILY_LIGHT = (146, 190, 88, 255)
LILY_SHADE = (66, 114, 46, 255)
LILY_RIM = (150, 52, 82, 255)
LILY_RIM_LIGHT = (192, 88, 112, 255)
LILY_RIM_SHADE = (106, 34, 62, 255)
LILY_RIM_DARK = (76, 26, 48, 255)
PETAL = (250, 246, 238, 255)
PETAL_SHADE = (220, 208, 210, 255)
PETAL_PINK = (232, 128, 164, 255)
PETAL_PINK_DEEP = (196, 76, 122, 255)
STILL_WATER = (46, 92, 96, 215)
STILL_WATER_DEEP = (32, 68, 74, 215)
RIPPLE = (128, 176, 170, 255)

# The jangada.
PIUBA = (214, 186, 136, 255)
PIUBA_LIGHT = (236, 214, 170, 255)
PIUBA_SHADE = (170, 138, 92, 255)
PIUBA_DARK = (128, 100, 66, 255)
HARDWOOD = (120, 80, 50, 255)
HARDWOOD_LIGHT = (160, 112, 72, 255)
SAIL = (246, 242, 230, 255)
SAIL_LIGHT = (255, 253, 246, 255)
SAIL_SHADE = (208, 200, 182, 255)
ROPE = (176, 146, 96, 255)
ROPE_DARK = (110, 88, 58, 255)
SEA_WATER = (48, 120, 150, 200)
SEA_FOAM = (226, 240, 240, 255)
PENNANT = (204, 62, 44, 255)
STRAW = (210, 176, 98, 255)
STRAW_SHADE = (158, 124, 62, 255)

# Marajoara pottery and dark earth.
SLIP = (238, 226, 204, 255)
SLIP_SHADE = (204, 186, 160, 255)
POT_RED = (176, 62, 38, 255)
POT_RED_SHADE = (128, 42, 28, 255)
POT_BLACK = (42, 30, 28, 255)
POT_INSIDE = (120, 52, 34, 255)
DARK_EARTH = (82, 62, 48, 255)
DARK_EARTH_LIGHT = (112, 88, 66, 255)
DARK_EARTH_SHADE = (60, 44, 34, 255)
SHERD = (190, 112, 74, 255)

# The teso, the floodwater, the thatch, the forest.
MOUND = (150, 104, 66, 255)
MOUND_LIGHT = (182, 134, 88, 255)
MOUND_SHADE = (112, 76, 48, 255)
GRASS = (104, 146, 64, 255)
GRASS_SHADE = (70, 108, 46, 255)
FLOOD = (126, 112, 74, 210)
FLOOD_LIGHT = (176, 162, 116, 255)
FLOOD_SHADE = (96, 84, 56, 210)
THATCH = (196, 164, 96, 255)
THATCH_LIGHT = (224, 196, 128, 255)
THATCH_SHADE = (150, 118, 64, 255)
THATCH_DARK = (110, 84, 46, 255)
POLE = (122, 88, 56, 255)
POLE_LIGHT = (158, 118, 76, 255)
POLE_SHADE = (88, 62, 40, 255)
INTERIOR = (52, 38, 30, 255)
HAMMOCK = (206, 120, 70, 255)
HAMMOCK_SHADE = (156, 80, 48, 255)
PALM = (70, 124, 66, 255)
PALM_LIGHT = (108, 160, 86, 255)
PALM_SHADE = (48, 92, 50, 255)
PALM_TRUNK = (120, 104, 82, 255)
ACAI = (70, 40, 74, 255)
CANOE = (78, 50, 34, 255)
CANOE_LIGHT = (136, 94, 60, 255)

# The mocambo and the forge.
CLAY = (176, 122, 78, 255)
CLAY_LIGHT = (204, 154, 106, 255)
CLAY_SHADE = (136, 90, 58, 255)
WATTLE = (120, 92, 60, 255)
WATTLE_LIGHT = (152, 120, 82, 255)
GROUND = (138, 104, 70, 255)
GROUND_SHADE = (106, 78, 52, 255)
HIDE = (170, 128, 86, 255)
HIDE_LIGHT = (200, 160, 116, 255)
HIDE_SHADE = (128, 92, 60, 255)
STONE = (136, 132, 124, 255)
STONE_LIGHT = (172, 168, 158, 255)
STONE_SHADE = (100, 96, 92, 255)
IRON = (74, 72, 78, 255)
IRON_LIGHT = (132, 130, 138, 255)
IRON_SHADE = (54, 52, 58, 255)
COAL = (44, 36, 34, 255)
EMBER = (232, 104, 36, 255)
EMBER_HOT = (255, 200, 90, 255)

# Rio, 1888: the writing table and the tram.
MAHOGANY = (132, 66, 40, 255)
MAHOGANY_LIGHT = (176, 102, 62, 255)
MAHOGANY_SHADE = (94, 46, 30, 255)
BAIZE = (48, 112, 70, 255)
BAIZE_LIGHT = (78, 146, 96, 255)
BAIZE_SHADE = (32, 80, 50, 255)
GOLD = (222, 180, 64, 255)
GOLD_LIGHT = (252, 228, 138, 255)
GOLD_SHADE = (164, 120, 36, 255)
PARCHMENT = (240, 228, 196, 255)
PARCHMENT_SHADE = (212, 194, 154, 255)
WRITING = (60, 46, 40, 255)
SEAL = (176, 36, 40, 255)
SEAL_LIGHT = (218, 82, 74, 255)
INKWELL = (64, 70, 92, 255)
SILVER = (196, 198, 204, 255)
TRAM_GREEN = (52, 108, 72, 255)
TRAM_GREEN_LIGHT = (84, 144, 98, 255)
TRAM_GREEN_SHADE = (34, 76, 50, 255)
TRAM_CREAM = (234, 214, 164, 255)
TRAM_CREAM_SHADE = (196, 172, 120, 255)
BENCH = (156, 98, 56, 255)
BENCH_LIGHT = (192, 132, 84, 255)
BENCH_SHADE = (112, 68, 40, 255)
ROOF = (222, 216, 200, 255)
ROOF_SHADE = (176, 168, 150, 255)
WHEEL = (60, 58, 64, 255)
WHEEL_LIGHT = (122, 120, 128, 255)
RAIL = (150, 152, 160, 255)
COBBLE = (150, 138, 120, 255)
COBBLE_SHADE = (112, 102, 88, 255)
MULE = (124, 100, 82, 255)
MULE_LIGHT = (160, 136, 114, 255)
MULE_SHADE = (90, 70, 58, 255)
MULE_MUZZLE = (196, 178, 156, 255)
HARNESS = (62, 42, 32, 255)
HARNESS_LIGHT = (104, 74, 54, 255)
BRASS = (214, 170, 70, 255)


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


def _lerp(a: float, b: float, u: float) -> float:
    return a + (b - a) * u


def _rect(x0: float, y0: float, x1: float, y1: float) -> List[Point]:
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def _turn(points: Sequence[Point], c: Point, degrees: float) -> List[Point]:
    a = math.radians(degrees)
    ca, sa = math.cos(a), math.sin(a)
    return [(c[0] + (x - c[0]) * ca - (y - c[1]) * sa, c[1] + (x - c[0]) * sa + (y - c[1]) * ca) for x, y in points]


def _writing_line(f: K.Frame, x0: float, x1: float, y: float, rng: random.Random, colour: RGBA, size: float = 1.0) -> None:
    """A line that looks like handwriting, with no real letters: short
    upright strokes in words, and small gaps between the words."""
    x = x0
    while x < x1 - 2.0 * size:
        run = min(x1, x + rng.uniform(3.0, 8.0) * size)
        while x < run:
            tall = rng.random() < 0.25
            f.ink([(x, y + 0.6 * size), (x + 0.5 * size, y - (1.8 if tall else 0.9) * size)], 0.4 * size, colour)
            x += rng.uniform(0.9, 1.4) * size
        x += rng.uniform(1.6, 2.6) * size


def _ripples(f: K.Frame, x0: float, x1: float, y: float, ph: float, colour: RGBA, rows: int, gap: float, seed: str) -> None:
    """Short light lines on water. They slide a little with the phase `ph`
    of the loop, and come back to the start at the end of it."""
    rng = random.Random(seed)
    for r in range(rows):
        yy = y + r * gap
        x = x0 + rng.uniform(0.0, 12.0)
        while x < x1 - 8.0:
            ln = rng.uniform(5.0, 12.0)
            dx = 2.0 * math.sin(2.0 * math.pi * (ph + rng.random()))
            a, b = max(x0, x + dx), min(x1, x + dx + ln)
            if b - a > 2.0:
                f.ink([(a, yy), (b, yy)], 0.8, colour)
            x += ln + rng.uniform(8.0, 18.0)


def _water(f: K.Frame, x0: float, x1: float, y0: float, y1: float, fill: RGBA) -> None:
    """A pool of water: a long flat oval from `x0` to `x1`, `y0` to `y1`.
    Its top is nearly level and its ends are round. It carries no
    outline."""
    cx, hw = (x0 + x1) / 2.0, (x1 - x0) / 2.0
    ym, hh = (y0 + y1) / 2.0, (y1 - y0) / 2.0
    top: List[Point] = []
    bottom: List[Point] = []
    for k in range(49):
        v = -1.0 + 2.0 * k / 48.0
        t = max(0.0, 1.0 - abs(v) ** 5) ** 0.3
        x = cx + v * hw
        top.append((x, ym - hh * t))
        bottom.append((x, ym + hh * t))
    f.poly(top + list(reversed(bottom)), fill, body=False)


def _thatch_rows(f: K.Frame, left: Callable[[float], float], right: Callable[[float], float], y0: float, y1: float, gap: float,
                 rng: random.Random, light: RGBA, dark: RGBA) -> None:
    """The courses of a thatched roof: rows of short hanging strokes from
    `y0` down to `y1`, between the edges `left(y)` and `right(y)`."""
    y = y0
    row = 0
    while y < y1:
        xa, xb = left(y), right(y)
        x = xa + (2.0 if row % 2 else 0.0)
        while x < xb - 1.0:
            ln = rng.uniform(3.0, 5.0)
            f.ink([(x, y), (x + rng.uniform(-0.6, 0.6), y + ln)], 0.6, dark if rng.random() < 0.6 else light)
            x += rng.uniform(2.0, 3.4)
        f.ink([(xa + 1.0, y + gap - 0.6), (xb - 1.0, y + gap - 0.6)], 0.8, dark)
        y += gap
        row += 1


# ---------------------------------------------------------------------------
# The Victoria water lily (a platform).
# ---------------------------------------------------------------------------


def _lily_edge(x: float, near: bool) -> float:
    """The top edge of the rim at `x`. The near edge is level over the
    span and the far edge is level a little higher; at the two tips they
    meet in a round end."""
    top = VICTORIA_LILY_TOP
    cx, half, end, depth = 110.0, 102.0, 22.0, 5.5
    d = abs(x - cx) - (half - end)
    k = 0.0
    if d > 0.0:
        k = 1.0 - math.sqrt(max(0.0, 1.0 - (min(d, end) / end) ** 2))
    if near:
        return top - depth * k
    return top - 2.0 * depth + depth * k


def _petal(base: Point, angle: float, length: float, width: float) -> List[Point]:
    """A petal (or a sepal) from `base`: narrow at the base, widest past
    its middle, with a round tip. `angle` is in degrees (0 is to the
    right, -90 is up)."""
    a = math.radians(angle)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    side_a: List[Point] = []
    side_b: List[Point] = []
    for k in range(13):
        t = k / 12.0
        hw = width * math.sin(math.pi * min(1.0, t * 0.92 + 0.04)) ** 0.7 * (0.55 + 0.45 * t)
        px, py = base[0] + ux * length * t, base[1] + uy * length * t
        side_a.append((px + nx * hw, py + ny * hw))
        side_b.append((px - nx * hw, py - ny * hw))
    return side_a + list(reversed(side_b))


def _lily_flower(f: K.Frame, cx: float, cy: float) -> None:
    """The flower of the Victoria lily: an open cup of white petals, the
    inner petals pink, on red-purple sepals just above the water."""
    base = (cx, cy + 4.0)
    # The sepals: two red-purple points that spread out under the cup.
    for a in (168.0, 12.0):
        f.poly(_petal((cx, cy + 6.0), a, 13.0, 3.6), LILY_RIM)
    f.ellipse(cx, cy + 6.5, 7.0, 3.0, LILY_RIM_SHADE)
    # The back petals, in shade, and the outer petals that open wide.
    for a in (-148.0, -126.0, -54.0, -32.0):
        f.poly(_petal(base, a, 19.0, 4.0), PETAL_SHADE)
    for a in (-172.0, -158.0, -22.0, -8.0):
        f.poly(_petal(base, a, 17.0, 4.0), PETAL)
        tip = _petal(base, a, 13.0, 0.0)[12]
        f.ink([base, tip], 0.5, PETAL_SHADE)
    # The inner petals stand up, white with pink bases, round a deep pink
    # heart.
    for a in (-116.0, -64.0):
        f.poly(_petal(base, a, 18.0, 4.0), PETAL)
        f.poly(_petal(base, a, 11.0, 2.8), PETAL_PINK, body=False)
    for a in (-100.0, -80.0):
        f.poly(_petal(base, a, 15.0, 3.6), PETAL_PINK)
        f.poly(_petal(base, a + 6.0, 11.0, 1.6), PETAL_PINK_DEEP, body=False)
    f.poly(_petal(base, -90.0, 12.0, 3.4), PETAL_PINK_DEEP)
    f.ink([(cx - 0.8, cy + 2.0), (cx - 0.8, cy - 5.0)], 0.6, (246, 184, 206, 255))


def _draw_victoria_lily(anim: str, i: int, n: int):
    w, h = VICTORIA_LILY_FRAME
    f = K.Frame(VICTORIA_LILY_FRAME)
    rng = random.Random("history_victoria_lily")
    ph = i / float(max(1, n))
    top = VICTORIA_LILY_TOP
    rim = 7.0
    xs = [8.0 + 204.0 * k / 100.0 for k in range(101)]
    # The still water under the leaf and the flower. It has no outline.
    _water(f, 4.0, w - 4.0, top + 5.0, h - 6.0, STILL_WATER)
    _water(f, 40.0, w - 40.0, top + 11.0, h - 8.0, STILL_WATER_DEEP)
    # The flower stands in the water beside the leaf.
    _lily_flower(f, 233.0, 27.0)
    # The reflection of the red rim, broken by the ripples.
    for k in range(9):
        x = 26.0 + k * 20.0 + 2.0 * math.sin(2.0 * math.pi * (ph + k * 0.31))
        f.ink([(x, top + rim + 3.0), (x + 12.0, top + rim + 3.0)], 1.2, K.alpha(LILY_RIM, 0.6))
    _ripples(f, 22.0, w - 22.0, top + rim + 8.0, ph, RIPPLE, 2, 6.0, "history_victoria_lily ripples")
    # The leaf: a flat round leaf seen nearly edge on. Its green top shows
    # over the near rim. The far rim shows its inner face, a darker green
    # with a red lip.
    surface = [(x, _lily_edge(x, False)) for x in xs] + [(x, _lily_edge(x, True)) for x in reversed(xs)]
    f.poly(surface, LILY_GREEN)
    f.poly([(x, _lily_edge(x, False)) for x in xs] + [(x, _lily_edge(x, False) + 3.0) for x in reversed(xs[4:-4])], LILY_SHADE, body=False)
    f.ink([(x, _lily_edge(x, False) + 0.4) for x in xs[1:-1]], 1.0, LILY_RIM)
    # The ribs of the leaf run out from its middle to the rim, and a light
    # sheen lies on the near half.
    hub = (110.0, top - 3.0)
    for k in range(-11, 12):
        x = 110.0 + k * 8.4
        f.ink([hub, (x, top - 7.4)], 0.7 if k % 2 else 0.5, LILY_SHADE)
    for rx, ry in ((40.0, 2.0), (72.0, 3.4)):
        f.ink(_ring(hub[0], hub[1] + 0.4, rx, ry, 190.0, 350.0, 20), 0.5, LILY_SHADE)
    f.ink([(36.0, top - 1.4), (96.0, top - 1.4)], 1.0, LILY_LIGHT)
    f.ink([(124.0, top - 1.4), (184.0, top - 1.4)], 1.0, LILY_LIGHT)
    # The near rim: it turns up round the leaf. Its outside is red-purple,
    # with creases where it folds.
    def under(x: float) -> float:
        return top + rim - (top - _lily_edge(x, True)) * 1.5

    band = [(x, _lily_edge(x, True)) for x in xs] + [(x, under(x)) for x in reversed(xs)]
    f.poly(band, LILY_RIM)
    f.poly([(x, _lily_edge(x, True) + rim * 0.6) for x in xs[3:-3]] + [(x, under(x)) for x in reversed(xs[3:-3])], LILY_RIM_SHADE, body=False)
    f.ink([(x, _lily_edge(x, True) + 1.0) for x in xs[2:-2]], 1.0, LILY_RIM_LIGHT)
    for x in xs[3:-3:3]:
        f.ink([(x, _lily_edge(x, True) + 2.4), (x + rng.uniform(-0.6, 0.6), under(x) - 0.6)], 0.6, LILY_RIM_DARK)
    return A.finish(f, width=1.3)


# ---------------------------------------------------------------------------
# The jangada (a platform).
# ---------------------------------------------------------------------------


def _draw_jangada(anim: str, i: int, n: int):
    w, h = JANGADA_FRAME
    f = K.Frame(JANGADA_FRAME)
    rng = random.Random("history_jangada")
    ph = i / float(max(1, n))
    top = JANGADA_TOP
    x0, x1 = 14.0, 372.0
    # The sea at the waterline. It has no outline.
    _water(f, 4.0, w - 4.0, top + 9.0, top + 28.0, SEA_WATER)
    _ripples(f, 18.0, w - 18.0, top + 19.0, ph, SEA_FOAM, 2, 5.0, "history_jangada ripples")
    # The steering oar: its loom rests in a rope on a post at the stern,
    # and its blade goes down into the sea.
    f.limb([(46.0, top), (44.0, top - 22.0)], 3.0, HARDWOOD)
    f.limb([(62.0, top - 30.0), (12.0, top + 22.0)], 3.4, HARDWOOD_LIGHT)
    f.poly([(20.0, top + 10.0), (14.0, top + 8.0), (6.0, top + 22.0), (10.0, top + 28.0), (18.0, top + 22.0)], HARDWOOD_LIGHT)
    f.limb([(40.0, top - 22.0), (50.0, top - 22.0)], 1.8, ROPE_DARK)
    # The mast, raked a little aft, and the sail. The mast passes through
    # the mast bench and stands in a step on the deck.
    foot = (268.0, top)
    head = (258.0, 12.0)
    tack = _mix(foot, head, 0.22)
    clew = (112.0, tack[1] - 4.0)
    fill = 0.5 + 0.5 * math.sin(2.0 * math.pi * ph)
    bulge = 15.0 + 4.0 * fill
    # The leech: a convex curve from the head of the sail to its clew.
    leech: List[Point] = []
    for k in range(25):
        u = k / 24.0
        p = _mix(head, clew, u)
        dx, dy = clew[0] - head[0], clew[1] - head[1]
        ln = math.hypot(dx, dy)
        nx, ny = dy / ln, -dx / ln
        b = bulge * math.sin(math.pi * u) * (1.0 - 0.25 * u)
        leech.append((p[0] - nx * b, p[1] - ny * b))
    luff = [_mix(tack, head, k / 12.0) for k in range(13)]
    f.poly(luff + leech[1:], SAIL)
    # The shade of the belly of the sail, behind the luff.
    f.poly([_mix(tack, head, k / 12.0) for k in range(11)] + [_mix(_mix(tack, head, k / 12.0), _mix(clew, head, k / 12.0), 0.1 + 0.04 * fill) for k in reversed(range(11))],
           K.alpha(SAIL_SHADE, 0.75), body=False)
    f.ink([(p[0] + 1.6, p[1] + 1.0) for p in leech[2:-3]], 1.2, SAIL_LIGHT)
    # The seams of the cloths run from the foot of the sail to its head.
    for k in range(1, 7):
        p = _mix(tack, clew, k / 7.0)
        f.ink([p, _mix(p, head, 0.86 - 0.02 * k)], 0.6, SAIL_SHADE)
    f.ink(leech, 0.9, SAIL_SHADE)
    # The boom along the foot of the sail, and the sheet down to the stern.
    f.limb([(tack[0] + 2.0, tack[1]), (clew[0] - 4.0, clew[1])], 3.0, HARDWOOD)
    f.ink([(clew[0] + 2.0, clew[1] + 1.0), (60.0, top - 30.0)], 0.9, ROPE_DARK)
    f.limb([foot, head], 4.2, HARDWOOD_LIGHT)
    f.ink([(foot[0] - 1.2, foot[1] - 2.0), (head[0] - 1.2, head[1] + 3.0)], 1.0, PIUBA_LIGHT)
    for k in range(6):
        p = _mix(tack, head, (k + 0.5) / 6.0)
        f.ink([(p[0] - 2.0, p[1]), (p[0] + 2.0, p[1])], 1.0, ROPE_DARK)
    # The pennant at the masthead shows the wind.
    fl = 3.0 * math.sin(2.0 * math.pi * ph)
    f.poly([(head[0], head[1] - 2.0), (head[0] - 18.0, head[1] + 1.0 + fl), (head[0] - 26.0, head[1] + 4.0 - fl * 0.5),
            (head[0] - 16.0, head[1] + 5.0 + fl), (head[0], head[1] + 4.0)], PENNANT)
    f.ellipse(head[0], head[1] - 1.0, 2.6, 2.6, HARDWOOD)
    # The mast bench: a plank across the raft on two legs; the mast passes
    # through it.
    for x in (252.0, 282.0):
        f.limb([(x, top), (x, top - 15.0)], 3.0, HARDWOOD)
    f.poly(_rect(246.0, top - 19.0, 288.0, top - 14.0), HARDWOOD_LIGHT)
    f.ink([(247.0, top - 18.2), (287.0, top - 18.2)], 0.8, PIUBA_LIGHT)
    # The bench of the master at the stern, where he sits and steers.
    for x in (74.0, 96.0):
        f.limb([(x, top), (x, top - 11.0)], 2.6, HARDWOOD)
    f.poly(_rect(68.0, top - 14.0, 102.0, top - 10.0), HARDWOOD_LIGHT)
    f.ink([(69.0, top - 13.3), (101.0, top - 13.3)], 0.8, PIUBA_LIGHT)
    # A basket of straw for the catch, lashed by the mast.
    f.poly([(300.0, top), (298.0, top - 12.0), (302.0, top - 15.0), (318.0, top - 15.0), (322.0, top - 12.0), (320.0, top)], STRAW)
    for y in (top - 11.0, top - 7.0, top - 3.0):
        f.ink([(299.5, y), (320.5, y)], 0.6, STRAW_SHADE)
    f.ellipse(310.0, top - 15.0, 10.0, 2.0, STRAW_SHADE, body=False)
    # The raft: the longer middle logs show at the bow and the stern, and
    # the near log runs along the side. Its top is the deck, and the deck
    # is the platform.
    f.poly([(x0 + 6.0, top), (x1 - 4.0, top), (x1 + 2.0, top + 4.0), (x1 - 2.0, top + 9.0), (x0 + 4.0, top + 9.0), (x0, top + 4.0)], PIUBA_SHADE)
    f.ink([(x0 + 4.0, top + 4.0), (x1 - 2.0, top + 4.0)], 0.6, PIUBA_DARK)
    nx0, nx1 = 34.0, 352.0
    f.poly([(nx0 + 6.0, top), (nx1 - 6.0, top), (nx1, top + 5.0), (nx1 - 6.0, top + 13.0), (nx0 + 6.0, top + 13.0), (nx0, top + 7.0)], PIUBA)
    f.poly([(nx0 + 4.0, top + 8.0), (nx1 - 3.0, top + 8.0), (nx1 - 6.0, top + 13.0), (nx0 + 6.0, top + 13.0)], PIUBA_SHADE, body=False)
    f.ink([(nx0 + 6.0, top + 1.6), (nx1 - 6.0, top + 1.6)], 1.0, PIUBA_LIGHT)
    # The grain of the logs, and a few knots.
    for _ in range(26):
        x = rng.uniform(nx0 + 10.0, nx1 - 30.0)
        y = rng.uniform(top + 3.0, top + 10.0)
        f.ink([(x, y), (x + rng.uniform(10.0, 24.0), y + rng.uniform(-0.4, 0.4))], 0.5, PIUBA_DARK)
    for x in (88.0, 196.0, 318.0):
        f.ellipse(x, top + 6.0, 1.8, 1.2, PIUBA_DARK, body=False)
    # The logs are held by pegs of hardwood driven through them, and lashed
    # with rope at the ends.
    for x in range(54, 340, 36):
        f.ellipse(float(x), top + 6.5, 1.6, 1.6, HARDWOOD)
        f.dot(float(x) - 0.5, top + 6.0, 0.5, HARDWOOD_LIGHT)
    for x in (nx0 + 10.0, nx1 - 12.0):
        for k in range(3):
            f.ink([(x + k * 2.4, top + 0.4), (x + k * 2.4 + 1.2, top + 12.6)], 1.2, ROPE_DARK)
    # Foam where the sea washes on the logs.
    for k in range(7):
        x = 40.0 + k * 46.0 + 3.0 * math.sin(2.0 * math.pi * (ph + k * 0.4))
        f.ink([(x, top + 13.0), (x + 14.0, top + 13.4)], 1.2, SEA_FOAM)
    return A.finish(f, width=1.4)


# ---------------------------------------------------------------------------
# Marajoara pottery.
# ---------------------------------------------------------------------------


def _profile_pot(f: K.Frame, cx: float, profile: Sequence[Tuple[float, float]], fill: RGBA) -> List[Point]:
    """A pot turned on its axis at `cx`: `profile` is a list of (y, radius)
    from the rim down to the foot. Returns the outline."""
    right = [(cx + r, y) for y, r in profile]
    left = [(cx - r, y) for y, r in reversed(profile)]
    out = right + left
    f.poly(out, fill)
    return out


def _radius_at(profile: Sequence[Tuple[float, float]], y: float) -> float:
    for (ya, ra), (yb, rb) in zip(profile, profile[1:]):
        if ya <= y <= yb:
            return _lerp(ra, rb, (y - ya) / max(1e-6, yb - ya))
    return profile[-1][1]


def _band(f: K.Frame, cx: float, profile, y0: float, y1: float, colour: RGBA, inset: float = 0.6) -> None:
    """A painted band round a pot from `y0` to `y1`."""
    ys = [_lerp(y0, y1, k / 6.0) for k in range(7)]
    f.poly([(cx + _radius_at(profile, y) - inset, y) for y in ys] + [(cx - _radius_at(profile, y) + inset, y) for y in reversed(ys)], colour, body=False)


def _steps(f: K.Frame, x0: float, x1: float, y0: float, y1: float, colour: RGBA, step: float, width: float) -> None:
    """A band of stepped lines, like a stair that goes up and down."""
    pts: List[Point] = []
    x = x0
    up = True
    levels = 3
    dy = (y1 - y0) / levels
    lv = 0
    while x < x1:
        y = y1 - lv * dy
        pts.append((x, y))
        x = min(x1, x + step)
        pts.append((x, y))
        lv += 1 if up else -1
        if lv >= levels:
            up = False
        if lv <= 0:
            up = True
    f.ink(pts, width, colour)


def _spiral(f: K.Frame, cx: float, cy: float, r: float, colour: RGBA, width: float, turns: float = 1.6, flip: float = 1.0) -> None:
    pts = []
    count = 28
    for k in range(count + 1):
        u = k / float(count)
        a = flip * 2.0 * math.pi * turns * u
        rr = r * (1.0 - u * 0.85)
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr * 0.9))
    f.ink(pts, width, colour)


def _draw_marajoara_pots(anim: str, i: int, n: int):
    w, h = MARAJOARA_POTS_FRAME
    f = K.Frame(MARAJOARA_POTS_FRAME)
    rng = random.Random("history_marajoara_pots")
    ground = h - 5.0
    # The low mound of dark earth, with bits of old pottery in it.
    mound = [(4.0, ground)] + [(x, ground - 12.0 * math.sin(math.pi * (x - 4.0) / 120.0) ** 0.7) for x in [4.0 + 120.0 * k / 24.0 for k in range(1, 24)]] + [(124.0, ground)]
    f.poly(mound, DARK_EARTH)
    f.poly([(10.0, ground)] + [(x, ground - 5.0 * math.sin(math.pi * (x - 10.0) / 108.0) ** 0.7) for x in [10.0 + 108.0 * k / 18.0 for k in range(1, 18)]] + [(118.0, ground)],
           DARK_EARTH_SHADE, body=False)
    for _ in range(14):
        x = rng.uniform(14.0, 114.0)
        y = ground - rng.uniform(1.5, 9.0 * math.sin(math.pi * (x - 4.0) / 120.0) ** 0.7)
        f.poly([(x, y), (x + 2.4, y - 0.8), (x + 3.0, y + 0.8), (x + 0.6, y + 1.2)], SHERD if rng.random() < 0.6 else DARK_EARTH_LIGHT, body=False)
    # The tall jar: a wide body, a narrow neck and a flared rim. It is
    # painted white, with bands of red and of black lines.
    jx = 50.0
    jar = [(12.0, 13.0), (15.0, 11.5), (22.0, 9.5), (28.0, 11.0), (36.0, 17.0), (46.0, 21.0), (56.0, 21.5), (66.0, 18.0), (74.0, 12.0), (79.0, 8.0), (82.0, 8.5)]
    _profile_pot(f, jx, jar, SLIP)
    _band(f, jx, jar, 12.0, 15.5, POT_RED)
    _band(f, jx, jar, 30.0, 33.0, POT_RED)
    _band(f, jx, jar, 60.0, 64.0, POT_RED)
    _band(f, jx, jar, 72.0, 82.0, POT_RED_SHADE)
    # The shade on the right side of the jar.
    ys = [_lerp(14.0, 80.0, k / 20.0) for k in range(21)]
    f.poly([(jx + _radius_at(jar, y) * 0.55, y) for y in ys] + [(jx + _radius_at(jar, y) - 0.6, y) for y in reversed(ys)], K.alpha(POT_RED_SHADE, 0.28), body=False)
    # The neck: a band of steps in black.
    _steps(f, jx - 8.0, jx + 8.0, 18.0, 26.0, POT_BLACK, 2.4, 0.9)
    # The body: a broad band of spirals, held between black lines.
    for y in (36.0, 54.0):
        r = _radius_at(jar, y) - 1.0
        f.ink([(jx - r, y), (jx + r, y)], 1.0, POT_BLACK)
    for k, x in enumerate((-12.0, 0.0, 12.0)):
        _spiral(f, jx + x, 45.0, 5.2, POT_BLACK, 1.0, flip=1.0 if k % 2 else -1.0)
    for x in (-6.0, 6.0):
        f.poly([(jx + x - 2.0, 45.0), (jx + x, 41.0), (jx + x + 2.0, 45.0), (jx + x, 49.0)], POT_RED, body=False)
    # The lower body: a red band with a white zigzag.
    zig = [(jx - 16.0 + k * 4.0, 61.0 + (1.6 if k % 2 else -1.6)) for k in range(9)]
    f.ink(zig, 0.8, SLIP)
    f.ink([(jx - 9.0, 13.2), (jx + 9.0, 13.2)], 0.7, SLIP_SHADE)
    f.ellipse(jx, 12.0, 13.0, 2.0, POT_INSIDE, body=False)
    # The wide bowl at the right: it shows its red inside, and a band of
    # steps and lines outside.
    bx, by = 98.0, 66.0
    bowl = [(by, 22.0), (by + 2.0, 22.0), (by + 8.0, 19.0), (by + 13.0, 13.0), (by + 16.0, 7.0), (by + 17.0, 7.5)]
    _profile_pot(f, bx, bowl, SLIP)
    f.ellipse(bx, by, 22.0, 3.6, SLIP)
    f.ellipse(bx, by + 0.4, 19.6, 2.6, POT_INSIDE, body=False)
    _band(f, bx, bowl, by + 1.0, by + 3.4, POT_RED)
    _steps(f, bx - 16.0, bx + 16.0, by + 5.0, by + 10.0, POT_BLACK, 2.6, 0.9)
    _band(f, bx, bowl, by + 12.0, by + 17.0, POT_RED_SHADE)
    for x in (-8.0, 8.0):
        _spiral(f, bx + x, by + 14.2, 2.2, SLIP, 0.6, 1.2)
    # The small bowl at the left, painted with black lines on red.
    sx, sy = 18.0, 72.0
    small = [(sy, 11.0), (sy + 1.4, 11.0), (sy + 6.0, 9.4), (sy + 10.0, 5.0), (sy + 11.0, 5.0)]
    _profile_pot(f, sx, small, POT_RED)
    f.ellipse(sx, sy, 11.0, 2.2, POT_RED)
    f.ellipse(sx, sy + 0.3, 9.4, 1.4, POT_INSIDE, body=False)
    _band(f, sx, small, sy + 1.0, sy + 3.0, SLIP)
    for k in range(5):
        x = sx - 7.0 + k * 3.5
        f.ink([(x, sy + 4.0), (x + 1.0, sy + 8.0)], 0.7, POT_BLACK)
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# The house on the teso.
# ---------------------------------------------------------------------------


def _palm_frond(f: K.Frame, base: Point, angle: float, length: float, droop: float, colour: RGBA, shade: RGBA) -> None:
    """A palm frond: a curved rib with thin leaflets that hang from it."""
    pts: List[Point] = []
    for k in range(9):
        u = k / 8.0
        a = math.radians(angle) + droop * u * u * (1.0 if math.cos(math.radians(angle)) >= 0 else -1.0)
        pts.append((base[0] + math.cos(a) * length * u, base[1] + math.sin(a) * length * u + droop * 10.0 * u * u))
    f.limb(pts, 1.4, shade)
    for k in range(2, 9):
        p = pts[k]
        ln = 6.0 * (1.0 - 0.4 * k / 8.0)
        f.limb([p, (p[0] - 1.5, p[1] + ln)], 1.4, colour)
        f.limb([p, (p[0] + 1.5, p[1] + ln)], 1.4, colour)


def _draw_teso_house(anim: str, i: int, n: int):
    w, h = TESO_HOUSE_FRAME
    f = K.Frame(TESO_HOUSE_FRAME)
    rng = random.Random("history_teso_house")
    water = 132.0
    # The açaí palm behind the house: a thin trunk, a crown of fronds, and
    # bunches of dark purple fruit.
    px = 166.0
    f.limb([(px, water + 2.0), (px - 2.0, 80.0), (px - 4.0, 34.0)], 3.0, PALM_TRUNK)
    for y in range(40, 130, 6):
        f.ink([(px - 4.0 + (y - 34.0) * 0.03 - 1.4, float(y)), (px - 4.0 + (y - 34.0) * 0.03 + 1.6, float(y))], 0.6, POLE_SHADE)
    crown = (px - 4.0, 32.0)
    for a, ln, d in ((-170.0, 18.0, 0.5), (-140.0, 18.0, 0.3), (-100.0, 16.0, 0.1), (-60.0, 16.0, 0.2), (-25.0, 15.0, 0.4), (-5.0, 13.0, 0.6), (200.0, 16.0, 0.4)):
        _palm_frond(f, crown, a, ln, d, PALM if a < -90.0 else PALM_LIGHT, PALM_SHADE)
    for dx in (-3.0, 2.0):
        f.limb([(crown[0] + dx, crown[1] + 4.0), (crown[0] + dx * 2.0, crown[1] + 12.0)], 1.0, PALM_SHADE)
        for k in range(5):
            f.dot(crown[0] + dx * 2.0 + rng.uniform(-2.0, 2.0), crown[1] + 10.0 + k * 1.6, 1.3, ACAI)
    # The teso: a broad mound of earth, built up above the flood. Its top
    # is level and grassy, and its sides show the layers of earth.
    mcx, mhw, mtop, mfoot = 98.0, 84.0, 97.0, water + 6.0

    def mound_y(x: float, lift: float = 0.0) -> float:
        v = min(1.0, abs(x - mcx) / mhw)
        return mfoot - (mfoot - mtop - lift) * max(0.0, 1.0 - v ** 3.2) ** 0.55

    mxs = [mcx - mhw + 2.0 * mhw * k / 40.0 for k in range(41)]
    f.poly([(x, mound_y(x)) for x in mxs], MOUND)
    # The lower slope is in shade; soft streaks show the layers of earth.
    f.poly([(x, max(mound_y(x), mound_y(x, -14.0))) for x in mxs], MOUND_SHADE, body=False)
    for k in range(16):
        x = rng.uniform(mcx - mhw * 0.7, mcx + mhw * 0.7)
        y = mound_y(x) + rng.uniform(5.0, mfoot - mound_y(x) - 4.0) if mfoot - mound_y(x) > 10.0 else mound_y(x) + 3.0
        f.ink([(x, y), (x + rng.uniform(5.0, 10.0), y + rng.uniform(-0.4, 0.4))], 0.7, MOUND_LIGHT if y < 116.0 else MOUND)
    # The grassy top of the mound.
    gx = [x for x in mxs if abs(x - mcx) < mhw * 0.8]
    f.poly([(x, mound_y(x) - 0.6) for x in gx] + [(x, mound_y(x) + 3.0) for x in reversed(gx)], GRASS_SHADE, body=False)
    f.ink([(x, mound_y(x) - 0.2) for x in gx], 1.0, GRASS)
    for k in range(26):
        x = gx[0] + 2.0 + k * (gx[-1] - gx[0] - 4.0) / 25.0 + rng.uniform(-1.0, 1.0)
        f.ink([(x, mound_y(x) + 0.6), (x + rng.uniform(-1.4, 1.4), mound_y(x) - 3.4)], 0.9, GRASS if k % 2 else GRASS_SHADE)
    # The house: a frame of poles, low walls of palm leaf, a dark doorway
    # with a hammock inside, and a tall roof of thatch.
    hx0, hx1 = 64.0, 136.0
    floor = 97.0
    f.poly(_rect(hx0, 70.0, hx1, floor), THATCH_SHADE)
    for x in range(int(hx0) + 2, int(hx1), 3):
        f.ink([(float(x), 71.0), (float(x) + 0.4, floor - 1.0)], 0.6, THATCH_DARK)
    dx0, dx1 = 88.0, 112.0
    f.poly(_rect(dx0, 72.0, dx1, floor), INTERIOR, body=False)
    sling = [(dx0 + 1.0, 80.0)] + [(_lerp(dx0 + 3.0, dx1 - 3.0, u), 83.0 + 6.0 * math.sin(math.pi * u)) for u in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)] + [(dx1 - 1.0, 80.0)]
    sling += [(_lerp(dx1 - 3.0, dx0 + 3.0, u), 86.0 + 6.0 * math.sin(math.pi * u)) for u in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)]
    f.poly(sling, HAMMOCK, body=False)
    f.ink([(_lerp(dx0 + 3.0, dx1 - 3.0, u), 87.6 + 6.0 * math.sin(math.pi * u)) for u in (0.0, 0.25, 0.5, 0.75, 1.0)], 1.0, HAMMOCK_SHADE)
    for u in (0.3, 0.5, 0.7):
        x = _lerp(dx0 + 3.0, dx1 - 3.0, u)
        f.ink([(x, 83.4 + 6.0 * math.sin(math.pi * u)), (x, 87.6 + 6.0 * math.sin(math.pi * u))], 0.6, HAMMOCK_SHADE)
    for x in (hx0, dx0, dx1, hx1):
        f.limb([(x, floor), (x, 68.0)], 2.6, POLE)
        f.ink([(x - 0.6, floor - 1.0), (x - 0.6, 69.0)], 0.6, POLE_LIGHT)
    # The roof: a steep hip of palm thatch to the ground of the eaves, with
    # a ridge bundle on top.
    ex0, ex1, eave = 52.0, 148.0, 74.0
    rx0, rx1, ridge = 84.0, 116.0, 18.0
    roof = [(rx0, ridge), (rx1, ridge), (ex1, eave), (ex1 - 3.0, eave + 3.0), (ex0 + 3.0, eave + 3.0), (ex0, eave)]
    f.poly(roof, THATCH)
    f.poly([(rx1 - 6.0, ridge), (rx1, ridge), (ex1, eave), (ex1 - 3.0, eave + 3.0), (ex1 - 22.0, eave + 3.0)], THATCH_SHADE, body=False)

    def left(y: float) -> float:
        return _lerp(rx0, ex0, (y - ridge) / (eave - ridge)) + 1.0

    def right(y: float) -> float:
        return _lerp(rx1, ex1, (y - ridge) / (eave - ridge)) - 1.0

    _thatch_rows(f, left, right, ridge + 3.0, eave, 7.0, rng, THATCH_LIGHT, THATCH_DARK)
    for k in range(32):
        x = ex0 + 3.0 + k * (ex1 - ex0 - 6.0) / 31.0
        f.ink([(x, eave + 1.0), (x + rng.uniform(-0.6, 0.6), eave + 3.0 + rng.uniform(0.0, 2.0))], 0.8, THATCH_DARK)
    f.limb([(rx0 - 3.0, ridge), (rx1 + 3.0, ridge)], 4.0, THATCH_DARK)
    for x in (rx0 + 4.0, 100.0, rx1 - 4.0):
        f.ink([(x, ridge - 2.0), (x, ridge + 2.0)], 1.0, POLE_SHADE)
    # A painted pot by the door.
    f.ellipse(122.0, floor - 5.0, 6.0, 5.0, SLIP)
    f.ink([(116.4, floor - 6.0), (127.6, floor - 6.0)], 1.2, POT_RED)
    f.ink([(117.0, floor - 3.4), (127.0, floor - 3.4)], 0.7, POT_BLACK)
    f.ellipse(122.0, floor - 9.6, 3.4, 1.2, POT_INSIDE)
    # The floodwater round the foot of the mound. It has no outline.
    _water(f, 4.0, w - 4.0, water - 2.0, h - 6.0, FLOOD)
    _ripples(f, 14.0, w - 14.0, water + 6.0, 0.0, FLOOD_LIGHT, 3, 5.0, "history_teso_house ripples")
    f.ink([(x, water - 0.4) for x in mxs if abs(x - mcx) < mhw - 6.0], 1.0, FLOOD_LIGHT)
    # A dugout canoe at the foot of the mound, with its paddle laid in it.
    cy = water + 7.0
    hull = [(10.0, cy - 7.0), (16.0, cy - 3.0), (50.0, cy - 3.0), (58.0, cy - 7.0), (56.0, cy), (48.0, cy + 4.0), (18.0, cy + 4.0), (12.0, cy)]
    f.poly(hull, CANOE)
    f.poly([(12.0, cy), (56.0, cy), (48.0, cy + 4.0), (18.0, cy + 4.0)], POLE_SHADE, body=False)
    f.ink([(16.0, cy - 2.4), (50.0, cy - 2.4)], 1.0, CANOE_LIGHT)
    f.limb([(20.0, cy - 9.0), (42.0, cy - 4.0)], 1.6, POLE_LIGHT)
    f.poly(_turn([(42.0, cy - 6.0), (50.0, cy - 6.0), (50.0, cy - 2.0), (42.0, cy - 2.0)], (42.0, cy - 4.0), 12.0), POLE_LIGHT)
    f.ink(hull + [hull[0]], 1.2, A.OUTLINE)
    return A.finish(f, width=1.3)


# ---------------------------------------------------------------------------
# The mocambo hut.
# ---------------------------------------------------------------------------


def _draw_mocambo_hut(anim: str, i: int, n: int):
    w, h = MOCAMBO_HUT_FRAME
    f = K.Frame(MOCAMBO_HUT_FRAME)
    rng = random.Random("history_mocambo_hut")
    ground = h - 5.0
    # A strip of beaten ground.
    f.poly([(6.0, ground - 3.0), (w - 6.0, ground - 3.0), (w - 4.0, ground), (4.0, ground)], GROUND)
    # The wall: mud pressed into a lattice of sticks (wattle). Where the
    # mud has fallen away, the lattice shows.
    wx0, wx1, wy = 30.0, 124.0, 66.0
    f.poly(_rect(wx0, wy, wx1, ground - 2.0), CLAY)
    f.poly(_rect(wx0, ground - 14.0, wx1, ground - 2.0), CLAY_SHADE, body=False)
    for _ in range(40):
        x = rng.uniform(wx0 + 3.0, wx1 - 6.0)
        y = rng.uniform(wy + 8.0, ground - 6.0)
        f.ink([(x, y), (x + rng.uniform(2.0, 5.0), y + rng.uniform(-0.5, 0.5))], 0.6, CLAY_LIGHT if rng.random() < 0.5 else CLAY_SHADE)
    for (px0, py0, px1, py1) in ((38.0, 80.0, 52.0, 94.0), (106.0, 92.0, 118.0, 104.0)):
        patch = [(px0, py0 + 2.0), (px0 + 4.0, py0), (px1, py0 + 1.0), (px1 + 1.0, py1 - 3.0), (px1 - 3.0, py1), (px0 + 1.0, py1 - 1.0)]
        f.poly(patch, CLAY_SHADE, body=False)
        for x in range(int(px0) + 2, int(px1), 3):
            f.ink([(float(x), py0 + 1.0), (float(x), py1 - 1.0)], 1.0, WATTLE)
        for y in range(int(py0) + 3, int(py1), 4):
            f.ink([(px0 + 1.0, float(y)), (px1, float(y) + 0.6)], 0.8, WATTLE_LIGHT)
    # The doorway: dark, under a lintel of wood.
    dx0, dx1 = 70.0, 92.0
    f.poly(_rect(dx0, 82.0, dx1, ground - 2.0), INTERIOR, body=False)
    f.limb([(dx0 - 3.0, 81.0), (dx1 + 3.0, 81.0)], 3.0, POLE)
    for x in (dx0, dx1):
        f.limb([(x, 82.0), (x, ground - 2.0)], 2.2, POLE_SHADE)
    # The roof: palm fronds laid over a frame of poles, steep, with a deep
    # ragged fringe over the wall.
    ex0, ex1, eave = 18.0, 136.0, 72.0
    rx0, rx1, ridge = 44.0, 110.0, 24.0
    roof = [(rx0, ridge), (rx1, ridge), (ex1, eave), (ex0, eave)]
    f.poly(roof, THATCH)
    f.poly([(rx1 - 8.0, ridge), (rx1, ridge), (ex1, eave), (ex1 - 26.0, eave)], THATCH_SHADE, body=False)

    def left(y: float) -> float:
        return _lerp(rx0, ex0, (y - ridge) / (eave - ridge)) + 1.0

    def right(y: float) -> float:
        return _lerp(rx1, ex1, (y - ridge) / (eave - ridge)) - 1.0

    _thatch_rows(f, left, right, ridge + 3.0, eave - 2.0, 8.0, rng, THATCH_LIGHT, THATCH_DARK)
    # The ragged fringe of the palm leaves along the eaves.
    fringe: List[Point] = [(ex0, eave - 1.0)]
    x = ex0
    while x < ex1:
        x2 = min(ex1, x + rng.uniform(3.0, 5.0))
        fringe += [((x + x2) / 2.0, eave + rng.uniform(3.0, 7.0)), (x2, eave + 1.0)]
        x = x2
    fringe.append((ex1, eave - 1.0))
    f.poly(fringe, THATCH)
    f.ink([(ex0 + 2.0, eave), (ex1 - 2.0, eave)], 0.8, THATCH_DARK)
    for px, py in fringe[1:-1:2]:
        f.ink([(px, py - 1.0), (px, eave + 0.4)], 0.5, THATCH_SHADE)
    f.limb([(rx0 - 3.0, ridge), (rx1 + 3.0, ridge)], 4.0, THATCH_DARK)
    for x in (rx0, 66.0, 88.0, rx1):
        f.ink([(x, ridge - 2.0), (x - 1.0, ridge + 2.0)], 1.0, POLE_SHADE)
    # A clay water jar on the left.
    f.ellipse(18.0, ground - 9.0, 8.0, 8.0, CLAY_LIGHT)
    f.poly([(14.0, ground - 20.0), (22.0, ground - 20.0), (21.0, ground - 15.0), (15.0, ground - 15.0)], CLAY_LIGHT)
    f.ellipse(18.0, ground - 20.0, 4.0, 1.2, CLAY_SHADE)
    f.ink(_ring(18.0, ground - 9.0, 6.6, 6.6, 20.0, 100.0, 8), 1.2, CLAY_SHADE)
    # The mortar and pestle by the door: a tall wooden mortar for pounding
    # maize and cassava, with its pestle standing in it.
    mx = 142.0
    f.limb([(mx + 2.0, ground - 22.0), (mx - 4.0, 58.0)], 2.6, POLE_LIGHT)
    f.ellipse(mx - 4.2, 58.0, 2.4, 3.0, POLE_LIGHT)
    f.poly([(mx - 8.0, ground - 24.0), (mx + 8.0, ground - 24.0), (mx + 6.0, ground - 14.0), (mx + 4.0, ground - 10.0), (mx + 7.0, ground - 2.0),
            (mx - 7.0, ground - 2.0), (mx - 4.0, ground - 10.0), (mx - 6.0, ground - 14.0)], HARDWOOD)
    f.poly([(mx + 2.0, ground - 24.0), (mx + 8.0, ground - 24.0), (mx + 6.0, ground - 14.0), (mx + 4.0, ground - 10.0), (mx + 7.0, ground - 2.0), (mx + 2.0, ground - 2.0)],
           K.alpha(MAHOGANY_SHADE, 0.6), body=False)
    f.ellipse(mx, ground - 24.0, 8.0, 1.8, HARDWOOD_LIGHT)
    f.ellipse(mx, ground - 24.0, 5.6, 1.0, INTERIOR, body=False)
    return A.finish(f, width=1.3)


# ---------------------------------------------------------------------------
# The village forge.
# ---------------------------------------------------------------------------


def _hoe(f: K.Frame, x: float, y0: float, length: float) -> None:
    """A hoe that hangs from a peg on the beam: a short wooden handle that
    hangs at a slant, and a broad iron blade set across its foot, like the
    hoes of Central Africa."""
    foot = (x - 5.0, y0 + length)
    f.limb([(x, y0), foot], 2.4, POLE_LIGHT)
    f.ellipse(x, y0, 2.2, 2.2, POLE)
    # The blade spreads from a narrow neck at the handle to a broad,
    # slightly curved edge. It points down and to the right, across the
    # line of the handle.
    a = math.radians(30.0)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    neck = (foot[0] + ux * 1.0, foot[1] + uy * 1.0)
    blade = [(neck[0] + nx * 1.8, neck[1] + ny * 1.8)]
    for k in range(9):
        t = -1.0 + 2.0 * k / 8.0
        reach = 11.0 + 1.6 * (1.0 - t * t)
        blade.append((foot[0] + ux * reach + nx * 6.0 * t, foot[1] + uy * reach + ny * 6.0 * t))
    blade.append((neck[0] - nx * 1.8, neck[1] - ny * 1.8))
    blade = [blade[0]] + list(reversed(blade[1:-1])) + [blade[-1]]
    f.poly(blade, IRON)
    f.poly([blade[0]] + blade[1:6] + [(foot[0] + ux * 4.0, foot[1] + uy * 4.0)], IRON_SHADE, body=False)
    f.ink(blade[5:10], 0.8, IRON_LIGHT)
    f.ellipse(foot[0], foot[1], 2.4, 2.4, POLE)


def _draw_village_forge(anim: str, i: int, n: int):
    w, h = VILLAGE_FORGE_FRAME
    f = K.Frame(VILLAGE_FORGE_FRAME)
    rng = random.Random("history_village_forge")
    ph = i / float(max(1, n))
    ground = h - 5.0
    f.poly([(6.0, ground - 3.0), (w - 6.0, ground - 3.0), (w - 4.0, ground), (4.0, ground)], GROUND)
    # The shelter: a low roof of palm thatch on two forked posts, open on
    # every side, so that the smoke goes out.
    eave = 30.0
    for x in (10.0, 118.0):
        f.limb([(x, ground - 2.0), (x, eave + 2.0)], 3.0, POLE)
        f.ink([(x - 0.8, ground - 3.0), (x - 0.8, eave + 3.0)], 0.6, POLE_LIGHT)
    f.limb([(8.0, eave + 1.0), (120.0, eave + 1.0)], 2.6, POLE_SHADE)
    rx0, rx1, ex0, ex1, ridge = 28.0, 100.0, 6.0, 122.0, 10.0
    f.poly([(rx0, ridge), (rx1, ridge), (ex1, eave), (ex0, eave)], THATCH)
    f.poly([(rx1 - 8.0, ridge), (rx1, ridge), (ex1, eave), (ex1 - 22.0, eave)], THATCH_SHADE, body=False)

    def left(y: float) -> float:
        return _lerp(rx0, ex0, (y - ridge) / (eave - ridge)) + 1.0

    def right(y: float) -> float:
        return _lerp(rx1, ex1, (y - ridge) / (eave - ridge)) - 1.0

    _thatch_rows(f, left, right, ridge + 3.0, eave - 2.0, 6.0, rng, THATCH_LIGHT, THATCH_DARK)
    fringe: List[Point] = [(ex0, eave - 1.0)]
    x = ex0
    while x < ex1:
        x2 = min(ex1, x + rng.uniform(3.0, 4.6))
        fringe += [((x + x2) / 2.0, eave + rng.uniform(2.6, 5.0)), (x2, eave + 0.6)]
        x = x2
    fringe.append((ex1, eave - 1.0))
    f.poly(fringe, THATCH)
    f.ink([(ex0 + 2.0, eave), (ex1 - 2.0, eave)], 0.7, THATCH_DARK)
    f.limb([(rx0 - 2.0, ridge), (rx1 + 2.0, ridge)], 3.0, THATCH_DARK)
    # New hoes hang from the beam, ready for the fields.
    for x, ln in ((86.0, 12.0), (106.0, 18.0)):
        _hoe(f, x, eave + 4.0, ln)
    # The two bowl bellows: wooden bowls covered with hide, each with a
    # stick to pump it. Their pipes meet in a clay nozzle into the hearth.
    for k, bx in enumerate((22.0, 44.0)):
        by = ground - 11.0
        f.poly([(bx - 12.0, by - 3.0), (bx + 12.0, by - 3.0), (bx + 10.0, ground - 2.0), (bx - 10.0, ground - 2.0)], POLE if k else POLE_SHADE)
        f.ink([(bx - 11.0, by + 1.0), (bx + 11.0, by + 1.0)], 0.8, POLE_LIGHT)
        dome = _ring(bx, by - 3.0, 12.0, 6.0 + 1.5 * k, 180.0, 360.0, 12)
        f.poly(dome, HIDE if k else HIDE_SHADE)
        for dx in (-5.0, 0.0, 5.0):
            f.ink([(bx + dx * 1.6, by - 3.4), (bx + dx * 0.4, by - 8.0 - 1.5 * k)], 0.6, HIDE_SHADE if k else (104, 72, 46, 255))
        f.ink(_ring(bx, by - 3.0, 10.0, 4.4 + 1.5 * k, 200.0, 290.0, 8), 0.8, HIDE_LIGHT)
        f.ink([(bx - 12.0, by - 3.0), (bx + 12.0, by - 3.0)], 1.4, ROPE_DARK)
        f.limb([(bx, by - 8.0 - 1.5 * k), (bx - 1.0, 50.0 + 4.0 * k)], 2.2, POLE_LIGHT)
        f.ellipse(bx - 1.0, 50.0 + 4.0 * k, 1.8, 1.8, POLE)
    # The nozzle: a clay pipe from the bellows into the foot of the hearth.
    f.limb([(54.0, ground - 8.0), (68.0, ground - 8.0)], 5.0, CLAY_SHADE)
    f.ink([(55.0, ground - 9.6), (67.0, ground - 9.6)], 0.8, CLAY_LIGHT)
    # The hearth: a low wall of clay round a bed of charcoal.
    hx0, hx1 = 64.0, 96.0
    f.poly([(hx0, ground - 2.0), (hx0 + 2.0, ground - 14.0), (hx1 - 2.0, ground - 14.0), (hx1, ground - 2.0)], CLAY)
    f.poly([(hx0 + 1.0, ground - 7.0), (hx1 - 1.0, ground - 7.0), (hx1, ground - 2.0), (hx0, ground - 2.0)], CLAY_SHADE, body=False)
    f.ink([(hx0 + 3.0, ground - 13.0), (hx1 - 3.0, ground - 13.0)], 0.8, CLAY_LIGHT)
    # The coals: a heap of black lumps; the live ones glow and breathe.
    span = hx1 - hx0 - 6.0

    def heap_y(x: float) -> float:
        return ground - 14.0 - 7.0 * max(0.0, math.sin(math.pi * (x - hx0 - 3.0) / span)) ** 0.8

    heap = [(x, heap_y(x)) for x in [hx0 + 3.0 + span * k / 12.0 for k in range(13)]]
    f.poly(heap, COAL)
    for k in range(9):
        x = hx0 + 6.0 + k * (span - 6.0) / 8.0 + rng.uniform(-0.8, 0.8)
        y = heap_y(x) + rng.uniform(1.6, 4.0)
        g = 0.55 + 0.45 * math.sin(2.0 * math.pi * (ph + k * 0.37))
        f.ellipse(x, y, 1.8, 1.2, K.alpha(EMBER_HOT if g > 0.8 else EMBER, 0.55 + 0.45 * g), body=False)
    cx = (hx0 + hx1) / 2.0
    pulse = 0.5 + 0.5 * math.sin(2.0 * math.pi * ph)
    f.glow(cx, ground - 17.0, 7.0 + 1.5 * pulse, (255, 150, 60, int(40 + 40 * pulse)))
    # Sparks rise from the coals and fade.
    for k in range(4):
        u = (ph + k / 4.0) % 1.0
        x = cx - 6.0 + k * 4.0 + 3.0 * math.sin(2.0 * math.pi * (u + k * 0.2))
        y = ground - 22.0 - 24.0 * u
        a = int(220 * (1.0 - u))
        if a > 12:
            f.glow(x, y, 0.9, (255, 210, 120, a))
    # The anvil: a heavy stone with a flat top, and an iron hammer on it.
    ax0, ax1 = 100.0, 118.0
    f.poly([(ax0, ground - 2.0), (ax0 + 1.0, ground - 15.0), (ax0 + 4.0, ground - 18.0), (ax1 - 3.0, ground - 18.0), (ax1, ground - 14.0), (ax1 + 1.0, ground - 2.0)], STONE)
    f.poly([(ax1 - 6.0, ground - 18.0), (ax1 - 3.0, ground - 18.0), (ax1, ground - 14.0), (ax1 + 1.0, ground - 2.0), (ax1 - 5.0, ground - 2.0)], STONE_SHADE, body=False)
    f.ink([(ax0 + 4.0, ground - 17.0), (ax1 - 4.0, ground - 17.0)], 1.0, STONE_LIGHT)
    f.ink([(ax0 + 4.0, ground - 10.0), (ax0 + 9.0, ground - 7.0)], 0.6, STONE_SHADE)
    f.limb([(ax0 + 1.0, ground - 20.0), (ax0 + 12.0, ground - 20.0)], 2.0, POLE_LIGHT)
    f.poly(_rect(ax0 + 11.0, ground - 24.0, ax0 + 16.0, ground - 18.0), IRON)
    f.ink([(ax0 + 11.6, ground - 23.0), (ax0 + 11.6, ground - 19.0)], 0.6, IRON_LIGHT)
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# The Lei Áurea: the writing table.
# ---------------------------------------------------------------------------


def _draw_lei_aurea(anim: str, i: int, n: int):
    w, h = LEI_AUREA_FRAME
    f = K.Frame(LEI_AUREA_FRAME)
    rng = random.Random("history_lei_aurea")
    ground = h - 4.0
    top = 74.0
    # The legs: turned mahogany, thin, with a ring and a foot.
    for x in (14.0, 82.0):
        f.limb([(x, top + 8.0), (x, ground - 2.0)], 3.4, MAHOGANY)
        f.ellipse(x, top + 16.0, 3.0, 2.0, MAHOGANY_LIGHT)
        f.ellipse(x, ground - 20.0, 2.6, 1.6, MAHOGANY_LIGHT)
        f.ellipse(x, ground - 2.0, 3.0, 1.6, MAHOGANY_SHADE)
        f.ink([(x - 0.8, top + 18.0), (x - 0.8, ground - 22.0)], 0.6, MAHOGANY_LIGHT)
    # The top and its apron, under a cloth of green baize with a gold
    # fringe.
    f.poly(_rect(6.0, top, 90.0, top + 10.0), MAHOGANY)
    f.poly(_rect(6.0, top + 7.0, 90.0, top + 10.0), MAHOGANY_SHADE, body=False)
    f.poly([(4.0, top - 2.0), (92.0, top - 2.0), (92.0, top + 5.0), (4.0, top + 5.0)], BAIZE)
    f.poly([(4.0, top + 2.0), (92.0, top + 2.0), (92.0, top + 5.0), (4.0, top + 5.0)], BAIZE_SHADE, body=False)
    f.ink([(5.0, top - 1.2), (91.0, top - 1.2)], 0.8, BAIZE_LIGHT)
    for k in range(29):
        x = 5.0 + k * 3.0
        f.ink([(x, top + 5.0), (x, top + 7.6)], 0.9, GOLD)
    f.ink([(4.0, top + 5.0), (92.0, top + 5.0)], 0.9, GOLD_SHADE)
    # The writing slope: a low box with a sloped lid, seen from the front.
    # Its lid shows as a tall face that leans back.
    sx0, sx1, sy0, sy1 = 12.0, 70.0, 40.0, top - 2.0
    f.poly([(sx0, sy1), (sx0 + 3.0, sy0), (sx1 - 3.0, sy0), (sx1, sy1)], MAHOGANY)
    f.poly([(sx1 - 6.0, sy0), (sx1 - 3.0, sy0), (sx1, sy1), (sx1 - 4.0, sy1)], MAHOGANY_SHADE, body=False)
    f.ink([(sx0 + 3.6, sy0 + 1.0), (sx1 - 3.6, sy0 + 1.0)], 0.8, MAHOGANY_LIGHT)
    f.poly(_rect(sx0, sy1 - 3.0, sx1, sy1), MAHOGANY_SHADE, body=False)
    # The parchment on the slope: lines of short strokes (no real words),
    # a wider heading, and a space at the foot for the signature.
    px0, px1, py0, py1 = sx0 + 7.0, sx1 - 7.0, sy0 + 3.0, sy1 - 5.0
    f.poly([(px0 - 1.0, py1), (px0 + 1.0, py0), (px1 - 1.0, py0), (px1 + 1.0, py1)], PARCHMENT)
    f.poly([(px1 - 4.0, py0), (px1 - 1.0, py0), (px1 + 1.0, py1), (px1 - 3.0, py1)], PARCHMENT_SHADE, body=False)
    f.ink([(px0 + 2.0, py0 + 1.0), (px1 - 2.0, py0 + 1.0)], 0.6, PARCHMENT_SHADE)
    _writing_line(f, px0 + 10.0, px1 - 10.0, py0 + 4.0, rng, WRITING, 1.2)
    for k in range(6):
        y = py0 + 8.5 + k * 3.0
        x0 = _lerp(px0 + 1.0, px0 - 1.0, (y - py0) / (py1 - py0)) + 3.0
        x1 = _lerp(px1 - 1.0, px1 + 1.0, (y - py0) / (py1 - py0)) - (3.0 if k < 5 else 18.0)
        _writing_line(f, x0, x1, y, rng, WRITING, 0.8)
    # The signature line, still empty, and the seal: red wax on a ribbon of
    # green and gold that hangs over the edge of the slope.
    f.ink([(px0 + 4.0, py1 - 3.0), (px0 + 22.0, py1 - 3.0)], 0.5, WRITING)
    rx = px1 - 8.0
    f.poly([(rx - 2.0, py1 - 6.0), (rx + 1.0, py1 - 6.0), (rx - 1.0, sy1 + 9.0), (rx - 4.0, sy1 + 8.0)], BAIZE)
    f.poly([(rx + 1.0, py1 - 6.0), (rx + 4.0, py1 - 6.0), (rx + 5.0, sy1 + 8.0), (rx + 2.0, sy1 + 9.0)], GOLD)
    f.ellipse(rx + 0.5, py1 - 4.0, 4.2, 4.2, SEAL)
    f.ellipse(rx - 0.2, py1 - 4.8, 1.8, 1.6, SEAL_LIGHT, body=False)
    f.ink(_ring(rx + 0.5, py1 - 4.0, 2.8, 2.8, 0.0, 360.0, 12), 0.5, (140, 24, 30, 255))
    # The inkstand and the gold pen in it.
    ix = 80.0
    f.poly(_rect(ix - 9.0, top - 6.0, ix + 9.0, top - 2.0), SILVER)
    f.ink([(ix - 8.0, top - 5.2), (ix + 8.0, top - 5.2)], 0.6, (236, 238, 242, 255))
    f.poly([(ix - 5.0, top - 6.0), (ix - 5.0, top - 13.0), (ix - 3.0, top - 15.0), (ix + 3.0, top - 15.0), (ix + 5.0, top - 13.0), (ix + 5.0, top - 6.0)], INKWELL)
    f.ink([(ix - 3.6, top - 12.0), (ix - 3.6, top - 8.0)], 0.8, (120, 130, 168, 255))
    f.ellipse(ix, top - 15.0, 3.0, 1.0, SILVER)
    f.limb([(ix - 1.0, top - 13.0), (ix + 7.0, 34.0)], 2.2, GOLD)
    f.ink([(ix - 0.4, top - 15.0), (ix + 6.6, 36.0)], 0.6, GOLD_LIGHT)
    for t in (0.3, 0.55):
        p = _mix((ix - 1.0, top - 13.0), (ix + 7.0, 34.0), t)
        f.ink([(p[0] - 1.4, p[1] + 0.4), (p[0] + 1.4, p[1] - 0.4)], 0.8, GOLD_SHADE)
    f.ellipse(ix + 7.2, 33.0, 1.6, 1.6, GOLD_LIGHT)
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# The bonde: a mule-drawn tram of Rio.
# ---------------------------------------------------------------------------


def _wheel(f: K.Frame, cx: float, cy: float, r: float) -> None:
    """An iron tram wheel with spokes and a flange."""
    f.ellipse(cx, cy, r, r, WHEEL)
    f.ink(_ring(cx, cy, r - 1.6, r - 1.6, 0.0, 360.0, 24), 0.8, WHEEL_LIGHT)
    for k in range(8):
        a = math.radians(k * 22.5 + 11.0)
        f.ink([(cx + math.cos(a) * 2.4, cy + math.sin(a) * 2.4), (cx + math.cos(a) * (r - 2.4), cy + math.sin(a) * (r - 2.4))], 0.8, WHEEL_LIGHT)
    f.ellipse(cx, cy, 2.6, 2.6, WHEEL_LIGHT)


def _mule(f: K.Frame, ground: float) -> None:
    """A mule in harness, facing right: long ears, a short mane, a collar
    and hames, a back pad and a belly band, and a bridle with blinkers."""
    # The far legs, a shade darker.
    f.limb([(202.0, 116.0), (200.0, 132.0), (204.0, ground - 2.0)], 3.8, MULE_SHADE)
    f.limb([(226.0, 118.0), (228.0, ground - 2.0)], 3.8, MULE_SHADE)
    for x in (204.0, 228.0):
        f.poly(_rect(x - 2.4, ground - 3.0, x + 2.6, ground), HARNESS)
    # The tail.
    f.limb([(191.0, 102.0), (187.0, 112.0), (187.0, 120.0)], 2.2, MULE_SHADE)
    f.poly([(185.6, 118.0), (188.6, 118.0), (190.0, 126.0), (188.6, 132.0), (186.6, 128.0), (185.0, 132.0), (184.0, 125.0)], HARNESS)
    # The body.
    body = [(192.0, 100.0), (200.0, 96.0), (214.0, 98.0), (226.0, 96.0), (234.0, 98.0), (238.0, 106.0), (236.0, 114.0), (228.0, 120.0),
            (210.0, 121.0), (198.0, 119.0), (191.0, 112.0)]
    f.poly(body, MULE)
    f.ellipse(198.0, 106.0, 8.0, 9.0, MULE)
    f.ellipse(230.0, 107.0, 8.0, 9.0, MULE)
    f.poly([(198.0, 116.0), (228.0, 116.0), (228.0, 120.0), (210.0, 121.0), (198.0, 119.0)], MULE_LIGHT, body=False)
    f.ink([(196.0, 99.0), (212.0, 99.4)], 0.8, MULE_LIGHT)
    # The near hind leg: a strong thigh, a hock, a thin cannon.
    f.poly([(192.0, 104.0), (204.0, 104.0), (204.0, 118.0), (200.0, 128.0), (197.0, 128.0), (193.0, 116.0)], MULE)
    f.limb([(198.6, 127.0), (196.0, 136.0), (198.0, ground - 2.0)], 4.0, MULE)
    # The near foreleg.
    f.poly([(228.0, 108.0), (236.0, 108.0), (236.0, 126.0), (232.0, 128.0)], MULE)
    f.limb([(234.0, 124.0), (234.0, ground - 2.0)], 4.0, MULE)
    for x in (198.0, 234.0):
        f.poly(_rect(x - 2.6, ground - 3.0, x + 2.6, ground), HARNESS)
    # The neck and the head: long, a little low, with long ears.
    f.poly([(226.0, 98.0), (234.0, 84.0), (240.0, 78.0), (245.0, 80.0), (240.0, 92.0), (238.0, 104.0)], MULE)
    f.poly([(239.0, 77.0), (244.0, 76.0), (250.0, 90.0), (250.0, 95.0), (246.0, 97.0), (242.0, 94.0), (239.0, 84.0)], MULE)
    f.poly([(246.0, 88.0), (250.0, 90.0), (250.0, 95.0), (246.0, 97.0), (243.0, 94.0)], MULE_MUZZLE, body=False)
    f.dot(248.0, 91.0, 0.7, HARNESS)
    # The long ears: the far one laid back, the near one up.
    f.poly([(238.0, 79.0), (231.0, 68.0), (229.0, 62.0), (232.0, 63.0), (240.0, 75.0)], MULE_SHADE)
    f.poly([(240.0, 78.0), (240.0, 66.0), (242.0, 59.0), (244.6, 62.0), (244.0, 77.0)], MULE)
    f.ink([(241.6, 64.0), (242.0, 74.0)], 1.0, MULE_LIGHT)
    # A short upright mane along the neck.
    f.ink([(227.0, 96.0), (233.0, 85.0), (239.0, 78.0)], 1.8, HARNESS)
    # The bridle, the blinker and the reins that go back to the tram.
    f.ink([(242.0, 77.0), (245.0, 92.0)], 0.9, HARNESS)
    f.ink([(241.0, 89.0), (249.0, 89.0)], 0.9, HARNESS)
    f.poly(_rect(240.0, 81.0, 245.0, 86.0), HARNESS)
    f.dot(247.0, 92.0, 0.9, BRASS)
    f.ink([(246.0, 92.0), (232.0, 96.0), (210.0, 92.0), (176.0, 96.0)], 0.7, HARNESS_LIGHT)
    # The collar and the hames round the neck, with brass knobs.
    f.limb([(230.0, 92.0), (236.0, 100.0), (238.0, 108.0)], 4.2, HARNESS)
    f.limb([(231.0, 90.0), (233.0, 87.0)], 1.6, BRASS)
    f.dot(236.4, 100.0, 1.0, BRASS)
    # The back pad and the belly band.
    f.poly(_rect(208.0, 96.0, 216.0, 106.0), HARNESS_LIGHT)
    f.limb([(212.0, 104.0), (212.0, 121.0)], 1.8, HARNESS)
    # The traces: from the collar back to the swingletree on the tram.
    f.limb([(236.0, 106.0), (210.0, 110.0), (180.0, 118.0)], 1.4, HARNESS)


def _draw_bonde(anim: str, i: int, n: int):
    w, h = BONDE_FRAME
    f = K.Frame(BONDE_FRAME)
    ground = h - 8.0
    # The street: a strip of cobbles with the rail let into it.
    f.poly([(5.0, ground), (w - 5.0, ground), (w - 5.0, h - 5.0), (5.0, h - 5.0)], COBBLE)
    for k in range(31):
        x = 8.0 + k * 8.0
        f.ink([(x, ground + 2.0), (x, h - 5.6)], 0.7, COBBLE_SHADE)
    f.limb([(6.0, ground + 0.6), (w - 6.0, ground + 0.6)], 1.8, RAIL)
    # The car: x0 to x1, with a platform at each end.
    x0, x1 = 12.0, 176.0
    floor = 122.0
    roof_y = 40.0
    # The wheels, behind the side skirt.
    for x in (50.0, 138.0):
        _wheel(f, x, ground - 11.0, 11.0)
    # The posts that hold the roof, and the benches across the car. From
    # the side, each bench shows its end: a seat and a back.
    posts = [x0 + 18.0 + k * 21.0 for k in range(8)]
    for k, x in enumerate(posts[:-1]):
        bx = x + 10.5
        f.poly(_rect(bx - 6.0, floor - 16.0, bx + 6.0, floor - 12.0), BENCH)
        f.ink([(bx - 5.0, floor - 15.2), (bx + 5.0, floor - 15.2)], 0.7, BENCH_LIGHT)
        f.limb([(bx - 4.0, floor - 12.0), (bx - 4.0, floor - 1.0)], 1.6, BENCH_SHADE)
        f.limb([(bx + 4.0, floor - 12.0), (bx + 4.0, floor - 1.0)], 1.6, BENCH_SHADE)
        f.limb([(bx - 4.0, floor - 16.0), (bx - 6.0, floor - 32.0)], 2.4, BENCH)
        f.ink([(bx - 5.0, floor - 30.0), (bx - 3.6, floor - 18.0)], 0.6, BENCH_LIGHT)
    for x in posts:
        f.limb([(x, floor), (x, roof_y + 8.0)], 1.8, TRAM_CREAM)
        f.ink([(x - 0.5, floor - 1.0), (x - 0.5, roof_y + 9.0)], 0.5, (250, 240, 210, 255))
    # The rail along the side at seat-back height, for the riders to hold.
    f.limb([(posts[0], floor - 26.0), (posts[-1], floor - 26.0)], 1.4, BRASS)
    # The roof: a low curve with a raised lantern in the middle, and a
    # letter board under the eaves (plain, with no letters).
    f.poly([(x0 - 2.0, roof_y + 6.0), (x0 + 4.0, roof_y + 2.0), (x1 - 4.0, roof_y + 2.0), (x1 + 2.0, roof_y + 6.0), (x1 + 2.0, roof_y + 9.0), (x0 - 2.0, roof_y + 9.0)], ROOF)
    f.poly([(x0 + 30.0, roof_y + 2.0), (x0 + 32.0, roof_y - 6.0), (x1 - 32.0, roof_y - 6.0), (x1 - 30.0, roof_y + 2.0)], ROOF)
    f.poly(_rect(x0 + 32.0, roof_y - 3.0, x1 - 32.0, roof_y + 1.0), TRAM_GREEN_SHADE, body=False)
    for k in range(10):
        x = x0 + 36.0 + k * 10.0
        f.ink([(x, roof_y - 2.6), (x, roof_y + 0.6)], 1.2, TRAM_CREAM_SHADE)
    f.ink([(x0 - 1.0, roof_y + 8.6), (x1 + 1.0, roof_y + 8.6)], 0.9, ROOF_SHADE)
    f.poly(_rect(x0 + 6.0, roof_y + 9.0, x1 - 6.0, roof_y + 16.0), TRAM_GREEN)
    f.ink([(x0 + 8.0, roof_y + 10.4), (x1 - 8.0, roof_y + 10.4), (x1 - 8.0, roof_y + 14.6), (x0 + 8.0, roof_y + 14.6), (x0 + 8.0, roof_y + 10.4)], 0.6, GOLD)
    # The body: a side sill of green with cream lining, the running board
    # under it, and the dashboards at the two ends.
    f.poly(_rect(x0 + 6.0, floor, x1 - 6.0, floor + 12.0), TRAM_GREEN)
    f.poly(_rect(x0 + 6.0, floor + 8.0, x1 - 6.0, floor + 12.0), TRAM_GREEN_SHADE, body=False)
    f.ink([(x0 + 8.0, floor + 2.0), (x1 - 8.0, floor + 2.0)], 0.8, TRAM_CREAM)
    for k in range(4):
        p0 = x0 + 14.0 + k * 38.0
        f.ink([(p0, floor + 4.0), (p0 + 30.0, floor + 4.0), (p0 + 30.0, floor + 8.0), (p0, floor + 8.0), (p0, floor + 4.0)], 0.6, GOLD)
    f.limb([(x0 + 10.0, floor + 16.0), (x1 - 10.0, floor + 16.0)], 2.6, BENCH_SHADE)
    for x in (x0 + 16.0, x1 - 16.0):
        f.limb([(x, floor + 12.0), (x, floor + 16.0)], 1.4, IRON)
    for x, s in ((x0, -1.0), (x1, 1.0)):
        dash = [(x - s * 6.0, floor + 10.0), (x - s * 6.0, floor - 18.0), (x + s * 1.0, floor - 16.0), (x + s * 2.0, floor + 4.0), (x, floor + 10.0)]
        f.poly(dash, TRAM_GREEN)
        f.ink([(x - s * 4.6, floor - 15.0), (x + s * 0.4, floor - 13.6), (x + s * 1.0, floor + 2.0)], 0.6, TRAM_CREAM)
        f.limb([(x - s * 6.0, floor - 18.0), (x - s * 6.0, roof_y + 9.0)], 1.8, TRAM_CREAM)
    # The brake handle on the front platform, and the swingletree.
    f.limb([(x1 - 10.0, floor), (x1 - 9.0, floor - 22.0)], 1.6, IRON)
    f.limb([(x1 - 12.0, floor - 22.0), (x1 - 6.0, floor - 22.0)], 1.6, IRON)
    f.limb([(x1 + 1.0, floor + 6.0), (x1 + 6.0, floor - 4.0)], 1.6, IRON)
    f.ellipse(x1 + 6.0, floor - 4.0, 2.0, 2.0, IRON_LIGHT)
    # A lamp on the front of the roof.
    f.poly(_rect(x1 - 1.0, roof_y + 12.0, x1 + 5.0, roof_y + 20.0), BRASS)
    f.poly(_rect(x1, roof_y + 14.0, x1 + 4.0, roof_y + 18.0), (252, 236, 170, 255), body=False)
    _mule(f, ground)
    return A.finish(f, width=1.3)


# ---------------------------------------------------------------------------
# Publication.
# ---------------------------------------------------------------------------

FRAMES: Dict[str, Tuple[int, int]] = {
    "history_victoria_lily": VICTORIA_LILY_FRAME,
    "history_jangada": JANGADA_FRAME,
    "history_marajoara_pots": MARAJOARA_POTS_FRAME,
    "history_teso_house": TESO_HOUSE_FRAME,
    "history_mocambo_hut": MOCAMBO_HUT_FRAME,
    "history_village_forge": VILLAGE_FORGE_FRAME,
    "history_lei_aurea": LEI_AUREA_FRAME,
    "history_bonde": BONDE_FRAME,
}
DRAW: Dict[str, Callable] = {
    "history_victoria_lily": _draw_victoria_lily,
    "history_jangada": _draw_jangada,
    "history_marajoara_pots": _draw_marajoara_pots,
    "history_teso_house": _draw_teso_house,
    "history_mocambo_hut": _draw_mocambo_hut,
    "history_village_forge": _draw_village_forge,
    "history_lei_aurea": _draw_lei_aurea,
    "history_bonde": _draw_bonde,
}
DISPLAY = {
    "history_victoria_lily": "Victoria Lily",
    "history_jangada": "Jangada",
    "history_marajoara_pots": "Marajoara Pots",
    "history_teso_house": "Teso House",
    "history_mocambo_hut": "Mocambo Hut",
    "history_village_forge": "Village Forge",
    "history_lei_aurea": "Lei Áurea",
    "history_bonde": "Bonde",
}
#: The room of each prop: its last tag.
ROOMS = {
    "history_victoria_lily": "amazonia",
    "history_jangada": "rio_1888",
    "history_marajoara_pots": "amazonia",
    "history_teso_house": "amazonia",
    "history_mocambo_hut": "palmares",
    "history_village_forge": "palmares",
    "history_lei_aurea": "rio_1888",
    "history_bonde": "rio_1888",
}
ROWS: Dict[str, List[Tuple[str, int, int]]] = {
    "history_victoria_lily": LOOP,
    "history_jangada": LOOP,
    "history_village_forge": LOOP,
}


def _foot(name: str) -> Dict[str, Tuple[float, float]]:
    w, h = FRAMES[name]
    return {"foot": (w / 2.0, float(h))}


#: The anchors of each prop. A platform has a "top" anchor at the middle of
#: the surface that a player stands on; the other props have a "foot".
ANCHORS: Dict[str, Dict[str, Tuple[float, float]]] = {name: _foot(name) for name in DISPLAY}
ANCHORS["history_victoria_lily"] = {"top": ((VICTORIA_LILY_SPAN[0] + VICTORIA_LILY_SPAN[1]) / 2.0, VICTORIA_LILY_TOP)}
ANCHORS["history_jangada"] = {"top": ((JANGADA_SPAN[0] + JANGADA_SPAN[1]) / 2.0, JANGADA_TOP)}
TAGS: Dict[str, List[str]] = {name: ["prop", "scenery", "history", ROOMS[name]] for name in DISPLAY}
TAGS["history_victoria_lily"] = ["prop", "platform", "history", ROOMS["history_victoria_lily"]]
TAGS["history_jangada"] = ["prop", "platform", "history", ROOMS["history_jangada"]]

TARGETS: Dict[str, dict] = {
    name: _publisher(name, DISPLAY[name], ROWS.get(name, STILL), FRAMES[name], DRAW[name], ANCHORS[name], "Scenery", TAGS[name]) for name in DISPLAY
}
