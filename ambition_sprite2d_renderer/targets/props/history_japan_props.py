"""The props of Japan after Heian (the History dimension): Hakata Bay in
1274 and 1281, Edo, and Tokyo in 1872.

Twice the fleets of the Mongol Yuan came to Hakata Bay, in northern
Kyushu. After the first attack (1274) the warriors of Kyushu built a dry
stone wall along the bay. In 1281 the second fleet could not land in
force, and a typhoon wrecked it at Takashima. Divers found a wreck there,
with the watertight bulkheads of a Chinese junk, stone anchor stocks, and
ceramic bombs (tetsuhau). Takezaki Suenaga, a samurai of Higo, fought both
times. He paid for a pair of painted handscrolls of his own deeds (the
Moko Shurai Ekotoba).

In Edo the print-sellers (ezoshi-ya) hung their woodblock prints on
strings in the shop front. Hokusai made his great wave about 1831.

In 1872 the first railway of Japan opened, from Shimbashi to Yokohama. Its
first engines were small tank engines from Britain. In the same year
Ginza burned. It was built again in brick ("Bricktown", 1872 to 1877),
with colonnades along the street. Rickshaws (jinrikisha) came into use
from 1869.

These props are drawn in the cel style of the dimension's cast
(`targets/characters/_history_americas_kit.py`): flat colour, one shade, a
bold warm outline. No script is drawn: writing is columns of short
strokes. There are no bodies and no weapons in use.

- ``history_meiji_train``: the look of a platform, the train of 1872: a
  small British tank engine (2-4-0 tank: a tall thin chimney with a
  flared cap, a brass dome, side water tanks, a short cab with a round
  window, red buffer beams, spoked wheels with coupling rods) that pulls
  one open carriage on four wheels (a roof on thin posts, cross benches,
  open sides), on a short length of track. The floor of the carriage and
  the running plate of the engine are the platform; they are level at one
  height, and an iron fall plate bridges the coupling between them
  (`MEIJI_TRAIN_SPAN` = (20, 488), `MEIJI_TRAIN_TOP` = 148, in a 512 x 224
  frame). Its ``idle`` row turns the wheels and the rods and puffs smoke
  from the chimney; the platform stays level and still.
- ``history_mongol_wreck``: scenery, the broken hull of a junk of the
  Yuan fleet on the beach of Takashima: the frames of the bow stand bare,
  the planked stern ends at a watertight bulkhead, a broken mast stump,
  the great rudder in its socket, a stone anchor stock, and drifted sand.
- ``history_tetsuhau``: scenery, a pile of round ceramic bombs of
  grey-brown stoneware, each with a short neck and a fuse of cord, one in
  a net of straw rope. They are at rest.
- ``history_suenaga_scroll``: scenery, a handscroll on a low stand of
  black lacquer, partly unrolled: gold clouds, small horsemen, a ship on
  the waves, and a band of text in columns of short strokes, between its
  two rolled ends.
- ``history_ukiyoe_stall``: scenery, the stall of an Edo print-seller: a
  low wooden stand under a small roof, a split curtain (noren) with no
  writing, and woodblock prints on strings and on the board: a great
  wave, a mountain, a bridge, and actors of the kabuki stage.
- ``history_jinrikisha``: scenery, an empty rickshaw of about 1875,
  parked: two tall thin wheels, a lacquered seat with a folding hood of
  black cloth half up, a footboard, and long shafts that rest on the
  ground.
- ``history_ginza_brick``: scenery, a brick shop front of Ginza Bricktown:
  two storeys of red brick with white trim, tall sash windows and a
  cornice, a colonnade of white columns that holds a balcony over the
  pavement, a shop door with a noren and a wide shop window under a plain
  signboard.

The numbers are frame pixels; the game shows each prop at half its frame.
No drop shadows: the game draws them.
"""

from __future__ import annotations

import math
import random
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from ..characters import _art_cast_kit as K
from ..characters import _history_americas_kit as A
from .art_props import _publisher

Point = Tuple[float, float]
RGBA = Tuple[int, int, int, int]
STILL: List[Tuple[str, int, int]] = [("idle", 1, 1000)]
LOOP: List[Tuple[str, int, int]] = [("idle", 8, 120)]

MEIJI_TRAIN_FRAME = (512, 224)
#: The floor of the carriage and the running plate of the engine are the
#: platform: they are level from x0 to x1 at the height `MEIJI_TRAIN_TOP`
#: (frame pixels). On the real train the floor of the carriage was a
#: little lower than the running plate; here they are one height.
MEIJI_TRAIN_SPAN = (20.0, 488.0)
MEIJI_TRAIN_TOP = 148.0
MONGOL_WRECK_FRAME = (320, 160)
TETSUHAU_FRAME = (112, 64)
SUENAGA_SCROLL_FRAME = (192, 96)
UKIYOE_STALL_FRAME = (224, 192)
JINRIKISHA_FRAME = (144, 112)
GINZA_BRICK_FRAME = (256, 256)

# Wood, sand and stone of the beach.
TIMBER = (128, 104, 80, 255)
TIMBER_LIGHT = (164, 140, 110, 255)
TIMBER_SHADE = (94, 74, 56, 255)
TIMBER_DARK = (62, 48, 38, 255)
TIMBER_END = (184, 160, 124, 255)
WRECK_INSIDE = (54, 42, 34, 255)
WEED = (72, 94, 58, 255)
SAND = (222, 198, 150, 255)
SAND_LIGHT = (240, 222, 182, 255)
SAND_SHADE = (190, 162, 116, 255)
GRANITE = (164, 156, 146, 255)
GRANITE_LIGHT = (198, 192, 180, 255)
GRANITE_SHADE = (122, 114, 106, 255)

# The ceramic bombs and their straw net.
STONEWARE = (132, 112, 96, 255)
STONEWARE_LIGHT = (168, 148, 128, 255)
STONEWARE_SHADE = (96, 80, 70, 255)
GLAZE = (88, 76, 66, 255)
CORD = (196, 170, 120, 255)
CORD_SHADE = (140, 116, 76, 255)
STRAW = (206, 178, 108, 255)
STRAW_SHADE = (156, 128, 70, 255)

# Lacquer, paper and paint of the scroll.
LACQUER = (40, 32, 34, 255)
LACQUER_LIGHT = (92, 80, 82, 255)
LACQUER_RED = (164, 42, 36, 255)
LACQUER_RED_LIGHT = (200, 76, 60, 255)
GOLD = (220, 178, 70, 255)
GOLD_LIGHT = (248, 222, 140, 255)
GOLD_SHADE = (166, 124, 44, 255)
PAPER = (238, 226, 196, 255)
PAPER_SHADE = (210, 194, 156, 255)
SCROLL_BACK = (120, 132, 92, 255)
IVORY = (234, 224, 196, 255)
IVORY_SHADE = (196, 182, 150, 255)
SCROLL_BACK_LIGHT = (156, 168, 120, 255)
INK_BLACK = (52, 44, 42, 255)
PAINT_RED = (186, 66, 50, 255)
PAINT_BLUE = (70, 100, 140, 255)
PAINT_GREEN = (96, 132, 88, 255)
HORSE_BROWN = (126, 88, 60, 255)
HORSE_WHITE = (232, 224, 210, 255)
SEA_PAINT = (96, 136, 150, 255)

# The print stall of Edo.
CEDAR = (170, 124, 82, 255)
CEDAR_LIGHT = (204, 160, 112, 255)
CEDAR_SHADE = (128, 90, 58, 255)
CEDAR_DARK = (90, 62, 42, 255)
SHINGLE = (104, 92, 84, 255)
SHINGLE_LIGHT = (140, 128, 116, 255)
SHINGLE_SHADE = (74, 64, 60, 255)
INDIGO = (46, 62, 104, 255)
INDIGO_LIGHT = (74, 94, 140, 255)
INDIGO_SHADE = (32, 42, 74, 255)
PRUSSIAN = (36, 72, 124, 255)
PRUSSIAN_LIGHT = (92, 136, 180, 255)
FOAM = (246, 244, 236, 255)
PRINT_SKY = (232, 214, 170, 255)
PRINT_DUSK = (224, 160, 112, 255)
MOUNT = (120, 136, 156, 255)
PINE = (64, 98, 70, 255)
KIMONO_RED = (190, 60, 50, 255)
KIMONO_BLACK = (50, 44, 46, 255)
KIMONO_GREEN = (80, 128, 92, 255)
KIMONO_PURPLE = (112, 72, 120, 255)
FACE = (240, 222, 200, 255)
HAIR = (36, 30, 32, 255)
MICA = (176, 168, 168, 255)
STRING = (90, 70, 52, 255)

# The rickshaw.
RICKSHAW_WOOD = (176, 64, 44, 255)
RICKSHAW_WOOD_LIGHT = (212, 102, 74, 255)
RICKSHAW_WOOD_SHADE = (126, 42, 32, 255)
TYRE = (52, 50, 54, 255)
CLOTH = (44, 42, 46, 255)
CLOTH_LIGHT = (86, 84, 90, 255)
CLOTH_SHADE = (30, 28, 32, 255)
CUSHION = (156, 36, 40, 255)
CUSHION_LIGHT = (196, 70, 66, 255)
BRASS = (210, 168, 72, 255)
BRASS_LIGHT = (246, 214, 130, 255)
BRASS_SHADE = (156, 116, 42, 255)

# Ginza Bricktown.
BRICK = (170, 74, 52, 255)
BRICK_LIGHT = (196, 104, 76, 255)
BRICK_SHADE = (124, 52, 40, 255)
MORTAR = (214, 196, 170, 255)
TRIM = (240, 232, 214, 255)
TRIM_LIGHT = (252, 248, 236, 255)
TRIM_SHADE = (196, 186, 164, 255)
GLASS = (84, 104, 112, 255)
GLASS_LIGHT = (150, 176, 182, 255)
GLASS_DARK = (52, 64, 72, 255)
ROOF_TILE = (92, 94, 102, 255)
ROOF_TILE_LIGHT = (130, 132, 140, 255)
ROOF_TILE_SHADE = (66, 68, 76, 255)
PAVEMENT = (170, 160, 144, 255)
PAVEMENT_SHADE = (132, 122, 108, 255)
DOOR_WOOD = (104, 70, 48, 255)
DOOR_WOOD_LIGHT = (140, 100, 70, 255)
GOODS = (184, 150, 96, 255)
IRON = (62, 60, 66, 255)
IRON_LIGHT = (120, 118, 126, 255)

# The train of 1872.
ENGINE_GREEN = (54, 104, 66, 255)
ENGINE_GREEN_LIGHT = (94, 146, 100, 255)
ENGINE_GREEN_SHADE = (36, 72, 46, 255)
ENGINE_BLACK = (44, 42, 46, 255)
ENGINE_BLACK_LIGHT = (96, 94, 100, 255)
BUFFER_RED = (186, 48, 40, 255)
BUFFER_RED_LIGHT = (222, 92, 72, 255)
STEEL = (150, 152, 160, 255)
STEEL_LIGHT = (196, 198, 206, 255)
STEEL_SHADE = (104, 106, 114, 255)
COPPER = (190, 104, 64, 255)
COPPER_LIGHT = (228, 150, 104, 255)
TEAK = (140, 84, 52, 255)
TEAK_LIGHT = (180, 120, 78, 255)
TEAK_SHADE = (100, 58, 36, 255)
CARRIAGE_ROOF = (226, 218, 198, 255)
CARRIAGE_ROOF_SHADE = (180, 170, 150, 255)
SLEEPER = (104, 82, 62, 255)
SLEEPER_SHADE = (76, 60, 46, 255)
BALLAST = (150, 140, 128, 255)
COAL = (40, 38, 42, 255)
SMOKE = (196, 192, 196, 255)
SMOKE_SHADE = (150, 146, 154, 255)
WINDOW_GLASS = (176, 204, 210, 255)


def _ring(cx: float, cy: float, rx: float, ry: float, a0: float = 0.0, a1: float = 360.0, count: int = 36) -> List[Point]:
    """Points on an ellipse from the angle `a0` to `a1` (degrees; 0 is to
    the right, 90 is down)."""
    out: List[Point] = []
    for k in range(count + 1):
        a = math.radians(a0 + (a1 - a0) * k / float(count))
        out.append((cx + math.cos(a) * rx, cy + math.sin(a) * ry))
    return out


def _lerp(a: float, b: float, u: float) -> float:
    return a + (b - a) * u


def _rect(x0: float, y0: float, x1: float, y1: float) -> List[Point]:
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def _turn(points: Sequence[Point], c: Point, degrees: float) -> List[Point]:
    a = math.radians(degrees)
    ca, sa = math.cos(a), math.sin(a)
    return [(c[0] + (x - c[0]) * ca - (y - c[1]) * sa, c[1] + (x - c[0]) * sa + (y - c[1]) * ca) for x, y in points]


def _writing_column(f: K.Frame, x: float, y0: float, y1: float, rng: random.Random, colour: RGBA, size: float = 1.0) -> None:
    """A column of writing with no real letters: small groups of short
    strokes, one under the next, from `y0` down to `y1`."""
    y = y0
    while y < y1 - 1.6 * size:
        kind = rng.random()
        if kind < 0.4:
            f.ink([(x - 0.8 * size, y), (x + 0.8 * size, y)], 0.4 * size, colour)
        elif kind < 0.7:
            f.ink([(x, y - 0.2 * size), (x, y + 1.2 * size)], 0.4 * size, colour)
        else:
            f.ink([(x - 0.7 * size, y + 1.0 * size), (x + 0.6 * size, y)], 0.4 * size, colour)
        y += rng.uniform(1.4, 2.2) * size


def _bricks(f: K.Frame, x0: float, x1: float, y0: float, y1: float, row_h: float, colour: RGBA, seed: str) -> None:
    """Courses of brick in a wall from `x0` to `x1`, `y0` to `y1`: mortar
    joints, and a few bricks of a darker tone."""
    rng = random.Random(seed)
    y = y1
    k = 0
    while y - row_h >= y0 - 0.01:
        f.ink([(x0 + 0.6, y), (x1 - 0.6, y)], 0.6, K.alpha(MORTAR, 0.75))
        x = x0 + (0.0 if k % 2 == 0 else 5.0)
        while x < x1 - 2.0:
            if x > x0 + 1.0:
                f.ink([(x, y - row_h + 0.5), (x, y - 0.5)], 0.5, K.alpha(MORTAR, 0.65))
            if rng.random() < 0.16:
                f.poly(_rect(max(x0, x + 0.8), y - row_h + 0.8, min(x1, x + 9.2), y - 0.8), K.alpha(K.shade(colour, 0.84), 0.9), body=False)
            x += 10.0
        y -= row_h
        k += 1


def _puff(f: K.Frame, x: float, y: float, r: float, colour: RGBA, rng: random.Random, lumps: int = 5, shade: Optional[RGBA] = None) -> None:
    """A puff of smoke: round lumps about a middle, with a shade under
    them."""
    for k in range(lumps):
        a = math.tau * k / lumps + rng.uniform(-0.3, 0.3)
        d = r * rng.uniform(0.35, 0.6)
        pr = r * rng.uniform(0.45, 0.65)
        f.ellipse(x + math.cos(a) * d, y + math.sin(a) * d * 0.8, pr, pr, colour)
    if shade is not None:
        f.ellipse(x + r * 0.15, y + r * 0.3, r * 0.55, r * 0.3, shade, body=False)


def _wheel(f: K.Frame, cx: float, cy: float, r: float, spokes: int, turn: float, rim: RGBA, spoke: RGBA, light: RGBA,
           tyre: float = 3.0, spoke_w: float = 1.4, hub: float = 4.0) -> None:
    """A spoked wheel turned by `turn` radians (clockwise on the screen):
    a tyre, straight spokes and a hub. The ground shows between the
    spokes, so only the tyre and the hub carry the outline."""
    for k in range(spokes):
        a = turn + math.tau * k / spokes
        f.ink([(cx + math.cos(a) * hub * 0.8, cy + math.sin(a) * hub * 0.8), (cx + math.cos(a) * (r - tyre * 0.5), cy + math.sin(a) * (r - tyre * 0.5))], spoke_w, spoke)
    ring = _ring(cx, cy, r - tyre * 0.5, r - tyre * 0.5, 0.0, 360.0, 64)
    f.limb(ring + ring[1:3], tyre, rim)
    f.ink(_ring(cx, cy, r - tyre * 0.5, r - tyre * 0.5, 200.0, 290.0, 12), 0.8, light)
    f.ellipse(cx, cy, hub, hub, spoke)
    f.ellipse(cx, cy, hub * 0.45, hub * 0.45, K.shade(spoke, 0.7), body=False)


# ---------------------------------------------------------------------------
# The train of 1872 (a platform).
# ---------------------------------------------------------------------------


def _crank(cx: float, cy: float, c: float, a: float) -> Point:
    return (cx + math.cos(a) * c, cy + math.sin(a) * c)


def _draw_meiji_train(anim: str, i: int, n: int):
    w, h = MEIJI_TRAIN_FRAME
    f = K.Frame(MEIJI_TRAIN_FRAME)
    ph = i / float(max(1, n))
    top = MEIJI_TRAIN_TOP
    x0, x1 = MEIJI_TRAIN_SPAN
    rail = 204.0
    # The drivers turn once in the loop. The small wheels are two thirds
    # of their size, so they turn one and a half times; their ten spokes
    # come back to the same place at the end of the loop.
    big_r, small_r = 27.0, 18.0
    turn_big = math.tau * ph
    turn_small = turn_big * big_r / small_r

    # The track: sleepers on a thin bed of ballast, and the rail on them.
    f.poly([(8.0, rail + 10.0), (w - 8.0, rail + 10.0), (w - 12.0, rail + 14.0), (12.0, rail + 14.0)], BALLAST)
    for k in range(21):
        sx = 14.0 + k * 23.8
        f.poly(_rect(sx, rail + 4.0, sx + 14.0, rail + 11.0), SLEEPER)
        f.ink([(sx + 1.0, rail + 9.6), (sx + 13.0, rail + 9.6)], 0.8, SLEEPER_SHADE)
    f.poly(_rect(10.0, rail, w - 10.0, rail + 4.4), STEEL)
    f.ink([(11.0, rail + 0.8), (w - 11.0, rail + 0.8)], 0.8, STEEL_LIGHT)
    for k in range(5):
        jx = 60.0 + k * 100.0
        f.poly(_rect(jx - 4.0, rail + 1.4, jx + 4.0, rail + 4.0), STEEL_SHADE, body=False)

    # ---- The carriage: x 20 to 216 -----------------------------------
    c0, c1 = x0, 216.0
    roof_y = top - 86.0
    # Its wheels, in axle guards under the solebar, with leaf springs.
    for wx in (64.0, 172.0):
        wy = rail - small_r
        _wheel(f, wx, wy, small_r, 10, turn_small, ENGINE_BLACK, STEEL_SHADE, STEEL_LIGHT, tyre=3.0, spoke_w=1.6, hub=4.0)
        for s in (-1.0, 1.0):
            f.limb([(wx + s * 9.0, top + 11.0), (wx + s * 4.0, wy - 2.0)], 2.2, ENGINE_BLACK)
        f.poly(_rect(wx - 5.0, wy - 5.0, wx + 5.0, wy + 4.0), ENGINE_BLACK)
        f.dot(wx, wy, 1.6, STEEL)
        f.ink([(wx - 22.0, top + 13.0), (wx, top + 17.0), (wx + 22.0, top + 13.0)], 2.4, STEEL_SHADE)
        f.ink([(wx - 18.0, top + 15.4), (wx, top + 19.0), (wx + 18.0, top + 15.4)], 1.6, STEEL_SHADE)
    # The solebar: a deep beam of teak under the floor, with iron bolts.
    f.poly(_rect(c0, top, c1, top + 12.0), TEAK)
    f.poly(_rect(c0, top + 8.0, c1, top + 12.0), TEAK_SHADE, body=False)
    for k in range(13):
        f.dot(c0 + 8.0 + k * 15.0, top + 6.0, 0.9, ENGINE_BLACK)
    # The buffer beams of the carriage, red, and the buffers.
    for bx, s in ((c0, -1.0), (c1, 1.0)):
        f.poly(_rect(min(bx, bx + s * 4.0), top + 1.0, max(bx, bx + s * 4.0), top + 15.0), BUFFER_RED)
        f.poly(_rect(min(bx + s * 4.0, bx + s * 8.0), top + 6.0, max(bx + s * 4.0, bx + s * 8.0), top + 10.0), STEEL)
        f.ellipse(bx + s * 9.0, top + 8.0, 1.8, 4.4, STEEL)
    # The cross benches: from the side each shows its end, a seat and a
    # back. The benches face the engine.
    posts = [c0 + 6.0 + k * (c1 - c0 - 12.0) / 6.0 for k in range(7)]
    for x in posts[:-1]:
        bx = x + (c1 - c0 - 12.0) / 12.0
        f.poly(_rect(bx - 8.0, top - 18.0, bx + 6.0, top - 14.0), TEAK_LIGHT)
        f.ink([(bx - 7.0, top - 17.2), (bx + 5.0, top - 17.2)], 0.7, (214, 160, 112, 255))
        f.limb([(bx - 6.0, top - 14.0), (bx - 6.0, top - 1.0)], 1.8, TEAK_SHADE)
        f.limb([(bx + 4.0, top - 14.0), (bx + 4.0, top - 1.0)], 1.8, TEAK_SHADE)
        f.limb([(bx - 8.0, top - 18.0), (bx - 10.0, top - 38.0)], 3.0, TEAK)
        f.ink([(bx - 9.2, top - 36.0), (bx - 7.8, top - 20.0)], 0.7, TEAK_LIGHT)
    # The posts that hold the roof, and a hand rail at the height of the
    # seat backs.
    for x in posts:
        f.limb([(x, top), (x, roof_y + 8.0)], 2.2, TEAK)
        f.ink([(x - 0.6, top - 1.0), (x - 0.6, roof_y + 9.0)], 0.6, TEAK_LIGHT)
    f.limb([(posts[0], top - 34.0), (posts[-1], top - 34.0)], 1.4, BRASS)
    # The ends of the carriage: a low panel at the waist, under the rail.
    for x in (posts[0], posts[-1]):
        f.limb([(x, top - 34.0), (x, top)], 3.2, TEAK)
    # The roof: a low arc with eaves that reach out, and an oil lamp pot.
    f.poly([(c0 - 4.0, roof_y + 6.0), (c0 + 4.0, roof_y + 1.0), (c1 - 4.0, roof_y + 1.0), (c1 + 4.0, roof_y + 6.0), (c1 + 4.0, roof_y + 10.0), (c0 - 4.0, roof_y + 10.0)], CARRIAGE_ROOF)
    f.poly([(c0 + 8.0, roof_y + 1.0), (c0 + 22.0, roof_y - 4.0), (c1 - 22.0, roof_y - 4.0), (c1 - 8.0, roof_y + 1.0)], CARRIAGE_ROOF)
    f.ink([(c0 - 3.0, roof_y + 9.4), (c1 + 3.0, roof_y + 9.4)], 1.0, CARRIAGE_ROOF_SHADE)
    f.ink([(c0 + 24.0, roof_y - 2.6), (c1 - 24.0, roof_y - 2.6)], 0.8, (244, 238, 224, 255))
    f.poly(_rect(c0 + 2.0, roof_y + 10.0, c1 - 2.0, roof_y + 15.0), TEAK)
    f.ink([(c0 + 4.0, roof_y + 12.5), (c1 - 4.0, roof_y + 12.5)], 0.6, GOLD)
    lx = (c0 + c1) / 2.0
    f.poly([(lx - 6.0, roof_y - 4.0), (lx - 5.0, roof_y - 11.0), (lx + 5.0, roof_y - 11.0), (lx + 6.0, roof_y - 4.0)], ENGINE_BLACK)
    f.poly([(lx - 3.0, roof_y - 11.0), (lx, roof_y - 15.0), (lx + 3.0, roof_y - 11.0)], ENGINE_BLACK)
    # The floor of the carriage: its top is the platform.
    f.poly(_rect(c0, top - 2.0, c1, top + 1.0), TEAK_LIGHT)

    # ---- The coupling, and the fall plate over it ---------------------
    f.ink([(c1 + 4.0, top + 12.0), (236.0, top + 12.0)], 2.2, ENGINE_BLACK)
    f.poly(_rect(c1 - 2.0, top - 1.0, 238.0, top + 2.0), STEEL)
    f.ink([(c1, top - 0.2), (236.0, top - 0.2)], 0.6, STEEL_LIGHT)

    # ---- The engine: x 230 to 490 -------------------------------------
    e0, e1 = 230.0, 490.0
    drivers = (318.0, 390.0)
    lead = 462.0
    dy = rail - big_r
    ly = rail - small_r
    crank = 9.0
    # The frames between the wheels: a dark plate under the running plate.
    f.poly(_rect(e0 + 10.0, top + 4.0, e1 - 8.0, top + 22.0), ENGINE_BLACK)
    # The wheels: two coupled drivers and a leading pair.
    for x in drivers:
        _wheel(f, x, dy, big_r, 12, turn_big, ENGINE_GREEN, ENGINE_GREEN_SHADE, ENGINE_GREEN_LIGHT, tyre=4.0, spoke_w=2.0, hub=6.0)
        f.ink(_ring(x, dy, big_r - 0.6, big_r - 0.6, 0.0, 360.0, 48), 1.2, STEEL_SHADE)
        # The balance weight between the spokes, across from the crank.
        a = turn_big + math.pi
        f.poly(_ring(x, dy, big_r - 5.0, big_r - 5.0, math.degrees(a) - 28.0, math.degrees(a) + 28.0, 8)
               + _ring(x, dy, big_r - 13.0, big_r - 13.0, math.degrees(a) + 28.0, math.degrees(a) - 28.0, 8), ENGINE_GREEN_SHADE, body=False)
    _wheel(f, lead, ly, small_r, 10, turn_small, ENGINE_GREEN, ENGINE_GREEN_SHADE, ENGINE_GREEN_LIGHT, tyre=3.0, spoke_w=1.6, hub=4.0)
    f.ink(_ring(lead, ly, small_r - 0.6, small_r - 0.6, 0.0, 360.0, 40), 1.0, STEEL_SHADE)
    # The cylinder, between the leading wheel and the front driver, with
    # its slide bars.
    f.poly([(424.0, top + 18.0), (450.0, top + 18.0), (452.0, top + 22.0), (452.0, top + 36.0), (450.0, top + 40.0), (424.0, top + 40.0)], ENGINE_GREEN)
    f.poly(_rect(424.0, top + 33.0, 452.0, top + 40.0), ENGINE_GREEN_SHADE, body=False)
    for x in (427.0, 449.0):
        f.limb([(x, top + 18.0), (x, top + 40.0)], 2.2, BRASS)
    f.limb([(402.0, top + 26.0), (424.0, top + 26.0)], 1.4, STEEL)
    f.limb([(402.0, top + 32.0), (424.0, top + 32.0)], 1.4, STEEL)
    # The brake hanger between the drivers, behind the rods.
    f.poly(_rect(352.0, top + 4.0, 358.0, top + 26.0), ENGINE_BLACK)
    # The cranks, the coupling rod and the connecting rod: they turn with
    # the wheels.
    pins = [_crank(x, dy, crank, turn_big) for x in drivers]
    f.limb([(pins[0][0], pins[0][1]), (pins[1][0], pins[1][1])], 3.6, STEEL)
    f.ink([(pins[0][0] + 3.0, pins[0][1] - 0.8), (pins[1][0] - 3.0, pins[1][1] - 0.8)], 0.8, STEEL_LIGHT)
    head_x = pins[1][0] + math.sqrt(max(1.0, 30.0 ** 2 - (pins[1][1] - (top + 29.0)) ** 2))
    f.poly(_rect(head_x - 4.0, top + 25.0, head_x + 4.0, top + 33.0), STEEL_SHADE)
    f.limb([(head_x + 4.0, top + 29.0), (436.0, top + 29.0)], 1.8, STEEL_LIGHT)
    f.limb([(head_x, top + 29.0), pins[1]], 3.2, STEEL)
    for p in pins:
        f.ellipse(p[0], p[1], 2.8, 2.8, STEEL_SHADE)
        f.dot(p[0], p[1], 1.1, STEEL_LIGHT)
    # The cab: a short cab with a roof, an open side and a round window.
    cab0, cab1 = 246.0, 300.0
    cab_top = top - 80.0
    f.poly([(cab0, top), (cab0, cab_top + 6.0), (cab1, cab_top + 6.0), (cab1, top)], ENGINE_GREEN)
    f.poly([(cab0 + 10.0, top - 4.0), (cab0 + 10.0, cab_top + 26.0), (cab0 + 14.0, cab_top + 20.0), (cab1 - 18.0, cab_top + 20.0), (cab1 - 18.0, top - 30.0),
            (cab1 - 26.0, top - 24.0), (cab1 - 26.0, top - 4.0)], ENGINE_BLACK, body=False)
    f.ink([(cab0 + 3.0, top - 3.0), (cab0 + 3.0, cab_top + 9.0), (cab1 - 3.0, cab_top + 9.0), (cab1 - 3.0, top - 3.0)], 0.8, GOLD)
    f.ellipse(cab1 - 9.0, cab_top + 22.0, 6.0, 6.0, BRASS)
    f.ellipse(cab1 - 9.0, cab_top + 22.0, 4.2, 4.2, WINDOW_GLASS, body=False)
    f.ink(_ring(cab1 - 9.0, cab_top + 22.0, 2.8, 2.8, 200.0, 260.0, 6), 0.8, (236, 246, 248, 255))
    # The reversing lever and the regulator, seen through the open side.
    f.limb([(cab0 + 24.0, top - 4.0), (cab0 + 28.0, top - 30.0)], 1.6, STEEL)
    f.limb([(cab0 + 20.0, cab_top + 34.0), (cab1 - 20.0, cab_top + 36.0)], 2.4, BRASS_SHADE)
    f.poly([(cab0 - 4.0, cab_top + 6.0), (cab0 + 2.0, cab_top), (cab1 - 2.0, cab_top), (cab1 + 4.0, cab_top + 6.0), (cab1 + 4.0, cab_top + 9.0), (cab0 - 4.0, cab_top + 9.0)], ENGINE_BLACK)
    f.ink([(cab0, cab_top + 2.0), (cab1, cab_top + 2.0)], 0.8, ENGINE_BLACK_LIGHT)
    # The coal bunker behind the cab, heaped with coal.
    f.poly(_rect(e0 + 4.0, top - 30.0, cab0, top), ENGINE_GREEN)
    f.poly([(e0 + 5.0, top - 30.0), (e0 + 8.0, top - 35.0), (e0 + 13.0, top - 37.0), (cab0 - 4.0, top - 36.0), (cab0, top - 30.0)], COAL)
    for k in range(5):
        f.dot(e0 + 9.0 + k * 3.0, top - 33.0 - (k % 2), 0.9, ENGINE_BLACK_LIGHT)
    f.ink([(e0 + 6.0, top - 27.0), (cab0 - 2.0, top - 27.0)], 0.8, GOLD)
    # The boiler: a drum from the cab to the smokebox. A brass band holds
    # each joint of its plates.
    b0, b1 = cab1, 438.0
    by, br = top - 44.0, 19.0
    f.poly(_rect(b0, by - br, b1, by + br), ENGINE_GREEN)
    f.poly(_rect(b0, by + br * 0.35, b1, by + br), ENGINE_GREEN_SHADE, body=False)
    f.ink([(b0 + 2.0, by - br + 4.0), (b1 - 2.0, by - br + 4.0)], 1.4, ENGINE_GREEN_LIGHT)
    for x in (b0 + 4.0, 362.0, 408.0, b1 - 3.0):
        f.limb([(x, by - br), (x, by + br)], 2.0, BRASS)
    # The dome, of polished brass, and the safety valve over the firebox.
    dx = 350.0
    f.poly([(dx - 15.0, by - br + 2.0), (dx - 11.0, by - br - 4.0)] + _ring(dx, by - br - 10.0, 10.0, 12.0, 180.0, 360.0, 16)[1:-1]
           + [(dx + 11.0, by - br - 4.0), (dx + 15.0, by - br + 2.0)], BRASS)
    f.ink(_ring(dx - 2.0, by - br - 10.0, 6.0, 8.0, 200.0, 250.0, 8), 1.6, BRASS_LIGHT)
    f.ink([(dx - 13.0, by - br), (dx + 13.0, by - br)], 1.0, BRASS_SHADE)
    f.poly([(310.0, by - br + 1.0), (312.0, by - br - 8.0), (320.0, by - br - 8.0), (322.0, by - br + 1.0)], BRASS)
    f.poly(_rect(313.0, by - br - 15.0, 319.0, by - br - 8.0), BRASS)
    f.ink([(314.2, by - br - 14.0), (314.2, by - br - 2.0)], 0.8, BRASS_LIGHT)
    # The whistle in front of the cab.
    f.limb([(304.0, by - br), (304.0, by - br - 10.0)], 1.6, BRASS)
    f.poly(_rect(302.0, by - br - 16.0, 306.0, by - br - 9.0), BRASS)
    # The side tank: a long box of water beside the boiler, lined out.
    t0, t1 = cab1, 410.0
    tt = top - 34.0
    f.poly([(t0, top), (t0, tt), (t1 - 6.0, tt), (t1, tt + 6.0), (t1, top)], ENGINE_GREEN)
    f.poly(_rect(t0, top - 8.0, t1, top), ENGINE_GREEN_SHADE, body=False)
    f.ink([(t0 + 4.0, top - 11.0), (t0 + 4.0, tt + 4.0), (t1 - 7.0, tt + 4.0), (t1 - 4.0, tt + 7.0), (t1 - 4.0, top - 11.0), (t0 + 4.0, top - 11.0)], 0.9, GOLD)
    f.ink([(t0 + 1.0, tt + 1.4), (t1 - 6.0, tt + 1.4)], 1.0, ENGINE_GREEN_LIGHT)
    for k in range(9):
        f.dot(t0 + 6.0 + k * 13.0, tt + 2.6, 0.7, ENGINE_GREEN_SHADE)
    # The smokebox, black, and its door at the front.
    # Under the boiler, in front of the tank, the frames show.
    f.poly(_rect(t1 - 2.0, by + br - 2.0, b1 + 2.0, top), ENGINE_BLACK)
    f.poly(_rect(t1 + 6.0, top - 14.0, t1 + 16.0, top), ENGINE_GREEN)
    f.ink([(t1 + 7.0, top - 12.6), (t1 + 15.0, top - 12.6)], 0.8, ENGINE_GREEN_LIGHT)
    s0, s1 = b1, 472.0
    f.poly([(s0 + 4.0, by + br), (s1 - 6.0, by + br), (s1 - 2.0, top), (s0, top)], ENGINE_BLACK)
    f.poly(_rect(s0, by - br - 1.0, s1, by + br + 1.0), ENGINE_BLACK)
    f.poly([(s1, by - br + 2.0), (s1 + 5.0, by - br + 6.0), (s1 + 5.0, by + br - 6.0), (s1, by + br - 2.0)], ENGINE_BLACK)
    f.ink([(s0 + 3.0, by - br + 3.0), (s1 - 3.0, by - br + 3.0)], 1.0, ENGINE_BLACK_LIGHT)
    f.ink([(s0 + 1.0, by + br + 1.0), (s1 - 1.0, by + br + 1.0)], 0.8, ENGINE_BLACK_LIGHT)
    f.dot(s1 + 3.0, by + 1.0, 1.6, STEEL)
    # The chimney: tall and thin, with a flared cap of copper.
    ch = 455.0
    cap = 38.0
    f.poly([(ch - 7.0, by - br), (ch - 5.0, cap + 10.0), (ch + 5.0, cap + 10.0), (ch + 7.0, by - br)], ENGINE_BLACK)
    f.poly([(ch - 10.0, by - br), (ch - 7.0, by - br - 6.0), (ch + 7.0, by - br - 6.0), (ch + 10.0, by - br)], ENGINE_BLACK)
    f.poly([(ch - 5.0, cap + 10.0), (ch - 10.0, cap + 2.0), (ch - 11.0, cap - 1.0), (ch + 11.0, cap - 1.0), (ch + 10.0, cap + 2.0), (ch + 5.0, cap + 10.0)], COPPER)
    f.ink([(ch - 8.0, cap + 2.0), (ch - 4.0, cap + 8.0)], 1.0, COPPER_LIGHT)
    f.ink([(ch - 3.0, cap + 12.0), (ch - 3.6, by - br - 8.0)], 1.0, ENGINE_BLACK_LIGHT)
    # The headlamp on the front of the running plate.
    f.poly(_rect(476.0, top - 12.0, 484.0, top - 2.0), ENGINE_BLACK)
    f.poly(_rect(483.0, top - 10.0, 486.0, top - 4.0), BRASS_LIGHT)
    # The running plate: a long ledge from the bunker to the front. Its
    # top is the platform. A red buffer beam closes each end.
    f.poly(_rect(e0 + 6.0, top, e1, top + 6.0), ENGINE_BLACK)
    f.ink([(e0 + 7.0, top + 0.6), (e1 - 1.0, top + 0.6)], 0.8, ENGINE_BLACK_LIGHT)
    f.poly(_rect(e0 + 6.0, top + 6.0, e1, top + 9.0), ENGINE_GREEN, body=False)
    for bx, s in ((e0 + 6.0, -1.0), (e1, 1.0)):
        f.poly(_rect(min(bx, bx + s * 6.0), top + 1.0, max(bx, bx + s * 6.0), top + 17.0), BUFFER_RED)
        f.ink([(bx + s * 3.0, top + 3.0), (bx + s * 3.0, top + 15.0)], 0.8, BUFFER_RED_LIGHT)
        f.poly(_rect(min(bx + s * 6.0, bx + s * 10.0), top + 6.0, max(bx + s * 6.0, bx + s * 10.0), top + 12.0), STEEL)
        f.ellipse(bx + s * 11.0, top + 9.0, 1.8, 4.8, STEEL)
    # The guard irons in front of the leading wheels.
    f.limb([(e1 - 4.0, top + 17.0), (e1 - 2.0, rail - 4.0)], 1.6, ENGINE_BLACK)

    # ---- The smoke: puffs that rise from the chimney and drift back ----
    for k in range(4):
        u = (ph + k / 4.0) % 1.0
        x = ch - 4.0 - 60.0 * u
        y = cap - 4.0 - 14.0 * u
        r = 4.5 + 5.5 * u
        _puff(f, x, max(1.2 * r + 5.0, y), r, K.alpha(SMOKE, 0.95 - 0.55 * u), random.Random(f"history_meiji_train smoke {k}"), 5,
              shade=K.alpha(SMOKE_SHADE, 0.6 * (1.0 - u)))
    return A.finish(f, width=1.4)


# ---------------------------------------------------------------------------
# The wreck at Takashima.
# ---------------------------------------------------------------------------


def _draw_mongol_wreck(anim: str, i: int, n: int):
    w, h = MONGOL_WRECK_FRAME
    f = K.Frame(MONGOL_WRECK_FRAME)
    rng = random.Random("history_mongol_wreck")
    sand_y = h - 14.0
    # The beach behind the wreck.
    f.poly([(8.0, sand_y + 2.0), (40.0, sand_y - 3.0), (120.0, sand_y - 4.0), (220.0, sand_y - 6.0), (300.0, sand_y - 2.0), (w - 8.0, sand_y + 2.0),
            (w - 10.0, h - 6.0), (10.0, h - 6.0)], SAND)
    # The keel and the keelson: long timbers that lie along the bottom.
    f.poly([(28.0, 134.0), (180.0, 134.0), (180.0, 141.0), (30.0, 141.0)], TIMBER_SHADE)
    f.ink([(30.0, 135.4), (178.0, 135.4)], 0.8, TIMBER)
    # The far side of the hull: its inner face shows, in shade, over the
    # broken top of the near side.
    far = [(150.0, 140.0), (150.0, 82.0), (170.0, 77.0), (200.0, 70.0), (232.0, 63.0), (262.0, 56.0), (268.0, 56.0), (268.0, 140.0)]
    f.poly(far, WRECK_INSIDE)
    # The bare frames (ribs) of the bow. Each is a curved timber that rises
    # from the keel and bends out at the turn of the bilge. The far ribs
    # bend the other way, so the frames make the shape of the hull. Some
    # are broken short. They rise toward the stern, as the hull did.
    ribs = [(40.0, 22.0), (55.0, 32.0), (70.0, 28.0), (85.0, 44.0), (100.0, 40.0), (115.0, 54.0), (130.0, 50.0)]
    for x, tall in ribs:
        f.limb([(x + 2.0, 136.0), (x + 9.0, 132.0 - tall * 0.35), (x + 11.0 + tall * 0.08, 140.0 - tall * 0.9)], 3.0, TIMBER_SHADE)
    # A long stringer still joins the far ribs, broken off at the bow.
    f.limb([(62.0, 120.0), (100.0, 110.0), (140.0, 98.0)], 3.4, TIMBER_SHADE)
    for x, tall in ribs:
        mid = (x - 5.0, 132.0 - tall * 0.35)
        tip = (x - 7.0 - tall * 0.1, 138.0 - tall)
        f.limb([(x + 2.0, 138.0), mid, tip], 4.4, TIMBER)
        f.ink([(x + 1.0, 136.0), (mid[0] + 0.9, mid[1]), (tip[0] + 0.9, tip[1] + 2.0)], 0.8, TIMBER_LIGHT)
        f.poly([(tip[0] - 2.4, tip[1] + 1.4), (tip[0] - 1.4, tip[1] - 2.0), (tip[0] + 0.4, tip[1] + 0.4), (tip[0] + 1.6, tip[1] - 1.6), (tip[0] + 2.4, tip[1] + 1.6)], TIMBER_END)
    # A few planks of the bottom still hang on the near frames. Their ends
    # are broken and ragged.
    for y0, xa, xb in ((128.0, 30.0, 92.0), (120.0, 66.0, 124.0)):
        f.poly([(xa, y0 + 1.0), (xa + 3.0, y0), (xb - 4.0, y0 - 2.0), (xb, y0), (xb - 3.0, y0 + 2.4), (xb + 1.0, y0 + 4.0), (xb - 2.0, y0 + 5.0), (xa + 3.0, y0 + 7.0),
                (xa - 1.0, y0 + 5.0)], TIMBER_LIGHT)
        f.ink([(xa + 3.0, y0 + 3.6), (xb - 5.0, y0 + 1.8)], 0.6, TIMBER_SHADE)
        for x in range(int(xa) + 8, int(xb) - 4, 15):
            f.dot(float(x), y0 + 3.4 - (x - xa) * 0.03, 0.9, TIMBER_DARK)
    # The bulkhead: a wall of thick planks across the hull. The near side
    # breaks off in front of it, so its face shows a little from the bow.
    bk0, bk1 = 140.0, 160.0
    bulk = [(bk0, 140.0), (bk0, 86.0), (bk1, 80.0), (bk1, 140.0)]
    f.poly(bulk, TIMBER_LIGHT)
    for k in range(1, 9):
        y = 140.0 - k * 6.6
        f.ink([(bk0 + 0.6, y + 0.8), (bk1 - 0.6, y - 0.6)], 0.8, TIMBER_SHADE)
    f.limb([(bk0 + 2.0, 139.0), (bk0 + 2.0, 87.0)], 2.4, TIMBER_SHADE)
    f.poly([(bk0, 86.0), (bk0 + 4.0, 82.0), (bk0 + 9.0, 85.0), (bk0 + 14.0, 80.0), (bk1, 80.0), (bk1, 83.0), (bk0, 89.0)], TIMBER_END)
    # The planked stern: the near side, with the broken top edge. Its
    # strakes run along the hull and rise to the stern.
    def sheer(x: float) -> float:
        return _lerp(84.0, 58.0, (x - bk1) / (266.0 - bk1))

    xs = [bk1 + (266.0 - bk1) * k / 24.0 for k in range(25)]
    broken = [(x, sheer(x) + (rng.uniform(2.0, 7.0) if 0 < k < 24 and k % 3 != 0 else 0.0)) for k, x in enumerate(xs)]
    def bottom(x: float) -> float:
        """The bottom of the hull: level, then it curves up under the
        high stern."""
        u = max(0.0, (x - 226.0) / (276.0 - 226.0))
        return 141.0 - 22.0 * u * u

    run = [bk1 + (274.0 - bk1) * k / 30.0 for k in range(31)]
    side = broken + [(272.0, 72.0)] + [(x, bottom(x)) for x in reversed(run)]
    f.poly(side, TIMBER)
    f.poly([(x, _lerp(sheer(min(x, 266.0)) + 6.0, bottom(x), 0.82)) for x in run] + [(x, bottom(x)) for x in reversed(run)], TIMBER_SHADE, body=False)
    for k in range(1, 9):
        u = k / 9.0
        f.ink([(x, _lerp(sheer(min(x, 266.0)) + 6.0, bottom(x) - 1.0, u)) for x in run[:-1]], 0.8, TIMBER_SHADE)
    f.limb([(x, sheer(min(x, 266.0)) + 12.0) for x in (bk1 + 1.0, 270.0)], 3.6, TIMBER_DARK)
    f.ink([(bk1 + 2.0, sheer(bk1) + 10.8), (269.0, sheer(266.0) + 10.8)], 0.8, TIMBER)
    for x in range(int(bk1) + 10, 268, 14):
        f.dot(float(x), _lerp(sheer(bk1) + 24.0, sheer(266.0) + 24.0, (x - bk1) / 108.0), 1.0, TIMBER_DARK)
    f.ink([(p[0], p[1] + 1.0) for p in broken[1:-1]], 0.8, TIMBER_LIGHT)
    # A hole where planks are gone shows the dark inside.
    f.poly([(196.0, 112.0), (208.0, 106.0), (222.0, 108.0), (226.0, 116.0), (214.0, 122.0), (200.0, 120.0)], WRECK_INSIDE, body=False)
    f.limb([(206.0, 107.0), (205.0, 121.0)], 2.2, TIMBER_SHADE, body=False)
    # Weed and shells on the low strakes.
    for _ in range(14):
        x = rng.uniform(bk1 + 4.0, 266.0)
        y = rng.uniform(126.0, 136.0)
        f.ink([(x, y), (x + rng.uniform(-2.0, 2.0), y + rng.uniform(2.0, 4.0))], 1.0, WEED)
    # The broken mast stump: it rises from the hull, tilted, and its top
    # is split.
    m_foot, m_top = (206.0, 86.0), (200.0, 30.0)
    f.limb([m_foot, m_top], 9.0, TIMBER_SHADE)
    f.ink([(m_foot[0] - 2.4, m_foot[1]), (m_top[0] - 2.2, m_top[1] + 4.0)], 1.4, TIMBER_LIGHT)
    f.poly([(m_top[0] - 5.0, m_top[1] + 2.0), (m_top[0] - 3.0, m_top[1] - 6.0), (m_top[0] - 1.0, m_top[1] - 1.0), (m_top[0] + 1.0, m_top[1] - 8.0),
            (m_top[0] + 3.0, m_top[1] - 2.0), (m_top[0] + 5.0, m_top[1] + 2.0)], TIMBER_END)
    for y in (48.0, 62.0):
        f.limb([(m_top[0] - 5.0 + (y - 30.0) * 0.1, y), (m_top[0] + 5.0 + (y - 30.0) * 0.1, y + 1.0)], 2.0, TIMBER_DARK)
    # The stern: a high flat transom. The great rudder hangs in its
    # socket; its stock rises above the transom and its blade is half in
    # the sand.
    f.poly([(266.0, 56.0), (276.0, 54.0), (280.0, 118.0), (273.0, 120.0)], TIMBER_SHADE)
    f.ink([(271.0, 58.0), (276.0, 117.0)], 0.8, TIMBER)
    stock_top, stock_foot = (284.0, 36.0), (292.0, 128.0)
    blade = [(282.0, 90.0), (306.0, 96.0), (312.0, 110.0), (312.0, sand_y - 2.0), (286.0, sand_y - 2.0)]
    f.poly(blade, TIMBER)
    f.poly([(300.0, 94.0), (306.0, 96.0), (312.0, 110.0), (312.0, sand_y - 2.0), (304.0, sand_y - 2.0)], TIMBER_SHADE, body=False)
    for k in range(1, 4):
        y = 92.0 + k * 9.0
        f.ink([(285.0, y + 1.0), (311.0, y + 4.0)], 0.8, TIMBER_SHADE)
    # The rudder of a junk has holes in its blade: it steers as well, and
    # is lighter to turn.
    for hx, hy in ((298.0, 106.0), (300.0, 118.0), (302.0, 130.0)):
        f.poly([(hx, hy - 3.6), (hx + 2.6, hy), (hx, hy + 3.6), (hx - 2.6, hy)], WRECK_INSIDE, body=False)
    f.limb([stock_top, stock_foot], 7.0, TIMBER_DARK)
    f.ink([(stock_top[0] - 1.4, stock_top[1] + 2.0), (stock_foot[0] - 1.4, stock_foot[1] - 6.0)], 1.0, TIMBER)
    f.limb([(276.0, 64.0), (292.0, 64.0)], 3.4, TIMBER_DARK)
    f.ellipse(stock_top[0], stock_top[1], 4.0, 3.0, TIMBER_END)
    f.limb([(279.0, 47.0), (292.0, 45.0)], 2.6, TIMBER_SHADE)
    # The sand that drifted against the hull, in front of it.
    f.poly([(10.0, h - 6.0), (14.0, sand_y), (40.0, sand_y - 6.0), (90.0, sand_y - 4.0), (150.0, sand_y - 9.0), (196.0, sand_y - 5.0), (240.0, sand_y - 10.0),
            (284.0, sand_y - 4.0), (308.0, sand_y), (w - 10.0, h - 6.0)], SAND)
    f.poly([(20.0, h - 6.0), (60.0, sand_y + 1.0), (140.0, sand_y), (230.0, sand_y - 2.0), (300.0, sand_y + 2.0), (w - 14.0, h - 6.0)], SAND_SHADE, body=False)
    f.ink([(40.0, sand_y - 4.4), (88.0, sand_y - 2.8)], 1.0, SAND_LIGHT)
    f.ink([(156.0, sand_y - 7.6), (196.0, sand_y - 3.8)], 1.0, SAND_LIGHT)
    f.ink([(236.0, sand_y - 8.6), (276.0, sand_y - 4.0)], 1.0, SAND_LIGHT)
    # The stone anchor stock: a long bar of granite that lies in the sand,
    # thick in the middle and tapered at the ends, with a socket for the
    # wooden shank.
    a0, a1, ay = 18.0, 124.0, h - 12.0
    mid = (a0 + a1) / 2.0
    f.poly([(a0, ay), (a0 + 6.0, ay - 6.0), (mid - 10.0, ay - 10.0), (mid + 10.0, ay - 10.0), (a1 - 6.0, ay - 6.0), (a1, ay), (a1 - 4.0, ay + 3.0),
            (a0 + 4.0, ay + 3.0)], GRANITE)
    f.poly([(a0 + 2.0, ay), (a1 - 2.0, ay), (a1 - 4.0, ay + 3.0), (a0 + 4.0, ay + 3.0)], GRANITE_SHADE, body=False)
    f.ink([(a0 + 7.0, ay - 4.6), (mid - 10.0, ay - 8.4), (mid - 6.0, ay - 8.4)], 1.2, GRANITE_LIGHT)
    f.ink([(mid + 8.0, ay - 8.4), (a1 - 10.0, ay - 5.4)], 1.0, GRANITE_LIGHT)
    # The socket in the middle, where the wooden shank of the anchor sat.
    f.poly(_rect(mid - 5.0, ay - 10.0, mid + 5.0, ay - 1.0), GRANITE_SHADE, body=False)
    f.ink([(mid - 5.0, ay - 9.4), (mid + 5.0, ay - 9.4)], 0.8, TIMBER_DARK)
    for _ in range(22):
        x = rng.uniform(a0 + 6.0, a1 - 6.0)
        y = rng.uniform(ay - 6.0, ay + 1.0)
        f.dot(x, y, 0.5, GRANITE_SHADE)
    # Sand drifted over one end of the stock.
    f.poly([(a1 - 18.0, h - 6.0), (a1 - 10.0, ay - 1.0), (a1 + 2.0, ay - 3.0), (a1 + 12.0, h - 6.0)], SAND, body=False)
    f.ink([(a1 - 9.0, ay - 0.6), (a1 + 1.0, ay - 2.4)], 0.8, SAND_LIGHT)
    return A.finish(f, width=1.4)


# ---------------------------------------------------------------------------
# The ceramic bombs (tetsuhau).
# ---------------------------------------------------------------------------


def _bomb(f: K.Frame, cx: float, cy: float, r: float, neck: float, seed: str) -> None:
    """A round bomb of stoneware: a sphere with a short neck at the angle
    `neck` (degrees), a plug in the neck, and a fuse of cord that hangs
    from it."""
    rng = random.Random(seed)
    a = math.radians(neck)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    base = (cx + ux * (r - 1.0), cy + uy * (r - 1.0))
    lip = (cx + ux * (r + 4.6), cy + uy * (r + 4.6))
    f.poly([(base[0] + nx * 3.8, base[1] + ny * 3.8), (lip[0] + nx * 2.8, lip[1] + ny * 2.8), (lip[0] - nx * 2.8, lip[1] - ny * 2.8), (base[0] - nx * 3.8, base[1] - ny * 3.8)], STONEWARE_SHADE)
    f.ellipse(cx, cy, r, r, STONEWARE)
    f.poly(_ring(cx, cy, r, r, 20.0, 160.0, 14) + _ring(cx - 1.0, cy - 2.4, r - 2.0, r - 3.0, 160.0, 20.0, 14), STONEWARE_SHADE, body=False)
    f.ink(_ring(cx - 1.0, cy - 1.0, r - 3.0, r - 3.0, 200.0, 250.0, 8), 1.4, STONEWARE_LIGHT)
    # The coarse skin of the stoneware: a few small pits.
    for _ in range(4):
        d = rng.uniform(r * 0.3, r - 3.0)
        t = rng.uniform(math.radians(20.0), math.radians(160.0))
        f.dot(cx + math.cos(t) * d, cy + math.sin(t) * d * 0.7, 0.5, GLAZE)
    f.ellipse(lip[0], lip[1], 3.0, 3.0, STONEWARE)
    f.ellipse(lip[0], lip[1], 1.8, 1.8, GLAZE, body=False)
    # The fuse: a cord out of the plug that bends over.
    tip = (lip[0] + ux * 4.0 + nx * 3.0, lip[1] + uy * 4.0 + ny * 3.0 + 2.0)
    f.limb([lip, (lip[0] + ux * 4.0, lip[1] + uy * 4.0), tip, (tip[0] + nx * 2.0, tip[1] + 3.0)], 1.3, CORD)


def _draw_tetsuhau(anim: str, i: int, n: int):
    w, h = TETSUHAU_FRAME
    f = K.Frame(TETSUHAU_FRAME)
    ground = h - 6.0
    r = 10.0
    # The back row and the bomb on top of the pile.
    _bomb(f, 33.0, ground - r - 15.0, r, -120.0, "tetsuhau a")
    _bomb(f, 55.0, ground - r - 14.0, r, -60.0, "tetsuhau b")
    # The front row.
    _bomb(f, 22.0, ground - r, r, -150.0, "tetsuhau c")
    _bomb(f, 44.0, ground - r + 0.4, r, -95.0, "tetsuhau d")
    _bomb(f, 66.0, ground - r, r, -40.0, "tetsuhau e")
    # The bomb in a net of straw rope, set apart. The cords of the net go
    # round it like the lines of a globe, and meet in a loop to carry it.
    cx, cy = 90.0, ground - r
    _bomb(f, cx, cy, r, -90.0, "tetsuhau f")
    for rx in (3.4, 7.0):
        f.ink(_ring(cx, cy, rx, r - 0.4, 270.0, 450.0, 16), 0.8, STRAW_SHADE)
        f.ink(_ring(cx, cy, rx, r - 0.4, 90.0, 270.0, 16), 0.8, STRAW_SHADE)
    for v in (-0.5, 0.0, 0.5):
        y = cy + v * r
        half = math.sqrt(max(0.0, r * r - (y - cy) ** 2)) - 0.4
        f.ink([(cx - half, y), (cx + half, y)], 0.8, STRAW_SHADE)
        for rx in (-7.0, -3.4, 3.4, 7.0):
            f.dot(cx + rx * math.sqrt(max(0.0, 1.0 - v * v)), y, 0.9, STRAW)
    f.limb([(cx - 6.0, cy - 8.0), (cx - 4.0, cy - 16.0), (cx, cy - 19.0), (cx + 4.0, cy - 16.0), (cx + 6.0, cy - 8.0)], 1.4, STRAW)
    f.ink([(cx - 4.4, cy - 15.0), (cx - 1.0, cy - 18.0)], 0.6, (236, 214, 150, 255))
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# The handscroll of Takezaki Suenaga.
# ---------------------------------------------------------------------------


def _gold_cloud(f: K.Frame, x0: float, x1: float, y: float, hh: float) -> None:
    """A band of gold cloud (suyari-gasumi): a long flat cloud with round
    ends, that hides part of the scene."""
    f.poly(_ring(x0 + hh, y, hh, hh, 90.0, 270.0, 8) + _ring(x1 - hh, y, hh, hh, 270.0, 450.0, 8), GOLD, body=False)
    f.ink([(x0 + hh, y - hh + 0.6), (x1 - hh, y - hh + 0.6)], 0.5, GOLD_LIGHT)


def _horseman(f: K.Frame, x: float, y: float, coat: RGBA, armour: RGBA, facing: float = 1.0, k: float = 1.0) -> None:
    """A small rider of the scroll, at rest on his horse, drawn in ink
    lines and flat paint. `y` is the foot of the hooves and `k` the size.
    The bow is held upright."""
    s = facing

    def P(dx: float, dy: float) -> Point:
        return (x + s * dx * k, y + dy * k)

    for lx, ly in ((-3.6, 0.0), (-2.2, 0.4), (2.6, 0.0), (3.8, 0.4)):
        f.ink([P(lx, -5.0), P(lx + 0.3 * s, ly)], 0.7 * k, INK_BLACK if lx in (-2.2, 3.8) else coat)
    body = _ring(0.0, -6.4, 5.0, 2.6, 0.0, 360.0, 16)
    f.poly([P(px, py) for px, py in body], coat, body=False)
    f.poly([P(3.0, -8.0), P(5.6, -12.0), P(8.2, -11.0), P(8.0, -9.8), P(5.6, -7.0), P(4.4, -5.6)], coat, body=False)
    f.ink([P(px, py) for px, py in body], 0.35 * k, INK_BLACK)
    f.ink([P(3.0, -8.0), P(5.6, -12.0), P(8.2, -11.0), P(8.0, -9.8), P(5.6, -7.0)], 0.35 * k, INK_BLACK)
    f.ink([P(-5.0, -7.0), P(-6.6, -3.4)], 0.7 * k, INK_BLACK)
    f.ink([P(4.4, -11.6), P(6.4, -13.0)], 0.6 * k, INK_BLACK)
    # The rider: armour, a small helmet, and the bow upright behind him.
    f.poly([P(-1.6, -8.4), P(1.6, -8.4), P(1.4, -13.0), P(-1.2, -13.0)], armour, body=False)
    f.ink([P(-1.6, -8.4), P(1.6, -8.4), P(1.4, -13.0), P(-1.2, -13.0), P(-1.6, -8.4)], 0.3 * k, INK_BLACK)
    f.ink([P(1.0, -7.6), P(1.6, -5.4)], 0.6 * k, armour)
    f.dot(*P(0.2, -14.2), 1.1 * k, INK_BLACK)
    f.ink([P(-2.4, -19.0), P(-3.4, -13.0), P(-2.4, -7.0)], 0.45 * k, INK_BLACK)


def _draw_suenaga_scroll(anim: str, i: int, n: int):
    w, h = SUENAGA_SCROLL_FRAME
    f = K.Frame(SUENAGA_SCROLL_FRAME)
    rng = random.Random("history_suenaga_scroll")
    foot = h - 6.0
    # The stand: a low table of black lacquer with curved legs, and on it
    # a sloped board that holds the scroll open to be seen.
    t0, t1 = 16.0, w - 16.0
    tt = 66.0
    for x, s in ((t0 + 10.0, -1.0), (t1 - 10.0, 1.0)):
        f.limb([(x, tt + 4.0), (x + s * 2.0, foot - 8.0), (x + s * 8.0, foot - 2.0)], 4.2, LACQUER)
        f.limb([(x + s * 4.0, foot - 2.0), (x + s * 12.0, foot - 2.0)], 3.0, LACQUER)
    f.limb([(t0 + 12.0, foot - 12.0), (t1 - 12.0, foot - 12.0)], 2.0, LACQUER)
    f.poly([(t0 - 4.0, tt), (t1 + 4.0, tt), (t1 + 2.0, tt + 6.0), (t0 - 2.0, tt + 6.0)], LACQUER)
    f.ink([(t0 - 2.0, tt + 1.0), (t1 + 2.0, tt + 1.0)], 0.8, LACQUER_LIGHT)
    f.ink([(t0, tt + 4.4), (t1, tt + 4.4)], 0.8, GOLD)
    # The board, tilted toward us: black lacquer with a lip at its foot.
    b0, b1 = 36.0, 156.0
    bt, bb = 30.0, tt - 2.0
    f.poly([(b0 + 2.0, bt), (b1 - 2.0, bt), (b1, bb), (b0, bb)], LACQUER)
    f.poly(_rect(t0 + 6.0, bb - 3.0, t1 - 6.0, bb + 2.0), LACQUER_RED)
    f.ink([(t0 + 8.0, bb - 2.0), (t1 - 8.0, bb - 2.0)], 0.6, LACQUER_RED_LIGHT)
    # The open scroll: paper from the left roll to the right roll.
    p0, p1 = 40.0, 154.0
    py0, py1 = 28.0, 58.0
    f.poly(_rect(p0, py0, p1, py1), PAPER)
    f.ink([(p0, py0 + 1.0), (p1, py0 + 1.0)], 0.6, PAPER_SHADE)
    f.ink([(p0, py1 - 1.0), (p1, py1 - 1.0)], 0.6, PAPER_SHADE)
    # The scene is read from right to left. At the right, a band of text in
    # columns of short strokes.
    for k in range(6):
        _writing_column(f, p1 - 6.0 - k * 4.0, py0 + 4.0, py1 - 4.0, rng, INK_BLACK, 1.0)
    # Gold clouds frame the scenes.
    _gold_cloud(f, p0 + 2.0, p0 + 40.0, py0 + 3.6, 2.6)
    _gold_cloud(f, p0 + 56.0, p0 + 96.0, py0 + 3.0, 2.4)
    _gold_cloud(f, p0 + 30.0, p0 + 70.0, py1 - 3.4, 2.4)
    f.ink([(p1 - 30.0, py0 + 2.0), (p1 - 30.0, py1 - 2.0)], 0.5, PAPER_SHADE)
    # Two horsemen ride along the shore, the near one on a white horse.
    f.ink([(p0 + 42.0, py1 - 6.4), (p0 + 80.0, py1 - 7.0)], 0.6, PAINT_GREEN)
    _horseman(f, p0 + 52.0, py1 - 6.0, HORSE_BROWN, PAINT_RED, -1.0, 1.3)
    _horseman(f, p0 + 70.0, py1 - 7.0, HORSE_WHITE, PAINT_BLUE, -1.0, 1.3)
    # A ship of the fleet on the waves, at the left.
    sx, sy = p0 + 18.0, py1 - 12.0
    f.poly([(sx - 13.0, sy - 3.0), (sx + 12.0, sy - 3.0), (sx + 9.0, sy + 2.0), (sx - 10.0, sy + 2.0)], HORSE_BROWN, body=False)
    f.ink([(sx - 12.0, sy - 3.0), (sx + 11.0, sy - 3.0)], 0.6, INK_BLACK)
    f.ink([(sx, sy - 3.0), (sx, sy - 14.0)], 0.6, INK_BLACK)
    f.poly([(sx - 6.0, sy - 13.0), (sx + 5.0, sy - 13.0), (sx + 5.0, sy - 5.0), (sx - 6.0, sy - 5.0)], PAPER_SHADE, body=False)
    for k in range(3):
        f.ink([(sx - 6.0, sy - 11.0 + k * 2.6), (sx + 5.0, sy - 11.0 + k * 2.6)], 0.4, INK_BLACK)
    for k in range(5):
        x = p0 + 3.0 + k * 7.0
        f.ink(_ring(x, py1 - 7.0, 3.0, 1.6, 180.0, 360.0, 6), 0.6, SEA_PAINT)
        f.ink(_ring(x + 3.4, py1 - 4.0, 3.0, 1.6, 180.0, 360.0, 6), 0.6, SEA_PAINT)
    # The stone wall on the shore behind the horsemen.
    f.poly(_rect(p0 + 40.0, py1 - 25.0, p0 + 84.0, py1 - 21.0), (196, 186, 166, 255), body=False)
    for k in range(9):
        f.ink([(p0 + 42.0 + k * 5.0, py1 - 25.0), (p0 + 42.0 + k * 5.0, py1 - 21.0)], 0.4, INK_BLACK)
    f.ink([(p0 + 40.0, py1 - 23.0), (p0 + 84.0, py1 - 23.0)], 0.3, INK_BLACK)
    # The rolled ends. At the left is the unread part, rolled on its
    # roller, with the ivory knobs of the roller above and below. At the right
    # is the read part, rolled more thinly.
    for cx, rr, knob in ((p0 - 6.0, 7.0, True), (p1 + 4.0, 4.6, False)):
        f.poly(_rect(cx - rr, py0 - 1.0, cx + rr, py1 + 1.0), SCROLL_BACK)
        f.poly(_rect(cx + rr * 0.3, py0 - 1.0, cx + rr, py1 + 1.0), K.shade(SCROLL_BACK, 0.8), body=False)
        f.ink([(cx - rr * 0.5, py0), (cx - rr * 0.5, py1)], 0.9, SCROLL_BACK_LIGHT)
        f.ink([(cx - rr, py0 + 2.0), (cx + rr, py0 + 2.0)], 0.5, GOLD)
        f.ink([(cx - rr, py1 - 2.0), (cx + rr, py1 - 2.0)], 0.5, GOLD)
        if knob:
            for y in (py0 - 4.0, py1 + 4.0):
                f.ellipse(cx, y, 3.4, 3.0, IVORY)
                f.ellipse(cx + 0.8, y + 0.6, 2.0, 1.6, IVORY_SHADE, body=False)
                f.dot(cx - 1.0, y - 0.8, 0.9, (252, 248, 236, 255))
        else:
            f.limb([(cx + rr + 1.0, py0 + 2.0), (cx + rr + 1.0, py1 - 2.0)], 1.4, GOLD_SHADE)
    # The silk cord that ties the scroll, loose on the board.
    f.limb([(p1 + 9.0, py0 + 8.0), (p1 + 13.0, py0 + 14.0), (p1 + 12.0, bb - 8.0), (p1 + 16.0, bb - 4.0)], 1.0, (150, 96, 160, 255))
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# The print stall of Edo.
# ---------------------------------------------------------------------------


def _print_wave(f: K.Frame, x0: float, y0: float, x1: float, y1: float) -> None:
    """A print after Hokusai's great wave, simplified: a high wave with a
    claw of foam, a small wave, and a small cone of a mountain."""
    pw, ph = x1 - x0, y1 - y0

    def p(u: float, v: float) -> Point:
        return (x0 + u * pw, y0 + v * ph)

    f.poly(_rect(x0, y0, x1, y1), PRINT_SKY, body=False)
    f.poly([p(0.0, 0.0), p(1.0, 0.0), p(1.0, 0.16), p(0.0, 0.16)], (210, 196, 170, 255), body=False)
    # The mountain, small and far, under the wave.
    f.poly([p(0.56, 0.86), p(0.66, 0.66), p(0.76, 0.86)], PRUSSIAN, body=False)
    f.poly([p(0.62, 0.74), p(0.66, 0.66), p(0.70, 0.74)], FOAM, body=False)
    # The great wave: it rises at the left and curls over to the right.
    wave = [p(0.0, 1.0), p(0.0, 0.62), p(0.10, 0.40), p(0.24, 0.24), p(0.40, 0.20), p(0.52, 0.28), p(0.56, 0.40), p(0.48, 0.38), p(0.42, 0.46),
            p(0.40, 0.62), p(0.48, 0.80), p(0.60, 0.92), p(1.0, 0.92), p(1.0, 1.0)]
    f.poly(wave, PRUSSIAN, body=False)
    f.poly([p(0.08, 1.0), p(0.12, 0.66), p(0.22, 0.46), p(0.30, 0.56), p(0.26, 0.78), p(0.34, 1.0)], PRUSSIAN_LIGHT, body=False)
    # The claws of foam on the crest.
    for k in range(5):
        u = 0.30 + k * 0.06
        v = 0.22 + 0.04 * abs(k - 2)
        f.ink([p(u, v), p(u + 0.04, v + 0.08), p(u + 0.01, v + 0.10)], 0.7, FOAM)
    f.ink([p(0.12, 0.40), p(0.26, 0.26), p(0.40, 0.22), p(0.52, 0.30)], 0.8, FOAM)
    # A small wave in front, with its own crest.
    f.poly([p(0.62, 1.0), p(0.70, 0.84), p(0.80, 0.80), p(0.88, 0.86), p(0.94, 1.0)], PRUSSIAN, body=False)
    f.ink([p(0.70, 0.84), p(0.80, 0.80), p(0.88, 0.86)], 0.6, FOAM)


def _print_mountain(f: K.Frame, x0: float, y0: float, x1: float, y1: float) -> None:
    """A landscape print: a red mountain against a pale sky, with green
    hills and a band of cloud."""
    pw, ph = x1 - x0, y1 - y0
    f.poly(_rect(x0, y0, x1, y1), PRINT_SKY, body=False)
    f.poly(_rect(x0, y0, x1, y0 + ph * 0.25), PRUSSIAN_LIGHT, body=False)
    f.poly([(x0, y1), (x0 + pw * 0.5, y0 + ph * 0.28), (x1, y1)], (176, 72, 50, 255), body=False)
    f.poly([(x0 + pw * 0.38, y0 + ph * 0.40), (x0 + pw * 0.5, y0 + ph * 0.28), (x0 + pw * 0.62, y0 + ph * 0.40), (x0 + pw * 0.55, y0 + ph * 0.44),
            (x0 + pw * 0.45, y0 + ph * 0.42)], FOAM, body=False)
    f.poly([(x0, y1), (x0, y0 + ph * 0.80), (x0 + pw * 0.4, y0 + ph * 0.86), (x1, y0 + ph * 0.78), (x1, y1)], PINE, body=False)
    f.ink([(x0 + pw * 0.1, y0 + ph * 0.6), (x0 + pw * 0.9, y0 + ph * 0.6)], 0.8, (244, 236, 220, 255))


def _print_bridge(f: K.Frame, x0: float, y0: float, x1: float, y1: float) -> None:
    """A landscape print: an arched wooden bridge over a blue river, with
    small figures with umbrellas on it."""
    pw, ph = x1 - x0, y1 - y0
    f.poly(_rect(x0, y0, x1, y1), PRINT_DUSK, body=False)
    f.poly(_rect(x0, y0 + ph * 0.6, x1, y1), PRUSSIAN, body=False)
    f.ink([(x0 + 2.0, y0 + ph * 0.75), (x1 - 4.0, y0 + ph * 0.75)], 0.5, PRUSSIAN_LIGHT)
    arch = _ring(x0 + pw * 0.5, y0 + ph * 0.68, pw * 0.48, ph * 0.26, 180.0, 360.0, 12)
    f.ink(arch, 1.4, CEDAR_DARK)
    for k in range(1, 6):
        q = arch[k * 2]
        f.ink([q, (q[0], y0 + ph * 0.72)], 0.6, CEDAR_DARK)
    for u, colour in ((0.38, KIMONO_BLACK), (0.56, KIMONO_RED)):
        q = (x0 + pw * u, y0 + ph * 0.42)
        f.ink([(q[0], q[1] + 1.0), (q[0], q[1] - 2.2)], 1.0, colour)
        f.ink([(q[0] - 1.8, q[1] - 2.6), (q[0] + 1.8, q[1] - 2.6)], 0.9, PRUSSIAN_LIGHT)


def _print_actor(f: K.Frame, x0: float, y0: float, x1: float, y1: float, robe: RGBA, pattern: RGBA, ground: RGBA) -> None:
    """A print of an actor of the kabuki stage: half a figure in a bold
    robe on a plain ground. The face is plain and calm."""
    pw, ph = x1 - x0, y1 - y0
    cx = x0 + pw * 0.5
    f.poly(_rect(x0, y0, x1, y1), ground, body=False)
    # The robe: wide shoulders and long sleeves.
    f.poly([(x0 + pw * 0.08, y1), (x0 + pw * 0.14, y0 + ph * 0.52), (cx - pw * 0.12, y0 + ph * 0.40), (cx + pw * 0.12, y0 + ph * 0.40),
            (x1 - pw * 0.14, y0 + ph * 0.52), (x1 - pw * 0.08, y1)], robe, body=False)
    for k in range(4):
        y = y0 + ph * (0.58 + k * 0.1)
        f.ink([(x0 + pw * 0.2, y), (x1 - pw * 0.2, y)], 0.6, pattern)
    f.ink([(cx - pw * 0.12, y0 + ph * 0.42), (cx, y0 + ph * 0.62), (cx + pw * 0.12, y0 + ph * 0.42)], 0.8, FACE)
    # The face and the hair: an oval face, and dark hair dressed on top.
    f.ellipse(cx, y0 + ph * 0.30, pw * 0.13, ph * 0.11, FACE, body=False)
    f.poly([(cx - pw * 0.15, y0 + ph * 0.28), (cx - pw * 0.13, y0 + ph * 0.18), (cx, y0 + ph * 0.13), (cx + pw * 0.13, y0 + ph * 0.18), (cx + pw * 0.15, y0 + ph * 0.28),
            (cx + pw * 0.10, y0 + ph * 0.22), (cx - pw * 0.10, y0 + ph * 0.22)], HAIR, body=False)
    f.ellipse(cx, y0 + ph * 0.11, pw * 0.07, ph * 0.04, HAIR, body=False)


def _hung_print(f: K.Frame, x0: float, y0: float, pw: float, ph: float, painter: Callable[..., None], *extra) -> None:
    """A print hung over the string by its top edge, with a white margin."""
    f.poly(_rect(x0, y0, x0 + pw, y0 + ph), FOAM)
    painter(f, x0 + 1.4, y0 + 1.4, x0 + pw - 1.4, y0 + ph - 1.4, *extra)
    f.ink([(x0 + pw * 0.3, y0 - 0.4), (x0 + pw * 0.3, y0 + 1.6)], 1.0, STRING)
    f.ink([(x0 + pw * 0.7, y0 - 0.4), (x0 + pw * 0.7, y0 + 1.6)], 1.0, STRING)


def _draw_ukiyoe_stall(anim: str, i: int, n: int):
    w, h = UKIYOE_STALL_FRAME
    f = K.Frame(UKIYOE_STALL_FRAME)
    rng = random.Random("history_ukiyoe_stall")
    ground = h - 6.0
    s0, s1 = 18.0, w - 18.0
    board = 142.0
    eave = 52.0
    # The back wall of the stall: upright boards in shade.
    f.poly(_rect(s0 + 4.0, eave, s1 - 4.0, board), CEDAR_SHADE)
    for k in range(1, 13):
        x = s0 + 4.0 + k * (s1 - s0 - 8.0) / 13.0
        f.ink([(x, eave + 2.0), (x, board - 1.0)], 0.8, CEDAR_DARK)
    # The two posts at the front, which hold the roof.
    for x in (s0 + 2.0, s1 - 2.0):
        f.limb([(x, ground - 1.0), (x, eave - 2.0)], 6.0, CEDAR)
        f.ink([(x - 1.6, ground - 3.0), (x - 1.6, eave)], 1.0, CEDAR_LIGHT)
    # The strings between the posts, and the prints that hang on them.
    rows = (78.0, 110.0)
    for y in rows:
        f.ink([(s0 + 4.0, y), (w / 2.0, y + 2.0), (s1 - 4.0, y)], 0.8, STRING)
    _hung_print(f, 28.0, 79.0, 30.0, 21.0, _print_wave)
    _hung_print(f, 64.0, 80.0, 20.0, 28.0, _print_actor, KIMONO_RED, KIMONO_BLACK, MICA)
    _hung_print(f, 92.0, 81.0, 20.0, 28.0, _print_mountain)
    _hung_print(f, 118.0, 81.0, 20.0, 28.0, _print_actor, KIMONO_BLACK, (226, 220, 210, 255), (214, 186, 120, 255))
    _hung_print(f, 146.0, 80.0, 30.0, 21.0, _print_bridge)
    _hung_print(f, 182.0, 79.0, 20.0, 28.0, _print_actor, KIMONO_GREEN, KIMONO_BLACK, MICA)
    _hung_print(f, 32.0, 112.0, 20.0, 27.0, _print_mountain)
    _hung_print(f, 58.0, 112.0, 20.0, 27.0, _print_actor, KIMONO_PURPLE, (234, 214, 150, 255), (200, 176, 160, 255))
    _hung_print(f, 146.0, 112.0, 20.0, 27.0, _print_actor, KIMONO_RED, (240, 230, 214, 255), (170, 196, 204, 255))
    _hung_print(f, 172.0, 112.0, 30.0, 21.0, _print_wave)
    # The board: a low stand of planks on short legs, with prints laid on
    # it in stacks and in a fan.
    f.poly(_rect(s0 + 2.0, board, s1 - 2.0, board + 6.0), CEDAR_LIGHT)
    f.poly(_rect(s0 + 6.0, board + 6.0, s1 - 6.0, board + 30.0), CEDAR)
    f.poly(_rect(s0 + 6.0, board + 24.0, s1 - 6.0, board + 30.0), CEDAR_SHADE, body=False)
    for k in range(1, 4):
        x = s0 + 6.0 + k * (s1 - s0 - 12.0) / 4.0
        f.ink([(x, board + 7.0), (x, board + 29.0)], 0.9, CEDAR_DARK)
    for x in (s0 + 10.0, s1 - 10.0, w / 2.0):
        f.limb([(x, board + 30.0), (x, ground - 1.0)], 4.0, CEDAR_SHADE)
    f.ink([(s0 + 3.0, board + 1.0), (s1 - 3.0, board + 1.0)], 0.8, (226, 188, 140, 255))
    # The stacks of prints on the board, seen from the front: thin piles
    # with their top print showing a little.
    for x, ww, k_n, colour in ((34.0, 30.0, 5, PRUSSIAN), (80.0, 26.0, 3, KIMONO_RED), (150.0, 30.0, 4, PINE)):
        for k in range(k_n):
            y = board - 1.0 - k * 1.6
            f.poly(_rect(x + k * 0.6, y - 1.6, x + ww + k * 0.6, y), FOAM if k % 2 == 0 else (230, 224, 210, 255))
        f.poly(_rect(x + k_n * 0.6 + 2.0, board - 1.0 - k_n * 1.6 - 1.2, x + ww + k_n * 0.6 - 2.0, board - 1.0 - k_n * 1.6 + 0.2), colour, body=False)
    # A print propped up against a small rack on the board, to be seen.
    f.limb([(120.0, board - 1.0), (124.0, board - 26.0)], 1.6, CEDAR_DARK)
    f.limb([(138.0, board - 1.0), (142.0, board - 26.0)], 1.6, CEDAR_DARK)
    f.poly([(112.0, board - 3.0), (116.0, board - 30.0), (138.0, board - 30.0), (134.0, board - 3.0)], FOAM)
    _print_actor(f, 115.4, board - 28.6, 134.6, board - 4.4, KIMONO_BLACK, KIMONO_RED, (226, 196, 140, 255))
    # The roof: a small roof of wooden shingles over the stall, its eave
    # reaching out past the posts.
    r0, r1 = 6.0, w - 6.0
    f.poly([(r0, eave), (r0 + 12.0, 24.0), (r1 - 12.0, 24.0), (r1, eave), (r1, eave + 5.0), (r0, eave + 5.0)], SHINGLE)
    for k in range(1, 5):
        y = 24.0 + k * 6.0
        xa, xb = _lerp(r0 + 12.0, r0, (y - 24.0) / (eave - 24.0)), _lerp(r1 - 12.0, r1, (y - 24.0) / (eave - 24.0))
        f.ink([(xa + 1.0, y), (xb - 1.0, y)], 0.8, SHINGLE_SHADE)
        x = xa + (3.0 if k % 2 else 0.0)
        while x < xb - 4.0:
            f.ink([(x, y - 5.4), (x, y - 0.6)], 0.5, SHINGLE_SHADE)
            x += rng.uniform(5.0, 8.0)
    f.ink([(r0 + 13.0, 25.4), (r1 - 13.0, 25.4)], 1.0, SHINGLE_LIGHT)
    f.limb([(r0 + 12.0, 23.0), (r1 - 12.0, 23.0)], 3.0, SHINGLE_SHADE)
    f.poly(_rect(r0, eave, r1, eave + 5.0), CEDAR_SHADE)
    f.ink([(r0 + 1.0, eave + 1.0), (r1 - 1.0, eave + 1.0)], 0.8, CEDAR)
    # The noren: a short curtain of indigo, split into panels, that hangs
    # from a rod under the eave. It carries no writing.
    f.limb([(s0 - 2.0, eave + 7.0), (s1 + 2.0, eave + 7.0)], 2.0, CEDAR_DARK)
    panels = 6
    pw = (s1 - s0 - 4.0) / panels
    for k in range(panels):
        px0 = s0 + 2.0 + k * pw + 0.8
        px1 = px0 + pw - 1.6
        sway = 0.6 * math.sin(k * 1.7)
        f.poly([(px0, eave + 7.0), (px1, eave + 7.0), (px1 + sway, eave + 22.0), (px0 + sway, eave + 22.0)], INDIGO)
        f.poly([(px1 - 4.0, eave + 7.0), (px1, eave + 7.0), (px1 + sway, eave + 22.0), (px1 - 4.0 + sway, eave + 22.0)], INDIGO_SHADE, body=False)
        f.ink([(px0 + 1.4, eave + 8.0), (px0 + 1.4 + sway, eave + 21.0)], 0.8, INDIGO_LIGHT)
        f.ink([(px0 + sway, eave + 19.0), (px1 + sway, eave + 19.0)], 0.8, (226, 230, 236, 255))
    return A.finish(f, width=1.3)


# ---------------------------------------------------------------------------
# The rickshaw (jinrikisha).
# ---------------------------------------------------------------------------


def _draw_jinrikisha(anim: str, i: int, n: int):
    w, h = JINRIKISHA_FRAME
    f = K.Frame(JINRIKISHA_FRAME)
    ground = h - 6.0
    # The parts are given in local units and drawn at the scale `k`. Then
    # the wheel is about 1.2 m high, at the scale of the other props.
    k = 0.75
    rl = 36.0
    r = rl * k
    axle = (50.0, ground - r)
    # The rickshaw is parked: its shafts rest on the ground, so the body
    # tips forward about the axle.
    tilt = 17.0
    shaft_len = 110.0

    def T(points: Sequence[Point]) -> List[Point]:
        return _turn([(axle[0] + x * k, axle[1] + y * k) for x, y in points], axle, tilt)

    # The far wheel and the far shaft show behind the body.
    f.ink(_ring(axle[0] + 4.0, axle[1] - 1.5, r - 1.0, r - 1.0, 170.0, 370.0, 30), 2.0, K.shade(TYRE, 0.9))
    f.limb(T([(-34.0, 2.0), (shaft_len - 8.0, 2.0)]), 2.6, RICKSHAW_WOOD_SHADE)
    # The hood: black cloth on folding ribs, half up. Its ribs fan out from
    # a pivot at the back of the seat; folded cloth hangs between them.
    piv = (-30.0, -52.0)
    a0, a1, hr = 158.0, 250.0, 34.0
    edge = _ring(piv[0], piv[1], hr, hr, a0, a1, 20)
    f.poly(T([piv] + edge), CLOTH)
    for a in (180.0, 204.0, 228.0):
        rib = _ring(piv[0], piv[1], hr - 1.0, hr - 1.0, a, a, 1)[0]
        f.ink(T([piv, rib]), 1.2, CLOTH_SHADE)
        f.ink(T([(piv[0] - 1.0, piv[1] - 1.0), _ring(piv[0], piv[1], hr - 3.0, hr - 3.0, a + 4.0, a + 4.0, 1)[0]]), 0.8, CLOTH_LIGHT)
    f.limb(T(edge), 2.4, CLOTH_SHADE)
    f.limb(T([piv, edge[-1]]), 1.8, CLOTH_SHADE)
    f.ink(T(_ring(piv[0], piv[1], hr - 2.0, hr - 2.0, a0 + 30.0, a1 - 6.0, 12)), 0.8, CLOTH_LIGHT)
    # The backrest and the cushion: red cloth, padded.
    f.poly(T([(-36.0, -70.0), (-28.0, -70.0), (-24.0, -46.0), (-34.0, -44.0)]), CUSHION)
    f.ink(T([(-31.0, -66.0), (-28.0, -48.0)]), 0.8, CUSHION_LIGHT)
    f.poly(T([(-30.0, -50.0), (10.0, -50.0), (13.0, -44.0), (-30.0, -44.0)]), CUSHION)
    f.ink(T([(-28.0, -49.0), (9.0, -49.0)]), 0.8, CUSHION_LIGHT)
    # The seat box: black lacquer with a gold line, and a curved front
    # that comes down to the footboard.
    side = [(-38.0, -50.0), (-32.0, -46.0), (-30.0, -44.0), (10.0, -44.0), (16.0, -38.0), (20.0, -16.0), (24.0, -8.0), (20.0, -4.0), (-36.0, -6.0)]
    f.poly(T(side), LACQUER)
    f.ink(T([(-33.0, -40.0), (8.0, -40.0), (13.0, -35.0), (16.0, -14.0), (-32.0, -12.0), (-33.0, -40.0)]), 0.9, GOLD)
    f.ink(T([(-36.0, -48.0), (-31.0, -45.0)]), 1.0, LACQUER_LIGHT)
    # The armrest: a curved rail along the top of the side, with a brass
    # knob at its front.
    f.limb(T([(-30.0, -56.0), (-4.0, -55.0), (8.0, -53.0), (12.0, -48.0)]), 2.4, LACQUER)
    f.limb(T([(-2.0, -55.0), (-1.0, -45.0)]), 1.6, LACQUER)
    f.ellipse(*T([(12.0, -47.0)])[0], 2.0, 2.0, BRASS)
    # The footboard in front of the seat, with a low dash at its front.
    f.poly(T([(18.0, -8.0), (52.0, -8.0), (52.0, -3.0), (20.0, -3.0)]), LACQUER)
    f.poly(T([(48.0, -8.0), (54.0, -22.0), (57.0, -22.0), (54.0, -3.0)]), LACQUER)
    f.ink(T([(22.0, -7.0), (50.0, -7.0)]), 0.8, LACQUER_LIGHT)
    # The near shaft: it runs under the body and out to the front, where
    # it rests on the ground. A crossbar joins the tips of the two shafts.
    f.limb(T([(-38.0, 2.0), (shaft_len, 2.0)]), 3.4, RICKSHAW_WOOD)
    f.ink(T([(-36.0, 1.0), (shaft_len - 2.0, 1.0)]), 0.8, RICKSHAW_WOOD_LIGHT)
    tip = T([(shaft_len, 2.0)])[0]
    f.ellipse(tip[0], tip[1] - 0.6, 2.6, 2.6, RICKSHAW_WOOD_SHADE)
    f.dot(tip[0], tip[1] - 0.6, 1.0, RICKSHAW_WOOD_LIGHT)
    # The spring under the body, from the body to the axle.
    f.limb(T([(-24.0, -4.0), (0.0, 1.0), (18.0, -4.0)]), 2.4, IRON)
    # The near wheel: tall and thin, with many thin wooden spokes and an
    # iron tyre, under a curved mudguard.
    _wheel(f, axle[0], axle[1], r, 16, 0.1, TYRE, RICKSHAW_WOOD, RICKSHAW_WOOD_LIGHT, tyre=2.2, spoke_w=1.0, hub=4.0)
    f.ink(_ring(axle[0], axle[1], r - 2.8, r - 2.8, 0.0, 360.0, 48), 1.2, RICKSHAW_WOOD)
    f.ellipse(axle[0], axle[1], 1.8, 1.8, BRASS, body=False)
    f.limb(T(_ring(0.0, 0.0, rl + 4.0, rl + 4.0, 200.0, 296.0, 18)), 2.2, LACQUER)
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# A brick shop front of Ginza.
# ---------------------------------------------------------------------------


def _sash_window(f: K.Frame, x0: float, y0: float, x1: float, y1: float) -> None:
    """A tall sash window with white frames: two sashes of six panes,
    a white lintel with a keystone over it, and a sill."""
    f.poly(_rect(x0, y0, x1, y1), TRIM)
    f.poly(_rect(x0 + 2.0, y0 + 2.0, x1 - 2.0, y1 - 2.0), GLASS, body=False)
    f.poly([(x0 + 2.0, y0 + 2.0), (x1 - 2.0, y0 + 2.0), (x0 + 2.0, y0 + (y1 - y0) * 0.5)], GLASS_DARK, body=False)
    f.ink([(x1 - 5.0, y0 + 6.0), (x1 - 8.0, y0 + 14.0)], 1.0, GLASS_LIGHT)
    ym = (y0 + y1) / 2.0
    for x in (_lerp(x0, x1, 1.0 / 3.0), _lerp(x0, x1, 2.0 / 3.0)):
        f.ink([(x, y0 + 2.0), (x, y1 - 2.0)], 0.8, TRIM)
    for y in (_lerp(y0, ym, 0.5), _lerp(ym, y1, 0.5)):
        f.ink([(x0 + 2.0, y), (x1 - 2.0, y)], 0.8, TRIM)
    f.limb([(x0 + 1.0, ym), (x1 - 1.0, ym)], 2.0, TRIM)
    f.poly([(x0 - 4.0, y0), (x0 - 2.0, y0 - 6.0), (x1 + 2.0, y0 - 6.0), (x1 + 4.0, y0)], TRIM)
    cx = (x0 + x1) / 2.0
    f.poly([(cx - 3.0, y0 + 1.0), (cx - 4.0, y0 - 7.0), (cx + 4.0, y0 - 7.0), (cx + 3.0, y0 + 1.0)], TRIM_LIGHT)
    f.poly(_rect(x0 - 3.0, y1, x1 + 3.0, y1 + 3.0), TRIM)
    f.ink([(x0 - 2.0, y1 + 2.6), (x1 + 2.0, y1 + 2.6)], 0.8, TRIM_SHADE)


def _column(f: K.Frame, x: float, top: float, foot: float, half: float) -> None:
    """A white column of the Tuscan order: a plain base, a round shaft and
    a simple capital."""
    f.poly(_rect(x - half - 3.0, foot - 5.0, x + half + 3.0, foot), TRIM)
    f.poly(_rect(x - half - 1.5, foot - 8.0, x + half + 1.5, foot - 5.0), TRIM)
    f.poly([(x - half, foot - 8.0), (x - half * 0.86, top + 6.0), (x + half * 0.86, top + 6.0), (x + half, foot - 8.0)], TRIM)
    f.poly([(x + half * 0.3, foot - 8.0), (x + half * 0.26, top + 6.0), (x + half * 0.86, top + 6.0), (x + half, foot - 8.0)], TRIM_SHADE, body=False)
    f.ink([(x - half * 0.5, foot - 9.0), (x - half * 0.44, top + 7.0)], 1.0, TRIM_LIGHT)
    f.poly(_rect(x - half - 1.0, top + 3.0, x + half + 1.0, top + 6.0), TRIM)
    f.poly(_rect(x - half - 3.0, top, x + half + 3.0, top + 3.0), TRIM)
    f.ink([(x - half - 2.0, foot - 0.6), (x + half + 2.0, foot - 0.6)], 0.8, TRIM_SHADE)


def _draw_ginza_brick(anim: str, i: int, n: int):
    w, h = GINZA_BRICK_FRAME
    f = K.Frame(GINZA_BRICK_FRAME)
    ground = h - 6.0
    x0, x1 = 14.0, w - 14.0
    roof_top, cornice = 12.0, 30.0
    floor2 = 132.0
    beam = 140.0
    # The roof of grey tiles shows a little over the cornice.
    f.poly([(x0 + 8.0, cornice), (x0 + 22.0, roof_top), (x1 - 22.0, roof_top), (x1 - 8.0, cornice)], ROOF_TILE)
    for k in range(1, 6):
        x = _lerp(x0 + 22.0, x1 - 22.0, k / 6.0)
        f.ink([(x, roof_top + 1.0), (x, cornice - 1.0)], 0.8, ROOF_TILE_SHADE)
    f.ink([(x0 + 14.0, roof_top + 8.0), (x1 - 14.0, roof_top + 8.0)], 0.8, ROOF_TILE_SHADE)
    f.limb([(x0 + 20.0, roof_top), (x1 - 20.0, roof_top)], 3.0, ROOF_TILE_SHADE)
    f.ink([(x0 + 24.0, roof_top + 2.4), (x1 - 24.0, roof_top + 2.4)], 0.8, ROOF_TILE_LIGHT)
    # The upper storey: a wall of red brick.
    f.poly(_rect(x0 + 4.0, cornice, x1 - 4.0, floor2), BRICK)
    _bricks(f, x0 + 4.0, x1 - 4.0, cornice + 6.0, floor2, 4.0, BRICK, "history_ginza_brick upper")
    # The cornice: white mouldings along the top of the wall.
    f.poly(_rect(x0, cornice, x1, cornice + 5.0), TRIM)
    f.poly(_rect(x0 + 2.0, cornice + 5.0, x1 - 2.0, cornice + 9.0), TRIM_SHADE)
    for k in range(23):
        x = x0 + 6.0 + k * 9.6
        f.poly(_rect(x, cornice + 9.0, x + 4.0, cornice + 12.0), TRIM)
    f.ink([(x0 + 1.0, cornice + 1.0), (x1 - 1.0, cornice + 1.0)], 1.0, TRIM_LIGHT)
    # White quoins at the corners of the wall.
    for k in range(10):
        y = cornice + 12.0 + k * 9.0
        for xa, s in ((x0 + 4.0, 1.0), (x1 - 4.0, -1.0)):
            ww = 9.0 if k % 2 == 0 else 6.0
            f.poly(_rect(min(xa, xa + s * ww), y, max(xa, xa + s * ww), y + 7.0), TRIM)
    # The three tall sash windows of the upper storey.
    for cx in (60.0, w / 2.0, w - 60.0):
        _sash_window(f, cx - 14.0, 58.0, cx + 14.0, 112.0)
    # The balcony over the colonnade: a white entablature on the columns
    # and a railing of white balusters on it.
    f.poly(_rect(x0 - 2.0, beam, x1 + 2.0, beam + 10.0), TRIM)
    f.poly(_rect(x0 - 2.0, beam + 7.0, x1 + 2.0, beam + 10.0), TRIM_SHADE, body=False)
    f.ink([(x0 - 1.0, beam + 1.0), (x1 + 1.0, beam + 1.0)], 1.0, TRIM_LIGHT)
    f.limb([(x0, floor2 - 14.0), (x1, floor2 - 14.0)], 2.4, TRIM)
    f.poly(_rect(x0, beam - 4.0, x1, beam), TRIM)
    for k in range(39):
        x = x0 + 4.0 + k * 5.85
        f.poly([(x - 1.2, beam - 4.0), (x - 1.6, beam - 9.0), (x, beam - 11.0), (x + 1.6, beam - 9.0), (x + 1.2, beam - 4.0)], TRIM, body=False)
        f.limb([(x, beam - 10.0), (x, floor2 - 14.0)], 1.4, TRIM)
    for x in (x0 + 2.0, (x0 + x1) / 2.0, x1 - 2.0):
        f.poly(_rect(x - 3.0, floor2 - 16.0, x + 3.0, beam), TRIM)
    # The ground storey, set back under the balcony, in shade.
    g0, g1 = x0 + 6.0, x1 - 6.0
    f.poly(_rect(g0, beam + 10.0, g1, ground), BRICK_SHADE)
    _bricks(f, g0, g1, beam + 10.0, ground, 4.0, BRICK_SHADE, "history_ginza_brick lower")
    # The shop door, with a short noren over it.
    d0, d1 = 34.0, 70.0
    f.poly(_rect(d0 - 3.0, beam + 18.0, d1 + 3.0, ground), TRIM_SHADE)
    f.poly(_rect(d0, beam + 21.0, d1, ground), DOOR_WOOD)
    f.ink([((d0 + d1) / 2.0, beam + 21.0), ((d0 + d1) / 2.0, ground)], 1.0, K.shade(DOOR_WOOD, 0.7))
    for xa, xb in ((d0 + 3.0, (d0 + d1) / 2.0 - 3.0), ((d0 + d1) / 2.0 + 3.0, d1 - 3.0)):
        f.poly(_rect(xa, beam + 46.0, xb, beam + 76.0), GLASS, body=False)
        f.ink([(xa, beam + 61.0), (xb, beam + 61.0)], 0.8, DOOR_WOOD_LIGHT)
        f.poly(_rect(xa, beam + 82.0, xb, ground - 4.0), DOOR_WOOD_LIGHT, body=False)
    f.dot((d0 + d1) / 2.0 - 2.4, beam + 72.0, 1.2, BRASS)
    f.dot((d0 + d1) / 2.0 + 2.4, beam + 72.0, 1.2, BRASS)
    f.limb([(d0 - 2.0, beam + 22.0), (d1 + 2.0, beam + 22.0)], 1.6, CEDAR_DARK)
    for k in range(3):
        nx0 = d0 + k * (d1 - d0) / 3.0 + 0.6
        nx1 = nx0 + (d1 - d0) / 3.0 - 1.2
        f.poly(_rect(nx0, beam + 22.0, nx1, beam + 42.0), INDIGO)
        f.poly(_rect(nx1 - 3.0, beam + 22.0, nx1, beam + 42.0), INDIGO_SHADE, body=False)
        f.ink([(nx0, beam + 38.0), (nx1, beam + 38.0)], 0.8, (226, 230, 236, 255))
    # The wide shop window: small panes in a white frame, and the goods
    # behind it: bolts of cloth and boxes on shelves.
    sw0, sw1 = 96.0, 222.0
    sy0, sy1 = beam + 36.0, ground - 22.0
    f.poly(_rect(sw0 - 3.0, sy0 - 3.0, sw1 + 3.0, sy1 + 3.0), TRIM)
    f.poly(_rect(sw0, sy0, sw1, sy1), GLASS_DARK, body=False)
    for k in range(3):
        y = sy0 + 12.0 + k * 15.0
        f.ink([(sw0, y), (sw1, y)], 1.2, CEDAR_DARK)
        x = sw0 + 3.0
        rng = random.Random(f"ginza goods {k}")
        while x < sw1 - 10.0:
            ww = rng.uniform(6.0, 11.0)
            hh = rng.uniform(5.0, 9.0)
            colour = (GOODS, KIMONO_RED, INDIGO_LIGHT, (226, 214, 180, 255), KIMONO_GREEN)[rng.randrange(5)]
            f.poly(_rect(x, y - hh, x + ww, y - 0.6), K.shade(colour, 0.8), body=False)
            x += ww + rng.uniform(1.5, 4.0)
    f.poly([(sw0, sy0), (sw0 + 40.0, sy0), (sw0 + 10.0, sy1), (sw0, sy1)], K.alpha(GLASS_LIGHT, 0.25), body=False)
    for k in range(1, 6):
        x = _lerp(sw0, sw1, k / 6.0)
        f.ink([(x, sy0), (x, sy1)], 1.2, TRIM)
    f.ink([(sw0, (sy0 + sy1) / 2.0), (sw1, (sy0 + sy1) / 2.0)], 1.0, TRIM)
    f.poly(_rect(sw0 - 3.0, sy1 + 3.0, sw1 + 3.0, ground), BRICK)
    _bricks(f, sw0 - 3.0, sw1 + 3.0, sy1 + 3.0, ground, 4.0, BRICK, "history_ginza_brick sill")
    # The signboard over the window: black lacquer with a gold edge, and
    # no writing on it.
    f.poly(_rect(sw0 + 6.0, beam + 16.0, sw1 - 6.0, beam + 30.0), LACQUER)
    f.ink([(sw0 + 8.0, beam + 18.0), (sw1 - 8.0, beam + 18.0), (sw1 - 8.0, beam + 28.0), (sw0 + 8.0, beam + 28.0), (sw0 + 8.0, beam + 18.0)], 0.8, GOLD)
    # The shade under the balcony falls on the wall behind the columns.
    f.poly(_rect(g0, beam + 10.0, g1, beam + 15.0), K.alpha(BRICK_SHADE, 0.8), body=False)
    # The pavement of the street.
    f.poly([(x0 - 6.0, ground), (x1 + 6.0, ground), (x1 + 8.0, h - 4.0), (x0 - 8.0, h - 4.0)], PAVEMENT)
    f.ink([(x0 - 5.0, ground + 0.6), (x1 + 5.0, ground + 0.6)], 0.8, PAVEMENT_SHADE)
    # The colonnade: white columns in front of the shop front, which hold
    # the balcony.
    for cx in (x0 + 6.0, 84.0, 172.0, x1 - 6.0):
        _column(f, cx, beam + 10.0, ground, 5.0)
    return A.finish(f, width=1.4)


# ---------------------------------------------------------------------------
# Publication.
# ---------------------------------------------------------------------------

FRAMES: Dict[str, Tuple[int, int]] = {
    "history_meiji_train": MEIJI_TRAIN_FRAME,
    "history_mongol_wreck": MONGOL_WRECK_FRAME,
    "history_tetsuhau": TETSUHAU_FRAME,
    "history_suenaga_scroll": SUENAGA_SCROLL_FRAME,
    "history_ukiyoe_stall": UKIYOE_STALL_FRAME,
    "history_jinrikisha": JINRIKISHA_FRAME,
    "history_ginza_brick": GINZA_BRICK_FRAME,
}
DRAW: Dict[str, Callable] = {
    "history_meiji_train": _draw_meiji_train,
    "history_mongol_wreck": _draw_mongol_wreck,
    "history_tetsuhau": _draw_tetsuhau,
    "history_suenaga_scroll": _draw_suenaga_scroll,
    "history_ukiyoe_stall": _draw_ukiyoe_stall,
    "history_jinrikisha": _draw_jinrikisha,
    "history_ginza_brick": _draw_ginza_brick,
}
DISPLAY = {
    "history_meiji_train": "Meiji Train",
    "history_mongol_wreck": "Mongol Wreck",
    "history_tetsuhau": "Tetsuhau",
    "history_suenaga_scroll": "Suenaga's Scroll",
    "history_ukiyoe_stall": "Ukiyo-e Stall",
    "history_jinrikisha": "Jinrikisha",
    "history_ginza_brick": "Ginza Brick",
}
#: The room of each prop: its last tag.
ROOMS = {
    "history_meiji_train": "meiji",
    "history_mongol_wreck": "kamakura",
    "history_tetsuhau": "kamakura",
    "history_suenaga_scroll": "kamakura",
    "history_ukiyoe_stall": "edo",
    "history_jinrikisha": "meiji",
    "history_ginza_brick": "meiji",
}
ROWS: Dict[str, List[Tuple[str, int, int]]] = {
    "history_meiji_train": LOOP,
}


def _foot(name: str) -> Dict[str, Tuple[float, float]]:
    w, h = FRAMES[name]
    return {"foot": (w / 2.0, float(h))}


#: The anchors of each prop. A platform has a "top" anchor at the middle of
#: the surface that a player stands on; the other props have a "foot".
ANCHORS: Dict[str, Dict[str, Tuple[float, float]]] = {name: _foot(name) for name in DISPLAY}
ANCHORS["history_meiji_train"] = {"top": ((MEIJI_TRAIN_SPAN[0] + MEIJI_TRAIN_SPAN[1]) / 2.0, MEIJI_TRAIN_TOP)}
TAGS: Dict[str, List[str]] = {name: ["prop", "scenery", "history", ROOMS[name]] for name in DISPLAY}
TAGS["history_meiji_train"] = ["prop", "platform", "history", ROOMS["history_meiji_train"]]

TARGETS: Dict[str, dict] = {
    name: _publisher(name, DISPLAY[name], ROWS.get(name, STILL), FRAMES[name], DRAW[name], ANCHORS[name], "Scenery", TAGS[name]) for name in DISPLAY
}
