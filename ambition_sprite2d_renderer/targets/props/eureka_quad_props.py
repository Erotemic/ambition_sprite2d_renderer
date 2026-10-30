"""Eureka's quad (`eureka_quad`, gate address SCIENCE), filled in between the
Patent Office and the observatory.

Drawn in room coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/eureka/make_specs.py` (`quad`): the street
(y 768); the raised walk (y 576, x 16..576) and its stair (y 704 at x
560..656, y 640 at x 600..664); the cafe's awning (y 656, x 1000..1200);
the lecture hall's steps (y 704 at x 1440..1536, y 640 at x 1520..1616) and
its terrace (y 576, x 1600..2320); the lab's door (x 2440..2488).

- `quad_raised_walk`: an arcade of sandstone arches under the walk, its
  balustrade, the stair's stone treads.
- `quad_cafe`: the Uncertain Cup: a shopfront under a striped awning (its
  top walked on), cups in the window, two tables out front.
- `quad_lecture_hall`: a colonnade under the terrace, tall windows lit
  between the columns, the hall's steps, the terrace's balustrade.
- `quad_fountain`: a fountain whose basin is a Klein bottle, pouring into
  itself.
- `quad_lab_front`: Tesseract Laboratories: red brick and a sawtooth roof, a
  tesla coil on the ridge, sparking.
- `court_furniture` (the gate court, `court`): the founders' plinth with a
  bronze light bulb on it, a bench, lamp posts, the steps, the raised walk
  on its arcade.

Animations: ``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .eureka_props import (BRICK, COPPER, IRON, IRON_LIGHT, OAK, OAK_DARK, PAL, SANDSTONE, SANDSTONE_DARK, Batch, arc, ashlar, bolt_points,
                           edge_line, tesla_coil)

STREET, WALK = 768, 576
WALK_X1 = 576
STAIR = ((560, 656, 704), (600, 664, 640))
AWNING = (1000, 1200, 656)
HALL_STEPS = ((1440, 1536, 704), (1520, 1616, 640))
TERRACE = (1600, 2320, 576)
#: The lecture hall's arch that is the stair down to the collider.
COLLIDER_ARCH = 1800
LAB_DOOR = (2440, 2488)
TRIM = (238, 230, 210)
GLASS = (150, 200, 226)
LAMP = (255, 222, 150)
WATER = (140, 200, 230)


def balustrade(c, x0, x1, y):
    c.put(c.mask(box(x0, y - 30, x1, y - 24)), TRIM)
    c.put(c.mask(lambda p: [p.ellipse(x, y - 13, 3.2, 9) for x in np.arange(x0 + 8, x1 - 4, 14)]), TRIM)
    c.tone(c.mask(lambda p: [p.ellipse(x + 1.5, y - 13, 1.6, 9) for x in np.arange(x0 + 8, x1 - 4, 14)]), -0.2)


def raised_walk(c, k):
    ashlar(c, 16, WALK, WALK_X1, STREET, SANDSTONE, tag="arcade")
    c.put(c.mask(lambda p: [p.arch(x, WALK + 50, x + 80, STREET) for x in range(40, WALK_X1 - 80, 120)]), (70, 80, 90))
    c.put(c.mask(lambda p: [p.arch(x + 4, WALK + 54, x + 76, STREET) for x in range(40, WALK_X1 - 80, 120)]), (110, 150, 120), 0.6)
    edge_line(c, 16, WALK_X1, WALK, TRIM, 8)
    balustrade(c, 16, WALK_X1, WALK)
    for x0, x1, y in STAIR:
        c.put(c.mask(box(x0, y, x1, STREET)), SANDSTONE_DARK)
        edge_line(c, x0, x1, y, TRIM, 5)


def cafe(c, k):
    x0, x1, aw = AWNING
    ashlar(c, x0 + 10, aw - 70, x1 - 10, STREET, SANDSTONE, tag="cafe")
    edge_line(c, x0 + 6, x1 - 6, aw - 70, TRIM, 6)
    win = c.mask(box(x0 + 30, aw + 14, x0 + 120, STREET - 20))
    c.put(win, GLASS)
    c.light(win * np.clip((c.y - (aw + 14)) / 80, 0, 1), LAMP, 0.4)
    c.put(c.mask(lambda p: [p.rect(x, aw + 60, x + 8, aw + 70) for x in range(x0 + 40, x0 + 116, 16)]), (240, 240, 236))
    c.put(c.mask(box(x0 + 136, aw + 14, x0 + 176, STREET)), OAK_DARK)
    # The awning: stripes, scalloped, its top the walk line.
    stripes = c.mask(lambda p: [p.poly([(x, aw), (x + 20, aw), (x + 24, aw + 26), (x + 4, aw + 26)]) for x in range(x0, x1, 40)])
    c.put(c.mask(lambda p: p.poly([(x0, aw), (x1, aw), (x1 + 4, aw + 26), (x0 + 4, aw + 26)])), (240, 236, 224))
    c.put(stripes, (60, 110, 120))
    c.put(c.mask(lambda p: [p.ellipse(x + 10, aw + 26, 10, 6) for x in range(x0, x1, 20)]), (60, 110, 120))
    edge_line(c, x0, x1, aw, (90, 140, 150), 3)
    # Tables out front, a cup on each.
    for tx in (x1 + 10, x1 + 70):
        c.put(c.mask(lambda p: (p.ellipse(tx, STREET - 34, 18, 3), p.rect(tx - 1.5, STREET - 34, tx + 1.5, STREET), p.rect(tx - 10, STREET - 2, tx + 10, STREET))), IRON)
        c.put(c.mask(lambda p: p.rect(tx - 3, STREET - 42, tx + 3, STREET - 36)), (240, 240, 236))


def lecture_hall(c, k):
    t0, t1, ty = TERRACE
    ashlar(c, t0, ty, t1, STREET, SANDSTONE, tag="hall")
    edge_line(c, t0, t1, ty, TRIM, 10)
    # Tall windows between columns, lit.
    cols = list(range(t0 + 20, t1, 90))
    for a, b in zip(cols, cols[1:]):
        if a == COLLIDER_ARCH:
            continue
        w = c.mask(lambda p: p.arch(a + 22, ty + 40, b - 8, STREET - 30))
        c.put(w, (60, 80, 100))
        c.light(w, LAMP, 0.35)
        c.put(w * c.mask(lambda p: [p.rect(x, ty + 40, x + 1.4, STREET) for x in np.arange(a + 30, b - 8, 12)]), (90, 80, 70))
    # One arch is the stair down to the collider (the quad's door zone,
    # x 1828..1876): a doorway to the street, its door, the ring's plaque.
    a, b = COLLIDER_ARCH, COLLIDER_ARCH + 90
    c.put(c.mask(lambda p: p.arch(a + 22, ty + 40, b - 8, STREET)), (24, 28, 36))
    c.put(c.mask(lambda p: [p.rect(a + 26, y, b - 12, y + 2) for y in range(STREET - 40, STREET, 10)]), (50, 56, 66))
    c.put(c.mask(box(a + 28, STREET - 96, a + 76, STREET)), (60, 90, 120))
    c.put(c.mask(lambda p: p.rect(a + 32, STREET - 90, a + 72, STREET - 60)), (150, 200, 226), 0.6)
    c.put(c.mask(lambda p: p.ellipse(a + 68, STREET - 46, 2.4)), (220, 200, 120))
    c.put(c.mask(lambda p: p.ellipse(a + 52, ty + 66, 13)), (40, 70, 140))
    c.put(c.mask(lambda p: p.ring(a + 52, ty + 66, 8, 2)), (240, 220, 140))
    b = Batch(c)
    for x in cols:
        b.add(TRIM, 1.0, box(x, ty + 16, x + 18, STREET - 8))
        b.add(SANDSTONE_DARK, 1.0, box(x + 13, ty + 16, x + 18, STREET - 8))
        b.add(TRIM, 1.0, box(x - 4, ty + 10, x + 22, ty + 18))
        b.add(TRIM, 1.0, box(x - 4, STREET - 10, x + 22, STREET))
    b.draw()
    balustrade(c, t0, 2080, ty)
    for x0, x1, y in HALL_STEPS:
        c.put(c.mask(box(x0, y, x1, STREET)), SANDSTONE_DARK)
        edge_line(c, x0, x1, y, TRIM, 5)


def fountain(c, k):
    cx, g = 1340, STREET
    c.put(c.mask(lambda p: (p.rect(cx - 80, g - 24, cx + 80, g), p.ellipse(cx, g - 24, 80, 8))), SANDSTONE_DARK)
    c.put(c.mask(lambda p: p.ellipse(cx, g - 24, 72, 6)), WATER)
    # The Klein bottle: a bulb whose neck bends down and back into its own side.
    glass = (180, 220, 236)
    c.put(c.mask(lambda p: p.ellipse(cx - 10, g - 70, 30, 34)), glass, 0.8)
    neck = [(cx + 6, g - 102), (cx + 14, g - 140), (cx + 44, g - 150), (cx + 60, g - 120), (cx + 50, g - 80), (cx + 26, g - 66), (cx + 10, g - 66)]
    c.put(c.mask(lambda p: p.line(neck, 10)), glass, 0.8)
    c.put(c.mask(lambda p: p.line(neck, 2)), (240, 250, 255))
    c.put(c.mask(lambda p: p.ring(cx - 10, g - 70, 30, 1.6)), (240, 250, 255))
    # Water pouring out of the mouth and back into itself.
    c.put(c.mask(lambda p: p.line([(cx - 40, g - 70), (cx - 50, g - 50), (cx - 52, g - 26)], 3)), WATER, 0.9)
    c.put(c.mask(lambda p: [p.ellipse(cx + dx, g - 30, 3, 2) for dx in (-56, -48, 30)]), (230, 245, 255))


def lab_front(c, k):
    d0, d1 = LAB_DOOR
    x0, x1, top = 2340, 2780, 560
    ashlar(c, x0, top, x1, STREET, BRICK, course=10, block=20, tag="lab_brick", vary=0.1)
    # Sawtooth roof, its glazing to the north.
    teeth = [(x, top) for x in range(x0, x1, 88)]
    for x, y in teeth:
        c.put(c.mask(lambda p: p.poly([(x, y), (x + 88, y), (x + 88, y - 50)])), IRON)
        c.put(c.mask(lambda p: p.poly([(x + 70, y - 2), (x + 86, y - 2), (x + 86, y - 44)])), GLASS, 0.8)
    c.put(c.mask(box(x0 - 6, top - 4, x1 + 6, top + 6)), IRON_LIGHT)
    # Windows, the door's frame.
    c.put(c.mask(lambda p: [p.rect(x, top + 50, x + 40, top + 120) for x in (x0 + 30, x0 + 210, x0 + 300, x0 + 380) if x + 40 < x1]), (60, 80, 100))
    c.light(c.mask(lambda p: [p.rect(x, top + 50, x + 40, top + 120) for x in (x0 + 30, x0 + 210, x0 + 300, x0 + 380) if x + 40 < x1]), (190, 220, 255), 0.4)
    # The door (the room's door zone is this): oak planks in an iron frame.
    c.put(c.mask(box(d0 - 12, STREET - 116, d1 + 12, STREET)), IRON)
    c.put(c.mask(box(d0, STREET - 104, d1, STREET)), OAK)
    c.put(c.mask(lambda p: [p.rect(x, STREET - 104, x + 1.2, STREET) for x in np.arange(d0 + 8, d1, 8)]), OAK_DARK)
    c.put(c.mask(lambda p: [p.rect(d0, y, d1, y + 4) for y in (STREET - 90, STREET - 30)]), IRON)
    c.put(c.mask(lambda p: p.ellipse(d1 - 8, STREET - 52, 3)), (220, 190, 110))
    c.put(c.mask(lambda p: p.ellipse((d0 + d1) / 2, STREET - 76, 7)), (220, 230, 240))
    # The coil on the ridge, sparking at the sky.
    tesla_coil(c, x0 + 330, top - 40, top - 170, r_toroid=28, tag="lab_roof_coil")
    rng = c.rand("roof_arc")
    for _ in range(3):
        arc(c, bolt_points(rng, (x0 + 330, top - 176), (x0 + 330 + rng.uniform(-90, 90), top - 260), n=8, jag=10), width=1.6)


#: The gate court's numbers (`make_specs.py` `court`): its floor, the
#: plinth (x 640..768, top 640), the bench (x 860..1020, top 672), the steps
#: (y 640 at x 1080..1176, y 576 at x 1160..1256), the raised walk (y 512
#: from x 1232).
COURT_FLOOR, COURT_WALK = 704, 512


def court(c, k):
    g = COURT_FLOOR
    # The founders' plinth, and on it a bronze light bulb, lit.
    c.put(c.mask(box(640, 640, 768, g)), SANDSTONE_DARK)
    edge_line(c, 632, 776, 640, TRIM, 6)
    c.put(c.mask(box(670, 660, 738, 680)), (170, 130, 60))
    bx, by = 704, 572
    c.put(c.mask(lambda p: (p.ellipse(bx, by, 30, 34), p.rect(bx - 14, by + 26, bx + 14, 634))), (176, 132, 70))
    c.put(c.mask(lambda p: [p.rect(bx - 15, y, bx + 15, y + 3) for y in (608, 616, 624)]), (120, 90, 48))
    c.light(c.mask(lambda p: p.ellipse(bx - 8, by - 10, 12), blur=6), LAMP, 0.6)
    c.light(c.mask(lambda p: p.ellipse(bx, by, 70), blur=20), LAMP, 0.2)
    # The bench: slats on iron legs.
    c.put(c.mask(lambda p: [p.rect(860, y, 1020, y + 5) for y in (672, 650, 640)]), OAK)
    c.put(c.mask(lambda p: [p.rect(x, 640, x + 6, g) for x in (870, 1004)]), IRON)
    # Lamp posts.
    for lx in (560, 1040):
        c.put(c.mask(lambda p: (p.rect(lx - 3, g - 140, lx + 3, g), p.rect(lx - 8, g - 6, lx + 8, g))), IRON)
        c.put(c.mask(lambda p: p.ellipse(lx, g - 148, 9, 11)), LAMP)
        c.light(c.mask(lambda p: p.ellipse(lx, g - 148, 40), blur=12), LAMP, 0.3)
    # The steps and the raised walk on its arcade, its balustrade.
    for x0, x1, y in ((1080, 1176, 640), (1160, 1256, 576)):
        c.put(c.mask(box(x0, y, x1, g)), SANDSTONE_DARK)
        edge_line(c, x0, x1, y, TRIM, 5)
    ashlar(c, 1232, COURT_WALK, 1600, g, SANDSTONE, tag="court_arcade")
    c.put(c.mask(lambda p: [p.arch(x, COURT_WALK + 50, x + 80, g) for x in range(1280, 1560, 120)]), (70, 80, 90))
    c.put(c.mask(lambda p: [p.arch(x + 4, COURT_WALK + 54, x + 76, g) for x in range(1280, 1560, 120)]), (110, 150, 120), 0.6)
    edge_line(c, 1232, 1600, COURT_WALK, TRIM, 8)
    balustrade(c, 1232, 1600, COURT_WALK)


def busker(c, k):
    """The busker's kit in the arcade's middle arch: a theremin on its stand
    (a box, its pitch antenna up and its volume loop out), an open case with
    a few coins and a card."""
    g = COURT_FLOOR
    tx = 1406
    c.put(c.mask(lambda p: (p.line([(tx, g), (tx + 12, g - 40)], 2), p.line([(tx + 24, g), (tx + 12, g - 40)], 2), p.line([(tx + 12, g), (tx + 12, g - 40)], 2))), IRON)
    c.put(c.mask(box(tx - 8, g - 52, tx + 32, g - 40)), OAK_DARK)
    c.put(c.mask(lambda p: p.rect(tx - 8, g - 53, tx + 32, g - 51)), OAK)
    c.put(c.mask(lambda p: (p.rect(tx + 28, g - 96, tx + 30, g - 52), p.ring(tx - 14, g - 50, 6, 1.6), p.line([(tx - 8, g - 48), (tx - 8, g - 46)], 1.6))), IRON_LIGHT)
    c.put(c.mask(lambda p: [p.line([(tx + 34 + i * 6, g - 80 - i * 4), (tx + 38 + i * 6, g - 86 - i * 4)], 1.2) for i in range(3)]), LAMP, 0.7)
    cx = 1466
    c.put(c.mask(lambda p: p.poly([(cx - 18, g), (cx + 18, g), (cx + 16, g - 8), (cx - 16, g - 8)])), (60, 40, 50))
    c.put(c.mask(lambda p: p.rect(cx - 15, g - 7, cx + 15, g - 2)), (150, 40, 60))
    c.put(c.mask(lambda p: [p.ellipse(cx + dx, g - 5, 2) for dx in (-8, -2, 5)]), (230, 200, 90))
    c.put(c.mask(lambda p: p.poly([(cx - 4, g - 8), (cx + 12, g - 12), (cx + 14, g - 4), (cx - 2, g - 2)])), TRIM)


PIECES: Dict[str, Piece] = {
    "court_furniture": Piece((520, 470, 1600, COURT_FLOOR), court),
    "court_busker": Piece((1380, COURT_FLOOR - 104, 1500, COURT_FLOOR), busker),
    "quad_raised_walk": Piece((16, WALK - 40, 680, STREET), raised_walk),
    "quad_cafe": Piece((990, 480, 1300, STREET), cafe),
    "quad_lecture_hall": Piece((1430, WALK - 40, 2330, STREET), lecture_hall),
    "quad_fountain": Piece((1250, 600, 1430, STREET), fountain),
    "quad_lab_front": Piece((2330, 300, 2790, STREET), lab_front),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
