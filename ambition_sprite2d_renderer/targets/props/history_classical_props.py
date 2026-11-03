"""The props of the Classical Shore of the History dimension (biome `history_classical`).

The shore of the Greeks, the Persians and Rome, drawn in the cel style of
the dimension's cast (`targets/characters/_history_cast_kit.py`): white
marble, terracotta red, olive green and Aegean blue, with a sepia outline.

- ``history_marble_column``: scenery. A tall Ionic column of white marble:
  a base, a fluted shaft and a capital with two scrolls.
- ``history_broken_column``: scenery. The stump of a column with a broken
  top, a drum of it that fell and lies on its side, rubble, and a sprig of
  olive that grows out of the cracks.
- ``history_aqueduct``: scenery. Two tiers of stone arches with a channel
  of water on top; a little water spills over its edge.
- ``history_amphorae``: scenery. Three amphorae of terracotta in a wooden
  stand, painted with black bands and a key pattern.
- ``history_stoa_gate``: a door (the look of a `LockWall` of 48 by 192
  world units, drawn at 2 to 1, as `art_colour_gate_*`). A bronze double
  door between two small columns, with a big question mark on it:
  Socratease opens it to the answer "I know that I know nothing".
- ``history_bust``: scenery. A marble bust of a stern Roman on a plinth.
  Somebody (a vandal) painted a black moustache on him.

The numbers are frame pixels; the game shows each prop at half its frame.
No drop shadows: the game draws them.
"""

from __future__ import annotations

import math
import random
from typing import Dict, List, Tuple

from PIL import ImageDraw

from ..characters import _art_cast_kit as K
from ..characters import _history_cast_kit as H
from .art_props import _publisher

STILL: List[Tuple[str, int, int]] = [("idle", 1, 1000)]

COLUMN_FRAME = (96, 384)
BROKEN_FRAME = (192, 192)
AQUEDUCT_FRAME = (512, 384)
AMPHORAE_FRAME = (128, 128)
STOA_FRAME = (96, 384)
BUST_FRAME = (96, 192)

STONE = (226, 208, 176, 255)
STONE_SHADE = (176, 152, 118, 255)
STONE_LIGHT = (242, 230, 206, 255)
WATER = (70, 150, 200, 255)
WATER_LIGHT = (170, 220, 240, 255)
BLACK_FIGURE = (44, 30, 26, 255)
PAINT = (30, 26, 34, 255)


def _punch(f: K.Frame, points) -> None:
    """Cut a hole through the frame: the sky shows through an arch."""
    pts = f._w(points)
    ImageDraw.Draw(f.image).polygon(pts, fill=(0, 0, 0, 0))  # raw-draw-ok: erasing a hole is a raw write of clear pixels
    ImageDraw.Draw(f.silhouette).polygon(pts, fill=0)  # raw-draw-ok: an L mask has no alpha to composite
    ImageDraw.Draw(f.glow_layer).polygon(pts, fill=(0, 0, 0, 0))  # raw-draw-ok: erasing a hole is a raw write of clear pixels


def _fluted_shaft(f: K.Frame, x0: float, x1: float, y0: float, y1: float, taper: float = 0.0) -> None:
    """A fluted marble shaft from `y0` (top) to `y1` (foot); `taper` narrows its top."""
    f.poly([(x0 + taper, y0), (x1 - taper, y0), (x1, y1), (x0, y1)], H.MARBLE)
    w = x1 - x0
    f.poly([(x1 - taper - w * 0.28, y0), (x1 - taper, y0), (x1, y1), (x1 - w * 0.28, y1)], H.MARBLE_SHADE, body=False)
    for k in range(1, 6):
        u = k / 6.0
        f.ink([(x0 + taper + (w - 2 * taper) * u, y0 + 2.0), (x0 + w * u, y1 - 2.0)], 1.4, K.alpha(H.MARBLE_SHADE if u < 0.7 else K.shade(H.MARBLE_SHADE, 0.85), 0.9))
    f.ink([(x0 + taper + 4.0, y0 + 4.0), (x0 + 5.0, y1 - 4.0)], 1.4, K.alpha(K.WHITE, 0.8))


def _ionic_capital(f: K.Frame, cx: float, y: float, half: float) -> None:
    """An Ionic capital at row `y` (its foot): two scrolls and an abacus."""
    f.poly([(cx - half - 4.0, y - 22.0), (cx + half + 4.0, y - 22.0), (cx + half + 4.0, y - 14.0), (cx - half - 4.0, y - 14.0)], H.MARBLE)
    f.poly([(cx - half + 2.0, y - 14.0), (cx + half - 2.0, y - 14.0), (cx + half - 6.0, y), (cx - half + 6.0, y)], H.MARBLE)
    for side in (-1.0, 1.0):
        sx = cx + side * (half - 1.0)
        f.ellipse(sx, y - 8.0, 8.0, 8.0, H.MARBLE)
        f.ellipse(sx, y - 8.0, 5.0, 5.0, H.MARBLE_SHADE, body=False)
        f.ellipse(sx, y - 8.0, 2.4, 2.4, H.MARBLE, body=False)
    f.ink([(cx - half + 8.0, y - 5.0), (cx + half - 8.0, y - 5.0)], 1.2, H.MARBLE_SHADE)
    for k in range(5):
        f.ellipse(cx - 12.0 + k * 6.0, y - 9.0, 2.0, 2.4, K.alpha(H.MARBLE_SHADE, 0.8), body=False)


def _draw_column(anim, i, n):
    w, h = COLUMN_FRAME
    f = K.Frame(COLUMN_FRAME)
    cx = w / 2.0
    foot = h - 6.0
    # The base: a square plinth and two round mouldings.
    f.poly([(cx - 34.0, foot), (cx + 34.0, foot), (cx + 34.0, foot - 12.0), (cx - 34.0, foot - 12.0)], H.MARBLE)
    f.poly([(cx + 18.0, foot), (cx + 34.0, foot), (cx + 34.0, foot - 12.0), (cx + 18.0, foot - 12.0)], H.MARBLE_SHADE, body=False)
    f.ellipse(cx, foot - 15.0, 30.0, 4.6, H.MARBLE)
    f.ellipse(cx, foot - 22.0, 26.0, 4.0, H.MARBLE)
    _fluted_shaft(f, cx - 22.0, cx + 22.0, 34.0, foot - 24.0, taper=3.0)
    _ionic_capital(f, cx, 36.0, 22.0)
    # A thin crack, and a little olive leaf caught at the base.
    f.ink([(cx + 8.0, 200.0), (cx + 4.0, 214.0), (cx + 9.0, 226.0)], 1.0, K.alpha(H.SEPIA_INK, 0.6))
    f.poly([(cx - 30.0, foot - 13.0), (cx - 22.0, foot - 18.0), (cx - 16.0, foot - 14.0), (cx - 24.0, foot - 11.0)], H.OLIVE)
    return f.finish(outline=H.SEPIA_INK, width=1.8)


def _draw_broken(anim, i, n):
    w, h = BROKEN_FRAME
    f = K.Frame(BROKEN_FRAME)
    foot = h - 6.0
    rng = random.Random("history_broken_column")
    # The stump: a base, a fluted shaft and a jagged broken top.
    cx = 56.0
    f.poly([(cx - 34.0, foot), (cx + 34.0, foot), (cx + 34.0, foot - 12.0), (cx - 34.0, foot - 12.0)], H.MARBLE)
    f.ellipse(cx, foot - 15.0, 30.0, 4.4, H.MARBLE)
    top = foot - 120.0
    jag = [(cx - 22.0, top + 18.0), (cx - 14.0, top + 6.0), (cx - 6.0, top + 14.0), (cx + 2.0, top), (cx + 10.0, top + 10.0), (cx + 16.0, top + 4.0),
           (cx + 22.0, top + 20.0)]
    f.poly([(cx - 22.0, foot - 18.0), (cx + 22.0, foot - 18.0)] + jag[::-1], H.MARBLE)
    f.poly([(cx + 10.0, foot - 18.0), (cx + 22.0, foot - 18.0), (cx + 22.0, top + 20.0), (cx + 16.0, top + 4.0), (cx + 10.0, top + 10.0)],
           H.MARBLE_SHADE, body=False)
    for k in range(1, 5):
        x = cx - 22.0 + 44.0 * k / 5.0
        f.ink([(x, foot - 20.0), (x, top + 22.0 - (6.0 if k == 3 else 0.0))], 1.4, K.alpha(H.MARBLE_SHADE, 0.9))
    f.ink([(cx - 14.0, top + 8.0), (cx - 8.0, top + 30.0), (cx - 12.0, top + 44.0)], 1.0, K.alpha(H.SEPIA_INK, 0.6))
    # The fallen drum, on its side: its round face toward us.
    dx, dy = 140.0, foot - 30.0
    f.poly([(dx - 40.0, dy - 28.0), (dx, dy - 28.0), (dx, dy + 28.0), (dx - 40.0, dy + 28.0)], H.MARBLE_SHADE)
    for k in range(4):
        y = dy - 21.0 + k * 14.0
        f.ink([(dx - 40.0, y), (dx - 2.0, y)], 1.2, K.shade(H.MARBLE_SHADE, 0.85))
    f.ellipse(dx, dy, 14.0, 28.0, H.MARBLE)
    f.ellipse(dx, dy, 9.0, 20.0, K.alpha(H.MARBLE_SHADE, 0.6), body=False)
    for k in range(12):
        a = math.tau * k / 12.0
        f.ink([(dx + math.cos(a) * 12.0, dy + math.sin(a) * 25.0), (dx + math.cos(a) * 14.0, dy + math.sin(a) * 28.0)], 1.2, H.MARBLE_SHADE)
    # Rubble.
    for x, r in ((96.0, 6.0), (108.0, 4.0), (176.0, 5.0), (20.0, 4.0)):
        pts = [(x + math.cos(a) * r * rng.uniform(0.7, 1.2), foot - r * 0.8 + math.sin(a) * r * 0.8) for a in [k * math.tau / 6 for k in range(6)]]
        f.poly(pts, H.MARBLE if r > 4.5 else H.MARBLE_SHADE)
    # A sprig of olive out of the cracks of the stump.
    f.ink([(cx + 4.0, top + 6.0), (cx + 12.0, top - 10.0), (cx + 20.0, top - 22.0)], 1.8, H.OLIVE_DARK)
    for k, (x, y, a) in enumerate(((cx + 8.0, top - 4.0, -150.0), (cx + 12.0, top - 10.0, -20.0), (cx + 16.0, top - 16.0, -160.0), (cx + 19.0, top - 21.0, -40.0))):
        r = math.radians(a)
        tip = (x + math.cos(r) * 10.0, y + math.sin(r) * 10.0)
        nx, ny = -math.sin(r) * 2.2, math.cos(r) * 2.2
        f.poly([(x, y), ((x + tip[0]) / 2 + nx, (y + tip[1]) / 2 + ny), tip, ((x + tip[0]) / 2 - nx, (y + tip[1]) / 2 - ny)], H.OLIVE)
    f.ellipse(cx + 21.0, top - 18.0, 2.6, 3.2, (60, 50, 70, 255))
    return f.finish(outline=H.SEPIA_INK, width=1.8)


def _draw_aqueduct(anim, i, n):
    w, h = AQUEDUCT_FRAME
    f = K.Frame(AQUEDUCT_FRAME)
    m = 6.0
    foot = h - m
    rng = random.Random("history_aqueduct")
    # The whole wall first, then the arches cut out of it: the inside of each
    # arch in shade, and the sky through it.
    top_chan, deck, mid = 40.0, 70.0, 200.0
    f.poly([(m, deck), (w - m, deck), (w - m, foot), (m, foot)], STONE)
    # The channel on top, with its water.
    f.poly([(m, top_chan), (w - m, top_chan), (w - m, deck), (m, deck)], STONE)
    f.poly([(m + 4.0, top_chan + 6.0), (w - m - 4.0, top_chan + 6.0), (w - m - 4.0, top_chan + 14.0), (m + 4.0, top_chan + 14.0)], WATER, body=False)
    for k in range(9):
        x = m + 20.0 + k * 54.0
        f.ink([(x, top_chan + 9.0), (x + 18.0, top_chan + 9.0)], 1.4, WATER_LIGHT)
    f.limb([(m, deck), (w - m, deck)], 3.0, STONE_SHADE, body=False)
    f.limb([(m, mid), (w - m, mid)], 3.0, STONE_SHADE, body=False)
    # Water that spills over the edge near the right end.
    f.poly([(400.0, top_chan + 2.0), (410.0, top_chan + 2.0), (412.0, deck + 30.0), (404.0, deck + 34.0), (398.0, deck + 24.0)], K.alpha(WATER, 0.85), body=False)
    f.ink([(404.0, top_chan + 6.0), (405.0, deck + 26.0)], 1.2, WATER_LIGHT)
    # The upper tier: six small arches.

    def arch(x0, x1, spring, base):
        r = (x1 - x0) / 2.0
        pts = [(x0, base), (x0, spring)]
        for k in range(1, 12):
            a = math.pi - math.pi * k / 12.0
            pts.append(((x0 + x1) / 2.0 + math.cos(a) * r, spring - math.sin(a) * r))
        pts += [(x1, spring), (x1, base)]
        return pts

    upper = 6
    span = (w - 2 * m) / upper
    for k in range(upper):
        x0 = m + k * span + 12.0
        x1 = m + (k + 1) * span - 12.0
        f.poly(arch(x0, x1, deck + 70.0, mid - 2.0), STONE_SHADE, body=False)
        _punch(f, arch(x0 + 6.0, x1, deck + 74.0, mid - 2.0))
        for j in range(9):
            a = math.pi - math.pi * (j + 0.5) / 9.0
            r = (x1 - x0) / 2.0
            c = ((x0 + x1) / 2.0, deck + 70.0)
            f.ink([(c[0] + math.cos(a) * r, c[1] - math.sin(a) * r), (c[0] + math.cos(a) * (r + 9.0), c[1] - math.sin(a) * (r + 9.0))], 1.2, STONE_SHADE)
    # The lower tier: three big arches on piers.
    lower = 3
    span = (w - 2 * m) / lower
    for k in range(lower):
        x0 = m + k * span + 22.0
        x1 = m + (k + 1) * span - 22.0
        f.poly(arch(x0, x1, mid + 90.0, foot), STONE_SHADE, body=False)
        _punch(f, arch(x0 + 10.0, x1, mid + 96.0, foot + 6.0))
        for j in range(11):
            a = math.pi - math.pi * (j + 0.5) / 11.0
            r = (x1 - x0) / 2.0
            c = ((x0 + x1) / 2.0, mid + 90.0)
            f.ink([(c[0] + math.cos(a) * r, c[1] - math.sin(a) * r), (c[0] + math.cos(a) * (r + 12.0), c[1] - math.sin(a) * (r + 12.0))], 1.4, STONE_SHADE)
    # Courses of stone on the piers, and a weed or two.
    for y in range(int(deck) + 16, int(foot), 22):
        for k in range(lower + 1):
            x = m + k * span
            f.ink([(max(m, x - 22.0), y), (min(w - m, x + 22.0), y)], 0.8, K.alpha(STONE_SHADE, 0.7))
    for k in range(5):
        x = rng.uniform(m + 10.0, w - m - 10.0)
        f.ink([(x, mid - 1.0), (x - 3.0, mid - 8.0)], 1.2, H.OLIVE)
        f.ink([(x, mid - 1.0), (x + 3.0, mid - 7.0)], 1.2, H.OLIVE)
    f.poly([(m, foot - 6.0), (w - m, foot - 6.0), (w - m, foot), (m, foot)], STONE_SHADE, body=False)
    return f.finish(outline=H.SEPIA_INK, width=2.0)


def _amphora(f: K.Frame, cx: float, foot: float, height: float, lean: float, colour) -> None:
    """One amphora standing on its point at `foot`, leaning `lean` degrees."""
    s = height / 80.0

    def P(pts):
        return K.turn([(cx + x * s, foot - y * s) for x, y in pts], cx, foot, lean)

    body = [(0.0, 0.0), (6.0, 8.0), (14.0, 26.0), (17.0, 44.0), (14.0, 58.0), (7.0, 64.0), (5.0, 72.0), (7.0, 76.0), (7.0, 80.0), (-7.0, 80.0),
            (-7.0, 76.0), (-5.0, 72.0), (-7.0, 64.0), (-14.0, 58.0), (-17.0, 44.0), (-14.0, 26.0), (-6.0, 8.0)]
    f.poly(P(body), colour)
    f.poly(P([(6.0, 8.0), (14.0, 26.0), (17.0, 44.0), (14.0, 58.0), (8.0, 58.0), (10.0, 40.0), (6.0, 16.0)]), K.shade(colour, 0.78), body=False)
    # The handles, from the neck to the shoulder.
    for side in (-1.0, 1.0):
        f.limb(P([(side * 5.0, 74.0), (side * 13.0, 74.0), (side * 14.0, 62.0)]), 2.6 * s, K.shade(colour, 0.9))
    # Black bands and a key pattern round the belly.
    f.poly(P([(-16.6, 46.0), (16.6, 46.0), (16.0, 38.0), (-16.0, 38.0)]), BLACK_FIGURE, body=False)
    pts = []
    for k in range(8):
        x = -14.0 + k * 4.0
        pts += [(x, 39.5), (x, 44.5), (x + 2.0, 44.5), (x + 2.0, 41.5)]
    f.ink(P(pts), 0.9 * s + 0.3, colour)
    f.limb(P([(-14.0, 26.0), (14.0, 26.0)]), 1.6 * s, BLACK_FIGURE, body=False)
    f.ink(P([(-10.0, 54.0), (-8.0, 30.0)]), 1.4, K.alpha(K.WHITE, 0.5))


def _draw_amphorae(anim, i, n):
    w, h = AMPHORAE_FRAME
    f = K.Frame(AMPHORAE_FRAME)
    foot = h - 6.0
    # The stand: two rails on four legs; the amphorae sit in its rings.
    for x in (14.0, 50.0, 78.0, 114.0):
        f.limb([(x, foot), (x + (4.0 if x < 64 else -4.0), foot - 46.0)], 3.6, K.WOOD_DARK)
    _amphora(f, 40.0, foot - 4.0, 88.0, -6.0, H.TERRACOTTA)
    _amphora(f, 90.0, foot - 4.0, 80.0, 8.0, K.shade(H.TERRACOTTA, 1.08))
    _amphora(f, 64.0, foot - 2.0, 96.0, 0.0, K.shade(H.TERRACOTTA, 0.95))
    f.limb([(10.0, foot - 40.0), (118.0, foot - 40.0)], 4.0, K.WOOD)
    f.limb([(12.0, foot - 12.0), (116.0, foot - 12.0)], 3.4, K.WOOD)
    return f.finish(outline=H.SEPIA_INK, width=1.6)


def _draw_stoa_gate(anim, i, n):
    w, h = STOA_FRAME
    f = K.Frame(STOA_FRAME)
    m = 6.0
    # The lintel with a band of key pattern, and the threshold.
    f.poly([(m, m), (w - m, m), (w - m, m + 26.0), (m, m + 26.0)], H.MARBLE)
    f.poly([(m + 4.0, m + 8.0), (w - m - 4.0, m + 8.0), (w - m - 4.0, m + 20.0), (m + 4.0, m + 20.0)], H.AEGEAN, body=False)
    pts = []
    for k in range(10):
        x = m + 6.0 + k * 8.0
        pts += [(x, m + 18.0), (x, m + 10.0), (x + 6.0, m + 10.0), (x + 6.0, m + 15.0), (x + 3.0, m + 15.0)]
    f.ink(pts, 1.4, H.MARBLE)
    f.poly([(m, h - m - 14.0), (w - m, h - m - 14.0), (w - m, h - m), (m, h - m)], H.MARBLE)
    f.poly([(w - m - 20.0, h - m - 14.0), (w - m, h - m - 14.0), (w - m, h - m), (w - m - 20.0, h - m)], H.MARBLE_SHADE, body=False)
    # The bronze double door.
    d0, d1, top, bot = m + 16.0, w - m - 16.0, m + 26.0, h - m - 14.0
    f.poly([(d0, top), (d1, top), (d1, bot), (d0, bot)], H.BRONZE)
    f.poly([(d1 - 10.0, top), (d1, top), (d1, bot), (d1 - 10.0, bot)], H.BRONZE_DARK, body=False)
    f.ink([(w / 2.0, top), (w / 2.0, bot)], 1.6, H.BRONZE_DARK)
    for y in (top + 30.0, bot - 30.0):
        f.ink([(d0, y), (d1, y)], 1.4, H.BRONZE_DARK)
    for y in (top + 14.0, top + 46.0, bot - 46.0, bot - 14.0):
        for x in (d0 + 6.0, w / 2.0 - 6.0, w / 2.0 + 6.0, d1 - 6.0):
            f.ellipse(x, y, 2.2, 2.2, H.BRONZE_LIGHT, body=False)
    for x in (w / 2.0 - 8.0, w / 2.0 + 8.0):
        f.ellipse(x, h * 0.66, 5.0, 5.0, H.BRONZE_DARK, body=False)
        f.ellipse(x, h * 0.66, 3.4, 3.4, H.BRONZE, body=False)
    # The question mark: big, embossed in gold, in the middle of the door.
    cy = h * 0.42
    curve = [(w / 2.0 - 14.0, cy - 30.0), (w / 2.0 - 8.0, cy - 42.0), (w / 2.0 + 4.0, cy - 44.0), (w / 2.0 + 14.0, cy - 36.0), (w / 2.0 + 14.0, cy - 22.0),
             (w / 2.0 + 4.0, cy - 12.0), (w / 2.0, cy - 2.0), (w / 2.0, cy + 6.0)]
    f.limb(curve, 9.0, H.BRONZE_DARK, body=False)
    f.limb(curve, 6.0, K.GOLD, body=False)
    f.ellipse(w / 2.0, cy + 20.0, 5.6, 5.6, H.BRONZE_DARK, body=False)
    f.ellipse(w / 2.0, cy + 20.0, 4.0, 4.0, K.GOLD, body=False)
    f.ink([curve[1], curve[2]], 1.2, K.alpha(K.WHITE, 0.8))
    # The two small columns at its sides.
    for x0 in (m, w - m - 16.0):
        _fluted_shaft(f, x0 + 1.0, x0 + 15.0, top + 4.0, bot, taper=0.0)
        f.poly([(x0 - 1.0, top), (x0 + 17.0, top), (x0 + 17.0, top + 6.0), (x0 - 1.0, top + 6.0)], H.MARBLE)
        f.poly([(x0 - 1.0, bot - 4.0), (x0 + 17.0, bot - 4.0), (x0 + 17.0, bot + 1.0), (x0 - 1.0, bot + 1.0)], H.MARBLE)
    return f.finish(outline=H.SEPIA_INK, width=1.8)


def _draw_bust(anim, i, n):
    w, h = BUST_FRAME
    f = K.Frame(BUST_FRAME)
    foot = h - 6.0
    cx = w / 2.0
    # The plinth: a tall block with a cornice and a name panel.
    f.poly([(cx - 26.0, foot), (cx + 26.0, foot), (cx + 26.0, foot - 8.0), (cx - 26.0, foot - 8.0)], H.MARBLE)
    f.poly([(cx - 20.0, foot - 8.0), (cx + 20.0, foot - 8.0), (cx + 20.0, foot - 90.0), (cx - 20.0, foot - 90.0)], H.MARBLE)
    f.poly([(cx + 8.0, foot - 8.0), (cx + 20.0, foot - 8.0), (cx + 20.0, foot - 90.0), (cx + 8.0, foot - 90.0)], H.MARBLE_SHADE, body=False)
    f.poly([(cx - 25.0, foot - 90.0), (cx + 25.0, foot - 90.0), (cx + 25.0, foot - 98.0), (cx - 25.0, foot - 98.0)], H.MARBLE)
    f.poly([(cx - 13.0, foot - 64.0), (cx + 13.0, foot - 64.0), (cx + 13.0, foot - 50.0), (cx - 13.0, foot - 50.0)], H.MARBLE_SHADE, body=False)
    for k in range(4):
        f.ink([(cx - 10.0 + k * 6.0, foot - 59.0), (cx - 6.0 + k * 6.0, foot - 59.0)], 1.4, H.SEPIA_INK)
    # The bust: shoulders in a draped toga, a neck, a stern bald head.
    base = foot - 98.0
    f.poly([(cx - 26.0, base), (cx + 26.0, base), (cx + 22.0, base - 22.0), (cx + 8.0, base - 30.0), (cx - 8.0, base - 30.0), (cx - 22.0, base - 22.0)],
           H.MARBLE)
    f.ink([(cx - 20.0, base - 20.0), (cx - 4.0, base - 6.0), (cx + 6.0, base - 2.0)], 1.4, H.MARBLE_SHADE)
    f.ink([(cx + 4.0, base - 26.0), (cx + 14.0, base - 12.0)], 1.4, H.MARBLE_SHADE)
    f.poly([(cx - 7.0, base - 26.0), (cx + 7.0, base - 26.0), (cx + 6.0, base - 40.0), (cx - 6.0, base - 40.0)], H.MARBLE)
    hy = base - 56.0
    f.ellipse(cx, hy, 15.0, 18.0, H.MARBLE)
    f.poly([(cx + 4.0, hy - 16.0), (cx + 15.0, hy - 6.0), (cx + 14.0, hy + 10.0), (cx + 4.0, hy + 16.0)], H.MARBLE_SHADE, body=False)
    f.ellipse(cx - 14.0, hy + 1.0, 3.0, 5.0, H.MARBLE)
    f.ellipse(cx + 14.0, hy + 1.0, 3.0, 5.0, H.MARBLE_SHADE)
    # A stern face: blank eyes under a heavy brow, a long nose.
    f.ink([(cx - 10.0, hy - 6.0), (cx - 3.0, hy - 4.0)], 1.8, H.MARBLE_SHADE)
    f.ink([(cx + 3.0, hy - 4.0), (cx + 10.0, hy - 6.0)], 1.8, H.MARBLE_SHADE)
    f.ellipse(cx - 6.0, hy - 1.0, 2.6, 1.6, K.alpha(H.MARBLE_SHADE, 0.8), body=False)
    f.ellipse(cx + 6.0, hy - 1.0, 2.6, 1.6, K.alpha(H.MARBLE_SHADE, 0.8), body=False)
    f.poly([(cx - 1.0, hy - 3.0), (cx + 1.0, hy - 3.0), (cx + 2.6, hy + 7.0), (cx - 2.6, hy + 7.0)], K.shade(H.MARBLE, 0.95), body=False)
    f.ink([(cx - 5.0, hy + 12.0), (cx + 5.0, hy + 12.0)], 1.4, H.MARBLE_SHADE)
    f.ink([(cx - 9.0, hy - 15.0), (cx + 9.0, hy - 15.0)], 1.0, K.alpha(H.MARBLE_SHADE, 0.6))
    # The moustache that somebody painted on him, and a drip of the paint.
    for side in (-1.0, 1.0):
        pts = [(cx + side * 1.0, hy + 9.0), (cx + side * 6.0, hy + 10.0), (cx + side * 11.0, hy + 8.0), (cx + side * 14.0, hy + 4.0),
               (cx + side * 13.0, hy + 1.0), (cx + side * 10.6, hy + 2.6)]
        f.ink(pts, 3.0, PAINT)
    f.limb([(cx + 3.0, hy + 10.5), (cx + 3.4, hy + 17.0)], 1.6, PAINT, body=False)
    f.ellipse(cx + 3.4, hy + 17.6, 1.4, 1.6, PAINT, body=False)
    f.ink([(cx - 5.0, hy + 9.4), (cx - 2.0, hy + 9.4)], 0.8, (110, 104, 124, 255))
    return f.finish(outline=H.SEPIA_INK, width=1.6)


def _scenery(name: str, display: str, frame, draw, foot):
    return _publisher(name, display, STILL, frame, draw, {"foot": foot}, "Scenery", ["prop", "scenery", "history", "classical"])


FRAMES = {
    "history_marble_column": COLUMN_FRAME,
    "history_broken_column": BROKEN_FRAME,
    "history_aqueduct": AQUEDUCT_FRAME,
    "history_amphorae": AMPHORAE_FRAME,
    "history_stoa_gate": STOA_FRAME,
    "history_bust": BUST_FRAME,
}
DRAW = {
    "history_marble_column": _draw_column,
    "history_broken_column": _draw_broken,
    "history_aqueduct": _draw_aqueduct,
    "history_amphorae": _draw_amphorae,
    "history_stoa_gate": _draw_stoa_gate,
    "history_bust": _draw_bust,
}

TARGETS: Dict[str, dict] = {
    "history_marble_column": _scenery("history_marble_column", "Marble Column", COLUMN_FRAME, _draw_column, (48.0, 384.0)),
    "history_broken_column": _scenery("history_broken_column", "Broken Column", BROKEN_FRAME, _draw_broken, (96.0, 192.0)),
    "history_aqueduct": _scenery("history_aqueduct", "Aqueduct", AQUEDUCT_FRAME, _draw_aqueduct, (256.0, 384.0)),
    "history_amphorae": _scenery("history_amphorae", "Amphorae", AMPHORAE_FRAME, _draw_amphorae, (64.0, 128.0)),
    "history_stoa_gate": _publisher("history_stoa_gate", "Stoa Gate", STILL, STOA_FRAME, _draw_stoa_gate, {"foot": (48.0, 384.0)}, "Door",
                                    ["prop", "door", "lock", "history", "classical"], forward=(0.0, -1.0)),
    "history_bust": _scenery("history_bust", "Bust", BUST_FRAME, _draw_bust, (48.0, 192.0)),
}
