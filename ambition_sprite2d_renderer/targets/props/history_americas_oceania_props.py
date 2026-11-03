"""The props of the Americas and Oceania floors of the History dimension.

The second pass of the History dimension is a grid of regions and times.
These props serve two of its floors: the Americas (Beringia, the first
maize) and Oceania (Sahul, the New Guinea highlands). They are drawn in the
cel style of the dimension's cast (`targets/characters/_history_americas_kit.py`):
flat colour, one shade, a bold warm outline. They show the skill and the age
of the first peoples of these lands with respect: no sacred designs.

- ``history_bamboo_raft``: a raft of lashed bamboo, as the first seafarers
  crossed to Sahul on: the look of a sweeping platform (as
  ``history_rail_wagon``). The top of its deck is the platform
  (`platform_looks.ron`: `RAFT_SPAN`, `RAFT_TOP`).
- ``history_clovis_points``: scenery, fluted stone spear points and a
  hammerstone on a hide.
- ``history_maize_plants``: scenery, a little teosinte (the wild grass)
  beside tall maize (what thousands of years of farmers made of it). Its
  ``idle`` row sways in the wind.
- ``history_andean_terrace``: scenery, stepped stone terraces with potato
  plants, steps set in the walls, and a basket of potatoes of many colours.
- ``history_tree_fern``: scenery, a tall tree fern of the highlands. Its
  ``idle`` row sways.
- ``history_boab_tree``: scenery, a boab tree with its bottle trunk.
- ``history_rock_shelter``: scenery, a sandstone overhang with hand
  stencils in ochre on its back wall, the black mark of old fires on its
  roof, and a hearth.

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

RAFT_FRAME = (320, 96)
RAFT_SPAN = (16.0, 304.0)
RAFT_TOP = 40.0
POINTS_FRAME = (128, 64)
MAIZE_FRAME = (192, 256)
TERRACE_FRAME = (384, 192)
FERN_FRAME = (192, 384)
BOAB_FRAME = (320, 384)
SHELTER_FRAME = (320, 256)
SWAY: List[Tuple[str, int, int]] = [("idle", 8, 160)]
SCENERY = ["prop", "scenery", "history"]

BAMBOO = (206, 188, 104, 255)
BAMBOO_SHADE = (156, 138, 66, 255)
BAMBOO_LIGHT = (234, 222, 156, 255)
BAMBOO_NODE = (128, 110, 52, 255)
FIBRE = (150, 104, 60, 255)
FIBRE_DARK = (104, 68, 36, 255)
HIDE = (176, 124, 82, 255)
HIDE_LIGHT = (206, 160, 112, 255)
HIDE_SHADE = (132, 88, 54, 255)
LEAF = (88, 150, 70, 255)
LEAF_SHADE = (58, 108, 50, 255)
LEAF_LIGHT = (140, 192, 100, 255)
STALK = (150, 168, 80, 255)
HUSK = (222, 206, 150, 255)
KERNEL = (246, 200, 64, 255)
KERNEL_SHADE = (204, 150, 40, 255)
SOIL = (122, 84, 56, 255)
SOIL_DARK = (88, 58, 38, 255)
STONE = (156, 150, 140, 255)
STONE_SHADE = (116, 110, 102, 255)
STONE_LIGHT = (190, 184, 172, 255)
BARK = (122, 92, 66, 255)
BARK_DARK = (84, 60, 42, 255)
BOAB = (186, 160, 146, 255)
BOAB_SHADE = (140, 116, 106, 255)
BOAB_LIGHT = (214, 194, 180, 255)
SANDSTONE = (214, 134, 82, 255)
SANDSTONE_SHADE = (166, 94, 56, 255)
SANDSTONE_DARK = (118, 62, 40, 255)
SANDSTONE_LIGHT = (236, 176, 120, 255)
OCHRE = (178, 52, 34, 255)
PIPECLAY = (240, 232, 214, 255)
SOOT = (40, 30, 30, 255)
ASH = (200, 192, 182, 255)


def _ellipse(cx: float, cy: float, rx: float, ry: float, n: int = 24) -> List[Point]:
    return K.ellipse_points(cx, cy, rx, ry, n)


# ---------------------------------------------------------------------------
# The bamboo raft (a platform).
# ---------------------------------------------------------------------------


def _pole(f: K.Frame, x0: float, x1: float, y: float, r: float, seed: str) -> None:
    """A bamboo pole seen from the side, from `x0` to `x1`, its middle at `y`."""
    rng = random.Random(seed)
    f.poly([(x0, y - r), (x1, y - r), (x1, y + r), (x0, y + r)], BAMBOO)
    f.poly([(x0, y + r * 0.35), (x1, y + r * 0.35), (x1, y + r), (x0, y + r)], BAMBOO_SHADE, body=False)
    f.ink([(x0 + 2.0, y - r * 0.5), (x1 - 2.0, y - r * 0.5)], 1.0, BAMBOO_LIGHT)
    x = x0 + rng.uniform(14.0, 26.0)
    while x < x1 - 8.0:
        f.ink([(x, y - r + 0.5), (x, y + r - 0.5)], 1.6, BAMBOO_NODE)
        f.ink([(x + 1.6, y - r + 1.0), (x + 1.6, y + r - 1.0)], 0.7, BAMBOO_LIGHT)
        x += rng.uniform(26.0, 34.0)
    # The cut ends: the rings of the hollow cane.
    for ex in (x0, x1):
        f.ellipse(ex, y, r * 0.45, r, BAMBOO)
        f.ellipse(ex, y, r * 0.25, r * 0.6, BAMBOO_NODE, body=False)


def _draw_raft():
    f = K.Frame(RAFT_FRAME)
    x0, x1 = RAFT_SPAN
    top = RAFT_TOP
    # The lower layer: two long poles, one behind the other.
    _pole(f, x0 + 10.0, x1 - 12.0, top + 30.0, 7.0, "raft-low-far")
    # The cross poles under the deck, seen end on.
    for k in range(11):
        cx = x0 + 18.0 + k * (x1 - x0 - 36.0) / 10.0
        f.ellipse(cx, top + 18.0, 6.0, 6.0, BAMBOO)
        f.ellipse(cx, top + 18.0, 3.4, 3.4, BAMBOO_NODE, body=False)
    _pole(f, x0 + 4.0, x1 - 4.0, top + 38.0, 7.5, "raft-low-near")
    # The deck: the side pole of the top layer. Its top is the platform.
    _pole(f, x0, x1, top + 7.0, 7.0, "raft-deck")
    # The lashings of plant fibre that tie the layers together.
    for k in range(6):
        cx = x0 + 30.0 + k * (x1 - x0 - 60.0) / 5.0
        f.poly([(cx - 4.0, top + 1.0), (cx + 4.0, top + 1.0), (cx + 4.0, top + 45.0), (cx - 4.0, top + 45.0)], FIBRE)
        for j in range(7):
            y = top + 3.0 + j * 6.0
            f.ink([(cx - 4.0, y), (cx + 4.0, y + 3.0)], 0.9, FIBRE_DARK)
    # The steering oar, lashed along the stern and trailing behind.
    f.limb([(x0 + 10.0, top + 18.0), (x0 + 2.0, top + 36.0)], 3.0, BARK)
    f.poly([(x0 - 1.0, top + 34.0), (x0 + 7.0, top + 34.0), (x0 + 4.0, top + 44.0), (x0 - 2.0, top + 43.0)], BARK)
    return A.finish(f, width=1.4)


# ---------------------------------------------------------------------------
# Clovis points on a hide.
# ---------------------------------------------------------------------------


def _point(f: K.Frame, cx: float, cy: float, length: float, width: float, angle: float, colour) -> None:
    """A fluted spear point: long and leaf shaped, with a concave base, a
    flute (the long flake taken off its base) and flake scars on its edges."""
    h, w = length / 2.0, width / 2.0
    pts = [(h, 0.0), (h * 0.55, -w * 0.8), (-h * 0.1, -w), (-h * 0.8, -w * 0.85), (-h, -w * 0.7), (-h * 0.86, 0.0), (-h, w * 0.7),
           (-h * 0.8, w * 0.85), (-h * 0.1, w), (h * 0.55, w * 0.8)]
    pts = K.turn([(cx + x, cy + y) for x, y in pts], cx, cy, angle)
    f.poly(pts, colour)
    flute = K.turn([(cx - h * 0.84, cy - w * 0.32), (cx + h * 0.05, cy - w * 0.22), (cx + h * 0.1, cy + w * 0.22), (cx - h * 0.84, cy + w * 0.32)],
                   cx, cy, angle)
    f.poly(flute, K.shade(colour, 0.86), body=False)
    for k in range(6):
        u = -0.7 + k * 0.28
        for side in (-1.0, 1.0):
            a = K.turn([(cx + h * u, cy + side * w * 0.9), (cx + h * (u + 0.1), cy + side * w * 0.45)], cx, cy, angle)
            f.ink(a, 0.6, K.shade(colour, 0.75))


def _draw_points():
    f = K.Frame(POINTS_FRAME)
    # The hide, laid flat: a rough outline with the legs of the skin.
    hide = [(10.0, 44.0), (16.0, 34.0), (8.0, 28.0), (22.0, 26.0), (40.0, 22.0), (64.0, 20.0), (90.0, 22.0), (106.0, 25.0), (120.0, 22.0),
            (116.0, 32.0), (120.0, 44.0), (112.0, 54.0), (118.0, 60.0), (96.0, 58.0), (64.0, 60.0), (34.0, 58.0), (12.0, 60.0), (16.0, 52.0)]
    f.poly(hide, HIDE)
    f.poly([(20.0, 36.0), (40.0, 28.0), (64.0, 26.0), (92.0, 28.0), (110.0, 34.0), (110.0, 46.0), (96.0, 52.0), (64.0, 54.0), (32.0, 52.0),
            (18.0, 46.0)], HIDE_LIGHT, body=False)
    f.ink([(18.0, 56.0), (60.0, 57.0), (108.0, 55.0)], 1.0, HIDE_SHADE)
    # Three points of fine stone, and a small one.
    _point(f, 38.0, 38.0, 40.0, 13.0, -14.0, (232, 222, 196, 255))
    _point(f, 70.0, 42.0, 36.0, 12.0, 8.0, (204, 160, 150, 255))
    _point(f, 98.0, 36.0, 30.0, 11.0, -30.0, (170, 172, 176, 255))
    _point(f, 92.0, 50.0, 18.0, 7.0, 4.0, (214, 196, 120, 255))
    # The hammerstone that made them.
    f.ellipse(20.0, 48.0, 7.0, 5.6, STONE)
    f.ellipse(18.6, 46.6, 2.6, 1.8, STONE_LIGHT, body=False)
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# Teosinte and maize.
# ---------------------------------------------------------------------------


def _leaf(f: K.Frame, base: Point, angle: float, length: float, width: float, droop: float, colour, shade_colour) -> None:
    """A long grass leaf from `base`: it rises at `angle` (degrees, 0 is
    right, -90 is up) and droops at its tip."""
    pts_mid = []
    a = math.radians(angle)
    x, y = base
    for k in range(7):
        u = k / 6.0
        x += math.cos(a) * length / 6.0
        y += math.sin(a) * length / 6.0 + droop * u * u * length / 6.0
        pts_mid.append((x, y))
    upper, lower = [], []
    path = [base] + pts_mid
    for k in range(len(path)):
        u = k / (len(path) - 1)
        p0 = path[max(0, k - 1)]
        p1 = path[min(len(path) - 1, k + 1)]
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        d = math.hypot(dx, dy) or 1.0
        w = width * math.sin(math.pi * min(1.0, 0.15 + u * 0.95)) * (1.0 - 0.9 * u)
        upper.append((path[k][0] - dy / d * w, path[k][1] + dx / d * w))
        lower.append((path[k][0] + dy / d * w, path[k][1] - dx / d * w))
    f.poly(upper + lower[::-1], colour)
    f.ink(path[:-1], 0.7, shade_colour)


def _draw_maize(i: int, n: int):
    w, h = MAIZE_FRAME
    f = K.Frame(MAIZE_FRAME)
    ground = h - 6.0
    t = i / float(n)
    wind = math.sin(math.tau * t)
    # The mound of earth that both stand in.
    f.poly([(10.0, ground + 2.0), (30.0, ground - 10.0), (100.0, ground - 14.0), (170.0, ground - 10.0), (184.0, ground + 2.0)], SOIL)
    f.poly([(14.0, ground + 2.0), (180.0, ground + 2.0), (176.0, ground - 2.0), (18.0, ground - 2.0)], SOIL_DARK, body=False)

    # The maize: a tall stalk with broad leaves, a tassel and two cobs.
    sx = 122.0
    top_y = 30.0
    sway = 3.0 * wind

    def stalk_at(y: float) -> Point:
        u = (ground - 10.0 - y) / (ground - 10.0 - top_y)
        return (sx + sway * u * u, y)

    stalk = [stalk_at(ground - 10.0 - k * (ground - 10.0 - top_y) / 8.0) for k in range(9)]
    for k, (ang, y, ln) in enumerate(((-24.0, 200.0, 56.0), (204.0, 176.0, 60.0), (-32.0, 150.0, 54.0), (210.0, 124.0, 56.0), (-40.0, 98.0, 48.0),
                                      (214.0, 76.0, 44.0))):
        base = stalk_at(y)
        _leaf(f, base, ang + 4.0 * wind, ln, 7.0, 0.9, LEAF if k % 2 else LEAF_LIGHT, LEAF_SHADE)
    f.limb(stalk, 7.0, STALK)
    for k in range(1, 8):
        x, y = stalk[k]
        f.ink([(x - 3.5, y), (x + 3.5, y)], 1.0, LEAF_SHADE)
    # The tassel at the top.
    tx, ty = stalk[-1]
    for k in range(6):
        a = -90.0 + (k - 2.5) * 22.0 + 6.0 * wind
        ex = tx + math.cos(math.radians(a)) * 18.0
        ey = ty + math.sin(math.radians(a)) * 18.0 + (8.0 if abs(k - 2.5) > 1.5 else 0.0)
        f.limb([(tx, ty), (ex, ey)], 2.0, (210, 180, 96, 255))
    # The cobs: one with its husk open on the yellow kernels.
    for (y, side, opened) in ((156.0, 1.0, True), (120.0, -1.0, False)):
        bx, by = stalk_at(y)
        cx, cy = bx + side * 12.0, by - 8.0
        ang = 70.0 * side - 90.0
        if opened:
            cob = K.turn([(cx - 6.0, cy - 18.0), (cx + 6.0, cy - 18.0), (cx + 7.0, cy + 6.0), (cx, cy + 14.0), (cx - 7.0, cy + 6.0)], cx, cy, 20.0 * side)
            f.poly(cob, KERNEL)
            for r in range(6):
                for c in range(3):
                    kx, ky = K.turn([(cx - 4.0 + c * 4.0, cy - 14.0 + r * 4.6)], cx, cy, 20.0 * side)[0]
                    f.dot(kx, ky, 1.1, KERNEL_SHADE)
            for s in (-1.0, 1.0):
                husk = K.turn([(cx + s * 6.0, cy - 4.0), (cx + s * 15.0, cy - 14.0), (cx + s * 9.0, cy + 10.0), (cx, cy + 16.0)], cx, cy, 20.0 * side)
                f.poly(husk, HUSK)
            silk = K.turn([(cx, cy - 18.0), (cx + 3.0, cy - 26.0), (cx + 7.0, cy - 28.0)], cx, cy, 20.0 * side)
            f.ink(silk, 1.2, (180, 110, 70, 255))
        else:
            cob = K.turn([(cx - 6.0, cy - 14.0), (cx + 6.0, cy - 14.0), (cx + 7.0, cy + 8.0), (cx, cy + 14.0), (cx - 7.0, cy + 8.0)], cx, cy, 20.0 * side)
            f.poly(cob, HUSK)
            f.ink(K.turn([(cx, cy - 12.0), (cx, cy + 12.0)], cx, cy, 20.0 * side), 0.8, K.shade(HUSK, 0.75))
        del ang
        f.limb([(bx, by), (cx - side * 2.0, cy + 10.0)], 3.0, STALK)

    # The teosinte: a low bushy grass of many thin stems, with tiny hard ears.
    rng = random.Random("teosinte")
    tx0 = 58.0
    for k in range(9):
        a = -90.0 + (k - 4.0) * 9.0 + 3.0 * wind
        ln = rng.uniform(40.0, 60.0)
        _leaf(f, (tx0 + (k - 4.0) * 2.0, ground - 10.0), a, ln, 2.6, 0.3, LEAF if k % 2 else LEAF_SHADE, LEAF_SHADE)
    for k in range(5):
        a = math.radians(-90.0 + (k - 2.0) * 20.0 + 3.0 * wind)
        ex = tx0 + math.cos(a) * 46.0
        ey = ground - 10.0 + math.sin(a) * 46.0
        f.limb([(tx0, ground - 10.0), (ex, ey)], 1.6, STALK)
        # The ear: a short zig-zag of a few hard brown seeds.
        for s in range(4):
            sx2 = ex + math.cos(a) * s * 3.2 + (1.4 if s % 2 else -1.4)
            sy2 = ey + math.sin(a) * s * 3.2
            f.ellipse(sx2, sy2, 1.8, 2.2, (150, 108, 62, 255))
    return A.finish(f, width=1.3)


# ---------------------------------------------------------------------------
# The Andean terrace.
# ---------------------------------------------------------------------------


def _stones(f: K.Frame, x0: float, x1: float, y0: float, y1: float, seed: str) -> None:
    """A wall of fitted field stones between `x0`..`x1` and `y0` (top)..`y1`."""
    rng = random.Random(seed)
    y = y0
    row = 0
    while y < y1 - 2.0:
        rh = min(y1 - y, rng.uniform(9.0, 13.0))
        x = x0 + (rng.uniform(0.0, 8.0) if row % 2 else 0.0)
        while x < x1 - 2.0:
            sw = min(x1 - x, rng.uniform(14.0, 24.0))
            pts = [(x + 1.2, y + 1.0), (x + sw - 1.0, y + 0.8 + rng.uniform(0.0, 1.0)), (x + sw - 0.6, y + rh - 1.0), (x + 1.0, y + rh - 0.8)]
            f.poly(pts, K.shade(STONE, rng.uniform(0.9, 1.08)), body=False)
            f.ink([(x + 2.0, y + rh - 1.6), (x + sw - 1.6, y + rh - 1.4)], 0.8, STONE_SHADE)
            x += sw
        y += rh
        row += 1


def _potato_plant(f: K.Frame, x: float, y: float, seed: str) -> None:
    """A potato plant: a bush of round leaflets with small flowers."""
    rng = random.Random(seed)
    for k in range(7):
        a = math.radians(-90.0 + (k - 3.0) * 26.0)
        ln = rng.uniform(10.0, 16.0)
        ex, ey = x + math.cos(a) * ln, y + math.sin(a) * ln * 0.9
        f.limb([(x, y), (ex, ey)], 1.4, LEAF_SHADE)
        f.ellipse(ex, ey, 4.4, 3.4, LEAF if k % 2 else LEAF_LIGHT)
    for k in range(3):
        fx, fy = x + rng.uniform(-9.0, 9.0), y - rng.uniform(12.0, 18.0)
        f.ellipse(fx, fy, 2.2, 2.2, (170, 120, 210, 255) if k % 2 else (246, 240, 230, 255))
        f.dot(fx, fy, 0.8, KERNEL)


def _draw_terrace():
    w, h = TERRACE_FRAME
    f = K.Frame(TERRACE_FRAME)
    foot = h - 6.0
    tiers = [(8.0, 146.0), (110.0, 100.0), (214.0, 54.0)]
    right = w - 8.0
    # The tiers, back to front: each is a stone wall with a bed of earth on it.
    for k, (x0, top) in enumerate(tiers[::-1]):
        base = foot if k == len(tiers) - 1 else tiers[::-1][k + 1][1]
        f.poly([(x0, base), (right, base), (right, top), (x0, top)], STONE)
        _stones(f, x0, right, top + 8.0, base, f"terrace-{k}")
        f.poly([(x0, top + 8.0), (x0 + 6.0, top + 8.0), (x0 + 6.0, base), (x0, base)], STONE_SHADE, body=False)
        # The bed of earth on top, and its edge of capstones.
        f.poly([(x0 - 2.0, top), (right, top), (right, top + 8.0), (x0 - 2.0, top + 8.0)], SOIL)
        f.ink([(x0, top + 1.2), (right - 2.0, top + 1.2)], 1.0, K.shade(SOIL, 1.2))
        for c in range(int((right - x0) // 30.0)):
            _potato_plant(f, x0 + 18.0 + c * 30.0, top + 2.0, f"potato-{k}-{c}")
        # The steps that jut out of the wall, one above the other.
        if k < len(tiers) - 1:
            lower_top = base
            sx = x0 + 10.0
            for s in range(3):
                sy = top + 14.0 + s * (lower_top - top - 14.0) / 3.0
                f.poly([(sx + s * 8.0, sy), (sx + s * 8.0 + 16.0, sy), (sx + s * 8.0 + 16.0, sy + 4.0), (sx + s * 8.0, sy + 4.0)], STONE_LIGHT)
    # A basket of potatoes of many colours at the foot of the terrace.
    bx, by = 52.0, foot
    f.poly([(bx - 24.0, by - 26.0), (bx + 24.0, by - 26.0), (bx + 18.0, by), (bx - 18.0, by)], (196, 154, 90, 255))
    for r in range(3):
        y = by - 22.0 + r * 8.0
        f.ink([(bx - 22.0 + r * 2.0, y), (bx + 22.0 - r * 2.0, y)], 1.0, (140, 100, 52, 255))
    for k, colour in enumerate(((120, 70, 140, 255), (226, 190, 80, 255), (176, 70, 60, 255), (210, 170, 120, 255), (90, 60, 110, 255))):
        f.ellipse(bx - 16.0 + k * 8.0, by - 28.0 - (k % 2) * 4.0, 5.4, 4.4, colour)
        f.dot(bx - 17.0 + k * 8.0, by - 29.0 - (k % 2) * 4.0, 0.7, K.shade(colour, 0.6))
    return A.finish(f, width=1.4)


# ---------------------------------------------------------------------------
# The tree fern.
# ---------------------------------------------------------------------------


def _frond(f: K.Frame, base: Point, angle: float, length: float, droop: float, colour, shade_colour) -> None:
    """A fern frond: an arching stem with leaflets on both sides."""
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
        nx, ny = -dy / d, dx / d
        ln = 12.0 * (1.0 - k / 11.0) + 2.0
        for s in (-1.0, 1.0):
            tip = (pts[k][0] + (nx * s + dx / d * 0.6) * ln, pts[k][1] + (ny * s + dy / d * 0.6) * ln)
            f.limb([pts[k], tip], 3.2, colour)
    f.limb(pts, 2.2, shade_colour)


def _draw_fern(i: int, n: int):
    w, h = FERN_FRAME
    f = K.Frame(FERN_FRAME)
    foot = h - 6.0
    t = i / float(n)
    wind = math.sin(math.tau * t)
    crown = (98.0 + 2.0 * wind, 112.0)
    # The trunk: thick and shaggy with the bases of old fronds.
    trunk = [(90.0, foot - 12.0), (92.0, foot - 90.0), (95.0, foot - 180.0), (crown[0], crown[1] + 6.0)]
    f.limb(trunk, 22.0, BARK)
    f.poly([(76.0, foot), (104.0, foot), (100.0, foot - 14.0), (80.0, foot - 14.0)], BARK)
    rng = random.Random("fern-trunk")
    for k in range(22):
        u = k / 22.0
        x = 90.0 + (crown[0] - 90.0) * u + rng.uniform(-7.0, 7.0)
        y = foot - 8.0 - (foot - crown[1] - 20.0) * u
        f.ink([(x - 3.0, y), (x, y - 5.0), (x + 3.0, y)], 1.2, BARK_DARK)
    # Dead fronds hang down under the crown.
    for s in (-1.0, 1.0):
        _frond(f, (crown[0] + s * 4.0, crown[1] + 10.0), 90.0 - s * 70.0, 50.0, 1.4, (150, 120, 70, 255), (110, 84, 48, 255))
    # The living fronds arch out of the crown.
    for k, (ang, ln) in enumerate(((-170.0, 80.0), (-10.0, 80.0), (-145.0, 80.0), (-35.0, 80.0), (-120.0, 72.0), (-60.0, 72.0), (-95.0, 58.0))):
        _frond(f, crown, ang + 4.0 * wind, ln, 0.8 if abs(ang + 90.0) > 40.0 else 0.4, LEAF if k % 2 else LEAF_LIGHT, LEAF_SHADE)
    # A new frond that has not yet unrolled: a tight curl.
    cx, cy = crown[0] + 6.0, crown[1] - 18.0
    f.limb([(crown[0], crown[1]), (cx, cy + 6.0)], 3.0, LEAF_SHADE)
    curl = [(cx + 6.0 * math.cos(a) * (1.0 - a / 12.0), cy + 6.0 * math.sin(a) * (1.0 - a / 12.0)) for a in [k * 0.6 for k in range(16)]]
    f.limb(curl, 3.0, LEAF_LIGHT)
    return A.finish(f, width=1.3)


# ---------------------------------------------------------------------------
# The boab tree.
# ---------------------------------------------------------------------------


def _draw_boab():
    w, h = BOAB_FRAME
    f = K.Frame(BOAB_FRAME)
    foot = h - 6.0
    cx = 160.0
    # The branches first: short, thick and crooked, out of the top of the
    # trunk, each with a fork or two and sparse tufts of leaves.
    branches = [[(cx - 20.0, 150.0), (cx - 56.0, 120.0), (cx - 84.0, 112.0), (cx - 110.0, 86.0)],
                [(cx - 12.0, 146.0), (cx - 38.0, 100.0), (cx - 34.0, 70.0), (cx - 56.0, 46.0)],
                [(cx + 2.0, 144.0), (cx + 8.0, 96.0), (cx - 4.0, 64.0), (cx + 6.0, 34.0)],
                [(cx + 14.0, 146.0), (cx + 40.0, 108.0), (cx + 66.0, 92.0), (cx + 76.0, 56.0)],
                [(cx + 24.0, 152.0), (cx + 70.0, 128.0), (cx + 100.0, 120.0), (cx + 120.0, 94.0)]]
    rng = random.Random("boab")
    tufts: List[Point] = []
    for k, br in enumerate(branches):
        f.limb(br, 15.0 - (k % 2) * 3.0, BOAB_SHADE)
        f.limb(br[1:], 9.0, BOAB)
        # Forks: crooked twigs off the middle and the end of the branch.
        for j, (bx, by) in enumerate(br[2:]):
            for side in ((-1.0, 1.0) if j == len(br) - 3 else (1.0 if k % 2 else -1.0,)):
                tx = bx + side * rng.uniform(12.0, 20.0)
                ty = by - rng.uniform(12.0, 20.0)
                mx = (bx + tx) / 2.0 + side * 3.0
                f.limb([(bx, by), (mx, (by + ty) / 2.0 + 2.0), (tx, ty)], 3.6, BOAB_SHADE)
                tufts.append((tx, ty))
    # Sparse tufts of small leaves at the ends of the twigs.
    for k, (tx, ty) in enumerate(tufts):
        for j in range(5):
            a = math.radians(-160.0 + j * 35.0 + rng.uniform(-10.0, 10.0))
            lx, ly = tx + math.cos(a) * 6.0, ty + math.sin(a) * 5.0
            f.ellipse(lx, ly, 4.0, 2.2, LEAF if (j + k) % 2 else LEAF_SHADE)
    # The seed pods: velvet ovals that hang on long stalks.
    for px, py in ((cx - 76.0, 124.0), (cx + 58.0, 106.0), (cx + 96.0, 132.0)):
        f.ink([(px, py - 10.0), (px, py)], 1.2, BOAB_SHADE)
        f.ellipse(px, py + 6.0, 4.4, 7.0, (150, 140, 96, 255))
    # The trunk: a great bottle, swollen low and narrow at the neck.
    left = [(cx - 74.0, foot), (cx - 86.0, foot - 50.0), (cx - 88.0, foot - 110.0), (cx - 74.0, foot - 160.0), (cx - 48.0, foot - 200.0),
            (cx - 30.0, 152.0), (cx - 24.0, 140.0)]
    right = [(cx + 26.0, 140.0), (cx + 34.0, 152.0), (cx + 52.0, foot - 200.0), (cx + 78.0, foot - 160.0), (cx + 90.0, foot - 110.0),
             (cx + 88.0, foot - 50.0), (cx + 78.0, foot)]
    f.poly(left + right, BOAB)
    f.poly([(cx + 40.0, foot), (cx + 78.0, foot), (cx + 88.0, foot - 50.0), (cx + 90.0, foot - 110.0), (cx + 78.0, foot - 160.0),
            (cx + 52.0, foot - 200.0), (cx + 40.0, foot - 180.0), (cx + 60.0, foot - 110.0), (cx + 58.0, foot - 50.0)], BOAB_SHADE, body=False)
    f.poly([(cx - 70.0, foot - 60.0), (cx - 74.0, foot - 110.0), (cx - 60.0, foot - 156.0), (cx - 50.0, foot - 150.0), (cx - 58.0, foot - 100.0),
            (cx - 56.0, foot - 60.0)], BOAB_LIGHT, body=False)
    # The folds of the bark, up and down the trunk.
    for k in range(7):
        x = cx - 60.0 + k * 20.0
        f.ink([(x, foot - 4.0), (x + 4.0 * math.sin(k), foot - 90.0), (x * 0.7 + cx * 0.3, foot - 190.0)], 1.2, BOAB_SHADE)
    # The roots spread at its foot.
    for s in (-1.0, 1.0):
        f.poly([(cx + s * 60.0, foot), (cx + s * 100.0, foot), (cx + s * 74.0, foot - 12.0)], BOAB_SHADE)
    return A.finish(f, width=1.6)


# ---------------------------------------------------------------------------
# The rock shelter.
# ---------------------------------------------------------------------------


def _hand(cx: float, cy: float, s: float, angle: float) -> List[Tuple[Point, float]]:
    """A hand as round strokes: (point list, width) for the palm and each
    finger. The fingers point up; `angle` turns the hand."""
    strokes: List[Tuple[Point, float]] = []
    fingers = [(-7.0, -2.0, -9.0, -12.0), (-3.4, -6.0, -4.0, -21.0), (0.6, -6.6, 0.8, -23.0), (4.4, -6.0, 5.6, -20.0), (7.4, -3.0, 10.0, -14.0)]
    out = []
    for x0, y0, x1, y1 in fingers:
        out.append(([(cx + x0 * s, cy + y0 * s), (cx + x1 * s, cy + y1 * s)], 4.4 * s))
    out.append(([(cx, cy - 1.0 * s), (cx, cy + 5.0 * s)], 16.0 * s))
    out.append(([(cx - 1.0 * s, cy + 6.0 * s), (cx - 1.0 * s, cy + 16.0 * s)], 9.0 * s))
    for pts, wd in out:
        strokes.append((K.turn(pts, cx, cy, angle), wd))
    return strokes


def _stencil(f: K.Frame, cx: float, cy: float, s: float, angle: float, spray, wall, seed: str) -> None:
    """A hand stencil: paint blown round a hand held to the wall. The hand
    stays the colour of the rock, inside a haze of paint."""
    rng = random.Random(seed)
    f.ellipse(cx, cy - 4.0 * s, 17.0 * s, 20.0 * s, K.alpha(spray, 0.35), body=False)
    f.ellipse(cx, cy - 4.0 * s, 13.0 * s, 16.0 * s, K.alpha(spray, 0.55), body=False)
    for _ in range(18):
        a = rng.uniform(0.0, math.tau)
        r = rng.uniform(12.0, 19.0) * s
        f.dot(cx + math.cos(a) * r, cy - 4.0 * s + math.sin(a) * r * 1.15, rng.uniform(0.5, 1.1), K.alpha(spray, 0.7))
    for pts, wd in _hand(cx, cy, s, angle):
        f.limb(pts, wd, wall, body=False)


def _draw_shelter():
    w, h = SHELTER_FRAME
    f = K.Frame(SHELTER_FRAME)
    floor = h - 8.0
    # The back wall of the hollow, under the roof. Left of it the hollow is
    # open: the roof juts out over nothing.
    back = [(46.0, floor), (40.0, 176.0), (52.0, 140.0), (100.0, 124.0), (150.0, 124.0), (190.0, 132.0), (214.0, 152.0), (226.0, 190.0),
            (230.0, floor)]
    f.poly(back, K.shade(SANDSTONE_SHADE, 1.12))
    f.poly([(46.0, floor), (40.0, 176.0), (52.0, 140.0), (100.0, 124.0), (150.0, 124.0), (190.0, 132.0), (120.0, 134.0), (70.0, 146.0), (56.0, 176.0),
            (60.0, floor)], SANDSTONE_SHADE, body=False)
    # The black mark of old fires, smeared up the wall and over the roof.
    rng = random.Random("soot")
    for k in range(9):
        x = 96.0 + rng.uniform(-16.0, 20.0)
        y = 138.0 + rng.uniform(-2.0, 8.0)
        f.ellipse(x, y, rng.uniform(8.0, 16.0), rng.uniform(3.0, 6.0), K.alpha(SOOT, 0.22), body=False)
    # Hand stencils on the back wall, in red ochre and in white clay.
    wall = K.shade(SANDSTONE_SHADE, 1.12)
    for k, (x, y, sc, ang, colour) in enumerate(((120.0, 168.0, 1.15, -12.0, OCHRE), (152.0, 160.0, 1.05, 8.0, OCHRE), (184.0, 178.0, 1.0, 20.0, PIPECLAY),
                                                 (136.0, 206.0, 0.95, -4.0, OCHRE), (102.0, 204.0, 0.9, -18.0, PIPECLAY), (168.0, 214.0, 0.85, 6.0, OCHRE))):
        _stencil(f, x, y, sc, ang, colour, wall, f"stencil-{k}")
    # The rock: a great slab whose roof juts out to the left, on a base of rock.
    rock = [(10.0, 108.0), (14.0, 70.0), (40.0, 34.0), (90.0, 14.0), (170.0, 10.0), (240.0, 20.0), (290.0, 46.0), (310.0, 100.0), (310.0, floor),
            (228.0, floor), (224.0, 186.0), (212.0, 152.0), (188.0, 130.0), (150.0, 121.0), (100.0, 120.0), (56.0, 120.0), (26.0, 116.0)]
    f.poly(rock, SANDSTONE)
    # The underside of the roof, in shade, and the layers of the sandstone.
    f.poly([(10.0, 108.0), (26.0, 116.0), (56.0, 120.0), (100.0, 120.0), (150.0, 121.0), (188.0, 130.0), (212.0, 152.0), (224.0, 186.0),
            (228.0, floor), (238.0, floor), (234.0, 180.0), (218.0, 140.0), (190.0, 118.0), (100.0, 110.0), (40.0, 106.0)], SANDSTONE_SHADE, body=False)
    for k, y in enumerate((40.0, 64.0, 88.0)):
        f.ink([(22.0 + k * 4.0, y + 16.0), (120.0, y), (220.0, y + 4.0), (300.0 - k * 4.0, y + 20.0)], 1.2, SANDSTONE_DARK)
    f.ink([(240.0, 130.0), (300.0, 140.0)], 1.2, SANDSTONE_DARK)
    f.ink([(236.0, 190.0), (304.0, 196.0)], 1.2, SANDSTONE_DARK)
    f.poly([(40.0, 34.0), (90.0, 14.0), (170.0, 10.0), (240.0, 20.0), (200.0, 24.0), (120.0, 22.0), (60.0, 38.0)], SANDSTONE_LIGHT, body=False)
    f.poly([(262.0, 110.0), (308.0, 104.0), (308.0, floor - 2.0), (270.0, floor - 2.0)], K.alpha(SANDSTONE_DARK, 0.35), body=False)
    # The floor of the hollow: packed earth.
    f.poly([(28.0, floor + 2.0), (236.0, floor + 2.0), (232.0, floor - 6.0), (34.0, floor - 6.0)], (178, 128, 88, 255))
    # The hearth on the floor: a ring of stones, ash and a few sticks.
    hx, hy = 82.0, floor - 6.0
    f.ellipse(hx, hy, 24.0, 5.0, ASH, body=False)
    for k in range(7):
        a = math.pi + k * math.pi / 6.0
        f.ellipse(hx + math.cos(a) * 24.0, hy + 1.0 + math.sin(a) * 4.0, 5.0, 3.6, STONE)
    for k in range(3):
        f.limb([(hx - 12.0 + k * 8.0, hy - 1.0), (hx - 2.0 + k * 6.0, hy - 6.0 - k)], 2.4, SOOT)
    f.glow(hx, hy - 3.0, 4.0, K.alpha((240, 120, 50, 255), 0.6))
    # A grinding stone with its top stone, near the fire.
    f.ellipse(182.0, floor - 6.0, 16.0, 5.0, STONE)
    f.ellipse(180.0, floor - 10.0, 6.0, 3.4, STONE_LIGHT)
    return A.finish(f, width=1.6)


TARGETS: Dict[str, dict] = {
    "history_bamboo_raft": _publisher("history_bamboo_raft", "Bamboo Raft", STILL, RAFT_FRAME, lambda anim, i, n: _draw_raft(),
                                      {"top": ((RAFT_SPAN[0] + RAFT_SPAN[1]) / 2.0, RAFT_TOP)}, "Scenery", ["prop", "platform", "history"]),
    "history_clovis_points": _publisher("history_clovis_points", "Clovis Points", STILL, POINTS_FRAME, lambda anim, i, n: _draw_points(),
                                        {"foot": (64.0, 64.0)}, "Scenery", SCENERY),
    "history_maize_plants": _publisher("history_maize_plants", "Teosinte and Maize", SWAY, MAIZE_FRAME, lambda anim, i, n: _draw_maize(i, n),
                                       {"foot": (96.0, 256.0)}, "Scenery", SCENERY),
    "history_andean_terrace": _publisher("history_andean_terrace", "Andean Terrace", STILL, TERRACE_FRAME, lambda anim, i, n: _draw_terrace(),
                                         {"foot": (192.0, 192.0)}, "Scenery", SCENERY),
    "history_tree_fern": _publisher("history_tree_fern", "Tree Fern", SWAY, FERN_FRAME, lambda anim, i, n: _draw_fern(i, n),
                                    {"foot": (96.0, 384.0)}, "Scenery", SCENERY),
    "history_boab_tree": _publisher("history_boab_tree", "Boab Tree", STILL, BOAB_FRAME, lambda anim, i, n: _draw_boab(),
                                    {"foot": (160.0, 384.0)}, "Scenery", SCENERY),
    "history_rock_shelter": _publisher("history_rock_shelter", "Rock Shelter", STILL, SHELTER_FRAME, lambda anim, i, n: _draw_shelter(),
                                       {"foot": (160.0, 256.0)}, "Scenery", SCENERY),
}

#: The drawing of each target, by its row (for previews).
DRAW = {
    "history_bamboo_raft": lambda anim, i, n: _draw_raft(),
    "history_clovis_points": lambda anim, i, n: _draw_points(),
    "history_maize_plants": lambda anim, i, n: _draw_maize(i, n),
    "history_andean_terrace": lambda anim, i, n: _draw_terrace(),
    "history_tree_fern": lambda anim, i, n: _draw_fern(i, n),
    "history_boab_tree": lambda anim, i, n: _draw_boab(),
    "history_rock_shelter": lambda anim, i, n: _draw_shelter(),
}
