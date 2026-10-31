"""The Void Projectile Polygon: the cannon beast polygon, made of the void.

An enemy of the void dungeon. The rig, the poses, the frames and the hit
volumes are those of `projectile_polygon`; only the paint changes
(`_void_polygon`). His muzzle flashes and beams are grey and white.
"""

from __future__ import annotations

from ambition_sprite2d_renderer.targets.characters import projectile_polygon as _source
from ambition_sprite2d_renderer.targets.characters._void_polygon import EyeSlit, VoidPolygon, module_api

# He looks to the east: the slits are on the source's visor plane, behind the
# snout's outline so it does not eat them, and slope down to the middle.
VOID = VoidPolygon(
    source=_source,
    target="void_projectile_polygon",
    display_name="Void Projectile Polygon",
    eyes=(
        EyeSlit(((690, 280), (718, 290), (716, 300), (691, 291))),
        EyeSlit(((726, 290), (754, 280), (753, 291), (728, 300))),
    ),
    description=(
        "The Projectile Polygon made of the void: a black faceted cannon "
        "beast with a white edge and white eye slits, an enemy of the void "
        "dungeon. Same rig, poses and frame data as `projectile_polygon`."
    ),
)
TARGET_NAME, ACTOR_METADATA, render = module_api(VOID)
