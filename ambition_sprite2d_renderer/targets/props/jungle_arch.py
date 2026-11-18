"""The Jungle's portal arch (WORLD-LAYERS JL-2): the portal arch's
assembly (``_portal_arch``) in old jungle stone, lichen grey-green, moss on
its head and threshold, a vine over its left shoulder and a fern at its
right foot. The gate rings are 288 world units and stand through the
Jungle's branch platforms; an arch is a door's size, small enough to stand
under a branch or on one.
"""

from __future__ import annotations

from . import _portal_arch as arch

TARGETS = {"jungle_arch": arch.render_targets("jungle_arch", arch.JUNGLE)}
