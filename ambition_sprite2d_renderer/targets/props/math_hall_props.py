"""The gate hall under the Math town (`math_gate_hall`): the arrivals hall of
the Math dimension, a vaulted undercroft (its parallax draws the vault).

Drawn in room coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/math_town/make_specs.py` (`gate_hall`): the
floor (y 704), the galleries (y 512: x 64..416 and 1184..1536), the gate's
cradle in the middle (x 560..1040), the door up to the town (x 1488).

- `math_hall_west`: the Manifest Office's booth (shuttered, an abacus in its
  window, closed for recounting) and, up on the west gallery, the customs
  desk where arrivals declare their axioms (stamps, a pile of forms, a
  turnstile).
- `math_hall_east`: the departures board over the east gallery, every
  destination a glyph and the infinity service cancelled in red; a porter's
  cart of trunks by the door (a hatbox strapped with a Moebius band).
- `math_hall_lamps`: lamps under the vault: polyhedra (a cube, an
  octahedron, an icosahedron) on chains, and banners of pi, sigma and
  infinity between them.

Animations: ``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .eureka_props import Batch, edge_line, panels
from .math_hotel_props import BRASS, CLARET, CREAM, GOLD, GREEN, PAPER, WOOD, WOOD_DARK, WOOD_LIGHT, infinity
from .math_town_terraces import PAL

W, FLOOR, VAULT = 1600, 704, 48
GALLERY_W = (64, 416, 512)
GALLERY_E = (1184, 1536, 512)
IRON = (46, 50, 58)
AMBER = (255, 186, 80)
RED = (230, 70, 60)
LAMP = (255, 222, 160)


def abacus(c, x0, y0, x1, y1):
    c.put(c.mask(box(x0, y0, x1, y1)), WOOD_DARK)
    c.put(c.mask(box(x0 + 4, y0 + 4, x1 - 4, y1 - 4)), (40, 30, 26))
    rows = np.linspace(y0 + 10, y1 - 10, 5)
    c.put(c.mask(lambda p: [p.rect(x0 + 4, y, x1 - 4, y + 1.2) for y in rows]), BRASS)
    rng = c.rand("abacus")
    beads = [(x0 + 10 + rng.randint(0, 3) * 7 + j * 7 + (x1 - x0 - 50) * (j > 2), y) for y in rows for j in range(5)]
    c.put(c.mask(lambda p: [p.ellipse(x, y + 0.6, 3.4, 3.0) for x, y in beads]), CLARET)


def west(c, k):
    g = FLOOR
    # The Manifest Office: a booth against the west wall, its shutter half
    # down over a window with the abacus, the ledgers piled at its foot.
    bx0, bx1 = 24, 196
    panels(c, bx0, g - 150, bx1, g, WOOD, 3, "manifest")
    c.put(c.mask(lambda p: p.poly([(bx0 - 8, g - 150), (bx1 + 8, g - 150), (bx1, g - 170), (bx0, g - 170)])), GREEN)
    c.put(c.mask(box(bx0 + 20, g - 136, bx1 - 20, g - 76)), (30, 26, 24))
    abacus(c, bx0 + 34, g - 116, bx1 - 34, g - 80)
    shutter = c.mask(box(bx0 + 20, g - 136, bx1 - 20, g - 112))
    c.put(shutter, (150, 140, 120))
    c.put(shutter * c.mask(lambda p: [p.rect(bx0 + 20, y, bx1 - 20, y + 1) for y in range(int(g - 132), int(g - 112), 4)]), (100, 94, 80))
    c.put(c.mask(box(bx0 + 14, g - 78, bx1 - 14, g - 72)), WOOD_LIGHT)
    for i, (w, col) in enumerate(((40, CLARET), (36, GREEN), (42, (52, 62, 100)), (34, CLARET))):
        y = g - 8 - i * 9
        c.put(c.mask(box(bx1 + 10, y, bx1 + 10 + w, y + 8)), col)
        c.put(c.mask(box(bx1 + 10, y + 2, bx1 + 10 + w - 3, y + 6)), PAPER, 0.8)
    # The customs desk up on the west gallery: forms, stamps, a turnstile.
    x0, x1, y = GALLERY_W
    dx = 180
    desk = c.mask(box(dx, y - 46, dx + 140, y))
    panels(c, dx, y - 46, dx + 140, y, WOOD_DARK, 2, "customs")
    edge_line(c, dx - 6, dx + 146, y - 50, WOOD_LIGHT, 5)
    rng = c.rand("forms")
    for i in range(7):
        c.put(c.mask(lambda p: p.poly([(dx + 16 + rng.uniform(-2, 2), y - 52 - i * 2.5), (dx + 50, y - 53 - i * 2.5), (dx + 50, y - 50 - i * 2.5), (dx + 16, y - 49 - i * 2.5)])), PAPER)
    for sx_ in (dx + 80, dx + 100):
        c.put(c.mask(lambda p: (p.rect(sx_ - 6, y - 60, sx_ + 6, y - 52), p.rect(sx_ - 2, y - 72, sx_ + 2, y - 60), p.ellipse(sx_, y - 74, 5, 4))), (40, 34, 30))
    c.put(c.mask(lambda p: p.ellipse(dx + 126, y - 54, 8, 3)), RED)
    tx = 120
    c.put(c.mask(lambda p: (p.rect(tx - 6, y - 40, tx + 6, y), [p.line([(tx, y - 30), (tx + 26 * math.cos(a), y - 30 + 10 * math.sin(a))], 3) for a in (0.3, 2.4, 4.4)])), BRASS)


def departures(c, x0, y0, x1, y1):
    c.put(c.mask(box(x0 - 6, y0 - 6, x1 + 6, y1 + 6)), WOOD_DARK)
    c.put(c.mask(box(x0, y0, x1, y1)), (20, 20, 24))
    rows = 4
    rh = (y1 - y0) / rows
    rng = c.rand("departures")
    b = Batch(c)
    for r in range(rows):
        cy = y0 + rh * (r + 0.5)
        # A destination: a glyph, then its time in dots; the last row is the
        # infinity service, cancelled.
        gx = x0 + 22
        if r == rows - 1:
            continue
        kind = r % 3
        if kind == 0:
            b.add(AMBER, 1.0, lambda p, gx=gx, cy=cy: p.poly([(gx - 9, cy + 8), (gx + 9, cy + 8), (gx, cy - 9)]))
        elif kind == 1:
            b.add(AMBER, 1.0, lambda p, gx=gx, cy=cy: p.ring(gx, cy, 8, 2))
        else:
            b.add(AMBER, 1.0, lambda p, gx=gx, cy=cy: p.rect(gx - 8, cy - 8, gx + 8, cy + 8))
        for x in np.arange(x0 + 50, x1 - 70, 7):
            if rng.random() < 0.6:
                b.add(AMBER, 1.0, lambda p, x=x, cy=cy: p.ellipse(x, cy, 1.8))
        for x in np.arange(x1 - 56, x1 - 12, 7):
            b.add(AMBER, 1.0, lambda p, x=x, cy=cy, rx=rng.random(): p.ellipse(x, cy, 1.8) if rx < 0.7 else None)
    b.draw()
    cy = y0 + rh * (rows - 0.5)
    infinity(c, x0 + 22, cy, 12, RED, width=2.0, glow=0.3)
    c.put(c.mask(lambda p: [p.ellipse(x, cy, 1.8) for x in np.arange(x0 + 50, x1 - 12, 7)]), RED)
    c.put(c.mask(lambda p: p.line([(x0 + 44, cy + 6), (x1 - 10, cy - 6)], 2)), RED)


def east(c, k):
    g = FLOOR
    x0, x1, y = GALLERY_E
    departures(c, x0 + 20, y - 190, x1 - 20, y - 96)
    c.put(c.mask(lambda p: [p.rect(x, y - 260, x + 2, y - 196) for x in (x0 + 60, x1 - 62)]), IRON)
    # The porter's cart of trunks, west of the door.
    cx0, cx1 = 1360, 1470
    c.put(c.mask(lambda p: (p.rect(cx0, g - 22, cx1, g - 14), p.rect(cx1 - 4, g - 70, cx1, g - 14))), IRON)
    c.put(c.mask(lambda p: [p.ellipse(x, g - 8, 8) for x in (cx0 + 14, cx1 - 14)]), (30, 30, 34))
    for (a, b_, top, col) in ((cx0 + 4, cx0 + 64, g - 58, CLARET), (cx0 + 68, cx1 - 8, g - 50, (52, 62, 100)), (cx0 + 12, cx0 + 58, g - 90, GREEN)):
        tr = c.mask(box(a, top, b_, g - 22))
        c.put(tr, col)
        c.put(c.mask(lambda p: [p.rect(x, top, x + 3, g - 22) for x in (a + 8, b_ - 11)]), WOOD_DARK)
        c.put(c.mask(box(a, top, b_, top + 3)), mix(col, (255, 255, 255), 0.3))
        c.tone(tr * np.clip((c.x - (a + b_) / 2) / ((b_ - a) / 2), -1, 1), -0.2)
    c.put(c.mask(lambda p: p.ellipse(cx0 + 30, g - 72, 6)), GOLD)
    c.put(c.mask(lambda p: p.poly([(cx0 + 90, g - 66), (cx0 + 100, g - 58), (cx0 + 80, g - 58)])), CREAM)
    # A hatbox on top, strapped with a Moebius band.
    hx, hy = cx0 + 96, g - 66
    c.put(c.mask(lambda p: (p.rect(hx - 18, hy - 22, hx + 18, hy), p.ellipse(hx, hy - 22, 18, 5))), CREAM)
    band = [(hx + 18 * math.cos(t), hy - 11 + 4 * math.sin(t) + 6 * math.sin(t / 2) * math.cos(t)) for t in np.linspace(0, 2 * math.pi, 40)]
    c.put(c.mask(lambda p: p.line(band, 2.4)), CLARET)


def lamps(c, k):
    def chain(x, y1):
        c.put(c.mask(box(x - 0.8, VAULT, x + 0.8, y1)), IRON)

    def lit(x, y, r):
        c.light(c.mask(lambda p: p.ellipse(x, y, r * 3), blur=14), LAMP, 0.3)

    def shape(pts, edges, colour=BRASS):
        c.put(c.mask(lambda p: p.poly([pts[i] for i in hull(pts)])), mix(LAMP, (255, 255, 255), 0.2))
        c.put(c.mask(lambda p: [p.line([pts[a], pts[b]], 1.6) for a, b in edges]), colour)

    def hull(pts):
        idx = sorted(range(len(pts)), key=lambda i: pts[i])
        def turn(o, a, b):
            return (pts[a][0] - pts[o][0]) * (pts[b][1] - pts[o][1]) - (pts[a][1] - pts[o][1]) * (pts[b][0] - pts[o][0])
        lower, upper = [], []
        for i in idx:
            while len(lower) >= 2 and turn(lower[-2], lower[-1], i) <= 0:
                lower.pop()
            lower.append(i)
        for i in reversed(idx):
            while len(upper) >= 2 and turn(upper[-2], upper[-1], i) <= 0:
                upper.pop()
            upper.append(i)
        return lower[:-1] + upper[:-1]

    def project(verts, cx, cy, s, rot=0.5):
        out = []
        for x, y, z in verts:
            x, z = x * math.cos(rot) - z * math.sin(rot), x * math.sin(rot) + z * math.cos(rot)
            y, z = y * math.cos(0.4) - z * math.sin(0.4), y * math.sin(0.4) + z * math.cos(0.4)
            out.append((cx + s * x, cy + s * y))
        return out

    cube = [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    cube_e = [(a, b) for a in range(8) for b in range(a + 1, 8) if sum(u != v for u, v in zip(cube[a], cube[b])) == 1]
    octa = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
    octa_e = [(a, b) for a in range(6) for b in range(a + 1, 6) if a // 2 != b // 2]
    ph = (1 + 5 ** 0.5) / 2
    ico = [v for a in (-1, 1) for b in (-ph, ph) for v in ((0, a, b), (a, b, 0), (b, 0, a))]
    ico_e = [(a, b) for a in range(12) for b in range(a + 1, 12) if abs(sum((u - v) ** 2 for u, v in zip(ico[a], ico[b])) - 4) < 1e-6]
    for x, (verts, edges, s), drop in ((200, (cube, cube_e, 14), 150), (480, (octa, octa_e, 20), 190), (1120, (ico, ico_e, 12), 190), (1400, (cube, cube_e, 14), 150)):
        chain(x, drop - 20)
        lit(x, drop, 18)
        shape(project(verts, x, drop, s), edges)
    # Banners between the lamps: pi, sigma, infinity on claret.
    for bx, glyph in ((340, "pi"), (1260, "sigma"), (800, "inf")):
        top = VAULT + 4
        m = c.mask(lambda p: p.poly([(bx - 34, top), (bx + 34, top), (bx + 34, top + 150), (bx, top + 170), (bx - 34, top + 150)]))
        c.put(m, CLARET if glyph != "inf" else GREEN)
        c.put(c.mask(box(bx - 34, top, bx + 34, top + 6)), BRASS)
        gy = top + 80
        if glyph == "pi":
            c.put(c.mask(lambda p: (p.line([(bx - 20, gy - 16), (bx + 20, gy - 18)], 4), p.line([(bx - 8, gy - 16), (bx - 12, gy + 20)], 4),
                                    p.line([(bx + 8, gy - 17), (bx + 10, gy + 16), (bx + 16, gy + 20)], 4))), GOLD)
        elif glyph == "sigma":
            c.put(c.mask(lambda p: p.line([(bx + 18, gy - 20), (bx - 16, gy - 20), (bx + 4, gy), (bx - 16, gy + 20), (bx + 18, gy + 20)], 4)), GOLD)
        else:
            infinity(c, bx, gy, 22, GOLD, width=3.5)


PIECES: Dict[str, Piece] = {
    "math_hall_west": Piece((16, 300, 460, FLOOR), west),
    "math_hall_east": Piece((1150, 300, 1590, FLOOR), east),
    "math_hall_lamps": Piece((0, VAULT, W, 240), lamps),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
