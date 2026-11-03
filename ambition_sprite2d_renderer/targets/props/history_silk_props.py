"""The props of the Silk Road of the History dimension (biome `history_silk`).

Dunes, an oasis and a caravanserai, drawn in the cel style of the
dimension's cast (`targets/characters/_history_cast_kit.py`): dune ochre,
crimson, saffron, jade and indigo, with a sepia outline.

- ``history_camel_caravan``: the look of a sweeping platform (as
  `art_crayon_rail`). Two Bactrian camels nose to tail with blankets and
  bags on their humps, and a long roll of carpet lashed across both: the
  top of the carpet is the platform (`platform_looks.ron`: `CARAVAN_SPAN`,
  `CARAVAN_TOP`). Its ``idle`` row walks the camels; the carpet stays level.
- ``history_silk_bolts``: scenery. Rolls of coloured silk on a wooden rack;
  one is unrolled and hangs down with a sheen.
- ``history_paper_lantern``: scenery. A red paper lantern on a post with a
  bracket; its ``idle`` row sways it a little, and it glows.
- ``history_spice_sacks``: scenery. Open sacks of saffron, black pepper and
  cinnamon sticks, with a brass scoop.
- ``history_pagoda``: scenery. A pagoda of five storeys with upturned
  eaves and a gold finial.

The numbers are frame pixels; the game shows each prop at half its frame.
No drop shadows: the game draws them.
"""

from __future__ import annotations

import math
import random
from typing import Dict, List, Tuple

from ..characters import _art_cast_kit as K
from ..characters import _history_cast_kit as H
from .art_props import _publisher

STILL: List[Tuple[str, int, int]] = [("idle", 1, 1000)]
WALK: List[Tuple[str, int, int]] = [("idle", 8, 140)]
SWAY: List[Tuple[str, int, int]] = [("idle", 6, 160)]

CARAVAN_FRAME = (320, 192)
#: The platform's top: the row of the frame the carpet's top is on, and the
#: span of its width (`data/platform_looks.ron` repeats these numbers).
CARAVAN_SPAN = (16.0, 304.0)
CARAVAN_TOP = 70.0
SILK_FRAME = (160, 128)
LANTERN_FRAME = (64, 256)
SPICE_FRAME = (160, 96)
PAGODA_FRAME = (256, 512)

CAMEL = (204, 160, 104, 255)
CAMEL_SHADE = (156, 112, 66, 255)
CAMEL_FUR = (130, 88, 50, 255)
CARPET = (168, 34, 44, 255)
CARPET_DARK = (110, 18, 30, 255)
LANTERN_RED = (214, 44, 40, 255)
LANTERN_LIGHT = (255, 196, 96, 255)
TILE = (52, 70, 84, 255)
TILE_LIGHT = (92, 116, 132, 255)
PILLAR = (184, 40, 36, 255)
WALL = (236, 222, 196, 255)
PEPPER = (46, 40, 40, 255)
CINNAMON = (150, 84, 44, 255)
BURLAP = (200, 172, 120, 255)
BURLAP_SHADE = (156, 128, 82, 255)


# ---------------------------------------------------------------------------
# The camel caravan.
# ---------------------------------------------------------------------------


def _camel(f: K.Frame, x0: float, t: float, phase0: float, blanket, bags) -> None:
    """One Bactrian camel facing right; its body spans `x0`..`x0 + 84`."""
    foot = CARAVAN_FRAME[1] - 6.0
    cyc = math.tau * t + phase0
    bx, by = x0 + 42.0, 118.0
    by += 0.8 * math.sin(cyc * 2.0)

    def a_leg(hip, swing, lift, colour):
        fx = hip[0] + 7.0 * swing
        knee = (hip[0] + 3.0 * swing + 2.0, hip[1] + 26.0 - lift * 0.5)
        ankle = (fx, foot - 3.0 - lift)
        f.limb([hip, knee], 9.0, colour)
        f.limb([knee, ankle], 6.0, colour)
        f.ellipse(knee[0], knee[1], 4.6, 4.0, K.shade(colour, 0.9))
        f.poly([(ankle[0] - 5.0, ankle[1] - 1.0), (ankle[0] + 7.0, ankle[1] - 1.0), (ankle[0] + 7.0, ankle[1] + 3.0), (ankle[0] - 5.0, ankle[1] + 3.0)],
               K.shade(colour, 0.85))

    # A pace: the two legs of one side move together.
    s_far, s_near = math.sin(cyc), -math.sin(cyc)
    l_far, l_near = 5.0 * max(0.0, math.cos(cyc)), 5.0 * max(0.0, -math.cos(cyc))
    a_leg((bx - 26.0, by + 8.0), s_far, l_far, CAMEL_SHADE)
    a_leg((bx + 24.0, by + 8.0), s_far, l_far, CAMEL_SHADE)
    # The tail.
    swish = 4.0 * math.sin(cyc * 2.0 + 1.0)
    f.limb([(bx - 40.0, by - 6.0), (bx - 46.0, by + 6.0), (bx - 46.0 + swish, by + 20.0)], 2.6, CAMEL_SHADE)
    f.ellipse(bx - 46.0 + swish, by + 22.0, 2.6, 3.6, CAMEL_FUR)
    # The body and the two humps.
    f.ellipse(bx, by, 44.0, 18.0, CAMEL)
    f.ellipse(bx - 18.0, by - 18.0, 14.0, 14.0, CAMEL_FUR)
    f.ellipse(bx + 14.0, by - 18.0, 14.0, 14.0, CAMEL_FUR)
    f.poly(K.ellipse_points(bx + 4.0, by + 8.0, 38.0, 8.0, 24), CAMEL_SHADE, body=False)
    # The neck: down from the shoulder and up to the head, with a shaggy mane.
    nod = 2.0 * math.sin(cyc * 2.0)
    head = (bx + 72.0, by - 14.0 + nod)
    neck = [(bx + 34.0, by - 8.0), (bx + 50.0, by + 4.0), (bx + 62.0, by + 2.0), (bx + 68.0, by - 8.0 + nod), head]
    f.limb(neck, 13.0, CAMEL)
    f.limb([(bx + 40.0, by + 4.0), (bx + 52.0, by + 12.0), (bx + 62.0, by + 10.0)], 6.0, CAMEL_FUR)
    hx, hy = head
    skull = [(hx - 8.0, hy - 6.0), (hx + 1.0, hy - 9.0), (hx + 12.0, hy - 6.0), (hx + 19.0, hy), (hx + 19.0, hy + 6.0), (hx + 14.0, hy + 10.0),
             (hx + 6.0, hy + 9.0), (hx - 5.0, hy + 7.0), (hx - 9.0, hy + 1.0)]
    f.poly(skull, CAMEL)
    f.poly([(hx + 6.0, hy + 9.0), (hx + 14.0, hy + 10.0), (hx + 16.0, hy + 14.0), (hx + 8.0, hy + 13.0)], CAMEL_SHADE)
    f.poly([(hx - 6.0, hy - 6.0), (hx - 9.0, hy - 13.0), (hx - 3.0, hy - 8.0)], CAMEL_SHADE)
    f.poly([(hx - 7.0, hy - 6.0), (hx - 2.0, hy - 11.0), (hx + 4.0, hy - 9.0), (hx, hy - 5.0)], CAMEL_FUR)
    f.ellipse(hx + 3.0, hy - 2.0, 2.0, 1.8, K.INK, body=False)
    f.ink([(hx + 0.5, hy - 3.6), (hx + 5.6, hy - 3.6)], 1.4, CAMEL_SHADE)
    f.ink([(hx + 15.0, hy + 1.0), (hx + 17.6, hy + 2.6)], 1.0, K.INK)
    f.ink([(hx + 12.0, hy + 8.0), (hx + 18.0, hy + 7.4)], 0.9, CAMEL_SHADE)
    # A halter of crimson with a brass ring.
    f.ink([(hx + 2.0, hy - 6.0), (hx + 4.0, hy + 8.0)], 1.6, H.CRIMSON)
    f.ink([(hx + 4.0, hy + 2.0), (hx + 16.0, hy + 3.0)], 1.6, H.CRIMSON)
    f.ellipse(hx + 6.0, hy + 9.0, 2.0, 2.0, K.GOLD)
    # The near legs, in front of the body.
    a_leg((bx - 22.0, by + 10.0), s_near, l_near, CAMEL)
    a_leg((bx + 28.0, by + 10.0), s_near, l_near, CAMEL)
    # The blanket over the humps, with tassels, and the bags at the sides.
    top = CARAVAN_TOP + 12.0
    f.poly([(bx - 36.0, top + 2.0), (bx + 32.0, top + 2.0), (bx + 38.0, by + 2.0), (bx - 40.0, by + 2.0)], blanket)
    f.poly([(bx - 36.0, top + 8.0), (bx + 34.0, top + 8.0), (bx + 35.0, top + 12.0), (bx - 37.0, top + 12.0)], H.SAFFRON, body=False)
    for k in range(8):
        x = bx - 36.0 + k * 10.6
        f.limb([(x, by + 2.0), (x, by + 6.0)], 1.6, H.SAFFRON, body=False)
    for k, (dx, colour) in enumerate(((-20.0, bags[0]), (14.0, bags[1]))):
        bag = [(bx + dx - 12.0, top + 16.0), (bx + dx + 12.0, top + 16.0), (bx + dx + 13.0, by + 10.0), (bx + dx - 13.0, by + 10.0)]
        f.poly(bag, colour)
        f.poly([(bx + dx - 12.0, top + 16.0), (bx + dx + 12.0, top + 16.0), (bx + dx + 11.0, top + 24.0), (bx + dx, top + 27.0), (bx + dx - 11.0, top + 24.0)],
               K.shade(colour, 0.75))
        f.ellipse(bx + dx, top + 24.0, 1.8, 1.8, K.GOLD, body=False)
        for j in range(3):
            f.ink([(bx + dx - 9.0 + j * 9.0, by - 2.0), (bx + dx - 6.0 + j * 9.0, by + 4.0), (bx + dx - 3.0 + j * 9.0, by - 2.0)], 1.0, K.alpha(H.SAFFRON, 0.9))


def _draw_caravan(anim, i, n):
    t = i / float(n)
    f = K.Frame(CARAVAN_FRAME)
    x0, x1 = CARAVAN_SPAN
    top = CARAVAN_TOP
    _camel(f, 22.0, t, 0.0, H.INDIGO, (H.JADE, CARPET))
    _camel(f, 160.0, t, 1.7, H.JADE_DARK, (H.INDIGO, K.shade(H.OCHRE, 0.9)))
    # The lead rope from the rear camel's halter to the front camel's bags.
    f.ink([(22.0 + 42.0 + 78.0, 118.0 - 4.0), (165.0, 108.0), (176.0, 104.0)], 1.4, K.WOOD_DARK)
    # The long roll of carpet across both: its top is the platform.
    f.poly([(x0, top), (x1, top), (x1, top + 14.0), (x0, top + 14.0)], CARPET)
    f.poly([(x0, top + 9.0), (x1, top + 9.0), (x1, top + 14.0), (x0, top + 14.0)], CARPET_DARK, body=False)
    f.ink([(x0 + 2.0, top + 1.6), (x1 - 2.0, top + 1.6)], 1.2, K.shade(CARPET, 1.3))
    for k in range(16):
        x = x0 + 10.0 + k * 18.0
        f.ink([(x, top + 3.0), (x + 6.0, top + 7.0), (x + 12.0, top + 3.0)], 1.0, K.alpha(H.SAFFRON, 0.9))
    for x in (x0, x1):
        f.ellipse(x, top + 7.0, 3.0, 7.0, CARPET_DARK)
        f.ellipse(x, top + 7.0, 1.6, 4.2, H.SAFFRON, body=False)
    # Rope lashings round the roll, one pair on each camel.
    for x in (44.0, 84.0, 182.0, 222.0):
        f.limb([(x, top - 0.5), (x + 2.0, top + 14.5)], 2.2, K.WOOD, body=False)
    return f.finish(outline=H.SEPIA_INK, width=1.6)


# ---------------------------------------------------------------------------
# Scenery.
# ---------------------------------------------------------------------------


def _draw_silk(anim, i, n):
    w, h = SILK_FRAME
    f = K.Frame(SILK_FRAME)
    foot = h - 6.0
    # The rack: two posts, two rails.
    for x in (16.0, 144.0):
        f.limb([(x, foot), (x, 30.0)], 5.0, K.WOOD_DARK)
        f.poly([(x - 8.0, foot), (x + 8.0, foot), (x + 6.0, foot - 5.0), (x - 6.0, foot - 5.0)], K.WOOD_DARK)
    f.limb([(12.0, 32.0), (148.0, 32.0)], 4.0, K.WOOD)
    f.limb([(14.0, 76.0), (146.0, 76.0)], 4.0, K.WOOD)
    # Rolls on the top rail, end on: a disc each with its spiral.
    colours = [H.CRIMSON, H.SAFFRON, H.JADE, H.INDIGO, (200, 110, 170, 255), H.AEGEAN]
    for k, c in enumerate(colours[:5]):
        cx = 30.0 + k * 25.0
        f.ellipse(cx, 22.0, 11.0, 11.0, c)
        f.ellipse(cx, 22.0, 7.0, 7.0, K.shade(c, 0.8), body=False)
        f.ellipse(cx, 22.0, 3.0, 3.0, K.WOOD, body=False)
        f.ink([(cx - 6.0, 16.0), (cx - 2.0, 13.0)], 1.2, K.alpha(K.WHITE, 0.7))
    # Rolls on the lower rail, side on, and one unrolled that hangs down.
    for k, c in enumerate(colours[2:]):
        x = 24.0 + k * 22.0
        f.poly([(x, 66.0), (x + 18.0, 66.0), (x + 18.0, 86.0), (x, 86.0)], c)
        f.ellipse(x + 18.0, 76.0, 3.0, 10.0, K.shade(c, 0.75))
    hang = [(104.0, 70.0), (136.0, 70.0), (138.0, 100.0), (134.0, 112.0), (126.0, 116.0), (116.0, 112.0), (106.0, 116.0), (102.0, 104.0)]
    f.poly(hang, H.CRIMSON)
    f.poly([(104.0, 70.0), (136.0, 70.0), (137.0, 76.0), (103.0, 76.0)], K.shade(H.CRIMSON, 0.75), body=False)
    f.ink([(112.0, 80.0), (114.0, 108.0)], 2.0, K.alpha((255, 170, 160, 255), 0.8))
    f.ink([(124.0, 80.0), (126.0, 104.0)], 1.4, K.alpha((255, 170, 160, 255), 0.6))
    f.ink([(106.0, 98.0), (118.0, 94.0), (132.0, 98.0)], 1.2, K.alpha(H.SAFFRON, 0.9))
    f.ellipse(120.0, 70.0, 18.0, 6.0, K.shade(H.CRIMSON, 0.85))
    return f.finish(outline=H.SEPIA_INK, width=1.6)


def _draw_lantern(anim, i, n):
    w, h = LANTERN_FRAME
    t = i / float(n)
    f = K.Frame(LANTERN_FRAME)
    foot = h - 6.0
    sway = 5.0 * math.sin(math.tau * t)
    # The post, its foot, the bracket arm and its brace.
    f.poly([(18.0, foot), (34.0, foot), (31.0, foot - 8.0), (21.0, foot - 8.0)], K.WOOD_DARK)
    f.limb([(26.0, foot - 6.0), (26.0, 30.0)], 6.0, K.WOOD)
    f.limb([(24.0, 32.0), (46.0, 32.0)], 4.0, K.WOOD)
    f.limb([(26.0, 50.0), (38.0, 33.0)], 2.6, K.WOOD_DARK)
    f.poly([(22.0, 26.0), (30.0, 26.0), (28.0, 20.0), (24.0, 20.0)], H.CRIMSON)
    # The lantern hangs from the end of the arm, and sways.
    px, py = 42.0, 34.0

    def S(x, y):
        return K.turn([(px + x, py + y)], px, py, -sway)[0]
    f.ink([S(0.0, 0.0), S(0.0, 12.0)], 1.2, K.INK)
    cx, cy = S(0.0, 34.0)
    f.glow(cx, cy, 15.0, K.alpha(LANTERN_LIGHT, 0.18))
    f.poly([S(-5.0, 12.0), S(5.0, 12.0), S(5.0, 16.0), S(-5.0, 16.0)], K.GOLD)
    body = [S(-6.0, 16.0), S(6.0, 16.0)] + [S(math.sin(math.pi * k / 10.0) * 14.0 + 0.0, 16.0 + 36.0 * k / 10.0) for k in range(1, 10)] + \
        [S(6.0, 52.0), S(-6.0, 52.0)] + [S(-math.sin(math.pi * k / 10.0) * 14.0, 16.0 + 36.0 * k / 10.0) for k in range(9, 0, -1)]
    f.poly(body, LANTERN_RED)
    for k in (-8.0, 0.0, 8.0):
        f.ink([S(k * 0.4, 17.0), S(k, 34.0), S(k * 0.4, 51.0)], 0.9, K.shade(LANTERN_RED, 0.7))
    f.poly([S(-4.0, 22.0), S(-1.0, 22.0), S(-1.0, 46.0), S(-4.0, 46.0)], K.alpha(LANTERN_LIGHT, 0.55), body=False)
    f.poly([S(-5.0, 52.0), S(5.0, 52.0), S(5.0, 56.0), S(-5.0, 56.0)], K.GOLD)
    # A character for luck, in gold, and the tassel.
    f.ink([S(-3.0, 30.0), S(3.0, 30.0)], 1.2, K.GOLD)
    f.ink([S(0.0, 27.0), S(0.0, 39.0)], 1.2, K.GOLD)
    f.ink([S(-3.0, 35.0), S(3.0, 35.0)], 1.2, K.GOLD)
    f.ink([S(-4.0, 39.0), S(4.0, 39.0)], 1.2, K.GOLD)
    tail = 2.0 * math.sin(math.tau * t + 1.0)
    f.limb([S(0.0, 56.0), S(0.0 + tail, 66.0)], 2.0, H.CRIMSON)
    f.poly([S(-2.6 + tail, 64.0), S(2.6 + tail, 64.0), S(3.4 + tail * 1.2, 76.0), S(-3.4 + tail * 1.2, 76.0)], H.CRIMSON)
    return f.finish(outline=H.SEPIA_INK, width=1.4, glow_blur=3.0)


def _sack(f: K.Frame, cx: float, foot: float, w: float, hgt: float, fill, kind: str, rng: random.Random) -> None:
    """An open sack with its top rolled down and its spice heaped in it."""
    body = [(cx - w * 0.5, foot), (cx + w * 0.5, foot), (cx + w * 0.56, foot - hgt * 0.6), (cx + w * 0.46, foot - hgt), (cx - w * 0.46, foot - hgt),
            (cx - w * 0.56, foot - hgt * 0.6)]
    f.poly(body, BURLAP)
    f.poly([(cx + w * 0.2, foot), (cx + w * 0.5, foot), (cx + w * 0.56, foot - hgt * 0.6), (cx + w * 0.46, foot - hgt), (cx + w * 0.2, foot - hgt)],
           BURLAP_SHADE, body=False)
    for k in range(4):
        y = foot - hgt * (0.2 + 0.2 * k)
        f.ink([(cx - w * 0.45, y), (cx + w * 0.45, y + 1.0)], 0.6, K.alpha(BURLAP_SHADE, 0.7))
    top = foot - hgt
    f.ellipse(cx, top, w * 0.5, 6.0, BURLAP_SHADE)
    if kind == "sticks":
        for k in range(7):
            x = cx - w * 0.32 + k * w * 0.1
            f.limb([(x, top + 2.0), (x + rng.uniform(-2.0, 2.0), top - 16.0 - rng.uniform(0.0, 4.0))], 3.0, CINNAMON)
            f.ink([(x - 0.5, top - 4.0), (x + 0.5, top - 12.0)], 0.6, K.shade(CINNAMON, 1.3))
        f.limb([(cx - w * 0.36, top - 6.0), (cx + w * 0.36, top - 6.0)], 1.6, H.CRIMSON, body=False)
    else:
        heap = [(cx - w * 0.44, top + 1.0), (cx - w * 0.3, top - 6.0), (cx - w * 0.1, top - 11.0), (cx + w * 0.12, top - 10.0), (cx + w * 0.32, top - 5.0),
                (cx + w * 0.44, top + 1.0)]
        f.poly(heap, fill)
        for _ in range(10):
            x = rng.uniform(cx - w * 0.3, cx + w * 0.3)
            y = rng.uniform(top - 7.0, top - 1.0)
            f.dot(x, y, 0.9, K.shade(fill, 1.35 if kind == "saffron" else 1.8))


def _draw_spices(anim, i, n):
    w, h = SPICE_FRAME
    f = K.Frame(SPICE_FRAME)
    foot = h - 6.0
    rng = random.Random("history_spice_sacks")
    _sack(f, 34.0, foot, 46.0, 48.0, PEPPER, "pepper", rng)
    _sack(f, 122.0, foot, 50.0, 44.0, CINNAMON, "sticks", rng)
    _sack(f, 78.0, foot, 54.0, 56.0, (232, 110, 30, 255), "saffron", rng)
    # A brass scoop in the saffron, and a little spill on the ground.
    f.limb([(86.0, foot - 62.0), (104.0, foot - 76.0)], 2.6, K.WOOD_DARK)
    f.poly([(76.0, foot - 64.0), (88.0, foot - 58.0), (90.0, foot - 64.0), (82.0, foot - 70.0)], K.GOLD)
    f.ellipse(60.0, foot - 1.0, 8.0, 1.8, (232, 110, 30, 255))
    return f.finish(outline=H.SEPIA_INK, width=1.6)


def _draw_pagoda(anim, i, n):
    w, h = PAGODA_FRAME
    f = K.Frame(PAGODA_FRAME)
    foot = h - 6.0
    cx = w / 2.0
    # The stone platform.
    f.poly([(cx - 104.0, foot), (cx + 104.0, foot), (cx + 98.0, foot - 16.0), (cx - 98.0, foot - 16.0)], (196, 186, 170, 255))
    f.ink([(cx - 100.0, foot - 8.0), (cx + 100.0, foot - 8.0)], 1.2, (150, 140, 126, 255))
    base = foot - 16.0
    storeys = 5
    widths = [140.0, 120.0, 102.0, 86.0, 72.0]
    heights = [92.0, 78.0, 70.0, 62.0, 56.0]
    y = base
    for k in range(storeys):
        sw, sh = widths[k], heights[k]
        half = sw / 2.0
        wall_top = y - sh + 14.0
        # The wall: red pillars and white panels with a window.
        f.poly([(cx - half, y), (cx + half, y), (cx + half, wall_top), (cx - half, wall_top)], WALL)
        f.poly([(cx + half * 0.55, y), (cx + half, y), (cx + half, wall_top), (cx + half * 0.55, wall_top)], K.shade(WALL, 0.85), body=False)
        for j in range(5):
            x = cx - half + 3.0 + j * (sw - 6.0) / 4.0
            f.poly([(x - 3.0, y), (x + 3.0, y), (x + 3.0, wall_top), (x - 3.0, wall_top)], PILLAR, body=False)
        if k == 0:
            f.poly([(cx - 14.0, y), (cx + 14.0, y), (cx + 14.0, y - 34.0), (cx, y - 42.0), (cx - 14.0, y - 34.0)], CARPET_DARK, body=False)
            f.ellipse(cx - 5.0, y - 18.0, 1.6, 1.6, K.GOLD, body=False)
            f.ellipse(cx + 5.0, y - 18.0, 1.6, 1.6, K.GOLD, body=False)
        else:
            f.poly([(cx - 8.0, y - 6.0), (cx + 8.0, y - 6.0), (cx + 8.0, wall_top + 6.0), (cx - 8.0, wall_top + 6.0)], H.INDIGO_DARK, body=False)
            f.ink([(cx, y - 6.0), (cx, wall_top + 6.0)], 1.0, K.GOLD)
        # The roof: wide eaves that turn up at their ends.
        ey = wall_top
        over = 26.0 - k * 2.0
        roof = [(cx - half - over, ey - 2.0), (cx - half - over - 8.0, ey - 20.0), (cx - half - over + 4.0, ey - 12.0), (cx - half * 0.55, ey - 24.0),
                (cx + half * 0.55, ey - 24.0), (cx + half + over - 4.0, ey - 12.0), (cx + half + over + 8.0, ey - 20.0), (cx + half + over, ey - 2.0),
                (cx + half, ey + 3.0), (cx - half, ey + 3.0)]
        f.poly(roof, TILE)
        f.poly([(cx - half - over, ey - 2.0), (cx + half + over, ey - 2.0), (cx + half, ey + 3.0), (cx - half, ey + 3.0)], K.shade(TILE, 0.7), body=False)
        f.ink([(cx - half - over + 2.0, ey - 9.0), (cx - half * 0.55, ey - 21.0), (cx + half * 0.55, ey - 21.0), (cx + half + over - 2.0, ey - 9.0)], 1.8,
              TILE_LIGHT)
        for j in range(9):
            x = cx - half * 0.9 + j * half * 0.225
            f.ink([(x, ey - 20.0), (x - 1.0, ey - 2.0)], 0.8, K.alpha(TILE_LIGHT, 0.6))
        for side in (-1.0, 1.0):
            f.ellipse(cx + side * (half + over + 8.0), ey - 20.0, 2.4, 2.4, K.GOLD)
        y = ey - 22.0
    # The finial: a gold spire of rings with a pearl on top.
    f.limb([(cx, y), (cx, y - 54.0)], 4.0, K.GOLD)
    for k in range(6):
        f.ellipse(cx, y - 8.0 - k * 7.0, 7.0 - k * 0.6, 2.0, K.GOLD_DARK)
    f.ellipse(cx, y - 60.0, 5.0, 5.0, K.GOLD)
    f.dot(cx - 1.6, y - 61.6, 1.4, K.WHITE)
    return f.finish(outline=H.SEPIA_INK, width=2.0)


def _scenery(name: str, display: str, rows, frame, draw, foot):
    return _publisher(name, display, rows, frame, draw, {"foot": foot}, "Scenery", ["prop", "scenery", "history", "silk"])


FRAMES = {
    "history_camel_caravan": CARAVAN_FRAME,
    "history_silk_bolts": SILK_FRAME,
    "history_paper_lantern": LANTERN_FRAME,
    "history_spice_sacks": SPICE_FRAME,
    "history_pagoda": PAGODA_FRAME,
}
DRAW = {
    "history_camel_caravan": _draw_caravan,
    "history_silk_bolts": _draw_silk,
    "history_paper_lantern": _draw_lantern,
    "history_spice_sacks": _draw_spices,
    "history_pagoda": _draw_pagoda,
}

TARGETS: Dict[str, dict] = {
    "history_camel_caravan": _publisher("history_camel_caravan", "Camel Caravan", WALK, CARAVAN_FRAME, _draw_caravan,
                                        {"top": ((CARAVAN_SPAN[0] + CARAVAN_SPAN[1]) / 2.0, CARAVAN_TOP)}, "Scenery",
                                        ["prop", "platform", "history", "silk"]),
    "history_silk_bolts": _scenery("history_silk_bolts", "Silk Bolts", STILL, SILK_FRAME, _draw_silk, (80.0, 128.0)),
    "history_paper_lantern": _scenery("history_paper_lantern", "Paper Lantern", SWAY, LANTERN_FRAME, _draw_lantern, (32.0, 256.0)),
    "history_spice_sacks": _scenery("history_spice_sacks", "Spice Sacks", STILL, SPICE_FRAME, _draw_spices, (80.0, 96.0)),
    "history_pagoda": _scenery("history_pagoda", "Pagoda", STILL, PAGODA_FRAME, _draw_pagoda, (128.0, 512.0)),
}
