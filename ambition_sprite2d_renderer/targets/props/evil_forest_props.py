"""The road through the Evil dimension's forest (`evil_gate_forest`), from its
gate to Castle Godwin: what the road passes.

Drawn in the room's coordinates (`_district_props`): the road is the floor
(y 656), the gate at its west end (x 64..428), the castle's front at its east
(x 1408). Under the forest's blood-red sky (`backgrounds/evil.py`) everything
here is near-black with a red rim on the side the sky lights.

- `evil_forest_roadside`: a graveyard behind a broken iron fence, its
  headstones leaning and one mausoleum with its door ajar (between the first
  thorns and the second); a dead oak with crows on it and a ring of chain
  (between the road sign and the third thorns); a coach's broken wheel by
  the castle's wall; low fog along the road. It is added after the room's
  other props, so it draws over them: it keeps out of their places.

Animations: ``idle``, 1 frame. No drop shadows.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale

PAL = {
    "stone": (60, 52, 56), "stone_light": (120, 90, 90), "trim": (90, 70, 72), "dark": (10, 6, 8),
    "glass_top": (120, 40, 40), "glass_low": (40, 10, 12), "lamp": (255, 110, 60), "wood": (40, 28, 26),
    "leaf": (30, 24, 26), "iron": (20, 16, 18), "brass": (150, 110, 60), "glaze": (150, 60, 40),
}
FLOOR = 656
NEAR_BLACK = (22, 16, 20)
STONE = (58, 52, 58)
RIM = (230, 70, 50)
FOG = (150, 120, 130)
X0, X1, TOP = 430, 1400, 260


def rim(c, m, strength=0.5):
    """Light from the red sky on the left edge of `m`."""
    edge = np.clip(m - np.roll(m, 6, axis=1), 0, 1)
    c.light(edge, RIM, strength)


def headstone(c, x, lean, h, kind, tag):
    w = h * 0.62
    ca, sa = math.cos(lean), math.sin(lean)
    def rot(px, py):
        return (x + px * ca - py * sa, FLOOR + px * sa + py * ca)
    if kind == "round":
        pts = [rot(-w / 2, 0), rot(w / 2, 0), rot(w / 2, -h + w / 2)] + [rot(w / 2 * math.cos(t), -h + w / 2 - w / 2 * math.sin(t)) for t in np.linspace(0, math.pi, 12)] + [rot(-w / 2, -h + w / 2)]
    elif kind == "cross":
        pts = [rot(-4, 0), rot(4, 0), rot(4, -h * 0.66), rot(14, -h * 0.66), rot(14, -h * 0.8), rot(4, -h * 0.8), rot(4, -h), rot(-4, -h), rot(-4, -h * 0.8), rot(-14, -h * 0.8), rot(-14, -h * 0.66), rot(-4, -h * 0.66)]
    else:
        pts = [rot(-w / 2, 0), rot(w / 2, 0), rot(w / 2 - 3, -h), rot(-w / 2 + 3, -h)]
    m = c.mask(lambda p: p.poly(pts))
    c.put(m, STONE)
    c.tone(m * (c.noise(("stone", tag), 6, 6, 2) - 0.5), 0.3)
    rim(c, m, 0.45)


def roadside(c, k):
    g = FLOOR
    # The graveyard fence: iron pales, some fallen.
    rng = c.rand("fence")
    pales = []
    for x in np.arange(534, 900, 11):
        if rng.random() < 0.15:
            continue
        lean = rng.uniform(-0.12, 0.12) if rng.random() < 0.3 else 0.0
        top = g - rng.uniform(40, 46)
        pales.append([(x, g), (x + (g - top) * math.sin(lean), top)])
    c.put(c.mask(lambda p: ([p.line(pl, 1.8) for pl in pales], [p.poly([(b[0] - 3, b[1] + 3), (b[0] + 3, b[1] + 3), (b[0], b[1] - 5)]) for _, b in pales], p.line([(534, g - 34), (900, g - 30)], 1.6), p.line([(534, g - 12), (900, g - 12)], 1.6))), NEAR_BLACK)
    # Headstones and a mausoleum behind it.
    for i, (x, lean, h, kind) in enumerate(((564, -0.12, 38, "round"), (606, 0.08, 50, "cross"), (650, 0.18, 34, "flat"), (790, -0.05, 44, "round"),
                                              (836, 0.22, 30, "flat"), (876, -0.15, 56, "cross"))):
        headstone(c, x, lean, h, kind, i)
    mx = 720
    maus = c.mask(lambda p: (p.rect(mx - 38, g - 92, mx + 38, g), p.poly([(mx - 46, g - 92), (mx + 46, g - 92), (mx, g - 128)])))
    c.put(maus, STONE)
    c.tone(maus * (c.noise("maus", 8, 8, 2) - 0.5), 0.3)
    rim(c, maus, 0.5)
    c.put(c.mask(lambda p: p.arch(mx - 16, g - 70, mx + 16, g)), (6, 4, 6))
    c.put(c.mask(lambda p: p.poly([(mx + 2, g - 54), (mx + 16, g - 60), (mx + 16, g), (mx + 2, g)])), (40, 34, 36))
    c.light(c.mask(lambda p: p.ellipse(mx - 6, g - 30, 6, 20), blur=6), (120, 255, 140), 0.35)
    # The dead oak, its crows, a chain hanging from its bough.
    tx = 1145
    trunk = c.mask(lambda p: p.poly([(tx - 18, g), (tx + 22, g), (tx + 10, g - 160), (tx + 4, g - 230), (tx - 6, g - 230), (tx - 10, g - 160)]))
    boughs = [[(tx, g - 200), (tx - 70, g - 250), (tx - 140, g - 262), (tx - 180, g - 300)],
              [(tx + 4, g - 180), (tx + 80, g - 240), (tx + 150, g - 250)],
              [(tx, g - 226), (tx + 20, g - 300), (tx + 50, g - 340)],
              [(tx - 100, g - 255), (tx - 110, g - 300)],
              [(tx + 90, g - 240), (tx + 110, g - 290)]]
    branches = c.mask(lambda p: [p.line(b, 9 - 2 * i if i < 3 else 4) for i, b in enumerate(boughs)])
    tree = np.maximum(trunk, branches)
    c.put(tree, NEAR_BLACK)
    rim(c, tree, 0.6)
    c.put(c.mask(lambda p: p.line([(tx + 120, g - 246), (tx + 122, g - 170)], 1.4)), (60, 56, 60))
    c.put(c.mask(lambda p: p.ring(tx + 122, g - 160, 9, 1.6)), (60, 56, 60))
    for bx, by, f in ((tx - 140, g - 270, 1), (tx - 60, g - 258, -1), (tx + 60, g - 238, 1), (tx + 140, g - 258, -1), (tx + 44, g - 336, 1)):
        c.put(c.mask(lambda p: (p.ellipse(bx, by - 7, 7, 6), p.ellipse(bx + 6 * f, by - 13, 4), p.poly([(bx + 9 * f, by - 14), (bx + 15 * f, by - 12), (bx + 9 * f, by - 11)]), p.poly([(bx - 6 * f, by - 6), (bx - 15 * f, by - 2), (bx - 6 * f, by - 2)]))), (8, 6, 8))
        c.put(c.mask(lambda p: p.ellipse(bx + 7 * f, by - 14, 1.0)), RIM)
    # A coach's wheel, broken, leaning on the castle's wall; its lantern.
    wx, wy, r = 1316, g - 22, 22
    c.put(c.mask(lambda p: (p.ring(wx, wy, r, 3.4), [p.line([(wx, wy), (wx + r * math.cos(a), wy + r * math.sin(a))], 1.6) for a in np.linspace(0.3, math.tau - 0.6, 7)], p.ellipse(wx, wy, 4))), (36, 24, 24))
    c.put(c.mask(lambda p: p.poly([(1340, g), (1352, g - 4), (1354, g - 16), (1342, g - 12)])), (60, 40, 30))
    c.light(c.mask(lambda p: p.ellipse(1347, g - 8, 6), blur=3), RIM, 0.6)
    # Low fog along the road.
    rng = c.rand("fog")
    for _ in range(18):
        fx, fw = rng.uniform(X0, X1), rng.uniform(60, 160)
        c.put(c.mask(lambda p: p.ellipse(fx, g - rng.uniform(4, 14), fw, rng.uniform(10, 18)), blur=10), FOG, 0.12)


PIECES: Dict[str, Piece] = {
    "evil_forest_roadside": Piece((X0, TOP, X1, FLOOR), roadside),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
