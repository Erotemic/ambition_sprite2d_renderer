"""The props of South Asia and East Asia in the History dimension's grid.

The second pass of the History dimension is a grid of regions and times.
These props are for two of its floors: South Asia (the southern route,
Mehrgarh and the Indus cities, biome `history_indus`) and East Asia (the
Yellow River and the Shang court, biome `history_yellow_river`). They are
drawn in the cel style of the Art dimension's cast
(`targets/characters/_art_cast_kit.py`), in the warm sepia of an old
textbook with the colours of each floor (`_history_asia_kit.py`).

South Asia:

- ``history_great_bath``: scenery. The Great Bath of Mohenjo-daro: a
  tank of fine baked brick, sealed with bitumen, with a flight of steps
  down into it at each end and a row of brick pillars behind it. Its
  ``idle`` row moves the water.
- ``history_unicorn_seal``: a key. A small square seal of white steatite
  with the one-horned bull cut into it and a line of signs over it; a
  `PickupSpawn` draws its ``idle`` row (a slow bob and a glint).
- ``history_seal_gate``: the look of a `LockWall` of 32 by 128 world
  units, drawn at 3 to 1. A gate in a citadel wall of red brick. Over it
  hangs a signboard with ten big signs of the script, as the one found
  at the north gate of Dholavira; on its door is the unicorn seal.
- ``history_mud_hut``: scenery. A house of mud brick of Mehrgarh: rooms
  side by side, a flat roof on poles, a low door, a storage jar and a
  grinding stone. Its ``idle`` row lets smoke rise from the roof.

East Asia:

- ``history_oracle_bones``: scenery. An ox shoulder blade and a turtle
  shell, with the hollows the diviners drilled, the cracks that the heat
  made, and the characters that wrote down the answer.
- ``history_bronze_gate``: the look of a `LockWall` of 32 by 128 world
  units, drawn at 3 to 1. A door of green bronze with a taotie face, in
  a wall of rammed earth.
- ``history_bronze_ding``: scenery. A great square cauldron of bronze on
  four legs, with two handles, a taotie face and rows of bosses. Its
  ``idle`` row lets steam rise from it.
- ``history_rice_sheaf``: scenery. A sheaf of rice, tied at the middle,
  its heavy heads bent over. Its ``idle`` row moves the heads in the wind.

No drop shadows: the game draws them. The numbers are frame pixels; the
game shows each prop at half its frame (a gate at a third).
"""

from __future__ import annotations

import math
import random
from typing import Dict, List, Tuple

from ..characters import _art_cast_kit as K
from ..characters import _history_asia_kit as A
from .art_props import STILL, _publisher

Point = Tuple[float, float]
LOOP: List[Tuple[str, int, int]] = [("idle", 8, 120)]
KEY_ROWS: List[Tuple[str, int, int]] = [("idle", 8, 110)]

#: The outline: the dark sepia of old ink.
OUTLINE = (54, 36, 26, 255)
MORTAR = (122, 64, 44, 255)
WATER = (70, 150, 160, 255)
WATER_LIGHT = (150, 210, 210, 255)
WATER_DARK = (40, 96, 112, 255)
BITUMEN = (52, 44, 40, 255)
WOOD = (150, 98, 58, 255)
WOOD_LIGHT = (186, 132, 82, 255)
WOOD_DARK = (98, 60, 34, 255)
GYPSUM = (246, 242, 230, 255)
MUD = (198, 160, 112, 255)
MUD_LIGHT = (222, 190, 144, 255)
MUD_SHADE = (156, 120, 80, 255)
MUD_DARK = (110, 82, 54, 255)
REED = (204, 176, 104, 255)
REED_DARK = (150, 122, 62, 255)
SMOKE = (186, 178, 170, 255)
STEAM = (238, 236, 232, 255)
RICE_STALK = (196, 168, 80, 255)
RICE_STALK_DARK = (146, 118, 50, 255)
RICE_GRAIN = (238, 200, 96, 255)
RICE_GRAIN_DARK = (190, 146, 52, 255)
STRAW_ROPE = (170, 120, 64, 255)


def _phase(i: int, n: int) -> float:
    return i / float(max(1, n))


def _rect(x0: float, y0: float, x1: float, y1: float) -> List[Point]:
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def _bricks(f: K.Frame, x0: float, y0: float, x1: float, y1: float, course: float = 6.0, length: float = 14.0,
            colour=MORTAR, alpha: float = 0.75) -> None:
    """Courses of brick on a face from (`x0`, `y0`) to (`x1`, `y1`): a
    joint line under each course and the joints of the bricks, offset in
    each other course."""
    y = y0 + course
    row = 0
    while y < y1 - 0.5:
        f.ink([(x0, y), (x1, y)], 0.8, K.alpha(colour, alpha))
        y += course
    y = y0
    while y < y1 - 0.5:
        off = 0.0 if row % 2 else length / 2.0
        x = x0 + off + length
        while x < x1 - 1.0:
            f.ink([(x, y), (x, min(y1, y + course))], 0.7, K.alpha(colour, alpha))
            x += length
        y += course
        row += 1


def _sign(f: K.Frame, kind: int, x: float, y: float, s: float, colour, w: float = 0.9) -> None:
    """One sign of the Indus script about (`x`, `y`), `s` wide: a jar, a
    fish, three strokes, a man, a wheel, an arrow."""
    kind %= 6
    if kind == 0:
        f.ink([(x - s, y - s), (x - s * 0.6, y + s), (x + s * 0.6, y + s), (x + s, y - s)], w, colour)
        f.ink([(x - s * 1.2, y - s), (x + s * 1.2, y - s)], w, colour)
    elif kind == 1:
        f.ink([(x - s, y), (x, y - s * 0.7), (x + s, y), (x, y + s * 0.7), (x - s, y), (x - s * 1.4, y - s * 0.5)], w, colour)
    elif kind == 2:
        for k in range(3):
            f.ink([(x - s + k * s, y - s), (x - s + k * s, y + s)], w, colour)
    elif kind == 3:
        f.ink([(x, y - s), (x, y + s * 0.4)], w, colour)
        f.ink([(x - s, y - s * 0.2), (x + s, y - s * 0.2)], w, colour)
        f.ink([(x - s * 0.7, y + s), (x, y + s * 0.4), (x + s * 0.7, y + s)], w, colour)
    elif kind == 4:
        ring = K.ellipse_points(x, y, s, s, 12)
        f.ink(ring + [ring[0]], w, colour)
        f.ink([(x - s, y), (x + s, y)], w * 0.8, colour)
        f.ink([(x, y - s), (x, y + s)], w * 0.8, colour)
    else:
        f.ink([(x, y + s), (x, y - s)], w, colour)
        f.ink([(x - s * 0.7, y - s * 0.3), (x, y - s), (x + s * 0.7, y - s * 0.3)], w, colour)


def _unicorn(f: K.Frame, cx: float, cy: float, s: float, colour, w: float = 1.0) -> None:
    """The one-horned bull of the seals, cut in lines, facing right, about
    (`cx`, `cy`) at scale `s` (1 is about 20 pixels long)."""
    def P(x, y):
        return (cx + x * s, cy + y * s)
    # The back, the rump and the belly.
    f.ink([P(-10.0, -2.0), P(-6.0, -4.0), P(4.0, -4.0), P(7.0, -6.0)], w, colour)
    f.ink([P(-10.0, -2.0), P(-10.0, 3.0), P(-7.0, 4.0), P(5.0, 4.0), P(7.0, 2.0)], w, colour)
    # The neck, the head and the horn.
    f.ink([P(7.0, -6.0), P(10.0, -7.0), P(12.0, -5.0), P(11.0, -3.0), P(7.0, 2.0)], w, colour)
    f.ink([P(9.0, -7.0), P(12.0, -10.0), P(15.0, -12.0)], w, colour)
    # The legs and the tail.
    for x in (-8.5, -6.5, 3.0, 5.0):
        f.ink([P(x, 4.0), P(x, 9.0)], w * 0.9, colour)
    f.ink([P(-10.0, -1.0), P(-12.0, 4.0), P(-12.0, 7.0)], w * 0.8, colour)
    # The harness and the folds of the neck.
    f.ink([P(5.5, -4.5), P(6.5, 3.5)], w * 0.8, colour)
    f.ink([P(8.5, -5.0), P(8.5, -1.0)], w * 0.6, colour)
    # The "standard" in front of it, as on the seals.
    f.ink([P(14.0, 9.0), P(14.0, 1.0)], w * 0.8, colour)
    f.ink([P(12.0, 1.0), P(16.0, 1.0), P(15.0, -2.0), P(13.0, -2.0), P(12.0, 1.0)], w * 0.8, colour)


def _taotie(f: K.Frame, cx: float, cy: float, s: float, base, light, dark, deep) -> None:
    """A taotie face in relief about (`cx`, `cy`), `s` wide for 1.0 of
    about 40 pixels: horns, round eyes, the nose ridge, an upper jaw with
    fangs. Drawn as relief on a surface (no outline of its own)."""
    def P(x, y):
        return (cx + x * s, cy + y * s)
    for side in (-1.0, 1.0):
        horn = [P(side * 4.0, -12.0), P(side * 9.0, -19.0), P(side * 16.0, -20.0), P(side * 20.0, -15.0), P(side * 18.0, -11.0), P(side * 14.0, -11.0)]
        f.limb(horn, 3.6 * s, dark, body=False)
        f.limb(horn[1:4], 1.4 * s, light, body=False)
        f.limb([P(side * 4.0, -8.0), P(side * 9.0, -12.0), P(side * 16.0, -11.0)], 2.2 * s, dark, body=False)
        ex, ey = cx + side * 9.0 * s, cy - 3.0 * s
        f.ellipse(ex, ey, 4.4 * s, 3.8 * s, deep, body=False)
        f.ellipse(ex, ey, 3.2 * s, 2.7 * s, light, body=False)
        f.ellipse(ex, ey, 1.6 * s, 1.6 * s, deep, body=False)
        # The thunder pattern on the cheek.
        x, y = cx + side * 15.0 * s, cy + 4.0 * s
        st = 1.6 * s
        f.ink([(x, y), (x + side * st, y), (x + side * st, y + st), (x - side * st, y + st), (x - side * st, y - st), (x + side * 2.0 * st, y - st)],
              0.7 * s, deep)
        f.limb([P(side * 12.0, 9.0), P(side * 15.0, 14.0), P(side * 17.0, 12.0)], 1.6 * s, light, body=False)
    f.poly([P(-1.6, -16.0), P(1.6, -16.0), P(1.6, 4.0), P(-1.6, 4.0)], dark, body=False)
    for k in range(4):
        f.ink([P(-1.6, -13.0 + k * 4.0), P(1.6, -13.0 + k * 4.0)], 0.6 * s, light)
    f.poly([P(-6.0, 3.0), P(6.0, 3.0), P(7.0, 7.0), P(-7.0, 7.0)], light, body=False)
    f.poly([P(-10.0, 8.0), P(10.0, 8.0), P(9.0, 12.0), P(-9.0, 12.0)], deep, body=False)
    for k in range(5):
        x = -8.0 + k * 4.0
        f.poly([P(x - 1.2, 8.0), P(x + 1.2, 8.0), P(x, 11.0)], light, body=False)


# ---------------------------------------------------------------------------
# The Great Bath of Mohenjo-daro.
# ---------------------------------------------------------------------------

BATH_FRAME = (384, 192)


def _draw_great_bath(anim: str, i: int, n: int):
    w, h = BATH_FRAME
    t = _phase(i, n)
    f = K.Frame(BATH_FRAME)
    foot = h - 4.0
    # The row of brick pillars behind the tank, and the beam over them.
    beam_y = 22.0
    f.poly(_rect(30.0, beam_y, w - 30.0, beam_y + 9.0), WOOD)
    f.ink([(32.0, beam_y + 3.0), (w - 32.0, beam_y + 3.0)], 0.8, WOOD_LIGHT)
    for k in range(9):
        x = 31.0 + k * (w - 76.0) / 8.0
        f.poly(_rect(x, beam_y + 9.0, x + 14.0, 86.0), A.BRICK)
        f.poly(_rect(x + 10.0, beam_y + 9.0, x + 14.0, 86.0), A.BRICK_DARK, body=False)
        _bricks(f, x, beam_y + 9.0, x + 14.0, 86.0, 5.0, 7.0, alpha=0.6)
    # The pavement round the tank: a band of brick seen from above.
    top = 78.0
    f.poly([(12.0, top + 46.0), (24.0, top), (w - 24.0, top), (w - 12.0, top + 46.0)], A.BRICK_LIGHT)
    for k in range(1, 5):
        y = top + k * 9.0
        u = (y - top) / 46.0
        f.ink([(24.0 - 12.0 * u, y), (w - 24.0 + 12.0 * u, y)], 0.7, K.alpha(MORTAR, 0.45))
    # The tank: its far wall in brick, then the water, sealed with bitumen.
    tx0, tx1, ty0, ty1 = 76.0, w - 76.0, top + 6.0, top + 42.0
    tank = [(tx0, ty1), (tx0 + 8.0, ty0), (tx1 - 8.0, ty0), (tx1, ty1)]
    f.poly(tank, A.BRICK_DARK, body=False)
    _bricks(f, tx0 + 8.0, ty0, tx1 - 8.0, ty0 + 12.0, 4.0, 10.0, colour=(90, 44, 30, 255), alpha=0.7)
    f.poly([(tx0 + 2.0, ty1), (tx0 + 6.0, ty0 + 12.0), (tx1 - 6.0, ty0 + 12.0), (tx1 - 2.0, ty1)], BITUMEN, body=False)
    wl = ty0 + 15.0
    f.poly([(tx0 + 3.0, ty1 - 1.0), (tx0 + 6.0, wl), (tx1 - 6.0, wl), (tx1 - 3.0, ty1 - 1.0)], WATER, body=False)
    f.poly([(tx0 + 6.0, wl), (tx1 - 6.0, wl), (tx1 - 5.6, wl + 4.0), (tx0 + 5.6, wl + 4.0)], WATER_DARK, body=False)
    # Ripples that move along the water.
    rng = random.Random("history_great_bath")
    for k in range(9):
        y = wl + 7.0 + (k % 3) * 6.0
        x = tx0 + 24.0 + ((rng.uniform(0.0, 1.0) + t * (0.6 if k % 2 else -0.6)) % 1.0) * (tx1 - tx0 - 60.0)
        ln = rng.uniform(8.0, 16.0)
        f.ink([(x, y), (x + ln * 0.5, y - 1.0), (x + ln, y)], 1.0, K.alpha(WATER_LIGHT, 0.9))
    # The rim of the tank.
    f.ink([tank[0], tank[1], tank[2], tank[3]], 1.6, MORTAR)
    # The steps down into the water at each end.
    for side in (-1.0, 1.0):
        edge = tx0 if side < 0 else tx1
        for k in range(6):
            sx0 = edge + side * 2.0
            sx1 = edge - side * (40.0 - k * 5.5)
            y = ty0 + 2.0 + k * 6.0
            lo, hi = min(sx0, sx1), max(sx0, sx1)
            f.poly(_rect(lo, y, hi, y + 6.0), A.BRICK_LIGHT if k % 2 == 0 else A.BRICK, body=False)
            f.ink([(lo, y), (hi, y)], 0.9, MORTAR)
        # The step edges where they meet the water.
        f.ink([(edge - side * 12.0, wl + 2.0), (edge - side * 22.0, wl + 2.0)], 0.8, K.alpha(WATER_LIGHT, 0.8))
    # The front wall of the platform: courses of fine brick.
    f.poly(_rect(12.0, top + 46.0, w - 12.0, foot), A.BRICK)
    f.poly(_rect(12.0, foot - 8.0, w - 12.0, foot), A.BRICK_DARK, body=False)
    _bricks(f, 12.0, top + 46.0, w - 12.0, foot, 6.0, 14.0)
    f.limb([(14.0, top + 46.0), (w - 14.0, top + 46.0)], 2.0, A.BRICK_LIGHT, body=False)
    # A drain out of the front wall.
    dx = w / 2.0
    f.poly(_rect(dx - 7.0, foot - 30.0, dx + 7.0, foot - 18.0), BITUMEN, body=False)
    f.ink([(dx - 9.0, foot - 31.0), (dx + 9.0, foot - 31.0)], 1.6, A.BRICK_LIGHT)
    return f.finish(outline=OUTLINE, width=1.6)


# ---------------------------------------------------------------------------
# The unicorn seal: a key.
# ---------------------------------------------------------------------------

SEAL_FRAME = (68, 68)


def _draw_unicorn_seal(anim: str, i: int, n: int):
    t = i / float(n)
    f = K.Frame(SEAL_FRAME)
    cx, cy = 34.0, 35.0 + 2.4 * math.sin(math.tau * t)
    s = 19.0
    # A soft glow, so a key shows from far off.
    f.glow(cx, cy, 22.0, K.alpha((255, 236, 170, 255), 0.22))
    # The seal: a square of white steatite with bevelled edges and a boss
    # on its back, seen just from the side.
    f.poly([(cx - s + 2.0, cy - s - 3.0), (cx + s - 2.0, cy - s - 3.0), (cx + s, cy - s), (cx - s, cy - s)], A.STEATITE_SHADE)
    f.poly([(cx - 6.0, cy - s - 3.0), (cx + 6.0, cy - s - 3.0), (cx + 5.0, cy - s - 7.0), (cx - 5.0, cy - s - 7.0)], A.STEATITE_SHADE)
    f.ink([(cx - 1.4, cy - s - 5.6), (cx + 1.4, cy - s - 5.6)], 0.8, A.STEATITE_DARK)
    face = _rect(cx - s, cy - s, cx + s, cy + s)
    f.poly(face, A.STEATITE)
    f.poly([(cx + s - 4.0, cy - s), (cx + s, cy - s), (cx + s, cy + s), (cx - s, cy + s), (cx - s, cy + s - 4.0), (cx + s - 4.0, cy + s - 4.0)],
           A.STEATITE_SHADE, body=False)
    inner = _rect(cx - s + 3.0, cy - s + 3.0, cx + s - 4.0, cy + s - 4.0)
    f.ink(inner + [inner[0]], 0.8, A.STEATITE_DARK)
    # The signs along the top, and the bull under them.
    for k, kind in enumerate((0, 2, 1, 4)):
        _sign(f, kind, cx - 10.0 + k * 6.6, cy - s + 8.0, 2.0, A.STEATITE_DARK, 1.2)
    _unicorn(f, cx - 1.6, cy + 4.0, 1.05, A.STEATITE_DARK, 1.5)
    # The glint that goes across the stone.
    gx = cx - s - 6.0 + (2.0 * s + 12.0) * t
    if abs(gx - cx) < s - 2.0:
        f.ink([(gx - 3.0, cy + s - 3.0), (gx + 4.0, cy - s + 3.0)], 1.6, K.alpha(K.WHITE, 0.85))
    return f.finish(outline=OUTLINE, width=1.3)


# ---------------------------------------------------------------------------
# The seal gate: a gate in the citadel wall, with the signboard.
# ---------------------------------------------------------------------------

GATE_FRAME = (96, 384)


def _gate_frame(f: K.Frame, w: float, foot: float, m: float) -> None:
    """The brick of a citadel wall from the top of the box to its foot."""
    f.poly(_rect(m, m, w - m, foot), A.BRICK)
    f.poly(_rect(w - 14.0, m, w - m, foot), A.BRICK_DARK, body=False)
    _bricks(f, m, m, w - m, foot, 8.0, 18.0)


def _draw_seal_gate(anim: str, i: int, n: int):
    w, h = GATE_FRAME
    m = 4.0
    foot = h - m
    f = K.Frame(GATE_FRAME)
    _gate_frame(f, w, foot, m)
    # The signboard over the gate: ten big white signs on a dark board, in
    # two rows of five.
    bx0, bx1, by0, by1 = 10.0, w - 10.0, 18.0, 66.0
    f.poly(_rect(bx0, by0, bx1, by1), WOOD_DARK, body=False)
    f.ink([(bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1), (bx0, by0)], 1.6, OUTLINE)
    signs = (0, 3, 2, 4, 0, 1, 5, 2, 3, 0)
    for k, kind in enumerate(signs):
        x = bx0 + 9.0 + (k % 5) * ((bx1 - bx0 - 18.0) / 4.0)
        y = by0 + 13.0 + (k // 5) * 22.0
        _sign(f, kind, x, y, 4.6, GYPSUM, 2.0)
    # The opening: a flat lintel of timber, and a door of planks.
    ox0, ox1, oy = 18.0, w - 18.0, 96.0
    f.poly(_rect(ox0 - 6.0, oy - 12.0, ox1 + 6.0, oy), WOOD)
    f.ink([(ox0 - 4.0, oy - 8.0), (ox1 + 4.0, oy - 8.0)], 0.8, WOOD_LIGHT)
    f.poly(_rect(ox0, oy, ox1, foot), WOOD_DARK, body=False)
    f.poly(_rect(ox0 + 3.0, oy + 2.0, ox1 - 3.0, foot), WOOD, body=False)
    for x in (ox0 + 12.0, ox0 + 22.0, ox1 - 22.0, ox1 - 12.0):
        f.ink([(x, oy + 2.0), (x, foot)], 1.0, K.alpha(WOOD_DARK, 0.9))
    f.ink([((ox0 + ox1) / 2.0, oy + 2.0), ((ox0 + ox1) / 2.0, foot)], 2.0, OUTLINE)
    for y in (oy + 30.0, foot - 40.0):
        f.limb([(ox0 + 4.0, y), (ox1 - 4.0, y)], 4.0, WOOD_DARK, body=False)
    # The unicorn seal on the door: big, square, white.
    cx, cy, s = w / 2.0, 214.0, 22.0
    f.poly(_rect(cx - s - 2.0, cy - s - 2.0, cx + s + 2.0, cy + s + 2.0), OUTLINE, body=False)
    f.poly(_rect(cx - s, cy - s, cx + s, cy + s), A.STEATITE, body=False)
    f.poly([(cx + s - 4.0, cy - s), (cx + s, cy - s), (cx + s, cy + s), (cx - s, cy + s), (cx - s, cy + s - 4.0), (cx + s - 4.0, cy + s - 4.0)],
           A.STEATITE_SHADE, body=False)
    for k, kind in enumerate((0, 2, 1)):
        _sign(f, kind, cx - 9.0 + k * 9.0, cy - s + 8.0, 2.6, A.STEATITE_DARK, 1.1)
    _unicorn(f, cx - 2.0, cy + 5.0, 1.2, A.STEATITE_DARK, 1.3)
    # Brick steps up to the door.
    f.poly(_rect(ox0 - 8.0, foot - 8.0, ox1 + 8.0, foot), A.BRICK_LIGHT, body=False)
    f.ink([(ox0 - 8.0, foot - 8.0), (ox1 + 8.0, foot - 8.0)], 1.0, MORTAR)
    return f.finish(outline=OUTLINE, width=1.6)


# ---------------------------------------------------------------------------
# A house of mud brick of Mehrgarh.
# ---------------------------------------------------------------------------

HUT_FRAME = (256, 192)


def _draw_mud_hut(anim: str, i: int, n: int):
    w, h = HUT_FRAME
    t = _phase(i, n)
    f = K.Frame(HUT_FRAME)
    foot = h - 4.0
    # The smoke from the hole in the roof, behind the roof.
    for k in range(4):
        u = (t + k / 4.0) % 1.0
        x = 150.0 + 8.0 * math.sin(math.tau * (u + k * 0.3)) + 10.0 * u
        y = 66.0 - 56.0 * u
        r = 5.0 + 8.0 * u
        f.ellipse(x, y, r, r * 0.85, K.alpha(SMOKE, 0.8 * (1.0 - u)), body=False)
    # Two rooms side by side: the big one on the left, a low store room on
    # the right.
    big = (34.0, 80.0, 176.0, foot)
    small = (176.0, 108.0, 232.0, foot)
    for (x0, y0, x1, y1), shade_w in ((big, 18.0), (small, 12.0)):
        f.poly(_rect(x0, y0, x1, y1), MUD)
        f.poly(_rect(x1 - shade_w, y0, x1, y1), MUD_SHADE, body=False)
        _bricks(f, x0, y0 + 4.0, x1, y1, 9.0, 22.0, colour=MUD_DARK, alpha=0.4)
    # The flat roofs: a layer of reeds and mud on poles whose ends stick out.
    for x0, y0, x1 in ((28.0, 70.0, 182.0), (172.0, 100.0, 238.0)):
        f.poly(_rect(x0, y0, x1, y0 + 10.0), REED)
        for x in range(int(x0) + 3, int(x1) - 2, 5):
            f.ink([(x, y0 + 1.0), (x + 1.0, y0 + 9.0)], 0.7, REED_DARK)
        f.poly(_rect(x0 + 2.0, y0 - 4.0, x1 - 2.0, y0 + 1.0), MUD_LIGHT)
        for x in range(int(x0) + 10, int(x1) - 6, 22):
            f.limb([(x, y0 + 12.0), (x, y0 + 14.0)], 4.0, WOOD)
            f.ellipse(x, y0 + 13.0, 2.4, 2.4, WOOD_DARK, body=False)
    # The low door, with a mat of reeds rolled up over it.
    f.poly([(70.0, foot), (70.0, 130.0), (76.0, 122.0), (98.0, 122.0), (104.0, 130.0), (104.0, foot)], MUD_DARK, body=False)
    f.poly([(73.0, foot), (73.0, 132.0), (78.0, 126.0), (96.0, 126.0), (101.0, 132.0), (101.0, foot)], (64, 46, 32, 255), body=False)
    f.limb([(68.0, 120.0), (106.0, 120.0)], 6.0, REED)
    for x in (74.0, 84.0, 94.0):
        f.ink([(x, 117.0), (x + 2.0, 123.0)], 0.8, REED_DARK)
    # A small window in the store room.
    f.poly(_rect(196.0, 128.0, 210.0, 138.0), MUD_DARK, body=False)
    # A big storage jar by the wall, painted with a band of black.
    jx, jy = 136.0, foot
    jar = [(jx - 12.0, jy), (jx - 16.0, jy - 18.0), (jx - 13.0, jy - 32.0), (jx - 6.0, jy - 38.0), (jx + 6.0, jy - 38.0), (jx + 13.0, jy - 32.0),
           (jx + 16.0, jy - 18.0), (jx + 12.0, jy)]
    f.poly(jar, (204, 120, 76, 255))
    f.poly([(jx + 6.0, jy), (jx + 12.0, jy), (jx + 16.0, jy - 18.0), (jx + 13.0, jy - 32.0), (jx + 8.0, jy - 30.0), (jx + 10.0, jy - 16.0)],
           (164, 90, 54, 255), body=False)
    f.limb([(jx - 15.0, jy - 24.0), (jx + 15.0, jy - 24.0)], 2.4, (54, 38, 30, 255), body=False)
    for k in range(5):
        x = jx - 12.0 + k * 6.0
        f.ink([(x, jy - 22.0), (x + 3.0, jy - 18.0), (x + 6.0, jy - 22.0)], 0.9, (54, 38, 30, 255))
    f.ellipse(jx, jy - 38.0, 7.0, 2.0, (164, 90, 54, 255))
    # A grinding stone and its rubber, with a little heap of barley.
    gx = 22.0
    f.poly([(gx - 10.0, foot), (gx - 12.0, foot - 6.0), (gx + 14.0, foot - 8.0), (gx + 16.0, foot)], (150, 140, 128, 255))
    f.ellipse(gx + 2.0, foot - 11.0, 6.0, 3.6, (178, 168, 154, 255))
    for k in range(7):
        f.dot(gx + 20.0 + (k % 4) * 2.6, foot - 1.6 - (k // 4) * 2.0, 1.3, A.SILT)
    return f.finish(outline=OUTLINE, width=1.6)


# ---------------------------------------------------------------------------
# The oracle bones.
# ---------------------------------------------------------------------------

BONES_FRAME = (128, 96)


def _oracle_char(f: K.Frame, kind: int, x: float, y: float, s: float, colour) -> None:
    """A character of the oracle bones about (`x`, `y`): the sun, the
    moon, a man, the crack (the sign "bu", a crack), the king, rain."""
    kind %= 6
    w = 0.9
    if kind == 0:
        ring = K.ellipse_points(x, y, s, s, 12)
        f.ink(ring + [ring[0]], w, colour)
        f.dot(x, y, 0.6, colour)
    elif kind == 1:
        f.ink([(x - s * 0.2, y - s), (x + s * 0.8, y - s * 0.4), (x + s * 0.8, y + s * 0.4), (x - s * 0.2, y + s)], w, colour)
        f.ink([(x + s * 0.1, y - s * 0.4), (x + s * 0.1, y + s * 0.3)], w * 0.8, colour)
    elif kind == 2:
        f.ink([(x + s * 0.3, y - s), (x - s * 0.2, y + s)], w, colour)
        f.ink([(x - s * 0.6, y - s * 0.1), (x + s * 0.1, y - s * 0.4)], w, colour)
    elif kind == 3:
        f.ink([(x, y - s), (x, y + s)], w, colour)
        f.ink([(x, y - s * 0.1), (x + s * 0.8, y - s * 0.5)], w, colour)
    elif kind == 4:
        f.ink([(x - s * 0.8, y - s), (x + s * 0.8, y - s)], w, colour)
        f.ink([(x, y - s), (x, y + s * 0.5)], w, colour)
        f.ink([(x - s, y + s * 0.5), (x, y + s), (x + s, y + s * 0.5)], w, colour)
    else:
        f.ink([(x - s, y - s), (x + s, y - s)], w, colour)
        for k in (-0.6, 0.0, 0.6):
            f.ink([(x + k * s, y - s * 0.6), (x + k * s, y - s * 0.1)], w * 0.8, colour)
            f.dot(x + k * s, y + s * 0.4, 0.55, colour)


def _draw_oracle_bones(anim: str, i: int, n: int):
    w, h = BONES_FRAME
    f = K.Frame(BONES_FRAME)
    foot = h - 4.0
    # The ox shoulder blade, leaning back on the right: broad below, and
    # the knob of the joint at the top.
    blade = [(66.0, foot), (76.0, foot - 30.0), (92.0, foot - 64.0), (100.0, foot - 74.0), (110.0, foot - 72.0), (114.0, foot - 60.0),
             (120.0, foot - 30.0), (122.0, foot)]
    f.poly(blade, A.BONE)
    f.ellipse(105.0, foot - 76.0, 7.0, 6.0, A.BONE)
    f.ellipse(105.0, foot - 77.0, 4.0, 3.0, A.BONE_SHADE, body=False)
    f.poly([(112.0, foot - 62.0), (116.0, foot - 40.0), (122.0, foot), (110.0, foot), (110.0, foot - 40.0)], A.BONE_SHADE, body=False)
    f.ink([(100.0, foot - 66.0), (96.0, foot - 30.0), (94.0, foot - 2.0)], 1.2, A.BONE_SHADE)
    # The pits the diviners drilled, and the cracks the heat made from them.
    for k, (x, y) in enumerate(((86.0, foot - 40.0), (104.0, foot - 44.0), (82.0, foot - 18.0), (108.0, foot - 20.0))):
        f.ellipse(x, y, 2.2, 3.2, A.BONE_SHADE, body=False)
        f.ellipse(x + 0.4, y + 0.4, 1.2, 2.0, (150, 120, 84, 255), body=False)
        f.ink([(x - 3.0, y - 6.0), (x - 1.0, y + 6.0)], 0.8, A.SEPIA_INK)
        f.ink([(x - 2.0, y), (x + 4.0, y - 2.4)], 0.8, A.SEPIA_INK)
        _oracle_char(f, k + 1, x + 9.0 if x < 100 else x + 8.0, y - 2.0, 2.6, A.CINNABAR_DARK)
    # The turtle shell, the belly side, lying at the front on the left: its
    # seams, its drilled pits, its cracks and its characters, rubbed with
    # red.
    cx, cy = 44.0, foot - 24.0
    shell = [(cx - 32.0, cy + 18.0), (cx - 38.0, cy + 4.0), (cx - 34.0, cy - 10.0), (cx - 24.0, cy - 18.0), (cx + 24.0, cy - 18.0),
             (cx + 34.0, cy - 10.0), (cx + 38.0, cy + 4.0), (cx + 32.0, cy + 18.0), (cx + 18.0, cy + 22.0), (cx - 18.0, cy + 22.0)]
    f.poly(shell, (226, 208, 166, 255))
    f.poly([(cx - 32.0, cy + 18.0), (cx + 32.0, cy + 18.0), (cx + 18.0, cy + 22.0), (cx - 18.0, cy + 22.0)], A.BONE_SHADE, body=False)
    f.ink([(cx, cy - 18.0), (cx, cy + 22.0)], 1.0, A.BONE_SHADE)
    for y in (cy - 8.0, cy + 4.0, cy + 14.0):
        f.ink([(cx - 34.0, y), (cx - 12.0, y + 1.0), (cx, y), (cx + 12.0, y + 1.0), (cx + 34.0, y)], 0.9, A.BONE_SHADE)
    rng = random.Random("history_oracle_bones")
    for k, (x, y) in enumerate(((cx - 22.0, cy - 2.0), (cx - 8.0, cy - 12.0), (cx + 8.0, cy - 12.0), (cx + 22.0, cy - 2.0), (cx - 16.0, cy + 10.0),
                                (cx + 16.0, cy + 10.0))):
        f.ellipse(x, y, 1.8, 2.6, A.BONE_SHADE, body=False)
        f.ink([(x, y - 4.0), (x + rng.uniform(-1.0, 1.0), y + 4.0)], 0.8, A.SEPIA_INK)
        side = -1.0 if x < cx else 1.0
        f.ink([(x, y), (x + side * 4.0, y - 1.6)], 0.8, A.SEPIA_INK)
        _oracle_char(f, k, x + side * 7.0, y + 1.0, 2.2, A.CINNABAR)
    return f.finish(outline=OUTLINE, width=1.4)


# ---------------------------------------------------------------------------
# The bronze gate of the Shang court.
# ---------------------------------------------------------------------------


def _draw_bronze_gate(anim: str, i: int, n: int):
    w, h = GATE_FRAME
    m = 4.0
    foot = h - m
    f = K.Frame(GATE_FRAME)
    # The wall of rammed earth: layers of loess, each pounded down.
    f.poly(_rect(m, m, w - m, foot), A.LOESS)
    f.poly(_rect(w - 14.0, m, w - m, foot), A.LOESS_DARK, body=False)
    rng = random.Random("history_bronze_gate")
    y = m + 10.0
    while y < foot - 2.0:
        f.ink([(m, y), (w - m, y + rng.uniform(-0.6, 0.6))], 0.9, K.alpha(A.LOESS_DARK, 0.8))
        # The marks of the pounders in each layer.
        for k in range(3):
            x = rng.uniform(m + 4.0, w - m - 8.0)
            f.ellipse(x, y - 4.0, 2.4, 1.2, K.alpha(A.LOESS_DARK, 0.45), body=False)
        y += 10.0
    # A roof of thatch over the gate.
    f.poly([(m, 32.0), (w / 2.0, m + 2.0), (w - m, 32.0), (w - m, 38.0), (m, 38.0)], REED)
    for k in range(12):
        x = m + 4.0 + k * 7.4
        f.ink([(x, 33.0), (x + 1.0, 38.0)], 0.8, REED_DARK)
    f.ink([(m, 32.0), (w / 2.0, m + 2.0), (w - m, 32.0)], 1.4, REED_DARK)
    # The door: two leaves of green bronze in a frame of timber.
    ox0, ox1, oy = 12.0, w - 12.0, 60.0
    f.poly(_rect(ox0 - 4.0, oy - 8.0, ox1 + 4.0, foot), WOOD_DARK, body=False)
    f.poly(_rect(ox0, oy, ox1, foot), A.BRONZE_GREEN, body=False)
    f.poly(_rect(ox1 - 10.0, oy, ox1, foot), A.BRONZE_GREEN_DARK, body=False)
    f.poly(_rect(ox0, oy, ox0 + 3.0, foot), A.BRONZE_GREEN_LIGHT, body=False)
    f.ink([(w / 2.0, oy), (w / 2.0, foot)], 2.0, A.BRONZE_GREEN_DEEP)
    # Bands of the thunder pattern across the door.
    for by in (oy + 10.0, foot - 24.0):
        f.poly(_rect(ox0 + 2.0, by - 5.0, ox1 - 2.0, by + 5.0), A.BRONZE_GREEN_DARK, body=False)
        x = ox0 + 5.0
        while x < ox1 - 8.0:
            f.ink([(x, by + 3.0), (x, by - 3.0), (x + 5.0, by - 3.0), (x + 5.0, by + 1.0), (x + 2.0, by + 1.0), (x + 2.0, by - 1.0)], 0.8, A.BRONZE_GREEN_LIGHT)
            x += 8.0
    # Rows of bosses down each leaf.
    for y in range(int(oy) + 28, int(foot) - 34, 18):
        if 120 < y < 210:
            continue
        for x in (ox0 + 8.0, w / 2.0 - 8.0, w / 2.0 + 8.0, ox1 - 8.0):
            f.dot(x, float(y), 2.6, A.BRONZE_GREEN_DARK)
            f.dot(x - 0.6, y - 0.7, 1.2, A.BRONZE_BRIGHT)
    # The taotie face, across both leaves.
    _taotie(f, w / 2.0, 164.0, 1.7, A.BRONZE_GREEN, A.BRONZE_GREEN_LIGHT, A.BRONZE_GREEN_DARK, A.BRONZE_GREEN_DEEP)
    # Two rings to pull it by.
    for x in (w / 2.0 - 8.0, w / 2.0 + 8.0):
        ring = K.ellipse_points(x, 236.0, 5.0, 6.0, 18)
        f.ink(ring + [ring[0]], 2.0, A.BRONZE_BRIGHT)
        f.dot(x, 230.0, 2.4, A.BRONZE_GREEN_DEEP)
    return f.finish(outline=OUTLINE, width=1.6)


# ---------------------------------------------------------------------------
# The great bronze ding.
# ---------------------------------------------------------------------------

DING_FRAME = (192, 192)


def _draw_bronze_ding(anim: str, i: int, n: int):
    w, h = DING_FRAME
    t = _phase(i, n)
    f = K.Frame(DING_FRAME)
    foot = h - 4.0
    cx = w / 2.0
    # The steam that rises out of it, behind the rim.
    for k in range(5):
        u = (t + k / 5.0) % 1.0
        x = cx - 30.0 + k * 15.0 + 6.0 * math.sin(math.tau * (u + k * 0.37))
        y = 58.0 - 50.0 * u
        r = 5.0 + 7.0 * u
        f.ellipse(x, y, r, r * 0.8, K.alpha(STEAM, 0.75 * (1.0 - u)), body=False)
    body_top, body_low = 66.0, 140.0
    # The far legs, in shade.
    for x in (cx - 30.0, cx + 30.0):
        f.limb([(x, body_low - 6.0), (x, foot - 10.0)], 12.0, A.BRONZE_GREEN_DARK)
    # The two handles: upright loops on the rim.
    for x in (cx - 40.0, cx + 40.0):
        f.limb([(x - 8.0, body_top), (x - 8.0, body_top - 30.0), (x + 8.0, body_top - 30.0), (x + 8.0, body_top)], 6.0, A.BRONZE_GREEN)
        f.ink([(x - 7.0, body_top - 31.6), (x + 7.0, body_top - 31.6)], 1.0, A.BRONZE_GREEN_LIGHT)
    # The vessel: a deep square body, a little wider at its lip.
    vessel = [(cx - 52.0, body_low), (cx - 56.0, body_top), (cx + 56.0, body_top), (cx + 52.0, body_low)]
    f.poly(vessel, A.BRONZE_GREEN)
    f.poly([(cx + 36.0, body_low), (cx + 38.0, body_top), (cx + 56.0, body_top), (cx + 52.0, body_low)], A.BRONZE_GREEN_DARK, body=False)
    f.poly([(cx - 52.0, body_low), (cx - 56.0, body_top), (cx - 50.0, body_top), (cx - 47.0, body_low)], A.BRONZE_GREEN_LIGHT, body=False)
    # The thick lip.
    f.poly(_rect(cx - 60.0, body_top - 6.0, cx + 60.0, body_top + 2.0), A.BRONZE_GREEN)
    f.ink([(cx - 58.0, body_top - 4.0), (cx + 58.0, body_top - 4.0)], 1.0, A.BRONZE_BRIGHT)
    f.ink([(cx - 60.0, body_top + 2.0), (cx + 60.0, body_top + 2.0)], 1.2, A.BRONZE_GREEN_DEEP)
    # A frame of bosses round the face, in rows of three: the nipple pattern.
    for k in range(3):
        for x0 in (cx - 46.0, cx + 40.0):
            for y in range(int(body_top) + 14, int(body_low) - 6, 12):
                f.dot(x0 + k * 3.0, float(y), 1.6, A.BRONZE_GREEN_DARK)
                f.dot(x0 + k * 3.0 - 0.4, y - 0.5, 0.7, A.BRONZE_BRIGHT)
    # The band under the lip, with its thunder pattern.
    f.poly(_rect(cx - 52.0, body_top + 4.0, cx + 52.0, body_top + 12.0), A.BRONZE_GREEN_DARK, body=False)
    x = cx - 50.0
    while x < cx + 46.0:
        by = body_top + 8.0
        f.ink([(x, by + 2.4), (x, by - 2.4), (x + 4.0, by - 2.4), (x + 4.0, by + 1.0), (x + 1.6, by + 1.0)], 0.8, A.BRONZE_GREEN_LIGHT)
        x += 7.0
    # The taotie face on its side.
    _taotie(f, cx - 2.0, 106.0, 1.25, A.BRONZE_GREEN, A.BRONZE_GREEN_LIGHT, A.BRONZE_GREEN_DARK, A.BRONZE_GREEN_DEEP)
    # The near legs: thick, with a ridge and a mask at the top of each.
    for x in (cx - 40.0, cx + 40.0):
        f.limb([(x, body_low - 4.0), (x, foot - 8.0)], 15.0, A.BRONZE_GREEN)
        f.ink([(x + 3.0, body_low + 4.0), (x + 3.0, foot - 8.0)], 1.0, A.BRONZE_GREEN_DARK)
        f.ink([(x - 4.0, body_low + 4.0), (x - 4.0, foot - 8.0)], 1.2, A.BRONZE_GREEN_LIGHT)
        f.ellipse(x, body_low + 6.0, 6.0, 4.0, A.BRONZE_GREEN_DARK, body=False)
        f.dot(x - 2.4, body_low + 5.0, 1.2, A.BRONZE_BRIGHT)
        f.dot(x + 2.4, body_low + 5.0, 1.2, A.BRONZE_BRIGHT)
        f.ellipse(x, foot - 6.0, 9.0, 3.0, A.BRONZE_GREEN_DARK)
    return f.finish(outline=OUTLINE, width=1.6)


# ---------------------------------------------------------------------------
# A sheaf of rice.
# ---------------------------------------------------------------------------

RICE_FRAME = (96, 128)


def _draw_rice_sheaf(anim: str, i: int, n: int):
    w, h = RICE_FRAME
    t = _phase(i, n)
    f = K.Frame(RICE_FRAME)
    foot = h - 4.0
    cx, tie = w / 2.0, 74.0
    sway = 3.0 * math.sin(math.tau * t)
    rng = random.Random("history_rice_sheaf")
    stalks = []
    for k in range(13):
        u = (k - 6.0) / 6.0
        base = (cx + u * 18.0, foot)
        top = (cx + u * 20.0 + sway * 0.3, 30.0 + abs(u) * 8.0 + rng.uniform(-2.0, 2.0))
        stalks.append((u, base, top))
    # The stalks: spread at the foot, drawn in at the tie, spread at the top.
    for u, base, top in stalks:
        mid = (cx + u * 5.0, tie)
        colour = RICE_STALK if abs(u) < 0.7 else RICE_STALK_DARK
        f.limb([base, mid, top], 2.4, colour)
    # The heads: each bends over and hangs, heavy with grain.
    for k, (u, base, top) in enumerate(stalks):
        side = 1.0 if u >= 0 else -1.0
        if abs(u) < 0.1:
            side = 1.0 if k % 2 else -1.0
        bend = 10.0 + 6.0 * abs(u)
        sw = sway * (0.8 + 0.4 * abs(u))
        pts = [top, (top[0] + side * bend * 0.6 + sw * 0.5, top[1] - 5.0), (top[0] + side * bend + sw, top[1] + 6.0),
               (top[0] + side * bend * 0.9 + sw, top[1] + 24.0)]
        f.limb(pts, 1.6, RICE_STALK_DARK)
        for q in range(8):
            a = 1.0 + q * 0.28
            seg = min(3, int(a))
            v = a - seg
            p0, p1 = pts[min(seg, 3)], pts[min(seg + 1, 3)]
            gx, gy = p0[0] + (p1[0] - p0[0]) * v, p0[1] + (p1[1] - p0[1]) * v
            f.ellipse(gx + side * 1.4 * (1 if q % 2 else -0.4), gy, 1.6, 2.4, RICE_GRAIN)
            f.ellipse(gx + side * 1.6 + 0.6, gy + 0.6, 0.8, 1.4, RICE_GRAIN_DARK, body=False)
    # The tie: a band of twisted straw.
    f.limb([(cx - 8.0, tie - 2.0), (cx + 8.0, tie + 1.0)], 4.0, STRAW_ROPE)
    f.limb([(cx - 8.0, tie + 3.0), (cx + 8.0, tie + 5.0)], 3.0, STRAW_ROPE)
    for k in range(4):
        x = cx - 6.0 + k * 4.0
        f.ink([(x, tie - 3.0), (x + 2.0, tie + 2.0)], 0.7, WOOD_DARK)
    # The cut ends at the foot.
    for u, base, _top in stalks:
        f.dot(base[0], base[1] - 1.0, 1.1, RICE_STALK_DARK)
    return f.finish(outline=OUTLINE, width=1.4)


# ---------------------------------------------------------------------------
# Publication.
# ---------------------------------------------------------------------------

SOUTH = ["prop", "scenery", "history", "south_asia"]
EAST = ["prop", "scenery", "history", "east_asia"]

FRAMES: Dict[str, Tuple[int, int]] = {
    "history_great_bath": BATH_FRAME,
    "history_unicorn_seal": SEAL_FRAME,
    "history_seal_gate": GATE_FRAME,
    "history_mud_hut": HUT_FRAME,
    "history_oracle_bones": BONES_FRAME,
    "history_bronze_gate": GATE_FRAME,
    "history_bronze_ding": DING_FRAME,
    "history_rice_sheaf": RICE_FRAME,
}
DRAW = {
    "history_great_bath": _draw_great_bath,
    "history_unicorn_seal": _draw_unicorn_seal,
    "history_seal_gate": _draw_seal_gate,
    "history_mud_hut": _draw_mud_hut,
    "history_oracle_bones": _draw_oracle_bones,
    "history_bronze_gate": _draw_bronze_gate,
    "history_bronze_ding": _draw_bronze_ding,
    "history_rice_sheaf": _draw_rice_sheaf,
}

TARGETS: Dict[str, dict] = {
    "history_great_bath": _publisher("history_great_bath", "Great Bath", LOOP, BATH_FRAME, _draw_great_bath,
                                     {"foot": (192.0, float(BATH_FRAME[1]))}, "Scenery", SOUTH),
    "history_unicorn_seal": _publisher("history_unicorn_seal", "Unicorn Seal", KEY_ROWS, SEAL_FRAME, _draw_unicorn_seal,
                                       {"middle": (34.0, 34.0)}, "Pickup", ["prop", "key", "pickup", "history", "south_asia"]),
    "history_seal_gate": _publisher("history_seal_gate", "Seal Gate", STILL, GATE_FRAME, _draw_seal_gate,
                                    {"foot": (48.0, 384.0)}, "Door", ["prop", "door", "lock", "history", "south_asia"], forward=(0.0, -1.0)),
    "history_mud_hut": _publisher("history_mud_hut", "Mud-Brick House", LOOP, HUT_FRAME, _draw_mud_hut,
                                  {"foot": (128.0, float(HUT_FRAME[1]))}, "Scenery", SOUTH),
    "history_oracle_bones": _publisher("history_oracle_bones", "Oracle Bones", STILL, BONES_FRAME, _draw_oracle_bones,
                                       {"foot": (64.0, float(BONES_FRAME[1]))}, "Scenery", EAST),
    "history_bronze_gate": _publisher("history_bronze_gate", "Bronze Gate", STILL, GATE_FRAME, _draw_bronze_gate,
                                      {"foot": (48.0, 384.0)}, "Door", ["prop", "door", "lock", "history", "east_asia"], forward=(0.0, -1.0)),
    "history_bronze_ding": _publisher("history_bronze_ding", "Bronze Ding", LOOP, DING_FRAME, _draw_bronze_ding,
                                      {"foot": (96.0, float(DING_FRAME[1]))}, "Scenery", EAST),
    "history_rice_sheaf": _publisher("history_rice_sheaf", "Rice Sheaf", LOOP, RICE_FRAME, _draw_rice_sheaf,
                                     {"foot": (48.0, float(RICE_FRAME[1]))}, "Scenery", EAST),
}
