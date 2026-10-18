"""A plain grey streak and burst.

`attack_vfx` of `officer`. Drawn by `_strike_fx_common` (style ``impact``);
this module states only whose blow it is.
"""

from __future__ import annotations

from ._strike_fx_common import Palette, renderer, sheet_files

TARGET_NAME = "officer_strike_fx"
SHEET_FILES = sheet_files(TARGET_NAME)

render, ACTOR_METADATA = renderer(
    TARGET_NAME,
    style="impact",
    palette=Palette(core=(248, 250, 255), body=(196, 202, 214), edge=(46, 56, 78), accent=(232, 236, 246)),
    display_name="Officer Strike",
    mote="dot",
)
