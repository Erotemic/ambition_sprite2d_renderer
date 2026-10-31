"""The Void Pugnacious Polygon: the brawler polygon, made of the void.

An enemy of the void dungeon. The rig, the poses, the frames and the hit
volumes are those of `pugnacious_polygon`; only the paint changes
(`_void_polygon`). His whooshes and re-entry cones are grey and white.
"""

from __future__ import annotations

from ambition_sprite2d_renderer.targets.characters import pugnacious_polygon as _source
from ambition_sprite2d_renderer.targets.characters._void_polygon import EyeSlit, VoidPolygon, module_api

# He looks to the west: the slits are on the front of his head, about the
# source's pale face plane, and slope down to the middle.
VOID = VoidPolygon(
    source=_source,
    target="void_pugnacious_polygon",
    display_name="Void Pugnacious Polygon",
    eyes=(
        EyeSlit(((568, 212), (596, 223), (594, 232), (569, 222))),
        EyeSlit(((606, 223), (634, 212), (633, 222), (608, 232))),
    ),
    description=(
        "The Pugnacious Polygon made of the void: a black faceted brawler "
        "with a white edge and white eye slits, an enemy of the void dungeon. "
        "Same rig, poses and frame data as `pugnacious_polygon`."
    ),
)
TARGET_NAME, ACTOR_METADATA, render = module_api(VOID)
