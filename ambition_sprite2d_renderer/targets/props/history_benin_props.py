"""The props of Benin City (the History dimension).

Benin City was the capital of the kingdom of Benin, in the forest of what
is now southern Nigeria, from about 1200 to 1897 CE. Walls of earth went
round it. The guild of brass casters (Igun Eronmwon) cast by lost wax on
Igun Street. The palace of the Oba had brass plaques on its pillars and a
brass bird on each turret. In 1897 a British force burned the city and
took the brass to Europe.

These props are drawn in the cel style of the dimension's cast
(`targets/characters/_history_americas_kit.py`): flat colour, one shade, a
bold warm outline. They show the skill of the casters and the size of the
court with respect. Each is "a" thing of its kind, not a copy of one real
work.

- ``history_brass_furnace``: scenery, a furnace of clay with a crucible of
  molten brass in its mouth, and two bellows of goatskin that blow into
  it. Its ``idle`` row pumps the bellows and moves the glow and the sparks.
- ``history_manillas``: scenery, a heap of brass manillas (open bracelets
  in the shape of a horseshoe) in a woven basket and on the ground. Traders
  paid in manillas, and the casters melted them for brass.
- ``history_benin_plaque``: scenery, a brass plaque: a warrior of the court
  in high relief with a spear and a shield, on a ground of incised flowers
  of four leaves, with a nail hole at each corner and green patina in the
  hollows.
- ``history_benin_palace``: scenery, a stretch of the palace: a long wall
  of red earth with ridges along it, a steep roof of wooden shingles, and a
  tall pointed turret. A brass bird with spread wings stands on its point,
  and a brass python goes down its front.
- ``history_benin_palace_gate``: the look of a `LockWall` of 32 by 128
  world units, drawn at 3 to 1: a tall gate of dark carved wood with brass
  studs and one small brass plaque, in a frame of red earth.
- ``history_museum_case``: scenery, a glass case on a stand of dark wood
  with a brass plaque in it, and a small white card that reads "ON LOAN".

The numbers are frame pixels; the game shows each prop at half its frame
(the gate at a third). No drop shadows: the game draws them.
"""

from __future__ import annotations

import math
import random
from typing import Callable, Dict, List, Tuple

from ..characters import _art_cast_kit as K
from ..characters import _history_americas_kit as A
from .art_props import _publisher

Point = Tuple[float, float]
STILL: List[Tuple[str, int, int]] = [("idle", 1, 1000)]
LOOP: List[Tuple[str, int, int]] = [("idle", 8, 120)]

FURNACE_FRAME = (160, 192)
MANILLAS_FRAME = (128, 64)
PLAQUE_FRAME = (96, 128)
PALACE_FRAME = (512, 384)
GATE_FRAME = (96, 384)
CASE_FRAME = (160, 224)

LATERITE = (176, 84, 52, 255)
LATERITE_LIGHT = (208, 118, 78, 255)
LATERITE_SHADE = (136, 60, 38, 255)
LATERITE_DARK = (98, 42, 28, 255)
BRASS = (214, 164, 66, 255)
BRASS_LIGHT = (246, 212, 124, 255)
BRASS_SHADE = (166, 116, 42, 255)
BRASS_DARK = (110, 72, 30, 255)
PATINA = (92, 150, 118, 255)
PATINA_LIGHT = (136, 186, 150, 255)
WOOD = (122, 80, 50, 255)
WOOD_LIGHT = (158, 112, 74, 255)
WOOD_DARK = (78, 50, 34, 255)
WOOD_BLACK = (52, 34, 26, 255)
SHINGLE = (140, 100, 64, 255)
SHINGLE_LIGHT = (176, 134, 88, 255)
SHINGLE_SHADE = (104, 72, 46, 255)
CLAY = (176, 118, 78, 255)
CLAY_LIGHT = (206, 150, 104, 255)
CLAY_SHADE = (136, 86, 56, 255)
CRUCIBLE = (128, 104, 92, 255)
CRUCIBLE_SHADE = (96, 76, 68, 255)
MOLTEN = (255, 214, 96, 255)
EMBER = (255, 132, 50, 255)
EMBER_HOT = (255, 226, 140, 255)
COAL = (54, 42, 40, 255)
GOATSKIN = (200, 170, 128, 255)
GOATSKIN_SHADE = (156, 124, 88, 255)
GOAT_SPOT = (110, 80, 56, 255)
STRAW = (204, 168, 100, 255)
STRAW_SHADE = (156, 120, 64, 255)
STRAW_DARK = (116, 86, 44, 255)
CARD = (250, 248, 240, 255)
CARD_SHADE = (214, 208, 194, 255)
CARD_INK = (40, 32, 30, 255)
GLASS = (206, 232, 236, 255)


def _rect(x0: float, y0: float, x1: float, y1: float) -> List[Point]:
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def _phase(i: int, n: int) -> float:
    return i / float(max(1, n))


def _ridges(f: K.Frame, x0: float, x1: float, y0: float, y1: float, gap: float, light, shade) -> None:
    """Ridges along a wall of earth, each `gap` px: a lit top and a line of
    shade under it, as the builders shaped the courses by hand."""
    y = y0 + gap * 0.5
    while y < y1 - 2.0:
        f.ink([(x0 + 1.0, y), (x1 - 1.0, y)], 1.4, light)
        f.ink([(x0 + 1.0, y + 2.2), (x1 - 1.0, y + 2.2)], 1.2, shade)
        y += gap


def _flower(f: K.Frame, x: float, y: float, s: float) -> None:
    """A flower of four leaves cut into the brass: the river leaf that fills
    the ground of a plaque."""
    for dx, dy in ((1.0, 0.0), (-1.0, 0.0), (0.0, 1.0), (0.0, -1.0)):
        rx, ry = (s * 0.5, s * 0.24) if dx else (s * 0.24, s * 0.5)
        f.ellipse(x + dx * s * 0.5, y + dy * s * 0.5, rx, ry, BRASS_SHADE, body=False)
        f.ellipse(x + dx * s * 0.55, y + dy * s * 0.55, rx * 0.5, ry * 0.5, BRASS_DARK, body=False)
    f.dot(x, y, s * 0.18, BRASS_LIGHT)


def _court_figure(f: K.Frame, cx: float, top: float, u: float, kind: str, shadow: bool = False) -> None:
    """A figure of the court in high relief, seen from the front, as the
    casters showed rank: `kind` is ``warrior`` (a spear and a shield) or
    ``horn`` (a side-blown horn at the mouth). `u` is one hundredth of its
    height; `top` is the top of its head. With `shadow` it draws the shade
    that the relief casts down and to the right on the ground."""
    ox, oy = (1.4 * u, 1.8 * u) if shadow else (0.0, 0.0)

    def p(x: float, y: float) -> Point:
        return (cx + x * u + ox, top + y * u + oy)

    hi, mid, lo = (BRASS_DARK,) * 3 if shadow else (BRASS_LIGHT, BRASS, BRASS_SHADE)
    # The arms come first, so the body covers their roots.
    if kind == "warrior":
        f.limb([p(-19.0, -2.0), p(-19.0, 98.0)], 1.6 * u, lo, body=False)
        f.poly([p(-19.0, -4.0), p(-16.4, 3.0), p(-19.0, 10.0), p(-21.6, 3.0)], hi, body=False)
        f.ink([p(-19.0, -2.0), p(-19.0, 8.0)], 0.5 * u, lo)
        f.limb([p(-10.0, 33.0), p(-17.0, 42.0), p(-19.0, 48.0)], 4.6 * u, mid, body=False)
        f.ellipse(*p(-19.0, 48.0), 2.6 * u, 2.6 * u, hi, body=False)
        f.limb([p(10.0, 33.0), p(17.0, 40.0), p(17.0, 46.0)], 4.6 * u, mid, body=False)
    else:
        f.limb([p(-10.0, 33.0), p(-20.0, 30.0), p(-17.0, 19.0)], 4.6 * u, mid, body=False)
        f.limb([p(10.0, 33.0), p(4.0, 34.0), p(-6.0, 22.0)], 4.6 * u, mid, body=False)
    # The legs and the feet, with rings at the ankles.
    for s in (-1.0, 1.0):
        f.limb([p(s * 5.0, 74.0), p(s * 5.5, 92.0)], 5.0 * u, mid, body=False)
        f.ellipse(*p(s * 6.5, 94.5), 4.2 * u, 2.2 * u, hi, body=False)
        f.ink([p(s * 5.5 - 2.4, 89.0), p(s * 5.5 + 2.4, 89.0)], 0.7 * u, lo)
    # The wrapper: wide at the hem, folds in it, and a sash knotted at the hip.
    skirt = [p(-11.0, 50.0), p(11.0, 50.0), p(19.0, 73.0), p(12.0, 77.0), p(-12.0, 77.0), p(-19.0, 73.0)]
    f.poly(skirt, hi, body=False)
    f.poly([p(3.0, 50.0), p(11.0, 50.0), p(19.0, 73.0), p(12.0, 77.0), p(4.0, 77.0)], mid, body=False)
    for x in (-10.0, -4.0, 2.0, 8.0):
        f.ink([p(x * 0.7, 54.0), p(x * 1.25, 75.0)], 0.6 * u, lo)
    f.ellipse(*p(9.0, 53.0), 3.0 * u, 2.4 * u, hi, body=False)
    f.limb([p(9.0, 54.0), p(12.0, 66.0)], 1.8 * u, hi, body=False)
    # The body, the shade on its far side, and a round pendant.
    f.poly([p(-12.0, 30.0), p(12.0, 30.0), p(10.0, 52.0), p(-10.0, 52.0)], hi, body=False)
    f.poly([p(3.0, 30.0), p(12.0, 30.0), p(10.0, 52.0), p(3.0, 52.0)], mid, body=False)
    f.ink([p(-10.0, 50.0), p(10.0, 50.0)], 1.2 * u, lo)
    f.ellipse(*p(0.0, 38.0), 3.0 * u, 3.0 * u, hi, body=False)
    f.ink([p(-2.0, 38.0), p(2.0, 38.0)], 0.5 * u, lo)
    # The high collar of beads: many strands, one over the next.
    f.poly([p(-6.5, 21.0), p(6.5, 21.0), p(7.5, 30.0), p(-7.5, 30.0)], mid, body=False)
    for k in range(5):
        y = 22.4 + k * 1.6
        f.ink([p(-6.6 - k * 0.2, y), p(6.6 + k * 0.2, y)], 0.6 * u, hi)
    # The head, the face, and the helmet with its rows of beads and a crest.
    f.ellipse(*p(0.0, 15.0), 7.0 * u, 8.0 * u, hi, body=False)
    f.poly([p(-8.0, 14.0), p(-8.0, 8.0), p(-5.0, 3.0), p(5.0, 3.0), p(8.0, 8.0), p(8.0, 14.0), p(0.0, 11.5)], mid, body=False)
    for y in (6.0, 9.0):
        for k in range(5):
            f.dot(*p(-5.0 + k * 2.5, y), 0.7 * u, hi)
    f.ellipse(*p(0.0, 2.0), 2.4 * u, 2.0 * u, hi, body=False)
    for s in (-1.0, 1.0):
        f.ink([p(s * 1.4, 15.6), p(s * 4.2, 15.2)], 0.7 * u, lo if shadow else BRASS_DARK)
    f.ink([p(0.0, 15.0), p(0.0, 18.4), p(1.2, 18.6)], 0.6 * u, lo)
    f.ink([p(-2.0, 20.4), p(2.0, 20.4)], 0.6 * u, lo)
    if kind == "warrior":
        # The shield: long, with rounded ends, a raised rim and a boss.
        shield = [p(13.0, 36.0), p(26.0, 36.0), p(28.0, 40.0), p(28.0, 60.0), p(26.0, 64.0), p(13.0, 64.0), p(11.0, 60.0), p(11.0, 40.0)]
        f.poly(shield, hi, body=False)
        f.poly([p(20.0, 36.0), p(26.0, 36.0), p(28.0, 40.0), p(28.0, 60.0), p(26.0, 64.0), p(20.0, 64.0)], mid, body=False)
        f.ink(shield + [shield[0]], 0.8 * u, lo)
        f.ink([p(13.0, 43.0), p(26.0, 57.0)], 0.6 * u, lo)
        f.ink([p(26.0, 43.0), p(13.0, 57.0)], 0.6 * u, lo)
        f.ellipse(*p(19.5, 50.0), 2.6 * u, 2.6 * u, hi, body=False)
    else:
        # The side-blown horn: its mouth hole at the lips, its bell out to the
        # side, with rings carved round it.
        f.poly([p(3.0, 18.4), p(3.0, 21.6), p(-26.0, 15.0), p(-28.0, 7.0)], hi, body=False)
        f.poly([p(3.0, 20.0), p(3.0, 21.6), p(-26.0, 15.0), p(-27.0, 11.0)], mid, body=False)
        for k in range(4):
            x = -6.0 - k * 5.0
            f.ink([p(x, 19.6 - k * 1.1 - 2.0 - k * 0.6), p(x, 20.2 - k * 0.9 + 0.6)], 0.6 * u, lo)
        f.ellipse(*p(-27.0, 11.0), 1.6 * u, 4.2 * u, lo if shadow else BRASS_DARK, body=False)
        for x, y in ((-17.0, 19.0), (-6.0, 22.0)):
            f.ellipse(*p(x, y), 2.6 * u, 2.6 * u, hi, body=False)


def _plaque(f: K.Frame, x0: float, y0: float, x1: float, y1: float, kind: str, seed: str) -> None:
    """A brass plaque from (`x0`, `y0`) to (`x1`, `y1`): a raised edge, a
    ground of incised flowers, green patina in its hollows, nail holes at
    its corners, and a figure of the court in high relief."""
    w, h = x1 - x0, y1 - y0
    edge = max(2.0, w * 0.06)
    f.poly(_rect(x0, y0, x1, y1), BRASS_SHADE)
    f.poly(_rect(x0 + edge, y0 + edge, x1 - edge, y1 - edge), BRASS, body=False)
    f.ink([(x0 + 1.0, y0 + 1.0), (x1 - 1.0, y0 + 1.0)], max(0.6, edge * 0.3), BRASS_LIGHT)
    f.ink([(x0 + 1.0, y0 + 1.0), (x0 + 1.0, y1 - 1.0)], max(0.6, edge * 0.3), BRASS_LIGHT)
    # The ground of flowers, in a grid.
    gap = max(7.0, w * 0.17)
    s = gap * 0.46
    rows = int((h - 2 * edge) // gap)
    cols = int((w - 2 * edge) // gap)
    ox = x0 + (w - (cols - 1) * gap) / 2.0
    oy = y0 + (h - (rows - 1) * gap) / 2.0
    for r in range(rows):
        for c in range(cols):
            _flower(f, ox + c * gap, oy + r * gap, s)
    # Green patina where the hollows of the ground hold the damp.
    rng = random.Random(seed)
    for _ in range(int(w * h / 420.0)):
        x = rng.uniform(x0 + edge + 2.0, x1 - edge - 2.0)
        y = rng.uniform(y0 + edge + 2.0, y1 - edge - 2.0)
        r = rng.uniform(0.04, 0.09) * w
        f.ellipse(x, y, r, r * 0.7, K.alpha(PATINA, 0.45), body=False)
        f.ellipse(x - r * 0.3, y - r * 0.2, r * 0.4, r * 0.3, K.alpha(PATINA_LIGHT, 0.45), body=False)
    # The figure, a little proud of the ground: its shade falls down-right.
    u = (h - 2 * edge) * 0.86 / 100.0
    top = y0 + edge + (h - 2 * edge) * 0.07
    cx = (x0 + x1) / 2.0
    _court_figure(f, cx, top, u, kind, shadow=True)
    _court_figure(f, cx, top, u, kind)
    # The nail holes at the corners, through the edge.
    r = max(1.0, w * 0.025)
    for x, y in ((x0 + edge * 1.8, y0 + edge * 1.8), (x1 - edge * 1.8, y0 + edge * 1.8), (x0 + edge * 1.8, y1 - edge * 1.8), (x1 - edge * 1.8, y1 - edge * 1.8)):
        f.ellipse(x, y, r * 1.6, r * 1.6, BRASS_LIGHT, body=False)
        f.dot(x, y, r, (40, 26, 20, 255))


# ---------------------------------------------------------------------------
# The brass furnace.
# ---------------------------------------------------------------------------


def _draw_furnace(anim: str, i: int, n: int):
    w, h = FURNACE_FRAME
    f = K.Frame(FURNACE_FRAME)
    foot = h - 8.0
    t = _phase(i, n)
    cyc = math.tau * t
    cx = 104.0
    pump = (0.5 + 0.5 * math.sin(cyc), 0.5 + 0.5 * math.sin(cyc + math.pi))
    heat = 0.75 + 0.25 * math.sin(cyc * 2.0)
    # Tongs that lean on the far side of the furnace.
    f.limb([(144.0, foot - 2.0), (150.0, 112.0)], 2.4, (70, 64, 66, 255))
    f.limb([(140.0, foot - 2.0), (148.0, 112.0)], 2.0, (90, 84, 86, 255))
    # The body of the furnace: thick clay, wider at its foot, cracked by the heat.
    body = [(68.0, foot), (140.0, foot), (136.0, 124.0), (128.0, 106.0), (80.0, 106.0), (72.0, 124.0)]
    f.poly(body, CLAY)
    f.poly([(112.0, foot), (140.0, foot), (136.0, 124.0), (128.0, 106.0), (112.0, 106.0)], CLAY_SHADE, body=False)
    f.poly([(74.0, 128.0), (80.0, 110.0), (86.0, 110.0), (82.0, 150.0), (76.0, 170.0)], CLAY_LIGHT, body=False)
    for y in (140.0, 160.0):
        f.ink([(72.0, y), (138.0, y)], 1.0, CLAY_SHADE)
    for pts in (((96.0, 120.0), (100.0, 132.0), (96.0, 142.0)), ((120.0, 150.0), (124.0, 164.0), (120.0, 174.0))):
        f.ink(list(pts), 1.2, K.alpha(EMBER, 0.55 + 0.35 * heat))
    # The mouth: a rim of clay round a bed of charcoal with live embers.
    f.ellipse(cx, 106.0, 28.0, 7.5, CLAY_LIGHT)
    f.ellipse(cx, 106.5, 23.0, 5.0, COAL, body=False)
    for k in range(10):
        a = math.tau * k / 10.0
        x, y = cx + math.cos(a) * 18.0, 106.5 + math.sin(a) * 3.4
        g = 0.5 + 0.5 * math.sin(cyc * 2.0 + k * 1.7)
        f.ellipse(x, y, 2.4, 1.4, EMBER_HOT if g > 0.7 else EMBER, body=False)
    # The crucible in the coals: a small thick pot of clay, full of molten brass.
    f.poly([(91.0, 107.0), (117.0, 107.0), (119.0, 90.0), (89.0, 90.0)], CRUCIBLE)
    f.poly([(106.0, 107.0), (117.0, 107.0), (119.0, 90.0), (108.0, 90.0)], CRUCIBLE_SHADE, body=False)
    f.ellipse(cx, 90.0, 15.0, 4.0, CRUCIBLE)
    f.ellipse(cx, 90.0, 12.0, 2.8, MOLTEN, body=False)
    f.ellipse(cx - 3.0, 89.4, 5.0, 1.2, K.alpha(K.WHITE, 0.7 * heat), body=False)
    f.glow(cx, 92.0, 13.0 + 3.0 * heat, K.alpha(EMBER, 0.20 * heat))
    f.glow(cx, 92.0, 7.0, K.alpha(EMBER_HOT, 0.6))
    # The sparks that the blast lifts out of the mouth.
    for k in range(7):
        s = (t + k / 7.0) % 1.0
        x = cx + (k - 3) * 4.0 + 10.0 * math.sin(math.tau * (s * 0.8 + k * 0.29)) * s
        y = 84.0 - s * 66.0
        r = 1.8 * (1.0 - s) + 0.6
        f.glow(x, y, r * 2.2, K.alpha(EMBER, 0.5 * (1.0 - s)))
        f.dot(x, y, r, K.alpha(EMBER_HOT, 1.0 - s * 0.8))
    # The tuyere: a pipe of clay that takes the wind into the foot of the fire.
    f.limb([(52.0, 168.0), (76.0, 162.0)], 8.0, CLAY_SHADE)
    f.ellipse(78.0, 162.0, 3.0, 4.0, COAL, body=False)
    # The two bellows of goatskin, pumped in turn. Each is a whole skin: the
    # stumps of its legs stick out, its neck is a pipe to the tuyere, and
    # its open back is held by two sticks that the helper opens to fill it
    # and shuts and pushes down to blow.
    for k, (bx, p) in enumerate(((27.0, pump[0]), (54.0, pump[1]))):
        ry = 6.0 + 8.0 * p
        by = foot - ry
        f.limb([(bx + 10.0, foot - 5.0), (60.0, 168.0)], 3.6, GOATSKIN_SHADE)
        for sx, sy, ex in ((-1.0, 0.2, -4.0), (1.0, 0.5, 4.0)):
            f.limb([(bx + sx * 11.0, by + sy * ry), (bx + sx * 11.0 + ex, by + sy * ry + 3.0)], 3.4, GOATSKIN_SHADE)
        f.ellipse(bx, by, 14.0, ry, GOATSKIN)
        f.ellipse(bx + 4.0, by + ry * 0.35, 9.0, ry * 0.55, GOATSKIN_SHADE, body=False)
        for sx, sy in ((-6.0, -0.2), (3.0, 0.15), (-1.0, 0.5)):
            f.ellipse(bx + sx, by + sy * ry, 2.4, 1.5, GOAT_SPOT, body=False)
        top = by - ry + 1.0
        gap = 1.0 + 3.0 * p
        f.limb([(bx - 10.0, top - gap), (bx + 10.0, top - gap)], 2.4, WOOD)
        f.limb([(bx - 10.0, top + 0.5), (bx + 10.0, top + 0.5)], 2.4, WOOD_LIGHT)
        if p > 0.4:
            f.poly([(bx - 8.0, top - gap + 1.0), (bx + 8.0, top - gap + 1.0), (bx + 8.0, top - 0.5), (bx - 8.0, top - 0.5)], COAL, body=False)
        # A breath of heat at the tuyere when the bag empties.
        if p < 0.3:
            f.glow(80.0, 160.0, 4.0, K.alpha(EMBER_HOT, 0.5))
    # Charcoal on the ground.
    for x, r in ((128.0, 4.0), (134.0, 3.0), (60.0, 3.4), (66.0, 2.6)):
        f.ellipse(x, foot - r * 0.8, r, r * 0.8, COAL)
    return A.finish(f, width=1.4)


# ---------------------------------------------------------------------------
# Manillas in a basket.
# ---------------------------------------------------------------------------


def _manilla(f: K.Frame, cx: float, cy: float, r: float, turn: float, colour, shade) -> None:
    """An open bracelet of brass in the shape of a horseshoe, with a flared
    knob at each end."""
    pts = []
    for k in range(17):
        a = math.radians(turn + 50.0 + k * (260.0 / 16.0))
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r * 0.62))
    f.limb(pts, r * 0.34, colour)
    f.ink(pts[2:-2], r * 0.12, K.shade(colour, 1.18))
    for x, y in (pts[0], pts[-1]):
        f.ellipse(x, y, r * 0.3, r * 0.26, shade)


def _draw_manillas(anim: str, i: int, n: int):
    w, h = MANILLAS_FRAME
    f = K.Frame(MANILLAS_FRAME)
    foot = h - 5.0
    rng = random.Random("history_manillas")
    # The back of the basket and the dark inside.
    bx0, bx1, rim = 62.0, 120.0, 28.0
    f.ellipse((bx0 + bx1) / 2.0, rim, (bx1 - bx0) / 2.0, 5.5, STRAW_SHADE)
    f.ellipse((bx0 + bx1) / 2.0, rim + 0.5, (bx1 - bx0) / 2.0 - 3.0, 4.0, STRAW_DARK, body=False)
    # The manillas that heap up out of the basket.
    for k in range(7):
        x = rng.uniform(bx0 + 10.0, bx1 - 10.0)
        y = rim - 2.0 - rng.uniform(0.0, 9.0) + abs(x - (bx0 + bx1) / 2.0) * 0.25
        _manilla(f, x, y, rng.uniform(7.5, 9.5), rng.uniform(0.0, 360.0), BRASS if k % 2 else BRASS_LIGHT, BRASS_SHADE)
    # The front of the basket: woven strips that cross, and a bound rim.
    front = [(bx0, rim), (bx1, rim), (bx1 - 5.0, foot), (bx0 + 5.0, foot)]
    f.poly(front, STRAW)
    f.poly([(bx1 - 14.0, rim), (bx1, rim), (bx1 - 5.0, foot), (bx1 - 18.0, foot)], STRAW_SHADE, body=False)
    for k in range(9):
        x = bx0 + 3.0 + k * 6.6
        f.ink([(x, rim + 3.0), (x - 2.0, foot - 1.0)], 0.9, STRAW_DARK)
    for y in range(int(rim) + 6, int(foot), 5):
        f.ink([(bx0 + 2.0, float(y)), (bx1 - 3.0, float(y))], 0.7, K.alpha(STRAW_DARK, 0.6))
    f.limb([(bx0, rim), (bx1, rim)], 3.4, STRAW_SHADE)
    f.ink([(bx0 + 2.0, rim - 0.6), (bx1 - 2.0, rim - 0.6)], 0.8, STRAW)
    # The heap on the ground to the left, and a few that slid down.
    for k in range(9):
        x = rng.uniform(14.0, 60.0)
        y = foot - 4.0 - max(0.0, 12.0 - abs(x - 36.0) * 0.5) * rng.uniform(0.4, 1.0)
        _manilla(f, x, y, rng.uniform(7.0, 9.0), rng.uniform(0.0, 360.0), BRASS if k % 3 else BRASS_LIGHT, BRASS_SHADE)
    _manilla(f, 108.0, foot - 4.0, 7.0, 200.0, BRASS, BRASS_SHADE)
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# A brass plaque.
# ---------------------------------------------------------------------------


def _draw_plaque(anim: str, i: int, n: int):
    w, h = PLAQUE_FRAME
    f = K.Frame(PLAQUE_FRAME)
    _plaque(f, 10.0, 6.0, w - 10.0, h - 6.0, "warrior", "history_benin_plaque")
    return A.finish(f, width=1.4)


# ---------------------------------------------------------------------------
# The palace.
# ---------------------------------------------------------------------------


def _shingles(f: K.Frame, left: Callable[[float], float], right: Callable[[float], float], y0: float, y1: float, row: float, width: float,
              seed: str) -> None:
    """Rows of wooden shingles between the edges `left(y)` and `right(y)`:
    a line under each row and the joints of the shingles, set off by half
    a shingle from row to row."""
    rng = random.Random(seed)
    y = y0 + row
    k = 0
    while y < y1 - 1.0:
        xl, xr = left(y), right(y)
        f.ink([(xl + 1.0, y), (xr - 1.0, y)], 1.2, SHINGLE_SHADE)
        f.ink([(xl + 1.0, y + 1.2), (xr - 1.0, y + 1.2)], 0.8, SHINGLE_LIGHT)
        x = xl + (width * 0.5 if k % 2 else 0.0) + rng.uniform(1.0, 3.0)
        while x < xr - 3.0:
            f.ink([(x, y - row + 1.6), (x, y - 0.6)], 0.9, SHINGLE_SHADE)
            x += width + rng.uniform(-2.0, 2.0)
        y += row
        k += 1


def _bird(f: K.Frame, cx: float, cy: float, s: float) -> None:
    """A brass bird with its wings spread, on a rod: a long beak, a fan of a
    tail, and the feathers of each wing as a scalloped edge."""
    f.limb([(cx, cy + 6.0 * s), (cx, cy + 22.0 * s)], 2.0 * s, BRASS_SHADE)
    for side in (-1.0, 1.0):
        wing = [(cx + side * 3.0 * s, cy - 1.0 * s), (cx + side * 14.0 * s, cy - 12.0 * s), (cx + side * 30.0 * s, cy - 17.0 * s),
                (cx + side * 34.0 * s, cy - 14.0 * s)]
        for k in range(5):
            x = 34.0 - k * 6.0
            wing.append((cx + side * (x - 3.0) * s, cy + (-8.0 + k * 2.4) * s))
            wing.append((cx + side * (x - 6.0) * s, cy + (-11.0 + k * 2.6) * s))
        wing.append((cx + side * 4.0 * s, cy + 4.0 * s))
        f.poly(wing, BRASS if side > 0 else BRASS_LIGHT)
        f.ink([(cx + side * 6.0 * s, cy - 2.0 * s), (cx + side * 28.0 * s, cy - 14.0 * s)], 0.9 * s, BRASS_SHADE)
    f.poly([(cx - 3.0 * s, cy + 4.0 * s), (cx + 3.0 * s, cy + 4.0 * s), (cx + 7.0 * s, cy + 13.0 * s), (cx - 7.0 * s, cy + 13.0 * s)], BRASS_SHADE)
    for x in (-4.0, 0.0, 4.0):
        f.ink([(cx, cy + 5.0 * s), (cx + x * s, cy + 12.0 * s)], 0.7 * s, BRASS_DARK)
    f.ellipse(cx, cy + 1.0 * s, 5.0 * s, 6.0 * s, BRASS)
    f.ellipse(cx + 3.0 * s, cy - 7.0 * s, 4.0 * s, 4.0 * s, BRASS)
    f.poly([(cx + 6.0 * s, cy - 8.4 * s), (cx + 17.0 * s, cy - 4.0 * s), (cx + 15.0 * s, cy - 3.0 * s), (cx + 6.0 * s, cy - 5.6 * s)], BRASS_LIGHT)
    f.dot(cx + 4.4 * s, cy - 7.6 * s, 0.9 * s, BRASS_DARK)


def _python(f: K.Frame, path: List[Point], w0: float, w1: float) -> None:
    """A brass python along `path` from its tail to its head: it thickens
    to the head, has a row of diamonds on its back, and its head goes
    down."""
    m = len(path)
    for k in range(m - 1):
        u = k / max(1, m - 2)
        f.limb([path[k], path[k + 1]], w0 + (w1 - w0) * u, BRASS)
    for k in range(2, m - 1, 2):
        u = k / max(1, m - 2)
        x, y = path[k]
        d = (w0 + (w1 - w0) * u) * 0.32
        f.poly([(x, y - d), (x + d, y), (x, y + d), (x - d, y)], BRASS_SHADE, body=False)
    for k in range(m - 1):
        x0, y0 = path[k]
        x1, y1 = path[k + 1]
        u = k / max(1, m - 2)
        f.ink([(x0 - (w0 + (w1 - w0) * u) * 0.25, y0), (x1 - (w0 + (w1 - w0) * u) * 0.25, y1)], 0.8, BRASS_LIGHT)
    hx, hy = path[-1]
    f.ellipse(hx, hy + w1 * 0.6, w1 * 0.75, w1 * 1.1, BRASS)
    f.ellipse(hx, hy + w1 * 0.4, w1 * 0.5, w1 * 0.6, BRASS_LIGHT, body=False)
    for s in (-1.0, 1.0):
        f.dot(hx + s * w1 * 0.4, hy + w1 * 0.9, w1 * 0.14, BRASS_DARK)


def _draw_palace(anim: str, i: int, n: int):
    w, h = PALACE_FRAME
    f = K.Frame(PALACE_FRAME)
    foot = h - 8.0
    # The steep roof of shingles over the whole wall.
    eave, ridge = 238.0, 168.0
    f.poly([(6.0, eave), (w - 6.0, eave), (w - 40.0, ridge), (40.0, ridge)], SHINGLE)
    f.poly([(6.0, eave), (w - 6.0, eave), (w - 10.0, eave - 8.0), (10.0, eave - 8.0)], SHINGLE_SHADE, body=False)

    def roof_l(y: float) -> float:
        return 40.0 - 34.0 * (y - ridge) / (eave - ridge)

    def roof_r(y: float) -> float:
        return w - roof_l(y)

    _shingles(f, roof_l, roof_r, ridge, eave - 8.0, 11.0, 22.0, "palace:roof")
    f.limb([(40.0, ridge), (w - 40.0, ridge)], 4.0, SHINGLE_SHADE)
    # The long wall of red earth, with ridges along it and a dark plinth.
    f.poly(_rect(14.0, eave, w - 14.0, foot), LATERITE)
    f.poly(_rect(14.0, eave, w - 14.0, eave + 8.0), LATERITE_SHADE, body=False)
    f.poly(_rect(14.0, foot - 12.0, w - 14.0, foot), LATERITE_SHADE, body=False)
    _ridges(f, 14.0, w - 14.0, eave + 8.0, foot - 12.0, 15.0, LATERITE_LIGHT, LATERITE_DARK)
    # Patches where the earth was polished smooth.
    rng = random.Random("palace:wall")
    for _ in range(8):
        x, y = rng.uniform(30.0, w - 30.0), rng.uniform(eave + 20.0, foot - 26.0)
        f.ellipse(x, y, rng.uniform(10.0, 22.0), rng.uniform(4.0, 6.0), K.alpha(LATERITE_LIGHT, 0.35), body=False)
    # A doorway with a carved door, and a row of brass plaques on the wall.
    f.poly(_rect(84.0, 284.0, 140.0, foot), WOOD_BLACK, body=False)
    f.poly(_rect(88.0, 290.0, 136.0, foot), WOOD_DARK, body=False)
    for x in (100.0, 112.0, 124.0):
        f.ink([(x, 294.0), (x, foot - 4.0)], 1.0, WOOD_BLACK)
    for y in (304.0, 328.0, 352.0):
        for x in (94.0, 106.0, 118.0, 130.0):
            f.dot(x, y, 1.8, BRASS)
    f.limb([(78.0, 282.0), (146.0, 282.0)], 5.0, WOOD)
    for k, x in enumerate((392.0, 432.0, 472.0)):
        _plaque(f, x - 15.0, 268.0, x + 15.0, 310.0, "warrior" if k % 2 == 0 else "horn", f"palace:plaque:{k}")
    # The turret: a tower of earth that rises through the roof, and its tall
    # pointed spire of shingles.
    tx, tower_top = 300.0, 150.0
    f.poly(_rect(tx - 28.0, tower_top, tx + 28.0, foot), LATERITE)
    f.poly(_rect(tx + 12.0, tower_top, tx + 28.0, foot), LATERITE_SHADE, body=False)
    _ridges(f, tx - 28.0, tx + 28.0, tower_top + 6.0, foot - 12.0, 15.0, LATERITE_LIGHT, LATERITE_DARK)
    apex, base = 50.0, tower_top + 4.0
    f.poly([(tx - 31.0, base), (tx + 31.0, base), (tx, apex)], SHINGLE)
    f.poly([(tx + 5.0, base), (tx + 31.0, base), (tx, apex)], SHINGLE_SHADE, body=False)

    def spire_l(y: float) -> float:
        return tx - 31.0 * (y - apex) / (base - apex)

    def spire_r(y: float) -> float:
        return tx + 31.0 * (y - apex) / (base - apex)

    _shingles(f, spire_l, spire_r, apex + 4.0, base - 2.0, 9.0, 12.0, "palace:spire")
    f.ink([(tx - 31.0, base), (tx, apex), (tx + 31.0, base)], 1.4, SHINGLE_LIGHT)
    f.limb([(tx - 32.0, base), (tx + 32.0, base)], 3.0, SHINGLE_SHADE)
    # The brass python goes down the front of the spire and the tower, head
    # first.
    path = []
    for k in range(41):
        s = k / 40.0
        y = apex + 22.0 + s * (338.0 - apex - 22.0)
        spread = min(15.0, 0.38 * 31.0 * (y - apex) / (base - apex)) if y < base else 15.0
        path.append((tx + spread * math.sin(s * math.tau * 3.4 + 0.6), y))
    _python(f, path, 3.0, 10.0)
    # The brass bird on the point.
    _bird(f, tx, 34.0, 1.0)
    return A.finish(f, width=1.6)


# ---------------------------------------------------------------------------
# The palace gate.
# ---------------------------------------------------------------------------


def _draw_gate(anim: str, i: int, n: int):
    w, h = GATE_FRAME
    f = K.Frame(GATE_FRAME)
    foot = h - 4.0
    # A little roof of shingles over the gate.
    f.poly([(4.0, 34.0), (92.0, 34.0), (80.0, 8.0), (16.0, 8.0)], SHINGLE)
    f.poly([(4.0, 34.0), (92.0, 34.0), (90.0, 29.0), (6.0, 29.0)], SHINGLE_SHADE, body=False)
    _shingles(f, lambda y: 16.0 - 12.0 * (y - 8.0) / 26.0, lambda y: 80.0 + 12.0 * (y - 8.0) / 26.0, 8.0, 30.0, 7.0, 10.0, "gate:roof")
    # The frame of red earth, with ridges along it.
    f.poly(_rect(8.0, 34.0, 88.0, foot), LATERITE)
    f.poly(_rect(74.0, 34.0, 88.0, foot), LATERITE_SHADE, body=False)
    _ridges(f, 8.0, 88.0, 36.0, foot, 16.0, LATERITE_LIGHT, LATERITE_DARK)
    # The opening and the two leaves of carved wood.
    x0, x1, y0 = 20.0, 76.0, 70.0
    f.poly(_rect(x0 - 2.0, y0 - 2.0, x1 + 2.0, foot), WOOD_BLACK, body=False)
    f.poly(_rect(x0, y0, x1, foot), WOOD_DARK, body=False)
    mid = (x0 + x1) / 2.0
    f.ink([(mid, y0), (mid, foot)], 1.4, WOOD_BLACK)
    # The carved panels: each raised, with a band of chevrons cut across it.
    for lx in (x0 + 3.0, mid + 3.0):
        for py0, py1 in ((150.0, 236.0), (246.0, 300.0), (310.0, foot - 8.0)):
            f.poly(_rect(lx, py0, lx + 22.0, py1), WOOD, body=False)
            f.poly(_rect(lx + 16.0, py0, lx + 22.0, py1), WOOD_DARK, body=False)
            f.ink([(lx, py0 + 0.6), (lx + 22.0, py0 + 0.6)], 0.9, WOOD_LIGHT)
            y = py0 + 8.0
            while y < py1 - 6.0:
                f.ink([(lx + 3.0, y + 3.0), (lx + 11.0, y), (lx + 19.0, y + 3.0)], 0.9, WOOD_BLACK)
                y += 9.0
    # The brass studs in rows on the leaves.
    for y in (78.0, 94.0, 142.0, 241.0, 305.0, foot - 4.0):
        for x in (x0 + 4.0, x0 + 14.0, mid - 4.0, mid + 4.0, x1 - 14.0, x1 - 4.0):
            f.dot(x, y, 2.0, BRASS_SHADE)
            f.dot(x - 0.5, y - 0.5, 1.0, BRASS_LIGHT)
    # The brass plaque on the gate, and two rings to pull it by.
    _plaque(f, mid - 15.0, 100.0, mid + 15.0, 138.0, "warrior", "gate:plaque")
    for s in (-1.0, 1.0):
        f.ellipse(mid + s * 5.0, 268.0, 3.6, 4.4, BRASS_SHADE, body=False)
        f.ellipse(mid + s * 5.0, 268.0, 2.0, 2.8, WOOD_DARK, body=False)
    # The lintel of dark wood over the opening.
    f.poly(_rect(14.0, y0 - 10.0, 82.0, y0 - 1.0), WOOD_BLACK)
    for x in (24.0, 40.0, 56.0, 72.0):
        f.dot(x, y0 - 5.5, 1.6, BRASS)
    return A.finish(f, width=1.6)


# ---------------------------------------------------------------------------
# The museum case.
# ---------------------------------------------------------------------------


def _letter(f: K.Frame, ch: str, x: float, y: float, lw: float, lh: float, width: float, colour) -> None:
    """One capital letter of `ch` in ink strokes, in a box `lw` by `lh` from
    its top left (`x`, `y`)."""
    if ch == "O":
        pts = K.ellipse_points(x + lw / 2.0, y + lh / 2.0, lw / 2.0, lh / 2.0, 20)
        f.ink(pts + [pts[0]], width, colour)
    elif ch == "N":
        f.ink([(x, y + lh), (x, y), (x + lw, y + lh), (x + lw, y)], width, colour)
    elif ch == "L":
        f.ink([(x, y), (x, y + lh), (x + lw, y + lh)], width, colour)
    elif ch == "A":
        f.ink([(x, y + lh), (x + lw / 2.0, y), (x + lw, y + lh)], width, colour)
        f.ink([(x + lw * 0.22, y + lh * 0.62), (x + lw * 0.78, y + lh * 0.62)], width, colour)


def _draw_case(anim: str, i: int, n: int):
    w, h = CASE_FRAME
    f = K.Frame(CASE_FRAME)
    foot = h - 8.0
    # The stand of dark wood: a top, an apron with a small brass label, legs.
    for x in (28.0, 132.0):
        f.limb([(x, 168.0), (x, foot - 1.0)], 6.0, WOOD_DARK)
        f.ellipse(x, foot - 2.0, 4.6, 2.0, WOOD_BLACK)
    f.limb([(30.0, 200.0), (130.0, 200.0)], 3.0, WOOD_DARK)
    f.poly(_rect(20.0, 156.0, 140.0, 172.0), WOOD_DARK)
    f.ink([(22.0, 157.0), (138.0, 157.0)], 1.0, WOOD_LIGHT)
    f.poly(_rect(70.0, 160.0, 90.0, 168.0), BRASS_SHADE, body=False)
    f.ink([(73.0, 164.0), (87.0, 164.0)], 0.8, BRASS_DARK)
    f.poly(_rect(14.0, 146.0, 146.0, 156.0), WOOD)
    f.poly(_rect(14.0, 152.0, 146.0, 156.0), WOOD_DARK, body=False)
    # The plinth in the case, and the plaque on its little stand.
    f.poly(_rect(24.0, 134.0, 136.0, 146.0), WOOD_BLACK)
    f.limb([(62.0, 134.0), (62.0, 126.0)], 4.0, WOOD_DARK)
    _plaque(f, 32.0, 40.0, 92.0, 128.0, "horn", "history_museum_case")
    # The card: it leans on the plinth beside the plaque.
    card = [(96.0, 104.0), (132.0, 102.0), (133.0, 133.0), (97.0, 134.0)]
    f.poly(card, CARD)
    f.poly([(96.0, 128.0), (133.0, 127.0), (133.0, 133.0), (97.0, 134.0)], CARD_SHADE, body=False)
    for k, ch in enumerate("ON"):
        _letter(f, ch, 105.0 + k * 10.0, 107.0, 7.0, 8.0, 1.2, CARD_INK)
    for k, ch in enumerate("LOAN"):
        _letter(f, ch, 99.5 + k * 8.0, 119.0, 5.6, 7.0, 1.1, CARD_INK)
    # The glass: a faint tint, light along its edges and two streaks of
    # reflection over the plaque.
    f.poly(_rect(24.0, 26.0, 136.0, 134.0), K.alpha(GLASS, 0.16), body=False)
    for x0 in (40.0, 56.0):
        f.poly([(x0, 30.0), (x0 + 10.0, 30.0), (x0 - 12.0, 130.0), (x0 - 22.0, 130.0)], K.alpha(K.WHITE, 0.16), body=False)
    f.poly([(110.0, 30.0), (114.0, 30.0), (100.0, 96.0), (96.0, 96.0)], K.alpha(K.WHITE, 0.22), body=False)
    # The frame of the case, and its lid.
    for pts in (((24.0, 26.0), (24.0, 134.0)), ((136.0, 26.0), (136.0, 134.0))):
        f.limb(list(pts), 3.2, WOOD_DARK)
    f.poly(_rect(18.0, 16.0, 142.0, 26.0), WOOD_DARK)
    f.ink([(20.0, 17.0), (140.0, 17.0)], 1.0, WOOD_LIGHT)
    return A.finish(f, width=1.4)


# ---------------------------------------------------------------------------
# Publication.
# ---------------------------------------------------------------------------

SCENERY = ["prop", "scenery", "history", "africa"]
DOOR = ["prop", "door", "lock", "history", "africa"]

FRAMES: Dict[str, Tuple[int, int]] = {
    "history_brass_furnace": FURNACE_FRAME,
    "history_manillas": MANILLAS_FRAME,
    "history_benin_plaque": PLAQUE_FRAME,
    "history_benin_palace": PALACE_FRAME,
    "history_benin_palace_gate": GATE_FRAME,
    "history_museum_case": CASE_FRAME,
}
DRAW: Dict[str, Callable] = {
    "history_brass_furnace": _draw_furnace,
    "history_manillas": _draw_manillas,
    "history_benin_plaque": _draw_plaque,
    "history_benin_palace": _draw_palace,
    "history_benin_palace_gate": _draw_gate,
    "history_museum_case": _draw_case,
}
DISPLAY = {
    "history_brass_furnace": "Brass Furnace",
    "history_manillas": "Manillas",
    "history_benin_plaque": "Benin Plaque",
    "history_benin_palace": "Benin Palace",
    "history_museum_case": "Museum Case",
}
ROWS = {"history_brass_furnace": LOOP}


def _foot(name: str) -> Dict[str, Tuple[float, float]]:
    w, h = FRAMES[name]
    return {"foot": (w / 2.0, float(h))}


TARGETS: Dict[str, dict] = {
    name: _publisher(name, DISPLAY[name], ROWS.get(name, STILL), FRAMES[name], DRAW[name], _foot(name), "Scenery", SCENERY) for name in DISPLAY
}
TARGETS["history_benin_palace_gate"] = _publisher("history_benin_palace_gate", "Benin Palace Gate", STILL, GATE_FRAME, _draw_gate, {"foot": (48.0, 384.0)},
                                                  "Door", DOOR, forward=(0.0, -1.0))
