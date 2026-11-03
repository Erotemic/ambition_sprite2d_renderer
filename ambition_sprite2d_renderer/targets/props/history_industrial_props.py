"""The props of the Industrial Age, era 8 of the History dimension.

A mill town, drawn in the cel style of the dimension's cast
(`targets/characters/_history_modern_kit.py`): flat colour, one shade, a
bold warm outline.

- ``history_chimney``: scenery, a tall brick mill chimney. Its ``idle`` row
  puffs smoke.
- ``history_steam_engine``: scenery, a beam engine on a brick bed: a
  cylinder, the rocking beam on its column, the rod and the flywheel. Its
  ``idle`` row runs it (the boiler lever of the Cotton Mill starts it; the
  room swaps nothing, the engine always runs in its picture).
- ``history_rail_wagon``: a flat railway wagon on its wheels: the look of a
  sweeping platform (as ``art_crayon_rail``). The top of its bed is the
  platform (`platform_looks.ron`: `WAGON_SPAN`, `WAGON_TOP`).
- ``history_factory_gate``: a door (the look of a `LockWall`, drawn at 3 to
  1, as ``art_colour_gate_*``): the riveted iron gate of a mill with an
  enamel sign, "NO HANDS WANTED".
- ``history_gas_lamp``: scenery, a cast-iron gas lamp, lit.

The numbers are frame pixels; the game shows each prop at half its frame.
No drop shadows: the game draws them.
"""

from __future__ import annotations

import math
import random
from typing import Dict, List, Tuple

from ..characters import _art_cast_kit as K
from ..characters import _history_modern_kit as H
from .art_props import STILL, _publisher

CHIMNEY_FRAME = (128, 512)
ENGINE_FRAME = (320, 320)
WAGON_FRAME = (320, 96)
WAGON_SPAN = (16.0, 304.0)
WAGON_TOP = 30.0
GATE_FRAME = (96, 384)
LAMP_FRAME = (64, 320)
LOOP: List[Tuple[str, int, int]] = [("idle", 8, 120)]
SCENERY = ["prop", "scenery", "history"]


def _bricks(f: K.Frame, quad_left, quad_right, y0: float, y1: float, row_h: float, colour, seed: str) -> None:
    """Courses of brick between `y0` and `y1`; `quad_left(y)` and
    `quad_right(y)` give the edges of the wall at a height."""
    rng = random.Random(seed)
    y = y1
    k = 0
    while y - row_h >= y0 - 0.01:
        l, r = quad_left(y - row_h / 2.0), quad_right(y - row_h / 2.0)
        f.ink([(l + 1.0, y), (r - 1.0, y)], 0.7, K.alpha(H.MORTAR, 0.8))
        off = 0.0 if k % 2 == 0 else 7.0
        x = l + off
        while x < r - 4.0:
            f.ink([(x, y - row_h + 0.6), (x, y - 0.6)], 0.6, K.alpha(H.MORTAR, 0.7))
            if rng.random() < 0.18:
                f.poly([(x + 1.0, y - row_h + 1.0), (x + 12.0, y - row_h + 1.0), (x + 12.0, y - 1.0), (x + 1.0, y - 1.0)],
                       K.alpha(K.shade(colour, 0.85), 0.9), body=False)
            x += 14.0
        y -= row_h
        k += 1


def _draw_chimney(i: int, n: int):
    w, h = CHIMNEY_FRAME
    f = K.Frame(CHIMNEY_FRAME)
    foot = h - 4.0
    cx = w / 2.0
    base_top, cap_y = foot - 70.0, 92.0
    # The base: a square plinth of darker brick with a stone band.
    f.poly([(cx - 44.0, foot), (cx + 44.0, foot), (cx + 44.0, base_top), (cx - 44.0, base_top)], H.BRICK_DARK)
    _bricks(f, lambda y: cx - 44.0, lambda y: cx + 44.0, base_top, foot, 8.0, H.BRICK_DARK, "chimney-base")
    f.poly([(cx - 48.0, base_top + 4.0), (cx + 48.0, base_top + 4.0), (cx + 48.0, base_top - 4.0), (cx - 48.0, base_top - 4.0)], H.MORTAR)
    f.poly([(cx - 10.0, foot), (cx + 10.0, foot), (cx + 10.0, foot - 24.0), (cx, foot - 30.0), (cx - 10.0, foot - 24.0)], H.IRON_DARK)
    # The shaft: it narrows as it rises.

    def half(y):
        return 30.0 - 10.0 * (base_top - y) / (base_top - cap_y)

    f.poly([(cx - half(base_top), base_top - 4.0), (cx + half(base_top), base_top - 4.0), (cx + half(cap_y), cap_y), (cx - half(cap_y), cap_y)], H.BRICK)
    _bricks(f, lambda y: cx - half(y), lambda y: cx + half(y), cap_y, base_top - 4.0, 8.0, H.BRICK, "chimney-shaft")
    f.poly([(cx + half(base_top) - 10.0, base_top - 4.0), (cx + half(base_top), base_top - 4.0), (cx + half(cap_y), cap_y), (cx + half(cap_y) - 7.0, cap_y)],
           K.alpha(H.BRICK_DARK, 0.6), body=False)
    # Iron bands that hold it together.
    for y in (base_top - 90.0, base_top - 190.0, base_top - 290.0):
        f.poly([(cx - half(y) - 1.0, y), (cx + half(y) + 1.0, y), (cx + half(y) + 1.0, y - 4.0), (cx - half(y) - 1.0, y - 4.0)], H.IRON_DARK)
    # The cap: corbelled courses that step out, black with soot.
    for k, (dy, d) in enumerate(((0.0, 2.0), (-6.0, 5.0), (-12.0, 7.0))):
        y = cap_y + dy
        f.poly([(cx - half(cap_y) - d, y), (cx + half(cap_y) + d, y), (cx + half(cap_y) + d, y - 6.0), (cx - half(cap_y) - d, y - 6.0)],
               K.shade(H.BRICK, 0.85 - 0.12 * k))
    f.poly([(cx - half(cap_y) - 7.0, cap_y - 18.0), (cx + half(cap_y) + 7.0, cap_y - 18.0), (cx + half(cap_y) + 5.0, cap_y - 22.0),
            (cx - half(cap_y) - 5.0, cap_y - 22.0)], H.SOOT)
    # The smoke: puffs that rise and drift to the right, a loop.
    t = i / float(n)
    for k in range(4):
        u = (t + k / 4.0) % 1.0
        x = cx + 2.0 + 18.0 * u + 4.0 * math.sin(u * 6.0)
        y = cap_y - 30.0 - 54.0 * u
        r = 9.0 + 9.0 * u
        H.puff(f, min(w - r - 6.0, x), max(r + 6.0, y), r, K.alpha(H.SOOT_LIGHT, 0.95 - 0.5 * u), random.Random(f"chimney:{k}"), 5,
               body=True, shade_colour=K.alpha(H.SOOT, 0.5 * (1.0 - u)))
    return H.finish(f, width=1.6)


def _draw_engine(i: int, n: int):
    w, h = ENGINE_FRAME
    f = K.Frame(ENGINE_FRAME)
    foot = h - 4.0
    t = i / float(n)
    turn = math.tau * t
    # The bed: a block of brick with a stone top.
    bed_top = foot - 62.0
    f.poly([(14.0, foot), (w - 14.0, foot), (w - 14.0, bed_top), (14.0, bed_top)], H.BRICK)
    _bricks(f, lambda y: 14.0, lambda y: w - 14.0, bed_top, foot, 8.0, H.BRICK, "engine-bed")
    f.poly([(10.0, bed_top + 4.0), (w - 10.0, bed_top + 4.0), (w - 10.0, bed_top - 4.0), (10.0, bed_top - 4.0)], H.MORTAR)
    # The flywheel turns in a pit at the right end of the bed.
    fx, fy, fr = 236.0, 186.0, 62.0
    f.ellipse(fx, fy, fr, fr, H.IRON_DARK)
    f.ellipse(fx, fy, fr - 9.0, fr - 9.0, K.alpha(H.SOOT, 0.35), body=False)
    H.ring(f, fx, fy, fr - 3.0, fr - 3.0, 1.2, H.IRON_LIGHT, 40)
    for k in range(6):
        a = turn + math.tau * k / 6.0
        f.limb([(fx + math.cos(a) * 8.0, fy + math.sin(a) * 8.0), (fx + math.cos(a) * (fr - 8.0), fy + math.sin(a) * (fr - 8.0))], 5.0, H.IRON)
    f.ellipse(fx, fy, 11.0, 11.0, H.IRON)
    f.ellipse(fx, fy, 4.0, 4.0, H.BRASS)
    # The crank on the wheel and the beam it drives.
    crank = (fx + math.cos(turn) * 30.0, fy + math.sin(turn) * 30.0)
    px, py = 150.0, 70.0
    tilt = math.degrees(math.asin(max(-1.0, min(1.0, (crank[1] - fy) / 110.0)))) * 0.9
    a = math.radians(tilt)
    left_end = (px - math.cos(a) * 104.0, py - math.sin(a) * 104.0)
    right_end = (px + math.cos(a) * 92.0, py + math.sin(a) * 92.0)
    # The column the beam rocks on.
    f.poly([(px - 9.0, bed_top - 4.0), (px + 9.0, bed_top - 4.0), (px + 6.0, py + 8.0), (px - 6.0, py + 8.0)], H.IRON)
    f.poly([(px - 9.0, bed_top - 4.0), (px - 3.0, bed_top - 4.0), (px - 2.0, py + 8.0), (px - 6.0, py + 8.0)], H.IRON_DARK, body=False)
    f.poly([(px - 16.0, bed_top - 4.0), (px + 16.0, bed_top - 4.0), (px + 12.0, bed_top - 14.0), (px - 12.0, bed_top - 14.0)], H.IRON_DARK)
    # The cylinder at the left, with its piston rod up to the beam.
    cyl_x = left_end[0] + 8.0
    f.poly([(cyl_x - 22.0, bed_top - 4.0), (cyl_x + 22.0, bed_top - 4.0), (cyl_x + 22.0, bed_top - 88.0), (cyl_x - 22.0, bed_top - 88.0)], H.IRON)
    f.poly([(cyl_x - 22.0, bed_top - 4.0), (cyl_x - 12.0, bed_top - 4.0), (cyl_x - 12.0, bed_top - 88.0), (cyl_x - 22.0, bed_top - 88.0)],
           H.IRON_DARK, body=False)
    for y in (bed_top - 8.0, bed_top - 84.0):
        f.poly([(cyl_x - 25.0, y + 3.0), (cyl_x + 25.0, y + 3.0), (cyl_x + 25.0, y - 3.0), (cyl_x - 25.0, y - 3.0)], H.BRASS)
    f.limb([(cyl_x, bed_top - 88.0), left_end], 4.0, H.STEEL)
    # A whiff of steam from the valve, once a stroke.
    if math.sin(turn) > 0.3:
        H.puff(f, cyl_x + 28.0, bed_top - 70.0, 7.0, K.alpha(H.STEAM, 0.9), random.Random(f"valve:{i}"), 5, body=False)
    # The connecting rod from the right end of the beam to the crank.
    f.limb([right_end, crank], 5.0, H.STEEL)
    f.ellipse(crank[0], crank[1], 5.0, 5.0, H.BRASS)
    # The beam: a long iron girder, deep in the middle.
    beam = [(left_end[0], left_end[1] - 4.0), (px, py - 10.0), (right_end[0], right_end[1] - 4.0), (right_end[0], right_end[1] + 4.0), (px, py + 10.0),
            (left_end[0], left_end[1] + 4.0)]
    f.poly(beam, H.IRON_DARK)
    f.ink([(left_end[0] + 4.0, left_end[1] - 1.5), (px, py - 6.0), (right_end[0] - 4.0, right_end[1] - 1.5)], 1.0, H.IRON_LIGHT)
    for e in (left_end, right_end):
        f.ellipse(e[0], e[1], 4.4, 4.4, H.BRASS)
    f.ellipse(px, py, 7.0, 7.0, H.BRASS)
    f.dot(px, py, 2.4, H.OUTLINE)
    # The governor on the column: two balls that fly out as it runs.
    gx, gy = px + 30.0, bed_top - 14.0
    f.limb([(gx, bed_top - 4.0), (gx, gy - 30.0)], 2.4, H.IRON)
    spread = 10.0 + 2.0 * math.sin(turn * 2.0)
    for s in (-1.0, 1.0):
        bx = gx + s * spread * math.cos(turn)
        f.ink([(gx, gy - 30.0), (bx, gy - 16.0)], 1.0, H.IRON_DARK)
        f.ellipse(bx, gy - 16.0, 4.0, 4.0, H.BRASS)
    return H.finish(f, width=1.6)


def _draw_wagon():
    w, h = WAGON_FRAME
    f = K.Frame(WAGON_FRAME)
    x0, x1 = WAGON_SPAN
    top = WAGON_TOP
    wy, wr = 66.0, 22.0
    # The wheels: iron, with spokes, a flange and a hub.
    for wx in (82.0, 238.0):
        f.ellipse(wx, wy, wr, wr, H.IRON_DARK)
        f.ellipse(wx, wy, wr - 4.0, wr - 4.0, H.IRON, body=False)
        for k in range(8):
            a = math.tau * k / 8.0 + 0.2
            f.ink([(wx, wy), (wx + math.cos(a) * (wr - 4.0), wy + math.sin(a) * (wr - 4.0))], 1.6, H.IRON_DARK)
        f.ellipse(wx, wy, 5.0, 5.0, H.IRON_DARK)
        f.dot(wx, wy, 1.8, H.BRASS)
        # The axle box and its leaf spring over the wheel.
        f.poly([(wx - 10.0, 48.0), (wx + 10.0, 48.0), (wx + 8.0, wy - 2.0), (wx - 8.0, wy - 2.0)], H.IRON_DARK)
        f.ink([(wx - 24.0, 46.0), (wx, 51.0), (wx + 24.0, 46.0)], 2.0, H.IRON_LIGHT)
    # The solebar: the iron beam along the side, with rivets.
    f.poly([(x0, top + 10.0), (x1, top + 10.0), (x1, top + 20.0), (x0, top + 20.0)], H.IRON)
    f.poly([(x0, top + 16.0), (x1, top + 16.0), (x1, top + 20.0), (x0, top + 20.0)], H.IRON_DARK, body=False)
    for k in range(18):
        f.dot(x0 + 8.0 + k * 16.0, top + 13.0, 1.0, H.IRON_LIGHT)
    # The buffers at each end, and the coupling hooks.
    for side, x in ((-1.0, x0), (1.0, x1)):
        f.poly([(x, top + 11.0), (x + side * 6.0, top + 11.0), (x + side * 6.0, top + 19.0), (x, top + 19.0)], H.IRON_DARK)
        f.ellipse(x + side * 8.0, top + 15.0, 2.4, 6.0, H.STEEL)
        f.ink([(x, top + 22.0), (x + side * 7.0, top + 24.0), (x + side * 8.0, top + 28.0)], 1.6, H.IRON_DARK)
    # The bed: oak planks; their top is the platform.
    f.poly([(x0, top), (x1, top), (x1, top + 10.0), (x0, top + 10.0)], H.OAK)
    f.poly([(x0, top + 6.0), (x1, top + 6.0), (x1, top + 10.0), (x0, top + 10.0)], H.OAK_DARK, body=False)
    for k in range(1, 12):
        x = x0 + k * (x1 - x0) / 12.0
        f.ink([(x, top + 1.0), (x, top + 9.0)], 0.8, H.OAK_DARK)
    f.ink([(x0 + 2.0, top + 1.2), (x1 - 2.0, top + 1.2)], 1.0, H.OAK_LIGHT)
    # The owner's mark painted on the solebar.
    H.text(f, (x0 + x1) / 2.0, top + 15.0, "L & M R", 7.0, H.CANVAS)
    return H.finish(f, width=1.4)


def _draw_gate():
    w, h = GATE_FRAME
    f = K.Frame(GATE_FRAME)
    m = 4.5
    # The frame: iron plates, from the top of the box to its foot (with a
    # small margin), heavy rivets round the edge.
    f.poly([(m, m), (w - m, m), (w - m, h - m), (m, h - m)], H.IRON)
    f.poly([(w - 16.0, m), (w - m, m), (w - m, h - m), (w - 16.0, h - m)], H.IRON_DARK, body=False)
    f.poly([(m, m), (14.0, m), (14.0, h - m), (m, h - m)], H.IRON_LIGHT, body=False)
    for y in (m + 4.0, 128.0, 256.0, h - m - 4.0):
        f.ink([(m, y), (w - m, y)], 1.4, H.IRON_DARK)
    for y in [m + 10.0 + k * 18.6 for k in range(20)]:
        for x in (9.0, w - 9.0):
            f.dot(x, y, 1.6, H.IRON_DARK)
            f.dot(x - 0.4, y - 0.4, 0.7, H.IRON_LIGHT)
    # Bars in the upper panel, with the dark of the mill behind them.
    f.poly([(18.0, 24.0), (w - 18.0, 24.0), (w - 18.0, 120.0), (18.0, 120.0)], H.SOOT)
    for k in range(5):
        x = 22.0 + k * (w - 44.0) / 4.0
        f.limb([(x, 24.0), (x, 120.0)], 4.0, H.IRON_DARK)
    f.limb([(18.0, 72.0), (w - 18.0, 72.0)], 3.0, H.IRON_DARK)
    # The lower panels: plates with a cross brace.
    for y0, y1 in ((136.0, 248.0), (264.0, 370.0)):
        f.poly([(18.0, y0), (w - 18.0, y0), (w - 18.0, y1), (18.0, y1)], K.shade(H.IRON, 0.92), body=False)
        f.ink([(20.0, y0 + 2.0), (w - 20.0, y1 - 2.0)], 3.0, H.IRON_DARK)
        f.ink([(w - 20.0, y0 + 2.0), (20.0, y1 - 2.0)], 3.0, H.IRON_DARK)
    # A streak of rust.
    f.ink([(70.0, 260.0), (71.0, 300.0), (69.0, 330.0)], 2.0, K.alpha((150, 76, 40, 255), 0.6))
    # The sign: white enamel with a black rim, on two bolts.
    sx0, sx1, sy0, sy1 = 10.0, w - 10.0, 150.0, 206.0
    f.poly([(sx0, sy0), (sx1, sy0), (sx1, sy1), (sx0, sy1)], H.CANVAS)
    f.ink([(sx0 + 2.5, sy0 + 2.5), (sx1 - 2.5, sy0 + 2.5), (sx1 - 2.5, sy1 - 2.5), (sx0 + 2.5, sy1 - 2.5), (sx0 + 2.5, sy0 + 2.5)], 1.4, H.SOOT)
    H.text(f, w / 2.0, sy0 + 14.0, "NO HANDS", 10.5, H.SOOT)
    H.text(f, w / 2.0, sy0 + 31.0, "WANTED", 13.0, H.SEAL_RED)
    f.ink([(sx0 + 10.0, sy1 - 10.0), (sx1 - 10.0, sy1 - 10.0)], 1.0, K.alpha(H.SOOT, 0.6))
    for x in (sx0 + 5.0, sx1 - 5.0):
        f.dot(x, sy1 - 6.0, 1.6, H.IRON_DARK)
    # A chip in the enamel.
    f.poly([(sx1 - 14.0, sy0 + 3.0), (sx1 - 8.0, sy0 + 3.0), (sx1 - 10.0, sy0 + 8.0)], H.SOOT, body=False)
    return H.finish(f, width=1.4)


def _draw_lamp():
    w, h = LAMP_FRAME
    f = K.Frame(LAMP_FRAME)
    foot = h - 4.0
    cx = w / 2.0
    # The foot and the fluted column.
    f.poly([(cx - 16.0, foot), (cx + 16.0, foot), (cx + 12.0, foot - 12.0), (cx - 12.0, foot - 12.0)], H.TAR)
    f.poly([(cx - 10.0, foot - 12.0), (cx + 10.0, foot - 12.0), (cx + 7.0, foot - 40.0), (cx - 7.0, foot - 40.0)], H.TAR)
    f.poly([(cx - 4.5, foot - 40.0), (cx + 4.5, foot - 40.0), (cx + 3.0, 92.0), (cx - 3.0, 92.0)], H.TAR)
    f.ink([(cx + 1.6, foot - 42.0), (cx + 1.2, 94.0)], 0.8, H.TAR_LIGHT)
    for y in (foot - 40.0, 150.0, 96.0):
        f.ellipse(cx, y, 6.0, 2.4, H.TAR)
    # The ladder bar the lamplighter leans his ladder on.
    f.limb([(cx - 18.0, 100.0), (cx + 18.0, 100.0)], 2.6, H.TAR)
    for s in (-1.0, 1.0):
        f.ellipse(cx + s * 18.0, 100.0, 2.4, 2.4, H.TAR)
    # The lantern: a cap, four panes of glass with the flame inside.
    f.poly([(cx - 6.0, 92.0), (cx + 6.0, 92.0), (cx + 10.0, 84.0), (cx - 10.0, 84.0)], H.TAR)
    f.poly([(cx - 10.0, 84.0), (cx + 10.0, 84.0), (cx + 15.0, 42.0), (cx - 15.0, 42.0)], H.GASLIGHT)
    f.poly([(cx - 4.0, 84.0), (cx + 4.0, 84.0), (cx + 5.0, 42.0), (cx - 5.0, 42.0)], H.GASLIGHT_HOT, body=False)
    for x0, x1 in ((-10.0, -15.0), (0.0, 0.0), (10.0, 15.0)):
        f.ink([(cx + x0, 84.0), (cx + x1, 42.0)], 1.4, H.TAR)
    f.ellipse(cx, 66.0, 2.4, 4.0, H.WHITE, body=False)
    f.poly([(cx - 18.0, 42.0), (cx + 18.0, 42.0), (cx + 8.0, 30.0), (cx - 8.0, 30.0)], H.TAR)
    f.limb([(cx, 30.0), (cx, 22.0)], 2.0, H.TAR)
    f.ellipse(cx, 20.0, 3.0, 3.0, H.TAR)
    f.glow(cx, 64.0, 18.0, K.alpha(H.GASLIGHT, 0.55))
    return H.finish(f, width=1.4)


TARGETS: Dict[str, dict] = {
    "history_chimney": _publisher("history_chimney", "Mill Chimney", LOOP, CHIMNEY_FRAME, lambda anim, i, n: _draw_chimney(i, n),
                                  {"foot": (64.0, 512.0)}, "Scenery", SCENERY),
    "history_steam_engine": _publisher("history_steam_engine", "Beam Engine", LOOP, ENGINE_FRAME, lambda anim, i, n: _draw_engine(i, n),
                                       {"foot": (160.0, 320.0)}, "Scenery", SCENERY),
    "history_rail_wagon": _publisher("history_rail_wagon", "Rail Wagon", STILL, WAGON_FRAME, lambda anim, i, n: _draw_wagon(),
                                     {"top": ((WAGON_SPAN[0] + WAGON_SPAN[1]) / 2.0, WAGON_TOP)}, "Scenery", ["prop", "platform", "history"]),
    "history_factory_gate": _publisher("history_factory_gate", "Factory Gate", STILL, GATE_FRAME, lambda anim, i, n: _draw_gate(),
                                       {"foot": (48.0, 384.0)}, "Door", ["prop", "door", "lock", "history"], forward=(0.0, -1.0)),
    "history_gas_lamp": _publisher("history_gas_lamp", "Gas Lamp", STILL, LAMP_FRAME, lambda anim, i, n: _draw_lamp(), {"foot": (32.0, 320.0)},
                                   "Scenery", SCENERY),
}

#: The drawing of each target, by its row (for previews).
DRAW = {
    "history_chimney": lambda anim, i, n: _draw_chimney(i, n),
    "history_steam_engine": lambda anim, i, n: _draw_engine(i, n),
    "history_rail_wagon": lambda anim, i, n: _draw_wagon(),
    "history_factory_gate": lambda anim, i, n: _draw_gate(),
    "history_gas_lamp": lambda anim, i, n: _draw_lamp(),
}
