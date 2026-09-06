"""The small, portable rendering core.

Everything in ``ambition_sprite2d_renderer.core`` must import with **only
Pillow + the Python standard library** — no ``yaml``, ``rich``, ``PySide6``,
or ``numpy``. The point (see docs/planning/sprite-renderer-refactor.md) is that
a chatbot agent with just ``pip install Pillow`` can author and render a sprite.

Heavy/optional dependencies live at the edges:
  * ``yaml``    — reading author-facing configs (an edge module), never here.
  * ``rich``    — CLI prettiness only.
  * ``PySide6`` — the rig editor GUI only.

The core owns portable operations that several authoring families can share:

    authored frames ──▶ supersample → downsample → crop → measure → assemble → emit

:class:`~.frameset.FrameSet` is one useful authoring seam for drawers and other
pipelines that naturally describe themselves as scalable frame painters. It is
not the universal character representation: module targets, config-driven
generators, rig documents, SVG parts, scene graphs, and bespoke pipelines may
retain different internal models. The universal boundary is the registered
target's published sprite-sheet pages and metadata, mirrored by
:mod:`~.manifest` and written as RON without YAML in the write path.

This package is grown incrementally as genuinely shared operations are
identified. Consolidation must not force unrelated artistic pipelines through a
common rig or pose model.
"""

from .frameset import (  # noqa: F401
    AnimationSpec,
    FrameSet,
    FrameSpec,
    frameset_from_states,
)

__all__ = ["FrameSpec", "AnimationSpec", "FrameSet", "frameset_from_states"]
