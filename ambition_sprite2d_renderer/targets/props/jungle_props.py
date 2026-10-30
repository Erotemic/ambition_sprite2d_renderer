"""Things along the primeval trail (the jungle dimension): small pieces, each
standing on the ground at the foot of its frame, placed in the trail's rooms
by `tools/ambition_ldtk_tools/specs/scenery_overlay.py`.

- `jungle_fern_clump`: giant ferns.
- `jungle_fallen_log`: a mossy fallen trunk with a shelf fungus.
- `jungle_nest`: a nest of speckled eggs in a ring of twigs (one egg hatching).
- `jungle_idol_head`: a toppled stone head, mossed, a fern growing out of it.
- `jungle_ribcage`: the bones of something very big, half sunk.
- `jungle_ranger_hut`: the trail ranger's hut by the gate.

Animations: ``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .primeval_props import BONE, LEAF, LEAF_LIGHT, MOSS, PAL, TEMPLE_LIGHT, blocks, fern


def fern_clump(c, k):
    for x, s in ((60, 70), (110, 90), (160, 64)):
        fern(c, x, 120, s, ("clump", x))


def fallen_log(c, k):
    g = 60
    log = c.mask(lambda p: (p.rect(20, g - 34, 240, g), p.ellipse(240, g - 17, 10, 17)))
    c.put(log, (96, 66, 44))
    c.put(c.mask(lambda p: [p.rect(20, y, 240, y + 1.2) for y in (g - 28, g - 18, g - 8)]), (70, 48, 32), 0.8)
    c.put(c.mask(lambda p: p.ellipse(240, g - 17, 8, 14)), (150, 116, 80))
    c.put(c.mask(lambda p: [p.ring(240, g - 17, r, 0.7) for r in (4, 8, 11)]), (110, 80, 54), 0.8)
    moss = np.clip((c.noise("log_moss", 12, 3, 2) - 0.45) * 4, 0, 1) * c.mask(box(20, g - 36, 230, g - 24))
    c.put(moss, MOSS)
    c.put(c.mask(lambda p: [p.ellipse(x, g - 30, 12, 4) for x in (90, 104)]), (220, 170, 90))
    fern(c, 30, g, 40, "log_fern")


def nest(c, k):
    g = 70
    c.put(c.mask(lambda p: p.ellipse(90, g - 10, 80, 20)), (110, 84, 50))
    rng = c.rand("twigs")
    c.put(c.mask(lambda p: [p.line([(rng.uniform(14, 166), g - rng.uniform(2, 26)), (rng.uniform(14, 166), g - rng.uniform(2, 26))], 1.6) for _ in range(60)]), (80, 58, 34))
    for i, (x, y, tilt) in enumerate(((60, g - 34, -0.2), (90, g - 38, 0.0), (120, g - 33, 0.25))):
        egg = c.mask(lambda p: p.ellipse(x, y, 13, 18))
        c.put(egg, (232, 222, 196))
        c.put(c.mask(lambda p: [p.ellipse(x + rng.uniform(-8, 8), y + rng.uniform(-12, 12), 1.6) for _ in range(9)]) * egg, (130, 110, 80))
        c.tone(egg * np.clip((c.x - x) / 13, -1, 1), -0.2)
    # The middle one is hatching: a crack, and an eye in it.
    c.put(c.mask(lambda p: p.line([(80, g - 44), (86, g - 38), (92, g - 44), (98, g - 38)], 1.2)), (60, 50, 40))
    c.put(c.mask(lambda p: p.ellipse(90, g - 42, 2.4)), (20, 20, 20))
    c.put(c.mask(lambda p: p.ellipse(90.8, g - 42.8, 0.8)), (255, 255, 255))


def idol_head(c, k):
    g = 110
    head = c.mask(lambda p: p.poly([(20, g), (30, g - 80), (70, g - 100), (130, g - 92), (150, g - 40), (140, g)]))
    blocks(c, head, TEMPLE_LIGHT, 18, 26, "idol")
    c.put(c.mask(lambda p: (p.rect(56, g - 66, 80, g - 56), p.rect(100, g - 64, 124, g - 54))), (40, 44, 36))
    c.put(c.mask(lambda p: p.poly([(84, g - 54), (96, g - 54), (100, g - 32), (80, g - 32)])), scale(TEMPLE_LIGHT, 0.8))
    c.put(c.mask(lambda p: p.rect(64, g - 22, 116, g - 14)), (40, 44, 36))
    fern(c, 120, g - 88, 34, "idol_fern")


def ribcage(c, k):
    g = 120
    spine = [(20, g - 20), (90, g - 34), (170, g - 38), (240, g - 26), (290, g - 10)]
    c.put(c.mask(lambda p: p.line(spine, 6)), BONE)
    # Each rib an arch from the spine up and over, down into the earth.
    for i, x in enumerate(np.linspace(60, 240, 7)):
        h = 60 + 30 * math.sin(i / 6 * math.pi)
        rib = [(x + 26 * (1 - math.cos(t)) - 8, g - 34 - h * math.sin(t)) for t in np.linspace(0, math.pi * 0.95, 14)]
        rib[-1] = (rib[-1][0], g - 4)
        c.put(c.mask(lambda p: p.line(rib, 4.5 - i * 0.2)), BONE)
    skull = c.mask(lambda p: p.poly([(270, g - 30), (310, g - 44), (318, g - 24), (300, g - 8), (276, g - 10)]))
    c.put(skull, BONE)
    c.put(c.mask(lambda p: p.ellipse(298, g - 30, 4)), (40, 36, 30))
    # Half sunk: earth and moss over its feet.
    c.put(c.mask(lambda p: p.ellipse(160, g, 170, 12)) * (c.y < g), (70, 90, 50))


def ranger_hut(c, k):
    """The trail ranger's hut by the gate: timber on stilts, a thatch of palm,
    the trail's map on a board (a dotted way past a skull to a crown), a
    bell, a first-aid box, a basket of coconuts."""
    g = 150
    wood, wood_dark, thatch = (128, 92, 58), (82, 58, 38), (176, 150, 84)
    c.put(c.mask(lambda p: [p.rect(x, g - 40, x + 6, g) for x in (20, 190)]), wood_dark)
    c.put(c.mask(box(10, g - 46, 210, g - 38)), wood)
    c.put(c.mask(box(30, g - 112, 190, g - 46)), wood)
    c.put(c.mask(lambda p: [p.rect(30, y, 190, y + 0.8) for y in range(int(g - 104), int(g - 46), 8)]), wood_dark)
    c.put(c.mask(box(46, g - 100, 86, g - 46)), (40, 34, 28))
    roof = c.mask(lambda p: p.poly([(0, g - 108), (110, g - 146), (220, g - 108), (210, g - 100), (10, g - 100)]))
    c.put(roof, thatch)
    c.put(roof * c.mask(lambda p: [p.line([(x, g - 146 + abs(x - 110) * 0.34), (x + 4, g - 100)], 1.0) for x in range(6, 216, 7)]), scale(thatch, 0.75))
    # The map: a dotted trail past a skull to a crown.
    c.put(c.mask(box(100, g - 100, 176, g - 56)), (232, 222, 190))
    c.put(c.mask(lambda p: [p.ellipse(106 + i * 6, g - 72 - 10 * math.sin(i / 2), 1.2) for i in range(11)]), (150, 60, 50))
    c.put(c.mask(lambda p: (p.ellipse(132, g - 86, 4), p.poly([(160, g - 88), (166, g - 96), (170, g - 88), (174, g - 96), (176, g - 84), (160, g - 84)]))), (90, 80, 70))
    # The bell, the first-aid box, the coconuts.
    c.put(c.mask(lambda p: (p.rect(196, g - 100, 198, g - 80), p.poly([(190, g - 70), (204, g - 70), (201, g - 82), (193, g - 82)]))), (200, 160, 70))
    c.put(c.mask(box(32, g - 34, 56, g - 46 + 30)), (230, 230, 230))
    c.put(c.mask(lambda p: (p.rect(42, g - 32, 46, g - 20), p.rect(38, g - 28, 50, g - 24))), (200, 50, 50))
    c.put(c.mask(lambda p: p.poly([(150, g), (190, g), (194, g - 22), (146, g - 22)])), (150, 120, 70))
    c.put(c.mask(lambda p: [p.ellipse(x, g - 24, 7) for x in (156, 168, 180)]), (100, 70, 40))


PIECES: Dict[str, Piece] = {
    "jungle_ranger_hut": Piece((0, 0, 220, 150), ranger_hut),
    "jungle_fern_clump": Piece((0, 0, 230, 120), fern_clump),
    "jungle_fallen_log": Piece((0, 0, 260, 60), fallen_log),
    "jungle_nest": Piece((0, 0, 180, 70), nest),
    "jungle_idol_head": Piece((0, 0, 170, 110), idol_head),
    "jungle_ribcage": Piece((0, 0, 320, 120), ribcage),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
