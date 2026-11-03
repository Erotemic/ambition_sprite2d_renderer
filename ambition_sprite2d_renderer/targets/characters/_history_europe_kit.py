"""The drawing kit of the European cast of the History dimension (second pass).

The second pass of the History dimension is a grid: each floor is a region
of the world, and each column is a time. The European floor goes from the
Ice Age to the Viking north. Its cast is drawn on the kit of the Art
dimension's cast (`_art_cast_kit.py`): flat colour with one shade, and one
bold dark outline round the silhouette. This module adds what that cast
shares:

- the colours of the European rooms: the Ice Age, the megalith builders and
  the northern woods;
- :class:`ScaledFrame`, a frame that draws every shape larger or smaller
  about one pivot point, so that a big beast can fill its frame;
- :func:`fur`, strands of long fur along a line;
- :func:`breath`, puffs of breath in the cold air.

The sidecar, the "!" and the dust are those of `_history_cast_kit.py`.
Each figure faces right and stands with its feet on its ground row.
"""

from __future__ import annotations

import math
import random
from typing import List, Sequence, Tuple

from . import _art_cast_kit as K

Point = Tuple[float, float]

#: The outline: the dark sepia ink of an old textbook.
OUTLINE = (44, 30, 24, 255)

# -- the Ice Age ----------------------------------------------------------------

SNOW = (240, 244, 250, 255)
ICE = (176, 214, 236, 255)
ICE_DARK = (110, 158, 196, 255)
#: The long hair of a mammoth: a warm red brown, darker underneath.
MAMMOTH_FUR = (150, 92, 54, 255)
MAMMOTH_FUR_LIGHT = (194, 132, 80, 255)
MAMMOTH_FUR_DARK = (100, 58, 34, 255)
MAMMOTH_SKIN = (84, 60, 50, 255)
IVORY = (240, 228, 196, 255)
IVORY_SHADE = (196, 178, 138, 255)
#: A cave bear: a dark brown with a grizzled light tip.
BEAR_FUR = (110, 74, 48, 255)
BEAR_FUR_LIGHT = (160, 116, 76, 255)
BEAR_FUR_DARK = (70, 46, 32, 255)
#: The paints of the caves.
OCHRE_RED = (178, 70, 40, 255)
OCHRE_YELLOW = (214, 160, 70, 255)
CHARCOAL = (46, 40, 38, 255)
ROCK = (196, 172, 140, 255)
ROCK_SHADE = (150, 124, 96, 255)

# -- the megalith builders -----------------------------------------------------

SARSEN = (176, 172, 158, 255)
SARSEN_LIGHT = (212, 208, 192, 255)
SARSEN_SHADE = (128, 124, 112, 255)
LICHEN = (196, 196, 120, 255)
TURF = (104, 150, 72, 255)
TURF_DARK = (66, 104, 48, 255)
THATCH = (206, 168, 92, 255)
THATCH_SHADE = (156, 118, 56, 255)

# -- the northern woods ---------------------------------------------------------

OAK = (138, 92, 54, 255)
OAK_LIGHT = (182, 132, 82, 255)
OAK_DARK = (90, 58, 34, 255)
PINE = (54, 98, 74, 255)
IRON = (96, 98, 110, 255)
IRON_LIGHT = (170, 174, 186, 255)
IRON_DARK = (58, 58, 68, 255)
WOOL_RED = (172, 46, 40, 255)
WOOL_RED_DARK = (114, 28, 26, 255)
WOOL_BLUE = (52, 84, 136, 255)
WOOL_BLUE_DARK = (32, 52, 92, 255)
WOOL = (226, 216, 190, 255)
WOOL_SHADE = (180, 166, 132, 255)
LEATHER = (120, 80, 50, 255)
LEATHER_DARK = (80, 52, 32, 255)
SKIN = (232, 186, 150, 255)
SKIN_SHADE = (192, 140, 106, 255)
BEARD = (196, 132, 62, 255)
BEARD_DARK = (140, 88, 36, 255)
GOLD = (236, 190, 70, 255)
#: The "!" of a figure that sees you: the red of a map.
ALARM = (206, 58, 40, 255)


class ScaledFrame(K.Frame):
    """A frame that draws every shape `size` times as large about `pivot`.

    A beast is drawn in its own numbers, then fitted to its frame: the
    shapes, the widths of the lines and the radii all scale.
    """

    def __init__(self, frame_size: Tuple[int, int], size: float, pivot: Point) -> None:
        super().__init__(frame_size)
        self.k = size
        self.pivot = pivot

    def at(self, x: float, y: float) -> Point:
        """The frame point of the drawing point (`x`, `y`)."""
        px, py = self.pivot
        return px + (x - px) * self.k, py + (y - py) * self.k

    def _w(self, points):
        return [(x * K.SUPER, y * K.SUPER) for x, y in (self.at(px, py) for px, py in points)]

    def ellipse(self, cx, cy, rx, ry, fill, body=True):
        x, y = self.at(cx, cy)
        super().ellipse(x, y, rx * self.k, ry * self.k, fill, body)

    def dot(self, cx, cy, r, fill=K.INK):
        x, y = self.at(cx, cy)
        super().dot(x, y, r * self.k, fill)

    def glow(self, cx, cy, r, fill):
        x, y = self.at(cx, cy)
        super().glow(x, y, r * self.k, fill)

    def limb(self, points, width, fill, body=True):
        super().limb(points, width * self.k, fill, body)

    def ink(self, points, width=1.2, fill=K.INK):
        super().ink(points, width * self.k, fill)


def fur(f: K.Frame, points: Sequence[Point], length: float, colour, seed: str, width: float = 1.4, lean: float = 0.0, step: float = 5.0) -> None:
    """Strands of long fur that hang from the line `points`.

    Each strand falls `length` pixels (a little more or less), and `lean`
    pushes its tip back (minus) or forward (plus), as fur in the wind.
    """
    rng = random.Random(seed)
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        seg = math.hypot(x1 - x0, y1 - y0)
        for k in range(max(1, int(seg / step))):
            u = (k + rng.uniform(0.0, 0.8)) / max(1, int(seg / step))
            x, y = x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
            ln = length * rng.uniform(0.7, 1.15)
            f.ink([(x, y), (x + lean * 0.5 + rng.uniform(-1.0, 1.0), y + ln * 0.55), (x + lean + rng.uniform(-1.5, 1.5), y + ln)], width, colour)


def breath(f: K.Frame, x: float, y: float, amount: float, colour=SNOW, toward: float = 1.0, limit: float = 1e9) -> None:
    """Two or three puffs of breath in the cold air, out of a mouth at (`x`,
    `y`). `amount` 0..1 grows them; `toward` is +1 to the right; no puff
    passes `limit` (a frame x)."""
    if amount <= 0.05:
        return
    for k in range(3):
        r = 2.4 + 2.6 * amount + k * 1.4
        px = x + toward * (4.0 + k * 6.0 * amount)
        if toward > 0:
            px = min(limit - r, px)
        f.ellipse(px, y - k * 2.0, r, r * 0.75, K.alpha(colour, 0.8 * amount * (1.0 - 0.2 * k)), body=False)


def smooth(points: Sequence[Point], per: int = 6) -> List[Point]:
    """A smooth curve through `points` (Catmull-Rom), with `per` points on
    each span."""
    pts = [points[0]] + list(points) + [points[-1]]
    out: List[Point] = []
    for k in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[k - 1], pts[k], pts[k + 1], pts[k + 2]
        for j in range(per):
            u = j / float(per)
            u2, u3 = u * u, u * u * u
            out.append(tuple(0.5 * (2 * p1[c] + (-p0[c] + p2[c]) * u + (2 * p0[c] - 5 * p1[c] + 4 * p2[c] - p3[c]) * u2
                                    + (-p0[c] + 3 * p1[c] - 3 * p2[c] + p3[c]) * u3) for c in (0, 1)))  # type: ignore[misc]
    out.append(points[-1])
    return out


def taper(f: K.Frame, points: Sequence[Point], w0: float, w1: float, colour, body: bool = True) -> List[Point]:
    """A smooth stroke through `points` that narrows from `w0` to `w1` (a
    tusk, a horn, a tail). Returns its middle line."""
    mid = smooth(points)
    left, right = [], []
    for k, (x, y) in enumerate(mid):
        a = mid[max(0, k - 1)]
        b = mid[min(len(mid) - 1, k + 1)]
        nx, ny = -(b[1] - a[1]), b[0] - a[0]
        ln = math.hypot(nx, ny) or 1.0
        w = (w0 + (w1 - w0) * k / max(1, len(mid) - 1)) / 2.0
        left.append((x + nx / ln * w, y + ny / ln * w))
        right.append((x - nx / ln * w, y - ny / ln * w))
    f.poly(left + right[::-1], colour, body)
    f.ellipse(mid[-1][0], mid[-1][1], w1 / 2.0, w1 / 2.0, colour, body)
    return mid
