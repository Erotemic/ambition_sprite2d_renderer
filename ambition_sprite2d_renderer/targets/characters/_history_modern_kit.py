"""The drawing kit of two eras of the History dimension: the Age of Sail and
the Industrial Age.

The cast of these eras is drawn on the kit of the Art dimension
(`_art_cast_kit.py`): flat colour, one shade, and one bold outline round the
silhouette. This module adds what the two eras share:

- the colours of an old textbook and a map (sepia, parchment), and the
  accent colours of each era (sea green, tar, canvas and brass; brick, soot,
  iron, steam and gaslight);
- the warm dark outline of the dimension;
- small things that several figures draw: the "!" of a figure that sees
  you, a puff of steam or smoke, a coin, a banknote, a line of text.

Each figure faces right and stands with its feet on its ground row.
"""

from __future__ import annotations

import math
import random
from typing import Optional, Sequence, Tuple

from ambition_sprite2d_renderer.core.draw import blending_draw, font

from . import _art_cast_kit as K

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

#: The outline of the dimension: the brown-black of old printer's ink.
OUTLINE: RGBA = (44, 28, 22, 255)

#: The textbook and the map.
PARCHMENT: RGBA = (238, 222, 184, 255)
PARCHMENT_SHADE: RGBA = (204, 182, 138, 255)
SEPIA: RGBA = (150, 104, 60, 255)
SEPIA_DARK: RGBA = (96, 62, 34, 255)

#: People.
SKIN: RGBA = (236, 190, 150, 255)
SKIN_SHADE: RGBA = (204, 148, 112, 255)
SKIN_TAN: RGBA = (204, 150, 104, 255)
SKIN_TAN_SHADE: RGBA = (166, 112, 74, 255)
FLUSH: RGBA = (230, 130, 120, 255)
WHITE: RGBA = (255, 255, 255, 255)
SHIRT: RGBA = (244, 238, 224, 255)
SHIRT_SHADE: RGBA = (206, 196, 178, 255)

#: The Age of Sail.
SEA_GREEN: RGBA = (40, 138, 118, 255)
SEA_GREEN_DARK: RGBA = (22, 88, 76, 255)
TAR: RGBA = (40, 36, 36, 255)
TAR_LIGHT: RGBA = (88, 82, 80, 255)
CANVAS: RGBA = (240, 232, 212, 255)
CANVAS_SHADE: RGBA = (204, 190, 160, 255)
BRASS: RGBA = (214, 170, 66, 255)
BRASS_DARK: RGBA = (150, 108, 30, 255)
BRASS_LIGHT: RGBA = (250, 222, 140, 255)
ROPE: RGBA = (206, 170, 110, 255)
ROPE_DARK: RGBA = (150, 116, 66, 255)
OAK: RGBA = (150, 100, 58, 255)
OAK_DARK: RGBA = (100, 64, 36, 255)
OAK_LIGHT: RGBA = (190, 140, 88, 255)
COAT_RED: RGBA = (170, 40, 44, 255)
COAT_RED_DARK: RGBA = (112, 24, 30, 255)
NAVY: RGBA = (40, 56, 100, 255)
NAVY_DARK: RGBA = (24, 34, 66, 255)
SEAL_RED: RGBA = (196, 30, 36, 255)
LEMON: RGBA = (252, 226, 64, 255)
LEMON_DARK: RGBA = (204, 168, 20, 255)
STEEL: RGBA = (214, 220, 230, 255)
STEEL_SHADE: RGBA = (140, 148, 164, 255)

#: The Industrial Age.
BRICK: RGBA = (168, 66, 46, 255)
BRICK_DARK: RGBA = (112, 40, 28, 255)
BRICK_LIGHT: RGBA = (204, 104, 76, 255)
MORTAR: RGBA = (196, 182, 160, 255)
SOOT: RGBA = (42, 40, 46, 255)
SOOT_LIGHT: RGBA = (92, 88, 100, 255)
IRON: RGBA = (104, 110, 120, 255)
IRON_DARK: RGBA = (62, 66, 76, 255)
IRON_LIGHT: RGBA = (156, 164, 176, 255)
STEAM: RGBA = (238, 242, 246, 255)
STEAM_SHADE: RGBA = (196, 204, 214, 255)
GASLIGHT: RGBA = (255, 214, 110, 255)
GASLIGHT_HOT: RGBA = (255, 244, 196, 255)
FIRE: RGBA = (250, 128, 40, 255)
FIRE_DARK: RGBA = (196, 66, 24, 255)
GOLD: RGBA = (244, 196, 60, 255)
GOLD_DARK: RGBA = (176, 124, 24, 255)
GOLD_LIGHT: RGBA = (255, 236, 150, 255)
BANKNOTE: RGBA = (196, 222, 180, 255)
BANKNOTE_DARK: RGBA = (96, 140, 90, 255)
FUR: RGBA = (150, 104, 70, 255)
FUR_LIGHT: RGBA = (204, 164, 120, 255)
FUR_DARK: RGBA = (100, 66, 42, 255)


def finish(f: K.Frame, fade: float = 1.0, width: float = 1.4, outline: RGBA = OUTLINE, glow_blur: float = 2.5):
    """The frame at its published size, in the outline of the dimension."""
    return f.finish(outline=outline, width=width, glow_blur=glow_blur, fade=fade)


def alarm_mark(f: K.Frame, x: float, y: float) -> None:
    """The "!" over the head of a figure that sees you: a red mark with a
    gold rim, as a stamp in the margin of a textbook."""
    f.limb([(x, y - 10.0), (x + 0.6, y)], 2.8, SEAL_RED)
    f.ellipse(x + 0.4, y + 5.0, 1.8, 1.8, SEAL_RED)


def puff(f: K.Frame, x: float, y: float, r: float, colour: RGBA, rng: random.Random, lumps: int = 5, body: bool = True, shade_colour: Optional[RGBA] = None) -> None:
    """A puff of steam or smoke: round lumps about a middle, with a shade
    under them."""
    pts = []
    for k in range(lumps):
        a = math.tau * k / lumps + rng.uniform(-0.3, 0.3)
        d = r * rng.uniform(0.35, 0.6)
        pts.append((x + math.cos(a) * d, y + math.sin(a) * d * 0.8, r * rng.uniform(0.45, 0.65)))
    for px, py, pr in pts:
        f.ellipse(px, py, pr, pr, colour, body=body)
    if shade_colour is not None:
        f.ellipse(x + r * 0.15, y + r * 0.3, r * 0.55, r * 0.3, shade_colour, body=False)


def coin(f, x: float, y: float, r: float, spin: float = 0.0) -> None:
    """A gold coin. `spin` (0..1) turns it on its edge: 0 shows its face."""
    sx = max(0.18, abs(math.cos(math.pi * spin)))
    f.ellipse(x, y, r * sx, r, GOLD_DARK)
    f.ellipse(x - r * 0.12 * sx, y - r * 0.08, r * 0.8 * sx, r * 0.82, GOLD, body=False)
    if sx > 0.5:
        f.ellipse(x - r * 0.12 * sx, y - r * 0.08, r * 0.45 * sx, r * 0.48, GOLD_DARK, body=False)
        f.dot(x - r * 0.4 * sx, y - r * 0.45, r * 0.18, GOLD_LIGHT)


def banknote(pen, x: float, y: float, angle: float, w: float = 8.0, h: float = 4.6) -> None:
    """A banknote that flutters: a green note with a darker frame and a seal."""
    pts = K.turn([(x - w / 2, y - h / 2), (x + w / 2, y - h / 2), (x + w / 2, y + h / 2), (x - w / 2, y + h / 2)], x, y, angle)
    pen.poly(pts, BANKNOTE)
    inner = K.turn([(x - w / 2 + 1.0, y - h / 2 + 0.9), (x + w / 2 - 1.0, y - h / 2 + 0.9), (x + w / 2 - 1.0, y + h / 2 - 0.9),
                    (x - w / 2 + 1.0, y + h / 2 - 0.9)], x, y, angle)
    pen.ink(inner + [inner[0]], 0.5, BANKNOTE_DARK)
    pen.dot(x, y, min(w, h) * 0.22, BANKNOTE_DARK)


def text(f: K.Frame, x: float, y: float, s: str, size: float, fill: RGBA, anchor: str = "mm") -> None:
    """A line of text centred on `(x, y)` (published pixels), drawn in the
    frame's picture and not in its silhouette."""
    d = blending_draw(f.image)
    d.text((x * K.SUPER, y * K.SUPER), s, fill=fill, font=font(int(round(size * K.SUPER))), anchor=anchor)


def ring(f: K.Frame, cx: float, cy: float, rx: float, ry: float, width: float, fill: RGBA, count: int = 28) -> None:
    """A ring of ink round an ellipse (it does not change the outline)."""
    pts = K.ellipse_points(cx, cy, rx, ry, count)
    f.ink(pts + [pts[0]], width, fill)


def tapered(points: Sequence[Point], widths: Sequence[float]) -> Tuple[list, list]:
    """The two edges of a shape that follows `points` with a width at each
    point (a tentacle, a tail, a plume). Returns the left and the right
    edge, each in the order of `points`."""
    left, right = [], []
    n = len(points)
    for k in range(n):
        x0, y0 = points[max(0, k - 1)]
        x1, y1 = points[min(n - 1, k + 1)]
        dx, dy = x1 - x0, y1 - y0
        d = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / d, dx / d
        w = widths[k] / 2.0
        x, y = points[k]
        left.append((x + nx * w, y + ny * w))
        right.append((x - nx * w, y - ny * w))
    return left, right
