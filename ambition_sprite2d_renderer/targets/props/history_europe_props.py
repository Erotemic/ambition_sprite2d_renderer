"""The props of the European floor of the History dimension (second pass).

The European floor of the grid goes from the Ice Age (biome
`history_ice_age`, and the painted cave `history_painted_cave`) through the
first farmers and the megalith builders (`history_megalith`) to the Celtic
frontier and the Viking north (`history_northwoods`). The props are drawn
in the cel style of the Art dimension's cast
(`targets/characters/_art_cast_kit.py`) in the warm sepia of an old
textbook, with the colours of `targets/characters/_history_europe_kit.py`.

- ``history_mammoth_bone_hut``: scenery. A dome hut of the mammoth
  hunters: a wall of mammoth jawbones, tusks over a dome of hides, and a
  door in an arch of two tusks. Its ``idle`` row lets smoke rise.
- ``history_hand_stencils``: scenery. A wall of a painted cave with hand
  stencils in red ochre, a row of dots and a horse in charcoal and ochre.
- ``history_longhouse``: scenery. A long house of the first farmers: walls
  of wattle and daub between oak posts under a high roof of thatch. Its
  ``idle`` row lets smoke rise through the thatch.
- ``history_trilithon_gate``: the look of a `LockWall` of 32 by 128 world
  units, drawn at 3 to 1 (as ``history_great_wall_gate``). Two standing
  stones and a lintel stone; a slab of bluestone stands in the gap.
- ``history_standing_stone``: scenery. A tall standing stone with lichen.
- ``history_palisade``: scenery. The palisade of a hillfort: sharp oak
  stakes on an earth bank, tied to two rails.
- ``history_longship``: the look of a moving platform. A longship with a
  striped sail, a row of shields and a dragon at the prow. Its deck top is
  the platform (`platform_looks.ron`: `LONGSHIP_SPAN`, `LONGSHIP_TOP`).
- ``history_rune_stone``: scenery. A rune stone with a band of runes in a
  red serpent that runs round its edge.

Animations: ``idle``. No drop shadows: the game draws them. The numbers are
frame pixels; the game shows each prop at half its frame (the gate at a
third).
"""

from __future__ import annotations

import math
import random
from typing import Dict, List, Tuple

from ..characters import _art_cast_kit as K
from ..characters import _history_europe_kit as E
from .art_props import STILL, _publisher

Point = Tuple[float, float]
LOOP: List[Tuple[str, int, int]] = [("idle", 8, 120)]

OUTLINE = E.OUTLINE
HIDE = (196, 156, 108, 255)
HIDE_SHADE = (156, 116, 76, 255)
HIDE_LIGHT = (222, 190, 146, 255)
BONE = (232, 220, 190, 255)
BONE_SHADE = (190, 174, 136, 255)
DARK = (58, 38, 30, 255)
FIRE = (255, 170, 70, 255)
SMOKE = (186, 180, 176, 255)
DAUB = (206, 176, 132, 255)
DAUB_SHADE = (164, 134, 94, 255)
EARTH = (132, 96, 62, 255)
EARTH_DARK = (96, 66, 42, 255)
BLUESTONE = (132, 140, 148, 255)
BLUESTONE_LIGHT = (170, 178, 186, 255)
BLUESTONE_SHADE = (96, 102, 112, 255)
GRANITE = (164, 160, 156, 255)
GRANITE_LIGHT = (198, 194, 188, 255)
GRANITE_SHADE = (118, 114, 112, 255)
SAIL_RED = (186, 44, 40, 255)
SAIL_WHITE = (240, 230, 206, 255)
SAIL_SHADE = (150, 30, 30, 255)
SHIELD_COLOURS = ((236, 190, 70, 255), (46, 40, 38, 255), (186, 44, 40, 255), (240, 230, 206, 255))


def _phase(i: int, n: int) -> float:
    return i / float(max(1, n))


def _rect(x0: float, y0: float, x1: float, y1: float) -> List[Point]:
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def _smoke(f: K.Frame, x: float, y: float, t: float, rise: float = 44.0) -> None:
    """Puffs of smoke that rise from (`x`, `y`), grow and fade."""
    for k in range(4):
        u = (t + k / 4.0) % 1.0
        px = x + 10.0 * u + 4.0 * math.sin(u * math.tau + k)
        py = y - rise * u
        r = 4.0 + 8.0 * u
        f.ellipse(px, py, r, r * 0.85, K.alpha(SMOKE, 0.8 * (1.0 - u)), body=False)


def _grass(f: K.Frame, x0: float, x1: float, y: float, seed: str, step: float = 7.0, tall: float = 10.0) -> None:
    """Tufts of grass along the ground from `x0` to `x1`."""
    rng = random.Random(seed)
    x = x0
    while x < x1:
        h = tall * rng.uniform(0.5, 1.0)
        f.poly([(x - 3.0, y), (x - 1.0, y - h), (x + 0.5, y - 2.0), (x + 2.0, y - h * 0.8), (x + 3.0, y)], E.TURF)
        x += step * rng.uniform(0.7, 1.3)


# ---------------------------------------------------------------------------
# The mammoth bone hut.
# ---------------------------------------------------------------------------

HUT_FRAME = (320, 256)
HUT_FOOT = 250.0


def _draw_hut(anim: str, i: int, n: int):
    t = _phase(i, n)
    f = K.Frame(HUT_FRAME)
    foot = HUT_FOOT
    cx = 160.0
    _smoke(f, cx + 4.0, 60.0, t, rise=48.0)
    # The dome of hides, sewn together.
    dome = [(cx + 124.0 * math.cos(math.pi + math.pi * k / 30.0), foot + 184.0 * math.sin(math.pi + math.pi * k / 30.0)) for k in range(31)]
    f.poly(dome, HIDE)
    f.poly([(cx + 124.0 * math.cos(math.pi + math.pi * k / 30.0), foot + 184.0 * math.sin(math.pi + math.pi * k / 30.0)) for k in range(20, 31)] + [(cx + 60.0, foot)],
           HIDE_SHADE, body=False)
    for k in range(1, 6):
        a = math.pi + math.pi * k / 6.0
        f.ink([(cx + 30.0 * math.cos(a), 74.0), (cx + 118.0 * math.cos(a), foot - 40.0)], 1.2, K.alpha(HIDE_SHADE, 0.9))
        for j in range(6):
            u = (j + 0.5) / 6.0
            x = cx + (30.0 + 88.0 * u) * math.cos(a)
            y = 74.0 + (foot - 114.0) * u
            f.ink([(x - 2.0, y - 1.0), (x + 2.0, y + 1.0)], 0.9, HIDE_LIGHT)
    # The smoke hole at the top, ringed in bone.
    f.ellipse(cx, 70.0, 16.0, 5.0, BONE)
    f.ellipse(cx, 70.0, 11.0, 3.0, DARK, body=False)
    # Long tusks laid over the dome to hold the hides down.
    for side in (-1.0, 1.0):
        for k, (bx, top) in enumerate(((110.0, 86.0), (78.0, 120.0))):
            pts = [(cx + side * bx, foot - 50.0), (cx + side * (bx - 16.0), (foot - 50.0 + top) / 2.0), (cx + side * (bx - 46.0), top),
                   (cx + side * (bx - 66.0), top - 4.0 - 8.0 * k)]
            E.taper(f, pts, 9.0, 4.0, BONE)
    # The wall of jawbones, laid in a herringbone, round the foot of the dome.
    wall = _rect(cx - 126.0, foot - 52.0, cx + 126.0, foot)
    f.poly(wall, BONE_SHADE)
    for row in range(3):
        y = foot - 46.0 + row * 16.0
        for k in range(14):
            x = cx - 118.0 + k * 18.0
            flip = 1.0 if (k + row) % 2 else -1.0
            f.poly([(x, y), (x + 8.0 * flip + 8.0, y + 6.0), (x + 16.0, y), (x + 16.0, y + 10.0), (x + 8.0 * flip + 8.0, y + 15.0), (x, y + 10.0)],
                   BONE, body=False)
            f.ink([(x + 2.0, y + 5.0), (x + 8.0 * flip + 8.0, y + 9.0), (x + 14.0, y + 5.0)], 0.9, BONE_SHADE)
    f.limb([(cx - 126.0, foot - 52.0), (cx + 126.0, foot - 52.0)], 3.0, BONE_SHADE, body=False)
    # Long bones stood up at the sides of the door, their knobbed ends up.
    for side in (-1.0, 1.0):
        for k in range(3):
            bx = cx + side * (40.0 + k * 10.0)
            f.limb([(bx, foot - 50.0), (bx, foot - 84.0 + 6.0 * k)], 5.0, BONE)
            f.ellipse(bx, foot - 86.0 + 6.0 * k, 4.6, 3.6, BONE)
    # The door: an arch of two tusks over a dark opening with firelight in it.
    door = [(cx - 26.0, foot)] + [(cx + 26.0 * math.cos(math.pi + math.pi * k / 16.0), foot - 52.0 + 40.0 * math.sin(math.pi + math.pi * k / 16.0))
                                  for k in range(17)] + [(cx + 26.0, foot)]
    f.poly(door, DARK, body=False)
    f.glow(cx, foot - 22.0, 10.0, K.alpha(FIRE, 0.5))
    f.ellipse(cx, foot - 6.0, 7.0, 4.0, K.alpha(FIRE, 0.9), body=False)
    for side in (-1.0, 1.0):
        E.taper(f, [(cx + side * 30.0, foot - 8.0), (cx + side * 34.0, foot - 56.0), (cx + side * 18.0, foot - 96.0), (cx - side * 6.0, foot - 104.0)], 11.0, 4.0, BONE)
    return f.finish(outline=OUTLINE, width=1.6)


# ---------------------------------------------------------------------------
# The cave wall with hand stencils and a horse.
# ---------------------------------------------------------------------------

STENCIL_FRAME = (256, 256)


def _hand(f: K.Frame, x: float, y: float, turn: float, size: float, colour) -> None:
    """A hand stencil: ochre blown round a hand, so the hand is the bare rock."""
    for k in range(6):
        r = (30.0 - k * 3.0) * size
        f.ellipse(x, y - 4.0 * size, r, r * 1.1, K.alpha(colour, 0.12 + 0.07 * k), body=False)
    palm = K.turn(K.ellipse_points(x, y, 9.0 * size, 10.0 * size, 18), x, y, turn)
    f.poly(palm, E.ROCK, body=False)
    fingers = ((-8.0, -26.0, -18.0), (-3.0, -32.0, -6.0), (2.0, -33.0, 2.0), (7.0, -29.0, 10.0), (12.0, -12.0, 50.0))
    for fx, fy, a in fingers:
        base = (x + fx * 0.8 * size, y - 6.0 * size)
        tip = (x + fx * size + math.sin(math.radians(a)) * 4.0 * size, y + fy * size * 0.85)
        pts = K.turn([base, tip], x, y, turn)
        f.limb(pts, 4.6 * size, E.ROCK, body=False)
    f.limb(K.turn([(x - 4.0 * size, y + 8.0 * size), (x - 4.0 * size, y + 18.0 * size), (x + 4.0 * size, y + 18.0 * size), (x + 4.0 * size, y + 8.0 * size)],
                  x, y, turn), 8.0 * size, E.ROCK, body=False)


def _draw_stencils(anim: str, i: int, n: int):
    f = K.Frame(STENCIL_FRAME)
    # The wall: a slab of rock with a rough edge.
    rng = random.Random("history_hand_stencils")
    pts = []
    for k in range(40):
        a = math.tau * k / 40.0
        r = 1.0 + rng.uniform(-0.04, 0.04)
        x = 128.0 + 120.0 * r * math.cos(a)
        y = 132.0 + 118.0 * r * math.sin(a)
        pts.append((max(5.0, min(251.0, x)), max(6.0, min(250.0, y))))
    pts = [(x, 250.0 if y > 220.0 else y) for x, y in pts]
    f.poly(pts, E.ROCK)
    f.poly([(x * 0.94 + 10.0, y * 0.94 + 12.0) for x, y in pts if x > 150.0] + [(150.0, 250.0)], E.ROCK_SHADE, body=False)
    for k in range(9):
        x0, y0 = rng.uniform(30.0, 220.0), rng.uniform(30.0, 220.0)
        f.ink([(x0, y0), (x0 + rng.uniform(-20.0, 20.0), y0 + rng.uniform(8.0, 26.0))], 1.0, K.alpha(E.ROCK_SHADE, 0.9))
    # The horse: an outline in charcoal, its body in ochre, its mane black.
    hx, hy = 138.0, 92.0
    body = K.ellipse_points(hx, hy, 50.0, 22.0, 28)
    f.poly(body, K.alpha(E.OCHRE_YELLOW, 0.85), body=False)
    f.poly([(hx - 50.0, hy), (hx + 50.0, hy), (hx + 40.0, hy + 14.0), (hx - 40.0, hy + 14.0)], K.alpha(E.OCHRE_RED, 0.5), body=False)
    neck = [(hx + 34.0, hy - 14.0), (hx + 52.0, hy - 38.0), (hx + 64.0, hy - 42.0), (hx + 78.0, hy - 26.0), (hx + 74.0, hy - 20.0), (hx + 60.0, hy - 24.0),
            (hx + 48.0, hy + 4.0)]
    f.poly(neck, K.alpha(E.OCHRE_YELLOW, 0.85), body=False)
    f.ink(body + [body[0]], 2.2, E.CHARCOAL)
    f.ink([(hx + 40.0, hy - 12.0), (hx + 52.0, hy - 38.0), (hx + 64.0, hy - 42.0), (hx + 78.0, hy - 26.0), (hx + 74.0, hy - 20.0), (hx + 60.0, hy - 24.0),
           (hx + 48.0, hy + 6.0)], 2.2, E.CHARCOAL)
    for k in range(7):
        x = hx + 40.0 + k * 3.4
        f.ink([(x, hy - 18.0 - k * 3.0), (x - 4.0, hy - 24.0 - k * 3.0)], 2.4, E.CHARCOAL)
    f.dot(hx + 66.0, hy - 34.0, 1.6, E.CHARCOAL)
    for lx, a in ((-34.0, -8.0), (-22.0, 6.0), (26.0, -4.0), (38.0, 10.0)):
        f.ink([(hx + lx, hy + 18.0), (hx + lx + a * 0.4, hy + 36.0), (hx + lx + a, hy + 50.0)], 2.6, E.CHARCOAL)
    f.ink([(hx - 50.0, hy - 4.0), (hx - 62.0, hy + 8.0), (hx - 64.0, hy + 26.0)], 3.0, E.CHARCOAL)
    # Hand stencils in red ochre, and one in black, and a row of dots.
    for x, y, a, s, c in ((52.0, 104.0, -14.0, 1.0, E.OCHRE_RED), (78.0, 176.0, 8.0, 0.9, E.OCHRE_RED), (150.0, 190.0, -4.0, 1.05, E.OCHRE_RED),
                          (206.0, 176.0, 16.0, 0.85, E.CHARCOAL), (44.0, 196.0, -24.0, 0.75, E.OCHRE_RED)):
        _hand(f, x, y, a, s, c)
    for k in range(6):
        f.dot(108.0 + k * 14.0, 150.0 + 2.0 * math.sin(k), 3.4, K.alpha(E.OCHRE_RED, 0.9))
    return f.finish(outline=OUTLINE, width=1.6)


# ---------------------------------------------------------------------------
# The longhouse of the first farmers.
# ---------------------------------------------------------------------------

LONGHOUSE_FRAME = (384, 256)
LONGHOUSE_FOOT = 250.0


def _draw_longhouse(anim: str, i: int, n: int):
    t = _phase(i, n)
    f = K.Frame(LONGHOUSE_FRAME)
    foot = LONGHOUSE_FOOT
    _smoke(f, 214.0, 44.0, t, rise=36.0)
    # The walls: wattle and daub between oak posts.
    f.poly(_rect(30.0, 160.0, 354.0, foot), DAUB)
    f.poly(_rect(30.0, 160.0, 354.0, 176.0), DAUB_SHADE, body=False)
    rng = random.Random("history_longhouse")
    for k in range(10):
        x = 30.0 + k * 36.0
        f.poly(_rect(x, 160.0, x + 7.0, foot), E.OAK)
        f.ink([(x + 2.0, 168.0), (x + 2.0, foot - 4.0)], 1.0, E.OAK_LIGHT)
        if k < 9:
            for j in range(3):
                y = 186.0 + j * 20.0 + rng.uniform(-3.0, 3.0)
                f.ink([(x + 10.0, y), (x + 33.0, y + rng.uniform(-2.0, 2.0))], 0.9, K.alpha(DAUB_SHADE, 0.9))
    f.poly(_rect(347.0, 160.0, 354.0, foot), E.OAK)
    # The door: oak planks in a dark frame.
    f.poly(_rect(166.0, 186.0, 206.0, foot), E.OAK_DARK)
    f.poly(_rect(170.0, 190.0, 202.0, foot), E.OAK)
    for x in (178.0, 186.0, 194.0):
        f.ink([(x, 191.0), (x, foot)], 1.0, E.OAK_DARK)
    # The roof of thatch: a high ridge, low eaves, and a hipped end.
    roof = [(14.0, 168.0), (40.0, 52.0), (344.0, 52.0), (370.0, 168.0)]
    f.poly(roof, E.THATCH)
    f.poly([(290.0, 168.0), (344.0, 52.0), (370.0, 168.0)], E.THATCH_SHADE, body=False)
    f.poly([(14.0, 168.0), (370.0, 168.0), (368.0, 160.0), (16.0, 160.0)], E.THATCH_SHADE, body=False)
    for k in range(32):
        x = 40.0 + k * 10.0
        u = (x - 40.0) / 304.0
        f.ink([(x - 2.0 + 6.0 * (u - 0.5), 62.0 + (k % 3) * 4.0), (x - 4.0 + 12.0 * (u - 0.5), 162.0)], 1.0, K.alpha(E.THATCH_SHADE, 0.9))
    # The ridge, tied down with hazel rods, and two rows of rope weights.
    f.limb([(40.0, 52.0), (344.0, 52.0)], 6.0, E.THATCH_SHADE)
    for k in range(16):
        x = 48.0 + k * 19.0
        f.ink([(x - 4.0, 49.0), (x + 4.0, 56.0)], 1.4, E.OAK_DARK)
    for y in (100.0, 136.0):
        inset = 26.0 * (y - 52.0) / 116.0
        f.ink([(44.0 - inset, y), (340.0 + inset, y)], 1.2, K.alpha(E.OAK_DARK, 0.7))
    return f.finish(outline=OUTLINE, width=1.6)


# ---------------------------------------------------------------------------
# The trilithon gate.
# ---------------------------------------------------------------------------

GATE_FRAME = (96, 384)


def _stone(f: K.Frame, pts: List[Point], light, base, shade, seed: str, lichen: int = 6) -> None:
    """A dressed stone: its face, a shade down its right side, cracks and lichen."""
    rng = random.Random(seed)
    f.poly(pts, base)
    xs = [x for x, _ in pts]
    ys = [y for _, y in pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    f.poly([(x1 - (x1 - x0) * 0.28, y0 + 3.0), (x1 - 2.0, y0 + 3.0), (x1 - 2.0, y1 - 2.0), (x1 - (x1 - x0) * 0.24, y1 - 2.0)], shade, body=False)
    f.ink([(x0 + 3.0, y0 + 4.0), (x0 + 3.0, y1 - 6.0)], 1.4, light)
    for k in range(int((y1 - y0) / 40.0) + 1):
        y = rng.uniform(y0 + 8.0, y1 - 8.0)
        x = rng.uniform(x0 + 4.0, x1 - 10.0)
        f.ink([(x, y), (x + rng.uniform(3.0, 8.0), y + rng.uniform(4.0, 12.0)), (x + rng.uniform(0.0, 6.0), y + rng.uniform(14.0, 20.0))], 0.9, shade)
    for k in range(lichen):
        x = rng.uniform(x0 + 5.0, x1 - 5.0)
        y = rng.uniform(y0 + 5.0, y1 - 5.0)
        r = rng.uniform(2.0, 4.5)
        f.ellipse(x, y, r, r * 0.8, K.alpha(E.LICHEN, 0.9), body=False)


def _draw_trilithon(anim: str, i: int, n: int):
    w, h = GATE_FRAME
    f = K.Frame(GATE_FRAME)
    foot = h - 4.0
    # The bluestone slab in the gap, behind.
    _stone(f, [(30.0, 44.0), (66.0, 44.0), (64.0, foot), (32.0, foot)], BLUESTONE_LIGHT, BLUESTONE, BLUESTONE_SHADE, "tri:blue", 4)
    # The bluestone is rough: blocks of it split along its beds.
    for y in (110.0, 196.0, 262.0, 330.0):
        f.ink([(32.0, y), (48.0, y + 4.0), (64.0, y - 2.0)], 1.4, BLUESTONE_SHADE)
    # The two uprights, a little wider at the foot.
    _stone(f, [(8.0, 40.0), (34.0, 40.0), (36.0, foot), (5.0, foot)], E.SARSEN_LIGHT, E.SARSEN, E.SARSEN_SHADE, "tri:left")
    _stone(f, [(62.0, 40.0), (88.0, 40.0), (91.0, foot), (60.0, foot)], E.SARSEN_LIGHT, E.SARSEN, E.SARSEN_SHADE, "tri:right")
    # The lintel: laid on top, with the knobs of its joints.
    for x in (21.0, 75.0):
        f.ellipse(x, 42.0, 6.0, 3.0, E.SARSEN_SHADE)
    _stone(f, [(5.0, 10.0), (91.0, 6.0), (91.0, 40.0), (5.0, 42.0)], E.SARSEN_LIGHT, E.SARSEN, E.SARSEN_SHADE, "tri:lintel", 4)
    f.ink([(6.0, 40.0), (90.0, 38.0)], 1.6, E.SARSEN_SHADE)
    # Turf at the foot.
    _grass(f, 8.0, 90.0, foot, "tri:grass", 6.0, 9.0)
    return f.finish(outline=OUTLINE, width=1.6)


# ---------------------------------------------------------------------------
# The standing stone.
# ---------------------------------------------------------------------------

STANDING_FRAME = (96, 256)


def _draw_standing(anim: str, i: int, n: int):
    f = K.Frame(STANDING_FRAME)
    foot = 252.0
    pts = [(22.0, foot), (16.0, 180.0), (20.0, 90.0), (30.0, 30.0), (46.0, 10.0), (60.0, 16.0), (70.0, 60.0), (78.0, 150.0), (80.0, foot)]
    f.poly(pts, E.SARSEN)
    f.poly([(58.0, 18.0), (60.0, 16.0), (70.0, 60.0), (78.0, 150.0), (80.0, foot), (62.0, foot), (62.0, 140.0), (56.0, 60.0)], E.SARSEN_SHADE, body=False)
    f.ink([(24.0, 92.0), (32.0, 34.0), (44.0, 16.0)], 1.6, E.SARSEN_LIGHT)
    rng = random.Random("history_standing_stone")
    for k in range(5):
        y = 40.0 + k * 42.0
        x = rng.uniform(28.0, 52.0)
        f.ink([(x, y), (x + 6.0, y + 10.0), (x + 3.0, y + 22.0)], 1.0, E.SARSEN_SHADE)
    for k in range(9):
        x, y = rng.uniform(24.0, 66.0), rng.uniform(30.0, 230.0)
        r = rng.uniform(2.5, 5.0)
        f.ellipse(x, y, r, r * 0.8, K.alpha(E.LICHEN, 0.9), body=False)
    _grass(f, 10.0, 88.0, foot, "standing:grass", 6.0, 12.0)
    return f.finish(outline=OUTLINE, width=1.6)


# ---------------------------------------------------------------------------
# The palisade of a hillfort.
# ---------------------------------------------------------------------------

PALISADE_FRAME = (256, 192)


def _draw_palisade(anim: str, i: int, n: int):
    f = K.Frame(PALISADE_FRAME)
    foot = 188.0
    rng = random.Random("history_palisade")
    # The stakes: oak trunks with sharp tops, some taller.
    for k in range(16):
        x = 12.0 + k * 15.0
        top = 34.0 + rng.uniform(-8.0, 10.0)
        colour = E.OAK if k % 2 == 0 else K.shade(E.OAK, 0.9)
        f.poly([(x - 6.5, 160.0), (x - 6.5, top + 12.0), (x, top), (x + 6.5, top + 12.0), (x + 6.5, 160.0)], colour)
        f.poly([(x + 2.5, 160.0), (x + 2.5, top + 8.0), (x + 6.5, top + 12.0), (x + 6.5, 160.0)], E.OAK_DARK, body=False)
        f.poly([(x - 6.5, top + 12.0), (x, top), (x + 6.5, top + 12.0), (x, top + 9.0)], E.OAK_LIGHT, body=False)
        f.ink([(x - 3.0, top + 22.0), (x - 3.0, top + 50.0)], 0.9, E.OAK_DARK)
    # The two rails, tied to each stake with withies.
    for y in (70.0, 128.0):
        f.limb([(10.0, y), (246.0, y)], 7.0, E.OAK_DARK)
        f.ink([(8.0, y - 1.6), (248.0, y - 1.6)], 1.0, E.OAK)
        for k in range(16):
            x = 12.0 + k * 15.0
            f.ink([(x - 4.0, y - 5.0), (x + 4.0, y + 5.0)], 1.4, E.THATCH)
            f.ink([(x - 4.0, y + 5.0), (x + 4.0, y - 5.0)], 1.4, E.THATCH)
    # The earth bank at the foot, with turf on its top.
    bank = [(4.0, foot), (8.0, 156.0), (60.0, 150.0), (128.0, 148.0), (196.0, 150.0), (248.0, 156.0), (252.0, foot)]
    f.poly(bank, EARTH)
    f.poly([(6.0, 166.0), (250.0, 166.0), (252.0, foot), (4.0, foot)], EARTH_DARK, body=False)
    f.limb([(8.0, 156.0), (60.0, 150.0), (128.0, 148.0), (196.0, 150.0), (248.0, 156.0)], 6.0, E.TURF, body=False)
    _grass(f, 10.0, 246.0, 154.0, "palisade:grass", 8.0, 8.0)
    for k in range(7):
        x, y = rng.uniform(20.0, 236.0), rng.uniform(166.0, 182.0)
        f.ellipse(x, y, 3.0, 2.2, K.shade(EARTH, 1.2), body=False)
    return f.finish(outline=OUTLINE, width=1.6)


# ---------------------------------------------------------------------------
# The longship: its deck is the platform.
# ---------------------------------------------------------------------------

LONGSHIP_FRAME = (384, 192)
LONGSHIP_SPAN = (16.0, 368.0)
LONGSHIP_TOP = 150.0


def _hull_bottom(x: float) -> float:
    """The keel line of the hull under the deck, at frame x."""
    u = (x - 30.0) / 324.0
    return 150.0 + 36.0 * math.sin(math.pi * max(0.0, min(1.0, u))) ** 0.6


def _draw_longship(anim: str, i: int, n: int):
    f = K.Frame(LONGSHIP_FRAME)
    top = LONGSHIP_TOP
    mast_x = 192.0
    # The stays from the mast head to the stem and the stern.
    f.ink([(mast_x, 16.0), (352.0, 96.0)], 1.0, E.OAK_DARK)
    f.ink([(mast_x, 16.0), (30.0, 104.0)], 1.0, E.OAK_DARK)
    # The mast and the yard.
    f.limb([(mast_x, top), (mast_x, 14.0)], 5.0, E.OAK_DARK)
    f.limb([(108.0, 24.0), (276.0, 24.0)], 4.0, E.OAK_DARK)
    # The sail: a square of red and white stripes, full of wind.
    sail = [(110.0, 26.0), (274.0, 26.0), (280.0, 76.0), (274.0, 124.0), (110.0, 124.0), (116.0, 76.0)]
    f.poly(sail, SAIL_WHITE)
    for k in range(6):
        if k % 2:
            continue
        x0 = 110.0 + k * 164.0 / 6.0
        x1 = x0 + 164.0 / 6.0
        f.poly([(x0, 26.0), (x1, 26.0), (x1 + 3.0 * (k - 2.5) / 2.5 + 6.0 * (k / 5.0), 76.0), (x1, 124.0), (x0, 124.0),
                (x0 + 3.0 * (k - 2.5) / 2.5 + 6.0 * (k / 5.0), 76.0)], SAIL_RED, body=False)
    f.poly([(220.0, 26.0), (274.0, 26.0), (280.0, 76.0), (274.0, 124.0), (220.0, 124.0), (226.0, 76.0)], K.alpha(SAIL_SHADE, 0.35), body=False)
    for y in (58.0, 92.0):
        f.ink([(113.0, y), (277.0, y)], 0.8, K.alpha(SAIL_SHADE, 0.6))
    # The sheets from the foot of the sail to the gunwale.
    f.ink([(110.0, 124.0), (80.0, top)], 1.0, E.OAK_DARK)
    f.ink([(274.0, 124.0), (306.0, top)], 1.0, E.OAK_DARK)
    # The hull: clinker planks that sweep up to a tall stern and a dragon prow.
    hull = [(28.0, top)]
    for k in range(25):
        x = 30.0 + 324.0 * k / 24.0
        hull.append((x, _hull_bottom(x)))
    hull += [(356.0, top), (362.0, 130.0), (366.0, 104.0), (372.0, 86.0), (376.0, 90.0), (370.0, 112.0), (364.0, 148.0), (340.0, 176.0)]
    hull = [(28.0, top), (22.0, 130.0), (16.0, 108.0), (12.0, 92.0), (18.0, 90.0), (26.0, 112.0), (34.0, 140.0)] + hull[1:]
    f.poly(hull, E.OAK)
    for k in range(1, 4):
        pts = []
        for j in range(25):
            x = 30.0 + 324.0 * j / 24.0
            pts.append((x, top + (_hull_bottom(x) - top) * k / 4.0))
        f.ink(pts, 1.4, E.OAK_DARK)
    f.poly([(40.0, top + 22.0)] + [(30.0 + 324.0 * j / 24.0, _hull_bottom(30.0 + 324.0 * j / 24.0)) for j in range(2, 23)] + [(344.0, top + 22.0)],
           K.alpha(E.OAK_DARK, 0.55), body=False)
    # The stern post: it curls back over at the top.
    E.taper(f, [(22.0, 120.0), (14.0, 96.0), (16.0, 76.0), (28.0, 70.0), (32.0, 80.0)], 9.0, 5.0, E.OAK)
    # The dragon at the prow: a neck that rises and a head with open jaws.
    E.taper(f, [(366.0, 120.0), (370.0, 90.0), (362.0, 66.0), (352.0, 50.0)], 11.0, 9.0, E.OAK)
    head = [(346.0, 52.0), (352.0, 40.0), (364.0, 36.0), (378.0, 42.0), (366.0, 46.0), (374.0, 52.0), (362.0, 54.0), (354.0, 60.0)]
    f.poly(head, E.OAK)
    f.poly([(350.0, 38.0), (346.0, 28.0), (356.0, 37.0)], E.OAK)
    f.dot(360.0, 42.0, 1.8, DARK)
    f.ink([(366.0, 46.0), (360.0, 49.0)], 1.0, DARK)
    for k in range(3):
        f.ink([(362.0 - k * 3.0, 62.0 + k * 14.0), (368.0 - k * 1.0, 66.0 + k * 14.0)], 1.0, E.OAK_DARK)
    # The deck edge: the top of the platform, lit.
    f.poly(_rect(28.0, top, 356.0, top + 4.0), E.OAK_LIGHT, body=False)
    # A row of shields along the side, and the oar holes between them.
    for k in range(14):
        x = 46.0 + k * 22.0
        c = SHIELD_COLOURS[k % 4]
        f.ellipse(x, top + 13.0, 9.0, 9.0, E.OAK_DARK, body=False)
        f.ellipse(x, top + 13.0, 7.6, 7.6, c, body=False)
        f.ellipse(x, top + 13.0, 2.6, 2.6, E.IRON, body=False)
        f.ink(K.ellipse_points(x, top + 13.0, 9.0, 9.0, 20) + [K.ellipse_points(x, top + 13.0, 9.0, 9.0, 20)[0]], 1.0, OUTLINE)
        if k < 13:
            f.ellipse(x + 11.0, top + 22.0, 2.0, 2.0, DARK, body=False)
    return f.finish(outline=OUTLINE, width=1.6)


# ---------------------------------------------------------------------------
# The rune stone.
# ---------------------------------------------------------------------------

RUNE_FRAME = (96, 192)


def _runes(f: K.Frame, a: Point, b: Point, seed: str, colour) -> None:
    """Little rune marks along the band from `a` to `b`: a stave and a twig
    or two on each."""
    rng = random.Random(seed)
    length = math.hypot(b[0] - a[0], b[1] - a[1])
    count = max(1, int(length / 7.0))
    dx, dy = (b[0] - a[0]) / length, (b[1] - a[1]) / length
    nx, ny = -dy, dx
    for k in range(count):
        u = (k + 0.5) / count
        x, y = a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u
        p0 = (x - nx * 3.0, y - ny * 3.0)
        p1 = (x + nx * 3.0, y + ny * 3.0)
        f.ink([p0, p1], 0.9, colour)
        kind = rng.randrange(4)
        if kind == 0:
            f.ink([(x - nx * 3.0, y - ny * 3.0), (x - nx * 1.0 + dx * 2.4, y - ny * 1.0 + dy * 2.4)], 0.8, colour)
        elif kind == 1:
            f.ink([(x, y), (x + nx * 2.0 + dx * 2.4, y + ny * 2.0 + dy * 2.4)], 0.8, colour)
        elif kind == 2:
            f.ink([(x - nx * 1.0 - dx * 2.0, y - ny * 1.0 - dy * 2.0), (x + nx * 1.0 + dx * 2.0, y + ny * 1.0 + dy * 2.0)], 0.8, colour)


def _draw_rune_stone(anim: str, i: int, n: int):
    f = K.Frame(RUNE_FRAME)
    foot = 188.0
    stone = [(12.0, foot), (10.0, 120.0), (14.0, 60.0), (26.0, 24.0), (48.0, 10.0), (70.0, 22.0), (82.0, 58.0), (86.0, 120.0), (84.0, foot)]
    f.poly(stone, GRANITE)
    f.poly([(64.0, 18.0), (70.0, 22.0), (82.0, 58.0), (86.0, 120.0), (84.0, foot), (70.0, foot), (72.0, 110.0), (66.0, 50.0)], GRANITE_SHADE, body=False)
    f.ink([(15.0, 100.0), (18.0, 58.0), (28.0, 28.0)], 1.4, GRANITE_LIGHT)
    # The serpent: a red band round the face of the stone, from its tail at
    # the foot on the left to its head at the foot on the right.
    path = [(24.0, 178.0), (22.0, 120.0), (25.0, 66.0), (34.0, 36.0), (48.0, 24.0), (62.0, 34.0), (71.0, 66.0), (74.0, 120.0), (70.0, 168.0)]
    mid = E.smooth(path, 4)
    f.limb(mid, 11.0, (40, 30, 28, 255), body=False)
    f.limb(mid, 8.0, E.OCHRE_RED, body=False)
    for a, b in zip(path, path[1:]):
        _runes(f, a, b, f"rune:{a}", (40, 30, 28, 255))
    # The serpent's head, with an eye, and its tail.
    f.poly([(64.0, 166.0), (76.0, 164.0), (80.0, 174.0), (70.0, 180.0), (60.0, 176.0)], E.OCHRE_RED)
    f.dot(71.0, 170.0, 1.4, (40, 30, 28, 255))
    f.limb([(24.0, 178.0), (30.0, 182.0), (36.0, 178.0)], 4.0, E.OCHRE_RED, body=False)
    # In the middle, a knot of two crossed bands.
    for a, b in (((36.0, 70.0), (60.0, 130.0)), ((60.0, 70.0), (36.0, 130.0))):
        f.limb([a, ((a[0] + b[0]) / 2.0 + 4.0, (a[1] + b[1]) / 2.0), b], 5.0, (40, 30, 28, 255), body=False)
        f.limb([a, ((a[0] + b[0]) / 2.0 + 4.0, (a[1] + b[1]) / 2.0), b], 3.0, SAIL_WHITE, body=False)
    f.ellipse(50.0, 100.0, 8.0, 8.0, (40, 30, 28, 255), body=False)
    f.ellipse(50.0, 100.0, 6.0, 6.0, E.WOOL_BLUE, body=False)
    _grass(f, 8.0, 90.0, foot, "rune:grass", 6.0, 10.0)
    return f.finish(outline=OUTLINE, width=1.6)


# ---------------------------------------------------------------------------
# Publication.
# ---------------------------------------------------------------------------

SCENERY = ["prop", "scenery", "history", "europe"]
DOOR = ["prop", "door", "lock", "history", "europe"]

FRAMES: Dict[str, Tuple[int, int]] = {
    "history_mammoth_bone_hut": HUT_FRAME,
    "history_hand_stencils": STENCIL_FRAME,
    "history_longhouse": LONGHOUSE_FRAME,
    "history_trilithon_gate": GATE_FRAME,
    "history_standing_stone": STANDING_FRAME,
    "history_palisade": PALISADE_FRAME,
    "history_longship": LONGSHIP_FRAME,
    "history_rune_stone": RUNE_FRAME,
}
DRAW = {
    "history_mammoth_bone_hut": _draw_hut,
    "history_hand_stencils": _draw_stencils,
    "history_longhouse": _draw_longhouse,
    "history_trilithon_gate": _draw_trilithon,
    "history_standing_stone": _draw_standing,
    "history_palisade": _draw_palisade,
    "history_longship": _draw_longship,
    "history_rune_stone": _draw_rune_stone,
}


def _foot(name: str) -> Dict[str, Tuple[float, float]]:
    w, h = FRAMES[name]
    return {"foot": (w / 2.0, float(h))}


TARGETS: Dict[str, dict] = {
    "history_mammoth_bone_hut": _publisher("history_mammoth_bone_hut", "Mammoth Bone Hut", LOOP, HUT_FRAME, _draw_hut, _foot("history_mammoth_bone_hut"),
                                           "Scenery", SCENERY),
    "history_hand_stencils": _publisher("history_hand_stencils", "Hand Stencils", STILL, STENCIL_FRAME, _draw_stencils, _foot("history_hand_stencils"),
                                        "Scenery", SCENERY),
    "history_longhouse": _publisher("history_longhouse", "Longhouse", LOOP, LONGHOUSE_FRAME, _draw_longhouse, _foot("history_longhouse"), "Scenery", SCENERY),
    "history_trilithon_gate": _publisher("history_trilithon_gate", "Trilithon Gate", STILL, GATE_FRAME, _draw_trilithon, {"foot": (48.0, 384.0)}, "Door",
                                         DOOR, forward=(0.0, -1.0)),
    "history_standing_stone": _publisher("history_standing_stone", "Standing Stone", STILL, STANDING_FRAME, _draw_standing, _foot("history_standing_stone"),
                                         "Scenery", SCENERY),
    "history_palisade": _publisher("history_palisade", "Palisade", STILL, PALISADE_FRAME, _draw_palisade, _foot("history_palisade"), "Scenery", SCENERY),
    "history_longship": _publisher("history_longship", "Longship", STILL, LONGSHIP_FRAME, _draw_longship,
                                   {"top": ((LONGSHIP_SPAN[0] + LONGSHIP_SPAN[1]) / 2.0, LONGSHIP_TOP)}, "Scenery", ["prop", "platform", "history", "europe"]),
    "history_rune_stone": _publisher("history_rune_stone", "Rune Stone", STILL, RUNE_FRAME, _draw_rune_stone, _foot("history_rune_stone"), "Scenery", SCENERY),
}
