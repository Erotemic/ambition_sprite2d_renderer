"""Procedural sprite target for Genghis Can.

Genghis Can is the confident half of a parody duo with Genghis Can't. The pair
share the same silhouette family and authored wardrobe grammar, but this
variant stands taller, gestures like a conqueror, and carries cleaner red-and-
gold lamellar.
"""

from __future__ import annotations

from ._genghis_pair_common import ACTOR_METADATA, render_portraits as _render_portraits, render_target

TARGET_NAME = "genghis_can"
ACTOR_METADATA = ACTOR_METADATA[TARGET_NAME]


def render(out_dir, **opts):
    return render_target(TARGET_NAME, out_dir, **opts)


def render_portraits(out_dir, **opts):
    return _render_portraits(TARGET_NAME, out_dir, **opts)


__all__ = ["ACTOR_METADATA", "render", "render_portraits"]
