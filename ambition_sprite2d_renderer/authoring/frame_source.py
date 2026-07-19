"""A shared sheet-pipeline input: ``FrameSource``.

``FrameSource`` is an authoring-side convenience for generators, rigs, and
frame callables that can expose a common frame-query surface. It is not the
universal sprite-target contract and does not prescribe how every character is
posed or drawn. The stable cross-family boundary remains the published sprite
sheet and metadata.

The requested ``size`` is the output raster size. Implementations may rerender
natively, render at a safe internal size and downsample, or adapt a legacy
fixed-size callable. Consumers that require newly rendered high-resolution
detail must use an explicit capability rather than infer it from this protocol.

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
from ..profiling import profile


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
        """Return frame ``index`` at output ``size``; native rerendering is not implied."""

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


@profile
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


@profile
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


class CallableFrameSource:
    """A :class:`FrameSource` over a module-authored target: a frame callable
    ``render_fn(animation, index, count) -> Image`` plus its row list and the
    sheet-build recipe (crop / label / geometry options).

    This is what a module *declares* instead of hand-rolling a ``render()`` that
    calls ``build_sheet``. The recipe fields are read back by
    ``sheet_build.render_sheet`` when it assembles the sheet, so the module says
    *what* it is once and the one pipeline does the building.

    ``render_fn`` draws at the module's native ``frame_size``; :meth:`frame`
    resizes to a caller-requested size (for the per-frame API / packer), while
    the sheet build uses the native size directly.
    """

    def __init__(
        self,
        *,
        target: str,
        rows: List[Tuple[str, int, int]],
        render_fn,
        frame_size: Tuple[int, int],
        label_width: int = 0,
        auto_crop: bool = True,
        crop_margin: int = 2,
        actor_metadata: Optional[Dict[str, Any]] = None,
        frame_meta_fn=None,
        body_metrics_fn=None,
        animation_key_map: Optional[Dict[str, str]] = None,
        attack_hitboxes: Optional[Dict[str, Any]] = None,
        sheet_tuning: Optional[Dict[str, Any]] = None,
        trim: Optional[bool] = None,
        max_sheet_dimension: int = 16384,
    ) -> None:
        self.target = target
        self.rows = list(rows)
        self.render_fn = render_fn
        self.frame_size = frame_size
        # Sheet-build recipe (read by render_sheet).
        self.label_width = label_width
        self.auto_crop = auto_crop
        self.crop_margin = crop_margin
        self._actor_metadata = actor_metadata
        self.frame_meta_fn = frame_meta_fn
        self.body_metrics_fn = body_metrics_fn
        self.animation_key_map = animation_key_map
        self._attack_hitboxes = attack_hitboxes
        self.sheet_tuning = sheet_tuning
        self.trim = trim
        self.max_sheet_dimension = max_sheet_dimension

    def animations(self) -> Dict[str, Dict[str, int]]:
        return {
            anim: {"frames": nframes, "duration_ms": duration_ms}
            for anim, nframes, duration_ms in self.rows
        }

    def frame(
        self, animation: str, index: int, count: int, size: Tuple[int, int]
    ) -> Image.Image:
        img = self.render_fn(animation, index, count)
        if img.size != size:
            img = img.resize(size, Image.Resampling.LANCZOS)
        return img

    def canonical_pose(self) -> Tuple[str, int]:
        anim, nframes, _ = self.rows[0]
        return (anim, min(1, nframes - 1))

    def attack_hitboxes(self, size: Tuple[int, int]) -> Dict[str, Dict[str, Any]]:
        del size  # authored in native-frame pixels
        return dict(self._attack_hitboxes or {})

    def hurtbox_parts(self, size: Tuple[int, int]) -> Dict[str, Dict[str, Any]]:
        del size  # module targets derive per-anim hurtboxes via animation_key_map
        return {}

    def body_inset(self) -> Optional[Dict[str, float]]:
        return None

    def actor_metadata(self) -> Optional[Dict[str, Any]]:
        return self._actor_metadata

    def spec_dict(self) -> Optional[Dict[str, Any]]:
        return None
