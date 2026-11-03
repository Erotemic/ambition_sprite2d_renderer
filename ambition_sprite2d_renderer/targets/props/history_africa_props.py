"""The props of Africa and the Levant in the History dimension (second pass).

The second pass of the History dimension is a grid: each floor is a region
of the world and each column a time. These props serve the African floor
(the Cradle, the southern coast, the Green Sahara, Aksum and Kush) and the
Levant and Sumer. They are drawn in the cel style of the cast
(`targets/characters/_art_cast_kit.py`) in the sepia of an old textbook,
with the colours of the savanna: ochre earth, gold grass, acacia green and
red ochre.

- ``history_thorn_boma``: the look of a `LockWall` of 32 by 128 world
  units, drawn at 3 to 1 (as ``history_great_wall_gate``). A boma: a wall
  of cut thorn branches, piled high and tangled, as herders build round
  their cattle at night.
- ``history_campfire``: scenery. A fire in a ring of stones with three
  logs. Its ``idle`` row moves the flames and sends up sparks and smoke.
- ``history_acacia``: scenery. An umbrella thorn acacia: a forked trunk
  and a wide flat crown.
- ``history_rock_art``: scenery. A face of sandstone painted with cattle,
  herders and a dancer in red ochre and white, as in the rock shelters of
  the Green Sahara.
- ``history_reed_boat``: the look of a sweeping platform (a
  `MovingPlatform` whose ``visual`` it is): a boat of bound reed bundles
  with a high curled prow and stern. The top of its deck is the platform
  (`platform_looks.ron`: `REED_BOAT_SPAN`, `REED_BOAT_TOP`). Its ``idle``
  row moves the pennant and the water at its sides; the deck does not move.
- ``history_aksum_stele``: scenery. A tall stele of granite of Aksum, carved
  as a tower: storeys of false windows, a false door at its foot and a
  round top.
- ``history_laetoli_footprints``: scenery. A slab of hardened volcanic ash
  with two trails of footprints, a large one and a small one, side by side.
  Someone walked here 3.7 million years ago.

The numbers are frame pixels; the game shows each prop at half its frame
(the boma at a third). No drop shadows: the game draws them.
"""

from __future__ import annotations

import math
import random
from typing import Callable, Dict, List, Tuple

from ..characters import _art_cast_kit as K
from .art_props import _publisher

Point = Tuple[float, float]
STILL: List[Tuple[str, int, int]] = [("idle", 1, 1000)]
LOOP: List[Tuple[str, int, int]] = [("idle", 8, 110)]

#: The outline: the dark sepia of old ink.
OUTLINE = (52, 34, 24, 255)
SEPIA = (112, 76, 48, 255)
THORN = (150, 112, 74, 255)
THORN_LIGHT = (196, 160, 112, 255)
THORN_DARK = (96, 66, 42, 255)
THORN_PALE = (236, 226, 200, 255)
ACACIA = (122, 150, 64, 255)
ACACIA_LIGHT = (168, 190, 90, 255)
ACACIA_DARK = (78, 104, 46, 255)
BARK = (110, 84, 62, 255)
BARK_LIGHT = (150, 120, 90, 255)
BARK_DARK = (72, 54, 40, 255)
STONE = (176, 164, 146, 255)
STONE_LIGHT = (208, 198, 180, 255)
STONE_SHADE = (128, 116, 102, 255)
SANDSTONE = (214, 156, 102, 255)
SANDSTONE_LIGHT = (234, 188, 136, 255)
SANDSTONE_SHADE = (170, 112, 72, 255)
SANDSTONE_DARK = (130, 80, 52, 255)
RED_OCHRE = (166, 52, 34, 255)
OCHRE_WHITE = (246, 236, 214, 255)
REED = (214, 186, 104, 255)
REED_LIGHT = (240, 220, 150, 255)
REED_SHADE = (164, 134, 66, 255)
ROPE = (126, 90, 52, 255)
WATER = (64, 140, 180, 255)
WATER_LIGHT = (156, 210, 232, 255)
GRANITE = (150, 140, 144, 255)
GRANITE_LIGHT = (188, 180, 182, 255)
GRANITE_SHADE = (108, 98, 104, 255)
GRANITE_DARK = (70, 62, 68, 255)
ASH = (196, 188, 178, 255)
ASH_LIGHT = (222, 216, 206, 255)
ASH_SHADE = (150, 140, 130, 255)
FIRE = (255, 196, 60, 255)
FIRE_HOT = (255, 244, 170, 255)
FIRE_RED = (232, 96, 40, 255)
EMBER = (255, 132, 50, 255)
SMOKE = (186, 178, 172, 255)
LINEN = (236, 224, 196, 255)


def _phase(i: int, n: int) -> float:
    return i / float(max(1, n))


def _rect(x0: float, y0: float, x1: float, y1: float) -> List[Point]:
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


# ---------------------------------------------------------------------------
# The thorn boma: a wall of cut thorn branches.
# ---------------------------------------------------------------------------

BOMA_FRAME = (96, 384)


def _branch(f: K.Frame, rng: random.Random, a: Point, b: Point, width: float, colour, depth: int = 0) -> None:
    """A thorn branch from `a` to `b`: a crooked limb, side twigs and thorns."""
    mid = ((a[0] + b[0]) / 2.0 + rng.uniform(-4.0, 4.0), (a[1] + b[1]) / 2.0 + rng.uniform(-4.0, 4.0))
    f.limb([a, mid, b], width, colour)
    length = math.hypot(b[0] - a[0], b[1] - a[1])
    for k in range(int(length / 9.0)):
        u = (k + 0.5) / max(1.0, length / 9.0)
        p = (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)
        ang = math.atan2(b[1] - a[1], b[0] - a[0]) + (1.0 if k % 2 else -1.0) * rng.uniform(0.6, 1.2)
        ln = rng.uniform(3.0, 6.0)
        tip = (p[0] + math.cos(ang) * ln, p[1] + math.sin(ang) * ln)
        # The long pale thorns of an acacia.
        f.limb([p, tip], 1.1, THORN_PALE)
    if depth < 1:
        for _ in range(2):
            u = rng.uniform(0.3, 0.8)
            p = (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)
            ang = math.atan2(b[1] - a[1], b[0] - a[0]) + rng.choice((-1.0, 1.0)) * rng.uniform(0.5, 1.0)
            ln = rng.uniform(10.0, 18.0)
            _branch(f, rng, p, (p[0] + math.cos(ang) * ln, p[1] + math.sin(ang) * ln), width * 0.55, colour, depth + 1)


def _draw_boma(anim: str, i: int, n: int):
    w, h = BOMA_FRAME
    m = 6.0
    foot = h - m
    f = K.Frame(BOMA_FRAME)
    rng = random.Random("history_thorn_boma")
    # The dark mass of the pile behind: the shadow between the branches. Its
    # edge is ragged, as a heap of thorn is.
    left, right = [], []
    for k in range(17):
        y = m + 14.0 + (foot - m - 14.0) * k / 16.0
        left.append((m + 2.0 + rng.uniform(0.0, 10.0), y))
        right.append((w - m - 2.0 - rng.uniform(0.0, 10.0), y))
    top_edge = [(30.0, m + 6.0), (48.0, m + 14.0), (66.0, m + 4.0)]
    f.poly(left[::-1] + top_edge + right, (88, 66, 50, 255))

    def clamp(p: Point) -> Point:
        return (min(w - m - 8.0, max(m + 8.0, p[0])), min(foot - 4.0, max(m + 10.0, p[1])))

    # Branches in layers from the back to the front, laid across on a slant:
    # grey dry wood, lighter at the front.
    for layer, colour in ((0, (128, 104, 82, 255)), (1, (164, 138, 108, 255)), (2, (204, 184, 152, 255))):
        for k in range(11):
            y = 26.0 + k * 33.0 + rng.uniform(-8.0, 8.0) + layer * 11.0
            if y > foot - 10.0:
                continue
            x0 = rng.uniform(m + 6.0, 26.0)
            x1 = rng.uniform(w - 26.0, w - m - 6.0)
            dy = rng.uniform(-30.0, 30.0)
            a, b = clamp((x0, y)), clamp((x1, y + dy))
            if rng.random() < 0.5:
                a, b = b, a
            _branch(f, rng, a, b, 6.4 - layer * 1.0, colour)
    # Two stout stakes that hold the pile, driven into the ground.
    for x in (24.0, 72.0):
        f.limb([(x, foot - 3.0), (x + rng.uniform(-3.0, 3.0), 26.0 + rng.uniform(0.0, 20.0))], 6.0, BARK)
        f.ink([(x - 1.2, foot - 6.0), (x - 1.2, 60.0)], 1.0, BARK_LIGHT)
    # A few green twigs still on the cut branches.
    for _ in range(14):
        x, y = rng.uniform(m + 12.0, w - m - 12.0), rng.uniform(24.0, foot - 12.0)
        f.ellipse(x, y, 3.0, 1.8, ACACIA_LIGHT, body=False)
    return f.finish(outline=OUTLINE, width=1.6)


# ---------------------------------------------------------------------------
# The campfire: a fire in a ring of stones.
# ---------------------------------------------------------------------------

CAMPFIRE_FRAME = (128, 128)
CAMPFIRE_FOOT = 115.0


def _flame(f: K.Frame, cx: float, base: float, width: float, height: float, lean: float, colour, glow: bool = False) -> None:
    pts = [(cx - width, base), (cx - width * 0.8, base - height * 0.4), (cx - width * 0.3 + lean * 0.5, base - height * 0.75), (cx + lean, base - height),
           (cx + width * 0.4 + lean * 0.4, base - height * 0.6), (cx + width, base - height * 0.3), (cx + width * 0.9, base)]
    if glow:
        f.glow_poly(pts, colour)
    else:
        f.poly(pts, colour, body=False)


def _draw_campfire(anim: str, i: int, n: int):
    t = _phase(i, n)
    cyc = math.tau * t
    f = K.Frame(CAMPFIRE_FRAME)
    foot = CAMPFIRE_FOOT
    cx = 64.0
    # The smoke, behind: puffs that rise and fade.
    for k in range(3):
        u = (t + k / 3.0) % 1.0
        x = cx + 6.0 * math.sin(u * 5.0 + k) + 10.0 * u
        y = 56.0 - 44.0 * u
        r = 4.0 + 7.0 * u
        f.ellipse(x, y, r, r * 0.85, K.alpha(SMOKE, 0.55 * (1.0 - u)), body=False)
    # The far stones of the ring.
    rng = random.Random("history_campfire")
    for k in range(5):
        a = math.pi + math.pi * (k + 0.5) / 5.0
        x, y = cx + math.cos(a) * 34.0, foot - 10.0 + math.sin(a) * 8.0
        f.ellipse(x, y, 8.0, 6.0, STONE_SHADE)
    # The logs: three, crossed in a cone; their ends glow.
    for (x0, y0, x1, y1) in ((cx - 30.0, foot - 4.0, cx + 4.0, foot - 30.0), (cx + 30.0, foot - 4.0, cx - 4.0, foot - 30.0), (cx - 8.0, foot - 2.0, cx + 2.0, foot - 32.0)):
        f.limb([(x0, y0), (x1, y1)], 8.0, BARK)
        f.ink([(x0 + (x1 - x0) * 0.1, y0 + (y1 - y0) * 0.1 - 2.0), (x0 + (x1 - x0) * 0.7, y0 + (y1 - y0) * 0.7 - 2.0)], 1.0, BARK_LIGHT)
        f.ellipse(x0, y0, 4.0, 4.0, BARK_LIGHT)
        f.ellipse(x0, y0, 2.4, 2.4, BARK_DARK, body=False)
    # The bed of embers.
    f.ellipse(cx, foot - 8.0, 22.0, 6.0, (110, 42, 28, 255))
    for k in range(9):
        x = cx - 18.0 + k * 4.5
        f.dot(x, foot - 8.0 + rng.uniform(-2.0, 2.0), 1.6, EMBER if (k + i) % 3 else FIRE_HOT)
    # The flames: three tongues, each with its own beat.
    f.glow(cx, foot - 22.0, 22.0, K.alpha(FIRE, 0.16))
    tongues = [(-10.0, 30.0, 0.0), (8.0, 34.0, 1.7), (0.0, 50.0, 3.4)]
    for dx, hgt, off in tongues:
        hh = hgt * (0.85 + 0.15 * math.sin(cyc * 2.0 + off))
        lean = 5.0 * math.sin(cyc + off)
        _flame(f, cx + dx, foot - 8.0, 10.0, hh, lean, FIRE_RED)
    for dx, hgt, off in tongues:
        hh = hgt * (0.85 + 0.15 * math.sin(cyc * 2.0 + off)) * 0.7
        lean = 4.0 * math.sin(cyc + off)
        _flame(f, cx + dx * 0.8, foot - 8.0, 6.6, hh, lean, FIRE)
    _flame(f, cx, foot - 8.0, 5.0, 22.0 * (0.9 + 0.1 * math.sin(cyc * 3.0)), 2.0 * math.sin(cyc), FIRE_HOT)
    # Sparks that fly up.
    for k in range(5):
        u = (t * 1.0 + k / 5.0) % 1.0
        x = cx + (k - 2) * 6.0 + 8.0 * math.sin(u * 6.0 + k)
        y = foot - 40.0 - 50.0 * u
        f.glow(x, y, 1.4, K.alpha(EMBER, 1.0 - u))
    # The near stones of the ring, over the fire's foot.
    for k in range(6):
        a = math.pi * (k + 0.5) / 6.0
        x, y = cx + math.cos(a) * 38.0, foot - 8.0 + math.sin(a) * 6.0
        f.ellipse(x, y, 9.0, 6.4, STONE)
        f.ellipse(x - 2.0, y - 2.0, 4.0, 2.2, STONE_LIGHT, body=False)
    return f.finish(outline=OUTLINE, width=1.4)


# ---------------------------------------------------------------------------
# The acacia: an umbrella thorn tree.
# ---------------------------------------------------------------------------

ACACIA_FRAME = (384, 384)


def _draw_acacia(anim: str, i: int, n: int):
    f = K.Frame(ACACIA_FRAME)
    foot = 376.0
    rng = random.Random("history_acacia")
    # The trunk forks low, then each fork forks again under the crown.
    trunk = [(178.0, foot - 12.0), (176.0, 300.0), (182.0, 250.0)]
    f.limb(trunk, 20.0, BARK)
    f.poly([(162.0, foot), (196.0, foot), (188.0, foot - 16.0), (168.0, foot - 16.0)], BARK)
    limbs = [
        [(182.0, 256.0), (150.0, 200.0), (110.0, 150.0), (70.0, 122.0)],
        [(182.0, 256.0), (214.0, 196.0), (262.0, 150.0), (310.0, 118.0)],
        [(150.0, 200.0), (162.0, 150.0), (150.0, 112.0)],
        [(214.0, 196.0), (206.0, 150.0), (220.0, 108.0)],
        [(110.0, 150.0), (120.0, 118.0)],
        [(262.0, 150.0), (256.0, 116.0)],
    ]
    for k, lm in enumerate(limbs):
        f.limb(lm, 12.0 if k < 2 else 7.0, BARK)
    # The light on the bark, and its cracks.
    f.ink([(172.0, foot - 4.0), (171.0, 300.0), (176.0, 258.0)], 2.0, BARK_LIGHT)
    for k in range(6):
        y = foot - 14.0 - k * 18.0
        f.ink([(180.0, y), (184.0, y - 6.0)], 1.0, BARK_DARK)
    # The crown: a wide flat umbrella, in tufts. The underside is dark.
    under = [(30.0, 120.0), (80.0, 132.0), (150.0, 124.0), (200.0, 130.0), (270.0, 124.0), (350.0, 118.0), (356.0, 104.0), (30.0, 106.0)]
    f.poly(under, ACACIA_DARK)
    tufts = []
    for k in range(14):
        x = 36.0 + k * 23.0 + rng.uniform(-4.0, 4.0)
        y = 98.0 - 26.0 * math.sin(math.pi * (x - 30.0) / 330.0) + rng.uniform(-4.0, 4.0)
        tufts.append((x, y, rng.uniform(22.0, 30.0), rng.uniform(12.0, 16.0)))
    for x, y, rx, ry in tufts:
        f.ellipse(x, y + 8.0, rx, ry, ACACIA)
    for x, y, rx, ry in tufts:
        f.ellipse(x - 4.0, y + 2.0, rx * 0.7, ry * 0.6, ACACIA_LIGHT, body=False)
    for x, y, rx, ry in tufts:
        for _ in range(4):
            px, py = x + rng.uniform(-rx * 0.8, rx * 0.8), y + rng.uniform(-ry * 0.3, ry * 0.9)
            f.ink([(px - 3.0, py), (px + 3.0, py)], 1.0, ACACIA_DARK)
    # The branches that show through the crown's underside.
    for x0, x1 in ((70.0, 40.0), (310.0, 346.0), (150.0, 130.0), (220.0, 240.0)):
        f.limb([(x0, 124.0), (x1, 112.0)], 3.0, BARK_DARK)
    # Seed pods: little curled tan spirals hanging under the crown.
    for x in (64.0, 118.0, 172.0, 236.0, 290.0, 334.0):
        f.limb([(x, 126.0), (x + 4.0, 136.0), (x - 1.0, 142.0)], 2.4, (200, 160, 90, 255))
    return f.finish(outline=OUTLINE, width=1.8)


# ---------------------------------------------------------------------------
# Rock art: a sandstone face painted with cattle and people.
# ---------------------------------------------------------------------------

ROCK_FRAME = (256, 192)


def _cow(f: K.Frame, x: float, y: float, s: float, colour, patch, facing: float = 1.0) -> None:
    """A painted cow, as the herders painted them: a long body, lyre horns,
    and patches on its hide. `s` is its size; `facing` -1 turns it left."""
    def P(px: float, py: float) -> Point:
        return (x + px * s * facing, y + py * s)

    f.poly([P(-14, -4), P(10, -6), P(14, -2), P(12, 4), P(-12, 5), P(-15, 1)], colour, body=False)
    for lx in (-11.0, -7.0, 7.0, 10.0):
        f.ink([P(lx, 3), P(lx + 0.4, 12)], 1.4 * s, colour)
    f.ink([P(12, -3), P(18, -6), P(20, -2)], 2.4 * s, colour)
    f.ink([P(18, -6), P(16, -12), P(19, -15)], 1.0 * s, colour)
    f.ink([P(18, -6), P(22, -11), P(21, -15)], 1.0 * s, colour)
    f.ink([P(-15, -2), P(-18, 6)], 0.9 * s, colour)
    f.ellipse(*P(-4, -1), 3.0 * s, 2.0 * s, patch, body=False)
    f.ellipse(*P(5, 1), 2.4 * s, 1.6 * s, patch, body=False)


def _person(f: K.Frame, x: float, y: float, s: float, colour, pose: str = "walk") -> None:
    """A painted person: a round head, a long body, thin limbs."""
    f.ellipse(x, y - 16.0 * s, 2.0 * s, 2.0 * s, colour, body=False)
    f.ink([(x, y - 14.0 * s), (x + 1.0 * s, y - 4.0 * s)], 1.6 * s, colour)
    if pose == "dance":
        f.ink([(x, y - 12.0 * s), (x - 6.0 * s, y - 16.0 * s), (x - 8.0 * s, y - 22.0 * s)], 1.0 * s, colour)
        f.ink([(x, y - 12.0 * s), (x + 6.0 * s, y - 15.0 * s), (x + 9.0 * s, y - 20.0 * s)], 1.0 * s, colour)
        f.ink([(x + 1.0 * s, y - 4.0 * s), (x - 5.0 * s, y), (x - 4.0 * s, y + 6.0 * s)], 1.1 * s, colour)
        f.ink([(x + 1.0 * s, y - 4.0 * s), (x + 6.0 * s, y - 1.0 * s), (x + 9.0 * s, y + 4.0 * s)], 1.1 * s, colour)
    else:
        # A herder with a staff, walking.
        f.ink([(x, y - 12.0 * s), (x + 5.0 * s, y - 8.0 * s)], 1.0 * s, colour)
        f.ink([(x + 5.0 * s, y - 20.0 * s), (x + 6.0 * s, y + 6.0 * s)], 0.8 * s, colour)
        f.ink([(x + 1.0 * s, y - 4.0 * s), (x - 3.0 * s, y + 6.0 * s)], 1.1 * s, colour)
        f.ink([(x + 1.0 * s, y - 4.0 * s), (x + 4.0 * s, y + 6.0 * s)], 1.1 * s, colour)


def _draw_rock_art(anim: str, i: int, n: int):
    f = K.Frame(ROCK_FRAME)
    foot = 186.0
    # The rock face: a slab with an overhang at the top, and rubble at its foot.
    face = [(10.0, foot), (8.0, 120.0), (14.0, 60.0), (30.0, 28.0), (70.0, 14.0), (140.0, 10.0), (200.0, 16.0), (238.0, 34.0), (248.0, 80.0),
            (244.0, 140.0), (248.0, foot)]
    f.poly(face, SANDSTONE)
    # The overhang: a darker ledge at the top that shades the paintings.
    f.poly([(14.0, 60.0), (30.0, 28.0), (70.0, 14.0), (140.0, 10.0), (200.0, 16.0), (238.0, 34.0), (246.0, 56.0), (200.0, 44.0), (140.0, 40.0),
            (80.0, 42.0), (30.0, 56.0)], SANDSTONE_LIGHT, body=False)
    f.poly([(30.0, 56.0), (80.0, 42.0), (140.0, 40.0), (200.0, 44.0), (246.0, 56.0), (246.0, 64.0), (200.0, 54.0), (140.0, 50.0), (80.0, 52.0),
            (24.0, 66.0)], SANDSTONE_SHADE, body=False)
    # The layers of the stone and its cracks.
    for y, x0, x1 in ((96.0, 12.0, 70.0), (150.0, 180.0, 246.0), (170.0, 12.0, 120.0)):
        f.ink([(x0, y), ((x0 + x1) / 2.0, y + 3.0), (x1, y - 1.0)], 1.0, SANDSTONE_SHADE)
    f.ink([(220.0, 70.0), (214.0, 96.0), (222.0, 120.0)], 1.2, SANDSTONE_DARK)
    f.poly([(200.0, foot), (206.0, 160.0), (248.0, 150.0), (248.0, foot)], SANDSTONE_SHADE, body=False)
    # The paintings: a herd of cattle, herders and a dancer.
    _cow(f, 60.0, 92.0, 1.5, RED_OCHRE, OCHRE_WHITE)
    _cow(f, 112.0, 104.0, 1.3, OCHRE_WHITE, RED_OCHRE)
    _cow(f, 166.0, 90.0, 1.4, RED_OCHRE, OCHRE_WHITE)
    _cow(f, 92.0, 140.0, 1.2, RED_OCHRE, OCHRE_WHITE, facing=-1.0)
    _cow(f, 148.0, 146.0, 1.1, RED_OCHRE, OCHRE_WHITE)
    _person(f, 196.0, 124.0, 1.3, RED_OCHRE)
    _person(f, 30.0, 140.0, 1.2, RED_OCHRE)
    _person(f, 196.0, 166.0, 1.0, OCHRE_WHITE, "dance")
    # A row of dots: someone counted something.
    for k in range(7):
        f.dot(56.0 + k * 6.0, 70.0, 1.4, RED_OCHRE)
    # Rubble at the foot of the face.
    for x, rx in ((24.0, 12.0), (54.0, 9.0), (226.0, 14.0)):
        f.ellipse(x, foot - 5.0, rx, 6.0, SANDSTONE_SHADE)
    return f.finish(outline=OUTLINE, width=1.6)


# ---------------------------------------------------------------------------
# The reed boat: a platform look.
# ---------------------------------------------------------------------------

REED_BOAT_FRAME = (320, 192)
REED_BOAT_SPAN = (16.0, 304.0)
REED_BOAT_TOP = 150.0


def _draw_reed_boat(anim: str, i: int, n: int):
    t = _phase(i, n)
    cyc = math.tau * t
    f = K.Frame(REED_BOAT_FRAME)
    top = REED_BOAT_TOP
    x0, x1 = REED_BOAT_SPAN
    # The water at its sides: two bands of ripples that move.
    for k in range(6):
        x = 30.0 + ((k * 52.0 + 40.0 * t) % 270.0)
        f.ink([(x, 182.0), (x + 10.0, 180.0), (x + 20.0, 182.0)], 1.6, K.alpha(WATER_LIGHT, 0.9))
    # The mast and the pennant, behind the hull.
    mast = 170.0
    f.limb([(mast, top), (mast, 44.0)], 4.0, BARK)
    flap = math.sin(cyc)
    pennant = [(mast + 1.0, 46.0)]
    for k in range(1, 6):
        u = k / 5.0
        pennant.append((mast + 1.0 + 32.0 * u, 50.0 + 4.0 * u + 4.0 * math.sin(cyc + u * 3.0) * u))
    for k in range(5, 0, -1):
        u = k / 5.0
        pennant.append((mast + 1.0 + 32.0 * u - 2.0 * u, 58.0 + 2.0 * u + 4.0 * math.sin(cyc + u * 3.0) * u))
    pennant.append((mast + 1.0, 60.0))
    f.poly(pennant, RED_OCHRE)
    del flap
    # A little shelter of reed mats on hoops, at the stern half.
    f.poly([(70.0, top), (70.0, 122.0), (82.0, 108.0), (126.0, 108.0), (138.0, 122.0), (138.0, top)], REED_SHADE)
    for k in range(6):
        x = 74.0 + k * 12.0
        f.ink([(x, top - 1.0), (x, 116.0 if 0 < k < 5 else 124.0)], 1.0, REED)
    f.ink([(76.0, 112.0), (132.0, 112.0)], 1.2, ROPE)
    # The hull: bundles of reeds bound tight, rising at each end into a high
    # curl. The top of the middle bundle is the deck.
    hull = [(x0, top), (x1, top), (x1 + 2.0, top + 10.0), (x1 - 12.0, top + 26.0), (x1 - 50.0, top + 34.0), (x0 + 50.0, top + 34.0),
            (x0 + 12.0, top + 26.0), (x0 - 2.0, top + 10.0)]
    f.poly(hull, REED)
    f.poly([(x0 + 12.0, top + 22.0), (x1 - 12.0, top + 22.0), (x1 - 12.0, top + 26.0), (x1 - 50.0, top + 34.0), (x0 + 50.0, top + 34.0),
            (x0 + 12.0, top + 26.0)], REED_SHADE, body=False)
    for y in (top + 7.0, top + 15.0, top + 23.0):
        f.ink([(x0 + 6.0, y), (x1 - 6.0, y)], 1.0, REED_SHADE)
    # The bindings round the bundles.
    for k in range(13):
        x = x0 + 18.0 + k * 21.0
        f.limb([(x, top + 1.0), (x + 1.0, top + 30.0)], 2.6, ROPE)
    # The prow (right) and the stern (left): tapered bundles that rise from
    # the ends of the hull and curl back over the deck.
    for side in (-1.0, 1.0):
        end = x1 if side > 0 else x0
        path = [(-22.0, 6.0), (-4.0, -4.0), (2.0, -30.0), (0.0, -60.0), (-10.0, -82.0), (-24.0, -88.0), (-34.0, -80.0), (-32.0, -70.0)]
        pts = [(end + side * px, top + py) for px, py in path]
        widths = [16.0, 14.0, 12.0, 10.0, 8.0, 6.4, 5.0]
        for k in range(len(pts) - 1):
            f.limb([pts[k], pts[k + 1]], widths[k], REED)
        for k in range(1, 6):
            x, y = pts[k]
            f.ink([(x - 4.0, y), (x + 4.0, y)], 1.8, ROPE)
        f.ink([pts[1], pts[2], pts[3], pts[4]], 1.0, REED_LIGHT)
    # Sun on the reeds.
    f.ink([(x0 + 10.0, top + 3.0), (x1 - 10.0, top + 3.0)], 1.2, REED_LIGHT)
    # A paddle laid on the deck at the stern.
    f.limb([(30.0, top - 2.0), (64.0, top - 6.0)], 2.4, BARK)
    f.ellipse(28.0, top - 2.0, 6.0, 3.0, BARK)
    return f.finish(outline=OUTLINE, width=1.6)


# ---------------------------------------------------------------------------
# The stele of Aksum: a granite tower of false windows.
# ---------------------------------------------------------------------------

STELE_FRAME = (96, 448)


def _draw_stele(anim: str, i: int, n: int):
    f = K.Frame(STELE_FRAME)
    foot = 442.0
    x0, x1 = 22.0, 74.0
    top = 26.0
    # The base platform of stone.
    f.poly(_rect(8.0, foot - 16.0, 88.0, foot), GRANITE_SHADE)
    f.poly(_rect(8.0, foot - 16.0, 88.0, foot - 12.0), GRANITE_LIGHT, body=False)
    # The shaft: a little narrower at the top, with a round head.
    head = [(x0 + 2.0, top + 18.0)]
    for k in range(13):
        a = math.pi + math.pi * k / 12.0
        head.append((48.0 + 24.0 * math.cos(a), top + 18.0 + 18.0 * math.sin(a)))
    shaft = [(x0, foot - 16.0), (x1, foot - 16.0), (x1 - 2.0, top + 18.0)] + head[::-1][:-1] + [(x0 + 2.0, top + 18.0)]
    f.poly(shaft, GRANITE)
    f.poly([(60.0, foot - 16.0), (x1, foot - 16.0), (x1 - 2.0, top + 18.0), (62.0, top + 10.0), (58.0, top + 18.0)], GRANITE_SHADE, body=False)
    # The false door at the foot, with its lock and its beam ends.
    f.poly(_rect(36.0, foot - 74.0, 60.0, foot - 18.0), GRANITE_DARK, body=False)
    f.poly(_rect(38.0, foot - 72.0, 58.0, foot - 20.0), GRANITE_SHADE, body=False)
    f.dot(54.0, foot - 46.0, 2.0, GRANITE_LIGHT)
    # The storeys: a band of beam ends ("monkey heads"), then a row of false windows.
    y = foot - 84.0
    storey = 0
    while y > top + 46.0:
        f.limb([(x0 + 1.0, y), (x1 - 1.0, y)], 3.0, GRANITE_LIGHT, body=False)
        for k in range(4):
            f.ellipse(x0 + 8.0 + k * 12.0, y + 4.0, 2.4, 2.2, GRANITE_SHADE, body=False)
        wy = y - 26.0
        for k in range(2 if storey % 2 else 3):
            nwin = 2 if storey % 2 else 3
            wx = x0 + 6.0 + k * ((x1 - x0 - 12.0) / nwin) + 2.0
            ww = (x1 - x0 - 12.0) / nwin - 4.0
            f.poly(_rect(wx, wy, wx + ww, wy + 18.0), GRANITE_DARK, body=False)
            f.ink([(wx + ww / 2.0, wy + 1.0), (wx + ww / 2.0, wy + 17.0)], 1.0, GRANITE)
            f.ink([(wx + 1.0, wy + 9.0), (wx + ww - 1.0, wy + 9.0)], 1.0, GRANITE)
        y -= 40.0
        storey += 1
    # The round head with its two holes, where a plaque once hung.
    f.ellipse(48.0, top + 16.0, 12.0, 8.0, GRANITE_SHADE, body=False)
    f.dot(42.0, top + 16.0, 2.0, GRANITE_DARK)
    f.dot(54.0, top + 16.0, 2.0, GRANITE_DARK)
    f.ink([(x0 + 4.0, top + 22.0), (x0 + 4.0, foot - 20.0)], 1.2, GRANITE_LIGHT)
    return f.finish(outline=OUTLINE, width=1.6)


# ---------------------------------------------------------------------------
# The Laetoli footprints: two trails in a slab of volcanic ash.
# ---------------------------------------------------------------------------

LAETOLI_FRAME = (256, 48)


def _foot(f: K.Frame, x: float, y: float, s: float) -> None:
    """One footprint seen from a little above, toes to the right: a heel,
    a narrow arch, the ball of the foot and a big toe in line with the rest."""
    dark = K.shade(ASH_SHADE, 0.72)
    sole = [(x - 7.0 * s, y), (x - 5.0 * s, y - 2.6 * s), (x + 1.0 * s, y - 2.2 * s), (x + 6.0 * s, y - 3.4 * s), (x + 8.0 * s, y - 1.0 * s),
            (x + 7.0 * s, y + 2.4 * s), (x + 1.0 * s, y + 1.6 * s), (x - 5.0 * s, y + 2.6 * s)]
    f.poly(sole, dark, body=False)
    f.poly([(x - 6.0 * s, y - 0.6 * s), (x - 4.0 * s, y - 2.0 * s), (x + 6.0 * s, y - 2.6 * s), (x + 7.0 * s, y - 1.0 * s)],
           K.shade(dark, 0.8), body=False)
    for k in range(4):
        f.dot(x + 10.0 * s - k * 0.3 * s, y - 2.6 * s + k * 1.6 * s, (1.5 - 0.22 * k) * s, dark)


def _draw_laetoli(anim: str, i: int, n: int):
    f = K.Frame(LAETOLI_FRAME)
    # The slab: a flat lens of grey ash, its front edge broken.
    slab = [(8.0, 30.0), (20.0, 16.0), (120.0, 10.0), (236.0, 14.0), (248.0, 28.0), (240.0, 40.0), (180.0, 42.0), (120.0, 40.0), (60.0, 42.0),
            (14.0, 40.0)]
    f.poly(slab, ASH)
    f.poly([(8.0, 30.0), (248.0, 28.0), (240.0, 40.0), (180.0, 42.0), (120.0, 40.0), (60.0, 42.0), (14.0, 40.0)], ASH_SHADE, body=False)
    f.ink([(8.0, 30.0), (60.0, 31.0), (120.0, 30.0), (190.0, 31.0), (248.0, 28.0)], 1.0, K.shade(ASH_SHADE, 0.85))
    f.poly([(24.0, 18.0), (120.0, 12.0), (230.0, 16.0), (120.0, 16.0)], ASH_LIGHT, body=False)
    # Two trails side by side: a larger walker behind, a smaller one in front.
    for k in range(5):
        _foot(f, 30.0 + k * 44.0, 19.0 + (1.6 if k % 2 else 0.0), 1.15)
        _foot(f, 46.0 + k * 40.0, 27.0 + (1.4 if k % 2 else 0.0), 0.9)
    # Raindrop pits and the prints of a hare, in the same ash.
    rng = random.Random("history_laetoli_footprints")
    for _ in range(18):
        f.dot(rng.uniform(20.0, 236.0), rng.uniform(15.0, 28.0), 0.6, K.shade(ASH_SHADE, 0.9))
    for k in range(3):
        f.dot(226.0 + k * 4.0, 20.0 + (k % 2) * 2.0, 0.9, K.shade(ASH_SHADE, 0.8))
    return f.finish(outline=OUTLINE, width=1.4)


# ---------------------------------------------------------------------------
# Publication.
# ---------------------------------------------------------------------------

SCENERY = ["prop", "scenery", "history", "africa"]
DOOR = ["prop", "door", "lock", "history", "africa"]

FRAMES: Dict[str, Tuple[int, int]] = {
    "history_thorn_boma": BOMA_FRAME,
    "history_campfire": CAMPFIRE_FRAME,
    "history_acacia": ACACIA_FRAME,
    "history_rock_art": ROCK_FRAME,
    "history_reed_boat": REED_BOAT_FRAME,
    "history_aksum_stele": STELE_FRAME,
    "history_laetoli_footprints": LAETOLI_FRAME,
}
DRAW: Dict[str, Callable] = {
    "history_thorn_boma": _draw_boma,
    "history_campfire": _draw_campfire,
    "history_acacia": _draw_acacia,
    "history_rock_art": _draw_rock_art,
    "history_reed_boat": _draw_reed_boat,
    "history_aksum_stele": _draw_stele,
    "history_laetoli_footprints": _draw_laetoli,
}

TARGETS: Dict[str, dict] = {
    "history_thorn_boma": _publisher("history_thorn_boma", "Thorn Boma", STILL, BOMA_FRAME, _draw_boma, {"foot": (48.0, 384.0)}, "Door", DOOR,
                                     forward=(0.0, -1.0)),
    "history_campfire": _publisher("history_campfire", "Campfire", LOOP, CAMPFIRE_FRAME, _draw_campfire, {"foot": (64.0, 128.0)}, "Scenery", SCENERY),
    "history_acacia": _publisher("history_acacia", "Acacia", STILL, ACACIA_FRAME, _draw_acacia, {"foot": (178.0, 384.0)}, "Scenery", SCENERY),
    "history_rock_art": _publisher("history_rock_art", "Rock Art", STILL, ROCK_FRAME, _draw_rock_art, {"foot": (128.0, 192.0)}, "Scenery", SCENERY),
    "history_reed_boat": _publisher("history_reed_boat", "Reed Boat", LOOP, REED_BOAT_FRAME, _draw_reed_boat,
                                    {"top": ((REED_BOAT_SPAN[0] + REED_BOAT_SPAN[1]) / 2.0, REED_BOAT_TOP)}, "Scenery",
                                    ["prop", "platform", "history", "africa"]),
    "history_aksum_stele": _publisher("history_aksum_stele", "Aksum Stele", STILL, STELE_FRAME, _draw_stele, {"foot": (48.0, 448.0)}, "Scenery",
                                      SCENERY),
    "history_laetoli_footprints": _publisher("history_laetoli_footprints", "Laetoli Footprints", STILL, LAETOLI_FRAME, _draw_laetoli,
                                             {"foot": (128.0, 48.0)}, "Scenery", SCENERY),
}
