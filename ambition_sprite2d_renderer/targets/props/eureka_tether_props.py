"""The Eureka tether (gate address SCIENCE): the space elevator's ground
station and its cars.

Use the room dimensions in `eureka/make_specs.py`.

- `eureka_tether_hall`: a hall of steel and glass round the foot of the
  tether (the sky and the town through the glazing); the roof truss and the
  bearing ring the ribbon goes up through; the shaft's guide rails; the
  ribbon, anchored in the floor; stairs and galleries on girders; the
  operator's console; the departures board; the altimeter; the banners
  of the institute.
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
GALLERIES = ((16, 904, 1024), (1144, 1584, 1024))
STEPS = ((464, 576, 1280), (416, 528, 1216), (352, 464, 1152), (288, 400, 1088),
         (1120, 1232, 1280), (1184, 1296, 1216), (1248, 1360, 1152), (1312, 1424, 1088))
WEST_DOOR_TOP = 1248
CONSOLE_X = 720
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


def notice(c, left, right, top, bottom):
    c.put(c.mask(box(left, top, right, bottom)), STEEL)
    c.put(c.mask(box(left + 4, top + 4, right - 4, bottom - 4)), SCREEN)
    c.put(c.mask(lambda p: [p.ellipse(x, top + 8, 1.6)
                            for x in (left + 8, right - 8)]), BRASS)


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
        for px_ in (x0 + 24, (x0 + x1) // 2, x1 - 34):
            c.put(c.mask(box(px_, y + 26, px_ + 10, g)), IRON)
    for left, right, top in STEPS:
        c.put(c.mask(lambda p: (
            p.rect(left + 13, top + 12, left + 19, g),
            p.rect(right - 20, top + 12, right - 14, g),
            p.line([(left + 16, top + 42), (left + 36, top + 12)], 4),
            p.line([(right - 17, top + 42), (right - 37, top + 12)], 4),
        )), IRON)
        c.put(c.mask(box(left, top, right, top + 15)), STEEL)
        c.put(c.mask(box(left, top, right, top + 3)), IRON_LIGHT)
        c.put(c.mask(lambda p: [p.ellipse(x, top + 8, 1.5)
                                for x in range(left + 9, right - 4, 18)]), IRON)
    hazard(c, 880, 1024, 904, 1028, step=8)
    hazard(c, 1144, 1024, 1168, 1028, step=8)
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
    notice(c, 86, 532, 802, 950)
    c.put(c.mask(box(102, 842, 516, 846)), STEEL)
    rng = c.rand("board")
    dots = [(x, y) for y in (866, 897, 928) for x in np.arange(108, 420, 7) if rng.random() < 0.55]
    c.put(c.mask(lambda p: [p.ellipse(x, y, 2) for x, y in dots]), AMBER)
    arrow = c.mask(lambda p: p.poly([(472, 861), (494, 885), (481, 885), (481, 930), (463, 930), (463, 885), (450, 885)]))
    c.put(arrow, GREEN)
    c.light(c.mask(lambda p: p.ellipse(472, 895, 30), blur=10), GREEN, 0.25)
    # The altimeter: brass ring, a needle at the station's height.
    ax, ay, ar = 1368, 812, 88
    c.put(c.mask(lambda p: p.ellipse(ax, ay, ar)), BRASS)
    c.put(c.mask(lambda p: p.ellipse(ax, ay, ar - 10)), (236, 230, 210))
    c.put(c.mask(lambda p: [p.line([(ax + (ar - 14) * math.cos(t), ay + (ar - 14) * math.sin(t)), (ax + (ar - 26 if i % 5 else ar - 34) * math.cos(t), ay + (ar - 26 if i % 5 else ar - 34) * math.sin(t))], 1.6)
                            for i, t in enumerate(np.linspace(math.radians(135), math.radians(405), 41))]), (40, 40, 44))
    t = math.radians(380)
    c.put(c.mask(lambda p: p.line([(ax, ay), (ax + (ar - 22) * math.cos(t), ay + (ar - 22) * math.sin(t))], 3)), RIBBON)
    c.put(c.mask(lambda p: p.ellipse(ax, ay, 6)), IRON)
    notice(c, 1186, 1550, 919, 983)
    notice(c, 703, 951, 1170, 1213)
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
