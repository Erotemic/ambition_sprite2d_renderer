"""Measure-by-default: derive body geometry from a rendered frame's pixels.

The heart of the metadata model — the renderer measures what it can from the
art instead of hand-authoring it. This is the one canonical body/feet
measurement; the two spines (``sheet.py``, ``sheet_build.py``) had divergent
copies (one used an inclusive last-opaque row for the feet, the other one-past).
We standardise on the **inclusive last opaque row**, the same "lowest opaque
pixel" rule the grounded-door fix uses, so feet planting is consistent.

Bevy anchor convention: ``(0, 0)`` = sprite centre, ``+0.5`` y = top edge. The
runtime uses ``feet_anchor_norm.y`` directly as ``feet_anchor_y`` so it never
hand-tunes feet per target.

A body is what is VISIBLE (:data:`VISIBLE_ALPHA`), not every pixel with a
non-zero alpha: the frames are resampled down from a larger canvas, and the
resampling kernel leaves a fringe of near-transparent pixels round every edge.
A box that counts the fringe stands the body on it, and the drawn feet then
float above the floor by the width of the fringe.

Pillow + stdlib only — takes a ``PIL.Image``, so this module imports nothing.
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

#: The least alpha a pixel has to be part of a measured body. The LANCZOS
#: fringe of a frame downsampled 4x reaches ~15 (measured on Sanic's soles);
#: an eighth of full opacity is above it and below any paint that is meant to
#: be seen.
VISIBLE_ALPHA = 32


def visible_bbox(frame) -> Optional[Tuple[int, int, int, int]]:
    """The box ``(x0, y0, x1, y1)`` (high side open) of the pixels of ``frame``
    with an alpha of at least :data:`VISIBLE_ALPHA`; ``None`` when it has none.

    The one rule for "where the drawn body is". Use the plain alpha box only to
    crop, where a faint pixel must not be cut.
    """
    if "A" not in frame.getbands():
        return frame.getbbox()
    return frame.getchannel("A").point(lambda a: 255 if a >= VISIBLE_ALPHA else 0).getbbox()


def measure_body_metrics(frame) -> Optional[Dict[str, Any]]:
    """Body bbox + feet anchor from ``frame``'s visible pixels (:func:`visible_bbox`).

    Returns ``None`` for a frame with no visible pixel (callers decide the
    degenerate fallback).
    """
    bbox = visible_bbox(frame)
    if bbox is None:
        return None
    fw, fh = frame.size
    x_min, y_min, x_max, y_max = bbox
    # `getbbox` is half-open on the high side; subtract 1 for the inclusive
    # last opaque row so the feet anchor sits on the last drawn pixel.
    feet_y = y_max - 1
    feet_x = (x_min + x_max - 1) / 2.0
    return {
        "frame_width": fw,
        "frame_height": fh,
        "body_pixel_bbox": {
            "x": int(x_min),
            "y": int(y_min),
            "w": int(x_max - x_min),
            "h": int(y_max - y_min),
        },
        "feet_pixel": {"x": float(feet_x), "y": float(feet_y)},
        # Image-y grows downward; image_y=feet_y → anchor_y = 0.5 - feet_y/fh.
        "feet_anchor_norm": {
            "x": float(feet_x / fw - 0.5),
            "y": float(0.5 - feet_y / fh),
        },
    }
