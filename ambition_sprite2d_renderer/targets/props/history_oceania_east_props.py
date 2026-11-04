"""The props of the eastern Oceania rooms of the History dimension.

The third pass of the History dimension carries the Oceania floor east,
from the New Guinea highlands to Rapa Nui: the Lapita voyagers (1,500 BCE),
the Polynesian wayfinders, and Rapa Nui (1200-1600 CE). The props are drawn
in the cel style of the dimension's cast (`targets/characters/_history_americas_kit.py`):
flat colour, one shade, a bold warm outline. They show the skill of the
first people to sail out of sight of land into remote Oceania, with
respect: no sacred object as a joke.

- ``history_lapita_pot``: scenery, a pot with bands of toothed-stamp
  patterns, white lime pressed into the marks, on a ring of fibre.
- ``history_stilt_house``: scenery, a thatched house on stilts over the
  lagoon, with a ladder and a canoe tied at a post.
- ``history_outrigger_canoe``: the look of a platform, a canoe with an
  outrigger float and a crab-claw sail. The top of its gunwale is the
  platform (`platform_looks.ron`: `OUTRIGGER_SPAN`, `OUTRIGGER_TOP`).
- ``history_coconut_palm``: scenery, a leaning coconut palm. Its ``idle``
  row sways.
- ``history_voyaging_canoe``: the look of a platform, a double-hulled
  voyaging canoe with a deck between the hulls, a shelter and a crab-claw
  sail. The top of its deck is the platform (`VOYAGING_SPAN`,
  `VOYAGING_TOP`).
- ``history_star_compass``: scenery, a ring of marker stones on the sand:
  the points where stars rise and set, as a navigator learns them.
- ``history_breadfruit_tree``: scenery, a breadfruit tree with big lobed
  leaves and round green fruit. Its ``idle`` row sways.
- ``history_moai``: scenery, a moai on its ahu platform, its back to the
  sea, a red pukao of scoria on its head.
- ``history_walking_moai``: the look of a platform, a moai that rocks from
  side to side as two teams pull ropes on both sides: so the people "walked"
  the moai upright from the quarry. The top of its pukao is the platform
  (`WALKING_SPAN`, `WALKING_TOP`); the pukao stays level while the body
  rocks under it.
- ``history_rongorongo_tablet``: scenery, a wooden tablet with rows of small
  glyph-like marks. The marks are made up: they copy no real text.
- ``history_kumara``: scenery, sweet potato plants on a mound, with a dug
  tuber. The sweet potato came from South America, so the voyagers reached
  it.

The numbers are frame pixels; the game shows each prop at half its frame.
No drop shadows: the game draws them.
"""

from __future__ import annotations

import math
import random
from typing import Dict, List, Sequence, Tuple

from ..characters import _art_cast_kit as K
from ..characters import _history_americas_kit as A
from .art_props import STILL, _publisher

Point = Tuple[float, float]

POT_FRAME = (96, 96)
STILT_FRAME = (256, 320)
OUTRIGGER_FRAME = (384, 192)
OUTRIGGER_SPAN = (16.0, 368.0)
OUTRIGGER_TOP = 140.0
PALM_FRAME = (192, 384)
VOYAGING_FRAME = (448, 256)
VOYAGING_SPAN = (16.0, 432.0)
VOYAGING_TOP = 196.0
COMPASS_FRAME = (256, 64)
BREADFRUIT_FRAME = (256, 320)
MOAI_FRAME = (192, 384)
WALKING_FRAME = (192, 384)
WALKING_SPAN = (56.0, 136.0)
WALKING_TOP = 36.0
TABLET_FRAME = (96, 64)
KUMARA_FRAME = (128, 96)
SWAY: List[Tuple[str, int, int]] = [("idle", 8, 160)]
ROCK: List[Tuple[str, int, int]] = [("idle", 8, 180)]
SCENERY = ["prop", "scenery", "history"]
PLATFORM = ["prop", "platform", "history"]

CLAY = (184, 102, 64, 255)
CLAY_SHADE = (138, 70, 44, 255)
CLAY_LIGHT = (214, 140, 96, 255)
LIME = (246, 240, 222, 255)
FIBRE = (176, 140, 84, 255)
FIBRE_DARK = (122, 92, 52, 255)
THATCH = (204, 168, 96, 255)
THATCH_SHADE = (150, 116, 60, 255)
THATCH_LIGHT = (232, 206, 140, 255)
WOOD = (150, 100, 62, 255)
WOOD_SHADE = (106, 68, 40, 255)
WOOD_LIGHT = (188, 138, 92, 255)
WOVEN = (196, 160, 104, 255)
WOVEN_SHADE = (156, 120, 72, 255)
LAGOON = (64, 176, 186, 210)
LAGOON_LIGHT = (150, 222, 220, 220)
LAGOON_DEEP = (40, 128, 150, 220)
PANDANUS = (222, 196, 136, 255)
PANDANUS_SHADE = (178, 148, 92, 255)
TAPA_RED = (150, 64, 40, 255)
LEAF = (78, 150, 68, 255)
LEAF_SHADE = (50, 106, 48, 255)
LEAF_LIGHT = (128, 188, 90, 255)
PALM_TRUNK = (152, 124, 92, 255)
PALM_TRUNK_SHADE = (112, 88, 64, 255)
COCONUT = (120, 150, 60, 255)
COCONUT_BROWN = (128, 86, 50, 255)
BREADFRUIT = (150, 186, 70, 255)
BREADFRUIT_SHADE = (110, 146, 50, 255)
SAND = (232, 210, 160, 255)
SAND_SHADE = (196, 170, 120, 255)
STONE = (120, 116, 112, 255)
STONE_SHADE = (84, 80, 78, 255)
STONE_LIGHT = (160, 156, 148, 255)
TUFF = (150, 138, 118, 255)
TUFF_SHADE = (108, 98, 84, 255)
TUFF_LIGHT = (186, 174, 150, 255)
LICHEN = (196, 186, 110, 255)
SCORIA = (172, 70, 48, 255)
SCORIA_SHADE = (126, 46, 32, 255)
SCORIA_LIGHT = (206, 104, 74, 255)
ROPE = (196, 164, 104, 255)
ROPE_DARK = (138, 108, 60, 255)
TABLET = (128, 86, 54, 255)
TABLET_SHADE = (92, 60, 38, 255)
TABLET_MARK = (46, 26, 16, 255)
SOIL = (122, 84, 56, 255)
SOIL_DARK = (88, 58, 38, 255)
KUMARA_SKIN = (170, 70, 96, 255)
KUMARA_SHADE = (122, 44, 70, 255)
KUMARA_FLESH = (236, 170, 90, 255)


def _ellipse(cx: float, cy: float, rx: float, ry: float, n: int = 24) -> List[Point]:
    return K.ellipse_points(cx, cy, rx, ry, n)


def _bez(p0: Point, p1: Point, p2: Point, n: int = 12) -> List[Point]:
    """Points on the quadratic curve from `p0` to `p2`, pulled toward `p1`."""
    out = []
    for k in range(n + 1):
        u = k / n
        out.append(((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0], (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1]))
    return out


def _crab_claw_sail(f: K.Frame, foot: Point, mast_top: Point, reach: float, lean: float) -> None:
    """A crab-claw sail of pandanus matting: two spars spread from a foot
    near the deck, each curved like a horn, and the sail between them cut
    in a deep curve. `mast_top` is where the front spar is held up; `reach`
    is how far back the rear spar goes; `lean` tips the whole sail back."""
    fx, fy = foot
    front = _bez(foot, (mast_top[0] + 16.0, (fy + mast_top[1]) / 2.0), (mast_top[0] - 18.0 - lean, mast_top[1]))
    back_tip = (fx - reach, mast_top[1] + 24.0)
    back = _bez(foot, (fx - reach * 0.75, fy - 20.0), back_tip)
    # The cut between the horns: a deep curve down between the spar tips.
    notch = _bez(front[-1], ((front[-1][0] + back_tip[0]) / 2.0, (front[-1][1] + back_tip[1]) / 2.0 + 64.0), back_tip)
    sail = front + notch[1:] + back[::-1][1:]
    f.poly(sail, PANDANUS)
    # The seams of the matting, and a shade on the back half.
    f.poly(notch + back[::-1][1:] + [(fx - reach * 0.3, fy - 40.0)], K.alpha(PANDANUS_SHADE, 0.55), body=False)
    for k in range(1, 6):
        u = k / 6.0
        a = front[int(u * (len(front) - 1))]
        b = back[int(u * (len(back) - 1))]
        f.ink([a, b], 0.9, PANDANUS_SHADE)
    for k in range(1, 4):
        u = k / 4.0
        a = notch[int(u * (len(notch) - 1))]
        f.ink([(fx, fy - 6.0), a], 0.7, PANDANUS_SHADE)
    f.limb(front, 3.6, WOOD)
    f.limb(back, 3.2, WOOD)


# ---------------------------------------------------------------------------
# The Lapita pot.
# ---------------------------------------------------------------------------


def _stamp_row(f: K.Frame, x0: float, x1: float, y: float, step: float, r: float) -> None:
    """A row of tiny square marks, as a toothed stamp leaves, filled with lime."""
    x = x0
    while x <= x1:
        f.poly([(x - r, y - r), (x + r, y - r), (x + r, y + r), (x - r, y + r)], LIME, body=False)
        x += step


def _draw_pot():
    f = K.Frame(POT_FRAME)
    cx, foot = 48.0, 90.0
    # The ring of plaited fibre it sits in.
    f.ellipse(cx, foot - 3.0, 26.0, 4.0, FIBRE)
    for k in range(9):
        x = cx - 22.0 + k * 5.5
        f.ink([(x, foot - 6.0), (x + 3.0, foot)], 0.9, FIBRE_DARK)
    # The body: round below, a sharp shoulder (the carination), a short
    # neck and a flared rim.
    body = [(cx - 14.0, foot - 4.0), (cx - 30.0, foot - 16.0), (cx - 38.0, foot - 34.0), (cx - 40.0, foot - 44.0), (cx - 30.0, foot - 54.0),
            (cx - 20.0, foot - 60.0), (cx - 22.0, foot - 70.0), (cx - 26.0, foot - 76.0), (cx + 26.0, foot - 76.0), (cx + 22.0, foot - 70.0),
            (cx + 20.0, foot - 60.0), (cx + 30.0, foot - 54.0), (cx + 40.0, foot - 44.0), (cx + 38.0, foot - 34.0), (cx + 30.0, foot - 16.0),
            (cx + 14.0, foot - 4.0)]
    f.poly(body, CLAY)
    f.poly([(cx + 14.0, foot - 4.0), (cx + 30.0, foot - 16.0), (cx + 38.0, foot - 34.0), (cx + 40.0, foot - 44.0), (cx + 24.0, foot - 40.0),
            (cx + 22.0, foot - 20.0), (cx + 8.0, foot - 5.0)], CLAY_SHADE, body=False)
    f.poly([(cx - 34.0, foot - 40.0), (cx - 28.0, foot - 50.0), (cx - 18.0, foot - 46.0), (cx - 24.0, foot - 30.0)], CLAY_LIGHT, body=False)
    # The mouth of the pot, dark inside.
    f.ellipse(cx, foot - 76.0, 25.0, 3.6, CLAY_SHADE)
    f.ellipse(cx, foot - 75.4, 21.0, 2.4, (70, 40, 28, 255), body=False)
    # The shoulder: the edge where the body turns in.
    f.ink([(cx - 40.0, foot - 44.0), (cx, foot - 46.0), (cx + 40.0, foot - 44.0)], 1.1, CLAY_SHADE)
    # The stamped bands, white with lime: a frieze of zig-zags on the
    # shoulder between two rows, arcs below, and a row on the neck.
    _stamp_row(f, cx - 18.0, cx + 18.0, foot - 66.0, 3.0, 0.7)
    _stamp_row(f, cx - 32.0, cx + 32.0, foot - 52.0, 3.0, 0.7)
    _stamp_row(f, cx - 37.0, cx + 37.0, foot - 39.0, 3.0, 0.7)
    for k in range(8):
        x0 = cx - 32.0 + k * 8.0
        for j in range(4):
            u = j / 3.0
            y = foot - 49.5 + 7.0 * (u if k % 2 == 0 else 1.0 - u)
            f.poly([(x0 + 8.0 * u - 0.7, y - 0.7), (x0 + 8.0 * u + 0.7, y - 0.7), (x0 + 8.0 * u + 0.7, y + 0.7), (x0 + 8.0 * u - 0.7, y + 0.7)], LIME,
                   body=False)
    for k in range(5):
        ax = cx - 26.0 + k * 13.0
        for j in range(7):
            a = math.pi * j / 6.0
            x, y = ax + 5.0 * math.cos(a), foot - 34.0 + 5.0 * math.sin(a)
            f.poly([(x - 0.6, y - 0.6), (x + 0.6, y - 0.6), (x + 0.6, y + 0.6), (x - 0.6, y + 0.6)], LIME, body=False)
        f.dot(ax, foot - 31.0, 0.9, LIME)
    return A.finish(f, width=1.3)


# ---------------------------------------------------------------------------
# The stilt house over the lagoon.
# ---------------------------------------------------------------------------


def _draw_stilt_house():
    w, h = STILT_FRAME
    f = K.Frame(STILT_FRAME)
    water_top, foot = 262.0, h - 6.0
    floor = 168.0
    # The posts, back row first, down into the water.
    for x in (52.0, 104.0, 152.0, 204.0):
        f.limb([(x + 6.0, floor - 2.0), (x + 8.0, foot - 4.0)], 6.0, WOOD_SHADE)
    # The lagoon round the posts: a band of clear water.
    f.poly([(8.0, water_top), (248.0, water_top), (248.0, foot), (8.0, foot)], LAGOON, body=False)
    f.poly([(8.0, water_top + 18.0), (248.0, water_top + 18.0), (248.0, foot), (8.0, foot)], LAGOON_DEEP, body=False)
    for k in range(6):
        x = 18.0 + k * 40.0
        f.ink([(x, water_top + 6.0 + (k % 2) * 8.0), (x + 18.0, water_top + 6.0 + (k % 2) * 8.0)], 1.4, LAGOON_LIGHT)
    for x in (40.0, 92.0, 140.0, 192.0, 222.0):
        f.limb([(x, floor + 4.0), (x + 2.0, foot - 2.0)], 7.0, WOOD)
        f.ink([(x - 1.6, floor + 8.0), (x - 1.0, water_top - 2.0)], 1.0, WOOD_LIGHT)
        f.ellipse(x + 1.0, water_top + 1.0, 8.0, 1.8, LAGOON_LIGHT, body=False)
    # The floor of split poles, and the platform before the door.
    f.poly([(26.0, floor - 4.0), (236.0, floor - 4.0), (236.0, floor + 6.0), (26.0, floor + 6.0)], WOOD)
    f.poly([(26.0, floor + 2.0), (236.0, floor + 2.0), (236.0, floor + 6.0), (26.0, floor + 6.0)], WOOD_SHADE, body=False)
    for k in range(14):
        x = 32.0 + k * 15.0
        f.ink([(x, floor - 3.0), (x, floor + 5.0)], 0.8, WOOD_SHADE)
    # The walls of woven panels, with a door.
    wall = [(54.0, floor - 4.0), (54.0, 100.0), (210.0, 100.0), (210.0, floor - 4.0)]
    f.poly(wall, WOVEN)
    for y in range(104, int(floor - 4), 8):
        for x in range(56, 208, 10):
            off = 5 if (y // 8) % 2 else 0
            f.ink([(x + off, y), (x + off + 5.0, y + 4.0)], 0.8, WOVEN_SHADE)
    f.poly([(116.0, floor - 4.0), (116.0, 118.0), (148.0, 118.0), (148.0, floor - 4.0)], (70, 48, 34, 255), body=False)
    f.poly([(54.0, 100.0), (210.0, 100.0), (210.0, 112.0), (54.0, 112.0)], K.alpha(WOVEN_SHADE, 0.7), body=False)
    # The roof: a steep thatched gable that comes down low over the walls,
    # with the ridge pole out past both ends.
    roof = [(28.0, 116.0), (82.0, 30.0), (182.0, 30.0), (236.0, 116.0), (220.0, 120.0), (128.0, 112.0), (44.0, 120.0)]
    f.poly(roof, THATCH)
    f.poly([(150.0, 30.0), (182.0, 30.0), (236.0, 116.0), (220.0, 120.0), (176.0, 116.0)], THATCH_SHADE, body=False)
    f.poly([(82.0, 30.0), (110.0, 30.0), (60.0, 104.0), (44.0, 112.0)], THATCH_LIGHT, body=False)
    rng = random.Random("stilt-thatch")
    for k in range(26):
        x = 40.0 + k * 7.4 + rng.uniform(-2.0, 2.0)
        # The top of the stroke is on the roof line (the gable rises from both eaves).
        top = 36.0 + max(0.0, 82.0 - x, x - 182.0) * 86.0 / 54.0
        f.ink([(x, top), (x + (x - 133.0) * 0.08, 112.0 + rng.uniform(0.0, 6.0))], 1.0, THATCH_SHADE)
    f.limb([(72.0, 26.0), (192.0, 26.0)], 6.0, WOOD)
    for x in (72.0, 192.0):
        f.limb([(x, 26.0), (x + (-1.0 if x < 100 else 1.0) * 8.0, 16.0)], 3.4, WOOD)
    # The ladder down to the water.
    for s in (0.0, 18.0):
        f.limb([(28.0 + s, floor + 4.0), (14.0 + s, water_top + 10.0)], 3.0, WOOD_LIGHT)
    for k in range(5):
        u = (k + 0.5) / 5.0
        y = floor + 4.0 + (water_top + 10.0 - floor - 4.0) * u
        x = 28.0 - 14.0 * u
        f.limb([(x, y), (x + 18.0, y)], 2.4, WOOD)
    # A small canoe tied at the front post.
    f.poly([(150.0, water_top + 4.0), (246.0, water_top + 4.0), (240.0, water_top + 12.0), (156.0, water_top + 12.0)], WOOD)
    f.poly([(150.0, water_top + 4.0), (246.0, water_top + 4.0), (244.0, water_top + 6.0), (152.0, water_top + 6.0)], WOOD_LIGHT, body=False)
    f.ink([(192.0, water_top - 30.0), (200.0, water_top + 4.0)], 1.2, ROPE_DARK)
    return A.finish(f, width=1.5)


# ---------------------------------------------------------------------------
# The outrigger canoe (a platform).
# ---------------------------------------------------------------------------


def _hull(f: K.Frame, x0: float, x1: float, top: float, depth: float, rise: float, colour, shade, light) -> None:
    """A dugout hull seen from the side: its gunwale level at `top`, its
    ends swept up by `rise`, its keel `depth` below."""
    gun = [(x0 - 4.0, top - rise), (x0 + 20.0, top - rise * 0.2), (x0 + 40.0, top), (x1 - 40.0, top), (x1 - 20.0, top - rise * 0.2),
           (x1 + 4.0, top - rise)]
    keel = [(x1 - 2.0, top - rise + 8.0), (x1 - 30.0, top + depth * 0.8), (x1 - 70.0, top + depth), (x0 + 70.0, top + depth),
            (x0 + 30.0, top + depth * 0.8), (x0 + 2.0, top - rise + 8.0)]
    f.poly(gun + keel, colour)
    f.poly([(x0 + 30.0, top + depth * 0.55), (x1 - 30.0, top + depth * 0.55)] + keel[1:5], shade, body=False)
    f.ink([(x0 + 20.0, top + 3.0), (x1 - 20.0, top + 3.0)], 1.2, light)
    # The washstrake: a plank lashed along the top of the dugout.
    f.ink([(x0 + 10.0, top + 9.0), (x1 - 10.0, top + 9.0)], 1.0, shade)
    for k in range(int((x1 - x0) // 30.0)):
        x = x0 + 24.0 + k * 30.0
        f.ink([(x, top + 6.0), (x, top + 12.0)], 1.0, ROPE_DARK)


def _draw_outrigger():
    f = K.Frame(OUTRIGGER_FRAME)
    x0, x1 = OUTRIGGER_SPAN
    top = OUTRIGGER_TOP
    # The crab-claw sail on its short mast, over the middle of the hull.
    f.limb([(206.0, top), (210.0, 40.0)], 4.0, WOOD_SHADE)
    _crab_claw_sail(f, (262.0, top - 4.0), (214.0, 12.0), 210.0, 6.0)
    f.ink([(210.0, 42.0), (262.0, top - 6.0)], 0.8, ROPE_DARK)
    # The hull: its gunwale is the platform.
    _hull(f, x0, x1, top, 30.0, 14.0, WOOD, WOOD_SHADE, WOOD_LIGHT)
    # The booms over the gunwale and the float on the near side, below,
    # joined by stanchions that slope down to it.
    fx0, fx1, fy = 96.0, 300.0, 176.0
    for bx in (126.0, 250.0):
        f.limb([(bx, top + 2.0), (bx + 6.0, fy - 6.0)], 3.0, WOOD_LIGHT)
        f.limb([(bx - 4.0, top + 1.0), (bx + 16.0, top + 4.0)], 4.0, WOOD)
        f.limb([(bx + 2.0, top + 4.0), (bx + 18.0, fy - 6.0)], 2.4, WOOD_SHADE)
        f.ellipse(bx + 2.0, top + 3.0, 3.6, 3.0, ROPE)
    f.poly([(fx0, fy - 4.0), (fx0 + 14.0, fy - 8.0), (fx1 - 14.0, fy - 8.0), (fx1, fy - 4.0), (fx1 - 10.0, fy + 3.0), (fx0 + 10.0, fy + 3.0)], WOOD_LIGHT)
    f.poly([(fx0 + 6.0, fy), (fx1 - 6.0, fy), (fx1 - 10.0, fy + 3.0), (fx0 + 10.0, fy + 3.0)], WOOD, body=False)
    # The steering paddle at the stern.
    f.limb([(x0 + 26.0, top - 18.0), (x0 + 6.0, top + 26.0)], 3.0, WOOD_SHADE)
    f.poly([(x0 + 4.0, top + 20.0), (x0 + 12.0, top + 24.0), (x0 + 4.0, top + 42.0), (x0 - 2.0, top + 34.0)], WOOD_SHADE)
    return A.finish(f, width=1.4)


# ---------------------------------------------------------------------------
# The coconut palm.
# ---------------------------------------------------------------------------


def _palm_frond(f: K.Frame, base: Point, angle: float, length: float, droop: float, colour, shade) -> None:
    """A feather leaf of a palm: an arching midrib with narrow leaflets that
    hang down from both sides."""
    a = math.radians(angle)
    pts = [base]
    x, y = base
    for k in range(10):
        u = (k + 1) / 10.0
        x += math.cos(a) * length / 10.0
        y += math.sin(a) * length / 10.0 + droop * u * length / 10.0
        pts.append((x, y))
    for k in range(1, 10):
        p0, p1 = pts[k - 1], pts[k + 1]
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        d = math.hypot(dx, dy) or 1.0
        ln = 18.0 * math.sin(math.pi * min(1.0, k / 9.0 + 0.1)) + 4.0
        for s in (-1.0, 1.0):
            # Leaflets point out and hang down.
            nx, ny = -dy / d * s, dx / d * s
            tip = (pts[k][0] + nx * ln * 0.7 + dx / d * ln * 0.5, pts[k][1] + abs(ny) * ln * 0.3 + ln * 0.75)
            f.limb([pts[k], tip], 2.6, colour if s > 0 else shade)
    f.limb(pts, 2.4, shade)


def _draw_palm(i: int, n: int):
    w, h = PALM_FRAME
    f = K.Frame(PALM_FRAME)
    foot = h - 6.0
    wind = math.sin(math.tau * i / float(n))
    # The trunk: it leans and curves, ringed with old leaf scars.
    base = (66.0, foot - 8.0)
    crown = (100.0 + 3.0 * wind, 92.0)
    trunk = _bez(base, (58.0, 200.0), crown, 16)
    for k in range(len(trunk) - 1):
        u = k / (len(trunk) - 1)
        f.limb([trunk[k], trunk[k + 1]], 15.0 - 6.0 * u, PALM_TRUNK)
    f.poly([(54.0, foot), (78.0, foot), (74.0, foot - 12.0), (58.0, foot - 12.0)], PALM_TRUNK)
    for k in range(1, len(trunk) - 1):
        u = k / (len(trunk) - 1)
        x, y = trunk[k]
        r = (15.0 - 6.0 * u) / 2.0
        f.ink([(x - r, y + 1.0), (x + r, y - 1.0)], 1.0, PALM_TRUNK_SHADE)
    f.ink([(p[0] + 3.0, p[1]) for p in trunk[2:-2]], 1.2, K.shade(PALM_TRUNK, 1.15))
    # The fronds behind, then the fronds in front.
    for ang, ln, dr in ((-150.0, 72.0, 1.4), (-30.0, 72.0, 1.4), (-100.0, 56.0, 0.7), (-75.0, 60.0, 0.9)):
        _palm_frond(f, crown, ang + 5.0 * wind, ln, dr, LEAF_SHADE, K.shade(LEAF_SHADE, 0.8))
    for ang, ln, dr in ((-172.0, 78.0, 2.2), (-8.0, 78.0, 2.2), (-130.0, 72.0, 1.3), (-50.0, 72.0, 1.3), (165.0, 60.0, 1.6), (15.0, 60.0, 1.6)):
        _palm_frond(f, crown, ang + 5.0 * wind, ln, dr, LEAF, LEAF_SHADE)
    # The coconuts in a bunch under the crown.
    for k, (dx, dy) in enumerate(((-9.0, 12.0), (1.0, 16.0), (10.0, 11.0), (-3.0, 7.0), (6.0, 5.0))):
        f.ellipse(crown[0] + dx, crown[1] + dy, 7.0, 8.0, COCONUT if k % 2 else COCONUT_BROWN)
        f.ellipse(crown[0] + dx - 2.0, crown[1] + dy - 2.6, 2.0, 2.0, K.shade(COCONUT, 1.3), body=False)
    return A.finish(f, width=1.3)


# ---------------------------------------------------------------------------
# The voyaging canoe (a platform).
# ---------------------------------------------------------------------------


def _draw_voyaging():
    f = K.Frame(VOYAGING_FRAME)
    x0, x1 = VOYAGING_SPAN
    top = VOYAGING_TOP
    # The far hull, a little higher, behind.
    _hull(f, x0 + 12.0, x1 - 4.0, top - 6.0, 34.0, 26.0, WOOD_SHADE, K.shade(WOOD_SHADE, 0.8), WOOD)
    # The mast and the crab-claw sail.
    f.limb([(240.0, top), (246.0, 48.0)], 5.0, WOOD_SHADE)
    _crab_claw_sail(f, (306.0, top - 6.0), (252.0, 12.0), 240.0, 8.0)
    f.ink([(246.0, 50.0), (306.0, top - 8.0)], 0.9, ROPE_DARK)
    f.ink([(246.0, 50.0), (402.0, top - 2.0)], 0.9, ROPE_DARK)
    # The shelter on the deck: a little house of thatch for the crew and
    # the seed plants, the pigs and the chickens.
    sx0, sx1 = 92.0, 176.0
    f.poly([(sx0, top), (sx0 + 4.0, top - 30.0), (sx1 - 4.0, top - 30.0), (sx1, top)], WOVEN)
    f.poly([(sx0 + 30.0, top), (sx0 + 30.0, top - 20.0), (sx0 + 50.0, top - 20.0), (sx0 + 50.0, top)], (70, 48, 34, 255), body=False)
    f.poly([(sx0 - 10.0, top - 26.0), (sx0 + 18.0, top - 58.0), (sx1 - 18.0, top - 58.0), (sx1 + 10.0, top - 26.0)], THATCH)
    f.poly([(sx1 - 30.0, top - 58.0), (sx1 - 18.0, top - 58.0), (sx1 + 10.0, top - 26.0), (sx1 - 10.0, top - 26.0)], THATCH_SHADE, body=False)
    for k in range(12):
        x = sx0 - 4.0 + k * 9.0
        f.ink([(x + (x - 134.0) * 0.1 * 0.3, top - 54.0), (x + (x - 134.0) * 0.12, top - 28.0)], 0.9, THATCH_SHADE)
    # A gourd of water and a bundle of plants by the shelter.
    f.ellipse(200.0, top - 8.0, 8.0, 8.0, (196, 170, 90, 255))
    f.limb([(200.0, top - 16.0), (200.0, top - 20.0)], 3.0, (150, 120, 60, 255))
    for k in range(4):
        f.limb([(214.0 + k * 3.0, top - 2.0), (210.0 + k * 6.0, top - 22.0)], 2.0, LEAF)
    # The deck of lashed poles between the hulls: its top is the platform.
    f.poly([(x0 + 24.0, top), (x1 - 24.0, top), (x1 - 24.0, top + 7.0), (x0 + 24.0, top + 7.0)], WOOD_LIGHT)
    for k in range(int((x1 - x0 - 48.0) // 14.0) + 1):
        x = x0 + 24.0 + k * 14.0
        f.ink([(x, top + 1.0), (x, top + 6.0)], 0.9, WOOD_SHADE)
    # The near hull, with its high curved ends.
    _hull(f, x0, x1, top + 6.0, 40.0, 34.0, WOOD, WOOD_SHADE, WOOD_LIGHT)
    for ex, s in ((x0 - 2.0, -1.0), (x1 + 2.0, 1.0)):
        f.limb([(ex, top - 26.0), (ex + s * 4.0, top - 40.0)], 4.0, WOOD)
    # A band painted along the near hull.
    f.ink([(x0 + 40.0, top + 22.0), (x1 - 40.0, top + 22.0)], 2.0, TAPA_RED)
    # The steering paddle at the stern.
    f.limb([(x0 + 36.0, top - 30.0), (x0 + 10.0, top + 34.0)], 3.4, WOOD_SHADE)
    f.poly([(x0 + 8.0, top + 26.0), (x0 + 18.0, top + 30.0), (x0 + 8.0, top + 52.0), (x0, top + 42.0)], WOOD_SHADE)
    return A.finish(f, width=1.5)


# ---------------------------------------------------------------------------
# The star compass.
# ---------------------------------------------------------------------------


def _draw_compass():
    w, h = COMPASS_FRAME
    f = K.Frame(COMPASS_FRAME)
    cx, cy, rx, ry = 128.0, 32.0, 112.0, 20.0
    # The patch of smoothed sand.
    f.poly(_ellipse(cx, cy + 2.0, rx + 10.0, ry + 6.0, 40), SAND)
    f.poly(_ellipse(cx, cy + 6.0, rx + 4.0, ry + 2.0, 40), K.alpha(SAND_SHADE, 0.4), body=False)
    # A line scratched across it, east to west: the path of the sun.
    f.ink([(cx - rx + 10.0, cy), (cx + rx - 10.0, cy)], 0.9, SAND_SHADE)
    # The marker stones: one for each point where a star rises or sets,
    # larger stones at the four quarters. The far half first.
    rng = random.Random("star-compass")
    stones = []
    for k in range(32):
        a = math.tau * k / 32.0
        big = k % 8 == 0
        stones.append((math.sin(a), cx + rx * math.cos(a), cy + ry * math.sin(a), big))
    for depth, x, y, big in sorted(stones):
        r = (5.4 if big else 3.6) * (0.85 + 0.15 * (depth + 1.0) / 2.0)
        colour = K.shade(STONE, rng.uniform(0.9, 1.1))
        f.poly(_ellipse(x, y - r * 0.3, r * 1.2, r * 0.8, 12), colour)
        f.poly(_ellipse(x - r * 0.3, y - r * 0.6, r * 0.5, r * 0.3, 8), STONE_LIGHT, body=False)
    # The navigator's seat in the middle: a flat stone, and a shell.
    f.poly(_ellipse(cx, cy, 10.0, 4.0, 16), STONE_SHADE)
    f.poly(_ellipse(cx + 18.0, cy + 6.0, 4.0, 2.4, 12), (246, 232, 214, 255))
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# The breadfruit tree.
# ---------------------------------------------------------------------------


def _lobed_leaf(f: K.Frame, base: Point, angle: float, size: float, colour, shade) -> None:
    """A big breadfruit leaf: long, deeply cut into pointed lobes."""
    a = math.radians(angle)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux

    def at(u: float, v: float) -> Point:
        return (base[0] + ux * u * size + nx * v * size, base[1] + uy * u * size + ny * v * size)

    lobes = [(0.3, 0.44, 0.22), (0.58, 0.42, 0.48), (0.82, 0.28, 0.72)]
    right = [at(0.0, 0.0), at(0.08, 0.1)]
    for u_tip, v_tip, u_notch in lobes:
        right += [at(u_tip - 0.06, v_tip), at(u_tip + 0.02, v_tip * 0.9), at(u_notch, 0.16)]
    right.append(at(1.0, 0.0))
    left = [at(0.08, -0.1)]
    for u_tip, v_tip, u_notch in lobes:
        left += [at(u_tip - 0.06, -v_tip), at(u_tip + 0.02, -v_tip * 0.9), at(u_notch, -0.16)]
    f.poly(right + left[::-1], colour)
    f.ink([at(0.0, 0.0), at(0.95, 0.0)], 0.9, shade)


def _draw_breadfruit(i: int, n: int):
    w, h = BREADFRUIT_FRAME
    f = K.Frame(BREADFRUIT_FRAME)
    foot = h - 6.0
    wind = math.sin(math.tau * i / float(n))
    cx = 128.0
    # The trunk and its main branches.
    f.poly([(cx - 18.0, foot), (cx + 18.0, foot), (cx + 12.0, foot - 40.0), (cx + 10.0, 150.0), (cx - 10.0, 150.0), (cx - 12.0, foot - 40.0)], WOOD)
    f.poly([(cx + 4.0, foot), (cx + 18.0, foot), (cx + 12.0, foot - 40.0), (cx + 10.0, 150.0), (cx + 4.0, 150.0)], WOOD_SHADE, body=False)
    for s in (-1.0, 1.0):
        f.poly([(cx + s * 18.0, foot), (cx + s * 34.0, foot), (cx + s * 14.0, foot - 16.0)], WOOD_SHADE)
    branches = [[(cx, 156.0), (cx - 40.0, 120.0), (cx - 70.0, 100.0)], [(cx, 156.0), (cx + 44.0, 118.0), (cx + 76.0, 104.0)],
                [(cx, 156.0), (cx - 8.0, 100.0), (cx - 20.0, 60.0)], [(cx + 2.0, 150.0), (cx + 18.0, 96.0), (cx + 30.0, 56.0)]]
    for br in branches:
        f.limb(br, 10.0, WOOD)
    # The crown: a dense round mass of foliage, dark below and lit above,
    # with big lobed leaves at its edge and on its face.
    sway = 2.0 * wind
    masses = [(cx - 66.0, 112.0, 46.0, 34.0), (cx + 66.0, 110.0, 46.0, 34.0), (cx - 30.0, 70.0, 52.0, 40.0), (cx + 32.0, 66.0, 52.0, 40.0),
              (cx, 108.0, 60.0, 40.0), (cx, 48.0, 40.0, 30.0)]
    for x, y, rx, ry in masses:
        f.poly(_ellipse(x + sway, y + 6.0, rx, ry, 28), LEAF_SHADE)
    for x, y, rx, ry in masses:
        f.poly(_ellipse(x + sway - rx * 0.12, y - ry * 0.12, rx * 0.8, ry * 0.75, 28), LEAF, body=False)
    rng = random.Random("breadfruit")
    edge = [(cx - 96.0, 118.0, 180.0), (cx - 86.0, 86.0, 205.0), (cx - 60.0, 48.0, 235.0), (cx - 18.0, 32.0, 262.0), (cx + 24.0, 32.0, 280.0),
            (cx + 64.0, 46.0, 305.0), (cx + 90.0, 84.0, 335.0), (cx + 98.0, 118.0, 0.0), (cx - 76.0, 140.0, 140.0), (cx + 80.0, 140.0, 40.0)]
    for x, y, a in edge:
        _lobed_leaf(f, (x + sway - 14.0 * math.cos(math.radians(a)), y - 14.0 * math.sin(math.radians(a))), a + 3.0 * wind, rng.uniform(28.0, 32.0),
                    LEAF_SHADE, K.shade(LEAF_SHADE, 0.75))
    for x, y, a in ((cx - 50.0, 74.0, 250.0), (cx + 40.0, 70.0, 290.0), (cx - 8.0, 98.0, 100.0), (cx + 66.0, 108.0, 60.0), (cx - 70.0, 108.0, 120.0)):
        _lobed_leaf(f, (x + sway, y), a + 3.0 * wind, rng.uniform(30.0, 36.0), LEAF_LIGHT, LEAF_SHADE)
    for x, y in ((cx - 58.0, 132.0), (cx + 60.0, 136.0), (cx - 6.0, 112.0), (cx + 30.0, 82.0), (cx - 36.0, 92.0)):
        x += 2.0 * wind
        f.ink([(x, y - 14.0), (x, y - 8.0)], 1.4, WOOD_SHADE)
        f.ellipse(x, y, 9.0, 10.0, BREADFRUIT)
        f.ellipse(x + 2.4, y + 3.0, 6.0, 6.0, BREADFRUIT_SHADE, body=False)
        for k in range(6):
            a = math.tau * k / 6.0
            f.dot(x + 5.0 * math.cos(a) - 1.0, y + 5.0 * math.sin(a) - 1.0, 0.8, K.shade(BREADFRUIT, 0.75))
    return A.finish(f, width=1.4)


# ---------------------------------------------------------------------------
# The moai on its ahu, and the walking moai.
# ---------------------------------------------------------------------------


def _moai_profile(f: K.Frame, x: float, base: float, height: float) -> Point:
    """A moai seen from the side, facing right, its base at (`x`, `base`).
    It returns the middle of the top of its head (where the pukao sits)."""
    s = height / 260.0

    def P(pts: Sequence[Point]) -> List[Point]:
        return [(x + px * s, base - py * s) for px, py in pts]

    # The back of the moai, then the face: heavy brow, long nose, pursed
    # lips, a jutting chin and the long ear.
    outline = [(-30.0, 0.0), (-34.0, 60.0), (-32.0, 120.0), (-26.0, 150.0), (-30.0, 180.0), (-30.0, 236.0), (-24.0, 252.0), (-8.0, 258.0),
               (22.0, 258.0), (32.0, 250.0), (36.0, 232.0), (34.0, 222.0), (46.0, 214.0), (52.0, 196.0), (44.0, 190.0), (40.0, 184.0),
               (44.0, 178.0), (40.0, 172.0), (42.0, 162.0), (34.0, 150.0), (30.0, 140.0), (34.0, 120.0), (36.0, 60.0), (32.0, 0.0)]
    f.poly(P(outline), TUFF)
    f.poly(P([(-30.0, 0.0), (-34.0, 60.0), (-32.0, 120.0), (-26.0, 150.0), (-30.0, 180.0), (-30.0, 236.0), (-24.0, 252.0), (-14.0, 250.0),
              (-18.0, 180.0), (-14.0, 150.0), (-18.0, 60.0), (-16.0, 0.0)]), TUFF_SHADE, body=False)
    # The deep socket under the brow (no eyes: they were set in only for a ceremony).
    f.poly(P([(20.0, 226.0), (34.0, 222.0), (32.0, 212.0), (22.0, 214.0)]), TUFF_SHADE, body=False)
    f.ink(P([(14.0, 230.0), (36.0, 230.0)]), 1.2, TUFF_SHADE)
    # The nostril, the lips, the chin.
    f.ink(P([(44.0, 196.0), (40.0, 194.0)]), 1.2, TUFF_SHADE)
    f.ink(P([(36.0, 184.0), (42.0, 182.0)]), 1.1, TUFF_SHADE)
    f.ink(P([(34.0, 176.0), (40.0, 175.0)]), 1.1, TUFF_SHADE)
    # The long ear, down the side of the head.
    f.poly(P([(-6.0, 234.0), (2.0, 236.0), (4.0, 196.0), (0.0, 182.0), (-6.0, 186.0)]), TUFF_SHADE, body=False)
    f.ink(P([(-2.0, 230.0), (0.0, 192.0)]), 1.0, TUFF)
    # The arm along the side, and the long hand over the belly.
    f.ink(P([(-10.0, 140.0), (-6.0, 90.0), (4.0, 64.0), (28.0, 58.0)]), 1.6, TUFF_SHADE)
    for k in range(4):
        f.ink(P([(10.0 + k * 5.0, 62.0), (12.0 + k * 5.0, 54.0)]), 0.9, TUFF_SHADE)
    # The light down the front, and patches of lichen.
    f.poly(P([(30.0, 140.0), (34.0, 120.0), (36.0, 60.0), (32.0, 6.0), (26.0, 6.0), (28.0, 60.0), (26.0, 120.0)]), TUFF_LIGHT, body=False)
    rng = random.Random(f"moai-lichen:{x}:{height}")
    for _ in range(9):
        px, py = rng.uniform(-24.0, 24.0), rng.uniform(10.0, 240.0)
        f.poly(P(_ellipse(px, py, rng.uniform(2.0, 5.0), rng.uniform(1.4, 3.0), 8)), K.alpha(LICHEN, 0.75), body=False)
    return P([(2.0, 258.0)])[0]


def _pukao(f: K.Frame, cx: float, top: float, width: float, height: float) -> None:
    """The red topknot of scoria, a short cylinder with a knob on top; its
    top is flat at `top`."""
    hw = width / 2.0
    f.poly([(cx - hw, top + 4.0), (cx - hw + 3.0, top), (cx + hw - 3.0, top), (cx + hw, top + 4.0), (cx + hw - 2.0, top + height),
            (cx - hw + 2.0, top + height)], SCORIA)
    f.poly([(cx + hw * 0.4, top + 2.0), (cx + hw - 3.0, top), (cx + hw, top + 4.0), (cx + hw - 2.0, top + height), (cx + hw * 0.4, top + height)],
           SCORIA_SHADE, body=False)
    f.poly([(cx - hw + 4.0, top + 3.0), (cx - hw * 0.4, top + 2.0), (cx - hw * 0.5, top + height - 3.0), (cx - hw + 4.0, top + height - 3.0)],
           SCORIA_LIGHT, body=False)
    rng = random.Random(f"pukao:{cx}:{top}")
    for _ in range(14):
        f.dot(cx + rng.uniform(-hw + 4.0, hw - 4.0), top + rng.uniform(4.0, height - 3.0), rng.uniform(0.6, 1.3), SCORIA_SHADE)


def _draw_moai():
    w, h = MOAI_FRAME
    f = K.Frame(MOAI_FRAME)
    foot = h - 6.0
    # The ahu: a long platform of fitted stones, its sea wall behind.
    ahu_top = foot - 46.0
    f.poly([(10.0, foot), (182.0, foot), (182.0, ahu_top), (10.0, ahu_top)], STONE)
    rng = random.Random("ahu")
    y = ahu_top + 4.0
    row = 0
    while y < foot - 3.0:
        rh = min(foot - y, rng.uniform(10.0, 14.0))
        x = 12.0 + (rng.uniform(4.0, 12.0) if row % 2 else 0.0)
        while x < 180.0:
            sw = min(180.0 - x, rng.uniform(18.0, 30.0))
            f.poly([(x + 1.0, y + 1.0), (x + sw - 1.0, y + 1.2), (x + sw - 1.0, y + rh - 1.0), (x + 1.0, y + rh - 1.0)],
                   K.shade(STONE, rng.uniform(0.9, 1.1)), body=False)
            x += sw
        y += rh
        row += 1
    f.poly([(10.0, ahu_top), (182.0, ahu_top), (182.0, ahu_top + 5.0), (10.0, ahu_top + 5.0)], STONE_LIGHT, body=False)
    # The moai, back to the sea (left), facing inland (right).
    head = _moai_profile(f, 92.0, ahu_top, 268.0)
    _pukao(f, head[0] + 2.0, head[1] - 38.0, 54.0, 40.0)
    return A.finish(f, width=1.5)


def _draw_walking(i: int, n: int):
    w, h = WALKING_FRAME
    f = K.Frame(WALKING_FRAME)
    foot = h - 8.0
    cx = (WALKING_SPAN[0] + WALKING_SPAN[1]) / 2.0
    pk_h = 34.0
    neck_top = WALKING_TOP + pk_h
    # The moai rocks from side to side about the middle of its pukao: its
    # base swings while the pukao stays level for whoever stands on it.
    rock = 3.2 * math.sin(math.tau * i / float(n))
    piv = (cx, neck_top)

    def R(pts: Sequence[Point]) -> List[Point]:
        return K.turn(pts, piv[0], piv[1], rock)

    # The ropes: one round the head to each side, to a team out of sight.
    # The side the moai rocks away from pulls tight; the other goes slack.
    for side in (-1.0, 1.0):
        tie = R([(cx + side * 34.0, neck_top + 116.0)])[0]
        end = (cx + side * 84.0, foot - 30.0)
        taut = max(0.0, -side * rock / 3.2)
        sag = 26.0 * (1.0 - taut) + 2.0
        rope = _bez(tie, ((tie[0] + end[0]) / 2.0, (tie[1] + end[1]) / 2.0 + sag), end)
        f.limb(rope, 3.0, ROPE)
        for k in range(1, len(rope) - 1, 2):
            f.ink([rope[k], rope[k + 1]], 0.8, ROPE_DARK)
        # The rope runs on along the ground, coiled at its end.
        f.limb([end, (end[0] + side * 2.0, foot - 6.0), (end[0] - side * 10.0, foot - 4.0)], 3.0, ROPE)
        f.poly(_ellipse(end[0] - side * 16.0, foot - 5.0, 9.0, 3.6, 14), ROPE)
        f.ink([(end[0] - side * 22.0, foot - 5.0), (end[0] - side * 10.0, foot - 5.0)], 0.8, ROPE_DARK)
    # The moai from the front: a long face, a heavy brow, a long nose, the
    # long ears, and the hands over the belly. Its base is a little rounded,
    # so it can rock on its edge.
    body = [(cx - 32.0, neck_top + 2.0), (cx + 32.0, neck_top + 2.0), (cx + 36.0, neck_top + 20.0), (cx + 38.0, neck_top + 92.0),
            (cx + 32.0, neck_top + 112.0), (cx + 44.0, neck_top + 130.0), (cx + 48.0, foot - 30.0), (cx + 44.0, foot - 4.0),
            (cx - 44.0, foot - 4.0), (cx - 48.0, foot - 30.0), (cx - 44.0, neck_top + 130.0), (cx - 32.0, neck_top + 112.0),
            (cx - 38.0, neck_top + 92.0), (cx - 36.0, neck_top + 20.0)]
    f.poly(R(body), TUFF)
    f.poly(R([(cx + 18.0, neck_top + 4.0), (cx + 32.0, neck_top + 2.0), (cx + 36.0, neck_top + 20.0), (cx + 38.0, neck_top + 92.0),
              (cx + 32.0, neck_top + 112.0), (cx + 44.0, neck_top + 130.0), (cx + 48.0, foot - 30.0), (cx + 44.0, foot - 4.0),
              (cx + 26.0, foot - 4.0), (cx + 28.0, neck_top + 130.0), (cx + 22.0, neck_top + 100.0)]), TUFF_SHADE, body=False)
    # The ears.
    for s in (-1.0, 1.0):
        f.poly(R([(cx + s * 36.0, neck_top + 26.0), (cx + s * 42.0, neck_top + 30.0), (cx + s * 42.0, neck_top + 86.0), (cx + s * 37.0, neck_top + 90.0)]),
               TUFF_SHADE)
    # The brow, the sockets under it, the nose and the lips.
    f.poly(R([(cx - 30.0, neck_top + 30.0), (cx + 30.0, neck_top + 30.0), (cx + 30.0, neck_top + 36.0), (cx - 30.0, neck_top + 36.0)]), TUFF_LIGHT,
           body=False)
    for s in (-1.0, 1.0):
        f.poly(R([(cx + s * 6.0, neck_top + 37.0), (cx + s * 26.0, neck_top + 37.0), (cx + s * 24.0, neck_top + 46.0), (cx + s * 8.0, neck_top + 46.0)]),
               TUFF_SHADE, body=False)
    f.poly(R([(cx - 4.0, neck_top + 36.0), (cx + 4.0, neck_top + 36.0), (cx + 9.0, neck_top + 74.0), (cx - 9.0, neck_top + 74.0)]), TUFF_LIGHT,
           body=False)
    f.ink(R([(cx - 9.0, neck_top + 74.0), (cx + 9.0, neck_top + 74.0)]), 1.2, TUFF_SHADE)
    f.ink(R([(cx - 12.0, neck_top + 86.0), (cx + 12.0, neck_top + 86.0)]), 1.4, TUFF_SHADE)
    f.ink(R([(cx - 10.0, neck_top + 92.0), (cx + 10.0, neck_top + 92.0)]), 1.0, TUFF_SHADE)
    # The chin and the line of the jaw.
    f.ink(R([(cx - 30.0, neck_top + 106.0), (cx, neck_top + 110.0), (cx + 30.0, neck_top + 106.0)]), 1.2, TUFF_SHADE)
    # The arms down the sides, and the long fingers that meet over the belly.
    for s in (-1.0, 1.0):
        f.ink(R([(cx + s * 40.0, neck_top + 136.0), (cx + s * 40.0, neck_top + 210.0), (cx + s * 30.0, neck_top + 236.0), (cx + s * 6.0, neck_top + 244.0)]),
              1.6, TUFF_SHADE)
        for k in range(4):
            f.ink(R([(cx + s * (8.0 + k * 5.0), neck_top + 238.0), (cx + s * (6.0 + k * 5.0), neck_top + 248.0)]), 0.9, TUFF_SHADE)
    # The ropes round the neck, where the two teams' ropes are tied.
    f.limb(R([(cx - 35.0, neck_top + 116.0), (cx, neck_top + 120.0), (cx + 35.0, neck_top + 116.0)]), 3.0, ROPE)
    rng = random.Random("walking-lichen")
    for _ in range(8):
        px, py = cx + rng.uniform(-34.0, 34.0), neck_top + rng.uniform(120.0, 260.0)
        f.poly(R(_ellipse(px, py, rng.uniform(2.0, 5.0), rng.uniform(1.4, 3.0), 8)), K.alpha(LICHEN, 0.75), body=False)
    # The pukao on top, level: its top is the platform.
    _pukao(f, cx, WALKING_TOP, WALKING_SPAN[1] - WALKING_SPAN[0], pk_h + 2.0)
    # Dust where the base scrapes the ground as it rocks.
    if abs(rock) > 2.0:
        bx = R([(cx + (44.0 if rock < 0 else -44.0), foot - 4.0)])[0][0]
        A.dust(f, bx, foot - 2.0, 10.0, 0.5, f"walking-moai:{i}", count=5)
    return A.finish(f, width=1.5)


# ---------------------------------------------------------------------------
# The rongorongo tablet.
# ---------------------------------------------------------------------------


def _glyph(f: K.Frame, x: float, y: float, s: float, rng: random.Random) -> None:
    """One made-up glyph: a little figure of strokes (a body, and arms,
    legs, a head or a curl), cut in the wood. It copies no real sign."""
    kind = rng.randrange(5)
    body = [(x, y - 3.0 * s), (x, y + 2.0 * s)]
    f.ink(body, 0.9, TABLET_MARK)
    if kind in (0, 1):
        f.ink([(x - 2.0 * s, y - 1.0 * s), (x, y - 2.0 * s), (x + 2.0 * s, y - (3.0 if kind else 0.0) * s)], 0.8, TABLET_MARK)
    if kind in (1, 2, 4):
        f.dot(x, y - 3.6 * s, 0.9 * s, TABLET_MARK)
    if kind == 3:
        f.ink([(x, y - 3.0 * s), (x + 1.6 * s, y - 4.0 * s), (x + 2.2 * s, y - 2.6 * s)], 0.8, TABLET_MARK)
    if kind in (0, 2, 3):
        f.ink([(x - 1.6 * s, y + 3.6 * s), (x, y + 2.0 * s), (x + 1.6 * s, y + 3.6 * s)], 0.8, TABLET_MARK)
    if kind == 4:
        f.ink([(x - 2.0 * s, y), (x + 2.0 * s, y)], 0.8, TABLET_MARK)


def _draw_tablet():
    w, h = TABLET_FRAME
    f = K.Frame(TABLET_FRAME)
    # A board of dark wood, a little warped, its ends rounded.
    board = [(10.0, 14.0), (20.0, 9.0), (50.0, 8.0), (78.0, 10.0), (88.0, 16.0), (88.0, 48.0), (78.0, 55.0), (48.0, 57.0), (18.0, 55.0),
             (8.0, 48.0)]
    f.poly(board, TABLET)
    f.poly([(8.0, 44.0), (88.0, 44.0), (88.0, 48.0), (78.0, 55.0), (48.0, 57.0), (18.0, 55.0), (8.0, 48.0)], TABLET_SHADE, body=False)
    f.ink([(16.0, 12.0), (76.0, 12.0)], 0.8, K.shade(TABLET, 1.3))
    # The fluted rows the signs are cut on, and the signs.
    rng = random.Random("rongorongo")
    for r in range(3):
        y = 21.0 + r * 11.0
        f.ink([(13.0, y + 6.0), (83.0, y + 6.0)], 0.6, TABLET_SHADE)
        x = 17.0
        while x < 80.0:
            _glyph(f, x, y, 1.35, rng)
            x += rng.uniform(7.4, 8.6)
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# The sweet potato.
# ---------------------------------------------------------------------------


def _kumara_leaf(f: K.Frame, x: float, y: float, s: float, angle: float, colour) -> None:
    """A sweet potato leaf: a heart with a point and two side lobes."""
    pts = [(0.0, 0.0), (-4.0, -2.0), (-7.0, -6.0), (-4.0, -8.0), (-5.0, -12.0), (0.0, -16.0), (5.0, -12.0), (4.0, -8.0), (7.0, -6.0), (4.0, -2.0)]
    f.poly(K.turn([(x + px * s, y + py * s) for px, py in pts], x, y, angle), colour)
    f.ink(K.turn([(x, y), (x, y - 13.0 * s)], x, y, angle), 0.6, LEAF_SHADE)


def _draw_kumara():
    w, h = KUMARA_FRAME
    f = K.Frame(KUMARA_FRAME)
    foot = h - 6.0
    # The mound of earth the slips are planted in.
    f.poly([(6.0, foot), (22.0, foot - 18.0), (64.0, foot - 26.0), (104.0, foot - 18.0), (122.0, foot)], SOIL)
    f.poly([(10.0, foot), (118.0, foot), (112.0, foot - 5.0), (16.0, foot - 5.0)], SOIL_DARK, body=False)
    # The vines over the mound, with their leaves.
    rng = random.Random("kumara")
    vines = [[(56.0, foot - 24.0), (36.0, foot - 32.0), (14.0, foot - 14.0)], [(60.0, foot - 26.0), (82.0, foot - 34.0), (108.0, foot - 20.0)],
             [(58.0, foot - 26.0), (46.0, foot - 40.0), (30.0, foot - 36.0)], [(62.0, foot - 26.0), (70.0, foot - 42.0), (88.0, foot - 40.0)]]
    for v in vines:
        f.limb(_bez(v[0], v[1], v[2], 8), 1.6, (110, 130, 70, 255))
    for v in vines:
        for u in (0.35, 0.65, 1.0):
            p = _bez(v[0], v[1], v[2], 8)[int(u * 8)]
            _kumara_leaf(f, p[0], p[1], rng.uniform(0.9, 1.15), rng.uniform(-40.0, 40.0), LEAF if rng.random() < 0.5 else LEAF_LIGHT)
    # A pale purple flower like a little morning glory.
    f.poly(_ellipse(64.0, foot - 46.0, 4.0, 3.0, 10), (210, 170, 220, 255))
    f.dot(64.0, foot - 46.0, 1.0, (130, 70, 140, 255))
    # The dug tuber, on the earth at the front: red-purple skin, orange inside.
    tx, ty = 92.0, foot - 8.0
    tuber = [(tx - 20.0, ty + 2.0), (tx - 14.0, ty - 6.0), (tx, ty - 9.0), (tx + 14.0, ty - 6.0), (tx + 22.0, ty), (tx + 12.0, ty + 5.0),
             (tx - 8.0, ty + 6.0)]
    f.poly(tuber, KUMARA_SKIN)
    f.poly([(tx - 12.0, ty + 3.0), (tx + 12.0, ty + 1.0), (tx + 12.0, ty + 5.0), (tx - 8.0, ty + 6.0)], KUMARA_SHADE, body=False)
    f.ellipse(tx + 19.0, ty - 1.0, 3.0, 3.4, KUMARA_FLESH, body=False)
    f.ink([(tx - 20.0, ty + 2.0), (tx - 27.0, ty - 2.0)], 1.0, KUMARA_SHADE)
    for k in range(3):
        f.dot(tx - 8.0 + k * 8.0, ty - 3.0 + (k % 2) * 3.0, 0.7, KUMARA_SHADE)
    return A.finish(f, width=1.2)


TARGETS: Dict[str, dict] = {
    "history_lapita_pot": _publisher("history_lapita_pot", "Lapita Pot", STILL, POT_FRAME, lambda anim, i, n: _draw_pot(),
                                     {"foot": (48.0, 96.0)}, "Scenery", SCENERY),
    "history_stilt_house": _publisher("history_stilt_house", "Stilt House", STILL, STILT_FRAME, lambda anim, i, n: _draw_stilt_house(),
                                      {"foot": (128.0, 320.0)}, "Scenery", SCENERY),
    "history_outrigger_canoe": _publisher("history_outrigger_canoe", "Outrigger Canoe", STILL, OUTRIGGER_FRAME, lambda anim, i, n: _draw_outrigger(),
                                          {"top": ((OUTRIGGER_SPAN[0] + OUTRIGGER_SPAN[1]) / 2.0, OUTRIGGER_TOP)}, "Scenery", PLATFORM),
    "history_coconut_palm": _publisher("history_coconut_palm", "Coconut Palm", SWAY, PALM_FRAME, lambda anim, i, n: _draw_palm(i, n),
                                       {"foot": (66.0, 384.0)}, "Scenery", SCENERY),
    "history_voyaging_canoe": _publisher("history_voyaging_canoe", "Voyaging Canoe", STILL, VOYAGING_FRAME, lambda anim, i, n: _draw_voyaging(),
                                         {"top": ((VOYAGING_SPAN[0] + VOYAGING_SPAN[1]) / 2.0, VOYAGING_TOP)}, "Scenery", PLATFORM),
    "history_star_compass": _publisher("history_star_compass", "Star Compass", STILL, COMPASS_FRAME, lambda anim, i, n: _draw_compass(),
                                       {"foot": (128.0, 64.0)}, "Scenery", SCENERY),
    "history_breadfruit_tree": _publisher("history_breadfruit_tree", "Breadfruit Tree", SWAY, BREADFRUIT_FRAME,
                                          lambda anim, i, n: _draw_breadfruit(i, n), {"foot": (128.0, 320.0)}, "Scenery", SCENERY),
    "history_moai": _publisher("history_moai", "Moai", STILL, MOAI_FRAME, lambda anim, i, n: _draw_moai(), {"foot": (96.0, 384.0)}, "Scenery", SCENERY),
    "history_walking_moai": _publisher("history_walking_moai", "Walking Moai", ROCK, WALKING_FRAME, lambda anim, i, n: _draw_walking(i, n),
                                       {"top": ((WALKING_SPAN[0] + WALKING_SPAN[1]) / 2.0, WALKING_TOP)}, "Scenery", PLATFORM),
    "history_rongorongo_tablet": _publisher("history_rongorongo_tablet", "Rongorongo Tablet", STILL, TABLET_FRAME, lambda anim, i, n: _draw_tablet(),
                                            {"foot": (48.0, 64.0)}, "Scenery", SCENERY),
    "history_kumara": _publisher("history_kumara", "Sweet Potato", STILL, KUMARA_FRAME, lambda anim, i, n: _draw_kumara(),
                                 {"foot": (64.0, 96.0)}, "Scenery", SCENERY),
}

#: The drawing of each target, by its row (for previews).
DRAW = {
    "history_lapita_pot": lambda anim, i, n: _draw_pot(),
    "history_stilt_house": lambda anim, i, n: _draw_stilt_house(),
    "history_outrigger_canoe": lambda anim, i, n: _draw_outrigger(),
    "history_coconut_palm": lambda anim, i, n: _draw_palm(i, n),
    "history_voyaging_canoe": lambda anim, i, n: _draw_voyaging(),
    "history_star_compass": lambda anim, i, n: _draw_compass(),
    "history_breadfruit_tree": lambda anim, i, n: _draw_breadfruit(i, n),
    "history_moai": lambda anim, i, n: _draw_moai(),
    "history_walking_moai": lambda anim, i, n: _draw_walking(i, n),
    "history_rongorongo_tablet": lambda anim, i, n: _draw_tablet(),
    "history_kumara": lambda anim, i, n: _draw_kumara(),
}
