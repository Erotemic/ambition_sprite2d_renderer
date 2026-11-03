"""The props of the Nile of the History dimension (biome `history_nile`).

The green strip of the river between the deserts, drawn in the cel style of
the cast (`targets/characters/_art_cast_kit.py`): the warm sepia of an old
textbook, with the colours of the era: sandstone, papyrus green, lapis, gold
and Nile blue.

- ``history_felucca``: the look of a sweeping platform (a `MovingPlatform`
  whose ``visual`` it is): a Nile sailing boat with a tall slanted sail on a
  long yard. The top of its deck is the platform (`platform_looks.ron`:
  `FELUCCA_SPAN`, `FELUCCA_TOP`); the sail rises over the deck. Its
  ``idle`` row fills the sail with the wind; the deck does not move.
- ``history_obelisk``: scenery. A tall obelisk of red granite with a gold
  cap, and a column of hieroglyphs down its face.
- ``history_papyrus``: scenery. A clump of papyrus: tall stems, each with a
  burst of fine threads at its top (its ``idle`` row moves them a little).
- ``history_canopic_jars``: scenery. Four jars of alabaster in a row, each
  with the lid of its guardian: a man, a baboon, a jackal and a falcon.
- ``history_pharaoh_statue``: scenery. A big seated statue of a pharaoh on
  his throne, hands on his knees, in a striped headdress and a false beard.
  Like many old statues, it has lost its nose. Its smile says that it does
  not mind.

The numbers are frame pixels; the game shows each prop at half its frame.
No drop shadows: the game draws them.
"""

from __future__ import annotations

import math
import random
from typing import Callable, Dict, List, Tuple

from PIL import ImageOps

from ..characters import _art_cast_kit as K
from .art_props import _publisher

STILL: List[Tuple[str, int, int]] = [("idle", 1, 1000)]
LOOP: List[Tuple[str, int, int]] = [("idle", 8, 140)]

#: The sepia of the textbook: the outline and the dark ink.
OUTLINE = (52, 34, 24, 255)
SEPIA = (112, 76, 48, 255)
SANDSTONE = (226, 186, 126, 255)
SANDSTONE_SHADE = (180, 136, 84, 255)
SANDSTONE_LIGHT = (244, 216, 166, 255)
GRANITE = (178, 96, 82, 255)
GRANITE_SHADE = (132, 64, 56, 255)
GRANITE_LIGHT = (210, 134, 116, 255)
PAPYRUS = (106, 160, 70, 255)
PAPYRUS_SHADE = (70, 116, 50, 255)
PAPYRUS_LIGHT = (176, 210, 104, 255)
LAPIS = (40, 74, 162, 255)
LAPIS_LIGHT = (86, 124, 206, 255)
GOLD = (236, 186, 60, 255)
GOLD_DARK = (176, 124, 30, 255)
GOLD_LIGHT = (252, 226, 140, 255)
NILE = (52, 132, 186, 255)
NILE_DARK = (30, 88, 136, 255)
TURQUOISE = (64, 176, 170, 255)
WOOD = (150, 98, 56, 255)
WOOD_SHADE = (106, 66, 36, 255)
WOOD_LIGHT = (190, 136, 84, 255)
CANVAS = (246, 236, 212, 255)
CANVAS_SHADE = (210, 192, 158, 255)
ROPE = (196, 164, 106, 255)
ALABASTER = (240, 228, 204, 255)
ALABASTER_SHADE = (204, 186, 156, 255)
LINEN = (246, 240, 224, 255)
LINEN_SHADE = (214, 202, 176, 255)
DARK = (60, 40, 30, 255)


def _phase(i: int, n: int) -> float:
    return i / float(max(1, n))


def _glyph(f: K.Frame, kind: str, x: float, y: float, s: float, colour) -> None:
    """One small hieroglyph in a box `s` high, its middle at (x, y)."""
    h = s / 2.0
    if kind == "ankh":
        f.ink(K.ellipse_points(x, y - h * 0.5, h * 0.35, h * 0.45, 12) + [K.ellipse_points(x, y - h * 0.5, h * 0.35, h * 0.45, 12)[0]], s * 0.13, colour)
        f.ink([(x - h * 0.6, y), (x + h * 0.6, y)], s * 0.14, colour)
        f.ink([(x, y), (x, y + h)], s * 0.14, colour)
    elif kind == "eye":
        f.poly([(x - h, y), (x - h * 0.2, y - h * 0.45), (x + h * 0.7, y - h * 0.1), (x + h * 0.4, y + h * 0.3), (x - h * 0.4, y + h * 0.25)], colour, body=False)
        f.ink([(x - h * 0.1, y + h * 0.3), (x - h * 0.2, y + h)], s * 0.1, colour)
        f.ink([(x + h * 0.2, y + h * 0.3), (x + h * 0.7, y + h * 0.9), (x + h * 0.9, y + h * 0.6)], s * 0.1, colour)
    elif kind == "bird":
        f.ellipse(x, y + h * 0.1, h * 0.55, h * 0.4, colour, body=False)
        f.ellipse(x + h * 0.5, y - h * 0.4, h * 0.25, h * 0.25, colour, body=False)
        f.poly([(x + h * 0.7, y - h * 0.45), (x + h, y - h * 0.3), (x + h * 0.7, y - h * 0.25)], colour, body=False)
        f.poly([(x - h * 0.4, y), (x - h, y + h * 0.3), (x - h * 0.3, y + h * 0.4)], colour, body=False)
        f.ink([(x, y + h * 0.4), (x - h * 0.1, y + h)], s * 0.08, colour)
        f.ink([(x + h * 0.2, y + h * 0.4), (x + h * 0.2, y + h)], s * 0.08, colour)
    elif kind == "water":
        for row in (-0.3, 0.3):
            pts = [(x - h + k * h / 3.0, y + row * h + (-h * 0.18 if k % 2 else h * 0.18)) for k in range(7)]
            f.ink(pts, s * 0.1, colour)
    elif kind == "reed":
        f.poly([(x, y + h), (x - h * 0.3, y), (x, y - h), (x + h * 0.25, y)], colour, body=False)
    elif kind == "sun":
        f.ink(K.ellipse_points(x, y, h * 0.7, h * 0.7, 14) + [K.ellipse_points(x, y, h * 0.7, h * 0.7, 14)[0]], s * 0.12, colour)
        f.dot(x, y, h * 0.2, colour)
    elif kind == "snake":
        f.ink([(x - h, y + h * 0.5), (x - h * 0.4, y + h * 0.1), (x + h * 0.1, y + h * 0.5), (x + h * 0.6, y), (x + h * 0.8, y - h * 0.4)], s * 0.14, colour)
    elif kind == "feather":
        f.poly([(x, y + h), (x - h * 0.3, y - h * 0.2), (x + h * 0.1, y - h), (x + h * 0.3, y - h * 0.1)], colour, body=False)
    elif kind == "hand":
        f.poly([(x - h, y + h * 0.2), (x + h * 0.6, y - h * 0.1), (x + h, y + h * 0.15), (x + h * 0.6, y + h * 0.35), (x - h, y + h * 0.5)], colour, body=False)
    else:
        f.poly([(x - h * 0.7, y - h * 0.15), (x + h * 0.7, y - h * 0.15), (x + h * 0.7, y + h * 0.15), (x - h * 0.7, y + h * 0.15)], colour, body=False)


GLYPHS = ("ankh", "eye", "bird", "water", "reed", "sun", "snake", "feather", "hand", "bar")


# ---------------------------------------------------------------------------
# The felucca: a platform look.
# ---------------------------------------------------------------------------

FELUCCA_FRAME = (320, 192)
FELUCCA_SPAN = (16.0, 304.0)
FELUCCA_TOP = 150.0


def _draw_felucca(anim: str, i: int, n: int):
    t = _phase(i, n)
    f = K.Frame(FELUCCA_FRAME)
    x0, x1 = FELUCCA_SPAN
    top = FELUCCA_TOP
    fill = 0.5 + 0.5 * math.sin(math.tau * t)
    # The mast, and the long yard that crosses it on a slant.
    mast_x = 150.0
    f.limb([(mast_x, top), (mast_x, 44.0)], 4.6, WOOD)
    f.ink([(mast_x - 1.0, top - 2.0), (mast_x - 1.0, 48.0)], 1.0, WOOD_LIGHT)
    tack, peak, clew = (54.0, 136.0), (266.0, 12.0), (238.0, 136.0)
    # The sail: a big triangle from the yard down to the boom. The wind
    # fills it: its back edge (the leech) and its middle bulge out.
    bulge = 6.0 + 8.0 * fill
    leech = []
    for k in range(9):
        u = k / 8.0
        x = peak[0] + (clew[0] - peak[0]) * u
        y = peak[1] + (clew[1] - peak[1]) * u
        leech.append((x + bulge * math.sin(math.pi * u), y))
    foot_line = []
    for k in range(9):
        u = k / 8.0
        x = clew[0] + (tack[0] - clew[0]) * u
        foot_line.append((x, clew[1] + 2.0 * math.sin(math.pi * u) * fill))
    sail = [tack, peak] + leech[1:] + foot_line[1:-1]
    f.poly(sail, CANVAS)
    # The shade of the sail where the wind fills it, and its seams.
    shade_poly = [(150.0 + 10.0 * fill, 70.0), peak] + leech[1:] + [(clew[0] - 30.0, clew[1])]
    f.poly(shade_poly, K.alpha(CANVAS_SHADE, 0.9), body=False)
    for k in range(1, 6):
        u = k / 6.0
        a = (tack[0] + (peak[0] - tack[0]) * u, tack[1] + (peak[1] - tack[1]) * u)
        b = (tack[0] + (clew[0] - tack[0]) * u + bulge * 0.4 * math.sin(math.pi * u), tack[1])
        f.ink([a, ((a[0] + b[0]) / 2.0 + bulge * 0.6, (a[1] + b[1]) / 2.0), b], 0.8, K.alpha(CANVAS_SHADE, 0.9))
    # The yard along the top edge, and the boom along its foot.
    f.limb([(tack[0] - 12.0, tack[1] + 6.0), (peak[0] + 4.0, peak[1] - 2.0)], 4.0, WOOD)
    f.ink([(tack[0] - 10.0, tack[1] + 4.6), (peak[0] + 2.0, peak[1] - 3.2)], 0.9, WOOD_LIGHT)
    f.limb([(tack[0] - 2.0, tack[1] + 1.0), (clew[0] + 4.0, clew[1] + 1.0)], 3.4, WOOD_SHADE)
    # The ropes: the sheet from the clew to the stern, a stay to the bow.
    f.ink([(clew[0] + 2.0, clew[1] + 2.0), (286.0, top - 2.0)], 1.0, ROPE)
    f.ink([(mast_x, 48.0), (24.0, top - 4.0)], 0.9, ROPE)
    f.ink([(mast_x, 48.0), (300.0, top - 6.0)], 0.9, ROPE)
    # The hull: the deck line is the platform; the hull curves under it to
    # a keel, with a high bow at the left and a low stern at the right.
    hull = [(x0, top), (x1, top), (312.0, top - 12.0), (310.0, top - 4.0), (296.0, 172.0), (250.0, 180.0), (80.0, 180.0), (36.0, 172.0),
            (10.0, top - 18.0), (8.0, top - 14.0)]
    f.poly(hull, WOOD)
    f.poly([(36.0, 172.0), (80.0, 180.0), (250.0, 180.0), (296.0, 172.0), (300.0, 166.0), (40.0, 166.0)], WOOD_SHADE, body=False)
    # The painted bands along the side: Nile blue, a line of gold, and an
    # eye at the bow to see the way.
    f.poly([(14.0, top + 4.0), (306.0, top + 4.0), (302.0, top + 11.0), (20.0, top + 11.0)], NILE, body=False)
    f.ink([(18.0, top + 13.0), (300.0, top + 13.0)], 1.4, GOLD)
    for k in range(13):
        f.ink([(30.0 + k * 21.0, top + 15.0), (30.0 + k * 21.0, top + 26.0)], 0.7, K.alpha(WOOD_SHADE, 0.9))
    f.poly([(22.0, top + 6.0), (32.0, top + 2.0), (40.0, top + 7.0), (32.0, top + 10.0)], K.WHITE, body=False)
    f.dot(32.0, top + 6.0, 1.8, DARK)
    # The deck: a strip of planks, lit on its top edge (the walking surface).
    f.poly([(x0, top), (x1, top), (x1, top + 3.0), (x0, top + 3.0)], WOOD_LIGHT, body=False)
    # The stern post and the steering oar at the right.
    f.limb([(304.0, top - 2.0), (312.0, top - 14.0)], 3.0, WOOD)
    f.limb([(290.0, top - 8.0), (304.0, 178.0)], 2.6, WOOD_SHADE)
    f.poly([(300.0, 172.0), (308.0, 172.0), (308.0, 186.0), (300.0, 186.0)], WOOD_SHADE)
    # The bow post at the left, curled up.
    f.limb([(16.0, top - 2.0), (9.0, top - 16.0), (12.0, top - 22.0)], 3.0, WOOD)
    # It is drawn with its bow at the left; the sheet faces right, as the
    # rest of the art does. The span is the same both ways.
    return ImageOps.mirror(f.finish(outline=OUTLINE, width=1.5))


# ---------------------------------------------------------------------------
# The obelisk.
# ---------------------------------------------------------------------------

OBELISK_FRAME = (96, 448)


def _draw_obelisk(anim: str, i: int, n: int):
    f = K.Frame(OBELISK_FRAME)
    rng = random.Random("history_obelisk")
    cx, foot, base_top = 48.0, 440.0, 414.0
    # The plinth.
    f.poly([(14.0, foot), (82.0, foot), (80.0, base_top), (16.0, base_top)], SANDSTONE)
    f.poly([(66.0, foot), (82.0, foot), (80.0, base_top), (66.0, base_top)], SANDSTONE_SHADE, body=False)
    f.ink([(17.0, base_top + 1.4), (79.0, base_top + 1.4)], 1.0, SANDSTONE_LIGHT)
    for x in (30.0, 48.0, 64.0):
        f.ink([(x, base_top + 4.0), (x, foot - 2.0)], 0.7, K.alpha(SANDSTONE_SHADE, 0.8))
    # The shaft, a little narrower at its top, then the pyramid of its cap.
    shaft_top = 54.0
    f.poly([(26.0, base_top), (70.0, base_top), (63.0, shaft_top), (33.0, shaft_top)], GRANITE)
    f.poly([(58.0, base_top), (70.0, base_top), (63.0, shaft_top), (56.0, shaft_top)], GRANITE_SHADE, body=False)
    f.ink([(28.0, base_top - 2.0), (34.5, shaft_top + 2.0)], 1.6, GRANITE_LIGHT)
    f.poly([(33.0, shaft_top), (63.0, shaft_top), (cx, 16.0)], GOLD)
    f.poly([(cx, shaft_top), (63.0, shaft_top), (cx, 16.0)], GOLD_DARK, body=False)
    f.ink([(35.0, shaft_top - 1.0), (cx - 0.5, 18.0)], 1.2, GOLD_LIGHT)
    f.glow(cx - 3.0, 32.0, 6.0, K.alpha(GOLD_LIGHT, 0.6))
    # The hieroglyphs: a column down the face of the shaft, and a cartouche
    # in the middle of it.
    y = shaft_top + 14.0
    k = 0
    while y < base_top - 14.0:
        if k == 6:
            f.poly(K.ellipse_points(cx - 2.0, y + 14.0, 8.0, 20.0, 20), K.alpha(GRANITE_SHADE, 0.9), body=False)
            f.ink(K.ellipse_points(cx - 2.0, y + 14.0, 8.0, 20.0, 20) + [K.ellipse_points(cx - 2.0, y + 14.0, 8.0, 20.0, 20)[0]], 1.0, GOLD)
            f.ink([(cx - 8.0, y + 36.0), (cx + 4.0, y + 36.0)], 1.2, GOLD)
            for j, kind in enumerate(("sun", "feather", "bird")):
                _glyph(f, kind, cx - 2.0, y + 2.0 + j * 12.0, 9.0, GOLD_LIGHT)
            y += 44.0
        else:
            kind = GLYPHS[rng.randrange(len(GLYPHS))]
            _glyph(f, kind, cx - 2.0, y, 11.0, LAPIS if k % 3 else GRANITE_SHADE)
            y += 15.0
        k += 1
    return f.finish(outline=OUTLINE, width=1.6)


# ---------------------------------------------------------------------------
# The papyrus.
# ---------------------------------------------------------------------------

PAPYRUS_FRAME = (128, 192)


def _draw_papyrus(anim: str, i: int, n: int):
    t = _phase(i, n)
    f = K.Frame(PAPYRUS_FRAME)
    rng = random.Random("history_papyrus")
    foot = 186.0
    stems = []
    for k in range(9):
        u = (k / 8.0) * 2.0 - 1.0
        stems.append((64.0 + u * 10.0 + rng.uniform(-2.0, 2.0), 64.0 + u * 38.0 + rng.uniform(-4.0, 4.0),
                      44.0 + abs(u) * 40.0 + rng.uniform(-8.0, 8.0), rng.random(), k))
    # Back to front: the far stems in shade, the near in full colour.
    order = sorted(stems, key=lambda s: s[3])
    for fx, tx, ty, r, k in order:
        sway = 3.0 * math.sin(math.tau * t + k * 0.8)
        tip = (tx + sway, ty)
        near = r > 0.4
        stem_col = PAPYRUS if near else PAPYRUS_SHADE
        mid = ((fx + tip[0]) / 2.0 + sway * 0.2, (foot + ty) / 2.0)
        f.limb([(fx, foot - 2.0), mid, tip], 3.0 if near else 2.4, stem_col)
        # The umbel: a fan of fine threads, out from the top of the stem.
        rays = []
        for j in range(23):
            a = math.radians(-172.0 + j * (164.0 / 22.0) + sway * 2.0)
            ln = (18.0 if j % 2 == 0 else 10.0) + 2.0 * math.sin(j * 1.7 + k)
            rays.append((tip[0] + math.cos(a) * ln, tip[1] + math.sin(a) * ln * 0.8))
        f.poly([tip] + rays, PAPYRUS_LIGHT if near else K.shade(PAPYRUS_LIGHT, 0.85))
        for ray in rays[::2]:
            f.ink([tip, ray], 0.6, stem_col)
            f.dot(ray[0], ray[1], 1.0, PAPYRUS_SHADE)
        f.poly([(tip[0] - 2.4, tip[1] + 3.0), (tip[0] + 2.4, tip[1] + 3.0), (tip[0], tip[1] - 2.0)], stem_col)
    # The sheaths at the foot of the stems.
    for k in range(6):
        x = 50.0 + k * 5.6
        f.poly([(x - 4.0, foot), (x + 4.0, foot), (x + 1.0 + (k - 2.5), foot - 16.0 - (k % 2) * 6.0)], PAPYRUS_SHADE)
    return f.finish(outline=OUTLINE, width=1.3)


# ---------------------------------------------------------------------------
# The canopic jars.
# ---------------------------------------------------------------------------

JARS_FRAME = (160, 96)


def _jar_body(f: K.Frame, cx: float, foot: float, rng: random.Random) -> float:
    """The jar of alabaster, with a column of glyphs; returns the row of its lip."""
    lip = foot - 46.0
    body = [(cx - 9.0, foot), (cx + 9.0, foot), (cx + 13.0, foot - 20.0), (cx + 13.0, foot - 34.0), (cx + 10.0, lip), (cx - 10.0, lip),
            (cx - 13.0, foot - 34.0), (cx - 13.0, foot - 20.0)]
    f.poly(body, ALABASTER)
    f.poly([(cx + 4.0, foot), (cx + 9.0, foot), (cx + 13.0, foot - 20.0), (cx + 13.0, foot - 34.0), (cx + 10.0, lip), (cx + 6.0, lip),
            (cx + 8.0, foot - 30.0)], ALABASTER_SHADE, body=False)
    f.poly([(cx - 3.5, lip + 5.0), (cx + 3.5, lip + 5.0), (cx + 3.5, foot - 5.0), (cx - 3.5, foot - 5.0)], K.alpha(ALABASTER_SHADE, 0.45), body=False)
    for j in range(3):
        _glyph(f, GLYPHS[rng.randrange(len(GLYPHS))], cx, lip + 10.0 + j * 10.0, 7.0, LAPIS)
    f.limb([(cx - 11.0, lip), (cx + 11.0, lip)], 3.0, ALABASTER_SHADE)
    return lip


def _draw_jars(anim: str, i: int, n: int):
    f = K.Frame(JARS_FRAME)
    rng = random.Random("history_canopic_jars")
    foot = 90.0
    xs = (24.0, 61.0, 99.0, 136.0)
    lips = [_jar_body(f, x, foot, rng) for x in xs]
    # The man: a face under a striped headdress.
    cx, lip = xs[0], lips[0]
    f.poly([(cx - 12.0, lip), (cx + 12.0, lip), (cx + 11.0, lip - 16.0), (cx + 6.0, lip - 26.0), (cx - 6.0, lip - 26.0), (cx - 11.0, lip - 16.0)],
           LAPIS)
    for k in range(5):
        y = lip - 4.0 - k * 4.5
        f.ink([(cx - 11.0 + (k > 2) * 2.0, y), (cx + 11.0 - (k > 2) * 2.0, y)], 1.2, GOLD)
    f.ellipse(cx + 1.0, lip - 12.0, 6.5, 8.0, (214, 160, 110, 255))
    f.dot(cx + 3.0, lip - 14.0, 1.1, DARK)
    f.dot(cx - 1.5, lip - 14.0, 1.1, DARK)
    f.ink([(cx - 1.0, lip - 8.0), (cx + 3.0, lip - 8.0)], 0.8, DARK)
    f.limb([(cx + 0.5, lip - 5.0), (cx + 0.5, lip + 1.0)], 2.4, LAPIS)
    # The baboon: a round head with a big muzzle, its ears to the side.
    cx, lip = xs[1], lips[1]
    fur = (176, 150, 112, 255)
    f.ellipse(cx, lip - 12.0, 11.0, 11.0, fur)
    f.ellipse(cx - 9.0, lip - 20.0, 5.0, 4.0, K.shade(fur, 0.85))
    f.ellipse(cx + 9.0, lip - 20.0, 5.0, 4.0, K.shade(fur, 0.85))
    f.ellipse(cx, lip - 16.0, 11.0, 6.0, K.shade(fur, 0.85))
    f.ellipse(cx + 2.0, lip - 6.0, 8.0, 6.0, (214, 180, 150, 255))
    f.dot(cx - 3.0, lip - 14.0, 1.4, DARK)
    f.dot(cx + 4.0, lip - 14.0, 1.4, DARK)
    f.dot(cx + 0.5, lip - 7.0, 0.9, DARK)
    f.dot(cx + 3.5, lip - 7.0, 0.9, DARK)
    f.ink([(cx - 2.0, lip - 3.0), (cx + 6.0, lip - 3.5)], 0.8, DARK)
    # The jackal: a long snout and tall pointed ears, painted black.
    cx, lip = xs[2], lips[2]
    jackal = (58, 52, 60, 255)
    f.poly([(cx - 4.0, lip - 16.0), (cx - 8.0, lip - 34.0), (cx + 1.0, lip - 20.0)], jackal)
    f.poly([(cx + 1.0, lip - 18.0), (cx + 2.0, lip - 34.0), (cx + 7.0, lip - 17.0)], jackal)
    f.ellipse(cx - 1.0, lip - 10.0, 9.0, 9.0, jackal)
    f.poly([(cx + 2.0, lip - 15.0), (cx + 17.0, lip - 8.0), (cx + 17.0, lip - 4.0), (cx + 2.0, lip - 2.0)], jackal)
    f.poly([(cx - 6.0, lip - 30.0), (cx - 3.0, lip - 21.0), (cx - 1.0, lip - 21.0)], GOLD, body=False)
    f.ellipse(cx + 3.0, lip - 12.0, 2.0, 1.4, GOLD, body=False)
    f.dot(cx + 16.0, lip - 7.0, 1.2, K.INK)
    f.ink([(cx - 9.0, lip - 4.0), (cx + 8.0, lip - 3.0)], 1.4, GOLD)
    # The falcon: a hooked beak and the mark under its eye.
    cx, lip = xs[3], lips[3]
    feather = (170, 120, 78, 255)
    f.ellipse(cx - 1.0, lip - 12.0, 11.0, 11.0, feather)
    f.poly([(cx + 7.0, lip - 16.0), (cx + 15.0, lip - 13.0), (cx + 13.0, lip - 7.0), (cx + 9.0, lip - 9.0)], GOLD)
    f.ink([(cx + 13.5, lip - 8.0), (cx + 11.0, lip - 6.0)], 1.0, GOLD_DARK)
    f.ellipse(cx + 3.0, lip - 15.0, 2.8, 2.8, K.WHITE, body=False)
    f.dot(cx + 3.6, lip - 15.0, 1.4, DARK)
    f.ink([(cx + 2.0, lip - 12.0), (cx + 1.0, lip - 5.0), (cx - 2.0, lip - 3.0)], 1.4, DARK)
    f.poly([(cx - 11.0, lip - 12.0), (cx - 4.0, lip - 22.0), (cx - 1.0, lip - 2.0), (cx - 11.0, lip - 4.0)], K.shade(feather, 0.82), body=False)
    return f.finish(outline=OUTLINE, width=1.3)


# ---------------------------------------------------------------------------
# The seated statue.
# ---------------------------------------------------------------------------

STATUE_FRAME = (256, 448)


def _draw_statue(anim: str, i: int, n: int):
    f = K.Frame(STATUE_FRAME)
    cx = 128.0
    foot = 440.0
    S0, S1, SL = SANDSTONE, SANDSTONE_SHADE, SANDSTONE_LIGHT
    # The plinth, with a cartouche on its front.
    f.poly([(18.0, foot), (238.0, foot), (236.0, 404.0), (20.0, 404.0)], S0)
    f.poly([(206.0, foot), (238.0, foot), (236.0, 404.0), (206.0, 404.0)], S1, body=False)
    f.ink([(22.0, 405.5), (234.0, 405.5)], 1.4, SL)
    cart = K.ellipse_points(cx, 422.0, 44.0, 11.0, 24)
    f.ink(cart + cart[:1], 1.6, SEPIA)
    f.ink([(cx + 46.0, 414.0), (cx + 46.0, 430.0)], 1.6, SEPIA)
    for k, kind in enumerate(("sun", "feather", "eye", "bird", "water", "ankh")):
        _glyph(f, kind, cx - 34.0 + k * 13.6, 422.0, 10.0, SEPIA)
    # The throne behind him: a block, its side to the right.
    f.poly([(42.0, 404.0), (214.0, 404.0), (214.0, 214.0), (42.0, 214.0)], S1)
    f.poly([(196.0, 404.0), (214.0, 404.0), (214.0, 214.0), (196.0, 214.0)], K.shade(S1, 0.85), body=False)
    for y in (240.0, 300.0, 360.0):
        f.ink([(44.0, y), (194.0, y)], 0.8, K.alpha(SEPIA, 0.4))
    # The legs: two columns, the shins straight down to the feet.
    for lx in (98.0, 158.0):
        f.poly([(lx - 18.0, 300.0), (lx + 18.0, 300.0), (lx + 15.0, 392.0), (lx - 15.0, 392.0)], S0)
        f.poly([(lx + 6.0, 300.0), (lx + 18.0, 300.0), (lx + 15.0, 392.0), (lx + 6.0, 392.0)], S1, body=False)
        f.ink([(lx - 4.0, 310.0), (lx - 3.0, 382.0)], 1.2, SL)
        # A foot: toes to the front.
        f.poly([(lx - 18.0, 404.0), (lx + 18.0, 404.0), (lx + 16.0, 390.0), (lx - 16.0, 390.0)], S0)
        for k in range(5):
            f.ink([(lx - 12.0 + k * 6.0, 398.0), (lx - 12.0 + k * 6.0, 404.0)], 0.8, S1)
    # The kilt over the thighs, pleated, with a belt.
    f.poly([(70.0, 250.0), (186.0, 250.0), (192.0, 304.0), (64.0, 304.0)], LINEN)
    f.poly([(160.0, 250.0), (186.0, 250.0), (192.0, 304.0), (162.0, 304.0)], LINEN_SHADE, body=False)
    for k in range(9):
        x = 82.0 + k * 12.0
        f.ink([(x, 258.0), (x + (x - cx) * 0.06, 302.0)], 0.8, LINEN_SHADE)
    f.poly([(cx - 10.0, 258.0), (cx + 10.0, 258.0), (cx + 8.0, 300.0), (cx - 8.0, 300.0)], GOLD, body=False)
    for k in range(4):
        f.ink([(cx - 9.0 + k * 0.5, 266.0 + k * 9.0), (cx + 9.0 - k * 0.5, 266.0 + k * 9.0)], 1.0, LAPIS)
    f.poly([(70.0, 244.0), (186.0, 244.0), (186.0, 254.0), (70.0, 254.0)], GOLD)
    for k in range(10):
        f.ink([(74.0 + k * 11.6, 245.0), (74.0 + k * 11.6, 253.0)], 1.0, LAPIS)
    # The chest: broad shoulders down to a narrow waist.
    f.poly([(72.0, 160.0), (184.0, 160.0), (174.0, 244.0), (82.0, 244.0)], S0)
    f.poly([(150.0, 160.0), (184.0, 160.0), (174.0, 244.0), (156.0, 244.0)], S1, body=False)
    f.ink([(cx, 196.0), (cx, 236.0)], 1.0, K.alpha(S1, 0.9))
    f.ellipse(cx, 238.0, 2.0, 1.6, S1, body=False)
    # The arms: down at his sides, and the forearms flat on his thighs,
    # the hands on his knees.
    for side in (-1.0, 1.0):
        sx = cx + side * 58.0
        f.poly([(sx - 11.0, 166.0), (sx + 11.0, 166.0), (sx + 9.0, 250.0), (sx - 9.0, 250.0)], S0 if side < 0 else S1)
        f.ink([(sx - side * 2.0, 176.0), (sx - side * 2.0, 242.0)], 1.0, SL if side < 0 else K.alpha(S0, 0.8))
        hx = cx + side * 40.0
        f.poly([(sx - 10.0, 250.0), (sx + 10.0, 250.0), (hx + 14.0, 290.0), (hx - 14.0, 290.0)], S0 if side < 0 else S1)
        f.poly([(hx - 15.0, 282.0), (hx + 15.0, 282.0), (hx + 14.0, 302.0), (hx - 14.0, 302.0)], S0)
        for k in range(4):
            f.ink([(hx - 10.0 + k * 6.6, 292.0), (hx - 10.0 + k * 6.6, 302.0)], 0.9, S1)
        # A gold band on the upper arm.
        f.limb([(sx - 11.0, 184.0), (sx + 11.0, 184.0)], 4.0, GOLD)
    # The neck, behind the beard and the lappets.
    f.poly([(cx - 32.0, 112.0), (cx + 32.0, 112.0), (cx + 34.0, 162.0), (cx - 34.0, 162.0)], S1)
    # The broad collar of beads, in rows of gold, lapis and turquoise.
    for k, colour in enumerate((GOLD, LAPIS, TURQUOISE, GOLD, LAPIS)):
        r = 46.0 - k * 5.0
        arc = [(cx + math.cos(a) * r, 154.0 + math.sin(a) * r * 0.62) for a in [math.pi * (j / 16.0) for j in range(17)]]
        f.limb(arc, 5.4, colour, body=k == 0)
    # The headdress: a cloth of gold and lapis stripes over the head, with
    # its two lappets down in front of the shoulders.
    for side in (-1.0, 1.0):
        lap = [(cx + side * 30.0, 120.0), (cx + side * 46.0, 132.0), (cx + side * 44.0, 186.0), (cx + side * 30.0, 186.0)]
        f.poly(lap, GOLD)
        for k in range(8):
            y = 130.0 + k * 7.0
            f.ink([(cx + side * 31.0, y), (cx + side * 45.0, y)], 2.4, LAPIS)
    hood = [(cx - 50.0, 130.0), (cx - 40.0, 64.0), (cx - 24.0, 40.0), (cx + 24.0, 40.0), (cx + 40.0, 64.0), (cx + 50.0, 130.0),
            (cx + 30.0, 124.0), (cx - 30.0, 124.0)]
    f.poly(hood, GOLD)
    for k in range(10):
        y = 50.0 + k * 8.0
        w = 26.0 + min(1.0, k / 4.0) * 20.0
        f.ink([(cx - w, y), (cx + w, y)], 2.6, LAPIS)
    f.poly([(cx + 26.0, 124.0), (cx + 50.0, 130.0), (cx + 40.0, 64.0), (cx + 30.0, 56.0)], K.alpha(GOLD_DARK, 0.55), body=False)
    # The face, framed by the band of the headdress.
    f.poly([(cx - 28.0, 58.0), (cx + 28.0, 58.0), (cx + 28.0, 64.0), (cx - 28.0, 64.0)], GOLD)
    f.ellipse(cx, 92.0, 25.0, 31.0, S0)
    f.poly([(cx + 10.0, 66.0), (cx + 25.0, 80.0), (cx + 22.0, 108.0), (cx + 10.0, 120.0)], K.alpha(S1, 0.7), body=False)
    # The cobra on the brow.
    f.limb([(cx, 70.0), (cx, 56.0), (cx + 3.0, 50.0)], 4.0, GOLD)
    f.ellipse(cx + 1.0, 50.0, 4.0, 5.0, GOLD)
    f.dot(cx + 2.0, 49.0, 0.9, DARK)
    # The eyes: long lines of kohl, and a contented look.
    for side in (-1.0, 1.0):
        ex = cx + side * 11.0
        f.ink([(ex - 7.0, 84.0), (ex + 7.0, 84.0), (ex + side * 11.0, 82.0)], 1.8, DARK)
        f.ink([(ex - 6.0, 86.0), (ex, 88.0), (ex + 6.0, 86.0)], 1.4, DARK)
        f.ink([(ex - 7.0, 78.0), (ex + 7.0, 77.0)], 2.0, K.alpha(DARK, 0.8))
    # The nose: broken off long ago. A flat chip of stone is all that is left.
    f.poly([(cx - 5.0, 90.0), (cx + 5.0, 90.0), (cx + 6.0, 104.0), (cx - 6.0, 104.0)], SL, body=False)
    for k in range(3):
        f.ink([(cx - 4.0 + k * 3.0, 93.0 + k * 2.0), (cx - 1.0 + k * 3.0, 98.0 + k * 2.0)], 0.9, S1)
    f.ink([(cx - 6.0, 104.0), (cx - 2.0, 106.0), (cx + 2.0, 105.0), (cx + 6.0, 104.0)], 1.0, S1)
    # A smile that does not mind.
    f.ink([(cx - 10.0, 111.0), (cx, 115.0), (cx + 10.0, 111.0)], 1.8, DARK)
    # The false beard: a plaited block on a strap, under his chin.
    f.poly([(cx - 6.0, 120.0), (cx + 6.0, 120.0), (cx + 5.0, 150.0), (cx - 5.0, 150.0)], LAPIS)
    for k in range(5):
        f.ink([(cx - 5.0, 125.0 + k * 5.5), (cx + 5.0, 123.0 + k * 5.5)], 1.2, GOLD)
    f.ink([(cx - 23.0, 100.0), (cx - 6.0, 121.0)], 1.0, K.alpha(DARK, 0.6))
    f.ink([(cx + 23.0, 100.0), (cx + 6.0, 121.0)], 1.0, K.alpha(DARK, 0.6))
    # A crack across the throne: it is very old.
    f.ink([(50.0, 226.0), (58.0, 236.0), (54.0, 248.0), (62.0, 262.0)], 1.2, K.alpha(SEPIA, 0.8))
    return f.finish(outline=OUTLINE, width=1.8)


# ---------------------------------------------------------------------------
# Publication.
# ---------------------------------------------------------------------------

DRAW: Dict[str, Callable] = {
    "history_felucca": _draw_felucca,
    "history_obelisk": _draw_obelisk,
    "history_papyrus": _draw_papyrus,
    "history_canopic_jars": _draw_jars,
    "history_pharaoh_statue": _draw_statue,
}

TARGETS: Dict[str, dict] = {
    "history_felucca": _publisher("history_felucca", "Felucca", LOOP, FELUCCA_FRAME, _draw_felucca,
                                  {"top": ((FELUCCA_SPAN[0] + FELUCCA_SPAN[1]) / 2.0, FELUCCA_TOP)}, "Scenery", ["prop", "platform", "history"]),
    "history_obelisk": _publisher("history_obelisk", "Obelisk", STILL, OBELISK_FRAME, _draw_obelisk, {"foot": (48.0, 448.0)}, "Scenery",
                                  ["prop", "scenery", "history"]),
    "history_papyrus": _publisher("history_papyrus", "Papyrus", LOOP, PAPYRUS_FRAME, _draw_papyrus, {"foot": (64.0, 192.0)}, "Scenery",
                                  ["prop", "scenery", "history"]),
    "history_canopic_jars": _publisher("history_canopic_jars", "Canopic Jars", STILL, JARS_FRAME, _draw_jars, {"foot": (80.0, 96.0)}, "Scenery",
                                       ["prop", "scenery", "history"]),
    "history_pharaoh_statue": _publisher("history_pharaoh_statue", "Pharaoh Statue", STILL, STATUE_FRAME, _draw_statue, {"foot": (128.0, 448.0)},
                                         "Scenery", ["prop", "scenery", "history"]),
}
