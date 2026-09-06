"""Procedural sprite target for Genghis Can't.

Genghis Can't is the anxious counterpart to Genghis Can. He keeps the shared
warlord silhouette but bends it into self-doubt: cooler colors, a slouched
posture, and gestures that read more shrug than command.
"""

from __future__ import annotations

from ._genghis_pair_common import ACTOR_METADATA, render_portraits as _render_portraits, render_target

TARGET_NAME = "genghis_cant"
ACTOR_METADATA = ACTOR_METADATA[TARGET_NAME]


def render(out_dir, **opts):
    return render_target(TARGET_NAME, out_dir, **opts)


def render_portraits(out_dir, **opts):
    return _render_portraits(TARGET_NAME, out_dir, **opts)


__all__ = ["ACTOR_METADATA", "render", "render_portraits"]
