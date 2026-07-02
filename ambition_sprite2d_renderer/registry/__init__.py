"""Target discovery + render configuration.

The "wiring" layer that turns the package's content surfaces into a flat
set of renderable ``Target`` objects:

- :mod:`registry.discovery` — walks ``targets/<category>/`` (tack-on
  Python modules) and ``configs/*.yaml`` (adapter targets) and yields a
  uniform ``Target`` for each. The source of truth for the Target
  protocol contract.
- :mod:`registry.config` — the ``CharacterJob`` / ``RenderConfig``
  dataclasses that describe a YAML adapter job.

Import the public names straight from this package
(``from ...registry import discover_all_targets, CharacterJob``); the
submodule split is an internal detail.
"""
from __future__ import annotations

from .config import (
    DEFAULT_ANIMATIONS,
    CharacterJob,
    RenderConfig,
    load_jobs,
)
from .discovery import (
    GENERATOR_MODULE_STEMS,
    CATEGORIES,
    DiscoveryReport,
    Target,
    _ensure_actor_sidecars,
    default_sheet_files,
    discover_all_targets,
    discover_module_targets,
)

__all__ = [
    "GENERATOR_MODULE_STEMS",
    "CATEGORIES",
    "CharacterJob",
    "DEFAULT_ANIMATIONS",
    "DiscoveryReport",
    "RenderConfig",
    "Target",
    "default_sheet_files",
    "discover_all_targets",
    "discover_module_targets",
    "load_jobs",
]
