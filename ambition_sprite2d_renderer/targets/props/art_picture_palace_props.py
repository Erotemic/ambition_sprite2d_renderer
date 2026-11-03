"""The props of the Picture Palace, the film studio of the Art dimension.

They are drawn in the cel style of the dimension's cast
(`targets/characters/_art_cast_kit.py`), in the colours of the studio: film
black, studio grey, tungsten-light yellow and the red of a recording light
(`targets/characters/_picture_palace_kit.py`).

- ``art_film_camera``: scenery. A big studio film camera on a tripod, with a
  magazine of two reels on top, a lens with a hood, and a red light.
- ``art_directors_chair``: scenery. A folding director's chair: a wooden
  X frame, a canvas seat and a canvas back with a gold star on it.
- ``art_studio_light``: scenery. A big tungsten lamp on a stand, with four
  barn doors round its lens. Its lens glows.
- ``art_monolith``: scenery. A perfect black slab, taller than a person,
  with a soft glint on its edge.
- ``art_pod_bay_door``: a door (the look of a `LockWall` of 32 by 128
  world units, drawn at 3 to 1, as `art_colour_gate_*`). A white spaceship
  door with round corners, a seam, red stripes and a red light.
- ``art_memory_module``: scenery. A rack of glass memory blocks that glow:
  the thing you pull out of MAL-9000. One block stands out of the rack.
  Its ``idle`` row is a loop: the light moves from block to block.
- ``art_clapperboard``: scenery. A big clapperboard on an easel, its
  striped clapper a little open.

Each frame leaves a margin round the drawing: art that touches the edge of
its frame is cut. The game shows each prop at half its frame. No drop
shadows: the game draws them.
"""

from __future__ import annotations

import math
from typing import Dict, List, Tuple

from ..characters import _art_cast_kit as K
from ..characters import _picture_palace_kit as M
from .art_props import _publisher

STILL: List[Tuple[str, int, int]] = [("idle", 1, 1000)]
LOOP: List[Tuple[str, int, int]] = [("idle", 6, 140)]
SCENERY = ["prop", "scenery", "art", "film"]

CAMERA_FRAME = (192, 256)
CHAIR_FRAME = (128, 160)
LIGHT_FRAME = (128, 256)
MONOLITH_FRAME = (128, 384)
POD_DOOR_FRAME = (96, 384)
MEMORY_FRAME = (96, 128)
CLAPPER_FRAME = (128, 160)

METAL = (70, 74, 88, 255)
METAL_DARK = (44, 46, 56, 255)
METAL_LIGHT = (150, 156, 174, 255)
CANVAS = M.FILM_BLACK
HULL = (238, 238, 232, 255)
HULL_SHADE = (196, 198, 196, 255)
GLASS = (210, 236, 246, 255)
SLAB = (18, 18, 24, 255)
CHALK = (240, 240, 232, 255)


def _tripod(f: K.Frame, head: Tuple[float, float], spread: float, foot: float, colour, near_colour) -> None:
    """Three legs from `head` to the floor at `foot`: the back leg first."""
    hx, hy = head
    M.rod(f, [(hx + 2.0, hy), (hx + 6.0, foot - 4.0)], 4.0, K.shade(colour, 0.7))
    for side in (-1.0, 1.0):
        M.rod(f, [(hx, hy), (hx + side * spread, foot)], 5.0, near_colour)
        f.ellipse(hx + side * spread, foot - 1.0, 4.0, 2.4, METAL_DARK)
    # The spreader that holds the legs apart.
    y = hy + (foot - hy) * 0.62
    M.rod(f, [(hx - spread * 0.62, y), (hx + spread * 0.62, y)], 2.2, METAL)


# ---------------------------------------------------------------------------
# The film camera.
# ---------------------------------------------------------------------------


def _reel(f: K.Frame, cx: float, cy: float, r: float) -> None:
    M.disc(f, cx, cy, r, r, METAL)
    f.ellipse(cx, cy, r * 0.8, r * 0.8, METAL_DARK, body=False)
    for k in range(3):
        a = k * math.tau / 3.0 + 0.4
        f.ellipse(cx + math.cos(a) * r * 0.48, cy + math.sin(a) * r * 0.48, r * 0.2, r * 0.2, (88, 92, 108, 255), body=False)
    M.disc(f, cx, cy, r * 0.16, r * 0.16, METAL_LIGHT, edge=0.6, body=False)
    f.ink(K.ellipse_points(cx, cy, r * 0.92, r * 0.92, 28)[17:24], 1.4, K.alpha(METAL_LIGHT, 0.8))


def _draw_camera():
    w, h = CAMERA_FRAME
    f = K.Frame(CAMERA_FRAME)
    foot = h - 8.0
    _tripod(f, (92.0, 160.0), 56.0, foot, METAL, METAL)
    # The pan head and its handle, back to the left.
    M.rod(f, [(70.0, 156.0), (22.0, 186.0)], 4.0, METAL_DARK)
    M.rod(f, [(22.0, 186.0), (16.0, 190.0)], 6.0, (40, 40, 44, 255))
    M.plate(f, [(72.0, 148.0), (114.0, 148.0), (110.0, 162.0), (76.0, 162.0)], METAL_DARK)
    # The magazine on top: two reels and the film between them.
    _reel(f, 70.0, 64.0, 27.0)
    _reel(f, 122.0, 64.0, 27.0)
    f.ink([(70.0, 91.0), (96.0, 98.0), (122.0, 91.0)], 1.6, (60, 40, 30, 255))
    M.plate(f, [(76.0, 82.0), (116.0, 82.0), (112.0, 98.0), (80.0, 98.0)], METAL)
    # The body of the camera.
    body = [(42.0, 96.0), (146.0, 96.0), (150.0, 102.0), (150.0, 146.0), (46.0, 148.0), (40.0, 140.0)]
    M.plate(f, body, METAL)
    f.poly([(40.0, 128.0), (150.0, 126.0), (150.0, 146.0), (46.0, 148.0), (40.0, 140.0)], METAL_DARK, body=False)
    f.ink([(46.0, 100.0), (144.0, 100.0)], 1.4, METAL_LIGHT)
    f.poly([(62.0, 108.0), (104.0, 108.0), (104.0, 122.0), (62.0, 122.0)], METAL_DARK, body=False)
    for k in range(4):
        f.ink([(66.0 + k * 10.0, 110.0), (66.0 + k * 10.0, 120.0)], 1.0, METAL)
    # The red light on top of the body: it records.
    f.ellipse(132.0, 108.0, 4.4, 4.4, M.REC_RED, body=False)
    f.glow(132.0, 108.0, 8.0, K.alpha(M.REC_RED, 0.5))
    f.dot(131.0, 107.0, 1.2, M.REC_RED_HOT)
    # The eyepiece at the back.
    M.plate(f, [(26.0, 104.0), (42.0, 106.0), (42.0, 120.0), (26.0, 122.0)], (40, 40, 44, 255))
    f.ellipse(24.0, 113.0, 3.0, 8.0, (30, 30, 34, 255))
    # The lens, and its hood at the front.
    M.plate(f, [(150.0, 106.0), (168.0, 106.0), (168.0, 138.0), (150.0, 138.0)], (36, 36, 42, 255))
    for x in (155.0, 162.0):
        f.ink([(x, 107.0), (x, 137.0)], 1.0, METAL_LIGHT)
    hood = [(168.0, 104.0), (184.0, 96.0), (184.0, 148.0), (168.0, 140.0)]
    M.plate(f, hood, METAL_DARK)
    f.ellipse(178.0, 122.0, 3.5, 16.0, (100, 140, 180, 255), body=False)
    f.ink([(177.0, 112.0), (178.0, 118.0)], 1.2, K.alpha(K.WHITE, 0.8))
    return f.finish(width=1.6)


# ---------------------------------------------------------------------------
# The director's chair.
# ---------------------------------------------------------------------------


def _star(cx: float, cy: float, r: float):
    pts = []
    for k in range(10):
        a = -math.pi / 2.0 + k * math.pi / 5.0
        rr = r if k % 2 == 0 else r * 0.45
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    return pts


def _draw_chair():
    w, h = CHAIR_FRAME
    f = K.Frame(CHAIR_FRAME)
    foot = h - 9.0
    wood, wood_far = K.WOOD, K.shade(K.WOOD, 0.72)
    dx, dy = 22.0, -8.0
    # The far side: its X frame, its arm and its back post.
    for a, b in (((30.0, foot), (82.0, 94.0)), ((82.0, foot), (30.0, 94.0))):
        M.rod(f, [(a[0] + dx, a[1] + dy), (b[0] + dx, b[1] + dy)], 5.0, wood_far)
    M.rod(f, [(30.0 + dx, 94.0 + dy), (30.0 + dx, 22.0 + dy)], 5.0, wood_far)
    M.rod(f, [(26.0 + dx, 74.0 + dy), (90.0 + dx, 74.0 + dy)], 5.0, wood_far)
    M.rod(f, [(86.0 + dx, 74.0 + dy), (86.0 + dx, 94.0 + dy)], 4.0, wood_far)
    # The canvas back, between the two back posts, with its gold star.
    back = [(30.0, 24.0), (30.0 + dx, 24.0 + dy), (30.0 + dx, 50.0 + dy), (30.0, 50.0)]
    M.plate(f, back, CANVAS)
    f.poly(_star(30.0 + dx / 2.0, 37.0 + dy / 2.0, 7.0), M.TUNGSTEN, body=False)
    # The canvas seat.
    seat = [(30.0, 94.0), (82.0, 94.0), (82.0 + dx, 94.0 + dy), (30.0 + dx, 94.0 + dy)]
    M.plate(f, seat, (60, 60, 70, 255))
    f.poly([(30.0, 94.0), (82.0, 94.0), (82.0, 98.0), (30.0, 98.0)], CANVAS)
    # The near side: its X frame, its back post, its arm.
    for a, b in (((30.0, foot), (82.0, 94.0)), ((82.0, foot), (30.0, 94.0))):
        M.rod(f, [a, b], 6.0, wood)
    f.dot(56.0, (foot + 94.0) / 2.0, 2.2, K.GOLD)
    M.rod(f, [(30.0, 96.0), (30.0, 20.0)], 6.0, wood)
    M.rod(f, [(82.0, 96.0), (82.0, 74.0)], 5.0, wood)
    M.rod(f, [(24.0, 74.0), (92.0, 74.0)], 6.0, wood)
    f.ink([(28.0, 72.5), (90.0, 72.5)], 1.0, K.shade(K.WOOD, 1.25))
    return f.finish(width=1.6)


# ---------------------------------------------------------------------------
# The studio light.
# ---------------------------------------------------------------------------


def _draw_light():
    w, h = LIGHT_FRAME
    f = K.Frame(LIGHT_FRAME)
    foot = h - 8.0
    _tripod(f, (64.0, 190.0), 42.0, foot, METAL, METAL)
    M.rod(f, [(64.0, 192.0), (64.0, 120.0)], 6.0, METAL)
    M.rod(f, [(64.0, 160.0), (64.0, 150.0)], 9.0, METAL_DARK)
    # The yoke that holds the lamp.
    M.rod(f, [(28.0, 92.0), (28.0, 122.0), (100.0, 122.0), (100.0, 92.0)], 4.0, METAL_DARK)
    # The barn doors: four flaps that open out round the lens.
    cx, cy, r = 64.0, 82.0, 28.0
    M.plate(f, [(cx - 30.0, cy - 30.0), (cx + 30.0, cy - 30.0), (cx + 40.0, cy - 50.0), (cx - 40.0, cy - 50.0)], METAL_DARK)
    M.plate(f, [(cx - 30.0, cy + 30.0), (cx + 30.0, cy + 30.0), (cx + 38.0, cy + 44.0), (cx - 38.0, cy + 44.0)], METAL_DARK)
    for side in (-1.0, 1.0):
        M.plate(f, [(cx + side * 30.0, cy - 28.0), (cx + side * 30.0, cy + 28.0), (cx + side * 52.0, cy + 36.0), (cx + side * 52.0, cy - 36.0)],
                METAL if side > 0 else K.shade(METAL, 0.8))
    # The housing, with its cooling fins on top, and the lens.
    M.plate(f, [(cx - 30.0, cy - 30.0), (cx + 30.0, cy - 30.0), (cx + 30.0, cy + 30.0), (cx - 30.0, cy + 30.0)], METAL)
    for k in range(5):
        x = cx - 20.0 + k * 10.0
        f.ink([(x, cy - 46.0), (x, cy - 34.0)], 1.6, K.shade(METAL_DARK, 0.8))
    M.disc(f, cx, cy, r - 2.0, r - 2.0, METAL_DARK, body=False)
    f.ellipse(cx, cy, r - 5.0, r - 5.0, M.TUNGSTEN, body=False)
    for k in range(1, 4):
        f.ink(K.ellipse_points(cx, cy, (r - 5.0) * k / 4.0, (r - 5.0) * k / 4.0, 28) + [K.ellipse_points(cx, cy, (r - 5.0) * k / 4.0, (r - 5.0) * k / 4.0, 28)[0]],
              0.9, K.shade(M.TUNGSTEN, 0.8))
    f.ellipse(cx, cy, 6.0, 6.0, (255, 246, 214, 255), body=False)
    f.glow(cx, cy, r + 6.0, K.alpha(M.TUNGSTEN, 0.45))
    f.ink([(cx - 14.0, cy - 12.0), (cx - 8.0, cy - 17.0)], 1.6, K.alpha(K.WHITE, 0.9))
    return f.finish(width=1.6, glow_blur=3.0)


# ---------------------------------------------------------------------------
# The monolith.
# ---------------------------------------------------------------------------


def _draw_monolith():
    w, h = MONOLITH_FRAME
    f = K.Frame(MONOLITH_FRAME)
    top, foot = 20.0, h - 8.0
    x0, x1, depth = 18.0, 98.0, 12.0
    # The side face, in a little light; then the face, perfectly black.
    M.plate(f, [(x1, top), (x1 + depth, top - 4.0), (x1 + depth, foot - 4.0), (x1, foot)], (42, 42, 52, 255))
    M.plate(f, [(x0, top), (x1, top), (x1, foot), (x0, foot)], SLAB)
    f.poly([(x0, top), (x1, top), (x1 + depth, top - 4.0), (x0 + depth, top - 4.0)], (60, 60, 72, 255))
    # A soft sheen down the face, and the light on its edge.
    f.poly([(x0 + 10.0, top + 6.0), (x0 + 22.0, top + 6.0), (x0 + 16.0, foot - 6.0), (x0 + 6.0, foot - 6.0)], K.alpha((90, 96, 120, 255), 0.22), body=False)
    f.ink([(x1 - 0.6, top + 2.0), (x1 - 0.6, foot - 2.0)], 1.2, K.alpha((170, 176, 200, 255), 0.75))
    f.ink([(x0 + 2.0, top + 1.0), (x1 - 2.0, top + 1.0)], 1.0, K.alpha((170, 176, 200, 255), 0.6))
    # The glint: a small star of light at the top corner.
    gx, gy = x1 - 1.0, top + 1.0
    f.glow(gx, gy, 9.0, K.alpha(K.WHITE, 0.45))
    f.glow_line([(gx - 9.0, gy), (gx + 9.0, gy)], 1.2, K.alpha(K.WHITE, 0.9))
    f.glow_line([(gx, gy - 9.0), (gx, gy + 9.0)], 1.2, K.alpha(K.WHITE, 0.9))
    return f.finish(width=1.6, glow_blur=2.0)


# ---------------------------------------------------------------------------
# The pod bay door (a door).
# ---------------------------------------------------------------------------


def _draw_pod_door():
    w, h = POD_DOOR_FRAME
    f = K.Frame(POD_DOOR_FRAME)
    m = 7.0
    x0, x1, y0, y1 = m, w - m, m, h - m
    # The frame of the door: studio grey, with round corners.
    frame = K.ellipse_points(x0 + 14.0, y0 + 14.0, 14.0, 14.0, 32)[16:25] + K.ellipse_points(x1 - 14.0, y0 + 14.0, 14.0, 14.0, 32)[24:32] + \
        [(x1, y0 + 14.0), (x1, y1 - 14.0)] + K.ellipse_points(x1 - 14.0, y1 - 14.0, 14.0, 14.0, 32)[0:9] + \
        K.ellipse_points(x0 + 14.0, y1 - 14.0, 14.0, 14.0, 32)[8:17]
    M.plate(f, frame, M.STUDIO_GREY)
    # The door in it: white, round cornered, with a seam down its middle.
    ix0, ix1, iy0, iy1 = x0 + 8.0, x1 - 8.0, y0 + 30.0, y1 - 10.0
    r = 10.0
    door = K.ellipse_points(ix0 + r, iy0 + r, r, r, 32)[16:25] + K.ellipse_points(ix1 - r, iy0 + r, r, r, 32)[24:32] + \
        [(ix1, iy0 + r), (ix1, iy1 - r)] + K.ellipse_points(ix1 - r, iy1 - r, r, r, 32)[0:9] + K.ellipse_points(ix0 + r, iy1 - r, r, r, 32)[8:17]
    M.plate(f, door, HULL, body=False)
    f.poly([(ix1 - 12.0, iy0 + 4.0), (ix1 - 2.0, iy0 + 8.0), (ix1 - 2.0, iy1 - 8.0), (ix1 - 12.0, iy1 - 4.0)], HULL_SHADE, body=False)
    mid = (ix0 + ix1) / 2.0
    f.ink([(mid, iy0 + 2.0), (mid, iy1 - 2.0)], 1.6, (120, 122, 128, 255))
    # Panel lines and a row of rivets.
    for y in (iy0 + 60.0, iy0 + 150.0, iy0 + 240.0):
        f.ink([(ix0 + 4.0, y), (ix1 - 4.0, y)], 1.0, HULL_SHADE)
        for x in (ix0 + 8.0, mid - 8.0, mid + 8.0, ix1 - 8.0):
            f.dot(x, y + 5.0, 1.2, HULL_SHADE)
    # The red stripes across the foot of the door, and a band of them at the head.
    for yb, hb in ((iy1 - 46.0, 30.0), (iy0 + 18.0, 14.0)):
        f.poly([(ix0 + 1.0, yb), (ix1 - 1.0, yb), (ix1 - 1.0, yb + hb), (ix0 + 1.0, yb + hb)], (230, 228, 220, 255), body=False)
        lo, hi = ix0 + 1.0, ix1 - 1.0
        for k in range(-2, 9):
            sx = ix0 + k * 12.0
            q = [(sx, yb), (sx + 6.0, yb), (sx + 6.0 - hb * 0.6, yb + hb), (sx - hb * 0.6, yb + hb)]
            q = [(min(hi, max(lo, x)), y) for x, y in q]
            if k % 2 == 0:
                f.poly(q, M.REC_RED, body=False)
        f.ink([(ix0 + 1.0, yb), (ix1 - 1.0, yb)], 0.8, (120, 122, 128, 255))
        f.ink([(ix0 + 1.0, yb + hb), (ix1 - 1.0, yb + hb)], 0.8, (120, 122, 128, 255))
    # The red light over the door, lit: the door is shut.
    lx, ly = w / 2.0, y0 + 16.0
    M.disc(f, lx, ly, 8.0, 8.0, METAL_DARK, body=False)
    f.ellipse(lx, ly, 5.6, 5.6, M.REC_RED, body=False)
    f.dot(lx - 1.4, ly - 1.4, 1.6, M.REC_RED_HOT)
    f.glow(lx, ly, 13.0, K.alpha(M.REC_RED, 0.55))
    # A round window high in the door.
    wy = iy0 + 100.0
    M.disc(f, mid, wy, 16.0, 16.0, M.STUDIO_GREY, body=False)
    f.ellipse(mid, wy, 12.0, 12.0, (24, 30, 46, 255), body=False)
    for sx, sy in ((mid - 5.0, wy - 4.0), (mid + 4.0, wy + 3.0), (mid + 1.0, wy - 7.0)):
        f.dot(sx, sy, 0.8, K.WHITE)
    f.ink([(mid - 8.0, wy - 3.0), (mid - 4.0, wy - 8.0)], 1.2, K.alpha(K.WHITE, 0.7))
    return f.finish(width=1.6, glow_blur=2.0)


# ---------------------------------------------------------------------------
# The memory module.
# ---------------------------------------------------------------------------


def _draw_memory(anim: str, i: int, n: int):
    w, h = MEMORY_FRAME
    f = K.Frame(MEMORY_FRAME)
    x0, x1, y0, y1 = 10.0, w - 10.0, 10.0, h - 8.0
    M.plate(f, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], METAL)
    f.poly([(x1 - 8.0, y0 + 2.0), (x1, y0), (x1, y1), (x1 - 8.0, y1 - 2.0)], METAL_DARK, body=False)
    f.poly([(x0 + 5.0, y0 + 6.0), (x1 - 5.0, y0 + 6.0), (x1 - 5.0, y1 - 14.0), (x0 + 5.0, y1 - 14.0)], (24, 24, 32, 255), body=False)
    # The feet of the rack.
    for x in (x0 + 6.0, x1 - 6.0):
        f.poly([(x - 5.0, y1 - 2.0), (x + 5.0, y1 - 2.0), (x + 5.0, y1 + 3.0), (x - 5.0, y1 + 3.0)], METAL_DARK)
    # The blocks of glass, two columns of five: a light moves along them.
    lit = i % n
    for row in range(5):
        for col in range(2):
            k = row * 2 + col
            out = 6.0 if (row, col) == (2, 1) else 0.0
            bx0 = x0 + 9.0 + col * 32.0 - out
            by0 = y0 + 10.0 + row * 18.0
            block = [(bx0, by0), (bx0 + 26.0, by0), (bx0 + 26.0, by0 + 12.0), (bx0, by0 + 12.0)]
            on = 0.45 + 0.55 * (1.0 if (k + lit * 2) % 6 < 2 else 0.0)
            glow_col = M.REC_RED if (row, col) == (2, 1) else M.TUNGSTEN
            M.plate(f, block, GLASS, edge=0.7, body=bool(out))
            f.poly([(bx0 + 2.0, by0 + 3.0), (bx0 + 24.0, by0 + 3.0), (bx0 + 24.0, by0 + 9.0), (bx0 + 2.0, by0 + 9.0)], K.alpha(glow_col, 0.55 * on),
                   body=False)
            f.ink([(bx0 + 3.0, by0 + 2.0), (bx0 + 12.0, by0 + 2.0)], 0.9, K.alpha(K.WHITE, 0.9))
            f.glow(bx0 + 13.0, by0 + 6.0, 7.0, K.alpha(glow_col, 0.3 * on))
    # The handle on the block that stands out: the one to pull.
    hx, hy = x0 + 9.0 + 32.0 - 6.0 + 26.0, y0 + 10.0 + 2 * 18.0 + 6.0
    M.rod(f, [(hx, hy - 4.0), (hx + 4.0, hy - 4.0), (hx + 4.0, hy + 4.0), (hx, hy + 4.0)], 1.6, METAL_LIGHT, edge=0.6)
    return f.finish(width=1.4, glow_blur=2.0)


# ---------------------------------------------------------------------------
# The clapperboard.
# ---------------------------------------------------------------------------


def _draw_clapper():
    w, h = CLAPPER_FRAME
    f = K.Frame(CLAPPER_FRAME)
    foot = h - 9.0
    # The easel: two front legs and one behind.
    M.rod(f, [(64.0, 20.0), (80.0, foot - 2.0)], 4.0, K.WOOD_DARK)
    M.rod(f, [(60.0, 20.0), (26.0, foot)], 5.0, K.WOOD)
    M.rod(f, [(68.0, 20.0), (102.0, foot)], 5.0, K.WOOD)
    M.rod(f, [(30.0, 122.0), (98.0, 122.0)], 5.0, K.WOOD)
    # The slate.
    x0, x1, y0, y1 = 16.0, 112.0, 50.0, 116.0
    M.plate(f, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], CANVAS)
    f.poly([(x0, y0), (x1, y0), (x1, y0 + 12.0), (x0, y0 + 12.0)], CANVAS, body=False)
    for (a, b) in (((x0 + 4.0, y0 + 26.0), (x1 - 4.0, y0 + 26.0)), ((x0 + 4.0, y0 + 46.0), (x1 - 4.0, y0 + 46.0)),
                   ((x0 + 48.0, y0 + 26.0), (x0 + 48.0, y1 - 4.0))):
        f.ink([a, b], 1.2, CHALK)
    # Chalk on the slate: the scene, the take, and a scribble of a name.
    f.ink([(x0 + 8.0, y0 + 18.0), (x0 + 14.0, y0 + 14.0), (x0 + 22.0, y0 + 19.0), (x0 + 30.0, y0 + 14.0), (x0 + 40.0, y0 + 18.0),
           (x0 + 52.0, y0 + 15.0), (x0 + 66.0, y0 + 18.0)], 1.2, CHALK)
    f.ink([(x0 + 14.0, y0 + 32.0), (x0 + 22.0, y0 + 30.0), (x0 + 18.0, y0 + 40.0)], 1.6, CHALK)
    f.ink([(x0 + 60.0, y0 + 31.0), (x0 + 60.0, y0 + 41.0)], 1.6, CHALK)
    f.ink([(x0 + 66.0, y0 + 31.0), (x0 + 72.0, y0 + 41.0), (x0 + 78.0, y0 + 31.0)], 1.6, CHALK)
    f.ink([(x0 + 12.0, y0 + 56.0), (x0 + 30.0, y0 + 54.0), (x0 + 40.0, y0 + 58.0)], 1.2, CHALK)
    f.ink([(x0 + 58.0, y0 + 57.0), (x0 + 84.0, y0 + 55.0)], 1.2, CHALK)
    # The fixed striped bar, and the clapper over it, a little open.
    def stripes(bar_x0, bar_y0, length, height, angle):
        pts = [(bar_x0, bar_y0), (bar_x0 + length, bar_y0), (bar_x0 + length, bar_y0 + height), (bar_x0, bar_y0 + height)]
        M.plate(f, K.turn(pts, bar_x0, bar_y0 + height, angle), K.WHITE)
        for k in range(6):
            sx = bar_x0 + 4.0 + k * 16.0
            q = [(sx, bar_y0), (sx + 8.0, bar_y0), (sx + 2.0, bar_y0 + height), (sx - 6.0, bar_y0 + height)]
            q = [(max(bar_x0, min(bar_x0 + length, x)), y) for x, y in q]
            f.poly(K.turn(q, bar_x0, bar_y0 + height, angle), CANVAS, body=False)
    stripes(x0, y0 - 10.0, x1 - x0, 10.0, 0.0)
    stripes(x0, y0 - 21.0, x1 - x0, 10.0, -11.0)
    f.ellipse(x0 + 2.0, y0 - 11.0, 3.0, 3.0, METAL_LIGHT)
    return f.finish(width=1.6)


DRAW = {
    "art_film_camera": lambda anim, i, n: _draw_camera(),
    "art_directors_chair": lambda anim, i, n: _draw_chair(),
    "art_studio_light": lambda anim, i, n: _draw_light(),
    "art_monolith": lambda anim, i, n: _draw_monolith(),
    "art_pod_bay_door": lambda anim, i, n: _draw_pod_door(),
    "art_memory_module": _draw_memory,
    "art_clapperboard": lambda anim, i, n: _draw_clapper(),
}
FRAMES = {
    "art_film_camera": CAMERA_FRAME, "art_directors_chair": CHAIR_FRAME, "art_studio_light": LIGHT_FRAME, "art_monolith": MONOLITH_FRAME,
    "art_pod_bay_door": POD_DOOR_FRAME, "art_memory_module": MEMORY_FRAME, "art_clapperboard": CLAPPER_FRAME,
}

TARGETS: Dict[str, dict] = {
    "art_film_camera": _publisher("art_film_camera", "Film Camera", STILL, CAMERA_FRAME, DRAW["art_film_camera"], {"foot": (92.0, 256.0)}, "Scenery",
                                  SCENERY),
    "art_directors_chair": _publisher("art_directors_chair", "Director's Chair", STILL, CHAIR_FRAME, DRAW["art_directors_chair"],
                                      {"foot": (64.0, 160.0)}, "Scenery", SCENERY),
    "art_studio_light": _publisher("art_studio_light", "Studio Light", STILL, LIGHT_FRAME, DRAW["art_studio_light"], {"foot": (64.0, 256.0)},
                                   "Scenery", SCENERY),
    "art_monolith": _publisher("art_monolith", "Monolith", STILL, MONOLITH_FRAME, DRAW["art_monolith"], {"foot": (64.0, 384.0)}, "Scenery", SCENERY),
    "art_pod_bay_door": _publisher("art_pod_bay_door", "Pod Bay Door", STILL, POD_DOOR_FRAME, DRAW["art_pod_bay_door"], {"foot": (48.0, 384.0)},
                                   "Door", ["prop", "door", "lock", "art", "film"], forward=(0.0, -1.0)),
    "art_memory_module": _publisher("art_memory_module", "Memory Module", LOOP, MEMORY_FRAME, DRAW["art_memory_module"], {"foot": (48.0, 128.0)},
                                    "Scenery", SCENERY),
    "art_clapperboard": _publisher("art_clapperboard", "Clapperboard", STILL, CLAPPER_FRAME, DRAW["art_clapperboard"], {"foot": (64.0, 160.0)},
                                   "Scenery", SCENERY),
}
