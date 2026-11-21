"""GNU-ton's arena (`gnu_ton_shoulders`, the Science dimension): the space
apple trees his apple rain falls from (Jon, 2026-11-12: "space apple trees
with apples on them").

Each tree grows on an island of earth that floats in the hall, and the
island's top is a real one-way platform of the room (Jon, 2026-11-21: "the
apple trees in the background should be on real floating platforms. I like
the earth and roots coming out of them"). The island is soil over earth over
a tip of rock, its roots hanging out of its underside, and a crystal in its
rock holds it up; a few crumbs of it float under it. The apples the player
can take are not drawn here: they are the room's own apples
(`GroundItem`, `hang_seconds`), which hang under each crown, ripen, fall and
grow again. A few drawn ones stay high in the crown.

Drawn in room coordinates (`_district_props`) on the room's numbers: the
floor at y 1248, the low one-way ledges at y 1120 (x 176..336 and
2480..2640), and the giant's back near y 788. The outer islands step up from
the low ledges (128 over them); the middle one is over the giant's back,
reached by standing on his shoulders.

- `shoulders_apple_tree_west`, `_middle`, `_east`: one island and tree each.

Animations: ``idle``, 1 frame each. No drop shadows: form shade on a
thing's own faces only.
"""

from __future__ import annotations

import math
from typing import Dict

from ._district_props import Piece, targets
from ._town_kit import mix
from .gnu_ton_orchard_props import apple, canopy, leaf, trunk
from .orbital_station import AMBER, CYAN, HULL, HULL_LIGHT, STEEL_DARK

PAL = {"stone": HULL, "stone_light": HULL_LIGHT, "dark": STEEL_DARK, "lamp": AMBER}

ROCK = (92, 84, 110)
ROCK_DARK = (58, 52, 74)
ROCK_LIGHT = (150, 140, 170)
SOIL = (62, 44, 32)
EARTH = (112, 80, 56)
EARTH_DARK = (78, 54, 38)
EARTH_LIGHT = (150, 112, 78)
PEBBLE = (168, 150, 132)
GRASS = (96, 168, 92)
GRASS_LIGHT = (156, 214, 120)
GRASS_DARK = (58, 112, 64)
ROOT = (128, 98, 72)
ROOT_DARK = (84, 62, 46)
ROOT_LIGHT = (176, 142, 108)

#: Each tree: its island's middle x, the y of its top (the one-way row the
#: room places there), its half width (the row's), and its crown's half
#: width and half height. The row's ends are on the 16 px grid.
TREES = {
    "shoulders_apple_tree_west": (464.0, 992.0, 112.0, 92.0, 58.0),
    "shoulders_apple_tree_middle": (1472.0, 656.0, 128.0, 104.0, 64.0),
    "shoulders_apple_tree_east": (2368.0, 992.0, 112.0, 88.0, 56.0),
}
#: The trunk's height over the island's top.
TRUNK = 96.0


def _outline(cx, top, half, rng):
    """The island's outline: flat on top, then a rough taper to a tip of
    rock under its middle, a little off centre."""
    depth = half * 0.95
    tip = cx + rng.uniform(-0.12, 0.12) * half
    pts = [(cx - half, top), (cx + half, top)]
    n = 15
    for i in range(1, n):
        t = i / n
        # Right side down to the tip, then the left side back up.
        if t <= 0.5:
            u = t / 0.5
            x = cx + half - (cx + half - tip) * u
            y = top + depth * (u ** 0.8) * (1.0 - 0.25 * (1 - u))
        else:
            u = (t - 0.5) / 0.5
            x = tip - (tip - (cx - half)) * u
            y = top + depth * ((1 - u) ** 0.8) * (1.0 - 0.25 * u)
        jag = rng.uniform(-0.11, 0.11) * half
        pts.append((x + jag * 0.5, max(top + 6.0, y + jag)))
    # pts: top left, top right, then the underside right to left.
    return pts, tip, top + depth


def _root(c, rng, x, y, length, width, sway, colour=ROOT):
    """One hanging root: a tapering curve with a rootlet or two off it."""
    pts = []
    for i in range(7):
        t = i / 6
        pts.append((x + sway * t * t + math.sin(t * 3.1 + x) * 3.0 * t, y + length * t))
    for a, b in zip(pts, pts[1:]):
        t = pts.index(a) / 6
        w = max(0.6, width * (1.0 - t * 0.85))
        c.put(c.mask(lambda p: p.line([a, b], w)), colour)
        c.put(c.mask(lambda p: p.line([(a[0] + w * 0.25, a[1]), (b[0] + w * 0.25, b[1])], w * 0.45)), ROOT_DARK, 0.5)
    c.put(c.mask(lambda p: p.line([(pts[0][0] - width * 0.25, pts[0][1]), (pts[2][0] - width * 0.2, pts[2][1])], max(0.5, width * 0.3))), ROOT_LIGHT, 0.6)
    for _ in range(rng.randint(1, 3)):
        k = rng.randint(2, 5)
        bx, by = pts[k]
        side = rng.choice((-1, 1))
        l2 = length * rng.uniform(0.18, 0.32)
        c.put(c.mask(lambda p: p.line([(bx, by), (bx + side * l2 * 0.5, by + l2 * 0.4), (bx + side * l2 * 0.7, by + l2)], max(0.5, width * 0.35))), colour, 0.9)


def island(c, cx, top, half, seed):
    """A floating island of earth: soil and grass on its flat top (the
    platform), earth under, a tip of rock, roots out of its underside and
    sides, a float crystal in its rock and crumbs drifting under it."""
    rng = c.rand(seed, "island")
    pts, tip, bottom = _outline(cx, top, half, rng)
    # The roots behind the island first, so the island covers where they
    # leave it.
    for i in range(9):
        x = cx + (i - 4) / 4.0 * half * 0.72 + rng.uniform(-6, 6)
        under = top + (bottom - top) * (1.0 - abs(x - tip) / (half * 1.05)) ** 0.9
        _root(c, rng, x, under - 10, rng.uniform(34, 96), rng.uniform(2.0, 3.6), rng.uniform(-16, 16))
    body = c.mask(lambda p: p.poly(pts))
    c.put(body, ROCK)
    # Its strata: earth over the rock's tip, the line between them wavy.
    wave = top + (bottom - top) * 0.5 + 7.0 * (c.noise((seed, "strata"), 6, 2) - 0.5) * 2
    earth = body * (c.y < wave)
    c.put(earth, EARTH)
    grain = c.noise((seed, "grain"), 18, 8)
    c.put(earth * (grain > 0.62), EARTH_DARK, 0.5)
    c.put(earth * (grain < 0.25), EARTH_LIGHT, 0.35)
    # Its far side in shade, and the rock's lit edges.
    c.put(body * (c.x > cx + half * 0.15) * ((c.x - cx) / half).clip(0, 1), ROCK_DARK, 0.55)
    c.put(body * (c.y >= wave) * (c.y < wave + 3.0), ROCK_LIGHT, 0.5)
    # Stones set in the earth.
    for _ in range(int(half / 10)):
        x = rng.uniform(cx - half * 0.8, cx + half * 0.8)
        y = rng.uniform(top + 14, top + (wave.mean() - top) * 0.9)
        r = rng.uniform(2.0, 4.5)
        c.put(c.mask(lambda p: p.ellipse(x, y, r, r * 0.7)) * body, PEBBLE)
        c.put(c.mask(lambda p: p.ellipse(x + r * 0.3, y + r * 0.25, r * 0.7, r * 0.45)) * body, ROCK_DARK, 0.5)
    # Roots that come out of its sides and curl down over them.
    for side in (-1, 1):
        for k in range(2):
            y0 = top + 14 + k * 16 + rng.uniform(-3, 3)
            x0 = cx + side * (half - 4 - (y0 - top) * 0.45)
            _root(c, rng, x0, y0, rng.uniform(26, 50), rng.uniform(1.6, 2.6), side * rng.uniform(8, 18))
    # The soil and the grass of the top: the platform's face.
    c.put(c.mask(lambda p: p.poly([(cx - half, top - 1), (cx + half, top - 1), (cx + half * 0.97, top + 9), (cx - half * 0.97, top + 9)])), SOIL)
    c.put(c.mask(lambda p: p.rect(cx - half, top - 4, cx + half, top + 2)), GRASS)
    c.put(c.mask(lambda p: p.rect(cx - half, top - 4, cx + half, top - 2)), GRASS_LIGHT, 0.8)
    for i in range(int(half * 2 / 5)):
        x = cx - half + 2 + i * 5 + rng.uniform(-1.5, 1.5)
        h = rng.uniform(3, 8)
        lean = rng.uniform(-2.5, 2.5)
        c.put(c.mask(lambda p: p.poly([(x - 1.6, top - 2), (x + 1.6, top - 2), (x + lean, top - 2 - h)])), GRASS if i % 3 else GRASS_DARK)
    # Grass over the lip at both ends, hanging a little.
    for side in (-1, 1):
        x = cx + side * half
        c.put(c.mask(lambda p: p.poly([(x - side * 10, top - 3), (x + side * 2, top - 2), (x + side * 1, top + 10), (x - side * 3, top + 6)])), GRASS_DARK)
    # The crystal that holds it up, glowing, and a crumb or two under it.
    gx, gy = tip + (cx - tip) * 0.2, top + (bottom - top) * 0.72
    c.put(c.mask(lambda p: p.ellipse(gx, gy, 22, 16), blur=6.0), CYAN, 0.35)
    for dx, dy, s in ((0.0, 0.0, 7.0), (-9.0, 5.0, 4.5), (8.0, 4.0, 4.0)):
        x, y = gx + dx, gy + dy
        c.put(c.mask(lambda p: p.poly([(x, y - s * 1.5), (x + s * 0.6, y), (x, y + s * 0.5), (x - s * 0.6, y)])), CYAN, 0.9)
        c.put(c.mask(lambda p: p.poly([(x, y - s * 1.5), (x + s * 0.6, y), (x, y)])), mix(CYAN, (255, 255, 255), 0.55), 0.9)
    for i in range(4):
        x = tip + rng.uniform(-half * 0.5, half * 0.5)
        y = bottom + rng.uniform(16, 60)
        r = rng.uniform(2.5, 6.0)
        c.put(c.mask(lambda p: p.poly([(x - r, y), (x - r * 0.3, y - r * 0.8), (x + r, y - r * 0.2), (x + r * 0.4, y + r * 0.7)])), EARTH if i % 2 else ROCK)
        c.put(c.mask(lambda p: p.ellipse(x, y + r * 1.6, r * 1.4, r * 0.5), blur=2.0), CYAN, 0.18)


def apple_tree(name):
    cx, top, half, crown_rx, crown_ry = TREES[name]

    def draw(c, k):
        rng = c.rand(name, "apples")
        island(c, cx, top, half, name)
        trunk(c, cx, top - 3, top - TRUNK, 20)
        crown_y = top - TRUNK - crown_ry * 0.55
        clumps = canopy(c, cx, crown_y, crown_rx, crown_ry, name)
        # A few apples high in the crown; the ones that fall are the room's.
        for x, y, r in clumps:
            if y < crown_y - crown_ry * 0.25 and rng.random() < 0.5:
                apple(c, x + rng.uniform(-6, 6), y + r * 0.4, 6.0, rng.uniform(-0.35, 0.35))
        for x, y, a in ((cx - crown_rx * 0.7, top - 8, 0.7), (cx + crown_rx * 0.5, top - 6, 2.1)):
            leaf(c, x, y, a)

    return draw


def _frame(name):
    cx, top, half, crown_rx, crown_ry = TREES[name]
    reach = max(crown_rx * 1.1, half + 26)
    crown_top = top - TRUNK - crown_ry * 0.55 - crown_ry - 12
    # On whole units, so the canvas is a whole number of pixels.
    return (math.floor(cx - reach), math.floor(crown_top), math.ceil(cx + reach), math.ceil(top + half * 0.95 + 150))


PIECES: Dict[str, Piece] = {name: Piece(_frame(name), apple_tree(name)) for name in TREES}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
