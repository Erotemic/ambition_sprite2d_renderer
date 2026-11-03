"""The props of the Mongol Steppe of the History dimension (biome `history_steppe`).

Grass to the end of the world under an enormous sky, felt gers with smoke,
and at the west end the Great Wall. The props are drawn in the cel style of
the Art dimension's cast (`targets/characters/_art_cast_kit.py`) in the
warm sepia of an old textbook, with the colours of the steppe: steppe green
and gold, sky blue, felt white and saddle red.

- ``history_ger``: scenery. A felt ger with a painted orange door, rope
  bands round its wall, and a stove pipe through its crown. Its ``idle``
  row lets smoke rise from the pipe.
- ``history_great_wall_gate``: the look of a `LockWall` of 32 by 128 world
  units, drawn at 3 to 1 (as ``art_colour_gate_*``). A heavy wooden door
  studded with iron, in a stone arch of the Wall. Genghis Can opens it.
- ``history_scaffold_plank``: the look of a `LockWall` of 160 by 24 world
  units, drawn at 2 to 1 (as ``art_bridge_planks``). A plank on a frame of
  bamboo poles, tied with rope. Genghis Can't builds it.
- ``history_great_wall``: scenery. A stretch of the Wall that steps over a
  hill, and a watchtower with a red pennant.
- ``history_ovoo``: scenery. A cairn of stones with a pole, branches and
  blue silk scarves. Its ``idle`` row moves the scarves in the wind.
- ``history_horse_standard``: scenery. A tug: a pole with a trident at its
  top and a plume of horse tail under it. Its ``idle`` row sways the plume.

Animations: ``idle``. No drop shadows: the game draws them. The numbers are
frame pixels; the game shows each prop at half its frame (the gate at a
third).
"""

from __future__ import annotations

import math
import random
from typing import Dict, List, Tuple

from ..characters import _art_cast_kit as K
from .art_props import STILL, _publisher

Point = Tuple[float, float]
LOOP: List[Tuple[str, int, int]] = [("idle", 8, 120)]

#: The outline: the dark sepia of old ink.
OUTLINE = (54, 36, 26, 255)
FELT = (242, 234, 214, 255)
FELT_SHADE = (204, 190, 162, 255)
SADDLE_RED = (178, 54, 40, 255)
SADDLE_RED_DARK = (120, 32, 26, 255)
DOOR_ORANGE = (236, 130, 40, 255)
DOOR_ORANGE_DARK = (178, 84, 24, 255)
SKY_BLUE = (78, 150, 222, 255)
SKY_BLUE_LIGHT = (156, 206, 244, 255)
SKY_BLUE_DARK = (44, 96, 164, 255)
STEPPE_GREEN = (112, 152, 66, 255)
STEPPE_GREEN_DARK = (72, 106, 44, 255)
STEPPE_GOLD = (214, 178, 84, 255)
STONE = (196, 182, 156, 255)
STONE_LIGHT = (222, 210, 186, 255)
STONE_SHADE = (148, 134, 112, 255)
STONE_DARK = (98, 86, 72, 255)
IRON = (74, 70, 80, 255)
IRON_LIGHT = (140, 136, 150, 255)
ROPE = (206, 176, 118, 255)
ROPE_DARK = (122, 92, 58, 255)
BAMBOO = (204, 184, 98, 255)
BAMBOO_LIGHT = (234, 220, 150, 255)
BAMBOO_SHADE = (150, 128, 58, 255)
SMOKE = (178, 172, 168, 255)
HAIR = (58, 46, 42, 255)
HAIR_LIGHT = (116, 98, 86, 255)


def _phase(i: int, n: int) -> float:
    return i / float(max(1, n))


def _rect(x0: float, y0: float, x1: float, y1: float) -> List[Point]:
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


# ---------------------------------------------------------------------------
# The ger: a round felt tent with an orange door.
# ---------------------------------------------------------------------------

GER_FRAME = (320, 256)
GER_FOOT = 250.0


def _draw_ger(anim: str, i: int, n: int):
    t = _phase(i, n)
    f = K.Frame(GER_FRAME)
    foot = GER_FOOT
    # The smoke from the stove pipe, behind the roof: puffs that rise, grow and fade.
    for k in range(4):
        u = (t + k / 4.0) % 1.0
        x = 174.0 + 12.0 * u + 4.0 * math.sin(u * math.pi * 2.0 + k)
        y = 62.0 - 40.0 * u
        r = 4.0 + 7.0 * u
        f.ellipse(x, y, r, r * 0.85, K.alpha(SMOKE, 0.8 * (1.0 - u)), body=False)
    # The stove pipe, through the crown.
    f.poly(_rect(168.0, 66.0, 177.0, 100.0), IRON)
    f.poly(_rect(166.0, 63.0, 179.0, 68.0), IRON)
    f.ink([(170.0, 70.0), (170.0, 98.0)], 1.0, IRON_LIGHT)
    # The wall: felt over the lattice.
    wall = [(34.0, 152.0), (286.0, 152.0), (289.0, foot), (31.0, foot)]
    f.poly(wall, FELT)
    f.poly([(232.0, 152.0), (286.0, 152.0), (289.0, foot), (234.0, foot)], FELT_SHADE, body=False)
    # The skirt of the felt at the foot, a little darker.
    f.poly([(31.5, foot - 9.0), (288.5, foot - 9.0), (289.0, foot), (31.0, foot)], K.shade(FELT_SHADE, 0.92), body=False)
    # The painted band under the eave: red, with a gold key pattern.
    f.poly([(34.0, 152.0), (286.0, 152.0), (286.4, 164.0), (33.6, 164.0)], SADDLE_RED, body=False)
    for k in range(21):
        x = 40.0 + k * 12.0
        f.ink([(x, 161.0), (x, 155.0), (x + 6.0, 155.0), (x + 6.0, 159.0), (x + 3.0, 159.0)], 1.2, STEPPE_GOLD)
    # The rope bands of horse hair round the wall.
    for y in (186.0, 224.0):
        f.limb([(33.0, y), (287.0, y)], 3.0, ROPE_DARK, body=False)
        for k in range(16):
            x = 40.0 + k * 16.0
            f.ink([(x, y - 1.0), (x + 4.0, y + 1.0)], 0.8, ROPE)
    # The roof: a low cone of felt to the crown ring.
    roof = [(22.0, 158.0), (298.0, 158.0), (190.0, 98.0), (130.0, 98.0)]
    f.poly(roof, FELT)
    f.poly([(214.0, 158.0), (298.0, 158.0), (190.0, 98.0), (178.0, 98.0)], FELT_SHADE, body=False)
    # The ropes that hold the roof felt down, from the crown to the eave.
    for k in range(9):
        u = k / 8.0
        f.ink([(134.0 + 52.0 * u, 100.0), (30.0 + 260.0 * u, 156.0)], 1.1, K.alpha(ROPE_DARK, 0.8))
    # The edge of the roof felt over the wall.
    f.limb([(22.0, 158.0), (298.0, 158.0)], 3.0, FELT_SHADE)
    # The crown ring (toono), in wood, and the cover rolled back from it.
    f.ellipse(160.0, 98.0, 31.0, 6.0, K.WOOD)
    f.ellipse(160.0, 97.0, 24.0, 3.6, K.WOOD_DARK, body=False)
    for k in range(5):
        x = 142.0 + k * 9.0
        f.ink([(x, 95.0), (x + 2.0, 99.0)], 1.0, K.WOOD)
    f.poly(_rect(168.0, 92.0, 177.0, 100.0), IRON)
    # The door frame, the orange door and its painted knot.
    f.poly(_rect(136.0, 180.0, 184.0, foot), K.WOOD_DARK)
    f.poly(_rect(141.0, 186.0, 179.0, foot), DOOR_ORANGE)
    f.poly(_rect(160.0, 186.0, 179.0, foot), DOOR_ORANGE_DARK, body=False)
    f.ink([(160.0, 186.0), (160.0, foot)], 1.4, OUTLINE)
    for x0, x1 in ((144.0, 157.0), (163.0, 176.0)):
        f.ink([(x0, 190.0), (x1, 190.0), (x1, foot - 4.0), (x0, foot - 4.0), (x0, 190.0)], 1.2, SADDLE_RED_DARK)
        cx, cy = (x0 + x1) / 2.0, 214.0
        diamond = [(cx, cy - 7.0), (cx + 5.0, cy), (cx, cy + 7.0), (cx - 5.0, cy), (cx, cy - 7.0)]
        f.ink(diamond, 1.4, STEPPE_GOLD)
        f.ink([(cx - 3.0, cy - 3.0), (cx + 3.0, cy + 3.0)], 1.0, STEPPE_GOLD)
        f.ink([(cx + 3.0, cy - 3.0), (cx - 3.0, cy + 3.0)], 1.0, STEPPE_GOLD)
    # The felt flap over the door, rolled up and tied.
    f.limb([(132.0, 180.0), (188.0, 180.0)], 7.0, FELT_SHADE)
    for x in (140.0, 180.0):
        f.ink([(x, 176.0), (x + 1.0, 184.0)], 1.4, ROPE_DARK)
    # The wooden sill.
    f.poly(_rect(132.0, foot - 4.0, 188.0, foot), K.WOOD)
    return f.finish(outline=OUTLINE, width=1.6)


# ---------------------------------------------------------------------------
# The gate in the Wall: a door studded with iron, in a stone arch.
# ---------------------------------------------------------------------------

GATE_FRAME = (96, 384)
#: The arch: its centre and its radius, in frame pixels.
GATE_ARCH = (48.0, 96.0, 32.0)


def _arch(cx: float, cy: float, r: float, foot: float, count: int = 20) -> List[Point]:
    """An opening with a round top: up one side, over, and down the other."""
    pts = [(cx - r, foot)]
    for k in range(count + 1):
        a = math.pi + math.pi * k / count
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    pts.append((cx + r, foot))
    return pts


def _draw_wall_gate(anim: str, i: int, n: int):
    w, h = GATE_FRAME
    m = 4.0
    foot = h - m
    cx, cy, r = GATE_ARCH
    f = K.Frame(GATE_FRAME)
    # The stone of the Wall, from the top of the box to its foot.
    f.poly(_rect(m, m, w - m, foot), STONE)
    f.poly(_rect(w - 16.0, m, w - m, foot), STONE_SHADE, body=False)
    # The parapet at the top, with its crenels.
    f.poly(_rect(m, m, w - m, 24.0), STONE_SHADE, body=False)
    for x in (16.0, 42.0, 68.0):
        f.poly(_rect(x, m + 3.0, x + 12.0, 16.0), STONE_DARK, body=False)
    f.limb([(m + 1.0, 25.0), (w - m - 1.0, 25.0)], 2.4, STONE_LIGHT, body=False)
    # The courses of stone on each side of the arch.
    rng = random.Random("history_great_wall_gate")
    for row, y in enumerate(range(40, int(foot), 16)):
        f.ink([(m, float(y)), (w - m, float(y))], 1.0, K.alpha(STONE_DARK, 0.7))
        off = 0.0 if row % 2 else 6.0
        for x in (8.0 + off, w - 12.0 - off):
            f.ink([(x, float(y)), (x, min(foot - 2.0, float(y) + 16.0))], 1.0, K.alpha(STONE_DARK, 0.6))
        if rng.random() < 0.3:
            f.ink([(m + 2.0, y + 8.0), (m + 6.0, y + 6.0)], 0.8, K.alpha(STONE_DARK, 0.5))
    # The voussoirs of the arch: a ring of light stone with its joints.
    f.poly(_arch(cx, cy, r + 9.0, cy, 24), STONE_LIGHT, body=False)
    for k in range(9):
        a = math.pi + math.pi * (k + 0.5) / 9.0
        f.ink([(cx + r * math.cos(a), cy + r * math.sin(a)), (cx + (r + 9.0) * math.cos(a), cy + (r + 9.0) * math.sin(a))], 1.2, STONE_DARK)
    f.ink([(cx - 6.0, cy - r - 9.0), (cx - 6.0, cy - r), (cx + 6.0, cy - r), (cx + 6.0, cy - r - 9.0)], 1.2, STONE_DARK)
    # The door: two leaves of thick planks in the arch.
    door = _arch(cx, cy, r, foot)
    f.poly(door, K.WOOD_DARK, body=False)
    f.poly(_arch(cx, cy, r - 3.0, foot), K.WOOD, body=False)
    f.poly([(cx + 12.0, foot), (cx + r - 3.0, foot), (cx + r - 3.0, cy), (cx + 12.0, cy - r + 6.0)], K.shade(K.WOOD, 0.88), body=False)
    for x in (cx - 20.0, cx - 10.0, cx + 10.0, cx + 20.0):
        top = cy - math.sqrt(max(0.0, (r - 3.0) ** 2 - (x - cx) ** 2))
        f.ink([(x, top + 1.0), (x, foot)], 1.0, K.alpha(K.WOOD_DARK, 0.9))
    f.ink([(cx, cy - r + 3.0), (cx, foot)], 2.0, OUTLINE)
    # The iron bands across the leaves, and the rows of iron studs.
    for y in (124.0, 206.0, 290.0, 354.0):
        f.limb([(cx - r + 4.0, y), (cx + r - 4.0, y)], 5.0, IRON, body=False)
        f.ink([(cx - r + 5.0, y - 1.6), (cx + r - 5.0, y - 1.6)], 0.8, IRON_LIGHT)
    for y in range(140, int(foot) - 8, 18):
        if any(abs(y - b) < 9 for b in (206, 290, 354)):
            continue
        for x in (cx - 22.0, cx - 11.0, cx + 11.0, cx + 22.0):
            f.dot(x, float(y), 2.3, IRON)
            f.dot(x - 0.6, y - 0.7, 0.8, IRON_LIGHT)
    # Two iron rings to pull it by.
    for x in (cx - 6.0, cx + 6.0):
        f.dot(x, 236.0, 3.0, IRON)
        f.ink(K.ellipse_points(x, 244.0, 4.6, 6.0, 18) + [K.ellipse_points(x, 244.0, 4.6, 6.0, 18)[0]], 1.8, IRON)
    return f.finish(outline=OUTLINE, width=1.6)


# ---------------------------------------------------------------------------
# The scaffold: a plank on a frame of bamboo.
# ---------------------------------------------------------------------------

SCAFFOLD_FRAME = (320, 48)


def _bamboo(f: K.Frame, x0: float, x1: float, y: float, width: float, rng: random.Random) -> None:
    """A bamboo pole that lies flat, with its nodes and cut ends."""
    f.limb([(x0, y), (x1, y)], width, BAMBOO)
    f.ink([(x0 + 2.0, y - width * 0.22), (x1 - 2.0, y - width * 0.22)], 1.0, BAMBOO_LIGHT)
    f.ink([(x0 + 2.0, y + width * 0.28), (x1 - 2.0, y + width * 0.28)], 1.0, BAMBOO_SHADE)
    x = x0 + rng.uniform(18.0, 30.0)
    while x < x1 - 10.0:
        f.ink([(x, y - width / 2.0 + 0.6), (x, y + width / 2.0 - 0.6)], 1.6, BAMBOO_SHADE)
        x += rng.uniform(38.0, 50.0)
    for x in (x0, x1):
        f.ellipse(x, y, width * 0.32, width * 0.5, BAMBOO_LIGHT, body=False)
        f.ellipse(x, y, width * 0.16, width * 0.28, BAMBOO_SHADE, body=False)


def _lashing(f: K.Frame, x: float, y: float) -> None:
    """A tie of rope where two poles cross."""
    f.ellipse(x, y, 4.2, 4.2, ROPE)
    for d in (-2.0, 0.0, 2.0):
        f.ink([(x - 3.2 + d, y - 3.4), (x - 1.2 + d, y + 3.4)], 0.9, ROPE_DARK)


def _draw_scaffold(anim: str, i: int, n: int):
    w, h = SCAFFOLD_FRAME
    f = K.Frame(SCAFFOLD_FRAME)
    rng = random.Random("history_scaffold_plank")
    top_y, low_y = 20.0, 38.0
    posts = (28.0, 110.0, 210.0, 292.0)
    # The braces, then the posts between the two poles.
    for a, b in ((posts[0], posts[1]), (posts[2], posts[3])):
        f.limb([(a, low_y), (b, top_y)], 4.0, BAMBOO_SHADE)
    f.limb([(posts[1], low_y), (posts[2], top_y)], 4.0, BAMBOO_SHADE)
    for x in posts:
        f.limb([(x, top_y), (x, low_y)], 5.0, BAMBOO)
        f.ink([(x - 1.0, top_y + 2.0), (x - 1.0, low_y - 2.0)], 0.8, BAMBOO_LIGHT)
    _bamboo(f, 13.0, 307.0, low_y, 7.0, rng)
    _bamboo(f, 12.0, 308.0, top_y, 8.0, rng)
    # The plank laid on the top pole: the part that is walked on.
    f.poly(_rect(14.0, 6.0, 306.0, 15.0), K.WOOD)
    f.poly(_rect(14.0, 12.0, 306.0, 15.0), K.WOOD_DARK, body=False)
    f.ink([(16.0, 7.4), (304.0, 7.4)], 1.0, K.shade(K.WOOD, 1.3))
    for x in (92.0, 170.0, 236.0):
        f.ink([(x, 6.5), (x, 14.5)], 1.0, K.WOOD_DARK)
    # The lashings: where the plank, the poles and the posts meet.
    for x in posts:
        _lashing(f, x, top_y)
        _lashing(f, x, low_y)
        f.ink([(x - 3.0, 13.0), (x + 3.0, 22.0)], 1.2, ROPE_DARK)
    return f.finish(outline=OUTLINE, width=1.4)


# ---------------------------------------------------------------------------
# The Great Wall: a stretch over a hill and a watchtower.
# ---------------------------------------------------------------------------

WALL_FRAME = (512, 384)
WALL_FOOT = 378.0


TILE = (78, 102, 96, 255)
TILE_DARK = (50, 66, 64, 255)
PILLAR_RED = (172, 50, 38, 255)


def _lerp(a: Point, b: Point, u: float) -> Point:
    return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)


def _wall_run(f: K.Frame, a: Point, b: Point, foot: float, rng: random.Random) -> None:
    """A run of the Wall whose walk climbs from `a` to `b`: its face, its
    courses of brick that follow the slope, and its merlons."""
    (x0, y0), (x1, y1) = a, b

    def top(x: float) -> float:
        return y0 + (y1 - y0) * (x - x0) / (x1 - x0)

    x = x0 + 2.0
    while x + 12.0 <= x1 - 1.0:
        ya, yb = top(x), top(x + 12.0)
        f.poly([(x, ya - 14.0), (x + 12.0, yb - 14.0), (x + 12.0, yb + 1.0), (x, ya + 1.0)], STONE)
        f.poly([(x + 8.0, top(x + 8.0) - 14.0), (x + 12.0, yb - 14.0), (x + 12.0, yb + 1.0), (x + 8.0, top(x + 8.0) + 1.0)], STONE_SHADE, body=False)
        x += 22.0
    f.poly([(x0, y0), (x1, y1), (x1, foot), (x0, foot)], STONE)
    # The shade under the coping, and the coping itself.
    f.poly([(x0, y0 + 4.0), (x1, y1 + 4.0), (x1, y1 + 12.0), (x0, y0 + 12.0)], STONE_SHADE, body=False)
    f.limb([(x0 + 1.0, y0 + 2.0), (x1 - 1.0, y1 + 2.0)], 3.0, STONE_LIGHT, body=False)
    # The courses follow the slope of the walk, down to the foot.
    low = foot - 4.0
    for row in range(1, 30):
        d = 12.0 + row * 14.0
        p, q = (x0 + 1.0, top(x0 + 1.0) + d), (x1 - 1.0, top(x1 - 1.0) + d)
        if p[1] > low and q[1] > low:
            break
        if p[1] > low:
            p = _lerp(p, q, (p[1] - low) / (p[1] - q[1]))
        if q[1] > low:
            q = _lerp(q, p, (q[1] - low) / (q[1] - p[1]))
        f.ink([p, q], 0.9, K.alpha(STONE_DARK, 0.55))
        xx = x0 + (14.0 if row % 2 else 4.0)
        while xx < x1 - 6.0:
            y = top(xx) + d
            if y + 14.0 < low and rng.random() < 0.55:
                f.ink([(xx, y), (xx, y + 14.0)], 0.8, K.alpha(STONE_DARK, 0.45))
            xx += 22.0


def _draw_great_wall(anim: str, i: int, n: int):
    f = K.Frame(WALL_FRAME)
    rng = random.Random("history_great_wall")
    foot = WALL_FOOT
    # The runs of the Wall: up the hill to the tower, and down the far side.
    _wall_run(f, (8.0, 268.0), (300.0, 196.0), foot, rng)
    _wall_run(f, (440.0, 204.0), (504.0, 236.0), foot, rng)
    # The watchtower: a pavilion with a tiled roof on a tower of brick.
    for x in (338.0, 402.0):
        f.limb([(x, 112.0), (x, 74.0)], 5.0, PILLAR_RED)
    f.poly(_rect(334.0, 70.0, 406.0, 78.0), K.WOOD_DARK)
    roof = [(310.0, 62.0), (322.0, 72.0), (418.0, 72.0), (430.0, 62.0), (412.0, 64.0), (392.0, 44.0), (348.0, 44.0), (328.0, 64.0)]
    f.poly(roof, TILE)
    f.poly([(322.0, 72.0), (418.0, 72.0), (430.0, 62.0), (412.0, 64.0), (328.0, 64.0), (310.0, 62.0)], TILE_DARK, body=False)
    for k in range(7):
        x = 352.0 + k * 6.0
        f.ink([(x, 46.0), (x - 14.0 + k * 4.6, 64.0)], 0.9, TILE_DARK)
    f.limb([(346.0, 44.0), (394.0, 44.0)], 3.0, TILE_DARK)
    # The pennant on its pole, over the ridge.
    f.limb([(370.0, 44.0), (370.0, 16.0)], 2.6, K.WOOD_DARK)
    f.poly([(371.0, 17.0), (408.0, 25.0), (371.0, 35.0)], SADDLE_RED)
    f.poly([(371.0, 28.0), (408.0, 25.0), (371.0, 35.0)], SADDLE_RED_DARK, body=False)
    f.dot(370.0, 15.0, 2.2, STEPPE_GOLD)
    tower = [(296.0, foot), (444.0, foot), (438.0, 110.0), (302.0, 110.0)]
    f.poly(tower, STONE)
    f.poly([(408.0, foot), (444.0, foot), (438.0, 110.0), (404.0, 110.0)], STONE_SHADE, body=False)
    x = 302.0
    while x + 14.0 <= 438.0:
        f.poly(_rect(x, 96.0, x + 14.0, 111.0), STONE)
        f.poly(_rect(x + 10.0, 96.0, x + 14.0, 111.0), STONE_SHADE, body=False)
        x += 24.0
    f.poly(_rect(302.0, 114.0, 438.0, 122.0), STONE_SHADE, body=False)
    f.limb([(301.0, 112.0), (439.0, 112.0)], 3.0, STONE_LIGHT, body=False)
    for row, y in enumerate(range(136, int(foot) - 4, 14)):
        f.ink([(300.0, float(y)), (441.0, float(y))], 0.9, K.alpha(STONE_DARK, 0.55))
        xx = 306.0 + (12.0 if row % 2 else 0.0)
        while xx < 436.0:
            if rng.random() < 0.5:
                f.ink([(xx, float(y)), (xx, float(y) + 14.0)], 0.8, K.alpha(STONE_DARK, 0.45))
            xx += 24.0
    # Its arched windows, and the arched door at the level of the walk.
    for wx, wy, ww, wh in ((326.0, 140.0, 18.0, 34.0), (361.0, 140.0, 18.0, 34.0), (396.0, 140.0, 18.0, 34.0), (355.0, 200.0, 30.0, 52.0)):
        cx = wx + ww / 2.0
        hole = _arch(cx, wy + ww / 2.0, ww / 2.0, wy + wh, 12)
        f.poly(K.grow(hole, 3.0), STONE_LIGHT, body=False)
        f.poly(hole, STONE_DARK, body=False)
    # The ridge of grass the Wall runs on, and tufts on it.
    ridge = [(6.0, foot - 10.0), (150.0, foot - 30.0), (300.0, foot - 50.0), (440.0, foot - 44.0), (506.0, foot - 16.0)]
    f.poly([(6.0, foot), (506.0, foot)] + ridge[::-1], STEPPE_GREEN)
    f.poly([(6.0, foot), (506.0, foot), (506.0, foot - 5.0), (6.0, foot - 5.0)], STEPPE_GREEN_DARK, body=False)
    for k in range(25):
        x = 16.0 + k * 19.5 + rng.uniform(-4.0, 4.0)
        seg = 0
        while seg < len(ridge) - 2 and ridge[seg + 1][0] < x:
            seg += 1
        a, b = ridge[seg], ridge[seg + 1]
        y = a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0]) + 6.0 + rng.uniform(0.0, 4.0)
        for d in (-3.0, 0.0, 3.0):
            f.ink([(x, y + 4.0), (x + d * 1.4, y - 6.0 + abs(d))], 1.2, STEPPE_GREEN_DARK if d else STEPPE_GOLD)
    return f.finish(outline=OUTLINE, width=1.8)


# ---------------------------------------------------------------------------
# The ovoo: a cairn of stones with blue scarves.
# ---------------------------------------------------------------------------

OVOO_FRAME = (128, 192)
OVOO_FOOT = 188.0


def _scarf(f: K.Frame, x: float, y: float, length: float, colour: K.RGBA, t: float, seed: float) -> None:
    """A silk scarf knotted at (x, y), its tail out in the wind."""
    top, low = [], []
    for k in range(9):
        s = k / 8.0
        wave = 4.0 * s * math.sin(math.tau * (t - s * 0.8) + seed)
        cx = x + length * s
        cy = y + 6.0 * s * s + wave
        half = 4.6 * (1.0 - 0.55 * s)
        top.append((cx, cy - half))
        low.append((cx, cy + half))
    f.poly(top + low[::-1], colour)
    f.ink([(p[0], p[1] + 2.0) for p in top[1:]], 0.8, K.shade(colour, 0.75))
    f.ellipse(x, y, 3.2, 3.6, colour)


def _draw_ovoo(anim: str, i: int, n: int):
    t = _phase(i, n)
    f = K.Frame(OVOO_FRAME)
    rng = random.Random("history_ovoo")
    foot = OVOO_FOOT
    # The pole and the two branches, stuck in the top of the cairn.
    f.limb([(64.0, 130.0), (64.0, 22.0)], 4.5, K.WOOD)
    f.ink([(63.0, 128.0), (63.0, 24.0)], 0.9, K.shade(K.WOOD, 1.3))
    for a, b in (((56.0, 132.0), (34.0, 74.0)), ((72.0, 132.0), (96.0, 80.0))):
        f.limb([a, ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0 - 2.0), b], 3.0, K.WOOD_DARK)
    # The trident at the top of the pole.
    f.poly([(61.0, 24.0), (67.0, 24.0), (64.0, 6.0)], STEPPE_GOLD)
    f.limb([(56.0, 24.0), (72.0, 24.0)], 2.4, STEPPE_GOLD)
    for side in (-1.0, 1.0):
        f.limb([(64.0 + side * 8.0, 24.0), (64.0 + side * 9.0, 13.0)], 2.2, STEPPE_GOLD)
    # The cords from the pole to the branches, with small scarves on them.
    for tip in ((34.0, 74.0), (96.0, 80.0)):
        f.ink([(64.0, 34.0), tip], 0.9, ROPE_DARK)
        for k in range(1, 4):
            u = k / 4.0
            px, py = 64.0 + (tip[0] - 64.0) * u, 34.0 + (tip[1] - 34.0) * u
            sway = 1.6 * math.sin(math.tau * t + k + tip[0])
            colour = (SKY_BLUE, FELT, SKY_BLUE_LIGHT)[k - 1]
            f.poly([(px - 3.0, py), (px + 3.0, py), (px + 3.0 + sway, py + 9.0), (px - 3.0 + sway, py + 9.0)], colour)
    # The cairn: a heap of stones, the big ones at the foot.
    rows = [(foot - 11.0, 6, 11.0, 20.0, 108.0), (foot - 28.0, 5, 10.0, 26.0, 102.0), (foot - 44.0, 4, 9.0, 36.0, 92.0),
            (foot - 58.0, 3, 8.0, 46.0, 82.0)]
    for y, count, r, x0, x1 in rows:
        for k in range(count):
            x = x0 + (x1 - x0) * k / max(1, count - 1) + rng.uniform(-2.0, 2.0)
            rr = r + rng.uniform(-1.5, 1.5)
            tone = rng.choice((STONE, STONE_LIGHT, K.shade(STONE, 0.92)))
            pts = K.ellipse_points(x, y + rng.uniform(-1.5, 1.5), rr, rr * 0.82, 12, 1.0, rng)
            f.poly(pts, tone)
            f.poly(K.ellipse_points(x + rr * 0.3, y + rr * 0.3, rr * 0.55, rr * 0.4, 10), STONE_SHADE, body=False)
            f.ink([(x - rr * 0.5, y - rr * 0.4), (x - rr * 0.1, y - rr * 0.6)], 1.0, K.alpha(K.WHITE, 0.7))
    f.ellipse(64.0, foot - 69.0, 7.0, 5.5, STONE_LIGHT)
    # The blue scarves knotted round the pole, their tails out in the wind.
    for k, (y, length, colour) in enumerate(((42.0, 40.0, SKY_BLUE), (62.0, 46.0, SKY_BLUE_DARK), (84.0, 38.0, SKY_BLUE_LIGHT),
                                             (106.0, 30.0, SKY_BLUE))):
        _scarf(f, 66.0, y, length, colour, t, k * 1.3)
    return f.finish(outline=OUTLINE, width=1.4)


# ---------------------------------------------------------------------------
# The horse standard: a pole with a plume of horse tail.
# ---------------------------------------------------------------------------

STANDARD_FRAME = (64, 320)
STANDARD_FOOT = 314.0


def _draw_standard(anim: str, i: int, n: int):
    t = _phase(i, n)
    cyc = math.tau * t
    f = K.Frame(STANDARD_FRAME)
    foot = STANDARD_FOOT
    # The foot: a heap of stones that holds the pole.
    f.poly([(14.0, foot), (50.0, foot), (44.0, foot - 12.0), (36.0, foot - 17.0), (26.0, foot - 16.0), (19.0, foot - 10.0)], STONE)
    f.poly([(34.0, foot), (50.0, foot), (44.0, foot - 12.0), (36.0, foot - 17.0)], STONE_SHADE, body=False)
    f.ink([(24.0, foot - 8.0), (32.0, foot - 11.0)], 1.0, STONE_DARK)
    # The pole.
    f.limb([(32.0, foot - 14.0), (32.0, 46.0)], 5.0, K.WOOD)
    f.ink([(31.0, foot - 16.0), (31.0, 48.0)], 1.0, K.shade(K.WOOD, 1.3))
    for y in (200.0, 250.0):
        f.limb([(29.0, y), (35.0, y)], 2.0, SADDLE_RED, body=False)
    # The plume of horse tail: a shaggy fall of hair from the ring. Its
    # hem is ragged, and it sways more at the hem than at the ring.
    rng = random.Random("history_horse_standard")

    def sway(s: float) -> float:
        return 4.5 * s * s * math.sin(cyc - 1.4 * s)

    left, right = [], []
    for k in range(9):
        s = k / 8.0
        half = 7.0 + 13.0 * math.sin(min(1.0, s * 2.2) * math.pi * 0.5) + 1.5 * math.sin(s * 9.0)
        y = 50.0 + 84.0 * s
        left.append((32.0 - half + sway(s), y))
        right.append((32.0 + half + sway(s), y))
    hem = []
    for k in range(11):
        u = k / 10.0
        x = right[-1][0] + (left[-1][0] - right[-1][0]) * u
        hem.append((x + sway(1.2) * 0.3, 134.0 + (rng.uniform(10.0, 20.0) if k % 2 else rng.uniform(0.0, 4.0))))
    f.poly(left + hem[::-1][1:-1] + right[::-1], HAIR)
    for k in range(9):
        u = (k + 0.5) / 9.0
        x_top = 26.0 + 12.0 * u
        mid = (left[4][0] + (right[4][0] - left[4][0]) * u, left[4][1])
        end = (left[-1][0] + (right[-1][0] - left[-1][0]) * u + sway(1.0) * 0.4, 140.0 + rng.uniform(0.0, 8.0))
        f.ink([(x_top, 54.0), mid, end], 1.0 if k % 2 else 1.4, HAIR_LIGHT)
    # The ring the plume hangs from.
    f.ellipse(32.0, 48.0, 13.0, 4.0, STEPPE_GOLD)
    f.ellipse(32.0, 47.0, 9.0, 2.0, K.GOLD_DARK, body=False)
    # The trident at the top: a blade like a leaf and two curved prongs.
    f.poly([(32.0, 8.0), (37.0, 22.0), (34.5, 42.0), (29.5, 42.0), (27.0, 22.0)], STONE_LIGHT)
    f.poly([(32.0, 8.0), (37.0, 22.0), (34.5, 42.0), (32.0, 42.0)], STONE_SHADE, body=False)
    for side in (-1.0, 1.0):
        f.limb([(32.0, 38.0), (32.0 + side * 9.0, 36.0), (32.0 + side * 12.0, 26.0), (32.0 + side * 11.0, 18.0)], 2.6, STONE_LIGHT)
    f.limb([(24.0, 42.0), (40.0, 42.0)], 3.0, STEPPE_GOLD)
    return f.finish(outline=OUTLINE, width=1.4)


# ---------------------------------------------------------------------------
# Publication.
# ---------------------------------------------------------------------------

SCENERY = ["prop", "scenery", "history", "steppe"]
DOOR = ["prop", "door", "lock", "history", "steppe"]

FRAMES: Dict[str, Tuple[int, int]] = {
    "history_ger": GER_FRAME,
    "history_great_wall_gate": GATE_FRAME,
    "history_scaffold_plank": SCAFFOLD_FRAME,
    "history_great_wall": WALL_FRAME,
    "history_ovoo": OVOO_FRAME,
    "history_horse_standard": STANDARD_FRAME,
}
DRAW = {
    "history_ger": _draw_ger,
    "history_great_wall_gate": _draw_wall_gate,
    "history_scaffold_plank": _draw_scaffold,
    "history_great_wall": _draw_great_wall,
    "history_ovoo": _draw_ovoo,
    "history_horse_standard": _draw_standard,
}

TARGETS: Dict[str, dict] = {
    "history_ger": _publisher("history_ger", "Ger", LOOP, GER_FRAME, _draw_ger, {"foot": (160.0, float(GER_FRAME[1]))}, "Scenery", SCENERY),
    "history_great_wall_gate": _publisher("history_great_wall_gate", "Great Wall Gate", STILL, GATE_FRAME, _draw_wall_gate,
                                          {"foot": (48.0, 384.0)}, "Door", DOOR, forward=(0.0, -1.0)),
    "history_scaffold_plank": _publisher("history_scaffold_plank", "Scaffold Plank", STILL, SCAFFOLD_FRAME, _draw_scaffold,
                                         {"foot": (160.0, 48.0)}, "Door", DOOR + ["bridge"], forward=(0.0, -1.0)),
    "history_great_wall": _publisher("history_great_wall", "Great Wall", STILL, WALL_FRAME, _draw_great_wall, {"foot": (256.0, float(WALL_FRAME[1]))},
                                     "Scenery", SCENERY),
    "history_ovoo": _publisher("history_ovoo", "Ovoo", LOOP, OVOO_FRAME, _draw_ovoo, {"foot": (64.0, float(OVOO_FRAME[1]))}, "Scenery", SCENERY),
    "history_horse_standard": _publisher("history_horse_standard", "Horse Standard", LOOP, STANDARD_FRAME, _draw_standard,
                                         {"foot": (32.0, float(STANDARD_FRAME[1]))}, "Scenery", SCENERY),
}
