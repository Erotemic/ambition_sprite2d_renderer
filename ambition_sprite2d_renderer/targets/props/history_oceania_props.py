"""The props of Australia and Aotearoa (the History dimension): Lake Mungo,
Aotearoa about 1375, Tonga and Samoa about 1200, Waitangi in 1840 and
Sydney Cove in 1788.

About 40,000 years ago the Willandra Lakes in south-west New South Wales
were full of fresh water. People fished them and ate their mussels, and
cooked on hearths of baked clay lumps. About 20,000 years ago people
walked, and one man ran, over wet clay at the lake's edge. More than 700
of their footprints were found in 2003 by Mary Pappin Jr, a young Mutthi
Mutthi woman. The Paakantyi, Mutthi Mutthi and Ngiyampaa peoples are the
traditional owners.

The first people of Aotearoa came by waka from East Polynesia about 1300.
They stored kumara in pits (rua) cut into banks, and ground pounamu
(greenstone) into adzes with sandstone.

In Tonga about 1200 the eleventh Tu'i Tonga, Tu'itatui, built the
Ha'amonga 'a Maui: two uprights of coral limestone and a lintel set into
notches in their tops. Women made ngatu (Tongan tapa) from beaten bark.
In Samoa people met in open houses (fale), and kava was mixed in a bowl
with many legs (tanoa).

On 6 February 1840 the Treaty of Waitangi was signed in front of James
Busby's house. It has two texts, in English and in Maori, and they do not
say the same thing. Across the bay, Hone Heke cut down the flagstaff on
Maiki Hill four times in 1844 and 1845.

In January 1788 the eleven ships of the First Fleet came to Warrane, Sydney
Cove, the land of the Gadigal people of the Eora nation. Eora women fished
from bark canoes (nawi), with a small fire on a pad of clay in the canoe.
These props of Sydney Cove are quiet and sober.

These props are drawn in the cel style of the dimension's cast
(`targets/characters/_history_americas_kit.py`): flat colour, one shade, a
bold warm outline. They show the skill and the dignity of the people who
made them. No script is drawn: writing is lines of short strokes. There
are no people, no bodies, no human remains and no sacred things.

- ``history_mungo_footprints``: scenery, a short stretch of the Willandra
  trackway: a slab of hard pale clay with fine cracks and a crust of
  pink-orange sand at its edges, and three trails of human footprints: a
  man who ran with long strides, and an adult and a child who walked.
- ``history_shell_midden``: scenery, a low heap of freshwater mussel
  shells by an old hearth (a ring of baked clay lumps and grey ash, a few
  burnt fish bones), on pale sand.
- ``history_rua_pit``: scenery, a kumara store (rua) cut into a clay bank:
  grass and fern on the bank, a small doorway framed by plain timber posts
  and a lintel, a sliding door half open, and a short drain in front.
- ``history_pounamu_adze``: scenery, a pounamu adze blade (toki) on a
  small plaited flax mat (whariki), and a sandstone grinding block with a
  groove.
- ``history_haamonga``: scenery, the Ha'amonga 'a Maui: two uprights of
  grey coral limestone and a lintel laid in notches in their tops, with
  lichen, pits of fossil coral and grass at the foot. Its top is level, so
  that a player can stand on it (`HAAMONGA_SPAN` = (40, 536),
  `HAAMONGA_TOP` = 58, in a 576 x 448 frame).
- ``history_ngatu_board``: scenery, a long ngatu laid flat: pale buff
  cloth with bands of brown and red-brown lines, triangles, dots and square
  panels, and beside it the wooden beater (ike) on a log anvil.
- ``history_samoan_fale``: scenery, a Samoan fale: a ring of wooden posts
  on a raised platform of stones and coral gravel (paepae), with no walls,
  under a big domed thatched roof. Plaited blinds are rolled up under the
  eaves.
- ``history_kava_bowl``: scenery, a wooden kava bowl (tanoa) on many short
  legs, with pale kava in it, a strainer of hibiscus fibre on its rim and a
  coconut-shell cup beside it.
- ``history_treaty_house``: scenery, James Busby's house of 1834: a small
  white weatherboard house with a hipped roof of grey shingles, a verandah
  on thin posts, a door between two sash windows, a low brick chimney and
  a step.
- ``history_treaty_table``: scenery, a plain wooden table with the two
  texts of the Treaty side by side (the English text, and the Maori text
  with a column of signature marks at its foot), a quill and an inkwell.
- ``history_flagstaff``: scenery, the flagstaff on Maiki Hill: a tall mast
  with a topmast and a small yard, stays to the ground, and the Union Flag
  of 1801 on its halyard.
- ``history_first_fleet_ship``: scenery, a ship of the First Fleet at
  anchor: three masts, all sails furled on the yards, a black hull with a
  pale band and shut gunports, stern windows, a bowsprit and the anchor
  cable into the water. A red ensign of 1788 hangs slack at the stern.
- ``history_nawi``: the look of a platform, an Eora bark canoe (nawi): one
  sheet of red-brown stringybark with its ends gathered and tied, and
  cross-sticks that hold its sides apart, with a small fire on a pad of
  clay in the middle. Its gunwale is the platform (`NAWI_SPAN` = (60, 324),
  `NAWI_TOP` = 112, in a 384 x 160 frame). Its ``idle`` row makes the fire
  flicker and the water move; the hull stays level and still.

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

MUNGO_FOOTPRINTS_FRAME = (288, 64)
SHELL_MIDDEN_FRAME = (160, 64)
RUA_PIT_FRAME = (192, 128)
POUNAMU_ADZE_FRAME = (128, 64)
HAAMONGA_FRAME = (576, 448)
#: The top of the trilithon is level: the lintel lies in notches in the
#: tops of the uprights, and its top is flush with theirs. A player can
#: stand on it from x0 to x1 at the height `HAAMONGA_TOP` (frame pixels;
#: the foot of the frame is y 448). The stone is about 5 m high at 76 frame
#: pixels a metre.
HAAMONGA_SPAN = (40.0, 536.0)
HAAMONGA_TOP = 58.0
NGATU_BOARD_FRAME = (288, 64)
SAMOAN_FALE_FRAME = (320, 256)
KAVA_BOWL_FRAME = (128, 72)
TREATY_HOUSE_FRAME = (320, 224)
TREATY_TABLE_FRAME = (160, 112)
FLAGSTAFF_FRAME = (160, 448)
FIRST_FLEET_SHIP_FRAME = (512, 512)
NAWI_FRAME = (384, 160)
#: The gunwale of the canoe is the platform: it is level from x0 to x1 at
#: the height `NAWI_TOP` (frame pixels). The ends of the canoe rise past
#: the span.
NAWI_SPAN = (60.0, 324.0)
NAWI_TOP = 112.0

# Lake Mungo: the hard clay, the sand, the shells and the hearth.
HARDPAN = (222, 214, 194, 255)
HARDPAN_LIGHT = (240, 234, 218, 255)
HARDPAN_SHADE = (184, 174, 156, 255)
HARDPAN_DARK = (150, 140, 124, 255)
PRINT_WALL = (120, 106, 92, 255)
PRINT_FLOOR = (174, 162, 142, 255)
DUNE = (226, 164, 120, 255)
DUNE_LIGHT = (240, 192, 152, 255)
DUNE_SHADE = (192, 128, 92, 255)
SAND = (232, 216, 182, 255)
SAND_SHADE = (200, 182, 146, 255)
MUSSEL = (74, 80, 96, 255)
MUSSEL_BLUE = (98, 108, 128, 255)
MUSSEL_SHADE = (52, 56, 70, 255)
NACRE = (214, 212, 222, 255)
NACRE_BLUE = (190, 200, 222, 255)
NACRE_PINK = (232, 208, 206, 255)
HEAP = (128, 122, 118, 255)
ASH = (176, 172, 166, 255)
ASH_LIGHT = (204, 200, 194, 255)
ASH_SHADE = (138, 134, 130, 255)
CHAR = (54, 48, 46, 255)
BAKED = (192, 104, 66, 255)
BAKED_LIGHT = (222, 142, 98, 255)
BAKED_SHADE = (148, 74, 46, 255)
BURNT_BONE = (118, 112, 108, 255)
BURNT_BONE_DARK = (78, 72, 70, 255)

# Aotearoa: the clay bank, the turf, the timber, the greenstone and flax.
CLAY = (196, 146, 84, 255)
CLAY_LIGHT = (220, 176, 114, 255)
CLAY_SHADE = (156, 108, 60, 255)
CLAY_DARK = (118, 80, 46, 255)
TURF = (104, 136, 66, 255)
TURF_LIGHT = (140, 170, 90, 255)
TURF_SHADE = (74, 104, 52, 255)
FERN = (78, 128, 70, 255)
FERN_LIGHT = (118, 164, 96, 255)
TIMBER = (128, 92, 60, 255)
TIMBER_LIGHT = (164, 124, 84, 255)
TIMBER_SHADE = (92, 64, 42, 255)
INTERIOR = (38, 28, 24, 255)
WATER = (96, 120, 128, 220)
WATER_LIGHT = (176, 196, 200, 255)
POUNAMU = (52, 128, 84, 255)
POUNAMU_DEEP = (26, 82, 54, 255)
POUNAMU_LIGHT = (108, 176, 120, 255)
POUNAMU_GLOSS = (196, 236, 200, 255)
FLAX = (222, 190, 112, 255)
FLAX_LIGHT = (240, 214, 146, 255)
FLAX_SHADE = (182, 148, 78, 255)
SANDSTONE = (168, 160, 140, 255)
SANDSTONE_LIGHT = (196, 188, 168, 255)
SANDSTONE_SHADE = (128, 120, 104, 255)

# Tonga and Samoa: coral limestone, tapa, the fale and the kava bowl.
CORAL = (172, 168, 154, 255)
CORAL_LIGHT = (200, 196, 182, 255)
CORAL_SHADE = (132, 128, 118, 255)
CORAL_DARK = (96, 92, 86, 255)
LICHEN = (204, 198, 128, 255)
LICHEN_ORANGE = (206, 150, 92, 255)
LICHEN_GREY = (214, 214, 200, 255)
GRASS = (98, 146, 64, 255)
GRASS_LIGHT = (140, 182, 88, 255)
GRASS_SHADE = (66, 108, 48, 255)
NGATU = (230, 212, 170, 255)
NGATU_SHADE = (198, 178, 134, 255)
DYE_BROWN = (138, 84, 46, 255)
DYE_DARK = (82, 40, 28, 255)
DYE_RED = (128, 54, 36, 255)
HARDWOOD = (120, 76, 44, 255)
HARDWOOD_LIGHT = (156, 106, 66, 255)
HARDWOOD_SHADE = (86, 52, 32, 255)
STONE = (126, 118, 108, 255)
STONE_LIGHT = (160, 152, 140, 255)
STONE_SHADE = (92, 86, 80, 255)
GRAVEL = (226, 222, 208, 255)
GRAVEL_SHADE = (190, 184, 170, 255)
THATCH = (186, 150, 92, 255)
THATCH_LIGHT = (214, 182, 122, 255)
THATCH_SHADE = (142, 108, 62, 255)
THATCH_DARK = (104, 76, 44, 255)
POST = (132, 94, 60, 255)
POST_LIGHT = (168, 126, 86, 255)
POST_SHADE = (88, 62, 40, 255)
BLIND = (208, 182, 126, 255)
BLIND_SHADE = (164, 136, 86, 255)
MAT = (220, 202, 156, 255)
MAT_SHADE = (184, 162, 116, 255)
TANOA = (138, 84, 48, 255)
TANOA_LIGHT = (176, 116, 72, 255)
TANOA_SHADE = (98, 58, 34, 255)
KAVA = (196, 182, 150, 255)
KAVA_LIGHT = (226, 216, 190, 255)
KAVA_SHADE = (168, 152, 120, 255)
HIBISCUS = (222, 206, 166, 255)
HIBISCUS_SHADE = (176, 156, 112, 255)
SHELL_CUP = (92, 58, 36, 255)
SHELL_CUP_LIGHT = (140, 96, 62, 255)
SHELL_CUP_INNER = (176, 134, 92, 255)

# Waitangi: the white house, the table and the flags.
WHITE = (244, 242, 232, 255)
WHITE_SHADE = (208, 204, 192, 255)
WHITE_DARK = (170, 166, 156, 255)
SHINGLE = (144, 144, 140, 255)
SHINGLE_LIGHT = (176, 176, 170, 255)
SHINGLE_SHADE = (110, 110, 108, 255)
BRICK = (164, 82, 60, 255)
BRICK_SHADE = (124, 58, 42, 255)
MORTAR = (206, 186, 160, 255)
GLASS = (84, 100, 108, 255)
GLASS_LIGHT = (156, 176, 182, 255)
DOOR = (96, 64, 44, 255)
DOOR_SHADE = (70, 46, 32, 255)
DECKING = (168, 150, 124, 255)
DECKING_SHADE = (130, 114, 92, 255)
STEP_STONE = (176, 170, 160, 255)
STEP_STONE_SHADE = (140, 134, 126, 255)
TABLE = (140, 96, 60, 255)
TABLE_LIGHT = (172, 124, 82, 255)
TABLE_SHADE = (104, 70, 44, 255)
PAPER = (242, 234, 212, 255)
PAPER_SHADE = (214, 202, 172, 255)
VELLUM = (236, 222, 190, 255)
VELLUM_SHADE = (206, 188, 150, 255)
WRITING = (62, 50, 44, 255)
INKPOT = (58, 62, 78, 255)
INKPOT_LIGHT = (104, 110, 128, 255)
QUILL = (246, 242, 232, 255)
QUILL_SHADE = (204, 196, 182, 255)
MAST = (150, 112, 72, 255)
MAST_LIGHT = (188, 148, 102, 255)
MAST_SHADE = (108, 78, 50, 255)
EARTH = (138, 102, 68, 255)
EARTH_SHADE = (104, 76, 50, 255)
FLAG_BLUE = (30, 48, 112, 255)
FLAG_RED = (196, 34, 44, 255)
FLAG_WHITE = (246, 244, 238, 255)

# Sydney Cove, 1788: muted and grey-blue.
HULL = (40, 38, 40, 255)
HULL_LIGHT = (78, 76, 80, 255)
HULL_SHADE = (26, 24, 26, 255)
OCHRE = (206, 176, 112, 255)
OCHRE_SHADE = (166, 138, 82, 255)
SPAR = (112, 84, 56, 255)
SPAR_LIGHT = (150, 116, 80, 255)
SPAR_SHADE = (80, 58, 38, 255)
CANVAS = (226, 218, 196, 255)
CANVAS_LIGHT = (242, 236, 220, 255)
CANVAS_SHADE = (184, 174, 150, 255)
RIGGING = (64, 52, 44, 255)
STERN_GLASS = (214, 196, 140, 255)
SEA = (92, 116, 126, 220)
SEA_DEEP = (70, 92, 104, 228)
SEA_LIGHT = (170, 192, 196, 255)
BARK = (142, 74, 46, 255)
BARK_LIGHT = (180, 106, 70, 255)
BARK_SHADE = (104, 52, 34, 255)
BARK_DARK = (76, 38, 26, 255)
CORD = (196, 168, 112, 255)
CORD_DARK = (134, 108, 66, 255)
CLAY_PAD = (176, 150, 116, 255)
CLAY_PAD_SHADE = (138, 114, 86, 255)
FIRE = (255, 196, 60, 255)
FIRE_HOT = (255, 240, 170, 255)
FIRE_RED = (230, 100, 42, 255)
STICK = (96, 70, 48, 255)
SMOKE = (186, 184, 180, 255)


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


def _quad(tl: Point, tr: Point, br: Point, bl: Point, s: float, t: float) -> Point:
    """A point in the four-sided shape `tl`, `tr`, `br`, `bl`: `s` goes
    from the left side to the right side, `t` from the top to the bottom.
    Flat things seen a little from above are drawn with it."""
    return _mix(_mix(tl, tr, s), _mix(bl, br, s), t)


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


def _puff(f: K.Frame, x: float, y: float, r: float, colour: RGBA, rng: random.Random, lumps: int = 5) -> None:
    """A puff of smoke: round lumps about a middle."""
    for k in range(lumps):
        a = math.tau * k / lumps + rng.uniform(-0.3, 0.3)
        d = r * rng.uniform(0.35, 0.6)
        pr = r * rng.uniform(0.45, 0.65)
        f.ellipse(x + math.cos(a) * d, y + math.sin(a) * d * 0.8, pr, pr, colour, body=False)


def _flame(f: K.Frame, cx: float, base: float, width: float, height: float, lean: float, colour: RGBA) -> None:
    """One tongue of flame from `base` up to `height`, its tip moved by
    `lean`."""
    pts = [(cx - width, base), (cx - width * 0.8, base - height * 0.4), (cx - width * 0.3 + lean * 0.5, base - height * 0.75), (cx + lean, base - height),
           (cx + width * 0.4 + lean * 0.4, base - height * 0.6), (cx + width, base - height * 0.3), (cx + width * 0.9, base)]
    f.poly(pts, colour, body=False)


def _tuft(f: K.Frame, x: float, y: float, rng: random.Random, size: float = 1.0, fill: RGBA = GRASS, light: RGBA = GRASS_LIGHT) -> None:
    """A tuft of grass: thin blades that fan out from one root."""
    count = rng.randint(5, 8)
    for k in range(count):
        a = math.radians(-90.0 + (k - (count - 1) / 2.0) * 16.0 + rng.uniform(-6.0, 6.0))
        ln = size * rng.uniform(7.0, 12.0)
        tip = (x + math.cos(a) * ln, y + math.sin(a) * ln)
        nx, ny = -math.sin(a) * 1.1 * size, math.cos(a) * 1.1 * size
        f.poly([(x - nx, y - ny), tip, (x + nx, y + ny)], fill if k % 3 else light)


def _dense(poly: Sequence[Point], step: float) -> List[Point]:
    """The polygon with more points on its edges: one each `step`. A bent
    flag needs them."""
    out: List[Point] = []
    for a, b in zip(poly, list(poly[1:]) + [poly[0]]):
        count = max(1, int(math.ceil(math.hypot(b[0] - a[0], b[1] - a[1]) / step)))
        for k in range(count):
            out.append(_mix(a, b, k / float(count)))
    return out


def _clip_box(poly: Sequence[Point], x0: float, y0: float, x1: float, y1: float) -> List[Point]:
    """The part of the polygon `poly` inside the box from (x0, y0) to
    (x1, y1)."""
    def cut(pts: List[Point], inside: Callable[[Point], bool], cross: Callable[[Point, Point], Point]) -> List[Point]:
        out: List[Point] = []
        for k in range(len(pts)):
            a, b = pts[k - 1], pts[k]
            if inside(b):
                if not inside(a):
                    out.append(cross(a, b))
                out.append(b)
            elif inside(a):
                out.append(cross(a, b))
        return out

    def at_x(xc: float) -> Callable[[Point, Point], Point]:
        return lambda a, b: (xc, a[1] + (b[1] - a[1]) * (xc - a[0]) / (b[0] - a[0]))

    def at_y(yc: float) -> Callable[[Point, Point], Point]:
        return lambda a, b: (a[0] + (b[0] - a[0]) * (yc - a[1]) / (b[1] - a[1]), yc)

    pts = list(poly)
    for inside, cross in ((lambda p: p[0] >= x0, at_x(x0)), (lambda p: p[0] <= x1, at_x(x1)), (lambda p: p[1] >= y0, at_y(y0)), (lambda p: p[1] <= y1, at_y(y1))):
        if not pts:
            break
        pts = cut(pts, inside, cross)
    return pts


# ---------------------------------------------------------------------------
# The flags. A flag is a list of flat pieces in flag units (60 by 30). A
# map takes each point to the frame, so that the same pieces can fly or
# hang.
# ---------------------------------------------------------------------------

FLAG_W, FLAG_H = 60.0, 30.0


def _saltire_band(c: Point, corner: Point, w0: float, w1: float, side: float) -> List[Point]:
    """A band along the line from the middle `c` through `corner`, from the
    distance `w0` to `w1` on one side of the line (`side` is +1 or -1 in
    y)."""
    dx, dy = corner[0] - c[0], corner[1] - c[1]
    ln = math.hypot(dx, dy)
    ux, uy = dx / ln, dy / ln
    nx, ny = -uy, ux
    if ny * side < 0.0:
        nx, ny = -nx, -ny
    far = 200.0
    return [(c[0] + nx * w0, c[1] + ny * w0), (c[0] + ux * far + nx * w0, c[1] + uy * far + ny * w0),
            (c[0] + ux * far + nx * w1, c[1] + uy * far + ny * w1), (c[0] + nx * w1, c[1] + ny * w1)]


def _union_pieces(x0: float, y0: float, x1: float, y1: float, patrick: bool) -> List[Tuple[List[Point], RGBA]]:
    """The Union Flag in the box (x0, y0) to (x1, y1) of flag units. With
    `patrick` it is the flag of 1801, with the red saltire of St Patrick
    counterchanged in the white one: the broad white is above the red on
    the hoist side and below it on the fly side. Without it, it is the
    flag of 1606."""
    s = (y1 - y0) / 30.0
    c = ((x0 + x1) / 2.0, (y0 + y1) / 2.0)
    out: List[Tuple[List[Point], RGBA]] = [(_rect(x0, y0, x1, y1), FLAG_BLUE)]
    corners = {"tl": (x0, y0), "tr": (x1, y0), "br": (x1, y1), "bl": (x0, y1)}
    for name in ("tl", "br"):
        out.append((_clip_box(_saltire_band(c, corners[name], -3.0 * s, 3.0 * s, 1.0), x0, y0, x1, y1), FLAG_WHITE))
    for name in ("tr", "bl"):
        out.append((_clip_box(_saltire_band(c, corners[name], -3.0 * s, 3.0 * s, 1.0), x0, y0, x1, y1), FLAG_WHITE))
    if patrick:
        for name, side in (("tl", 1.0), ("tr", -1.0), ("br", -1.0), ("bl", 1.0)):
            band = _saltire_band(c, corners[name], 0.0, 2.0 * s, side)
            out.append((_clip_box(band, x0, y0, x1, y1), FLAG_RED))
    out.append((_rect(x0, c[1] - 5.0 * s, x1, c[1] + 5.0 * s), FLAG_WHITE))
    out.append((_rect(c[0] - 5.0 * s, y0, c[0] + 5.0 * s, y1), FLAG_WHITE))
    out.append((_rect(x0, c[1] - 3.0 * s, x1, c[1] + 3.0 * s), FLAG_RED))
    out.append((_rect(c[0] - 3.0 * s, y0, c[0] + 3.0 * s, y1), FLAG_RED))
    return out


def _draw_flag(f: K.Frame, pieces: Sequence[Tuple[List[Point], RGBA]], place: Callable[[float, float], Point], step: float = 2.0) -> None:
    """The flag `pieces`, each point moved to the frame by `place`. The
    whole flag is the body; the pieces are drawn on it."""
    whole = [place(x, y) for x, y in _dense(_rect(0.0, 0.0, FLAG_W, FLAG_H), step)]
    f.poly(whole, pieces[0][1])
    for poly, colour in pieces[1:]:
        if len(poly) >= 3:
            f.poly([place(x, y) for x, y in _dense(poly, step)], colour, body=False)


# ---------------------------------------------------------------------------
# The Willandra footprints.
# ---------------------------------------------------------------------------

#: The print of a bare foot, from the heel (u 0) to the toes (u 1), with
#: `v` across the foot (+ is the inner side, where the arch is). Units are
#: the length of the foot.
FOOT_OUTER = ((0.02, 0.0), (0.05, -0.1), (0.13, -0.15), (0.26, -0.15), (0.45, -0.15), (0.62, -0.19), (0.72, -0.2), (0.78, -0.16))
FOOT_INNER = ((0.79, 0.14), (0.75, 0.22), (0.66, 0.22), (0.56, 0.12), (0.44, 0.04), (0.32, 0.05), (0.2, 0.13), (0.08, 0.12))
#: The toes: (u, v, radius), from the big toe to the little toe.
FOOT_TOES = ((0.91, 0.14, 0.07), (0.885, 0.03, 0.045), (0.86, -0.05, 0.04), (0.835, -0.12, 0.036), (0.8, -0.19, 0.032))


def _footprint(f: K.Frame, x: float, y: float, length: float, facing: float, inner: float, ran: bool = False) -> None:
    """One print of a bare human foot, seen from a little above, its middle
    at (x, y). `facing` is +1 when the walker goes to the right; `inner` is
    the side (+1 down, -1 up) of the big toe. A print made by a runner has
    a deep ball and toes and only a light heel."""
    sq = 0.9

    def to(u: float, v: float) -> Point:
        return (x + facing * (u - 0.5) * length, y + inner * v * length * sq)

    outer = [p for p in FOOT_OUTER if not ran or p[0] > 0.3]
    inner_pts = [p for p in FOOT_INNER if not ran or p[0] > 0.3]
    sole = [to(u, v) for u, v in outer] + [to(u, v) for u, v in inner_pts]
    f.poly(sole, PRINT_WALL, body=False)
    floor = [(px, py + 0.5) for px, py in sole]
    cx = sum(px for px, _ in floor) / len(floor)
    cy = sum(py for _, py in floor) / len(floor)
    f.poly([(cx + (px - cx) * 0.86, cy + (py - cy) * 0.66) for px, py in floor], PRINT_FLOOR, body=False)
    if ran:
        # The heel touched only lightly; the ball pushed the clay back.
        hx, hy = to(0.12, 0.0)
        f.ellipse(hx, hy, length * 0.09, length * 0.05, PRINT_FLOOR, body=False)
        f.ink([to(0.30, -0.15), to(0.26, 0.0), to(0.30, 0.12)], 0.9, HARDPAN_LIGHT)
    for u, v, r in FOOT_TOES:
        tx, ty = to(u, v)
        rr = r * length * (1.15 if ran else 1.0)
        f.ellipse(tx, ty, rr, rr * 0.7, PRINT_WALL, body=False)
        f.ellipse(tx, ty + 0.3, rr * 0.6, rr * 0.4, PRINT_FLOOR, body=False)


def _trail(f: K.Frame, x0: float, x1: float, y: float, step: float, length: float, facing: float, ran: bool, rng: random.Random) -> None:
    """A trail of prints from `x0` to `x1` along the line `y`: left and
    right feet in turn, each a little to its own side of the line."""
    x = x0 if facing > 0 else x1
    left = True
    while (facing > 0 and x <= x1) or (facing < 0 and x >= x0):
        inner = facing * (1.0 if left else -1.0)
        _footprint(f, x + rng.uniform(-1.0, 1.0), y - inner * length * 0.12 + rng.uniform(-0.3, 0.3), length, facing, inner, ran)
        x += facing * step * rng.uniform(0.94, 1.06)
        left = not left


def _draw_mungo_footprints(anim: str, i: int, n: int):
    w, h = MUNGO_FOOTPRINTS_FRAME
    f = K.Frame(MUNGO_FOOTPRINTS_FRAME)
    rng = random.Random("history_mungo_footprints")
    # The pink-orange sand: it lies round the slab and over its edges.
    sand = [(6.0, 36.0), (12.0, 16.0), (40.0, 6.0), (150.0, 4.6), (250.0, 6.0), (278.0, 16.0), (282.0, 36.0), (276.0, 52.0), (240.0, 57.0),
            (150.0, 58.0), (50.0, 57.0), (12.0, 52.0)]
    f.poly(sand, DUNE)
    f.poly([(8.0, 46.0), (280.0, 46.0), (276.0, 52.0), (240.0, 57.0), (150.0, 58.0), (50.0, 57.0), (12.0, 52.0)], DUNE_SHADE, body=False)
    for x, y in ((24.0, 12.0), (140.0, 7.0), (262.0, 12.0)):
        f.ink([(x - 10.0, y), (x + 12.0, y - 0.6)], 0.8, DUNE_LIGHT)
    # The slab of hard clay: a flat top, and a thin broken front edge.
    side = [(16.0, 43.0), (272.0, 42.0), (270.0, 47.0), (230.0, 48.0), (214.0, 50.0), (160.0, 49.4), (120.0, 50.6), (70.0, 49.0), (40.0, 50.0),
            (18.0, 48.0)]
    f.poly(side, HARDPAN_SHADE, body=False)
    f.ink([(18.0, 46.0), (120.0, 46.8), (270.0, 45.4)], 0.6, HARDPAN_DARK)
    top = [(16.0, 43.0), (20.0, 18.0), (34.0, 10.6), (120.0, 8.6), (230.0, 9.0), (262.0, 12.0), (272.0, 22.0), (272.0, 42.0), (180.0, 44.0),
           (90.0, 44.4)]
    f.poly(top, HARDPAN, body=False)
    f.poly([(30.0, 13.0), (120.0, 10.0), (240.0, 11.0), (120.0, 12.4)], HARDPAN_LIGHT, body=False)
    # Fine cracks: short joined lines that cross the clay.
    for _ in range(40):
        x, y = rng.uniform(28.0, 260.0), rng.uniform(12.0, 42.0)
        pts = [(x, y)]
        for _ in range(rng.randint(2, 4)):
            a = rng.uniform(0.0, math.tau)
            x = min(266.0, max(22.0, x + math.cos(a) * rng.uniform(4.0, 9.0)))
            y = min(42.0, max(11.4, y + math.sin(a) * rng.uniform(1.0, 3.0)))
            pts.append((x, y))
        f.ink(pts, 0.45, HARDPAN_SHADE)
    # Sand drifts over the ends of the slab.
    f.poly([(16.0, 43.0), (18.0, 24.0), (30.0, 30.0), (38.0, 43.4)], DUNE, body=False)
    f.poly([(262.0, 12.0), (272.0, 20.0), (272.0, 42.0), (256.0, 42.4), (250.0, 28.0)], DUNE, body=False)
    f.ink([(20.0, 28.0), (30.0, 33.0)], 0.6, DUNE_LIGHT)
    f.ink([(254.0, 26.0), (266.0, 21.0)], 0.6, DUNE_LIGHT)
    # The three trails. The man who ran, at the back, with long strides;
    # in front, an adult and a child who walked side by side the other way.
    _trail(f, 48.0, 244.0, 16.6, 60.0, 22.0, 1.0, True, rng)
    _trail(f, 50.0, 240.0, 29.0, 31.0, 20.0, -1.0, False, rng)
    _trail(f, 58.0, 232.0, 39.4, 19.0, 12.0, -1.0, False, rng)
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# The shell midden and the old hearth.
# ---------------------------------------------------------------------------


def _mussel(f: K.Frame, x: float, y: float, degrees: float, size: float, open_: bool, blue: bool) -> None:
    """One freshwater mussel shell: a small long oval. A closed shell is
    dark blue-grey with a growth line; an open valve shows its pearly
    inside."""
    body = _oval(x, y, 7.0 * size, 3.4 * size, degrees, 14)
    if open_:
        f.poly(body, MUSSEL_SHADE, body=False)
        f.poly(_oval(x, y - 0.2, 5.8 * size, 2.4 * size, degrees, 14), NACRE, body=False)
        f.poly(_oval(x + 0.6 * size, y + 0.2, 3.0 * size, 1.0 * size, degrees, 10), NACRE_BLUE if blue else NACRE_PINK, body=False)
        return
    f.poly(body, MUSSEL_BLUE if blue else MUSSEL, body=False)
    f.poly(_oval(x, y + 0.6 * size, 6.0 * size, 1.6 * size, degrees, 12), MUSSEL_SHADE, body=False)
    a = math.radians(degrees)
    ux, uy = math.cos(a), math.sin(a)
    f.ink([(x - ux * 2.4 * size, y - uy * 2.4 * size - 0.5), (x + ux * 2.0 * size, y + uy * 2.0 * size - 0.7)], 0.4 * size, (150, 158, 176, 255))


def _fish_bones(f: K.Frame, x: float, y: float, length: float, degrees: float) -> None:
    """The burnt backbone of a small fish: a spine with short ribs and the
    bones of the head."""
    a = math.radians(degrees)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    p0, p1 = (x - ux * length / 2.0, y - uy * length / 2.0), (x + ux * length / 2.0, y + uy * length / 2.0)
    f.ink([p0, p1], 0.6, BURNT_BONE_DARK)
    for k in range(1, 7):
        p = _mix(p0, p1, 0.12 + k * 0.1)
        rib = 1.6 * (1.0 - abs(k - 3.5) / 5.0)
        f.ink([(p[0] - nx * rib * 0.9, p[1] - ny * rib * 0.45), (p[0] + nx * rib * 0.9, p[1] + ny * rib * 0.45)], 0.4, BURNT_BONE)
    f.poly([(p1[0], p1[1]), (p1[0] + ux * 2.4 + nx * 1.2, p1[1] + uy * 2.4 + ny * 0.6), (p1[0] + ux * 2.6 - nx * 1.2, p1[1] + uy * 2.6 - ny * 0.6)], BURNT_BONE, body=False)
    f.ink([(p0[0], p0[1]), (p0[0] - ux * 2.0 + nx * 1.4, p0[1] - uy * 2.0 + ny * 0.7)], 0.5, BURNT_BONE)
    f.ink([(p0[0], p0[1]), (p0[0] - ux * 2.0 - nx * 1.4, p0[1] - uy * 2.0 - ny * 0.7)], 0.5, BURNT_BONE)


def _clay_lump(f: K.Frame, x: float, y: float, r: float, rng: random.Random) -> None:
    """A lump of clay that the fire baked hard: round and a little rough."""
    pts = [(x + math.cos(a) * r * rng.uniform(0.82, 1.1), y + math.sin(a) * r * 0.78 * rng.uniform(0.82, 1.1)) for a in (math.tau * k / 9.0 for k in range(9))]
    f.poly(pts, BAKED)
    f.ellipse(x + r * 0.2, y + r * 0.3, r * 0.6, r * 0.35, BAKED_SHADE, body=False)
    f.dot(x - r * 0.3, y - r * 0.3, r * 0.3, BAKED_LIGHT)


def _draw_shell_midden(anim: str, i: int, n: int):
    w, h = SHELL_MIDDEN_FRAME
    f = K.Frame(SHELL_MIDDEN_FRAME)
    rng = random.Random("history_shell_midden")
    ground = 52.0
    # The pale sand.
    f.poly(_ring(80.0, ground, 74.0, 7.0, 0.0, 360.0, 40), SAND)
    f.poly(_ring(80.0, ground + 1.0, 72.0, 5.6, 10.0, 170.0, 20), SAND_SHADE, body=False)
    # The old hearth on the left: the far lumps of baked clay, the grey ash
    # and charcoal, then the near lumps.
    hx, hy = 38.0, ground - 2.0
    lumps = [(hx + math.cos(a) * 22.0, hy + math.sin(a) * 6.4, a) for a in (math.tau * (k + 0.3) / 11.0 for k in range(11))]
    for x, y, a in lumps:
        if math.sin(a) < 0.0:
            _clay_lump(f, x, y, rng.uniform(3.2, 4.2), rng)
    f.poly(_ring(hx, hy, 19.0, 5.2, 0.0, 360.0, 28), ASH)
    f.poly(_ring(hx + 2.0, hy + 1.0, 12.0, 2.8, 0.0, 360.0, 20), ASH_SHADE, body=False)
    f.ellipse(hx - 6.0, hy - 1.6, 6.0, 1.4, ASH_LIGHT, body=False)
    for _ in range(9):
        f.poly(_oval(hx + rng.uniform(-12.0, 12.0), hy + rng.uniform(-2.4, 2.4), rng.uniform(2.0, 3.6), rng.uniform(1.0, 1.6), rng.uniform(-30.0, 30.0), 8), CHAR,
               body=False)
    _fish_bones(f, hx + 4.0, hy - 1.0, 11.0, -8.0)
    for x, y, a in lumps:
        if math.sin(a) >= 0.0:
            _clay_lump(f, x, y, rng.uniform(3.4, 4.4), rng)
    _fish_bones(f, 70.0, ground + 2.4, 9.0, 12.0)
    # The heap of mussel shells: a low dome of what was eaten here.
    mx, mr, mh = 112.0, 40.0, 28.0

    def dome(x: float) -> float:
        return ground + 1.0 - mh * max(0.0, 1.0 - ((x - mx) / mr) ** 2) ** 0.6

    xs = [mx - mr + 2.0 * mr * k / 32.0 for k in range(33)]
    f.poly([(x, dome(x)) for x in xs] + [(mx + mr, ground + 2.0), (mx - mr, ground + 2.0)], HEAP)
    y = ground - mh + 2.0
    while y < ground + 1.6:
        rise = max(0.0, ground + 1.0 - y) / mh
        half = mr * math.sqrt(max(0.0, 1.0 - rise ** (1.0 / 0.6)))
        x = mx - half + rng.uniform(1.0, 4.0)
        while x < mx + half - 2.0:
            _mussel(f, x, y, rng.uniform(-35.0, 35.0), rng.uniform(1.1, 1.35), rng.random() < 0.22, rng.random() < 0.5)
            x += rng.uniform(6.4, 8.0)
        y += 3.4
    # A few shells that have rolled out onto the sand.
    for x, y, a in ((80.0, ground + 3.0, 20.0), (148.0, ground + 2.0, -30.0), (88.0, ground + 5.0, -10.0), (140.0, ground + 5.0, 40.0)):
        _mussel(f, x, y, a, 0.9, rng.random() < 0.5, rng.random() < 0.5)
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# The kumara store (rua).
# ---------------------------------------------------------------------------


def _frond(f: K.Frame, base: Point, tip: Point, bend: float, size: float) -> None:
    """A small fern frond: a curved stem with pairs of narrow leaflets that
    get shorter to the tip."""
    pts = []
    for k in range(13):
        u = k / 12.0
        p = _mix(base, tip, u)
        dx, dy = tip[0] - base[0], tip[1] - base[1]
        ln = math.hypot(dx, dy)
        nx, ny = -dy / ln, dx / ln
        b = bend * math.sin(math.pi * u)
        pts.append((p[0] + nx * b, p[1] + ny * b))
    for k in range(1, 12):
        a, b = pts[k], pts[k + 1]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1.0
        ux, uy = dx / ln, dy / ln
        leaf = size * (6.0 - 4.4 * k / 12.0)
        for side in (1.0, -1.0):
            nx, ny = -uy * side, ux * side
            tipp = (a[0] + nx * leaf + ux * leaf * 0.5, a[1] + ny * leaf + uy * leaf * 0.5)
            f.poly([(a[0] - ux * 0.8, a[1] - uy * 0.8), tipp, (a[0] + ux * 1.4, a[1] + uy * 1.4)], FERN if (k + int(side > 0)) % 2 else FERN_LIGHT)
    f.limb(pts, 1.2, TURF_SHADE)


def _draw_rua_pit(anim: str, i: int, n: int):
    w, h = RUA_PIT_FRAME
    f = K.Frame(RUA_PIT_FRAME)
    rng = random.Random("history_rua_pit")
    ground = 118.0
    # The bank: a low hump of clay with turf on top.
    bank = [(8.0, ground), (12.0, 98.0), (24.0, 72.0), (42.0, 54.0), (70.0, 42.0), (108.0, 38.0), (144.0, 44.0), (168.0, 60.0), (180.0, 84.0),
            (184.0, ground)]
    f.poly(bank, CLAY)
    f.poly([(150.0, 48.0), (168.0, 60.0), (180.0, 84.0), (184.0, ground), (150.0, ground)], CLAY_SHADE, body=False)
    for y, x0, x1 in ((84.0, 16.0, 60.0), (96.0, 12.0, 58.0), (90.0, 136.0, 178.0), (104.0, 140.0, 182.0)):
        f.ink([(x0, y), (_lerp(x0, x1, 0.5), y + 1.0), (x1, y - 0.4)], 0.6, CLAY_DARK)
    for _ in range(14):
        x, y = rng.uniform(20.0, 176.0), rng.uniform(70.0, 112.0)
        if not 62.0 < x < 130.0:
            f.ellipse(x, y, rng.uniform(1.0, 2.0), rng.uniform(0.8, 1.4), CLAY_SHADE, body=False)
    # The face cut into the bank round the doorway: flat and fresh.
    face = [(64.0, ground), (64.0, 64.0), (70.0, 58.0), (124.0, 56.0), (130.0, 62.0), (130.0, ground)]
    f.poly(face, CLAY_LIGHT, body=False)
    f.ink([(64.0, ground), (64.0, 64.0), (70.0, 58.0), (124.0, 56.0), (130.0, 62.0), (130.0, ground)], 0.8, CLAY_DARK)
    for x in range(70, 126, 7):
        f.ink([(float(x), 62.0), (float(x) + 1.0, 68.0)], 0.5, CLAY_SHADE)
    # The turf along the top of the bank, and grass and fern on it.
    crest = [(12.0, 98.0), (24.0, 72.0), (42.0, 54.0), (70.0, 42.0), (108.0, 38.0), (144.0, 44.0), (168.0, 60.0), (180.0, 84.0)]
    f.poly(crest + [(p[0] - (2.0 if p[0] > 108.0 else -2.0), p[1] + 7.0) for p in reversed(crest)], TURF, body=False)
    f.ink([(p[0], p[1] + 1.4) for p in crest[1:-1]], 1.0, TURF_LIGHT)
    for x, y in ((30.0, 66.0), (52.0, 49.0), (86.0, 40.0), (126.0, 40.0), (156.0, 52.0), (172.0, 70.0)):
        _tuft(f, x, y + 1.0, rng, 0.9, TURF, TURF_LIGHT)
    _frond(f, (64.0, 44.0), (42.0, 18.0), 6.0, 1.0)
    _frond(f, (70.0, 43.0), (92.0, 14.0), -5.0, 1.0)
    _frond(f, (140.0, 44.0), (162.0, 22.0), -4.0, 0.9)
    _frond(f, (24.0, 72.0), (12.0, 52.0), 3.0, 0.7)
    # The doorway: the dark store inside, plain timber posts, a lintel and
    # a sill.
    dx0, dx1, dy0, dy1 = 84.0, 112.0, 74.0, 110.0
    f.poly(_rect(dx0, dy0, dx1, dy1), INTERIOR, body=False)
    f.ink([(dx0 + 2.0, dy1 - 6.0), (dx1 - 2.0, dy1 - 6.0)], 0.6, (60, 46, 38, 255))
    for x in (dx0 - 3.0, dx1 + 3.0):
        f.poly(_rect(x - 3.0, dy0 - 2.0, x + 3.0, dy1 + 4.0), TIMBER)
        f.ink([(x - 1.6, dy0), (x - 1.6, dy1 + 2.0)], 0.8, TIMBER_LIGHT)
        f.ink([(x + 2.0, dy0), (x + 2.0, dy1 + 2.0)], 0.6, TIMBER_SHADE)
    f.poly(_rect(dx0 - 10.0, dy0 - 8.0, dx1 + 10.0, dy0 - 1.0), TIMBER)
    f.ink([(dx0 - 8.0, dy0 - 6.6), (dx1 + 8.0, dy0 - 6.6)], 0.8, TIMBER_LIGHT)
    f.ink([(dx0 - 8.0, dy0 - 2.4), (dx1 + 8.0, dy0 - 2.4)], 0.6, TIMBER_SHADE)
    f.poly(_rect(dx0 - 8.0, dy1, dx1 + 8.0, dy1 + 5.0), TIMBER_SHADE)
    f.ink([(dx0 - 7.0, dy1 + 1.0), (dx1 + 7.0, dy1 + 1.0)], 0.6, TIMBER_LIGHT)
    # The sliding door: a board in a groove under the lintel, pushed half
    # open to the left.
    f.poly(_rect(dx0 - 6.0, dy0, dx0 + 14.0, dy1), TIMBER_LIGHT)
    f.ink([(dx0 - 4.0, dy0 + 2.0), (dx0 - 4.0, dy1 - 2.0)], 0.5, TIMBER_SHADE)
    for x in (dx0 + 1.0, dx0 + 7.0):
        f.ink([(x, dy0 + 2.0), (x + 0.4, dy1 - 2.0)], 0.5, TIMBER_SHADE)
    f.ink([(dx0 + 14.0, dy0), (dx0 + 14.0, dy1)], 0.8, TIMBER_SHADE)
    f.ellipse(dx0 + 10.6, (dy0 + dy1) / 2.0, 1.4, 2.4, TIMBER_SHADE, body=False)
    # The ground in front, and the short drain that takes the rain away.
    f.poly([(40.0, ground), (56.0, ground - 4.0), (140.0, ground - 4.0), (170.0, ground + 1.0), (160.0, ground + 4.0), (50.0, ground + 4.0)], CLAY_SHADE)
    f.ink([(58.0, ground - 2.6), (138.0, ground - 2.6)], 0.6, CLAY_LIGHT)
    f.poly([(94.0, dy1 + 5.0), (106.0, dy1 + 5.0), (166.0, ground + 1.0), (162.0, ground + 3.6), (150.0, ground + 3.6)], CLAY_DARK, body=False)
    f.poly([(100.0, dy1 + 6.0), (106.0, dy1 + 6.0), (160.0, ground + 1.6), (154.0, ground + 2.6)], WATER, body=False)
    f.ink([(104.0, dy1 + 6.4), (156.0, ground + 1.8)], 0.6, WATER_LIGHT)
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# The pounamu adze, its mat and the grinding block.
# ---------------------------------------------------------------------------


def _draw_pounamu_adze(anim: str, i: int, n: int):
    w, h = POUNAMU_ADZE_FRAME
    f = K.Frame(POUNAMU_ADZE_FRAME)
    rng = random.Random("history_pounamu_adze")
    # The plaited flax mat, seen a little from above: a checker of pale
    # gold strips, with a plain border.
    tl, tr, br, bl = (16.0, 26.0), (88.0, 26.0), (96.0, 56.0), (6.0, 56.0)
    f.poly([tl, tr, br, bl], FLAX)
    cols, rows = 12, 6
    for r in range(rows):
        for c in range(cols):
            s0, s1 = 0.04 + 0.92 * c / cols, 0.04 + 0.92 * (c + 1) / cols
            t0, t1 = 0.08 + 0.84 * r / rows, 0.08 + 0.84 * (r + 1) / rows
            cell = [_quad(tl, tr, br, bl, s0, t0), _quad(tl, tr, br, bl, s1, t0), _quad(tl, tr, br, bl, s1, t1), _quad(tl, tr, br, bl, s0, t1)]
            f.poly(cell, FLAX_LIGHT if (r + c) % 2 else FLAX_SHADE, body=False)
            f.ink([cell[0], cell[1]], 0.4, FLAX_SHADE)
    for t in (0.04, 0.96):
        f.ink([_quad(tl, tr, br, bl, 0.02, t), _quad(tl, tr, br, bl, 0.98, t)], 1.0, FLAX_SHADE)
    # The adze blade: long, polished and deep green, thicker at the butt,
    # with a light bevel and a light, thin cutting edge.
    butt, edge = (22.0, 44.0), (82.0, 38.0)
    dx, dy = edge[0] - butt[0], edge[1] - butt[1]
    ln = math.hypot(dx, dy)
    ux, uy = dx / ln, dy / ln
    nx, ny = -uy, ux

    def at(u: float, v: float) -> Point:
        p = _mix(butt, edge, u)
        return (p[0] + nx * v, p[1] + ny * v * 0.7)

    def half(u: float) -> float:
        return 4.2 + 3.4 * u

    us = [k / 16.0 for k in range(17)]
    # The side of the blade shows as a dark band under its flat face.
    side = [at(u, half(u)) for u in us] + [at(u, half(u) + 2.2) for u in reversed(us)]
    f.poly(side, POUNAMU_DEEP)
    blade = [at(0.0, -half(0.0) * 0.8), at(0.02, -half(0.02))] + [at(u, -half(u)) for u in us[1:]] + [at(1.03, 0.0)] + [at(u, half(u)) for u in reversed(us[1:])] + [
        at(0.02, half(0.02)), at(0.0, half(0.0) * 0.8)]
    f.poly(blade, POUNAMU)
    # The bevel at the cutting end: a lighter facet, ground thin, and the
    # bright edge.
    f.poly([at(0.8, -half(0.8)), at(1.0, -half(1.0)), at(1.03, 0.0), at(1.0, half(1.0)), at(0.8, half(0.8))], POUNAMU_LIGHT, body=False)
    f.ink([at(0.8, -half(0.8)), at(0.8, half(0.8))], 0.7, POUNAMU_DEEP)
    f.ink([at(0.99, -half(0.99) + 0.6), at(1.03, 0.0), at(0.99, half(0.99) - 0.6)], 0.9, POUNAMU_GLOSS)
    # The polish: light along the upper edge, and a few pale flecks where
    # the light goes through the stone.
    f.ink([at(0.04, -half(0.04) + 0.8), at(0.78, -half(0.78) + 0.9)], 0.9, POUNAMU_LIGHT)
    f.ink([at(0.2, -0.6), at(0.55, -1.2)], 0.7, POUNAMU_GLOSS)
    for u, v in ((0.3, 1.8), (0.48, 2.6), (0.66, 0.4), (0.9, -1.4)):
        p = at(u, v)
        f.dot(p[0], p[1], 0.7, POUNAMU_LIGHT)
    # The grinding block of grey sandstone, with the groove that the adze
    # wore in it.
    f.poly([(98.0, 42.0), (120.0, 42.0), (124.0, 36.0), (124.0, 50.0), (120.0, 56.0), (98.0, 56.0)], SANDSTONE_SHADE)
    f.poly(_rect(98.0, 42.0, 120.0, 56.0), SANDSTONE)
    f.poly([(98.0, 42.0), (103.0, 34.0), (124.0, 34.0), (120.0, 42.0)], SANDSTONE_LIGHT)
    f.poly([(102.0, 39.6), (104.0, 37.6), (120.0, 36.4), (118.0, 38.6)], SANDSTONE_SHADE, body=False)
    f.ink([(103.0, 39.8), (118.4, 38.8)], 0.6, SANDSTONE_LIGHT)
    for _ in range(10):
        f.dot(rng.uniform(100.0, 118.0), rng.uniform(44.0, 54.0), 0.5, SANDSTONE_SHADE)
    f.ink([(100.0, 48.0), (106.0, 47.0), (110.0, 49.0)], 0.5, SANDSTONE_SHADE)
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# The Ha'amonga 'a Maui.
# ---------------------------------------------------------------------------


def _weather(f: K.Frame, x0: float, x1: float, y0: float, y1: float, rng: random.Random, count: int) -> None:
    """The face of old coral limestone: small pits, the round marks of
    fossil coral, dark streaks and patches of lichen."""
    for _ in range(count):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        f.ellipse(x, y, rng.uniform(0.8, 1.8), rng.uniform(0.6, 1.4), CORAL_DARK, body=False)
    for _ in range(count // 4):
        x, y = rng.uniform(x0 + 4.0, x1 - 4.0), rng.uniform(y0 + 4.0, y1 - 4.0)
        r = rng.uniform(2.0, 3.6)
        f.ink(_ring(x, y, r, r * 0.8, 0.0, 360.0, 12), 0.5, CORAL_SHADE)
        f.dot(x, y, 0.7, CORAL_SHADE)
    for _ in range(count // 6):
        x = rng.uniform(x0 + 2.0, x1 - 2.0)
        ya = rng.uniform(y0, y1 - 30.0)
        f.ink([(x, ya), (x + rng.uniform(-1.0, 1.0), ya + rng.uniform(16.0, 40.0))], rng.uniform(0.8, 1.6), K.alpha(CORAL_DARK, 0.5))
    for _ in range(count // 8):
        x, y = rng.uniform(x0 + 6.0, x1 - 6.0), rng.uniform(y0 + 6.0, y1 - 6.0)
        colour = rng.choice((LICHEN, LICHEN, LICHEN_ORANGE, LICHEN_GREY))
        for _ in range(7):
            f.ellipse(x + rng.uniform(-5.0, 5.0), y + rng.uniform(-3.6, 3.6), rng.uniform(1.2, 2.6), rng.uniform(1.0, 2.0), colour, body=False)


def _draw_haamonga(anim: str, i: int, n: int):
    w, h = HAAMONGA_FRAME
    f = K.Frame(HAAMONGA_FRAME)
    rng = random.Random("history_haamonga")
    top = HAAMONGA_TOP
    ground = 438.0
    # The two uprights: 1.4 m wide and 4 m apart. Their tops are flat and
    # level; their sides are worn and a little rough.
    for x0, x1 in ((30.0, 136.0), (440.0, 546.0)):
        left = [(x0 + 2.0, ground + 2.0), (x0 - 1.0, 360.0), (x0 + 1.0, 250.0), (x0 - 0.6, 150.0), (x0 + 2.0, top + 10.0), (x0 + 10.0, top)]
        right = [(x1 - 10.0, top), (x1 - 2.0, top + 10.0), (x1 + 0.6, 160.0), (x1 - 1.0, 280.0), (x1 + 1.0, ground + 2.0)]
        f.poly(left + right, CORAL)
        sx = x1 - 34.0
        f.poly([(sx, top + 2.0), (x1 - 10.0, top + 2.0), (x1 - 2.0, top + 10.0), (x1 + 0.6, 160.0), (x1 - 1.0, 280.0), (x1 + 1.0, ground + 2.0),
                (sx + 4.0, ground + 2.0), (sx - 2.0, 300.0), (sx + 2.0, 180.0)], CORAL_SHADE, body=False)
        f.ink([(x0 + 4.0, top + 12.0), (x0 + 2.0, 200.0), (x0 + 4.0, 380.0)], 1.4, CORAL_LIGHT)
        # A few worn hollows, where softer coral has weathered out.
        for _ in range(4):
            hx, hy = rng.uniform(x0 + 16.0, x1 - 20.0), rng.uniform(150.0, 400.0)
            hw, hh = rng.uniform(6.0, 12.0), rng.uniform(4.0, 9.0)
            f.ellipse(hx, hy, hw, hh, CORAL_SHADE, body=False)
            f.ellipse(hx + 1.0, hy + hh * 0.3, hw * 0.7, hh * 0.6, CORAL_DARK, body=False)
            f.ink(_ring(hx, hy, hw, hh, 200.0, 340.0, 8), 0.8, CORAL_LIGHT)
        _weather(f, x0 + 4.0, x1 - 4.0, top + 50.0, ground - 10.0, rng, 90)
        # Cracks in the stone.
        for _ in range(3):
            cx, cy = rng.uniform(x0 + 10.0, x1 - 10.0), rng.uniform(160.0, 380.0)
            pts = [(cx, cy)]
            for _ in range(4):
                cx += rng.uniform(-6.0, 6.0)
                cy += rng.uniform(6.0, 14.0)
                pts.append((cx, cy))
            f.ink(pts, 0.9, CORAL_DARK)
    # The lintel: 5.8 m long, laid in a notch cut in the top of each
    # upright. Its top is flush with theirs, so the walk line is level.
    lx0, lx1, ly1 = 68.0, 508.0, top + 44.0
    f.poly([(lx0, top), (lx1, top), (lx1, ly1), (440.0, ly1), (430.0, ly1 + 1.6), (300.0, ly1 + 0.6), (200.0, ly1 + 2.0), (136.0, ly1), (lx0, ly1)], CORAL)
    f.poly([(lx0, top + 30.0), (lx1, top + 30.0), (lx1, ly1), (440.0, ly1), (300.0, ly1 + 0.6), (200.0, ly1 + 2.0), (136.0, ly1), (lx0, ly1)], CORAL_SHADE,
           body=False)
    f.ink([(lx0 + 2.0, top + 3.0), (lx1 - 2.0, top + 3.0)], 1.4, CORAL_LIGHT)
    # The joints of the notches: the ends of the lintel and the floor of
    # each notch show as fine dark lines on the uprights.
    for x in (lx0, lx1):
        f.ink([(x, top + 1.0), (x, ly1)], 1.2, CORAL_DARK)
    f.ink([(lx0, ly1), (136.0, ly1)], 1.2, CORAL_DARK)
    f.ink([(440.0, ly1), (lx1, ly1)], 1.2, CORAL_DARK)
    _weather(f, lx0 + 6.0, lx1 - 6.0, top + 10.0, ly1 - 4.0, rng, 70)
    # Lichen and pits near the tops of the uprights, under the top edge.
    _weather(f, 34.0, 132.0, ly1 + 4.0, top + 90.0, rng, 18)
    _weather(f, 444.0, 542.0, ly1 + 4.0, top + 90.0, rng, 18)
    _weather(f, 34.0, lx0 - 2.0, top + 8.0, ly1, rng, 8)
    _weather(f, lx1 + 2.0, 542.0, top + 8.0, ly1, rng, 8)
    # The top edge: one straight line, level from end to end.
    f.ink([(40.0, top + 0.6), (536.0, top + 0.6)], 1.0, CORAL_LIGHT)
    # Grass at the foot of the stones.
    for x0, x1 in ((24.0, 144.0), (432.0, 554.0)):
        x = x0
        while x < x1:
            _tuft(f, x, ground + 3.0, rng, rng.uniform(1.6, 2.4))
            x += rng.uniform(9.0, 14.0)
    return A.finish(f, width=1.6)


# ---------------------------------------------------------------------------
# The ngatu, the beater and the anvil.
# ---------------------------------------------------------------------------


def _draw_ngatu_board(anim: str, i: int, n: int):
    w, h = NGATU_BOARD_FRAME
    f = K.Frame(NGATU_BOARD_FRAME)
    rng = random.Random("history_ngatu_board")
    # The cloth lies flat, seen a little from above: its far edge is short
    # of its near edge.
    tl, tr, br, bl = (16.0, 14.0), (220.0, 14.0), (228.0, 50.0), (8.0, 50.0)

    def q(s: float, t: float) -> Point:
        return _quad(tl, tr, br, bl, s, t)

    edge_top = [q(k / 24.0, 0.0) for k in range(25)]
    edge_bot = [q(k / 24.0, 1.0) for k in range(25)]
    edge_top = [(x, y + (0.6 if k % 3 == 1 else 0.0)) for k, (x, y) in enumerate(edge_top)]
    edge_bot = [(x, y - (0.6 if k % 4 == 2 else 0.0)) for k, (x, y) in enumerate(edge_bot)]
    f.poly(edge_top + list(reversed(edge_bot)), NGATU)
    f.poly([q(k / 24.0, 0.86) for k in range(25)] + list(reversed(edge_bot)), NGATU_SHADE, body=False)
    # The border lines.
    for t in (0.07, 0.11, 0.89, 0.93):
        f.ink([q(0.02, t), q(0.98, t)], 0.8, DYE_DARK)
    for s in (0.015, 0.985):
        f.ink([q(s, 0.07), q(s, 0.93)], 0.8, DYE_DARK)
    # A band of triangles at each side, pointing in to the middle.
    count = 30
    for t0, t1 in ((0.14, 0.27), (0.86, 0.73)):
        for k in range(count):
            s0, s1 = 0.03 + 0.94 * k / count, 0.03 + 0.94 * (k + 1) / count
            f.poly([q(s0, t0), q(s1, t0), q((s0 + s1) / 2.0, t1)], DYE_BROWN if k % 2 else DYE_RED, body=False)
    # Rows of dots.
    for t in (0.31, 0.69):
        for k in range(60):
            p = q(0.03 + 0.94 * (k + 0.5) / 60.0, t)
            f.dot(p[0], p[1], 0.7, DYE_DARK)
    # The band of large square panels: plain shapes, a filled diamond in
    # one, a cross of lines in the next.
    panels = 14
    for k in range(panels):
        s0, s1 = 0.03 + 0.94 * k / panels, 0.03 + 0.94 * (k + 1) / panels
        t0, t1 = 0.36, 0.64
        cell = [q(s0, t0), q(s1, t0), q(s1, t1), q(s0, t1)]
        f.ink(cell + [cell[0]], 0.8, DYE_DARK)
        sm, tm = (s0 + s1) / 2.0, (t0 + t1) / 2.0
        ds, dt = (s1 - s0) * 0.36, (t1 - t0) * 0.36
        if k % 2 == 0:
            f.poly([q(sm, tm - dt), q(sm + ds, tm), q(sm, tm + dt), q(sm - ds, tm)], DYE_RED, body=False)
            c = q(sm, tm)
            f.dot(c[0], c[1], 0.8, NGATU)
        else:
            f.ink([q(s0 + 0.004, t0 + 0.03), q(s1 - 0.004, t1 - 0.03)], 0.8, DYE_BROWN)
            f.ink([q(s1 - 0.004, t0 + 0.03), q(s0 + 0.004, t1 - 0.03)], 0.8, DYE_BROWN)
    # A soft fold across the cloth.
    f.ink([q(0.42, 0.0), q(0.44, 1.0)], 0.6, K.alpha(NGATU_SHADE, 0.8))
    # The anvil: a short beam of hardwood with a flat top, its end grain
    # to the left.
    ax0, ax1, ay0, ay1 = 236.0, 282.0, 38.0, 51.0
    f.poly([(ax0 + 2.0, ay0), (ax1 - 2.0, ay0), (ax1, ay0 + 2.0), (ax1, ay1 - 2.0), (ax1 - 2.0, ay1), (ax0 + 2.0, ay1), (ax0, ay1 - 2.0), (ax0, ay0 + 2.0)],
           HARDWOOD)
    f.poly(_rect(ax0 + 1.0, ay0 + 8.0, ax1 - 1.0, ay1 - 0.6), HARDWOOD_SHADE, body=False)
    f.ink([(ax0 + 6.0, ay0 + 1.4), (ax1 - 3.0, ay0 + 1.4)], 0.9, HARDWOOD_LIGHT)
    f.ink([(ax0 + 10.0, ay0 + 5.0), (ax1 - 12.0, ay0 + 5.4)], 0.4, HARDWOOD_SHADE)
    f.poly(_rect(ax0 + 0.6, ay0 + 0.6, ax0 + 5.0, ay1 - 0.6), HARDWOOD_LIGHT, body=False)
    f.ink(_ring(ax0 + 2.8, (ay0 + ay1) / 2.0, 1.2, 3.4, 0.0, 360.0, 10), 0.4, HARDWOOD_SHADE)
    # The beater: a round handle and a square head, 3 grooves showing.
    b0, b1 = (240.0, 35.4), (282.0, 33.0)
    f.limb([b0, _mix(b0, b1, 0.36)], 3.2, HARDWOOD_LIGHT)
    hd0, hd1 = _mix(b0, b1, 0.34), b1
    dx, dy = hd1[0] - hd0[0], hd1[1] - hd0[1]
    ln = math.hypot(dx, dy)
    nx, ny = -dy / ln, dx / ln
    head = [(hd0[0] - nx * 3.6, hd0[1] - ny * 3.6), (hd1[0] - nx * 3.6, hd1[1] - ny * 3.6), (hd1[0] + nx * 3.6, hd1[1] + ny * 3.6),
            (hd0[0] + nx * 3.6, hd0[1] + ny * 3.6)]
    f.poly(head, HARDWOOD)
    f.poly([hd0, hd1, head[2], head[3]], HARDWOOD_SHADE, body=False)
    for k in range(5):
        v = -3.0 + k * 1.5
        f.ink([(hd0[0] + 2.0 + nx * v, hd0[1] + ny * v), (hd1[0] - 1.0 + nx * v, hd1[1] + ny * v)], 0.4, HARDWOOD_SHADE if k % 2 else HARDWOOD_LIGHT)
    del rng
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# The Samoan fale.
# ---------------------------------------------------------------------------


def _draw_samoan_fale(anim: str, i: int, n: int):
    w, h = SAMOAN_FALE_FRAME
    f = K.Frame(SAMOAN_FALE_FRAME)
    rng = random.Random("history_samoan_fale")
    cx = w / 2.0
    eave, floor, ground = 150.0, 206.0, 248.0
    # The platform (paepae): a front face of round stones, and a top of
    # pale coral gravel.
    f.poly([(14.0, floor + 4.0), (306.0, floor + 4.0), (310.0, ground), (10.0, ground)], STONE_SHADE)
    y = floor + 10.0
    row = 0
    while y < ground - 2.0:
        x = 16.0 + (7.0 if row % 2 else 0.0)
        while x < 304.0:
            rx = rng.uniform(6.0, 9.0)
            f.ellipse(x + rx, y, rx, 5.4, STONE if rng.random() < 0.7 else STONE_LIGHT, body=False)
            f.ellipse(x + rx - 1.6, y - 1.6, rx * 0.5, 1.6, STONE_LIGHT, body=False)
            x += 2.0 * rx + 1.0
        y += 9.4
        row += 1
    f.poly([(22.0, floor - 4.0), (298.0, floor - 4.0), (306.0, floor + 5.0), (14.0, floor + 5.0)], GRAVEL)
    for _ in range(90):
        f.dot(rng.uniform(22.0, 300.0), rng.uniform(floor - 3.0, floor + 4.4), 0.6, GRAVEL_SHADE)
    f.poly([(64.0, floor - 3.0), (256.0, floor - 3.0), (260.0, floor + 1.0), (60.0, floor + 1.0)], MAT, body=False)
    f.ink([(62.0, floor + 0.4), (258.0, floor + 0.4)], 0.6, MAT_SHADE)
    # The posts at the back of the ring, the two middle posts, and the
    # blinds rolled up at the back.
    for x in (58.0, 108.0, 212.0, 262.0):
        f.limb([(x, eave), (x, floor - 3.0)], 4.0, POST_SHADE)
    for x in (148.0, 172.0):
        f.limb([(x, eave - 10.0), (x, floor - 2.0)], 7.0, POST)
        f.ink([(x - 1.6, eave), (x - 1.6, floor - 4.0)], 1.0, POST_LIGHT)
    for xa, xb in ((62.0, 104.0), (112.0, 144.0), (176.0, 208.0), (216.0, 258.0)):
        f.poly(_rect(xa, eave + 1.0, xb, eave + 6.0), BLIND_SHADE)
    # The roof: a big dome of thatch that comes low over the posts.
    hw, hh, p = 152.0, 128.0, 2.4

    def half(y: float) -> float:
        u = max(0.0, min(1.0, (eave - y) / hh))
        return hw * max(0.0, 1.0 - u ** p) ** (1.0 / p)

    ys = [eave - hh * k / 40.0 for k in range(41)]
    roof = [(cx - half(y), y) for y in ys] + [(cx + half(y), y) for y in reversed(ys)]
    fringe = []
    for k in range(41):
        x = cx + hw - 2.0 * hw * k / 40.0
        fringe.append((x, eave + (3.0 if k % 2 else 0.0)))
    f.poly(roof[:41] + roof[41:] + fringe, THATCH)
    _thatch_rows(f, lambda y: cx - half(y) + 2.0, lambda y: cx + half(y) - 2.0, eave - hh + 8.0, eave - 6.0, 7.0, rng, THATCH_LIGHT, THATCH_SHADE)
    f.poly([(cx + half(y) * 0.55, y) for y in ys] + [(cx + half(y), y) for y in reversed(ys)], K.alpha(THATCH_SHADE, 0.55), body=False)
    f.poly([(cx - half(y) * 0.92, y) for y in ys[4:34]] + [(cx - half(y) * 0.72, y) for y in reversed(ys[4:34])], K.alpha(THATCH_LIGHT, 0.5), body=False)
    f.poly(_rect(cx - hw + 2.0, eave - 6.0, cx + hw - 2.0, eave), THATCH_DARK, body=False)
    for k in range(76):
        x = cx - hw + 4.0 + k * (2.0 * hw - 8.0) / 75.0
        f.ink([(x, eave - 6.0), (x + rng.uniform(-0.6, 0.6), eave + rng.uniform(1.0, 3.0))], 0.7, THATCH_SHADE)
    # The front posts of the ring, and the blinds rolled up between them.
    posts = (34.0, 84.0, 134.0, 186.0, 236.0, 286.0)
    for xa, xb in zip(posts[:-1], posts[1:]):
        f.poly(_rect(xa + 5.0, eave + 2.0, xb - 5.0, eave + 10.0), BLIND)
        f.ink([(xa + 6.0, eave + 6.0), (xb - 6.0, eave + 6.0)], 0.6, BLIND_SHADE)
        for x in range(int(xa) + 8, int(xb) - 6, 4):
            f.ink([(float(x), eave + 2.6), (float(x) + 2.0, eave + 9.4)], 0.4, BLIND_SHADE)
        for x in (xa + 12.0, xb - 12.0):
            f.ink([(x, eave + 1.0), (x, eave + 11.0)], 1.0, POST_SHADE)
    for x in posts:
        f.limb([(x, eave - 2.0), (x, floor + 3.0)], 6.0, POST)
        f.ink([(x - 1.4, eave), (x - 1.4, floor + 1.0)], 1.0, POST_LIGHT)
        f.ink([(x + 1.8, eave), (x + 1.8, floor + 1.0)], 0.6, POST_SHADE)
    return A.finish(f, width=1.4)


# ---------------------------------------------------------------------------
# The kava bowl.
# ---------------------------------------------------------------------------


def _draw_kava_bowl(anim: str, i: int, n: int):
    w, h = KAVA_BOWL_FRAME
    f = K.Frame(KAVA_BOWL_FRAME)
    rng = random.Random("history_kava_bowl")
    ground = 64.0
    cx, rim, rx, ry = 56.0, 28.0, 41.0, 8.6
    belly = 52.0
    # The legs: ten short legs in a ring under the bowl, a little splayed.
    # The far ones go first.
    legs = [math.tau * (k + 0.5) / 10.0 for k in range(10)]
    for a in legs:
        if math.sin(a) < 0.0:
            x = cx + math.cos(a) * 24.0
            f.limb([(x, belly - 6.0 + math.sin(a) * 3.0), (x + math.cos(a) * 4.0, ground - 4.0 + math.sin(a) * 2.0)], 5.0, TANOA_SHADE)
    # The bowl: wide and shallow, cut from one block, with a round belly.
    def depth(a: float) -> float:
        return rim + (belly - rim) * math.sin(math.radians(a))

    body = _ring(cx, rim, rx, ry, 180.0, 360.0, 20) + [(cx + rx * math.cos(math.radians(a)) * (1.0 - 0.12 * math.sin(math.radians(a))), depth(a))
                                                     for a in range(0, 181, 9)]
    f.poly(body, TANOA)
    f.poly([(cx + rx * math.cos(math.radians(a)) * (1.0 - 0.12 * math.sin(math.radians(a))), depth(a)) for a in range(0, 100, 9)]
           + [(cx + 4.0, rim + 14.0), (cx + rx - 6.0, rim + 6.0)], TANOA_SHADE, body=False)
    f.ink([(cx + (rx - 5.0) * math.cos(math.radians(a)) * (1.0 - 0.12 * math.sin(math.radians(a))), depth(a) - 4.0) for a in range(118, 166, 8)], 1.0, TANOA_LIGHT)
    # The rim, the inside and the kava.
    f.poly(_ring(cx, rim, rx, ry, 0.0, 360.0, 36), TANOA_LIGHT)
    f.poly(_ring(cx, rim + 0.6, rx - 3.4, ry - 2.2, 0.0, 360.0, 36), TANOA_SHADE, body=False)
    f.poly(_ring(cx, rim + 1.6, rx - 5.0, ry - 3.6, 0.0, 360.0, 36), KAVA, body=False)
    f.poly(_ring(cx, rim + 1.6, rx - 5.0, ry - 3.6, 20.0, 160.0, 14), KAVA_SHADE, body=False)
    f.ink([(cx - 18.0, rim), (cx - 6.0, rim - 0.6)], 0.8, KAVA_LIGHT)
    # The near legs.
    for a in legs:
        if math.sin(a) >= 0.0:
            x = cx + math.cos(a) * 28.0
            top = belly - 6.0 + math.sin(a) * 3.0
            foot = (x + math.cos(a) * 5.0, ground - 2.0 + math.sin(a) * 1.0)
            f.limb([(x, top), foot], 5.6, TANOA)
            f.ink([(x - 1.4, top + 1.0), (foot[0] - 1.4, foot[1] - 2.0)], 0.8, TANOA_LIGHT)
    # The strainer: a bundle of pale hibiscus fibre over the left rim.
    sx = cx - rx + 2.0
    for k in range(12):
        x0 = sx + 10.0 + k * 0.6
        tip = (sx - 6.0 + k * 0.7 + rng.uniform(-1.0, 1.0), rim + 18.0 + rng.uniform(-3.0, 4.0))
        f.limb([(x0, rim + 1.0), (sx + 2.0 + k * 0.3, rim - 3.0), (sx - 3.0 + k * 0.5, rim + 4.0), tip], 1.2, HIBISCUS if k % 3 else HIBISCUS_SHADE)
    f.ellipse(sx + 1.0, rim - 2.0, 5.0, 2.6, HIBISCUS)
    f.ink([(sx - 3.0, rim - 2.0), (sx + 5.0, rim - 3.0)], 0.6, HIBISCUS_SHADE)
    # The coconut-shell cup on the ground, open side up.
    ux, uy = 106.0, ground - 9.0
    f.poly(_ring(ux, uy, 11.0, 3.2, 180.0, 360.0, 12) + _ring(ux, uy, 11.0, 8.0, 0.0, 180.0, 16), SHELL_CUP)
    f.poly(_ring(ux, uy, 11.0, 3.2, 0.0, 360.0, 20), SHELL_CUP_LIGHT)
    f.poly(_ring(ux, uy + 0.4, 9.6, 2.2, 0.0, 360.0, 20), SHELL_CUP_INNER, body=False)
    f.ink(_ring(ux, uy + 1.0, 8.0, 6.0, 30.0, 70.0, 6), 0.8, SHELL_CUP_LIGHT)
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# The Treaty House.
# ---------------------------------------------------------------------------


def _sash(f: K.Frame, x0: float, y0: float, x1: float, y1: float) -> None:
    """A sash window of six panes over six, in a white frame, with a sill."""
    f.poly(_rect(x0 - 2.0, y0 - 2.0, x1 + 2.0, y1 + 2.0), WHITE)
    f.poly(_rect(x0, y0, x1, y1), GLASS, body=False)
    for k in range(1, 3):
        x = _lerp(x0, x1, k / 3.0)
        f.ink([(x, y0), (x, y1)], 1.0, WHITE)
    ym = (y0 + y1) / 2.0
    for y in (_lerp(y0, ym, 0.5), _lerp(ym, y1, 0.5)):
        f.ink([(x0, y), (x1, y)], 1.0, WHITE)
    f.ink([(x0, ym), (x1, ym)], 2.0, WHITE)
    for k in range(3):
        xa = _lerp(x0, x1, k / 3.0) + 2.0
        f.ink([(xa, y0 + 2.0), (xa + 3.0, y0 + 5.0)], 0.6, GLASS_LIGHT)
        f.ink([(xa, ym + 2.0), (xa + 3.0, ym + 5.0)], 0.6, GLASS_LIGHT)
    f.poly(_rect(x0 - 4.0, y1 + 2.0, x1 + 4.0, y1 + 5.0), WHITE)
    f.ink([(x0 - 3.0, y1 + 4.4), (x1 + 3.0, y1 + 4.4)], 0.6, WHITE_DARK)


def _draw_treaty_house(anim: str, i: int, n: int):
    w, h = TREATY_HOUSE_FRAME
    f = K.Frame(TREATY_HOUSE_FRAME)
    rng = random.Random("history_treaty_house")
    ground = 216.0
    wx0, wx1 = 40.0, 280.0
    eave, ridge = 98.0, 40.0
    vtop, vfront = 108.0, 126.0
    deck = 200.0
    # The low brick chimney behind the ridge.
    chx = 216.0
    f.poly(_rect(chx, ridge - 14.0, chx + 16.0, ridge + 20.0), BRICK)
    f.poly(_rect(chx + 10.0, ridge - 14.0, chx + 16.0, ridge + 20.0), BRICK_SHADE, body=False)
    for k in range(5):
        y = ridge - 10.0 + k * 5.0
        f.ink([(chx, y), (chx + 16.0, y)], 0.5, MORTAR)
        xo = chx + (4.0 if k % 2 else 8.0)
        f.ink([(xo, y), (xo, y + 5.0)], 0.5, MORTAR)
    f.poly(_rect(chx - 2.0, ridge - 18.0, chx + 18.0, ridge - 14.0), BRICK_SHADE)
    # The white walls of the house.
    f.poly(_rect(wx0, eave - 2.0, wx1, deck), WHITE)
    for y in range(int(eave) + 4, int(deck), 5):
        f.ink([(wx0 + 1.0, float(y)), (wx1 - 1.0, float(y))], 0.5, WHITE_SHADE)
    # The hipped roof of grey shingles.
    roof = [(wx0 - 12.0, eave), (wx1 + 12.0, eave), (wx1 - 76.0, ridge), (wx0 + 76.0, ridge)]
    f.poly(roof, SHINGLE)
    y = ridge + 4.0
    row = 0
    while y < eave - 1.0:
        u = (y - ridge) / (eave - ridge)
        xa, xb = _lerp(wx0 + 76.0, wx0 - 12.0, u) + 1.0, _lerp(wx1 - 76.0, wx1 + 12.0, u) - 1.0
        f.ink([(xa, y), (xb, y)], 0.6, SHINGLE_SHADE)
        x = xa + (3.0 if row % 2 else 0.0)
        while x < xb - 2.0:
            f.ink([(x, y - 5.0), (x, y)], 0.5, SHINGLE_SHADE)
            x += rng.uniform(5.0, 8.0)
        y += 5.6
        row += 1
    f.poly([(wx1 - 76.0, ridge), (wx1 + 12.0, eave), (wx1 - 20.0, eave), (wx1 - 90.0, ridge + 6.0)], K.alpha(SHINGLE_SHADE, 0.55), body=False)
    f.ink([(wx0 + 76.0, ridge + 1.0), (wx1 - 76.0, ridge + 1.0)], 1.4, SHINGLE_LIGHT)
    f.ink([(wx0 + 76.0, ridge + 1.0), (wx0 - 10.0, eave - 1.0)], 1.0, SHINGLE_LIGHT)
    f.ink([(wx1 - 76.0, ridge + 1.0), (wx1 + 10.0, eave - 1.0)], 1.0, SHINGLE_SHADE)
    f.poly(_rect(wx0 - 12.0, eave - 2.0, wx1 + 12.0, eave + 1.0), WHITE)
    # The wall under the verandah is in shade.
    f.poly(_rect(wx0, vfront, wx1, deck), WHITE_SHADE, body=False)
    for y in range(int(vfront) + 3, int(deck), 5):
        f.ink([(wx0 + 1.0, float(y)), (wx1 - 1.0, float(y))], 0.5, WHITE_DARK)
    # The door with its fanlight, and a sash window each side.
    d0, d1 = 148.0, 172.0
    f.poly(_rect(d0 - 3.0, 130.0, d1 + 3.0, deck), WHITE)
    f.poly(_rect(d0, 134.0, d1, 141.0), GLASS, body=False)
    for k in range(1, 4):
        x = _lerp(d0, d1, k / 4.0)
        f.ink([(x, 134.0), (x, 141.0)], 0.7, WHITE)
    f.poly(_rect(d0, 143.0, d1, deck), DOOR, body=False)
    for px0, px1 in ((d0 + 2.0, (d0 + d1) / 2.0 - 1.0), ((d0 + d1) / 2.0 + 1.0, d1 - 2.0)):
        for py0, py1 in ((146.0, 160.0), (163.0, 178.0), (181.0, deck - 3.0)):
            f.ink(_rect(px0, py0, px1, py1) + [(px0, py0)], 0.6, DOOR_SHADE)
    f.dot(d1 - 4.0, 172.0, 1.0, (210, 180, 100, 255))
    _sash(f, 74.0, 140.0, 114.0, 182.0)
    _sash(f, 206.0, 140.0, 246.0, 182.0)
    # The verandah: a low roof from the wall out over thin posts.
    f.poly([(wx0 - 8.0, vfront), (wx0 - 2.0, vtop), (wx1 + 2.0, vtop), (wx1 + 8.0, vfront)], SHINGLE_LIGHT)
    for k in range(3):
        y = vtop + 4.0 + k * 5.0
        f.ink([(wx0 - 4.0 - k * 1.6, y), (wx1 + 4.0 + k * 1.6, y)], 0.6, SHINGLE_SHADE)
    f.poly(_rect(wx0 - 8.0, vfront, wx1 + 8.0, vfront + 4.0), WHITE)
    f.ink([(wx0 - 7.0, vfront + 3.4), (wx1 + 7.0, vfront + 3.4)], 0.6, WHITE_DARK)
    for x in (wx0 - 4.0, 131.0, 189.0, wx1 + 4.0):
        f.poly(_rect(x - 1.8, vfront + 4.0, x + 1.8, deck), WHITE)
        f.ink([(x + 1.0, vfront + 5.0), (x + 1.0, deck - 1.0)], 0.5, WHITE_DARK)
    # The floor of the verandah and the step to the lawn.
    f.poly(_rect(wx0 - 10.0, deck, wx1 + 10.0, deck + 7.0), DECKING)
    f.ink([(wx0 - 9.0, deck + 1.2), (wx1 + 9.0, deck + 1.2)], 0.7, WHITE_SHADE)
    f.poly(_rect(wx0 - 10.0, deck + 4.0, wx1 + 10.0, deck + 7.0), DECKING_SHADE, body=False)
    f.poly(_rect(138.0, deck + 7.0, 182.0, ground), STEP_STONE)
    f.ink([(139.0, deck + 8.4), (181.0, deck + 8.4)], 0.7, WHITE_SHADE)
    f.poly(_rect(138.0, ground - 3.0, 182.0, ground), STEP_STONE_SHADE, body=False)
    for x in range(int(wx0) - 6, int(wx1) + 8, 10):
        if not 136 < x < 184:
            f.ink([(float(x), deck + 7.0), (float(x), ground - 2.0)], 0.6, DECKING_SHADE)
    f.poly(_rect(wx0 - 8.0, deck + 7.0, 138.0, ground - 2.0), K.alpha(DECKING_SHADE, 0.5), body=False)
    f.poly(_rect(182.0, deck + 7.0, wx1 + 8.0, ground - 2.0), K.alpha(DECKING_SHADE, 0.5), body=False)
    return A.finish(f, width=1.4)


# ---------------------------------------------------------------------------
# The table with the two texts of the Treaty.
# ---------------------------------------------------------------------------


def _sheet(f: K.Frame, tl: Point, tr: Point, br: Point, bl: Point, fill: RGBA, shade: RGBA, rows: Sequence[Tuple[float, float, float]], rng: random.Random) -> None:
    """A big sheet that lies flat on the table, and its lines of writing.
    `rows` gives each line as (t, s0, s1) in the sheet."""
    f.poly([tl, tr, br, bl], fill)
    f.poly([_quad(tl, tr, br, bl, 0.0, 0.88), _quad(tl, tr, br, bl, 1.0, 0.88), br, bl], shade, body=False)
    for t, s0, s1 in rows:
        a, b = _quad(tl, tr, br, bl, s0, t), _quad(tl, tr, br, bl, s1, t)
        _writing_line(f, a[0], b[0], (a[1] + b[1]) / 2.0, rng, WRITING, 0.7)


def _draw_treaty_table(anim: str, i: int, n: int):
    w, h = TREATY_TABLE_FRAME
    f = K.Frame(TREATY_TABLE_FRAME)
    rng = random.Random("history_treaty_table")
    ground = 106.0
    far, near = 40.0, 76.0
    # The legs: the far pair is shorter and darker.
    for x in (30.0, 130.0):
        f.limb([(x, near + 4.0), (x, ground - 8.0)], 4.0, TABLE_SHADE)
    for x in (18.0, 142.0):
        f.limb([(x, near + 4.0), (x, ground - 2.0)], 5.0, TABLE)
        f.ink([(x - 1.2, near + 6.0), (x - 1.2, ground - 4.0)], 0.8, TABLE_LIGHT)
    # The top: seen a little from above, with its front edge.
    top = [(20.0, far), (140.0, far), (150.0, near), (10.0, near)]
    f.poly(_rect(10.0, near, 150.0, near + 6.0), TABLE_SHADE)
    f.ink([(11.0, near + 1.2), (149.0, near + 1.2)], 0.7, TABLE)
    f.poly(top, TABLE)
    for k in range(1, 4):
        t = k / 4.0
        f.ink([_quad(*top, 0.0, t), _quad(*top, 1.0, t)], 0.4, TABLE_SHADE)
    f.ink([(22.0, far + 1.0), (138.0, far + 1.0)], 0.8, TABLE_LIGHT)
    # The two texts side by side. The English sheet is on the left; the
    # Maori sheet on the right carries a column of marks at its foot.
    english = [(24.0, far + 3.0), (76.0, far + 4.0), (78.0, near - 2.0), (18.0, near - 3.0)]
    rows_en = [(0.1, 0.32, 0.68)] + [(0.2 + k * 0.075, 0.1, 0.9) for k in range(4)] + [(0.53 + k * 0.075, 0.1, 0.9 if k < 3 else 0.5) for k in range(4)]
    _sheet(f, *english, PAPER, PAPER_SHADE, rows_en, rng)
    maori = [(84.0, far + 4.0), (136.0, far + 2.0), (144.0, near - 3.0), (84.0, near - 1.0)]
    rows_mi = [(0.1, 0.3, 0.7)] + [(0.2 + k * 0.075, 0.1, 0.9 if k < 4 else 0.6) for k in range(5)]
    _sheet(f, *maori, VELLUM, VELLUM_SHADE, rows_mi, rng)
    # The signature marks: two short columns of small, different marks.
    for s in (0.2, 0.58):
        for k in range(4):
            p = _quad(*maori, s + rng.uniform(-0.03, 0.03), 0.6 + k * 0.09)
            x, y = p
            kind = rng.randint(0, 2)
            if kind == 0:
                f.ink([(x, y), (x + 3.0, y - 1.4), (x + 5.0, y + 0.4), (x + 8.0, y - 1.0)], 0.5, WRITING)
            elif kind == 1:
                f.ink(_ring(x + 2.0, y - 0.4, 1.8, 1.0, 0.0, 330.0, 8) + [(x + 7.0, y)], 0.5, WRITING)
            else:
                f.ink([(x, y + 0.4), (x + 2.0, y - 1.4), (x + 2.6, y + 0.6), (x + 4.6, y - 1.2), (x + 9.0, y - 0.4)], 0.5, WRITING)
            f.ink([(x + 11.0, y), (x + 18.0, y)], 0.4, K.alpha(WRITING, 0.7))
    # The inkwell and the quill, at the back of the table.
    ix, iy = 132.0, far + 8.0
    f.poly([(ix - 5.0, iy), (ix - 5.0, iy - 5.0), (ix - 2.6, iy - 8.0), (ix + 2.6, iy - 8.0), (ix + 5.0, iy - 5.0), (ix + 5.0, iy)], INKPOT)
    f.poly(_rect(ix - 2.6, iy - 10.0, ix + 2.6, iy - 8.0), INKPOT)
    f.ink([(ix - 3.4, iy - 6.0), (ix - 3.4, iy - 2.0)], 0.8, INKPOT_LIGHT)
    qb, qt = (ix + 1.0, iy - 9.0), (ix + 12.0, iy - 40.0)
    vane = []
    for k in range(9):
        u = 0.3 + 0.7 * k / 8.0
        p = _mix(qb, qt, u)
        vane.append((p[0] + 3.0 * math.sin(math.pi * (u - 0.3) / 0.7) ** 0.6, p[1] + 1.0))
    back = [(_mix(qb, qt, u)[0] - 1.4 * math.sin(math.pi * (u - 0.3) / 0.7) ** 0.6, _mix(qb, qt, u)[1]) for u in (1.0, 0.85, 0.7, 0.55, 0.4, 0.3)]
    f.poly(vane + back, QUILL)
    for k in range(4):
        p = _mix(qb, qt, 0.4 + k * 0.14)
        f.ink([p, (p[0] + 2.6, p[1] + 2.0)], 0.5, QUILL_SHADE)
    f.ink([_mix(qb, qt, 0.3), qt], 0.7, QUILL_SHADE)
    f.limb([(ix + 0.6, iy - 8.0), _mix(qb, qt, 0.34)], 1.2, QUILL_SHADE)
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# The flagstaff on Maiki Hill.
# ---------------------------------------------------------------------------


def _draw_flagstaff(anim: str, i: int, n: int):
    w, h = FLAGSTAFF_FRAME
    f = K.Frame(FLAGSTAFF_FRAME)
    rng = random.Random("history_flagstaff")
    ground = 436.0
    mx = 48.0
    cap, truck = 120.0, 20.0
    # The stays: from the head of the lower mast to stakes in the ground.
    for x in (10.0, 130.0):
        f.ink([(mx, cap + 6.0), (x, ground - 2.0)], 0.9, RIGGING)
        f.limb([(x, ground - 6.0), (x, ground + 1.0)], 2.4, TIMBER)
    for x in (22.0, 100.0):
        f.ink([(mx, truck + 30.0), (x, cap + 4.0)], 0.6, RIGGING)
    # The mound of earth round the foot of the mast.
    f.poly([(14.0, ground + 2.0), (30.0, ground - 10.0), (66.0, ground - 12.0), (86.0, ground + 2.0)], EARTH)
    f.poly([(50.0, ground - 11.0), (66.0, ground - 12.0), (86.0, ground + 2.0), (56.0, ground + 2.0)], EARTH_SHADE, body=False)
    for x, y in ((28.0, ground - 2.0), (70.0, ground - 3.0), (44.0, ground)):
        f.ellipse(x, y, 4.0, 2.6, STONE_LIGHT)
    _tuft(f, 22.0, ground + 1.0, rng, 0.8)
    _tuft(f, 80.0, ground + 1.0, rng, 0.8)
    # The lower mast, tapered, and the topmast above it, held by a cap.
    f.poly([(mx - 4.0, ground - 6.0), (mx + 4.0, ground - 6.0), (mx + 2.8, cap), (mx - 2.8, cap)], MAST)
    f.ink([(mx - 2.0, ground - 8.0), (mx - 1.4, cap + 2.0)], 1.0, MAST_LIGHT)
    f.ink([(mx + 2.6, ground - 8.0), (mx + 1.8, cap + 2.0)], 0.8, MAST_SHADE)
    f.poly([(mx - 1.8, cap + 18.0), (mx + 1.8, cap + 18.0), (mx + 1.2, truck), (mx - 1.2, truck)], MAST)
    f.ink([(mx - 0.6, cap + 16.0), (mx - 0.4, truck + 2.0)], 0.6, MAST_LIGHT)
    f.poly(_rect(mx - 5.0, cap - 2.0, mx + 5.0, cap + 3.0), MAST_SHADE)
    f.poly(_rect(mx - 4.0, cap + 14.0, mx + 4.0, cap + 18.0), MAST_SHADE)
    f.ellipse(mx, truck - 1.0, 3.0, 2.2, MAST_SHADE)
    # The small cross-yard below the cap.
    f.limb([(mx - 24.0, cap + 30.0), (mx + 24.0, cap + 30.0)], 2.4, MAST)
    f.ink([(mx - 22.0, cap + 29.4), (mx + 22.0, cap + 29.4)], 0.6, MAST_LIGHT)
    f.ink([(mx - 24.0, cap + 30.0), (mx, cap - 2.0), (mx + 24.0, cap + 30.0)], 0.5, RIGGING)
    # The halyard, from the truck down to a cleat low on the mast.
    f.ink([(mx + 2.0, truck + 2.0), (mx + 2.4, ground - 30.0)], 0.5, RIGGING)
    f.limb([(mx + 2.0, ground - 32.0), (mx + 6.0, ground - 32.0)], 1.6, MAST_SHADE)
    # The Union Flag of 1801 at the head, flying to the right.
    fx, fy, s = mx + 3.0, truck + 4.0, 1.5

    def place(u: float, v: float) -> Point:
        a = u / FLAG_W
        wave = 3.0 * a * math.sin(2.0 * math.pi * (a * 1.2 - 0.15))
        return (fx + u * s * (1.0 - 0.03 * math.sin(math.pi * a)), fy + v * s + wave + 2.0 * a)

    _draw_flag(f, _union_pieces(0.0, 0.0, FLAG_W, FLAG_H, True), place)
    for u in (16.0, 36.0):
        f.ink([place(u, 0.4), place(u + 4.0, FLAG_H - 0.4)], 0.8, K.alpha((20, 20, 40, 255), 0.25))
    f.ink([place(0.0, 0.0), place(0.0, FLAG_H)], 1.0, CANVAS)
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# A ship of the First Fleet at anchor.
# ---------------------------------------------------------------------------


def _furled(f: K.Frame, x0: float, x1: float, y: float, depth: float, rng: random.Random) -> None:
    """A sail furled on its yard: a lumpy roll of canvas on top of the
    spar, fuller in the middle, with gaskets of rope round it."""
    top: List[Point] = []
    for k in range(17):
        u = k / 16.0
        bulge = depth * (0.6 + 0.4 * math.sin(math.pi * u))
        top.append((_lerp(x0, x1, u), y - bulge + (rng.uniform(-0.6, 0.6) if 0 < k < 16 else 0.0)))
    f.poly(top + [(x1, y + 1.0), (x0, y + 1.0)], CANVAS)
    f.poly([(p[0], _lerp(p[1], y, 0.5)) for p in top] + [(x1, y + 1.0), (x0, y + 1.0)], CANVAS_SHADE, body=False)
    f.ink([(p[0], p[1] + 1.0) for p in top[2:-2]], 0.7, CANVAS_LIGHT)
    for k in range(1, 6):
        x = _lerp(x0, x1, k / 6.0)
        f.ink([(x - 0.6, y - depth), (x + 0.6, y + 1.0)], 0.9, RIGGING)


def _yard(f: K.Frame, cx: float, y: float, half: float, rng: random.Random) -> None:
    """A yard across the mast at `y`, with its sail furled on it."""
    _furled(f, cx - half + 4.0, cx + half - 4.0, y - 1.0, max(4.0, half * 0.1), rng)
    f.limb([(cx - half, y), (cx + half, y)], 2.6, SPAR)
    f.ink([(cx - half + 2.0, y - 0.6), (cx + half - 2.0, y - 0.6)], 0.6, SPAR_LIGHT)


def _shrouds(f: K.Frame, x0: float, x1: float, y0: float, top: Point, count: int) -> None:
    """The shrouds of a mast: lines from the channel on the hull up to the
    top, and the ratlines across them."""
    feet = [(_lerp(x0, x1, k / float(count - 1)), y0) for k in range(count)]
    for p in feet:
        f.ink([p, top], 0.6, RIGGING)
    for k in range(1, 9):
        u = k / 9.0
        a = _mix(feet[0], top, u)
        b = _mix(feet[-1], top, u)
        f.ink([a, b], 0.35, K.alpha(RIGGING, 0.7))


def _draw_first_fleet_ship(anim: str, i: int, n: int):
    w, h = FIRST_FLEET_SHIP_FRAME
    f = K.Frame(FIRST_FLEET_SHIP_FRAME)
    rng = random.Random("history_first_fleet_ship")
    wl = 440.0
    bow, stern = 96.0, 446.0

    def sheer(x: float) -> float:
        if x < 250.0:
            return 362.0 - 14.0 * ((250.0 - x) / 154.0) ** 2
        return 362.0 - 26.0 * ((x - 250.0) / 196.0) ** 2

    # The masts: (x, deck, top of the lower mast, crosstrees, truck), and
    # the yards on each as (y, half its length).
    masts = [(178.0, 228.0, 136.0, 80.0, [(242.0, 64.0), (158.0, 50.0), (98.0, 34.0)]),
             (290.0, 206.0, 106.0, 34.0, [(222.0, 78.0), (128.0, 60.0), (56.0, 40.0)]),
             (386.0, 252.0, 170.0, 126.0, [(266.0, 48.0), (184.0, 36.0)])]
    # The bowsprit and the stays to it.
    bs0, bs1 = (124.0, sheer(124.0) + 4.0), (26.0, 296.0)
    f.limb([bs0, _mix(bs0, bs1, 0.62)], 7.0, SPAR)
    f.limb([_mix(bs0, bs1, 0.5), bs1], 4.0, SPAR)
    f.ink([_mix(bs0, bs1, 0.05), _mix(bs0, bs1, 0.95)], 0.8, SPAR_LIGHT)
    f.limb([_mix(bs0, bs1, 0.6), (_mix(bs0, bs1, 0.6)[0], _mix(bs0, bs1, 0.6)[1] + 8.0)], 3.0, SPAR_SHADE)
    fore = masts[0]
    f.ink([(fore[0], fore[1] + 4.0), _mix(bs0, bs1, 0.75)], 0.7, RIGGING)
    f.ink([(fore[0], fore[2] + 2.0), bs1], 0.7, RIGGING)
    f.ink([(fore[0], fore[3] + 2.0), (bs1[0] + 4.0, bs1[1] + 1.0)], 0.6, RIGGING)
    f.ink([_mix(bs0, bs1, 0.6), (_mix(bs0, bs1, 0.6)[0] + 6.0, wl - 30.0), (bow + 10.0, sheer(bow + 10.0) + 30.0)], 0.6, RIGGING)
    # The stays between the masts.
    main, mizzen = masts[1], masts[2]
    f.ink([(main[0], main[1] + 4.0), (fore[0] + 6.0, sheer(fore[0]) - 2.0)], 0.7, RIGGING)
    f.ink([(main[0], main[2] + 2.0), (fore[0], fore[1] + 2.0)], 0.6, RIGGING)
    f.ink([(main[0], main[3] + 2.0), (fore[0], fore[2] + 2.0)], 0.5, RIGGING)
    f.ink([(mizzen[0], mizzen[1] + 4.0), (main[0] + 4.0, sheer(main[0]) - 24.0)], 0.6, RIGGING)
    f.ink([(mizzen[0], mizzen[2] + 2.0), (main[0], main[1] + 30.0)], 0.5, RIGGING)
    # The shrouds and the backstays.
    for x, top, cross, truck, yards in masts:
        dy = sheer(x)
        _shrouds(f, x - 30.0, x + 22.0, dy + 6.0, (x, top + 4.0), 5)
        _shrouds(f, x - 12.0, x + 12.0, top, (x, cross + 4.0), 3)
        f.ink([(x, cross + 2.0), (x + 40.0, sheer(x + 40.0) + 6.0)], 0.5, RIGGING)
        del truck, yards
    # The masts, with their tops and crosstrees.
    for x, top, cross, truck, yards in masts:
        dy = sheer(x)
        f.poly([(x - 4.4, dy), (x + 4.4, dy), (x + 3.6, top), (x - 3.6, top)], SPAR)
        f.ink([(x - 2.2, dy - 2.0), (x - 1.8, top + 2.0)], 1.0, SPAR_LIGHT)
        f.poly([(x - 2.4, top + 6.0), (x + 2.4, top + 6.0), (x + 1.8, cross), (x - 1.8, cross)], SPAR)
        f.poly([(x - 1.4, cross + 6.0), (x + 1.4, cross + 6.0), (x + 0.8, truck), (x - 0.8, truck)], SPAR)
        f.ellipse(x, truck - 1.0, 2.2, 1.6, SPAR_SHADE)
        f.poly([(x - 14.0, top), (x + 14.0, top), (x + 12.0, top + 5.0), (x - 12.0, top + 5.0)], SPAR_SHADE)
        f.limb([(x - 10.0, cross + 1.0), (x + 10.0, cross + 1.0)], 1.8, SPAR_SHADE)
        for y, half in yards:
            _yard(f, x, y, half, rng)
    # The spanker: its gaff and boom on the mizzen, the sail furled on the
    # gaff.
    mz = mizzen[0]
    gaff0, gaff1 = (mz + 2.0, 284.0), (450.0, 262.0)
    f.limb([gaff0, gaff1], 2.6, SPAR)
    f.limb([(mz + 2.0, sheer(mz) - 12.0), (482.0, sheer(482.0) - 16.0)], 3.0, SPAR)
    roll = [_mix(gaff0, gaff1, 0.06 + 0.88 * k / 10.0) for k in range(11)]
    f.limb([(x, y + 3.0) for x, y in roll], 6.0, CANVAS)
    f.ink([(x, y + 4.6) for x, y in roll], 1.4, CANVAS_SHADE)
    f.ink([(x, y + 1.4) for x, y in roll[1:-1]], 0.7, CANVAS_LIGHT)
    for k in range(1, 5):
        x, y = _mix(gaff0, gaff1, 0.06 + 0.88 * k / 5.0)
        f.ink([(x - 0.6, y - 0.4), (x + 0.6, y + 6.4)], 0.9, RIGGING)
    f.ink([gaff1, (482.0, sheer(482.0) - 16.0)], 0.5, RIGGING)
    # The ensign staff at the stern, and the red ensign of 1788 that hangs
    # slack on it: a red field with the Union Flag of 1606 in the corner.
    st0, st1 = (stern - 4.0, sheer(stern) - 8.0), (466.0, 286.0)
    f.limb([st0, st1], 2.0, SPAR_SHADE)
    sd = (st0[0] - st1[0], st0[1] - st1[1])
    sl = math.hypot(*sd)
    sd = (sd[0] / sl, sd[1] / sl)
    s = 0.62

    def hang(u: float, v: float) -> Point:
        a = u / FLAG_W
        x = st1[0] + 1.2 + sd[0] * v * s + a * 9.0 + 1.6 * math.sin(a * 3.0 * math.pi)
        y = st1[1] + 1.0 + sd[1] * v * s + u * s * 0.8
        return (x, y)

    ensign = [(_rect(0.0, 0.0, FLAG_W, FLAG_H), FLAG_RED)] + _union_pieces(0.0, 0.0, FLAG_W / 2.0, FLAG_H / 2.0, False)
    _draw_flag(f, ensign, hang)
    for u in (20.0, 40.0):
        f.ink([hang(u, 0.6), hang(u + 2.0, FLAG_H - 0.6)], 0.8, K.alpha((40, 10, 10, 255), 0.3))
    # The hull: black, with a pale band along the shut gunports, a sheer
    # that rises to the bow and the stern, and a raised quarterdeck.
    xs = [bow + (stern - bow) * k / 40.0 for k in range(41)]
    top_line = [(x, sheer(x) - (8.0 if x > 372.0 else 0.0)) for x in xs]
    hull = top_line + [(stern + 6.0, sheer(stern) - 2.0), (stern - 4.0, wl + 4.0), (128.0, wl + 4.0), (104.0, wl - 30.0), (94.0, sheer(bow) + 22.0),
                       (bow - 4.0, sheer(bow) + 4.0)]
    f.poly(hull, HULL)
    f.poly([(bow + 30.0, sheer(bow + 30.0) + 46.0), (stern - 10.0, sheer(stern - 10.0) + 50.0), (stern - 4.0, wl + 4.0), (128.0, wl + 4.0)], HULL_SHADE, body=False)
    band = [(x, sheer(x) + 16.0) for x in xs[3:-2]]
    f.poly(band + [(x, y + 11.0) for x, y in reversed(band)], OCHRE, body=False)
    f.ink([(x, y + 10.4) for x, y in band], 0.6, OCHRE_SHADE)
    for k in range(11):
        x = 150.0 + k * 25.0
        y = sheer(x) + 18.0
        f.poly(_rect(x - 3.8, y, x + 3.8, y + 7.0), HULL_SHADE, body=False)
        f.ink([(x - 3.8, y + 0.6), (x + 3.8, y + 0.6)], 0.4, HULL_LIGHT)
    f.ink([(x, y + 1.0) for x, y in top_line[1:-1]], 1.2, OCHRE)
    f.ink([(x, sheer(x) + 34.0) for x in xs[4:-3]], 1.0, HULL_LIGHT)
    f.ink([(x, sheer(x) + 40.0) for x in xs[4:-3]], 0.8, HULL_LIGHT)
    # The quarter gallery and the stern windows.
    qx0, qx1 = 410.0, stern + 2.0
    qy = sheer(qx0) - 4.0
    f.poly([(qx0, qy), (qx1, qy - 4.0), (qx1 + 2.0, qy + 26.0), (qx0 + 6.0, qy + 30.0)], HULL)
    f.ink([(qx0, qy), (qx1, qy - 4.0)], 1.0, OCHRE)
    for k in range(3):
        x = qx0 + 6.0 + k * 10.0
        f.poly(_rect(x, qy + 6.0 - k * 1.0, x + 6.0, qy + 16.0 - k * 1.0), STERN_GLASS, body=False)
        f.ink([(x + 3.0, qy + 6.0 - k), (x + 3.0, qy + 16.0 - k)], 0.5, HULL)
    f.ink([(qx0 + 4.0, qy + 22.0), (qx1, qy + 20.0)], 0.8, OCHRE)
    # The knee of the head under the bowsprit, the cathead and the stowed
    # anchor at the bow.
    f.poly([(bow - 2.0, sheer(bow) + 6.0), (bow - 18.0, sheer(bow) + 2.0), (bow - 14.0, sheer(bow) + 12.0), (bow - 2.0, sheer(bow) + 24.0)], HULL)
    f.ink([(bow - 16.0, sheer(bow) + 4.0), (bow - 3.0, sheer(bow) + 18.0)], 0.8, OCHRE)
    ax, ay = 124.0, sheer(124.0) + 10.0
    f.limb([(ax, ay), (ax + 2.0, ay + 26.0)], 2.2, HULL_LIGHT)
    f.ink([(ax - 6.0, ay + 20.0), (ax + 2.0, ay + 27.0), (ax + 9.0, ay + 22.0)], 1.6, HULL_LIGHT)
    f.limb([(ax - 5.0, ay + 1.0), (ax + 5.0, ay + 1.0)], 1.8, SPAR)
    # The anchor cable from the hawse hole, down into the water.
    hx, hy = bow + 6.0, sheer(bow) + 16.0
    f.ellipse(hx, hy, 2.2, 2.0, HULL_SHADE)
    f.limb([(hx, hy), (hx - 20.0, hy + 30.0), (hx - 36.0, wl + 2.0)], 2.0, RIGGING)
    # The water: harbour water over the foot of the hull.
    _water(f, 12.0, w - 12.0, wl - 8.0, wl + 36.0, SEA)
    _water(f, 30.0, w - 30.0, wl + 2.0, wl + 32.0, SEA_DEEP)
    _ripples(f, 30.0, w - 30.0, wl + 2.0, 0.0, SEA_LIGHT, 4, 6.0, "history_first_fleet_ship ripples")
    return A.finish(f, width=1.4)


# ---------------------------------------------------------------------------
# The nawi.
# ---------------------------------------------------------------------------


def _draw_nawi(anim: str, i: int, n: int):
    w, h = NAWI_FRAME
    f = K.Frame(NAWI_FRAME)
    rng = random.Random("history_nawi")
    ph = i / float(max(1, n))
    top = NAWI_TOP
    x0, x1 = NAWI_SPAN
    tip_l, tip_r = 22.0, 362.0
    wl = top + 14.0

    def gunwale(x: float) -> float:
        if x < x0:
            return top - 20.0 * ((x0 - x) / (x0 - tip_l)) ** 1.7
        if x > x1:
            return top - 20.0 * ((x - x1) / (tip_r - x1)) ** 1.7
        return top

    def keel(x: float) -> float:
        u = (x - tip_l) / (tip_r - tip_l)
        return gunwale(x) + 26.0 * max(0.0, math.sin(math.pi * u)) ** 0.45

    # The water behind the canoe. It has no outline.
    _water(f, 8.0, w - 8.0, wl - 4.0, wl + 16.0, SEA)
    # The smoke: a thin wisp that rises and fades.
    for k in range(3):
        u = (ph + k / 3.0) % 1.0
        _puff(f, 196.0 + 12.0 * u + 3.0 * math.sin(2.0 * math.pi * (u + k * 0.3)), top - 32.0 - 48.0 * u, 4.0 + 6.0 * u,
              K.alpha(SMOKE, 0.45 * (1.0 - u)), random.Random(f"history_nawi smoke {k}"), 5)
    # The pad of clay in the middle of the canoe: only its top shows over
    # the near side of the hull.
    fx = 196.0
    f.ellipse(fx, top + 1.0, 16.0, 5.0, CLAY_PAD)
    f.ellipse(fx - 4.0, top - 1.8, 8.0, 1.4, (200, 178, 146, 255), body=False)
    # The hull: one sheet of bark, its ends gathered up and tied.
    xs = [tip_l + (tip_r - tip_l) * k / 64.0 for k in range(65)]
    hull = [(x, gunwale(x)) for x in xs] + [(x, keel(x)) for x in reversed(xs)]
    f.poly(hull, BARK)
    f.poly([(x, _lerp(gunwale(x), keel(x), 0.55)) for x in xs] + [(x, keel(x)) for x in reversed(xs)], BARK_SHADE, body=False)
    # The grain of the stringybark runs along the hull.
    for _ in range(40):
        xa = rng.uniform(tip_l + 20.0, tip_r - 40.0)
        frac = rng.uniform(0.2, 0.9)
        xb = min(tip_r - 16.0, xa + rng.uniform(14.0, 36.0))
        pts = [(x, _lerp(gunwale(x), keel(x), frac)) for x in (xa, (xa + xb) / 2.0, xb)]
        f.ink(pts, 0.5, BARK_DARK if rng.random() < 0.6 else BARK_LIGHT)
    # The rim: the edge of the bark, lighter where it is rolled over.
    f.ink([(x, gunwale(x) + 1.2) for x in xs[2:-2]], 1.4, BARK_LIGHT)
    f.ink([(x, gunwale(x) + 3.2) for x in xs[4:-4]], 0.5, BARK_DARK)
    # The gathered ends: pleats that run in to the tied point, and the
    # wraps of cord round them.
    for tip, sign in ((tip_l, 1.0), (tip_r, -1.0)):
        for k in range(4):
            xa = tip + sign * (20.0 + k * 6.0)
            f.ink([(tip + sign * 2.0, gunwale(tip) + 3.0), (xa, _lerp(gunwale(xa), keel(xa), 0.25 + k * 0.17))], 0.6, BARK_DARK)
        for k in range(3):
            xc = tip + sign * (8.0 + k * 3.0)
            f.ink([(xc, gunwale(xc) + 0.4), (xc + sign * 1.0, keel(xc) - 0.6)], 1.2, CORD_DARK)
            f.ink([(xc - sign * 0.4, gunwale(xc) + 0.4), (xc + sign * 0.6, keel(xc) - 1.0)], 0.5, CORD)
    # The cross-sticks: their ends show under the rim, each tied on.
    for x in (110.0, 274.0):
        f.ellipse(x, top + 3.6, 2.6, 2.4, STICK)
        f.dot(x - 0.6, top + 3.0, 0.9, (140, 106, 72, 255))
        f.ink([(x - 3.6, top + 1.0), (x + 3.6, top + 6.4)], 0.8, CORD_DARK)
    # The handle of the short paddle, laid in the canoe near the stern.
    f.limb([(330.0, top + 2.0), (352.0, top - 16.0)], 2.6, STICK)
    f.ink([(332.0, top + 0.6), (350.0, top - 14.4)], 0.5, (140, 106, 72, 255))
    # The hand line, from a short stick tied under the rim down into the
    # water.
    f.limb([(292.0, top + 2.4), (300.0, top + 3.4)], 1.8, STICK)
    f.ink([(300.0, top + 3.4), (304.0, top + 16.0), (308.0, wl + 10.0)], 0.4, K.alpha(CORD, 0.8))
    # The small fire on the pad of clay. Its sticks cross over the pad.
    for a, b in (((fx - 9.0, top - 1.0), (fx + 6.0, top - 6.0)), ((fx + 9.0, top - 1.0), (fx - 5.0, top - 6.0))):
        f.limb([a, b], 2.4, STICK)
    cyc = 2.0 * math.pi * ph
    f.glow(fx, top - 10.0, 14.0, K.alpha(FIRE, 0.14))
    for dx, hgt, off in ((-5.0, 16.0, 0.0), (5.0, 18.0, 1.9), (0.0, 25.0, 3.6)):
        hh = hgt * (0.82 + 0.18 * math.sin(cyc * 2.0 + off))
        _flame(f, fx + dx, top - 3.0, 5.6, hh, 3.0 * math.sin(cyc + off), FIRE_RED)
    for dx, hgt, off in ((-3.0, 11.0, 1.0), (3.0, 13.0, 2.6)):
        hh = hgt * (0.82 + 0.18 * math.sin(cyc * 2.0 + off))
        _flame(f, fx + dx, top - 3.0, 3.6, hh, 2.4 * math.sin(cyc + off), FIRE)
    _flame(f, fx, top - 3.0, 2.4, 8.0 * (0.9 + 0.1 * math.sin(cyc * 3.0)), 1.2 * math.sin(cyc), FIRE_HOT)
    # The water in front covers the foot of the hull. Ripples move.
    _water(f, 12.0, w - 12.0, wl + 1.0, wl + 18.0, SEA_DEEP)
    _ripples(f, 24.0, w - 24.0, wl + 8.0, ph, SEA_LIGHT, 2, 5.0, "history_nawi ripples")
    for k in range(6):
        x = 40.0 + k * 56.0 + 3.0 * math.sin(2.0 * math.pi * (ph + k * 0.37))
        f.ink([(x, wl + 3.0), (x + 12.0, wl + 3.0)], 1.0, SEA_LIGHT)
    return A.finish(f, width=1.4)


# ---------------------------------------------------------------------------
# Publication.
# ---------------------------------------------------------------------------

FRAMES: Dict[str, Tuple[int, int]] = {
    "history_mungo_footprints": MUNGO_FOOTPRINTS_FRAME,
    "history_shell_midden": SHELL_MIDDEN_FRAME,
    "history_rua_pit": RUA_PIT_FRAME,
    "history_pounamu_adze": POUNAMU_ADZE_FRAME,
    "history_haamonga": HAAMONGA_FRAME,
    "history_ngatu_board": NGATU_BOARD_FRAME,
    "history_samoan_fale": SAMOAN_FALE_FRAME,
    "history_kava_bowl": KAVA_BOWL_FRAME,
    "history_treaty_house": TREATY_HOUSE_FRAME,
    "history_treaty_table": TREATY_TABLE_FRAME,
    "history_flagstaff": FLAGSTAFF_FRAME,
    "history_first_fleet_ship": FIRST_FLEET_SHIP_FRAME,
    "history_nawi": NAWI_FRAME,
}
DRAW: Dict[str, Callable] = {
    "history_mungo_footprints": _draw_mungo_footprints,
    "history_shell_midden": _draw_shell_midden,
    "history_rua_pit": _draw_rua_pit,
    "history_pounamu_adze": _draw_pounamu_adze,
    "history_haamonga": _draw_haamonga,
    "history_ngatu_board": _draw_ngatu_board,
    "history_samoan_fale": _draw_samoan_fale,
    "history_kava_bowl": _draw_kava_bowl,
    "history_treaty_house": _draw_treaty_house,
    "history_treaty_table": _draw_treaty_table,
    "history_flagstaff": _draw_flagstaff,
    "history_first_fleet_ship": _draw_first_fleet_ship,
    "history_nawi": _draw_nawi,
}
DISPLAY = {
    "history_mungo_footprints": "Willandra Footprints",
    "history_shell_midden": "Shell Midden",
    "history_rua_pit": "Kumara Store",
    "history_pounamu_adze": "Pounamu Adze",
    "history_haamonga": "Ha'amonga 'a Maui",
    "history_ngatu_board": "Ngatu",
    "history_samoan_fale": "Samoan Fale",
    "history_kava_bowl": "Kava Bowl",
    "history_treaty_house": "Treaty House",
    "history_treaty_table": "Treaty Table",
    "history_flagstaff": "Flagstaff",
    "history_first_fleet_ship": "First Fleet Ship",
    "history_nawi": "Nawi",
}
#: The room of each prop: its last tag.
ROOMS = {
    "history_mungo_footprints": "lake_mungo",
    "history_shell_midden": "lake_mungo",
    "history_rua_pit": "aotearoa",
    "history_pounamu_adze": "aotearoa",
    "history_haamonga": "tonga_samoa",
    "history_ngatu_board": "tonga_samoa",
    "history_samoan_fale": "tonga_samoa",
    "history_kava_bowl": "tonga_samoa",
    "history_treaty_house": "waitangi",
    "history_treaty_table": "waitangi",
    "history_flagstaff": "waitangi",
    "history_first_fleet_ship": "sydney_cove",
    "history_nawi": "sydney_cove",
}
ROWS: Dict[str, List[Tuple[str, int, int]]] = {
    "history_nawi": LOOP,
}


def _foot(name: str) -> Dict[str, Tuple[float, float]]:
    w, h = FRAMES[name]
    return {"foot": (w / 2.0, float(h))}


#: The anchors of each prop. A platform has a "top" anchor at the middle of
#: the surface that a player stands on; the other props have a "foot".
ANCHORS: Dict[str, Dict[str, Tuple[float, float]]] = {name: _foot(name) for name in DISPLAY}
ANCHORS["history_nawi"] = {"top": ((NAWI_SPAN[0] + NAWI_SPAN[1]) / 2.0, NAWI_TOP)}
TAGS: Dict[str, List[str]] = {name: ["prop", "scenery", "history", ROOMS[name]] for name in DISPLAY}
TAGS["history_nawi"] = ["prop", "platform", "history", ROOMS["history_nawi"]]

TARGETS: Dict[str, dict] = {
    name: _publisher(name, DISPLAY[name], ROWS.get(name, STILL), FRAMES[name], DRAW[name], ANCHORS[name], "Scenery", TAGS[name]) for name in DISPLAY
}
