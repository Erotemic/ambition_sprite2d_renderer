"""Scenery of the Automaton dimension (gate address CELLS,
`docs/planning/game/automaton-dimension.md`).

The rooms are written by
`game/ambition_map_assets/ambition_content/generators/automaton/make_specs.py`.
Each piece is drawn in its room's coordinates (`_district_props`): where the
room places a walk line, the piece draws the light top edge of the thing
walked on at that y. The numbers here are the generator's; change them
together.

- The Works (floor y 640): the Escapement Cafe, its gear sign, its tables;
  the water wheel under its spout; the stair of blocks Busy Beaver is
  building (tops at y 576, 512, 448, 384); the clock tower, its gears in a
  skeleton face, its door the Tape Room's.
- The Life field (floor y 896, the east terrace y 448): the block, a still
  life, on its plinth; the Sierpinski panel on the terrace.
- The Tape Room (floor y 512): the tape between its two spools, with its
  ones lit; the rail the Head runs on; the table of states.
- The Cell-ular Arena (gallery y 448, ground y 768, ring top y 720): the
  ring's face, the four generations of rule 150 lit along it, and its corner
  posts; the failure log on the gallery, a row of cells for each challenger,
  each row ending in a red cell.

Also ``automaton_glider_lift``, the look of the glider lifts of the Life
field (`data/platform_looks.ron`): a slab of cubes whose front shows a
glider stepping through its four phases.

Nothing here is writing: the words of the rooms are their signs.

Animations: ``idle``, 1 frame each (the glider lift: 4).
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

from ..characters import _art_cast_kit as K
from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .art_props import _publisher

PAL = {
    "stone": (176, 160, 196), "stone_light": (214, 204, 230), "trim": (214, 170, 92), "dark": (40, 32, 52),
    "glass_top": (255, 230, 180), "glass_low": (90, 80, 120), "lamp": (255, 222, 150), "wood": (130, 86, 56),
    "leaf": (110, 150, 96), "iron": (60, 52, 80), "brass": (214, 170, 92), "glaze": (240, 200, 210),
}

STONE = (176, 160, 196)
STONE_LIGHT = (214, 204, 230)
STONE_DARK = (120, 106, 150)
BRASS = (214, 170, 92)
BRASS_LIGHT = (255, 226, 150)
BRASS_DARK = (150, 110, 60)
IRON = (60, 52, 80)
ROSE = (226, 150, 176)
CREAM = (248, 236, 228)
WOOD = (130, 86, 56)
WOOD_DARK = (84, 54, 38)
LAMP = (255, 222, 150)
WATER = (150, 214, 236)
FOAM = (236, 248, 255)
BLOCK = (150, 140, 186)
BLOCK_LIGHT = (196, 188, 226)
BLOCK_DARK = (96, 86, 130)
LIME = (184, 240, 60)
CUBE = (34, 34, 70)
CUBE_LIGHT = (70, 72, 120)
CELL = (120, 220, 255)
AMBER = (255, 184, 70)
STEEL = (90, 92, 108)
STEEL_LIGHT = (150, 152, 170)
TAPE = (232, 226, 210)
VIOLET = (108, 75, 176)

#: The Works.
FLOOR = 640
CAFE = (600, 980)
WHEEL = (1230, 470, 140)
#: The stair of blocks: each step's left and top; every step runs to STAIR_END.
STAIRS = ((1560, 576), (1624, 512), (1688, 448), (1752, 384))
STAIR_END = 1880
TOWER = (1960, 2240)
TOWER_DOOR_X = 2100
#: The Life field.
FIELD_FLOOR = 896
BLOCK_AT = (1180, 1290)
TERRACE = (2040, 448)
#: The Tape Room.
ROOM_FLOOR = 512
SPOOLS = ((150, 330), (1450, 330))
TAPE_Y = (306, 354)
TABLE = (1060, 110, 1420, 270)

#: The Cell-ular Arena.
GALLERY = (0, 448, 448)
ARENA_GROUND = 768
RING = (832, 1856, 720)
LOG = (160, 230, 360, 448)

#: The glider lift's sheet.
LIFT_FRAME = (160, 96)
LIFT_SPAN = (16.0, 144.0)
LIFT_TOP = 24.0
GLIDER_PHASES = (("010", "001", "111"), ("101", "011", "010"), ("001", "101", "011"), ("100", "011", "110"))


# ---------------------------------------------------------------------------
# Parts
# ---------------------------------------------------------------------------


def walk_top(c, x0, x1, y, colour):
    """The light top edge of a thing walked on, at `y`."""
    c.put(c.mask(box(x0, y, x1, y + 3)), mix(colour, (255, 255, 240), 0.5))


def gear(c, cx, cy, r, teeth, colour, hole=0.4, spokes=0):
    """A brass gear, its hub open, with `spokes` spokes if any."""
    pts = []
    for k in range(teeth * 4):
        a = math.tau * k / (teeth * 4)
        rr = r if (k % 4) in (0, 1) else r * 0.86
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    m = c.mask(lambda p: p.poly(pts))
    if spokes:
        inner = c.mask(lambda p: p.ellipse(cx, cy, r * 0.74, r * 0.74))
        arms = c.mask(lambda p: [p.line([(cx, cy), (cx + r * 0.8 * math.cos(math.tau * k / spokes), cy + r * 0.8 * math.sin(math.tau * k / spokes))], max(2.0, r * 0.1)) for k in range(spokes)])
        hub = c.mask(lambda p: p.ellipse(cx, cy, r * 0.2, r * 0.2))
        m = np.clip(m - inner + arms + hub, 0, 1)
    if hole > 0.0:
        m = m * (1.0 - c.mask(lambda p: p.ellipse(cx, cy, r * hole * (0.4 if spokes else 1.0), r * hole * (0.4 if spokes else 1.0))))
    c.put(m, colour)
    c.light(m * c.mask(lambda p: p.ellipse(cx - r * 0.3, cy - r * 0.3, r * 0.8, r * 0.8), blur=r * 0.3), mix(colour, (255, 255, 240), 0.5), 0.35)
    c.tone(m * np.clip((c.y - cy) / r, 0, 1), -0.2)
    return m


def cube(c, x0, y0, s, face, light, dark, cells=None, cell_colour=LIME):
    """A builder's cube seen from the front: its face, a light top edge, a
    dark side, and lit cells in it if any (a list of (col, row) of a 3 by 3)."""
    c.put(c.mask(box(x0, y0, x0 + s, y0 + s)), face)
    c.put(c.mask(box(x0, y0, x0 + s, y0 + 4)), light)
    c.put(c.mask(box(x0 + s - 6, y0 + 4, x0 + s, y0 + s)), dark)
    c.put(c.mask(lambda p: p.line([(x0, y0), (x0 + s, y0), (x0 + s, y0 + s), (x0, y0 + s), (x0, y0)], 1.4)), scale(dark, 0.6))
    if cells:
        q = (s - 16) / 3.0
        for col, row in cells:
            cx, cy = x0 + 6 + col * q, y0 + 8 + row * q
            m = c.mask(box(cx + 2, cy + 2, cx + q - 2, cy + q - 2))
            c.put(m, cell_colour)
            c.light(c.soften(m, 4.0), cell_colour, 0.35)


def pattern(c, rows, x0, y0, s, colour, gap=0.16, glow=0.4):
    """The live cells of `rows` (strings of '0'/'1'), top left at (x0, y0)."""
    inset = s * gap / 2.0
    m = c.mask(lambda p: [p.rect(x0 + j * s + inset, y0 + i * s + inset, x0 + (j + 1) * s - inset, y0 + (i + 1) * s - inset)
                          for i, row in enumerate(rows) for j, ch in enumerate(row) if ch == "1"])
    c.put(m, colour)
    if glow:
        c.light(c.soften(m, s * 0.4), colour, glow)
    return m


def sierpinski(n):
    """Rule 90 from one live cell: `n` rows of a Sierpinski triangle."""
    w = 2 * n - 1
    row = [0] * w
    row[n - 1] = 1
    out = []
    for _ in range(n):
        out.append("".join(str(x) for x in row))
        row = [(row[i - 1] if i > 0 else 0) ^ (row[i + 1] if i < w - 1 else 0) for i in range(w)]
    return out


# ---------------------------------------------------------------------------
# The Works
# ---------------------------------------------------------------------------


def cafe(c, k):
    """The Escapement Cafe: a front of lavender stone, a striped awning of
    rose and cream, a gear for its sign, lit windows, two tables out front."""
    x0, x1 = CAFE
    g = FLOOR
    k.wall(x0, 300, x1, g, STONE, tag="cafe")
    c.put(c.mask(box(x0 - 10, 288, x1 + 10, 304)), STONE_LIGHT)
    c.put(c.mask(box(x0 - 10, 300, x1 + 10, 304)), STONE_DARK)
    # The upper storey's round windows, a gear in each.
    for cx in (x0 + 90, (x0 + x1) / 2, x1 - 90):
        win = c.mask(lambda p: p.ellipse(cx, 360, 26, 26))
        c.put(win, IRON)
        c.paint(win, c.ramp([(334, mix(LAMP, (255, 255, 240), 0.3)), (386, scale(LAMP, 0.8))]), 0.8)
        gear(c, cx, 360, 18, 8, BRASS_DARK, hole=0.35)
    # The awning over the shop front.
    k.awning(x0 + 10, x1 - 10, 420, 34, (ROSE, CREAM))
    # The shop front: two wide windows lit warm, a door between them.
    for wx0, wx1 in ((x0 + 30, x0 + 150), (x1 - 150, x1 - 30)):
        pane = c.mask(box(wx0, 470, wx1, g - 40))
        c.put(c.mask(box(wx0 - 6, 464, wx1 + 6, g - 34)), WOOD_DARK)
        c.paint(pane, c.ramp([(470, mix(LAMP, (255, 255, 240), 0.4)), (g - 40, scale(LAMP, 0.75))]), 0.9)
        c.put(c.mask(lambda p: p.rect((wx0 + wx1) / 2 - 2, 470, (wx0 + wx1) / 2 + 2, g - 40)) * pane, WOOD_DARK)
        # Cups on a shelf in the window.
        c.put(c.mask(lambda p: [p.rect(x, g - 80, x + 10, g - 68) for x in np.arange(wx0 + 12, wx1 - 12, 22)]), CREAM)
        c.put(c.mask(box(wx0, g - 66, wx1, g - 62)), WOOD)
    k.ground = g
    k.door((x0 + x1) / 2, 60, 120, WOOD, arch=True, glass_lit=0.8)
    # The sign: a brass gear on a bracket over the door.
    bx = (x0 + x1) / 2
    c.put(c.mask(lambda p: p.line([(bx + 70, 300), (bx + 70, 280), (bx + 120, 280)], 4)), IRON)
    gear(c, bx + 120, 250, 26, 10, BRASS, hole=0.3)
    # Two tables and their chairs, a cup on each.
    for tx in (x0 - 0 + 40, x1 - 40):
        c.put(c.mask(lambda p: (p.ellipse(tx, g - 44, 30, 6), p.rect(tx - 3, g - 44, tx + 3, g), p.rect(tx - 14, g - 4, tx + 14, g))), IRON)
        c.put(c.mask(lambda p: p.ellipse(tx, g - 46, 30, 5)), CREAM)
        c.put(c.mask(lambda p: (p.rect(tx - 6, g - 58, tx + 4, g - 48), p.ring(tx + 6, g - 53, 3, 1.4))), ROSE)
        for side in (-1, 1):
            sx = tx + side * 44
            c.put(c.mask(lambda p: (p.rect(sx - 10, g - 34, sx + 10, g - 30), p.rect(sx - 10, g - 30, sx - 7, g), p.rect(sx + 7, g - 30, sx + 10, g),
                                    p.rect(sx + side * 7 - 2, g - 60, sx + side * 7 + 2, g - 30))), IRON)


def waterwheel(c, k):
    """The water wheel: a brass pipe brings water to a spout over it; the
    wheel turns in a stone trough."""
    cx, cy, r = WHEEL
    g = FLOOR
    # The frame that holds the axle.
    c.put(c.mask(lambda p: (p.poly([(cx - 90, g), (cx - 70, g), (cx + 6, cy), (cx - 6, cy)]), p.poly([(cx + 70, g), (cx + 90, g), (cx + 6, cy), (cx - 6, cy)]))), WOOD_DARK)
    # The wheel: a rim, spokes and paddles.
    rim = c.mask(lambda p: p.ring(cx, cy, r, 12))
    spokes = c.mask(lambda p: [p.line([(cx, cy), (cx + r * math.cos(math.tau * j / 12), cy + r * math.sin(math.tau * j / 12))], 6) for j in range(12)])
    c.put(np.clip(rim + spokes, 0, 1), WOOD)
    c.tone(np.clip(rim + spokes, 0, 1) * np.clip((c.y - cy) / r, 0, 1), -0.25)
    for j in range(16):
        a = math.tau * j / 16
        px, py = cx + (r + 4) * math.cos(a), cy + (r + 4) * math.sin(a)
        tx, ty = -math.sin(a), math.cos(a)
        c.put(c.mask(lambda p: p.poly([(px - 18 * math.cos(a) - 6 * tx, py - 18 * math.sin(a) - 6 * ty), (px + 10 * math.cos(a) - 6 * tx, py + 10 * math.sin(a) - 6 * ty),
                                         (px + 10 * math.cos(a) + 6 * tx, py + 10 * math.sin(a) + 6 * ty), (px - 18 * math.cos(a) + 6 * tx, py - 18 * math.sin(a) + 6 * ty)])), WOOD_DARK)
    gear(c, cx, cy, 34, 12, BRASS, hole=0.3)
    # The pipe from the east and its spout over the wheel.
    pipe = c.mask(lambda p: (p.rect(cx + 40, 266, 1420, 290), p.rect(cx + 20, 266, cx + 48, 310)))
    c.put(pipe, BRASS_DARK)
    c.light(pipe * c.mask(box(cx + 20, 266, 1420, 272)), BRASS_LIGHT, 0.6)
    for x in (cx + 90, cx + 150):
        c.put(c.mask(box(x, 262, x + 8, 294)), BRASS)
    # The water falling onto the paddles, and the foam where it lands.
    fall = c.mask(lambda p: p.poly([(cx + 24, 310), (cx + 44, 310), (cx + 52, cy - r + 30), (cx + 30, cy - r + 30)]), blur=1.0)
    c.put(fall, WATER, 0.85)
    c.light(fall * c.noise(("wheel", "fall"), 3, 30, 2), FOAM, 0.5)
    c.put(c.mask(lambda p: [p.ellipse(cx + 40 + dx, cy - r + 30, 10, 6) for dx in (-10, 0, 12)], blur=1.5), FOAM, 0.8)
    # The trough.
    trough = c.mask(box(cx - 180, g - 44, cx + 180, g))
    c.put(trough, STONE)
    c.put(c.mask(box(cx - 180, g - 44, cx + 180, g - 40)), STONE_LIGHT)
    c.put(c.mask(box(cx - 172, g - 40, cx + 172, g - 30)), WATER, 0.9)
    c.tone(trough * c.mask(box(cx - 180, g - 30, cx + 180, g)) * (c.noise(("trough", "stone"), 10, 3, 3) - 0.5), 0.2)


def block_stairs(c, k):
    """The stair of blocks Busy Beaver is building: cubes of 64, a cell
    pattern lit in each, the tops of the steps light; a loose block on the
    ground beside it."""
    tops = {}
    for x0, top in STAIRS:
        for x in range(x0, STAIR_END, 64):
            tops[x] = min(tops.get(x, FLOOR), top)
    patterns = (((0, 0), (1, 1), (2, 2)), ((1, 0), (1, 1), (1, 2)), ((0, 2), (1, 2), (2, 2), (2, 1), (1, 0)), ((0, 0), (2, 0), (1, 1), (0, 2), (2, 2)), ((1, 1),))
    n = 0
    for x, top in sorted(tops.items()):
        for y in range(top, FLOOR, 64):
            cube(c, x, y, 64, BLOCK, BLOCK_LIGHT, BLOCK_DARK, patterns[n % len(patterns)])
            n += 1
    for x0, top in STAIRS:
        walk_top(c, x0, STAIR_END, top, BLOCK_LIGHT)
    # The loose block, waiting, and a second set down beside it.
    cube(c, 1404, FLOOR - 64, 64, BLOCK, BLOCK_LIGHT, BLOCK_DARK, ((1, 1),))
    cube(c, 1440, FLOOR - 112, 48, BLOCK, BLOCK_LIGHT, BLOCK_DARK, ((0, 0), (2, 2)))


def clock_tower(c, k):
    """The clock tower: lavender stone, a skeleton clock face with its gears
    showing, a spire with a brass cell at the top, an arched door."""
    x0, x1 = TOWER
    cx = (x0 + x1) / 2
    g = FLOOR
    k.wall(x0, 150, x1, g, STONE, tag="tower")
    c.tone(c.mask(box(x1 - 30, 150, x1, g)), -0.18)
    for y in (150, 330):
        c.put(c.mask(box(x0 - 12, y - 10, x1 + 12, y + 4)), STONE_LIGHT)
    # The spire and its cell.
    spire = c.mask(lambda p: p.poly([(x0 - 6, 146), (x1 + 6, 146), (cx, 56)]))
    c.put(spire, VIOLET)
    c.light(spire * (c.x < cx), (200, 170, 240), 0.25)
    cell = c.mask(box(cx - 10, 40, cx + 10, 60))
    c.put(cell, LIME)
    c.light(c.soften(cell, 8), LIME, 0.5)
    # The skeleton clock: a brass ring, gears in it, two hands.
    fy = 240
    c.put(c.mask(lambda p: p.ellipse(cx, fy, 96, 96)), scale(STONE_DARK, 0.6))
    gear(c, cx - 30, fy + 20, 40, 12, BRASS_DARK, spokes=5)
    gear(c, cx + 36, fy - 26, 30, 10, BRASS, spokes=4)
    gear(c, cx + 30, fy + 44, 20, 8, BRASS_DARK, hole=0.3)
    c.put(c.mask(lambda p: p.ring(cx, fy, 92, 8)), BRASS)
    c.put(c.mask(lambda p: [p.rect(cx + 82 * math.cos(math.tau * j / 12) - 3, fy + 82 * math.sin(math.tau * j / 12) - 3,
                                   cx + 82 * math.cos(math.tau * j / 12) + 3, fy + 82 * math.sin(math.tau * j / 12) + 3) for j in range(12)]), BRASS_LIGHT)
    c.put(c.mask(lambda p: (p.line([(cx, fy), (cx + 50, fy - 30)], 5), p.line([(cx, fy), (cx - 12, fy - 70)], 3.5), p.ellipse(cx, fy, 7, 7))), IRON)
    # Windows up the shaft, and the door.
    for y in (380, 440):
        win = c.mask(lambda p: p.arch(cx - 14, y, cx + 14, y + 40))
        c.put(win, IRON)
        c.put(c.mask(lambda p: p.arch(cx - 10, y + 4, cx + 10, y + 40)), mix(LAMP, (255, 255, 240), 0.3), 0.8)
    k.ground = g
    k.door(TOWER_DOOR_X, 64, 110, VIOLET, arch=True, glass_lit=0.6)


# ---------------------------------------------------------------------------
# The Life field
# ---------------------------------------------------------------------------


def still_life(c, k):
    """The block: the smallest still life, two by two cells, on a plinth.
    Each of its cells has three live neighbours, so none of them dies."""
    x0, x1 = BLOCK_AT
    g = FIELD_FLOOR
    c.put(c.mask(box(x0, g - 24, x1, g)), CUBE_LIGHT)
    c.put(c.mask(box(x0, g - 24, x1, g - 21)), AMBER)
    s = (x1 - x0 - 10) / 2.0
    for i in range(2):
        for j in range(2):
            cx, cy = x0 + 5 + j * s, g - 24 - (2 - i) * s
            m = c.mask(box(cx + 3, cy + 3, cx + s - 3, cy + s - 3))
            c.put(m, CELL)
            c.put(c.mask(box(cx + 12, cy + 12, cx + s - 12, cy + s - 12)), scale(CUBE, 1.0))
            c.light(c.soften(m, 10), CELL, 0.4)


def sierpinski_panel(c, k):
    """A panel on two posts on the terrace: a Sierpinski triangle, rule 90
    run down from one live cell, lit on the dark."""
    x0, g = TERRACE
    px0, px1, py0, py1 = x0 + 30, x0 + 330, 90, 340
    for x in (px0 + 30, px1 - 30):
        c.put(c.mask(box(x - 5, py1, x + 5, g)), CUBE_LIGHT)
    panel = c.mask(box(px0, py0, px1, py1))
    c.put(panel, CUBE)
    c.put(c.mask(lambda p: p.line([(px0, py0), (px1, py0), (px1, py1), (px0, py1), (px0, py0)], 4)), AMBER)
    c.light(c.soften(c.mask(lambda p: p.line([(px0, py0), (px1, py0), (px1, py1), (px0, py1), (px0, py0)], 4)), 6), AMBER, 0.4)
    rows = sierpinski(32)
    s = (px1 - px0 - 24) / len(rows[0])
    pattern(c, rows, px0 + 12, py1 - 12 - len(rows) * s, s, CELL, gap=0.2, glow=0.25)


# ---------------------------------------------------------------------------
# The Tape Room
# ---------------------------------------------------------------------------


def tape(c, k):
    """The tape between its two spools along the wall: cells, the ones lit
    lime; the rail the Head runs on along the floor; a guide roller."""
    g = ROOM_FLOOR
    t0, t1 = TAPE_Y
    (ax, ay), (bx, by) = SPOOLS
    # Posts that hold the spools.
    for sx in (ax, bx):
        c.put(c.mask(lambda p: p.poly([(sx - 30, g), (sx - 18, g), (sx + 4, ay), (sx - 4, ay)])), STEEL)
        c.put(c.mask(lambda p: p.poly([(sx + 18, g), (sx + 30, g), (sx + 4, ay), (sx - 4, ay)])), STEEL)
    # The tape: cells of paper, a few ones lit.
    tape_m = c.mask(box(ax, t0, bx, t1))
    c.put(tape_m, TAPE)
    c.put(c.mask(box(ax, t0, bx, t0 + 3)), mix(TAPE, (255, 255, 255), 0.5))
    c.tone(c.mask(box(ax, t1 - 6, bx, t1)), -0.15)
    cell_w = 40
    ones = "0001101111011101111110111111111011000100"
    for j, x in enumerate(range(ax + 20, bx - 20, cell_w)):
        c.put(c.mask(box(x, t0, x + 2, t1)), scale(TAPE, 0.7))
        if ones[j % len(ones)] == "1":
            m = c.mask(box(x + 12, t0 + 12, x + cell_w - 10, t1 - 12))
            c.put(m, LIME)
            c.light(c.soften(m, 6), LIME, 0.3)
    # The spools: gears with the tape wound on them.
    for sx, sy in SPOOLS:
        c.put(c.mask(lambda p: p.ellipse(sx, sy, 64, 64)), TAPE)
        c.put(c.mask(lambda p: [p.ring(sx, sy, r, 1.0) for r in (40, 48, 56)]), scale(TAPE, 0.8))
        gear(c, sx, sy, 36, 12, BRASS, spokes=5)
    # The rail along the floor, its sleepers.
    c.put(c.mask(box(60, g - 14, 1540, g - 6)), STEEL_LIGHT)
    c.put(c.mask(lambda p: [p.rect(x, g - 6, x + 24, g) for x in range(70, 1530, 60)]), STEEL)


def state_table(c, k):
    """The table of states on the wall: a row for each of the five states,
    two entries a row (reading 0, reading 1); each entry a lit cell if it
    writes a one, an arrow of the way it moves, and the lamp of the next
    state."""
    x0, y0, x1, y1 = TABLE
    c.put(c.mask(box(x0, y0, x1, y1)), WOOD_DARK)
    c.put(c.mask(box(x0 + 8, y0 + 8, x1 - 8, y1 - 8)), (40, 34, 52))
    c.put(c.mask(lambda p: p.line([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], 3)), BRASS)
    lamps = (LIME, (120, 220, 255), AMBER, (226, 150, 176), (200, 170, 240))
    # The five-state champion's table (A..E), as (write, move, next): move
    # +1 right, -1 left; next -1 halts.
    table = (((1, 1, 1), (1, -1, 2)), ((1, 1, 2), (1, 1, 1)), ((1, 1, 3), (0, -1, 4)),
             ((1, -1, 0), (1, -1, 3)), ((1, 1, -1), (0, -1, 0)))
    rh = (y1 - y0 - 24) / 5.0
    for r, row in enumerate(table):
        y = y0 + 12 + r * rh + rh / 2
        c.put(c.mask(lambda p: p.ellipse(x0 + 30, y, 7, 7)), lamps[r])
        for col, (write, move, nxt) in enumerate(row):
            ex = x0 + 70 + col * 150
            m = c.mask(box(ex, y - 8, ex + 16, y + 8))
            c.put(m, LIME if write else (70, 66, 84))
            ax = ex + 40
            c.put(c.mask(lambda p: p.poly([(ax + 14 * move, y), (ax - 6 * move, y - 8), (ax - 6 * move, y + 8)])), CREAM)
            if nxt >= 0:
                c.put(c.mask(lambda p: p.ellipse(ex + 84, y, 7, 7)), lamps[nxt])
            else:
                c.put(c.mask(box(ex + 77, y - 7, ex + 91, y + 7)), (220, 80, 70))


# ---------------------------------------------------------------------------
# The Cell-ular Arena
# ---------------------------------------------------------------------------


def rule150_cycle():
    """Rule 150 (each cell the XOR of itself and its two neighbours) on a ring
    of sixteen, from two live cells eight apart: it comes back in four
    generations. The PCA's fight music is written from the same rows."""
    row = [1 if i in (0, 8) else 0 for i in range(16)]
    rows = []
    for _ in range(4):
        rows.append(row)
        row = [row[i - 1] ^ row[i] ^ row[(i + 1) % 16] for i in range(16)]
    assert row == rows[0]
    return rows


def arena_ring(c, k):
    """The ring's face: dark cubes, an amber lip, the four generations of
    rule 150 lit along the front; a post of cubes at each corner with a lit
    cube on top."""
    x0, x1, top = RING
    g = ARENA_GROUND
    face = c.mask(box(x0, top, x1, g))
    c.put(face, CUBE)
    c.put(c.mask(lambda p: [p.rect(x, top + 4, x + 1.5, g) for x in range(x0, x1, 16)]), CUBE_LIGHT)
    c.put(c.mask(box(x0, top, x1, top + 4)), AMBER)
    c.light(c.soften(c.mask(box(x0, top, x1, top + 4)), 6), AMBER, 0.35)
    rows = rule150_cycle()
    seg = (x1 - x0 - 64) / 4.0
    s = (seg - 24) / 16.0
    for n, row in enumerate(rows):
        pattern(c, ["".join(str(v) for v in row)], x0 + 32 + n * seg + 12, top + 16, s, CELL, gap=0.25, glow=0.3)
    for px in (x0 - 8, x1 - 24):
        for j in range(4):
            cube(c, px, top - 32 * (j + 1), 32, CUBE_LIGHT, mix(CUBE_LIGHT, (255, 255, 255), 0.25), CUBE)
        m = c.mask(box(px + 6, top - 150, px + 26, top - 130))
        c.put(m, CELL)
        c.light(c.soften(m, 14), CELL, 0.6)


def failure_log(c, k):
    """The failure log: a dark board on two posts, a row of dim cells for
    each challenger (a name in the rule's own writing), each ending in a red
    cell; the last row empty, its first cell lit, waiting."""
    x0, y0, x1, g = LOG
    for x in (x0 + 24, x1 - 24):
        c.put(c.mask(box(x - 5, y0, x + 5, g)), CUBE_LIGHT)
    y1 = y0 + 160
    c.put(c.mask(box(x0, y0, x1, y1)), CUBE)
    edge = c.mask(lambda p: p.line([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], 3))
    c.put(edge, AMBER)
    rng = np.random.default_rng(65)
    rows = 8
    rh = (y1 - y0 - 24) / rows
    cs = 9.0
    for r in range(rows):
        y = y0 + 12 + r * rh + (rh - cs) / 2
        if r == rows - 1:
            m = c.mask(box(x0 + 14, y, x0 + 14 + cs, y + cs))
            c.put(m, CELL)
            c.light(c.soften(m, 6), CELL, 0.5)
            continue
        n = int(rng.integers(6, 14))
        bits = rng.integers(0, 2, n)
        c.put(c.mask(lambda p: [p.rect(x0 + 14 + j * (cs + 2), y, x0 + 14 + j * (cs + 2) + cs, y + cs) for j in range(n) if bits[j]]),
              mix(CELL, CUBE, 0.45))
        xr = x1 - 14 - cs
        m = c.mask(box(xr, y, xr + cs, y + cs))
        c.put(m, (230, 70, 70))
        c.light(c.soften(m, 5), (230, 70, 70), 0.4)


#: Every piece: its frame in its room, and how it is drawn.
PIECES: Dict[str, Piece] = {
    # The Works.
    "automaton_cafe": Piece((560, 200, 1020, 640), cafe),
    "automaton_waterwheel": Piece((1040, 250, 1420, 640), waterwheel),
    "automaton_block_stairs": Piece((1396, 376, 1888, 640), block_stairs),
    "automaton_clock_tower": Piece((1940, 30, 2260, 640), clock_tower),
    # The Life field.
    "automaton_still_life": Piece((1170, 760, 1300, 896), still_life),
    "automaton_sierpinski_panel": Piece((2060, 120, 2380, 448), sierpinski_panel),
    # The Tape Room.
    "automaton_tape": Piece((60, 250, 1540, 512), tape),
    "automaton_state_table": Piece((1050, 100, 1430, 280), state_table),
    # The Cell-ular Arena.
    "automaton_arena_ring": Piece((816, 560, 1872, 768), arena_ring),
    "automaton_failure_log": Piece((150, 220, 370, 448), failure_log),
}

TARGETS = targets(PIECES, PAL)


def _draw_glider_lift(i: int):
    """The glider lift: a slab of dark cubes, its top edge amber, and on its
    front a glider in phase `i`."""
    f = K.Frame(LIFT_FRAME)
    x0, x1 = LIFT_SPAN
    top = LIFT_TOP
    f.poly([(x0, top), (x1, top), (x1, top + 44.0), (x0, top + 44.0)], CUBE + (255,))
    for x in np.arange(x0, x1, 16.0):
        f.ink([(x, top + 2.0), (x, top + 44.0)], 0.8, CUBE_LIGHT + (255,))
    f.poly([(x0, top), (x1, top), (x1, top + 4.0), (x0, top + 4.0)], AMBER + (255,), body=False)
    s = 12.0
    gx, gy = (x0 + x1) / 2.0 - 1.5 * s, top + 6.0
    for r, row in enumerate(GLIDER_PHASES[i % 4]):
        for col, ch in enumerate(row):
            if ch == "1":
                cx, cy = gx + col * s, gy + r * s
                f.poly([(cx + 1.5, cy + 1.5), (cx + s - 1.5, cy + 1.5), (cx + s - 1.5, cy + s - 1.5), (cx + 1.5, cy + s - 1.5)], CELL + (255,), body=False)
                f.glow(cx + s / 2, cy + s / 2, s * 0.6, CELL + (90,))
    return f.finish(outline=CUBE + (255,), width=1.0, glow_blur=2.0)


TARGETS["automaton_glider_lift"] = _publisher(
    "automaton_glider_lift", "Glider Lift", [("idle", 4, 220)], LIFT_FRAME, lambda anim, i, n: _draw_glider_lift(i),
    {"top": ((LIFT_SPAN[0] + LIFT_SPAN[1]) / 2.0, LIFT_TOP)}, "Scenery", ["prop", "platform", "automaton"])

__all__ = ["PAL", "PIECES", "TARGETS"]
