"""The hall of the Shadow Clan (`ninja_dojo`, PvN dimension): the clan's dojo,
between the village forest and the Mockingbird's arena.

Drawn in the room's coordinates (`_district_props`): the floor (y 608), the
two rafters walked on (y 384, x 320..512; y 320, x 736..928), the doors (to
the hub x 56, to the village forest x 720, to the arena x 1180).

- `shadow_dojo_hall`: dark timber posts and beams, lit shoji screens between
  them, the rafters as balconies on brackets, racks of practice swords and
  staffs, a gong, a shrine with a bonsai, paper lanterns, a hanging scroll
  of brush strokes, and the scroll the Mockingbird "corrected": bird
  footprints across its kata, feathers by the arena's door.

Everyday architecture, drawn with care: no costume and no joke at the
culture's cost (the joke is the bird's). Animations: ``idle``, 1 frame. No
drop shadows.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .eureka_props import Batch, edge_line
from .ninja_village_props import PAL

W, FLOOR = 1280, 608
RAFTERS = ((320, 512, 384), (736, 928, 320))
TIMBER = (44, 30, 24)
TIMBER_LIGHT = (96, 66, 46)
PAPER = (238, 226, 196)
INK = (30, 26, 28)
RED = (176, 40, 36)
GOLD = (210, 170, 80)
TATAMI = (170, 166, 110)


def shoji(c, x0, y0, x1, y1, lit=0.5):
    m = c.mask(box(x0, y0, x1, y1))
    c.put(m, PAPER)
    c.light(m, (255, 220, 160), lit)
    c.put(c.mask(lambda p: ([p.rect(x, y0, x + 1.4, y1) for x in np.arange(x0, x1 + 1, (x1 - x0) / 4)],
                            [p.rect(x0, y, x1, y + 1.4) for y in np.arange(y0, y1 + 1, (y1 - y0) / 6)])), TIMBER)


def scroll(c, x, top, h, tag, footprints=False):
    w = 46
    c.put(c.mask(box(x - 4, top - 4, x + w + 4, top)), TIMBER_LIGHT)
    c.put(c.mask(box(x, top, x + w, top + h)), PAPER)
    c.put(c.mask(box(x - 4, top + h, x + w + 4, top + h + 4)), TIMBER_LIGHT)
    rng = c.rand("brush", tag)
    for i in range(5):
        y = top + 12 + i * (h - 24) / 5
        pts = [(x + 10 + rng.uniform(-2, 2), y), (x + w / 2 + rng.uniform(-6, 6), y + rng.uniform(4, 10)), (x + w - 10, y + rng.uniform(-3, 6))]
        c.put(c.mask(lambda p: p.line(pts, rng.uniform(1.6, 3.2))), INK)
    c.put(c.mask(lambda p: p.rect(x + w - 12, top + h - 14, x + w - 5, top + h - 7)), RED)
    if footprints:
        for j in range(6):
            fx, fy = x + 6 + j * 7, top + 20 + j * (h - 40) / 6
            c.put(c.mask(lambda p: [p.line([(fx, fy), (fx + 4 * math.cos(a), fy - 4 * math.sin(a))], 0.9) for a in (math.radians(60), math.radians(90), math.radians(120), math.radians(270))]), (90, 90, 100))


def rack(c, x, kind):
    c.put(c.mask(lambda p: (p.rect(x - 2, FLOOR - 120, x + 2, FLOOR), p.rect(x + 74, FLOOR - 120, x + 78, FLOOR))), TIMBER)
    for y in (FLOOR - 104, FLOOR - 70, FLOOR - 36):
        c.put(c.mask(box(x - 4, y, x + 80, y + 4)), TIMBER_LIGHT)
        if kind == "swords":
            c.put(c.mask(lambda p: p.line([(x + 22, y - 4.5), (x + 76, y - 6)], 2.0)), (210, 212, 220))
            c.put(c.mask(lambda p: p.line([(x + 4, y - 4), (x + 22, y - 4.5)], 3.4)), (20, 18, 20))
            c.put(c.mask(lambda p: p.ellipse(x + 23, y - 4.5, 2.4, 3.4)), GOLD)
        else:
            c.put(c.mask(lambda p: p.line([(x - 8, y - 3), (x + 88, y - 3)], 3.0)), (210, 170, 110))


def hall(c, k):
    g = FLOOR
    back = c.mask(box(0, 0, W, g))
    c.put(back, (30, 22, 20))
    # Posts and beams, shoji between them (low ones; the rafters cross high).
    posts = list(range(0, W + 1, 160))
    for a, b in zip(posts, posts[1:]):
        shoji(c, a + 10, 180, b - 10, g - 80, 0.45)
    b_ = Batch(c)
    for x in posts:
        b_.add(TIMBER, 1.0, box(x - 8, 0, x + 8, g))
        b_.add(TIMBER_LIGHT, 1.0, box(x - 8, 0, x - 6, g))
    b_.add(TIMBER, 1.0, box(0, 160, W, 180))
    b_.add(TIMBER, 1.0, box(0, 40, W, 56))
    b_.draw()
    # A low wall under the screens, and the tatami edge on the floor.
    c.put(c.mask(box(0, g - 80, W, g)), (60, 42, 32))
    c.put(c.mask(box(0, g - 6, W, g)), TATAMI)
    c.put(c.mask(lambda p: [p.rect(x, g - 6, x + 3, g) for x in range(0, W, 96)]), (60, 60, 40))
    # The rafters as balconies on brackets, the walk lines light.
    for x0, x1, y in RAFTERS:
        c.put(c.mask(box(x0, y, x1, y + 14)), TIMBER)
        edge_line(c, x0, x1, y, TIMBER_LIGHT, 4)
        c.put(c.mask(lambda p: [p.poly([(x, y + 14), (x + 6, y + 14), (x + 24 * (1 if x < (x0 + x1) / 2 else -1) + 3, y + 46), (x + 24 * (1 if x < (x0 + x1) / 2 else -1) - 3, y + 46)]) for x in (x0 + 10, x1 - 16)]), TIMBER)
        c.put(c.mask(lambda p: (p.rect(x0, y - 26, x1, y - 23), [p.rect(x, y - 26, x + 2, y) for x in np.arange(x0 + 2, x1, 24)])), TIMBER_LIGHT, 0.9)
    # Racks, the gong, the shrine.
    rack(c, 150, "swords")
    rack(c, 560, "staffs")
    gx, gy = 1000, 300
    c.put(c.mask(lambda p: (p.rect(gx - 50, gy - 60, gx - 44, g), p.rect(gx + 44, gy - 60, gx + 50, g), p.rect(gx - 56, gy - 66, gx + 56, gy - 58))), TIMBER)
    gong = c.mask(lambda p: p.ellipse(gx, gy + 10, 36))
    c.put(gong, (190, 140, 60))
    c.put(c.mask(lambda p: [p.ring(gx, gy + 10, r, 1.0) for r in (12, 24, 32)]), (150, 100, 40), 0.8)
    c.light(c.mask(lambda p: p.ellipse(gx - 12, gy - 2, 10), blur=4), (255, 230, 170), 0.5)
    c.put(c.mask(lambda p: (p.line([(gx - 20, gy - 58), (gx - 16, gy - 24)], 1.0), p.line([(gx + 20, gy - 58), (gx + 16, gy - 24)], 1.0))), INK)
    sx = 880
    c.put(c.mask(lambda p: (p.rect(sx - 40, g - 60, sx + 40, g), p.rect(sx - 48, g - 66, sx + 48, g - 60))), TIMBER_LIGHT)
    c.put(c.mask(lambda p: p.poly([(sx - 10, g - 66), (sx + 10, g - 66), (sx + 7, g - 78), (sx - 7, g - 78)])), (110, 70, 50))
    rng = c.rand("bonsai")
    trunk = [(sx, g - 78), (sx - 6, g - 92), (sx + 4, g - 104), (sx - 2, g - 116)]
    c.put(c.mask(lambda p: p.line(trunk, 3)), (70, 50, 36))
    c.put(c.mask(lambda p: [p.ellipse(sx + dx, g - dy, rx, 6) for dx, dy, rx in ((-14, 98, 14), (10, 110, 12), (-4, 122, 13))]), (60, 110, 60))
    # Scrolls: one of brush strokes, and the one the Mockingbird corrected.
    scroll(c, 260, 196, 140, "kata")
    scroll(c, 1100, 196, 140, "mocked", footprints=True)
    # Paper lanterns.
    for lx in (80, 400, 700, 1180):
        c.put(c.mask(box(lx - 0.6, 56, lx + 0.6, 92)), INK)
        lan = c.mask(lambda p: p.ellipse(lx, 108, 14, 18))
        c.put(lan, RED)
        c.light(lan, (255, 200, 120), 0.4)
        c.put(c.mask(lambda p: [p.rect(lx - 14, y, lx + 14, y + 0.8) for y in (96, 104, 112, 120)]) * lan, (120, 20, 20), 0.6)
        c.light(c.mask(lambda p: p.ellipse(lx, 110, 40), blur=14), (255, 180, 100), 0.25)
    # Feathers by the arena's door.
    rng = c.rand("feathers")
    for _ in range(7):
        fx, fy, a = rng.uniform(1120, 1260), rng.uniform(g - 30, g - 4), rng.uniform(0, math.pi)
        ca, sa = math.cos(a), math.sin(a)
        vane = [(fx + ca * t * 10 - sa * w, fy + sa * t * 10 + ca * w) for t, w in ((-1, 0), (-0.4, 3.5), (0.6, 2.6), (1, 0), (0.6, -2), (-0.4, -2.6))]
        c.put(c.mask(lambda p: p.poly(vane)), (200, 204, 212))


PIECES: Dict[str, Piece] = {
    "shadow_dojo_hall": Piece((0, 0, W, FLOOR), hall),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
