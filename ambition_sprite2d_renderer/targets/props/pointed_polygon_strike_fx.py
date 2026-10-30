"""His polygon sword: a bright arc that travels with the blow.

`attack_vfx` of `pointed_polygon`. Drawn by `_strike_fx_common` (style ``arc``);
this module states only whose blow it is.
"""

from __future__ import annotations

from ._strike_fx_common import Palette, renderer, sheet_files

TARGET_NAME = "pointed_polygon_strike_fx"
SHEET_FILES = sheet_files(TARGET_NAME)

render, ACTOR_METADATA = renderer(
    TARGET_NAME,
    style="arc",
    palette=Palette(core=(255, 255, 255), body=(178, 218, 255), edge=(46, 78, 140), accent=(220, 240, 255)),
    display_name="Pointed Polygon Strike",
    mote="dot",
)
