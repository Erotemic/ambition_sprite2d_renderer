"""His oversized fists: a bright red arc that travels with the blow.

`attack_vfx` of `pugnacious_polygon`. Drawn by `_strike_fx_common` (style ``arc``);
this module states only whose blow it is.
"""

from __future__ import annotations

from ._strike_fx_common import Palette, renderer, sheet_files

TARGET_NAME = "pugnacious_polygon_strike_fx"
SHEET_FILES = sheet_files(TARGET_NAME)

render, ACTOR_METADATA = renderer(
    TARGET_NAME,
    style="arc",
    palette=Palette(core=(255, 250, 250), body=(255, 160, 160), edge=(136, 36, 48), accent=(255, 214, 214)),
    display_name="Pugnacious Polygon Strike",
    mote="dot",
)
