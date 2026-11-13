"""The drum kit of the bossofthegame's band (``docs/planning/game/final-boss.md``).

A prop of the stage, not of a body: an agent plays it in its ``band_drums``
row, sat on the kit's throne with a stick in each fist
(``targets/characters/_band_instruments.py``). Seen from the front three
quarters, as the band's rows are: a bass drum with a dark head, a snare, two
rack toms, a floor tom, a hi-hat, a crash and a ride on their stands, and the
throne behind. No writing on the bass drum head: the game may draw a prop
mirrored.

Animations: ``idle`` (one frame) and ``played`` (the cymbals shake, the
heads flash on the beat). No drop shadows: the game draws them.
"""

from __future__ import annotations

import math
from typing import Dict, List, Tuple

from ..characters import _art_cast_kit as K
from .art_props import _publisher

FRAME = (288, 208)
ROWS: List[Tuple[str, int, int]] = [("idle", 1, 1000), ("played", 4, 85)]

SHELL = (196, 40, 60, 255)
SHELL_DARK = (128, 22, 40, 255)
CHROME = (205, 210, 220, 255)
CHROME_DARK = (120, 126, 140, 255)
HEAD = (238, 232, 218, 255)
HEAD_DARK = (36, 30, 44, 255)
BRASS = (226, 182, 82, 255)
BRASS_DARK = (168, 124, 40, 255)
SEAT = (40, 34, 48, 255)
FLASH = (255, 236, 170, 255)


def _stand(f: K.Frame, x: float, top: float, foot: float) -> None:
    f.limb([(x, top), (x, foot - 6.0)], 2.0, CHROME_DARK, body=False)
    for dx in (-9.0, 0.0, 9.0):
        f.limb([(x, foot - 8.0), (x + dx, foot)], 1.6, CHROME_DARK, body=False)


def _cymbal(f: K.Frame, x: float, y: float, r: float, tilt: float, shake: float) -> None:
    a = math.radians(tilt + shake)
    ca, sa = math.cos(a), math.sin(a)
    pts = []
    for j in range(24):
        t = math.tau * j / 24.0
        px, py = r * math.cos(t), r * 0.22 * math.sin(t)
        pts.append((x + px * ca - py * sa, y + px * sa + py * ca))
    f.poly(pts, BRASS)
    f.ink([(x - r * 0.8 * ca, y - r * 0.8 * sa), (x + r * 0.8 * ca, y + r * 0.8 * sa)], 1.0, BRASS_DARK)
    f.dot(x, y, 2.0, BRASS_DARK)


def _drum(f: K.Frame, cx: float, top: float, rx: float, depth: float, flash: float) -> None:
    """A drum seen from a little above: its shell, its rim, its head."""
    ry = rx * 0.32
    f.poly([(cx - rx, top), (cx + rx, top), (cx + rx, top + depth), (cx - rx, top + depth)], SHELL)
    f.ellipse(cx, top + depth, rx, ry, SHELL)
    f.poly([(cx + rx * 0.45, top), (cx + rx, top), (cx + rx, top + depth), (cx + rx * 0.45, top + depth)], SHELL_DARK, body=False)
    for k in range(5):
        x = cx - rx + (k + 0.5) * 2.0 * rx / 5.0
        f.limb([(x, top + 2.0), (x, top + depth - 2.0)], 1.4, CHROME, body=False)
    f.ellipse(cx, top, rx, ry, CHROME)
    f.ellipse(cx, top, rx * 0.9, ry * 0.86, HEAD)
    if flash:
        f.glow(cx, top, rx * 0.8, K.alpha(FLASH, 0.5 * flash))


def _draw(i: int, n: int, played: bool):
    w, h = FRAME
    f = K.Frame(FRAME)
    foot = h - 4.0
    beat = (i % 2 == 0) if played else False
    shake = (6.0 if i % 2 == 0 else -4.0) if played else 0.0
    # The throne, behind the kit.
    f.limb([(150.0, foot - 64.0), (150.0, foot - 4.0)], 3.0, CHROME_DARK, body=False)
    f.ellipse(150.0, foot - 66.0, 20.0, 7.0, SEAT)
    # Cymbal stands and cymbals, behind the drums.
    _stand(f, 40.0, 58.0, foot)
    _stand(f, 246.0, 70.0, foot)
    _cymbal(f, 46.0, 54.0, 34.0, -14.0, shake)
    _cymbal(f, 240.0, 66.0, 38.0, 10.0, -shake)
    # The hi-hat, at the left.
    _stand(f, 70.0, 104.0, foot)
    _cymbal(f, 70.0, 100.0, 20.0, 0.0, 0.0)
    _cymbal(f, 70.0, 94.0 - (3.0 if beat else 0.0), 20.0, 0.0, 0.0)
    # The floor tom, at the right.
    for dx in (-18.0, 18.0):
        f.limb([(214.0 + dx, foot - 46.0), (214.0 + dx * 1.2, foot)], 1.6, CHROME_DARK, body=False)
    _drum(f, 214.0, foot - 82.0, 26.0, 40.0, 0.0)
    # The bass drum, seen from the front three quarters: its round front
    # head, dark, with a ring and a port.
    cx, cy, r = 138.0, foot - 44.0, 44.0
    f.ellipse(cx + 10.0, cy, r * 0.94, r, SHELL_DARK)
    f.ellipse(cx, cy, r, r, CHROME)
    f.ellipse(cx, cy, r - 4.0, r - 4.0, HEAD_DARK)
    f.ellipse(cx, cy, r * 0.62, r * 0.62, K.shade(HEAD_DARK, 1.12))
    f.ellipse(cx + 14.0, cy + 16.0, 8.0, 8.0, (20, 16, 26, 255))
    for k in range(8):
        t = math.tau * k / 8.0
        f.dot(cx + (r - 2.0) * math.cos(t), cy + (r - 2.0) * math.sin(t), 2.0, CHROME_DARK)
    for dx in (-30.0, 30.0):
        f.limb([(cx + dx, cy + 30.0), (cx + dx * 1.3, foot)], 2.0, CHROME_DARK, body=False)
    # The rack toms on the bass drum.
    _drum(f, 112.0, foot - 118.0, 18.0, 22.0, 0.0)
    _drum(f, 160.0, foot - 116.0, 20.0, 24.0, 0.8 if beat else 0.0)
    # The snare, at the left, on its stand.
    _stand(f, 92.0, foot - 64.0, foot)
    _drum(f, 92.0, foot - 76.0, 22.0, 14.0, 1.0 if beat else 0.0)
    return f.finish(width=1.6)


TARGETS: Dict[str, dict] = {
    "band_drum_kit": _publisher("band_drum_kit", "Drum Kit", ROWS, FRAME, lambda anim, i, n: _draw(i, n, anim == "played"),
                                {"foot": (144.0, float(FRAME[1]))}, "Scenery", ["prop", "scenery", "stage", "band", "boss_stage"]),
}
