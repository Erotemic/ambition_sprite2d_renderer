"""The Void (the Magical dimension, Mary-O's): the rooms past the Void
Lizard's bridge where the picture has lost its colour. Black and white, as
the void's own things are: a body with no light in it and a white edge.

Drawn in room coordinates (`_district_props`) on the numbers of
`tools/ambition_ldtk_tools/specs/magical/make_specs.py`:

- `magical_void_rift` (floor y 576, roof y 64): `rift_tear`, its west end,
  where the castle's coloured stone breaks into black shards with white
  edges; `rift_outlines`, the things of the town the void has half rubbed
  out, in white line: a star lamp, the star tree, a house.
- `magical_void_gallery` (floor y 576; its hole down x 1200..1264):
  `gallery_exhibits`, THINGS THE VOID HAS TAKEN: four plinths, each with the
  white outline of what was on it (a star lamp, a cart's wheel, a crescent
  from the bakery, a wand).
- `magical_void_falls` (768 by 1280, floor y 1216): `falls_cascade`, the
  void falling down the east side like water, from a crack in the roof to a
  pool at the bottom.
- `magical_void_heart` (floor y 576): `heart_black_star`, the first star
  that went out, as big as the room, asleep.
- The rift's pool and the heart's wall: `rift_pool`, the void standing in a
  cut in the rift's floor (x 1880..2160), black, its rings white;
  `rift_shard`, the look of the shards across it (each 60 by 16: they crumble
  under a body and come back); `void_crack_wall`, the look of the heart's
  west wall (32 by 96), black, cracked with white.
- `magical_void_nursery` (640 by 640, floor y 576; behind the heart's west
  wall, which breaks): `nursery_cradles`, where a star goes the first time it
  goes out: crescent cradles in white line, a little black star asleep in
  each, and a mobile of outlined stars over them.

Animations: ``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

import math
from typing import Dict

from ._district_props import Piece, targets
from ._town_kit import box, mix
from .magical_void_props import STONE, STONE_DARK, STONE_LIGHT

FLOOR, ROOF = 576, 64
FALLS_FLOOR = 1216
GALLERY_HOLE = (1200, 1264)

VOID = (8, 6, 12)
EDGE = (240, 238, 250)
GREY = (120, 118, 128)
PAL = {"stone": GREY, "stone_light": EDGE, "dark": VOID, "lamp": EDGE}


def shrink(pts, d):
    """`pts` drawn in by `d` toward their middle."""
    cx = sum(x for x, _ in pts) / len(pts)
    cy = sum(y for _, y in pts) / len(pts)
    out = []
    for x, y in pts:
        r = math.hypot(x - cx, y - cy) or 1.0
        k = max(0.0, (r - d) / r)
        out.append((cx + (x - cx) * k, cy + (y - cy) * k))
    return out


def void_poly(c, pts, edge=1.8):
    """A shape of void: black, with a white edge."""
    c.put(c.mask(lambda p: p.poly(pts)), EDGE)
    c.put(c.mask(lambda p: p.poly(shrink(pts, edge))), VOID)


def star_pts(x, y, r, k=0.45, tilt=0.0):
    return [(x + (r if i % 2 == 0 else r * k) * math.cos(-math.pi / 2 + tilt + i * math.pi / 5),
             y + (r if i % 2 == 0 else r * k) * math.sin(-math.pi / 2 + tilt + i * math.pi / 5)) for i in range(10)]


def dashed(c, pts, w=2.0, dash=14.0, gap=9.0, colour=EDGE, a=1.0):
    """A white line along `pts`, broken: the void has rubbed bits out."""
    segs = []
    carry, on = 0.0, True
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = math.hypot(x1 - x0, y1 - y0)
        t = 0.0
        while t < n:
            step = min((dash if on else gap) - carry, n - t)
            if on:
                segs.append(((x0 + (x1 - x0) * t / n, y0 + (y1 - y0) * t / n), (x0 + (x1 - x0) * (t + step) / n, y0 + (y1 - y0) * (t + step) / n)))
            t += step
            carry += step
            if carry >= (dash if on else gap) - 1e-6:
                carry, on = 0.0, not on
    c.put(c.mask(lambda p: [p.line([a0, a1], w) for a0, a1 in segs]), colour, a)


def circle(x, y, r, n=40):
    return [(x + r * math.cos(2 * math.pi * i / n), y + r * math.sin(2 * math.pi * i / n)) for i in range(n + 1)]


def tear(c, k):
    # The castle's stone, in its colour, at the west end; it breaks as it
    # goes east, and each piece that comes away has lost its colour.
    rows = range(ROOF, FLOOR, 48)
    for j, y in enumerate(rows):
        reach = 70 + (j * 37) % 60
        off = 0 if j % 2 else 30
        for x in range(-30 + off, reach, 60):
            c.put(c.mask(box(x, y, x + 58, y + 46)), STONE)
            c.put(c.mask(box(x, y, x + 58, y + 3)), STONE_LIGHT)
            c.put(c.mask(box(x + 54, y, x + 58, y + 46)), STONE_DARK)
        # The broken edge: shards come away, smaller and further, colourless.
        for i in range(5):
            sx = reach + 20 + i * 44 + (j * 13 + i * 29) % 26
            sy = y + 6 + (i * 17 + j * 11) % 30
            s = max(5.0, 20 - i * 3.4)
            pts = [(sx, sy), (sx + s, sy + s * 0.3), (sx + s * 0.7, sy + s), (sx - s * 0.2, sy + s * 0.7)]
            void_poly(c, pts, 1.4)


def outlines(c, k):
    # A star lamp, the star tree, a house: as the town drew them, rubbed out.
    x = 820
    dashed(c, [(x, FLOOR), (x, FLOOR - 130)], 2.4)
    dashed(c, star_pts(x, FLOOR - 146, 18, 0.5) + [star_pts(x, FLOOR - 146, 18, 0.5)[0]], 2.0, 10, 7)
    x = 1180
    dashed(c, [(x - 10, FLOOR), (x - 4, FLOOR - 150), (x + 6, FLOOR - 200)], 2.4)
    dashed(c, [(x + 10, FLOOR), (x + 8, FLOOR - 150)], 2.4)
    for dx, dy, r in ((-80, -250, 60), (0, -290, 76), (80, -250, 60)):
        dashed(c, circle(x + dx, FLOOR + dy, r), 2.0, 16, 12)
    for dx, dy in ((-90, -240), (10, -300), (70, -230)):
        p = star_pts(x + dx, FLOOR + dy, 9, 0.5)
        dashed(c, p + [p[0]], 1.6, 8, 6)
    x0, x1 = 1460, 1660
    dashed(c, [(x0, FLOOR), (x0, FLOOR - 170), ((x0 + x1) / 2, FLOOR - 250), (x1, FLOOR - 170), (x1, FLOOR)], 2.4, 22, 14)
    dashed(c, [(x0 + 80, FLOOR), (x0 + 80, FLOOR - 70), (x0 + 120, FLOOR - 70), (x0 + 120, FLOOR)], 2.0)
    dashed(c, [(x0 + 30, FLOOR - 140), (x0 + 70, FLOOR - 140), (x0 + 70, FLOOR - 100), (x0 + 30, FLOOR - 100), (x0 + 30, FLOOR - 140)], 1.8)


def plinth(c, x, top=FLOOR - 90):
    void_poly(c, [(x - 40, FLOOR), (x + 40, FLOOR), (x + 40, top), (x - 40, top)], 2.0)
    void_poly(c, [(x - 48, top), (x + 48, top), (x + 48, top - 10), (x - 48, top - 10)], 2.0)
    c.put(c.mask(box(x - 22, FLOOR - 52, x + 22, FLOOR - 40)), EDGE, 0.85)


def exhibits(c, k):
    top = FLOOR - 100
    # 1. A star lamp, switched off.
    x = 620
    plinth(c, x)
    c.put(c.mask(lambda p: p.line([(x, top), (x, top - 120)], 2.4)), EDGE)
    p = star_pts(x, top - 136, 18, 0.5)
    c.put(c.mask(lambda q: q.line(p + [p[0]], 2.0)), EDGE)
    # 2. The cart's wheel.
    x = 900
    plinth(c, x)
    c.put(c.mask(lambda q: q.ring(x, top - 52, 40, 2.4)), EDGE)
    c.put(c.mask(lambda q: [q.line([(x, top - 52), (x + 38 * math.cos(a), top - 52 + 38 * math.sin(a))], 1.8) for a in (0.3, 1.35, 2.4, 3.45, 4.5, 5.55)]), EDGE)
    c.put(c.mask(lambda q: q.ring(x, top - 52, 6, 1.8)), EDGE)
    # 3. A crescent, from the Star Bakery.
    x = 1440
    plinth(c, x)
    c.put(c.mask(lambda q: q.ellipse(x, top - 50, 36)), EDGE)
    c.put(c.mask(lambda q: q.ellipse(x, top - 50, 33)), VOID)
    c.put(c.mask(lambda q: q.ellipse(x + 18, top - 58, 32)), VOID)
    c.put(c.mask(lambda q: q.ring(x + 18, top - 58, 32, 0.01)), VOID)
    # 4. A wand, bent (Wanda never got it back).
    x = 1640
    plinth(c, x)
    c.put(c.mask(lambda q: q.line([(x - 20, top - 8), (x + 2, top - 60), (x + 26, top - 82)], 2.6)), EDGE)
    p = star_pts(x + 30, top - 92, 12, 0.5, 0.4)
    c.put(c.mask(lambda q: q.line(p + [p[0]], 1.8)), EDGE)
    # The rope that keeps you off them, on its posts.
    posts = (520, 760, 1040, 1340, 1540, 1720)
    for px in posts:
        void_poly(c, [(px - 4, FLOOR), (px + 4, FLOOR), (px + 4, FLOOR - 50), (px - 4, FLOOR - 50)], 1.4)
        c.put(c.mask(lambda q: q.ellipse(px, FLOOR - 54, 6)), EDGE)
    for a, b in ((520, 760), (760, 1040), (1340, 1540), (1540, 1720)):
        pts = [(a + (b - a) * t / 12, FLOOR - 48 + 16 * math.sin(math.pi * t / 12)) for t in range(13)]
        c.put(c.mask(lambda q: q.line(pts, 1.8)), EDGE, 0.8)


def cascade(c, k):
    # The crack it comes from, in the roof.
    void_poly(c, [(600, ROOF), (720, ROOF), (690, ROOF + 26), (650, ROOF + 18)], 2.0)
    # The fall: a black stream, white at its edges, rippled down its face.
    def x_of(y, side):
        wob = 6 * math.sin(y / 37.0) + 3 * math.sin(y / 11.0 + side)
        return (614 if side < 0 else 706) + wob * (1 if side < 0 else -1)
    ys = list(range(ROOF + 18, FALLS_FLOOR - 20, 8))
    left = [(x_of(y, -1), y) for y in ys]
    right = [(x_of(y, 1), y) for y in ys]
    c.put(c.mask(lambda p: p.poly(left + right[::-1])), VOID)
    c.put(c.mask(lambda p: (p.line(left, 2.2), p.line(right, 2.2))), EDGE)
    for i, y in enumerate(range(ROOF + 80, FALLS_FLOOR - 60, 64)):
        x = 640 + (i * 23) % 50
        c.put(c.mask(lambda p: p.line([(x, y), (x + 4, y + 30)], 1.2)), EDGE, 0.55)
    # The pool at the foot, its rings.
    void_poly(c, [(560, FALLS_FLOOR), (752, FALLS_FLOOR), (752, FALLS_FLOOR - 22), (560, FALLS_FLOOR - 16)], 2.0)
    for r, a in ((40, 0.8), (70, 0.5), (96, 0.3)):
        c.put(c.mask(lambda p: p.line([(660 + r * math.cos(t / 10 * math.pi), FALLS_FLOOR - 18 + 5 * math.sin(t / 10 * math.pi)) for t in range(11)], 1.4)), EDGE, a)


def black_star(c, k):
    x, y, r = 700, 320, 236
    pts = star_pts(x, y, r, 0.47, 0.06)
    c.put(c.mask(lambda p: p.poly(pts)), EDGE)
    c.put(c.mask(lambda p: p.poly(shrink(pts, 3.2))), VOID)
    # A second edge inside it, faint: it was lit, once.
    c.put(c.mask(lambda p: p.line(shrink(pts, 22) + [shrink(pts, 22)[0]], 1.2)), GREY, 0.6)
    # Asleep: two shut eyes, a mouth that says nothing.
    for ex in (-58, 58):
        c.put(c.mask(lambda p: p.line([(x + ex - 26, y - 6), (x + ex, y + 8), (x + ex + 26, y - 6)], 3.2)), EDGE)
    c.put(c.mask(lambda p: p.line([(x - 18, y + 70), (x + 18, y + 70)], 2.4)), EDGE, 0.8)
    # A crack down one point, and the light still in it.
    crack = [(x + 40, y - 150), (x + 26, y - 110), (x + 44, y - 80), (x + 30, y - 40)]
    c.put(c.mask(lambda p: p.line(crack, 4.0), blur=3), EDGE, 0.5)
    c.put(c.mask(lambda p: p.line(crack, 1.6)), EDGE)
    # What it breathes out: specks, drifting up.
    for i in range(14):
        sx = x - 260 + (i * 97) % 520
        sy = 100 + (i * 53) % 380
        c.put(c.mask(lambda p: p.ellipse(sx, sy, 1.8 + (i % 3) * 0.8)), EDGE, 0.75)


def cradles(c, k):
    for i, x in enumerate((140, 320, 500)):
        # A crescent rocking on the floor, in white line: the cradle.
        arc = [(x + 60 * math.cos(math.pi * t / 16), FLOOR - 40 + 34 * math.sin(math.pi * t / 16)) for t in range(17)]
        c.put(c.mask(lambda p: p.line(arc, 2.6)), EDGE)
        c.put(c.mask(lambda p: p.line([(x - 60, FLOOR - 40), (x + 60, FLOOR - 40)], 1.4)), EDGE, 0.6)
        # Its star, asleep, little.
        pts = star_pts(x, FLOOR - 40, 22, 0.47, 0.2 * (i - 1))
        void_poly(c, pts, 1.6)
        for ex in (-7, 7):
            c.put(c.mask(lambda p: p.line([(x + ex - 4, FLOOR - 42), (x + ex, FLOOR - 39), (x + ex + 4, FLOOR - 42)], 1.2)), EDGE)
    # The mobile over them, from the roof.
    c.put(c.mask(lambda p: p.line([(320, ROOF), (320, ROOF + 90)], 1.4)), EDGE)
    c.put(c.mask(lambda p: p.line([(180, ROOF + 90), (460, ROOF + 90)], 1.8)), EDGE)
    for x, ln in ((180, 60), (270, 90), (370, 70), (460, 100)):
        c.put(c.mask(lambda p: p.line([(x, ROOF + 90), (x, ROOF + 90 + ln)], 1.0)), EDGE, 0.8)
        pts = star_pts(x, ROOF + 104 + ln, 12, 0.5)
        c.put(c.mask(lambda p: p.line(pts + [pts[0]], 1.6)), EDGE)


POOL = (1880, 2160)


def pool(c, k):
    x0, x1 = POOL
    c.put(c.mask(box(x0, FLOOR, x1, FLOOR + 64)), VOID)
    c.put(c.mask(lambda p: (p.line([(x0, FLOOR), (x0, FLOOR + 64)], 2), p.line([(x1, FLOOR), (x1, FLOOR + 64)], 2))), EDGE)
    for i, y in enumerate((FLOOR + 26, FLOOR + 40, FLOOR + 54)):
        pts = [(x0 + 10 + t * (x1 - x0 - 20) / 24, y + 3 * math.sin(t * 0.9 + i)) for t in range(25)]
        dashed(c, pts, 1.4, 18 + i * 6, 10, EDGE, 0.8 - i * 0.2)


def shard(c, k):
    void_poly(c, [(0, 0), (60, 0), (56, 16), (6, 14)], 1.6)
    c.put(c.mask(lambda p: p.line([(18, 2), (24, 8), (20, 13)], 1.0)), EDGE, 0.8)
    c.put(c.mask(lambda p: p.line([(42, 1), (38, 9)], 1.0)), EDGE, 0.6)


def crack_wall(c, k):
    void_poly(c, [(0, 0), (32, 0), (32, 96), (0, 96)], 1.6)
    crack = [(14, 0), (20, 22), (10, 44), (22, 66), (14, 96)]
    c.put(c.mask(lambda p: p.line(crack, 1.6)), EDGE)
    c.put(c.mask(lambda p: p.line([(20, 22), (28, 30)], 1.0)), EDGE, 0.7)
    c.put(c.mask(lambda p: p.line([(10, 44), (3, 52)], 1.0)), EDGE, 0.7)


PIECES: Dict[str, Piece] = {
    "rift_tear": Piece((0, ROOF, 360, FLOOR), tear),
    "rift_outlines": Piece((760, 220, 1700, FLOOR), outlines),
    "gallery_exhibits": Piece((500, 200, 1740, FLOOR), exhibits),
    "falls_cascade": Piece((540, ROOF, 760, FALLS_FLOOR), cascade),
    "heart_black_star": Piece((420, ROOF, 980, FLOOR), black_star),
    "nursery_cradles": Piece((60, ROOF, 580, FLOOR), cradles),
    "rift_pool": Piece((POOL[0] - 4, FLOOR, POOL[1] + 4, FLOOR + 64), pool),
    "rift_shard": Piece((0, 0, 60, 16), shard),
    "void_crack_wall": Piece((0, 0, 32, 96), crack_wall),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
