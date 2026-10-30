"""The Eureka tether (gate address SCIENCE): the space elevator's ground
station and its cars.

Drawn in room coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/eureka/make_specs.py` (`elevator_station`):
the floor (y 1344), the roof (to y 48) open over the shaft (x 960..1088),
the galleries (y 1024: x 16..496 and 1200..1584), the way west to the quad
(y 1248..1344), the operator by her console (x 720), the down car's platform
(x 360).

- `eureka_tether_hall`: a hall of steel and glass round the foot of the
  tether (the sky and the town through the glazing); the roof truss and the
  bearing ring the ribbon goes up through; the shaft's guide rails; the
  ribbon, anchored in the floor; railed galleries on girders; the operator's
  console (an altitude curve, a lever); a departure board; a great
  altimeter; the down car's capsule tube and its hatch; the institute's
  banners.
- `eureka_tether_car`: the car, a platform look (`platform_looks.ron`): its
  floor is the platform (span x 0..128 at y 0, in the car's own units), a
  glazed capsule round the rider, the clamp that rides the ribbon over and
  under it, a beacon.

Animations: ``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .eureka_props import BRASS, GOLD, IRON, IRON_LIGHT, NAVY, PAL, RIBBON, SANDSTONE, SANDSTONE_DARK, Batch, edge_line, panels

W, FLOOR, ROOF = 1600, 1344, 48
SHAFT = (960, 1088)
GALLERIES = ((16, 496, 1024), (1200, 1584, 1024))
WEST_DOOR_TOP = 1248
CONSOLE_X = 720
DOWN_PAD_X = 360
TETHER = (1016, 1032)
STEEL = (88, 96, 110)
GLASS = (176, 210, 236)
HAZARD = (232, 186, 52)
AMBER = (255, 180, 70)
GREEN = (110, 230, 140)
SCREEN = (16, 30, 34)

#: The car, in its own units: its floor (the platform's top) at y 0 over x
#: 0..128 (`CAR_W`), drawn in the frame below. `platform_looks.ron` states
#: these in frame pixels: px 2, frame (-24, -150)..(152, 40).
CAR_FRAME = (-24, -150, 152, 40)
CAR_SPAN = (0, 128)


def hazard(c, x0, y0, x1, y1, step=12):
    m = c.mask(box(x0, y0, x1, y1))
    c.put(m, HAZARD)
    stripes = ((np.floor((c.x - c.y) / step) % 2) == 0).astype(np.float32)
    c.put(m * stripes, (30, 30, 34))


def ribbon(c, x0, x1, y0, y1):
    """The tether's ribbon: dark composite, a lit edge, gauge marks."""
    c.put(c.mask(box(x0, y0, x1, y1)), (58, 62, 74))
    c.put(c.mask(box(x0, y0, x0 + 2, y1)), (160, 170, 190))
    c.put(c.mask(lambda p: [p.rect(x0 + 3, y, x1 - 3, y + 2) for y in np.arange(y0 + 20, y1, 64)]), (120, 128, 146))


def hall(c, k):
    g = FLOOR
    s0, s1 = SHAFT
    # The glazing: the sky through it, tinted, its reflections.
    glass = c.mask(box(0, 120, W, 1160))
    c.put(glass, GLASS, 0.22)
    c.light(c.mask(lambda p: [p.poly([(x, 1160), (x + 60, 1160), (x + 360, 120), (x + 300, 120)]) for x in range(-300, W, 520)], blur=6) * glass,
            (255, 255, 255), 0.12)
    b = Batch(c)
    for y in range(224, 1160, 104):
        b.add(STEEL, 1.0, box(0, y, W, y + 4))
    cols = [x for x in range(0, W + 1, 200) if not s0 - 20 < x < s1 + 20]
    for x in cols:
        b.add(IRON, 1.0, box(x - 7, 120, x + 7, g))
        b.add(IRON_LIGHT, 1.0, box(x - 7, 120, x - 5, g))
    b.draw()
    # The low wall: the institute's sandstone, panelled.
    panels(c, 0, 1160, W, g, SANDSTONE, 16, "station_wall")
    edge_line(c, 0, W, 1156, SANDSTONE_DARK, 6)
    hazard(c, s0 - 24, 1170, s1 + 24, 1182)
    # The roof truss, and the bearing ring the ribbon goes up through.
    chords = c.mask(lambda p: (p.rect(0, 40, W, 54), p.rect(0, 116, W, 130)))
    c.put(chords, IRON)
    c.put(c.mask(lambda p: [p.line([(x, 54), (x + 40, 116)], 4) for x in range(0, W, 80)] + [p.line([(x + 40, 116), (x + 80, 54)], 4) for x in range(0, W, 80)]), IRON)
    c.put(c.mask(box(0, 116, W, 118)), IRON_LIGHT)
    ring = c.mask(lambda p: p.rect(s0 - 28, 30, s1 + 28, 140))
    c.put(ring, STEEL)
    c.put(c.mask(box(s0 - 4, 30, s1 + 4, 140)), (36, 40, 50))
    c.put(c.mask(lambda p: [p.ellipse(x, y, 3) for x in (s0 - 18, s1 + 18) for y in range(44, 136, 18)]), IRON_LIGHT)
    # The shaft: guide rails, braced; the ribbon down the middle into its anchor.
    for rx in (s0 - 12, s1 + 2):
        c.put(c.mask(box(rx, 140, rx + 10, g)), STEEL)
        c.put(c.mask(box(rx, 140, rx + 2, g)), IRON_LIGHT)
    c.put(c.mask(lambda p: [p.rect(s0 - 30, y, s0 - 12, y + 6) for y in range(240, g, 160)] + [p.rect(s1 + 12, y, s1 + 30, y + 6) for y in range(240, g, 160)]), IRON)
    ribbon(c, *TETHER, 0, g)
    anchor = c.mask(lambda p: p.poly([(990, g), (996, g - 14), (1052, g - 14), (1058, g)]))
    c.put(anchor, IRON)
    c.put(c.mask(lambda p: [p.ellipse(x, g - 7, 2.4) for x in (1002, 1014, 1034, 1046)]), BRASS)
    # The galleries: walks on girders, railed, on posts.
    for x0, x1, y in GALLERIES:
        edge_line(c, x0, x1, y, STEEL, 10)
        c.put(c.mask(box(x0, y + 10, x1, y + 26)), IRON)
        c.put(c.mask(lambda p: [p.line([(x, y + 10), (x + 16, y + 26)], 2) for x in range(x0, x1 - 16, 32)] + [p.line([(x + 16, y + 10), (x, y + 26)], 2) for x in range(x0, x1 - 16, 32)]), STEEL)
        c.put(c.mask(lambda p: (p.rect(x0, y - 36, x1, y - 32), [p.rect(x, y - 36, x + 3, y) for x in range(x0 + 4, x1, 40)], p.rect(x0, y - 18, x1, y - 16))), IRON_LIGHT)
        for px_ in (x0 + 24, x1 - 34):
            c.put(c.mask(box(px_, y + 26, px_ + 10, g)), IRON)
    # Banners of the institute: an atom on navy, a red hem.
    for bx in (180, 1480):
        m = c.mask(lambda p: p.poly([(bx - 40, 130), (bx + 40, 130), (bx + 40, 420), (bx, 450), (bx - 40, 420)]))
        c.put(m, NAVY)
        c.put(m * c.mask(box(bx - 40, 400, bx + 40, 460)), RIBBON)
        c.put(c.mask(lambda p: p.ellipse(bx, 270, 5)), GOLD)
        for a in (0, 60, 120):
            t = math.radians(a)
            pts = [(bx + 30 * math.cos(u) * math.cos(t) - 11 * math.sin(u) * math.sin(t), 270 + 30 * math.cos(u) * math.sin(t) + 11 * math.sin(u) * math.cos(t))
                   for u in np.linspace(0, 2 * math.pi, 40)]
            c.put(c.mask(lambda p: p.line(pts, 1.6)), GOLD)
    # The departure board: amber dot rows, the up arrow lit.
    c.put(c.mask(box(440, 250, 900, 390)), (24, 24, 28))
    c.put(c.mask(box(440, 250, 900, 256)), STEEL)
    rng = c.rand("board")
    dots = [(x, y) for y in (284, 320, 356) for x in np.arange(470, 820, 7) if rng.random() < 0.55]
    c.put(c.mask(lambda p: [p.ellipse(x, y, 2) for x, y in dots]), AMBER)
    arrow = c.mask(lambda p: p.poly([(860, 272), (884, 304), (870, 304), (870, 360), (850, 360), (850, 304), (836, 304)]))
    c.put(arrow, GREEN)
    c.light(c.mask(lambda p: p.ellipse(860, 316, 34), blur=10), GREEN, 0.25)
    # The altimeter: brass ring, a needle at the station's height.
    ax, ay, ar = 1300, 520, 92
    c.put(c.mask(lambda p: p.ellipse(ax, ay, ar)), BRASS)
    c.put(c.mask(lambda p: p.ellipse(ax, ay, ar - 10)), (236, 230, 210))
    c.put(c.mask(lambda p: [p.line([(ax + (ar - 14) * math.cos(t), ay + (ar - 14) * math.sin(t)), (ax + (ar - 26 if i % 5 else ar - 34) * math.cos(t), ay + (ar - 26 if i % 5 else ar - 34) * math.sin(t))], 1.6)
                            for i, t in enumerate(np.linspace(math.radians(135), math.radians(405), 41))]), (40, 40, 44))
    t = math.radians(380)
    c.put(c.mask(lambda p: p.line([(ax, ay), (ax + (ar - 22) * math.cos(t), ay + (ar - 22) * math.sin(t))], 3)), RIBBON)
    c.put(c.mask(lambda p: p.ellipse(ax, ay, 6)), IRON)
    # The down car's tube from the roof to its hatch by the platform.
    tx = DOWN_PAD_X
    tube = c.mask(box(tx - 22, 130, tx + 22, 1210))
    c.put(tube, GLASS, 0.35)
    c.put(c.mask(lambda p: (p.rect(tx - 22, 130, tx - 19, 1210), p.rect(tx + 19, 130, tx + 22, 1210), [p.rect(tx - 26, y, tx + 26, y + 8) for y in range(200, 1210, 200)])), STEEL)
    cap = c.mask(lambda p: (p.rect(tx - 16, 640, tx + 16, 700), p.ellipse(tx, 640, 16, 10), p.ellipse(tx, 700, 16, 10)))
    c.put(cap, (210, 214, 222))
    c.put(c.mask(box(tx - 16, 664, tx + 16, 674)), RIBBON)
    hatch = c.mask(lambda p: p.ellipse(tx, 1270, 52))
    c.put(hatch, STEEL)
    c.put(c.mask(lambda p: p.ellipse(tx, 1270, 40)), (40, 46, 58))
    c.put(c.mask(lambda p: [p.ellipse(tx + 46 * math.cos(a), 1270 + 46 * math.sin(a), 2.4) for a in np.linspace(0, 2 * math.pi, 12, endpoint=False)]), IRON_LIGHT)
    c.put(c.mask(lambda p: p.ellipse(tx, 1206, 6)), GREEN)
    c.light(c.mask(lambda p: p.ellipse(tx, 1206, 20), blur=6), GREEN, 0.3)
    # The operator's console, west of where she stands.
    cx = CONSOLE_X - 130
    desk = c.mask(lambda p: p.poly([(cx, g), (cx, g - 70), (cx + 20, g - 96), (cx + 110, g - 96), (cx + 110, g)]))
    c.put(desk, STEEL)
    c.tone(desk * np.clip((g - 70 - c.y) / 26, 0, 1), 0.15)
    c.put(c.mask(box(cx + 10, g - 160, cx + 100, g - 100)), IRON)
    scr = c.mask(box(cx + 16, g - 154, cx + 94, g - 106))
    c.put(scr, SCREEN)
    curve = [(cx + 20 + i * 3, g - 110 - 40 * (1 - math.exp(-i / 8))) for i in range(25)]
    c.put(c.mask(lambda p: p.line(curve, 1.6)), GREEN)
    c.light(scr, GREEN, 0.15)
    c.put(c.mask(lambda p: [p.ellipse(cx + 34 + i * 14, g - 82, 3.5) for i in range(5)]), AMBER)
    c.put(c.mask(lambda p: [p.ellipse(cx + 48 + i * 14, g - 82, 3.5) for i in range(0, 4, 2)]), GREEN)
    c.put(c.mask(lambda p: p.line([(cx + 96, g - 90), (cx + 116, g - 128)], 4)), IRON_LIGHT)
    c.put(c.mask(lambda p: p.ellipse(cx + 117, g - 130, 7)), RIBBON)
    # The way west: a steel frame round the opening.
    c.put(c.mask(lambda p: (p.rect(16, WEST_DOOR_TOP - 20, 70, WEST_DOOR_TOP), p.rect(54, WEST_DOOR_TOP, 70, g))), STEEL)
    c.put(c.mask(box(16, WEST_DOOR_TOP - 20, 70, WEST_DOOR_TOP - 18)), IRON_LIGHT)


def car(c, k):
    x0, x1 = CAR_SPAN
    # The capsule round the rider: a glazed back, its ribs, the roof.
    back = c.mask(lambda p: (p.rect(x0 - 6, -124, x1 + 6, 0), p.ellipse((x0 + x1) / 2, -124, (x1 - x0) / 2 + 6, 14)))
    c.put(back, (60, 92, 118), 0.75)
    c.light(back * np.clip((-60 - c.y) / 64, 0, 1), (150, 200, 230), 0.3)
    c.put(c.mask(lambda p: [p.rect(x, -130, x + 3, 0) for x in (x0 + 30, x1 - 33)]), STEEL)
    roof = c.mask(lambda p: (p.rect(x0 - 10, -136, x1 + 10, -124), p.ellipse((x0 + x1) / 2, -136, (x1 - x0) / 2 + 4, 8)))
    c.put(roof, (210, 214, 222))
    c.tone(roof * np.clip((c.y + 136) / 12, 0, 1), -0.25)
    for px_ in (x0 - 12, x1 + 2):
        c.put(c.mask(box(px_, -130, px_ + 10, 0)), STEEL)
        c.put(c.mask(box(px_, -130, px_ + 2, 0)), IRON_LIGHT)
    # The clamp over the roof that rides the ribbon, and its beacon.
    mid = (x0 + x1) / 2
    c.put(c.mask(box(mid - 18, -150, mid + 18, -136)), IRON)
    c.put(c.mask(lambda p: [p.ellipse(mid + dx, -143, 5) for dx in (-11, 11)]), IRON_LIGHT)
    c.put(c.mask(lambda p: p.ellipse(x1 - 6, -142, 4)), AMBER)
    c.light(c.mask(lambda p: p.ellipse(x1 - 6, -142, 12), blur=4), AMBER, 0.4)
    # The floor (the platform), its hazard edge, the clamp under it.
    c.put(c.mask(box(x0 - 12, 0, x1 + 12, 14)), STEEL)
    hazard(c, x0, 0, x1, 4, step=8)
    c.put(c.mask(lambda p: p.poly([(mid - 30, 14), (mid + 30, 14), (mid + 16, 34), (mid - 16, 34)])), IRON)
    c.put(c.mask(lambda p: [p.ellipse(mid + dx, 26, 6) for dx in (-13, 13)]), IRON_LIGHT)
    c.put(c.mask(lambda p: p.ellipse(x0 + 8, 8, 2.4)), GREEN)


PIECES: Dict[str, Piece] = {
    "eureka_tether_hall": Piece((0, 0, W, FLOOR), hall),
    "eureka_tether_car": Piece(CAR_FRAME, car),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["CAR_FRAME", "CAR_SPAN", "PIECES", "TARGETS"]
