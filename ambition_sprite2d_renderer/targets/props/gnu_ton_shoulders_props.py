"""GNU-ton's arena (`gnu_ton_shoulders`, the Science dimension): the space
apple trees his apple rain falls from (Jon, 2026-11-12: "space apple trees
with apples on them").

Each tree grows on a small rock that floats in the upper air of the hall,
moored to the station's ceiling truss by a cable. Its roots hang under the
rock; its apples hang under its crown, where the rain's apples appear (the
rain drops them a little under the rocks' height, `apple_rain.rs`).

Drawn in room coordinates (`_district_props`) on the numbers of
`game/ambition_map_assets/ambition_content/generators/gnu_ton_gravity/make_specs.py`
(`shoulders`): the ceiling (y 0..16), the entry ledge (x 16..464, y 208),
which no tree crowds, and the floor (y 1248), far below.

- `shoulders_apple_tree_west`, `_middle`, `_east`: one tree each.

Animations: ``idle``, 1 frame each. No drop shadows: form shade on a
thing's own faces only.
"""

from __future__ import annotations

import math
from typing import Dict

from ._district_props import Piece, targets
from ._town_kit import mix
from .gnu_ton_orchard_props import apple, canopy, leaf, trunk
from .orbital_station import AMBER, CYAN, HULL, HULL_LIGHT, STEEL, STEEL_DARK, STEEL_LIGHT

CEILING = 16
PAL = {"stone": HULL, "stone_light": HULL_LIGHT, "dark": STEEL_DARK, "lamp": AMBER}

ROCK = (92, 84, 110)
ROCK_DARK = (58, 52, 74)
ROCK_LIGHT = (150, 140, 170)
SOIL = (70, 52, 40)
MOSS = (96, 168, 92)
ROOT = (120, 92, 70)

#: Each tree: its rock's middle (x, y), the rock's half width, and the
#: crown's half width and half height.
TREES = {
    "shoulders_apple_tree_west": (700.0, 330.0, 70.0, 92.0, 58.0),
    "shoulders_apple_tree_middle": (1160.0, 300.0, 78.0, 104.0, 64.0),
    "shoulders_apple_tree_east": (1580.0, 340.0, 66.0, 88.0, 56.0),
}
#: The trunk's height over the rock's soil.
TRUNK = 96.0


def mooring(c, x, y_rock):
    """The cable from the ceiling truss to the rock, with its clamps."""
    c.put(c.mask(lambda p: p.line([(x, CEILING), (x, y_rock)], 2.2)), STEEL_DARK)
    c.put(c.mask(lambda p: p.line([(x - 0.6, CEILING), (x - 0.6, y_rock)], 0.8)), STEEL_LIGHT, 0.6)
    c.put(c.mask(lambda p: p.rect(x - 9, CEILING, x + 9, CEILING + 7)), STEEL)
    c.put(c.mask(lambda p: p.rect(x - 9, CEILING + 5, x + 9, CEILING + 7)), STEEL_DARK)
    c.put(c.mask(lambda p: p.rect(x - 5, y_rock - 9, x + 5, y_rock - 2)), AMBER)
    c.put(c.mask(lambda p: p.ellipse(x, y_rock - 5.5, 1.6, 1.6)), (255, 240, 200))


def rock(c, cx, cy, half, seed):
    """A floating rock, flat on top (where the soil is) and rough under,
    with its roots hanging out of it."""
    rng = c.rand(seed)
    top = cy
    under = [(cx + half * math.cos(a), cy + half * 0.95 * math.sin(a) * rng.uniform(0.75, 1.15))
             for a in [i * math.pi / 9 for i in range(10)]]
    pts = [(cx + half, top)] + [(x, max(top + 4, y)) for x, y in under] + [(cx - half, top)]
    # The roots first, so the rock covers where they leave it.
    for i in range(7):
        x = cx + (i - 3) * half * 0.26 + rng.uniform(-4, 4)
        y0 = top + half * 0.45
        length = rng.uniform(24, 60)
        sway = rng.uniform(-10, 10)
        c.put(c.mask(lambda p: p.line([(x, y0), (x + sway * 0.4, y0 + length * 0.5), (x + sway, y0 + length)], rng.uniform(1.2, 2.4))), ROOT, 0.9)
    c.put(c.mask(lambda p: p.poly(pts)), ROCK)
    # Its far side in shade: the part of its outline right of a line down
    # its middle.
    shade = [(cx + half * 0.1, top + 7)] + [(x, y) for x, y in pts if x > cx + half * 0.1]
    c.put(c.mask(lambda p: p.poly(shade)), ROCK_DARK, 0.55)
    c.put(c.mask(lambda p: p.poly([(cx - half, top), (cx + half, top), (cx + half * 0.9, top + 7), (cx - half * 0.9, top + 7)])), ROCK_LIGHT, 0.7)
    # Its soil and moss, and a crystal or two in its face.
    c.put(c.mask(lambda p: p.poly([(cx - half * 0.92, top + 1), (cx + half * 0.92, top + 1), (cx + half * 0.8, top - 5), (cx - half * 0.8, top - 5)])), SOIL)
    c.put(c.mask(lambda p: [p.ellipse(cx + (i - 4) * half * 0.22, top - 5, half * 0.16, 3.2) for i in range(9)]), MOSS)
    for dx, dy, s in ((-0.45, 0.42, 6.0), (0.3, 0.6, 4.5)):
        x, y = cx + dx * half, top + dy * half
        c.put(c.mask(lambda p: p.poly([(x, y - s * 1.4), (x + s * 0.6, y), (x, y + s * 0.5), (x - s * 0.6, y)])), CYAN, 0.85)
        c.put(c.mask(lambda p: p.poly([(x, y - s * 1.4), (x + s * 0.6, y), (x, y)])), mix(CYAN, (255, 255, 255), 0.5), 0.9)


def apple_tree(name):
    cx, cy, half, crown_rx, crown_ry = TREES[name]

    def draw(c, k):
        rng = c.rand(name, "apples")
        mooring(c, cx + half * 0.35, cy - 4)
        rock(c, cx, cy, half, name)
        trunk(c, cx, cy - 4, cy - TRUNK, 20)
        crown_y = cy - TRUNK - crown_ry * 0.55
        clumps = canopy(c, cx, crown_y, crown_rx, crown_ry, name)
        # The apples hang under the crown, and a few at its edges.
        for x, y, r in clumps:
            if y > crown_y - crown_ry * 0.2:
                apple(c, x + rng.uniform(-8, 8), y + r * 0.55, 6.5, rng.uniform(-0.35, 0.35))
        for i in range(6):
            a = math.pi * (0.15 + 0.7 * i / 5)
            apple(c, cx + math.cos(a) * crown_rx * 0.85, crown_y + math.sin(a) * crown_ry * 0.9, 6.5, rng.uniform(-0.3, 0.3))
        for x, y, a in ((cx - crown_rx * 0.6, cy + 30, 0.7), (cx + crown_rx * 0.4, cy + 52, 2.1)):
            leaf(c, x, y, a)

    return draw


def _frame(name):
    cx, cy, half, crown_rx, crown_ry = TREES[name]
    reach = max(crown_rx * 1.5, half * 1.4) + 12
    return (cx - reach, CEILING, cx + reach, cy + half + 70)


PIECES: Dict[str, Piece] = {name: Piece(_frame(name), apple_tree(name)) for name in TREES}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
