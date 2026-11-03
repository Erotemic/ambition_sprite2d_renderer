"""The props of the Fertile Crescent of the History dimension (biome `history_crescent`).

A river plain at the dawn of farming, drawn in the cel style of the cast
(`targets/characters/_art_cast_kit.py`): the warm sepia of an old textbook,
with the colours of the era: mudbrick tan, wheat gold, river teal and lapis
blue.

- ``history_wheat_sheaf``: scenery. A sheaf of wheat bound with a twist of
  straw (its ``idle`` row moves the ears a little in the wind).
- ``history_code_stele``: scenery. A tall stele of black basalt: at its top a
  relief of a seated judge who gives the law to a standing king, and under
  it, line after line of cuneiform.
- ``history_ziggurat``: scenery. A stepped ziggurat of mudbrick with three
  stairs that meet at its first terrace, and a shrine with a band of lapis
  at its top.
- ``history_date_palm``: scenery. A date palm with a scaled trunk and bunches
  of dates (its ``idle`` row moves the fronds).
- ``history_reed_bridge``: the look of the bridge over the canal (a
  `LockWall` of 224 by 24 world units, drawn at 2 to 1). Three long bundles
  of reeds, bound with cord, as the marsh people still make them.
- ``history_clay_tablets``: scenery. A stack of clay tablets written in
  cuneiform, and a basket of more tablets.

The numbers are frame pixels; the game shows each prop at half its frame.
No drop shadows: the game draws them.
"""

from __future__ import annotations

import math
import random
from typing import Callable, Dict, List, Tuple

from ..characters import _art_cast_kit as K
from .art_props import _publisher

STILL: List[Tuple[str, int, int]] = [("idle", 1, 1000)]
LOOP: List[Tuple[str, int, int]] = [("idle", 8, 140)]

#: The sepia of the textbook: the outline and the dark ink.
OUTLINE = (52, 34, 24, 255)
SEPIA = (112, 76, 48, 255)
MUDBRICK = (204, 160, 108, 255)
MUDBRICK_SHADE = (158, 114, 72, 255)
MUDBRICK_LIGHT = (230, 196, 144, 255)
MORTAR = (120, 82, 52, 255)
WHEAT = (238, 198, 90, 255)
WHEAT_SHADE = (192, 146, 52, 255)
WHEAT_LIGHT = (252, 226, 150, 255)
STRAW = (214, 176, 96, 255)
TEAL = (56, 152, 150, 255)
LAPIS = (40, 74, 162, 255)
LAPIS_LIGHT = (86, 124, 206, 255)
GOLD = (232, 182, 62, 255)
BASALT = (70, 68, 82, 255)
BASALT_SHADE = (46, 44, 56, 255)
BASALT_LIGHT = (112, 110, 128, 255)
RELIEF = (150, 148, 166, 255)
CUNEIFORM = (176, 172, 190, 255)
CLAY = (180, 128, 84, 255)
CLAY_SHADE = (136, 92, 58, 255)
CLAY_LIGHT = (212, 166, 120, 255)
REED = (204, 184, 108, 255)
REED_SHADE = (156, 136, 74, 255)
REED_LIGHT = (232, 216, 150, 255)
CORD = (118, 80, 46, 255)
PALM_TRUNK = (150, 108, 66, 255)
PALM_TRUNK_SHADE = (108, 74, 44, 255)
FROND = (98, 146, 62, 255)
FROND_SHADE = (64, 104, 44, 255)
FROND_LIGHT = (150, 190, 90, 255)
DATE = (180, 84, 40, 255)
DATE_LIGHT = (222, 128, 66, 255)
WICKER = (186, 140, 78, 255)
WICKER_SHADE = (134, 96, 50, 255)


def _phase(i: int, n: int) -> float:
    return i / float(max(1, n))


def _wedge(f: K.Frame, x: float, y: float, size: float, kind: int, colour) -> None:
    """One mark of cuneiform: a small head of a wedge and its tail. `kind` 0
    is a wedge across, 1 a wedge down, 2 a corner wedge."""
    s = size
    if kind == 0:
        f.poly([(x, y - s * 0.5), (x + s * 0.7, y), (x, y + s * 0.5)], colour, body=False)
        f.ink([(x + s * 0.5, y), (x + s * 1.6, y)], max(0.6, s * 0.22), colour)
    elif kind == 1:
        f.poly([(x - s * 0.5, y), (x, y + s * 0.7), (x + s * 0.5, y)], colour, body=False)
        f.ink([(x, y + s * 0.5), (x, y + s * 1.5)], max(0.6, s * 0.22), colour)
    else:
        f.poly([(x, y), (x + s * 0.8, y - s * 0.4), (x + s * 0.5, y + s * 0.5)], colour, body=False)


def _cuneiform_lines(f: K.Frame, x0: float, x1: float, y0: float, y1: float, rng: random.Random, colour, size: float = 3.0,
                     gap: float = 9.0, rule=None) -> None:
    """Lines of cuneiform between two rules each, from `y0` to `y1`."""
    y = y0
    while y + gap <= y1 + 0.1:
        if rule is not None:
            f.ink([(x0, y), (x1, y)], 0.7, rule)
        x = x0 + rng.uniform(1.0, 3.0)
        while x < x1 - size * 2.0:
            kind = rng.choice((0, 0, 1, 1, 2))
            _wedge(f, x, y + gap * 0.45, size, kind, colour)
            x += size * (2.0 if kind == 0 else 1.3) + rng.uniform(0.6, 2.4)
        y += gap
    if rule is not None:
        f.ink([(x0, y), (x1, y)], 0.7, rule)


# ---------------------------------------------------------------------------
# The wheat sheaf.
# ---------------------------------------------------------------------------

SHEAF_FRAME = (96, 128)


def _draw_sheaf(anim: str, i: int, n: int):
    t = _phase(i, n)
    f = K.Frame(SHEAF_FRAME)
    rng = random.Random("history_wheat_sheaf")
    foot = 122.0
    band = (48.0, 80.0)
    wind = math.sin(math.tau * t)
    stalks = []
    for k in range(15):
        u = (k / 14.0) * 2.0 - 1.0
        foot_x = 48.0 + u * 20.0 + rng.uniform(-1.5, 1.5)
        top_x = 48.0 + u * 30.0 + rng.uniform(-2.0, 2.0)
        top_y = 30.0 + abs(u) * 14.0 + rng.uniform(-3.0, 3.0)
        stalks.append((u, foot_x, top_x, top_y, rng.random()))
    # The stalks: from the cut ends on the ground, in through the band, out to the ears.
    for u, foot_x, top_x, top_y, r in stalks:
        sway = wind * (1.6 + 1.2 * r) * (1.0 - 0.3 * abs(u))
        tip = (top_x + sway, top_y)
        mid = (band[0] + u * 4.0, band[1])
        tone = WHEAT if r > 0.35 else WHEAT_SHADE
        f.limb([(foot_x, foot), mid, ((mid[0] + tip[0]) / 2.0 + sway * 0.3, (mid[1] + tip[1]) / 2.0), tip], 2.2, tone)
    # The ears: long and plump, with their grains and their awns.
    for u, foot_x, top_x, top_y, r in stalks:
        sway = wind * (1.6 + 1.2 * r) * (1.0 - 0.3 * abs(u))
        tip = (top_x + sway, top_y)
        ang = math.degrees(math.atan2(tip[0] - band[0], band[1] - tip[1]))
        ear = K.turn(K.ellipse_points(tip[0], tip[1] - 6.0, 3.0, 8.0, 16), tip[0], tip[1], ang)
        f.poly(ear, WHEAT_LIGHT if r > 0.5 else WHEAT)
        for g in range(4):
            gy = tip[1] - 2.0 - g * 3.4
            p = K.turn([(tip[0] - 2.4, gy), (tip[0], gy - 1.4), (tip[0] + 2.4, gy)], tip[0], tip[1], ang)
            f.ink(p, 0.6, WHEAT_SHADE)
        for side in (-1.0, 1.0):
            for g in range(3):
                gy = tip[1] - 6.0 - g * 3.4
                a = K.turn([(tip[0] + side * 2.6, gy), (tip[0] + side * 6.0, gy - 7.0)], tip[0], tip[1], ang)
                f.ink(a, 0.5, K.alpha(WHEAT_SHADE, 0.9))
        a = K.turn([(tip[0], tip[1] - 13.0), (tip[0], tip[1] - 20.0)], tip[0], tip[1], ang)
        f.ink(a, 0.5, K.alpha(WHEAT_SHADE, 0.9))
    # The cut ends of the stalks, on the ground.
    for u, foot_x, *_ in stalks:
        f.dot(foot_x, foot - 0.5, 1.0, WHEAT_SHADE)
    # The band: a twist of straw round its waist.
    f.poly([(band[0] - 11.0, band[1] - 4.0), (band[0] + 11.0, band[1] - 4.0), (band[0] + 10.0, band[1] + 4.0), (band[0] - 10.0, band[1] + 4.0)], STRAW)
    for k in range(6):
        x = band[0] - 9.0 + k * 3.6
        f.ink([(x, band[1] - 3.6), (x + 2.6, band[1] + 3.6)], 0.9, WHEAT_SHADE)
    f.ink([(band[0] + 10.0, band[1]), (band[0] + 15.0, band[1] + 6.0)], 1.6, STRAW)
    return f.finish(outline=OUTLINE, width=1.3)


# ---------------------------------------------------------------------------
# The stele of the code.
# ---------------------------------------------------------------------------

STELE_FRAME = (128, 320)


def _draw_stele(anim: str, i: int, n: int):
    f = K.Frame(STELE_FRAME)
    rng = random.Random("history_code_stele")
    x0, x1, top, foot = 26.0, 102.0, 14.0, 300.0
    cx = (x0 + x1) / 2.0
    # The plinth it stands on.
    f.poly([(x0 - 8.0, foot), (x1 + 8.0, foot), (x1 + 8.0, 314.0), (x0 - 8.0, 314.0)], MUDBRICK)
    f.poly([(x1 - 6.0, foot), (x1 + 8.0, foot), (x1 + 8.0, 314.0), (x1 - 6.0, 314.0)], MUDBRICK_SHADE, body=False)
    f.ink([(x0 - 7.0, foot + 1.4), (x1 + 7.0, foot + 1.4)], 1.0, MUDBRICK_LIGHT)
    # The stone: a slab with a round top, a little wider at its foot.
    shape = [(x0 - 2.0, foot)]
    for k in range(17):
        a = math.pi * (1.0 - k / 16.0)
        shape.append((cx + math.cos(a) * (x1 - x0) / 2.0, top + 30.0 - math.sin(a) * 30.0))
    shape.append((x1 + 2.0, foot))
    f.poly(shape, BASALT)
    f.poly([(x1 - 10.0, 50.0), (x1 - 1.0, 40.0), (x1 + 2.0, foot), (x1 - 8.0, foot)], BASALT_SHADE, body=False)
    # The relief at its top: a field cut down into the stone. The figures
    # are drawn on a small grid and made `RS` times larger, so that they
    # read at the size of the game.
    ground = 140.0
    field = [(x0 + 5.0, ground + 2.0)]
    for k in range(13):
        a = math.pi * (1.0 - k / 12.0)
        field.append((cx + math.cos(a) * 33.0, top + 34.0 - math.sin(a) * 24.0))
    field.append((x1 - 5.0, ground + 2.0))
    f.poly(field, BASALT_SHADE, body=False)
    relief = RELIEF
    RS = 1.3

    def R(points):
        return [(cx + (x - 64.0) * RS, ground + (y - 110.0) * RS) for x, y in points]

    def RE(x, y, rx, ry):
        (px, py), = R([(x, y)])
        f.ellipse(px, py, rx * RS, ry * RS, relief, body=False)

    # A sun with rays in the top of the field.
    f.ellipse(cx, 27.0, 4.0, 4.0, relief, body=False)
    for k in range(8):
        a = math.tau * k / 8.0
        f.ink([(cx + math.cos(a) * 5.5, 27.0 + math.sin(a) * 5.5), (cx + math.cos(a) * 8.0, 27.0 + math.sin(a) * 8.0)], 0.9, relief)
    # The judge, on a throne at the right: a tall cap of horns, a beard,
    # a robe in flounces, and the rod and the ring that he gives.
    jx, jy = 80.0, 110.0
    f.poly(R([(jx + 6.0, jy), (jx + 12.0, jy), (jx + 12.0, jy - 26.0), (jx + 6.0, jy - 26.0)]), K.shade(relief, 0.8), body=False)
    f.poly(R([(jx - 8.0, jy), (jx + 8.0, jy), (jx + 6.0, jy - 26.0), (jx - 6.0, jy - 26.0)]), relief, body=False)
    for k in range(4):
        f.ink(R([(jx - 7.5 + k * 0.4, jy - 6.0 - k * 5.0), (jx + 7.5 - k * 0.4, jy - 6.0 - k * 5.0)]), 0.7, BASALT_SHADE)
    f.poly(R([(jx - 6.0, jy - 26.0), (jx + 6.0, jy - 26.0), (jx + 5.0, jy - 40.0), (jx - 5.0, jy - 40.0)]), relief, body=False)
    RE(jx - 1.0, jy - 45.0, 5.0, 5.5)
    f.poly(R([(jx - 6.0, jy - 44.0), (jx - 4.0, jy - 35.0), (jx - 1.0, jy - 42.0)]), relief, body=False)
    f.ink(R([(jx - 5.4, jy - 43.0), (jx - 3.8, jy - 37.0)]), 0.7, BASALT_SHADE)
    f.ink(R([(jx - 3.6, jy - 46.0), (jx - 2.0, jy - 46.0)]), 1.0, BASALT_SHADE)
    f.poly(R([(jx - 5.0, jy - 49.0), (jx + 5.0, jy - 49.0), (jx + 4.0, jy - 60.0), (jx - 4.0, jy - 60.0)]), relief, body=False)
    for k in range(3):
        f.ink(R([(jx - 4.6, jy - 52.0 - k * 3.0), (jx + 4.6, jy - 52.0 - k * 3.0)]), 0.7, BASALT_SHADE)
    f.limb(R([(jx - 4.0, jy - 34.0), (jx - 14.0, jy - 36.0)]), 2.4 * RS, relief, body=False)
    f.ink(R([(jx - 15.0, jy - 42.0), (jx - 15.0, jy - 30.0)]), 1.4, relief)
    ring = R(K.ellipse_points(jx - 15.0, jy - 28.0, 2.2, 2.2, 10))
    f.ink(ring + ring[:1], 1.1, relief)
    # The king, who stands at the left with a hand up to his mouth.
    kx, ky = 46.0, 110.0
    f.poly(R([(kx - 6.0, ky), (kx + 6.0, ky), (kx + 5.0, ky - 34.0), (kx - 5.0, ky - 34.0)]), relief, body=False)
    f.ink(R([(kx - 5.5, ky - 4.0), (kx + 5.5, ky - 4.0)]), 0.7, BASALT_SHADE)
    RE(kx + 1.0, ky - 39.0, 4.6, 5.0)
    f.ink(R([(kx + 2.4, ky - 40.0), (kx + 3.6, ky - 40.0)]), 1.0, BASALT_SHADE)
    f.poly(R([(kx - 4.0, ky - 43.0), (kx + 5.0, ky - 43.0), (kx + 5.0, ky - 47.0), (kx - 4.0, ky - 47.0)]), relief, body=False)
    f.poly(R([(kx + 4.0, ky - 38.0), (kx + 6.5, ky - 31.0), (kx + 2.0, ky - 34.0)]), relief, body=False)
    f.limb(R([(kx + 3.0, ky - 30.0), (kx + 8.0, ky - 34.0), (kx + 6.0, ky - 38.0)]), 2.0 * RS, relief, body=False)
    # The ground line under the two figures.
    f.ink([(x0 + 6.0, ground + 2.0), (x1 - 6.0, ground + 2.0)], 1.2, relief)
    # The laws: lines of cuneiform, ruled, down the whole stone.
    _cuneiform_lines(f, x0 + 6.0, x1 - 6.0, ground + 10.0, foot - 8.0, rng, CUNEIFORM, size=2.8, gap=8.5, rule=K.alpha(RELIEF, 0.35))
    # The light on the left edge of the stone.
    f.ink([(x0 + 1.5, 50.0), (x0 - 0.5, foot - 2.0)], 2.0, K.alpha(RELIEF, 0.7))
    return f.finish(outline=OUTLINE, width=1.6)


# ---------------------------------------------------------------------------
# The ziggurat.
# ---------------------------------------------------------------------------

ZIGGURAT_FRAME = (512, 384)


def _brick_block(f: K.Frame, x0: float, x1: float, y0: float, y1: float, batter: float, rng: random.Random, course: float = 9.0) -> None:
    """One tier of mudbrick: sloped sides (`batter` pixels in at its top), a
    lit face, a shaded right side, the courses and the buttresses."""
    face = [(x0, y1), (x1, y1), (x1 - batter, y0), (x0 + batter, y0)]
    f.poly(face, MUDBRICK)
    w = x1 - x0
    f.poly([(x1 - w * 0.16, y1), (x1, y1), (x1 - batter, y0), (x1 - w * 0.16 - batter * 0.3, y0)], MUDBRICK_SHADE, body=False)
    f.poly([(x0 + batter, y0), (x1 - batter, y0), (x1 - batter - 2.0, y0 + 4.0), (x0 + batter + 2.0, y0 + 4.0)], MUDBRICK_LIGHT, body=False)
    y = y1 - course
    row = 0
    while y > y0 + 5.0:
        u = (y1 - y) / (y1 - y0)
        lx, rx = x0 + batter * u, x1 - batter * u
        f.ink([(lx + 1.0, y), (rx - 1.0, y)], 0.8, K.alpha(MORTAR, 0.5))
        bx = lx + (7.0 if row % 2 else 0.0) + 8.0
        while bx < rx - 6.0:
            if rng.random() < 0.6:
                f.ink([(bx, y), (bx, y + course)], 0.7, K.alpha(MORTAR, 0.35))
            bx += 14.0
        y -= course
        row += 1
    # The buttresses: tall flat recesses up the face, as the temples had.
    k = 0
    bx = x0 + 22.0
    while bx < x1 - 22.0:
        if k % 2:
            f.poly([(bx, y1 - 2.0), (bx + 10.0, y1 - 2.0), (bx + 10.0 - batter * 0.1, y0 + 6.0), (bx - batter * 0.1, y0 + 6.0)],
                   K.alpha(MUDBRICK_SHADE, 0.5), body=False)
        bx += 22.0
        k += 1


def _stair(f: K.Frame, foot_l: float, foot_r: float, top_l: float, top_r: float, y_top: float, y_foot: float, steps: int) -> None:
    f.poly([(foot_l, y_foot), (foot_r, y_foot), (top_r, y_top), (top_l, y_top)], MUDBRICK_LIGHT)
    f.poly([(foot_r - (foot_r - foot_l) * 0.2, y_foot), (foot_r, y_foot), (top_r, y_top), (top_r - (top_r - top_l) * 0.2, y_top)],
           K.alpha(MUDBRICK, 0.9), body=False)
    for s in range(1, steps):
        u = s / float(steps)
        y = y_foot + (y_top - y_foot) * u
        lx = foot_l + (top_l - foot_l) * u
        rx = foot_r + (top_r - foot_r) * u
        f.ink([(lx + 1.0, y), (rx - 1.0, y)], 1.0, MUDBRICK_SHADE)
    f.ink([(foot_l, y_foot), (top_l, y_top)], 1.6, MUDBRICK_SHADE)
    f.ink([(foot_r, y_foot), (top_r, y_top)], 1.6, MUDBRICK_SHADE)


def _draw_ziggurat(anim: str, i: int, n: int):
    f = K.Frame(ZIGGURAT_FRAME)
    rng = random.Random("history_ziggurat")
    foot = 376.0
    # Three tiers, each smaller, from the ground up.
    _brick_block(f, 34.0, 478.0, 262.0, foot, 14.0, rng)
    _brick_block(f, 112.0, 400.0, 176.0, 262.0, 12.0, rng)
    _brick_block(f, 168.0, 344.0, 112.0, 176.0, 10.0, rng)
    # The shrine on its top: white plaster, a band of lapis, a door.
    f.poly([(212.0, 112.0), (300.0, 112.0), (296.0, 58.0), (216.0, 58.0)], (236, 222, 196, 255))
    f.poly([(284.0, 112.0), (300.0, 112.0), (296.0, 58.0), (282.0, 58.0)], (196, 178, 150, 255), body=False)
    f.poly([(214.0, 58.0), (298.0, 58.0), (298.0, 46.0), (214.0, 46.0)], LAPIS)
    f.poly([(284.0, 58.0), (298.0, 58.0), (298.0, 46.0), (284.0, 46.0)], K.shade(LAPIS, 0.75), body=False)
    for k in range(7):
        f.dot(222.0 + k * 11.5, 52.0, 1.8, GOLD)
    f.poly([(208.0, 46.0), (304.0, 46.0), (300.0, 40.0), (212.0, 40.0)], (236, 222, 196, 255))
    for x in (218.0, 238.0, 258.0, 278.0, 294.0):
        f.poly([(x - 4.0, 40.0), (x + 4.0, 40.0), (x + 4.0, 32.0), (x - 4.0, 32.0)], (236, 222, 196, 255))
    arch = [(246.0, 112.0)] + [(256.0 + math.cos(a) * 10.0, 86.0 - math.sin(a) * 12.0) for a in [math.pi * (1.0 - k / 10.0) for k in range(11)]] + [(266.0, 112.0)]
    f.poly(arch, (60, 40, 30, 255), body=False)
    # The three stairs: one straight up the front, and one from each side,
    # that meet at a gate house on the first terrace.
    _stair(f, 46.0, 98.0, 200.0, 226.0, 262.0, foot, 13)
    _stair(f, 466.0, 414.0, 312.0, 286.0, 262.0, foot, 13)
    _stair(f, 226.0, 286.0, 232.0, 280.0, 112.0, foot, 30)
    f.poly([(220.0, 270.0), (292.0, 270.0), (292.0, 242.0), (220.0, 242.0)], MUDBRICK)
    f.poly([(278.0, 270.0), (292.0, 270.0), (292.0, 242.0), (278.0, 242.0)], MUDBRICK_SHADE, body=False)
    gate = [(244.0, 270.0)] + [(256.0 + math.cos(a) * 12.0, 256.0 - math.sin(a) * 10.0) for a in [math.pi * (1.0 - k / 10.0) for k in range(11)]] + [(268.0, 270.0)]
    f.poly(gate, (60, 40, 30, 255), body=False)
    for x in (226.0, 238.0, 274.0, 286.0):
        f.poly([(x - 3.5, 242.0), (x + 3.5, 242.0), (x + 3.5, 236.0), (x - 3.5, 236.0)], MUDBRICK)
    # Small trees on the terraces: the gardens that grew on them.
    for x, y in ((136.0, 262.0), (176.0, 262.0), (336.0, 262.0), (376.0, 262.0), (186.0, 176.0), (326.0, 176.0)):
        f.limb([(x, y), (x, y - 10.0)], 2.4, PALM_TRUNK)
        f.ellipse(x, y - 15.0, 8.0, 7.0, FROND)
        f.ellipse(x - 2.0, y - 17.0, 4.5, 3.5, FROND_LIGHT, body=False)
    return f.finish(outline=OUTLINE, width=1.8)


# ---------------------------------------------------------------------------
# The date palm.
# ---------------------------------------------------------------------------

PALM_FRAME = (192, 384)


def _draw_palm(anim: str, i: int, n: int):
    t = _phase(i, n)
    f = K.Frame(PALM_FRAME)
    wind = math.sin(math.tau * t)
    foot = 378.0
    crown = (100.0 + 1.0 * wind, 118.0)
    # The trunk: a gentle curve from the foot up to the crown.
    spine = []
    for k in range(13):
        u = k / 12.0
        spine.append((92.0 + 10.0 * math.sin(u * math.pi * 0.8) + (crown[0] - 100.0) * u * u, foot - 10.0 - (foot - 10.0 - crown[1]) * u))
    widths = [16.0 - 5.0 * (k / 12.0) for k in range(13)]
    for k in range(12):
        f.limb([spine[k], spine[k + 1]], widths[k], PALM_TRUNK)
    # A flare at its foot, into the ground.
    f.poly([(80.0, foot), (104.0, foot), (100.0, foot - 12.0), (84.0, foot - 12.0)], PALM_TRUNK)
    # The scales of the trunk: the bases of old fronds, as chevrons.
    for k in range(1, 26):
        u = k / 26.0
        idx = u * 12.0
        a, b = spine[int(idx)], spine[min(12, int(idx) + 1)]
        fr = idx - int(idx)
        x, y = a[0] + (b[0] - a[0]) * fr, a[1] + (b[1] - a[1]) * fr
        w = (16.0 - 5.0 * u) / 2.0
        f.ink([(x - w, y - 2.0), (x, y + 2.0), (x + w, y - 2.0)], 1.0, PALM_TRUNK_SHADE)
        f.ink([(x + w * 0.2, y + 1.0), (x + w, y - 1.6)], 1.6, K.alpha(PALM_TRUNK_SHADE, 0.6))

    def frond(angle: float, length: float, droop: float, colour, shade_colour) -> None:
        """A frond: a curved rib with leaflets on both sides, out from the crown."""
        a = math.radians(angle)
        pts = []
        for k in range(11):
            u = k / 10.0
            px = crown[0] + math.cos(a) * length * u
            py = crown[1] - math.sin(a) * length * u + droop * u * u
            pts.append((px, py))
        for k in range(1, 11):
            u = k / 10.0
            x, y = pts[k]
            dx, dy = pts[k][0] - pts[k - 1][0], pts[k][1] - pts[k - 1][1]
            d = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / d, dx / d
            leaf = 16.0 * math.sin(math.pi * min(1.0, u * 1.1)) + 3.0
            for side in (-1.0, 1.0):
                tip = (x + nx * leaf * side + dx / d * 6.0, y + ny * leaf * side + dy / d * 6.0 + 4.0)
                f.poly([(x - dx * 0.3, y - dy * 0.3), tip, (x + dx * 0.4, y + dy * 0.4)], colour if side > 0 else shade_colour)
        f.limb(pts, 2.4, shade_colour)
        f.ink(pts, 0.8, FROND_LIGHT)

    # The fronds behind, then the dates, then the fronds in front.
    back = [(160.0, 66.0, 34.0), (20.0, 66.0, 34.0), (120.0, 58.0, 10.0), (60.0, 58.0, 10.0)]
    for ang, length, droop in back:
        frond(ang + 3.0 * wind, length, droop, FROND_SHADE, K.shade(FROND_SHADE, 0.8))
    # Bunches of dates that hang from under the crown.
    for bx, by in ((86.0, 132.0), (114.0, 134.0), (100.0, 140.0)):
        bx += wind * 0.6
        f.limb([(crown[0], crown[1] + 4.0), (bx, by - 4.0)], 2.2, GOLD)
        rng = random.Random(f"dates:{bx:.0f}")
        for _ in range(14):
            dx, dy = rng.uniform(-8.0, 8.0), rng.uniform(-2.0, 16.0)
            f.ellipse(bx + dx * (1.0 - dy / 24.0), by + dy, 2.6, 3.4, DATE if rng.random() < 0.7 else DATE_LIGHT)
    front = [(175.0, 74.0, 56.0), (5.0, 74.0, 56.0), (140.0, 70.0, 20.0), (40.0, 70.0, 20.0), (95.0, 46.0, 0.0), (195.0, 56.0, 70.0),
             (-15.0, 56.0, 70.0)]
    for k, (ang, length, droop) in enumerate(front):
        sway = 4.0 * math.sin(math.tau * t + k * 0.7)
        frond(ang + sway, length, droop, FROND, FROND_SHADE)
    f.ellipse(crown[0], crown[1], 7.0, 6.0, PALM_TRUNK_SHADE)
    return f.finish(outline=OUTLINE, width=1.5)


# ---------------------------------------------------------------------------
# The reed bridge.
# ---------------------------------------------------------------------------

BRIDGE_FRAME = (448, 48)


def _draw_reed_bridge(anim: str, i: int, n: int):
    w, h = BRIDGE_FRAME
    f = K.Frame(BRIDGE_FRAME)
    rng = random.Random("history_reed_bridge")
    x0, x1 = 8.0, w - 8.0
    # Three bundles, side by side and one over the two: seen from the side,
    # each is a long round bundle with tapered ends.
    for y, r, tone in ((30.0, 9.0, REED_SHADE), (18.0, 10.5, REED)):
        body = [(x0 + 4.0, y)] + [(x0 + 18.0, y - r), (x1 - 18.0, y - r), (x1 - 4.0, y), (x1 - 18.0, y + r), (x0 + 18.0, y + r)]
        f.poly(body, tone)
        f.poly([(x0 + 18.0, y + r * 0.35), (x1 - 18.0, y + r * 0.35), (x1 - 8.0, y + r * 0.2), (x1 - 18.0, y + r), (x0 + 18.0, y + r),
                (x0 + 8.0, y + r * 0.2)], K.shade(tone, 0.82), body=False)
        f.ink([(x0 + 20.0, y - r + 2.0), (x1 - 20.0, y - r + 2.0)], 1.2, REED_LIGHT)
        # The reeds of the bundle: long fine lines.
        for _ in range(16):
            yy = y + rng.uniform(-r + 2.0, r - 2.0)
            xa = rng.uniform(x0 + 12.0, x0 + 80.0)
            xb = xa + rng.uniform(60.0, 200.0)
            f.ink([(xa, yy), (min(xb, x1 - 14.0), yy + rng.uniform(-0.6, 0.6))], 0.6, K.alpha(REED_SHADE if tone == REED else K.shade(REED_SHADE, 0.8), 0.8))
        # The tufts of the reed ends.
        for side, xe in ((-1.0, x0 + 4.0), (1.0, x1 - 4.0)):
            for k in range(3):
                f.ink([(xe - side * 6.0, y - 3.0 + k * 3.0), (xe + side * 2.0, y - 5.0 + k * 5.0)], 0.8, REED_SHADE)
    # The cords that bind it, round all three bundles.
    x = x0 + 26.0
    while x < x1 - 20.0:
        for d in (0.0, 3.4):
            f.limb([(x + d, 6.0), (x + d + 2.0, 41.0)], 2.0, CORD)
        f.ink([(x - 0.4, 12.0), (x + 5.6, 13.0)], 0.8, K.shade(CORD, 1.3))
        x += 36.0
    return f.finish(outline=OUTLINE, width=1.4)


# ---------------------------------------------------------------------------
# The clay tablets.
# ---------------------------------------------------------------------------

TABLETS_FRAME = (128, 96)


def _tablet(f: K.Frame, x: float, y: float, w: float, h: float, angle: float, rng: random.Random, tone=CLAY) -> None:
    """A tablet seen from the front, with rounded corners, at its middle (x, y)."""
    r = 2.5
    pts = []
    for cx, cy, a0 in ((x + w / 2 - r, y - h / 2 + r, -90.0), (x + w / 2 - r, y + h / 2 - r, 0.0), (x - w / 2 + r, y + h / 2 - r, 90.0),
                       (x - w / 2 + r, y - h / 2 + r, 180.0)):
        for k in range(4):
            a = math.radians(a0 + k * 30.0)
            pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    pts = K.turn(pts, x, y, angle)
    f.poly(pts, tone)
    f.poly(K.turn([(x + w / 2 - 3.0, y - h / 2 + 1.0), (x + w / 2, y - h / 2 + 3.0), (x + w / 2, y + h / 2 - 2.0),
                   (x + w / 2 - 3.0, y + h / 2)], x, y, angle), K.shade(tone, 0.8), body=False)
    marks = random.Random(rng.random())
    yy = y - h / 2 + 3.5
    while yy < y + h / 2 - 3.0:
        xx = x - w / 2 + 3.0
        while xx < x + w / 2 - 5.0:
            kind = marks.choice((0, 0, 1, 2))
            p = K.turn([(xx, yy)], x, y, angle)[0]
            _wedge(f, p[0], p[1], 1.8, kind, CLAY_SHADE)
            xx += 4.0 + marks.uniform(0.0, 1.6)
        yy += 4.4


def _draw_tablets(anim: str, i: int, n: int):
    f = K.Frame(TABLETS_FRAME)
    rng = random.Random("history_clay_tablets")
    foot = 90.0
    # The basket at the right: a round basket of woven palm leaf, full of
    # tablets that stand up in it.
    bx = 88.0
    for k, (dx, h, ang) in enumerate(((-12.0, 26.0, -10.0), (0.0, 30.0, 3.0), (12.0, 24.0, 12.0))):
        _tablet(f, bx + dx, foot - 34.0 - h * 0.3, 15.0, h, ang, rng, CLAY_LIGHT if k == 1 else CLAY)
    basket = [(bx - 26.0, foot - 32.0), (bx + 26.0, foot - 32.0), (bx + 22.0, foot - 2.0), (bx - 22.0, foot - 2.0)]
    f.poly(basket, WICKER)
    f.poly([(bx + 10.0, foot - 32.0), (bx + 26.0, foot - 32.0), (bx + 22.0, foot - 2.0), (bx + 8.0, foot - 2.0)], WICKER_SHADE, body=False)
    for k in range(5):
        y = foot - 28.0 + k * 6.0
        f.ink([(bx - 25.0 + k * 0.8, y), (bx + 25.0 - k * 0.8, y)], 0.9, WICKER_SHADE)
    for k in range(9):
        x = bx - 22.0 + k * 5.5
        f.ink([(x, foot - 31.0), (x - 1.0, foot - 3.0)], 0.7, K.alpha(WICKER_SHADE, 0.7))
    f.limb([(bx - 27.0, foot - 32.0), (bx + 27.0, foot - 32.0)], 3.4, WICKER)
    # The stack at the left: tablets laid flat, one on another, and one that
    # leans on the stack, its face to us.
    for k in range(5):
        y = foot - 4.0 - k * 7.0
        x = 36.0 + rng.uniform(-3.0, 3.0)
        tone = CLAY if k % 2 == 0 else CLAY_LIGHT
        f.poly([(x - 24.0, y + 3.0), (x + 24.0, y + 3.0), (x + 22.0, y - 3.5), (x - 22.0, y - 3.5)], tone)
        f.poly([(x - 24.0, y + 3.0), (x + 24.0, y + 3.0), (x + 23.0, y + 0.5), (x - 23.0, y + 0.5)], K.shade(tone, 0.8), body=False)
    _tablet(f, 50.0, foot - 52.0, 28.0, 34.0, 8.0, rng, CLAY_LIGHT)
    # A reed stylus on the top of the stack.
    f.limb([(14.0, foot - 40.0), (34.0, foot - 44.0)], 2.2, REED)
    f.poly([(14.0, foot - 41.2), (10.0, foot - 39.6), (14.0, foot - 38.8)], REED_SHADE)
    return f.finish(outline=OUTLINE, width=1.3)


# ---------------------------------------------------------------------------
# Publication.
# ---------------------------------------------------------------------------

DRAW: Dict[str, Callable] = {
    "history_wheat_sheaf": _draw_sheaf,
    "history_code_stele": _draw_stele,
    "history_ziggurat": _draw_ziggurat,
    "history_date_palm": _draw_palm,
    "history_reed_bridge": _draw_reed_bridge,
    "history_clay_tablets": _draw_tablets,
}

TARGETS: Dict[str, dict] = {
    "history_wheat_sheaf": _publisher("history_wheat_sheaf", "Wheat Sheaf", LOOP, SHEAF_FRAME, _draw_sheaf, {"foot": (48.0, 128.0)}, "Scenery",
                                      ["prop", "scenery", "history"]),
    "history_code_stele": _publisher("history_code_stele", "Code Stele", STILL, STELE_FRAME, _draw_stele, {"foot": (64.0, 320.0)}, "Scenery",
                                     ["prop", "scenery", "history"]),
    "history_ziggurat": _publisher("history_ziggurat", "Ziggurat", STILL, ZIGGURAT_FRAME, _draw_ziggurat, {"foot": (256.0, 384.0)}, "Scenery",
                                   ["prop", "scenery", "history"]),
    "history_date_palm": _publisher("history_date_palm", "Date Palm", LOOP, PALM_FRAME, _draw_palm, {"foot": (96.0, 384.0)}, "Scenery",
                                    ["prop", "scenery", "history"]),
    "history_reed_bridge": _publisher("history_reed_bridge", "Reed Bridge", STILL, BRIDGE_FRAME, _draw_reed_bridge, {"foot": (224.0, 48.0)},
                                      "Door", ["prop", "door", "bridge", "history"], forward=(0.0, -1.0)),
    "history_clay_tablets": _publisher("history_clay_tablets", "Clay Tablets", STILL, TABLETS_FRAME, _draw_tablets, {"foot": (64.0, 96.0)},
                                       "Scenery", ["prop", "scenery", "history"]),
}
