"""Scenery of Eureka (gate address SCIENCE): the buildings of the Patent Clerk
and of Carl Stargan, outside on the quad and inside.

The rooms are `eureka_quad`, `eureka_patent_office` and `eureka_observatory`
(`tools/ambition_ldtk_tools/specs/eureka/make_specs.py`). Each piece is drawn
in its room's coordinates (`_district_props`): where the room places a walk
line (a counter, the cabinets, the archive gallery, a stair, the telescope's
platform), the piece draws the light top edge of the thing walked on there.

- The quad: the Patent Office (Third Class), an old federal office of
  sandstone with an arcade on the street, shuttered windows with geraniums,
  a copper mansard and a clock gable; over its door, the office's seal with
  a light bulb. Up on the lecture hall's terrace (y 576), the observatory: a
  white drum with a band of gold constellations, a copper dome with its slit
  open and the refractor looking out of it.
- The patent office inside: panelling under sage plaster, a wall of
  pigeonholes stuffed with applications over the counter (y 536), a card
  cabinet (y 480), the archive gallery (y 400) with its shelf of patent
  models (a wheel that would turn for ever, a flying machine, a bulb), and
  the clerk's chalkboard of trains, lightning and light cones.
- The observatory inside: the dome's vault at night, ribbed and painted with
  a star map, the slit open on the stars and on the station's pale dot. The
  stair of treads up the wall (y 880..400, red observing lamps), the
  platform (y 320) and the great refractor on its mount, a golden record and
  a pale blue dot framed on the wall, an orrery, a bookcase.

Animations: ``idle``, 1 frame each. No drop shadows: form shade on a thing's
own faces only.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale

PAL = {
    "stone": (196, 178, 140), "stone_light": (240, 228, 200), "trim": (238, 230, 210), "dark": (40, 44, 52),
    "glass_top": (150, 200, 226), "glass_low": (60, 92, 118), "lamp": (255, 222, 150), "wood": (110, 74, 48),
    "leaf": (70, 122, 64), "iron": (44, 46, 52), "brass": (206, 160, 76), "glaze": (210, 170, 80),
}
SANDSTONE = (226, 204, 160)
SANDSTONE_DARK = (184, 158, 118)
SHUTTER = (92, 126, 104)
GERANIUM = (214, 58, 52)
COPPER = (112, 168, 146)
COPPER_DARK = (70, 118, 104)
OAK = (132, 90, 56)
OAK_DARK = (86, 58, 38)
OAK_LIGHT = (184, 138, 92)
SAGE = (186, 196, 168)
PAPER = (236, 228, 204)
PAPER_OLD = (214, 198, 160)
RIBBON = (168, 52, 48)
CHALK = (232, 236, 228)
BOARD = (44, 62, 54)
DOME_WHITE = (236, 236, 228)
NAVY = (26, 36, 70)
NIGHT = (14, 20, 44)
NIGHT_RIB = (34, 46, 86)
GOLD = (232, 192, 96)
RED_LAMP = (230, 60, 48)
BRASS = PAL["brass"]


class Batch:
    """Shapes gathered by colour and drawn with one mask each: a canvas mask
    is the size of the whole frame, so many small things are drawn at once."""

    def __init__(self, c):
        self.c, self.by = c, {}

    def add(self, colour, a, f):
        self.by.setdefault((tuple(int(v) for v in colour), a), []).append(f)

    def draw(self):
        for (colour, a), fs in self.by.items():
            self.c.put(self.c.mask(lambda p: [f(p) for f in fs]), colour, a)
        self.by = {}


def ashlar(c, x0, y0, x1, y1, colour, course=12.0, block=24.0, tag="ashlar", vary=0.08):
    """A wall of dressed stone blocks in courses, each block its own tone,
    the joints darker and each block's top edge lit."""
    m = c.mask(box(x0, y0, x1, y1))
    c.put(m, colour)
    row = np.floor((c.y - y0) / course)
    u = (c.x - x0) / block + (row % 2) * 0.5
    col = np.floor(u)
    h = (np.sin(row * 12.9898 + col * 78.233) * 43758.5453) % 1.0
    c.tone(m * (h - 0.5) * 2, vary)
    fy = (c.y - y0) / course - row
    fx = u - col
    joint = ((fy < 0.07) | (fx < 0.03)).astype(np.float32)
    c.put(m * joint, scale(colour, 0.72), 0.55)
    lit = ((fy >= 0.07) & (fy < 0.15)).astype(np.float32)
    c.put(m * lit * (1 - joint), PAL["stone_light"], 0.22)
    c.tone(m * (c.noise((tag, "stone"), 16, 10, 3) - 0.5), 0.10)
    c.tone(m * np.clip((c.y - y0) / max(1.0, y1 - y0), 0, 1), -0.10)
    return m


def edge_line(c, x0, x1, y, colour, h=5.0):
    """The walked edge at `y`: a board whose top is the one light line."""
    c.put(c.mask(box(x0, y, x1, y + h)), colour)
    c.put(c.mask(box(x0, y, x1, y + 1.2)), mix(colour, (255, 240, 210), 0.5))
    c.put(c.mask(box(x0, y + h - 1, x1, y + h)), scale(colour, 0.55))


def panels(c, x0, y0, x1, y1, colour, n, tag):
    """A face of raised wooden panels."""
    m = c.mask(box(x0, y0, x1, y1))
    c.put(m, colour)
    c.tone(m * (c.noise((tag, "grain"), 6, 30, 2) - 0.5), 0.22)
    w = (x1 - x0) / n
    xs = [(x0 + i * w + 4, x0 + (i + 1) * w - 4) for i in range(n)]
    py0, py1 = y0 + 5, y1 - 5
    c.put(c.mask(lambda p: [p.rect(a, py0, b, py1) for a, b in xs]), mix(colour, (255, 236, 200), 0.10))
    c.put(c.mask(lambda p: [p.rect(a, py0, b, py0 + 1.2) for a, b in xs]), scale(colour, 0.62))
    c.put(c.mask(lambda p: [p.rect(a, py0, a + 1.2, py1) for a, b in xs]), scale(colour, 0.7))
    c.put(c.mask(lambda p: [p.rect(a, py1 - 1.0, b, py1) for a, b in xs]), mix(colour, (255, 236, 200), 0.35))
    return m


BINDINGS = ((116, 44, 40), (52, 72, 110), (60, 96, 70), (150, 120, 70), (90, 60, 110), PAPER_OLD)


def books(b, rng, x0, x1, shelf, h0, h1, w0, w1):
    """A shelf's row of books, into batch `b`: spines with gilt bands."""
    x = x0
    while x < x1:
        w, h = rng.uniform(w0, w1), rng.uniform(h0, h1)
        b.add(rng.choice(BINDINGS), 1.0, box(x, shelf - h, x + w - 0.8, shelf))
        b.add(GOLD, 0.7, lambda p, x=x, w=w, h=h: (p.rect(x + 1, shelf - h + 4, x + w - 2, shelf - h + 5.2), p.rect(x + 1, shelf - 7, x + w - 2, shelf - 5.8)))
        x += w + (rng.uniform(4, 10) if rng.random() < 0.12 else 0)


def bulb(c, cx, cy, r, colour=BRASS, w=1.2):
    """A light bulb in outline: the emblem of an invention."""
    c.put(c.mask(lambda p: (p.ring(cx, cy, r, w), p.rect(cx - r * 0.42, cy + r * 0.8, cx + r * 0.42, cy + r * 1.5))), colour)
    c.put(c.mask(lambda p: [p.rect(cx - r * 0.42, y, cx + r * 0.42, y + w * 0.6) for y in (cy + r * 1.05, cy + r * 1.3)]), scale(colour, 0.6))
    c.put(c.mask(lambda p: p.line([(cx - r * 0.3, cy + r * 0.5), (cx - r * 0.15, cy - r * 0.2), (cx, cy + r * 0.2), (cx + r * 0.15, cy - r * 0.2), (cx + r * 0.3, cy + r * 0.5)], w * 0.7)), colour)


def pendant(c, x, y_ceiling, drop, lit=0.8, glass=(255, 236, 190)):
    """A lamp on a rod from the ceiling: a glass globe."""
    y = y_ceiling + drop
    c.put(c.mask(box(x - 0.6, y_ceiling, x + 0.6, y - 6)), PAL["iron"])
    c.put(c.mask(lambda p: p.poly([(x - 4, y - 6), (x + 4, y - 6), (x + 2.6, y - 3), (x - 2.6, y - 3)])), BRASS)
    c.put(c.mask(lambda p: p.ellipse(x, y + 4, 7.5)), mix(glass, (255, 255, 255), 0.4))
    c.light(c.mask(lambda p: p.ellipse(x, y + 4, 10), blur=6), PAL["lamp"], lit)
    c.light(c.mask(lambda p: p.ellipse(x, y + 20, 70, 50), blur=30), PAL["lamp"], lit * 0.18)


def stars(c, x0, y0, x1, y1, n, tag, colour=(255, 255, 240), clip=None):
    rng = c.rand(tag, "stars")
    pts = [(rng.uniform(x0, x1), rng.uniform(y0, y1), rng.random()) for _ in range(n)]
    m = c.mask(lambda p: [p.ellipse(x, y, 0.5 + b * 0.9) for x, y, b in pts])
    glow = c.mask(lambda p: [p.ellipse(x, y, 2.5) for x, y, b in pts if b > 0.85], blur=1.2)
    if clip is not None:
        m, glow = m * clip, glow * clip
    c.put(m, colour)
    c.light(glow, colour, 0.5)


#: Constellation figures as points in a unit box (drawn as gold lines and dots).
FIGURES = (
    ((0.0, 0.6), (0.2, 0.2), (0.45, 0.35), (0.6, 0.1), (0.85, 0.3), (1.0, 0.0)),  # the dipper's sweep
    ((0.1, 0.0), (0.0, 1.0), (0.5, 0.5), (1.0, 1.0), (0.9, 0.0)),  # a W
    ((0.5, 0.0), (0.3, 0.45), (0.5, 0.5), (0.7, 0.45), (0.5, 0.0), (0.5, 1.0), (0.2, 0.8), (0.8, 0.8)),  # a hunter
    ((0.0, 0.5), (0.3, 0.3), (0.6, 0.4), (1.0, 0.1)),
)


def constellation(c, fig, x, y, w, h, colour=GOLD, width=0.6, dot=1.2):
    pts = [(x + px * w, y + py * h) for px, py in FIGURES[fig % len(FIGURES)]]
    c.put(c.mask(lambda p: p.line(pts, width)), colour, 0.7)
    c.put(c.mask(lambda p: [p.ellipse(px, py, dot) for px, py in pts]), mix(colour, (255, 255, 240), 0.5))


# ---------------------------------------------------------------------------
# The quad: the Patent Office (Third Class)
# ---------------------------------------------------------------------------

STREET, TERRACE = 768, 576
#: The patent office's door zone (x 760..808) and the house's sides.
PATENT_DOOR = 784
PO_X0, PO_X1 = 676, 984
PO_ARCADE = 618
PO_FIRST, PO_SECOND, PO_CORNICE = 498, 378, 372


def patent_front(c, k):
    """The Patent Office (Third Class) on the quad: three storeys of
    sandstone over an arcade of four arches (the door's is the second), a
    copper mansard with dormers, and a clock gable over the door."""
    k.ground = STREET
    x0, x1 = PO_X0, PO_X1
    arches = (712, PATENT_DOOR, 856, 928)
    # The mansard and its dormers, behind the gable.
    roof = c.mask(lambda p: p.poly([(x0 - 6, PO_CORNICE), (x1 + 6, PO_CORNICE), (x1 - 14, PO_CORNICE - 52), (x0 + 14, PO_CORNICE - 52)]))
    c.put(roof, COPPER)
    k._tiles(roof, x0 - 6, x1 + 6, PO_CORNICE - 52, PO_CORNICE, COPPER, "slate", "po_roof")
    c.tone(roof * np.clip((PO_CORNICE - c.y) / 52, 0, 1), 0.12)
    c.put(c.mask(box(x0 + 14, PO_CORNICE - 55, x1 - 14, PO_CORNICE - 51)), COPPER_DARK)
    for dx in (712, 856, 928):
        c.put(c.mask(lambda p: p.poly([(dx - 15, PO_CORNICE - 6), (dx + 15, PO_CORNICE - 6), (dx + 15, PO_CORNICE - 34), (dx, PO_CORNICE - 46), (dx - 15, PO_CORNICE - 34)])), SANDSTONE)
        k.window(dx, PO_CORNICE - 34, 16, 24, "arch", lit=0.0, frame=PAL["trim"], sill=False, tag=("po_dormer", dx))
    # The walls: rusticated base, smooth ashlar over it.
    ashlar(c, x0, PO_CORNICE, x1, PO_ARCADE, SANDSTONE, 12, 26, "po_upper")
    ashlar(c, x0, PO_ARCADE, x1, STREET, SANDSTONE_DARK, 15, 34, "po_base", 0.12)
    c.put(c.mask(lambda p: [p.rect(x0, y, x1, y + 0.9) for y in np.arange(PO_ARCADE + 15, STREET, 15)]), scale(SANDSTONE_DARK, 0.7), 0.7)
    # Pilasters at the corners and between the bays.
    for px in (x0, x1 - 10):
        c.put(c.mask(box(px, PO_CORNICE, px + 10, PO_ARCADE)), mix(SANDSTONE, (255, 255, 255), 0.18))
        c.put(c.mask(box(px + 8.5, PO_CORNICE, px + 10, PO_ARCADE)), scale(SANDSTONE, 0.8))
    # String courses and the cornice.
    for y, h in ((PO_ARCADE - 6, 6), (PO_FIRST - 4, 4)):
        c.put(c.mask(box(x0 - 3, y, x1 + 3, y + h)), PAL["trim"])
        c.put(c.mask(box(x0 - 3, y + h - 1.2, x1 + 3, y + h)), scale(PAL["trim"], 0.7))
    c.put(c.mask(box(x0 - 8, PO_CORNICE - 2, x1 + 8, PO_CORNICE + 8)), PAL["trim"])
    c.put(c.mask(lambda p: [p.rect(x, PO_CORNICE + 8, x + 3, PO_CORNICE + 12) for x in np.arange(x0 - 4, x1 + 4, 7)]), scale(PAL["trim"], 0.82))
    c.put(c.mask(box(x0 - 8, PO_CORNICE - 2, x1 + 8, PO_CORNICE - 0.8)), (255, 255, 250), 0.6)
    k.eave_shade(x0, x1, PO_CORNICE + 12, 8, 0.25)
    # The windows: shuttered, with geraniums on the first floor.
    for cx in arches:
        k.window(cx, PO_FIRST + 22, 26, 58, "rect", shutters=SHUTTER, flowers=GERANIUM, tag=("po_w1", cx))
        k.window(cx, PO_SECOND + 26, 26, 54, "rect", shutters=SHUTTER, tag=("po_w2", cx))
    # The arcade: four round arches on piers; the door's is open, the others glazed.
    for cx in arches:
        ax0, ax1 = cx - 26, cx + 26
        c.put(c.mask(lambda p: p.arch(ax0 - 4, PO_ARCADE + 10, ax1 + 4, STREET)), PAL["trim"])
        inner = c.mask(lambda p: p.arch(ax0, PO_ARCADE + 14, ax1, STREET))
        c.put(inner, scale(SANDSTONE_DARK, 0.42))
        c.tone(inner * np.clip(1 - (c.y - PO_ARCADE - 14) / 60, 0, 1), -0.25)
        c.put(c.mask(lambda p: p.poly([(cx - 4, PO_ARCADE + 8), (cx + 4, PO_ARCADE + 8), (cx + 3, PO_ARCADE + 20), (cx - 3, PO_ARCADE + 20)])), PAL["stone_light"])
        if cx != PATENT_DOOR:
            k.window(cx, PO_ARCADE + 46, 34, 72, "arch", lit=0.35, tag=("po_arcade", cx))
            c.put(c.mask(box(cx - 22, STREET - 30, cx + 22, STREET - 27)), PAL["trim"])
    # A lantern under the door's arch, and the seal over it.
    c.put(c.mask(box(PATENT_DOOR - 0.5, PO_ARCADE + 14, PATENT_DOOR + 0.5, PO_ARCADE + 22)), PAL["iron"])
    c.put(c.mask(lambda p: p.poly([(PATENT_DOOR - 3, PO_ARCADE + 22), (PATENT_DOOR + 3, PO_ARCADE + 22), (PATENT_DOOR + 2, PO_ARCADE + 30), (PATENT_DOOR - 2, PO_ARCADE + 30)])), mix(PAL["lamp"], (255, 255, 230), 0.4))
    c.light(c.mask(lambda p: p.ellipse(PATENT_DOOR, PO_ARCADE + 27, 10), blur=5), PAL["lamp"], 0.5)
    sx, sy = PATENT_DOOR, PO_FIRST - 14
    # The gable over the door bay, with the clock in it.
    gx0, gx1 = PATENT_DOOR - 34, PATENT_DOOR + 34
    c.put(c.mask(lambda p: p.poly([(gx0, PO_CORNICE - 2), (gx1, PO_CORNICE - 2), (gx1, PO_CORNICE - 44), (PATENT_DOOR, PO_CORNICE - 76), (gx0, PO_CORNICE - 44)])), SANDSTONE)
    c.put(c.mask(lambda p: p.line([(gx0 - 3, PO_CORNICE - 43), (PATENT_DOOR, PO_CORNICE - 79), (gx1 + 3, PO_CORNICE - 43)], 3.2)), PAL["trim"])
    c.put(c.mask(lambda p: p.line([(PATENT_DOOR, PO_CORNICE - 79), (PATENT_DOOR, PO_CORNICE - 92)], 1.0)), PAL["iron"])
    c.put(c.mask(lambda p: p.ellipse(PATENT_DOOR, PO_CORNICE - 93, 2.2)), BRASS)
    clock_y = PO_CORNICE - 36
    c.put(c.mask(lambda p: p.ellipse(PATENT_DOOR, clock_y, 20)), PAL["trim"])
    c.put(c.mask(lambda p: p.ellipse(PATENT_DOOR, clock_y, 17)), (246, 242, 230))
    c.put(c.mask(lambda p: [p.rect(PATENT_DOOR + 14 * math.cos(a) - 0.8, clock_y + 14 * math.sin(a) - 0.8, PATENT_DOOR + 14 * math.cos(a) + 0.8, clock_y + 14 * math.sin(a) + 0.8) for a in np.linspace(0, math.tau, 13)[:-1]]), NAVY)
    # Its hands: ten past ten, and a second hand that is behind the others' time.
    c.put(c.mask(lambda p: (p.line([(PATENT_DOOR, clock_y), (PATENT_DOOR - 8, clock_y - 5)], 1.6), p.line([(PATENT_DOOR, clock_y), (PATENT_DOOR + 9, clock_y - 9)], 1.1))), NAVY)
    c.put(c.mask(lambda p: p.line([(PATENT_DOOR, clock_y), (PATENT_DOOR + 2, clock_y + 13)], 0.5)), GERANIUM)
    c.put(c.mask(lambda p: p.ellipse(PATENT_DOOR, clock_y, 1.4)), BRASS)
    # The seal: a brass medallion with the bulb, between laurel sprays.
    c.put(c.mask(lambda p: p.ellipse(sx, sy, 13)), BRASS)
    c.put(c.mask(lambda p: p.ellipse(sx, sy, 10.5)), scale(BRASS, 0.75))
    bulb(c, sx, sy - 2, 5.0, (255, 236, 170), 1.0)
    for side in (-1, 1):
        c.put(c.mask(lambda p: [p.ellipse(sx + side * (16 + i * 4), sy + 4 - i * 3.4, 3.2, 1.6) for i in range(5)]), PAL["leaf"])
    # Bollards and a bicycle stand on the street, by the arcade.
    for bx in (692, 968):
        c.put(c.mask(lambda p: (p.rect(bx - 3, STREET - 20, bx + 3, STREET), p.ellipse(bx, STREET - 20, 3))), PAL["iron"])


# ---------------------------------------------------------------------------
# The quad: the observatory on the lecture hall's terrace
# ---------------------------------------------------------------------------

DOME_DOOR = 2204
OB_X0, OB_X1 = 2088, 2320
OB_DRUM = 380
OB_DOME_R = 112


def observatory_front(c, k):
    """Carl Stargan's observatory on the terrace (y 576): a white drum with a
    band of gold constellations on navy, round windows, and a copper dome
    whose slit is open with the refractor's tube out of it."""
    k.ground = TERRACE
    cx = (OB_X0 + OB_X1) / 2
    # The dome: a copper hemisphere with its ribs, sunlit from the left.
    dome = c.mask(lambda p: p.ellipse(cx, OB_DRUM, OB_DOME_R + 4, OB_DOME_R)) * (c.y <= OB_DRUM)
    c.put(dome, COPPER)
    d = np.clip(((c.x - cx) ** 2 / (OB_DOME_R + 4) ** 2 + (c.y - OB_DRUM) ** 2 / OB_DOME_R**2), 0, 1)
    c.tone(dome * np.clip((c.x - cx) / OB_DOME_R, -1, 1), -0.22)
    c.tone(dome * (1 - d), 0.10)
    for f in (-0.8, -0.55, -0.28, 0.28, 0.55, 0.8):
        pts = [(cx + f * (OB_DOME_R + 4) * math.cos(t), OB_DRUM - OB_DOME_R * math.sin(t)) for t in np.linspace(0, math.pi / 2, 30)]
        c.put(c.mask(lambda p: p.line(pts, 1.0)) * dome, COPPER_DARK, 0.8)
    # Verdigris streaks.
    c.tone(dome * (c.noise("ob_verdigris", 30, 8, 2) - 0.5), 0.18)
    # The slit, open: its shutters drawn back and the dark inside.
    sx0, sx1 = cx + 10, cx + 40
    slit = c.mask(lambda p: p.poly([(sx0, OB_DRUM - 4), (sx1, OB_DRUM - 4), (sx1 - 8, OB_DRUM - OB_DOME_R + 4), (sx0 - 4, OB_DRUM - OB_DOME_R + 2)])) * dome
    c.put(slit, NIGHT)
    for ex in (sx0 - 5, sx1 + 1):
        c.put(c.mask(lambda p: p.poly([(ex, OB_DRUM - 4), (ex + 4, OB_DRUM - 4), (ex + (0 if ex < cx + 20 else -6), OB_DRUM - OB_DOME_R + 4), (ex - 4 + (0 if ex < cx + 20 else -6), OB_DRUM - OB_DOME_R + 4)])) * dome, mix(COPPER, (255, 255, 240), 0.25))
    # The refractor's tube out of the slit, to the up-right.
    t0, t1 = (cx + 24, OB_DRUM - 40), (cx + 66, OB_DRUM - OB_DOME_R - 46)
    c.put(c.mask(lambda p: p.line([t0, t1], 9)), DOME_WHITE)
    c.put(c.mask(lambda p: p.line([(t0[0] + 2, t0[1] + 2), (t1[0] + 2, t1[1] + 2)], 2)), scale(DOME_WHITE, 0.78))
    c.put(c.mask(lambda p: p.line([(t1[0] - 3.5, t1[1] + 3.5), (t1[0] + 3.5, t1[1] - 3.5)], 4)), BRASS)
    mid = (t0[0] + (t1[0] - t0[0]) * 0.55, t0[1] + (t1[1] - t0[1]) * 0.55)
    c.put(c.mask(lambda p: p.line([(mid[0] - 2, mid[1] + 5), (mid[0] + 2, mid[1] - 5)], 11)), BRASS)
    # The finial: a little brass comet.
    c.put(c.mask(lambda p: p.line([(cx, OB_DRUM - OB_DOME_R), (cx, OB_DRUM - OB_DOME_R - 16)], 1.2)), PAL["iron"])
    c.put(c.mask(lambda p: p.ellipse(cx, OB_DRUM - OB_DOME_R - 19, 3.2)), GOLD)
    c.put(c.mask(lambda p: p.poly([(cx + 2, OB_DRUM - OB_DOME_R - 21.5), (cx + 2, OB_DRUM - OB_DOME_R - 16.5), (cx + 16, OB_DRUM - OB_DOME_R - 23)])), GOLD, 0.8)
    # The drum: white stucco, a cornice, the constellation band.
    ashlar(c, OB_X0, OB_DRUM, OB_X1, TERRACE, DOME_WHITE, 12, 30, "ob_drum", 0.05)
    c.tone(c.mask(box(OB_X0, OB_DRUM, OB_X1, TERRACE)) * np.clip((c.x - cx) / ((OB_X1 - OB_X0) / 2), -1, 1) ** 3, -0.22)
    c.put(c.mask(box(OB_X0 - 6, OB_DRUM - 2, OB_X1 + 6, OB_DRUM + 6)), PAL["trim"])
    c.put(c.mask(box(OB_X0 - 6, OB_DRUM + 5, OB_X1 + 6, OB_DRUM + 6)), scale(PAL["trim"], 0.7))
    band0, band1 = OB_DRUM + 10, OB_DRUM + 38
    c.put(c.mask(box(OB_X0, band0, OB_X1, band1)), NAVY)
    stars(c, OB_X0, band0, OB_X1, band1, 60, "ob_band")
    for i, x in enumerate(np.arange(OB_X0 + 10, OB_X1 - 30, 46)):
        constellation(c, i, x, band0 + 5, 30, 18)
    c.put(c.mask(lambda p: (p.rect(OB_X0, band0, OB_X1, band0 + 1.2), p.rect(OB_X0, band1 - 1.2, OB_X1, band1))), GOLD)
    k.eave_shade(OB_X0, OB_X1, OB_DRUM + 6, 6, 0.22)
    # Round windows either side of the door, and a plinth course.
    for wx in (OB_X0 + 36, OB_X1 - 36):
        k.window(wx, band1 + 12, 26, 26, "round", lit=0.25, tag=("ob_port", wx))
    for wx in (OB_X0 + 36, OB_X1 - 36):
        k.window(wx, 488, 18, 44, "arch", lit=0.25, tag=("ob_slim", wx))
    c.put(c.mask(box(OB_X0 - 2, TERRACE - 12, OB_X1 + 2, TERRACE)), PAL["stone"])
    c.put(c.mask(box(OB_X0 - 2, TERRACE - 12, OB_X1 + 2, TERRACE - 11)), PAL["stone_light"])
    # The door's surround: an arch with a ringed planet in its keystone.
    c.put(c.mask(lambda p: p.arch(DOME_DOOR - 32, TERRACE - 124, DOME_DOOR + 32, TERRACE - 10)), PAL["trim"])
    recess = c.mask(lambda p: p.arch(DOME_DOOR - 27, TERRACE - 119, DOME_DOOR + 27, TERRACE - 10))
    c.put(recess, NAVY)
    c.tone(recess * np.clip(1 - (c.y - TERRACE + 119) / 50, 0, 1), -0.3)
    stars(c, DOME_DOOR - 27, TERRACE - 119, DOME_DOOR + 27, TERRACE - 10, 14, "ob_recess", clip=recess)
    py = TERRACE - 118
    c.put(c.mask(lambda p: p.ellipse(DOME_DOOR, py, 7)), GOLD)
    c.put(c.mask(lambda p: p.ellipse(DOME_DOOR, py, 13, 3.4)) * (1 - c.mask(lambda p: p.ellipse(DOME_DOOR, py, 10.5, 2.0))) * (1 - c.mask(lambda p: p.rect(DOME_DOOR - 7, py - 7, DOME_DOOR + 7, py)) * c.mask(lambda p: p.ellipse(DOME_DOOR, py, 7))), mix(GOLD, (255, 255, 240), 0.3))
    # A brass sundial on a post by the door: an observatory keeps the time.
    dx = OB_X0 - 22
    c.put(c.mask(box(dx - 4, TERRACE - 34, dx + 4, TERRACE)), PAL["stone"])
    c.put(c.mask(lambda p: p.ellipse(dx, TERRACE - 36, 10, 2.6)), BRASS)
    c.put(c.mask(lambda p: p.poly([(dx - 1, TERRACE - 37), (dx + 1, TERRACE - 37), (dx + 6, TERRACE - 46)])), scale(BRASS, 0.8))


# ---------------------------------------------------------------------------
# The patent office inside
# ---------------------------------------------------------------------------

PO_FLOOR, PO_CEILING = 576, 32
COUNTER_X0, COUNTER_X1, COUNTER_TOP = 480, 720, 536
CABINET_X0, CABINET_X1, CABINET_TOP = 820, 980, 480
GALLERY_X0, GALLERY_X1, GALLERY = 760, 1008, 400
WAINSCOT = 446


def patent_room(c, k):
    """The Patent Office (Third Class) inside: oak panelling under sage
    plaster, a tall window, the wall clock, the clerk's chalkboard, the
    pigeonholes over the counter, the card cabinet and the archive gallery
    with its shelf of patent models."""
    x0, x1 = 16, 1008
    g = PO_FLOOR
    k.ground = g
    k.wall(x0, PO_CEILING, x1, WAINSCOT, SAGE, "plaster", tag="po_in_wall")
    panels(c, x0, WAINSCOT, x1, g, OAK, 12, "po_wainscot")
    c.put(c.mask(box(x0, WAINSCOT - 3, x1, WAINSCOT + 3)), OAK_DARK)
    c.put(c.mask(box(x0, PO_CEILING + 40, x1, PO_CEILING + 44)), OAK)
    # A coffered ceiling: beams across.
    c.put(c.mask(box(x0, PO_CEILING, x1, PO_CEILING + 14)), OAK_DARK)
    c.put(c.mask(lambda p: [p.rect(x, PO_CEILING, x + 12, PO_CEILING + 22) for x in np.arange(x0 + 60, x1, 160)]), OAK_DARK)
    # The door out (its zone x 40..88, 96 tall): a frame and a transom.
    c.put(c.mask(box(32, g - 112, 96, g)), OAK_DARK)
    c.put(c.mask(box(36, g - 110, 92, g - 98)), PAPER_OLD)
    k.glass(c.mask(box(38, g - 108, 90, g - 100)), 0.0, g - 108, g - 100, "po_transom")
    # The hat stand, a bowler on it.
    hx = 128
    c.put(c.mask(lambda p: (p.rect(hx - 1.4, g - 120, hx + 1.4, g), p.line([(hx - 14, g), (hx, g - 12), (hx + 14, g)], 2))), OAK_DARK)
    c.put(c.mask(lambda p: [p.line([(hx, g - 116), (hx + s * 9, g - 124)], 1.6) for s in (-1, 1)]), OAK_DARK)
    c.put(c.mask(lambda p: (p.ellipse(hx + 8, g - 126, 8, 7), p.ellipse(hx + 8, g - 121, 12, 2.4))), (36, 34, 36))
    c.put(c.mask(box(hx - 2, g - 98, hx + 10, g - 60)), (70, 64, 60))  # a coat
    # The tall window on the town.
    k.window(220, 120, 64, 190, "arch", lit=0.0, frame=PAL["trim"], tag="po_in_window")
    # The wall clock with its pendulum.
    cx, cy = 316, 118
    c.put(c.mask(box(cx - 14, cy, cx + 14, cy + 86)), OAK)
    c.put(c.mask(lambda p: p.ellipse(cx, cy, 18)), OAK_DARK)
    c.put(c.mask(lambda p: p.ellipse(cx, cy, 15)), (246, 242, 230))
    c.put(c.mask(lambda p: [p.ellipse(cx + 12 * math.cos(a), cy + 12 * math.sin(a), 0.9) for a in np.linspace(0, math.tau, 13)[:-1]]), NAVY)
    c.put(c.mask(lambda p: (p.line([(cx, cy), (cx + 7, cy - 4)], 1.4), p.line([(cx, cy), (cx - 2, cy - 11)], 1.0))), NAVY)
    k.glass(c.mask(box(cx - 10, cy + 22, cx + 10, cy + 80)), 0.0, cy + 22, cy + 80, "po_clock_case")
    c.put(c.mask(lambda p: (p.line([(cx, cy + 22), (cx + 4, cy + 66)], 0.8), p.ellipse(cx + 4.4, cy + 69, 4.4))), BRASS)
    # The clerk's chalkboard: a train struck by lightning at both ends, a
    # light cone, and a clock running slow.
    bx0, by0, bx1, by1 = 340, 210, 470, 320
    c.put(c.mask(box(bx0 - 4, by0 - 4, bx1 + 4, by1 + 6)), OAK)
    board = c.mask(box(bx0, by0, bx1, by1))
    c.put(board, BOARD)
    c.tone(board * (c.noise("po_chalk_smudge", 8, 6, 3) - 0.5), 0.35)
    ty = by0 + 42
    c.put(c.mask(lambda p: (p.line([(bx0 + 10, ty), (bx0 + 70, ty), (bx0 + 70, ty - 12), (bx0 + 10, ty - 12), (bx0 + 10, ty)], 0.8),
                            [p.ring(x, ty + 3, 3, 0.7) for x in (bx0 + 20, bx0 + 34, bx0 + 46, bx0 + 60)],
                            p.line([(bx0 + 4, ty + 6), (bx0 + 78, ty + 6)], 0.6),
                            p.line([(bx0 + 6, by0 + 6), (bx0 + 12, by0 + 18), (bx0 + 8, by0 + 18), (bx0 + 13, ty - 13)], 0.8),
                            p.line([(bx0 + 74, by0 + 6), (bx0 + 68, by0 + 18), (bx0 + 72, by0 + 18), (bx0 + 67, ty - 13)], 0.8))), CHALK, 0.85)
    lx, ly = bx0 + 104, by0 + 50
    c.put(c.mask(lambda p: (p.line([(lx - 18, ly - 26), (lx + 18, ly + 26)], 0.7), p.line([(lx + 18, ly - 26), (lx - 18, ly + 26)], 0.7),
                            p.line([(lx, ly - 34), (lx, ly + 34)], 0.5))), CHALK, 0.85)
    for yy in (ly - 26, ly + 26):
        c.put(c.mask(lambda p: p.ellipse(lx, yy, 18, 3.6)) * (1 - c.mask(lambda p: p.ellipse(lx, yy, 17.2, 2.8))), CHALK, 0.85)
    c.put(c.mask(lambda p: (p.ring(bx0 + 30, by1 - 22, 12, 0.7), p.line([(bx0 + 30, by1 - 22), (bx0 + 30, by1 - 31)], 0.7), p.line([(bx0 + 30, by1 - 22), (bx0 + 37, by1 - 20)], 0.7),
                            p.line([(bx0 + 48, by1 - 22), (bx0 + 62, by1 - 22)], 0.7), p.line([(bx0 + 58, by1 - 25), (bx0 + 62, by1 - 22), (bx0 + 58, by1 - 19)], 0.7),
                            p.ring(bx0 + 82, by1 - 22, 14, 0.7), p.line([(bx0 + 82, by1 - 22), (bx0 + 82, by1 - 32)], 0.7))), CHALK, 0.85)
    c.put(c.mask(box(bx0, by1, bx1, by1 + 4)), OAK_LIGHT)
    c.put(c.mask(box(bx0 + 20, by1 - 1.5, bx0 + 28, by1 + 0.5)), CHALK)
    # The pigeonholes over the counter, stuffed with applications.
    px0, py0, px1, py1 = COUNTER_X0, 96, COUNTER_X1 + 20, 404
    c.put(c.mask(box(px0 - 6, py0 - 8, px1 + 6, py1 + 4)), OAK_DARK)
    rng = c.rand("pigeonholes")
    cw, ch = 26.0, 28.0
    b = Batch(c)
    for yy in np.arange(py0, py1 - ch + 1, ch):
        for xx in np.arange(px0, px1 - cw + 1, cw):
            b.add(scale(OAK_DARK, 0.45), 1.0, box(xx + 1.6, yy + 1.6, xx + cw - 1.6, yy + ch - 1.6))
            kind = rng.random()
            floor_y = yy + ch - 1.6
            if kind < 0.45:  # rolled applications, ends out, tied with ribbon
                for i in range(rng.choice((1, 2, 3, 3))):
                    ry = floor_y - 4.4 - i * 4.6
                    x_end = xx + rng.uniform(4, 7)
                    b.add(rng.choice((PAPER, PAPER_OLD)), 1.0, lambda p, ry=ry, x_end=x_end, xx=xx: p.rect(x_end, ry, xx + cw - 2.4, ry + 4.2))
                    b.add(scale(PAPER_OLD, 0.78), 1.0, lambda p, ry=ry, x_end=x_end: p.ellipse(x_end, ry + 2.1, 1.6, 2.1))
                    b.add(RIBBON, 1.0, lambda p, ry=ry, xx=xx: p.rect(xx + cw * 0.6, ry, xx + cw * 0.6 + 1.6, ry + 4.2))
            elif kind < 0.85:  # a stack of folded papers
                n = rng.choice((2, 3, 4, 5))
                for i in range(n):
                    sy = floor_y - (i + 1) * 2.6
                    dx = rng.uniform(-1.5, 1.5)
                    b.add(rng.choice((PAPER, PAPER_OLD, (222, 214, 236))), 1.0, lambda p, sy=sy, dx=dx, xx=xx: p.rect(xx + 3.5 + dx, sy, xx + cw - 3.5 + dx, sy + 2.2))
                if rng.random() < 0.5:
                    b.add(RIBBON, 1.0, lambda p, xx=xx, top=floor_y - n * 2.6, bot=floor_y: p.rect(xx + cw / 2 - 0.8, top, xx + cw / 2 + 0.8, bot))
    b.draw()
    c.put(c.mask(lambda p: ([p.rect(px0, y, px1, y + 1.6) for y in np.arange(py0, py1 + 1, ch)], [p.rect(x, py0, x + 1.6, py1) for x in np.arange(px0, px1 + 1, cw)])), OAK)
    # The counter: panelled oak, its top the walk line (y 536), the
    # clerk's things on it.
    panels(c, COUNTER_X0, COUNTER_TOP, COUNTER_X1, g, OAK, 4, "po_counter")
    edge_line(c, COUNTER_X0 - 6, COUNTER_X1 + 6, COUNTER_TOP, OAK_LIGHT, 6)
    # A green-shaded lamp, the in and out trays, the stamp rack and the bell.
    lx = 520
    c.put(c.mask(lambda p: (p.rect(lx - 6, COUNTER_TOP - 3, lx + 6, COUNTER_TOP), p.rect(lx - 0.8, COUNTER_TOP - 22, lx + 0.8, COUNTER_TOP - 3))), BRASS)
    c.put(c.mask(lambda p: p.poly([(lx - 13, COUNTER_TOP - 22), (lx + 13, COUNTER_TOP - 22), (lx + 9, COUNTER_TOP - 30), (lx - 9, COUNTER_TOP - 30)])), (40, 112, 70))
    c.light(c.mask(lambda p: p.ellipse(lx, COUNTER_TOP - 14, 22, 10), blur=6), PAL["lamp"], 0.45)
    for tx, stack in ((580, 4), (606, 9)):
        c.put(c.mask(lambda p: (p.rect(tx - 10, COUNTER_TOP - 6, tx + 10, COUNTER_TOP), p.rect(tx - 10, COUNTER_TOP - 6 - stack, tx + 10, COUNTER_TOP - 6))), BRASS)
        c.put(c.mask(box(tx - 9, COUNTER_TOP - 6 - stack + 0.8, tx + 9, COUNTER_TOP - 6)), PAPER)
        c.put(c.mask(lambda p: [p.rect(tx - 9, y, tx + 9, y + 0.4) for y in np.arange(COUNTER_TOP - 6 - stack + 2, COUNTER_TOP - 6, 1.6)]), PAPER_OLD)
    rx = 664
    c.put(c.mask(lambda p: (p.rect(rx - 12, COUNTER_TOP - 3, rx + 12, COUNTER_TOP), p.rect(rx - 0.8, COUNTER_TOP - 18, rx + 0.8, COUNTER_TOP - 3), p.rect(rx - 12, COUNTER_TOP - 18, rx + 12, COUNTER_TOP - 16))), OAK_DARK)
    for i, sx in enumerate(np.arange(rx - 10, rx + 11, 5)):
        c.put(c.mask(lambda p: (p.ellipse(sx, COUNTER_TOP - 13, 1.6), p.rect(sx - 0.6, COUNTER_TOP - 12, sx + 0.6, COUNTER_TOP - 8), p.rect(sx - 2, COUNTER_TOP - 8, sx + 2, COUNTER_TOP - 6))), (RIBBON, (60, 70, 140), (40, 40, 44))[i % 3])
    bx = 702
    c.put(c.mask(lambda p: (p.rect(bx - 7, COUNTER_TOP - 2, bx + 7, COUNTER_TOP), p.ellipse(bx, COUNTER_TOP - 3, 5.5, 5), p.rect(bx - 0.6, COUNTER_TOP - 11, bx + 0.6, COUNTER_TOP - 7))), BRASS)
    c.put(c.mask(lambda p: p.ellipse(bx - 2, COUNTER_TOP - 5, 1.6, 1.2)), (255, 240, 200), 0.7)
    # The card cabinet: drawers with brass pulls, its top the walk line (y 480).
    c.put(c.mask(box(CABINET_X0, CABINET_TOP, CABINET_X1, g)), OAK)
    c.tone(c.mask(box(CABINET_X0, CABINET_TOP, CABINET_X1, g)) * (c.noise("po_cab", 6, 20, 2) - 0.5), 0.2)
    b = Batch(c)
    for yy in np.arange(CABINET_TOP + 8, g - 10, 15):
        for xx in np.arange(CABINET_X0 + 4, CABINET_X1 - 18, 19):
            b.add(mix(OAK, (255, 236, 200), 0.08), 1.0, box(xx, yy, xx + 17, yy + 13))
            b.add(scale(OAK, 0.6), 1.0, box(xx, yy + 12, xx + 17, yy + 13))
            b.add(PAPER, 1.0, box(xx + 5, yy + 3, xx + 12, yy + 6))
            b.add(BRASS, 1.0, lambda p, xx=xx, yy=yy: p.ellipse(xx + 8.5, yy + 9, 2.2, 1.2))
    b.draw()
    c.put(c.mask(box(CABINET_X0, g - 10, CABINET_X1, g)), OAK_DARK)
    edge_line(c, CABINET_X0 - 4, CABINET_X1 + 4, CABINET_TOP, OAK_LIGHT, 6)
    # The archive gallery (y 400) on brackets, its rail behind the play,
    # and over it the shelves of the archive to the ceiling.
    b = Batch(c)
    for sy in np.arange(PO_CEILING + 60, GALLERY - 10, 56):
        b.add(OAK_DARK, 1.0, box(GALLERY_X0 + 10, sy, x1, sy + 5))
        books(b, c.rand("archive", sy), GALLERY_X0 + 14, x1 - 14, sy, 30, 46, 7, 14)
    b.draw()
    # The shelf of patent models on the gallery's back wall.
    my = GALLERY - 46
    c.put(c.mask(box(GALLERY_X0 + 20, my, GALLERY_X0 + 210, my + 5)), OAK_LIGHT)
    wx, wy = GALLERY_X0 + 50, my - 22  # the wheel that would turn for ever
    c.put(c.mask(lambda p: (p.ring(wx, wy, 18, 1.4), [p.line([(wx, wy), (wx + 18 * math.cos(a), wy + 18 * math.sin(a))], 0.8) for a in np.linspace(0, math.tau, 9)[:-1]], p.poly([(wx - 2, wy), (wx + 2, wy), (wx + 6, my), (wx - 6, my)]))), BRASS)
    c.put(c.mask(lambda p: [p.ellipse(wx + 18 * math.cos(a), wy + 18 * math.sin(a), 2.6) for a in np.linspace(0, math.tau, 9)[:-1]]), (80, 82, 90))
    fx, fy = GALLERY_X0 + 120, my - 26  # a flying machine
    c.put(c.mask(lambda p: (p.rect(fx - 22, fy - 1, fx + 22, fy + 1), p.rect(fx - 22, fy + 9, fx + 22, fy + 11), [p.rect(x - 0.4, fy, x + 0.4, fy + 10) for x in (fx - 18, fx - 6, fx + 6, fx + 18)], p.line([(fx + 22, fy + 5), (fx + 34, fy + 5)], 0.8), p.rect(fx + 32, fy + 1, fx + 35, fy + 9))), PAPER_OLD)
    c.put(c.mask(lambda p: p.line([(fx, fy + 11), (fx, my)], 0.6)), OAK_DARK)
    bulb(c, GALLERY_X0 + 180, my - 20, 8.0, (255, 236, 170), 1.2)
    c.light(c.mask(lambda p: p.ellipse(GALLERY_X0 + 180, my - 20, 14), blur=6), PAL["lamp"], 0.35)
    c.put(c.mask(box(GALLERY_X0 + 172, my - 6, GALLERY_X0 + 188, my)), OAK_DARK)
    # The gallery's floor and brackets, the rail behind, the library ladder.
    edge_line(c, GALLERY_X0, x1, GALLERY, OAK_LIGHT, 8)
    c.put(c.mask(lambda p: [p.poly([(x, GALLERY + 8), (x + 4, GALLERY + 8), (x + 2, GALLERY + 28)]) for x in np.arange(GALLERY_X0 + 10, x1, 60)]), OAK_DARK)
    rail = c.mask(lambda p: (p.rect(GALLERY_X0, GALLERY - 30, x1, GALLERY - 28), [p.rect(x, GALLERY - 30, x + 1.2, GALLERY) for x in np.arange(GALLERY_X0 + 2, x1, 10)]))
    c.put(rail, BRASS, 0.8)
    c.put(c.mask(lambda p: (p.line([(GALLERY_X0 + 4, GALLERY - 34), (GALLERY_X0 - 36, CABINET_TOP)], 2.0), p.line([(GALLERY_X0 + 18, GALLERY - 34), (GALLERY_X0 - 22, CABINET_TOP)], 2.0),
                            [p.line([(GALLERY_X0 + 4 - 40 * t, GALLERY - 34 + (CABINET_TOP - GALLERY + 34) * t), (GALLERY_X0 + 18 - 40 * t, GALLERY - 34 + (CABINET_TOP - GALLERY + 34) * t)], 1.2) for t in np.linspace(0.08, 0.92, 7)])), OAK_LIGHT)
    # The lamps.
    for lx in (430, 620, 900):
        pendant(c, lx, PO_CEILING + 14, 50 if lx != 900 else 30)


# ---------------------------------------------------------------------------
# The observatory inside
# ---------------------------------------------------------------------------

OBS_W, OBS_FLOOR = 1280, 960
PLATFORM_X0, PLATFORM_X1, PLATFORM = 320, 800, 320
#: The stair up the wall: each tread's left x and its top (the room's ledges).
TREADS = tuple((x, OBS_FLOOR - 80 * (i + 1)) for i, x in enumerate((240, 480, 720, 960, 720, 480, 240)))
TREAD_W = 160
SLIT_X0, SLIT_X1 = 600, 690


def observatory_room(c, k):
    """The observatory inside, at night: the dome's vault painted with a star
    map and open at the slit; the stair of treads with red observing lamps,
    the platform and the refractor; a golden record and a pale blue dot on
    the wall, an orrery, a bookcase."""
    x0, x1 = 16, OBS_W - 16
    g = OBS_FLOOR
    k.ground = g
    full = c.mask(box(0, 0, OBS_W, g))
    c.paint(full, c.ramp([(0, NIGHT), (600, (24, 30, 58)), (g, (40, 40, 60))]))
    # The vault: ribs from the slit down to the drum's ring at y 560.
    cx = (SLIT_X0 + SLIT_X1) / 2
    ring_y = 560
    # Each rib a meridian of the dome seen from under it: it leaves the slit
    # level, bulges out and comes down steep to the ring.
    ribs = []
    for a in (-1.0, -0.72, -0.45, -0.2, 0.2, 0.45, 0.72, 1.0):
        top_x = cx + math.copysign(60, a)
        bot_x = cx + a * 700
        ribs.append([(top_x + (bot_x - top_x) * math.sin(t), ring_y * (1 - math.cos(t)) ** 0.8) for t in np.linspace(0, math.pi / 2, 48)])
    c.put(c.mask(lambda p: [p.line(pts, 7) for pts in ribs]), NIGHT_RIB)
    c.put(c.mask(lambda p: [p.line([(x + 3, y) for x, y in pts], 1.2) for pts in ribs]), mix(NIGHT_RIB, (120, 140, 200), 0.25))
    # The star map painted on the vault: gold figures, faint.
    rng = c.rand("vault_map")
    for i in range(16):
        fx, fy = rng.uniform(60, OBS_W - 140), rng.uniform(60, ring_y - 80)
        if SLIT_X0 - 60 < fx < SLIT_X1 + 10:
            continue
        constellation(c, i, fx, fy, rng.uniform(50, 80), rng.uniform(30, 50), mix(GOLD, NIGHT, 0.35), 0.9, 1.8)
    stars(c, 20, 20, OBS_W - 20, ring_y, 220, "vault_dots", colour=mix(GOLD, (255, 255, 255), 0.4))
    # The drum's wall below the ring: boards of deep blue, the ring a brass track.
    ashlar(c, x0, ring_y, x1, g, (46, 52, 84), 14, 40, "obs_drum", 0.06)
    c.put(c.mask(box(0, ring_y - 6, OBS_W, ring_y + 6)), scale(BRASS, 0.8))
    c.put(c.mask(lambda p: [p.ellipse(x, ring_y, 3.2) for x in np.arange(20, OBS_W, 40)]), BRASS)
    c.put(c.mask(box(0, ring_y - 6, OBS_W, ring_y - 4.8)), mix(BRASS, (255, 255, 230), 0.4))
    # The slit, open on the night sky, the stars and the station's pale dot.
    slit = c.mask(box(SLIT_X0, 0, SLIT_X1, 300))
    c.paint(slit, c.ramp([(0, (4, 6, 20)), (300, (20, 30, 70))]))
    stars(c, SLIT_X0, 0, SLIT_X1, 300, 70, "slit_stars", clip=slit)
    c.put(c.mask(box(cx + 14, 0, cx + 15, 300)) * slit, (220, 232, 255), 0.35)  # the tether
    c.put(c.mask(lambda p: p.ellipse(cx + 14.5, 40, 2.4)), (230, 240, 255))
    c.light(c.mask(lambda p: p.ellipse(cx + 14.5, 40, 9), blur=4), (190, 210, 255), 0.6)
    for ex, sgn in ((SLIT_X0, -1), (SLIT_X1, 1)):
        c.put(c.mask(box(ex - (14 if sgn < 0 else 0), 0, ex + (0 if sgn < 0 else 14), 306)), (64, 72, 104))
        c.put(c.mask(box(ex - (14 if sgn < 0 else 0), 0, ex - (12 if sgn < 0 else -2), 306)), (100, 110, 150))
    # Wall pieces: the golden record, the pale blue dot, a star chart, the bookcase.
    gx, gy = 1190, 640
    c.put(c.mask(box(gx - 46, gy - 46, gx + 46, gy + 46)), OAK_DARK)
    c.put(c.mask(box(gx - 42, gy - 42, gx + 42, gy + 42)), (20, 22, 30))
    c.put(c.mask(lambda p: p.ellipse(gx, gy, 34)), GOLD)
    c.put(c.mask(lambda p: [p.ring(gx, gy, r, 0.5) for r in np.arange(12, 34, 2.6)]), scale(GOLD, 0.8), 0.8)
    c.put(c.mask(lambda p: p.ellipse(gx, gy, 9)), mix(GOLD, (255, 255, 230), 0.4))
    c.put(c.mask(lambda p: (p.ring(gx, gy, 4.5, 0.6), [p.line([(gx, gy), (gx + 7 * math.cos(a), gy + 7 * math.sin(a))], 0.4) for a in np.linspace(0, math.tau, 8)[:-1]])), scale(GOLD, 0.6))
    c.put(c.mask(lambda p: p.poly([(gx - 30, gy - 30), (gx - 10, gy - 34), (gx - 34, gy - 10)])), (255, 255, 255), 0.25)
    dx, dy = 1190, 450
    c.put(c.mask(box(dx - 36, dy - 50, dx + 36, dy + 50)), OAK_DARK)
    c.put(c.mask(box(dx - 32, dy - 46, dx + 32, dy + 46)), (12, 12, 18))
    beams = c.mask(lambda p: [p.poly([(dx - 32 + o, dy - 46), (dx - 22 + o, dy - 46), (dx + 10 + o, dy + 46), (dx + o, dy + 46)]) for o in (-8, 12, 30)])
    c.paint(beams * c.mask(box(dx - 32, dy - 46, dx + 32, dy + 46)), c.ramp([(dy - 46, (230, 170, 120)), (dy + 46, (150, 100, 110))]), 0.3)
    c.put(c.mask(lambda p: p.ellipse(dx + 4, dy + 6, 1.4)), (150, 200, 255))
    c.light(c.mask(lambda p: p.ellipse(dx + 4, dy + 6, 4), blur=2), (150, 200, 255), 0.4)
    # The star chart on the west wall: a round planisphere.
    sx, sy = 120, 620
    c.put(c.mask(lambda p: p.ellipse(sx, sy, 56)), BRASS)
    c.put(c.mask(lambda p: p.ellipse(sx, sy, 52)), NAVY)
    stars(c, sx - 50, sy - 50, sx + 50, sy + 50, 70, "planisphere", clip=c.mask(lambda p: p.ellipse(sx, sy, 50)))
    for i, (ox, oy) in enumerate(((-30, -26), (6, -34), (-12, 6), (14, 14))):
        constellation(c, i, sx + ox, sy + oy, 26, 18, GOLD, 0.5, 1.0)
    c.put(c.mask(lambda p: (p.ring(sx, sy, 40, 0.6), p.line([(sx - 52, sy), (sx + 52, sy)], 0.5))), mix(GOLD, NAVY, 0.4))
    # The bookcase by the door.
    bx0, bx1, by0 = 110, 224, 760
    c.put(c.mask(box(bx0, by0, bx1, g)), OAK_DARK)
    b = Batch(c)
    for i, sy_ in enumerate(np.arange(by0 + 44, g - 4, 40)):
        b.add(scale(OAK_DARK, 0.5), 1.0, box(bx0 + 4, sy_ - 38, bx1 - 4, sy_))
        b.draw()
        books(b, c.rand("obs_books", i), bx0 + 6, bx1 - 12, sy_, 24, 36, 5, 10)
        b.add(OAK, 1.0, box(bx0, sy_, bx1, sy_ + 4))
    b.draw()
    # The orrery on its table: the sun and the planets on their arms.
    ox, oy = 1120, g - 64
    c.put(c.mask(lambda p: (p.rect(ox - 34, oy + 26, ox + 34, oy + 31), p.rect(ox - 3, oy + 31, ox + 3, g - 4), p.rect(ox - 16, g - 4, ox + 16, g))), OAK)
    c.put(c.mask(lambda p: (p.rect(ox - 1.2, oy, ox + 1.2, oy + 26), p.ellipse(ox, oy + 24, 10, 2.4))), BRASS)
    c.put(c.mask(lambda p: p.ellipse(ox, oy - 2, 7)), (255, 200, 90))
    c.light(c.mask(lambda p: p.ellipse(ox, oy - 2, 14), blur=5), (255, 200, 90), 0.5)
    for r, a, pr, col in ((14, 0.4, 2.0, (200, 180, 160)), (22, 2.2, 2.6, (230, 190, 120)), (31, 4.0, 3.0, (90, 150, 220)), (40, 5.4, 2.4, (210, 100, 70)), (52, 1.2, 5.0, (220, 180, 130))):
        px_, py_ = ox + r * math.cos(a), oy - 2 + r * math.sin(a) * 0.32
        c.put(c.mask(lambda p: (p.line([(ox, oy - 2), (px_, py_)], 0.5), p.line([(px_, py_), (px_, py_ - 4)], 0.5))), BRASS)
        c.put(c.mask(lambda p: p.ellipse(px_, py_ - 4 - pr, pr)), col)
    c.put(c.mask(lambda p: p.ellipse(ox + 52 * math.cos(1.2), oy - 2 + 52 * math.sin(1.2) * 0.32 - 9, 9, 2)) * (1 - c.mask(lambda p: p.ellipse(ox + 52 * math.cos(1.2), oy - 2 + 52 * math.sin(1.2) * 0.32 - 9, 6.5, 1.2))), (240, 220, 170), 0.8)
    # The platform (y 320): an iron catwalk on two columns, its rail behind.
    for px_ in (PLATFORM_X0 + 24, PLATFORM_X1 - 24):
        c.put(c.mask(box(px_ - 6, PLATFORM + 8, px_ + 6, g)), (60, 64, 80))
        c.put(c.mask(box(px_ - 6, PLATFORM + 8, px_ - 4, g)), (96, 104, 130))
    c.put(c.mask(lambda p: [p.line([(PLATFORM_X0 + 24, PLATFORM + 40 + y), (PLATFORM_X1 - 24, PLATFORM + 80 + y)], 1.6) for y in (0, 200, 400)] + [p.line([(PLATFORM_X1 - 24, PLATFORM + 40 + y), (PLATFORM_X0 + 24, PLATFORM + 80 + y)], 1.6) for y in (0, 200, 400)]), (60, 64, 80), 0.8)
    c.put(c.mask(box(PLATFORM_X0, PLATFORM, PLATFORM_X1, PLATFORM + 12)), (70, 74, 92))
    c.put(c.mask(lambda p: [p.rect(x, PLATFORM + 2, x + 1, PLATFORM + 12) for x in np.arange(PLATFORM_X0 + 4, PLATFORM_X1, 8)]), (40, 44, 58))
    c.put(c.mask(box(PLATFORM_X0, PLATFORM, PLATFORM_X1, PLATFORM + 1.6)), (170, 180, 210))
    c.put(c.mask(lambda p: (p.rect(PLATFORM_X0, PLATFORM - 34, PLATFORM_X1, PLATFORM - 32), [p.rect(x, PLATFORM - 34, x + 1.4, PLATFORM) for x in np.arange(PLATFORM_X0 + 2, PLATFORM_X1, 24)])), BRASS, 0.8)
    # The refractor: a pier on the platform, the mount, the long white tube
    # up at the slit, its counterweight, and the eyepiece low for Stargan.
    mx, my = 600, PLATFORM - 70
    c.put(c.mask(lambda p: p.poly([(mx - 22, PLATFORM), (mx + 22, PLATFORM), (mx + 12, my + 10), (mx - 12, my + 10)])), (210, 214, 222))
    c.tone(c.mask(lambda p: p.poly([(mx, PLATFORM), (mx + 22, PLATFORM), (mx + 12, my + 10), (mx, my + 10)])), -0.2)
    c.put(c.mask(lambda p: p.ellipse(mx, my + 4, 16, 12)), BRASS)
    t_lo, t_hi = (mx - 100, my + 58), (cx + 10, 60)
    c.put(c.mask(lambda p: p.line([t_lo, t_hi], 22)), DOME_WHITE)
    c.put(c.mask(lambda p: p.line([(t_lo[0] + 5, t_lo[1] + 6), (t_hi[0] + 5, t_hi[1] + 6)], 5)), scale(DOME_WHITE, 0.72))
    c.put(c.mask(lambda p: p.line([(t_lo[0] - 3, t_lo[1] - 3), (t_hi[0] - 3, t_hi[1] - 3)], 3)), (255, 255, 255), 0.6)
    for t in (0.0, 0.42, 1.0):
        bxp, byp = t_lo[0] + (t_hi[0] - t_lo[0]) * t, t_lo[1] + (t_hi[1] - t_lo[1]) * t
        dxn, dyn = t_hi[1] - t_lo[1], -(t_hi[0] - t_lo[0])
        n = math.hypot(dxn, dyn)
        dxn, dyn = dxn / n * 13, dyn / n * 13
        c.put(c.mask(lambda p: p.line([(bxp - dxn, byp - dyn), (bxp + dxn, byp + dyn)], 6 if t == 1.0 else 4)), BRASS)
    c.put(c.mask(lambda p: (p.line([(t_lo[0], t_lo[1]), (t_lo[0] - 8, t_lo[1] + 14)], 4), p.ellipse(t_lo[0] - 9, t_lo[1] + 16, 3.4))), (40, 40, 46))
    c.put(c.mask(lambda p: (p.line([(mx, my + 4), (mx + 46, my + 48)], 3), p.ellipse(mx + 50, my + 52, 9))), (90, 96, 110))
    # The finder scope beside the tube.
    c.put(c.mask(lambda p: p.line([(t_lo[0] + 60 - 14, t_lo[1] - 30 - 14), (t_lo[0] + 160 - 14, t_lo[1] - 80 - 14)], 5)), (60, 64, 74))
    # The stair of treads up the wall, each on two iron brackets, a red
    # observing lamp under every other one.
    for i, (tx, ty) in enumerate(TREADS):
        c.put(c.mask(lambda p: [p.poly([(bx_, ty + 6), (bx_ + 4, ty + 6), (bx_ + 24 * (1 if bx_ < tx + TREAD_W / 2 else -1), ty + 40), (bx_ + 24 * (1 if bx_ < tx + TREAD_W / 2 else -1) - 3, ty + 40)]) for bx_ in (tx + 16, tx + TREAD_W - 20)]), (60, 64, 80))
        edge_line(c, tx, tx + TREAD_W, ty, OAK, 7)
        if i % 2 == 0:
            lx = tx + TREAD_W / 2
            c.put(c.mask(lambda p: p.rect(lx - 4, ty + 7, lx + 4, ty + 11)), (40, 40, 46))
            c.put(c.mask(lambda p: p.ellipse(lx, ty + 12, 2.6, 1.6)), RED_LAMP)
            c.light(c.mask(lambda p: p.ellipse(lx, ty + 26, 40, 22), blur=14), RED_LAMP, 0.22)
    # The door out (its zone x 40..88): a frame of brass rivets.
    c.put(c.mask(box(32, g - 110, 96, g)), (64, 70, 96))
    c.put(c.mask(lambda p: [p.ellipse(x, y, 1.6) for x in (36, 92) for y in np.arange(g - 104, g, 12)]), BRASS)
    # A desk lamp's pool on the floor by the orrery.
    c.light(c.mask(lambda p: p.ellipse(ox, g - 50, 80, 50), blur=26), PAL["lamp"], 0.16)


PIECES: Dict[str, Piece] = {
    # The quad.
    "eureka_patent_front": Piece((PO_X0 - 14, PO_CORNICE - 100, PO_X1 + 14, STREET), patent_front),
    "eureka_observatory_front": Piece((OB_X0 - 36, OB_DRUM - OB_DOME_R - 60, OB_X1 + 10, TERRACE), observatory_front),
    # Inside.
    "eureka_patent_room": Piece((16, PO_CEILING, 1008, PO_FLOOR), patent_room),
    "eureka_observatory_room": Piece((0, 0, OBS_W, OBS_FLOOR), observatory_room),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PAL", "PIECES", "TARGETS"]
