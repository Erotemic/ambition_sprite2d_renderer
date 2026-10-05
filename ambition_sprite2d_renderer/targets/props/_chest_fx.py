"""Effects the SVG-rigged chests share (``treasure_chest``, ``boss_chest``):
light pooled over the opening, beams fanning out of it, the light leaking
under a cracked lid, the burst as the lid flies back, the click of the lock
and sparkles. Painted in the drawing's SVG units, about each glyph's pivot,
for ``_creature_fx.Glyphs``; ``GLYPHS`` gives each one's extent.
"""

from __future__ import annotations

import math
from typing import Dict, Tuple

from ..characters import _creature_fx as FX
from ..characters._svg_fighter_effects import FxCanvas

LIGHT = (255, 226, 130)
HOT = (255, 248, 214)
WHITE = (255, 255, 250, 255)
def tint(rgb, alpha: int):
    return (rgb[0], rgb[1], rgb[2], alpha)


def paint_glow(c: FxCanvas) -> None:
    """Warm light pooled over the opening (soft: stacked translucent ovals)."""
    for k, (rx, ry, alpha) in enumerate(((170, 74, 26), (140, 58, 30), (112, 44, 36), (82, 30, 44), (52, 18, 60))):
        c.ellipse((0, 0), rx, ry, tint(LIGHT if k < 3 else HOT, alpha))


def paint_rays(c: FxCanvas) -> None:
    """Thin beams fanning up out of the chest, each a pale core in a warm sheath."""
    for k, ang in enumerate(range(-150, -20, 18)):
        length = 210.0 if k % 2 else 160.0
        for half, scale, color in ((2.6, 1.0, tint(LIGHT, 48)), (0.9, 0.85, tint(HOT, 96))):
            a0, a1 = math.radians(ang - half), math.radians(ang + half)
            L = length * scale
            c.polygon([(0, 0), (L * math.cos(a0), L * math.sin(a0)), (L * math.cos(a1), L * math.sin(a1))], color)


def paint_leak(c: FxCanvas) -> None:
    """Light escaping the crack under a lifted lid: a hot slit, a halo, short
    beams fanning up and out."""
    c.ellipse((0, 0), 150, 22, tint(LIGHT, 60))
    c.ellipse((0, 0), 140, 8, tint(HOT, 200))
    for ang in (-170, -150, -125, -100, -80, -55, -30, -10):
        r = math.radians(ang)
        c.line([(110 * math.cos(r) * 0.9, 6 * math.sin(r)), (150 * math.cos(r), 70 * math.sin(r))], tint(HOT, 150), 3.0)


def paint_burst(c: FxCanvas) -> None:
    c.star((0, 0), 120.0, tint(HOT, 170), points=12, inner=0.32, rotation=-90)
    c.star((0, 0), 64.0, WHITE, points=8, inner=0.4, rotation=-67.5)


def paint_sparkle(c: FxCanvas) -> None:
    c.star((0, 0), 16.0, WHITE, points=4, inner=0.22, rotation=0)
    c.star((0, 0), 8.0, tint(LIGHT, 255), points=4, inner=0.3, rotation=45)


def paint_click(c: FxCanvas) -> None:
    c.star((0, 0), 26.0, tint(HOT, 255), points=6, inner=0.3, rotation=0)
    for ang in (-60, -20, 20, 60, 120, 160, 200, 240):
        r = math.radians(ang)
        c.line([(28 * math.cos(r), 28 * math.sin(r)), (40 * math.cos(r), 40 * math.sin(r))], WHITE, 2.4)


#: The shared glyphs by name: (extent, paint), in SVG units.
GLYPHS: Dict[str, Tuple[FX.Extent, FX.Paint]] = {
    "glow": ((172.0, 76.0, 172.0, 76.0), paint_glow),
    "rays": ((212.0, 212.0, 212.0, 6.0), paint_rays),
    "leak": ((152.0, 72.0, 152.0, 24.0), paint_leak),
    "burst": ((154.0, 154.0, 154.0, 154.0), paint_burst),
    "sparkle": ((18.0, 18.0, 18.0, 18.0), paint_sparkle),
    "click": ((42.0, 42.0, 42.0, 42.0), paint_click),
}
