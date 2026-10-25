"""Scenery of the General's tower (`military_tower`, the Iron Bastion of the
Faction of Steel): the inside of each of its five floors.

The room is 480 x 1280 units (`tools/ambition_ldtk_tools/specs/
military_tower_area.ron`). Steel decks 16 units thick divide it into floors;
each deck has a hatch 64 units wide with a grating over a ladder, on the
left and the right in turn. Each piece is one floor drawn in the room's
coordinates (`_district_props`): its back wall, and the furniture that
stands on its floor line. The game draws a room's ladders and doors behind
its scenery, so a piece leaves them open: it cuts its picture away over the
ladder that goes up from its floor and over the two doors.

- `tower_parade_deck` (floor y 1248): the entry. Concrete over an olive
  wainscot, the faction's banner, the duty desk, the roll-call board and the
  flag. The two doors (x 300..348, 380..428) are the room's.
- `tower_barracks` (floor y 1008): bunks, footlockers, lockers.
- `tower_armory` (floor y 768): racks of rifles, crates of ammunition, the
  quartermaster's issue counter and a workbench.
- `tower_signals` (floor y 528): the radio desk, a switchboard and a pinned
  map of the district.
- `tower_war_room` (floor y 288): the map table, the campaign map on the
  wall, the General's medal cabinet and two banners.

The mark of the faction is a white five-point star on an olive roundel with a
brass rim (an invented mark; the gear is the mark of Castle Godwin's regime).
No drop shadows: form shade on a thing's own faces only.

Animations: ``idle``, 1 frame each.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale

PAL = {
    "stone": (142, 140, 132), "stone_light": (196, 192, 182), "trim": (196, 188, 160), "dark": (34, 38, 36),
    "glass_top": (176, 196, 186), "glass_low": (70, 86, 80), "lamp": (255, 214, 140), "wood": (110, 82, 54),
    "leaf": (78, 110, 64), "iron": (44, 48, 50), "brass": (184, 145, 62), "glaze": (210, 170, 80),
}
CONCRETE = (150, 147, 138)
CONCRETE_DARK = (112, 110, 104)
OLIVE = (91, 97, 54)
OLIVE_DARK = (62, 66, 38)
OLIVE_LIGHT = (128, 134, 84)
KHAKI = (183, 167, 122)
KHAKI_DARK = (140, 126, 90)
STEEL = (74, 82, 88)
STEEL_DARK = (46, 52, 56)
STEEL_LIGHT = (128, 138, 144)
BRASS = (184, 145, 62)
RED = (168, 56, 44)
CREAM = (232, 224, 200)
PAPER = (226, 218, 192)
WOOD = (110, 82, 54)
WOOD_DARK = (74, 54, 36)
LAMP = (255, 214, 140)

#: The room: its walls, and the top of each deck (the floor line of the floor above it).
X0, X1 = 16, 464
CEILING = 32
FLOORS = (1248, 1008, 768, 528, 288)
DECK = 16
#: The hatch of each deck (x0, x1): the ladder that comes up through it stands in it.
HATCHES = {1008: (64, 128), 768: (352, 416), 528: (64, 128), 288: (352, 416)}
#: The ladder in a hatch: 32 wide, in its middle (the room's Climbable cells).
LADDER_W = 32
#: The room's two doors on the parade deck (x0, x1), 96 high on its floor.
DOORS = ((300, 348), (380, 428))


def _top(floor: float) -> float:
    """The top of the floor whose floor line is `floor`: the deck above, or the ceiling."""
    above = [f for f in FLOORS if f < floor]
    return max(above) + DECK if above else CEILING


def _open(c, floor: float) -> None:
    """Cut the picture away over the ladder that goes up from `floor` and,
    on the parade deck, over the doors: the game draws those behind the
    scenery."""
    holes = []
    above = max([f for f in FLOORS if f < floor], default=None)
    if above in HATCHES:
        h0, h1 = HATCHES[above]
        cx = (h0 + h1) / 2
        holes.append((cx - LADDER_W / 2 - 2, _top(floor), cx + LADDER_W / 2 + 2, floor))
    if floor == FLOORS[0]:
        holes += [(x0 - 2, floor - 98, x1 + 2, floor) for x0, x1 in DOORS]
    for x0, y0, x1, y1 in holes:
        c.alpha *= 1.0 - c.mask(box(x0, y0, x1, y1))


def _clear(floor: float) -> list[tuple[float, float]]:
    """The x spans where a floor's furniture can stand: not over the hatch in
    its floor, not in front of the ladder that goes up from it."""
    blocked = []
    if floor in HATCHES:
        blocked.append(HATCHES[floor])
    above = max([f for f in FLOORS if f < floor], default=None)
    if above in HATCHES:
        blocked.append(HATCHES[above])
    spans, x = [], X0
    for b0, b1 in sorted(blocked):
        if b0 > x:
            spans.append((x, b0))
        x = max(x, b1)
    if x < X1:
        spans.append((x, X1))
    return spans


# ---------------------------------------------------------------------------
# Walls and fittings
# ---------------------------------------------------------------------------


def back_wall(c, k, floor, tag):
    """Poured concrete over an olive painted wainscot, with the form lines of
    the shuttering, steel columns at the walls and a band of rivets under the
    deck above."""
    top = _top(floor)
    wall = c.mask(box(X0, top, X1, floor))
    c.put(wall, CONCRETE)
    c.tone(wall * (c.noise((tag, "concrete"), 9, 5, 4) - 0.5), 0.10)
    # The lines where the shuttering boards met: faint horizontal joints.
    c.put(c.mask(lambda p: [p.rect(X0, y, X1, y + 0.7) for y in np.arange(top + 22, floor - 60, 22)]) * wall, CONCRETE_DARK, 0.35)
    # The tie holes of the shuttering, in a grid.
    c.put(c.mask(lambda p: [p.ellipse(x, y, 1.1) for x in np.arange(X0 + 30, X1, 60) for y in np.arange(top + 33, floor - 60, 44)]), CONCRETE_DARK, 0.7)
    # The wainscot: olive paint with a darker stripe at its top.
    dado = floor - 56
    c.put(c.mask(box(X0, dado, X1, floor)), OLIVE)
    c.tone(c.mask(box(X0, dado, X1, floor)) * (c.noise((tag, "paint"), 12, 3, 3) - 0.5), 0.10)
    c.put(c.mask(box(X0, dado - 3, X1, dado)), OLIVE_DARK)
    # The column at each wall, an I-beam face with its flanges.
    for x in (X0, X1 - 14):
        c.put(c.mask(box(x, top, x + 14, floor)), STEEL)
        c.put(c.mask(box(x + 4, top, x + 10, floor)), STEEL_DARK)
        c.put(c.mask(box(x, top, x + 1.4, floor)), STEEL_LIGHT)
    # The rivet band under the deck above.
    c.put(c.mask(box(X0, top, X1, top + 8)), STEEL_DARK)
    c.put(c.mask(lambda p: [p.ellipse(x, top + 4, 1.4) for x in np.arange(X0 + 6, X1, 12)]), STEEL_LIGHT)


def roundel(c, cx, cy, r):
    """The faction's mark: a white star on an olive disc with a brass rim."""
    c.put(c.mask(lambda p: p.ellipse(cx, cy, r)), BRASS)
    c.put(c.mask(lambda p: p.ellipse(cx, cy, r * 0.84)), OLIVE)
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r * (0.66 if i % 2 == 0 else 0.27)
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    c.put(c.mask(lambda p: p.poly(pts)), CREAM)


def banner(c, cx, y0, w, h, tag):
    """A long olive banner with the mark, hung from a brass rod."""
    x0, x1 = cx - w / 2, cx + w / 2
    cloth = c.mask(lambda p: p.poly([(x0, y0), (x1, y0), (x1, y0 + h), (cx, y0 + h - w * 0.35), (x0, y0 + h)]))
    c.put(cloth, OLIVE)
    c.tone(cloth * (c.noise((tag, "folds"), 3, 1, 2) - 0.5), 0.22)
    c.put(c.mask(lambda p: (p.rect(x0, y0 + 6, x0 + 2.5, y0 + h - 2), p.rect(x1 - 2.5, y0 + 6, x1, y0 + h - 2))) * cloth, BRASS)
    roundel(c, cx, y0 + w * 0.75, w * 0.32)
    c.put(c.mask(box(x0 - 4, y0 - 2, x1 + 4, y0 + 2)), BRASS)


def caged_lamp(c, k, x, top, drop=18, lit=0.85):
    """A lamp in a wire cage on a conduit from the deck above."""
    y = top + drop
    c.put(c.mask(box(x - 0.8, top, x + 0.8, y)), STEEL_DARK)
    c.put(c.mask(lambda p: p.ellipse(x, y + 6, 6, 7)), mix(LAMP, CREAM, 0.3))
    c.put(c.mask(lambda p: (p.rect(x - 6, y + 2, x + 6, y + 3), p.rect(x - 6, y + 8, x + 6, y + 9), p.rect(x - 0.6, y, x + 0.6, y + 13))), STEEL_DARK)
    c.put(c.mask(box(x - 4, y - 2, x + 4, y + 1)), STEEL)
    c.light(c.mask(lambda p: p.ellipse(x, y + 6, 46, 40), blur=14.0), LAMP, 0.32 * lit)


def stencil_digit(c, x, y, d, h=26, colour=CREAM):
    """A stencilled floor number: a digit of seven bars."""
    w, t = h * 0.55, h * 0.14
    segs = {
        "a": (x, y, x + w, y + t), "g": (x, y + h / 2 - t / 2, x + w, y + h / 2 + t / 2), "d": (x, y + h - t, x + w, y + h),
        "f": (x, y, x + t, y + h / 2), "b": (x + w - t, y, x + w, y + h / 2),
        "e": (x, y + h / 2, x + t, y + h), "c": (x + w - t, y + h / 2, x + w, y + h),
    }
    on = {"0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc", "5": "afgcd"}[d]
    # A stencil leaves small bridges: short gaps at the ends of each bar.
    c.put(c.mask(lambda p: [p.rect(x0 + (t * 0.5 if x1 - x0 > y1 - y0 else 0), y0 + (t * 0.5 if y1 - y0 > x1 - x0 else 0),
                                   x1 - (t * 0.5 if x1 - x0 > y1 - y0 else 0), y1 - (t * 0.5 if y1 - y0 > x1 - x0 else 0))
                            for s, (x0, y0, x1, y1) in segs.items() if s in on]), colour, 0.85)


def floor_sign(c, floor, number, x=X0 + 22):
    """The floor's number, stencilled high on the wall by the west column."""
    stencil_digit(c, x, _top(floor) + 18, str(number))


def notice_board(c, x0, y0, w, h, tag):
    """A cork board with pinned orders and a roster."""
    c.put(c.mask(box(x0 - 2, y0 - 2, x0 + w + 2, y0 + h + 2)), WOOD_DARK)
    board = c.mask(box(x0, y0, x0 + w, y0 + h))
    c.put(board, (168, 128, 82))
    c.tone(board * (c.noise((tag, "cork"), 20, 10, 2) - 0.5), 0.25)
    rng = c.rand(tag, "papers")
    for _ in range(int(w * h / 260)):
        px, py = rng.uniform(x0 + 2, x0 + w - 14), rng.uniform(y0 + 2, y0 + h - 16)
        pw, ph = rng.uniform(9, 14), rng.uniform(11, 16)
        c.put(c.mask(box(px, py, px + pw, py + ph)), mix(PAPER, (255, 255, 255), rng.uniform(0, 0.3)))
        c.put(c.mask(lambda p: [p.rect(px + 1.5, ly, px + pw - 1.5, ly + 0.6) for ly in np.arange(py + 3, py + ph - 1, 2.4)]), (120, 116, 104), 0.7)
        c.put(c.mask(lambda p: p.ellipse(px + pw / 2, py + 1.2, 1.0)), RED)


def crate(c, x0, y1, w, h, colour=OLIVE, mark=True):
    """A wooden ammunition crate standing on `y1`, with its rope handles and stencil."""
    y0 = y1 - h
    body = c.mask(box(x0, y0, x0 + w, y1))
    c.put(body, colour)
    c.tone(body * (c.noise(("crate", x0, y1), 4, 2, 2) - 0.5), 0.14)
    c.put(c.mask(lambda p: (p.rect(x0, y0, x0 + w, y0 + 2.2), p.rect(x0, y1 - 2.2, x0 + w, y1), p.rect(x0, y0, x0 + 2.2, y1), p.rect(x0 + w - 2.2, y0, x0 + w, y1))), scale(colour, 0.7))
    c.put(c.mask(box(x0, y0, x0 + w, y0 + 1)), mix(colour, CREAM, 0.35))
    if mark and w > 18:
        c.put(c.mask(lambda p: [p.rect(x0 + w * 0.2, y0 + h * 0.42, x0 + w * 0.8, y0 + h * 0.42 + 1.6), p.rect(x0 + w * 0.3, y0 + h * 0.58, x0 + w * 0.7, y0 + h * 0.58 + 1.6)]), (214, 196, 120), 0.85)


def sandbags(c, x0, x1, y1, rows=3):
    """A low wall of sandbags, laid in courses."""
    h = 8.0
    for r in range(rows):
        y = y1 - (r + 1) * h
        off = (r % 2) * 9
        for x in np.arange(x0 + off - 9, x1, 18):
            if x + 17 < x0 or x > x1:
                continue
            bag = c.mask(lambda p: p.ellipse(x + 9, y + h / 2, 9.6, h / 2 + 0.6))
            c.put(bag, KHAKI)
            c.tone(bag * c.mask(lambda p: p.ellipse(x + 9, y + h * 0.75, 9, h / 3), blur=1.0), -0.28)
            c.put(c.mask(lambda p: p.rect(x + 8.4, y + 1, x + 9.6, y + h - 1)) * bag, KHAKI_DARK, 0.7)


def rifle(c, x, y0, y1, colour=WOOD):
    """A rifle standing in a rack: stock below, barrel up."""
    n = y1 - y0
    c.put(c.mask(lambda p: p.poly([(x - 2.4, y1), (x + 3.2, y1), (x + 2.0, y1 - n * 0.26), (x - 1.2, y1 - n * 0.26)])), colour)
    c.put(c.mask(box(x - 1.0, y1 - n * 0.62, x + 2.0, y1 - n * 0.24)), scale(colour, 0.8))
    c.put(c.mask(box(x - 0.2, y0, x + 1.2, y1 - n * 0.5)), STEEL_DARK)
    c.put(c.mask(box(x - 2.0, y1 - n * 0.48, x + 1.0, y1 - n * 0.40)), STEEL)


def locker(c, x0, y1, w=22, h=70, colour=OLIVE_LIGHT, open_=False):
    y0 = y1 - h
    c.put(c.mask(box(x0, y0, x0 + w, y1)), colour)
    c.put(c.mask(box(x0, y0, x0 + 1.2, y1)), mix(colour, CREAM, 0.3))
    c.put(c.mask(box(x0 + w - 1.2, y0, x0 + w, y1)), scale(colour, 0.7))
    c.put(c.mask(lambda p: [p.rect(x0 + 4, y0 + 6 + i * 3, x0 + w - 4, y0 + 7.2 + i * 3) for i in range(4)]), scale(colour, 0.6))
    c.put(c.mask(box(x0 + w - 6, y0 + h * 0.45, x0 + w - 4, y0 + h * 0.6)), STEEL_DARK)
    c.put(c.mask(box(x0 + 3, y0 + 22, x0 + w - 3, y0 + 30)), PAPER, 0.9)


def bunk(c, x0, y1, w=78):
    """A steel double bunk with olive blankets and white pillows."""
    for x in (x0, x0 + w - 3):
        c.put(c.mask(box(x, y1 - 78, x + 3, y1)), STEEL)
    for yb in (y1 - 18, y1 - 58):
        c.put(c.mask(box(x0, yb, x0 + w, yb + 3)), STEEL)
        mattress = c.mask(lambda p: p.rect(x0 + 3, yb - 8, x0 + w - 3, yb))
        c.put(mattress, OLIVE)
        c.put(c.mask(box(x0 + 3, yb - 8, x0 + w - 3, yb - 6.8)), OLIVE_LIGHT)
        c.put(c.mask(lambda p: p.ellipse(x0 + 14, yb - 9, 9, 3.4)), CREAM)
        c.tone(mattress * (c.noise(("blanket", x0, yb), 5, 1, 2) - 0.5), 0.2)
    c.put(c.mask(lambda p: [p.rect(x0 + w - 3 - 10, y, x0 + w - 3, y + 1.6) for y in np.arange(y1 - 74, y1 - 22, 7)]), STEEL_DARK)


def footlocker(c, x0, y1, w=30, h=13):
    c.put(c.mask(box(x0, y1 - h, x0 + w, y1)), OLIVE_DARK)
    c.put(c.mask(box(x0, y1 - h, x0 + w, y1 - h + 3)), OLIVE)
    c.put(c.mask(box(x0 + w / 2 - 2, y1 - h + 3, x0 + w / 2 + 2, y1 - h + 7)), BRASS)
    c.put(c.mask(lambda p: (p.rect(x0 + 3, y1 - h, x0 + 5, y1), p.rect(x0 + w - 5, y1 - h, x0 + w - 3, y1))), STEEL_DARK)


def desk(c, x0, x1, y1, h=30, colour=OLIVE_DARK, drawers=True):
    c.put(c.mask(box(x0 - 3, y1 - h - 3, x1 + 3, y1 - h)), WOOD)
    c.put(c.mask(box(x0 - 3, y1 - h - 3, x1 + 3, y1 - h - 2.2)), mix(WOOD, CREAM, 0.4))
    c.put(c.mask(box(x0, y1 - h, x1, y1)), colour)
    c.put(c.mask(box(x0, y1 - h, x0 + 1.2, y1)), mix(colour, CREAM, 0.25))
    if drawers:
        c.put(c.mask(lambda p: [p.rect(x1 - 22, y, x1 - 4, y + 0.9) for y in np.arange(y1 - h + 8, y1 - 2, 8)]), scale(colour, 0.6))
        c.put(c.mask(lambda p: [p.rect(x1 - 15, y + 3, x1 - 11, y + 4.4) for y in np.arange(y1 - h + 4, y1 - 4, 8)]), BRASS)


def chair(c, x, y1, facing=1):
    c.put(c.mask(box(x - 8, y1 - 16, x + 8, y1 - 13)), WOOD)
    c.put(c.mask(lambda p: (p.rect(x - 7, y1 - 13, x - 5, y1), p.rect(x + 5, y1 - 13, x + 7, y1))), WOOD_DARK)
    bx = x - 8 if facing > 0 else x + 6
    c.put(c.mask(box(bx, y1 - 36, bx + 2.4, y1 - 13)), WOOD_DARK)
    c.put(c.mask(box(min(bx, bx + 2.4) - 0.5, y1 - 34, min(bx, bx + 2.4) + 3, y1 - 26)), WOOD)


def wall_clock(c, x, y):
    c.put(c.mask(lambda p: p.ellipse(x, y, 11)), STEEL_DARK)
    c.put(c.mask(lambda p: p.ellipse(x, y, 9.4)), CREAM)
    c.put(c.mask(lambda p: [p.rect(x + 7.6 * math.cos(a) - 0.5, y + 7.6 * math.sin(a) - 0.5, x + 7.6 * math.cos(a) + 0.5, y + 7.6 * math.sin(a) + 0.5) for a in np.linspace(0, math.tau, 13)[:-1]]), STEEL_DARK)
    c.put(c.mask(lambda p: (p.line([(x, y), (x, y - 6.4)], 1.2), p.line([(x, y), (x + 4.4, y + 1.2)], 1.4))), STEEL_DARK)


# ---------------------------------------------------------------------------
# The floors
# ---------------------------------------------------------------------------


def parade_deck(c, k):
    """The entry: the faction's banner and roll-call board, the duty desk and
    a sandbag wall. The duty desk stands west of the player's start (x 240);
    the sentry stands east of the hub door (x 432..464)."""
    g = FLOORS[0]
    top = _top(g)
    back_wall(c, k, g, "parade")
    floor_sign(c, g, 1)
    banner(c, 196, top + 12, 52, 120, "parade_banner")
    notice_board(c, 124, top + 40, 50, 34, "rollcall")
    wall_clock(c, 268, top + 52)
    # The duty desk, with its logbook, a lamp and a telephone.
    desk(c, 136, 200, g, 30)
    c.put(c.mask(box(154, g - 36, 182, g - 33)), PAPER)
    c.put(c.mask(box(168, g - 36.5, 169, g - 33)), (90, 80, 60))
    c.put(c.mask(lambda p: (p.rect(142, g - 44, 145, g - 33), p.poly([(138, g - 50), (150, g - 50), (147, g - 44), (141, g - 44)]))), STEEL)
    c.light(c.mask(lambda p: p.ellipse(144, g - 38, 18, 9), blur=4.0), LAMP, 0.4)
    c.put(c.mask(lambda p: (p.rect(186, g - 38, 196, g - 33), p.ellipse(191, g - 40, 5, 2))), STEEL_DARK)
    chair(c, 216, g, -1)
    # A short sandbag wall by the west column, crates on it.
    sandbags(c, 18, 60, g, 3)
    crate(c, 22, g - 24, 34, 16, OLIVE_DARK)
    for x in (100, 196, 300, 404):
        caged_lamp(c, k, x, top, 14)
    _open(c, g)

def barracks(c, k):
    """Bunks and footlockers, lockers by the east ladder."""
    g = FLOORS[1]
    top = _top(g)
    back_wall(c, k, g, "barracks")
    floor_sign(c, g, 2)
    for x in (134, 218):
        bunk(c, x, g, 78)
        footlocker(c, x + 24, g)
    for i, x in enumerate((292, 316, 340)):
        locker(c, x, g, 22, 72, OLIVE_LIGHT if i != 1 else mix(OLIVE_LIGHT, KHAKI, 0.25))
    # A mirror and a shelf by the east wall, past the ladder.
    c.put(c.mask(box(424, g - 112, 452, g - 80)), STEEL)
    c.put(c.mask(box(426, g - 110, 450, g - 82)), (168, 188, 186))
    c.light(c.mask(box(427, g - 109, 434, g - 83)), CREAM, 0.4)
    c.put(c.mask(box(420, g - 62, 456, g - 59)), WOOD)
    for x, col in ((426, CREAM), (436, (90, 120, 160)), (446, KHAKI)):
        c.put(c.mask(box(x, g - 70, x + 6, g - 62)), col)
    notice_board(c, 140, top + 40, 40, 26, "duty_roster")
    for x in (160, 330):
        caged_lamp(c, k, x, top, 14)
    _open(c, g)

def armory(c, k):
    """Racks of rifles, crates of ammunition, the issue counter and a bench."""
    g = FLOORS[2]
    top = _top(g)
    back_wall(c, k, g, "armory")
    floor_sign(c, g, 3)
    # Two racks of rifles on the wall, west of the counter.
    for rx0 in (134, 206):
        c.put(c.mask(box(rx0, g - 112, rx0 + 66, g - 106)), WOOD_DARK)
        c.put(c.mask(box(rx0, g - 34, rx0 + 66, g - 28)), WOOD_DARK)
        for x in np.arange(rx0 + 7, rx0 + 64, 11):
            rifle(c, x, g - 116, g - 30)
    # The issue counter: a grille window over a steel counter.
    cx0, cx1 = 282, 346
    c.put(c.mask(box(cx0, g - 120, cx1, g - 40)), STEEL_DARK)
    c.put(c.mask(lambda p: [p.rect(x, g - 116, x + 1.2, g - 44) for x in np.arange(cx0 + 6, cx1 - 4, 7)]), STEEL_LIGHT)
    c.put(c.mask(box(cx0 - 4, g - 40, cx1 + 4, g - 34)), STEEL)
    c.put(c.mask(box(cx0, g - 34, cx1, g)), OLIVE_DARK)
    c.put(c.mask(lambda p: [p.ellipse(x, g - 37, 0.9) for x in np.arange(cx0, cx1, 8)]), STEEL_LIGHT)
    c.put(c.mask(box(cx0 + 18, g - 132, cx1 - 18, g - 122)), PAPER)
    # Ammunition crates, stacked, by the east wall past the hatch.
    crate(c, 420, g, 36, 18)
    crate(c, 424, g - 18, 30, 16, OLIVE_DARK)
    crate(c, 18, g, 40, 18)
    crate(c, 22, g - 18, 34, 16, OLIVE_DARK)
    # Helmets on a shelf over the crates.
    c.put(c.mask(box(418, g - 92, 458, g - 89)), WOOD)
    for x in (425, 438, 451):
        c.put(c.mask(lambda p: p.ellipse(x, g - 92, 6, 5)), OLIVE)
        c.put(c.mask(lambda p: p.rect(x - 6, g - 92, x + 6, g - 89)), WOOD)
    for x in (160, 320):
        caged_lamp(c, k, x, top, 14)
    _open(c, g)

def signals(c, k):
    """The radio desk with its sets, the switchboard and the pinned map."""
    g = FLOORS[3]
    top = _top(g)
    back_wall(c, k, g, "signals")
    floor_sign(c, g, 4)
    # The map of the district, pinned, with strings between pins.
    mx0, my0, mx1, my1 = 128, top + 30, 250, top + 112
    c.put(c.mask(box(mx0 - 3, my0 - 3, mx1 + 3, my1 + 3)), WOOD_DARK)
    sheet = c.mask(box(mx0, my0, mx1, my1))
    c.put(sheet, (206, 200, 166))
    c.put(c.mask(lambda p: [p.line([(mx0 + 10 + i * 18, my0), (mx0 + 4 + i * 18, my1)], 0.8) for i in range(7)]) * sheet, (150, 170, 150), 0.6)
    c.put(c.mask(lambda p: p.poly([(mx0 + 20, my0 + 50), (mx0 + 50, my0 + 30), (mx0 + 90, my0 + 42), (mx0 + 110, my0 + 70), (mx0 + 60, my0 + 76)])), (176, 190, 150), 0.8)
    pins = [(mx0 + 30, my0 + 46), (mx0 + 70, my0 + 38), (mx0 + 96, my0 + 62), (mx0 + 52, my0 + 66)]
    c.put(c.mask(lambda p: p.line(pins + [pins[0]], 0.7)), RED, 0.85)
    c.put(c.mask(lambda p: [p.ellipse(x, y, 1.8) for x, y in pins]), RED)
    # The radio desk and its sets: dials, a meter, the valves glowing.
    desk(c, 262, 360, g, 30)
    for i, (x0, w, h) in enumerate(((266, 40, 36), (310, 46, 44))):
        y1 = g - 33
        c.put(c.mask(box(x0, y1 - h, x0 + w, y1)), (78, 86, 72))
        c.put(c.mask(box(x0, y1 - h, x0 + w, y1 - h + 1.2)), mix((78, 86, 72), CREAM, 0.3))
        for j in range(3):
            c.put(c.mask(lambda p: p.ellipse(x0 + 8 + j * (w - 16) / 2, y1 - 9, 3.6)), STEEL_DARK)
            c.put(c.mask(lambda p: p.ellipse(x0 + 8 + j * (w - 16) / 2, y1 - 9, 1.2)), CREAM)
        c.put(c.mask(box(x0 + 5, y1 - h + 5, x0 + w - 5, y1 - h + 15)), (226, 214, 160))
        c.put(c.mask(lambda p: p.line([(x0 + w / 2, y1 - h + 14), (x0 + w / 2 + 5, y1 - h + 7)], 0.7)), STEEL_DARK)
    c.put(c.mask(lambda p: [p.ellipse(x, g - 82, 2.2, 3.2) for x in (320, 328, 336)]), (255, 170, 90))
    c.light(c.mask(lambda p: p.ellipse(328, g - 82, 14, 10), blur=3.0), (255, 170, 90), 0.5)
    # A headset hangs on the set; a microphone on the desk.
    c.put(c.mask(lambda p: (p.ring(300, g - 76, 6, 1.4), p.ellipse(294, g - 72, 2.6), p.ellipse(306, g - 72, 2.6))), STEEL_DARK)
    c.put(c.mask(lambda p: (p.rect(352, g - 44, 354, g - 33), p.ellipse(353, g - 46, 3, 3.6))), STEEL)
    chair(c, 312, g, 1)
    # The switchboard by the east wall, past the ladder.
    c.put(c.mask(box(420, g - 104, 458, g)), WOOD_DARK)
    c.put(c.mask(box(423, g - 100, 455, g - 46)), (40, 40, 38))
    c.put(c.mask(lambda p: [p.ellipse(x, y, 1.2) for x in np.arange(428, 452, 6) for y in np.arange(g - 94, g - 52, 7)]), BRASS)
    c.put(c.mask(lambda p: [p.line([(430 + i * 7, g - 60 + i), (436 + i * 5, g - 30)], 0.8) for i in range(3)]), RED)
    for x in (160, 330):
        caged_lamp(c, k, x, top, 14)
    _open(c, g)

def war_room(c, k):
    """The map table, the campaign map, the medal cabinet and two banners.
    The General stands west of the table (x 120); his adjutant east of it."""
    g = FLOORS[4]
    top = _top(g)
    back_wall(c, k, g, "war_room")
    floor_sign(c, g, 5)
    # The campaign map: a big framed sheet on the wall, arrows and fronts.
    mx0, my0, mx1, my1 = 120, top + 22, 330, top + 128
    c.put(c.mask(box(mx0 - 5, my0 - 5, mx1 + 5, my1 + 5)), WOOD_DARK)
    c.put(c.mask(box(mx0 - 5, my0 - 5, mx1 + 5, my0 - 3.6)), mix(WOOD_DARK, CREAM, 0.3))
    sea = c.mask(box(mx0, my0, mx1, my1))
    c.put(sea, (150, 176, 180))
    land = c.mask(lambda p: (p.poly([(mx0, my0 + 30), (mx0 + 70, my0 + 10), (mx0 + 140, my0 + 26), (mx0 + 210, my0 + 8), (mx1, my0 + 20), (mx1, my1), (mx0, my1)]),))
    c.put(land * sea, (196, 188, 146))
    c.tone(land * sea * (c.noise(("war_map", "relief"), 12, 6, 3) - 0.5), 0.2)
    c.put(c.mask(lambda p: p.line([(mx0 + 30, my1 - 10), (mx0 + 80, my0 + 60), (mx0 + 150, my0 + 50), (mx0 + 190, my1 - 20)], 1.2)), (120, 100, 70), 0.8)
    for (x, y), d in (((mx0 + 60, my0 + 76), 1), ((mx0 + 150, my0 + 60), -1)):
        c.put(c.mask(lambda p: p.poly([(x - 14 * d, y + 6), (x + 10 * d, y), (x - 14 * d, y - 6)])), RED if d > 0 else OLIVE_DARK, 0.9)
    roundel(c, mx1 - 18, my0 + 18, 9)
    # Banners either side of the map.
    banner(c, 72, top + 10, 40, 140, "war_banner_w")
    banner(c, 348, top + 10, 40, 140, "war_banner_e")
    # The map table, its top a relief of the district with markers on it.
    tx0, tx1 = 160, 300
    c.put(c.mask(box(tx0 + 6, g - 30, tx0 + 12, g)), WOOD_DARK)
    c.put(c.mask(box(tx1 - 12, g - 30, tx1 - 6, g)), WOOD_DARK)
    c.put(c.mask(box(tx0, g - 36, tx1, g - 28)), WOOD)
    c.put(c.mask(box(tx0, g - 40, tx1, g - 36)), (176, 170, 128))
    c.put(c.mask(box(tx0, g - 40, tx1, g - 39)), mix((176, 170, 128), CREAM, 0.4))
    rng = c.rand("war_table", "markers")
    for _ in range(9):
        x = rng.uniform(tx0 + 8, tx1 - 8)
        col = rng.choice([OLIVE_DARK, RED, BRASS])
        c.put(c.mask(lambda p: (p.rect(x - 1.6, g - 46, x + 1.6, g - 40), p.poly([(x - 1.6, g - 46), (x + 6, g - 44), (x - 1.6, g - 42)]))), col)
    # The medal cabinet: a glass case by the east wall, past the hatch.
    cx0, cx1 = 420, 458
    c.put(c.mask(box(cx0, g - 108, cx1, g)), WOOD_DARK)
    c.put(c.mask(box(cx0 + 3, g - 104, cx1 - 3, g - 30)), (60, 70, 66))
    k.glass(c.mask(box(cx0 + 3, g - 104, cx1 - 3, g - 30)), 0.15, g - 104, g - 30, "medal_case")
    for row, y in enumerate((g - 94, g - 72, g - 50)):
        for i in range(3):
            x = cx0 + 9 + i * 10
            col = [(168, 56, 44), (60, 90, 140), (91, 97, 54)][(row + i) % 3]
            c.put(c.mask(box(x - 2, y - 6, x + 2, y)), col)
            c.put(c.mask(lambda p: p.ellipse(x, y + 3, 3)), BRASS)
    c.put(c.mask(box(cx0, g - 30, cx1, g)), WOOD)
    for x in (110, 230, 340):
        caged_lamp(c, k, x, top, 10)
    _open(c, g)

#: Every piece: its frame in the room (one floor, deck to deck), and how it is drawn.
PIECES: Dict[str, Piece] = {
    "tower_parade_deck": Piece((X0, _top(FLOORS[0]), X1, FLOORS[0]), parade_deck),
    "tower_barracks": Piece((X0, _top(FLOORS[1]), X1, FLOORS[1]), barracks),
    "tower_armory": Piece((X0, _top(FLOORS[2]), X1, FLOORS[2]), armory),
    "tower_signals": Piece((X0, _top(FLOORS[3]), X1, FLOORS[3]), signals),
    "tower_war_room": Piece((X0, _top(FLOORS[4]), X1, FLOORS[4]), war_room),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["FLOORS", "HATCHES", "PAL", "PIECES", "TARGETS"]
