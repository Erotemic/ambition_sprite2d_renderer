"""The Void Pointed Polygon: the sword polygon, made of the void.

An enemy of the void dungeon. The rig, the poses, the frames and the hit
volumes are those of `pointed_polygon`; only the paint changes
(`_void_polygon`). The sword is black with a white edge, and its ribbon is a
white slash.
"""

from __future__ import annotations

from ambition_sprite2d_renderer.targets.characters import pointed_polygon as _source
from ambition_sprite2d_renderer.targets.characters._void_polygon import EyeSlit, VoidPolygon, module_api

# She looks to the west: the slits are on the front of the face, where the
# source has its visor plane, and slope down to the middle.
VOID = VoidPolygon(
    source=_source,
    target="void_pointed_polygon",
    display_name="Void Pointed Polygon",
    eyes=(
        EyeSlit(((596, 212), (619, 220), (617, 228), (597, 221))),
        EyeSlit(((627, 220), (651, 212), (650, 221), (629, 228))),
    ),
    description=(
        "The Pointed Polygon made of the void: a black faceted swordswoman "
        "with a white edge and white eye slits, an enemy of the void dungeon. "
        "Same rig, poses and frame data as `pointed_polygon`."
    ),
)
TARGET_NAME, ACTOR_METADATA, render = module_api(VOID)
