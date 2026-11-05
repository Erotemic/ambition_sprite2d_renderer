"""The props of Central Africa (the History dimension): Ishango, the
kingdom of Kongo, Ndongo and Matamba, and the Congo river about 1904.

About 20,000 years ago hunter-fishers lived at Ishango, where the Semliki
river leaves Lake Edward. They left the Ishango bone: a baboon fibula with
three columns of grouped notches and a chip of quartz set in one end. Down
the river at Katanda, people made barbed harpoon points of bone perhaps
90,000 years ago.

About 1520 Mbanza Kongo was the capital of the kingdom of Kongo. Its
weavers made raffia cloth so fine that Europeans called it velvet. Its
money was nzimbu: small shells from the island of Luanda, gathered only
for the king. In 1526 King Afonso I wrote to Lisbon against the slave
trade.

At Luanda in 1622 the Portuguese governor sat in a chair and gave Nzinga
Mbande only a mat on the floor. Later she fought Portugal for thirty years
from the war camps (kilombo) of Matamba. Baobabs grow in the Kwanza
valley.

From 1885 to 1908 the Congo Free State was the private property of King
Leopold II. Its agents took wild rubber by quota and by terror. Witnesses
told the world: Alice Seeley Harris showed her photographs with a magic
lantern. Small stern-wheel steamers went up the river. These props of the
Congo river are quiet and sober.

These props are drawn in the cel style of the dimension's cast
(`targets/characters/_history_americas_kit.py`): flat colour, one shade, a
bold warm outline. They show the skill and the dignity of the people who
made them. No script is drawn: writing is lines of short strokes. There
are no people, no bodies and no weapons in use.

- ``history_ishango_bone``: scenery, the Ishango bone, much larger than
  life: a thin, slightly curved dark-brown bone with three rows of grouped
  notches (11, 13, 17, 19; 3, 6, 4, 8, 10, 5, 5, 7; 11, 21, 19, 9) and a
  pale quartz chip set in its end, on a flat stone.
- ``history_bone_harpoons``: scenery, barbed bone harpoon points of the
  Katanda type, hung by fibre cords on a drying rack of forked poles,
  with three fish that dry on the lower pole.
- ``history_raffia_loom``: scenery, the upright single-heddle raffia loom
  of Kongo: a frame of poles that leans on a forked post, a warp of pale
  raffia, a shed rod, a heddle rod with string loops, a beater, and a
  half-woven square panel with a pattern of interlaced diamonds.
- ``history_nzimbu_basket``: scenery, a round coiled basket full of nzimbu
  shells (small, smooth, olive-shaped shells), with a few spilled beside
  it.
- ``history_afonso_letter``: scenery, a small writing table of the 1500s
  with a writing slope, an open letter (lines of short strokes and a red
  seal), an inkwell with a quill, and a second letter rolled and tied.
- ``history_kongo_house``: scenery, a rectangular house of Mbanza Kongo:
  walls of woven palm-mat panels framed by poles, a low door, and a steep
  two-slope thatched roof with a ridge.
- ``history_kilombo_gate``: scenery, the gate of a war camp (kilombo) of
  Matamba: a palisade of sharpened stakes lashed to cross poles, a closed
  gate of stakes between two tall posts, and a lookout platform on poles
  under a small thatched roof.
- ``history_luanda_chair``: scenery, Luanda, 1622: a high-backed chair of
  dark wood with crimson velvet and brass nails, on a low dais of one
  step, and beside it a plain woven mat on the floor. No people.
- ``history_baobab``: scenery, a big baobab: a massive grey trunk with a
  hollow, stout branches that spread at the top, a few leaves and hanging
  fruit pods. Two limbs are level so that a player can stand on them
  (`BAOBAB_LOW_SPAN` = (88, 330) at `BAOBAB_LOW_TOP` = 352, and
  `BAOBAB_HIGH_SPAN` = (352, 532) at `BAOBAB_HIGH_TOP` = 144, in a
  576 x 576 frame).
- ``history_rubber_vine``: scenery, a wild rubber vine (Landolphia) that
  climbs a tree trunk, with a cut in the vine and a slow drip of white
  latex into a small clay cup. Its ``idle`` row grows a drop and lets it
  fall.
- ``history_magic_lantern``: scenery, a magic lantern of about 1904 (a
  black metal body, a chimney and a brass lens tube) on a wooden tripod
  stand, and an open box of glass lantern slides. Its ``idle`` row makes
  a faint warm glow at the lens.
- ``history_congo_steamer``: the look of a platform, a small stern-wheel
  river steamer of about 1890: a long low white hull, a flat open deck, a
  wood-fired boiler with one tall thin funnel, an awning roof on
  stanchions, a wheelhouse on the roof, a cord of firewood, and the
  paddle wheel at the stern. Its deck is the platform
  (`CONGO_STEAMER_SPAN` = (118, 476), `CONGO_STEAMER_TOP` = 236, in a
  512 x 320 frame). Its ``idle`` row turns the wheel and puffs smoke from
  the funnel; the deck stays level and still.

The numbers are frame pixels; the game shows each prop at half its frame.
No drop shadows: the game draws them.
"""

from __future__ import annotations

import math
import random
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from ..characters import _art_cast_kit as K
from ..characters import _history_americas_kit as A
from .art_props import _publisher

Point = Tuple[float, float]
RGBA = Tuple[int, int, int, int]
STILL: List[Tuple[str, int, int]] = [("idle", 1, 1000)]
LOOP: List[Tuple[str, int, int]] = [("idle", 8, 120)]

ISHANGO_BONE_FRAME = (176, 80)
BONE_HARPOONS_FRAME = (160, 160)
RAFFIA_LOOM_FRAME = (144, 176)
NZIMBU_BASKET_FRAME = (112, 72)
AFONSO_LETTER_FRAME = (128, 112)
KONGO_HOUSE_FRAME = (256, 224)
KILOMBO_GATE_FRAME = (256, 320)
LUANDA_CHAIR_FRAME = (224, 176)
BAOBAB_FRAME = (576, 576)
#: The two level limbs of the baobab. A player can stand on each one from
#: x0 to x1 at its height (frame pixels; the foot of the frame is y 576).
#: The low ledge is the flat shoulder of the trunk and the left limb; the
#: high ledge is the right limb.
BAOBAB_LOW_SPAN = (88.0, 330.0)
BAOBAB_LOW_TOP = 352.0
BAOBAB_HIGH_SPAN = (352.0, 532.0)
BAOBAB_HIGH_TOP = 144.0
RUBBER_VINE_FRAME = (160, 288)
MAGIC_LANTERN_FRAME = (160, 144)
CONGO_STEAMER_FRAME = (512, 320)
#: The main deck of the steamer is the platform: it is level from x0 to x1
#: at the height `CONGO_STEAMER_TOP` (frame pixels).
CONGO_STEAMER_SPAN = (118.0, 476.0)
CONGO_STEAMER_TOP = 236.0

# Ishango: the bone and its stone.
FOSSIL = (132, 92, 58, 255)
FOSSIL_LIGHT = (170, 128, 86, 255)
FOSSIL_SHADE = (96, 64, 40, 255)
NOTCH = (44, 26, 18, 255)
QUARTZ = (238, 236, 230, 255)
QUARTZ_SHADE = (196, 190, 192, 255)
QUARTZ_LIGHT = (255, 255, 252, 255)
STONE = (140, 134, 122, 255)
STONE_LIGHT = (176, 170, 156, 255)
STONE_SHADE = (106, 100, 92, 255)
STONE_DARK = (82, 78, 72, 255)

# The harpoon rack.
BONE_PALE = (232, 220, 190, 255)
BONE_LIGHT = (250, 244, 226, 255)
BONE_SHADE = (190, 174, 140, 255)
POLE = (122, 90, 58, 255)
POLE_LIGHT = (156, 120, 80, 255)
POLE_SHADE = (88, 64, 42, 255)
FIBRE = (188, 156, 100, 255)
FIBRE_DARK = (128, 100, 62, 255)
FISH = (150, 134, 106, 255)
FISH_LIGHT = (190, 176, 146, 255)
FISH_SHADE = (104, 88, 66, 255)

# Kongo: raffia, the basket, the shells, the house.
RAFFIA = (226, 206, 150, 255)
RAFFIA_LIGHT = (244, 230, 186, 255)
RAFFIA_SHADE = (184, 160, 106, 255)
CLOTH = (190, 150, 96, 255)
CLOTH_LIGHT = (214, 180, 124, 255)
CLOTH_DARK = (88, 56, 34, 255)
CLOTH_RED = (150, 66, 40, 255)
BASKET = (178, 136, 80, 255)
BASKET_LIGHT = (210, 172, 112, 255)
BASKET_SHADE = (134, 98, 56, 255)
SHELL = (226, 222, 212, 255)
SHELL_TAN = (206, 186, 156, 255)
SHELL_GREY = (184, 182, 178, 255)
SHELL_SHADE = (150, 140, 128, 255)
SHELL_GLOSS = (255, 255, 250, 255)
GROUND = (146, 108, 72, 255)
GROUND_SHADE = (112, 82, 54, 255)
MAT = (214, 194, 148, 255)
MAT_LIGHT = (238, 224, 186, 255)
MAT_SHADE = (166, 140, 94, 255)
THATCH = (176, 136, 76, 255)
THATCH_LIGHT = (210, 170, 104, 255)
THATCH_SHADE = (134, 98, 52, 255)
THATCH_DARK = (98, 70, 38, 255)
INTERIOR = (52, 38, 30, 255)

# The letter of Afonso I.
WALNUT = (112, 72, 44, 255)
WALNUT_LIGHT = (150, 102, 64, 255)
WALNUT_SHADE = (80, 50, 32, 255)
PAPER = (240, 230, 202, 255)
PAPER_SHADE = (212, 196, 160, 255)
WRITING = (60, 46, 40, 255)
SEAL = (176, 36, 40, 255)
SEAL_LIGHT = (218, 82, 74, 255)
INKPOT = (58, 62, 78, 255)
INKPOT_LIGHT = (104, 110, 128, 255)
QUILL = (246, 242, 232, 255)
QUILL_SHADE = (204, 196, 182, 255)
RIBBON = (150, 40, 44, 255)

# Ndongo and Matamba: the palisade, the chair, the baobab.
STAKE = (132, 96, 62, 255)
STAKE_LIGHT = (170, 128, 84, 255)
STAKE_SHADE = (94, 66, 42, 255)
STAKE_TIP = (198, 162, 116, 255)
CHAIR_WOOD = (70, 42, 28, 255)
CHAIR_LIGHT = (110, 70, 46, 255)
CHAIR_SHADE = (48, 28, 20, 255)
VELVET = (150, 28, 40, 255)
VELVET_LIGHT = (194, 58, 66, 255)
VELVET_SHADE = (104, 18, 30, 255)
BRASS = (216, 172, 72, 255)
BRASS_LIGHT = (250, 222, 140, 255)
BRASS_SHADE = (160, 118, 40, 255)
DAIS = (138, 98, 62, 255)
DAIS_LIGHT = (172, 128, 84, 255)
DAIS_SHADE = (104, 72, 46, 255)
STRAW = (214, 186, 124, 255)
STRAW_LIGHT = (234, 212, 156, 255)
STRAW_SHADE = (170, 140, 86, 255)
BARK = (158, 146, 136, 255)
BARK_LIGHT = (188, 176, 164, 255)
BARK_SHADE = (122, 110, 102, 255)
BARK_DARK = (88, 78, 74, 255)
HOLLOW = (46, 38, 36, 255)
HOLLOW_WATER = (70, 96, 104, 255)
LEAF = (98, 136, 66, 255)
LEAF_LIGHT = (136, 170, 92, 255)
LEAF_SHADE = (68, 102, 50, 255)
POD = (168, 160, 120, 255)
POD_SHADE = (126, 118, 86, 255)

# The Congo river about 1904: quiet, grey-green.
VINE = (100, 76, 54, 255)
VINE_LIGHT = (136, 108, 80, 255)
VINE_SHADE = (70, 52, 38, 255)
GLOSSY = (72, 102, 74, 255)
GLOSSY_LIGHT = (126, 154, 120, 255)
GLOSSY_SHADE = (50, 74, 56, 255)
HOST = (140, 140, 128, 255)
HOST_LIGHT = (170, 170, 156, 255)
HOST_SHADE = (108, 108, 98, 255)
MOSS = (110, 124, 88, 255)
LATEX = (246, 244, 236, 255)
LATEX_SHADE = (214, 210, 198, 255)
CUP = (156, 100, 66, 255)
CUP_LIGHT = (188, 132, 92, 255)
CUP_SHADE = (116, 72, 48, 255)
JAPAN = (38, 36, 40, 255)
JAPAN_LIGHT = (84, 82, 92, 255)
JAPAN_SHADE = (24, 22, 26, 255)
GOLD_LINE = (196, 160, 78, 255)
LENS = (150, 170, 176, 255)
LENS_LIGHT = (220, 236, 238, 255)
GLOW = (255, 214, 140, 255)
OAK = (150, 108, 66, 255)
OAK_LIGHT = (184, 140, 92, 255)
OAK_SHADE = (110, 76, 46, 255)
SLIDE_GLASS = (200, 204, 200, 255)
SLIDE_BORDER = (40, 38, 40, 255)
SLIDE_BLUR = (128, 128, 124, 255)
HULL = (224, 222, 208, 255)
HULL_LIGHT = (242, 240, 230, 255)
HULL_SHADE = (180, 178, 164, 255)
WATERLINE = (50, 48, 46, 255)
DECK = (150, 116, 78, 255)
DECK_LIGHT = (184, 148, 104, 255)
DECK_SHADE = (110, 82, 54, 255)
CANVAS = (210, 204, 182, 255)
CANVAS_LIGHT = (232, 228, 210, 255)
CANVAS_SHADE = (168, 160, 138, 255)
IRON = (66, 66, 70, 255)
IRON_LIGHT = (118, 118, 124, 255)
IRON_SHADE = (44, 44, 48, 255)
FUNNEL = (34, 32, 34, 255)
FUNNEL_LIGHT = (78, 76, 80, 255)
BUCKET = (148, 52, 40, 255)
BUCKET_LIGHT = (184, 86, 66, 255)
LOG_END = (200, 166, 116, 255)
LOG_BARK = (108, 80, 54, 255)
EMBER = (214, 120, 60, 255)
WINDOW = (70, 86, 90, 255)
RIVER = (88, 104, 92, 215)
RIVER_DEEP = (66, 82, 72, 225)
RIPPLE = (168, 182, 168, 255)
FOAM = (226, 230, 222, 255)
SMOKE = (178, 176, 172, 255)
SMOKE_SHADE = (136, 134, 132, 255)


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


def _oval(cx: float, cy: float, length: float, width: float, degrees: float, count: int = 16) -> List[Point]:
    """An ellipse of `length` by `width`, turned by `degrees`."""
    return K.turn(_ring(cx, cy, length / 2.0, width / 2.0, 0.0, 360.0, count), cx, cy, degrees)


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


def _clip(p: Point, d: Point, poly: Sequence[Point]) -> Optional[Tuple[Point, Point]]:
    """The part of the line through `p` with the direction `d` that lies
    inside the convex polygon `poly`, or None."""
    cx = sum(x for x, _ in poly) / len(poly)
    cy = sum(y for _, y in poly) / len(poly)
    t0, t1 = -1e9, 1e9
    for a, b in zip(poly, list(poly[1:]) + [poly[0]]):
        nx, ny = -(b[1] - a[1]), b[0] - a[0]
        if nx * (cx - a[0]) + ny * (cy - a[1]) < 0.0:
            nx, ny = -nx, -ny
        num = nx * (p[0] - a[0]) + ny * (p[1] - a[1])
        den = nx * d[0] + ny * d[1]
        if abs(den) < 1e-9:
            if num < 0.0:
                return None
            continue
        t = -num / den
        if den > 0.0:
            t0 = max(t0, t)
        else:
            t1 = min(t1, t)
    if t0 >= t1:
        return None
    return (p[0] + d[0] * t0, p[1] + d[1] * t0), (p[0] + d[0] * t1, p[1] + d[1] * t1)


def _hatch(f: K.Frame, poly: Sequence[Point], d: Point, spacing: float, colour: RGBA, width: float, offset: float = 0.0) -> None:
    """Parallel lines with the direction `d`, `spacing` apart, inside the
    convex polygon `poly`. Weaves and patterns are made of them."""
    ln = math.hypot(d[0], d[1])
    ux, uy = d[0] / ln, d[1] / ln
    nx, ny = -uy, ux
    cx = sum(x for x, _ in poly) / len(poly)
    cy = sum(y for _, y in poly) / len(poly)
    proj = [(x - cx) * nx + (y - cy) * ny for x, y in poly]
    s = math.floor(min(proj) / spacing) * spacing + offset
    while s <= max(proj):
        seg = _clip((cx + nx * s, cy + ny * s), (ux, uy), poly)
        if seg is not None:
            f.ink(list(seg), width, colour)
        s += spacing


def _puff(f: K.Frame, x: float, y: float, r: float, colour: RGBA, rng: random.Random, lumps: int = 5, shade: Optional[RGBA] = None) -> None:
    """A puff of smoke: round lumps about a middle, with a shade under
    them."""
    for k in range(lumps):
        a = math.tau * k / lumps + rng.uniform(-0.3, 0.3)
        d = r * rng.uniform(0.35, 0.6)
        pr = r * rng.uniform(0.45, 0.65)
        f.ellipse(x + math.cos(a) * d, y + math.sin(a) * d * 0.8, pr, pr, colour)
    if shade is not None:
        f.ellipse(x + r * 0.15, y + r * 0.3, r * 0.55, r * 0.3, shade, body=False)


def _branch(f: K.Frame, pts: Sequence[Point], w0: float, w1: float, fill: RGBA, light: Optional[RGBA] = None) -> None:
    """A branch along `pts` that tapers from the width `w0` to `w1`."""
    count = len(pts) - 1
    for k in range(count):
        wd = _lerp(w0, w1, (k + 0.5) / count)
        f.limb([pts[k], pts[k + 1]], wd, fill)
    if light is not None:
        for k in range(count):
            wd = _lerp(w0, w1, (k + 0.5) / count)
            a, b = pts[k], pts[k + 1]
            f.ink([(a[0] - wd * 0.25, a[1]), (b[0] - wd * 0.25, b[1])], max(0.8, wd * 0.18), light)


# ---------------------------------------------------------------------------
# The Ishango bone.
# ---------------------------------------------------------------------------

#: The notches of the three rows, group by group, as on the real bone.
ISHANGO_ROWS = ((11, 13, 17, 19), (3, 6, 4, 8, 10, 5, 5, 7), (11, 21, 19, 9))


def _draw_ishango_bone(anim: str, i: int, n: int):
    w, h = ISHANGO_BONE_FRAME
    f = K.Frame(ISHANGO_BONE_FRAME)
    rng = random.Random("history_ishango_bone")
    # The flat stone: a pale top face, seen a little from above, on a
    # darker side.
    face = [(8.0, 50.0), (24.0, 42.0), (90.0, 40.0), (146.0, 41.0), (168.0, 47.0), (166.0, 54.0), (134.0, 58.0), (44.0, 59.0), (10.0, 56.0)]
    side = [(10.0, 56.0), (44.0, 59.0), (134.0, 58.0), (166.0, 54.0), (170.0, 63.0), (162.0, 75.0), (20.0, 75.0), (6.0, 64.0)]
    f.poly(side, STONE)
    f.poly([(12.0, 67.0), (164.0, 65.0), (162.0, 75.0), (20.0, 75.0)], STONE_SHADE, body=False)
    f.poly(face, STONE_LIGHT)
    f.ink([(10.0, 56.0), (44.0, 59.0), (134.0, 58.0), (166.0, 54.0)], 0.9, STONE_DARK)
    for x, y, ln in ((30.0, 62.0, 14.0), (100.0, 65.0, 18.0), (140.0, 62.0, 10.0), (64.0, 70.0, 12.0)):
        f.ink([(x, y), (x + ln * 0.5, y + 1.4), (x + ln, y + 0.6)], 0.6, STONE_DARK)
    # The bone: thin and a little curved, thicker at its two ends.
    x0, x1 = 16.0, 158.0

    def centre(u: float) -> Point:
        return (_lerp(x0, x1, u), 41.0 - 7.0 * math.sin(math.pi * u))

    def half(u: float) -> float:
        return 5.8 + 3.0 * (abs(u - 0.5) * 2.0) ** 5

    us = [k / 48.0 for k in range(49)]
    upper = [(centre(u)[0], centre(u)[1] - half(u)) for u in us]
    lower = [(centre(u)[0], centre(u)[1] + half(u)) for u in us]
    # The left end is broken and rough; the right end is the knob that
    # holds the quartz.
    left_end = [(x0 - 1.6, centre(0.0)[1] + 4.0), (x0 - 3.0, centre(0.0)[1] + 1.0), (x0 - 1.0, centre(0.0)[1] - 2.0), (x0 - 2.6, centre(0.0)[1] - 5.0)]
    right_end = _ring(x1, centre(1.0)[1], 3.6, half(1.0), -90.0, 90.0, 10)
    f.poly(upper + right_end + list(reversed(lower)) + left_end, FOSSIL)
    f.poly([(x, y + 1.0) for x, y in lower] + [(centre(u)[0], centre(u)[1] + half(u) * 0.45) for u in reversed(us)], FOSSIL_SHADE, body=False)
    f.ink([(x, y + 1.2) for x, y in upper[2:-2]], 1.0, FOSSIL_LIGHT)
    # The quartz chip, set in a groove in the end of the bone.
    qx, qy = x1 + 2.0, centre(1.0)[1] - 2.0
    f.poly([(qx - 3.0, qy + 2.0), (qx + 1.0, qy - 6.0), (qx + 6.0, qy - 8.0), (qx + 10.0, qy - 2.0), (qx + 7.0, qy + 4.0), (qx + 1.0, qy + 5.0)], QUARTZ)
    f.poly([(qx + 6.0, qy - 8.0), (qx + 10.0, qy - 2.0), (qx + 7.0, qy + 4.0), (qx + 5.0, qy - 2.0)], QUARTZ_SHADE, body=False)
    f.ink([(qx + 1.0, qy - 5.0), (qx + 5.0, qy - 2.0), (qx + 1.6, qy + 3.6)], 0.6, QUARTZ_SHADE)
    f.ink([(qx + 2.0, qy - 4.6), (qx + 5.4, qy - 6.8)], 0.8, QUARTZ_LIGHT)
    f.ink([(qx - 2.0, qy + 2.0), (qx - 1.0, qy - 2.0)], 1.2, FOSSIL_SHADE)
    # The three rows of notches. Each group is a run of short cuts, and a
    # gap divides the groups. The three rows fill the same length.
    s = 1.76
    for row, groups in enumerate(ISHANGO_ROWS):
        off = (-3.9, 0.0, 3.9)[row]
        total = sum(groups) * s + (len(groups) - 1) * 2.4 * s
        x = (x0 + x1) / 2.0 - 2.0 - total / 2.0
        for g in groups:
            for _ in range(g):
                u = (x - x0) / (x1 - x0)
                cy = centre(u)[1] + off * half(u) / 5.8
                tilt = rng.uniform(-0.3, 0.3)
                f.ink([(x - 0.3 + tilt, cy - 1.5), (x + 0.3 - tilt, cy + 1.5)], 0.7, NOTCH)
                x += s
            x += 2.4 * s
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# The harpoon rack.
# ---------------------------------------------------------------------------


def _harpoon(f: K.Frame, x: float, y: float, length: float, barbs: Sequence[float], rng: random.Random) -> None:
    """A barbed bone harpoon point that hangs point down from `(x, y)`.
    `barbs` names the sides (-1 left, 1 right) that carry a row of barbs.
    The barbs point back, up to the base."""
    tip = (x + rng.uniform(-0.6, 0.6), y + length)
    hw = 2.6
    body = [(x - hw + 0.6, y), (x + hw - 0.6, y), (x + hw, y + 6.0), (x + hw, y + length * 0.72), (tip[0] + 0.6, tip[1] - 2.0), tip,
            (tip[0] - 0.6, tip[1] - 2.0), (x - hw, y + length * 0.72), (x - hw, y + 6.0)]
    for side in barbs:
        for k in range(4):
            by = y + length * (0.3 + 0.13 * k)
            ex = x + side * hw
            f.poly([(ex, by + 4.0), (ex + side * 2.8, by - 1.2), (ex, by + 0.6)], BONE_PALE)
            f.ink([(ex + side * 0.4, by + 3.2), (ex + side * 2.2, by - 0.4)], 0.5, BONE_SHADE)
    f.poly(body, BONE_PALE)
    f.poly([(x + 0.6, y + 2.0), (x + hw - 0.4, y + 6.0), (x + hw - 0.4, y + length * 0.72), (tip[0] + 0.3, tip[1] - 3.0)], BONE_SHADE, body=False)
    f.ink([(x - 1.2, y + 3.0), (x - 1.2, y + length * 0.7)], 0.7, BONE_LIGHT)
    # The base is ringed with grooves where it was bound to its shaft.
    for k in range(2):
        f.ink([(x - hw, y + 3.0 + k * 2.4), (x + hw, y + 3.0 + k * 2.4)], 0.6, BONE_SHADE)


def _fish(f: K.Frame, x: float, y: float, length: float, rng: random.Random) -> None:
    """A split fish that dries, hung by its tail from `(x, y)`."""
    head = y + length
    body = [(x, y + 6.0)]
    for k in range(1, 12):
        u = k / 11.0
        body.append((x + 5.2 * math.sin(math.pi * min(1.0, u * 1.08)) ** 0.8, y + 6.0 + (length - 6.0) * u))
    for k in range(10, 0, -1):
        u = k / 11.0
        body.append((x - 4.6 * math.sin(math.pi * min(1.0, u * 1.08)) ** 0.8, y + 6.0 + (length - 6.0) * u))
    f.poly([(x - 1.0, y + 7.0), (x - 5.0, y), (x, y + 3.0), (x + 5.0, y), (x + 1.0, y + 7.0)], FISH_SHADE)
    f.poly(body, FISH)
    f.poly([(x + 0.6, y + 8.0)] + [(x + 4.6 * math.sin(math.pi * min(1.0, k / 11.0 * 1.08)) ** 0.8, y + 6.0 + (length - 6.0) * k / 11.0) for k in range(2, 11)]
           + [(x + 1.0, head - 4.0)], FISH_SHADE, body=False)
    f.ink([(x - 2.0, y + 9.0), (x - 2.0, head - 6.0)], 0.8, FISH_LIGHT)
    f.dot(x - 0.6, head - 4.0, 1.0, FISH_SHADE)
    for k in range(3):
        yy = y + 12.0 + k * 5.0
        f.ink([(x - 3.0, yy), (x + 3.0, yy + 1.6)], 0.5, FISH_SHADE)
    del rng


def _lash(f: K.Frame, x: float, y: float, size: float) -> None:
    """A lashing of fibre cord where two poles cross."""
    f.ink([(x - size, y - size), (x + size, y + size)], 1.4, FIBRE_DARK)
    f.ink([(x - size, y + size), (x + size, y - size)], 1.4, FIBRE)
    f.ink([(x - size * 0.6, y - size * 0.9), (x + size * 0.9, y + size * 0.6)], 0.6, FIBRE)


def _draw_bone_harpoons(anim: str, i: int, n: int):
    w, h = BONE_HARPOONS_FRAME
    f = K.Frame(BONE_HARPOONS_FRAME)
    rng = random.Random("history_bone_harpoons")
    ground = h - 8.0
    top, low = 32.0, 92.0
    # Two forked uprights hold the top pole. A lower pole is lashed to them.
    for x, lean in ((20.0, -1.0), (140.0, 1.0)):
        f.limb([(x + lean * 2.0, ground), (x, top + 4.0)], 5.0, POLE)
        f.ink([(x + lean * 2.0 - 1.0, ground - 2.0), (x - 1.0, top + 6.0)], 1.0, POLE_LIGHT)
        f.limb([(x, top + 6.0), (x - 6.0, top - 10.0)], 3.4, POLE)
        f.limb([(x, top + 6.0), (x + 6.0, top - 9.0)], 3.4, POLE_SHADE)
    f.limb([(8.0, top), (152.0, top - 1.0)], 4.6, POLE)
    f.ink([(10.0, top - 1.2), (150.0, top - 2.2)], 0.9, POLE_LIGHT)
    f.limb([(12.0, low), (148.0, low + 1.0)], 4.0, POLE_SHADE)
    f.ink([(14.0, low - 1.0), (146.0, low)], 0.8, POLE)
    for x, y in ((20.0, top + 1.0), (140.0, top), (20.0, low), (140.0, low + 1.0)):
        _lash(f, x, y, 3.0)
    # The harpoon points hang by cords from the top pole.
    for x, ln, barbs in ((40.0, 44.0, (1.0,)), (60.0, 40.0, (-1.0, 1.0)), (80.0, 46.0, (1.0,)), (100.0, 38.0, (-1.0,)), (120.0, 44.0, (-1.0, 1.0))):
        f.ink([(x, top + 1.0), (x, top + 7.0)], 1.0, FIBRE_DARK)
        f.ellipse(x, top + 1.4, 1.8, 2.4, FIBRE)
        _harpoon(f, x, top + 7.0, ln, barbs, rng)
        f.ink([(x - 2.4, top + 8.6), (x + 2.4, top + 9.4)], 1.0, FIBRE_DARK)
    # The fish hang by their tails from the lower pole.
    for x, ln in ((44.0, 40.0), (80.0, 46.0), (116.0, 38.0)):
        f.ink([(x, low + 1.0), (x, low + 5.0)], 1.0, FIBRE_DARK)
        _fish(f, x, low + 4.0, ln, rng)
    # A little ground at the feet of the poles.
    for x in (20.0, 140.0):
        f.poly([(x - 10.0, ground + 2.0), (x - 4.0, ground - 2.0), (x + 4.0, ground - 2.0), (x + 10.0, ground + 2.0)], GROUND)
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# The raffia loom.
# ---------------------------------------------------------------------------


def _cloth_pattern(f: K.Frame, x0: float, y0: float, x1: float, y1: float) -> None:
    """Kongo raffia cloth: a tan square with a border of lines and a field
    of interlaced diamonds in dark brown, a dot in each diamond."""
    f.poly(_rect(x0, y0, x1, y1), CLOTH)
    for y in (y0 + 2.0, y0 + 4.4, y1 - 4.4, y1 - 2.0):
        f.ink([(x0 + 1.0, y), (x1 - 1.0, y)], 0.8, CLOTH_DARK)
    for x in (x0 + 2.0, x1 - 2.0):
        f.ink([(x, y0 + 1.0), (x, y1 - 1.0)], 0.8, CLOTH_DARK)
    field = _rect(x0 + 4.0, y0 + 7.0, x1 - 4.0, y1 - 7.0)
    f.poly(field, CLOTH_LIGHT, body=False)
    sp = 10.0
    for d in ((1.0, 1.0), (1.0, -1.0)):
        _hatch(f, field, d, sp, CLOTH_DARK, 1.2)
        _hatch(f, field, d, sp, CLOTH_DARK, 0.6, 2.4)
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    for gx in range(-3, 4):
        for gy in range(-3, 4):
            px = cx + gx * sp / math.sqrt(2.0) + sp / (2.0 * math.sqrt(2.0)) * 0.0
            py = cy + gy * sp / math.sqrt(2.0)
            if (gx + gy) % 2 == 0 and x0 + 7.0 < px < x1 - 7.0 and y0 + 9.0 < py < y1 - 9.0:
                f.dot(px, py, 1.0, CLOTH_RED)


def _draw_raffia_loom(anim: str, i: int, n: int):
    w, h = RAFFIA_LOOM_FRAME
    f = K.Frame(RAFFIA_LOOM_FRAME)
    rng = random.Random("history_raffia_loom")
    ground = h - 6.0
    # The forked post behind the loom: the top beam rests in its fork.
    f.limb([(72.0, ground - 2.0), (72.0, 22.0)], 7.0, POLE_SHADE)
    f.limb([(72.0, 24.0), (62.0, 10.0)], 4.0, POLE_SHADE)
    f.limb([(72.0, 24.0), (82.0, 11.0)], 4.0, POLE_SHADE)
    # The two side poles of the frame. They lean back on the post, so the
    # frame is a little narrower at the top.
    top_y, beam_y = 28.0, 156.0
    for xa, xb in ((26.0, 38.0), (118.0, 106.0)):
        f.limb([(xa, ground), (xb, 16.0)], 5.0, POLE)
        f.ink([(xa - 1.0, ground - 2.0), (xb - 1.0, 18.0)], 0.9, POLE_LIGHT)
    # The warp: pale raffia fibres from the top beam down to the cloth.
    panel_top = 98.0
    wl, wr = 44.0, 100.0
    pl, pr = 40.0, 104.0
    f.poly([(wl, top_y), (wr, top_y), (pr, panel_top), (pl, panel_top)], RAFFIA_SHADE)
    count = 26
    for k in range(count + 1):
        u = k / float(count)
        a = (_lerp(wl, wr, u), top_y + 2.0)
        b = (_lerp(pl, pr, u), panel_top)
        f.ink([a, b], 0.9, RAFFIA if k % 2 else RAFFIA_LIGHT)
    # The top beam, lashed into the fork of the post and to the poles.
    f.limb([(30.0, top_y), (114.0, top_y)], 5.0, POLE)
    f.ink([(32.0, top_y - 1.2), (112.0, top_y - 1.2)], 0.9, POLE_LIGHT)
    for x in (37.0, 72.0, 107.0):
        _lash(f, x, top_y, 2.6)
    # The shed rod holds the warp open; under it, the heddle rod lifts
    # every other fibre on a loop of string.
    f.limb([(36.0, 48.0), (108.0, 48.0)], 4.0, POLE_LIGHT)
    f.ink([(37.0, 47.0), (107.0, 47.0)], 0.8, (190, 150, 104, 255))
    hy = 68.0
    for k in range(1, count, 2):
        u = k / float(count)
        x = _lerp(_lerp(wl, pl, (hy - top_y) / (panel_top - top_y)), _lerp(wr, pr, (hy - top_y) / (panel_top - top_y)), u)
        f.ink([(x - 0.8, hy), (x, hy + 4.0), (x + 0.8, hy)], 0.5, FIBRE_DARK)
    f.limb([(34.0, hy), (110.0, hy)], 2.6, POLE_SHADE)
    # The woven panel: square, with its border and its diamonds.
    _cloth_pattern(f, pl, panel_top, pr, panel_top + 56.0)
    f.ink([(pl, panel_top), (pr, panel_top)], 1.0, RAFFIA_SHADE)
    # The beater: a flat wooden sword in the shed, just over the cloth.
    by = 88.0
    f.poly([(32.0, by - 2.0), (112.0, by - 2.4), (116.0, by), (112.0, by + 2.4), (32.0, by + 2.0)], WALNUT_LIGHT)
    f.ink([(34.0, by - 0.8), (110.0, by - 1.0)], 0.6, (196, 150, 104, 255))
    f.limb([(116.0, by), (128.0, by + 1.0)], 3.0, WALNUT)
    # The cloth beam at the bottom, lashed to the poles.
    f.limb([(24.0, beam_y), (120.0, beam_y)], 5.0, POLE)
    f.ink([(26.0, beam_y - 1.2), (118.0, beam_y - 1.2)], 0.9, POLE_LIGHT)
    for x in (28.0, 116.0):
        _lash(f, x, beam_y, 2.6)
    # A hank of raffia hangs from the left pole, ready to use.
    hx, hy0 = 22.0, 62.0
    f.ellipse(hx + 6.0, hy0, 3.0, 2.4, RAFFIA_SHADE)
    for k in range(9):
        x = hx + 2.0 + k * 1.1 + rng.uniform(-0.4, 0.4)
        f.limb([(hx + 6.0, hy0), (x, hy0 + 26.0 + rng.uniform(-3.0, 3.0))], 1.0, RAFFIA if k % 2 else RAFFIA_LIGHT)
    f.ink([(hx + 3.0, hy0 + 4.0), (hx + 9.0, hy0 + 4.0)], 1.0, FIBRE_DARK)
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# The basket of nzimbu.
# ---------------------------------------------------------------------------


def _nzimbu(f: K.Frame, x: float, y: float, degrees: float, size: float, fill: RGBA) -> None:
    """One nzimbu shell: smooth and olive-shaped, with a small pointed
    spire at one end and a long narrow slit along one side."""
    body = _oval(x, y, 6.0 * size, 3.2 * size, degrees, 14)
    a = math.radians(degrees)
    ux, uy = math.cos(a), math.sin(a)
    tip = (x + ux * 3.9 * size, y + uy * 3.9 * size)
    nx, ny = -uy, ux
    f.poly([(x + ux * 2.2 * size + nx * 1.2 * size, y + uy * 2.2 * size + ny * 1.2 * size), tip,
            (x + ux * 2.2 * size - nx * 1.2 * size, y + uy * 2.2 * size - ny * 1.2 * size)], K.shade(fill, 0.86))
    f.poly(body, fill)
    f.ink(body, 0.45 * size, SHELL_SHADE)
    f.ink([(x - ux * 2.0 * size + nx * 0.7 * size, y - uy * 2.0 * size + ny * 0.7 * size), (x + ux * 1.2 * size + nx * 0.9 * size, y + uy * 1.2 * size + ny * 0.9 * size)],
          0.4 * size, K.shade(fill, 0.8))
    f.dot(x - ux * 0.6 * size - nx * 0.6 * size, y - uy * 0.6 * size - ny * 0.6 * size, 0.55 * size, SHELL_GLOSS)


def _draw_nzimbu_basket(anim: str, i: int, n: int):
    w, h = NZIMBU_BASKET_FRAME
    f = K.Frame(NZIMBU_BASKET_FRAME)
    rng = random.Random("history_nzimbu_basket")
    ground = h - 6.0
    cx, rim = 48.0, 36.0
    shells = (SHELL, SHELL_TAN, SHELL_GREY, SHELL, SHELL_TAN)
    # The heap of shells over the rim: a low dome. The back rows go first.
    for row in range(5):
        y = rim - 3.0 - row * 3.6
        half = 31.0 * math.sqrt(max(0.0, 1.0 - (row / 5.2) ** 2))
        x = cx - half + 3.0
        while x < cx + half - 3.0:
            _nzimbu(f, x + rng.uniform(-0.8, 0.8), y + rng.uniform(-0.8, 0.8), rng.uniform(-40.0, 40.0) + rng.choice((0.0, 180.0)), 1.4, rng.choice(shells))
            x += rng.uniform(6.4, 7.6)
    for row in range(2):
        y = rim + 0.5 - row * 2.4
        x = cx - 29.0 + row * 3.0
        while x < cx + 30.0:
            _nzimbu(f, x + rng.uniform(-0.6, 0.6), y, rng.uniform(-25.0, 25.0) + rng.choice((0.0, 180.0)), 1.4, rng.choice(shells))
            x += rng.uniform(6.2, 7.2)
    # The basket: a coiled basket, wide at the rim and narrower at its foot.
    def radius(y: float) -> float:
        u = (y - rim) / (ground - rim)
        return _lerp(36.0, 26.0, u ** 1.4)

    ys = [_lerp(rim, ground, k / 12.0) for k in range(13)]
    f.poly([(cx + radius(y), y) for y in ys] + [(cx - radius(y), y) for y in reversed(ys)], BASKET)
    f.poly([(cx + radius(y) * 0.45, y) for y in ys] + [(cx + radius(y) - 0.6, y) for y in reversed(ys)], BASKET_SHADE, body=False)
    f.ink([(cx - radius(y) + 4.0, y) for y in ys[1:-2]], 1.2, BASKET_LIGHT)
    # The coils run round the basket; short stitches bind each coil to the
    # one under it.
    y = rim + 4.0
    row = 0
    while y < ground - 1.0:
        r = radius(y)
        f.ink(_ring(cx, y - 1.2, r - 0.4, 1.4, 0.0, 180.0, 16), 0.7, BASKET_SHADE)
        for k in range(14):
            a = math.radians(10.0 + k * 12.0 + (6.0 if row % 2 else 0.0))
            sx = cx + math.cos(a) * (r - 0.6)
            f.ink([(sx, y - 3.0), (sx + 0.8, y - 0.4)], 0.5, BASKET_LIGHT)
        y += 4.0
        row += 1
    # The rim: a thick round coil.
    f.limb(_ring(cx, rim + 1.0, 36.0, 4.0, 0.0, 180.0, 20), 3.0, BASKET)
    f.ink(_ring(cx, rim + 0.4, 36.0, 4.0, 20.0, 160.0, 16), 0.8, BASKET_LIGHT)
    # A few shells spilled on the ground beside the basket.
    for x, y, a in ((88.0, ground - 2.6, 20.0), (96.0, ground - 2.4, 160.0), (101.0, ground - 6.0, 70.0), (92.0, ground - 6.4, 130.0)):
        _nzimbu(f, x, y, a, 1.3, rng.choice(shells))
    return A.finish(f, width=1.1)


# ---------------------------------------------------------------------------
# The letter of Afonso I.
# ---------------------------------------------------------------------------


def _turned_leg(f: K.Frame, x: float, y0: float, y1: float, wood: RGBA, light: RGBA, shade: RGBA, width: float = 4.0) -> None:
    """A turned leg: a round post with a knob and a ring or two."""
    f.limb([(x, y0), (x, y1)], width, wood)
    span = y1 - y0
    for u, r in ((0.12, 1.0), (0.4, 1.7), (0.62, 1.2), (0.9, 1.4)):
        f.ellipse(x, y0 + span * u, width * 0.5 * r + 0.6, 2.2 * r, wood)
    f.ink([(x - width * 0.25, y0 + 1.0), (x - width * 0.25, y1 - 1.0)], 0.7, light)
    f.ink([(x + width * 0.3, y0 + 1.0), (x + width * 0.3, y1 - 1.0)], 0.6, shade)


def _draw_afonso_letter(anim: str, i: int, n: int):
    w, h = AFONSO_LETTER_FRAME
    f = K.Frame(AFONSO_LETTER_FRAME)
    rng = random.Random("history_afonso_letter")
    ground = h - 7.0
    ttop = 64.0
    # The table: a plain board on an apron, turned legs and a stretcher.
    for x in (22.0, 106.0):
        _turned_leg(f, x, ttop + 10.0, ground, WALNUT, WALNUT_LIGHT, WALNUT_SHADE, 4.6)
    f.limb([(22.0, ground - 8.0), (106.0, ground - 8.0)], 3.0, WALNUT_SHADE)
    f.poly(_rect(16.0, ttop + 4.0, 112.0, ttop + 11.0), WALNUT)
    f.ink([(18.0, ttop + 9.6), (110.0, ttop + 9.6)], 0.7, WALNUT_SHADE)
    f.poly(_rect(10.0, ttop - 1.0, 118.0, ttop + 4.0), WALNUT_LIGHT)
    f.ink([(11.0, ttop), (117.0, ttop)], 0.8, (186, 136, 92, 255))
    # The writing slope: its sloped face turns to us, and the open letter
    # lies on it.
    f.poly([(16.0, ttop - 1.0), (76.0, ttop - 1.0), (76.0, ttop - 6.0), (72.0, ttop - 34.0), (20.0, ttop - 34.0), (16.0, ttop - 6.0)], WALNUT)
    f.poly(_rect(16.0, ttop - 6.0, 76.0, ttop - 1.0), WALNUT_SHADE, body=False)
    f.ink([(17.0, ttop - 5.2), (75.0, ttop - 5.2)], 0.7, WALNUT_LIGHT)
    sheet = [(22.0, ttop - 8.0), (70.0, ttop - 8.0), (68.0, ttop - 33.0), (24.0, ttop - 33.0)]
    f.poly(sheet, PAPER)
    f.poly([(22.0, ttop - 8.0), (70.0, ttop - 8.0), (69.6, ttop - 12.0), (22.4, ttop - 12.0)], PAPER_SHADE, body=False)
    for k in range(5):
        y = ttop - 29.0 + k * 3.8
        _writing_line(f, 27.0 + k * 0.1, 65.0 - k * 0.1 - (12.0 if k == 4 else 0.0), y, rng, WRITING, 1.0)
    # The seal of red wax at the foot of the letter.
    f.ellipse(58.0, ttop - 10.6, 3.2, 2.4, SEAL)
    f.dot(57.2, ttop - 11.4, 1.0, SEAL_LIGHT)
    # The inkwell and the quill that stands in it.
    ix = 100.0
    f.poly([(ix - 6.0, ttop - 1.0), (ix - 6.0, ttop - 7.0), (ix - 3.0, ttop - 10.0), (ix + 3.0, ttop - 10.0), (ix + 6.0, ttop - 7.0), (ix + 6.0, ttop - 1.0)], INKPOT)
    f.poly(_rect(ix - 3.0, ttop - 13.0, ix + 3.0, ttop - 10.0), INKPOT)
    f.ink([(ix - 4.0, ttop - 8.0), (ix - 4.0, ttop - 3.0)], 0.8, INKPOT_LIGHT)
    qb, qt = (ix + 1.0, ttop - 12.0), (ix + 14.0, ttop - 50.0)
    vane = []
    for k in range(9):
        u = 0.3 + 0.7 * k / 8.0
        p = _mix(qb, qt, u)
        vane.append((p[0] + 3.4 * math.sin(math.pi * (u - 0.3) / 0.7) ** 0.6, p[1] + 1.0))
    back = [(_mix(qb, qt, u)[0] - 1.6 * math.sin(math.pi * (u - 0.3) / 0.7) ** 0.6, _mix(qb, qt, u)[1]) for u in (1.0, 0.85, 0.7, 0.55, 0.4, 0.3)]
    f.poly(vane + back, QUILL)
    for k in range(4):
        p = _mix(qb, qt, 0.4 + k * 0.14)
        f.ink([p, (p[0] + 3.0, p[1] + 2.4)], 0.5, QUILL_SHADE)
    f.ink([_mix(qb, qt, 0.3), qt], 0.7, QUILL_SHADE)
    f.limb([(ix + 0.6, ttop - 10.0), _mix(qb, qt, 0.34)], 1.2, QUILL_SHADE)
    # A second letter, rolled and tied with a ribbon.
    rx0, rx1, ry = 78.0, 94.0, ttop - 3.4
    f.poly(_rect(rx0, ry - 2.6, rx1, ry + 2.6), PAPER)
    f.ink([(rx0, ry + 1.6), (rx1, ry + 1.6)], 0.7, PAPER_SHADE)
    f.ellipse(rx1, ry, 1.6, 2.6, PAPER_SHADE)
    f.ink(_ring(rx1, ry, 0.8, 1.4, 0.0, 300.0, 8), 0.4, WRITING)
    f.limb([(86.0, ry - 2.8), (86.0, ry + 2.8)], 1.2, RIBBON)
    f.ink([(86.0, ry + 2.6), (84.0, ry + 4.4)], 0.8, RIBBON)
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# The house of Mbanza Kongo.
# ---------------------------------------------------------------------------


def _mat_panel(f: K.Frame, poly: Sequence[Point], spacing: float = 4.6) -> None:
    """A panel of woven palm mat: a diagonal weave in two shades."""
    f.poly(poly, MAT)
    _hatch(f, poly, (1.0, 1.0), spacing, MAT_SHADE, 0.8)
    _hatch(f, poly, (1.0, -1.0), spacing, MAT_LIGHT, 0.8, spacing / 2.0)


def _draw_kongo_house(anim: str, i: int, n: int):
    w, h = KONGO_HOUSE_FRAME
    f = K.Frame(KONGO_HOUSE_FRAME)
    rng = random.Random("history_kongo_house")
    ground = h - 6.0
    wx0, wx1, wtop = 26.0, 170.0, 138.0
    depth = (54.0, -27.0)
    # The gable end, seen at an angle: a wall of mat to the apex.
    bx, by = wx1 + depth[0], wtop + depth[1]
    apex = (wx1 + depth[0] / 2.0, 36.0)
    _mat_panel(f, [(wx1, ground), (wx1, wtop), apex, (bx, by), (bx, ground + depth[1])], 5.0)
    f.poly([(wx1, ground), (bx, ground + depth[1]), (bx, ground + depth[1] - 6.0), (wx1, ground - 6.0)], K.alpha(MAT_SHADE, 0.7), body=False)
    mid_low = (apex[0], ground + depth[1] / 2.0)
    f.limb([mid_low, (apex[0], apex[1] + 4.0)], 3.0, POLE)
    f.limb([(wx1, 178.0), (bx, 178.0 + depth[1])], 3.0, POLE)
    f.limb([(bx, ground + depth[1]), (bx, by)], 3.4, POLE)
    # The far slope of the roof shows its edge over the gable.
    f.poly([(apex[0] + 8.0, 22.0), (bx + 16.0, by + 8.0), (bx + 10.0, by + 11.0), (bx, by), apex], THATCH_SHADE)
    f.ink([(apex[0] + 9.0, 25.0), (bx + 13.0, by + 8.0)], 0.8, THATCH_DARK)
    # The front wall: squares of mat framed by poles, and a low door.
    rail = 178.0
    posts = [wx0 + k * (wx1 - wx0) / 4.0 for k in range(5)]
    for k in range(4):
        for ya, yb in ((wtop, rail), (rail, ground)):
            _mat_panel(f, _rect(posts[k], ya, posts[k + 1], yb))
    f.poly(_rect(wx0, ground - 6.0, wx1, ground), K.alpha(MAT_SHADE, 0.7), body=False)
    dx0, dx1, dtop = 86.0, 110.0, 162.0
    f.poly(_rect(dx0, dtop, dx1, ground), INTERIOR)
    f.poly(_rect(dx0, dtop, dx1, dtop + 6.0), (36, 26, 22, 255), body=False)
    f.limb([(wx0, rail), (dx0, rail)], 3.0, POLE)
    f.limb([(dx1, rail), (wx1, rail)], 3.0, POLE)
    for x in posts:
        if abs(x - (dx0 + dx1) / 2.0) < 4.0:
            f.limb([(x, wtop), (x, dtop - 2.0)], 3.2, POLE)
        else:
            f.limb([(x, ground), (x, wtop)], 3.6 if x in (wx0, wx1) else 3.2, POLE)
            f.ink([(x - 0.8, ground - 1.0), (x - 0.8, wtop + 2.0)], 0.7, POLE_LIGHT)
    for x in (dx0, dx1):
        f.limb([(x, ground), (x, dtop)], 3.2, POLE)
    f.limb([(dx0 - 4.0, dtop), (dx1 + 4.0, dtop)], 3.4, POLE)
    f.ink([(dx0 - 3.0, dtop - 0.8), (dx1 + 3.0, dtop - 0.8)], 0.7, POLE_LIGHT)
    # The near slope of the roof: steep, thatched in courses, from the
    # eaves to the ridge.
    ex0, ex1, ey = 14.0, 182.0, 146.0
    ry = 22.0

    def left(y: float) -> float:
        return ex0 + (ey - y) / (ey - ry) * depth[0] / 2.0

    def right(y: float) -> float:
        return ex1 + (ey - y) / (ey - ry) * depth[0] / 2.0

    slope = [(ex0, ey), (ex1, ey), (right(ry), ry), (left(ry), ry)]
    f.poly(slope, THATCH)
    _thatch_rows(f, left, right, ry + 4.0, ey - 2.0, 8.0, rng, THATCH_LIGHT, THATCH_SHADE)
    f.poly([(ex0, ey), (ex1, ey), (right(ey - 6.0), ey - 6.0), (left(ey - 6.0), ey - 6.0)], THATCH_SHADE, body=False)
    for k in range(40):
        x = ex0 + 2.0 + k * (ex1 - ex0 - 4.0) / 39.0
        f.ink([(x, ey - 5.0), (x + rng.uniform(-0.6, 0.6), ey + rng.uniform(0.5, 2.0))], 0.7, THATCH_DARK)
    # The gable edge of the near slope: a thick band of thatch.
    f.limb([(ex1 - 1.0, ey - 1.0), (right(ry) - 1.0, ry + 2.0)], 4.0, THATCH_SHADE)
    f.ink([(ex1 - 2.0, ey - 2.0), (right(ry) - 2.0, ry + 3.0)], 0.8, THATCH_LIGHT)
    # The ridge: a roll of thatch bound at intervals.
    f.limb([(left(ry) - 2.0, ry), (right(ry) + 2.0, ry)], 7.0, THATCH_SHADE)
    f.ink([(left(ry), ry - 1.6), (right(ry), ry - 1.6)], 1.0, THATCH_LIGHT)
    for k in range(9):
        x = left(ry) + 6.0 + k * (right(ry) - left(ry) - 12.0) / 8.0
        f.ink([(x, ry - 3.4), (x + 0.6, ry + 3.4)], 1.0, THATCH_DARK)
    for x, s in ((left(ry) - 2.0, -1.0), (right(ry) + 2.0, 1.0)):
        f.limb([(x, ry), (x + s * 5.0, ry - 7.0)], 2.4, THATCH_SHADE)
    # The ends of the rafters show under the eaves.
    for x in (30.0, 64.0, 100.0, 136.0, 168.0):
        f.limb([(x, ey - 3.0), (x - 3.0, ey + 5.0)], 2.6, POLE_SHADE)
    return A.finish(f, width=1.3)


# ---------------------------------------------------------------------------
# The gate of a kilombo.
# ---------------------------------------------------------------------------


def _stake(f: K.Frame, x: float, top: float, bottom: float, width: float, rng: random.Random) -> None:
    """A sharpened stake: a pole with a pointed top cut on two faces."""
    hw = width / 2.0
    lean = rng.uniform(-0.6, 0.6)
    point = top - width * 1.2
    f.poly([(x - hw, bottom), (x - hw + lean, top), (x + lean * 1.5, point), (x + hw + lean, top), (x + hw, bottom)],
           STAKE if rng.random() < 0.6 else K.shade(STAKE, 0.9))
    f.poly([(x + lean * 1.5, point), (x + hw + lean, top), (x + lean * 0.5, top + 1.0)], STAKE_TIP, body=False)
    f.poly([(x + hw * 0.3, bottom), (x + hw * 0.3 + lean, top + 1.0), (x + hw + lean, top), (x + hw, bottom)], STAKE_SHADE, body=False)
    f.ink([(x - hw * 0.5, bottom - 2.0), (x - hw * 0.5 + lean, top + 2.0)], 0.7, STAKE_LIGHT)
    for _ in range(2):
        y = rng.uniform(top + 10.0, bottom - 10.0)
        f.ink([(x - hw * 0.4, y), (x + hw * 0.2, y + 2.0)], 0.6, STAKE_SHADE)


def _draw_kilombo_gate(anim: str, i: int, n: int):
    w, h = KILOMBO_GATE_FRAME
    f = K.Frame(KILOMBO_GATE_FRAME)
    rng = random.Random("history_kilombo_gate")
    ground = h - 7.0
    deck = 112.0
    # The lookout: four poles (two show) rise behind the palisade to a
    # platform and a small roof of thatch.
    lx0, lx1 = 176.0, 230.0
    for x in (lx0, lx1):
        f.limb([(x, ground - 20.0), (x, 66.0)], 5.0, POLE)
        f.ink([(x - 1.2, ground - 22.0), (x - 1.2, 68.0)], 0.9, POLE_LIGHT)
    f.limb([(lx0, deck + 30.0), (lx1, deck + 4.0)], 3.0, POLE_SHADE)
    f.limb([(lx1, deck + 30.0), (lx0, deck + 4.0)], 3.0, POLE_SHADE)
    f.poly(_rect(lx0 - 12.0, deck - 2.0, lx1 + 12.0, deck + 5.0), POLE_LIGHT)
    for k in range(9):
        x = lx0 - 10.0 + k * 9.0
        f.ink([(x, deck - 1.6), (x, deck + 4.6)], 0.6, POLE_SHADE)
    f.limb([(lx0 - 10.0, deck - 18.0), (lx1 + 10.0, deck - 18.0)], 2.6, POLE)
    for x in (lx0 - 10.0, lx0 + 18.0, lx1 - 18.0, lx1 + 10.0):
        f.limb([(x, deck - 2.0), (x, deck - 18.0)], 2.0, POLE)
    _lash(f, lx0, deck - 18.0, 2.4)
    _lash(f, lx1, deck - 18.0, 2.4)
    roof = [(lx0 - 16.0, 72.0), (lx1 + 16.0, 72.0), ((lx0 + lx1) / 2.0 + 4.0, 26.0), ((lx0 + lx1) / 2.0 - 4.0, 26.0)]
    f.poly(roof, THATCH)
    rcx = (lx0 + lx1) / 2.0

    def rl(y: float) -> float:
        return _lerp(rcx - 4.0, lx0 - 16.0, (y - 26.0) / 46.0)

    def rr(y: float) -> float:
        return _lerp(rcx + 4.0, lx1 + 16.0, (y - 26.0) / 46.0)

    _thatch_rows(f, rl, rr, 30.0, 70.0, 7.0, rng, THATCH_LIGHT, THATCH_SHADE)
    f.poly([(lx0 - 16.0, 72.0), (lx1 + 16.0, 72.0), (rr(66.0), 66.0), (rl(66.0), 66.0)], THATCH_SHADE, body=False)
    for k in range(24):
        x = lx0 - 14.0 + k * (lx1 - lx0 + 28.0) / 23.0
        f.ink([(x, 67.0), (x + rng.uniform(-0.6, 0.6), 74.0)], 0.7, THATCH_DARK)
    f.limb([(rcx - 5.0, 25.0), (rcx + 5.0, 25.0)], 4.0, THATCH_SHADE)
    # The palisade: sharpened stakes side by side, on both sides of the
    # gate.
    for xa, xb in ((10.0, 88.0), (168.0, 248.0)):
        x = xa + 5.0
        while x <= xb - 4.0:
            _stake(f, x, rng.uniform(150.0, 166.0), ground, 10.0, rng)
            x += 9.6
    # The gateposts: two thick posts, taller than the palisade, with a
    # pole lashed across their tops.
    gx0, gx1 = 96.0, 160.0
    for x in (gx0, gx1):
        _stake(f, x, 116.0, ground, 15.0, rng)
    f.limb([(gx0 - 10.0, 132.0), (gx1 + 10.0, 132.0)], 4.6, POLE)
    f.ink([(gx0 - 8.0, 130.6), (gx1 + 8.0, 130.6)], 0.9, POLE_LIGHT)
    _lash(f, gx0, 132.0, 3.4)
    _lash(f, gx1, 132.0, 3.4)
    # The gate: a leaf of stakes on two bars and a brace. It is closed.
    x = gx0 + 11.0
    while x <= gx1 - 10.0:
        _stake(f, x, 170.0 + rng.uniform(-2.0, 2.0), ground - 4.0, 8.0, rng)
        x += 7.6
    # The gate stands back in the gateway, a little in shade.
    f.poly(_rect(gx0 + 7.0, 158.0, gx1 - 7.0, ground - 4.0), (44, 30, 22, 70), body=False)
    for y in (194.0, 286.0):
        f.limb([(gx0 + 7.0, y), (gx1 - 7.0, y)], 4.0, POLE_SHADE)
        f.ink([(gx0 + 8.0, y - 1.0), (gx1 - 8.0, y - 1.0)], 0.8, POLE)
    f.limb([(gx0 + 10.0, 284.0), (gx1 - 10.0, 197.0)], 3.6, POLE_SHADE)
    # The cross poles of the palisade, lashed to every other stake.
    for xa, xb in ((8.0, 90.0), (166.0, 250.0)):
        for y in (196.0, 272.0):
            f.limb([(xa, y), (xb, y)], 4.4, POLE)
            f.ink([(xa + 2.0, y - 1.2), (xb - 2.0, y - 1.2)], 0.9, POLE_LIGHT)
            x = xa + 7.0
            while x < xb - 4.0:
                _lash(f, x, y, 2.0)
                x += 19.2
    return A.finish(f, width=1.4)


# ---------------------------------------------------------------------------
# The chair and the mat at Luanda.
# ---------------------------------------------------------------------------


def _draw_luanda_chair(anim: str, i: int, n: int):
    w, h = LUANDA_CHAIR_FRAME
    f = K.Frame(LUANDA_CHAIR_FRAME)
    rng = random.Random("history_luanda_chair")
    ground = h - 4.0
    # The dais: a low wooden platform of one step. Its top shows a little.
    dx0, dx1, dtop = 8.0, 132.0, 146.0
    f.poly(_rect(dx0, dtop + 6.0, dx1, ground), DAIS)
    for k in range(1, 8):
        x = dx0 + k * (dx1 - dx0) / 8.0
        f.ink([(x, dtop + 8.0), (x, ground - 1.0)], 0.7, DAIS_SHADE)
    f.poly(_rect(dx0, ground - 4.0, dx1, ground), DAIS_SHADE, body=False)
    f.poly([(dx0 + 4.0, dtop), (dx1 - 4.0, dtop), (dx1, dtop + 6.0), (dx0, dtop + 6.0)], DAIS_LIGHT)
    f.ink([(dx0, dtop + 6.0), (dx1, dtop + 6.0)], 1.0, DAIS_SHADE)
    # The chair: a tall back between two posts, arms, a seat with a
    # cushion, and turned front legs with a broad stretcher.
    cx = 70.0
    foot = dtop + 3.0
    seat = 104.0
    bl, br = cx - 24.0, cx + 24.0
    back_top = 34.0
    # The back posts with their finials.
    for x in (bl, br):
        f.limb([(x, foot - 2.0), (x, back_top)], 6.0, CHAIR_WOOD)
        f.ink([(x - 1.4, foot - 4.0), (x - 1.4, back_top + 2.0)], 0.9, CHAIR_LIGHT)
        f.ellipse(x, back_top - 2.0, 4.6, 3.0, CHAIR_WOOD)
        f.ellipse(x, back_top - 8.0, 3.6, 4.2, BRASS)
        f.dot(x - 1.0, back_top - 9.0, 1.0, BRASS_LIGHT)
    # The back: crimson velvet held by brass nails, with a carved top rail.
    f.poly(_rect(bl + 3.0, back_top + 4.0, br - 3.0, 92.0), VELVET)
    f.poly(_rect(bl + 3.0, 82.0, br - 3.0, 92.0), VELVET_SHADE, body=False)
    f.ink([(bl + 7.0, back_top + 8.0), (bl + 7.0, 86.0)], 1.0, VELVET_LIGHT)
    for k in range(13):
        y = back_top + 7.0 + k * 4.4
        for x in (bl + 4.6, br - 4.6):
            f.dot(x, y, 1.0, BRASS)
    for k in range(9):
        x = bl + 6.0 + k * 4.5
        for y in (back_top + 6.0, 90.0):
            f.dot(x, y, 1.0, BRASS)
    f.poly([(bl - 2.0, back_top + 6.0), (bl, back_top - 2.0), (cx - 8.0, back_top - 4.0), (cx, back_top - 9.0), (cx + 8.0, back_top - 4.0),
            (br, back_top - 2.0), (br + 2.0, back_top + 6.0)], CHAIR_WOOD)
    f.ink([(bl + 2.0, back_top + 1.0), (cx - 8.0, back_top - 1.0), (cx, back_top - 5.0), (cx + 8.0, back_top - 1.0), (br - 2.0, back_top + 1.0)], 0.8, CHAIR_LIGHT)
    f.ellipse(cx, back_top - 2.0, 3.0, 2.4, BRASS)
    # The seat rail and the velvet seat.
    f.poly(_rect(bl - 4.0, seat, br + 4.0, seat + 8.0), CHAIR_WOOD)
    f.ink([(bl - 3.0, seat + 1.4), (br + 3.0, seat + 1.4)], 0.8, CHAIR_LIGHT)
    for k in range(10):
        f.dot(bl - 1.0 + k * 5.6, seat + 4.6, 0.9, BRASS)
    f.poly([(bl - 3.0, seat), (bl - 1.0, seat - 6.0), (br + 1.0, seat - 6.0), (br + 3.0, seat)], VELVET_SHADE)
    # The cushion: a plump square of velvet with a tassel at each corner.
    f.poly([(bl - 2.0, seat - 3.0), (bl, seat - 13.0), (cx, seat - 15.0), (br, seat - 13.0), (br + 2.0, seat - 3.0), (cx, seat - 1.0)], VELVET)
    f.ink([(bl + 2.0, seat - 11.0), (cx, seat - 13.0), (br - 2.0, seat - 11.0)], 1.0, VELVET_LIGHT)
    f.ink([(bl, seat - 4.0), (cx, seat - 2.4), (br, seat - 4.0)], 1.0, VELVET_SHADE)
    for x, y in ((bl - 2.0, seat - 3.0), (br + 2.0, seat - 3.0), (bl, seat - 13.0), (br, seat - 13.0)):
        f.limb([(x, y), (x + (1.0 if x > cx else -1.0), y + 4.0)], 1.6, BRASS)
    # The arms: flat rails from the back posts, on the front legs.
    for x, s in ((bl, -1.0), (br, 1.0)):
        f.limb([(x, 78.0), (x + s * 8.0, 80.0)], 5.0, CHAIR_WOOD)
        f.ellipse(x + s * 8.0, 80.0, 3.6, 3.0, CHAIR_WOOD)
        f.limb([(x + s * 8.0, 82.0), (x + s * 7.0, seat)], 3.6, CHAIR_WOOD)
    # The front legs and the broad stretcher between them.
    for x in (bl - 2.0, br + 2.0):
        _turned_leg(f, x, seat + 8.0, foot, CHAIR_WOOD, CHAIR_LIGHT, CHAIR_SHADE, 5.0)
    f.poly([(bl, 124.0), (cx - 10.0, 122.0), (cx, 118.0), (cx + 10.0, 122.0), (br, 124.0), (br, 132.0), (bl, 132.0)], CHAIR_WOOD)
    f.ink([(bl + 2.0, 128.0), (br - 2.0, 128.0)], 0.7, CHAIR_LIGHT)
    f.ink(_ring(cx, 124.0, 6.0, 3.0, 180.0, 360.0, 10), 0.7, CHAIR_LIGHT)
    # The mat on the floor beside the dais: plain, flat and low.
    mx0, mx1, my = 142.0, 214.0, ground - 6.0
    mat = [(mx0 + 6.0, my - 6.0), (mx1 - 4.0, my - 6.0), (mx1, my), (mx0, my)]
    f.poly([(mx0, my), (mx1, my), (mx1, my + 2.4), (mx0, my + 2.4)], STRAW_SHADE)
    f.poly(mat, STRAW)
    _hatch(f, mat, (1.0, 0.0), 2.0, STRAW_SHADE, 0.5)
    _hatch(f, mat, (0.6, 1.0), 5.0, STRAW_LIGHT, 0.5)
    for x in range(int(mx0) + 2, int(mx1), 3):
        f.ink([(float(x), my + 2.4), (float(x) + 0.4, my + 3.4)], 0.5, STRAW_SHADE)
    del rng
    return A.finish(f, width=1.3)


# ---------------------------------------------------------------------------
# The baobab.
# ---------------------------------------------------------------------------


def _leaf_tuft(f: K.Frame, x: float, y: float, rng: random.Random, size: float = 1.0) -> None:
    """A tuft of baobab leaves: hands of five leaflets on short stalks."""
    for j in range(rng.choice((2, 3))):
        hx, hy = x + rng.uniform(-6.0, 6.0) * size, y - rng.uniform(2.0, 8.0) * size
        f.ink([(x, y), (hx, hy)], 0.8, BARK_SHADE)
        for k in range(5):
            a = -160.0 + k * 35.0 + rng.uniform(-8.0, 8.0)
            r = math.radians(a)
            lx, ly = hx + math.cos(r) * 5.0 * size, hy + math.sin(r) * 5.0 * size
            f.poly(_oval(lx, ly, 9.0 * size, 3.6 * size, a, 10), LEAF if (j + k) % 2 else LEAF_LIGHT)
            f.ink([(hx, hy), (lx + math.cos(r) * 2.0 * size, ly + math.sin(r) * 2.0 * size)], 0.5, LEAF_SHADE)


def _pod(f: K.Frame, x: float, y: float, stalk: float, sway: float) -> None:
    """A baobab fruit: a velvet oval that hangs on a long stalk."""
    f.ink([(x, y), (x + sway * 0.5, y + stalk * 0.5), (x + sway, y + stalk)], 1.2, BARK_SHADE)
    px, py = x + sway, y + stalk + 9.0
    f.ellipse(px, py, 6.0, 10.0, POD)
    f.poly(_ring(px, py, 6.0, 10.0, -60.0, 100.0, 12) + [(px + 1.0, py + 6.0)], POD_SHADE, body=False)
    f.ink(_ring(px, py, 4.0, 7.6, 170.0, 230.0, 6), 1.0, (196, 190, 152, 255))


def _draw_baobab(anim: str, i: int, n: int):
    w, h = BAOBAB_FRAME
    f = K.Frame(BAOBAB_FRAME)
    rng = random.Random("history_baobab")
    foot = h - 7.0
    low, high = BAOBAB_LOW_TOP, BAOBAB_HIGH_TOP
    tips: List[Point] = []
    # The crown: stout branches that spread at the top like roots. They
    # go first, so the trunk covers their bases.
    crown = [
        ([(250.0, low + 14.0), (246.0, 300.0), (226.0, 244.0), (196.0, 196.0), (156.0, 164.0), (118.0, 152.0)], 62.0, 18.0),
        ([(306.0, low + 14.0), (304.0, 280.0), (294.0, 204.0), (282.0, 132.0), (272.0, 76.0), (264.0, 50.0)], 54.0, 16.0),
        ([(380.0, low + 10.0), (424.0, 330.0), (470.0, 304.0), (510.0, 290.0), (534.0, 274.0)], 38.0, 14.0),
    ]
    for pts, w0, w1 in crown:
        _branch(f, pts, w0, w1, BARK, BARK_LIGHT)
        tips.append(pts[-1])
    # Twigs: short crooked forks off the branches, each with a tuft.
    twigs = [
        [(196.0, 196.0), (182.0, 150.0), (176.0, 110.0), (164.0, 84.0)],
        [(156.0, 164.0), (134.0, 132.0), (110.0, 120.0)],
        [(118.0, 152.0), (92.0, 144.0), (70.0, 150.0)],
        [(118.0, 152.0), (104.0, 128.0), (100.0, 104.0)],
        [(282.0, 132.0), (310.0, 98.0), (326.0, 64.0)],
        [(272.0, 76.0), (244.0, 56.0), (226.0, 38.0)],
        [(264.0, 50.0), (270.0, 32.0)],
        [(470.0, 304.0), (488.0, 266.0), (496.0, 236.0)],
        [(534.0, 274.0), (546.0, 250.0)],
        [(534.0, 274.0), (548.0, 284.0)],
    ]
    for pts in twigs:
        _branch(f, pts, 14.0, 6.0, BARK)
        tips.append(pts[-1])
    # The high limb: it rises from the right of the trunk, turns at an
    # elbow, and runs level to the right. Its top is the high ledge.
    hx0, hx1 = BAOBAB_HIGH_SPAN
    limb = [(334.0, low + 4.0), (340.0, 300.0), (344.0, 240.0), (342.0, 184.0), (342.0, high + 14.0), (346.0, high + 4.0), (hx0 - 2.0, high),
            (hx1, high), (hx1 + 7.0, high + 3.0), (hx1 + 8.0, high + 10.0), (hx1 + 2.0, high + 15.0), (480.0, high + 20.0), (420.0, high + 26.0),
            (392.0, high + 36.0), (384.0, 220.0), (386.0, 300.0), (390.0, low + 4.0)]
    f.poly(limb, BARK)
    f.poly([(hx1 + 2.0, high + 15.0), (480.0, high + 20.0), (420.0, high + 26.0), (392.0, high + 36.0), (384.0, 220.0), (386.0, 300.0), (390.0, low + 4.0),
            (376.0, low + 4.0), (374.0, 300.0), (374.0, 216.0), (384.0, high + 26.0), (420.0, high + 18.0), (480.0, high + 13.0), (hx1 + 4.0, high + 9.0)],
           BARK_SHADE, body=False)
    f.ink([(hx0, high + 2.0), (hx1 - 2.0, high + 2.0)], 1.6, BARK_LIGHT)
    f.ink([(347.0, 300.0), (350.0, 240.0), (348.0, high + 16.0)], 1.4, BARK_LIGHT)
    for x in (400.0, 446.0, 492.0):
        f.ink([(x, high + 6.0), (x + 10.0, high + 9.0)], 0.8, BARK_SHADE)
    for pts in ([(366.0, high + 2.0), (372.0, 104.0), (384.0, 64.0), (396.0, 40.0)], [(hx1 + 4.0, high + 6.0), (544.0, 120.0), (548.0, 98.0)]):
        _branch(f, pts, 14.0, 5.0, BARK)
        tips.append(pts[-1])
    # The low limb: from the left of the trunk it runs level to the left.
    # Its top and the flat shoulder of the trunk make the low ledge.
    lx0, _lx1 = BAOBAB_LOW_SPAN
    left_limb = [(lx0 - 6.0, low + 5.0), (lx0 - 3.0, low + 0.6), (lx0 + 2.0, low), (214.0, low), (214.0, low + 50.0), (180.0, low + 36.0),
                 (140.0, low + 26.0), (104.0, low + 20.0), (lx0 - 2.0, low + 16.0), (lx0 - 7.0, low + 11.0)]
    f.poly(left_limb, BARK)
    f.poly([(lx0 - 2.0, low + 16.0), (104.0, low + 20.0), (140.0, low + 26.0), (180.0, low + 36.0), (214.0, low + 50.0), (214.0, low + 30.0),
            (180.0, low + 24.0), (140.0, low + 16.0), (104.0, low + 12.0), (lx0, low + 10.0)], BARK_SHADE, body=False)
    f.ink([(lx0 + 2.0, low + 2.0), (212.0, low + 2.0)], 1.6, BARK_LIGHT)
    _branch(f, [(lx0 - 2.0, low + 4.0), (70.0, 322.0), (60.0, 300.0)], 10.0, 5.0, BARK)
    tips.append((60.0, 300.0))
    # The trunk: massive and nearly round, a little wider at the foot, with
    # a flat shoulder at the low ledge.
    left_edge = [(150.0, foot), (176.0, foot - 12.0), (188.0, foot - 50.0), (192.0, foot - 110.0), (194.0, foot - 170.0), (198.0, low + 8.0), (204.0, low)]
    right_edge = [(388.0, low + 2.0), (392.0, low + 40.0), (394.0, foot - 140.0), (396.0, foot - 70.0), (402.0, foot - 24.0), (432.0, foot)]
    f.poly(left_edge + [(334.0, low), (360.0, low + 1.0)] + right_edge, BARK)
    # Light on the left, shade on the right, and the folds of the bark.
    f.poly([(206.0, foot - 12.0), (208.0, foot - 110.0), (212.0, low + 14.0), (232.0, low + 10.0), (226.0, foot - 110.0), (226.0, foot - 12.0)], BARK_LIGHT, body=False)
    f.poly([(352.0, low + 4.0), (388.0, low + 2.0), (392.0, low + 40.0), (394.0, foot - 140.0), (396.0, foot - 70.0), (402.0, foot - 24.0), (432.0, foot),
            (360.0, foot), (366.0, foot - 80.0), (362.0, low + 60.0)], BARK_SHADE, body=False)
    for k in range(8):
        x = 216.0 + k * 22.0 + rng.uniform(-4.0, 4.0)
        pts = [(x + 6.0 * math.sin(k + v * 3.0) * (1.0 if k % 2 else -1.0) + (x - 290.0) * 0.18 * (v ** 3), foot - 6.0 - v * (foot - low - 20.0)) for v in [j / 8.0 for j in range(9)]]
        f.ink(pts, 1.2, BARK_SHADE if x < 340.0 else BARK_DARK)
    for k in range(10):
        x = rng.uniform(220.0, 370.0)
        y = rng.uniform(low + 30.0, foot - 30.0)
        f.ink([(x, y), (x + rng.uniform(6.0, 12.0), y + rng.uniform(-1.0, 1.0))], 0.7, BARK_SHADE)
    f.ink([(206.0, low + 2.0), (330.0, low + 2.0)], 1.6, BARK_LIGHT)
    # The roots spread at its foot.
    for s, x in ((-1.0, 176.0), (1.0, 404.0)):
        f.poly([(x - s * 6.0, foot), (x + s * 34.0, foot), (x + s * 4.0, foot - 22.0)], BARK)
        f.ink([(x + s * 4.0, foot - 18.0), (x + s * 26.0, foot - 2.0)], 1.0, BARK_SHADE)
    # The hollow in the trunk, where water was kept.
    hx, hy = 266.0, 486.0
    f.ellipse(hx, hy, 27.0, 44.0, BARK_SHADE, body=False)
    f.ellipse(hx + 1.0, hy + 3.0, 21.0, 38.0, HOLLOW, body=False)
    f.poly(_ring(hx + 1.0, hy + 3.0, 21.0, 38.0, 25.0, 155.0, 12), HOLLOW_WATER, body=False)
    f.ink(_ring(hx + 1.0, hy + 28.0, 17.0, 2.0, 180.0, 360.0, 10), 0.8, (120, 150, 156, 255))
    f.ink(_ring(hx, hy, 27.0, 44.0, 110.0, 250.0, 14), 1.8, BARK_LIGHT)
    # A few leaves, and the fruit pods on their long stalks.
    for x, y in tips:
        _leaf_tuft(f, x, y, rng, 1.0)
    for x, y, stalk, sway in ((150.0, 168.0, 26.0, -3.0), (196.0, 206.0, 30.0, 2.0), (450.0, high + 22.0, 30.0, 2.0), (506.0, high + 18.0, 22.0, -2.0),
                              (494.0, 296.0, 26.0, 2.0), (120.0, low + 22.0, 20.0, 2.0)):
        _pod(f, x, y, stalk, sway)
    return A.finish(f, width=1.6)


# ---------------------------------------------------------------------------
# The rubber vine.
# ---------------------------------------------------------------------------


def _glossy_leaf(f: K.Frame, x: float, y: float, degrees: float, length: float) -> None:
    """A glossy oval leaf on a short stalk from `(x, y)`."""
    a = math.radians(degrees)
    ux, uy = math.cos(a), math.sin(a)
    cx, cy = x + ux * (length / 2.0 + 2.0), y + uy * (length / 2.0 + 2.0)
    f.ink([(x, y), (x + ux * 3.0, y + uy * 3.0)], 0.8, VINE_SHADE)
    f.poly(_oval(cx, cy, length, length * 0.48, degrees, 16), GLOSSY)
    f.ink([(x + ux * 2.6, y + uy * 2.6), (cx + ux * length * 0.42, cy + uy * length * 0.42)], 0.6, GLOSSY_SHADE)
    nx, ny = -uy, ux
    f.ink([(cx - ux * length * 0.2 + nx * length * 0.12, cy - uy * length * 0.2 + ny * length * 0.12),
           (cx + ux * length * 0.15 + nx * length * 0.14, cy + uy * length * 0.15 + ny * length * 0.14)], 0.9, GLOSSY_LIGHT)


def _draw_rubber_vine(anim: str, i: int, n: int):
    w, h = RUBBER_VINE_FRAME
    f = K.Frame(RUBBER_VINE_FRAME)
    rng = random.Random("history_rubber_vine")
    ph = i / float(max(1, n))
    ground = h - 7.0
    tx0, tx1 = 58.0, 98.0
    tcx, tr = (tx0 + tx1) / 2.0, 30.0

    # The vine winds round the trunk: two and a half turns from the root
    # to the top. Its parts behind the trunk go first.
    def at(t: float) -> Tuple[Point, float]:
        th = math.pi * 0.5 + t * 5.0 * math.pi
        y = 262.0 - t * 220.0
        return (tcx + tr * math.sin(th), y), math.cos(th)

    ts = [k / 120.0 for k in range(121)]
    runs: List[Tuple[bool, List[Point]]] = []
    for t in ts:
        p, depth = at(t)
        front = depth > -0.05
        if not runs or runs[-1][0] != front:
            runs.append((front, [p] if not runs else [runs[-1][1][-1], p]))
        else:
            runs[-1][1].append(p)
    for front, pts in runs:
        if not front:
            f.limb(pts, 8.0, VINE_SHADE)
    # The host tree: a tall grey trunk with moss, a fork at the top and
    # a few clumps of its own leaves.
    f.poly([(tx0 - 12.0, ground), (tx0 - 2.0, ground - 10.0), (tx0, 40.0), (tx0 - 4.0, 30.0), (tx1 + 4.0, 30.0), (tx1, 40.0), (tx1 + 2.0, ground - 10.0),
            (tx1 + 12.0, ground)], HOST)
    f.poly([(tx1 - 10.0, ground), (tx1 - 10.0, 40.0), (tx1, 40.0), (tx1 + 2.0, ground - 10.0), (tx1 + 12.0, ground)], HOST_SHADE, body=False)
    f.ink([(tx0 + 5.0, ground - 8.0), (tx0 + 5.0, 44.0)], 1.2, HOST_LIGHT)
    for k in range(5):
        x = tx0 + 8.0 + k * 6.0
        f.ink([(x, ground - 14.0), (x + rng.uniform(-1.5, 1.5), 150.0), (x + rng.uniform(-1.5, 1.5), 46.0)], 0.6, HOST_SHADE)
    for k in range(9):
        y = 60.0 + k * 22.0 + rng.uniform(-4.0, 4.0)
        f.ink([(tx0 + 8.0, y), (tx0 + 14.0, y + 1.0)], 0.7, HOST_SHADE)
        f.ellipse(tx0 + rng.uniform(2.0, 30.0), y + 8.0, rng.uniform(2.0, 4.0), 1.6, K.alpha(MOSS, 0.8), body=False)
    for pts in ([(tx0 + 4.0, 34.0), (40.0, 22.0), (22.0, 18.0)], [(tx1 - 4.0, 34.0), (118.0, 20.0), (138.0, 16.0)]):
        _branch(f, pts, 9.0, 5.0, HOST)
    for x, y in ((22.0, 16.0), (40.0, 12.0), (118.0, 12.0), (138.0, 14.0), (78.0, 14.0)):
        for k in range(5):
            a = -170.0 + k * 40.0
            r = math.radians(a)
            f.poly(_oval(x + math.cos(r) * 5.0, y + math.sin(r) * 3.0 + 4.0, 10.0, 4.4, a, 10), HOST_LIGHT if k % 2 else MOSS)
    # The front parts of the vine, woody and thick.
    for front, pts in runs:
        if front:
            f.limb(pts, 8.4, VINE)
            f.ink([(x - 1.6, y - 1.0) for x, y in pts], 1.2, VINE_LIGHT)
    f.limb([at(0.0)[0], (at(0.0)[0][0] + 4.0, ground - 3.0)], 8.4, VINE)
    # The leaves: pairs along the vine.
    for t in [0.03 + k * 0.03 for k in range(32)]:
        p, depth = at(t)
        if depth < -0.4 or abs(t - 0.31) < 0.04:
            continue
        side = 1.0 if p[0] > tcx else -1.0
        base = -90.0 + side * 70.0
        _glossy_leaf(f, p[0], p[1], base + rng.uniform(-12.0, 12.0), rng.uniform(13.0, 16.0))
        _glossy_leaf(f, p[0], p[1], base + side * 50.0 + rng.uniform(-10.0, 10.0), rng.uniform(11.0, 14.0))
    # The cut: a slanting gash in a front part of the vine, and the white
    # latex that wells out of it and drips into a clay cup.
    cut_t = 0.31
    (cx, cy), _ = at(cut_t)
    f.ink([(cx - 3.4, cy - 2.6), (cx + 3.4, cy + 0.4)], 1.6, LATEX)
    f.ink([(cx - 3.4, cy - 1.2), (cx + 3.4, cy + 1.8)], 0.7, LATEX_SHADE)
    f.limb([(cx + 1.0, cy + 0.6), (cx + 1.2, cy + 6.0)], 1.6, LATEX)
    cup_y = cy + 30.0
    # The cup hangs by a cord tied round the vine under the cut.
    f.ink([(cx - 2.0, cy + 4.0), (cx - 7.0, cup_y - 6.0)], 0.7, FIBRE_DARK)
    f.ink([(cx + 4.0, cy + 4.0), (cx + 8.0, cup_y - 6.0)], 0.7, FIBRE_DARK)
    f.poly([(cx - 8.0, cup_y - 6.0), (cx + 9.0, cup_y - 6.0), (cx + 7.0, cup_y + 2.0), (cx + 3.0, cup_y + 5.0), (cx - 3.0, cup_y + 5.0), (cx - 7.0, cup_y + 2.0)], CUP)
    f.poly([(cx + 2.0, cup_y - 6.0), (cx + 9.0, cup_y - 6.0), (cx + 7.0, cup_y + 2.0), (cx + 3.0, cup_y + 5.0)], CUP_SHADE, body=False)
    f.ellipse(cx + 0.5, cup_y - 6.0, 8.5, 1.8, CUP_LIGHT)
    f.ellipse(cx + 0.5, cup_y - 5.8, 6.6, 1.1, LATEX, body=False)
    # The drop: it grows at the lip of the cut, falls, and comes again.
    drop_x = cx + 1.0
    if ph < 0.6:
        r = 1.0 + 1.0 * ph / 0.6
        f.ellipse(drop_x + 0.2, cy + 6.0 + r * 0.8, r, r * 1.2, LATEX)
    else:
        u = (ph - 0.6) / 0.4
        y = cy + 9.0 + u * (cup_y - 9.0 - cy - 8.0)
        f.ellipse(drop_x + 0.2, y, 1.4, 2.2, LATEX)
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# The magic lantern.
# ---------------------------------------------------------------------------


def _slide(f: K.Frame, x: float, y: float, s: float, rng: random.Random) -> None:
    """A glass lantern slide: a square with a dark border and a small grey
    blur for its picture."""
    f.poly(_rect(x, y, x + s, y + s), SLIDE_BORDER)
    f.poly(_rect(x + 2.0, y + 2.0, x + s - 2.0, y + s - 2.0), SLIDE_GLASS, body=False)
    f.ellipse(x + s / 2.0 + rng.uniform(-1.0, 1.0), y + s / 2.0, s * 0.26, s * 0.2, SLIDE_BLUR, body=False)
    f.ink([(x + 2.6, y + 2.6), (x + s * 0.4, y + 2.6)], 0.5, (240, 240, 236, 255))


def _draw_magic_lantern(anim: str, i: int, n: int):
    w, h = MAGIC_LANTERN_FRAME
    f = K.Frame(MAGIC_LANTERN_FRAME)
    rng = random.Random("history_magic_lantern")
    ph = i / float(max(1, n))
    ground = h - 7.0
    stand = 88.0
    # The tripod stand: a board on three splayed legs.
    for a, b in (((30.0, stand + 4.0), (16.0, ground)), ((60.0, stand + 4.0), (60.0, ground)), ((90.0, stand + 4.0), (104.0, ground))):
        f.limb([a, b], 3.6, OAK)
        f.ink([(a[0] - 0.8, a[1] + 2.0), (b[0] - 0.8, b[1] - 2.0)], 0.7, OAK_LIGHT)
    f.limb([(24.0, ground - 22.0), (96.0, ground - 22.0)], 2.4, OAK_SHADE)
    f.poly(_rect(14.0, stand, 106.0, stand + 6.0), OAK)
    f.ink([(15.0, stand + 1.0), (105.0, stand + 1.0)], 0.8, OAK_LIGHT)
    f.ink([(15.0, stand + 5.0), (105.0, stand + 5.0)], 0.7, OAK_SHADE)
    # The lantern body: a box of black-japanned metal with gold lines, a
    # door with a small window, and feet.
    bx0, bx1, by0, by1 = 28.0, 76.0, 46.0, 84.0
    for x in (32.0, 72.0):
        f.poly(_rect(x - 3.0, by1, x + 3.0, stand), JAPAN)
    f.poly(_rect(bx0, by0, bx1, by1), JAPAN)
    f.poly(_rect(bx0, by1 - 7.0, bx1, by1), JAPAN_SHADE, body=False)
    f.ink([(bx0 + 3.0, by0 + 3.0), (bx1 - 3.0, by0 + 3.0), (bx1 - 3.0, by1 - 3.0), (bx0 + 3.0, by1 - 3.0), (bx0 + 3.0, by0 + 3.0)], 0.7, GOLD_LINE)
    f.ink([(bx0 + 2.0, by0 + 1.4), (bx1 - 2.0, by0 + 1.4)], 1.0, JAPAN_LIGHT)
    f.ellipse(46.0, 66.0, 5.0, 5.0, BRASS)
    glow = 0.5 + 0.5 * math.sin(2.0 * math.pi * ph)
    f.ellipse(46.0, 66.0, 3.4, 3.4, K.shade(GLOW, 0.75 + 0.15 * glow), body=False)
    f.dot(62.0, 66.0, 1.6, BRASS)
    # The chimney for the lamp, with a cowl and vents.
    f.poly([(46.0, by0), (47.0, 20.0), (57.0, 20.0), (58.0, by0)], JAPAN)
    f.ink([(48.4, by0 - 2.0), (48.8, 22.0)], 0.8, JAPAN_LIGHT)
    f.poly([(42.0, 20.0), (44.0, 14.0), (60.0, 14.0), (62.0, 20.0)], JAPAN)
    f.poly(_rect(48.0, 10.0, 56.0, 14.0), JAPAN)
    for k in range(4):
        f.dot(46.0 + k * 4.0, 17.0, 0.9, JAPAN_LIGHT)
    f.limb([(64.0, by0), (66.0, by0 - 6.0), (72.0, by0 - 6.0), (74.0, by0)], 1.8, JAPAN_LIGHT)
    # The slide stage and the brass lens tube, in two drawn tubes.
    cy = 64.0
    f.poly(_rect(bx1, 48.0, bx1 + 6.0, 80.0), BRASS_SHADE)
    f.ink([(bx1 + 1.6, 50.0), (bx1 + 1.6, 78.0)], 0.8, BRASS_LIGHT)
    f.poly(_rect(bx1 + 6.0, cy - 9.0, 106.0, cy + 9.0), BRASS)
    f.poly(_rect(bx1 + 6.0, cy + 4.0, 106.0, cy + 9.0), BRASS_SHADE, body=False)
    f.ink([(bx1 + 7.0, cy - 6.4), (105.0, cy - 6.4)], 1.0, BRASS_LIGHT)
    for x in (bx1 + 10.0, 104.0):
        f.ink([(x, cy - 9.0), (x, cy + 9.0)], 0.8, BRASS_SHADE)
    f.poly(_rect(106.0, cy - 7.0, 118.0, cy + 7.0), BRASS)
    f.poly(_rect(106.0, cy + 3.0, 118.0, cy + 7.0), BRASS_SHADE, body=False)
    f.ink([(107.0, cy - 4.6), (117.0, cy - 4.6)], 0.8, BRASS_LIGHT)
    f.ellipse(119.0, cy, 3.0, 7.4, BRASS_SHADE)
    f.ellipse(119.6, cy, 2.0, 6.0, LENS, body=False)
    f.ink([(119.8, cy - 4.0), (120.0, cy - 1.0)], 0.7, LENS_LIGHT)
    f.limb([(96.0, cy + 9.0), (96.0, 80.0), (90.0, stand)], 2.0, BRASS_SHADE)
    # The faint warm glow at the lens.
    f.glow(121.0, cy, 4.0 + 1.6 * glow, K.alpha(GLOW, 0.32 + 0.22 * glow))
    # The open box of slides on the floor beside the stand: its lid leans
    # back; the slides stand in rows; two lean on its front.
    sx0, sx1, sy0 = 112.0, 154.0, 112.0
    f.poly([(sx0 + 2.0, sy0), (sx0 + 6.0, sy0 - 22.0), (sx1 - 2.0, sy0 - 22.0), (sx1 - 2.0, sy0)], OAK_SHADE)
    f.poly([(sx0 + 5.0, sy0 - 2.0), (sx0 + 8.0, sy0 - 19.0), (sx1 - 5.0, sy0 - 19.0), (sx1 - 5.0, sy0 - 2.0)], K.shade(OAK_SHADE, 0.8), body=False)
    for k in range(12):
        x = sx0 + 5.0 + k * 3.2
        f.poly(_rect(x, sy0 - 6.0, x + 1.6, sy0 + 2.0), SLIDE_GLASS)
        f.ink([(x + 0.8, sy0 - 6.0), (x + 0.8, sy0 + 1.0)], 0.6, SLIDE_BORDER)
    f.poly(_rect(sx0, sy0, sx1, ground), OAK)
    f.poly(_rect(sx0, ground - 5.0, sx1, ground), OAK_SHADE, body=False)
    f.ink([(sx0 + 1.0, sy0 + 1.2), (sx1 - 1.0, sy0 + 1.2)], 0.8, OAK_LIGHT)
    for x in (sx0 + 3.0, sx1 - 3.0):
        f.ink([(x, sy0 + 2.0), (x, ground - 2.0)], 0.6, OAK_SHADE)
    _slide(f, sx0 + 6.0, ground - 16.0, 14.0, rng)
    _slide(f, sx0 + 22.0, ground - 15.0, 14.0, rng)
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# The stern-wheel steamer (a platform).
# ---------------------------------------------------------------------------


def _paddle_wheel(f: K.Frame, cx: float, cy: float, r: float, turn: float) -> None:
    """The stern wheel: two rims on spokes, with red buckets on the rim.
    `turn` turns it (radians, clockwise on the screen)."""
    spokes = 10
    for k in range(spokes):
        a = turn + math.tau * k / spokes
        f.ink([(cx + math.cos(a) * 3.0, cy + math.sin(a) * 3.0), (cx + math.cos(a) * (r - 2.0), cy + math.sin(a) * (r - 2.0))], 1.6, IRON)
    ring = _ring(cx, cy, r - 6.0, r - 6.0, 0.0, 360.0, 48)
    f.limb(ring + ring[1:3], 2.0, IRON)
    for k in range(spokes):
        a = turn + math.tau * (k + 0.5) / spokes
        c, s = math.cos(a), math.sin(a)
        nx, ny = -s, c
        p0, p1 = (cx + c * (r - 10.0), cy + s * (r - 10.0)), (cx + c * (r + 1.0), cy + s * (r + 1.0))
        f.poly([(p0[0] + nx * 2.2, p0[1] + ny * 2.2), (p1[0] + nx * 2.2, p1[1] + ny * 2.2), (p1[0] - nx * 2.2, p1[1] - ny * 2.2), (p0[0] - nx * 2.2, p0[1] - ny * 2.2)], BUCKET)
        f.ink([(p0[0] + nx * 1.0, p0[1] + ny * 1.0), (p1[0] + nx * 1.0, p1[1] + ny * 1.0)], 0.6, BUCKET_LIGHT)
    ring = _ring(cx, cy, r - 1.0, r - 1.0, 0.0, 360.0, 48)
    f.limb(ring + ring[1:3], 1.8, IRON)
    f.ellipse(cx, cy, 4.6, 4.6, IRON)
    f.dot(cx - 1.0, cy - 1.0, 1.4, IRON_LIGHT)


def _draw_congo_steamer(anim: str, i: int, n: int):
    w, h = CONGO_STEAMER_FRAME
    f = K.Frame(CONGO_STEAMER_FRAME)
    rng = random.Random("history_congo_steamer")
    ph = i / float(max(1, n))
    top = CONGO_STEAMER_TOP
    hull0, hull1 = 110.0, 488.0
    wl = top + 24.0
    roof = top - 150.0
    # The river behind the hull. It has no outline.
    _water(f, 6.0, w - 6.0, wl - 4.0, wl + 38.0, RIVER)
    # The stern wheel turns two buckets in the loop. Its lower part is in
    # the water. The far beam that carries it goes first.
    wcx, wcy, wr = 62.0, wl - 12.0, 48.0
    f.limb([(hull0 + 4.0, wcy - 2.0), (16.0, wcy - 2.0)], 4.0, DECK_SHADE)
    _paddle_wheel(f, wcx, wcy, wr, math.tau * 2.0 / 10.0 * ph)
    # The near beam, from the hull past the axle, and the bearing.
    f.limb([(hull0 + 4.0, wcy), (20.0, wcy)], 4.6, DECK)
    f.ink([(hull0 + 2.0, wcy - 1.2), (22.0, wcy - 1.2)], 0.8, DECK_LIGHT)
    f.limb([(hull0 + 2.0, top + 4.0), (wcx + 20.0, wcy)], 3.0, DECK_SHADE)
    f.ellipse(wcx, wcy, 6.0, 5.0, IRON)
    f.dot(wcx - 1.4, wcy - 1.2, 1.6, IRON_LIGHT)
    # The stanchions that hold the awning, and the boiler with its funnel.
    posts = [116.0, 166.0, 216.0, 266.0, 382.0, 432.0, 474.0]
    for x in posts:
        f.limb([(x, top), (x, roof + 6.0)], 2.4, DECK_SHADE)
        f.ink([(x - 0.6, top - 1.0), (x - 0.6, roof + 8.0)], 0.6, DECK_LIGHT)
    fx = 322.0
    f.poly([(fx - 22.0, top), (fx - 22.0, top - 60.0), (fx + 22.0, top - 60.0), (fx + 22.0, top)], IRON)
    f.ellipse(fx, top - 60.0, 22.0, 6.0, IRON)
    f.poly(_rect(fx + 8.0, top - 60.0, fx + 22.0, top), IRON_SHADE, body=False)
    f.ink([(fx - 18.0, top - 2.0), (fx - 18.0, top - 58.0)], 1.0, IRON_LIGHT)
    for y in (top - 44.0, top - 24.0):
        f.ink([(fx - 22.0, y), (fx + 22.0, y)], 0.7, IRON_SHADE)
        for k in range(9):
            f.dot(fx - 19.0 + k * 4.8, y - 2.0, 0.6, IRON_LIGHT)
    f.poly(_rect(fx - 10.0, top - 22.0, fx + 4.0, top - 8.0), IRON_SHADE)
    f.poly(_rect(fx - 8.0, top - 20.0, fx + 2.0, top - 10.0), K.shade(EMBER, 0.6), body=False)
    f.ink([(fx - 8.0, top - 12.0), (fx + 2.0, top - 12.0)], 0.8, K.shade(EMBER, 0.8))
    # The cord of firewood on the deck: logs stacked end on.
    for row in range(4):
        y = top - 4.6 - row * 8.0
        for k in range(6 - row):
            x = 362.0 + row * 4.6 + k * 9.2
            f.ellipse(x, y, 4.6, 4.2, LOG_BARK)
            f.ellipse(x - 0.4, y - 0.2, 3.2, 2.8, LOG_END, body=False)
            f.dot(x - 0.4, y - 0.2, 0.8, LOG_BARK)
    # A bench and a few crates of goods at the stern.
    f.poly(_rect(128.0, top - 18.0, 154.0, top), OAK)
    f.ink([(130.0, top - 16.0), (152.0, top - 2.0)], 0.6, OAK_SHADE)
    f.ink([(130.0, top - 2.0), (152.0, top - 16.0)], 0.6, OAK_SHADE)
    f.poly(_rect(132.0, top - 30.0, 150.0, top - 18.0), OAK_LIGHT)
    f.ink([(133.0, top - 24.0), (149.0, top - 24.0)], 0.6, OAK_SHADE)
    f.poly(_rect(182.0, top - 14.0, 208.0, top - 10.0), DECK_LIGHT)
    for x in (185.0, 205.0):
        f.limb([(x, top - 10.0), (x, top)], 2.0, DECK_SHADE)
    # The awning: a flat roof of boards with a canvas valance, and the
    # side curtain rolled up under its edge.
    f.poly(_rect(106.0, roof, 480.0, roof + 7.0), CANVAS)
    f.ink([(108.0, roof + 1.2), (478.0, roof + 1.2)], 1.0, CANVAS_LIGHT)
    f.poly(_rect(106.0, roof + 5.0, 480.0, roof + 7.0), CANVAS_SHADE, body=False)
    val = [(106.0, roof + 7.0)]
    for k in range(39):
        x = 106.0 + k * (374.0 / 38.0)
        val.append((x, roof + (12.0 if k % 2 else 9.0)))
    val.append((480.0, roof + 7.0))
    f.poly(val, CANVAS_LIGHT)
    f.limb([(110.0, roof + 15.0), (476.0, roof + 15.0)], 4.0, CANVAS_SHADE)
    f.ink([(112.0, roof + 14.0), (474.0, roof + 14.0)], 0.8, CANVAS)
    # The wheelhouse on the roof, at the front, with its windows.
    hx0, hx1 = 404.0, 458.0
    f.poly(_rect(hx0, roof - 36.0, hx1, roof), HULL)
    f.poly(_rect(hx0, roof - 8.0, hx1, roof), HULL_SHADE, body=False)
    for k in range(3):
        x = hx0 + 6.0 + k * 16.0
        f.poly(_rect(x, roof - 30.0, x + 11.0, roof - 18.0), WINDOW)
        f.ink([(x + 1.6, roof - 28.6), (x + 5.0, roof - 28.6)], 0.6, (150, 170, 172, 255))
    f.poly([(hx0 - 5.0, roof - 36.0), (hx0 - 1.0, roof - 41.0), (hx1 + 1.0, roof - 41.0), (hx1 + 5.0, roof - 36.0)], DECK)
    f.ink([(hx0 - 3.0, roof - 37.0), (hx1 + 3.0, roof - 37.0)], 0.7, DECK_SHADE)
    # The funnel: one tall thin black funnel, through the roof.
    ftop = 40.0
    f.poly(_rect(fx - 5.0, ftop, fx + 5.0, top - 64.0), FUNNEL)
    f.ink([(fx - 2.6, ftop + 2.0), (fx - 2.6, top - 66.0)], 1.0, FUNNEL_LIGHT)
    f.poly(_rect(fx - 7.0, ftop - 4.0, fx + 7.0, ftop + 1.0), FUNNEL)
    f.poly(_rect(fx - 8.0, roof - 2.0, fx + 8.0, roof + 1.0), FUNNEL)
    # The hull: long, low and white, with a dark waterline and a raked
    # bow. Its deck is level.
    f.poly([(hull0, top), (hull1 - 8.0, top), (hull1 + 6.0, top + 2.0), (hull1 + 2.0, top + 10.0), (hull1 - 12.0, top + 26.0), (hull0 + 2.0, top + 26.0),
            (hull0 - 2.0, top + 14.0)], HULL)
    f.poly([(hull0 - 1.0, top + 16.0), (hull1 - 4.0, top + 16.0), (hull1 - 12.0, top + 26.0), (hull0 + 2.0, top + 26.0)], HULL_SHADE, body=False)
    f.poly([(hull0, top + 20.0), (hull1 - 7.6, top + 20.0), (hull1 - 11.0, top + 24.0), (hull0 + 1.0, top + 24.0)], WATERLINE, body=False)
    f.ink([(hull0 + 2.0, top + 8.0), (hull1, top + 8.0)], 1.0, HULL_SHADE)
    f.ink([(hull0 + 2.0, top + 3.6), (hull1 - 2.0, top + 3.6)], 0.8, HULL_LIGHT)
    f.poly(_rect(hull0 - 2.0, top, hull1 - 4.0, top + 2.4), DECK)
    for x in range(int(hull0) + 20, int(hull1) - 10, 40):
        f.dot(float(x), top + 12.0, 1.2, HULL_SHADE)
    # The river in front: it covers the foot of the hull and the lower
    # part of the wheel. Ripples move, and foam churns at the wheel.
    _water(f, 6.0, w - 6.0, wl + 2.0, wl + 38.0, RIVER_DEEP)
    _ripples(f, 18.0, w - 18.0, wl + 10.0, ph, RIPPLE, 4, 7.0, "history_congo_steamer ripples")
    for k in range(7):
        x = 14.0 + k * 14.0 + 3.0 * math.sin(2.0 * math.pi * (ph + k * 0.3))
        f.ink([(x, wl + 4.0 + (k % 2) * 3.0), (x + 9.0, wl + 4.0 + (k % 2) * 3.0)], 1.4, FOAM)
    # The smoke: puffs that rise from the funnel and drift back.
    for k in range(4):
        u = (ph + k / 4.0) % 1.0
        x = fx - 4.0 - 64.0 * u
        y = ftop - 8.0 - 14.0 * u
        r = 4.0 + 5.0 * u
        _puff(f, x, max(1.2 * r + 5.0, y), r, K.alpha(SMOKE, 0.95 - 0.55 * u), random.Random(f"history_congo_steamer smoke {k}"), 5,
              shade=K.alpha(SMOKE_SHADE, 0.6 * (1.0 - u)))
    del rng
    return A.finish(f, width=1.4)


# ---------------------------------------------------------------------------
# Publication.
# ---------------------------------------------------------------------------

FRAMES: Dict[str, Tuple[int, int]] = {
    "history_ishango_bone": ISHANGO_BONE_FRAME,
    "history_bone_harpoons": BONE_HARPOONS_FRAME,
    "history_raffia_loom": RAFFIA_LOOM_FRAME,
    "history_nzimbu_basket": NZIMBU_BASKET_FRAME,
    "history_afonso_letter": AFONSO_LETTER_FRAME,
    "history_kongo_house": KONGO_HOUSE_FRAME,
    "history_kilombo_gate": KILOMBO_GATE_FRAME,
    "history_luanda_chair": LUANDA_CHAIR_FRAME,
    "history_baobab": BAOBAB_FRAME,
    "history_rubber_vine": RUBBER_VINE_FRAME,
    "history_magic_lantern": MAGIC_LANTERN_FRAME,
    "history_congo_steamer": CONGO_STEAMER_FRAME,
}
DRAW: Dict[str, Callable] = {
    "history_ishango_bone": _draw_ishango_bone,
    "history_bone_harpoons": _draw_bone_harpoons,
    "history_raffia_loom": _draw_raffia_loom,
    "history_nzimbu_basket": _draw_nzimbu_basket,
    "history_afonso_letter": _draw_afonso_letter,
    "history_kongo_house": _draw_kongo_house,
    "history_kilombo_gate": _draw_kilombo_gate,
    "history_luanda_chair": _draw_luanda_chair,
    "history_baobab": _draw_baobab,
    "history_rubber_vine": _draw_rubber_vine,
    "history_magic_lantern": _draw_magic_lantern,
    "history_congo_steamer": _draw_congo_steamer,
}
DISPLAY = {
    "history_ishango_bone": "Ishango Bone",
    "history_bone_harpoons": "Bone Harpoons",
    "history_raffia_loom": "Raffia Loom",
    "history_nzimbu_basket": "Nzimbu Basket",
    "history_afonso_letter": "Letter of Afonso I",
    "history_kongo_house": "Kongo House",
    "history_kilombo_gate": "Kilombo Gate",
    "history_luanda_chair": "Luanda Chair",
    "history_baobab": "Baobab",
    "history_rubber_vine": "Rubber Vine",
    "history_magic_lantern": "Magic Lantern",
    "history_congo_steamer": "Congo Steamer",
}
#: The room of each prop: its last tag.
ROOMS = {
    "history_ishango_bone": "ishango",
    "history_bone_harpoons": "ishango",
    "history_raffia_loom": "kongo",
    "history_nzimbu_basket": "kongo",
    "history_afonso_letter": "kongo",
    "history_kongo_house": "kongo",
    "history_kilombo_gate": "ndongo",
    "history_luanda_chair": "ndongo",
    "history_baobab": "ndongo",
    "history_rubber_vine": "congo_free_state",
    "history_magic_lantern": "congo_free_state",
    "history_congo_steamer": "congo_free_state",
}
ROWS: Dict[str, List[Tuple[str, int, int]]] = {
    "history_rubber_vine": LOOP,
    "history_magic_lantern": LOOP,
    "history_congo_steamer": LOOP,
}


def _foot(name: str) -> Dict[str, Tuple[float, float]]:
    w, h = FRAMES[name]
    return {"foot": (w / 2.0, float(h))}


#: The anchors of each prop. A platform has a "top" anchor at the middle of
#: the surface that a player stands on; the other props have a "foot".
ANCHORS: Dict[str, Dict[str, Tuple[float, float]]] = {name: _foot(name) for name in DISPLAY}
ANCHORS["history_congo_steamer"] = {"top": ((CONGO_STEAMER_SPAN[0] + CONGO_STEAMER_SPAN[1]) / 2.0, CONGO_STEAMER_TOP)}
TAGS: Dict[str, List[str]] = {name: ["prop", "scenery", "history", ROOMS[name]] for name in DISPLAY}
TAGS["history_congo_steamer"] = ["prop", "platform", "history", ROOMS["history_congo_steamer"]]

TARGETS: Dict[str, dict] = {
    name: _publisher(name, DISPLAY[name], ROWS.get(name, STILL), FRAMES[name], DRAW[name], ANCHORS[name], "Scenery", TAGS[name]) for name in DISPLAY
}
