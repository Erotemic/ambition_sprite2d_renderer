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
  first field: a flared trunk, limbs into a full crown, a few apples
  ripening on it. The apples that come off it are things of the world (the
  `apple` held item, grown in its crown by the room's `GroundItem`s), and
  they fall UP in its field, to the vault's underside.
- `orchard_hanging_tree`: over the first chasm, a tree that grows down
  from a planter in the vault (up is down for it). Its apples drop the way
  it grows, onto the ceiling a body walks.
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


def leaf(c, x, y, ang, s=5.0):
    dx, dy = math.cos(ang) * s, math.sin(ang) * s
    c.put(c.mask(lambda p: p.poly([(x - dx, y - dy), (x - dy * 0.4, y + dx * 0.4), (x + dx, y + dy), (x + dy * 0.4, y - dx * 0.4)])), LEAF)
    c.put(c.mask(lambda p: p.line([(x - dx, y - dy), (x + dx, y + dy)], 0.6)), LEAF_DARK)


LEAF_DEEP = scale(LEAF_DARK, 0.72)
LEAF_SUN = mix(LEAF, (226, 244, 170), 0.42)
BARK_LIGHT = mix(BARK, (200, 170, 130), 0.35)


def clump(c, x, y, r, cx, cy, rx, ry, rim=True):
    """One clump of leaves in a crown centred (cx, cy): darker under, and
    lighter the nearer it sits to the crown's sunny upper left."""
    lit = 0.5 + 0.5 * max(-1.0, min(1.0, ((cx - x) / rx + (cy - y) / ry) * 0.7))
    if rim:
        c.put(c.mask(lambda p: p.ellipse(x, y, r * 1.05, r * 0.9)), LEAF_DEEP)
    c.put(c.mask(lambda p: p.ellipse(x, y, r, r * 0.86)), mix(LEAF_DARK, LEAF, 0.35 + 0.4 * lit))
    c.put(c.mask(lambda p: p.ellipse(x - r * 0.18, y - r * 0.22, r * 0.72, r * 0.6)), mix(LEAF, LEAF_SUN, 0.15 + 0.5 * lit))
    c.put(c.mask(lambda p: p.ellipse(x - r * 0.36, y - r * 0.4, r * 0.3, r * 0.22)), LEAF_SUN, 0.35 + 0.5 * lit)


def canopy(c, cx, cy, rx, ry, seed):
    """A full apple-tree crown, lit from the upper left: a deep shadow
    inside, clumps of leaves over it, each clump darker under and lighter on
    its sunny side, a leafy grain through it all and loose leaves at its
    edge. Returns the clumps, front ones last."""
    rng = c.rand(seed)
    clumps = []
    for _ in range(30):
        a = rng.uniform(0.0, math.tau)
        d = math.sqrt(rng.uniform(0.0, 1.0))
        x, y = cx + math.cos(a) * d * rx * 0.86, cy + math.sin(a) * d * ry * 0.8
        clumps.append((x, y, rng.uniform(0.26, 0.42) * rx))
    # Back to front: the clumps lower and to the right are further round
    # the crown from the light.
    clumps.sort(key=lambda clump: clump[0] - clump[1])
    crown = c.mask(lambda p: [p.ellipse(x, y, r * 1.05, r * 0.9) for x, y, r in clumps])
    c.put(crown, LEAF_DEEP)
    for x, y, r in clumps:
        clump(c, x, y, r, cx, cy, rx, ry)
    c.tone(crown * (c.noise((seed, "leaves"), rx / 5.0, ry / 5.0, 3) - 0.5), 0.32)
    # Loose leaves round the edge break up its outline.
    for _ in range(46):
        a = rng.uniform(0.0, math.tau)
        lx, ly = cx + math.cos(a) * rx * rng.uniform(0.88, 1.04), cy + math.sin(a) * ry * rng.uniform(0.86, 1.02)
        leaf(c, lx, ly, a + rng.uniform(-0.8, 0.8), rng.uniform(3.4, 5.2))
    return clumps


def trunk(c, x, y0, y1, w, seed="trunk"):
    """A trunk from its foot at y0 to its crown at y1 (either way): a flared
    foot, a taper, bark grain, a knot or two, and four limbs that reach out
    into the crown."""
    sign = 1 if y1 > y0 else -1
    length = abs(y1 - y0)
    rng = c.rand(seed)
    flare = [(x - w * 0.95, y0), (x - w * 0.5, y0 + sign * 10), (x - w * 0.36, y1), (x + w * 0.36, y1),
             (x + w * 0.5, y0 + sign * 10), (x + w * 0.95, y0)]
    body = c.mask(lambda p: p.poly(flare))
    c.put(body, BARK)
    # The shaded side and the lit edge.
    c.put(c.mask(lambda p: p.poly([(x + w * 0.1, y0), (x + w * 0.95, y0), (x + w * 0.5, y0 + sign * 10), (x + w * 0.36, y1), (x + w * 0.04, y1)])), BARK_DARK, 0.55)
    c.put(c.mask(lambda p: p.poly([(x - w * 0.5, y0 + sign * 10), (x - w * 0.36, y1), (x - w * 0.24, y1), (x - w * 0.36, y0 + sign * 10)])), BARK_LIGHT, 0.55)
    # Bark grain along it, and knots.
    grain = c.mask(lambda p: [p.line([(x + dx, y0 + sign * 6), (x + dx * 0.7, y1)], 0.9) for dx in (-w * 0.3, -w * 0.12, w * 0.06, w * 0.22)])
    c.put(grain * body, BARK_DARK, 0.7)
    c.tone(body * (c.noise((seed, "bark"), 3, max(4.0, length / 14.0), 2) - 0.5), 0.25)
    for t in (0.38, 0.62):
        kx, ky = x + rng.uniform(-w * 0.15, w * 0.15), y0 + sign * length * t
        c.put(c.mask(lambda p: p.ellipse(kx, ky, w * 0.14, w * 0.2)), BARK_DARK)
        c.put(c.mask(lambda p: p.ellipse(kx - 0.6, ky - 0.6, w * 0.07, w * 0.1)), BARK_LIGHT, 0.6)


def limbs(c, x, y0, y1, w):
    """The trunk's limbs, painted over the crown's lower part (the crown's
    front clumps go over their ends after): out and on into the leaves,
    thinning as they go, with twigs off them."""
    sign = 1 if y1 > y0 else -1
    for side, reach, rise in ((-1, 3.2, 1.2), (1, 3.6, 1.5), (-1, 1.5, 2.6), (1, 1.3, 2.9)):
        bx, by = x + side * w * 0.12, y1 - sign * w * 0.9
        mx, my = x + side * w * reach * 0.5, y1 + sign * w * rise * 0.8
        ex, ey = x + side * w * reach, y1 + sign * w * rise * 1.6
        c.put(c.mask(lambda p: p.line([(bx, by), (mx, my)], w * 0.42)), BARK)
        c.put(c.mask(lambda p: p.line([(mx, my), (ex, ey)], w * 0.24)), BARK)
        c.put(c.mask(lambda p: p.line([(bx + side * w * 0.12, by), (mx + side * w * 0.08, my), (ex, ey)], w * 0.1)), BARK_DARK, 0.6)
        tx, ty = (mx + ex) / 2, (my + ey) / 2
        c.put(c.mask(lambda p: p.line([(tx, ty), (tx - side * w * 0.5, ty + sign * w * 0.9)], w * 0.1)), BARK)


def front_leaves(c, clumps, cx, cy, rx, ry, seed, every=3):
    """Some of a crown's clumps again, over its limbs, so the limbs show in
    the gaps between them and not as sticks laid on top."""
    front = clumps[1::every]
    for x, y, r in front:
        clump(c, x, y, r * 0.72, cx, cy, rx, ry, rim=False)
    m = c.mask(lambda p: [p.ellipse(x, y, r * 0.72, r * 0.62) for x, y, r in front])
    c.tone(m * (c.noise((seed, "front"), rx / 5.0, ry / 5.0, 3) - 0.5), 0.32)
    for x, y, r in front:
        leaf(c, x + r * 0.5, y + r * 0.45, 0.6 + x % 1.3, 4.2)


def planter(c, x0, x1, y_open, depth):
    """A steel planter box: soil at its open face (y_open), `depth` deep
    (down for a floor planter, up for one in the vault)."""
    y_far = y_open + depth
    lo, hi = min(y_open, y_far), max(y_open, y_far)
    c.put(c.mask(box(x0, lo, x1, hi)), STEEL)
    c.put(c.mask(box(x0, lo, x1, lo + 2)), STEEL_LIGHT)
    c.put(c.mask(box(x0 + 4, min(y_open, y_open + 4 * (1 if depth > 0 else -1)), x1 - 4, max(y_open, y_open + 4 * (1 if depth > 0 else -1)))), SOIL)
    c.put(c.mask(lambda p: [p.rect(x, lo + 4, x + 2, hi - 2) for x in range(int(x0) + 10, int(x1) - 6, 18)]), STEEL_DARK, 0.6)


#: Where the trees' crowns are, for the room's apples: (centre x, centre y,
#: half width, half height) in room coordinates. The generator grows the
#: `apple` ground items inside these.
RISING_CROWN = ((FIRST[0] + FIRST[1]) / 2, FLOOR - 262, 98, 70)
HANGING_CROWN = ((BRIDGE[0] + BRIDGE[1]) / 2, VAULT + 236, 118, 74)


def ripening(c, clumps, rng, stem_turn):
    """A few apples ripening on the branches, half in the leaves: most of a
    tree's apples are the world's own (the generator grows them)."""
    for x, y, r in clumps[2::5]:
        apple(c, x + rng.uniform(-r * 0.4, r * 0.4), y + r * 0.35 * (1 if stem_turn == 0.0 else -1), 5.2,
              stem_turn + rng.uniform(-0.35, 0.35))


def rising_tree(c, k):
    x0, x1 = FIRST
    cx, cy, rx, ry = RISING_CROWN
    planter(c, cx - 56, cx + 56, FLOOR - 14, 14)
    trunk(c, cx, FLOOR - 14, FLOOR - 200, 20, "rising_trunk")
    clumps = canopy(c, cx, cy, rx, ry, "rising_crown")
    limbs(c, cx, FLOOR - 14, FLOOR - 200, 20)
    front_leaves(c, clumps, cx, cy, rx, ry, "rising_crown")
    ripening(c, clumps, c.rand("rising_apples"), 0.0)


def hanging_tree(c, k):
    x0, x1 = BRIDGE
    cx, cy, rx, ry = HANGING_CROWN
    planter(c, cx - 64, cx + 64, VAULT + 12, -12)
    trunk(c, cx, VAULT + 12, VAULT + 172, 22, "hanging_trunk")
    clumps = canopy(c, cx, cy, rx, ry, "hanging_crown")
    limbs(c, cx, VAULT + 12, VAULT + 172, 22)
    front_leaves(c, clumps, cx, cy, rx, ry, "hanging_crown")
    ripening(c, clumps, c.rand("hanging_apples"), math.pi)


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
