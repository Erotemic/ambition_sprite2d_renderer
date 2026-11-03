"""The props of the Story Stacks, the fiction quarter of the Art dimension.

The scenery of a land of giant books, and the two doors of the Library of
Endings, drawn in the cel style of the dimension's cast
(`targets/characters/_art_cast_kit.py`) with the accent of the quarter:
parchment, leather browns, ink black and gold leaf.

- ``art_book_tower``: scenery (a `Prop`). A teetering stack of giant books,
  some with the spine to you and some with the page edges, and a candle
  stub on the top book.
- ``art_lectern``: scenery. A wooden lectern with an open book on it. The
  pages glow, and letters rise off them (``idle``: six frames).
- ``art_quill_lamp``: scenery. A street lamp: its post is a quill pen that
  stands in a pot of ink, and the tip of the feather curls over to hold a
  lantern (``idle``: six frames, the flame moves).
- ``art_ending_door_happy`` and ``art_ending_door_sad``: doors (the look of
  a `LockWall` of 48 by 192 world units, the shape of
  ``art_colour_gate_*``). Each is the cover of a book: the happy ending in
  gold leather with a sun, the sad ending in deep blue with a crescent moon
  and rain. The Author's choice opens one of them.

World size is the frame size divided by two. No drop shadows: the game
draws them. Nothing touches the edge of its frame.
"""

from __future__ import annotations

import math
import random
from typing import Dict, List, Tuple

from ..characters import _art_cast_kit as K
from .art_props import _publisher

Point = Tuple[float, float]

PARCHMENT: K.RGBA = (240, 226, 190, 255)
PARCHMENT_SHADE: K.RGBA = (204, 186, 146, 255)
LEATHER: K.RGBA = (128, 74, 42, 255)
LEATHER_DARK: K.RGBA = (84, 46, 26, 255)
OXBLOOD: K.RGBA = (138, 34, 40, 255)
BOTTLE: K.RGBA = (46, 104, 70, 255)
NAVY: K.RGBA = (40, 58, 120, 255)
INK_BLACK: K.RGBA = (28, 24, 38, 255)
FLAME: K.RGBA = (255, 190, 70, 255)

STILL: List[Tuple[str, int, int]] = [("idle", 1, 1000)]
GLOW_ROWS: List[Tuple[str, int, int]] = [("idle", 6, 140)]

TOWER_FRAME = (192, 384)
LECTERN_FRAME = (128, 176)
LAMP_FRAME = (96, 384)
DOOR_FRAME = (96, 384)


def _rect(cx: float, cy: float, w: float, h: float, tilt: float = 0.0) -> List[Point]:
    pts = [(cx - w / 2.0, cy - h / 2.0), (cx + w / 2.0, cy - h / 2.0), (cx + w / 2.0, cy + h / 2.0), (cx - w / 2.0, cy + h / 2.0)]
    return K.turn(pts, cx, cy, tilt)


# ---------------------------------------------------------------------------
# The book tower.
# ---------------------------------------------------------------------------

#: The books from the bottom up: width, thickness, colour, the shift of its
#: middle from the middle of the frame, its tilt, and what faces you (the
#: spine, or the edges of the pages).
BOOKS = [
    (172.0, 40.0, LEATHER, 0.0, 0.0, "spine"),
    (150.0, 30.0, OXBLOOD, -6.0, -2.0, "pages"),
    (160.0, 36.0, NAVY, 2.0, 1.5, "spine"),
    (136.0, 26.0, BOTTLE, 10.0, 3.0, "pages"),
    (140.0, 34.0, LEATHER_DARK, 4.0, -2.0, "spine"),
    (126.0, 30.0, OXBLOOD, -8.0, -4.0, "spine"),
    (134.0, 26.0, LEATHER, 6.0, 3.0, "pages"),
    (118.0, 32.0, BOTTLE, 16.0, 5.0, "spine"),
    (124.0, 24.0, NAVY, 24.0, 3.0, "pages"),
]


def _book(f: K.Frame, cx: float, cy: float, w: float, h: float, colour: K.RGBA, tilt: float, face: str, rng: random.Random) -> None:
    """A closed book that lies flat, seen from its side."""
    f.poly(_rect(cx, cy, w, h, tilt), colour)
    if face == "pages":
        # The edges of the pages between the two boards of the cover.
        f.poly(_rect(cx - 3.0, cy, w - 10.0, h - 8.0, tilt), PARCHMENT, body=False)
        for k in range(1, 4):
            y = cy - (h - 8.0) / 2.0 + (h - 8.0) * k / 4.0
            f.ink(K.turn([(cx - w / 2.0 + 4.0, y), (cx + w / 2.0 - 10.0, y)], cx, cy, tilt), 0.7, PARCHMENT_SHADE)
        # A ribbon of a bookmark that hangs out.
        rx = cx + rng.uniform(-w * 0.3, w * 0.2)
        f.poly(K.turn([(rx, cy + h / 2.0 - 2.0), (rx + 5.0, cy + h / 2.0 - 2.0), (rx + 5.0, cy + h / 2.0 + 9.0), (rx + 2.5, cy + h / 2.0 + 6.0),
                       (rx, cy + h / 2.0 + 9.0)], cx, cy, tilt), K.MAGENTA, body=False)
        return
    # The spine: a shade at its foot, bands of gold leaf, and a label.
    f.poly(_rect(cx, cy + h * 0.3, w, h * 0.4, tilt), K.shade(colour, 0.78), body=False)
    for bx in (cx - w / 2.0 + 12.0, cx + w / 2.0 - 12.0):
        f.poly(_rect(bx, cy, 4.0, h - 4.0, tilt), K.GOLD, body=False)
    f.poly(_rect(cx, cy, w * 0.42, h * 0.46, tilt), K.GOLD, body=False)
    f.poly(_rect(cx, cy, w * 0.42 - 4.0, h * 0.46 - 4.0, tilt), K.shade(colour, 0.7), body=False)
    # The title: a line of gold letters.
    for k in range(int(w * 0.042)):
        x = cx - w * 0.17 + k * 5.0
        f.ink(K.turn([(x, cy - 1.5), (x + 3.0, cy - 1.5)], cx, cy, tilt), 1.4, K.GOLD)


def _draw_tower():
    w, h = TOWER_FRAME
    f = K.Frame(TOWER_FRAME)
    rng = random.Random("book_tower")
    y = h - 4.0
    top = (w / 2.0, y)
    for width, thick, colour, shift, tilt, face in BOOKS:
        cy = y - thick / 2.0
        _book(f, w / 2.0 + shift, cy, width, thick, colour, tilt, face, rng)
        y -= thick - 1.0
        top = (w / 2.0 + shift, y)
    # A stub of a candle on the top book, with wax run down it.
    cx = top[0] - 30.0
    f.poly([(cx - 7.0, top[1] + 1.0), (cx + 7.0, top[1] + 1.0), (cx + 7.0, top[1] - 22.0), (cx - 7.0, top[1] - 22.0)], PARCHMENT)
    f.ellipse(cx, top[1] - 22.0, 7.0, 2.4, K.WHITE, body=False)
    f.limb([(cx - 3.0, top[1] - 22.0), (cx - 3.0, top[1] - 12.0)], 2.6, K.WHITE, body=False)
    f.ink([(cx, top[1] - 23.0), (cx, top[1] - 27.0)], 1.0, K.INK)
    f.poly([(cx - 3.0, top[1] - 28.0), (cx, top[1] - 40.0), (cx + 3.0, top[1] - 28.0), (cx, top[1] - 25.0)], FLAME, body=False)
    f.glow(cx, top[1] - 31.0, 9.0, K.alpha(FLAME, 0.45))
    # An ink pot and a quill beside the candle.
    px = top[0] + 34.0
    f.ellipse(px, top[1] - 9.0, 11.0, 9.0, INK_BLACK)
    f.poly([(px - 5.0, top[1] - 16.0), (px + 5.0, top[1] - 16.0), (px + 5.0, top[1] - 21.0), (px - 5.0, top[1] - 21.0)], INK_BLACK)
    f.ellipse(px - 4.0, top[1] - 12.0, 2.4, 2.0, K.alpha(K.WHITE, 0.6), body=False)
    f.limb([(px + 1.0, top[1] - 20.0), (px + 14.0, top[1] - 52.0)], 1.8, PARCHMENT_SHADE)
    vane = [(px + 5.0, top[1] - 30.0), (px + 6.0, top[1] - 44.0), (px + 15.0, top[1] - 56.0), (px + 16.0, top[1] - 44.0), (px + 10.0, top[1] - 32.0)]
    f.poly(vane, K.WHITE)
    return f.finish(width=1.6, glow_blur=2.0)


# ---------------------------------------------------------------------------
# The lectern.
# ---------------------------------------------------------------------------


def _draw_lectern(i: int, n: int):
    w, h = LECTERN_FRAME
    t = i / float(n)
    f = K.Frame(LECTERN_FRAME)
    foot = h - 5.0
    # The foot, the post and the desk.
    f.poly([(30.0, foot), (98.0, foot), (90.0, foot - 10.0), (38.0, foot - 10.0)], K.WOOD_DARK)
    f.poly([(54.0, foot - 10.0), (74.0, foot - 10.0), (70.0, 98.0), (58.0, 98.0)], K.WOOD)
    f.poly([(66.0, foot - 10.0), (74.0, foot - 10.0), (70.0, 98.0), (66.0, 98.0)], K.WOOD_DARK, body=False)
    for y in (foot - 22.0, 112.0):
        f.limb([(56.0, y), (72.0, y)], 2.4, K.WOOD_DARK, body=False)
    desk = [(16.0, 100.0), (112.0, 78.0), (114.0, 88.0), (20.0, 110.0)]
    f.poly(desk, K.WOOD)
    f.poly([(20.0, 110.0), (114.0, 88.0), (113.0, 84.0), (19.0, 106.0)], K.WOOD_DARK, body=False)
    # The open book on the desk: two pages that curve up from the gutter.
    gx, gy = 64.0, 88.0
    left = [(gx, gy + 1.0), (24.0, gy + 10.0), (22.0, gy - 2.0), (40.0, gy - 12.0), (gx, gy - 8.0)]
    right = [(gx, gy + 1.0), (gx, gy - 8.0), (86.0, gy - 22.0), (106.0, gy - 22.0), (104.0, gy - 10.0)]
    f.poly(K.grow(left, 0.0), PARCHMENT)
    f.poly(right, PARCHMENT)
    f.poly([(gx, gy + 1.0), (gx - 8.0, gy - 1.0), (gx, gy - 8.0)], PARCHMENT_SHADE, body=False)
    for k in range(4):
        u = 0.25 + k * 0.16
        f.ink([(30.0 + 2.0 * k, gy + 4.0 - 10.0 * u - k * 2.0), (56.0, gy - 2.0 - k * 2.6)], 0.8, K.alpha(K.INK, 0.55))
        f.ink([(68.0, gy - 6.0 - k * 2.6), (98.0 - k * 2.0, gy - 12.0 - k * 2.6)], 0.8, K.alpha(K.INK, 0.55))
    # The ribbon of a bookmark that hangs over the front of the desk.
    f.poly([(60.0, gy), (65.0, gy), (63.0, gy + 34.0), (60.5, gy + 30.0), (58.0, gy + 34.0)], K.MAGENTA, body=False)
    # The glow of the pages, and letters that rise off them.
    pulse = 0.75 + 0.25 * math.sin(math.tau * t)
    f.glow(gx + 2.0, gy - 10.0, 16.0, K.alpha(K.GOLD, 0.28 * pulse))
    f.glow_poly(right, K.alpha(K.YELLOW, 0.18 * pulse))
    f.glow_poly(left, K.alpha(K.YELLOW, 0.18 * pulse))
    rng = random.Random("lectern_letters")
    for k in range(5):
        x0, phase0 = rng.uniform(34.0, 96.0), rng.uniform(0.0, 1.0)
        u = (t + phase0) % 1.0
        x, y = x0 + 6.0 * math.sin(math.tau * u + k), gy - 18.0 - 52.0 * u
        a = math.sin(math.pi * u)
        _letter(f, x, y, "ABEOS"[k], 7.0, K.alpha(K.GOLD, a))
    return f.finish(width=1.6, glow_blur=2.6)


#: Small strokes of a few letters, in a box one unit high.
LETTER_STROKES: Dict[str, List[List[Point]]] = {
    "A": [[(0.0, 1.0), (0.35, 0.0), (0.7, 1.0)], [(0.15, 0.6), (0.55, 0.6)]],
    "B": [[(0.0, 1.0), (0.0, 0.0), (0.5, 0.05), (0.55, 0.3), (0.0, 0.48), (0.6, 0.65), (0.55, 0.95), (0.0, 1.0)]],
    "E": [[(0.6, 0.0), (0.0, 0.0), (0.0, 1.0), (0.6, 1.0)], [(0.0, 0.5), (0.45, 0.5)]],
    "O": [[(0.3, 0.0), (0.6, 0.25), (0.6, 0.75), (0.3, 1.0), (0.0, 0.75), (0.0, 0.25), (0.3, 0.0)]],
    "S": [[(0.6, 0.1), (0.3, 0.0), (0.0, 0.2), (0.6, 0.75), (0.3, 1.0), (0.0, 0.9)]],
}


def _letter(f: K.Frame, x: float, y: float, ch: str, size: float, colour: K.RGBA) -> None:
    for stroke in LETTER_STROKES[ch]:
        f.glow_line([(x + px * size, y + py * size) for px, py in stroke], 1.4, colour)


# ---------------------------------------------------------------------------
# The quill lamp.
# ---------------------------------------------------------------------------


def _draw_lamp(i: int, n: int):
    w, h = LAMP_FRAME
    t = i / float(n)
    f = K.Frame(LAMP_FRAME)
    foot = h - 5.0
    cx = 40.0
    # The pot of ink it stands in: a squat bottle with a gold label.
    f.poly([(cx - 26.0, foot), (cx + 26.0, foot), (cx + 30.0, foot - 22.0), (cx + 20.0, foot - 38.0), (cx - 20.0, foot - 38.0),
            (cx - 30.0, foot - 22.0)], INK_BLACK)
    f.poly([(cx - 10.0, foot - 38.0), (cx + 10.0, foot - 38.0), (cx + 10.0, foot - 46.0), (cx - 10.0, foot - 46.0)], INK_BLACK)
    f.ellipse(cx, foot - 46.0, 11.0, 3.0, K.shade(INK_BLACK, 1.4), body=False)
    f.poly([(cx - 18.0, foot - 24.0), (cx + 18.0, foot - 24.0), (cx + 18.0, foot - 12.0), (cx - 18.0, foot - 12.0)], K.GOLD, body=False)
    f.ink([(cx - 12.0, foot - 18.0), (cx + 12.0, foot - 18.0)], 1.0, K.GOLD_DARK)
    f.ink([(cx - 22.0, foot - 30.0), (cx - 18.0, foot - 36.0)], 1.6, K.alpha(K.WHITE, 0.6))
    # The shaft of the quill: up out of the pot, a little bent.
    shaft = [(cx, foot - 46.0), (cx + 1.0, 250.0), (cx - 1.0, 150.0), (cx + 2.0, 70.0)]
    f.limb(shaft, 6.0, PARCHMENT_SHADE)
    f.ink([(cx - 1.0, foot - 48.0), (cx, 250.0), (cx - 2.0, 150.0), (cx + 1.0, 72.0)], 1.0, K.alpha(K.WHITE, 0.8))
    # The feather: a long vane each side of the shaft, the barbs inked.
    vane_l = [(cx, 250.0), (cx - 13.0, 220.0), (cx - 18.0, 160.0), (cx - 15.0, 100.0), (cx - 6.0, 66.0), (cx + 1.0, 64.0)]
    vane_r = [(cx + 1.0, 64.0), (cx + 10.0, 80.0), (cx + 14.0, 140.0), (cx + 11.0, 200.0), (cx + 3.0, 236.0)]
    f.poly(vane_l + list(reversed([(cx + 1.0, p[1]) for p in vane_l])), K.WHITE)
    f.poly(vane_r + list(reversed([(cx + 1.0, p[1]) for p in vane_r])), (236, 232, 222, 255))
    for k in range(9):
        y = 230.0 - k * 18.0
        f.ink([(cx - 1.0, y), (cx - 12.0, y - 10.0)], 0.7, PARCHMENT_SHADE)
        if y < 220.0:
            f.ink([(cx + 2.0, y), (cx + 10.0, y - 8.0)], 0.7, PARCHMENT_SHADE)
    # The tip curls over into a hook, and the lantern hangs from it.
    hook = [(cx + 2.0, 70.0), (cx + 6.0, 40.0), (cx + 22.0, 26.0), (cx + 36.0, 30.0), (cx + 40.0, 44.0)]
    f.limb(hook, 4.0, PARCHMENT_SHADE)
    f.limb([(cx + 6.0, 54.0), (cx + 10.0, 36.0), (cx + 22.0, 30.0)], 6.0, K.WHITE)
    lx, ly = cx + 40.0, 58.0
    f.ink([(lx, 44.0), (lx, ly - 12.0)], 1.4, K.INK)
    # The lantern: a gold cap, glass, a flame, and a gold foot.
    f.poly([(lx - 10.0, ly - 10.0), (lx + 10.0, ly - 10.0), (lx, ly - 18.0)], K.GOLD)
    f.poly([(lx - 9.0, ly - 10.0), (lx + 9.0, ly - 10.0), (lx + 7.0, ly + 14.0), (lx - 7.0, ly + 14.0)], (255, 236, 170, 255))
    f.ink([(lx - 9.0, ly - 10.0), (lx - 7.0, ly + 14.0)], 1.4, K.GOLD_DARK)
    f.ink([(lx + 9.0, ly - 10.0), (lx + 7.0, ly + 14.0)], 1.4, K.GOLD_DARK)
    f.ink([(lx, ly - 10.0), (lx, ly + 14.0)], 1.0, K.alpha(K.GOLD_DARK, 0.7))
    f.poly([(lx - 9.0, ly + 14.0), (lx + 9.0, ly + 14.0), (lx + 6.0, ly + 19.0), (lx - 6.0, ly + 19.0)], K.GOLD)
    flick = math.sin(math.tau * t) * 1.2 + math.sin(math.tau * t * 2.0 + 1.0) * 0.6
    f.poly([(lx - 3.0, ly + 9.0), (lx + flick, ly - 3.0 - abs(flick)), (lx + 3.0, ly + 9.0), (lx, ly + 11.0)], FLAME, body=False)
    f.glow(lx, ly + 2.0, 11.0 + 1.5 * math.sin(math.tau * t), K.alpha(FLAME, 0.55))
    # A drop of ink on the nib end, at the mouth of the pot.
    f.ellipse(cx + 8.0, foot - 44.0, 2.0, 2.6, INK_BLACK)
    return f.finish(width=1.6, glow_blur=2.2)


# ---------------------------------------------------------------------------
# The doors of the Library of Endings: two covers of a book.
# ---------------------------------------------------------------------------

#: Each ending: the leather, its dark, its trim, its light.
ENDINGS = {
    "happy": ((222, 168, 58, 255), (166, 112, 30, 255), (255, 232, 140, 255), (255, 214, 70, 255)),
    "sad": ((34, 50, 112, 255), (20, 28, 70, 255), (176, 196, 228, 255), (150, 200, 255, 255)),
}


def _sun(f: K.Frame, cx: float, cy: float, trim: K.RGBA, light: K.RGBA) -> None:
    for k in range(12):
        a = math.tau * k / 12.0
        r0, r1 = 16.0, 26.0 if k % 2 == 0 else 22.0
        tip = (cx + math.cos(a) * r1, cy + math.sin(a) * r1)
        side = (-math.sin(a) * 3.2, math.cos(a) * 3.2)
        base = (cx + math.cos(a) * r0, cy + math.sin(a) * r0)
        f.poly([(base[0] + side[0], base[1] + side[1]), tip, (base[0] - side[0], base[1] - side[1])], trim, body=False)
    f.ellipse(cx, cy, 14.0, 14.0, light, body=False)
    # A face on the sun: two eyes shut in a smile, and a smile.
    for ox in (-5.0, 5.0):
        f.ink([(cx + ox - 2.6, cy - 2.0), (cx + ox, cy - 4.0), (cx + ox + 2.6, cy - 2.0)], 1.2, (150, 96, 20, 255))
    f.ink([(cx - 6.0, cy + 3.0), (cx, cy + 7.0), (cx + 6.0, cy + 3.0)], 1.4, (150, 96, 20, 255))
    f.glow(cx, cy, 20.0, K.alpha(light, 0.45))


def _moon(f: K.Frame, cx: float, cy: float, leather: K.RGBA, trim: K.RGBA, light: K.RGBA) -> None:
    f.ellipse(cx, cy, 16.0, 16.0, trim, body=False)
    f.ellipse(cx + 8.0, cy - 5.0, 14.0, 14.0, leather, body=False)
    # A shut eye on the moon, and a tear.
    f.ink([(cx - 10.0, cy - 2.0), (cx - 7.0, cy), (cx - 4.0, cy - 1.0)], 1.2, (70, 84, 130, 255))
    f.ellipse(cx - 6.0, cy + 5.0, 1.6, 2.4, light, body=False)
    f.glow(cx - 4.0, cy, 18.0, K.alpha(light, 0.35))
    # Stars round it.
    for sx, sy in ((cx + 18.0, cy - 16.0), (cx - 20.0, cy - 18.0), (cx + 22.0, cy + 10.0)):
        f.ink([(sx - 2.4, sy), (sx + 2.4, sy)], 1.0, trim)
        f.ink([(sx, sy - 2.4), (sx, sy + 2.4)], 1.0, trim)


def _draw_door(ending: str):
    leather, dark, trim, light = ENDINGS[ending]
    w, h = DOOR_FRAME
    f = K.Frame(DOOR_FRAME)
    top, foot = 3.0, h - 3.0
    # The edges of the pages, at the right of the cover, and the cover.
    f.poly([(w - 14.0, top + 8.0), (w - 5.0, top + 8.0), (w - 5.0, foot - 8.0), (w - 14.0, foot - 8.0)], PARCHMENT)
    for x in (w - 11.0, w - 8.0):
        f.ink([(x, top + 10.0), (x, foot - 10.0)], 0.6, PARCHMENT_SHADE)
    f.poly([(5.0, top), (w - 10.0, top), (w - 10.0, foot), (5.0, foot)], leather)
    # The spine at the left: dark, with raised bands.
    f.poly([(5.0, top), (20.0, top), (20.0, foot), (5.0, foot)], dark, body=False)
    for y in (40.0, 120.0, h - 120.0, h - 40.0):
        f.poly([(5.0, y - 4.0), (20.0, y - 4.0), (20.0, y + 4.0), (5.0, y + 4.0)], trim, body=False)
    f.ink([(20.0, top), (20.0, foot)], 1.4, K.shade(dark, 0.7))
    # A border tooled in the leather, and corners of metal.
    f.ink([(28.0, top + 12.0), (w - 18.0, top + 12.0), (w - 18.0, foot - 12.0), (28.0, foot - 12.0), (28.0, top + 12.0)], 1.6, trim)
    for cx0, cy0, sx, sy in ((w - 10.0, top, -1.0, 1.0), (w - 10.0, foot, -1.0, -1.0)):
        f.poly([(cx0, cy0), (cx0 + sx * 16.0, cy0), (cx0, cy0 + sy * 16.0)], trim, body=False)
    # The emblem of its ending, high on the cover.
    ex, ey = (20.0 + w - 10.0) / 2.0, 110.0
    if ending == "happy":
        _sun(f, ex, ey, trim, light)
    else:
        _moon(f, ex, ey, leather, trim, light)
        # Rain under the moon, down the cover.
        rng = random.Random("sad_door_rain")
        for _ in range(16):
            x, y = rng.uniform(32.0, w - 24.0), rng.uniform(146.0, 300.0)
            f.ink([(x, y), (x - 2.5, y + 9.0)], 1.2, K.alpha(light, 0.8))
    # The plate of the title, and the title in lines of gold.
    py = 230.0 if ending == "happy" else 316.0
    f.poly([(32.0, py - 14.0), (w - 22.0, py - 14.0), (w - 22.0, py + 14.0), (32.0, py + 14.0)], dark, body=False)
    f.ink([(32.0, py - 14.0), (w - 22.0, py - 14.0), (w - 22.0, py + 14.0), (32.0, py + 14.0), (32.0, py - 14.0)], 1.2, trim)
    f.ink([(38.0, py - 4.0), (w - 28.0, py - 4.0)], 2.0, trim)
    f.ink([(44.0, py + 5.0), (w - 34.0, py + 5.0)], 1.4, K.alpha(trim, 0.8))
    if ending == "happy":
        # The end, in leaves of gold under the plate: a little vine.
        for k in range(5):
            x = 36.0 + k * 9.0
            f.ellipse(x, 270.0 + 4.0 * math.sin(k), 3.0, 1.8, trim, body=False)
        f.ink([(34.0, 272.0), (52.0, 268.0), (74.0, 274.0)], 1.0, trim)
    return f.finish(width=1.6, glow_blur=2.0)


# ---------------------------------------------------------------------------
# Publication.
# ---------------------------------------------------------------------------

TARGETS: Dict[str, dict] = {
    "art_book_tower": _publisher("art_book_tower", "Book Tower", STILL, TOWER_FRAME, lambda anim, i, n: _draw_tower(),
                                 {"foot": (96.0, 384.0)}, "Scenery", ["prop", "scenery", "art", "stacks"]),
    "art_lectern": _publisher("art_lectern", "Lectern", GLOW_ROWS, LECTERN_FRAME, lambda anim, i, n: _draw_lectern(i, n),
                              {"foot": (64.0, 176.0)}, "Scenery", ["prop", "scenery", "art", "stacks"]),
    "art_quill_lamp": _publisher("art_quill_lamp", "Quill Lamp", GLOW_ROWS, LAMP_FRAME, lambda anim, i, n: _draw_lamp(i, n),
                                 {"foot": (40.0, 384.0)}, "Scenery", ["prop", "scenery", "art", "stacks"]),
}
for _ending in ENDINGS:
    TARGETS[f"art_ending_door_{_ending}"] = _publisher(
        f"art_ending_door_{_ending}", f"{_ending.title()} Ending Door", STILL, DOOR_FRAME,
        (lambda e: lambda anim, i, n: _draw_door(e))(_ending), {"foot": (48.0, 384.0)}, "Door", ["prop", "door", "lock", "art", "stacks"],
        forward=(0.0, -1.0))
