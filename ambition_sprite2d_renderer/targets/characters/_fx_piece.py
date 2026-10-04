"""Action effects (glows, arcs, streaks) as rig pieces for the ``_toon_rig``
painters.

An effect that a painter draws straight into the frame at its strength (an
alpha, a length) is a new raster in every frame of a part flipbook. Drawn
through this module, the effect is a piece painted ONCE at full strength
and placed with the strength as the draw's opacity (``rigdoc.blit_rotated``
records it), turned (an orbit, a spin) or mirrored (the same raster
transposed). Users: Alice and Bob.
"""

from __future__ import annotations

import math
from typing import Callable, Dict, Hashable, Tuple

from PIL import Image

from ...authoring import rigdoc
from . import _toon_rig

Point = Tuple[float, float]

_MIRRORED: Dict[int, Tuple[Image.Image, Tuple[Image.Image, Point]]] = {}


def mirrored(part: Tuple[Image.Image, Point]) -> Tuple[Image.Image, Point]:
    """``part`` mirrored left to right about its pivot: the same raster
    transposed (a zero-cost transform for the publisher), cached."""
    image, pivot = part
    cached = _MIRRORED.get(id(image))
    if cached is None or cached[0] is not image:
        cached = (image, (image.transpose(Image.FLIP_LEFT_RIGHT), (image.width - pivot[0], pivot[1])))
        _MIRRORED[id(image)] = cached
    return cached[1]


def place_fx(
    frame: _toon_rig.Frame,
    key: Hashable,
    half: Tuple[float, float],
    at: Point,
    paint: Callable,
    name: str,
    *,
    degrees: float = 0.0,
    opacity: float = 1.0,
    mirror: bool = False,
) -> None:
    """An effect piece painted by ``paint(draw, origin)`` around ``origin``
    on a ``2 * half`` canvas (as ``_toon_rig.anchored``), placed with the
    origin at ``at`` (canvas pixels, before the body turn), turned
    ``degrees`` plus the body turn, with ``opacity``. A hit flash does not
    tint it: an effect is light, not a surface. ``mirror`` places the piece
    mirrored about its origin. ``key`` must name everything ``paint`` reads."""
    hx, hy = float(math.ceil(half[0])), float(math.ceil(half[1]))
    origin = (hx, hy)
    part = _toon_rig.piece(key, (2 * hx, 2 * hy), origin, lambda draw: paint(draw, origin))
    if mirror:
        part = mirrored(part)
    rigdoc.blit_rotated(
        frame.canvas, part[0], part[1], frame.point(at), degrees + frame.degrees, round(opacity, 3), part_name=name
    )


def place_mirrored_pair(
    frame: _toon_rig.Frame,
    key: Hashable,
    half: Tuple[float, float],
    at: Point,
    paint: Callable,
    name: str,
    *,
    degrees: float = 0.0,
    opacity: float = 1.0,
) -> None:
    """An effect that is symmetric about its own x axis (an arc around +x)
    as ONE half: ``paint`` paints the half below the axis (+y), placed as
    ``place_fx`` does, and its mirror above the axis is the same raster
    mirrored and turned a half turn. Draws ``name`` and ``name + "_mirror"``."""
    place_fx(frame, key, half, at, paint, name, degrees=degrees, opacity=opacity)
    place_fx(frame, key, half, at, paint, f"{name}_mirror", degrees=degrees + 180.0, opacity=opacity, mirror=True)
