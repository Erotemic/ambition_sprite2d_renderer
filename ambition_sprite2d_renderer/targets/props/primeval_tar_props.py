"""The Tar Pits (`primeval_tar_pits`, the jungle dimension): out past the end
of the primeval trail, east of the canopy.

Drawn in room coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/primeval/tar_pits.py`: the ground (y 576),
the two pools (x 520..900 and 1300..1700, the tar from y 576 to their beds
at 624; the room's water is the murky kind, and has no picture of its own),
the mammoth's back (x 600..840, y 480), the dig camp's scaffold (y 480 and
384).

- `tar_pits_pools`: the tar, black and glossy, a bubble rising, a tusk and a
  claw going under, wisps of steam.
- `tar_pits_mammoth`: a mammoth's skeleton half sunk in the first pool, its
  spine walked on, its tusks curling out of the tar.
- `tar_pits_dig_camp`: the paleontologists' camp: a canvas tent, the
  scaffold of planks, a sieve on trestles, buckets, a wheelbarrow of bones,
  a survey grid of string pegged over the ground.
- `tar_pits_bones`: a sabre-tooth's skull and scattered bones by the way in.

Animations: ``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .eureka_props import edge_line
from .primeval_props import BONE, LEAF, MOSS, PAL, fern

FLOOR, BED = 576, 624
POOLS = ((520, 900), (1300, 1700))
MAMMOTH_BACK = (600, 840, 480)
SCAFFOLD = ((1980, 2140, 480), (2040, 2200, 384))
TAR = (16, 14, 14)
TAR_SHINE = (120, 116, 130)
CANVAS = (214, 196, 150)
WOOD = (130, 96, 60)
WOOD_DARK = (84, 60, 38)
STRING = (230, 80, 60)
BONE_DARK = (176, 160, 124)


def pools(c, k):
    rng = c.rand("tar")
    for x0, x1 in POOLS:
        tar = c.mask(lambda p: p.poly([(x0, FLOOR - 2), (x1, FLOOR - 2), (x1, BED), (x0, BED)]))
        c.put(tar, TAR)
        # The gloss: long soft highlights on the surface, a ring of a bubble.
        c.put(c.mask(lambda p: [p.ellipse(rng.uniform(x0 + 40, x1 - 40), FLOOR + 1, rng.uniform(20, 60), 1.4) for _ in range(6)], blur=1), TAR_SHINE, 0.6)
        bx = rng.uniform(x0 + 60, x1 - 60)
        c.put(c.mask(lambda p: p.ellipse(bx, FLOOR - 6, 9, 8)), TAR)
        c.put(c.mask(lambda p: p.ring(bx, FLOOR - 6, 9, 1.2)), TAR_SHINE, 0.8)
        c.put(c.mask(lambda p: p.ellipse(bx - 3, FLOOR - 9, 2.4, 1.6)), (220, 220, 230))
        # Steam.
        for _ in range(3):
            sx = rng.uniform(x0 + 30, x1 - 30)
            pts = [(sx + 8 * math.sin(t * 1.7 + sx), FLOOR - 8 - t * 18) for t in np.linspace(0, 4, 20)]
            c.put(c.mask(lambda p: p.line(pts, 6), blur=6), (200, 196, 190), 0.25)
        # The banks: the earth stained black where the tar laps.
        c.put(c.mask(lambda p: (p.ellipse(x0, FLOOR + 2, 26, 6), p.ellipse(x1, FLOOR + 2, 26, 6))), (40, 34, 30), 0.8)
    # In the second pool: a claw going under, a tusk of something else.
    c.put(c.mask(lambda p: [p.line([(1460 + i * 9, FLOOR), (1452 + i * 12, FLOOR - 26 - i * 3), (1440 + i * 15, FLOOR - 34 - i * 2)], 3.2) for i in range(3)]), BONE_DARK)
    tusk = [(1600 + 30 * math.cos(t), FLOOR - 4 - 42 * math.sin(t)) for t in np.linspace(0.1, 2.2, 20)]
    c.put(c.mask(lambda p: p.line(tusk, 6)), BONE)


def tapered(c, pts, w0, w1, colour, under=None):
    """A bone or tusk along `pts`, `w0` wide at its root and `w1` at its tip;
    none of it under `under` (the ground it goes into)."""
    n = len(pts) - 1
    m = c.mask(lambda p: [p.line([pts[i], pts[i + 1]], w0 + (w1 - w0) * i / n) for i in range(n)])
    c.put(m if under is None else m * (c.y < under), colour)


def mammoth(c, k):
    x0, x1, back = MAMMOTH_BACK
    # The spine along the walk line: a row of rounded vertebrae, each with
    # its short process, flat on top where it is walked.
    c.put(c.mask(box(x0, back + 2, x1, back + 12)), BONE_DARK)
    c.put(c.mask(lambda p: [p.ellipse(x, back + 6, 8, 6) for x in range(x0 + 8, x1, 16)]), BONE)
    c.put(c.mask(lambda p: [p.rect(x - 2, back, x + 2, back + 4) for x in range(x0 + 8, x1, 16)]), BONE)
    edge_line(c, x0 + 4, x1 - 4, back, BONE, 3)
    # The ribs: curved, each out from the spine and down into the tar,
    # longest over the chest (the west), the far side's behind and darker.
    for far in (True, False):
        ribs = []
        for i, x in enumerate(np.linspace(x0 + 30, x1 - 70, 10)):
            depth = FLOOR + 6 - back
            bow = 26 - i * 1.6
            ribs.append([(x + (6 if far else 0) - bow * math.sin(t * math.pi * 0.8), back + 10 + depth * t) for t in np.linspace(0, 1, 9)])
        for r in ribs:
            tapered(c, r, 5.0 if not far else 3.6, 2.6, BONE_DARK if far else BONE)
    # The legs' long bones going down into the tar, a knob at each joint.
    for lx, top in ((x0 + 24, back + 10), (x1 - 34, back + 10)):
        c.put(c.mask(lambda p: p.line([(lx, top), (lx - 10, FLOOR + 6)], 10)), BONE_DARK)
        c.put(c.mask(lambda p: p.ellipse(lx - 5, (top + FLOOR) / 2 + 6, 8, 7)), BONE_DARK)
    # The skull at the west end, bowed: a high domed crown, a deep socket
    # for the eye, the heavy sheath of the tusks down into the tar.
    skull = c.mask(lambda p: (p.ellipse(562, 474, 40, 44),
                              p.poly([(530, 448), (600, 470), (604, 512), (560, 548), (512, 572), (494, 552), (506, 500)])))
    c.put(skull, BONE)
    c.tone(skull * np.clip((c.y - 440) / 130, 0, 1), -0.22)
    c.tone(skull * np.clip((c.x - 540) / 60, 0, 1) * np.clip((500 - c.y) / 50, 0, 1), 0.12)
    c.put(c.mask(lambda p: p.ellipse(548, 492, 11, 9)), (52, 44, 34))
    c.put(c.mask(lambda p: p.ellipse(520, 526, 2.6, 6)), (96, 84, 64))
    # The tusks, out of their sheath, curving forward and up: a spiral.
    for far, (cx, cy) in ((True, (470, 512)), (False, (458, 520))):
        pts = []
        for t in np.linspace(0, 1, 28):
            a = math.radians(40 + 215 * t)
            r = 62 - 18 * t
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        tapered(c, pts, 10 if not far else 8, 3, BONE_DARK if far else BONE, under=FLOOR)
    c.tone(c.mask(lambda p: p.rect(POOLS[0][0], FLOOR - 8, x1, FLOOR + 6)), -0.3)


def dig_camp(c, k):
    g = FLOOR
    # The tent: canvas on a ridge pole, its flap tied back.
    tx0, tx1 = 1880, 2000
    c.put(c.mask(lambda p: p.poly([(tx0, g), ((tx0 + tx1) / 2, g - 100), (tx1, g)])), CANVAS)
    c.put(c.mask(lambda p: p.poly([((tx0 + tx1) / 2, g - 100), ((tx0 + tx1) / 2 + 20, g), ((tx0 + tx1) / 2 - 6, g)])), (60, 50, 40))
    c.put(c.mask(lambda p: (p.line([((tx0 + tx1) / 2, g - 100), (tx0 - 20, g)], 1.0), p.line([((tx0 + tx1) / 2, g - 100), (tx1 + 20, g)], 1.0))), (200, 190, 160))
    c.tone(c.mask(lambda p: p.poly([(tx0, g), ((tx0 + tx1) / 2, g - 100), ((tx0 + tx1) / 2, g)])), 0.12)
    # The scaffold: planks on poles, lashed.
    for x0, x1, y in SCAFFOLD:
        c.put(c.mask(box(x0, y, x1, y + 10)), WOOD)
        edge_line(c, x0, x1, y, WOOD, 4)
        for px in (x0 + 8, x1 - 12):
            c.put(c.mask(box(px, y + 10, px + 6, g)), WOOD_DARK)
            c.put(c.mask(lambda p: p.line([(px - 2, y + 18), (px + 8, y + 24)], 1.6)), (200, 180, 120))
    c.put(c.mask(lambda p: (p.line([(1990, g), (2130, 490)], 3), p.line([(2130, g), (1990, 490)], 3))), WOOD_DARK)
    # The sieve on trestles, buckets, the wheelbarrow of bones.
    c.put(c.mask(lambda p: (p.rect(2220, g - 46, 2330, g - 40), p.line([(2226, g), (2240, g - 44)], 3), p.line([(2324, g), (2310, g - 44)], 3))), WOOD_DARK)
    c.put(c.mask(lambda p: [p.rect(x, g - 52, x + 1, g - 46) for x in range(2224, 2330, 6)]), (140, 140, 150))
    for bx in (2250, 2280):
        c.put(c.mask(lambda p: p.poly([(bx - 9, g), (bx + 9, g), (bx + 11, g - 22), (bx - 11, g - 22)])), (110, 120, 140))
    c.put(c.mask(lambda p: (p.poly([(2050, g - 20), (2120, g - 20), (2110, g - 44), (2060, g - 44)]), p.line([(2120, g - 30), (2160, g - 14)], 3))), (90, 100, 90))
    c.put(c.mask(lambda p: p.ellipse(2064, g - 10, 10)), (30, 30, 30))
    c.put(c.mask(lambda p: [p.line([(2066 + i * 9, g - 44), (2072 + i * 8, g - 58 + i * 2)], 3) for i in range(5)]), BONE)
    # The survey grid: string pegged in squares over the ground west of camp.
    gx0, gx1 = 1740, 1860
    c.put(c.mask(lambda p: [p.rect(x - 1, g - 8, x + 1, g) for x in range(gx0, gx1 + 1, 40)]), WOOD)
    c.put(c.mask(lambda p: p.rect(gx0, g - 6, gx1, g - 5)), STRING)


def scattered_bones(c, k):
    g = FLOOR
    # A sabre-tooth's skull, its fangs down.
    sx = 260
    skull = c.mask(lambda p: p.poly([(sx, g), (sx + 6, g - 26), (sx + 30, g - 38), (sx + 64, g - 30), (sx + 76, g - 12), (sx + 70, g)]))
    c.put(skull, BONE)
    c.put(c.mask(lambda p: p.ellipse(sx + 46, g - 24, 6, 5)), (60, 52, 40))
    c.put(c.mask(lambda p: [p.poly([(sx + x, g - 8), (sx + x + 6, g - 8), (sx + x + 2, g + 16)]) for x in (56, 64)]) * (c.y < g + 2), BONE)
    c.tone(skull * np.clip((c.y - (g - 38)) / 38, 0, 1), -0.2)
    rng = c.rand("scatter")
    c.put(c.mask(lambda p: [p.line([(x, g - 3), (x + rng.uniform(16, 30), g - rng.uniform(2, 8))], 4) for x in (180, 360, 420)]), BONE_DARK)
    fern(c, 470, g, 50, "tar_fern")
    fern(c, 160, g, 40, "tar_fern2")


PIECES: Dict[str, Piece] = {
    "tar_pits_pools": Piece((500, 440, 1720, 640), pools),
    "tar_pits_mammoth": Piece((380, 410, 860, 600), mammoth),
    "tar_pits_dig_camp": Piece((1730, 360, 2380, FLOOR + 4), dig_camp),
    "tar_pits_bones": Piece((120, 500, 520, 600), scattered_bones),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
