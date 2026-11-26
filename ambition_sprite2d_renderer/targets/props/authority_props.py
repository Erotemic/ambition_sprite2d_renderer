"""Scenery of the Central Hub, the Gate Authority's capital (gate address
LICENSED, `docs/planning/game/central-hub-dimension.md`).

The rooms are written by
`game/ambition_map_assets/ambition_content/generators/authority/make_specs.py`.
Each piece is drawn in its room's coordinates (`_district_props`): where the
room places a walk line (the catwalk, a stair, the balcony, the planter),
the piece draws the light top edge of the thing walked on at that y. The
numbers here are the generator's; change them together.

- The Concourse (floor y 640, the baggage hall's floor y 1024): the
  information booth; the catwalk (y 512) and its freight; the stairwell
  (the grate at y 640, steps at 768, 832, 896, 960); the baggage hall: the
  conveyor (y 984), the claw, the carts, Lost Baggage.
- Authority Plaza (floor y 640): the clock arcade, its balcony (y 448) and
  steps (y 512, 576); the blossom tree on its planter (y 576), the benches
  (y 604), a bough (y 448), the lamp posts; the notice board; the Manifest
  Office's portico.
- The Manifest Office (floor y 640): the take-a-number machine, the board,
  the chairs (y 604), the counter; the filing cabinets (y 512, 384).

The Authority's sign is the gate's apex: a gold triangle, point up, on navy.
Nothing here is writing: the words of the rooms are their signs.

Animations: ``idle``, 1 frame each.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale

PAL = {
    "stone": (214, 206, 220), "stone_light": (240, 234, 244), "trim": (226, 184, 92), "dark": (24, 26, 40),
    "glass_top": (170, 214, 250), "glass_low": (60, 80, 120), "lamp": (255, 222, 160), "wood": (120, 80, 56),
    "leaf": (90, 140, 90), "iron": (40, 46, 70), "brass": (226, 184, 92), "glaze": (230, 200, 150),
}

STONE = (214, 206, 220)
STONE_LIGHT = (240, 234, 244)
STONE_DARK = (140, 132, 160)
NAVY = (40, 50, 96)
NAVY_LIGHT = (80, 96, 160)
GOLD = (226, 184, 92)
GOLD_LIGHT = (255, 226, 150)
STEEL = (70, 84, 120)
STEEL_LIGHT = (120, 136, 176)
STEEL_DARK = (36, 44, 70)
IRON = (40, 46, 70)
GLASS = (170, 214, 250)
LAMP = (255, 222, 160)
WOOD = (130, 86, 56)
WOOD_DARK = (80, 50, 34)
CRATE = (170, 120, 70)
MAROON = (118, 40, 62)
BLOSSOM = (246, 170, 206)
BLOSSOM_LIGHT = (255, 210, 230)
BLOSSOM_DARK = (200, 110, 160)
BARK = (110, 70, 50)
LEAF = (90, 140, 90)
PAPER = (240, 234, 220)
SCREEN = (30, 40, 70)
SCREEN_LIGHT = (120, 230, 255)
RED = (200, 60, 60)

#: The Concourse.
FLOOR = 640
HALL_FLOOR = 1024
CATWALK = (960, 1720, 512)
STAIR_GAP = (1800, 2140)
STEPS = ((2040, 2140, 768), (1940, 2040, 832), (1840, 1940, 896), (1740, 1840, 960))
CONVEYOR = (300, 1120, 984)
#: Authority Plaza.
BALCONY = (16, 520, 448)
PLAZA_STEPS = ((520, 600, 512), (600, 680, 576))
CLOCK_WALK = (512, 1056, 448)
PLANTER = (1040, 1360, 576)
BENCHES = ((940, 1040, 604), (1360, 1460, 604))
BOUGH = (1120, 1280, 448)
GARDEN_PERCH = (1280, 1392, 512)
#: The Manifest Office.
CHAIRS = (420, 820, 604)
CABINETS = ((1240, 1400, 512), (1400, 1584, 384))


# ---------------------------------------------------------------------------
# Parts
# ---------------------------------------------------------------------------


def walk_top(c, x0, x1, y, colour):
    """The light top edge of a thing walked on, at `y`."""
    c.put(c.mask(box(x0, y, x1, y + 3)), mix(colour, (255, 255, 240), 0.5))


def sign_mark(c, cx, cy, r, colour=GOLD):
    """The Authority's sign: a triangle point up, open."""
    pts = [(cx + r * math.cos(math.radians(a)), cy - r * math.sin(math.radians(a))) for a in (90.0, 210.0, 330.0)]
    c.put(c.mask(lambda p: p.line(pts + [pts[0]], max(1.5, r * 0.28))), colour)


def banner(c, x, top, bottom, w, colour=NAVY):
    c.put(c.mask(box(x - w * 0.7, top - 4, x + w * 0.7, top)), GOLD)
    c.put(c.mask(lambda p: p.poly([(x - w / 2, top), (x + w / 2, top), (x + w / 2, bottom), (x, bottom - w * 0.5), (x - w / 2, bottom)])), colour)
    c.tone(c.mask(box(x, top, x + w / 2, bottom)), -0.12)
    sign_mark(c, x, top + (bottom - top) * 0.36, w * 0.3)


def lamp_post(c, x, foot, h):
    """A black lamp post with a lantern lit warm."""
    c.put(c.mask(lambda p: (p.rect(x - 3, foot - h, x + 3, foot), p.rect(x - 7, foot - 10, x + 7, foot), p.rect(x - 5, foot - 22, x + 5, foot - 10))), IRON)
    lantern = c.mask(lambda p: p.poly([(x - 10, foot - h - 30), (x + 10, foot - h - 30), (x + 7, foot - h), (x - 7, foot - h)]))
    c.put(lantern, IRON)
    c.put(c.mask(lambda p: p.poly([(x - 7, foot - h - 26), (x + 7, foot - h - 26), (x + 5, foot - h - 4), (x - 5, foot - h - 4)])), mix(LAMP, (255, 255, 240), 0.4))
    c.put(c.mask(lambda p: p.poly([(x - 12, foot - h - 30), (x + 12, foot - h - 30), (x, foot - h - 42)])), IRON)
    c.light(c.mask(lambda p: p.ellipse(x, foot - h - 15, 40, 40), blur=16), LAMP, 0.35)


def crate(c, x0, y1, w, h):
    m = c.mask(box(x0, y1 - h, x0 + w, y1))
    c.put(m, CRATE)
    c.tone(c.mask(box(x0 + w * 0.6, y1 - h, x0 + w, y1)), -0.15)
    c.put(c.mask(lambda p: (p.rect(x0, y1 - h, x0 + w, y1 - h + 4), p.rect(x0, y1 - 4, x0 + w, y1), p.line([(x0 + 3, y1 - 4), (x0 + w - 3, y1 - h + 4)], 3))), scale(CRATE, 0.65))


def suitcase(c, x, y1, w, h, colour):
    c.put(c.mask(lambda p: (p.rect(x, y1 - h, x + w, y1), p.rect(x + w * 0.35, y1 - h - 6, x + w * 0.65, y1 - h))), colour)
    c.put(c.mask(lambda p: p.rect(x + w * 0.4, y1 - h - 4, x + w * 0.6, y1 - h)), (0, 0, 0), 0.0)
    c.tone(c.mask(box(x, y1 - h * 0.25, x + w, y1)), -0.18)
    c.put(c.mask(lambda p: [p.rect(xx, y1 - h, xx + 2, y1) for xx in (x + w * 0.22, x + w * 0.74)]), scale(colour, 0.6))


def cart(c, x0, foot, w):
    """A baggage cart: a grey tub on wheels, boxes in it."""
    c.put(c.mask(box(x0, foot - 52, x0 + w, foot - 12)), (150, 156, 170))
    c.tone(c.mask(box(x0, foot - 24, x0 + w, foot - 12)), -0.2)
    c.put(c.mask(box(x0 + w * 0.3, foot - 44, x0 + w * 0.7, foot - 36)), SCREEN_LIGHT, 0.8)
    for wx in (x0 + 12, x0 + w - 12):
        c.put(c.mask(lambda p: p.ellipse(wx, foot - 8, 8, 8)), IRON)
        c.put(c.mask(lambda p: p.ellipse(wx, foot - 8, 3, 3)), STEEL_LIGHT)
    crate(c, x0 + 10, foot - 52, 34, 24)
    crate(c, x0 + 48, foot - 52, 26, 18)


# ---------------------------------------------------------------------------
# The Concourse
# ---------------------------------------------------------------------------


def info_booth(c, k):
    """The information booth: a round kiosk of glass under a blue dome with
    a gold lamp on top, a wooden counter and a screen in it."""
    x0, x1, g = 640, 880, FLOOR
    cx = (x0 + x1) / 2
    # The counter and the glass.
    glass = c.mask(box(x0 + 10, 520, x1 - 10, g - 60))
    c.paint(glass, c.ramp([(520, GLASS), (g - 60, mix(GLASS, (255, 240, 210), 0.5))]), 0.55)
    c.put(c.mask(lambda p: [p.rect(x, 520, x + 4, g - 60) for x in (x0 + 10, cx - 2, x1 - 14)]), NAVY)
    c.put(c.mask(box(x0, g - 64, x1, g)), WOOD)
    c.put(c.mask(box(x0 - 6, g - 68, x1 + 6, g - 60)), mix(WOOD, (255, 240, 210), 0.3))
    c.put(c.mask(lambda p: [p.rect(x, g - 56, x + 50, g - 8) for x in (x0 + 16, x1 - 66)]), WOOD_DARK, 0.5)
    # The screen on the counter.
    c.put(c.mask(box(cx + 30, g - 100, cx + 70, g - 72)), SCREEN)
    c.put(c.mask(box(cx + 34, g - 96, cx + 66, g - 76)), SCREEN_LIGHT, 0.7)
    c.put(c.mask(box(cx + 46, g - 72, cx + 54, g - 68)), IRON)
    # The dome: navy with gold ribs and a gold rim.
    dome = c.mask(lambda p: (p.ellipse(cx, 520, (x1 - x0) / 2 + 10, 64), p.rect(x0 - 10, 504, x1 + 10, 520)))
    dome = dome * (c.y < 522)
    c.put(dome, NAVY)
    c.light(dome * np.clip((520 - c.y) / 64, 0, 1) * (c.x < cx), NAVY_LIGHT, 0.35)
    for dx in (-80, -40, 0, 40, 80):
        c.put(c.mask(lambda p: p.line([(cx + dx * 1.4, 520), (cx + dx * 0.5, 470), (cx, 456)], 3)) * dome, GOLD, 0.8)
    c.put(c.mask(box(x0 - 14, 516, x1 + 14, 526)), GOLD)
    c.put(c.mask(lambda p: (p.rect(cx - 4, 430, cx + 4, 458), p.ellipse(cx, 426, 12, 12))), GOLD)
    c.light(c.mask(lambda p: p.ellipse(cx, 426, 30, 30), blur=12), LAMP, 0.5)
    # A lamp inside, over the counter.
    c.light(c.mask(lambda p: p.ellipse(cx, 560, 60, 40), blur=20), LAMP, 0.35)


def catwalk(c, k):
    """The catwalk over the Concourse (y 512): a steel truss on two
    columns, a brass rail, crates of freight and a lit crate on it."""
    x0, x1, top = CATWALK
    for cx in (x0 + 40, x1 - 40):
        col = c.mask(box(cx - 14, top + 40, cx + 14, FLOOR))
        c.put(col, STEEL)
        c.tone(c.mask(box(cx + 4, top + 40, cx + 14, FLOOR)), -0.2)
        c.put(c.mask(lambda p: [p.rect(cx - 18, y, cx + 18, y + 8) for y in (top + 40, FLOOR - 16)]), GOLD)
        c.light(c.mask(lambda p: p.ellipse(cx, top + 64, 6, 6)), LAMP, 0.8)
        c.light(c.mask(lambda p: p.ellipse(cx, top + 70, 30, 24), blur=10), LAMP, 0.3)
    body = c.mask(box(x0, top, x1, top + 40))
    c.put(body, STEEL_DARK)
    c.put(c.mask(lambda p: [p.line([(x, top + 6), (x + 20, top + 34), (x + 40, top + 6)], 3) for x in np.arange(x0, x1 - 20, 40)]), STEEL)
    c.put(c.mask(box(x0, top + 34, x1, top + 40)), STEEL)
    walk_top(c, x0, x1, top, STEEL_LIGHT)
    # The brass rail.
    c.put(c.mask(lambda p: ([p.rect(x, top - 34, x + 3, top) for x in np.arange(x0 + 4, x1, 48)], p.rect(x0, top - 36, x1, top - 32))), GOLD, 0.9)
    # Freight on it.
    crate(c, x0 + 420, top, 60, 56)
    crate(c, x0 + 486, top, 48, 40)
    crate(c, x0 + 440, top - 56, 40, 34)
    m = c.mask(box(x0 + 560, top - 44, x0 + 620, top))
    c.put(m, STEEL)
    c.put(c.mask(box(x0 + 574, top - 34, x0 + 606, top - 22)), SCREEN_LIGHT)
    c.light(c.mask(lambda p: p.ellipse(x0 + 590, top - 28, 24, 16), blur=8), SCREEN_LIGHT, 0.4)


def stairwell(c, k):
    """The stairwell down to the baggage hall: a grate over it in the
    Concourse's floor (y 640), steps of steel down (y 768, 832, 896, 960),
    a brass rail along them."""
    g0, g1 = STAIR_GAP
    grate = c.mask(box(g0, FLOOR, g1, FLOOR + 10))
    c.put(grate, STEEL_DARK)
    c.put(c.mask(lambda p: [p.rect(x, FLOOR + 2, x + 4, FLOOR + 10) for x in np.arange(g0 + 4, g1, 10)]), STEEL_LIGHT, 0.6)
    walk_top(c, g0, g1, FLOOR, STEEL_LIGHT)
    for x0, x1, top in STEPS:
        step = c.mask(box(x0, top, x1, top + 18))
        c.put(step, STEEL)
        c.put(c.mask(box(x0, top + 14, x1, top + 18)), STEEL_DARK)
        walk_top(c, x0, x1, top, STEEL_LIGHT)
        c.put(c.mask(box(x0 + 4, top + 18, x0 + 10, HALL_FLOOR)), STEEL_DARK, 0.7)
    # The rail, along the steps' nosings.
    pts = [(x1 - 4, top - 34) for x0, x1, top in STEPS] + [(STEPS[-1][0] + 4, STEPS[-1][2] - 34)]
    c.put(c.mask(lambda p: p.line(pts, 3)), GOLD)
    c.put(c.mask(lambda p: [p.rect(x1 - 6, top - 34, x1 - 3, top) for x0, x1, top in STEPS]), GOLD, 0.9)
    c.light(c.mask(lambda p: p.ellipse((g0 + g1) / 2, FLOOR + 40, 120, 40), blur=16), LAMP, 0.2)


def baggage_lift_shaft(c, _kit):
    """Draw the lift rails and the grate at the upper stop."""
    c.put(c.mask(box(1120, 644, 1280, 1008)), NAVY, 0.84)
    for x in (1120, 1272):
        c.put(c.mask(box(x, 616, x + 8, 1008)), STEEL_DARK)
        c.put(c.mask(box(x + 2, 616, x + 4, 1008)), STEEL_LIGHT)
        c.put(c.mask(lambda p: [p.rect(x - 4, y, x + 12, y + 4) for y in range(640, 1008, 64)]), GOLD)
    c.put(c.mask(box(1120, FLOOR, 1280, FLOOR + 10)), STEEL_DARK)
    c.put(c.mask(lambda p: [p.rect(x, FLOOR + 2, x + 3, FLOOR + 10) for x in range(1124, 1280, 10)]), STEEL_LIGHT)
    walk_top(c, 1120, 1280, FLOOR, STEEL_LIGHT)
    c.put(c.mask(box(1172, 598, 1228, 625)), IRON)
    c.put(c.mask(lambda p: p.poly([(1187, 614), (1200, 602), (1213, 614), (1204, 614), (1204, 621), (1196, 621), (1196, 614)])), GOLD_LIGHT)


def baggage_lift(c, _kit):
    """Draw the lift car with the walking surface at y 20."""
    c.put(c.mask(box(12, 20, 164, 40)), STEEL_DARK)
    walk_top(c, 12, 164, 20, STEEL_LIGHT)
    c.put(c.mask(box(15, 30, 161, 33)), GOLD)
    c.put(c.mask(lambda p: [
        p.poly([(x, 39), (x + 12, 39), (x + 8, 46), (x + 4, 46)])
        for x in (18, 146)
    ]), STEEL)
    c.put(c.mask(box(70, 34, 106, 38)), SCREEN_LIGHT)


def _baggage_wall(x0, x1):
    """The baggage hall's back wall from `x0` to `x1`, under the Concourse's
    floor: steel-blue panels in arched bays. The hall is wider than one
    page, so the wall is two pieces, west and east."""

    def draw(c, k):
        top, g = FLOOR + 64, HALL_FLOOR
        part = c.mask(box(x0, top, x1, g))
        c.put(part, (52, 60, 88))
        for x in np.arange(40, 2384, 360):
            bay = c.mask(lambda p: p.arch(x, top + 40, x + 300, g)) * part
            c.put(bay, (40, 46, 70))
            c.put(c.mask(lambda p: [p.rect(x + 20, y, x + 280, y + 3) for y in np.arange(top + 200, g, 40)]) * bay, (60, 70, 100), 0.6)
        c.tone(c.mask(box(x0, top, x1, top + 30)), -0.25)

    return draw


def baggage_hall(c, k):
    """The baggage hall under the Concourse: lamps under the floor, the
    conveyor (its top y 984) with bags from every dimension on it, the
    claw over it, carts west, and Lost Baggage east: a counter and shelves
    of things no one came back for."""
    top, g = FLOOR + 64, HALL_FLOOR
    # Lamps under the Concourse's floor.
    for x in (200, 560, 920, 1280, 1600):
        c.put(c.mask(lambda p: p.poly([(x - 20, top), (x + 20, top), (x + 12, top + 10), (x - 12, top + 10)])), STEEL_DARK)
        c.light(c.mask(lambda p: p.ellipse(x, top + 10, 6, 3)), LAMP, 0.9)
        c.light(c.mask(lambda p: p.ellipse(x, top + 60, 90, 60), blur=20), LAMP, 0.2)
    # The arches of the vault between the lamps.
    c.put(c.mask(lambda p: [p.rect(x - 12, top, x + 12, g) for x in (380, 1100)]), STEEL_DARK, 0.8)
    # The conveyor.
    x0, x1, belt = CONVEYOR
    c.put(c.mask(box(x0, belt, x1, g)), STEEL_DARK)
    c.put(c.mask(box(x0, belt, x1, belt + 10)), (50, 54, 70))
    walk_top(c, x0, x1, belt, STEEL_LIGHT)
    c.put(c.mask(lambda p: [p.ellipse(x, belt + 22, 7, 7) for x in np.arange(x0 + 16, x1, 32)]), (150, 140, 100))
    c.put(c.mask(lambda p: [p.ellipse(x, belt + 22, 2.5, 2.5) for x in np.arange(x0 + 16, x1, 32)]), IRON)
    bags = ((420, 50, 32, MAROON), (560, 40, 40, (70, 90, 150)), (700, 56, 30, (200, 160, 70)),
            (980, 44, 36, (90, 130, 90)), (1080, 60, 28, (60, 60, 70)))
    for bx, bw, bh, colour in bags:
        suitcase(c, bx, belt, bw, bh, colour)
    # A bag that went through the Primeval gate: it is a nest now, an egg in it.
    nx = 840
    c.put(c.mask(lambda p: p.ellipse(nx, belt - 12, 34, 14)), (130, 100, 60))
    c.put(c.mask(lambda p: [p.line([(nx - 34 + i * 7, belt - 6), (nx - 26 + i * 7, belt - 22)], 2) for i in range(10)]), (100, 76, 44))
    c.put(c.mask(lambda p: p.ellipse(nx + 4, belt - 26, 12, 15)), (240, 232, 210))
    c.put(c.mask(lambda p: [p.ellipse(nx + dx, belt - 26 + dy, 2.2) for dx, dy in ((-3, -6), (6, 2), (0, 6))]), (130, 160, 110))
    # The claw on its arm from the ceiling.
    cx = 800
    c.put(c.mask(lambda p: (p.rect(600, top, 1000, top + 10), p.rect(cx - 6, top + 10, cx + 6, top + 70), p.line([(cx, top + 70), (cx + 40, top + 110), (cx + 20, top + 150)], 10))), GOLD)
    c.put(c.mask(lambda p: (p.ellipse(cx, top + 70, 10, 10), p.ellipse(cx + 40, top + 110, 9, 9))), STEEL)
    jaw = (cx + 20, top + 150)
    c.put(c.mask(lambda p: (p.line([jaw, (jaw[0] - 16, jaw[1] + 14), (jaw[0] - 10, jaw[1] + 28)], 4), p.line([jaw, (jaw[0] + 16, jaw[1] + 14), (jaw[0] + 10, jaw[1] + 28)], 4))), STEEL_DARK)
    # The carts, west.
    cart(c, 40, g, 110)
    cart(c, 160, g, 110)
    # Lost Baggage, east: a counter, shelves behind it of odd things.
    lx0, lx1 = 1300, 1580
    c.put(c.mask(box(lx0, top + 60, lx1, g - 70)), (60, 66, 92))
    for y in (top + 100, top + 150, top + 200):
        c.put(c.mask(box(lx0 + 8, y, lx1 - 8, y + 6)), WOOD)
    # On the shelves: a pirate's hat, a noodle in a jar, an umbrella, a
    # lantern, a sword in its scabbard, a bag that is (now) a cloud.
    sy = top + 100
    c.put(c.mask(lambda p: (p.poly([(1320, sy), (1376, sy), (1366, sy - 22), (1348, sy - 30), (1330, sy - 22)]))), (30, 30, 36))
    sign_mark(c, 1348, sy - 14, 5, (240, 240, 230))
    c.put(c.mask(lambda p: p.rect(1400, sy - 34, 1428, sy)), GLASS, 0.6)
    c.put(c.mask(lambda p: p.line([(1404, sy - 6), (1414, sy - 26), (1424, sy - 8)], 3)), (240, 210, 120))
    c.put(c.mask(lambda p: (p.poly([(1450, sy - 30), (1490, sy - 30), (1470, sy - 44)]), p.rect(1469, sy - 30, 1471, sy))), MAROON)
    sy = top + 150
    c.put(c.mask(lambda p: (p.rect(1330, sy - 30, 1350, sy), p.ellipse(1340, sy - 32, 12, 6))), (120, 110, 70))
    c.light(c.mask(lambda p: p.ellipse(1340, sy - 16, 16, 16), blur=6), LAMP, 0.5)
    c.put(c.mask(lambda p: p.line([(1380, sy - 4), (1470, sy - 28)], 5)), (60, 50, 40))
    c.put(c.mask(lambda p: p.line([(1462, sy - 26), (1500, sy - 36)], 3)), STEEL_LIGHT)
    c.put(c.mask(lambda p: (p.ellipse(1530, sy - 20, 18, 12), p.ellipse(1516, sy - 18, 12, 10), p.ellipse(1546, sy - 16, 12, 9))), (250, 250, 255))
    sy = top + 200
    suitcase(c, 1330, sy, 40, 30, (160, 70, 140))
    suitcase(c, 1390, sy, 34, 26, (70, 140, 140))
    crate(c, 1450, sy, 40, 34)
    # The counter, its bell.
    c.put(c.mask(box(lx0 - 10, g - 70, lx1 + 10, g)), WOOD)
    c.put(c.mask(box(lx0 - 14, g - 74, lx1 + 14, g - 66)), mix(WOOD, (255, 240, 210), 0.3))
    c.put(c.mask(lambda p: (p.ellipse(lx0 + 40, g - 80, 10, 8), p.rect(lx0 + 28, g - 78, lx0 + 52, g - 74))), GOLD)


# ---------------------------------------------------------------------------
# Authority Plaza
# ---------------------------------------------------------------------------


def clock_arcade(c, k):
    """The arcade at the west of the plaza: a round arch on two pillars,
    the great clock in it, the balcony (y 448) under the clock and the
    steps up to it (y 512, 576); a bookstall under the balcony with its
    striped awning."""
    b0, b1, top = BALCONY
    # The arch and its pillars.
    for x0, foot in ((b0, FLOOR), (b1 - 50, top)):
        c.put(c.mask(box(x0, 160, x0 + 50, foot)), STONE)
        c.tone(c.mask(box(x0 + 32, 160, x0 + 50, foot)), -0.15)
    ax = (b0 + b1) / 2
    arch = c.mask(lambda p: p.ellipse(ax, 300, (b1 - b0) / 2, 150)) * (c.y < 300) - c.mask(lambda p: p.ellipse(ax, 300, (b1 - b0) / 2 - 50, 114)) * (c.y < 300)
    arch = np.clip(arch, 0, 1)
    c.put(arch, STONE)
    c.light(arch * c.mask(lambda p: p.ellipse(ax - 120, 200, 160, 120), blur=30), STONE_LIGHT, 0.3)
    c.put(c.mask(box(b0, 296, b1, 310)), STONE_DARK)
    # The vault in shadow, warm light from the clock.
    vault = c.mask(lambda p: (p.ellipse(ax, 300, (b1 - b0) / 2 - 50, 114), p.rect(b0 + 50, 300, b1 - 50, top))) * (c.y > 176)
    c.put(vault, (90, 70, 70), 0.55)
    c.light(c.mask(lambda p: p.ellipse(ax, 320, 180, 140), blur=30), LAMP, 0.35)
    # The clock: a dark face, gold numerals as dots, gold hands.
    cx, cy, r = ax - 30, 320, 90
    c.put(c.mask(lambda p: p.ellipse(cx, cy, r + 10, r + 10)), WOOD_DARK)
    c.put(c.mask(lambda p: p.ellipse(cx, cy, r, r)), (50, 46, 56))
    c.put(c.mask(lambda p: p.ring(cx, cy, r - 6, 3)), GOLD)
    c.put(c.mask(lambda p: [p.ellipse(cx + (r - 18) * math.cos(a), cy + (r - 18) * math.sin(a), 5) for a in np.linspace(0, math.tau, 13)[:-1]]), GOLD)
    c.put(c.mask(lambda p: (p.line([(cx, cy), (cx + 52, cy - 36)], 6), p.line([(cx, cy), (cx - 10, cy - 70)], 4))), GOLD_LIGHT)
    c.put(c.mask(lambda p: p.ellipse(cx, cy, 8, 8)), GOLD)
    # The balcony and its rail; the podium on it.
    walk_top(c, b0, b1, top, STONE)
    c.put(c.mask(box(b0, top, b1, top + 22)), STONE)
    c.tone(c.mask(box(b0, top + 16, b1, top + 22)), -0.2)
    c.put(c.mask(lambda p: ([p.rect(x, top - 30, x + 4, top) for x in np.arange(b0 + 20, b1, 24)], p.rect(b0 + 16, top - 32, b1, top - 28))), GOLD, 0.9)
    c.put(c.mask(lambda p: p.poly([(370, top), (430, top), (424, top - 50), (376, top - 50)])), WOOD)
    c.put(c.mask(lambda p: p.poly([(364, top - 50), (436, top - 50), (436, top - 60), (364, top - 56)])), mix(WOOD, (255, 240, 210), 0.3))
    c.put(c.mask(box(380, top - 66, 420, top - 58)), SCREEN_LIGHT, 0.8)
    sign_mark(c, 400, top - 26, 9)
    # Open treads leave space for the street below.
    for x0, x1, y in PLAZA_STEPS:
        c.put(c.mask(box(x0, y, x1, y + 16)), STONE)
        c.put(c.mask(box(x0, y + 12, x1, y + 16)), STONE_DARK)
        walk_top(c, x0, x1, y, STONE)
        c.put(c.mask(lambda p: p.line([(x0 + 10, y + 36), (x0 + 38, y + 16)], 5)), STEEL_DARK)
    c.put(c.mask(lambda p: p.line([(680, 576 - 32), (608, 576 - 32),
                                  (528, 512 - 32), (b1 - 8, top - 30)], 3)), GOLD)
    # The bookstall under the balcony.
    k.awning(80, 300, top + 70, 30, (MAROON, (240, 230, 220)))
    c.put(c.mask(box(84, top + 100, 296, FLOOR)), (100, 70, 50), 0.9)
    c.put(c.mask(box(84, FLOOR - 50, 296, FLOOR)), WOOD)
    rng = c.rand("books")
    for x in np.arange(96, 284, 8):
        h = rng.uniform(20, 34)
        c.put(c.mask(box(x, FLOOR - 50 - h, x + 6, FLOOR - 50)), rng.choice([MAROON, NAVY, (70, 110, 80), (200, 160, 80), (150, 140, 130)]))
    banner(c, 160, top + 110, top + 168, 30, MAROON)


def clock_walk(c, k):
    """Draw the raised walk, its open arches, and the garden rail."""
    x0, x1, top = CLOCK_WALK
    for left, right in ((x0 + 12, 764), (764, x1 - 14)):
        cap = top + 17
        span = c.mask(box(left, cap, right, FLOOR))
        opening = c.mask(lambda p: p.arch(left + 18, cap + 20, right - 18, FLOOR + 2))
        wall = np.clip(span - opening, 0, 1)
        c.put(wall, STONE_DARK)
        crown = c.mask(lambda p: p.arch(left + 12, cap + 14, right - 12, FLOOR + 2))
        c.put(np.clip(crown - opening, 0, 1) * span, STONE)
        c.put(c.mask(lambda p: [p.rect(pier - 5, FLOOR - 20, pier + 18, FLOOR)
                                for pier in (left + 5, right - 16)]), STONE)
    c.put(c.mask(box(x0, top, x1, top + 21)), STONE)
    c.put(c.mask(box(x0, top + 15, x1, top + 21)), STONE_DARK)
    walk_top(c, x0, x1, top, STONE)
    c.put(c.mask(box(x0 + 4, top - 32, x1 - 12, top - 28)), GOLD)
    c.put(c.mask(lambda p: [p.rect(x, top - 30, x + 4, top)
                            for x in range(x0 + 12, x1 - 10, 24)]), GOLD)
    for x in (x0 + 110, x1 - 12):
        c.put(c.mask(box(x - 4, top - 40, x + 4, top)), STEEL_DARK)
        c.put(c.mask(lambda p: p.ellipse(x, top - 42, 6)), GOLD_LIGHT)


def blossom_tree(c, k):
    """The blossom tree in the middle of the plaza: its planter (y 576),
    the benches either side (y 604), a bough to stand on (y 448) in its
    crown, two lamp posts with the Authority's banners."""
    p0, p1, ptop = PLANTER
    # The planter: stone with a gold plaque of the sign.
    c.put(c.mask(box(p0, ptop, p1, FLOOR)), STONE)
    c.tone(c.mask(box(p0, ptop + 40, p1, FLOOR)), -0.12)
    c.put(c.mask(box(p0 - 6, ptop, p1 + 6, ptop + 10)), STONE_LIGHT)
    walk_top(c, p0, p1, ptop, STONE)
    c.put(c.mask(box(1160, ptop + 16, 1240, ptop + 52)), MAROON)
    c.put(c.mask(lambda p: p.ring(1200, ptop + 34, 30, 2)) * c.mask(box(1160, ptop + 16, 1240, ptop + 52)), GOLD, 0.0)
    c.put(c.mask(lambda p: p.rect(1160, ptop + 16, 1240, ptop + 20)), GOLD)
    sign_mark(c, 1200, ptop + 36, 10)
    # The benches.
    for x0, x1, y in BENCHES:
        c.put(c.mask(box(x0, y, x1, y + 8)), WOOD)
        walk_top(c, x0, x1, y, WOOD)
        c.put(c.mask(lambda p: [p.rect(x, y + 8, x + 8, FLOOR) for x in (x0 + 8, x1 - 16)]), IRON)
    # The trunk and the boughs.
    c.put(c.mask(lambda p: p.poly([(1170, ptop + 2), (1236, ptop + 2), (1226, 520), (1250, 440), (1214, 440), (1200, 500), (1176, 440), (1140, 450), (1180, 520)])), BARK)
    c.put(c.mask(lambda p: (p.line([(1200, 470), (1120, 400), (1040, 360)], 14), p.line([(1220, 450), (1300, 390), (1380, 350)], 12), p.line([(1200, 450), (1210, 330)], 12))), BARK)
    c.tone(c.mask(lambda p: p.poly([(1210, ptop), (1236, ptop), (1226, 520), (1210, 500)])), -0.2)
    # The crown of blossom, in lumps, darker under.
    rng = c.rand("blossom")
    lumps = [(rng.uniform(960, 1440), rng.uniform(180, 420), rng.uniform(40, 80)) for _ in range(34)]
    crown = c.mask(lambda p: [p.ellipse(x, y, r, r * 0.8) for x, y, r in lumps if (x - 1200) ** 2 / 260 ** 2 + (y - 310) ** 2 / 140 ** 2 < 1.0])
    c.paint(crown, c.ramp([(160, BLOSSOM_LIGHT), (300, BLOSSOM), (440, BLOSSOM_DARK)]))
    c.tone(crown * (c.noise("petals", 30, 20, 2) - 0.5), 0.25)
    c.light(crown * c.mask(lambda p: p.ellipse(1080, 220, 160, 110), blur=40), BLOSSOM_LIGHT, 0.35)
    # The bough to stand on, in front of the blossom.
    b0, b1, btop = BOUGH
    c.put(c.mask(lambda p: p.line([(b0 - 20, btop + 30), (b0, btop + 6), (b1, btop + 6), (b1 + 24, btop - 10)], 14)), BARK)
    walk_top(c, b0, b1, btop, BARK)
    # The perch joins the planter to the bough.
    x0, x1, y = GARDEN_PERCH
    c.put(c.mask(lambda p: p.line([(x0, ptop), (x0 + 58, y + 12), (x1 - 18, ptop)], 8)), BARK)
    c.put(c.mask(box(x0, y, x1, y + 14)), WOOD_DARK)
    c.put(c.mask(box(x0 + 2, y + 4, x1 - 2, y + 10)), WOOD)
    walk_top(c, x0, x1, y, WOOD)
    # Under it, low hedges in the planter, white flowers.
    hedge = c.mask(lambda p: [p.ellipse(x, ptop - 6, 26, 18) for x in np.arange(p0 + 20, p1, 34)])
    c.put(hedge, LEAF)
    c.put(c.mask(lambda p: [p.ellipse(x, ptop - 12 + (x % 3) * 3, 3) for x in np.arange(p0 + 12, p1, 22)]), (250, 250, 240))
    # Falling petals.
    c.put(c.mask(lambda p: [p.ellipse(rng.uniform(900, 1500), rng.uniform(300, 620), 2.5, 1.6) for _ in range(40)]), BLOSSOM_LIGHT, 0.9)
    # The lamp posts and their banners.
    for x in (840, 1580):
        lamp_post(c, x, FLOOR, 200)
        banner(c, x + 30, FLOOR - 190, FLOOR - 90, 34, MAROON)
        c.put(c.mask(box(x, FLOOR - 194, x + 46, FLOOR - 190)), IRON)


def notice_board(c, k):
    """The notice board: a wooden board under a little roof, its notices
    pinned on it (the words are the room's signs), a lamp over it."""
    x0, x1, y0, y1 = 1640, 2000, 460, 620
    for x in (x0 + 20, x1 - 30):
        c.put(c.mask(box(x, y0, x + 10, FLOOR)), WOOD_DARK)
    c.put(c.mask(box(x0, y0, x1, y1)), WOOD)
    c.put(c.mask(box(x0 + 8, y0 + 8, x1 - 8, y1 - 8)), (176, 140, 96))
    c.put(c.mask(lambda p: p.poly([(x0 - 20, y0), (x1 + 20, y0), (x1 - 10, y0 - 30), (x0 + 10, y0 - 30)])), MAROON)
    c.tone(c.mask(lambda p: p.poly([(x0 - 20, y0), (x1 + 20, y0), (x1 + 10, y0 - 8), (x0 - 10, y0 - 8)])), -0.25)
    # Old papers pinned along its foot, under the signs.
    rng = c.rand("notices")
    for px in np.arange(x0 + 20, x1 - 40, 46):
        h = rng.uniform(14, 22)
        c.put(c.mask(box(px, y1 - 10 - h, px + 36, y1 - 10)), PAPER, 0.85)
        c.put(c.mask(lambda p: p.ellipse(px + 18, y1 - 8 - h, 2.5)), RED)
    c.light(c.mask(lambda p: p.ellipse((x0 + x1) / 2, y0 + 40, 160, 70), blur=20), LAMP, 0.25)


def manifest_portico(c, k):
    """The Manifest Office's front: a portico of two columns and a
    pediment round the door, the sign in the pediment, steps of stone."""
    x0, x1 = 2120, 2340
    c.put(c.mask(box(x0 + 20, 420, x1 - 20, FLOOR)), STONE_DARK)
    for x in (x0, x1 - 40):
        c.put(c.mask(box(x, 430, x + 40, FLOOR - 8)), STONE)
        c.tone(c.mask(box(x + 26, 430, x + 40, FLOOR - 8)), -0.15)
        c.put(c.mask(lambda p: [p.rect(x + xx, 440, x + xx + 2, FLOOR - 16) for xx in (10, 20, 30)]), STONE_DARK, 0.5)
    c.put(c.mask(box(x0 - 10, 410, x1 + 10, 432)), STONE)
    c.put(c.mask(lambda p: p.poly([(x0 - 14, 410), (x1 + 14, 410), ((x0 + x1) / 2, 360)])), STONE_LIGHT)
    c.put(c.mask(lambda p: p.poly([(x0 + 20, 404), (x1 - 20, 404), ((x0 + x1) / 2, 372)])), STONE)
    sign_mark(c, (x0 + x1) / 2, 392, 10)
    c.put(c.mask(box(x0 - 10, FLOOR - 8, x1 + 10, FLOOR)), STONE_LIGHT)
    banner(c, x0 + 20, 450, 540, 26, NAVY)
    banner(c, x1 - 20, 450, 540, 26, NAVY)


# ---------------------------------------------------------------------------
# The Manifest Office
# ---------------------------------------------------------------------------


def office_counter(c, k):
    """The front of the Manifest Office: the take-a-number machine on its
    post, the NOW SERVING board (its number is the room's sign), a row of
    chairs (y 604), and the counter with its glass and its great stamp."""
    g = FLOOR
    # The take-a-number machine.
    x = 260
    c.put(c.mask(box(x - 4, g - 110, x + 4, g)), IRON)
    c.put(c.mask(box(x - 24, g - 150, x + 24, g - 104)), MAROON)
    c.put(c.mask(box(x - 8, g - 112, x + 8, g - 92)), PAPER)
    c.put(c.mask(lambda p: p.ellipse(x, g - 132, 10, 10)), GOLD)
    # The board.
    bx0, bx1, by0, by1 = 520, 780, 200, 300
    c.put(c.mask(box(bx0, by0, bx1, by1)), STEEL_DARK)
    c.put(c.mask(box(bx0 + 8, by0 + 8, bx1 - 8, by1 - 8)), (20, 20, 24))
    c.put(c.mask(lambda p: [p.rect(xx, by0 - 40, xx + 3, by0) for xx in (bx0 + 30, bx1 - 33)]), IRON)
    c.light(c.mask(box(bx0 + 8, by0 + 8, bx1 - 8, by1 - 8)) * (0.6 + 0.4 * np.sin(c.y * 2.0)), (255, 140, 60), 0.2)
    # The chairs.
    x0, x1, y = CHAIRS
    for cx in np.arange(x0, x1, 50):
        c.put(c.mask(box(cx + 4, y, cx + 46, y + 8)), NAVY)
        c.put(c.mask(box(cx + 6, y - 40, cx + 12, y + 2)), NAVY)
        c.put(c.mask(lambda p: [p.rect(xx, y + 8, xx + 3, g) for xx in (cx + 8, cx + 40)]), IRON)
    walk_top(c, x0, x1, y, NAVY)
    # The counter: wood, a pane of glass on it, a slot in the glass.
    k0, k1 = 900, 1220
    c.put(c.mask(box(k0, g - 80, k1, g)), WOOD)
    c.put(c.mask(lambda p: [p.rect(xx, g - 70, xx + 70, g - 10) for xx in (k0 + 20, k0 + 125, k0 + 230)]), WOOD_DARK, 0.45)
    c.put(c.mask(box(k0 - 6, g - 86, k1 + 6, g - 78)), mix(WOOD, (255, 240, 210), 0.3))
    glass = c.mask(box(k0, g - 200, k1, g - 86)) - c.mask(box(1040, g - 110, 1100, g - 86))
    c.put(np.clip(glass, 0, 1), GLASS, 0.3)
    c.put(c.mask(lambda p: [p.rect(xx, g - 200, xx + 4, g - 86) for xx in (k0, 1060, k1 - 4)]), STEEL_DARK)
    # The great stamp, on the counter, and what it has stamped.
    sx = 1160
    c.put(c.mask(lambda p: (p.rect(sx - 26, g - 104, sx + 26, g - 86), p.rect(sx - 8, g - 140, sx + 8, g - 104), p.ellipse(sx, g - 146, 18, 12))), (120, 30, 40))
    c.put(c.mask(box(sx - 30, g - 90, sx + 30, g - 86)), RED)
    c.put(c.mask(lambda p: [p.rect(xx, g - 92, xx + 40, g - 87) for xx in (k0 + 40, k0 + 90)]), PAPER)
    # Pigeonholes on the wall behind.
    for row in range(4):
        for col in range(8):
            px, py = 920 + col * 36, 300 + row * 34
            c.put(c.mask(box(px, py, px + 32, py + 30)), WOOD_DARK)
            if (row * 8 + col) % 3:
                c.put(c.mask(box(px + 4, py + 10, px + 28, py + 30)), PAPER, 0.8)


def filing_cabinets(c, k):
    """Filing cabinets to the ceiling at the east end: two tiers to climb
    (their tops y 512 and 384), drawers on drawers, and the wall of drawers
    behind them up into the dark."""
    for row in range(14):
        for col in range(9):
            px, py = 1240 + col * 38, 40 + row * 36
            if py > 380:
                break
            c.put(c.mask(box(px, py, px + 36, py + 34)), mix(STEEL, (30, 30, 40), 0.4))
            c.put(c.mask(box(px + 12, py + 14, px + 24, py + 18)), GOLD, 0.5)
    for x0, x1, top in CABINETS:
        c.put(c.mask(box(x0, top, x1, FLOOR)), (130, 136, 150))
        c.tone(c.mask(box(x1 - 16, top, x1, FLOOR)), -0.2)
        walk_top(c, x0, x1, top, (150, 156, 170))
        for y in np.arange(top + 10, FLOOR - 10, 32):
            for x in np.arange(x0 + 6, x1 - 20, 44):
                c.put(c.mask(box(x, y, x + 40, y + 28)), (150, 156, 170))
                c.put(c.mask(box(x + 14, y + 10, x + 26, y + 14)), IRON)
        # One drawer pulled out, papers spilling.
        c.put(c.mask(box(x0 - 18, top + 42, x0 + 30, top + 70)), (150, 156, 170))
        c.put(c.mask(lambda p: [p.rect(x0 - 14 + i * 6, top + 34 - i * 2, x0 + 4 + i * 6, top + 44) for i in range(4)]), PAPER)


#: Every piece: its frame in its room, and how it is drawn.
PIECES: Dict[str, Piece] = {
    # The Concourse.
    "authority_info_booth": Piece((620, 400, 900, 640), info_booth),
    "authority_catwalk": Piece((940, 470, 1740, 640), catwalk),
    "authority_stairwell": Piece((1720, 620, 2160, 1024), stairwell),
    "authority_baggage_wall_west": Piece((8, 696, 1224, 1032), _baggage_wall(16, 1216)),
    "authority_baggage_wall_east": Piece((1176, 696, 2392, 1032), _baggage_wall(1184, 2384)),
    "authority_baggage_hall": Piece((16, 704, 1720, 1024), baggage_hall),
    "authority_baggage_lift_shaft": Piece((1100, 598, 1300, 1016), baggage_lift_shaft),
    "authority_baggage_lift": Piece((0, 0, 176, 52), baggage_lift),
    # Authority Plaza.
    "authority_clock_walk": Piece((508, 394, 1064, 640), clock_walk),
    "authority_clock_arcade": Piece((0, 140, 700, 640), clock_arcade),
    "authority_blossom_tree": Piece((780, 160, 1640, 640), blossom_tree),
    "authority_notice_board": Piece((1610, 420, 2030, 640), notice_board),
    "authority_manifest_portico": Piece((2100, 350, 2360, 640), manifest_portico),
    # The Manifest Office.
    "authority_office_counter": Piece((200, 150, 1240, 640), office_counter),
    "authority_filing_cabinets": Piece((1210, 32, 1584, 640), filing_cabinets),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PAL", "PIECES", "TARGETS"]
