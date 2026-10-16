"""The set dressing of the rooms of Castle Godwin (Evil dimension).

Jon (2026-10-15): "the Nazi banners are fine for a room, but we need more
than that." Each room gets things of its own: a guard post, posters, a
searchlight, the barracks (a bunk bed, lockers, a mess table), the rally
hall (a podium), the lab (a tesla coil, a specimen vat, an operating table)
and the throne room (Wolfenstein's iron throne).

Every one is scenery (an LDtk `Prop`, no collision), drawn as
``castle_godwin`` draws: world units at `PX` pixels to the unit, the bottom
of the frame on the floor, the blue-grey stone, black iron and red of the
castle, and a dark line round each part, as the characters have. No drop
shadow is drawn.

The mark of the regime is the cog of ``_evil_faction``: an invented mark,
not a real symbol. Every word on a poster is invented.

The bunk bed lines up with the room's one-way platforms: the top of its
lower mattress is 112 units over the floor and the top of its upper one 224.

Animations: ``idle``, 1 frame; the tesla coil and the specimen vat have 6
(the arc crackles; the bubbles rise).
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Callable, Dict, List, Tuple

import numpy as np
from PIL import Image, ImageFilter

from ...authoring.sheet_build import build_sheet
from ..characters import _evil_faction as F
from . import castle_godwin as CG
from ._town_kit import Canvas, box, mix, scale

#: Pixels of the frame to one world unit.
PX = 2

INK = (22, 18, 26)
STONE = CG.STONE
STONE_LIGHT = CG.STONE_LIGHT
STONE_DARK = CG.STONE_DARK
IRON = (70, 72, 84)
IRON_DARK = (40, 40, 50)
IRON_LIGHT = (128, 132, 146)
RIVET = (170, 174, 184)
RED = CG.RED
RED_DARK = CG.RED_DARK
RED_LIGHT = (196, 44, 46)
WHITE = CG.WHITE
BLACK = CG.BLACK
PAPER = (222, 210, 176)
PAPER_DARK = (176, 160, 122)
WOOD = (96, 64, 44)
WOOD_DARK = (60, 40, 30)
WOOD_LIGHT = (140, 100, 70)
UNIFORM = (98, 110, 92)
UNIFORM_DARK = (66, 76, 64)
BLANKET = (112, 114, 118)
BLANKET_DARK = (78, 80, 86)
MATTRESS = (190, 182, 160)
LEATHER = (110, 70, 44)
LEATHER_DARK = (70, 44, 30)
BRASS = (196, 150, 70)
BRASS_DARK = (130, 94, 40)
BRASS_LIGHT = (240, 206, 130)
COPPER = (190, 104, 60)
COPPER_DARK = (120, 60, 36)
LAMP = (255, 236, 170)
GLOW = (255, 220, 130)
FLUID = (90, 220, 110)
FLUID_DARK = (30, 120, 60)
ARC = (220, 200, 255)
ARC_CORE = (255, 255, 255)
ROBOT = (244, 244, 246)
ROBOT_SHADE = (200, 202, 210)
VISOR = (22, 22, 30)
CYAN = (60, 230, 240)
PURPLE = (190, 70, 220)
STEEL = (180, 184, 192)


# ---------------------------------------------------------------------------
# Drawing in the castle's line
# ---------------------------------------------------------------------------


def grow(c: Canvas, m: np.ndarray, w: float) -> np.ndarray:
    """`m` grown by `w` world units all round: the dark line of a part."""
    n = max(1, int(round(w * c.k)))
    img = Image.fromarray(np.clip(m * 255, 0, 255).astype(np.uint8), "L").filter(ImageFilter.MaxFilter(2 * n + 1))
    return np.asarray(img, np.float32) / 255.0


def solid(c: Canvas, shape, colour, dark=None, y0: float = 0.0, y1: float = 0.0, w: float = 0.8) -> np.ndarray:
    """A part with a dark line round it: `shape` is a mask or a draw for
    one. With `dark`, the part goes from `colour` at `y0` to `dark` at
    `y1`. Returns its mask."""
    m = shape if isinstance(shape, np.ndarray) else c.mask(shape)
    if w > 0:
        c.put(grow(c, m, w), INK)
    if dark is None:
        c.put(m, colour)
    else:
        c.paint(m, c.ramp([(y0, colour), (y1, dark)]))
    return m


def edge(c: Canvas, m: np.ndarray, side: str, colour, width: float = 1.4, a: float = 0.6) -> None:
    """Light (or shade) the `side` edge of part `m`: 'top', 'bottom',
    'left' or 'right'."""
    n = max(1, int(round(width * c.k)))
    if side == "top":
        inner = np.roll(m, n, axis=0)
    elif side == "bottom":
        inner = np.roll(m, -n, axis=0)
    elif side == "left":
        inner = np.roll(m, n, axis=1)
    else:
        inner = np.roll(m, -n, axis=1)
    c.put(np.clip(m - inner, 0, 1), colour, a)


def rivets(c: Canvas, pts, r: float = 1.1) -> None:
    c.put(c.mask(lambda p: [p.ellipse(x, y, r + 0.5) for x, y in pts]), INK)
    c.put(c.mask(lambda p: [p.ellipse(x, y, r) for x, y in pts]), RIVET)
    c.put(c.mask(lambda p: [p.ellipse(x - r * 0.3, y - r * 0.3, r * 0.4) for x, y in pts]), WHITE, 0.8)


def mark(c: Canvas, cx: float, cy: float, r: float, ring: float = 0.0) -> None:
    """The mark of the regime: the black cog on a white disc (``ring``: a
    red ring round the disc this wide)."""
    if ring > 0:
        c.put(c.mask(lambda p: p.ellipse(cx, cy, r + ring + 0.7)), INK)
        c.put(c.mask(lambda p: p.ellipse(cx, cy, r + ring)), RED)
    c.put(c.mask(lambda p: p.ellipse(cx, cy, r + 0.6)), INK)
    c.put(c.mask(lambda p: p.ellipse(cx, cy, r)), WHITE)
    k = r * 0.8
    body = c.mask(lambda p: (p.poly(F.cog_points((cx, cy), k)), p.ellipse(cx, cy, k * F.COG_BODY)))
    hole = c.mask(lambda p: p.ellipse(cx, cy, k * F.COG_HOLE))
    c.put(body * (1.0 - hole), BLACK)


def words(c: Canvas, text: str, cx: float, top: float, h: float, ink=INK, light=None) -> None:
    CG.lettering(c, text, cx, top, h, ink, light)


def text_width(text: str, h: float) -> float:
    unit = h / 6.0
    return unit * 5.4 * len(text) - unit * 1.4


# ---------------------------------------------------------------------------
# 1. The guard post
# ---------------------------------------------------------------------------


def _guard_post(c: Canvas) -> None:
    w, h = 160, 112
    g = h
    top = g - 30
    # The sign on its post: PAPERS.
    solid(c, box(14, 30, 18, g), IRON, IRON_DARK, 30, g)
    board = solid(c, box(2, 10, 58, 34), PAPER, PAPER_DARK, 10, 34)
    c.put(board * c.mask(box(2, 10, 58, 13)), RED)
    words(c, "PAPERS", 30, 17, 10, ink=(30, 20, 20))
    rivets(c, [(5, 31), (55, 31)], 0.9)
    # The desk: a top, a front panel with the mark, legs.
    for x in (36, 144):
        solid(c, box(x, top + 4, x + 6, g), WOOD_DARK)
    front = solid(c, box(46, top + 4, 140, g - 6), WOOD, WOOD_DARK, top, g)
    edge(c, front, "top", WOOD_LIGHT, 1.2, 0.5)
    c.put(c.mask(box(80, top + 9, 106, g - 12)), INK)
    c.put(c.mask(box(81, top + 10, 105, g - 13)), RED)
    mark(c, 93, top + 19, 7)
    deck = solid(c, box(30, top, 152, top + 5), WOOD_LIGHT, WOOD, top, top + 5)
    edge(c, deck, "top", (190, 150, 110), 1.0, 0.7)
    # A stack of papers, a stamp on its pad.
    for k, (x0, x1) in enumerate(((84, 112), (85, 111), (83, 112), (86, 110))):
        y = top - 2.2 * (k + 1)
        solid(c, box(x0, y, x1, y + 2.2), PAPER if k % 2 else mix(PAPER, WHITE, 0.4), w=0.5)
    solid(c, box(60, top - 3, 76, top), (30, 30, 36), w=0.6)
    solid(c, box(62, top - 4, 74, top - 2), RED_DARK, w=0.5)
    solid(c, lambda p: (p.rect(66, top - 14, 70, top - 4), p.ellipse(68, top - 16, 4.5, 4)), WOOD_LIGHT, WOOD, top - 20, top - 4, w=0.6)
    # The lamp: a heavy base, an arm, a green shade, lit.
    solid(c, box(126, top - 4, 144, top), IRON, IRON_DARK, top - 4, top, w=0.6)
    solid(c, lambda p: p.line([(136, top - 3), (140, top - 30), (126, top - 40)], 2.2), IRON, w=0.6)
    shade = solid(c, lambda p: p.poly([(112, top - 34), (130, top - 44), (136, top - 36), (120, top - 26)]), (40, 92, 60), (20, 52, 34), top - 44, top - 26)
    edge(c, shade, "top", (100, 160, 110), 1.0, 0.6)
    bulb = c.mask(lambda p: p.poly([(116, top - 29), (122, top - 26), (124, top - 28), (118, top - 32)]))
    c.put(bulb, LAMP)
    c.light(c.mask(lambda p: p.ellipse(110, top - 6, 30, 10), blur=6.0) * (c.alpha > 0.5), GLOW, 0.35)


# ---------------------------------------------------------------------------
# 2. The wanted poster
# ---------------------------------------------------------------------------


def _paper(c: Canvas, x0, y0, x1, y1, colour=PAPER, dark=PAPER_DARK, torn: bool = True) -> np.ndarray:
    """A sheet pinned to the wall: a little crooked, a torn corner, nails."""
    pts = [(x0, y0), (x1, y0 + 1), (x1 - 0.6, y1), (x0 + 0.8, y1 - 0.6)]
    if torn:
        pts = [(x0, y0), (x1, y0 + 1), (x1 - 0.6, y1 - 6), (x1 - 4, y1 - 3), (x1 - 6, y1), (x0 + 0.8, y1 - 0.6)]
    m = solid(c, lambda p: p.poly(pts), colour, dark, y0, y1)
    stain = c.noise(("stain", x0, y0), 3, 4, 3)
    c.tone(m * np.clip(stain - 0.55, 0, 1), -0.5)
    rivets(c, [(x0 + 3, y0 + 3), (x1 - 3, y0 + 4)], 0.9)
    return m


def _robot_head(c: Canvas, cx: float, cy: float, r: float) -> None:
    """The player robot, drawn on a poster: a white round head with a black
    visor, two cyan eyes, and the purple antenna ball on its left."""
    # The antenna and its ball, on the left.
    solid(c, lambda p: p.line([(cx - r * 0.95, cy - r * 0.2), (cx - r * 1.05, cy - r * 1.35)], r * 0.12), ROBOT_SHADE, w=0.6)
    solid(c, lambda p: p.ellipse(cx - r * 1.05, cy - r * 1.5, r * 0.26), PURPLE, w=0.6)
    solid(c, lambda p: p.ellipse(cx - r * 0.98, cy + r * 0.05, r * 0.3, r * 0.42), PURPLE, w=0.6)
    head = solid(c, lambda p: p.ellipse(cx, cy, r, r * 0.88), ROBOT, ROBOT_SHADE, cy - r, cy + r)
    visor = solid(c, lambda p: p.ellipse(cx + r * 0.12, cy, r * 0.66, r * 0.5), VISOR, w=0.5)
    del head, visor
    for dx in (-0.12, 0.34):
        c.put(c.mask(lambda p: p.ellipse(cx + r * dx, cy, r * 0.1, r * 0.22)), CYAN)
    # Its shoulders, under the head.
    solid(c, lambda p: p.ellipse(cx, cy + r * 1.55, r * 0.9, r * 0.6), ROBOT, ROBOT_SHADE, cy + r, cy + r * 2.0, w=0.6)
    c.put(c.mask(lambda p: p.rect(cx - r * 0.12, cy + r * 1.3, cx + r * 0.16, cy + r * 1.58)), CYAN)


def _wanted_poster(c: Canvas) -> None:
    w, h = 48, 64
    _paper(c, 2, 2, w - 2, h - 2)
    words(c, "WANTED", w / 2, 6, 6, ink=(60, 16, 16))
    c.put(c.mask(box(7, 14, w - 7, 15)), (60, 16, 16))
    c.put(c.mask(box(9, 17, w - 9, 43)), PAPER_DARK, 0.5)
    _robot_head(c, w / 2 + 1, 27, 7.4)
    words(c, "REWARD", w / 2, 46, 4.2)
    words(c, "5000 GEARS", w / 2, 53, 4.2, ink=(60, 16, 16))


# ---------------------------------------------------------------------------
# 3. The posters of the regime
# ---------------------------------------------------------------------------


def _poster_frame(c: Canvas, colour, dark) -> np.ndarray:
    w, h = 48, 72
    return _paper(c, 2, 2, w - 2, h - 2, colour, dark, torn=False)


def _poster_a(c: Canvas) -> None:
    """OBEY THE GEAR: the mark, big, on red, rays behind it."""
    w, h = 48, 72
    m = _poster_frame(c, RED_LIGHT, RED_DARK)
    rays = c.mask(lambda p: [p.poly([(24, 28), (24 + 40 * math.cos(a - 0.1), 28 + 40 * math.sin(a - 0.1)), (24 + 40 * math.cos(a + 0.1), 28 + 40 * math.sin(a + 0.1))])
                             for a in [math.tau * k / 12 for k in range(12)]])
    c.put(rays * m * c.mask(box(4, 4, 44, 52)), RED_DARK, 0.6)
    mark(c, 24, 28, 15)
    c.put(m * c.mask(box(2, 50, 46, 70)), BLACK)
    words(c, "OBEY", w / 2, 53, 6, ink=WHITE)
    words(c, "THE GEAR", w / 2, 62, 4.6, ink=WHITE)
    del h


def _poster_b(c: Canvas) -> None:
    """ORDER IS FREEDOM: a raised fist on black, a red disc behind it."""
    w, h = 48, 72
    m = _poster_frame(c, (40, 38, 44), (20, 18, 24))
    c.put(m * c.mask(lambda p: p.ellipse(24, 26, 17)), RED)
    # The forearm, the fist, the cuff of a uniform.
    solid(c, lambda p: p.poly([(18, 50), (30, 50), (29, 32), (19, 32)]), UNIFORM, UNIFORM_DARK, 32, 50, w=0.7)
    solid(c, box(17.5, 30, 30.5, 34), RED, w=0.6)
    fist = solid(c, lambda p: (p.rect(15, 14, 33, 31), p.ellipse(24, 15, 9, 4)), (230, 196, 170), (190, 150, 124), 10, 31, w=0.8)
    for x in (19.5, 24, 28.5):
        c.put(c.mask(lambda p: p.line([(x, 12), (x, 20)], 0.7)) * fist, (150, 110, 94))
    solid(c, lambda p: p.poly([(15, 20), (12, 26), (16, 30), (20, 25)]), (220, 184, 158), w=0.6)
    c.put(m * c.mask(box(2, 52, 46, 70)), RED_DARK)
    words(c, "ORDER IS", w / 2, 54, 5.0, ink=WHITE)
    words(c, "FREEDOM", w / 2, 62, 5.0, ink=WHITE)
    del h


def _poster_c(c: Canvas) -> None:
    """PAPERS, PLEASE: three jackboots marching on cream, a red band."""
    w, h = 48, 72
    m = _poster_frame(c, PAPER, PAPER_DARK)
    c.put(m * c.mask(box(2, 8, 46, 14)), RED)
    for k, x in enumerate((5, 19, 33)):
        # A jackboot in step: the shaft, a round toe, a heel, the sole; the
        # middle one is up off the ground.
        lift = 4.0 if k == 1 else 0.0
        tilt = -8.0 if k == 1 else 0.0
        a = math.radians(tilt)

        def t(px, py, x=x, lift=lift, a=a):
            px, py = px * 0.78, py * 0.78
            return (x + px * math.cos(a) - py * math.sin(a), 41 - lift + px * math.sin(a) + py * math.cos(a))

        boot = solid(c, lambda p: (p.poly([t(0.6, -22), t(8.6, -22), t(7.6, -14), t(8.4, -6), t(13, -5), t(13.4, 0), t(0, 0), t(-0.6, -12)]), p.ellipse(*t(11.6, -2.6), 2.2, 2.2)),
                     (44, 42, 48), (16, 14, 20), 18, 42, w=0.6)
        edge(c, boot, "left", (130, 130, 146), 0.9, 0.7)
        c.put(c.mask(lambda p: p.line([t(0.4, -0.6), t(13.4, -0.6)], 1.2)), (12, 10, 14))
        c.put(c.mask(lambda p: p.poly([t(0, -3), t(3, -3), t(3, 0), t(0, 0)])), (12, 10, 14))
        c.put(c.mask(lambda p: p.poly([t(-0.6, -25), t(8.6, -25), t(8.4, -21), t(-0.4, -21)])), UNIFORM_DARK)
    c.put(m * c.mask(lambda p: [p.line([(x, 46.4), (x + 6, 46.4)], 0.8) for x in (6, 20, 34)]), PAPER_DARK)
    c.put(m * c.mask(box(4, 44, 44, 45.0)), INK)
    words(c, "PAPERS,", w / 2, 51, 5.4)
    words(c, "PLEASE", w / 2, 60, 5.4, ink=RED_DARK)
    del h


# ---------------------------------------------------------------------------
# 4. The searchlight
# ---------------------------------------------------------------------------


def _searchlight(c: Canvas) -> None:
    w, h = 64, 80
    g = h
    # The tripod.
    for foot in (8, 56, 34):
        solid(c, lambda p: p.line([(32, 44), (foot, g - 1.5)], 2.6), IRON, w=0.7)
    solid(c, box(29, 38, 35, 48), IRON_DARK, w=0.7)
    # The yoke, and the drum tilted up toward the right.
    solid(c, lambda p: p.line([(22, 40), (22, 28), (42, 28), (42, 40)], 2.6), IRON, w=0.7)
    a = math.radians(-24)
    ca, sa = math.cos(a), math.sin(a)

    def t(x, y):
        return (32 + x * ca - y * sa, 26 + x * sa + y * ca)

    drum = solid(c, lambda p: p.poly([t(-16, -11), t(12, -12), t(12, 12), t(-16, 11)]), IRON_LIGHT, IRON_DARK, 10, 40, w=0.8)
    edge(c, drum, "top", (190, 194, 206), 1.2, 0.6)
    for x in (-10, -4):
        c.put(c.mask(lambda p: p.line([t(x, -11), t(x, 11)], 0.8)) * drum, IRON_DARK)
    solid(c, lambda p: p.poly([t(-20, -7), t(-16, -9), t(-16, 9), t(-20, 7)]), IRON_DARK, w=0.7)
    # The lens: lit, a rim of brass.
    lens = solid(c, lambda p: p.poly([t(12, -13.4), t(16, -13), t(16, 13), t(12, 13.4)]), BRASS, BRASS_DARK, 10, 40, w=0.8)
    del lens
    face = c.mask(lambda p: p.poly([t(13, -11.4), t(15.4, -11), t(15.4, 11), t(13, 11.4)]))
    c.put(face, LAMP)
    c.light(c.mask(lambda p: p.ellipse(*t(14, 0), 9, 13), blur=3.0) * (c.alpha > 0.5), GLOW, 0.8)
    for k in range(3):
        c.put(c.mask(lambda p: p.line([t(17, -8 + 8 * k), t(26, -12 + 12 * k)], 1.2), blur=0.4), LAMP, 0.7)
    del w


# ---------------------------------------------------------------------------
# 5. The bunk bed
# ---------------------------------------------------------------------------

BUNK_W, BUNK_H = 224, 240
#: The tops of the two mattresses, over the floor: where the room's one-way
#: platforms are.
BUNK_LOWER_TOP, BUNK_UPPER_TOP = 112, 224


def _mattress(c: Canvas, x0: float, x1: float, top: float, tag) -> None:
    """A mattress on iron springs, its top at `top`, a grey blanket over it
    and a pillow at the left."""
    solid(c, box(x0, top + 12, x1, top + 16), IRON_DARK, w=0.8)
    c.put(c.mask(lambda p: [p.line([(x, top + 12), (x + 4, top + 16)], 0.8) for x in np.arange(x0 + 2, x1 - 4, 6)]), IRON_LIGHT, 0.5)
    solid(c, box(x0, top, x1, top + 12), MATTRESS, scale(MATTRESS, 0.8), top, top + 12, w=0.8)
    c.put(c.mask(lambda p: [p.line([(x, top + 3), (x, top + 9)], 0.5) for x in np.arange(x0 + 8, x1 - 4, 12)]), scale(MATTRESS, 0.7), 0.7)
    pillow = solid(c, lambda p: p.ellipse(x0 + 18, top - 1.2, 14, 4.6), WHITE, scale(WHITE, 0.82), top - 6, top + 3, w=0.7)
    del pillow
    rng = c.rand(tag)
    blanket = [(x0 + 34, top - 0.6), (x1 - 2, top - 0.6), (x1 + 1, top + 14), (x1 - 8, top + 24), (x1 - 20, top + 18), (x1 - 34, top + 22)]
    x = x1 - 46
    while x > x0 + 40:
        blanket.append((x, top + 12 + rng.uniform(-1.5, 2.5)))
        x -= rng.uniform(14, 22)
    blanket.append((x0 + 34, top + 10))
    m = solid(c, lambda p: p.poly(blanket), BLANKET, BLANKET_DARK, top, top + 24, w=0.8)
    for k in range(4):
        fx = x0 + 60 + k * 32
        c.put(m * c.mask(lambda p: p.line([(fx, top + 1), (fx + 4, top + 12)], 0.8)), BLANKET_DARK, 0.7)
    c.put(m * c.mask(box(x0 + 34, top - 0.6, x1, top + 1.4)), mix(BLANKET, WHITE, 0.3), 0.7)


def _bunk_bed(c: Canvas) -> None:
    w, h = BUNK_W, BUNK_H
    g = h
    lower, upper = g - BUNK_LOWER_TOP, g - BUNK_UPPER_TOP
    # The far posts first, then the bunks, then the near posts and rails.
    for x in (6, w - 14):
        solid(c, box(x, upper - 10, x + 8, g), IRON, IRON_DARK, upper, g)
    _mattress(c, 14, w - 14, lower, "lower")
    _mattress(c, 14, w - 14, upper, "upper")
    for y in (lower + 16, upper + 16):
        solid(c, box(6, y, w - 6, y + 4), IRON, w=0.8)
    for x in (6, w - 14):
        post = c.mask(box(x, upper - 10, x + 8, g))
        edge(c, post, "left", IRON_LIGHT, 1.6, 0.6)
        rivets(c, [(x + 4, upper + 18), (x + 4, lower + 18)], 1.2)
        solid(c, lambda p: p.ellipse(x + 4, upper - 11, 5.5, 3.2), IRON_LIGHT, IRON_DARK, upper - 14, upper - 8)
    # The head rails and the ladder at the right.
    for y in (upper - 4, lower - 4):
        solid(c, box(6, y, 14, y + 2), IRON, w=0.6)
    for x in (w - 40, w - 22):
        solid(c, box(x, upper + 20, x + 3, lower - 1), IRON_DARK, w=0.6)
    for y in np.arange(upper + 32, lower - 4, 20):
        solid(c, box(w - 40, y, w - 19, y + 3), IRON, w=0.6)
    # A footlocker under the lower bunk.
    lock = solid(c, box(70, g - 30, 150, g), (70, 82, 64), (46, 54, 42), g - 30, g, w=0.9)
    edge(c, lock, "top", (120, 134, 108), 1.4, 0.6)
    for x in (72, 146):
        solid(c, box(x - 1, g - 30, x + 3, g), IRON_DARK, w=0.5)
    solid(c, box(70, g - 22, 150, g - 19), IRON_DARK, w=0.5)
    solid(c, box(106, g - 24, 114, g - 15), BRASS, BRASS_DARK, g - 24, g - 15, w=0.6)
    c.put(c.mask(box(84, g - 14, 136, g - 6)), PAPER, 0.85)
    words(c, "1207", 110, g - 13.2, 6.0, ink=INK)
    del w


# ---------------------------------------------------------------------------
# 6. The lockers
# ---------------------------------------------------------------------------


def _locker_row(c: Canvas) -> None:
    w, h = 128, 96
    g = h
    for k, x in enumerate((4, 44, 84)):
        body = solid(c, box(x, 4, x + 40, g - 3), (88, 100, 92), (56, 64, 60), 4, g, w=0.9)
        edge(c, body, "top", (140, 152, 142), 1.2, 0.6)
        for lx in (x + 3, x + 33):
            solid(c, box(lx, g - 4, lx + 4, g), IRON_DARK, w=0.5)
        if k == 1:
            # Open: the dark inside, a uniform on a hook, a cap on the shelf.
            c.put(c.mask(box(x + 3, 7, x + 37, g - 6)), (24, 26, 30))
            c.put(c.mask(box(x + 3, 22, x + 37, 24)), IRON_DARK)
            solid(c, lambda p: p.ellipse(x + 20, 18, 9, 3.4), UNIFORM, UNIFORM_DARK, 14, 22, w=0.6)
            solid(c, box(x + 13, 18, x + 27, 20.4), BLACK, w=0.4)
            solid(c, lambda p: p.line([(x + 20, 26), (x + 20, 30)], 1.0), IRON_LIGHT, w=0.4)
            coat = solid(c, lambda p: p.poly([(x + 9, 32), (x + 31, 32), (x + 34, 52), (x + 32, 76), (x + 8, 76), (x + 6, 52)]), UNIFORM, UNIFORM_DARK, 30, 76, w=0.7)
            c.put(coat * c.mask(lambda p: p.line([(x + 20, 32), (x + 20, 76)], 0.8)), UNIFORM_DARK)
            for by in (40, 50, 60, 70):
                c.put(c.mask(lambda p: p.ellipse(x + 21.6, by, 0.9)), RIVET)
            solid(c, box(x + 6, 40, x + 11, 47), RED, w=0.5)
            c.put(c.mask(box(x + 6, 76, x + 34, 78)), UNIFORM_DARK)
            # The door, swung out, seen almost edge on.
            door = solid(c, lambda p: p.poly([(x + 37, 5), (x + 46, 3), (x + 46, g - 1), (x + 37, g - 6)]), (104, 116, 108), (64, 72, 68), 4, g, w=0.8)
            edge(c, door, "right", (150, 160, 152), 1.0, 0.5)
            continue
        c.put(body * c.mask(lambda p: p.line([(x + 3, 7), (x + 37, 7), (x + 37, g - 6), (x + 3, g - 6), (x + 3, 7)], 0.6)), INK, 0.8)
        c.put(c.mask(lambda p: [p.rect(x + 10, y, x + 30, y + 1.4) for y in (12, 16, 20)]), (36, 40, 40))
        c.put(c.mask(lambda p: [p.rect(x + 10, y, x + 30, y + 1.4) for y in (g - 20, g - 16)]), (36, 40, 40))
        solid(c, box(x + 31, 44, x + 34, 56), IRON_LIGHT, w=0.5)
        solid(c, box(x + 13, 28, x + 27, 36), PAPER, w=0.5)
        words(c, str(k + 1), x + 20, 29.4, 5.0)
    del w


# ---------------------------------------------------------------------------
# 7. The mess table
# ---------------------------------------------------------------------------


def _mess_table(c: Canvas) -> None:
    w, h = 160, 48
    g = h
    top = g - 30
    for x in (14, 140):
        solid(c, box(x, top + 4, x + 6, g), WOOD_DARK, w=0.8)
    deck = solid(c, box(6, top, 154, top + 5), WOOD_LIGHT, WOOD, top, top + 5, w=0.8)
    edge(c, deck, "top", (180, 140, 104), 1.0, 0.7)
    # Tin plates and mugs, a loaf.
    for x in (26, 62, 98, 134):
        solid(c, lambda p: p.ellipse(x, top - 0.8, 9, 2.2), STEEL, scale(STEEL, 0.75), top - 3, top + 1, w=0.6)
        c.put(c.mask(lambda p: p.ellipse(x, top - 1.2, 5.4, 1.1)), scale(STEEL, 0.82))
        mx = x + 13
        solid(c, box(mx - 3, top - 8, mx + 3, top), STEEL, scale(STEEL, 0.7), top - 8, top, w=0.6)
        solid(c, lambda p: p.ring(mx + 4.2, top - 4, 2.4, 1.1), STEEL, w=0.5)
    solid(c, lambda p: p.ellipse(80, top - 3.6, 8, 4), (196, 140, 80), (150, 96, 50), top - 8, top, w=0.6)
    # The bench in front.
    for x in (22, 132):
        solid(c, box(x, g - 14, x + 5, g), WOOD_DARK, w=0.7)
    bench = solid(c, box(12, g - 18, 148, g - 13), WOOD, WOOD_DARK, g - 18, g - 13, w=0.8)
    edge(c, bench, "top", WOOD_LIGHT, 1.0, 0.7)
    del w


# ---------------------------------------------------------------------------
# 8. The rally podium
# ---------------------------------------------------------------------------


def _microphone(c: Canvas, foot: Tuple[float, float], head: Tuple[float, float]) -> None:
    solid(c, lambda p: p.line([foot, head], 1.4), IRON_DARK, w=0.5)
    mic = solid(c, lambda p: p.ellipse(head[0], head[1] - 3, 3.4, 4.4), STEEL, IRON, head[1] - 7, head[1] + 1, w=0.6)
    c.put(mic * c.mask(lambda p: [p.line([(head[0] - 3, head[1] - 3 + d), (head[0] + 3, head[1] - 3 + d)], 0.5) for d in (-2, 0, 2)]), IRON_DARK, 0.8)
    solid(c, box(head[0] - 3.6, head[1] - 0.6, head[0] + 3.6, head[1] + 1.4), BRASS, w=0.4)


def _rally_podium(c: Canvas) -> None:
    w, h = 128, 96
    g = h
    # The stage: two steps of stone.
    for y0, x0, x1 in ((g - 8, 4, 124), (g - 16, 14, 114)):
        m = solid(c, box(x0, y0, x1, y0 + 8), STONE, STONE_DARK, y0, y0 + 8, w=0.8)
        edge(c, m, "top", STONE_LIGHT, 1.2, 0.7)
    # The microphones, behind the lectern.
    for foot, head in (((52, 40), (40, 18)), ((64, 40), (64, 12)), ((76, 40), (88, 18))):
        _microphone(c, foot, head)
    # The lectern: a slanted top, a front of red cloth with the mark.
    front = solid(c, lambda p: p.poly([(36, 40), (92, 40), (88, g - 16), (40, g - 16)]), RED_LIGHT, RED_DARK, 40, g - 16, w=0.9)
    folds = 0.5 + 0.5 * np.sin((c.x - 64) / 56 * math.pi * 4.0)
    c.tone(front * folds * c.mask(box(36, 56, 92, g - 16)), -0.18)
    c.put(front * c.mask(box(36, g - 22, 92, g - 18)), BRASS, 0.9)
    mark(c, 64, 56, 11)
    top = solid(c, lambda p: p.poly([(32, 34), (96, 34), (94, 41), (34, 41)]), WOOD_LIGHT, WOOD, 34, 41, w=0.8)
    edge(c, top, "top", (190, 150, 110), 1.0, 0.7)
    del w


# ---------------------------------------------------------------------------
# 9. The tesla coil
# ---------------------------------------------------------------------------


def _tesla_coil(c: Canvas, frame: int = 0) -> None:
    w, h = 64, 176
    g = h
    # The base, and the stack of insulators.
    base = solid(c, box(10, g - 14, 54, g), IRON, IRON_DARK, g - 14, g, w=0.9)
    edge(c, base, "top", IRON_LIGHT, 1.2, 0.7)
    rivets(c, [(14, g - 6), (50, g - 6)], 1.0)
    for k in range(4):
        y = g - 16 - k * 7
        solid(c, lambda p: (p.ellipse(32, y - 3, 12 - k * 0.6, 3.6), p.rect(26, y - 3, 38, y + 1)), (226, 220, 206), (168, 160, 146), y - 7, y + 1, w=0.6)
    # The coil: copper wound round a tube.
    tube = solid(c, box(24, 52, 40, g - 42), (60, 44, 34), w=0.8)
    c.put(tube * c.mask(lambda p: [p.rect(24, y, 40, y + 1.6) for y in np.arange(54, g - 44, 2.6)]), COPPER)
    c.put(tube * c.mask(box(24, 52, 28, g - 42)), COPPER_DARK, 0.5)
    c.put(tube * c.mask(box(33, 52, 35, g - 42)), (240, 170, 120), 0.5)
    # The sphere at the top.
    sphere = solid(c, lambda p: p.ellipse(32, 36, 17, 16), STEEL, IRON, 20, 52, w=0.9)
    c.put(sphere * c.mask(lambda p: p.ellipse(26, 30, 6, 4.6), blur=1.2), WHITE, 0.8)
    solid(c, box(29, 50, 35, 54), IRON_DARK, w=0.5)
    # The arc: a crackle off the sphere, a new one each frame.
    rng = c.rand("arc", frame)
    arcs = []
    for _ in range(2 if frame % 3 else 3):
        a = rng.uniform(-2.9, -0.25)
        x, y = 32 + 16 * math.cos(a), 36 + 15 * math.sin(a)
        pts = [(x, y)]
        for _k in range(rng.randint(4, 6)):
            a += rng.uniform(-0.6, 0.6)
            step = rng.uniform(3.5, 6.0)
            x = min(max(x + step * math.cos(a), 6.0), w - 6.0)
            y = min(max(y + step * math.sin(a), 6.0), 60.0)
            pts.append((x, y))
        arcs.append(pts)
    c.put(c.mask(lambda p: [p.line(pts, 3.2) for pts in arcs], blur=1.0), ARC, 0.6)
    c.put(c.mask(lambda p: [p.line(pts, 1.2) for pts in arcs]), ARC_CORE)
    c.light(sphere * c.mask(lambda p: [p.ellipse(*pts[0], 6) for pts in arcs], blur=2.0), ARC, 0.6)


# ---------------------------------------------------------------------------
# 10. The specimen vat
# ---------------------------------------------------------------------------

#: The inside of the vat's glass, in world units.
VAT_GLASS = (14, 22, 66, 116)


def _vat_back(c: Canvas, frame: int) -> None:
    del frame
    w, h = 80, 144
    g = h
    x0, y0, x1, y1 = VAT_GLASS
    base = solid(c, box(6, y1, 74, g), BRASS, BRASS_DARK, y1, g, w=0.9)
    edge(c, base, "top", BRASS_LIGHT, 1.4, 0.7)
    rivets(c, [(12, g - 8), (40, g - 8), (68, g - 8)], 1.1)
    solid(c, box(30, y1 + 8, 50, y1 + 18), IRON_DARK, w=0.6)
    for k, colour in enumerate(((240, 70, 60), (90, 230, 110), (240, 200, 70))):
        c.put(c.mask(lambda p: p.ellipse(34 + k * 6, y1 + 13, 1.6)), colour)
    glass = solid(c, box(x0 - 2, y0, x1 + 2, y1), FLUID, FLUID_DARK, y0, y1, w=0.9)
    c.light(glass * c.mask(lambda p: p.ellipse(40, (y0 + y1) / 2, 22, 40), blur=8.0), (180, 255, 170), 0.5)
    del w


def _vat_front(c: Canvas, frame: int) -> None:
    w, h = 80, 144
    x0, y0, x1, y1 = VAT_GLASS
    # Bubbles, rising: each frame a sixth of the way on.
    rng = c.rand("bubbles")
    bubbles = []
    for _ in range(9):
        bx, speed, r = rng.uniform(x0 + 4, x1 - 4), rng.uniform(10, 18), rng.uniform(0.9, 2.2)
        y = y1 - 4 - ((rng.uniform(0, 90) + speed * frame) % (y1 - y0 - 8))
        bubbles.append((bx + 1.2 * math.sin(frame + bx), y, r))
    c.put(c.mask(lambda p: [p.ring(x, y, r, 0.6) for x, y, r in bubbles]), (220, 255, 220), 0.9)
    c.put(c.mask(lambda p: [p.ellipse(x - r * 0.3, y - r * 0.3, r * 0.3) for x, y, r in bubbles]), WHITE, 0.9)
    # The light on the glass, and its line.
    c.put(c.mask(box(x0 + 3, y0 + 4, x0 + 6, y1 - 6), blur=0.6), WHITE, 0.45)
    c.put(c.mask(box(x1 - 6, y0 + 4, x1 - 4.6, y1 - 6), blur=0.4), WHITE, 0.3)
    # The cap, its pipes.
    cap = solid(c, box(8, y0 - 14, 72, y0 + 2), BRASS, BRASS_DARK, y0 - 14, y0 + 2, w=0.9)
    edge(c, cap, "top", BRASS_LIGHT, 1.2, 0.7)
    rivets(c, [(14, y0 - 6), (40, y0 - 6), (66, y0 - 6)], 1.0)
    solid(c, lambda p: p.line([(26, y0 - 14), (26, y0 - 18), (8, y0 - 18)], 3.0), COPPER, w=0.6)
    solid(c, lambda p: p.line([(56, y0 - 14), (56, 5), (72, 5)], 3.0), COPPER, w=0.6)
    solid(c, box(3, y0 - 20, 9, y0 - 16), COPPER_DARK, w=0.5)
    del w, h


def _prototype_in_the_vat() -> Image.Image:
    """The Failed Prototype as he floats: a frame of his own sheet, sunk in
    green, at the vat's frame scale."""
    from ..characters import evil_failed_prototype as fp

    img = fp._render_frame("fall", 2, 6)
    a = img.getchannel("A")
    img = img.crop(a.getbbox())
    # His sheet is about 0.75 px to the cm; the vat is PX px to a world unit
    # (2.58 cm): he is 130 cm, about 50 units, and the vat is 52 wide.
    k = (46.0 * PX) / img.size[1]
    img = img.resize((max(1, round(img.size[0] * k)), max(1, round(img.size[1] * k))), Image.Resampling.LANCZOS)
    rgb = np.asarray(img, np.float32)
    green = np.array([40, 150, 70], np.float32)
    rgb[:, :, :3] = rgb[:, :, :3] * 0.35 + green * 0.65 * (0.5 + 0.5 * rgb[:, :, :3].mean(axis=2, keepdims=True) / 255.0)
    rgb[:, :, 3] *= 0.8
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGBA")


def _specimen_vat_frame(name: str, frame: int) -> Image.Image:
    w, h = PROPS[name][0], PROPS[name][1]
    back = Canvas(name, w, h, origin=(0.0, 0.0), ppu=PX)
    _vat_back(back, frame)
    out = back.image()
    body = _prototype_in_the_vat().rotate(-8.0 + 4.0 * math.sin(frame * math.tau / 6.0), resample=Image.Resampling.BICUBIC, expand=True)
    x0, y0, x1, y1 = VAT_GLASS
    bob = 2.0 * math.sin(frame * math.tau / 6.0)
    at = (int(round(((x0 + x1) / 2.0) * PX - body.size[0] / 2.0)), int(round(((y0 + y1) / 2.0 + 2.0 + bob) * PX - body.size[1] / 2.0)))
    out.alpha_composite(body, at)
    front = Canvas(name + " front", w, h, origin=(0.0, 0.0), ppu=PX)
    _vat_front(front, frame)
    out.alpha_composite(front.image())
    return out


# ---------------------------------------------------------------------------
# 11. The operating table
# ---------------------------------------------------------------------------


def _operating_table(c: Canvas) -> None:
    w, h = 176, 72
    g = h
    # The lamp: a stand at the left, an arm over the table, a dome.
    solid(c, box(4, g - 4, 20, g), IRON_DARK, w=0.7)
    solid(c, box(10, 8, 14, g - 4), IRON, IRON_DARK, 8, g, w=0.7)
    solid(c, lambda p: p.line([(12, 9), (84, 9)], 2.6), IRON, w=0.7)
    solid(c, lambda p: p.line([(84, 9), (88, 14)], 2.0), IRON, w=0.6)
    dome = solid(c, lambda p: p.poly([(76, 22), (100, 22), (96, 13), (80, 13)]), IRON_LIGHT, IRON_DARK, 12, 22, w=0.8)
    del dome
    c.put(c.mask(lambda p: p.ellipse(88, 22.4, 10, 1.6)), LAMP)
    c.light(c.mask(lambda p: p.ellipse(88, 30, 30, 12), blur=6.0) * (c.alpha > 0.5), GLOW, 0.3)
    # The cables: off the right end, down to the floor.
    solid(c, lambda p: p.line([(150, 40), (160, 50), (164, 62), (170, 70)], 1.8), (30, 30, 34), w=0.5)
    solid(c, lambda p: p.line([(146, 42), (150, 60), (158, 68), (166, 70)], 1.6), RED_DARK, w=0.5)
    # The table: an iron pedestal, a top, a sheet, straps.
    solid(c, lambda p: p.poly([(76, 46), (100, 46), (104, g - 4), (72, g - 4)]), IRON, IRON_DARK, 46, g, w=0.8)
    solid(c, box(60, g - 5, 116, g), IRON_DARK, w=0.7)
    deck = solid(c, box(22, 38, 154, 46), IRON_LIGHT, IRON_DARK, 38, 46, w=0.9)
    rivets(c, [(28, 42), (148, 42), (88, 42)], 1.0)
    sheet = solid(c, lambda p: p.poly([(26, 35), (150, 35), (152, 44), (146, 54), (134, 48), (120, 56), (104, 47), (60, 50), (44, 46), (28, 54), (24, 44)]),
                  WHITE, (180, 180, 176), 35, 56, w=0.7)
    c.put(sheet * c.mask(lambda p: [p.line([(x, 37), (x + 3, 50)], 0.7) for x in (48, 84, 116, 140)]), (170, 170, 168), 0.7)
    c.put(sheet * c.mask(box(60, 40, 76, 50), blur=1.0), (160, 40, 40), 0.25)
    for x in (44, 92, 132):
        strap = solid(c, box(x, 33, x + 7, 47), LEATHER, LEATHER_DARK, 33, 47, w=0.6)
        del strap
        solid(c, box(x + 1, 38, x + 6, 41), BRASS, w=0.4)
    del deck, w


# ---------------------------------------------------------------------------
# 12. The iron throne
# ---------------------------------------------------------------------------


def _claw_marks(c: Canvas, x: float, y: float, length: float) -> None:
    c.put(c.mask(lambda p: [p.line([(x + k * 3.0, y), (x + k * 3.0 + length * 0.35, y + length)], 1.0) for k in range(3)]), (18, 16, 22))
    c.put(c.mask(lambda p: [p.line([(x + k * 3.0 + 0.8, y), (x + k * 3.0 + 0.8 + length * 0.35, y + length)], 0.5) for k in range(3)]), IRON_LIGHT, 0.8)


def _chain(c: Canvas, pts) -> None:
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        steps = max(2, int(math.dist((ax, ay), (bx, by)) / 4.0))
        links = [(ax + (bx - ax) * k / steps, ay + (by - ay) * k / steps) for k in range(steps)]
        c.put(c.mask(lambda p: [p.ring(x, y, 2.2 if k % 2 else 1.6, 1.2) for k, (x, y) in enumerate(links)]), INK)
        c.put(c.mask(lambda p: [p.ring(x, y, 2.2 if k % 2 else 1.6, 0.6) for k, (x, y) in enumerate(links)]), IRON_LIGHT)


def _iron_throne(c: Canvas) -> None:
    w, h = 160, 192
    g = h
    # The back: a tall riveted plate with spikes, the mark on it.
    for k, x in enumerate((36, 52, 68, 80, 92, 108, 124)):
        tall = 13 if k == 3 else 10 if k in (2, 4) else 7
        solid(c, lambda p: p.poly([(x - 5, 16), (x, 16 - tall), (x + 5, 16)]), IRON, IRON_DARK, 16 - tall, 16, w=0.7)
    back = solid(c, lambda p: p.poly([(28, 16), (132, 16), (128, 120), (32, 120)]), IRON, IRON_DARK, 16, 120, w=1.0)
    edge(c, back, "left", IRON_LIGHT, 1.8, 0.5)
    c.put(back * c.mask(lambda p: [p.line([(30, y), (130, y)], 0.8) for y in (40, 68, 96)]), IRON_DARK, 0.9)
    rivets(c, [(x, y) for y in (21, 44, 72, 100) for x in (36, 124)] + [(x, 21) for x in (60, 80, 100)], 1.3)
    mark(c, 80, 56, 20, ring=4)
    # The seat, a red cushion.
    solid(c, box(20, 118, 140, 130), IRON, IRON_DARK, 118, 130, w=1.0)
    cushion = solid(c, lambda p: p.poly([(34, 108), (126, 108), (130, 120), (30, 120)]), RED_LIGHT, RED_DARK, 108, 120, w=0.8)
    edge(c, cushion, "top", (226, 96, 90), 1.0, 0.6)
    # The arms, with the marks of claws, and chains off them.
    for x0, x1 in ((10, 40), (120, 150)):
        arm = solid(c, box(x0, 88, x1, 128), IRON, IRON_DARK, 88, 128, w=1.0)
        edge(c, arm, "top", IRON_LIGHT, 1.6, 0.7)
        solid(c, lambda p: p.ellipse((x0 + x1) / 2, 88, (x1 - x0) / 2 + 2, 5), IRON_LIGHT, IRON, 83, 93, w=0.8)
        rivets(c, [(x0 + 5, 100), (x1 - 5, 100), (x0 + 5, 120), (x1 - 5, 120)], 1.1)
        _claw_marks(c, x0 + 8, 95, 16)
    _chain(c, [(14, 112), (8, 140), (16, 166)])
    _chain(c, [(146, 112), (152, 146), (144, 170)])
    # The block under it, and its step.
    block = solid(c, box(18, 130, 142, g - 12), IRON_DARK, (24, 24, 30), 130, g, w=1.0)
    c.put(block * c.mask(lambda p: [p.line([(18, y), (142, y)], 0.8) for y in (150, 168)]), INK, 0.7)
    rivets(c, [(x, y) for x in (26, 80, 134) for y in (140, 160)], 1.2)
    step = solid(c, box(6, g - 12, 154, g), STONE, STONE_DARK, g - 12, g, w=0.9)
    edge(c, step, "top", STONE_LIGHT, 1.4, 0.7)
    del w


# ---------------------------------------------------------------------------
# The targets
# ---------------------------------------------------------------------------

#: name: (width, height, draw, frames, ms, tags). `draw(c, frame)` paints a
#: frame on a canvas, or `None` for a prop that makes its own frames.
PROPS: Dict[str, Tuple[float, float, Callable, int, int, List[str]]] = {
    "castle_guard_post": (160, 112, lambda c, f: _guard_post(c), 1, 400, ["prop", "scenery", "castle", "furniture"]),
    "castle_wanted_poster": (48, 64, lambda c, f: _wanted_poster(c), 1, 400, ["prop", "scenery", "castle", "poster"]),
    "castle_propaganda_poster_a": (48, 72, lambda c, f: _poster_a(c), 1, 400, ["prop", "scenery", "castle", "poster"]),
    "castle_propaganda_poster_b": (48, 72, lambda c, f: _poster_b(c), 1, 400, ["prop", "scenery", "castle", "poster"]),
    "castle_propaganda_poster_c": (48, 72, lambda c, f: _poster_c(c), 1, 400, ["prop", "scenery", "castle", "poster"]),
    "castle_searchlight": (64, 80, lambda c, f: _searchlight(c), 1, 400, ["prop", "scenery", "castle", "light"]),
    "castle_bunk_bed": (BUNK_W, BUNK_H, lambda c, f: _bunk_bed(c), 1, 400, ["prop", "scenery", "castle", "furniture", "barracks"]),
    "castle_locker_row": (128, 96, lambda c, f: _locker_row(c), 1, 400, ["prop", "scenery", "castle", "furniture", "barracks"]),
    "castle_mess_table": (160, 48, lambda c, f: _mess_table(c), 1, 400, ["prop", "scenery", "castle", "furniture", "barracks"]),
    "castle_rally_podium": (128, 96, lambda c, f: _rally_podium(c), 1, 400, ["prop", "scenery", "castle", "furniture"]),
    "castle_tesla_coil": (64, 176, _tesla_coil, 6, 70, ["prop", "scenery", "castle", "lab", "animated"]),
    "castle_specimen_vat": (80, 144, None, 6, 140, ["prop", "scenery", "castle", "lab", "animated"]),
    "castle_operating_table": (176, 72, lambda c, f: _operating_table(c), 1, 400, ["prop", "scenery", "castle", "lab", "furniture"]),
    "castle_iron_throne": (160, 192, lambda c, f: _iron_throne(c), 1, 400, ["prop", "scenery", "castle", "throne_room", "furniture"]),
}


def _frame_size(name: str) -> Tuple[int, int]:
    w, h = PROPS[name][0], PROPS[name][1]
    return (int(w * PX), int(h * PX))


def draw(name: str, frame: int = 0) -> Image.Image:
    """One frame of the prop `name`."""
    w, h, paint = PROPS[name][0], PROPS[name][1], PROPS[name][2]
    if paint is None:
        return _specimen_vat_frame(name, frame)
    c = Canvas(name, w, h, origin=(0.0, 0.0), ppu=PX)
    paint(c, frame)
    return c.image()


def _renderer(name: str):
    frames, ms = PROPS[name][3], PROPS[name][4]

    def render_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
        del nframes
        if anim != "idle":
            raise ValueError(f"unknown animation: {anim}")
        return draw(name, frame_idx)

    def frame_meta(anim: str, frame_idx: int, nframes: int) -> dict:
        del anim, frame_idx, nframes
        fw, fh = _frame_size(name)
        return {"anchors": {"foot": {"x": fw / 2, "y": float(fh)}}, "forward": {"x": 0.0, "y": -1.0}, "angle_deg": 0.0}

    def render(out_dir: str | Path, **opts) -> List[Path]:
        del opts
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        outputs = build_sheet(
            target=name,
            rows=[("idle", frames, ms)],
            render_fn=render_frame,
            out_dir=out_dir,
            frame_size=_frame_size(name),
            frame_meta_fn=frame_meta,
            auto_crop=False,
            actor_metadata=_actor(name),
        )
        return [outputs[key] for key in ("canonical", "canonical_transparent", "spritesheet", "yaml", "ron", "actor", "preview")]

    return render


def _actor(name: str) -> dict:
    tags = PROPS[name][5]
    return {
        "actor": {"character_id": f"prop_{name}", "display_name": name.replace("_", " ").title()},
        "body": {"body_plan": "Prop", "body_kind": "Scenery", "mass_class": "Heavy", "locomotion_hint": "Static", "traits": tags},
        "brain": {"default_preset": "stand_still"},
        "actions": {"default_preset": "peaceful"},
        "animation_bindings": {"default": {"animation": "idle", "events": []}},
        "tags": tags,
    }


TARGETS = {name: {"render": _renderer(name), "actor_metadata": _actor(name)} for name in PROPS}

__all__ = ["PROPS", "PX", "BUNK_LOWER_TOP", "BUNK_UPPER_TOP", "TARGETS", "draw"]
