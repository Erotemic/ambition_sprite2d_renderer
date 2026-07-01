"""The canonical procedural character generator.

A target's generator **is** a :class:`CharacterGenerator`; the sheet pipeline
renders any :class:`CharacterGenerator`. There is deliberately no separate
adapter layer that reshapes a generator into a canonical interface — each
generator implements this interface directly.

The base owns the shared machinery (spec sampling + overrides, single/canonical
frame rendering, the default gameplay-geometry hooks). A concrete generator
implements only what is genuinely its own:

* ``ANIMATIONS`` — the animation → ``{"frames": n, "duration_ms": d}`` table;
* :meth:`build_spec` — sample the per-character spec from a :class:`CharacterJob`;
* :meth:`render_frame` — render one frame of one animation;
* optionally, the authored gameplay geometry for *that* character
  (:meth:`attack_hitboxes` / :meth:`hurtbox_parts` / :meth:`body_inset`).
"""

from __future__ import annotations

from dataclasses import asdict, fields, is_dataclass, replace
from typing import Any, Dict, List, Tuple

from PIL import Image

from ..registry import CharacterJob


def _strip_callables(value: Any) -> Any:
    # Spec dataclasses may carry hook callables (e.g. ToonSpec.pose_override).
    # asdict passes them through unchanged, and yaml/RON can't represent
    # functions — drop them so the manifest stays serialisable.
    if isinstance(value, dict):
        return {k: _strip_callables(v) for k, v in value.items() if not callable(v)}
    if isinstance(value, list):
        return [_strip_callables(v) for v in value if not callable(v)]
    if isinstance(value, tuple):
        return tuple(_strip_callables(v) for v in value if not callable(v))
    return value


def dataclass_dict(obj: Any) -> Dict[str, Any]:
    """Serialise a spec dataclass to a plain, hook-free dict for the manifest."""
    data = asdict(obj) if is_dataclass(obj) else dict(obj)
    return _strip_callables(data)


class CharacterGenerator:
    """Base for every procedural character/prop generator."""

    #: Registry id; also the ``target:`` in the target's YAML config.
    target: str = ""

    #: ``animation name -> {"frames": n, "duration_ms": d}``.
    ANIMATIONS: Dict[str, Dict[str, int]] = {}

    #: When True, a job's ``name`` overrides the sampled spec's ``name`` field
    #: (bespoke, single-identity targets such as Bob or Trent). Left False for
    #: procedurally-named families whose spec owns its own name.
    applies_job_name: bool = False

    # -- animation surface ------------------------------------------------

    def animations(self) -> Dict[str, Dict[str, int]]:
        return dict(self.ANIMATIONS)

    def default_animations(self) -> List[str]:
        return list(self.animations().keys())

    def canonical_pose(self) -> Tuple[str, int]:
        """The (animation, frame) rendered as the single canonical pose."""
        return ("idle", 1)

    # -- spec sampling ----------------------------------------------------

    def build_spec(self, job: CharacterJob) -> Any:
        """Sample this character's spec from the job. Subclasses implement."""
        raise NotImplementedError

    def sample_spec(self, job: CharacterJob) -> Any:
        """Canonical entry point: sample the spec, override its name from the
        job when this target opts in, then apply job spec-overrides."""
        spec = self.build_spec(job)
        if self.applies_job_name and job.name:
            spec = replace(spec, name=job.name)
        return self._apply_overrides(spec, job)

    def spec_dict(self, spec: Any) -> Dict[str, Any]:
        return dataclass_dict(spec)

    # -- frame rendering --------------------------------------------------

    def render_frame(
        self,
        spec: Any,
        animation: str,
        frame_index: int,
        size: Tuple[int, int],
        job: CharacterJob,
    ) -> Image.Image:
        """Render one frame of ``animation`` at ``size``. Subclasses implement."""
        raise NotImplementedError

    def render_single(
        self, spec: Any, animation: str, frame_index: int, job: CharacterJob
    ) -> Image.Image:
        r = job.render
        return self.render_frame(
            spec, animation, frame_index, (r.single_width, r.single_height), job
        )

    def render_canonical(self, spec: Any, job: CharacterJob) -> Image.Image:
        animation, frame_index = self.canonical_pose()
        return self.render_single(spec, animation, frame_index, job)

    # -- authored gameplay geometry (defaults: none) ----------------------

    def attack_hitboxes(self, size: Tuple[int, int]) -> Dict[str, Dict[str, Any]]:
        """Per-animation attack-hitbox shapes, in source-canvas pixels.

        Returns a dict mapping animation name to a hitbox descriptor — either a
        coarse ``{"bbox": (x, y, w, h)}`` or a multi-part
        ``{"parts": [{"name", "x", "y", "w", "h"}, ...]}`` (optionally with a
        convex ``"poly"``). The renderer translates these to cropped-frame
        coordinates before emitting. Default: none (gameplay falls back to its
        own volume math).
        """
        del size
        return {}

    def hurtbox_parts(self, size: Tuple[int, int]) -> Dict[str, Dict[str, Any]]:
        """Per-animation hurtbox-parts override.

        When declared, the listed parts REPLACE the renderer's auto-derived
        alpha-bbox hurtbox for that animation, letting a character carve a
        multi-rect hurtbox that excludes cosmetic / unsafe extensions (e.g.
        arms extended during an attack). Coordinates are source-canvas pixels.
        Default: none (use the auto-derived alpha bbox).
        """
        del size
        return {}

    def body_inset(self) -> Dict[str, float] | None:
        """Fractional shrink applied to the measured body bbox (and each
        per-animation hurtbox) at generation time.

        Returns a mapping with optional ``left`` / ``right`` / ``top`` /
        ``bottom`` keys, each a fraction of the measured width (left/right) or
        height (top/bottom) to trim from that edge. ``None`` keeps the raw
        measured alpha box. Because it scales with the measured box rather than
        pinning absolute pixels, it survives art changes. Default: ``None``.
        """
        return None

    # -- overrides --------------------------------------------------------

    def _apply_overrides(self, spec: Any, job: CharacterJob) -> Any:
        overrides = dict(getattr(job, "spec_overrides", {}) or {})
        if not overrides:
            return spec
        if not is_dataclass(spec):
            raise TypeError(
                f"spec overrides are only supported for dataclass specs (target={job.target})"
            )
        known = {f.name for f in fields(spec)}
        unknown = sorted(set(overrides) - known)
        if unknown:
            raise KeyError(
                f"unknown spec override keys for {job.target}: {unknown}; available={sorted(known)}"
            )
        return replace(spec, **overrides)
