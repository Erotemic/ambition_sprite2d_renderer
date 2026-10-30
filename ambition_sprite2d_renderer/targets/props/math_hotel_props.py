"""Hylbert's Hotel (Math dimension): the hotel that always has a room.

Drawn in each room's coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/math_town/make_specs.py`.

- `math_hotel_entrance`: its front, in one bay of the passage under Euclid
  Street's first terrace (x 2080..2240, the vault y 1184, the street y 1280):
  a brass revolving door under a striped canopy, an infinity over it, lit
  windows, bay trees in tubs.
- `math_hotel_lobby_room`: the lobby (1280 x 576, floor y 512): the front
  desk (its top y 464) with the bell and the register, the key rack behind
  it whose rows of hooks run off to a point and never end, a chandelier, the
  lift with its dial (the last mark on it is an infinity), a stair going up,
  palms, an armchair.
- `math_hotel_corridor_room`: the corridor (1600 x 448, floor y 384), which
  goes on: patterned paper, a runner, a door every 240 with a brass plate,
  sconces, a room-service trolley, a do-not-disturb card.

Animations: ``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .eureka_props import Batch, edge_line, panels, pendant
from .math_town_terraces import PAL, WALK

BRASS = PAL["brass"]
WOOD = (110, 62, 44)
WOOD_DARK = (70, 38, 28)
WOOD_LIGHT = (170, 110, 70)
CLARET = (128, 30, 44)
GREEN = (44, 92, 70)
PAPER = (232, 214, 170)
GOLD = (232, 190, 90)
NEON = (255, 120, 170)
CREAM = (236, 226, 200)

# The entrance, in the street's coordinates.
BAY_X0, BAY_X1, VAULT, STREET = 2080, 2240, 1184, 1280
DOOR_X = 2136
# The lobby.
LOBBY_W, LOBBY_H, LOBBY_FLOOR, LOBBY_CEILING = 1280, 576, 512, 32
DESK_X0, DESK_X1, DESK_TOP = 520, 760, 464
# The corridor.
CORR_W, CORR_H, CORR_FLOOR, CORR_CEILING = 1600, 448, 384, 32
CORR_DOORS = tuple(range(160, CORR_W - 100, 240))


def infinity(c, cx, cy, rx, colour, width=1.4, glow=0.0):
    pts = [(cx + rx * math.cos(t), cy + rx * 0.32 * math.sin(2 * t)) for t in np.linspace(0, math.tau, 80)]
    if glow:
        c.light(c.mask(lambda p: p.line(pts, width * 5), blur=4), colour, glow)
    c.put(c.mask(lambda p: p.line(pts, width)), colour)


def hotel_entrance(c, k):
    """The hotel's front in its bay of the passage."""
    x0, x1, top, g = BAY_X0, BAY_X1, VAULT, STREET
    # A cream front set into the bay's back wall.
    front = c.mask(box(x0 + 6, top + 18, x1 - 6, g))
    c.put(front, CREAM)
    c.tone(front * (c.noise("hotel_front", 8, 4, 2) - 0.5), 0.1)
    c.put(c.mask(lambda p: [p.rect(x, top + 18, x + 0.8, g) for x in np.arange(x0 + 14, x1 - 6, 12)]), scale(CREAM, 0.9), 0.6)
    # Lit windows either side.
    for wx in (x0 + 22, x1 - 22):
        k.window(wx, g - 66, 16, 26, "arch", lit=0.85, frame=GOLD, tag=("hotel_win", wx))
    # The revolving door: brass frame, four leaves of glass, warm inside.
    dx0, dx1 = DOOR_X - 2, DOOR_X + 50
    c.put(c.mask(lambda p: p.arch(dx0 - 4, g - 82, dx1 + 4, g)), BRASS)
    glass = c.mask(lambda p: p.arch(dx0, g - 78, dx1, g))
    c.put(glass, (60, 40, 30))
    c.light(glass, (255, 210, 140), 0.55)
    c.put(c.mask(lambda p: (p.rect(DOOR_X + 23, g - 70, DOOR_X + 25, g), p.line([(dx0 + 4, g - 40), (dx1 - 4, g - 30)], 1.6), p.line([(dx0 + 6, g - 26), (dx1 - 6, g - 44)], 1.6))), BRASS)
    c.put(c.mask(box(dx0 - 6, g - 3, dx1 + 6, g)), (60, 50, 44))
    # The canopy: claret and cream stripes, scalloped.
    k.awning(dx0 - 18, dx1 + 18, g - 92, 12, (CLARET, CREAM), tag="hotel_canopy")
    # The infinity over the canopy, lit.
    infinity(c, DOOR_X + 24, top + 30, 16, NEON, 1.6, glow=0.6)
    # Bay trees in tubs.
    for tx in (x0 + 14, x1 - 14):
        c.put(c.mask(lambda p: p.poly([(tx - 7, g - 16), (tx + 7, g - 16), (tx + 5, g), (tx - 5, g)])), WOOD)
        c.put(c.mask(lambda p: (p.rect(tx - 0.8, g - 34, tx + 0.8, g - 16), p.ellipse(tx, g - 40, 9))), (60, 110, 60))


def key_rack(c, x0, y0, x1, y1):
    """Rows of hooks with keys, the rows closing up toward a point so they
    never end."""
    c.put(c.mask(box(x0, y0, x1, y1)), WOOD_DARK)
    vx, vy = x1 - 6, (y0 + y1) / 2
    b = Batch(c)
    rows = 5
    for r in range(rows):
        y = y0 + 14 + r * (y1 - y0 - 24) / (rows - 1)
        for i in range(90):
            t = 1 - 0.93 ** i
            x = x0 + 10 + (vx - x0 - 10) * t
            yy = y + (vy - y) * t
            s = 1 - t
            if s < 0.06:
                break
            b.add(BRASS, 1.0, lambda p, x=x, yy=yy, s=s: (p.rect(x - 0.6 * s, yy - 4 * s, x + 0.6 * s, yy), p.ellipse(x, yy + 3 * s, 2.2 * s, 2.2 * s)))
            if (i * 7 + r * 3) % 5:
                b.add(GOLD, 1.0, lambda p, x=x, yy=yy, s=s: p.rect(x - 0.8 * s, yy + 4 * s, x + 0.8 * s, yy + 12 * s))
    b.draw()
    c.put(c.mask(lambda p: p.ellipse(vx, vy, 3)), GOLD)


def lobby_room(c, k):
    """The lobby."""
    x0, x1, g = 16, LOBBY_W - 16, LOBBY_FLOOR
    k.ground = g
    wall = c.mask(box(x0, LOBBY_CEILING, x1, g))
    c.put(wall, GREEN)
    stripes = ((c.x // 18) % 2).astype(np.float32)
    c.tone(wall * stripes, 0.08)
    panels(c, x0, g - 120, x1, g, WOOD, 10, "lobby_wainscot")
    c.put(c.mask(box(x0, LOBBY_CEILING, x1, LOBBY_CEILING + 18)), WOOD_DARK)
    c.put(c.mask(box(x0, LOBBY_CEILING + 18, x1, LOBBY_CEILING + 22)), GOLD)
    # The door back to the street (its zone x 40..88).
    c.put(c.mask(lambda p: p.arch(32, g - 120, 96, g)), BRASS)
    c.put(c.mask(lambda p: p.arch(38, g - 114, 90, g)), (60, 40, 30))
    c.light(c.mask(lambda p: p.arch(38, g - 114, 90, g)), (200, 220, 255), 0.25)
    # The key rack behind the desk, and the desk.
    key_rack(c, 460, 150, 840, 330)
    infinity(c, 650, 128, 22, GOLD, 2.0)
    panels(c, DESK_X0, DESK_TOP, DESK_X1, g, WOOD_LIGHT, 4, "desk")
    edge_line(c, DESK_X0 - 8, DESK_X1 + 8, DESK_TOP, (210, 160, 110), 6)
    bx = DESK_X0 + 40
    c.put(c.mask(lambda p: (p.rect(bx - 7, DESK_TOP - 2, bx + 7, DESK_TOP), p.ellipse(bx, DESK_TOP - 3, 5.5, 5), p.rect(bx - 0.6, DESK_TOP - 11, bx + 0.6, DESK_TOP - 7))), BRASS)
    rx = DESK_X1 - 60
    c.put(c.mask(lambda p: p.poly([(rx - 22, DESK_TOP - 2), (rx + 22, DESK_TOP - 2), (rx + 18, DESK_TOP - 8), (rx - 18, DESK_TOP - 8)])), PAPER)
    c.put(c.mask(lambda p: [p.rect(rx - 16, DESK_TOP - 7 + i * 1.4, rx + (8 if i % 2 else 14), DESK_TOP - 6.6 + i * 1.4) for i in range(4)]), (90, 80, 70))
    c.put(c.mask(lambda p: p.line([(rx + 10, DESK_TOP - 4), (rx + 26, DESK_TOP - 16)], 1.0)), (40, 40, 60))
    # The lift: a brass gate and its dial, whose last mark is an infinity.
    lx0, lx1 = 930, 1030
    c.put(c.mask(box(lx0 - 8, g - 170, lx1 + 8, g)), BRASS)
    c.put(c.mask(box(lx0, g - 160, lx1, g)), (40, 30, 26))
    c.put(c.mask(lambda p: [p.line([(x, g - 160), (x + 20, g)], 1.0) for x in np.arange(lx0 - 20, lx1, 10)] + [p.line([(x + 20, g - 160), (x, g)], 1.0) for x in np.arange(lx0 - 20, lx1, 10)]) * c.mask(box(lx0, g - 160, lx1, g)), BRASS, 0.85)
    dcx, dcy = (lx0 + lx1) / 2, g - 196
    c.put(c.mask(lambda p: p.ellipse(dcx, dcy, 26, 26) ), BRASS)
    c.put(c.mask(lambda p: p.ellipse(dcx, dcy, 22, 22)), CREAM)
    c.put(c.mask(lambda p: [p.ellipse(dcx + 18 * math.cos(a), dcy + 18 * math.sin(a), 1.2) for a in np.linspace(math.pi, 2 * math.pi, 7)[:-1]]), (60, 50, 40))
    infinity(c, dcx + 18, dcy, 3.2, (60, 50, 40), 0.9)
    c.put(c.mask(lambda p: p.line([(dcx, dcy), (dcx + 16, dcy - 2)], 1.4)), CLARET)
    # A stair up beside it (the floors above are not this room's).
    sx0 = 1060
    c.put(c.mask(lambda p: [p.rect(sx0 + i * 14, g - (i + 1) * 14, x1, g - i * 14) for i in range(14)]), WOOD)
    c.put(c.mask(lambda p: [p.rect(sx0 + i * 14, g - (i + 1) * 14, sx0 + i * 14 + 14, g - (i + 1) * 14 + 2) for i in range(14)]), WOOD_LIGHT)
    c.put(c.mask(lambda p: p.line([(sx0 + 6, g - 40), (sx0 + 200, g - 236)], 2.4)), BRASS)
    # A chandelier, palms, an armchair and a rug.
    cx, cy = 300, LOBBY_CEILING + 70
    c.put(c.mask(box(cx - 0.8, LOBBY_CEILING + 22, cx + 0.8, cy)), BRASS)
    c.put(c.mask(lambda p: (p.ellipse(cx, cy + 8, 40, 8), [p.line([(cx + dx, cy + 8), (cx + dx, cy - 6)], 1.2) for dx in (-34, -17, 0, 17, 34)])), BRASS)
    c.light(c.mask(lambda p: [p.ellipse(cx + dx, cy - 9, 3.5) for dx in (-34, -17, 0, 17, 34)], blur=2), (255, 230, 170), 0.9)
    c.light(c.mask(lambda p: p.ellipse(cx, cy + 60, 260, 150), blur=60), (255, 220, 160), 0.15)
    for px in (190, 880):
        c.put(c.mask(lambda p: p.poly([(px - 14, g - 30), (px + 14, g - 30), (px + 10, g), (px - 10, g)])), CLARET)
        rng = c.rand("palm", px)
        for _ in range(9):
            a = rng.uniform(-2.8, -0.3)
            L = rng.uniform(40, 70)
            pts = [(px + L * t * math.cos(a), g - 30 + L * t * math.sin(a) + 14 * t * t) for t in np.linspace(0, 1, 10)]
            c.put(c.mask(lambda p: p.line(pts, 3.2)), (60, 120, 60))
    ax = 300
    c.put(c.mask(lambda p: (p.rect(ax - 30, g - 38, ax + 30, g - 18), p.rect(ax - 34, g - 70, ax - 22, g - 18), p.rect(ax + 22, g - 70, ax + 34, g - 18), p.rect(ax - 28, g - 80, ax + 28, g - 36))), CLARET)
    c.put(c.mask(lambda p: [p.rect(x - 2, g - 18, x + 2, g) for x in (ax - 26, ax + 26)]), WOOD_DARK)
    c.put(c.mask(lambda p: p.ellipse(640, g - 1, 220, 4)), CLARET, 0.8)


def corridor_room(c, k):
    """The corridor that goes on."""
    x0, x1, g = 0, CORR_W, CORR_FLOOR
    k.ground = g
    wall = c.mask(box(x0, CORR_CEILING, x1, g))
    c.put(wall, (150, 60, 66))
    # Damask: a repeating lozenge.
    lz = ((np.abs(((c.x % 36) - 18)) / 18 + np.abs(((c.y % 48) - 24)) / 24) < 0.5).astype(np.float32)
    c.put(wall * lz, (170, 80, 84), 0.7)
    panels(c, x0, g - 90, x1, g, WOOD, 20, "corr_wainscot")
    c.put(c.mask(box(x0, CORR_CEILING, x1, CORR_CEILING + 14)), WOOD_DARK)
    c.put(c.mask(box(x0, g - 4, x1, g)), CLARET)
    # The doors, each with a brass plate (its number is the room's label).
    for dx in CORR_DOORS:
        c.put(c.mask(box(dx - 30, g - 132, dx + 30, g)), WOOD_DARK)
        door = c.mask(box(dx - 24, g - 126, dx + 24, g))
        c.put(door, WOOD)
        c.put(c.mask(lambda p: (p.rect(dx - 18, g - 118, dx + 18, g - 70), p.rect(dx - 18, g - 60, dx + 18, g - 10))) * door, WOOD_LIGHT, 0.35)
        c.put(c.mask(lambda p: p.ellipse(dx + 16, g - 62, 2.4)), BRASS)
        c.put(c.mask(box(dx - 12, g - 146, dx + 12, g - 136)), BRASS)
    # Sconces between the doors.
    for sx in [d + 120 for d in CORR_DOORS[:-1]]:
        c.put(c.mask(lambda p: (p.rect(sx - 1, CORR_CEILING + 90, sx + 1, CORR_CEILING + 110), p.poly([(sx - 7, CORR_CEILING + 90), (sx + 7, CORR_CEILING + 90), (sx + 4, CORR_CEILING + 78), (sx - 4, CORR_CEILING + 78)]))), BRASS)
        c.light(c.mask(lambda p: p.ellipse(sx, CORR_CEILING + 84, 30, 34), blur=10), (255, 220, 160), 0.45)
    # A room-service trolley and a do-not-disturb card.
    tx = CORR_DOORS[2] + 70
    c.put(c.mask(lambda p: (p.rect(tx - 26, g - 36, tx + 26, g - 32), p.rect(tx - 26, g - 12, tx + 26, g - 9), p.rect(tx - 24, g - 36, tx - 22, g - 4), p.rect(tx + 22, g - 36, tx + 24, g - 4))), (200, 200, 210))
    c.put(c.mask(lambda p: (p.ellipse(tx - 6, g - 40, 12, 7), p.ellipse(tx + 14, g - 39, 4, 3))), (220, 220, 230))
    c.put(c.mask(lambda p: [p.ellipse(x, g - 3, 3) for x in (tx - 22, tx + 22)]), (40, 40, 44))
    dd = CORR_DOORS[4]
    c.put(c.mask(lambda p: (p.rect(dd + 12, g - 76, dd + 22, g - 54), p.ring(dd + 17, g - 78, 3, 0.8))), (240, 220, 120))


# The lift's shaft (640 x 1600): the car runs at x 320..448; the landing's top
# is y 1572 (40 under the car's top, 68 over the shaft's bottom).
SHAFT_W, SHAFT_H = 640, 1600
SHAFT_CAR_X0, SHAFT_CAR_X1 = 320, 448
SHAFT_LANDING = SHAFT_H - 68 + 40


def lift_shaft(c, k):
    """The shaft: brick, the car's rails and cables, a brass band at each
    floor, the landing and its gate."""
    m = c.mask(box(16, 0, SHAFT_W - 16, SHAFT_H))
    c.put(m, (70, 44, 40))
    rows = ((c.y // 10) % 2).astype(np.float32)
    joints = (((c.y % 10) < 1) | ((((c.x + rows * 12) % 24) < 1))).astype(np.float32)
    c.put(m * joints, (44, 28, 26), 0.8)
    c.tone(m * (c.noise("shaft", 6, 20, 2) - 0.5), 0.2)
    for x in (SHAFT_CAR_X0 - 10, SHAFT_CAR_X1 + 4):
        c.put(c.mask(box(x, 0, x + 6, SHAFT_H)), (110, 116, 126))
        c.put(c.mask(box(x, 0, x + 2, SHAFT_H)), (170, 176, 186))
    for x in (370, 384, 398):
        c.put(c.mask(box(x - 0.8, 0, x + 0.8, SHAFT_H)), (40, 40, 44))
    for y in range(SHAFT_H - 360, 100, -320):
        c.put(c.mask(box(16, y + 30, SHAFT_W - 16, y + 36)), BRASS)
        if y < 600:  # the high floors: an infinity on their bands
            infinity(c, 560, y + 10, 10, GOLD, 1.0)
    c.put(c.mask(box(16, SHAFT_LANDING, SHAFT_CAR_X0 - 32, SHAFT_H)), (90, 60, 44))
    edge_line(c, 16, SHAFT_CAR_X0 - 32, SHAFT_LANDING, (170, 120, 80), 5)
    c.put(c.mask(lambda p: [p.line([(x, SHAFT_LANDING - 110), (x + 18, SHAFT_LANDING)], 1.2) for x in np.arange(120, 260, 12)] + [p.line([(x + 18, SHAFT_LANDING - 110), (x, SHAFT_LANDING)], 1.2) for x in np.arange(120, 260, 12)]), BRASS, 0.9)


PIECES: Dict[str, Piece] = {
    "math_hotel_entrance": Piece((BAY_X0, VAULT, BAY_X1, STREET), hotel_entrance),
    "math_hotel_lobby_room": Piece((16, LOBBY_CEILING, LOBBY_W - 16, LOBBY_FLOOR), lobby_room),
    "math_hotel_corridor_room": Piece((0, CORR_CEILING, CORR_W, CORR_FLOOR), corridor_room),
    "math_hotel_lift_shaft": Piece((16, 0, SHAFT_W - 16, SHAFT_H), lift_shaft),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
