"""The props of South America (the History dimension): the Andes and Caral.

In the high Andes near Lake Titicaca, people began to farm the potato
about 8,000 years ago, and in time they bred thousands of kinds of it, of
many colours. They also learned to keep potatoes for years as chuno: they
spread the potatoes on the ground for the frost of the night and the sun of
the day, and they trod the water out of them, so that the potatoes became
light, dry and hard.

On the coast of Peru, in the Supe valley, the people of Caral built a city
of stone platforms and sunken round plazas about 2600 BCE, as early as the
pyramids of Egypt. They had no pottery yet. They grew cotton in the valley
and made it into fishing nets, and the people of the coast paid for the
nets with anchovies. The builders filled their walls with shicra: bags of
twisted reed full of stones. A knotted cord found at Caral may be the
oldest quipu, the record of knots that the Andes used for thousands of
years after.

These props are drawn in the cel style of the dimension's cast
(`targets/characters/_history_americas_kit.py`): flat colour, one shade, a
bold warm outline. They show the skill of the people who made them.

- ``history_potatoes``: scenery, a heap of potatoes of many colours,
  shapes and sizes, and a wooden digging stick that leans on the heap.
- ``history_chuno``: scenery, potatoes spread on a bed of straw on the
  ground to freeze and dry: some pale with frost, some dark and shrunken.
- ``history_quipu``: scenery, a knotted-cord record: a top cord with many
  pendant cords of cotton in natural colours, with knots, tied to the
  crosspiece of a wooden stake.
- ``history_shicra_bags``: scenery, a pile of open-mesh bags of twisted
  reed, each full of stones.
- ``history_cotton_nets``: scenery, cotton fishing nets that hang to dry
  on a rope between poles, with gourd floats. Its ``idle`` row moves the
  nets a little in the wind.

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
LOOP: List[Tuple[str, int, int]] = [("idle", 8, 140)]

POTATOES_FRAME = (128, 64)
CHUNO_FRAME = (192, 64)
QUIPU_FRAME = (96, 128)
SHICRA_FRAME = (128, 96)
NETS_FRAME = (192, 160)

#: The kinds of potato of the heap: (skin, shade, light).
POTATO_KINDS: Dict[str, Tuple[RGBA, RGBA, RGBA]] = {
    "purple": ((112, 62, 118, 255), (76, 40, 84, 255), (150, 100, 156, 255)),
    "red": ((176, 56, 52, 255), (124, 36, 36, 255), (214, 104, 92, 255)),
    "yellow": ((224, 186, 84, 255), (174, 136, 52, 255), (246, 220, 140, 255)),
    "white": ((230, 218, 186, 255), (186, 170, 136, 255), (248, 242, 222, 255)),
    "tan": ((176, 128, 82, 255), (128, 88, 54, 255), (210, 166, 118, 255)),
    "pink": ((210, 120, 126, 255), (160, 80, 90, 255), (236, 166, 166, 255)),
    "blue": ((70, 60, 96, 255), (46, 38, 66, 255), (110, 100, 140, 255)),
}
FROST = ((224, 230, 238, 255), (176, 186, 202, 255), (252, 252, 255, 255))
SHRUNK = ((86, 64, 56, 255), (56, 40, 36, 255), (122, 98, 86, 255))

WOOD = (138, 94, 58, 255)
WOOD_LIGHT = (178, 132, 86, 255)
WOOD_DARK = (88, 58, 36, 255)
STRAW = (210, 178, 98, 255)
STRAW_LIGHT = (238, 214, 140, 255)
STRAW_SHADE = (156, 124, 62, 255)
EARTH = (132, 104, 78, 255)
EARTH_SHADE = (96, 74, 56, 255)
COTTON = (238, 230, 210, 255)
COTTON_SHADE = (196, 184, 160, 255)
COTTON_TAN = (204, 168, 116, 255)
COTTON_BROWN = (150, 102, 68, 255)
COTTON_DARK = (100, 68, 48, 255)
REED = (178, 160, 92, 255)
REED_LIGHT = (214, 198, 128, 255)
REED_SHADE = (126, 110, 58, 255)
STONE = (168, 156, 136, 255)
STONE_LIGHT = (204, 194, 174, 255)
STONE_SHADE = (120, 110, 96, 255)
GAP = (70, 58, 48, 255)
GOURD = (214, 176, 98, 255)
GOURD_LIGHT = (240, 212, 140, 255)
GOURD_SHADE = (164, 126, 64, 255)
GLINT = (255, 255, 255, 255)


def _phase(i: int, n: int) -> float:
    return i / float(max(1, n))


def _lumpy(cx: float, cy: float, rx: float, ry: float, rng: random.Random, lumps: float = 0.10, count: int = 18) -> List[Point]:
    """An oval with small bumps on its edge, as a potato or a stone has."""
    phase = rng.uniform(0.0, math.tau)
    k = rng.choice((2, 3, 4))
    pts = []
    for j in range(count):
        a = math.tau * j / count
        r = 1.0 + lumps * math.sin(a * k + phase) + rng.uniform(-lumps, lumps) * 0.5
        pts.append((cx + rx * r * math.cos(a), cy + ry * r * math.sin(a)))
    return pts


def _potato(f: K.Frame, cx: float, cy: float, rx: float, ry: float, colours: Tuple[RGBA, RGBA, RGBA], rng: random.Random,
            wrinkled: bool = False, frosted: bool = False) -> None:
    """One potato: a lumpy oval with a shade on its lower side, a light on
    its upper side, and a few eyes. A shrunken potato has wrinkles; a frosted
    one has glints of frost."""
    skin, shade, light = colours
    f.poly(_lumpy(cx, cy, rx, ry, rng, 0.16 if wrinkled else 0.09), skin)
    f.poly(_lumpy(cx + rx * 0.18, cy + ry * 0.30, rx * 0.78, ry * 0.62, rng, 0.05), shade, body=False)
    f.ellipse(cx - rx * 0.35, cy - ry * 0.40, rx * 0.30, ry * 0.20, light, body=False)
    if wrinkled:
        for _ in range(3):
            x = cx + rng.uniform(-0.6, 0.5) * rx
            f.ink([(x, cy - ry * 0.5), (x + rx * 0.2, cy), (x + rx * 0.05, cy + ry * 0.5)], 0.6, K.shade(shade, 1.3))
    else:
        for _ in range(2 if rx < 7.0 else 3):
            a = rng.uniform(0.0, math.tau)
            f.dot(cx + math.cos(a) * rx * 0.55, cy + math.sin(a) * ry * 0.5, 0.6, K.shade(shade, 1.35))
    if frosted:
        for _ in range(3):
            gx, gy = cx + rng.uniform(-0.6, 0.6) * rx, cy + rng.uniform(-0.6, 0.2) * ry
            f.ink([(gx - 1.2, gy), (gx + 1.2, gy)], 0.4, GLINT)
            f.ink([(gx, gy - 1.2), (gx, gy + 1.2)], 0.4, GLINT)


# ---------------------------------------------------------------------------
# The heap of potatoes.
# ---------------------------------------------------------------------------


def _draw_potatoes(anim: str, i: int, n: int):
    w, h = POTATOES_FRAME
    f = K.Frame(POTATOES_FRAME)
    rng = random.Random("history_potatoes")
    ground = h - 6.0
    kinds = list(POTATO_KINDS)
    # The digging stick: a straight pole of hard wood with a point that was
    # hardened in the fire. It leans on the heap, its point on the ground.
    f.limb([(56.0, ground - 1.0), (120.0, 12.0)], 3.6, WOOD)
    f.ink([(60.0, ground - 3.0), (118.0, 13.0)], 0.8, WOOD_LIGHT)
    f.poly([(53.0, ground + 0.4), (57.0, ground - 6.0), (60.6, ground - 4.6)], WOOD_DARK)
    # The heap: a wide bottom row of big and small potatoes, and smaller rows
    # on top of it. Each potato has its own kind, size and shape.
    rows = [(ground - 6.0, 10, 14.0, 106.0, (6.0, 10.0)), (ground - 14.0, 7, 26.0, 94.0, (5.5, 9.0)),
            (ground - 21.0, 5, 36.0, 82.0, (5.0, 8.0)), (ground - 27.5, 3, 46.0, 72.0, (4.5, 7.0))]
    k = 0
    for y, count, x0, x1, (rmin, rmax) in rows:
        for j in range(count):
            x = x0 + (x1 - x0) * j / max(1, count - 1) + rng.uniform(-2.0, 2.0)
            rx = rng.uniform(rmin, rmax)
            ry = rx * rng.uniform(0.62, 0.8)
            _potato(f, x, y + rng.uniform(-1.0, 1.0) + (6.0 - ry) * 0.4, rx, ry, POTATO_KINDS[kinds[(k * 3 + j) % len(kinds)]], rng)
            k += 1
    # Two long finger potatoes and a small knobbly one in front of the heap.
    _potato(f, 30.0, ground - 2.5, 9.0, 3.4, POTATO_KINDS["yellow"], rng)
    _potato(f, 92.0, ground - 2.6, 8.0, 3.2, POTATO_KINDS["purple"], rng)
    _potato(f, 64.0, ground - 2.8, 4.0, 3.2, POTATO_KINDS["red"], rng)
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# Chuno on its bed of straw.
# ---------------------------------------------------------------------------


def _draw_chuno(anim: str, i: int, n: int):
    w, h = CHUNO_FRAME
    f = K.Frame(CHUNO_FRAME)
    rng = random.Random("history_chuno")
    ground = h - 6.0
    # The bed: a low, wide layer of ichu straw on the cold ground. It is
    # thickest in the middle and thin at its ends, and its edges are ragged
    # where the stalks stick out.
    top = []
    for j in range(33):
        u = j / 32.0
        x = 8.0 + (w - 16.0) * u
        top.append((x, ground - 2.0 - 9.0 * math.sin(math.pi * u) ** 0.4 - rng.uniform(0.0, 1.8)))
    f.poly([(6.0, ground)] + top + [(w - 6.0, ground)], STRAW)
    f.poly([(10.0, ground)] + [(x, ground - (ground - y) * 0.35) for x, y in top[1:-1]] + [(w - 10.0, ground)], STRAW_SHADE, body=False)
    for _ in range(140):
        x = rng.uniform(10.0, w - 10.0)
        u = (x - 8.0) / (w - 16.0)
        y = ground - rng.uniform(1.0, 9.0 * math.sin(math.pi * u) ** 0.4 + 1.0)
        lean = rng.uniform(-7.0, 7.0)
        f.ink([(x, y), (x + lean, y + rng.uniform(-1.2, 1.2))], 0.5, STRAW_LIGHT if rng.random() < 0.55 else STRAW_SHADE)
    for k in range(14):
        x, y = top[1 + k * 30 // 13]
        f.limb([(x, y + 2.0), (x + rng.uniform(-7.0, 7.0), y - rng.uniform(2.0, 4.0))], 0.8, STRAW)
    # The potatoes in one layer on the bed, apart from each other, in two
    # rows. The fresh ones are pale with the frost of the night, and their
    # own colour shows through the frost. The ones that were trodden and
    # dried are dark and shrunken.
    tints = list(POTATO_KINDS.values())
    for row, (lift, start) in enumerate(((6.0, 24.0), (1.0, 16.0))):
        x = start
        k = row
        while x < w - 18.0:
            u = (x - 8.0) / (w - 16.0)
            rx = rng.uniform(4.4, 6.2)
            dark = k % 3 == 1 or rng.random() < 0.2
            y = ground - 3.0 - lift - 5.0 * math.sin(math.pi * u) ** 0.4 + rng.uniform(-0.6, 0.6)
            if dark:
                _potato(f, x, y, rx * 0.85, rx * 0.55, SHRUNK, rng, wrinkled=True)
            else:
                skin = tints[k % len(tints)][0]
                frost = tuple(int(a * 0.7 + b * 0.3) for a, b in zip(FROST[0][:3], skin[:3])) + (255,)
                shade = tuple(int(a * 0.6 + b * 0.4) for a, b in zip(FROST[1][:3], skin[:3])) + (255,)
                _potato(f, x, y, rx, rx * 0.74, (frost, shade, FROST[2]), rng, frosted=True)
            x += rx * 2.0 + rng.uniform(5.0, 9.0)
            k += 1
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# The quipu.
# ---------------------------------------------------------------------------


def _draw_quipu(anim: str, i: int, n: int):
    w, h = QUIPU_FRAME
    f = K.Frame(QUIPU_FRAME)
    rng = random.Random("history_quipu")
    ground = h - 6.0
    sx = w / 2.0
    bar = 22.0
    # The stake, set in a small mound of earth, and its crosspiece, tied on
    # with cord.
    f.poly([(sx - 15.0, ground), (sx - 9.0, ground - 4.0), (sx, ground - 5.4), (sx + 9.0, ground - 4.0), (sx + 15.0, ground)], EARTH)
    f.poly([(sx + 2.0, ground), (sx + 9.0, ground - 3.0), (sx + 15.0, ground)], EARTH_SHADE, body=False)
    f.limb([(sx, ground - 1.0), (sx, 14.0)], 4.6, WOOD)
    f.ink([(sx - 1.0, ground - 4.0), (sx - 1.0, 16.0)], 0.8, WOOD_LIGHT)
    f.limb([(10.0, bar), (w - 10.0, bar - 1.0)], 3.4, WOOD)
    f.ink([(11.0, bar - 1.0), (w - 11.0, bar - 2.0)], 0.7, WOOD_LIGHT)
    for d in (-1.6, 0.0, 1.6):
        f.ink([(sx - 3.0, bar - 3.0 + d), (sx + 3.0, bar + 2.0 + d)], 0.7, COTTON_BROWN)
    # The top cord: tied to the crosspiece at its two ends and in the middle,
    # so that it hangs in two shallow loops.
    top = []
    for j in range(31):
        u = j / 30.0
        x = 14.0 + (w - 28.0) * u
        top.append((x, bar + 4.0 + 3.0 * math.sin(math.pi * ((u * 2.0) % 1.0))))
    for x, y in (top[0], top[15], top[30]):
        f.ink([(x, bar), (x, y)], 1.0, COTTON_TAN)
    f.limb(top, 1.8, COTTON_TAN)
    # The pendant cords. Each hangs from the top cord; its colour and its
    # knots carry the record: single knots for tens and hundreds high up,
    # and long knots for the units low down. Some cords carry a short
    # subsidiary cord.
    colours = [COTTON, COTTON_TAN, COTTON, COTTON_BROWN, COTTON, COTTON_TAN, COTTON, COTTON_DARK, COTTON_TAN, COTTON, COTTON_BROWN, COTTON]
    count = len(colours)
    for k, colour in enumerate(colours):
        x0, y0 = top[1 + k * 28 // (count - 1)] if k < count - 1 else top[29]
        length = rng.uniform(62.0, 86.0)
        sway = rng.uniform(-1.6, 1.6)
        cord = [(x0, y0), (x0 + sway * 0.4, y0 + length * 0.5), (x0 + sway, y0 + length)]
        f.limb(cord, 2.0, colour)

        def at(u: float) -> Point:
            return (x0 + sway * u, y0 + length * u)

        knot = K.shade(colour, 1.3)
        # Hundreds and tens: single knots in two bands.
        for band, top_u in ((0.18, 0.18), (0.42, 0.42)):
            for m in range(rng.randint(0, 4)):
                px, py = at(top_u + m * 0.035)
                f.ellipse(px, py, 2.2, 1.6, knot)
        # Units: one long knot of several turns.
        turns = rng.randint(2, 7)
        px, py = at(0.72)
        f.ellipse(px, py, 2.3, 1.2 + turns * 0.6, knot)
        for m in range(turns):
            f.ink([(px - 1.4, py - turns * 0.5 + m * 1.0), (px + 1.4, py - turns * 0.5 + m * 1.0 + 0.6)], 0.4, K.shade(colour, 1.6))
        # The frayed end of the cord.
        ex, ey = at(1.0)
        for d in (-1.0, 0.0, 1.0):
            f.ink([(ex, ey - 1.0), (ex + d, ey + 2.4)], 0.5, colour)
        if k % 4 == 2:
            sx0, sy0 = at(0.30)
            f.limb([(sx0, sy0), (sx0 + 3.0, sy0 + 10.0), (sx0 + 3.6, sy0 + 22.0)], 1.0, COTTON_SHADE)
            f.ellipse(sx0 + 3.4, sy0 + 16.0, 1.3, 1.1, K.shade(COTTON_SHADE, 1.25))
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# The shicra bags.
# ---------------------------------------------------------------------------


def _shicra(f: K.Frame, cx: float, cy: float, rx: float, ry: float, rng: random.Random) -> None:
    """One shicra: an open-mesh bag of twisted reed, full of stones, with
    its mouth tied shut on top. The stones show through the mesh."""
    f.poly(_lumpy(cx, cy, rx, ry, rng, 0.06), GAP)
    # The stones inside: packed close, each with its own tone and a light.
    for _ in range(int(rx * ry / 9.0)):
        a = rng.uniform(0.0, math.tau)
        d = math.sqrt(rng.uniform(0.0, 1.0)) * 0.78
        sr = rng.uniform(2.6, 4.6)
        x, y = cx + math.cos(a) * d * (rx - sr * 0.6), cy + math.sin(a) * d * (ry - sr * 0.6)
        tone = rng.uniform(-0.12, 0.12)
        stone = tuple(max(0, min(255, int(c * (1.0 + tone)))) for c in STONE[:3]) + (255,)
        f.poly(_lumpy(x, y, sr, sr * 0.8, rng, 0.12, 10), stone, body=False)
        f.ellipse(x - sr * 0.3, y - sr * 0.35, sr * 0.35, sr * 0.22, STONE_LIGHT, body=False)
    f.poly(_lumpy(cx + rx * 0.2, cy + ry * 0.45, rx * 0.75, ry * 0.45, rng, 0.04), K.alpha(STONE_SHADE, 0.45), body=False)
    # The mesh: cords from the knot on top down round the bag, and rows of
    # cord across it, twisted, with the light on each turn.
    tx, ty = cx + rng.uniform(-2.0, 2.0), cy - ry - 3.0
    for s in (-0.85, -0.55, -0.25, 0.05, 0.35, 0.65, 0.92):
        pts = [(cx + rx * s * math.sin(math.pi * u), cy - ry * math.cos(math.pi * u)) for u in [j / 10.0 for j in range(1, 11)]]
        f.ink([(tx, ty + 2.0)] + pts, 0.9, REED)
    for v in (-0.45, -0.05, 0.35, 0.72):
        half = math.sqrt(max(0.0, 1.0 - v * v))
        pts = [(cx + rx * half * math.cos(a), cy + ry * v + ry * 0.12 * half * math.sin(a)) for a in [math.pi * j / 12.0 for j in range(13)]]
        f.ink(pts, 0.9, REED)
        for x, y in pts[1:-1:2]:
            f.dot(x, y, 0.5, REED_LIGHT)
    # The mouth of the bag, tied shut, and the tail of the knot.
    f.poly([(tx - 4.0, ty + 3.0), (tx + 4.0, ty + 3.0), (tx + 2.0, ty - 1.0), (tx - 2.0, ty - 1.0)], REED)
    f.limb([(tx - 1.0, ty - 1.0), (tx - 3.0, ty - 5.0)], 1.4, REED_SHADE)
    f.limb([(tx + 1.0, ty - 1.0), (tx + 4.0, ty - 4.0)], 1.4, REED)


def _draw_shicra(anim: str, i: int, n: int):
    w, h = SHICRA_FRAME
    f = K.Frame(SHICRA_FRAME)
    rng = random.Random("history_shicra_bags")
    ground = h - 6.0
    # A pile of six bags: three on the ground, two on them, one on top.
    for cx, cy, rx, ry in ((26.0, ground - 13.0, 18.0, 13.0), (64.0, ground - 14.0, 19.0, 14.0), (102.0, ground - 13.0, 18.0, 13.0),
                           (45.0, ground - 36.0, 17.0, 12.5), (84.0, ground - 36.0, 17.0, 12.5), (64.0, ground - 57.0, 16.0, 12.0)):
        _shicra(f, cx, cy, rx, ry, rng)
    # Two loose stones on the ground beside the pile.
    for x, r in ((8.0, 2.6), (120.0, 3.0)):
        f.poly(_lumpy(x, ground - r * 0.7, r, r * 0.75, rng, 0.12, 10), STONE)
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# The cotton nets.
# ---------------------------------------------------------------------------


def _gourd(f: K.Frame, x: float, y: float, r: float) -> None:
    """A gourd float: a small round dry gourd, tied on by its neck."""
    f.ellipse(x, y + r * 0.2, r, r * 0.9, GOURD)
    f.ellipse(x + r * 0.25, y + r * 0.45, r * 0.65, r * 0.5, GOURD_SHADE, body=False)
    f.ellipse(x - r * 0.35, y - r * 0.15, r * 0.3, r * 0.22, GOURD_LIGHT, body=False)
    f.limb([(x, y - r * 0.6), (x + 0.6, y - r * 1.2)], r * 0.45, GOURD_SHADE)


def _net(f: K.Frame, x0: float, x1: float, top: Sequence[Point], drop: float, sway: float, rng: random.Random) -> None:
    """One net that hangs over the rope from `x0` to `x1`. `top` is the line
    of the rope; the net hangs `drop` below it, its foot ragged, and the
    wind moves its foot by `sway`. The mesh is a grid of diamonds."""

    def rope_y(x: float) -> float:
        for (ax, ay), (bx, by) in zip(top, top[1:]):
            if ax <= x <= bx:
                return ay + (by - ay) * (x - ax) / max(1e-6, bx - ax)
        return top[-1][1]

    cols = 14
    xs = [x0 + (x1 - x0) * j / cols for j in range(cols + 1)]
    feet = [drop * (0.82 + 0.18 * math.sin(math.pi * j / cols)) + rng.uniform(-2.0, 2.0) for j in range(cols + 1)]

    def point(j: float, v: float) -> Point:
        """A point of the net: column `j`, `v` of the way down."""
        j0 = min(cols - 1, int(j))
        u = j - j0
        x = xs[j0] + (xs[j0 + 1] - xs[j0]) * u
        foot = feet[j0] + (feet[j0 + 1] - feet[j0]) * u
        return (x + sway * v * v, rope_y(x) + foot * v)

    outline = [point(j / 2.0, 0.0) for j in range(2 * cols + 1)] + [point(j / 2.0, 1.0) for j in range(2 * cols, -1, -1)]
    f.poly(outline, K.alpha(COTTON_SHADE, 0.28), body=False)
    # The diamonds: lines that go down to the left and down to the right.
    rows = 9
    for k in range(-rows, cols + 1):
        for s in (1.0, -1.0):
            pts = []
            for r in range(rows + 1):
                j = k + r * 0.5 if s > 0 else (cols - k) - r * 0.5
                if 0.0 <= j <= cols:
                    pts.append(point(j, r / rows))
            if len(pts) > 1:
                f.ink(pts, 0.7, COTTON)
    # The heavy cords at its edges.
    f.ink([point(j / 2.0, 1.0) for j in range(2 * cols + 1)], 1.1, COTTON_SHADE)
    f.ink([point(0.0, v / 8.0) for v in range(9)], 1.1, COTTON_SHADE)
    f.ink([point(float(cols), v / 8.0) for v in range(9)], 1.1, COTTON_SHADE)


def _draw_nets(anim: str, i: int, n: int):
    w, h = NETS_FRAME
    f = K.Frame(NETS_FRAME)
    t = _phase(i, n)
    cyc = math.tau * t
    rng = random.Random("history_cotton_nets")
    ground = h - 6.0
    poles = [(18.0, 22.0), (96.0, 16.0), (174.0, 22.0)]
    # The poles: straight trunks of huarango wood, set in the ground.
    for x, top_y in poles:
        f.limb([(x, ground), (x, top_y)], 4.4, WOOD)
        f.ink([(x - 1.0, ground - 2.0), (x - 1.0, top_y + 2.0)], 0.8, WOOD_LIGHT)
        f.ellipse(x, ground, 6.0, 1.8, WOOD_DARK)
    # The rope between the pole tops, in two slack spans.
    rope: List[Point] = []
    for (ax, ay), (bx, by) in zip(poles, poles[1:]):
        for j in range(13):
            u = j / 12.0
            rope.append((ax + (bx - ax) * u, ay + 3.0 + (by - ay) * u + 6.0 * math.sin(math.pi * u)))
    # Two nets hang over the rope, one in each span; the wind moves them.
    _net(f, 22.0, 92.0, rope, 98.0, 3.0 * math.sin(cyc), rng)
    _net(f, 100.0, 170.0, rope, 86.0, 3.0 * math.sin(cyc + 0.9), rng)
    f.limb(rope, 1.6, COTTON_TAN)
    for x, top_y in poles:
        f.ink([(x - 3.0, top_y + 2.0), (x + 3.0, top_y + 5.0)], 1.0, COTTON_TAN)
    # The floats: gourds tied along the rope, the line that keeps the top of
    # a net at the surface of the sea.
    for k, x in enumerate((34.0, 52.0, 70.0, 88.0, 112.0, 130.0, 148.0, 164.0)):
        j = min(range(len(rope)), key=lambda q: abs(rope[q][0] - x))
        bob = 0.8 * math.sin(cyc + k)
        _gourd(f, x + bob, rope[j][1] + 5.0, 3.6 if k % 3 else 4.2)
    # A small pile of spare gourds and a coil of cord at the foot of a pole.
    for x, y, r in ((30.0, ground - 4.0, 4.4), (40.0, ground - 4.0, 4.0), (35.0, ground - 10.0, 3.8)):
        _gourd(f, x, y, r)
    f.ellipse(150.0, ground - 2.0, 10.0, 3.0, COTTON_TAN)
    f.ellipse(150.0, ground - 2.6, 6.0, 1.6, K.shade(COTTON_TAN, 1.3), body=False)
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# Publication.
# ---------------------------------------------------------------------------

SCENERY = ["prop", "scenery", "history", "americas"]

FRAMES: Dict[str, Tuple[int, int]] = {
    "history_potatoes": POTATOES_FRAME,
    "history_chuno": CHUNO_FRAME,
    "history_quipu": QUIPU_FRAME,
    "history_shicra_bags": SHICRA_FRAME,
    "history_cotton_nets": NETS_FRAME,
}
DRAW: Dict[str, Callable] = {
    "history_potatoes": _draw_potatoes,
    "history_chuno": _draw_chuno,
    "history_quipu": _draw_quipu,
    "history_shicra_bags": _draw_shicra,
    "history_cotton_nets": _draw_nets,
}
DISPLAY = {
    "history_potatoes": "Potatoes",
    "history_chuno": "Chuno",
    "history_quipu": "Quipu",
    "history_shicra_bags": "Shicra Bags",
    "history_cotton_nets": "Cotton Nets",
}
ROWS = {"history_cotton_nets": LOOP}


def _foot(name: str) -> Dict[str, Tuple[float, float]]:
    w, h = FRAMES[name]
    return {"foot": (w / 2.0, float(h))}


TARGETS: Dict[str, dict] = {
    name: _publisher(name, DISPLAY[name], ROWS.get(name, STILL), FRAMES[name], DRAW[name], _foot(name), "Scenery", SCENERY) for name in DISPLAY
}
