"""His polygon sword: a faceted crescent that breaks into triangles.

`attack_vfx` of `pointed_polygon`. Drawn by `_strike_fx_common` (style ``shard``);
this module states only whose blow it is.
"""

from __future__ import annotations

from ._strike_fx_common import Palette, renderer, sheet_files

TARGET_NAME = "pointed_polygon_strike_fx"
SHEET_FILES = sheet_files(TARGET_NAME)

render, ACTOR_METADATA = renderer(
    TARGET_NAME,
    style="shard",
    palette=Palette(core=(255, 255, 255), body=(178, 218, 255), edge=(46, 78, 140), accent=(220, 240, 255)),
    display_name="Pointed Polygon Strike",
    mote="dot",
)
