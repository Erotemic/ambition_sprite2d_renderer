"""A warm auburn streak and burst.

`attack_vfx` of `performer`. Drawn by `_strike_fx_common` (style ``impact``);
this module states only whose blow it is.
"""

from __future__ import annotations

from ._strike_fx_common import Palette, renderer, sheet_files

TARGET_NAME = "performer_strike_fx"
SHEET_FILES = sheet_files(TARGET_NAME)

render, ACTOR_METADATA = renderer(
    TARGET_NAME,
    style="impact",
    palette=Palette(core=(255, 250, 244), body=(242, 184, 140), edge=(128, 58, 46), accent=(255, 226, 196)),
    display_name="Performer Strike",
    mote="dot",
)
