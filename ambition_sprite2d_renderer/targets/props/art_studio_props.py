"""The props of the Art dimension's concept sheets that are things to use.

- ``art_brush_seesaw``: a big paint brush that lies flat and rocks on its
  middle: the look of a swinging plank (`MovingPlatform` with `line` and
  `swing`). Its top surface is the platform (`platform_looks.ron`:
  `SEESAW_SPAN`, `SEESAW_TOP`). The renderer turns it with the plank.
- ``art_crayon_rail``: a giant crayon that lies on its side and rides to and
  fro: the look of a sweeping platform. Its top is the platform
  (`CRAYON_SPAN`, `CRAYON_TOP`).
- ``art_scribble_wall``: a wall of pencil scribble, the look of a `LockWall`
  of 48 by 192 world units. An eraser switch rubs it out.
- ``art_eraser``: a big pink eraser on a stand, the scenery behind the
  switch that rubs the scribble out.

The numbers are frame pixels; the game shows each prop at half its frame.
"""

from __future__ import annotations

import math
import random

from ..characters import _art_cast_kit as K
from .art_props import STILL, _publisher

SEESAW_FRAME = (384, 64)
SEESAW_SPAN = (16.0, 368.0)
SEESAW_TOP = 22.0
CRAYON_FRAME = (320, 64)
CRAYON_SPAN = (16.0, 304.0)
CRAYON_TOP = 18.0
SCRIBBLE_FRAME = (96, 384)
ERASER_FRAME = (128, 128)

GRAPHITE = (72, 70, 84, 255)
ERASER_PINK = (246, 150, 170, 255)


def _draw_seesaw():
    f = K.Frame(SEESAW_FRAME)
    x0, x1 = SEESAW_SPAN
    top = SEESAW_TOP
    # The handle, from the left end to the ferrule.
    f.poly([(x0, top), (x0 + 220.0, top), (x0 + 220.0, top + 16.0), (x0 + 10.0, top + 14.0), (x0, top + 8.0)], K.WOOD)
    f.poly([(x0 + 10.0, top + 10.0), (x0 + 220.0, top + 11.0), (x0 + 220.0, top + 16.0), (x0 + 10.0, top + 14.0)], K.WOOD_DARK, body=False)
    f.ink([(x0 + 4.0, top + 1.2), (x0 + 218.0, top + 1.2)], 1.2, K.shade(K.WOOD, 1.35))
    # The ferrule, with its crimp.
    f.poly([(x0 + 220.0, top - 2.0), (x0 + 262.0, top - 2.0), (x0 + 262.0, top + 18.0), (x0 + 220.0, top + 18.0)], K.GOLD)
    for x in (x0 + 230.0, x0 + 252.0):
        f.ink([(x, top - 1.0), (x, top + 17.0)], 1.4, K.GOLD_DARK)
    # The bristles, loaded with paint at their tips.
    f.poly([(x0 + 262.0, top - 1.0), (x1 - 10.0, top), (x1, top + 8.0), (x1 - 12.0, top + 18.0), (x0 + 262.0, top + 17.0)], (232, 214, 180, 255))
    f.poly([(x1 - 40.0, top), (x1 - 10.0, top), (x1, top + 8.0), (x1 - 12.0, top + 18.0), (x1 - 40.0, top + 17.0)], K.MAGENTA, body=False)
    for k in range(5):
        y = top + 2.0 + k * 3.2
        f.ink([(x0 + 266.0, y), (x1 - 44.0, y + 0.4)], 0.8, K.shade((232, 214, 180, 255), 0.8))
    # The pivot it rocks on, at its middle, under the top.
    mid = (x0 + x1) / 2.0
    f.ellipse(mid, top + 22.0, 10.0, 10.0, K.GOLD_DARK)
    f.ellipse(mid, top + 22.0, 4.0, 4.0, K.INK, body=False)
    return f.finish(width=1.4)


def _draw_crayon():
    f = K.Frame(CRAYON_FRAME)
    x0, x1 = CRAYON_SPAN
    top = CRAYON_TOP
    body = K.CYAN
    # The body, then the point at the right end.
    f.poly([(x0, top), (x1 - 56.0, top), (x1 - 56.0, top + 26.0), (x0, top + 26.0)], body)
    f.poly([(x0, top + 18.0), (x1 - 56.0, top + 18.0), (x1 - 56.0, top + 26.0), (x0, top + 26.0)], K.shade(body, 0.75), body=False)
    f.poly([(x1 - 56.0, top), (x1 - 4.0, top + 11.0), (x1 - 4.0, top + 15.0), (x1 - 56.0, top + 26.0)], K.shade(body, 1.1))
    f.ellipse(x1 - 6.0, top + 13.0, 3.0, 2.4, K.shade(body, 0.6), body=False)
    # The paper wrapper with its zigzag edges and its label.
    w0, w1 = x0 + 40.0, x1 - 90.0
    f.poly([(w0, top - 1.0), (w1, top - 1.0), (w1, top + 27.0), (w0, top + 27.0)], K.WHITE)
    for edge in (w0, w1):
        f.ink([(edge, top - 1.0), (edge + 4.0, top + 6.0), (edge, top + 13.0), (edge + 4.0, top + 20.0), (edge, top + 27.0)], 1.2, K.shade(body, 0.6))
    f.poly([(w0 + 30.0, top + 6.0), (w1 - 30.0, top + 6.0), (w1 - 30.0, top + 20.0), (w0 + 30.0, top + 20.0)], K.alpha(body, 0.45), body=False)
    f.ink([(w0 + 44.0, top + 13.0), (w1 - 44.0, top + 13.0)], 1.6, K.shade(body, 0.5))
    # The worn flat end at the left.
    f.ellipse(x0 + 2.0, top + 13.0, 3.0, 12.0, K.shade(body, 0.8), body=False)
    return f.finish(width=1.4)


def _draw_scribble():
    w, h = SCRIBBLE_FRAME
    m = 6.0
    f = K.Frame(SCRIBBLE_FRAME)
    rng = random.Random("art_scribble_wall")
    # A sheet of paper, and over it a dense scribble of graphite: something
    # drawn over and over until nobody could see through it.
    f.poly([(m, m), (w - m, m), (w - m, h - m), (m, h - m)], K.PAPER)
    for _ in range(34):
        y = rng.uniform(m + 10.0, h - m - 10.0)
        pts = []
        for k in range(9):
            x = m + 6.0 + k * (w - 2 * m - 12.0) / 8.0
            pts.append((x, y + rng.uniform(-14.0, 14.0)))
        f.ink(pts, rng.uniform(1.6, 3.2), K.alpha(GRAPHITE, rng.uniform(0.6, 0.95)))
    f.ink([(m + 8.0, m + 8.0), (w - m - 8.0, h - m - 8.0)], 3.0, GRAPHITE)
    f.ink([(w - m - 8.0, m + 8.0), (m + 8.0, h - m - 8.0)], 3.0, GRAPHITE)
    return f.finish(width=1.6)


def _draw_eraser():
    w, h = ERASER_FRAME
    f = K.Frame(ERASER_FRAME)
    foot = h - 6.0
    # The stand, and the eraser on top of it, with crumbs of rubber.
    f.limb([(64.0, foot), (64.0, 70.0)], 6.0, K.WOOD_DARK)
    f.poly([(40.0, foot), (88.0, foot), (82.0, foot - 8.0), (46.0, foot - 8.0)], K.WOOD)
    block = [(22.0, 70.0), (100.0, 62.0), (108.0, 30.0), (30.0, 38.0)]
    f.poly(block, ERASER_PINK)
    f.poly([(22.0, 70.0), (100.0, 62.0), (102.0, 54.0), (24.0, 62.0)], K.shade(ERASER_PINK, 0.8), body=False)
    f.poly([(30.0, 38.0), (108.0, 30.0), (104.0, 26.0), (34.0, 34.0)], K.shade(ERASER_PINK, 1.12), body=False)
    # A band of card round its middle.
    f.poly([(56.0, 35.0), (76.0, 33.0), (72.0, 66.0), (52.0, 68.0)], K.CYAN, body=False)
    for x, y in ((16.0, 84.0), (26.0, 90.0), (108.0, 80.0)):
        f.ellipse(x, y, 2.4, 1.6, K.shade(ERASER_PINK, 0.85))
    return f.finish(width=1.6)


TARGETS = {
    "art_brush_seesaw": _publisher("art_brush_seesaw", "Brush Seesaw", STILL, SEESAW_FRAME, lambda anim, i, n: _draw_seesaw(),
                                   {"top": ((SEESAW_SPAN[0] + SEESAW_SPAN[1]) / 2.0, SEESAW_TOP)}, "Scenery", ["prop", "platform", "art"]),
    "art_crayon_rail": _publisher("art_crayon_rail", "Crayon Rail", STILL, CRAYON_FRAME, lambda anim, i, n: _draw_crayon(),
                                  {"top": ((CRAYON_SPAN[0] + CRAYON_SPAN[1]) / 2.0, CRAYON_TOP)}, "Scenery", ["prop", "platform", "art"]),
    "art_scribble_wall": _publisher("art_scribble_wall", "Scribble Wall", STILL, SCRIBBLE_FRAME, lambda anim, i, n: _draw_scribble(),
                                    {"foot": (48.0, 384.0)}, "Door", ["prop", "door", "lock", "art"], forward=(0.0, -1.0)),
    "art_eraser": _publisher("art_eraser", "Eraser", STILL, ERASER_FRAME, lambda anim, i, n: _draw_eraser(),
                             {"foot": (64.0, 128.0)}, "Scenery", ["prop", "scenery", "art"]),
}
