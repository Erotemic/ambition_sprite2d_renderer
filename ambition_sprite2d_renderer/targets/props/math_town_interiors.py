"""Inside the houses of the Math town: the furniture and the fittings of its rooms.

Jon, 2026-10-22: "Add more game world content to math town", and of what I
offered, "Enterable interiors". Three rooms, each its own LDtk level in the
theme `math_interior` (whitewashed plaster, a wainscot of hexagonal tiles,
timber under the ceiling: `backgrounds/math_town.interior`):

- The café on the first terrace, "The Convergent Series": a counter with a
  brass espresso machine, a chalkboard menu, marble tables, a shelf of jars,
  windows onto the terrace, lamps.
- The Surveyor's Office on the second terrace: the great map of the town on
  the wall (whose street runs off its right edge and comes back on its left),
  a drafting table, a cabinet of map drawers, a theodolite, and a gallery of
  rolled maps up a ladder.
- The Observatory on the summit: the inside of the dome with its slit open
  on the night, the brass telescope on its pier, its platform, a star chart
  (the same stars at both of its edges) and the astronomer's desk.

Each is an LDtk `Prop` (decoration, no collision). Where the art draws a top
a body stands on (the counter, the gallery, the platform), the room places a
still one-way platform. Drawn with `_town_kit` in world units at `PX` pixels
to the unit; each piece is its own target, so a room names the piece it wants
by its `kind`. No rings or round emblems (Jon, 2026-10-14).

Animations:

- ``idle``: 1 frame.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Callable, Dict, List, Tuple

import numpy as np
from PIL import Image

from ...authoring.sheet_build import build_sheet
from ._town_kit import Canvas, Kit, box, mix, scale
from .castle_godwin import GLYPHS

#: Pixels of the frame to one world unit.
PX = 2

PAL = {
    "stone": (214, 206, 190), "stone_light": (246, 240, 226), "trim": (246, 242, 232), "dark": (40, 52, 70),
    "glass_top": (110, 170, 214), "glass_low": (50, 90, 130), "lamp": (255, 210, 140), "wood": (96, 70, 52),
    "leaf": (70, 128, 80), "iron": (36, 48, 64), "brass": (200, 150, 70), "glaze": (226, 180, 70),
}
WOOD = (120, 84, 58)
WOOD_DARK = (74, 50, 36)
WOOD_LIGHT = (168, 124, 86)
BRASS = (204, 156, 72)
BRASS_LIGHT = (246, 214, 140)
IRON = (40, 46, 56)
MARBLE = (236, 232, 222)
SLATE = (46, 58, 54)
CHALK = (240, 240, 230)
CHALK_DIM = (190, 196, 186)
PAPER = (236, 224, 196)
PAPER_DARK = (196, 178, 140)
INK = (60, 70, 96)
TILE = (70, 112, 170)
TERRACOTTA = (184, 100, 70)
LAMP = (255, 214, 150)
NIGHT = (22, 30, 58)
NIGHT_LOW = (44, 58, 100)
STAR = (250, 246, 226)
SKY_DAY = (150, 196, 236)
SKY_LOW = (226, 236, 242)
LIMESTONE = (228, 216, 192)

# ---- Lettering -------------------------------------------------------------------

#: The glyphs of the castle's signs (`castle_godwin.GLYPHS`), and the ones a
#: menu and a map need that they lack. A grid 4 wide and 6 high.
EXTRA_GLYPHS: Dict[str, List[List[Tuple[float, float]]]] = {
    "J": [[(4, 0), (4, 5.4), (3.4, 6), (0.6, 6), (0, 5.4)]],
    "Q": [[(0.6, 0), (3.4, 0), (4, 0.6), (4, 5.4), (3.4, 6), (0.6, 6), (0, 5.4), (0, 0.6), (0.6, 0)], [(2.4, 4.2), (4, 6.4)]],
    "X": [[(0, 0), (4, 6)], [(4, 0), (0, 6)]],
    "Z": [[(0, 0), (4, 0), (0, 6), (4, 6)]],
    "4": [[(3, 6), (3, 0), (0, 4), (4, 4)]],
    "6": [[(4, 0), (0.6, 0), (0, 0.6), (0, 5.4), (0.6, 6), (3.4, 6), (4, 5.4), (4, 3.4), (3.4, 2.8), (0, 2.8)]],
    "8": [[(0.6, 0), (3.4, 0), (4, 0.6), (4, 2.4), (3.4, 3), (0.6, 3), (0, 3.6), (0, 5.4), (0.6, 6), (3.4, 6), (4, 5.4), (4, 3.6), (3.4, 3), (0.6, 3), (0, 2.4), (0, 0.6), (0.6, 0)]],
    "9": [[(4, 3.2), (0.6, 3.2), (0, 2.6), (0, 0.6), (0.6, 0), (3.4, 0), (4, 0.6), (4, 5.4), (3.4, 6), (0, 6)]],
    ".": [[(2, 5.4), (2, 6)]],
    "-": [[(0.8, 3), (3.2, 3)]],
    "+": [[(0.6, 3), (3.4, 3)], [(2, 1.4), (2, 4.6)]],
    "=": [[(0.6, 2.2), (3.4, 2.2)], [(0.6, 3.8), (3.4, 3.8)]],
    "/": [[(4, 0), (0, 6)]],
    "?": [[(0, 1), (0.8, 0), (3.2, 0), (4, 1), (4, 2.2), (2, 3.6), (2, 4.4)], [(2, 5.4), (2, 6)]],
    "'": [[(2, 0), (2, 1.6)]],
    # pi: a bar and two legs.
    "π": [[(0, 1), (4, 1)], [(1.2, 1), (1.2, 6)], [(3, 1), (3, 5.4), (3.6, 6)]],
    # the square root: a tick and its roof.
    "√": [[(0, 3.6), (0.8, 3), (1.8, 6), (2.8, 0), (4.4, 0)]],
    # aleph, as a surveyor's clerk writes it: an X with two hooks.
    "ℵ": [[(0.4, 0), (3.6, 6)], [(3.4, 0), (3.4, 2), (2.4, 2.6)], [(0.6, 6), (0.6, 4), (1.6, 3.4)]],
}
LETTERS = {**GLYPHS, **EXTRA_GLYPHS}


def letters(c: Canvas, text: str, x: float, top: float, h: float, ink, width: float = 1.0, centre: bool = False) -> float:
    """`text` in block capitals `h` high from `x` (or centred on it), drawn
    as strokes `width` of a letter's unit thick. Returns its width."""
    unit = h / 6.0
    adv = unit * 5.4
    total = adv * len(text) - unit * 1.4
    if centre:
        x -= total / 2
    strokes = []
    for ch in text:
        for path in LETTERS.get(ch, []):
            strokes.append([(x + px * unit, top + py * unit) for px, py in path])
        x += adv
    c.put(c.mask(lambda p: [p.line(s, unit * width) for s in strokes]), ink)
    return total


# ---- Pieces that several rooms share ---------------------------------------------


def wood_box(c: Canvas, x0, y0, x1, y1, colour=WOOD, tag="wood") -> np.ndarray:
    """A box of planed wood: grain, a light top edge, a dark foot."""
    m = c.mask(box(x0, y0, x1, y1))
    c.put(m, colour)
    grain = c.noise((tag, "grain"), 3, 30, 2)
    c.tone(m * (grain - 0.5), 0.22)
    c.put(m * c.mask(box(x0, y0, x1, y0 + 1.6)), mix(colour, (255, 240, 210), 0.45))
    c.put(m * c.mask(box(x0, y1 - 1.6, x1, y1)), scale(colour, 0.55))
    c.put(c.mask(lambda p: p.line([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], 0.7)), WOOD_DARK, 0.8)
    return m


def pendant_lamp(c: Canvas, cx, top, drop, lit=0.9) -> None:
    """A lamp on a chain from the ceiling: a brass cap, a glass shade, its glow."""
    c.put(c.mask(lambda p: p.line([(cx, top), (cx, top + drop)], 0.8)), IRON)
    y = top + drop
    c.put(c.mask(lambda p: p.poly([(cx - 3, y), (cx + 3, y), (cx + 10, y + 9), (cx - 10, y + 9)])), BRASS)
    c.put(c.mask(lambda p: p.poly([(cx - 3, y), (cx + 3, y), (cx + 10, y + 9), (cx - 10, y + 9)])) * c.mask(box(cx - 10, y, cx, y + 9)), BRASS_LIGHT, 0.35)
    glow = c.mask(lambda p: p.ellipse(cx, y + 11, 6, 3.5), blur=0.4)
    c.put(glow, LAMP)
    c.light(c.mask(lambda p: p.ellipse(cx, y + 14, 26, 18), blur=6.0), LAMP, 0.55 * lit)


def window_view(c: Canvas, k: Kit, x0, y0, x1, y1, view: Callable[[Canvas, np.ndarray, float, float, float, float], None], tag) -> None:
    """An arched window in a deep plaster reveal: `view` paints what is seen
    through it (inside the opening), then the glazing bars, the sill."""
    open_ = c.mask(lambda p: p.arch(x0, y0, x1, y1))
    reveal = c.mask(lambda p: p.arch(x0 - 4, y0 - 4, x1 + 4, y1 + 2))
    c.put(reveal, (226, 210, 186))
    c.tone(reveal * c.mask(box(x0 - 4, y0 - 4, x0, y1)), -0.18)
    view(c, open_, x0, y0, x1, y1)
    # The glazing bars: a cross, and the arch's own bar.
    w = x1 - x0
    bars = c.mask(lambda p: [p.line([((x0 + x1) / 2, y0 + w / 2), ((x0 + x1) / 2, y1)], 1.2), p.line([(x0, y0 + w / 2 + (y1 - y0 - w / 2) * 0.45), (x1, y0 + w / 2 + (y1 - y0 - w / 2) * 0.45)], 1.2)])
    c.put(bars * open_, (236, 230, 216))
    c.put(c.mask(box(x0 - 6, y1, x1 + 6, y1 + 4)), (240, 232, 214))
    c.put(c.mask(box(x0 - 6, y1 + 3, x1 + 6, y1 + 4)), (170, 150, 120))


def terrace_view(c: Canvas, m: np.ndarray, x0, y0, x1, y1) -> None:
    """Day on the terrace: sky, the far terraces in the haze, an arch of the
    aqueduct, an olive."""
    c.paint(m, c.ramp([(y0, SKY_DAY), (y1, SKY_LOW)]))
    hills = c.mask(lambda p: p.poly([(x0, y1 - (y1 - y0) * 0.35), (x0 + (x1 - x0) * 0.3, y1 - (y1 - y0) * 0.5), (x0 + (x1 - x0) * 0.7, y1 - (y1 - y0) * 0.38), (x1, y1 - (y1 - y0) * 0.45), (x1, y1), (x0, y1)]))
    c.put(hills * m, (196, 206, 214))
    # White houses far off.
    rng = c.rand("terrace view", x0)
    houses = c.mask(lambda p: [p.rect(x, y1 - (y1 - y0) * rng.uniform(0.28, 0.42), x + rng.uniform(5, 9), y1) for x in np.arange(x0 + 2, x1 - 4, 9.0)])
    c.put(houses * m, (240, 238, 232))
    # The aqueduct crossing the view.
    deck = y0 + (y1 - y0) * 0.42
    span = (x1 - x0) / 2
    aq = c.mask(box(x0, deck, x1, deck + 5)) + c.mask(lambda p: [p.rect(x0 + i * span - 2, deck, x0 + i * span + 2, y1) for i in range(3)])
    c.put(np.clip(aq, 0, 1) * m, (214, 204, 184))
    c.put(c.mask(lambda p: p.ellipse(x0 + (x1 - x0) * 0.25, y1 - 6, 8, 7)) * m, (90, 130, 90))


def night_view(c: Canvas, m: np.ndarray, x0, y0, x1, y1) -> None:
    """The night through the slit of the dome: dark blue, many stars."""
    c.paint(m, c.ramp([(y0, NIGHT), (y1, NIGHT_LOW)]))
    rng = c.rand("stars", x0, y0)
    stars = c.mask(lambda p: [p.ellipse(rng.uniform(x0, x1), rng.uniform(y0, y1), r, r) for r in [rng.choice([0.5, 0.6, 0.8, 1.1]) for _ in range(int((x1 - x0) * (y1 - y0) / 60))]])
    c.put(stars * m, STAR)


# ---- The café ----------------------------------------------------------------------


def cafe_counter(c: Canvas, k: Kit, w: float, h: float) -> None:
    """The counter: a marble top over a front of blue tiles, the brass
    espresso machine and a row of cups on it. Its top is at `TOP`."""
    top = h - COUNTER_H
    # The front: tiles in a wooden frame.
    wood_box(c, 0, top + 4, w, h, WOOD, "counter")
    face = c.mask(box(6, top + 10, w - 6, h - 6))
    c.put(face, TILE)
    tiles = c.mask(lambda p: [p.rect(x, y, x + 9, y + 9) for x in np.arange(7, w - 7, 10) for y in np.arange(top + 11, h - 7, 10)])
    c.put(tiles * face, mix(TILE, (255, 255, 255), 0.12))
    c.put(c.mask(lambda p: [p.rect(x, y, x + 9, y + 9) for i, x in enumerate(np.arange(7, w - 7, 10)) for j, y in enumerate(np.arange(top + 11, h - 7, 10)) if (i * 3 + j * 5) % 7 == 0]) * face, (214, 170, 84))
    # The marble top.
    c.put(c.mask(box(-2, top, w + 2, top + 5)), MARBLE)
    c.put(c.mask(box(-2, top + 4, w + 2, top + 5)), (180, 174, 164))
    # The espresso machine: a brass drum with a dome and an eagle-less top.
    mx = w * 0.62
    body = c.mask(lambda p: p.rect(mx - 16, top - 34, mx + 16, top))
    c.paint(body, c.ramp([(top - 34, BRASS_LIGHT), (top, BRASS)]))
    c.tone(body * c.mask(box(mx + 6, top - 34, mx + 16, top)), -0.25)
    c.put(c.mask(lambda p: p.ellipse(mx, top - 34, 16, 6)), BRASS_LIGHT)
    c.put(c.mask(lambda p: p.ellipse(mx, top - 40, 6, 6)), BRASS)
    c.put(c.mask(lambda p: p.rect(mx - 22, top - 18, mx - 14, top - 14)), IRON)
    c.put(c.mask(lambda p: p.rect(mx + 14, top - 18, mx + 22, top - 14)), IRON)
    # Steam.
    c.put(c.mask(lambda p: p.line([(mx, top - 46), (mx - 4, top - 54), (mx + 2, top - 62), (mx - 2, top - 70)], 2.0), blur=1.2), (255, 255, 255), 0.45)
    # Cups, stacked and set out.
    for i, cx in enumerate(np.arange(16, w * 0.45, 14)):
        cup = c.mask(lambda p: p.poly([(cx - 4, top - 7), (cx + 4, top - 7), (cx + 3, top), (cx - 3, top)]))
        c.put(cup, (246, 244, 236))
        c.put(c.mask(lambda p: p.rect(cx - 6, top - 1, cx + 6, top)), (230, 226, 216))
        if i % 2:
            c.put(c.mask(lambda p: p.ellipse(cx, top - 7, 3.6, 1.0)), (90, 56, 36))


def cafe_menu(c: Canvas, k: Kit, w: float, h: float) -> None:
    """The chalkboard menu on the wall, in a wooden frame."""
    wood_box(c, 0, 0, w, h, WOOD_DARK, "menu frame")
    board = c.mask(box(4, 4, w - 4, h - 4))
    c.put(board, SLATE)
    c.tone(board * (c.noise("slate", 6, 4, 2) - 0.5), 0.25)
    letters(c, "MENU", w / 2, 9, 9, CHALK, 1.1, centre=True)
    rows = [("π PIE", "3.14"), ("E-SPRESSO", "2.72"), ("√ROOT BEER", "1.41"), ("GOLDEN TEA", "1.62")]
    for i, (name, price) in enumerate(rows):
        y = 26 + i * 13
        letters(c, name, 9, y, 6.5, CHALK_DIM, 1.0)
        letters(c, price, w - 9 - (6.5 / 6 * 5.4 * len(price) - 6.5 / 6 * 1.4), y, 6.5, CHALK, 1.0)
    letters(c, "REFILLS: ℵ0", w / 2, h - 16, 6.0, (232, 210, 150), 1.0, centre=True)


def cafe_table(c: Canvas, k: Kit, w: float, h: float) -> None:
    """A round marble table on one iron foot, with a bentwood chair each side
    and a cup on it."""
    cx = w / 2
    top = h - 34
    # The chairs: a bentwood back and seat, side on.
    for side in (-1, 1):
        x = cx + side * 26
        back = x + side * 9
        c.put(c.mask(lambda p: p.line([(back, h), (back, top - 10), (back - side * 2, top - 18)], 2.0)), WOOD_DARK)
        c.put(c.mask(lambda p: p.line([(x - side * 8, h), (x - side * 6, top + 10)], 1.6)), WOOD_DARK)
        c.put(c.mask(lambda p: p.line([(x - side * 9, top + 10), (back, top + 10)], 2.4)), WOOD)
    # The table.
    c.put(c.mask(lambda p: p.line([(cx, top + 3), (cx, h - 3)], 2.4)), IRON)
    c.put(c.mask(lambda p: p.poly([(cx - 10, h), (cx + 10, h), (cx + 3, h - 4), (cx - 3, h - 4)])), IRON)
    c.put(c.mask(lambda p: p.ellipse(cx, top, 17, 3.2)), MARBLE)
    c.put(c.mask(lambda p: p.ellipse(cx, top + 1.2, 17, 2.4)) * c.mask(box(0, top + 0.5, w, top + 4)), (196, 190, 180))
    cup = c.mask(lambda p: p.poly([(cx + 2, top - 7), (cx + 9, top - 7), (cx + 8, top - 2), (cx + 3, top - 2)]))
    c.put(cup, (246, 244, 236))


def cafe_shelf(c: Canvas, k: Kit, w: float, h: float) -> None:
    """A shelf on two brackets: jars of beans with numbers on them, a plant."""
    shelf_y = h - 8
    wood_box(c, 0, shelf_y, w, shelf_y + 5, WOOD, "shelf")
    for x in (10, w - 14):
        c.put(c.mask(lambda p: p.poly([(x, shelf_y + 5), (x + 4, shelf_y + 5), (x + 4, h)])), WOOD_DARK)
    for i, x in enumerate(np.arange(14, w - 30, 22)):
        jar = c.mask(box(x, shelf_y - 20, x + 15, shelf_y))
        c.put(jar, (230, 236, 232), 0.85)
        beans = c.mask(box(x + 1, shelf_y - 13 + (i % 3) * 2, x + 14, shelf_y - 1))
        c.put(beans, (96, 60, 40))
        c.put(c.mask(box(x - 1, shelf_y - 23, x + 16, shelf_y - 20)), (176, 108, 78))
        c.put(c.mask(box(x + 3, shelf_y - 11, x + 12, shelf_y - 5)), PAPER)
        letters(c, str((2, 3, 5, 7, 11, 13)[i % 6]), x + 7.5, shelf_y - 10.4, 4.4, INK, 1.0, centre=True)
    pot = w - 22
    c.put(c.mask(lambda p: p.poly([(pot - 7, shelf_y - 12), (pot + 7, shelf_y - 12), (pot + 5, shelf_y), (pot - 5, shelf_y)])), TERRACOTTA)
    c.put(c.mask(lambda p: [p.ellipse(pot + dx, shelf_y - 18 + dy, 5, 3) for dx, dy in ((-5, 0), (4, -2), (0, -7), (-3, -12), (5, -10))]), (80, 140, 90))


def cafe_window(c: Canvas, k: Kit, w: float, h: float) -> None:
    """A window onto the terrace, with a box of flowers under it."""
    window_view(c, k, 10, 8, w - 10, h - 14, terrace_view, "cafe window")
    box_m = c.mask(box(6, h - 12, w - 6, h - 4))
    c.put(box_m, TERRACOTTA)
    c.put(c.mask(lambda p: [p.ellipse(x, h - 14, 3, 3) for x in np.arange(10, w - 8, 6)]), (90, 140, 90))
    c.put(c.mask(lambda p: [p.ellipse(x, h - 16, 1.8, 1.8) for x in np.arange(12, w - 8, 9)]), (240, 200, 80))


def cafe_lamps(c: Canvas, k: Kit, w: float, h: float) -> None:
    """Three lamps on chains, hung from the ceiling over the room."""
    for i, x in enumerate((w * 0.18, w * 0.5, w * 0.82)):
        pendant_lamp(c, x, 0, h - 26 - (i % 2) * 8)


# ---- The Surveyor's Office ---------------------------------------------------------


def office_map(c: Canvas, k: Kit, w: float, h: float) -> None:
    """The great map of the town: the street, the terraces in section, the
    aqueduct over them, the passage under the first terrace. The street runs
    off the right edge with an arrow, and an arrow brings it back on the
    left: a surveyor's question mark beside each."""
    wood_box(c, 0, 0, w, h, WOOD_DARK, "map frame")
    sheet = c.mask(box(5, 5, w - 5, h - 5))
    c.put(sheet, PAPER)
    c.tone(sheet * (c.noise("map paper", 5, 4, 3) - 0.5), 0.18)
    # Its edges are browned.
    edge = np.clip(1 - np.minimum(np.minimum(c.x - 5, w - 5 - c.x), np.minimum(c.y - 5, h - 5 - c.y)) / 14, 0, 1)
    c.tone(sheet * edge, -0.25)
    # The grid of the survey.
    grid = c.mask(lambda p: [p.line([(x, 8), (x, h - 8)], 0.35) for x in np.arange(12, w - 8, 16)] + [p.line([(8, y), (w - 8, y)], 0.35) for y in np.arange(14, h - 8, 16)])
    c.put(grid * sheet, (176, 160, 130))
    # The town in section: the street, then the terraces stepping up.
    base = h - 20
    x_street, x_t1, x_t2, x_top = 14, w * 0.48, w * 0.66, w * 0.80
    ground = [(14, base), (x_t1, base), (x_t1, base - 22), (x_t2, base - 22), (x_t2, base - 42), (x_top, base - 42), (x_top, base - 62), (w - 14, base - 62)]
    c.put(c.mask(lambda p: p.line(ground, 1.6)), INK)
    # The aqueduct across the top, its arches.
    deck = base - 66
    c.put(c.mask(lambda p: [p.line([(14, deck), (x_top, deck)], 1.2)] + [p.line([(x, deck), (x, base - (0 if x < x_t1 else 22 if x < x_t2 else 42))], 0.8) for x in np.arange(30, x_top, 24)]), INK)
    # The houses as small blocks.
    rng = c.rand("map houses")
    blocks = c.mask(lambda p: [p.rect(x, gy - rng.uniform(6, 12), x + rng.uniform(6, 10), gy) for x, gy in [(x, base) for x in np.arange(24, x_t1 - 12, 18)] + [(x, base - 22) for x in np.arange(x_t1 + 6, x_t2 - 8, 16)] + [(x, base - 42) for x in np.arange(x_t2 + 6, x_top - 8, 16)]])
    c.put(blocks, (176, 108, 78), 0.85)
    # The passage under the first terrace, dashed.
    c.put(c.mask(lambda p: [p.line([(x, base - 6), (x + 6, base - 6)], 0.9) for x in np.arange(x_t1 + 2, w - 18, 10)]), INK)
    # The street goes off the right edge... and comes back on the left.
    c.put(c.mask(lambda p: [p.line([(w - 30, base - 6), (w - 10, base - 6)], 1.4), p.poly([(w - 10, base - 10), (w - 4, base - 6), (w - 10, base - 2)])]), (176, 52, 52))
    c.put(c.mask(lambda p: [p.line([(4, base - 6), (24, base - 6)], 1.4), p.poly([(24, base - 10), (30, base - 6), (24, base - 2)])]), (176, 52, 52))
    letters(c, "?", w - 20, base - 24, 9, (176, 52, 52), 1.2, centre=True)
    letters(c, "?", 16, base - 24, 9, (176, 52, 52), 1.2, centre=True)
    letters(c, "EUCLID STREET AND TERRACES", w / 2, 12, 8, INK, 1.0, centre=True)
    letters(c, "SURVEYED BY G. CANTER", w / 2, 24, 5, mix(INK, PAPER, 0.3), 1.0, centre=True)
    # The compass rose of a mapmaker: four points, no circle.
    cx, cy = w - 26, 44
    c.put(c.mask(lambda p: [p.poly([(cx, cy - 12), (cx + 3, cy), (cx, cy + 12), (cx - 3, cy)]), p.poly([(cx - 12, cy), (cx, cy - 3), (cx + 12, cy), (cx, cy + 3)])]), INK)
    letters(c, "N", cx, cy - 22, 6, INK, 1.0, centre=True)


def office_drafting(c: Canvas, k: Kit, w: float, h: float) -> None:
    """A drafting table: a tilted board on a trestle, a sheet pinned on it, a
    T-square and a pair of compasses; a stool."""
    board_top, board_low = h - 64, h - 44
    # The trestle.
    c.put(c.mask(lambda p: [p.line([(14, h), (w * 0.45, board_low)], 2.2), p.line([(w - 14, h), (w * 0.55, board_low)], 2.2), p.line([(22, h - 14), (w - 22, h - 14)], 1.8)]), WOOD_DARK)
    # The board, tilted toward the room.
    board = c.mask(lambda p: p.poly([(6, board_low), (w - 6, board_top), (w - 4, board_top + 5), (8, board_low + 5)]))
    c.put(board, WOOD_LIGHT)
    sheet = c.mask(lambda p: p.poly([(14, board_low - 2), (w - 16, board_top + 1), (w - 15, board_top + 4), (15, board_low + 1)]))
    c.put(sheet, PAPER)
    # A line ruled on it.
    c.put(c.mask(lambda p: p.line([(26, board_low - 3.5), (w * 0.6, board_low - 3.5 - (board_low - board_top) * 0.56)], 0.5)), INK)
    # The T-square along its edge, and the compasses standing open.
    c.put(c.mask(lambda p: p.line([(10, board_low + 2), (w * 0.7, board_low + 2 - (board_low - board_top) * 0.68)], 1.6)), (220, 190, 120))
    cx = w * 0.55
    c.put(c.mask(lambda p: p.line([(cx - 5, board_top + 8), (cx, board_top - 8), (cx + 6, board_top + 6)], 1.0)), (190, 196, 206))
    # The stool.
    sx = w * 0.22
    c.put(c.mask(lambda p: [p.line([(sx - 8, h), (sx - 4, h - 20)], 1.6), p.line([(sx + 8, h), (sx + 4, h - 20)], 1.6)]), WOOD_DARK)
    c.put(c.mask(box(sx - 9, h - 23, sx + 9, h - 19)), WOOD)


def office_cabinet(c: Canvas, k: Kit, w: float, h: float) -> None:
    """A cabinet of flat map drawers, each with a brass pull and a label:
    aleph-null, aleph-one, and so on up to drawers that say only "...". The
    top drawer is open, and a smaller cabinet is in it."""
    wood_box(c, 0, 0, w, h, WOOD, "cabinet")
    rows = 7
    dh = (h - 10) / rows
    labels = ["ℵ0", "ℵ1", "ℵ2", "ℵ3", "ℵ4", "...", "..."]
    for i in range(rows):
        y = 5 + i * dh
        d = c.mask(box(5, y + 1, w - 5, y + dh - 1))
        c.put(d, mix(WOOD, WOOD_LIGHT, 0.25))
        c.put(c.mask(box(5, y + dh - 2, w - 5, y + dh - 1)), WOOD_DARK)
        c.put(c.mask(box(w / 2 - 7, y + dh / 2 - 1, w / 2 + 7, y + dh / 2 + 1.5)), BRASS)
        c.put(c.mask(box(10, y + dh / 2 - 4, 26, y + dh / 2 + 4)), PAPER)
        letters(c, labels[i], 18, y + dh / 2 - 2.4, 4.8, INK, 1.0, centre=True)
    # The open top drawer sticks out, and a little cabinet stands in it.
    c.put(c.mask(box(w - 4, 4, w + 10, 5 + dh)), WOOD_LIGHT)
    c.put(c.mask(box(w - 2, -10, w + 8, 6)), WOOD)
    for j in range(3):
        c.put(c.mask(box(w - 1, -9 + j * 5, w + 7, -6 + j * 5)), mix(WOOD, WOOD_LIGHT, 0.4))


def office_theodolite(c: Canvas, k: Kit, w: float, h: float) -> None:
    """A surveyor's theodolite on a tripod: a brass telescope on a turntable."""
    cx = w / 2
    head = h - 70
    c.put(c.mask(lambda p: [p.line([(cx, head + 8), (cx - 18, h)], 1.8), p.line([(cx, head + 8), (cx + 18, h)], 1.8), p.line([(cx, head + 8), (cx + 4, h)], 1.8)]), WOOD)
    c.put(c.mask(box(cx - 9, head + 4, cx + 9, head + 9)), BRASS)
    c.put(c.mask(lambda p: [p.line([(cx - 6, head + 4), (cx - 5, head - 6)], 1.4), p.line([(cx + 6, head + 4), (cx + 5, head - 6)], 1.4)]), BRASS)
    scope = c.mask(lambda p: p.line([(cx - 14, head - 4), (cx + 14, head - 10)], 4.0))
    c.put(scope, BRASS)
    c.put(scope * c.mask(box(0, 0, w, head - 8)), BRASS_LIGHT, 0.4)
    c.put(c.mask(lambda p: p.ellipse(cx + 14, head - 10, 1.4, 2.6)), (120, 170, 214))


def office_gallery(c: Canvas, k: Kit, w: float, h: float) -> None:
    """A gallery on timber posts along the wall, with a rail, and shelves of
    rolled maps on it; a ladder up to it at its left end. Its floor is at
    `GALLERY_FLOOR` from the frame's top."""
    floor = GALLERY_FLOOR
    # Posts and braces under it.
    for x in np.arange(40, w, (w - 40) / 3):
        c.put(c.mask(box(x - 4, floor + 6, x + 4, h)), WOOD_DARK)
        c.put(c.mask(lambda p: [p.line([(x - 4, floor + 26), (x - 22, floor + 6)], 2.4), p.line([(x + 4, floor + 26), (x + 22, floor + 6)], 2.4)]), WOOD_DARK)
    wood_box(c, 20, floor, w, floor + 8, WOOD, "gallery floor")
    # The rail.
    c.put(c.mask(lambda p: [p.line([(24, floor - 22), (w, floor - 22)], 2.2)] + [p.line([(x, floor), (x, floor - 22)], 1.4) for x in np.arange(30, w, 14)]), WOOD_DARK)
    # Shelves of rolled maps behind the rail.
    for i, y in enumerate((floor - 70, floor - 44)):
        wood_box(c, 40, y, w - 10, y + 4, WOOD, f"map shelf {i}")
        rng = c.rand("rolls", i)
        for x in np.arange(46, w - 20, 9):
            r = rng.uniform(3, 4.2)
            c.put(c.mask(lambda p: p.rect(x, y - 2 * r, x + 7, y)), mix(PAPER, PAPER_DARK, rng.uniform(0, 1)))
            c.put(c.mask(lambda p: p.ellipse(x + 3.5, y - r, 3.2, r * 0.9)), PAPER_DARK)
    # The ladder at the left end.
    lx0, lx1 = 2, 18
    c.put(c.mask(lambda p: [p.line([(lx0, floor - 30), (lx0, h)], 1.8), p.line([(lx1, floor - 30), (lx1, h)], 1.8)] + [p.line([(lx0, y), (lx1, y)], 1.4) for y in np.arange(floor - 22, h, 12)]), WOOD_LIGHT)


# ---- The Observatory ---------------------------------------------------------------


def obs_dome(c: Canvas, k: Kit, w: float, h: float) -> None:
    """The inside of the dome over the drum: its ribs, the panels between
    them, and its slit open on the night from the crown down to the drum."""
    cx = w / 2
    # The top of the drum's wall in the corners beside the dome, in shadow.
    c.put(c.mask(box(0, 0, w, h)), (150, 130, 108))
    c.tone(c.mask(box(0, 0, w, h)) * np.clip(1 - c.y / h, 0, 1), -0.35)
    shell = c.mask(lambda p: p.ellipse(cx, h, w / 2, h)) * c.mask(box(0, 0, w, h))
    c.paint(shell, c.ramp([(0, (120, 128, 140)), (h, (196, 200, 206))]))
    c.tone(shell * (c.noise("dome panels", 8, 4, 2) - 0.5), 0.08)
    # The slit: a band from the crown down, open on the night.
    slit = c.mask(box(cx - 26, 0, cx + 26, h)) * shell
    night_view(c, slit, cx - 26, 0, cx + 26, h)
    # The ribs: arcs from the drum to the crown (lines in the section).
    ribs = c.mask(lambda p: [p.line([(cx + math.sin(a) * (w / 2) * math.cos(t), h - math.cos(a) * 0 - h * math.sin(t)) for t in np.linspace(0, math.pi / 2, 16)], 2.2) for a in (math.radians(v) for v in (-70, -45, -22, 22, 45, 70))])
    c.put(ribs * shell * (1 - c.mask(box(cx - 28, 0, cx + 28, h))), (90, 96, 110))
    # The edges of the slit, and the drum's cornice at the foot.
    c.put(c.mask(lambda p: [p.line([(cx - 27, 0), (cx - 27, h)], 3.0), p.line([(cx + 27, 0), (cx + 27, h)], 3.0)]) * shell, (70, 76, 90))
    c.put(c.mask(box(0, h - 7, w, h)), (226, 220, 206))
    c.put(c.mask(box(0, h - 2, w, h)), (150, 140, 124))


def obs_telescope(c: Canvas, k: Kit, w: float, h: float) -> None:
    """The great brass refractor on its iron pier, pointing up through the
    slit; a counterweight; a ladder to its eyepiece."""
    pier_x = w * 0.42
    head = h - 120
    # The pier.
    pier = c.mask(lambda p: p.poly([(pier_x - 16, h), (pier_x + 16, h), (pier_x + 8, head + 10), (pier_x - 8, head + 10)]))
    c.paint(pier, c.ramp([(head, (70, 80, 96)), (h, (40, 46, 56))]))
    c.put(c.mask(box(pier_x - 20, h - 6, pier_x + 20, h)), IRON)
    # The mount, and the tube up to the sky.
    c.put(c.mask(lambda p: p.ellipse(pier_x, head + 8, 10, 7)), BRASS)
    tube = c.mask(lambda p: p.line([(pier_x - 46, head + 52), (pier_x + 70, head - 72)], 13.0))
    c.paint(tube, c.ramp([(head - 80, BRASS_LIGHT), (head + 60, BRASS)]))
    c.put(c.mask(lambda p: [p.line([(pier_x + t * 116 - 46 - 7, head + 52 - t * 124 - 7), (pier_x + t * 116 - 46 + 7, head + 52 - t * 124 + 7)], 2.4) for t in (0.18, 0.5, 0.82)]), (150, 106, 50))
    c.put(c.mask(lambda p: p.ellipse(pier_x + 70, head - 72, 7, 7)), (120, 170, 214))
    # The eyepiece at the low end, and the counterweight.
    c.put(c.mask(lambda p: p.line([(pier_x - 46, head + 52), (pier_x - 52, head + 62)], 4.0)), IRON)
    c.put(c.mask(lambda p: p.line([(pier_x, head + 8), (pier_x + 22, head + 26)], 2.0)), IRON)
    c.put(c.mask(box(pier_x + 18, head + 24, pier_x + 30, head + 36)), IRON)


def obs_platform(c: Canvas, k: Kit, w: float, h: float) -> None:
    """The observing platform on iron legs, with a rail; a stair of open
    treads up to it from the floor at its left. Its floor is `PLATFORM_FLOOR`
    from the frame's top."""
    floor = PLATFORM_FLOOR
    x1 = w * STAIR_RUN
    for x in (x1 + 20, w - 8):
        c.put(c.mask(box(x - 3, floor + 6, x + 3, h)), IRON)
    c.put(c.mask(lambda p: p.line([(x1 + 20, floor + 40), (w - 8, floor + 8)], 1.6)), IRON)
    wood_box(c, x1, floor, w, floor + 7, WOOD, "platform")
    c.put(c.mask(lambda p: [p.line([(x1 + 4, floor - 22), (w, floor - 22)], 2.0)] + [p.line([(x, floor), (x, floor - 22)], 1.2) for x in np.arange(x1 + 6, w, 12)]), IRON)
    # The stair: open treads on a stringer, from the floor up to the platform.
    x0 = 6.0
    c.put(c.mask(lambda p: p.line([(x0, h), (x1, floor + 4)], 2.4)), IRON)
    steps = int((h - floor) / 12)
    for i in range(1, steps + 1):
        t = i / (steps + 0.0)
        x = x0 + (x1 - x0) * t
        y = h - (h - floor) * t
        c.put(c.mask(box(x - 8, y, x + 6, y + 3)), WOOD)
    c.put(c.mask(lambda p: p.line([(x0, h - 28), (x1, floor - 22)], 1.6)), IRON)


def obs_chart(c: Canvas, k: Kit, w: float, h: float) -> None:
    """A star chart on the wall: the stars and the lines of their figures on
    blue paper. The figure at the left edge is cut by the edge, and the same
    figure comes back cut at the right edge."""
    wood_box(c, 0, 0, w, h, WOOD_DARK, "chart frame")
    sheet = c.mask(box(4, 4, w - 4, h - 4))
    c.put(sheet, (36, 52, 92))
    c.tone(sheet * (c.noise("chart", 4, 3, 2) - 0.5), 0.15)
    rng = c.rand("chart stars")
    stars = c.mask(lambda p: [p.ellipse(rng.uniform(6, w - 6), rng.uniform(14, h - 6), r, r) for r in [rng.choice([0.5, 0.7, 0.9]) for _ in range(70)]])
    c.put(stars * sheet, (200, 210, 230))
    # One figure, a kite of five stars, cut by each edge: its right half at
    # the left edge, its left half at the right edge.
    fig = [(0, 0), (12, -10), (22, 0), (12, 14), (0, 0), (-12, 6)]
    for ox, part in ((4 - 8, "right"), (w - 4 + 8 - 22, "left")):
        pts = [(ox + x, h * 0.55 + y) for x, y in fig]
        clip = sheet
        c.put(c.mask(lambda p: p.line(pts, 0.6)) * clip, (150, 170, 220))
        c.put(c.mask(lambda p: [p.ellipse(x, y, 1.6, 1.6) for x, y in pts]) * clip, (250, 246, 226))
    letters(c, "THE SKY OF THE TOWN", w / 2, 8, 5, (220, 210, 170), 1.0, centre=True)


def obs_desk(c: Canvas, k: Kit, w: float, h: float) -> None:
    """The astronomer's desk: an open logbook, a lamp with a green shade, a
    stack of books, a chair pushed back."""
    top = h - 34
    wood_box(c, 0, top, w, top + 6, WOOD, "desk")
    for x in (4, w - 10):
        c.put(c.mask(box(x, top + 6, x + 6, h)), WOOD_DARK)
    wood_box(c, w - 46, top + 6, w - 10, h - 6, WOOD, "desk drawers")
    # The logbook, open.
    c.put(c.mask(lambda p: p.poly([(10, top), (34, top - 3), (58, top), (34, top + 1)])), PAPER)
    c.put(c.mask(lambda p: [p.line([(14 + i * 3, top - 1), (30, top - 2.6 + i * 0.3)], 0.3) for i in range(3)]), INK)
    # The lamp.
    lx = w - 28
    c.put(c.mask(lambda p: p.line([(lx, top), (lx, top - 22)], 1.4)), BRASS)
    c.put(c.mask(lambda p: p.poly([(lx - 12, top - 20), (lx + 12, top - 20), (lx + 7, top - 28), (lx - 7, top - 28)])), (70, 130, 90))
    c.light(c.mask(lambda p: p.ellipse(lx, top - 8, 30, 14), blur=4.0), LAMP, 0.5)
    # Books.
    for i, colour in enumerate(((150, 60, 60), (60, 90, 140), (180, 150, 80))):
        c.put(c.mask(box(lx - 40 + i * 2, top - 6 - i * 5, lx - 18 + i * 2, top - 1 - i * 5)), colour)


#: The heights the rooms place a walk on (world units from the frame's top
#: or its bottom). The numbers are the art's: change them with it.
COUNTER_H = 40
GALLERY_FLOOR = 90
PLATFORM_FLOOR = 60
#: How far across the platform's frame its stair reaches the platform.
STAIR_RUN = 0.55

#: Each piece: (width, height) in world units, and how it is drawn.
PIECES: Dict[str, Tuple[float, float, Callable]] = {
    "math_cafe_counter": (220, 112, cafe_counter),
    "math_cafe_menu": (130, 96, cafe_menu),
    "math_cafe_table": (80, 64, cafe_table),
    "math_cafe_shelf": (160, 48, cafe_shelf),
    "math_cafe_window": (96, 150, cafe_window),
    "math_cafe_lamps": (720, 140, cafe_lamps),
    "math_office_map": (320, 170, office_map),
    "math_office_drafting": (120, 90, office_drafting),
    "math_office_cabinet": (70, 120, office_cabinet),
    "math_office_theodolite": (60, 90, office_theodolite),
    "math_office_gallery": (380, 300, office_gallery),
    "math_obs_dome": (800, 260, obs_dome),
    "math_obs_telescope": (240, 300, obs_telescope),
    "math_obs_platform": (420, 260, obs_platform),
    "math_obs_chart": (140, 100, obs_chart),
    "math_obs_desk": (130, 70, obs_desk),
}

#: Room round each piece in the frame, so a stroke on its edge is not cut.
MARGIN = 6


def _frame_size(name: str) -> Tuple[int, int]:
    w, h, _ = PIECES[name]
    return (int((w + 2 * MARGIN) * PX), int((h + 2 * MARGIN) * PX))


def _draw(name: str) -> Image.Image:
    w, h, draw = PIECES[name]
    c = Canvas(name, w + 2 * MARGIN, h + 2 * MARGIN, origin=(-MARGIN, -MARGIN), ppu=PX)
    k = Kit(c, PAL, sun=-1)
    k.ground = h
    draw(c, k, w, h)
    return c.image()


def _renderer(name: str):
    def render_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
        del frame_idx, nframes
        if anim != "idle":
            raise ValueError(f"unknown animation: {anim}")
        return _draw(name)

    def frame_meta(anim: str, frame_idx: int, nframes: int) -> dict:
        del anim, frame_idx, nframes
        fw, fh = _frame_size(name)
        return {"anchors": {"foot": {"x": fw / 2, "y": float(fh - MARGIN * PX)}}, "forward": {"x": 0.0, "y": -1.0}, "angle_deg": 0.0}

    def render(out_dir: str | Path, **opts) -> List[Path]:
        del opts
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        outputs = build_sheet(
            target=name,
            rows=[("idle", 1, 400)],
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
    return {
        "actor": {"character_id": f"prop_{name}", "display_name": name.replace("_", " ").title()},
        "body": {"body_plan": "Prop", "body_kind": "Scenery", "mass_class": "Heavy", "locomotion_hint": "Static", "traits": ["prop", "furniture", "scenery"]},
        "brain": {"default_preset": "stand_still"},
        "actions": {"default_preset": "peaceful"},
        "animation_bindings": {"default": {"animation": "idle", "events": []}},
        "tags": ["prop", "furniture", "scenery"],
    }


TARGETS = {name: {"render": _renderer(name), "actor_metadata": _actor(name)} for name in PIECES}

__all__ = ["COUNTER_H", "GALLERY_FLOOR", "MARGIN", "PIECES", "PLATFORM_FLOOR", "PX", "TARGETS"]
