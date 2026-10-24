"""Scenery of the Pirate Port (gate address SAILING): a lived-in harbour town.

The rooms are `pirate_port_gate_plaza`, `pirate_port_waterfront`,
`pirate_port_tavern` and `pirate_port_docks`
(`tools/ambition_ldtk_tools/specs/pirate_port/make_specs.py`). Each piece is
drawn in its room's coordinates (`_district_props`): where the room places a
walk line (a gallery, a roof, a yard of the brig, the gantry), the piece
draws the light top edge of the thing that is walked on at that y.

- The plaza: the harbour house with its balcony (y 448) and the stone stair
  up to it; the dock clerk's freight booth and the ring's crates.
- The waterfront: timber-and-plaster houses with one long gallery (y 512),
  the stair to it, the chandler's stall, the front of The Drowned Compass,
  the chandlery and the net loft with roof terraces (y 448, 384).
- The tavern: its back wall, back bar, counter (y 344) and tables.
- The docks: the bonded warehouse (roof y 448), the gantry and its crane
  (y 384), and the brig PERSISTENCE: her hull (deck y 640), two masts, the
  yards (y 528, 416), the crow's nest (y 304), the signal rope (y 416).
- Small things: lamp posts, barrels and rope, and the clerk's page (the
  pickup of the port's problem).

Animations: ``idle``, 1 frame each.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale

PAL = {
    "stone": (168, 154, 134), "stone_light": (226, 214, 190), "trim": (232, 222, 198), "dark": (40, 44, 52),
    "glass_top": (120, 170, 196), "glass_low": (52, 82, 104), "lamp": (255, 206, 130), "wood": (96, 66, 44),
    "leaf": (78, 120, 70), "iron": (40, 40, 44), "brass": (198, 150, 70), "glaze": (210, 170, 80),
}
PLASTER = (232, 214, 182)
PLASTER_BLUE = (186, 206, 214)
PLASTER_OCHRE = (222, 186, 128)
PLASTER_ROSE = (214, 160, 138)
TIMBER = (70, 48, 34)
PLANK = (132, 96, 64)
PLANK_DARK = (88, 62, 42)
PLANK_LIGHT = (182, 142, 96)
ROOF_RED = (164, 78, 54)
ROOF_OCHRE = (184, 128, 66)
ROOF_SLATE = (78, 86, 96)
HULL = (92, 58, 38)
HULL_DARK = (56, 36, 26)
HULL_BAND = (196, 160, 82)
SAIL = (234, 224, 198)
ROPE = (176, 146, 98)
TAR = (36, 30, 26)
SEA_GREEN = (64, 112, 104)
NAVY = (38, 56, 82)
RED_PAINT = (168, 52, 44)


def planks(c, k, x0, y0, x1, y1, colour, step=6.0, vertical=False, tag="planks"):
    """A face of boards with their joints and grain."""
    m = c.mask(box(x0, y0, x1, y1))
    c.put(m, colour)
    if vertical:
        joints = c.mask(lambda p: [p.rect(x, y0, x + 0.6, y1) for x in np.arange(x0 + step, x1, step)])
        grain = c.noise((tag, "grain"), (x1 - x0) / step, 4, 2)
    else:
        joints = c.mask(lambda p: [p.rect(x0, y, x1, y + 0.6) for y in np.arange(y0 + step, y1, step)])
        grain = c.noise((tag, "grain"), 6, (y1 - y0) / step, 2)
    c.put(joints * m, scale(colour, 0.62), 0.9)
    c.tone(m * (grain - 0.5), 0.22)
    return m


def deck_edge(c, x0, x1, y, colour=PLANK):
    """The walked edge of a deck at `y`: a thick board whose top is the light line."""
    c.put(c.mask(box(x0, y, x1, y + 5)), colour)
    c.put(c.mask(box(x0, y, x1, y + 1.2)), mix(colour, (255, 236, 200), 0.5))
    c.put(c.mask(box(x0, y + 4, x1, y + 5)), scale(colour, 0.55))


def post(c, x, y0, y1, w=4.0, colour=TIMBER):
    c.put(c.mask(box(x - w / 2, y0, x + w / 2, y1)), colour)
    c.put(c.mask(box(x - w / 2, y0, x - w / 2 + 0.8, y1)), mix(colour, (255, 230, 190), 0.25))


def rope_line(c, pts, w=1.2, colour=ROPE):
    c.put(c.mask(lambda p: p.line(pts, w)), colour)


def sag(a, b, s, n=24):
    return [(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t + s * 4 * t * (1 - t)) for t in np.linspace(0, 1, n)]


def crate(c, x0, y0, x1, y1, colour=PLANK, mark=None):
    m = c.mask(box(x0, y0, x1, y1))
    c.put(m, colour)
    c.put(c.mask(lambda p: (p.rect(x0, y0, x1, y0 + 2.4), p.rect(x0, y1 - 2.4, x1, y1), p.rect(x0, y0, x0 + 2.4, y1), p.rect(x1 - 2.4, y0, x1, y1),
                            p.line([(x0 + 2, y1 - 2), (x1 - 2, y0 + 2)], 2.0))), scale(colour, 0.7))
    c.put(c.mask(box(x0, y0, x1, y0 + 1.0)), mix(colour, (255, 236, 200), 0.45))
    c.tone(m * (c.noise(("crate", x0, y0), 3, 6, 2) - 0.5), 0.2)
    if mark:
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        c.put(c.mask(lambda p: (p.rect(cx - 7, cy - 4, cx + 7, cy + 4))), mix(colour, (240, 230, 200), 0.55), 0.8)
        c.put(c.mask(lambda p: p.line([(cx - 5, cy), (cx + 5, cy)], 1.2)), mark, 0.9)


def barrel(c, x, ground, w=16, h=22):
    m = c.mask(lambda p: p.ellipse(x, ground - h / 2, w / 2, h / 2))
    m = np.maximum(m, c.mask(box(x - w / 2 + 1, ground - h + 3, x + w / 2 - 1, ground - 3)))
    c.put(m, PLANK)
    c.put(c.mask(lambda p: [p.rect(x - w / 2, y, x + w / 2, y + 1.6) for y in (ground - h + 4, ground - 5)]) * m, (60, 60, 64))
    c.tone(m * np.clip((c.x - x) / (w / 2), -1, 1), -0.25)


def coil(c, x, ground, r=9):
    for i, rr in enumerate(np.linspace(r, 3, 4)):
        c.put(c.mask(lambda p: p.ellipse(x, ground - rr * 0.45, rr, rr * 0.45)), scale(ROPE, 0.8 + 0.07 * i))
    c.put(c.mask(lambda p: p.ellipse(x, ground - 2, 2, 1)), scale(ROPE, 0.5))


def lantern(c, k, x, y, lit=0.7):
    """A hanging ship's lantern whose top is at `y`."""
    c.put(c.mask(lambda p: p.rect(x - 0.5, y - 10, x + 0.5, y)), PAL["iron"])
    cage = c.mask(lambda p: p.poly([(x - 4, y), (x + 4, y), (x + 3, y + 10), (x - 3, y + 10)]))
    c.put(cage, PAL["iron"])
    c.put(c.mask(lambda p: p.poly([(x - 3, y + 1.5), (x + 3, y + 1.5), (x + 2.2, y + 8.5), (x - 2.2, y + 8.5)])), mix(PAL["lamp"], (255, 255, 230), 0.4))
    c.light(c.mask(lambda p: p.ellipse(x, y + 5, 16), blur=8), PAL["lamp"], lit * 0.5)


def painted_board(c, x0, y0, x1, y1, colour, emblem="anchor"):
    """A painted board with the emblem of its trade (the room's label says
    the words): an anchor, a fish, a bottle or a coil of rope."""
    c.put(c.mask(box(x0, y0, x1, y1)), colour)
    c.put(c.mask(box(x0, y0, x1, y0 + 1.0)), mix(colour, (255, 255, 255), 0.35))
    c.put(c.mask(box(x0, y1 - 1.0, x1, y1)), scale(colour, 0.6))
    c.put(c.mask(lambda p: (p.rect(x0 + 2, y0 + 2, x1 - 2, y0 + 2.6), p.rect(x0 + 2, y1 - 2.6, x1 - 2, y1 - 2))), (226, 196, 120), 0.8)
    cx, cy, r = (x0 + x1) / 2, (y0 + y1) / 2, (y1 - y0) * 0.36
    ink = (240, 222, 170)
    if emblem == "anchor":
        shape = lambda p: (p.line([(cx, cy - r), (cx, cy + r)], r * 0.18), p.line([(cx - r * 0.5, cy - r * 0.55), (cx + r * 0.5, cy - r * 0.55)], r * 0.16),
                           p.line([(cx - r * 0.8, cy + r * 0.2), (cx - r * 0.55, cy + r * 0.85), (cx, cy + r), (cx + r * 0.55, cy + r * 0.85), (cx + r * 0.8, cy + r * 0.2)], r * 0.16),
                           p.ring(cx, cy - r * 0.95, r * 0.2, r * 0.12))
    elif emblem == "fish":
        shape = lambda p: (p.ellipse(cx - r * 0.2, cy, r * 0.9, r * 0.45), p.poly([(cx + r * 0.5, cy), (cx + r * 1.2, cy - r * 0.5), (cx + r * 1.2, cy + r * 0.5)]))
    elif emblem == "bottle":
        shape = lambda p: (p.rect(cx - r * 0.35, cy - r * 0.2, cx + r * 0.35, cy + r), p.rect(cx - r * 0.12, cy - r, cx + r * 0.12, cy - r * 0.2))
    else:
        shape = lambda p: [p.ring(cx, cy, r * f, r * 0.12) for f in (0.9, 0.6, 0.3)]
    c.put(c.mask(shape), ink)
    for bx in (x0 + 4, x1 - 4):
        c.put(c.mask(lambda p: p.ellipse(bx, cy, 0.9)), (60, 50, 40))


# ---------------------------------------------------------------------------
# The plaza
# ---------------------------------------------------------------------------

PLAZA_FLOOR, BALCONY = 704, 448


def harbour_house(c, k):
    """The harbour house over the east of the plaza, its balcony (y 448) the
    harbour balcony, and the stone stair up to it (treads 640, 576, 512)."""
    g = PLAZA_FLOOR
    x0, x1 = 1216, 1600
    eave = 208
    k.ground = g
    k.wall(x0, eave, x1, g, PLASTER_BLUE, "plaster", tag="hh")
    k.timber(x0, BALCONY + 6, x1, g, TIMBER, posts=5, braces=False, tag="hh_low")
    k.eave_shade(x0, x1, eave, 6)
    k.hipped(x0, x1, eave, 70, ROOF_SLATE, tiles="slate", overhang=10, tag="hh_roof")
    k.chimney(x0 + 60, eave - 40, 16, 36, PAL["stone"], smoke=(200, 200, 205), tag="hh_ch")
    for cx in (x0 + 70, x0 + 170, x0 + 270):
        k.window(cx, eave + 40, 26, 40, "rect", shutters=NAVY, lit=0.15, tag=("hhw", cx))
        k.window(cx, eave + 128, 26, 40, "rect", shutters=NAVY, tag=("hhw2", cx))
    # The ground floor: the harbour office's doors and a window, behind the walk.
    for cx in (x0 + 90, x0 + 230):
        c.put(c.mask(box(cx - 22, g - 120, cx + 22, g)), PLANK_DARK)
        c.put(c.mask(lambda p: [p.rect(x, g - 120, x + 0.6, g) for x in np.arange(cx - 22, cx + 22, 7)]), scale(PLANK_DARK, 0.7))
    k.window(x0 + 330, g - 150, 30, 44, "rect", lit=0.2, tag="hh_office")
    painted_board(c, x0 + 60, g - 190, x0 + 260, g - 168, NAVY)
    # The balcony: the walk line at y 448.
    k.balcony(1232, x1, BALCONY, PLANK, rail=TIMBER)
    for x in np.arange(1250, x1, 48):
        c.put(c.mask(lambda p: p.poly([(x, BALCONY + 4), (x + 3, BALCONY + 4), (x + 18, BALCONY + 22), (x + 15, BALCONY + 22)])), TIMBER)
    # The stone stair: three treads, each a block of masonry to the floor.
    for i, (sx, top) in enumerate(((1000, 640), (1080, 576), (1160, 512))):
        m = c.mask(box(sx, top, sx + 96, g))
        c.put(m, PAL["stone"])
        rows = c.mask(lambda p: [p.rect(sx, y, sx + 96, y + 0.8) for y in np.arange(top + 12, g, 12)])
        c.put(rows * m, scale(PAL["stone"], 0.72), 0.8)
        c.tone(m * (c.noise(("stair", i), 4, 6, 3) - 0.5), 0.18)
        c.put(c.mask(box(sx, top, sx + 96, top + 3)), PAL["stone_light"])
    # Flags on the balcony rail: the port's bunting.
    pts = sag((1240, BALCONY - 40), (1590, BALCONY - 40), 14)
    rope_line(c, pts, 0.6, (60, 50, 40))
    cols = [RED_PAINT, (230, 200, 90), NAVY, (240, 236, 220)]
    for i, (x, y) in enumerate(pts[1:-1:2]):
        c.put(c.mask(lambda p: p.poly([(x - 4, y), (x + 4, y), (x, y + 9)])), cols[i % 4])


def freight_booth(c, k):
    """The clerk's booth and the ring's freight by it: the crates are the
    room's steps (tops y 656, x 560..656, and y 608, x 584..632)."""
    g = PLAZA_FLOOR
    k.ground = g
    # The booth: a timber hut with a counter window and a slate roof.
    bx0, bx1 = 664, 800
    k.wall(bx0, g - 120, bx1, g, PLASTER, "plaster", tag="booth")
    k.timber(bx0, g - 120, bx1, g, TIMBER, posts=3, braces=False, tag="booth_t")
    c.put(c.mask(box(bx0 + 14, g - 92, bx1 - 14, g - 52)), PAL["dark"])
    k.glass(c.mask(box(bx0 + 16, g - 90, bx1 - 16, g - 54)), 0.35, g - 90, g - 54, "booth_glass")
    c.put(c.mask(box(bx0 + 8, g - 54, bx1 - 8, g - 48)), PLANK_LIGHT)
    # Ledgers on the counter, a lamp.
    c.put(c.mask(lambda p: (p.rect(bx0 + 24, g - 60, bx0 + 50, g - 54), p.rect(bx0 + 54, g - 62, bx0 + 72, g - 54))), (120, 40, 36))
    k.hipped(bx0, bx1, g - 120, 26, ROOF_SLATE, tiles="slate", overhang=8, tag="booth_roof")
    painted_board(c, bx0 + 6, g - 150, bx1 - 6, g - 132, NAVY)
    # The crates: the low row, and one on top.
    for x0 in (560, 608):
        crate(c, x0, 656, x0 + 48, g, PLANK, mark=RED_PAINT if x0 == 560 else NAVY)
    crate(c, 584, 608, 632, 656, PLANK_LIGHT, mark=(40, 90, 60))
    barrel(c, 820, g)
    k.lamp(546, h=96, colour=PAL["iron"], lit=0.6, tag="booth_lamp")


def lamp_post(c, k):
    x0, y0, x1, y1 = PIECES["port_lamp_post"].frame
    k.ground = y1
    k.lamp(x0 + 8, h=100, colour=PAL["iron"], lit=0.7, tag="lamp_post")


# ---------------------------------------------------------------------------
# The waterfront
# ---------------------------------------------------------------------------

STREET, GALLERY, ROOF_A, ROOF_B = 768, 512, 448, 384


def town_house(c, k, x0, x1, wall, roof, eave, peak, tag, shutters=NAVY, sign=None):
    """A house of the waterfront: plaster and timber over a planked ground
    floor; the gallery at y 512 runs along its front."""
    g = STREET
    k.ground = g
    k.wall(x0, eave, x1, g, wall, "plaster", tag=tag)
    mid = (eave + GALLERY - 30) / 2
    k.timber(x0, eave, x1, mid, TIMBER, posts=max(2, int((x1 - x0) / 60)), tag=(tag, "t"))
    k.timber(x0, mid, x1, GALLERY - 30, TIMBER, posts=max(2, int((x1 - x0) / 60)), braces=False, tag=(tag, "t2"))
    k.eave_shade(x0, x1, eave, 6)
    k.gable(x0, x1, eave, peak, roof, tiles="clay", overhang=10, tag=(tag, "roof"))
    for cx in np.arange(x0 + 40, x1 - 20, 80):
        k.window(cx, eave + 36, 22, 34, "rect", shutters=shutters, lit=0.1, tag=(tag, "w1", cx))
        k.window(cx, GALLERY - 92, 22, 40, "rect", shutters=shutters, tag=(tag, "w2", cx))
    # Ground floor: a shopfront of boards and a window behind the street.
    planks(c, k, x0, GALLERY + 8, x1, g, scale(wall, 0.62), step=7, vertical=True, tag=(tag, "shop"))
    for cx in np.arange(x0 + 60, x1 - 40, 120):
        k.window(cx, g - 150, 36, 46, "rect", lit=0.35, tag=(tag, "shopw", cx))
    door_x = x1 - 50
    c.put(c.mask(box(door_x - 22, g - 96, door_x + 22, g)), TIMBER)
    c.put(c.mask(box(door_x - 18, g - 92, door_x + 18, g)), PLANK_DARK)
    c.put(c.mask(lambda p: [p.rect(x, g - 92, x + 0.6, g) for x in np.arange(door_x - 18, door_x + 18, 6)]), scale(PLANK_DARK, 0.7))
    c.put(c.mask(lambda p: p.ellipse(door_x + 12, g - 46, 1.4)), PAL["brass"])
    if sign:
        painted_board(c, *sign, NAVY)


def gallery_run(c, k, x0, x1):
    """The gallery (y 512): its deck edge, brackets under it, the rail behind."""
    k.balcony(x0, x1, GALLERY, PLANK, rail=TIMBER)
    for x in np.arange(x0 + 20, x1, 64):
        c.put(c.mask(lambda p: p.poly([(x, GALLERY + 4), (x + 3.5, GALLERY + 4), (x + 3.5, GALLERY + 30), (x, GALLERY + 30)])), TIMBER)
        c.put(c.mask(lambda p: p.line([(x + 2, GALLERY + 26), (x + 20, GALLERY + 5)], 2.4)), TIMBER)


def waterfront_west(c, k):
    """Two houses from the west wall to x 560, with the gallery."""
    town_house(c, k, 16, 290, PLASTER_OCHRE, ROOF_RED, 250, 70, "wf_a", shutters=SEA_GREEN)
    town_house(c, k, 290, 560, PLASTER, ROOF_OCHRE, 290, 60, "wf_b", shutters=NAVY)
    gallery_run(c, k, 16, 560)
    # Laundry across the street side of the gallery.
    pts = sag((40, GALLERY - 70), (270, GALLERY - 70), 10)
    rope_line(c, pts, 0.6, (90, 80, 70))
    for i, (x, y) in enumerate(pts[2:-2:4]):
        c.put(c.mask(box(x - 5, y, x + 5, y + 14)), [(220, 220, 210), (170, 60, 50), (90, 120, 160)][i % 3])


def waterfront_middle(c, k):
    """Two houses from x 560 to 1100, with the gallery."""
    town_house(c, k, 560, 830, PLASTER_ROSE, ROOF_RED, 270, 66, "wf_c", shutters=(220, 200, 150))
    town_house(c, k, 830, 1100, PLASTER_BLUE, ROOF_SLATE, 230, 76, "wf_d", shutters=RED_PAINT)
    gallery_run(c, k, 560, 1100)


def tavern_front(c, k):
    """The front of The Drowned Compass round its door (x 1320..1368); the
    gallery runs on to x 1600."""
    x0, x1 = 1100, 1600
    g = STREET
    k.ground = g
    k.wall(x0, 240, x1, g, PLASTER, "plaster", tag="tav")
    k.timber(x0, 240, x1, GALLERY - 30, TIMBER, posts=6, braces=False, tag="tav_t")
    k.timber(x0, GALLERY + 8, x1, g, TIMBER, posts=6, braces=False, tag="tav_t2")
    k.eave_shade(x0, x1, 240, 6)
    k.hipped(x0, x1, 240, 64, ROOF_RED, tiles="clay", overhang=10, tag="tav_roof")
    for cx in (1160, 1260, 1460, 1540):
        k.window(cx, 286, 24, 36, "rect", shutters=SEA_GREEN, lit=0.2, tag=("tav_w", cx))
    for cx in (1180, 1460):
        k.window(cx, g - 170, 60, 70, "rect", lit=0.65, tag=("tav_low", cx))
    # The door's surround (the game draws the door itself) and the sign.
    c.put(c.mask(box(1308, g - 112, 1380, g)), TIMBER)
    c.put(c.mask(box(1314, g - 106, 1374, g)), PAL["dark"])
    painted_board(c, 1250, GALLERY + 20, 1440, GALLERY + 46, (40, 66, 70), emblem="bottle")
    # A compass rose painted on a hanging board.
    k.sign(1400, GALLERY + 62, 34, 28, NAVY, glyph="circle", tag="tav_sign")
    lantern(c, k, 1290, GALLERY + 54)
    lantern(c, k, 1398 + 30, GALLERY + 100, 0.5)
    gallery_run(c, k, 1100, 1600)


def waterfront_stair(c, k):
    """The timber stair from the street to the gallery: treads at y 704, 640,
    576 (x 400..496, 480..576, 560..656)."""
    for (sx, top) in ((400, 704), (480, 640), (560, 576)):
        post(c, sx + 8, top, STREET, 7)
        post(c, sx + 88, top, STREET, 7)
        c.put(c.mask(lambda p: p.line([(sx + 8, top + 12), (sx + 88, STREET - 6)], 3.0)), TIMBER)
        c.put(c.mask(box(sx, top, sx + 96, top + 10)), PLANK)
        c.put(c.mask(box(sx, top + 8, sx + 96, top + 10)), PLANK_DARK)
        deck_edge(c, sx, sx + 96, top)
    c.put(c.mask(lambda p: p.line([(404, 676), (660, 516)], 3.0)), TIMBER)
    for x, y in ((404, 676), (532, 596), (660, 516)):
        post(c, x, y, y + 30, 3.2)


def chandler_stall(c, k):
    """Agnes's stall: an awning whose frame top is the room's ledge (y 656,
    x 760..920), goods on a table under it."""
    g = STREET
    top = 656
    k.ground = g
    for x in (764, 916):
        post(c, x, top, g, 5)
    k.awning(760, 920, top, 18, ((234, 224, 200), RED_PAINT), tag="stall")
    c.put(c.mask(box(760, top - 3, 920, top + 1)), PLANK)
    c.put(c.mask(box(760, top - 3, 920, top - 2)), PLANK_LIGHT)
    # The table and its goods: rope, jars of tar, biscuits in a crate.
    c.put(c.mask(box(770, g - 40, 910, g - 34)), PLANK_LIGHT)
    for x in (780, 900):
        post(c, x, g - 34, g, 3)
    coil(c, 800, g - 40, 10)
    for i, x in enumerate((830, 842, 854)):
        c.put(c.mask(lambda p: p.rect(x, g - 52, x + 9, g - 40)), [TAR, (110, 70, 40), (60, 80, 60)][i])
    crate(c, 868, g - 58, 904, g - 40, PLANK_LIGHT)
    barrel(c, 936, g)
    barrel(c, 954, g, 14, 18)


def chandlery(c, k):
    """The chandlery, its flat roof terrace the walk line (y 448, x 1664..2016)."""
    x0, x1 = 1664, 2016
    g = STREET
    k.ground = g
    k.wall(x0, ROOF_A, x1, g, PLASTER_OCHRE, "plaster", tag="chand")
    k.timber(x0, ROOF_A, x1, g - 130, TIMBER, posts=4, braces=False, tag="chand_t")
    for cx in (1720, 1840, 1960):
        k.window(cx, ROOF_A + 50, 26, 40, "rect", shutters=NAVY, tag=("ch_w", cx))
    planks(c, k, x0 + 20, g - 130, x1 - 20, g, PLANK_DARK, step=8, vertical=True, tag="chand_doors")
    painted_board(c, 1720, ROOF_A + 130, 1960, ROOF_A + 152, NAVY, emblem="coil")
    # The roof terrace: a parapet whose top is the walk line, crates on it.
    deck_edge(c, x0, x1, ROOF_A, PAL["stone"])
    c.put(c.mask(lambda p: [p.rect(x, ROOF_A - 14, x + 3, ROOF_A) for x in (x0 + 2, x1 - 5)]), TIMBER)
    rope_line(c, [(x0 + 3, ROOF_A - 14), (x1 - 3, ROOF_A - 14)], 0.8)


def net_loft(c, k):
    """The net loft at the east end, its roof terrace the walk line (y 384,
    x 2080..2560); nets hang to dry over the street."""
    x0, x1 = 2080, 2560
    g = STREET
    k.ground = g
    k.wall(x0, ROOF_B, x1, g, PLASTER_BLUE, "plaster", tag="loft")
    k.timber(x0, ROOF_B, x1, g - 150, TIMBER, posts=5, braces=False, tag="loft_t")
    for cx in (2150, 2260, 2370, 2480):
        k.window(cx, ROOF_B + 50, 24, 36, "rect", shutters=SEA_GREEN, lit=0.1, tag=("lf_w", cx))
    planks(c, k, x0, g - 150, x1, g, PLANK, step=8, vertical=True, tag="loft_low")
    # Nets on poles down the front.
    for i, nx in enumerate((2120, 2300)):
        net = c.mask(lambda p: p.poly([(nx, g - 260), (nx + 120, g - 260), (nx + 110, g - 160), (nx + 10, g - 170)]))
        grid = c.mask(lambda p: ([p.line([(x, g - 262), (x - 6, g - 160)], 0.5) for x in np.arange(nx, nx + 124, 6)],
                                 [p.line([(nx, y), (nx + 120, y)], 0.5) for y in np.arange(g - 260, g - 160, 6)]))
        c.put(grid * net, (60, 64, 58), 0.85)
        c.put(c.mask(lambda p: [p.ellipse(nx + 20 + j * 24, g - 175 + (j % 2) * 6, 3) for j in range(4)]), (220, 140, 60))
    deck_edge(c, x0, x1, ROOF_B, PAL["stone"])
    c.put(c.mask(lambda p: [p.rect(x, ROOF_B - 20, x + 3, ROOF_B) for x in np.arange(x0 + 2, x1, 80)]), TIMBER)
    rope_line(c, [(x0 + 3, ROOF_B - 18), (x1 - 3, ROOF_B - 18)], 0.8)


# ---------------------------------------------------------------------------
# The tavern
# ---------------------------------------------------------------------------

TAV_FLOOR, TAV_CEILING = 384, 32


def tavern_room(c, k):
    """The Drowned Compass inside: planked walls under beams, two windows on
    the harbour, the back bar with its bottles over the counter (y 344,
    x 720..960), tables, lanterns and a ship's wheel on the wall."""
    x0, x1 = 16, 1008
    g = TAV_FLOOR
    k.ground = g
    planks(c, k, x0, TAV_CEILING, x1, g, (120, 86, 58), step=8, tag="tav_wall")
    c.put(c.mask(lambda p: [p.rect(x, TAV_CEILING, x + 10, g) for x in np.arange(x0 + 100, x1, 220)]), TIMBER)
    c.put(c.mask(box(x0, TAV_CEILING, x1, TAV_CEILING + 14)), TIMBER)
    c.put(c.mask(box(x0, g - 70, x1, g - 64)), PLANK_DARK)
    for cx in (220, 520):
        k.window(cx, 110, 70, 80, "rect", lit=0.0, tag=("tav_in_w", cx))
    # The wheel.
    c.put(c.mask(lambda p: (p.ring(380, 140, 26, 4), [p.line([(380, 140), (380 + 36 * math.cos(a), 140 + 36 * math.sin(a))], 2.4) for a in np.linspace(0, math.tau, 9)[:-1]], p.ellipse(380, 140, 6))), PLANK_LIGHT)
    # The back bar: shelves of bottles.
    c.put(c.mask(box(700, 90, 990, g - 40)), PLANK_DARK)
    for y in (130, 190, 250):
        c.put(c.mask(box(700, y, 990, y + 4)), PLANK_LIGHT)
        rng = c.rand("bottles", y)
        for x in np.arange(708, 980, 11):
            h = rng.uniform(16, 26)
            col = rng.choice([(60, 110, 70), (120, 60, 40), (190, 160, 90), (70, 80, 120)])
            c.put(c.mask(lambda p: (p.rect(x, y - h, x + 7, y), p.rect(x + 2.4, y - h - 6, x + 4.6, y - h))), col)
    # The counter: its top is the walk line (y 344).
    planks(c, k, 720, 344, 960, g, PLANK, step=7, vertical=True, tag="counter")
    deck_edge(c, 714, 966, 344, PLANK_LIGHT)
    for x in (760, 820, 880):
        c.put(c.mask(lambda p: (p.rect(x, 330, x + 8, 344), p.ring(x + 10, 337, 3, 1.2))), (190, 170, 120))
    # Tables and stools.
    for tx in (180, 560):
        c.put(c.mask(box(tx - 40, g - 34, tx + 40, g - 28)), PLANK_LIGHT)
        post(c, tx, g - 28, g, 5, PLANK_DARK)
        for sx in (tx - 54, tx + 54):
            c.put(c.mask(box(sx - 9, g - 22, sx + 9, g - 18)), PLANK)
            post(c, sx, g - 18, g, 3, PLANK_DARK)
        c.put(c.mask(lambda p: (p.rect(tx - 10, g - 44, tx - 2, g - 34), p.rect(tx + 8, g - 42, tx + 16, g - 34))), (200, 180, 130))
    for lx in (180, 560, 840):
        lantern(c, k, lx, TAV_CEILING + 26, 0.8)


# ---------------------------------------------------------------------------
# The docks
# ---------------------------------------------------------------------------

DECK, SEA_FLOOR = 768, 928
HULL_X0, HULL_X1, SHIP_DECK = 1760, 2560, 640
FOREMAST, MAINMAST = 1960, 2256
WAREHOUSE_ROOF, GANTRY, RIGGING_ROPE = 448, 384, 416


def pilings(c, x0, x1, step=48):
    for x in np.arange(x0 + 8, x1, step):
        post(c, x, DECK + 16, SEA_FLOOR, 8, PLANK_DARK)
        c.put(c.mask(box(x - 4, DECK + 30, x + 4, DECK + 34)), (50, 70, 60), 0.6)


def warehouse(c, k):
    """The bonded warehouse on the middle span of the pier, its flat roof
    the walk line (y 448, x 864..1504)."""
    x0, x1 = 864, 1504
    k.ground = DECK
    pilings(c, 832, 1504)
    planks(c, k, x0, WAREHOUSE_ROOF, x1, DECK, (110, 84, 62), step=8, vertical=True, tag="wh")
    c.put(c.mask(lambda p: [p.rect(x, WAREHOUSE_ROOF, x + 8, DECK) for x in np.arange(x0, x1, 128)]), TIMBER)
    # Two great cargo doors, one ajar on crates.
    for dx in (960, 1250):
        c.put(c.mask(box(dx, DECK - 170, dx + 120, DECK)), PLANK_DARK)
        c.put(c.mask(lambda p: (p.line([(dx + 4, DECK - 4), (dx + 116, DECK - 166)], 3), p.line([(dx + 4, DECK - 166), (dx + 116, DECK - 4)], 3))), scale(PLANK_DARK, 0.7))
    crate(c, 1100, DECK - 40, 1140, DECK)
    crate(c, 1140, DECK - 40, 1180, DECK, PLANK_LIGHT)
    crate(c, 1120, DECK - 80, 1160, DECK - 40, mark=RED_PAINT)
    painted_board(c, 1000, WAREHOUSE_ROOF + 40, 1370, WAREHOUSE_ROOF + 70, (150, 50, 40), emblem="anchor")
    # A hoist beam over the doors, and the roof's parapet.
    c.put(c.mask(box(1240, WAREHOUSE_ROOF + 6, 1290, WAREHOUSE_ROOF + 14)), TIMBER)
    rope_line(c, [(1286, WAREHOUSE_ROOF + 14), (1286, WAREHOUSE_ROOF + 120)], 1.0)
    c.put(c.mask(lambda p: p.ring(1286, WAREHOUSE_ROOF + 124, 4, 1.4)), PAL["iron"])
    deck_edge(c, x0, x1, WAREHOUSE_ROOF, PLANK)


def gantry(c, k):
    """The gantry from the west wall to the warehouse (walk line y 384), on
    trestles to the pier and the harbour, a crane at its east end."""
    x0, x1 = 16, 864
    pilings(c, 0, 720)
    for x in np.arange(60, x1, 140):
        post(c, x, GANTRY + 4, DECK if x < 720 else SEA_FLOOR, 7, TIMBER)
        c.put(c.mask(lambda p: p.line([(x, GANTRY + 70), (x + 70, GANTRY + 6)], 3)), TIMBER)
    c.put(c.mask(box(x0, GANTRY + 4, x1, GANTRY + 12)), PLANK_DARK)
    deck_edge(c, x0, x1, GANTRY)
    # The crane: a mast and a jib over the gap, its hook down to the water.
    post(c, 800, GANTRY - 140, GANTRY, 8, TIMBER)
    c.put(c.mask(lambda p: p.line([(800, GANTRY - 120), (880, GANTRY - 150)], 5)), TIMBER)
    rope_line(c, [(800, GANTRY - 140), (878, GANTRY - 150)], 1.0)
    rope_line(c, [(876, GANTRY - 148), (876, GANTRY + 210)], 1.0)
    c.put(c.mask(lambda p: p.line([(870, GANTRY + 210), (876, GANTRY + 218), (882, GANTRY + 210)], 2.0)), PAL["iron"])
    # The rail behind the walk.
    c.put(c.mask(lambda p: (p.rect(x0, GANTRY - 18, x1, GANTRY - 16), [p.rect(x, GANTRY - 18, x + 2, GANTRY) for x in np.arange(x0, x1, 40)])), TIMBER)


def brig(c, k):
    """The brig PERSISTENCE at her moorings on the east span. Her hull is the
    room's block (x 1760..2560, deck y 640); her bowsprit points east. The
    masts stand at the yards' middles (fore x 1960, main x 2256), the yards
    are drawn at their walk lines, the crow's nest's floor is y 304, and the
    signal rope runs from the main upper yard to the warehouse roof (y 416).
    Furled sails hang under the yards, clear of the walk lines."""
    # The signal rope, behind the rigging, with pennants under it.
    c.put(c.mask(lambda p: p.line([(1500, RIGGING_ROPE + 1.5), (2180, RIGGING_ROPE + 1.5)], 3.0)), ROPE)
    c.put(c.mask(lambda p: p.line([(1500, RIGGING_ROPE), (2180, RIGGING_ROPE)], 1.0)), mix(ROPE, (255, 240, 200), 0.5))
    cols = [RED_PAINT, (234, 200, 80), NAVY, SAIL, SEA_GREEN]
    for i, x in enumerate(np.arange(1530, 2170, 34)):
        c.put(c.mask(lambda p: p.poly([(x - 7, RIGGING_ROPE + 3), (x + 7, RIGGING_ROPE + 3), (x, RIGGING_ROPE + 18)])), cols[i % 5])
    # Masts.
    for mx, top in ((FOREMAST, 380), (MAINMAST, 236)):
        c.put(c.mask(box(mx - 6, top, mx + 6, SHIP_DECK)), (112, 80, 52))
        c.put(c.mask(box(mx - 6, top, mx - 3, SHIP_DECK)), (150, 112, 74))
        c.put(c.mask(box(mx - 8, top - 6, mx + 8, top)), TIMBER)
    # Stays and shrouds.
    rope_line(c, [(MAINMAST, 240), (HULL_X1 + 70, 610)], 1.0, (60, 50, 40))
    rope_line(c, [(FOREMAST, 384), (HULL_X1 + 70, 600)], 0.8, (60, 50, 40))
    rope_line(c, [(MAINMAST, 240), (FOREMAST, 384)], 0.8, (60, 50, 40))
    rope_line(c, [(FOREMAST, 384), (HULL_X0 + 10, 600)], 0.8, (60, 50, 40))
    # The shroud ladder up the main (the room's ladder, x 2240..2272).
    c.put(c.mask(lambda p: ([p.line([(2232 + 0.5 * j, SHIP_DECK), (2248 + 0.5 * j, 300)], 0.8) for j in (0, 40)],
                            [p.rect(2234, y, 2276, y + 0.9) for y in np.arange(310, SHIP_DECK, 12)])), (60, 50, 40))
    # Yards with furled sails.
    yards = [(1880, 2040, 528), (2160, 2352, 528), (2176, 2336, 416)]
    for x0, x1, y in yards:
        cx = (x0 + x1) / 2
        furl = c.mask(lambda p: p.poly([(x0 + 6, y + 4), (x1 - 6, y + 4), (x1 - 14, y + 18), (cx, y + 24), (x0 + 14, y + 18)]))
        c.put(furl, SAIL)
        c.tone(furl * np.clip((c.y - y) / 22, 0, 1), -0.25)
        c.put(c.mask(lambda p: [p.line([(x, y + 4), (x + 3, y + 22)], 0.8) for x in np.arange(x0 + 20, x1 - 10, 22)]), (150, 140, 120))
        c.put(c.mask(box(x0, y, x1, y + 5)), TIMBER)
        c.put(c.mask(box(x0, y, x1, y + 1.2)), PLANK_LIGHT)
    # The crow's nest: its floor is the walk line (y 304, x 2216..2296).
    nest = c.mask(lambda p: p.poly([(2212, 304), (2300, 304), (2292, 330), (2220, 330)]))
    c.put(nest, PLANK)
    c.put(c.mask(lambda p: [p.rect(2214, y, 2298, y + 1.4) for y in (312, 322)]), PLANK_DARK)
    deck_edge(c, 2216, 2296, 304, PLANK_LIGHT)
    c.put(c.mask(lambda p: (p.rect(2216, 284, 2219, 304), p.rect(2293, 284, 2296, 304), p.rect(2216, 284, 2296, 286))), TIMBER)
    # The flag at the main truck: a black flag with a white compass star.
    flag = c.mask(lambda p: p.poly([(MAINMAST + 4, 206), (MAINMAST + 46, 210), (MAINMAST + 40, 222), (MAINMAST + 46, 234), (MAINMAST + 4, 230)]))
    c.put(c.mask(box(MAINMAST - 2, 200, MAINMAST + 2, 236)), TIMBER)
    c.put(flag, (24, 22, 24))
    c.put(c.mask(lambda p: [p.line([(MAINMAST + 24, 220), (MAINMAST + 24 + 8 * math.cos(a), 220 + 8 * math.sin(a))], 1.6) for a in np.linspace(0, math.tau, 5)[:-1] + 0.4]), (236, 232, 220))
    # The hull: a gun deck of wales and ports, a stern castle, the bow.
    hull = c.mask(lambda p: p.poly([(HULL_X0 - 20, SHIP_DECK - 30), (HULL_X0 + 70, SHIP_DECK - 30), (HULL_X0 + 80, SHIP_DECK),
                                     (HULL_X1 - 30, SHIP_DECK), (HULL_X1 + 40, SHIP_DECK - 26), (HULL_X1 + 30, 700),
                                     (HULL_X1 - 30, DECK), (HULL_X0 + 40, DECK), (HULL_X0, 712)]))
    c.put(hull, HULL)
    c.put(c.mask(lambda p: [p.rect(HULL_X0 - 30, y, HULL_X1 + 50, y + 1.4) for y in np.arange(SHIP_DECK + 10, DECK, 9)]) * hull, HULL_DARK, 0.8)
    for y, colour in ((SHIP_DECK + 4, HULL_BAND), (SHIP_DECK + 52, (34, 30, 30))):
        c.put(c.mask(box(HULL_X0 - 30, y, HULL_X1 + 50, y + 7)) * hull, colour)
    for x in np.arange(HULL_X0 + 90, HULL_X1 - 50, 70):
        c.put(c.mask(box(x, SHIP_DECK + 22, x + 18, SHIP_DECK + 38)), (30, 24, 22))
        c.put(c.mask(box(x - 1.5, SHIP_DECK + 20.5, x + 19.5, SHIP_DECK + 22)), HULL_BAND)
    c.tone(hull * np.clip((c.y - SHIP_DECK) / (DECK - SHIP_DECK), 0, 1), -0.3)
    # Her name on the stern, the stern windows lit.
    painted_board(c, HULL_X0 + 6, SHIP_DECK + 66, HULL_X0 + 140, SHIP_DECK + 86, HULL_DARK)
    for x in (HULL_X0 + 4, HULL_X0 + 30, HULL_X0 + 56):
        c.put(c.mask(box(x - 14, SHIP_DECK - 24, x + 4, SHIP_DECK - 8)), mix(PAL["lamp"], (255, 240, 200), 0.3))
    # The deck's rail (behind the walk), the deck edge, the bowsprit.
    c.put(c.mask(lambda p: (p.rect(HULL_X0 + 80, SHIP_DECK - 18, HULL_X1 - 30, SHIP_DECK - 15),
                            [p.rect(x, SHIP_DECK - 18, x + 2.5, SHIP_DECK) for x in np.arange(HULL_X0 + 80, HULL_X1 - 30, 24)])), TIMBER)
    deck_edge(c, HULL_X0, HULL_X1, SHIP_DECK, PLANK)
    c.put(c.mask(lambda p: p.line([(HULL_X1 + 30, SHIP_DECK - 20), (HULL_X1 + 70, SHIP_DECK - 50)], 6)), (112, 80, 52))
    # The gangway's crates (top y 704, x 1680..1760).
    crate(c, 1680, 704, 1720, DECK)
    crate(c, 1720, 704, 1760, DECK, PLANK_LIGHT)
    deck_edge(c, 1680, 1760, 704, PLANK_LIGHT)
    # The mooring lines to the bollards.
    for bx, hx in ((1730, HULL_X0 + 40), (2590, HULL_X1 - 10)):
        c.put(c.mask(lambda p: (p.rect(bx - 6, DECK - 14, bx + 6, DECK), p.rect(bx - 8, DECK - 16, bx + 8, DECK - 12))), (50, 50, 54))
        rope_line(c, sag((bx, DECK - 12), (hx, SHIP_DECK + 30), 10), 1.4)


def dock_clutter(c, k):
    """Barrels, a coil of rope and a crate, for the pier."""
    x0, y0, x1, y1 = PIECES["port_dock_clutter"].frame
    g = y1
    barrel(c, x0 + 12, g)
    barrel(c, x0 + 30, g, 16, 24)
    barrel(c, x0 + 21, g - 22, 14, 18)
    coil(c, x0 + 58, g, 11)
    crate(c, x0 + 74, g - 30, x0 + 110, g, mark=NAVY)


def manifest_page(c, k):
    """The clerk's page: a sheet of the freight log, ruled, with entries and
    a gull's footprint on it."""
    x0, y0, x1, y1 = PIECES["port_manifest_page"].frame
    w, h = x1 - x0, y1 - y0
    page = c.mask(lambda p: p.poly([(x0 + 3, y0 + 2), (x1 - 2, y0 + 3.5), (x1 - 3, y1 - 2), (x0 + 2, y1 - 3)]))
    c.put(page, (244, 236, 212))
    c.put(c.mask(lambda p: p.poly([(x1 - 7, y1 - 2.2), (x1 - 3, y1 - 2), (x1 - 2.6, y1 - 6)])), (210, 198, 168))
    c.put(c.mask(lambda p: [p.rect(x0 + 5, y, x1 - 5, y + 0.4) for y in np.arange(y0 + 6, y1 - 4, 2.6)]) * page, (110, 130, 170), 0.8)
    c.put(c.mask(lambda p: p.rect(x0 + 8, y0 + 4, x0 + 8.4, y1 - 4)) * page, (190, 70, 60), 0.8)
    c.put(c.mask(lambda p: [p.rect(x0 + 9.5, y - 1.2, x0 + 9.5 + (5 + (i * 7) % 8), y) for i, y in enumerate(np.arange(y0 + 8, y1 - 5, 2.6))]) * page, (40, 40, 60), 0.85)
    gx, gy = x0 + w * 0.68, y0 + h * 0.6
    c.put(c.mask(lambda p: [p.line([(gx, gy + 2.5), (gx + 3.2 * math.cos(a), gy + 2.5 - 3.6 * math.sin(a))], 0.7) for a in (1.1, 1.57, 2.04)]), (90, 80, 70), 0.9)
    c.put(c.mask(lambda p: p.line([(x0 + 2, y0 + 3), (x1 - 2, y0 + 3.5)], 0.5)), (255, 255, 255), 0.6)


#: Every piece: its frame in its room, and how it is drawn.
PIECES: Dict[str, Piece] = {
    # pirate_port_gate_plaza
    "port_harbour_house": Piece((990, 120, 1600, 704), harbour_house),
    "port_freight_booth": Piece((520, 560, 850, 704), freight_booth),
    "port_lamp_post": Piece((0, 600, 32, 704), lamp_post),
    # pirate_port_waterfront
    "port_waterfront_west": Piece((0, 160, 580, 768), waterfront_west),
    "port_waterfront_middle": Piece((540, 140, 1120, 768), waterfront_middle),
    "port_tavern_front": Piece((1080, 160, 1620, 768), tavern_front),
    "port_waterfront_stair": Piece((396, 560, 664, 768), waterfront_stair),
    "port_chandler_stall": Piece((750, 630, 970, 768), chandler_stall),
    "port_chandlery": Piece((1660, 420, 2020, 768), chandlery),
    "port_net_loft": Piece((2076, 356, 2560, 768), net_loft),
    # pirate_port_tavern
    "port_tavern_room": Piece((16, 32, 1008, 384), tavern_room),
    # pirate_port_docks
    "port_warehouse": Piece((828, 440, 1508, 928), warehouse),
    "port_gantry": Piece((0, 220, 890, 928), gantry),
    "port_brig": Piece((1496, 196, 2640, 772), brig),
    "port_dock_clutter": Piece((0, 0, 120, 40), dock_clutter),
    # The pickup of the port's problem.
    "port_manifest_page": Piece((0, 0, 24, 24), manifest_page, px=4.0, traits=("pickup",)),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PAL", "PIECES", "TARGETS"]
