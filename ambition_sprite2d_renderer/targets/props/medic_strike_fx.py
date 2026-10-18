"""A red streak and burst.

`attack_vfx` of `medic`. Drawn by `_strike_fx_common` (style ``impact``);
this module states only whose blow it is.
"""

from __future__ import annotations

from ._strike_fx_common import Palette, renderer, sheet_files

TARGET_NAME = "medic_strike_fx"
SHEET_FILES = sheet_files(TARGET_NAME)

render, ACTOR_METADATA = renderer(
    TARGET_NAME,
    style="impact",
    palette=Palette(core=(255, 248, 248), body=(255, 150, 150), edge=(158, 30, 42), accent=(255, 214, 214)),
    display_name="Medic Strike",
    mote="dot",
)
