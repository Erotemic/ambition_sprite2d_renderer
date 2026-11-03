"""The colours of the Mongol Steppe and the Monsoon Coast (the History dimension).

The cast of the History dimension is drawn on the kit of the Art dimension
(`_art_cast_kit.py`): cel shapes, flat colour with one shade, and one thick
dark outline round each silhouette. This module adds what the creatures of
era 5 (the Mongol Steppe) and era 6 (Timbuktu and the Monsoon Coast) share:

- the sepia ink of an old textbook, for the outline and the lines;
- the accents of each era;
- the "!" that a creature shows when it sees you, in the red of a map;
- :class:`ScaledPen`, a pen of `_stage_kit.py` that also scales.

It draws nothing by itself.
"""

from __future__ import annotations

from . import _art_cast_kit as K
from . import _stage_kit as S

#: The ink of the dimension: the dark brown of a printed textbook.
SEPIA_INK = (50, 32, 24, 255)
SEPIA_LINE = (86, 58, 40, 255)
PAPER = (244, 232, 204, 255)
PAPER_SHADE = (210, 190, 152, 255)
MAP_RED = (206, 58, 40, 255)

# -- the Mongol Steppe ---------------------------------------------------------

STEPPE_GREEN = (104, 150, 70, 255)
STEPPE_GREEN_DARK = (66, 104, 48, 255)
STEPPE_GOLD = (226, 184, 84, 255)
STEPPE_GOLD_DARK = (164, 122, 46, 255)
SKY = (98, 160, 214, 255)
SKY_DARK = (58, 108, 164, 255)
FELT = (240, 232, 214, 255)
FELT_SHADE = (196, 184, 160, 255)
SADDLE_RED = (184, 50, 40, 255)
SADDLE_RED_DARK = (124, 30, 28, 255)
FUR = (176, 118, 64, 255)
FUR_DARK = (124, 78, 40, 255)
SKIN = (226, 172, 122, 255)
SKIN_SHADE = (190, 132, 90, 255)
HAIR_BLACK = (44, 34, 30, 255)

# -- Timbuktu and the Monsoon Coast ---------------------------------------------

ADOBE = (204, 146, 86, 255)
ADOBE_DARK = (150, 98, 54, 255)
GOLD = (246, 196, 62, 255)
GOLD_LIGHT = (255, 236, 150, 255)
GOLD_DARK = (176, 120, 30, 255)
SALT = (246, 244, 236, 255)
TURQUOISE = (44, 186, 180, 255)
TURQUOISE_DARK = (22, 120, 124, 255)
MONSOON = (138, 146, 160, 255)
MONSOON_LIGHT = (190, 198, 210, 255)
MONSOON_DARK = (84, 90, 108, 255)
CORAL = (238, 110, 92, 255)
CORAL_LIGHT = (252, 164, 142, 255)
CORAL_DARK = (172, 62, 58, 255)


def alarm_mark(f: K.Frame, x: float, y: float) -> None:
    """The "!" over a creature that sees you: map red, as a mark on a map."""
    f.limb([(x, y - 10.0), (x, y)], 2.6, MAP_RED)
    f.ellipse(x, y + 5.0, 1.7, 1.7, MAP_RED)


class ScaledPen(S.Pen):
    """A pen that also makes what it draws `scale` times larger about its
    pivot (before the turn and the move). Line widths and dots grow too."""

    def __init__(self, f: K.Frame, pivot=(0.0, 0.0), rot: float = 0.0, shift=(0.0, 0.0), scale: float = 1.0) -> None:
        super().__init__(f, pivot, rot, shift)
        self.scale = scale

    def p(self, points):
        px, py, s = self.pivot[0], self.pivot[1], self.scale
        return super().p([(px + (x - px) * s, py + (y - py) * s) for x, y in points])

    def limb(self, points, width, fill, body=True) -> None:
        super().limb(points, width * self.scale, fill, body)

    def ink(self, points, width=1.2, fill=SEPIA_INK) -> None:
        super().ink(points, width * self.scale, fill)

    def dot(self, cx, cy, r, fill=SEPIA_INK) -> None:
        super().dot(cx, cy, r * self.scale, fill)
