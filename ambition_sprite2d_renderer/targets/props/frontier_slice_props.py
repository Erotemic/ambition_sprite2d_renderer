"""Scenery of the Frontier's first slice, west of Dry Dock: Halfway Siding
(gate address SIDING) on the gulch rim, the Number 9 ore freight on the
gulch floor with the Rustler at its head, and Clinker Flats down the line.

The rooms are written by
`game/ambition_map_assets/ambition_content/generators/frontier/make_specs.py`
(its first-slice section). Each piece is drawn in its room's coordinates
(`_district_props`): where the room has a walk line (a platform, a porch
roof, a car's roof, the tipple road), the piece draws the light top edge of
the thing walked on at that y, over the room's block. The numbers here are
the generator's; change them together.

- Halfway Siding: the station house on its platform (y 608) with the
  luggage (y 560, 496) and its flat roof (y 448); the Lie-Down Inn, the
  mercantile, the windmill (its platform y 432) and the telegraph office
  over the boardwalks (y 608) and their porch roofs (y 496); the inn's
  recovery room; the trestle's deck (y 640) and its loose planks
  (x 1120..1280) on bents down to the gulch floor; Sprocket Row's arch,
  Hettie's garage and hoist (y 512), the parts yard and boiler (y 528), the
  shut rolling gate.
- The freight: every car's underframe at y 672 on wheels to the rails
  (y 720). The caboose (roof y 512, cupola y 448), box cars (y 480, 496),
  flat cars (deck y 608) with crates, the tank car (y 560, dome y 512), the
  ore car (walls y 560, ore y 624), and the Rustler: tender (y 528, hatch
  y 480), cab (y 432), boiler (y 512) and domes, pilot beam (y 608).
- Clinker Flats: the yard's dock (y 1376) and tracks, the tipple road on
  trestles (from 496, 1408 up to 2340, 640) and the tipple; the works'
  furnace house, slag pots (y 576) and crane gantry (y 512, 448); the Row's
  shacks (roofs y 528, 544) and the pump on the cinder hump; the railhead's
  old tramway grade (from 288, 640 down to 2128, 1408) and water tower.

Animations: ``idle``, 1 frame each.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .frontier_props import (
    GLOW, HAZARD, NEON_TEAL, PLANK, PLANK_DARK, PLANK_LIGHT, RUST, SIDING_BLUE, SIDING_GREY, SIDING_OCHRE, SIDING_RED,
    STEEL, STEEL_DARK, STEEL_LIGHT, TIMBER, TIN, door_surround, false_front, girder, grating, pipe, porch, siding,
    tin_roof, x_brace,
)
from .pirate_port_props import barrel, coil, crate, deck_edge, planks, post, rope_line

PAL = {
    "stone": (176, 140, 104), "stone_light": (226, 196, 150), "trim": (222, 204, 170), "dark": (36, 28, 26),
    "glass_top": (150, 176, 196), "glass_low": (64, 70, 84), "lamp": (255, 200, 120), "wood": (110, 74, 48),
    "leaf": (110, 120, 70), "iron": (44, 40, 40), "brass": (206, 160, 76), "glaze": (210, 170, 80),
}

RIM = 640
WALK = 608
PORCH = 496

BOXCAR_RED = (134, 58, 40)
BOXCAR_BROWN = (104, 70, 50)
OCHRE_CAR = (176, 128, 64)
TANK_BLACK = (48, 46, 48)
ORE_GREY = (86, 84, 90)
RUSTLER_BLACK = (36, 34, 38)
RUSTLER_RED = (150, 36, 32)
BRASS = (206, 160, 76)
CINDER = (70, 64, 66)
SLAG_GLOW = (255, 150, 60)


# ---------------------------------------------------------------------------
# Shared parts
# ---------------------------------------------------------------------------


def boardwalk(c, x0, x1, top, ground):
    """A boardwalk's front: planks on its edge, the walk's light lip."""
    planks(c, None, x0, top, x1, ground, PLANK, step=5.0, tag=("walk", x0))
    deck_edge(c, x0, x1, top, PLANK_LIGHT)
    c.put(c.mask(lambda p: [p.rect(x, top + 4, x + 3, ground) for x in np.arange(x0 + 10, x1, 64)]), PLANK_DARK)


def wheels(c, x0, x1, under=672, rail=720, tag="truck"):
    """The two trucks of a car: frames and wheels from its underframe down to
    the rails, the couplers at its ends."""
    for cx in (x0 + 70, x1 - 70):
        c.put(c.mask(box(cx - 48, under, cx + 48, under + 14)), (34, 32, 34))
        for dx in (-26, 26):
            w = c.mask(lambda p: p.ellipse(cx + dx, rail - 15, 15))
            c.put(w, (40, 38, 40))
            c.put(c.mask(lambda p: p.ring(cx + dx, rail - 15, 11, 2.2)), (90, 86, 84))
            c.put(c.mask(lambda p: p.ellipse(cx + dx, rail - 15, 3)), (120, 116, 110))
        c.put(c.mask(box(cx - 44, under + 14, cx + 44, under + 20)), (60, 56, 56))
    c.put(c.mask(box(x0 - 10, under + 2, x0 + 4, under + 12)), STEEL_DARK)
    c.put(c.mask(box(x1 - 4, under + 2, x1 + 10, under + 12)), STEEL_DARK)


def car_body(c, x0, x1, top, colour, tag, under=672, ribs=48):
    """A car's side: painted boards or plate, ribs, grime, its roof walk."""
    m = c.mask(box(x0, top, x1, under))
    planks(c, None, x0, top, x1, under, colour, step=6.0, vertical=True, tag=tag)
    c.put(c.mask(lambda p: [p.rect(x, top, x + 3, under) for x in np.arange(x0 + ribs / 2, x1 - 4, ribs)]), scale(colour, 0.62))
    c.put(c.mask(box(x0, top, x1, top + 6)), scale(colour, 0.7))
    c.put(c.mask(box(x0, under - 8, x1, under)), scale(colour, 0.55))
    grime = c.noise((tag, "grime"), (x1 - x0) / 60, 3, 3)
    c.tone(m * (grime - 0.5), 0.25)
    c.tone(m * np.clip((c.y - top) / (under - top), 0, 1), -0.18)
    deck_edge(c, x0, x1, top, mix(colour, (255, 236, 210), 0.35))
    return m


def car_lettering(c, x0, y, n=6, colour=(226, 214, 186)):
    """A railway's lettering as bars of paint (the game writes no words here)."""
    c.put(c.mask(lambda p: [p.rect(x0 + i * 14, y, x0 + i * 14 + 10, y + 10) for i in range(n)]), colour, 0.85)


def sliding_door(c, x0, x1, top, bottom, colour):
    m = c.mask(box(x0, top, x1, bottom))
    c.put(m, scale(colour, 0.88))
    c.put(c.mask(lambda p: (p.rect(x0, top, x1, top + 3), p.rect(x0, bottom - 3, x1, bottom), p.line([(x0, top), (x1, bottom)], 2.4),
                            p.line([(x1, top), (x0, bottom)], 2.4))), scale(colour, 0.6))
    c.put(c.mask(box(x0 - 6, top - 6, x1 + 6, top - 2)), STEEL_DARK)


def ladder_rungs(c, x, top, bottom, colour=STEEL_DARK):
    c.put(c.mask(lambda p: [p.rect(x, y, x + 12, y + 2) for y in np.arange(top + 8, bottom - 4, 12)]), colour)


def cargo_crate(c, x0, y0, x1, y1, colour=PLANK, stencil=True):
    """A slatted crate whose top is walked on."""
    crate(c, x0, y0, x1, y1, colour)
    deck_edge(c, x0, x1, y0, mix(colour, (255, 236, 200), 0.4))
    if stencil:
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        c.put(c.mask(lambda p: p.rect(cx - 10, cy - 4, cx + 10, cy + 4)), (60, 40, 30), 0.6)


def lamp_glow(c, x, y, r=40, strength=0.3):
    c.light(c.mask(lambda p: p.ellipse(x, y, r, r * 0.8), blur=r * 0.4), GLOW, strength)
    c.put(c.mask(lambda p: p.ellipse(x, y, 4)), (255, 230, 170))


# ---------------------------------------------------------------------------
# Halfway Siding: the station
# ---------------------------------------------------------------------------


def station_house(c, k):
    """The rail halt: its platform (y 608, x 640..1520), the station house
    (x 720..1200, flat roof y 448) with the agent's window, the luggage
    stacked at its east end (y 560, 496), a bench, a clock, the rails behind."""
    g, plat, roof = RIM, WALK, 448
    k.ground = plat
    # The track behind the platform, its ties along it.
    c.put(c.mask(box(640, plat - 24, 1520, plat - 20)), (90, 86, 84))
    c.put(c.mask(lambda p: [p.rect(x, plat - 20, x + 14, plat - 14) for x in np.arange(640, 1520, 24)]), (86, 62, 44))
    # The house: boards, a deep cornice, the agent's window and a door.
    siding(c, 728, roof + 8, 1192, plat, SIDING_OCHRE, "station")
    c.put(c.mask(box(716, roof, 1204, roof + 10)), scale(SIDING_OCHRE, 0.6))
    deck_edge(c, 720, 1200, roof, (230, 210, 170))
    k.eave_shade(728, 1192, roof + 10, 10, 0.3)
    k.window(900, roof + 40, 90, 60, "rect", lit=0.45, frame=(226, 214, 186), tag="ticket")
    c.put(c.mask(box(860, roof + 92, 940, roof + 98)), PLANK_DARK)
    c.put(c.mask(box(880, roof + 80, 920, roof + 92)), (40, 34, 30))
    for cx in (780, 1040, 1140):
        k.window(cx, roof + 48, 34, 52, "rect", lit=0.2, tag=("station_w", cx))
    c.put(c.mask(box(980, roof + 50, 1016, plat)), (78, 60, 46))
    c.put(c.mask(box(976, roof + 46, 1020, roof + 50)), PLANK_DARK)
    # The clock on a bracket over the platform.
    c.put(c.mask(box(1206, roof + 20, 1240, roof + 24)), STEEL_DARK)
    c.put(c.mask(lambda p: p.ellipse(1238, roof + 40, 16)), (236, 230, 214))
    c.put(c.mask(lambda p: p.ring(1238, roof + 40, 16, 2.0)), STEEL_DARK)
    c.put(c.mask(lambda p: (p.line([(1238, roof + 40), (1238, roof + 30)], 1.6), p.line([(1238, roof + 40), (1246, roof + 44)], 1.6))), (30, 30, 30))
    # A bench and a milk churn.
    c.put(c.mask(box(1060, plat - 26, 1130, plat - 22)), PLANK_LIGHT)
    for x in (1064, 1122):
        c.put(c.mask(box(x, plat - 22, x + 4, plat)), TIMBER)
    c.put(c.mask(lambda p: (p.rect(670, plat - 30, 690, plat), p.ellipse(680, plat - 30, 10, 4))), STEEL_LIGHT)
    # The luggage: a steamer trunk, then a stack, their lids the steps.
    for x0, x1, top, colour in ((1240, 1320, 560, (110, 60, 40)), (1290, 1370, 496, (60, 80, 110)), (1296, 1366, 560, (140, 110, 70))):
        m = c.mask(box(x0, top, x1, top + 48 if top == 496 else plat))
        c.put(m, colour)
        c.put(c.mask(lambda p: (p.rect(x0, top + 6, x1, top + 9), p.rect(x0 + 10, top, x0 + 14, top + 48), p.rect(x1 - 14, top, x1 - 10, top + 48))) * m, BRASS, 0.8)
        deck_edge(c, x0, x1, top, mix(colour, (255, 236, 200), 0.4))
    # The platform's edge: boards over the room's block.
    boardwalk(c, 640, 1520, plat, g)
    # A board for the timetable (the room's label is the writing).
    for x in (1170, 1550):
        post(c, x, 430, plat, 5)
    board = c.mask(box(1150, 398, 1570, 436))
    c.put(board, (44, 50, 58))
    c.put(c.mask(lambda p: (p.rect(1150, 398, 1570, 401), p.rect(1150, 433, 1570, 436))), PLANK_DARK)


# ---------------------------------------------------------------------------
# Halfway Siding: the street
# ---------------------------------------------------------------------------


def inn_front(c, k):
    """The Lie-Down Inn: two storeys, x 180..660, a sleeping-porch balcony
    with cots on it, its door at x 396..444 on the boardwalk (y 608), the
    porch roof (y 496, x 200..640)."""
    x0, x1, top, g = 180, 660, 220, WALK
    k.ground = g
    false_front(c, k, x0, x1, top, g, SIDING_BLUE, "inn", step=50)
    for cx in (250, 350, 490, 590):
        k.window(cx, 300, 36, 56, "rect", lit=0.25, frame=(226, 214, 186), tag=("inn_up", cx))
        # Curtains drawn: the guests are lying down.
        c.put(c.mask(box(cx - 16, 304, cx + 16, 350)), (200, 170, 150), 0.6)
    c.put(c.mask(lambda p: ([p.rect(x, 380, x + 1.2, 396) for x in np.arange(x0 + 10, x1 - 10, 6)], p.rect(x0 + 8, 378, x1 - 8, 381))), (226, 214, 186), 0.9)
    for cx in (270, 560):
        k.window(cx, 524, 76, 56, "rect", lit=0.55, frame=(226, 214, 186), tag=("inn_low", cx))
    door_surround(c, 396, 444, g)
    # A bucket by the door, and a cot airing on the rail.
    c.put(c.mask(lambda p: p.poly([(460, g - 18), (476, g - 18), (474, g), (462, g)])), (150, 150, 146))
    c.put(c.mask(lambda p: p.ring(468, g - 20, 7, 1.0)) * c.mask(box(458, g - 30, 478, g - 18)), (90, 90, 90))
    porch(c, k, 200, 640, PORCH, g, [206, 330, 510, 634], "inn")
    boardwalk(c, 160, 680, g, RIM)


def mercantile_front(c, k):
    """Halfway Mercantile: a false front, x 690..1080, a display window of
    tins and rope; the porch roof (y 496, x 700..1060)."""
    x0, x1, top, g = 696, 1076, 260, WALK
    k.ground = g
    false_front(c, k, x0, x1, top, g, SIDING_GREY, "merc")
    for cx in (760, 1000):
        k.window(cx, 320, 40, 50, "rect", lit=0.15, tag=("merc_up", cx))
    k.window(780, 524, 120, 64, "rect", lit=0.35, bars=False, tag="merc_low")
    c.put(c.mask(lambda p: [p.rect(740 + i * 14, g - 46, 750 + i * 14, g - 30) for i in range(6)]), (170, 60, 40))
    coil(c, 820, g - 24, 9)
    door_surround(c, 940, 980, g, 92)
    c.put(c.mask(box(944, g - 86, 976, g)), (90, 70, 56))
    porch(c, k, 700, 1060, PORCH, g, [706, 880, 1054], "merc")
    boardwalk(c, 680, 1080, g, RIM)
    barrel(c, 1040, g, 16, 22)


def siding_windmill(c, k):
    """The windmill over the trough: its lattice tower, the platform (y 432,
    x 1150..1340) round its top, the wheel and tail over it; the trough and
    pump rod on the street (y 640)."""
    g, deck = RIM, 432
    k.ground = g
    for xa, xb in ((1170, 1200), (1320, 1290)):
        c.put(c.mask(lambda p: p.line([(xa, g), (xb, deck)], 6)), TIMBER)
    for y in np.arange(deck + 40, g, 52):
        f = (y - deck) / (g - deck)
        xa, xb = 1200 - 30 * f, 1290 + 30 * f
        c.put(c.mask(lambda p: p.rect(xa, y, xb, y + 3)), scale(TIMBER, 0.9))
    x_brace(c, 1190, 1300, deck + 20, g - 10, scale(TIMBER, 0.85), 2.4)
    # The pump rod down the middle and the trough.
    c.put(c.mask(box(1243, deck, 1247, g - 30)), STEEL_DARK)
    trough = c.mask(box(1120, g - 34, 1380, g))
    planks(c, None, 1120, g - 34, 1380, g, PLANK_DARK, step=8.0, tag="trough")
    c.put(c.mask(box(1124, g - 32, 1376, g - 26)), (90, 130, 140), 0.9)
    c.tone(trough * 0, 0)
    # The platform and its rail.
    deck_edge(c, 1150, 1340, deck, PLANK_LIGHT)
    c.put(c.mask(box(1150, deck + 3, 1340, deck + 10)), PLANK)
    c.put(c.mask(lambda p: ([p.rect(x, deck - 20, x + 2, deck) for x in np.arange(1152, 1340, 20)], p.rect(1150, deck - 22, 1340, deck - 20))), TIMBER)
    # The wheel: twelve vanes in a ring on its hub, and the tail vane.
    cx, cy, r = 1245, 300, 78
    c.put(c.mask(lambda p: p.rect(1241, cy, 1249, deck)), STEEL_DARK)
    for i in range(16):
        a = i * math.tau / 16
        pts = [(cx + math.cos(a) * 20, cy + math.sin(a) * 20), (cx + math.cos(a + 0.16) * r, cy + math.sin(a + 0.16) * r),
               (cx + math.cos(a - 0.04) * r, cy + math.sin(a - 0.04) * r)]
        c.put(c.mask(lambda p: p.poly(pts)), (196, 192, 184))
    c.put(c.mask(lambda p: (p.ring(cx, cy, r, 3), p.ring(cx, cy, 30, 2))), STEEL_DARK)
    c.put(c.mask(lambda p: p.ellipse(cx, cy, 8)), RUST)
    c.put(c.mask(lambda p: (p.rect(cx, cy - 3, cx + 110, cy + 3), p.poly([(cx + 80, cy - 34), (cx + 150, cy - 24), (cx + 150, cy + 24), (cx + 80, cy + 10)]))), (176, 170, 160))


def telegraph_front(c, k):
    """The telegraph office: a small false front, x 1440..1800, its wires
    up to a pole; the porch roof (y 496, x 1460..1780); the east boardwalk
    on to x 2160, the signpost at its end."""
    x0, x1, top, g = 1444, 1796, 300, WALK
    k.ground = g
    false_front(c, k, x0, x1, top, g, SIDING_RED, "telegraph")
    k.window(1520, 360, 40, 50, "rect", lit=0.2, tag="tel_up")
    k.window(1700, 524, 90, 60, "rect", lit=0.45, tag="tel_low")
    door_surround(c, 1580, 1620, g, 92)
    c.put(c.mask(box(1584, g - 86, 1616, g)), (70, 80, 90))
    porch(c, k, 1460, 1780, PORCH, g, [1466, 1620, 1774], "telegraph")
    # The pole and its insulators, the wires off to the west.
    c.put(c.mask(box(1830, 180, 1838, g)), TIMBER)
    c.put(c.mask(box(1806, 196, 1862, 202)), TIMBER)
    for x in (1810, 1826, 1842, 1858):
        c.put(c.mask(lambda p: p.ellipse(x, 192, 2.4, 3)), (120, 170, 160))
    c.put(c.mask(lambda p: [p.line([(x, 192), (1796, 310 + i * 6)], 0.8) for i, x in enumerate((1810, 1826))]), (40, 36, 34))
    boardwalk(c, 1440, 2160, g, RIM)
    # The signpost: arrows east.
    post(c, 2020, 400, RIM, 6, TIMBER)
    for y in (420, 450):
        c.put(c.mask(lambda p: p.poly([(1960, y), (2066, y), (2080, y + 10), (2066, y + 20), (1960, y + 20)])), PLANK_LIGHT)


# ---------------------------------------------------------------------------
# The Lie-Down Inn
# ---------------------------------------------------------------------------


def inn_room(c, k):
    """The recovery room: striped paper, a row of iron cots with a bucket by
    each (Alice's at x 700, Bob's at x 820), the desk (x 240..360), the stair
    (y 448, x 980..1092) to the landing (y 384) and its numbered doors."""
    g = 512
    k.ground = g
    wall = c.mask(box(16, 32, 1264, g))
    stripes = (np.sin((c.x - 16) * math.tau / 18.0) > 0.3).astype(np.float32)
    c.put(wall, (176, 150, 130))
    c.put(wall * stripes, (156, 126, 110), 0.8)
    c.tone(wall * np.clip((c.y - 32) / (g - 32), 0, 1), -0.2)
    c.put(c.mask(box(16, 360, 1264, 368)), PLANK_DARK)
    planks(c, None, 16, 368, 1264, g, (120, 84, 60), step=6.0, vertical=True, tag="wainscot")
    # Windows with the blinds half down.
    for cx in (520, 940):
        k.window(cx, 150, 90, 110, "rect", lit=0.6, frame=(220, 200, 170), tag=("inn_w", cx))
        c.put(c.mask(box(cx - 45, 150, cx + 45, 200)), (230, 210, 170), 0.9)
    # The desk, a bell on it, the key board behind it.
    c.put(c.mask(box(236, g - 64, 364, g)), (96, 62, 40))
    deck_edge(c, 236, 364, g - 64, (170, 120, 80))
    c.put(c.mask(lambda p: p.ellipse(340, g - 70, 6, 5)), BRASS)
    c.put(c.mask(box(250, 220, 350, 300)), (70, 48, 34))
    c.put(c.mask(lambda p: [p.ellipse(266 + (i % 4) * 22, 240 + (i // 4) * 26, 3) for i in range(12)]), BRASS)
    # The cots: iron frames, grey blankets, a bucket by each.
    for x in (560, 680, 800, 920):
        c.put(c.mask(box(x - 50, g - 34, x + 50, g - 24)), (190, 196, 204))
        c.put(c.mask(lambda p: (p.rect(x - 50, g - 50, x - 46, g), p.rect(x + 46, g - 40, x + 50, g), p.rect(x - 50, g - 24, x + 50, g - 21))), (60, 60, 64))
        c.put(c.mask(lambda p: p.ellipse(x - 34, g - 38, 12, 6)), (236, 232, 222))
        c.put(c.mask(lambda p: p.poly([(x + 54, g - 16), (x + 68, g - 16), (x + 66, g), (x + 56, g)])), (150, 150, 146))
    # The stair and the landing, its rail and the numbered doors upstairs.
    c.put(c.mask(box(980, 448, 1092, g)), (110, 76, 52))
    deck_edge(c, 980, 1092, 448, (176, 130, 90))
    c.put(c.mask(box(1092, 384, 1248, 394)), (110, 76, 52))
    deck_edge(c, 1092, 1248, 384, (176, 130, 90))
    for x in np.arange(1094, 1248, 14):
        c.put(c.mask(box(x, 360, x + 2, 384)), (80, 54, 38))
    c.put(c.mask(box(1092, 358, 1248, 362)), (80, 54, 38))
    for x in (1130, 1200):
        c.put(c.mask(box(x, 290, x + 40, 384)), (90, 62, 44))
        c.put(c.mask(lambda p: p.ellipse(x + 20, 304, 6, 5)), BRASS)
    # An oil lamp on the desk.
    lamp_glow(c, 300, g - 84, 50, 0.35)


# ---------------------------------------------------------------------------
# The Halfway Trestle
# ---------------------------------------------------------------------------

DECK = 640
PLANKS_X0, PLANKS_X1 = 1120, 1280


def trestle(c, k):
    """The trestle: its road deck (y 640) across the room, the loose planks
    over the hole (x 1120..1280) sagging and a board gone, the railing with a
    gap over the hole; the timber bents down to the gulch floor, the rails
    along the floor; a signal mast by the east end."""
    k.ground = 1536
    floor = 1500
    # The bents: pairs of raking legs with cross ties, every 200.
    for x in np.arange(100, 2400, 200):
        for xa, xb in ((x - 60, x - 20), (x + 60, x + 20)):
            c.put(c.mask(lambda p: p.line([(xa, floor), (xb, DECK + 32)], 10)), scale(TIMBER, 0.95))
        for y in np.arange(DECK + 120, floor, 160):
            f = (y - DECK) / (floor - DECK)
            c.put(c.mask(lambda p: p.rect(x - 24 - 40 * f, y, x + 24 + 40 * f, y + 7)), scale(TIMBER, 0.85))
        x_brace(c, x - 50, x + 50, DECK + 40, floor - 20, scale(TIMBER, 0.75), 3.0)
    # Stringers between the bents, under the deck.
    c.put(c.mask(box(0, DECK + 32, 2400, DECK + 48)), scale(TIMBER, 0.8))
    # The deck: planks across it, darker where the wagons wore it.
    for x0, x1 in ((0, PLANKS_X0), (PLANKS_X1, 2400)):
        planks(c, None, x0, DECK, x1, DECK + 32, PLANK, step=7.0, vertical=True, tag=("deck", x0))
        deck_edge(c, x0, x1, DECK, PLANK_LIGHT)
    # The loose planks: a few boards, sagging, one gone.
    for i, x in enumerate(np.arange(PLANKS_X0, PLANKS_X1, 20)):
        if i == 4:
            continue
        sag = 2 + (i % 3) * 2
        c.put(c.mask(lambda p: p.poly([(x + 1, DECK + sag), (x + 18, DECK + sag + 2), (x + 18, DECK + sag + 12), (x + 1, DECK + sag + 10)])), PLANK_LIGHT if i % 2 else PLANK)
    # The railing, with its gap over the planks.
    for x0, x1 in ((0, PLANKS_X0 - 20), (PLANKS_X1 + 40, 2400)):
        c.put(c.mask(lambda p: ([p.rect(x, DECK - 36, x + 4, DECK) for x in np.arange(x0 + 8, x1, 40)], p.rect(x0, DECK - 38, x1, DECK - 34),
                                p.rect(x0, DECK - 20, x1, DECK - 17))), TIMBER)
    # A broken rail end hanging down.
    c.put(c.mask(lambda p: p.line([(PLANKS_X0 - 20, DECK - 36), (PLANKS_X0 + 6, DECK - 6)], 3)), TIMBER)
    # The gulch floor: gravel, the rails along it.
    c.put(c.mask(box(0, floor, 2400, 1536)), (120, 76, 54))
    c.put(c.mask(lambda p: [p.rect(x, floor - 6, x + 16, floor) for x in np.arange(0, 2400, 26)]), (86, 62, 44))
    c.put(c.mask(lambda p: (p.rect(0, floor - 10, 2400, floor - 6), p.rect(0, floor - 2, 2400, floor))), (110, 106, 104))
    # The signal mast: a semaphore arm at stop, its lamp lit.
    c.put(c.mask(box(1996, 400, 2004, DECK)), STEEL_DARK)
    c.put(c.mask(lambda p: p.poly([(2004, 420), (2070, 414), (2070, 428), (2004, 432)])), (190, 40, 36))
    c.put(c.mask(lambda p: p.rect(2050, 414, 2056, 428)), (236, 230, 214))
    lamp_glow(c, 1992, 430, 20, 0.4)


# ---------------------------------------------------------------------------
# Sprocket Row
# ---------------------------------------------------------------------------


def gear(c, x, y, r, teeth, colour):
    pts = []
    for i in range(teeth * 2):
        a = i * math.pi / teeth
        rr = r if i % 2 == 0 else r * 0.8
        pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
    c.put(c.mask(lambda p: p.poly(pts)), colour)
    c.put(c.mask(lambda p: p.ellipse(x, y, r * 0.3)), scale(colour, 0.5))


def sprocket_arch(c, k):
    """The arch over the mechanics' street: two iron posts, a lattice beam
    with a big gear at its middle (the room's label is the name)."""
    g = RIM
    k.ground = g
    for x in (80, 400):
        girder(c, x, 420, g, 12, STEEL_DARK)
    c.put(c.mask(box(70, 416, 410, 432)), STEEL_DARK)
    c.put(c.mask(box(70, 460, 410, 472)), STEEL_DARK)
    x_brace(c, 86, 394, 432, 460, STEEL, 2.0)
    gear(c, 240, 410, 34, 12, BRASS)
    gear(c, 286, 430, 18, 8, scale(BRASS, 0.8))


def hettie_garage(c, k):
    """Hettie Gimbal's garage: an open bay under a tin roof, the hoist beam
    (y 512, x 680..960) with its chain and an engine on it, the crate by the
    door (top y 576, x 940..1020), a bench of tools, a wagon wheel."""
    g = RIM
    k.ground = g
    # The back wall of the bay, dark inside, and the frame.
    back = c.mask(box(500, 270, 1100, g))
    c.put(back, (70, 54, 44))
    c.tone(back * np.clip((c.y - 270) / (g - 270), 0, 1), 0.12)
    siding(c, 490, 230, 540, g, SIDING_GREY, "gar_l")
    siding(c, 1060, 230, 1110, g, SIDING_GREY, "gar_r")
    tin_roof(c, 480, 220, 1120, 240, "garage_roof")
    # The hoist: its beam on two legs, the trolley, the chain and the engine.
    for x in (690, 950):
        girder(c, x, 512, g, 8, STEEL_DARK)
    c.put(c.mask(box(680, 512, 960, 522)), STEEL)
    deck_edge(c, 680, 960, 512, STEEL_LIGHT)
    c.put(c.mask(lambda p: [p.ellipse(800, 528 + i * 6, 2.4, 3.2) for i in range(8)]), STEEL_DARK)
    eng = c.mask(box(770, 576, 830, 616))
    c.put(eng, (80, 84, 88))
    c.put(c.mask(lambda p: [p.rect(x, 572, x + 6, 580) for x in (776, 790, 804, 818)]), (60, 62, 66))
    pipe(c, [(830, 590), (846, 590), (846, 616)], 3, (140, 100, 60))
    # The crate by the door.
    cargo_crate(c, 940, 576, 1020, g, PLANK)
    # The bench, its vice and tools on the wall.
    c.put(c.mask(box(540, 590, 660, 596)), PLANK_LIGHT)
    for x in (546, 652):
        c.put(c.mask(box(x, 596, x + 4, g)), TIMBER)
    c.put(c.mask(box(560, 576, 580, 590)), STEEL_DARK)
    c.put(c.mask(lambda p: [p.line([(x, 470), (x + 4, 520)], 3) for x in (560, 580, 600, 620)]), STEEL_LIGHT, 0.9)
    gear(c, 1040, 600, 30, 14, (110, 80, 50))
    lamp_glow(c, 820, 290, 60, 0.3)


def parts_yard(c, k):
    """The parts yard: the boiler on blocks (top y 528, x 1320..1480), the
    crate before it (y 576, x 1220..1300), piles of gears and a cart wheel."""
    g = RIM
    k.ground = g
    cargo_crate(c, 1220, 576, 1300, g, PLANK_DARK)
    m = c.mask(lambda p: (p.rect(1320, 534, 1480, g - 16), p.ellipse(1320, 573, 6, 39), p.ellipse(1480, 573, 6, 39)))
    c.put(m, (90, 96, 100))
    c.tone(m * np.clip((c.y - 573) / 40, -1, 1), -0.3)
    c.put(c.mask(lambda p: [p.rect(x, 534, x + 2, g - 16) for x in np.arange(1340, 1480, 24)]), (60, 64, 68))
    deck_edge(c, 1320, 1480, 528, STEEL_LIGHT)
    for x in (1340, 1450):
        c.put(c.mask(box(x - 10, g - 16, x + 10, g)), (120, 116, 110))
    pipe(c, [(1400, 528), (1400, 500), (1420, 490)], 6, STEEL)
    for x, y, r in ((1180, 620, 18), (1530, 616, 22), (1555, 628, 12)):
        gear(c, x, y, r, 10, RUST)


def rolling_gate(c, k):
    """The workshops' rolling gate across the street's end, shut, in a frame
    of girders; a lamp over it."""
    g = RIM
    k.ground = g
    for x in (1660, 1974):
        girder(c, x, 330, g, 14, STEEL_DARK)
    c.put(c.mask(box(1650, 320, 1984, 340)), STEEL_DARK)
    gate = c.mask(box(1668, 340, 1966, g))
    tin_roof(c, 1668, 340, 1966, g, "rolling_gate", (120, 116, 108))
    c.put(c.mask(lambda p: [p.rect(1668, y, 1966, y + 2) for y in np.arange(352, g, 14)]), (90, 86, 80), 0.8)
    c.put(c.mask(box(1668, g - 40, 1966, g - 20)) * gate, HAZARD, 0.6)
    c.put(c.mask(lambda p: [p.poly([(x, g - 40), (x + 10, g - 40), (x + 30, g - 20), (x + 20, g - 20)]) for x in np.arange(1668, 1960, 30)]), (30, 30, 30), 0.7)
    lamp_glow(c, 1817, 350, 30, 0.35)


# ---------------------------------------------------------------------------
# The Number 9 freight
# ---------------------------------------------------------------------------

UNDER, RAIL = 672, 720


def track(c, w):
    """The rails and ties under the train at speed: the ties smeared into a
    blur, the rails bright."""
    c.put(c.mask(box(0, RAIL, w, RAIL + 32)), (110, 84, 64))
    rng = c.rand("ties", w)
    c.put(c.mask(lambda p: [p.rect(x, RAIL + 4, x + rng.uniform(40, 90), RAIL + 12) for x in np.arange(0, w, 70)], blur=2.0), (70, 50, 38), 0.8)
    c.put(c.mask(box(0, RAIL - 2, w, RAIL + 4)), (150, 146, 142))
    c.put(c.mask(box(0, RAIL - 2, w, RAIL - 1)), (220, 216, 210))
    c.put(c.mask(lambda p: [p.ellipse(rng.uniform(0, w), RAIL + 20, rng.uniform(6, 20), 3) for _ in range(int(w / 30))], blur=3.0), (150, 120, 96), 0.6)


def caboose(c, k):
    """The caboose: red boards, its roof (y 512, x 32..480), the cupola (top
    y 448, x 160..300) with its lit windows, the end platform and its rail."""
    k.ground = RAIL
    car_body(c, 32, 480, 512, (150, 46, 38), "caboose")
    for cx in (110, 250, 400):
        k.window(cx, 548, 36, 40, "rect", lit=0.5, frame=(226, 214, 186), tag=("cab_w", cx))
    m = c.mask(box(160, 448, 300, 512))
    planks(c, None, 160, 448, 300, 512, (150, 46, 38), step=6.0, vertical=True, tag="cupola")
    c.put(c.mask(box(152, 444, 308, 452)), (60, 30, 26))
    deck_edge(c, 160, 300, 448, (210, 140, 120))
    for cx in (195, 265):
        k.window(cx, 466, 30, 26, "rect", lit=0.6, tag=("cupola_w", cx))
    c.tone(m * 0, 0)
    c.put(c.mask(box(20, 520, 24, UNDER)), (60, 60, 64))
    c.put(c.mask(lambda p: [p.rect(18, y, 32, y + 3) for y in (540, 580, 620)]), (60, 60, 64))
    lamp_glow(c, 36, 530, 14, 0.5)
    wheels(c, 32, 480, tag="caboose")
    car_lettering(c, 330, 630, 8)


def box_car(x0, x1, top, colour, tag):
    def draw(c, k):
        k.ground = RAIL
        car_body(c, x0, x1, top, colour, tag)
        mid = (x0 + x1) / 2
        sliding_door(c, mid - 50, mid + 50, top + 20, UNDER - 10, colour)
        ladder_rungs(c, x0 + 6, top, UNDER)
        ladder_rungs(c, x1 - 18, top, UNDER)
        car_lettering(c, x0 + 40, top + 30, 5)
        c.put(c.mask(lambda p: [p.rect(x, top - 4, x + 20, top) for x in np.arange(x0 + 20, x1 - 20, 40)]), scale(colour, 0.5), 0.7)
        wheels(c, x0, x1, tag=tag)
    return draw


def flat_car(x0, x1, stacks, tag, open_west=False, open_east=False):
    """A flat car's deck (y 608) and the crate stacks lashed on it."""
    def draw(c, k):
        k.ground = RAIL
        car_body(c, x0, x1, 608, (90, 70, 56), tag, ribs=64)
        for sx0, sx1, top in stacks:
            for y in np.arange(top, 608, 64):
                cargo_crate(c, sx0, y, sx1, min(y + 64, 608), PLANK if (y // 64) % 2 else PLANK_LIGHT)
            rope_line(c, [(sx0, top + 6), (sx1, 600)], 1.4)
        if not open_west:
            c.put(c.mask(box(x0, 596, x0 + 6, 608)), STEEL_DARK)
        if not open_east:
            c.put(c.mask(box(x1 - 6, 596, x1, 608)), STEEL_DARK)
        if x1 - x0 > 400:
            wheels(c, x0, x1, tag=tag)
        else:
            # The far end of a car that runs on from the room before: its
            # second truck.
            cx = x1 - 70
            c.put(c.mask(box(cx - 48, UNDER, cx + 48, UNDER + 14)), (34, 32, 34))
            for dx in (-26, 26):
                c.put(c.mask(lambda p: p.ellipse(cx + dx, RAIL - 15, 15)), (40, 38, 40))
    return draw


def loose_crate(c, k):
    """A crate loose on a flat car (a moving platform's picture, 64 x 64)."""
    cargo_crate(c, 0, 0, 64, 64, PLANK_LIGHT)
    c.put(c.mask(lambda p: (p.line([(4, 4), (60, 60)], 3), p.line([(60, 4), (4, 60)], 3))), PLANK_DARK)


def tank_car(c, k):
    """The tank car: a black tank (top y 560, x 424..904) on its frame, the
    dome (y 512, x 620..700) with its hatch, a walkway along its side."""
    k.ground = RAIL
    x0, x1, top = 424, 904, 560
    m = c.mask(lambda p: (p.rect(x0 + 20, top, x1 - 20, UNDER - 10), p.ellipse(x0 + 20, (top + UNDER - 10) / 2, 24, (UNDER - 10 - top) / 2),
                          p.ellipse(x1 - 20, (top + UNDER - 10) / 2, 24, (UNDER - 10 - top) / 2)))
    c.put(m, TANK_BLACK)
    c.tone(m * np.clip((c.y - (top + 50)) / 56, -1, 1), -0.35)
    c.light(m * np.clip(1 - np.abs(c.y - (top + 18)) / 10, 0, 1), (200, 200, 210), 0.3)
    c.put(c.mask(lambda p: [p.rect(x, top, x + 2, UNDER - 10) for x in (x0 + 120, x1 - 120)]), (30, 30, 32))
    dome = c.mask(lambda p: (p.rect(620, 512, 700, top + 4), p.ellipse(660, 512, 40, 6)))
    c.put(dome, (58, 56, 58))
    deck_edge(c, 620, 700, 512, (150, 150, 156))
    deck_edge(c, x0 + 20, x1 - 20, top, (120, 120, 126))
    c.put(c.mask(box(x0, UNDER - 14, x1, UNDER)), (34, 32, 34))
    c.put(c.mask(box(x0 + 200, top + 40, x0 + 300, top + 54)), (226, 214, 186), 0.8)
    wheels(c, x0, x1, tag="tank")


def ore_car(c, k):
    """The open ore car: its end walls (y 560, x 968..992 and 1424..1448),
    the ore heaped inside to y 624, the hopper doors under it."""
    k.ground = RAIL
    x0, x1 = 968, 1448
    m = c.mask(lambda p: p.poly([(x0, 560), (x1, 560), (x1, UNDER), (x0 + 0, UNDER)]))
    plates_like = c.mask(box(x0, 560, x1, UNDER))
    c.put(plates_like, ORE_GREY)
    c.put(c.mask(lambda p: [p.rect(x, 560, x + 3, UNDER) for x in np.arange(x0 + 30, x1, 50)]), scale(ORE_GREY, 0.7))
    c.tone(m * (c.noise("ore car", 8, 2, 3) - 0.5), 0.3)
    # The near side is cut down to show the ore: its top at 600.
    c.alpha[:] = np.where((c.y < 600) & (c.x > x0 + 24) & (c.x < x1 - 24) & (c.y >= 560), 0, c.alpha)
    rng = c.rand("ore")
    c.put(c.mask(lambda p: [p.ellipse(rng.uniform(x0 + 30, x1 - 30), 624 - rng.uniform(0, 30), rng.uniform(10, 22), rng.uniform(6, 12)) for _ in range(40)]), (78, 74, 80))
    c.put(c.mask(lambda p: [p.ellipse(rng.uniform(x0 + 30, x1 - 30), 610 - rng.uniform(0, 16), 3) for _ in range(20)]), (190, 170, 120))
    deck_edge(c, x0, x0 + 24, 560, STEEL_LIGHT)
    deck_edge(c, x1 - 24, x1, 560, STEEL_LIGHT)
    deck_edge(c, x0 + 24, x1 - 24, 600, scale(STEEL_LIGHT, 0.85))
    wheels(c, x0, x1, tag="ore")


def rustler(c, k):
    """The Rustler, the outlaw engine at the head of the Number 9: its tender
    (y 528, x 908..1308) with grapple arms folded over it and the water
    hatch (y 480, x 1180..1290); the cab (roof y 432, x 1308..1548); the
    boiler (y 512, x 1548..2160) with its steam dome (y 464) and sand dome
    (y 472), the smokestack (y 384, x 2040..2100) blowing back; the
    smokebox's headlamp eye, a red bandana of paint over it; the pilot beam
    (y 608, x 2160..2400) and a cowcatcher like a grin of teeth."""
    k.ground = RAIL
    # The tender.
    t = c.mask(box(908, 528, 1308, UNDER))
    c.put(t, RUSTLER_BLACK)
    c.put(c.mask(lambda p: [p.rect(x, 528, x + 3, UNDER) for x in np.arange(930, 1308, 60)]), (60, 58, 62))
    c.put(c.mask(box(908, 600, 1308, 612)), RUSTLER_RED)
    deck_edge(c, 908, 1308, 528, (110, 106, 110))
    c.put(c.mask(lambda p: [p.ellipse(x, 524, 16, 6) for x in np.arange(930, 1170, 26)]), (40, 38, 40))
    c.put(c.mask(box(1180, 480, 1290, 528)), (70, 68, 74))
    deck_edge(c, 1180, 1290, 480, (140, 136, 140))
    # The grapple arms: two jointed booms reaching back over the train.
    for base_x, reach in ((960, 180), (1060, 240)):
        pts = [(base_x, 528), (base_x - 40, 420), (base_x - reach, 450), (base_x - reach - 20, 500)]
        c.put(c.mask(lambda p: p.line(pts, 9)), (70, 68, 72))
        c.put(c.mask(lambda p: p.line(pts, 4)), (130, 124, 120))
        hx, hy = pts[-1]
        c.put(c.mask(lambda p: p.line([(hx, hy), (hx, hy + 22), (hx - 6, hy + 30), (hx - 14, hy + 26), (hx - 14, hy + 18)], 4)), STEEL_LIGHT)
    # The cab.
    cab = c.mask(box(1308, 432, 1548, UNDER))
    c.put(cab, RUSTLER_BLACK)
    c.put(c.mask(box(1300, 424, 1556, 440)), (60, 56, 60))
    deck_edge(c, 1300, 1556, 432, (140, 136, 140))
    for cx in (1380, 1480):
        k.window(cx, 470, 50, 46, "rect", lit=0.7, frame=(200, 160, 80), tag=("cab_w", cx))
    c.light(c.mask(box(1330, 520, 1530, 600), blur=20), SLAG_GLOW, 0.35)
    c.put(c.mask(box(1308, 600, 1548, 612)), RUSTLER_RED)
    # The boiler, its bands, the domes and the stack.
    b = c.mask(box(1548, 512, 2160, UNDER - 20))
    c.put(b, (44, 42, 46))
    c.tone(b * np.clip((c.y - 560) / 50, -1, 1), -0.3)
    c.light(b * np.clip(1 - np.abs(c.y - 526) / 8, 0, 1), (200, 200, 210), 0.3)
    c.put(c.mask(lambda p: [p.rect(x, 512, x + 6, UNDER - 20) for x in np.arange(1600, 2160, 110)]), BRASS)
    deck_edge(c, 1548, 2160, 512, (130, 128, 134))
    for x0, x1, top in ((1700, 1780, 464), (1880, 1940, 472)):
        c.put(c.mask(lambda p: (p.rect(x0, top + 6, x1, 512), p.ellipse((x0 + x1) / 2, top + 6, (x1 - x0) / 2, 8))), BRASS)
        deck_edge(c, x0, x1, top, (240, 210, 140))
    c.put(c.mask(lambda p: (p.rect(2040, 392, 2100, 512), p.rect(2030, 384, 2110, 400))), (40, 38, 42))
    deck_edge(c, 2030, 2110, 384, (110, 108, 112))
    smoke = c.mask(lambda p: [p.ellipse(2070 - i * 70, 360 - i * 10 - (i % 2) * 8, 30 + i * 10, 18 + i * 5) for i in range(10)], blur=6)
    c.put(smoke, (90, 86, 86), 0.7)
    # The smokebox front: a headlamp like an eye, a bandana of red paint.
    c.put(c.mask(box(2100, 512, 2160, UNDER - 20)), (30, 30, 34))
    c.put(c.mask(lambda p: p.poly([(2060, 530), (2160, 530), (2160, 556), (2110, 548), (2060, 552)])), RUSTLER_RED)
    c.put(c.mask(lambda p: p.ellipse(2150, 500, 16, 14)), (60, 56, 50))
    c.put(c.mask(lambda p: p.ellipse(2156, 500, 9, 9)), (255, 230, 150))
    c.light(c.mask(lambda p: p.poly([(2160, 494), (2400, 450), (2400, 560), (2160, 506)]), blur=10), (255, 236, 170), 0.35)
    # The drivers: big wheels and their rods.
    for cx in (1640, 1800, 1960):
        c.put(c.mask(lambda p: p.ellipse(cx, RAIL - 34, 34)), (40, 38, 40))
        c.put(c.mask(lambda p: p.ring(cx, RAIL - 34, 30, 4)), RUSTLER_RED)
        c.put(c.mask(lambda p: [p.line([(cx, RAIL - 34), (cx + math.cos(a) * 28, RAIL - 34 + math.sin(a) * 28)], 2) for a in np.linspace(0, math.tau, 9)[:-1]]), (90, 86, 84))
    c.put(c.mask(lambda p: p.line([(1640, RAIL - 46), (1960, RAIL - 46)], 6)), STEEL_LIGHT)
    for cx in (1000, 1220):
        c.put(c.mask(lambda p: [p.ellipse(cx + dx, RAIL - 15, 15) for dx in (-26, 26)]), (40, 38, 40))
    # The pilot beam and the cowcatcher's teeth.
    c.put(c.mask(box(2160, 608, 2390, UNDER)), RUSTLER_RED)
    deck_edge(c, 2160, 2390, 608, (210, 120, 110))
    c.put(c.mask(lambda p: [p.poly([(x, UNDER), (x + 14, UNDER), (x + 26 + (x - 2160) * 0.2, RAIL - 2), (x + 12 + (x - 2160) * 0.2, RAIL - 2)]) for x in np.arange(2170, 2380, 22)]), (210, 206, 196))
    c.put(c.mask(box(2380, 616, 2400, 640)), STEEL_DARK)


# ---------------------------------------------------------------------------
# Clinker Flats
# ---------------------------------------------------------------------------

LOW, HIGH = 1408, 640


def yard_tracks(c, k):
    """The yard's ground: two tracks with a switch stand, a string of ore cars
    parked on the far one (under the tipple road), a buffer stop; the dock
    (top y 1376, x 0..448) of planks."""
    k.ground = LOW
    for y in (LOW - 4, LOW - 30):
        c.put(c.mask(lambda p: [p.rect(x, y - 2, x + 16, y + 4) for x in np.arange(448, 2400, 24)]), (70, 56, 46))
        c.put(c.mask(box(448, y - 4, 2400, y - 1)), (130, 126, 122))
    for x0 in (900, 1180, 1460):
        m = c.mask(lambda p: p.poly([(x0, LOW - 130), (x0 + 240, LOW - 130), (x0 + 220, LOW - 60), (x0 + 20, LOW - 60)]))
        c.put(m, scale(ORE_GREY, 0.75))
        c.tone(m * (c.noise(("parked", x0), 6, 2, 2) - 0.5), 0.3)
        for dx in (50, 190):
            c.put(c.mask(lambda p: p.ellipse(x0 + dx, LOW - 46, 14)), (40, 38, 40))
    c.put(c.mask(box(2300, LOW - 70, 2330, LOW - 30)), (170, 40, 36))
    post(c, 720, LOW - 90, LOW, 4, STEEL_DARK)
    c.put(c.mask(lambda p: p.ellipse(720, LOW - 92, 10, 6)), (220, 180, 60))
    planks(c, None, 0, 1376, 448, LOW, PLANK_DARK, step=7.0, vertical=True, tag="dock")
    deck_edge(c, 0, 448, 1376, PLANK_LIGHT)
    for x, y in ((200, 1376), (260, 1376)):
        cargo_crate(c, x, y - 40, x + 40, y, PLANK)


def tipple_road(c, k):
    """The tipple road: its deck along the line from (496, 1408) up to
    (2340, 640), on timber bents down to the yard; the tipple at the top (its
    floor y 640, x 2340..2400), a loading chute over the far track."""
    k.ground = LOW
    x0, y0, x1, y1 = 496, LOW, 2340, HIGH
    slope = (y1 - y0) / (x1 - x0)
    for x in np.arange(x0 + 120, x1, 160):
        y = y0 + (x - x0) * slope
        post(c, x, y + 10, LOW, 8, scale(TIMBER, 0.9))
        if LOW - y > 160:
            x_brace(c, x - 70, x + 10, y + 30, LOW - 10, scale(TIMBER, 0.75), 2.4)
    c.put(c.mask(lambda p: p.poly([(x0, y0), (x1, y1), (x1, y1 + 16), (x0, y0 + 16)])), PLANK)
    c.put(c.mask(lambda p: p.line([(x0, y0), (x1, y1)], 2.4)), PLANK_LIGHT)
    c.put(c.mask(lambda p: [p.rect(x, y0 + (x - x0) * slope - 26, x + 3, y0 + (x - x0) * slope) for x in np.arange(x0 + 40, x1, 60)]), TIMBER)
    c.put(c.mask(lambda p: p.line([(x0, y0 - 24), (x1, y1 - 24)], 2.0)), TIMBER)
    # The tipple: a tall shed on legs, its chute down to the track.
    m = c.mask(box(2200, 360, 2400, HIGH))
    siding(c, 2200, 360, 2400, HIGH, (110, 90, 74), "tipple")
    tin_roof(c, 2190, 340, 2400, 364, "tipple_roof")
    k.window(2280, 420, 40, 50, "rect", lit=0.3, tag="tipple_w")
    for x in (2210, 2390):
        post(c, x, HIGH, LOW, 10, TIMBER)
    x_brace(c, 2210, 2390, HIGH + 20, LOW - 20, scale(TIMBER, 0.8), 3.0)
    c.put(c.mask(lambda p: p.poly([(2220, HIGH + 10), (2260, HIGH + 10), (2160, LOW - 200), (2130, LOW - 200)])), (90, 80, 72))
    deck_edge(c, 2340, 2400, HIGH, PLANK_LIGHT)
    c.tone(m * 0, 0)


def furnace_house(c, k):
    """The furnace house of the works: brick, a tall stack, the fire door
    glowing (floor y 640, x 100..700)."""
    g = HIGH
    k.ground = g
    k.wall(120, 340, 660, g, (120, 64, 48), "brick", tag="furnace")
    tin_roof(c, 100, 320, 680, 344, "furnace_roof", (90, 86, 80))
    c.put(c.mask(box(520, 120, 580, 330)), (110, 58, 44))
    c.put(c.mask(lambda p: [p.rect(516, y, 584, y + 6) for y in (120, 200, 280)]), (70, 40, 32))
    smoke = c.mask(lambda p: [p.ellipse(560 + i * 30, 100 - i * 14, 26 + i * 8, 16 + i * 4) for i in range(6)], blur=6)
    c.put(smoke, (80, 76, 76), 0.6)
    door = c.mask(box(300, 520, 420, g))
    c.put(door, (60, 30, 20))
    c.light(c.mask(box(300, 520, 420, g), blur=30), SLAG_GLOW, 0.6)
    c.put(c.mask(box(316, 540, 404, g)), (255, 170, 80))
    for cx in (200, 600):
        k.window(cx, 420, 50, 60, "rect", lit=0.8, tag=("furnace_w", cx))


def slag_pots(c, k):
    """The slag pots on their carriages (tops y 576, x 700..812 and
    1400..1512), crusted and glowing at the lip."""
    g = HIGH
    k.ground = g
    for x0 in (700, 1400):
        x1 = x0 + 112
        m = c.mask(lambda p: p.poly([(x0, 576), (x1, 576), (x1 - 14, g - 14), (x0 + 14, g - 14)]))
        c.put(m, CINDER)
        c.tone(m * (c.noise(("pot", x0), 4, 3, 2) - 0.5), 0.35)
        c.put(c.mask(box(x0 - 4, 576, x1 + 4, 584)), (50, 46, 48))
        c.light(c.mask(box(x0 + 6, 570, x1 - 6, 580), blur=8), SLAG_GLOW, 0.6)
        deck_edge(c, x0, x1, 576, (255, 180, 100))
        for dx in (24, 88):
            c.put(c.mask(lambda p: p.ellipse(x0 + dx, g - 7, 7)), (40, 38, 40))


def works_crane(c, k):
    """The slag crane's gantry: the lower walk (y 512, x 820..1180) and the
    upper (y 448, x 1200..1560) on girder legs, the cab, the ladle on its
    chains."""
    g = HIGH
    k.ground = g
    for x in (830, 1170):
        girder(c, x, 512, g, 10)
    for x in (1210, 1550):
        girder(c, x, 448, g, 10)
    x_brace(c, 1210, 1550, 460, g - 10)
    grating(c, 820, 1180, 512)
    grating(c, 1200, 1560, 448)
    cab = c.mask(box(1600, 360, 1700, 448))
    c.put(cab, (180, 140, 50))
    k.window(1650, 380, 60, 36, "rect", lit=0.4, tag="crane_cab")
    girder(c, 1650, 448, g, 12)
    c.put(c.mask(box(1300, 300, 1720, 316)), STEEL_DARK)
    c.put(c.mask(lambda p: [p.ellipse(1420, 320 + i * 7, 2.4, 3.4) for i in range(10)]), STEEL_DARK)
    ladle = c.mask(lambda p: p.poly([(1390, 392), (1450, 392), (1440, 432), (1400, 432)]))
    c.put(ladle, CINDER)
    c.light(c.mask(box(1394, 388, 1446, 396), blur=6), SLAG_GLOW, 0.6)
    c.tone(cab * 0, 0)


def row_shacks(x_spans, tag):
    """Shacks of the Row: tin walls, lean-to roofs whose tops are the walks."""
    def draw(c, k):
        g = RIM
        k.ground = g
        for i, (x0, x1, roof) in enumerate(x_spans):
            colour = (120, 112, 104) if i % 2 else (138, 96, 72)
            tin_roof(c, x0 + 8, roof + 10, x1 - 8, g, (tag, i, "wall"), colour)
            tin_roof(c, x0 - 6, roof, x1 + 6, roof + 12, (tag, i, "roof"), (100, 96, 90))
            deck_edge(c, x0, x1, roof, (170, 160, 150))
            cx = (x0 + x1) / 2
            c.put(c.mask(box(cx - 20, g - 70, cx + 20, g)), (50, 42, 38))
            k.window(cx + 60 if x1 - x0 > 260 else cx - 70, roof + 40, 34, 30, "rect", lit=0.5, tag=(tag, i, "w"))
            c.put(c.mask(box(x0 + 30, roof - 40, x0 + 38, roof)), STEEL_DARK)
    return draw


def row_pump(c, k):
    """The pump on the cinder hump (top y 576, x 1104..1296) and the
    washing lines across the Row on poles."""
    g = RIM
    k.ground = g
    c.put(c.mask(box(1194, 520, 1206, 576)), STEEL_DARK)
    c.put(c.mask(lambda p: p.line([(1200, 524), (1236, 512)], 4)), STEEL_DARK)
    c.put(c.mask(lambda p: p.line([(1196, 540), (1180, 548)], 4)), STEEL_DARK)
    c.put(c.mask(lambda p: p.poly([(1170, 576), (1230, 576), (1226, 560), (1174, 560)])), (90, 90, 96))
    for x in (900, 1500):
        post(c, x, 440, g, 4)
    pts = [(900, 450), (1200, 476), (1500, 450)]
    rope_line(c, pts, 1.2)
    colours = [(200, 200, 196), (120, 140, 170), (190, 100, 80), (220, 210, 170), (110, 120, 90)]
    for i, x in enumerate(np.arange(940, 1480, 60)):
        y = 450 + 26 * (1 - abs((x - 1200) / 300.0))
        c.put(c.mask(lambda p: p.poly([(x - 18, y), (x + 18, y), (x + 14, y + 40), (x - 14, y + 40)])), colours[i % len(colours)])


def railhead_grade(c, k):
    """The old tramway grade: its head (y 640, x 0..288), the deck down on
    timber bents to the street at (2128, 1408); the water tower for the line
    and its spout; the line's signal and rails east."""
    k.ground = LOW
    x0, y0, x1, y1 = 288, HIGH, 2128, LOW
    slope = (y1 - y0) / (x1 - x0)
    planks(c, None, 0, HIGH, x0, HIGH + 16, PLANK, step=7.0, vertical=True, tag="grade_head")
    deck_edge(c, 0, x0, HIGH, PLANK_LIGHT)
    for x in (40, 160, 260):
        post(c, x, HIGH + 16, LOW, 8, scale(TIMBER, 0.9))
    for x in np.arange(x0 + 80, x1 - 100, 160):
        y = y0 + (x - x0) * slope
        post(c, x, y + 10, LOW, 8, scale(TIMBER, 0.9))
        if LOW - y > 160:
            x_brace(c, x - 10, x + 70, y + 30, LOW - 10, scale(TIMBER, 0.75), 2.4)
    c.put(c.mask(lambda p: p.poly([(x0, y0), (x1, y1), (x1, y1 + 16), (x0, y0 + 16)])), PLANK)
    c.put(c.mask(lambda p: p.line([(x0, y0), (x1, y1)], 2.4)), PLANK_LIGHT)
    # Old tram rails along the grade.
    c.put(c.mask(lambda p: p.line([(x0, y0 - 3), (x1, y1 - 3)], 1.6)), (120, 110, 100))
    # The water tower by the line.
    tx0, tx1, ttop = 2180, 2340, 1060
    planks(c, None, tx0, ttop, tx1, ttop + 120, (110, 80, 56), step=8.0, vertical=True, tag="rh_tank")
    c.put(c.mask(lambda p: [p.rect(tx0, y, tx1, y + 3) for y in (ttop + 20, ttop + 60, ttop + 100)]), (52, 48, 46))
    tin_roof(c, tx0 - 6, ttop - 20, tx1 + 6, ttop, "rh_lid", (140, 134, 126))
    for x in (2190, 2330):
        post(c, x, ttop + 120, LOW, 8, TIMBER)
    x_brace(c, 2190, 2330, ttop + 130, LOW - 10, scale(TIMBER, 0.8), 3.0)
    c.put(c.mask(lambda p: p.line([(tx0, ttop + 100), (2140, ttop + 140), (2140, ttop + 180)], 4)), STEEL_DARK)
    # The rails of the line east, on the street.
    c.put(c.mask(lambda p: [p.rect(x, LOW - 6, x + 16, LOW) for x in np.arange(1200, 2400, 24)]), (70, 56, 46))
    c.put(c.mask(box(1200, LOW - 8, 2400, LOW - 5)), (130, 126, 122))
    c.put(c.mask(box(2380, LOW - 220, 2388, LOW)), STEEL_DARK)
    c.put(c.mask(lambda p: p.poly([(2388, LOW - 210), (2398, LOW - 206), (2398, LOW - 196), (2388, LOW - 200)])), (60, 170, 80))


#: Every piece: its frame in its room, and how it is drawn.
PIECES: Dict[str, Piece] = {
    # frontier_siding_station
    "frontier_siding_station_house": Piece((620, 370, 1590, 640), station_house),
    # frontier_siding_street
    "frontier_lie_down_inn_front": Piece((150, 160, 690, 640), inn_front),
    "frontier_mercantile_front": Piece((670, 220, 1090, 640), mercantile_front),
    "frontier_siding_windmill": Piece((1100, 200, 1420, 640), siding_windmill),
    "frontier_telegraph_front": Piece((1430, 170, 2170, 640), telegraph_front),
    # frontier_lie_down_inn
    "frontier_lie_down_inn_room": Piece((16, 32, 1264, 512), inn_room),
    # frontier_siding_trestle
    "frontier_siding_trestle": Piece((0, 380, 2400, 1536), trestle, px=1.0),
    # frontier_sprocket_row
    "frontier_sprocket_arch": Piece((40, 360, 440, 640), sprocket_arch),
    "frontier_hettie_garage": Piece((470, 200, 1130, 640), hettie_garage),
    "frontier_parts_yard": Piece((1150, 470, 1590, 640), parts_yard),
    "frontier_rolling_gate": Piece((1630, 300, 1990, 640), rolling_gate),
    # frontier_freight_tail
    "frontier_freight_track_tail": Piece((0, 700, 2400, 752), lambda c, k: track(c, 2400), px=1.0),
    "frontier_caboose": Piece((10, 400, 500, 720), caboose),
    "frontier_box_car_1": Piece((530, 470, 1040, 720), box_car(544, 1024, 480, BOXCAR_RED, "box1")),
    "frontier_box_car_2": Piece((1074, 470, 1584, 720), box_car(1088, 1568, 480, BOXCAR_BROWN, "box2")),
    "frontier_flat_car_1": Piece((1636, 470, 2400, 720), flat_car(1648, 2400, [(1760, 1888, 544), (1888, 1968, 480)], "flat1", open_east=True)),
    # frontier_freight_cars
    "frontier_freight_track_cars": Piece((0, 700, 2800, 752), lambda c, k: track(c, 2800), px=1.0),
    "frontier_flat_car_1_end": Piece((0, 590, 380, 720), flat_car(0, 360, [], "flat1e", open_west=True)),
    "frontier_tank_car": Piece((410, 500, 920, 720), tank_car),
    "frontier_ore_car": Piece((954, 540, 1462, 720), ore_car),
    "frontier_box_car_3": Piece((1498, 486, 2006, 720), box_car(1512, 1992, 496, OCHRE_CAR, "box3")),
    "frontier_flat_car_2": Piece((2076, 530, 2800, 720), flat_car(2088, 2800, [(2560, 2688, 544)], "flat2", open_east=True)),
    # frontier_rustler_head
    "frontier_freight_track_head": Piece((0, 700, 2400, 752), lambda c, k: track(c, 2400), px=1.0),
    "frontier_flat_car_2_end": Piece((0, 530, 320, 720), flat_car(0, 300, [(180, 260, 544)], "flat2e", open_west=True)),
    "frontier_box_car_4": Piece((350, 470, 858, 720), box_car(364, 844, 480, BOXCAR_RED, "box4")),
    "frontier_rustler": Piece((720, 300, 2400, 720), rustler, px=1.0),
    # The loose crates (moving platforms' pictures).
    "frontier_loose_crate": Piece((0, 0, 64, 64), loose_crate),
    # frontier_clinker_yard
    "frontier_yard_tracks": Piece((0, 1240, 2400, 1420), yard_tracks, px=1.0),
    "frontier_tipple_road": Piece((480, 330, 2400, 1420), tipple_road, px=1.0),
    # frontier_clinker_works
    "frontier_furnace_house": Piece((90, 60, 720, 640), furnace_house),
    "frontier_slag_pots": Piece((690, 560, 1530, 640), slag_pots),
    "frontier_works_crane": Piece((800, 280, 1730, 640), works_crane),
    # frontier_clinker_row
    "frontier_row_shacks_west": Piece((220, 470, 860, 640), row_shacks([(240, 560, 528), (600, 840, 544)], "row_w")),
    "frontier_row_pump": Piece((880, 430, 1520, 640), row_pump),
    "frontier_row_shacks_east": Piece((1580, 470, 2260, 640), row_shacks([(1600, 1880, 528), (1960, 2240, 544)], "row_e")),
    # frontier_clinker_railhead
    "frontier_railhead_grade": Piece((0, 600, 2400, 1420), railhead_grade, px=1.0),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PAL", "PIECES", "TARGETS"]
