"""The props of Bengal and the cotton (the History dimension): Dhaka
muslin, the Company Raj and Ekushey.

At Dhaka, about 1700, Bengal was the richest province of the Mughal
empire. Women spun thread from the phuti karpas cotton that grew along the
Meghna. Weavers sat at pit looms, with their feet in a pit under the loom,
and wove muslin so fine that people called it "woven air": a length of it
could pass through a ring. Country boats (nouka) carried the cloth on the
Buriganga: long wooden hulls that rise at both ends, a curved roof of
bamboo matting (chhoi) over the middle, and a square sail.

After the battle of Plassey (1757) the East India Company ruled Bengal.
It bought the cloth at prices that it set, and shipped it in bales that
carried the Company's bale mark. At Serampore, from 1800, a mission press
cast type for Bengali and printed books on wooden hand presses.

In 1905 Begum Rokeya wrote "Sultana's Dream", a story of a land run by
women, where people flew in air-cars lifted by "hydrogen balls". On 21
February 1952 students in Dhaka died for the right to the Bengali language.
The Shaheed Minar stands for them: white columns in a row, the tallest one
in the middle bent forward at its top, like a mother over her children, in
front of a red sun. In 1971 people followed the war of independence on
transistor radios.

These props are drawn in the cel style of the dimension's cast
(`targets/characters/_history_americas_kit.py`): flat colour, one shade, a
bold warm outline. They show the skill and the dignity of the people who
made them.

- ``history_country_boat``: the look of a platform, a Bengal country boat:
  a long hull of dark wood that rises to a high stem and a high stern, a
  curved roof of bamboo matting over the middle, a square sail furled on
  its yard, and a steering oar at the stern. Its deck is the platform
  (`COUNTRY_BOAT_SPAN` = (30, 354), `COUNTRY_BOAT_TOP` = 104, in a 384 x
  160 frame).
- ``history_air_car``: the look of a platform, the air-car of "Sultana's
  Dream" as we imagine it: a small open carriage of polished wood and
  brass, two curved seats, two little wings, and two glowing hydrogen balls
  on short poles. Its floor is the platform (`AIR_CAR_SPAN` = (24, 296),
  `AIR_CAR_TOP` = 78, in a 320 x 128 frame). Its `idle` row glows and
  beats its wings; the floor stays level.
- ``history_pit_loom``: scenery, a Bengal pit loom: the pit and the
  weaver's bench, the frame with its heddles and beater, white warp
  threads, and a roll of muslin on the cloth beam.
- ``history_muslin_bolts``: scenery, folded bolts of muslin, so fine that
  they are nearly clear, on a low wooden stand; one length goes through a
  ring.
- ``history_company_bales``: scenery, bales of cotton in sacking and rope
  on a stone quay, stamped with a bale mark: a heart cut by a cross. There
  are no letters on them.
- ``history_serampore_press``: scenery, a wooden hand press of about 1800,
  a printed sheet (lines of strokes, no real writing) and a case of type.
- ``history_shaheed_minar``: scenery, the Shaheed Minar of Dhaka: five
  white columns on a base of steps, the tallest in the middle bent forward
  at its top, a large red sun behind them, and wreaths of marigolds at the
  foot. There are no people.
- ``history_radio_1971``: scenery, a transistor radio of the 1970s with its
  aerial up, on a small table.

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

COUNTRY_BOAT_FRAME = (384, 160)
#: The deck of the country boat is the platform: it is level from x0 to x1
#: at the height `COUNTRY_BOAT_TOP` (frame pixels).
COUNTRY_BOAT_SPAN = (30.0, 354.0)
COUNTRY_BOAT_TOP = 104.0
AIR_CAR_FRAME = (320, 128)
#: The floor of the air-car is the platform: it is level from x0 to x1 at
#: the height `AIR_CAR_TOP` (frame pixels).
AIR_CAR_SPAN = (24.0, 296.0)
AIR_CAR_TOP = 78.0
PIT_LOOM_FRAME = (192, 128)
MUSLIN_BOLTS_FRAME = (96, 64)
COMPANY_BALES_FRAME = (128, 96)
SERAMPORE_PRESS_FRAME = (128, 160)
SHAHEED_MINAR_FRAME = (256, 192)
RADIO_FRAME = (64, 48)

HULL = (104, 72, 48, 255)
HULL_LIGHT = (144, 104, 70, 255)
HULL_SHADE = (76, 52, 36, 255)
HULL_DARK = (54, 38, 28, 255)
MADDER = (172, 54, 44, 255)
MADDER_LIGHT = (214, 98, 74, 255)
MADDER_SHADE = (124, 36, 32, 255)
TURMERIC = (226, 172, 52, 255)
TURMERIC_LIGHT = (250, 210, 112, 255)
INDIGO = (52, 70, 128, 255)
INDIGO_LIGHT = (96, 118, 176, 255)
MATTING = (200, 170, 112, 255)
MATTING_LIGHT = (228, 204, 150, 255)
MATTING_SHADE = (156, 126, 78, 255)
MATTING_DARK = (112, 88, 54, 255)
BAMBOO = (176, 162, 98, 255)
BAMBOO_LIGHT = (212, 200, 136, 255)
BAMBOO_SHADE = (128, 114, 64, 255)
CANVAS = (222, 204, 162, 255)
CANVAS_LIGHT = (242, 230, 196, 255)
CANVAS_SHADE = (178, 158, 116, 255)
ROPE = (176, 146, 96, 255)
ROPE_DARK = (110, 88, 58, 255)
INTERIOR = (54, 40, 32, 255)

MAHOGANY = (146, 74, 44, 255)
MAHOGANY_LIGHT = (192, 116, 72, 255)
MAHOGANY_SHADE = (104, 50, 32, 255)
MAHOGANY_DARK = (72, 34, 24, 255)
BRASS = (214, 170, 70, 255)
BRASS_LIGHT = (248, 220, 132, 255)
BRASS_SHADE = (158, 116, 42, 255)
VELVET = (58, 112, 86, 255)
VELVET_LIGHT = (98, 156, 120, 255)
VELVET_SHADE = (38, 80, 62, 255)
FEATHER = (236, 226, 204, 255)
FEATHER_SHADE = (196, 182, 156, 255)
FEATHER_TIP = (150, 132, 108, 255)
HYDROGEN = (252, 244, 210, 255)
HYDROGEN_LIGHT = (255, 255, 244, 255)
HYDROGEN_SHADE = (236, 206, 140, 255)

TEAK = (150, 104, 62, 255)
TEAK_LIGHT = (188, 140, 90, 255)
TEAK_SHADE = (108, 72, 42, 255)
TEAK_DARK = (76, 50, 32, 255)
EARTH = (150, 112, 76, 255)
EARTH_LIGHT = (180, 140, 98, 255)
EARTH_SHADE = (112, 82, 56, 255)
PIT = (60, 42, 32, 255)
MUSLIN = (244, 242, 232, 255)
MUSLIN_SHADE = (214, 210, 196, 255)
MUSLIN_EDGE = (176, 168, 150, 255)
THREAD = (250, 248, 240, 255)

SACKING = (184, 154, 106, 255)
SACKING_LIGHT = (212, 184, 136, 255)
SACKING_SHADE = (142, 114, 76, 255)
SACKING_DARK = (108, 84, 56, 255)
STAMP = (52, 46, 60, 255)
QUAY = (156, 150, 140, 255)
QUAY_LIGHT = (186, 180, 168, 255)
QUAY_SHADE = (118, 112, 104, 255)

PAPER = (238, 228, 200, 255)
PAPER_SHADE = (206, 192, 160, 255)
PRINT = (46, 38, 36, 255)
TYPE_METAL = (120, 120, 126, 255)
TYPE_LIGHT = (170, 170, 176, 255)
LEATHER = (110, 66, 42, 255)
LEATHER_LIGHT = (150, 98, 64, 255)
IRON = (82, 80, 86, 255)
IRON_LIGHT = (136, 134, 140, 255)

MARBLE = (242, 240, 232, 255)
MARBLE_LIGHT = (255, 254, 248, 255)
MARBLE_SHADE = (200, 196, 186, 255)
MARBLE_DARK = (156, 150, 140, 255)
SUN = (206, 44, 42, 255)
SUN_LIGHT = (228, 82, 66, 255)
SUN_SHADE = (168, 30, 34, 255)
MARIGOLD = (240, 140, 30, 255)
MARIGOLD_LIGHT = (252, 192, 64, 255)
MARIGOLD_SHADE = (196, 96, 22, 255)
LEAF = (78, 124, 62, 255)
LEAF_SHADE = (54, 92, 46, 255)

RADIO_RED = (168, 60, 46, 255)
RADIO_RED_SHADE = (120, 40, 32, 255)
RADIO_CREAM = (232, 220, 190, 255)
RADIO_CREAM_SHADE = (194, 178, 144, 255)
GRILLE = (70, 58, 54, 255)
CHROME = (196, 198, 204, 255)
CHROME_SHADE = (130, 132, 140, 255)
DIAL = (240, 222, 150, 255)


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


def _script_line(f: K.Frame, x0: float, x1: float, y: float, rng: random.Random, colour: RGBA, size: float = 1.0) -> None:
    """A line that looks like Bengali print, with no real letters: short
    runs of top bar with short strokes that hang under it, and small gaps
    between the runs."""
    x = x0
    while x < x1 - 2.0 * size:
        run = min(x1, x + rng.uniform(4.0, 10.0) * size)
        f.ink([(x, y), (run, y)], 0.7 * size, colour)
        s = x + 1.0 * size
        while s < run - 0.5:
            f.ink([(s, y), (s + rng.uniform(-0.4, 0.4) * size, y + rng.uniform(1.4, 2.6) * size)], 0.5 * size, colour)
            s += rng.uniform(1.4, 2.6) * size
        x = run + rng.uniform(1.6, 2.8) * size


# ---------------------------------------------------------------------------
# The country boat (a platform).
# ---------------------------------------------------------------------------


def _boat_deck_y(x: float) -> float:
    """The top of the hull at `x`: level over the platform span, and swept
    up steeply to the high stem and the high stern, outside the span."""
    x0, x1 = COUNTRY_BOAT_SPAN
    if x < x0:
        return COUNTRY_BOAT_TOP - 42.0 * ((x0 - x) / 20.0) ** 1.7
    if x > x1:
        return COUNTRY_BOAT_TOP - 48.0 * ((x - x1) / 20.0) ** 1.7
    return COUNTRY_BOAT_TOP


def _boat_depth(x: float) -> float:
    """The depth of the hull under its top at `x`: deep in the middle and
    thin at the two horns."""
    u = (x - 192.0) / 182.0
    return 4.0 + 28.0 * max(0.0, 1.0 - abs(u) ** 3.0) ** 0.6


def _bamboo_pole(f: K.Frame, a: Point, b: Point, width: float, body: bool = True) -> None:
    """A pole of bamboo from `a` to `b`, with a ring at each node."""
    f.limb([a, b], width, BAMBOO, body)
    f.ink([(a[0] - width * 0.25, a[1]), (b[0] - width * 0.25, b[1])], width * 0.3, BAMBOO_LIGHT)
    for k in range(1, 9):
        p = _mix(a, b, k / 9.0)
        f.ink([(p[0] - width * 0.6, p[1] + 0.4), (p[0] + width * 0.6, p[1] - 0.4)], 0.8, BAMBOO_SHADE)


def _draw_country_boat(anim: str, i: int, n: int):
    f = K.Frame(COUNTRY_BOAT_FRAME)
    rng = random.Random("history_country_boat")
    top = COUNTRY_BOAT_TOP
    xs = [10.0 + (374.0 - 10.0) * k / 120.0 for k in range(121)]
    mast_x, mast_top = 300.0, 14.0
    # The steering oar at the stern: a long oar on a post. The helmsman
    # stands on the high stern and swings it. Its blade goes in the river.
    f.limb([(54.0, top), (52.0, 70.0)], 3.0, HULL_SHADE)
    f.limb([(70.0, 64.0), (26.0, 148.0)], 4.2, HULL_LIGHT)
    f.poly([(36.0, 126.0), (30.0, 122.0), (18.0, 146.0), (22.0, 152.0), (28.0, 150.0)], HULL_LIGHT)
    f.poly([(32.0, 128.0), (28.0, 150.0), (22.0, 152.0)], HULL_SHADE, body=False)
    f.limb([(46.0, 72.0), (58.0, 70.0)], 2.0, ROPE_DARK)
    # The mast and its stays. The stays are thin ropes and carry no body.
    f.ink([(mast_x, mast_top + 2.0), (370.0, _boat_deck_y(370.0) + 2.0)], 0.9, ROPE_DARK)
    f.ink([(mast_x, mast_top + 2.0), (262.0, top - 2.0)], 0.9, ROPE_DARK)
    f.limb([(mast_x, top), (mast_x, mast_top)], 4.6, BAMBOO)
    f.ink([(mast_x - 1.2, top - 1.0), (mast_x - 1.2, mast_top + 2.0)], 1.2, BAMBOO_LIGHT)
    for k in range(1, 8):
        y = _lerp(top, mast_top, k / 8.0)
        f.ink([(mast_x - 2.4, y + 0.5), (mast_x + 2.4, y - 0.5)], 0.8, BAMBOO_SHADE)
    f.ellipse(mast_x, mast_top - 1.0, 3.0, 2.4, HULL_SHADE)
    # The square sail is furled on its yard: a fat roll of patched cloth,
    # bound with ties, hung from the masthead by a halyard.
    yard_y = 36.0
    sx0, sx1 = 258.0, 344.0
    f.ink([(mast_x + 1.0, mast_top + 2.0), (mast_x + 1.0, yard_y - 4.0)], 1.0, ROPE_DARK)
    f.ink([(mast_x, mast_top + 2.0), (sx0 + 4.0, yard_y - 3.0)], 0.7, ROPE_DARK)
    f.ink([(mast_x, mast_top + 2.0), (sx1 - 4.0, yard_y - 3.0)], 0.7, ROPE_DARK)
    f.limb([(sx0 - 4.0, yard_y - 3.0), (sx1 + 4.0, yard_y - 3.0)], 3.0, BAMBOO_SHADE)
    def sag(x: float) -> float:
        return 2.5 * math.sin(math.pi * (x - sx0) / (sx1 - sx0))

    rxs = [_lerp(sx0, sx1, k / 16.0) for k in range(17)]
    roll = [(x, yard_y - 1.0 + sag(x) * 0.5) for x in rxs] + _ring(sx1, yard_y + 3.0, 3.5, 4.0, -90.0, 90.0, 6)[1:-1]
    roll += [(x, yard_y + 7.0 + sag(x)) for x in reversed(rxs)] + _ring(sx0, yard_y + 3.0, 3.5, 4.0, 90.0, 270.0, 6)[1:-1]
    f.poly(roll, CANVAS)
    f.poly([(x, yard_y + 4.0 + sag(x)) for x in rxs] + [(x, yard_y + 7.0 + sag(x)) for x in reversed(rxs)], CANVAS_SHADE, body=False)
    f.ink([(x, yard_y + 0.6 + sag(x) * 0.5) for x in rxs[1:-1]], 1.0, CANVAS_LIGHT)
    # The folds of the cloth, and the ties round the roll.
    for k in range(1, 16, 2):
        x = rxs[k]
        f.ink([(x - 2.0, yard_y + 1.0 + sag(x) * 0.6), (x + 2.0, yard_y + 5.0 + sag(x))], 0.6, CANVAS_SHADE)
    for k in range(5):
        x = sx0 + 8.0 + k * (sx1 - sx0 - 16.0) / 4.0
        f.ink([(x - 0.6, yard_y - 3.0), (x + 0.6, yard_y + 8.0 + sag(x))], 1.6, ROPE_DARK)
    for px, py in ((276.0, 39.0), (318.0, 39.6)):
        f.poly(_rect(px, py, px + 7.0, py + 4.0), CANVAS_SHADE, body=False)
    # The roof (chhoi): a long half barrel of bamboo matting on hoops of
    # split bamboo, over the middle of the deck. The passengers and the
    # cargo stay dry under it.
    rx0, rx1 = 132.0, 258.0
    rise = 44.0

    def roof_y(u: float) -> float:
        v = abs(2.0 * max(0.0, min(1.0, u)) - 1.0)
        return top - 2.0 - rise * (1.0 - v ** 3.0) ** 0.42

    us = [k / 48.0 for k in range(49)]
    arch = [(_lerp(rx0, rx1, u), roof_y(u)) for u in us]
    f.poly(arch + [(rx1, top), (rx0, top)], MATTING)
    f.poly([(_lerp(rx0, rx1, u), roof_y(u)) for u in us if u >= 0.7] + [(rx1, top), (_lerp(rx0, rx1, 0.7), top)], MATTING_SHADE, body=False)
    f.ink([(_lerp(rx0, rx1, u), roof_y(u) + 2.4) for u in us[3:30]], 1.6, MATTING_LIGHT)
    for k in range(1, 18):
        u = k / 18.0
        x = _lerp(rx0, rx1, u)
        f.ink([(x, roof_y(u) + 0.8), (x, top - 1.0)], 1.2, MATTING_DARK)
    for k in range(40):
        u = (k + 0.5) / 40.0
        x = _lerp(rx0, rx1, u)
        y = roof_y(u) + 5.0
        row = 0
        while y < top - 3.0:
            f.ink([(x - 1.2, y + (1.0 if row % 2 else -1.0)), (x + 1.2, y + (-1.0 if row % 2 else 1.0))], 0.6, MATTING_SHADE if u < 0.7 else MATTING_DARK)
            y += 5.0
            row += 1
    # The open end of the roof at the bow side: the last hoop, and the dark
    # inside under it, with a bundle of cargo.
    ex0 = rx1 - 14.0
    end = [(_lerp(rx0, rx1, u), roof_y(u) + 3.0) for u in us if _lerp(rx0, rx1, u) >= ex0 + 2.0]
    f.poly([(ex0 + 2.0, top - 1.0), (ex0 + 2.0, roof_y((ex0 + 2.0 - rx0) / (rx1 - rx0)) + 3.0)] + end + [(rx1 - 3.0, top - 1.0)], INTERIOR, body=False)
    f.poly([(ex0 + 4.0, top - 1.0), (ex0 + 5.0, top - 9.0), (ex0 + 10.0, top - 11.0), (rx1 - 2.0, top - 7.0), (rx1 - 2.0, top - 1.0)], CANVAS_SHADE, body=False)
    f.ink([(ex0 + 7.0, top - 10.0), (ex0 + 8.0, top - 2.0)], 0.7, ROPE_DARK)
    f.ink([(ex0, top - 1.0), (ex0, roof_y((ex0 - rx0) / (rx1 - rx0)) + 1.0)] + [(_lerp(rx0, rx1, u), roof_y(u) + 1.0) for u in us if _lerp(rx0, rx1, u) > ex0],
          2.0, BAMBOO)
    f.limb([(rx0 - 2.0, top - 1.0), (rx1 + 2.0, top - 1.0)], 3.0, BAMBOO_SHADE)
    # The hull: a long crescent of planks, tarred dark, that rises to a
    # tall stem at the bow and a tall stern. Its top is the deck, and the
    # deck is the platform.
    hull = [(x, _boat_deck_y(x)) for x in xs] + [(x, _boat_deck_y(x) + _boat_depth(x)) for x in reversed(xs)]
    f.poly(hull, HULL)
    f.poly([(x, _boat_deck_y(x) + _boat_depth(x) * 0.62) for x in xs[6:-6]] + [(x, _boat_deck_y(x) + _boat_depth(x)) for x in reversed(xs[6:-6])],
           HULL_SHADE, body=False)
    for t in (0.42, 0.62, 0.8):
        f.ink([(x, _boat_deck_y(x) + _boat_depth(x) * t) for x in xs[3:-3]], 0.8, HULL_DARK)
    # The seams of the planks are sewn and the joints show as short marks.
    for x in xs[8:-8:7]:
        t = rng.uniform(0.45, 0.75)
        f.ink([(x, _boat_deck_y(x) + _boat_depth(x) * t), (x, _boat_deck_y(x) + _boat_depth(x) * (t + 0.15))], 0.7, HULL_DARK)
    # The gunwale: a thick rail along the deck, and under it a painted band
    # of madder red with turmeric diamonds.
    f.limb([(x, _boat_deck_y(x) + 2.0) for x in xs[1:-1]], 3.8, HULL_LIGHT)
    band = [(x, _boat_deck_y(x) + 6.0) for x in xs[3:-3]] + [(x, _boat_deck_y(x) + 11.0) for x in reversed(xs[3:-3])]
    f.poly(band, MADDER, body=False)
    f.ink([(x, _boat_deck_y(x) + 10.6) for x in xs[3:-3]], 1.0, MADDER_SHADE)
    f.ink([(x, _boat_deck_y(x) + 6.4) for x in xs[3:-3]], 0.7, MADDER_LIGHT)
    for x in xs[6:-6:4]:
        y = _boat_deck_y(x) + 8.5
        f.poly([(x, y - 2.0), (x + 1.8, y), (x, y + 2.0), (x - 1.8, y)], TURMERIC, body=False)
    # The stem and the sternpost: the horns of the crescent end in a
    # carved knob.
    for x, s in ((372.0, 1.0), (12.0, -1.0)):
        y = _boat_deck_y(x)
        f.ellipse(x - s * 1.0, y + 1.0, 3.2, 3.2, HULL_LIGHT)
        f.dot(x - s * 1.6, y + 0.2, 1.0, TURMERIC_LIGHT)
    return A.finish(f, width=1.4)


# ---------------------------------------------------------------------------
# The air-car of "Sultana's Dream" (a platform).
# ---------------------------------------------------------------------------


def _air_bottom_y(x: float) -> float:
    """The bottom of the carriage at `x`: a shallow boat shape."""
    u = (x - 160.0) / 146.0
    return AIR_CAR_TOP + 4.0 + 22.0 * max(0.0, 1.0 - abs(u) ** 2.6) ** 0.7


def _wing(f: K.Frame, root: Point, s: float, lift: float, far: bool) -> None:
    """A little wing of white feathers. It grows up and back (to the left)
    from `root`; `s` scales it, and `lift` turns it up (degrees). The far
    wing is a shade darker."""
    base = FEATHER_SHADE if far else FEATHER
    shade = FEATHER_TIP if far else FEATHER_SHADE
    rx, ry = root

    def place(pts: Sequence[Point]) -> List[Point]:
        return _turn([(rx + x * s, ry + y * s) for x, y in pts], root, lift)

    # The leading edge arches up to the tip; the trailing edge is a row of
    # long feathers that come back to the root.
    lead = [(0.0, -2.0), (-14.0, -16.0), (-30.0, -27.0), (-46.0, -33.0), (-57.0, -33.0)]
    trail = [(-52.0, -26.0), (-55.0, -21.0), (-44.0, -18.0), (-47.0, -11.0), (-35.0, -9.0), (-36.0, -2.0), (-24.0, -1.0), (-22.0, 4.0), (-10.0, 3.0), (0.0, 4.0)]
    f.poly(place(lead + trail), base)
    f.poly(place([(0.0, -2.0), (-14.0, -16.0), (-30.0, -27.0), (-46.0, -33.0), (-42.0, -26.0), (-28.0, -17.0), (-14.0, -7.0), (-2.0, 0.0)]), shade, body=False)
    for a, b in (((-42.0, -26.0), (-52.0, -26.0)), ((-36.0, -21.0), (-44.0, -18.0)), ((-28.0, -15.0), (-35.0, -9.0)), ((-18.0, -9.0), (-24.0, -1.0)), ((-8.0, -3.0), (-10.0, 3.0))):
        f.ink(place([a, b]), 0.9, shade)
    f.ink(place([(-4.0, -4.0), (-16.0, -15.0), (-30.0, -24.0), (-44.0, -30.0)]), 0.8, FEATHER if far else (250, 246, 236, 255))
    f.ink(place([(-55.0, -32.0), (-53.0, -27.0)]), 1.2, FEATHER_TIP)


def _hydrogen_ball(f: K.Frame, x: float, foot: float, top: float, r: float, glow: float) -> None:
    """A glowing hydrogen ball held in a brass cup on a short pole."""
    f.limb([(x, foot), (x, top + r)], 2.8, BRASS)
    f.ink([(x - 0.7, foot - 1.0), (x - 0.7, top + r + 1.0)], 0.7, BRASS_LIGHT)
    f.ellipse(x, foot - 2.0, 4.0, 2.0, BRASS_SHADE)
    cy = top
    f.ellipse(x, cy, r, r, HYDROGEN)
    f.poly(_ring(x, cy, r, r, 20.0, 160.0, 14), HYDROGEN_SHADE, body=False)
    f.ellipse(x - r * 0.3, cy - r * 0.3, r * 0.42, r * 0.36, HYDROGEN_LIGHT, body=False)
    # The cup and its four brass straps hold the ball.
    f.poly([(x - r * 0.7, cy + r * 0.62), (x + r * 0.7, cy + r * 0.62), (x + r * 0.4, cy + r + 2.0), (x - r * 0.4, cy + r + 2.0)], BRASS)
    f.ink([(x - r * 0.6, cy + r * 0.72), (x + r * 0.6, cy + r * 0.72)], 0.8, BRASS_LIGHT)
    for dx in (-0.45, 0.45):
        f.ink([(x + r * dx * 1.3, cy + r * 0.7), (x + r * dx, cy - r * 0.2), (x + r * dx * 0.3, cy - r * 0.9)], 0.8, BRASS_SHADE)
    f.glow(x, cy, r + 4.0, (255, 236, 160, int(70 + 60 * glow)))
    f.glow(x, cy, r * 0.6, (255, 252, 230, int(120 + 80 * glow)))


def _seat(f: K.Frame, x0: float, floor: float) -> None:
    """An Edwardian seat that faces the bow (right): a curved back of
    green velvet in a wooden frame, a cushion, and small brass feet."""
    w = 38.0
    seat_y = floor - 13.0
    for x in (x0 + 4.0, x0 + w - 4.0):
        f.limb([(x, floor), (x, seat_y + 2.0)], 2.2, BRASS_SHADE)
    # The back curves up from the seat and over at its top, like a scroll.
    back = [(x0, seat_y + 4.0), (x0 - 3.0, seat_y - 10.0), (x0 - 2.0, seat_y - 22.0), (x0 + 4.0, seat_y - 29.0), (x0 + 11.0, seat_y - 28.0),
            (x0 + 13.0, seat_y - 22.0), (x0 + 9.0, seat_y - 18.0), (x0 + 8.0, seat_y - 6.0), (x0 + 12.0, seat_y)]
    f.poly(back, MAHOGANY)
    f.poly([(x0 + 1.0, seat_y - 2.0), (x0 - 0.5, seat_y - 12.0), (x0 + 1.0, seat_y - 22.0), (x0 + 5.0, seat_y - 25.0), (x0 + 9.0, seat_y - 23.0),
            (x0 + 6.0, seat_y - 18.0), (x0 + 5.0, seat_y - 5.0)], VELVET, body=False)
    f.ink([(x0 + 1.4, seat_y - 6.0), (x0 + 0.6, seat_y - 14.0), (x0 + 2.0, seat_y - 21.0)], 0.9, VELVET_LIGHT)
    for y in (seat_y - 9.0, seat_y - 16.0):
        f.dot(x0 + 3.0, y, 0.8, BRASS)
    f.ellipse(x0 + 11.0, seat_y - 22.0, 2.4, 2.4, MAHOGANY_LIGHT, body=False)
    # The cushion and the seat rail.
    f.poly([(x0 + 2.0, seat_y - 4.0), (x0 + w, seat_y - 4.0), (x0 + w + 2.0, seat_y), (x0 + w, seat_y + 3.0), (x0 + 2.0, seat_y + 3.0)], VELVET)
    f.ink([(x0 + 6.0, seat_y - 3.2), (x0 + w - 1.0, seat_y - 3.2)], 1.0, VELVET_LIGHT)
    f.poly([(x0 + 4.0, seat_y + 1.0), (x0 + w, seat_y + 1.0), (x0 + w, seat_y + 3.0), (x0 + 2.0, seat_y + 3.0)], VELVET_SHADE, body=False)
    f.limb([(x0 + 1.0, seat_y + 4.0), (x0 + w + 1.0, seat_y + 4.0)], 2.6, MAHOGANY_SHADE)
    # An arm rest at the front end, with a brass knob.
    f.limb([(x0 + w - 1.0, seat_y + 3.0), (x0 + w - 1.0, seat_y - 8.0), (x0 + w - 6.0, seat_y - 8.0)], 2.0, MAHOGANY)
    f.dot(x0 + w - 1.0, seat_y - 8.6, 1.4, BRASS)


def _draw_air_car(anim: str, i: int, n: int):
    f = K.Frame(AIR_CAR_FRAME)
    ph = i / float(max(1, n))
    top = AIR_CAR_TOP
    glow = 0.5 + 0.5 * math.sin(2.0 * math.pi * ph)
    flap = 10.0 * math.sin(2.0 * math.pi * ph)
    xs = [12.0 + (308.0 - 12.0) * k / 74.0 for k in range(75)]
    # The far wing shows above the carriage, behind the near one.
    _wing(f, (160.0, top - 1.0), 0.9, 8.0 + flap, True)
    # The two hydrogen balls on their poles, at the bow and the stern.
    _hydrogen_ball(f, 38.0, top, 28.0, 11.0, glow)
    _hydrogen_ball(f, 282.0, top, 28.0, 11.0, 1.0 - glow)
    # The two seats.
    _seat(f, 66.0, top)
    _seat(f, 204.0, top)
    # The steering lever by the front seat: a brass rod with a knob, on a
    # quadrant of brass.
    lx = 262.0
    f.poly(_ring(lx, top, 9.0, 9.0, 180.0, 360.0, 10), BRASS_SHADE)
    for a in range(200, 360, 30):
        p = _ring(lx, top, 7.0, 7.0, a, a, 1)[0]
        f.dot(p[0], p[1], 0.6, BRASS_LIGHT)
    f.limb([(lx, top - 1.0), (lx + 6.0, top - 26.0)], 2.2, BRASS)
    f.ellipse(lx + 6.4, top - 27.5, 3.0, 3.0, MAHOGANY_LIGHT)
    f.dot(lx + 5.6, top - 28.4, 0.9, BRASS_LIGHT)
    # The carriage: a small open shell of polished wood, curled up at the
    # bow and the stern like a scroll. Its top is the floor, and the floor
    # is the platform.
    bow = [(304.0, top), (309.0, top - 5.0), (310.0, top - 11.0), (306.0, top - 15.0), (301.0, top - 13.0), (302.0, top - 9.0), (305.0, top - 9.0)]
    body = [(16.0, top)] + [(x, top) for x in xs if 18.0 <= x <= 302.0] + [(304.0, top)]
    body += [(306.0, top + 3.0), (300.0, top + 10.0)] + [(x, _air_bottom_y(x)) for x in reversed(xs) if 22.0 <= x <= 296.0] + [(16.0, top + 8.0), (12.0, top + 3.0)]
    f.poly(body, MAHOGANY)
    f.limb(bow, 3.4, MAHOGANY_LIGHT)
    f.limb([(16.0, top), (12.0, top - 4.0), (14.0, top - 8.0), (18.0, top - 7.0)], 3.0, MAHOGANY_LIGHT)
    f.poly([(x, _air_bottom_y(x) - 7.0) for x in xs if 26.0 <= x <= 294.0] + [(x, _air_bottom_y(x)) for x in reversed(xs) if 26.0 <= x <= 294.0], MAHOGANY_SHADE, body=False)
    # The panels of the side, each framed in brass, with a stud at each
    # corner.
    for k in range(6):
        p0 = 44.0 + k * 40.0
        p1 = p0 + 32.0
        y1 = min(_air_bottom_y(p0), _air_bottom_y(p1)) - 9.0
        f.poly(_rect(p0, top + 7.0, p1, y1), MAHOGANY_LIGHT, body=False)
        f.poly(_rect(p0 + 2.0, top + 9.0, p1, y1), MAHOGANY, body=False)
        f.ink([(p0, top + 7.0), (p1, top + 7.0), (p1, y1), (p0, y1), (p0, top + 7.0)], 0.9, BRASS_SHADE)
        for x, y in ((p0, top + 7.0), (p1, top + 7.0), (p0, y1), (p1, y1)):
            f.dot(x, y, 0.9, BRASS_LIGHT)
    # The floor edge: a polished brass strip along the top of the side, and
    # a thin band of brass along the bottom.
    f.limb([(x, top + 2.0) for x in xs if 18.0 <= x <= 302.0], 3.6, BRASS)
    f.ink([(x, top + 1.0) for x in xs if 20.0 <= x <= 300.0], 0.9, BRASS_LIGHT)
    f.ink([(x, _air_bottom_y(x) - 3.0) for x in xs if 30.0 <= x <= 290.0], 1.4, BRASS)
    f.dot(306.0, top - 13.0, 1.4, BRASS_LIGHT)
    f.dot(16.0, top - 6.0, 1.2, BRASS_LIGHT)
    # The near wing, on the side of the carriage.
    _wing(f, (180.0, top + 8.0), 1.0, flap, False)
    # Faint motes of light fall from under the carriage and fade.
    for k in range(5):
        u = (ph + k / 5.0) % 1.0
        x = 70.0 + k * 46.0 + 4.0 * math.sin(2.0 * math.pi * (u + k * 0.3))
        y = _air_bottom_y(x) + 4.0 + 16.0 * u
        a = int(150 * (1.0 - u))
        if a > 10:
            f.glow(x, y, 1.6, (255, 236, 170, a))
    return A.finish(f, width=1.4)


# ---------------------------------------------------------------------------
# The pit loom.
# ---------------------------------------------------------------------------


def _draw_pit_loom(anim: str, i: int, n: int):
    w, h = PIT_LOOM_FRAME
    f = K.Frame(PIT_LOOM_FRAME)
    rng = random.Random("history_pit_loom")
    ground = h - 6.0
    floor = 104.0
    warp_y = 86.0
    beam_x, back_x = 58.0, 174.0
    # The floor of beaten earth, a block with a pit cut in it. The weaver
    # sits on its edge with the legs in the pit.
    f.poly([(10.0, floor), (184.0, floor), (184.0, ground), (10.0, ground)], EARTH)
    f.poly([(10.0, floor + 9.0), (184.0, floor + 9.0), (184.0, ground), (10.0, ground)], EARTH_SHADE, body=False)
    f.ink([(11.0, floor + 1.4), (183.0, floor + 1.4)], 1.0, EARTH_LIGHT)
    px0, px1 = 36.0, 76.0
    f.poly([(px0, floor), (px1, floor), (px1 - 2.0, ground - 3.0), (px0 + 2.0, ground - 3.0)], PIT, body=False)
    f.poly([(px1 - 6.0, floor), (px1, floor), (px1 - 2.0, ground - 3.0), (px1 - 7.0, ground - 3.0)], EARTH_SHADE, body=False)
    # The treadles in the pit: two foot boards on cords to the heddles.
    for k, x in enumerate((50.0, 60.0)):
        f.limb([(x - 6.0, ground - 6.0 - 2.0 * k), (x + 6.0, ground - 8.0 - 2.0 * k)], 2.0, TEAK)
    # The bench: a plank on two short legs at the back edge of the pit.
    f.limb([(18.0, floor), (18.0, 92.0)], 3.0, TEAK_SHADE)
    f.limb([(34.0, floor), (34.0, 92.0)], 3.0, TEAK_SHADE)
    f.poly(_rect(12.0, 88.0, 40.0, 93.0), TEAK)
    f.ink([(13.0, 89.0), (39.0, 89.0)], 0.9, TEAK_LIGHT)
    # The back post that holds the warp beam, and the warp beam.
    f.limb([(back_x, floor), (back_x, warp_y + 2.0)], 3.6, TEAK_SHADE)
    f.ellipse(back_x, warp_y, 4.4, 4.4, TEAK)
    f.ellipse(back_x - 1.0, warp_y - 1.0, 1.6, 1.6, TEAK_LIGHT, body=False)
    # The frame: two posts and a top bar. The heddles and the beater hang
    # from the bar on cords.
    fx0, fx1 = 82.0, 140.0
    frame_top = 26.0
    for x in (fx0, fx1):
        f.limb([(x, floor), (x, frame_top)], 4.0, TEAK)
        f.ink([(x - 1.0, floor - 1.0), (x - 1.0, frame_top + 2.0)], 1.0, TEAK_LIGHT)
    f.limb([(fx0 - 6.0, frame_top), (fx1 + 6.0, frame_top)], 5.0, TEAK)
    f.ink([(fx0 - 5.0, frame_top - 1.2), (fx1 + 5.0, frame_top - 1.2)], 1.0, TEAK_LIGHT)
    f.limb([(fx0, frame_top + 12.0), (fx1, frame_top + 12.0)], 2.4, TEAK_SHADE)
    # The warp: many fine white threads from the cloth beam to the warp
    # beam. At the heddles they part into two sheets (the shed) for the
    # shuttle to pass between them.
    hx = 116.0
    for k in range(7):
        dy = (k - 3) * 0.45
        f.ink([(beam_x + 4.0, warp_y - 2.0 + dy), (hx - 18.0, warp_y - 2.0 + dy * 0.6), (hx, warp_y - 4.0 + dy * 0.3), (back_x - 3.0, warp_y - 1.0 + dy)], 0.5, THREAD)
        f.ink([(beam_x + 4.0, warp_y - 1.0 + dy), (hx - 18.0, warp_y - 0.5 + dy * 0.6), (hx, warp_y + 2.0 + dy * 0.3), (back_x - 3.0, warp_y + 0.0 + dy)], 0.5, MUSLIN_SHADE)
    # The heddles: two shafts, each a pair of sticks with loops of cord
    # round the warp, hung from the top bar.
    for k, x in enumerate((hx - 3.0, hx + 3.0)):
        f.ink([(x, frame_top + 12.0), (x, warp_y - 12.0)], 0.8, ROPE_DARK)
        f.limb([(x - 0.4, warp_y - 12.0), (x + 0.4, warp_y - 12.0)], 2.2, TEAK_DARK)
        f.limb([(x, warp_y - 13.0), (x, warp_y + 10.0)], 1.8, TEAK_DARK)
        for y in range(int(warp_y - 10.0), int(warp_y + 9.0), 2):
            f.ink([(x - 1.6, y), (x + 1.6, y)], 0.4, ROPE)
        f.ink([(x, warp_y + 11.0), (x - 20.0 - 6.0 * k, floor - 1.0)], 0.6, ROPE_DARK)
    # The beater (the reed in its frame), hung on two cords from the bar.
    bx = 92.0
    f.ink([(bx, frame_top + 2.0), (bx, warp_y - 14.0)], 0.8, ROPE_DARK)
    f.limb([(bx, warp_y - 14.0), (bx, warp_y + 8.0)], 2.6, TEAK)
    f.poly(_rect(bx + 1.0, warp_y - 10.0, bx + 4.0, warp_y + 5.0), BAMBOO_SHADE)
    for y in range(int(warp_y - 9.0), int(warp_y + 5.0), 2):
        f.ink([(bx + 1.0, y), (bx + 4.0, y)], 0.4, BAMBOO_LIGHT)
    # The shuttle lies in the shed: a little boat of polished wood.
    f.poly([(100.0, warp_y), (104.0, warp_y - 1.6), (114.0, warp_y - 1.6), (118.0, warp_y), (114.0, warp_y + 1.4), (104.0, warp_y + 1.4)], TEAK_LIGHT)
    f.ink([(106.0, warp_y - 0.2), (112.0, warp_y - 0.2)], 0.6, TEAK_DARK)
    # The cloth beam, with the new muslin wound on it, and the woven web
    # between the beam and the beater: finer than the threads, nearly
    # clear.
    f.poly([(beam_x + 4.0, warp_y - 3.0), (bx - 1.0, warp_y - 3.0), (bx - 1.0, warp_y + 1.0), (beam_x + 4.0, warp_y + 1.6)], (246, 244, 236, 200), body=False)
    f.ink([(beam_x + 4.0, warp_y - 3.0), (bx - 1.0, warp_y - 3.0)], 0.6, MUSLIN_EDGE)
    f.limb([(beam_x, floor), (beam_x, warp_y + 4.0)], 3.4, TEAK_SHADE)
    f.ellipse(beam_x, warp_y, 9.0, 9.0, MUSLIN)
    f.poly(_ring(beam_x, warp_y, 9.0, 9.0, 10.0, 170.0, 12), MUSLIN_SHADE, body=False)
    for r in (3.0, 5.4, 7.6):
        f.ink(_ring(beam_x, warp_y, r, r, 200.0, 330.0, 10), 0.5, MUSLIN_EDGE)
    f.ellipse(beam_x, warp_y, 2.2, 2.2, TEAK_DARK, body=False)
    # A fold of the finished cloth hangs down from the roll towards the
    # pit, so fine that the beam post shows through it.
    f.poly([(beam_x - 8.0, warp_y + 4.0), (beam_x + 6.0, warp_y + 7.0), (beam_x + 8.0, floor - 2.0), (beam_x - 2.0, floor + 4.0), (beam_x - 7.0, floor - 1.0)],
           (248, 246, 238, 150), body=False)
    for k in range(3):
        x = beam_x - 5.0 + k * 4.4
        f.ink([(x, warp_y + 6.0), (x + 1.4 + rng.uniform(-0.4, 0.4), floor - 1.0)], 0.5, MUSLIN_EDGE)
    # A bowl of water stands by the warp: the fine thread needs damp air,
    # and the weaver wets it.
    f.ellipse(156.0, floor - 4.0, 7.0, 4.0, (112, 120, 132, 255))
    f.ellipse(156.0, floor - 6.6, 5.6, 1.4, (150, 186, 204, 255), body=False)
    return A.finish(f, width=1.4)


# ---------------------------------------------------------------------------
# The bolts of muslin.
# ---------------------------------------------------------------------------


def _draw_muslin_bolts(anim: str, i: int, n: int):
    w, h = MUSLIN_BOLTS_FRAME
    f = K.Frame(MUSLIN_BOLTS_FRAME)
    ground = h - 6.0
    top = 40.0
    sx0, sx1 = 8.0, 78.0
    # The low stand: a top of teak on four short turned legs.
    for x in (sx0 + 4.0, sx1 - 4.0):
        f.limb([(x, top + 4.0), (x, ground)], 3.0, TEAK)
        f.ellipse(x, top + 11.0, 2.2, 1.6, TEAK_LIGHT)
    f.limb([(sx0 + 5.0, ground - 6.0), (sx1 - 5.0, ground - 6.0)], 1.6, TEAK_SHADE)
    f.poly(_rect(sx0, top, sx1, top + 5.0), TEAK)
    f.ink([(sx0 + 1.0, top + 0.8), (sx1 - 1.0, top + 0.8)], 0.9, TEAK_LIGHT)
    f.poly(_rect(sx0, top + 3.5, sx1, top + 5.0), TEAK_SHADE, body=False)
    # Three folded bolts, one on another. Each fold is a flat block with a
    # rounded front edge, and the layers of the fold show as faint lines.
    bolts = ((12.0, 56.0, top, 8.0), (16.0, 54.0, top - 8.0, 7.0), (20.0, 50.0, top - 15.0, 6.0))
    for k, (x0, x1, y1, th) in enumerate(bolts):
        y0 = y1 - th
        f.poly([(x0 + 1.0, y0), (x1 - 2.0, y0), (x1, y0 + 2.0), (x1, y1 - 1.0), (x1 - 2.0, y1), (x0, y1), (x0, y0 + 1.0)], MUSLIN)
        f.poly([(x0, y1 - th * 0.35), (x1, y1 - th * 0.35), (x1 - 2.0, y1), (x0, y1)], MUSLIN_SHADE, body=False)
        for t in (0.3, 0.55, 0.78):
            f.ink([(x0 + 2.0, y0 + th * t), (x1 - 1.0, y0 + th * t)], 0.4, MUSLIN_EDGE)
        # A thin band of indigo thread ties each bolt.
        f.ink([(x0 + (x1 - x0) * 0.32, y0), (x0 + (x1 - x0) * 0.32, y1)], 0.9, INDIGO_LIGHT)
        f.ink([(x0 + (x1 - x0) * 0.68, y0), (x0 + (x1 - x0) * 0.68, y1)], 0.9, INDIGO_LIGHT)
    # The ring on its little post: a ring that a ring finger wears.
    rx, ry, rr = 70.0, 20.0, 5.2
    f.limb([(rx, top), (rx, ry + rr + 1.0)], 1.8, TEAK_SHADE)
    f.ellipse(rx, top - 1.0, 4.0, 1.6, TEAK)
    f.limb(_ring(rx, ry, rr, rr, 0.0, 360.0, 24), 1.8, A.MAIZE)
    f.ink(_ring(rx, ry, rr - 0.4, rr - 0.4, 200.0, 290.0, 8), 0.6, (252, 232, 150, 255))
    # One length of muslin comes off the top bolt, goes up through the
    # ring, and falls on the far side. It is so fine that the stand and the
    # post show through it.
    sheer = (252, 252, 248, 185)
    edge = (176, 168, 150, 255)
    up = [(48.0, top - 21.0), (56.0, top - 26.0), (64.0, ry + 1.6), (rx, ry - 1.6), (rx + 4.0, ry - 1.0)]
    down = [(rx + 4.0, ry + 2.6), (rx + 7.0, ry + 8.0), (rx + 10.0, top - 2.0), (rx + 12.0, top + 10.0), (rx + 14.0, top + 14.0)]
    lower = [(rx + 8.0, top + 13.0), (rx + 6.0, top + 4.0), (rx + 4.0, ry + 8.0), (rx, ry + 2.6), (64.0, ry + 4.0), (56.0, top - 20.0), (48.0, top - 16.0)]
    f.poly(up + down + lower, sheer, body=False)
    f.ink(up + down, 0.8, edge)
    f.ink(lower, 0.8, edge)
    for k in range(3):
        f.ink([(rx + 5.0 + k * 1.6, ry + 5.0), (rx + 7.0 + k * 2.0, top + 4.0 + k * 3.0)], 0.4, edge)
        f.ink([(52.0 + k * 3.0, top - 20.5 - k * 0.8), (60.0 + k * 2.4, ry + 4.0 - k)], 0.4, edge)
    # The ring is drawn again over the cloth where the cloth passes behind
    # its near side.
    f.ink(_ring(rx, ry, rr, rr, 300.0, 420.0, 10), 1.8, A.MAIZE)
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# The Company's bales.
# ---------------------------------------------------------------------------


def _heart(cx: float, cy: float, s: float) -> List[Point]:
    """The outline of a heart, `s` wide, with its point down."""
    out: List[Point] = []
    for k in range(40):
        t = 2.0 * math.pi * k / 40.0
        x = 16.0 * math.sin(t) ** 3
        y = 13.0 * math.cos(t) - 5.0 * math.cos(2 * t) - 2.0 * math.cos(3 * t) - math.cos(4 * t)
        out.append((cx + x * s / 34.0, cy - y * s / 34.0))
    return out


def _bale(f: K.Frame, x0: float, y0: float, x1: float, y1: float, rng: random.Random, mark: bool) -> None:
    """A bale of cotton pressed in sacking: a block with bulging sides, two
    bands of rope round it, and a bale mark stamped on its face."""
    b = 2.6
    outline = [(x0 + 3.0, y0), ((x0 + x1) / 2.0, y0 - b), (x1 - 3.0, y0), (x1, y0 + 3.0), (x1 + b * 0.6, (y0 + y1) / 2.0), (x1, y1 - 3.0),
               (x1 - 3.0, y1), ((x0 + x1) / 2.0, y1 + b * 0.6), (x0 + 3.0, y1), (x0, y1 - 3.0), (x0 - b * 0.6, (y0 + y1) / 2.0), (x0, y0 + 3.0)]
    f.poly(outline, SACKING)
    f.poly([(x0, (y0 + y1) / 2.0 + 4.0), (x1, (y0 + y1) / 2.0 + 4.0), (x1, y1 - 3.0), (x1 - 3.0, y1), ((x0 + x1) / 2.0, y1 + b * 0.6), (x0 + 3.0, y1), (x0, y1 - 3.0)],
           SACKING_SHADE, body=False)
    f.ink([(x0 + 4.0, y0 + 1.4), (x1 - 4.0, y0 + 1.4)], 1.0, SACKING_LIGHT)
    # The weave of the sacking.
    for _ in range(int((x1 - x0) * (y1 - y0) / 18.0)):
        x, y = rng.uniform(x0 + 2.0, x1 - 2.0), rng.uniform(y0 + 2.0, y1 - 2.0)
        f.ink([(x, y), (x + 1.4, y)], 0.4, SACKING_DARK)
    # The seam at the end, sewn with twine.
    for y in range(int(y0 + 3), int(y1 - 2), 3):
        f.ink([(x1 - 3.0, y), (x1 - 1.4, y + 1.4)], 0.6, SACKING_DARK)
    # Two bands of rope, and one round the middle.
    for u in (0.2, 0.8):
        x = _lerp(x0, x1, u)
        f.limb([(x, y0 - b * 0.6), (x, y1 + b * 0.4)], 1.8, ROPE)
        for y in range(int(y0), int(y1), 3):
            f.ink([(x - 0.8, y), (x + 0.8, y + 1.6)], 0.5, ROPE_DARK)
    ym = _lerp(y0, y1, 0.5)
    f.limb([(x0 - b * 0.5, ym), (x1 + b * 0.5, ym)], 1.6, ROPE)
    if mark:
        # The bale mark: a heart cut in four by a cross. There are no
        # letters in it.
        cx = (x0 + x1) / 2.0
        cy = _lerp(y0, y1, 0.3) + 1.0
        s = min(14.0, (x1 - x0) * 0.32)
        f.ink(_heart(cx, cy, s) + [_heart(cx, cy, s)[0]], 1.1, STAMP)
        f.ink([(cx, cy - s * 0.18), (cx, cy + s * 0.48)], 1.0, STAMP)
        f.ink([(cx - s * 0.46, cy + s * 0.04), (cx + s * 0.46, cy + s * 0.04)], 1.0, STAMP)


def _draw_company_bales(anim: str, i: int, n: int):
    w, h = COMPANY_BALES_FRAME
    f = K.Frame(COMPANY_BALES_FRAME)
    rng = random.Random("history_company_bales")
    ground = h - 4.0
    quay = ground - 7.0
    # The quay: a course of cut stone, its blocks set end to end.
    f.poly(_rect(6.0, quay, 122.0, ground), QUAY)
    f.ink([(7.0, quay + 1.0), (121.0, quay + 1.0)], 1.0, QUAY_LIGHT)
    for x in (30.0, 62.0, 94.0):
        f.ink([(x, quay + 1.0), (x, ground - 0.5)], 0.8, QUAY_SHADE)
    f.poly(_rect(6.0, ground - 2.0, 122.0, ground), QUAY_SHADE, body=False)
    # The bales: two below, one on them, and one more at the side.
    _bale(f, 12.0, quay - 30.0, 54.0, quay, rng, True)
    _bale(f, 58.0, quay - 30.0, 100.0, quay, rng, True)
    _bale(f, 34.0, quay - 60.0, 78.0, quay - 31.0, rng, True)
    _bale(f, 102.0, quay - 22.0, 118.0, quay, rng, False)
    # A loose end of rope lies on the stone.
    f.ink([(84.0, quay - 0.5), (92.0, quay - 2.0), (98.0, quay - 0.5)], 1.2, ROPE)
    return A.finish(f, width=1.3)


# ---------------------------------------------------------------------------
# The press of Serampore.
# ---------------------------------------------------------------------------


def _draw_serampore_press(anim: str, i: int, n: int):
    w, h = SERAMPORE_PRESS_FRAME
    f = K.Frame(SERAMPORE_PRESS_FRAME)
    rng = random.Random("history_serampore_press")
    ground = h - 6.0
    cx0, cx1 = 42.0, 76.0
    head_y = 16.0
    bed_y = 98.0
    # The bed and its rails: they run through the press, from the tympan
    # on the left to the far rail on the right, on a frame with feet.
    for x in (14.0, 108.0):
        f.limb([(x, bed_y + 4.0), (x, ground)], 3.6, TEAK_SHADE)
    f.limb([(14.0, ground - 10.0), (108.0, ground - 10.0)], 2.4, TEAK_SHADE)
    f.poly(_rect(10.0, bed_y, 112.0, bed_y + 6.0), TEAK)
    f.ink([(11.0, bed_y + 1.0), (111.0, bed_y + 1.0)], 0.9, TEAK_LIGHT)
    # The two cheeks: tall posts of heavy timber, on a heavy sill.
    f.poly(_rect(cx0 - 10.0, ground - 6.0, cx1 + 10.0, ground), TEAK_SHADE)
    for x in (cx0, cx1):
        f.poly(_rect(x - 4.5, head_y, x + 4.5, ground - 5.0), TEAK)
        f.poly(_rect(x + 1.5, head_y, x + 4.5, ground - 5.0), TEAK_SHADE, body=False)
        f.ink([(x - 3.4, head_y + 2.0), (x - 3.4, ground - 7.0)], 0.9, TEAK_LIGHT)
    # The head (with the nut of the screw in it) and the winter below the
    # bed, joining the cheeks.
    f.poly(_rect(cx0 - 7.0, head_y - 6.0, cx1 + 7.0, head_y + 8.0), TEAK)
    f.poly(_rect(cx0 - 7.0, head_y + 4.0, cx1 + 7.0, head_y + 8.0), TEAK_SHADE, body=False)
    f.ink([(cx0 - 6.0, head_y - 5.0), (cx1 + 6.0, head_y - 5.0)], 0.9, TEAK_LIGHT)
    f.poly(_rect(cx0 - 4.0, bed_y + 8.0, cx1 + 4.0, bed_y + 16.0), TEAK)
    f.poly(_rect(cx0 - 4.0, bed_y + 13.0, cx1 + 4.0, bed_y + 16.0), TEAK_SHADE, body=False)
    for x in (cx0 - 3.0, cx1 + 3.0):
        f.dot(x, head_y + 1.0, 1.2, IRON)
    # The screw, the hose round it, and the platen that presses the sheet
    # down on the type.
    sx = (cx0 + cx1) / 2.0
    f.limb([(sx, head_y + 8.0), (sx, 62.0)], 5.0, IRON)
    for y in range(int(head_y + 10.0), 50, 3):
        f.ink([(sx - 2.4, y), (sx + 2.4, y + 1.6)], 0.7, IRON_LIGHT)
    f.poly(_rect(sx - 8.0, 52.0, sx + 8.0, 70.0), TEAK_LIGHT)
    f.poly(_rect(sx + 3.0, 52.0, sx + 8.0, 70.0), TEAK, body=False)
    f.poly(_rect(cx0 + 4.0, 70.0, cx1 - 4.0, 76.0), IRON)
    f.ink([(cx0 + 5.0, 71.0), (cx1 - 5.0, 71.0)], 0.8, IRON_LIGHT)
    # The bar: it turns the screw. Its handle comes out to the right.
    f.limb([(sx, 58.0), (100.0, 64.0)], 2.6, IRON)
    f.limb([(98.0, 63.8), (112.0, 66.0)], 4.0, TEAK_LIGHT)
    # The forme of type on the bed under the platen, and its chase.
    f.poly(_rect(cx0 + 4.0, bed_y - 6.0, cx1 - 4.0, bed_y), IRON)
    for x in range(int(cx0 + 6), int(cx1 - 4), 2):
        f.ink([(x, bed_y - 5.0), (x, bed_y - 1.0)], 0.5, TYPE_LIGHT)
    # Two ink balls of leather on wooden handles, on the bed at the right.
    for bx, a in ((92.0, -14.0), (102.0, 12.0)):
        f.ellipse(bx, bed_y - 4.0, 5.0, 3.6, LEATHER)
        f.ellipse(bx - 1.4, bed_y - 5.2, 2.0, 1.2, LEATHER_LIGHT, body=False)
        f.ink([(bx, bed_y - 4.0), (bx, bed_y - 6.0)], 0.6, PRINT)
        f.limb(_turn([(bx, bed_y - 7.0), (bx, bed_y - 16.0)], (bx, bed_y - 7.0), a), 2.2, TEAK_LIGHT)
    # The tympan stands up on its hinge at the left end of the bed, with a
    # new sheet pinned on it: lines of print that look like Bengali, and no
    # real letters.
    tx0, tx1 = 10.0, 32.0
    ty0, ty1 = 40.0, bed_y - 1.0
    f.poly(_rect(tx0, ty0, tx1, ty1), TEAK)
    f.poly(_rect(tx0 + 2.0, ty0 + 2.0, tx1 - 2.0, ty1 - 2.0), PAPER)
    f.poly(_rect(tx1 - 6.0, ty0 + 2.0, tx1 - 2.0, ty1 - 2.0), PAPER_SHADE, body=False)
    f.poly(_rect(tx0 + 5.0, ty0 + 6.0, tx1 - 5.0, ty0 + 9.0), PRINT, body=False)
    y = ty0 + 13.0
    while y < ty1 - 6.0:
        _script_line(f, tx0 + 4.5, tx1 - 4.5, y, rng, PRINT, 0.75)
        y += 4.0
    f.ink([(tx0 + 4.0, ty1 - 4.0), (tx1 - 4.0, ty1 - 4.0)], 0.6, PRINT)
    f.dot(tx0 + 3.0, ty0 + 3.0, 0.8, IRON)
    f.dot(tx1 - 3.0, ty0 + 3.0, 0.8, IRON)
    # The case of type on its stand, in front of the press at the right:
    # a sloping tray of many small boxes, with type in them.
    kx0, kx1 = 84.0, 122.0
    ky0, ky1 = 118.0, 128.0
    for x in (kx0 + 3.0, kx1 - 3.0):
        f.limb([(x, ky1), (x, ground)], 2.4, TEAK)
    f.poly([(kx0, ky1), (kx0 + 2.0, ky0), (kx1 - 2.0, ky0), (kx1, ky1)], TEAK)
    f.poly([(kx0 + 2.0, ky1 - 1.0), (kx0 + 3.4, ky0 + 1.4), (kx1 - 3.4, ky0 + 1.4), (kx1 - 2.0, ky1 - 1.0)], TEAK_DARK, body=False)
    for k in range(1, 8):
        x = _lerp(kx0 + 2.6, kx1 - 2.6, k / 8.0)
        f.ink([(x, ky0 + 1.4), (x, ky1 - 1.0)], 0.6, TEAK_LIGHT)
    f.ink([(kx0 + 2.6, (ky0 + ky1) / 2.0), (kx1 - 2.6, (ky0 + ky1) / 2.0)], 0.6, TEAK_LIGHT)
    for _ in range(26):
        f.dot(rng.uniform(kx0 + 4.0, kx1 - 4.0), rng.uniform(ky0 + 2.4, ky1 - 2.0), 0.5, TYPE_LIGHT)
    f.limb([(kx0 + 3.0, ground - 8.0), (kx1 - 3.0, ground - 8.0)], 1.6, TEAK_SHADE)
    return A.finish(f, width=1.3)


# ---------------------------------------------------------------------------
# The Shaheed Minar.
# ---------------------------------------------------------------------------

#: The columns of the Shaheed Minar, left to right: (x0, x1, top). The
#: numbers are frame pixels; `top` is from the top of the frame. The middle
#: column bends forward over its top part, from `MINAR_BEND` to its top.
MINAR_COLUMNS: Tuple[Tuple[float, float, float], ...] = (
    (30.0, 54.0, 104.0),
    (66.0, 92.0, 74.0),
    (110.0, 146.0, 20.0),
    (164.0, 190.0, 74.0),
    (202.0, 226.0, 104.0),
)
MINAR_BEND = 60.0
MINAR_BASE = 160.0


def _minar_column(f: K.Frame, x0: float, x1: float, top: float, foot: float, bars: int, turn: float) -> None:
    """One column of the Minar: an open frame of white marble with thin
    upright bars of iron in it. `turn` (-1 to 1) is the way the column faces
    out of the line, so one side of it is in shade."""
    w = x1 - x0
    m = max(3.4, w * 0.15)
    ix0, ix1 = x0 + m, x1 - m
    iy0, iy1 = top + m, foot - 10.0
    # The iron bars go behind the marble, so the frame is drawn over them.
    for k in range(1, bars + 1):
        x = _lerp(ix0, ix1, k / float(bars + 1))
        f.limb([(x, iy0), (x, iy1)], 1.2, IRON)
    # The frame is cut through: the sky (or the sun) shows in the middle.
    f.poly(_rect(x0, top, x1, iy0), MARBLE)
    f.poly(_rect(x0, iy1, x1, foot), MARBLE)
    f.poly(_rect(x0, top, ix0, foot), MARBLE)
    f.poly(_rect(ix1, top, x1, foot), MARBLE)
    if turn < 0.0:
        f.poly(_rect(x0, top, x0 + m * (0.4 + 0.4 * abs(turn)), foot), MARBLE_SHADE, body=False)
    else:
        f.poly(_rect(x1 - m * (0.4 + 0.4 * abs(turn)), top, x1, foot), MARBLE_SHADE, body=False)
    f.ink([(ix0, iy1 + 0.5), (ix1, iy1 + 0.5)], 1.0, MARBLE_SHADE)
    f.ink([(x0 + 1.0, top + 1.0), (x1 - 1.0, top + 1.0)], 1.0, MARBLE_LIGHT)


def _wreath(f: K.Frame, cx: float, cy: float, r: float, rng: random.Random) -> None:
    """A round wreath of marigolds on a stand of bamboo, as people lay at
    the Minar on 21 February."""
    f.limb([(cx - r * 0.6, cy + r * 0.4), (cx - r * 0.8, MINAR_BASE + 26.0)], 1.6, BAMBOO_SHADE)
    f.limb([(cx + r * 0.6, cy + r * 0.4), (cx + r * 0.8, MINAR_BASE + 26.0)], 1.6, BAMBOO_SHADE)
    f.limb(_ring(cx, cy, r, r, 0.0, 360.0, 30), r * 0.5, LEAF)
    for k in range(18):
        a = 360.0 * k / 18.0 + rng.uniform(-6.0, 6.0)
        p = _ring(cx, cy, r, r, a, a, 1)[0]
        f.ellipse(p[0], p[1], r * 0.24, r * 0.24, MARIGOLD if k % 3 else MARIGOLD_LIGHT, body=False)
        f.dot(p[0] + 0.4, p[1] + 0.4, r * 0.1, MARIGOLD_SHADE)
    # A ribbon in the colours of the day, white and black, at its foot.
    f.poly([(cx - 2.0, cy + r - 1.0), (cx + 2.0, cy + r - 1.0), (cx + 4.0, cy + r + 8.0), (cx, cy + r + 5.0), (cx - 4.0, cy + r + 8.0)], MARBLE)
    f.ink([(cx - 1.0, cy + r + 1.0), (cx - 3.0, cy + r + 6.0)], 0.8, PRINT)


def _draw_shaheed_minar(anim: str, i: int, n: int):
    w, h = SHAHEED_MINAR_FRAME
    f = K.Frame(SHAHEED_MINAR_FRAME)
    rng = random.Random("history_shaheed_minar")
    ground = h - 6.0
    base = MINAR_BASE
    # The red sun behind the columns.
    sx, sy, sr = 128.0, 84.0, 58.0
    f.ellipse(sx, sy, sr, sr, SUN)
    f.poly(_ring(sx, sy, sr, sr, -30.0, 120.0, 24) + [(sx + sr * 0.4, sy + sr * 0.2)], SUN_SHADE, body=False)
    f.ink(_ring(sx, sy, sr - 4.0, sr - 4.0, 200.0, 260.0, 10), 2.0, SUN_LIGHT)
    # The base: a broad platform of three low steps.
    for k, (x0, x1) in enumerate(((10.0, 246.0), (18.0, 238.0), (26.0, 230.0))):
        y0 = base + 8.0 * (2 - k) - 0.0
        y1 = y0 + 8.0
        if k == 0:
            y0, y1 = base + 16.0, ground
        f.poly(_rect(x0, y0, x1, y1), MARBLE)
        f.ink([(x0 + 1.0, y0 + 1.0), (x1 - 1.0, y0 + 1.0)], 1.0, MARBLE_LIGHT)
        f.poly(_rect(x0, y1 - 2.4, x1, y1), MARBLE_SHADE, body=False)
    # The columns. The four at the sides turn a little out of the line, as
    # they stand on a half circle; the middle one faces straight on.
    turns = (-1.0, -0.5, 0.0, 0.5, 1.0)
    for (x0, x1, top), t in zip(MINAR_COLUMNS, turns):
        if t == 0.0:
            continue
        _minar_column(f, x0, x1, top, base, 4 if x1 - x0 < 26.0 else 5, t)
    # The middle column: a tall frame, and over it the top part bent
    # forward. The bent part leans out at the viewer, so it looks shorter,
    # a little wider at its top, and its underside shows in shade.
    x0, x1, top = MINAR_COLUMNS[2]
    bend = MINAR_BEND
    _minar_column(f, x0, x1, bend, base, 6, 0.0)
    # The kink: the underside of the bent part, in shade.
    f.poly([(x0 - 1.0, bend - 4.0), (x1 + 1.0, bend - 4.0), (x1, bend + 1.0), (x0, bend + 1.0)], MARBLE_DARK)
    m = 5.4
    ix0, ix1 = x0 + m, x1 - m
    iy0, iy1 = top + m, bend - 9.0
    for k in range(1, 7):
        u = k / 7.0
        f.limb([(_lerp(ix0 - 1.4, ix1 + 1.4, u), iy0), (_lerp(ix0, ix1, u), iy1)], 1.2, IRON)
    f.poly([(x0 - 3.0, top), (x1 + 3.0, top), (x1 + 2.6, iy0), (x0 - 2.6, iy0)], MARBLE)
    f.poly([(x0 - 0.6, iy1), (x1 + 0.6, iy1), (x1 + 1.0, bend - 4.0), (x0 - 1.0, bend - 4.0)], MARBLE)
    f.poly([(x0 - 3.0, top), (ix0 - 1.4, top), (ix0, bend - 4.0), (x0 - 1.0, bend - 4.0)], MARBLE)
    f.poly([(ix1 + 1.4, top), (x1 + 3.0, top), (x1 + 1.0, bend - 4.0), (ix1, bend - 4.0)], MARBLE)
    f.poly([(x1 - 1.0, top), (x1 + 3.0, top), (x1 + 1.0, bend - 4.0), (x1 - 2.4, bend - 4.0)], MARBLE_SHADE, body=False)
    f.ink([(ix0, iy1 + 0.5), (ix1, iy1 + 0.5)], 1.0, MARBLE_SHADE)
    f.ink([(x0 - 2.0, top + 1.0), (x1 + 2.0, top + 1.0)], 1.0, MARBLE_LIGHT)
    # Wreaths of marigolds stand at the foot, and loose flowers lie on the
    # steps.
    for cx, cy, r in ((72.0, base + 6.0, 11.0), (128.0, base + 4.0, 13.0), (184.0, base + 6.0, 11.0)):
        _wreath(f, cx, cy, r, rng)
    for _ in range(26):
        x = rng.uniform(24.0, 232.0)
        y = rng.choice((base + 15.0, base + 23.0, ground - 2.0))
        f.dot(x, y, 1.3, MARIGOLD if rng.random() < 0.7 else MARIGOLD_LIGHT)
    return A.finish(f, width=1.4)


# ---------------------------------------------------------------------------
# The radio of 1971.
# ---------------------------------------------------------------------------


def _draw_radio_1971(anim: str, i: int, n: int):
    w, h = RADIO_FRAME
    f = K.Frame(RADIO_FRAME)
    ground = h - 5.0
    top = 32.0
    # The small table: a round top on three thin legs.
    for x0, x1 in ((16.0, 12.0), (32.0, 32.0), (48.0, 52.0)):
        f.limb([(x0, top + 2.0), (x1, ground)], 1.6, TEAK_SHADE)
    f.poly(_rect(8.0, top, 56.0, top + 3.0), TEAK)
    f.ink([(9.0, top + 0.6), (55.0, top + 0.6)], 0.7, TEAK_LIGHT)
    # The aerial: a chrome rod in three sections, drawn out, at a slant.
    ax, ay = 42.0, 16.0
    f.limb([(ax, ay), (ax + 4.0, ay - 6.0)], 1.4, CHROME)
    f.limb([(ax + 4.0, ay - 6.0), (ax + 8.0, ay - 9.5)], 1.0, CHROME)
    f.limb([(ax + 8.0, ay - 9.5), (ax + 10.0, ay - 11.0)], 0.8, CHROME)
    f.dot(ax + 10.0, ay - 11.0, 0.9, CHROME_SHADE)
    # The handle: a strap of leather over the top.
    f.limb([(18.0, 17.0), (20.0, 12.5), (36.0, 12.5), (38.0, 17.0)], 1.6, RADIO_RED_SHADE)
    # The case: red leatherette with a cream front, and rounded corners.
    x0, x1, y0, y1 = 14.0, 46.0, 16.0, top
    f.poly([(x0 + 2.0, y0), (x1 - 2.0, y0), (x1, y0 + 2.0), (x1, y1), (x0, y1), (x0, y0 + 2.0)], RADIO_RED)
    f.poly(_rect(x0, y1 - 3.0, x1, y1), RADIO_RED_SHADE, body=False)
    f.poly(_rect(x0 + 2.0, y0 + 3.0, x1 - 2.0, y1 - 3.0), RADIO_CREAM, body=False)
    f.poly(_rect(x0 + 2.0, y1 - 5.0, x1 - 2.0, y1 - 3.0), RADIO_CREAM_SHADE, body=False)
    # The speaker grille: rows of holes.
    for gy in range(int(y0 + 5), int(y1 - 5), 2):
        for gx in range(int(x0 + 4), int(x0 + 18), 2):
            f.dot(gx + (1.0 if gy % 4 else 0.0), gy + 0.5, 0.5, GRILLE)
    # The dial: a window with a scale of marks and a red needle, and the
    # tuning knob under it.
    dx0, dx1 = x0 + 20.0, x1 - 4.0
    f.poly(_rect(dx0, y0 + 5.0, dx1, y0 + 10.0), DIAL, body=False)
    for k in range(6):
        x = _lerp(dx0 + 1.0, dx1 - 1.0, k / 5.0)
        f.ink([(x, y0 + 5.4), (x, y0 + 7.0)], 0.4, PRINT)
    f.ink([(dx0 + 4.4, y0 + 5.0), (dx0 + 4.4, y0 + 10.0)], 0.6, RADIO_RED)
    f.ink([(dx0, y0 + 5.0), (dx1, y0 + 5.0), (dx1, y0 + 10.0), (dx0, y0 + 10.0), (dx0, y0 + 5.0)], 0.5, GRILLE)
    f.ellipse((dx0 + dx1) / 2.0, y1 - 8.5, 2.6, 2.6, CHROME)
    f.dot((dx0 + dx1) / 2.0 - 0.6, y1 - 9.1, 0.8, (240, 240, 244, 255))
    return A.finish(f, width=1.1)


# ---------------------------------------------------------------------------
# Publication.
# ---------------------------------------------------------------------------

FRAMES: Dict[str, Tuple[int, int]] = {
    "history_country_boat": COUNTRY_BOAT_FRAME,
    "history_air_car": AIR_CAR_FRAME,
    "history_pit_loom": PIT_LOOM_FRAME,
    "history_muslin_bolts": MUSLIN_BOLTS_FRAME,
    "history_company_bales": COMPANY_BALES_FRAME,
    "history_serampore_press": SERAMPORE_PRESS_FRAME,
    "history_shaheed_minar": SHAHEED_MINAR_FRAME,
    "history_radio_1971": RADIO_FRAME,
}
DRAW: Dict[str, Callable] = {
    "history_country_boat": _draw_country_boat,
    "history_air_car": _draw_air_car,
    "history_pit_loom": _draw_pit_loom,
    "history_muslin_bolts": _draw_muslin_bolts,
    "history_company_bales": _draw_company_bales,
    "history_serampore_press": _draw_serampore_press,
    "history_shaheed_minar": _draw_shaheed_minar,
    "history_radio_1971": _draw_radio_1971,
}
DISPLAY = {
    "history_country_boat": "Country Boat",
    "history_air_car": "Air-Car",
    "history_pit_loom": "Pit Loom",
    "history_muslin_bolts": "Muslin Bolts",
    "history_company_bales": "Company Bales",
    "history_serampore_press": "Serampore Press",
    "history_shaheed_minar": "Shaheed Minar",
    "history_radio_1971": "Radio, 1971",
}
#: The room of each prop: its last tag.
ROOMS = {
    "history_country_boat": "dhaka_muslin",
    "history_air_car": "ekushey",
    "history_pit_loom": "dhaka_muslin",
    "history_muslin_bolts": "dhaka_muslin",
    "history_company_bales": "company_raj",
    "history_serampore_press": "company_raj",
    "history_shaheed_minar": "ekushey",
    "history_radio_1971": "ekushey",
}
ROWS: Dict[str, List[Tuple[str, int, int]]] = {
    "history_air_car": LOOP,
}


def _foot(name: str) -> Dict[str, Tuple[float, float]]:
    w, h = FRAMES[name]
    return {"foot": (w / 2.0, float(h))}


#: The anchors of each prop. A platform has a "top" anchor at the middle of
#: the surface that a player stands on; the other props have a "foot".
ANCHORS: Dict[str, Dict[str, Tuple[float, float]]] = {name: _foot(name) for name in DISPLAY}
ANCHORS["history_country_boat"] = {"top": ((COUNTRY_BOAT_SPAN[0] + COUNTRY_BOAT_SPAN[1]) / 2.0, COUNTRY_BOAT_TOP)}
ANCHORS["history_air_car"] = {"top": ((AIR_CAR_SPAN[0] + AIR_CAR_SPAN[1]) / 2.0, AIR_CAR_TOP)}
TAGS: Dict[str, List[str]] = {name: ["prop", "scenery", "history", ROOMS[name]] for name in DISPLAY}
TAGS["history_country_boat"] = ["prop", "platform", "history", ROOMS["history_country_boat"]]
TAGS["history_air_car"] = ["prop", "platform", "history", ROOMS["history_air_car"]]

TARGETS: Dict[str, dict] = {
    name: _publisher(name, DISPLAY[name], ROWS.get(name, STILL), FRAMES[name], DRAW[name], ANCHORS[name], "Scenery", TAGS[name]) for name in DISPLAY
}
