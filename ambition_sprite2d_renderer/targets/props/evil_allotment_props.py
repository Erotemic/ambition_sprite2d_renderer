"""The Castle Allotments (`evil_castle_allotments`, the Evil dimension): out
of town, west of the Searchlight Moor: where the castle grows its
vegetables. Evil needs its greens.

Drawn in room coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/evil_moor/make_specs.py` (`allotments`):
the ground (y 656); the raised beds, walked on (BEDS: x0, x1, top); the
water butt (x 860..900, top 592) and the greenhouse's roof (x 470..850,
y 512), walked on; the gardener's fence (x 380).

- `allotment_west`: the gardener's shed (tools on the wall, seed packets,
  a mug), the fence and its gate, the greenhouse (whitewashed panes, a
  grapevine of nightshade inside, its roof walked on), the water butt.
- `allotment_beds`: raised beds of the castle's vegetables: pumpkins that
  grow their own scowls and glow, cabbages with teeth, mandrakes (only
  their leaves; do not pull), a trellis of nightshade; a compost heap
  steaming; the scarecrow in the castle's helmet; the show bench with the
  prize marrow and its rosette.

Silhouettes against the moor's red sky, lit on their left by it, as the
moor. Animations: ``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .eureka_props import Batch, edge_line
from .evil_forest_props import NEAR_BLACK, PAL, RIM, rim

FLOOR = 656
BEDS = ((960, 1160, 624), (1240, 1440, 624), (1520, 1720, 624))
BUTT = (860, 900, 592)
ROOF = (470, 850, 512)
FENCE_X = 380
TIMBER = (34, 26, 24)
EARTH = (40, 28, 24)
LEAF = (34, 52, 32)
LEAF_LIGHT = (70, 96, 52)
PUMPKIN = (200, 90, 30)
GLOW = (255, 170, 60)
CABBAGE = (90, 70, 110)
GLASS = (150, 150, 140)


def west(c, k):
    g = FLOOR
    # The shed: boards, a lean roof, the tools on its wall.
    shed = c.mask(lambda p: p.poly([(60, g), (60, g - 120), (280, g - 140), (280, g)]))
    c.put(shed, TIMBER)
    c.put(shed * c.mask(lambda p: [p.rect(x, g - 150, x + 1.2, g) for x in range(72, 280, 16)]), NEAR_BLACK)
    rim(c, shed)
    c.put(c.mask(lambda p: p.poly([(48, g - 116), (292, g - 142), (292, g - 150), (48, g - 124)])), NEAR_BLACK)
    c.put(c.mask(box(110, g - 90, 160, g - 50)), (120, 40, 30))  # its one window, lit
    c.put(c.mask(lambda p: (p.rect(134, g - 90, 136, g - 50), p.rect(110, g - 71, 160, g - 69))), TIMBER)
    for x, (a, b) in zip((190, 214, 238), (((0, -60), (0, -20)), ((0, -64), (0, -24)), ((0, -58), (0, -20)))):
        c.put(c.mask(lambda p: p.line([(x, g + a[1]), (x, g + b[1])], 2.2)), (110, 100, 96))
    c.put(c.mask(lambda p: (p.poly([(184, g - 20), (196, g - 20), (190, g - 6)]), p.rect(208, g - 24, 220, g - 20), [p.line([(232 + i * 3, g - 20), (232 + i * 3, g - 12)], 1) for i in range(5)])), (110, 100, 96))
    # The fence, its gate open.
    c.put(c.mask(lambda p: ([p.rect(x, g - 40, x + 4, g) for x in range(300, FENCE_X + 20, 14)], p.rect(296, g - 32, FENCE_X + 24, g - 29), p.rect(296, g - 16, FENCE_X + 24, g - 13))), TIMBER)
    c.put(c.mask(lambda p: [p.poly([(x, g - 40), (x + 2, g - 46), (x + 4, g - 40)]) for x in range(300, FENCE_X + 20, 14)]), TIMBER)
    # The greenhouse: a frame of glazing bars, panes whitewashed, its roof
    # (walked on) a ridge of glass over a gutter.
    x0, x1, roof = ROOF
    walls = c.mask(box(x0, roof + 10, x1, g))
    c.put(walls, GLASS, 0.35)
    c.put(walls * c.mask(lambda p: [p.rect(x0, y, x1, y + 2) for y in range(roof + 10, g, 36)]), TIMBER)
    c.put(walls * c.mask(lambda p: [p.rect(x, roof + 10, x + 2, g) for x in range(x0, x1 + 1, 38)]), TIMBER)
    c.put(c.mask(box(x0 - 4, roof, x1 + 4, roof + 10)), TIMBER)
    edge_line(c, x0, x1, roof, (90, 60, 50), 4)
    # Nightshade inside, on wires: dark leaves, the berries.
    rng = c.rand("greenhouse")
    vines = [[(x, g), (x + rng.uniform(-14, 14), g - 60), (x + rng.uniform(-20, 20), roof + 20)] for x in range(x0 + 30, x1 - 20, 60)]
    c.put(c.mask(lambda p: [p.line(v, 2) for v in vines]), LEAF)
    c.put(c.mask(lambda p: [p.ellipse(rng.uniform(x0 + 20, x1 - 20), rng.uniform(roof + 24, g - 20), 7, 4) for _ in range(40)]), LEAF_LIGHT)
    c.put(c.mask(lambda p: [p.ellipse(rng.uniform(x0 + 20, x1 - 20), rng.uniform(roof + 30, g - 30), 2.4) for _ in range(30)]), (30, 20, 50))
    # The water butt, walked on.
    bx0, bx1, btop = BUTT
    butt = c.mask(box(bx0, btop, bx1, g))
    c.put(butt, TIMBER)
    c.put(butt * c.mask(lambda p: [p.rect(bx0, y, bx1, y + 3) for y in (btop + 10, g - 16)]), (70, 66, 66))
    edge_line(c, bx0, bx1, btop, (90, 60, 50), 3)
    rim(c, butt)


def pumpkin(b, x, g, r):
    b.add(PUMPKIN, 1.0, lambda p: (p.ellipse(x, g - r, r * 1.25, r), p.ellipse(x - r * 0.5, g - r, r * 0.8, r * 0.95), p.ellipse(x + r * 0.5, g - r, r * 0.8, r * 0.95)))
    b.add(scale(PUMPKIN, 0.6), 1.0, lambda p: [p.line([(x + d, g - 2 * r + 2), (x + d * 1.1, g - 2)], 1) for d in (-r * 0.45, r * 0.45)])
    # Its scowl: brows down, a ragged grin, lit from inside.
    b.add(GLOW, 1.0, lambda p: (p.poly([(x - r * 0.6, g - r * 1.25), (x - r * 0.15, g - r * 1.05), (x - r * 0.55, g - r * 0.95)]),
                                p.poly([(x + r * 0.6, g - r * 1.25), (x + r * 0.15, g - r * 1.05), (x + r * 0.55, g - r * 0.95)]),
                                p.poly([(x - r * 0.7, g - r * 0.7), (x - r * 0.35, g - r * 0.5), (x, g - r * 0.65), (x + r * 0.35, g - r * 0.5), (x + r * 0.7, g - r * 0.7), (x + r * 0.4, g - r * 0.3), (x - r * 0.4, g - r * 0.3)])))
    b.add(LEAF, 1.0, lambda p: p.line([(x, g - 2 * r), (x + 3, g - 2 * r - 7)], 3))


def beds(c, k):
    g = FLOOR
    rng = c.rand("beds")
    # The beds: boarded boxes of earth, their tops walked on.
    for x0, x1, top in BEDS:
        bed = c.mask(box(x0, top, x1, g))
        c.put(bed, TIMBER)
        c.put(bed * c.mask(lambda p: p.rect(x0, top + 14, x1, top + 16)), NEAR_BLACK)
        c.put(c.mask(box(x0 + 4, top - 4, x1 - 4, top + 2)), EARTH)
        edge_line(c, x0, x1, top, (90, 60, 50), 3)
        rim(c, bed)
    # Pumpkins in the first bed, scowling, glowing.
    b = Batch(c)
    (p0, p1, ptop), (c0, c1, ctop), (m0, m1, mtop) = BEDS
    for x, r in ((p0 + 34, 13), (p0 + 84, 16), (p0 + 134, 12), (p0 + 172, 10)):
        pumpkin(b, x, ptop - 2, r)
    b.draw()
    c.light(c.mask(lambda p: [p.ellipse(x, ptop - 16, 30) for x in (p0 + 34, p0 + 84, p0 + 134)], blur=12), GLOW, 0.25)
    c.put(c.mask(lambda p: p.line([(p0 + 10, ptop - 4), (p0 + 60, ptop - 10), (p0 + 110, ptop - 4), (p0 + 190, ptop - 8)], 1.6)), LEAF)
    # Cabbages with teeth in the second.
    for x in range(c0 + 26, c1 - 10, 44):
        head = c.mask(lambda p: p.ellipse(x, ctop - 14, 16, 13))
        c.put(head, CABBAGE)
        c.put(head * c.mask(lambda p: [p.line([(x + d, ctop - 2), (x + d * 0.4, ctop - 26)], 1) for d in (-10, -4, 4, 10)]), scale(CABBAGE, 0.7))
        c.put(c.mask(lambda p: p.poly([(x - 10, ctop - 12), (x + 10, ctop - 12), (x + 8, ctop - 6), (x - 8, ctop - 6)])), (20, 8, 16))
        c.put(c.mask(lambda p: [p.poly([(x + d - 2, ctop - 12), (x + d + 2, ctop - 12), (x + d, ctop - 8)]) for d in (-7, -2, 3, 8)]), (236, 228, 210))
        c.put(c.mask(lambda p: [p.ellipse(x + d, ctop - 20, 1.6) for d in (-5, 5)]), (255, 210, 80))
    # Mandrakes in the third: only their leaves show. Do not pull.
    for x in range(m0 + 20, m1 - 10, 30):
        c.put(c.mask(lambda p: [p.poly([(x, mtop - 2), (x + dx, mtop - 22 - abs(dx)), (x + dx * 0.5 + 3, mtop - 2)]) for dx in (-10, -3, 5, 11)]), LEAF_LIGHT)
    # The trellis of nightshade.
    tx0, tx1 = 1760, 1830
    c.put(c.mask(lambda p: ([p.rect(x, g - 200, x + 4, g) for x in (tx0, tx1)], [p.line([(tx0, y), (tx1, y + 40)], 1.4) for y in range(g - 200, g - 40, 40)], [p.line([(tx1, y), (tx0, y + 40)], 1.4) for y in range(g - 200, g - 40, 40)])), TIMBER)
    c.put(c.mask(lambda p: [p.ellipse(rng.uniform(tx0 - 6, tx1 + 6), rng.uniform(g - 200, g - 10), 6, 4) for _ in range(40)]), LEAF)
    c.put(c.mask(lambda p: [p.ellipse(rng.uniform(tx0, tx1), rng.uniform(g - 190, g - 20), 2.6) for _ in range(24)]), (40, 20, 70))
    # The compost heap, steaming, a fork in it.
    heap = c.mask(lambda p: p.ellipse(1205, g, 34, 26))
    c.put(heap * (c.y <= g), EARTH)
    c.put(heap * (c.y <= g) * np.clip((c.noise("compost", 6, 6, 2) - 0.5) * 3, 0, 1), LEAF)
    c.put(c.mask(lambda p: (p.line([(1214, g - 20), (1236, g - 64)], 2.2), [p.line([(1210 + d, g - 18), (1212 + d, g - 4)], 1) for d in (-2, 2, 6)])), (110, 100, 96))
    for i in range(4):
        c.put(c.mask(lambda p: p.ellipse(1195 + i * 6, g - 34 - i * 16, 8 + i * 3, 5 + i * 2), blur=4), (150, 120, 130), 0.3)
    # The scarecrow in the castle's helmet, arms out.
    sx = 1900
    c.put(c.mask(lambda p: (p.rect(sx - 2, g - 110, sx + 2, g), p.rect(sx - 34, g - 92, sx + 34, g - 88))), TIMBER)
    coat = c.mask(lambda p: p.poly([(sx - 26, g - 92), (sx + 26, g - 92), (sx + 18, g - 44), (sx - 18, g - 44)]))
    c.put(coat, (60, 50, 40))
    rim(c, coat)
    c.put(c.mask(lambda p: [p.line([(sx + s * 30, g - 90), (sx + s * 36, g - 80 + dy)], 1) for s in (-1, 1) for dy in (0, 4, 8)]), (200, 170, 100))
    c.put(c.mask(lambda p: p.ellipse(sx, g - 104, 10, 11)), (200, 170, 100))
    helm = c.mask(lambda p: (p.ellipse(sx, g - 110, 13, 10), p.rect(sx - 15, g - 108, sx + 15, g - 104)))
    c.put(helm * (c.y < g - 103), (70, 70, 76))
    c.put(c.mask(lambda p: p.rect(sx - 9, g - 108, sx + 9, g - 106)), NEAR_BLACK)
    # The show bench between the beds: the prize marrow, its rosette.
    c.put(c.mask(lambda p: (p.rect(1450, g - 36, 1510, g - 32), p.rect(1454, g - 32, 1458, g), p.rect(1502, g - 32, 1506, g))), TIMBER)
    c.put(c.mask(lambda p: p.ellipse(1480, g - 46, 24, 9)), (70, 110, 50))
    c.put(c.mask(lambda p: [p.line([(1464 + i * 8, g - 52), (1468 + i * 8, g - 40)], 1) for i in range(4)]), (110, 150, 70))
    c.put(c.mask(lambda p: (p.ellipse(1488, g - 60, 6), p.poly([(1485, g - 56), (1482, g - 44), (1487, g - 48)]), p.poly([(1491, g - 56), (1494, g - 44), (1489, g - 48)]))), (180, 30, 40))
    c.put(c.mask(lambda p: p.ellipse(1488, g - 60, 2.4)), (240, 200, 90))

PIECES: Dict[str, Piece] = {
    "allotment_west": Piece((40, 480, 920, FLOOR), west),
    "allotment_beds": Piece((940, 420, 1960, FLOOR), beds),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
