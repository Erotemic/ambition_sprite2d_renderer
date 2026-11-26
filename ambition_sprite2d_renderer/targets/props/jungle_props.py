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
from .pirate_port_props import deck_edge, planks, post, rope_line, sag
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


RUN_SPINE = ((2200, 368), (2224, 368), (2312, 352), (2416, 336),
             (2496, 344), (2560, 368), (2592, 368))


def run_rib_walk(c, k):
    """Draw the exposed spine between the two ledges."""
    ground = 480
    shade = scale(BONE, 0.68)
    for x, top, reach in ((2248, 364, 24), (2290, 356, 34), (2332, 349, 46),
                          (2374, 342, 46), (2416, 336, 49), (2458, 340, 46),
                          (2500, 346, 36), (2542, 361, 29)):
        arc = [(x + reach * (1 - math.cos(t)) * 0.5, top + (ground - top) * math.sin(t * 0.5))
               for t in np.linspace(0, math.pi, 16)]
        c.put(c.mask(lambda p: p.line(arc, 7)), shade)
        c.put(c.mask(lambda p: p.line([(px - 2, py) for px, py in arc], 3)), BONE)
        c.put(c.mask(lambda p: p.ellipse(x + reach, ground - 2, 10, 2)), MOSS)
    underside = [(x, y + 13) for x, y in reversed(RUN_SPINE)]
    bone = c.mask(lambda p: p.poly([*RUN_SPINE, *underside]))
    c.put(bone, shade)
    c.tone(bone * (c.noise("run_spine", 9, 2, 2) - 0.5), 0.3)
    c.put(c.mask(lambda p: p.line(RUN_SPINE, 4)) * bone, BONE)
    for a, b in zip(RUN_SPINE[1:-1], RUN_SPINE[2:]):
        c.put(c.mask(lambda p: p.line([(a[0], a[1] + 8), (b[0], b[1] + 6)], 2)), scale(BONE, 0.8))
    fern(c, 2270, ground, 44, "west_ribs")
    fern(c, 2584, ground, 36, "east_ribs")


TRAILHEAD_FLOOR = 480
SURVEY_WALK = (1040, 1456, 384)
SURVEY_STEPS = ((1024, 1104, 432), (1424, 1536, 432))


def survey_walk(c, k):
    """Draw the ranger's survey walk and its two steps."""
    left, right, top = SURVEY_WALK
    wood = (99, 77, 48)
    for x in (1056, 1170, 1290, 1436):
        post(c, x, top + 8, TRAILHEAD_FLOOR, 8, wood)
        c.put(c.mask(lambda p: p.line([(x, top + 43), (x + 22, top + 12)], 4.5)), wood)
    for x in (1200, 1276, 1352, 1428):
        post(c, x, top - 21, top, 4, wood)
    for x in (1200, 1276, 1352):
        rope_line(c, sag((x, top - 19), (x + 76, top - 19), 5), 2, (154, 123, 78))
    planks(c, k, left, top, right, top + 14, wood, step=10, vertical=True, tag="survey_walk")
    deck_edge(c, left, right, top, (165, 141, 87))
    for left, right, top in SURVEY_STEPS:
        for x in (left + 7, right - 8):
            post(c, x, top + 8, TRAILHEAD_FLOOR, 6, wood)
        planks(c, k, left, top, right, top + 10, wood, step=9, vertical=True, tag=("survey_step", left))
        deck_edge(c, left, right, top, (165, 141, 87))


PIECES: Dict[str, Piece] = {
    "jungle_survey_walk": Piece((1016, 352, 1544, TRAILHEAD_FLOOR), survey_walk),
    "jungle_run_rib_walk": Piece((2192, 320, 2624, 480), run_rib_walk),
    "jungle_ranger_hut": Piece((0, 0, 220, 150), ranger_hut),
    "jungle_fern_clump": Piece((0, 0, 230, 120), fern_clump),
    "jungle_fallen_log": Piece((0, 0, 260, 60), fallen_log),
    "jungle_nest": Piece((0, 0, 180, 70), nest),
    "jungle_idol_head": Piece((0, 0, 170, 110), idol_head),
    "jungle_ribcage": Piece((0, 0, 320, 120), ribcage),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
