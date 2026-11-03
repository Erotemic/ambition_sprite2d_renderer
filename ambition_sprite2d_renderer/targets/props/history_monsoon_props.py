"""The props of Timbuktu and the Monsoon Coast of the History dimension (biome `history_monsoon`).

The west half of the room is the Sahel: mudbrick walls with wooden spikes
(toron), salt slabs and gold. The east half is a coast of coral stone and
dhows under monsoon clouds. The props are drawn in the cel style of the Art
dimension's cast (`targets/characters/_art_cast_kit.py`) in the warm sepia
of an old textbook, with the colours of the era: adobe ochre, gold, salt
white, turquoise sea and monsoon grey.

- ``history_dhow``: the look of a sweeping platform (`MovingPlatform`
  ``visual``). A dhow with a lateen sail on a mast that leans forward. Its
  deck top is the platform (`platform_looks.ron`: `DHOW_SPAN`, `DHOW_TOP`);
  the sail rises over the deck and the hull hangs under it.
- ``history_salt_slabs``: scenery. Two slabs of rock salt with their
  traders' marks, tied on a wooden frame.
- ``history_mud_tower``: scenery. A tower of mudbrick as the mosques of the
  Sahel build them: a tapered face with ribs, rows of toron, rounded
  pinnacles and an ostrich egg on the top.
- ``history_manuscripts``: scenery. A chest of manuscripts with its lid
  open, and a stack of bound books beside it with one open on the top.
- ``history_gold_pile``: scenery. A heap of gold dust, coins, a bar and a
  nugget. Its ``idle`` row moves a glint over it.

Animations: ``idle``. No drop shadows: the game draws them. The numbers are
frame pixels; the game shows each prop at half its frame.
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
ADOBE = (206, 150, 88, 255)
ADOBE_LIGHT = (230, 186, 128, 255)
ADOBE_SHADE = (164, 110, 62, 255)
ADOBE_DARK = (112, 70, 38, 255)
PLASTER = (238, 222, 190, 255)
SALT = (242, 238, 228, 255)
SALT_SHADE = (200, 194, 182, 255)
SALT_VEIN = (164, 150, 140, 255)
TURQUOISE = (40, 172, 172, 255)
TURQUOISE_DARK = (24, 112, 120, 255)
MONSOON_GREY = (122, 128, 140, 255)
HULL = (156, 100, 58, 255)
HULL_LIGHT = (196, 140, 88, 255)
HULL_DARK = (104, 62, 34, 255)
HULL_WHITE = (236, 228, 208, 255)
SAIL = (244, 234, 208, 255)
SAIL_SHADE = (208, 192, 158, 255)
ROPE = (210, 178, 116, 255)
ROPE_DARK = (130, 100, 62, 255)
GOLD = K.GOLD
GOLD_LIGHT = (255, 228, 130, 255)
GOLD_DARK = K.GOLD_DARK
GOLD_DEEP = (130, 84, 22, 255)
PAGE = (240, 228, 196, 255)
PAGE_SHADE = (206, 188, 150, 255)
LEATHER_RED = (156, 52, 40, 255)
LEATHER_BROWN = (122, 76, 44, 255)
LEATHER_DARK = (78, 46, 28, 255)
SCRIPT_RED = (176, 40, 32, 255)


def _phase(i: int, n: int) -> float:
    return i / float(max(1, n))


def _rect(x0: float, y0: float, x1: float, y1: float) -> List[Point]:
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def _turned_rect(cx: float, cy: float, w: float, h: float, tilt: float) -> List[Point]:
    return K.turn(_rect(cx - w / 2.0, cy - h / 2.0, cx + w / 2.0, cy + h / 2.0), cx, cy, tilt)


def _script(f: K.Frame, x0: float, x1: float, y: float, rng: random.Random, colour: K.RGBA, width: float = 0.7) -> None:
    """A line of flowing script: loops and strokes, with dots over it. It is
    a pattern only, not words."""
    pts = []
    x = x0
    while x < x1:
        pts.append((x, y + rng.uniform(-0.8, 0.8)))
        x += rng.uniform(1.4, 2.6)
        if rng.random() < 0.25:
            pts.append((x, y - rng.uniform(2.0, 3.2)))
            pts.append((x + 0.4, y))
    if len(pts) > 1:
        f.ink(pts, width, colour)
    for _ in range(int((x1 - x0) / 6.0)):
        f.dot(rng.uniform(x0, x1), y - rng.uniform(2.6, 3.6), 0.35, colour)


# ---------------------------------------------------------------------------
# The dhow: its deck is the platform.
# ---------------------------------------------------------------------------

DHOW_FRAME = (320, 192)
DHOW_SPAN = (16.0, 304.0)
DHOW_TOP = 150.0


def _draw_dhow(anim: str, i: int, n: int):
    f = K.Frame(DHOW_FRAME)
    top = DHOW_TOP
    x0, x1 = DHOW_SPAN
    mast_foot, mast_top = (176.0, top), (190.0, 64.0)
    yard_low, yard_high = (300.0, 124.0), (40.0, 10.0)
    # The rigging, behind the sail: stays from the mast head to the bow and the stern.
    f.ink([mast_top, (308.0, 132.0)], 1.0, ROPE_DARK)
    f.ink([mast_top, (22.0, 134.0)], 1.0, ROPE_DARK)
    # The mast, leaning forward.
    f.limb([mast_foot, mast_top], 5.0, HULL_DARK)
    # The lateen sail: a big triangle under the long yard. Its leech bellies
    # out and its foot sags a little over the deck.
    tack, peak, clew = (288.0, 128.0), (48.0, 15.0), (96.0, 141.0)
    sail = [tack]
    for k in range(1, 12):
        sail.append(_on(tack, peak, k / 12.0))
    for k in range(13):
        u = k / 12.0
        p = _on(peak, clew, u)
        sail.append((p[0] - 18.0 * math.sin(math.pi * u), p[1] + 4.0 * math.sin(math.pi * u)))
    for k in range(1, 12):
        u = k / 12.0
        p = _on(clew, tack, u)
        sail.append((p[0], p[1] + 4.0 * math.sin(math.pi * u)))
    f.poly(sail, SAIL)
    # The shade in the belly of the sail, along its leech.
    belly = [_on(peak, clew, 0.1)]
    for k in range(1, 10):
        u = 0.1 + 0.8 * k / 9.0
        p = _on(peak, clew, u)
        belly.append((p[0] - 18.0 * math.sin(math.pi * u), p[1] + 4.0 * math.sin(math.pi * u)))
    for k in range(9, 0, -1):
        u = 0.1 + 0.8 * k / 9.0
        p = _on(peak, clew, u)
        belly.append((p[0] + 6.0, p[1] - 6.0 + 2.0 * math.sin(math.pi * u)))
    f.poly(belly, SAIL_SHADE, body=False)
    # The seams of the cloths of the sail, down from the yard.
    for k in range(1, 9):
        u = k / 9.0
        a = _on(tack, peak, u)
        b = (a[0] - 8.0 - 10.0 * u, min(141.0, a[1] + (128.0 - a[1]) * 0.9 + 10.0))
        f.ink([a, b], 0.8, K.alpha(SAIL_SHADE, 0.95))
    # The yard, over the head of the sail, and the halyard to the mast head.
    f.limb([yard_low, yard_high], 4.0, HULL_DARK)
    f.ink([_on(yard_low, yard_high, 0.42), mast_top], 1.2, ROPE_DARK)
    f.dot(*mast_top, 2.4, HULL_DARK)
    # The sheet: from the clew to the stern.
    f.ink([clew, (40.0, 146.0)], 1.0, ROPE_DARK)
    # The hull: a high stern on the left, a long raked bow on the right.
    hull = [(10.0, 130.0), (21.0, 130.0), (25.0, top), (298.0, top), (310.0, 125.0), (313.0, 128.0), (302.0, 158.0), (278.0, 178.0),
            (232.0, 186.0), (82.0, 186.0), (42.0, 178.0), (20.0, 160.0)]
    f.poly(hull, HULL)
    # The lower hull, white with lime and oil below the waterline.
    f.poly([(36.0, 174.0), (284.0, 174.0), (278.0, 178.0), (232.0, 186.0), (82.0, 186.0), (42.0, 178.0)], HULL_WHITE, body=False)
    # The shade under the gunwale.
    f.poly([(25.0, top + 6.0), (299.0, top + 6.0), (296.0, top + 12.0), (27.0, top + 12.0)], HULL_DARK, body=False)
    # The deck edge: the top of the platform, lit.
    f.poly(_rect(25.0, top, 298.0, top + 4.0), HULL_LIGHT, body=False)
    # The painted band along the gunwale: turquoise with white diamonds.
    f.poly([(26.0, top + 4.0), (299.0, top + 4.0), (299.5, top + 9.0), (26.5, top + 9.0)], TURQUOISE, body=False)
    for k in range(27):
        x = 32.0 + k * 10.0
        f.poly([(x, top + 6.5), (x + 2.6, top + 4.6), (x + 5.2, top + 6.5), (x + 2.6, top + 8.4)], HULL_WHITE, body=False)
    # The planks of the hull.
    for y, a, b in ((164.0, 24.0, 300.0), (170.0, 30.0, 290.0)):
        f.ink([(a, y), (b, y - 4.0)], 0.9, HULL_DARK)
    for x in (80.0, 150.0, 220.0):
        f.ink([(x, top + 12.0), (x + 2.0, 174.0)], 0.8, K.alpha(HULL_DARK, 0.7))
    # The carved stern post, and the stem head at the bow.
    f.poly(_rect(10.0, 128.0, 22.0, 134.0), HULL_DARK)
    f.ink([(13.0, 140.0), (19.0, 140.0)], 1.2, TURQUOISE)
    f.ink([(15.0, 146.0), (21.0, 146.0)], 1.2, HULL_WHITE)
    f.limb([(308.0, 130.0), (313.0, 124.0)], 3.0, HULL_DARK)
    return f.finish(outline=OUTLINE, width=1.6)


def _on(a: Point, b: Point, u: float) -> Point:
    return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)


# ---------------------------------------------------------------------------
# The salt slabs: two slabs of rock salt tied on a frame.
# ---------------------------------------------------------------------------

SALT_FRAME = (128, 96)
SALT_FOOT = 90.0


def _slab(f: K.Frame, x0: float, y0: float, x1: float, y1: float, rng: random.Random, mark: str) -> None:
    """A slab of rock salt: a block with chipped corners, grey veins and a
    trader's mark in charcoal."""
    c = 3.0
    pts = [(x0 + c, y0), (x1 - c - 1.0, y0 + 0.5), (x1, y0 + c + 1.0), (x1 - 0.5, y1 - c), (x1 - c, y1), (x0 + c + 1.0, y1),
           (x0, y1 - c - 1.0), (x0 + 0.5, y0 + c)]
    f.poly(pts, SALT)
    f.poly([(x1 - 9.0, y0 + 0.5), (x1 - c - 1.0, y0 + 0.5), (x1, y0 + c + 1.0), (x1 - 0.5, y1 - c), (x1 - c, y1), (x1 - 9.0, y1)], SALT_SHADE, body=False)
    for k in range(5):
        y = y0 + 6.0 + k * (y1 - y0 - 12.0) / 4.0
        vein = [(x0 + 3.0, y)]
        for s in range(1, 6):
            vein.append((x0 + 3.0 + (x1 - x0 - 6.0) * s / 5.0, y + rng.uniform(-2.0, 2.0)))
        f.ink(vein, 0.8, K.alpha(SALT_VEIN, 0.8))
    cx, cy = (x0 + x1) / 2.0 - 2.0, (y0 + y1) / 2.0
    if mark == "diamond":
        f.ink([(cx, cy - 6.0), (cx + 5.0, cy), (cx, cy + 6.0), (cx - 5.0, cy), (cx, cy - 6.0)], 1.4, OUTLINE)
        f.dot(cx, cy, 1.2, OUTLINE)
    else:
        f.ink([(cx - 5.0, cy - 5.0), (cx + 5.0, cy + 5.0)], 1.4, OUTLINE)
        f.ink([(cx + 5.0, cy - 5.0), (cx - 5.0, cy + 5.0)], 1.4, OUTLINE)
        f.ink([(cx - 6.0, cy), (cx + 6.0, cy)], 1.2, OUTLINE)


def _draw_salt(anim: str, i: int, n: int):
    f = K.Frame(SALT_FRAME)
    rng = random.Random("history_salt_slabs")
    foot = SALT_FOOT
    # The frame: two legs and a pole across their tops.
    for a, b in (((18.0, 24.0), (12.0, foot)), ((110.0, 24.0), (116.0, foot))):
        f.limb([a, b], 4.0, K.WOOD)
    f.limb([(10.0, 24.0), (118.0, 24.0)], 4.6, K.WOOD)
    f.ink([(12.0, 23.0), (116.0, 23.0)], 0.8, K.shade(K.WOOD, 1.3))
    # The slabs, standing in the frame.
    _slab(f, 22.0, 28.0, 62.0, foot - 1.0, rng, "diamond")
    _slab(f, 66.0, 30.0, 106.0, foot - 1.0, rng, "cross")
    # The ropes that tie them to the frame and to each other.
    for y in (46.0, 74.0):
        f.limb([(16.0, y), (112.0, y + 1.0)], 2.4, ROPE)
        f.ink([(16.0, y + 0.6), (112.0, y + 1.6)], 0.6, ROPE_DARK)
    for x in (20.0, 64.0, 108.0):
        f.limb([(x, 22.0), (x + 1.0, 30.0)], 2.2, ROPE)
        f.ellipse(x, 24.0, 2.6, 2.6, ROPE)
    return f.finish(outline=OUTLINE, width=1.4)


# ---------------------------------------------------------------------------
# The mud tower: mudbrick, ribs, toron and pinnacles.
# ---------------------------------------------------------------------------

TOWER_FRAME = (192, 448)
TOWER_FOOT = 440.0
TOWER_BASE = (28.0, 164.0)
TOWER_TOP_Y = 136.0
TOWER_TOP = (54.0, 138.0)


def _tower_edge(y: float, side: int) -> float:
    """The x of the left (`side` -1) or right (+1) edge of the tower's
    face at row `y`: a taper, with the waver of a wall plastered by hand."""
    u = (y - TOWER_TOP_Y) / (TOWER_FOOT - TOWER_TOP_Y)
    base = TOWER_BASE[0] if side < 0 else TOWER_BASE[1]
    top = TOWER_TOP[0] if side < 0 else TOWER_TOP[1]
    return top + (base - top) * u + 1.2 * math.sin(y * 0.07 + side)


def _draw_mud_tower(anim: str, i: int, n: int):
    f = K.Frame(TOWER_FRAME)
    foot = TOWER_FOOT
    rng = random.Random("history_mud_tower")
    ys = [TOWER_TOP_Y + (foot - TOWER_TOP_Y) * k / 20.0 for k in range(21)]
    left = [(_tower_edge(y, -1), y) for y in ys]
    right = [(_tower_edge(y, 1), y) for y in ys]
    # The pinnacles: one tall cone in the middle with an egg, and one at each corner.
    for cx, base_w, tip_y in ((96.0, 44.0, 36.0), (62.0, 16.0, 98.0), (130.0, 16.0, 98.0)):
        cone = []
        for k in range(13):
            u = k / 12.0
            half = base_w / 2.0 * (1.0 - u ** 1.6)
            cone.append((cx - half, TOWER_TOP_Y + 2.0 - (TOWER_TOP_Y + 2.0 - tip_y) * u))
        cone += [(2.0 * cx - x, y) for x, y in cone[::-1]]
        f.poly(cone, ADOBE)
        f.poly([(cx + 2.0, tip_y + 2.0)] + [(2.0 * cx - x, y) for x, y in cone[:12]][::-1] + [(cx + 2.0, TOWER_TOP_Y + 2.0)], ADOBE_SHADE, body=False)
    f.ellipse(96.0, 30.0, 5.0, 7.0, SALT)
    f.ellipse(97.5, 31.0, 2.4, 4.0, SALT_SHADE, body=False)
    for cx, tip_y in ((96.0, 60.0), (62.0, 110.0), (130.0, 110.0)):
        f.limb([(cx - 6.0, tip_y), (cx + 6.0, tip_y)], 3.0, K.WOOD_DARK)
    # The face of the tower, and its shaded side.
    f.poly(left + right[::-1], ADOBE)
    f.poly([((l[0] + r[0]) / 2.0 + (r[0] - l[0]) * 0.22, l[1]) for l, r in zip(left, right)] + right[::-1], ADOBE_SHADE, body=False)
    # The plaster cap round the top of the face.
    f.poly([(TOWER_TOP[0] - 2.0, TOWER_TOP_Y - 2.0), (TOWER_TOP[1] + 2.0, TOWER_TOP_Y - 2.0), (_tower_edge(TOWER_TOP_Y + 10.0, 1) + 1.0, TOWER_TOP_Y + 10.0),
            (_tower_edge(TOWER_TOP_Y + 10.0, -1) - 1.0, TOWER_TOP_Y + 10.0)], PLASTER)
    # The ribs up the face: buttresses that stand out a little.
    for u in (0.3, 0.7):
        rib = [(left[k][0] + (right[k][0] - left[k][0]) * u, ys[k]) for k in range(len(ys))]
        f.limb([(x - 2.0, y) for x, y in rib[1:]], 3.0, ADOBE_LIGHT, body=False)
        f.ink([(x + 1.6, y) for x, y in rib[1:]], 1.4, ADOBE_DARK)
    # The toron: rows of palm wood beams. They stand out of each side and
    # show their ends on the face.
    for row, y in enumerate((168.0, 214.0, 260.0, 306.0, 352.0, 398.0)):
        lx, rx = _tower_edge(y, -1), _tower_edge(y, 1)
        f.limb([(lx + 2.0, y), (lx - 11.0, y + 1.0)], 4.0, K.WOOD)
        f.limb([(rx - 2.0, y), (rx + 11.0, y + 1.0)], 4.0, K.WOOD_DARK)
        count = 5
        for k in range(count):
            x = lx + (rx - lx) * (k + 0.5) / count + (6.0 if row % 2 else 0.0) - 3.0
            f.poly(_rect(x - 3.0, y - 2.4, x + 3.0, y + 2.4), K.WOOD)
            f.poly(_rect(x + 0.6, y - 2.4, x + 3.0, y + 2.4), K.WOOD_DARK, body=False)
            f.ink([(x - 2.0, y - 2.6), (x - 2.0, y + 2.6)], 0.6, K.shade(K.WOOD, 1.3))
    # The courses of mudbrick, faint under the plaster.
    for k in range(40):
        y = rng.uniform(150.0, foot - 10.0)
        lx, rx = _tower_edge(y, -1), _tower_edge(y, 1)
        x = rng.uniform(lx + 6.0, rx - 20.0)
        f.ink([(x, y), (x + rng.uniform(8.0, 16.0), y + rng.uniform(-0.6, 0.6))], 0.7, K.alpha(ADOBE_DARK, 0.4))
    # Two slit windows and the door at the foot.
    for y in (232.0, 330.0):
        f.poly(_rect(92.0, y, 100.0, y + 18.0), ADOBE_DARK, body=False)
    door = [(84.0, foot), (84.0, 410.0), (88.0, 403.0), (96.0, 400.0), (104.0, 403.0), (108.0, 410.0), (108.0, foot)]
    f.poly(K.grow(door, 3.0), PLASTER, body=False)
    f.poly(door, K.WOOD_DARK, body=False)
    f.ink([(96.0, 401.0), (96.0, foot)], 1.0, OUTLINE)
    for y in (414.0, 428.0):
        for x in (90.0, 102.0):
            f.dot(x, y, 1.4, GOLD)
    return f.finish(outline=OUTLINE, width=1.8)


# ---------------------------------------------------------------------------
# The manuscripts: a chest of them, and a stack.
# ---------------------------------------------------------------------------

BOOKS_FRAME = (128, 96)
BOOKS_FOOT = 92.0


def _draw_manuscripts(anim: str, i: int, n: int):
    f = K.Frame(BOOKS_FRAME)
    rng = random.Random("history_manuscripts")
    foot = BOOKS_FOOT
    # The lid, open and leaning back.
    f.poly([(14.0, 52.0), (82.0, 52.0), (86.0, 20.0), (20.0, 16.0)], K.WOOD_DARK)
    f.poly([(18.0, 50.0), (78.0, 50.0), (82.0, 24.0), (23.0, 20.0)], K.shade(K.WOOD_DARK, 0.8), body=False)
    for x in (20.0, 80.0):
        f.dot(x, 30.0 if x < 50 else 34.0, 1.6, GOLD)
    # The manuscripts in the chest: loose quires in leather folders, tied with cord.
    for cx, cy, tilt, cover in ((26.0, 48.0, -14.0, LEATHER_RED), (40.0, 44.0, -4.0, LEATHER_BROWN), (54.0, 46.0, 8.0, None),
                                (68.0, 44.0, -6.0, LEATHER_RED), (80.0, 48.0, 14.0, LEATHER_BROWN)):
        if cover is None:
            f.poly(_turned_rect(cx, cy, 13.0, 22.0, tilt), PAGE)
            for k in range(4):
                f.ink(K.turn([(cx - 4.5, cy - 7.0 + k * 4.0), (cx + 4.5, cy - 7.0 + k * 4.0)], cx, cy, tilt), 0.6, K.alpha(OUTLINE, 0.6))
        else:
            f.poly(_turned_rect(cx, cy, 13.0, 22.0, tilt), cover)
            f.poly(_turned_rect(cx + 0.5, cy - 1.0, 11.0, 20.0, tilt), PAGE, body=False)
            f.poly(_turned_rect(cx + 1.5, cy + 1.0, 11.0, 18.0, tilt), cover, body=False)
            f.ink(K.turn([(cx - 6.5, cy), (cx + 6.5, cy)], cx, cy, tilt), 1.0, ROPE)
    # The chest: wood, with bands and brass bosses.
    f.poly(_rect(12.0, 52.0, 86.0, foot), K.WOOD)
    f.poly(_rect(66.0, 52.0, 86.0, foot), K.WOOD_DARK, body=False)
    f.poly(_rect(12.0, 52.0, 86.0, 58.0), K.shade(K.WOOD, 1.15), body=False)
    for x in (24.0, 74.0):
        f.poly(_rect(x - 3.0, 52.0, x + 3.0, foot), LEATHER_DARK, body=False)
    for x in (16.0, 49.0, 82.0):
        for y in (62.0, 84.0):
            f.dot(x, y, 2.0, GOLD)
            f.dot(x - 0.5, y - 0.6, 0.7, GOLD_LIGHT)
    f.poly(_rect(44.0, 64.0, 54.0, 74.0), GOLD, body=False)
    f.dot(49.0, 69.0, 1.4, OUTLINE)
    # The stack beside the chest: three bound books, and one open on top.
    for k, (colour, h) in enumerate(((LEATHER_BROWN, 6.0), (LEATHER_RED, 5.0), (LEATHER_DARK, 6.0))):
        y1 = foot - k * 6.0
        x0, x1 = 90.0 + k * 1.0, 122.0 - k * 1.0
        f.poly(_rect(x0, y1 - h, x1, y1), colour)
        f.poly(_rect(x0 + 2.0, y1 - h + 1.4, x1, y1 - 1.4), PAGE, body=False)
        f.ink([(x0 + 3.0, y1 - h / 2.0), (x1 - 1.0, y1 - h / 2.0)], 0.5, PAGE_SHADE)
    top = foot - 18.0
    pages = [(88.0, top), (105.0, top - 3.0), (122.0, top), (122.0, top - 14.0), (105.0, top - 16.0), (88.0, top - 14.0)]
    f.poly(pages, PAGE)
    f.poly([(105.0, top - 3.0), (122.0, top), (122.0, top - 14.0), (105.0, top - 16.0)], PAGE_SHADE, body=False)
    f.ink([(105.0, top - 3.0), (105.0, top - 16.0)], 0.8, K.alpha(OUTLINE, 0.8))
    for k in range(4):
        y = top - 12.0 + k * 3.0
        _script(f, 90.0, 104.0, y + 0.0, rng, SCRIPT_RED if k == 0 else OUTLINE, 0.6)
        _script(f, 107.0, 120.0, y - 0.6, rng, OUTLINE, 0.6)
    return f.finish(outline=OUTLINE, width=1.4)


# ---------------------------------------------------------------------------
# The gold pile: dust, coins, a bar and a nugget.
# ---------------------------------------------------------------------------

GOLD_FRAME = (128, 64)
GOLD_FOOT = 58.0
#: The places the glint visits, in turn.
GLINTS = [(48.0, 30.0), (82.0, 38.0), (64.0, 22.0), (30.0, 46.0)]


def _sparkle(f: K.Frame, x: float, y: float, r: float, a: float) -> None:
    star = []
    for k in range(8):
        ang = k * math.pi / 4.0
        rr = r if k % 2 == 0 else r * 0.22
        star.append((x + math.cos(ang) * rr, y + math.sin(ang) * rr))
    f.glow_poly(star, K.alpha(K.WHITE, a))
    f.glow(x, y, r * 0.5, K.alpha(GOLD_LIGHT, 0.6 * a))


def _draw_gold(anim: str, i: int, n: int):
    t = _phase(i, n)
    f = K.Frame(GOLD_FRAME)
    rng = random.Random("history_gold_pile")
    foot = GOLD_FOOT
    # The bar, leaning on the heap at the back.
    bar = [(86.0, 30.0), (114.0, 36.0), (112.0, 46.0), (84.0, 40.0)]
    f.poly(bar, GOLD)
    f.poly([(86.0, 30.0), (114.0, 36.0), (113.0, 39.0), (85.5, 33.0)], GOLD_LIGHT, body=False)
    f.poly([(112.0, 46.0), (84.0, 40.0), (84.6, 37.0), (112.6, 43.0)], GOLD_DARK, body=False)
    # The heap of gold dust, lumpy.
    heap = [(8.0, foot)]
    for k in range(1, 20):
        u = k / 20.0
        x = 8.0 + 108.0 * u
        y = foot - 40.0 * math.sin(math.pi * u) ** 1.3 - 2.0 * math.sin(u * 23.0)
        heap.append((x, y))
    heap.append((116.0, foot))
    f.poly(heap, GOLD)
    f.poly([(62.0, foot)] + [(x, y + 6.0) for x, y in heap[11:-1]] + [(116.0, foot)], GOLD_DARK, body=False)
    for _ in range(30):
        x = rng.uniform(16.0, 108.0)
        ymax = foot - 40.0 * math.sin(math.pi * (x - 8.0) / 108.0) ** 1.3 + 4.0
        y = rng.uniform(ymax, foot - 3.0)
        f.dot(x, y, 0.7, GOLD_LIGHT if rng.random() < 0.6 else GOLD_DEEP)
    # Coins on the heap and on the ground.
    for x, y, rx in ((38.0, 40.0, 5.5), (60.0, 30.0, 5.0), (74.0, 44.0, 5.5), (50.0, 52.0, 6.0), (92.0, 52.0, 5.0), (24.0, 53.0, 5.0),
                     (106.0, 55.0, 4.6), (12.0, 56.0, 3.8)):
        f.ellipse(x, y, rx, rx * 0.5, GOLD_DARK)
        f.ellipse(x, y - 0.6, rx * 0.86, rx * 0.4, GOLD_LIGHT, body=False)
        f.ellipse(x, y - 0.6, rx * 0.5, rx * 0.22, GOLD, body=False)
    # A nugget at the foot.
    nug = K.ellipse_points(118.0, foot - 4.0, 5.0, 3.6, 9, 1.0, rng)
    f.poly(nug, GOLD)
    f.poly(K.ellipse_points(119.0, foot - 3.0, 3.0, 2.0, 7), GOLD_DARK, body=False)
    # The glint: it moves from place to place and flares at each.
    k = int(t * len(GLINTS) * 2.0)
    if k % 2 == 0:
        x, y = GLINTS[(k // 2) % len(GLINTS)]
        u = (t * len(GLINTS) * 2.0) % 1.0
        _sparkle(f, x, y, 4.0 + 5.0 * math.sin(math.pi * (0.3 + 0.7 * u)), 0.95)
    return f.finish(outline=OUTLINE, width=1.4, glow_blur=1.2)


# ---------------------------------------------------------------------------
# Publication.
# ---------------------------------------------------------------------------

SCENERY = ["prop", "scenery", "history", "monsoon"]

FRAMES: Dict[str, Tuple[int, int]] = {
    "history_dhow": DHOW_FRAME,
    "history_salt_slabs": SALT_FRAME,
    "history_mud_tower": TOWER_FRAME,
    "history_manuscripts": BOOKS_FRAME,
    "history_gold_pile": GOLD_FRAME,
}
DRAW = {
    "history_dhow": _draw_dhow,
    "history_salt_slabs": _draw_salt,
    "history_mud_tower": _draw_mud_tower,
    "history_manuscripts": _draw_manuscripts,
    "history_gold_pile": _draw_gold,
}

TARGETS: Dict[str, dict] = {
    "history_dhow": _publisher("history_dhow", "Dhow", STILL, DHOW_FRAME, _draw_dhow, {"top": ((DHOW_SPAN[0] + DHOW_SPAN[1]) / 2.0, DHOW_TOP)},
                               "Scenery", ["prop", "platform", "history", "monsoon"]),
    "history_salt_slabs": _publisher("history_salt_slabs", "Salt Slabs", STILL, SALT_FRAME, _draw_salt, {"foot": (64.0, float(SALT_FRAME[1]))}, "Scenery",
                                     SCENERY),
    "history_mud_tower": _publisher("history_mud_tower", "Mud Tower", STILL, TOWER_FRAME, _draw_mud_tower, {"foot": (96.0, float(TOWER_FRAME[1]))},
                                    "Scenery", SCENERY),
    "history_manuscripts": _publisher("history_manuscripts", "Manuscripts", STILL, BOOKS_FRAME, _draw_manuscripts, {"foot": (64.0, float(BOOKS_FRAME[1]))},
                                      "Scenery", SCENERY),
    "history_gold_pile": _publisher("history_gold_pile", "Gold Pile", LOOP, GOLD_FRAME, _draw_gold, {"foot": (64.0, float(GOLD_FRAME[1]))}, "Scenery",
                                    SCENERY),
}
