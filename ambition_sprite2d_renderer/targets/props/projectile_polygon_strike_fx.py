"""Faceted bites and tail swipes: an orange crescent that breaks into triangles.

`attack_vfx` of `projectile_polygon`. Drawn by `_strike_fx_common` (style ``shard``);
this module states only whose blow it is.
"""

from __future__ import annotations

from ._strike_fx_common import Palette, renderer, sheet_files

TARGET_NAME = "projectile_polygon_strike_fx"
SHEET_FILES = sheet_files(TARGET_NAME)

render, ACTOR_METADATA = renderer(
    TARGET_NAME,
    style="shard",
    palette=Palette(core=(255, 252, 246), body=(255, 188, 136), edge=(148, 66, 36), accent=(255, 226, 196)),
    display_name="Projectile Polygon Strike",
    mote="dot",
)
