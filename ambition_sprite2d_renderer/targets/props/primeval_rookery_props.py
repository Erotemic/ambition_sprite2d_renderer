"""The birdwatcher's hide in the rookery (`primeval_rookery`, the jungle
dimension), on the raised ground (x 1472..1680, y 416) between the second
nest and the second palm.

Drawn in room coordinates (`_district_props`) on the level's own numbers
(edited in place: `tools/ambition_ldtk_tools/specs/scenery_overlay.py`).

- `rookery_hide`: a hide of poles and green canvas, palm fronds over it, a
  viewing slit with a long lens poking out; by it a camp stool, a thermos,
  the field notebook open on the tally (penguins: far too many).

Animations: ``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .primeval_props import LEAF, LEAF_LIGHT, PAL

#: The raised ground the hide stands on (x 1472..1680).
G = 416
CANVAS = (96, 110, 70)
CANVAS_DARK = (64, 76, 48)
POLE = (110, 82, 52)


def hide(c, k):
    rng = c.rand("hide")
    x0, x1 = 1490, 1610
    # The canvas over its poles: a box with a sagging roof.
    body = c.mask(lambda p: p.poly([(x0, G), (x0, G - 84), (x0 + 30, G - 90), (x1 - 30, G - 88), (x1, G - 84), (x1, G)]))
    c.put(body, CANVAS)
    c.tone(body * (c.noise("hide_canvas", 10, 6, 2) - 0.5), 0.2)
    c.put(body * c.mask(lambda p: [p.rect(x, G - 92, x + 1.2, G) for x in (x0 + 40, x1 - 40)]), CANVAS_DARK)
    c.put(c.mask(lambda p: [p.rect(x - 2, G - 96, x + 2, G) for x in (x0, x1)]), POLE)
    # Palm fronds over the roof.
    for i in range(7):
        fx = x0 - 6 + i * 22
        pts = [(fx, G - 90), (fx + 18, G - 100 - rng.uniform(0, 6)), (fx + 38, G - 86)]
        c.put(c.mask(lambda p: p.line(pts, 6)), LEAF if i % 2 else LEAF_LIGHT)
        c.put(c.mask(lambda p: [p.line([(fx + t * 38, G - 90 - 10 * (1 - abs(t - 0.5) * 2)), (fx + t * 38 + 4, G - 78)], 1.2) for t in np.linspace(0.1, 0.9, 6)]), LEAF)
    # The viewing slit, and the long lens through it.
    c.put(c.mask(box(x0 + 20, G - 62, x1 - 20, G - 52)), (24, 26, 20))
    c.put(c.mask(lambda p: (p.rect(x0 + 10, G - 60, x0 + 46, G - 54), p.rect(x0 + 2, G - 61, x0 + 12, G - 53))), (40, 40, 44))
    c.put(c.mask(lambda p: p.ellipse(x0 + 3, G - 57, 1.6, 3.4)), (150, 200, 230))
    # The camp stool, a thermos, the notebook open on the tally.
    sx = 1640
    c.put(c.mask(lambda p: (p.line([(sx - 10, G), (sx + 10, G - 22)], 2), p.line([(sx + 10, G), (sx - 10, G - 22)], 2))), POLE)
    c.put(c.mask(box(sx - 12, G - 24, sx + 12, G - 20)), (150, 60, 50))
    c.put(c.mask(lambda p: (p.rect(sx - 6, G - 34, sx + 8, G - 24), p.line([(sx - 6, G - 34), (sx + 1, G - 31), (sx + 8, G - 34)], 0.8))), (236, 230, 210))
    c.put(c.mask(lambda p: [p.rect(sx - 4 + i * 2.4, G - 32, sx - 3.4 + i * 2.4, G - 27) for i in range(5)]), (30, 30, 30))
    c.put(c.mask(box(1662, G - 22, 1670, G)), (60, 100, 140))
    c.put(c.mask(box(1661, G - 25, 1671, G - 21)), (40, 40, 44))


PIECES: Dict[str, Piece] = {
    "rookery_hide": Piece((1470, G - 110, 1690, G), hide),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
