"""The props of Micronesia (the History dimension): the Marianas, the
Marshall Islands, Nan Madol, Yap, Nauru and Bikini Atoll.

The Chamorro (CHamoru) people sailed to the Marianas from island Southeast
Asia about 1500 BCE. From about 1000 CE they set their houses on two rows of
latte stones: limestone pillars (haligi), each with a hemispherical capstone
(tasa) set flat face up. They sailed the sakman, a big fast flying proa,
and husked rice in stone mortars (lusong).

Marshallese navigators learned the swells of the ocean from stick charts:
frames of palm-rib sticks tied in patterns, with small shells for islands.

At Nan Madol, off Pohnpei, the Saudeleur dynasty (about 1180 to 1628) built
nearly a hundred islets on the reef. Their walls are of black basalt
columns, laid like a log cabin: one course along the wall, the next across
it, ends out, with coral rubble as fill. Sakau (kava) was pounded on flat
basalt stones.

On Yap, rai (stone money) are discs of limestone with a hole in the middle.
They were quarried in Palau and carried 400 km by canoe and raft. They stand
on edge along the stone paths. Men met in a faluw, a house with a tall steep
roof on a stone platform.

From about 1920 to 1968 the phosphate of Nauru was dug out from between
pinnacles of coral limestone, and steel cantilevers carried it out over the
reef to the ships. The land was lost. These props show that plainly.

In March 1946 the people of Bikini Atoll were moved away so that the United
States could test atomic bombs there. These props are sober and still: an
empty house, and a grey warship of the target fleet at anchor far away.
There is no explosion and no damage.

These props are drawn in the cel style of the dimension's cast
(`targets/characters/_history_americas_kit.py`): flat colour, one shade, a
bold warm outline. They show the skill and the dignity of the people who
made them. No script is drawn. There are no people and no sacred things.

- ``history_latte_house``: scenery, a Chamorro latte house: three pairs of
  latte stones (the back row darker), a timber sill on the capstones, and a
  house of posts and woven walls under a tall steep thatched roof. The walls
  stand back from the edge of the floor, so that the floor is a ledge. The
  floor is level (`LATTE_SPAN` = (24, 392), `LATTE_TOP` = 290, in a
  416 x 480 frame).
- ``history_lusong``: scenery, a stone mortar (lusong): a block of
  limestone with a round bowl in its top, a stone pestle that leans in it,
  and a few grains of rice and a husk by it.
- ``history_sakman``: the look of a platform, the Chamorro flying proa: one
  long narrow hull with ends that are the same (the proa shunts), an
  outrigger float on booms on the far side, a platform across the booms, a
  mast and a big triangular lateen sail of pandanus matting on a yard and a
  boom. Its gunwale is the platform (`SAKMAN_SPAN` = (52, 396),
  `SAKMAN_TOP` = 276, in a 448 x 352 frame). The boom of the sail crosses
  the space over the deck at about the height of a player's knees and waist,
  behind the player. Its ``idle`` row moves the water and fills the sail a
  little; the hull and the gunwale stay level and still.
- ``history_stick_chart``: scenery, a Marshallese stick chart: a square
  frame of pale palm-rib sticks tied at their crossings, curved sticks for
  the swells that bend round the islands, and small cowrie shells for the
  islands. It leans on a short post. It is not a copy of a known chart.
- ``history_basalt_wall``: scenery, a stretch of wall of Nan Madol: black
  basalt columns in alternate courses (one course along the wall, the next
  across it, ends out), with coral rubble in the gaps and water at its
  foot. Its right corner lifts a little. Its top is level
  (`BASALT_SPAN` = (24, 376), `BASALT_TOP` = 40, in a 448 x 352 frame).
- ``history_sakau_stone``: scenery, a flat basalt pounding stone with a
  heap of sakau roots (some pounded pale), a stone pounder, and a cup of
  coconut shell beside it.
- ``history_rai_big``: scenery, a large rai: a disc of white-grey limestone
  with a hole in the middle, about 2.6 m across. It stands on edge on flat
  paving stones and leans back on a low platform of fitted stones.
- ``history_rai_small``: scenery, a small rai with a wooden carrying pole
  through its hole. The pole rests on two short forked stakes.
- ``history_faluw``: scenery, a Yapese men's house (faluw): a platform of
  fitted stones, a long house of posts with walls of woven panels, and a
  tall steep thatched roof whose pointed gables rise past the walls at each
  end. The gable boards are plain.
- ``history_phosphate_cantilever``: scenery, a cantilever loader of Nauru:
  a steel lattice tower on a concrete footing on the reef, and a long
  lattice arm that reaches out over the sea, held by stays from the top of
  the tower, with a chute at its outer end. The top of the arm is level
  (`CANTILEVER_SPAN` = (136, 548), `CANTILEVER_TOP` = 122, in a 576 x 352
  frame).
- ``history_pinnacles``: scenery, pinnacles of grey-white coral limestone
  on mined-out Topside, with fluting and pits, and deep bare gaps between
  them where the phosphate was dug out.
- ``history_target_ship``: scenery, a grey battleship of 1946 at anchor,
  far away and quiet: a long hull, two turrets forward and two aft with
  their guns level along the deck, a tripod mast, one funnel and no smoke.
  It has no number, no flag and no damage.
- ``history_empty_house``: scenery, a Marshallese house of 1946 on short
  posts: plank and pandanus walls, a steep thatched roof with a patch of
  corrugated iron, a step, and a rolled mat by the open door. The house is
  dark inside and empty.

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
LOOP: List[Tuple[str, int, int]] = [("idle", 8, 130)]

LATTE_HOUSE_FRAME = (416, 480)
#: The floor of the latte house is level: a player can stand on it from x0
#: to x1 at the height `LATTE_TOP` (frame pixels; the foot of the frame is
#: y 480). The walls stand back from its front edge, and the eaves are high
#: enough for a player to stand under them.
LATTE_SPAN = (24.0, 392.0)
LATTE_TOP = 290.0
LUSONG_FRAME = (128, 80)
SAKMAN_FRAME = (448, 352)
#: The gunwale of the proa is the platform: it is level from x0 to x1 at
#: the height `SAKMAN_TOP` (frame pixels), in every frame. The ends of the
#: hull rise past the span.
SAKMAN_SPAN = (52.0, 396.0)
SAKMAN_TOP = 276.0
STICK_CHART_FRAME = (128, 160)
BASALT_WALL_FRAME = (448, 352)
#: The top course of the wall is level: a player can stand on it from x0 to
#: x1 at the height `BASALT_TOP` (frame pixels). Past x1 the corner of the
#: wall lifts.
BASALT_SPAN = (24.0, 376.0)
BASALT_TOP = 40.0
SAKAU_STONE_FRAME = (144, 72)
RAI_BIG_FRAME = (288, 288)
RAI_SMALL_FRAME = (160, 96)
FALUW_FRAME = (448, 384)
CANTILEVER_FRAME = (576, 352)
#: The top of the arm of the cantilever is level: a player can stand on it
#: from x0 (right of the tower) to x1 (the outer end) at the height
#: `CANTILEVER_TOP` (frame pixels).
CANTILEVER_SPAN = (136.0, 548.0)
CANTILEVER_TOP = 122.0
PINNACLES_FRAME = (288, 272)
TARGET_SHIP_FRAME = (512, 192)
EMPTY_HOUSE_FRAME = (256, 208)

# The Marianas: latte limestone, timber, thatch, the proa and its sail.
LIMESTONE = (214, 206, 184, 255)
LIMESTONE_LIGHT = (234, 228, 210, 255)
LIMESTONE_SHADE = (172, 162, 142, 255)
LIMESTONE_DARK = (130, 122, 106, 255)
LIMESTONE_DEEP = (104, 96, 84, 255)
TIMBER = (128, 90, 58, 255)
TIMBER_LIGHT = (164, 122, 82, 255)
TIMBER_SHADE = (92, 62, 40, 255)
FLOOR = (176, 140, 96, 255)
FLOOR_LIGHT = (206, 172, 124, 255)
WEAVE = (202, 176, 120, 255)
WEAVE_LIGHT = (226, 204, 150, 255)
WEAVE_SHADE = (156, 128, 80, 255)
WEAVE_DARK = (120, 96, 60, 255)
THATCH = (180, 146, 90, 255)
THATCH_LIGHT = (210, 180, 120, 255)
THATCH_SHADE = (138, 106, 62, 255)
THATCH_DARK = (100, 74, 44, 255)
INTERIOR = (40, 30, 26, 255)
EAVE_SHADOW = (70, 52, 36, 150)
RICE = (236, 226, 190, 255)
HUSK = (196, 160, 92, 255)
PROA = (150, 88, 56, 255)
PROA_LIGHT = (188, 124, 84, 255)
PROA_SHADE = (110, 62, 40, 255)
PROA_DARK = (78, 44, 30, 255)
FLOAT = (118, 84, 58, 255)
FLOAT_SHADE = (88, 62, 44, 255)
SPAR = (112, 82, 54, 255)
SPAR_LIGHT = (150, 114, 78, 255)
SAIL = (230, 204, 136, 255)
SAIL_LIGHT = (244, 226, 172, 255)
SAIL_SHADE = (196, 164, 98, 255)
SAIL_SEAM = (160, 128, 72, 255)
CORD = (196, 168, 112, 255)
CORD_DARK = (120, 92, 56, 255)
SEA = (74, 132, 138, 220)
SEA_DEEP = (54, 108, 120, 230)
SEA_FAR = (92, 144, 148, 210)
SEA_LIGHT = (184, 222, 214, 255)

# The Marshalls: palm rib, fibre and cowries.
RIB = (228, 208, 150, 255)
RIB_LIGHT = (244, 230, 188, 255)
RIB_SHADE = (178, 154, 98, 255)
FIBRE = (126, 92, 56, 255)
COWRIE = (248, 244, 232, 255)
COWRIE_SHADE = (208, 198, 176, 255)
COWRIE_SLIT = (120, 96, 70, 255)
POST = (122, 88, 58, 255)
POST_LIGHT = (156, 118, 82, 255)
POST_SHADE = (88, 62, 42, 255)
SAND = (226, 214, 180, 255)
SAND_SHADE = (196, 182, 144, 255)

# Nan Madol: basalt with a blue sheen, lichen, coral rubble and sakau.
BASALT = (70, 72, 80, 255)
BASALT_LIGHT = (108, 114, 128, 255)
BASALT_SHEEN = (138, 150, 172, 255)
BASALT_SHADE = (48, 50, 58, 255)
BASALT_DARK = (32, 32, 38, 255)
LICHEN = (168, 172, 158, 255)
LICHEN_LIGHT = (196, 198, 184, 255)
RUBBLE = (204, 198, 178, 255)
RUBBLE_SHADE = (156, 150, 132, 255)
WATER = (58, 82, 84, 225)
WATER_DEEP = (42, 62, 66, 235)
WATER_LIGHT = (150, 176, 170, 255)
ROOT = (126, 104, 80, 255)
ROOT_LIGHT = (160, 138, 106, 255)
ROOT_SHADE = (90, 72, 54, 255)
POUNDED = (216, 202, 166, 255)
POUNDED_SHADE = (184, 166, 126, 255)
SHELL_CUP = (92, 60, 38, 255)
SHELL_CUP_LIGHT = (138, 96, 62, 255)
SHELL_CUP_INNER = (176, 136, 94, 255)
SAKAU_DRINK = (150, 138, 104, 255)

# Yap: the calcite of the rai, moss, the stones of the paths and platforms.
CALCITE = (224, 222, 212, 255)
CALCITE_LIGHT = (242, 242, 234, 255)
CALCITE_MID = (210, 208, 198, 255)
CALCITE_SHADE = (178, 176, 166, 255)
CALCITE_DARK = (136, 134, 126, 255)
MOSS = (108, 128, 70, 255)
MOSS_LIGHT = (142, 160, 90, 255)
STONE = (120, 114, 104, 255)
STONE_LIGHT = (154, 148, 136, 255)
STONE_SHADE = (88, 84, 76, 255)
STONE_DARK = (62, 58, 54, 255)
GRASS = (98, 140, 66, 255)
GRASS_LIGHT = (136, 174, 88, 255)

# Nauru: riveted steel, concrete, reef rock and the coral pinnacles.
STEEL = (136, 96, 82, 255)
STEEL_LIGHT = (170, 128, 108, 255)
STEEL_SHADE = (98, 68, 60, 255)
STEEL_DARK = (70, 48, 44, 255)
CONCRETE = (190, 186, 174, 255)
CONCRETE_SHADE = (150, 146, 134, 255)
REEF = (150, 140, 120, 255)
REEF_LIGHT = (184, 174, 152, 255)
REEF_SHADE = (110, 102, 88, 255)
FOAM = (236, 240, 234, 255)
PINNACLE = (214, 210, 196, 255)
PINNACLE_LIGHT = (236, 234, 222, 255)
PINNACLE_SHADE = (168, 164, 150, 255)
PINNACLE_DARK = (122, 118, 108, 255)
GAP = (70, 62, 54, 255)
GAP_DARK = (48, 42, 38, 255)
PHOSPHATE = (140, 102, 66, 255)
PHOSPHATE_SHADE = (106, 76, 50, 255)

# Bikini: haze grey, muted sea, and a muted house.
HAZE = (150, 156, 160, 255)
HAZE_LIGHT = (178, 184, 188, 255)
HAZE_SHADE = (118, 124, 130, 255)
HAZE_DARK = (88, 92, 98, 255)
BOOT = (98, 100, 104, 255)
LAGOON = (120, 146, 150, 215)
LAGOON_DEEP = (100, 126, 134, 225)
LAGOON_LIGHT = (196, 210, 210, 255)
PLANK = (150, 136, 116, 255)
PLANK_LIGHT = (176, 164, 142, 255)
PLANK_SHADE = (116, 104, 88, 255)
PANDANUS = (176, 162, 124, 255)
PANDANUS_SHADE = (140, 126, 94, 255)
DULL_THATCH = (164, 146, 110, 255)
DULL_THATCH_LIGHT = (188, 172, 136, 255)
DULL_THATCH_SHADE = (128, 112, 82, 255)
DULL_THATCH_DARK = (96, 84, 62, 255)
IRON = (140, 138, 134, 255)
IRON_LIGHT = (170, 168, 162, 255)
IRON_RUST = (150, 108, 80, 255)
MAT = (196, 180, 140, 255)
MAT_SHADE = (156, 140, 104, 255)
DOORWAY = (34, 32, 32, 255)


# ---------------------------------------------------------------------------
# Small shared shapes.
# ---------------------------------------------------------------------------


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


def _quad(tl: Point, tr: Point, br: Point, bl: Point, s: float, t: float) -> Point:
    """A point in the four-sided shape `tl`, `tr`, `br`, `bl`: `s` goes
    from the left side to the right side, `t` from the top to the bottom."""
    return _mix(_mix(tl, tr, s), _mix(bl, br, s), t)


def _dense(poly: Sequence[Point], step: float) -> List[Point]:
    """The closed polygon with more points on its edges: one each `step`.
    A shape that is bent by a transform needs them."""
    out: List[Point] = []
    for a, b in zip(poly, list(poly[1:]) + [poly[0]]):
        count = max(1, int(math.ceil(math.hypot(b[0] - a[0], b[1] - a[1]) / step)))
        for k in range(count):
            out.append(_mix(a, b, k / float(count)))
    return out


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


def _thatch(f: K.Frame, left: Callable[[float], float], right: Callable[[float], float], top: Callable[[float], float], y0: float, y1: float,
            gap: float, rng: random.Random, light: RGBA, dark: RGBA) -> None:
    """The courses of a thatched roof: rows of short hanging strokes from
    `y0` down to `y1`, between the edges `left(y)` and `right(y)`, and
    under the line `top(x)` of the ridge."""
    y = y0
    row = 0
    while y < y1:
        xa, xb = left(y), right(y)
        x = xa + (2.0 if row % 2 else 0.0)
        run: List[Point] = []
        while x < xb - 1.0:
            if y > top(x) + 3.0:
                ln = rng.uniform(3.0, 5.0)
                f.ink([(x, y), (x + rng.uniform(-0.6, 0.6), y + ln)], 0.6, dark if rng.random() < 0.6 else light)
                run.append((x, y + gap - 0.6))
            elif len(run) > 1:
                f.ink(run, 0.8, dark)
                run = []
            x += rng.uniform(2.0, 3.4)
        if len(run) > 1:
            f.ink(run, 0.8, dark)
        y += gap
        row += 1


def _tuft(f: K.Frame, x: float, y: float, rng: random.Random, size: float = 1.0, fill: RGBA = GRASS, light: RGBA = GRASS_LIGHT) -> None:
    """A tuft of grass: thin blades that fan out from one root."""
    count = rng.randint(5, 8)
    for k in range(count):
        a = math.radians(-90.0 + (k - (count - 1) / 2.0) * 16.0 + rng.uniform(-6.0, 6.0))
        ln = size * rng.uniform(7.0, 12.0)
        tip = (x + math.cos(a) * ln, y + math.sin(a) * ln)
        nx, ny = -math.sin(a) * 1.1 * size, math.cos(a) * 1.1 * size
        f.poly([(x - nx, y - ny), tip, (x + nx, y + ny)], fill if k % 3 else light)


def _weave(f: K.Frame, x0: float, y0: float, x1: float, y1: float, step: float, light: RGBA, dark: RGBA) -> None:
    """A woven panel: a checker of short strokes that go one way, then the
    other, in squares of `step`."""
    y = y0
    row = 0
    while y < y1 - 0.5:
        x = x0
        col = row % 2
        while x < x1 - 0.5:
            xb, yb = min(x1, x + step), min(y1, y + step)
            if col % 2:
                for k in range(1, 3):
                    yy = y + (yb - y) * k / 3.0
                    f.ink([(x + 0.4, yy), (xb - 0.4, yy)], 0.4, dark)
            else:
                for k in range(1, 3):
                    xx = x + (xb - x) * k / 3.0
                    f.ink([(xx, y + 0.4), (xx, yb - 0.4)], 0.4, light)
            x += step
            col += 1
        y += step
        row += 1


# ---------------------------------------------------------------------------
# The latte house.
# ---------------------------------------------------------------------------


def _latte_stone(f: K.Frame, cx: float, ground: float, cap: float, back: bool, rng: random.Random) -> None:
    """One latte stone: a limestone pillar (haligi) that tapers up, and a
    hemispherical capstone (tasa) on it with its flat face up at `cap`.
    The stones of the back row are darker."""
    if back:
        body, light, shade, dark = LIMESTONE_DARK, LIMESTONE_SHADE, LIMESTONE_DEEP, (82, 76, 66, 255)
    else:
        body, light, shade, dark = LIMESTONE, LIMESTONE_LIGHT, LIMESTONE_SHADE, LIMESTONE_DARK
    neck = cap + 30.0
    mid = (neck + ground) / 2.0
    left = [(cx - 19.0, ground + 1.0), (cx - 16.0 + rng.uniform(-1.0, 1.0), mid + 20.0), (cx - 14.0, mid - 20.0), (cx - 12.0, neck)]
    right = [(cx + 12.0, neck), (cx + 14.0, mid - 16.0), (cx + 16.0 + rng.uniform(-1.0, 1.0), mid + 24.0), (cx + 19.0, ground + 1.0)]
    f.poly(left + right, body)
    f.poly([(cx + 3.0, neck), (cx + 12.0, neck), (cx + 14.0, mid - 16.0), (cx + 16.0, mid + 24.0), (cx + 19.0, ground + 1.0), (cx + 6.0, ground + 1.0),
            (cx + 5.0, mid)], shade, body=False)
    f.ink([(cx - 11.0, neck + 4.0), (cx - 13.0, mid), (cx - 16.0, ground - 6.0)], 1.2, light)
    # Pits and dark streaks in the old limestone.
    for _ in range(14):
        y = rng.uniform(neck + 6.0, ground - 6.0)
        u = (y - neck) / (ground - neck)
        half = 12.0 + 7.0 * u
        f.ellipse(cx + rng.uniform(-half + 3.0, half - 3.0), y, rng.uniform(0.8, 1.6), rng.uniform(0.6, 1.2), dark, body=False)
    for _ in range(2):
        x = cx + rng.uniform(-8.0, 6.0)
        ya = rng.uniform(neck + 8.0, mid)
        f.ink([(x, ya), (x + rng.uniform(-1.0, 1.0), ya + rng.uniform(16.0, 30.0))], 0.9, K.alpha(dark, 0.6))
    # The capstone: a half ball, its flat face up.
    dome = _ring(cx, cap, 34.0, 40.0, 0.0, 180.0, 28)
    f.poly(dome, body)
    f.poly(_ring(cx, cap, 34.0, 40.0, 0.0, 110.0, 16) + [(cx + 4.0, cap + 22.0), (cx + 20.0, cap + 4.0)], shade, body=False)
    f.ink(_ring(cx, cap, 30.0, 34.0, 120.0, 165.0, 8), 1.2, light)
    f.ink([(cx - 33.0, cap + 1.6), (cx + 33.0, cap + 1.6)], 1.0, light)
    for _ in range(8):
        a = math.radians(rng.uniform(20.0, 160.0))
        d = rng.uniform(0.3, 0.85)
        f.ellipse(cx + math.cos(a) * 34.0 * d, cap + math.sin(a) * 40.0 * d, rng.uniform(0.8, 1.6), rng.uniform(0.6, 1.2), dark, body=False)


def _draw_latte_house(anim: str, i: int, n: int):
    w, h = LATTE_HOUSE_FRAME
    f = K.Frame(LATTE_HOUSE_FRAME)
    rng = random.Random("history_latte_house")
    top = LATTE_TOP
    x0, x1 = LATTE_SPAN
    ground = 472.0
    cap = top + 22.0
    back_floor = top - 10.0
    eave = 144.0
    ridge = 16.0
    # The back row of latte stones: behind the front row, a little higher,
    # and in shade.
    for cx in (96.0, 224.0, 352.0):
        _latte_stone(f, cx, ground - 12.0, cap - 8.0, True, rng)
    # The front row.
    for cx in (70.0, 198.0, 326.0):
        _latte_stone(f, cx, ground, cap, False, rng)
    # The walls of the house: posts and woven panels, set back from the
    # front edge of the floor and in the shade of the eaves.
    wx0, wx1 = 50.0, 366.0
    f.poly(_rect(wx0, eave, wx1, back_floor), WEAVE_SHADE)
    posts = (wx0, 112.0, 176.0, 240.0, 304.0, wx1)
    for xa, xb in zip(posts[:-1], posts[1:]):
        _weave(f, xa + 3.0, eave + 4.0, xb - 3.0, back_floor - 2.0, 6.0, WEAVE, WEAVE_DARK)
    # The open doorway: dark inside.
    dx0, dx1 = 184.0, 232.0
    f.poly(_rect(dx0, eave + 22.0, dx1, back_floor), INTERIOR)
    f.ink([(dx0, eave + 22.0), (dx1, eave + 22.0)], 2.0, TIMBER_SHADE)
    for x in posts:
        f.limb([(x, eave), (x, back_floor)], 5.0, TIMBER)
        f.ink([(x - 1.2, eave + 2.0), (x - 1.2, back_floor - 1.0)], 0.8, TIMBER_LIGHT)
    f.ink([(wx0, back_floor - 3.0), (wx1, back_floor - 3.0)], 2.4, TIMBER_SHADE)
    # The shadow of the eaves on the top of the walls.
    f.poly(_rect(wx0 - 2.0, eave, wx1 + 2.0, eave + 16.0), EAVE_SHADOW, body=False)
    # The floor: a strip of boards seen a little from above, its front edge
    # level at the walk line, then the edge of the boards and the sill.
    f.poly(_rect(x0 - 4.0, back_floor, x1 + 4.0, top), FLOOR_LIGHT)
    for k in range(1, 3):
        y = back_floor + k * 10.0 / 3.0
        f.ink([(x0 - 2.0, y), (x1 + 2.0, y)], 0.5, FLOOR)
    f.poly(_rect(x0 - 4.0, top, x1 + 4.0, top + 8.0), FLOOR)
    for x in range(int(x0) + 6, int(x1), 22):
        f.ink([(float(x), top + 0.6), (float(x), top + 7.4)], 0.6, TIMBER_SHADE)
    f.poly(_rect(x0 + 2.0, top + 8.0, x1 - 2.0, cap), TIMBER)
    f.poly(_rect(x0 + 2.0, top + 15.0, x1 - 2.0, cap), TIMBER_SHADE, body=False)
    f.ink([(x0 + 4.0, top + 10.0), (x1 - 4.0, top + 10.0)], 0.8, TIMBER_LIGHT)
    for x in (x0 + 2.0, x1 - 2.0):
        f.ellipse(x, top + 15.0, 2.6, 6.0, TIMBER_LIGHT, body=False)
        f.ink(_ring(x, top + 15.0, 1.4, 3.4, 0.0, 360.0, 10), 0.4, TIMBER_SHADE)
    f.ink([(x0 - 3.0, top + 0.6), (x1 + 3.0, top + 0.6)], 1.0, (226, 196, 150, 255))
    # The roof: tall and steep, its ridge along the length of the house.
    fringe_y = eave + 3.0

    def lx(y: float) -> float:
        u = (eave - y) / (eave - ridge)
        return _lerp(12.0, 116.0, u) - 6.0 * math.sin(math.pi * u)

    def rx(y: float) -> float:
        return w - lx(y)

    ys = [eave - (eave - ridge) * k / 30.0 for k in range(31)]
    fringe = []
    for k in range(57):
        x = rx(eave) - (rx(eave) - lx(eave)) * k / 56.0
        fringe.append((x, fringe_y + (2.6 if k % 2 else 0.0)))
    roof = [(lx(y), y) for y in ys] + [(rx(y), y) for y in reversed(ys)] + fringe
    f.poly(roof, THATCH)
    _thatch(f, lambda y: lx(y) + 2.0, lambda y: rx(y) - 2.0, lambda x: ridge, ridge + 6.0, eave - 4.0, 7.0, rng, THATCH_LIGHT, THATCH_SHADE)
    f.poly([(_lerp(lx(y), rx(y), 0.62), y) for y in ys] + [(rx(y), y) for y in reversed(ys)], K.alpha(THATCH_SHADE, 0.5), body=False)
    f.poly([(lx(y) + 4.0, y) for y in ys[3:26]] + [(lx(y) + 24.0, y) for y in reversed(ys[3:26])], K.alpha(THATCH_LIGHT, 0.5), body=False)
    for k in range(80):
        x = lx(eave) + 3.0 + k * (rx(eave) - lx(eave) - 6.0) / 79.0
        f.ink([(x, eave - 4.0), (x + rng.uniform(-0.6, 0.6), eave + rng.uniform(1.0, 3.6))], 0.7, THATCH_SHADE)
    # The ridge: a thick roll of thatch, tied down along its length.
    f.poly([(lx(ridge) - 2.0, ridge + 1.0), (rx(ridge) + 2.0, ridge + 1.0), (rx(ridge) + 4.0, ridge + 8.0), (lx(ridge) - 4.0, ridge + 8.0)], THATCH_DARK)
    f.ink([(lx(ridge), ridge + 2.0), (rx(ridge), ridge + 2.0)], 0.8, THATCH)
    for k in range(13):
        x = lx(ridge) + 6.0 + k * (rx(ridge) - lx(ridge) - 12.0) / 12.0
        f.ink([(x, ridge + 1.0), (x, ridge + 8.0)], 1.2, THATCH_SHADE)
    del h
    return A.finish(f, width=1.6)


# ---------------------------------------------------------------------------
# The lusong.
# ---------------------------------------------------------------------------


def _draw_lusong(anim: str, i: int, n: int):
    f = K.Frame(LUSONG_FRAME)
    rng = random.Random("history_lusong")
    ground = 74.0
    cx, ty = 58.0, 42.0
    # The block of limestone: a squat round block, its top seen a little
    # from above.
    body = _ring(cx, ty, 40.0, 11.0, 180.0, 360.0, 18) + [(cx + 38.0, ground - 6.0), (cx + 34.0, ground + 1.0), (cx - 34.0, ground + 1.0),
                                                       (cx - 38.0, ground - 6.0)]
    f.poly(body, LIMESTONE)
    f.poly([(cx + 10.0, ty + 6.0), (cx + 40.0, ty), (cx + 38.0, ground - 6.0), (cx + 34.0, ground + 1.0), (cx + 12.0, ground + 1.0)], LIMESTONE_SHADE,
           body=False)
    f.ellipse(cx, ty, 40.0, 11.0, LIMESTONE_LIGHT)
    f.ink(_ring(cx, ty, 40.0, 11.0, 10.0, 170.0, 20), 0.8, LIMESTONE_SHADE)
    for _ in range(16):
        f.ellipse(rng.uniform(cx - 34.0, cx + 34.0), rng.uniform(ty + 12.0, ground - 4.0), rng.uniform(0.7, 1.4), rng.uniform(0.6, 1.0), LIMESTONE_DARK,
                  body=False)
    # The bowl: a round hollow in the top, dark at its far side and lit on
    # its near side.
    f.ellipse(cx, ty, 22.0, 6.4, LIMESTONE_DARK, body=False)
    f.poly(_ring(cx, ty, 22.0, 6.4, 20.0, 160.0, 14) + list(reversed(_ring(cx, ty + 1.6, 18.0, 4.0, 30.0, 150.0, 12))), LIMESTONE_SHADE, body=False)
    f.ellipse(cx + 2.0, ty + 1.0, 9.0, 2.4, (224, 216, 192, 255), body=False)
    for _ in range(9):
        f.ellipse(cx + rng.uniform(-6.0, 10.0), ty + rng.uniform(-0.6, 2.0), 1.0, 0.6, RICE, body=False)
    # The pestle: a long rounded stone that leans in the bowl.
    p0, p1 = (cx + 8.0, ty - 1.0), (cx + 36.0, 8.0)
    f.limb([p0, p1], 9.0, LIMESTONE)
    f.limb([_mix(p0, p1, 0.08), _mix(p0, p1, 0.92)], 3.0, LIMESTONE_SHADE, body=False)
    f.ink([(p0[0] - 3.0, p0[1] - 2.0), (p1[0] - 3.4, p1[1] + 1.0)], 1.2, LIMESTONE_LIGHT)
    f.ellipse(p1[0], p1[1], 4.4, 3.4, LIMESTONE_LIGHT, body=False)
    # Grains of rice and a husk on the ground by the mortar.
    for _ in range(9):
        x = rng.uniform(102.0, 118.0)
        f.ellipse(x, ground - rng.uniform(0.0, 2.0), 1.4, 0.8, RICE)
    f.poly([(14.0, ground - 1.0), (20.0, ground - 3.4), (26.0, ground - 2.0), (21.0, ground + 0.6)], HUSK)
    f.ink([(15.0, ground - 1.2), (25.0, ground - 2.2)], 0.4, K.shade(HUSK, 0.75))
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# The sakman.
# ---------------------------------------------------------------------------


def _draw_sakman(anim: str, i: int, n: int):
    w, h = SAKMAN_FRAME
    f = K.Frame(SAKMAN_FRAME)
    rng = random.Random("history_sakman")
    ph = i / float(max(1, n))
    cyc = 2.0 * math.pi * ph
    top = SAKMAN_TOP
    x0, x1 = SAKMAN_SPAN
    tip_l, tip_r = 14.0, w - 14.0
    wl = top + 26.0

    def gunwale(x: float) -> float:
        if x < x0:
            return top - 26.0 * ((x0 - x) / (x0 - tip_l)) ** 1.8
        if x > x1:
            return top - 26.0 * ((x - x1) / (tip_r - x1)) ** 1.8
        return top

    def keel(x: float) -> float:
        u = (x - tip_l) / (tip_r - tip_l)
        return gunwale(x) + 40.0 * max(0.0, math.sin(math.pi * u)) ** 0.42

    # The far water, round the float.
    _water(f, 96.0, 352.0, top - 30.0, top - 14.0, SEA_FAR)
    # The outrigger on the far side: the float on its booms, and the
    # platform across the booms. It is smaller and darker than the hull.
    fx0, fx1, fy = 128.0, 320.0, top - 26.0
    f.poly([(fx0 - 6.0, fy - 1.0), (fx0 + 10.0, fy - 5.0), (fx1 - 10.0, fy - 5.0), (fx1 + 6.0, fy - 1.0), (fx1 - 8.0, fy + 4.0), (fx0 + 8.0, fy + 4.0)],
           FLOAT)
    f.poly([(fx0 + 6.0, fy + 1.0), (fx1 - 6.0, fy + 1.0), (fx1 - 8.0, fy + 4.0), (fx0 + 8.0, fy + 4.0)], FLOAT_SHADE, body=False)
    for bx in (166.0, 282.0):
        f.limb([(bx, top + 1.0), (bx + 4.0, fy - 6.0)], 3.4, FLOAT)
        f.limb([(bx + 4.0, fy - 6.0), (bx + 4.0, fy + 1.0)], 2.0, FLOAT_SHADE)
        f.ellipse(bx + 4.0, fy - 5.0, 2.4, 2.0, CORD_DARK)
    for k in range(5):
        y = top - 4.0 - k * 3.0
        f.ink([(168.0 + k * 0.8, y), (282.0 + k * 0.8, y)], 1.4, FLOAT_SHADE if k % 2 else FLOAT)
    # The lateen sail of pandanus matting: its tack at the left end of the
    # hull, its head high on the yard, its clew at the end of the boom.
    tack, peak, clew = (34.0, top - 30.0), (356.0, 12.0), (424.0, top - 92.0)
    belly = 14.0 + 4.0 * math.sin(cyc)
    sag = 4.0 + 1.4 * math.sin(cyc + 1.2)
    ex, ey = clew[0] - peak[0], clew[1] - peak[1]
    el = math.hypot(ex, ey)
    nx, ny = ey / el, -ex / el

    def leech(u: float) -> Point:
        p = _mix(peak, clew, u)
        b = belly * math.sin(math.pi * u) * (1.0 + 0.12 * math.sin(cyc * 2.0 + u * 6.0))
        return (p[0] + nx * b, p[1] + ny * b)

    def foot(u: float) -> Point:
        p = _mix(clew, tack, u)
        return (p[0], p[1] + sag * math.sin(math.pi * u))

    sail = [_mix(tack, peak, k / 16.0) for k in range(16)] + [leech(k / 16.0) for k in range(17)] + [foot(k / 16.0) for k in range(1, 16)]
    f.poly(sail, SAIL)
    shade = [leech(0.08 + 0.84 * k / 12.0) for k in range(13)]
    shade += [(p[0] - nx * (18.0 + 6.0 * math.sin(cyc)), p[1] - ny * (18.0 + 6.0 * math.sin(cyc))) for p in reversed(shade)]
    f.poly(shade, K.alpha(SAIL_SHADE, 0.9), body=False)
    f.poly([_mix(tack, peak, 0.1 + 0.6 * k / 8.0) for k in range(9)] + [_mix(_mix(tack, peak, 0.7), clew, 0.12), _mix(_mix(tack, peak, 0.1), clew, 0.1)],
           K.alpha(SAIL_LIGHT, 0.7), body=False)
    # The seams of the strips of matting run from the yard to the boom; a
    # fine weave lies across them.
    for k in range(1, 12):
        u = k / 12.0
        a = _mix(tack, peak, u)
        b = foot(1.0 - u) if u < 1.0 else clew
        b = _mix(a, b, 0.97)
        f.ink([a, _mix(a, b, 0.5), b], 0.9, SAIL_SEAM)
    for _ in range(140):
        u, v = rng.random(), rng.random()
        if u + v > 1.0:
            u, v = 1.0 - u, 1.0 - v
        p = (tack[0] + (peak[0] - tack[0]) * u + (clew[0] - tack[0]) * v, tack[1] + (peak[1] - tack[1]) * u + (clew[1] - tack[1]) * v)
        f.ink([(p[0] - 1.0, p[1] + 1.0), (p[0] + 1.0, p[1] - 1.0)], 0.4, SAIL_SHADE)
    # The yard and the boom.
    f.limb([tack, peak], 3.6, SPAR)
    f.ink([_mix(tack, peak, 0.03), _mix(tack, peak, 0.97)], 0.7, SPAR_LIGHT)
    f.limb([tack, clew], 3.0, SPAR)
    # The mast, the stays to the ends of the hull and the sheet.
    mast_head = _mix(tack, peak, (212.0 - tack[0]) / (peak[0] - tack[0]))
    f.limb([(222.0, top + 2.0), (mast_head[0], mast_head[1] + 2.0)], 4.4, SPAR)
    f.ink([(220.6, top), (mast_head[0] - 1.0, mast_head[1] + 4.0)], 0.8, SPAR_LIGHT)
    f.ellipse(mast_head[0], mast_head[1] + 1.0, 3.0, 3.0, CORD_DARK)
    f.ink([mast_head, (tip_l + 14.0, gunwale(tip_l + 14.0) + 2.0)], 0.6, CORD_DARK)
    f.ink([mast_head, (tip_r - 14.0, gunwale(tip_r - 14.0) + 2.0)], 0.6, CORD_DARK)
    f.ink([clew, (tip_r - 6.0, gunwale(tip_r - 6.0) + 1.0)], 0.7, CORD_DARK)
    # The hull: one long narrow hull with both ends alike.
    xs = [tip_l + (tip_r - tip_l) * k / 80.0 for k in range(81)]
    hull = [(x, gunwale(x)) for x in xs] + [(x, keel(x)) for x in reversed(xs)]
    f.poly(hull, PROA)
    f.poly([(x, _lerp(gunwale(x), keel(x), 0.58)) for x in xs] + [(x, keel(x)) for x in reversed(xs)], PROA_SHADE, body=False)
    # The washstrake, sewn on along the top of the hull.
    f.ink([(x, gunwale(x) + 1.2) for x in xs[2:-2]], 1.4, PROA_LIGHT)
    f.ink([(x, gunwale(x) + 10.0) for x in xs[5:-5]], 0.8, PROA_DARK)
    for k in range(int((x1 - x0) // 24.0) + 3):
        x = x0 - 18.0 + k * 24.0
        f.ink([(x, gunwale(x) + 7.0), (x, gunwale(x) + 13.0)], 1.0, CORD_DARK)
    # The end pieces, alike at both ends, and the grain along the hull.
    for tip, sign in ((tip_l, 1.0), (tip_r, -1.0)):
        f.poly([(tip - sign * 2.0, gunwale(tip) - 2.0), (tip + sign * 6.0, gunwale(tip) - 6.0), (tip + sign * 12.0, gunwale(tip + sign * 12.0) + 2.0),
                (tip + sign * 4.0, gunwale(tip) + 10.0)], PROA_SHADE)
        f.ink([(tip + sign * 16.0, gunwale(tip + sign * 16.0) + 2.0), (tip + sign * 20.0, keel(tip + sign * 20.0) - 2.0)], 0.8, PROA_DARK)
    for _ in range(30):
        xa = rng.uniform(tip_l + 30.0, tip_r - 70.0)
        frac = rng.uniform(0.3, 0.9)
        xb = xa + rng.uniform(16.0, 40.0)
        f.ink([(x, _lerp(gunwale(x), keel(x), frac)) for x in (xa, (xa + xb) / 2.0, xb)], 0.5, PROA_DARK if rng.random() < 0.6 else PROA_LIGHT)
    # The water in front covers the foot of the hull. Ripples move.
    _water(f, 8.0, w - 8.0, wl - 4.0, wl + 40.0, SEA)
    _water(f, 16.0, w - 16.0, wl + 3.0, wl + 38.0, SEA_DEEP)
    _ripples(f, 24.0, w - 24.0, wl + 10.0, ph, SEA_LIGHT, 3, 7.0, "history_sakman ripples")
    for k in range(7):
        x = 30.0 + k * 58.0 + 4.0 * math.sin(cyc + k * 2.3)
        f.ink([(x, wl + 2.0), (x + 14.0, wl + 2.0)], 1.0, SEA_LIGHT)
    del h
    return A.finish(f, width=1.4)


# ---------------------------------------------------------------------------
# The stick chart.
# ---------------------------------------------------------------------------


def _draw_stick_chart(anim: str, i: int, n: int):
    f = K.Frame(STICK_CHART_FRAME)
    rng = random.Random("history_stick_chart")
    ground = 152.0
    # The short post that the chart leans on.
    f.limb([(64.0, ground), (64.0, 26.0)], 7.0, POST)
    f.ink([(62.4, ground - 2.0), (62.4, 28.0)], 1.0, POST_LIGHT)
    f.ellipse(64.0, 26.0, 3.4, 1.6, POST_LIGHT)
    # The chart leans back, so its top is a little narrower.
    tl, tr, br, bl = (20.0, 44.0), (108.0, 44.0), (114.0, ground - 4.0), (14.0, ground - 4.0)

    def q(s: float, t: float) -> Point:
        return _quad(tl, tr, br, bl, s, t)

    def stick(pts: Sequence[Point], width: float = 2.2) -> None:
        f.limb(pts, width, RIB)
        f.ink([(p[0] - 0.5, p[1] - 0.5) for p in pts], 0.5, RIB_LIGHT)

    def tie(s: float, t: float) -> None:
        p = q(s, t)
        f.ink([(p[0] - 2.0, p[1] - 1.6), (p[0] + 2.0, p[1] + 1.6)], 1.1, FIBRE)
        f.ink([(p[0] - 2.0, p[1] + 1.6), (p[0] + 2.0, p[1] - 1.6)], 1.1, FIBRE)

    def cowrie(s: float, t: float) -> None:
        p = q(s, t)
        f.ellipse(p[0], p[1], 3.6, 2.6, COWRIE)
        f.ellipse(p[0] + 0.6, p[1] + 0.8, 2.6, 1.4, COWRIE_SHADE, body=False)
        f.ink([(p[0] - 2.4, p[1] + 0.2), (p[0] + 2.4, p[1] + 0.2)], 0.6, COWRIE_SLIT)
        f.dot(p[0] - 1.2, p[1] - 1.0, 0.6, (255, 255, 255, 255))

    # The frame: four straight sticks that cross past the corners.
    for t in (0.0, 1.0):
        stick([q(-0.05, t), q(1.05, t)], 2.6)
    for s in (0.0, 1.0):
        stick([q(s, -0.05), q(s, 1.05)], 2.6)
    # Straight sticks across the frame: the middle lines and two diagonals.
    stick([q(0.5, 0.0), q(0.5, 1.0)])
    stick([q(0.0, 0.5), q(1.0, 0.5)])
    stick([q(0.0, 0.0), q(1.0, 1.0)], 1.8)
    stick([q(1.0, 0.0), q(0.0, 1.0)], 1.8)
    # Curved sticks: the swells that bend round the islands.
    for c, r, a0, a1 in (((0.3, 0.3), 0.2, 200.0, 340.0), ((0.3, 0.3), 0.2, 20.0, 160.0), ((0.72, 0.68), 0.22, 160.0, 290.0),
                         ((0.72, 0.68), 0.22, 300.0, 400.0), ((0.5, 0.5), 0.46, 120.0, 150.0)):
        pts = [q(c[0] + math.cos(math.radians(a)) * r, c[1] + math.sin(math.radians(a)) * r) for a in [a0 + (a1 - a0) * k / 10.0 for k in range(11)]]
        stick(pts, 1.8)
    for k in range(3):
        u = 0.2 + 0.3 * k
        pts = [q(0.04 + 0.92 * j / 8.0, u + 0.08 * math.sin(math.pi * j / 8.0)) for j in range(9)]
        stick(pts, 1.4)
    # Fibre ties at the crossings.
    for s, t in ((0.0, 0.0), (1.0, 0.0), (0.0, 1.0), (1.0, 1.0), (0.5, 0.0), (0.5, 1.0), (0.0, 0.5), (1.0, 0.5), (0.5, 0.5), (0.25, 0.25),
                 (0.75, 0.75), (0.75, 0.25), (0.25, 0.75)):
        tie(s, t)
    # The cowrie shells: the islands.
    for s, t in ((0.3, 0.3), (0.72, 0.68), (0.5, 0.5), (0.86, 0.18), (0.16, 0.82)):
        cowrie(s, t)
    # A little sand at the foot.
    f.poly([(6.0, ground + 1.0), (20.0, ground - 3.0), (110.0, ground - 3.0), (122.0, ground + 1.0)], SAND)
    for _ in range(14):
        f.dot(rng.uniform(12.0, 116.0), rng.uniform(ground - 2.0, ground), 0.5, SAND_SHADE)
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# The basalt wall of Nan Madol.
# ---------------------------------------------------------------------------


def _draw_basalt_wall(anim: str, i: int, n: int):
    w, h = BASALT_WALL_FRAME
    f = K.Frame(BASALT_WALL_FRAME)
    rng = random.Random("history_basalt_wall")
    top = BASALT_TOP
    x0, x1 = BASALT_SPAN
    ground = 330.0
    wl, wr = 20.0, 420.0

    def lift(x: float) -> float:
        return -18.0 * max(0.0, (x - x1) / (wr - x1)) ** 2

    def bend(pts: Sequence[Point]) -> List[Point]:
        """The points with the lift of the corner: full at the top of the
        wall and none at its foot."""
        out = []
        for x, y in pts:
            out.append((x, y + lift(x) * max(0.0, min(1.0, (ground - y) / (ground - top)))))
        return out

    def poly(pts: Sequence[Point], fill: RGBA, body: bool = True) -> None:
        f.poly(bend(_dense(pts, 6.0)), fill, body)

    def ink(pts: Sequence[Point], width: float, fill: RGBA) -> None:
        f.ink(bend(pts), width, fill)

    def left_edge(y: float) -> float:
        return wl + 4.0 * (ground - y) / (ground - top)

    def right_edge(y: float) -> float:
        return wr - 6.0 * (ground - y) / (ground - top)

    # The body of the wall: the dark of the gaps, and the coral rubble that
    # shows in them.
    poly([(left_edge(top), top), (right_edge(top), top), (right_edge(ground + 8.0), ground + 8.0), (left_edge(ground + 8.0), ground + 8.0)], BASALT_DARK)
    for _ in range(700):
        x, y = rng.uniform(wl + 4.0, wr - 6.0), rng.uniform(top + 4.0, ground)
        p = bend([(x, y)])[0]
        f.ellipse(p[0], p[1], rng.uniform(1.0, 2.6), rng.uniform(0.8, 1.8), RUBBLE if rng.random() < 0.6 else RUBBLE_SHADE, body=False)
    # The courses, from the top down: a course of columns laid along the
    # wall, then a course of columns laid across it, ends out.
    y = top
    along = True
    while y < ground:
        depth = 30.0 if along else 34.0
        ya, yb = y, min(ground + 8.0, y + depth)
        xl, xr = left_edge(yb), right_edge(yb)
        if along:
            x = xl + rng.uniform(-4.0, 6.0)
            while x < xr - 8.0:
                ln = min(xr - x, rng.uniform(70.0, 170.0))
                if xr - (x + ln) < 30.0:
                    ln = xr - x
                a = max(x, xl)
                b = x + ln
                t0 = ya if ya == top else ya + rng.uniform(0.6, 2.0)
                t1 = yb - rng.uniform(0.6, 2.0)
                k0, k1 = rng.uniform(-3.0, 3.0), rng.uniform(-3.0, 3.0)
                faces = [(a + 2.0 + k0, t0), (b - 2.0 + k1, t0), (b + k1, t0 + (t1 - t0) * 0.3), (b - 1.0 + k1, t1), (a + 1.0 + k0, t1),
                         (a + k0, t0 + (t1 - t0) * 0.3)]
                poly(faces, BASALT)
                poly([(a + 2.0 + k0, t0), (b - 2.0 + k1, t0), (b + k1, t0 + (t1 - t0) * 0.3), (a + k0, t0 + (t1 - t0) * 0.3)], BASALT_LIGHT, False)
                poly([(a + k0 + 1.0, t0 + (t1 - t0) * 0.72), (b + k1 - 1.0, t0 + (t1 - t0) * 0.72), (b - 1.0 + k1, t1), (a + 1.0 + k0, t1)], BASALT_SHADE,
                     False)
                ink([(a + 6.0 + k0, t0 + (t1 - t0) * 0.3), (b - 6.0 + k1, t0 + (t1 - t0) * 0.3)], 0.6, BASALT_SHADE)
                ink([(a + 10.0, t0 + 1.4), (a + 10.0 + (b - a) * rng.uniform(0.3, 0.7), t0 + 1.4)], 0.8, BASALT_SHEEN)
                if rng.random() < 0.35:
                    lx = rng.uniform(a + 8.0, b - 24.0)
                    for _ in range(6):
                        poly(_ring(lx + rng.uniform(0.0, 14.0), rng.uniform(t0 + 6.0, t1 - 4.0), rng.uniform(1.4, 3.0), rng.uniform(1.0, 2.0), 0.0, 360.0, 8),
                             LICHEN if rng.random() < 0.7 else LICHEN_LIGHT, False)
                x = b + rng.uniform(3.0, 6.0)
        else:
            x = xl + rng.uniform(0.0, 4.0)
            while x < xr - 10.0:
                cw = rng.uniform(28.0, 40.0)
                if xr - (x + cw) < 14.0:
                    cw = xr - x - 1.0
                cx, cy = x + cw / 2.0, (ya + yb) / 2.0 + rng.uniform(-1.0, 1.0)
                sides = rng.choice((5, 6, 6, 6))
                rot = rng.uniform(0.0, 360.0)
                rxx, ryy = cw / 2.0 - 1.0, (yb - ya) / 2.0 - 1.0
                pts = []
                for k in range(sides):
                    a = math.radians(rot + 360.0 * k / sides + rng.uniform(-8.0, 8.0))
                    pts.append((cx + math.cos(a) * rxx * rng.uniform(0.9, 1.05), cy + math.sin(a) * ryy * rng.uniform(0.9, 1.05)))
                poly(pts, BASALT)
                c = (cx, cy)
                lit = [p for p in pts if p[1] < cy + 2.0 and p[0] < cx + 4.0]
                if len(lit) >= 2:
                    lit.sort(key=lambda p: math.atan2(p[1] - cy, p[0] - cx))
                    poly([c] + lit, BASALT_LIGHT, False)
                dark = [p for p in pts if p[1] > cy - 2.0 and p[0] > cx - 4.0]
                if len(dark) >= 2:
                    dark.sort(key=lambda p: math.atan2(p[1] - cy, p[0] - cx))
                    poly([c] + dark, BASALT_SHADE, False)
                poly([_mix(c, p, 0.5) for p in pts], BASALT, False)
                ink([(cx - rxx * 0.4, cy - ryy * 0.3), (cx - rxx * 0.1, cy - ryy * 0.4)], 0.7, BASALT_SHEEN)
                if rng.random() < 0.25:
                    poly(_ring(cx + rng.uniform(-4.0, 4.0), cy + rng.uniform(-3.0, 3.0), 3.4, 2.2, 0.0, 360.0, 8), LICHEN, False)
                x += cw + rng.uniform(2.0, 5.0)
        y = yb
        along = not along
    # The level top of the wall, lit.
    ink([(left_edge(top) + 2.0, top + 0.8), (right_edge(top) - 2.0, top + 0.8)], 1.2, BASALT_SHEEN)
    # The water at the foot of the wall, and two wet stones in it.
    for sx, sr in ((86.0, 16.0), (300.0, 12.0)):
        f.ellipse(sx, ground + 4.0, sr, sr * 0.6, BASALT)
        f.ellipse(sx - sr * 0.3, ground - sr * 0.2, sr * 0.5, sr * 0.2, BASALT_SHEEN, body=False)
    _water(f, 8.0, w - 8.0, ground - 2.0, ground + 16.0, WATER)
    _water(f, 16.0, w - 16.0, ground + 4.0, ground + 15.0, WATER_DEEP)
    _ripples(f, 24.0, w - 24.0, ground + 4.0, 0.0, WATER_LIGHT, 2, 5.0, "history_basalt_wall ripples")
    del h
    return A.finish(f, width=1.6)


# ---------------------------------------------------------------------------
# The sakau stone.
# ---------------------------------------------------------------------------


def _root(f: K.Frame, pts: Sequence[Point], width: float, rng: random.Random) -> None:
    """A knobbly root of sakau: a thick bent limb with knots on it."""
    f.limb(pts, width, ROOT)
    f.ink([(p[0], p[1] - width * 0.25) for p in pts], width * 0.25, ROOT_LIGHT)
    for k in range(len(pts) - 1):
        p = _mix(pts[k], pts[k + 1], rng.uniform(0.2, 0.8))
        f.ellipse(p[0] + rng.uniform(-1.0, 1.0), p[1] + rng.uniform(-1.0, 1.0), width * 0.62, width * 0.5, ROOT)
        f.dot(p[0], p[1] + width * 0.2, 0.6, ROOT_SHADE)


def _draw_sakau_stone(anim: str, i: int, n: int):
    f = K.Frame(SAKAU_STONE_FRAME)
    rng = random.Random("history_sakau_stone")
    ground = 66.0
    # The stone: a wide low slab of basalt, its flat top seen a little from
    # above.
    tl, tr = (16.0, 38.0), (110.0, 36.0)
    slab = [(10.0, 44.0), tl, (60.0, 33.0), tr, (118.0, 42.0), (120.0, 56.0), (112.0, ground + 1.0), (18.0, ground + 1.0), (8.0, 56.0)]
    f.poly(slab, BASALT)
    f.poly([(10.0, 44.0), tl, (60.0, 33.0), tr, (118.0, 42.0), (112.0, 49.0), (16.0, 50.0)], BASALT_LIGHT, body=False)
    f.poly([(12.0, 58.0), (118.0, 56.0), (112.0, ground + 1.0), (18.0, ground + 1.0)], BASALT_SHADE, body=False)
    f.ink([(20.0, 49.6), (110.0, 48.6)], 0.8, BASALT_SHEEN)
    for _ in range(10):
        f.dot(rng.uniform(16.0, 112.0), rng.uniform(52.0, 62.0), 0.6, BASALT_DARK)
    # The heap of roots: knobbly grey-brown roots, and a pad of pounded
    # root, pale and fibrous.
    f.ellipse(44.0, 42.0, 20.0, 5.0, POUNDED)
    f.ellipse(46.0, 43.4, 16.0, 3.2, POUNDED_SHADE, body=False)
    for _ in range(14):
        x = rng.uniform(28.0, 60.0)
        f.ink([(x, 39.0 + rng.uniform(0.0, 2.0)), (x + rng.uniform(-3.0, 3.0), 44.0 + rng.uniform(0.0, 2.0))], 0.4, POUNDED_SHADE)
    _root(f, [(64.0, 40.0), (76.0, 34.0), (90.0, 36.0)], 5.0, rng)
    _root(f, [(70.0, 42.0), (84.0, 41.0), (100.0, 38.0)], 5.6, rng)
    _root(f, [(76.0, 30.0), (88.0, 26.0), (98.0, 30.0)], 4.4, rng)
    _root(f, [(86.0, 42.0), (96.0, 44.0), (106.0, 41.0)], 4.0, rng)
    for x, y, a in ((92.0, 26.0, -60.0), (102.0, 36.0, -30.0), (66.0, 36.0, -120.0)):
        f.limb([(x, y), (x + math.cos(math.radians(a)) * 7.0, y + math.sin(math.radians(a)) * 7.0)], 1.2, ROOT_SHADE)
    # The pounder: a round cobble of basalt, the size of a fist.
    f.ellipse(30.0, 34.0, 8.0, 6.4, BASALT)
    f.ellipse(28.0, 31.6, 4.0, 2.4, BASALT_LIGHT, body=False)
    f.ellipse(31.0, 37.4, 6.0, 2.2, BASALT_SHADE, body=False)
    # The cup of coconut shell beside the stone, with a little sakau in it.
    cx, cy = 130.0, 54.0
    f.poly(_ring(cx, cy, 9.0, 11.0, 0.0, 180.0, 14), SHELL_CUP)
    f.ellipse(cx, cy, 9.0, 3.0, SHELL_CUP_INNER)
    f.ellipse(cx, cy + 0.6, 7.4, 2.0, SAKAU_DRINK, body=False)
    f.ink(_ring(cx, cy, 9.0, 11.0, 110.0, 160.0, 6), 1.0, SHELL_CUP_LIGHT)
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# The rai.
# ---------------------------------------------------------------------------


def _rai(f: K.Frame, cx: float, cy: float, rx: float, ry: float, th: float, hole: float, rng: random.Random, behind: RGBA) -> None:
    """A disc of stone money (rai) seen nearly face on: its thickness shows
    as a shaded edge on the right, its rim is thick and its middle thin, and
    the hole in its middle shows `behind` through it."""
    for k in range(int(th), 0, -1):
        f.ellipse(cx + k, cy - k * 0.25, rx, ry, CALCITE_SHADE if k < th - 1 else CALCITE_DARK)
    f.ellipse(cx, cy, rx, ry, CALCITE)
    # The thin middle: a shallow dish, in shade at its top left and lit at
    # its bottom right; the thick rim is lit at its top left.
    f.ellipse(cx + rx * 0.02, cy + ry * 0.02, rx * 0.74, ry * 0.74, CALCITE_MID, body=False)
    f.poly(_ring(cx, cy, rx * 0.74, ry * 0.74, 190.0, 260.0, 10) + list(reversed(_ring(cx + rx * 0.05, cy + ry * 0.05, rx * 0.66, ry * 0.66, 190.0, 260.0, 10))),
           CALCITE_SHADE, body=False)
    f.poly(_ring(cx, cy, rx * 0.74, ry * 0.74, 10.0, 80.0, 10) + list(reversed(_ring(cx - rx * 0.05, cy - ry * 0.05, rx * 0.66, ry * 0.66, 10.0, 80.0, 10))),
           CALCITE_LIGHT, body=False)
    f.ink(_ring(cx, cy, rx * 0.94, ry * 0.94, 150.0, 260.0, 16), max(1.0, rx * 0.03), CALCITE_LIGHT)
    f.ink(_ring(cx, cy, rx * 0.97, ry * 0.97, 10.0, 80.0, 10), max(0.8, rx * 0.02), CALCITE_SHADE)
    # The flecks of the crystalline stone, and grey streaks of weather.
    for _ in range(int(rx * 1.6)):
        a = rng.uniform(0.0, math.tau)
        d = math.sqrt(rng.random()) * 0.94
        x, y = cx + math.cos(a) * rx * d, cy + math.sin(a) * ry * d
        if math.hypot((x - cx) / hole, (y - cy) / hole) > 1.3:
            f.dot(x, y, rng.uniform(0.4, 0.8) * max(0.6, rx / 100.0), CALCITE_LIGHT if rng.random() < 0.6 else CALCITE_SHADE)
    for _ in range(max(2, int(rx / 12.0))):
        a = rng.uniform(200.0, 340.0)
        x, y = cx + math.cos(math.radians(a)) * rx * rng.uniform(0.3, 0.85), cy + math.sin(math.radians(a)) * ry * rng.uniform(0.3, 0.85)
        f.ink([(x, y), (x + rng.uniform(-1.0, 1.0), y + rng.uniform(0.2, 0.5) * ry)], max(0.6, rx * 0.012), K.alpha(CALCITE_DARK, 0.45))
    # The hole: its inner wall shows on the left, and the stones behind it
    # show through.
    f.ellipse(cx, cy, hole, hole * 0.98, CALCITE_DARK, body=False)
    f.ellipse(cx + th * 0.5, cy - th * 0.12, hole - th * 0.5, (hole - th * 0.5) * 0.98, behind, body=False)
    f.ink(_ring(cx, cy, hole, hole * 0.98, 20.0, 160.0, 12), max(0.6, rx * 0.012), CALCITE_LIGHT)


def _draw_rai_big(anim: str, i: int, n: int):
    w, h = RAI_BIG_FRAME
    f = K.Frame(RAI_BIG_FRAME)
    rng = random.Random("history_rai_big")
    ground = 280.0
    # The low platform of fitted flat stones behind the disc.
    px0, px1, ptop = 10.0, 278.0, 206.0
    f.poly([(px0 + 4.0, ptop), (px1 - 4.0, ptop), (px1, ptop + 8.0), (px1, ground - 6.0), (px0, ground - 6.0), (px0, ptop + 8.0)], STONE)
    f.poly(_rect(px0 + 2.0, ptop + 1.0, px1 - 2.0, ptop + 8.0), STONE_LIGHT, body=False)
    y = ptop + 9.0
    row = 0
    while y < ground - 8.0:
        hgt = rng.uniform(8.0, 12.0)
        x = px0 + 1.0 + (rng.uniform(4.0, 14.0) if row % 2 else 0.0)
        while x < px1 - 4.0:
            ln = min(px1 - 1.0 - x, rng.uniform(22.0, 44.0))
            f.poly(_rect(x + 0.8, y + 0.6, x + ln - 0.8, min(ground - 6.0, y + hgt) - 0.6), rng.choice((STONE, STONE, STONE_LIGHT, STONE_SHADE)), body=False)
            f.ink([(x + 1.6, y + 1.4), (x + ln - 2.0, y + 1.4)], 0.6, STONE_LIGHT)
            x += ln
        f.ink([(px0 + 1.0, y), (px1 - 1.0, y)], 0.8, STONE_DARK)
        y += hgt
        row += 1
    # The paving at the foot of the disc: flat stones seen a little from
    # above.
    f.poly([(14.0, ground - 10.0), (274.0, ground - 10.0), (280.0, ground + 1.0), (8.0, ground + 1.0)], STONE_LIGHT)
    x = 12.0
    while x < 272.0:
        ln = rng.uniform(26.0, 46.0)
        f.ink([(x, ground - 10.0), (x - 2.0, ground + 1.0)], 0.8, STONE_SHADE)
        x += ln
    f.ink([(14.0, ground - 5.0), (276.0, ground - 5.0)], 0.5, K.alpha(STONE_SHADE, 0.7))
    # The disc: about 2.6 m across, on edge, leaning back on the platform.
    cx, cy, rx, ry = 138.0, 182.0, 100.0, 96.0
    _rai(f, cx, cy, rx, ry, 12.0, 17.0, rng, STONE_SHADE)
    # Moss and lichen low on the disc, where it stays wet.
    for _ in range(9):
        a = math.radians(rng.uniform(50.0, 130.0))
        x, y = cx + math.cos(a) * rx * rng.uniform(0.7, 0.95), cy + math.sin(a) * ry * rng.uniform(0.7, 0.95)
        f.ellipse(x, y, rng.uniform(3.0, 6.0), rng.uniform(1.6, 3.0), MOSS if rng.random() < 0.6 else MOSS_LIGHT, body=False)
    for _ in range(6):
        a = math.radians(rng.uniform(0.0, 360.0))
        x, y = cx + math.cos(a) * rx * rng.uniform(0.4, 0.85), cy + math.sin(a) * ry * rng.uniform(0.4, 0.85)
        for _ in range(5):
            f.ellipse(x + rng.uniform(-4.0, 4.0), y + rng.uniform(-3.0, 3.0), rng.uniform(1.2, 2.4), rng.uniform(1.0, 1.8), (196, 196, 168, 255), body=False)
    # Grass at the ends of the paving.
    for x in (18.0, 30.0, 258.0, 270.0):
        _tuft(f, x, ground - 2.0, rng, 1.4)
    del w, h
    return A.finish(f, width=1.6)


def _draw_rai_small(anim: str, i: int, n: int):
    f = K.Frame(RAI_SMALL_FRAME)
    rng = random.Random("history_rai_small")
    ground = 90.0
    py = 34.0
    # The two short forked stakes.
    for sx in (24.0, 136.0):
        f.limb([(sx, ground + 1.0), (sx, py + 4.0)], 4.4, POST)
        f.limb([(sx, py + 6.0), (sx - 5.0, py - 4.0)], 3.0, POST)
        f.limb([(sx, py + 6.0), (sx + 5.0, py - 4.0)], 3.0, POST)
        f.ink([(sx - 1.0, ground - 2.0), (sx - 1.0, py + 8.0)], 0.8, POST_LIGHT)
    # The pole behind the disc, on the right of the hole.
    f.limb([(80.0, py), (152.0, py - 1.0)], 5.0, POST_SHADE)
    # The disc, about 0.6 m across, turned so that its face is seen from the
    # side and the front. Its edge shows on the right.
    cx, cy, rx, ry, th = 80.0, py + 2.6, 15.0, 23.0, 6.0
    for k in range(int(th), 0, -1):
        f.ellipse(cx + k, cy, rx, ry, CALCITE_SHADE if k < th - 1 else CALCITE_DARK)
    f.ellipse(cx, cy, rx, ry, CALCITE)
    f.ellipse(cx + 0.6, cy + 0.6, rx * 0.7, ry * 0.7, CALCITE_MID, body=False)
    f.ink(_ring(cx, cy, rx * 0.92, ry * 0.92, 150.0, 260.0, 12), 1.0, CALCITE_LIGHT)
    for _ in range(14):
        a = rng.uniform(0.0, math.tau)
        d = rng.uniform(0.45, 0.9)
        f.dot(cx + math.cos(a) * rx * d, cy + math.sin(a) * ry * d, 0.5, CALCITE_SHADE if rng.random() < 0.5 else CALCITE_LIGHT)
    f.ellipse(cx + 0.4, py, 3.6, 5.0, CALCITE_DARK, body=False)
    # The pole in front of the disc, from the hole to the left stake.
    f.limb([(8.0, py + 1.0), (cx + 1.0, py)], 5.0, POST)
    f.ink([(10.0, py - 0.6), (cx, py - 1.2)], 1.0, POST_LIGHT)
    f.ellipse(8.0, py + 1.0, 2.0, 2.6, POST_LIGHT)
    # A stone by the foot of a stake, and grass.
    f.ellipse(112.0, ground - 3.0, 7.0, 4.0, STONE)
    f.ellipse(110.0, ground - 5.0, 3.6, 1.4, STONE_LIGHT, body=False)
    for x in (18.0, 32.0, 128.0, 144.0):
        _tuft(f, x, ground, rng, 0.9)
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# The faluw.
# ---------------------------------------------------------------------------


def _draw_faluw(anim: str, i: int, n: int):
    w, h = FALUW_FRAME
    f = K.Frame(FALUW_FRAME)
    rng = random.Random("history_faluw")
    ground = 376.0
    ptop = 300.0
    eave = 236.0
    cx = w / 2.0
    # The platform of fitted stones, about 1 m high.
    px0, px1 = 14.0, w - 14.0
    f.poly([(px0 + 6.0, ptop), (px1 - 6.0, ptop), (px1, ptop + 8.0), (px1 + 2.0, ground + 1.0), (px0 - 2.0, ground + 1.0), (px0, ptop + 8.0)], STONE)
    f.poly(_rect(px0 + 3.0, ptop + 1.0, px1 - 3.0, ptop + 8.0), STONE_LIGHT, body=False)
    y = ptop + 9.0
    row = 0
    while y < ground - 2.0:
        hgt = rng.uniform(10.0, 15.0)
        x = px0 + (rng.uniform(6.0, 18.0) if row % 2 else 0.0)
        while x < px1 - 2.0:
            ln = min(px1 - x, rng.uniform(26.0, 52.0))
            f.poly(_rect(x + 0.8, y + 0.6, x + ln - 0.8, min(ground, y + hgt) - 0.6), rng.choice((STONE, STONE, STONE_LIGHT, STONE_SHADE)), body=False)
            f.ink([(x + 1.6, y + 1.6), (x + ln - 2.0, y + 1.6)], 0.6, STONE_LIGHT)
            x += ln
        f.ink([(px0, y), (px1, y)], 0.8, STONE_DARK)
        y += hgt
        row += 1
    # A step of flat stones up to the platform.
    f.poly([(196.0, ptop + 34.0), (252.0, ptop + 34.0), (256.0, ground + 1.0), (192.0, ground + 1.0)], STONE_LIGHT)
    f.ink([(194.0, ptop + 55.0), (254.0, ptop + 55.0)], 0.8, STONE_DARK)
    # The house: posts and woven panels under the eaves, and a dark open
    # middle.
    wx0, wx1 = 72.0, w - 72.0
    f.poly(_rect(wx0, eave - 6.0, wx1, ptop), WEAVE_SHADE)
    posts = [wx0 + (wx1 - wx0) * k / 6.0 for k in range(7)]
    for k, (xa, xb) in enumerate(zip(posts[:-1], posts[1:])):
        if k in (2, 3):
            f.poly(_rect(xa + 2.0, eave, xb - 2.0, ptop), INTERIOR)
        else:
            _weave(f, xa + 3.0, eave + 2.0, xb - 3.0, ptop - 2.0, 6.0, WEAVE, WEAVE_DARK)
    for x in posts:
        f.limb([(x, eave - 4.0), (x, ptop)], 5.0, TIMBER)
        f.ink([(x - 1.2, eave), (x - 1.2, ptop - 1.0)], 0.8, TIMBER_LIGHT)
    f.ink([(wx0, ptop - 2.0), (wx1, ptop - 2.0)], 2.4, TIMBER_SHADE)
    f.poly(_rect(wx0 - 2.0, eave, wx1 + 2.0, eave + 14.0), EAVE_SHADOW, body=False)
    # The roof: tall and steep. Its ridge sags a little in the middle, and
    # its gables sweep up and out past the walls to high points.
    peak_l, peak_r = (26.0, 16.0), (w - 26.0, 16.0)
    corner_l, corner_r = (52.0, eave - 4.0), (w - 52.0, eave - 4.0)
    sag = 46.0

    def ridge(x: float) -> float:
        u = (x - peak_l[0]) / (peak_r[0] - peak_l[0])
        return peak_l[1] + sag * math.sin(math.pi * max(0.0, min(1.0, u))) ** 0.7

    def eave_y(x: float) -> float:
        u = (x - corner_l[0]) / (corner_r[0] - corner_l[0])
        return eave + 2.0 - 6.0 * abs(2.0 * u - 1.0) ** 3

    def left(y: float) -> float:
        u = (corner_l[1] - y) / (corner_l[1] - peak_l[1])
        return _lerp(corner_l[0], peak_l[0], u) + 8.0 * math.sin(math.pi * u)

    def right(y: float) -> float:
        return w - left(y)

    ys = [corner_l[1] - (corner_l[1] - peak_l[1]) * k / 30.0 for k in range(31)]
    xs = [peak_l[0] + (peak_r[0] - peak_l[0]) * k / 40.0 for k in range(41)]
    eaves = [(corner_r[0] - (corner_r[0] - corner_l[0]) * k / 50.0, 0.0) for k in range(51)]
    eaves = [(x, eave_y(x) + (2.4 if k % 2 else 0.0)) for k, (x, _) in enumerate(eaves)]
    roof = [(left(y), y) for y in ys] + [(x, ridge(x)) for x in xs[1:-1]] + [(right(y), y) for y in reversed(ys)] + eaves
    f.poly(roof, THATCH)
    _thatch(f, lambda y: left(y) + 2.0, lambda y: right(y) - 2.0, ridge, peak_l[1] + 6.0, eave - 4.0, 7.0, rng, THATCH_LIGHT, THATCH_SHADE)
    f.poly([(cx + 40.0, ridge(cx + 40.0))] + [(x, ridge(x) + 2.0) for x in xs if x > cx + 40.0] + [(right(y), y) for y in reversed(ys)]
           + [(cx + 60.0, eave_y(cx + 60.0))], K.alpha(THATCH_SHADE, 0.45), body=False)
    for k in range(90):
        x = corner_l[0] + 3.0 + k * (corner_r[0] - corner_l[0] - 6.0) / 89.0
        f.ink([(x, eave_y(x) - 4.0), (x + rng.uniform(-0.6, 0.6), eave_y(x) + rng.uniform(1.0, 3.4))], 0.7, THATCH_SHADE)
    # The ridge: a roll of thatch along the sagging line.
    f.limb([(x, ridge(x) + 3.0) for x in xs[2:-2]], 6.0, THATCH_DARK)
    f.ink([(x, ridge(x) + 1.6) for x in xs[3:-3]], 0.8, THATCH)
    # The plain gable boards along the outer edges, crossed at the peaks.
    for sign, peak, corner in ((1.0, peak_l, corner_l), (-1.0, peak_r, corner_r)):
        pts = [(left(y) if sign > 0 else right(y), y) for y in ys]
        f.limb(pts, 4.0, TIMBER)
        f.ink([(p[0] + sign * 1.0, p[1]) for p in pts[1:-1]], 0.8, TIMBER_LIGHT)
        f.limb([(peak[0], peak[1] + 2.0), (peak[0] - sign * 6.0, peak[1] - 8.0)], 3.4, TIMBER)
        f.limb([(peak[0] + sign * 2.0, peak[1] + 4.0), (peak[0] + sign * 14.0, ridge(peak[0] + sign * 14.0) + 2.0)], 3.0, TIMBER_SHADE)
        del corner
    del h
    return A.finish(f, width=1.6)


# ---------------------------------------------------------------------------
# The phosphate cantilever of Nauru.
# ---------------------------------------------------------------------------


def _lattice(f: K.Frame, a0: Point, a1: Point, b0: Point, b1: Point, count: int, width: float, colour: RGBA) -> None:
    """The bracing between two members `a0`-`a1` and `b0`-`b1`: rungs
    and crossed diagonals in `count` bays."""
    for k in range(count + 1):
        u = k / float(count)
        f.limb([_mix(a0, a1, u), _mix(b0, b1, u)], width, colour)
    for k in range(count):
        u0, u1 = k / float(count), (k + 1) / float(count)
        f.limb([_mix(a0, a1, u0), _mix(b0, b1, u1)], width * 0.7, colour)
        f.limb([_mix(b0, b1, u0), _mix(a0, a1, u1)], width * 0.7, colour)


def _draw_phosphate_cantilever(anim: str, i: int, n: int):
    w, h = CANTILEVER_FRAME
    f = K.Frame(CANTILEVER_FRAME)
    rng = random.Random("history_phosphate_cantilever")
    top = CANTILEVER_TOP
    x0, x1 = CANTILEVER_SPAN
    bottom = top + 24.0
    sea = 306.0
    # The sea and the reef rock under the tower, with surf at its edge.
    _water(f, 150.0, w - 8.0, sea - 4.0, sea + 36.0, SEA)
    _water(f, 170.0, w - 16.0, sea + 4.0, sea + 34.0, SEA_DEEP)
    _ripples(f, 220.0, w - 24.0, sea + 8.0, 0.0, SEA_LIGHT, 3, 7.0, "history_phosphate_cantilever ripples")
    rock = [(8.0, sea + 36.0), (10.0, 300.0), (24.0, 286.0), (52.0, 282.0), (150.0, 280.0), (186.0, 288.0), (206.0, 300.0), (222.0, 318.0),
            (228.0, sea + 36.0)]
    f.poly(rock, REEF)
    f.poly([(150.0, 284.0), (186.0, 290.0), (206.0, 302.0), (222.0, 318.0), (228.0, sea + 36.0), (120.0, sea + 36.0), (110.0, 310.0)], REEF_SHADE, body=False)
    f.ink([(14.0, 299.0), (26.0, 288.0), (52.0, 284.6)], 1.2, REEF_LIGHT)
    for _ in range(40):
        f.ellipse(rng.uniform(16.0, 210.0), rng.uniform(292.0, sea + 30.0), rng.uniform(0.8, 2.0), rng.uniform(0.6, 1.4), REEF_SHADE, body=False)
    for k in range(7):
        x = 200.0 + k * 6.0
        f.ellipse(x, sea + rng.uniform(-2.0, 6.0), rng.uniform(4.0, 7.0), rng.uniform(2.0, 3.4), FOAM, body=False)
    f.ink([(232.0, sea + 2.0), (262.0, sea + 2.0)], 1.2, FOAM)
    # The concrete footing on the rock.
    f.poly([(44.0, 286.0), (52.0, 258.0), (148.0, 258.0), (156.0, 286.0)], CONCRETE)
    f.poly([(112.0, 258.0), (148.0, 258.0), (156.0, 286.0), (118.0, 286.0)], CONCRETE_SHADE, body=False)
    f.ink([(52.0, 262.0), (148.0, 262.0)], 0.8, CONCRETE_SHADE)
    # The stays from the top of the tower to the arm, behind the arm.
    head = (100.0, 30.0)
    for x in (28.0, 290.0, 410.0, 530.0):
        f.limb([head, (x, top + 1.0)], 1.8, STEEL_SHADE)
    # The tower: four legs seen as two, tapered, with lattice bracing.
    lb, rb, lt, rt = (62.0, 260.0), (138.0, 260.0), (88.0, 34.0), (112.0, 34.0)
    levels = 6
    for k in range(levels):
        u0, u1 = k / float(levels), (k + 1) / float(levels)
        _lattice(f, _mix(lb, lt, u0), _mix(lb, lt, u1), _mix(rb, rt, u0), _mix(rb, rt, u1), 1, 1.8, STEEL)
    for a, b in ((lb, lt), (rb, rt)):
        f.limb([a, b], 4.6, STEEL)
        f.ink([(a[0] - 1.0, a[1] - 2.0), (b[0] - 1.0, b[1] + 2.0)], 0.8, STEEL_LIGHT)
    f.poly([(84.0, 22.0), (116.0, 22.0), (118.0, 36.0), (82.0, 36.0)], STEEL)
    f.poly(_rect(84.0, 30.0, 116.0, 36.0), STEEL_SHADE, body=False)
    f.ellipse(head[0], head[1] - 2.0, 4.0, 4.0, STEEL_DARK)
    # The arm: a lattice girder that reaches out over the sea. Its top is a
    # level deck.
    ax0, ax1 = 24.0, 552.0
    f.poly(_rect(ax0, top, ax1, top + 5.0), STEEL)
    f.poly(_rect(ax0, bottom - 3.0, ax1, bottom + 2.0), STEEL)
    bays = 22
    for k in range(bays + 1):
        x = _lerp(ax0 + 2.0, ax1 - 2.0, k / float(bays))
        f.limb([(x, top + 4.0), (x, bottom - 2.0)], 2.2, STEEL)
    for k in range(bays):
        xa = _lerp(ax0 + 2.0, ax1 - 2.0, k / float(bays))
        xb = _lerp(ax0 + 2.0, ax1 - 2.0, (k + 1) / float(bays))
        if k % 2:
            f.limb([(xa, top + 4.0), (xb, bottom - 2.0)], 1.6, STEEL_SHADE)
        else:
            f.limb([(xa, bottom - 2.0), (xb, top + 4.0)], 1.6, STEEL_SHADE)
    f.ink([(ax0 + 1.0, top + 1.0), (ax1 - 1.0, top + 1.0)], 1.0, STEEL_LIGHT)
    f.ink([(ax0 + 1.0, top + 4.4), (ax1 - 1.0, top + 4.4)], 0.6, STEEL_DARK)
    f.ink([(ax0 + 1.0, bottom + 1.4), (ax1 - 1.0, bottom + 1.4)], 0.6, STEEL_DARK)
    for k in range(int((ax1 - ax0) / 8.0)):
        x = ax0 + 4.0 + k * 8.0
        f.dot(x, top + 2.6, 0.5, STEEL_DARK)
        f.dot(x, bottom - 0.6, 0.5, STEEL_DARK)
    # The chute at the outer end, that pours the phosphate into the hold of
    # a ship.
    f.poly([(530.0, bottom), (552.0, bottom), (550.0, bottom + 16.0), (532.0, bottom + 16.0)], STEEL_SHADE)
    f.poly([(533.0, bottom + 14.0), (549.0, bottom + 14.0), (562.0, bottom + 84.0), (550.0, bottom + 88.0)], STEEL)
    f.poly([(541.0, bottom + 14.0), (549.0, bottom + 14.0), (562.0, bottom + 84.0), (556.0, bottom + 86.0)], STEEL_SHADE, body=False)
    f.poly([(546.0, bottom + 84.0), (564.0, bottom + 80.0), (566.0, bottom + 92.0), (550.0, bottom + 96.0)], STEEL_DARK)
    # Rust streaks on the old steel.
    for _ in range(14):
        x = rng.uniform(ax0 + 6.0, ax1 - 10.0)
        f.ink([(x, bottom + 1.0), (x + rng.uniform(-0.6, 0.6), bottom + rng.uniform(2.0, 5.0))], 0.8, K.alpha(STEEL_DARK, 0.6))
    del h
    return A.finish(f, width=1.4)


# ---------------------------------------------------------------------------
# The pinnacles of Topside.
# ---------------------------------------------------------------------------


def _spire(f: K.Frame, bx: float, ground: float, half: float, height: float, lean: float, rng: random.Random) -> None:
    """One pinnacle of coral limestone: a jagged spire with vertical
    flutes and pits, lit on its left."""
    tip = (bx + lean, ground - height)
    left: List[Point] = []
    right: List[Point] = []
    for k in range(9):
        u = k / 8.0
        wdt = half * (1.0 - u) ** 0.8 + 2.0
        y = _lerp(ground + 2.0, tip[1] + 6.0, u)
        x = _lerp(bx, tip[0], u)
        left.append((x - wdt + rng.uniform(-3.0, 3.0), y))
        right.append((x + wdt + rng.uniform(-3.0, 3.0), y + rng.uniform(-3.0, 3.0)))
    jag = [(tip[0] - 2.0, tip[1] + 4.0), (tip[0] + rng.uniform(-1.0, 1.0), tip[1]), (tip[0] + 3.0, tip[1] + 6.0)]
    f.poly(left + jag + list(reversed(right)), PINNACLE)
    f.poly([_mix(l, r, 0.6) for l, r in zip(left, right)] + jag[2:] + list(reversed(right)), PINNACLE_SHADE, body=False)
    f.poly([_mix(l, r, 0.08) for l, r in zip(left, right)][:-1] + list(reversed([_mix(l, r, 0.24) for l, r in zip(left, right)][:-1])), PINNACLE_LIGHT,
           body=False)
    # The flutes: grooves that run down the spire, cut by the rain.
    for s in (0.3, 0.45, 0.7, 0.85):
        pts = [_mix(l, r, s + rng.uniform(-0.03, 0.03)) for l, r in zip(left, right)][: rng.randint(6, 9)]
        f.ink(pts, 1.0, PINNACLE_DARK if s > 0.5 else PINNACLE_SHADE)
        f.ink([(p[0] - 1.4, p[1]) for p in pts], 0.6, PINNACLE_LIGHT)
    # Pits and holes.
    for _ in range(int(height / 8.0)):
        u = rng.uniform(0.0, 0.85)
        k = min(7, int(u * 8.0))
        p = _mix(_mix(left[k], right[k], rng.uniform(0.15, 0.85)), _mix(left[k + 1], right[k + 1], 0.5), u * 8.0 - k)
        f.ellipse(p[0], p[1], rng.uniform(0.8, 2.0), rng.uniform(0.8, 1.6), PINNACLE_DARK, body=False)


def _draw_pinnacles(anim: str, i: int, n: int):
    w, h = PINNACLES_FRAME
    f = K.Frame(PINNACLES_FRAME)
    rng = random.Random("history_pinnacles")
    ground = 264.0
    # The gaps between the pinnacles: deep, bare and dark, with a little
    # brown phosphate earth left at their floor.
    f.poly([(20.0, ground + 1.0), (24.0, ground - 70.0), (70.0, ground - 96.0), (140.0, ground - 104.0), (210.0, ground - 96.0), (262.0, ground - 66.0),
            (266.0, ground + 1.0)], GAP)
    f.poly([(40.0, ground - 40.0), (250.0, ground - 40.0), (262.0, ground + 1.0), (24.0, ground + 1.0)], GAP_DARK, body=False)
    f.poly([(22.0, ground - 10.0), (100.0, ground - 14.0), (180.0, ground - 12.0), (264.0, ground - 9.0), (266.0, ground + 1.0), (20.0, ground + 1.0)],
           PHOSPHATE)
    f.ink([(24.0, ground - 6.0), (262.0, ground - 5.0)], 0.6, PHOSPHATE_SHADE)
    for _ in range(18):
        f.dot(rng.uniform(26.0, 260.0), rng.uniform(ground - 8.0, ground - 1.0), 0.7, PHOSPHATE_SHADE)
    # The pinnacles, from the back to the front.
    for bx, half, hgt, lean in ((112.0, 32.0, 232.0, 4.0), (204.0, 30.0, 208.0, -6.0), (156.0, 26.0, 168.0, 2.0), (58.0, 28.0, 186.0, -4.0),
                                (246.0, 20.0, 128.0, 4.0), (30.0, 16.0, 104.0, -2.0), (182.0, 18.0, 96.0, 0.0), (90.0, 16.0, 76.0, 2.0)):
        _spire(f, bx, ground, half, hgt, lean, rng)
    del w, h
    return A.finish(f, width=1.4)


# ---------------------------------------------------------------------------
# The target ship.
# ---------------------------------------------------------------------------


def _turret(f: K.Frame, cx: float, base: float, facing: float) -> None:
    """A gun turret with two guns that point level along the deck, to the
    side `facing` (1 is to the right, -1 is to the left)."""
    f.limb([(cx + facing * 8.0, base - 7.0), (cx + facing * 44.0, base - 7.4)], 2.4, HAZE_SHADE)
    f.limb([(cx + facing * 8.0, base - 9.4), (cx + facing * 42.0, base - 9.8)], 2.2, HAZE)
    f.poly([(cx - 14.0, base), (cx - 12.0, base - 12.0), (cx + 10.0, base - 13.0), (cx + 15.0, base - 6.0), (cx + 15.0, base)] if facing > 0 else
           [(cx + 14.0, base), (cx + 12.0, base - 12.0), (cx - 10.0, base - 13.0), (cx - 15.0, base - 6.0), (cx - 15.0, base)], HAZE)
    f.poly(_rect(cx - 13.0, base - 4.0, cx + 14.0, base), HAZE_SHADE, body=False)
    f.ink([(cx - 11.0, base - 11.4), (cx + 9.0, base - 12.2)], 0.8, HAZE_LIGHT)


def _draw_target_ship(anim: str, i: int, n: int):
    w, h = TARGET_SHIP_FRAME
    f = K.Frame(TARGET_SHIP_FRAME)
    rng = random.Random("history_target_ship")
    wl = 164.0
    stern, bow = 22.0, 492.0

    def deck(x: float) -> float:
        if x > 300.0:
            return 138.0 - 6.0 * ((x - 300.0) / (bow - 300.0)) ** 2
        return 142.0

    # The tripod mast: three legs to a fire-control top.
    mx = 300.0
    for dx in (-10.0, 0.0, 10.0):
        f.limb([(mx + dx, deck(mx) - 30.0), (mx, 46.0)], 2.0, HAZE_SHADE if dx else HAZE)
    f.poly([(mx - 12.0, 46.0), (mx + 12.0, 46.0), (mx + 10.0, 34.0), (mx - 10.0, 34.0)], HAZE)
    f.poly(_rect(mx - 11.0, 40.0, mx + 11.0, 46.0), HAZE_SHADE, body=False)
    f.limb([(mx, 34.0), (mx, 18.0)], 1.4, HAZE_SHADE)
    f.limb([(mx - 8.0, 24.0), (mx + 8.0, 24.0)], 1.2, HAZE_SHADE)
    # The aft mast: a short pole with a yard.
    f.limb([(160.0, deck(160.0) - 20.0), (160.0, 70.0)], 2.2, HAZE_SHADE)
    f.limb([(152.0, 80.0), (168.0, 80.0)], 1.2, HAZE_SHADE)
    # The funnel: one, tall and plain, with no smoke.
    f.poly([(220.0, deck(220.0) - 26.0), (250.0, deck(250.0) - 26.0), (246.0, 72.0), (226.0, 72.0)], HAZE)
    f.poly([(238.0, deck(238.0) - 26.0), (250.0, deck(250.0) - 26.0), (246.0, 72.0), (238.0, 72.0)], HAZE_SHADE, body=False)
    f.poly(_rect(225.0, 70.0, 247.0, 76.0), HAZE_DARK)
    # The superstructure: the bridge forward, decks round the funnel, and
    # a deckhouse aft.
    f.poly([(268.0, deck(268.0)), (268.0, 104.0), (282.0, 96.0), (318.0, 96.0), (326.0, 104.0), (334.0, deck(334.0))], HAZE)
    f.poly(_rect(270.0, 96.0, 316.0, 102.0), HAZE_LIGHT, body=False)
    for k in range(6):
        f.poly(_rect(278.0 + k * 7.0, 99.0, 282.0 + k * 7.0, 101.4), HAZE_DARK, body=False)
    f.poly([(196.0, deck(196.0)), (196.0, 116.0), (268.0, 112.0), (268.0, deck(268.0))], HAZE)
    f.poly([(150.0, deck(150.0)), (150.0, 124.0), (196.0, 122.0), (196.0, deck(196.0))], HAZE)
    for x0, x1, y in ((196.0, 268.0, 120.0), (150.0, 196.0, 128.0), (268.0, 334.0, 116.0)):
        f.ink([(x0 + 2.0, y), (x1 - 2.0, y)], 0.8, HAZE_SHADE)
    for k in range(8):
        x = 204.0 + k * 8.0
        f.dot(x, 126.0, 0.9, HAZE_DARK)
    # Small guns for the air at rest on the upper decks.
    for x in (206.0, 258.0, 176.0):
        f.limb([(x, 114.0 if x > 196.0 else 122.0), (x + 6.0, 108.0 if x > 196.0 else 116.0)], 1.0, HAZE_DARK)
    # The turrets: two forward and two aft, the inner ones higher.
    _turret(f, 404.0, deck(404.0), 1.0)
    f.poly(_rect(342.0, deck(350.0) - 10.0, 374.0, deck(350.0)), HAZE)
    _turret(f, 358.0, deck(358.0) - 10.0, 1.0)
    _turret(f, 92.0, deck(92.0), -1.0)
    f.poly(_rect(118.0, deck(130.0) - 10.0, 150.0, deck(130.0)), HAZE)
    _turret(f, 134.0, deck(134.0) - 10.0, -1.0)
    # The hull: long and low, its stem raked at the bow, its stern round.
    xs = [stern + 8.0 + (bow - stern - 8.0) * k / 50.0 for k in range(51)]
    hull = [(stern, deck(stern) + 2.0)] + [(x, deck(x)) for x in xs] + [(bow + 2.0, deck(bow) - 2.0), (bow - 10.0, wl + 4.0), (stern + 16.0, wl + 4.0),
                                                                      (stern + 4.0, wl - 8.0)]
    f.poly(hull, HAZE)
    f.poly([(stern + 6.0, wl - 10.0), (bow - 14.0, wl - 10.0), (bow - 10.0, wl + 4.0), (stern + 16.0, wl + 4.0)], HAZE_SHADE, body=False)
    f.poly([(stern + 10.0, wl - 2.0), (bow - 12.0, wl - 2.0), (bow - 10.0, wl + 4.0), (stern + 14.0, wl + 4.0)], BOOT, body=False)
    f.ink([(x, deck(x) + 1.2) for x in xs[1:-1]], 0.9, HAZE_LIGHT)
    f.ink([(x, deck(x) + 8.0) for x in xs[4:-6]], 0.6, HAZE_SHADE)
    for k in range(18):
        x = 60.0 + k * 22.0
        f.dot(x, deck(x) + 5.0, 0.8, HAZE_DARK)
    # The anchor chain from the hawse, down into the water.
    hx = bow - 22.0
    f.ellipse(hx, deck(hx) + 6.0, 1.6, 1.4, HAZE_DARK)
    f.ink([(hx, deck(hx) + 6.0), (hx + 8.0, wl - 6.0), (hx + 10.0, wl + 2.0)], 0.8, HAZE_DARK)
    # The calm lagoon over its foot.
    _water(f, 8.0, w - 8.0, wl - 2.0, wl + 22.0, LAGOON)
    _water(f, 20.0, w - 20.0, wl + 4.0, wl + 20.0, LAGOON_DEEP)
    _ripples(f, 30.0, w - 30.0, wl + 6.0, 0.0, LAGOON_LIGHT, 2, 6.0, "history_target_ship ripples")
    del rng, h
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# The empty house of Bikini.
# ---------------------------------------------------------------------------


def _draw_empty_house(anim: str, i: int, n: int):
    w, h = EMPTY_HOUSE_FRAME
    f = K.Frame(EMPTY_HOUSE_FRAME)
    rng = random.Random("history_empty_house")
    ground = 200.0
    floor = 168.0
    eave = 104.0
    hx0, hx1 = 40.0, 216.0
    # The short posts under the floor.
    for x in (46.0, 100.0, 156.0, 210.0):
        f.limb([(x, floor), (x, ground + 1.0)], 5.0, PLANK_SHADE)
    f.poly(_rect(hx0 - 4.0, floor - 2.0, hx1 + 4.0, floor + 6.0), PLANK)
    f.ink([(hx0 - 2.0, floor + 4.0), (hx1 + 2.0, floor + 4.0)], 0.8, PLANK_SHADE)
    # The walls: planks on the left of the door, woven pandanus panels on
    # the right.
    f.poly(_rect(hx0, eave, hx1, floor - 2.0), PLANK)
    for k in range(int((112.0 - hx0) / 8.0) + 1):
        x = hx0 + k * 8.0
        f.ink([(x, eave + 2.0), (x, floor - 3.0)], 0.7, PLANK_SHADE)
        f.ink([(x + 1.2, eave + 2.0), (x + 1.2, floor - 3.0)], 0.5, PLANK_LIGHT)
    f.poly(_rect(146.0, eave + 2.0, hx1 - 2.0, floor - 3.0), PANDANUS, body=False)
    _weave(f, 146.0, eave + 4.0, hx1 - 2.0, floor - 4.0, 6.0, (196, 184, 150, 255), PANDANUS_SHADE)
    for x in (hx0, 112.0, 146.0, hx1):
        f.limb([(x, eave), (x, floor - 2.0)], 3.4, PLANK_SHADE)
    # The door: open, and dark inside, with no one in it. The door leaf
    # stands open against the wall.
    dx0, dx1 = 114.0, 144.0
    f.poly(_rect(dx0, eave + 14.0, dx1, floor - 2.0), DOORWAY)
    f.poly([(dx0 + 2.0, floor - 4.0), (dx1 - 2.0, floor - 4.0), (dx1 - 2.0, floor - 2.0), (dx0 + 2.0, floor - 2.0)], (60, 54, 50, 255), body=False)
    f.poly([(dx1 + 1.0, eave + 14.0), (dx1 + 9.0, eave + 18.0), (dx1 + 9.0, floor - 6.0), (dx1 + 1.0, floor - 2.0)], PLANK_LIGHT)
    f.ink([(dx1 + 5.0, eave + 17.0), (dx1 + 5.0, floor - 5.0)], 0.5, PLANK_SHADE)
    f.ink([(dx0, eave + 13.0), (dx1, eave + 13.0)], 2.0, PLANK_SHADE)
    # The shadow of the eaves.
    f.poly(_rect(hx0, eave, hx1, eave + 10.0), K.alpha((60, 54, 46, 255), 0.5), body=False)
    # The step under the door: a flat stone on a block.
    f.poly([(dx0 - 4.0, floor + 12.0), (dx1 + 4.0, floor + 12.0), (dx1 + 6.0, ground + 1.0), (dx0 - 6.0, ground + 1.0)], STONE_LIGHT)
    f.poly(_rect(dx0 - 5.0, floor + 20.0, dx1 + 5.0, ground + 1.0), STONE, body=False)
    # The rolled mat, on the ground by the step.
    mx, my = 176.0, ground - 6.0
    f.poly([(mx - 16.0, my - 6.0), (mx + 16.0, my - 6.0), (mx + 16.0, my + 6.0), (mx - 16.0, my + 6.0)], MAT)
    f.ellipse(mx + 16.0, my, 3.0, 6.0, MAT_SHADE)
    f.ink(_ring(mx + 16.0, my, 1.8, 3.6, 0.0, 330.0, 12), 0.5, (120, 106, 78, 255))
    for k in range(5):
        f.ink([(mx - 14.0 + k * 6.0, my - 6.0), (mx - 12.0 + k * 6.0, my + 6.0)], 0.5, MAT_SHADE)
    f.limb([(mx - 6.0, my - 6.4), (mx - 6.0, my + 6.4)], 1.0, (128, 110, 82, 255), body=False)
    f.limb([(mx + 8.0, my - 6.4), (mx + 8.0, my + 6.4)], 1.0, (128, 110, 82, 255), body=False)
    # The roof: steep thatch, with a patch of corrugated iron on its right.
    ridge = 30.0

    def lx(y: float) -> float:
        return _lerp(20.0, 74.0, (eave - y) / (eave - ridge))

    def rx(y: float) -> float:
        return w - lx(y)

    ys = [eave - (eave - ridge) * k / 20.0 for k in range(21)]
    fringe = [(rx(eave) - (rx(eave) - lx(eave)) * k / 40.0, eave + (2.4 if k % 2 else 0.0)) for k in range(41)]
    f.poly([(lx(y), y) for y in ys] + [(rx(y), y) for y in reversed(ys)] + fringe, DULL_THATCH)
    _thatch(f, lambda y: lx(y) + 2.0, lambda y: rx(y) - 2.0, lambda x: ridge, ridge + 6.0, eave - 4.0, 6.0, rng, DULL_THATCH_LIGHT, DULL_THATCH_SHADE)
    f.poly([(_lerp(lx(y), rx(y), 0.66), y) for y in ys] + [(rx(y), y) for y in reversed(ys)], K.alpha(DULL_THATCH_SHADE, 0.45), body=False)
    ix0, ix1, iy0, iy1 = 150.0, 196.0, 52.0, 86.0
    f.poly(_rect(ix0, iy0, ix1, iy1), IRON, body=False)
    for k in range(int((ix1 - ix0) / 4.0) + 1):
        x = ix0 + k * 4.0
        f.ink([(x, iy0 + 0.5), (x, iy1 - 0.5)], 0.7, IRON_LIGHT if k % 2 else K.shade(IRON, 0.8))
    f.ink([(ix0 + 2.0, iy1 - 2.0), (ix0 + 18.0, iy1 - 2.0)], 1.4, K.alpha(IRON_RUST, 0.7))
    f.ink([(ix1 - 6.0, iy0 + 4.0), (ix1 - 6.0, iy0 + 14.0)], 1.0, K.alpha(IRON_RUST, 0.6))
    f.poly([(lx(ridge) - 2.0, ridge), (rx(ridge) + 2.0, ridge), (rx(ridge) + 3.0, ridge + 6.0), (lx(ridge) - 3.0, ridge + 6.0)], DULL_THATCH_DARK)
    del h
    return A.finish(f, width=1.4)


# ---------------------------------------------------------------------------
# Publication.
# ---------------------------------------------------------------------------

FRAMES: Dict[str, Tuple[int, int]] = {
    "history_latte_house": LATTE_HOUSE_FRAME,
    "history_lusong": LUSONG_FRAME,
    "history_sakman": SAKMAN_FRAME,
    "history_stick_chart": STICK_CHART_FRAME,
    "history_basalt_wall": BASALT_WALL_FRAME,
    "history_sakau_stone": SAKAU_STONE_FRAME,
    "history_rai_big": RAI_BIG_FRAME,
    "history_rai_small": RAI_SMALL_FRAME,
    "history_faluw": FALUW_FRAME,
    "history_phosphate_cantilever": CANTILEVER_FRAME,
    "history_pinnacles": PINNACLES_FRAME,
    "history_target_ship": TARGET_SHIP_FRAME,
    "history_empty_house": EMPTY_HOUSE_FRAME,
}
DRAW: Dict[str, Callable] = {
    "history_latte_house": _draw_latte_house,
    "history_lusong": _draw_lusong,
    "history_sakman": _draw_sakman,
    "history_stick_chart": _draw_stick_chart,
    "history_basalt_wall": _draw_basalt_wall,
    "history_sakau_stone": _draw_sakau_stone,
    "history_rai_big": _draw_rai_big,
    "history_rai_small": _draw_rai_small,
    "history_faluw": _draw_faluw,
    "history_phosphate_cantilever": _draw_phosphate_cantilever,
    "history_pinnacles": _draw_pinnacles,
    "history_target_ship": _draw_target_ship,
    "history_empty_house": _draw_empty_house,
}
DISPLAY = {
    "history_latte_house": "Latte House",
    "history_lusong": "Lusong",
    "history_sakman": "Sakman",
    "history_stick_chart": "Stick Chart",
    "history_basalt_wall": "Basalt Wall",
    "history_sakau_stone": "Sakau Stone",
    "history_rai_big": "Rai",
    "history_rai_small": "Small Rai",
    "history_faluw": "Faluw",
    "history_phosphate_cantilever": "Phosphate Cantilever",
    "history_pinnacles": "Pinnacles",
    "history_target_ship": "Target Ship",
    "history_empty_house": "Empty House",
}
#: The room of each prop: its last tag.
ROOMS = {
    "history_latte_house": "marianas",
    "history_lusong": "marianas",
    "history_sakman": "marianas",
    "history_stick_chart": "marshalls",
    "history_basalt_wall": "nan_madol",
    "history_sakau_stone": "nan_madol",
    "history_rai_big": "yap",
    "history_rai_small": "yap",
    "history_faluw": "yap",
    "history_phosphate_cantilever": "nauru",
    "history_pinnacles": "nauru",
    "history_target_ship": "bikini",
    "history_empty_house": "bikini",
}
ROWS: Dict[str, List[Tuple[str, int, int]]] = {
    "history_sakman": LOOP,
}


def _foot(name: str) -> Dict[str, Tuple[float, float]]:
    w, h = FRAMES[name]
    return {"foot": (w / 2.0, float(h))}


#: The anchors of each prop. A platform has a "top" anchor at the middle of
#: the surface that a player stands on; the other props have a "foot".
ANCHORS: Dict[str, Dict[str, Tuple[float, float]]] = {name: _foot(name) for name in DISPLAY}
ANCHORS["history_sakman"] = {"top": ((SAKMAN_SPAN[0] + SAKMAN_SPAN[1]) / 2.0, SAKMAN_TOP)}
TAGS: Dict[str, List[str]] = {name: ["prop", "scenery", "history", ROOMS[name]] for name in DISPLAY}
TAGS["history_sakman"] = ["prop", "platform", "history", ROOMS["history_sakman"]]

TARGETS: Dict[str, dict] = {
    name: _publisher(name, DISPLAY[name], ROWS.get(name, STILL), FRAMES[name], DRAW[name], ANCHORS[name], "Scenery", TAGS[name]) for name in DISPLAY
}
