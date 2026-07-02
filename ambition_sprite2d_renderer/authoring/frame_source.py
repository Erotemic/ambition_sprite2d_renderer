"""The canonical thing the sheet pipeline consumes: a ``FrameSource``.

A ``FrameSource`` is "a character or prop ready to render, at any size". It is
the one contract behind every distinct drawing backend — procedural PIL
generators, bone rigs, plain frame callables. Each backend *produces* a
FrameSource; none is reshaped into one by an adapter.

The build pipeline asks a FrameSource four kinds of question:

* what animations do you have, and how long is each? (:meth:`animations`)
* draw me one frame at this size (:meth:`frame`)
* which pose is your canonical still? (:meth:`canonical_pose`)
* what is your gameplay geometry and identity? (the geometry/metadata hooks)

Concrete producers live next door: :class:`GeneratedFrameSource` (procedural
generators), and the callable/​rig sources introduced with the unified pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol, Tuple, runtime_checkable

from PIL import Image


@runtime_checkable
class FrameSource(Protocol):
    """Everything the sheet pipeline needs to build one target's sheet."""

    #: Target id (the sheet/record key; matches the config/module stem).
    target: str

    def animations(self) -> Dict[str, Dict[str, int]]:
        """``{animation: {"frames": n, "duration_ms": d}}``."""

    def frame(
        self, animation: str, index: int, count: int, size: Tuple[int, int]
    ) -> Image.Image:
        """Render frame ``index`` of ``animation`` (``count`` frames total) at ``size``."""

    def canonical_pose(self) -> Tuple[str, int]:
        """The ``(animation, frame_index)`` used as the single canonical still."""

    def attack_hitboxes(self, size: Tuple[int, int]) -> Dict[str, Dict[str, Any]]:
        """Per-animation authored attack-hitbox shapes (default: none)."""

    def hurtbox_parts(self, size: Tuple[int, int]) -> Dict[str, Dict[str, Any]]:
        """Per-animation authored hurtbox-part overrides (default: none)."""

    def body_inset(self) -> Optional[Dict[str, float]]:
        """Fractional shrink of the measured body box (default: ``None``)."""

    def actor_metadata(self) -> Optional[Dict[str, Any]]:
        """Sparse actor-contract facts for the ``*_actor.ron`` sidecar (default ``None``)."""

    def spec_dict(self) -> Optional[Dict[str, Any]]:
        """The serialised spec for the manifest, or ``None`` for spec-less sources."""


@dataclass(frozen=True)
class RenderedFrame:
    """One independently-rendered frame, with the metadata a packer or a debug
    view needs. ``image`` is at the requested render size."""

    animation: str
    index: int
    count: int
    duration_ms: int
    image: Image.Image

    @property
    def key(self) -> Tuple[str, int]:
        return (self.animation, self.index)


def render_animation(
    source: FrameSource, animation: str, size: Tuple[int, int]
) -> List[RenderedFrame]:
    """Render every frame of one animation independently at ``size``."""
    info = source.animations()[animation]
    count = int(info["frames"])
    duration_ms = int(info.get("duration_ms", 0))
    return [
        RenderedFrame(
            animation=animation,
            index=i,
            count=count,
            duration_ms=duration_ms,
            image=source.frame(animation, i, count, size),
        )
        for i in range(count)
    ]


def render_all_frames(source: FrameSource, size: Tuple[int, int]) -> List[RenderedFrame]:
    """Render every frame of every animation independently at ``size``.

    This is the seam for custom packers and debug tools: each frame is produced
    on its own, in a deterministic order, so a caller can pack them with any
    algorithm (or lay them out for inspection) without going through the built-in
    sheet pipeline. Rendering one frame never depends on any other, so the caller
    may also render a subset or reorder freely.
    """
    frames: List[RenderedFrame] = []
    for animation in source.animations():
        frames.extend(render_animation(source, animation, size))
    return frames


# Generators draw their detail relative to the frame size; below this many
# pixels on the short edge, fine features (a 1-2px rounded corner) collapse to
# degenerate geometry and some generators' PIL calls fail outright. Rendering at
# this floor and downsampling to the requested size makes every generator robust
# at any resolution AND yields better-antialiased small sprites — the standard
# way to make a small sprite is to draw big and shrink.
_MIN_RENDER_PX = 96


class GeneratedFrameSource:
    """A :class:`FrameSource` over a procedural
    :class:`~ambition_sprite2d_renderer.authoring.generator.CharacterGenerator`
    bound to one :class:`CharacterJob`.

    The spec is sampled once here; ``frame`` closes over it. The generator's
    bespoke PIL drawing lives inside its ``render_frame`` — this wrapper only
    supplies the uniform envelope, it does not reshape the drawing.
    """

    def __init__(self, generator, job) -> None:
        self._generator = generator
        self._job = job
        self._spec = generator.sample_spec(job)
        self.target = generator.target or job.target

    def animations(self) -> Dict[str, Dict[str, int]]:
        return self._generator.animations()

    def frame(
        self, animation: str, index: int, count: int, size: Tuple[int, int]
    ) -> Image.Image:
        del count  # the generator recomputes frame count from animations()
        w, h = size
        short = max(1, min(w, h))
        if short >= _MIN_RENDER_PX:
            return self._generator.render_frame(self._spec, animation, index, size, self._job)
        # Render detail at a safe internal resolution, then downsample to the
        # requested (small) size.
        scale = _MIN_RENDER_PX / short
        internal = (max(1, round(w * scale)), max(1, round(h * scale)))
        big = self._generator.render_frame(self._spec, animation, index, internal, self._job)
        return big.resize(size, Image.Resampling.LANCZOS)

    def canonical_pose(self) -> Tuple[str, int]:
        return self._generator.canonical_pose()

    def attack_hitboxes(self, size: Tuple[int, int]) -> Dict[str, Dict[str, Any]]:
        return self._generator.attack_hitboxes(size)

    def hurtbox_parts(self, size: Tuple[int, int]) -> Dict[str, Dict[str, Any]]:
        return self._generator.hurtbox_parts(size)

    def body_inset(self) -> Optional[Dict[str, float]]:
        return self._generator.body_inset()

    def actor_metadata(self) -> Optional[Dict[str, Any]]:
        return None

    def spec_dict(self) -> Optional[Dict[str, Any]]:
        return self._generator.spec_dict(self._spec)
