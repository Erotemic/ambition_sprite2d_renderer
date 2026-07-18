"""A portable authoring seam: :class:`FrameSet`.

``FrameSet`` represents a target that naturally describes itself as scalable
frame-painting callables: named animations, ordered frames, and a known logical
canvas. Shared pipeline code can supersample, downsample, crop, measure,
assemble, and emit those frames without each compatible family reimplementing
that machinery.

It is deliberately **not** the universal character representation. Bespoke
procedural modules, config-driven generators, bone/rig documents, SVG-part
renderers, scene graphs, and other specialized targets may use ``FrameSet``
when it is a good fit or publish through another family-specific path. Their
common contract is the resulting sprite sheet and rich metadata, not this
source type.

Coordinate frame (matches the existing drawers): logical pixels, origin
top-left, +x right, +y down, angles clockwise. A frame is drawn by a callable
``draw(d, s)`` where ``d`` is a ``PIL.ImageDraw`` over a canvas of
``base_size * s`` and ``s`` is the working scale the spine chooses (supersample
× the requested output ``scale``). Authoring multiplies its coordinates by
``s`` — exactly the convention ``targets/props/entities.py`` already uses.

Pillow + stdlib only. No metadata is *required*; compatible pipeline code can
measure feet and body extent from rendered pixels. ``FrameSpec.meta`` carries
facts pixels cannot express reliably, such as sockets, explicit collision
boxes, or declared attack hitboxes — "measure by default, declare the
exceptions."
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

# A frame painter: draw into a PIL.ImageDraw over a `base_size * s` canvas.
# Typed loosely (``object``) so importing this module needs no Pillow types at
# definition time; the spine passes a real ``PIL.ImageDraw``.
DrawFn = Callable[[object, float], None]


@dataclass
class FrameSpec:
    """One frame: how to paint it, plus optional declared metadata."""

    draw: DrawFn
    # Per-frame declarations the renderer can't measure from pixels. Examples:
    #   "sockets":  {"hand_r": (x, y), "muzzle": (x, y)}   # logical-px points
    #   "hitbox":   (x, y, w, h)                            # declared attack box
    # All in logical (unscaled) canvas pixels. Empty = "measure everything."
    meta: Dict[str, object] = field(default_factory=dict)


@dataclass
class AnimationSpec:
    """One animation row: an ordered list of frames and a frame cadence."""

    name: str
    frames: List[FrameSpec]
    frame_duration_ms: int = 120

    @property
    def frame_count(self) -> int:
        return len(self.frames)


@dataclass
class FrameSet:
    """The complete authoring output for one target's sheet."""

    name: str
    base_size: Tuple[int, int]
    animations: List[AnimationSpec]
    # Optional shared palette (name -> "#RRGGBB[AA]") for authors that want one;
    # purely informational to the spine.
    palette: Optional[Dict[str, str]] = None
    # Crop behaviour for the assembled frames, mirroring the existing drawers:
    #   "tight"  — crop to the union alpha bbox (default for sprites)
    #   "ground" — like tight, but keep the bottom edge flush (feet = bottom row)
    #   "none"   — keep the full canvas (tiles that repeat seamlessly)
    crop: str = "tight"

    def animation(self, name: str) -> Optional[AnimationSpec]:
        return next((a for a in self.animations if a.name == name), None)

    @property
    def animation_names(self) -> List[str]:
        return [a.name for a in self.animations]


def frameset_from_states(
    name: str,
    base_size: Tuple[int, int],
    states: Dict[str, DrawFn],
    *,
    crop: str = "tight",
    frame_duration_ms: int = 120,
) -> FrameSet:
    """Build a single-frame-per-state FrameSet from ``{state: draw_fn}``.

    The common shape for props/entities/icons, whose "animations" are really
    one still frame per state (e.g. ``chest_closed`` / ``chest_open``). Mirrors
    how ``targets/props/entities.py`` is authored, so those drawers can adopt
    the seam with a one-line wrapper.
    """
    return FrameSet(
        name=name,
        base_size=base_size,
        crop=crop,
        animations=[
            AnimationSpec(state, [FrameSpec(fn)], frame_duration_ms)
            for state, fn in states.items()
        ],
    )
