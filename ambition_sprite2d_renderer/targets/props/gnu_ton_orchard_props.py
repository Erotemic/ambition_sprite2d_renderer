"""GNU-ton's orchard (`gnu_ton_orchard`, the Science dimension): "here an
apple falls up". The room's up fields are its trees, and the trees show the
player what a field does before they walk into one.

Drawn in room coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/gnu_ton_gravity/make_specs.py` (`orchard`):
the floor (y 704), the vault's underside (y 80), the nook in it
(x 432..512), the first field (x 352..592), the bridge field over the first
chasm (x 896..1568), the swinging field's track (its centre 2176, 256 each
way, 224 wide), the middle bank (x 1504..1888).

- `orchard_rising_tree`: an apple tree in a planter on the floor, in the
  first field. Its apples come off and fall UP: some on their way, a leaf
  or two with them, and the rest resting against the vault's underside.
- `orchard_hanging_tree`: over the first chasm, a tree that grows down
  from a planter in the vault (up is down for it), its apples fallen up
  round its pot, where a body walking the ceiling walks among them.
- `orchard_swing_rail`: the swinging field's track, a rail under the vault
  with its end stops, and the hooks a tree hung from once.
- `orchard_crates`: on the middle bank, crates of picked apples, stencilled
  THIS WAY UP with the arrow, wrongly, both ways.

Animations: ``idle``, 1 frame each. No drop shadows: form shade on a
thing's own faces only.
"""

from __future__ import annotations

import math
from typing import Dict

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .orbital_station import AMBER, HULL, HULL_DARK, HULL_LIGHT, INK, LEAF, LEAF_DARK, STEEL, STEEL_DARK, STEEL_LIGHT

FLOOR, VAULT = 704, 80
NOOK = (432, 512)
FIRST = (352, 592)
BRIDGE = (896, 1568)
SWING_CENTRE, SWING_REACH, SWING_W = 2176, 256, 224
MIDDLE_BANK = (1504, 1888)
PAL = {"stone": HULL, "stone_light": HULL_LIGHT, "dark": STEEL_DARK, "lamp": AMBER}

APPLE = (206, 46, 40)
APPLE_DARK = (140, 28, 30)
APPLE_LIGHT = (250, 130, 110)
BARK = (112, 80, 56)
BARK_DARK = (76, 52, 36)
SOIL = (70, 52, 40)
WOOD = (176, 132, 84)
WOOD_DARK = (126, 90, 56)


def apple(c, x, y, r=6.0, turn=0.0):
    """An apple centred at (x, y), its stem `turn` radians from up."""
    c.put(c.mask(lambda p: p.ellipse(x, y, r, r * 0.92)), APPLE)
    c.put(c.mask(lambda p: p.ellipse(x + r * 0.25, y + r * 0.3, r * 0.75, r * 0.6)), APPLE_DARK, 0.45)
    c.put(c.mask(lambda p: p.ellipse(x - r * 0.38, y - r * 0.35, r * 0.28, r * 0.22)), APPLE_LIGHT, 0.9)
    sx, sy = math.sin(turn), -math.cos(turn)
    c.put(c.mask(lambda p: p.line([(x + sx * r * 0.7, y + sy * r * 0.7), (x + sx * r * 1.35, y + sy * r * 1.35)], 1.2)), BARK_DARK)
    lx, ly = x + sx * r * 1.1 + sy * r * 0.5, y + sy * r * 1.1 - sx * r * 0.5
    c.put(c.mask(lambda p: p.ellipse(lx, ly, r * 0.45, r * 0.25)), LEAF)


def rising(c, x, y, r=6.0, turn=0.0, trail=18.0):
    """An apple on its way up: the comic's speed lines under it."""
    c.put(c.mask(lambda p: [p.line([(x + dx, y + r + 3), (x + dx, y + r + 3 + trail * k)], 1.0) for dx, k in ((-3.5, 0.6), (0, 1.0), (3.5, 0.7))]), HULL_LIGHT, 0.55)
    apple(c, x, y, r, turn)


def leaf(c, x, y, ang, s=5.0):
    dx, dy = math.cos(ang) * s, math.sin(ang) * s
    c.put(c.mask(lambda p: p.poly([(x - dx, y - dy), (x - dy * 0.4, y + dx * 0.4), (x + dx, y + dy), (x + dy * 0.4, y - dx * 0.4)])), LEAF)
    c.put(c.mask(lambda p: p.line([(x - dx, y - dy), (x + dx, y + dy)], 0.6)), LEAF_DARK)


def canopy(c, cx, cy, rx, ry, seed):
    """A round apple-tree crown: clumps of leaves, dark under, light over."""
    rng = c.rand(seed)
    clumps = [(cx + rng.uniform(-rx, rx) * 0.8, cy + rng.uniform(-ry, ry) * 0.75, rng.uniform(0.35, 0.55) * rx) for _ in range(14)]
    c.put(c.mask(lambda p: [p.ellipse(x, y, r, r * 0.8) for x, y, r in clumps]), LEAF_DARK)
    c.put(c.mask(lambda p: [p.ellipse(x - r * 0.15, y - r * 0.2, r * 0.8, r * 0.62) for x, y, r in clumps]), LEAF)
    c.put(c.mask(lambda p: [p.ellipse(x - r * 0.35, y - r * 0.4, r * 0.35, r * 0.25) for x, y, r in clumps]), mix(LEAF, (220, 240, 180), 0.35), 0.8)
    return clumps


def trunk(c, x, y0, y1, w):
    """A trunk from y0 to y1 (either way), forking at the far end."""
    sign = 1 if y1 > y0 else -1
    pts = [(x - w / 2, y0), (x + w / 2, y0), (x + w * 0.3, y1), (x - w * 0.3, y1)]
    c.put(c.mask(lambda p: p.poly(pts)), BARK)
    c.put(c.mask(lambda p: p.poly([(x + w * 0.15, y0), (x + w / 2, y0), (x + w * 0.3, y1), (x + w * 0.05, y1)])), BARK_DARK, 0.6)
    for side in (-1, 1):
        c.put(c.mask(lambda p: p.line([(x, y1 - sign * 10), (x + side * w * 1.6, y1 + sign * 14)], w * 0.35)), BARK)


def planter(c, x0, x1, y_open, depth):
    """A steel planter box: soil at its open face (y_open), `depth` deep
    (down for a floor planter, up for one in the vault)."""
    y_far = y_open + depth
    lo, hi = min(y_open, y_far), max(y_open, y_far)
    c.put(c.mask(box(x0, lo, x1, hi)), STEEL)
    c.put(c.mask(box(x0, lo, x1, lo + 2)), STEEL_LIGHT)
    c.put(c.mask(box(x0 + 4, min(y_open, y_open + 4 * (1 if depth > 0 else -1)), x1 - 4, max(y_open, y_open + 4 * (1 if depth > 0 else -1)))), SOIL)
    c.put(c.mask(lambda p: [p.rect(x, lo + 4, x + 2, hi - 2) for x in range(int(x0) + 10, int(x1) - 6, 18)]), STEEL_DARK, 0.6)


def rising_tree(c, k):
    x0, x1 = FIRST
    cx = (x0 + x1) / 2
    planter(c, cx - 56, cx + 56, FLOOR - 14, 14)
    trunk(c, cx, FLOOR - 14, FLOOR - 190, 18)
    clumps = canopy(c, cx, FLOOR - 250, 92, 64, "rising_crown")
    rng = c.rand("rising_apples")
    for x, y, r in clumps[::2]:
        apple(c, x + rng.uniform(-6, 6), y + r * 0.4, 5.5, rng.uniform(-0.4, 0.4))
    # Off the tree and up: apples on their way, and a leaf or two.
    for x, y in ((cx - 50, 360), (cx + 30, 300), (cx - 8, 230), (cx + 62, 190), (cx - 70, 160)):
        rising(c, x, y, 6.0, rng.uniform(-0.6, 0.6), rng.uniform(14, 22))
    for x, y, a in ((cx + 10, 330, 0.6), (cx - 40, 250, 2.2), (cx + 48, 140, 1.1)):
        leaf(c, x, y, a)
    # Fallen up: resting against the vault's underside, stems down, either
    # side of the nook (the nook's own apple is its coin).
    for x in (x0 + 14, x0 + 30, x0 + 47, x0 + 62, NOOK[1] + 14, NOOK[1] + 31, NOOK[1] + 50, x1 - 14):
        apple(c, x, VAULT + 6.5, 6.0, math.pi + rng.uniform(-0.5, 0.5))


def hanging_tree(c, k):
    x0, x1 = BRIDGE
    cx = (x0 + x1) / 2
    planter(c, cx - 64, cx + 64, VAULT + 12, -12)
    trunk(c, cx, VAULT + 12, VAULT + 170, 20)
    clumps = canopy(c, cx, VAULT + 232, 110, 70, "hanging_crown")
    rng = c.rand("hanging_apples")
    for x, y, r in clumps[1::2]:
        apple(c, x + rng.uniform(-6, 6), y - r * 0.4, 5.5, math.pi + rng.uniform(-0.4, 0.4))
    # Its apples fall the way it grows: down to the ceiling, round its pot
    # and out along the walk.
    for x in (cx - 150, cx - 126, cx - 96, cx - 80, cx + 82, cx + 100, cx + 131, cx + 170, cx + 230):
        apple(c, x, VAULT + 6.5, 6.0, math.pi + rng.uniform(-0.6, 0.6))
    for x, y in ((cx - 46, VAULT + 70), (cx + 52, VAULT + 104)):
        rising(c, x, y, 6.0, rng.uniform(-0.5, 0.5), 16)


def swing_rail(c, k):
    x0, x1 = SWING_CENTRE - SWING_REACH - SWING_W / 2, SWING_CENTRE + SWING_REACH + SWING_W / 2
    c.put(c.mask(box(x0, VAULT, x1, VAULT + 10)), STEEL)
    c.put(c.mask(box(x0, VAULT + 8, x1, VAULT + 10)), STEEL_DARK)
    c.put(c.mask(lambda p: [p.rect(x, VAULT, x + 3, VAULT + 10) for x in range(int(x0) + 24, int(x1) - 20, 48)]), STEEL_DARK, 0.7)
    for x in (x0, x1 - 14):
        c.put(c.mask(box(x, VAULT, x + 14, VAULT + 22)), AMBER)
        c.put(c.mask(lambda p: [p.poly([(x + d, VAULT + 22), (x + d + 5, VAULT + 22), (x + d + 12, VAULT + 10), (x + d + 7, VAULT + 10)]) for d in (-4, 6)]), INK)
    # The hooks a tree hung from once (it went for a walk).
    for x in (SWING_CENTRE - 40, SWING_CENTRE, SWING_CENTRE + 40):
        c.put(c.mask(lambda p: p.ring(x, VAULT + 20, 5, 1.6)), STEEL_LIGHT)
        c.put(c.mask(box(x - 1, VAULT + 10, x + 1, VAULT + 15)), STEEL_LIGHT)


def crate(c, x0, y1, w, h, arrow_up):
    y0 = y1 - h
    c.put(c.mask(box(x0, y0, x1 := x0 + w, y1)), WOOD)
    c.put(c.mask(lambda p: [p.rect(x0, y, x1, y + 1.2) for y in (y0 + h / 3, y0 + 2 * h / 3)]), WOOD_DARK, 0.7)
    c.put(c.mask(lambda p: [p.rect(x0, y0, x0 + 3, y1), p.rect(x1 - 3, y0, x1, y1), p.rect(x0, y0, x1, y0 + 3)]), WOOD_DARK)
    c.put(c.mask(box(x1 - 6, y0 + 3, x1 - 3, y1)), scale(WOOD_DARK, 0.85))
    # Apples heaped in the open top.
    for i in range(int(w // 9)):
        apple(c, x0 + 7 + i * 9, y0 - 3 + (i % 2) * 2, 4.6, (i - 2) * 0.3)
    # THIS WAY UP, the arrow stencilled once each way.
    ax, ay = x0 + w / 2, y0 + h * 0.55
    s = -1 if arrow_up else 1
    c.put(c.mask(lambda p: (p.poly([(ax, ay + s * 9), (ax - 7, ay + s * 2), (ax + 7, ay + s * 2)]), p.rect(ax - 2.2, min(ay + s * 2, ay - s * 8), ax + 2.2, max(ay + s * 2, ay - s * 8)))), INK, 0.85)


def crates(c, k):
    x0 = MIDDLE_BANK[0] + 96
    crate(c, x0, FLOOR, 54, 34, True)
    crate(c, x0 + 58, FLOOR, 54, 34, False)
    crate(c, x0 + 28, FLOOR - 34, 54, 30, True)


PIECES: Dict[str, Piece] = {
    "orchard_rising_tree": Piece((FIRST[0], VAULT, FIRST[1], FLOOR), rising_tree),
    "orchard_hanging_tree": Piece((BRIDGE[0] + 60, VAULT, BRIDGE[1] - 60, VAULT + 340), hanging_tree),
    "orchard_swing_rail": Piece((SWING_CENTRE - SWING_REACH - SWING_W / 2, VAULT, SWING_CENTRE + SWING_REACH + SWING_W / 2, VAULT + 28), swing_rail),
    "orchard_crates": Piece((MIDDLE_BANK[0] + 90, FLOOR - 80, MIDDLE_BANK[0] + 220, FLOOR), crates),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
