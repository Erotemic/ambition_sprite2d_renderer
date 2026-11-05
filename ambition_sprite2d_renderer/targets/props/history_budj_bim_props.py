"""The props of Budj Bim (the History dimension), in Gunditjmara country,
south-west Victoria, Australia.

Budj Bim is a volcano. Its lava flow, about 37,000 years old, runs south to
Tae Rak (Lake Condah) and the sea. On the flow the Gunditjmara cut channels
and built weirs and ponds of basalt to trap, hold and grow kooyang
(short-finned eels) for at least 6,600 years. It is one of the oldest
systems of aquaculture in the world, and it has been on the World Heritage
list of UNESCO since 2019. The Gunditjmara built houses with low round walls
of stacked basalt, roofed with branches and turf or bark. They smoked eels in
hollow manna gums and traded them.

These props are drawn in the cel style of the dimension's cast
(`targets/characters/_history_americas_kit.py`): flat colour, one shade, a
bold warm outline. They show the skill of the people who made these things
and how old the system is. There are no people and no sacred things.

- ``history_eel_weir``: scenery, a low weir of stacked basalt across a
  channel, about 1.4 m wide, with a gap in its middle; a long woven eel
  trap of plaited sedge is set in the gap, held by a stake, and the water
  runs through it. Water lies on both sides. Its ``idle`` row moves the
  water.
- ``history_stone_house``: scenery, the house of a Gunditjmara family: a
  ring of stacked basalt about 1 m high and 3 m across, with a domed roof
  of bent branches covered with turf and sheets of bark, and a low doorway
  in the wall.
- ``history_smoking_tree``: scenery, a hollow manna gum where eels are
  smoked: a pale trunk with ribbons of bark, a hollow at its foot that the
  fire has made black, a small fire low in it, eels hung on a stick across
  the hollow, and thin smoke that comes out of it and out of a hole higher
  on the trunk. Its ``idle`` row moves the smoke and the fire.

The numbers are frame pixels; the game shows each prop at half its frame.
No drop shadows: the game draws them.
"""

from __future__ import annotations

import math
import random
from typing import Callable, Dict, List, Sequence, Tuple

from ..characters import _art_cast_kit as K
from ..characters import _history_americas_kit as A
from .art_props import _publisher

Point = Tuple[float, float]
RGBA = Tuple[int, int, int, int]
STILL: List[Tuple[str, int, int]] = [("idle", 1, 1000)]
LOOP: List[Tuple[str, int, int]] = [("idle", 8, 130)]

EEL_WEIR_FRAME = (192, 96)
STONE_HOUSE_FRAME = (256, 160)
SMOKING_TREE_FRAME = (192, 320)

# The basalt of the flow, its moss and lichen.
BASALT = (84, 82, 80, 255)
BASALT_LIGHT = (124, 122, 116, 255)
BASALT_SHADE = (60, 58, 58, 255)
BASALT_DARK = (40, 38, 38, 255)
MOSS = (96, 122, 64, 255)
MOSS_LIGHT = (136, 160, 86, 255)
LICHEN = (184, 190, 160, 255)
LICHEN_ORANGE = (200, 144, 76, 255)
# The water of the channels and the wetland.
WATER = (92, 112, 114, 225)
WATER_DEEP = (68, 86, 90, 235)
WATER_LIGHT = (184, 196, 190, 255)
FOAM = (226, 232, 226, 255)
# Sedge and the woven trap.
SEDGE = (196, 170, 112, 255)
SEDGE_LIGHT = (222, 200, 146, 255)
SEDGE_SHADE = (150, 124, 76, 255)
SEDGE_DARK = (110, 88, 52, 255)
GREEN_SEDGE = (118, 132, 72, 255)
GREEN_SEDGE_LIGHT = (156, 168, 96, 255)
STAKE = (112, 84, 56, 255)
STAKE_LIGHT = (146, 112, 78, 255)
EARTH = (96, 84, 66, 255)
EARTH_SHADE = (70, 60, 48, 255)
# The roof of the house: branches, turf and bark.
BRANCH = (110, 82, 56, 255)
BRANCH_LIGHT = (146, 112, 78, 255)
TURF = (104, 118, 66, 255)
TURF_LIGHT = (138, 150, 86, 255)
TURF_SHADE = (76, 88, 52, 255)
BARK_SHEET = (126, 92, 62, 255)
BARK_SHEET_LIGHT = (160, 122, 84, 255)
BARK_SHEET_SHADE = (92, 64, 44, 255)
INTERIOR = (30, 26, 24, 255)
# The manna gum, its fire and its smoke.
GUM = (222, 214, 196, 255)
GUM_LIGHT = (240, 236, 222, 255)
GUM_SHADE = (180, 170, 150, 255)
GUM_RIBBON = (168, 130, 94, 255)
GUM_RIBBON_DARK = (126, 94, 66, 255)
LEAF = (106, 124, 94, 255)
LEAF_LIGHT = (140, 156, 118, 255)
LEAF_SHADE = (78, 94, 72, 255)
CHAR = (44, 36, 32, 255)
CHAR_EDGE = (82, 66, 54, 255)
EMBER = (230, 110, 48, 255)
FIRE = (255, 190, 70, 255)
FIRE_HOT = (255, 238, 170, 255)
EEL = (96, 76, 46, 255)
EEL_LIGHT = (140, 116, 72, 255)
EEL_DARK = (60, 46, 30, 255)
STICK = (96, 70, 48, 255)
SMOKE = (176, 174, 170, 255)


def _ring(cx: float, cy: float, rx: float, ry: float, a0: float = 0.0, a1: float = 360.0, count: int = 36) -> List[Point]:
    """Points on an ellipse from the angle `a0` to `a1` (degrees; 0 is to
    the right, 90 is down)."""
    out: List[Point] = []
    for k in range(count + 1):
        a = math.radians(a0 + (a1 - a0) * k / float(count))
        out.append((cx + math.cos(a) * rx, cy + math.sin(a) * ry))
    return out


def _mix(p: Point, q: Point, u: float) -> Point:
    return (p[0] + (q[0] - p[0]) * u, p[1] + (q[1] - p[1]) * u)


def _lerp(a: float, b: float, u: float) -> float:
    return a + (b - a) * u


def _water(f: K.Frame, x0: float, x1: float, y0: float, y1: float, fill: RGBA) -> None:
    """A pool of water: a long flat oval from `x0` to `x1`, `y0` to `y1`.
    Its top is nearly level and its ends are round. It carries no
    outline."""
    cx, hw = (x0 + x1) / 2.0, (x1 - x0) / 2.0
    ym, hh = (y0 + y1) / 2.0, (y1 - y0) / 2.0
    top: List[Point] = []
    bottom: List[Point] = []
    for k in range(49):
        v = -1.0 + 2.0 * k / 48.0
        t = max(0.0, 1.0 - abs(v) ** 5) ** 0.3
        x = cx + v * hw
        top.append((x, ym - hh * t))
        bottom.append((x, ym + hh * t))
    f.poly(top + list(reversed(bottom)), fill, body=False)


def _ripples(f: K.Frame, x0: float, x1: float, y: float, ph: float, colour: RGBA, rows: int, gap: float, seed: str) -> None:
    """Short light lines on water. They slide a little with the phase `ph`
    of the loop, and come back to the start at the end of it."""
    rng = random.Random(seed)
    for r in range(rows):
        yy = y + r * gap
        x = x0 + rng.uniform(0.0, 10.0)
        while x < x1 - 6.0:
            ln = rng.uniform(4.0, 10.0)
            dx = 2.0 * math.sin(2.0 * math.pi * (ph + rng.random()))
            a, b = max(x0, x + dx), min(x1, x + dx + ln)
            if b - a > 2.0:
                f.ink([(a, yy), (b, yy)], 0.8, colour)
            x += ln + rng.uniform(6.0, 14.0)


def _block(f: K.Frame, x: float, y: float, w: float, h: float, rng: random.Random, tone: float = 0.0) -> List[Point]:
    """A rough block of basalt with its middle at `(x, y)`: a lumpy shape
    with flat faces, lit on its top, dark at its foot, with a few small
    holes of gas and, on some, lichen or moss. Returns its outline."""
    pts = []
    for k in range(9):
        a = math.tau * (k + rng.uniform(-0.22, 0.22)) / 9.0
        r = rng.uniform(0.86, 1.04)
        yy = math.sin(a) * h * r
        pts.append((x + math.cos(a) * w * r, y + (min(yy, h * 0.8) if yy > 0 else yy)))
    fill = BASALT if tone == 0.0 else (BASALT_LIGHT if tone > 0 else BASALT_SHADE)
    f.poly(pts, fill)
    top = [p for p in pts if p[1] < y - h * 0.25]
    if len(top) >= 2:
        top = sorted(top)
        f.poly(top + [(top[-1][0] - w * 0.15, y - h * 0.1), (top[0][0] + w * 0.15, y - h * 0.1)], BASALT_LIGHT if tone <= 0 else (150, 148, 140, 255), body=False)
    f.poly([(x - w * 0.8, y + h * 0.45), (x + w * 0.9, y + h * 0.40), (x + w * 0.7, y + h * 0.75), (x - w * 0.6, y + h * 0.78)], BASALT_SHADE, body=False)
    for _ in range(rng.randint(3, 6)):
        hx, hy = x + rng.uniform(-0.7, 0.7) * w, y + rng.uniform(-0.2, 0.6) * h
        f.dot(hx, hy, rng.uniform(0.35, 0.65), BASALT_DARK)
    roll = rng.random()
    if roll < 0.30:
        lx = x + rng.uniform(-0.4, 0.2) * w
        f.poly([(lx, y - h * 0.55), (lx + w * 0.45, y - h * 0.6), (lx + w * 0.55, y - h * 0.35), (lx + w * 0.1, y - h * 0.3)], K.alpha(LICHEN, 0.8), body=False)
    elif roll < 0.42:
        f.ellipse(x + rng.uniform(-0.3, 0.3) * w, y - h * 0.1, w * 0.16, h * 0.12, K.alpha(LICHEN_ORANGE, 0.85), body=False)
    return pts


def _moss_cap(f: K.Frame, x: float, y: float, w: float, rng: random.Random) -> None:
    """A cushion of moss on the top of a stone."""
    for _ in range(4):
        cx = x + rng.uniform(-0.6, 0.6) * w
        r = rng.uniform(0.25, 0.4) * w
        f.ellipse(cx, y + 1.0, r, r * 0.45, MOSS, body=False)
        f.ellipse(cx - r * 0.2, y + 0.4, r * 0.5, r * 0.2, MOSS_LIGHT, body=False)


def _tuft(f: K.Frame, x: float, y: float, rng: random.Random, size: float = 1.0, fill: RGBA = GREEN_SEDGE, light: RGBA = GREEN_SEDGE_LIGHT) -> None:
    """A tuft of sedge: thin blades that fan out from one root."""
    count = rng.randint(6, 9)
    for k in range(count):
        a = math.radians(-90.0 + (k - (count - 1) / 2.0) * 13.0 + rng.uniform(-5.0, 5.0))
        ln = size * rng.uniform(9.0, 15.0)
        tip = (x + math.cos(a) * ln, y + math.sin(a) * ln)
        nx, ny = -math.sin(a) * 1.0 * size, math.cos(a) * 1.0 * size
        f.poly([(x - nx, y - ny), tip, (x + nx, y + ny)], fill if k % 3 else light)


def _puff(f: K.Frame, x: float, y: float, r: float, colour: RGBA, rng: random.Random, lumps: int = 5) -> None:
    """A puff of smoke: round lumps about a middle."""
    for k in range(lumps):
        a = math.tau * k / lumps + rng.uniform(-0.3, 0.3)
        d = r * rng.uniform(0.35, 0.6)
        pr = r * rng.uniform(0.45, 0.65)
        f.ellipse(x + math.cos(a) * d, y + math.sin(a) * d * 0.8, pr, pr, colour, body=False)


def _flame(f: K.Frame, cx: float, base: float, width: float, height: float, lean: float, colour: RGBA) -> None:
    """One tongue of flame from `base` up to `height`, its tip moved by
    `lean`."""
    pts = [(cx - width, base), (cx - width * 0.8, base - height * 0.4), (cx - width * 0.3 + lean * 0.5, base - height * 0.75), (cx + lean, base - height),
           (cx + width * 0.4 + lean * 0.4, base - height * 0.6), (cx + width, base - height * 0.3), (cx + width * 0.9, base)]
    f.poly(pts, colour, body=False)


def _trap(f: K.Frame, mouth: Point, tail: Point, r0: float, r1: float, squash: float = 0.8) -> None:
    """A long eel trap of plaited sedge, a basket that tapers from a round
    open mouth at `mouth` (half height `r0`) to a narrow closed tail at
    `tail` (half height `r1`). The plaiting shows as a check of strips and
    bands that go round the basket; the mouth is a dark ring."""
    count = 20
    dx, dy = tail[0] - mouth[0], tail[1] - mouth[1]
    ln = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / ln, dx / ln

    def at(t: float, side: float) -> Point:
        r = _lerp(r0, r1, t ** 0.8)
        return (mouth[0] + dx * t + nx * r * side, mouth[1] + dy * t + ny * r * side)

    ts = [k / float(count) for k in range(count + 1)]
    outline = [at(t, -1.0) for t in ts] + [at(t, 1.0) for t in reversed(ts)]
    f.poly(outline, SEDGE)
    f.poly([at(t, 0.35) for t in ts] + [at(t, 1.0) for t in reversed(ts)], SEDGE_SHADE, body=False)
    f.poly([at(t, -1.0) for t in ts] + [at(t, -0.6) for t in reversed(ts)], SEDGE_LIGHT, body=False)
    # The plaiting: slant strips both ways, and the bands round it.
    for k in range(1, count * 2):
        t0, t1 = k / float(count * 2), min(1.0, (k + 1.6) / float(count * 2))
        f.ink([at(t0, -0.95), at(t1, 0.95)], 0.5, SEDGE_DARK)
        f.ink([at(t0, 0.95), at(t1, -0.95)], 0.4, SEDGE_SHADE)
    for t in (0.12, 0.34, 0.56, 0.76, 0.92):
        f.ink([at(t, -1.0), at(t + 0.01, 0.0), at(t, 1.0)], 1.1, SEDGE_DARK)
    # The mouth: a hoop of bent stick with the dark inside of the basket.
    rx = r0 * 0.42
    f.ellipse(mouth[0], mouth[1], rx + 1.4, r0 + 0.6, STAKE)
    f.ellipse(mouth[0] + 0.6, mouth[1], rx, r0 - 1.6, CHAR, body=False)
    # The tail is tied shut with cord.
    tx, ty = at(0.97, 0.0)
    f.ink([at(0.95, -1.0), at(0.95, 1.0)], 1.2, SEDGE_DARK)
    f.ink([(tx, ty), (tail[0] + dx / ln * 4.0, tail[1] + dy / ln * 4.0 + 1.0)], 0.9, SEDGE_DARK)


# ---------------------------------------------------------------------------
# The eel weir.
# ---------------------------------------------------------------------------


def _draw_eel_weir(anim: str, i: int, n: int):
    w, h = EEL_WEIR_FRAME
    f = K.Frame(EEL_WEIR_FRAME)
    rng = random.Random("history_eel_weir")
    ph = i / float(max(1, n))
    gap0, gap1 = 88.0, 106.0
    # The water held behind the weir: a long pool, its far bank of sedge.
    _water(f, 10.0, w - 10.0, 34.0, 60.0, WATER)
    _ripples(f, 26.0, w - 26.0, 42.0, ph, WATER_LIGHT, 2, 5.0, "history_eel_weir pond")
    for x in (26.0, 34.0, 158.0, 166.0):
        _tuft(f, x, 40.0, rng, 0.8)
    # The water below the weir, in front; the channel runs on to the left
    # and the right.
    _water(f, 6.0, w - 6.0, 66.0, 92.0, WATER_DEEP)
    # The banks where the channel is cut through the flow: low heaps of
    # basalt and earth at the two ends, higher than the weir.
    for x0, x1, sgn in ((12.0, 40.0, 1.0), (w - 12.0, w - 40.0, -1.0)):
        f.poly([(x0, 80.0), (x0 + sgn * 2.0, 50.0), (x0 + sgn * 10.0, 36.0), (x1, 44.0), (x1 + sgn * 6.0, 80.0)], EARTH)
        f.poly([(x0 + sgn * 2.0, 50.0), (x0 + sgn * 10.0, 36.0), (x1, 44.0), (x1 - sgn * 4.0, 50.0)], EARTH_SHADE, body=False)
    for x, y, bw, bh in ((20.0, 46.0, 8.0, 6.0), (30.0, 60.0, 9.0, 7.0), (18.0, 70.0, 8.0, 6.5), (w - 20.0, 46.0, 8.0, 6.0), (w - 30.0, 60.0, 9.0, 7.0), (w - 18.0, 70.0, 8.0, 6.5)):
        _block(f, x, y, bw, bh, rng, 0.0)
    # The weir: rows of rough blocks of basalt, each row over the joints of
    # the row under it, with a gap in the middle where the water runs.
    # Dark joints show between them.
    f.poly([(36.0, 80.0), (40.0, 46.0), (gap0 - 2.0, 44.0), (gap0 - 2.0, 80.0)], BASALT_DARK)
    f.poly([(gap1 + 2.0, 80.0), (gap1 + 2.0, 44.0), (w - 40.0, 46.0), (w - 36.0, 80.0)], BASALT_DARK)
    rows = ((73.0, 7.6), (61.0, 7.0), (50.0, 6.2))
    for r, (y, bh) in enumerate(rows):
        x = 34.0 + r * 3.0 + rng.uniform(0.0, 3.0)
        end = w - 34.0 - r * 3.0
        while x < end:
            bw = rng.uniform(7.0, 10.0)
            cx = x + bw
            if gap0 - bw * 0.6 < cx < gap1 + bw * 0.6:
                x = gap1 + 1.0 if cx < gap1 else x + 2.0 * bw
                continue
            _block(f, cx, y + rng.uniform(-1.0, 1.0), bw, bh, rng, rng.choice((-1.0, 0.0, 0.0, 1.0)))
            if r == len(rows) - 1 and rng.random() < 0.5:
                _moss_cap(f, cx, y - bh * 0.8, bw, rng)
            x += bw * 1.8 + rng.uniform(-0.8, 0.4)
    # The water that pours through the gap into the trap.
    cyc = 2.0 * math.pi * ph
    f.poly([(gap0 + 1.0, 50.0), (gap1 - 1.0, 50.0), (gap1 + 1.0, 76.0), (gap0 - 1.0, 76.0)], WATER, body=False)
    for k in range(4):
        x = gap0 + 3.0 + k * 4.0
        y = 54.0 + ((ph * 20.0 + k * 5.0) % 18.0)
        f.ink([(x, y), (x + 0.6, y + 5.0)], 0.8, WATER_LIGHT)
    # The trap: its mouth in the gap, its long body down the channel in
    # front, held by a stake driven into the bed.
    _trap(f, (97.0, 70.0), (164.0, 82.0), 9.0, 2.2)
    f.limb([(140.0, 64.0), (138.0, 88.0)], 3.0, STAKE)
    f.ink([(140.6, 66.0), (139.0, 86.0)], 0.6, STAKE_LIGHT)
    f.ink([(139.2, 76.0), (142.0, 79.0), (138.0, 80.0)], 0.8, SEDGE_DARK)
    # Foam where the water falls, and ripples that move.
    for k in range(5):
        a = cyc + k * 1.3
        f.ellipse(88.0 + k * 4.0 + 1.5 * math.sin(a), 77.0 + 0.8 * math.cos(a), 2.6, 1.2, FOAM, body=False)
    _ripples(f, 14.0, 84.0, 84.0, ph, WATER_LIGHT, 2, 4.0, "history_eel_weir front")
    _ripples(f, 120.0, w - 14.0, 88.0, ph, WATER_LIGHT, 1, 4.0, "history_eel_weir front right")
    # Sedge at the two ends of the weir, on the banks.
    for x, y, s in ((20.0, 80.0, 0.9), (32.0, 84.0, 0.8), (172.0, 80.0, 0.9), (160.0, 84.0, 0.8)):
        _tuft(f, x, y, rng, s)
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# The stone house.
# ---------------------------------------------------------------------------


def _draw_stone_house(anim: str, i: int, n: int):
    w, h = STONE_HOUSE_FRAME
    f = K.Frame(STONE_HOUSE_FRAME)
    rng = random.Random("history_stone_house")
    cx = w / 2.0
    ground = 148.0
    rx = 110.0
    wall_top = 90.0
    ry = 10.0
    # The roof: a dome of bent branches over the ring of the wall, covered
    # with turf, and sheets of bark laid on it like shingles. `on_dome`
    # gives a point of its surface: `phi` goes round it (0 faces the eye)
    # and `lat` goes up from the rim (0) to the top (90).
    dome_h = 64.0

    def on_dome(phi: float, lat: float) -> Point:
        a, b = math.radians(phi), math.radians(lat)
        return (cx + (rx + 3.0) * math.cos(b) * math.sin(a), wall_top + 2.0 + (ry + 2.0) * math.cos(b) * math.cos(a) - dome_h * math.sin(b))

    outline = [on_dome(-90.0 + 180.0 * k / 40.0, 0.0) for k in range(41)]
    sky = [on_dome(90.0, 0.0)] + [on_dome(180.0, lat) for lat in range(0, 91, 6)][1:] + [on_dome(-180.0 + 0.001, lat) for lat in range(90, -1, -6)]
    sky = [(cx + (x - cx), y) for x, y in sky]
    top_edge = [(cx + (rx + 3.0) * math.cos(math.radians(t)), wall_top + 2.0 - dome_h * math.sin(math.radians(t))) for t in range(0, 181, 5)]
    f.poly(top_edge + list(reversed(outline)), TURF)
    f.poly([on_dome(phi, 0.0) for phi in range(20, 91, 5)] + [on_dome(90.0, lat) for lat in range(0, 91, 10)] + [on_dome(phi, 70.0) for phi in range(90, 19, -10)], TURF_SHADE, body=False)
    # The bent branches that show at the rim and between the sheets.
    for phi in range(-80, 81, 16):
        f.ink([on_dome(phi, lat) for lat in range(0, 91, 10)], 1.0, BRANCH)
    # Sheets of bark in rows round the dome, each a little curved, lit on
    # its top edge, the upper rows over the lower.
    for lat0, dlat, step in ((2.0, 22.0, 20.0), (20.0, 22.0, 24.0), (38.0, 22.0, 30.0), (56.0, 20.0, 44.0)):
        phi = -88.0 + rng.uniform(0.0, step * 0.5)
        while phi < 88.0:
            if rng.random() < 0.72:
                half = step * rng.uniform(0.30, 0.42)
                l0, l1 = lat0 + rng.uniform(-2.0, 2.0), lat0 + dlat + rng.uniform(-2.0, 2.0)
                p0, p1 = max(-89.0, phi - half), min(89.0, phi + half)
                top = [on_dome(p0 + (p1 - p0) * k / 4.0, l1) for k in range(5)]
                low = [on_dome(p1 - (p1 - p0) * k / 4.0, l0) for k in range(5)]
                f.poly(top + low, BARK_SHEET)
                f.ink(top, 0.9, BARK_SHEET_LIGHT)
                f.ink(low, 1.0, BARK_SHEET_SHADE)
                f.ink([on_dome((p0 + p1) / 2.0, l0 + 2.0), on_dome((p0 + p1) / 2.0 + 2.0, l1 - 2.0)], 0.4, BARK_SHEET_SHADE)
            phi += step
    # Tufts of grass that grow in the turf.
    for _ in range(16):
        px, py = on_dome(rng.uniform(-80.0, 80.0), rng.uniform(10.0, 80.0))
        f.ink([(px, py), (px + rng.uniform(-2.0, 2.0), py - rng.uniform(3.0, 6.0))], 0.8, TURF_LIGHT)
        f.ink([(px + 1.0, py), (px + rng.uniform(0.0, 3.0), py - rng.uniform(2.0, 5.0))], 0.7, TURF_LIGHT)
    # The wall: a ring of stacked basalt. Its top is the near half of an
    # ellipse; its face goes down to the ground in courses of blocks.
    rim = _ring(cx, wall_top, rx, ry, 0.0, 180.0, 40)
    base = _ring(cx, ground - 6.0, rx + 2.0, ry, 0.0, 180.0, 40)
    f.poly(rim + list(reversed(base)), BASALT_DARK)
    door0, door1 = cx - 18.0, cx + 18.0
    door_top = 108.0
    courses = 6
    for c in range(courses):
        t0 = c / float(courses)
        t1 = (c + 1) / float(courses)
        bh = (ground - wall_top) / courses * 0.62
        x = cx - rx + 4.0 + (6.0 if c % 2 else 0.0)
        while x < cx + rx - 4.0:
            bw = rng.uniform(7.0, 10.5)
            bx = x + bw
            u = (bx - cx) / rx
            curve = ry * math.sqrt(max(0.0, 1.0 - u * u))
            by = wall_top + curve + (ground - 6.0 - wall_top) * (t0 + t1) * 0.5 + 2.0
            if not (door0 - bw * 0.5 < bx < door1 + bw * 0.5 and by > door_top - 2.0):
                shrink = 1.0 - 0.35 * abs(u) ** 3
                _block(f, bx, by, bw * shrink, bh, rng, rng.choice((-1.0, 0.0, 0.0, 1.0)))
            x += bw * 2.0 * (1.0 - 0.3 * abs(u) ** 3) + rng.uniform(-0.6, 0.4)
    # The top of the wall: a course of flat stones under the eave, moss on
    # some of them.
    for k in range(17):
        a = 6.0 + k * 168.0 / 16.0
        px, py = _ring(cx, wall_top, rx, ry, a, a, 1)[0]
        if door0 < px < door1:
            continue
        bw = 8.0 * (0.5 + 0.5 * math.sin(math.radians(a)))
        _block(f, px, py - 1.0, max(3.0, bw), 4.0, rng, 1.0)
        if rng.random() < 0.4:
            _moss_cap(f, px, py - 4.0, max(3.0, bw), rng)
    # The low doorway: a gap in the wall under a lintel of branches, dark
    # inside, with two big stones at its sides.
    f.poly([(door0, ground - 2.0), (door0, door_top + 6.0), (door0 + 6.0, door_top), (door1 - 6.0, door_top), (door1, door_top + 6.0), (door1, ground - 2.0)], INTERIOR)
    f.ellipse(cx, ground - 3.0, 18.0, 3.0, EARTH_SHADE, body=False)
    f.limb([(door0 - 3.0, door_top - 1.0), (door1 + 3.0, door_top - 2.0)], 4.6, BRANCH)
    f.ink([(door0 - 2.0, door_top - 2.4), (door1 + 2.0, door_top - 3.4)], 1.0, BRANCH_LIGHT)
    for side in (-1.0, 1.0):
        _block(f, cx + side * 25.0, ground - 22.0, 7.5, 9.0, rng, 0.0)
        _block(f, cx + side * 25.0, ground - 6.0, 8.0, 7.0, rng, -1.0)
    # The ground at the foot: earth and sedge.
    f.poly(_ring(cx, ground - 3.0, rx + 10.0, 6.0, 0.0, 180.0, 30), EARTH, body=False)
    for x in (cx - rx + 2.0, cx - rx + 22.0, cx + rx - 18.0, cx + rx + 2.0, cx - 46.0, cx + 50.0):
        _tuft(f, x, ground + 1.0 - 3.0 * (abs(x - cx) < 60.0), rng, 0.7)
    return A.finish(f, width=1.4)


# ---------------------------------------------------------------------------
# The smoking tree.
# ---------------------------------------------------------------------------


def _draw_smoking_tree(anim: str, i: int, n: int):
    w, h = SMOKING_TREE_FRAME
    f = K.Frame(SMOKING_TREE_FRAME)
    rng = random.Random("history_smoking_tree")
    ph = i / float(max(1, n))
    cyc = 2.0 * math.pi * ph
    ground = 314.0
    cx = 90.0

    def half(y: float) -> float:
        """The half width of the trunk at the height `y`: a wide foot with
        buttresses, a long straight bole."""
        t = (ground - y) / 220.0
        return 12.0 + 26.0 * max(0.0, 1.0 - t * 3.2) ** 2 - 4.5 * max(0.0, min(1.0, (130.0 - y) / 50.0))

    def mid(y: float) -> float:
        return cx + 4.0 * math.sin((ground - y) / 70.0)

    top_y = 80.0
    ys = [ground - (ground - top_y) * k / 30.0 for k in range(31)]
    left = [(mid(y) - half(y), y) for y in ys]
    right = [(mid(y) + half(y), y) for y in ys]
    # The limbs and the crown: pale limbs that fork up, and thin hanging
    # clumps of leaves. The crown is drawn first, so the trunk stands in
    # front of its lower part.
    limbs = [((mid(104.0) - 2.0, 104.0), (58.0, 68.0), (38.0, 42.0)), ((mid(96.0) + 2.0, 96.0), (120.0, 60.0), (150.0, 36.0)),
             ((mid(top_y), top_y + 4.0), (96.0, 50.0), (92.0, 22.0)), ((mid(134.0) + 4.0, 134.0), (140.0, 114.0), (164.0, 98.0))]
    clumps = []
    for (a, b, c) in limbs:
        for t in (0.6, 1.0):
            px, py = _mix(b, c, t) if t > 0.5 else _mix(a, b, 0.9)
            clumps.append((px, py))
    clumps += [(70.0, 30.0), (122.0, 26.0), (44.0, 54.0), (156.0, 70.0), (106.0, 40.0)]
    for px, py in clumps:
        for _ in range(4):
            x = px + rng.uniform(-14.0, 14.0)
            y = py + rng.uniform(-6.0, 8.0)
            x = min(w - 18.0, max(18.0, x))
            y = max(16.0, y)
            f.ellipse(x, y, rng.uniform(10.0, 15.0), rng.uniform(6.0, 9.0), LEAF)
            f.ellipse(x - 3.0, y - 2.0, 6.0, 3.0, LEAF_LIGHT, body=False)
            f.ellipse(x + 3.0, y + 3.0, 6.0, 2.6, LEAF_SHADE, body=False)
    for a, b, c in limbs:
        f.limb([a, b, c], 6.0, GUM)
        f.ink([(a[0] - 1.0, a[1]), (b[0] - 1.0, b[1]), (c[0] - 1.0, c[1])], 1.0, GUM_LIGHT)
    for px, py in clumps[::2]:
        for k in range(5):
            x = px + rng.uniform(-12.0, 12.0)
            y = py + rng.uniform(2.0, 10.0)
            x = min(w - 14.0, max(14.0, x))
            leaf = [(x, y), (x + 1.4, y + 5.0), (x + 0.4, y + 11.0), (x - 1.0, y + 5.0)]
            f.poly(leaf, LEAF_SHADE if k % 2 else LEAF)
    # The trunk: pale and smooth, with the old bark that hangs in ribbons,
    # shade on its right side.
    f.poly(left + list(reversed(right)), GUM)
    f.poly([(mid(y) + half(y) * 0.35, y) for y in ys] + list(reversed(right)), GUM_SHADE, body=False)
    f.poly([(mid(y) - half(y) * 0.85, y) for y in ys] + [(mid(y) - half(y) * 0.55, y) for y in reversed(ys)], GUM_LIGHT, body=False)
    for k in range(9):
        y0 = rng.uniform(top_y + 30.0, ground - 120.0)
        side = rng.choice((-0.7, -0.3, 0.4, 0.8))
        x0 = mid(y0) + half(y0) * side
        ln = rng.uniform(18.0, 34.0)
        rib = [(x0, y0), (x0 + 1.5, y0 + ln * 0.5), (x0 - 1.0, y0 + ln)]
        f.limb(rib, 2.2, GUM_RIBBON, body=False)
        f.ink(rib, 0.6, GUM_RIBBON_DARK)
    for k in range(5):
        y = rng.uniform(top_y + 20.0, ground - 130.0)
        f.ink([(mid(y) - half(y) * 0.5, y), (mid(y) + half(y) * 0.2, y + 3.0)], 0.6, GUM_SHADE)
    # The hole high on the trunk where some of the smoke comes out.
    hy = 168.0
    f.ellipse(mid(hy) + 2.0, hy, 4.4, 7.0, CHAR_EDGE)
    f.ellipse(mid(hy) + 2.4, hy + 0.6, 2.8, 5.2, CHAR, body=False)
    # The hollow at the foot: a tall arch that the fire burned out, black
    # inside and charred at its edges, with the small fire low in it.
    hx = mid(ground) - 2.0
    arch_top = ground - 80.0
    hw = 13.0
    arch = [(hx - hw, ground - 1.0), (hx - hw - 2.0, ground - 40.0), (hx - hw + 2.0, arch_top + 22.0), (hx - 6.0, arch_top + 4.0), (hx, arch_top),
            (hx + 7.0, arch_top + 6.0), (hx + hw - 1.0, arch_top + 26.0), (hx + hw + 2.0, ground - 36.0), (hx + hw, ground - 1.0)]
    edge = [(x + (2.6 if x > hx else -2.6), y - (2.0 if y < ground - 4.0 else 0.0)) for x, y in arch]
    f.poly(edge, CHAR_EDGE)
    f.poly(arch, CHAR, body=False)
    f.glow(hx, ground - 14.0, 16.0, K.alpha(FIRE, 0.18))
    # The eels hang in the hollow from a stick across it: small, dark,
    # curved, each tied by the head.
    sy = arch_top + 26.0
    f.limb([(hx - hw - 4.0, sy + 2.0), (hx + hw + 4.0, sy - 1.0)], 2.4, STICK)
    for k, dx in enumerate((-8.0, -1.0, 6.0)):
        x = hx + dx
        y = sy + 1.0 - dx * 0.08
        ln = 22.0 - abs(dx) * 0.3
        bend = 1.6 * (1.0 if k % 2 else -1.0)
        body = [(x, y + 1.0), (x + bend * 0.6, y + ln * 0.4), (x - bend * 0.3, y + ln * 0.75), (x + bend * 0.2, y + ln)]
        f.limb(body[:3], 4.2, EEL, body=False)
        f.limb(body[2:], 2.6, EEL, body=False)
        f.ink([(px - 1.0, py) for px, py in body[:-1]], 0.8, EEL_LIGHT)
        f.dot(body[-1][0], body[-1][1] + 1.0, 1.0, EEL_DARK)
        f.ink([(x - 1.2, y + 0.6), (x + 1.2, y + 0.6)], 1.0, SEDGE_DARK)
    # The fire: embers on the floor of the hollow and small low flames.
    for k in range(5):
        f.ellipse(hx - 9.0 + k * 4.6, ground - 4.0, 2.6, 1.6, EMBER, body=False)
    for a, b in (((hx - 10.0, ground - 2.0), (hx + 6.0, ground - 7.0)), ((hx + 10.0, ground - 2.0), (hx - 6.0, ground - 8.0))):
        f.limb([a, b], 2.4, STICK, body=False)
    for dx, hgt, off in ((-4.0, 11.0, 0.0), (4.0, 13.0, 1.9), (0.0, 16.0, 3.6)):
        hh = hgt * (0.82 + 0.18 * math.sin(cyc * 2.0 + off))
        _flame(f, hx + dx, ground - 5.0, 3.8, hh, 2.0 * math.sin(cyc + off), EMBER)
    _flame(f, hx, ground - 5.0, 2.2, 8.0 * (0.9 + 0.1 * math.sin(cyc * 3.0)), 1.0 * math.sin(cyc), FIRE)
    f.glow(hx, ground - 10.0, 8.0, K.alpha(FIRE_HOT, 0.25))
    # The smoke: thin puffs that rise out of the top of the hollow and out
    # of the hole, lean with the wind and fade.
    for src, (sx, sy0), rise, lean, size in ((0, (hx + 4.0, arch_top + 8.0), 110.0, 30.0, 8.0), (1, (mid(hy) + 6.0, hy - 4.0), 70.0, 34.0, 6.0)):
        for k in range(4):
            u = (ph + k / 4.0) % 1.0
            x = sx + lean * u + 3.0 * math.sin(2.0 * math.pi * (u + k * 0.3))
            y = sy0 - rise * u
            if src == 0 and y < arch_top:
                # Out of the top of the hollow the smoke clings to the
                # trunk, then leaves it.
                x = max(x, mid(y) + half(y) * 0.6 + 4.0 * u)
            _puff(f, min(w - 14.0, x), max(14.0, y), size * (0.6 + 0.8 * u), K.alpha(SMOKE, 0.72 * (1.0 - u) ** 0.8), random.Random(f"history_smoking_tree smoke {src} {k}"), 5)
    # The ground at the foot: earth, a few stones and sedge.
    f.poly(_ring(cx, ground, 66.0, 5.0, 180.0, 360.0, 30) + [(cx + 66.0, ground + 1.0), (cx - 66.0, ground + 1.0)], EARTH, body=False)
    for x, s in ((34.0, 0.9), (146.0, 1.0), (160.0, 0.7)):
        _tuft(f, x, ground + 1.0, rng, s)
    _block(f, 136.0, ground - 4.0, 8.0, 5.0, rng, 0.0)
    return A.finish(f, width=1.4)


# ---------------------------------------------------------------------------
# Publication.
# ---------------------------------------------------------------------------

FRAMES: Dict[str, Tuple[int, int]] = {
    "history_eel_weir": EEL_WEIR_FRAME,
    "history_stone_house": STONE_HOUSE_FRAME,
    "history_smoking_tree": SMOKING_TREE_FRAME,
}
DRAW: Dict[str, Callable] = {
    "history_eel_weir": _draw_eel_weir,
    "history_stone_house": _draw_stone_house,
    "history_smoking_tree": _draw_smoking_tree,
}
DISPLAY = {
    "history_eel_weir": "Eel Weir",
    "history_stone_house": "Stone House",
    "history_smoking_tree": "Smoking Tree",
}
#: The room of each prop: its last tag.
ROOMS = {
    "history_eel_weir": "budj_bim",
    "history_stone_house": "budj_bim",
    "history_smoking_tree": "budj_bim",
}
ROWS: Dict[str, List[Tuple[str, int, int]]] = {
    "history_eel_weir": LOOP,
    "history_smoking_tree": LOOP,
}


def _foot(name: str) -> Dict[str, Tuple[float, float]]:
    w, h = FRAMES[name]
    return {"foot": (w / 2.0, float(h))}


#: The anchors of each prop: each has a "foot" at the middle of its foot.
ANCHORS: Dict[str, Dict[str, Tuple[float, float]]] = {name: _foot(name) for name in DISPLAY}
TAGS: Dict[str, List[str]] = {name: ["prop", "scenery", "history", ROOMS[name]] for name in DISPLAY}

TARGETS: Dict[str, dict] = {
    name: _publisher(name, DISPLAY[name], ROWS.get(name, STILL), FRAMES[name], DRAW[name], ANCHORS[name], "Scenery", TAGS[name]) for name in DISPLAY
}
