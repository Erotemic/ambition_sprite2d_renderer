"""Effects and rig loading shared by the SVG-rigged creatures built with
``rigbuild.creature_rig`` (the T-rex boss, the raptor stalker, the bear mauler).

Each is drawn in SVG units and published at an ``art_scale``; its effects are
authored in the same units. Each effect is a glyph painted ONCE at full
strength, about its own pivot (logical (0, 0)), at the effect canvas's
supersample; a frame places it with the clip's ``fx.*`` strength as the draw's
opacity, so a part flipbook stores one raster per glyph, not one per frame.
"""

from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path
from typing import Callable, Dict, Tuple

from PIL import Image

from ...authoring.rigdoc import RigDocument
from ._svg_fighter_effects import FxCanvas

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]
Paint = Callable[[FxCanvas], None]
#: (left, top, right, bottom) extent about the pivot, in SVG units.
Extent = Tuple[float, float, float, float]

#: ``compose_rig_frame``'s effect supersample for a rig published at 1x.
FX_SCALE = 3

FLASH = (255, 252, 236, 255)
FLASH_GOLD = (255, 214, 92, 255)
DUST = (176, 150, 108, 170)
DUST_DARK = (128, 106, 74, 150)
SHOCK = (255, 232, 170, 230)
CRACK = (58, 44, 30, 220)
HIT = (255, 236, 120, 255)


@lru_cache(maxsize=8)
def _load_doc_cached(path_text: str, mtime_ns: int, size: int) -> RigDocument:
    del mtime_ns, size
    return RigDocument.load(path_text)


def rig_document(path: Path) -> RigDocument:
    """The rig document at ``path``, reloaded when the file changes."""
    stat = path.stat()
    return _load_doc_cached(str(path), stat.st_mtime_ns, stat.st_size)


def rest_frames(doc: RigDocument) -> Dict[str, Tuple[Point, float]]:
    """Each bone's rest ``(origin, world angle)`` in sprite pixels: the pose
    the drawing is in."""
    frame = doc.frame
    worlds = doc.build_skeleton().world({}, root=(float(frame["center_x"]), float(frame["ground_y"])))
    return {name: (bw.origin, bw.angle) for name, bw in worlds.items()}


def anchor(rest: Dict[str, Tuple[Point, float]], bone: str, svg_point: Point, art_scale: float) -> Point:
    """A point the drawing marks (SVG units) in ``bone``'s own frame, so an
    effect placed with ``world[bone].to_world(anchor)`` stays on the drawn
    feature (a fin's edge, a tail tip) however the bone turns."""
    (ox, oy), angle = rest[bone]
    dx, dy = svg_point[0] * art_scale - ox, svg_point[1] * art_scale - oy
    r = math.radians(-angle)
    return (dx * math.cos(r) - dy * math.sin(r), dx * math.sin(r) + dy * math.cos(r))


class Glyphs:
    """A character's effect glyphs, painted at its ``art_scale``."""

    def __init__(self, art_scale: float, glyphs: Dict[str, Tuple[Extent, Paint]]) -> None:
        self.art_scale = art_scale
        self.glyphs = glyphs
        self._rasters: Dict[str, Tuple[Image.Image, Point]] = {}

    def raster(self, name: str) -> Tuple[Image.Image, Point]:
        """The glyph's raster and its pivot, in effect-canvas pixels."""
        cached = self._rasters.get(name)
        if cached is None:
            (left, top, right, bottom), paint = self.glyphs[name]
            k = self.art_scale
            size = (int(math.ceil((left + right) * k)), int(math.ceil((top + bottom) * k)))
            canvas = FxCanvas(size, scale=FX_SCALE, origin=(left, top), unit_scale=k)
            paint(canvas)
            cached = self._rasters[name] = (canvas.image, (left * FX_SCALE * k, top * FX_SCALE * k))
        return cached

    def place(self, canvas: FxCanvas, name: str, at: Point, opacity: float, degrees: float = 0.0) -> None:
        if opacity > 0.02:
            canvas.place(self.raster(name), at, degrees, min(1.0, opacity), name=name)

    def local(self, bone, x: float, y: float) -> Point:
        """A point in a bone's frame given in SVG units."""
        return bone.to_world((x * self.art_scale, y * self.art_scale))


# --- shared glyph paints (SVG units) ---------------------------------------------


def paint_bite(c: FxCanvas) -> None:
    # The snap: crescents closing on the fang tips, and a glint where they meet.
    for sign in (-1.0, 1.0):
        c.arc((-6, sign * 22.0), 30, 22, 300 if sign > 0 else 30, 360 if sign > 0 else 90, FLASH_GOLD, 3.4)
        c.arc((-6, sign * 22.0), 30, 22, 305 if sign > 0 else 35, 355 if sign > 0 else 85, FLASH, 1.6)
    for ang in (-30.0, 0.0, 30.0):
        r = math.radians(ang)
        c.line([(18 + 4 * math.cos(r), 10 * math.sin(r)), (18 + 16 * math.cos(r), 22 * math.sin(r))], FLASH_GOLD, 2.2)
    c.star((10, 0), 8.0, FLASH, points=4, inner=0.28, rotation=0)


def tail_trail(radius: float) -> Paint:
    """A trail swept by a tail's tip: an arc whose centre is ``radius`` to the
    glyph's right (pivot on the arc, so it is placed a tail's length behind
    the tail's root)."""

    def paint(c: FxCanvas) -> None:
        c.arc((radius, 0), radius, radius * 0.92, 146, 214, (255, 255, 255, 120), 9.0)
        c.arc((radius, 0), radius, radius * 0.92, 150, 210, (255, 246, 214, 220), 3.2)
        c.arc((radius, 0), radius - 16, radius * 0.92 - 16, 156, 204, (255, 246, 214, 150), 1.8)

    return paint


def paint_dust(c: FxCanvas) -> None:
    for (x, y, r) in ((-12, 2, 9.0), (0, -4, 11.0), (13, 1, 9.5), (4, 5, 8.0)):
        c.ellipse((x, y), r, r * 0.72, DUST)
    for (x, y, r) in ((-7, 6, 5.0), (9, 6, 5.5)):
        c.ellipse((x, y), r, r * 0.6, DUST_DARK)


def paint_shock(c: FxCanvas) -> None:
    c.ellipse((0, 0), 78, 13, None, SHOCK, 3.0)
    c.ellipse((0, 0), 52, 8, None, (255, 246, 214, 170), 1.8)
    for pts in (
        [(-6, 2), (-22, 5), (-30, 3), (-44, 7)],
        [(6, 2), (20, 6), (34, 4), (46, 8)],
        [(0, 3), (-4, 8), (2, 11)],
    ):
        c.line(pts, CRACK, 1.6)


def paint_hit(c: FxCanvas) -> None:
    c.star((0, 0), 18.0, HIT, points=8, inner=0.38, rotation=-90)
    c.star((0, 0), 9.0, FLASH, points=8, inner=0.45, rotation=-67.5)


def paint_thud(c: FxCanvas) -> None:
    for (x, y, r) in ((-60, 0, 13), (-34, -5, 16), (-6, -7, 18), (24, -5, 16), (52, 0, 13), (78, 2, 10)):
        c.ellipse((x, y), r, r * 0.62, DUST)
    for (x, y, r) in ((-46, 4, 8), (8, 3, 10), (60, 4, 7)):
        c.ellipse((x, y), r, r * 0.5, DUST_DARK)


#: The glyphs every creature shares, by name: (extent, paint).
COMMON: Dict[str, Tuple[Extent, Paint]] = {
    "bite": ((40.0, 30.0, 40.0, 30.0), paint_bite),
    "dust": ((24.0, 16.0, 26.0, 14.0), paint_dust),
    "shock": ((84.0, 18.0, 84.0, 18.0), paint_shock),
    "hit": ((20.0, 20.0, 20.0, 20.0), paint_hit),
    "thud": ((76.0, 20.0, 92.0, 14.0), paint_thud),
}
