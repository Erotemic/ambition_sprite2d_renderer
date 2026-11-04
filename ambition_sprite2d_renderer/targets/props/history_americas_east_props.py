"""The props of the Olmec heartland, the Maya city and the Taino islands (the History dimension).

The third pass of the History dimension grows the Americas floor east: the
Olmec of the Gulf coast (1,200 BCE), the Maya city (250-900 CE) and the
Taino of the Greater Antilles (1000-1492 CE). These props are drawn in the
cel style of the dimension's cast (`targets/characters/_history_americas_kit.py`):
flat colour, one shade, a bold warm outline. They show the skill and the
invention of these peoples with respect. Each is "an" object of its kind,
not a copy of one real artefact.

- ``history_colossal_head``: scenery, a colossal head of basalt in a
  helmet, as the Olmec carved them.
- ``history_rubber_balls``: scenery, a heap of black rubber balls beside a
  bowl of white latex. The Olmec made the first rubber: latex and the juice
  of a morning glory vine.
- ``history_cacao_tree``: scenery, a cacao tree with its pods growing
  straight out of the trunk.
- ``history_maya_pyramid``: scenery, a stepped temple pyramid with a stair
  up its front, a temple on top and a roof comb.
- ``history_maya_stela``: scenery, a carved stela of glyph blocks and
  bar-and-dot numbers.
- ``history_ballcourt_ring``: scenery, a stone ring set high in the sloped
  wall of a ballcourt.
- ``history_ballcourt_gate``: the look of a `LockWall` of 32 by 128 world
  units, drawn at 3 to 1: a gate of carved stone with a ballplayer in
  relief, a yoke at the waist, hitting the ball with the hip.
- ``history_bohio``: scenery, a round Taino house of cane walls under a
  cone of thatch.
- ``history_dugout_canoe``: the look of a sweeping platform (a
  `MovingPlatform` whose ``visual`` it is): a long canoe hollowed from one
  tree, with paddlers' seats. The top of its sides is the platform
  (`platform_looks.ron`: `CANOE_SPAN`, `CANOE_TOP`).
- ``history_hammock``: scenery, a cotton hammock slung between two posts. A
  rebound pad sits on it in the room.
- ``history_buren``: scenery, a round clay griddle on three stones with a
  disc of cassava bread on it.
- ``history_barbacoa``: scenery, a frame of green sticks over embers, with
  fish on it. Its ``idle`` row moves the embers and the smoke.
- ``history_ceiba_tree``: scenery, a huge ceiba with buttress roots and a
  wide flat crown.

The numbers are frame pixels; the game shows each prop at half its frame
(the gate at a third). No drop shadows: the game draws them.
"""

from __future__ import annotations

import math
import random
from typing import Callable, Dict, List, Tuple

from ..characters import _art_cast_kit as K
from ..characters import _history_americas_kit as A
from .art_props import _publisher

Point = Tuple[float, float]
STILL: List[Tuple[str, int, int]] = [("idle", 1, 1000)]
LOOP: List[Tuple[str, int, int]] = [("idle", 8, 120)]

HEAD_FRAME = (256, 320)
BALLS_FRAME = (128, 64)
CACAO_FRAME = (192, 256)
PYRAMID_FRAME = (384, 384)
STELA_FRAME = (96, 288)
RING_FRAME = (128, 192)
GATE_FRAME = (96, 384)
BOHIO_FRAME = (256, 256)
CANOE_FRAME = (384, 128)
CANOE_SPAN = (16.0, 368.0)
CANOE_TOP = 72.0
HAMMOCK_FRAME = (192, 128)
BUREN_FRAME = (128, 64)
BARBACOA_FRAME = (160, 128)
CEIBA_FRAME = (320, 384)

BASALT = (104, 102, 110, 255)
BASALT_LIGHT = (140, 138, 146, 255)
BASALT_SHADE = (76, 74, 84, 255)
BASALT_DARK = (50, 48, 58, 255)
LIMESTONE = (214, 204, 180, 255)
LIMESTONE_LIGHT = (236, 228, 208, 255)
LIMESTONE_SHADE = (170, 158, 134, 255)
LIMESTONE_DARK = (124, 112, 92, 255)
MAYA_RED = (178, 64, 46, 255)
MAYA_RED_SHADE = (132, 44, 34, 255)
GLYPH = (88, 64, 50, 255)
RUBBER = (46, 40, 36, 255)
RUBBER_LIGHT = (96, 86, 76, 255)
LATEX = (246, 242, 230, 255)
CLAY = (186, 116, 70, 255)
CLAY_LIGHT = (214, 150, 100, 255)
CLAY_SHADE = (140, 82, 50, 255)
BARK = (122, 92, 66, 255)
BARK_LIGHT = (156, 124, 92, 255)
BARK_DARK = (84, 60, 42, 255)
CEIBA_BARK = (170, 168, 150, 255)
CEIBA_LIGHT = (200, 198, 180, 255)
CEIBA_SHADE = (130, 128, 112, 255)
LEAF = (70, 138, 64, 255)
LEAF_LIGHT = (120, 180, 90, 255)
LEAF_SHADE = (44, 100, 50, 255)
LEAF_NEW = (184, 96, 70, 255)
POD_YELLOW = (230, 184, 60, 255)
POD_ORANGE = (220, 120, 48, 255)
POD_RED = (160, 50, 54, 255)
GRASS = (110, 160, 70, 255)
GRASS_SHADE = (74, 120, 52, 255)
CANE = (206, 184, 120, 255)
CANE_SHADE = (160, 136, 80, 255)
CANE_DARK = (120, 98, 56, 255)
THATCH = (196, 160, 92, 255)
THATCH_LIGHT = (226, 196, 128, 255)
THATCH_SHADE = (150, 116, 62, 255)
WOOD = (150, 104, 64, 255)
WOOD_LIGHT = (184, 136, 90, 255)
WOOD_SHADE = (110, 74, 44, 255)
BIXA = (192, 64, 42, 255)
COTTON = (240, 232, 214, 255)
COTTON_SHADE = (204, 192, 168, 255)
ROPE = (176, 150, 104, 255)
CASSAVA = (240, 226, 186, 255)
CASSAVA_SHADE = (212, 190, 140, 255)
STONE = (150, 144, 134, 255)
STONE_LIGHT = (186, 180, 170, 255)
STONE_SHADE = (112, 106, 98, 255)
EMBER = (255, 132, 50, 255)
EMBER_HOT = (255, 214, 120, 255)
COAL = (60, 44, 40, 255)
ASH = (200, 192, 182, 255)
SMOKE = (196, 190, 184, 255)
STICK = (122, 150, 76, 255)
STICK_SHADE = (88, 112, 54, 255)
FISH = (150, 166, 178, 255)
FISH_SHADE = (106, 120, 134, 255)
FISH_BROWN = (176, 122, 70, 255)


def _rect(x0: float, y0: float, x1: float, y1: float) -> List[Point]:
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def _phase(i: int, n: int) -> float:
    return i / float(max(1, n))


def _grass(f: K.Frame, x0: float, x1: float, foot: float, seed: str, h0: float = 5.0, h1: float = 11.0) -> None:
    """A fringe of grass along the foot of a prop."""
    rng = random.Random(seed)
    f.poly([(x0, foot), (x1, foot), (x1, foot - 3.0), (x0, foot - 3.0)], GRASS_SHADE)
    x = x0 + 2.0
    while x < x1 - 2.0:
        h = rng.uniform(h0, h1)
        lean = rng.uniform(-3.0, 3.0)
        f.poly([(x - 2.0, foot - 1.0), (x + lean, foot - h), (x + 2.0, foot - 1.0)], GRASS if rng.random() < 0.6 else GRASS_SHADE)
        x += rng.uniform(3.0, 6.0)


def _blocks(f: K.Frame, x0: float, x1: float, y0: float, y1: float, seed: str, shade_colour, rh: Tuple[float, float] = (12.0, 16.0),
            rw: Tuple[float, float] = (18.0, 30.0)) -> None:
    """Courses of cut stone between `x0`..`x1` and `y0` (top)..`y1`: joints only."""
    rng = random.Random(seed)
    y = y0
    row = 0
    while y < y1 - 3.0:
        h = min(y1 - y, rng.uniform(*rh))
        f.ink([(x0 + 1.0, y), (x1 - 1.0, y)], 0.9, shade_colour)
        x = x0 + (rng.uniform(4.0, 12.0) if row % 2 else rng.uniform(0.0, 4.0))
        while True:
            x += rng.uniform(*rw)
            if x > x1 - 6.0:
                break
            f.ink([(x, y + 1.0), (x, y + h - 1.0)], 0.9, shade_colour)
        y += h
        row += 1


# ---------------------------------------------------------------------------
# The colossal head.
# ---------------------------------------------------------------------------


def _draw_head(anim: str, i: int, n: int):
    w, h = HEAD_FRAME
    f = K.Frame(HEAD_FRAME)
    foot = h - 6.0
    cx = w / 2.0
    # The ear flaps of the helmet hang down the sides, behind the face.
    for s in (-1.0, 1.0):
        x0 = cx + s * 104.0
        x1 = cx + s * 80.0
        f.poly([(x0, 104.0), (x1, 100.0), (cx + s * 82.0, 236.0), (cx + s * 100.0, 246.0), (cx + s * 110.0, 220.0)], BASALT_SHADE)
        # A round earspool on the flap.
        ex = cx + s * 98.0
        f.ellipse(ex, 196.0, 11.0, 15.0, BASALT)
        f.ellipse(ex, 196.0, 5.0, 7.0, BASALT_DARK, body=False)
    # The face: broad, heavy cheeks, a strong flat chin, sitting on its base.
    face = [(cx - 84.0, 112.0), (cx + 84.0, 112.0), (cx + 90.0, 160.0), (cx + 88.0, 214.0), (cx + 80.0, 262.0), (cx + 64.0, 292.0),
            (cx + 36.0, foot), (cx - 36.0, foot), (cx - 64.0, 292.0), (cx - 80.0, 262.0), (cx - 88.0, 214.0), (cx - 90.0, 160.0)]
    f.poly(face, BASALT)
    # The planes of the face, in shade on the right and light on the left.
    f.poly([(cx + 50.0, 120.0), (cx + 84.0, 112.0), (cx + 90.0, 160.0), (cx + 88.0, 214.0), (cx + 80.0, 262.0), (cx + 64.0, 292.0),
            (cx + 36.0, foot), (cx + 20.0, foot), (cx + 52.0, 280.0), (cx + 66.0, 230.0), (cx + 62.0, 170.0)], BASALT_SHADE, body=False)
    f.poly([(cx - 70.0, 130.0), (cx - 40.0, 124.0), (cx - 52.0, 170.0), (cx - 70.0, 200.0), (cx - 80.0, 180.0)], BASALT_LIGHT, body=False)
    # The heavy brow, and the eyes under it: almond shaped, heavy lidded.
    f.ink([(cx - 70.0, 146.0), (cx - 40.0, 138.0), (cx - 12.0, 144.0)], 2.0, BASALT_DARK)
    f.ink([(cx + 12.0, 144.0), (cx + 40.0, 138.0), (cx + 70.0, 146.0)], 2.0, BASALT_DARK)
    for s in (-1.0, 1.0):
        ex = cx + s * 40.0
        eye = [(ex - 22.0, 162.0), (ex - 8.0, 152.0), (ex + 10.0, 152.0), (ex + 22.0, 160.0), (ex + 8.0, 168.0), (ex - 10.0, 168.0)]
        f.poly(eye, BASALT_LIGHT, body=False)
        f.poly([(ex - 22.0, 162.0), (ex - 8.0, 152.0), (ex + 10.0, 152.0), (ex + 22.0, 160.0), (ex + 8.0, 158.0), (ex - 10.0, 157.0)], BASALT_SHADE,
               body=False)
        f.ink(eye + [eye[0]], 1.4, BASALT_DARK)
        f.ellipse(ex + s * 2.0, 162.0, 4.0, 4.0, BASALT_DARK, body=False)
    # The nose: broad and flat, its wide nostrils flared.
    f.poly([(cx - 10.0, 150.0), (cx + 10.0, 150.0), (cx + 18.0, 200.0), (cx + 30.0, 214.0), (cx + 24.0, 226.0), (cx, 230.0), (cx - 24.0, 226.0),
            (cx - 30.0, 214.0), (cx - 18.0, 200.0)], BASALT_LIGHT, body=False)
    f.poly([(cx + 4.0, 152.0), (cx + 10.0, 150.0), (cx + 18.0, 200.0), (cx + 30.0, 214.0), (cx + 24.0, 226.0), (cx + 4.0, 228.0)], BASALT, body=False)
    for s in (-1.0, 1.0):
        f.ellipse(cx + s * 14.0, 220.0, 6.0, 3.6, BASALT_DARK, body=False)
        f.ink([(cx + s * 30.0, 214.0), (cx + s * 34.0, 204.0), (cx + s * 22.0, 196.0)], 1.4, BASALT_DARK)
    # The lips: full, the corners turned down, a little apart.
    f.poly([(cx - 34.0, 252.0), (cx - 14.0, 240.0), (cx, 244.0), (cx + 14.0, 240.0), (cx + 34.0, 252.0), (cx, 254.0)], BASALT_LIGHT, body=False)
    f.poly([(cx - 34.0, 252.0), (cx, 256.0), (cx + 34.0, 252.0), (cx + 22.0, 270.0), (cx, 274.0), (cx - 22.0, 270.0)], BASALT, body=False)
    f.ink([(cx - 36.0, 254.0), (cx - 14.0, 254.0), (cx, 257.0), (cx + 14.0, 254.0), (cx + 36.0, 254.0)], 2.0, BASALT_DARK)
    f.ink([(cx - 36.0, 254.0), (cx - 40.0, 262.0)], 1.4, BASALT_DARK)
    f.ink([(cx + 36.0, 254.0), (cx + 40.0, 262.0)], 1.4, BASALT_DARK)
    f.ink([(cx - 22.0, 270.0), (cx, 275.0), (cx + 22.0, 270.0)], 1.4, BASALT_SHADE)
    # The cheeks.
    f.ink([(cx - 58.0, 200.0), (cx - 54.0, 232.0), (cx - 44.0, 250.0)], 1.6, BASALT_SHADE)
    f.ink([(cx + 58.0, 200.0), (cx + 54.0, 232.0), (cx + 44.0, 250.0)], 1.6, BASALT_DARK)
    # The helmet: a close cap, a band across the brow with a row of raised
    # ovals, and the crown of the cap above.
    cap = [(cx - 104.0, 112.0), (cx - 106.0, 70.0), (cx - 90.0, 36.0), (cx - 56.0, 16.0), (cx, 10.0), (cx + 56.0, 16.0), (cx + 90.0, 36.0),
           (cx + 106.0, 70.0), (cx + 104.0, 112.0)]
    f.poly(cap, BASALT)
    f.poly([(cx + 40.0, 18.0), (cx + 56.0, 16.0), (cx + 90.0, 36.0), (cx + 106.0, 70.0), (cx + 104.0, 112.0), (cx + 84.0, 104.0), (cx + 82.0, 60.0),
            (cx + 62.0, 30.0)], BASALT_SHADE, body=False)
    f.poly([(cx - 80.0, 40.0), (cx - 50.0, 22.0), (cx - 10.0, 18.0), (cx - 48.0, 34.0), (cx - 76.0, 56.0)], BASALT_LIGHT, body=False)
    band = [(cx - 106.0, 86.0), (cx + 106.0, 86.0), (cx + 104.0, 124.0), (cx - 104.0, 124.0)]
    f.poly(band, BASALT)
    f.poly([(cx + 70.0, 86.0), (cx + 106.0, 86.0), (cx + 104.0, 124.0), (cx + 70.0, 124.0)], BASALT_SHADE, body=False)
    f.ink([(cx - 104.0, 87.0), (cx + 104.0, 87.0)], 1.6, BASALT_DARK)
    f.ink([(cx - 102.0, 123.0), (cx + 102.0, 123.0)], 1.6, BASALT_DARK)
    for k in range(9):
        x = cx - 88.0 + k * 22.0
        f.ellipse(x, 105.0, 7.0, 11.0, BASALT_LIGHT if k < 6 else BASALT, body=False)
        f.ink([(x - 7.0, 105.0), (x, 94.0), (x + 7.0, 105.0), (x, 116.0), (x - 7.0, 105.0)], 1.0, BASALT_DARK)
    # The pocks of the hard stone, and lichen.
    rng = random.Random("history_colossal_head")
    for _ in range(26):
        x, y = rng.uniform(cx - 80.0, cx + 80.0), rng.uniform(30.0, 300.0)
        f.dot(x, y, rng.uniform(0.6, 1.2), BASALT_DARK)
    for _ in range(6):
        x, y = rng.uniform(cx - 90.0, cx + 90.0), rng.uniform(20.0, 80.0)
        f.ellipse(x, y, rng.uniform(3.0, 6.0), rng.uniform(2.0, 4.0), K.alpha((170, 182, 120, 255), 0.8), body=False)
    _grass(f, cx - 96.0, cx + 96.0, foot, "head:grass", 6.0, 14.0)
    return A.finish(f, width=1.6)


# ---------------------------------------------------------------------------
# Rubber balls and a bowl of latex.
# ---------------------------------------------------------------------------


def _ball(f: K.Frame, x: float, y: float, r: float) -> None:
    f.ellipse(x, y, r, r, RUBBER)
    f.ellipse(x - r * 0.35, y - r * 0.4, r * 0.35, r * 0.25, RUBBER_LIGHT, body=False)
    f.ink([(x - r * 0.7, y + r * 0.1), (x - r * 0.1, y + r * 0.5), (x + r * 0.7, y + r * 0.2)], 0.7, RUBBER_LIGHT)


def _draw_balls(anim: str, i: int, n: int):
    w, h = BALLS_FRAME
    f = K.Frame(BALLS_FRAME)
    foot = h - 5.0
    # The bowl of latex, white and thick, and the morning glory vine beside it.
    f.poly([(80.0, foot - 18.0), (118.0, foot - 18.0), (112.0, foot - 4.0), (104.0, foot), (94.0, foot), (86.0, foot - 4.0)], CLAY)
    f.poly([(102.0, foot - 18.0), (118.0, foot - 18.0), (112.0, foot - 4.0), (104.0, foot), (100.0, foot)], CLAY_SHADE, body=False)
    f.ellipse(99.0, foot - 18.0, 19.0, 4.0, CLAY_LIGHT)
    f.ellipse(99.0, foot - 18.0, 15.0, 2.8, LATEX, body=False)
    f.ink([(88.0, foot - 11.0), (110.0, foot - 11.0)], 0.9, CLAY_SHADE)
    for k, (vx, vy) in enumerate(((116.0, foot - 3.0), (119.0, foot - 11.0), (114.0, foot - 21.0))):
        f.ellipse(vx, vy, 4.0, 3.0, LEAF if k % 2 else LEAF_LIGHT)
    f.ellipse(118.0, foot - 25.0, 3.0, 2.4, (190, 150, 220, 255))
    f.dot(118.0, foot - 25.0, 0.9, K.WHITE)
    # The heap of balls: big ones at the back, a few in front.
    for x, y, r in ((28.0, foot - 30.0, 11.0), (50.0, foot - 32.0, 12.0), (18.0, foot - 11.0, 10.0), (40.0, foot - 13.0, 13.0), (63.0, foot - 12.0, 12.0),
                    (78.0, foot - 7.0, 7.0)):
        _ball(f, x, y, r)
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# The cacao tree.
# ---------------------------------------------------------------------------


def _pod(f: K.Frame, x: float, y: float, length: float, angle: float, colour) -> None:
    """A cacao pod: long, ridged, pointed at its end, hanging from a short stalk."""
    pts = [(-length * 0.5, 0.0), (-length * 0.3, -length * 0.28), (length * 0.2, -length * 0.3), (length * 0.5, -length * 0.08),
           (length * 0.62, 0.0), (length * 0.5, length * 0.08), (length * 0.2, length * 0.3), (-length * 0.3, length * 0.28)]
    pts = K.turn([(x + px, y + py) for px, py in pts], x, y, angle)
    f.poly(pts, colour)
    for s in (-0.14, 0.0, 0.14):
        a = K.turn([(x - length * 0.4, y + s * length), (x + length * 0.4, y + s * length * 0.6)], x, y, angle)
        f.ink(a, 0.8, K.shade(colour, 0.72))
    a = K.turn([(x - length * 0.25, y - length * 0.14), (x + length * 0.1, y - length * 0.2)], x, y, angle)
    f.ink(a, 1.0, K.shade(colour, 1.3))


def _big_leaf(f: K.Frame, base: Point, angle: float, length: float, width: float, colour) -> None:
    x, y = base
    pts = [(0.0, 0.0), (length * 0.3, -width), (length * 0.75, -width * 0.8), (length, 0.0), (length * 0.75, width * 0.8), (length * 0.3, width)]
    pts = K.turn([(x + px, y + py) for px, py in pts], x, y, angle)
    f.poly(pts, colour)
    f.ink(K.turn([(x, y), (x + length * 0.9, y)], x, y, angle), 0.7, LEAF_SHADE)


def _draw_cacao(anim: str, i: int, n: int):
    w, h = CACAO_FRAME
    f = K.Frame(CACAO_FRAME)
    foot = h - 6.0
    rng = random.Random("history_cacao_tree")
    # The leaves at the back of the crown.
    for _ in range(26):
        x, y = rng.uniform(26.0, 166.0), rng.uniform(22.0, 104.0)
        _big_leaf(f, (x, y), rng.uniform(60.0, 130.0), rng.uniform(22.0, 30.0), 7.6, LEAF_SHADE)
    # The trunk and its few low branches.
    f.limb([(92.0, foot - 6.0), (94.0, 160.0), (92.0, 112.0)], 12.0, BARK)
    f.poly([(80.0, foot), (104.0, foot), (99.0, foot - 10.0), (86.0, foot - 10.0)], BARK)
    f.limb([(93.0, 140.0), (60.0, 96.0), (40.0, 70.0)], 7.0, BARK)
    f.limb([(93.0, 128.0), (128.0, 90.0), (152.0, 66.0)], 7.0, BARK)
    f.limb([(92.0, 112.0), (96.0, 60.0)], 6.0, BARK)
    f.ink([(88.0, foot - 4.0), (90.0, 120.0)], 1.2, BARK_LIGHT)
    for k in range(6):
        y = foot - 12.0 - k * 18.0
        f.dot(95.0 + (k % 2) * 2.0, y, 1.2, BARK_DARK)
    # The leaves in front: long, hanging; a few new ones in bronze red.
    for k in range(22):
        x, y = rng.uniform(22.0, 170.0), rng.uniform(16.0, 100.0)
        colour = LEAF_NEW if k % 7 == 3 else (LEAF if k % 2 else LEAF_LIGHT)
        _big_leaf(f, (x, y), rng.uniform(55.0, 125.0), rng.uniform(24.0, 32.0), 7.6, colour)
    # The pods grow straight out of the trunk and the big branches.
    for x, y, ln, ang, colour in ((86.0, 176.0, 30.0, 100.0, POD_YELLOW), (100.0, 196.0, 28.0, 75.0, POD_RED), (84.0, 214.0, 26.0, 105.0, POD_ORANGE),
                                  (102.0, 152.0, 26.0, 70.0, POD_ORANGE), (70.0, 118.0, 24.0, 110.0, POD_YELLOW),
                                  (120.0, 106.0, 24.0, 76.0, POD_RED)):
        f.limb([(x, y - ln * 0.5), (x, y - ln * 0.36)], 2.0, BARK_DARK)
        _pod(f, x, y, ln, ang, colour)
    # Tiny pink flowers on the trunk.
    for x, y in ((90.0, 196.0), (97.0, 170.0), (88.0, 150.0), (99.0, 226.0)):
        f.ellipse(x, y, 1.6, 1.6, (240, 200, 210, 255))
    _grass(f, 62.0, 124.0, foot, "cacao:grass", 4.0, 9.0)
    return A.finish(f, width=1.3)


# ---------------------------------------------------------------------------
# The stepped temple pyramid.
# ---------------------------------------------------------------------------


def _draw_pyramid(anim: str, i: int, n: int):
    w, h = PYRAMID_FRAME
    f = K.Frame(PYRAMID_FRAME)
    foot = h - 6.0
    cx = w / 2.0
    tiers = 7
    top_y = 176.0
    base_half, top_half = 176.0, 60.0
    step_h = (foot - top_y) / tiers
    # The tiers, from the bottom: each a sloped wall with an inset band.
    for k in range(tiers):
        y1 = foot - k * step_h
        y0 = y1 - step_h
        hw1 = base_half - (base_half - top_half) * k / tiers
        hw0 = hw1 - 6.0
        f.poly([(cx - hw1, y1), (cx + hw1, y1), (cx + hw0, y0), (cx - hw0, y0)], LIMESTONE)
        f.poly([(cx + hw1 * 0.55, y1), (cx + hw1, y1), (cx + hw0, y0), (cx + hw0 * 0.55, y0)], LIMESTONE_SHADE, body=False)
        f.poly([(cx - hw1 + 3.0, y0 + step_h * 0.55), (cx + hw1 - 3.0, y0 + step_h * 0.55), (cx + hw1 - 2.0, y0 + step_h * 0.75),
                (cx - hw1 + 2.0, y0 + step_h * 0.75)], LIMESTONE_DARK, body=False)
        f.ink([(cx - hw0, y0 + 0.5), (cx + hw0, y0 + 0.5)], 1.2, LIMESTONE_LIGHT)
        # Traces of red paint on the plaster.
        if k % 2 == 0:
            f.poly([(cx - hw1 + 6.0, y0 + 3.0), (cx - hw1 + 26.0, y0 + 3.0), (cx - hw1 + 24.0, y0 + step_h * 0.5), (cx - hw1 + 7.0, y0 + step_h * 0.5)],
                   K.alpha(MAYA_RED, 0.55), body=False)
    # The stair up the front, with its side walls.
    sw1, sw0 = 40.0, 26.0
    f.poly([(cx - sw1, foot), (cx + sw1, foot), (cx + sw0, top_y), (cx - sw0, top_y)], LIMESTONE_LIGHT)
    y = foot - 4.0
    while y > top_y + 2.0:
        u = (foot - y) / (foot - top_y)
        hw = sw1 + (sw0 - sw1) * u - 6.0
        f.ink([(cx - hw, y), (cx + hw, y)], 1.0, LIMESTONE_SHADE)
        y -= 6.0
    for s in (-1.0, 1.0):
        f.poly([(cx + s * sw1, foot), (cx + s * (sw1 - 7.0), foot), (cx + s * (sw0 - 5.0), top_y), (cx + s * sw0, top_y)], LIMESTONE)
    # The platform on top and the temple: a room with a dark door, under a
    # sloped roof, and on the roof the comb, a tall wall of open lattice.
    f.poly(_rect(cx - 64.0, top_y - 8.0, cx + 64.0, top_y + 1.0), LIMESTONE)
    f.poly(_rect(cx - 50.0, top_y - 52.0, cx + 50.0, top_y - 8.0), LIMESTONE_LIGHT)
    f.poly(_rect(cx + 24.0, top_y - 52.0, cx + 50.0, top_y - 8.0), LIMESTONE_SHADE, body=False)
    f.poly([(cx - 12.0, top_y - 8.0), (cx - 12.0, top_y - 34.0), (cx, top_y - 40.0), (cx + 12.0, top_y - 34.0), (cx + 12.0, top_y - 8.0)], (52, 40, 36, 255),
           body=False)
    f.poly([(cx - 56.0, top_y - 52.0), (cx + 56.0, top_y - 52.0), (cx + 44.0, top_y - 74.0), (cx - 44.0, top_y - 74.0)], MAYA_RED)
    f.poly([(cx + 20.0, top_y - 52.0), (cx + 56.0, top_y - 52.0), (cx + 44.0, top_y - 74.0), (cx + 20.0, top_y - 74.0)], MAYA_RED_SHADE, body=False)
    for k in range(5):
        x = cx - 36.0 + k * 18.0
        f.ellipse(x, top_y - 63.0, 4.0, 4.0, LIMESTONE_LIGHT, body=False)
    comb_y0, comb_y1 = top_y - 74.0, 18.0
    f.poly([(cx - 34.0, comb_y0), (cx + 34.0, comb_y0), (cx + 26.0, comb_y1), (cx - 26.0, comb_y1)], LIMESTONE)
    f.poly([(cx + 12.0, comb_y0), (cx + 34.0, comb_y0), (cx + 26.0, comb_y1), (cx + 10.0, comb_y1)], LIMESTONE_SHADE, body=False)
    for r in range(4):
        yy = comb_y0 - 14.0 - r * 18.0
        for c in range(3):
            x = cx - 16.0 + c * 16.0
            f.poly(_rect(x - 4.0, yy - 5.0, x + 4.0, yy + 5.0), (64, 52, 46, 255), body=False)
    f.ink([(cx - 26.0, comb_y1 + 1.0), (cx + 26.0, comb_y1 + 1.0)], 1.4, MAYA_RED)
    # A little green in the joints of the old stone.
    rng = random.Random("history_maya_pyramid")
    for _ in range(14):
        k = rng.randrange(tiers)
        y0 = foot - (k + 1) * step_h
        hw = base_half - (base_half - top_half) * k / tiers - 10.0
        x = cx + rng.choice((-1.0, 1.0)) * rng.uniform(sw1 + 10.0, hw)
        f.ellipse(x, y0 + 1.0, rng.uniform(4.0, 9.0), rng.uniform(2.0, 3.6), LEAF if rng.random() < 0.5 else LEAF_LIGHT)
    return A.finish(f, width=1.6)


# ---------------------------------------------------------------------------
# A carved stela.
# ---------------------------------------------------------------------------


def _bar_dot(f: K.Frame, x: float, y: float, value: int, s: float, colour) -> None:
    """A Maya number: dots (ones) over bars (fives), from the bottom up."""
    bars, dots = divmod(value, 5)
    for k in range(bars):
        yy = y - k * 3.2 * s
        f.poly(_rect(x - 7.0 * s, yy - 1.0 * s, x + 7.0 * s, yy + 1.0 * s), colour, body=False)
    yd = y - bars * 3.2 * s - 0.6 * s
    if value == 0:
        # Zero: a shell.
        f.ellipse(x, y - 2.0 * s, 5.0 * s, 3.2 * s, LIMESTONE_LIGHT, body=False)
        f.ink([(x - 4.0 * s, y - 2.0 * s), (x + 4.0 * s, y - 2.0 * s)], 0.8, colour)
        f.ink([(x - 2.0 * s, y - 4.6 * s), (x - 2.0 * s, y + 0.6 * s)], 0.7, colour)
        f.ink([(x + 2.0 * s, y - 4.6 * s), (x + 2.0 * s, y + 0.6 * s)], 0.7, colour)
        return
    for k in range(dots):
        f.ellipse(x - (dots - 1) * 2.2 * s + k * 4.4 * s, yd, 1.4 * s, 1.4 * s, colour, body=False)


def _glyph(f: K.Frame, x: float, y: float, s: float, seed: int, colour) -> None:
    """A glyph block: a rounded square with inner shapes. Not a real sign."""
    rng = random.Random(seed)
    hw = 10.0 * s
    f.poly([(x - hw + 2.0, y - hw), (x + hw - 2.0, y - hw), (x + hw, y - hw + 2.0), (x + hw, y + hw - 2.0), (x + hw - 2.0, y + hw), (x - hw + 2.0, y + hw),
            (x - hw, y + hw - 2.0), (x - hw, y - hw + 2.0)], LIMESTONE_LIGHT, body=False)
    f.ink([(x - hw + 2.0, y - hw), (x + hw - 2.0, y - hw), (x + hw, y - hw + 2.0), (x + hw, y + hw - 2.0), (x + hw - 2.0, y + hw), (x - hw + 2.0, y + hw),
           (x - hw, y + hw - 2.0), (x - hw, y - hw + 2.0), (x - hw + 2.0, y - hw)], 1.0, colour)
    kind = rng.randrange(4)
    if kind == 0:
        f.ellipse(x - 3.0 * s, y, 4.0 * s, 6.0 * s, LIMESTONE, body=False)
        f.ink([(x - 3.0 * s, y - 6.0 * s), (x - 3.0 * s, y + 6.0 * s)], 0.8, colour)
        f.dot(x + 5.0 * s, y - 3.0 * s, 1.4 * s, colour)
        f.dot(x + 5.0 * s, y + 3.0 * s, 1.4 * s, colour)
    elif kind == 1:
        f.ink([(x - 6.0 * s, y - 5.0 * s), (x + 6.0 * s, y - 5.0 * s), (x + 6.0 * s, y + 5.0 * s), (x - 6.0 * s, y + 5.0 * s)], 0.9, colour)
        f.ink([(x - 2.0 * s, y - 2.0 * s), (x + 2.0 * s, y + 2.0 * s)], 0.9, colour)
        f.dot(x - 4.0 * s, y + 2.0 * s, 1.2 * s, colour)
    elif kind == 2:
        f.ink([(x - 6.0 * s, y + 4.0 * s), (x - 2.0 * s, y - 5.0 * s), (x + 3.0 * s, y + 1.0 * s), (x + 6.0 * s, y - 4.0 * s)], 0.9, colour)
        f.ellipse(x, y + 4.0 * s, 3.0 * s, 1.6 * s, LIMESTONE, body=False)
    else:
        f.ellipse(x, y, 6.0 * s, 6.0 * s, LIMESTONE, body=False)
        f.ellipse(x, y, 2.4 * s, 2.4 * s, colour, body=False)
        for a in range(0, 360, 90):
            f.dot(x + math.cos(math.radians(a + 45)) * 7.0 * s, y + math.sin(math.radians(a + 45)) * 7.0 * s, 1.0 * s, colour)


def _draw_stela(anim: str, i: int, n: int):
    w, h = STELA_FRAME
    f = K.Frame(STELA_FRAME)
    foot = h - 6.0
    slab = [(16.0, foot), (14.0, 40.0), (20.0, 20.0), (34.0, 10.0), (62.0, 10.0), (76.0, 20.0), (82.0, 40.0), (80.0, foot)]
    f.poly(slab, LIMESTONE)
    f.poly([(64.0, 12.0), (76.0, 20.0), (82.0, 40.0), (80.0, foot), (70.0, foot), (72.0, 40.0)], LIMESTONE_SHADE, body=False)
    f.poly([(20.0, 22.0), (34.0, 12.0), (48.0, 12.0), (26.0, 30.0), (20.0, 60.0)], LIMESTONE_LIGHT, body=False)
    # The carved panel: a frame, glyph blocks in two columns, and numbers.
    f.ink([(22.0, 30.0), (74.0, 30.0), (74.0, foot - 30.0), (22.0, foot - 30.0), (22.0, 30.0)], 1.2, LIMESTONE_DARK)
    rows = 8
    for r in range(rows):
        y = 44.0 + r * 27.0
        for c, x in enumerate((36.0, 60.0)):
            if (r, c) in ((1, 1), (4, 0), (6, 1)):
                f.poly(_rect(x - 10.0, y - 10.0, x + 10.0, y + 10.0), LIMESTONE_LIGHT, body=False)
                _bar_dot(f, x, y + 6.0, {(1, 1): 13, (4, 0): 9, (6, 1): 0}[(r, c)], 0.9, GLYPH)
            else:
                _glyph(f, x, y, 1.0, r * 7 + c * 3, GLYPH)
    # Old red paint in the cuts.
    f.ink([(23.0, 31.0), (73.0, 31.0)], 1.0, K.alpha(MAYA_RED, 0.6))
    # A low round altar stone at its foot.
    f.poly([(26.0, foot), (28.0, foot - 12.0), (68.0, foot - 12.0), (70.0, foot)], LIMESTONE)
    f.ellipse(48.0, foot - 12.0, 20.0, 3.6, LIMESTONE_LIGHT)
    _grass(f, 10.0, 86.0, foot, "stela:grass", 4.0, 9.0)
    return A.finish(f, width=1.4)


# ---------------------------------------------------------------------------
# The ballcourt ring.
# ---------------------------------------------------------------------------


def _draw_ring(anim: str, i: int, n: int):
    w, h = RING_FRAME
    f = K.Frame(RING_FRAME)
    foot = h - 6.0
    # The wall: a vertical upper face over a sloped bench.
    f.poly([(10.0, foot), (10.0, 16.0), (118.0, 16.0), (118.0, foot)], LIMESTONE)
    f.poly([(98.0, 16.0), (118.0, 16.0), (118.0, foot), (98.0, foot)], LIMESTONE_SHADE, body=False)
    _blocks(f, 11.0, 117.0, 18.0, 120.0, "ring:wall", LIMESTONE_SHADE)
    f.poly([(10.0, 120.0), (118.0, 120.0), (118.0, foot), (10.0, foot)], LIMESTONE_LIGHT)
    f.poly([(10.0, 120.0), (118.0, 120.0), (118.0, 128.0), (10.0, 128.0)], LIMESTONE_SHADE, body=False)
    for k in range(5):
        f.ink([(14.0, 136.0 + k * 10.0), (114.0, 136.0 + k * 10.0)], 0.8, LIMESTONE_SHADE)
    f.ink([(10.0, 17.0), (118.0, 17.0)], 1.4, LIMESTONE_LIGHT)
    f.poly([(10.0, 16.0), (118.0, 16.0), (118.0, 10.0), (10.0, 10.0)], MAYA_RED)
    # The ring: a stone disc with a round hole, its rim carved with a band.
    cx, cy = 64.0, 66.0
    f.ellipse(cx + 3.0, cy + 2.0, 30.0, 32.0, LIMESTONE_SHADE)
    f.ellipse(cx, cy, 30.0, 32.0, LIMESTONE_LIGHT)
    f.ellipse(cx, cy, 24.0, 26.0, LIMESTONE, body=False)
    for k in range(12):
        a = math.tau * k / 12.0
        f.ink([(cx + math.cos(a) * 18.0, cy + math.sin(a) * 19.5), (cx + math.cos(a) * 26.0, cy + math.sin(a) * 28.0)], 1.2, LIMESTONE_DARK)
    f.ellipse(cx, cy, 13.0, 14.0, (60, 48, 44, 255), body=False)
    f.ellipse(cx - 2.0, cy - 2.0, 11.0, 12.0, (40, 32, 30, 255), body=False)
    f.ink([(cx - 13.0, cy - 2.0), (cx - 6.0, cy - 12.0), (cx + 6.0, cy - 13.0)], 1.2, LIMESTONE_LIGHT)
    return A.finish(f, width=1.5)


# ---------------------------------------------------------------------------
# The ballcourt gate (a LockWall look).
# ---------------------------------------------------------------------------


def _draw_gate(anim: str, i: int, n: int):
    w, h = GATE_FRAME
    f = K.Frame(GATE_FRAME)
    foot = h - 4.0
    # The pier of masonry.
    f.poly([(8.0, foot), (10.0, 34.0), (86.0, 34.0), (88.0, foot)], LIMESTONE)
    f.poly([(70.0, 34.0), (86.0, 34.0), (88.0, foot), (72.0, foot)], LIMESTONE_SHADE, body=False)
    _blocks(f, 10.0, 86.0, 36.0, 104.0, "gate:top", LIMESTONE_SHADE, (14.0, 18.0), (20.0, 30.0))
    _blocks(f, 10.0, 86.0, 300.0, foot, "gate:foot", LIMESTONE_SHADE, (14.0, 18.0), (20.0, 30.0))
    # The cornice: a red band of stone that juts out at the top.
    f.poly([(4.0, 34.0), (92.0, 34.0), (90.0, 22.0), (6.0, 22.0)], LIMESTONE_LIGHT)
    f.poly([(6.0, 22.0), (90.0, 22.0), (88.0, 10.0), (8.0, 10.0)], MAYA_RED)
    for k in range(4):
        f.ellipse(18.0 + k * 20.0, 16.0, 4.0, 3.4, LIMESTONE_LIGHT, body=False)
    # The relief panel: a ballplayer in profile, a yoke at his waist, down on
    # one knee to hit the ball with his hip.
    px0, py0, px1, py1 = 14.0, 108.0, 82.0, 296.0
    f.poly(_rect(px0, py0, px1, py1), LIMESTONE_LIGHT)
    f.ink([(px0 + 3.0, py0 + 3.0), (px1 - 3.0, py0 + 3.0), (px1 - 3.0, py1 - 3.0), (px0 + 3.0, py1 - 3.0), (px0 + 3.0, py0 + 3.0)], 1.0, LIMESTONE_SHADE)
    rel = (188, 170, 140, 255)
    ink = (96, 82, 62, 255)
    # The headdress of feathers, the head and the body.
    for k in range(4):
        f.limb([(40.0, 150.0), (30.0 - k * 4.0, 124.0 + k * 3.0)], 3.0, rel, body=False)
    f.ellipse(44.0, 156.0, 8.0, 9.0, rel, body=False)
    f.ink([(51.0, 156.0), (53.0, 160.0), (49.0, 162.0)], 0.9, ink)
    f.dot(47.0, 154.0, 1.0, ink)
    f.limb([(42.0, 166.0), (38.0, 200.0)], 11.0, rel, body=False)
    # The yoke: a thick U of padding round the waist.
    f.poly([(28.0, 198.0), (52.0, 196.0), (54.0, 210.0), (30.0, 214.0)], (196, 176, 140, 255), body=False)
    f.ink([(28.0, 198.0), (52.0, 196.0), (54.0, 210.0), (30.0, 214.0), (28.0, 198.0)], 1.0, ink)
    # The arms: one out for balance, one down to the ground.
    f.limb([(44.0, 172.0), (62.0, 168.0), (72.0, 156.0)], 4.0, rel, body=False)
    f.limb([(36.0, 176.0), (26.0, 196.0), (22.0, 222.0)], 4.0, rel, body=False)
    # The legs: one knee down, one leg out behind; a knee pad.
    f.limb([(40.0, 212.0), (58.0, 232.0), (50.0, 258.0)], 6.0, rel, body=False)
    f.limb([(34.0, 212.0), (26.0, 240.0), (20.0, 264.0)], 6.0, rel, body=False)
    f.ellipse(58.0, 232.0, 4.4, 4.4, (196, 176, 140, 255), body=False)
    f.ink([(16.0, 266.0), (78.0, 266.0)], 1.2, ink)
    # The ball, in the air beside his hip, and the line of its flight.
    f.ellipse(66.0, 206.0, 8.0, 8.0, RUBBER, body=False)
    f.ellipse(64.0, 203.0, 2.6, 2.0, RUBBER_LIGHT, body=False)
    for k in range(3):
        f.ink([(56.0 - k * 4.0, 214.0 + k * 3.0), (60.0 - k * 4.0, 212.0 + k * 3.0)], 0.9, ink)
    # Outline of the figure, cut into the stone.
    f.ink([(36.0, 147.0), (44.0, 146.0), (52.0, 152.0), (53.0, 162.0), (46.0, 166.0)], 1.0, ink)
    # A band of glyph blocks under the scene.
    for k, x in enumerate((30.0, 54.0, 76.0)):
        if x < 76.0:
            _glyph(f, x + 4.0, 282.0, 0.9, 40 + k, GLYPH)
    _grass(f, 6.0, 90.0, foot, "gate:grass", 5.0, 10.0)
    return A.finish(f, width=1.6)


# ---------------------------------------------------------------------------
# The bohio: a round house of cane and thatch.
# ---------------------------------------------------------------------------


def _draw_bohio(anim: str, i: int, n: int):
    w, h = BOHIO_FRAME
    f = K.Frame(BOHIO_FRAME)
    foot = h - 6.0
    cx = w / 2.0
    # The wall: canes side by side, tied with a band of fibre.
    wall_top = 150.0
    f.poly(_rect(cx - 88.0, wall_top - 6.0, cx + 88.0, foot), CANE)
    x = cx - 86.0
    k = 0
    while x < cx + 86.0:
        f.ink([(x, wall_top), (x, foot - 1.0)], 1.0, CANE_SHADE if k % 2 else CANE_DARK)
        x += 6.0
        k += 1
    f.poly(_rect(cx + 50.0, wall_top - 6.0, cx + 88.0, foot), K.alpha(CANE_DARK, 0.35), body=False)
    for y in (wall_top + 26.0, wall_top + 62.0):
        f.poly(_rect(cx - 88.0, y, cx + 88.0, y + 3.0), CANE_DARK, body=False)
    # The door: a dark opening with a cotton curtain tied back.
    f.poly([(cx - 18.0, foot), (cx - 18.0, wall_top + 18.0), (cx - 12.0, wall_top + 10.0), (cx + 12.0, wall_top + 10.0), (cx + 18.0, wall_top + 18.0),
            (cx + 18.0, foot)], (52, 40, 32, 255))
    f.poly([(cx - 18.0, wall_top + 14.0), (cx - 6.0, wall_top + 14.0), (cx - 14.0, wall_top + 50.0), (cx - 18.0, foot - 4.0)], COTTON)
    f.ink([(cx - 16.0, wall_top + 50.0), (cx - 12.0, wall_top + 48.0)], 1.4, BIXA)
    # The roof: a tall cone of thatch, its eaves wide, a knot at the top.
    apex = (cx, 16.0)
    eave_l, eave_r = (cx - 118.0, wall_top + 6.0), (cx + 118.0, wall_top + 6.0)
    f.poly([apex, (cx + 6.0, 24.0), eave_r, (cx + 100.0, wall_top + 14.0), (cx - 100.0, wall_top + 14.0), eave_l, (cx - 6.0, 24.0)], THATCH)
    f.poly([apex, eave_r, (cx + 100.0, wall_top + 14.0), (cx + 40.0, wall_top + 12.0)], THATCH_SHADE, body=False)
    f.poly([apex, (cx - 30.0, wall_top + 8.0), (cx - 70.0, wall_top + 8.0)], THATCH_LIGHT, body=False)
    rng = random.Random("history_bohio")
    for k in range(5):
        y = 50.0 + k * 22.0
        u = (y - apex[1]) / (eave_l[1] - apex[1])
        hw = 118.0 * u
        pts = []
        for j in range(14):
            v = j / 13.0
            pts.append((cx - hw + 2.0 * hw * v, y + 3.0 * math.sin(math.pi * v) + rng.uniform(-0.8, 0.8)))
        f.ink(pts, 1.2, THATCH_SHADE)
    for _ in range(60):
        v = rng.uniform(0.15, 1.0)
        y = apex[1] + (eave_l[1] - apex[1]) * v
        x = cx + rng.uniform(-1.0, 1.0) * 116.0 * v
        f.ink([(x, y), (x + (x - cx) * 0.06, y + 8.0)], 0.8, THATCH_SHADE if rng.random() < 0.6 else THATCH_LIGHT)
    # The ragged hem of the eaves.
    for k in range(26):
        x = eave_l[0] + 6.0 + k * 9.0
        y = wall_top + 6.0 + 8.0 * (1.0 - abs(x - cx) / 118.0)
        f.poly([(x - 4.0, y - 2.0), (x, y + 6.0), (x + 4.0, y - 2.0)], THATCH)
    f.poly([(cx - 8.0, 30.0), (cx + 8.0, 30.0), (cx + 4.0, 10.0), (cx - 4.0, 10.0)], THATCH_SHADE)
    f.limb([(cx, 12.0), (cx, 6.0)], 3.0, WOOD)
    _grass(f, cx - 96.0, cx + 96.0, foot, "bohio:grass", 4.0, 9.0)
    return A.finish(f, width=1.5)


# ---------------------------------------------------------------------------
# The dugout canoe (a platform).
# ---------------------------------------------------------------------------


def _draw_canoe(anim: str, i: int, n: int):
    f = K.Frame(CANOE_FRAME)
    x0, x1 = CANOE_SPAN
    top = CANOE_TOP
    keel = 112.0
    # The hull: one tree, hollowed by fire and stone. Its sides are straight
    # along the middle; its bow and stern rise into blunt points.
    hull = [(x0 - 8.0, top - 8.0), (x0 + 10.0, top), (x1 - 10.0, top), (x1 + 8.0, top - 8.0), (x1 + 4.0, top + 6.0), (x1 - 14.0, keel - 14.0),
            (x1 - 40.0, keel), (x0 + 40.0, keel), (x0 + 14.0, keel - 14.0), (x0 - 4.0, top + 6.0)]
    f.poly(hull, WOOD)
    f.poly([(x0 + 14.0, keel - 14.0), (x1 - 14.0, keel - 14.0), (x1 - 40.0, keel), (x0 + 40.0, keel)], WOOD_SHADE, body=False)
    f.poly([(x0 + 12.0, top + 2.0), (x1 - 12.0, top + 2.0), (x1 - 14.0, top + 8.0), (x0 + 14.0, top + 8.0)], WOOD_LIGHT, body=False)
    # The grain of the log, and the marks of the adze.
    rng = random.Random("history_dugout_canoe")
    for k in range(4):
        y = top + 14.0 + k * 6.0
        f.ink([(x0 + 22.0 + k * 4.0, y), (x1 - 22.0 - k * 4.0, y + 0.6)], 0.8, WOOD_SHADE)
    for _ in range(22):
        x = rng.uniform(x0 + 30.0, x1 - 30.0)
        y = rng.uniform(top + 12.0, keel - 8.0)
        f.ink([(x, y), (x + 4.0, y - 1.6)], 0.8, K.shade(WOOD, 0.8))
    # A painted band of red bixa along the side, with white triangles.
    f.poly([(x0 + 14.0, top + 9.0), (x1 - 14.0, top + 9.0), (x1 - 16.0, top + 15.0), (x0 + 16.0, top + 15.0)], BIXA, body=False)
    for k in range(18):
        x = x0 + 24.0 + k * 18.0
        f.poly([(x - 4.0, top + 15.0), (x, top + 9.5), (x + 4.0, top + 15.0)], COTTON, body=False)
    # The paddlers' seats: thwarts across the hull, their ends in the sides.
    for k in range(9):
        x = x0 + 44.0 + k * (x1 - x0 - 88.0) / 8.0
        f.poly(_rect(x - 6.0, top - 0.5, x + 6.0, top + 4.0), WOOD_SHADE, body=False)
        f.ink([(x - 5.0, top + 1.0), (x + 5.0, top + 1.0)], 0.8, WOOD_LIGHT)
    # The blunt raised ends, carved with a simple spiral.
    for s, ex in ((-1.0, x0 - 2.0), (1.0, x1 + 2.0)):
        f.ellipse(ex - s * 8.0, top + 2.0, 4.0, 4.0, WOOD_LIGHT, body=False)
        f.ink([(ex - s * 8.0, top + 2.0), (ex - s * 10.0, top), (ex - s * 6.0, top - 1.0), (ex - s * 5.0, top + 4.0), (ex - s * 11.0, top + 5.0)], 0.8,
              WOOD_SHADE)
    return A.finish(f, width=1.5)


# ---------------------------------------------------------------------------
# The hammock.
# ---------------------------------------------------------------------------


def _draw_hammock(anim: str, i: int, n: int):
    w, h = HAMMOCK_FRAME
    f = K.Frame(HAMMOCK_FRAME)
    foot = h - 8.0
    # The two posts, forked at the top.
    for x in (20.0, 172.0):
        f.limb([(x, foot), (x, 18.0)], 7.0, WOOD)
        f.limb([(x, 22.0), (x - 5.0, 10.0)], 3.0, WOOD)
        f.limb([(x, 22.0), (x + 5.0, 10.0)], 3.0, WOOD)
        f.ink([(x - 1.6, foot - 2.0), (x - 1.6, 26.0)], 1.0, WOOD_LIGHT)
    # The ropes from the posts to the ends of the hammock, and the hammock:
    # a sling of woven cotton that sags, with coloured stripes.
    left, right = (34.0, 44.0), (158.0, 44.0)
    for (px, py), (ex, ey) in (((20.0, 26.0), left), ((172.0, 26.0), right)):
        for k in range(3):
            f.ink([(px, py), (ex, ey - 3.0 + k * 3.0)], 1.0, ROPE)
    top_edge, bottom_edge = [], []
    for k in range(17):
        u = k / 16.0
        x = left[0] + (right[0] - left[0]) * u
        sag = math.sin(math.pi * u)
        top_edge.append((x, left[1] + 36.0 * sag))
        bottom_edge.append((x, left[1] + 5.0 + 54.0 * sag))
    f.poly(top_edge + bottom_edge[::-1], COTTON)
    for stripe, colour in ((0.3, BIXA), (0.55, (58, 104, 150, 255)), (0.78, BIXA)):
        pts = [(a[0], a[1] + (b[1] - a[1]) * stripe) for a, b in zip(top_edge, bottom_edge)]
        f.ink(pts[1:-1], 1.6, colour)
    # The weave: short strands along the sling.
    for k in range(1, 16, 2):
        a, b = top_edge[k], bottom_edge[k]
        f.ink([a, b], 0.6, COTTON_SHADE)
    f.ink(top_edge, 1.0, COTTON_SHADE)
    return A.finish(f, width=1.3)


# ---------------------------------------------------------------------------
# The buren: a clay griddle with cassava bread.
# ---------------------------------------------------------------------------


def _draw_buren(anim: str, i: int, n: int):
    w, h = BUREN_FRAME
    f = K.Frame(BUREN_FRAME)
    foot = h - 5.0
    # The three stones, the embers between them.
    for x in (30.0, 98.0, 64.0):
        f.poly([(x - 12.0, foot), (x - 10.0, foot - 16.0), (x + 9.0, foot - 18.0), (x + 12.0, foot)], STONE if x != 64.0 else STONE_SHADE)
        f.ink([(x - 8.0, foot - 14.0), (x + 6.0, foot - 15.0)], 1.0, STONE_LIGHT)
    for x in (46.0, 56.0, 74.0, 82.0):
        f.ellipse(x, foot - 4.0, 5.0, 3.0, COAL)
        f.ellipse(x, foot - 5.0, 2.4, 1.4, EMBER, body=False)
    f.glow(64.0, foot - 6.0, 7.0, K.alpha(EMBER, 0.45))
    # The griddle: a wide flat disc of fired clay, seen from the side.
    f.ellipse(64.0, foot - 21.0, 56.0, 8.0, CLAY)
    f.ellipse(64.0, foot - 19.0, 56.0, 6.0, CLAY_SHADE, body=False)
    f.ellipse(64.0, foot - 23.0, 52.0, 5.4, CLAY_LIGHT, body=False)
    # The cassava bread: a big thin round, crisp at the edge.
    f.ellipse(62.0, foot - 25.0, 40.0, 5.0, CASSAVA)
    f.ellipse(62.0, foot - 24.0, 38.0, 3.0, CASSAVA_SHADE, body=False)
    rng = random.Random("history_buren")
    for _ in range(14):
        f.dot(rng.uniform(30.0, 94.0), foot - 25.0 + rng.uniform(-2.4, 1.0), 0.7, (196, 160, 100, 255))
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# The barbacoa: a frame of green sticks over embers.
# ---------------------------------------------------------------------------


def _draw_barbacoa(anim: str, i: int, n: int):
    w, h = BARBACOA_FRAME
    f = K.Frame(BARBACOA_FRAME)
    foot = h - 8.0
    t = _phase(i, n)
    grid_y = 66.0
    # The smoke goes up through the frame.
    for k in range(4):
        u = (t + k * 0.25) % 1.0
        x = 80.0 + (k - 1.5) * 18.0 + 6.0 * math.sin(math.tau * (u + k * 0.3))
        y = grid_y - 6.0 - u * 48.0
        f.ellipse(x, max(12.0, y), 7.0 + 6.0 * u, 5.0 + 4.0 * u, K.alpha(SMOKE, 0.55 * (1.0 - u)), body=False)
    # The far posts.
    for x in (30.0, 130.0):
        f.limb([(x + 6.0, foot - 4.0), (x + 6.0, grid_y - 4.0)], 3.6, STICK_SHADE)
    # The embers and the coals in a shallow pit.
    f.poly([(20.0, foot), (140.0, foot), (128.0, foot - 8.0), (32.0, foot - 8.0)], ASH)
    rng = random.Random("history_barbacoa")
    for k in range(9):
        x = 34.0 + k * 11.5 + rng.uniform(-2.0, 2.0)
        y = foot - 7.0 + rng.uniform(-1.0, 1.0)
        f.ellipse(x, y, 6.0, 3.6, COAL)
        glow = 0.6 + 0.4 * math.sin(math.tau * (t + k * 0.37))
        f.ellipse(x, y - 1.0, 3.6, 1.8, K.alpha(EMBER if glow < 0.85 else EMBER_HOT, glow), body=False)
    # The grid of green sticks, laid across two bars on forked posts.
    f.poly(_rect(16.0, grid_y - 2.0, 144.0, grid_y + 2.0), STICK)
    for k in range(13):
        x = 22.0 + k * 9.8
        f.limb([(x - 4.0, grid_y - 2.0), (x + 4.0, grid_y + 2.0)], 3.0, STICK if k % 2 else STICK_SHADE)
    # The fish on the grid, and a split of cassava.
    for x, flip in ((52.0, 1.0), (104.0, -1.0)):
        body = [(x - 22.0 * flip, grid_y - 4.0), (x - 8.0 * flip, grid_y - 12.0), (x + 12.0 * flip, grid_y - 10.0), (x + 20.0 * flip, grid_y - 4.0),
                (x + 12.0 * flip, grid_y - 1.0), (x - 8.0 * flip, grid_y - 1.0)]
        f.poly(body, FISH_BROWN if flip > 0 else FISH)
        f.poly([(x + 20.0 * flip, grid_y - 4.0), (x + 30.0 * flip, grid_y - 12.0), (x + 28.0 * flip, grid_y + 1.0)], FISH_SHADE)
        f.dot(x - 14.0 * flip, grid_y - 7.0, 1.2, K.INK)
        for k in range(3):
            f.ink([(x - 2.0 * flip + k * 7.0 * flip, grid_y - 10.0), (x - 4.0 * flip + k * 7.0 * flip, grid_y - 3.0)], 1.0, (90, 60, 40, 255))
    # The near posts, forked at the top.
    for x in (22.0, 138.0):
        f.limb([(x, foot - 2.0), (x, grid_y)], 4.4, STICK)
        f.limb([(x, grid_y + 2.0), (x - 4.0, grid_y - 8.0)], 2.4, STICK)
        f.limb([(x, grid_y + 2.0), (x + 4.0, grid_y - 8.0)], 2.4, STICK)
    return A.finish(f, width=1.3)


# ---------------------------------------------------------------------------
# The ceiba.
# ---------------------------------------------------------------------------


def _draw_ceiba(anim: str, i: int, n: int):
    w, h = CEIBA_FRAME
    f = K.Frame(CEIBA_FRAME)
    foot = h - 6.0
    cx = w / 2.0
    rng = random.Random("history_ceiba_tree")
    # The crown at the back: wide flat layers of leaves.
    for layer, (y, hw, colour) in enumerate(((44.0, 100.0, LEAF_SHADE), (78.0, 124.0, LEAF_SHADE), (112.0, 112.0, LEAF))):
        for k in range(16):
            x = cx - hw + 2.0 * hw * k / 15.0 + rng.uniform(-6.0, 6.0)
            yy = y + rng.uniform(-8.0, 8.0) + 10.0 * (abs(x - cx) / hw) ** 2
            f.ellipse(x, yy, rng.uniform(16.0, 24.0), rng.uniform(9.0, 13.0), colour)
    # The branches: straight out from the top of the trunk, level.
    for s in (-1.0, 1.0):
        f.limb([(cx, 140.0), (cx + s * 50.0, 112.0), (cx + s * 110.0, 98.0)], 12.0, CEIBA_BARK)
        f.limb([(cx, 128.0), (cx + s * 40.0, 80.0), (cx + s * 92.0, 62.0)], 9.0, CEIBA_BARK)
        f.limb([(cx + s * 50.0, 112.0), (cx + s * 80.0, 76.0)], 6.0, CEIBA_BARK)
    f.limb([(cx, 130.0), (cx + 4.0, 50.0)], 9.0, CEIBA_BARK)
    # The trunk: tall and straight, pale grey, wide at its foot where the
    # buttress roots spread out like walls.
    trunk = [(cx - 22.0, 140.0), (cx + 22.0, 140.0), (cx + 26.0, 260.0), (cx + 40.0, 320.0), (cx + 96.0, foot - 4.0), (cx + 120.0, foot),
             (cx - 120.0, foot), (cx - 92.0, foot - 4.0), (cx - 40.0, 316.0), (cx - 26.0, 260.0)]
    f.poly(trunk, CEIBA_BARK)
    f.poly([(cx + 6.0, 140.0), (cx + 22.0, 140.0), (cx + 26.0, 260.0), (cx + 40.0, 320.0), (cx + 96.0, foot - 4.0), (cx + 120.0, foot), (cx + 60.0, foot),
            (cx + 22.0, 320.0), (cx + 10.0, 260.0)], CEIBA_SHADE, body=False)
    f.ink([(cx - 14.0, 150.0), (cx - 16.0, 260.0)], 1.6, CEIBA_LIGHT)
    # The buttresses: thin walls of root, each lit on one face.
    for s, x2 in ((-1.0, 90.0), (-1.0, 50.0), (1.0, 64.0), (0.0, 0.0)):
        if s == 0.0:
            f.poly([(cx - 4.0, 290.0), (cx + 4.0, 290.0), (cx + 12.0, foot), (cx - 12.0, foot)], CEIBA_LIGHT, body=False)
            continue
        f.poly([(cx + s * 12.0, 280.0), (cx + s * 18.0, 286.0), (cx + s * x2, foot - 2.0), (cx + s * (x2 - 14.0), foot)], CEIBA_LIGHT, body=False)
        f.ink([(cx + s * 12.0, 280.0), (cx + s * (x2 - 14.0), foot)], 1.2, CEIBA_SHADE)
    # The short conical spines on the bark.
    for _ in range(18):
        x = cx + rng.uniform(-18.0, 18.0)
        y = rng.uniform(150.0, 300.0)
        f.poly([(x - 2.0, y), (x, y - 4.0), (x + 2.0, y)], CEIBA_SHADE, body=False)
    # The leaves in front: clumps of the hand-shaped leaves, and a few pale
    # pods of kapok fluff.
    for k in range(18):
        x = cx + rng.uniform(-120.0, 120.0)
        y = rng.uniform(30.0, 120.0) + 14.0 * (abs(x - cx) / 120.0) ** 2
        f.ellipse(x, y, rng.uniform(12.0, 18.0), rng.uniform(7.0, 10.0), LEAF_LIGHT if k % 3 else LEAF)
    for k in range(6):
        x = cx + rng.uniform(-110.0, 110.0)
        y = rng.uniform(60.0, 120.0)
        f.ellipse(x, y, 4.0, 2.6, COTTON)
    _grass(f, cx - 126.0, cx + 126.0, foot, "ceiba:grass", 4.0, 10.0)
    return A.finish(f, width=1.6)


# ---------------------------------------------------------------------------
# Publication.
# ---------------------------------------------------------------------------

SCENERY = ["prop", "scenery", "history", "americas"]
DOOR = ["prop", "door", "lock", "history", "americas"]

FRAMES: Dict[str, Tuple[int, int]] = {
    "history_colossal_head": HEAD_FRAME,
    "history_rubber_balls": BALLS_FRAME,
    "history_cacao_tree": CACAO_FRAME,
    "history_maya_pyramid": PYRAMID_FRAME,
    "history_maya_stela": STELA_FRAME,
    "history_ballcourt_ring": RING_FRAME,
    "history_ballcourt_gate": GATE_FRAME,
    "history_bohio": BOHIO_FRAME,
    "history_dugout_canoe": CANOE_FRAME,
    "history_hammock": HAMMOCK_FRAME,
    "history_buren": BUREN_FRAME,
    "history_barbacoa": BARBACOA_FRAME,
    "history_ceiba_tree": CEIBA_FRAME,
}
DRAW: Dict[str, Callable] = {
    "history_colossal_head": _draw_head,
    "history_rubber_balls": _draw_balls,
    "history_cacao_tree": _draw_cacao,
    "history_maya_pyramid": _draw_pyramid,
    "history_maya_stela": _draw_stela,
    "history_ballcourt_ring": _draw_ring,
    "history_ballcourt_gate": _draw_gate,
    "history_bohio": _draw_bohio,
    "history_dugout_canoe": _draw_canoe,
    "history_hammock": _draw_hammock,
    "history_buren": _draw_buren,
    "history_barbacoa": _draw_barbacoa,
    "history_ceiba_tree": _draw_ceiba,
}
DISPLAY = {
    "history_colossal_head": "Colossal Head",
    "history_rubber_balls": "Rubber Balls",
    "history_cacao_tree": "Cacao Tree",
    "history_maya_pyramid": "Maya Pyramid",
    "history_maya_stela": "Maya Stela",
    "history_ballcourt_ring": "Ballcourt Ring",
    "history_bohio": "Bohio",
    "history_hammock": "Hammock",
    "history_buren": "Buren",
    "history_barbacoa": "Barbacoa",
    "history_ceiba_tree": "Ceiba Tree",
}
ROWS = {"history_barbacoa": LOOP}


def _foot(name: str) -> Dict[str, Tuple[float, float]]:
    w, h = FRAMES[name]
    return {"foot": (w / 2.0, float(h))}


TARGETS: Dict[str, dict] = {
    name: _publisher(name, DISPLAY[name], ROWS.get(name, STILL), FRAMES[name], DRAW[name], _foot(name), "Scenery", SCENERY) for name in DISPLAY
}
TARGETS["history_ballcourt_gate"] = _publisher("history_ballcourt_gate", "Ballcourt Gate", STILL, GATE_FRAME, _draw_gate, {"foot": (48.0, 384.0)}, "Door",
                                               DOOR, forward=(0.0, -1.0))
TARGETS["history_dugout_canoe"] = _publisher("history_dugout_canoe", "Dugout Canoe", STILL, CANOE_FRAME, _draw_canoe,
                                             {"top": ((CANOE_SPAN[0] + CANOE_SPAN[1]) / 2.0, CANOE_TOP)}, "Scenery",
                                             ["prop", "platform", "history", "americas"])
