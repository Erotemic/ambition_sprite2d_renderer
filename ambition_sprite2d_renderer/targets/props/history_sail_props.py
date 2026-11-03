"""The props of the Age of Sail, era 7 of the History dimension.

A harbour of tall ships, drawn in the cel style of the dimension's cast
(`targets/characters/_history_modern_kit.py`): flat colour, one shade, a
bold warm outline.

- ``history_ship_boom``: the boom of a ship's sail, a wooden spar with the
  sail furled on top of it and tied with gaskets: the look of a swinging
  plank (`MovingPlatform` with `line` and `swing`, as ``art_brush_seesaw``).
  The top of the furled sail is the platform (`platform_looks.ron`:
  `BOOM_SPAN`, `BOOM_TOP`). It turns on the iron band at its middle.
- ``history_mast``: scenery, a mast with two yards, furled sails, a top,
  the shrouds with their ratlines, and a pennant.
- ``history_cargo_crates``: scenery, the Columbian exchange in crates:
  potatoes, tomatoes, maize, and a basket of cocoa pods.
- ``history_astrolabe``: scenery, a big brass astrolabe on a wooden stand.
- ``history_lighthouse``: scenery, a striped lighthouse on its rocks. Its
  ``idle`` row turns the beam of its lamp.

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

BOOM_FRAME = (384, 64)
BOOM_SPAN = (16.0, 368.0)
BOOM_TOP = 22.0
MAST_FRAME = (192, 512)
CRATES_FRAME = (192, 128)
ASTROLABE_FRAME = (128, 192)
LIGHTHOUSE_FRAME = (192, 512)
LIGHTHOUSE_ROWS: List[Tuple[str, int, int]] = [("idle", 8, 140)]
SCENERY = ["prop", "scenery", "history"]


def _furled_sail(f: K.Frame, x0: float, x1: float, y_top: float, y_bot: float, ties: int, rng: random.Random) -> None:
    """A sail rolled up along a spar: a lumpy roll of canvas, with rope ties."""
    pts_top = []
    for k in range(17):
        x = x0 + (x1 - x0) * k / 16.0
        pts_top.append((x, y_top + (rng.uniform(0.0, 1.6) if 0 < k < 16 else 2.0)))
    pts_bot = [(x1 - 2.0, y_bot), (x0 + 2.0, y_bot)]
    f.poly(pts_top + pts_bot, H.CANVAS)
    f.poly([(x0 + 2.0, (y_top + y_bot) / 2.0 + 1.5), (x1 - 2.0, (y_top + y_bot) / 2.0 + 1.5), (x1 - 2.0, y_bot), (x0 + 2.0, y_bot)], H.CANVAS_SHADE, body=False)
    for k in range(5):
        x = x0 + 10.0 + k * (x1 - x0 - 20.0) / 4.0
        f.ink([(x, y_top + 2.0), (x + 6.0, y_bot - 1.0)], 0.8, H.CANVAS_SHADE)
    for k in range(ties):
        x = x0 + (x1 - x0) * (k + 0.5) / ties
        f.limb([(x - 1.0, y_top + 0.5), (x + 1.0, y_bot + 0.5)], 2.0, H.ROPE)
        f.ink([(x - 1.0, y_top + 0.5), (x + 1.0, y_bot + 0.5)], 0.6, H.ROPE_DARK)


def _draw_boom():
    f = K.Frame(BOOM_FRAME)
    rng = random.Random("history_ship_boom")
    x0, x1 = BOOM_SPAN
    top = BOOM_TOP
    # The spar: a round pole under the sail, a little thinner at its ends.
    spar_top, spar_bot = top + 11.0, top + 23.0
    f.poly([(x0, spar_top + 2.0), (x0 + 30.0, spar_top), (x1 - 30.0, spar_top), (x1, spar_top + 2.0), (x1, spar_bot - 2.0),
            (x1 - 30.0, spar_bot), (x0 + 30.0, spar_bot), (x0, spar_bot - 2.0)], H.OAK)
    f.poly([(x0, spar_bot - 5.0), (x1, spar_bot - 5.0), (x1, spar_bot - 2.0), (x1 - 30.0, spar_bot), (x0 + 30.0, spar_bot), (x0, spar_bot - 2.0)],
           H.OAK_DARK, body=False)
    for k in range(6):
        x = x0 + 30.0 + k * 58.0
        f.ink([(x, spar_top + 3.0), (x + 40.0, spar_top + 3.5)], 0.8, H.OAK_LIGHT)
    # Iron bands at its ends.
    for x in (x0 + 6.0, x1 - 10.0):
        f.poly([(x, spar_top - 0.5), (x + 4.0, spar_top - 0.5), (x + 4.0, spar_bot + 0.5), (x, spar_bot + 0.5)], H.IRON_DARK)
    # The sail furled along the top: its top is the platform.
    _furled_sail(f, x0 + 2.0, x1 - 2.0, top, spar_top + 1.0, 7, rng)
    # The iron band at its middle, with the ring it turns on.
    mid = (x0 + x1) / 2.0
    f.poly([(mid - 6.0, spar_top - 0.5), (mid + 6.0, spar_top - 0.5), (mid + 6.0, spar_bot + 1.0), (mid - 6.0, spar_bot + 1.0)], H.IRON_DARK)
    f.ellipse(mid, spar_bot + 5.0, 5.0, 5.0, H.IRON)
    f.ellipse(mid, spar_bot + 5.0, 2.2, 2.2, H.OUTLINE, body=False)
    # A block and a coil of the sheet rope that hangs from it.
    f.limb([(x1 - 50.0, spar_bot), (x1 - 52.0, spar_bot + 6.0)], 1.6, H.ROPE)
    f.ellipse(x1 - 52.0, spar_bot + 8.0, 3.0, 3.4, H.OAK_DARK)
    return H.finish(f, width=1.4)


def _draw_mast():
    w, h = MAST_FRAME
    f = K.Frame(MAST_FRAME)
    rng = random.Random("history_mast")
    cx, foot = w / 2.0, h - 4.0
    top_y = 208.0
    # The shrouds: from the top down to the rail on each side, with ratlines.
    for side in (-1.0, 1.0):
        lines = []
        for k in range(3):
            a = (cx + side * (14.0 + k * 3.0), top_y + 4.0)
            b = (cx + side * (52.0 + k * 12.0), foot - 26.0)
            f.ink([a, b], 1.2, H.TAR)
            lines.append((a, b))
        for r in range(1, 16):
            u = r / 16.0
            p = [(a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u) for a, b in lines]
            f.ink([p[0], p[-1]], 0.8, H.ROPE_DARK)
    # A stay from the masthead down to the bow, off to the right.
    f.ink([(cx + 4.0, 34.0), (w - 10.0, foot - 30.0)], 1.2, H.TAR)
    # The rail at the foot, and the deck block round the mast.
    f.poly([(14.0, foot - 30.0), (w - 14.0, foot - 30.0), (w - 14.0, foot - 22.0), (14.0, foot - 22.0)], H.OAK_DARK)
    for x in (24.0, w - 30.0):
        f.ellipse(x + 3.0, foot - 32.0, 3.0, 2.0, H.IRON)
    # The mast: a tall pole that narrows, in two pieces lapped at the top.
    f.poly([(cx - 9.0, foot), (cx + 9.0, foot), (cx + 6.0, top_y - 10.0), (cx - 6.0, top_y - 10.0)], H.OAK)
    f.poly([(cx - 9.0, foot), (cx - 3.0, foot), (cx - 2.0, top_y - 10.0), (cx - 6.0, top_y - 10.0)], H.OAK_DARK, body=False)
    f.poly([(cx - 4.0, top_y + 20.0), (cx + 4.0, top_y + 20.0), (cx + 3.0, 28.0), (cx - 3.0, 28.0)], H.OAK)
    f.poly([(cx - 4.0, top_y + 20.0), (cx - 1.0, top_y + 20.0), (cx - 1.0, 28.0), (cx - 3.0, 28.0)], H.OAK_DARK, body=False)
    for y in (foot - 60.0, foot - 140.0, top_y + 30.0):
        f.poly([(cx - 9.5, y), (cx + 9.5, y), (cx + 9.5, y + 5.0), (cx - 9.5, y + 5.0)], H.IRON_DARK)
    f.poly([(cx - 22.0, foot - 2.0), (cx + 22.0, foot - 2.0), (cx + 18.0, foot - 12.0), (cx - 18.0, foot - 12.0)], H.OAK_DARK)
    # A coil of rope at the foot of the mast.
    f.ellipse(cx + 34.0, foot - 4.0, 14.0, 4.0, H.ROPE)
    for r in (10.0, 6.0, 2.5):
        H.ring(f, cx + 34.0, foot - 4.6, r, r * 0.3, 0.8, H.ROPE_DARK)
    # The main yard and the top yard, with their sails furled on them.
    for y, half in ((top_y + 52.0, 80.0), (110.0, 62.0)):
        f.poly([(cx - half, y), (cx + half, y), (cx + half - 2.0, y + 6.0), (cx - half + 2.0, y + 6.0)], H.OAK_DARK)
        _furled_sail(f, cx - half + 4.0, cx + half - 4.0, y + 5.0, y + 15.0, 6, rng)
        f.ink([(cx - half, y + 1.0), (cx - half + 6.0, y + 26.0)], 1.0, H.TAR)
        f.ink([(cx + half, y + 1.0), (cx + half - 6.0, y + 26.0)], 1.0, H.TAR)
    # The top: a platform on the mast where the lookout stands.
    f.poly([(cx - 30.0, top_y), (cx + 30.0, top_y), (cx + 24.0, top_y + 8.0), (cx - 24.0, top_y + 8.0)], H.OAK)
    f.ink([(cx - 30.0, top_y + 1.0), (cx + 30.0, top_y + 1.0)], 1.0, H.OAK_LIGHT)
    for k in range(5):
        x = cx - 24.0 + k * 12.0
        f.ink([(x, top_y), (x, top_y - 10.0)], 1.2, H.OAK_DARK)
    f.ink([(cx - 26.0, top_y - 10.0), (cx + 26.0, top_y - 10.0)], 1.4, H.OAK_DARK)
    # The truck at the masthead and a long pennant in the wind.
    f.ellipse(cx, 26.0, 5.0, 3.0, H.OAK_DARK)
    pen = [(cx + 3.0, 18.0), (cx + 70.0, 22.0), (cx + 50.0, 25.0), (cx + 76.0, 30.0), (cx + 3.0, 26.0)]
    f.poly(pen, H.COAT_RED)
    f.poly([(cx + 3.0, 23.0), (cx + 60.0, 25.6), (cx + 76.0, 30.0), (cx + 3.0, 26.0)], H.COAT_RED_DARK, body=False)
    f.ink([(cx, 28.0), (cx, 12.0)], 1.6, H.OAK_DARK)
    return H.finish(f, width=1.6)


def _potato(f, x, y, r, rng):
    f.ellipse(x, y, r * 1.25, r, (176, 128, 76, 255))
    f.ellipse(x + r * 0.2, y + r * 0.3, r * 0.9, r * 0.5, (140, 96, 54, 255), body=False)
    for _ in range(2):
        f.dot(x + rng.uniform(-r, r) * 0.7, y + rng.uniform(-r, r) * 0.5, 0.7, (100, 66, 36, 255))


def _tomato(f, x, y, r):
    f.ellipse(x, y, r * 1.1, r, (220, 48, 36, 255))
    f.ellipse(x + r * 0.3, y + r * 0.3, r * 0.6, r * 0.45, (160, 24, 20, 255), body=False)
    f.dot(x - r * 0.4, y - r * 0.4, r * 0.25, (255, 200, 190, 255))
    for k in range(4):
        a = math.radians(-90.0 + (k - 1.5) * 50.0)
        f.ink([(x, y - r * 0.8), (x + math.cos(a) * r * 0.7, y - r * 0.8 + math.sin(a) * r * 0.4)], 1.0, (60, 140, 60, 255))


def _maize(f, x, y, angle):
    cob = K.turn([(x - 4.0, y), (x - 3.0, y - 20.0), (x, y - 24.0), (x + 3.0, y - 20.0), (x + 4.0, y)], x, y, angle)
    f.poly(cob, (250, 206, 70, 255))
    for k in range(5):
        a = K.turn([(x - 3.0, y - 3.0 - k * 4.0), (x + 3.0, y - 3.0 - k * 4.0)], x, y, angle)
        f.ink(a, 0.6, (204, 150, 30, 255))
    for side in (-1.0, 1.0):
        husk = K.turn([(x, y + 2.0), (x + side * 7.0, y - 10.0), (x + side * 3.0, y - 16.0), (x + side * 2.0, y - 4.0)], x, y, angle)
        f.poly(husk, (120, 170, 80, 255))


def _cocoa(f, x, y, angle):
    pod = K.turn([(x - 8.0, y), (x - 5.0, y - 4.0), (x + 5.0, y - 4.0), (x + 9.0, y), (x + 5.0, y + 4.0), (x - 5.0, y + 4.0)], x, y, angle)
    f.poly(pod, (204, 116, 44, 255))
    for k in (-1.6, 1.6):
        f.ink(K.turn([(x - 7.0, y + k * 0.6), (x + 8.0, y + k * 0.6)], x, y, angle), 0.6, (150, 74, 26, 255))


def _crate(f, x0, y0, x1, y1, label_colour):
    f.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], H.OAK_LIGHT)
    for k in range(1, 4):
        y = y0 + (y1 - y0) * k / 4.0
        f.ink([(x0, y), (x1, y)], 1.0, H.OAK)
    f.poly([(x0, y0), (x0 + 6.0, y0), (x0 + 6.0, y1), (x0, y1)], H.OAK, body=False)
    f.poly([(x1 - 6.0, y0), (x1, y0), (x1, y1), (x1 - 6.0, y1)], H.OAK, body=False)
    f.ink([(x0 + 6.0, y1 - 2.0), (x1 - 6.0, y0 + 2.0)], 2.0, H.OAK)
    # A painted stencil of where it came from: a band of colour.
    mx, my = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    f.ellipse(mx, my, 10.0, 7.0, K.alpha(label_colour, 0.85), body=False)
    H.ring(f, mx, my, 10.0, 7.0, 1.0, K.alpha(H.OUTLINE, 0.6))


def _draw_crates():
    w, h = CRATES_FRAME
    f = K.Frame(CRATES_FRAME)
    rng = random.Random("history_cargo_crates")
    foot = h - 4.0
    # The produce first (it pokes out over the tops of the crates).
    for k in range(9):
        _potato(f, 18.0 + k * 7.5 + rng.uniform(-1.0, 1.0), 73.0 - (k % 2) * 4.0, 5.0, rng)
    for k in range(8):
        _tomato(f, 104.0 + k * 9.0 + rng.uniform(-1.0, 1.0), 73.0 - (k % 2) * 4.0, 5.0)
    _crate(f, 12.0, 76.0, 92.0, foot, (176, 128, 76, 255))
    _crate(f, 98.0, 76.0, 180.0, foot, (220, 48, 36, 255))
    # The top crate, of maize, sits across the two.
    for k in range(6):
        _maize(f, 52.0 + k * 9.0, 40.0, -14.0 + k * 6.0)
    _crate(f, 44.0, 36.0, 116.0, 76.0, (250, 206, 70, 255))
    # A basket of cocoa pods beside it.
    for k in range(4):
        _cocoa(f, 132.0 + k * 9.0, 52.0 - (k % 2) * 3.0, -20.0 + k * 15.0)
    f.poly([(122.0, 52.0), (174.0, 52.0), (168.0, 76.0), (128.0, 76.0)], (184, 150, 96, 255))
    for k in range(4):
        y = 56.0 + k * 5.0
        f.ink([(123.0 + k, y), (173.0 - k, y)], 0.8, (140, 106, 60, 255))
    for k in range(7):
        x = 128.0 + k * 7.0
        f.ink([(x, 53.0), (x + 1.0, 75.0)], 0.6, (140, 106, 60, 255))
    return H.finish(f, width=1.6)


def _draw_astrolabe():
    w, h = ASTROLABE_FRAME
    f = K.Frame(ASTROLABE_FRAME)
    foot = h - 4.0
    cx, cy, r = 64.0, 82.0, 42.0
    # The stand: three wooden legs and a post up to the disc.
    for x in (22.0, 64.0, 106.0):
        f.limb([(64.0, 136.0), (x, foot - 5.0)], 5.0, H.OAK_DARK if x == 64.0 else H.OAK)
    f.limb([(64.0, 140.0), (64.0, cy + r - 4.0)], 7.0, H.OAK)
    f.ellipse(64.0, 138.0, 9.0, 5.0, H.OAK_DARK)
    # The ring it hangs from, the shackle and the crown.
    f.ellipse(cx, cy - r - 16.0, 7.0, 7.0, H.BRASS)
    f.ellipse(cx, cy - r - 16.0, 4.0, 4.0, H.OUTLINE, body=False)
    f.poly([(cx - 10.0, cy - r + 4.0), (cx + 10.0, cy - r + 4.0), (cx + 6.0, cy - r - 10.0), (cx - 6.0, cy - r - 10.0)], H.BRASS)
    # The mater: a thick brass ring with a scale of degrees.
    f.ellipse(cx, cy, r, r, H.BRASS)
    f.ellipse(cx + 2.0, cy + 2.0, r - 6.0, r - 6.0, H.BRASS_DARK, body=False)
    f.ellipse(cx, cy, r - 7.0, r - 7.0, (190, 150, 60, 255), body=False)
    for k in range(36):
        a = math.tau * k / 36.0
        r0 = r - 2.0 if k % 3 else r - 5.0
        f.ink([(cx + math.cos(a) * r0, cy + math.sin(a) * r0), (cx + math.cos(a) * (r - 1.0), cy + math.sin(a) * (r - 1.0))], 0.6, H.BRASS_DARK)
    # The plate: circles of the sky and lines of the hours.
    for rr in (30.0, 20.0, 11.0):
        H.ring(f, cx, cy - 4.0 + rr * 0.15, rr, rr * 0.92, 0.7, H.BRASS_DARK)
    for k in range(6):
        a = math.pi * k / 6.0
        f.ink([(cx - math.cos(a) * 33.0, cy - math.sin(a) * 33.0 * 0.4 + 6.0), (cx, cy + 10.0)], 0.6, K.alpha(H.BRASS_DARK, 0.7))
    # The rete: an open star map in bright brass over the plate.
    H.ring(f, cx + 5.0, cy - 5.0, 22.0, 22.0, 1.8, H.BRASS_LIGHT)
    for k, (a, d) in enumerate(((0.5, 30.0), (1.6, 26.0), (2.6, 31.0), (3.7, 24.0), (4.6, 29.0), (5.5, 27.0))):
        x, y = cx + math.cos(a) * d, cy + math.sin(a) * d
        f.ink([(cx, cy), (x, y)], 1.0, H.BRASS_LIGHT)
        f.poly([(x, y - 3.4), (x + 1.2, y), (x, y + 3.4), (x - 1.2, y)], H.BRASS_LIGHT, body=False)
    # The alidade: a sighting rule across the back, and the pin.
    a = math.radians(-28.0)
    f.limb([(cx - math.cos(a) * 38.0, cy - math.sin(a) * 38.0), (cx + math.cos(a) * 38.0, cy + math.sin(a) * 38.0)], 3.4, H.BRASS_DARK)
    for s in (-1.0, 1.0):
        x, y = cx + s * math.cos(a) * 28.0, cy + s * math.sin(a) * 28.0
        f.poly([(x - 2.0, y - 4.0), (x + 2.0, y - 4.0), (x + 2.0, y + 1.0), (x - 2.0, y + 1.0)], H.BRASS)
    f.ellipse(cx, cy, 4.0, 4.0, H.BRASS_LIGHT)
    f.dot(cx, cy, 1.6, H.OUTLINE)
    f.ink([(cx - 30.0, cy - 22.0), (cx - 20.0, cy - 32.0)], 1.6, K.alpha(H.WHITE, 0.6))
    return H.finish(f, width=1.6)


def _draw_lighthouse(i: int, n: int):
    w, h = LIGHTHOUSE_FRAME
    f = K.Frame(LIGHTHOUSE_FRAME)
    rng = random.Random("history_lighthouse")
    foot = h - 4.0
    cx = w / 2.0
    base_y, gallery_y = foot - 40.0, 160.0
    # The rocks it stands on.
    for k in range(7):
        x = 36.0 + k * 20.0 + rng.uniform(-3.0, 3.0)
        rr = rng.uniform(13.0, 19.0)
        f.ellipse(x, foot - rr * 0.7, rr, rr * 0.7, (110, 108, 104, 255))
        f.ellipse(x + rr * 0.2, foot - rr * 0.4, rr * 0.7, rr * 0.35, (80, 78, 76, 255), body=False)
        f.dot(x - rr * 0.4, foot - rr * 1.0, 1.4, (150, 148, 142, 255))
    f.poly([(24.0, foot), (w - 24.0, foot), (w - 26.0, foot - 6.0), (26.0, foot - 6.0)], (90, 88, 86, 255))
    # The tower: it narrows as it rises, in bands of red and white.
    bw, tw = 46.0, 30.0

    def half(y):
        u = (base_y - y) / (base_y - gallery_y)
        return bw + (tw - bw) * u

    bands = 6
    for k in range(bands):
        y0 = base_y - (base_y - gallery_y) * k / bands
        y1 = base_y - (base_y - gallery_y) * (k + 1) / bands
        colour = H.COAT_RED if k % 2 == 0 else H.CANVAS
        f.poly([(cx - half(y0), y0), (cx + half(y0), y0), (cx + half(y1), y1), (cx - half(y1), y1)], colour)
        f.poly([(cx + half(y0) - 12.0, y0), (cx + half(y0), y0), (cx + half(y1), y1), (cx + half(y1) - 9.0, y1)],
               K.shade(colour, 0.8), body=False)
    # A door at the foot and small windows up the tower.
    f.poly([(cx - 9.0, base_y), (cx + 9.0, base_y), (cx + 9.0, base_y - 26.0), (cx, base_y - 32.0), (cx - 9.0, base_y - 26.0)], H.OAK_DARK)
    f.dot(cx + 5.0, base_y - 12.0, 1.4, H.BRASS)
    for y in (base_y - 100.0, base_y - 170.0, base_y - 240.0):
        f.poly([(cx - 4.0, y), (cx + 4.0, y), (cx + 4.0, y - 12.0), (cx - 4.0, y - 12.0)], H.TAR)
        f.ink([(cx - 4.0, y - 6.0), (cx + 4.0, y - 6.0)], 0.6, H.GASLIGHT)
    # The gallery: a walk round the lamp, with a rail.
    f.poly([(cx - 46.0, gallery_y), (cx + 46.0, gallery_y), (cx + 40.0, gallery_y + 8.0), (cx - 40.0, gallery_y + 8.0)], H.TAR)
    for k in range(9):
        x = cx - 42.0 + k * 10.5
        f.ink([(x, gallery_y), (x, gallery_y - 14.0)], 1.2, H.TAR)
    f.ink([(cx - 44.0, gallery_y - 14.0), (cx + 44.0, gallery_y - 14.0)], 1.6, H.TAR)
    # The lantern: panes of glass, and the lamp lit inside.
    lt, lb = 104.0, gallery_y
    t = i / float(n)
    pulse = 0.8 + 0.2 * math.sin(math.tau * t)
    f.poly([(cx - 24.0, lb), (cx + 24.0, lb), (cx + 24.0, lt), (cx - 24.0, lt)], H.GASLIGHT)
    f.ellipse(cx, (lt + lb) / 2.0, 10.0, 12.0, H.GASLIGHT_HOT, body=False)
    for x in (cx - 12.0, cx, cx + 12.0):
        f.ink([(x, lb), (x, lt)], 1.4, H.TAR)
    f.ink([(cx - 24.0, (lt + lb) / 2.0), (cx + 24.0, (lt + lb) / 2.0)], 1.0, H.TAR)
    # The dome and its vane.
    f.poly([(cx - 30.0, lt), (cx + 30.0, lt), (cx + 18.0, lt - 18.0), (cx, lt - 26.0), (cx - 18.0, lt - 18.0)], H.COAT_RED_DARK)
    f.limb([(cx, lt - 26.0), (cx, lt - 44.0)], 2.0, H.TAR)
    f.ellipse(cx, lt - 28.0, 4.0, 4.0, H.BRASS)
    f.poly([(cx, lt - 44.0), (cx + 14.0, lt - 40.0), (cx, lt - 37.0)], H.TAR)
    # The beam: it turns, so it swings from one side to the other and back.
    swing = math.cos(math.tau * t)
    lx, ly = cx, (lt + lb) / 2.0
    length = 74.0 * abs(swing) + 10.0
    side = 1.0 if swing >= 0.0 else -1.0
    f.glow_poly([(lx, ly - 6.0), (lx + side * length, ly - 18.0), (lx + side * length, ly + 14.0), (lx, ly + 6.0)], K.alpha(H.GASLIGHT_HOT, 0.4 * pulse))
    f.glow(lx, ly, 20.0 * pulse, K.alpha(H.GASLIGHT, 0.55))
    return H.finish(f, width=1.6)


TARGETS: Dict[str, dict] = {
    "history_ship_boom": _publisher("history_ship_boom", "Ship's Boom", STILL, BOOM_FRAME, lambda anim, i, n: _draw_boom(),
                                    {"top": ((BOOM_SPAN[0] + BOOM_SPAN[1]) / 2.0, BOOM_TOP)}, "Scenery", ["prop", "platform", "history"]),
    "history_mast": _publisher("history_mast", "Mast", STILL, MAST_FRAME, lambda anim, i, n: _draw_mast(), {"foot": (96.0, 512.0)}, "Scenery", SCENERY),
    "history_cargo_crates": _publisher("history_cargo_crates", "Cargo Crates", STILL, CRATES_FRAME, lambda anim, i, n: _draw_crates(),
                                       {"foot": (96.0, 128.0)}, "Scenery", SCENERY),
    "history_astrolabe": _publisher("history_astrolabe", "Astrolabe", STILL, ASTROLABE_FRAME, lambda anim, i, n: _draw_astrolabe(),
                                    {"foot": (64.0, 192.0)}, "Scenery", SCENERY),
    "history_lighthouse": _publisher("history_lighthouse", "Lighthouse", LIGHTHOUSE_ROWS, LIGHTHOUSE_FRAME, lambda anim, i, n: _draw_lighthouse(i, n),
                                     {"foot": (96.0, 512.0)}, "Scenery", SCENERY),
}

#: The drawing of each target, by its row (for previews).
DRAW = {
    "history_ship_boom": lambda anim, i, n: _draw_boom(),
    "history_mast": lambda anim, i, n: _draw_mast(),
    "history_cargo_crates": lambda anim, i, n: _draw_crates(),
    "history_astrolabe": lambda anim, i, n: _draw_astrolabe(),
    "history_lighthouse": lambda anim, i, n: _draw_lighthouse(i, n),
}
